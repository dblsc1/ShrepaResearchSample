"""Check author_is_not_reviewer (dispatch): a review task does not go to whoever did the work.

A review is a task of its own: `sherpa dispatch --to <reviewer> --reviews T-1,T-2 --waits-for T-1,T-2`.
The reviewed tasks must exist, and none of them may be assigned to the reviewer."""
from sherpa.result import passed, red, skipped

COMMANDS = ("dispatch",)


def run(sample, params):
    reviewed = [t for t in (sample.options.get("reviews") or "").split(",") if t and t != "yes"]
    if not reviewed:
        return skipped("not a review task (no --reviews)")
    tasks = (sample.parts.get("archive") or {}).get("tasks", {})
    unknown = [t for t in reviewed if t not in tasks]
    if unknown:
        return red("review_rules.unknown_task", f"--reviews names {', '.join(unknown)}, which do not exist",
                   "review only tasks already dispatched", unknown)
    own = [t for t in reviewed if tasks[t].get("assignee") == sample.options.get("to")]
    if own:
        return red("review_rules.author_is_reviewer", f"{sample.options.get('to')} did {', '.join(own)} and would review it",
                   "send the review to someone else", own)
    return passed(*reviewed)
