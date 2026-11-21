"""Step 8 · verdict: blocked when any result is red with action block."""
from sherpa.result import Result, Verdict


def make(results) -> Verdict:
    results = tuple(results)
    return Verdict(blocked=any(r.blocks for r in results), results=results)


def stopped(command: str, red, args, policy=None, kernel_hash: str = "") -> Result:
    """The Result of a command a kernel step stopped before any check ran. A stop that does not
    block (only base is on, the command is in no flow table) is ok: its one warning is the Result."""
    common = dict(command=command, inst=args.options.get("inst", ""), task=args.options.get("task", ""),
                  kernel_hash=kernel_hash, policy_pack=policy.policy_pack if policy else "",
                  policy_pack_hash=policy.policy_pack_hash if policy else "")
    if not red.blocks:
        return Result(ok=True, verdict=Verdict(False, ()), warnings=(red,), **common)
    return Result(ok=False, verdict=Verdict(True, (red,)), warnings=policy.warnings if policy else (), **common)
