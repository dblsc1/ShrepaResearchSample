# 量法一：规则对组织的引用矩阵（第一版，2026-11-18）

> sora 整理。只读文件和 git 对象，不执行被测代码。脚本 `tools/coupling_refmatrix.py`（`python3 -I`，约 30 秒）。
> 输出：每家一张矩阵 `refmatrix_<系统>.tsv`（行是规则，列是组织元素，格子里 `S` = 名字出现在可执行源码里，`C` = 出现在声明或配置里，两者都有写 `CS`；末列是清点自己的点名记录，可对照）；全部匹配逐条 `refmatrix_matches.tsv`（规则、元素、文件、行号、桶，共 358 条）；汇总 `refmatrix_summary.tsv`。
> 这是规则对组织的耦合，和顾问 11-10 量的模块对模块的传播代价不是一回事，配套论文里分开报。

## 一 怎么判「点名」（可复查）

- **可执行源码**（`.py`）：用 `ast` 取字符串常量，去掉文档字符串；常量的值**整串等于**元素名才算。（`.ts/.tsx`：去掉注释后取字符串字面量，整串相等才算。）注释、文档、报错文字里提到角色名不算；变量名不算。
- **声明和配置**（`.toml`、`.tsv`、`.yaml`、`.json`）：去掉 `#` 注释后，元素名作为整词出现就算。
- **ChatDev 的 yaml 按结构判**：节点块里的 `tooling`（工具白名单，C1）、循环计数器的 `max_iterations`（C6）记到该节点；每条边的 `from`、`to` 记到两端节点（C4 顺序；带关键字条件的边另记 C5；进出计数器的边另记 C6）。
- **规则单元和定义位置**：
  - Bernstein：11-17 清点的 80 条（`scripts/rules.tsv` 的位置；`R31` 在 `rules.tsv` 里有位置、报告规则表里没有，按 80 条口径不计）。`::符号` 形式的位置用 `ast` 解析成函数或类的起止行。
  - Paperclip：11-17 清点的 353 条（`final.tsv`，去掉 68 条存疑），位置相对 `server/src/`。有 22 处位置写法解析不了（如「hasCreatePermission at llms.ts:14-18」、只有行号没有文件名的续行），列在矩阵末列 `unresolved_locations`，这几处没参与判定。
  - ChatDev（9 条，C1–C9）、TradingAgents（10 条，R1–R10，R11 存疑不计）：各自 `ORG_AND_RULES.md` 的规则表和「强制它的代码」位置。TradingAgents 的 R4、R5 位置是整个 `agents/tools.py`。
  - Sherpa 一侧（小组和三个等价物）：每个装了的包算一个单元（加内核 `Core/` 一个单元），位置是包目录下的 `.py`、`.tsv`、`.toml`（不含用例），加工作流文件里 `[policy.<包>]` 那一段。组织元素是工作流里的 `[seat.*]`。所以 Sherpa 一侧的规则单元是「包」，比外部几家的「条」粗，见第四节。
- **组织元素**：ChatDev 26 个节点名；TradingAgents 13 个节点名加 5 个分析员选择键（`market` 等；第一版误列了不存在的 `Social Analyst`，11-18 按 zumi 的核对去掉）；Bernstein 起点 `bernstein.yaml` 里的 9 个角色；Paperclip `AGENT_ROLES` 的 12 个角色加 `board`（人类董事会这一类主体）；Sherpa 一侧各工作流的位置。

## 二 结果

| 系统 | 规则单元 | 组织元素 | 有引用的格子 | 密度 | 其中落在可执行源码的格子 | 其中落在声明或配置的格子 | 一条规则平均点名几个元素 | 一个元素平均被几条规则点名 | 点名了元素的规则数 | 被点名的元素数 |
|---|---|---|---|---|---|---|---|---|---|---|
| ChatDev | 9 | 26 | 49（原 58） | 20.9%（原 24.8%） | **0** | **49**（原 58） | 5.44（原 6.44） | 1.88（原 2.23） | 3（C4、C5、C6；原 4，含 C1） | 26 |
| TradingAgents ᵘ | 10 | 18 | 26 | 14.4% | **26** | **0** | 2.60 | 1.44 | 5 | 17 |
| Bernstein | 80 | 9 | 25 | 3.5% | **25** | **0** | 0.31 | 2.78 | 7 | 9 |
| Paperclip | 353 | 13 | 52 | 1.1% | **52** | **0** | 0.15 | 4.00 | 47 | 3（board、ceo、general） |
| Sherpa 小组 | 16 | 4 | 1 | 1.6% | **0** | **1** | 0.06 | 0.25 | 1（base） | 1（human） |
| ChatDev 等价物 | 12 | 10 | 19 | 15.8% | **0** | **19** | 1.58 | 1.90 | 4 | 10 |
| TradingAgents 等价物 | 11 | 14 | 31 | 20.1% | **0** | **31** | 2.82 | 2.21 | 4 | 14 |
| Bernstein 等价物 | 12 | 10 | 11 | 9.2% | **0** | **11** | 0.92 | 1.10 | 4 | 9 |

**重点（源码对声明）**：外部系统里规则对组织的引用，Bernstein、Paperclip、TradingAgents **全部**落在可执行源码里；ChatDev 全部落在 yaml 工作流文件里（它的规则就写在流程里）。Sherpa 一侧**一格源码引用都没有**：包的代码里不出现任何位置名，引用全在声明文件的 `[policy.*]` 参数里，外加 `base` 包的角色表里有 `human` 一行。

点名落在哪些地方（按 `refmatrix_matches.tsv` 归纳）：
- Bernstein：`agent_jwt.py`（R09、R11 按角色发令牌权限）、`permissions.py`（R29 按角色的可写路径表，8 个角色）、`workflow.py`（R37 governed 工作流各阶段的允许角色）、`adapters/claude.py`（R46 按角色的工具白名单）、`task_store_core.py`（R19 只认 manager）、`spawner_core.py`（R20 只认 manager）。
- Paperclip：`board` 42 处、`ceo` 9 处、`general` 1 处，分布在 47 条规则里。
- TradingAgents：`graph/setup.py` 和 `graph/conditional_logic.py` 里边和路由的节点名（R1、R2、R9），`graph/analyst_execution.py` 里分析员键和节点名（R3）。
- ChatDev：C4（顺序）的 54 条边点名了全部 26 个节点；C1 的 9 段工具白名单；C5 的 4 条关键字边；C6 的 5 个计数器和进出它们的边。
- 等价物：`seat_write_limit`、`reopen_limit`、`seat_precedence`、`fixed_order` 的参数按位置名写（例如 `params = "code_reviewer=-;..."`），`must_decompose` 的 `only = ["manager"]`、`parallel_wait_all` 的 `except`。

ᵘ **事后查明并更正**（11-18，统一位置，mero #18843）：TradingAgents 的规则位置按「最小语法单元的完整行范围」改了（zumi #18988）：R7 从两行条件改成两个路由方法的完整体（`conditional_logic.py:12-21,23-33`），R8 `setup.py:73-89`，R9 `setup.py:160-166`，R3 `analyst_execution.py:20-46`，R6 `setup.py:53-90`。路由方法里写着节点名，所以格子从 18 变 26（源码 18 → 26，声明仍 0）。旧行：10 / 18 / 18 / 10.0% / 18 / 0 / 1.80 / 1.00 / 4（R1、R2、R3、R9）/ 16。ChatDev 的源码位置也改了（naga #18960），源码格仍是 0。Bernstein 80 条、Paperclip 353 条用的是 11-17 清点存档的位置，没有按新取法重取；Bernstein 15 条核心规则新旧范围的敏感性检查没有格子变（`_techdoc/40` 第七节）。

## 三 和清点自己的点名记录对照

- **Bernstein**：清点记 9 条点名（R09、R11、R19、R20、R21、R29、R37、R38、R46），我的判定命中其中 7 条。没命中的两条：R21（清点记「点名：manager」）和 R38（「阶段由角色集合定义」）。可能原因是名字不是以整串字符串常量出现（例如经常量或集合间接引用），或清点给的行号范围没覆盖到那一行；没有逐条追。我命中的 7 条里点名的角色和清点一致或是它的子集（R11 我多数到的都在清点列出的 6 个里）。
- **Paperclip**：清点的 `named2` 口径更宽，353 条里 115 条不是 `none`，包括「按具体 agent 的配置」「适配器类型」「成员身份」等；其中和组织元素有关的（`role:`、`actor-type:board`、`reportsTo`、`agentId-in-config`）58 条。我的判定只认角色名和 `board` 的字符串字面量，命中 47 条：`role:ceo` 10 条中命中 9 条；`actor-type:board` 一半左右命中，另一半应是经常量或函数（如 `assertBoard()`）判断、没有字面量；`agentId-in-config`（按具体 agent 的 id 配）一条都没命中，因为 id 不是固定名字。所以按清点口径，Paperclip 点名组织的规则比我数的多。
- ChatDev、TradingAgents、Sherpa 一侧没有逐条点名记录可对照。

## 四 读这张表要知道的，包括对我们不利的

1. **密度不能横比。** 规则单元的粒度差很多：Paperclip 353 条、Bernstein 80 条是逐条清点，ChatDev、TradingAgents 是 9、10 条大规则，Sherpa 一侧是按包。一个包往往对应好几条规则（例如 `seat_write_limit` 一个包对应 ChatDev 的 C1）。粒度越粗密度越高，所以 Sherpa 等价物 9%–20% 的密度比 Bernstein 3.5%、Paperclip 1.1% 高，**不说明等价物耦合更重，也不说明更轻**。能比的是「引用落在哪」：源码对声明。
2. **等价物的规则确实点名了位置，而且点得不少**：TradingAgents 等价物一条规则平均点名 2.82 个位置，比 TradingAgents 原系统的 1.80 还多；ChatDev 等价物 19 格，Bernstein 等价物 11 格。这和表甲一致：Sherpa 不是让规则不认识组织，而是让「认识组织」只发生在声明里、不进规则代码。改组织时这些参数要跟着改（表甲第二节）。
3. **Sherpa 小组几乎为 0**，是因为它装的包都不按位置配；`base` 包的 `roles.tsv`、`flow.tsv` 里写了 `human`，这是基础生命周期把「人」当成固定的顶层角色，内核每个工作流都有，算一格照实记。
4. **字面量判定的漏和错**：只认整串相等的字符串常量，漏掉经常量、枚举、函数间接判断的点名（Paperclip 的 `board`、Bernstein 的 R21、R38），所以外部系统的数是下限；反过来，TradingAgents 的分析员键 `market`、`news` 这类普通词可能误配，我看过 `refmatrix_matches.tsv` 里 TradingAgents 的全部 31 条，都在分析员注册表和图的节点名上，没有发现误配。
5. **ChatDev 的 C4 把全部节点都点名了**，因为它的顺序规则就是边、每条边写两端节点名。这一格算法对 ChatDev 是如实的，但让 ChatDev 的「一条规则平均点名 5.44 个元素」（原 6.44）显得很高。（11-19 事后查明并更正，mero #22750：引用矩阵只算元素自己定义之外的点名；ChatDev 节点块里的 tooling 是节点自己的定义，C1 的 9 格不再算。旧数留在括号里）
6. Paperclip 有 22 处位置解析不了，Bernstein 的 `::符号` 位置全部解析成功（0 处失败）。

## 五 复查命令

```
cd _companion
nice -n 10 python3 -I tools/coupling_refmatrix.py
# 看某家某条：awk -F'\t' '$1=="bernstein" && $2=="R29"' results/coupling/refmatrix_matches.tsv
```

脚本会在 `results/coupling/.tree_<系统>/` 下解出 Sherpa 一侧四棵树的 `baseline`（`git archive`），只读，可删。
