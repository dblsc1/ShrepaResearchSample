"""Hashes stamped on every Result and audit row: which kernel and which policy packs ran."""
import hashlib
from functools import lru_cache
from pathlib import Path

KERNEL_DIR = Path(__file__).resolve().parent.parent


def tree_hash(roots, files=()) -> str:
    """sha256 over (relative path, bytes) of every file under the given dirs, sorted, then of
    the extra files (by name)."""
    h = hashlib.sha256()
    for root in roots:
        root = Path(root)
        for f in sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
            h.update(f.relative_to(root).as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
    for f in sorted(Path(f) for f in files):
        h.update(f.name.encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()[:16]


@lru_cache(maxsize=1)
def kernel_hash() -> str:
    return tree_hash([KERNEL_DIR])
