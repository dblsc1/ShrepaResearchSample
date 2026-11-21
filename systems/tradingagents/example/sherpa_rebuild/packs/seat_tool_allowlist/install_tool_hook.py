"""Output install_tool_hook (dispatch.passed, takeoff.passed): the task's worktree gets a Claude Code
PreToolUse hook that runs tool_hook.py before every tool call, and tool_hook.py asks
`sherpa tool-call` (claude_session starts workers with --setting-sources project,local, so the
worktree's .claude/settings.local.json is read; the worker may not edit .claude/, claude_session denies it).

Hook format (Claude Code docs, hooks): matcher "*" is every tool; "args" makes it exec form (no shell);
"onFailure": "block" refuses the tool call when the hook itself fails or times out (from 2.1.295) --
without it a crashed or hung hook would let every call through. The file goes into the clone's own
exclude list, so the worker's `git add -A` never commits it. Other hooks in the file are kept."""
import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parent / "tool_hook.py"
EXCLUDE_LINE = ".claude/settings.local.json"
TIMEOUT_SECONDS = 120


def keep_out_of_git(folder: Path):
    common = subprocess.run(["git", "-C", str(folder), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                            capture_output=True, text=True).stdout.strip()
    if not common:
        return
    exclude = Path(common) / "info" / "exclude"
    present = exclude.read_text(encoding="utf-8").split() if exclude.is_file() else []
    if EXCLUDE_LINE not in present:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a", encoding="utf-8") as f:
            f.write(f"{EXCLUDE_LINE}\n")


def apply(sample, params, outcome, task):
    card = json.loads((Path(sample.governance_repo) / "tasks" / task / "task.json").read_text(encoding="utf-8"))
    folder = Path(sample.home) / card["worktree"]
    if not folder.is_dir():
        return f"{card['worktree']} does not exist yet: tool hook not installed (takeoff installs it)"
    settings = folder / ".claude" / "settings.local.json"
    data = json.loads(settings.read_text(encoding="utf-8")) if settings.is_file() else {}
    ours = {"type": "command", "command": sys.executable,
            "args": [str(HOOK), "--task", task, "--sherpa", sample.sherpa_bin, "--worktree", str(folder)],
            "timeout": TIMEOUT_SECONDS, "onFailure": "block"}
    groups = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
    kept = [g for g in groups if not any(str(HOOK) in h.get("args", []) for h in g.get("hooks", []))]
    data["hooks"]["PreToolUse"] = kept + [{"matcher": "*", "hooks": [ours]}]
    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    keep_out_of_git(folder)
    if settings.is_file() and settings.read_text(encoding="utf-8") == text:
        return f"tool hook already in {card['worktree']}/.claude/settings.local.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(text, encoding="utf-8")
    return f"tool hook in {card['worktree']}/.claude/settings.local.json: every tool call there asks sherpa tool-call first"
