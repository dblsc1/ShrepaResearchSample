"""Stack the packs' tables in load order and find every conflict.

Five tables merge by key (flow: command; checks: command+check; outputs: event+output; roles: role;
plugins: name). A row whose key is already there:
  restated word for word        noise: the first row stays
  the old row is locked         policy.locked_row
  the new pack requires the old one (directly or not)
                                an intended override: applied, and listed by `ppo check`
  anything else                 policy.row_conflict: two packs that know nothing of each other.
                                The person settles it by editing a pack (human ruling 2026-11-03).
A row whose every non-key cell is '-' deletes the key, under the same rules.

Then the stacked tables must hold together (every plugin named is registered with its kind and its
file is in its pack, every check sits on a known command...), and no two packs may claim one path.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

from ppo import PpoError, Problem
from ppo.policy_tables import ACTIONS, KINDS, STAGES, TABLES, is_deletion, key_of, read_table, split_list


@dataclass
class Stacked:
    tables: dict                                     # table -> {key: row}; each row has '_from' (its pack)
    overrides: list = field(default_factory=list)    # (table, key, winner, loser)
    problems: list = field(default_factory=list)
    warnings: list = field(default_factory=list)     # shown by the kernel on every Result (via the lock)
    notes: list = field(default_factory=list)        # shown by ppo once, at build


def required_by(decls: dict) -> dict:
    """pack -> every pack it requires, directly or not."""
    out = {}
    for name in decls:
        seen, todo = set(), [name]
        while todo:
            for req in decls[todo.pop()].requires:
                if req.name in decls and req.name not in seen:
                    seen.add(req.name)
                    todo.append(req.name)
        out[name] = seen
    return out


def where(row, table) -> str:
    return f"{row['_from']}/{TABLES[table].file}:{row['_line']}"


def stack(order: list, decls: dict) -> Stacked:
    stacked = Stacked({t: {} for t in TABLES})
    requires = required_by(decls)
    for pack in order:
        for table, shape in TABLES.items():
            try:
                rows = read_table(decls[pack].folder / shape.file, shape)
            except PpoError as err:
                stacked.problems += err.problems
                continue
            for row in rows:
                row["_from"] = pack
                key = key_of(row, shape)
                old = stacked.tables[table].get(key)
                if old is not None and old["_from"] != pack:
                    if all(old[c] == row[c] for c in shape.columns):
                        continue
                    if old.get("locked") == "yes":
                        stacked.problems.append(Problem(
                            "policy.locked_row", f"{where(row, table)} changes {'/'.join(key)}, locked by {old['_from']}",
                            "remove that row: a locked row cannot be changed or deleted", (where(row, table),)))
                        continue
                    if old["_from"] not in requires[pack]:
                        stacked.problems.append(Problem(
                            "policy.row_conflict",
                            f"{pack} and {old['_from']} both write {shape.file} row {'/'.join(key)}, "
                            "and neither requires the other",
                            f"edit one of the two packs: drop the row from it, or make {pack} require "
                            f"{old['_from']} (then it replaces the row on purpose); or disable one",
                            (pack, old["_from"])))
                        continue
                    stacked.overrides.append((table, "/".join(key), pack, old["_from"]))
                if is_deletion(row, shape):
                    stacked.tables[table].pop(key, None)
                else:
                    stacked.tables[table][key] = row
    return stacked


def check_cells(stacked: Stacked):
    def bad(table, row, why, fix):
        stacked.problems.append(Problem("policy.bad_table", f"{where(row, table)}: {why}", fix, (where(row, table),)))
    for row in stacked.tables["checks"].values():
        if row["stage"] not in STAGES:
            bad("checks", row, f"stage '{row['stage']}'", f"stage is one of {', '.join(STAGES)}")
        if row["action"] not in ACTIONS:
            bad("checks", row, f"action '{row['action']}'", f"action is one of {', '.join(ACTIONS)}")
    for table in ("checks", "outputs", "plugins"):
        for row in stacked.tables[table].values():
            if row["locked"] not in ("yes", "no"):
                bad(table, row, f"locked '{row['locked']}'", "locked is yes or no")
    for row in stacked.tables["plugins"].values():
        if row["kind"] not in KINDS:
            bad("plugins", row, f"kind '{row['kind']}'", f"kind is one of {', '.join(KINDS)}")
    for row in stacked.tables["flow"].values():
        if row["object"] == "-" and (row["from"] != "-" or row["to"] != "-"):
            bad("flow", row, "from/to without an object", "write the object, or '-' in from and to")
        if row["to"] != "-" and len(split_list(row["to"])) != 1:
            bad("flow", row, f"to '{row['to']}' names more than one state", "to is one state, or '-'")


def code_file(row, decls) -> Path:
    """The file a plugin row points at inside its own pack; None for an importable module name."""
    impl = row["impl"][len("exec:"):] if row["impl"].startswith("exec:") else row["impl"]
    if row["impl"].startswith("exec:") or impl.endswith(".py"):
        return decls[row["_from"]].folder / impl
    return None


def check_names(stacked: Stacked, decls: dict):
    """Every plugin a table names is registered with the right kind, and its file is in its pack."""
    plugins, commands = stacked.tables["plugins"], {k[0] for k in stacked.tables["flow"]}

    def need(name, kind, row, table):
        found = plugins.get((name,))
        if found is None or found["kind"] != kind:
            stacked.problems.append(Problem("policy.unknown_plugin",
                                            f"{where(row, table)} names {kind} '{name}', no pack registers such a {kind}",
                                            f"add '{name}\t{kind}\t<file>' to a plugins.tsv, or fix the name",
                                            (where(row, table),)))
    for row in stacked.tables["checks"].values():
        need(row["check"], "check", row, "checks")
        if row["command"] != "*" and row["command"] not in commands:
            stacked.problems.append(Problem(
                "policy.unknown_command", f"{where(row, 'checks')} binds '{row['check']}' to unknown command '{row['command']}'",
                "bind it to a command some pack's flow.tsv has, or '*'", (where(row, "checks"),)))
    for row in stacked.tables["outputs"].values():
        need(row["output"], "output", row, "outputs")
        command, _, outcome = row["event"].rpartition(".")
        if outcome not in ("passed", "red") or (command != "any" and command not in commands):
            stacked.problems.append(Problem(
                "policy.unknown_event", f"{where(row, 'outputs')} event '{row['event']}'",
                "event is <command>.passed, <command>.red, any.passed or any.red", (where(row, "outputs"),)))
    for row in stacked.tables["flow"].values():
        if row["body"] != "-":
            need(row["body"], "command", row, "flow")
    for row in plugins.values():
        path = code_file(row, decls)
        if path is not None and not path.is_file():
            stacked.problems.append(Problem("policy.plugin_missing", f"{where(row, 'plugins')}: {row['impl']} is not in pack {row['_from']}",
                                            "put the file in the pack's folder, or fix the impl column", (str(path),)))
    writers = [r["name"] for r in plugins.values() if r["kind"] == "audit_writer"]
    if len(writers) > 1:
        stacked.problems.append(Problem("policy.bad_table", f"{len(writers)} audit_writer rows: {writers}",
                                        "keep exactly one audit_writer row"))
    if not writers:
        stacked.warnings.append(Problem("policy.no_audit_writer", "no pack registers an audit_writer: nothing is recorded",
                                        "`ppo enable audit`"))


def check_paths(stacked: Stacked, order: list, decls: dict):
    """No two packs claim one path to write (one folder inside the other counts)."""
    def overlap(a, b):
        return a == b or (b.endswith("/") and a.startswith(b)) or (a.endswith("/") and b.startswith(a))
    claims = [(pack, path) for pack in order for path in decls[pack].writes]
    for i, (a, pa) in enumerate(claims):
        for b, pb in claims[i + 1:]:
            if a != b and overlap(pa, pb):
                stacked.problems.append(Problem("policy.path_conflict", f"{a} writes {pa} and {b} writes {pb}",
                                                f"only one pack may own a path: change the writes of {a} or {b}, "
                                                "or disable one", (a, b)))


def check_facts(stacked: Stacked, order: list, decls: dict):
    """spec 8.4: one pack provides a fact; what a pack reads, some enabled pack provides."""
    provider = {}
    for pack in order:
        for fact in decls[pack].provides:
            if fact in provider:
                stacked.problems.append(Problem("policy.fact_conflict", f"{provider[fact]} and {pack} both provide {fact!r}",
                                                f"only one pack may provide a fact: disable {pack} or {provider[fact]}, "
                                                "or rename the fact in one of them", (provider[fact], pack)))
            provider.setdefault(fact, pack)
    for pack in order:
        missing = [f for f in decls[pack].reads if f not in provider]
        if missing:
            stacked.problems.append(Problem("policy.fact_missing", f"{pack} reads {', '.join(map(repr, missing))}, "
                                            "which no enabled pack provides",
                                            "enable the pack that provides it, or disable " + pack, (pack,)))


ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")     # contract 2.3: an object is a folder name
PPO_FOLDERS = ("policy", "policypack")


def check_built(stacked: Stacked):
    """After the workflow is compiled: what the kernel's step 1 refuses (contract 2.5), found at build."""
    roles = {k[0] for k in stacked.tables["roles"]}
    plugins = stacked.tables["plugins"]

    def problem(code, table, row, why, fix):
        stacked.problems.append(Problem(code, f"{where(row, table)}: {why}", fix, (where(row, table),)))
    for table in ("flow", "checks", "outputs"):
        for row in stacked.tables[table].values():
            unknown = [r for r in split_list(row["roles"]) if r != "*" and r not in roles]
            if unknown:
                problem("policy.unknown_role", table, row, f"roles names {', '.join(unknown)}, which is no role",
                        f"roles are {', '.join(sorted(roles))}: fix the row, or the workflow file's seats")
    for row in stacked.tables["roles"].values():
        if row["superior"] != "-" and row["superior"] not in roles:
            problem("policy.unknown_role", "roles", row, f"superior {row['superior']} is no role", "fix the superior")
    for row in stacked.tables["flow"].values():
        if row["object"] != "-" and (not ID.fullmatch(row["object"]) or row["object"] in PPO_FOLDERS):
            problem("policy.bad_table", "flow", row, f"object {row['object']!r}",
                    "object is a folder name in the governance repo (e.g. tasks), not policy or policypack; or '-'")
        sampler = row["actor"].split(".", 1)[0]
        if row["actor"] != "-" and ("." not in row["actor"] or plugins.get((sampler,), {}).get("kind") != "sampler"):
            problem("policy.bad_table", "flow", row, f"actor {row['actor']!r}",
                    "actor is a path into the sample's parts that starts at a sampler (task_card.card.assignee); or '-'")


def stack_and_check(order: list, decls: dict) -> Stacked:
    stacked = stack(order, decls)
    check_cells(stacked)
    check_names(stacked, decls)
    check_paths(stacked, order, decls)
    check_facts(stacked, order, decls)
    return stacked
