---
title: "IronClaw：安全私密个人 AI 助手完全指南"
slug: "ironclaw-secure-ai-assistant-guide"
date: 2026-03-31T14:35:00+08:00
categories: ["技术笔记"]
tags: ["IronClaw", "AI助手", "安全隐私", "WASM", "Rust", "PostgreSQL"]
description: "全面解析 IronClaw：11.2k Stars 的安全私密个人 AI 助手。支持 WASM 沙箱安全隔离、多渠道（REPL/Telegram/Slack）、混合搜索、Rust 编写的开源项目。"
---

# IronClaw：安全私密个人 AI 助手完全指南

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 IronClaw 的核心定位与安全理念
- ✅ 掌握 IronClaw 的技术架构与核心组件
- ✅ 熟练部署 IronClaw（从源码编译 + Docker）
- ✅ 熟练使用 REPL、Web Gateway、Telegram 等多种渠道
- ✅ 配置多种 LLM Provider（Anthropic、OpenAI、GitHub Copilot、MiniMax 等）
- ✅ 理解 WASM Sandbox 安全机制
- ✅ 使用 Routines 实现定时任务和自动化
- ✅ 掌握 Hybrid Search 混合搜索的使用
- ✅ 理解 IronClaw 与 OpenClaw 的区别

---

## §2 项目概述

### 2.1 什么是 IronClaw？

**IronClaw**（官方仓库：[nearai/ironclaw](https://github.com/nearai/ironclaw)）是一款**安全私密的个人 AI 助手**，核心理念是"Your data stays yours"。

**官方描述**：

> IronClaw is built on a simple principle: your AI assistant should work for you, not against you. In a world where AI systems are increasingly opaque about data handling and aligned with corporate interests, IronClaw takes a different approach: Your data stays yours - All information is stored locally, encrypted, and never leaves your control. Transparency by design - Open source, auditable, no hidden telemetry or data harvesting. Self-expanding capabilities - Build new tools on the fly without waiting for vendor updates. Defense in depth - Multiple security layers protect against prompt injection and data exfiltration.

**四大核心理念**：

| 理念 | 说明 |
|------|------|
| **Your data stays yours** | 所有数据本地存储、加密，永不离开用户控制 |
| **Transparency by design** | 开源可审计，无隐藏遥测或数据采集 |
| **Self-expanding capabilities** | 随时构建新工具，无需等待供应商更新 |
| **Defense in depth** | 多层安全防护，抵御提示注入和数据泄露 |

### 2.2 核心数据

```
Stars:     11,200 (11.2k)
Forks:     1,300 (1.3k)
Watchers:  78
贡献者:   108 人
提交数:   857 次
发布版本:  26 个
最新版本:  v0.23.0 (2026-03-27)
许可证:   Apache-2.0 OR MIT
主要语言: Rust 90.5%, Shell 2.8%, JavaScript 2.8%, Python 2.5%
```

### 2.3 与 OpenClaw 的关系

IronClaw 是受 [OpenClaw](https://github.com/openclaw/openclaw) 启发、用 **Rust 语言重写的实现**，专注于隐私和安全。

**主要区别**：

| 特性 | IronClaw (Rust) | OpenClaw (TypeScript) |
|------|-----------------|----------------------|
| 语言 | Rust（原生性能、内存安全） | TypeScript |
| 沙箱 | WASM 沙箱（轻量、能力强） | Docker |
| 数据库 | PostgreSQL（生产级） | SQLite |
| 安全设计 | 安全优先，多层防御 | 安全优先 |
| 部署 | 单二进制文件 | Node.js 运行时 |

### 2.4 技术栈

| 组件 | 技术 |
|------|------|
| 核心语言 | Rust 1.85+ |
| 数据库 | PostgreSQL 15+ (with pgvector) |
| 沙箱隔离 | WebAssembly (WASM) |
| 容器隔离 | Docker |
| LLM 支持 | Anthropic、OpenAI、GitHub Copilot、Gemini、MiniMax、Mistral、Ollama、OpenRouter 等 |

---

## §3 核心特性详解

### 3.1 安全优先（Security First）

**WASM 沙箱**

所有不受信任的工具都在隔离的 WebAssembly 容器中运行：

| 安全机制 | 说明 |
|----------|------|
| **基于能力的权限** | HTTP、Secrets、工具调用需显式授权 |
| **端点白名单** | HTTP 请求仅限批准的 host/路径 |
| **凭证注入** | 凭证在主机边界注入，不暴露给 WASM 代码 |
| **泄露检测** | 扫描请求/响应中的凭证泄露尝试 |
| **速率限制** | 每个工具的请求限制防止滥用 |
| **资源限制** | 内存、CPU、执行时间约束 |

```
WASM ──► Allowlist ──► Leak Scan ──► Credential ──► Execute ──► Leak Scan ──► Response
        (request)    Injector         (response)
```

**提示注入防御（Prompt Injection Defense）**

外部内容通过多层安全处理：

1. 基于模式的注入尝试检测
2. 内容清理和转义
3. 策略规则（阻止/警告/审查/清理）
4. 工具输出包装，确保 LLM 上下文安全注入

**数据保护**

- 所有数据存储在本地 PostgreSQL 数据库
- 凭证使用 AES-256-GCM 加密
- 无遥测、分析或数据共享
- 完整的工具执行审计日志

### 3.2 随时可用（Always Available）

**多渠道支持**

| 渠道 | 说明 |
|------|------|
| **REPL** | 交互式命令行 |
| **HTTP Webhooks** | HTTP 接口调用 |
| **WASM Channels** | Telegram、Slack 等消息平台 |
| **Web Gateway** | 浏览器 UI（SSE + WebSocket 流式） |

**Docker 沙箱**

- 隔离的容器执行
- 每个 job 的 token
- Orchestrator/Worker 模式

**自动化引擎**

- **Routines**: Cron 调度、事件触发、Webhook 处理器
- **Heartbeat System**: 主动后台执行监控和维护任务
- **Parallel Jobs**: 隔离上下文中并发处理多个请求
- **Self-repair**: 自动检测和恢复卡住的操作

### 3.3 自我扩展（Self-Expanding）

**动态工具构建**

描述你需要的工具，IronClaw 会将其构建为 WASM 工具。

**MCP 协议**

连接到 Model Context Protocol 服务器，获取额外能力。

**插件架构**

无需重启，即可插入新的 WASM 工具和渠道。

### 3.4 持久化记忆（Persistent Memory）

**混合搜索**

全文 + 向量搜索，使用 Reciprocal Rank Fusion。

**工作区文件系统**

灵活的基于路径的存储，用于笔记、日志和上下文。

**身份文件**

跨会话保持一致的人格和偏好。

---

## §4 技术架构深度解析

### 4.1 系统架构图

```
┌────────────────────────────────────────────────────────────────┐
│                         Channels                              │
│  ┌──────┐  ┌──────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ REPL │  │ HTTP │  │WASM Channels│  │ Web Gateway│       │
│  │      │  │      │  │(Telegram,   │  │ (SSE + WS) │       │
│  │      │  │      │  │ Slack)       │  │             │       │
│  └──┬───┘  └──┬───┘  └──────┬──────┘  └─────────────┘       │
│     │         │              │                                │
└─────┼─────────┼──────────────┼────────────────────────────────┘
      │         │              │
      ▼         ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Loop                               │
│              Intent routing (命令/查询/任务)                 │
└────┬──────────────────┬────────────────────────────────────┘
     │                  │
     ▼                  ▼
┌───────────┐    ┌──────────────────┐
│ Scheduler │    │  Routines Engine │
│(parallel  │    │(cron, event, wh)│
│  jobs)    │    │                  │
└─────┬─────┘    └────────┬─────────┘
      │                   │
      ▼                   ▼
┌─────────────┐    ┌──────────────────────────────────────┐
│Local Workers│    │         Orchestrator                  │
│(in-proc)   │    │  ┌───────────────┐                    │
│            │    │  │ Docker Sandbox │                   │
│            │    │  │  ┌───────────┐ │                   │
│            │    │  │  │Worker / CC│ │                   │
│            │    │  │  └───────────┘ │                   │
│            │    │  └───────────────┘                    │
└─────────────┘    └──────────────────────────────────────┘
      │                   │
      ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                     Tool Registry                           │
│              Built-in, MCP, WASM                            │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 核心组件详解

| 组件 | 功能 |
|------|------|
| **Agent Loop** | 主消息处理和任务协调 |
| **Router** | 分类用户意图（命令/查询/任务）|
| **Scheduler** | 管理并行任务执行和优先级 |
| **Worker** | 使用 LLM 推理和工具调用执行任务 |
| **Orchestrator** | 容器生命周期、LLM 代理、per-job 认证 |
| **Web Gateway** | 浏览器 UI（聊天、记忆、任务、日志、扩展、Routines）|
| **Routines Engine** | 调度（cron）和响应（事件、Webhook）后台任务 |
| **Workspace** | 带混合搜索的持久化记忆 |
| **Safety Layer** | 提示注入防御和内容清理 |

### 4.3 目录结构

| 目录 | 说明 |
|------|------|
| `.claude` | Claude 代理配置 |
| `.github` | GitHub Actions CI/CD |
| `benches` | 性能基准测试 |
| `channels-src` | WASM 渠道源码（Telegram、Slack 等）|
| `crates` | 核心 Rust crates |
| `deploy` | 部署配置 |
| `docker` | Docker 相关文件 |
| `docs` | 文档 |
| `fuzz` | 模糊测试 |
| `migrations` | 数据库迁移 |
| `registry` | 工具注册表 |
| `scripts` | 辅助脚本 |
| `skills` | 技能定义 |
| `src` | 主源码 |
| `tests` | 测试 |
| `tools-src` | 工具源码 |
| `wit` | WASM 接口类型 |
| `wix` | Windows 安装器 |

---

## §5 安装与配置

### 5.1 环境要求

| 要求 | 版本 |
|------|------|
| Rust | 1.85+ |
| PostgreSQL | 15+ (with pgvector extension) |
| NEAR AI 账号 | 用于认证（通过设置向导处理）|

### 5.2 数据库设置

```bash
# 创建数据库
createdb ironclaw

# 启用 pgvector
psql ironclaw -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 5.3 安装方式

**方式一：下载预构建版本**

访问 [Releases 页面](https://github.com/nearai/ironclaw/releases/) 下载最新版本。

**方式二：从源码构建**

```bash
# 克隆仓库
git clone https://github.com/nearai/ironclaw
cd ironclaw

# 构建
cargo build --release

# 二进制文件位于 target/release/ironclaw
```

### 5.4 配置向导

首次设置时，运行设置向导配置 IronClaw：

```bash
ironclaw onboard
```

向导会处理：
1. 数据库连接配置
2. NEAR AI 认证（通过浏览器 OAuth）
3. 凭证加密（使用系统密钥链）

### 5.5 LLM Provider 配置

IronClaw 默认使用 NEAR AI，但支持多种 LLM Provider。

**内置 Provider**

- Anthropic
- OpenAI
- GitHub Copilot
- Google Gemini
- MiniMax
- Mistral
- Ollama（本地）

**OpenAI 兼容服务**

- OpenRouter（300+ 模型）
- Together AI
- Fireworks AI
- 自托管服务器（vLLM、LiteLLM）

**配置示例**

```bash
# MiniMax（内置，204K 上下文）
LLM_BACKEND=minimax
MINIMAX_API_KEY=...

# OpenAI 兼容端点
LLM_BACKEND=openai_compatible
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY=sk-or-...
LLM_MODEL=anthropic/claude-sonnet-4
```

详细配置请参考 [docs/LLM_PROVIDERS.md](https://github.com/nearai/ironclaw/blob/staging/docs/LLM_PROVIDERS.md)。

---

## §6 使用说明

### 6.1 REPL 交互

```bash
# 首次设置（配置数据库、认证等）
ironclaw onboard

# 启动交互式 REPL
cargo run

# 带调试日志
RUST_LOG=ironclaw=debug cargo run
```

### 6.2 Web Gateway

Web Gateway 提供浏览器 UI，支持：

- 实时聊天（SSE/WebSocket 流式）
- 记忆管理
- 任务监控
- 日志查看
- 扩展管理
- Routines 配置

### 6.3 Telegram 渠道

设置和 DM 配对请参考 [docs/TELEGRAM_SETUP.md](https://github.com/nearai/ironclaw/blob/staging/docs/TELEGRAM_SETUP.md)。

### 6.4 开发命令

```bash
# 格式化代码
cargo fmt

# Lint
cargo clippy --all --benches --tests --examples --all-features

# 运行测试
createdb ironclaw_test
cargo test

# 运行特定测试
cargo test test_name
```

---

## §7 安全机制详解

### 7.1 WASM 沙箱工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    WASM Sandboxed Tool                      │
│  1. 请求进入 → Allowlist 检查                             │
│  2. 通过 → Leak Scan（检测凭证泄露）                       │
│  3. 通过 → Credential Injector（在边界注入凭证）          │
│  4. 执行工具                                               │
│  5. 响应 → Leak Scan（再次检测）                         │
│  6. 返回结果                                               │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 提示注入防御

外部内容通过多层处理：

| 层级 | 机制 |
|------|------|
| **模式检测** | 基于模式的注入尝试检测 |
| **内容清理** | 内容清理和转义 |
| **策略规则** | 严重级别（Block/Warn/Review/Sanitize）|
| **输出包装** | 工具输出安全包装用于 LLM 上下文注入 |

### 7.3 凭证保护

- 凭证在主机边界注入
- WASM 代码永远看不到凭证
- 泄露检测扫描请求和响应

---

## §8 Routines 自动化

### 8.1 Routines 引擎

Routines 引擎支持：

- **Cron 调度**: 定时任务
- **事件触发**: 响应系统事件
- **Webhook 处理器**: HTTP 回调

### 8.2 Heartbeat System

主动后台执行监控和维护任务。

### 8.3 Self-repair

自动检测和恢复卡住的操作。

---

## §9 Hybrid Search 混合搜索

### 9.1 工作原理

Hybrid Search 结合：

- **全文搜索**: 精确关键词匹配
- **向量搜索**: 语义相似度

使用 **Reciprocal Rank Fusion** 融合两种搜索结果。

### 9.2 Workspace 文件系统

基于路径的灵活存储：

- 笔记
- 日志
- 上下文

### 9.3 身份文件

跨会话保持一致的人格和偏好设置。

---

## §10 最佳实践

### 10.1 部署建议

**生产环境部署**

1. 使用 Docker 进行容器化部署
2. 配置 PostgreSQL 数据库（带 pgvector）
3. 设置环境变量
4. 启用 HTTPS
5. 配置备份策略

**开发环境**

```bash
# 格式化代码
cargo fmt

# Lint 检查
cargo clippy --all --benches --tests --examples --all-features

# 运行测试
cargo test
```

### 10.2 安全建议

- 保持 Rust 和依赖更新
- 使用强密码和密钥管理
- 定期审计日志
- 限制网络暴露
- 使用 WASM 沙箱隔离不受信任的工具

### 10.3 性能优化

- 使用 Docker 沙箱隔离重操作
- 配置适当的超时和资源限制
- 使用 PostgreSQL 连接池
- 监控内存和 CPU 使用

---

## §11 常见问题

### Q1：IronClaw 和 OpenClaw 有什么区别？

IronClaw 是用 Rust 重写的版本，专注于：
- 更强的安全机制（WASM 沙箱）
- 生产级数据库（PostgreSQL）
- 原生性能和内存安全
- 单二进制部署

### Q2：数据存储在哪里？

所有数据存储在本地 PostgreSQL 数据库，使用 AES-256-GCM 加密凭证，无远程遥测。

### Q3：支持哪些 LLM？

支持多种 Provider：
- 内置：Anthropic、OpenAI、GitHub Copilot、Gemini、MiniMax、Mistral、Ollama
- OpenAI 兼容：OpenRouter、Together AI、Fireworks AI、vLLM、LiteLLM

### Q4：如何扩展工具？

支持两种方式：
- **MCP 协议**: 连接 Model Context Protocol 服务器
- **WASM 插件**: 构建新的 WASM 工具

### Q5：是否支持中文？

支持多语言 README：
- English
- 简体中文
- Русский
- 日本語

### Q6：许可证是什么？

双许可证：
- Apache License 2.0
- MIT License

二选一使用。

---

## §12 总结

### 12.1 核心优势

| 优势 | 说明 |
|------|------|
| **安全优先** | WASM 沙箱、凭证保护、提示注入防御 |
| **隐私保护** | 本地存储、加密、无遥测 |
| **自我扩展** | 动态构建工具、MCP 协议、插件架构 |
| **多渠道** | REPL、HTTP、Telegram、Slack、Web Gateway |
| **持久记忆** | Hybrid Search、工作区文件系统、身份文件 |
| **自动化** | Routines、Heartbeat、Self-repair |
| **Rust 性能** | 原生速度、内存安全、单二进制 |

### 12.2 相关资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/nearai/ironclaw |
| 官方网站 | https://www.ironclaw.com |
| Telegram | @ironclawAI |
| Reddit | r/ironclawAI |
| Releases | https://github.com/nearai/ironclaw/releases |
| LLM Provider 文档 | docs/LLM_PROVIDERS.md |
| Telegram 设置 | docs/TELEGRAM_SETUP.md |

### 12.3 项目信息

- 最新版本：v0.23.0 (2026-03-27)
- Stars：11.2k
- Forks：1.3k
- 贡献者：108 人
- 许可证：Apache-2.0 OR MIT

---

*文档版本 1.0 | 撰写日期：2026-03-31 | 基于 v0.23.0 (2026-03-27) | Stars: 11.2k ⭐*