# Gas Town (role-oriented subject)

- Repository: https://github.com/gastownhall/gastown (Go), `origin` URL of the local clone
- Commit: `94cc82289d2ead275a62e1db4ef1d4ada4a1f98e` (2026-11-12); the owner report writes the short form `94cc822`
- Licence: MIT (LICENSE of that commit, "Copyright (c) 2025 Steve Yegge"). See `LICENSES.md`.
- Stars (18,834 on 2026-11-19): not traced to a file here.

Changes were counted but never compiled or tested (no Go toolchain on the experiment machine). Branches `razu/add-role-tinker` (58f2515, add one role governed like `polecat`), `razu/rule-one-role`, `razu/rule-one-role-code`, `razu/rule-seven-roles`, each diffed against `94cc822`; patches in `patches/`. There is no Sherpa equivalent and no scale sweep for Gas Town.

## What is here

- `reports/`: the owner session's report(s), copied as they are (Chinese). Session names and message numbers in them are the authors' working notes.
- `scripts/`: the owner's generator, counting and acceptance scripts, copied as they are. They read research repos that are not shipped, so they are for reading; the numbers they produced are in `data/`.
- `patches/`: one `git diff <base>..<branch>` per change; the first line of each file names the refs. For size sweeps only size 1 and the largest size are shipped. The other sizes come from the same generator with another size argument (see the owner report), or from `git diff` in the research repo (`data/scale/git_series.tsv` holds the counts of every size).
- `results/`: pass/fail summaries only (the last two lines of each run output), not the full logs.
