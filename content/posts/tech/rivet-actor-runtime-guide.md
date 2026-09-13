---
title: "Rivet Actor：有状态工作负载的原始抽象——从 Actors 到 agentOS 完全指南"
date: "2026-03-31T15:20:00+08:00"
lastmod: "2026-09-13T10:00:00+08:00"
slug: "rivet-actor-runtime-guide"
github_repo: "rivet-dev/actors"
source_key: "gh:rivet-dev/actors"
description: "Rivet 6.1k Stars · 为 AI Agent 和协作应用而生的 Actor 持久化运行时。三种状态层（Durable/Ephemeral/SQLite）、Durable Workflows、Queues、Cron，加 agentOS 为每个 agent 提供独立计算机。TypeScript/Rust/Python/Effect/Swift SDK。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Actor Model", "Rust", "TypeScript"]
---

# Rivet Actor：有状态工作负载的原始抽象——从 Actors 到 agentOS 完全指南

## §1 这篇文章覆盖什么

Rivet 想解决的问题是：有状态服务很难运维。传统做法把状态塞进数据库、把计算放进无状态服务，两者之间每一次交互都有网络和序列化开销。Rivet 把 Actor 模型做成了托管基础设施——状态和计算住在同一个进程里，持久化、休眠唤醒、崩溃恢复全部内置，你只写业务逻辑。

本文在 2026 年 9 月的 Rivet 生态基础上展开：

- **Actor 模型的生产形态**：三种状态层（Durable / Ephemeral / SQLite）与传统基础设施的根本区别
- **技术架构**：Rust Engine + 多语言 SDK 的仓库布局与内部模块
- **核心原语**：Actions、run 循环 + Queues、Durable Workflows（`ctx.step()` checkpoint）、Schedule & Cron
- **agentOS 层**：跑在你进程里的 agent 轻量 VM
- **实战代码**：从 counter 到 AI Agent 的完整 Actor 定义（全部对齐官方文档与示例）
- **部署与选型**：Just a Library / Self-Host / Rivet Cloud 的取舍，何时该用、何时别用

---

## §2 项目概述

### 2.1 什么是 Rivet？

**Rivet**（官方仓库：[rivet-dev/actors](https://github.com/rivet-dev/actors)）是一个**为 AI Agent 和协作应用设计的 Actor 持久化运行时**：

> Rivet Actors are the primitive for stateful workloads. One Actor per agent, per session, per user — state, storage, and networking included.

**翻译**：Rivet Actor 是有状态工作负载的原始抽象。每个 agent、每个会话、每个用户对应一个 Actor——状态、存储、网络全包。

Rivet 生态现在是四条产品线（首页导航的原话分别是 Orchestrate / Operate / Automate / Deploy）：

| 产品线 | 定位 | 状态 |
|--------|------|------|
| **Actors** | 核心持久化运行时 | 生产可用 |
| **Workflows** | Durable、可重放的多步骤操作（2026-02-24 发布） | 生产可用 |
| **agentOS** | 给每个 agent 一台"独立计算机"的库（2026-04-04 发布） | 生产可用 |
| **Dynamic Apps** | AI 生成的每用户后端（2026-08-31 发布） | 生产可用 |

**官方文档**：<https://rivet.dev/docs>。老域名 rivet.gg 的所有链接现在都 301 到 rivet.dev——如果你在旧资料里看到 rivet.gg，直接换域名即可。

### 2.2 核心数据（2026-09-13 核实）

```text
仓库:     rivet-dev/actors（monorepo，含 engine 与各 SDK）
Stars:    6,124
Forks:    246
最新版本: v2.3.17（2026-09-10，npm rivetkit 同步发布）
提交数:   6,100+
许可证:   Apache-2.0
文档:     rivet.dev/docs
```

历史上项目经历过两次搬家：早期是 `rivet-dev/rivet` monorepo，一度拆出到 `rivet-gg/engine`，2026 年又合并回 `rivet-dev` 组织并更名为 `actors`。搜索引擎和旧文章里的 `rivet-gg/*` 链接基本都已失效或重定向，认准 `rivet-dev` 即可。

### 2.3 关键性能指标

官方 README 给出了一张对比表，先看数字，再讲这些数字怎么读：

| 指标 | Rivet Actor | 传统对比 |
|------|-------------|----------|
| **冷启动** | ~20ms（含状态恢复） | K8s Pod ~6s，VM ~30s |
| **每实例内存** | ~0.6KB | K8s Pod ~50MB，VM ~512MB |
| **空闲成本** | $0（休眠即零资源） | K8s 集群 ~$85/月，VM ~$5/月 |
| **状态读取延迟** | 0ms（内存直读） | Redis ~1ms，Postgres ~5ms |
| **水平扩展** | 无限 | K8s ~5k 节点，VM 手动 |
| **多区域** | 全球边缘（EPaxos） | 单区域 |

这些数字的测量口径（官方 README 附带的方法论）：

- **20ms 冷启动**：包含 durable state 初始化，不只是进程拉起；实测环境是 Node.js + FoundationDB，且无 actor key 时没有跨区域锁开销。
- **0.6KB 内存**：在 Linux x86 上同时拉起 10,000 个 Actor，用 RSS 增量除以 Actor 数得出。
- **K8s ~6s**：Node.js 24 Alpine 镜像（压缩后 56MB）跑在 AWS EKS 预置好的 m5.large 节点上，约 1s 拉镜像、3-4s 调度和容器运行时初始化、1s 容器启动。
- **VM ~30s**：AWS EC2 最小实例 t3.nano（512MB 内存）从启动到 SSH 可用。

怎么读这张表：它比较的是"多运行一个 Actor 实例"的边际成本，而不是"上线一套系统"的总成本。Rivet 的优势场景是大量小粒度 Actor（每个会话、每个文档一个），如果你的负载是少数几个长驻服务，K8s 的数字劣势并不致命。反过来，"空闲 Actor 不占资源"这条对突发型负载（大多数 Agent 会话正是如此）价值最大。

### 2.4 技术栈

| 组件 | 语言 | 说明 |
|------|------|------|
| **Rivet Engine** | Rust | 核心 Actor 编排引擎（engine/ 目录） |
| **RivetKit TypeScript** | TypeScript | 主 SDK，npm `rivetkit` |
| **RivetKit Rust** | Rust | SDK（Beta，2026-06-17 发布） |
| **RivetKit Effect** | Effect | 函数式 SDK（Beta，`@rivetkit/effect`，2026-06-16 发布） |
| **RivetKit Swift** | Swift | iOS/macOS Client SDK（2026-01-25 发布） |
| **RivetKit Python** | Python | SDK（在 monorepo rivetkit-python/ 目录） |
| **@rivetkit/react** | TypeScript | React hooks（`createRivetKit` / `useActor`） |
| **网站 & 文档** | Astro + MDX | rivet.dev（源码在 rivet-dev/website） |

---

## §3 Actor 模型深度解析

### 3.1 什么是 Actor？

Actor 是一种并发计算模型，每个 Actor 是：

- **独立的计算单元**：拥有自己的状态和执行上下文
- **长期运行**：不像 serverless function 那样短暂，而是持续运行、空闲休眠
- **消息驱动**：通过队列接收消息，处理后响应

Rivet 把这个模型落地成生产基础设施时，做了三件关键的事：把 Actor 状态从"进程内变量"升级为**自动持久化的三层状态**、把 Actor 的生命周期从"手动管理"变成**自动休眠唤醒**、把跨 Actor 通信从"自己写 RPC"变成**内置 Queues / Workflows**。

### 3.2 三种状态层（最容易被忽视的核心）

Rivet Actor 的状态不是一个单一的"内存对象"。官方定义了三种状态层，各自独立、职责分明：

| 层级 | 属性 | 访问方式 | 持久化 | 典型用途 |
|------|------|----------|--------|----------|
| **Durable State** | `c.state` | actions 内直接读写 | ✅ 自动持久化，跨重启恢复 | 计数器、配置、消息列表等 |
| **Ephemeral Vars** | `c.vars` | actions / run 内读写 | ❌ 不持久化，每次启动重建 | DB 连接池、API 客户端、EventEmitter |
| **SQLite** | `c.db` | 通过 SQL 查询 | ✅ 自动持久化 | 需要 SQL 查询、schema 迁移、大于内存的数据集 |

这三层的区分是理解 Rivet API 的关键。在旧版示例（包括本文旧稿）里，只用 `state: { messages: [] }` 一种写法，容易让人误以为所有状态都放一个对象里。

**Durable State 示例**：最常见的用法，简单可序列化数据

```typescript
import { actor } from "rivetkit";

const counter = actor({
  // 常量初始状态
  state: { count: 0 },

  actions: {
    get: (c) => c.state.count,

    increment: (c) => {
      c.state.count += 1; // 改 c.state 就自动持久化
      return c.state.count;
    },
  },
});
```

持久化不是每改一次写一次盘：变更会被攒起来，按 `stateSaveInterval`（默认 1 秒）节流批量写入，Actor 休眠或关闭时再强制刷一次。读永远不会触发写盘。如果初始状态依赖创建参数，用 `createState` 动态计算（它只在 Actor 首次创建时运行一次，之后每次唤醒都从存储加载）：

```typescript
interface CounterState { count: number; }

const counter = actor({
  createState: (c, input: { startingCount: number }): CounterState => ({
    count: input.startingCount,
  }),
  actions: { /* ... */ },
});
```

**Ephemeral Vars 示例**：不可序列化的对象，每次 Actor 启动时重建

```typescript
const chatRoom = actor({
  state: { messages: [] as string[] }, // 持久化

  // createVars 每次启动都会运行，适合重建连接、加载外部数据
  createVars: () => ({ emitter: createEventEmitter() }),

  actions: {
    broadcast: (c, text: string) => {
      c.state.messages.push(text);               // 写 Durable State
      c.vars.emitter.emit("message", text);      // 用 Ephemeral Vars
    },
  },
});
```

**SQLite 示例**：需要 SQL 查询的数据。`db({ onMigrate })` 负责建表，RivetKit 把 `onMigrate` 包在 SQLite savepoint 里执行，迁移是原子的——抛错则全部回滚：

```typescript
import { actor } from "rivetkit";
import { db } from "rivetkit/db";

const todoList = actor({
  db: db({
    onMigrate: async (db) => {
      await db.execute(`
        CREATE TABLE IF NOT EXISTS todos (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          title TEXT NOT NULL
        );
      `);
    },
  }),

  actions: {
    add: async (c, title: string) => {
      await c.db.execute("INSERT INTO todos (title) VALUES (?)", title);
    },

    list: async (c) => {
      // SELECT 返回行对象数组
      return await c.db.execute("SELECT id, title FROM todos ORDER BY id DESC");
    },
  },
});
```

**三者混用**：一个真实场景的常见组合——连接池在模块级建一次（所有 Actor 共享），每个 Actor 启动时从 Postgres 加载属于自己的行：

```typescript
import { Pool } from "pg";

const pool = new Pool({ connectionString: process.env.DATABASE_URL });

const userActor = actor({
  state: { profile: null as Record<string, unknown> | null }, // Durable
  db: db({ /* schema migration */ }),                          // SQLite

  createVars: async (c) => {
    const { rows } = await pool.query(
      "SELECT * FROM users WHERE id = $1", [c.key[0]]
    );
    return { postgresRow: rows[0] }; // Ephemeral
  },

  actions: { /* ... */ },
});
```

### 3.3 Rivet Actor 的完整特性清单

| 特性 | 说明 |
|------|------|
| **内存状态** | 状态与计算共置，0ms 读写延迟 |
| **自动持久化** | Durable State（1 秒节流批量写）/ SQLite 自动持久化，无需手写 save() |
| **长期运行 + 休眠** | 活跃时常驻内存，空闲自动休眠到 $0 成本 |
| **水平无限扩展** | 零启动成本意味着可以开成千上万个 Actor |
| **实时事件** | `c.broadcast()` 向所有连接客户端推送，WebSocket 内置 |
| **Durable Workflows** | `ctx.step()` 自动 checkpoint，崩溃后从断点恢复（`@rivet-dev/workflows`） |
| **Queues** | 持久化消息队列，`run` 循环内 `c.queue.iter()` 消费 |
| **Schedule & Cron** | `c.schedule.after/at` + `c.cron.set/every`，跨重启存活的定时调度 |
| **三种 SDK 风格** | 对象式（TypeScript/Python）、函数式（Effect，Beta）、原生（Swift） |

### 3.4 Actions 与 run 循环：两种互补模式

Rivet Actor 有两条处理入口，不是新旧替代关系，官方文档对分工的建议是：**"Actions are for getting data, queue entries are for mutating data"**——读操作走 Actions，改状态的操作进队列串行处理。

**Actions** 是定义在 `actions` 对象里的类型化方法，客户端直接调用。它们非常轻量（官方口径：每秒数千次调用是安全的），**默认并行执行**；需要严格顺序控制时才用队列：

```typescript
const counter = actor({
  state: { count: 0 },
  actions: {
    increment: (c, amount: number) => {
      c.state.count += amount;
      return c.state.count;
    },
  },
});

export const registry = setup({ use: { counter } });
```

**run 循环** 是 Actor 内长驻的异步循环，典型形态是从队列逐条取消息处理。这是 Rivet 官方 README 的主示例模式：

```typescript
const counter = actor({
  state: { value: 0 },
  queues: {
    increment: queue<{ amount: number }>(),
  },
  run: async (c) => {
    for await (const message of c.queue.iter()) {
      c.state.value += message.body.amount;
    }
  },
});
```

两者也可以共存：Actions 做查询入口，内部把变更 `c.queue.send()` 塞进 run 循环，保证所有状态变更串行、可预测。带 `run` handler 的 Actor 在 handler 忙时不会休眠，只有当 run 循环阻塞等待队列消息（`iter(...)` / `next(...)` 内部）时才允许休眠——所以你可以在 run 里写普通代码，不用担心执行到一半被休眠打断。

---

## §4 技术架构

### 4.1 分层总览

2026 年的 Rivet 生态分三层：**SDK 层**（开发者写代码的入口）、**Engine 层**（Rust 核心编排引擎）、**Agent 层**（agentOS 和 Dynamic Apps 这些在 Actor 之上的产品化层）。

```text
┌──────────────────────────────────────────────────────────────────┐
│                    Agent 层（可选）                               │
│  agentOS（进程内 agent VM）  │  Dynamic Apps（AI 生成后端）        │
├──────────────────────────────────────────────────────────────────┤
│                    SDK 层（开发者入口）                           │
│  rivetkit  │  rivetkit-rust  │  @rivetkit/effect  │  rivetkit-swift │
├──────────────────────────────────────────────────────────────────┤
│                    Rivet Engine（Rust）                           │
│  Pegboard（Actor 编排） │ Gasoline（Durable Execution）│ Guard（路由）│ Epoxy（KV/EPaxos）│
├──────────────────────────────────────────────────────────────────┤
│                    存储后端                                       │
│  文件系统（单节点） │ PostgreSQL（多节点） │ FoundationDB（企业版） │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Engine 子模块

Engine 的内部模块名（Pegboard、Gasoline、Guard、Epoxy）仍在使用，都可以在 `engine/packages/` 下找到：

| 模块 | 职责 |
|------|------|
| **Pegboard** | Actor 编排、网络通信、生命周期管理（创建/休眠/唤醒）|
| **Gasoline** | Durable Execution Engine——Workflows checkpoint 和自动重试 |
| **Guard** | 流量路由代理，处理 WebSocket 连接和广播 |
| **Epoxy** | 多区域 KV 存储（EPaxos 算法，保证跨区域一致）|

### 4.3 仓库组织（2026-09-13 核实）

所有核心项目都在 `rivet-dev` 组织下。核心是一个 monorepo，产品线和 SDK 分仓库管理：

| 仓库/目录 | 说明 |
|-----------|------|
| [rivet-dev/actors](https://github.com/rivet-dev/actors) | 主 monorepo：`engine/`（Rust 引擎）、`rivetkit-typescript/`、`rivetkit-python/`、`rivetkit-rust/`、`rivetkit-swift/`、`docs/` 全在这里 |
| [rivet-dev/agentos](https://github.com/rivet-dev/agentos) | agentOS——进程内 agent VM（4.6k Stars） |
| [rivet-dev/workflows](https://github.com/rivet-dev/workflows) | Durable Workflows 独立包 `@rivet-dev/workflows` |
| [rivet-dev/dynamic-apps](https://github.com/rivet-dev/dynamic-apps) | Dynamic Apps——每用户 AI 生成后端 |
| [rivet-dev/sandbox-agent](https://github.com/rivet-dev/sandbox-agent) | 在沙箱里跑 Coding Agent、经 HTTP 控制（1.5k Stars） |
| [rivet-dev/rivet-durable-streams](https://github.com/rivet-dev/rivet-durable-streams) | Durable Streams 协议的原生实现 |
| [rivet-dev/skills](https://github.com/rivet-dev/skills) | 给 AI 编码工具用的 Rivet skill 文件（`npx skills add rivet-dev/skills`） |
| [rivet-dev/website](https://github.com/rivet-dev/website) | rivet.dev 网站与文档源码 |

### 4.4 agentOS：跑在你进程里的 Agent 虚拟机

agentOS 是 2026 年 4 月发布的上层产品，官方一句话定位是 "Give agents an operating system as a library"——它不是另一套集群，而是一个 npm 包（`@rivet-dev/agentos`），在你的进程里给每个 agent 起一台轻量 VM。

它和传统 sandbox 的区别在 README 里说得很直接：没有 microVM 要启动、没有容器镜像要拉取、没有嵌套虚拟化。warm VM 创建只要几毫秒，每台 VM 只占几十 MB 内存。官方给的对比数字是：比 sandbox 冷启动快 92 倍、内存省 47 倍、成本低 254 倍。guest JavaScript 跑在 V8 isolates 里，编译型工具跑在 WebAssembly 里。

对 Agent 开发者真正要紧的是两件事：

- **bindings**：agent 通过普通 JavaScript 调用直接触达你的后端函数，不是再起一个网络服务。凭证留在宿主机上，agent 只看到输入和输出。
- **permissions**：文件系统、网络、进程、环境变量访问都走权限门控，对外的网络出口默认拒绝。

内置的 ACP agent 有 Pi、Claude Code、Codex、OpenCode 四个，装法一致。最小用法：

```typescript
import { agentOS, setup } from "@rivet-dev/agentos";
import pi from "@agentos-software/pi";

const vm = agentOS({ software: [pi] });

export const registry = setup({ use: { vm } });
registry.start();
```

agentOS 需要完整 Linux 环境（浏览器、原生二进制、dev server）时也不必二选一，它支持 sandbox mounting——按需拉起一个完整 sandbox 并挂载其文件系统。

---

## §5 性能对比

### 5.1 与传统基础设施对比

| 指标 | Rivet Actor | Kubernetes Pod | Virtual Machine |
|------|-------------|----------------|-----------------|
| **冷启动** | ~20ms（含状态恢复）| ~6s | ~30s |
| **每实例内存** | ~0.6KB | ~50MB | ~512MB |
| **空闲成本** | $0（休眠即零资源）| ~$85/月（集群）| ~$5/月 |
| **水平扩展** | 无限 | ~5k 节点 | 手动 |
| **多区域** | 全球边缘（EPaxos）| 1 区域 | 1 区域 |

测量口径见 §2.3，这里不重复。补充一个官方没有直接给出、但可以从口径推出的判断：K8s 的 6s 是"调度 + 拉镜像 + 启动"的一次性成本，Pod 起来之后 JVM/Node 进程的稳态吞吐并不受影响；所以这组数字真正区分的是**创建新实例的频率**——每请求新建（serverless 风格）或每会话新建（Agent 场景）时差距最大，长驻服务时差距无关紧要。

### 5.2 与状态存储对比

| 指标 | Rivet Actor | Redis | Postgres |
|------|-------------|-------|----------|
| **状态读取延迟** | 0ms | ~1ms | ~5ms |

Rivet 的 0ms 不是玄学——状态和计算进程在同一个地址空间，读 `c.state.count` 就是内存读。Redis 虽快但仍然是跨进程 RPC，Postgres 更是磁盘 IO。代价是这份状态只属于这一个 Actor，跨 Actor 查询要走队列或外部存储——它替代的是"会话级热点状态"，不是通用数据库。

---

## §6 快速开始

### 6.1 方式 A：Just a Library（本地开发）

RivetKit 是一个普通 npm 库——装好、定义 Actor、启动 registry，本地就在 6420 端口跑起来，不需要先部署任何基础设施：

```bash
npm install rivetkit
```

```typescript
import { actor, setup } from "rivetkit";

export const counter = actor({
  state: { count: 0 },
  actions: {
    increment: (c, x: number) => {
      c.state.count += x;
      c.broadcast("newCount", c.state.count);
      return c.state.count;
    },
  },
});

export const registry = setup({ use: { counter } });
registry.start();
```

```bash
npx tsx --watch index.ts   # 或 bun --watch index.ts
```

服务起在 `http://localhost:6420`。浏览器打开这个地址就是 Rivet Inspector 开发者工具，可以实时查看和调试 Actor。客户端连接（前端后端皆可）：

```typescript
import { createClient } from "rivetkit/client";
import type { registry } from "./index";

const client = createClient<typeof registry>("http://localhost:6420");

// getOrCreate 拿到（或创建）key 为 ["my-counter"] 的 Actor
const counter = client.counter.getOrCreate(["my-counter"]);

// 直接调用 action，类型全链路推断
const count = await counter.increment(3);
console.log("New count:", count);

// 监听实时事件
const connection = counter.connect();
connection.on("newCount", (newCount: number) => {
  console.log("Count changed:", newCount);
});
```

React 前端装 `@rivetkit/react`，用 `createRivetKit` 工厂生成 hooks：

```tsx
import { createRivetKit } from "@rivetkit/react";
import { useState } from "react";
import type { registry } from "./backend";

const { useActor } = createRivetKit<typeof registry>("http://localhost:6420");

function Counter() {
  const [count, setCount] = useState(0);

  const counter = useActor({ name: "counter", key: ["my-counter"] });

  counter.useEvent("newCount", (x: number) => setCount(x));

  const increment = async () => {
    await counter.connection?.increment(1);
  };

  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={increment}>Increment</button>
    </div>
  );
}
```

支持的运行时：Node.js、Bun、Deno，以及 Cloudflare Workers、Vercel、Supabase Functions 等 serverless 平台（serverless 模式下 Actor 代码响应 Rivet 的 HTTP 请求而非长驻进程，可用 `rivet dev --provider <name>` 本地模拟）。

### 6.2 方式 B：Rivet Cloud（生产托管）

Rivet CLI（`@rivetkit/cli`）是可选的，主要为两件事存在：部署到 Rivet Cloud、给 serverless 平台做本地开发：

```bash
npx @rivetkit/cli deploy   # 构建镜像并部署到 Rivet Cloud，打印 dashboard URL
npx @rivetkit/cli dev      # 本地起 engine + dev server（--provider 选 cloudflare/supabase 等）
```

`rivet deploy` 会构建并推送项目的 Docker 镜像、创建或更新托管 compute pool。控制平面由 Rivet 托管在 `dashboard.rivet.dev`，你的 worker 主动向外连接它，不需要公网入口或开防火墙——这种"只管 worker"的模式官方叫 BYOC。

### 6.3 方式 C：Self-Host（Docker）

Engine 有官方 Docker 镜像 `rivetdev/engine`：

```bash
# 用 SQLite（最简单）
docker run -p 6420:6420 rivetdev/engine

# 用 Postgres（多节点部署推荐）
docker run -p 6420:6420 \
  -e DATABASE_URL=postgres://user:pass@host:5432/rivet \
  rivetdev/engine
```

存储后端的官方口径值得记住：**文件系统**推荐单节点；**PostgreSQL** 面向多节点，官方明确说适合 light-to-moderate 负载、不为企业级规模设计；**FoundationDB** 扩展性和性能最好，但**需要企业版授权**。选型时别把 FoundationDB 当成开箱即用的免费选项。

---

## §7 核心功能详解

### 7.1 Durable Workflows

Durable Workflows 是 Rivet 在 2026 年最具差异化的原语，2026-02-24 发布，独立包 `@rivet-dev/workflows`。它把多步骤流程的每一步自动 checkpoint——进程崩溃、重启、升级后，从最后一个 checkpoint 重放继续。

一个 workflow 就是一个"持久化、可重放的 actor 定义"：支持完整的 actor 配置（state、actions、生命周期钩子），区别在 `run` 函数里用重放安全的工作流原语。

```typescript
import { setup, workflow } from "@rivet-dev/workflows";

export const invoiceActor = workflow({
  state: {
    invoiceId: null as string | null,
    total: 0,
    status: "idle" as "idle" | "complete",
  },
  run: async (ctx) => {
    // 每个 step 是一个 checkpoint
    const subtotal = await ctx.step("load-subtotal", async () => loadSubtotal());
    const tax = await ctx.step("calculate-tax", async () => calculateTax(subtotal));
    await ctx.step("save-invoice", async (step) => saveInvoice(step, subtotal, tax));
    ctx.state.status = "complete";
  },
  actions: {
    getState: (c) => c.state,
  },
});

export const registry = setup({ use: { invoiceActor } });
```

如果 `send-welcome-email` 执行到一半进程崩溃了，重启后 Workflow 会跳过已完成的 step，从断点重新执行。**开发者不需要写任何恢复代码**。

官方文档确认的控制流原语：

- **Durable Loops**：`ctx.loop()` 承载长寿命工作循环（官方推荐的 workflow 形态就是"setup → 循环处理队列 → teardown"）
- **Sleep / 定时器**：以队列消息为触发源，在 workflow 内持久化 sleep
- **Join / Race**：多个独立任务并行后汇合（join），或取最先完成者（race）
- **Rollback**：为有补偿动作的 step 前置 rollback checkpoint；跨 Actor 的 saga（补偿事务）有官方模式
- **队列暂停**：workflow 可以等一条队列消息再继续——事件驱动，可停任意久

一个必须写进肌肉记忆的边界（官方原话）：**失败的 step 重试时，它的 `state` / `vars` 变更不会被回滚**。所以 step 函数要按幂等写，副作用尽量放在外部调用的最后，或者用 `tryStep` / `try` 显式兜住失败。

**队列驱动的 Agent 循环**（官方推荐的长驻 workflow 形态）：

```typescript
import { queue, setup, workflow } from "@rivet-dev/workflows";

export const agent = workflow({
  state: { processed: 0 },
  queues: {
    input: queue<{ text: string }>(),
  },
  run: async (ctx) => {
    await ctx.loop("agent-loop", async (loopCtx) => {
      // 等待下一条消息（休眠等待，不占资源）
      const message = await loopCtx.queue.next("input");
      await loopCtx.step("apply-command", async (step) => {
        await handleCommand(step, message.body.text);
        loopCtx.state.processed += 1;
      });
    });
  },
  actions: { getState: (c) => c.state },
});

export const registry = setup({ use: { agent } });
```

### 7.2 Queues（持久化消息队列）

Queues 是跨 Actor 通信和异步任务分发的基础。消息持久化，消费者可以宕机再回来继续处理；每个 Actor 的队列存储按 actor key 隔离。默认模式：`queues` 里声明队列名和负载类型，`run` 循环里 `c.queue.iter()` 消费，客户端 `handle.send()` 发布：

```typescript
import { actor, queue, setup } from "rivetkit";

export const worker = actor({
  state: { processed: 0 },

  queues: {
    tasks: queue<{ data: string }>(),
  },

  run: async (c) => {
    for await (const message of c.queue.iter()) {
      await processData(message.body.data);
      c.state.processed += 1;
    }
  },
});

export const registry = setup({ use: { worker } });
```

```typescript
// 客户端（或另一个 Actor 用 c.client()）
const handle = client.worker.getOrCreate(["worker-1"]);
await handle.send("tasks", { data: "hello" });
```

**请求/响应模式**：队列负载可以声明第二个类型参数作为完成回执。消费侧在 `iter({ completable: true })` 循环里调 `message.complete()`，发送侧 `send` 时带 `wait: true` 等回执：

```typescript
const counter = actor({
  state: { value: 0 },
  queues: {
    increment: queue<{ amount: number }, { value: number }>(),
  },
  run: async (c) => {
    for await (const message of c.queue.iter({ completable: true })) {
      c.state.value += message.body.amount;
      await message.complete({ value: c.state.value });
    }
  },
});

// 发送方等到处理完成
const result = await handle.send("increment", { amount: 5 }, { wait: true, timeout: 5_000 });
if (result.status === "completed") {
  console.log(result.response.value); // 5
}
```

两条来自官方文档的坑位提醒：

- `wait: true` 会阻塞发送方的 run 循环。**Actor 给自己发 `wait: true` 消息是必然死锁**（run 循环正在处理当前消息）。Actor 之间也尽量避免，改为"发出去 → 干完回一条"。
- `message.complete()` 不改变持久化语义：消息在**接收时**就从队列存储移除，不是完成时。处理失败不会重新投递，等待回执的一方会超时（`status: "timedOut"`）。

### 7.3 Schedule & Cron（定时调度）

2026 年 7 月发布。定时任务以 **action 名** 为单位调度，跨休眠、重启、升级、崩溃存活，Actor 睡着也没关系——到点 Rivet 会把它唤醒。惯用位置是 `onCreate` 钩子，创建时注册一次：

```typescript
const reports = actor({
  onCreate: async (c) => {
    // cron 表达式（标准五段式），时区默认 UTC
    await c.cron.set({
      name: "daily-report",
      expression: "0 9 * * *",
      action: "runReport",
      args: ["sales"],                    // 可选
      timezone: "America/Los_Angeles",    // 可选
    });

    // 一次性延迟（毫秒），到点调用 action
    await c.schedule.after(30_000, "sendReminder", "reminder-123");

    // 固定间隔（最小 5 秒）
    await c.cron.every({ name: "refresh-cache", interval: 60_000, action: "refreshCache" });
  },

  actions: {
    runReport: (c, report: string) => { /* ... */ },
    sendReminder: (c, reminderId: string) => { /* ... */ },
    refreshCache: (c, cache: string) => { /* ... */ },
  },
});
```

管理接口齐全：`c.cron.get/list/delete/history` 查看与删除定时任务，`c.schedule.get/list/cancel` 管理一次性调度；`c.cron.history()` 能看每次运行的结果（`running` / `ok` / `error` / `skipped`，默认保留 100 条）。执行语义上，失败的运行**不会立即重试**——周期任务等下一个周期，一次性任务即告完成，需要重试就基于 history 自己搭；重叠的周期运行会被跳过；action 被删掉后对应任务自动删除。

### 7.4 实时事件（WebSocket）

服务端 `c.broadcast(eventName, ...args)` 向所有连接的客户端广播；客户端通过 `connect()` 拿到连接对象后 `.on()` 订阅（React 用 `counter.useEvent(...)`，见 §6.1）。事件名和负载类型用 `events` + `event<T>()` 声明：

```typescript
import { actor, event } from "rivetkit";

const chatRoom = actor({
  state: { messages: [] },
  events: {
    message: event<string>(),
  },
  actions: {
    send: (c, text: string) => {
      c.state.messages.push(text);
      c.broadcast("message", text);
    },
  },
});
```

Actions 只有单个返回值；要把一段数据流式推给前端（比如 LLM token 流），用的就是事件而不是 action 返回值。

### 7.5 SQLite 内嵌数据库

每个 Actor 有自己独立的 SQLite 实例——`onMigrate` 在启动时原子执行，数据随 Actor 生命周期持久化。适合需要 SQL 查询、又不值得为它开独立 Postgres 的场景。进阶玩法：SQLite 当 source of truth，`c.vars` 里放一份工作副本，读走内存、写回 `c.db`；也有官方的 Drizzle 集成（`rivetkit/db/drizzle`）和 SQLite Profiling 工具。

（基础示例见 §3.2。）

### 7.6 Actor 命名与图标

Actor 可以设置 `options.name` 和 `options.icon`，在 Rivet Inspector 和 Dashboard 里方便识别。icon 支持 Emoji 或 FontAwesome 图标名（不带 `fa-` 前缀）：

```typescript
const notificationService = actor({
  options: { name: "通知服务", icon: "bell" },
  // ...
});
```

### 7.7 MCP 集成

2026-09-10 发布的 Rivet MCP 让 AI 客户端直接连上 Rivet：检查 Actor、调用 action、使用 Actor Inspector。托管端点是 `https://mcp.rivet.dev/mcp`，接入只需一条命令（连接时 Rivet 会弹出授权流程）：

```bash
# Claude Code
claude mcp add --transport http rivet https://mcp.rivet.dev/mcp

# Codex
codex mcp add rivet --url https://mcp.rivet.dev/mcp

# Cursor：在 mcpServers 配置里加 { "rivet": { "url": "https://mcp.rivet.dev/mcp" } }

# 本地模式（连本机已在跑的 Rivet，无需登录）
# { "command": "npx", "args": ["-y", "@rivet-dev/mcp", "--target", "local"] }
```

托管端点还支持用 organization / project / namespace 查询参数收窄访问范围。配合 `rivet-dev/skills` 仓库的 skill 文件（`npx skills add rivet-dev/skills`），AI 编码工具可以按官方文档生成 Rivet 项目代码。

---

## §8 使用场景

### 8.1 AI Agent（最适合的场景）

Rivet 的设计初衷就是为 AI Agent 提供一个生产级的状态层。一个 Agent 一个 Actor，天然适合"每个用户一个独立 agent 会话"的架构。把 §7.1 的队列循环具体化，一次用户提问在系统里的完整路径是：

1. 客户端 `handle.send("input", { text })` 把问题投进 Actor 的持久化队列；
2. Actor 的 run 循环醒来，取出消息，`ctx.step("llm-call")` 内调用 LLM——这一步自动 checkpoint；
3. 工具调用逐个包在 `ctx.step("tool-...")` 里，每个都是独立 checkpoint；
4. 回复写进 `state`，`c.broadcast` 推给前端，回到循环等下一条消息；
5. 进程此时崩溃：重启后 workflow 重放历史，已完成的 step 直接跳过，从断点继续，用户的会话上下文一条不丢。

```typescript
import { queue, setup, workflow } from "@rivet-dev/workflows";

export const agentActor = workflow({
  state: { messages: [] as Message[] },
  queues: { input: queue<{ text: string }>() },

  run: async (ctx) => {
    await ctx.loop("agent-loop", async (loopCtx) => {
      const message = await loopCtx.queue.next("input");

      const response = await loopCtx.step("llm-call", async (step) => {
        loopCtx.state.messages.push({ role: "user", content: message.body.text });
        return await callLLM(step, loopCtx.state.messages);
      });

      // 每个工具调用也是独立 checkpoint
      for (const toolCall of response.toolCalls) {
        await loopCtx.step(`tool-${toolCall.name}`, async () => {
          const result = await executeTool(toolCall);
          loopCtx.state.messages.push(result);
        });
      }

      // 广播放在 step 内：state 变更 + broadcast 是官方推荐的进度通知模式
      await loopCtx.step("reply", async (step) => {
        step.broadcast("reply", response.text);
      });
    });
  },

  options: { name: "AI Agent Session", icon: "robot" },
});

export const registry = setup({ use: { agentActor } });
```

为什么这个架构比"LLM CLI 跑在 sandbox 里"更稳？因为 Agent Loop 本身在一个有状态的 Actor 里——sandbox 挂了不影响 Agent 的上下文和重试逻辑。Rivet 官方 2026 年 7 月的博客（"Run your harness outside the sandbox"）论证的正是这一点：sandbox 用来装不可信代码，harness 需要可靠的状态持久化和错误恢复，两者应该分开。agentOS 就是这个架构的生产实现（见 §4.4）。

### 8.2 多人协作文档

每个文档一个 Actor，向所有连接用户广播变更。状态和文档数据共置，读延迟为零：

```typescript
const docActor = actor({
  state: { content: "" },
  db: db({ /* schema */ }),

  actions: {
    applyChange: (c, change: Change) => {
      c.state.content = applyOps(c.state.content, change.ops);
      c.db.execute("INSERT INTO changes (...)");
      c.broadcast("change", { content: c.state.content });
      return c.state.content;
    },
  },

  options: { name: "Collab Doc", icon: "file" },
});
```

### 8.3 沙箱编排

一个 Actor 协调多个 sandbox worker，定时清理交给 Schedule & Cron。注意下面的写法：调度目标是 action 名，不是匿名回调——这正是 §7.3 说的"cron 调 action"语义：

```typescript
const workspace = actor({
  state: { activeSandboxes: [] as string[] },

  onCreate: async (c) => {
    await c.cron.every({
      name: "sweep-expired",
      interval: 30 * 60_000,
      action: "sweepExpired",
    });
  },

  actions: {
    sweepExpired: async (c) => {
      for (const id of c.state.activeSandboxes) {
        if (await isExpired(id)) {
          await terminateSandbox(id);
        }
      }
      c.state.activeSandboxes = c.state.activeSandboxes.filter(isRecent);
    },

    createSandbox: async (c, taskId: string) => {
      const sandbox = await createSandboxWorker(taskId);
      c.state.activeSandboxes.push(sandbox.id);
      return sandbox.id;
    },
  },
});
```

这个场景 rivet-dev 有更完整的产品化版本：`sandbox-agent` 仓库提供"在沙箱里跑 Coding Agent、经 HTTP 控制"的完整方案，可按需取用。

### 8.4 多租户数据库

每个租户一个 Actor，状态（租户数据）和计算（读写逻辑）在同一个进程里。0ms 延迟意味着"租户自己的 Actor 处理自己的请求"，比"走 Postgres 查一遍"快得多。配合 §3.2 的混用模式：SQLite 存租户数据，`createVars` 启动时从外部系统加载补充信息。

### 8.5 Dynamic Apps（2026-08 新场景）

2026-08-31 发布的产品线，面向"用户生成应用"的平台场景：用户通过 AI 描述想要一个"记账 App"，平台用 sandboxed deployment VM 构建用户生成的请求处理器，发布状态存在 Rivet Actor 里，缓存命中的请求直接从本地有界的 V8 isolates 出结果，不用每次都路由到执行 Actor。对平台方来说，这解决了"用户-generated 代码怎么安全、低成本地跑"的问题。

---

## §9 部署选项

### 9.1 三个部署模型

官方把部署讲成三件事，别混：

| 模型 | 说明 | 适用场景 |
|------|------|----------|
| **Just a Library** | npm install，`registry.start()` 起在本地进程，SQLite 默认持久化 | 开发调试、小项目快速上线 |
| **BYOC + Rivet Cloud** | 你只跑 worker（业务代码），控制平面和存储由 Rivet Cloud 托管 | 大多数生产部署，支持 serverless worker |
| **Self-Host** | worker、控制平面、存储全部自己管，Engine 有官方 Docker 镜像 | 气隙环境、严格合规、自定义安全策略 |

一个容易被忽略的点：**worker 主动向外连接控制平面**，所以 worker 不需要公网可达、不需要开入站防火墙规则——这在企业内网部署里能省掉很多审批。

### 9.2 运行时模式

每个部署模型下 worker 还有两种运行时形态（`RIVETKIT_RUNTIME_MODE` 控制，默认 Runner）：

- **Runner**（默认）：业务代码是长驻进程，主动连到 Rivet 控制平面领任务。本地开发、容器、VM、裸金属都是这个模式。
- **Serverless**：Actor 代码被动响应 Rivet 的 HTTP 请求，自动扩缩。Vercel、Cloudflare Workers、Supabase Functions 等 serverless 平台用这个模式，Rivet Cloud 也会自动设置。

### 9.3 Self-Host 要点

```bash
# 最简（SQLite 自带）
docker run -p 6420:6420 rivetdev/engine

# 多节点推荐（Postgres）
docker run -p 6420:6420 \
  -e DATABASE_URL=postgres://user:pass@host:5432/rivet \
  rivetdev/engine
```

存储后端选型（官方口径）：

| 后端 | 定位 |
|------|------|
| **文件系统** | 单节点部署推荐 |
| **PostgreSQL** | 多节点部署推荐；适合轻到中等负载，官方明说不为企业级规模设计 |
| **FoundationDB** | 扩展性与性能最好，多区域场景；**需要企业版授权** |

Kubernetes、VM、AWS、Railway、Render 各平台都有官方部署指南，控制平面支持多区域、TLS、备份恢复。

---

## §10 内置可观测性

### 10.1 Rivet Inspector

本地开发时 Inspector 就在 6420 端口（浏览器打开即用），自托管或 Cloud 的 Dashboard 也自带：

| 功能 | 说明 |
|------|------|
| **SQLite Viewer** | 实时浏览 Actor 内的 SQLite 数据库，执行查询 |
| **Workflow Inspector** | 查看 workflow 历史与 checkpoint 状态（`GET /inspector/workflow-history`） |
| **Queue Monitor** | 队列大小与消息堆积（`GET /inspector/queue`，`/inspector/summary` 含 queueSize） |
| **Event Stream** | 实时订阅 state 变更、广播、action 调用 |
| **REPL** | 直接调用 actor actions、发送队列消息 |
| **Actor Tree** | 浏览全局所有 Actor，按名称/图标/状态过滤 |

注意：非 dev 模式下 inspector 端点需要授权。

### 10.2 日志

RivetKit 内置 Pino 日志，也支持接入自定义 logger（见 Logging 文档）。workflow 的错误钩子会带上 attempt 次数、重试计数、是否还会重试和下次重试延迟，排查重试风暴时先看这里。

---

## §11 集成生态

### 11.1 上层产品

| 产品 | 说明 |
|------|------|
| **agentOS** | 进程内 agent 轻量 VM（`@rivet-dev/agentos`），bindings + 权限门控，内置 Pi / Claude Code / Codex / OpenCode |
| **Dynamic Apps** | AI 生成的每用户后端：sandboxed VM 构建 + Actor 存发布状态 + V8 isolates 出缓存命中 |
| **Rivet MCP** | `mcp.rivet.dev` 托管端点，Claude Code / Codex / Cursor / Gemini CLI / VS Code 直连 |
| **sandbox-agent** | 沙箱内跑 Coding Agent、HTTP 控制（独立开源项目） |

### 11.2 基础设施

| 平台 | 说明 |
|------|------|
| **Vercel** | 官方模板 + serverless worker 支持 |
| **Railway** | 快速部署（官方模板含多区域配置）|
| **Cloudflare Workers / Supabase Functions** | serverless worker 支持 |
| **AWS / Kubernetes / VM** | Runner 模式自托管 |
| **Docker** | `rivetdev/engine` 官方镜像 |

### 11.3 SDK 与框架

| SDK / 框架 | 说明 |
|------------|------|
| **RivetKit TypeScript** | 主 SDK，npm `rivetkit` |
| **@rivetkit/effect** | Effect 函数式 SDK（Beta）|
| **RivetKit Rust** | Rust SDK（Beta）|
| **RivetKit Swift** | iOS / macOS Client SDK（SwiftUI 另有文档）|
| **RivetKit Python** | Python SDK（monorepo 内）|
| **@rivetkit/react** | React hooks（`createRivetKit` / `useActor`）|
| **Vercel AI SDK** | 官方示例集成 |
| **Drizzle** | SQLite + Drizzle ORM 官方集成 |
| **Zod** | action 输入校验（Standard Schema）|
| **Pino** | 内置日志 |

### 11.4 DevTooling

| 工具 | 说明 |
|------|------|
| **Rivet Inspector** | 本地 6420 端口即开的开发者工具 + Dashboard |
| **Rivet CLI** | `@rivetkit/cli`：`rivet deploy`、`rivet dev`、`rivet engine`、`rivet token` 等 |
| **Claude Code Skill** | `npx skills add rivet-dev/skills`——让 AI 编码工具按官方文档生成 Rivet 代码 |
| **Rivet MCP** | AI 客户端直连运行中的 Rivet 实例（§7.7）|

---

## §12 实践建议

### 12.1 Actor 设计原则

- **一个 Actor 一个职责**。粒度是"一个会话 / 一个用户 / 一个文档"，不是"所有聊天记录"。粒度错了，后面所有问题都会放大。
- **状态分层**。简单数据放 `state`，不可序列化对象放 `vars`，需要 SQL 查询放 `db`。SQLite 当 source of truth、`vars` 放内存工作副本的模式值得记住。
- **读走 Actions，写进队列**。官方的原话是 "Actions are for getting data, queue entries are for mutating data"。Actions 默认并行，队列严格串行——把变更收敛到一条队列循环里，顺序就可预测。
- **别让 Actor 互相等**。Actor 间通信发队列消息就够；`wait: true` 留给外部调用方（HTTP handler、CLI、客户端）。给自己发 `wait: true` 是必然死锁。

### 12.2 Workflow 使用建议

- **step 名要语义化且稳定**：`"create-customer"` 而不是 `step-1`——checkpoint 按 step 名记录，改名等于换了一步。
- **按幂等写 step**：官方明确 `state` / `vars` 变更在失败重试时不会回滚。副作用放外部调用最后，或用 `tryStep` / `try` 显式处理失败。
- **长耗时外部操作包进 step**：网络请求、数据库写入、LLM 调用都该有 checkpoint。
- **长驻 workflow 用"setup → 队列循环 → teardown"形态**：这是官方 quickstart 的推荐形状，别把所有逻辑平铺在 run 顶层。
- **checkpoint 里别塞大对象**：workflow 进度存 `state` 并随进度广播，恢复速度取决于 checkpoint 大小。

### 12.3 性能优化

- **信任默认持久化**：`state` 变更按 1 秒节流批量写盘（`stateSaveInterval`），休眠/关闭时强制刷盘。高频写不需要你手动合并。
- **状态最小化**：`state` 里只放必须 durable 的数据；大数组、历史记录移到 SQLite。
- **活用休眠**：run 循环阻塞在 `iter()` / `next()` 上时 Actor 才能休眠——循环别写死循环空转，把等待交给队列。

### 12.4 安全

- **校验所有 action 输入**：actions 是公开 API。官方建议用 Zod（支持 Standard Schema 的校验库都可以）做参数验证；错误处理上，未捕获异常只返回 `internal_error`，不会把内部信息漏给客户端，主动返回用户可见错误用 `UserError`。
- **用 agentOS 的权限门控跑 agent**：文件、网络、进程、环境变量逐项授权，网络出口默认拒绝。
- **限流发送侧**：持久化队列可能被恶意消息塞满，在 `send` 入口做限流。
- **隔离租户数据**：不同租户用不同 Actor（key 隔离已经给了第一层），敏感场景再加独立 SQLite 文件或 Postgres schema。

---

## §13 常见问题

### Q1：Rivet vs Cloudflare Durable Objects？

两者都是"有状态的 Actor 运行时"，但定位差异很大：

| 特性 | Rivet | Cloudflare Durable Objects |
|------|-------|--------------------------|
| **持久化机制** | Durable State 自动 checkpoint（1s 节流）+ SQLite | 手动 `state.storage.put()` |
| **Durable Workflows** | ✅ 内建 `ctx.step()` checkpoint | ❌ 无，需自己用 DO 模拟 |
| **开源** | ✅ Apache 2.0 | ❌ Cloudflare 专有 |
| **自托管** | ✅ Docker / 任意云 | ❌ 必须跑在 Cloudflare Workers |
| **状态读取延迟** | 0ms（内存直读） | 0ms（内存直读）|
| **Agent 基建** | ✅ workflow + queue + cron + agentOS | ❌ 需要自己拼 |

**一句话总结**：DO 是"有状态的 Cloudflare Worker"，Rivet 是完整的 actor runtime——durable workflow、queue、cron 都在盒子里，还能自己部署。

### Q2：Rivet vs Temporal？

| 特性 | Rivet | Temporal |
|------|-------|--------|
| **核心抽象** | Actor（状态 + 进程 + 队列一体）| Workflow + Activity（无状态函数的 durable 包装）|
| **状态模型** | 状态在 Actor 进程内，自动持久化 | Temporal 服务自己的持久化层 |
| **适用场景** | Agent、协作文档、实时应用（每个会话 = 一个 Actor）| 后端工作流（审批、订单、ETL）|
| **代码复杂度** | 低——`actor({ state, actions, run })` 就够 | 较高——要理解 determinism、超时、重试策略 |
| **扩展粒度** | 每个用户一个 Actor | 一个 Workflow 一个流程实例 |

Rivet 不打算替代 Temporal。"一个流程跑几个异步步骤、支持人工审批、失败自动重试"——Temporal 更成熟。"每个用户一个独立 agent 会话、状态和计算在一个进程里、0ms 延迟"——Rivet 更合适。两者也可以共存：会话层用 Rivet Actor，重型业务流程下沉 Temporal。

### Q3：什么时候用 agentOS vs 纯 Actors？

agentOS 是跑在你进程里的 agent VM 库。如果你的 agent 需要 harness（Claude Code、Codex、Pi、OpenCode）、需要在受控环境里执行 agent 生成的代码，agentOS 给你 bindings + 权限门控 + 每会话隔离。如果你只是要 durable 的工作流和状态，纯 Rivet Actors + Workflows 就够了，不需要引入 agentOS。

### Q4：什么时候应该使用 Rivet？

- 需要持久状态的 AI Agent（一个 agent 一个 Actor，天然隔离）
- 多人实时协作应用（一个文档 / 一个房间 = 一个 Actor）
- 低延迟状态访问的多租户系统
- durable 工作流需求（`ctx.step()` 自动 checkpoint）
- 想自托管状态运行时（Apache 2.0，不被平台锁死）

### Q5：什么时候不应该使用 Rivet？

- 无状态微服务（普通 HTTP handler 或 serverless function 就够了）
- 极高吞吐的临时任务分发（每秒百万级消息用 Kafka / SQS 这类专门队列——Rivet 队列是每个 Actor 私有的，不是共享 topic）
- 跨多个 Actor 的强一致事务（Actor 模型没有跨 Actor 事务，需要的话用传统数据库）
- 不需要持久化的纯计算任务（持久化和调度有固定开销）

### Q6：支持哪些数据库后端？

| 数据库 | 状态 | 说明 |
|--------|------|------|
| **文件系统 / SQLite** | ✅ 默认 | 单节点推荐，Just a Library 模式开箱即用 |
| **PostgreSQL** | ✅ 支持 | 多节点推荐；轻到中等负载，不为企业级规模设计 |
| **FoundationDB** | ✅ 支持 | 扩展性最好，多区域 EPaxos；**需要企业版授权** |

### Q7：怎么调试？

本地开发打开 `http://localhost:6420` 就是 Inspector：浏览和查询 Actor 的 SQLite、看 workflow 历史与 checkpoint、看队列堆积、REPL 直接调 action、实时订阅事件流。远程环境用 Dashboard；非 dev 模式记得配授权。队列问题的排查入口是 `GET /inspector/queue` 和 `GET /inspector/summary` 的 queueSize。

### Q8：Just a Library 模式和 Cloud 模式有什么区别？

Just a Library 是"我自己跑进程，把 rivetkit 当库 import"——控制平面和存储都在你本地进程里（SQLite 持久化），适合开发和小项目。Rivet Cloud 是"worker 连到 rivet.dev 托管的控制平面"——Engine、KV、存储全托管，适合生产。**两者的 Actor 定义代码完全一样**，迁移只是换部署方式，不改业务代码。

---

## §14 总结

### 14.1 核心优势一句话版

Rivet 把"有状态"这个最难的事做成了基础设施：**状态在进程内（0ms 读写）、自动持久化（不用写 save）、崩溃自动恢复（`ctx.step()` checkpoint）、空闲零成本（自动休眠）**。

### 14.2 选型建议

| 场景 | 推荐度 |
|------|--------|
| AI Agent（有持久化状态）| ⭐⭐⭐⭐⭐ 首选 |
| AI Agent 代码执行环境 | ⭐⭐⭐⭐⭐ 用 agentOS |
| 多人实时协作 | ⭐⭐⭐⭐⭐ |
| Durable 工作流 | ⭐⭐⭐⭐⭐ |
| 无状态微服务 | ❌ 过度工程 |
| 强一致分布式事务 | ❌ 用 Temporal 或传统 DB |

落地顺序建议：先用 Just a Library 把核心 Actor 写出来（半天足够），本地 Inspector 调通状态与队列；需要多实例或 serverless 时切 BYOC + Rivet Cloud（代码不变）；有数据主权要求再上 Self-Host。agentOS 留到 agent 真的需要受控代码执行环境时再引入。

### 14.3 生态快照（2026-09）

| 组件 | 状态 |
|------|------|
| Rivet Engine（actors monorepo）| 生产可用（6.1k Stars，v2.3.17）|
| Durable Workflows（2026-02）| 生产可用 |
| agentOS（2026-04）| 生产可用 |
| Schedule & Cron（2026-07）| 生产可用 |
| Dynamic Apps（2026-08）| 生产可用 |
| Rivet MCP（2026-09）| 生产可用 |
| Effect SDK（2026-06）| Beta |
| Rust SDK（2026-06）| Beta |
| Python SDK | monorepo 内迭代 |

### 14.4 项目信息（2026-09-13 核实）

| 项 | 值 |
|----|----|
| 主仓库 | [rivet-dev/actors](https://github.com/rivet-dev/actors) |
| Stars | 6,124 |
| 最新版本 | v2.3.17（2026-09-10）|
| 许可证 | Apache-2.0 |
| 主语言 | Rust（Engine）+ TypeScript（SDK）|
| 官方文档 | <https://rivet.dev/docs> |
| agentOS 文档 | <https://agentos-sdk.dev/docs> |
| Workflows 文档 | <https://rivet.dev/workflows/docs> |
| Discord | <https://rivet.dev/discord> |
| X | [@rivet_dev](https://x.com/rivet_dev) |
