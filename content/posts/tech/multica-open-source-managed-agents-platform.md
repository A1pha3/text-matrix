---
title: "Multica：把 AI 代码代理变成真正的队友"
date: "2026-05-21T20:16:13+08:00"
slug: "multica-open-source-managed-agents-platform"
description: "Multica 是一个开源托管代理平台，让 AI 编程代理（Claude Code、Codex 等）变成真正的团队成员，支持任务分配、进度追踪、技能复用和多代理协作。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Claude Code", "多代理", "MCP", "开源"]
---

# Multica：把 AI 代码代理变成真正的队友

![Multica: humans and agents, side by side](docs/assets/banner.jpg)

**开源托管代理平台，把编程代理变成真正的团队成员。**

[![CI](https://github.com/multica-ai/multica/actions/workflows/ci.yml/badge.svg)](https://github.com/multica-ai/multica/actions/workflows/ci.yml)
[![GitHub stars](https://img.shields.io/github/stars/multica-ai/multica?style=flat)](https://github.com/multica-ai/multica/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 背景：为什么需要 Multica

大型语言模型（LLM）驱动下的 AI 编程代理（Claude Code、Codex、Copilot、Cursor Agent 等）已经能独立完成大量代码任务。然而，当你想让多个代理协同工作时，问题来了：

- 代理之间没有统一的任务分配机制
- 无法追踪每个代理的进度和阻塞
- 跨代理的知识和技能无法复用
- 多代理和人类之间的协作缺乏基础设施

**Multica** 解决了这些问题。它是一个开源的托管代理平台，让你可以像分配任务给人类同事一样，把 issue 分配给 AI 代理——代理会接取任务、写代码、报告阻塞、自动更新状态。

> 名字由来：**Mul**tiplexed **I**nformation and **C**omputing **A**gent。致敬 1960 年代的多路复用操作系统 Multics（Unix 就是从 Multics 简化而来）。Multica 认为，在 AI 时代，"多路复用"正在重新定义：一个人类工程师 + 一群 AI 代理，应该能像二十个人的团队一样高效运转。

---

## 核心特性

### 1. 代理即队友

在 Multica 中，每个 AI 代理都是一个"队友"。你可以在 issue 中 @ 某个代理，代理会：

- **接取任务**：自动认领分配给它的 issue
- **报告进度**：通过评论更新任务状态
- **报告阻塞**：当遇到问题时主动提出
- **提交代码**：独立完成开发工作

代理不再是"跑一次就没了"的单次任务，而是一个持续参与团队协作的成员。

### 2. Squad（编队）：多代理协作

Squad 功能允许你把多个代理（和人类）组成一个小组，由一个"领导代理"负责协调：

```
@FrontendTeam → 领导代理决定谁来做
              → 前端代理A / 前端代理B / 设计代理
```

当一个新的 issue 分配给 Squad 时，领导代理会决定哪个成员最适合处理，避免了任务分配的混乱。

支持的代理：**Claude Code、Codex、GitHub Copilot CLI、OpenClaw、OpenCode、Hermes、 Gemini、Pi、Cursor Agent、Kimi、Kiro CLI** 等。

### 3. 可复用技能（Skills）

Multica 的技能系统让每个解决过的问题都变成可复用的团队资产：

- 部署流程 → 技能
- 数据库迁移 → 技能
- 代码审查 → 技能

当一个新代理需要执行类似任务时，直接调用已有技能，不需要重复编写提示词。

### 4. 实时进度流

通过 WebSocket 提供实时进度流：

```
代理A：正在处理 #234 用户认证模块...
代理B：已完成 #123，提交了 PR #456
领导代理：任务 #789 被阻塞，需要人工介入
```

### 5. 自托管与云端

- **自托管**：完全开源，可以部署在自己的服务器上
- **云端**：multica.ai 提供托管服务，开箱即用

---

## 架构设计

### 系统架构

Multica 的核心设计围绕**代理生命周期管理**：

```
┌─────────────────────────────────────────────────┐
│                  Multica Core                    │
├─────────────────────────────────────────────────┤
│  Task Queue  │  Agent Registry  │  Skill Store │
│  (任务队列)    │  (代理注册表)      │  (技能仓库)    │
├─────────────────────────────────────────────────┤
│         WebSocket Server (实时进度流)             │
├─────────────────────────────────────────────────┤
│  Agent Adapter Layer (多代理适配)                 │
│  Claude Code / Codex / Copilot / OpenClaw ...   │
└─────────────────────────────────────────────────┘
```

**核心模块：**

1. **Agent Registry**：管理所有注册的代理，维护其状态和能力描述
2. **Task Queue**：统一的任务队列，支持任务的创建、分配、执行、完成、失败等生命周期
3. **Skill Store**：存储和管理可复用的技能模板
4. **WebSocket Server**：实时推送代理进度更新
5. **Agent Adapter Layer**：不同代理（Claude Code、Codex 等）的统一适配接口

### 任务生命周期

```
创建 → 入队(enqueue) → 认领(claim) → 开始(start) → 完成(complete) / 失败(fail)
                                    ↓
                                阻塞(blocked) → 解阻 → 继续
```

每个状态变化都会通过 WebSocket 实时通知客户端。

---

## 安装与使用

### 安装

```bash
# 通过 npm 安装
npm install -g @multica-ai/cli

# 或者使用 Docker
docker run -d -p 3000:3000 multica-ai/multica
```

### 快速开始

```bash
# 初始化项目
multica init my-project

# 启动 Multica 服务
multica start

# 在浏览器打开 http://localhost:3000
```

### 注册代理

```bash
# 注册 Claude Code 代理
multica agent add claude-code --api-key your-key

# 注册 Codex 代理
multica agent add codex --api-key your-key
```

### 分配任务

通过 Web 界面或 CLI：

```bash
# 通过 CLI 分配任务
multica issue create --title "实现用户登录" --assign @claude-agent

# 通过 @Squad 分配
multica issue create --title "重构前端组件" --assign @FrontendTeam
```

---

## Web 界面

Multica 提供了一个现代化的看板界面，与 GitHub Issue 无缝集成：

- **Board 视图**：类似 GitHub Projects 的看板，看每个代理正在做什么
- **Issue 列表**：创建、编辑、分配 issue
- **Activity 时间线**：每个代理的实时活动日志
- **Squad 管理**：创建和管理多代理编队

---

## 与主流工具的集成

### Claude Code 集成

```bash
# 安装 Claude Code Multica 插件
claude code plugin install multica
```

然后在 `claude_desktop_config.json` 中配置：

```json
{
  "mcpServers": {
    "multica": {
      "command": "npx",
      "args": ["-y", "@multica-ai/mcp@latest"]
    }
  }
}
```

### GitHub 集成

Multica 可以直接从 GitHub Issue 获取任务，并在完成时自动提交 PR 和更新 Issue 状态。

---

## Squad 模式详解

Squad 是 Multica 最强大的功能之一。想象一个典型的大型任务：

```
用户需求：重构电商网站的前端
涉及模块：商品列表、购物车、支付、用户中心
```

如果只用一个代理，需要把所有上下文都给它，容易达到 token 上限。如果拆成多个代理，又需要手动协调。

**Squad 方案：**

1. 创建一个 `@EcommerceFrontendTeam` Squad
2. 设置一个领导代理（如 Claude Code）作为协调者
3. 领导代理下辖多个专业代理：商品代理、购物车代理、支付代理、用户代理
4. 把任务分配给 Squad，领导代理自动决定谁来处理

```bash
# 创建 Squad
multica squad create EcommerceFrontendTeam --leader claude-code

# 添加成员
multica squad add-member EcommerceFrontendTeam --agent product-agent --role "商品模块"
multica squad add-member EcommerceFrontendTeam --agent cart-agent --role "购物车模块"
```

---

## 自托管部署

### Docker Compose 部署

```yaml
version: '3.8'
services:
  multica:
    image: multica-ai/multica:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/multica
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接串 | `sqlite://multica.db` |
| `REDIS_URL` | Redis 连接串 | 内置内存 |
| `PORT` | 服务端口 | `3000` |
| `SECRET_KEY` | 会话密钥 | 必填 |
| `AGENTS_MAX_CONCURRENT` | 最大并发代理数 | `10` |

---

## 与 LangChain/AutoGen 的对比

| 特性 | Multica | LangChain | AutoGen |
|------|---------|-----------|---------|
| **定位** | 托管代理平台 | LLM 应用开发框架 | 多代理对话框架 |
| **任务管理** | 内置 + GitHub 集成 | 需自行实现 | 需自行实现 |
| **技能复用** | 内置技能市场 | 需自行实现 | 需自行实现 |
| **Web 界面** | 有，开箱即用 | 无 | 无 |
| **自托管** | 支持 | 支持 | 支持 |
| **GitHub Issue 集成** | 有 | 需自行实现 | 需自行实现 |

Multica 的核心差异在于：**它是一个完整的团队协作平台**，而不是一个开发框架。即使你不懂 LLM，只要你会用 GitHub Issue，就能让 AI 代理帮你干活。

---

## 适用场景

- **需要多个 AI 代理协同的中大型项目**（代码重构、大型功能开发）
- **希望把 AI 代理纳入现有开发流程**（GitHub Issue → 代理执行 → PR）
- **团队希望建立 AI 代理资产库**（技能复用、经验积累）
- **研究多代理协作的研究者**（Squad 模式提供了开箱即用的实验环境）

---

## 结论

Multica 解决了一个实际问题：当 AI 代理从"单次任务执行者"升级为"团队成员"时，我们需要一个完整的基础设施来支撑这种协作。它不是又一个 AI 编程工具，而是一个让 AI 代理融入团队协作流程的**平台层**。

如果你正在使用 Claude Code、Codex 或其他 AI 编程代理，Multica 提供了一个让它们协同工作的框架，值得尝试。

---

**GitHub 地址**：[https://github.com/multica-ai/multica](https://github.com/multica-ai/multica)

**官网**：[https://multica.ai](https://multica.ai)
