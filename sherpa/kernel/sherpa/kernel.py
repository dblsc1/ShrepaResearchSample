"""The kernel: one command, ten steps, fixed order (constitution 1-2). Nothing else lives here
except one side door, query(), for the read-only commands. `init` is a command like any other
(human ruling 2026-10-31): the base policy pack's flow table has its row.
"""
from sherpa.result import KernelStop, kernel_red
from sherpa.result.fingerprint import kernel_hash
from sherpa.step01_policy_load import policy_load
from sherpa.step02_identity_read import identity_read
from sherpa.step03_flow_control.lookup import lookup
from sherpa.step04_sample_freeze import sample_freeze
from sherpa.step05_checks_run import checks_run
from sherpa.step06_builtin_checks import builtin_checks
from sherpa.step07_audit_trace import audit_trace
from sherpa.step08_verdict import verdict as verdict_step
from sherpa.step09_command_execute import command_execute
from sherpa.step10_output_apply import output_apply


def step(command, args, workspace):
    try:
        return ten_steps(command, args, workspace)
    except Exception as err:            # a bug anywhere becomes a red Result, never a traceback
        import traceback
        where = traceback.extract_tb(err.__traceback__)[-1]
        red = kernel_red("kernel", "kernel.crashed", f"{type(err).__name__}: {err} ({where.filename}:{where.lineno})",
                         "report this as a kernel bug; the governance lock was released")
        return verdict_step.stopped(command, red, args, None, kernel_hash())


def ten_steps(command, args, workspace):
    policy = None
    try:
        policy = policy_load.run(workspace)                                          # 1
        caller = identity_read.run(args, policy)                                     # 2
        row = lookup(policy, command)                                                # 3
        sample = sample_freeze.run(workspace, policy, caller, row, args)             # 4
        results = checks_run.run(policy, row, sample)                                # 5
        results += builtin_checks.run(policy, row, sample)                           # 6
        audit = audit_trace.run(policy, sample, results)                             # 7 rows; 10 writes
        verdict = verdict_step.make(results)                                         # 8
        products = command_execute.run(policy, row, sample, verdict)                 # 9
    except KernelStop as stop:          # nothing written yet: steps 1-9 never write
        return verdict_step.stopped(command, stop.result, args, policy, kernel_hash())
    return output_apply.run(workspace, policy, row, sample, verdict, products, audit)  # 10


# ---- the side door (host ruling 2026-10-28): read-only queries ----
QUERIES = ("help", "config", "next", "whoami", "sample", "check", "audit")
USAGE = """sherpa <command> [--inst <license id>] [--task <task id>] [--json] ...

  sherpa init --inst <license id>                    make this folder a workspace (sherpa/ here)
                                                     (sherpa/policy/ must be built first, by ppo)
  sherpa -h                                          commands of this workspace's policy
  sherpa config --dump [--for <command>]             the built five tables: row, pack, impl, locked
  sherpa next                                        what can I run now
  sherpa whoami | sample <command> | check <check> <command> | audit [--task <id>]

exit code: 0 done; 1 refused (fix what it says); 2 the policy is broken or missing (stop, tell a person);
3 sherpa could not finish (run again)
"""


def query(name, args, workspace):
    """Read-only commands: steps 1-4 as needed, no checks, no audit, no writes."""
    from sherpa.query import queries
    return queries.run(name, args, workspace)

