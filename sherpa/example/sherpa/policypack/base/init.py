"""Command body init (base): make this folder a sherpa workspace. Computes the files; writes nothing
(step 10 writes them after sample verification).

The folder sherpa/ is the workspace and the governance repo at once. config.toml marks it as
initialized. .gitignore keeps the lock file, worker logs and task worktrees out of its history."""
from pathlib import Path

from sherpa.result import kernel_red

IGNORED = (".lock", "runs/", "worktrees/")
CONFIG = "# A sherpa workspace: written by `sherpa init`. Settings go here.\n"


def run(sample, registry_view):
    repo = Path(sample.governance_repo)
    if (repo / "config.toml").exists():
        return {"red": kernel_red("init", "base.workspace_exists",
                                  f"{repo / 'config.toml'} already exists: this folder is a sherpa workspace",
                                  "nothing to do; `sherpa next --inst <your license>` shows what you can run")}
    ignore = repo / ".gitignore"
    text = ignore.read_text(encoding="utf-8") if ignore.is_file() else ""
    text += "".join(f"{entry}\n" for entry in IGNORED if entry not in text.split())
    return {"files": {"config.toml": CONFIG, ".gitignore": text},
            "notes": [f"workspace {repo} founded by {sample.caller.inst}"]}
