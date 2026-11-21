"""Sampler task_card: the --task's card, its state and its worklog. Read-only."""
import json
from pathlib import Path

NO_STATE = "-"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def sample(request) -> dict:
    if not request.task:
        return {"card": None, "state": NO_STATE, "worklog": None}
    folder = Path(request.governance_repo) / "tasks" / request.task
    state = read_json(folder / "state.json") or {}
    worklog = folder / "worklog.md"
    text = worklog.read_text(encoding="utf-8") if worklog.is_file() else None
    return {"card": read_json(folder / "task.json"),
            "state": state.get("state", NO_STATE),
            "worklog": None if text is None else {"first_line": (text.splitlines() or [""])[0],
                                                  "lines": len(text.splitlines())}}
