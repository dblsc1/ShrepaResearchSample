"""Build sherpa/policy/: the five tables and a dated lock, as the contract says (sections 2.1-2.4, 5).

  plan(policypack)   order the enabled packs, stack their tables, compile the custom lifecycle,
                     and check it all; nothing is written
  write(repo, plan)  under the governance lock: the five tables first, the lock last (a half-written
                     build fails the kernel's hash check instead of being read); a build equal to the
                     newest lock writes nothing; a governance repo that is a git repo gets a commit

Built rows: the pack the row came from as a last column `pack`; plugin impl and role cards made
relative to policypack/ (task_card.py in pack classic_lifecycle -> classic_lifecycle/task_card.py).
"""
import hashlib
import subprocess
import time
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from ppo import PpoError, Problem
from ppo.governance_lock import governance_lock
from ppo.lifecycle_compile import compile_lifecycle
from ppo.load_order import resolve
from ppo.pack_library import declarations, read_load_order
from ppo.policy_tables import TABLES
from ppo.stack import check_built, stack_and_check
from ppo.tree_hash import tree_hash

POLICY = "policy"
HEADER = "# Built by `ppo build` from sherpa/policypack/. Do not edit: change a pack, then build.\n"


@dataclass
class Plan:
    order: object
    stacked: object = None
    decls: dict = field(default_factory=dict)
    problems: list = field(default_factory=list)


def plan(policypack: Path, packs=None) -> Plan:
    packs = tuple(packs) if packs is not None else read_load_order(policypack)
    decls = declarations(policypack, packs)
    order = resolve(decls, packs)
    if order.problems:
        return Plan(order, decls=decls, problems=list(order.problems))
    stacked = stack_and_check(order.names, decls)
    problems = list(stacked.problems)
    if not problems:
        problems += compile_lifecycle(stacked, decls)
    if not problems:
        check_built(stacked)
        problems += stacked.problems
    return Plan(order, stacked, decls, problems)


def pack_relative(cell: str, pack: str) -> str:
    """A file in the pack (x.py, exec:x) -> its path under policypack/; module names and absolute paths
    stay (the same rule stack.code_file uses to find the file)."""
    if cell.startswith("exec:") and not cell[5:].startswith("/"):
        return f"exec:{pack}/{cell[5:]}"
    return f"{pack}/{cell}" if cell.endswith(".py") and not cell.startswith("/") else cell


def built_text(table: str, rows) -> str:
    shape = TABLES[table]
    lines = [HEADER, "\t".join((*shape.columns, "pack")) + "\n"]
    for row in rows:
        cells = dict(row)
        if table == "plugins":
            cells["impl"] = pack_relative(row["impl"], row["_from"])
        if table == "roles" and row["card"] != "-":
            cells["card"] = f"{row.get('_card_from', row['_from'])}/{row['card']}"
        lines.append("\t".join([*(cells[c] for c in shape.columns), row["_from"]]) + "\n")
    return "".join(lines)


def toml_str(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def newest_lock(folder: Path):
    locks = sorted(folder.glob("policy*.lock"))
    return locks[-1] if locks else None


def next_lock_name(folder: Path) -> str:
    """policyYYYYMMDD_NN, sorting after every lock there (the kernel takes the last by name)."""
    day = time.strftime("%Y%m%d")
    taken = [p.stem for p in folder.glob(f"policy{day}_*.lock")]
    n = max((int(s.rsplit("_", 1)[1]) for s in taken if s.rsplit("_", 1)[1].isdigit()), default=-1) + 1
    name, last = f"policy{day}_{n:02d}", newest_lock(folder)
    if n > 99 or (last is not None and name <= last.stem):
        raise PpoError(Problem("policy.lock_name", f"the next lock {name} would not sort after {last.stem if last else '-'}",
                               "the clock is behind the newest lock, or 100 builds today: move old locks out of policy/"))
    return name


def lock_text(name, the_plan: Plan, table_hashes: dict, pack_hashes: dict) -> str:
    decls, order = the_plan.decls, the_plan.order.names
    lines = ["# Written by `ppo build`. The kernel reads the newest lock here and checks every hash.",
             f"name = {toml_str(name)}",
             f"built_at = {toml_str(time.strftime('%Y-%m-%dT%H:%M:%S%z'))}",
             f"no_guarantees = {'true' if all(decls[n].group == 'base' for n in order) else 'false'}",
             f"order = [{', '.join(toml_str(n) for n in order)}]", "", "[tables]"]
    lines += [f"{t} = {toml_str(h)}" for t, h in table_hashes.items()]
    for n in order:
        lines += ["", f"[pack.{n}]", f"version = {toml_str(decls[n].version)}", f"hash = {toml_str(pack_hashes[n])}"]
    for w in the_plan.stacked.warnings:
        lines += ["", "[[warnings]]", f"code = {toml_str(w.code)}", f"reason = {toml_str(w.reason)}",
                  f"fix = {toml_str(w.fix)}"]
    return "\n".join(lines) + "\n"


def same_as(lock: Path, order, table_hashes, pack_hashes) -> bool:
    """The newest lock already pins this build, and the tables on disk are still the ones it pins."""
    try:
        data = tomllib.loads(lock.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return False
    on_disk = {t: hashlib.sha256(f.read_bytes()).hexdigest() if f.is_file() else ""
               for t, f in ((t, lock.parent / TABLES[t].file) for t in TABLES)}
    return (data.get("order") == list(order) and data.get("tables") == table_hashes == on_disk
            and all(data.get("pack", {}).get(n, {}).get("hash") == h for n, h in pack_hashes.items()))


def write(repo: Path, the_plan: Plan) -> tuple:
    """Returns (lock name, written?). The plan must have no problems."""
    if the_plan.problems:
        raise PpoError(*the_plan.problems)
    texts = {t: built_text(t, the_plan.stacked.tables[t].values()) for t in TABLES}
    table_hashes = {t: hashlib.sha256(x.encode("utf-8")).hexdigest() for t, x in texts.items()}
    pack_hashes = {n: tree_hash(repo / "policypack" / n) for n in the_plan.order.names}
    folder = repo / POLICY
    with governance_lock(repo):
        folder.mkdir(parents=True, exist_ok=True)
        last = newest_lock(folder)
        if last is not None and same_as(last, the_plan.order.names, table_hashes, pack_hashes):
            commit(repo, last.stem)              # an earlier commit may have failed
            return last.stem, False
        name = next_lock_name(folder)
        for t, x in texts.items():
            (folder / TABLES[t].file).write_text(x, encoding="utf-8")
        (folder / f"{name}.lock").write_text(lock_text(name, the_plan, table_hashes, pack_hashes), encoding="utf-8")
    commit(repo, name)
    return name, True


def commit(repo: Path, name: str):
    """contract 1: a governance repo that is already a git repo gets policy/ and policypack/ committed."""
    if not (repo / ".git").exists():
        return
    subprocess.run(["git", "add", "-A", "--", POLICY, "policypack"], cwd=repo, capture_output=True)
    if not subprocess.run(["git", "status", "--porcelain", "--", POLICY, "policypack"], cwd=repo,
                          capture_output=True, text=True).stdout.strip():
        return
    done = subprocess.run(["git", "commit", "-q", "-m", f"ppo build {name}", "--", POLICY, "policypack"],
                          cwd=repo, capture_output=True, text=True)
    if done.returncode != 0:
        raise PpoError(Problem("policy.commit_failed", f"built {name}, but git commit in {repo} failed: "
                               f"{(done.stderr or done.stdout).strip()[:300]}",
                               "fix git there (user.name, hooks), then run `ppo build` again: it commits what is built"))
