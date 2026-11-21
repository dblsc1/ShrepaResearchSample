# Paperclip 大体量

> paperclip-bela，2026-11-18，回 mero #19331 / #19388 / #19423。做法定义见同目录 `PLAN.md`（mero #19423 确认）。
> 行号对 Paperclip 提交 `dc9971bd`（标签 `baseline`），服务端路径省略 `server/src/`。标「实测」的有输出文件；标「读代码」的没跑过。

## 0 结论

- 四个变更都只改团队定义文件（`TEAM.md`、`agents/<slug>/AGENTS.md`、`.paperclip.yaml`），**源码 0 行**。
- 随规模长的：**按角色配的规则**（每个角色 8 行，`.paperclip.yaml` 一个文件，k=16 时 +392）和**加一层**（每组组长的 `AGENTS.md` 改 1 行 `reportsTo`，k=16 时 19 个文件 +34/−16）。不长的：加一个角色（3 个文件 +17）、复制一整组（5 个文件 +54）。
- **只用定义文件，「只能派给自己的下级」不起作用**（配置 (a)，实测）：越级 6 类里只有 V5（评审交给写的人）被拒，其余 5 类全放，各规模都是「每组 1 条拒」（k=16：16/96）。
- **加上每个 agent 2 个 API 请求撤宽授权**（配置 (b)，请求数随角色数长，k=16 是 98 个请求）：拒 V1、V3、V5、V6；**V2（总负责人越过组长直接派给下级）、V4（总负责人越过组长收下级的任务）照样放**，这是 Paperclip 的设计，和 Sherpa 相反。k=16：64/96。合法动作两种配置下全放（96/96）。
- 「审的人不是写的人」在引擎里，不看角色名：新角色、新层、新组在 (a)(b) 下都自动受管（实测，每个变更、每个规模）。
- **按角色配的规则第一版跑不起来**：给每个角色一块工作区外的可写目录，Paperclip 生成沙箱时直接拒（实测，`adapter-utils/src/local-process-sandbox.ts:363-377`）。改成每个角色一块只读目录后能跑。「每个角色只写自己那块」在 Paperclip 里写不出来，见 4.1。
- 按角色配规则还有一个副作用：要用沙箱就得把每个 agent 的运行时从 `paperclip_runner` 换成本地适配器 `claude_local`（`services/agent-runner-selection.ts:350`），见 4.2。

## 1 怎么放大、标签和分支

- 形状：1 个 `head-of-engineering` 带 k 组，每组是仓库自带团队 `product-engineering` 的三个人（`cto-g<i>`、`senior-coder-g<i>`、`qa-g<i>`）。角色数 1 + 3k。依据：`packages/teams-catalog/catalog/bundled/software-development/product-engineering/TEAM.md:32` 说这个团队装在已有的 CEO 或经理下面。
- 生成器 `gen_team.py <仓库> <k> [变更]` 写出 `packages/teams-catalog/catalog/bundled/software-development/scale-engineering/`，再用包自带的 `pnpm run build:manifest` 重新生成 `packages/teams-catalog/generated/catalog.json`。
- 每个 agent 在 `.paperclip.yaml` 里标 `permissions.authorizationPolicy.assignmentPolicy.mode: protected`（5 行），这是 Paperclip 自己的「只能按授权派」开关（`services/authorization.ts:390-395`）。导入时这个设置带过去了（实测：每次运行的 `SCALE org` 行，`assignmentPolicy` 都是 `protected`）。
- `make_sizes.sh 1 2 4 8 16`：在 `paperclip/modified` 从 `baseline` 出发，每个 k 一个提交、打标签 `size-k`；每个变更从标签拉分支 `size-k-<变更>`、一个提交。作者 `research-bot`，只在本地，不推送。

| 标签 | 提交 | 组数 | 角色数 |
|---|---|---|---|
| baseline | dc9971bdb8 | — | — |
| size-1 | 1aa806c669 | 1 | 4 |
| size-2 | a220d702b8 | 2 | 7 |
| size-4 | 00ea482d0e | 4 | 13 |
| size-8 | 9b36b3f83e | 8 | 25 |
| size-16 | c05d6bb0b1 | 16 | 49 |

各分支的提交号在 `runs/<分支>/HEAD.txt`（每次运行记下的 `git rev-parse HEAD`）。

## 2 改动规模

只用 `git diff --numstat <标签>..<分支>`（`measure.py`，输出 `counts.tsv`）。每行拆成源码 / 配置 / 提示词：`.paperclip.yaml` 算配置；`AGENTS.md`、`TEAM.md` 的 frontmatter（两条 `---` 之间）算配置，正文算提示词。`generated/catalog.json` 单列，不进主数。本次没有测试文件进分支（验收测试在运行时复制进去、跑完删掉，见第 3 节）。

| 规模 | 组数 | 角色数 | 变更 | 文件 | + | − | 其中源码 / 配置 / 提示词（+/−） | 生成文件 catalog.json（文件/+/−，不进主数） | 验收 | 命令（在 paperclip/modified 下） |
|---|---|---|---|---|---|---|---|---|---|---|
| size-1 | 1 | 4 | 加一个角色 | 3 | 17 | 0 | +0/-0 / +15/-0 / +2/-0 | 1/+15/-7 | 新角色的活同组评审放、自评拒；(b) 本组组长派给它放、非上级派给它拒 | `git diff --numstat size-1..size-1-add-role` |
| size-1 | 1 | 4 | 按角色配的规则 | 1 | 32 | 0 | +0/-0 / +32/-0 / +0/-0 | 1/+4/-4 | 每个角色的沙箱只读挂自己那块、可写只有工作区（参数级）；rw 版生成沙箱时被拒 | `git diff --numstat size-1..size-1-per-role-rule` |
| size-1 | 1 | 4 | 加一层 | 4 | 19 | 1 | +0/-0 / +17/-1 / +2/-0 | 1/+18/-9 | director 的活交上级评审放、自评拒；(b) director 派组长放、组长派 director 拒 | `git diff --numstat size-1..size-1-add-layer` |
| size-1 | 1 | 4 | 复制一整组 | 5 | 54 | 0 | +0/-0 / +48/-0 / +6/-0 | 1/+38/-11 | 新组评审放、自评拒；(b) 新组长派本组放、旧组长派新组拒 | `git diff --numstat size-1..size-1-add-group` |
| size-2 | 2 | 7 | 加一个角色 | 3 | 17 | 0 | +0/-0 / +15/-0 / +2/-0 | 1/+15/-7 | 新角色的活同组评审放、自评拒；(b) 本组组长派给它放、非上级派给它拒 | `git diff --numstat size-2..size-2-add-role` |
| size-2 | 2 | 7 | 按角色配的规则 | 1 | 56 | 0 | +0/-0 / +56/-0 / +0/-0 | 1/+4/-4 | 每个角色的沙箱只读挂自己那块、可写只有工作区（参数级）；rw 版生成沙箱时被拒 | `git diff --numstat size-2..size-2-per-role-rule` |
| size-2 | 2 | 7 | 加一层 | 5 | 20 | 2 | +0/-0 / +18/-2 / +2/-0 | 1/+20/-11 | director 的活交上级评审放、自评拒；(b) director 派组长放、组长派 director 拒 | `git diff --numstat size-2..size-2-add-layer` |
| size-2 | 2 | 7 | 复制一整组 | 5 | 54 | 0 | +0/-0 / +48/-0 / +6/-0 | 1/+38/-11 | 新组评审放、自评拒；(b) 新组长派本组放、旧组长派新组拒 | `git diff --numstat size-2..size-2-add-group` |
| size-4 | 4 | 13 | 加一个角色 | 3 | 17 | 0 | +0/-0 / +15/-0 / +2/-0 | 1/+15/-7 | 新角色的活同组评审放、自评拒；(b) 本组组长派给它放、非上级派给它拒 | `git diff --numstat size-4..size-4-add-role` |
| size-4 | 4 | 13 | 按角色配的规则 | 1 | 104 | 0 | +0/-0 / +104/-0 / +0/-0 | 1/+4/-4 | 每个角色的沙箱只读挂自己那块、可写只有工作区（参数级）；rw 版生成沙箱时被拒 | `git diff --numstat size-4..size-4-per-role-rule` |
| size-4 | 4 | 13 | 加一层 | 7 | 22 | 4 | +0/-0 / +20/-4 / +2/-0 | 1/+24/-15 | director 的活交上级评审放、自评拒；(b) director 派组长放、组长派 director 拒 | `git diff --numstat size-4..size-4-add-layer` |
| size-4 | 4 | 13 | 复制一整组 | 5 | 54 | 0 | +0/-0 / +48/-0 / +6/-0 | 1/+38/-11 | 新组评审放、自评拒；(b) 新组长派本组放、旧组长派新组拒 | `git diff --numstat size-4..size-4-add-group` |
| size-8 | 8 | 25 | 加一个角色 | 3 | 17 | 0 | +0/-0 / +15/-0 / +2/-0 | 1/+15/-7 | 新角色的活同组评审放、自评拒；(b) 本组组长派给它放、非上级派给它拒 | `git diff --numstat size-8..size-8-add-role` |
| size-8 | 8 | 25 | 按角色配的规则 | 1 | 200 | 0 | +0/-0 / +200/-0 / +0/-0 | 1/+4/-4 | 每个角色的沙箱只读挂自己那块、可写只有工作区（参数级）；rw 版生成沙箱时被拒 | `git diff --numstat size-8..size-8-per-role-rule` |
| size-8 | 8 | 25 | 加一层 | 11 | 26 | 8 | +0/-0 / +24/-8 / +2/-0 | 1/+32/-23 | director 的活交上级评审放、自评拒；(b) director 派组长放、组长派 director 拒 | `git diff --numstat size-8..size-8-add-layer` |
| size-8 | 8 | 25 | 复制一整组 | 5 | 54 | 0 | +0/-0 / +48/-0 / +6/-0 | 1/+38/-11 | 新组评审放、自评拒；(b) 新组长派本组放、旧组长派新组拒 | `git diff --numstat size-8..size-8-add-group` |
| size-16 | 16 | 49 | 加一个角色 | 3 | 17 | 0 | +0/-0 / +15/-0 / +2/-0 | 1/+15/-7 | 新角色的活同组评审放、自评拒；(b) 本组组长派给它放、非上级派给它拒 | `git diff --numstat size-16..size-16-add-role` |
| size-16 | 16 | 49 | 按角色配的规则 | 1 | 392 | 0 | +0/-0 / +392/-0 / +0/-0 | 1/+4/-4 | 每个角色的沙箱只读挂自己那块、可写只有工作区（参数级）；rw 版生成沙箱时被拒 | `git diff --numstat size-16..size-16-per-role-rule` |
| size-16 | 16 | 49 | 加一层 | 19 | 34 | 16 | +0/-0 / +32/-16 / +2/-0 | 1/+48/-39 | director 的活交上级评审放、自评拒；(b) director 派组长放、组长派 director 拒 | `git diff --numstat size-16..size-16-add-layer` |
| size-16 | 16 | 49 | 复制一整组 | 5 | 54 | 0 | +0/-0 / +48/-0 / +6/-0 | 1/+34/-7 | 新组评审放、自评拒；(b) 新组长派本组放、旧组长派新组拒 | `git diff --numstat size-16..size-16-add-group` |

各变更具体改了什么：

- **加一个角色**：第 1 组加 `release-engineer-g1`。新 `AGENTS.md`（frontmatter 9 行 + 正文 2 行）、`TEAM.md` 的 `includes` 加 1 行、`.paperclip.yaml` 加它的 5 行 protected。
- **按角色配的规则**：`.paperclip.yaml` 里每个 agent 加 8 行 `adapter` 块（`type: claude_local`、`runner: legacy`、`filesystemScope: workspace`、一条 `filesystemExtraPaths`，路径按角色不同）。行数 = 8 × 角色数。
- **加一层**：加 `director`（`reportsTo: head-of-engineering`），每个组长的 `AGENTS.md` 改 1 行 `reportsTo`。文件数 = 3 + k，−k 行。
- **复制一整组**：第 k+1 组，3 个新 `AGENTS.md`、`TEAM.md` 加 3 行、`.paperclip.yaml` 加 15 行。

`catalog.json` 加一层那栏随 k 长：清单里每个文件记了 `sizeBytes` 和 `sha256`，k 个组长的 `AGENTS.md` 各变一次，各多 2 行 + 2 行 −（`git diff size-2..size-2-add-layer -- packages/teams-catalog/generated/catalog.json`）。复制一整组在 k=16 是 +34/−7、其他规模 +38/−11，差的 4 行没细查。

## 3 验收和越级表

测试 `tests/scale.test.ts`，运行时由 `run_scale.sh` 复制到 `server/src/__tests__/zz-scale/`，跑完删掉，不进分支。用 Paperclip 真代码：嵌入式 Postgres、真的目录安装器装生成的团队（`include.skills: false`，理由同主报告第 2 节：技能导入在本机每次要几分钟，和治理无关）、真的授权服务 `authorizationService(db).decide`（参数形状同 `routes/issues.ts:5084-5097`）、真的任务路由 `PATCH /api/issues/:id`、真的执行策略引擎。输出 `runs/<分支>/scale.log`（`SCALE` 开头的行）和 `scale.json`。`collect.py` 汇总。

### 3.1 两种配置

- **(a) 只用定义文件**。
- **(b) (a) 加上每个 agent 撤两条宽授权**：`tasks:assign`（不带范围）和 `tasks:manage_active_checkouts`。测试里直接删 `principal_permission_grants` 表里这两行。等价的 API（读代码）是每个 agent 2 个请求，都要 board 身份：
  - `PATCH /api/agents/:id/permissions`，body `{"canCreateAgents": false, "canAssignTasks": false}`（`routes/agents.ts:5034`，`:5076-5091` 据此删掉 `tasks:assign`）；
  - `PATCH /api/agents/:id/permission-grants`，body `{"permissionKey": "tasks:manage_active_checkouts", "enabled": false}`（`routes/agent-permission-grants.ts:14`，一次只改一个键，`:53-58`）。
  - 请求数 = 2 × 角色数：k=1 8 个，k=2 14，k=4 26，k=8 50，k=16 98。以后每加一个角色再加 2 个。这些请求是旁注，不进第 2 节的主数。
  - 为什么非走 API 不可：新 agent 激活时一律拿 15 条默认授权，含这两条（`services/agent-hiring.ts:86-99`）；导入只加授权、不撤（`services/company-portability.ts:3598-3616`）。

### 3.2 越级表

用例名和 `_scale/sherpa/gen_cases.py` 一样，每组一套（k=1 没有别组，V1/P1 不跑，V6 改成派给本组 QA）：

- V1 组长派给别组下级 / P1 组长派给本组下级（授权判定）
- V2 总负责人越过组长派给下级 / P2 总负责人派给组长（授权判定）
- V3 下级把组长名下进行中的任务改成 done / P3 下级改自己的（任务路由）
- V4 总负责人把下级的任务改成 done / P4 组长把本组下级的改成 done（任务路由）
- V5 评审阶段只有执行人自己 / P5 评审阶段 [执行人, QA]（执行策略引擎）
- V6 下级派给别组下级 / P6 下级派给自己（授权判定）

拒 = 越级被拦下的条数 / 越级总条数；合法 = 合法动作放行的条数 / 总条数。

| 规模 | 组数 | 角色数 | 变更 | (a) 拒 | (a) 合法 | (b) 拒 | (b) 合法 | (b) 各类拒（V1 V2 V3 V4 V5 V6） | 装团队秒数 |
|---|---|---|---|---|---|---|---|---|---|
| size-1 | 1 | 4 | — | 1/5 | 5/5 | 3/5 | 5/5 | V1:- V2:0/1 V3:1/1 V4:0/1 V5:1/1 V6:1/1 | 210 |
| size-1-add-role | 1 | 5 | 加一个角色 | 1/5 | 5/5 | 3/5 | 5/5 | V1:- V2:0/1 V3:1/1 V4:0/1 V5:1/1 V6:1/1 | 210 |
| size-1-per-role-rule | 1 | 4 | 按角色配的规则 | 1/5 | 5/5 | 3/5 | 5/5 | V1:- V2:0/1 V3:1/1 V4:0/1 V5:1/1 V6:1/1 | 201 |
| size-1-add-layer | 1 | 5 | 加一层 | 1/5 | 5/5 | 3/5 | 5/5 | V1:- V2:0/1 V3:1/1 V4:0/1 V5:1/1 V6:1/1 | 206 |
| size-1-add-group | 2 | 7 | 复制一整组 | 2/12 | 12/12 | 8/12 | 12/12 | V1:2/2 V2:0/2 V3:2/2 V4:0/2 V5:2/2 V6:2/2 | 204 |
| size-2 | 2 | 7 | — | 2/12 | 12/12 | 8/12 | 12/12 | V1:2/2 V2:0/2 V3:2/2 V4:0/2 V5:2/2 V6:2/2 | 201 |
| size-2-add-role | 2 | 8 | 加一个角色 | 2/12 | 12/12 | 8/12 | 12/12 | V1:2/2 V2:0/2 V3:2/2 V4:0/2 V5:2/2 V6:2/2 | 205 |
| size-2-per-role-rule | 2 | 7 | 按角色配的规则 | 2/12 | 12/12 | 8/12 | 12/12 | V1:2/2 V2:0/2 V3:2/2 V4:0/2 V5:2/2 V6:2/2 | 202 |
| size-2-add-layer | 2 | 8 | 加一层 | 2/12 | 12/12 | 8/12 | 12/12 | V1:2/2 V2:0/2 V3:2/2 V4:0/2 V5:2/2 V6:2/2 | 203 |
| size-2-add-group | 3 | 10 | 复制一整组 | 3/18 | 18/18 | 12/18 | 18/18 | V1:3/3 V2:0/3 V3:3/3 V4:0/3 V5:3/3 V6:3/3 | 204 |
| size-4 | 4 | 13 | — | 4/24 | 24/24 | 16/24 | 24/24 | V1:4/4 V2:0/4 V3:4/4 V4:0/4 V5:4/4 V6:4/4 | 202 |
| size-4-add-role | 4 | 14 | 加一个角色 | 4/24 | 24/24 | 16/24 | 24/24 | V1:4/4 V2:0/4 V3:4/4 V4:0/4 V5:4/4 V6:4/4 | 202 |
| size-4-per-role-rule | 4 | 13 | 按角色配的规则 | 4/24 | 24/24 | 16/24 | 24/24 | V1:4/4 V2:0/4 V3:4/4 V4:0/4 V5:4/4 V6:4/4 | 204 |
| size-4-add-layer | 4 | 14 | 加一层 | 4/24 | 24/24 | 16/24 | 24/24 | V1:4/4 V2:0/4 V3:4/4 V4:0/4 V5:4/4 V6:4/4 | 201 |
| size-4-add-group | 5 | 16 | 复制一整组 | 5/30 | 30/30 | 20/30 | 30/30 | V1:5/5 V2:0/5 V3:5/5 V4:0/5 V5:5/5 V6:5/5 | 202 |
| size-8 | 8 | 25 | — | 8/48 | 48/48 | 32/48 | 48/48 | V1:8/8 V2:0/8 V3:8/8 V4:0/8 V5:8/8 V6:8/8 | 202 |
| size-8-add-role | 8 | 26 | 加一个角色 | 8/48 | 48/48 | 32/48 | 48/48 | V1:8/8 V2:0/8 V3:8/8 V4:0/8 V5:8/8 V6:8/8 | 203 |
| size-8-per-role-rule | 8 | 25 | 按角色配的规则 | 8/48 | 48/48 | 32/48 | 48/48 | V1:8/8 V2:0/8 V3:8/8 V4:0/8 V5:8/8 V6:8/8 | 203 |
| size-8-add-layer | 8 | 26 | 加一层 | 8/48 | 48/48 | 32/48 | 48/48 | V1:8/8 V2:0/8 V3:8/8 V4:0/8 V5:8/8 V6:8/8 | 206 |
| size-8-add-group | 9 | 28 | 复制一整组 | 9/54 | 54/54 | 36/54 | 54/54 | V1:9/9 V2:0/9 V3:9/9 V4:0/9 V5:9/9 V6:9/9 | 206 |
| size-16 | 16 | 49 | — | 16/96 | 96/96 | 64/96 | 96/96 | V1:16/16 V2:0/16 V3:16/16 V4:0/16 V5:16/16 V6:16/16 | 208 |
| size-16-add-role | 16 | 50 | 加一个角色 | 16/96 | 96/96 | 64/96 | 96/96 | V1:16/16 V2:0/16 V3:16/16 V4:0/16 V5:16/16 V6:16/16 | 208 |
| size-16-per-role-rule | 16 | 49 | 按角色配的规则 | 16/96 | 96/96 | 64/96 | 96/96 | V1:16/16 V2:0/16 V3:16/16 V4:0/16 V5:16/16 V6:16/16 | 206 |
| size-16-add-layer | 16 | 50 | 加一层 | 16/96 | 96/96 | 64/96 | 96/96 | V1:16/16 V2:0/16 V3:16/16 V4:0/16 V5:16/16 V6:16/16 | 213 |
| size-16-add-group | 17 | 52 | 复制一整组 | 17/102 | 102/102 | 68/102 | 102/102 | V1:17/17 V2:0/17 V3:17/17 V4:0/17 V5:17/17 V6:17/17 | 208 |

所有分支上，(a) 的拒只来自 V5；(b) 的 V2、V4 全放。逐条输出在 `runs/<分支>/scale.log` 的 `SCALE case.a` / `SCALE case.b` 行。

(b) 下各类拒的原因（`case.b` 行里的 `reason` / `code`，实测）：

- V1、V6：`deny_policy_restricted`，派单人的 `tasks:assign_scope` 只覆盖自己的子树（`services/authorization.ts:502-527` 调 `:400-415`）。
- V3：HTTP 409「Another agent's run owns this task (Run checkout lock)」。拦它的是任务的检出规则：(b) 撤了 `tasks:manage_active_checkouts`，下级不能动别人检出的任务。不是层级判断。
- V5：执行策略引擎排除执行人，评审阶段没有别人可选（「No eligible review participant is configured for this issue」）。
- V2 放：授权按派单人的整棵子树算，下级在总负责人的子树里。
- V4 放：任务路由对别人名下的任务先问 `tasks:manage_active_checkouts`（`routes/issues.ts:5869-5878` 调 `:5780-5791`），授权服务对汇报链上方的 agent 直接放（`services/authorization.ts:2705-2716`，`reason: allow_manager_chain`，不看授权表），所以 (b) 撤了授权也挡不住。P4（组长收本组下级的任务）放也是同一条。

### 3.3 每个变更的验收

都在两种配置下跑（`SCALE change.a` / `SCALE change.b` 行），所有规模结果一样：

| 变更 | 放的一条 | 拒的一条 | (a) | (b) |
|---|---|---|---|---|
| 加一个角色 | `release-engineer-g1` 的活，评审阶段 [它, QA G1]，交给 QA G1 | 评审阶段只有它自己 | 放 / 拒 | 放 / 拒 |
| 加一个角色（派单） | CTO G1 派给它 | 别组组长（k=1 时是 Senior Coder G1）派给它 | 放 / **放** | 放 / 拒 |
| 加一层 | director 的活，评审阶段 [director, Head]，交给 Head | 评审阶段只有 director | 放 / 拒 | 放 / 拒 |
| 加一层（派单） | director 派给 CTO G1 | CTO G1 派给 director（往上派） | 放 / **放** | 放 / 拒 |
| 复制一整组 | 新组 Senior Coder 的活，评审 [它, 新组 QA] | 评审阶段只有它自己 | 放 / 拒 | 放 / 拒 |
| 复制一整组（派单） | 新组组长派给本组下级 | CTO G1 派给新组下级 | 放 / **放** | 放 / 拒 |
| 按角色配的规则 | 每个角色的沙箱：工作区可写，自己那块只读挂进来 | 别的角色那块不挂（看不到） | 放 / 拒（同一套参数） | 同 (a) | | | |

(a) 下派单的「拒的一条」都放了，这就是 3.2 里 (a) 层级不起作用的同一件事。

### 3.4 按角色配的规则

测试拿装好的每个 agent 的 `adapterConfig`，交给 Paperclip 自己的 `buildLocalProcessSandboxSpawnTarget`（`packages/adapter-utils/src/local-process-sandbox.ts`），看它生成的 bubblewrap 参数（`--bind` 可写、`--ro-bind` 只读、根是不是 `--tmpfs /`）。`/srv/team-shared/<区>` 映射到临时目录。结果在 `runs/size-k-per-role-rule/scale.log` 的 `SCALE perRoleRule` 行（实测）：

| 规模 | 角色数 | 运行时 | 可写只有工作区 | 只读挂的正好是自己那块 | 根是 tmpfs | 生成沙箱被拒 |
|---|---|---|---|---|---|---|
| size-1 | 4 | 全是 `claude_local` | 4/4 | 4/4 | 4/4 | 0 |
| size-2 | 7 | 全是 `claude_local` | 7/7 | 7/7 | 7/7 | 0 |
| size-4 | 13 | 全是 `claude_local` | 13/13 | 13/13 | 13/13 | 0 |
| size-8 | 25 | 全是 `claude_local` | 25/25 | 25/25 | 25/25 | 0 |
| size-16 | 49 | 全是 `claude_local` | 49/49 | 49/49 | 49/49 | 0 |

区按角色分：Head → docs，CTO → plans，Senior Coder → src，QA → tests。「只读挂的正好是自己那块」是逐个角色核对的：临时目录下只有自己那一条 `--ro-bind`，别的角色的区不在参数里，根又是 tmpfs，所以看不到。

rw 版（分支 `size-k-per-role-rule-rw`，5 个规模）：这个测试在第一个角色上就报错退出（`Tests 1 failed | 2 passed (3)`），错误是 `Writable sandbox path "<tmp>/shared/src" is outside synchronized workspace "<tmp>/workspace" and has no outbound restore mapping.`（`local-process-sandbox.ts:373`）。那时测试还没包 try/catch，所以 rw 版只记了第一个被拒的角色。同一分支上越级表和变更验收那两条测试照样过。

只到参数这一层：本机 bubblewrap 起不来（4.2），没有真的拦住一次读写。

## 4 对 Paperclip 不利、照写

### 4.1 「每个角色只写自己那块」写不出来

- 第一版给每个角色一块工作区外的可写目录（`/srv/team-shared/<区>`，`access: rw`，分支 `size-k-per-role-rule-rw`，结果在 `runs/size-k-per-role-rule-rw/`）。Paperclip 生成沙箱时报错：`Writable sandbox path "…/shared/plans" is outside synchronized workspace "…/workspace" and has no outbound restore mapping.`（实测，5 个规模都一样；`packages/adapter-utils/src/local-process-sandbox.ts:363-377`）。真跑时这个 agent 起不来。
- 「outbound restore mapping」来自远程执行环境的工作区实现（`services/workspace-realization.ts:202`、`services/environment-run-orchestrator.ts:728`），不是团队定义文件能写的（读代码）。
- 可写目录放进工作区里面倒是允许，但 `filesystemScope: workspace` 本来就让整个工作区可写，再加工作区里的子目录不会让范围变窄。所以同一个工作区里「写代码的只写 src、QA 只写 tests」这种按角色分的写范围，Paperclip 的定义文件表达不了（读代码）。
- 现在的版本（分支 `size-k-per-role-rule`）退一步：每个角色只读挂自己那块目录，看不到别的角色的目录；写只在工作区里。这是「每个角色各配自己的参数」，但管的是读不是写，比要求弱。两版的 `git diff --numstat` 行数一样（只差 `rw` / `ro` 一个词）。

### 4.2 按角色配的规则要换运行时

- 沙箱只有本地适配器有，`paperclip_runner` 不支持（`services/agent-runner-selection.ts:350`）。所以按角色配的规则把每个 agent 的 `adapter.type` 从默认的 `paperclip_runner` 换成 `claude_local`，`runner: legacy`。这是副作用：agent 的运行方式变了，不只是多了一条规则。
- 本机 bubblewrap 起不来（`No permissions to create a new namespace`，主报告第 7 节），验收只检查 Paperclip 生成的沙箱参数，没有真的拦住一次写或读。

### 4.3 其他

- 层级要靠 API 补：只用定义文件，层级不起作用（3.2 (a)）；补上要每个 agent 2 个 API 请求，以后每加一个角色还要再补，定义文件里看不出来。
- V2、V4 放：越级派单、越级收任务，Paperclip 设计上允许。
- (b) 的撤授权在测试里是直接写表，没有走 HTTP；API 请求数是读代码数的。
- 「审的人不是写的人」只对挂了评审阶段的任务生效，验收里的任务都挂了。没挂的任务没有这条规则。
- 装团队的时间各规模都在 201 到 213 秒（3.2 表），和规模关系不大（4 个 agent 和 49 个 agent 差不多），时间主要花在固定开销上（主报告第 2 节）。只是一个现象，不作结论。

## 5 上游测试原样跑

### 5.1 `packages/teams-catalog`（11 条）

每个分支都跑（`run_all.sh`，`runs/<分支>/teams-catalog.{json,log}`）。所有 30 个标签和分支（5 个标签、20 个变更分支、5 个 `size-k-per-role-rule-rw`）结果相同：8 过 3 不过。起点上 11 条全过（`runs/baseline/teams-catalog.json`）。3 条不过都在 `packages/teams-catalog/src/shipped-catalog.test.ts`，都是把仓库自带的团队清单逐项写死的断言，多了一个自带团队就会变：

- 「ships the expected bundled and optional team fixtures」：`expected [ …(4) ] to deeply equal [ …(3) ]`（`:34`，团队数 3 变 4）；
- 「exposes a stable manifest header for downstream consumers」：`expected 6 to be 5`（`:81`）；
- 「preserves shipped agent roles, reporting lines, and skill assignments」：角色表多了 scale-engineering 的条目（`:121`）。

这 3 条是加了一个自带团队必然会变的，没有改断言。第一次跑时还有第 4 条不过（团队缺 `recommendedForCompanyTypes`），这是生成器的问题，补了生成器、重建所有标签和分支、全部重跑，表里是重跑后的数。

### 5.2 服务端 `teams-catalog-*`

每个分支原样跑 `server/src/__tests__/teams-catalog-routes.test.ts`（8 条）和 `teams-catalog-service.test.ts`（30 条）；`teams-catalog-install-no-overrides.test.ts`（4 条）一次要 13 分钟多，只在 k=16 的 5 个分支上跑（最大的规模，其他规模装的东西是它的子集）。起点用主报告已有的全量结果（`paperclip/tests/runs/baseline/server-list.json`，同一个提交 `dc9971bd`），不重跑。命令 `upstream_server.sh`，参数 `--root server --config vitest.config.ts`，超时 900000（同 `run-suite.sh:40-43`）。输出 `runs/<分支>/server-teams-catalog.{json,log}`。

| 分支 | 文件 | 条数 | 结果 | 用时 |
|---|---|---|---|---|
| baseline（已有结果） | 3 | 42 | 42 过 | install-no-overrides 821 s |
| size-1/2/4/8 的标签和 4 个变更（20 个） | 2 | 38 | 每个都 38 过 | 每个约 30 s |
| size-16 和 4 个变更（5 个） | 3 | 42 | 每个都 42 过 | 816–823 s |

服务端这三个文件没有一条因为加了 scale-engineering 团队而不过；`packages/teams-catalog` 那 3 条不过（5.1）只是写死清单的断言。rw 分支没跑服务端测试（它和只读版只差一个词，团队清单一样）。

## 6 复现

```
cd _scale/paperclip
bash make_sizes.sh 1 2 4 8 16          # 标签和分支（按角色的规则后来按 redo_per_role_rule.sh 重建）
python3 measure.py                     # counts.tsv
bash run_all.sh                        # 每个分支的验收 + 越级表 + packages/teams-catalog
bash redo_per_role_rule.sh             # 按角色配的规则改成只读后重建、重跑
bash upstream_server.sh <分支...>       # 服务端 teams-catalog-*
python3 collect.py                     # 汇总
```

一次只跑一个 vitest，最多 2 个 worker；不调模型，不用密钥。

## 7 两个探针：规则和角色的耦合（mero #23586，静态计数，没跑进程）

- 只数 `git diff -U0 --diff-algorithm=histogram size-<k>..<分支>`，脚本 `probes.py`，结果 `probes.tsv`。
- 三栏：
  - **规则**：源码（这里没有）加 `.paperclip.yaml`。这个文件只放每个 agent 的授权和适配器设置：protected、按角色的沙箱块。
  - **组织**：`AGENTS.md` / `TEAM.md` 的 frontmatter（name、role、reportsTo、includes…）。
  - **其余**：两种 md 的正文（角色卡文字）。
  - `generated/catalog.json` 照旧不进主数。
- 生成器 `gen_team.py` 的变更参数可以用 `+` 连起来。改完先在 size-1、size-16 的 10 个旧标签和分支上重生成，团队目录 0 处变化，再新建分支：

| 分支 | 提交 | 做法 |
|---|---|---|
| size-1-layer-rule | d94d2e8cfb | `add-layer+per-role-rule` |
| size-16-layer-rule | 54569f5531 | 同上 |
| size-1-move-qa | e78de780d6 | qa-g1 从 cto-g1 挪到 head-of-engineering（k = 1 没有别的组长） |
| size-16-move-qa | 0b998e86f2 | qa-g1 从 cto-g1 挪到 cto-g2 |

### 7.1 探针一：加一层、按角色的规则、两样都做

每格是文件 / 处 / 行：

| k | 变更 | 规则 | 组织 | 其余 | 合计 |
|---|---|---|---|---|---|
| 1 | L 加一层 | 1 / 1 / +5 | 3 / 3 / +12/−1 | 1 / 1 / +2 | 4 / 5 / +19/−1 |
| 1 | R 按角色的规则 | 1 / 4 / +32 | 0 | 0 | 1 / 4 / +32 |
| 1 | L+R | 1 / 4 / +45 | 3 / 3 / +12/−1 | 1 / 1 / +2 | 4 / 8 / +59/−1 |
| 16 | L 加一层 | 1 / 1 / +5 | 18 / 18 / +27/−16 | 1 / 1 / +2 | 19 / 20 / +34/−16 |
| 16 | R 按角色的规则 | 1 / 49 / +392 | 0 | 0 | 1 / 49 / +392 |
| 16 | L+R | 1 / 49 / +405 | 18 / 18 / +27/−16 | 1 / 1 / +2 | 19 / 68 / +434/−16 |

- **L+R 比 L 加 R 多 8 行，全在规则栏**，两个规模一样：k = 1 是 59 对 51，k = 16 是 434 对 426。
  - 多出来的是新加的 director 在 `.paperclip.yaml` 里的 8 行沙箱块：每个 agent 一块，没有按角色类型写一次的写法。
  - director 的区沿用生成器原来定的 `docs`，和 head 相同。
- 处数反而少 1（k = 1：8 对 9；k = 16：68 对 69）：director 的 protected 5 行和沙箱 8 行紧接在 head 的沙箱块后面，并成一处。
- 文件数不多：都在同一个 `.paperclip.yaml` 里。
- 旧角色照旧受管：它们的块一字没动。L+R 和 R 的规则栏只差 director 那 13 行（5 + 8）。
- 第 4 节的限制照旧：
  - 这条规则管的是读不是写，可写的版本生成沙箱时被拒；
  - 还要把运行时换成 `claude_local`。

### 7.2 探针二：换上级

| k | 规则 | 组织 | 其余 | 合计 |
|---|---|---|---|---|
| 1 | 0 | 1 / 1 / +1/−1 | 0 | 1 / 1 / +1/−1 |
| 16 | 0 | 1 / 1 / +1/−1 | 0 | 1 / 1 / +1/−1 |

- 改的是 `agents/qa-g1/AGENTS.md` 的 `reportsTo` 一行。
- 它自己的规则不用改：`.paperclip.yaml` 里的设置按 slug 写，不看上级是谁。
- 管不管得住，看配置（读代码，没跑）：
  - **(a) 只用定义文件**：0 行规则改动，但也不强制。第 3.2 节实测 (a) 下谁派给谁都放（V1 全放），挪不挪都一样。
  - **(b) 每个 agent 撤两条宽授权**：不用改规则，也不用多发 API 请求。
    - 派单看派单人的 `tasks:assign_scope` 覆盖的子树，子树每次判定时从 `agents.reportsTo` 现查（`services/authorization.ts:400-415` `agentIsInSubtree`，`:502-527`）。
    - 挪过去以后，cto-g2 能派给 qa-g1，cto-g1 被拒（`deny_policy_restricted`）。
    - 收任务（V4 那条）也跟着汇报链走（`:2705-2716` `allow_manager_chain`）。
  - **照写的例外**：
    - head-of-engineering 挪前挪后都能派，因为 V2 设计上就放。
    - k = 1 时 qa-g1 挪到 head 名下，「新上级能派」挪前就成立。
- 没查的：改定义文件对已经装好的公司是否生效（导入是否更新已有 agent 的 `reportsTo`）。运行中的公司换上级走 agent 的 API，这里只数定义文件，和第 2 节口径一致。

## 8 组合演示（mero #23876，静态计数，没跑进程）

三栏同第 7 节：规则 = 源码加 `.paperclip.yaml`；组织 = md 的 frontmatter；其余 = md 正文、上游测试文件、`MIGRATION.md`。`catalog.json` 不进主数。测试文件（`*.test.ts`）归其余，这是新加的一条，第 7 节的数不变（那里没有测试文件）。

### 8.1 演示一：放大，规则不变

`git diff -U0 --diff-algorithm=histogram size-1..size-k` 的整段累计，`demo1.py`，结果 `demo1.tsv`。每格文件 / 处 / 行：

| k | 规则 | 组织 | 其余 | 合计 |
|---|---|---|---|---|
| 2 | 1 / 1 / +15 | 4 / 4 / +33 | 3 / 3 / +6 | 5 / 8 / +54 |
| 4 | 1 / 1 / +45 | 10 / 10 / +99 | 9 / 9 / +18 | 11 / 20 / +162 |
| 8 | 1 / 1 / +105 | 22 / 22 / +231 | 21 / 21 / +42 | 23 / 44 / +378 |
| 16 | 1 / 1 / +225 | 46 / 46 / +495 | 45 / 45 / +90 | 47 / 92 / +810 |

- **线性**：每多一组 +54 行，即 54(k−1)。没有删行。
- **规则栏也随 k 涨**，每组 +15 行。规则本身一条没加、没改，涨的是每个新 agent 在 `.paperclip.yaml` 里那 5 行 `assignmentPolicy.mode: protected`。
  - Paperclip 没有「按角色默认」的写法，新 agent 不写这 5 行就不是 protected。
  - 配置 (b) 另要每个新 agent 2 个 API 请求，不进 diff。
- 组织栏：每组 3 个新 `AGENTS.md` 的 frontmatter（各 10 行），加 `TEAM.md` 的 `includes` 3 行。其余栏：3 个新角色卡正文各 2 行。
- **原有规则管不管得到新角色：管得到，有实测数**（第 3.2 节，每个规模每组一套越级用例）：

| k | (a) 拒 | (b) 拒 | 合法放行 |
|---|---|---|---|
| 1 | 1/5 | 3/5 | 5/5 |
| 2 | 2/12 | 8/12 | 12/12 |
| 4 | 4/24 | 16/24 | 24/24 |
| 8 | 8/48 | 32/48 | 48/48 |
| 16 | 16/96 | 64/96 | 96/96 |

  - 每组拒的条数相同：(a) 每组 1 条（V5），(b) 每组 4 条（V1、V3、V5、V6）。新组和第 1 组一样受管。
  - 「管得到」的程度就是 Paperclip 本来的程度：V2、V4 在各规模都放。

### 8.2 演示二：嵌套（执行者带 3 个同种手下）

- 分支 `scenario-7-nest-3` = `33292c1075`。在规程场景 7（Senior Coder 带 1 个 Helper）上，照 Helper 的写法加 `helper-2`、`helper-3`。
  - 三个 helper 都是 `role: engineer`，和 Senior Coder 同一种角色，`reportsTo: senior-coder`。
  - `TEAM.md` 加 2 行 includes，成员说明那行改写；Senior Coder 角色卡一句改成「三个 Helper」；`MIGRATION.md` 一句；三个上游测试里列 agent 的断言各补上。
- 起点是规程的 1 倍组织（`baseline`，product-engineering 团队），不是规模线。依据是 mero 说的「在场景 7 上改成 3 个」。

| 比较 | 规则 | 组织 | 其余 | 合计 |
|---|---|---|---|---|
| baseline → 场景 7（1 个 helper） | 0 | 2 / 2 / +10 | 7 / 8 / +9/−4 | 7 / 10 / +19/−4 |
| baseline → 3 个 helper | 0 | 4 / 4 / +30 | 9 / 10 / +17/−4 | 9 / 14 / +47/−4 |
| 场景 7 → 3 个 helper | 0 | 3 / 3 / +20 | 8 / 9 / +13/−5 | 8 / 12 / +33/−5 |

- 规则 0 行：product-engineering 的 `.paperclip.yaml` 只给 CTO 写了 `canCreateAgents`，Senior Coder 本来就没有按 agent 的设置。「套用原执行者那套规则」在 Paperclip 里不用写，管它的规则都在引擎里、不看角色名。
- 其余栏里，测试文件占 3 个文件：从 baseline 算 +8/−2，从场景 7 算 +6/−2。它们是上游断言「这个团队装出几个 agent」，加人就得改。

**验收要点**（写进 `demo2_cases.tsv`，没跑）：

| 用例 | 内容 | (a) 只用定义文件 | (b) 撤宽授权 | 依据 |
|---|---|---|---|---|
| N1 | Senior Coder 派给 helper-2 | 放 | 放 | 读代码：默认授权不分对象；(b) 子树按 `reportsTo` 现查 |
| N2 | CTO 越过 Senior Coder 直接派给 helper-2 | **放** | **放** | 规模线实测 V2：子树含孙辈，Paperclip 设计上允许 |
| N3 | QA（不是它的上级）派给 helper-2 | **放** | 拒 | 规模线实测 V6 的同类情形 |
| N4 | Senior Coder 评审 helper-2 的活 | 放 | 放 | 执行策略引擎，同场景 7 的用例 |
| N5 | helper-2 评审自己的活 | 拒 | 拒 | 执行策略引擎排除执行人（实测 V5） |

**做不到的照写**：
- 「别的上级不能越过新领导直接派」Paperclip 做不到：CTO 在两种配置下都能直接派给 helper（N2）。
- 非上级（QA）只在 (b) 下被拒；(a) 下谁都能派。
- 新手下受原执行者那套规则管：评审规则管得到（N4 放、N5 拒）。Senior Coder 本来没有别的按 agent 的规则。

**验收实测（mero #24289，单进程，没被系统停）**：
- 测试 `paperclip/tests/acceptance/demo2-nest.test.ts`：3 个 helper 各跑 N1–N5，配置 (a)、(b) 各一遍，加一条装出结构检查，共 31 条。
- 分支 `scenario-7-nest-3`：31/31 对上，结果在 `paperclip/tests/runs/demo2-nest/`，逐条在 `acceptance.log` 的 `DEMO2` 行。
  - (a)：N1、N2、N3 都放（`allow_visible_issue_write`），N4 放，N5 拒（`No eligible review participant`）。
  - (b)：N1、N2 放（`allow_explicit_grant`，子树授权），N3 拒（`deny_policy_restricted`），N4 放，N5 拒。
  - 和用例表一致，包括 Paperclip 不拦的那几条：N2 在 (a)(b) 都放，N3 在 (a) 放。
- 起点 `baseline` 反跑：31/31 对不上，结果在 `paperclip/tests/runs/demo2-nest-on-baseline/`。每条都停在「agent Helper… not installed」，属于第 2 节说的较弱证据：起点上没有这些角色，没走到判定。
- **第一次跑错了，照写**：结果留在 `runs/demo2-nest-try1-no-scope/`、`runs/demo2-nest-on-baseline-try1-no-scope/`。
  - 那次 (b) 的 N1、N2 共 6 条被拒，原因在测试：用了 harness 的 `canAssign`，它不传 `scope`，子树授权 `tasks:assign_scope` 没法匹配。
  - 真的路由会传 `scope`（`routes/issues.ts:5084-5097`），规模线的测试也传。改成同一形状后重跑分支和起点各一次，就是上面的数。

## 9 格点 T(k, m)（mero #24380，只建树，没跑）

- 仓 `paperclip/modified`，分支 `grid2-k<k>-m<m>`，k = 0、1、2、4、8，m = 0、1、2，共 15 个。
  - 全部从 `size-1`（1 倍组织：head-of-engineering、cto-g1、senior-coder-g1、qa-g1）出发，各一个提交。
  - `grid2-k0-m0` 就是 `size-1`（1aa806c669），没有提交。
- 生成器 `gen_team.py` 新加两个变更名：`kinds<K>`、`max-turns`。改完先在 14 个旧标签和分支上重生成，团队目录 0 处变化。
- **新角色**：kind1..kindK 挂在 cto-g1 下面，照加一个普通执行者的原生做法写。
  - 一个 `agents/kind<i>/AGENTS.md`（自己的名字、标题、提示词），`TEAM.md` 一行 includes。
  - `.paperclip.yaml` 5 行 protected：1 倍组织里每个 agent 都有，同第 1 节。
- **规则族**：
  - F1 读的区（我们写的，规模线验收过，参数级）：每个角色的 `adapter` 块带 `filesystemScope: workspace` 和一条只读 `filesystemExtraPaths`，路径按角色不同，新角色是 `/srv/team-shared/kind<i>`。
  - F2 每次运行的轮数上限（Paperclip 原生）：`claude_local` 适配器的 `maxTurnsPerRun`，按角色取值（head 40、lead 60、coder 200、qa 80、kind<i> 100 + 10i）。执行时变成 `--max-turns`（`packages/adapters/claude-local/src/server/execute.ts:445`、`:869`）。导入照原样带入 adapter 配置。
  - m = 1 是 F1，m = 2 是 F1 + F2。两族都要求运行时是 `claude_local`，所以 m ≥ 1 时每个 agent 多 4 行 `adapter` 头（type、runner、config）。这 4 行是两族共用的开销。
- **做不到的档**：m = 4、8 不做。
  - 已验收的按角色规则只有 F1 一族。
  - 原生的按角色取值里，这次核实过、能当规则用的只有 `maxTurnsPerRun`。
  - 候选还有 `timeoutSec`（同一适配器的运行超时）和 `budgetMonthlyCents`（每个 agent 的月预算）。前者凑不满 4 族；后者导入后是否建出真正起作用的预算策略，没核实。不新造。
- **原生去不掉的**：评审不是执行人（执行策略引擎，不看角色）；新 agent 激活时拿 15 条默认授权（`services/agent-hiring.ts:86-99`）。这些在 T(0,0) 里也在。
- 用例 `grid2_cases.tsv`：每个新角色每族一放一拒，共 90 行，没跑。两族都只能到参数级。
  - F1 看生成的沙箱参数，同第 3.4 节。
  - F2 看 `--max-turns` 参数：不调模型，CLI 真的在第 N 轮停下没法测。
- 数行时请排除 `packages/teams-catalog/generated/catalog.json`：它是生成文件，每次重建 `generatedAt` 时间戳都会变。例如 `grid2-k0-m1` 和 `size-1-per-role-rule` 只差这一行。

| 分支 | 提交 | 变更 |
|---|---|---|
| grid2-k0-m0 | 1aa806c669 | （= size-1） |
| grid2-k0-m1 | 0507ea6569 | per-role-rule |
| grid2-k0-m2 | c6e03e9c11 | per-role-rule+max-turns |
| grid2-k1-m0 | c708eeea58 | kinds1 |
| grid2-k1-m1 | 2a48e857eb | kinds1+per-role-rule |
| grid2-k1-m2 | c2b01eed0c | kinds1+per-role-rule+max-turns |
| grid2-k2-m0 | f53315f890 | kinds2 |
| grid2-k2-m1 | 8d602aae86 | kinds2+per-role-rule |
| grid2-k2-m2 | 5f4332ef3f | kinds2+per-role-rule+max-turns |
| grid2-k4-m0 | 188a3908f9 | kinds4 |
| grid2-k4-m1 | 793dca8392 | kinds4+per-role-rule |
| grid2-k4-m2 | 78a4b8a14b | kinds4+per-role-rule+max-turns |
| grid2-k8-m0 | 4143e6b393 | kinds8 |
| grid2-k8-m1 | ca6d3ebcbd | kinds8+per-role-rule |
| grid2-k8-m2 | fbee095578 | kinds8+per-role-rule+max-turns |

## 10 grid3：模拟规则（mero `_scale/GRID3-模拟规则.md`，只建树，没跑）

- 仓 `paperclip/modified`，分支 `grid3-k<k>-m<m>`，k、m 各取 0、1、2、4、8，共 25 个。
- 另有「先扩，再改」5 个：`grid3-k<k>-m0-change`。
- 脚本：
  - `gen_team.py`：新加 `copies<K>`、`coder-mode-default`，改完在旧分支上重生成，0 处变化；
  - `gen_relay.py`：写前 m 条规则。
- 用例 `grid3_cases.tsv`：8 条规则各一放一拒，没跑。

**角色这一维**：
- 挑的是 senior coder（写代码的执行者，活最容易变多）。
- `grid3-k<k>-m0` = size-1 加 senior-coder-g1-2 … senior-coder-g1-(k+1)，挂 cto-g1，同一份提示词、同样的 skills 和 protected 取值，各有名字。
  - Paperclip 原生就是一个 agent 一个名字，能单独派活，不用改代码。
  - 每加一个是 3 个文件约 +17 行。
- `grid3-k0-m0` 就是 `size-1`（1aa806c669）。

**规则写在哪、照的哪段**：
- 一个模块 `server/src/services/issue-relay-rules.ts`，全局写一次，管所有 agent，包括新加的。
- 照的是执行策略引擎的写法：
  - `services/issue-execution-policy.ts` 是纯检查，不合格 `throw unprocessable(...)`（`errors.js:40`）；
  - 由 `routes/issues.ts` 在落库前调用：PATCH 里 `applyIssueExecutionPolicyTransition`（:15234）先于 `Object.assign(updateFields, transition.patch)`。
  - 派单处挂在 `assertCanAssignTasks`（:13321、:13720）后面，同样是落库前拦。
- 路由里 3 处调用：
  - **派单**：`POST /companies/:companyId/issues` 和 `POST /issues/:id/children`，由 agent 发起、指派给 agent。文本是新任务的 description；交出者收到的文本是父任务的 description。
  - **交回**：`PATCH /issues/:id`，执行人自己把任务改成 in_review 或 done。文本是这次的 comment；接手的是建这个任务的 agent（`createdByAgentId`）；交出者收到的文本是这个任务的 description。
- **在哪一步查**：服务端收下文本、落库之前。接手的 agent 只能从服务端拿到这段文本，服务端拒了它就收不到；交回的评论在接手方领单时不出现，所以不能放到接手方的动作里查。
- 每条规则都是模块里 `RELAY_RULES` 的一项，都是全局一次：

| 号 | 实现 |
|---|---|
| R1 | `pw` 等于 123 |
| R2 | `names` 最后一个等于交出者（agent 名字转成小写加下划线） |
| R3 | `n` 等于收到那行的 n 加 1；没有父任务时为 1 |
| R4 | 只在交回时查：`heard` 包含交出者全部直接下级，查 `agents.reportsTo` |
| R5 | `key` 等于交出者 `role` 字段对应的词：engineering-manager green、engineer blue、qa amber |
| R6 | 只在交回时查：`names` 倒数第二个是接手方 |
| R7 | `n` ≤ 9 |
| R8 | 文本 ≤ 2000 字符 |

- R5 的词按 Paperclip 自己的 `role` 字段取，写一次，复制品共用 engineer → blue，不随 k 加行。代码里本来就有按 `role` 判的地方（`authorization.ts` 的 `role === "ceo"`）。
- **R7 的 N**：合法流程里 n 最大是 3（head 派 CTO 为 1，CTO 派 coder 为 2，coder 交回为 3）。复制品是并排的，不拉长链，所以 N = 9 各格点不变。
- **不适用**：无，8 条都装进去了。
- **改动量**：路由每个格点都是同样 13 行（import 1 行、3 处调用）；模块随 m 涨（m = 1/2/4/8 时合计 +85/+86/+96/+113，从 `grid3-k<k>-m0` 算），和 k 无关。

**特殊点**：
- 只查 agent 对 agent 的交接：board 或人发起的派单、交回不查。
- R3 的「收到的 n」取的是把任务交给交出者的那段文本：派单看父任务，交回看本任务。一个上级收齐下级的交回再往上交时，n 不累计下级那几段。
- **没编译验证**：上次会话跑服务端 `tsc --noEmit` 撑爆内存被杀（137），这次按 mero 的要求不起进程。类型只靠读代码核对：`Db` 的导入、`req.actor.agentId`、`existing.createdByAgentId`、`unprocessable` 的签名都照抄了已有用法。验收排队时第一步会先编译。

**「先扩，再改」**（`grid3-k<k>-m0-change`）：
- 改 senior coder 的 `assignmentPolicy.mode`：protected 改成 company_default（`authorization.ts:355-361` 只认这两个值）。m0 树里按 agent 带值的原生规则只有这一条，`maxTurnsPerRun` 不在 m0 树里。
- 每个名字各写一遍：改动 1 + k 处，k = 8 时 9 处 ±9，都在 `.paperclip.yaml` 一个文件里。

| 分支 | 提交 | 分支 | 提交 |
|---|---|---|---|
| grid3-k0-m0 | 1aa806c669 | grid3-k0-m0-change | f0aa3bbb8f |
| grid3-k1-m0 | 70e3775a5c | grid3-k1-m0-change | c2468a0a8b |
| grid3-k2-m0 | b444208b38 | grid3-k2-m0-change | 1ce2554263 |
| grid3-k4-m0 | 9cc5edf3bd | grid3-k4-m0-change | 412b122c88 |
| grid3-k8-m0 | d10d265823 | grid3-k8-m0-change | 625dd8afb2 |

m ≥ 1 的 20 个（k0/k1/k2/k4/k8 × m1/m2/m4/m8）：a863c82c5c 10dc9b696c 490c627a72 96e6c3716f / d4a2b2e4ad 5f26e87acd 687de29c2f 941ddcc29e / 1f697a3623 68f44e781a c9572ce02b cf2dd0f9e3 / 31b8c6c875 7903ae871e 2f6648a97d 0bacb8b659 / bb929b35fc 440db13ce5 b0104120b8 c8a463a8bc。

### 10.1 grid3 验收（mero #25024，单进程，没被系统停）

- 测试 `tests/grid3.test.ts`，runner `run_grid3.sh`，结果 `runs/grid3/<名>/grid3.log`，逐条看 `GRID3` 行。
- (a)、(d) 用配置 (b)：撤两条宽授权，不强加 protected，保留分支自己的取值。模拟规则走真路由：`POST /issues/:id/children`、`PATCH /issues/:id`。

| 跑 | 分支 | 结果 |
|---|---|---|
| a | grid3-k8-m0 | 4/4 对上：CTO G1 派给复制品 Senior Coder G1 9 放（allow_explicit_grant）；QA G1 派它拒（deny_policy_restricted）；QA 评审它放；它评审自己拒 |
| a 反跑 | grid3-k0-m0 | 4/4 对不上，全停在「agent Senior Coder G1 9 not installed」，较弱证据 |
| d | grid3-k8-m0-change | 4/4 对上：原 coder 和复制品各两条。QA 派给它放（allow_visible_issue_write，新值生效）；它派给 QA 拒（QA 仍 protected） |
| d 反跑 | grid3-k8-m0 | 2 条对不上：QA 派给两个 coder 变拒（deny_policy_restricted，旧值）。另 2 条照样对上 |
| 模拟规则 | grid3-k8-m8 | 16/16 对上：8 个放都过（建子单 201、交回 200）；8 个拒都是 422，并且是被要测的那条规则拒的 |
| 模拟规则 反跑 | grid3-k8-m0 | 8 条对不上：8 个拒全放了，没装规则；8 个放照样放 |

- **模拟规则第一次跑没跑到派单，照写**：
  - 结果留在 `runs/grid3/relay-try1-paused`、`relay-rev-try1-paused`。那次交回的 6 条对上、反跑 3 条对不上；派单的 10 条都在规则之前就被拦了，报 409「Cannot assign work to a paused agent」。
  - 原因：从目录装进来的 agent 是 paused 状态，而 agent 不许派给 paused 的 agent（`routes/issues.ts:7980`），这条检查在规则之前。
  - 改法：测试在派单前把复制品设成 idle，相当于 board 操作员解除暂停。改完只重跑模拟规则这一对，就是上表。

## 11 grid4 汇报线规则 P1、P2（mero `_scale/GRID4-汇报线规则.md`，树已建，验收排队中）

- 分支 `grid3-k<k>-p`，k = 0、1、2、4、8，从 `grid3-k<k>-m0` 起：

| 分支 | 提交 |
|---|---|
| grid3-k0-p | 6c9e1f203c |
| grid3-k1-p | 6264bfcea5 |
| grid3-k2-p | a327665082 |
| grid3-k4-p | 734e058e12 |
| grid3-k8-p | 9e10613251 |

- 脚本 `gen_report_line.py`。esbuild 转译过；没跑 tsc，内存紧，排到时先编模块。
- **规则源码**：`server/src/services/issue-report-line-rules.ts`，另在 `routes/issues.ts` PATCH 里挂一处，交回时调用。
  - P1：接收方（建这张单的 agent，`createdByAgentId`）必须等于交出者的 `agents.reportsTo`。
  - P2：评论末行 `from: <交出者>` 必须等于交出者的名字（小写加下划线）。
- **照的代码**：
  - 数据：Paperclip 自己的 `reportsTo`，授权现读它（`services/authorization.ts:400-415` `agentIsInSubtree`，`:2705-2716` `allow_manager_chain`）。规则里不写任何名字。
  - 写法：同 grid3 的模拟规则，即执行策略引擎那种纯检查加 `throw unprocessable`，在 PATCH 落库前调用（`:15234`）。
- **行数**：k = 0 时 +45 行（模块 39、路由 6）；k = 1、2、4、8 时比 `grid3-k<k>-m0` 多的也都是 +45。**每多一个执行者，规则这边 0 行。**
  - 新执行者的上级写在它自己的 `AGENTS.md` 的 `reportsTo` 一行里。那一行属于「加执行者」本身，已经在 m0 树里。
- **「谁是谁的上级」写在几处**（k = 0）：
  - 配置 5 处：4 个 `AGENTS.md` 的 `reportsTo`（head 是 null），加 `TEAM.md` 的 `manager:`。k = 8 时每个复制品再各 1 行，共 13 处。
  - 提示词和文档 3 处：head 的角色卡「hand each pod's CTO its goals」；`TEAM.md` 的 description 和正文各一句「head over the pods」。
  - 规则 0 处。
- **用例**（`tests/grid3.test.ts`，`GRID3_MODE=p`，k = 8，走真路由 `PATCH /issues/:id`）：
  - p1：复制品 Senior Coder G1 9 交回给上级 CTO G1，落款自己 → 放。
  - p2：交回给 QA G1（不是它的上级，那张单是 QA 建的）→ 拒，P1。
  - p3：交回给 CTO G1，落款写成 senior_coder_g1 → 拒，P2。
  - p4：原来的 Senior Coder G1 交回给 CTO G1，落款自己 → 放。
  - 反跑在 `grid3-k8-m0` 上。
- **口径**：交回 = 执行人把自己的任务改成 in_review 或 done；接收方 = 建单的 agent。只查 agent 对 agent 的交回。
- **「上级」用的是组织图上的上级**（mero #25633）：P1 比的是交出者的 `agents.reportsTo`，不是派单人。
  - Paperclip 只用定义文件时谁都能派活（第 3.2 节 (a)：V1、V6 全放）；撤宽授权以后，祖辈也能越级派（V2 放）。所以「派它的人」不一定是它的上级。
  - 派单人（建单的 agent）只当「这次交回交给了谁」用，P1 再核对他是不是交出者的上级。用例 p2 就是 QA 建单、复制品交回给 QA，被 P1 拒。

## 12 grid5 两族形式规则（mero `_scale/GRID5-两族形式规则.md`，树已建，验收排队中）

- 脚本：`gen_grid5.py`（规则）；`gen_team.py` 新加 `words<M>`（点名族的口令）。改完在旧分支上重生成，0 处变化。
- **挂法同 grid3 的模拟规则**：
  - 派单（建单、建子单的 description）和交回（执行人改 in_review/done 的 comment）时查；
  - 都在 `routes/issues.ts` 落库前调用，不合格 `throw unprocessable`，照执行策略引擎的写法（`services/issue-execution-policy.ts`）。
- **通用族 G**：`server/src/services/issue-generic-marker-rules.ts`，全局一次，不认角色。
  - 每行 `g<i>:` 必须等于真正交出者的名字（agent 名小写加下划线），按交出者的 agent id 现查 `agents.name`。
  - mero #25753 改过一次：第一版是「从 1 起的连续整数」，分支已按新定义重建，提交号见下表。
  - m 条规则的键写在同一行数组里，所以模块行数不随 m 变：每棵树都是 +46。
- **点名族 N**：`server/src/services/issue-named-marker-rules.ts` 按交出者读它自己的 `agents.runtime_config.handoffWords.n<i>`，代码里不写任何名字。
  - 口令写在 `.paperclip.yaml` 里每个 agent 自己的 `runtime` 块。
  - 照的是 Paperclip 本来写按 agent 的值的地方：同一个 agent 块里的 `permissions.authorizationPolicy.assignmentPolicy.mode`、`adapter.config.maxTurnsPerRun`。
  - 导入原样存进 `agents.runtime_config`（`services/company-portability.ts:3259-3266`；`:1336` 的整理只动 heartbeat、debug、modelProfiles）。
  - 复制品和原来的 coder 各写一份，口令相同。
  - 口令按角色种类各 8 个，不从名字算出：head maple…、lead willow…、coder juniper topaz anchor prairie indigo summit heron cinder、qa birch onyx kettle…（见 `gen_team.py` 的 `WORDS`）。
- **点名族每多写几行**：
  - 每多一个执行者，多 2 + m 行（`runtime:`、`handoffWords:` 两行头，加每条规则 1 行），都在 `.paperclip.yaml` 它自己的块里；
  - 每多一条规则，每个 agent 各多 1 行（k = 0 时 4 个 agent）；
  - 模块和路由固定 +45。
- 行数（从 `grid3-k<k>-m0` 算，不含 catalog.json）：

| 分支 | 提交 | 改动 |
|---|---|---|
| g5-k0-g1 | 762d84c4f6 | 2 files changed, 46 insertions(+) |
| g5-k0-n1 | ff41780d40 | 3 files changed, 57 insertions(+) |
| g5-k0-g2 | c4426df295 | 2 files changed, 46 insertions(+) |
| g5-k0-n2 | 2bd0854842 | 3 files changed, 61 insertions(+) |
| g5-k0-g4 | 047db00ec7 | 2 files changed, 46 insertions(+) |
| g5-k0-n4 | 9eacead9f4 | 3 files changed, 69 insertions(+) |
| g5-k0-g8 | 7d6964aaf9 | 2 files changed, 46 insertions(+) |
| g5-k0-n8 | cb2a68908b | 3 files changed, 85 insertions(+) |
| g5-k1-g1 | 95ee3964d0 | 2 files changed, 46 insertions(+) |
| g5-k1-n1 | 6e78d6a649 | 3 files changed, 60 insertions(+) |
| g5-k2-g2 | 85d07e5ca5 | 2 files changed, 46 insertions(+) |
| g5-k2-n2 | 5b604bdf5c | 3 files changed, 69 insertions(+) |
| g5-k4-g4 | a2754f2328 | 2 files changed, 46 insertions(+) |
| g5-k4-n4 | 2f4c3f04bc | 3 files changed, 93 insertions(+) |
| g5-k8-g8 | 5d29d9bb79 | 2 files changed, 46 insertions(+) |
| g5-k8-n8 | a1e9e524f3 | 3 files changed, 165 insertions(+) |

- 验收（`tests/grid3.test.ts`，`GRID3_MODE=g5g` / `g5n`，在 g5-k8-g8 / g5-k8-n8 上，走真路由，复制品 Senior Coder G1 9 交回给 CTO G1）：
  - 1：8 行都对，放；
  - 2：第 1 行错（通用族写成别人的名字 senior_coder_g1），拒，并且只报 G1/N1；
  - 3：第 8 行错（通用族写成 cto_g1），拒，只报 G8/N8；
  - 4（点名族）：第 1 行写 QA 的口令，拒。
  - 反跑在 `grid3-k8-m0` 上。esbuild 转译过；没跑 tsc，排到时先编模块。

### 12.1 grid5、grid4 验收（单进程，没被系统停）

- 跑之前三个新模块各自 `tsc --noEmit` 都退出 0：`issue-report-line-rules.ts`、`issue-generic-marker-rules.ts`、`issue-named-marker-rules.ts`。
- 结果 `runs/grid3/<名>/grid3.log`，逐条看 `GRID3` 行。

| 跑 | 分支 | 结果 |
|---|---|---|
| 通用族 g5g | g5-k8-g8 | 3/3 对上：8 行都对放（200）；第 1 行写别人的名字拒，只报 G1；第 8 行写 cto_g1 拒，只报 G8 |
| 通用族 反跑 | grid3-k8-m0 | 2 条对不上：两个拒都放了。全对的那条照样放 |
| 点名族 g5n | g5-k8-n8 | 4/4 对上：8 行都对放；第 1 行错拒，只报 N1；第 8 行错拒，只报 N8；第 1 行写 QA 的口令拒，只报 N1 |
| 点名族 反跑 | grid3-k8-m0 | 3 条对不上：三个拒都放了 |
| 汇报线 p | grid3-k8-p | 4/4 对上：复制品交回给上级 CTO G1、落款自己放；交回给 QA G1 拒（P1）；落款写成 senior_coder_g1 拒（P2）；原 Senior Coder G1 交回给上级放 |
| 汇报线 反跑 | grid3-k8-m0 | 2 条对不上：两个拒都放了。两个放照样放 |
