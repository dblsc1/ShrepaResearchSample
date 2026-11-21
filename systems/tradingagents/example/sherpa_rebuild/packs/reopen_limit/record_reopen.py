"""Output record_reopen (reopen.passed): add one to reopens/<task> in the governance repo."""
from pathlib import Path


def apply(sample, params, outcome, task):
    counter = Path(sample.governance_repo) / "reopens" / task
    counter.parent.mkdir(parents=True, exist_ok=True)
    count = (int(counter.read_text().strip() or 0) if counter.is_file() else 0) + 1
    counter.write_text(f"{count}\n")
    return f"{task} sent back {count} time(s)"
