---
title: "Free Claude Code：用开源代理让 Claude Code 调用自由"
date: "2026-04-28T19:39:53+08:00"
slug: "free-claude-code-anthropic-proxy"
description: "Free Claude Code 是一个开源的 Anthropic API 代理，允许用户通过 NVIDIA NIM、OpenRouter、DeepSeek、LM Studio、llama.cpp、Ollama 等后端自由调用 Claude Code，绕过官方付费限制。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Anthropic", "API Proxy", "OpenRouter", "开源"]
---

## 项目概览

Free Claude Code（简称 FCC）是 Alishahryar1 在 GitHub 上开源的 Anthropic API 代理项目，目前已经获得了 **16.9k Stars** 和 **2.4k Forks**，采用 MIT 开源许可证。该项目的主要目标是让用户能够通过 Claude Code CLI、VS Code 扩展、JetBrains ACP 插件或聊天机器人等方式，免费使用 Claude Code 的核心能力。

其核心原理是将 Claude Code 发出的 Anthropic Messages API 流量，路由到用户自选的后端提供商（NVIDIA NIM、OpenRouter、DeepSeek、LM Studio、llama.cpp、Ollama），而非必须使用 Anthropic 官方付费 API。用户可以在不改变 Claude Code 客户端使用习惯的前提下，自由选择免费、付费或本地部署的模型后端。

**核心能力一览：**

| 能力项 | 具体说明 |
|--------|----------|
| 代理能力 | Claude Code API 调用的透明代理，保持客户端协议稳定 |
| 提供商支持 | NVIDIA NIM、OpenRouter、DeepSeek、LM Studio、llama.cpp、Ollama（6 种） |
| 模型路由 | 按模型层级（Opus、Sonnet、Haiku）分别路由到不同提供商 |
| 协议兼容 | Streaming、Tool Use、Thinking/Reasoning Block 处理 |
| 远程接入 | 可选的 Discord 或 Telegram Bot 包装器 |
| 语音输入 | 可选的语音笔记转录（Whisper 或 NVIDIA NIM） |

## 核心问题与解决思路

Claude Code 是 Anthropic 官方推出的命令行编程助手，基于 Claude Opus 4.7 模型构建，能够理解代码库、读写文件、执行命令、调用工具，并以流式方式输出代码片段（Artifact）。它迅速走红，但随之而来的是一个核心限制：Claude Code 必须绑定 Anthropic 官方付费 API，费用按 Token 用量计算。这对于个人开发者、小团队或只是想尝鲜的用户来说，是一道不低的门槛。

Free Claude Code 试图解决的就是这个根本矛盾：如何在不改变 Claude Code 客户端体验的前提下，用更灵活的后端替代 Anthropic 官方 API？

它的解决思路可以归纳为四条设计原则：

**1. 保持客户端协议稳定，只替换传输层**

Claude Code 与服务端之间使用 Anthropic Messages API 协议进行通信。FCC 在本地启动一个 FastAPI 代理服务器（默认端口 8082），将 Claude Code 发出的请求拦截并转换为目标提供商的 API 格式，再将响应转换回 Claude Code 期望的格式。这个过程对 Claude Code 客户端是透明的——它不知道自己实际上在和一个第三方后端通信。

**2. 支持多种后端，不绑定任何一家**

FCC 支持 NVIDIA NIM（支持免费额度）、OpenRouter（聚合多种模型）、DeepSeek（价格低廉）、LM Studio（本地部署）、llama.cpp（本地部署）、Ollama（本地部署）六种后端。用户可以根据自己的需求（免费、便宜、本地隐私）自由选择。这种灵活性是 Anthropic 官方 API 做不到的。

**3. 支持模型层级路由，物尽其用**

Claude Code 在不同任务中会调用不同层级的模型（Opus、Sonnet、Haiku）。FCC 支持为每个层级配置不同的提供商，实现精细化的路由控制。例如，可以将 Opus 请求路由到 OpenRouter（高质量），将 Sonnet 路由到 DeepSeek（性价比），将 Haiku 路由到本地 Ollama（免费且快速）。

**4. 保持 Claude Code 的完整能力，不阉割**

Claude Code 的核心能力包括 Streaming 流式输出、Tool Use（读写文件、执行命令）、Thinking/Reasoning Block（思维链）。FCC 在各提供商之间进行了差异化的协议转换，确保这些能力在目标后端上尽可能完整地保留。

## 架构与关键机制

FCC 的技术架构分为三个主要层：客户端层、代理层、提供商层。

**整体架构图：**

```
┌──────────────────────────────────────────────────────────────────┐
│                        客户端层                                    │
│   Claude Code CLI / VS Code 扩展 / JetBrains ACP / 聊天机器人     │
└────────────────────────────┬─────────────────────────────────────┘
                             │ Anthropic Messages API
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                       代理层（本地 :8082）                        │
│                                                                  │
│   FastAPI Server                                                 │
│   ├── /v1/messages          ← Anthropic 兼容路由                  │
│   ├── /v1/messages/count_tokens                                     │
│   └── /v1/models                                                   │
│                                                                  │
│   ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│   │ Model       │  │ Provider     │  │ Request               │  │
│   │ Routing     │  │ Transports   │  │ Optimizations         │  │
│   │ (Opus/      │  │ (NIM/OpenAI/ │  │ (trivial probes       │  │
│   │  Sonnet/    │  │  Anthropic/  │  │  answered locally)    │  │
│   │  Haiku)     │  │  SSE)        │  │                       │  │
│   └─────────────┘  └──────────────┘  └───────────────────────┘  │
└────────────────────────────┬─────────────────────────────────────┘
                             │ Provider-specific Request/Stream Adapter
                             ▼
┌──────────────────────────────────────────────────────────────────┐
│                       提供商层                                    │
│   ┌────────────┐  ┌────────────┐  ┌────────┐  ┌────────────┐   │
│   │ NVIDIA NIM │  │ OpenRouter │  │DeepSeek│  │ LM Studio  │   │
│   │            │  │            │  │        │  │ llama.cpp  │   │
│   │            │  │            │  │        │  │ Ollama     │   │
│   └────────────┘  └────────────┘  └────────┘  └────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

**技术栈明细：**

| 层级 | 技术选型 |
|------|----------|
| 代理服务器 | FastAPI（Python 3.14+，ASGI） |
| 服务发现 | 环境变量（.env 配置） |
| 传输协议 | NVIDIA NIM（OpenAI Chat → Anthropic SSE 转换）、OpenRouter（原生 Anthropic Messages）、DeepSeek（原生 Anthropic Messages）、LM Studio（Anthropic Messages）、llama.cpp（Anthropic Messages）、Ollama（Anthropic Messages） |
| 可选集成 | Discord/Telegram Bot、Whisper（语音转录） |
| CLI 管理 | Python 包入口（uv/pip） |

**本地存储结构（~/.config/free-claude-code/）：**

```
~/.config/free-claude-code/
└── .env                    ← API Keys、Provider URLs、Routing 配置
```

FCC 通过 `fcc-init` 命令自动创建配置模板，配置文件使用 `uv` 管理依赖隔离。

## 安装与最小示例

**环境要求：**

- Claude Code（官方 CLI）
- uv（Python 包管理器，3.14+）
- Python 3.14+
- 至少一个受支持的 API 提供商

**安装步骤：**

```bash
# 1. 安装 uv（macOS/Linux）
curl -LsSf https://astral.sh/uv/install.sh | sh
uv self update
uv python install 3.14

# 2. 克隆仓库并配置
git clone https://github.com/Alishahryar1/free-claude-code.git
cd free-claude-code
cp .env.example .env

# 3. 编辑 .env，选择一个提供商（以 NVIDIA NIM 为例）
# NVIDIA_NIM_API_KEY="nvapi-your-key"
# MODEL="nvidia_nim/z-ai/glm4-7"
# ANTHROPIC_AUTH_TOKEN="freecc"

# 4. 启动代理
uv run uvicorn server:app --host 0.0.0.0 --port 8082
```

**包安装方式（替代步骤 2-4）：**

```bash
uv tool install git+https://github.com/Alishahryar1/free-claude-code.git
fcc-init              # 创建 ~/.config/free-claude-code/.env
free-claude-code      # 启动代理（默认 0.0.0.0:8082）
```

**启动 Claude Code：**

```bash
# PowerShell
$env:ANTHROPIC_AUTH_TOKEN="freecc"
$env:ANTHROPIC_BASE_URL="http://localhost:8082"
claude

# Bash
ANTHROPIC_AUTH_TOKEN="freecc" ANTHROPIC_BASE_URL="http://localhost:8082" claude
```

**VS Code 扩展配置：**

在 `settings.json` 中添加：

```json
"claudeCode.environmentVariables": [
  { "name": "ANTHROPIC_BASE_URL", "value": "http://localhost:8082" },
  { "name": "ANTHROPIC_AUTH_TOKEN", "value": "freecc" }
]
```

## 代码结构与模块拆解

**仓库结构一览：**

```
free-claude-code/
├── server.py              ← ASGI 入口（uvicorn server:app）
├── api/                   ← FastAPI 路由、服务层、路由逻辑、请求优化
│   ├── __init__.py
│   ├── routes.py          ← /v1/messages 等路由
│   ├── service.py         ← 请求路由分发核心逻辑
│   └── optimizations.py   ← 本地优化（trivia probes）
├── core/                  ← 共享的 Anthropic 协议辅助函数和 SSE 工具
│   ├── anthropic_helpers.py
│   └── sse_utils.py
├── providers/             ← 提供商传输层、注册表、限流
│   ├── __init__.py
│   ├── base.py            ← 传输层基类
│   ├── anthropic_messages.py    ← 原生 Anthropic Messages 传输（DeepSeek/Ollama 等）
│   ├── nim_transport.py         ← NVIDIA NIM 传输（OpenAI → Anthropic 转换）
│   ├── registry.py        ← 提供商注册表
│   └── rate_limit.py      ← 限流实现
├── messaging/              ← Discord/Telegram 适配器、会话管理、语音
│   ├── discord.py
│   ├── telegram.py
│   └── voice.py
├── cli/                   ← 包入口和 Claude 进程管理
│   └── __init__.py
├── config/                ← 设置、提供商目录、日志配置
│   ├── settings.py
│   └── provider_catalog.py
├── tests/                 ← 单元测试和契约测试
│   ├── test_routing.py
│   └── test_providers.py
├── .env.example           ← 配置模板
└── pyproject.toml         ← uv 项目配置
```

**关键模块详解：**

**providers/anthropic_messages.py** — 这是 FCC 最核心的文件之一。它实现了原生 Anthropic Messages 传输适配器，支持 DeepSeek、LM Studio、llama.cpp、Ollama 等直接兼容 Anthropic 协议的后端。传输层负责将 Claude Code 发出的请求转换为目标提供商的格式，并将响应转换回 Claude Code 期望的格式。

**providers/nim_transport.py** — NVIDIA NIM 使用 OpenAI Chat 格式而非原生 Anthropic Messages 格式，因此需要一个额外的转换层。NIM 传输适配器负责将 Anthropic 请求转换为 OpenAI Chat 格式，再将 OpenAI SSE 流式响应转换回 Anthropic SSE 格式。

**api/service.py** — 这是请求路由的核心逻辑。它根据请求中的模型名称（Opus/Sonnet/Haiku）解析对应的 `MODEL_OPUS`、`MODEL_SONNET`、`MODEL_HAIKU` 环境变量，确定实际应该路由到哪个提供商。

**core/sse_utils.py** — Claude Code 使用 Server-Sent Events（SSE）进行流式响应。SSE 工具函数负责处理流式事件的解析和重组，确保 Thinking Block、Tool Call、Content Block 等不同类型的事件能够正确地被 Claude Code 客户端识别。

## 适用场景、优势与边界

**最适合的场景：**

- 个人开发者或小团队想要免费或低成本使用 Claude Code
- 已有 NVIDIA NIM、OpenRouter、DeepSeek 等 API 额度，不想再额外付费给 Anthropic
- 需要在本地环境（LM Studio、llama.cpp、Ollama）运行模型以保护隐私
- 想通过 Discord 或 Telegram 远程控制 Claude Code 进行结对编程

**主要优势：**

1. **成本自由**：绕过 Anthropic 官方付费墙，使用免费或低价的第三方 API
2. **本地部署**：支持 llama.cpp、LM Studio、Ollama，数据不出本地
3. **模型混用**：支持按任务层级选择不同模型（Opus→OpenRouter、Haiku→Ollama）
4. **远程接入**：Discord/Telegram Bot 支持远程编程和团队协作
5. **协议透明**：对 Claude Code 客户端透明，无需修改任何代码

**需要认识的边界：**

1. **Tool Use 表现依赖后端**：部分 OpenAI 兼容模型可能发出格式错误的 Tool Call，需要目标模型和运行时都支持 Claude Code 所需的上下文长度和工具
2. **llama.cpp 需要正确启动参数**：llama.cpp 需要以足够的 `--ctx-size` 启动才能处理 Claude Code 的长提示
3. **流式响应可能中断**：部分提供商的网关可能在流式响应中途断开连接，需要降低并发或重试
4. **VS Code 扩展可能仍显示登录界面**：浏览器登录流程可能仍会出现一次，但实际流量由本地代理处理

## 总结与延伸阅读

Free Claude Code 是一个巧妙的技术项目，它通过一个本地代理服务器，将 Claude Code 与 Anthropic 官方 API 解耦，同时保持了对客户端的完全透明。其支持的六种后端提供商、模型层级路由、Discord/Telegram 远程接入等特性，使其成为想要突破 Claude Code 成本限制的开发者的有力选择。

**延伸阅读：**

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/Alishahryar1/free-claude-code |
| 官方文档 | https://github.com/Alishahryar1/free-claude-code#readme |
| Claude Code 官方 | https://docs.anthropic.com/en/docs/claude-code |
| NVIDIA NIM | https://developer.nvidia.com/nim |
| OpenRouter | https://openrouter.ai/ |
| DeepSeek | https://api.deepseek.com/ |
| LM Studio | https://lmstudio.ai/ |
| Ollama | https://ollama.com/ |

---

*原文地址：https://github.com/Alishahryar1/free-claude-code*
