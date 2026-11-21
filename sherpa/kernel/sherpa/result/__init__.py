"""Plugin-facing API: checks return passed() / skipped() / red()."""
from sherpa.result.result import (DONE, NOT_FINISHED, POLICY_BROKEN, REFUSED, SCHEMA_VERSION, STATUSES,
                                  CheckResult, KernelStop, Result, Verdict, exit_code, kernel_red, passed,
                                  red, skipped, stamped)

__all__ = ["SCHEMA_VERSION", "STATUSES", "CheckResult", "KernelStop", "Result", "Verdict",
           "kernel_red", "passed", "red", "skipped", "stamped", "exit_code",
           "DONE", "REFUSED", "POLICY_BROKEN", "NOT_FINISHED"]
