---
title: "Free Claude Code：用免费提供商替代 Anthropic API，让 Claude Code 零成本运行"
date: "2026-04-27T01:04:00+08:00"
slug: free-claude-code
aliases:
  - "/posts/tech/free-claude-code-anthropic-proxy/"
  - "/posts/tech/free-claude-code-proxy-guide/"
  - "/posts/tech/free-claude-code-proxy-anthropic/"
  - "/posts/tech/free-claude-code-proxy-anthropic-api-free/"
description: "Free Claude Code 是一个 Python 代理服务器，通过环境变量拦截 Claude Code 的 Anthropic API 调用并路由到免费提供商（NVIDIA NIM / OpenRouter / DeepSeek / LM Studio / llama.cpp / Ollama），实现 Claude Code 零成本使用。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Anthropic", "API", "免费", "本地部署", "OpenRouter", "NVIDIA NIM"]
---

# Free Claude Code：用免费提供商替代 Anthropic API，让 Claude Code 零成本运行

Claude Code 是 Anthropic 官方的命令行 AI 编程助手，默认只接受 Anthropic API 调用——每次对话都要按 token 付费，对个人开发者持续使用成本不低。Free Claude Code 做的事很直接：用两个环境变量把 Claude Code 的 API 请求拦截下来，透明转发到免费或本地模型。Claude Code 不知道自己连的不是 Anthropic 的服务器。

GitHub 12.9k stars，MIT 协议，Python 3.14 + uv + Ty + Ruff + Loguru 技术栈。核心是一个 FastAPI 代理，本地监听 `:8082`，支持 NVIDIA NIM（40 req/min 免费）、OpenRouter（大量免费模型）、DeepSeek 直接 API，以及完全本地的 LM Studio / llama.cpp / Ollama。

**本文覆盖：怎么用两个环境变量让 Claude Code 走免费模型；六大提供商分别适合什么场景；代理在后台做了哪些转换；以及这个方案的能力边界在哪里。**

---

## 一、系统地图：三层结构

代理的职责边界——它不负责推理，只负责"让 Claude Code 以为自己在跟 Anthropic 对话"：

| 层次 | 做什么 | 不做什么 |
|------|--------|---------|
| 环境变量层 | 把 Claude Code 的 API 端点指向 `localhost:8082` | 不修改 Claude Code 源码或配置 |
| 代理服务层 | 解析请求中的 model 信息、路由到对应提供商、做格式转换 | 不存储请求/响应，不缓存 |
| 提供商适配层 | 把 Anthropic Messages 格式转为各提供商原生格式，再转回 SSE | 不实现 LLM 推理，不管理模型生命周期 |

三条线各司其职，下面分别展开。

---

## 二、核心原理：一次请求如何流过代理

```
Claude Code → Free Claude Code Proxy (:8082) → 免费 LLM 提供商
  Anthropic API 格式                            Native/OpenAI 格式
```

假设你用 `claude` 命令行让 Claude Code 重构一个 Python 文件。实际发生的链路是：

1. Claude Code 构造一个标准的 Anthropic Messages API 请求，发往 `ANTHROPIC_BASE_URL`（已被你设为 `http://localhost:8082`）。
2. 代理收到请求，解析 `model` 字段——如果用户没指定，则用 `.env` 中 `MODEL` 作为 fallback。
3. 根据 model 前缀（`nvidia_nim/`、`open_router/`、`deepseek/`、`lmstudio/`、`ollama/`、`llamacpp/`）匹配对应的提供商适配器。
4. 适配器把 Anthropic 格式的请求体转为目标格式：NVIDIA NIM 用 OpenAI Chat 格式，Ollama 用原生 Anthropic Messages 格式，以此类推。
5. 提供商返回响应后，适配器把响应转回 Claude Code 期望的 SSE 事件流。
6. Claude Code 收到 SSE 流，渲染对话——整个过程对用户完全透明。

代理还拦截 5 类琐碎请求，直接本地响应，不消耗 API 配额：

1. **Quota probe**：配额探测请求
2. **Title generation**：会话标题生成
3. **Prefix detection**：前缀检测
4. **Suggestions**：代码建议
5. **Filepath extraction**：文件路径提取

这些请求量大但价值低，拦截后既省配额又降延迟。

### Claude Thinking 块转换

模型输出的 ` thinking` 标签和 `reasoning_content` 字段可以被转换为原生 Claude thinking 块。开启 `ENABLE_MODEL_THINKING`（或针对 Opus / Sonnet / Haiku 分别设置）后，在 DeepSeek-R1 这类推理模型上也能使用 Claude Code 的完整 thinking 能力。

---

## 三、六大提供商

### 3.1 NVIDIA NIM（推荐，免费，40 req/min）

注册地址：https://build.nvidia.com/settings/api-keys

无需付费，40 请求/分钟，适合日常开发：

```dotenv
NVIDIA_NIM_API_KEY="nvapi-your-key-here"
MODEL_OPUS=
MODEL_SONNET=
MODEL_HAIKU=
MODEL="nvidia_nim/z-ai/glm4.7"   # fallback
ENABLE_MODEL_THINKING=true
```

主流可用模型含 MiniMax-M2.5、Qwen3.5 等。

### 3.2 OpenRouter（大量免费模型）

注册地址：https://openrouter.ai/keys

覆盖数百种模型，部分免费：

```dotenv
OPENROUTER_API_KEY="sk-or-your-key-here"
MODEL_OPUS="open_router/deepseek/deepseek-r1-0528:free"
MODEL_SONNET="open_router/openai/gpt-oss-120b:free"
MODEL_HAIKU="open_router/stepfun/step-3.5-flash:free"
MODEL="open_router/stepfun/step-3.5-flash:free"
```

### 3.3 DeepSeek（直接 API）

注册地址：https://platform.deepseek.com/api_keys

```dotenv
DEEPSEEK_API_KEY="your-deepseek-key-here"
MODEL_OPUS="deepseek/deepseek-reasoner"
MODEL_SONNET="deepseek/deepseek-chat"
MODEL_HAIKU="deepseek/deepseek-chat"
```

### 3.4 LM Studio（完全本地，无 API key）

本地运行 GGUF 格式模型，无需联网：

```dotenv
MODEL_OPUS="lmstudio/unsloth/MiniMax-M2.5-GGUF"
MODEL_SONNET="lmstudio/unsloth/Qwen3.5-35B-A3B-GGUF"
MODEL_HAIKU="lmstudio/unsloth/GLM-4.7-Flash-GGUF"
```

安装 [LM Studio](https://lmstudio.ai)，下载模型，无需 API key。

### 3.5 llama.cpp（本地推理引擎，无 API key）

轻量级本地推理，运行 `llama-server`：

```dotenv
LLAMACPP_BASE_URL="http://localhost:8080/v1"
MODEL_OPUS="llamacpp/local-model"
MODEL="llamacpp/local-model"
```

### 3.6 Ollama（本地运行时，无 API key）

简单易用的本地 LLM 运行时，原生 Anthropic Messages API 支持：

```dotenv
OLLAMA_BASE_URL="http://localhost:11434"
MODEL_OPUS="ollama/llama3.1"
MODEL="ollama/llama3.1"
```

安装后 `ollama serve` 保持运行即可。

### 3.7 混用提供商

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

## 四、安装与快速开始

### 4.1 环境准备

```bash
# 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装 Python 3.14
uv python install 3.14
```

### 4.2 克隆与配置

```bash
git clone https://github.com/Alishahryar1/free-claude-code.git
cd free-claude-code
cp .env.example .env
# 编辑 .env，选择提供商并填入 API key
```

### 4.3 启动代理 + Claude Code

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

### 4.4 VSCode 扩展配置

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

### 4.5 IntelliJ 扩展配置

编辑 `~/.jetbrains/acp.json`（Linux / macOS）或 `%APPDATA%/JetBrains/acp-agents/installed.json`（Windows），在 `acp.registry.claude-acp` 的 `env` 中加入：

```json
"env": {
  "ANTHROPIC_AUTH_TOKEN": "freecc",
  "ANTHROPIC_BASE_URL": "http://localhost:8082"
}
```

然后重启 IDE。

---

## 五、Model Picker：交互式选择模型

`claude-pick` 是内置的交互式模型选择器，每次启动 Claude Code 时选择模型：

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

## 六、可选：身份认证

在公网暴露代理时，可以设置 `ANTHROPIC_AUTH_TOKEN` 要求客户端认证：

```dotenv
ANTHROPIC_AUTH_TOKEN="your-secret-token-here"
```

客户端需要提供相同 token：

```bash
ANTHROPIC_AUTH_TOKEN="your-secret-token-here" ANTHROPIC_BASE_URL="http://localhost:8082" claude
```

---

## 七、技术栈与架构

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

架构设计清晰：`BaseProvider` ABC 定义 provider 接口，`MessagingPlatform` ABC 定义消息平台扩展点。新增 provider 或 platform 只需实现对应接口。

---

## 八、与 Ollama / LocalAI 等本地方案的区别

| 对比 | Free Claude Code | Ollama / LM Studio 直接用 |
|------|-----------------|------------------------|
| Anthropic 兼容 | 原生 | 需要兼容层 |
| Claude Code 集成 | 透明（两个 env 变量）| 需要修改 Claude Code 配置 |
| Claude Thinking | 支持 | 部分支持 |
| Tool use 处理 | 启发式解析 | 需要模型支持 |
| Per-model 路由 | 支持（Opus / Sonnet / Haiku 分别路由）| 不支持 |

Free Claude Code 做的关键工作是格式转换与协议欺骗：它知道 Anthropic Messages API 和 OpenAI Chat API 之间的差异，在请求和响应两端做双向转换，让 Claude Code 始终以为自己在跟 Anthropic 通信。

---

## 九、常见问题

**Q：免费模型的能力跟 Claude 官方模型差距大吗？**

看具体任务。简单代码修改、注释生成、单文件重构，NVIDIA NIM 上的 Qwen3.5 或 MiniMax-M2.5 差距不大。复杂多文件重构、精确的 tool use 调用，免费模型可能不够稳定——这是当前所有 Anthropic API 替代方案共有的天花板。

**Q：会泄露我的代码到第三方吗？**

取决于你选的提供商。LM Studio / llama.cpp / Ollama 完全本地，代码不出本机。NVIDIA NIM 和 OpenRouter 走云端 API，代码会发送到它们的服务器。如果你对代码隐私有要求，优先用本地方案。

**Q：代理崩溃了会怎样？**

Claude Code 会收到连接错误，跟 Anthropic API 断连的表现一样。不影响已有代码，重启代理即可恢复。

**Q：可以用同一个代理服务多个 Claude Code 实例吗？**

可以。代理默认监听 `0.0.0.0:8082`，支持并发请求。但免费提供商的速率限制（如 NIM 40 req/min）是共享的，多实例会分摊配额。

---

## 十、适用场景与决策建议

| 场景 | 推荐提供商 | 优先级 |
|------|----------|--------|
| 日常开发，想零成本用 Claude Code | NVIDIA NIM（40 req/min 免费）| 先试这个 |
| 需要 Opus 级别推理能力 | OpenRouter（DeepSeek-R1 等免费大模型）| 能力不够再上 |
| 完全本地，代码隐私敏感 | LM Studio / llama.cpp / Ollama | 本机有 GPU 优先 |
| 想用 DeepSeek 推理模型 | DeepSeek（direct API）| 已有 DeepSeek 额度直接用 |
| 混用不同级别模型 | 混用模式（Opus 走云端，Haiku 走本地）| 最佳性价比 |

**如果你日常开发量不大**，先从 NVIDIA NIM 免费方案开始——不需要任何付费，40 req/min 足够一个人正常使用。

**如果对代码隐私有要求**，直接用 LM Studio 下载 GGUF 模型，完全离线。本地模型不考虑 API 费用，但需要你有足够的显存（至少 8GB 推荐 16GB 以上）。

**如果你已经买了 DeepSeek API 额度**，把 Opus 路由到 `deepseek-reasoner`、Sonnet / Haiku 路由到 `deepseek-chat` 是个合理的混用方案。

**反过来，如果你需要 Claude Code 的完整能力**——尤其是复杂多文件重构、精确的 tool use 调用——免费模型的兼容性可能不够稳。这时直接付 Anthropic API 费用更划算，代理的格式转换层在这个场景下反而可能引入额外的不确定性。

**如果你需要多实例共享**，把代理部署在一台机器上，所有 Claude Code 实例通过同一个 `ANTHROPIC_BASE_URL` 连接。注意免费提供商的速率限制是共享的，多实例会分摊配额。

---

## 相关链接

- GitHub：https://github.com/Alishahryar1/free-claude-code（12.9k stars）
- NVIDIA NIM：https://build.nvidia.com/settings/api-keys
- OpenRouter：https://openrouter.ai/keys
- DeepSeek：https://platform.deepseek.com/api_keys

🦞 每日 08:00 自动更新