"""Output prepare_worktree (dispatch.passed, takeoff.passed): give the task its own folder, a git
worktree on the task branch, so no two workers ever share a checkout and the person's own checkout
stays where it is (constitution 8: one task, one branch, one worktree).

Made at dispatch, because a worker's session starts in that folder and cannot move later; takeoff
only remakes it if it went missing. A folder already on the task branch is left as it is."""
import json
import subprocess
from pathlib import Path


def git(where, *argv):
    return subprocess.run(["git", "-C", str(where), *argv], capture_output=True, text=True)


def keep_out_of_status(home: Path, folder: str):
    """The worktrees sit inside the project: list them in the clone's own exclude file (not a
    tracked .gitignore) so the person's `git status` does not show them."""
    common = git(home, "rev-parse", "--git-common-dir").stdout.strip()
    exclude = home / common / "info" / "exclude"
    line = f"/{folder}/"
    present = exclude.read_text(encoding="utf-8").split() if exclude.is_file() else []
    if line not in present:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a", encoding="utf-8") as f:
            f.write(f"{line}\n")


def apply(sample, params, outcome, task):
    card = json.loads((Path(sample.governance_repo) / "tasks" / task / "task.json").read_text(encoding="utf-8"))
    home, branch, parent = Path(sample.home), card["branch"], card["parent_branch"]
    folder = home / card["worktree"]
    if folder.exists():
        on = git(folder, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        if on != branch:
            raise RuntimeError(f"{card['worktree']} exists but is on {on or 'no branch'}, not {branch}")
        return f"worktree {card['worktree']} on {branch}: work there"
    keep_out_of_status(home, Path(card["worktree"]).parent.as_posix())
    have_branch = git(home, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0
    argv = (["worktree", "add", str(folder), branch] if have_branch
            else ["worktree", "add", "-b", branch, str(folder), parent])
    done = git(home, *argv)
    if done.returncode != 0:
        raise RuntimeError(f"git {' '.join(argv)}: {done.stderr.strip()}")
    return f"worktree {card['worktree']} on {branch}" + ("" if have_branch else f" (new, from {parent})") + \
        ": work there"
