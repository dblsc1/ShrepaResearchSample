"""Step 6 · builtin_checks: the two floor rules first, then the tables' stage=builtin rows.

The floor (human 2026-10-30 and 2026-10-31: "must be in the kernel, may not be switched off") is
code here, not a table row, so no policy pack can drop it -- not even one with nothing else in it,
and no roles column can leave a caller out of it:
  caller_identified             the sample carries an identified caller (a fuse behind step 2)
  transition_is_in_flow_table   role, current state and task-card party fit the flow-table row (F2)
The check names stay what they were as table rows, so audit trails and replays read the same.
"""
from sherpa.result import stamped
from sherpa.step03_flow_control.transition_check import transition_check
from sherpa.step05_checks_run.runner import call, rows_for, run_rows
from sherpa.step06_builtin_checks.caller_identified import caller_identified

FLOOR = (("caller_identified", lambda row, sample: caller_identified(sample)),
         ("transition_is_in_flow_table", transition_check))


def run(policy, row, sample) -> list:
    floor = [stamped(call(lambda s, p, f=f: f(row, s), sample, {}), name, "builtin", "block") for name, f in FLOOR]
    return floor + run_rows(policy, rows_for(policy, "builtin", row["command"], sample.caller.role), sample)
