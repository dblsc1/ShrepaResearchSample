#!/usr/bin/env python3
"""One count for the two formal rule families (grid5, see GRID5-两族形式规则.md): `python3 -I count_grid5.py` prints a
table and writes grid5.tsv next to this file.

Every number is the added lines of `git diff --numstat` between two committed trees, tests and generated files left out:
    rules  T(0, 0) -> T(0, m)      the family alone, m = 1, 2, 4, 8
    over   T(k, 0) -> T(k, k)      what the family costs on an organization that already has k more executors
    both   T(0, 0) -> T(k, k)
    inter  over(k) - rules(k)      the lines that exist only because executors and rules were both added
A tree that does not exist gives an empty cell (Gas Town has no trees along k).
"""
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXCLUDE = [":(exclude)*_test.go", ":(exclude)*generated/catalog.json", ":(exclude)tests", ":(exclude)acceptance"]
SYSTEMS = {      # name: (repo, base tree of k, family tree of (letter, k, m))
    "bernstein": (ROOT / "_scale/bernstein/modified", "grid3-k{k}-m0", "g5-k{k}-{f}{m}"),
    "tradingagents": (ROOT / "_scale/tradingagents/modified", "grid3-k{k}-m0", "g5-k{k}-{f}{m}"),
    "deerflow1": (ROOT / "deerflow/modified", "df1-grid3-k{k}-m0", "df1-g5-k{k}-{f}{m}"),
    "deerflow2": (ROOT / "deerflow/v2-modified", "df2-grid3-k{k}-m0", "df2-g5-k{k}-{f}{m}"),
    "paperclip": (ROOT / "paperclip/modified", "grid3-k{k}-m0", "g5-k{k}-{f}{m}"),
    "gastown": (ROOT / "_candidates/gastown-addrole", "grid3-k{k}-m0", "g5-k{k}-{f}{m}"),
    "sherpa": (ROOT / "_scale/sherpa/modified", "grid3n-k{k}-m0", "g5n-k{k}-{f}{m}"),
}
KS = [1, 2, 4, 8]


def added(repo, a, b):
    """Added lines from tree a to tree b, or None when one of them does not exist."""
    for ref in (a, b):
        if subprocess.run(["git", "-C", str(repo), "rev-parse", "-q", "--verify", ref + "^{commit}"], capture_output=True).returncode:
            return None
    out = subprocess.run(["git", "-C", str(repo), "diff", "--numstat", a, b, "--", ".", *EXCLUDE],
                         check=True, capture_output=True, text=True).stdout
    return sum(int(line.split("\t")[0]) for line in out.splitlines() if line.split("\t")[0].isdigit())


def count():
    rows = []
    for name, (repo, base, tree) in SYSTEMS.items():
        for f in "gn":
            rules = [added(repo, base.format(k=0), tree.format(k=0, f=f, m=m)) for m in KS]
            over = [added(repo, base.format(k=k), tree.format(k=k, f=f, m=k)) for k in KS]
            both = [added(repo, base.format(k=0), tree.format(k=k, f=f, m=k)) for k in KS]
            inter = [None if o is None or r is None else o - r for o, r in zip(over, rules)]
            rows.append((name, f, rules, over, both, inter))
    return rows


if __name__ == "__main__":
    rows = count()
    cell = lambda v: "" if v is None else str(v)
    lines = ["system\tfamily\tseries\t" + "\t".join(str(k) for k in KS)]
    for name, f, rules, over, both, inter in rows:
        for series, values in (("rules", rules), ("over", over), ("both", both), ("inter", inter)):
            lines.append(f"{name}\t{f}\t{series}\t" + "\t".join(cell(v) for v in values))
        print(f"{name:14}{'generic' if f == 'g' else 'named':8} rules {rules}  over {over}  inter {inter}")
    (HERE / "grid5.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
