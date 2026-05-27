---
title: "iii：实时服务编排框架，让微服务像搭积木一样简单"
date: 2026-05-28T03:30:00+08:00
draft: false
categories:
  - 架构
  - 服务编排
tags:
  - 微服务
  - 实时编排
  - Workers
  - TypeScript
  - Python
  - Rust
description: "iii是一个实时服务编排框架，通过Worker/Function/Trigger三个原语，让团队可以轻松地组合、扩展、观察服务。支持TypeScript、Python、Rust多语言SDK，可在运行时动态添加Worker，构建自我进化的AI Agent系统。"
---

# iii：实时服务编排框架，让微服务像搭积木一样简单

在后端开发中，每当引入一个新组件——无论是消息队列、Agent框架还是可观测性工具——都需要面对同一个问题：**如何让它们彼此协作？** 传统方案是靠无数的手工集成代码。iii 的答案是：**让服务自己说出来、连起来。**

<!--more-->

## 项目概述

**iii**（发音：eye-eye-eye）是 [iii-hq](https://github.com/iii-hq/iii) 开发的开源实时服务编排框架。它的核心理念是极简化：系统中的每一个功能单元（Worker）通过三个原语——**Worker**、**Function**、**Trigger**——注册到 iii 引擎，引擎自动维护一个**实时服务目录**，任何其他 Worker 可以立即发现、调用、追踪这些功能。

## 三个原语，一切从简

iii 的设计异常精简，只需要理解三个概念：

### Worker（工作者）

Worker 是 iii 系统中的基本构建单元。任何可以注册到引擎并向外提供功能的东西都是 Worker：

```bash
iii worker add queue      # 添加一个队列 Worker
iii worker add agent      # 添加一个 Agent Worker
iii worker add sandbox    # 添加一个沙箱 Worker
iii worker add <anything> # 任何功能都可以变成 Worker
```

一个 TypeScript API 服务是一个 Worker。一个 Python 数据管道是一个 Worker。一个 Rust 微服务也是一个 Worker。Workers 甚至可以在运行时动态创建其他 Worker，这意味着 **Agent 可以自我扩展系统**。

### Function（函数）

Function 是具体的工作单元，拥有稳定的标识符：

```
content::classify
orders::validate
users::authenticate
```

每个 Function 接收输入、执行工作、返回输出。Functions 存在于 Workers 内部。

### Trigger（触发器）

Trigger 是让 Function 运行的"开关"。iii 支持多种触发类型：

| Trigger类型 | 说明 |
|------------|------|
| **直接调用** | 显式调用某个 Function |
| **HTTP端点** | REST API 触发 |
| **Cron调度** | 定时任务触发 |
| **队列订阅** | 消息队列事件触发 |
| **状态变更** | 数据状态变化触发 |
| **流事件** | 实时数据流事件触发 |

## 前后对比

### 传统方案

引入新组件的痛苦：
- 新可观测性工具 → 数不清的集成配置
- 新 Agent 框架 → 单独的重试配置、追踪配置、timeout配置
- 新消息队列 → 供应商评估、采购，加上数周的集成工作

### iii 方案

```bash
iii worker add observability   # 一行命令
iii worker add queue          # 一行命令
# 完成！系统自动发现、追踪、可调用
```

三个原语统一了一切——编排、观察、扩展——全部通过同一个接口。

## 技术特点

### 多语言 SDK

iii 提供了多语言 SDK，开发者可以用自己熟悉的语言构建 Worker：

| 语言 | 包管理 | 安装 |
|------|--------|------|
| TypeScript/JavaScript | npm | `npm install iii-sdk` |
| Python | PyPI | `pip install iii-sdk` |
| Rust | crates.io | `cargo add iii-sdk` |

同时提供官方 Docker 镜像，开箱即用。

### 零集成共享运行时

iii 的核心创新在于**共享运行时**。传统微服务需要为每个新组件单独集成，而 iii 的 Workers 共享同一个引擎上下文：

- 一个 Worker 注册，其他所有 Worker **立即知道**它的 Function
- 可以**直接调用**，无需服务发现配置
- 引擎自动处理**序列化、路由、交付**
- 每一次调用都有**完整的追踪记录**

### Agent 原生支持

iii 设计之初就考虑了 AI Agent 场景。当一个任务需要系统不具备的能力时，Agent 可以：

1. `iii worker add <capability>` 添加一个 Worker
2. 发现它的 Functions（通过实时目录）
3. 调用它们
4. 查看完整的执行追踪

整个过程对 Agent 暴露的是同一个接口——正是开发者日常使用的那个接口。

### 完全可观测

iii 不需要额外的可观测性集成。引擎天然记录：
- 每一个 Function 的调用链路
- 输入/输出数据
- 执行时间和状态

打开追踪窗口，你就能看到完整的请求流——从 Trigger 到 Function 到返回。

## 快速上手

### 安装 iii

```bash
# macOS / Linux
curl -fsSL https://get.iii.dev | bash

# 或者通过 npm
npm install -g iii

# 验证安装
iii --version
```

### 初始化项目

```bash
iii project init myapp
cd myapp
iii
```

项目启动后，引擎运行在本地，Workers 注册进来，你可以在 `http://localhost:3000` 查看服务目录。

### 添加第一个 Worker

```bash
iii worker add queue
iii worker add agent
iii worker add sandbox
```

在 iii.dev 的 [Workers 目录](https://workers.iii.dev/) 可以浏览所有已发布的 Workers。

### 代码示例：创建一个 Function Worker

**TypeScript**

```typescript
import { Worker } from 'iii-sdk';

const worker = new Worker({
  name: 'content-processor',
  triggers: ['http'],
  functions: {
    'content::classify': async ({ input }) => {
      // 内容分类逻辑
      return { category: 'tech', confidence: 0.92 };
    },
    'content::summarize': async ({ input }) => {
      // 内容摘要逻辑
      return { summary: '这是一篇关于...' };
    }
  }
});

worker.start();
```

**Python**

```python
from iiisdk import Worker

worker = Worker(
    name='content-processor',
    triggers=['http'],
    functions={
        'content::classify': lambda input: {'category': 'tech'},
        'content::summarize': lambda input: {'summary': '这是一篇关于...'}
    }
)

worker.start()
```

### 触发 Function

```bash
iii call content::classify --input "这篇关于AI大模型的技术文章..."
```

或者通过 HTTP：

```bash
curl -X POST http://localhost:3000/fn/content::classify \
  -d '{"input": "这篇关于AI大模型的技术文章..."}'
```

## 适用场景

- 🏗 **平台团队**：构建可复用的 Worker 库，供应用团队直接集成
- 🤖 **AI Agent 开发**：Agent 运行时需要动态扩展系统能力
- 🔧 **后端重构**：将单体应用拆分为 Workers，渐进式迁移
- 📊 **数据管道**：Python 数据处理逻辑与 API 服务共享同一目录
- 🔔 **可观测性集成**：一个命令添加新的观测能力，无需手工配置

## 与其他方案的对比

| 特性 | iii | 传统微服务 | 服务网格 |
|------|-----|-----------|---------|
| 组件添加 | `iii worker add` | 手动集成 | .sidecar 配置 |
| 服务发现 | 自动 | 需要服务注册中心 | Sidecar 代理 |
| 追踪能力 | 内置 | 需单独接入 | 需单独接入 |
| Agent 友好 | ✅ 原生 | ❌ | ❌ |
| 多语言支持 | ✅ TS/Py/Rust | ✅ | ✅ |
| 运行时扩展 | ✅ | ❌ | ❌ |

## 结语

iii 的价值主张非常清晰：**用三个原语替代无数的一次性集成**。无论是人工开发者还是 AI Agent，都通过同一个接口与系统交互——发现能力、调用功能、追踪结果。这不是又一个"更智能的框架"，而是一种让服务自我说明、自我连接、自我观测的**新心智模型**。

---

⭐ 项目地址：[iii-hq/iii](https://github.com/iii-hq/iii)  
🌐 官方网站：[iii.dev](https://iii.dev)