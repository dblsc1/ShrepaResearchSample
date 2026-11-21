"""ppo, the policy pack organizer: installs packs into a workspace, orders them, finds their conflicts
and builds sherpa/policy/ -- the only thing the kernel reads. ppo never imports the kernel: every
format it writes is the contract's (SherpaV0.3 Spec/kernel-policy-contract.zh.md, section 2).

  pack_library.py    where packs live (four layer folders), a pack's policy_pack.toml, load_order.toml
  policy_tables.py   the five tables: shapes and the one TSV reader (contract 2.2, 2.3)
  load_order.py      the order packs stack in: hard rules, soft layers, tie-break (as LOOT sorts)
  stack.py           stack the tables in that order; every conflict is found here
  tree_hash.py       a folder's hash, as the lock records it (contract 2.4)
  governance_lock.py the lock ppo and the kernel share on <governance repo>/.lock (contract 5)
  lifecycle_compile.py the one workflow file -> roles rows, the roles column, the dispatch pairing check
  policy_build.py    plan a build; write the five tables and the dated lock
  cli.py             the `ppo` command (bin/ppo)
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Problem:
    code: str
    reason: str
    fix: str
    objects: tuple = ()

    def text(self) -> str:
        return f"RED {self.code}  {self.reason}\n  -> {self.fix}"


class PpoError(Exception):
    """Stops a ppo command; carries every problem found."""

    def __init__(self, *problems: Problem):
        super().__init__("; ".join(p.code for p in problems))
        self.problems = problems
