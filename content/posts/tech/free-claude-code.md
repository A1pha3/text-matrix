---
title: "Free Claude Code：用免费提供商替代 Anthropic API，让 Claude Code 零成本运行"
date: "2026-04-27T01:04:00+08:00"
lastmod: "2026-09-10T08:00:00+08:00"
slug: free-claude-code
github_repo: "Alishahryar1/free-claude-code"
aliases:
  - "/posts/tech/free-claude-code-anthropic-proxy/"
  - "/posts/tech/free-claude-code-proxy-guide/"
  - "/posts/tech/free-claude-code-proxy-anthropic/"
  - "/posts/tech/free-claude-code-proxy-anthropic-api-free/"
description: "Free Claude Code 是一个本地代理，把 Claude Code / Codex / Pi 等编码代理的 Anthropic API 流量路由到 50+ 个提供商（NVIDIA NIM / OpenRouter / DeepSeek / 本地模型等），月均 13 亿+ 免费 token，让 Claude Code 零成本运行。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Anthropic", "API", "本地部署", "OpenRouter"]
---

# Free Claude Code：用免费提供商替代 Anthropic API，让 Claude Code 零成本运行

> **目标读者**：希望零成本使用 Claude Code 的开发者，或对 AI 编程助手 API 代理机制感兴趣的技术人员
> **前置知识**：基本了解 Claude Code、Anthropic API、环境变量配置，有 Python 基础更佳

---

## 一句话理解

Free Claude Code（FCC）是一个**本地代理**：它监听 `localhost:8082`，把编码代理发出的 Anthropic Messages API 请求拦截下来，转发到你配置的任意提供商（云端免费模型或本地模型），再把响应转回编码代理能识别的格式。编码代理始终以为自己在跟 Anthropic 对话，实际背后可能是 NVIDIA NIM、OpenRouter，或你机器上的 Ollama。

它从 2026 年 1 月发布以来快速迭代，目前支持 **10 个编码代理**（Claude Code、Codex、Pi、OpenCode、Cline、Hermes、DeepSeek Harness、Grok Build、Muse Code、Aider）和 **50+ 个符合服务条款的提供商**，月均可用的免费 token 超过 13 亿。

---

## 三层结构

代理的职责边界——它不负责推理，只负责"让 Claude Code 以为自己在跟 Anthropic 对话"：

| 层次 | 做什么 | 不做什么 |
|------|--------|---------|
| 环境变量层 | 通过 `fcc-claude` / `fcc-codex` 等启动器，把编码代理的 API 端点指向 `localhost:8082` | 不修改编码代理源码或配置 |
| 代理服务层 | 解析请求中的 model 信息、路由到对应提供商、做格式转换 | 不存储请求/响应，不缓存 |
| 提供商适配层 | 把 Anthropic Messages 格式转为各提供商原生格式，再转回 SSE | 不实现 LLM 推理，不管理模型生命周期 |

这一层级的核心设计意图：**把"模型选择"从编码代理的硬编码中解放出来**。Claude Code 只认 Anthropic 协议，而模型可以来自任何地方——这就是代理存在的全部理由。

---

## 核心原理：一次请求如何流过代理

```
Claude Code → FCC 代理 (:8082) → 免费 LLM 提供商
  Anthropic API 格式             Native/OpenAI 格式
```

假设你用 `fcc-claude` 让 Claude Code 重构一个 Python 文件。实际发生的链路是：

1. `fcc-claude` 启动器注入环境变量（`ANTHROPIC_BASE_URL=http://localhost:8082`），Claude Code 构造一个标准的 Anthropic Messages API 请求发往本地代理。
2. 代理收到请求，解析 `model` 字段——如果用户没指定，则用 Admin UI 中 `MODEL` 作为 fallback。
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

### 故障切换：Fallback Models

代理支持配置一个**有序的备用模型列表**。当主模型的请求在重试后仍失败，代理会自动切换到列表中的下一个模型继续当前回合，不需要你重启对话——这在免费额度波动或服务中断时尤其有用。注意：一次失败请求可能跨多个提供商消耗 token，配置时要考虑这一点。

### 终端输出瘦身：RTK

可选集成 [RTK](https://github.com/rtk-ai/rtk) 后，终端里的常见命令输出会被过滤，最多减少 90% 的输出 token。安装时勾选 RTK 即可启用。

### Claude Thinking 块转换

模型输出的 ` thinking` 标签和 `reasoning_content` 字段可以被转换为原生 Claude thinking 块。在 Admin UI 的 **Reasoning** 设置里，可以选择 `From client`（沿用 Claude Code 发出的推理等级）、`Off`（关闭推理）或强制指定 `Low` / `Medium` / `High` / `X-High` / `Max`。在 DeepSeek-R1 这类推理模型上，也能保留 Claude Code 的完整思考体验。

---

## 50+ 提供商：从六个常用提供商开始

代理发布初期支持 NVIDIA NIM、OpenRouter、DeepSeek、LM Studio、llama.cpp、Ollama 六个后端；如今已扩展到 **50+ 个符合服务条款的提供商**，覆盖 Groq、Google Gemini、Kimi、Z.ai、GitHub Copilot、OpenAI/ChatGPT 订阅等。所有提供商在 Admin UI 里统一配置：填入 API key → 搜索模型 → 校验 → 应用。

下面从最常用的六个讲起。模型名均以官方 README 当前为准。

### NVIDIA NIM（推荐，免费，40 req/min）

注册地址：https://build.nvidia.com/settings/api-keys

无需付费，40 请求/分钟，适合日常开发。默认模型为 `nvidia_nim/nvidia/nemotron-3-super-120b-a12b`，也可在模型下拉框里搜索其他模型：

```dotenv
NVIDIA_NIM_API_KEY="nvapi-your-key-here"
MODEL="nvidia_nim/nvidia/nemotron-3-super-120b-a12b"
```

### OpenRouter（大量免费模型）

注册地址：https://openrouter.ai/keys

覆盖数百种模型，部分免费：

```dotenv
OPENROUTER_API_KEY="sk-or-your-key-here"
MODEL="open_router/openrouter/free"
```

### DeepSeek（直接 API）

注册地址：https://platform.deepseek.com/api_keys

```dotenv
DEEPSEEK_API_KEY="your-deepseek-key-here"
MODEL="deepseek/deepseek-chat"
```

### LM Studio（完全本地，无 API key）

本地运行 GGUF 格式模型，无需联网。默认地址 `http://localhost:1234/v1`：

```dotenv
LM_STUDIO_BASE_URL="http://localhost:1234/v1"
MODEL="lmstudio/<model-id>"
```

安装 [LM Studio](https://lmstudio.ai)，加载支持 tool use 的模型，把模型标识符配到 `lmstudio/` 前缀后面。

### llama.cpp（本地推理引擎，无 API key）

轻量级本地推理，运行 `llama-server`（默认 `http://localhost:8080/v1`）：

```dotenv
LLAMACPP_BASE_URL="http://localhost:8080/v1"
MODEL="llamacpp/local-model"
```

### Ollama（本地运行时，无 API key）

简单易用的本地 LLM 运行时，默认 `http://localhost:11434`：

```dotenv
OLLAMA_BASE_URL="http://localhost:11434"
MODEL="ollama/llama3.1"
```

安装后 `ollama pull llama3.1 && ollama serve` 保持运行即可。

### 按模型档位路由（混用提供商）

`MODEL` 是所有请求的 fallback。可以为 Fable、Opus、Sonnet、Haiku 分别指定模型档位，覆盖到不同提供商：

```dotenv
NVIDIA_NIM_API_KEY="nvapi-your-key-here"
OPENROUTER_API_KEY="sk-or-your-key-here"

MODEL_OPUS="nvidia_nim/nvidia/nemotron-3-super-120b-a12b"  # Opus 用 NIM
MODEL_SONNET="open_router/openrouter/free"                # Sonnet 用 OpenRouter 免费
MODEL_HAIKU="lmstudio/qwen3.5-coder"                      # Haiku 用本地 LM Studio
MODEL="zai/glm-5.2"                                       # fallback
```

这一设计的价值在于**成本与能力的解耦**：把高质量任务路由到云端付费/免费大模型，把高频低难度任务路由到本地小模型，各取所需。

---

## 安装与快速开始

### 一键安装（官方推荐）

macOS / Linux：

```bash
curl -fsSL "https://raw.githubusercontent.com/Alishahryar1/free-claude-code/main/scripts/install.sh" | sh
```

Windows PowerShell：

```powershell
& ([scriptblock]::Create((irm "https://raw.githubusercontent.com/Alishahryar1/free-claude-code/main/scripts/install.ps1")))
```

安装时按提示选择至少一个编码代理（Claude Code / Codex / Pi / OpenCode / Cline / Hermes / DeepSeek Harness / Grok Build / Muse Code / Aider），可选安装 RTK。重复执行同一命令即可升级。

### 启动与配置

macOS / Windows 启动后出现桌面启动器或系统托盘图标，点击即可打开 Admin UI；Linux 运行：

```bash
fcc-server
```

服务器启动后会自动打开 Admin UI（默认 `http://127.0.0.1:8082/admin`）。配置步骤：

1. 在 [NVIDIA NIM](https://build.nvidia.com/settings/api-keys) 等提供商注册并创建 API key。
2. 在 Admin UI 填入对应字段（如 `NVIDIA_NIM_API_KEY`）。
3. 在 `MODEL` 下拉框搜索并选择模型，或手动输入 `<provider-id>/<model-id>`。
4. 点击 **Validate** 校验连接，再点 **Apply** 应用。

### 运行编码代理

```bash
fcc-claude    # Claude Code
fcc-codex     # Codex
fcc-pi        # Pi
```

启动器会自动注入代理所需的环境变量，编码代理原生参数照常可用，例如 `fcc-codex exec "hello"`。也可以从 Claude Code 的 `/model` 原生选择器里直接挑 FCC 暴露的模型。

### 从源码运行（可选）

想自己跑源码时：

```bash
git clone https://github.com/Alishahryar1/free-claude-code.git
cd free-claude-code
uv run fcc-server
```

源码按标准 Python 包组织在 `src/free_claude_code/` 下，`uv run` 会直接解析依赖并调用 `fcc-server` 入口。

### VSCode 扩展配置

1. 启动 FCC（桌面图标或 `fcc-server`）
2. 打开 VSCode Settings → 以 JSON 形式编辑用户设置
3. 添加：

```json
"claudeCode.disableLoginPrompt": true,
"claudeCode.environmentVariables": [
  { "name": "ANTHROPIC_BASE_URL", "value": "http://localhost:8082" },
  { "name": "ANTHROPIC_AUTH_TOKEN", "value": "freecc" },
  { "name": "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY", "value": "1" },
  { "name": "CLAUDE_CODE_AUTO_COMPACT_WINDOW", "value": "190000" },
  { "name": "DISABLE_AUTOUPDATER", "value": "1" },
  { "name": "DISABLE_FEEDBACK_COMMAND", "value": "1" },
  { "name": "DISABLE_ERROR_REPORTING", "value": "1" }
]
```

4. 重载扩展。端口和 token 需与 Admin UI 保持一致。

### IntelliJ / JetBrains 扩展配置

编辑 `~/.jetbrains/acp.json`（Linux / macOS）或 `%APPDATA%/JetBrains/acp-agents/installed.json`（Windows），在 `acp.registry.claude-acp` 的 `env` 中加入：

```json
"env": {
  "ANTHROPIC_BASE_URL": "http://localhost:8082",
  "ANTHROPIC_AUTH_TOKEN": "freecc",
  "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": "1",
  "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "190000",
  "DISABLE_AUTOUPDATER": "1",
  "DISABLE_FEEDBACK_COMMAND": "1",
  "DISABLE_ERROR_REPORTING": "1"
}
```

然后重启 IDE。

### 仍然提示登录？

如果配置完成后 Claude Code 仍要求登录，编辑其状态文件 `~/.claude.json`（Windows 为 `%USERPROFILE%\.claude.json`），在 JSON 中加入：

```json
"hasCompletedOnboarding": true
```

重启 Claude Code 或 IDE 即可。

---

## 模型选择

模型选择有两条路径，都不需要额外工具：

- **Admin UI**：在 `MODEL` 下拉框里搜索 FCC 暴露的全部模型，校验后应用。
- **编码代理原生选择器**：`fcc-claude` 启动后，直接在 Claude Code 的 `/model` 命令里挑选 FCC 的模型；Codex 同样支持原生模型选择。

FCC 通过模型发现机制（环境变量 `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1`）把自己的模型目录注入编码代理，让"换模型"和"换提供商"变成 UI 里的一个下拉框。

---

## 可选：代理身份认证

代理默认只监听本机，没有认证。需要把代理暴露到公网，或防止本机其他进程滥用时，可以在 Admin UI 里启用 **Proxy Authentication**，为代理设置一个 bearer token。客户端启动器会自动读取该 token，例如 Codex 通过 `fcc-codex --print-proxy-auth-token` 获取。

---

## 技术栈与架构

| 组件 | 技术选型 |
|------|---------|
| 语言 | Python 3.14 |
| 包管理 | uv + `pyproject.toml` |
| Web 框架 | FastAPI + Uvicorn |
| 测试 | Pytest（含 e2e 与 smoke 测试）|
| 类型检查 | Ty |
| 代码风格 | Ruff |
| 日志 | Loguru |
| HTTP 客户端 | httpx |
| 并发控制 | asyncio |

架构设计清晰：`BaseProvider` ABC 定义 provider 接口，消息平台则通过 `OutboundMessenger` 等 Protocol 定义扩展点（Discord、Telegram 都由此接入）。新增 provider 或消息平台只需实现对应接口；同时支持 `fcc-server --version` 查看版本、一键脚本原地升级、卸载脚本清理 `~/.fcc/`。

---

## 与直接用 Ollama / LM Studio 的区别

| 对比 | Free Claude Code | Ollama / LM Studio 直接用 |
|------|-----------------|------------------------|
| Anthropic 兼容 | 原生 | 需要兼容层 |
| Claude Code 集成 | 透明（`fcc-claude` 启动器）| 需要手动改配置 |
| Claude Thinking | 支持（可调推理等级）| 部分支持 |
| Tool use 处理 | 启发式解析 + 转发 | 需要模型支持 |
| Per-model 路由 | 支持（Fable / Opus / Sonnet / Haiku 分别路由）| 不支持 |
| 云端免费模型 | 支持（NIM / OpenRouter 等）| 不支持 |

Free Claude Code 做的关键工作是格式转换与协议适配：它知道 Anthropic Messages API 和 OpenAI Chat API 之间的差异，在请求和响应两端做双向转换，让 Claude Code 始终以为自己在跟 Anthropic 通信。

---

## 常见问题

**Q：免费模型的能力跟 Claude 官方模型差距大吗？**

看具体任务。简单代码修改、注释生成、单文件重构，NVIDIA NIM 上的 Nemotron、OpenRouter 免费模型差距不大。复杂多文件重构、精确的 tool use 调用，免费模型可能不够稳定——这是当前所有 Anthropic API 替代方案共有的天花板。

**Q：会泄露我的代码到第三方吗？**

取决于你选的提供商。LM Studio / llama.cpp / Ollama 完全本地，代码不出本机。NVIDIA NIM 和 OpenRouter 走云端 API，代码会发送到它们的服务器。如果你对代码隐私有要求，优先用本地方案。

**Q：代理崩溃了会怎样？**

编码代理会收到连接错误，跟 Anthropic API 断连的表现一样。不影响已有代码，重启 FCC 即可恢复。

**Q：可以用同一个代理服务多个编码代理吗？**

可以。代理默认监听 `0.0.0.0:8082`，支持并发请求，Claude Code、Codex、Pi 可共用同一代理。但免费提供商的速率限制（如 NIM 40 req/min）是共享的，多实例会分摊配额。

**Q：配置了代理还是提示登录？**

按上文"仍然提示登录"一节处理：在 `~/.claude.json` 中设置 `hasCompletedOnboarding: true`，然后重启。

---

## 适用场景与决策建议

| 场景 | 推荐提供商 | 优先级 |
|------|----------|--------|
| 日常开发，想零成本用 Claude Code | NVIDIA NIM（40 req/min 免费）| 先试这个 |
| 需要更强推理能力 | OpenRouter / Z.ai / Groq 免费大模型 | 能力不够再上 |
| 完全本地，代码隐私敏感 | LM Studio / llama.cpp / Ollama | 本机有 GPU 优先 |
| 想用 DeepSeek 模型 | DeepSeek（direct API）| 已有 DeepSeek 额度直接用 |
| 混用不同级别模型 | 按档位路由（Opus 走云端，Haiku 走本地）| 最佳性价比 |
| 需要稳定高并发 | 付费提供商或 Anthropic 官方 API | 预算允许时直接官方 |

**日常开发量不大**，先从 NVIDIA NIM 免费方案开始——不需要任何付费，40 req/min 足够一个人正常使用。

**代码隐私敏感**，直接用 LM Studio 下载 GGUF 模型，完全离线。本地模型不考虑 API 费用，但需要至少 8GB 显存，推荐 16GB 以上。

**已经买了 DeepSeek API 额度**，把 `MODEL` 指到 `deepseek/deepseek-chat` 即可，量大的任务再按档位细分。

**需要 Claude Code 的完整能力**——尤其是复杂多文件重构、精确的 tool use 调用——免费模型的兼容性可能不够稳。这时直接付 Anthropic API 费用更划算，代理的格式转换层在这个场景下反而可能引入额外的不确定性。

**多实例共享**，把代理部署在一台机器上，所有编码代理通过同一个 `ANTHROPIC_BASE_URL` 连接。注意免费提供商的速率限制是共享的，多实例会分摊配额。

---

## 相关链接

- GitHub：https://github.com/Alishahryar1/free-claude-code（53k+ stars，MIT License）
- NVIDIA NIM：https://build.nvidia.com/settings/api-keys
- OpenRouter：https://openrouter.ai/keys
- DeepSeek：https://platform.deepseek.com/api_keys

🦞 每日 08:00 自动更新