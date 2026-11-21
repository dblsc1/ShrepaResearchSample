"""Audit writer audit_git (the audit pack, locked): append-only jsonl in the governance repo's own
audit/ folder, one book per license (audit/<inst>.jsonl) and one per task (audit/tasks/<task>.jsonl);
every command ends in one git commit there.

The governance repo (sherpa/) becomes a git repo on the first write, which is init's. A refused
command never founds one: with no repo yet, its rows have nowhere to go and are dropped."""
import json
import os
import subprocess
from pathlib import Path

COMMITTER = ["-c", "user.name=sherpa", "-c", "user.email=sherpa@localhost"]


def git(repo, *argv):
    # Inside a code repo's git hook, git exports GIT_INDEX_FILE / GIT_DIR...; inherited here they
    # would point the governance repo's git at the code repo's index. Drop every GIT_* variable.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["git", "-C", str(repo), *argv], capture_output=True, text=True, env=env)


def books(repo, row) -> list:
    task_book = row["task"] and (Path(repo) / "tasks" / row["task"] / "task.json").is_file()
    return [f"audit/{row['inst']}.jsonl"] + ([f"audit/tasks/{row['task']}.jsonl"] if task_book else [])


def write(repo, rows) -> list:
    if not (Path(repo) / ".git").exists():
        if any(r["status"] == "red" and r["action"] == "block" for r in rows):
            return []
        git(repo, "init", "-q")
    written = {}
    for row in rows:
        for relative in books(repo, row):
            written.setdefault(relative, []).append(json.dumps(row, ensure_ascii=False))
    for relative, lines in written.items():
        path = Path(repo) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as book:
            book.write("".join(line + "\n" for line in lines))
    return list(written)


def commit(repo, message: str, paths=(), task: str = ""):
    """Commit exactly what this command wrote, plus its task's worklog (the worker writes that
    between commands). Returns the short sha, or None if nothing changed. Any other change in the
    repo stays uncommitted and shows in `git status` there: a stray or tampered file never enters
    the record under another command's name."""
    if not (Path(repo) / ".git").exists():
        return None
    wanted = [*paths, *([f"tasks/{task}/worklog.md"] if task else [])]
    present = [p for p in dict.fromkeys(wanted) if (Path(repo) / p).is_file()]
    if not present:
        return None
    git(repo, "add", "--", *present)
    done = git(repo, *COMMITTER, "commit", "-m", message, "--", *present)
    if done.returncode != 0:
        if "nothing to commit" in done.stdout + done.stderr or "no changes added" in done.stdout:
            return None
        raise RuntimeError(f"git commit in {repo} failed: {(done.stderr or done.stdout).strip()}")
    return done.stdout.split("]", 1)[0].rsplit(" ", 1)[-1]      # "[main abc1234] msg" -> abc1234


def read(repo, inst: str = "", task: str = "") -> list:
    if task:
        files = [Path(repo) / "audit" / "tasks" / f"{task}.jsonl"]
    elif inst:
        files = [Path(repo) / "audit" / f"{inst}.jsonl"]
    else:
        files = sorted((Path(repo) / "audit").glob("*.jsonl"))     # the license books hold every row
    rows = [json.loads(line) for f in files if f.is_file() for line in f.read_text(encoding="utf-8").splitlines()]
    return sorted(rows, key=lambda r: r["ts"])
