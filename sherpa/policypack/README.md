# policypack: the default pack library

Four layers, stacked in this order. A pack is one folder; the folder it sits in is its layer.

| Layer | Folder | What is in it |
|---|---|---|
| 0 | `base/` | Only what lets the kernel run: the `init` command and the seat `human`. No rules. |
| 1 | `classic_lifecycle/` | One delegation: an upper hands a task to a lower. Its nine checkpoints are the rows of `flow.tsv`. |
| 2 | `classic_lifecycle_pack/<pack>/` | Packs that hang on those checkpoints. One folder per pack. |
| 3 | `custom_lifecycle/<name>/` | An organization: who is whose upper (the declaration). None ships here; the user supplies one (see `../example/sherpa/policypack/PPOtest2CtoTeam/`). |

## The packs here

| Pack | Layer | What it does | Requires |
|---|---|---|---|
| `base` | 0 | `init`; the seat `human` | none |
| `classic_lifecycle` | 1 | The nine checkpoints and the task's state changes; two facts for rules to read: one task's record, and every task's state; the rule "dispatch only to your own lower" | `base` |
| `audit` | 2 | One audit row per check result; one commit per command | `base` |
| `git` | 2 | The code checkout as a fact; git rules at takeoff, landing and receipt; installs the commit hook | `base`, `classic_lifecycle` |
| `task_card_check` | 2 | A task's record is complete before dispatch writes it | `base`, `classic_lifecycle` |
| `worktree` | 2 | Each task gets its own working folder | `base`, `classic_lifecycle` |

## What a pack may contain

| File | Meaning |
|---|---|
| `policy_pack.toml` | Name, layer, the packs it requires, what it reads and writes |
| `flow.tsv` | Checkpoints: one row per command (who may issue it, from which states, to which state) |
| `checks.tsv` | Rules: which check runs at which checkpoint, and whether a failure refuses or only warns |
| `outputs.tsv` | Actions run after a command passed or was refused |
| `roles.tsv` | Seats |
| `plugins.tsv` | Where the code of each check, action and fact is |
| `*.py` | That code |

The compiler (`../ppo/`) stacks the enabled packs layer by layer into five tables; the kernel (`../kernel/`) reads
only those tables.
