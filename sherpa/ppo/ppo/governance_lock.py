"""The lock ppo shares with the kernel (contract 5): an exclusive flock on <governance repo>/.lock.
On taking it, empty the file and write our pid at its start; empty it again before a clean release.
A pid found on entry means the last holder died holding it. ppo holds it while it writes policy/,
so the kernel never reads half-written tables."""
import fcntl
import os
import time
from contextlib import contextmanager
from pathlib import Path

from ppo import PpoError, Problem

LOCK_FILE = ".lock"
WAIT_SECONDS = 10.0


_HELD = set()          # locks this process holds: a nested take is a no-op (flock would wait on itself)


@contextmanager
def governance_lock(repo):
    """Yields notes: one line when the previous holder died holding the lock.
    ppo holds it for every change to policy/ and policypack/: the kernel reads both under a shared lock."""
    path = Path(repo).resolve() / LOCK_FILE
    if path in _HELD:
        yield []
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        delay, deadline = 0.02, time.monotonic() + WAIT_SECONDS
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() > deadline:
                    raise PpoError(Problem("lock.busy", f"{path} held for over {WAIT_SECONDS:.0f}s",
                                           "a sherpa command or another ppo is writing; run ppo again"))
                time.sleep(delay)
                delay = min(delay * 2, 0.5)
        left = os.pread(fd, 64, 0).decode(errors="replace").split()
        notes = [f"previous holder pid {left[0]} died holding {path}"] if left else []
        os.ftruncate(fd, 0)
        os.pwrite(fd, f"{os.getpid()} {time.time()}".encode(), 0)
        _HELD.add(path)
        try:
            yield notes
        finally:
            _HELD.discard(path)
            os.ftruncate(fd, 0)
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)
