"""Every file the worker changes is inside the card's writable paths.

landing: the staged files (run by the pre-commit hook).
debrief: the files committed on the task branch since it left its parent. This one does not
trust the client: a commit that skipped the hook (--no-verify, -n, a hooksPath trick) is caught here.

Files that set an agent's own rules (settings and hooks, sub-agent definitions, MCP servers,
instruction files) are forbidden at any depth, even inside the write scope: a worker would be
rewriting its own fence, and after a merge a planted hook would run in the person's own sessions.
The one list of them is the task_card_check pack's agent_rule_files.py (this pack requires task_card_check).
"""
import importlib.util
from pathlib import Path

from sherpa.result import passed, red, skipped

COMMANDS = ("landing", "debrief")


def from_task_card(name: str):
    """A helper file of the task_card_check pack, installed beside this pack."""
    path = Path(__file__).resolve().parents[1] / "task_card_check" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"sherpa_pack_task_card_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


agent_rules = from_task_card("agent_rule_files").agent_rules


def inside(path: str, writable) -> bool:
    return any(path == w.rstrip("/") or path.startswith(w.rstrip("/") + "/") for w in writable)


def run(sample, params):
    card = (sample.parts.get("task_card") or {}).get("card")
    if not card:
        return skipped("no task card")
    git = sample.parts.get("git") or {}
    writable = card.get("writable", [])
    if sample.command == "landing":
        files, code, what = git.get("staged", []), "write_scope.staged_outside_writable", "staged"
        forbidden_code, fix = "write_scope.staged_in_forbidden", "git restore --staged {files}"
    else:
        files, code, what = git.get("branch_files"), "write_scope.committed_outside_writable", "committed on the task branch"
        forbidden_code = "write_scope.committed_in_forbidden"
        fix = "take {files} out of the task branch (git revert, or a new commit undoing them)"
        if files is None:
            return skipped("task branch or parent branch missing: nothing to compare")
    ruled = [p for p in files if agent_rules(p)]
    if ruled:
        return red(forbidden_code, f"{what}: agent rule files ({', '.join(ruled)}) are never a worker's to change",
                   f"{fix.format(files=' '.join(ruled))}; {card.get('issued_by')} changes them by hand if needed",
                   ruled)
    outside = [p for p in files if not inside(p, writable)]
    if outside:
        return red(code, f"{what} outside {', '.join(writable) or '(nothing writable)'}: {', '.join(outside)}",
                   f"{fix.format(files=' '.join(outside))}, or ask {card.get('issued_by')} to widen the scope",
                   outside)
    return passed(*files)
