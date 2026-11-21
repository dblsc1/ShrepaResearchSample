# Sherpa scale line (the paper's Sherpa numbers for the role-shaped organization)

- No upstream: Sherpa is the authors' own system. The research copy is the repo `_scale/sherpa/modified`; it starts from tag `sherpa-pristine` (`41d01a50645db108417f19bb0dd291831a41548c`, "Sherpa as measured", 2026-11-17).
- Seat classes and the shared role card are part of Sherpa (compiler change `sherpa/seat-class.patch`; one card per role, a seat's own information comes from its task card). The paper's Sherpa line is tags `sizecc-<k>` and branches `sizecc-<k>-{add-seat,add-same,add-seat-rule,add-layer,add-group}` (add-same = a further seat of an existing role) and `sizecc-<k>-move` (re-parenting, k = 2 and 16), k = 1, 2, 4, 8, 16: these are THE Sherpa numbers. Patches for k = 1 and 16 (move: k = 2 and 16) are in `patches/`; results in `results/size-shared-role-card/` and `results/move-shared-role-card/`.
- Earlier forms, kept as ablations: seat classes with one card per seat (tags `sizec-<k>`, `data/without-shared-role-card/`) and no seat class (tags `size-<k>`, `data/without-seat-class/`).
- Licence of the research copy: not stated in the files read; the licence of Sherpa is for the authors to decide (see `LICENSES.md`).

Regenerate the trees: `scripts/make_sizes_class.sh` (flag `--class-cards` of `gen_scale.py` gives the shared role card) or `scripts/make_sizes.sh`; acceptance: `PREFIX=sizecc scripts/run_size.sh <k>...` (needs the research repo and a machine with enough memory). In `results/size-shared-role-card/k<k>/summary.txt` the over-reach list and the five change tables report 0 mismatches on the change branches and the "before" (reverse) runs on the start tag report mismatches, for all five sizes.

## What is here

- `reports/`: the owner session's report(s), copied as they are (Chinese). Session names and message numbers in them are the authors' working notes.
- `scripts/`: the owner's generator, counting and acceptance scripts, copied as they are. They read research repos that are not shipped, so they are for reading; the numbers they produced are in `data/`.
- `patches/`: one `git diff <base>..<branch>` per change; the first line of each file names the refs. For size sweeps only size 1 and the largest size are shipped. The other sizes come from the same generator with another size argument (see the owner report), or from `git diff` in the research repo (`data/scale/git_series.tsv` holds the counts of every size).
- `results/`: pass/fail summaries only (the last two lines of each run output), not the full logs.
