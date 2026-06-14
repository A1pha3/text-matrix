---
title: "Hermes WebUI：自托管AI Agent的网页界面完全指南"
date: "2026-05-31T20:07:02+08:00"
slug: "hermes-webui-self-hosted-agent-web-interface-guide"
description: "Hermes WebUI是Hermes Agent的轻量级网页界面，三栏布局、无需构建步骤、原生Python实现。本文详细解析其核心能力、与CLI的完整功能对等性、安装方式、与OpenClaw/Claude Code的横向对比，以及自托管AI Agent网页化访问的最佳实践。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Hermes", "WebUI", "自托管", "NousResearch"]
---

# Hermes WebUI：自托管 AI Agent 的网页界面完全指南

Hermes WebUI 是一个专为 [Hermes Agent](https://hermes-agent.nousresearch.com/) 设计的网页界面，可以在浏览器中完成 CLI 上的所有操作。它不需要任何构建步骤、不依赖前端框架、不需要打包工具——核心只需 Python 和原生 JavaScript。对于已经在服务器上运行 Hermes Agent 的用户来说，这是从任何设备安全访问 Agent 最便捷的方案。

## 项目概览

| 指标 | 数值 |
|------|------|
| 仓库 | [nesquena/hermes-webui](https://github.com/nesquena/hermes-webui) |
| Stars | 9,563 |
| Forks | 1,323 |
| 主要语言 | Python |
| 许可证 | MIT |

## 为什么值得看

大多数 AI Agent 工具都重度依赖终端或桌面客户端，一旦离开本地环境就很难继续使用上下文。Hermes WebUI 的关键价值在于：**将一个功能完整的自托管 Agent 变成可以在任何浏览器访问的网页应用**，而不引入额外的复杂度或供应商绑定。

## 核心能力

### 三栏布局

WebUI 采用经典的三栏设计：

- **左侧边栏**：会话管理和导航
- **中央聊天区**：与 Agent 对话的核心区域
- **右侧工作区文件浏览器**：直接浏览 Agent 可见的文件系统

Model（模型）、profile（配置）和 workspace（工作区）控制项统一收敛在底部的 **Composer Footer** 中——无论在哪个区域，始终可见。

### Hermes Control Center

所有设置和会话工具都集中在 Hermes Control Center 中，通过侧边栏底部的快捷启动器唤起。它等价于 CLI 中的完整配置体系，不需要用户记忆任何命令行参数。

### Token 用量圆环

右下角的圆形 context ring 实时展示 token 使用量，让用户对上下文消耗有直观感知，避免在长对话中不知不觉超出上下文窗口。

### 与 CLI 的完整功能对等

根据官方说明，WebUI 实现了与 Hermes CLI 的 **1:1 功能对等**（Full parity）：CLI 上能做的事，WebUI 全部可以完成。这意味着 Agent 的 memory、skills、scheduled jobs 等能力在网页端完全可用。

### 自托管 + SSH 隧道访问

默认安装下 WebUI 绑定在 `localhost`，通过 SSH 隧道从远程安全访问。本质上是一个在自有服务器上运行的网页服务，天然支持内网穿透和零信任访问模型。

### 会话预填充（Prefill）

WebUI 支持在新建浏览器会话时附加上下文预填充。支持的场景包括：从 Joplin、Obsidian、Notion、Notion 等第三方笔记系统拉取项目上下文，或从本地 `llm-wiki` 中注入检索指引。

预填充支持两种方式：

1. **静态 JSON 文件**：通过 `prefill_messages_file` 或 `HERMES_PREFILL_MESSAGES_FILE` 环境变量指定
2. **动态脚本**：通过 `webui_prefill_messages_script` 执行任意 Python 脚本获取最新上下文，超时 5 秒，输出上限 256 KiB

### Gateway 桥接模式

对于已运行 Hermes Gateway/API Server 的高级部署，WebUI 可以将浏览器对话路由到 Gateway 运行时，而不是 WebUI 自带的 in-process 运行时：

```bash
HERMES_WEBUI_CHAT_BACKEND=gateway \
HERMES_WEBUI_GATEWAY_BASE_URL=http://127.0.0.1:8642 \
HERMES_WEBUI_GATEWAY_API_KEY=... \
./ctl.sh restart
```

这使得同一个 Agent 实例可以同时服务于 WebUI 和多个消息平台，共享同一套 memory 和 tools。

## 安装方式

### 方式一：bootstrap 脚本（推荐）

```bash
git clone https://github.com/nesquena/hermes-webui.git hermes-webui
cd hermes-webui
python3 bootstrap.py
```

Bootstrap 脚本会自动：
1. 检测 Hermes Agent 是否已安装，缺失时执行官方安装脚本
2. 查找或创建包含 WebUI 依赖的 Python 环境
3. 启动 Web 服务并等待 `/health` 就绪
4. 打开浏览器进入首次运行引导向导
5. 若传 `--no-browser` 则静默启动

### 方式二：Docker 单容器

```bash
git clone https://github.com/nesquena/hermes-webui
cd hermes-webui
cp .env.docker.example .env
docker compose up -d
# 访问 http://localhost:8787
```

开启密码保护（暴露在外网时必须）：

```bash
echo "HERMES_WEBUI_PASSWORD=change-me-to-something-strong" >> .env
docker compose up -d --force-recreate
```

### 方式三：Docker 多容器

- **双容器**（Agent 和 WebUI 隔离）：`docker compose -f docker-compose.two-container.yml up -d`
- **三容器**（Agent + Dashboard + WebUI）：`docker compose -f docker-compose.three-container.yml up -d`

### 方式四：原生 Windows（社区支持）

Windows 原生安装需要 Python 3.11+，通过 PowerShell 创建 venv 并安装依赖。WSL2 不是必须项。具体步骤见 [@markwang2658/hermes-windows-native](https://github.com/markwang2658/hermes-windows-native)。

## 与同类工具横向对比

| 能力 | OpenClaw | Claude Code | Codex CLI | OpenCode | Hermes |
|------|----------|-------------|----------|----------|--------|
| 持久化记忆（自动） | Yes | Partial | Partial | Partial | **Yes** |
| 自托管定时任务 | Yes | No | No | No | **Yes** |
| 消息应用接入 | Yes (15+) | Partial | No | No | **Yes (10+)** |
| 自托管 Web UI | Dashboard only | No | No | Yes | **Yes** |
| 自我改进 Skills | Partial | No | No | No | **Yes** |
| Python/ML 生态 | No | No | No | No | **Yes** |
| 模型无关 | Yes | No（仅 Claude） | Yes | Yes | **Yes** |
| 开源 | Yes（MIT） | No | Yes | Yes | **Yes** |

**核心差异**：Hermes 的自我改进 Skills（从经验中自动编写和保存 skills）是其独有能力；与 OpenClaw 相比，Hermes 在跨版本稳定性上表现更佳，且原生运行在 Python 生态中，对于已有 Python 工具链的团队更加友好。

## 适用边界

**适合**：
- 已在服务器上运行 Hermes Agent，希望从多设备访问同一 Agent 上下文的用户
- 需要在团队内部署统一 AI 工作助手的场景
- 希望用网页界面替代终端操作的运维场景

**不适合**：
- 不希望维护自托管服务的用户（直接使用 Claude Code/ChatGPT 等更省心）
- 需要多租户隔离的严肃企业场景（目前 WebUI 缺乏权限模型）
- Windows 用户（需要 WSL2 或社区维护的非官方方案）

## 快速验证清单

如果你用 AI 助手帮你安装或调试 Hermes WebUI，可以让助手先阅读 [docs/onboarding-agent-checklist.md](https://github.com/nesquena/hermes-webui/blob/master/docs/onboarding-agent-checklist.md)，它包含了安装检查、常见失败模式和处理步骤的完整清单。

## 结语

Hermes WebUI 解决了自托管 AI Agent 的"最后一公里"问题——让一个功能强大的服务器端 Agent 在不损失任何能力的前提下，变成可以在任何设备浏览器中使用的网页应用。对于已经在运行 Hermes Agent 的开发者来说，这个 WebUI 是当前市面上实现最完整、体验最顺畅的网页化方案之一。
