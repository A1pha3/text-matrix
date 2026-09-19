---
title: "pgrust 架构拆解：Rust 重写 PostgreSQL 之后，凭什么让人相信它没跑偏"
slug: malisper-pgrust-postgres-rust-rewrite
github_repo: "malisper/pgrust"
source_key: "gh:malisper/pgrust"
date: 2026-07-13T03:03:14+08:00
lastmod: 2026-09-19T00:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Rust", "PostgreSQL", "数据库"]
description: "按 2026-09-19 的 main（v0.3 快照）与三条归档分支拆解 pgrust：回归 oracle 的实际计数口径、Kani 双执行证明找出的 12 处分歧、四次重写路线的死因、benchmark 套件里三个口径不一致的 ClickHouse 领先幅度，以及一份对得上仓库现实的上手与排查路径。"
---

pgrust 把 PostgreSQL 的服务端整个换成了 Rust，然后声称行为没有变。真正值得读的并不是"用 Rust 重写"这件事本身，而是它为了让这句声称站得住搭起的四层证据，四层能说的话各不相同：跑上游回归套件并逐字节比对期望输出、用模型检验（model checking）对单个函数做等价性证明、对上游做差分模糊测试、按种子重放的崩溃与并发模拟。四层在仓库里都有实物——回归套件原样 vendor 了上游源码，证明层是一份 3,400 行的台账，模糊层有 98 个测试目标，模拟层有 18 条性质实现。基准测试是另一条线，它不证明行为，只把性能主张变成可复核的脚本、机型和权重。

另一边，仓库对读者的呈现并不总是跟上仓库自己。`main` 分支上那份 README 引用了 `benchmarks/`、`Dockerfile` 和 `docs/conformance/README.md`，而这三条路径在 `main` 的提交树里都不存在；同一段性能叙述在 README、基准套件和打分脚本的注释里给出了 18.5%、~7%、8.6% 三个不同的"领先 ClickHouse"幅度；形式化证明的数量在根 README、`proofs/README.md` 和证明台账分别是约 1000、1,086 和 1,336。这些差异不影响 pgrust 的价值判断，但决定了你按文档走能不能走通。

下面这些断言逐条对照 2026-09-19 的仓库实物（一次 `--filter=blob:none` 的克隆，`main` 提交 `79ad992`、`v0.3-beta` 提交 `20d63e2`、三条归档分支）与作者的四篇一手复盘，核到的写成事实，核不到的标 unresolved。

## 先分清三条主线

把 pgrust 当成"一个更快的 Postgres"来读会读偏。它同时在做三件互相约束的事，任何一件单独拿出来都够写一个项目：

| 主线 | 要回答的问题 | 仓库里的实物 | 目前状态 |
| --- | --- | --- | --- |
| 行为保真 | 换一个实现，凭什么输出还和 C 版一样 | `crates/postgres-18.6-reference/`（7,284 个文件的上游源码）、`regress/` 三套期望输出覆盖层、`proofs/`（857 个文件）、`fuzz/`（约 39 万个文件） | 回归套件按 README 口径全过；证明与模糊在推进 |
| 结构改造 | 哪些地方非改不可才能更快 | `crates/backend/` 下 26 个子系统、工作区里 888 个 crate | 向量化执行器、JIT、线程模型、调度器、内置 OOM 杀手已进 README 的实现清单 |
| 对外呈现 | 读者能不能复现 | `README.md`、归档分支上的 `benchmarks/` 与 `GOAL.md` | 与代码不同步的部分见下文逐条 |

三条主线的节奏不一样。前两条还在往前走（仓库最近一次推送 2026-09-18），`main` 上的 README 却在描述一份比它自己更完整的仓库。看这个项目时，"文档说了什么"和"这棵树上有什么"必须当成两个问题分别查。

## 项目坐标

| 维度 | 2026-09-19 的实测值 | 来源 |
| --- | --- | --- |
| 星标 / 派生（fork） | 5,077 / 191 | GitHub 的 REST（表述性状态转移）接口，`repos/malisper/pgrust` |
| 许可证 | AGPL-3.0（`LICENSE`），派生自 PostgreSQL 的部分保留 PostgreSQL License（`NOTICE`） | 仓库根 |
| 仓库创建 / 最近推送 | 2026-04-20 / 2026-09-18 | 同上 |
| 发行版本 | v0.3，badge 三枚：Postgres 18.6、`regression_suite 46,066/46,066`、version v0.3 | `README.md` |
| 语言构成 | Rust 94,570,767 字节（52.6%）、C 70,049,944 字节（39.0%） | `languages` 接口 |
| `main` 提交树 | 403,826 个文件，其中 `fuzz/corpus` 独占 388,805 | `git ls-tree -r HEAD` |
| 仓库体积 | GitHub API（应用程序接口）的 `size` 字段 639,095 KB，约 624 MB | 同第一行 |
| 服务端可执行文件名 | `postgres`（`cargo build --release --locked --bin postgres`） | README |

两处需要解释。**Rust 52.6% 而不是"95%+"**：C 那 70 MB 基本来自树里 vendor 进来的上游源码——光 `crates/postgres-18.6-reference/` 就有 2,463 个 `.c`/`.h`，它们不是 pgrust 自己的实现语言。**624 MB 里绝大部分是测试数据**：`fuzz/corpus` 一个目录就占了 38.8 万个文件，克隆前值得想清楚要不要它们。

## `main` 是一个单提交快照，不是开发史

`git rev-list --count HEAD` 在 `main` 上返回 1，提交信息是 `v0.3: Try us on real world workloads in non-critical environments`，日期 2026-09-15。也就是说公开 `main` 上没有增量历史，只有一次发布导出。想看演进，得去那三条归档分支：

| 分支 | 分支头提交日期 | 树规模 | 顶层特征 |
| --- | --- | --- | --- |
| `archive/pre-fabled-2026-06-25` | 2026-06-01 | 1,662 个文件 | `src/`、`tests/`、`plans/`、`optimizations/`、`antithesis/`、`AGENTS.md`、`CLAUDE.md`、`.claude/`、`.codex/`；该分支的 README 自称 `Status: V1 / experimental`、"约 96% 回归通过"，与复盘里第一代"四周推到 96%"对得上 |
| `archive/v0.1-main-2026-07-29` | 2026-07-29 | 6,529 个文件 | 含 `vendor/`、`scripts/`、`docker/`；`scripts/` 下有 `run-regression`、`run-pg-regress`、`run-pg-isolation` 等 10 个脚本，`vendor/postgres-18.3` 是当时的上游源码落点 |
| `archive/v0.2-main-2026-09-15` | 2026-09-07 | 4,819 个文件 | 新增 `benchmarks/`、`CATALOG.tsv`、`GOAL.md`、`RENAME-MAP.md`、`Dockerfile`、`docker/` |
| `main` | 2026-09-15 | 403,826 个文件 | 去掉 `Dockerfile`、`docker/`、`benchmarks/`、`CATALOG.tsv`、`GOAL.md`；新增 `fuzz/`（+38.8 万）、`crates/`（+8,210）、`proofs/`（+383）、`docs/` |

顺手记一条：v0.1 的 README 有专门的 History 一节，说旧实现归档在 `archive/pre-fabled-2026-06-23`，而 `git ls-remote --heads` 里那条分支的真名是 `...-06-25`，差两天。按文档里的字符串去 `git checkout` 会失败，分支名以 `ls-remote` 为准。

这张表里最影响使用的一条：`main` 上没有 `Dockerfile`、没有 `docker/`、没有 `scripts/`、没有 `benchmarks/`，而 README 的 Docker 一节写着"要用源码构建镜像，仓库的 `Dockerfile` 用了 BuildKit 缓存挂载"，Conformance 一节写着"由 `scripts/pg-regress-fast.sh` 驱动"、"细节见 `docs/conformance/README.md`"，性能一节写着"测试脚本在 `benchmarks/` 下"。用两种独立方法确认过这些路径在 `main` 上确实不存在：`git ls-tree -r --name-only HEAD` 前缀匹配为空，GitHub 的 `contents/` 接口返回的顶层清单里也没有它们。`main` 的 `docs/` 只有一个文件：`docs/fuzzing/rulings.toml`。

要按 README 里那些路径办事，先切到带全套文件的分支：

```bash
git clone https://github.com/malisper/pgrust
cd pgrust
git ls-tree --name-only HEAD                 # 先确认这棵树上有没有你要读的东西
git checkout archive/v0.2-main-2026-09-15    # benchmarks/、Dockerfile、GOAL.md 在这里
```

## 行为保真的四层证据，各自能说到什么程度

### 第一层：上游回归套件，逐字节比对

README 的说法是"跑 PostgreSQL 自带的 `src/test/regress`，原封不动 vendor 在 `crates/postgres-18.6-reference/src/test/regress`，用上游 `pg_regress` 打到一个 pgrust 服务端上"，判定门槛写成"231 个 `parallel_schedule` 文件全部逐字节匹配 vendor 的期望输出"。

这几个数能在树里对上：`parallel_schedule` 有 28 行 `test:`，展开后是 **231** 个测试名；上游 `sql/` 目录下有 **233** 个 `.sql`；`expected/` 下有 **265** 个 `.out`。pgrust 自己另加了 `regress/`，分 `overlay`、`isolation-overlay`、`tap-overlay` 三块共 208 个文件——那是它对同一批测试写自己的期望输出时用的覆盖层，不是替代上游套件。

**46,066 这个数是数什么的，我没有核到。** 它不是文件数（231 / 233 / 265 都不是），也不是期望输出的总行数（265 个 `.out` 合起来 277,159 行），还不是 `sql/` 里分号的个数（53,281 个）。README 明确说"这套 harness 到底数的是文件、行还是查询"写在 `docs/conformance/README.md`，而那份文件不在 `main` 上。这一条按 unresolved 处理：想知道确切口径，只能自己拉一份带文档的分支，或者直接看 `scripts/pg-regress-fast.sh`——它也不在 `main` 上。

这里有个措辞变化值得留意：v0.1 时代的 README badge 是 `regression_queries 46k+`，正文写"跨 46,000 多条回归**查询**匹配 Postgres 期望输出"；v0.3 的 badge 改成 `regression_suite 46,066/46,066`，正文改成"通过全部 46,066 个回归**测试**"。数字从模糊变精确的同时，计量单位换了一次词。

### 第二层：Kani 双执行等价性证明

`proofs/README.md` 是全文技术含量最高的一份文档。做法是把 pgrust 的函数和 vendor 的原版 C 函数用 `-Z c-ffi --c-lib` 编进同一个 goto-program，喂同一份符号输入，让 CBMC 在给定的输入长度与循环展开界限内证明两者输出对所有输入都相等。文档里那句话可以当作读这类证明的钥匙：`a green harness is a theorem, with its bounds recorded in the ledger`——绿色的 harness 是一条定理，而它的适用边界记在台账里。也就是说"证明了"永远要连着"在什么界限内"一起读。

台账实物是 `proofs/USER_FACING_FUNCTIONS.tsv`：6 列（`oid`、`name`、`source_file`、`status`、`class`、`notes`），3,400 行数据、**3,189 个不同 OID**、3,056 个不同函数名，覆盖 PostgreSQL 18.3 `pg_proc` 里所有可从 SQL 调用的内建函数，完整性审计另见 `proofs/LEDGER-AUDIT-2026-07-28.md`。同一份文件里，`status` 以 `proved(` 开头的有 1,397 行、涉及 **1,336 个不同 OID**；`excluded(...)` 1,352 行；`tested(differential)` 429 行。

三份文档给的是三个数：根 README 说"3000 个用户可见函数里形式化验证了 1000 个"；`proofs/README.md` 说"1,086 个函数已证 + 26 个用穷举或大规模采样的原生差分覆盖"；同一提交上的台账按 `proved(` 聚合出来是 1,336。三个数指向同一件事（已证比例在三到四成之间），不一致的只是精确值——文档落后于台账是这里最合理的解释，但没有任何一份文件写明这一点。**别人问你"pgrust 形式化验证到什么程度"，能给的答案是"约三成，且以台账为准"，而不是三个数字里的某一个。**

这条线最硬的结果是那 12 处分歧：8 处 pgrust 移植错误、4 处上游 PostgreSQL 的真实错误，另加一处（`money` 除法在 `MIN/-1`）同时贡献给两边。四个上游错误逐个都值得单独看：

| 上游函数 | 问题 | 可观察后果 |
| --- | --- | --- |
| `macaddr_in` | 用 C99 `sscanf` 的 `%x`，字段超过 8 位十六进制时按 2^32 取模 | 接受本该拒绝的 MAC 地址输入 |
| `cash_div_int8/4/2` | 漏了 2024 年那轮 money 溢出修补到处都有的 `INT64_MIN / -1` 保护 | x86-64 靠 SIGFPE 处理变成一个古怪错误，aarch64 静默返回错值 |
| `hashchar` / `hashcharextended` | 对裸 `char` 做加宽时没有像 "char" 比较运算符那样显式转 `uint8` | 有符号/无符号 `char` 的 ABI 给出不同哈希，跨架构散列分区路由会分叉 |
| `tidin` | `strtoul` 之后没查 `endptr == nptr` | `'(,5)'` 在 glibc 上被当 `(0,5)` 接受，在 BSD libc 上被拒 |

四条里有两条的结论是"同一份 C 代码在不同平台上行为不同"，而这只有把证明套件复制到 Linux-aarch64 上重跑才看得见。这类事情对 Postgres 用户本身也是有用的信息——它说明平台相关的解析与哈希差异确实存在于被广泛信任的实现里。

### 第三层：对上游做差分模糊测试

`fuzz/` 下 98 个 `.rs` 测试目标，`fuzz/divergences/` 16 个文件、`fuzz/fleet-evidence/` 23 个文件、`fuzz/known-divergences/` 2 个，语料 38.8 万个文件。`proofs/COVERAGE.md` 点明跑在证明层之上的三个 cargo-fuzz 目标是 `float_in_diff`、`float_out_diff`、`geo_diff`，即浮点输入输出与几何类型——浮点和几何正是 C 与 Rust 最容易在舍入与规范化上分叉的地方。

### 第四层：自带一套确定性崩溃模拟

`crash-simulator/`（110 个文件）容易被当成 Antithesis 的适配层，其实不是：它的包名是 `simharness`，`Cargo.toml` 第一行注释写着它是 "H1 sim-harness core"，并且**故意不挂进仓库根工作区**，理由是客户端侧依赖绝不能进入产品构建闭包。Antithesis 在这棵树上的痕迹属于上一代——`archive/pre-fabled-2026-06-25` 分支里有一个完整的 `antithesis/` 目录（Dockerfile、docker-compose、`test/main/README.md`），`main` 上只剩根 README 那句"正在与 Antithesis 合作做模拟测试"。

它的工作方式从 `src/bridge.rs` 的注释能读出来：runner 侧的 profile JSON 与生成侧的 `GenProfile` 是同一个文件、同一个 sha256 的两个类型视图；oracle 侧的性质被适配成生成器能消费的形式，压成"冻结的计划格式 v1 步骤"，与计划里的 `seq` 一一对应，好让运行期上下文不漂移；每个种子的 oracle 运行上下文（台账操作、探针槽位、检查）**可以由种子确定性地重新生成，因此绝不写进计划**。注释把这条叫 "determinism law"。

性质清单在 `src/oracle/props/` 下，18 个实现文件（`cursor.rs` 是 `c1`/`c2` 共用的底座）。按前缀分：`c1_cursor_walk`、`c2_hold_cursor` 管游标遍历与持有游标；`f1`…`f8` 八条覆盖插入可见性、删除缺席、约束报错、DDL 效果、聚合一致性、内存与资源基线；`m1_read_your_writes` 检查事务内看得到自己未提交的写、savepoint 回滚后恰好看不见被回滚的那批、提交后固化；`m2_cross_session` 分两条臂，READ COMMITTED 下另一会话的未提交 INSERT 必须不可见、提交后可见、回滚后不可见，REPEATABLE READ 下先取快照的会话在他人提交后重读必须仍是旧计数；`s1_spec_conflict` 是最刁钻的一条——两个会话在同一唯一键上抢 `INSERT ... ON CONFLICT`，用咨询锁把执行停在投机插入窗口内，逼出 `heap_abort_speculative`，再用一个 REPEATABLE READ 地平线钉住被杀元组不让它被清理；`x1_arm_equivalence`、`x2_index_invariance`、`x4_statement_form` 则要求同一读在不同 GUC（PostgreSQL 的运行时配置参数）臂、不同索引选择、不同语句形状下给出多重集相等的结果，臂间强制 `RESET ALL`。`bridge.rs` 的注释说 v1 是 14 条，现在按文件名数出来是 18 条。

真正值得单独说的是 `l1_tlp` 与 `l2_norec`，因为它们是这条证据链的逻辑支点。前者的模块注释直接署名 Rigger & Su 的 OOPSLA 2020 论文：对任意谓词 `p`，每一行必然恰好落进 `(p)`、`NOT p`、`(p) IS NULL` 三个三值逻辑分区之一，所以整表结果与三分区拼回来的结果必须相等——**不需要任何参照引擎**。后者是同一对作者的 ESEC/FSE 2020 NoREC：把 `SELECT .. FROM t WHERE p` 交给优化器，另跑一条优化器插不上手的改写 `SELECT (p) FROM t`（谓词在投影里，只能逐行算），前者的行数必须等于后者里 `TRUE` 的个数。

注释对这两条的价值有一句判断，正好补上第三层模糊测试的盲区：差分测试拿 C 版 Postgres 当答案卷，而"C 版本身有错"这种情况在结构上就测不出来（原话是 `C PG is its answer key`）；TLP 与 NoREC 是 reference-free 的，所以能抓到上游自己的 bug。`l1`/`l2` 的模块注释都点名了这一点，而 `proofs/` 那条线确实交出了四个上游 bug——两边对上的是同一件事。

`profiles/` 里十二份 JSON 决定每一轮跑什么形状：`default.json`、`float-lenient.json`、`metamorphic.json`、`multi-session.json`、`parallel-arms.json`、`planner-swarm.json`、`savepoint-stress.json`、`sim-bridge.json`（就是上面那条 bridge 的 profile）、`sim-m2.json`、`sim-s1.json`、`spill-stress.json`、`write-heavy.json`。

四类证据各自能撑到哪一步，读文档时最好一直带着这张表：

| 证据 | 覆盖方式 | 能说什么 | 不能说 |
| --- | --- | --- | --- |
| 回归套件 | 上游手写的用例，逐字节比对 | "这 231 组已知输入的输出一致" | 一致范围之外的任何行为 |
| Kani 证明 | 指定界限内穷举 | "在这些输入长度和展开界限内等价" | 界限外的输入 |
| 差分模糊 | 采样 | "在语料覆盖到的输入上没找到分歧" | 没有分歧 ≠ 正确 |
| 崩溃模拟 | 按种子重放 + 性质检查 | "在这些性质下，崩溃与并发行为符合预期" | 未列入性质清单的行为 |

`proofs/COVERAGE.md` 自己也用一句话挡住了误读：`A covered line is not a verified line`——被某一层覆盖到的行，不等于被验证过的行。

## 查询引擎为什么快：一条 SUM 的逐级加速

README 里"分析型快几百倍"这句话太粗，作者在 v0.2 发布后写的那篇执行引擎复盘把差距拆成了可复算的台阶。例子是把 1 到 5 亿求和：

```sql
CREATE TABLE my_table AS select col::float8 from generate_series(1.0, 500000000.0) g(col);
SELECT SUM(col) FROM my_table;
```

| 实现 | 耗时（作者实测，c8g.4xl，关并行） | 变化在哪 |
| --- | --- | --- |
| PostgreSQL | ~20 s | 参照物 |
| 手写 Volcano 迷你执行器（Rust，`next()` 一次只吐一行） | 1.3 s | 只保留执行器语义 |
| 加批处理：`const BATCH: usize = 1024`，`next_batch()` 写栈上缓冲 | ~480 ms | 每千行一次虚调用，聚合期间零分配 |
| 裸 `for` 循环 | 358 ms | 去掉所有算子抽象 |
| 算子融合（`SeqScan` 与求和合成一个节点） | 与裸循环同速 | 消掉拷贝 |
| 再上 NEON SIMD（每次处理 8 个 `f64`，4 个累加寄存器） | 135 ms | 比 Volcano 版快约 10 倍 |

作者给的判断有两处很实在。其一，这个例子不是同口径对比，Postgres 那一侧还包含解析存储格式、提取元组、加锁等开销，"优化数据库就是把这些开销尽量拆掉"——他把两大来源点名为锁与堆格式解析。其二，融合那一步他直接写"这确实是在作弊"：预先硬编码几个常见组合必然覆盖不全，要"在每条查询上都作弊"就得靠即时编译。

编译器为什么不自动把浮点循环换成 SIMD：浮点加法不满足结合律，换求和顺序会换结果，编译器默认不敢动。这类"必须重写成能控制指令序列的形状"的地方，正是 pgrust 需要自己的即时编译器的原因。

## 其余五处结构改动

这五处都写在 README 的 Implementation 一节，且都指向 Postgres 改不动的旧决定：

**线程代替进程。** 连接和并行查询都用线程。作者对动机的解释比"少一次 fork"更完整：`max_connections` 之所以需要重启才能改、并行查询之所以只给长查询开，根源都是进程贵；而 Postgres 抱住进程模型是因为隔离性，Rust 的编译期安全保证正好替掉这层理由。顺带把两条老路一起解决了——连接数上限和并行度选择。

**查询调度器。** 每条查询带优先级，跑得久的逐步降级，让短查询不被长查询挤死。

**内置 OOM 杀手。** 内存逼近机器上限时自己挑一个 worker 杀掉，一条查询死掉换服务端继续活着。README 把这两项放在一起说：它们对着的是作者那篇动机文里"四个骑马人"中的两个，具体哪两个没有点名。动机文自己列的是 VACUUM 与事务号回卷、连接数上限与查询并行、坏查询计划、JSON 四类。

**pipelined `fsync`。** worker 调完 `fsync` 就释放锁，不等它完成。成立的条件写得很清楚：这次查询在 `fsync` 结束前不会被确认，它的效果也不可观察。作者给的数字是高争用更新快 30–50 倍。

**JIT 编译从 ~50 ms 降到 ~5 µs。** 做法不是接 LLVM，也不是生成 C 再编译，而是 copy-and-patch：预备一批 ARM64 指令模板（stencil），运行时按算子填模板拼成函数。作者在专文里给了一个背景判断——今天没有任何一个生产级数据库自带即时编译器，大家要么用 LLVM 要么生成 C/C++，两者编译延迟都大到只能挑一部分查询来 JIT；µs 级之后可以对每条 SQL 都 JIT。代价写在 README 里：即时编译器目前只针对 neoverse-v2，也就是 Graviton4，别的平台能跑但拿不到同样的性能。

## 一条 SQL 走完全程

上面那些机制得串成一次具体动作才知道怎么配合。下面这条路径按仓库实物与 README 声明画，每步标出依据强度，避免把它读成一份从 C 版抄来的教科书流程图：

```text
你：initdb -D /tmp/pgrust-data ...        ← PostgreSQL 18 的 initdb（pgrust 暂未自带）
你：export PGRUST_PGSHAREDIR / PGRUST_TZDIR
你：./pgrust-0.3-macos-arm64 -D ... -c io_method=sync -c max_stack_depth=60000
   │
   ├─ 读 data 目录、共享内存、监听            依据：README 启动参数与报错文本
   ▼
psql -h /tmp -p 5432 -U postgres -c "select version()"
   │  wire protocol v3                       依据：README 声明协议兼容；客户端是上游 psql
   ▼
后端线程（不是 fork 出的进程）               依据：README "Threads instead of processes"
   │  crates/interfaces/pgclient 同名实现族
   ▼
parser → optimizer → 向量化 push-based 执行器  依据：README Implementation
   │                                    JIT 发射 neoverse-v2 指令（5µs 量级）
   │  行存 heap 或 pgrcolumnar 列存      依据：README Storage 一节
   ▼
DataRow + ReadyForQuery
   ▼
你看到：PostgreSQL 18.6 (pgrust 0.3)        依据：README 给出的预期输出
```

图里唯一一条能直接跑通验证的就是最后那行版本字符串，README 明写。中间各框之间怎么交接（执行器如何向存储层取批、JIT 在计划期的哪个点介入），`main` 上没有对应文档能让我确认，就不画了。crate 的名字倒是可以确认一件事：`crates/backend/` 下 26 个子目录——`access`、`catalog`、`commands`、`executor`、`libpq`、`nodes`、`optimizer`、`parser`、`postmaster`、`regex`、`replication`、`storage`、`tcop`、`utils` 等——和上游 `src/backend/` 的分层逐字对应。归档分支上的 `CATALOG.tsv` 把这层对应关系写成了表：1,241 行数据，列是 `unit`、`c_sources`、`status`、`crate`、`bench_ratio`、`notes`，`c_sources` 里直接填 `src/backend/utils/mmgr/mcxt.c,src/backend/utils/mmgr/aset.c,...`。**要找一个 pgrust 单元对应上游哪些 C 文件，查这张表比读代码快**；`GOAL.md` 说这张表建的时候是"约 970 个单元"，现在 1,241 行，两边相差三个多月。

## benchmark 数字该怎么读

先回答"测的是什么"。基准套件（在 `archive/v0.2` 与 `v0.3-beta` 上）分两组机器、两套协议：

| 项目 | 服务端机型 | 数据集 | 协议要点 |
| --- | --- | --- | --- |
| ClickBench | c8g.4xlarge（16 vCPU/32 GB）+ 500 GiB **gp2** | 43 条查询，与上游 `postgresql/queries.sql` 逐字节相同 | 每条查询：停服 → 清 OS 页缓存 → 重启 → 跑 3 次；第 1 次算冷，`min(2,3)` 算热 |
| OLTP 只读 | i8g.xlarge（4 vCPU/32 GB，约 872 GB 本地 NVMe） | sysbench `oltp_read_only`，10 表 × 1.3 亿行 ≈ 300 GB | 600 s 预热，3 轮 × 300 s，32 与 64 线程两档 |
| OLTP 读写 | 同上 | pgbench TPC-B-like | 同一套重复纪律 |

客户端是独立的 c8g.2xlarge，理由写在套件文档里：客户端 CPU 不能从服务端偷。两个引擎跑同一份 `configs/oltp-common.conf`（`shared_buffers=16GB`、`work_mem=64MB`，外加 pgrust 必需的 `io_method=sync`、`max_stack_depth=60000`），`fsync`、`synchronous_commit`、`full_page_writes` 一律不动，autovacuum 开着。

再看数字。同一件事在三处有三个说法：

| 出处 | 说法 |
| --- | --- |
| `main` / `v0.3-beta` 的 `README.md` | ClickBench combined 分数上比 ClickHouse 快 18.5%，比 PostgreSQL 快几百倍；sysbench 只读在 300 GB 上比 Postgres 18.3 高 30% |
| `benchmarks/README.md` 的 What to expect | combined 约 0.93，"约领先 ClickHouse 已发布的 c8g.4xlarge 那一行 7%"；只读 pgrust/C 比在 1.25–1.40×；读写约 1.03× |
| `benchmarks/scorers/score-clickbench.py` 注释 | "combined 公式就是那句公开的'领先 ClickHouse 8.6%'背后的公式" |

18.5% 与 7% 差了一倍多，8.6% 是第三个值。要判断该信哪个，得先看 combined 是什么：打分脚本里写着 `combined = hot_geo^0.6 * cold_geo^0.2 * load_ratio^0.1 * size_ratio^0.1`，并明确标注 `This is OUR weighting, not ClickBench's`——热/冷几何平均、加载耗时比、数据体积比的四项加权，权重是 pgrust 自选的，小于 1 表示领先。ClickBench 官网自己那套是逐查询 `(t+10ms)/(baseline+10ms)` 再取几何平均，10 ms 是上游给亚毫秒查询加的阻尼项。两个指标可以给出两个百分比，18.5% / 7% / 8.6% 更可能是不同子集、不同 bank（脚本里另有 `use-parquet-bank.sh`）与不同时点的产物，但我无法从仓库里断定它们各自的运行条件——README 说这些数字都来自同一套交给外部审计人的脚本，而脚本本身没随 `main` 发布。

从这套材料里**不能**推出的几件事：

- **不能推出在你的机器上会更快。** 已发布的是通用架构二进制，数字来自 `-Ctarget-cpu=neoverse-v2` 的调优构建，README 自己说"你从下载件复现不出这些数"；套件又说非 PGO 构建的读数要低 20–30 个点。
- **不能推出存储配置无关。** 同一份二进制换到默认的 gp3 根卷上，combined 会差约 12 分——文档原话是"那是磁盘不是引擎"，并要求在下结论前先跑 `use-reference-storage.sh --check`。
- **不能推出 OLTP 全面领先。** 读写在裸机型上只有约 1.03×，README 与套件都提到同样二进制在 Kubernetes（100 GB）上量到 50–60% 的只读差距，而作者明确写了"没有隔离出为什么同一份二进制在两边的行为不同，所以我们引用较低的那个数"。
- **不能拿 ClickBench 的数字推断事务系统能力。** ClickBench 测的是单表扫描与聚合为主的一批分析查询，它连"加载耗时和数据体积"都算进综合分，与并发小事务是两回事。

两个细节值得单独表扬，因为它们正是同类发布最容易糊过去的地方：PGO 构建脚本带一道机械校验（`pgo/lint-training-overlap.sh`），证明用于 profile 的语料与基准查询不共享任何一条语句；每个 runner 都会在输出里记录被测二进制的 sha256，让一个数字不可能被挂到没产出它的二进制上。打分脚本在任何一侧有查询缺失时直接拒绝出分，注释里写得很直白：悄悄丢掉查询是美化基准结果的经典手法。

## 四次尝试，三个死路

行为保真和性能都不是第一版就有的。作者在 2026-07-16 的复盘里把这条路完整写了一遍（四次尝试、自述累计花费约 10 万美元、最终 180 万行惯用 Rust、峰值同时跑 40 个子智能体）。这段的价值不在故事，在于每一步死因对"要做大系统重写"的人都能复用：

| 尝试 | 做法 | 推进到 | 死因 |
| --- | --- | --- | --- |
| `pgrust-og` | 一个特性一个特性地移植，先搭核心子系统再补特性 | 四周约 96% 测试通过 | 计划节点形状与上游不同：`SELECT name FROM users WHERE age > 30` 在 C 里是一个 `SeqScan`（`qual` 挂在节点内），在 Rust 版里是 `Projection{Filter{SeqScan}}` 三个节点；表在 C 里按索引引用、在 Rust 里按字符串引用。数十处这类差异叠加，planner 接不进剩余代码 |
| `c2rust` | 把 C 直接转译成 unsafe Rust | 两天得到 530 万行 unsafe Rust，通过 100% 回归，性能与 Postgres 相当，甚至与 Postgres **ABI 兼容**（扩展能用） | 转译产物每个值都是指针，改一个函数要连带改数百个调用方与被调用方，无法增量收敛 |
| `pgrust-idiomatic` | 以转译产物为底，一个 crate 一个 crate 重写 | 建立了 `find-next-crate` / `port-crate` / `audit-crate` 三个技能 | 卡在上游正则那 1.6 万行、228 个函数：模型两轮各只改了 11 个函数，分别烧掉 18.5 万与 33.4 万词元（token）；后来靠一次结构化子智能体流程 30 分钟完成，但词元开销比订阅制高一个量级 |
| `pgrust-fabled` | 全新代码库，优先接"接缝"（seam），扩大审计清单 | 通过 100% 回归套件；写那篇复盘时它就是公开版本 | 为把惯用 Rust 写到底，性能约为 Postgres 的 1/8 |

第一代失败时那篇复盘把 planner 的处境称为"器官移植排异"，这个比喻比任何"AI 写代码行不行"的议论都准确：单个组件全对，接口形状不同照样装不回去。第三代留下的方法论最值钱——把"下一个该做哪个 crate"和"做完自己审自己"写成可复用技能，优先实现接缝让偏差尽早暴露。第四代把这两条当输入，另外把前三代的技术债日志一起喂进去。

这里要认准代际，否则会把两份文档读成互相打脸：7 月那篇复盘里"公开版本"指的是 pgrust-fabled，作者直说它比 Postgres 慢 8 倍；今天 `main` 上的 v0.3 属于下一代 `pgrust-fast`，`wasm/README.md` 里就写的是"跑 pgrust-fast 的单用户 `postgres.wasm`"。v0.1 与 v0.3 两份 README 描述的是重量完全不同的项目，`archive/` 分支存在的意义就在这里。

## 上手：三条路径与三条硬约束

按成本从低到高：

```bash
# 1) 浏览器，零安装：完整的 pgrust 服务端编译成 WebAssembly
#    https://pgrust.com —— 输入 SQL，返回 psql 风格的表格

# 2) 本机二进制（macOS Apple Silicon；另有 x86_64 与 universal）
brew install postgresql@18
export PATH="$(brew --prefix postgresql@18)/bin:$PATH"
curl -LO https://pgrust.com/downloads/v0.3/pgrust-0.3-macos-arm64
curl -LO https://pgrust.com/downloads/v0.3/pgrust-0.3-macos-arm64.sha256
shasum -a 256 -c pgrust-0.3-macos-arm64.sha256 && chmod +x pgrust-0.3-macos-arm64
initdb -D /tmp/pgrust-data --no-locale --encoding UTF8 -U postgres
export PGRUST_PGSHAREDIR="$(brew --prefix postgresql@18)/share/postgresql"
export PGRUST_TZDIR="$PGRUST_PGSHAREDIR/timezone"
ulimit -s 65520
RUST_MIN_STACK=33554432 ./pgrust-0.3-macos-arm64 -D /tmp/pgrust-data \
  -k /tmp -p 5432 -c listen_addresses= -c io_method=sync -c max_stack_depth=60000
# 第二个终端
psql -h /tmp -p 5432 -U postgres -c "select version()"
# 期望：PostgreSQL 18.6 (pgrust 0.3)

# 3) 容器：官方 postgres 镜像的直接替换（同名环境变量、同一份初始化脚本目录、同一数据卷路径）
docker run -d --name pgrust -e POSTGRES_PASSWORD=secret -p 5432:5432 malisper/pgrust:v0.3
```

三条硬约束，哪一条没满足都会在第一步就卡住：

1. **`initdb` 和 `psql` 得用上游的。** README 明写 pgrust 目前不自带这两个工具，所以下面每条路径都先装 PostgreSQL 18 的客户端。有趣的是树里已经有 `crates/bin/psql`，`src/main.rs` 第一段注释写着"psql, ported to Rust for pgrust"，范围包括 v3 协议的 startup/auth/simple/extended/COPY、带 psql 提示规则的交互 REPL 和 `print.c` 保真的结果渲染。两句话不矛盾：一个说的是发行物里还没有，一个说的是工作区里已经在做。真要跑起来，按 README 装 `postgresql@18` 的客户端工具最省事。
2. **平台只针对 Graviton4 调优。** 即时编译器只发射 neoverse-v2 指令；在别的机器上能跑，但别拿 README 的数字对照。
3. **扩展 ABI 未稳定，现有扩展装不上。** 上游 contrib 的 57 个模块目录里有 41 个在 `crates/contrib/` 下有了同名 Rust crate，`auth_delay`、`dict_int`、`dict_xsyn`、`intagg`、`oid2name`、`sepgsql`、`vacuumlo`、`xml2` 以及 6 个 plperl/plpython 桥接模块还没有。`PL/Python`、`PL/Perl`、`PL/Tcl` 明确没有，`crates/pl/` 下只有 `plpgsql`。`pgvector` 和它的 HNSW 构建 crate 在 `crates/contrib/` 里——那是内置移植版，不是能 `CREATE EXTENSION` 加载的外部扩展。

版本升级还有一条破坏性改动：v0.3 把 `cbstore` 整体改名 `pgrcolumnar`，`CREATE INDEX ... USING cbstore` 一类的旧 DDL 直接失效，README 要求改写。改名规则、保护清单和符号对照在归档分支的 `RENAME-MAP.md` 里，其中一条细节是格式血缘名（`cbstore8-v6`）、`PGRUST_CBSTORE_*` 环境变量与脚本文件名一律不改，因为那是历史标识。

## 按现象排查

前五行的报错文本与处理办法直接来自 README 的 Quickstart 与 Stopping, restarting, cleaning up 两节；后三行是这份仓库现状带来的——第 7 行的参数同样写在 README 里，只是它不报错，只会崩。

| 现象 | 直接原因 | 处理 |
| --- | --- | --- |
| `FATAL: lock file "/tmp/.s.PGSQL.5432.lock" already exists` | 5432 上已有服务端，多半是本机 PostgreSQL | 换端口 `-p 5433`，并用 `psql -h /tmp -p 5433 -U postgres` 连；连上后先看 `select version()` |
| `could not open directory "/usr/local/pgsql/share/timezone"` | `PGRUST_PGSHAREDIR` / `PGRUST_TZDIR` 没在跑服务端的这个 shell 里导出 | 重新导出两个变量；Debian/Ubuntu 上 `PGRUST_TZDIR` 指向 `/usr/share/zoneinfo` |
| macOS 弹"Apple 无法验证…恶意软件" | 用浏览器下载带了 quarantine 属性，且二进制尚未公证 | `xattr -d com.apple.quarantine <文件>`，或在系统设置里"仍要打开"；改用 `curl` 下载则不会触发 |
| Homebrew 装的 `initdb` 找不到 | `postgresql@18` 是 keg-only，不进 PATH | 按 README 导出 `$(brew --prefix postgresql@18)/bin` |
| 一切正常但行为不像 pgrust | 静默连到了本机原版 Postgres | 看 `select version()` 有没有 `(pgrust 0.3)` 字样 |
| 性能明显低于 README | 下载的是通用架构二进制，且非 PGO 构建 | 自己 `./build-pgo.sh`（README 与套件都提示这一步要数小时）；或在 Graviton4 上测 |
| 栈溢出 / 深度递归语句异常 | 线程模型的栈尺寸要显式给 | `ulimit -s 65520` 与 `RUST_MIN_STACK=33554432`，并按 README 设 `max_stack_depth=60000` |
| 想照 README 用 `benchmarks/` 或 `Dockerfile` 却 404 | 这两个路径不在 `main` 的提交树上 | `git checkout archive/v0.2-main-2026-09-15`，或直接用 Docker Hub 上的 `malisper/pgrust:v0.3` |

源码构建的依赖也和 v0.1 时期不同：`rust-toolchain.toml` 把工具钉在 Rust 1.96.0，rustup 会自动装；真正的外部依赖只有 RE2 正则库（Debian/Ubuntu `libre2-dev`，macOS `brew install re2 pkg-config`）。README 说明这是故意的——release 构建缺 RE2 就拒绝编译，因为回退正则引擎在正则密集负载下慢得离谱。发布的二进制额外用 `--profile dist`（fat LTO）构建，代价是编译时间显著变长。

## 谁该现在试，谁再等

现在动手有明确价值的：

- **读 Postgres 内部。** `crates/backend/` 的 26 个子系统与上游 `src/backend/` 逐层同名，归档分支上的 `CATALOG.tsv` 用 `c_sources` 一列把每个单元映射到具体 C 文件。定位一个子系统的入口，比在 2,463 个 `.c`/`.h` 里翻要快。
- **想抄"怎么证明重写没跑偏"。** `proofs/` 的双执行 harness 与台账结构、`regress/` 的三套覆盖层、`benchmarks/` 里那两条纪律（语料不重叠证明、二进制 sha256 记账），可以直接搬到任何遗留系统重写项目上。
- **要一个能改的 Postgres 行为实验台。** 在浏览器里那条 WASM 演示就能试语义，不占本地端口。
- **数据库/编译器方向的写作者与讲师。** 四次尝试的失败序列、5 亿行求和的性能台阶、四个上游 bug，都是能独立讲清机制的例子。

再等一等的：

- **生产 OLTP，以及任何装了你不敢丢的数据。** README 的措辞已经从 v0.3-beta 时期的 `pgrust is not production ready. Do not put data you care about in it.` 变成"暂不建议生产使用，但我们内部已在非关键环境成功运行，不可丢的数据仍以 Postgres 为准"。方向明确，强度也仍然有限——同段还写着"它仍然有很多 bug，当前第一优先级是测试与可靠性"。
- **依赖扩展生态的系统。** 扩展 ABI 未稳定，plperl/plpython 桥接模块未移植。
- **需要分布式的一体化方案。** pgrust 是单节点，路线图上的 Autoscaling 与 instant forking 都还没实现。
- **准备提 PR 的人。** README 写着目前不主动接收合并请求，但欢迎开 issue 报破坏、报安装困惑、报希望对齐的 Postgres 行为。

和相邻路线的分工，只按公开定位陈述：

| 方案 | 改的是哪一层 | 与 pgrust 的分界 |
| --- | --- | --- |
| pgrust | 服务端实现整体替换，目标行为不变 | 少见地把"逐字节贴上游 + 形式化证明"当成主主张 |
| CockroachDB、YugabyteDB | 兼容 PostgreSQL 协议与方言，存储与事务自研 | 换来分布式，代价是语义边界与上游不完全重合 |
| Greenplum、openGauss 这类派生 | 在上游源码上做深度改造 | 与上游共同演化，但磁盘/行为兼容面被改动 |
| PgBouncer、pgcat | 连接池与路由，不碰内核 | 解决连接数症状，不触及进程模型 |

pgrust 押的是一条窄路：既不换语义也不换格式，所以继承整个 psql 生态与现有数据目录，代价是任何性能收益都必须先过逐字节比对。

## 动手练习

想花半天得到一次真实判断，按这个顺序做，每步都有可核对的输出：

1. 打开 <https://pgrust.com>，在交互终端里执行 `select version();`，再建一张小表插几千行、跑一次带 `like` 过滤的 `count(*)`。这一步只验证 WASM 那条路径通不通：`wasm/README.md` 写明它是单用户服务端 + 内存 VFS，别拿这里的耗时当性能证据。
2. 本机按上面第二节启动服务端，跑 `psql -h /tmp -p 5432 -U postgres -f crates/postgres-18.6-reference/src/test/regress/sql/strings.sql`，再对照同目录的 `expected/strings.out`。这是把第一层证据缩到单个文件重放；`strings.out` 里有 75 行以 `ERROR` 开头，这个测试本来就在测非法语法，逐字节一致包含错误行一致。
3. 打开 `proofs/USER_FACING_FUNCTIONS.tsv`，用 `awk -F'\t' '$4 ~ /^proved\(/' proofs/USER_FACING_FUNCTIONS.tsv | wc -l` 复算已证行数，再和 `proofs/README.md` 里的 1,086 对一下——你会直接经验到本文说的那个数字不一致。
4. 在 `main` 上执行 `test -f Dockerfile && echo yes || echo no`，然后 `git checkout archive/v0.2-main-2026-09-15` 再执行一次。

## 六个自测题

1. pgrust 说回归套件全过，判定单位是什么？为什么说这决定了 46,066 能不能被复算？
2. 一个绿色（proved）的 Kani harness 能保证函数在所有合法输入上都与 C 版等价吗？
3. 为什么把 C 版逐行转译成 unsafe Rust（第二代）反而不能进入生产演进？
4. README 说 ClickBench 上领先 ClickHouse 18.5%，基准套件说约 7%，你该用哪个数字向同事汇报，为什么？
5. 想在非 Graviton 机器上验证 pgrust 的读性能，哪些前提条件必须同时满足，否则测的是别的东西？
6. 现有 Postgres 扩展在 pgrust 上能用吗？如果不能，`crates/contrib/pgvector` 是什么？

<details>
<summary>答案</summary>

1. 判定门槛是 `parallel_schedule` 里 231 个测试文件的期望输出逐字节一致，单位是"测试文件"。46,066 不是文件数（231/233/265），不是期望输出行数（277,159），也不是 `sql/` 里的分号数（53,281），口径记录在 `main` 上缺失的 `docs/conformance/README.md` 里，所以按当前 `main` 复算不出来。
2. 不能。证明只在 harness 声明的输入长度与循环展开界限内成立，界限写在台账的 `status` 括号里和 `notes` 列。这也是台账比"已证 X 个"这个数字更有信息量的原因。
3. 语义上等价，但不可演进：转译产物到处是指针与 `unsafe`，安全化一个函数会牵动数百个调用方与被调用方，改不动也没法增量收敛。它甚至 ABI 兼容、扩展能直接加载，可是"能跑"与"能持续改"是两件事。
4. 都不该直接引用。它们指向同一类自定义口径：`combined = hot_geo^0.6 * cold_geo^0.2 * load_ratio^0.1 * size_ratio^0.1`，打分脚本注明"这是我们的权重，不是 ClickBench 的"。三个数各自对应哪次构建、哪种存储、哪个数据装载分支，仓库里没写明。要汇报就说"在 Graviton4 + gp2 参考存储 + PGO 构建下，按 pgrust 自定义 combined 口径领先约 7%–18.5%"，并补一句脚本不在 `main` 上、当前无法就地复现。
5. 即时编译器只发射 neoverse-v2 指令，下载的二进制是通用架构构建。所以非 Graviton4 平台、或没有用 `-Ctarget-cpu=neoverse-v2` 与 PGO 自建时，测到的是另一个负载；再加上 `io_method=sync`、`max_stack_depth` 这类必需 GUC，以及 `fsync` 保持默认——关掉持久化之后的收益是另一回事。
6. 不能。上游 contrib 的 57 个模块目录里有 41 个在 `crates/contrib/` 下有了同名 Rust crate，`auth_delay`、`dict_int`、`intagg`、`sepgsql`、`xml2`、`vacuumlo` 等还没有，扩展 ABI 也尚未稳定。`pgvector` 不在上游 contrib 里，它是被内置移植进来的第三方扩展，用法与加载外部 `.so` 完全不同。

</details>

## 下一步读哪份代码

按问题选入口，都比从参数表读起划算：

- 想知道一个单元对应哪些 C：归档分支上的 `CATALOG.tsv`（1,241 行），先看 `status` 与 `bench_ratio` 两列。
- 想知道哪些函数已经证明、证到什么界限：`proofs/USER_FACING_FUNCTIONS.tsv`，配合 `proofs/README.md` 的 12 条分歧与 `proofs/TRIAGE.md`。
- 想知道"证了多少"是不是"跑了多少"：`proofs/COVERAGE.md`，它把 Kani、差分模糊、回归三条线的行级覆盖合并成一份产物，并且开篇就警告覆盖不等于验证。
- 想知道崩溃与并发行为怎么测：`crash-simulator/src/bridge.rs` 的模块注释是全仓最集中的一份说明，再看 `src/oracle/props/` 与 `profiles/`。
- 想知道数字是怎么来的：`benchmarks/README.md`（在归档分支）的 hardware of record 与 What to expect 两段，加上 `benchmarks/scorers/score-clickbench.py` 的指标注释。
- 想知道浏览器的 pgrust 是怎么塞进 wasm 的：`wasm/README.md`，它写清了 `wasm32-wasip1`、panic=unwind 经标准 Wasm 异常处理降级、以及恰好 33 个 `wasi_snapshot_preview1` 导入。
- 想读机制解释：作者四篇专文——三次死路的复盘、分析性能的执行器复盘、JIT 那篇、以及"四个骑马人"那篇动机文。

## 参考资源

以下链接均在 2026-09-19 逐条访问确认可达（HTTP 200）。

- 仓库（`main` 为 v0.3 单提交快照 `79ad992`）：<https://github.com/malisper/pgrust>
- 归档分支：`archive/pre-fabled-2026-06-25`、`archive/v0.1-main-2026-07-29`、`archive/v0.2-main-2026-09-15`，以及 `v0.3-beta`
- 仓库内一手文档：`README.md`、`crash-simulator/Cargo.toml` 与 `src/bridge.rs`、`docs/fuzzing/rulings.toml`、`proofs/README.md`、`proofs/COVERAGE.md`、`wasm/README.md`；`benchmarks/README.md`、`GOAL.md`、`RENAME-MAP.md`、`CATALOG.tsv` 需切到 `archive/v0.2-main-2026-09-15` 才看得到
- 浏览器演示：<https://pgrust.com>；更新订阅：<https://pgrust.com/#updates>；X：<https://x.com/pgrustdb>；Discord：<https://discord.gg/FZZ4dbdvwU>
- 作者一手复盘：[pgrust: rebuilding Postgres in Rust with AI](https://malisper.me/pgrust-rebuilding-postgres-in-rust-with-ai/)、[Postgres in Rust: three dead ends before we passed 100% of the regression suite](https://malisper.me/postgres-in-rust-regression-suite/)（2026-07-16，07-22 更新）、[pgrust passes 100% of the Postgres regression tests](https://malisper.me/pgrust-passes-100-of-postgresqls-regression-tests/)（2026-06-25）、[The four horsemen behind thousands of Postgres outages](https://malisper.me/the-four-horsemen-behind-thousands-of-postgres-outages/)、[Rebuilding Postgres for 300x faster analytics](https://malisper.me/how-we-made-postgres-hundreds-of-times-faster-the-query-engine/)、[JIT Compiling Code in 5μs](https://malisper.me/how-ai-changes-the-economics-of-jit-compilers/)、[pgrust update: at 67% Postgres compatibility](https://malisper.me/pgrust-update-at-67-postgres-compatibility-and-accelerating/)
- PlanetScale 演讲视频：<https://www.youtube.com/watch?v=7L_nG3EBjck>
- 工具：[Kani](https://github.com/model-checking/kani)（Rust 模型检验，底层是 CBMC）、[Antithesis](https://antithesis.com)（确定性模拟测试）

三处显式 unresolved，留给后续复核：46,066 的计量单位（依据文件不在 `main`）；ClickHouse 领先幅度三个值各自的运行条件；根 README 的"约 1000 已证"与 `proofs/README.md` 的"1,086"和台账实测 1,336 之间的换算规则。

维护这份文稿时先做三件事：`git clone --filter=blob:none --no-checkout` 拿最新 `main`，比对 `git ls-tree --name-only HEAD` 与文中列出的顶层清单；重跑 `parallel_schedule` 与 `USER_FACING_FUNCTIONS.tsv` 的计数；再读一遍 `README.md` 的 Status 与 Performance 两节。文中所有"截至 2026-09-19"的判断在以下任一条件下失效：`main` 出现第二个提交（说明公开树回到增量历史）、出现 `docs/conformance/` 目录（46,066 口径可以定案）、或 README 的 badge 版本号不再是 v0.3。
