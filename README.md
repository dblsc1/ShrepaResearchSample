# Material for the paper "A Checkpoint-Based Design Approach for Multi-Agent Governance Systems"

| Path | Content |
|---|---|
| `sherpa/` | A minimal, runnable Sherpa: `kernel/`, the compiler `ppo/`, the default rule packs `policypack/`, and `example/`, the project of Section III (run `python3 -I run_example.py` to rebuild it; `example_transcript.txt` is the transcript of its 24 commands). |
| `systems/<system>/UPSTREAM.md` | Repository, commit and licence of each system studied. |
| `systems/<system>/origin/` | The system's source at the commit all work started from (tracked files only, under the system's own licence). |
| `systems/<system>/example/changes/` | The four changes of the six-panel figure as `git diff` files for k = 1, 2, 4, 8, and `counts.tsv` with the lines each adds. `a`, `b`: add k executors on a tree whose k rules name no role / name roles. `d`, `e`: install k rules that name no role / name roles on a tree with k more executors. Gas Town adds executors at run time, so it has only `d` and `e`. |
| `systems/<system>/example/sherpa_rebuild/` | The Sherpa counterpart of the system: its declaration with role cards, and the rule packs it uses under `packs/`. For Bernstein and TradingAgents, whose core rules were rebuilt, also `REPORT.md` and `tests/` with the baseline acceptance case tables and their results on both sides. Paperclip has no counterpart of its own: its team has the shape of Sherpa's own tree. |
| `systems/sherpa/example/changes/` | The same four changes on Sherpa. |
| `systems/<system>/example/changes/REPORT.md` | The working report of the changes on that system (Bernstein, TradingAgents, deer-flow, Paperclip, Sherpa): where each rule was written and which existing code of the system it follows. |
| `measurement/` | The definition of the two groups of rules and of the added executors, and the script that counts the added lines. |
| `issue-census/` | The classification of GitHub issues behind the figures of the introduction, with its limits. |
| `reference-matrices/` | The reference matrices (one row per rule, one column per role) and the notes on how they were counted. |
| `build_artifact.py` | Rebuilds `systems/` from the research tree (not included). |

The reports and notes are working documents and are partly in Chinese.
