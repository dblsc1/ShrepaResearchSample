"""Check dispatched_enough (debrief): the caller has dispatched at least min tasks for this one.
A task counts when the caller issued it and it names this task as --parent or names none. params: min=<number>. No min: skipped.

ponytail: a caller holding two tasks counts the same children for both when none names --parent; require --parent when that matters."""
from sherpa.result import passed, red, skipped

COMMANDS = ("debrief",)


def run(sample, params):
    if not params.get("min", "").isdigit():
        return skipped("no min: set it in the workflow file, [policy.must_decompose] params = \"min=1\"")
    tasks = (sample.parts.get("archive") or {}).get("tasks", {})
    sent = sorted(t for t, row in tasks.items() if row.get("issued_by") == sample.caller.inst
                  and row.get("parent") in (None, "", sample.task))
    if len(sent) < int(params["min"]):
        return red("must_decompose.nothing_dispatched", f"{sample.caller.inst} dispatched {len(sent)} task(s) for {sample.task}; at least {params['min']} are required",
                   "split the work and dispatch it before handing this task back", sent)
    return passed(*sent)
