# 角色数 × 规则数：TradingAgents 和它的 Sherpa 等价物（四个角）

> 2026-11-19，zumi。回答 mero #21651、#21868（格点改成 T = 1、2、3），#22641（Sherpa 另量一套带类的）。只算 git。命令和数在 `runs/rules_count_corners.tsv`，验收输出在 `runs/rules/`。四个角是 s = 1、8。s = 2、4 的计数在 `runs/rules_count.tsv`，Sherpa 的验收已跑；TradingAgents 的测试也已跑完。

## 0 结论

- **先读这一条：三族按构造都是「按角色带参数」的规则。** 挑选条件本身就要求每族给每个角色一个值，所以两边都出现「族数 × 角色数」是挑选造成的，不是一般结论。挂在上下级关系上的规则（下一节）没进这个格子，因为 TradingAgents 那边没有按角色强制的对应物。

## 0.1 三族在 Sherpa 一侧能不能写在上下级关系上（mero #22875）

| 族 | 本质 | 能不能写在关系上 | 现在怎么写 |
|---|---|---|---|
| 写范围 | 每个位置一个值：写自己那份 `reports/<自己>.md`。值里有位置自己的名字 | 不能，它不是关系。参数里要是有「本座位」占位（例如 `reports/@seat.md`），就能一项管全部，那要改包 | `seat_write_limit`，每座位一行；类也写不出 |
| 读范围 | 一部分是关系：辩论者读同一个上级下的同伴（`risk_debate_state` 就是同伴的发言），组长读自己的下级。另一部分不是：辩论者还读分析员的报告和交易员的提案，那些位置和它没有上下级或同伴关系 | 关系那部分能写（「读同伴的、读自己下级的」），但现有的包里没有这样的规则，要新写一个包。不是关系的那部分仍然要按位置或按类列出 | `seat_tool_allowlist` 的 `Read(...)`，每座位一行；按类时恒定 |
| 动作次数上限 | 每种角色一个值（分析员 26，其他 6）。这是角色的属性，不是关系 | 不能。和关系沾边的写法只有「上级派单时给这张单定上限」：`token_budget` 有按单的 `--token-budget`，`tool_call_limit` 没有 | `tool_call_limit`，每座位一行；按类时恒定 |

**已经挂在关系上、不随角色数涨的 Sherpa 规则**都不在这个格子里，因为 TradingAgents 那边对应的约束是图的结构，不是按角色带参数的规则：
- 只有上级能派单：`classic_lifecycle.not_your_lower`。
- 只有单的上级能收单：内核的 `builtin.actor`。
- 消息只能发给上级、下级或同伴：`task_messages` 包，在 `_pairing/packs/`，这棵树没启用。
- 乙里加组长以后这两条（派单、收单）自动管到新的一层，不用改规则一行。乙要改的是每个辩论者的 `upper`，这是组织定义。

- **能凑出的规则族只有 3 族。** 每族都要两边都能按角色强制，而且起点上没管到全部角色。所以 R 最大是 3，R=4 和 R=8 做不了。这本身是一个结果：面向流程的系统里，能按角色挂硬规则的地方少。
  - 写范围：每个角色只能写自己那份。
  - 读范围：每个角色只能读列出的那些。
  - 动作次数上限。
- **甲，按位置写（原来的 Sherpa）：两边都是「族数 × 角色数」。** 每多一族，每多 21 个角色，两边都多大约 21 行。
  - TradingAgents：每族一张表，一个角色一行。加上每个节点注册时包一层 `govern(...)`，这一项 N 行，和族数无关。
  - Sherpa：每族一个参数块，一个座位一行。
  - 改动的位置（@@）两边都不随规模变：TradingAgents 3 到 6 处，Sherpa 1 到 3 处。
- **甲，按类写（Sherpa -c）：读和次数两族变成恒定，写这一族照旧涨。** 写这一族照旧是每个座位一行，因为每个座位的路径不一样（各写 `reports/<自己>.md`），类写不出来。
  - s=8、T=3 时：按位置 +105，按类 +63，TradingAgents +202。
- **乙，复合变更（T=2）。**
  - 行数：两边都随规模涨。
    - s=1 → s=8：TradingAgents 从 +113 −55 涨到 +159 −101，Sherpa 按位置从 +60 −26 涨到 +101 −67，Sherpa 按类从 +60 −26 涨到 +80 −46。
    - 按类时，规则块的改动恒定（+17 −14），涨的只剩组织部分：每个辩论者的 `upper` 要改成自己的组长。
  - 改动的位置：**对 Sherpa 不利。**
    - TradingAgents 恒定 27 处。
    - Sherpa 从 18 处涨到 39 处，两套一样。原因是每个辩论者的 `[[instance]] upper` 都是单独的一处改动。
- **被排除的工具范围一族：对 Sherpa 不利。**
  - TradingAgents 是 0：非分析员本来就没有工具，结构上已经管住。
  - Sherpa 要每个座位装一行：s=1 +17，s=8 +38；按类 s=8 是 +17。
- **类本身的代价。** 编译器是一次性的：+42 −6，加 49 行测试，记在框架本体一栏。每棵树还要在每个辩论者座位下加一行 `class`，这算组织定义：s=1 +6 −3，s=8 +27 −24。

## 1 三族规则在哪（文件:行）

**TradingAgents。** 摘自 `size-8/rules-write-read-runs` = `6f9a470`；`size-1` 的对应分支是 `a40728c`，行号相同的地方一样。
- 写范围
  - 表：`tradingagents/graph/role_rules.py:5` `WRITABLE`，每个角色一行。
  - 检查：`:65` `changed_keys`；违规时 `govern` 抛 `WriteOutsideRoleError`。
- 读范围
  - 表：`:21` `READABLE`。
  - 只把列出的键交给节点：`:76` `RoleView`；要别的键时，`:84` 抛 `ReadOutsideRoleError`。
- 动作次数上限
  - 表：`:37` `RUNS_LIMIT`。
  - 计数：`agents/state.py:79` 的 `role_runs`，合并函数在 `:45`。
  - 检查：`role_rules.py:92-94`。
- 每个角色的节点都包一层：`setup.py:28` 导入，`:146` 起每个 `add_node` 包 `govern(...)`。

**Sherpa。** 摘自 `size-1/rules-write-read-runs` = `84f55bb`；包的代码没动。
- 写范围：`PPOtestTradingAgents.toml:147` `[policy.seat_write_limit]`；包里在 `seat_write_limit.py:23` 拒绝。
- 读范围：`:180` `[policy.seat_tool_allowlist]`，`Read(...)` 列出能读的报告；在 `seat_tool_allowlist.py:140` 拒绝（`input_not_allowed`）。
- 动作次数上限：`:196` `[policy.tool_call_limit]`；在 `tool_call_limit.py:16` 拒绝。
- 启用：`policy_pack.toml:4` 的 `requires`。

**带类的一套。** `size-8/rules-write-read-runs-c` = `179440a`。
- 每个辩论者座位下加 `class = "aggressive"`、`"conservative"`、`"neutral"`，从 `:241` 开始。
- 读、次数、`reopen_limit` 三块里，三个类各写一项（例如 `:430-432`）。

**两边的行从哪来。** 两边的行都从 TradingAgents 离线端到端跑一遍时，每个节点实际读写的键得来（探针 `runs/rules_probe`），Sherpa 的行再由 TradingAgents 的表生成（`gen_rules_eq.py`）。动作次数一族照第 12 节 R8 做近似：TradingAgents 每个角色运行 1 次；Sherpa 分析员 26 次工具调用，其他座位 6 次。

## 2 数（git diff -U0：文件 / @@ / + / −；四栏各写 +/− 和 @@）

| 差 | 边 | s | 角色 | T | 文件 | @@ | + | − | 规则源码 | 组织定义 | 框架本体 | 声明或配置 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 甲 | TA | 1 | 12 | 1 | 2 | 3 | 59 | 11 | +59 −11 @@3 | 0 | 0 | 0 |
| 甲 | TA | 1 | 12 | 2 | 2 | 3 | 90 | 11 | +90 −11 @@3 | 0 | 0 | 0 |
| 甲 | TA | 1 | 12 | 3 | 3 | 5 | 119 | 11 | +119 −11 @@5 | 0 | 0 | 0 |
| 甲 | TA | 8 | 33 | 1 | 2 | 4 | 100 | 31 | +100 −31 @@4 | 0 | 0 | 0 |
| 甲 | TA | 8 | 33 | 2 | 2 | 4 | 152 | 31 | +152 −31 @@4 | 0 | 0 | 0 |
| 甲 | TA | 8 | 33 | 3 | 3 | 6 | 202 | 31 | +202 −31 @@6 | 0 | 0 | 0 |
| 甲 | Sherpa 按位置 | 1 | 12 | 1 | 1 | 1 | 9 | 1 | 0 | 0 | 0 | +9 −1 @@1 |
| 甲 | Sherpa 按位置 | 1 | 12 | 2 | 2 | 3 | 26 | 2 | 0 | 0 | 0 | +26 −2 @@3 |
| 甲 | Sherpa 按位置 | 1 | 12 | 3 | 2 | 3 | 42 | 2 | 0 | 0 | 0 | +42 −2 @@3 |
| 甲 | Sherpa 按位置 | 8 | 33 | 1 | 1 | 1 | 30 | 1 | 0 | 0 | 0 | +30 −1 @@1 |
| 甲 | Sherpa 按位置 | 8 | 33 | 2 | 2 | 3 | 68 | 2 | 0 | 0 | 0 | +68 −2 @@3 |
| 甲 | Sherpa 按位置 | 8 | 33 | 3 | 2 | 3 | 105 | 2 | 0 | 0 | 0 | +105 −2 @@3 |
| 甲 | Sherpa 按类 | 1 | 12 | 1/2/3 | 同按位置 | | | | | | | |
| 甲 | Sherpa 按类 | 8 | 33 | 1 | 1 | 1 | 30 | 1 | 0 | 0 | 0 | +30 −1 @@1 |
| 甲 | Sherpa 按类 | 8 | 33 | 2 | 2 | 3 | 47 | 2 | 0 | 0 | 0 | +47 −2 @@3 |
| 甲 | Sherpa 按类 | 8 | 33 | 3 | 2 | 3 | 63 | 2 | 0 | 0 | 0 | +63 −2 @@3 |
| 乙 | TA | 1 | 14 | 2 | 7 | 27 | 113 | 55 | +31 −29 @@8 | +82 −26 @@19 | 0 | 0 |
| 乙 | TA | 8 | 35 | 2 | 7 | 27 | 159 | 101 | +52 −50 @@8 | +107 −51 @@19 | 0 | 0 |
| 乙 | Sherpa 按位置 | 1 | 14 | 2 | 6 | 18 | 60 | 26 | 0 | +42 −12 @@14 | 0 | +18 −14 @@4 |
| 乙 | Sherpa 按位置 | 8 | 35 | 2 | 6 | 39 | 101 | 67 | 0 | +62 −32 @@35 | 0 | +39 −35 @@4 |
| 乙 | Sherpa 按类 | 1 | 14 | 2 | 6 | 18 | 60 | 26 | 0 | +43 −12 @@14 | 0 | +17 −14 @@4 |
| 乙 | Sherpa 按类 | 8 | 35 | 2 | 6 | 39 | 80 | 46 | 0 | +63 −32 @@35 | 0 | +17 −14 @@4 |
| 排除（工具范围） | TA | 1、8 | | 1 | 0 | 0 | 0 | 0 | 起点已由结构管住 | | | |
| 排除（工具范围） | Sherpa 按位置 | 1 / 8 | | 1 | 2 / 2 | 2 / 2 | 17 / 38 | 1 / 1 | 0 | 0 | 0 | 全在这栏 |
| 排除（工具范围） | Sherpa 按类 | 1 / 8 | | 1 | 2 / 2 | 2 / 2 | 17 / 17 | 1 / 1 | 0 | 0 | 0 | 全在这栏 |
| 规模线 b | TA | 1 / 8 | | | 1 / 1 | 2 / 2 | 27 / 69 | 3 / 24 | 计在组织定义 | | | |
| 规模线 b | Sherpa 按位置 | 1 / 8 | | | 1 / 1 | 1 / 1 | 4 / 25 | 1 / 1 | | | | 全在这栏 |
| 规模线 b-c | Sherpa 按类 | 1 / 8 | | | 1 / 1 | 1 / 1 | 4 / 25 | 1 / 1 | | | | 和 b 一样：每个座位的路径不同，类写不出 |
| 类的起点 | Sherpa | 1 / 8 | | | 3 / 3 | 14 / 35 | 91 / 112 | 9 / 30 | | +6 −3 / +27 −24 | +85 −6 | |

**口径。**
- 甲的起点：TradingAgents 是标签 `size-k`。Sherpa 是标签 `rules-size-k`，即 `size-k` 加上从 `baseline-with-tool-rules` 拷来的 `seat_tool_allowlist`、`tool_call_limit` 两个包，不启用。按类那一套的起点是 `rules-size-k-c`，即再加上类的编译器（研究副本 `40d744d`）和 `class` 行。
- 乙的起点是同一边、同一套的 `size-k/rules-write-read`。乙在甲的终点上做三件事：
  - 把风险组按发言顺序分成两组，前一组多一个；
  - 每组加一个组长，照 C2 做（每组一个子图，只交回组长的汇总），两组都在交易员之后并行，投资组合经理等两个组长；
  - 把读范围换成动作次数上限。
- 角色数是 12 + 3(k−1)，乙另加两个组长。Memory Log 两边都不受这三族管。
  - **为什么不含 Memory Log（mero #24102）：** 角色数 N 只数调模型的智能体，即 TA `setup.py` 里套 `govern` 的那些节点（4 个分析员的子图、多空研究员、研究经理、交易员、3k 个风险辩论者、投资组合经理），不数 Memory Log。
    - Memory Log 是结算往期决定的一步代码，不调模型。三族在两边都没有它的行：TA 的 `wrap_nodes` 特意跳过它，Sherpa 的规则块里也没有 `memory_log`。
    - 所以 `setup.py` 的 `add_node` 和 Sherpa 的 `[[instance]]` 都比 N 多 1，是 13 / 16 / 22 / 34。
- 四栏怎么分写在 `count_rules.py` 的说明里。TradingAgents 的规则表在一个 Python 模块里，所以计在规则源码。Sherpa 的规则行在声明文件的规则块里，所以计在声明或配置。乙里 TradingAgents 挪进子图的 `govern(...)` 注册行算组织定义。
- 分支名：`size-k/rules-write`、`rules-write-read`、`rules-write-read-runs`、`split-teams-swap-read-runs`；Sherpa 另有 `rules-tools`，和带类的同名分支加 `-c`。逐条命令在 tsv 的最后一列，都写成提交号。

## 2.1 规模线 a、c、d 带类（mero #23114）

起点是 `size-k-c`：`size-k` 加类的编译器（`40d744d`）和 `class` 行，和 b-c 同一个起点。不用 `rules-size-k-c`，因为规模线按位置那套的起点是 `size-k`，不带那两个规则包。分支 `size-k/a-c`、`c-c`、`d-c` 由 `build_scale_c.sh` 生成（`gen_rules_eq.py <tree> <k> a|c|d -c`，内部调 `gen_eq.render(..., classes=True)`；`--check` 核过带类的起点和 b 与 `gen_rules_eq` 逐字节相同，按位置那套的分支照旧逐字节复现）。全部改动都在组织定义一栏（工作流文件的 `[[instance]]`、`[seat.*]`、`fixed_order`、`reopen_limit` 和卡片），另三栏为 0。

| 变更 | s | 按位置：文件 / @@ / + / − | 按类：文件 / @@ / + / − |
|---|---|---|---|
| a 加一个角色 | 1 | 3 / 7 / 19 / 3 | 3 / 7 / 19 / 3 |
| a | 2 | 3 / 7 / 19 / 3 | 3 / 7 / 19 / 3 |
| a | 4 | 3 / 7 / 19 / 3 | 3 / 7 / 19 / 3 |
| a | 8 | 3 / 7 / 19 / 3 | 3 / 7 / 19 / 3 |
| b 每座位一条写范围 | 1 / 2 / 4 / 8 | 1 / 1 / 4·7·13·25 / 1 | 同按位置 |
| c 加一层 | 1 | 3 / 9 / 21 / 6 | 3 / 9 / 21 / 6 |
| c | 2 | 3 / 12 / 24 / 9 | 3 / 12 / 24 / 9 |
| c | 4 | 3 / 18 / 30 / 15 | 3 / 18 / 30 / 15 |
| c | 8 | 3 / 30 / 42 / 27 | 3 / 30 / 42 / 27 |
| d 复制一组 | 1 | 5 / 9 / 51 / 3 | 5 / 8 / 50 / 2 |
| d | 2 | 8 / 12 / 99 / 3 | 8 / 11 / 98 / 2 |
| d | 4 | 14 / 18 / 195 / 3 | 14 / 17 / 194 / 2 |
| d | 8 | 26 / 30 / 387 / 3 | 26 / 29 / 386 / 2 |

论文里引的三个数带类以后：
- 加一个角色：恒定 7 处（+19 −3），不变。
- 复制一组：按位置 3 + 48k 行（+51 到 +387），带类 2 + 48k 行（+50 到 +386）。只少 1 行，−3 变 −2。
- 加一层：+21 −6 到 +42 −27，不变。

为什么几乎不变：
- 编译器只在两处认类：`only` / `except`，和 params 里以类为键的项（`lifecycle_compile.py` 的 `class_params`）。`[[instance]]` 的 `upper` / `lower`、`fixed_order` 的 `after.<座位>` / `needs.<座位>` 键、值里的座位名单都不认类。
- 规模线上随 k 增长的行恰好在这些地方：c 的 −6 到 −27 是 3k 个 `[[instance]]` 的 `upper` 从投资组合经理改成风险组长；d 的 48k 是 3k 个 `[[instance]]`、`[seat.*]`、`after.*` 和卡片。
- 带类以后能省的只有 `reopen_limit`，它在起点上已经按类收成三行。
  - d 的复制座位归原来的类，所以 `reopen_limit` 不用再加 3k 行。
  - 但每个复制座位要多写一行 `class = ...`，正好抵掉。
  - 净差只剩 `reopen_limit` 块末行不再改动的那 1 行。

两个归类的选择，照原系统写：
- **新角色（合规分析师）不归类，也不另立一类。**
  - 在 TradingAgents 的场景 1 里，它是一个新节点，有自己的提示词（不是三种立场之一）。
  - 全系统只有它一个座位。一个座位的类收不了任何行，反而多一行 `class = ...`。
  - 若另立一类 `compliance`，计数是 a 加 1 行。
- **复制出来的辩论者归原来的类。**
  - 在 TradingAgents 里，复制组用的是同一个立场的提示词（`gen_eq.STANCE_TEXT[stance]`），是同一种辩论者。
  - `seat_class` 对 `<座位>_g2` 返回原立场。
  - 若给复制组另立三类，`reopen_limit` 要多三项，`class` 行照样 3k 行，计数只会更大。
- **c 的风险组长也不归类**，理由同上：全系统一个座位。乙里两个组长是一类 `risk_lead`。

验收（mero #23311，一次一个进程，`ONLY=scalec sh run_rules.sh`，日志 `runs/rules/scalec.log`，表在 `runs/rules/eq/size-k__<变更>-c[__on_start]/`）：用按位置那套的同一张表（`gen_cases_eq.py`）。

| 变更 | 行数 | 分支上对上（s = 1、2、4、8） | 起点 `size-k-c` 上反跑失败 | 起点上怎么失败 |
|---|---|---|---|---|
| a-c | 2 | 2 / 2，每档 | 2 / 2，每档 | 放行的那条设置时被 `classic_lifecycle.not_your_lower` 拒（起点没有合规分析师）；拒的那条被放行 |
| b-c | 2 | 2 / 2，每档 | 1 / 2，每档 | 拒的那条被放行（起点不限风险座位的写范围）；放行的那条起点本来就放行 |
| c-c | 3 | 3 / 3，每档 | 3 / 3，每档 | 三条都在设置时被拒：起点没有风险组长 |
| d-c | 2 | 2 / 2，每档 | 2 / 2，每档 | 放行的那条设置时被拒（起点没有复制组）；拒的那条被放行 |

和按位置那套（`runs/eq/size-k_<变更>`、`size-k__<变更>_on_tag`）逐档逐条一样。

## 2.2 同一角色的位置共用一张角色卡（mero #23470）

在带类那一套上再出一套，后缀 `-c-rolecard`（`build_role_cards.sh`，`gen_rules_eq.py ... -c --role-cards`）：
- **起点：**
  - `size-k-c-rolecard` 是 `size-k-c` 合卡后的样子，作 a、c、d 的起点。
  - `size-k/rules-write-read-c-rolecard` 是 `size-k/rules-write-read-c` 合卡后的样子，作乙的起点。
- **分支：** `size-k/{a,c,d}-c-rolecard`、`size-k/split-teams-swap-read-runs-c-rolecard`。

写法：
- 同一类的位置都写 `card = "cards/<类>.md"`，例如 `cards/aggressive.md`。原来的每位置卡删掉。
- 角色卡里只写这个角色是什么，用 TradingAgents 自己的话。
  - 不写位置名、执照号、上级。
  - 也不写「在谁之后发言 / 派给谁」那一行：这些在任务单里，`fixed_order` 管。
- 新的一种角色写一张角色卡：a 的合规分析师写 `cards/compliance_analyst.md`，c 的风险组长写 `cards/risk_lead.md`。乙的两个组长是一类 `risk_lead`，共用同一张 `cards/risk_lead.md`。
- 复制出来的位置不写卡：d 的复制组归原类，读原类的卡。

| 变更 | s | 带类：文件 / @@ / + / − | 带类 + 角色卡：文件 / @@ / + / − |
|---|---|---|---|
| 乙 复合变更 | 1 | 6 / 18 / +60 / −26 | 4 / 15 / +53 / −24 |
| 乙 | 2 | 6 / 21 / +62 / −28 | 4 / 19 / +56 / −27 |
| 乙 | 4 | 6 / 27 / +68 / −34 | 4 / 25 / +62 / −33 |
| 乙 | 8 | 6 / 39 / +80 / −46 | 4 / 37 / +74 / −45 |
| a 加一个角色 | 1 / 2 / 4 / 8 | 3 / 7 / +19 / −3 | 3 / 7 / +17 / −3 |
| c 加一层 | 1 | 3 / 9 / +21 / −6 | 3 / 9 / +21 / −6 |
| c | 8 | 3 / 30 / +42 / −27 | 3 / 30 / +42 / −27 |
| d 复制一组 | 1 | 5 / 8 / +50 / −2 | 2 / 5 / +35 / −2 |
| d | 2 | 8 / 11 / +98 / −2 | 2 / 5 / +68 / −2 |
| d | 4 | 14 / 17 / +194 / −2 | 2 / 5 / +134 / −2 |
| d | 8 | 26 / 29 / +386 / −2 | 2 / 5 / +266 / −2 |
| 合卡本身（一次性，每棵树） | 1 / 2 / 4 / 8 | — | 5 / 9 / +8 / −14；8 / 15 / +11 / −32；14 / 27 / +17 / −68；26 / 51 / +29 / −140 |

c 在 s = 2、4 也和带类一样（+24 −9，+30 −15）。全部改动仍只在组织定义一栏。

**不变的格点：**
- 甲 T = 1、2、3、工具范围、b 不变。
- 核过的办法：它们在带类那一套上的差里没有一行碰到 `cards/` 或 `card =`，所以合卡不改它们。

**数怎么变的：**
- **d：** 2 + 48k 变成 2 + 33k 行，文件从 3k + 2 个变成恒定 2 个，@@ 从 3k + 5 变成恒定 5。
  - 每个复制位置还剩 11 行：`[[instance]]` 6 行、`[seat.*]` 3 行、`after.*` 1 行、`needs` 名单 1 行。
- **乙：**
  - 第二组第一个位置不用再改卡（它读原类的卡）。
  - 两个组长共用一张 5 行的卡。原来是两张各 5 行。
- **a：** 合规分析师的卡少了位置那两行：标题里的位置名和执照号，以及「在谁之后发言」。
- **c：** 不变。组长卡原来就是 5 行，3k 个 `upper` 行照旧。

**合了哪些（mero #23533 定：合）：** 依据是那些不同的文字由同一个模板按位置填出来，属于位置信息。仓主的原设计（0.2）是角色级的卡同角色共用，位置和任务的信息进任务单。

| 合成的类和卡 | TradingAgents 里这些实例的提示词差在哪 | Sherpa 一侧这信息由谁、在什么时候给 |
|---|---|---|
| `aggressive`、`conservative`、`neutral` → `cards/<立场>.md`。每类是该立场全部 k 个位置，加上 d 的复制组 | 第 j 个辩论者是拷原立场的文件改名而成（`gen_ta.rename`），立场那段一字不差。差在三处，都按位置填：<br>(1) 提示词里点名要回应的同伴：「Here is the last response from the *X* analyst: {current_*x*_response}」，每个同伴一段，由 `gen_ta.add_peers` 填；<br>(2) 自己发言的标签 `latest_speaker` 和 `argument = f"<节点名>: ..."`；<br>(3) 状态键名（`<key>_history`、`current_<key>_response`） | **在谁之后、回应谁：**<br>• 上级在派单时（`dispatch`）写进任务单的 `--waits-for`；<br>• `fixed_order_declared_waits` 在派单时核它和 `after.<位置>` 一致；<br>• `waited_tasks_ended` 在领单时（`takeoff`）放行。<br>agent 领单时从任务单看到等的是哪几张单，前面的人交回的报告在 `reports/<位置>.md`。<br>**自己是谁：** 由执照号（领单的那个位置）给，不在卡里。<br>(3) 是 TradingAgents 的状态管道，Sherpa 没有对应物 |
| `risk_lead`（乙的两个组长）→ `cards/risk_lead.md`；c 的单个组长读同一张 | 两个组长出自同一个工厂 `create_risk_lead(llm, team, summary_key)`。差在两处：<br>(1) 提示词里的组员名单 `you run {team}`；<br>(2) 交回的状态键 `risk_summary_1` / `risk_summary_2` | **组员是谁：**<br>• 由 `[[instance]]` 的 `upper = "risk_lead_i"` 给。只有这几个位置派得出去：派单时 `classic_lifecycle.not_your_lower` 核；<br>• `needs.risk_lead_i` 在交回时（`debrief`）由 `fixed_order_required_lowers` 核，要求每个组员的单都已收回。<br>agent 派单前从工作流看到自己的下级，交回前缺谁会被拒并点名。<br>**交到哪：** 组长的报告文件 `reports/risk_lead_i.md` 由写范围（`seat_write_limit`）按位置给 |

- **没合：** 其余每个位置都是独一种角色，各自一张卡，照旧。
- **没动（mero #23533）：** 投资组合经理那张卡里「派给谁」那一行仍点名下级。若这行也挪进任务单：
  - a、c、d 各少一个文件（+1 −1，@@ 1）；
  - 乙少一个文件（+2 −2）。

**验收**（mero #23688）：
- **怎么跑的：** 一次一个进程，`ONLY=rolecard sh run_rules.sh`。日志 `runs/rules/rolecard.log`，表在 `runs/rules/eq/size-k__<变更>-c-rolecard[__on_start]/`。
- **用的表：**
  - a、c、d 用规模线的表（`gen_cases_eq.py`）；
  - 复合变更用格点的表（`gen_cases_rules_eq.py`，write、runs 两族，加组织的两条）。
- **甲和 b：** 没变，没重跑。

| 变更 | 分支上对上（s = 1、2、4、8 每档） | 起点上反跑失败（每档） |
|---|---|---|
| a-c-rolecard | 2 / 2 | 2 / 2 |
| c-c-rolecard | 3 / 3 | 3 / 3 |
| d-c-rolecard | 2 / 2 | 2 / 2 |
| 复合变更 -c-rolecard | 6 / 6 | 6 / 6：起点上没有组长，设置时就被 `classic_lifecycle.not_your_lower` 拒 |

和带类那一套逐档逐条一样。合卡没有让哪一条放行或拒绝变样。

## 2.3 规则和角色的耦合：两个探针（mero #23586，静态）

分支由 `build_probes.sh` 生成，数由 `count_rules.py --probes` 得出，tsv 是 `runs/probes_count.tsv`，s = 1 和 8。Sherpa 用共用角色卡那套。四栏照前面的分法；mero 要的「其余」等于框架本体加声明或配置。

**探针一：L、R、L+R。**

起点：TradingAgents 是 `size-k`，Sherpa 是 `size-k-c-rolecard`。

| 行 | TradingAgents 分支 | Sherpa 分支 |
|---|---|---|
| L 只加一层 | `size-k/c2`：组长加在风险组上，层由子图强制。不用 C，因为 C 不强制，Sherpa 的层是强制的 | `size-k/c-c-rolecard` |
| R 只加一条按角色带值的规则 | `size-k/rules-write`：写范围族，每个角色一行 | `size-k/rules-write-c-rolecard`：同一族，`seat_write_limit` 每个位置一行 |
| L+R | `size-k/c2-rules-write`：在 C2 上装写范围，组长也有一行，风险组子图里的节点也套 `govern` | `size-k/c-rules-write-c-rolecard`：c 加写范围，组长也有一行。`--check` 核过它的规则行和 R 的同一套写法 |

| 边 | s | L | R | L+R | L+R − (L + R) |
|---|---|---|---|---|---|
| TA | 1 | 6 / 16 / +52 −17，全在组织定义 | 2 / 3 / +59 −11，全在规则源码 | 7 / 18 / +109 −25：规则源码 +57 −8 @@3，组织定义 +52 −17 @@16 | 文件 −1，@@ −1，+ −2，− −3 |
| TA | 8 | 6 / 16 / +73 −38 | 2 / 4 / +100 −31 | 7 / 18 / +151 −46：规则源码 +78 −8 @@3，组织定义 +73 −38 @@16 | 文件 −1，@@ −2，+ −22，− −23 |
| Sherpa | 1 | 3 / 9 / +21 −6，全在组织定义 | 1 / 1 / +9 −1，全在声明或配置 | 3 / 10 / +31 −7：组织定义 +21 −6 @@9，声明或配置 +10 −1 @@1 | 文件 0，@@ 0，+ +1（声明或配置），− 0 |
| Sherpa | 8 | 3 / 30 / +42 −27 | 1 / 1 / +30 −1 | 3 / 31 / +73 −28：组织定义 +42 −27 @@30，声明或配置 +31 −1 @@1 | 文件 0，@@ 0，+ +1（声明或配置），− 0 |

**Sherpa：** L+R 恰好是 L 加 R 再加 1 行，`risk_lead=reports/risk_lead.md`，在 R 已有的那个规则块里。组织定义一栏和 L 一字不差，两个规模都一样。

**TradingAgents：** L+R 的行数反而比 L 加 R 少，但耦合在内容上。
- **少在哪：**
  - R 要给每个辩论者的 `workflow.add_node` 套 `govern`。s = 1 是 3 行，s = 8 是 24 行。
  - L（C2）已把这些行删掉，改成风险组子图里一行循环 `graph.add_node(name, node)`。
- **多在哪：**
  - L+R 要改 L 新写的两行：子图里的 `graph.add_node(name, govern(name, node))` 和 `graph.add_node("Risk Lead", govern("Risk Lead", risk_lead))`。这两行按行算在组织定义里，行数和 L 一样，但内容是规则改的。
  - 规则表多一行 `"Risk Lead": {"risk_summary"}`。
- **分开看（`R on L` 指在 L 上再装 R，`L on R` 指在 R 上再加 L）：**
  - TA 的 R on L 是 2 / 7 / +58 −9（s = 1）、+79 −9（s = 8），全在规则源码，里面包括那两行。
  - TA 的 L on R 是 7 / 17 / +53 −17：规则源码多 +1（组长那一行），其余同 L。
  - Sherpa 的 R on L 是 +10 −1（s = 1）、+31 −1（s = 8）。L on R 是 L 加 1 行声明或配置。

**探针二：换上级。**

起点是乙那棵树（两个组长），做法是把第一组的最后一个辩论者挪到第二组，排在第二组最后发言：
- s = 1：`conservative_analyst`（TA 里是 `Conservative Analyst`） 从组长 1 挪到组长 2 名下；
- s = 8：`neutral_analyst_4`（TA 里是 `Neutral Analyst 4`） 挪过去。

规则（写范围、次数上限）都不改。

| 边 | s | 文件 / @@ / + / − | 规则源码 | 组织定义 | 其余 | 改了什么 |
|---|---|---|---|---|---|---|
| TA | 1 | 2 / 9 / +10 −10 | 0 | +10 −10 @@9 | 0 | 见下 |
| TA | 8 | 2 / 9 / +10 −10 | 0 | +10 −10 @@9 | 0 | 同上 |
| Sherpa | 1 | 1 / 4 / +5 −5 | 0 | +5 −5 @@4 | 0 | 见下 |
| Sherpa | 8 | 1 / 5 / +5 −5 | 0 | +5 −5 @@5 | 0 | 同上 |

**TA 改了什么**（`conditional_logic.py`、`setup.py`）：
- 两组路由的轮数门槛和接力；
- 两个组的路径表和子图节点表；
- 两个组长提示词里的组员名单。

**Sherpa 改了什么**：都在工作流文件里。
- 该位置 `[[instance]]` 的 `upper`；
- 它的 `after.*`；
- `needs.risk_lead_1` 和 `needs.risk_lead_2` 两个名单。

**两边谁带谁都强制，都不用改规则：**
- **TradingAgents：**
  - **怎么强制：** 靠图的结构。辩论者是哪个组子图里的节点，就只在那个组里发言。原组长的子图里已经没有它，到不了它。
  - **规则为什么不用改：** 规则表按节点名一行（`WRITABLE`、`RUNS_LIMIT`），`role_rules.py` 一字不改，挪过去照旧生效。
  - **有一点不同：** TA 的组长不「派单」，谁发言由组内路由定，所以「新上级能派、旧上级不能派」在 TA 里是「只在新组里发言」。
- **Sherpa：**
  - **怎么强制：**
    - `upper` 改了以后，只有新组长派得出去，原组长派单会被 `classic_lifecycle.not_your_lower` 拒；
    - `needs.risk_lead_2` 在新组长交回时要它的单。
  - **规则为什么不用改：** `seat_write_limit` 和 `tool_call_limit` 按位置或类写，不改。

## 2.4 组合演示：放大、嵌套（mero #23876，静态）

分支由 `build_demos.sh` 生成，数由 `count_rules.py --demos` 得出，tsv 是 `runs/demos_count.tsv`。三栏：规则源码 / 组织定义 / 其余（框架本体加工作流文件里的规则块）。Sherpa 用共用角色卡那套。

两个演示的起点都是三族（写、读、次数）全装的那棵 s = 1 的树：
- TradingAgents：`size-1/rules-write-read-runs`；
- Sherpa：`size-1/rules-write-read-runs-c-rolecard`，这次新建，是 `size-1/rules-write-read-runs-c` 换成共用角色卡。

计数时顺手修了 `count_rules.py` 的一处分法：带 `govern` 的块里只是重新缩进的行，原来会被算进规则源码，现在算组织定义。前面各节的数重算过，一个没变（只有演示二碰到这种行）。

**演示一：放大，规则不变。**

- **分支：**
  - TradingAgents：`size-k/rules-write-read-runs-frozen-at-size-1`，从 `size-k` 起（s = 16 的标签 `size-16` 这次新建，做法同 `build_ta.sh`）。规则表和 `govern` 只覆盖 s = 1 的 12 个角色，和起点一字不差；复制出来的辩论者照上游写法加进去，不套 `govern`。
  - Sherpa：`size-k/rules-write-read-runs-c-rolecard-frozen-at-size-1`，在起点上重写组织部分。三个规则块（`seat_write_limit`、`seat_tool_allowlist`、`tool_call_limit`）照抄 s = 1 的，`policy_pack.toml` 不动。
- **核过：** 两边规则源码和规则块都是 0 行改动，见下表。

| 边 | k | 文件 / @@ / + / − | 规则源码 | 组织定义 | 其余 |
|---|---|---|---|---|---|
| TA | 2 | 16 / 38 / +394 −8 | 0 | +394 −8 @@38 | 0 |
| TA | 4 | 22 / 44 / +1436 −8 | 0 | +1436 −8 @@44 | 0 |
| TA | 8 | 34 / 56 / +4600 −8 | 0 | +4600 −8 @@56 | 0 |
| TA | 16 | 58 / 80 / +15248 −8 | 0 | +15248 −8 @@80 | 0 |
| Sherpa | 2 | 2 / 5 / +35 −2 | 0 | +35 −2 @@5 | 0 |
| Sherpa | 4 | 2 / 5 / +101 −2 | 0 | +101 −2 @@5 | 0 |
| Sherpa | 8 | 2 / 5 / +233 −2 | 0 | +233 −2 @@5 | 0 |
| Sherpa | 16 | 2 / 5 / +497 −2 | 0 | +497 −2 @@5 | 0 |

**路由代码单独列（mero #24102）。** 上表的「规则源码 0」只指三张按角色的规则表（`role_rules.py`，加上 `govern` 和 `role_runs`）。TA 的 `conditional_logic.py` 记在组织定义里，但它跟着组织改了；Sherpa 对应的是 `[policy.fixed_order]` 的参数，也记在组织定义里：

| k | TA `conditional_logic.py`（文件 / @@ / + / −） | Sherpa `fixed_order` 参数（@@ / + / −） |
|---|---|---|
| 2 | 1 / 2 / +8 −2 | 2 / +7 −1 |
| 4 | 1 / 2 / +20 −2 | 2 / +19 −1 |
| 8 | 1 / 2 / +44 −2 | 2 / +43 −1 |
| 16 | 1 / 2 / +92 −2 | 2 / +91 −1 |

- **TA 改了什么：** 两处。
  - 风险辩论的轮数门槛：`3 * self.max_risk_discuss_rounds` 改成 `3k * …`，连同那行注释，−2 +2。
  - 轮换路由加 3(k−1) 个分支，每个两行，即 +6(k−1)：谁说完轮到谁。
  - `max_risk_discuss_rounds` 本身（`default_config.py`）不变。
- **Sherpa 改了什么：** `after.*` 加 3(k−1) 行（轮换次序），`needs.portfolio_manager` 名单加 3(k−1) 个位置（尾行改一处，−1 +1）。轮数在 Sherpa 是「每个位置派一次、`reopen_limit` 0」，按类写，不随 k 改。
- **为什么归组织定义：** 这份报告的分栏只把三族按角色的规则表算规则源码；其余写着节点名、谁接谁的代码都算组织定义。路由里的分支和门槛的倍数，就是「风险组有哪几个人、按什么顺序说」，是组织本身。Sherpa 一侧口径相同：`fixed_order` 的参数一直记在组织定义。
- **和引用矩阵怎么对上：** 引用矩阵（`_companion/results/coupling/measure-1-reference-matrix.md`）的 TA 规则清单把轮换次序和轮数上限算规则：R1 的位置是 `conditional_logic.py:23-33`，R7 是 `:12-21,23-33`。按矩阵的口径，演示一里 TA 改的这些行都落在 R1、R7 的位置里，规则代码并不是 0 行；这正是矩阵量的「规则代码里写着组织」。所以两种说法要一起写：**三张按角色的规则表 0 行；路由代码（R1、R7 的位置）跟着组织改了，k = 2、4、8、16 各 +8 −2、+20 −2、+44 −2、+92 −2。** 按同一口径，Sherpa 的 R1 对应物是 `fixed_order` 的 `after.*`，也随 k 涨，见上表右栏；但它是声明里的参数，包的源码 0 行。

- TA 每多一个辩论者多一个文件（它的 `*_debator.py`），所以文件数随 k 涨；行数里大头是复制的辩论者文件和每个辩论者提示词里的同伴名单（每加一个人，所有人的名单都要改）。
- Sherpa 一直是两个文件（工作流文件、投资组合经理卡）、5 处：`[[instance]]`、`[seat.*]`、`after.*`、`needs.portfolio_manager`、经理卡里点名下级那一行。行数是 33(k − 1) + 2。

**放大以后，原有规则管不管得到新加的角色**（都是读代码的结论，没有跑）：
- **TradingAgents：管不到。**
  - 新辩论者的节点没套 `govern`，三张表里也没有它们的行，所以写、读、次数三族都不管它们。
  - 只补 `govern` 也不行：`govern` 查 `RUNS_LIMIT[role]` 和 `WRITABLE[role]` 时找不到这一行，会抛 `KeyError`，节点第一轮就出错，连该放行的也放不过。要管到就得每个新角色在每张表里加一行，那就是改规则了。
- **Sherpa：管得到，但带 s = 1 的值。**
  - 三个规则块在 s = 1 时，风险位置的那一项都是按类写的（`aggressive=…`、`conservative=…`、`neutral=…`，一类只有一个位置，值自然相同）。编译器把按类写的一项展开成这一类每个位置一项（`ppo/lifecycle_compile.py` `class_params`），所以新位置三族都管得到。
  - **值对的：** `tool_call_limit` 的 6，`reopen_limit` 的 0，同类每个位置本来就一样。
  - **值不对的：** 写在值里的位置信息还是 s = 1 的。
    - `seat_write_limit`：`aggressive=reports/aggressive_analyst.md`。新的 `aggressive_analyst_2` 只能写原位置那份报告，写自己的 `reports/aggressive_analyst_2.md` 会被拒。
    - `seat_tool_allowlist`：读名单只有 s = 1 的报告。比如 `conservative_analyst_2` 读不到它前一位 `aggressive_analyst_2` 的报告；`portfolio_manager` 那一行不是按类写的，读不到任何新报告。
  - 所以「规则一行不改」时，Sherpa 新位置是被管住了，但管的是 s = 1 那几个文件；要各写各的报告，`seat_write_limit` 得每个新位置加一行（每个位置的报告路径不同，这是 2.2 节说的位置信息）。

**演示二：嵌套。**

- **谁当领导：** 基本面分析师（场景 7 的那个执行者）。场景 7 在它名下加一个报表分析师，那是另一种角色；这次照定义换成 3 个和它同一种角色的手下。TA 叫 `Fundamentals Analyst 2`、`3`、`4`，Sherpa 叫 `fundamentals_analyst_2`、`_3`、`_4`，命名照复制辩论者的写法。场景 7 的分支在原系统的基线上，没有三族规则，所以在三族那棵树上新建。
- **分支：**
  - TradingAgents：`size-1/rules-write-read-runs-nest-fundamentals-analyst`。照场景 7 的位置，3 个手下是基本面分析师子图里的节点，同时跑，各写自己的报告键，跑完基本面分析师再读三份报告。每个手下的节点套 `govern(<自己的名字>, …)`，三张表各加三行，抄基本面分析师那一行（写的键换成自己的）。
  - Sherpa：`size-1/rules-write-read-runs-c-rolecard-nest-fundamentals-analyst`。3 个 `[[instance]]` 的 `upper` 是 `fundamentals_analyst`，加 `needs.fundamentals_analyst`。基本面分析师和 3 个手下归一类 `fundamentals`：共用 `cards/fundamentals.md`（原卡换成角色卡，去掉位置名、执照号和报告路径，加一句「有自己的分析师就先同时派出去，读完他们的报告再写自己的」）；`tool_call_limit`、`reopen_limit` 按类写一项。

| 边 | 文件 / @@ / + / − | 规则源码 | 组织定义 | 其余 |
|---|---|---|---|---|
| TA | 5 / 15 / +37 −7 | +9 −0 @@3 | +28 −7 @@12 | 0 |
| Sherpa | 3 / 9 / +46 −9 | 0 | +38 −7 @@6 | +8 −2 @@3 |

- **TA 规则源码 +9：** 写、读、次数三张表各三行。
  - 手下那行 `graph.add_node(helper.agent_node, govern(helper.agent_node, …))` 是新写的一行，照前面的分法算在组织定义里（和乙里组子图那行一样）。
  - 基本面分析师自己的三行不用改：手下在它的子图里，它的子图只交回 `fundamentals_report`，读三份报告也在子图里，不经过它的规则。
- **TA 组织定义：** 分析师工厂多两个参数（报告键、要读的手下报告），`AnalystNodeSpec` 多一项 `helpers`，状态多三个键，`_analyst_graph` 先跑手下再跑自己。
- **Sherpa 其余 +8 −2**（都是规则块）：
  - `seat_write_limit` 加三行，每个手下一份报告；
  - `seat_tool_allowlist` 加三行（手下的值就是基本面分析师原来那行），基本面分析师那行改一处，加上读三份报告；
  - `tool_call_limit` 的 `fundamentals_analyst=26` 改成 `fundamentals=26`。
  - 前两块按类合不起来：写的路径每个位置不同；读名单领导和手下不同（领导要读手下的报告）。
- **Sherpa 组织定义：**
  - 3 个 `[[instance]]`，4 个 `[seat.*]`（基本面分析师的卡改指角色卡并加类）；
  - `needs.fundamentals_analyst`，`reopen_limit` 那一项改按类写；
  - 卡：删 `fundamentals_analyst.md`，加 `fundamentals.md`。

**验收要点**（写进 `runs/demos/nesting_cases.tsv`，没有跑）：

| 要点 | TradingAgents | Sherpa |
|---|---|---|
| 新领导能派给新手下 | 离线端到端跑一次：3 个手下各在基本面分析师的子图里跑一次，报告进它的提示词 | `fundamentals_analyst` 派 `fundamentals_analyst_2`：放行 |
| 别的上级不能越过它直接派 | 外层图里加一条研究经理 → `Fundamentals Analyst 2` 的边，图编译不过（节点只在子图里）。这是建图时靠结构拒，TA 运行时没有派单可拒 | `research_manager` 派 `fundamentals_analyst_2`：`classic_lifecycle.not_your_lower` 拒。另加一条：领导不派齐三个就交回，`fixed_order.missing_lower` 拒 |
| 新手下受原执行者那套规则管 | 写、读、次数各一放一拒：`govern("Fundamentals Analyst 2", …)` 写 `fundamentals_report_2` 放行、写 `fundamentals_report` 被 `WriteOutsideRoleError` 拒；读 `market_report` 被 `ReadOutsideRoleError` 拒；第二次跑被 `RunsOverRoleLimitError` 拒 | 写、读、次数各一放一拒：提交 `reports/fundamentals_analyst_2.md` 放行、提交 `reports/fundamentals_analyst.md` 被 `seat_write_limit` 拒；数据工具放行、`Read` 别人的报告被 `seat_tool_allowlist` 拒；第 26 次工具调用放行、第 27 次被 `tool_call_limit` 拒 |

TA 的写拒绝要直接调套了 `govern` 的节点：真图里手下的子图只交回 `fundamentals_report_2`（`output_schema`），越界的键在 `govern` 看到之前就被结构丢掉了。

**验收实测（mero #24211、#24261）。** 用 `ONLY=nest sh run_rules.sh` 跑，单进程，先 TA 后 Sherpa，各在分支和起点上各一遍，日志 `runs/rules/nest.log`。

| 边 | 分支上对上 | 起点上反跑对不上 | 结果文件 |
|---|---|---|---|
| TA（`acceptance/test_nesting.py`） | 8 / 9 | 9 / 9 | `runs/rules/ta/nest__size-1_rules-write-read-runs-nest-fundamentals-analyst.txt`，起点 `…nest__size-1_rules-write-read-runs.txt` |
| Sherpa（`gen_cases_rules_eq.py … nest`） | 9 / 9 | 8 / 9 | `runs/rules/eq/nest__size-1_rules-write-read-runs-c-rolecard-nest-fundamentals-analyst/cases.txt`，起点 `…nest__size-1_rules-write-read-runs-c-rolecard/cases.txt` |

- **TA 没对上的一条：** `test_read_refused_a_helper_asking_for_another_report`。手下要 `market_report` 确实拿不到，但抛的是 `KeyError`，不是用例预期的 `ReadOutsideRoleError`。原因在用例的写法：
  - 手下是一个子图。`govern` 把过滤后的 `RoleView` 交给子图，子图里的节点拿到的是 LangGraph 新建的普通字典，没交进来的键就不在，问起来是普通的 `KeyError`。
  - 再外一层，领导自己的 `RoleView` 已经把 `market_report` 滤掉了，所以真图里这一条分不出是手下那一行管的，还是领导那一行管的。四个分析员在甲里也是子图，读范围对它们一样是「不交进去」，不是「问了就拒」。
  - 要单测手下那一行，得像写和次数那样直接调套了 `govern` 的节点，问起来就会抛 `ReadOutsideRoleError`。已照这样改（mero #24290）：状态里有 `market_report`，手下那一行没有，套了 `govern` 的节点去问它，预期 `ReadOutsideRoleError`。改后没跑：嵌套验收的队列已取消（mero #24339），要跑时只跑这一条（`ONLY=nest NEST_ONLY=test_read_refused_a_helper_asking_for_another_report sh run_rules.sh`）。
- **Sherpa 起点上没反过来的一条：** `D-block`。起点上没有 `fundamentals_analyst_2`，研究经理派它照样被 `classic_lifecycle.not_your_lower` 拒，所以这一条在起点上也拒，分不出新旧。另外两条派单相关的 `D-pass`、`D-needs` 在起点上都反过来了。

## 3 验收（每格每族放一条、拒一条，再拿到起点上反跑）

**Sherpa。**
- 两套、两个规模的全部格点（甲 T=1/2/3、乙、工具范围、b-c）在分支上全对得上。
- 在起点上反跑：甲对不上的条数等于拒绝条数（1、2、3）。乙对不上 6 条：起点上没有组长，准备步骤就失败。
- 用例生成：`gen_cases_rules_eq.py`。工具范围的拒绝条是辩论者调 `get_news`，被拒为 `seat_tool_allowlist.tool_not_allowed`。

- s=2、4 也跑完了（`runs/rules/eq_sizes_2_4.log`、`eqx_sizes_2_4.log`），和上面一样：两套在分支上全对得上，起点上对不上的条数等于拒绝条数，乙是 6 条。

**TradingAgents。** 测试在 `acceptance/test_role_rules.py`。拒绝条让一个角色出格：甲里是最后一位辩论者，乙里写范围用组长 2、次数用第二组最后一位。另有每族「图里每个角色都在表里」一条。
- 分支上：甲 3/6/9 条过，乙 8 条过，两个规模都是。
- 起点上反跑（四个规模全部补齐，一次一个进程，`runs/rules/ta_queue.log`）：
  - 甲 T=1：2 条失败、1 条过；T=2：4 条失败、2 条过；T=3：7 条失败、2 条过。四个规模一样，过的是放行条，起点上本来也过。
  - 乙：7 条失败、1 条过，四个规模一样。

**上游测试。** 跑 `test_risk_router_path_map`、`test_debate_opening`、`test_graph_end_to_end` 三个文件，每个文件单独跑。
- s=1 甲三格：18、8、15 条全过，和起点一样。
- s=2、4、8 甲三格：5 条失败，和各自的 `size-k` 起点一样。这些测试写死了 3 位辩论者，所以和规则无关。
- 乙变了两处：
  - 路由测试导入失败：整组的路由换成了每组一个，`RISK_ANALYSIS_PATH_MAP` 不在了。
  - `test_an_interrupted_run_resumes_from_its_checkpoint` 失败：它数续跑时的模型调用次数，假定风险辩论是串行的。两组并行以后，续跑少做 2 次（实际 4 次，测试期望 6 次）。

## 4 不利的和拿不准的

- 乙的改动位置数，Sherpa 随规模涨，TradingAgents 恒定。类也救不了，因为上下级关系仍然只能按位置写。
- 工具范围一族：TradingAgents 是 0，Sherpa 每座位一行（按类以后恒定）。
- 写范围一族用不上类：每个座位的路径不同，参数里没有「本座位」这种占位写法。如果包支持 `reports/@seat.md` 这样的写法，写范围也能恒定，但那要改包，这次没做。
- 动作次数一族两边口径不同：TradingAgents 数节点运行次数，Sherpa 数工具调用。
- TradingAgents 的规则全部写在一个新模块和一个包装函数里，这是我选的写法；B 原来是写在 `setup.py` 里。分成每族一个包装函数的话，每族还要多改 N 行注册，TradingAgents 会更贵。
- 行数是生成器写出来的。生成器照上游和照 B 的写法写，没有为哪一边压行数。

## 5 简化实验：格点 T(k, m)（mero #24380，只建树，不跑）

分支由 `build_grid2.sh` 生成（生成器 `gen_grid2.py`），每个格点一个分支，都从本边的 T(0,0) 起，所以 `git diff T(0,0)..T(k,m)` 就是改动。k = 0、1、2、4、8，m = 0、1、2。

- **仓库和分支：**
  - TradingAgents：`_scale/tradingagents/modified`，`ta-grid2-k<k>-m<m>`，15 个。T(0,0) 就是标签 `size-1`（上游原样，没有按角色规则）。
  - Sherpa 等价物：`_scale/tradingagents/sherpa`，两种写法各 15 个：
    - `sherpa-ownclass-grid2-k<k>-m<m>`（甲）：每个新角色自成一类，用自己的取值；
    - `sherpa-sharedclass-grid2-k<k>-m<m>`（乙）：新角色归进已有的类 `neutral`。三个风险类除了报告路径，取值本来都一样，所以选哪一类不影响规则行。新角色仍用自己的卡（`cards/kind<i>.md`），因为它是新的一种角色，有自己的提示词；这一点和「同类共用一张卡」不一致，照实写在这里。
    - 两种写法的 T(0,0) 是同一个提交：`rules-size-1-c` 换成共用角色卡；k = 0 的两种写法也是同一棵树。
- **核过：** k = 0 的树和以前验收过的同族分支一致：TA `ta-grid2-k0-m1`、`-m2` 和 `size-1/rules-write`、`rules-write-read` 一字不差；Sherpa 的工作流目录和 `size-1/rules-write-c-rolecard`、`rules-write-read-c-rolecard` 一字不差（只差没启用的两个包的拷贝）。
- **新角色怎么加：** 照场景 1 A2 加合规分析员的原生做法。`kind1`..`kind8` 是风险分析员，排在最后一位后面，挂在投资组合经理名下；各有自己的名字、提示词（占位）和状态键；其他辩论者都读它。Sherpa 一侧是 `kind<i>_analyst` 位置，`upper = "portfolio_manager"`，接在 `after.*` 链尾，进 `needs.portfolio_manager`。
- **每族规则是什么：** m 取三族的前 m 族，都是我们写的、在角色规则格子里验收过的。
  1. 写：每个角色只能改自己的状态键（TA `WRITABLE` / Sherpa `seat_write_limit`，原生包，值是我们写的）。
  2. 读：每个角色只拿到自己那几个键（TA `READABLE` / Sherpa `seat_tool_allowlist` 的 `Read(...)`）。
  3. 次数：TA `RUNS_LIMIT` / Sherpa `tool_call_limit`，三族全装是 m = 3，不在格点里。
- **做不到的档：** m = 4、8。TA 没有原生的按角色规则，我们写好并验收过的只有这三族。
- **原生去不掉的规则：**
  - TA：没有按角色的规则，只有结构。每个分析员只有自己的工具（各自的 `ToolNode`），只交回自己的报告（`output_schema`），谁接谁由图的边定。
  - Sherpa 的 T(0,0)：四个分析员的 `seat_write_limit`（TA `output_schema` 的对应物），每个位置的 `reopen_limit` 0，`fixed_order` 的 `after.*` 和 `needs.*`，`classic_lifecycle` 的上下级。`reopen_limit` 和 `fixed_order` 在 m = 0 时也管到新角色：甲每个新角色加一行 `kind<i>=0`，乙由类 `neutral` 管，不加行。
- **用例（每个新角色每族一放一拒，没跑）：**
  - TA：`acceptance/test_grid2.py`，`GRID_K=<k> RULES_FAMILIES=<前 m 族>`，按新角色参数化。
  - Sherpa：`gen_cases_rules_eq.py <out> <k> <tree> <前 m 族> grid2`，每个新角色 `kind<i>-W/R/N-pass/block`。
  - m = 0 没有用例。

## 6 grid3：模拟规则（mero #24557、#24624，只建树，不跑）

统一定义见 `_scale/GRID3-模拟规则.md`。分支由 `build_grid3.sh` 生成（生成器 `gen_grid3.py`），只做原系统一侧。

- **仓库和分支：** `_scale/tradingagents/modified`，`grid3-k<k>-m<m>`，k、m 各取 0、1、2、4、8，共 25 个。`grid3-k0-m0` 就是标签 `size-1`（上游原样），其余都从它起。
- **复制的执行者：** 中立风险分析员（Neutral Analyst）。复制品 `Neutral Analyst 2` .. `k+1` 照 `gen_ta.py` 复制辩论者的办法写：上游中立文件改名，提示词同一份；各有节点名、状态键、路由分支，路由能单独把发言交给它；排在中立分析员后面，同属投资组合经理。选它是因为风险组按顺序发言，链是直的，每个复制品都是一次单独的交接。
- **交接是什么：** TA 是流程图，没有派单。一次交接就是一个节点的输出交给下一步的节点。
  - 谁交给我：上一步跑过的节点（LangGraph 的 `langgraph_step` 少 1），照 `conditional_logic.py:19,29-32` 路由读「上一个发言者」的写法。
  - 交出的文本：节点这一轮写的文字（报告；辩论状态里的 `current_*` 和 `judge_decision`），末尾加接龙行，存进新的状态键 `handoff`。合并写法照 `state.py` 的 `merge_role_runs`（`size-1/rules-write-read-runs` 的 `state.py:45,79`）。
  - 多个节点同时交给一个节点时（四个分析员交给多头研究员），名字串接最长的那条，一样长取字母序最后的。
- **规则写在哪：** 都在 `tradingagents/graph/relay_rules.py`，只写装上的那几条。`setup.py` 里 `workflow = StateGraph(AgentState)` 换成 `RelayGraph(AgentState)`（1 行，外加 1 行 import）。`RelayGraph` 在 `add_node` 时把每个节点（Memory Log 是步骤不是角色，除外）包上 `relay(...)`。
  - 包装照 `role_rules.govern` 的写法（`size-1/rules-write-read-runs` 的 `role_rules.py:87-101`，角色规则格子里验收过）：接手时先查交给它的每一份，再跑节点，再写自己的接龙行。
  - **全局一次：** 八条（实际七条）都是全局写一次，新角色不用接任何一行。
  - **按角色的数据只有一处：** R5 的口令表，一种角色一行，共 12 行，复制品和原角色共用一行。
- **逐条：**

| 号 | 怎么查 | 全局还是按角色 | 备注 |
|---|---|---|---|
| R1 密码 | `pw=123` | 全局 | |
| R2 名字接龙 | 名字串最后一个是交出者 | 全局 | |
| R3 报数 | `n` = 交出者收到的最大 `n` + 1，链头（四个分析员）是 1 | 全局 | |
| R4 点名 | 裁定者交出时 `heard=` 列全它的直接下级 | 全局 | 直接下级从图里算：同一张路由表路由的那些节点，加上表里不是它们中任何一个的那个目标。算出来是研究经理（多空研究员）、投资组合经理（全部风险辩论者，含复制品）。投资组合经理后面没有接手的节点，在交出那一步自查（定义允许） |
| R5 口令 | `key=` 是交出者那种角色的词 | 全局，口令表每种角色一行 | |
| R6 原路交回 | — | 不适用 | 流程图里没有交回：每条边都交给新节点，没有一条回到派活给它的节点。照 mero #24624 不写代码，m = 8 是七条 |
| R7 步数上限 | `n` ≤ N | 全局 | N 取让合法流程通过的最小值：四个分析员 1、多头 2、空头 3、研究经理 4、交易员 5、三位辩论者 6–8、复制品 9..8+k、投资组合经理 9+k，所以 N = 9 + k：k = 0、1、2、4、8 时为 9、10、11、13、17。改这个数算进改动 |
| R8 字数上限 | 交出的文本 ≤ 2000 字符 | 全局 | 离线跑的模型输出很短；真模型的报告常超过 2000，会被拒 |

- **用例（没跑）：** `acceptance/test_grid3.py`，环境变量 `GRID_K`、`GRID_M`。
  - 每条装上的规则一放一拒：从最后一位中立分析员（k > 0 时是最后一个复制品）交出，先造一份全过的交接，再弄坏这条查的那个字段；R4 用投资组合经理。
  - 另有一条整次离线运行（每次交接都过）。
  - 写这些的时候用桩模块跑过一次规则逻辑（不是验收）：k = 2 时整条链过，投资组合经理 n = 11，点名齐。
- **特殊点：**
  - 规则本身全局写一次，新角色不加规则行；但 R7 的 N 跟着组织变（9 + k），这是流程图里规则跟着组织变的地方。
  - R4 的「直接下级」也跟着组织变，不过是从图里算出来的，不用改规则代码。
  - 加一个复制品要改约 10 个文件（每个辩论者的提示词都要列出所有同伴），这部分只在组织定义里。

**先扩，再改（mero #24719，静态）。**
- **规则：** TA 没有原生的按角色规则，用我们写并验收过的次数族（`RUNS_LIMIT`，`gen_rules_ta.py`）。改动是把中立分析员这种角色的次数上限从 1 改成 2，原来那个和 k 个复制品全都要改。
- **分支：** grid3-k<k>-m0 里没有任何按角色规则，没有值可改，所以中间加一层：
  - `grid3-k<k>-m0-runs`：在 `grid3-k<k>-m0` 上装次数族，每个角色 1；
  - `grid3-k<k>-m0-change`：在它上面改值。
  - 改动本身是 `-m0-runs..-m0-change`；从 `grid3-k<k>-m0` 数则连装族的行一起算。
- **每个名字各写一遍：** `RUNS_LIMIT` 按节点名一行，复制品各有一行，没有按种类写一次的办法。所以改值要改 k + 1 行：k = 0、1、2、4、8 各改 1、2、3、5、9 行，都在 `role_rules.py` 的一个连续块里（1 处）。

**grid3 验收实测（mero #24911）。** 用 `run_grid3.sh` 跑，单进程，没被停，结果在 `runs/grid3/`（日志 `run.log`）。

| 项 | 分支上对上 | 起点反跑对不上 | 结果文件 |
|---|---|---|---|
| 1 复制品接到发言、原生路由管它（`test_grid3_scale_change.py`，`GRID_CHECK=copy`） | `grid3-k8-m0` 3 / 3 | `grid3-k0-m0` 2 / 3 | `copy__grid3-k8-m0.txt`、`copy__grid3-k0-m0__on_start.txt` |
| 2 改后的次数上限管原来那个和最后一个复制品（`GRID_CHECK=change`） | `grid3-k8-m0-change` 4 / 4 | `grid3-k8-m0-runs` 2 / 4 | `change__grid3-k8-m0-change.txt`、`change__grid3-k8-m0-runs__on_start.txt` |
| 3 `test_grid3.py`（七条规则各一放一拒 + 整次离线运行） | `grid3-k8-m8` 15 / 15 | 没要求反跑 | `rules__grid3-k8-m8.txt` |

- **1 的三条：**
  - 放行：`Neutral Analyst 9` 在整次运行里发言一次，紧接着是投资组合经理；路由在 `Neutral 8` 之后把发言交给它。
  - 拒：所有人都说过以后（count = 11），路由交给投资组合经理，不再给它。
  - 起点上两条放行都反过来了；拒的那条在起点上也成立（起点的轮数门槛是 3，count = 11 同样交给投资组合经理），分不出新旧。
- **2 的四条：** 中立分析员和 `Neutral Analyst 9` 各一放一拒，放行是第 2 次运行，拒是第 3 次运行。起点上限是 1，两条放行反过来了；两条拒在起点上也拒（1 比 2 更严），分不出新旧。

**Sherpa 等价物上的对照（mero #24968，只建树，不跑）。** 分支在 `_scale/tradingagents/sherpa`，`build_grid3.sh` 末段生成。
- **(a) 加执行者：** `eq-grid3-k<k>-m0`，从 `size-1-c-rolecard`（带类、共用卡的 1 倍树）起；`eq-grid3-k0-m0` 就是它。加的位置是 `neutral_analyst_2` .. `k+1`，类 `neutral`，卡 `cards/neutral.md`，取值和中立分析员一样。
  - **每加一个位置 11 行：**
    - `[[instance]]` 6 行（含空行），`[seat.*]` 3 行（节、卡、类），都是组织；
    - 规则参数 2 行，都是 `fixed_order` 的：`after.<新位置>=<前一位>` 1 行（同级先后），`needs.portfolio_manager` 名单 1 项（汇合名单）。
  - **只改一次的：** 投资组合经理卡里点名下级那一行，加第一个位置时名单尾行也改一次（−1 +1）。k = 8 共 +90 −2。
  - **不用写的：** `reopen_limit` 按类写一次（`neutral=0`），不加行。m0 的 `seat_write_limit` 只管四个分析员，也不加行。
- **(d) 先扩再改：** `eq-grid3-k<k>-m0-change`。
  - 对应原系统那次改动（中立分析员能跑两次）的是原生的 `reopen_limit`：`neutral=0` 改 `neutral=1`，可以打回一次，也就是两轮。等价物在角色规则格子里拿 `tool_call_limit` 对 TA 的次数族，但「跑几轮」在 Sherpa 里是 `reopen_limit`，所以用它。
  - 按类写一次，k = 0、1、2、4、8 都只改 1 行、1 处；原系统 k = 8 要改 9 行。
  - 起点就是 `eq-grid3-k<k>-m0`，不用像原系统那样先装一族。
- **用例（没跑）：** `gen_cases_rules_eq.py <out> 8 <tree> - eq-grid3-copy|eq-grid3-change`，跑法 `run_grid3_eq.sh`。和原系统的要点一一对应：
  - (a) 三条：
    - `C-turn-pass`：最后一个复制位置在前一位之后派出，放行。对应「复制品接到发言」。
    - `C-turn-block`：不等前一位就派，`fixed_order.missing_wait` 拒。对应原生路由管它。
    - `C-again-block`：交回后打回，`reopen_limit.limit_reached` 拒。对应「不再给第二次」。
  - (d) 四条：中立分析员和最后一个复制位置各一放一拒，第一次打回放行，第二次打回被 `reopen_limit.limit_reached` 拒。

**(a) 用 `copies = k` 重做（mero #25117，只建树，验收排队）。** 编译器换成研究副本 `seat-copies`（`76ff788`）。`eqn-grid3-k0-m0` 是 `size-1-c-rolecard` 加这个编译器（2 个文件 +55，只一次，算框架本体）；`eqn-grid3-k<k>-m0` 从它起，k = 1、2、4、8。
- **新增行数：** k = 1、2、4、8 各 +5 −2、+7 −2、+11 −2、+19 −2，即 +(2k + 3) −2。
  - `copies = k` 1 行。
  - 规则参数 2k 行，都是 `fixed_order` 的：每个复制位置的 `after.<位置>=<前一位>`，和 `needs.portfolio_manager` 名单里的一项（名单尾行另改一次，−1 +1）。
  - 投资组合经理卡里点名下级那一行改一次（−1 +1）。
  - 复制位置的 `[[instance]]` 和 `[seat.*]` 不再写，由编译器展开。
- **和逐个写位置比，做不到的：** `copies` 只展开实例和席位（卡、类照抄）。`fixed_order` 的 `after.*` 和 `needs.*` 按位置名写，类在那里不认，所以复制位置的先后和汇合名单还得一个一个写：每个位置 2 行规则参数，和逐个写时一样。少掉的只是组织的 9 行。另外，复制品排在原来那个后面的发言先后，`copies` 本身表达不了，也靠这些 `after.*` 行。
- **验收实测（mero #25166）：** `EQN=1 sh run_grid3_eq.sh`，单进程，结果在 `runs/grid3/eq/`（日志 `eqn.log`）。
  - `eqn-grid3-k8-m0`：3 / 3 对上：`neutral_analyst_9` 在前一位之后派出放行；不等前一位被 `fixed_order.missing_wait` 拒；交回后打回被 `reopen_limit.limit_reached` 拒。
  - 起点 `eqn-grid3-k0-m0`：3 / 3 对不上。没有复制位置，派 `neutral_analyst_2` 的准备步骤就被 `classic_lifecycle.not_your_lower` 拒。
  - 第一次跑 `C-again-block` 没对上，是用例写错了：准备步骤没先 `start` 就 `land`，任务还不在能交回的状态。补上 `start` 后重跑三条全对上。第一次的结果留在 `runs/grid3/eq/first_try/`。(d) 的用例有同样的错，一起改了（(d) 还没跑）。

## 7 重点案例：TradingAgents 照原生办法一直加辩论者（mero #25251）

演示一（放大，规则不变）的同一批树，加了 32 倍一档（96 个辩论者，`size-32` 标签和两边的 `…-frozen-at-size-1`，`build_demos.sh` 末段）。

**验收（单进程，结果在 `runs/scale_turns/`）：**

| 树 | TA：一次离线整次运行，每个辩论者按顺序各发言一次 | 等价物：依次派完，最后一位放行、不等前一位被拒、交回后打回被拒 |
|---|---|---|
| 16 倍（48 个辩论者） | 1 / 1 通过 | 3 / 3 对上 |
| 32 倍（96 个辩论者） | **没通过**：LangGraph `GraphRecursionError`，步数上限 100（`default_config.py:135` `max_recur_limit`）不够 | 3 / 3 对上 |

- 32 倍的 TA 一次运行要走 96 个辩论者加前后约 6 步，超过默认的 100 步。要跑通得把 `max_recur_limit` 调大（1 行配置），所以这也是随人数涨、要跟着改的地方：48 个辩论者时还在 100 以内，大约 94 个是上限。树里没改这一行，照原样记。
- 等价物没有这种全局步数上限，96 个位置照样派完。

**每一步的新增行数分三栏**（`count_scale_parts.py`，tsv `runs/scale_parts.tsv`，git diff -U0；「每步」是从前一档到这一档）：

| 档 | 辩论者 | 这一步新加 | 列同伴 | 路由 | 其余 | 合计 |
|---|---|---|---|---|---|---|
| 1→2 | 6 | 3 | +130 −3 | +8 −2 | +256 −3 | +394 −8 |
| 2→4 | 12 | 6 | +530 −6 | +14 −2 | +509 −3 | +1053 −11 |
| 4→8 | 24 | 12 | +2140 −12 | +26 −2 | +1015 −3 | +3181 −17 |
| 8→16 | 48 | 24 | +8600 −24 | +50 −2 | +2027 −3 | +10677 −29 |
| 16→32 | 96 | 48 | +34480 −48 | +98 −2 | +4051 −3 | +38629 −53 |
| 1→32 累计 | 96 | 93 | +45790 −3 | +188 −2 | +7846 −3 | +53824 −8 |

- **折成每个新辩论者：** 列同伴约 43、88、178、358、718 行，每档翻一倍；路由一直约 2 行；其余一直约 84 行。
- **列同伴为什么随人数涨：** 每个辩论者的文件里，每个同伴要占 5 行，提示词那一行也要多点它的名。加第 N+1 个人时，它自己的文件要列 N 个同伴，原来 N 个人的文件也各要多列它一个，所以总量约 5·N·(N−1)，是平方级。96 个人时约 4.6 万行，占全部的 85%。
- **源码里列同伴的地方**（上游原样，即标签 `size-1`，三个辩论者文件 `tradingagents/agents/risk_mgmt/{aggressive,conservative,neutral}_debator.py`）：
  1. 读每个同伴最近一次发言：`:16-21`，每个同伴一个 `opponent_argument_or_opening(...)`，3 行；
  2. 提示词点每个同伴的发言：`:44`（一行长字符串，每个同伴一段）；
  3. 交回的辩论状态带上每个同伴的历史和最近发言：`:54-56`、`:58-63`，每个同伴 2 项。
- **路由：** `tradingagents/graph/conditional_logic.py:23-33`。每加一人，轮换多一个分支（2 行）；轮数门槛 `3 * max_risk_discuss_rounds` 的倍数和注释，每档改一次（−2 +2）。线性。
- **其余：** 每人约 84 行，线性。其中：
  - 新辩论者文件本体约 56 行（复制上游文件，不算列同伴的行）；
  - 上游列出三个辩论者的每一处都给它加一项，约 28 行：`cli/run.py` 8、`state.py` 6（两个字段）、`setup.py` 4（import、路径表、工厂、`add_node`；条件边的元组那一行每档改一次）、`cli/display.py`、`agents/__init__.py`、`portfolio_manager.py`、`propagation.py` 各 2、`trading_graph.py`、`reporting.py` 各 1。
- **等价物：** 1 到 32 倍累计 +1025 −2，每人 11 行：`[[instance]]` 6 行、`[seat.*]` 3 行、`after.*` 1 行、`needs` 名单 1 项，没有平方项，因为卡里不列同伴，同伴的发言在任务和报告文件里。

## 8 汇报线规则 P1、P2（mero #25571，`_scale/GRID4-汇报线规则.md`）

- **分支：** `modified/` 的 `grid3-k<k>-p`，k = 0、1、2、4、8，从 `grid3-k<k>-m0` 起（`build_grid4.sh`，生成器 `gen_grid4.py`）。
- **规则源码：** `tradingagents/graph/report_line.py`（新文件）；`setup.py` 里建图的 `StateGraph` 换成 `ReportLineGraph`（1 行，加 1 行 import）；`state.py` 加 `handoff` 键和它的合并函数。
- **「谁是谁的上级」从哪来：** TA 没有这份数据。规则从图上读：一张路由表路由的那几个节点，表里不属于它们的那个目标就是它们的上级（研究经理管多空研究员，投资组合经理管全部风险辩论者）。这就是路由「到上限交给谁」（`conditional_logic.py:18`、`:28`）和路径表里裁定者那一项（`setup.py:38`、`:44`）在图上的样子。
  - 写法照 grid3 验收过的 `relay_rules.RelayGraph.relay_lowers`：包装每个节点，接收方核对上一步交来的。
  - **「上级」用的是哪种口径（mero #25633）：** 组织图上的上级，即一个组归哪位裁定者管，不是「这一次谁派的」。TA 没有派单，也就没有派发人可读。谁管一个组由图强制：组的路由只能交回到那位裁定者，别的节点到不了它的组员。上级就从这份强制的结构里读。
  - **为什么一处能管到所有角色：** 照上游加一个辩论者，原本就要把它放进路径表和出边元组（这些在 `grid3-k<k>-m0` 里已经有了），所以规则这边不点任何人的名字，每个执行者 0 行。
- **P1、P2 只在「交回」时查**，也就是接收方是裁定者的时候：辩论者交给投资组合经理，多空研究员交给研究经理。辩论者之间的接力不算交回。每个节点交出的文本末尾都加 `from: <自己>`，存进 `handoff`。
- **行数：** k = 0 装两条规则 +98 −1（3 个文件）；k = 1、2、4、8 比 `grid3-k<k>-m0` 也都是 +98 −1，每多一个执行者规则这边 0 行。
- **「谁是谁的上级」在原系统里写在几处：**
  - 规则 2 处：路由的两个终点 `conditional_logic.py:18`、`:28`；
  - 配置 2 处：路径表里两位裁定者的项 `setup.py:38`、`:44`；
  - 提示词 2 处：研究经理（`research_manager.py:23`，「this round of debate」）、投资组合经理（`portfolio_manager.py:42`，「the risk analysts' debate」）；
  - 另有 CLI 显示的分组 `cli/display.py:29-32`（`:218-221` 是同样一份），只管显示。
  - 每个辩论者自己的定义里都不写它的上级。新规则不增加任何一处。
- **用例（`acceptance/test_grid4.py`，`GRID_K=8`；跑法 `run_grid4.sh`，在 `grid3-k8-p` 上跑，再在 `grid3-k8-m0` 上反跑）：**
  1. 最后一个复制品交给它的上级、落款自己：放行；
  2. 交给不是它上级的研究经理：P1 拒；
  3. 落款写成别人：P2 拒；
  4. 原来的中立分析员交给上级、落款自己：放行。
  - 另有一次整次离线运行。上级用图自己算出来的那份。
  - 写的时候用桩模块跑过一遍逻辑（不是验收）：整条链能过；两种拒绝分别报 P1、P2。

## 9 grid5：两族形式规则（mero #25667，`_scale/GRID5-两族形式规则.md`）

- **分支：** `modified/` 的 `g5-k0-g<m>`、`g5-k0-n<m>`（m = 1、2、4、8）和 `g5-k<k>-g<k>`、`g5-k<k>-n<k>`（k = 1、2、4、8），都从 `grid3-k<k>-m0` 起（`build_grid5.sh`，生成器 `gen_grid5.py`）。
- **规则源码：** `tradingagents/graph/form_rules.py`（新）；`setup.py` 里 `StateGraph` 换成 `FormGraph`（+2 −1）；`state.py` 加 `handoff` 键（+6）。
  - 两族用同一套包装，照 grid3 验收过的 `relay_rules`：每个节点包一层，下一步的节点查上一步交来的标记行；投资组合经理后面没人接，在交出那一步自查。
- **通用族：** 标记行是 `g<i>: <交出者自己的名字>`（mero #25753 改的，原来是连续的数），接手的人核对它就是真正交出的那个节点。一个规则名单 `GENERIC_RULES = ["g1", ...]`，查法写一次，不点任何角色。装几条只是名单那一行长短不同，所以 m = 1、2、4、8 都是 +94 −1，加执行者也不变。
- **点名族：** 每条规则一张 dict，键是节点名，值是口令。照 TA 已有的按节点名的表写：原生的路径表（`setup.py:38-48` `RISK_ANALYSIS_PATH_MAP`，每个辩论者一项）和角色规则格子里验收过的 `role_rules.WRITABLE`（每个节点一行）。复制品照它在 `grid3-k<k>-m0` 里进路径表的做法，各占一行，口令和中立分析员相同。
  - **行数：** k = 0 时 n1、n2、n4、n8 是 +105、+120、+150、+210（−1）；一起加时 k = m = 1、2、4、8 是 +106、+124、+166、+274。
  - **每多一条规则 15 行：** 注释 1、表头 1、12 个角色各 1、表尾 1；登记那一行只变长。
  - **每多一个执行者、每条规则 1 行：** 它在那张表里的一行。所以 k = m = 8 比只加规则多 8 × 8 = 64 行。
  - **口令：** 颜色 + 动物，按（规则、角色种类）取，96 个两两不同，不由角色名算出。同一种角色（中立分析员和它的复制品）口令相同。

| 角色 | n1 | n2 | n3 | n4 | n5 | n6 | n7 | n8 |
|---|---|---|---|---|---|---|---|---|
| Market Analyst | cobalt-crane | crimson-ferret | ivory-heron | jade-lynx | lilac-marten | ochre-otter | olive-wren | pearl-badger |
| Sentiment Analyst | crimson-crane | ivory-ferret | jade-heron | lilac-lynx | ochre-marten | olive-otter | pearl-wren | russet-badger |
| News Analyst | ivory-crane | jade-ferret | lilac-heron | ochre-lynx | olive-marten | pearl-otter | russet-wren | slate-badger |
| Fundamentals Analyst | jade-crane | lilac-ferret | ochre-heron | olive-lynx | pearl-marten | russet-otter | slate-wren | teal-badger |
| Bull Researcher | lilac-crane | ochre-ferret | olive-heron | pearl-lynx | russet-marten | slate-otter | teal-wren | amber-badger |
| Bear Researcher | ochre-crane | olive-ferret | pearl-heron | russet-lynx | slate-marten | teal-otter | amber-wren | cobalt-badger |
| Research Manager | olive-crane | pearl-ferret | russet-heron | slate-lynx | teal-marten | amber-otter | cobalt-wren | crimson-badger |
| Trader | pearl-crane | russet-ferret | slate-heron | teal-lynx | amber-marten | cobalt-otter | crimson-wren | ivory-badger |
| Aggressive Analyst | russet-crane | slate-ferret | teal-heron | amber-lynx | cobalt-marten | crimson-otter | ivory-wren | jade-badger |
| Conservative Analyst | slate-crane | teal-ferret | amber-heron | cobalt-lynx | crimson-marten | ivory-otter | jade-wren | lilac-badger |
| Neutral Analyst | teal-crane | amber-ferret | cobalt-heron | crimson-lynx | ivory-marten | jade-otter | lilac-wren | ochre-badger |
| Portfolio Manager | amber-crane | cobalt-ferret | crimson-heron | ivory-lynx | jade-marten | lilac-otter | ochre-wren | olive-badger |

- **用例（`acceptance/test_grid5.py`，跑法 `run_grid5.sh`；每族在 `g5-k8-<f>8` 上跑，再在 `grid3-k8-m0` 上反跑）：**
  1. 第 8 个复制品 8 行都对：放行；
  2. 第 1 条错：拒，报第 1 条；
  3. 第 8 条错：拒，报第 8 条；
  4. 点名族另加：写成另一种角色的口令：拒。
  - 另有一次整次离线运行。
  - 写的时候用桩模块跑过一遍两族的逻辑（不是验收）：整条链能过，错一条报那一条。
- **验收实测（mero #25787）：** `run_grid5.sh`、`run_grid4.sh`，单进程，结果在 `runs/grid5/`、`runs/grid4/`。
  - 通用族：`g5-k8-g8` 对上 4 / 4（3 条照定义，加整次运行；第 4 条只属点名族，跳过）；`grid3-k8-m0` 上 4 / 4 对不上。
  - 点名族：`g5-k8-n8` 对上 5 / 5（4 条照定义，加整次运行）；`grid3-k8-m0` 上 5 / 5 对不上。
  - 汇报线（第 8 节）：`grid3-k8-p` 对上 5 / 5（4 条照定义，加整次运行）；`grid3-k8-m0` 上 5 / 5 对不上（没有 `report_line` 模块，取上级那一步就出错）。
