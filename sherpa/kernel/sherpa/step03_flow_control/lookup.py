"""F1 · step 3: the flow-table row of this command.

Not in the flow table: red flow.unknown_command -- except when only base-group packs are on
(ppo's no_guarantees): then the command passes with one warning and does nothing else, a card
reader with no policy (human ruling 2026-11-03). The caller was already identified in step 2.
"""
from dataclasses import replace

from sherpa.result import KernelStop, kernel_red

STEP = "step03_flow_control"


def lookup(policy, command: str):
    row = policy.flow.get(command)
    if row is not None:
        return row
    if policy.no_guarantees:
        note = next((w for w in policy.warnings if w.error_code == "policy.no_guarantees"), None)
        raise KernelStop(replace(kernel_red(
            STEP, "policy.no_guarantees",
            f"'{command}' is in no flow table, so nothing was checked, recorded or changed; "
            + (note.reason if note else "only the base policy pack is on: sherpa guarantees nothing here"),
            note.fix if note else "turn feature packs on with ppo, then rebuild the policy", [command]),
            status="skip", action="warn"))
    raise KernelStop(kernel_red(
        STEP, "flow.unknown_command", f"'{command}' is not in the flow table",
        f"run one of: {', '.join(policy.flow)}", [command]))
