#!/usr/bin/env python3
"""Assembles this repository from the frozen snapshot: `python3 -I assemble_from_snapshot.py`.

Every file under kernel/, ppo/, policypack/ and the five user packs in example/sherpa/policypack/ is a byte-for-byte
copy, except the edits listed in EDITS below. They do two things and nothing else:
  1  the pack library moves out of the compiler's own folder into policypack/ (one constant in the compiler)
  2  the rule pack `task_card` is renamed `task_card_check`, so that it no longer has the name of the fact
     `task_card` that classic_lifecycle provides (the pack's name, its four error codes, and the places that
     refer to the pack)
Left out: the other rule packs and workflows of the full library, test folders, and each pack's `cases/`
(its own test cases). Folder names here are placeholders.
"""
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAPSHOT = HERE.parent / "_reviewer_artifact_sherpa_snapshot"
ORGANIZER = SNAPSHOT / "SherpaPolicyPackOrganizer"
RULE_PACKS = ORGANIZER / "classic_lifecycle_pack"
SKIP = shutil.ignore_patterns("__pycache__", "cases")
DEFAULT, USER = "policypack/classic_lifecycle_pack/", "example/sherpa/policypack/"

# target (relative to this folder) -> source
COPIES = {
    "kernel/bin": SNAPSHOT / "Core" / "bin",
    "kernel/sherpa": SNAPSHOT / "Core" / "sherpa",
    "ppo/bin": ORGANIZER / "bin",
    "ppo/ppo": ORGANIZER / "ppo",
    # the default pack library, by layer
    "policypack/base": ORGANIZER / "base",
    "policypack/classic_lifecycle": ORGANIZER / "classic_lifecycle",
    DEFAULT + "audit": RULE_PACKS / "audit",
    DEFAULT + "git": RULE_PACKS / "git",
    DEFAULT + "task_card_check": RULE_PACKS / "task_card",
    DEFAULT + "worktree": RULE_PACKS / "worktree",
    # what a user adds: four rule packs and an organization (the declaration). They live where a real project
    # keeps its own packs, in the project's sherpa/policypack/, one folder per pack; run_example.py builds the rest
    # of the project around them
    USER + "waits_for": RULE_PACKS / "waits_for",
    USER + "parallel_wait_all": RULE_PACKS / "parallel_wait_all",
    USER + "write_scope": RULE_PACKS / "write_scope",
    USER + "review_rules": RULE_PACKS / "review_rules",
    USER + "PPOtest2CtoTeam": ORGANIZER / "custom_lifecycle" / "PPOtest2CtoTeam",
}
# file -> [(text in the snapshot, text here)]; each old text stands exactly once in its file
EDITS = {
    "ppo/ppo/pack_library.py": [
        ("LIBRARY = Path(__file__).resolve().parents[1]\n", 'LIBRARY = Path(__file__).resolve().parents[2] / "policypack"\n'),
        ("The library is this repo: base/,", "The library is ../policypack/: base/,"),
    ],
    DEFAULT + "task_card_check/policy_pack.toml": [
        ('name      = "task_card"', 'name      = "task_card_check"'),
        ("# task_card: a card", "# task_card_check: a card"),
    ],
    DEFAULT + "task_card_check/plugins.tsv": [("# task_card: a card", "# task_card_check: a card")],
    DEFAULT + "task_card_check/task_card_complete.py": [        # the pack's four error codes follow its name
        ('red("task_card.missing_required"', 'red("task_card_check.missing_required"'),
        ('red("task_card.placeholder_left"', 'red("task_card_check.placeholder_left"'),
        ('red("task_card.bad_assignee"', 'red("task_card_check.bad_assignee"'),
        ('red("task_card.bad_scope"', 'red("task_card_check.bad_scope"'),
    ],
    "policypack/classic_lifecycle/dispatch.py": [
        ("the task_card pack says it better", "the task_card_check pack says it better"),
    ],
    USER + "write_scope/policy_pack.toml": [
        ('"classic_lifecycle", "task_card", "git"]', '"classic_lifecycle", "task_card_check", "git"]'),
    ],
    USER + "write_scope/write_scope.py": [
        ('parents[1] / "task_card" /', 'parents[1] / "task_card_check" /'),
        ("the task_card pack's agent_rule_files.py (this pack requires task_card).",
         "the task_card_check pack's agent_rule_files.py (this pack requires task_card_check)."),
        ('"""A helper file of the task_card pack,', '"""A helper file of the task_card_check pack,'),
    ],
}

if __name__ == "__main__":
    for target, source in COPIES.items():
        shutil.copytree(source, HERE / target, ignore=SKIP, dirs_exist_ok=True)
    for name, edits in EDITS.items():
        text = (HERE / name).read_text(encoding="utf-8")
        for old, new in edits:
            assert text.count(old) == 1, f"{name} in the snapshot no longer has exactly one: {old!r}"
            text = text.replace(old, new)
        (HERE / name).write_text(text, encoding="utf-8")
    files = [p for t in COPIES for p in (HERE / t).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    lines = sum(len(p.read_text(encoding="utf-8", errors="replace").splitlines()) for p in files)
    print(f"{len(COPIES)} folders copied, {len(EDITS)} files edited ({sum(map(len, EDITS.values()))} places): "
          f"{len(files)} files, {lines} lines")
