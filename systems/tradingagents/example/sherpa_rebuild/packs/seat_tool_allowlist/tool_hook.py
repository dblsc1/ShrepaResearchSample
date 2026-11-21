#!/usr/bin/env python3
"""Claude Code PreToolUse hook (installed by install_tool_hook): ask `sherpa tool-call` before each tool call.

stdin: the hook event (Claude Code docs, hooks: session_id, transcript_path, cwd, tool_name, tool_input).
sherpa says ok (exit 0)   -> exit 0, print nothing: the call goes on through Claude Code's own permissions.
anything else             -> print a PreToolUse "deny" decision whose reason is sherpa's reason and fix,
                             exit 0 (docs: exit 1 is a non-blocking error that lets the call through).
sample.changed / lock.busy (two tool calls of one turn judged at once) -> ask again, a few times.
Any failure of this script also denies (and onFailure "block" covers a crash before that).
"""
import argparse
import json
import os
import subprocess
import sys
import time

RETRY_CODES = {"sample.changed", "lock.busy"}
ATTEMPTS = 6
FIELD_CHARS = 4000       # argv limit: only free text no rule judges may be cut; any other long field is refused
FREE_TEXT = {"content", "new_string", "old_string", "new_source"}   # Write/Edit/NotebookEdit bodies


def deny(reason: str):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    sys.exit(0)


def short(key, value):
    """A judged field is never cut: a long command could hide `; rm -rf` past the cut."""
    if isinstance(value, str) and len(value) > FIELD_CHARS:
        if key not in FREE_TEXT:
            deny(f"sherpa cannot judge this call: field {key} is longer than {FIELD_CHARS} characters; "
                 "split it into shorter calls")
        return value[:FIELD_CHARS] + f"...[{len(value)} chars]"
    return value


def reds(result) -> list:
    rows = (result.get("verdict") or {}).get("results") or []
    return [r for r in rows if r.get("status") == "red"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--sherpa", required=True)
    ap.add_argument("--worktree", required=True)
    args = ap.parse_args()
    event = json.load(sys.stdin)
    tool_input = {k: short(k, v) for k, v in (event.get("tool_input") or {}).items()}
    argv = [args.sherpa, "tool-call", "--task", args.task, f"--tool={event.get('tool_name', '')}",
            f"--input={json.dumps(tool_input, ensure_ascii=False)}", f"--session={event.get('session_id', '')}", "--json"]
    if event.get("agent_id"):                    # a subagent's call (docs, hooks: agent_id, agent_type)
        argv.append(f"--agent={event['agent_id']}:{event.get('agent_type', '')}")
    transcript = event.get("transcript_path") or ""
    if transcript and os.path.isfile(transcript):
        argv += [f"--transcript={transcript}", f"--transcript-bytes={os.path.getsize(transcript)}"]
    for attempt in range(ATTEMPTS):
        done = subprocess.run(argv, cwd=args.worktree, capture_output=True, text=True, timeout=90)
        if done.returncode == 0:
            sys.exit(0)
        try:
            result = json.loads(done.stdout)
        except ValueError:
            deny(f"sherpa tool-call exited {done.returncode}: {(done.stderr or done.stdout).strip()[:500]}")
        found = reds(result)
        if done.returncode == 3 and found and {r["error_code"] for r in found} <= RETRY_CODES:
            time.sleep(0.3 * (attempt + 1))
            continue
        break
    lines = [f"{r['error_code']}: {r.get('reason', '')} -> {r.get('fix', '')}" for r in found] or [done.stdout.strip()[:500]]
    deny("sherpa refused this tool call (exit %d). %s" % (done.returncode, " | ".join(lines)))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as err:          # fail closed
        deny(f"sherpa tool hook failed: {type(err).__name__}: {err}")
