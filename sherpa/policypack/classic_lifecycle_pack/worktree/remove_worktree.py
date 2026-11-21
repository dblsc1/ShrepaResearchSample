"""Output remove_worktree (receipt.passed): the task is merged and closed, so its folder goes.
The branch and its commits stay. git refuses while anything in the folder is uncommitted; then the
red says so and the person looks before forcing."""
import subprocess
from pathlib import Path


def apply(sample, params, outcome, task):
    card = (sample.parts.get("task_card") or {}).get("card") or {}
    relative = card.get("worktree")
    if not relative or not (Path(sample.home) / relative).exists():
        return f"no worktree to remove for {task}"
    done = subprocess.run(["git", "-C", str(sample.home), "worktree", "remove", relative],
                          capture_output=True, text=True)
    if done.returncode != 0:
        raise RuntimeError(f"{relative} kept: {done.stderr.strip()}; look inside, then "
                           f"`git worktree remove --force {relative}`")
    return f"removed worktree {relative} (branch {card.get('branch')} kept)"
