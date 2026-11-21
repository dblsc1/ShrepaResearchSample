"""Check waited_tasks_ended (takeoff): the tasks this one waits for have ended. params: ended=<states>."""
from sherpa.result import passed, red

from .waited import waited

COMMANDS = ("takeoff",)


def run(sample, params):
    ended = set(params.get("ended", "closed,cancelled").split(","))
    card = (sample.parts.get("task_card") or {}).get("card")
    tasks = (sample.parts.get("archive") or {}).get("tasks", {})
    waiting = [t for t in waited(card) if (tasks.get(t) or {}).get("state") not in ended]
    if waiting:
        return red("waits_for.not_ended", f"{sample.task} waits for {', '.join(waiting)}, not ended yet",
                   "take off after those tasks are closed (`sherpa next` shows when)", waiting)
    return passed()
