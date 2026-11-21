"""Sampler git: the code checkout the command was typed in (branch, staged files, dirty or not,
the task branch against its parent and the files it commits). Read-only. Its git calls run side by side."""
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

GIT_SECONDS = 4      # under the kernel's 5 s sampler budget, so a hung git is killed, not waited for


def git(cwd, *argv):
    done = subprocess.run(["git", "-C", str(cwd), *argv], capture_output=True, text=True)
    return done.stdout.strip() if done.returncode == 0 else None


def task_card(request):
    path = Path(request.governance_repo) / "tasks" / request.task / "task.json"
    return json.loads(path.read_text(encoding="utf-8")) if request.task and path.is_file() else None


def parse_status(text: str) -> dict:
    """`git status --porcelain=v2 --branch -z` -> branch, head, staged paths, dirty.
    Paths come raw (no quoting), so spaces and non-ASCII names survive."""
    out = {"branch": "", "head": "", "staged": [], "dirty": False}
    fields = iter(text.split("\0"))
    for entry in fields:
        if entry.startswith("# branch.head "):
            out["branch"] = "" if entry.endswith("(detached)") else entry.split(" ", 2)[2]
        elif entry.startswith("# branch.oid "):
            out["head"] = "" if entry.endswith("(initial)") else entry.split(" ", 2)[2]
        elif entry[:2] in ("1 ", "2 ", "u "):
            path = entry.split(" ", {"1": 8, "2": 9, "u": 10}[entry[0]])[-1]
            if entry[0] == "2":
                next(fields, None)                    # a rename's original path follows
            if entry[0] == "u" or entry.split(" ")[1][0] != ".":
                out["staged"].append(path)
            out["dirty"] = True
    out["staged"].sort()
    return out


def sample(request) -> dict:
    card = task_card(request)
    parent, branch = (card or {}).get("parent_branch", ""), (card or {}).get("branch", "")
    # --no-renames: a rename lists both paths, so moving a file out of the write scope is seen
    calls = {"top": ("rev-parse", "--show-toplevel"),
             "status": ("status", "--porcelain=v2", "--branch", "--untracked-files=no", "--no-renames", "-z")}
    if card:
        calls["refs"] = ("for-each-ref", "--format=%(refname:short)", f"refs/heads/{parent}", f"refs/heads/{branch}")
        calls["merged"] = ("merge-base", "--is-ancestor", branch, parent)
        calls["branch_files"] = ("diff", "--name-only", "--no-renames", "--no-ext-diff", "-z", f"{parent}...{branch}")
    with ThreadPoolExecutor(max_workers=len(calls)) as pool:
        futures = {k: pool.submit(subprocess.run, ["git", "-C", request.cwd, *argv], capture_output=True, text=True,
                                  timeout=GIT_SECONDS) for k, argv in calls.items()}
    done = {k: f.result() for k, f in futures.items()}
    if done["top"].returncode != 0:
        return {"repo": None}
    out = {"repo": done["top"].stdout.strip(), **parse_status(done["status"].stdout)}
    if card:
        refs = done["refs"].stdout.split()
        out["parent_branch_exists"] = parent in refs
        out["task_branch_exists"] = branch in refs
        out["task_branch_merged"] = done["merged"].returncode == 0
        # what the task branch commits since it left its parent; None when either branch is missing
        files = done["branch_files"]
        out["branch_files"] = sorted(f for f in files.stdout.split("\0") if f) if files.returncode == 0 else None
    return out
