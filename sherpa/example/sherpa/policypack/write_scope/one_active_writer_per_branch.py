"""One active writer per branch (the write_scope pack, locked). Another task on the same
branch, in an active state (params: active=<states>), held by someone else -> red."""
from sherpa.result import passed, red, skipped

COMMANDS = ("*",)


def run(sample, params):
    card = (sample.parts.get("task_card") or {}).get("card")
    if not card or not card.get("branch"):
        return skipped("no task branch in this command")
    active = set(params.get("active", "working").split(","))
    tasks = (sample.parts.get("archive") or {}).get("tasks", {})
    others = [t for t, info in tasks.items()
              if t != sample.task and info.get("branch") == card["branch"]
              and info.get("state") in active and info.get("assignee") != card.get("assignee")]
    if others:
        return red("write_scope.one_active_writer", f"branch {card['branch']} is also being written by {', '.join(others)}",
                   "give this task its own branch, or wait until the other task leaves "
                   f"{'/'.join(sorted(active))}", others)
    return passed(card["branch"])
