# Licences of the upstream systems

Each source tree under `systems/<system>/origin/` is an unmodified copy of the upstream repository at the commit named in
`systems/<system>/UPSTREAM.md`, redistributed under that system's own licence. The licence file is `LICENSE` in that folder
(Bernstein also has `NOTICE`).

| System | Folder | Licence |
|---|---|---|
| Bernstein | `systems/bernstein/origin/` | Apache-2.0 |
| TradingAgents | `systems/tradingagents/origin/` | Apache-2.0 |
| deer-flow 1.x | `systems/deer-flow-1.x/origin/` | MIT |
| deer-flow 2.0 | `systems/deer-flow-2.0/origin/` | MIT |
| Paperclip | `systems/paperclip/origin/` | MIT |
| Gas Town | `systems/gas-town/origin/` | MIT |

The `git diff` files under `systems/<system>/example/changes/` quote lines of the upstream files and fall under the same
licences.
