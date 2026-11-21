"""Check tool_call_limit (tool-call): the task's agent has had fewer than n tool calls let through.

params (from the workflow file): <seat>=<n>. A seat not named is not limited. The count is the
tool_ledger fact: calls sherpa let through on this task, over all of its sessions."""
from sherpa.result import passed, red, skipped

COMMANDS = ("tool-call",)


def run(sample, params):
    seat = sample.caller.role
    if not params.get(seat, "").isdigit():
        return skipped(f"no tool call limit for seat {seat}")
    limit, calls = int(params[seat]), (sample.parts.get("tool_ledger") or {}).get("calls", 0)
    if calls >= limit:
        return red("tool_call_limit.reached", f"{sample.task} has had its {limit} tool calls (seat {seat})",
                   "stop calling tools: write up what you have (no more tools), and tell your upper the limit was reached",
                   [str(calls)])
    return passed(f"{calls + 1}/{limit}")
