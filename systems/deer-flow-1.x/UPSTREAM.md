# deer-flow (ByteDance): 1.x and 2.0

- Repository: https://github.com/bytedance/deer-flow (`origin` URL of the local original clones)
- 1.x: commit `2ab28765803d4d9582aaa8f2f3355137d154e273` (2026-03-12), research repo `deerflow/modified`, branch `main-1.x` upstream. Patches `patches/1x/`.
- 2.0: commit `e0cccd6b376191e7017c1d4602326a96d5cde28c` (2026-11-18), research repo `deerflow/v2-modified`. Patches `patches/2.0/`. 2.0 is a rewrite and does not share code with 1.x (statement from the upstream README, quoted in the owner report).
- Licence: MIT, both commits ("Copyright (c) 2025 Bytedance Ltd. and/or its affiliates"; 2.0 adds "DeerFlow Authors"). See `LICENSES.md`.
- Stars (85,487 on 2026-11-19): not traced to a file here.

Both versions are scaled to the same execution organization (1, 2, 4, 8 groups; branches `size-<s>/{a,b,c,d}`, 2.0 also `bcfg`). Sweeps: patches for s = 1 and 8. Counting tables: `results/count-1x/table.tsv`, `results/count-v2/table.tsv` (also in `data/scale/`). There is no Sherpa equivalent for deer-flow; the comparison is between its two versions.

## What is here

- `reports/`: the owner session's report(s), copied as they are (Chinese). Session names and message numbers in them are the authors' working notes.
- `scripts/`: the owner's generator, counting and acceptance scripts, copied as they are. They read research repos that are not shipped, so they are for reading; the numbers they produced are in `data/`.
- `patches/`: one `git diff <base>..<branch>` per change; the first line of each file names the refs. For size sweeps only size 1 and the largest size are shipped. The other sizes come from the same generator with another size argument (see the owner report), or from `git diff` in the research repo (`data/scale/git_series.tsv` holds the counts of every size).
- `results/`: pass/fail summaries only (the last two lines of each run output), not the full logs.
