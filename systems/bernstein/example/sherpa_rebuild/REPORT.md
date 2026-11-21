# Bernstein 的 Sherpa 等价物：报告

> vuna，2026-11-17 夜。规程第 12 节和后面三小节；方案和 mero 的答复见 `PLAN.md`；使用反馈见 `SHERPA_FEEDBACK.md`。
> 目录：`modified/`（git 仓库：`sherpa-pristine` 是量过的 Sherpa 原样副本，`baseline` 是加上等价物之后的版本，场景分支从 `baseline` 出发），`original/`（`git archive baseline` 解出来的只读副本），`tests/`（配对配置、用例表、结果），`wt-sN/`（各场景分支的 worktree，跑用例用）。
> 「跑过」指用 `_pairing/run_table.py` 在真的 Sherpa 内核上跑过（每条用例一个新的临时项目，真的 `ppo init`、真的内核命令）；「读代码」指只读过代码。

## 11-18 更正（mero #18875）

- **撤单能绕过 R3，已补。** 原来 `waits_for` 把撤掉的单也算「结束」（`waits_for/checks.tsv` 的 `ended=closed,cancelled`），上级一人撤掉被等的单，等它的审核单就能开工。Bernstein 不行：撤掉的依赖永远不算满足（`task_store_core.py:1484-1488`，实测 `../tests/acceptance/test_baseline_rows.py::test_C3_*`）。等价物比 Bernstein 松，是强制性不对等。
- 补法：声明末尾加 `[policy.waits_for] params = "ended=closed"`（+5 行，算搭建成本）。新提交 `0e6cb1c` 打成 `baseline`，旧的改名 `baseline-v1`（`465a373`）；八个场景分支和 `probe-r15-enabled` 都变基到新 `baseline`；`original/` 按新 `baseline` 重新解出。
- 基线表加两行：R3d（撤掉被等的单后开工，拒）、R7c（manager 派出再撤，交差照样放行，两边相同）。现在 20 行。全部用例表和自带测试重跑，结果见 `tests/runs/`、`tests/runs/tree_tests.txt`（旧的在 `tree_tests-baseline-v1.txt`）。
- 另两条撤单查过、两边相同或等价物更严：R7 撤掉的子任务两边都照样算拆过；R9 在 Bernstein 只是自动完成，父任务在等时 worker 直接交差照样成功（实测 `test_C9b_*`），等价物更严。
- 下面第 0 到 4 节写于 11-17，数是补之前的；基线表行数、搭建成本以本节为准。

## 0 先说结论和不等价之处

清单里的 9 条核心规则（R1、R2、R3、R4、R5、R7、R8、R9、R15），等价物全部覆盖：
- 7 条用包或内核表达，基线用例判决和 Bernstein 逐条相同；
- R8 由构造保证，没有为它加包；
- R5 只是近似。

没有一条记为「没有复现」。基线用例 18 条加 R15 打开时 2 条，共 20 条，跑过，判决全部和 Bernstein 相同。另有 2 条 Bernstein 的基线断言翻不过来，见下面第 1 点。八个场景都做成了：每个场景的用例表判决和 Bernstein 那边相同；基线表在各场景上重跑，变了的只有事先列明的行。

**不等价之处**（等价物比 Bernstein 严或松的地方）：
1. **派单的边。** Sherpa 只能沿声明的上下级派单，一个位置只能有一个上级；Bernstein 的任何 worker 都能给任何角色建任务（`tasks:claim` 等同 `tasks:write`，`self-create` 不校验角色名）。等价物在这里比 Bernstein 严，放宽不了。代价是 Bernstein 场景 7 的两条验收翻不过来：`test_backend_delegates_to_helper_and_waits` 和 `test_parent_not_done_while_helper_open`。它们在 Bernstein 的 baseline 上本来就通过，因为 backend 可以给一个连定义都没有的 `helper` 角色建子任务；在等价物的 baseline 上，backend 没有下级，这一步派单被拒（`classic_lifecycle.not_your_lower`）。这两条在等价物的场景 7 上是通过的。
2. **场景 6 插层之后。** Bernstein 的 manager 仍然可以绕过 team_lead 直接给 worker 建任务（提示词只是建议它别这么做）；等价物里 worker 改挂到 team_lead 下面，manager 不能再直接派。等价物更严。
3. **R5 只能操作自己的任务。** Bernstein 的 manager 令牌能操作所有任务；Sherpa 的上级只能做上级那几条命令（派单、收单、打回），不能替下级开工或交差。用例只翻了「worker 碰不了别人的单」这一面，判决相同；manager 那一面没有对应。
4. **R8 manager 的隔离。** Bernstein 是派生时检查有没有独立工作树或沙箱，没有就拒绝派生，收尾时把写进主检出的文件移进隔离目录。Sherpa 每张单开工都在自己的工作树里，没有命令能在主检出里开工，所以「拒绝」那一面在等价物里根本构造不出来。记为由构造保证，没有用例行。
5. **R9 父等子。** Bernstein 只在经 `self-create` 建子任务时让父任务等；worker 也可以用普通的 `POST /tasks` 建任务、不等。等价物用 `parallel_wait_all` 并排除 manager（manager 和 team_lead 是规划者，建完就交差，同 Bernstein），其余位置一旦派过单就必须等，没有「不等」的退路，比 Bernstein 严。
6. **R2 任务范围的默认值。** Bernstein 的任务没写 `owned_files` 时默认只许改 `src/`；Sherpa 派单必须写 `--scope`。用例里都写明了范围，判决相同。
7. **R15 审稿模型不同。** Bernstein 是任务完成后对改动做一次自动的跨模型审稿，审稿模型是配置里的 `reviewer_model`，写的模型是那个 agent 会话的模型。等价物是派审核单（`--reviews`）时，拿声明里的 `reviewer_model` 和被审单所在位置的模型比，模型表照抄 `bernstein.yaml` 的 `role_model_policy`。比的是声明里的值，不是会话实际用的模型。
8. **场景 4 的「同一个 agent」。** Bernstein 认的是认领时带的 agent 身份（`claim-batch` 的 `agent_id` 或 agent 令牌），审核任务按角色名 `reviewer` 认；等价物认的是位置，审核按 `--reviews` 认，检查点在派单时。Bernstein 有三个认领入口，等价物只有派单一个入口，所以 Bernstein 的两条验收翻成同一行（S4a）。
9. **场景 2 的两条。** Bernstein 的 `auto` 角色分类（`test_auto_role_no_longer_routes_to_removed_role`）在 Sherpa 里没有对应，没翻；计划文件校验（`test_plan_files_reject_removed_role_accept_others`）翻成派单被拒和派单放行两行，合并进 S2a、S2e。
10. **「去掉一条规则」两边做的事不同（场景 5）。** Bernstein 删的是框架代码（`cross_model_verifier.py` 里的 5 行检查）；等价物改的是声明（工作流 `requires` 里去掉 `review_model_differs`，1 行）。

## 1 核心功能清单（定死的）

组织：human → manager → 8 个平级下级（architect、security、backend、frontend、qa、reviewer、docs、devops），照 `bernstein.yaml:9-18`。

| 规则 | 依据（Bernstein 基线验收） | 等价物里怎么写 | 结论 |
|---|---|---|---|
| R1 角色可写路径 | `test_scenario_2/3` 在 baseline 上通过的条目 | `seat_write_limit`（复用 `_pairing/packs`），参数照抄 `permissions.py:155-196` 的 allow 表 | 相同（判决层面）；Bernstein 的 deny 表在起点上全落在 allow 表之外，所以只抄 allow 表 |
| R2 任务范围 | `test_scenario_5b::test_owned_files_scope_check_still_runs` | 现有 `write_scope` 加派单 `--scope` | 相同（判决层面），见不等价第 6 点 |
| R3 依赖 | `test_scenario_1/2/5` | 现有 `waits_for` | 相同。Bernstein 的 `depends_on` 也是声明式的，不声明就没有约束，所以不加强制规则（R3c 用例验了这一面） |
| R4 角色在名单里 | `test_scenario_1::test_task_server_still_rejects_undefined_role` | 内核：只能派给声明了 instance 的位置 | 相同 |
| R5 只能操作自己的任务 | `test_baseline_core::test_r5_*`（11-17 夜补） | 内核地板 `builtin.actor` | 近似，见不等价第 3 点 |
| R7 manager 必须拆出子任务 | `test_baseline_core::test_r7_*` | `must_decompose`（11-17 复现 Bernstein 时写的），`only = ["manager"]` | 相同 |
| R8 manager 隔离 | `test_baseline_core::test_r8_*` | 现有 `worktree`：由构造保证 | 由构造保证，见不等价第 4 点 |
| R9 父等子 | `test_scenario_7` 在 baseline 上通过的两条 | 现有 `parallel_wait_all`，`except = ["manager"]` | 近似，见不等价第 1、5 点 |
| R15 审稿模型不同（起点默认关） | `test_scenario_5` 打开该功能后的对照 | 新包 `review_model_differs`，装上不配置（默认关） | 近似，见不等价第 7 点 |

## 2 搭建成本（`count_sherpa.py modified sherpa-pristine baseline`）

内核、编译器、基础生命周期、13 个现有包改动 0 字节。

| 栏 | 文件 | 增 |
|---|---|---|
| 规则（3 个包） | 12 | 126 |
| 声明（工作流文件 95 行、`policy_pack.toml` 8 行、10 张卡片 486 行） | 12 | 589 |
| 测试（新包的 6 个 todo 用例） | 6 | 6 |

各包（行数含空行和注释）：

| 包 | 来源 | 检查代码 | 表和配置 | 用例 |
|---|---|---|---|---|
| `seat_write_limit` | `_pairing/packs`（ChatDev 那一对写的），复用 | 25 | 16 | 2 |
| `must_decompose` | 11-17 复现 Bernstein 的 `new_packs.patch`，复用；原用例依赖 `MigratedShapeB`，改成 todo | 19 | 15 | 2 |
| `review_model_differs` | 新写，已放进 `_pairing/packs/` | 34 | 17 | 2 |

卡片是用脚本从 Bernstein 的 `templates/roles/<角色>/system_prompt.md` 原文生成的，每张末尾加两三行 Sherpa 操作。

## 3 等价性检验（基线）

用例表 `tests/flow_baseline.tsv`（18 条）、`tests/r15_enabled.tsv`（2 条，在探测分支 `probe-r15-enabled` 上跑，该分支只在声明里打开 R15，不算场景），结果在同目录的 `*.results.tsv`。命令：`TMPDIR=... python3 _pairing/run_table.py tests/pairing.toml tests/flow_baseline.tsv`。

| 规则 | 用例 | 放行 / 拒绝 | 结果 |
|---|---|---|---|
| R1 | R1a backend 改 `src/`；R1b backend 改 `.github/`；R1c qa 改 `.github/`；R1d frontend 改 `package.json`；R1e reviewer 改 `.github/`（表外角色不受限） | 放、拒、拒、放、放 | 全部相同 |
| R2 | R2a 范围内；R2b 范围外 | 放、拒（`write_scope.staged_outside_writable`） | 相同 |
| R3 | R3a 依赖没完成；R3b 完成后；R3c 没声明依赖 | 拒（`waits_for.not_ended`）、放、放 | 相同 |
| R4 | R4a 派给 backend；R4b 派给没定义的 `ghost_role` | 放、拒（`classic_lifecycle.not_your_lower`） | 相同 |
| R5 | R5a 开自己的单；R5b 开 qa 的单 | 放、拒（`builtin.actor`） | 相同 |
| R7 | R7a 派过单再交差；R7b 没派单就交差 | 放、拒（`must_decompose.nothing_dispatched`） | 相同 |
| R9 | R9a manager 在下级没结束时交差（Bernstein 的 manager 不等） | 放 | 相同 |
| R15 | R15c 默认关时同模型审稿；R15a 打开后同模型；R15b 打开后不同模型 | 放、拒（`review_model_differs.same_model`）、放 | 相同 |

翻不过来的：Bernstein 场景 7 的两条，见第 0 节不等价第 1 点。R8 由构造保证，没有用例行。

被测树自带的两套测试（`baseline` 上）：内核 `Tests` 130 通过、1 跳过；包仓 `SherpaPolicyPackOrganizer/Tests` 53 通过、11 跳过。原样副本 `sherpa-pristine` 上包仓是 53 通过、5 跳过，多出的 6 条跳过就是 3 个新包各 2 条 todo 用例。

## 4 八个场景

每个场景从 `baseline` 开分支，分支名和 Bernstein 那边一样。用例表 `tests/scenario_N.tsv` 是 Bernstein 那个场景的验收逐条翻过来的；基线表 `flow_baseline.tsv` 在每个场景上也重跑。结果在 `tests/runs/sN/`，命令 `tests/run_scenario.sh N`。

事先列明的基线表变化：场景 2 的 R1d（frontend 没了，前置派单报错）；场景 6 的所有「manager 直接派 worker」的行（worker 改挂到 team_lead 下面）。其余场景不该有变化。

| 场景 | 等价物怎么做 | 场景用例 | 基线表重跑 |
|---|---|---|---|
| 1 加 `security_reviewer` | 加 instance、卡片；`seat_write_limit` 加 `security_reviewer=tests,docs`；manager 卡片加一行 | 7 条，全部相同 | 18 条全相同 |
| 2 去掉 `frontend` | 删 instance、seat、卡片、`seat_write_limit` 里的一项；manager 卡片删一行 | 5 条，全部相同 | 只有 R1d 变（事先列明） |
| 3 backend 不许改 `pyproject.toml` | `seat_write_limit` 参数改一项 | 4 条，全部相同 | 18 条全相同 |
| 4 审核不能给写的人 | 工作流 `requires` 加现有 `review_rules` | 3 条，全部相同 | 18 条全相同 |
| 5 去掉 R15 | 工作流 `requires` 去掉 `review_model_differs` | 4 条，全部相同 | 18 条全相同 |
| 6 插入 `team_lead` | 8 条 instance 的上级改成 team_lead，加 manager → team_lead；`must_decompose` 的 `only`、`parallel_wait_all` 的 `except` 加 team_lead；`seat_write_limit` 加 team_lead；manager 卡片加一行；team_lead 卡片 | 7 条，全部相同 | 事先列明的 16 行变；把这 18 行改成经 team_lead 派单后（`extra_s6_flow_via_team_lead.tsv`）18 条全相同 |
| 7 backend 带 `helper` | 加 backend → helper；`seat_write_limit` 加 helper；backend 卡片加一节；helper 卡片 | 7 条，全部相同 | 18 条全相同 |
| 8 1 加 4 | 挑场景 1、4 的提交，不需要另加一行：`review_rules` 不点名位置，自动管到新位置 | 12 条（场景 1 的 7 条、场景 4 的 3 条、新位置受新规则管的 2 条），全部相同 | 18 条全相同 |

被测树自带的两套测试在八个场景分支上全部和 `baseline` 一致：内核 `Tests` 每个分支都是 130 通过、1 跳过；包仓 `SherpaPolicyPackOrganizer/Tests` 每个分支都是 53 通过、11 跳过。跑过，单进程，原始输出 `tests/runs/tree_tests.txt`。

### 计数，和 Bernstein 并排

等价物按 Sherpa 四栏（`count_sherpa.py modified baseline <分支>`，`tests/counts.tsv`）：内核、规则、编译器和基础生命周期三栏在八个场景里都是 0，改动全在声明栏。Bernstein 那边的数取自 `../tests/counts.md`（「全部」含测试和生成的镜像文档；「不含」是去掉这两类之后）。

| 场景 | Bernstein 全部：文件 / 处 / 增 / 删 | Bernstein 不含测试和镜像：文件 / 增 / 删 | 等价物：文件 / 处 / 增 / 删（全在声明栏） | 等价物其中卡片 |
|---|---|---|---|---|
| 1 | 14 / 14 / 107 / 1 | 8 / 101 / 0 | 3 / 4 / 54 / 1 | 2 个文件 +45 |
| 2 | 13 / 13 / 3 / 117 | 7 / 0 / 109 | 3 / 5 / 1 / 54 | 2 个文件 −45 |
| 3 | 2 / 2 / 5 / 1 | 1 / 1 / 1 | 1 / 1 / 1 / 1 | 0 |
| 4 | 2 / 11 / 40 / 0 | 2 / 40 / 0 | 1 / 1 / 1 / 1 | 0 |
| 5 | 2 / 2 / 0 / 16 | 1 / 0 / 5 | 1 / 1 / 1 / 1 | 0 |
| 6 | 17 / 20 / 220 / 6 | 11 / 214 / 5 | 3 / 4 / 167 / 18 | 2 个文件 +141 |
| 7 | 14 / 14 / 111 / 1 | 8 / 105 / 0 | 3 / 4 / 53 / 1 | 2 个文件 +44 |
| 8 | 16 / 25 / 147 / 1 | 10 / 141 / 0 | 4 / 5 / 55 / 2 | 2 个文件 +45 |

说明：
- 两边的卡片和提示词都是从 Bernstein 的提示词原文来的，大头相同。
- Bernstein 那边还要改源码里的按角色表（`KNOWN_ROLES`、两张权限表、`_WRITE_BOUNDARY_ROLES`、`_PLANNING_ROLES` 等），并重新生成 5 份镜像文档。等价物只改声明。
- 场景 4、5 两边差得最多：Bernstein 要在框架里加或删代码，等价物各改一行声明。
- 场景 8 在 Bernstein 那边要多一行，把新角色加进 `_REVIEW_ROLES`；等价物不用。

## 5 拿不准的

- R15 的等价程度（不等价第 7 点）：两边比的东西不同，一边是会话实际用的模型，一边是声明里的模型表，只在「配置相同就拒」这一层判决相同。
- 场景 7 的两条 Bernstein 验收在等价物 baseline 上翻不过来，是放宽不了的结构差别，不是做错。
