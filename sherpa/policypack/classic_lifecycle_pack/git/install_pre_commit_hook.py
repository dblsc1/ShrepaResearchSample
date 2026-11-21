"""Output install_pre_commit_hook (init.passed): a commit on a task branch passes `sherpa landing`
first. Goes into the project's own repo; never overwrites a hook already there."""
import os
import subprocess
from pathlib import Path

PRE_COMMIT = """#!/bin/sh
# Installed by `sherpa init`: a commit on a task branch passes `sherpa landing` first.
branch=$(git symbolic-ref --short -q HEAD) || exit 0
case "$branch" in
  task/*) exec "{sherpa}" landing --task "${{branch#task/}}" ;;
esac
"""


def git(repo, *argv):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["git", "-C", str(repo), *argv], capture_output=True, text=True, env=env)


def apply(sample, params, outcome, task):
    home = Path(sample.home)
    found = git(home, "rev-parse", "--git-path", "hooks/pre-commit")
    if found.returncode != 0:
        return "no git repo here: no pre-commit hook installed"
    hook = Path(found.stdout.strip())
    hook = hook if hook.is_absolute() else home / hook
    if hook.exists():
        return f"{hook} already exists: left alone (add `sherpa landing` to it yourself)"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(PRE_COMMIT.format(sherpa=sample.sherpa_bin), encoding="utf-8")
    hook.chmod(0o755)
    return f"pre-commit hook {hook}: commits on task/<id> branches run sherpa landing"
