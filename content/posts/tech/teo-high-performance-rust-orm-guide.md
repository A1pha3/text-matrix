---
title: "TEO 0.4：从多语言框架收缩成纯 Rust ORM，四库统一但仍在 WIP"
date: "2026-05-11T12:55:00+08:00"
slug: "teo-high-performance-rust-orm"
github_repo: "teodevgroup/teo"
description: "TEO 0.4 是 teodevgroup/teo 的方向性重写：把多语言 schema 驱动 Web 框架收敛为纯 Rust ORM。MySQL、PostgreSQL、SQLite、MongoDB 共用一套 API。项目标注 WIP，最新发布 0.4.0-alpha.0，本文基于官方仓库核实并给出诚实的使用建议。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "数据库", "PostgreSQL", "ORM"]
hiddenFromHomePage: true
---

# TEO 0.4：从多语言框架收缩成纯 Rust ORM

## 核心判断

TEO 值得关注的地方不在"又一个高性能 Rust ORM（对象关系映射）"，而在 0.4 这次方向性重写。它原本同时维护 Rust、Node.js、Python 三套服务端实现，是 schema（模式）驱动的 Web 框架。现在被收缩成**纯 Rust ORM**。MySQL、PostgreSQL、SQLite、MongoDB 统一到一套 API（应用程序接口）上。

这次收缩是作者对维护成本的明确回应。官方仓库自 0.4 起标注 WIP（Work In Progress）。最新发布停留在 [0.4.0-alpha.0](https://lib.rs/crates/teo)，发布于 2025 年 8 月 2 日，基于 Rust 2024 edition。结论先放在这里：**方向清晰、四库统一是真实卖点，但 API 尚未稳定。** 技术观察可以现在开始，生产选型要等 stable。

## 系统地图：0.4 仓库里有什么

0.4 的 Cargo workspace 只包含三类 crate，外加一组集成示例：

```text
teo/               — ORM 核心
teo-derive/        — 过程宏（模型声明相关）
teo-column-type/   — 列类型系统
examples/axum-integration/   — 与 Axum 的集成示例
    ├── mongodb / mysql / mysql_async
    ├── postgres / tokio-postgres / rusqlite
```

官方 README 声明的能力清单，以及我在仓库里能验证到的程度：

| 官方声明 | 仓库证据 | 现状 |
|---------|---------|------|
| 支持 MySQL / PostgreSQL / SQLite / MongoDB | workspace 与示例目录一一对应 | 已确认 |
| 全异步（Fully asynchronous） | README 明确列出 | 已确认 |
| 增量数据库迁移 | README 列出，roadmap 有对应条目 | 已确认方向，细节待文档 |
| 易于使用的查询 API | README 列出 | 已确认方向，API 未稳定 |
| 高性能 | README 定位语 | 无独立 benchmark 可佐证 |

## 为什么需要另一个 Rust ORM

Rust 生态已有的 ORM / SQL 工具各走一路：

| 工具 | 定位 | 数据库 | 特点 |
|------|------|--------|------|
| Diesel | 成熟 ORM | MySQL / PG / SQLite | 同步 API，编译期查询验证 |
| SQLx | SQL 工具 | 多种 | 编译期验证，运行时执行 |
| SeaORM | 异步 ORM | MySQL / PG / SQLite | ActiveRecord 风格 |
| **TEO** | 高性能 ORM | 上述 + MongoDB | 声明式 Schema + 增量迁移，目标四库统一 API |

TEO 想拉开差距的是三件事：

1. **四库统一**。SQL 和 MongoDB 共用同一套查询与写入语义，不用为两种数据模型维护两套访问代码。这是它在官方 README 里反复强调的定位。与 Diesel / SQLx 最直接的区别在于，后两者对 MongoDB 基本不覆盖。
2. **声明式 Schema + 增量迁移**。模型定义即数据库结构，Schema 变更自动生成增量 SQL，减少手写 `ALTER TABLE`。
3. **重写后的纯 Rust 内核**。0.4 放弃 Node.js / Python 服务端实现。内核收敛到单一语言，异步能力建立在 Tokio 之上。

要注意的是，上面第 2、3 点目前都在 WIP 状态下，API 形态与旧版不同，官方示例也还在补充中。下文会展开这层不确定性。

## 版本演进：一次主动收缩

TEO 的版本历史解释了"为什么会有这次重写"：

- **0.2.x / 0.3.x**（2022-2024）：schema 驱动的多语言 Web 框架。该版本同时提供 Rust、Node.js、Python 服务端实现。它还生成 TypeScript / Swift / Kotlin / C# / Dart 前端查询客户端。crates.io 上 0.2.19 的 README 完整保留了这套定位。
- **0.4**（2025-08 起，当前 alpha）：纯 Rust ORM。官方在 lib.rs 的版本说明里说得很直接：把 TEO 重写成纯 Rust ORM。移除对 Node.js 和 Python 的支持。

把多语言服务端改成单语言，维护的不再是"一个项目四个实现"，而是"一个内核 + 按需生成的客户端"。这是架构决策，不是单纯的功能增删。重写后的 TEO 更聚焦，也更 Rust-native。代价是旧版文档中的 Node.js / Python 示例和 API 全部失效。迁移到 0.4 需要重新适应。

## 怎么开始（按官方 README）

官方 README 给出的安装方式是按数据库开 feature 引入依赖：

```toml
teo = { version = "0.4", features = ["postgres"] }
```

把 `features` 换成 `mysql` / `sqlite` / `mongodb`，即对应不同数据库。项目协议为 MIT，代码全部是 Rust。快速上手以 [官方 quickstart](https://docs.teodev.io/getting-started/quickstart) 为准。

## 核心机制：能确认的与还不能确认的

### 能确认的：四库同一套 API

从 workspace 的示例目录可以确认这一点。mongodb / postgres / mysql / sqlite 各有一套 Axum 集成。TEO 0.4 的目标是把数据库差异封装在连接器层，上层代码不感知具体数据库。SQL 侧和 MongoDB 侧各有连接器 crate 支撑，例如 `teo-sql-connector`、`teo-mongodb-connector`。这说明它**不是把 MongoDB 硬塞进关系模型**，而是为两类数据模型分别适配，再在上层统一语义。

### 还不能确认的：API 具体形态

0.4 处于 alpha，官方文档与示例尚未补齐。以官方 [axum 集成示例](https://github.com/teodevgroup/teo/tree/main/examples/axum-integration/postgres) 为例，`main.rs` 目前仍是空实现。这意味着：

- 模型声明、Pipeline（数据处理管道）、权限控制等机制，官方在旧版 README 和 roadmap 中描述过。但 0.4 的具体写法以官方文档为准，本文不给出无法验证的 API 片段。
- 迁移、客户端生成等命令同样未在 0.4 文档中定型，写死命令名反而会误导读者。

这条边界值得单独说。关于 WIP 项目的文章，与其展示"看起来能跑"的代码，不如明确告诉读者哪些已确定、哪些还在变动。

## 一个任务流过系统（概念级）

由于 API 未定型，这里只描述机制如何配合，不附代码：

1. **定义模型**。开发者在 Schema 或 Rust 代码中声明模型与字段约束。这同时决定数据结构、校验规则和可迁移性。
2. **迁移**。Schema 变更通过增量迁移落到数据库，代码里的结构变化与库表变化由同一条链路驱动。
3. **请求处理**。一次写入请求经过校验、数据处理管道、权限检查后到达连接器；连接器按目标数据库生成对应的 SQL 或 MongoDB 操作。
4. **客户端侧**。如果沿用旧版能力，前端可拿到由同一份 Schema 生成的类型化客户端。前后端字段名不再需要手工对齐。但这项能力在 0.4 是否保留、以什么命令触发，需要等官方文档确认。

这个流程想强调的是：TEO 把"数据结构、校验、迁移、访问、类型同步"收敛到同一个源头。各层不再各写一套。这是它区别于"SQL 工具"的地方，也是它作为 ORM 的价值主张。

## 现在该不该用

### 适合等它的人

- 正在做一个新的 Rust Web 项目（Axum / Actix）。数据库选型同时涉及 SQL 和 MongoDB。
- 被"手写迁移 SQL"和"前后端类型不同步"反复折磨，想减少样板代码。
- 愿意接受 alpha 版本的不稳定，能跟着官方 roadmap 走。

### 现在不建议用它的人

- 生产环境或对数据安全敏感的存量项目。alpha 阶段 API 与文档都在变，锁死一个不稳定版本的成本高于收益。
- 只用一个 SQL 数据库、团队已深度使用 Diesel 或 SQLx。此时切到 TEO 没有足够的额外收益，迁移成本反而更高。
- 依赖成熟文档、稳定 API 和完整示例的团队。TEO 0.4 目前这三样都还没齐。

### 采用顺序（如果决定试点）

1. 先跑通官方 quickstart，确认 0.4 的模型声明和迁移流程符合预期。
2. 在一个 Schema 稳定的新模块上试一个迭代周期，重点看增量迁移是否顺手。
3. 若前两步都顺畅，再评估是否把已有项目的数据层迁过来；不推荐一次性迁移所有表。

## 参考资源

- 仓库：[github.com/teodevgroup/teo](https://github.com/teodevgroup/teo)
- 官方文档：[docs.teodev.io](https://docs.teodev.io)
- 官网：[teodev.io](https://teodev.io)
- crates.io 版本记录：[crates.io/crates/teo](https://crates.io/crates/teo)
- 开发路线图：[ROADMAP.md](https://github.com/teodevgroup/teo/blob/main/ROADMAP.md)
