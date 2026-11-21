#!/usr/bin/env python3
"""Builds this folder from the research tree: `python3 -I build_artifact.py` (folder name is a placeholder).

systems/<system>/
  UPSTREAM.md                 where the system comes from: repository, commit, licence
  origin/                     the system's source at the commit all our work started from (tracked files only)
  example/sherpa_rebuild/     the Sherpa counterpart: the declaration with its role cards, and the rule packs it uses
  example/changes/            the four changes of the paper's Fig. 2 as `git diff` files, k = 1, 2, 4, 8:
      a  add k executors on a tree whose k rules name no role      T(0,k) -> T(k,k), generic family
      b  the same on a tree whose k rules name roles               T(0,k) -> T(k,k), named family
      d  install k rules that name no role on a tree with k more executors     T(k,0) -> T(k,k), generic family
      e  the same for rules that name roles                        T(k,0) -> T(k,k), named family
    counts.tsv                lines added by each diff (tests and generated files left out), with the two refs
Sherpa itself is systems/sherpa/ (changes only); the Sherpa source is ../_sherpa_minimal.
"""
import io
import shutil
import subprocess
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EXCLUDE = [":(exclude)*_test.go", ":(exclude)*generated/catalog.json", ":(exclude)tests", ":(exclude)acceptance"]
KS = [1, 2, 4, 8]
# files Bernstein regenerates from its role list: left out of the count of added executors, as in the paper
GENERATED = {"bernstein": [".cursor", ".goosehints", "AGENTS.md", "CLAUDE.md", "CONVENTIONS.md"]}
STANDARD = {"PPOtest1Solo", "PPOtest2CtoTeam", "PPOtest3SingleLine", "PPOtestToolGate"}
ORGANIZER = "SherpaPolicyPackOrganizer"
# system: (measured repo, base tree, family tree, ref of the origin, upstream note in the earlier artifact,
#          counterpart repo, counterpart ref, counterpart workflow)
SYSTEMS = {
    "bernstein": ("_scale/bernstein/modified", "grid3-k{k}-m0", "g5-k{k}-{f}{m}", "baseline", "bernstein",
                  "bernstein/sherpa_equivalent/modified", "baseline", "PPOtestBernstein"),
    "tradingagents": ("_scale/tradingagents/modified", "grid3-k{k}-m0", "g5-k{k}-{f}{m}", "baseline", "tradingagents",
                      "TradingAgents/sherpa_equivalent/modified", "baseline-with-tool-rules", "PPOtestTradingAgents"),
    "deer-flow-1.x": ("deerflow/modified", "df1-grid3-k{k}-m0", "df1-g5-k{k}-{f}{m}", "baseline", "deer-flow",
                      "deerflow/sherpa_eq", "df1-eq-grid3-k0-m0", None),
    "deer-flow-2.0": ("deerflow/v2-modified", "df2-grid3-k{k}-m0", "df2-g5-k{k}-{f}{m}", "baseline", "deer-flow",
                      "deerflow/sherpa_eq", "df2-eq-grid3-k0-m0", None),
    "paperclip": ("paperclip/modified", "grid3-k{k}-m0", "g5-k{k}-{f}{m}", "grid3-k0-m0", "paperclip", None, None, None),
    "gas-town": ("_candidates/gastown-addrole", "grid3-k{k}-m0", "g5-k{k}-{f}{m}", "grid3-k0-m0", "gas-town",
                 "_capability/gastown_eq/modified", "eq-grid3-k0-m0", "PPOtestGasTown"),
    "sherpa": ("_scale/sherpa/modified", "grid3n-k{k}-m0", "g5n-k{k}-{f}{m}", None, "sherpa-scale-line", None, None, None),
}


def git(repo, *args, text=True):
    return subprocess.run(["git", "-C", str(ROOT / repo), *args], capture_output=True, text=text)


def has(repo, ref):
    return git(repo, "rev-parse", "-q", "--verify", ref + "^{commit}").returncode == 0


def extract(repo, ref, paths, target):
    """The tracked files of `paths` at `ref`, written under target (paths keep their last folder name)."""
    done = git(repo, "archive", ref, *paths, text=False)
    if done.returncode:
        return False
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(done.stdout)) as tar:
        tar.extractall(target, filter="data")
    return True


def changes(name, repo, base, tree, out):
    rows = ["change\tk\tlines_added\tfrom\tto"]
    for letter, family, start in (("a", "g", "rules"), ("b", "n", "rules"), ("d", "g", "base"), ("e", "n", "base")):
        for k in KS:
            a = tree.format(k=0, f=family, m=k) if start == "rules" else base.format(k=k)
            b = tree.format(k=k, f=family, m=k)
            if not (has(repo, a) and has(repo, b)):          # no trees along k (Gas Town): the rules alone, T(0,0) -> T(0,m)
                a, b = base.format(k=0), tree.format(k=0, f=family, m=k)
                if start == "rules" or not (has(repo, a) and has(repo, b)):
                    continue
            exclude = EXCLUDE + ([f":(exclude){path}" for path in GENERATED.get(name, [])] if letter in "ab" else [])
            diff = git(repo, "diff", a, b, "--", ".", *exclude).stdout
            stat = git(repo, "diff", "--numstat", a, b, "--", ".", *exclude).stdout
            added = sum(int(line.split("\t")[0]) for line in stat.splitlines() if line.split("\t")[0].isdigit())
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{letter}-k{k}.diff").write_text(diff, encoding="utf-8", errors="replace")
            rows.append(f"{letter}\t{k}\t{added}\t{a}\t{b}")
    if len(rows) > 1:
        (out / "counts.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return len(rows) - 1


def rebuild(repo, ref, workflow, out):
    """The counterpart's declaration folder and the rule packs it requires."""
    listing = git(repo, "ls-tree", "--name-only", ref, f"{ORGANIZER}/custom_lifecycle/").stdout.split()
    names = [Path(p).name for p in listing if Path(p).name not in STANDARD]
    chosen = [workflow] if workflow in names else [n for n in names if n != "PPOtestBernstein"] or names
    copied = []
    for flow in chosen:
        top = f"{ORGANIZER}/custom_lifecycle/{flow}"
        extract(repo, ref, [top], out / "_tmp")
        shutil.copytree(out / "_tmp" / top, out / flow, dirs_exist_ok=True)
        copied.append(flow)
        toml = (out / flow / "policy_pack.toml").read_text(encoding="utf-8")
        line = next((x for x in toml.splitlines() if x.startswith("requires")), "")
        for pack in [p.strip(' "') for p in line.split("[", 1)[-1].rstrip("]").split(",") if p.strip(' "')]:
            for layer in ("classic_lifecycle_pack", ""):
                top = f"{ORGANIZER}/{layer}/{pack}".replace("//", "/")
                if git(repo, "cat-file", "-e", f"{ref}:{top}").returncode == 0 and pack not in ("base", "classic_lifecycle"):
                    extract(repo, ref, [top], out / "_tmp")
                    shutil.copytree(out / "_tmp" / top, out / "packs" / pack, dirs_exist_ok=True)
                    copied.append("packs/" + pack)
                    break
    shutil.rmtree(out / "_tmp", ignore_errors=True)
    return copied


if __name__ == "__main__":
    for name, (repo, base, tree, origin, note, eq_repo, eq_ref, workflow) in SYSTEMS.items():
        folder = HERE / "systems" / name
        folder.mkdir(parents=True, exist_ok=True)
        upstream = ROOT / "_reviewer_artifact" / "subjects" / note / "UPSTREAM.md"
        if upstream.is_file():
            shutil.copyfile(upstream, folder / "UPSTREAM.md")
        report = [name]
        if origin and has(repo, origin):
            ok = extract(repo, origin, [], folder / "origin")
            size = sum(p.stat().st_size for p in (folder / "origin").rglob("*") if p.is_file()) // (1 << 20)
            report.append(f"origin {origin}: {'ok' if ok else 'failed'}, {size} MB")
        report.append(f"changes: {changes(name, repo, base, tree, folder / 'example' / 'changes')} diffs")
        if eq_repo and has(eq_repo, eq_ref):
            report.append("sherpa_rebuild: " + ", ".join(rebuild(eq_repo, eq_ref, workflow, folder / "example" / "sherpa_rebuild")))
        elif eq_repo:
            report.append(f"sherpa_rebuild: ref {eq_ref} not found in {eq_repo}")
        print(" | ".join(report))
