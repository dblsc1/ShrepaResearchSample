"""`ppo new <pack>`: the smallest pack that enables and builds as it is -- a declaration, one check
bound to dispatch that passes, its plugins row, and a should_pass and a should_block case to fill in."""
import json
from pathlib import Path

DECLARATION = '''# {name}: say in one line what rule this pack adds.
name      = "{name}"
version   = "1"
requires  = ["base", "classic_lifecycle"]   # every pack whose command, fact or plugin you use
after     = []
conflicts = []
group     = "classic_lifecycle_pack"
writes    = []                              # paths in the governance repo this pack writes (folders end in /)
provides  = []                              # facts it adds: a sampler's name, or "<command> --<option>"
reads     = []                              # facts it reads, e.g. "archive", "task_card", "dispatch --to"
'''
CHECKS = '''# Which time point the check hangs on (or * for every one). Never a role or seat name: whom it runs for
# is the workflow file's business ([policy.{name}] only / except).
command\tcheck\tstage\taction\tparams\tlocked
dispatch\t{name}_check\tgeneral\tblock\t-\tno
'''
PLUGINS = "name\tkind\timpl\tlocked\n{name}_check\tcheck\t{name}_check.py\tno\n"
CHECK = '''"""Check {name}_check: say what it stops. It reads the frozen sample only (no disk), and only runtime
facts (what was dispatched, in what state), never a count set in advance."""
from sherpa.result import passed, red

COMMANDS = ("dispatch",)


def run(sample, params):
    if False:                    # the rule goes here
        return red("{name}.broken", "what is wrong, in one sentence", "what to do about it")
    return passed()
'''
SHOULD_PASS = {"about": "should pass: say what", "steps": [
    {"by": "human", "run": "dispatch", "options": {"to": "worker", "goal": "fix a", "scope": "src/"},
     "expect": {"exit": 0}}]}
SHOULD_BLOCK = {"about": "should be red: say what", "todo": "write the steps that break the rule", "steps": [
    {"by": "human", "run": "dispatch", "options": {"to": "worker", "goal": "fix a", "scope": "src/"},
     "expect": {"exit": 1, "red": "{name}.broken"}}]}


def write_skeleton(folder: Path, name: str):
    (folder / "cases").mkdir(parents=True)
    for file, text in (("policy_pack.toml", DECLARATION), ("checks.tsv", CHECKS), ("plugins.tsv", PLUGINS),
                       (f"{name}_check.py", CHECK)):
        (folder / file).write_text(text.format(name=name), encoding="utf-8")
    for file, case in (("should_pass.json", SHOULD_PASS), ("should_block.json", SHOULD_BLOCK)):
        text = json.dumps(case, ensure_ascii=False, indent=1).replace("{name}", name)
        (folder / "cases" / file).write_text(text + "\n", encoding="utf-8")
