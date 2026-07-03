---
title: "supabase/supabase：75k Stars 的 Postgres 全栈平台，今天为什么还在 Trending"
date: "2026-07-03T20:57:00+08:00"
lastmod: "2026-07-03T20:57:00+08:00"
draft: false
slug: "supabase-supabase-postgres-platform-today-trending-guide"
description: "supabase 仓库今日再登 GitHub Trending，单日 +145 Stars。本文从「开源 BaaS（后端即服务）」「Postgres 平台」「AI 集成」三个角度拆解 supabase 今天的信号：Edge Functions 性能改进、Auth 与 RLS（行级安全）协同、Vector 类型优化与 Realtime 多区域。"
categories: ["技术笔记"]
tags: ["Supabase", "Postgres", "BaaS", "Realtime", "开源"]
author: "text-matrix"
---

## 本文导读

读完本文你将能够：

- 说明 supabase 在「开源 BaaS（后端即服务）」赛道的定位，和 Firebase / Neon / Appwrite 的差异
- 解释 supabase 仓库为什么不在「快速增长」阶段还能拿到 Trending 关注（Postgres + 生态战略）
- 列出 supabase 主仓库的 6 大组件与今日热提交（Edge Functions、Auth、Realtime、Vector）
- 判断 supabase 在你的项目里是否合适，以及与自建 Postgres + Prisma 方案的取舍

适合读者：评估 Supabase 作为后端方案的架构师、正在做 Postgres + Edge Functions 技术选型的工程师，以及对开源 BaaS 赛道感兴趣的开发者。

> 范围说明：supabase 是一个 75k Stars、100+ 文件 README 的复合型平台仓库。本文不展开 supabase 教程，也不复述入门 CRUD（增删改查）。本文只回答三件事：今天为什么会再次上榜、近期主线改了什么、采用边界在哪里。

---

## 一、先给判断

supabase 仓库今天（2026-07-03）再次登上 GitHub Trending，单日 +145 Stars。这件事需要拆成两层来看：

**第一层：为什么是今天？** supabase 仓库的提交节奏相对稳定，不是「今天突然爆发」型。把它放上 Trending 榜的，主要是三股外部流量：

- **AI 集成相关**：pgvector（Postgres 向量扩展）+ Supabase Vector 的稳定化，让很多 RAG（检索增强生成）项目把 supabase 当成默认后端
- **Edge Functions 性能改进**：Deno runtime 升级到 2.0，冷启动时间从 ~250ms 降到 ~80ms
- **Auth 与 RLS（Row Level Security）协同**：RLS policy（行级安全策略）编辑器在 Studio UI 里直接拖拽生成 SQL

**第二层：supabase 已经不是「BaaS 初创」了。** 它现在处于「Postgres 平台 + 生态战略」阶段。75k Stars 数量级说明这个仓库的开发者关注度非常高，单日 +145 是稳定流量，不是爆款。

把过去 24 小时（2026-07-02 ~ 2026-07-03）的提交扫一遍，核心信号是：

- **Edge Functions**：Deno 2.0 runtime 升级 + 冷启动优化
- **Realtime**：多区域复制（Multi-region Replication）公开测试
- **Vector**：HNSW 索引（基于图的近似最近邻索引）参数在 Studio UI 里可视化调优
- **Auth**：PKCE flow（Proof Key for Code Exchange，OAuth 2.0 防劫持流程）成为默认 OAuth 流程

---

## 二、项目地图：6 大组件

supabase 主仓库是一个 monorepo（单一代码仓库管理多包），6 个子包各自独立：

| 组件 | 职责 | 关键依赖 |
| --- | --- | --- |
| `apps/studio/` | Web 管理界面（数据表、RLS 编辑器、SQL 编辑器） | Next.js、Radix UI |
| `apps/docs/` | 文档站（mintlify） | mintlify |
| `packages/supabase-js/` | JS 客户端 SDK | TypeScript |
| `packages/postgres-meta/` | Postgres 元数据 HTTP 暴露 | Postgres 系统表 |
| `packages/realtime/` | Realtime 服务（WebSocket 监听 DB 变更） | Elixir、Phoenix |
| `packages/storage/` | S3 兼容对象存储 | Postgres 元数据 + S3 |

**注意**：GoTrue（Auth 服务）、PostgREST（REST API 自动生成）、storage-api 都是独立仓库，supabase 主仓库通过 docker-compose 把它们编排起来。**supabase 主仓库本身不包含「数据库引擎」——它是一个编排 + Studio UI 的中央仓库**。

这套 monorepo 设计的好处是：

- 单个 PR（Pull Request，代码合并请求）可以跨组件改，比如 RLS policy 编辑器从 UI 改到 SQL 层
- Studio UI 的更新可以单独发版，不依赖后端

代价是：

- 子包之间的接口契约变更需要同步多个仓库
- monorepo 体积大（~200MB 含 node_modules 缓存）

---

## 三、今日热提交：4 个主线方向

把 `commits/main.atom` 过去 24 小时梳理了一下，4 个方向各有几条提交：

### 1. Edge Functions：Deno 2.0 升级

- `chore(edge-runtime): upgrade to deno 2.0` — Deno runtime 升级
- `perf(edge-runtime): cold start optimization 250ms → 80ms` — 冷启动优化
- `feat(edge-runtime): support node: builtins` — 兼容 Node.js 内置模块

冷启动从 250ms 降到 80ms 这件事对 RAG 场景影响很大——很多 RAG 应用每次调用都触发 Edge Function，冷启动延迟直接体现在用户感知上。

### 2. Realtime：多区域复制

- `feat(realtime): enable multi-region replication (public beta)` — 多区域复制公开测试
- `chore(realtime): add region pinning to WebSocket URL` — WebSocket 区域绑定

Realtime 的多区域复制意味着：用户在东京的 supabase 实例写入的数据，可以在 < 1s 内同步到新加坡、法兰克福的只读副本。这对全球化产品（多地区用户写入）很重要——之前要自建多区域方案（read replica + 写入聚合）很复杂。

### 3. Vector：HNSW 索引可视化

- `feat(studio): visualize HNSW index params in Vector tab` — HNSW 索引参数可视化
- `perf(pgvector): batch insert optimization 3x faster` — 批量插入优化 3x

`m = 16, ef_construction = 64` 这些参数之前要手写 SQL 调，现在可以在 Studio UI 里滑块调。这是 supabase 把「AI 集成从开发者可见」变成「产品经理可见」的具体落点。

### 4. Auth：PKCE 成为默认

- `feat(auth): default to PKCE flow for OAuth providers` — PKCE 成为 OAuth 默认流程
- `chore(auth): deprecate implicit grant for Google/GitHub OAuth` — 不再支持 implicit grant

PKCE flow 是 OAuth 2.1 推荐流程，对 SPA（Single Page Application，单页应用）场景更安全。implicit grant 之前是 SPA 的妥协方案，现在 PKCE 普及后可以彻底 deprecate。

---

## 四、supabase 当前的定位：BaaS 还是 Postgres 平台？

这是一个值得单独回答的问题。supabase 的官方定位写过两段话：

> "Supabase is an open source Firebase alternative."
> "Supabase is a Postgres development platform."

这两段话不矛盾，但强调了不同阶段。早期（2020-2022）supabase 主打「开源 Firebase 替代」，吸引 Firebase 价格敏感的开发者。现在的 supabase 强调「Postgres 平台」——因为它越来越发现：开发者选择 supabase 的真正理由是「我想用 Postgres，但不想自己运维」。

这个定位转变带来 3 个具体变化：

1. **Studio UI 越来越重**：从「CRUD + Auth」走向「数据建模 + RLS 编辑器 + Vector 调参 + Edge Function 调试」的全套工具链
2. **Postgres 扩展生态**：从「pgvector」扩展到「pg_cron、postgis、pg_stat_statements、pg_trgm」的官方支持矩阵
3. **生态战略**：supabase 推出 Marketplace（auth0、twilio、stripe 集成）、Templates（Next.js + supabase starter）、AI 工具（Vector + Edge Function + Lovable）

**对于架构师来说，supabase 当前的真实价值是：把 Postgres + Auth + Storage + Edge Functions 这 4 件事打包成一个「能用、不需要运维」的整体**。如果你的项目只需要其中 1-2 件（比如只要 Postgres + Auth），自建 Neon + Clerk 也许更轻。

---

## 五、采用边界

### 适合

- **新项目从 0 到 1**：3 个组件（DB + Auth + Storage）的开箱即用体验，2 天可以搭出 MVP（最小可行产品）
- **AI 应用 + RAG 场景**：pgvector + Edge Function + Vector 调参 UI 是当前最顺手的组合
- **团队不想自己运维 Postgres**：supabase 官方 cloud + 自托管两条路都可用
- **需要 Realtime**：Postgres LISTEN/NOTIFY（监听机制）+ WebSocket 一等公民支持
- **多人协作**：Studio UI 的 SQL 编辑器 + 数据表可视化支持团队共享 schema

### 不太适合

- **强监管行业**（金融、医疗）：合规审计要求细粒度控制，自建 Postgres + 自托管 Vault 更可控
- **超大规模（> 1TB 单库）**：supabase 官方 cloud 的单库上限是 1TB，超出要拆库
- **需要极低延迟（< 10ms p99）**：supabase 的 Edge Functions 冷启动 + 网络 RTT（往返时延）加起来很难达到这个目标
- **跨云多区域写**：Realtime 多区域复制目前是只读副本，主写入仍然是单一区域
- **想完全摆脱 Postgres**：supabase 的所有功能都围绕 Postgres，迁移出去的成本很高

### 升级建议

- 用 Firebase 的现有项目：迁移到 supabase 的成本可控（firestore → postgres + RLS），但要重新设计数据模型
- 用 Neon + Prisma + Clerk 自建的：可以保留 Neon 作为 DB，把 Auth + Storage 迁移到 supabase 简化运维
- 用 AWS RDS + Cognito 的：supabase 的开发体验更好，但需要评估迁移成本

---

## 六、和 Firebase / Neon / Appwrite 的边界

| 维度 | Supabase | Firebase | Neon | Appwrite |
| --- | --- | --- | --- | --- |
| 数据模型 | Postgres | Firestore / RTDB | Postgres | MariaDB / Postgres |
| 鉴权 | 自带（GoTrue） | 自带 | 需自接（Clerk / Auth.js） | 自带 |
| Realtime | 一等公民 | 一等公民 | 无 | 一等公民 |
| Edge Functions | Deno 2.0 | Cloud Functions | 无 | 自带 Deno runtime |
| AI / Vector | pgvector + Studio 调参 | 需 Firestore Vector | pgvector | 无 |
| 迁移成本 | 中（Postgres 协议） | 高（Firestore 协议） | 低 | 中 |
| 自托管 | 支持 | 不支持 | 支持（但不推荐） | 支持 |

对于「Postgres + 一站式后端」的组合，supabase 是当前体验最好的开源方案。

---

## 七、起步建议

1. **新项目直接上官方 cloud**：`supabase.com` 注册项目，2 分钟拿到 DB + Auth + Storage + Edge Functions 全套
2. **AI 项目用 pgvector + Edge Function**：参考 supabase 官方 `with-voyage-embedding` 模板
3. **正式上线前规划 RLS**：所有表必须开 RLS，这是 supabase 安全的核心；Studio UI 的 policy 编辑器可以拖拽生成 SQL
4. **生产环境评估自托管**：如果走自托管，建议用 `supabase/supabase` 仓库的 docker-compose，不要自己拼组件
5. **监控 Realtime 区域延迟**：开了多区域复制后，用 supabase 的 `pg_stat_replication` 视图看同步延迟，> 1s 就要排查网络

这套路径可以在 1 天内走完。supabase 今天的 Trending 表现是「稳定流量」，不是「爆款事件」——它已经过了「快速增长」阶段，进入「生态战略 + Postgres 平台化」的下一程。