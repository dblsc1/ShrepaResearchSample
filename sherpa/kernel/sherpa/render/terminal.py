"""Result -> text for the terminal (what an AI or a person reads). --json prints the Result itself."""

MARK = {"pass": "pass", "skip": "skip", "red": "RED "}


def result_line(r) -> str:
    action = "" if r.action in ("block", "-") or r.status != "red" else f" [{r.action}]"
    line = f"  {MARK[r.status]} {r.check:22s} {r.error_code}{action}"
    if r.reason:
        line += f"  {r.reason}"
    if r.status == "red" and r.fix:
        line += f"\n       -> {r.fix}"
    return line.rstrip()


def render(result) -> str:
    head = f"sherpa {result.command}"
    if result.task:
        head += f"  {result.task}"
    if result.inst:
        head += f"  by {result.inst}"
    # ok with no check run at all: only base is on and the command is in no flow table (step 3).
    # Say so in the first word an agent reads, not just "ok" (human ruling 2026-11-03).
    outcome = "BLOCKED" if not result.ok else "ok" if result.verdict.results else "finish, nothing done (no policy)"
    lines = [f"{head}  ->  {outcome}"]
    lines += [result_line(r) for r in result.verdict.results]
    lines += [f"  warn {w.error_code}  {w.reason}" for w in result.warnings]
    lines += [f"  done {d}" for d in result.outputs_done]
    if result.next:
        lines.append(f"  next: {', '.join(result.next)}")
    return "\n".join(lines)
