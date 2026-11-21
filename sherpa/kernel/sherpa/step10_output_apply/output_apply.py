"""Step 10 · output_apply: the only step that writes. All of it under the governance lock:

  1 sample verification (the kernel's)     -> sample.changed: nothing is written
  2 the command body's files
  3 flow_control.advance: the row's `to`    (the kernel's)
  4 the outputs.tsv rows for <command>.passed / .red and any.passed / any.red, for the caller's role
  5 the audit rows (step 7's and this step's own) are appended, then the audit_writer commits
"""
import os
from dataclasses import replace
from pathlib import Path

from sherpa.registry import registry
from sherpa.result import Result, Verdict, kernel_red
from sherpa.result.fingerprint import kernel_hash
from sherpa.step01_policy_load.tables import parse_params, role_allowed
from sherpa.step03_flow_control.advance import advance
from sherpa.step03_flow_control.runnable import runnable
from sherpa.step03_flow_control.transition_check import state_of
from sherpa.step04_sample_freeze.verify import verify
from sherpa.step07_audit_trace import audit_trace
from sherpa.step10_output_apply.governance_lock import LockBusy, governance_lock

STEP = "step10_output_apply"


def matching_outputs(policy, command: str, outcome: str, role: str) -> list:
    wanted = (f"{command}.{outcome}", f"any.{outcome}")
    return [r for r in policy.outputs if r["event"] in wanted and role_allowed(r, role)]


def write_files(repo, files) -> list:
    done = []
    for relative, text in files.items():
        path = Path(repo) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, path)                   # a crash never leaves a half-written file
        done.append(f"wrote {relative}")
    return done


def apply_outputs(policy, sample, rows, outcome: str, task: str):
    done, reds = [], []
    for row in rows:
        try:
            note = registry.load(policy, row["output"], "output")(sample, parse_params(row["params"]), outcome, task)
        except Exception as err:
            already = " (state already advanced; finish this output by hand)" if outcome == "passed" else ""
            reds.append(kernel_red(STEP, "output.failed", f"{row['output']}: {type(err).__name__}: {err}{already}",
                                   f"fix the {row['output']} module or what it reports"))
            continue
        if note:
            done.append(f"{row['output']}: {note}")
    return done, reds


def run(workspace, policy, row, sample, verdict, products, audit_rows) -> Result:
    repo, task = sample.governance_repo, sample.task      # a body's new task id counts once it is written
    extra, audit, written = [], [], []    # audit: the books appended to; written: what else this command wrote
    done = list(products.get("notes", ()))           # what the body already did outward (step 9)
    state_after = state_of(row, sample)
    ok = False
    try:
        with governance_lock(repo) as notes:
            extra += [replace(kernel_red(STEP, "lock.stale_taken", n, "nothing to do; recorded for audit"),
                              status="skip", action="log") for n in notes]
            if products.get("red"):
                extra.append(products["red"])
            moved = None if verdict.blocked or products.get("red") else verify(policy, sample)
            ok = not verdict.blocked and not products.get("red") and moved is None
            if moved:
                extra.append(moved)
            if ok:
                done += write_files(repo, products.get("files", {}))
                written += list(products.get("files", {}))
                task = products.get("task") or task
                state_file = advance(repo, row, sample.caller.inst, task)
                if state_file:
                    written.append(Path(state_file).relative_to(repo).as_posix())
                    done.append(f"{task}: {state_after} -> {row['to']}")
                    state_after = row["to"]
            outcome = "passed" if ok else "red"
            notes_done, output_reds = apply_outputs(policy, sample, matching_outputs(policy, row["command"], outcome, sample.caller.role),
                                                    outcome, task)
            done += notes_done
            extra += output_reds
            ok = ok and not output_reds
            try:
                audit += audit_trace.write(policy, repo, [*audit_rows, *audit_trace.run(policy, sample, extra, task)])
            except audit_trace.AuditFailed as failed:     # exit 3 says "run again": say what already happened
                already = f" (already done: {'; '.join(done)})" if done else ""
                extra.append(replace(failed.red, reason=failed.red.reason + already))
                ok = False
            writer = audit_trace.audit_writer(policy)
            if writer is not None:
                try:
                    committed = writer.commit(repo, f"{row['command']} {task or '-'} by {sample.caller.inst}: {outcome}",
                                              [*audit, *written], task)
                except Exception as err:
                    committed, ok = None, False
                    extra.append(kernel_red(STEP, "output.failed", f"audit commit: {err}",
                                            "fix the governance repo (is it a git repo?), then run again"))
                if committed:
                    done.append(f"committed {committed}")
    except LockBusy as err:
        started = " A worker was already started (see done); do not start another." if products.get("notes") else ""
        extra.append(kernel_red(STEP, "lock.busy", f"{err}.{started}", "another sherpa command is writing; run again"))
        ok = False
    except Exception as err:          # after the lock was taken: say what had already happened
        extra.append(kernel_red(STEP, "output.failed",
                                f"{type(err).__name__}: {err}; already done: {'; '.join(done) or 'nothing'}",
                                "check the governance repo (git status there), finish by hand, run `sherpa next`"))
        ok = False
    results = verdict.results + tuple(extra)
    return Result(
        ok=ok, command=row["command"], verdict=Verdict(verdict.blocked or not ok, results),
        inst=sample.caller.inst, task=task,
        next=tuple(runnable(policy, sample.caller.role, state_after)),
        audit_written=tuple(dict.fromkeys(audit)), outputs_done=tuple(done), warnings=policy.warnings,
        kernel_hash=kernel_hash(), policy_pack=policy.policy_pack, policy_pack_hash=policy.policy_pack_hash)
