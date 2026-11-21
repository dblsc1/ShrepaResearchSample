#!/bin/bash
# Run the baseline table and scenario_N.tsv on branch scenario-N-* of ../modified, in its own worktree.
# Usage: tests/run_scenario.sh N   (from sherpa_equivalent/). Results: tests/runs/sN/*.results.tsv
set -u
n=$1; here=$(cd "$(dirname "$0")/.." && pwd)
branch=$(git -C "$here/modified" branch --format='%(refname:short)' | grep "^scenario-$n-")
wt="$here/wt-s$n"; out="$here/tests/runs/s$n"
[ -d "$wt" ] || git -C "$here/modified" worktree add -q "$wt" "$branch"
git -C "$wt" checkout -q "$branch" 2>/dev/null || git -C "$wt" checkout -q --detach "$branch"
mkdir -p "$out"
sed "s|^sherpa *=.*|sherpa   = \"$wt\"|" "$here/tests/pairing.toml" > "$out/pairing.toml"
[ -f "$here/tests/pairing-s$n.packs" ] && sed -i "s|^packs *=.*|packs    = $(cat "$here/tests/pairing-s$n.packs")|" "$out/pairing.toml"
cp "$here/tests/flow_baseline.tsv" "$out/"
[ -f "$here/tests/scenario_$n.tsv" ] && cp "$here/tests/scenario_$n.tsv" "$out/"
echo "$branch $(git -C "$wt" rev-parse --short HEAD)"
TMPDIR=${TMPDIR:-/tmp} python3 _pairing/run_table.py "$out/pairing.toml" "$out/flow_baseline.tsv" $( [ -f "$out/scenario_$n.tsv" ] && echo "$out/scenario_$n.tsv" ) $(for f in "$here"/tests/extra_s${n}_*.tsv; do [ -f "$f" ] && cp "$f" "$out/" && echo "$out/$(basename "$f")"; done) 2>&1 | grep -v "^OK " 
