#!/usr/bin/env python3
"""Claude Code PreToolUse hook (installed by install_tool_hook): ask `sherpa tool-call` before each tool call.

stdin: the hook event (Claude Code docs, hooks: session_id, transcript_path, cwd, tool_name, tool_input).
sherpa says ok (exit 0)   -> exit 0, print nothing: the call goes on through Claude Code's own permissions.
anything else             -> print a PreToolUse "deny" decision whose reason is sherpa's reason and fix,
                             exit 0 (docs: exit 1 is a non-blocking error that lets the call through).
sample.changed / lock.busy (two tool calls of one turn judged at once) -> ask again, a few times.
Any failure of this script also denies (and onFailure "block" covers a crash before that).
A long input does not fit on a command line: --input carries it with free text cut (call_id.cut), and the whole
input goes to --input-file, <governance repo>/tool_inputs/<random>.json, removed when sherpa has answered. Sherpa
checks the two fit and hashes the whole input itself; an approval binds that hash.
"""
import argparse
import json
import os
import secrets
import subprocess
import sys
import time

RETRY_CODES = {"sample.changed", "lock.busy"}
ATTEMPTS = 6


def deny(reason: str):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    sys.exit(0)


def reds(result) -> list:
    rows = (result.get("verdict") or {}).get("results") or []
    return [r for r in rows if r.get("status") == "red"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--sherpa", required=True)
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--inputs", required=True)
    args = ap.parse_args()
    from call_id import FIELD_CHARS, cut     # this script's folder is first on sys.path; inside the fail-closed try
    event = json.load(sys.stdin)
    whole = event.get("tool_input") or {}
    tool_input, too_long = cut(whole)
    if too_long:                                 # a judged field is never cut: a long command could hide `; rm -rf`
        deny(f"sherpa cannot judge this call: field {too_long} is longer than {FIELD_CHARS} characters; "
             "split it into shorter calls")
    os.makedirs(args.inputs, exist_ok=True)
    input_file = os.path.join(args.inputs, secrets.token_hex(16) + ".json")
    with open(input_file, "x", encoding="utf-8") as f:
        json.dump(whole, f, ensure_ascii=False)
    try:
        ask(args, event, tool_input, input_file)
    finally:
        os.remove(input_file)


def ask(args, event, tool_input, input_file):
    argv = [args.sherpa, "tool-call", "--task", args.task, f"--tool={event.get('tool_name', '')}",
            f"--input={json.dumps(tool_input, ensure_ascii=False)}", f"--input-file={input_file}",
            f"--session={event.get('session_id', '')}", "--json"]
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
