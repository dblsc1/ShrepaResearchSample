"""Check seat_write_limit (landing, debrief): every file the caller's seat changes is under that seat's paths.

params (from the workflow file): <seat>=<path>,<path>;<seat>=-   "-" means the seat may change nothing.
landing looks at the staged files, debrief at everything committed on the task branch (so a commit that
skipped the hook is caught at debrief). A seat not named in params is not limited by this check."""
from sherpa.result import passed, red, skipped

COMMANDS = ("landing", "debrief")


def run(sample, params):
    seat = sample.caller.role
    if seat not in params:
        return skipped(f"no write limit for seat {seat}")
    allowed = [] if params[seat] in ("-", "", "yes") else [p.rstrip("/") for p in params[seat].split(",") if p]
    git = sample.parts.get("git") or {}
    files = git.get("staged", []) if sample.command == "landing" else git.get("branch_files")
    if files is None:
        return skipped("task branch or parent branch missing: nothing to compare")
    outside = [f for f in files if not any(f == a or f.startswith(a + "/") for a in allowed)]
    if outside:
        where = ", ".join(a + "/" for a in allowed) or "nothing (read-only)"
        return red("seat_write_limit.outside_seat_paths", f"seat {seat} may change only {where}: {', '.join(outside)}",
                   "take those files out of the commit, or ask for the seat's limit to be changed in the workflow", outside)
    return passed(*files)
