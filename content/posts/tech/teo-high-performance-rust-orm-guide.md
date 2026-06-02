---
title: "TEO：Rust高性能ORM，支持MySQL/PostgreSQL/SQLite/MongoDB四库合一"
date: "2026-05-11T12:55:00+08:00"
slug: "teo-high-performance-rust-orm"
description: "深度解析teodevgroup/teo：Rust原生高性能ORM，0.4版本完全重写，支持MySQL/PostgreSQL/SQLite/MongoDB四大数据库，内置Pipeline中间件、权限系统和自动迁移。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "ORM", "数据库", "MySQL", "PostgreSQL", "MongoDB", "异步", "性能"]
hiddenFromHomePage: true
---

> Rust ORM 的困境不是缺选择，而是缺一个同时做好三件事的方案：多数据库适配、声明式 Schema、以及贯穿读写操作的数据处理管道。TEO 0.4 用完全重写的 Rust 内核把这三件事拼到了一起。它比 SQLx 更"ORM"，比 Diesel 更 async，而且是目前唯一在 SQL 和 MongoDB 上提供同一套 API 的 Rust ORM。

---

## 一句话定位

[TEO](https://github.com/teodevgroup/teo) 是一个用 Rust 编写的高性能 ORM，支持 **MySQL、PostgreSQL、SQLite、MongoDB** 四种主流数据库。核心思路是：

> 保留 SQL 的表达能力，同时通过声明式 Schema、Pipeline 中间件和自动迁移，把 CRUD 样板代码从项目里拿掉。

当前版本 0.4（Alpha）完全用 Rust 重写，Edition 2024，Rust 版本要求 1.93+。

---

## 系统总览：五条线怎么串在一起

理解 TEO 的关键是把它的五条机制分开看，而不是混成一团。下面这张表给出快速定位：

| 机制 | 解决的问题 | 作用时机 |
|------|-----------|----------|
| **声明式 Schema** | struct 即数据库 DDL，不用手写 SQL 建表 | 编译期 + 迁移期 |
| **Pipeline 中间件** | 在 save / create / update 前后插入自定义逻辑 | 运行时（每次数据库操作） |
| **权限装饰器** | 字段级读写控制，不靠 if-else 堆在业务代码里 | 运行时（每次查询/写入前） |
| **自动迁移** | Schema 变更自动生成增量 SQL | 开发期（`cargo teo migrate`） |
| **多语言 SDK 生成** | Rust 后端 Schema 同步到 TS / Python / Go 客户端 | 构建期 |

这五条线是正交的：你可以在不改 Pipeline 的情况下调整权限，也可以在不触达 Schema 的情况下增加新的 Pipeline 步骤。后面的章节会逐一展开，但先记住这张地图有助于避免读完每个 H2 后忘记它们之间的关系。

---

## 为什么需要另一个 Rust ORM

Rust 生态已有的 ORM / SQL 工具各走一路：

| 工具 | 定位 | 多数据库 | 特点 |
|------|------|----------|------|
| Diesel | 成熟 ORM | MySQL/PG/SQLite | 同步 API，编译时查询验证 |
| SQLx | SQL 工具 | 全部 | 编译时验证，运行时执行 |
| SeaORM | 异步 ORM | MySQL/PG/SQLite | ActiveRecord 风格 |
| **TEO** | **高性能 ORM** | **全部 + MongoDB** | **Pipeline 中间件 + 自动迁移 + 多语言 SDK** |

TEO 真正的差异点不在"又一个异步 ORM"，而在以下四件事：

1. **Pipeline**：类似 Express.js 中间件的数据处理管道，贯穿 save / find / create 等操作。你可以把密码哈希、日志记录、数据校验串成链，而不是在每个 handler 里重复写。
2. **自动迁移**：Schema 即数据库版本控制，`cargo teo migrate` 一条命令搞定增量 DDL。
3. **多语言客户端**：不只 Rust 服务端能用，还生成 TypeScript / Python / Go 客户端 SDK，前后端类型定义来自同一个 Schema。
4. **MongoDB 原生支持**：不是把 MongoDB 当"另一种 SQL"处理，而是单独做了聚合管道（Aggregation Pipeline）适配。

---

## 核心架构

### 工作空间结构

TEO 是一个 Cargo workspace，包含三个核心 crate：

```
teo/              — 主 ORM 核心
teo-derive/       — 过程宏（@id, @defaults, @relation 等）
teo-column-type/  — 列类型系统（i32, String, DateTime 等）
```

### Schema 声明式设计

TEO 的核心理念：**你的 Rust struct 就是数据库 Schema**。

```rust
use teo::prelude::*;
use serde::{Deserialize, Serialize};

#[derive(Model, Serialize, Deserialize)]
pub struct User {
    #[id]
    pub id: i64,

    #[unique]
    #[email]
    pub email: String,

    #[length(min = 8, max = 128)]
    pub password: String,

    pub nickname: Option<String>,

    #[defaults(current)]
    pub created_at: DateTime,

    #[defaults(current)]
    pub updated_at: DateTime,

    #[relation(to = "Post::author")]
    pub posts: HasMany<Post>,
}
```

这个 struct 同时承担三件事：
- Rust 类型（编译期）
- 数据库 Schema（迁移期）
- API 序列化和验证（运行时）

不需要额外维护一份 `.sql` 迁移文件或 JSON Schema。

### Pipeline：数据处理的中间件链

Pipeline 是 TEO 最独特的设计。它在 `save` / `create` / `update` 等操作的**前后**插入自定义逻辑，链式执行。

```rust
let user = user.save()
    .pipeline(|ctx| async move {
        // before save：校验并哈希密码
        let password = ctx.value::<String>("password")?;
        if password.len() < 8 {
            return Err(Error::invalid("password too short"));
        }
        let hashed = hash_password(password)?;
        ctx.set("password", hashed);
        Ok(())
    })
    .pipeline(|ctx| async move {
        // after save：记录日志
        let id = ctx.result::<User>()?.id;
        log::info!("user {} saved", id);
        Ok(())
    })
    .await?;
```

Pipeline 可以在三个粒度上注册：字段级别、模型级别、或者整个 Handler 级别。同一个操作可以串联多个 Pipeline 步骤，按注册顺序执行。

### 权限系统

TEO 内置了 `@canRead`、`@canCreate`、`@canUpdate`、`@canDelete` 装饰器，在数据读写之前做检查：

```rust
#[derive(Model)]
pub struct Article {
    #[id]
    pub id: i64,

    #[canRead(identity().is_authenticated())]
    #[canUpdate(identity().is_admin())]
    pub title: String,

    #[canRead(identity().is_authenticated())]
    #[canUpdate(identity().eq("author_id", identity().id()))]
    pub content: String,

    #[canRead(identity().is_admin())]
    pub is_draft: bool,
}
```

权限规则直接挂在字段上，不走业务代码里的 if-else。`identity()` 对象由 TEO 在请求上下文中注入，你只需要定义规则表达式。

---

## 一个完整流程：用户注册并发表文章

前面拆开的 Schema / Pipeline / 权限 / 多语言 SDK 四条线，在一次"新用户注册并发表第一篇文章"的流程里是怎么配合的：

1. **Schema 定义阶段**：开发者在 `User` 和 `Article` struct 上写好 `#[derive(Model)]` 和装饰器，运行 `cargo teo migrate` 生成建表 SQL。此时 Rust struct、数据库表和权限规则三者已经绑定。

2. **客户端类型同步**：运行 `cargo teo generate --lang typescript`，前端拿到 `User` 和 `Article` 的类型定义，IDE 自动补全 `user.email`、`article.title` 等字段。前后端共享同一份 Schema，不存在字段名对不上的情况。

3. **用户注册请求到达**：Axum handler 收到 `POST /register`，调用 `user.save()`。TEO 执行 Pipeline 链：第一步校验密码长度并哈希，第二步记录注册日志。如果密码太短，Pipeline 第一步直接返回 `Err`，后续步骤和数据库写入都不会执行。

4. **发表文章时的权限检查**：用户登录后请求 `POST /articles`。TEO 在写入 `Article` 之前扫描 `@canCreate` 规则——如果没有显式声明 `@canCreate`，默认放行。但如果用户尝试更新别人的文章，`@canUpdate(identity().eq("author_id", identity().id()))` 会拦截：只有作者本人能改自己的文章，管理员也改不了 `content`（因为 `content` 字段上没有 `@canUpdate(identity().is_admin())`）。

5. **MongoDB 场景的差异**：如果后端用的是 MongoDB 而不是 PostgreSQL，上面这四步的代码完全不变。TEO 在底层把 `find_unique` 翻译成 `findOne`，把 `save` 翻译成 `insertOne`，把 Pipeline 中的字段操作映射到 MongoDB 的文档更新。开发者不需要写两套数据访问代码。

这个流程里，Schema 负责"数据结构长什么样"，Pipeline 负责"写入前后做什么"，权限负责"谁能碰哪些字段"，多语言 SDK 负责"前端怎么知道数据结构"。四条线各管各的，但在一次真实请求里全部参与了。

---

## 四种数据库的适配层

### SQL 数据库（MySQL / PostgreSQL / SQLite）

SQL 数据库使用 [quaint](https://github.com/quaint-dev/quaint)（Prisma 背后的 ORM 引擎）作为底层 SQL 抽象。TEO 在其上构建了三层：

- **统一的 Schema 解析**：四种 SQL 方言的 DDL 差异被抽象掉，同一份 struct 定义映射到不同的 CREATE TABLE 语法。
- **迁移引擎**：`teo-cli migrate` 命令自动生成 SQL 迁移文件。
- **查询构建器**：链式 API 生成类型安全 SQL。

```rust
// 查找用户并预加载其文章（避免 N+1）
let user = teo::new()
    .find_unique("user")
    .where_("id", 1)
    .include("posts")
    .await?;

// 条件更新
user.update()
    .set("nickname", "newname")
    .where_("updated_at", .lt(last_week))
    .await?;
```

`include("posts")` 是 TEO 的 eager loading 语法——一次查询把关联数据也拉回来，不像 ActiveRecord 那样默认 lazy loading 导致 N+1。

### MongoDB 适配

大多数 Rust ORM 只支持 SQL，TEO 专门做了 MongoDB 的聚合管道（Aggregation Pipeline）适配，支持 `$match`、`$group`、`$project` 等操作：

```rust
let result = teo::new()
    .aggregate("orders")
    .group("user_id")
    .sum("amount")
    .await?;
```

MongoDB 适配层的关键设计决策：TEO 没有把 MongoDB 的文档模型硬塞进关系模型的框里。对于 `find`、`insert`、`aggregate` 这些 MongoDB 原生操作，TEO 提供了一一对应的 API，而不是模拟 SQL 语义。

---

## 自动迁移系统

修改 Rust struct 后，运行一条命令：

```bash
cargo teo migrate
```

TEO 对比当前 Schema 和数据库实际结构，生成增量迁移 SQL：

```sql
-- migration: 2026-05-11_add_user_nickname.sql
ALTER TABLE users ADD COLUMN nickname VARCHAR(255);
```

迁移文件会落到项目目录下，可以纳入版本控制。相比手写 `ALTER TABLE` 脚本或者用第三方迁移工具，Schema 驱动迁移的好处是：改 struct 和改数据库是同一件事，不会有"代码里加了字段但数据库忘了加"的偏差。

---

## 多语言客户端生成

TEO 的设计目标是**全栈数据库解决方案**，不只服务 Rust 后端：

```bash
# 生成 TypeScript 客户端
cargo teo generate --lang typescript --out ./clients/ts

# 生成 Python 客户端
cargo teo generate --lang python --out ./clients/py

# 生成 Go 客户端
cargo teo generate --lang go --out ./clients/go

# 生成 Swift 客户端
cargo teo generate --lang swift --out ./clients/swift
```

实际效果：Rust 后端定义的 `User` struct，自动生成前端 `interface User { id: number; email: string; ... }`。前后端类型定义来自同一个源头，不需要手动维护两套，也不存在字段名不一致导致的运行时错误。前后端团队可以并行开发，类型安全在 API 边界得到保证。

注意：生成的客户端 SDK 是**类型定义 + HTTP 调用封装**，不是把 Rust 编译到目标语言。客户端仍然用目标语言的 HTTP 库发请求，只是请求/响应的类型结构由 TEO 保证一致。

---

## 性能特性

TEO 没有公布独立的 benchmark 数据，但从架构层面可以分析它的性能边界：

### 全异步 runtime

TEO 基于 `async/await` + `Tokio`，所有数据库操作都是非阻塞的：

```rust
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let teo = Teo::new().await?;
    let users = teo.find_many("user").await?;
    Ok(())
}
```

支持多个 async runtime 适配器：
- `mysql_async` — 异步 MySQL
- `tokio-postgres` — 异步 PostgreSQL
- `rusqlite` — 同步 SQLite（可与异步连接器混用）

**这组特性主要影响什么**：吞吐量。异步 runtime 让单个线程可以同时处理多个数据库连接，在高并发场景下比 Diesel 的同步模型更有优势。

**不能推出什么**：异步不等于"更快"。单次查询的延迟主要由数据库和网络决定，TEO 的 async 层不改变这个。如果查询本身很慢（缺索引、大表扫描），换成 TEO 不会变快。

### 连接池

每个数据库连接器内置连接池。池大小可通过配置调整：

```toml
[teo]
connectors.postgres.connection_string = "postgres://user:pass@localhost/db"
connectors.postgres.pool.max = 10
connectors.postgres.pool.min = 2
```

连接池影响的是**连接建立开销**——避免每次请求都重新建连。在高并发 Web 服务中，这个配置直接决定数据库连接是否会成为瓶颈。

### 预处理语句

所有重复查询使用数据库预处理语句，避免每次执行重新解析 SQL。

**这组特性主要影响什么**：重复查询的 CPU 开销。对于 Web 服务中最常见的"按 ID 查用户""按条件分页"这类查询，预处理语句减少了 SQL 解析时间。

**不能推出什么**：预处理语句不影响查询计划的优化。如果 SQL 本身需要全表扫描，预处理不会让它变快。

### 性能层面的实际取舍

TEO 在性能上的代价主要来自两层抽象：
1. **quaint 引擎层**：统一 SQL 方言的代价是不能用各数据库的专有优化（如 PostgreSQL 的 `COPY`、MySQL 的 `INSERT ... ON DUPLICATE KEY` 原生语法）。
2. **Pipeline 运行时**：每个 `save` / `update` 操作都会执行 Pipeline 链，比直接调用 `INSERT` 多一层函数调用开销。

如果业务里有每秒数万次简单写入的场景，TEO 的 Pipeline 层和 quaint 抽象层会构成可测量的开销。这类场景更适合直接用 SQLx 手写 SQL。但对于绝大多数 Web 应用的 CRUD 负载（每秒几百到几千次操作），这两层抽象的开销远小于网络延迟和数据库执行时间。

---

## 与 Actix-web / Axum 的集成

TEO 官方提供了 Axum 集成示例：

```rust
// examples/axum-integration/postgres/main.rs
use teo::prelude::*;
use axum::{Router, routing::get};

#[derive(Model)]
pub struct User {
    #[id]
    pub id: i64,
    pub name: String,
}

#[handler]
async fn get_user(ctx: &Ctx) -> Result<Json<User>, Error> {
    let user = ctx.find_unique("user").await?;
    Ok(Json(user))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let teo = Teo::new().await?;
    let app = Router::new()
        .route("/users/:id", get(get_user))
        .layer(teo::axum::layer(teo));
    Ok(())
}
```

`teo::axum::layer()` 把 Teo 实例作为 Axum 中间件嵌入，自动处理数据库上下文注入。Actix-web 的集成方式类似。

---

## 版本演进：从 0.0 到 0.4

TEO 的版本历史说明了一件事：多语言服务端的维护成本超过了它的收益。

- **0.0.x**（2022-2023）：Python / Node.js / Go 多语言实现为主，Rust 只是其中之一。
- **0.3.x**：多语言 SDK 成熟，pipeline、middleware、权限系统完善。
- **0.4**（当前 Alpha）：**完全重写为 Rust ORM**。放弃 Python / Node.js 服务端实现，只保留多语言客户端生成能力。

0.4 的方向转变说明作者承认了一个现实：用多语言实现服务端核心，维护的不是一个项目而是四个。把服务端收敛到 Rust，把多语言能力保留在客户端 SDK 生成这一层，是一个更可持续的架构决策。重写后的 TEO 更聚焦，也更 Rust-native。

---

## 适用场景与采用建议

### 适合用 TEO

- 新起的 Rust Web 项目（Axum、Actix），需要类型安全的数据层。
- 需要同时支持 SQL（MySQL / PG）和 NoSQL（MongoDB），不想维护两套数据访问代码。
- Schema 变更频繁，每次都要手写迁移 SQL 成本太高。
- 前后端分离，需要生成 TypeScript SDK 保证类型一致性。
- 需要在数据库层面实现字段级权限，而不是把所有权限逻辑堆在应用层。

### 不适合用 TEO

- 每秒数万次简单写入——Pipeline 层和 quaint 抽象层的开销会显现。
- 已有数据库不想改造 Schema——TEO 的声明式 Schema 要求 struct 驱动 DDL。
- 需要复杂关联查询（JOIN、子查询）且对性能敏感的报表场景——TEO 的查询构建器覆盖这类场景的能力有限。
- 团队已经深度使用 Diesel 或 SQLx 且有大量已有代码——迁移成本高于收益。

### 采用顺序

1. 先用 `cargo teo migrate` 在一个新表上跑通 Schema → 迁移 → CRUD 的完整闭环，确认 TEO 的声明式风格是否适合团队。
2. 再引入 Pipeline，把现有的密码哈希、日志记录、数据校验逻辑迁移到 Pipeline 链上，看看"中间件式数据管道"在项目里是否比分散的 handler 逻辑更好维护。
3. 确认上述两步都舒服之后，再启用量产环境的 `cargo teo generate`，把客户端 SDK 接到前端项目里。

不建议一上来就把所有表全部迁到 TEO 上。选一个 Schema 稳定的新模块先试，跑通一个迭代周期再评估是否推广。

---

## 结尾

TEO 做的不是"最快的 Rust ORM"这件事。它做的是把 Schema 定义、迁移、权限、Pipeline 和跨语言类型同步这五件事焊在一起，让 Rust 后端的数据层不再由零散工具拼装。

如果你是刚起步的 Rust Web 项目，或者正在被手写迁移 SQL 和前后端类型不一致折磨，TEO 值得放进评估列表。如果你的项目已经在 Diesel 或 SQLx 上跑得很稳，TEO 的收益主要在 Pipeline 和 MongoDB 支持上——先看这两项是否是你当前项目的真实痛点，再决定是否切过来。

---

**项目信息**

- GitHub：[teodevgroup/teo](https://github.com/teodevgroup/teo) ⭐ 1.4k
- 语言：Rust（MIT）
- 支持数据库：MySQL、PostgreSQL、SQLite、MongoDB
- 官方文档：[docs.teodev.io](https://docs.teodev.io)
- 官网：[teodev.io](https://teodev.io)
- 当前版本：0.4.0-alpha.1（Rust 1.93+，Edition 2024）