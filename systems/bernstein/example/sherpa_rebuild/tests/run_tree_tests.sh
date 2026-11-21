#!/bin/bash
# Sherpa's own two test suites on every scenario worktree (HOWTO section 5), one process at a time.
here=bernstein/sherpa_equivalent; V=sherpa/.venv/bin/python
for n in 1 2 3 4 5 6 7 8; do
  wt=$here/wt-s$n; out=$here/tests/runs/s$n
  echo "s$n kernel: $($V -m pytest -q -p no:cacheprovider $wt/Tests 2>&1 | tail -1)" | tee -a $here/tests/runs/tree_tests.txt
  echo "s$n packs: $($V -m pytest -q -p no:cacheprovider $wt/SherpaPolicyPackOrganizer/Tests 2>&1 | tail -1)" | tee -a $here/tests/runs/tree_tests.txt
done
