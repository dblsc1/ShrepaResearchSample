"""Sampler tool_ledger: what this task's agent has used so far. Read-only.

  calls     tool calls sherpa let through on this task (tool_ledger/<task>.json, written by tool_ledger_write)
  sessions  {session id: tokens} of the task's earlier agent sessions, from the same file
  tokens    tokens the current session has used: its Claude Code transcript (--transcript) read up to
            --transcript-bytes, the size the hook saw, so a re-sample at step 10 reads the same bytes
  total     tokens over every session of the task

Tokens = input + cache_creation_input + cache_read_input + output of each API response, counted once
per message id: Claude Code writes one transcript line per content block, each carrying the same
usage (Agent SDK docs, cost-tracking: deduplicate by ID). The transcript's format is internal to
Claude Code (docs: sessions, "Where transcripts are stored"); checked on 2.1.326.
"""
import json
from pathlib import Path


def ledger_path(request) -> Path:
    return Path(request.governance_repo) / "tool_ledger" / f"{request.task}.json"


def transcript_tokens(path: Path, size: int) -> int:
    per_message = {}
    with path.open("rb") as f:
        data = f.read(size)
    for line in data.decode("utf-8", errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue                                   # a half-written last line
        message = entry.get("message") if isinstance(entry, dict) else None
        usage = message.get("usage") if isinstance(message, dict) else None
        if entry.get("type") != "assistant" or not isinstance(usage, dict):
            continue
        n = sum(int(usage.get(k) or 0) for k in ("input_tokens", "cache_creation_input_tokens",
                                                  "cache_read_input_tokens", "output_tokens"))
        key = message.get("id") or entry.get("requestId") or entry.get("uuid")
        per_message[key] = max(n, per_message.get(key, 0))
    return sum(per_message.values())


def sample(request) -> dict:
    path = ledger_path(request) if request.task else None
    ledger = json.loads(path.read_text(encoding="utf-8")) if path and path.is_file() else {}
    session = request.options.get("session", "")
    sessions = {k: v for k, v in (ledger.get("sessions") or {}).items() if k != session}
    transcript, size = request.options.get("transcript", ""), request.options.get("transcript_bytes", "")
    tokens = None                                       # None: this call brought no transcript to read
    if transcript and size.isdigit():
        file = Path(transcript) if Path(transcript).is_absolute() else Path(request.cwd) / transcript
        tokens = transcript_tokens(file, int(size)) if file.is_file() else None
    return {"calls": int(ledger.get("calls", 0)), "sessions": sessions, "tokens": tokens,
            "total": sum(sessions.values()) + (tokens or 0)}
