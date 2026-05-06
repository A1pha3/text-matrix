---
title: "Rivet：新一代 Actor 持久化运行时完全指南"
date: "2026-03-31T15:20:00+08:00"
slug: "rivet-actor-runtime-guide"
description: "全面解析 Rivet (5.3k Stars)：新一代 Actor 持久化运行时。~20ms冷启动、~0.6KB内存、$0空闲成本，内置Workflows/Queues/Scheduling，支持TypeScript/Rust/Python SDK。"
draft: false
categories: ["技术笔记"]
tags: ["Rivet", "Actor", "持久化运行时", "AI Agent", "Rust", "TypeScript", "WebSocket"]
---

# Rivet：新一代 Actor 持久化运行时完全指南

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 Rivet Actor 模型的核心思想与价值主张
- ✅ 掌握 Rivet 的技术架构（Engine + RivetKit）
- ✅ 理解 Actor 与传统基础设施的对比优势
- ✅ 熟练使用 RivetKit TypeScript/Python/Rust 客户端
- ✅ 构建 AI Agent 应用
- ✅ 实现多人协作应用
- ✅ 部署到 Self-Host 或 Rivet Cloud
- ✅ 理解 Rivet 的适用场景与选型建议

---

## §2 项目概述

### 2.1 什么是 Rivet？

**Rivet**（官方仓库：[rivet-dev/rivet](https://github.com/rivet-dev/rivet)）是一个**新一代 Actor 持久化运行时**，核心理念是：

> Rivet Actors are the primitive for stateful workloads. Built for AI agents, collaborative apps, and durable execution.

**翻译**：Rivet Actor 是有状态工作负载的原始抽象。为 AI Agent、协作应用和持久化执行而构建。

**官方网站**：https://www.rivet.dev

### 2.2 核心价值主张

| 价值 | 说明 |
|------|------|
| **内存状态** | 状态与计算共置，实现即时读写。支持 SQLite 或自选数据库持久化 |
| **持久运行** | 活跃时长期运行，空闲时休眠 |
| **无限扩展** | 支持突发工作负载，零成本空闲 |
| **全球边缘网络** | 部署在用户附近或特定法律管辖区，无需复杂配置 |

### 2.3 核心数据

```
Stars:     5,300 (5.3k)
Forks:     163
Watchers:  17
贡献者:    25 人
提交数:   4,865 次
分支数:    679 个
标签数:    49 个
最新版本:  2.1.10 (2026-03-26)
许可证:    Apache-2.0
```

### 2.4 技术栈

| 组件 | 语言 | 占比 |
|------|------|------|
| **Rivet Engine** | Rust | 42.7% |
| **RivetKit TypeScript** | TypeScript | 36.2% |
| **文档** | MDX | 14.7% |
| **RivetKit Swift** | Swift | 2.9% |
| **网站** | Astro | 1.4% |
| **其他** | JavaScript 等 | 1.5% |

---

## §3 Actor 模型深度解析

### 3.1 什么是 Actor？

Actor 是一种并发计算模型，每个 Actor 是：

- **独立的计算单元**：拥有自己的状态和执行上下文
- **长期运行**：不像函数调用一样短暂，而是持续运行
- **消息驱动**：通过队列接收消息，处理后响应

### 3.2 Rivet Actor 的特性

| 特性 | 说明 |
|------|------|
| **内存状态** | 状态在内存中，低延迟读取写入 |
| **自动持久化** | 使用 SQLite 或自选数据库自动持久化状态 |
| **长期运行** | 活跃时持续运行，空闲时休眠节省资源 |
| **无限扩展** | 水平扩展无限制，支持零扩展 |
| **WebSocket 内置** | 内置实时双向流 |
| **Workflows** | 多步骤操作，自动重试 |
| **Queues** | 持久化消息队列 |
| **Scheduling** | 定时器和 Cron 任务 |

### 3.3 代码示例

**后端 Actor 定义**

```typescript
const agent = actor({
  // 内存状态，自动持久化
  state: {
    messages: [] as Message[],
  },
  // 长期运行的 Actor 进程
  run: async (c) => {
    // 从队列处理传入消息
    for await (const msg of c.queue.iter()) {
      c.state.messages.push({
        role: "user",
        content: msg.body.text,
      });

      // 调用 LLM
      const response = streamText({
        model: openai("gpt-5"),
        messages: c.state.messages,
      });

      // 实时事件广播给所有连接客户端
      for await (const delta of response.textStream) {
        c.broadcast("token", delta);
      }

      c.state.messages.push({
        role: "assistant",
        content: await response.text,
      });
    }
  },
});
```

**客户端连接**

```typescript
// 连接到 Actor
const agent = client.agent.getOrCreate("agent-123").connect();

// 监听实时事件
agent.on("token", (delta) => process.stdout.write(delta));

// 发送消息到 Actor
await agent.queue.send("how many r's in strawberry?");
```

---

## §4 技术架构

### 4.1 系统架构

Rivet 由以下核心组件构成：

```
┌─────────────────────────────────────────────────────────────┐
│                      RivetKit                              │
│  TypeScript Client  │  Rust Client  │  Python Client       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Rivet Engine (Rust)                      │
│  ┌─────────┐  ┌───────────┐  ┌────────┐  ┌────────┐    │
│  │ Pegboard │  │  Gasoline  │  │  Guard  │  │  Epoxy   │    │
│  │ Actor   │  │ Durable   │  │ Traffic │  │ Multi-  │    │
│  │orchestr.│  │ Execution │  │ Routing │  │ region  │    │
│  │         │  │ Engine   │  │ Proxy   │  │ KV Store │    │
│  └─────────┘  └───────────┘  └────────┘  └────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Postgres │  │ File    │  │Founda-   │
        │          │  │ System  │  │tionDB    │
        └──────────┘  └──────────┘  └──────────┘
```

### 4.2 核心子模块

| 模块 | 说明 |
|------|------|
| **Pegboard** | Actor 编排和网络通信 |
| **Gasoline** | 持久化执行引擎 |
| **Guard** | 流量路由代理 |
| **Epoxy** | 多区域 KV 存储（EPaxos 算法）|

### 4.3 仓库结构

| 目录 | 说明 |
|------|------|
| `rivetkit-typescript` | TypeScript 客户端和服务端库 |
| `rivetkit-rust` | Rust 客户端（实验性）|
| `rivetkit-python` | Python 客户端（实验性）|
| `engine` | Rust 编排引擎 |
| `frontend` | Dashboard Inspector |
| `website` | rivet.dev 网站源码 |
| `examples` | 示例项目 |
| `self-host/k8s` | Kubernetes 自托管配置 |

---

## §5 性能对比

### 5.1 与传统基础设施对比

| 指标 | Rivet Actor | Kubernetes Pod | Virtual Machine |
|------|-------------|----------------|-----------------|
| **冷启动** | ~20ms | ~6s | ~30s |
| **每实例内存** | ~0.6KB | ~50MB | ~512MB |
| **空闲成本** | $0 | ~$85/月（集群）| ~$5/月 |
| **水平扩展** | 无限 | ~5k 节点 | 手动 |
| **多区域** | 全球边缘 | 1 区域 | 1 区域 |

### 5.2 与状态存储对比

| 指标 | Rivet Actor | Redis | Postgres |
|------|-------------|-------|----------|
| **读取延迟** | 0ms | ~1ms | ~5ms |

**优势总结**：
- 比 Kubernetes/VM 启动快 **300-1500 倍**
- 内存占用比 Kubernetes **小 83,000 倍**
- 读取延迟比 Redis 更低（内存直读）

---

## §6 快速开始

### 6.1 使用 Coding Agent（推荐）

Rivet 提供了 AI Coding Agent 技能，可以直接让 Agent 创建示例和集成项目：

```bash
npx skills add rivet-dev/skills
```

这适用于 Claude Code、Cursor、Windsurf 等 AI 编码工具。

### 6.2 从零开始

**安装依赖**

```bash
npm install rivetkit
# 或
bun add rivetkit
```

**支持的运行时和框架**

| 运行时 | 框架 |
|--------|------|
| **Node.js** | Express, Hono, Elysia, tRPC |
| **Bun** | 同 Node.js |
| **Deno** | 原生支持 |
| **Cloudflare Workers** | Workers 运行时 |

### 6.3 基本使用

```typescript
import { actor, client } from "rivetkit";

// 定义 Actor
const myActor = actor({
  state: {
    count: 0,
  },
  run: async (c) => {
    for await (const msg of c.queue.iter()) {
      c.state.count += 1;
      console.log(`Count: ${c.state.count}`);
    }
  },
});

// 创建客户端
const cli = client({
  token: process.env.RIVET_TOKEN!,
});

// 获取或创建 Actor
const actor = cli.actor.getOrCreate("my-actor").connect();

// 发送消息
await actor.queue.send("increment");
```

---

## §7 核心功能详解

### 7.1 内存状态

Rivet Actor 的状态存储在内存中，支持即时读写：

```typescript
state: {
  // 任意 TypeScript 类型
  user: { id: string, name: string } | null,
  messages: Message[],
  cache: Map<string, any>,
}
```

**持久化选项**

| 选项 | 说明 |
|------|------|
| **SQLite（默认）** | 自动持久化到 SQLite |
| **自选数据库** | 连接外部 Postgres、FoundationDB 等 |

### 7.2 WebSocket 实时通信

```typescript
// 广播消息给所有连接客户端
c.broadcast("token", delta);

// 客户端监听
agent.on("token", (delta) => {
  console.log("Received:", delta);
});
```

### 7.3 Workflows（工作流）

```typescript
const workflowActor = actor({
  state: { steps: [], result: null },
  run: async (c) => {
    for await (const step of c.workflow.steps()) {
      // 执行步骤
      const result = await processStep(step);
      // 检查点持久化
      c.state.steps.push({ ...step, result });
    }
  },
});
```

### 7.4 Queues（消息队列）

```typescript
// 发送持久化消息
await actor.queue.send({ type: "process", data: input });

// 接收消息
for await (const msg of actor.queue.iter()) {
  console.log("Received:", msg.body);
}
```

### 7.5 Scheduling（定时调度）

```typescript
// 设置定时任务
c.scheduler.cron("*/5 * * * *", async () => {
  await cleanupOldData();
});

// 延迟执行
c.scheduler.delay(60_000, async () => {
  await sendReminder();
});
```

---

## §8 使用场景

### 8.1 AI Agent

每个 AI Agent 作为独立的 Actor 运行：

- 持久化上下文和记忆
- 调度工具调用
- 多 Agent 协调

```typescript
const agentActor = actor({
  state: {
    context: [] as Message[],
    tools: [] as Tool[],
  },
  run: async (c) => {
    for await (const task of c.queue.iter()) {
      // 调用 LLM
      const response = await llm.call(c.state.context);
      // 执行工具
      for (const toolCall of response.toolCalls) {
        const result = await executeTool(toolCall);
        c.state.context.push(result);
      }
    }
  },
});
```

### 8.2 沙箱编排

协调多个沙箱会话、队列工作和清理：

```typescript
const workspaceActor = actor({
  state: {
    sandboxes: new Map(),
    queue: [] as Task[],
  },
  run: async (c) => {
    // 协调多个沙箱
    for await (const task of c.queue.iter()) {
      const sandbox = await createSandbox();
      c.state.sandboxes.set(task.id, sandbox);
      // 处理完成后清理
      c.scheduler.delay(30 * 60_000, () => {
        sandbox.terminate();
        c.state.sandboxes.delete(task.id);
      });
    }
  },
});
```

### 8.3 多人协作文档

每个文档是一个 Actor，向所有连接用户广播变更：

```typescript
const docActor = actor({
  state: {
    content: "",
    users: new Set<string>(),
  },
  run: async (c) => {
    for await (const change of c.queue.iter()) {
      c.state.content = applyChange(c.state.content, change);
      // 广播给所有用户
      c.broadcast("change", {
        content: c.state.content,
        user: change.user,
      });
    }
  },
});
```

### 8.4 聊天应用

每个房间或会话一个 Actor：

- 内存状态
- 持久化历史
- 实时消息传递

### 8.5 多租户数据库

每个租户一个 Actor：

- 低延迟内存读取
- 持久化租户数据

---

## §9 部署选项

### 9.1 选项对比

| 选项 | 说明 | 适用场景 |
|------|------|----------|
| **Just a Library** | npm install 后本地运行，无服务器 | 开发调试 |
| **Self-Host** | Docker 或 Rust 二进制，支持 Postgres/FoundationDB | 企业部署 |
| **Rivet Cloud** | 全托管，全球边缘网络 | 生产环境 |

### 9.2 Just a Library（开发）

```bash
npm install rivetkit
```

Actor 在开发进程中运行，无需基础设施。

### 9.3 Self-Host（自托管）

```bash
# Docker 部署
docker run -p 6420:6420 rivetdev/engine

# 使用 Postgres
docker run -p 6420:6420 \
  -e DATABASE_URL=postgres://user:pass@host:5432/rivet \
  rivetdev/engine
```

### 9.4 Rivet Cloud（云托管）

- 全托管服务
- 全球边缘网络
- 连接现有云（Vercel、Railway、AWS）

### 9.5 自托管优势

| 优势 | 说明 |
|------|------|
| **企业部署** | 满足企业安全合规需求 |
| **云可移植性** | 避免供应商锁定 |
| **数据主权** | 数据存储在自己的基础设施 |

---

## §10 内置可观测性

### 10.1 Rivet Inspector

Dashboard 提供强大的调试和监控工具：

| 功能 | 说明 |
|------|------|
| **SQLite Viewer** | 实时浏览和查询 Actor 的 SQLite 数据库 |
| **Workflow State** | 检查工作流进度、步骤和重试 |
| **Event Monitoring** | 跟踪每个状态变更和操作 |
| **REPL** | 调用操作、订阅事件、直接与代码交互 |

### 10.2 日志集成

Rivet 支持 Pino 日志：

```typescript
import { logger } from "rivetkit";

logger.info("Actor started");
logger.error("Error processing", { error });
```

---

## §11 集成生态

### 11.1 基础设施

| 平台 | 说明 |
|------|------|
| **Vercel** | Edge Functions 部署 |
| **Railway** | 快速部署 |
| **AWS** | EC2、ECS、EKS |
| **Docker** | 自托管 |

### 11.2 框架

| 框架 | 说明 |
|------|------|
| **React** | 前端客户端 |
| **Next.js** | SSR 支持 |
| **Hono** | 轻量级框架 |
| **Express** | Node.js 框架 |
| **tRPC** | 类型安全 API |

### 11.3 工具

| 工具 | 说明 |
|------|------|
| **Vitest** | 测试框架 |
| **Pino** | 日志库 |
| **AI SDK** | AI 模型集成 |
| **OpenAPI** | API 文档生成 |
| **AsyncAPI** | 异步 API 文档 |

---

## §12 最佳实践

### 12.1 Actor 设计原则

| 原则 | 说明 |
|------|------|
| **单一职责** | 每个 Actor 只负责一个功能 |
| **状态最小化** | 只在状态中存储必要数据 |
| **消息驱动** | 通过队列而非直接调用 |

### 12.2 性能优化

| 实践 | 说明 |
|------|------|
| **批量操作** | 合并多次小操作为批量 |
| **缓存策略** | 使用内存缓存热点数据 |
| **懒加载** | 按需加载大状态 |

### 12.3 安全建议

| 实践 | 说明 |
|------|------|
| **输入验证** | 验证所有队列消息 |
| **限流** | 使用 Rate Limiting 防止滥用 |
| **隔离存储** | 不同租户使用不同持久化后端 |

---

## §13 常见问题

### Q1：Rivet 和 Cloudflare Durable Objects 有什么区别？

| 特性 | Rivet | Cloudflare Durable Objects |
|------|-------|-------------------------|
| **语言** | TypeScript/Rust/Python | JavaScript/TypeScript |
| **数据库** | SQLite/Postgres/FoundationDB | KV storage |
| **全球分布** | 多区域 KV（EPaxos）| 单区域 |
| **开源** | Apache 2.0 | 专有 |

### Q2：Rivet 和 Temporal 有什么区别？

| 特性 | Rivet | Temporal |
|------|-------|--------|
| **模型** | Actor | Workflow/Activity |
| **状态** | 内存+持久化 | External |
| **适用场景** | Agent/协作 | 后端工作流 |

### Q3：什么时候应该使用 Rivet？

- 构建需要持久状态的 AI Agent
- 多人实时协作应用
- 需要低延迟状态访问的多租户系统
- 需要长期运行的任务和调度

### Q4：什么时候不应该使用 Rivet？

- 无状态微服务（用普通函数即可）
- 极高吞吐量临时任务（用队列服务）
- 强一致性事务（用传统数据库）

### Q5：支持哪些数据库后端？

| 数据库 | 状态 | 说明 |
|--------|------|------|
| **SQLite** | ✅ 默认 | 开箱即用 |
| **Postgres** | ✅ 支持 | 自托管推荐 |
| **FoundationDB** | ✅ 支持 | 大规模部署 |

### Q6：如何调试 Rivet 应用？

使用 Rivet Inspector Dashboard：
- 浏览 SQLite 数据库
- 检查 Workflow 状态
- 监控事件流
- 使用 REPL 直接交互

---

## §14 总结

### 14.1 核心优势

| 优势 | 说明 |
|------|------|
| **极低延迟** | 0ms 读取（内存直读）|
| **极速冷启动** | ~20ms（比 K8s 快 300 倍）|
| **超低内存** | ~0.6KB/实例（比 K8s 小 83,000 倍）|
| **零空闲成本** | 空闲时不消耗资源 |
| **多语言 SDK** | TypeScript/Rust/Python |
| **开源** | Apache 2.0 |

### 14.2 适用场景

| 场景 | 推荐指数 |
|------|----------|
| AI Agent | ⭐⭐⭐⭐⭐ |
| 多人协作 | ⭐⭐⭐⭐⭐ |
| 实时应用 | ⭐⭐⭐⭐⭐ |
| 多租户系统 | ⭐⭐⭐⭐ |
| 后端工作流 | ⭐⭐⭐ |

### 14.3 项目信息

- Stars：5.3k
- Forks：163
- 贡献者：25 人
- 最新版本：2.1.10 (2026-03-26)
- 许可证：Apache-2.0

### 14.4 相关资源

| 资源 | 链接 |
|------|------|
| 官方网站 | https://www.rivet.dev |
| GitHub | https://github.com/rivet-dev/rivet |
| Discord | https://www.rivet.dev/discord |
| Twitter | @rivet_dev |
| 文档 | https://www.rivet.dev/docs |
| Changelog | https://www.rivet.dev/changelog |

---

*文档版本 1.0 | 撰写日期：2026-03-31 | 基于 v2.1.10 (2026-03-26) | Stars: 5.3k ⭐*