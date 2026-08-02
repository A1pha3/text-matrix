---
title: "iii：Rust 运行时实现零集成的服务编排"
date: "2026-05-28T10:35:00+08:00"
slug: "iii-rust-zero-integration-service-orchestration"
aliases:
  - "/posts/iii-real-time-service-orchestration-guide/"
description: "iii 是一个以 Rust 实现的实时服务编排运行时，通过 Worker、Function、Trigger 三大原语将服务发现、调用、编排压缩到共享运行时刻，无需任何集成配置。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "AI Agent", "微服务"]
---

# iii：Rust 运行时实现零集成的服务编排

iii 解决一个很具体的问题：在写第一行业务逻辑之前，后端服务要先把队列、Cron、HTTP 端点、状态管理、可观测性、AI Agent 接入这些基础设施集成一遍。每个维度有独立的工具和接入方案，集成成本随服务数量线性增长。

iii 的解法是**共享运行时刻**（shared runtime）：所有服务注册到同一个 iii 引擎，引擎负责发现、路由、调度。新服务加入时，运行时目录自动广播，其他服务立即可调用——不需要修改配置、重启进程、注册端点。

项目仓库：[iii-hq/iii](https://github.com/iii-hq/iii)，16,907 Stars，Rust 实现，引擎层 ELv2 许可证，SDK 层 Apache 2.0。

## 三大原语

iii 的心智模型只有三个概念：Worker、Function、Trigger。

### Worker

Worker 是注册到 iii 引擎的进程。TypeScript API 服务是 Worker，Python 数据管道是 Worker，Rust 微服务也是 Worker。Worker 可以创建其他 Worker，所以 AI Agent 可以在运行时动态扩展能力，不需要事先定义好所有服务。

```bash
iii worker add queue
iii worker add agent
iii worker add sandbox
```

每个 Worker 加入实时目录（live catalog），包含它提供的 Function 列表和调用签名。新 Worker 加入时，目录广播给所有已注册的 Worker。

### Function

Function 是工作的原子单位，有稳定的标识符（如 `content::classify`、`orders::validate`）。它接收输入，执行工作，返回输出。Function 存在于 Worker 内部，Worker 可以注册任意数量的 Function。

```typescript
// TypeScript Worker 示例
import { createWorker } from 'iii-sdk';

const worker = createWorker('content-service');

worker.register('content::classify', async (input: { text: string }) => {
  const category = await classify(input.text);
  return { category, confidence: 0.95 };
});

await worker.start();
```

### Trigger

Trigger 是触发 Function 运行的任何事件。Trigger 是声明式的——Worker 定义"此函数在此事件发生时运行"，iii 负责路由、序列化和投递。

Trigger 的类型包括：

- **直接调用**：其他 Worker 按 Function 标识符调用
- **HTTP 端点**：自动为每个 Function 生成 HTTP 入口
- **Cron 调度**：按 cron 表达式定时触发
- **队列订阅**：从指定队列拉取消息触发
- **状态变更**：监听某个键的值变化触发
- **流事件**：订阅流式数据源

```typescript
// 声明式 Trigger 示例
worker.register('orders::validate', async (input) => {
  // ...
}, {
  trigger: [
    { type: 'http', path: '/orders/validate' },
    { type: 'queue', source: 'orders.pending' },
  ]
});
```

## 运行时架构

```
Worker A 注册 → 引擎广播 catalog
                    ↓
Worker B 收到通知 → 发现 Worker A 的 Function
                    → 通过引擎调用 Function A
                    → 结果可追踪
```

引擎的核心职责：

1. **目录管理**：维护所有 Worker 的 live catalog，包含 Function 签名、状态、健康检查
2. **消息路由**：根据 Function 标识符将调用请求投递到正确的 Worker
3. **序列化/反序列化**：跨语言调用时自动处理数据格式转换
4. **调用追踪**：每个调用生成 trace ID，支持跨 Worker 的链路追踪
5. **错误处理**：调用超时、重试、熔断由引擎统一管理

Worker 间不直接通信，所有调用通过引擎中转。这带来一个好处：调用方不需要知道目标 Worker 的地址、端口、协议版本——只按 Function 名字调用即可。引擎负责把调用路由到正确的 Worker，无论它在同一进程、不同容器还是不同机器。

## 与 Temporal 的异同

iii 常被拿来和 Temporal 比较，二者都做编排，但分层不同：

| 维度 | iii | Temporal |
|------|-----|----------|
| 抽象层级 | 共享运行时 + 函数调用 | Workflow + Activity 状态机 |
| 服务发现 | 内置（live catalog 自动广播） | 外部（依赖 DNS/服务网格） |
| 持久化 | 可选（状态变更可持久化） | 强制（Event Sourcing） |
| 调用模型 | 同步/异步函数调用 | 异步 Workflow 执行 |
| 多语言支持 | TypeScript/Python/Rust | Go/Java/Python/TypeScript |
| 适用场景 | 轻量服务编排、动态扩展 | 长时间运行、强一致性 Workflow |

iii 的定位更轻——不做 Event Sourcing，不要求 Workflow 定义与执行分离。它的核心价值是"零集成"：你不需要在代码里引入服务发现客户端、配置消息队列、注册 HTTP 路由。这些由引擎兜底。

代价是 iii 不适合需要强一致性保证的长时间 Workflow（如支付结算、多步事务补偿）。这类场景 Temporal 的 Event Sourcing + 确定性重放是更成熟的选择。

## AI Agent 场景

iii 的 Worker 动态注册能力对 AI Agent 场景特别直接：

> 当一个任务需要系统不具备的能力时，Agent 可以直接添加一个 Worker，发现它的 Function，调用它，并追踪发生了什么。Agent 和人类开发者使用完全相同的接口。

这意味着 Agent 不需要额外的适配层或工具注册流程。Agent 接受到任务后，如果发现需要的能力不存在，可以通过引擎创建一个新的 Worker 进程，新 Worker 注册自己的 Function 到 catalog，Agent 立即就能调用。整个过程不需要重启、不需要修改配置、不需要人工介入。

## 多语言 SDK

| 语言 | 安装 |
|------|------|
| TypeScript | `npm install iii-sdk` |
| Python | `pip install iii-sdk` |
| Rust | `cargo add iii-sdk` |
| Docker | `docker pull iiidev/iii` |

SDK 封装了 Worker 注册、Function 声明、Trigger 配置、引擎通信协议。Worker 可以用任意 SDK 语言编写，引擎统一做跨语言序列化。

## 部署方式

```bash
# 启动引擎
docker run -d --name iii-engine -p 7000:7000 iiidev/iii

# 注册 Worker
iii worker add my-service --script ./worker.ts
```

引擎支持单节点和集群模式。集群模式下，Worker 可分布在多台机器上，引擎负责跨节点路由。官方维护了一个公开的 [Workers 目录](https://workers.iii.dev/)，可浏览社区贡献的可用能力。

## 适用边界

### 适合

- 微服务数量多且频繁变动的系统
- 需要动态扩展能力的 AI Agent 平台
- 跨语言服务编排（TypeScript + Python + Rust 混用）
- 初创团队或小团队，希望减少基础设施集成负担

### 不适合

- 需要强一致性保证的长时间 Workflow
- 已经重度依赖 Temporal/Cadence 的系统
- 对延迟极端敏感的场景（引擎中转增加一次网络跳转）
- 安全隔离要求高的多租户环境（引擎共享运行时）

---

*相关链接：[GitHub 仓库](https://github.com/iii-hq/iii) | [Workers 目录](https://workers.iii.dev/) | [npm](https://www.npmjs.com/package/iii-sdk) | [PyPI](https://pypi.org/project/iii-sdk/)*