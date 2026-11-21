# 角色数 × 规则数 二维扫描：Bernstein 和它的 Sherpa 等价物（mero #21652）

vuna，2026-11-19。四个角先报，11-19 补了 s=4。全部实跑，数都由命令出。

## 规则族（原生、区分角色、默认生效）
| 族 | Bernstein（`baseline` cb761c6） | 等价物（`baseline` 0e6cb1c） |
|---|---|---|
| F1 可写路径 | 表 `core/security/permissions.py:155-198`，判断 `:327-375` | `seat_write_limit`（`seat_write_limit.py:11-25`），参数按位置写 |
| F2 令牌权限 | 表 `core/identity/agent_jwt.py:110-172`，兜底 `:175-188` | 派单配对 `lower_seat_pairing.py:10-20`，参数由 `[[instance]]` 生成；由构造覆盖 |
| F3 令牌任务范围 | `core/identity/agent_jwt.py:201`、`:204-216` | 内核地板 `builtin.actor`（`transition_check.py:43-48`）；由构造覆盖 |
| F4 规划必须拆单 | `core/tasks/task_store_core.py:2399-2426`（写死 `"manager"`） | `must_decompose`（`dispatched_enough.py:10-19`），`only` 列位置 |
| F5 规划角色写边界 | `core/agents/spawner_core.py:433`、`:443-487` | `worktree` 包，由构造保证，没有拒绝路径，写不出拒绝用例 |

凑不够 8 族。没算进来的候选：
- R4 `role_model_policy`：它就是组织名单本身；
- `claude_permission_profiles.py:85`：只有 CLI `role_adapter_policy` 引用，默认没接上；
- `seccomp_sandbox.py:930-946`：没有调用处；
- `agent_card.py:135-147` 的 `DEFAULT_DENIED`：只用来生成卡片，没找到强制处；
- `_XL_ROLES` 等：只选模型，不拒绝；
- `rules.yaml`：不分角色。

## 格点怎么定
- 规模 s：1、4、16 组。起点是现有的 `scale-native-keep-k<s>`（Bernstein），和 `grid-k<s>-start`（等价物）。起点上各族只管原有角色。
- R=2 用 {F1, F4}；R=4 用 {F1, F2, F3, F4}。F5 不进集合，因为等价物一侧写不出它的拒绝用例。
- R=8 做不了：原生只有 5 族。
- 「管到」的意思：新角色被当成它照抄的那个角色来判。组长当 manager，`<角色>_g<n>` 当 `<角色>`。
- 甲：起点 → 各族管到全部角色。
  - Bernstein 一侧：表里每个新角色抄一份条目（照场景 1 和 gen_org 版本 A 的写法）；集合一行一个名字；改动在 `grid_rules.py`。
  - 等价物一侧：参数一行一个位置；改动在 `grid_sherpa.py`。
- 乙：在甲上把每组拆成两组：`lead_g<n>` 留前 4 个 worker，新的 `lead_g<n>b` 带后 4 个。同时把 F4 换成 F2，F1 保留。
  - 「去掉 F4」：Bernstein 删检查代码；等价物删 `[policy.must_decompose]` 段和 requires 里那一项。
- 乙只在 R=2 上做。R=4 要换 2 族，得有 2 族在集合外，只剩 F5，所以做不了。

## 四个角的数
`git diff -U0`，每格是文件/@@/增/删。生成命令：`./grid_counts.sh 1 16`。
| side | diff | files | @@ (-U0) | + | - | rule source | org definition | framework | declaration or config | other |
|---|---|---|---|---|---|---|---|---|---|---|
| bernstein | scale-native-keep-k1..grid-k1-r2-a | 3 | 4 | 24 | 2 | 2/3/13/1 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/1/11/1 |
| sherpa | grid-k1-start..grid-k1-r2-a | 1 | 2 | 2 | 0 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/2/2/0 | 0/0/0/0 |
| bernstein | grid-k1-r2-a..grid-k1-r2-b | 15 | 19 | 221 | 46 | 3/4/27/40 | 6/9/188/6 | 0/0/0/0 | 0/0/0/0 | 6/6/6/0 |
| sherpa | grid-k1-r2-a..grid-k1-r2-b | 8 | 20 | 32 | 23 | 0/0/0/0 | 7/16/29/14 | 0/0/0/0 | 2/4/3/9 | 0/0/0/0 |
| bernstein | scale-native-keep-k1..grid-k1-r4-a | 4 | 6 | 41 | 3 | 3/5/30/2 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/1/11/1 |
| sherpa | grid-k1-start..grid-k1-r4-a | 1 | 2 | 2 | 0 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/2/2/0 | 0/0/0/0 |
| bernstein | scale-native-keep-k16..grid-k16-r2-a | 3 | 4 | 789 | 2 | 2/3/658/1 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/1/131/1 |
| sherpa | grid-k16-start..grid-k16-r2-a | 1 | 3 | 138 | 1 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/3/138/1 | 0/0/0/0 |
| bernstein | grid-k16-r2-a..grid-k16-r2-b | 75 | 238 | 4286 | 151 | 3/19/1182/55 | 66/129/3008/96 | 0/0/0/0 | 0/0/0/0 | 6/90/96/0 |
| sherpa | grid-k16-r2-a..grid-k16-r2-b | 98 | 275 | 482 | 233 | 0/0/0/0 | 97/241/449/209 | 0/0/0/0 | 2/34/33/24 | 0/0/0/0 |
| bernstein | scale-native-keep-k16..grid-k16-r4-a | 4 | 6 | 1736 | 3 | 3/5/1605/2 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/1/131/1 |
| sherpa | grid-k16-start..grid-k16-r4-a | 1 | 3 | 138 | 1 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/3/138/1 | 0/0/0/0 |

列的分法：
- Bernstein：`count_scale.py` 的 rule 算规则源码。`bernstein.yaml`、模板、提示词算组织定义。上游测试和生成的镜像文档算 other。
- 等价物：`[[instance]]`、`[seat]`、卡片、文首注释算组织定义。`[policy.*]`、requires 算声明或配置。

## 验收
每族一条放行、一条拒绝，打在最新的组长上；F1 另加一条最新的 `backend_g<n>`。

- Bernstein：`tests/test_grid_rules.py`，跑法 `grid_test.sh <分支> <族>`，输出在 `tests/grid/`。
- 等价物：`grid_sherpa.py cases`，跑法 `bernstein/sherpa_equivalent/grid_test.sh`，输出在 `bernstein/sherpa_equivalent/tests/grid/`。
- 终点上全部通过。
- 拿到起点上反跑：
  - Bernstein：区分得出的用例在起点上都失败；
  - 等价物：只有 F1、F4 的拒绝用例失败；F2、F3 本来就管到（构造）。
- 乙的用例反跑在甲的终点上：新组长还不存在，放行用例失败或报错。

## 读数（拟合留给 mero）
1. 甲，Bernstein：
   - @@ 数不随 s 变：R=2 时 4 个，R=4 时 6 个；
   - 行数随 s×R 涨：k=16 时 R=2 是 +789，R=4 是 +1736。
2. 甲，等价物：
   - @@ 数 2–3 个，R=2 和 R=4 一样，因为 F2、F3 由构造覆盖，改动为 0；
   - 行数只随 s 涨：k=16 时 +138。
3. 乙，规则和声明那部分：
   - Bernstein 规则源码的 @@，从 k=1 的 4 个涨到 k=16 的 19 个：新组长插进每张保留表和新加表的中间。
   - 等价物声明的 @@，从 4 个涨到 34 个：
     - `seat_write_limit` 每个新组长一处；
     - `parallel_wait_all` 的 `except` 每个新组长也一处。
   - 后者不利于 Sherpa：Bernstein 的 manager 交差不等子任务，组长照抄 manager，所以每个组长都得进 `except`。它是按位置写的配置，和规则族无关。
4. 乙，组织那部分，等价物比 Bernstein 大：k=16 时 241 个 @@ 对 129 个。
   - 等价物：64 条 `[[instance]]` 的上级改了，64 张 worker 卡片里写着自己的组长。
   - Bernstein：worker 的文件一个没动，因为它不强制谁带谁，拆组只改提示词。
5. Bernstein 去掉 F4 以后，上游的 `tests/unit/core/tasks/test_zero_yield_planning_task.py` 有 3 条失败。没改这个测试，所以不在计数里。
6. 写法会影响行数：
   - Bernstein 的条目整块照抄，每个 3–12 行；等价物每个位置一行。
   - Bernstein 有更省的路：查表时把 `_g<n>` 后缀映射回原角色，代价和角色数无关。没量。
7. 守着的测试：
   - `tests/unit/test_permissions.py` 加 agent_jwt 的测试，在 k=16 的三个分支上都是 45 条通过；
   - `test_manager_write_boundary.py` 在 R=2 的甲上通过。

## 补：全部格点（s=1、4、16）
生成命令：`./grid_counts.sh 1 4 16`。s=4 的验收全过；起点上的反跑和角上一样。

| side | diff | files | @@ (-U0) | + | - | rule source | org definition | framework | declaration or config | other |
|---|---|---|---|---|---|---|---|---|---|---|
| bernstein | scale-native-keep-k1..grid-k1-r2-a | 3 | 4 | 24 | 2 | 2/3/13/1 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/1/11/1 |
| sherpa | grid-k1-start..grid-k1-r2-a | 1 | 2 | 2 | 0 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/2/2/0 | 0/0/0/0 |
| bernstein | grid-k1-r2-a..grid-k1-r2-b | 15 | 19 | 221 | 46 | 3/4/27/40 | 6/9/188/6 | 0/0/0/0 | 0/0/0/0 | 6/6/6/0 |
| sherpa | grid-k1-r2-a..grid-k1-r2-b | 8 | 20 | 32 | 23 | 0/0/0/0 | 7/16/29/14 | 0/0/0/0 | 2/4/3/9 | 0/0/0/0 |
| bernstein | scale-native-keep-k1..grid-k1-r4-a | 4 | 6 | 41 | 3 | 3/5/30/2 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/1/11/1 |
| sherpa | grid-k1-start..grid-k1-r4-a | 1 | 2 | 2 | 0 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/2/2/0 | 0/0/0/0 |
| bernstein | scale-native-keep-k4..grid-k4-r2-a | 3 | 4 | 177 | 2 | 2/3/142/1 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/1/35/1 |
| sherpa | grid-k4-start..grid-k4-r2-a | 1 | 3 | 30 | 1 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/3/30/1 | 0/0/0/0 |
| bernstein | grid-k4-r2-a..grid-k4-r2-b | 27 | 64 | 1034 | 67 | 3/7/258/43 | 18/33/752/24 | 0/0/0/0 | 0/0/0/0 | 6/24/24/0 |
| sherpa | grid-k4-r2-a..grid-k4-r2-b | 26 | 71 | 122 | 65 | 0/0/0/0 | 25/61/113/53 | 0/0/0/0 | 2/10/9/12 | 0/0/0/0 |
| bernstein | scale-native-keep-k4..grid-k4-r4-a | 4 | 6 | 380 | 3 | 3/5/345/2 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/1/35/1 |
| sherpa | grid-k4-start..grid-k4-r4-a | 1 | 3 | 30 | 1 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/3/30/1 | 0/0/0/0 |
| bernstein | scale-native-keep-k16..grid-k16-r2-a | 3 | 4 | 789 | 2 | 2/3/658/1 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/1/131/1 |
| sherpa | grid-k16-start..grid-k16-r2-a | 1 | 3 | 138 | 1 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/3/138/1 | 0/0/0/0 |
| bernstein | grid-k16-r2-a..grid-k16-r2-b | 75 | 238 | 4286 | 151 | 3/19/1182/55 | 66/129/3008/96 | 0/0/0/0 | 0/0/0/0 | 6/90/96/0 |
| sherpa | grid-k16-r2-a..grid-k16-r2-b | 98 | 275 | 482 | 233 | 0/0/0/0 | 97/241/449/209 | 0/0/0/0 | 2/34/33/24 | 0/0/0/0 |
| bernstein | scale-native-keep-k16..grid-k16-r4-a | 4 | 6 | 1736 | 3 | 3/5/1605/2 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/1/131/1 |
| sherpa | grid-k16-start..grid-k16-r4-a | 1 | 3 | 138 | 1 | 0/0/0/0 | 0/0/0/0 | 0/0/0/0 | 1/3/138/1 | 0/0/0/0 |

## 补：Sherpa 加了「位置的类」以后重量（mero #22640，11-19）

做法：
- 补丁 `2026-11-19-seat-class.patch`（sha256 前 16 位 6fcdd6d86cd6fd48；对应 `_scale/sherpa` 的 6677eb7、40d744d）原样打到等价物树上，得到分支 `baseline-c`（840652a），只改编译器。`test_ppo_build.py` 16 条通过。
- 分支都带 `-c` 后缀，原分支和原数都留着。
- `grid_sherpa.py --classes` 的写法：
  - 每组同名角色一类，叫 `<角色>_seats`；组长一类，叫 `lead_seats`。都是占位名。类名不能和位置名相同，而第 1 组保留了原名，所以加了后缀。
  - manager、human 不归类。
  - 管到全部位置的族，按类写一次；`parallel_wait_all` 的 except 写 `lead_seats`。
  - `[[instance]]` 仍然写位置。
- 只重做 Sherpa 一侧。Bernstein 的数不变，见上表。
- 验收全部照跑，用例和原来相同。终点上全过；起点上的反跑和原来一样。

新旧并排（Sherpa 一侧；文件/@@/+/-；声明或配置 | 组织定义）：

| 格点 | 原来（按位置写） | 带类（-c） |
|---|---|---|
| 甲 s=1 R=2 | 1/2/+2/-0 | 1/2/+9/-7 |
| 甲 s=4 R=2 | 1/3/+30/-1 | 1/2/+9/-7 |
| 甲 s=16 R=2 | 1/3/+138/-1 | 1/2/+9/-7 |
| 甲 s=1 R=4 | 1/2/+2/-0 | 1/2/+9/-7 |
| 甲 s=4 R=4 | 1/3/+30/-1 | 1/2/+9/-7 |
| 甲 s=16 R=4 | 1/3/+138/-1 | 1/2/+9/-7 |
| 乙 s=1 | 8/20/+32/-23：声明 2/4/3/9，组织 7/16/29/14 | 8/18/+31/-23：声明 2/2/1/9，组织 7/16/30/14 |
| 乙 s=4 | 26/71/+122/-65：声明 2/10/9/12，组织 25/61/113/53 | 26/63/+118/-62：声明 2/2/1/9，组织 25/61/117/53 |
| 乙 s=16 | 98/275/+482/-233：声明 2/34/33/24，组织 97/241/449/209 | 98/243/+466/-218：声明 2/2/1/9，组织 97/241/465/209 |

甲：
- 带类以后，三个规模、两种 R 都是 2 个 @@、+9 −7。
- 这 +9 −7 是什么：shipped 的 7 项按位置写的路径换成按类写，加 `lead_seats` 一项；`must_decompose` 的 only 加 `lead_seats` 一行。
- s=1 比原来多 7 行：原来只加 `lead_g1` 一项，现在把原有的 7 项也改写成了类。

上次报的两处不利：
1. 每个新组长要进 `parallel_wait_all` 的 except：**没有了**。
   - 带类以后 except 写的是 `lead_seats`，乙里这一段 0 改动。
   - 乙的声明部分三个规模都是 2 个 @@（+1 −9），只剩删掉 `must_decompose` 段和 requires 里那一项。原来是 4 / 10 / 34 个 @@。
2. 组织部分 241 处：**没变**。
   - 三个规模的 @@ 是 16 / 61 / 241，和原来相同。
   - 行数多了，每个新组长多一行 `class = "lead_seats"`：k=16 时 +449 变 +465。
   - 原因：`[[instance]]` 的上下级只能写位置（k=16 时 80 条 upper 改动：64 个挪组的 worker，加 16 条 manager→新组长）；96 张卡片写着组长名（16 张新的，80 张改的）。类管不到这两样。

命令：
- 建分支：`CLASSES=1 bernstein/sherpa_equivalent/grid_build.sh <s> F1,F4 F1,F2`，再跑一次 `... <s> F1,F2,F3,F4`。
- 量：`count_grid.py sherpa <从> <到>`。
- 验收：`grid_test.sh grid-k<s>-...-c ...`。

## 补：Bernstein 每族每组多少行（mero #23281，11-19）
只读，不跑测试。数的是甲的 diff：`scale-native-keep-k<s>..grid-k<s>-r4-a`（R=2 用 `-r2-a`），`git diff -U0`，在 `modified/` 里。
按 @@ 分族：`permissions.py` 算 F1；`tests/unit/test_permissions.py` 算 F1 的测试钉（计数里在 other 列）；`agent_jwt.py` 里含 `UNSCOPED_AGENT_ROLES` 的那处算 F3，另一处算 F2；`task_store_core.py` 算 F4。
每组 = (k16 − k1) / 15，再用 (k16 − k4) / 12 对一遍。命令：`./grid_per_family.sh r4`、`./grid_per_family.sh r2`。

| 族 | +k1 | +k4 | +k16 | 删（每个 s） | 每组（k1..k16） | 每组（k4..k16） |
|---|---|---|---|---|---|---|
| F1 可写路径 | 5 | 131 | 635 | 0 | 42 | 42 |
| F1 的测试钉（other） | 11 | 35 | 131 | 1 | 8 | 8 |
| F2 令牌权限 | 11 | 194 | 926 | 0 | 61 | 61 |
| F3 令牌任务范围 | 6 | 9 | 21 | 1 | 1 | 1 |
| F4 规划必须拆单 | 8 | 11 | 23 | 1 | 1 | 1 |

- 都整除，余数 0。R=2 分支上 F1、钉、F4 的数和 R=4 完全相同。
- 合起来（只算规则源码，不含钉）：R=2 是 42+1=43；R=4 是 42+61+1+1=105。和上表 rule source 列一致：(658−13)/15=43，(1605−30)/15=105。
- 为什么这样分：每多一组多 9 个角色（1 个组长、8 个 worker）。
  - F1：表里每个新角色抄一块，reviewer 不在表里，所以每组 8 块。
  - F2：同样整块抄，块更大。
  - F3、F4：集合里每组只多 1 个组长名，一行。
  - 钉：上游测试里的角色集合，每组多 8 个名字。
- 「每多一族约 31 行」是 R=2 到 R=4 的平均：(105−43)/2=31。实际加的两族是 F2 61 行、F3 1 行，不均。
- Sherpa 一侧（带类，baseline-c）：甲在三个规模上都是 +9 −7，每族每组 0 行。

仓主 11-19 定了「位置的类」算 Sherpa 的一部分。正文里这一对的 Sherpa 数只用带类（-c）那套；上面按位置写的 Sherpa 行留作记录。

## 补：同一角色的位置共用一张角色卡（mero #23470，11-19）
只做静态计数，没跑进程；验收等 mero 通知。在带类（-c）那套上再出两套，都从 `baseline-c` 起：
- `-cs`：每一类共用一张卡，`card = "cards/<类>.md"`，worker 的 8 类和组长类都合。
- `-csw`：只合 worker 的 8 类；组长每人还是自己的卡。
- 写法：`grid_sherpa.py --classes --shared-cards all|workers`；建分支 `CLASSES=1 CARDS=all|workers grid_build.sh <s> ...`。
- 共用卡里不写位置名、执照号、上级名：原卡的标题行改成 `# <类>`，「The manager dispatches your task.」改成「Your upper dispatches your task (the task shows who).」。组长卡不列 worker，写「你的下级位置；派给别的位置会被拒」。
- 卡文件：`-cs` 上任何规模都是 11 张（human、manager、`lead_seats`、8 个 `<角色>_seats`）。卡路径都查过，文件都在；共用卡里查不到 `_g<n>` 和执照号。

忠实性（只读 Bernstein 的 diff）：
- worker：s=16 上 8 个角色 × 15 组 × 3 个文件（`system_prompt.md`、`task_prompt.md`、`config.yaml`），360 对和原角色逐字节相同。合并。
- 组长：15 个 `lead_g<n>/system_prompt.md` 都和 `lead_g1` 不同。照字面规则组长不合，就是 `-csw`。
- mero 11-19 定（#23544）：正文用 `-cs`，`-csw` 留作保守口径。理由：组长卡之间只差同一个模板按位置填的字段，是位置信息；0.2 原设计里角色卡同角色共用，位置信息进任务单。
- 组长卡差在哪（`scale-native-keep-k4`，`lead_g1` 对 `lead_g2`）：
  - `system_prompt.md:3` 组号（"You lead group 2"）；
  - `system_prompt.md:21-28` 组员名单（`backend_g2` 等 8 个）；
  - `system_prompt.md:71`、`:95` 和 `task_prompt.md:44` 例子里的角色名（`"role": "backend_g2"`）。
  - 拆组后（`grid-k4-r2-b`，`lead_g2` 对 `lead_g2b`）同样是这几处：`:3`、`:21-24`、`:67`、`:91`。
- 这些信息在 Sherpa 一侧组长从哪里得到：
  - 上级：任务单的 `issued_by`，派单时写入（`classic_lifecycle/dispatch.py:32`）。
  - 下级：派给不是自己下级的位置时被拒，拒绝信息列出自己下级的执照前缀（`classic_lifecycle/lower_seat_pairing.py:18-20`）。
  - 组号：不需要，下级就定了组。
  - 例子里的角色名：卡里写占位 `<SEAT>-01`。
  - 注意：`sherpa claude` 给的 brief（`claude_session/start_session.py:15-27`）只有角色卡和任务的目标、写范围、分支，不列 `issued_by`，也不列下级。

装规则（甲，六个格点）：三套都是 1 个文件、2 个 @@、+9 −7，没变。

复合变更（乙；文件/@@/+/−；括号里是组织定义那部分，声明部分三套都是 2/2/+1/−9）：

| s | 带类（-c） | 共用卡、组长不合（-csw） | 共用卡、全合（-cs） |
|---|---|---|---|
| 1 | 8/18/+31/−23（7/16/+30/−14） | 4/14/+27/−19（3/12/+26/−10） | 2/12/+19/−18（1/10/+18/−9） |
| 4 | 26/63/+118/−62（25/61/+117/−53） | 10/47/+102/−46（9/45/+101/−37） | 2/39/+70/−42（1/37/+69/−33） |
| 16 | 98/243/+466/−218（97/241/+465/−209） | 34/179/+402/−154（33/177/+401/−145） | 2/147/+274/−138（1/145/+273/−129） |

- s=16，243 处：`-cs` 变 147，正好少 96 处卡片；`-csw` 变 179，剩组长的 32 处卡（16 张新的、16 张名单变短的）。
- `-cs` 剩下的 145 处组织改动全在 `PPOtestBernstein.toml`：`[[instance]]` 上级改动 112 处、新组长的 `[[instance]]` 16 处、新组长的 `[seat]` 16 处、文首注释 1 处。
- 112 处里 64 处只改 `id` 行，48 处只改 `upper` 行（另 16 处 `upper` 改动和新 `[[instance]]` 并在一处）。`id` 写成 `<上级>_to_<下级>` 是我当初的写法，换组长时跟着变；`id` 不带上级名的话，这 64 处没有。没建分支量。
- 命令：`count_grid.py sherpa grid-k<s>-r2-a<后缀> grid-k<s>-r2-b<后缀>`，后缀 `-c`/`-csw`/`-cs`。

### 再改：`[[instance]]` 的 id 写下级名（mero #23544）
- 原来 id 写 `<上级>_to_<下级>`，是搭等价物时自己加的耦合。Sherpa 自带的 `PPOtest2CtoTeam` 用 `top`、`team`、`review` 这类标签。
- 新套 `-csi`：`-cs` 加 `grid_sherpa.py --id-lower`，id 就是下级位置名（每个位置只有一个上级，不会重名）。建分支 `CLASSES=1 CARDS=all ID=lower grid_build.sh <s> ...`。
- 改名算起点的写法：`grid-k16-start-cs..grid-k16-start-csi` 只改了 145 行 id，别的一行没动；id 无重复。

装规则（甲，六个格点）：`-csi` 也是 1/2/+9/−7，没变。

复合变更（乙；文件/@@/+/−；括号里是组织定义，声明部分都是 2/2/+1/−9）：

| s | `-cs` | `-csi` |
|---|---|---|
| 1 | 2/12/+19/−18（1/10/+18/−9） | 2/9/+15/−14（1/7/+14/−5） |
| 4 | 2/39/+70/−42（1/37/+69/−33） | 2/27/+54/−26（1/25/+53/−17） |
| 16 | 2/147/+274/−138（1/145/+273/−129） | 2/99/+210/−74（1/97/+209/−65） |

- 16 组时 147 处变 99 处。
- 99 处是：挪组 worker 的 `upper` 64 处，新组长的 `[[instance]]` 16 处（manager→新组长）、`[seat]` 16 处，文首注释 1 处，声明 2 处（`must_decompose` 段和 requires）。
- 每组 6 处 = 4 个挪组 worker + 新组长的 1 条 `[[instance]]` + 1 个 `[seat]`，与组的个数成正比。
- 命令：`count_grid.py sherpa grid-k<s>-r2-a-csi grid-k<s>-r2-b-csi`。

## 补：耦合探针（mero #23586，11-19）
静态计数，没跑进程。Bernstein 起点 `scale-native-keep-k<s>`；Sherpa 用共用卡套，起点 `grid-k<s>-start-csi`。s=1 和 16。
三栏：规则源码 / 组织定义 / 其余。Bernstein 的其余 = 上游测试钉 + 生成的镜像文档；Sherpa 的其余 = 声明（`[policy.*]`），单独标出。每格文件/@@/+/−。

### 探针一：L、R、L+R
- L 加一层：Bernstein 用已有的 `native-keep-k<s>-layer`（manager 和组长之间加 `director`，照抄 manager）。Sherpa 用 `grid_sherpa.py --layer`：`director` 一个位置、自己一张新卡、不归类；它照抄 manager，所以和 manager 一样进 `parallel_wait_all` 的 except。
- R 加一条按角色带值的规则：F1 可写路径（每个角色一组路径），管到起点上全部角色。分支 `grid-k<s>-r1-a`（两边同名，Sherpa 带 `-csi`）。原来格点里没有只装 F1 的分支，这次新建。
- L+R：在加层的树上装 F1，`director` 也管到（照 manager 的路径），旧角色照旧。Bernstein `probe-k<s>-layer-r1`，Sherpa `grid-k<s>-layer-r1-a-csi`。

| s | 一侧 | 行 | 规则源码 | 组织定义 | 其余 | 合计 |
|---|---|---|---|---|---|---|
| 1 | Bernstein | L | 0 | 6/8/+186/−4 | 5/5/+5/−0 | 11/13/+191/−4 |
| 1 | Bernstein | R | 1/1/+5/−0 | 0 | 1/1/+11/−1 | 2/2/+16/−1 |
| 1 | Bernstein | L+R | 1/1/+10/−0 | 6/8/+186/−4 | 6/6/+17/−1 | 13/15/+213/−5 |
| 1 | Sherpa | L | 0 | 3/6/+18/−3 | 声明 1/1/+1/−0 | 3/7/+19/−3 |
| 1 | Sherpa | R | 0 | 0 | 声明 1/1/+8/−7 | 1/1/+8/−7 |
| 1 | Sherpa | L+R | 0 | 3/6/+18/−3 | 声明 1/2/+10/−7 | 3/8/+28/−10 |
| 16 | Bernstein | L | 0 | 21/23/+216/−34 | 5/5/+5/−0 | 26/28/+221/−34 |
| 16 | Bernstein | R | 1/1/+635/−0 | 0 | 1/1/+131/−1 | 2/2/+766/−1 |
| 16 | Bernstein | L+R | 1/1/+640/−0 | 21/23/+216/−34 | 6/6/+137/−1 | 28/30/+993/−35 |
| 16 | Sherpa | L | 0 | 3/21/+33/−18 | 声明 1/1/+1/−0 | 3/22/+34/−18 |
| 16 | Sherpa | R | 0 | 0 | 声明 1/1/+8/−7 | 1/1/+8/−7 |
| 16 | Sherpa | L+R | 0 | 3/21/+33/−18 | 声明 1/2/+10/−7 | 3/23/+43/−25 |

L+R 比 L 加 R 多出（两个规模一样）：
- Bernstein：+6 行，文件数和 @@ 不多。规则源码 +5：`permissions.py` 的表里给 `director` 抄一块 manager 的条目。其余 +1：上游测试钉里多一个名字。
- Sherpa：+1 行，在声明里：`seat_write_limit` 的 params 多一项 `director=<manager 的路径>`。文件数和 @@ 也不多（L 的 except 那处、R 的 params 那处，L+R 里还是这两处）。
- 注意 L 本身：
  - Sherpa 的 L 里已经有 1 行声明，就是 `director` 进 `parallel_wait_all` 的 except。这是组织的事：Bernstein 照抄 manager 的角色交差不等子任务。
  - Bernstein 的 L 在 s=16 改 16 个组长提示词，因为里面写着上级是 Manager。Sherpa 的组长共用卡写「你的上级」，不改。
  - Sherpa 的 L 在 s=16 有 16 处 `[[instance]]` 的上级从 manager 换成 director，所以 @@ 随 s 涨。

### 探针二：换上级
- s=1：`backend` 从 `lead_g1` 挪到 `manager` 名下（s=1 只有这两个上级）。s=16：`backend_g16` 从 `lead_g16` 挪到 `lead_g15`。
- Bernstein：`probe-k<s>-move`，`probe_move.py`；Sherpa：`grid-k<s>-move-csi`，`grid_sherpa.py --move`。

| s | 一侧 | 规则源码 | 组织定义 | 其余 | 强制吗 |
|---|---|---|---|---|---|
| 1 | Bernstein | 0 | 2/2/+2/−2 | 0 | 不强制 |
| 16 | Bernstein | 0 | 3/3/+3/−3 | 0 | 不强制 |
| 1 | Sherpa | 0 | 1/1/+1/−1 | 0 | 强制 |
| 16 | Sherpa | 0 | 1/1/+1/−1 | 0 | 强制 |

- Bernstein：规则 0 行改动，也不强制谁带谁。任何能建任务的角色都能给任何角色建任务（`auth_middleware.py:206-208`；`self-create` 不校验角色名，`task_crud.py:1301-1340`；见 11 号文档）。所以新上级本来就能派它，旧上级挪走以后也照样能派。
  - 改的只是提示词：旧组长名单 −1 行，新上级名单 +1 行，manager 提示词里两组的成员括号各改一处（s=1 时新上级就是 manager，所以是 manager 一个文件里 +2 −1）。
  - 镜像文档没变（`agents-md sync` 后无改动）。旧组长提示词里例子 curl 写的 `backend_g16` 没改。
  - 原生规则里没有「谁带谁」可改；要强制得加框架代码（版本 B，`enforce-framework` 分支），不在这次计数里。
- Sherpa：改 `[[instance]]` 的 1 行 `upper`（id 是下级名，不动）。派单配对由 `[[instance]]` 生成（`lower_seat_pairing.py:16-20`），挪过去以后新上级能派、旧上级被拒。它自己的写范围等规则按位置或类写，不动。共用卡不动。
  - s=1 挪到 manager 名下时，manager 的卡还写着「你的下级是各组长」，没改。它是位置信息，按共用卡的写法本不该写在卡里；没改，照实记下。

命令：
- Bernstein：`probe_build.sh 1 backend lead_g1 manager`、`probe_build.sh 16 backend_g16 lead_g16 lead_g15`。
- Sherpa：`bernstein/sherpa_equivalent/probe_build.sh 1 backend:manager`、`... 16 backend_g16:lead_g15`。
- 量：`count_grid.py bernstein|sherpa <起点> <分支>`。

## 补：装 1–4 族的新增行数，直接量（mero #23672，11-19）
族的先后 F1、F4、F2、F3。新建 Bernstein `grid-k4-r1-a`、`grid-k<s>-r3-a`（F1,F4,F2）；Sherpa 用 `-csi` 套，新建 `grid-k4-r1-a-csi`、`grid-k<s>-r3-a-csi`。静态计数，没跑进程。
命令：`count_grid.py bernstein scale-native-keep-k<s> grid-k<s>-r<R>-a`；`count_grid.py sherpa grid-k<s>-start-csi grid-k<s>-r<R>-a-csi`。

| R | 族 | Bernstein 规则源码 + 行（s=1/4/16） | Bernstein 合计 +/−（含测试钉） | Sherpa（-csi）+/−（s=1/4/16 都一样） |
|---|---|---|---|---|
| 1 | F1 | 5 / 131 / 635 | +16/−1、+166/−1、+766/−1 | +8 −7 |
| 2 | F1 F4 | 13 / 142 / 658 | +24/−2、+177/−2、+789/−2 | +9 −7 |
| 3 | F1 F4 F2 | 24 / 336 / 1584 | +35/−2、+371/−2、+1715/−2 | +9 −7 |
| 4 | F1 F4 F2 F3 | 30 / 345 / 1605 | +41/−3、+380/−3、+1736/−3 | +9 −7 |

- 量出来的规则源码行数和「每族每组多少行」那节按族加出来的一样：R=1 是 5/131/635，R=3 是 24/336/1584。
- Sherpa：F1 是 params 按类写，+8 −7；F4 是 `only` 加一行 `lead_seats`；F2、F3 由构造覆盖，0 行。所以 R=2、3、4 都是 +9 −7，和 s 无关。

## 补：-csi 套的验收（mero #23714，11-19）
跑法：`bernstein/sherpa_equivalent/queue_csi.sh`，一次一个进程，21 次，12:43–12:46 跑完，没被停。结果在 `bernstein/sherpa_equivalent/tests/grid/grid-k<s>-*-csi--*/`。

| 规模 | 分支（用例） | 对上 |
|---|---|---|
| s=1、4、16 | `r1-a-csi`（F1，3 条） | 全对 |
| s=1、4、16 | `r2-a-csi`（F1 F4，5 条） | 全对 |
| s=1、4、16 | `r3-a-csi`（F1 F4 F2，7 条） | 全对 |
| s=1、4、16 | `r4-a-csi`（4 族，9 条） | 全对 |
| s=1、4、16 | `r2-b-csi`（乙，F1 F2，5 条） | 全对 |

起点上反跑：
- 4 族用例放到 `start-csi` 上：s=1 有 2 条失败（F1-refuse、F4-refuse）；s=4、16 有 3 条失败（再加 F1-refuse-worker；s=1 的 worker 是原有的 backend，起点上本来就管到）。F2、F3 由构造覆盖，起点上就对。
- 乙的用例放到 `r2-a-csi` 上：三个规模都是 3 条失败（F1-allow、F1-refuse、F2-allow），因为新组长还不存在。
- 和带类（-c）那套逐条相同。

## 补：组合演示（mero #23876，11-19）
静态计数，没跑进程；验收等通知。三栏是规则源码 / 组织定义 / 其余（Bernstein 的其余 = 镜像文档和上游测试钉；Sherpa 的其余 = 声明）。每格文件/@@/+/−。

### 演示一：放大，规则不变
- Bernstein：原生扩法 `scale-native-keep-k<k>`。补建了 k=2、8，做法和原来一样（`gen_org.py . <k> --native --keep-names`，再 `agents-md sync`）。用同样做法重建 k=4，树的哈希和原分支相同（ef77ef85f）。
- Sherpa：`-csi` 套。1 倍上规则已经按类写好（`grid-k<k>-r4-a-csi`，4 族）。补建了 k=2、8。
- 数的是 size-1 到 size-k 的整段 diff：`count_grid.py bernstein scale-native-keep-k1 scale-native-keep-k<k>`；`count_grid.py sherpa grid-k1-r4-a-csi grid-k<k>-r4-a-csi`。

| k | Bernstein 规则源码 | Bernstein 组织定义 | Bernstein 其余 | Sherpa 规则源码 | Sherpa 组织定义 | Sherpa 其余（声明） |
|---|---|---|---|---|---|---|
| 2 | 0 | 29/31/+866/−1 | 5/45/+45/−0 | 0 | 1/3/+82/−1 | 0 |
| 4 | 0 | 83/85/+2596/−1 | 5/45/+135/−0 | 0 | 1/3/+244/−1 | 0 |
| 8 | 0 | 191/193/+6056/−1 | 5/45/+315/−0 | 0 | 1/3/+568/−1 | 0 |
| 16 | 0 | 407/409/+12976/−1 | 5/45/+675/−0 | 0 | 1/10/+1224/−9 | 0 |

- Bernstein 每多一组：组织 +27 个文件（9 个角色 × 3 个模板文件）、+865 行（(12976−866)/14）；镜像文档 5 个文件，每组 +45 行。
- Sherpa 只改一个文件 `PPOtestBernstein.toml`，每组 +81 行（9 条 `[[instance]]` 和 9 个 `[seat]`）。共用卡不加文件，声明 0 行。
- Sherpa k=16 的 10 个 @@ 和 −9 是 git 默认 diff 算法的对齐结果：实际只有插入和文首注释一处；用 `--histogram` 是 3 个 @@。

放大以后，原有规则管不管得到新角色：
- Bernstein：管不到。实测：4 族用例（打在最新组长和最新 `backend_g<k>` 上）在 `scale-native-keep-k4`、`-k16` 上各 7 条失败、3 条通过；在 k=1 上 5 条失败、2 条通过，`lead_g1` 也管不到。结果在 `tests/grid/scale-native-keep-k<s>--F1-F2-F3-F4.txt`。k=2、8 没跑，表按角色名写、放大不改表，读代码结论相同。
- Sherpa：管得到。规则按类写，新位置在 `[seat]` 里写了类，就被同一条规则管。实测：`r4-a-csi` 在 s=1、4、16 上 9 条全对（见上一节）。k=2、8 没跑，声明和 k=1 逐字节相同。
- 对照：如果 Sherpa 1 倍的规则按位置写（`start-csi`），放大同样管不到新位置：s=4、16 上 F1-refuse、F1-refuse-worker、F4-refuse 失败。

### 演示二：嵌套（1 倍上，backend 带 3 个同种的新手下）
- Bernstein：`demo2-k1-nest`，从 `scale-native-keep-k1` 起，`demo2_nest.py`。
  - Bernstein 只有角色，没有位置，「3 个」写不进任何文件：同时跑几个由 spawner 定。
  - 所以手下是一个新角色 `backend_helper`（占位名），照抄 backend：模板原样复制，`bernstein.yaml` 加一行。
  - backend 的提示词加「Delegating to helpers」一段（照场景 7 的写法）。
  - backend 的 F1、F2 条目给 `backend_helper` 各抄一份，上游测试钉加一个名字。
  - `plan_schema.py` 的 `KNOWN_ROLES` 没加：它只管计划文件，`gen_org.py --native` 也不加。
- Sherpa：`demo2-k1-nest-csi`，从 `grid-k1-r4-a-csi` 起，`grid_sherpa.py --nest backend:3`。
  - 3 个位置 `backend_h1..3`，类是 `backend_seats`，共用 backend 的卡。
  - 共用卡加一段通用的「下级位置」说明，不写任何位置名。
  - backend 照旧等手下交差，不进 `parallel_wait_all` 的 except。

| 一侧 | 规则源码 | 组织定义 | 其余 | 合计 |
|---|---|---|---|---|
| Bernstein | 2/2/+14/−0 | 5/5/+89/−0 | 6/6/+6/−1 | 13/13/+109/−1 |
| Sherpa | 0 | 2/3/+31/−0 | 0 | 2/3/+31/−0 |

- Sherpa 的 +31：3 条 `[[instance]]` 18 行，3 个 `[seat]` 9 行，卡 4 行。规则 0 行，因为手下进了 backend 的类。
- Bernstein 的规则源码 +14：`permissions.py` 4 行，`agent_jwt.py` 10 行。手下数从 1 变 3，Bernstein 的数不变，Sherpa 每个手下 +9 行。

验收要点（只写了用例，没跑）：
- Bernstein：`tests/test_nest.py`。
  - 新领导能派给新手下：能。读代码：`/tasks/self-create` 收任何角色名（`task_crud.py:1301-1340`），backend 不缺权限。
  - 别的上级不能越过它直接派：做不到。任何角色都能给任何角色建任务（`auth_middleware.py:206-208`），没有「谁的手下」。用例里记的是 manager 带 `agents:spawn`。
  - 新手下受 backend 的规则管：F1 一放一拒、F2 一放一拒。在 `scale-native-keep-k1` 上反跑，会区分的是 F1 拒绝和 F2 放行；另两条在那里本来就成立。
- Sherpa：`bernstein/sherpa_equivalent/tests/demo2/cases.tsv`。
  - N-allow：backend 派给 backend_h1，放行。
  - N-refuse-bypass：lead_g1 派给 backend_h1，被拒（`classic_lifecycle.not_your_lower`）。
  - N-rule-allow：backend_h1 改 `src/`，放行。
  - N-rule-refuse：backend_h1 改 `.github/`，被拒（`seat_write_limit.outside_seat_paths`）。
  - 跑法：`grid_test.sh demo2-k1-nest-csi 1 N --nest`。

### 演示二验收（mero #24211，11-19）
一次一个进程，4 次，没被停。

| 一侧 | 分支 | 结果 | 文件 |
|---|---|---|---|
| Bernstein | `demo2-k1-nest` | 5 条全过 | `tests/grid/demo2-k1-nest--nest.txt` |
| Bernstein | 起点 `scale-native-keep-k1` 反跑 | 2 条失败（F1 拒绝、F2 放行），3 条通过 | `tests/grid/scale-native-keep-k1--nest.txt` |
| Sherpa | `demo2-k1-nest-csi` | 4 条全对 | `bernstein/sherpa_equivalent/tests/grid/demo2-k1-nest-csi--N--nest/` |
| Sherpa | 起点 `grid-k1-r4-a-csi` 反跑 | 3 条对不上 | `bernstein/sherpa_equivalent/tests/grid/grid-k1-r4-a-csi--N--nest/` |

- Bernstein 起点上通过的 3 条，事先就写明了不区分：
  - F1 放行：不认识的角色什么都能改；
  - F2 拒绝：兜底权限里本来就没有 `agents:spawn`；
  - 越级那条：记的是「做不到」，manager 本来就能给任何角色建任务。
- Sherpa 起点上对不上的 3 条：N-allow 被拒（`builtin.role`、`not_your_lower`）；两条规则用例在准备那步就失败，因为 backend_h1 位置还不存在。
- Sherpa 起点上 N-refuse-bypass 照样被拒，理由一样是 `not_your_lower`：位置不存在时也派不过去。这条在起点上不区分。
- 跑法：`nest_test.sh <分支>`（Bernstein）；`grid_test.sh <分支> 1 N --nest`（Sherpa）。

## 补：树的格点 T(k, m)（mero #24340、#24380，11-19）
只建树、提交，没跑验收；行数由 mero 统一数。#24340 那 12 棵起点上 4 族已管到 `lead_g1`，和新定义不符，已删掉重建。
- k = 新种类数 0、1、2、4、8，挂在 `lead_g1` 下，占位名 `kind1..kind8`。新种类有自己的名字、提示词、取值：模板从 backend 的起手，换掉标题和「做什么」那行，可写路径是自己的 `modules/kind<i>/`。
- m = 管到全部角色（含 `lead_g1` 和新种类）的族数 0、1、2、4，次序 F1 可写路径、F2 令牌权限、F4 规划必须拆单、F3 令牌任务范围。m=8 做不了：两边都能强制的原生按角色族只有 4 个。
- F3、F4 是只认 manager 的「是/否」标志。新执行者落在默认值上（令牌按任务限定、不必拆单），两边都 0 行也照样受管。F4、F3 的成本只在让 `lead_g1` 管到的那部分。
- 分支：
  - Bernstein：`_scale/bernstein/modified` 里的 `grid2-k<k>-m<m>`。
  - Sherpa 等价物：`bernstein/sherpa_equivalent/modified` 里的 `own-grid2-k<k>-m<m>`（甲，每个新种类自成一类）和 `join-grid2-k<k>-m<m>`（乙，归进 `backend_seats`）。k=0 时甲乙是同一棵树。
- T(0,0)：
  - Bernstein 是 `scale-native-keep-k1` 原样，树相同。原生的 4 族管着原有 8 个角色，去不掉；`lead_g1` 哪族都不管。
  - Sherpa 是 `grid-k1-start-csi`，树相同。F1、F4 按原有位置写；F2、F3 由构造覆盖，去不掉。
- 建法：`bernstein/sherpa_equivalent/grid2_build.sh`（Bernstein 用 `grid_rules.py` + `kinds.py`；Sherpa 用 `grid_sherpa.py` + `kinds_sherpa.py`）。
- 用例，写好没跑：
  - Bernstein `tests/test_kinds.py`：每个新种类，F1、F2、F3 各一放一拒，F4 只有放行（执行者不会被它拒）。
  - Sherpa `bernstein/sherpa_equivalent/tests/kinds/k<k>-own|join.tsv`：同样的分法。
  - `lead_g1` 那部分用原来的 `tests/test_grid_rules.py` 和 `grid_sherpa.py cases`。

## 补：grid3 模拟规则（mero #24557，11-19）
定义见 `_scale/GRID3-模拟规则.md`。只建树、提交、写用例，没跑；行数 mero 统一数。
- 分支：`_scale/bernstein/modified` 里的 `grid3-k<k>-m<m>`，25 个。`grid3-k0-m0` 和 `scale-native-keep-k1` 是同一棵树。建法 `grid3_build.sh`（调 `grid3.py`）。
- 角色：Bernstein 原生只能运行时多起几个、共用 `backend` 这个名字。要各有名字、能单独派，最小改动是照 `gen_org.py --native` 复制成新角色 `backend_c1..c8`（占位名）：
  - 模板原样复制，`bernstein.yaml` 一行，`lead_g1` 名单一行，manager 的组成员括号里加名字，再 `agents-md sync`。
  - 为了「其余完全一样」，原生的按角色表也给每个复制品抄一份 backend 的条目：F1 `permissions.py` 4 行，F2 `agent_jwt.py` 10 行，上游测试钉加名字。这部分算在规则源码文件里，但属于角色这一维。
- 规则：新文件 `core/tasks/relay_rules.py`，每条规则一块，全局写一次：
  - 派单文本（任务说明）在 worker 认领时查（接手方）。照的是 TASK-003 文件归属检查：三条认领路径上各一处，`task_store_core.py:2161-2165`、`:2237-2239`、`:2297-2299`；检查本身照 `:3310-3334` 写成 store 的方法。
  - 交回文本（result_summary）在 `complete` 里查，放在 #4401 规划检查之前（`:2399`）。Bernstein 的上级没有「接收交回」这一步，所以在交出那一步查。
  - 拒绝时抛 ValueError，照 `claim_by_id` 的拒法（`:2229-2239`）。
  - R4 的「全部直接下级」取这个任务建出来的子任务的角色。Bernstein 没有谁带谁的名单，只有父子任务。
  - R5 的词表按角色名为键，照 `DEFAULT_ROLE_PERMISSIONS`（`permissions.py:155-198`）的写法，所以每个复制品各一行（都是 blue）。这是 8 条里唯一按角色各接一次的。
  - R7：合法流程最多 4 步（派 2 步、交回 2 步）；复制品在同一层，链不会变长，N 一直是 9。
  - 接龙行由 agent 写，树里没有教它写的提示词。要加的话，全局一处在 `core/agents/spawn_prompt.py`。
- 用例（写好没跑）：`tests/test_relay.py`。每条开着的规则一放一拒，打在 manager → `lead_g1` → 最新复制品这条链上。m=0 时全部跳过。

### grid3「先扩，再改」（mero #24719）
- 分支 `grid3-k<k>-m0-change`，从 `grid3-k<k>-m0` 起，`grid3_change.py`。只改、只提交，没跑。
- 改的是原生 F1 可写路径（`permissions.py` 的 `DEFAULT_ROLE_PERMISSIONS`）：backend 不许再写 `pyproject.toml`，和场景 3 的改动相同。
- 这张表以角色名为键，每个复制品各有一项（grid3 复制时抄的），所以每个名字各改一遍。k=0、1、2、4、8 时分别改 1、2、3、5、9 处，每处 +1 −1。

### grid3 验收（mero #24857，11-19）
一次一个进程，没被停。用例在 `tests/test_grid3_roles.py`（(a)、(d)）和 `tests/test_relay.py`，跑法 `grid3_test.sh`，结果在 `tests/grid3/`。

| 项 | 分支 | 结果 | 起点反跑 |
|---|---|---|---|
| (a) backend_c8 能派活，F1、F2 各一放一拒（6 条） | `grid3-k8-m0` | 6 条全过 | `grid3-k0-m0`：3 条失败（派活放行、F1 拒绝、F2 放行），3 条通过 |
| (d) 收窄后的可写范围，backend 和 backend_c8 各一放一拒（4 条） | `grid3-k8-m0-change` | 4 条全过 | `grid3-k8-m0`：2 条失败（两个拒绝），2 条通过 |
| 8 条接龙规则，各一放一拒（16 条） | `grid3-k8-m8` | 16 条全过 | 没要求反跑 |

- 反跑时通过的几条事先就不区分：
  - 「backend_c9 不是合法角色」本来就成立；
  - 不认识的角色什么都能改，所以 F1 放行照样过；
  - 兜底权限里本来就没有 `agents:spawn`，所以 F2 拒绝照样过；
  - 收窄前 `src/` 本来就能写，所以 (d) 的两条放行照样过。
- 接龙规则头一次跑是 13 过 3 败，3 条都是用例自己写错了，不是规则的问题：
  - R2、R3 两条，同一个参数传了两遍（TypeError）；
  - R7 那条，链中间一步先被 R3 拒了，没走到 R7。改法是让 manager 的根任务带 n=8，这样往下派是 9 步、10 步，R3 都对，第 10 步才轮到 R7 拒。
  - 改完重跑 16 条全过。头一次的结果留在 `tests/grid3/grid3-k8-m8--relay.first-run.txt`。

### grid3 (a)、(d) 在 Sherpa 等价物上（mero #24968，控制变量）
只建树、提交、写用例，没跑。
- 仓库 `bernstein/sherpa_equivalent/modified`，分支 `eq-grid3-k<k>-m0` 和 `eq-grid3-k<k>-m0-change`，k=0、1、2、4、8，共 10 个。
- 起点 `grid-k1-r4-a-csi`：1 倍，带类、共用卡，id 用下级名，F1 按类写（`backend_seats=...`）。建法 `eq_grid3_build.sh`（调 `eq_grid3.py`）。
- (a) 每多一个位置 `backend_c<i>`：一条 `[[instance]]` 6 行加一个 `[seat]` 3 行，共 9 行，全在组织定义里，规则参数 0 行。
  - 这份声明里没有逐个点 worker 位置的策略：`parallel_wait_all` 的 except 和 `must_decompose` 的 only 只写 manager 和 `lead_seats`。所以新位置不用各写规则行。
  - k=8 是 1 个文件、2 处、+72。
- (d) 改 `backend_seats` 那一项，去掉 `pyproject.toml`。任何 k 都是 1 处，+1 −1。
- 用例（和 Bernstein 的一一对应），在 `bernstein/sherpa_equivalent/tests/eq-grid3/k<k>-a.tsv`、`k<k>-d.tsv`：
  - (a)：派活放行；派给没设的 `backend_c<k+1>` 被拒；F1 一放一拒；F2（派单配对）一放一拒。
  - (d)：backend 和 `backend_c<k>` 各一放一拒（写 `src/` 放行，写 `pyproject.toml` 被拒）。
- 对照：如果起点的 F1 按位置写（`grid-k1-start-csi` 里是 `backend=...`），新位置就得各加一行参数才能取到同样的值，(d) 也要改 k+1 处。

### (a) 用 `copies = N` 重做（mero #25117）
- 补丁 `2026-11-20-seat-copies.patch`（sha256 前 16 位 392a4ad8d1734f00）原样打到 `grid-k1-r4-a-csi` 上，得到 `grid-k1-r4-a-csi-copies`（17754ae）。`test_ppo_build.py` 18 条通过。
- 分支 `eqn-grid3-k<k>-m0`，k=1、2、4、8：在 backend 那条 `[[instance]]` 上加一行 `copies = k`（`eq_grid3.py copies`）。每个 k 都是 1 个文件、1 处、+1 行，规则参数 0 行。
- 验收（k=8，位置名 `backend_9`，未设的是 `backend_10`）：`tests/eq-grid3/k8-a-copies.tsv`，6 条全对。在 `grid-k1-r4-a-csi-copies` 上反跑：4 条对不上（派活放行、F1 一放一拒、F2 放行），2 条拒绝照样被拒。结果在 `bernstein/sherpa_equivalent/tests/eq-grid3/runs/`。
- 和逐个写位置比：
  - 名字由编译器定（`_2`..`_N+1`），不能自己起名；
  - 复制品只能挂在同一个上级下；
  - 要把其中一个挪走或去掉中间某一个，就得把它们逐个写出来。
  - 某一个要用不同的卡或类，可以单独写它的 `[seat]`：展开用的是 setdefault，写了就以写的为准。

## 补：改名探针（mero #25281、#25694，11-20）
Bernstein 上游基线 `scale-base`（cb761c6）上开 `probe-rename`（96a6f8a4f），把角色 backend 改名为 `server_dev`（占位名），别的不动。脚本 `probe_rename.py`，规则写在它的说明里。
- 改的地方：
  - `src/` 里按词法切出的、作角色名用的字符串字面量，167 处（表键、默认值、角色名单、映射的值）；
  - 角色模板目录、技能目录、`bernstein.yaml` 的键；
  - manager 提示词的名单，以及两处让 agent 照抄的建任务例子；
  - 21 个随包模板（plans、workflows、recipes、scenarios、ticket、teams）里有效的 `role:`/`agent:` 行；
  - 镜像文档（再同步一次）。
- 没改的：
  - 注释和 docstring 里的 75 处（开发文档）；
  - 不是角色的 backend：存储、沙箱、密钥、vault、集群、指标标签、doctor 的后端，以及 capability_router 的能力标签；
  - 文本关键词（role_classifier、agency/plugin 的关键词表，commit_stats、log_search 的关键词）；
  - GitHub/GitLab/ticket 的标签名（键；它们映射到的角色改了）；
  - 一个带固定摘要的一致性向量；
  - eval 里历史事故记录的 `owner: backend`。
- `git diff -U0 -M`，文件/处/+/−：

| 规则源码 | 组织定义和配置 | 提示词和文档 | 测试 | 框架其余 | 合计 |
|---|---|---|---|---|---|
| 6/6/+7/−7 | 23/40/+40/−40 | 16/18/+13/−13 | 0 | 86/145/+156/−156 | 131/209/+216/−216 |

  - 规则源码只算以角色名为键的规则表：`permissions.py`、`agent_jwt.py`、`credential_scoping.py`、`claude_permission_profiles.py`、`agent_card.py`、`seccomp_sandbox.py`。其余 `src/` 代码（默认角色、名单、路由、CLI 默认值）算框架其余。
- 漏改了谁会报错：没有一处会被编译器或类型检查拦住。角色名在 Bernstein 里全是字符串，没有一个是标识符。所以 209 处全是「漏改不报错」那一类。
  - 例子：漏改 `permissions.py` 的表键，`server_dev` 就不在表里，查表落到 `AgentPermissions()`，什么路径都能写（`permissions.py:218`）。grid3 反跑时实测过同一机制：`backend_c8` 不在表里时，F1 拒绝用例失败，它能改 `.github/`。
  - 漏改 `agent_jwt.py`，就落到兜底权限，少了 `tests:run`。
- 测试：选了 321 个文件：用到 "backend" 又 import 了改过的模块的 221 个，并上原先的 122 个相关文件。单进程。
  - 基线跑完：7625 过、30 跳过、1 败（`test_stale_heartbeat_reaps_agent`）。
  - 改名后：跑到第 57 个文件时按 mero 的要求停了，没跑完。已跑完的部分 2762 过、21 跳过、12 败、1 错。新增的 12 个失败都是测试里写死了 backend：
    - 用 backend 建任务，现在被 400 拒：`test_role_task_notifications` 5 条；
    - 断言默认角色等于 backend：`test_acp_bridge::test_default_role_is_backend`、`test_ab_test::test_defaults`、`test_gitlab_webhook_pipeline::test_mr_open_creates_one_task`；
    - `test_capability_matrix_spawn_refusal` 3 条：测试仍用旧名 backend，这个名字现在没有能力档，于是本该拒的派生不拒了（DID NOT RAISE SpawnError）。这正好演示了漏改不报错、管控悄悄失效。
    - `test_cross_adapter_orchestration`：少派生一个，原因没查清。
- 发现的不一致：
  - 角色名单写在很多处，彼此不由 `bernstein.yaml` 推出：`plan_schema.KNOWN_ROLES`、`a2a_jsonrpc.py:285` 的合法角色集合、coordinator 和 status_bar 的 worker 集合、changelog 的元组、quickstart 模板、`worker_cmd` 的默认名单、catalog 的亲和表、`sandbox_eval` 的队伍；
  - 约 60 处把「没写角色」默认成 backend；
  - `teams/*.toml` 以角色名为键钉模板哈希。
- Sherpa 等价物：基线上开 `probe-rename`（9ed78d9），`probe_rename_eq.py`。3 个文件、6 处、+6 −6：
  - 组织定义 2 处（`[[instance]]` 的 lower、`[seat]` 节名）；
  - 声明 1 处（`seat_write_limit` 的参数键）；
  - 提示词 3 处（卡的标题、manager 卡的名单和例子）。
  - 没改：实例 id `manager_to_backend`（标签）、卡的文件名（路径）。
  - 用例表 `sherpa_equivalent/tests/probe/rename_flow.tsv`，15 行改了名。没跑：Bernstein 测试停了以后队列交给了 razu。漏改参数键会不会被编译器拦，没实测（razu 在 Gas Town 对应物上读代码看是不报错）。

## 补：GRID4 汇报线的树（mero #25571，只建没跑）
`grid3-k<k>-p`，k=0、1、2、4、8，`grid4.py`。
- P1 用 `REPORTS_TO` 表：Bernstein 没有规则读得到的上下级，任何人都能给任何人派活，所以「派它的人」不等于上级。
- P2 全局一次。
- k=0 装两条规则是 2 个文件 +37 行；每多一个执行者 +1 行（`REPORTS_TO` 里它的一项）。
- 用例 `tests/test_report_line.py`，没跑。

## 补：GRID5 两族形式规则（mero #25667、#25753，11-20，只建没跑）
分支在 `_scale/bernstein/modified`：
- 通用族 `g5-k0-g<m>`、`g5-k<k>-g<k>`；
- 点名族 `g5-k0-n<m>`、`g5-k<k>-n<k>`；
- 都从 `grid3-k<k>-m0` 起。建法 `grid5_build.sh`（调 `grid5.py`）。
- 新文件 `core/tasks/form_rules.py`，查的位置和 grid3 一样：派单在认领时查（三条认领路径），交回在 complete 里查。
- 通用族 G<i>：`g<i>: <交出者自己的名字>`，核对等于真正交出的角色。全局一次，没有表。
- 点名族 N<i>：`n<i>: <口令>`，每条规则一张以角色名为键的表，照 `DEFAULT_ROLE_PERMISSIONS`（`permissions.py:155-198`）写。复制品各占一项，口令和 backend 相同，照 grid3 进原生表的做法。口令是占位词，由音节拼出，和角色名无关（`grid5.py` 的 `word()`）。
- 行数（比 `grid3-k<k>-m0` 多出的）：

| 树 | m=1 | m=2 | m=4 | m=8 |
|---|---|---|---|---|
| 通用族，k=0 | +51 | +53 | +57 | +65 |
| 通用族，k=m | +51 | +53 | +57 | +65 |
| 点名族，k=0 | +64 | +80 | +112 | +176 |
| 点名族，k=m | +65 | +84 | +128 | +240 |

  - 通用族每条规则 2 行，每多一个执行者 0 行。
  - 点名族每条规则一张表：10 个角色 10 行，加表头表尾和 2 行检查，共 16 行；每多一个执行者，每条规则多 1 行（k=m=8 时比 k=0 多 8×8=64 行）。
- 用例 `tests/test_grid5.py`，写好没跑：全对放行；第 1 条错拒；第 8 条错拒；点名族另有一条「用别种角色的口令」拒。
