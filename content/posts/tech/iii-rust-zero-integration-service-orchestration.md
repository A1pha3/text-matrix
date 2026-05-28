---
title: "iii：Rust 运行时实现零集成的服务编排"
date: "2026-05-28T10:35:00+08:00"
slug: "iii-rust-zero-integration-service-orchestration"
aliases:
  - "/posts/iii-real-time-service-orchestration-guide/"
description: "iii 是一个以 Rust 实现的实时服务编排运行时，通过 Worker、Function、Trigger 三大原语实现零集成互通，适合需要动态扩展能力的微服务与 AI Agent 系统。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "AI Agent", "微服务", "服务编排", "后端开发"]
---

# iii：Rust 运行时实现零集成的服务编排

## 项目信息

| 项目 | 信息 |
|------|------|
| **仓库** | [iii-hq/iii](https://github.com/iii-hq/iii) |
| **Star** | 16,907 ⭐ |
| **语言** | Rust |
| **许可证** | ELv2（引擎）/ Apache 2.0（SDK） |
| **Docker** | `iiidev/iii` |

## 痛点

现代后端服务在写第一行业务逻辑之前，就要面对：

- 队列系统如何集成？
- Cron 定时任务谁来触发？
- HTTP 端点怎么暴露？
- 状态管理用什么方案？
- 可观测性谁来管？
- AI Agent 如何接入？

每个维度通常都有独立的工具和集成方案，**iii 的核心理念是：把这些全部压缩到一个共享运行时刻（shared runtime）中，让集成数量降为零。**

## 三大原语

iii 的整个心智模型只有三个概念：

### 1. Worker（工作者）

Worker 是注册到 iii 引擎的进程。TypeScript API 服务是 Worker，Python 数据管道是 Worker，Rust 微服务也是 Worker。Worker 可以创建其他 Worker，所以 **AI Agent 可以在系统运行时动态扩展能力**。

```bash
iii worker add queue
iii worker add agent
iii worker add sandbox
iii worker add <anything>
```

### 2. Function（函数）

Function 是工作的原子单位，有稳定的标识符（如 `content::classify`、`orders::validate`）。它接收输入，执行工作，返回输出。所有 Function 存在于 Worker 内部。

### 3. Trigger（触发器）

Trigger 是触发 Function 运行的任何事件。Trigger 可以是：

- 直接函数调用
- HTTP 端点
- Cron 定时调度
- 队列订阅
- 状态变更
- 流事件

Trigger 是声明式的：Worker 定义“此函数在此事件发生时运行”，iii 负责路由、序列化和投递。

## 工作原理

```
Worker 注册 → 注册 Trigger/Function → iii 引擎广播catalog
                                              ↓
其他 Worker 发现 → 立即可调用 → 调用结果可追踪
```

每个 Worker 加入实时目录（live catalog）。其他所有 Worker 都会收到通知并可以立即调用它。整个过程**无需任何集成配置**。

## AI Agent 场景

iii 特别适合 AI Agent 场景：

> 当一个任务需要系统不具备的能力时，Agent 可以直接添加一个 Worker，发现它的 Function，调用它，并追踪发生了什么，而开发者使用的也是同一个接口。

这意味着 Agent 和人类开发者使用完全相同的接口，天然实现了人机协作。

## 多语言 SDK

| 语言 | 包管理 |
|------|--------|
| TypeScript | `npm install iii-sdk` |
| Python | `pip install iii-sdk` |
| Rust | `cargo add iii-sdk` |
| Docker | `docker pull iiidev/iii` |

## 访问 Workers 目录

iii 官方维护了一个公开的 Workers 目录：[workers.iii.dev](https://workers.iii.dev/)，可以直接浏览可用能力。

## 结语

iii 用 Rust 实现了一个极简但强大的服务编排运行时。Worker/Function/Trigger 三大原语将过去需要大量集成配置的工作压缩为几行声明。AI Agent 可以在运行时动态扩展系统，而人类开发者与 Agent 使用完全相同的接口。

---

> **钳岳星君曰**：Rust 实现 zero-integration 这个理念很有意思。传统中间件思维是加层，而 iii 的思路是消层，让服务天然在一个运行时中互相发现。对于构建 AI Agent 系统来说，这种动态扩展能力尤其有价值。

*相关链接：[GitHub 仓库](https://github.com/iii-hq/iii) | [Workers 目录](https://workers.iii.dev/) | [npm](https://www.npmjs.com/package/iii-sdk) | [PyPI](https://pypi.org/project/iii-sdk/)*