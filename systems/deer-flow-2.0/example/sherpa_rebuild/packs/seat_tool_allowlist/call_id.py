"""One exact tool call: its argv form and its id. The same file is in seat_tool_allowlist and tool_call_approval.

A long tool input does not fit on a command line. The hook therefore hands sherpa two things:
  --input       the input with free text over 4000 characters cut (cut() below); the rules judge only this, and
                they never judge free text; any other field over 4000 characters is refused by the hook
  --input-file  the whole input, in <governance repo>/tool_inputs/<32 hex>.json, written by the hook just before
                (agents cannot write there: governance_write_ban, the Bash allowlist)
The sampler tool_input reads that file, checks that cut(file) is exactly --input, and hashes the whole input itself.
Sherpa never takes a hash from outside. An approval is bound to that hash: call_id = sha256 of [tool, hash], 32 hex
digits (128 bits); change the tail of a long Write and the id changes.
Left out of the hash: what does not change what runs. Bash's `description` (docs, hooks, PreToolUse input: "Optional
description of what the command does") is new text each time Claude writes the call, so an approved command would
never match its retry (found in the real session of 11-18, runs/e2e_final_run1_description_mismatch/)."""
import hashlib
import json

FIELD_CHARS = 4000
FREE_TEXT = {"content", "new_string", "old_string", "new_source"}   # Write/Edit/NotebookEdit bodies
NOT_RUN = {"Bash": ("description",)}


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=dict)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cut(tool_input: dict) -> tuple:
    """(the input as it goes on the command line, name of a judged field too long to send or '')."""
    out = {}
    for key, value in tool_input.items():
        if isinstance(value, str) and len(value) > FIELD_CHARS:
            if key not in FREE_TEXT:
                return out, key
            value = value[:FIELD_CHARS] + f"...[{len(value)} chars]"
        out[key] = value
    return out, ""


def bound(tool: str, tool_input):
    """The part of the input an approval is bound to: all of it but the fields that do not change what runs."""
    if not isinstance(tool_input, dict):
        return tool_input
    return {k: v for k, v in tool_input.items() if k not in NOT_RUN.get(tool, ())}


def call_id(tool: str, input_sha256: str) -> str:
    return sha256(canonical([tool, input_sha256]))[:32]
