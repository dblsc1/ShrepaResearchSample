# TradingAgents 的 Sherpa 等价物

> 2026-11-17，zumi 写。依据规程第 12 节、「提速办法」和「强制性要对等」两节，做法照 `_pairing/HOWTO.md`。
> 做完了：清单、等价物、等价性检验，以及在等价物上重做八个场景（场景 3 不可比）。
> 方案和 mero 的答复见 `PLAN.md`；使用反馈见 `SHERPA_FEEDBACK.md`。

## 0 覆盖了几条

> **11-18 更新：** 在 razu 的新包上另开一条线 `baseline-with-tool-rules`，覆盖从 5 条变成 9 条（R3 完整，R4、R5、R8 近似），R10 没有对应物。见第 7 节。下面是原来 `baseline` 上的情况，保留不改。

清单按 10 条规则算（R11「读不出评级记 REVIEW」只改记录的值、不拒绝动作，按 mero 定的口径移到存疑，不计入）。

**复现 5 条，没有复现 5 条。**

- 复现：R1 风险审核、R2 研究审核、R6 分析员只交回自己的报告（近似）、R7 辩论轮数上限（只在默认的一轮下）、R9 五路汇合。
- 没有复现，分两种（人类 11-18 更正：Sherpa 能做工具级权限和调用次数，只是还没写包，不许直接记成表达不了）：
  - **待新包做完重判**：R3 工具范围、R8 工具轮数上限（`_capability/` 正在用运行时钩子做工具级权限和工具调用次数上限）；R4 数据日期、R5 数据标的（取数也是工具调用，可以挂在同一个钩子上；TradingAgents 是改写参数，只拦不改够不够，等新包再判）。这四条现在没有复现，原因是现有包的检查只挂在生命周期命令和提交上，还没有挂在「agent 调工具」上的包。
  - **没有对应物**：R10。它检查的是 LangGraph 执行引擎自己的配置（工具轮数要放得进递归上限），Sherpa 没有递归上限这个概念，这条不适用。

组织 14 个座位全部搬了。要说明的近似：TradingAgents 的上级（研究经理、投资组合经理）只裁定、不派单，谁什么时候干活由图的边决定；Sherpa 的上级既派单又收单。

## 1 等价物是什么

- `modified/`：Sherpa 内核加规则包仓的副本（取自 `sherpa/original/`，即内核 `93ffd25` 加未提交改动、规则包仓 `d9838a5`），git 仓库。标签 `sherpa-pristine` 是原样副本，`baseline` 是加上等价物之后。`original/` 是 `git archive baseline` 解包，只读。
- 内核 `Core/`、编译器 `ppo/`、`base/`、`classic_lifecycle/` 和现有 13 个包都没改（`count_sherpa.py` 的 kernel、compiler 两栏是 0）。
- 工作流 `PPOtestTradingAgents`（占位名）：14 个座位，13 个 `classic_lifecycle` 实例。

```
human
 └─ portfolio_manager
     ├─ research_manager
     │   ├─ market_analyst / sentiment_analyst / news_analyst / fundamentals_analyst
     │   └─ bull_researcher / bear_researcher
     ├─ memory_log
     ├─ trader
     └─ aggressive_analyst / conservative_analyst / neutral_analyst
```

| TradingAgents | 等价物里怎么写 | 包 |
|---|---|---|
| 图上写死的先后：五路汇合后才辩论（R9）；空头在多头之后；交易员在研究经理裁定之后（R2）；风险组在交易员之后、三人依次（R1） | 工作流参数 `after.<座位>=<座位>,...`：派给这个座位的单必须 `--waits-for` 每个前置座位的单，没写就在派单时拒绝；写了，开工时由 `waits_for` 拦住没结束的。可以跨上级等待（多头研究员由研究经理派，要等投资组合经理派的 memory_log） | 新包 `fixed_order`，加现有 `waits_for` |
| 裁定者必须听完：研究经理要等多空辩论（R2），投资组合经理要等风险审核（R1） | 工作流参数 `needs.<座位>=<座位>,...`：交回之前必须派过每个列出的座位；派出的单都要结束 | 新包 `fixed_order`，加现有 `parallel_wait_all` |
| 每个节点只跑一次，辩论一轮（R7） | 每个座位最多打回 0 次 | `_pairing/packs/reopen_limit`（ChatDev 那对写的） |
| 分析员只交回自己的报告（R6） | 每个分析员只能提交 `reports/<自己>.md`；其他座位不限，和 TradingAgents 一致 | `_pairing/packs/seat_write_limit`（ChatDev 那对写的） |

装的包：`base, classic_lifecycle, git, worktree, task_card, waits_for, parallel_wait_all, fixed_order, seat_write_limit, reopen_limit`。不装 `write_scope`、`worklog`、`review_rules`、`max_open_lowers` 和只有输出的包：TradingAgents 起点上没有对应的规则（场景 4 才加「审的人不能是写的人」）。

**为什么新写 `fixed_order`，不用 naga 的 `seat_precedence`**：`seat_precedence` 只认同一个上级派的单，TradingAgents 的五路汇合里 memory_log 和分析员不在同一个上级下面。`fixed_order` 的 `after` 一半强制派单时声明等待，可以跨上级；`needs` 一半就是方案里的 `required_lowers`。两个检查合成一个包，已放进 `_pairing/packs/fixed_order/`。

## 2 搭建成本（跑过的：`python3 -I _pairing/count_sherpa.py modified sherpa-pristine baseline`，输出 `tests/runs/build-cost.txt`）

合计 39 个文件、+397 行，全是新增：

| 部分 | 文件 | 行 | 出处 |
|---|---|---|---|
| 工作流文件 `PPOtestTradingAgents.toml` | 1 | 125 | 新写（13 个实例，每个 6 行，占了一大半） |
| 工作流的 `policy_pack.toml` | 1 | 8 | 新写 |
| 角色卡 `cards/*.md` | 14 | 68 | 新写，正文抄 TradingAgents 各角色提示词的开头，末尾一两句 Sherpa 操作 |
| 新包 `fixed_order` | 6 | 77 | 新写 |
| `reopen_limit` | 7 | 72 | 复用 `_pairing/packs/`（naga 写） |
| `seat_write_limit` | 4 | 41 | 复用 `_pairing/packs/`（naga 写） |
| 三个包的 `cases/` 占位 | 6 | 6 | 写成 todo：`pack_cases.py` 只认五个固定的人，也设不了工作流参数；这几个包由用例表覆盖 |

按四栏：内核 0；规则（`classic_lifecycle_pack/`）17 个文件 +190；声明文件（`custom_lifecycle/`）16 个文件 +201，其中卡片 14 个文件 +68；编译器和基础生命周期 0；测试 6 个文件 +6。

## 3 等价性检验（跑过的）

用例表 `tests/flow_baseline.tsv`，28 行，用通用运行器 `_pairing/run_table.py` 跑（真的 ppo 构建，真的内核命令，每行一个新的临时项目）。**28 行判决全部和 TradingAgents 一致**，结果在 `tests/flow_baseline.results.tsv`，打印输出在 `tests/runs/flow_baseline.txt`。

| 规则 | 行 | 放行 | 拒绝 | 其中「上级漏写或想跳过」 |
|---|---|---|---|---|
| R9 五路汇合 | B1–B5 | 1 | 4 | B4（漏了 memory_log）、B5（一个都没写），红码 `fixed_order.missing_wait` |
| 多头 → 空头 | B6–B8 | 1 | 2 | B8 |
| R7 一轮 | B9–B11 | 1 | 2（`reopen_limit.limit_reached`） | — |
| R2 研究审核 | B12–B17 | 2 | 4 | B14（交易员不等研究计划）、B15（研究经理没开辩论就交回，`fixed_order.missing_lower`） |
| R1 风险审核 | B18–B24 | 2 | 5 | B19、B21（风险组不按顺序）、B22（投资组合经理不经风险审核就交回，`fixed_order.missing_lower`） |
| R6 只交回自己的报告 | B25–B28 | 2 | 2（`seat_write_limit.outside_seat_paths`） | — |

每一行的 `source` 列写着对应 TradingAgents 的哪条测试或哪条图的边（`../ORG_AND_RULES.md` 的规则表和关系表）。TradingAgents 那一侧，这些判决由图的结构给出：边上没有的跳转不会发生，不需要显式拒绝；对应的上游测试都在基线里通过（`../tests/runs/baseline-full.txt`）。

**翻不过来的 TradingAgents 用例**（都属于没有复现的 R3、R4、R5、R8、R10；R3、R4、R5、R8 待新包做完重判）：

- R3：`../tests/acceptance/test_starting_point_rules.py::test_rule_A_another_analysts_tool_is_not_run`、`test_rule_A_own_tool_runs`。
- R4：上游 `test_tool_date_enforcement.py::test_future_curr_date_from_the_model_is_clamped`、`test_future_window_from_the_model_is_clamped`、`test_trade_date_is_hidden_from_the_model` 等。
- R5：上游 `test_tool_date_enforcement.py::test_a_tool_serves_the_run_instrument_whatever_the_model_passes`、`test_the_instrument_is_hidden_from_the_model`。
- R8：上游 `test_graph_end_to_end.py::test_an_analyst_that_keeps_calling_tools_writes_its_report_at_the_limit`、`test_the_last_turn_is_offered_no_tools_and_reads_its_tool_results_as_text`。
- R10：上游 `test_graph_end_to_end.py::test_a_tool_limit_the_recursion_limit_cannot_hold_is_refused`。

原因：这些判决发生在一次运行内部（工具调用、工具参数、执行引擎的配置），等价物现有的包只在任务的派单、开工、提交、交回、收单上做判决。R3、R4、R5、R8 是还没有包，R10 是没有对应物。

## 4 等价物树自己的测试（跑过的）

和 `sherpa/` 做实验用的同一个虚拟环境（`sherpa/.venv`），`pytest -n 2`：

| 测试集 | 通过 | 失败 | 跳过 | 和 Sherpa 基线比 |
|---|---|---|---|---|
| 内核 `modified/Tests` | 130 | 0 | 1 | 一致（跳过的是负载高时不判的计时测试） |
| 规则包整理器 `modified/SherpaPolicyPackOrganizer/Tests` | 53 | 0 | 11 | 通过数一致；多出的 6 条跳过是三个新拷进来的包各 2 条 todo 用例（见第 2 节） |

原始输出：`tests/runs/sherpa-tests-baseline.txt`、`tests/runs/ppo-tests-baseline.txt`。

## 5 比 TradingAgents 弱或只是近似的地方

- **上级的角色**：TradingAgents 的上级只裁定；Sherpa 的上级还要派单、收单。先后和汇合在 TradingAgents 里由图自动推进，在这里要上级按顺序派单（顺序错了、漏了会被拒绝，但推进要人或 agent 来敲）。
- **R6**：TradingAgents 限的是状态字段，这里限的是文件路径。
- **R7**：只在默认的一轮下对等（打回 0 次）。多轮时有两处现成包写不出来：多空交替（`waits_for` 要被等的单已经结束，而结束了的单不能再打回；naga 在 HOWTO 3.1 里遇到同样的问题，写明强制会死锁），以及「必须说满轮数」（`reopen_limit` 只管上限）。后面场景遇到时，用不了的用例记为翻不过来。
- **建模选择**：TradingAgents 的分析员没有明写的上级，这里放在研究经理下面；Memory Log 放在投资组合经理下面。mero 已同意。
- **`after` 的一个漏洞**：派单时只检查「等的单里有前置座位的单」，不检查那张单是不是这一次运行的。上级等一张以前运行留下的、早已结束的同座位单，也能通过。TradingAgents 每次运行是一张新图，没有这个问题。

## 6 在等价物上重做八个场景

做法和 TradingAgents 侧一样（同样的映射和退路，新角色同样的占位名）。每个场景：从 `baseline` 开分支；把 TradingAgents 这个场景的验收测试逐条翻成 `tests/scenario_N.tsv`，用 `tests/pairing_scenario_N.toml`（宏按这个场景的组织改了）跑；再用原来的 `pairing.toml` 把 28 行基线表在这个分支上重跑一遍（`tests/run_baseline_on.sh N`），会变的行事先写在 `tests/expected-changes.md`。计数用 `python3 -I _pairing/count_sherpa.py modified baseline <分支>`，输出 `tests/runs/counts.txt`。

### 6.1 并排

TradingAgents 的数见 `../REPORT.md` 第 5 节（规则 / 规则兼组织 / 组织定义 / 框架本体四类）。等价物这边按 Sherpa 四栏：内核、规则包、声明文件、编译器和基础生命周期；八个场景里内核、规则包、编译器三栏全是 0，改动全在声明文件里（工作流文件、`policy_pack.toml`、角色卡）。

| 场景 | TradingAgents 文件 / 处 / +行 / −行 | 等价物 文件 / 处 / +行 / −行（全在声明文件） | 其中角色卡 | 等价物验收用例 | 基线表重跑 |
|---|---|---|---|---|---|
| 1 加角色 | 4 / 9 / +63 / −3 | 3 / 5 / +16 / −3 | 2 个文件 +6 −1 | 7 行，全部对上 | 变 1 行（B24），和预计一致 |
| 2 减角色 | 5 / 14 / +10 / −22 | 2 / 4 / +3 / −11 | 1 个文件 +1 −1 | 4 行，全部对上 | 变 3 行（B21、B23、B24），和预计一致 |
| 3 收窄范围 | 1 / 3 / +1 / −3 | 原 `baseline` 上不可比；在 `baseline-with-tool-rules` 上 1 / 1 / +1 / −1（见 7.4） | 0 | 4 行，全部对上 | 基线表、工具规则表都不变 |
| 4 加规则 | 2 / 3 / +34 / −8 | 1 / 1 / +1 / −1 | 0 | 5 行，全部对上 | 不变（安装时加上 `review_rules`） |
| 5 减规则 | 3 / 6 / +3 / −8 | 2 / 2 / +3 / −3 | 1 个文件 +2 −2 | 3 行，全部对上 | 变 1 行（B22），和预计一致 |
| 6 加层 | 6 / 11 / +33 / −2 | 3 / 6 / +19 / −6 | 2 个文件 +6 −1 | 8 行，全部对上 | 变 6 行（预计 7 行，B19 没变） |
| 7 加嵌套 | 4 / 10 / +55 / −5 | 3 / 5 / +17 / −4 | 2 个文件 +6 −1 | 7 行，全部对上 | 变 23 行（预计 24 行，B2 没变） |
| 8 复合（1+4） | 5 / 10 / +98 / −11 | 4 / 6 / +17 / −4 | 2 个文件 +6 −1 | 2 行新的 + 场景 1 的 7 行全部对上；场景 4 的 5 行里 S4-1 对不上（见 6.2） | 变 1 行（B24），和预计一致 |

读数时要注意：

- **工作流参数写在一行里。** `fixed_order`、`seat_write_limit`、`reopen_limit` 的参数各是一整行字符串，加一个座位、去一个座位都只算这一行的「1 处 +1 −1」。所以等价物的处数和行数会偏小；改的规则条目数要看参数内容（例如场景 1 在这三行里各加了一项）。
- **等价物里的近似。** 场景 6、7 在等价物里是真正的嵌套（新的一层既派单又收单），TradingAgents 里新的一层只是图上的先后（不派单）。场景 4 用的是现有的 `review_rules`（审核单不能派给被审单的承办人），TradingAgents 侧是新写的检查（审核节点不能审自己写过的字段）。
- **这些数不含翻用例。** 用例表算测试，不进上面的计数。

### 6.2 每个场景

**场景 1，加合规分析员（占位名，对应 `security_reviewer`）。** 工作流里加一个实例（投资组合经理 → 合规分析员）和一个座位；`fixed_order` 加 `after.compliance_analyst=neutral_analyst`、在 `needs.portfolio_manager` 里加上它；`reopen_limit` 加它的 0 次；新卡片 1 张；投资组合经理的卡片里点了风险组的名单，跟着改。验收 7 行：整轮跑完后投资组合经理交回（放行）；合规分析员在中立分析员之后开工（放行）；三人说完还不能交回（拒绝，`missing_lower`）；合规分析员没说完不能交回（拒绝）；中立分析员没说完合规分析员不能开工（拒绝）；不按顺序派它（拒绝，`missing_wait`）；打回它（拒绝，一轮）。翻不过来的：`test_allowed_round_cap_counts_its_turns`（两轮配置，要改工作流参数，而且多轮的交替写不出来），以及 `test_rejected_...` 里「合规分析员说完后进入第二轮」那一个断言。

**场景 2，去掉中立分析员。** 工作流里去掉它的实例和座位，三行参数里去掉它；投资组合经理的卡片改名单。和 TradingAgents 侧一样取最小读法：中立分析员的卡片文件留着（TradingAgents 侧留着它的代码文件）。验收 4 行：两人说完交回（放行）；投资组合经理再派中立分析员（拒绝，`classic_lifecycle.not_your_lower`，它已不在组织里）；保守仍在激进之后（拒绝）；保守没审不能交回（拒绝）。翻不过来的：`test_allowed_full_run_reviews_with_the_two_remaining_analysts` 里两轮计数的部分；`test_rejected_the_remaining_prompts_no_longer_address_the_neutral_analyst`（查提示词内容，不是治理判决）。

**场景 3，不可比。** TradingAgents 侧退到了工具范围；等价物里没有工具范围（R3 没有复现），照实记为不可比，没有开分支。

**场景 4，加「审的人不能是写的人」。** 装现有包 `review_rules`：工作流的 `policy_pack.toml` 的 `requires` 加一项（1 处 +1 −1），规则包和卡片都不改。验收 5 行：风险分析员带 `--reviews <交易员的单>` 审，整轮跑完（放行）；投资组合经理、激进分析员、研究经理各自去审自己的单（拒绝，`review_rules.author_is_reviewer`，3 行）；别人审交易员的单（放行）。要说明：`review_rules` 只管带了 `--reviews` 的派单，上级不写 `--reviews` 就不算审核单；但在这个组织里审核座位和作者座位是不同的执照，不写 `--reviews` 也派不出「自己审自己」的单。TradingAgents 侧的新检查同样只在状态被改过时才会拒绝。

**场景 5，去掉风险审核环节。** `needs.portfolio_manager` 去掉三位风险分析员（1 处 +1 −1）；投资组合经理的卡片照 TradingAgents 侧提示词的改法改（2 处）。三位风险分析员的座位留着，和 TradingAgents 侧「三个风险节点留在图里但走不到」对应。验收 3 行：交易员之后直接交回（放行）；交易员仍要等研究计划（拒绝）；研究经理仍不能不开辩论就交回（拒绝）。

**场景 6，插风险组长（占位名，对应 `team_lead`）。** 加实例「投资组合经理 → 风险组长」，三位风险分析员的上级改成风险组长（3 处），`needs` 改成投资组合经理要风险组长、风险组长要三位风险分析员，`reopen_limit` 加它；新卡片 1 张，投资组合经理的卡片改一句。验收 8 行：风险组长在三位之后交回（放行）；投资组合经理在风险组长之后交回（放行）；投资组合经理直接派风险分析员（拒绝，`not_your_lower`）；投资组合经理不经风险组长交回（拒绝）；风险组长在中立分析员没说完时交回（拒绝）；风险组长少派一位（拒绝）；新上级下顺序照样管（拒绝，`missing_wait`）；新上级下打回照样限次（拒绝）。翻不过来的：两轮计数，以及「投资组合经理的提示词里有风险组长的意见」（查内容）。基线表里 6 行在前置步骤失败，因为它们写死了「投资组合经理派风险分析员」，而等价物把汇报线真的改了；TradingAgents 侧只变了 2 条路由测试。

**场景 7，基本面分析员带财报分析员（占位名，对应 `helper`）。** 加实例「基本面分析员 → 财报分析员」和座位；`needs.fundamentals_analyst=statements_analyst`（TradingAgents 里下级在子图里总是先跑，绕不过去，这里也要绕不过去）；`seat_write_limit` 加它只能写 `reports/statements_analyst.md`；`reopen_limit` 加它；新卡片 1 张，基本面分析员的卡片加一句。验收 7 行：基本面分析员在下级之后交回（放行）；整轮跑完（放行）；下级写别人的报告（拒绝）、写自己的（放行）；基本面分析员不派下级就交回（拒绝）；下级没做完就交回（拒绝）；打回下级（拒绝）。翻不过来的（都属于没有复现的 R3、R4、R5、R8）：下级调不了分析员的工具；分析员调不了移给下级的工具；下级取数用本次运行的标的和日期；下级的工具轮数上限。TradingAgents 侧把三张报表的工具从分析员移给了下级，等价物里没有工具，这一半没有对应。基线表里 23 行在前置步骤失败：在 Sherpa 里加一层嵌套，上一层就多了必须做的事（派下级、收单），表里写死的「基本面分析员直接交差」不再成立；TradingAgents 侧下级在子图里自动跑，调用方不用管，上游测试只变了 2 条计数。

**场景 8，复合。** 把场景 1、4 的提交摘过来，没有冲突，改动正好是两者之和。验收：新加 2 行（合规分析员带 `--reviews` 审交易员的单、整轮跑完，放行；合规分析员去审自己的单，拒绝）；场景 1 的 7 行原样全部对上；场景 4 的 5 行里 S4-1 对不上：这一行的前置步骤没派新加的合规分析员，投资组合经理交回时被 `fixed_order.missing_lower` 拦下。TradingAgents 侧整张图会自动带上新角色，场景 4 的测试原样通过；这里要把新角色写进前置步骤，补上后的同一条用例就是 S8-1，通过。等价物树自带测试在这个分支上全量跑：内核 130/0/1、规则包 53/0/11，和 `baseline` 一致（`tests/runs/sherpa-tests-scenario-8.txt`、`ppo-tests-scenario-8.txt`）。

### 6.3 和 naga 的 `seat_precedence` 的关系

功能有重叠，和 naga 商量后**先不合**：两对都已经用各自的包做完了等价性和场景，合并要重算两边的搭建成本和计数；两个包拦的时点不同：`seat_precedence` 在开工时拦，不看派单声明，只认同一上级；`fixed_order` 的 `after` 在派单时要求声明 `--waits-for`，可以跨上级；`needs`（交回前必须派过）`seat_precedence` 没有。naga 已在 HOWTO 第 3 节写明各管什么；ChatDev 那对的场景 7 复用了 `fixed_order` 的 `needs`。真要合的方向：给 `seat_precedence` 加一种不限上级的写法，再把 `needs` 并进去。

## 7 装上工具规则包以后（2026-11-18，回答 mero #17552）

### 7.1 做了什么

`modified` 从 `baseline` 另开一条线 `baseline-with-tool-rules`（占位名）。原来的 `baseline` 和八个场景分支没有动。

- **拷进来的包**，都来自 razu（`_capability/REPORT.md`），从 `_pairing/packs/` 原样拷，一字没改：
  - `seat_tool_allowlist`：新命令 `tool-call`，按座位的工具表；
  - `tool_call_limit`：一张单最多放行几次工具调用；
  - `token_budget`：只因为这些包自带用例所用的测试工作流 `PPOtestToolGate` 需要它才拷，交易团队的工作流不装；
  - `PPOtestToolGate` 本身也一起拷了。
- **交易团队的工作流**（`PPOtestTradingAgents`）：`requires` 加了两个包；工作流文件里加两张参数表，注释写着每条对应 TradingAgents 的哪条规则、哪里只是近似。
  - **R3**：13 个座位每个一张工具表。
    - TradingAgents 的 12 个取数工具（11-18 更正：原写 13，数错了；市场 3、新闻 4、基本面 5），记为一个 MCP 服务的工具 `mcp__trading__<名>`。TradingAgents 注入的参数（标的、日期）在这里显式传。这是建模选择。
    - 四位分析员各自只有自己那组工具，情绪分析员没有取数工具；其余 9 个座位都没有取数工具。在 TradingAgents 里，分析员以外的节点调模型时根本不带工具。
    - 每个座位都有干一张 Sherpa 单要用的工具：读 `reports/`、`src/`，以自己的执照敲 `sherpa`，`git add`，`git commit -m <消息>`。分析员只能写自己那份报告。
  - **R4、R5**：取数工具的条件写成 `symbol=@ticker`、`end_date<=@date` 这类。研究经理派单给分析员时，把这次运行的 `--ticker`、`--date` 写在卡片上。
  - **R8**：每位分析员一张单最多 26 次工具调用，即 20 次取数（TradingAgents 的 `max_tool_rounds`）加 6 次干活要用的调用（开工两次、写报告、git add、git commit、交回）。

**安全复查改了两次 `git commit` 的写法。** 第一版用的是「`git commit *`，但不许出现 `--no-verify`、` -n`」，后台安全复查指出能绕。
- 第一次复查：`-an`（短选项连写）、`--no-veri`（git 接受缩写）能绕过去。
- 第二次复查：`'-n'`（加引号）、用制表符隔开的 `-n` 也能绕。
- 现在的写法只放行 `git commit -m <消息>`：不许长选项；短选项只许 `-m`；消息里只许字母、数字、空格和 `._/-`。
- 制表符本来就不能写进规则：参数会编进一张 TSV 表，写了 `ppo` 构建就报 `policy.bad_table`，我第一次就踩到了。
- 就算有人绕过了提交钩子，交回（`debrief`）时 `seat_write_limit` 和 `write_scope` 会再查一遍提交的文件。
- `sherpa --inst` 这条规则拒；缩写 `--ins` 能过这条规则，但内核自己拒（`identity.mismatch`，执照和 `SHERPA_INST` 对不上），razu 实测过。
- 对应的用例是 X-2 到 X-7。

**运行器。** `_pairing/run_table.py` 加了三样，只加不改，共 +24 行：派单可以带任意「键 值」；前置步骤 `tool T1 <工具名> <JSON>`；被检查的一步可以是 `does = tool-call`。都是在单的工作树里按钩子的方式敲 `sherpa tool-call`，不起模型。旧表不受影响：本仓 28 行基线表和 naga 复核的 ChatDev 22 行，判决和红码都逐条相同。HOWTO 第 4 节已补。

### 7.2 覆盖：10 条里从 5 条变成 9 条

| 规则 | 原来 | 现在 | 用例（`tests/tool_rules.tsv`，`pairing_tools.toml`） |
|---|---|---|---|
| R3 每位分析员只能用自己那组工具 | 没有复现 | **完整** | T3-1 到 T3-5 |
| R4 取数日期不能晚于运行日期 | 没有复现 | **近似**：TradingAgents 把日期压回运行日期并照常取数，日期对模型隐藏；这里拒绝这次调用，拒绝原因里说出允许的日期 | T4-1 到 T4-4 |
| R5 取数标的只能是本次运行的 | 没有复现 | **近似**：TradingAgents 不管模型传什么都取本次标的，标的也对模型隐藏；这里拒绝 | T5-1、T5-2 |
| R8 分析员工具轮数上限 | 没有复现 | **近似**：TradingAgents 数的是「带工具调用的模型回合」，到上限后给最后一回合不带工具、让它写报告；这里数的是单次调用，到上限后再调什么都拒，写报告和交回也包括在内 | T8-1、T8-2 |
| R10 工具上限要放得进递归上限 | 没有对应物 | 没有对应物（Sherpa 没有递归上限） | — |

- **现在复现的 9 条：** R1、R2、R6、R7、R9、R3、R4、R5、R8。其中**近似的 5 条**：R6（限文件，不限状态字段）、R7（只在默认一轮下对等）、R4、R5、R8。完整的 4 条：R1、R2、R9、R3。
- **用例：** 工具规则表 20 行，全部对上（`tests/tool_rules.results.tsv`，打印输出 `tests/runs/tool_rules.txt`）。其中：
  - 13 行对应 R3、R4、R5、R8；
  - X-1：别的座位不能在别人的单上调工具，TradingAgents 没有身份，这条是 Sherpa 多出来的；
  - X-2 到 X-7：提交命令的写法；
  - X-5：分析员写别人的报告，在工具这一层就被拒（提交时的 `seat_write_limit` 仍在）。

### 7.3 之前翻不过来的断言，逐条重翻

| TradingAgents 的断言 | 现在 | 用例或缺什么 |
|---|---|---|
| `test_rule_A_another_analysts_tool_is_not_run` | 翻过来 | T3-2 |
| `test_rule_A_own_tool_runs` | 翻过来 | T3-1 |
| `test_future_curr_date_from_the_model_is_clamped` | 近似 | T4-2：那边压回日期、照常取数，这边拒绝 |
| `test_future_window_from_the_model_is_clamped` | 近似 | T4-3：同上 |
| `test_a_tool_serves_the_run_instrument_whatever_the_model_passes` | 近似 | T5-1：那边照取本次标的，这边拒绝 |
| `test_an_analyst_that_keeps_calling_tools_writes_its_report_at_the_limit` | 近似 | T8-1、T8-2：按次数不按回合；到上限后连报告也写不了 |
| `test_trade_date_is_hidden_from_the_model`、`test_the_instrument_is_hidden_from_the_model`、`test_trade_date_is_injected_not_model_visible` | 仍翻不过来 | 缺「对模型隐藏参数」：这里的拒绝原因反而把允许的值告诉了模型。要做到，得由钩子改写参数（Claude Code 钩子的 `updatedInput` 能做，包里没做），并且 MCP 工具的接口里干脆没有这两个参数 |
| `test_statement_tool_with_omitted_date_uses_the_run_date` | 仍翻不过来，判决相反 | 那边不传日期就用运行日期，放行；这里规则要求有 `curr_date`，不传就拒。缺的同上：改写参数 |
| 不带日期的两个工具（`get_insider_transactions`、`get_prediction_markets`）按运行日期截止（`test_undated_tools_as_of.py` 的相关几条） | 仍翻不过来 | 这两个工具没有日期参数，规则只能整个放行或整个拒，管不了「截止到哪天」。缺的是：改写参数，或者 MCP 服务端按卡片日期截止 |
| `test_propagate_rejects_a_future_date`（运行日期不能是未来） | 仍翻不过来 | 派单时没有检查 `--date` 是否在未来，新包管的是工具调用。要做就在 `dispatch` 上加一个检查，没做 |
| `test_the_last_turn_is_offered_no_tools_and_reads_its_tool_results_as_text` | 仍翻不过来 | 管的是模型最后一回合的内容，不是规则 |
| `test_a_tool_limit_the_recursion_limit_cannot_hold_is_refused`（R10） | 没有对应物 | — |

另外一个弱点：
- TradingAgents 里，标的和日期属于整次运行，所有分析员看到的都一样。
- 这里是研究经理给每位分析员派单时各写一次，它要是写错了（或者写了一个更晚的日期），没有检查会拦。
- 要堵，得加一个检查：分析员卡片上的值必须和上级自己卡片上的一致。这个没做。

### 7.4 场景 3（收窄范围）重做，和 TradingAgents 并排

需求：基本面分析员去掉 `get_insider_transactions`，和 TradingAgents 那边一样。分支是 `scenario-3-narrow-scope`，从 `baseline-with-tool-rules` 开。

| | TradingAgents | 等价物 |
|---|---|---|
| 文件 / 处 / +行 / −行 | 1 / 3 / +1 / −3（工具元组 −1、import −1、提示词里提到这个工具的一句改写） | 1 / 1 / +1 / −1（声明文件里基本面分析员那一行工具表去掉一项），内核、规则包、编译器 0 |
| 角色卡 / 提示词 | 改了一句：提示词里点了工具名 | 0：角色卡里没有点工具名 |
| 验收 | 3 条 | 4 行（`tests/scenario_3.tsv`），全部对上 |
| 基线表重跑 | 上游自带测试变 2 条（端到端调用过的取数方法集合少一项） | 28 行基线表、20 行工具规则表都逐条不变 |

- 4 行验收：S3-1 剩下的报表工具照常、S3-2 内部人交易被拒、S3-3 收入表照常、S3-4 整轮照样走完。
- 对照：同一张场景 3 表在 `baseline-with-tool-rules` 上跑，只有 S3-2 对不上（放行）。这正是改动造成的变化（`tests/runs/scenario_3_on_tool_rules_base.txt`）。
- 会变的行事先写在 `tests/expected-changes.md`。

### 7.5 原来的基线表在新基线上逐条不变

- 28 行基线表在 `baseline-with-tool-rules` 上跑（装着新包，分析员派单多带 `--ticker`、`--date`），`got`、`reds`、`match` 三列和 `baseline` 上逐条相同（`tests/runs/flow_baseline_on_tool_rules.results.tsv`）。
- 在 `scenario-3-narrow-scope` 上同样逐条相同。
- 八个场景没有重做，按 mero 的说法只确认这一点。

**树自己的测试：**
- 内核 `Tests/` 130 过、1 跳，和基线相同。这是在第一个提交上跑的；之后的提交只动了声明文件。
- 包整理器 `SherpaPolicyPackOrganizer/Tests` 70 过、11 跳、0 失败：原 53 条，加新拷进来三个包的 17 条用例（`seat_tool_allowlist` 12、`tool_call_limit` 2、`token_budget` 3），跳过的还是原来那 11 条。
- 原始输出：`tests/runs/sherpa-tests-tool-rules.txt`、`ppo-tests-tool-rules.txt`。
- 第一次跑 ppo 时有 16 条失败，原因是没拷 `token_budget`，测试工作流 `PPOtestToolGate` 起不来；拷上以后全过。

### 7.6 搭建成本（新包单列：新写的，不算复用）

`python3 -I _pairing/count_sherpa.py modified baseline baseline-with-tool-rules`：内核 0、编译器 0。

| 部分 | 文件 | 加的行（git，含空行） | 非空行 | 说明 |
|---|---|---|---|---|
| `seat_tool_allowlist` | 10 | 363 | 319 | **新写**（razu），另有用例 12 个文件 |
| `tool_call_limit` | 4 | 35 | 31 | **新写**（razu），另有用例 2 个文件 |
| `token_budget` | 4 | 42 | — | **新写**（razu），只为测试工作流，交易团队的工作流不用；另有用例 4 个文件 |
| 测试工作流 `PPOtestToolGate` | 4 | 37 | — | razu 的，包自带用例要用 |
| 交易团队工作流 `PPOtestTradingAgents.toml` | 1 | +38 | — | 本仓的改动：其中注释 19 行、空行 2 行，表头和参数 17 行 |
| 交易团队 `policy_pack.toml` | 1 | +1 −1 | — | `requires` 加两个包 |
| 运行器 `_pairing/run_table.py` | 1 | +24 | — | 共用工具，不在树里 |

和原来的搭建成本（第 2 节）合起来看：原来新写的包只有 `fixed_order`，复用 `seat_write_limit`、`reopen_limit`；这次的 3 个包都是新写的，按 mero 的说法单列，不算复用。


## 8 堵绕法和同步共用包（2026-11-18，回答 mero #18874、#19191、#19536）

- **两种绕法，原来都成立，现在都堵了。** 用例表 `tests/cancel_rules.tsv` 共 6 行。在修补前的树上 6 行全部放行（`tests/runs/cancel-fix/cancel_rules_on_pre.results.tsv`、`redispatch_on_1879.results.tsv`），在新 `baseline` 上全部拒绝。
  - **撤单**（C1–C4）：上级把要求派的单或被等的单撤掉，就能交回或让下级提前开工。
    - 修法一：工作流里写 `[policy.waits_for] params = "ended=closed"`。这是现成参数。
    - 修法二：`fixed_order` 的 `needs` 只认已收单的单。
  - **另派新单**（C5、C6）：收单或撤单以后再派一张，就能多说一轮。修法：`reopen_limit` 换成 `_pairing/packs/` 的权威版（naga 改的），和 ChatDev 等价物逐字节相同。
- **日期比较：** 工具规则里 `<=` 原来按字符串比，空日期、`"2026"` 这类值会放行。现在条件值是日期时按日期比，取到的值也必须是合法日期（T4-5、T4-6）。razu 已并进源包。
- **提交：**
  - `baseline` = `22f73a0`（`1dc2ad3` → `1879a76` 撤单 → `22f73a0` reopen_limit）；`baseline-with-tool-rules` = `ee7450c`。
  - 旧的留在 `baseline-v1`、`baseline-v2` 和各分支的 `-v1` 标签上。
  - 八个场景分支都已变基，改动逐行不变。
- **重跑：** 18 张表，原有每一行的判决和「对上没有」都不变。28 行多了一个红码，逐条见 `tests/runs/cancel-fix/compare.py` 的输出和 `_techdoc/12-tradingagents.md` 2.d 节后面的「重跑」一段。包整理器测试 53/11/0（`baseline`）、70/11/0（工具规则线）。
- **搭建成本增量**（`tests/runs/cancel-fix/build-cost-increment.txt`）：
  - 规则包 6 个文件 +46 −33，其中 `fixed_order` +9 −6，`reopen_limit` 换版 +37 −27；
  - 工作流 +5；
  - 工具规则线另有日期 +18 −1。
- **TradingAgents 那边补测：** 28 行基线表里实跑 20 行、读代码 0 行、没有对应动作 8 行。22 行工具规则表里实跑 15 行、没有对应物 7 行。测试在 `../tests/acceptance/test_flow_baseline_rows.py`、`test_tool_rule_rows.py`，16 条全过（`../tests/runs/flow-and-tool-rows-on-baseline.txt`）。
- **没修的：** 检查不分运行，同一个项目里以前运行留下的单也算数。见 12 节 2.d 第 3 条。
