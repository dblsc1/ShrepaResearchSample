"""Step 2 · identity_read: a form check only. License id -> prefix -> role (constitution 7).

Whether the license is real, unexpired or bound to this session are check rows, not this step.
"""
import os
import re
from dataclasses import dataclass

from sherpa.result import KernelStop, kernel_red

STEP = "step02_identity_read"
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")     # license and task ids: they become file names


@dataclass(frozen=True)
class Caller:
    inst: str
    role: str


def run(args, policy) -> Caller:
    given, session = args.options.get("inst", ""), os.environ.get("SHERPA_INST", "")
    if given and session and given != session:     # a worker's shell carries its own license
        raise KernelStop(kernel_red(STEP, "identity.mismatch", f"--inst {given} but SHERPA_INST is {session}",
                                    "act as the license this session was started with", [given, session]))
    inst = given or session
    if not inst:
        raise KernelStop(kernel_red(STEP, "identity.missing", "no license id given",
                                    "pass --inst <license id> or set SHERPA_INST"))
    if not ID.fullmatch(inst):
        raise KernelStop(kernel_red(STEP, "identity.unknown", f"{inst!r} is not a license id",
                                    "pass --inst <license id>, e.g. WKR-01", [inst]))
    prefix = inst.split("-", 1)[0]
    row = policy.role_of_prefix(prefix)
    if row is None:
        known = ", ".join(f"{r['prefix']} ({r['role']})" for r in policy.roles.values())
        raise KernelStop(kernel_red(STEP, "identity.unknown", f"prefix '{prefix}' of {inst} is in no role row",
                                    f"use a license id starting with one of: {known}", [inst]))
    return Caller(inst, row["role"])
