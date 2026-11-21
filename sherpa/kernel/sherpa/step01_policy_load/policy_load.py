"""Step 1 · policy_load: read the built policy, sherpa/policy/, and nothing else (human ruling 2026-11-03).

ppo, the policy pack organizer (a tool of its own, outside this repo), stacks the policy packs and
writes five tables plus a dated lock, policyYYYYMMDD_NN.lock (Spec/kernel-policy-contract.zh.md, section 2). This step takes the newest lock and checks every hash in it:
the five tables, and each pack folder the plugins' code is loaded from. Nothing built yet ->
policy.not_built; anything changed since the build -> policy.changed_since_build. Either way the
command stops here and nothing is written.

The kernel never stacks packs, never judges a locked row and never reads policy_pack.toml.
"""
import hashlib
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType

from sherpa.result import KernelStop, kernel_red
from sherpa.result.fingerprint import tree_hash
from sherpa.step01_policy_load.tables import (ACTIONS, KINDS, STAGES, STEP, TABLES, TableShape, read_table,
                                              split_list)
from sherpa.step03_flow_control import validate as flow_validate
from sherpa.step10_output_apply.governance_lock import LockBusy, policy_read_lock

POLICY = "policy"           # sherpa/policy/: what ppo built
POLICYPACK = "policypack"   # sherpa/policypack/: the installed packs, where plugin code and role cards are


@dataclass(frozen=True)
class Policy:
    policy_pack: str            # the lock that judged this command, e.g. policy20261103_00
    packs: tuple                # pack names in load order
    pack_root: Path             # sherpa/policypack: plugin impl and role card paths are relative to it
    flow: MappingProxyType      # command -> row
    checks: tuple               # rows in table order
    outputs: tuple
    roles: MappingProxyType     # role -> row
    plugins: MappingProxyType   # name -> row
    states: frozenset
    warnings: tuple
    policy_pack_hash: str       # of the lock file: it pins every table and pack folder
    no_guarantees: bool = False  # only base-group packs are on (ppo decides)

    def role_of_prefix(self, prefix: str):
        return next((r for r in self.roles.values() if r["prefix"] == prefix), None)


def stop(code, reason, fix, objects=()):
    return KernelStop(kernel_red(STEP, code, reason, fix, objects))


def warn(code, reason, fix):
    return replace(kernel_red(STEP, code, reason, fix), action="warn")


def built_shape(shape: TableShape) -> TableShape:
    """A built table has one more column: the pack each row came from."""
    return replace(shape, columns=(*shape.columns, "pack"))


def newest_lock(folder: Path) -> Path:
    locks = sorted(folder.glob("policy*.lock"))
    if not locks:
        raise stop("policy.not_built", f"no policy built in {folder}",
                   "build the policy with ppo, then run again")
    return locks[-1]


def changed(what: str, lock: Path):
    return stop("policy.changed_since_build", f"{what} changed after {lock.stem} was built",
                "rebuild the policy with ppo (if the change was meant), or undo it", [what])


def read_lock(path: Path) -> tuple:
    data = path.read_bytes()
    try:
        return tomllib.loads(data.decode("utf-8")), hashlib.sha256(data).hexdigest()[:16]
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as err:
        raise stop("policy.changed_since_build", f"{path}: {err}", "rebuild the policy with ppo", [str(path)])


def frozen(row: dict) -> MappingProxyType:
    row = dict(row)
    row["_from"] = row.pop("pack")
    return MappingProxyType(row)


def read_tables(folder: Path, lock: dict, lock_path: Path) -> dict:
    out = {}
    for table, shape in TABLES.items():
        path = folder / shape.file
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != lock.get("tables", {}).get(table):
            raise changed(f"{POLICY}/{shape.file}", lock_path)
        out[table] = [frozen(r) for r in read_table(path, built_shape(shape))]
    return out


def check_packs(pack_root: Path, lock: dict, lock_path: Path):
    """The code the plugins load, and the role cards, are in the pack folders: pinned by hash."""
    for name in lock.get("order", []):
        if tree_hash([pack_root / name]) != lock.get("pack", {}).get(name, {}).get("hash"):
            raise changed(f"{POLICYPACK}/{name}/", lock_path)


def check_cells(tables: dict):
    """Only what the kernel itself relies on; ppo checked everything else before it built."""
    for row in tables["checks"]:
        if row["stage"] not in STAGES or row["action"] not in ACTIONS:
            raise stop("policy.bad_table", f"{POLICY}/checks.tsv:{row['_line']}: stage {row['stage']} / action {row['action']}",
                       "rebuild the policy with ppo")
    roles = {r["role"] for r in tables["roles"]}
    for table in ("checks", "outputs"):
        for row in tables[table]:
            unknown = [r for r in split_list(row["roles"]) if r != "*" and r not in roles]
            if unknown:
                raise stop("policy.unknown_role", f"{POLICY}/{table}.tsv:{row['_line']} names role '{unknown[0]}', "
                           "roles.tsv has no such role", "rebuild the policy with ppo")
    prefixes = {}
    for row in tables["roles"]:
        if row["prefix"] in prefixes:      # step 2 could not tell the two roles apart
            raise stop("policy.bad_table", f"{POLICY}/roles.tsv:{row['_line']}: prefix {row['prefix']} is also "
                       f"role {prefixes[row['prefix']]}'s", "give each role its own prefix, then rebuild the policy with ppo")
        prefixes[row["prefix"]] = row["role"]
    for row in tables["plugins"]:
        if row["kind"] not in KINDS:
            raise stop("policy.bad_table", f"{POLICY}/plugins.tsv:{row['_line']}: kind {row['kind']}",
                       "rebuild the policy with ppo")


def run(workspace) -> Policy:
    folder, pack_root = workspace.dot / POLICY, workspace.dot / POLICYPACK
    try:
        with policy_read_lock(workspace.governance_repo):      # ppo writes policy/ holding .lock
            lock_path = newest_lock(folder)
            lock, lock_hash = read_lock(lock_path)
            tables = read_tables(folder, lock, lock_path)
            check_packs(pack_root, lock, lock_path)
    except LockBusy as busy:
        raise stop("lock.busy", f"{busy}: ppo may be writing the policy", "wait for ppo to finish, then run again")
    check_cells(tables)
    flow = {r["command"]: r for r in tables["flow"]}
    roles = {r["role"]: r for r in tables["roles"]}
    plugins = {r["name"]: r for r in tables["plugins"]}
    states = flow_validate.validate(flow, roles, plugins)
    return Policy(
        policy_pack=lock.get("name", lock_path.stem),
        packs=tuple(lock.get("order", [])),
        pack_root=pack_root,
        flow=MappingProxyType(flow),
        checks=tuple(tables["checks"]),
        outputs=tuple(tables["outputs"]),
        roles=MappingProxyType(roles),
        plugins=MappingProxyType(plugins),
        states=states,
        warnings=tuple(warn(w["code"], w["reason"], w["fix"]) for w in lock.get("warnings", [])),
        policy_pack_hash=lock_hash,
        no_guarantees=bool(lock.get("no_guarantees", False)),
    )


__all__ = ["Policy", "run", "split_list", "STAGES", "ACTIONS", "KINDS", "POLICY", "POLICYPACK"]
