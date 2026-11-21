"""Check fixed_order_required_lowers (debrief): the caller has a closed (taken receipt of) task of every seat the workflow
requires of it. A cancelled task does not count: parallel_wait_all counts it as ended, so without this an upper could
dispatch a required lower, cancel it and hand back without the hand-off (zumi 11-18, mero #18874)."""
from sherpa.result import passed, red

from .seats import listed, prefix, seat_of

COMMANDS = ("debrief",)


def run(sample, params):
    needed = listed(params, "needs", sample.caller.role)
    if not needed:
        return passed()
    tasks = (sample.parts.get("archive") or {}).get("tasks", {})
    dispatched = {seat_of(row.get("assignee")) for row in tasks.values() if row.get("issued_by") == sample.caller.inst
                  and row.get("state") == "closed"}
    missing = [s for s in needed if prefix(s) not in dispatched]
    if missing:
        return red("fixed_order.missing_lower", f"{sample.caller.role} has no closed task of {', '.join(missing)}",
                   f"dispatch to {', '.join(missing)} and take receipt before handing this task back (a cancelled task does not count)",
                   missing)
    return passed()
