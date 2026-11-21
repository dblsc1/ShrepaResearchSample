"""Command body dispatch: compute the new task's card. Writes nothing itself;
step 10 writes the files after sample verification. The id comes from the frozen archive sample,
so two dispatches racing for one id end in sample.changed for the slower one.

The card keeps every option the upper typed (`options`): packs read their own from there
(waits_for reads --waits-for), so the unit never needs to know which packs are on."""
import json
import time

from sherpa.result import kernel_red

OWN_OPTIONS = ("inst", "task", "json", "to", "goal", "scope", "parent")

def new_task_id(sample) -> str:
    taken = set((sample.parts.get("archive") or {}).get("tasks", {}))
    day = time.strftime("%y%m%d")
    n = 1
    while f"T-{day}-{n}" in taken:
        n += 1
    return f"T-{day}-{n}"


def run(sample, registry_view):
    missing = [f"--{n}" for n in ("to", "goal", "scope") if sample.options.get(n) in (None, "", "yes")]
    if missing:                       # the task_card_check pack says it better; this holds without it
        return {"red": kernel_red("dispatch", "classic_lifecycle.dispatch_incomplete", f"dispatch needs {', '.join(missing)}",
                                  'sherpa dispatch --to <license id> --goal "<one sentence>" --scope <path>,<path>',
                                  missing)}
    task = new_task_id(sample)
    git = sample.parts.get("git") or {}
    card = {"schema_version": 1, "task": task, "goal": sample.options["goal"],
            "assignee": sample.options["to"], "issued_by": sample.caller.inst,
            "parent": sample.options.get("parent"),
            "options": {k: v for k, v in sample.options.items() if k not in OWN_OPTIONS},
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "writable": [p for p in sample.options["scope"].split(",") if p],
            "parent_branch": git.get("branch") or "main", "branch": f"task/{task}",
            "worktree": f"sherpa/worktrees/{task}"}     # the task's own folder (constitution 8)
    return {"task": task,
            "files": {f"tasks/{task}/task.json": json.dumps(card, ensure_ascii=False, indent=1) + "\n"}}
