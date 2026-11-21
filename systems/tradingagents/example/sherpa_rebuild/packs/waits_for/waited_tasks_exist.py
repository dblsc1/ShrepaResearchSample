"""Check waited_tasks_exist (dispatch): every task named in --waits-for exists already."""
from sherpa.result import passed, red

COMMANDS = ("dispatch",)


def run(sample, params):
    names = [t for t in (sample.options.get("waits_for") or "").split(",") if t and t != "yes"]
    tasks = (sample.parts.get("archive") or {}).get("tasks", {})
    unknown = [t for t in names if t not in tasks]
    if unknown:
        return red("waits_for.unknown_task", f"--waits-for names {', '.join(unknown)}, which do not exist",
                   "wait only for tasks already dispatched: --waits-for T-...,T-...", unknown)
    return passed(*names)
