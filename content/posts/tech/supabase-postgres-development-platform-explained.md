---
title: "Supabase：开源版 Firebase 的七年答卷，把 Postgres 变成全栈开发平台"
date: 2026-09-20T04:25:00+08:00
lastmod: 2026-09-28T00:00:00+08:00
slug: "supabase-postgres-development-platform-explained"
github_repo: "supabase/supabase"
source_key: "gh:supabase/supabase"
description: "Supabase 是 11 万 Star 的开源 Postgres 开发平台，围绕数据库组装认证、自动 API、实时订阅、边缘函数与向量工具链。本文拆解其组合开源工具的架构策略、模块化客户端设计与自托管路径。"
draft: false
categories: ["技术笔记"]
tags: ["Supabase", "PostgreSQL", "后端", "开源", "BaaS"]
---

## 核心判断

Supabase 常被一句话介绍为"开源版 Firebase"，这个说法只说对了一半。Firebase 的核心是 Google 云上的封闭服务集合；Supabase 的核心是一个**专属于你的 Postgres 数据库**，认证、API、实时订阅、文件存储、边缘函数、向量检索全部围绕这个数据库组装。项目 2019 年创建，Apache 2.0 协议，主仓库以 TypeScript 为主——它给出的答卷是：用企业级开源工具拼出 Firebase 级的开发体验，且每一个组件都可以自托管。

## 项目概览

| 项 | 数据（2026-09-28 取自 GitHub API） |
|---|---|
| 仓库 | [supabase/supabase](https://github.com/supabase/supabase) |
| 定位 | The Postgres development platform |
| Stars / Forks | 110,809 / 15,137 |
| 主语言 | TypeScript |
| License | Apache-2.0 |
| 创建 | 2019-10-12，master 分支持续活跃 |

## 先给判断

Supabase 最值得学的不是功能清单，而是一条工程原则：**能用现成开源工具就绝不重造，造出来的也全部开源**。README 原文写得很直白——如果社区已有 MIT/Apache 级协议的成熟工具，就直接用；如果没有，他们自己造然后开源。这条原则决定了它的架构形态：Supabase 不是单体应用，而是七八个独立开源项目的编排层。带来的直接好处是**无锁定**：哪天不想用 Supabase 平台了，底下的 Postgres、PostgREST 都是标准组件，数据和行为都跟得走。

## 系统地图：一个数据库，七件工具

| 组件 | 职责 | 本体 |
|------|------|------|
| Postgres | 数据库本体，30 余年的对象关系数据库 | PostgreSQL（PostgreSQL License） |
| PostgREST | 把数据库直接变成 RESTful API | [PostgREST/postgrest](https://github.com/PostgREST/postgrest)，Haskell，MIT，27,685 stars |
| GoTrue | 基于 JWT 的认证：注册、登录、会话管理 | Supabase 自研，Go，JWT-based |
| Realtime | 用 WebSocket 广播增删改、在线状态与消息 | [supabase/realtime](https://github.com/supabase/realtime)，Elixir + Phoenix，Apache 2.0，7,644 stars |
| pg_graphql | GraphQL API | Postgres 扩展，Rust |
| Storage | S3 兼容的对象存储，元数据存 Postgres | Supabase 自研，TypeScript，Apache 2.0 |
| postgres-meta | 管理 Postgres 本身（建表、角色、查询） | Supabase 自研，TypeScript，Apache 2.0 |

边缘函数走 Deno 运行时（现代 JS/TS 运行时），连接池由 Supavisor（Elixir 写的多租户连接池）负责；外层由 Envoy 统一网关。每个组件是独立进程、独立仓库，Supabase 平台做的是把它们编排成一致的开发者体验：Dashboard 控制台、自动生成的 API、统一的客户端库。

这张表里藏着一个关键设计：**权限模型单一化**。Storage 的文件权限、Realtime 的订阅授权、PostgREST 的行级安全（Row Level Security）全部回落到 Postgres 本身的权限体系。学会一套 Postgres 权限，就学会了整个平台的访问控制。

## 一个任务如何流过系统

以"前端订阅某张表的新增记录并实时展示"为例：

1. 前端用 `supabase-js` 的 `auth` 模块通过 GoTrue 登录，拿到 JWT
2. 建立 WebSocket 连接到 Realtime 服务，订阅目标表
3. 有新行写入 Postgres 时，Realtime 通过 Postgres 的逻辑复制拿到变更：一个 replication slot 挂在写前日志（WAL）上，变更经解码成 JSON
4. Realtime 按订阅者的 RLS 策略逐条过滤（RLS 版走 WALRUS 函数算出授权订阅者列表），再把变更经 WebSocket 广播给客户端

代码落到客户端是这么写的（来自官方文档的 quick start）：

```js
import { createClient } from '@supabase/supabase-js'

const client = createClient('https://<project>.supabase.co', '<anon-key>')

client
  .channel('schema-db-changes')
  .on('postgres_changes', { event: '*', schema: 'public' }, (payload) => {
    // 新行已经通过 WAL -> 逻辑复制 -> WebSocket 到达这里
  })
  .subscribe()
```

注意第 4 步：授权不是应用层自己写的 if-else，而是复用 Postgres 权限。这是"单一权限模型"落到实处的样子。官方也明确过边界：Realtime 不保证每条变更都送达，断线期间的事件不会补发——它是为"实时 UI 更新"设计的，不是可靠的变更数据管道；要把变更可靠地送进分析库，官方另有 Supabase Pipelines，一条托管的 CDC 管道，按 publication 同步并对瞬时失败自动重试。

## 客户端的模块化设计

Supabase 官方客户端覆盖 JavaScript/TypeScript、Dart/Flutter、Swift、Python 四语言；社区维护 C#、Go、Kotlin、Ruby、Godot（GDScript）、Elixir、R 等（社区与官方差距可以直接量化：官方 SDK 能力矩阵 2026-09-27 更新，JavaScript 覆盖 96%、Flutter 100%、Python 73%、Swift 74%、Kotlin 83%、C# 46%、Go 0%——后几个社区库的功能完整度需要先查再信）。

值得看的设计是**每个子客户端都是独立实现**：supabase-js 内部由 postgrest-js、auth-js、realtime-js、storage-js、functions-js 五个独立包组成（现已归入 supabase-js 的 `packages/core/` 目录），主包只是聚合。这意味着你可以在任何项目里单独用 postgrest-js 操作 PostgREST，不必引入整套 Supabase 运行时——"支持现有工具"这条原则在客户端层同样成立。

## 部署路径：三种选择

- **托管平台**：supabase.com 注册即用，零安装
- **自托管**：官方提供 self-host 文档，所有组件开源意味着整套栈可以搬进自己的机房。2026 年 8 月起，自托管默认 API 网关从 Kong 换成了 Envoy（服务名 `api-gw`），原因官方说得很直白：Kong 的开源线停更近一年，继续沿用有安全与合规风险；Envoy 的配置以代码形式管理，且对新一代 API 密钥（`sb_publishable_*` / `sb_secret_*`）有第一等支持
- **本地开发**：`supabase cli` 支持本地起完整环境开发，与云端结构一致

对数据合规敏感的团队，"云端开发体验 + 数据不出内网"两者兼得，是 Supabase 相对 Firebase 的结构性优势。

## 维护状态

Supabase 全职维护，生态各组件独立版本线：master 分支每日有提交（2026-09-27 仍在推送），自托管镜像随各仓库发版，例如 auth 镜像当前为 `supabase/gotrue:v2.196.0`。官方维护强度还体现在工具的成套性：`supabase cli` 同时管本地开发与云端部署，SDK 能力矩阵有专人维护并公开在 supabase.github.io/sdk——生态的健康度是看得见的。

## 适用边界

**适合谁**：前端/移动团队想快速搭建带认证和实时能力的全栈应用，又不想被云厂商锁定；已经熟悉 Postgres 的团队上手成本尤其低——你积累的 Postgres 技能（RLS、触发器、函数）全部直接可用，包括 `pgvector` 做的 AI 向量工具链。

**不适合谁**：需要 Firebase 那种全球化边缘节点实时同步（Firestore 的多区域冲突消解）的场景——Supabase 的实时能力建立在单库复制上，跨区域扩展是另一套问题；重度依赖非关系模型（宽列、文档型灵活 schema）的场景，Postgres 的 JSONB 能做但不是它的主场。

**采用顺序建议**：从托管平台免费档起步，用 Dashboard 建表试 API 和 Auth，跑通后再决定是否 self-host——先体验它对开发效率的提升，再权衡运维成本。

## 一句话总结

Supabase 证明了 BaaS（Backend as a Service）可以建立在完全开源的栈上而不牺牲开发体验。它对开发者的最大承诺不是功能多，而是**你的数据住在你信得过的数据库里**——对一个 2019 年才起步的项目，11 万 Star 是市场对这条路线的投票。

## 参考来源与口径说明

- 仓库元数据（stars 110,809、forks 15,137、创建于 2019-10-12、Apache-2.0、主语言 TypeScript）：GitHub API，2026-09-28 读数。
- 组件元数据（PostgREST、Realtime、pg_graphql、Storage、postgres-meta、supabase-js 及五个子包）：各仓库 GitHub API，2026-09-28 读数。
- 架构与组件职责：Supabase 官方文档 Architecture 页当前版本。
- 客户端语言列表：官方文档 Client Libraries 页（官方四语言 + 社区库列表）与 SDK 能力矩阵（supabase.github.io/sdk，2026-09-27 更新）。
- Realtime 实现机制（逻辑复制、replication slot、WAL、wal2json、WALRUS、RLS 过滤；WALRUS 即 supabase/walrus，"Write Ahead Log Realtime Unified Security"）与"不保证送达"的边界：官方 Realtime 文档、supabase/realtime 与 supabase/walrus 仓库 README、官方博客《Realtime or Pipelines? How to choose the right tool》（2026-05-05）。
- Envoy 网关变更（changelog《Self-hosted Supabase: Envoy becomes the default API gateway (breaking change)》，2026-07-17 发布，8 月 9 日当周生效）：Supabase Changelog 与 Self-Hosting Envoy 文档。
- auth 镜像版本 `v2.196.0`：supabase/supabase 仓库 `docker/docker-compose.yml` master 分支。
- 本文为项目解读与使用判断，非官方文档；英文引文均为原文及其中文翻译。
