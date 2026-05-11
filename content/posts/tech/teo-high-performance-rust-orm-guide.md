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

> Rust 生态的 ORM 一直是个痛点：要么太薄（只是 SQL 生成器），要么太重（对标 ActiveRecord 但缺乏 Rust 味）。TEO 是一个试图在性能和 ergonomics 之间找到平衡点的尝试。

---

## 一句话定位

[TEO](https://github.com/teodevgroup/teo) 是一个用 Rust 编写的高性能 ORM，支持 **MySQL、PostgreSQL、SQLite、MongoDB** 四种主流数据库，核心设计哲学是：

> 保留 SQL 的表达能力，同时通过声明式 Schema、Pipeline 中间件和自动迁移，让 CRUD 代码从模板中解放出来。

当前版本 0.4（Alpha）完全用 Rust 重写，Edition 2024，Rust 版本要求 1.93+。

---

## 为什么需要另一个 Rust ORM

Rust 生态已有多个 ORM / SQL 工具：

| 工具 | 定位 | 多数据库 | 特点 |
|------|------|----------|------|
| Diesel | 成熟 ORM | MySQL/PG/SQLite | 同步 API，编译时查询验证 |
| SQLx | SQL 工具 | 全部 | 编译时验证，运行时执行 |
| SeaORM | 异步 ORM | MySQL/PG/SQLite | ActiveRecord 风格 |
| **TEO** | **高性能 ORM** | **全部 + MongoDB** | **Pipeline 中间件 + 自动迁移 + 多语言 SDK** |

TEO 的差异化在于：
1. **Pipeline**：类似 Express.js 中间件的数据处理管道，贯穿 save/find/create 等操作
2. **自动迁移**：Schema 即数据库版本控制，migration 融入开发流程
3. **多语言客户端**：不仅 Rust 服务端，还生成 TypeScript/Python/Go 客户端 SDK
4. **MongoDB 原生支持**：同时支持 SQL 和 NoSQL，而不是把 MongoDB 当"另一种 SQL"处理

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

这个 struct 同时定义了：
- Rust 类型（编译期）
- 数据库 Schema（迁移期）
- API 序列化和验证（运行时）

### Pipeline：数据处理的中间件链

Pipeline 是 TEO 最独特的设计。它让你在 `save`/`create`/`update` 等操作的**前后**插入自定义逻辑。

```rust
// 在 save 前验证密码强度，save 后记录日志
let user = user.save()
    .pipeline(|ctx| async move {
        // before save
        let password = ctx.value<string>("password")?;
        if password.len() < 8 {
            return Err(Error::invalid("password too short"));
        }
        // hash password
        let hashed = hash_password(password)?;
        ctx.set("password", hashed);
        Ok(())
    })
    .pipeline(|ctx| async move {
        // after save
        let id = ctx.result::<User>()?.id;
        log::info!("user {} saved", id);
        Ok(())
    })
    .await?;
```

Pipeline 可以作用于不同的粒度：字段级别、模型级别、或者整个 Handler 级别。

### 权限系统

TEO 内置了 `@canRead`、`@canCreate`、`@canUpdate`、`@canDelete` 装饰器：

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

基于 Pipeline 的权限系统在数据读写之前进行检查，不需要手动写 if-else。

---

## 四种数据库的适配层

### SQL 数据库（MySQL / PostgreSQL / SQLite）

SQL 数据库使用 [quaint](https://github.com/quaint-dev/quaint)（也是 Prisma 背后的 ORM 引擎）作为底层 SQL 抽象。TEO 在其上构建了：

- **统一的 Schema 解析**：四种 SQL 方言的 DDL 差异被抽象掉
- **迁移引擎**：`teo-cli migrate` 命令自动生成 SQL 迁移文件
- **查询构建器**：链式 API 生成类型安全 SQL

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

### MongoDB 适配

MongoDB 适配层是 TEO 的另一个亮点。大多数 Rust ORM 只支持 SQL，TEO 专门做了 MongoDB 的聚合管道（Aggregation Pipeline）重写，支持 `$match`、`$group`、`$project` 等操作。

```rust
// MongoDB 聚合查询
let result = teo::new()
    .aggregate("orders")
    .group("user_id")
    .sum("amount")
    .pipelinectx.add
    .await?;
```

---

## 自动迁移系统

TEO 的 Schema 声明即数据库版本控制。开发者修改 Rust struct 后，运行：

```bash
cargo teo migrate
```

TEO 会对比当前 Schema 和数据库实际 Schema，生成增量迁移 SQL：

```sql
-- migration: 2026-05-11_add_user_nickname.sql
ALTER TABLE users ADD COLUMN nickname VARCHAR(255);
```

这消除了手动维护 SQL 迁移文件或者用 `ALTER TABLE` 脚本的历史负担。

---

## 多语言客户端生成

TEO 不仅仅是一个 Rust 库——它的设计目标是**全栈数据库解决方案**。

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

这意味着：你在 Rust 后端定义的 Schema，自动同步到前端 TypeScript 类型定义，不需要手动维护两套类型。Team 可以并行开发后端和客户端，而类型安全在 API 边界得到保证。

---

## 性能特性

### 全异步 runtime

TEO 基于 `async/await` + `Tokio`，所有数据库操作都是非阻塞的：

```rust
// Tokio 异步 runtime
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
- `rusqlite` — 同步 SQLite（可与 `mysql_async` 混用）

### 连接池

每个数据库连接器内置 HikariCP-style 连接池。池大小可通过配置调整：

```toml
[teo]
connectors.postgres.connection_string = "postgres://user:pass@localhost/db"
connectors.postgres.pool.max = 10
connectors.postgres.pool.min = 2
```

### 预处理语句

所有重复查询使用数据库预处理语句，避免每次执行重新解析 SQL。

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

`teo::axum::layer()` 把 Teo 实例作为 Axum 中间件嵌入，自动处理数据库上下文注入。

---

## 版本演进：从 0.0 到 0.4

TEO 的 roadmap 展示了它的工程演进路径：

- **0.0.x**（2022-2023）：Python/Node.js/Go 多语言实现为主，Rust 只是其中之一
- **0.3.x**：多语言 SDK 成熟，pipeline、middleware、权限系统完善
- **0.4**（当前 Alpha）：**完全重写为 Rust ORM**，放弃 Python/Node.js 服务端实现，保留多语言客户端生成能力

0.4 的方向转变很关键：作者意识到"用多语言实现服务端"反而带来了维护负担，而 Rust 生态对高性能 ORM 的需求更迫切。重写后的 TEO 是一个更聚焦、更 Rust-native 的项目。

---

## 适用场景

**✅ 适合用 TEO 的场景：**
- 新 Rust Web 项目（Axum、Actix）需要类型安全的数据层
- 需要同时支持 SQL（MySQL/PG）和 NoSQL（MongoDB）
- Schema 变更频繁，需要自动化迁移
- 前后端分离，需要生成 TypeScript SDK 保证类型一致性
- 需要在数据库层面实现细粒度权限（而不仅仅依赖应用层）

**❌ 不适合的场景：**
- 极致性能场景（直接使用 SQLx 写手写 SQL）
- 已有数据库不想改造 Schema
- 需要复杂关联查询（JOIN、子查询）且对性能敏感的场景

---

## 总结

TEO 是 Rust 生态中一个野心勃勃的 ORM 尝试。它的核心价值主张很清晰：

1. **Schema 即代码**：Rust struct 和数据库 Schema 一体化
2. **Pipeline 中间件**：统一的数据处理管道，贯穿读写操作
3. **四库合一**：MySQL / PostgreSQL / SQLite / MongoDB 同一套 API
4. **多语言 SDK**：TypeScript / Python / Go / Swift 客户端自动生成
5. **自动迁移**：Schema 变更驱动数据库演进

如果你在构建 Rust Web 服务且需要一个既能处理 SQL 又能处理 MongoDB 的 ORM，TEO 值得关注。

---

**项目信息**

- GitHub：[teodevgroup/teo](https://github.com/teodevgroup/teo) ⭐ 1.4k
- 语言：Rust（MIT）
- 支持数据库：MySQL、PostgreSQL、SQLite、MongoDB
- 官方文档：[docs.teodev.io](https://docs.teodev.io)
- 官网：[teodev.io](https://teodev.io)
- 当前版本：0.4.0-alpha.1（Rust 1.93+，Edition 2024）
