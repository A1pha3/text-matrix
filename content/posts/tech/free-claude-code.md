---
title: "Free Claude Code：用免费提供商替代 Anthropic API，让 Claude Code 零成本运行"
date: 2026-04-27T01:04:00+08:00
slug: free-claude-code
description: "Free Claude Code 是一个 Python 代理服务器，通过环境变量拦截 Claude Code 的 Anthropic API 调用并路由到免费提供商（NVIDIA NIM / OpenRouter / DeepSeek / LM Studio / llama.cpp / Ollama），实现 Claude Code 零成本使用。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Anthropic", "API", "免费", "本地部署", "OpenRouter", "NVIDIA NIM"]
---

# Free Claude Code：用免费提供商替代 Anthropic API，让 Claude Code 零成本运行

Claude Code 是 Anthropic 官方出的 AI 编程助手，但每次调用都要消耗 Anthropic API 额度。用不起？Free Claude Code 来解决。

GitHub 12.9k stars，MIT 协议，Python 3.14 + uv + Ty + Ruff + Loguru 技术栈。一个轻量代理服务器，通过两个环境变量把 Claude Code 的 API 调用透明路由到免费提供商——NVIDIA NIM（40 req/min 免费）、OpenRouter（大量免费模型）、DeepSeek、以及完全免费的本地方案（LM Studio / llama.cpp / Ollama）。

**一行配置，零修改 Claude Code 本体，Claude Code 变成免费的。**

---

## 一、核心原理：透明代理拦截

Free Claude Code 的核心是一个 FastAPI 代理服务器，运行在本地 `:8082` 端口：

```
Claude Code → Free Claude Code Proxy (:8082) → 免费 LLM 提供商
  Anthropic API                               Native/OpenAI 格式
```

Claude Code 发送标准 Anthropic API 格式的请求，代理拦截后：
1. 解析请求中的 model 信息（Opus / Sonnet / Haiku）
2. 根据 `MODEL_OPUS` / `MODEL_SONNET` / `MODEL_HAIKU` 配置路由到对应提供商的模型
3. 转换为提供商原生的 API 格式（Anthropic Messages / OpenAI Chat）
4. 转发请求，获取响应
5. 将响应转回 Claude 兼容的 SSE 格式返回

Claude Code 完全感知不到代理的存在——它以为自己连的是 Anthropic API。

---

## 二、六大提供商

### 2.1 NVIDIA NIM（推荐，免费，40 req/min）

注册地址：https://build.nvidia.com/settings/api-keys

无需付费，40 请求/分钟，适合日常驱动开发：

```dotenv
NVIDIA_NIM_API_KEY="nvapi-your-key-here"
MODEL_OPUS=
MODEL_SONNET=
MODEL_HAIKU=
MODEL="nvidia_nim/z-ai/glm4.7"   # fallback
ENABLE_MODEL_THINKING=true
```

主流可用模型（含 MiniMax-M2.5、Qwen3.5 等）。

### 2.2 OpenRouter（大量免费模型）

注册地址：https://openrouter.ai/keys

覆盖数百种模型，部分免费：

```dotenv
OPENROUTER_API_KEY="sk-or-your-key-here"
MODEL_OPUS="open_router/deepseek/deepseek-r1-0528:free"
MODEL_SONNET="open_router/openai/gpt-oss-120b:free"
MODEL_HAIKU="open_router/stepfun/step-3.5-flash:free"
MODEL="open_router/stepfun/step-3.5-flash:free"
```

### 2.3 DeepSeek（直接 API）

注册地址：https://platform.deepseek.com/api_keys

```dotenv
DEEPSEEK_API_KEY="your-deepseek-key-here"
MODEL_OPUS="deepseek/deepseek-reasoner"
MODEL_SONNET="deepseek/deepseek-chat"
MODEL_HAIKU="deepseek/deepseek-chat"
```

### 2.4 LM Studio（完全本地，无 API key）

本地运行 GGUF 格式模型，隐私无上网：

```dotenv
MODEL_OPUS="lmstudio/unsloth/MiniMax-M2.5-GGUF"
MODEL_SONNET="lmstudio/unsloth/Qwen3.5-35B-A3B-GGUF"
MODEL_HAIKU="lmstudio/unsloth/GLM-4.7-Flash-GGUF"
```

安装 [LM Studio](https://lmstudio.ai)，下载模型，无需 API key。

### 2.5 llama.cpp（本地推理引擎，无 API key）

轻量级本地推理，运行 `llama-server`：

```dotenv
LLAMACPP_BASE_URL="http://localhost:8080/v1"
MODEL_OPUS="llamacpp/local-model"
MODEL="llamacpp/local-model"
```

### 2.6 Ollama（本地运行时，无 API key）

简单易用的本地 LLM 运行时，原生 Anthropic Messages API 支持：

```dotenv
OLLAMA_BASE_URL="http://localhost:11434"
MODEL_OPUS="ollama/llama3.1"
MODEL="ollama/llama3.1"
```

安装后 `ollama serve` 保持运行即可。

### 2.7 混用提供商

每个 `MODEL_*` 变量可以配置不同提供商，灵活组合：

```dotenv
NVIDIA_NIM_API_KEY="nvapi-your-key-here"
OPENROUTER_API_KEY="sk-or-your-key-here"

MODEL_OPUS="nvidia_nim/moonshotai/kimi-k2.5"              # Opus 用 NIM
MODEL_SONNET="open_router/deepseek/deepseek-r1-0528:free" # Sonnet 用 OpenRouter 免费
MODEL_HAIKU="lmstudio/unsloth/GLM-4.7-Flash-GGUF"        # Haiku 用本地 LM Studio
MODEL="nvidia_nim/z-ai/glm4.7"                           # fallback
```

---

## 三、请求优化：5 类本地拦截

代理还会拦截 5 类琐碎请求，直接本地响应，不消耗任何 API 配额：

1. **Quota probe**：配额探测请求
2. **Title generation**：会话标题生成
3. **Prefix detection**：前缀检测
4. **Suggestions**：代码建议
5. **Filepath extraction**：文件路径提取

这些请求量大但价值低，拦截后既省配额又降延迟。

---

## 四、Claude Thinking 块支持

模型输出的 `<think>` 标签和 `reasoning_content` 字段可以被转换为原生 Claude thinking 块——只要在配置中开启 `ENABLE_MODEL_THINKING`（或针对 Opus/Sonnet/Haiku 分别设置）。

这意味着可以在 DeepSeek-R1 类的推理模型上使用 Claude Code 的完整 thinking 能力。

---

## 五、安装与快速开始

### 5.1 环境准备

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装 Python 3.14
uv python install 3.14
```

### 5.2 克隆与配置

```bash
git clone https://github.com/Alishahryar1/free-claude-code.git
cd free-claude-code
cp .env.example .env
# 编辑 .env，选择提供商并填入 API key
```

### 5.3 启动代理 + Claude Code

**终端 1：启动代理**
```bash
uv run uvicorn server:app --host 0.0.0.0 --port 8082
```

**终端 2：运行 Claude Code**
```bash
# PowerShell
$env:ANTHROPIC_AUTH_TOKEN="freecc"; $env:ANTHROPIC_BASE_URL="http://localhost:8082"; claude

# Bash
ANTHROPIC_AUTH_TOKEN="freecc" ANTHROPIC_BASE_URL="http://localhost:8082" claude
```

### 5.4 VSCode 扩展配置

1. 启动代理（同上）
2. 打开 VSCode Settings → 搜索 `claude-code.environmentVariables`
3. 添加：
```json
"claudeCode.environmentVariables": [
  { "name": "ANTHROPIC_BASE_URL", "value": "http://localhost:8082" },
  { "name": "ANTHROPIC_AUTH_TOKEN", "value": "freecc" }
]
```
4. 重载扩展，如果看到登录页面点击 Anthropic Console 然后 authorize

### 5.5 IntelliJ 扩展配置

编辑 `~/.jetbrains/acp.json`（Linux/macOS）或 `%APPDATA%/JetBrains/acp-agents/installed.json`（Windows），在 `acp.registry.claude-acp` 的 `env` 中加入：

```json
"env": {
  "ANTHROPIC_AUTH_TOKEN": "freecc",
  "ANTHROPIC_BASE_URL": "http://localhost:8082"
}
```
然后重启 IDE。

---

## 六、Model Picker：交互式选择模型

`claude-pick` 是内置的交互式模型选择器，每次启动 Claude Code 时可以选择模型：

```bash
# 先安装 fzf
brew install fzf

# 添加 alias 到 ~/.zshrc
alias claude-pick="/path/to/free-claude-code/claude-pick"
source ~/.zshrc

# 每次运行
claude-pick   # 交互式选择模型，然后启动 Claude Code
```

也支持固定模型 alias，不需要 picker：
```bash
alias claude-kimi='ANTHROPIC_BASE_URL="http://localhost:8082" ANTHROPIC_AUTH_TOKEN="freecc:moonshotai/kimi-k2.5" claude'
```

---

## 七、可选：身份认证

在公网暴露代理时，可以设置 `ANTHROPIC_AUTH_TOKEN` 要求客户端认证：

```dotenv
ANTHROPIC_AUTH_TOKEN="your-secret-token-here"
```

客户端需要提供相同 token：
```bash
ANTHROPIC_AUTH_TOKEN="your-secret-token-here" ANTHROPIC_BASE_URL="http://localhost:8082" claude
```

---

## 八、技术栈与架构

| 组件 | 技术选型 |
|------|---------|
| 语言 | Python 3.14 |
| 包管理 | uv + `pyproject.toml` |
| Web 框架 | FastAPI + Uvicorn |
| 类型检查 | Ty |
| 代码风格 | Ruff |
| 日志 | Loguru |
| HTTP 客户端 | httpx |
| 并发控制 | asyncio |

架构设计清晰：`BaseProvider` ABC 定义provider接口，`MessagingPlatform` ABC 定义消息平台扩展点。新增 provider 或 platform 非常容易。

---

## 九、与 Ollama/LocalAI 等本地方案的区别

| 对比 | Free Claude Code | Ollama / LM Studio 直接用 |
|------|-----------------|------------------------|
| Anthropic 兼容 | 原生 | 需要兼容层 |
| Claude Code 集成 | 透明（两个 env 变量）| 需要修改 Claude Code 配置 |
| Claude Thinking | 支持 | 部分支持 |
| Tool use 处理 | 启发式解析 | 需要模型支持 |
| Per-model 路由 | 支持（Opus/Sonnet/Haiku 分别路由）| 不支持 |

Free Claude Code 的核心价值在于：**它知道怎么让 Claude Code 以为自己在跟 Anthropic 说话**，而实际上背后连的是各种免费或本地模型。

---

## 十、适用场景

| 场景 | 推荐提供商 |
|------|----------|
| 日常开发，想零成本用 Claude Code | NVIDIA NIM（40 req/min 免费）|
| 需要 Opus 级别能力 | OpenRouter（DeepSeek-R1 等免费大模型）|
| 完全本地，隐私敏感 | LM Studio / llama.cpp / Ollama |
| 想用 DeepSeek 推理模型 | DeepSeek（direct API）|
| 混用不同级别模型（Opus/Sonnet/Haiku 不同源）| 混用模式 |

---

## 总结

Free Claude Code 解决的是一个非常实际的问题：**Claude Code 是个好工具，但 Anthropic API 不是免费的**。

它用透明代理 + per-model 路由 + 请求优化 + thinking 块转换的方式，让 Claude Code 可以在 NVIDIA NIM、OpenRouter、DeepSeek 和各种本地模型上运行，两个环境变量配置，零修改 Claude Code 本体。

如果你在找一种方式让 Claude Code 免费跑起来，或者想用本地模型保护隐私，这个项目值得一试。

**相关链接：**

- GitHub：https://github.com/Alishahryar1/free-claude-code（12.9k stars）
- NVIDIA NIM：https://build.nvidia.com/settings/api-keys
- OpenRouter：https://openrouter.ai/keys
- DeepSeek：https://platform.deepseek.com/api_keys

🦞 每日08:00自动更新