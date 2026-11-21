"""The write segment lock of the governance repo: one writer at a time, retried with backoff.

An flock on .lock: the kernel drops it when the holder exits, even by crashing, so a dead
holder never blocks anyone. The holder writes its pid into the file and empties it on a clean
release; finding a pid there on entry means the last holder died inside the write segment, and
that is reported (lock.stale_taken) so it lands in the audit trail.
"""
import fcntl
import os
import time
from contextlib import contextmanager
from pathlib import Path

LOCK_FILE = ".lock"
WAIT_SECONDS = 10.0


class LockBusy(Exception):
    pass


def wait_for(fd, how, path):
    delay, deadline = 0.02, time.monotonic() + WAIT_SECONDS
    while True:
        try:
            return fcntl.flock(fd, how | fcntl.LOCK_NB)
        except BlockingIOError:
            if time.monotonic() > deadline:
                raise LockBusy(f"{path} held for over {WAIT_SECONDS}s")
            time.sleep(delay)
            delay = min(delay * 2, 0.5)


@contextmanager
def policy_read_lock(repo):
    """Shared: readers of policy/ wait while ppo (or a write segment) holds .lock. No lock file, no wait."""
    path = Path(repo) / LOCK_FILE
    try:
        fd = os.open(path, os.O_RDONLY)
    except FileNotFoundError:
        yield
        return
    try:
        wait_for(fd, fcntl.LOCK_SH, path)
        yield
    finally:
        os.close(fd)                                # closing drops the lock


@contextmanager
def governance_lock(repo):
    """Yields a list of notes; it holds one string if the previous holder died holding the lock."""
    path = Path(repo) / LOCK_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        wait_for(fd, fcntl.LOCK_EX, path)
        left = os.pread(fd, 64, 0).decode(errors="replace").split()
        notes = [f"previous holder pid {left[0]} died inside the write segment"] if left else []
        os.ftruncate(fd, 0)
        os.pwrite(fd, f"{os.getpid()} {time.time()}".encode(), 0)
        try:
            yield notes
        finally:
            os.ftruncate(fd, 0)
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)
