"""Check dispatched_tasks_ended (debrief): every task the caller dispatched has ended.
Reads the runtime facts only (the archive): no count is assumed. params: ended=<states>.

ponytail: every task the caller dispatched, as the human put it ("他派出的单都已结束"); a lower holding
two tasks of its own waits for the lowers of both. Narrow it to the card's children (parent) when
someone needs that."""
from sherpa.result import passed, red

COMMANDS = ("debrief",)


def run(sample, params):
    ended = set(params.get("ended", "closed,cancelled").split(","))
    tasks = (sample.parts.get("archive") or {}).get("tasks", {})
    open_ones = sorted(t for t, row in tasks.items() if row.get("issued_by") == sample.caller.inst
                       and row.get("state") not in ended)
    if open_ones:
        return red("parallel_wait_all.tasks_not_ended", f"{sample.caller.inst} dispatched {', '.join(open_ones)}, not ended yet",
                   "take receipt of them (or cancel them), then debrief", open_ones)
    return passed()
