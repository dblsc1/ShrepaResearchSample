"""Step 9 · command_execute: the few commands with work of their own (a command body).

A body acts outward (asks questions, starts a process) and computes its products, but writes
no file: it returns {"task": <object id it created>, "files": {<path in the governance repo>: text},
"notes": [<one line per thing it did>]} and step 10 writes the files after sample verification
(constitution 4: only step 10 writes). A body that raises becomes the red command.failed.
"""
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from sherpa.registry import registry
from sherpa.result import kernel_red

NOTHING = MappingProxyType({})


@dataclass(frozen=True)
class RegistryView:
    """What a body may look up besides the sample: other plugins, and role cards."""
    policy: object

    def plugin(self, kind: str, name: str):
        if name not in self.policy.plugins or self.policy.plugins[name]["kind"] != kind:
            raise LookupError(f"plugins.tsv has no {kind} named {name}")
        return registry.load(self.policy, name, kind)

    def role_of(self, inst: str) -> str:
        row = self.policy.role_of_prefix(inst.split("-", 1)[0])
        return row["role"] if row else ""

    def role_card(self, role: str) -> str:
        row = self.policy.roles.get(role)
        if row is None or row["card"] == "-":
            return ""
        path = Path(self.policy.pack_root) / row["card"]
        return path.read_text(encoding="utf-8") if path.is_file() else ""


def run(policy, row, sample, verdict):
    if verdict.blocked or row["body"] == "-":
        return NOTHING
    body = registry.load(policy, row["body"], "command")
    try:
        products = dict(body(sample, RegistryView(policy)) or {})
        repo = Path(sample.governance_repo).resolve()
        for relative in products.get("files", {}):
            path = (repo / relative).resolve()
            if not path.is_relative_to(repo) or path.name == "state.json" or \
                    path.relative_to(repo).parts[:1] in (("policy",), ("policypack",)):
                raise ValueError(f"may not write {relative!r}: outside the governance repo, a state file "
                                 "(only flow control writes state), or the policy (only ppo builds it)")
        return MappingProxyType(products)
    except Exception as err:
        return MappingProxyType({"red": kernel_red("step09_command_execute", "command.failed",
                                                   f"{row['body']}: {type(err).__name__}: {err}",
                                                   "fix what the reason says, then run the command again")})
