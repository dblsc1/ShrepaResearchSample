# deer-flow 案例报告

> deerflow-polo，向 mero 汇报。2026-11-19 起。
> 「读代码」= 只读源码得出，没有运行证据；「实测」= 有命令和输出文件。没做的写「没做」。

## 0 工作目录

| 路径 | 是什么 |
|---|---|
| `original/` | `bytedance/deer-flow` 的 `main-1.x`，不带凭据克隆（`git -c credential.helper= clone --branch main-1.x --single-branch`），停在 `2ab2876`，原样不动；推送地址改成了 `no_push` |
| `modified/` | 从 `original/` 本地克隆，标签 `baseline` = `2ab2876`，没有远端。放大的起点和各变更分支都在这里 |
| `v2-original/`、`v2-modified/` | 2.0 主分支，停在 `e0cccd6`，同样做法（`v2-modified` 打了 `baseline`） |
| `deliver/` | 给 writer-sora 的位置清单（TSV + 说明） |
| `tools/` | 自己写的脚本（都用 `python3 -I` 跑）、测试运行器 |
| `runs/` | 每次运行的输出 |
| `venvs/` | 隔离的虚拟环境（uv 按 `uv.lock` 冻结安装，Python 3.12） |

## 1 第 2 项：规则清点（1.x，`2ab2876`）

### 1.1 组织（读代码）

- 9 个节点，建图在 `src/graph/builder.py:53-69`：coordinator → (background_investigator) → planner → human_feedback → research_team ⇄ {researcher, analyst, coder}，最后 reporter。
- 执行组三个：researcher（网搜、爬取、检索）、analyst（无工具）、coder（python_repl）。research_team 是空节点（`nodes.py:957-961`），派单由它的条件边 `continue_to_running_research_team` 按计划中「第一个没做完的步骤」的 `step_type` 决定（`builder.py:24-47`）。
- 边只有 4 条固定边和 1 条条件边写在 builder 里；其余边是节点函数返回 `Command(goto=...)`，返回类型 `Command[Literal[...]]` 声明能去哪（`nodes.py:270,460,591,1082,1359,1428,1471,1486`）。组织定义散在 builder、nodes、planner_model、config/agents 四个文件里。
- 状态（`src/graph/types.py:14-48`）没有任何按节点的读写限制：每个节点都能写任意字段；执行节点还直接改计划对象里步骤的 `execution_res`（`nodes.py:1313`，原地改，不经过状态更新）。

### 1.2 规则表：只算代码强制的，22 条（读代码）

位置按 mero #18843 取法：做判断的最小语法单元的完整行范围。`N` = `src/graph/nodes.py`，`B` = `src/graph/builder.py`。

| 编号 | 规则 | 位置 | 挂在 | 超限/不符时 | 默认 |
|---|---|---|---|---|---|
| R01 | research_team 只派第一个没做完的步骤，按 step_type 派给 researcher / analyst / coder，全做完回 planner；执行节点自己也只取第一个没做完的步骤 | `B:24-47`；`N:1092-1100` | 边（research_team 的条件边） | 改道 | 生效 |
| R02 | 规划轮数到 `max_plan_iterations`（默认 1）不再规划，直接交 reporter | `N:317-321` | 节点 planner | 强制放行 | 生效 |
| R03 | 模型自报 `has_enough_context` 就跳过人审和执行组，直接交 reporter | `N:377-387` | 节点 planner | 放行（凭模型自报） | 生效 |
| R04 | planner 输出不是 JSON：规划过就出报告，否则结束 | `N:341-352`；`N:354-371` | 节点 planner | 拒绝 | 生效 |
| R05 | 人审计划：停下等人，只有 `[ACCEPTED]` 开头才放行到 research_team，其余打回 planner | `N:464-497` | 节点 human_feedback | 拒绝（打回） | 服务端生效（`auto_accepted_plan` 默认假，`chat_request.py:53-55`）；命令行入口写死跳过（`workflow.py:70`） |
| R06 | 计划解析或校验失败：没到 `max_plan_iterations` 打回 planner，到了出报告或结束 | `N:549-570` | 节点 human_feedback | 拒绝 + 上限 | 生效 |
| R07 | `step_type` 只能是三种之一，否则整份计划校验失败（再按 R06） | `src/prompts/planner_model.py:20` | 全局（计划模式） | 拒绝 | 生效 |
| R08 | 步骤缺 `step_type` 时代码补：要搜网补 research，否则补 analysis | `N:145-158` | 全局（计划修补） | 强制改写 | 生效 |
| R09 | `enforce_web_search` 开时，计划里没有搜网步骤就改第一个 research 步（或第一步）为搜网，没步骤就补一步 | `N:164-198` | 全局（配置） | 强制改写 | 不生效（默认关） |
| R10 | 澄清到 `max_clarification_rounds` 轮仍不交接，强制交 planner | `N:750-755` | 节点 coordinator | 强制放行 | 不生效（澄清默认关） |
| R11 | 只有模型调用交接工具才进 planner；不调用：澄清关就结束，开就回落 planner | `N:627-651`；`N:806-846` | 节点 coordinator | 拒绝或放行 | 生效 |
| R12 | 开背景调查时，交 planner 一律先过 background_investigator | `N:849-850` | 边 coordinator→planner | 改道 | 生效 |
| R13 | 每个节点只绑自己的工具（工具表写死在节点函数里） | `N:614`；`N:712`；`N:1437-1449`；`N:1476-1481`；`N:1500-1505` | 节点 | 拿不到别的工具 | 生效 |
| R14 | MCP 服务的工具只给 `add_to_agents` 里写了名字的角色 | `N:1388-1398` | 以角色名为键 | 拿不到 | 只在配了 MCP 时（服务端默认禁 MCP，见 R21） |
| R15 | `agent_name == "researcher"` 时查有没有调用 web_search，没有就在结果后加警告 | `N:1292`；`N:1295-1310`；`N:975-1004` | 以角色名为键 | 只加警告，照样放行（拿不准算不算） | 生效 |
| R16 | 执行 agent 递归上限 `AGENT_RECURSION_LIMIT`（默认 25）；超了不带工具让模型收尾，步骤记为完成 | `N:1152-1172`；`N:1216-1245` | 节点（三个执行节点共用） | 强制放行 | 生效 |
| R17 | 执行出错时把错误文字记为这一步的结果，继续下一步 | `N:1246-1278` | 节点（三个执行节点共用） | 强制放行 | 生效 |
| R18 | `interrupt_before_tools` 里的工具调用前等人批准，没有批准词就不执行 | `src/agents/tool_interceptor.py:44-47`；`:111-144`；`:181-209` | 全局（按工具名） | 拒绝 | 不生效（默认空表） |
| R19 | `ENABLE_PYTHON_REPL` 不为真时 python_repl 拒绝执行 | `src/tools/python_repl.py:17-20`；`:39-42` | 全局（工具） | 拒绝 | 生效：默认就拒，coder 默认跑不了代码 |
| R20 | `enable_web_search` 关时背景调查不搜、researcher 拿不到网搜和爬取 | `N:208-210`；`N:1440-1443` | 全局（配置） | 拦 | 不生效（默认开） |
| R21 | `ENABLE_MCP_SERVER_CONFIGURATION` 不为真时请求带 MCP 设置就 403 | `src/server/app.py:256-260`；`:276` | 全局（服务入口） | 拒绝 | 生效：默认就拒 |
| R22 | 整次运行步数上限 `recursion_limit`（服务端默认 25，命令行 100），超了 LangGraph 抛错终止 | `src/config/configuration.py:27-38` | 全局 | 拒绝（终止） | 生效 |

- **分类：** 节点或边 12（R01–R06、R10–R13、R16、R17），以角色名为键 2（R14、R15），全局 8（R07–R09、R18–R22）。
- **和先前「约 11 条（5 / 4 / 2）」的差别：** 我多算了出错改道（R04、R06、R17）、模型自报跳过（R03）、计划修补（R08、R09）、四个全局开关（R19–R22），按取法它们都是运行时会拒绝、拦住或改道的判断。只留核心 11 条（R01、R02、R05、R07、R10–R16）是：节点或边 8、角色名 2、全局 1。先前算「以角色名为键」的另两条我没算：`nodes.py:1130` 只是给 researcher 多追加两条提示；`AGENT_LLM_MAP` 是角色属性，不是判断。
- **四类共用规则都有：** write（R13、R14），cap（R02、R06、R10、R16、R22），order（R01、R12），review（R05、R18；审的都是人，不是另一个 agent）。
- **没有的东西（读代码）：** 没有按节点限写状态字段；没有「执行节点只做与自己类型相符的步骤」的检查——执行节点只取第一个没做完的步骤（`N:1092-1100`），对不对口全靠 research_team 派对；没有 agent 审 agent。

### 1.3 仅提示词，不算

- 计划最多 `max_step_num` 步（默认 3）：只在 `src/prompts/planner.md:163,177,179,286`，代码不数。
- 「至少一个 research 步要搜网」（`planner.md:105-107,180`）：代码只在 `enforce_web_search` 开时修补（R09），默认关。
- coordinator 的「澄清已关，不许问」「到上限必须调用 handoff_after_clarification」（`N:609,724`）。
- researcher「必须用 local_search_tool」「引用写法」（`N:1140,1146`）。
- 各角色提示词里的分工（如「Researcher can not do math」）。

### 1.4 交给 writer-sora 的

- `deliver/deer-flow-1x-locations.tsv`：元素 9、组织段 10、组织文件 5、规则 22、T、U。
- `deliver/deer-flow-1x-locations.md`：默认组织、仅提示词、加一个角色的估计、7 处拿不准。
- 生成脚本 `tools/write_locations_1x.py`。

### 1.5 起点测试（实测，验收用的基线）

- 环境：`venvs/v1`，`uv sync --frozen --extra test --python 3.12 --no-install-project`（日志 `venvs/v1-sync.log`）。
- 运行器 `tools/run-tests.sh`：`env -i` 干净环境（不继承任何变量），pytest 插件 `tools/blocknet.py` 拒绝一切非本机的连接和域名解析；不跑 `tests/unit/checkpoint`（要 Postgres / MongoDB）和 Tavily 相关测试（要 `TAVILY_API_KEY`）。
- 第一次全跑（只排除 checkpoint）：986 过、17 败、6 错、1 跳（`runs/tests-baseline.txt`）。败和错的 23 条全是 Tavily，报 `Did not find tavily_api_key`，即要密钥，之后排除。

## 2 第 3 项：1.x 规模计数（实测）

### 2.1 怎么放大

- **放大的组：执行组（researcher、analyst、coder）。** size-k 有 3k 个执行者：1、2、4、8 倍是 3、6、12、24 个；节点总数 6 + 3k，即 9、12、18、30。
- **照上游写法重复，不重构**（`tools/gen_1x.py size k`）。第 i 份（i ≥ 2）的 researcher 叫 `researcher_i`，其余同理，每个复制品都和上游原件一样有：
  - 自己的节点函数（照抄原件，换名字）、自己的 `StepType` 值（`research_i`）、派单表里自己的一个分支、一条 `add_node`、条件边名单里的一项；
  - `AGENT_LLM_MAP` 一项、两份提示词文件（英文、中文，照抄原件改自称）、规划者提示词里一段说明；
  - 发言人名单 `ASSISTANT_SPEAKER_NAMES` 照上游只收 researcher、coder 两类的复制品（上游本来就没收 analyst）；
  - 按 `"researcher"` 判断的地方（`N:1130`、`N:1292`、`N:175`）从 `==` 改成列出全部 researcher 的元组，每个名字一行。
- **size-1 就是上游 `2ab2876`，一行没改。** 起点本身的代价（不算进任何变更）：`git diff --shortstat size-1 size-8` = 49 个文件 +3144 −4。
- 标签 `size-1/2/4/8`，分支 `size-k/a|b|c|d`，都在 `modified/`。生成全部起点和分支：`tools/build_1x.sh`。提交号：

| | 起点 | a | b | c | d |
|---|---|---|---|---|---|
| size-1 | `2ab2876` | `812bdd0` | `ba617ea` | `57d9add` | `9f7ebcc` |
| size-2 | `d86e52c` | `415fd94` | `e637927` | `0e0e8e4` | `d42dc2e` |
| size-4 | `37ed5bd` | `e34b31c` | `f3ca438` | `ade2400` | `cf3145f` |
| size-8 | `213e0ce` | `e0ee78b` | `282c7d9` | `e14752f` | `9f90c9e` |

### 2.2 四个变更在 1.x 里怎么做（`tools/gen_1x.py change X k`）

| 变更 | 做法 |
|---|---|
| a 加一个 agent | 新执行者 `fact_checker`（核查步骤，带网搜和爬取工具）：`StepType.FACT_CHECK`、节点函数、builder 的导入 / `add_node` / 派单分支 / 条件边名单、`AGENT_LLM_MAP`、发言人名单、两份提示词、规划者提示词两段（中英） |
| b 每个角色配一条规则 | 按节点限写状态字段：builder 里一张 `NODE_WRITABLE_KEYS` 表（每个节点一行，6 + 3k 行）、一个包装函数 `_limit_writes`，每条 `add_node` 套上包装；节点返回的更新里有表外的键就抛 `PermissionError`（拒绝） |
| c 加一层组长（代码强制） | 新节点 `execution_lead`。research_team 的条件边只剩 planner 和 execution_lead；组长按原派单表派给执行者；执行者一律交回组长（共用的 `_execute_agent_step` 里 `goto` 改成组长），不再自己记步骤结果和观察，只把结果放进新状态字段 `execution_lead_inbox`；只有组长把结果记成步骤结果、加进观察，再报回 research_team。每个执行节点的返回类型标注改成去组长（3k 处） |
| d 复制一整组（并列） | 第二组 `research_team_2` 和 3k 个 `second_*` 执行者（各有自己的步骤类型、节点函数、提示词等，同 2.1）。人审通过后同时派给两组（`goto` 两个目标）；两组各只做自己类型的步骤（第一组的派单表和执行者取步骤时都跳过第二组的类型）；第二组写自己的 `observations_2`、`citations_2`，也不重写会话元字段，免得两组在同一步写同一个键；planner 加 `defer=True`，两组都做完才再规划；reporter 合并两组的观察和引用 |

### 2.3 计数怎么量

- 命令（逐个规模、逐个变更）：
  - `git -C modified diff --numstat size-k size-k/X`（文件数、增删行）
  - `git -C modified diff -U0 size-k size-k/X | grep -c '^@@'`（@@ 数）
  - `python3 -I tools/count_1x.py modified size-k size-k/X runs/count-1x/size-k_X.hunks.tsv`（分类；每个 @@ 的归类写进 `.hunks.tsv`，可逐个核对）。汇总表 `runs/count-1x/table.tsv`。
- 分类按改动**落在哪**，不按为什么改：
  - **规则源码**：派单函数（`continue_to_*`）、组长节点的函数体、限写表和包装函数、按 researcher 判断的语句、计划修补函数、执行者取步骤的循环。
  - **组织定义**：`AGENT_LLM_MAP`、发言人名单、`StepType` 枚举、builder 的节点导入和 `_build_base_graph`、所有函数签名行（`Command[Literal[...]]` 声明边）、所有 `goto` 行、整个执行者节点函数（新节点 = 新元素，工具表含在内，所以 R13 那几行也记在这里）。
  - **框架其余**：状态字段、执行助手函数里的其他改动、其他导入、reporter。
  - **配置**：yaml / json / toml，1.x 的这四个变更都没有碰。
  - **提示词文件**：`src/prompts/*.md`，单列。
  - 已知的粗糙处：签名行一律算组织，所以 d 里给助手函数加的 `team` 参数（3 行）记进了组织。

### 2.4 结果

| 规模 | 变更 | 文件 | @@ | + | − | 规则源码（+/−，@@） | 组织定义（+/−，@@） | 框架其余（+/−，@@） | 配置 | 提示词文件（+/−，@@） |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | a 加一个 agent | 9 | 12 | 50 | 1 | +2 −0，1 | +23 −1，7 | 0 | 0 | +25 −0，4 |
| 2 | a | 9 | 12 | 50 | 0 | +2 −0，1 | +23 −0，7 | 0 | 0 | +25 −0，4 |
| 4 | a | 9 | 12 | 50 | 0 | +2 −0，1 | +23 −0，7 | 0 | 0 | +25 −0，4 |
| 8 | a | 9 | 12 | 50 | 0 | +2 −0，1 | +23 −0，7 | 0 | 0 | +25 −0，4 |
| 1 | b 每个角色一条规则 | 1 | 4 | 65 | 9 | +50 −0，1 | +11 −9，1 | +4 −0，2 | 0 | 0 |
| 2 | b | 1 | 4 | 71 | 12 | +53 −0，1 | +14 −12，1 | +4 −0，2 | 0 | 0 |
| 4 | b | 1 | 4 | 83 | 18 | +59 −0，1 | +20 −18，1 | +4 −0，2 | 0 | 0 |
| 8 | b | 1 | 4 | 107 | 30 | +71 −0，1 | +32 −30，1 | +4 −0，2 | 0 | 0 |
| 1 | c 加一层组长 | 3 | 19 | 59 | 16 | +25 −0，1 | +26 −10，10 | +8 −6，8 | 0 | 0 |
| 2 | c | 3 | 22 | 65 | 27 | +25 −0，1 | +32 −21，13 | +8 −6，8 | 0 | 0 |
| 4 | c | 3 | 28 | 77 | 39 | +25 −0，1 | +44 −33，19 | +8 −6，8 | 0 | 0 |
| 8 | c | 3 | 40 | 101 | 63 | +25 −0，0 | +68 −57，32 | +8 −6，8 | 0 | 0 |
| 1 | d 复制一组 | 14 | 43 | 540 | 29 | +37 −6，7 | +138 −9，16 | +22 −14，12 | 0 | +343 −0，8 |
| 2 | d | 20 | 49 | 984 | 26 | +37 −3，7 | +243 −9，16 | +22 −14，12 | 0 | +682 −0，14 |
| 4 | d | 32 | 61 | 1890 | 26 | +55 −3，7 | +453 −9，16 | +22 −14，12 | 0 | +1360 −0，26 |
| 8 | d | 56 | 85 | 3702 | 26 | +91 −3，7 | +873 −9，16 | +22 −14，12 | 0 | +2716 −0，50 |

（@@ 按多数行归类；一个 @@ 里规则和组织各半时只算一边，所以 size-8 的 c 规则源码 @@ 是 0、行数仍是 +25。）

### 2.5 读法

- **a 不随规模变**：9 个文件、12 个 @@、+50。改到规则源码的只有 1 处（派单表 R01 加一个分支，+2 行）；组织定义 23 行散在 5 个文件（枚举、节点函数、builder 三处、模型表、发言人名单）；提示词 25 行。和子代理先前读出的「5 个文件 6 到 7 处」比，实际是 9 个文件：多出的是两份新提示词文件和规划者提示词（中英两份），代码文件正好 5 个。
- **b 随规模线性增长**，每多一个角色 +2 行（表里一行、`add_node` 改一行）：size-1 +65 −9，size-8 +107 −30。只碰 builder 一个文件。读代码得出的漏洞：限写只查节点**返回**的更新；执行者原地改计划对象里步骤的 `execution_res`（`N:1313`）不经过返回，查不到。
- **c 随规模增长**：size-1 +59 −16，size-8 +101 −63。不变的部分是规则源码 +25（research_team 新的派单函数和组长函数体）和框架其余 +8 −6（状态字段、执行者改交收件箱）。增长的全在组织定义：每个执行节点的返回类型标注改一行（3k 行），条件边名单从 research_team 挪到组长的返回类型里（约 3k 行）。标注只给 LangGraph 画图和静态检查用，运行时不靠它；上游每个节点都写，所以照改。
- **d 随规模线性增长，量最大**：size-1 14 个文件 +540，size-8 56 个文件 +3702。大头是提示词（每个复制品两份文件，size-8 占 2716 行）和新节点函数（组织 873 行）。另有不变的部分：两组并行时要防同一步写同一键（1.x 的状态没有合并规则，每个执行者都重写 8 个会话元字段），所以第二组改写自己的字段、不写元字段，planner 等两组（`defer=True`），reporter 合并。「不这样做会报错」是读 LangGraph 的语义得出的，我没有实做一个不防的版本去看它报错。

## 3 第 4 项：1.x 验收（实测）

### 3.1 自己的验收：假模型跑真图

- 脚本 `tools/accept_1x.py`：换掉 `src.graph.nodes` 里的 `get_llm_by_type` 和 `create_agent`，不调任何模型；真图 `builder.build_graph()` 从 coordinator 跑到 reporter（计划由假模型给出，每个执行者一个步骤，两组交错排）。
- 每个起点都查：每步都做了、每步恰好由它的 `step_type` 指定的执行者做一次、每步一条观察、reporter 写出报告。
- 变更另查：
  - b：再跑一遍，把 researcher 换成一个写 `final_report` 的节点，被 `PermissionError` 拒绝。
  - c：research_team 的出边只有 planner 和 execution_lead；每个执行者的出边只有 execution_lead；执行序列里每个执行者前后都是组长；把 research_team 的派单函数改成直接派 researcher，运行被拒（`KeyError: 'researcher'`，LangGraph 不认名单外的去向）。
  - d：人审后两组同时开始；第二组的步骤只由第二组做；planner 跑两次，第二次在两组都做完之后。
- 结果：20 个提交（4 个起点 + 16 个分支）全过。输出 `runs/accept-1x/<提交>.txt`，命令 `tools/run_all_1x.sh`。
- 反跑（实测，只做了 size-1）：拿每个变更的验收去起点 `size-1` 上跑，确认验收能分辨。输出 `runs/accept-1x-reverse/size-1_start_as_<X>.txt`。
  - a、d：起点没有这两个变更加的步骤类型，假模型的计划解析失败，运行崩（`AttributeError: 'str' object has no attribute 'steps'`），exit 1。是「崩」不是「查出来」，但验收没有误报通过。
  - b：起点四项都过；「researcher 写 final_report 被拒」不过：起点不拒，被劫持的节点一直循环到 `GraphRecursionError`（上限 1000）。
  - c：执行序列三项过；「research_team 只能到 planner 和 execution_lead」「执行者只能到 execution_lead」两项不过（起点 research_team 能直接到三个执行者）。
- 没做：size-2/4/8 的反跑。

### 3.2 上游测试

- 每个提交跑 `tools/run-tests.sh`（`tests/unit` 去掉 checkpoint 和 Tavily，加 `tests/test_state.py`），输出 `runs/tests-1x/<提交>.txt`。
- 4 个起点都是 978 过、1 跳（另有 23 条 Tavily 被排除）。a、b 的 8 个分支都和起点一样。
- 变了的（每个规模都一样）：

| 分支 | 失败的测试 | 原因（读测试代码） |
|---|---|---|
| c | `tests/unit/graph/test_nodes_recursion_limit.py::TestHandleRecursionLimitFallback::test_fallback_generates_summary_from_observations`、`::test_fallback_sanitizes_response` | 测试断言递归上限回退时执行者自己把结果写进步骤；c 的规矩正是「只有组长记步骤结果」，回退那一行被删了。行为是有意改的 |
| d | `tests/unit/graph/test_builder.py::test_build_base_graph_adds_nodes_and_edges` | 测试写死「条件边只有 1 条」（`test_builder.py:100`）；d 给第二组加了第 2 条 |

- 我没有改上游测试。

## 4 第 5 项：2.0（`e0cccd6`）同一张表（实测）

### 4.1 2.0 的组织和规则（读代码，详见 `deliver/deer-flow-2-locations.md`）

- 没有流程图。lead agent 用 `task` 工具派子 agent，结果作为工具返回；内置子 agent general-purpose、bash；自定义子 agent 写在 `config.yaml` 的 `subagents.custom_agents.<名字>`。
- 代码强制的规则 18 条：节点或边 0、以角色名为键 6、全局 12。按名字取参数的判断代码都是通用的，代码里只点了一个角色名（`bash`）。
- 子 agent 不能再派子 agent（V01），三道：组装子 agent 的工具时 `subagent_enabled` 写死 False（`task_tool.py:1096-1101`），默认禁用表含 `task`，托管定义强制禁用。

### 4.2 怎么放大

- 照 1.x：同一个执行组写成 2.0 文档里的样子，`config.yaml` 里 3k 个自定义子 agent（`researcher`、`analyst`、`coder`，复制品 `researcher_2` 等），工具表对应 1.x（网搜和抓取 / 无 / bash 和读写文件）。
- `config.yaml` = `config.example.yaml` 原样，在注释掉的示例段前插入一段生效的 `subagents:`，并把 `max_total_per_run` 设成上限 50（默认 6 不够 3k 个子 agent 用）。上游不入库 `config.yaml`，我在 `v2-modified` 里强制加入，git 才看得到改动。
- 起点本身的代价：`git diff --shortstat size-1 size-8` = 1 个文件 +182。
- 生成：`tools/gen_v2.py`，`tools/build_v2.sh`（在单独的工作树 `wt-build-v2` 里建，避免测试产物混进提交）。提交号：

| | 起点 | a | b | bcfg | c | d |
|---|---|---|---|---|---|---|
| size-1 | `90edae3` | `f20239e` | `ad27a74` | `cf29599` | `d65f6f5` | `1182447` |
| size-2 | `a1bc0d8` | `25622cf` | `845e00a` | `d3666e5` | `f7e72b8` | `c47c332` |
| size-4 | `1c315ef` | `4f8d8c0` | `a2c2aa1` | `80825c6` | `20690b0` | `f690b85` |
| size-8 | `5e96e09` | `7d2d249` | `5c997de` | `10a67b5` | `d8a256b` | `8919b76` |

### 4.3 四个变更在 2.0 里怎么做

| 变更 | 做法 |
|---|---|
| a 加一个 agent | `config.yaml` 加一段 `fact_checker`（键、description、system_prompt、工具表）。lead 的提示词和 task 的可选名单都从注册表自动生成，不用改别处 |
| b 每个角色配一条规则 | 同 1.x 的「限写」：2.0 没有这种规则，要写代码。`CustomSubagentConfig`、`SubagentConfig` 加字段 `write_paths`，注册表照抄一行；新中间件 `WritePathMiddleware`（write_file、str_replace 的路径不在前缀下就返回错误）；执行器在组装子 agent 中间件时挂上。配置里每个子 agent 一行 `write_paths: ["/mnt/user-data/outputs/<名字>"]`。只覆盖自定义子 agent（内置子 agent 走另一套覆盖配置，lead 也没覆盖）；bash 工具能绕过（读代码） |
| bcfg 每个角色一条规则（现成配置项） | 另量一种：用 2.0 已有的按角色配置项，每个子 agent 加一行 `max_turns: 25`。纯配置 |
| c 加一层组长（代码强制） | 框架禁止嵌套，最小改动：`CustomSubagentConfig`、`SubagentConfig` 加字段 `allowed_subagents`，注册表照抄一行；task 工具两处：给声明了 `allowed_subagents` 的子 agent 组装 task 工具，子 agent 调 task 时只许派给自己的名单。配置：`execution_lead` 一段（工具只有 task，名单列全部 3k 个执行者，每个一行）；另加一个自定义 lead agent `research-lead`（`backend/.deer-flow/agents/research-lead/config.yaml`），`allowed_subagents` 只有 execution_lead。没做：给组长挂派单数上限中间件（`SubagentLimitMiddleware` 现在只挂在 lead 上）、委派台账的两层记账 |
| d 复制一整组（并列） | `config.yaml` 加 3k 段 `second_*`。2.0 的子 agent 本来就由 lead 并行派，不用改代码 |

### 4.4 计数

- 命令同 1.x，仓换成 `v2-modified`，分类脚本 `tools/count_v2.py`，汇总表 `runs/count-v2/table.tsv`，每个 @@ 的归类在 `runs/count-v2/size-k_X.hunks.tsv`。
- 2.0 的组织和按角色的规则都写在 `config.yaml` 里，所以配置这一栏再按行分三种：**配置·组织**（子 agent 的键、tools、disallowed_tools、allowed_subagents，自定义 lead 的名字和名单）、**配置·规则**（write_paths、max_turns）、**配置·提示词**（description、system_prompt，给模型读的文字）。Python 里：b 的字段、中间件和挂载算规则源码；c 里 task 工具「子 agent 只许派给自己的名单」那 3 行算规则源码，字段、注册表和「给组长 task 工具」那一行算框架其余。

| 规模 | 变更 | 文件 | @@ | + | − | 规则源码（+/−，@@） | 组织定义（源码） | 框架其余（+/−，@@） | 配置·组织（+/−） | 配置·规则（+/−） | 配置·提示词（+/−） |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | a 加一个 agent | 1 | 1 | 9 | 0 | 0 | 0 | 0 | +4 | 0 | +5 |
| 2 | a | 1 | 1 | 9 | 0 | 0 | 0 | 0 | +4 | 0 | +5 |
| 4 | a | 1 | 1 | 9 | 0 | 0 | 0 | 0 | +4 | 0 | +5 |
| 8 | a | 1 | 1 | 9 | 0 | 0 | 0 | 0 | +4 | 0 | +5 |
| 1 | b 每个角色一条规则（新规则，要写代码） | 6 | 8 | 51 | 0 | +44 −0，4 | 0 | +4 −0，1 | 0 | +3 | 0 |
| 2 | b | 6 | 11 | 54 | 0 | +44 −0，4 | 0 | +4 −0，1 | 0 | +6 | 0 |
| 4 | b | 6 | 17 | 60 | 0 | +44 −0，4 | 0 | +4 −0，1 | 0 | +12 | 0 |
| 8 | b | 6 | 29 | 72 | 0 | +44 −0，4 | 0 | +4 −0，1 | 0 | +24 | 0 |
| 1 | bcfg 每个角色一条规则（现成配置项） | 1 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | +3 | 0 |
| 2 | bcfg | 1 | 6 | 6 | 0 | 0 | 0 | 0 | 0 | +6 | 0 |
| 4 | bcfg | 1 | 12 | 12 | 0 | 0 | 0 | 0 | 0 | +12 | 0 |
| 8 | bcfg | 1 | 24 | 24 | 0 | 0 | 0 | 0 | 0 | +24 | 0 |
| 1 | c 加一层组长 | 6 | 7 | 27 | 1 | +3 −0，1 | 0 | +7 −1，4 | +11 | 0 | +6 |
| 2 | c | 6 | 7 | 30 | 1 | +3 −0，1 | 0 | +7 −1，4 | +14 | 0 | +6 |
| 4 | c | 6 | 7 | 36 | 1 | +3 −0，1 | 0 | +7 −1，4 | +20 | 0 | +6 |
| 8 | c | 6 | 7 | 48 | 1 | +3 −0，1 | 0 | +7 −1，4 | +32 | 0 | +6 |
| 1 | d 复制一组 | 1 | 1 | 26 | 0 | 0 | 0 | 0 | +11 | 0 | +15 |
| 2 | d | 1 | 1 | 52 | 0 | 0 | 0 | 0 | +22 | 0 | +30 |
| 4 | d | 1 | 1 | 104 | 0 | 0 | 0 | 0 | +44 | 0 | +60 |
| 8 | d | 1 | 1 | 208 | 0 | 0 | 0 | 0 | +88 | 0 | +120 |

### 4.5 验收（实测）

**自己的验收：假模型跑真 lead**

- 脚本 `tools/accept_v2.py`，`tools/run_all_v2.sh` 逐个提交跑。
  - 只换模型：`config.yaml` 里加一个模型条目，指向 `tools/v2fake/scripted_model.py` 的 `ScriptedChatModel`。它按系统提示词认出自己是 lead 还是哪个子 agent，按计划文件发 task 调用，每轮最多 3 个，和 `max_concurrent` 默认值一样。每次调用记日志。
  - 其余都是真的：Gateway 的图工厂 `make_lead_agent`、真 task 工具、真子 agent 执行器、真中间件链。
  - 不联网（`blocknet`），`env -i` 起进程。
- 每个起点查三项：
  1. 组里每个子 agent 都跑了；
  2. lead 收到了它们的结果；
  3. 没有子 agent 发出 task 调用。
- 变更另查：
  - b：coder 往自己的 `write_paths` 下写被放行；往 researcher 的目录写被拒（`may only write`）。
  - c 用自定义 lead `research-lead`：
    - lead 只派给 execution_lead；
    - 组长派给全部执行者，执行者全跑了，组长收到了结果；
    - lead 直接派 researcher 被拒（`Unknown subagent type`）；
    - 执行者想再往下派，被拒（它没有 task 工具）。
- 结果（`runs/accept-v2/<提交>.txt`）：

每格「上限 100 的结果 ∣ 上限 1000 的结果」。上限 1000 只重跑了上限 100 下崩的 6 个，其余记「—」（没跑）。

| 规模 | 起点 | a | b | bcfg | c | d |
|---|---|---|---|---|---|---|
| 1（3 个执行者） | 3/3 ∣ — | 3/3 ∣ — | 5/5 ∣ — | 3/3 ∣ — | 6/6 ∣ — | 3/3 ∣ — |
| 2（6 个） | 3/3 ∣ — | 3/3 ∣ — | 5/5 ∣ — | 3/3 ∣ — | 6/6 ∣ — | 3/3 ∣ — |
| 4（12 个） | 3/3 ∣ — | 3/3 ∣ — | 5/5 ∣ — | 3/3 ∣ — | 6/6 ∣ — | **崩** ∣ 3/3（d 有 24 个） |
| 8（24 个） | **崩** ∣ 3/3 | **崩** ∣ 3/3 | **崩** ∣ 5/5 | **崩** ∣ 3/3 | 6/6 ∣ — | **崩** ∣ 3/3（48 个） |

上限 1000 下 24 个提交的验收全过。上限 100 的输出留在 `runs/accept-v2/<提交>.rl100.txt`，上限 1000 的在 `runs/accept-v2/<提交>.txt`，重跑命令 `tools/accept_rerun_v2.sh size-4/d size-8 size-8/a size-8/b size-8/bcfg size-8/d`。

- **崩的 6 个是同一个原因：`GraphRecursionError: Recursion limit of 100 reached`。**
  - 我的 2.0 验收给 lead 一次运行的 `recursion_limit` 是 100。这是 Gateway 在客户端不传时的默认值（`app_config.py:261-265`，规则 V18）。1.x 的验收用的是 1000（`tools/accept_1x.py:79`），两边不对等，是我的疏忽。
  - 实测：每轮 lead 最多派 3 个（假模型这样发；真模型多发也会被 V09 截到 3 个）。100 步内 lead 只跑了 6 轮、派出 18 个，就停了。日志在 `runs/v2home/<提交>/main/calls.jsonl`。
  - 由此推出 lead 每轮约占 16 步。这是推算：中间件各占图的节点，我没有逐一数。
  - c 在 size-8 不崩：lead 只派 1 次（派给组长），组长在自己的子 agent 运行里派 24 个，它的步数上限是 `max_turns`，不受 lead 的 100 步管。
  - 这也是一个实测结论：**按 Gateway 默认配置，一个 lead 一次运行派不完 24 个子 agent**。V09（每轮 3 个）和 V18（每次运行 100 步）两条全局规则合起来，给组的大小设了一个隐含上限，约 18 个。要放大到 size-8，得把 `recursion_limit` 调高：每次运行在请求里传，或在 `config.yaml` 改默认值，上限 `max_recursion_limit` 默认 1000。这一项没进 §4.4 的计数。如果走改 `config.yaml` 这条路，size-8 的起点多 1 行配置·规则。
- 已改：`tools/accept_v2.py` 改成默认 1000（可用环境变量 `ACCEPT_RECURSION_LIMIT` 改），和 1.x 一致。崩的 6 个在内存队列轮到我后（mero #22979）一次一个进程重跑，全过（见上表右半）。
- 2.0 的特有发现，c 的反面：同一个自定义 lead `research-lead` 换用嵌入式客户端 `DeerFlowClient` 跑，lead 直接派 researcher，**researcher 跑了**。`client.py` 不读自定义 agent 的 `allowed_subagents`（V03 只在 Gateway 路径生效）。也就是说，c 的「lead 只能经组长派」只在 Gateway 上成立。验收里这一项记为 NOTE 行，不算 PASS/FAIL；4 个规模的 c 都一样。
- 反跑（实测，只做了 size-1）：拿每个变更的验收去没改过的起点 `size-1` 上跑，命令 `tools/accept_reverse_v2.sh`，输出 `runs/accept-v2-reverse/size-1_start_as_<X>.txt`。四个都 exit 1，验收没有误报通过：
  - a：「组里每个子 agent 都跑了」不过，缺 `fact_checker`。起点没有它，task 预检拒掉（V02）。另两项过。
  - b：起点四项都过；「coder 往 researcher 的目录写被拒」不过：起点没有限写，工具回 `OK`。
  - c：直接崩，`FileNotFoundError: Agent directory not found: …/agents/research-lead`。起点没有自定义 lead `research-lead`，运行起不来。是「崩」不是「查出来」，和 1.x 的 a、d 一样。
  - d：「组里每个子 agent 都跑了」不过，缺 `second_analyst`、`second_coder`、`second_researcher`。另两项过。
  - bcfg 没反跑：它的验收只有起点那三项，没有专门查 `max_turns` 的项，反跑分辨不了。
- 没做：
  - size-2/4/8 的反跑；
  - bcfg 的专项验收：没查 `max_turns: 25` 是否真的生效；
  - b 的 bash 绕过：读代码可知 bash 工具能写任意路径，没实测；
  - 内置子 agent 和 lead 的写限制：b 没覆盖它们。

**上游测试：子集**

**上游测试：全量**（只跑了 Python 有改动的两个分支：size-1/b、size-1/c，加 baseline）

- 第一次：三份同时跑，被系统以内存不足停掉（机器 14 GB），没跑完。部分输出移到 `runs/tests-v2-full/oom-run1/`。
- 第二次：mero 排内存队列后（#22979），一次一份跑，脚本 `tools/run_full_v2.sh`，用的是 `run-tests-v2.sh` 不带文件名（`-m "not live and not integration"`，不联网）。输出 `runs/tests-v2-full/<提交>.txt`。

| 提交 | 结果 |
|---|---|
| baseline `e0cccd6` | 77 失败、42527 过、992 跳、86 排除，49 分 50 秒 |
| size-1/b | 79 失败、42524 过、993 跳，54 分 46 秒 |
| size-1/c 第一次 | **没跑完**：到 93% 时 pytest 自己崩了（`INTERNALERROR`，终端输出时 `ValueError('I/O operation on closed file.')`），不是被系统停的。崩之前从约 60% 起就已经连片失败（见下） |
| size-1/c 第二次（仓主让再试，mero #23087） | 77 失败、42526 过、993 跳、86 排除，56 分 26 秒，没崩 |

- size-1/c 第一次为什么坏（实测加推断）：
  - 按 `--collect-only` 的顺序把进度符号对到测试名上，前约 25560 个测试的失败和 baseline 一样。从 `tests/test_project_document_tools.py` 起，往后 200 多个文件大片 F 和 E，这些文件在 baseline、size-1/b 上都过；之后到 93% 崩掉。
  - 单跑 `tests/test_project_document_tools.py`：49 个全过（`runs/tests-v2-full/single/one-c-pdt.txt`）。
  - 第二次用同一个提交跑完全量，这些文件也都过了。所以是那一次运行的环境问题，或者某个测试污染了后面的状态，不是 c 的代码。具体原因没查到：失败摘要随崩溃丢了。
- 第二次改了的命令行参数（`tools/run_full_c_retry.sh`）：`-q` 换成 `-v`，每个测试一行，方便定位连片失败；加 `--junitxml=runs/tests-v2-full/size-1_c.retry.xml`，崩了也有逐条结果。其余同 `run-tests-v2.sh`：`env -i`、`-p blocknet -p no:cacheprovider -rfE -m "not live and not integration"`，输出本来就直接写文件。输出 `runs/tests-v2-full/size-1_c.retry.txt`，第一次的留在 `size-1_c.txt`。
- size-1/c（第二次）和 baseline 比：多 1 个失败，少 1 个失败（跳过 +1），**c 自己造成的失败是 0**。
  - 多的 `tests/blocking_io/test_subagent_registry_offloop.py::test_task_tool_sandbox_policy_resolves_off_loop`：单跑对照，baseline 4 过；起点 `size-1`、size-1/b、size-1/c 都是 1 失败 3 过。是起点造成的，同 b。
  - 少的 `test_config_upgrade_creates_checkout_config_when_none_exists`：变成跳过，同 b，原因是仓里有 `config.yaml`。
  - 和 size-1/b 比：c 没有 b 那 2 个 `test_skills_authorization` 失败（c 没碰执行器）。其余完全一样。
  - 单跑对照的输出都在 `runs/tests-v2-full/single/`。
- baseline 的 77 个失败都是环境问题（读失败信息）：
  - 17 个是 PATH 里没有 `uv`（同子集）；
  - 38 个 `test_extension_manager.py`、1 个 `test_extension_dependency_sync.py`，都要调 `uv`；
  - 13 个是 `blocknet` 拒了 DNS 或网络（`test_web_tool_url_validation.py` 10 个、`test_personal_mcp_network.py` 3 个）；
  - 其余 8 个（`test_web_fetch_relative_links.py` 5 个，沙箱和 boxd 3 个）没逐个查原因。它们在 size-1/b 上一样失败，和改动无关。
- size-1/b 比 baseline 多 3 个失败、少 1 个失败（跳过 +1）：
  - 少的 1 个：`test_config_upgrade_creates_checkout_config_when_none_exists` 变成跳过，同子集，原因是仓里有 `config.yaml`。
  - 多的 `tests/blocking_io/test_subagent_registry_offloop.py::test_task_tool_sandbox_policy_resolves_off_loop`：**起点造成的，不是 b**。我单跑这个文件做了对照（实测）：baseline 4 过，起点 `size-1` 和 size-1/b 都是 1 失败 3 过。失败信息 `Unknown subagent type 'bash'. Available: general-purpose, researcher`。原因没核对代码。起点和 baseline 唯一的差别是仓里多了 `config.yaml`（声明了自定义子 agent），所以推断是测试读到了它。这个文件不在 68 个文件的子集里，所以子集没看到。
  - 多的 `tests/test_skills_authorization.py::test_subagent_executor_resolves_skill_authorization_for_chain`、`::test_subagent_executor_shares_one_skill_authorization_instance`：**是 b 造成的**。失败信息 `AttributeError: 'types.SimpleNamespace' object has no attribute 'write_paths'`：测试用 `SimpleNamespace` 冒充子 agent 配置，我在执行器里写的是 `self.config.write_paths`。改成 `getattr(self.config, "write_paths", None)` 应该就过，但我没改也没验证，计数按现在的提交算。这也说明：在 2.0 里加一种按角色的新规则，会碰到上游测试对配置对象形状的假设。

**上游测试：子集**

- 改跑子集：68 个文件（`tools/v2-subset.txt`），是和配置、lead、子 agent、task 工具、中间件有关的测试。命令 `tools/run-tests-v2.sh <工作树> <输出> <文件…>`，输出 `runs/tests-v2/<提交>.txt`。
- baseline（`e0cccd6` 原样）：17 失败、2082 过、28 跳。17 个失败全在 `tests/test_config_version.py`，原因都是 `scripts/config-upgrade.sh: line 60: uv: command not found`。我的 `env -i` 环境的 PATH 里没有 `uv`，是环境问题，和改动无关。
- 24 个提交：都是 16 失败、2082 过、29 跳。和 baseline 唯一的差别是 `test_config_upgrade_creates_checkout_config_when_none_exists` 从失败变成跳过，所有起点和分支都一样。
  - 原因（读测试代码，`test_config_version.py:773-774`）：仓里有 `config.yaml` 时它自己跳过；起点强制加入了 `config.yaml`。
  - 所以在子集里，四个变更没有让任何上游测试改变结果。全量（只跑了 b、c）里，b 让 2 个测试失败，c 是 0（见上）。
  - size-8/d 后来跑完，也是 16 失败、2082 过、29 跳，同上。24 个全齐。
- 我没有改上游测试。

## 5 重写前后对照（1.x 和 2.0，同一个执行组，实测计数）

每格是 `git diff -U0` 起点到分支的：文件数、@@ 数、+/− 行数，括号里是规则源码（Python）行数。2.0 的「配置」指 `config.yaml`。

| 变更 | 1.x size-1 | 1.x size-8 | 2.0 size-1 | 2.0 size-8 |
|---|---|---|---|---|
| 起点放大 1→8 倍 | — | 49 个文件 +3144 | — | 1 个文件 +182 |
| a 加一个 agent | 9 文件 12 @@ +50 −1（规则 +2） | 9 / 12 / +50 −0（规则 +2） | 1 文件 1 @@ +9（规则 0） | 同左 |
| b 每个角色一条新规则 | 1 / 4 / +65 −9（规则 +50） | 1 / 4 / +107 −30（规则 +71） | 6 / 8 / +51（规则 +44，配置·规则 +3） | 6 / 29 / +72（规则 +44，配置·规则 +24） |
| bcfg 现成按角色配置项 | 1.x 没有对应的配置项 | — | 1 / 3 / +3（纯配置） | 1 / 24 / +24 |
| c 加一层组长 | 3 / 19 / +59 −16（规则 +25） | 3 / 40 / +101 −63（规则 +25） | 6 / 7 / +27 −1（规则 +3，框架 +7 −1） | 6 / 7 / +48 −1（同左） |
| d 复制一整组 | 14 / 43 / +540 −29（规则 +37 −6） | 56 / 85 / +3702 −26（规则 +91 −3） | 1 / 1 / +26（规则 0） | 1 / 1 / +208（规则 0） |

**读法。** 下面每条注明来源：「实测」是上表的数字，「读代码」是读源码得出的。

1. 实测：在 2.0 里，加 agent（a）和复制一组（d）都不碰任何 Python，也不碰规则源码，只改 `config.yaml`。1.x 加一个 agent 要碰 5 个代码文件，其中规则源码 1 处，因为派单表 R01 按 StepType 点名。复制一组到 size-8 是 56 个文件 +3702。
   - 对 Sherpa 不利的一点：「改组织不碰规则」这件事，2.0 不靠检查点就做到了。它靠的是把组织搬进配置，加上通用的、按名字取参数的规则代码。
   - 本报告只量 deer-flow，没有 Sherpa 自己的数。仓主 2026-11-19 定：「位置的类」算 Sherpa 的一部分；拿 Sherpa 对照时，以带类的数为准（由 writer-sora 汇总）。deer-flow 的数不变。
2. 实测：需要一种新规则时（b 限写），两边都得写代码。
   - 2.0 是固定成本：+44 行规则源码，碰 6 个文件，不随规模变。另外每个角色 1 行配置。
   - 1.x 的规则源码随规模涨：+50 到 +71。限写表按节点名列出，每个角色一行。
   - 规则若是现成的配置项（bcfg），2.0 每个角色只要 1 行配置。
3. 实测：加一层组长（c）。
   - 2.0 框架禁止嵌套，要改框架：规则 +3、框架 +7 −1，固定不变。配置每个执行者 1 行（组长的名单）。
   - 1.x 的规则源码固定 +25，但组织定义随规模涨（每个执行者的返回类型标注、边名单），size-8 是 +68 −57。
4. 实测加读代码：2.0 的规则不挂在节点和边上，但有两处挂在入口和全局参数上。这两处随组织变化会出问题，计数看不出来：
   - **V03 只在 Gateway 路径生效**（实测）：嵌入式客户端不管 `allowed_subagents`，c 的层级在那条路径上不成立。
   - **V09 和 V18 合起来限住了组的大小**（实测）：按默认值，一次运行派到约 18 个子 agent 就停。放大到 size-8 要调 `recursion_limit`。
   - 上限提到 1000 后 size-8 全过（实测），所以这是默认值问题，不是做不到。
   - 1.x 没量到这类问题，但也没在默认值下量过：它的验收按我设的 1000 步跑，全过。1.x 自己的默认值是 `get_recursion_limit(default=100)`（`src/workflow.py:103`），用默认值时 size-8 会不会撞上，我没量。
5. 对比的局限：
   - 行数不是同一种单位。2.0 一行 YAML 和 1.x 一行 Python 改起来的难度不同。
   - 2.0 的提示词写在 `config.yaml` 里，1.x 的是单独的 `.md` 文件，所以分成「配置·提示词」和「提示词文件」两栏。
   - 2.0 的 b、c 是我写的最小实现，b 只覆盖自定义子 agent，没覆盖内置子 agent 和 lead。上游如果自己实现，量可能不同。

## 6 组合演示（mero #23876，静态计数；验收只写了用例，没跑）

### 6.1 演示一：放大，规则不变（实测计数）

- 新建 `size-16`：用和 1–8 倍同一个生成器，`tools/build_size16.sh`。1.x `size-16` = `01610a7`；2.0 `size-16` = `6556f2910`（48 个自定义子 agent，没超过 `max_total_per_run` 的上限 50）。
- 命令：
  - 1.x：`python3 -I tools/count_1x.py modified size-1 size-<k> <hunks>`
  - 2.0：`python3 -I tools/count_v2.py v2-modified size-1 size-<k> <hunks>`
  - 每个 @@ 的归类在 `runs/demo1/`。
- 三栏怎么并：
  - 1.x：其余 = 框架其余 + 配置 + 提示词文件。
  - 2.0：组织定义 = 源码组织 + 配置·组织；其余 = 框架 + 配置·规则 + 配置·提示词。
- 下表是累计量：size-1 到 size-k 的整段 diff。

| 版本 | size-1 到 | 合计 | 规则源码 | 组织定义 | 其余 |
|---|---|---|---|---|---|
| 1.x | 2 | 13 文件 19 @@ +462 −4 | 2 文件 4 @@ +18 −3 | 5 文件 7 @@ +105 −1 | 8 文件 8 @@ +339 −0 |
| 1.x | 4 | 25 文件 31 @@ +1356 −4 | 2 文件 4 @@ +36 −3 | 5 文件 7 @@ +303 −1 | 20 文件 20 @@ +1017 −0 |
| 1.x | 8 | 49 文件 55 @@ +3144 −4 | 2 文件 4 @@ +72 −3 | 5 文件 7 @@ +699 −1 | 44 文件 44 @@ +2373 −0 |
| 1.x | 16 | 97 文件 103 @@ +6720 −4 | 2 文件 4 @@ +144 −3 | 5 文件 7 @@ +1491 −1 | 92 文件 92 @@ +5085 −0 |
| 2.0 | 2 | 1 文件 1 @@ +26 | 0 | 1 文件 +11（@@ 归给了其余） | 1 文件 1 @@ +15 |
| 2.0 | 4 | 1 文件 1 @@ +78 | 0 | +33 | +45 |
| 2.0 | 8 | 1 文件 1 @@ +182 | 0 | +77 | +105 |
| 2.0 | 16 | 1 文件 1 @@ +390 | 0 | +165 | +225 |

- 1.x「其余」全是提示词文件：size-16 是 +5085，每个复制品两份。2.0「其余」全是配置·提示词，即每个子 agent 的 description 和 system_prompt。
- 2.0 的 @@ 恒为 1：所有子 agent 是 `config.yaml` 里连续的一段。@@ 按多数行归类，所以组织那一栏 @@ 记 0。

**订正（2026-11-19，mero #24103 的黑盒核对指出）**：

- 最初版本里，1.x 放大的规则源码是 +16 / +34 / +70 / +142，比黑盒按改动位置重数少 2 行。少的是 `nodes.py:1130` 和 `nodes.py:1292` 两处名单元组的收尾行：`    ):` 和 `    )`。
- `tools/count_1x.py` 原来只认「含角色名的行」和 `agent_name in (` 那一行是规则，收尾行被归进了框架其余。现在改成：规则行后面紧跟的收尾行也算规则。
- 改后是 +18 / +36 / +72 / +144（−3 不变），「其余」相应各少 2 行，和黑盒一致。上表已是改后的数。
- 用改后的脚本重算了 §2.4 的 16 个变更：只有 size-1 的 d 变了。规则源码 +35 → +37，框架其余 +24 → +22，因为 size-1 的 d 把 `== "researcher"` 第一次改成元组，size-2 起元组已在起点里。§2.4、§5 已改，`runs/count-1x/table.tsv` 已重生成。演示二的计数没变。

**1.x 做不到「规则一行不改」**（实测加读代码）：要让新复制的执行者接到活、并且受原有规则管，必须改规则源码。规则源码那一栏不为 0，包括：

- **R01 派单表**：`builder.py` 的 `continue_to_running_research_team`，每个复制品 2 行，size-16 共 +90。不改的话，新 step_type 走不到新节点：路由函数不会返回它的名字。
- **R09 计划修补**：`nodes.py:175`，`step_type == "research"` 改成元组，新的 research 复制品也算。
- **R15 网搜检查**：`nodes.py:1292`，`agent_name == "researcher"` 改成元组。
- **引用提示**：`nodes.py:1130`，同样是按 researcher 名字判断，+18 −1。它只往提示词里加话、不拦，§1 的规则清单里不算规则，但计数脚本把它归进了规则源码。按清单算，size-16 的规则源码是 +126 −2。

这些行的条数随 k 线性增长（每个复制品在每处各加 1 到 2 行），规则的内容不变，只是名单变长。如果一行规则源码都不改，新加的角色就收不到任何派单。

**2.0 规则源码 0 行**：放大只改 `config.yaml`。

**原有规则管不管得到新加的角色**

| 版本 | 规则 | 结论 | 依据 |
|---|---|---|---|
| 1.x | R01 派单 | 管得到，但要先把新角色加进派单表（上表的规则源码） | 实测：size-2/4/8 验收「每步恰好由 step_type 指定的执行者做一次」全过（`runs/accept-1x/`）。size-16 没跑 |
| 1.x | R13 各节点的工具表 | 管得到：复制节点函数时工具表一起复制 | 读代码 |
| 1.x | R15 网搜检查 | 管得到，要改规则源码（元组） | 读代码。用例 D1-1x-2，没跑 |
| 1.x | R16、R17（三个执行节点共用的辅助函数） | 自动管得到：复制品调用同一个函数 | 读代码 |
| 1.x | R19 python_repl 开关 | 自动管得到：开关在工具里 | 读代码 |
| 1.x | R14 MCP 按名字给工具 | 不自动：新名字要写进请求或配置的 `add_to_agents` | 读代码 |
| 1.x | R22 整次运行的步数上限 | 管得到，但上限不随规模放大。每多一步约多 2 个超步（执行者和 research_team 来回各一次），服务端默认 25。估计 size-4（12 步）就会撞上 | 读代码推算，没实测（用例 D1-1x-4）。我的验收用的是 1000 |
| 2.0 | V01 禁止嵌套、V02 派单预检、V05–V08（工具表、max_turns、timeout、token 预算的默认值） | 自动管得到：判断代码不点名，新子 agent 一注册就适用 | 放行实测：size-8 上限 1000 时 24 个子 agent 全跑、没有子 agent 派单（`runs/accept-v2/size-8.txt`）。拒绝（新子 agent 想再派单）只读了代码，用例 D1-v2-3 没跑 |
| 2.0 | V09 加 V18 | 管得到，并且会限住新角色：默认值下 lead 一次运行派到约 18 个子 agent 就停 | 实测，size-8 上限 100（`runs/accept-v2/size-8.rl100.txt`）。size-16 要 48 个，估计约 260 步，上限 1000 够，没跑 |
| 2.0 | V09 每次运行最多派的子 agent 数 | 上限写死 50（`subagents_config.py:15`，`:198` 的 `le=`），配置调不上去。size-17 起（51 个）必须改框架代码，否则一次运行派不完 | 读代码 |

### 6.2 演示二：嵌套（实测计数）

在 1 倍的组织上，researcher 从执行者变成领导，带 3 个新手下 `researcher_helper_1..3`。手下和 researcher 同一种角色。

- **1.x**（`tools/gen_1x.py change nest 1`，分支 `size-1/nest` = `4bba848`）：
  - `researcher_node` 改成领导：拿当前没做完的 research 步，交给第 (已做完的 research 步数 mod 3) + 1 个手下；手下做完回到 researcher，researcher 再回 research_team。
  - 三个手下是原 researcher 节点函数的副本，调用时仍用 agent_name `"researcher"`。所以按名字判断的规则（R15、R09、引用提示）、工具表（R13）、模型表、提示词都和 researcher 一样，**不用改一行规则源码**。
  - 框架其余：`_execute_agent_step` 和 `_setup_and_execute_agent_step` 加一个参数 `report_to`，原来写死的 3 处 `goto="research_team"` 改成 `goto=report_to`。
  - R01 派单表不变：research_team 照旧只派给 researcher。
  - 静态检查（实测，只建图、不跑）：图里新增 researcher→三个手下、手下→researcher 的边；research_team 到手下没有边。
- **2.0**（`tools/gen_v2.py change nest 1`，分支 `size-1/nest` = `028fe9d4e`）：
  - **2.0 禁止嵌套，要改框架**，和变更 c 同一处最小改动，4 个文件：
    - `config/subagents_config.py`：`CustomSubagentConfig.allowed_subagents` 字段，+4；
    - `subagents/config.py`：`SubagentConfig.allowed_subagents`，+1；
    - `subagents/registry.py`：照抄一行，+1；
    - `tools/builtins/task_tool.py`：给声明了名单的子 agent 组装 task 工具，+1 −1；子 agent 调 task 时只许派给自己的名单，+3，算规则源码。
  - 配置：
    - researcher 的工具表加 `task`，并加 `allowed_subagents`（三个手下）。还要加 `disallowed_tools: [ask_clarification, present_files]`，因为自定义子 agent 默认禁用表里有 `task`（`subagents_config.py:145-148`），不覆盖就拿不到 task 工具。这一点我第一次漏了，读代码发现后重建了分支。
    - 三个手下各一段，description、提示词正文、工具表和 researcher 一样。
    - 自定义 lead `research-lead` 的名单只有 researcher、analyst、coder，lead 不能直接派给手下。

| 版本 | 合计 | 规则源码 | 组织定义 | 其余 |
|---|---|---|---|---|
| 1.x | 3 文件 18 @@ +139 −15 | +11（researcher 领导的派单判断，含 5 行文档字符串；@@ 归给了组织） | 3 文件 16 @@ +126 −13（三个手下节点 +104 左右；签名和 goto 行；builder、utils 名单各 +3） | 1 文件 2 @@ +2 −2（import、传参） |
| 2.0 | 6 文件 7 @@ +50 −1 | 1 文件 1 @@ +3（task 工具的名单限制） | 2 文件 2 @@ +24（配置·组织：键、工具表、禁用表、名单，research-lead 的名单） | 6 文件 4 @@ +23 −1（框架 +7 −1，配置·提示词 +16） |

- 命令：`python3 -I tools/count_1x.py modified size-1 size-1/nest runs/demo2/1x-nest.hunks.tsv`；`python3 -I tools/count_v2.py v2-modified size-1 size-1/nest runs/demo2/v2-nest.hunks.tsv`。
- `count_1x.py` 为此加了两处：`researcher_helper_N_node` 算执行节点（组织）；分支里 researcher 是领导时，它函数体里新增的非签名、非 goto 行算规则。重算 size-2/8 的放大计数，和改前一样。
- 规则源码的对照：1.x +11，即领导自己的派单判断，手下套用 researcher 的规则不用改；2.0 +3，即嵌套必需的名单限制。两边都没有为手下改原有规则。

**验收要点**：都写进了用例表 `runs/demo-cases/cases.tsv`，一条都**没跑**（等 mero 排队）。

- 1.x：
  - 领导能派给手下：D2-1x-1。
  - research_team 越级派给手下被拒：D2-1x-2，条件边的名单不认，同变更 c 的测法。
  - 手下受 researcher 的规则管：放行看 D2-1x-3，工具表相同；拒绝看 D2-1x-5（没有 python_repl）和 D2-1x-4（R15 只加警告、不拦）。
  - **1.x 做不到的一条**（读代码，`venvs/v1` 里 langgraph 1.0.4 的 `graph/state.py:1265-1291`）：「别的上级不能越过它」只在 research_team 的条件边上成立。任何节点返回 `Command(goto="researcher_helper_1")` 都能直达手下，`Command[Literal[...]]` 标注只用来画图，不拦。这对 §2 的变更 c 也成立：c 只拦住了 research_team 的派单函数。
- 2.0：
  - 领导能派给手下：D2-v2-1。
  - lead 越级派给手下被拒：D2-v2-2，靠 `research-lead` 的名单。
  - 手下受 researcher 的规则管：放行看 D2-v2-4（网搜），拒绝看 D2-v2-5（手下不能再派）和 D2-v2-6（researcher 只能派给自己的手下）。
  - **2.0 做不到的一条**：走嵌入式客户端时 lead 能越级（D2-v2-3），同 §4.5 的实测；默认 lead（不用 `research-lead`）也能直接派给手下。

**c 和演示二共用的框架改动有两个缺口**（自动安全审查指出，我读代码核对过，没改分支）：

1. `batch_task` 工具没设同样的限制：
   - 子 agent 一旦 `subagent_enabled`，就能拿到 `batch_task`（`tools/tools.py:256-262`，批处理运行时可用时）。`batch_task_tool.py:218-222` 只看 lead 传下来的 `allowed_subagents`，不看调用者自己的名单。
   - 我的配置里，组长和 researcher 的工具表是显式列的（只有 `task` 等），V05 会把 `batch_task` 滤掉，所以这次的 c 和嵌套碰不到它。
   - 但如果某个子 agent 声明了 `allowed_subagents`、工具表却留空（继承全部），它就能用 `batch_task` 派给名单外的任何子 agent。
   - 完整的改动应该在 `batch_task_tool.py` 加同样的约 3 行。这些行不在 §4.4 和 §6.2 的计数里，所以那里的「最小改动」偏小。
2. 子 agent 的名单不和上一级的名单取交集：lead 的 `allowed_subagents` 管不到下一层派给谁。这是有意的，嵌套就是要让 researcher 派给 lead 名单外的手下。但这也意味着，上级的名单只管一层。

**演示二验收状态（2026-11-19）**：验收脚本已写好，都没跑：

- `tools/accept_1x.py nest`、`tools/accept_v2.py nest`，以及一次一个进程的 `tools/run_nest.sh`（含在 size-1 起点上的反跑）。
- 仓主改成更简单的实验，mero #24339 取消了嵌套验收的队列，所以没跑。分支和数据都留着。
- §6.2 的计数是实测；验收要点只在用例表里，没有实测结果。

## 7 简化实验：格点 T(k, m)（mero #24380；只建树和提交，没跑验收）

- k = 新加的角色种类数（kind1..kindk），m = 管到全部角色、包括新角色的按角色规则族数。每个格点一个分支，都从标签 `size-1` 出发；T(0,0) 就是 `size-1`。
- 生成 `tools/gen_grid2.py`，建分支 `tools/build_grid2.sh`。行数由 mero 统一从 git 数，这里不报。
- 1.x：仓 `deerflow/modified`，分支 `df1-grid2-k{0,1,2,4,8}-m{0,1}`，10 个。
- 2.0：仓 `deerflow/v2-modified`，分支 `df2-grid2-k{0,1,2,4,8}-m{0,1,2,4}`，20 个。

**新角色怎么加**（原生做法，挂在同一个上级下）：
- 1.x 同变更 a，每个 kind 一套：
  - StepType 一个值、节点函数一个（无工具）、research_team 派单表一个分支、`add_node`、条件边名单、`AGENT_LLM_MAP`、发言人名单；
  - 中英两份提示词文件，planner 提示词各一行。
- 2.0：`config.yaml` 的 `custom_agents` 里一段，有自己的 description、提示词、空工具表。

**规则族**：

| 版本 | 第几族 | 规则 | 原生还是我们写的 | 每个角色自己的取值 |
|---|---|---|---|---|
| 1.x | 1 | 限写：每个节点只能写表里给它的状态键，其余 `PermissionError`（§2.2 的变更 b） | 我写的，size-1 到 8 都验收过 | 表里一行；执行者都是同一组键 |
| 2.0 | 1 | `write_paths`：文件写入只许在自己目录下（§4.3 的变更 b） | 我写的（框架代码 +44 行，只加一次），验收过一放一拒 | `/mnt/user-data/outputs/<名字>` |
| 2.0 | 2 | `max_turns`（V06） | 原生，自定义子 agent 的字段 | researcher 40、analyst 20、coder 30、kind_i 20+i |
| 2.0 | 3 | `timeout_seconds`（V07） | 原生，同上 | 900 / 600 / 1200 / 600+30i |
| 2.0 | 4 | `token_budget`（V08） | 原生，但写在另一段 `subagents.agents.<名字>.token_budget`（`get_token_budget_for` 对自定义子 agent 也生效，`subagents_config.py:299-320`） | 400000 / 200000 / 300000 / 100000+10000i |

- 核对：T(0,1) 两个版本都和已验收的 `size-1/b` 逐字节相同（`git diff` 为空）。
- 静态核对（实测，没跑验收）：
  - 1.x 的 `df1-grid2-k8-m1` 能建图：19 个节点；research_team 能到 planner、3 个执行者、8 个 kind；限写表 17 行。
  - 2.0 的 `config.yaml` 用上游的 `SubagentsAppConfig` 解析能过；`df2-grid2-k8-m4` 的 kind8 token 预算解析为 180000，researcher 的 max_turns 为 40。

**做不到的档和原因**：
- 1.x m = 2、4、8：只有限写这一族能管到全部角色。原生的按角色规则都不行：
  - R13 工具表是节点定义的一部分，去不掉，也不算「另加的一族」；
  - R15 只点 researcher；
  - R14 MCP 按名字给工具，名字在运行请求或运行时配置里，不在仓里；
  - 其余都是全局规则。
  - 再加就得新造规则，按要求不做。
- 2.0 m = 8：能用的只有 4 族。2.0 原生「按角色名取参数」的 6 条（V03–V08）里能用 3 条（V06、V07、V08）：
  - V03 是自定义 lead 的名单，只管 lead；
  - V04 只点 bash；
  - V05 工具表是角色定义的一部分，每个格点都带着，和 1.x 的 R13 一样当原生去不掉的规则。

**T(0,0) 里原生去不掉的**：
- 1.x：R13（各执行节点自带工具表），R15（researcher 的网搜检查），R01（按 step_type 派单，兼做组织）。
- 2.0：V05（`size-1` 的三个子 agent 都写了工具表）。另外 max_turns 默认 50、timeout 默认 900、token 预算默认开（200 万）对每个自定义子 agent 都生效，但所有角色同一个值，不算按角色。

**用例**（一放一拒，没跑）：`runs/grid2/cases-df1.tsv` 16 条（8 个 kind × 1 族 × 2），`runs/grid2/cases-df2.tsv` 64 条（8 × 4 × 2）。`applies_to` 列写明在哪些格点上适用。

**这个系统在实验里的特殊点**：
- 1.x 加一个角色本身就要改规则源码（R01 派单表加一个分支）。限写表每个节点一行，所以规则代码也随 k 长。
- 2.0 加角色和三族原生规则都只改 `config.yaml`；只有我们写的那一族要一次性的框架代码。token 预算不写在角色那段里，而在另一处按名字再写一遍。
- 静态核对时看到：上游的配置模型不认识的键直接忽略、不报错。上游代码读带 `write_paths` 的配置照样能过。所以规则键写错一个字母，规则就悄悄没了。

## 8 最终实验 grid3：模拟规则（mero #24557，`_scale/GRID3-模拟规则.md`；只建树、提交、写用例，没跑验收）

- 仓库和分支，每个都从标签 `size-1` 出发；T(0,0) 就是 `size-1`：
  - 1.x：`deerflow/modified`，`df1-grid3-k{0,1,2,4,8}-m{0,1,2,4,8}`，25 个。
  - 2.0：`deerflow/v2-modified`，`df2-grid3-k{0,1,2,4,8}-m{0,1,2,4,8}`，25 个。
- 生成 `tools/gen_grid3.py`，建分支 `tools/build_grid3.sh`。用例 `runs/grid3/cases-df1.tsv`、`cases-df2.tsv`，每条规则一放一拒，各 16 条，没跑。

**扩的角色**：两版都挑 researcher（研究步骤最容易变多）。复制品叫 `researcher_2` 到 `researcher_{k+1}`。

- 1.x：每个复制品要一个节点函数（researcher 节点的副本，调用时仍用 agent 类型 `"researcher"`，所以提示词、模型表、按 researcher 判断的检查都和原来一样）、一个 StepType、派单表一个分支、`add_node`、条件边名单、发言人名单，planner 提示词中英各一行。planner 可以把步骤单独派给某个复制品。
- 2.0：原生不改文件时只能「运行时多起几个、共用一个名字」：lead 对同一个类型多次调 task。要各有名字，最小改动是用原生做法在 `config.yaml` 里每个复制品写一段：researcher 那段原样复制、只换键名，提示词仍写 `researcher`。

**接龙行在两个系统里走哪几段交接**（接手的一方检查；不合格就拒绝，报错不往下走）：

| 交接 | 1.x | 2.0 |
|---|---|---|
| 派单（上级交给下级） | research_team 交给执行者。文本是那一步的 description；research_team 是代码节点，由它的代码把接龙行接在 description 末尾。执行者在共用的 `_execute_agent_step` 开头检查 | lead 交给子 agent。文本是 task 的 prompt，由 lead 的模型写接龙行。在 task 工具里、子 agent 开始之前检查 |
| 交回（下级交给上级） | 执行者交给 research_team。文本是这一步的结果（execution_res），由执行者的模型写。research_team 节点检查；交回的是谁，取 LangGraph 给节点的名字（`langgraph_node`），由执行者在状态里记下 | 子 agent 交给 lead。文本是子 agent 的结果，由子 agent 的模型写。task 工具在 COMPLETED 时检查 |
| 上级往上交（R4 用） | research_team 交给 planner。research_team 没有自己的文本，用新状态字段 `relay_up` 装一行，由 research_team 的代码写；planner 开头检查 | lead 交给用户，即最终回答。系统里没有接手的一方，所以**在交出那一步检查**：模型调用之后的中间件 |

**每条规则写在哪、照的哪段原代码**：两版都是一个检查函数 `check_relay` 加三个调用点。函数在 1.x 的 `src/graph/relay.py`、2.0 的 `subagents/relay.py`。m 条规则就只生成那 m 段。

| 位置 | 1.x（照的原代码，`2ab2876`） | 2.0（照的原代码，`e0cccd6`） |
|---|---|---|
| 派单的检查 | `_execute_agent_step` 里 R15 网搜检查的写法（`nodes.py:1290-1310`，三个执行节点共用） | task 工具的预检拒绝（`task_tool.py:961-973`：不合格就返回 `result_command(status="failed")`） |
| 交回的检查 | 写在 `research_team_node`（`nodes.py:957-961`，原来是空节点）里；派单行像执行者原地写 `step.execution_res` 那样原地接在 step 上（`nodes.py:1313`） | task 工具 COMPLETED 分支，紧跟收据核对的位置（`task_tool.py:1269-1282`） |
| 往上交的检查 | `planner_node` 开头（`nodes.py:274` 一带，同 R02 的计数检查位置） | 新中间件 `RelayHandUpMiddleware`，照 `SubagentLimitMiddleware.after_model`（`subagent_limit_middleware.py:134-190`），挂在它后面（`agent.py:721`） |
| R4 的直接下级名单 | `src/config/agents.py` 的 `RESEARCH_TEAM_MEMBERS`，照发言人名单（`utils.py:6-13`）一个节点一行 | 运行时从 `config.yaml` 的 custom_agents 取，不用另写 |
| R5 每种角色的词 | `src/config/agents.py` 的 `AGENT_RELAY_KEY`，照 `AGENT_LLM_MAP`（`agents.py:10-21`），按 agent 类型取，所以复制品不用加 | 子 agent 字段 `relay_key`，照 `timeout_seconds`（`subagents_config.py:170-174`）、`SubagentConfig.max_turns`（`config.py:54`）、注册表（`registry.py:54`）；两个内置子 agent 各加一行；`config.yaml` 每个子 agent 一行，复制品也要 |

- **全局一次**：R1、R2、R3、R6、R7、R8 的判断都在 `check_relay` 里写一次，管到所有角色，复制品不用另接。
- **按角色接的**：
  - R4：1.x 每个执行节点在名单里一行；2.0 不用。
  - R5：1.x 每种角色一行，复制品不用；2.0 每个子 agent 一行，复制品也要，因为 2.0 没有「种类」，复制品就是另一个子 agent。

**做不到或不会触发的**：
- R7（n ≤ 9）：两版都是两层，每段派单链最多 n=2，加复制品也不会把链拉长，N 在所有格点都是 9 不用改。所以 R7 在合法流程里永远不会触发。拒绝用例只能人为写 n=10。检查放在 R3 之前，这样报的是 R7。
- R4 在 2.0 是在交出那一步检查，上面已写明。
- R4 在 1.x 的往上交，用的是新状态字段，不是原生文本。

**特殊点**：
- 写接龙行的一方：代码节点（1.x 的 research_team）由代码写；模型（执行者、lead、子 agent）由模型写，**我没有加提示模型怎么写的话**。所以真模型跑 m ≥ 1 的格点会全被拒；验收用假模型直接写对或写错的行，只看检查拦不拦，符合定义里「不看模型会不会写」。
- 没检查的交接：
  - 1.x 执行者出错时交回的错误文本，以及递归上限回退的结果，不经过检查（没记交回者）；
  - 2.0 只检查 COMPLETED 的结果，FAILED 和 TIMED_OUT 不检查。
- 2.0 的 R4 直接下级取的是 config.yaml 里的执行组，不含内置的 general-purpose 和 bash：它们是按需调的通用助手。如果要算进去，lead 每次运行都得派它们一次。
- 静态核对（实测，没跑验收）：
  - 1.x 和 2.0 各取 5 个格点，改过的 .py 都能编译。
  - 1.x `df1-grid3-k8-m8` 能建图，research_team 能到 researcher 和 8 个复制品；R4 名单 11 个，R5 词表 4 个。
  - 2.0 `df2-grid3-k8-m8` 的 config.yaml 用分支自己的代码解析，11 个子 agent 的 relay_key 是 blue/green/red；task 工具、新中间件、lead agent 都能导入。
  - `check_relay` 用 6 组手写的行试过：合格的放行，R1/R4/R6/R7 不合格的拒绝。

### 8.1 先扩，再改（mero #24719；只改、只提交，没跑）

- 分支：`df1-grid3-k{0,1,2,4,8}-m0-change`（modified）、`df2-grid3-k{0,1,2,4,8}-m0-change`（v2-modified），各从对应的 `-m0` 出发。脚本 `tools/build_grid3_change.sh`。
- **1.x**：用原生规则 R13（各执行节点自带的工具表）。researcher 和它的 k 个复制品都去掉 `crawl_tool`，只留网搜。
  - 工具表写在每个节点函数里，复制品是函数副本，所以**每个名字各改一遍**。k=8 时改 9 处，1 个文件，+9 −9。
  - 同一种角色共用的值（按 agent 类型 `"researcher"` 取的模型表、R15）只要改一次，但它们不是工具或轮数这类限制。
- **2.0**：用原生规则 V06（每个自定义子 agent 的 `max_turns`）。researcher 和复制品从默认 50 改成 25。
  - 2.0 没有「种类」，复制品是各自独立的一段配置，所以**每个名字各写一遍**。k=8 时改 9 处，1 个文件（`config.yaml`），+9。
  - YAML 的锚点和别名能让多段共用一份值，但上游文档和示例没用这种写法，我没用。
- 两版都没用到我们自己写的那一族，原生规则就够了。

### 8.2 只加执行者时动了几行规则源码（mero #24894，实测计数）

`python3 -I tools/count_1x.py modified df1-grid3-k0-m0 df1-grid3-k<k>-m0 runs/grid3-count/df1-k<k>-m0.hunks.tsv`

| k | 合计 | 规则源码 | 组织定义 | 提示词文件 | 框架其余、配置 |
|---|---|---|---|---|---|
| 1 | 6 文件 9 @@ +60 −1 | +2（1 @@） | +54 −1（4 文件 6 @@） | +4（2 文件 2 @@） | 0 |
| 2 | 6 / 9 / +114 −1 | +4 | +102 −1 | +8 | 0 |
| 4 | 6 / 9 / +222 −1 | +8 | +198 −1 | +16 | 0 |
| 8 | 6 / 9 / +438 −1 | +16 | +390 −1 | +32 | 0 |

- 规则源码全是 R01 派单表（`builder.py` 的 `continue_to_running_research_team`），每个复制品 2 行：`if step_type == ...: return "researcher_N"`。
- 和 §6.1 的 +18 / +36 / +72 / +144 不同的原因：那里复制的是整个执行组，复制品各有自己的 agent 名字，所以 R09、R15 和引用提示的名单元组也要加长。grid3 的复制品仍以 agent 类型 `"researcher"` 运行，这些按名字判断的检查自动管到，不用改。
- 组织定义：节点函数副本（每个约 45 行）、StepType、`add_node`、条件边名单、发言人名单。提示词：planner 提示词中英各一行；复制品共用 researcher 的提示词文件，所以没有新提示词文件。

### 8.3 grid3 验收（mero #24931，实测；一次一个进程，先 2.0 后 1.x）

- 脚本：
  - 2.0：`tools/accept_grid3_v2.py`（Gateway 的 `make_lead_agent` + 假模型；假模型加了 loop、suffix、pad、task_suffix 几种计划），由 `tools/run_grid3_v2.sh` 跑。
  - 1.x：`tools/accept_grid3_1x.py`（真图 + 假模型），由 `tools/run_grid3_1x.sh` 跑。
- 结果文件 `runs/accept-grid3/`。每个文件第一行是提交号。

| 版本 | 项 | 格点 | 结果 | 反跑 | 反跑结果 |
|---|---|---|---|---|---|
| 2.0 | 1 复制品接活、原生规则生效 | k8-m0 | 4/4 过：researcher_9 接到并交回；V05 给了它自己的工具（web_search、web_fetch），没给 bash、write_file、task（V05、V01）；V02 拒绝没声明的 researcher_10 | k0-m0 | 3 条不过（researcher_9 不存在，「Unknown subagent type」），V02 那条照样过（它在哪都成立） |
| 2.0 | 2 改后的值（max_turns 25） | k8-m0-change | 4/4 过：researcher 和 researcher_9 要 10 次工具调用都做完；要 40 次都在 25 次时被停（「Task failed (capped: turn budget)」） | k8-m0 | 2 条拒绝不过（默认 50，40 次都做完），2 条放行照样过 |
| 2.0 | 3 cases-df2 | k8-m8 | 16/16 过：8 条放行共用一次合格的运行；8 条拒绝各报 `relay R1`…`relay R8`。R4 在 lead 的最终回答处拒（`RuntimeError`），其余是 task 工具返回 `Task failed. Error: relay R…` | — | — |
| 1.x | 1 复制品接活、原生规则生效 | k8-m0 | 5/5 过：researcher_9 接到 research_9 步并做完；R13 工具表（crawl_tool、web_search），没有 python_repl_tool；R15 警告也加到它身上；R07 拒绝没声明的 research_10 | k0-m0 | 4 条不过，R07 那条照样过 |
| 1.x | 2 改后的值（去掉 crawl_tool） | k8-m0-change | 4/4 过：researcher 和 researcher_9 都只剩 web_search | k8-m0 | 2 条拒绝不过（crawl_tool 还在），2 条放行照样过 |
| 1.x | 3 cases-df1 | k8-m8 | 第一次 8/16：8 条放行全不过，都是 `relay R4: heard misses ['researcher_9']`。修正后 16/16 过 | — | — |

**1.x 规则代码的一处错（验收查出来的，已改）**：
- 现象：research_team 写往上交的那一行时，`heard` 用的是这次交回之前的名单，最后一个交回的执行者总是漏掉，所以合格的流程也被 R4 拒绝。拒绝用例「漏掉 researcher_9」报的是漏 researcher_8 和 researcher_9，也是同一个原因。
- 改法：`gen_grid3.py` 里那一行改成先取本次更新后的名单。重建了 1.x 的 10 个分支（`df1-grid3-k{0,1,2,4,8}-m{4,8}`），每个分支相对旧提交只改这 1 行（+1 −1），相对 `size-1` 的行数和分栏都不变，但提交号变了。
- 重跑 k8-m8 的 cases，16/16 过。第一次的输出留在 `df1-cases.before-heard-fix.txt`。
- 2.0 没有这个问题：它的 R4 下级名单是从配置取的，heard 由模型写。

## 9 deer-flow 的 Sherpa 对应物（mero #25011；只为 grid3 的 (a) 加执行者、(d) 先扩再改）

- **仓**：`deerflow/sherpa_eq`，本地克隆自 `_scale/sherpa/modified`，push 地址设成 `no_push`。
  - 起点 `eq-base` = 标签 `sizec-base`（已带「位置的类」的编译器改动），加上从 `_pairing/packs/` 原样拷进来的 `seat_tool_allowlist`、`tool_call_limit` 两个包。
  - 不新写规则包，不改内核和编译器。
- **生成和建分支**：`tools/gen_eq.py`、`tools/build_eq.sh`。分支 `df1-eq-grid3-k{0,1,2,4,8}-m0` 和 `-m0-change`、`df2-eq-grid3-…`，共 20 个。
- **组织**（和 1 倍的树同样的角色、同样的谁带谁）：
  - 1.x，工作流 `PPOtestDeerflow1`：human（扮引擎）带 coordinator、planner、reporter、research_team；research_team 带 researcher、analyst、coder。
  - 2.0，工作流 `PPOtestDeerflow2`：human 带 lead；lead 带 researcher、analyst、coder、general_purpose。
  - researcher 和它的复制品 `researcher_2..` 归一个类 `researcher_role`，共用一张卡。类名不能和位置同名（编译器规定），所以类名都带 `_role`（占位名）。
- **规则**：
  - 基础包：base、classic_lifecycle（上下级、派单配对），加上跑用例要的 git、worktree、task_card。
  - (d) 那条原生规则的对应物，按类写值：

| 版本 | 原系统 (d) 改的 | 对应物 | 起点的值 | -change 的值 |
|---|---|---|---|---|
| 1.x | R13 节点工具表 | `seat_tool_allowlist` | `researcher_role=web_search,crawl_tool;analyst_role=-;coder_role=python_repl_tool` | researcher_role 去掉 crawl_tool |
| 2.0 | V06 max_turns | `tool_call_limit` | `researcher_role=50;analyst_role=50;coder_role=50;general_purpose=150`（2.0 的默认值） | researcher_role=25 |

- 2.0 一侧也装了 `seat_tool_allowlist`，因为 `tool_call_limit` 依赖它的工具台账。它没有 params，什么都不限。

**行数**（`git diff --shortstat`，实测）：
- 每加一个位置 9 行（instance 6 行含空行、seat 3 行），全在工作流文件里，**其中规则参数 0 行**。两版一样：k=1 是 +9，k=8 是 +72。
- (d) 在 k=8 时改 **1 处**（类的那一个值，+1 −1）。原系统两版都是 9 处。

**用例和结果**（`run_table.py`，一次一个进程，实测）：表在 `sherpa_eq_tests/`，结果在 `runs/eq/<版本>_<表>_on_<分支>/cases.results.tsv`。

| 表 | 对应原系统 | 在目标分支上 | 反跑 | 反跑结果 |
|---|---|---|---|---|
| df1_a（4 条） | 1.x (a)：researcher_9 接到步骤；R13 放行它的工具、拒 python_repl；R07 拒没声明的 research_10 | k8-m0：4/4 对上（拒绝红码 `seat_tool_allowlist.tool_not_allowed`、`classic_lifecycle.not_your_lower`） | k0-m0 | 3 条对不上（researcher_9 不存在），拒 researcher_10 那条照样对 |
| df1_d（4 条） | 1.x (d)：researcher、researcher_9 留 web_search、不再有 crawl_tool | k8-m0-change：4/4 | k8-m0 | 2 条拒绝对不上 |
| df2_a（6 条） | 2.0 (a)：researcher_9 接到任务、报告交回；V02 拒 researcher_10；V01 子 agent 不能再派；V06 对它生效（第 51 次被拒） | k8-m0：6/6（`classic_lifecycle.not_your_lower`、`tool_call_limit.reached`） | k0-m0 | 5 条对不上，拒 researcher_10 那条照样对 |
| df2_d（4 条） | 2.0 (d)：researcher、researcher_9 做 10 次以上照常，第 26 次被拒 | k8-m0-change：4/4 | k8-m0 | 2 条拒绝对不上（上限 50） |

**和原系统对不上的地方**：
- 1.x 的 R15（researcher 没用网搜就加警告）没有对应物：它只加警告、不拦，不属于这两类规则。原系统 (a) 的那一条没有翻。
- 2.0 的 V05 工具表（复制品拿到 web_search、web_fetch，拿不到 bash、write_file、task）没装对应物。mero 只要两类规则，所以 df2_a 不查工具名。V01（子 agent 不能再派）由上下级配对管：复制品没有下级。
- 2.0 的 max_turns 数的是「轮」（一次模型调用），`tool_call_limit` 数的是放行的工具调用次数。一轮一次工具调用时两者相同；一轮多次调用时，Sherpa 一侧更早到上限。原系统撞到上限是强制收尾、交回一个带标记的失败，Sherpa 是拒绝下一次工具调用。
- 1.x 的工具名（web_search、crawl_tool、python_repl_tool）在 Sherpa 里只是 `sherpa tool-call --tool` 的字符串，没有真的工具。用例按钩子的方式敲，不起模型。
- 原系统的复制品在派单链里由 research_team（1.x，代码）或 lead（2.0，模型）派；Sherpa 一侧由坐在 research_team、lead 位置上的 agent 派。1.x 的「planner 写计划、research_team 按 step_type 派」这个顺序没有搬：只有 (a)、(d) 用，按要求越小越好。

### 9.1 用 `copies = k` 重做 (a)（mero #25117；实测）

- 起点 `eqn-base` = `_scale/sherpa/modified` 的分支 `seat-copies`（76ff788，编译器认 `[[instance]] copies = N`），加上和 `eq-base` 同样拷来的两个包。
- 分支 `df1-eqn-grid3-k{0,1,2,4,8}-m0`、`df2-eqn-grid3-k{0,1,2,4,8}-m0`，`tools/gen_eq.py <tree> <版本> 0 --copies k`。k0 的工作流文件和原写法的 `-eq-grid3-k0-m0` 相同。
- **新增行数**：每个 k 都是 **1 行**，即 researcher 那条 `[[instance]]` 上的 `copies = k`，两版一样。不用补规则参数行：(d) 那条规则按类写值，展开出来的位置照抄 researcher 的类，自动管到。原写法每个位置 9 行，k=8 是 +72。
- **用例**：在 k=8 上重跑原来 (a) 的表。展开出来的位置名正好是 `researcher_2..researcher_9`，用例不用改。df1_a 4/4 对上，df2_a 6/6 对上，红码和原写法相同。结果在 `runs/eqn/`。
- **和逐个写位置比，做不到或没验的**：
  - 名字只能是 `<原名>_2..<原名>_{N+1}`，不能自己起。deer-flow 的复制品名正好是这个样子。
  - 不能只拿掉中间的一个（比如 researcher_5），只能减 N，从尾巴上去掉。
  - 复制品和原来那个同一个上级。读代码看，给某一个复制品单独设值，可以在 params 里按它的位置名再写一项（编译器规定位置自己的项优先），但我没验。
  - 工作流文件里看不到逐个的位置名，审阅的人要知道展开规则。
  - 对照原系统：1.x 每个复制品要一个节点函数和若干名单项，2.0 要一段配置；两者都没有这种「写一个数」的办法。

## 10 汇报线规则 grid4 和两族形式规则 grid5（mero #25571、#25667、#25753；实测）

**grid4**（生成器 `tools/gen_grid4.py`，分支 `df1-grid3-k{0,1,2,4,8}-p`、`df2-grid3-k{0,1,2,4,8}-p`）：

- **1.x**：上级取组织图上的上级，从图的条件边读出来（`builder.branches`：接到这个节点的那条边的起点，即 research_team），不读派发人。依据：1.x 里任何节点返回 `Command(goto=执行者)` 都能直达执行者，所以「只有上级能派活」没有被强制。
  - P1：builder 里每个执行节点套一层 `_report_line` 包装，交回的 goto 不是上级就拒（`PermissionError`）。包装的写法照我们的限写（变更 b 的 `_limit_writes`），上游没有包装节点的先例。
  - P2：在 `research_team_node` 核对落款，交回者由包装记在状态里。
  - 行数（相对 -m0）：k0 +39−4，每多一个执行者 +1−1（它那行 add_node 改成套包装）。
- **2.0**：派发人就是上级。只有 lead 拿得到 task 工具（V01：子 agent 不能再派；V03：自定义 lead 的名单），结果只经 task 调用回到调用方。
  - P1 结构上成立，不写代码。
  - P2 在 task 工具的 COMPLETED 分支，拿 subagent_type 核对落款。
  - 每个 k 都是 +5，每多一个执行者 0 行。
- **「谁是谁的上级」写在几处**（k=0）：
  - 1.x：规则 1 处（读图）；组织里条件边名单 1 处、执行节点返回类型 3 处（每加一个执行者 +1）、共用函数里写死的 goto 3 处、辅助函数返回类型 2 处；提示词里 3 个执行者各一句「managed by supervisor」（中英文都有）；配置 0。
  - 2.0：规则 0 处；配置只有用自定义 lead 时的 allowed_subagents；提示词 0。
- **验收**（结果在 `runs/accept-grid4/`）：

| 版本 | 1 新执行者交给上级、落款对 | 2 交给非上级 | 3 落款写别人 | 4 原执行者 | 反跑 -m0 |
|---|---|---|---|---|---|
| 1.x k8-p | 过 | 拒（`report line P1: researcher_9 handed back to 'planner'`） | 拒（P2） | 过 | 第 2、3 条对不上（被禁的交回通过了），第 1、4 条照样过 |
| 2.0 k8-p | 过 | 不适用：子 agent 指定不了接收方 | 拒（P2） | 过 | 第 3 条对不上，第 1、4 条照样过 |

**grid5**（生成器 `tools/gen_grid5.py`，分支 `df?-g5-k0-{g,n}{1,2,4,8}`、`df?-g5-k{1,2,4,8}-{g,n}{k}`；交接点和查法同 grid3）：

- **通用族**（按 #25753 改成写交出者自己的名字）：两版都是一个循环，规则里没有角色名。
  - 真正的交出者：1.x 取 research_team 或 LangGraph 的节点名；2.0 取 lead 或任务的 subagent_type。
  - 行数不随 m、k 变：1.x 每格 +56−1，2.0 每格 +38。
- **点名族**：
  - 1.x：每条规则一张以 agent 类型为键的表，照 `AGENT_LLM_MAP`（`src/config/agents.py:10-21`），4 项。复制品以类型 researcher 运行，不进表。每多一条规则 +8 行，每多一个执行者 0 行：k0-n1 +65、n2 +73、n4 +89、n8 +121；一起加的格点和同 m 的数相同。
  - 2.0：写在每个子 agent 的配置里，照 `timeout_seconds` 和 grid3 的 `relay_key`。一个 `marks` 字段（框架 3 行，加两个内置子 agent 各 1 行）；config.yaml 每个子 agent 写一行 `marks:`，再每条规则 1 行；lead 的口令是代码常量。
    - 只加规则：k0-n1 +45、n2 +48、n4 +54、n8 +66（每条规则 +3）。
    - 一起加：k1-n1 +47、k2-n2 +54、k4-n4 +74、k8-n8 +138。每多一个执行者多 m+1 行：复制品是另一段配置，口令照抄 researcher 的。
  - 口令表：`python3 -I tools/gen_grid5.py words`。
- **验收**（k8、m8，结果在 `runs/accept-grid5/`）：四棵树全对上：通用族 3/3，点名族 4/4，两版都是。反跑在 grid3-k8-m0 上，通用族 2 条、点名族 3 条对不上（被禁的都通过了），第 1 条照样过。
