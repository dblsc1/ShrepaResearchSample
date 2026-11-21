"""The one list of files that set an agent's own rules (settings and hooks, sub-agent definitions,
MCP servers, instruction files), for every agent tool a project may run (Claude Code, Codex,
opencode, Cursor, Gemini, Copilot). A worker may never change them, even inside its write scope.

Read by task_card_complete (here), write_scope/write_scope.py and solo/claude.py."""
from pathlib import PurePosixPath

AGENT_RULE_DIRS = (".claude", ".codex", ".opencode", ".cursor", ".gemini")
AGENT_RULE_FILES = ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", "GEMINI.md", ".mcp.json", "opencode.json",
                    "opencode.jsonc", ".cursorrules", ".github/copilot-instructions.md")


def agent_rules(path: str) -> bool:
    """Case-insensitive: on macOS and Windows `claude.md` is the same file as `CLAUDE.md`."""
    low = PurePosixPath(path.casefold()).as_posix().strip("/")
    parts = low.split("/")
    return (any(d.casefold() in parts for d in AGENT_RULE_DIRS)
            or any(low == f.casefold() or low.endswith("/" + f.casefold()) for f in AGENT_RULE_FILES))
