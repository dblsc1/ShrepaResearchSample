# TradingAgents (process-oriented subject)

- Repository: https://github.com/TauricResearch/TradingAgents (`origin` URL of `TradingAgents/modified`)
- Commit all work started from: `9fa1196fffbcfd9de5146d2dd2869df84ab99838` (2026-11-04, tag `baseline`; the scale repo `_scale/tradingagents/modified` has the same `baseline`)
- Licence: Apache License 2.0 (`LICENSE` of that commit). See `LICENSES.md`.
- Stars (123,060 on 2026-11-19): not traced to a file here.

Our refs: small-scale scenarios `baseline..scenario-1..8` (`patches/scenarios/`); scale line `size-<s>` tags and `size-<s>/{a1,a2,b,c,c2,d}` branches, s = 1, 2, 4, 8 (`patches/scale/` ships s = 1 and 8); roles-by-rules grid (`patches/grid/`, the 36 corner cells of `data/grid/tradingagents_rules_count_corners.tsv` and its by-seat part).

Sherpa equivalent (`sherpa_equivalent/`): research repo `_scale/tradingagents/sherpa`. Paper version (seat classes, one role card per role): tags `size-<s>-c-rolecard`, branches `size-<s>/{a,c,d}-c-rolecard` and `size-<s>/split-teams-swap-read-runs-c-rolecard` (compound change), s = 1 and 8 patches in `sherpa_equivalent/patches/scale/` and `.../grid/`; the per-role-rule change does not touch a card and keeps branch `size-<s>/b-c`. Probes (L, R, L+R, re-parenting): `patches/probes/` (both sides). Own-cards seat-class branches (`-c`) are in `data/without-shared-role-card/patches/`; the no-class ones in `data/without-seat-class/patches/`. Small-scale equivalent baseline `22f73a0a1c9187f8eec8e2edb5bc8e0f2e535e86`; scenario 3 is based on `baseline-with-tool-rules`, the other seven on `baseline`. Sherpa side: seat-class tags and shared role card are part of Sherpa; no upstream.

## What is here

- `reports/`: the owner session's report(s), copied as they are (Chinese). Session names and message numbers in them are the authors' working notes.
- `scripts/`: the owner's generator, counting and acceptance scripts, copied as they are. They read research repos that are not shipped, so they are for reading; the numbers they produced are in `data/`.
- `patches/`: one `git diff <base>..<branch>` per change; the first line of each file names the refs. For size sweeps only size 1 and the largest size are shipped. The other sizes come from the same generator with another size argument (see the owner report), or from `git diff` in the research repo (`data/scale/git_series.tsv` holds the counts of every size).
- `results/`: pass/fail summaries only (the last two lines of each run output), not the full logs.
