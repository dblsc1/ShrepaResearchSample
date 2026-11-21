"""Check reopens_under_limit (reopen, dispatch): a seat gets at most n+1 rounds from the same upper.
params (from the workflow file): <seat>=<n>;...  n = how many times the seat's work may be sent back. A round is
a task the upper dispatched to the seat, or one reopen of such a task; cancelled tasks keep the rounds they had.
So a new task to the seat cannot start round n+2 (pairing: ChatDev's loop counter counts per node, not per task).
A seat not named is not limited."""
from sherpa.result import passed, red, skipped

COMMANDS = ("reopen", "dispatch")


def run(sample, params):
    part = sample.parts.get("reopen_count") or {}
    roles, reopens = part.get("roles", {}), part.get("reopens", {})
    if sample.command == "dispatch":
        seat = roles.get((sample.options.get("to") or "").split("-", 1)[0])
    else:
        seat = part.get("assignee_role")
    if seat not in params:
        return skipped(f"no reopen limit for seat {seat}")
    limit = int(params[seat])
    tasks = (sample.parts.get("archive") or {}).get("tasks", {})
    mine = [t for t, row in tasks.items() if row.get("issued_by") == sample.caller.inst
            and roles.get((row.get("assignee") or "").split("-", 1)[0]) == seat]
    rounds = sum(1 + reopens.get(t, 0) for t in mine)
    if rounds > limit:
        return red("reopen_limit.limit_reached",
                   f"seat {seat} has had {rounds} round(s) from {sample.caller.inst} ({', '.join(sorted(mine))}); it allows {limit + 1}",
                   "take receipt (or cancel) and move on to the next step", sorted(mine))
    return passed(*mine)
