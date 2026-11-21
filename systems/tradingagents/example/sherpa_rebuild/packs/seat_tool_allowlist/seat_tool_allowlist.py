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
                                     value compares as a string);
                                     @name is the task card's --name, typed by the upper at dispatch;
                                     @task is the task's own id
Paths are compared relative to the worktree the agent works in; '*' matches '/' too. A Bash command with
shell operators (; & | ` $( > < newline) never matches a glob: a prefix must not hide a second command.
Bash(sherpa *, command!~*--inst*) lets a seat run sherpa only under its own license (the kernel takes --inst as given).
"""
import fnmatch
import json
from datetime import date
import os
import re

from sherpa.result import passed, red, skipped

COMMANDS = ("tool-call",)
MAIN_FIELD = {"Read": "file_path", "Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path",
              "NotebookEdit": "notebook_path", "Glob": "path", "Grep": "path", "Bash": "command"}
PATH_FIELDS = {"file_path", "notebook_path", "path"}
SHELL_OPERATORS = re.compile(r"[;&|`<>\n]|\$\(")
CONDITION = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(<=|!~|=|~)\s*(.*)$")
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


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


def as_path(value: str, cwd: str) -> str:
    """A path inside the worktree becomes relative to it, after '..' and symlinks are resolved
    (a link src/x -> /etc must not pass Read(src/**))."""
    value = value or "."
    real_cwd = os.path.realpath(cwd)
    full = os.path.realpath(value if os.path.isabs(value) else os.path.join(cwd, value))
    rel = os.path.relpath(full, real_cwd)
    return full if rel == ".." or rel.startswith(".." + os.sep) else rel


def as_date(text):
    """The date a YYYY-MM-DD text names, or None."""
    try:
        return date.fromisoformat(text) if ISO_DATE.fullmatch(text) else None
    except ValueError:
        return None


def field_value(tool: str, field: str, tool_input: dict, cwd: str):
    value = tool_input.get(field)
    if field in PATH_FIELDS and (value is None or isinstance(value, str)):
        return as_path(value or "", cwd)
    return value if isinstance(value, str) else (None if value is None else json.dumps(value))


def condition_holds(tool, item, tool_input, cwd, card_options, task="") -> tuple:
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
    have = field_value(tool, field, tool_input, cwd)
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
        return not fnmatch.fnmatchcase(have, want), f"{field} may not match {want}"
    if field == "command" and SHELL_OPERATORS.search(have):
        return False, "the command chains shell operators; run one plain command"
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
    card = (sample.parts.get("task_card") or {}).get("card") or {}
    rules = [] if params[seat] in ("-", "", "yes") else split_top(params[seat])
    misses = []
    for rule in rules:
        name, items = parse_rule(rule)
        if not fnmatch.fnmatchcase(tool, name):
            continue
        results = [condition_holds(tool, i, tool_input, sample.cwd, card.get("options") or {}, sample.task) for i in items]
        if all(ok for ok, _ in results):
            return passed(tool)
        misses += [f"{rule}: {why}" for ok, why in results if not ok]
    allowed = ", ".join(rules) or "no tool at all"
    if misses:
        return red("seat_tool_allowlist.input_not_allowed", f"seat {seat} may call {tool} only so: {'; '.join(misses)}",
                   f"call {tool} within those limits (seat {seat} may use: {allowed})", [tool])
    return red("seat_tool_allowlist.tool_not_allowed", f"seat {seat} may not call {tool}",
               f"use only the tools of seat {seat}: {allowed}; or ask your upper to change the workflow", [tool])
