"""Sampler reopen_count: how many times each task was sent back, and the seat of each license prefix. Read-only.
The counts are the files reopens/<task> in the governance repo (written by record_reopen); the seats come from
the built roles table (policy/roles.tsv). count and assignee_role describe the --task, if there is one."""
import json
from pathlib import Path


def sample(request) -> dict:
    repo = Path(request.governance_repo)
    roles = {}
    table = repo / "policy" / "roles.tsv"
    if table.is_file():
        rows = [line.split("\t") for line in table.read_text(encoding="utf-8").splitlines()
                if line and not line.startswith("#")]                 # built tables start with a comment line
        for row in rows[1:]:
            cells = dict(zip(rows[0], row))
            roles[cells.get("prefix")] = cells.get("role")
    folder = repo / "reopens"
    reopens = {f.name: int(f.read_text().strip() or 0) for f in folder.iterdir() if f.is_file()} if folder.is_dir() else {}
    card_file = repo / "tasks" / (request.task or "-") / "task.json"
    card = json.loads(card_file.read_text(encoding="utf-8")) if request.task and card_file.is_file() else {}
    return {"count": reopens.get(request.task, 0), "assignee_role": roles.get((card.get("assignee") or "").split("-", 1)[0]),
            "roles": roles, "reopens": reopens}
