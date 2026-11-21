"""Step 5 · checks_run: the priority stage first; if it blocks, the general stage never runs.

ponytail: one sample serves both stages and only the two built-in stage names exist;
a small priority-only sample and user-added stages come when a pack needs them.
"""
from sherpa.step05_checks_run.runner import rows_for, run_rows


def run(policy, row, sample) -> list:
    results = run_rows(policy, rows_for(policy, "priority", row["command"], sample.caller.role), sample)
    if any(r.blocks for r in results):
        return results
    return results + run_rows(policy, rows_for(policy, "general", row["command"], sample.caller.role), sample)
