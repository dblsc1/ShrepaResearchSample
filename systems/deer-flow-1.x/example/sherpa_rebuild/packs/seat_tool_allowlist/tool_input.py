"""Sampler tool_input (tool-call): every disk read the tool rules need, done here because a check reads only the
sample (contract 3.1). Read-only.

  sha256, chars, cut, whole   the whole tool input, and the hash of what in it changes what runs (call_id.bound), computed here. From --input-file when the hook
                              sent one (it must be <governance repo>/tool_inputs/<32 hex>.json, and cutting it must
                              give --input exactly), else from --input (typed without the hook: that is all of it).
                              sha256 None, and why, when the file is not the hook's or does not fit.
  paths                       realpath ('..' and symlinks resolved) of: cwd (the hook asks from the worktree), the
                              governance repo, the task card's worktree ('' when none), and each input field
                              file_path / notebook_path / path that is a string or missing (missing or '' = '.')
Step 10 re-runs this sampler: a link or file swapped between judging and writing gives sample.changed."""
import json
import os
import re
from pathlib import Path

from .call_id import bound, canonical, cut, sha256

PATH_FIELDS = ("file_path", "notebook_path", "path")
INPUT_FILE = re.compile(r"[0-9a-f]{32}\.json")


def card_worktree(request) -> str:
    path = Path(request.governance_repo) / "tasks" / request.task / "task.json"
    if not request.task or not path.is_file():
        return ""
    worktree = json.loads(path.read_text(encoding="utf-8")).get("worktree")
    return os.path.realpath(os.path.join(request.home, worktree)) if worktree else ""


def whole_input(request, given) -> tuple:
    """(the whole input, why it cannot be trusted or '')."""
    file = request.options.get("input_file", "")
    if not file or file == "yes":
        return given, ""
    folder = os.path.realpath(os.path.join(request.governance_repo, "tool_inputs"))
    path = os.path.realpath(file if os.path.isabs(file) else os.path.join(request.cwd, file))
    if os.path.dirname(path) != folder or not INPUT_FILE.fullmatch(os.path.basename(path)) or not os.path.isfile(path):
        return None, "--input-file is not a file the tool hook wrote (<governance repo>/tool_inputs/<32 hex>.json)"
    try:
        whole = json.loads(Path(path).read_text(encoding="utf-8"))
    except ValueError:
        return None, "--input-file is not JSON"
    if not isinstance(whole, dict) or not isinstance(given, dict) or cut(whole) != (given, ""):
        return None, "--input-file does not fit --input"
    return whole, ""


def sample(request) -> dict:
    if request.command != "tool-call":
        return {}
    try:
        given = json.loads(request.options.get("input", "{}"))
    except ValueError:
        given = None
    whole, why = whole_input(request, given)
    text = None if why else canonical(whole)
    fields = {}
    for field in PATH_FIELDS:
        value = given.get(field) if isinstance(given, dict) else None
        if value is None or isinstance(value, str):
            value = value or "."
            fields[field] = os.path.realpath(value if os.path.isabs(value) else os.path.join(request.cwd, value))
    return {"sha256": None if why else sha256(canonical(bound(request.options.get("tool", ""), whole))), "why": why, "chars": len(text) if text else 0,
            "cut": not why and whole != given, "whole": None if why else whole,
            "paths": {"cwd": os.path.realpath(request.cwd), "governance_repo": os.path.realpath(request.governance_repo),
                      "worktree": card_worktree(request), "fields": fields}}
