"""The three data structures that cross step boundaries (constitution 3).

Add-only: new fields get defaults, nothing is renamed or removed; an
incompatible change bumps SCHEMA_VERSION.
"""
from dataclasses import asdict, dataclass, replace

SCHEMA_VERSION = 1
STATUSES = ("pass", "skip", "red")


@dataclass(frozen=True)
class CheckResult:
    """One check's answer. The tri-state JSON contract is its text form."""
    check: str
    stage: str
    status: str                     # pass / skip / red
    error_code: str = ""
    reason: str = ""
    fix: str = ""
    objects: tuple = ()
    action: str = "block"           # from the checks table's action column

    @property
    def blocks(self) -> bool:
        return self.status == "red" and self.action == "block"


@dataclass(frozen=True)
class Verdict:
    blocked: bool
    results: tuple = ()


@dataclass(frozen=True)
class Result:
    ok: bool
    command: str
    verdict: Verdict
    inst: str = ""
    task: str = ""
    next: tuple = ()
    audit_written: tuple = ()
    outputs_done: tuple = ()
    warnings: tuple = ()
    kernel_hash: str = ""
    policy_pack: str = ""
    policy_pack_hash: str = ""
    schema_version: int = SCHEMA_VERSION

    def to_json_dict(self) -> dict:
        return asdict(self)


class KernelStop(Exception):
    """Raised by steps 1-4 when the command cannot go on (unknown policy pack, unknown caller...)."""

    def __init__(self, result: CheckResult):
        super().__init__(f"{result.error_code}: {result.reason}")
        self.result = result


# Exit codes of `sherpa` (and so of the pre-commit hook). An agent reads the number before the text:
#   0 done (also: only base is on and nothing was done)
#   1 refused: a rule or the command line said no -- fix what the reason says, run again
#   2 the policy is broken or missing (policy.*, a check that crashed) -- stop; a person rebuilds it with ppo
#   3 sherpa could not finish (busy lock, the world moved, an output or the audit failed, a crash) --
#     run again; the reason says if something had already happened. Also: init where a workspace already is
DONE, REFUSED, POLICY_BROKEN, NOT_FINISHED = 0, 1, 2, 3
NOT_FINISHED_CODES = ("lock.busy", "sample.changed", "sample.failed", "output.failed", "audit.failed",
                      "kernel.crashed", "command.failed",
                      "init.workspace_exists")          # human 2026-11-03: init where a workspace already is


def exit_code(error_codes) -> int:
    """The exit code for the blocking reds of a command (none -> 0). The most serious one wins."""
    codes = list(error_codes)
    if not codes:
        return DONE
    if any(c.startswith(("policy.", "check.")) for c in codes):
        return POLICY_BROKEN
    if any(c in NOT_FINISHED_CODES for c in codes):
        return NOT_FINISHED
    return REFUSED


# Helpers a check plugin returns; the kernel fills in check / stage / action.
def passed(*objects) -> CheckResult:
    return CheckResult("", "", "pass", objects=tuple(objects))


def skipped(reason: str, error_code: str = "") -> CheckResult:
    return CheckResult("", "", "skip", error_code=error_code, reason=reason)


def red(error_code: str, reason: str, fix: str, objects=()) -> CheckResult:
    return CheckResult("", "", "red", error_code=error_code, reason=reason, fix=fix,
                       objects=tuple(objects))


def kernel_red(step: str, error_code: str, reason: str, fix: str, objects=()) -> CheckResult:
    """A red raised by a kernel step itself (not by a table row)."""
    return CheckResult(step, "kernel", "red", error_code, reason, fix, tuple(objects), "block")


def stamped(result: CheckResult, check: str, stage: str, action: str) -> CheckResult:
    return replace(result, check=check, stage=stage, action=action)


__all__ = ["CheckResult", "Verdict", "Result", "KernelStop", "SCHEMA_VERSION", "STATUSES",
           "passed", "skipped", "red", "kernel_red", "stamped", "exit_code",
           "DONE", "REFUSED", "POLICY_BROKEN", "NOT_FINISHED"]
