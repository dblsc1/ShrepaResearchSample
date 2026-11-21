"""Output exclude_sherpa_folder (init.passed): sherpa/ is a git repo of its own (the governance
repo), so the project's git status should not show it. Listed in the clone's own exclude file,
not in a tracked .gitignore: no file of the project changes."""
import subprocess
from pathlib import Path

LINE = "/sherpa/"


def apply(sample, params, outcome, task):
    home = Path(sample.home)
    common = subprocess.run(["git", "-C", str(home), "rev-parse", "--git-common-dir"], capture_output=True, text=True)
    if common.returncode != 0:
        return "no git repo here: nothing to exclude"
    exclude = home / common.stdout.strip() / "info" / "exclude"
    present = exclude.read_text(encoding="utf-8").split() if exclude.is_file() else []
    if LINE in present:
        return f"{LINE} already in {exclude}"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a", encoding="utf-8") as f:
        f.write(f"{LINE}\n")
    return f"{LINE} added to {exclude}: the project's git status leaves sherpa/ out"
