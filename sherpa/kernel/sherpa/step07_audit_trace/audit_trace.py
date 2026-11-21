"""Step 7 · audit_trace: one audit row per result. This step only shapes the rows; step 10
appends them under the governance lock, right before its commit (so a row never lands outside
the lock, and init can record into the governance repo it has only just made).

The kernel shapes the row; the audit_writer decides where it lands (the audit pack: audit_git).
No audit_writer -> nothing recorded (ppo then warns policy.no_audit_writer on every Result).
"""
import time

from sherpa.registry import registry
from sherpa.result import kernel_red
from sherpa.result.fingerprint import kernel_hash


def audit_writer(policy):
    names = registry.names_of_kind(policy, "audit_writer")
    return registry.load(policy, names[0], "audit_writer") if names else None


def audit_row(result, sample, policy, task: str) -> dict:
    return {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "inst": sample.caller.inst,
            "command": sample.command, "task": task, "check": result.check, "stage": result.stage,
            "status": result.status, "error_code": result.error_code, "action": result.action,
            "kernel_hash": kernel_hash(), "policy_pack": policy.policy_pack,
            "policy_pack_hash": policy.policy_pack_hash, "sample_hash": sample.hash}


def run(policy, sample, results, task: str = "") -> tuple:
    """The rows for these results (written by step 10, not here)."""
    return tuple(audit_row(r, sample, policy, task or sample.task) for r in results)


def write(policy, repo, rows) -> tuple:
    """Step 10: append the rows. Returns the paths written (relative to the governance repo);
    raises the red audit.failed as an exception's argument when the writer fails."""
    writer = audit_writer(policy)
    if writer is None or not rows:
        return ()
    try:
        return tuple(writer.write(repo, list(rows)))
    except Exception as err:
        raise AuditFailed(kernel_red("step10_output_apply", "audit.failed", f"{type(err).__name__}: {err}",
                                     "fix the governance repo, then run again"))


class AuditFailed(Exception):
    def __init__(self, red):
        super().__init__(red.reason)
        self.red = red
