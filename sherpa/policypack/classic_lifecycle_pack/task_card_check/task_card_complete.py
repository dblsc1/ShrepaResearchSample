"""dispatch: the card's must-have fields are there and sane before it is written.

The write scope becomes the worker's Edit/Write rules, so it may only name paths inside the
project and never sherpa's own files (sherpa/, the governance repo), .git/, or the agent's own
rules (.claude/ at any depth, CLAUDE.md, AGENTS.md, .mcp.json): a worker must not rewrite its fence.
"""
from pathlib import Path, PurePosixPath

from sherpa.result import passed, red

from .agent_rule_files import agent_rules

COMMANDS = ("dispatch",)
REQUIRED = ("to", "goal", "scope")
ID_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-")


def bad_scope(entry: str, governance: str) -> bool:
    path = PurePosixPath(entry)
    parts = path.parts
    return (not parts or path.is_absolute() or ".." in parts or entry.strip("./") == ""
            or any(c in entry for c in "*?[]{}") or parts[0] in (".git", "sherpa") or agent_rules(entry)
            or bool(governance) and (str(path) + "/").startswith(governance.rstrip("/") + "/"))


def run(sample, params):
    missing = [f"--{name}" for name in REQUIRED if not sample.options.get(name) or sample.options[name] == "yes"]
    if missing:
        return red("task_card_check.missing_required", f"dispatch needs {', '.join(missing)}",
                   'sherpa dispatch --to <license id> --goal "<one sentence>" --scope <path>,<path>', missing)
    if sample.options["goal"].lstrip().startswith(("<", "TODO", "...")):
        return red("task_card_check.placeholder_left", f"--goal is still a placeholder: {sample.options['goal']}",
                   "write the goal as one plain sentence", ["--goal"])
    to = sample.options["to"]
    if not to[:1].isalnum() or not set(to) <= ID_CHARS:
        return red("task_card_check.bad_assignee", f"--to {to!r} is not a license id", "pass --to <license id>, e.g. WORKER-01", [to])
    try:
        governance = Path(sample.governance_repo).resolve().relative_to(Path(sample.cwd).resolve()).as_posix()
    except ValueError:
        governance = ""                                   # governance repo outside the checkout
    bad = [e for e in sample.options["scope"].split(",") if e and bad_scope(e, governance)]
    if bad:
        return red("task_card_check.bad_scope", f"--scope may only name paths inside the project, not {', '.join(bad)}",
                   "use relative paths like src/ or README.md; no .., no globs, nothing under .git/ or sherpa/, no .claude/ or CLAUDE.md",
                   bad)
    return passed(to)
