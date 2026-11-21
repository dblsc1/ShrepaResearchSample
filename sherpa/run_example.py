#!/usr/bin/env python3
"""Builds example/ and runs the paper's example in it: `python3 -I run_example.py`. Uses only this repository.

example/ is a real project, laid out exactly as a user's project is:
  example/src/                        the project's own code
  example/sherpa/policypack/<pack>/   the packs that are on: the default ones, copied in by `ppo init` from
                                      ../policypack/, and the user's own, which live only here
  example/sherpa/policy/              what the compiler wrote: the five tables and the lock
  example/sherpa/tasks/<task>/        each task's record and state
  example/sherpa/audit/               one row per check result
The user's own packs are four rule packs and an organization (PPOtest2CtoTeam: a person hands a goal to a CTO; the
CTO dispatches a work task to a programmer and a review of it to a reviewer).

A run rebuilds the project from nothing but the user's packs: they are taken from the existing example/, the default
packs are installed, everything is compiled, and 24 commands are issued through the kernel's command line; 5 of them
must be refused, one per rule. example_transcript.txt keeps each command, who issued it, its exit code and the
terminal text the agent sees. The commands are issued by this script, not by language-model agents.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
PPO = HERE / "ppo" / "bin" / "ppo"
SHERPA = HERE / "kernel" / "bin" / "sherpa"
PROJECT = HERE / "example"
PREVIOUS = HERE / "example.previous"            # the project of the run before, until this run has passed
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@localhost"]
DEFAULT_PACKS = ["base", "classic_lifecycle", "audit", "git", "task_card_check", "worktree"]
USER_PACKS = ["waits_for", "parallel_wait_all", "write_scope", "review_rules", "PPOtest2CtoTeam"]
LINES = []


def run(folder, *argv, inst=None):
    env = {**os.environ, "SHERPA_HOME": "", "PYTHONDONTWRITEBYTECODE": "1"}
    if inst:
        env["SHERPA_INST"] = inst
    return subprocess.run([str(a) for a in argv], cwd=folder, capture_output=True, text=True, env=env)


def record(title, done, expect):
    LINES.append(f"$ {title}  exit {done.returncode}\n{done.stdout}{done.stderr}")
    assert done.returncode == expect, (title, done.returncode, done.stdout, done.stderr)


def sherpa(inst, *argv, folder=None, expect=0):
    record(f"sherpa {' '.join(argv)}        [{inst}]", run(folder or PROJECT, SHERPA, *argv, "--inst", inst), expect)


def card(task):
    return json.loads((PROJECT / "sherpa" / "tasks" / task / "task.json").read_text())


def worktree(task):
    return PROJECT / card(task)["worktree"]


def dispatch(by, to, *extra, expect=0):
    sherpa(by, "dispatch", "--to", to, "--goal", f"work for {to}", "--scope", "src/", *extra, expect=expect)
    return sorted(os.listdir(PROJECT / "sherpa" / "tasks"), key=lambda name: int(name.rsplit("-", 1)[1]))[-1]


def commit(inst, task, path, expect=0):
    """The lower writes one file and commits; the hook installed at init runs `sherpa landing` on the commit."""
    folder = worktree(task)
    (folder / path).parent.mkdir(parents=True, exist_ok=True)
    (folder / path).write_text(f"# {task}\n")
    run(folder, "git", "add", path)
    done = run(folder, *GIT, "commit", "-q", "-m", task, inst=inst)
    record(f"git commit {path}  (the hook runs sherpa landing --task {task})        [{inst}]", done, expect)
    if expect:                                   # a refused commit: take the file back out
        run(folder, "git", "reset", "-q", "--", path)
        os.remove(folder / path)


def merge(task):
    run(PROJECT, "git", "switch", "-q", card(task)["parent_branch"])
    run(PROJECT, *GIT, "merge", "-q", "--no-edit", card(task)["branch"])


def fresh_project():
    """An empty git project with the user's packs in sherpa/policypack/, taken from the project of the run before."""
    if PREVIOUS.exists():                        # the run before failed half way: its source is still PREVIOUS
        if PROJECT.exists():
            shutil.rmtree(PROJECT)
    else:
        PROJECT.rename(PREVIOUS)
    PROJECT.mkdir()
    run(PROJECT, "git", "init", "-q", "-b", "main")
    (PROJECT / "src").mkdir()
    (PROJECT / "src" / "a.py").write_text("a\n")
    run(PROJECT, "git", "add", "-A")
    run(PROJECT, *GIT, "commit", "-q", "-m", "the project before Sherpa")
    for pack in USER_PACKS:
        shutil.copytree(PREVIOUS / "sherpa" / "policypack" / pack, PROJECT / "sherpa" / "policypack" / pack,
                        ignore=shutil.ignore_patterns("__pycache__"))


if __name__ == "__main__":
    fresh_project()
    packs = ",".join(DEFAULT_PACKS + USER_PACKS)
    record(f"ppo init --packs {packs}", run(PROJECT, PPO, "init", "--packs", packs), 0)

    sherpa("HUM-00", "init")                                                             # 1
    goal = dispatch("HUM-00", "CTO-01")                                                  # 2
    sherpa("CTO-01", "brief", "--task", goal, folder=worktree(goal))                     # 3
    sherpa("CTO-01", "takeoff", "--task", goal, folder=worktree(goal))                   # 4
    work = dispatch("CTO-01", "WORKER-01")                                               # 5
    dispatch("CTO-01", "WORKER-01", "--reviews", work, "--waits-for", work, expect=1)    # 6  REFUSED author reviews
    review = dispatch("CTO-01", "REVIEWER-01", "--reviews", work, "--waits-for", work)   # 7
    dispatch("HUM-00", "WORKER-01", expect=1)                                            # 8  REFUSED not own lower
    sherpa("REVIEWER-01", "brief", "--task", review)                                     # 9
    sherpa("REVIEWER-01", "takeoff", "--task", review, expect=1)                         # 10 REFUSED work still open
    sherpa("WORKER-01", "brief", "--task", work, folder=worktree(work))                  # 11
    sherpa("WORKER-01", "takeoff", "--task", work, folder=worktree(work))                # 12
    commit("WORKER-01", work, "docs/note.md", expect=1)                                  # 13 REFUSED outside src/
    commit("WORKER-01", work, f"src/{work}.py")                                          # 14 landing
    sherpa("WORKER-01", "debrief", "--task", work, folder=worktree(work))                # 15
    merge(work)
    sherpa("CTO-01", "receipt", "--task", work)                                          # 16
    commit("CTO-01", goal, f"src/{goal}.py")                                             # 17 landing
    sherpa("CTO-01", "debrief", "--task", goal, folder=worktree(goal), expect=1)         # 18 REFUSED review still open
    sherpa("REVIEWER-01", "takeoff", "--task", review)                                   # 19
    commit("REVIEWER-01", review, f"src/{review}.py")                                    # 20 landing
    sherpa("REVIEWER-01", "debrief", "--task", review, folder=worktree(review))          # 21
    merge(review)
    sherpa("CTO-01", "receipt", "--task", review)                                        # 22
    sherpa("CTO-01", "debrief", "--task", goal, folder=worktree(goal))                   # 23
    merge(goal)
    sherpa("HUM-00", "receipt", "--task", goal)                                          # 24

    (HERE / "example_transcript.txt").write_text("\n".join(LINES), encoding="utf-8")
    shutil.rmtree(PREVIOUS)
    print("24 commands issued, 5 refused as expected; example/ is the project after the run; example_transcript.txt written")
