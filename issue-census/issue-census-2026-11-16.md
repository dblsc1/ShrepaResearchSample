> 2026-11-16。子代理（sonnet）用未认证的 GitHub 公开搜索接口做的；主会话保存并抽查。
> **主会话抽查了 10 条**（Paperclip #12892、#15842、#2196、#5085、#10635、#4164、#653、#12182；Bernstein #5046、#425）：逐条调公开接口，状态和报告一致，报告里的引文都在 issue 正文里找到，都不是 pull request。
> **读这份数字要注意三点（子代理自己写明的）：**
> - A、B、C 三类是下限。它没有逐条读完全部 3,195 个候选，先用关键词筛，再挑出约 210 个读了正文。
> - 有 9 个查询的结果超过 300 条被截断。
> - Bernstein 的候选 91.6% 是维护者自己提交的，反映的是他自己的规划和自查，不是用户反馈。两家的数不要并列比。

# 治理变更类 issue 的计数与清单（paperclipai/paperclip 与 sipyourdrink-ltd/bernstein，2026-11-16）

**重要说明：我没有逐条读完全部候选。** 去重后共 3,195 个候选（Paperclip 2,025，Bernstein 1,170）。我先用关键词正则在「标题加前 1,500 字符正文」上筛选（Paperclip 860 个通过，Bernstein 400 个通过），逐条读了通过者的标题，再挑出约 150 个 Paperclip issue 和约 60 个 Bernstein issue 读正文并分类。未通过筛选的、以及标题明显无关的，一律按 D 计，没有读正文。所以下面的 A、B、C 是**下限**。论文里建议写「至少 N 个」，或再对 D 里通过筛选但未读正文的约 1,100 个做一轮复核。

## 1. 摘要

**Paperclip（2,025 个唯一候选）：** A 类 17（开放 13，关闭 4）；B 类 45（开放 38，关闭 7）；C 类 30（开放 30，关闭 0）；A 与 B 同时成立 0；D 类 1,933（其中 27 个列入「不确定」）。17+45+30+0+1,933=2,025。

**Bernstein（1,170 个唯一候选）：** 纯 A 类 0；纯 B 类 7（全部已关闭）；A 与 B 同时成立 1（#7019，开放）；C 类 18（开放 6，关闭 12）；D 类 1,144（其中 12 个列入「不确定」）。0+7+1+18+1,144=1,170。

Bernstein 的候选中有 1,072 个（91.6%）由维护者账号 `chernistry` 提交；已归类的 26 个中有 22 个也是它提交的（B 类 7、A+B 的 1、C 类 18 里的 14）。所以 Bernstein 的数字主要反映维护者自己的路线图和自审记录，不是外部用户反馈。

## 2. A 类与 B 类表

### Paperclip A 类（17）

| # | 状态 | 创建日期 | 反应数 | 标题 | 归类原因 | 原文引用 |
|---|---|---|---|---|---|---|
| 15315 | open | 2026-10-06 | 2 | Root CEO created with role "general" never gets its default change grants (agents:configure, skills:create) | 默认授权硬编码在 role 为 ceo 上。 | "`ensureRootAgentDefaultChangeGrants` (server/dist/services/built-in-agents.js) only grants `agents:configure` and `skills:create` to a root agent whose role is `ceo`, so our CEO held only `tasks:assign`." |
| 13949 | open | 2026-09-24 | 6 | No way to edit an agent's `role` after creation; owner can't grant `agents:suggest-changes` either | role 创建后无法修改。 | "The code comment says the role "can be set later, in the app", but we could not find any UI control to edit `role` after creation." |
| 40 | open | 2026-03-05 | 4 | Agent with CEO role cannot be recreated after termination — Board access required for CEO-role operations | CEO 角色 agent 被终止后无法恢复、删除或替换。 | "it cannot be reactivated, deleted, or replaced by other agents in the organization — even agents with `canCreateAgents: true` permission." |
| 12892 | open | 2026-09-05 | 0 | Changing a member's role writes no permission grants: an "owner" is denied with "Missing permission: agents:configure or agents:suggest-changes" | 改成员角色不写入授权。 | "Authorization resolves **grant rows**, never the membership role: `decidePrincipalGrant` → `findGrant(...)` over `principal_permission_grants` (`server/src/services/authorization.ts:648-672`)." |
| 5945 | open | 2026-05-13 | 0 | Second bug: setUserCompanyAccess (PUT /admin/users/:id/company-access) skips setPrincipalGrants, leaving users without role permissions | 管理端点加入成员后角色权限未写入。 | "Summary \`PUT /api/admin/users/:userId/company-access\` (instance-admin endpoint) inserts \`company_memberships\` rows but does **not** populate \`principal_permission_grants\` with the role's expected permissions." |
| 15842 | open | 2026-10-10 | 0 | Grant PATCH endpoints replace `principal_permission_grants` without re-applying role defaults, silently stripping a member's role-implied permissions | 改授权或角色时角色默认值被丢掉。 | "the whole `principal_permission_grants` set for a principal instead of merging with the role's defaults, and the plain role-change endpoint never writes grants at all." |
| 653 | closed | 2026-03-12 | 0 | Feature Request: Editing hierarchies without going through the CEO | 汇报关系无法重组。 | "I've built my team and would like restructure who reports to who." |
| 986 | closed | 2026-03-15 | 0 | is there any way to change this org chart? | 用户找不到改汇报关系的办法。 | "How can I change the Intern SE reports to Coder?" |
| 5085 | open | 2026-05-03 | 0 | executionPolicy: validate participant agentIds against live roster at attach-time and via periodic reconciler | agent 重建后策略仍指向旧 id。 | "When an agent is re-created or migrated, its UUID changes but the policy retains the old ID." |
| 10788 | open | 2026-08-03 | 0 | Deleting an agent leaves dangling execution-stage references and 404s the dashboard; the holding issue can't be deleted either (missing cascade on cost_events) | 删除 agent 留下悬空引用。 | "does not check whether the agent is still referenced by an issue's execution stage." |
| 2196 | open | 2026-03-30 | 1 | [BUG] Agent role is a closed enum in API but free-text in UI — should be text everywhere | role 是封闭枚举，自定义角色无法使用。 | "The `AgentRole` type in `shared/src/constants.ts` is a closed enum" |
| 7386 | open | 2026-06-02 | 0 | Add a dedicated role + instruction bundle for chief-local subordinate agents | 角色分类没有位置给新型下属 agent。 | "The role taxonomy (`AGENT_ROLES`) has no dedicated bucket for chief-local subordinate-execution agents - the openclaw_gateway agents a CEO orchestrator delegates discrete tasks to." |
| 18867 | open | 2026-11-03 | 0 | Plugin-managed agents are created without a company membership, so permission checks deny them | 插件创建的 agent 无成员关系，权限检查全拒绝。 | "That agent gets no row in `company_memberships`." |
| 1582 | open | 2026-03-22 | 0 | All agents hired via non-OpenClaw paths do not receive a `company_memberships` row in the database | 部分路径雇用的 agent 无成员行，无法授权。 | "This is a systemic issue — agents hired via non-OpenClaw paths do not receive a `company_memberships` row, blocking any permission grants like `tasks:assign`." |
| 15332 | open | 2026-10-06 | 0 | Lifecycle for task-scoped (one-shot) agents: allow self-termination after handover, or creator-managed teardown | agent 无法自行结束生命周期。 | "Today the platform has no supported way to end a copy's lifecycle without a human board action per copy: 1." |
| 10015 | closed | 2026-07-22 | 0 | Built-in agents: how to keep a bundled meta-agent (reflection-coach/summarizer) off the single-root manager? reportsTo=null drifts back via ensure() | 改不了内置 agent 的汇报关系。 | "Setting `reportsTo = null` (making it a root) is not stable: `ensure()` silently re-parents it back to the single root manager on the next reconcile." |
| 20795 | closed | 2026-11-11 | 0 | Feature: editable agent graph and customizable dashboard (reference implementation available) | 组织图只读，无法调整组织。 | "The org chart is a read-only drawing." |

### Paperclip B 类（45）

| # | 状态 | 创建日期 | 反应数 | 标题 | 归类原因 | 原文引用 |
|---|---|---|---|---|---|---|
| 1323 | open | 2026-03-20 | 8 | Feature request: Proper agent permission grants API | 没有像样的 agent 授权 API。 | "Currently there's no clean way to grant granular permissions (like `tasks:assign`) to non-CEO agents." |
| 375 | closed | 2026-03-09 | 2 | Feature Request: Expose Permission Grants API for Agent Task Assignment | 只有 CEO 能分配任务。 | "Currently, **only the CEO role can assign tasks**, creating a coordination bottleneck." |
| 17790 | open | 2026-10-26 | 0 | Access page defers grant editing to an extension, but the routes an extension would call cannot address agent principals | 编辑授权依赖扩展，路由又够不到 agent。 | "… editing advanced permissions requires an installed extension." |
| 17303 | open | 2026-10-23 | 0 | Agent-principal permission grants: no API read surface, and the only write path is replace-all (resets granted_by_user_id) | agent 授权无读接口，写入只有整体替换。 | "principals have **no read surface** via the API, and the only write path that reaches them is **replace-all**, which silently **destroys `granted_by_user_id`/`created_at`** of the grants it does not touch." |
| 17875 | open | 2026-10-27 | 0 | Supported stock editor/API for scoped grants on existing agents | 询问收窄现有授权的受支持办法。 | "Is there a supported core API/CLI alternative for narrowing agents:configure and agents:suggest-changes grants on existing agents?" |
| 15161 | closed | 2026-10-05 | 4 | No path (UI or API) to grant `agents:configure` / `agents:suggest-changes` to an existing agent | 现有 agent 无法被授予配置权限。 | "There's no way to grant an existing agent the `agents:configure` or `agents:suggest-changes` permission after it's created — not from the UI, and not through any API route." |
| 10086 | open | 2026-07-23 | 0 | Project-scoped access control for agents and human members (per-project RBAC within a company) | 无按项目的访问控制。 | "Problem Within a single company that has multiple projects, there's no way to restrict which **agents** and which **human members** can access which **project**." |
| 8769 | open | 2026-06-29 | 0 | Feature: read-only / viewer API scope (GET-only mintable credential for deployed read surfaces) | 无法签发只读凭证。 | "There is currently **no way to mint a provably read-only credential** for a deployed surface that only needs to *read* board state." |
| 1070 | closed | 2026-03-16 | 0 | feat: Per-agent assignment ACL — control who can task which agents | 请求按 agent 的分配 ACL。 | "Summary Add optional per-agent assignment access control lists (ACLs) so that only authorised users can create or reassign tasks to specific agents." |
| 18032 | open | 2026-10-28 | 0 | RFC: a deny-by-default `client` company membership role | 缺少默认拒绝的成员角色。 | "There is no role for a principal who should see almost nothing." |
| 3019 | open | 2026-04-07 | 1 | Feature: User membership roles with agent visibility filtering (limited/admin) | 请求限制成员可见 agent 的角色。 | "**Current state:** All company members see all agents and tasks." |
| 6437 | open | 2026-05-20 | 0 | feat(invites): add role picker to web invite form (admin/operator/viewer, not just owner) | 邀请只能设 owner，改角色要改数据库。 | "The web invite form (`Company Settings → Invites → Create invite`) currently defaults `defaults_payload.human.role = "owner"` with no UI control to choose otherwise." |
| 16941 | open | 2026-10-20 | 0 | Should member permission edits narrow role defaults? Revoked defaults return after restart | 追问权限编辑能否收窄角色默认值。 | "Should the member permissions editor let an administrator narrow a member below the defaults of that member's role, with that narrowing persisting, or are role defaults an irreducible minimum that the editor can never remove?" |
| 7906 | open | 2026-06-10 | 0 | feat: honor the manager chain (reportsTo) — or a permission grant — for issue:mutate so managers can re-home/reassign reports' issues | issue 修改权只属于被指派者。 | "For agent actors, `issue:mutate` is **assignee-only** — and there is no supported way to widen it." |
| 4264 | open | 2026-04-22 | 0 | CEO/manager agents cannot create routines for their direct reports | 例行任务授权写死。 | "Paperclip's routine authorization hardcodes that agents can only create/manage routines where they are the routine's own assignee." |
| 13378 | open | 2026-09-14 | 0 | [Feature Request] Manager agents: allow cancel/reassign of direct-report tickets | 经理不能转派下属工单。 | "Today this fails — an agent can only mutate issues it is assigned to." |
| 13377 | open | 2026-09-14 | 0 | [Feature Request] Manager agents: allow cancel/reassign of direct-report tickets | 与 13378 同标题的另一份报告。 | "Today this fails — an agent can only mutate issues it is assigned to." |
| 7448 | open | 2026-06-03 | 0 | feat: allow manager agents to create and manage routines for subordinates | 例行任务规则限定自己名下。 | "Manager agents (e.g. `A - Project Manager`) cannot create routines assigned to subordinates (e.g. `A - DevOps Engineer`) even when those subordinates are in their `chainOfCommand`." |
| 8851 | closed | 2026-07-02 | 0 | feat: no permission model lets a supervisor/goal-owner role mutate (status/blockers/wake) issues it doesn't directly own — HQ-style liveness supervision is unimplementable | 无权限让监督角色改他人 issue。 | "Paperclip supports assigning a recurring routine to act as a "goal supervisor" — an agent whose job is to periodically reconcile the state of a set of issues assigned to *other* agents" |
| 10271 | open | 2026-07-26 | 0 | feat(server): manager-scoped issue-state authority — let orchestrator agents activate their reports' issues | 经理不能改下属 issue 状态。 | "they cannot mutate issue state on issues assigned to other agents — `PATCH /api/issues/:id` authorization is checkout/assignee-centric, and the resume/reopen flows explicitly exclude `backlog`." |
| 7418 | open | 2026-06-02 | 0 | Scope Scrum coordination permissions for assigned-agent issues | 请求 Scrum 角色的受限协调权限。 | "Allow Scrum to set coordination statuses or restore the rightful waiting path/owner without broad mutation rights." |
| 6274 | closed | 2026-05-18 | 0 | feat: add tasks:cross_issue_comment permission for monitor agents | 现有规则拦住监控 agent。 | "The escalation monitor routine receives HTTP 403 when attempting to post `ESCALATION` comments on issues assigned to other agents." |
| 16758 | open | 2026-10-18 | 0 | Agent-holdable, read-only audit metadata permission (members, attributed audit feed, secret access events) | 审计 agent 无法获得只读审计权限。 | "An auditing agent cannot read who holds which grant, who did what, or who resolved a secret." |
| 21633 | open | 2026-11-14 | 0 | Enhancement: let a board user grant one agent the task Retry (tasks:retry), with a per-task cap | 请求可授予的重试权限。 | "Every agent gets 403 "Board access required"." |
| 21826 | open | 2026-11-15 | 0 | Show and edit agent interaction permissions in the board UI | 交互权限只能用 CLI 或 API 改。 | "Agent interaction permissions (`canAssignTasksToAgents`, `canMentionAgents`, `canAskHumans` from #21819, and the others) can only be changed with the CLI or the API." |
| 21819 | open | 2026-11-15 | 0 | Agent interaction permission to stop an agent from asking people directly (canAskHumans) | 请求新增限制向人提问的权限。 | "There is no matching control for questions to people." |
| 6202 | open | 2026-05-17 | 1 | Add company tool access matrix for agents | 请求公司级工具访问矩阵。 | "Add a company-level tool catalog and per-agent access matrix so admins can manage tool access once from Paperclip instead of editing each agent profile by hand." |
| 6203 | open | 2026-05-17 | 1 | Add governance for tool access changes | 请求工具权限变更的审批门。 | "Admin or secret-level tools should be auditable, and companies should be able to require approval before agents receive higher-risk access." |
| 8890 | open | 2026-07-02 | 0 | feat: team-scoped session reset endpoint so peers can clear stuck agent sessions without CEO relay | 同事 agent 无受限的重置权限。 | "there is no API path to clear that session without escalating to a board-level operator or CEO." |
| 18769 | open | 2026-11-03 | 0 | Plugin API route auth mode admitting scoped non-admin human members | 插件路由无面向普通成员的认证模式。 | "There's no mode that admits an `operator`/`viewer`-tier human at all — only board-tier (owner/admin) humans or agents can call a route declared `"board-or-agent"`." |
| 11353 | open | 2026-08-14 | 0 | Feature request: First-class human employees with agent-scoped access and human project leads | 无法把人放进层级并限制其访问范围。 | "I need to invite a human, place them in the organization chart with a job title and reporting line, make them responsible for projects and tasks, and restrict their access so they can operate exactly one assigned agent instead of the whole company." |
| 15239 | open | 2026-10-05 | 0 | Company (and project) default executionPolicy applied at issue creation when the create call omits one | 无公司级默认执行策略。 | "There is no company- or project-level default." |
| 4761 | open | 2026-04-29 | 0 | Auto-attach executionPolicy by assignee role on issue creation | 请求按角色在服务端强制策略。 | "When an issue is created with `assigneeAgentId` pointing at an `engineer` or `devops` role agent, there is no server-side enforcement of execution policies." |
| 12078 | closed | 2026-08-24 | 0 | Let routines copy an execution policy to each created issue | 例行任务不能携带执行策略。 | "A routine can create an assigned issue, but its create and update APIs cannot accept an `executionPolicy`." |
| 6567 | open | 2026-05-23 | 0 | Routines should carry an executionPolicy template that's copied into spawned issues at creation | 例行任务不能内嵌策略模板。 | "Routines (/api/routines) cannot embed an executionPolicy template." |
| 1150 | open | 2026-03-17 | 0 | policy: mandatory project inheritance for sub-issues | 请求一条强制治理规则。 | "New Governance Rule: All agents and users MUST ensure that any sub-issue created (where parentId is defined) inherits the exact projectId of its parent." |
| 4388 | open | 2026-04-24 | 0 | Feature request: requireBoardApprovalForRoutines company setting | 无「例行任务需批准」的设置。 | "There is `requireBoardApprovalForNewAgents` but no equivalent for routines." |
| 15508 | open | 2026-10-07 | 0 | Make tool-action approval expiry configurable (currently hardcoded to 1 hour) | 审批过期时间写死。 | "Approval cards for tool actions ("Approve tool action") expire 60 minutes after they are requested." |
| 10125 | open | 2026-07-23 | 0 | Protected adapterConfig fields: let companies lock `model` (and other keys) against agent-authenticated PATCH | 请求可配置地锁定关键字段。 | "mechanism so agent-authenticated callers cannot mutate governance-critical adapter settings — primarily `adapterConfig.model` — on themselves or on other agents." |
| 20052 | open | 2026-11-08 | 0 | Let an agent's manager agent resolve a bounded access request for an existing connection | 只有责任用户能处理访问请求。 | "Today only the responsible user can resolve that card." |
| 8828 | closed | 2026-07-01 | 0 | Allow @-mentioned non-assignee agents to post comments (comment-only, fail-closed) | 评论规则拦住必须参与的评审 agent。 | "This blocks a common governance workflow: a **mandatory reviewer** (e.g. a Security or QA agent) that is @-mentioned on" |
| 11439 | open | 2026-08-15 | 0 | Secrets-injection allowlist is closed and undocumented; agents outside the bundled list (e.g. CEO) cannot receive injected env vars like MGC_PAPERCLIP_TELEGRAM_BOT_TOKEN | 密钥注入允许名单写死（成立依据主要来自标题）。 | "Paperclip ships a secrets-injection mechanism that injects environment variables from a configured provider (Infisical / `local_encrypted`) into the runtime of selected agents." |
| 1203 | open | 2026-03-18 | 0 | feat: task lifecycle guards (child-completion blocking, status transition prerequisites) | 无法为状态转换设前置条件。 | "Paperclip has parent/child task relationships (`parentId`) and a status state machine (`assertTransition()`), but no way to enforce **prerequisites before a status transition**." |
| 10310 | open | 2026-07-27 | 1 | pipelines:write is ungrantable on single-owner instances — member-removal guard also gates permission changes and never inspects the request body | 移除成员的保护逻辑拦住授权。 | "`pipelines:write` cannot be granted through any supported surface on a single-owner instance." |
| 12182 | open | 2026-08-25 | 0 | Crash-recovery escalates engineering issues to CEO when no CTO exists, and discards returnOwnerAgentId on blocked→todo transitions | 升级链写死 cto、ceo 角色名。 | "Escalation ladder resolves to CEO without a CTO `resolveStrandedIssueRecoveryOwnerAgentId` (`services/recovery/service.js`) walks role fallbacks `["cto", "ceo"]`." |

### Bernstein A 类：无纯 A 类。

### Bernstein A 与 B 同时成立（1）

| # | 状态 | 创建日期 | 反应数 | 标题 | 归类原因 | 原文引用 |
|---|---|---|---|---|---|---|
| 7019 | open | 2026-11-11 | 0 | Role-adapter policy: optional default entry for unlisted roles | 无条目的角色可用任何 adapter，运营者无法关闭默认放开。 | "A role that has no entry may use any adapter, and so may every role when the file is missing or empty." |

### Bernstein B 类（7，全部已关闭，全部由 `chernistry` 提交）

| # | 状态 | 创建日期 | 反应数 | 标题 | 归类原因 | 原文引用 |
|---|---|---|---|---|---|---|
| 2554 | closed | 2026-07-16 | 0 | Tenant charters: chain-governed team boundaries, scoped delegation certificates, and receipt-grade cost showback | 无团队边界，人人是 root。 | "An install serving more than one group of humans has exactly one authority level today: everyone who can reach the fleet is root on the fleet." |
| 425 | closed | 2026-04-06 | 0 | Add RBAC for API endpoints (admin, operator, viewer roles) | 所有令牌权限相同。 | "All authenticated API requests have the same privileges." |
| 2366 | closed | 2026-07-06 | 0 | Dashboard authentication and role-based access | 仪表盘无认证和角色。 | "The dashboard's `/dashboard/auth/*` routes are unimplemented stubs (the corresponding tests are skipped), so anyone who can reach the port sees run data." |
| 2309 | closed | 2026-07-06 | 0 | RBAC, budgets, and seat attribution as verifiable projections over the audit chain | 请求 RBAC 与预算。 | "Operators running Bernstein for teams need role-based access control, budget enforcement, and per-seat attribution, and these are usually implemented as mutable database state that is logged but not itself verifiable." |
| 1318 | closed | 2026-05-17 | 0 | feat(security): per-tool allowlist + fail-closed policy + read-only profile | agent 可调任何工具。 | "Today Bernstein agents can call any registered tool." |
| 498 | closed | 2026-04-06 | 0 | Implement command allowlist per task scope | 请求按任务限制命令。 | "Beyond per-role command permissions, allow per-task command restrictions." |
| 494 | closed | 2026-04-06 | 0 | Implement permission hooks for external policy engines | 请求外部策略引擎作为决策来源。 | "Allow enterprise users to integrate external policy engines (OPA/Rego, Cedar, custom webhooks) as permission decision sources." |

## 3. C 类

**Paperclip C 类 30 个，全部开放：** 14294, 14732, 17993, 4164, 16935, 19174, 17301, 15511, 15070, 10635, 15219, 7398, 15800, 11604, 19973, 17166, 10363, 15027, 18280, 20785, 7786, 17391, 13859, 15904, 17777, 10007, 6343, 8020, 13431, 10326。

**最清晰的 10 个：**

| # | 状态 | 创建日期 | 反应数 | 标题 | 归类原因 | 原文引用 |
|---|---|---|---|---|---|---|
| 4164 | open | 2026-04-20 | 1 | [BUG] Owner membership does not grant permissions - hasPermission only checks explicit grants | 权限检查不看成员角色。 | "Permissions must be explicitly granted via `principal_permission_grants` entries — the membership role is never consulted." |
| 16935 | open | 2026-10-20 | 0 | Agent can change its own budget and adapterConfig through `PATCH /api/agents/:id` (`allow_self`); a mixed body also skips the profile change grant | agent 能改自己的预算和配置。 | "An agent that authenticates with only its own agent API key can send `PATCH /api/agents/<its own id>` and change its own `budgetMonthlyCents` and `adapterConfig` (including `dangerouslySkipPermissions` and `extraArgs`)." |
| 17301 | open | 2026-10-23 | 0 | An agent's issue update can remove its review and approval stages (executionPolicy: { stages: [] }), so the issue closes unreviewed with its PR still open | agent 能删掉自己的评审阶段。 | "`PATCH /api/issues/:id` replaces `executionPolicy` wholesale, and nothing stops the assigned agent's own run from sending a policy with no stages." |
| 15511 | open | 2026-10-08 | 0 | `allowIssueOverride` is never enforced: `executionWorkspacePreference: reuse_existing` is accepted with 201 while the project policy forbids issue-level overrides | 设置项无代码读取。 | "`ProjectExecutionWorkspacePolicy.allowIssueOverride` is **parsed, persisted, echoed back by the API, and then never read by anything that enforces it.**" |
| 10635 | open | 2026-08-01 | 0 | Execution policy never compares the approving actor to the author: an agent can name itself reviewer and approve its own work; skipped review stages are recorded as completed | agent 能自己评审自己。 | "an agent can name **itself** as the review participant and then approve its own work to `done`, producing a real recorded approval decision." |
| 7398 | open | 2026-06-02 | 0 | Recovery + auto-claim defeat reviewer independence: cross-assigned issue auto-reassigned to creator, then independence gate self-closed by the reviewed party | 独立评审门被被评审方关闭。 | "Two **coupled** control-plane defects combine to let a **mandated cross-family / independence review gate be closed by the gated party itself**." |
| 15800 | open | 2026-10-10 | 0 | Adapter-wired stdio MCP server tools bypass the MCP tool approval gate (no ask-first path) | 工具调用绕过审批门。 | "Tools of stdio MCP servers that are wired directly through an agent's adapter configuration (for example Copilot CLI `--additional-mcp-config`) never pass through the MCP Tool Approval Gate." |
| 11604 | open | 2026-08-18 | 0 | Agent tools:* lifecycle grants from migration 0149 are dead: all tool application/connection routes are board-only | 授予的权限无路由读取。 | "Agents are granted `tools:*` lifecycle permissions by migration `0149`, but no route ever reads them." |
| 19973 | open | 2026-11-08 | 0 | Default tools:use grant on new standard agents bypasses connection agent selection and Off action settings | 默认授权绕过连接设置。 | "On v2026.1106.0 (d69631b0), a standard agent can see and call tools that the connection's own settings deny it." |
| 17391 | open | 2026-10-23 | 0 | Tool profile bind/unbind skips the agent-edit check that connection installs enforce (any non-viewer member can change an agent's tool profile) | 绑定工具配置时跳过编辑权限检查。 | "A board member who **cannot** edit an agent can still bind a tool profile to that agent." |

**Bernstein C 类 18 个（开放 6，关闭 12）：** 3648, 7020, 5788, 7067, 4545, 4134, 6183, 4912, 5046, 3036, 5051, 4530, 3081, 4699, 6761, 4444, 6615, 3768。

**最清晰的 10 个：**

| # | 状态 | 创建日期 | 反应数 | 标题 | 归类原因 | 原文引用 |
|---|---|---|---|---|---|---|
| 7067 | open | 2026-11-12 | 0 | bernstein.yaml permission_mode and BERNSTEIN_PERMISSION_MODE are read by nothing, and ten more documented keys are ignored | 文档里的设置无代码读取。 | "The docs show `bernstein.yaml` sections that no code reads." |
| 4545 | open | 2026-08-25 | 0 | Production webhook routes bypass the trigger rules engine, so triggers.yaml silently does not govern real events | webhook 绕过规则引擎。 | "Real external events never pass through it." |
| 6183 | closed | 2026-09-22 | 0 | security: run_guardrails builds a DecisionGraph, populates it, and discards it without evaluating | 护栏决策图被丢弃未评估。 | "`run_guardrails` builds a `DecisionGraph`, feeds every guardrail decision into it, and then returns without ever evaluating it." |
| 4912 | open | 2026-08-31 | 0 | External policy engines are bridged but no decision path consults them, and an unreachable engine reads as "no rule matched" | 外部策略引擎无人调用。 | "Nothing in `src/` calls it." |
| 5046 | closed | 2026-09-01 | 0 | identity: a spawned agent's scope is never checked against its spawner's | 派生 agent 范围从不与派生者比较。 | "The parent id is stored on the identity, serialised by `to_dict`, written into the audit metadata, returned by the identities API and rendered as a column by the agents CLI — and never read by a comparison." |
| 5051 | closed | 2026-09-01 | 0 | approval: a timed-out approval is recorded as granted | 审批超时被记为批准。 | "`_default_poll_decision` returns `"approved"` when the wait expires, and the fail-closed variant is reachable only when the caller supplies an explicit timeout." |
| 4530 | closed | 2026-08-25 | 0 | PR approval mode can mark a task verified without ever opening a pull request | 审批没执行却标为已验证。 | "In PR approval mode, a task can be marked verified without a pull request ever being opened, and without anything recording that the approval step did not run." |
| 3081 | closed | 2026-07-25 | 0 | bernstein_approve force-completes any task regardless of state | 审批工具实为强制完成。 | "The tool name promises an approval gate; the implementation is an unconditional force-complete." |
| 4699 | closed | 2026-08-28 | 0 | An approval survives a branch rewrite: bind approvals to the diff hash and journal head they reviewed | 分支改写后旧审批仍生效。 | "Our own review flow makes the window real: a PR is reviewed and approved, then amended by a fix pass, force-updated during a rescue, or ejected from the merge queue and re-armed — and the approval silently carries over to a diff nobody looked at." |
| 6761 | open | 2026-10-24 | 0 | governance: reconcile automation writer approvals with NoSelf | 自动化审批分支可放行自审。 | "Checker acceptance therefore cannot authorize self-review." |

## 4. 不确定清单（均已计入 D）

**Paperclip（27）：** 7400 Org Chart empty when top-level agents reportsTo a board user (not null); 1110 Feature Request: Support human board members in org chart; 2346 Hybrid Organization Charts - Import Existing Organization Structure and Mix in AI Agents; 9759 Feature request: opt-out for bundled built-in agent auto-provisioning (terminated built-ins are re-p…; 9541 [Bug] Make blocker replacement atomic and manager-authorized; 10361 Allow blocked work to route to a reporting-line manager; 17783 PATCH executionPolicy replaces the whole policy: a body without the monitor disarms it, with a 200; 15068 Review-stage participants are not validated when an execution policy is written; 21317 codex_local defaults dangerouslyBypassApprovalsAndSandbox to true, so agent-filed hires always reque…; 18122 Agent long-lived keys can read peer agents' configuration (`/configuration`, `/config-revisions`), w…; 9565 Feature request: routine-level runnableBy allowlist — let a named agent fire a routine it doesn't ow…; 8367 Proposal: opt-out flag for cross-issue mention-grant (`allowIssueMentionGrant`); 15408 Discussion: a neutral external-policy decision interface for the tool gateway; 3950 Add workflow templates and SOP enforcement; 5264 Issue write-gate is assignment-based, not checkout-based — blocks multi-reviewer flows; misleading 4…; 379 RFC: Agent Trust Levels — automatic promotion and demotion based on run history; 2390 Browser access approval system for agents; 15057 Owners cannot answer issue-thread interactions: only the (company-default-derived) addressee can res…; 9581 bug(authz): create-then-delegate strands the creator — no POST /comments after assigning away; 9582 bug(authz): closing an issue revokes non-assignee comment grants; resume:true does not restore them; 9584 bug(authz): blockedByIssueIds can only be set by the assignee — finders cannot wire dependencies; 11654 Per-agent governance of Claude Code built-in tools on local adapters: is it intended to be reachable…; 12701 Agent `capabilities` renders with platform authority but is unvalidated self-description; 14228 Agent actors have no authorization path to instance environments (read or write) — and `environments…; 17984 Docs: supported least-privilege agent permission and environment diagnostic workflows; 17020 Editing a pending review policy can clear its stage and strand a blocked issue on the reviewer; 12733 Execution policy: final-stage pass should optionally return to the assignee instead of auto-closing…

**Bernstein（12）：** 661 Graduated access control that restricts new agents and expands trust over time; 2248 Named team manifests: pinned bundles of roles, model policies, and response profiles; 5022 identity: a grant valid at issue can be invalid at use, so re-decide at dispatch and name what chang…; 5757 governance: request one core reviewer per pull request instead of all four; 6036 delegation: a hop's authority is linked but not provably attenuated, and only our own verifier reads…; 3834 Refuse a resume whose grant moved, before the first side effect; 5031 identity: revocation has no bounded propagation, so "revoked" has no time in it; 4893 Coarse sampling capability is an unchecked blanket grant over a growing key set; 2793 Manager/planning spawn has no enforced write boundary by default; stray write lands untracked in ope…; 2781 Adapter selection allowlists reject most registered adapters (seed cli and --cli); 649 Agent sandbox profiles with composable capability sets; 2355 Provider availability policy: per-role fallback chains and failover drills

## 5. 方法的局限

**被截断的查询（total_count 超过 300，只取了前 300 条）：** Paperclip 的 role（303，只差 3 条）、permission（387）、policy（576）、approval（487）、ceo（431）、"add agent"（410）、rule（351）；Bernstein 的 role（544）、policy（328）。其余查询完整取回。Bernstein 的 ceo 和 "org chart" 返回 0。

**候选集可能漏掉的内容：** 词表不含 owner、admin、ACL、RBAC、scope 等词，只靠这些词出现的 issue 不会进来。我只保存了正文前 1,500 字符，分类看不到后半段。要补全可按创建日期切时间段再查。

**分类局限：** 我只读了关键词筛选后挑出的部分正文，其余按 D 计，A、B、C 是下限。C 类里有边界案例（例如「设置项没被读取」是否算治理规则）。重复报告没有合并（如 Paperclip #13377 与 #13378）。#11439 的归类主要依据标题，正文前段没有直接陈述问题，保守起见可剔除。

**Bernstein 数字怎么读：**
- 1,072 个候选（91.6%）由维护者 `chernistry` 提交；另有 `github-actions[bot]` 23 个，`Chirag6722` 15 个，`vaibhav8a` 11 个。
- 已归类的 26 个里 22 个是它提交的：B 类 7 个、A+B 的 1 个、C 类 18 个中的 14 个。
- B 类基本是维护者自己写的功能规划条目，不是用户遇到问题后的报告。
- C 类多是维护者对自家代码的审计缺陷记录，不是外部用户反馈。
- 候选里 1,052 个已关闭，开放仅 118 个。
- 因此 Bernstein 的数字不宜与 Paperclip 的用户反馈类数字直接并列比较。

**Paperclip 数字怎么读：** `LukeAbell` 一人提交了 64 个候选，另有不少 issue 看起来由同一批活跃用户或 AI agent 代写，条数不等于独立用户的人数。

**其他：** 全程只用未认证的公开 REST 搜索 API，没用 gh、令牌或本地凭证，请求里没有请求者或其项目的任何信息。

## 6. 运行过的查询

每条查询形式为 `repo:<仓库> is:issue in:title,body <词>`，`<仓库>` 取 `paperclipai/paperclip` 或 `sipyourdrink-ltd/bernstein`，每仓库各 21 条。每次请求前 sleep 7 秒，只在 total_count 大于已取条数时才取下一页，每个查询最多 3 页。

词表：role、roles、permission、permissions、grant、policy、"execution policy"、"review stage"、approval、governance、hierarchy、"org chart"、"reports to"、"reporting line"、delegation、ceo、manager、"custom agent"、"add agent"、allowlist、rule。

各词的 total_count（Paperclip / Bernstein）：role 303/544；roles 73/71；permission 387/113；permissions 235/50；grant 272/98；policy 576/328；"execution policy" 162/5；approval 487/178；"review stage" 113/7；governance 124/96；hierarchy 33/7；"org chart" 77/0；"reports to" 127/79；"reporting line" 13/3；delegation 59/58；ceo 431/0；manager 255/133；"custom agent" 74/7；"add agent" 410/147；allowlist 125/86；rule 351/259。

共 78 次请求，其中 1 次（Bernstein 的 policy 第 1 页）收到 403，等 60 秒后重试成功。

## 总数复核

我做了复核，结果如下：
- Paperclip：17（A）+45（B）+30（C）+0（A 与 B 同时）+1,933（D）=2,025，等于唯一候选数。
- Bernstein：0（A）+7（B）+1（A 与 B 同时）+18（C）+1,144（D）=1,170，等于唯一候选数。
- 不确定清单的 27 个和 12 个都已包含在各自的 D 里，没有重复计数。

**清理：** 我用 `mktemp -d` 创建的临时目录已删除。除此之外，我只在 scratchpad 目录里写过一个指向该临时目录的路径记录文件，也已删除。
