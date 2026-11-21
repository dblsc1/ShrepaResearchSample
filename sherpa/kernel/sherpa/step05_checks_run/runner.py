"""Run check rows: in parallel, merged back in table order. Shared by steps 5 and 6."""
from concurrent.futures import ThreadPoolExecutor

from sherpa.registry import registry
from sherpa.result import STATUSES, CheckResult, red, stamped
from sherpa.step01_policy_load.tables import parse_params, role_allowed


def rows_for(policy, stage: str, command: str, role: str) -> list:
    """A row whose roles column leaves out the caller's role is not run and not recorded."""
    return [r for r in policy.checks
            if r["stage"] == stage and r["command"] in (command, "*") and role_allowed(r, role)]


def call(function, sample, params) -> CheckResult:
    try:
        result = function(sample, params)
    except Exception as err:                      # a broken check reds, it never crashes the kernel
        return red("check.crashed", f"{type(err).__name__}: {err}", "fix the check module")
    if not isinstance(result, CheckResult) or result.status not in STATUSES:
        return red("check.bad_output", f"returned {result!r}", "return passed(), skipped() or red()")
    return result


def run_rows(policy, rows, sample) -> list:
    if not rows:
        return []
    jobs = []
    for row in rows:
        if row["action"] == "off":
            jobs.append(None)
        else:
            jobs.append((registry.load(policy, row["check"], "check", sample.command), parse_params(row["params"])))
    with ThreadPoolExecutor(max_workers=min(8, len(rows))) as pool:
        futures = [None if job is None else pool.submit(call, job[0], sample, job[1]) for job in jobs]
    out = []
    for row, future in zip(rows, futures):
        result = (CheckResult("", "", "skip", "check.off", "switched off in checks.tsv")
                  if future is None else future.result())
        out.append(stamped(result, row["check"], row["stage"], row["action"]))
    return out
