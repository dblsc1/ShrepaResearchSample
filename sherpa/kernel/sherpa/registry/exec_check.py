"""A check written in any language: JSON on stdin, one JSON line on stdout, exit 0 pass / 3 skip / 1 red."""
import json
import subprocess

from sherpa.result import CheckResult, red
from sherpa.step04_sample_freeze.sample_freeze import to_plain

EXIT_STATUS = {0: "pass", 3: "skip", 1: "red"}


def exec_check(path):
    executable = str(path)

    def run(sample, params):
        request = {"command": sample.command, "params": params, "sample": to_plain(sample)}
        try:
            done = subprocess.run([executable], input=json.dumps(request), capture_output=True,
                                  text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as err:
            return red("check.exec_failed", f"{executable}: {err}", "fix or remove the executable check")
        status = EXIT_STATUS.get(done.returncode)
        lines = done.stdout.strip().splitlines()
        try:
            answer = json.loads(lines[-1]) if lines else {}
        except json.JSONDecodeError:
            answer = None
        if status is None or answer is None or answer.get("status", status) != status:
            return red("check.bad_output", f"{executable} exited {done.returncode} with {done.stdout[-200:]!r}",
                       "print one JSON line and exit 0, 3 or 1")
        return CheckResult("", "", status, answer.get("error_code", ""), answer.get("reason", ""),
                           answer.get("fix", ""), tuple(answer.get("objects", ())))

    return run
