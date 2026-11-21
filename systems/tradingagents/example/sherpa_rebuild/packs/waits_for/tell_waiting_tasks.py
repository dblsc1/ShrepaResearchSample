"""Output tell_waiting_tasks (receipt, cancel-confirm): name the tasks that may now take off.

ponytail: no transport yet -- the note goes into the Result, like notify's."""
from .waited import waited


def apply(sample, params, outcome, task):
    ended = set(params.get("ended", "closed,cancelled").split(","))
    tasks = (sample.parts.get("archive") or {}).get("tasks", {})
    now = "cancelled" if sample.command == "cancel-confirm" else "closed"            # what this command just did
    state = lambda t: now if t == task else (tasks.get(t) or {}).get("state")       # archive is from before it
    free = sorted(f"{t} ({row.get('assignee')})" for t, row in tasks.items()
                  if task in waited(row) and all(state(w) in ended for w in waited(row)))
    return f"may take off now: {', '.join(free)} (no transport configured)" if free else None
