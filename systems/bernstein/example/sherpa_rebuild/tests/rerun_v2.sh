#!/bin/bash
# Re-run every table and the tree tests after the R3 fix (baseline-v1 -> baseline, mero #18875). One process at a time.
here=bernstein/sherpa_equivalent; cd $here
export TMPDIR=/tmp/...
for n in 1 2 3 4 5 6 7 8; do echo "== s$n"; tests/run_scenario.sh $n; done
echo "== r15"; python3 _pairing/run_table.py tests/pairing-r15-enabled.toml tests/r15_enabled.tsv 2>&1 | grep -v "^OK "
V=sherpa/.venv/bin/python
echo "baseline kernel: $($V -m pytest -q -p no:cacheprovider modified/Tests 2>&1 | tail -1)" | tee -a tests/runs/tree_tests.txt
echo "baseline packs: $($V -m pytest -q -p no:cacheprovider modified/SherpaPolicyPackOrganizer/Tests 2>&1 | tail -1)" | tee -a tests/runs/tree_tests.txt
tests/run_tree_tests.sh
echo "rerun done"
