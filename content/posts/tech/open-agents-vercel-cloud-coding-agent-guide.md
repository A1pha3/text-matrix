---
title: "Open Agents：Vercel 开源的云端 AI 编码智能体模板"
date: "2026-05-08T03:11:04+08:00"
slug: "open-agents-vercel-cloud-coding-agent-guide"
description: "Open Agents 是 Vercel 开源的云端 AI 编码智能体参考模板，基于 Web -> Agent Workflow -> Sandbox VM 三层架构设计。本文详细解析其核心架构、代码执行隔离机制、GitHub 集成方式和快速部署方法。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Vercel", "云端执行", "Sandbox", "编码智能体"]
---

## 学习目标

读完这篇文章后，你应该能够：

1. 理解 Open Agents 的三层架构设计（Web、Agent Workflow、Sandbox VM）及其设计动机。
2. 掌握 Open Agents 的核心架构决策：Agent 不运行在 Sandbox 内部，而是通过工具与 Sandbox 交互。
3. 能够基于官方模板在 Vercel 上完成一键部署，并配置 GitHub 集成。
4. 理解 Sandbox 的生命周期管理（休眠与恢复）机制以及其对 Agent 稳定性的影响。
5. 判断 Open Agents 适合哪些场景，以及如何基于该模板做二次开发。

---

## 一、项目概述

### 1.1 什么是 Open Agents

**Open Agents**（[vercel-labs/open-agents](https://github.com/vercel-labs/open-agents)，4.9k Stars）是 Vercel 团队开源的一个参考模板，用于在 Vercel 平台上构建和运行云端 AI 编码智能体（Background Coding Agents）。

官方地址：[https://open-agents.dev](https://open-agents.dev)

这不是一个"开箱即用"的产品，而是一个**架构参考实现**——它展示了如何在云端可靠地运行一个 AI 编码 Agent，包括 Web UI、Agent 运行时、代码执行沙箱和 GitHub 集成。Vercel 官方鼓励 fork 并根据需求自行修改。

### 1.2 核心问题：本地 Agent 的局限性

在 Open Agents 出现之前，主流的 AI 编码 Agent（如 Claude Code、Cursor AI）都是**本地运行**的。这意味着：

- Agent 执行依赖用户本地环境（文件系统、Shell、网络）
- Agent 运行与用户交互 session 绑定，无法在后台持续运行
- 用户电脑关机后 Agent 无法继续工作
- 无法轻松实现多 Agent 并行或长时间任务

Open Agents 的出发点是：**把 AI 编码 Agent 从本地搬到云端**，让它能够：

- 在后台持续运行，不依赖用户本地环境
- 通过 Web UI 与用户交互
- 利用 Vercel 的基础设施做弹性扩缩容
- 与 GitHub 等外部服务深度集成

---

## 二、架构解析

### 2.1 三层架构总览

Open Agents 采用经典的三层架构：

```
Web（用户界面） -> Agent Workflow（推理与决策） -> Sandbox VM（代码执行环境）
```

**第一层：Web**
负责用户认证、会话管理、聊天 UI 和流式响应展示。使用 Next.js 构建，部署在 Vercel Edge Network 上。

**第二层：Agent Workflow**
运行在 Vercel 的 Durable Objects 上，作为持久化的工作流引擎。它负责：
- 接收用户指令
- 调用 LLM 进行推理和决策
- 管理任务状态和执行计划
- 与 Sandbox 交互协调

**第三层：Sandbox VM**
独立的虚拟机环境，拥有自己的文件系统、Shell、Git 和开发服务器。Agent 通过工具调用（文件读取、编辑、Shell 命令等）操作 Sandbox，而不是直接运行在 VM 内。

### 2.2 核心架构决策：Agent 不在 Sandbox 内

这是整个项目最关键的设计决策，也是最容易让人困惑的地方。

大多数人会直觉地认为"运行代码的 Agent"应该直接在 VM 里执行。但 Open Agents 的做法是：

> Agent 运行在 Vercel 的 Durable Objects 上，Sandbox 是被 Agent 通过工具操作的独立环境。

两者的关系是**主从分离**：

| 组件 | 运行位置 | 生命周期 |
|------|---------|---------|
| Agent 运行时 | Vercel Durable Objects | 持久化，可休眠/恢复 |
| Sandbox VM | 独立 VM（隔离环境） | 按需创建，可休眠/恢复 |

这样做有几个重要优势：

1. **Agent 执行不绑定请求周期**：Vercel 的 Request-Response 模式只适合短任务，而 Agent 需要跨多个请求持续思考和工作
2. **Sandbox 可以独立扩缩**：Sandbox 是纯执行环境，不需要承载 Agent 逻辑，可以更灵活地管理资源
3. **模型和工具可以独立演进**：Sandbox 的具体实现（是 VM、Docker 还是其他）可以被替换，而不需要改动 Agent 逻辑

### 2.3 Sandbox 生命周期

Sandbox VM 支持**休眠（Hibernate）和恢复（Resume）**：

- 当 Sandbox 空闲一段时间后会自动进入休眠状态
- 再次需要执行代码时会被唤醒
- 休眠期间不占用计算资源

这使得长时间任务成为可能——Agent 可以发起一个需要数小时的任务，期间 Sandbox 多次休眠和恢复，而 Agent 状态保持不变。

---

## 三、快速部署

### 3.1 一键部署

Open Agents 支持直接通过 Vercel 一键部署：

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?project-name=open-agents&repository-name=open-agents&repository-url=https%3A%2F%2Fgithub.com%2Fvercel-labs%2Fopen-agents)

部署时需要配置以下环境变量：

| 变量 | 说明 |
|------|------|
| `POSTGRES_URL` | Neon 提供的 PostgreSQL 连接地址（可自动配置） |
| `BETTER_AUTH_SECRET` | 认证密钥（需手动生成） |
| `NEXT_PUBLIC_VERCEL_APP_CLIENT_ID` | Vercel OAuth 客户端 ID |
| `VERCEL_APP_CLIENT_SECRET` | Vercel OAuth 客户端密钥 |
| `NEXT_PUBLIC_GITHUB_CLIENT_ID` | GitHub OAuth 应用客户端 ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth 应用客户端密钥 |
| `GITHUB_APP_ID` | GitHub App ID（用于 GitHub 集成） |
| `GITHUB_APP_PRIVATE_KEY` | GitHub App 私钥 |

### 3.2 手动部署步骤

```bash
# 克隆仓库
git clone https://github.com/vercel-labs/open-agents.git
cd open-agents

# 安装依赖
npm install

# 复制环境变量模板
cp .env.example .env.local

# 填充必要的环境变量后启动
npm run dev
```

### 3.3 GitHub 集成配置

Open Agents 提供了与 GitHub 的深度集成，可以让 Agent 直接在 GitHub 仓库上工作。配置步骤：

1. 创建一个 GitHub OAuth App，填入 `GITHUB_CLIENT_ID` 和 `GITHUB_CLIENT_SECRET`
2. 创建一个 GitHub App，填入 `GITHUB_APP_ID` 和 `GITHUB_APP_PRIVATE_KEY`
3. 在 Vercel 上配置好上述环境变量

Agent 就可以代表用户操作 GitHub 仓库，创建 Branch、提交 PR 等。

---

## 四、使用场景与边界

### 4.1 适合的场景

- **需要长时间运行的代码任务**：Agent 在后台运行，不需要保持浏览器打开
- **团队共享的 AI 编码工具**：团队成员通过 Web UI 共享同一个 Agent 实例
- **需要与 GitHub 深度集成的自动化任务**：自动 Review PR、生成文档、修复 CI 问题
- **构建团队内部 AI 开发助手**：基于模板二次开发，构建自己的 AI 编码工具

### 4.2 不适合的场景

- **即时响应类任务**：Open Agents 的架构导致延迟较高，不适合需要毫秒级响应的场景
- **资源受限的小团队**：需要维护完整的 Vercel + Neon + GitHub App 基础设施
- **只是想用 AI 编码**：已经有 Claude Code、Cursor 等成熟方案，本地使用更简单直接

### 4.3 与现有方案的对比

| 维度 | Claude Code | Cursor AI | Open Agents |
|------|------------|----------|-------------|
| 运行位置 | 本地 | 本地 | 云端 |
| 后台运行 | ❌ | ❌ | ✅ |
| Web UI | ❌ | ❌ | ✅ |
| GitHub 集成 | 基础 | 基础 | 深度集成 |
| 定制化难度 | 低 | 低 | 高（需要理解架构） |
| 部署难度 | 无需部署 | 无需部署 | 需要配置云服务 |

---

## 五、总结

Open Agents 是一个架构参考实现而非开箱即用产品。它最核心的价值在于展示了**如何在云端可靠地运行需要持久状态的 AI 编码 Agent**，以及**如何让 Agent 通过工具模式与隔离的代码执行环境交互**。

如果你正在考虑构建自己的 AI 编码平台、需要让 Agent 在后台长时间运行、或者想研究云端 Agent 架构，Open Agents 是一个值得研究的模板。它的三层架构和 Agent-Sandbox 分离设计是当前云端 Agent 实践中的主流选择。

但如果你只是想在本地使用 AI 编程工具，Vercel 的这套方案可能过度设计了——直接使用 Claude Code 或 Cursor 等成熟产品体验会更好。

---

## 相关资源

- GitHub：[vercel-labs/open-agents](https://github.com/vercel-labs/open-agents)（4.9k Stars）
- 官网：[https://open-agents.dev](https://open-agents.dev)
- 部署文档：Vercel 平台上可直接 Fork 部署，参考仓库 README