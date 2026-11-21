"""F4 · for `sherpa next`: which commands can this caller run in this state?"""
from sherpa.step03_flow_control.transition_check import allowed_from, role_allowed


def runnable(policy, role: str, state: str) -> list:
    # Every caller is inside a workspace, where init always stops with init.workspace_exists.
    return [command for command, row in policy.flow.items()
            if command != "init" and role_allowed(row, role)
            and (row["object"] == "-" or state in allowed_from(row))]
