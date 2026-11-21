"""F2 · called by step 6, always (a floor rule written into the kernel): may this caller make
this move right now? Role, current state, task-card party.

Reads only the frozen sample. The same row drives F3 (advance), so judging a move and
writing it never drift apart. The state is the kernel's own read (sample.state); the party
comes from the sample's parts, at the path the row's actor column names.
"""
from sherpa.result import passed, red
from sherpa.step01_policy_load.tables import role_allowed, split_list

NO_STATE = "-"


def allowed_from(row) -> tuple:
    return (NO_STATE,) if row["from"] == "-" else split_list(row["from"])


def actor_value(path: str, parts):
    """The value at an actor path ('task_card.card.assignee') in the sample's parts, or None."""
    value = parts
    for key in path.split("."):
        value = value.get(key) if hasattr(value, "get") else None
    return value


def state_of(row, sample) -> str:
    """The state the kernel read itself in step 4 (read_state), not a sampler's copy."""
    return sample.state if row["object"] != "-" else NO_STATE


def transition_check(row, sample):
    command, caller = row["command"], sample.caller
    if not role_allowed(row, caller.role):
        return red("builtin.role", f"{command} is for {row['roles']}; {caller.inst} is {caller.role}",
                   f"ask a {row['roles']} to run {command}", [caller.inst])
    if row["object"] == "-":
        return passed(command)
    state = state_of(row, sample)
    if state not in allowed_from(row):
        what = sample.task or f"no --task given ({row['object']})"
        return red("builtin.transition", f"{command} needs state {row['from']}; {what} is {state}",
                   "run `sherpa next` to see what this state allows", [sample.task or row["object"]])
    party = row["actor"]
    who = actor_value(party, sample.parts) if party != "-" else caller.inst
    if who != caller.inst:
        return red("builtin.actor", f"{command} is for the {party.rpartition('.')[2]} of {sample.task} ({who}); "
                                    f"caller is {caller.inst}",
                   f"ask {who} to run it", [sample.task])
    return passed(command)
