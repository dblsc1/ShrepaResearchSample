"""A folder's hash as the lock records it (contract 2.4): every file under the folder, sorted by its
relative path, __pycache__ skipped; sha256 over "relative path \\0 bytes \\0" for each; first 16 hex."""
import hashlib
from pathlib import Path


def tree_hash(folder) -> str:
    folder, h = Path(folder), hashlib.sha256()
    # sorted as path objects, the way the kernel sorts them (a/b before a-b), so both sides agree
    for f in sorted(p for p in folder.rglob("*") if p.is_file() and "__pycache__" not in p.parts):
        h.update(f.relative_to(folder).as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
    return h.hexdigest()[:16]
