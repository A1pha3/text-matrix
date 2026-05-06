---
title: "Free Claude Code：用免费代理突破 Anthropic API 限制"
slug: "free-claude-code-proxy-guide"
description: "Free Claude Code 是一个轻量级代理工具，通过将 Claude Code 的 Anthropic API 调用路由到 NVIDIA NIM、OpenRouter、DeepSeek、LM Studio 或 llama.cpp，让用户无需 Anthropic API Key 即可免费使用 Claude Code CLI 和 VSCode 扩展。"
date: "2026-04-24T11:30:00+08:00"
categories: ["技术笔记"]
tags: ["Claude Code", "AI编程", "API代理", "开源工具", "NVIDIA NIM"]
---

# Free Claude Code：用免费代理突破 Anthropic API 限制

> **项目地址**：[github.com/Alishahryar1/free-claude-code](https://github.com/Alishahryar1/free-claude-code)
>
> **核心理念**：通过路由 Claude Code 的 API 调用到免费或低成本供应商，让更多开发者免费使用 Claude Code。

## 项目概览

Claude Code 是 Anthropic 官方推出的 AI 编程助手，支持 CLI 和 VSCode 扩展。然而，使用 Claude Code 需要付费的 Anthropic API Key，这对于个人开发者或小型团队来说可能是一笔不小的开支。

**Free Claude Code** 应运而生——它是一个轻量级代理工具，通过将 Claude Code 的 Anthropic API 调用路由到多个免费或低成本的 AI API 供应商，让用户无需 Anthropic API Key 即可免费使用 Claude Code。

## 核心特性

| 特性 | 说明 |
|------|------|
| **零成本** | NVIDIA NIM 提供 40 req/min 免费额度，OpenRouter 提供多种免费模型 |
| **即插即用** | 只需设置 2 个环境变量，无需修改 Claude Code 本身 |
| **多供应商支持** | 支持 NVIDIA NIM、OpenRouter、DeepSeek、LM Studio、llama.cpp |
| **思维令牌支持** | 支持解析 `</think>` 标签和 `reasoning_content` 到原生 Claude 思维块 |
| **智能速率限制** | 滚动窗口限流 + 429 指数退避 + 可选并发上限 |
| **Discord/Telegram 机器人** | 远程自主编码，支持树状线程、会话持久化和实时进度 |

## 支持的供应商

### 1. NVIDIA NIM（推荐）

NVIDIA NIM 提供 40 req/min 的免费额度，是目前最好的免费选项：

```bash
NVIDIA_NIM_API_KEY="nvapi-your-key-here"
MODEL_OPUS="nvidia_nim/z-ai/glm4-7b"
MODEL_SONNET="nvidia_nim/moonshotai/kimi-k2-thinking"
MODEL_HAIKU="nvidia_nim/stepfun-ai/step-3.5-flash"
ENABLE_THINKING=true
```

获取 API Key：[build.nvidia.com/settings/api-keys](https://build.nvidia.com/settings/api-keys)

### 2. OpenRouter

OpenRouter 支持数百种模型，包括多种免费模型：

```bash
OPENROUTER_API_KEY="sk-or-your-key-here"
MODEL_OPUS="open_router/deepseek/deepseek-r1-0528:free"
MODEL_SONNET="open_router/openai/gpt-oss-120b:free"
MODEL_HAIKU="open_router/stepfun/step-3.5-flash:free"
```

### 3. DeepSeek

DeepSeek 提供直接的 API 支持：

```bash
DEEPSEEK_API_KEY="your-deepseek-key"
```

### 4. LM Studio（完全本地）

如果你有本地 GPU，可以完全离线运行：

```bash
# 无需 API Key，直接使用本地模型
LM_STUDIO_BASE_URL="http://localhost:1234/v1"
```

### 5. llama.cpp（完全本地）

使用 `llama-server` 运行本地模型：

```bash
LLAMA_CPP_BASE_URL="http://localhost:8080/v1"
```

## 快速开始

### 前置要求

1. 获取 API Key（LM Studio 或 llama.cpp 本地运行无需 Key）：
   - NVIDIA NIM：[build.nvidia.com/settings/api-keys](https://build.nvidia.com/settings/api-keys)
   - OpenRouter：[openrouter.ai/keys](https://openrouter.ai/keys)
   - DeepSeek：[platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)
   - LM Studio：[lmstudio.ai](https://lmstudio.ai)

2. 安装 Claude Code：
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

### 安装与配置

```bash
# 克隆仓库
git clone https://github.com/Alishahryar1/free-claude-code.git
cd free-claude-code

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，选择你的供应商
nano .env  # 或使用任何文本编辑器
```

### 启动代理

```bash
# 使用 uv 运行（推荐）
pip install uv
uv run python proxy.py

# 或直接运行
python proxy.py
```

### 配置 Claude Code

在你的终端中设置环境变量：

```bash
# Linux/macOS
export ANTHROPIC_BASE_URL="http://localhost:8080/v1"
export ANTHROPIC_API_KEY="anything"  # 可以是任意值，代理会忽略

# Windows (PowerShell)
$env:ANTHROPIC_BASE_URL="http://localhost:8080/v1"
$env:ANTHROPIC_API_KEY="anything"
```

现在你可以像平常一样使用 Claude Code 了！

## 工作原理

Free Claude Code 的核心是一个轻量级代理服务器：

```
Claude Code CLI → Free Claude Code Proxy → NVIDIA NIM/OpenRouter/DeepSeek/LM Studio/llama.cpp
                 (本地端口 8080)         (远程/本地 API)
```

代理服务器拦截 Claude Code 的 API 调用，进行以下转换：

1. **模型映射**：将 Claude 模型名称（如 `claude-opus-4-5-20251120`）映射到目标供应商的等效模型
2. **请求转发**：将请求转发到目标供应商的 API
3. **响应转换**：将供应商的响应转换为 Claude Code 期望的格式
4. **思维块处理**：处理思维令牌和 `reasoning_content`

## 适用场景

### 适合的场景

- 个人开发者或小型团队，想免费体验 Claude Code
- 有 NVIDIA GPU，希望完全本地运行 AI 编程助手
- 想尝试不同 AI 模型进行编程
- 学习 AI 编程，不想花费太多 API 费用

### 不适合的场景

- 需要使用官方 Claude Code 的完整功能（某些高级功能可能不可用）
- 需要稳定的生产级服务（建议使用官方 API）
- 需要使用 Opus 模型进行复杂任务（免费模型能力有限）

## 常见问题

### Q: 免费供应商的模型质量如何？

A: 免费模型（如 NVIDIA NIM 的 GLM-4-7B）在大多数编程任务上表现良好，但对于复杂的多步骤任务，可能不如 Claude Opus。建议根据任务复杂度选择合适的模型。

### Q: 支持 Claude Code 的 VSCode 扩展吗？

A: 支持！Free Claude Code 兼容 CLI 和 VSCode 扩展。只需要设置环境变量即可。

### Q: 本地运行需要什么硬件？

A: 如果使用 LM Studio 或 llama.cpp 本地运行，建议：
- 至少 16GB RAM
- NVIDIA GPU（至少 8GB 显存）效果最佳
- macOS Apple Silicon（M1/M2/M3/M4）也可以

### Q: 安全吗？

A: Free Claude Code 是一个本地代理，所有请求都经过你的机器。如果你使用远程 API，请确保遵守供应商的使用条款。

## 总结

Free Claude Code 是一个创新的开源项目，它通过智能路由让更多开发者能够免费使用 Claude Code 进行 AI 编程。虽然它不能完全替代官方 Claude Code（尤其是需要 Opus 模型复杂任务的场景），但对于学习、实验和日常轻量级编程任务来说，它提供了一个很好的免费选择。

如果你想尝试 AI 编程但又不想花费太多，Free Claude Code 绝对值得一试！

## 延伸阅读

- [Claude Code 官方文档](https://docs.anthropic.com/claude-code)
- [NVIDIA NIM API](https://build.nvidia.com/)
- [OpenRouter](https://openrouter.ai/)
- [LM Studio](https://lmstudio.ai/)

---

*本文由钳岳星君撰写，基于 GitHub 仓库 [Alishahryar1/free-claude-code](https://github.com/Alishahryar1/free-claude-code) 的 README。*
