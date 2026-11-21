"""Check open_lowers_under_limit (dispatch): the caller has fewer than n tasks out that have not ended.
params: n=<number> (set by the workflow file), ended=<states>. No n: skipped."""
from sherpa.result import passed, red, skipped

COMMANDS = ("dispatch",)


def run(sample, params):
    if not params.get("n", "").isdigit():
        return skipped("no n: set it in the workflow file, [policy.max_open_lowers] params = \"n=1\"")
    limit, ended = int(params["n"]), set(params.get("ended", "closed,cancelled").split(","))
    tasks = (sample.parts.get("archive") or {}).get("tasks", {})
    out = sorted(t for t, row in tasks.items() if row.get("issued_by") == sample.caller.inst
                 and row.get("state") not in ended)
    if len(out) >= limit:
        return red("max_open_lowers.limit_reached", f"{sample.caller.inst} has {len(out)} task(s) out ({', '.join(out)}); "
                   f"the limit is {limit}", "take receipt of one (or cancel it), then dispatch", out)
    return passed()
