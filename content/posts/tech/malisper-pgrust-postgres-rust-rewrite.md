---
title: "pgrust 架构拆解：用 Rust + AI 重写 PostgreSQL 是怎么做到的"
slug: malisper-pgrust-postgres-rust-rewrite
date: 2026-07-13T03:03:14+08:00
lastmod: 2026-07-13T03:03:14+08:00
draft: false
categories: ["技术笔记"]
tags: ["Rust", "PostgreSQL", "数据库", "重写", "源码分析"]
description: "pgrust 是 malisper 用 Rust 重写 PostgreSQL 18.3，磁盘兼容、回归套件 100% 通过。本文解读其线程模型改造、回归 oracle 选择与性能数据应如何解读。"
---

# pgrust 架构拆解：用 Rust + AI 重写 PostgreSQL 是怎么做到的

## 核心判断

pgrust 解决的不是"做一个 Rust 版的 Postgres 客户端"或"做一个协议绑定"，而是**把 PostgreSQL 整个 server 重写成 Rust，并保持磁盘兼容（可直接 boot 现有 pg 18.3 data dir），同时通过 Postgres 自带 4.6 万多条回归查询做 orcale 验证**。这是它的硬性约束：行为贴 Postgres、不重写 SQL 协议、不发明新存储格式。这一约束决定了它的取舍——能改的是内部实现，不能改的是对外兼容面。本文从这个约束倒推它的架构边界。

## 项目坐标

| 维度 | 数据 |
|------|------|
| 仓库 | malisper/pgrust |
| Stars | 约 2.4k（截至 2026-07） |
| 主语言 | Rust（95%+） |
| License | AGPL-3.0 |
| 目标兼容版本 | PostgreSQL 18.3 |
| 回归测试通过 | 100%（README 顶部 badge 标注 regression queries 46k+）|
| 仓库体积 | ~272 MB（含 `vendor/postgres-18.3/`） |
| 主入口 | `crates/` workspace，bin 名 `postgres`（重命名版 pg server） |

> README 顶部一段很重要：项目在 2026-06-23 前后换了实现（README 的 History 段指向 `archive/pre-fabled-2026-06-23`）。新版本（HEAD）声称"线程每连接" + 比 Postgres 在事务型 workload 快 50%、分析型 workload 快 300x、对照 clickbench 仅 2 倍慢于 ClickHouse。这意味着**新版本和 archive 版本的内部架构有较大差异，本文主要解读 HEAD 版本**。

## 反直觉的"非典型数据库内核"取舍

### 1. 不是绑定，是完整的 server

很多"X 语言版的 PostgreSQL 库"实际是 `libpq` 的封装或 Rust 写的协议层（用 wire protocol 跟真的 Postgres 通信，例如 `tokio-postgres`、`rust-postgres`）。pgrust 不在这条路线上——它直接接收 `psql` 客户端发过来的连接，自己处理 SQL 解析、优化、执行、回包。

这点有个直接证据：仓库根目录下 `Dockerfile` + `docker/` 子目录构建的是 `malisper/pgrust:v0.1` 镜像，启动后通过镜像内的 `psql` 客户端连 `localhost:5432`。下游用户不需要换客户端工具，**保留一套 PostgreSQL 生态（psql、pgAdmin、BI 工具、ORM）的兼容性，是这个项目最大的杠杆**。

### 2. 磁盘兼容现有的 Postgres data dir

```bash
target/release/postgres --initdb \
  -D /tmp/pgrust-data \
  -L "$PWD/vendor/postgres-18.3/share" \
  --no-locale \
  --encoding UTF8 \
  -U postgres
```

启动时不指定 `-L` 时，pgrust 也能从"别的 Postgres 进程生成"的 data dir 启动——因为 README 明说"disk compatible with Postgres and can boot from an existing Postgres 18.3 data directory"。

这个约束意味着：pgrust 不能改 `pg_class` / `pg_attribute` 之类的系统表布局，不能改 WAL 记录的 magic 字节，不能改 heap page 的 header 结构，不能改 B-tree 的 split 算法语义。它要做的，是**用 Rust 实现同样的格式语义，但允许内部数据结构、并发模型、内存布局做替换**。这也是所有"无破坏性内核替换"路径的共同点——保留 on-disk 与 wire format 是迁移成本的护城河。

### 3. 把 Postgres 自带回归测试当 oracle

README 的回归段落：

```bash
PGRUST_BIN="$PWD/target/release/postgres" \
scripts/run-regression
```

README 末段声称这是"verified launch result: pgrust matched Postgres's expected output across more than 46,000 regression queries"。换句话说，pgrust 的"正确性"不是自己写的单元测试集说了算，而是原版 Postgres 写了几十年的回归测试集说了算。这套 oracle 把 pgrust 的 spec 固定到一个外部权威实现上，而不是"作者认为 Postgres 应该这样工作"。

> 这种 oracle 模式在重写项目里非常少见——很多数据库重写是直接走 TPC-C / YCSB 之类工业 benchmark，但那些 benchmark 测的是性能维度，对行为正确性的覆盖度不够。pgrust 的 4.6 万条回归查询里包含解析错误、事务回滚、嵌套子查询、约束冲突、字符集边界等大量行为测试，是目前**对"PostgreSQL 是否行为真的一样"最强的 oracle**。

## 系统地图：模块切分

仓库根目录的几个关键元素：

| 模块 | 位置 | 用途 |
|------|------|------|
| `crates/` | Rust workspace | pgrust 自身实现的多 crate 拆分 |
| `vendor/postgres-18.3/` | pg 18.3 源码 | 测试用 orcale + 兼容性参考（不是 pgrust 的运行时依赖，是构建期校验） |
| `scripts/run-regression` | shell 脚本 | 执行 pg 回归测试集 |
| `docker/` | Docker 文件 | 容器化启动 |
| `Dockerfile` | Docker 镜像构建 | 与 docker/ 配合 |
| `Cargo.toml` / `Cargo.lock` | workspace 总配 | `cargo build --release --locked --bin postgres` |
| `archive/pre-fabled-2026-06-23` | git 历史 | 旧版 pgrust 实现，与 HEAD 行为差异较大 |

HEAD 版本 README 提到已经 100% 通过 4.6 万条回归查询，且写入新设计："thread per connection model instead of process per connection"——这是把 Postgres 经典的 "fork 一个进程给每个连接" 模型改成"每连接一个 OS 线程"。这条改动单独看就是地震级取舍（影响共享缓冲、信号处理、子事务、连接数上限、内存耗尽策略），但 README 把它描述为已落地的优化而不是路线图，意味着它已经在新版本里跑通。

## 任务流案例：一条 SQL 从客户端到结果

把抽象机制用一个简单的 `SELECT version()` 串起来，看它在 pgrust 内部的流动路径：

```
psql 客户端
  │
  │  TCP 5432（标准的 pg wire protocol v3）
  │
  ▼
┌───────────────────────┐
│ pgrust main loop      │
│ - accept connection   │
│ - spawn pthread       │  ← thread per connection
│ - feed socket → conn  │
└───────────────────────┘
  │
  ▼
┌───────────────────────┐
│ Connection state      │
│ - per-conn backend    │
│ - per-conn memory ctx │
│ - per-conn transaction│
└───────────────────────┘
  │
  │  parse "select version(), 1 + 1 as two" → pg_query AST
  ▼
┌───────────────────────┐
│ Parser                │
│ - 同 pg 18 grammar    │
│ - 同一棵 parse tree   │  ← 行为一致 oracle
└───────────────────────┘
  │
  │  AST → planner → optimized plan
  ▼
┌───────────────────────┐
│ Planner / Optimizer   │
│ - Cost-based          │
│ - Stats 走 pg 系统表   │  ← 读 pg_statistic, pg_class
└───────────────────────┘
  │
  ▼
┌───────────────────────┐
│ Executor              │
│ - volcano-style       │
│ - 节点：SeqScan /    │
│   FunctionScan /      │
│   Arithmetic / Result │
└───────────────────────┘
  │
  ▼
┌───────────────────────┐
│ Storage               │
│ - Heap page format 同 │
│   pg 18.3             │  ← 磁盘兼容
│ - WAL 同 pg 18.3      │
│ - 共享缓冲（线程模型） │
└───────────────────────┘
  │
  ▼
┌───────────────────────┐
│ 结果序列化            │
│ - DataRow message     │
│ - ReadyForQuery       │
└───────────────────────┘
  │
  ▼
psql 客户端
postgres  | 1 + 1 | 2
```

> 关键观察：`pg 18.3 grammar / heap page format / WAL format / system catalogs` 这四条边界**全部贴 Postgres**，因此上述案例的"对外可观察行为"应当与原版 Postgres 在那一行字节上完全一致。oracle 是 pg 回归测试集，不是 pgrust 自己写的。

## 关键设计取舍

### 1. 线程每连接 vs 进程每连接

Postgres 多年延续 "**fork per connection**" 模型，原因是稳定性——一个连接崩溃，别的连接不受影响，且 `fork()` 让每个 backend 拥有独立的内存空间。代价：

- **连接数 = 进程数**：每个连接一份虚拟内存，每个连接占用独立内存页表，无法跨连接共享 OS page cache 之外的优化机会。
- **跨连接通信成本高**：共享内存需要 `shmget`、`mmap`，信号机制复杂。
- **进程 fork 的开销**：在连接突发时延迟可见。

pgrust 改成 "**thread per connection**"（README 措辞：thread per connection model instead of process per connection），意味着：

- 同一进程内的线程可直接共享部分数据结构（缓冲池、缓存、元数据）。
- 不再有 fork 带来的内存膨胀，连接突发时延下降。
- 但也意味着连接的崩溃半径从"自己进程"扩大到"整个 server"——需要 Rust 的 panic 隔离（catch_unwind 或 per-thread panic hook）来约束一个连接 panic 不杀死整个 server。

这个 trade-off 是否值？理论上是巨型改进（Postgres 用户多年吐槽的连接数 + 内存碎片问题），但是孤儿资源（一条连接持有的内存、外部资源 fd）在 thread 模型下的回收比 fork 模型更微妙。这是回归测试 oracle 体现价值的地方——同样的 4.6 万条 query 行为必须保持。

### 2. 仓库 vendor 整份 Postgres 源码

`vendor/postgres-18.3/` 占仓库 ~272 MB 大部分的体积。原因不是 pgrust 编译时依赖 pg 源码（Rust workspace 不靠它），而是**回归测试 oracle 需要 pg 自带的 SQL 测试文件 + 期望输出**：

```bash
PGRUST_BIN="$PWD/target/release/postgres" scripts/run-regression
```

脚本会调用 pgrust 的 `--initdb`、`psql` 客户端连接 pgrust、跑 pg 18.3 的官方测试文件集。vendor 这部分是 oracle 的输入，不参与构建。

> 这个设计有副作用：任何想要 fork pgrust 的开发者必须接受 ~272 MB 的额外下载。在 CI 上成本也明显，但相对 4.6 万条 oracle 来说，这笔投入是值得的。

### 3. 性能数据需要小心解读

README 顶部 update 段：

> Currently passes 100% of Postgres regression suite, has a thread per connection model instead of process per connection, is 50% faster than Postgres on transaction workloads, and is ~300x faster than Postgres on analytical workloads (2x slower than Clickhouse on clickbench and we think it can get faster than Clickhouse).

读这段需要区分四类判断：

1. **100% regression pass**——行为正确。这是 binary 结果，没有"测什么 workload"的问题（4.6 万条测试覆盖范围广）。
2. **50% faster on transaction workloads**——这是"事务型 workload"的对比，但具体哪种事务型（点查、高并发 TPC-C-like、写多读多）？README 没有明确给出 TPC-C / sysbench-pg 等具体 benchmark 名字。
3. **300x faster on analytical workloads**——这里指的是 ClickBench 一类侧重单表扫描/聚合的分析型 query，但同样没明确给出具体测试集与配置。
4. **2x slower than ClickHouse on clickbench**——ClickBench 是一个公开的 benchmark，所以这个对比可以复核。

> 性能数字必须配 oracle + benchmark 脚本才能验证。单看 README 这段，"300x faster"是一个**开发者自声明的数字**，需要等仓库或下游提供公开复现脚本才能形成可重复结论。

### 4. 状态：不生产就绪

README 显式写："pgrust is not production-ready yet. It is not performance optimized yet."——这是诚实声明，包括：

- 没有兼容 PL/Python、PL/Perl、PL/Tcl 之类的过程语言扩展。
- 没有完全实现所有 contrib 模块。
- 没有经过第三方审计。

换句话说，**用 pgrust 当 production 数据库是 README 自己警告过的**。它目前的合理用法是：研究 / 教学 / 内部玩具 / 给原版 Postgres 提 issue 时复现 bug。

## 路线图与"作者想做什么"

README Roadmap 段列了 7 项，每一项都不是单纯性能优化，而是**Postgres 长期想改但很难改的事**：

| 方向 | 改动幅度 | oracle 阻力 |
|------|----------|-------------|
| 多线程 Postgres 内部 | 大（已经开始） | 中（行格式不变） |
| 内置连接池 | 中（Postgres 长期想加 pg_bouncer 集成） | 小 |
| 更好的 JSON 重 workload | 大（JSONB 路径表达式计算 + 索引） | 中（行为 oracle） |
| 快速 fork / branching 工作流 | 大（schema 分支） | 大 |
| 存储实验，包括无 vacuum 设计 | 极大（改 heap / autovacuum 行为） | 极大（与现有 data dir 兼容冲突） |
| 对坏 query 与 AI 生成 SQL 的 runtime guardrail | 中（新增组件） | 小 |
| 减少"突然的坏 plan 切换" | 中（planner 改造） | 中 |

> 这个 roadmap 的核心信号是：**保留磁盘兼容 + 测试 oracle 不破坏**。任何改动只要破了这两条，就脱离了 pgrust 的价值主张。这也是为什么 README 不敢说"5.0 / 6.0 性能 + 100% 兼容 + 增加商业特性"三件齐上的原因。

## 适用场景与采用顺序

### 谁该先用

- **Postgres 内部研究者 / 数据库内核学习者**——多了一条源码可读路径（Rust 比 30 万行 C 容易读）。
- **Postgres 贡献者 / patch 评审者**——能用 pgrust 当 sandbox 验证某个补丁的 oracle 影响。
- **教学场景 / 公司内部培训**——能在不用装 Postgres C toolchain 的情况下部署一个能跑的 pg 兼容 server。
- **AI 工具研究者**——pgrust 自己就是用"AI 辅助编程"做的（README 用词是"AI-assisted programming"），这个项目本身就是一份案例。

### 谁不该用

- **生产 OLTP**——README 明确不 production-ready。
- **依赖 PL/Python 之类的扩展栈**——兼容性没收口。
- **要求 100% Postgres 原版 bit-perfect 兼容性，且需要保留每个 contrib**——目前没承诺这个 SLA。
- **追求 ClickHouse 级别分析性能**——README 自承 2x 慢于 ClickHouse，且未公开复现脚本。

### 从哪里开始尝试

```bash
# 1. Docker（最快，零本地依赖）
docker run -d --name pgrust -e POSTGRES_PASSWORD=secret malisper/pgrust:v0.1
docker exec -it -e PGPASSWORD=secret pgrust psql -h 127.0.0.1 -U postgres

# 2. 源码构建（需要 libpq + icu + openssl）
brew install icu4c openssl@3 libpq
git clone https://github.com/malisper/pgrust
cd pgrust
cargo build --release --locked --bin postgres

# 3. 跑回归测试（确认在自己机器上 oracle 全过）
PGRUST_BIN="$PWD/target/release/postgres" scripts/run-regression

# 4. WebAssembly demo（无需安装，浏览器即跑）
# https://pgrust.com
```

## 与"Postgres 重写项目"的边界

历史上重写 PostgreSQL 内核的项目不少，对照看：

| 项目 | 语言 | 状态 | 与 pgrust 的差异 |
|------|------|------|------------------|
| pgrust | Rust | 早期，46k+ 回归通过 | 重写 + 磁盘兼容 + AI 辅助 |
| CockroachDB | Go | 生产 | 分布式 Postgres 兼容，重新发明存储 / 事务 |
| YugabyteDB | C++ | 生产 | 分布式 PostgreSQL 兼容层 |
| Amazon Aurora | C++/Rust 部分 | 商业 | 闭源，分裂存储 + 计算 |
| openGauss / MogDB | C | 生产 | Postgres 深度 fork |
| pgcat / pgpool | C/Rust | 生产 | 连接池 + 负载均衡，不重写内核 |

> pgrust 的独特之处：**单节点、磁盘兼容、行为贴 Postgres 18.3**。这条路线既能继承 psql 生态，又能让 Postgres 内部更容易演进（Rust + AI 辅助确实是进程友好得多）。代价是失去了分布式扩展的能力——那是 CockroachDB / YugabyteDB 的地盘。

## 阅读路径建议

1. **先看 README + Roadmap**——项目的边界声明非常清晰，先确认自己关心的改动属于 roadmap 哪一条。
2. **跑一次 `scripts/run-regression`**——10 分钟内能确认 HEAD 在你机器上 oracle 全过；如果失败，先看 diff 通常是已知 issue。
3. **翻 `crates/` workspace**——按依赖图（`Cargo.toml` 的 `dependencies`）从底层 crate 开始读，向上找具体的执行路径。
4. **对照 `vendor/postgres-18.3/`**——任何"这个行为对吗"的疑问，用原版 pg 源码做 orcale。
5. **关注 Discord / 更新邮件**——README 提到的持续更新节奏很快，master 分支每周都有结构改动。

## 参考资源

- 主仓库：`https://github.com/malisper/pgrust`
- 官网 + WASM 演示：`https://pgrust.com`
- Discord：`https://discord.gg/FZZ4dbdvwU`
- 原始 launch 文章（malisper 博客）：`https://malisper.me/pgrust-rebuilding-postgres-in-rust-with-ai/`
- 67% 回归更新：`https://malisper.me/pgrust-update-at-67-postgres-compatibility-and-accelerating/`
- Four Horsemen 路线图背景：`https://malisper.me/the-four-horsemen-behind-thousands-of-postgres-outages/`
- 旧实现归档：`archive/pre-fabled-2026-06-23` 分支
- 联系：`maintainers@pgrust.com`
