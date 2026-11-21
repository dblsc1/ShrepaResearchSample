"""Check fixed_order_declared_waits (dispatch): a task to a seat the workflow fixes a predecessor for waits for a task
of every such seat (--waits-for). waits_for then holds the takeoff until those tasks have ended."""
from sherpa.result import passed, red

from .seats import listed, prefix, seat_of

COMMANDS = ("dispatch",)


def run(sample, params):
    to = seat_of(sample.options.get("to"))
    seat = next((k.split(".", 1)[1] for k in params if k.startswith("after.") and prefix(k.split(".", 1)[1]) == to), None)
    if seat is None:
        return passed()
    tasks = (sample.parts.get("archive") or {}).get("tasks", {})
    waited = [t for t in (sample.options.get("waits_for") or "").split(",") if t and t != "yes"]
    covered = {seat_of((tasks.get(t) or {}).get("assignee")) for t in waited}
    missing = [s for s in listed(params, "after", seat) if prefix(s) not in covered]
    if missing:
        return red("fixed_order.missing_wait", f"a task to {seat} must wait for a task of {', '.join(missing)}",
                   f"dispatch it with --waits-for naming the {', '.join(missing)} task(s)", missing)
    return passed(*waited)
