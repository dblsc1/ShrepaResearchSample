"""Step 4 · sample_freeze: every sampler the policy registers reads once, in parallel; the
answers are frozen and stamped. Checks judge this sample only; they never read the world.

The object's state is not a sampler's: the kernel reads it itself (flow control's read_state,
the mirror of the advance that writes it) and freezes it with the rest.
"""
import hashlib
import json
from dataclasses import dataclass, field, is_dataclass, replace
from pathlib import Path
from types import MappingProxyType

from sherpa.registry import registry
from sherpa.result import CheckResult, KernelStop, kernel_red
from sherpa.step02_identity_read.identity_read import ID
from sherpa.step03_flow_control.advance import read_state
from sherpa.step04_sample_freeze.parallel import run_parallel

SAMPLER_SECONDS = 5.0       # ponytail: one budget for all samplers; per-sampler budgets when one is slow
SHERPA_BIN = str(Path(__file__).resolve().parents[2] / "bin" / "sherpa")


@dataclass(frozen=True)
class Sample:
    command: str
    caller: object              # step 2's Caller
    task: str                   # --task, "" when none
    options: MappingProxyType   # every --name value of the command line
    positionals: tuple
    row: MappingProxyType       # the flow-table row
    home: str                   # directory holding sherpa/
    governance_repo: str        # sherpa/: task cards, states, the audit trail
    cwd: str                    # where the command was typed (the code checkout)
    state: str = "-"            # the object's state, read by the kernel itself (not by a sampler)
    sherpa_bin: str = SHERPA_BIN  # the sherpa command, an absolute path (for hooks and worker sessions)
    parts: MappingProxyType = field(default_factory=lambda: MappingProxyType({}))
    stamps: MappingProxyType = field(default_factory=lambda: MappingProxyType({}))
    errors: MappingProxyType = field(default_factory=lambda: MappingProxyType({}))

    @property
    def hash(self) -> str:
        return stamp({"command": self.command, "inst": self.caller.inst, "task": self.task, "state": self.state,
                      "options": dict(self.options), "stamps": dict(self.stamps)})


def freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({k: freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple, set, frozenset)):
        return tuple(freeze(v) for v in value)
    return value


def to_plain(value):
    """Frozen sample -> JSON-ready dicts and lists (for exec checks, `sherpa sample`, hashes)."""
    if isinstance(value, Sample):
        return {**{k: to_plain(getattr(value, k)) for k in value.__dataclass_fields__}, "hash": value.hash}
    if is_dataclass(value):
        return {k: to_plain(getattr(value, k)) for k in value.__dataclass_fields__}
    if isinstance(value, (dict, MappingProxyType)):
        return {k: to_plain(v) for k, v in value.items() if not str(k).startswith("_")}
    if isinstance(value, (list, tuple)):
        return [to_plain(v) for v in value]
    return value


def stamp(data) -> str:
    text = json.dumps(to_plain(data), sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def take(policy, request: Sample, only=None) -> tuple:
    """Run every sampler (or those in `only`) once, in parallel. Returns (parts, stamps, errors)."""
    names = [n for n in registry.names_of_kind(policy, "sampler") if only is None or n in only]
    functions = {n: registry.load(policy, n, "sampler") for n in names}
    answers = run_parallel({n: (lambda f=f: f(request)) for n, f in functions.items()}, SAMPLER_SECONDS)
    parts, stamps, errors = {}, {}, {}
    for n in names:                                   # policy-table order, not finish order
        status, value = answers[n]
        parts[n] = value if status == "ok" else None
        if status != "ok":
            errors[n] = value
        stamps[n] = stamp(parts[n]) if status == "ok" else "error"
    return parts, stamps, errors


def failed(errors) -> CheckResult:
    return kernel_red("step04_sample_freeze", "sample.failed",
                      "; ".join(f"sampler {n}: {e}" for n, e in errors.items()),
                      "fix what the sampler reports (a broken file in the governance repo?), then run again",
                      list(errors))


def task_id(args) -> str:
    task = args.options.get("task", "")
    if task and not ID.fullmatch(task):
        raise KernelStop(kernel_red("step04_sample_freeze", "sample.bad_task_id",
                                    f"--task {task!r} is not a task id", "pass --task <id>, e.g. T-261027-1", [task]))
    return task


def state_now(request: Sample) -> str:
    try:
        return read_state(request.governance_repo, request.row, request.task)
    except ValueError as err:
        raise KernelStop(kernel_red("step04_sample_freeze", "sample.failed", str(err),
                                    "fix the state file in the governance repo, then run again", [request.task]))


def request_of(workspace, caller, row, args, task: str) -> Sample:
    """What a sampler is asked with: the sample before its parts, the kernel's own state read in."""
    request = Sample(
        command=row["command"], caller=caller, task=task,
        options=freeze(dict(args.options)), positionals=tuple(args.positionals), row=row,
        home=str(workspace.home), governance_repo=str(workspace.governance_repo), cwd=str(workspace.cwd))
    return replace(request, state=state_now(request))


def run(workspace, policy, caller, row, args) -> Sample:
    request = request_of(workspace, caller, row, args, task_id(args))
    parts, stamps, errors = take(policy, request)
    if errors:                    # a missing part would let checks pass blind: stop instead
        raise KernelStop(failed(errors))
    return replace(request, parts=freeze(parts), stamps=MappingProxyType(stamps),
                   errors=MappingProxyType(errors))
