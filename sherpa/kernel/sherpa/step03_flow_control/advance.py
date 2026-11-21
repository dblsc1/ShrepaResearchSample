"""F3 · called by step 10 under the governance lock, after sample verification: write `to`.
And read_state, its mirror, called by step 4: the one reader of object state.

The only writer of object state. Writing reads nothing: step 10 re-read the state just before
(sample verification), so a state that moved has already been caught.
"""
import json
import os
import time
from pathlib import Path

NO_STATE = "-"


def object_dir(archive, obj: str, ident: str) -> Path:
    """The flow row's object column is the object's folder in the governance repo (e.g. tasks)."""
    return Path(archive) / obj / ident


def read_state(archive, row, ident: str) -> str:
    """The object's state as F3 wrote it ('-' when there is none). Step 4 reads it into the sample:
    the kernel judges moves on the state it writes itself, never on a pack's sampler (K4)."""
    if row["object"] == "-" or not ident:
        return NO_STATE
    path = object_dir(archive, row["object"], ident) / "state.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))["state"] if path.is_file() else NO_STATE
    except (ValueError, KeyError, TypeError) as err:
        raise ValueError(f"{path} is broken: {err}")


def advance(archive, row, inst: str, ident: str):
    """Write row['to'] as the object's state. Returns the path written, or None."""
    if row["object"] == "-" or row["to"] == "-" or not ident:
        return None
    path = object_dir(archive, row["object"], ident) / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"state": row["to"], "by": inst, "command": row["command"],
              "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    temporary = path.with_name(".state.json.tmp")
    temporary.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(temporary, path)                       # never a half-written state
    return path
