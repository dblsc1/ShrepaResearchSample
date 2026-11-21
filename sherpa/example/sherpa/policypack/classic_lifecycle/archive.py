"""Sampler archive: every task in the governance repo, one line each. Read-only.

ponytail: scans every task folder per command; keep an index file when tasks reach thousands.
ponytail: one stamp covers every task, so another task changing state in the ~100 ms between
sampling and writing reds this command sample.changed (run it again). When many agents write at
once, stamp only what a command depends on (its own branch's tasks, the id set).
"""
import json
from pathlib import Path


def sample(request) -> dict:
    tasks = {}
    for card_file in sorted((Path(request.governance_repo) / "tasks").glob("*/task.json")):
        card = json.loads(card_file.read_text(encoding="utf-8"))
        state_file = card_file.with_name("state.json")
        state = json.loads(state_file.read_text(encoding="utf-8"))["state"] if state_file.is_file() else "-"
        tasks[card_file.parent.name] = {"state": state, "assignee": card.get("assignee"),
                                        "issued_by": card.get("issued_by"),
                                        "branch": card.get("branch"), "parent": card.get("parent"),
                                        "options": card.get("options") or {}}
    return {"tasks": tasks}
