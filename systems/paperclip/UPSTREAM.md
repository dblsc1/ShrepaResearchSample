# Paperclip (partly decoupled subject)

- Repository: https://github.com/paperclipai/paperclip (`origin` URL of `paperclip/modified`)
- Commit all work started from: `dc9971bdb823534dc7b348934bcc28cfd7fe9f4d` (2026-11-10, tag `baseline`)
- Licence: MIT ("Copyright (c) 2025 Paperclip AI"). See `LICENSES.md`.
- Stars (114,807 on 2026-11-19): not traced to a file here.

Refs: scenarios `baseline..scenario-1..8` (`patches/scenarios/`); scale line tags `size-<s>` and branches `size-<s>-{add-role,per-role-rule,add-layer,add-group}`, s = 1, 2, 4, 8, 16 (`patches/scale/`: s = 1 and 16; `generated/catalog.json` is excluded from the patches, as in the owner's counts). Counting table of the owner: `data/scale/paperclip_counts_numstat.tsv` (`git diff --numstat`); the shapes in `data/scale/git_series.tsv` are recounted with `git diff -U0`.
Sherpa side: the Sherpa equivalent is built by us on the Sherpa research copy (`sherpa-pristine`); it has no upstream. The shipped Sherpa is the seat-class version (see `sherpa/`); the by-seat variant is an ablation under `data/without-seat-class/`.

## What is here

- `reports/`: the owner session's report(s), copied as they are (Chinese). Session names and message numbers in them are the authors' working notes.
- `scripts/`: the owner's generator, counting and acceptance scripts, copied as they are. They read research repos that are not shipped, so they are for reading; the numbers they produced are in `data/`.
- `patches/`: one `git diff <base>..<branch>` per change; the first line of each file names the refs. For size sweeps only size 1 and the largest size are shipped. The other sizes come from the same generator with another size argument (see the owner report), or from `git diff` in the research repo (`data/scale/git_series.tsv` holds the counts of every size).
- `results/`: pass/fail summaries only (the last two lines of each run output), not the full logs.
