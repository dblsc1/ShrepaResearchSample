# Bernstein (role-oriented subject)

- Repository: https://github.com/sipyourdrink-ltd/bernstein (the `origin` URL of `bernstein/modified`)
- Commit all work started from: `cb761c69b3d11689233e5e7a9ed07fdb26b9e7e5` (2026-10-29, tag `baseline`)
- Licence: Apache License 2.0 (`LICENSE` of that commit; its `NOTICE` says "Licensed under the Apache License, Version 2.0"). See `LICENSES.md`.
- Stars in paper table 2 (1,216 on 2026-11-19): not traced to a file in this repository.

Our refs: small-scale scenarios `baseline..scenario-1..8` in `bernstein/modified` (`patches/scenarios/`); scale line in the second research repo `_scale/bernstein/modified` (base tags `scale-native-keep-k{1,4,16}`, branches `native-keep-k<s>-{seat,layer,group}`; patches for s = 1 and 16 in `patches/scale-native/`); roles-by-rules grid (branches `grid-k<s>-r2-a`, `r2-b`, `r4-a`; patches for s = 1 and 16 in `patches/grid/`).

Sherpa equivalent (`sherpa_equivalent/`), baseline `0e6cb1c055d36d2e68433f587fa7e41de1554721`. Paper version: branches with suffix `-csi` (seat classes, one shared role card per class, instance id named after the lower seat), patches in `sherpa_equivalent/patches/grid/` and `.../probes/`; Bernstein-side probe branches (`grid-k<s>-r1-a`, `probe-k<s>-layer-r1`, `probe-k<s>-move`) in `patches/probes/`. The own-cards seat-class set (`-c`, `baseline-c`) is under `data/without-shared-role-card/patches/`, the no-class set under `data/without-seat-class/`. The eight small scenarios exist only without a class version.

## What is here

- `reports/`: the owner session's report(s), copied as they are (Chinese). Session names and message numbers in them are the authors' working notes.
- `scripts/`: the owner's generator, counting and acceptance scripts, copied as they are. They read research repos that are not shipped, so they are for reading; the numbers they produced are in `data/`.
- `patches/`: one `git diff <base>..<branch>` per change; the first line of each file names the refs. For size sweeps only size 1 and the largest size are shipped. The other sizes come from the same generator with another size argument (see the owner report), or from `git diff` in the research repo (`data/scale/git_series.tsv` holds the counts of every size).
- `results/`: pass/fail summaries only (the last two lines of each run output), not the full logs.
