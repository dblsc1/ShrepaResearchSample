# 大体量实验，Sherpa 一侧：Bernstein 等价物放大到 k 组

负责人：naga。规程第 13 节，mero #16492、#16520。

## A 和 Paperclip 配对的 1+3k 线（mero #19388、#19415、#19432、#19536）

这一节是主图用的 Sherpa 线。下面第 0–7 节是先做的 2+9k 线，留作附加；它的四个变更也按同一口径重报，见 A.6。

### A.1 形状和标签

- **形状**：human（人）→ 1 个 manager（总负责人）→ k 组，每组 3 人：`lead_g<n>`（组长）、`backend_g<n>`（写代码）、`qa_g<n>`。
  - 和 Paperclip 的 head-of-engineering 带 k 组（cto、senior-coder、qa）对齐（`_scale/paperclip/PLAN.md`）。
  - 角色数 1+3k，human 另算。
- **生成器**：`gen_scale.py modified <k> --workers backend,qa --one-per-line`。
  - 规则包和参数的写法照 Bernstein 等价物，同第 0 节。
  - `--one-per-line`：点名位置的参数一个位置一行，用 TOML 多行字符串加行尾反斜杠，数组也分行。
- **一行一座位和单行的对比**：编译出的 5 张表逐字节相同（实测，`runs/size/layout-identity.txt`）。
  - 比了 k=1 和 k=16，带和不带「加角色 + 加层 + 按位置的规则」，还有原来 8 人一组的 k=16。
  - 用的脚本是 `layout_check.py`。
- **起点**：标签 `size-base` = `8577ccb`，是 `scale-base`（`465a373`）加一个提交：从 `_pairing/packs/` 拷来权威版的 `reopen_limit`，只给「按位置配的规则」这个变更用。
- **规模标签**（每个是 `size-base` 上一个提交，生成器输出）：

| 标签 | 提交 | 组数 | 角色数 |
|---|---|---|---|
| size-1 | e44044f | 1 | 4 |
| size-2 | 2635a76 | 2 | 7 |
| size-4 | 276663a | 4 | 13 |
| size-8 | 9226b7e | 8 | 25 |
| size-16 | 1ef8709 | 16 | 49 |

做标签和分支的脚本：`make_sizes.sh 1 2 4 8 16`。

### A.2 四个变更

每个变更从规模标签开分支 `size-<k>-<变更>`，内容是生成器多带一个参数的输出：

| 变更 | 分支后缀 | 生成器参数 | 内容 |
|---|---|---|---|
| 加一个角色 | `add-seat` | `--extra-seat` | 第 1 组加 `tester_g1`，和 qa 同等对待：同一个组长派单，同样的可写路径，受同样的包管 |
| 加按位置配的规则 | `add-seat-rule` | `--seat-rule` | 装 `reopen_limit`，每个位置配自己的打回次数（manager 1、组长 1、backend 4、qa 9、tester 9，见 `gen_scale.py` 的 `REOPENS`） |
| 加一层 | `add-layer` | `--extra-layer` | manager 和各组长之间插 `director` |
| 复制一整组 | `add-group` | k+1 | 多一组 3 人 |

**走的路**：四个变更都只改工作流声明（toml 和卡片）。内核、编译器、包都是 0：分栏里的「源码」一栏全是 0。

### A.3 数（只来自 git）

命令（审稿人可以照着跑，在 `_scale/sherpa/modified` 里）：

```
git diff --numstat size-<k>..size-<k>-<变更>            # 文件、+、−
git diff size-<k>..size-<k>-<变更> | wc -c               # 字节
python3 size_table.py                                    # 下表，含最长新增行
```

分栏：源码 = `*.py`；配置 = `*.toml`、`*.tsv`；提示词 = `cards/*.md`。测试不在树里（在 `_scale/sherpa/tests/`），所以没有测试栏。「其中生成的」= 全部，因为 `PPOtestScale/` 下的文件都是 `gen_scale.py` 写的。

| 规模 | 组数 | 角色数 | 变更 | 文件 | + | − | 源码 / 配置 / 提示词（文件:+−） | diff 字节 | 最长新增行字符 | 其中生成的 | 验收 | 命令 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| size-1 | 1 | 4 → 5 | add-seat | 2 | 50 | 1 | 0:+0-0 / 1:+10-1 / 1:+40-0 | 3730 | 246 | 2/50/1 | 4/4 对上（runs/size/k1/accept-add-seat.txt）；改前同一张表 3 条不符 | `git diff --numstat size-1..size-1-add-seat` |
| size-1 | 1 | 4 → 4 | add-seat-rule | 2 | 9 | 1 | 0:+0-0 / 2:+9-1 / 0:+0-0 | 1361 | 140 | 2/9/1 | 4/4 对上（runs/size/k1/accept-add-seat-rule.txt）；改前同一张表 2 条不符 | `git diff --numstat size-1..size-1-add-seat-rule` |
| size-1 | 1 | 4 → 5 | add-layer | 3 | 19 | 2 | 0:+0-0 / 1:+11-1 / 2:+8-1 | 2780 | 185 | 3/19/2 | 2/2 对上（runs/size/k1/accept-add-layer.txt）；改前同一张表 2 条不符 | `git diff --numstat size-1..size-1-add-layer` |
| size-1 | 1 | 4 → 7 | add-group | 4 | 117 | 2 | 0:+0-0 / 1:+30-2 / 3:+87-0 | 7220 | 246 | 4/117/2 | 3/3 对上（runs/size/k1/accept-add-group.txt）；改前同一张表 2 条不符 | `git diff --numstat size-1..size-1-add-group` |
| size-2 | 2 | 7 → 8 | add-seat | 2 | 49 | 0 | 0:+0-0 / 1:+9-0 / 1:+40-0 | 3834 | 246 | 2/49/0 | 4/4 对上（runs/size/k2/accept-add-seat.txt）；改前同一张表 3 条不符 | `git diff --numstat size-2..size-2-add-seat` |
| size-2 | 2 | 7 → 7 | add-seat-rule | 2 | 12 | 1 | 0:+0-0 / 2:+12-1 / 0:+0-0 | 1401 | 140 | 2/12/1 | 4/4 对上（runs/size/k2/accept-add-seat-rule.txt）；改前同一张表 2 条不符 | `git diff --numstat size-2..size-2-add-seat-rule` |
| size-2 | 2 | 7 → 8 | add-layer | 4 | 21 | 4 | 0:+0-0 / 1:+12-2 / 3:+9-2 | 3681 | 185 | 4/21/4 | 2/2 对上（runs/size/k2/accept-add-layer.txt）；改前同一张表 2 条不符 | `git diff --numstat size-2..size-2-add-layer` |
| size-2 | 2 | 7 → 10 | add-group | 4 | 117 | 2 | 0:+0-0 / 1:+30-2 / 3:+87-0 | 7320 | 246 | 4/117/2 | 3/3 对上（runs/size/k2/accept-add-group.txt）；改前同一张表 2 条不符 | `git diff --numstat size-2..size-2-add-group` |
| size-4 | 4 | 13 → 14 | add-seat | 2 | 49 | 0 | 0:+0-0 / 1:+9-0 / 1:+40-0 | 3837 | 246 | 2/49/0 | 4/4 对上（runs/size/k4/accept-add-seat.txt）；改前同一张表 3 条不符 | `git diff --numstat size-4..size-4-add-seat` |
| size-4 | 4 | 13 → 13 | add-seat-rule | 2 | 18 | 1 | 0:+0-0 / 2:+18-1 / 0:+0-0 | 1483 | 140 | 2/18/1 | 4/4 对上（runs/size/k4/accept-add-seat-rule.txt）；改前同一张表 2 条不符 | `git diff --numstat size-4..size-4-add-seat-rule` |
| size-4 | 4 | 13 → 14 | add-layer | 6 | 25 | 8 | 0:+0-0 / 1:+14-4 / 5:+11-4 | 5502 | 185 | 6/25/8 | 2/2 对上（runs/size/k4/accept-add-layer.txt）；改前同一张表 2 条不符 | `git diff --numstat size-4..size-4-add-layer` |
| size-4 | 4 | 13 → 16 | add-group | 4 | 117 | 2 | 0:+0-0 / 1:+30-2 / 3:+87-0 | 7325 | 246 | 4/117/2 | 3/3 对上（runs/size/k4/accept-add-group.txt）；改前同一张表 2 条不符 | `git diff --numstat size-4..size-4-add-group` |
| size-8 | 8 | 25 → 26 | add-seat | 2 | 49 | 0 | 0:+0-0 / 1:+9-0 / 1:+40-0 | 3839 | 246 | 2/49/0 | 4/4 对上（runs/size/k8/accept-add-seat.txt）；改前同一张表 3 条不符 | `git diff --numstat size-8..size-8-add-seat` |
| size-8 | 8 | 25 → 25 | add-seat-rule | 2 | 30 | 1 | 0:+0-0 / 2:+30-1 / 0:+0-0 | 1643 | 140 | 2/30/1 | 4/4 对上（runs/size/k8/accept-add-seat-rule.txt）；改前同一张表 2 条不符 | `git diff --numstat size-8..size-8-add-seat-rule` |
| size-8 | 8 | 25 → 26 | add-layer | 10 | 33 | 16 | 0:+0-0 / 1:+18-8 / 9:+15-8 | 9117 | 185 | 10/33/16 | 2/2 对上（runs/size/k8/accept-add-layer.txt）；改前同一张表 2 条不符 | `git diff --numstat size-8..size-8-add-layer` |
| size-8 | 8 | 25 → 28 | add-group | 4 | 117 | 2 | 0:+0-0 / 1:+30-2 / 3:+87-0 | 7327 | 246 | 4/117/2 | 3/3 对上（runs/size/k8/accept-add-group.txt）；改前同一张表 2 条不符 | `git diff --numstat size-8..size-8-add-group` |
| size-16 | 16 | 49 → 50 | add-seat | 2 | 49 | 0 | 0:+0-0 / 1:+9-0 / 1:+40-0 | 3839 | 246 | 2/49/0 | 4/4 对上（runs/size/k16/accept-add-seat.txt）；改前同一张表 3 条不符 | `git diff --numstat size-16..size-16-add-seat` |
| size-16 | 16 | 49 → 49 | add-seat-rule | 2 | 54 | 1 | 0:+0-0 / 2:+54-1 / 0:+0-0 | 1984 | 140 | 2/54/1 | 4/4 对上（runs/size/k16/accept-add-seat-rule.txt）；改前同一张表 2 条不符 | `git diff --numstat size-16..size-16-add-seat-rule` |
| size-16 | 16 | 49 → 50 | add-layer | 18 | 49 | 32 | 0:+0-0 / 1:+26-16 / 17:+23-16 | 16421 | 185 | 18/49/32 | 2/2 对上（runs/size/k16/accept-add-layer.txt）；改前同一张表 2 条不符 | `git diff --numstat size-16..size-16-add-layer` |
| size-16 | 16 | 49 → 52 | add-group | 4 | 117 | 2 | 0:+0-0 / 1:+30-2 / 3:+87-0 | 7381 | 246 | 4/117/2 | 3/3 对上（runs/size/k16/accept-add-group.txt）；改前同一张表 2 条不符 | `git diff --numstat size-16..size-16-add-group` |

（出处：`runs/size/size_table.md`，由 `python3 size_table.py` 生成。）

**读法**：
- **加一个角色**：2 个文件 +49 行，不随规模变。toml +9（实例、位置、可写路径一行），卡片 +40。
  - size-1 是 +50 −1：k=1 时 `qa_g1` 是参数里最后一项，加了 tester 以后要补一个分号，一行改写。
- **复制一组**：4 个文件 +117 −2，不随规模变。toml +30 −2，3 张卡 +87。
  - −2：一行是文件头注释里的「k=4 groups」；一行是 `seat_write_limit` 原来的最后一项补分号。生成器把组数写进了注释，这是它自己的写法，算 1 行。
- **加一层**：随组数线性长。k=1 是 3 个文件 +19 −2，k=16 是 18 个文件 +49 −32。
  - toml 里每个组长的 `upper` 改一行（k 行）。
  - 每个组长的卡改一行：「You take a task from manager」改成「director」，k 个文件。
  - 卡这一半是生成器的写法：卡里写了上级是谁。不改卡，规则照样生效（规则只看 toml），只是卡里的话错了。不改卡的话，k=16 是 2 个文件 +26 −16，仍随 k 线性长。
- **加按位置配的规则**：随角色数线性长，k=1 是 +9 −1，k=16 是 +54 −1。
  - 一个位置一行（49 行），加节名、引号几行；−1 是 `policy_pack.toml` 的 `requires` 一行改写，加上 `reopen_limit`。
  - 改成单行写法的话，行数恒定是 +3 −1，但那一行随角色数变长。
- **最长新增行**：一行一座位以后不随规模变，恒定 246 字符，是卡片里的一行。对比 A.6 的单行写法：k=64 时 25475 字符。

### A.4 验收（实测）

`run_size.sh 1 2 4 8 16`：在每个变更分支上跑 `gen_size_cases.py` 写的表，每个变更至少放一条、拒一条；再把同一张表拿到改之前的标签上跑（反向对照）。输出在 `runs/size/k<k>/`，摘要在 `runs/size/run_size.log`。

| 变更 | 放 | 拒 | k=1、2、4、8、16 | 改前同一张表 |
|---|---|---|---|---|
| 加角色 | S1 组长派给 tester；S2 tester 在可写路径里提交 | S3 tester 提交到任务范围里、可写路径外（`seat_write_limit.outside_seat_paths`）；S4 manager 越过组长派给 tester（`not_your_lower`） | 4/4 对上 | 3 条不符：没有 tester 这个位置 |
| 按位置的规则 | R1 qa 第 9 次打回；R4 backend 第 4 次打回 | R2 qa 第 10 次；R3 backend 第 5 次（它自己的数是 4） | 4/4 对上 | 2 条不符：R2、R3 放行，没有上限 |
| 加一层 | Y1 director 派给组长 | Y2 manager 越过 director 直接派组长（`not_your_lower`） | 2/2 对上 | 2 条不符 |
| 复制一组 | G1 新组长派给新组的 backend | G2 新组长派给旧组的 backend；G3 旧组长派给新组的 backend（都是 `not_your_lower`） | 3/3 对上 | 2 条不符：新组不存在，前置步骤报错 |

**越级表**（`gen_cases.py`，和 Paperclip 用的是同一份）在每个规模标签上（`runs/size/k<k>/enforcement.txt`）：
- 越权的全拒，合法的全放。
- k=1、2、4、8、16 分别是 4、10、20、40、80 条越权，加同样多条合法。
- 1+3k 形状里没有 reviewer，V5 不在这张表里。

### A.5 上游测试

树自带测试，原样跑（实测，`runs/size/upstream/`，命令 `pytest -q -rA -p no:cacheprovider Tests` 和 `... SherpaPolicyPackOrganizer/Tests`）：

| 引用 | 内核 | 规则包 |
|---|---|---|
| `scale-base` 465a373（放大之前） | 130 过 1 跳 | 53 过 11 跳 |
| `size-16-add-seat-rule` ed55858（最大规模，改动最多的分支） | 130 过 1 跳 | 53 过 13 跳 |

- 规则包多跳的 2 条是 `reopen_limit` 的用例占位。它的 `cases/*.json` 是 todo：`pack_cases.py` 只认五个固定的人，用例里设不了工作流参数。这个包的判决由 A.4 的 R1–R4 管。
- 内核那 1 条跳过两边是同一条：机器负载高时不判计时，见 `Tests/test_kernel.py:120`。
- 树自带测试不装 `PPOtestScale`，所以它们对放大几乎没有区分力。这和 ChatDev 那边的情况一样。

### A.6 附加：2+9k 线按同一口径重报

标签是原来的分支 `scale-k<k>`，变更分支是 `scale-k<k>-<变更>`。这条线的参数是单行写法，「加规则」是 `review_rules`（一条全局规则，不按位置配）。

```
python3 size_table.py --wide
```

| 规模 | 组数 | 角色数 | 变更 | 文件 | + | − | 源码 / 配置 / 提示词（文件:+−） | diff 字节 | 最长新增行字符 | 其中生成的 | 命令 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| scale-k1 | 1 | 10 → 11 | add-seat | 2 | 49 | 1 | 0:+0-0 / 1:+9-1 / 1:+40-0 | 4436 | 465 | 2/49/1 | `git diff --numstat scale-k1..scale-k1-add-seat` |
| scale-k1 | 1 | 10 → 10 | add-rule | 1 | 1 | 1 | 0:+0-0 / 1:+1-1 / 0:+0-0 | 823 | 140 | 1/1/1 | `git diff --numstat scale-k1..scale-k1-add-rule` |
| scale-k1 | 1 | 10 → 11 | add-layer | 3 | 19 | 4 | 0:+0-0 / 1:+11-3 / 2:+8-1 | 3516 | 465 | 3/19/4 | `git diff --numstat scale-k1..scale-k1-add-layer` |
| scale-k1 | 1 | 10 → 19 | add-group | 10 | 427 | 3 | 0:+0-0 / 1:+75-3 / 9:+352-0 | 23300 | 822 | 10/427/3 | `git diff --numstat scale-k1..scale-k1-add-group` |
| scale-k4 | 4 | 37 → 38 | add-seat | 2 | 49 | 1 | 0:+0-0 / 1:+9-1 / 1:+40-0 | 6964 | 1635 | 2/49/1 | `git diff --numstat scale-k4..scale-k4-add-seat` |
| scale-k4 | 4 | 37 → 37 | add-rule | 1 | 1 | 1 | 0:+0-0 / 1:+1-1 / 0:+0-0 | 823 | 140 | 1/1/1 | `git diff --numstat scale-k4..scale-k4-add-rule` |
| scale-k4 | 4 | 37 → 38 | add-layer | 6 | 25 | 10 | 0:+0-0 / 1:+14-6 / 5:+11-4 | 8648 | 1635 | 6/25/10 | `git diff --numstat scale-k4..scale-k4-add-layer` |
| scale-k4 | 4 | 37 → 46 | add-group | 10 | 427 | 3 | 0:+0-0 / 1:+75-3 / 9:+352-0 | 25709 | 1992 | 10/427/3 | `git diff --numstat scale-k4..scale-k4-add-group` |
| scale-k16 | 16 | 145 → 146 | add-seat | 2 | 49 | 1 | 0:+0-0 / 1:+9-1 / 1:+40-0 | 16579 | 6371 | 2/49/1 | `git diff --numstat scale-k16..scale-k16-add-seat` |
| scale-k16 | 16 | 145 → 145 | add-rule | 1 | 1 | 1 | 0:+0-0 / 1:+1-1 / 0:+0-0 | 823 | 140 | 1/1/1 | `git diff --numstat scale-k16..scale-k16-add-rule` |
| scale-k16 | 16 | 145 → 146 | add-layer | 18 | 49 | 34 | 0:+0-0 / 1:+26-18 / 17:+23-16 | 29368 | 6371 | 18/49/34 | `git diff --numstat scale-k16..scale-k16-add-layer` |
| scale-k16 | 16 | 145 → 154 | add-group | 10 | 427 | 3 | 0:+0-0 / 1:+75-3 / 9:+352-0 | 35577 | 6736 | 10/427/3 | `git diff --numstat scale-k16..scale-k16-add-group` |
| scale-k64 | 64 | 577 → 578 | add-seat | 2 | 49 | 1 | 0:+0-0 / 1:+9-1 / 1:+40-0 | 55365 | 25475 | 2/49/1 | `git diff --numstat scale-k64..scale-k64-add-seat` |
| scale-k64 | 64 | 577 → 577 | add-rule | 1 | 1 | 1 | 0:+0-0 / 1:+1-1 / 0:+0-0 | 823 | 140 | 1/1/1 | `git diff --numstat scale-k64..scale-k64-add-rule` |
| scale-k64 | 64 | 577 → 578 | add-layer | 66 | 145 | 130 | 0:+0-0 / 1:+74-66 / 65:+71-64 | 112884 | 25475 | 66/145/130 | `git diff --numstat scale-k64..scale-k64-add-layer` |
| scale-k64 | 64 | 577 → 586 | add-group | 10 | 427 | 3 | 0:+0-0 / 1:+75-3 / 9:+352-0 | 74939 | 25840 | 10/427/3 | `git diff --numstat scale-k64..scale-k64-add-group` |

（出处：`runs/size/wide_table.md`。）验收见第 3 节：只在 base 和 add-rule 上跑过；其余三个变更分支没跑过验收，21 节已写明。

### A.7 对 Sherpa 不利、照写

- **声明全部是生成器写的**：toml 和卡片都由 `gen_scale.py` 写出，「其中生成的」一栏等于合计。手写同样的内容行数一样，但审稿人可以说这些行要有人维护。
- **按位置配的规则随角色数线性长**：一个位置一行，Paperclip 那边也是每个角色几行（bela 的 PLAN）。
  - 换成单行写法，行数恒定（+3 −1），但字节照样随角色数长。
  - 两种写法编译结果相同；行数取哪种写法，由图的口径定。这里报的是一行一座位。
- **加一层要改 k 个组长**：toml 里 k 行 `upper`，卡里 k 行。按位置配对，「谁是谁的上级」写在每个实例上，没有「整组挂到新上级下」的写法。
- **`reopen_limit` 是我们为配对写的包**，不在 Sherpa 起点上。
  - 它的行数在 `size-base` 那个提交里，不在变更里。
  - 今天为撤单绕法刚改过一次：权威版在 `_pairing/packs/`，ChatDev 等价物的提交是 `b14ed00`。
- **按位置配对分不出同一位置的不同执照属于哪组**：第 5 节方案 B 的 B2。复制一组靠的是新的位置名（`lead_g<k+1>`），不是同一位置的第二个执照。
- **这条线不跑 V5**：1+3k 形状里没有 reviewer 位置。


---

# 附加：2+9k 线（先做的，第 0–7 节）

**底子**：`bernstein/sherpa_equivalent/modified` 的 `baseline`，复制到 `modified/`，原处没动。

**生成器** `gen_scale.py <树> <k>` 写出工作流 `PPOtestScale`（占位名）：
- 组织：human 带 manager，manager 带 k 个组长 `lead_g<n>`，每个组长带和等价物一样的 8 个下级 `<角色>_g<n>`。位置数是 2 + 9k：k=1、4、16、64 时分别是 11、38、146、578。
- 规则包和参数照等价物原样。按位置点名的参数，生成器按同一规律写：
  - `seat_write_limit`：每个下级用它角色的路径，组长用 manager 的路径；
  - `must_decompose`：manager 加所有组长；
  - `parallel_wait_all`：仍然只排除 manager。

**量法**：
- `measure.py <k>`：真 ppo、真内核；
- `run_k.sh <k>`：量法加越权表一起跑；
- 越权表的用例由 `gen_cases.py` 生成，和 Bernstein 一侧的 vuna 对齐成同一份清单。

## 0 结论先说

- **内核、编译器、现有规则包、配对用的包**：四个 k 上改动都是 0 字节（`git diff baseline..scale-k<k>` 只碰工作流文件夹）。
- **强制没有随规模走样**：
  - 越权动作：k=1、4、16、64 上分别 4、20、80、320 条，全部被拒；合法动作同样条数，全部放行。没有一条不对。
  - 「审的人不是写的人」：没装 review_rules 时全部放行，静默不报错；装上后全部被拒。
- **速度**：
  - k=64 以内，编译（ppo init）和单条命令的判决都在 0.2 到 0.4 秒。编译中位数是 0.174、0.225、0.178、0.327 秒，k=64 约是 k=1 的两倍（更正：原来写「看不出随 k 变」）。
  - 再往上探到 k=256（2,306 个位置）、k=1024（9,218 个位置），编译分别是 1.0 秒、6.2 秒，单条命令约 0.46 秒、1.0 到 1.1 秒。
  - 没有报错，也没有写死的上限。
- **四个变更**：
  - 加规则恒定，1 行。
  - 加位置、加一组的行数恒定，但它们要改的那几行参数随 k 变长（k=64 时一行 25,000 多字符）。
  - 加层随 k 长：每个组长各改一行。
- **不利的照实说**：按位置点名的参数都是一个字符串、写在一行里，k 越大越长。两个人同时改不同的组，会在同一行上冲突。配对检查的 pairs 也挤在编译出的一行里（k=64 时 1 万多字符）。

## 1 声明文件和未动部分

| k | 位置 | 声明文件（toml + policy_pack）行数 / 字节 | 卡片 文件 / 行 | 内核、编译器、基础生命周期、现有包、配对包的改动 |
|---|---|---|---|---|
| 1 | 11 | 102 / 2,756 | 11 / 493 | 0 字节 |
| 4 | 38 | 318 / 8,330 | 38 / 1,549 | 0 字节 |
| 16 | 146 | 1,182 / 30,998 | 146 / 5,773 | 0 字节 |
| 64 | 578 | 4,638 / 122,726 | 578 / 22,669 | 0 字节 |

- 声明行数约是 30 + 72k（k=1 是 102，k=64 是 4,638；更正：原来写 9 + 72k）：每组一个组长、8 个下级，每个位置一段 `[[instance]]`（6 行）和一段 `[seat.x]`（2 行）。
- 卡片一个位置一张，正文抄 Bernstein 的角色提示词，只换第一行的执照和交差对象。卡片内容只差一行，本可以共用，但当前的卡片格式把执照写在了正文里。

## 2 编译出的表和用时

| k | roles 行 | checks / flow / outputs / plugins 行 | 配对检查 pairs 个数 | pairs 那一行的字符数 | 最长的表行 | ppo init 中位数（k=16、64 是 5 次；k=1、4 是 3 次，改成 5 次以后没有重跑） | sherpa init | 派单 / 开工 / 交回 中位数（9 轮；k=256、1024 的探测是 5 轮） |
|---|---|---|---|---|---|---|---|---|
| 1 | 11 | 15 / 10 / 7 / 21 | 10 | 235 | 482 | 0.17 秒（另一次量 0.52） | 0.33 | 0.40 / 0.36 / 0.29 |
| 4 | 38 | 同上 | 37 | 700 | 1,652 | 0.23 | 0.18 | 0.33 / 0.30 / 0.38 |
| 16 | 146 | 同上 | 145 | 2,679 | 6,388 | 0.18 | 0.21 | 0.27 / 0.27 / 0.25 |
| 64 | 578 | 同上 | 577 | 10,935 | 25,492 | 0.33 | 0.22 | 0.32 / 0.25 / 0.30 |
| 256（探） | 2,306 | 同上 | 2,305 | 46,628 | 103,164 | 1.0 | 0.41 | 0.46 / 0.48 / 0.46 |
| 1024（探） | 9,218 | 同上 | 9,217 | 192,205 | 415,172 | 6.2 | 0.93 | 1.12 / 1.10 / 0.94 |

- 只有 roles 表随 k 长。checks、flow、outputs、plugins 四张表的行数不变，因为规则是按包和检查点写的，不是按位置写的；按位置的部分都塞进了参数。
- 命令是由最后一组的组长计时的：它的位置排在角色表的最末尾，查表最慢。
- k=256、1024 是探测（`probe_k.py`，结果在 `runs/probe.json`）。只量编译和命令，不跑越权表和变更。
  - 量的时候 k=64 已经跑完，但机器上还有别的会话（4 核，负载约 8），所以数要当量级看。
  - 第一次探测是和 k=64 的越权表同时量的，数大一倍以上（编译 2.4 秒、16.4 秒），留在 `runs/probe-under-load.json`。
- 增长：
  - 位置数每涨 4 倍，编译时间涨约 3.1 倍和 6.1 倍（64 → 256 → 1024：0.33 → 1.0 → 6.2 秒），高的一端比位置数涨得快；
  - 单条命令在 k=64 以内不变，往上大致随角色表线性涨。

## 3 强制有没有随规模走样

**越权表**：每组五对，一条越权配一条合法动作。
- V1：组长给别组下级派单（k=1 时没有）。
- V2：manager 越过组长直接给下级派单。
- V3：下级越过组长去交组长的单。
- V4：manager 越过组长收下级的单。
- V6：下级给别组的人派单。
- 收单这一行由表里那个人亲自敲：运行器在 `_scale` 下拷了一份改过，共用的那份没动。

**V5（审核派给被审单的承办人）**：单独放在「加规则」那个变更上跑。

| k | 越权：被拒 / 总数 | 合法：放行 / 总数 | V5 没装 review_rules：被拒 / 总数 | V5 装上 review_rules：被拒 / 总数（合法放行） |
|---|---|---|---|---|
| 1 | 4 / 4 | 4 / 4 | 0 / 1 | 1 / 1（1 / 1） |
| 4 | 20 / 20 | 20 / 20 | 0 / 4 | 4 / 4（4 / 4） |
| 16 | 80 / 80 | 80 / 80 | 0 / 16 | 16 / 16（16 / 16） |
| 64 | 320 / 320 | 320 / 320 | 0 / 64 | 64 / 64（64 / 64） |

- **红码**：
  - V1、V2 是 `classic_lifecycle.not_your_lower`；V6 是 `builtin.role` 加 `classic_lifecycle.not_your_lower`（更正：原来只写了后者）；
  - V3、V4 是 `builtin.actor`；
  - V5 是 `review_rules.author_is_reviewer`。
- **`--reuse-build`**：建一次站点，每条用例复制一份。k=1 上和逐条重建相比，判决、红码逐条相同（`runs/k1/enforcement-fresh-build.results.tsv`）。

## 4 四个变更的改动量

基准是 `scale-k<k>`，变更分支是 `scale-k<k>-add-seat`、`-add-rule`、`-add-layer`、`-add-group`。四栏里内核、规则、编译器每一格都是 0，只有声明有改动。

| 变更 | k=1 | k=4 | k=16 | k=64 | 怎么随 k 变 |
|---|---|---|---|---|---|
| 加一个位置（给第 1 组加 tester_g1） | toml +9 −1；卡 1 个 +40；最长的新行 465 字符 | 同；1,635 | 同；6,371 | 同；25,475 | 行数恒定。但改的那一行是 seat_write_limit 的参数，整行重写，长度随 k 线性涨（增删字节数 2,909/433 → 27,919/25,443） |
| 加一条规则（requires 里加 review_rules） | toml +1 −1，140 字符 | 同 | 同 | 同 | 恒定。不用给任何位置补参数 |
| 在 manager 和组长之间加一层（director） | toml +11 −3；卡 2 个 +8 −1 | +14 −6；卡 5 个 | +26 −18；卡 17 个 | +74 −66；卡 65 个 +71 −64 | 随 k 长：每个组长的 `upper` 各改一行，每张组长卡各改一行；另外 seat_write_limit、must_decompose 两行参数要重写 |
| 再加一整组 | toml +75 −3；卡 9 个 +352；最长 822 | 同；1,992 | 同；6,736 | 同；25,840 | 新增的行数恒定。被重写的 3 行（文件头注释里的 k、seat_write_limit 参数行、must_decompose 的 only）里，后两行随 k 变长 |

**重点**：
- **加规则时要不要给每个位置补参数？** review_rules 不要。要按位置配参数的包（seat_write_limit、reopen_limit、seat_precedence 这类）则要，而且补的是一行里的一段：k=64 时，给一个位置改参数等于重写一行 25,000 字符的字符串。
- **一行参数随 k 变得很长**：
  - `[policy.<包>] params` 只接受一个字符串，按位置的映射只能写在一行里；
  - 编译出的配对检查也把全部 pairs 放进一行（k=64 时 10,935 字符，k=1024 时 19 万字符）。
  - 对编译和内核没造成问题，但对人读、对 diff、对多人同时改都不友好：加一组时 diff 里那 3 行是整行替换。
- **加层改的行数和组数成正比**：组长的上级写在每个组长自己的 `[[instance]]` 里，没有「这些位置的上级都是 X」这种一次声明的写法。

## 5 乙：同一位置发第二个执照，声明文件 0 行

mero #16520：复制一组，除了甲（生成器多写一组位置），还有乙：声明一行不改，同一位置用 -02 执照（用例里只用到 -02）。

在 k=1 工作流上跑了 13 条（`tests/licenses*.tsv`，结果在 `runs/licenses/`）：

| 条 | 测什么 | 结果 |
|---|---|---|
| B1 | -02 执照能用 | 放行，对 |
| B3 | manager 仍然越不过组长 | 被拒，对 |
| B4、B5 | 别组的人交不了我的单、收不了我的单 | 被拒（`builtin.actor`），对 |
| B6 | 收自己的单 | 放行，对 |
| B7 | 等待：第 2 组的单没结束，不卡第 1 组的组长 | 放行，对 |
| B8 | 等待：第 2 组的组长等自己的下级 | 被拒（`parallel_wait_all.tasks_not_ended`），对 |
| B9 | 必须分解：第 1 组派过单，不替第 2 组算 | 被拒（`must_decompose.nothing_dispatched`），对 |
| B10 | 写路径限制对 -02 同样生效 | 被拒，对 |
| B11、B12、B13 | 审的人不能是写的人 | 按执照比：作者本人被拒；另一个角色放行；同一位置的另一个执照算另一个人，放行 |
| **B2** | **组长 LEADG1-01 给 BACKENDG1-02 派单** | **放行，串了** |

- 打回限次：Bernstein 等价物没有这条规则，不适用。
- 串的那一条：配对检查按位置配，分不出组。所以乙的做法里「组」这个边界表达不出来，只能靠甲。
- 乙的代价：声明 0 行，但组和组之间的派单不受限。

## 6 卡住的地方

- k=64 以内没有遇到任何慢、报错或写死的上限。
- k=256、1024：
  - 编译和单条命令变慢，但到 9,218 个位置也只有编译约 6 秒、单条命令约 1 秒。原因是角色表和配对那一行的大小：每条命令都要读整张 roles 表，配对检查要解析一个 19 万字符的参数。
  - 没有报错。
  - 代码里没有找到上限。执照只要求是字母、数字和 `._-` 组成的名字（`Core/sherpa/step02_identity_read/identity_read.py:12`），编号没有位数限制，位置名也没有个数限制。
- **运行器的代价最显眼**：每条用例要建一个站点。k=64 有 320 条越权用例加 320 条合法用例（更正：原来写「640 条越权用例」），即使复制站点而不是重建，也跑了 49 分钟（k=16 的 160 条是 7 分钟），每条约 4.6 秒，主要花在复制站点、走前置步骤上。这是测试的成本，不是 Sherpa 运行时的成本。

## 7 文件

| 文件 | 内容 |
|---|---|
| `gen_scale.py`、`gen_cases.py`、`measure.py`、`run_k.sh`、`probe_k.py` | 生成器、用例生成器、量法、一键跑、探测 |
| `run_table_scale.py` | 共用运行器的拷贝：执照可带编号；收单、打回由表里的人敲；`--reuse-build`；提交里可以写指定内容 |
| `tests/` | 配置和用例表 |
| `runs/k<k>/` | measure.json、越权表的结果、summary.txt |
| `runs/licenses/`、`runs/probe.json` | 乙的结果；k=256、1024 的探测 |
| `SHERPA_FEEDBACK.md` | 使用反馈 |
