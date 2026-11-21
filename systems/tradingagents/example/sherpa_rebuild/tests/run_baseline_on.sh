#!/bin/sh
# Usage: tests/run_baseline_on.sh <N> [<extra pack>]  -- rerun flow_baseline.tsv (with the baseline pairing.toml) on the branch modified/ has
# checked out; the table copy and its results go to runs/flow_baseline_on_scenario_<N>.{tsv,results.tsv,txt}.
T=$(cd "$(dirname "$0")" && pwd)
cp "$T/flow_baseline.tsv" "$T/runs/flow_baseline_on_scenario_$1.tsv"
# a scenario that adds a pack to the workflow's requires needs it installed here too (the table itself is unchanged)
sed -e 's|^sherpa   = "../modified"|sherpa   = "../../modified"|' \
    -e "s|\"reopen_limit\"\]|\"reopen_limit\"${2:+, \"$2\"}]|" "$T/pairing.toml" > "$T/runs/pairing_baseline_copy.toml"
mkdir -p "$T/tmp"
TMPDIR="$T/tmp" python3 -I _pairing/run_table.py "$T/runs/pairing_baseline_copy.toml" \
  "$T/runs/flow_baseline_on_scenario_$1.tsv" > "$T/runs/flow_baseline_on_scenario_$1.txt" 2>&1
grep -E "FAIL|did not" "$T/runs/flow_baseline_on_scenario_$1.txt"
