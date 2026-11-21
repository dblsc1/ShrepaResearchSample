"""Check seat_tool_allowlist (tool-call): the caller's seat may call this tool, with this input.

params (from the workflow file): <seat>=<rule>,<rule>,...   <seat>=-  allows no tool at all.
A seat not named is not limited by this check. A tool no rule names is refused.

A rule is a tool name (fnmatch: mcp__data__* is every tool of that server), optionally with conditions:
  Read(src/**)                       the tool's main field matches the glob (Read/Edit/Write: file_path,
                                     NotebookEdit: notebook_path, Glob/Grep: path, Bash: command)
  mcp__data__get(symbol=@ticker, curr_date<=@date, source~yahoo*)
                                     field = value, field ~ glob, field !~ glob (must not match),
                                     field <= value (a YYYY-MM-DD value compares as a date, and then only a
                                     YYYY-MM-DD date passes: an empty or undated value is refused; any other
                                     value compares as a string; langgraph-zumi, mero #18874);
                                     @name is the task card's --name, typed by the upper at dispatch;
                                     @task is the task's own id
Paths are compared relative to the worktree the agent works in; '*' matches '/' too.
Bash is allowlist only: Bash(git status*) hits when the command is one plain command (no operators, no $, `,
braces, globs or ~; not run through a shell, interpreter or wrapper) whose first words are exactly `git status`.
Anything else is refused; with tool_call_approval installed, the refusal says how the upper approves that call --
except a failed `!~` condition or a path outside the worktree: those are hard limits, never approvable.
An approval is bound to the hash of the whole input, which the sampler tool_input computes itself (call_id.py).
`sherpa tool-call` typed in Bash is refused: only the hook types it.
Bash(sherpa *, command!~*--inst*) lets a seat run sherpa only under its own license (the kernel takes --inst as given).
"""
import fnmatch
import json
import os
from datetime import date
import re
import shlex

from sherpa.result import passed, red, skipped

from .call_id import call_id

COMMANDS = ("tool-call",)
MAIN_FIELD = {"Read": "file_path", "Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path",
              "NotebookEdit": "notebook_path", "Glob": "path", "Grep": "path", "Bash": "command"}
PATH_FIELDS = {"file_path", "notebook_path", "path"}
SHELL_OPERATORS = re.compile(r"[;&|`<>\n]|\$\(")
CONDITION = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(<=|!~|=|~)\s*(.*)$")
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
EXPANDS = re.compile(r"[$`{}*?\[\]~]")               # what would run cannot be read off the text
LAUNCHERS = {"sh", "bash", "zsh", "dash", "ksh", "fish", "eval", "exec", "source", ".", "xargs", "env", "command",
             "builtin", "sudo", "doas", "nohup", "timeout", "nice", "stdbuf", "time", "python", "python3", "perl",
             "ruby", "node", "php", "awk", "busybox"}


def plain_words(command: str):
    """The command's words if it is one plain command: no shell operators, no expansion, splits cleanly
    (quotes removed the way the shell removes them), and its first word is no shell, interpreter or wrapper.
    None otherwise: such a command never hits the list (allowlist only; the upper may approve it)."""
    if SHELL_OPERATORS.search(command) or EXPANDS.search(command):
        return None
    try:
        words = shlex.split(command)
    except ValueError:
        return None
    return words if words and words[0] not in LAUNCHERS and os.path.basename(words[0]) not in LAUNCHERS else None


def typed_tool_call(command: str) -> bool:
    """`sherpa tool-call ...` (any path to sherpa), read the shell's way; JSON braces do not hide it."""
    try:
        words = shlex.split(command)
    except ValueError:
        return False
    return len(words) > 1 and os.path.basename(words[0]) == "sherpa" and words[1] == "tool-call"


def command_hits(command: str, pattern: str) -> tuple:
    """`git status*`: the command's first words are exactly git, status (anything may follow);
    `git status`: the command is exactly those words. Compared word by word, never as text."""
    words = plain_words(command)
    if words is None:
        return False, "only one plain command counts (no operators, variables, globs, interpreters or wrappers)"
    open_end = pattern.rstrip().endswith("*")
    want = pattern.rstrip().rstrip("*").split()
    ok = words[:len(want)] == want and (open_end or len(words) == len(want))
    return ok, f"command {command} does not start with {' '.join(want)}"


def split_top(text: str) -> list:
    """'Read(a,b),Grep' -> ['Read(a,b)', 'Grep']: commas inside parentheses stay."""
    out, depth, start = [], 0, 0
    for i, c in enumerate(text):
        depth += (c == "(") - (c == ")")
        if c == "," and depth == 0:
            out.append(text[start:i])
            start = i + 1
    out.append(text[start:])
    return [x.strip() for x in out if x.strip()]


def parse_rule(rule: str) -> tuple:
    name, _, rest = rule.partition("(")
    return name.strip(), split_top(rest[:-1]) if rest.endswith(")") else []


def as_path(field: str, paths) -> str:
    """A path inside the worktree becomes relative to it. '..' and symlinks were resolved by the sampler
    tool_input (a link src/x -> /etc must not pass Read(src/**)); here only strings are compared."""
    full = paths["fields"][field]
    rel = os.path.relpath(full, paths["cwd"])          # both absolute: string work, no disk
    return full if rel == ".." or rel.startswith(".." + os.sep) else rel


def as_date(text):
    """The date a YYYY-MM-DD text names, or None."""
    try:
        return date.fromisoformat(text) if ISO_DATE.fullmatch(text) else None
    except ValueError:
        return None


def field_value(tool: str, field: str, tool_input: dict, paths):
    value = tool_input.get(field)
    if field in PATH_FIELDS and (value is None or isinstance(value, str)):
        return as_path(field, paths)
    return value if isinstance(value, str) else (None if value is None else json.dumps(value))


def condition_holds(tool, item, tool_input, paths, card_options, task="") -> tuple:
    """(holds, why not) for one condition of a rule."""
    found = CONDITION.match(item)
    field, op, want = found.groups() if found else (MAIN_FIELD.get(tool), "~", item)
    if field is None:
        return False, f"{tool} has no main field for the pattern {item}"
    if want == "@task":
        want = task
    elif want.startswith("@"):
        if want[1:] not in card_options:
            return False, f"the task card has no --{want[1:]} for {field} to match"
        want = str(card_options[want[1:]])
    have = field_value(tool, field, tool_input, paths)
    if have is None:
        return False, f"{field} is missing"
    if op == "=":
        return have == want, f"{field} must be {want}, not {have}"
    if op == "<=":
        if ISO_DATE.fullmatch(want):          # a date bound compares dates; "" or "2026" is no date (mero #18874)
            bound, value = as_date(want), as_date(have)
            if bound is None or value is None:
                return False, f"{field} must be a date YYYY-MM-DD, {want} or earlier, not {have!r}"
            return value <= bound, f"{field} must be {want} or earlier, not {have}"
        return have <= want, f"{field} must be {want} or earlier, not {have}"
    if op == "!~":
        if field == "command":                         # judge the words the shell would run, not only the text
            words = plain_words(have)
            if words is None:
                return False, "the command cannot be read as one plain command"
            have = " ".join(words) + "\n" + have
        return not fnmatch.fnmatchcase(have, want), f"{field} may not match {want}"
    if field == "command":
        return command_hits(have, want)
    if tool == "Glob" and field == "path":
        pattern = str(tool_input.get("pattern", ""))
        if pattern.startswith("/") or ".." in pattern.split("/"):
            return False, f"the Glob pattern {pattern} leaves its path"
    folder = field in PATH_FIELDS and want.endswith("/**") and have == want[:-3]     # src/** covers src itself
    return folder or fnmatch.fnmatchcase(have, want), f"{field} {have} is not under {want}"


def run(sample, params):
    seat = sample.caller.role
    if seat not in params:
        return skipped(f"no tool list for seat {seat}")
    tool = sample.options.get("tool", "")
    if not tool or tool == "yes":
        return red("seat_tool_allowlist.no_tool", "tool-call came without --tool", "the hook passes --tool=<name>")
    try:
        tool_input = json.loads(sample.options.get("input", "{}"))
    except ValueError:
        return red("seat_tool_allowlist.bad_input", "--input is not JSON", "the hook passes --input=<tool_input JSON>")
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    whole = sample.parts.get("tool_input") or {}
    digest, paths = whole.get("sha256"), whole.get("paths") or {"cwd": "", "fields": {}}
    if digest is None:
        return red("seat_tool_allowlist.input_unverified", whole.get("why") or "the whole tool input is unknown",
                   "make the tool call itself; the hook hands sherpa the whole input", [tool])
    if tool == "Bash" and typed_tool_call(str(tool_input.get("command", ""))):
        return red("seat_tool_allowlist.tool_call_by_hand", "`sherpa tool-call` is typed by the tool hook only",
                   "make the tool call itself; the hook asks sherpa", [tool])
    card = (sample.parts.get("task_card") or {}).get("card") or {}
    rules = [] if params[seat] in ("-", "", "yes") else split_top(params[seat])
    misses, hard = [], False
    for rule in rules:
        name, items = parse_rule(rule)
        if not fnmatch.fnmatchcase(tool, name):
            continue
        results = [condition_holds(tool, i, tool_input, paths, card.get("options") or {}, sample.task) for i in items]
        if all(ok for ok, _ in results):
            return passed(tool)
        misses += [f"{rule}: {why}" for ok, why in results if not ok]
        hard = hard or any(not ok and (m := CONDITION.match(i)) and m.group(2) == "!~" for i, (ok, _) in zip(items, results))
    field = MAIN_FIELD.get(tool)
    if field in PATH_FIELDS and os.path.isabs(str(field_value(tool, field, tool_input, paths))):
        hard = True                                    # outside the worktree: no approval opens that
    allowed = ", ".join(rules) or "no tool at all"
    if misses:
        cid = call_id(tool, digest)
        approvals = sample.parts.get("tool_approvals")        # tool_call_approval's fact, when that pack is on
        if approvals is not None and not hard and (approvals.get("approved") or {}).get(cid) == digest:
            return passed(cid)                                 # the approval's hash is this whole input's hash
        ask = "" if hard else (f"; or stop and ask {card.get('issued_by', 'your upper')} to run "
               f"`sherpa approve-tool --task {sample.task} --call {cid}`, then make exactly the same call again "
               "(no answer means no)") if approvals is not None else ""
        return red("seat_tool_allowlist.input_not_allowed", f"seat {seat} may call {tool} only so: {'; '.join(misses)}",
                   f"call {tool} within those limits (seat {seat} may use: {allowed}){ask}", [tool, cid])
    return red("seat_tool_allowlist.tool_not_allowed", f"seat {seat} may not call {tool}",
               f"use only the tools of seat {seat}: {allowed}; or ask your upper to change the workflow", [tool])
