"""Command body tool_ledger_write (`sherpa tool-call`): the call passed every check, so count it.
Writes nothing itself: tool_ledger/<task>.json goes back as a file, and step 10 commits it together
with this command's audit rows -- the count and the token bookkeeping land in the record."""
import json
import time


def run(sample, registry_view):
    ledger = sample.parts.get("tool_ledger") or {}
    sessions = dict(ledger.get("sessions") or {})
    session = sample.options.get("session", "")
    if session and ledger.get("tokens") is not None:
        sessions[session] = ledger["tokens"]
    calls = ledger.get("calls", 0) + 1
    record = {"task": sample.task, "calls": calls, "sessions": sessions, "tokens_total": sum(sessions.values()),
              "last": {"tool": sample.options.get("tool", ""), "session": session, "agent": sample.options.get("agent", ""),
                       "at": time.strftime("%Y-%m-%dT%H:%M:%S%z")}}
    return {"files": {f"tool_ledger/{sample.task}.json": json.dumps(record, ensure_ascii=False, indent=1) + "\n"},
            "notes": [f"tool call {calls} on {sample.task}: {record['last']['tool']} "
                      f"(tokens so far {record['tokens_total']})"]}
