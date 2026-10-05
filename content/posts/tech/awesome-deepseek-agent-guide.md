---
title: "Awesome DeepSeek Agent：23 款主流 AI 编程助手接入 DeepSeek 模型完整指南"
date: "2026-04-30T18:32:10+08:00"
slug: "awesome-deepseek-agent-integration-guide"
github_repo: "deepseek-ai/awesome-deepseek-agent"
source_key: "gh:deepseek-ai/awesome-deepseek-agent"
description: "基于 DeepSeek 官方仓库 awesome-deepseek-agent，梳理 23 款 AI 编程助手接入 DeepSeek-V4 的三种模式（Anthropic 兼容、OpenAI 兼容、模型直连），给出配置方法、选型建议与常见问题。"
draft: false
categories: ["技术笔记"]
tags: ["DeepSeek", "AI 编程", "Claude Code", "Agent Skills", "OpenClaw"]
---

# Awesome DeepSeek Agent：23 款主流 AI 编程助手接入 DeepSeek 模型完整指南

awesome-deepseek-agent 仓库把 23 款 AI 编程助手接 DeepSeek-V4 的方式收敛成三种接入模式：Anthropic 兼容、OpenAI 兼容、模型直连。已经用 Claude Code 的开发者改几个环境变量就能切换；从零开始的人选 Reasonix 或 Deep Code 走向导；要接飞书、微信的人看 OpenClaw 或 AstrBot。本文按这三种模式拆解配置步骤，并给出按场景和接入难度排序的选型建议。

## 目录

- [1. 项目概览](#1-项目概览)
- [2. 三种接入模式](#2-三种接入模式)
- [3. 23 款工具全景图](#3-23-款工具全景图)
- [4. Anthropic 兼容模式详解](#4-anthropic-兼容模式详解)
- [5. OpenAI 兼容模式详解](#5-openai-兼容模式详解)
- [6. 模型直连模式详解](#6-模型直连模式详解)
- [7. 选型建议](#7-选型建议)
- [8. 成本参考](#8-成本参考)
- [9. 常见问题](#9-常见问题)
- [10. 官方资源](#10-官方资源)

---

## 1. 项目概览

| 项目 | 信息 |
|------|------|
| **仓库** | [deepseek-ai/awesome-deepseek-agent](https://github.com/deepseek-ai/awesome-deepseek-agent) |
| **创建时间** | 2026-04-27 |
| **Stars / Forks** | 6,149 / 739（2026-09-28 读数；2026-04-30 创建初期为 360+ / 25+） |
| **官方文档** | [DeepSeek Platform](https://platform.deepseek.com/) · [API Docs](https://api-docs.deepseek.com/) |
| **覆盖工具数** | README 目录表 23 款（docs/ 另有一份未列入目录的 Factory AI Droid 指南） |

[awesome-deepseek-agent](https://github.com/deepseek-ai/awesome-deepseek-agent) 是 DeepSeek 官方维护的精选指南仓库，每款工具对应一份独立的 `docs/<tool-name>.md` 文档，涵盖安装、配置和首次运行三个步骤。文档提供英文和简体中文两个版本（`docs/<tool-name>.zh-CN.md`），由 DeepSeek 团队持续更新。仓库从 2026 年 4 月创建初期的 16 款工具扩展到现在的 23 款，半年间新增了 DeepSeek-TUI、Codex、Cherry Studio、LobeHub、Cline、Qwen Code、Qoder 七款。

这个仓库适合已经在用 DeepSeek 模型、想把它接入日常编程工具链的开发者。如果你还没有 DeepSeek API Key，需要先到 [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys) 申请。

---

## 2. 三种接入模式

23 款工具的接入方式各异，但底层依赖的 API 协议只有三种。理解这三种模式后，任意工具的接入路径都可快速判断：

| 模式 | API 端点 | 适用工具 |
|------|----------|----------|
| **Anthropic 兼容** | `https://api.deepseek.com/anthropic` | Claude Code、GitHub Copilot CLI、Codex（经 Moon Bridge 转发层） |
| **OpenAI 兼容** | `https://api.deepseek.com` | WorkBuddy/CodeBuddy、Kilo Code、OpenCode、Crush、Pi、nanobot、Langcli |
| **模型直连** | 内置 DeepSeek 支持 | Deep Code、Reasonix、DeepSeek-TUI、OpenClaw、AstrBot、Hermes、Cherry Studio、Cline、LobeHub、Qoder、Qwen Code、GitHub Copilot（扩展） |

不同工具最初对接的 API 协议不同。Claude Code 天然对接 Anthropic 协议，DeepSeek 在 Anthropic 兼容端点上做了协议适配；大多数开源工具走 OpenAI 协议，DeepSeek 的主端点同样兼容；Codex 只说 OpenAI Responses API，需要再架一层转发服务（Moon Bridge）把请求路由到 Anthropic 兼容端点。Reasonix、Deep Code 这类专为 DeepSeek 打造的工具直接调用原生 API，不涉及协议转换。

选工具时，先确认它支持哪种协议，再对照上表找到对应的配置方式。

---

## 3. 23 款工具全景图

### 编程助手类

| 工具 | 说明 | 接入模式 |
|------|------|----------|
| **Claude Code** | Anthropic 官方终端编程助手（也有 VS Code 扩展形态），通过 `ANTHROPIC_BASE_URL` 指向 DeepSeek 的 Anthropic 兼容端点接入 | Anthropic 兼容 |
| **Codex** | OpenAI 的编程 Agent，需搭配 Moon Bridge 转发层使用 | Anthropic 兼容（转发层） |
| **GitHub Copilot** | VS Code 内置的 AI 编程助手，安装 "DeepSeek V4 for Copilot Chat" 扩展后模型直接进入 Copilot 选择器 | 扩展直连 |
| **GitHub Copilot CLI** | 终端版 Copilot，支持 Agent 能力，通过 Anthropic 兼容端点接入 | Anthropic 兼容 |
| **Kilo Code** | CLI 和编辑器插件双形态的 AI 编程助手，`/connect` 命令选择 DeepSeek | OpenAI 兼容 |
| **Langcli** | 100% 兼容 Claude Code 的开源编程助手，支持 CLI 和 Zed ACP Agent | OpenAI 兼容 |
| **OpenCode** | 开源多形态 AI 编程助手，支持终端 / Web 等，通过 `/connect deepseek` 命令接入 | OpenAI 兼容 |
| **Cline** | VS Code 扩展形式的 AI 编程助手，支持多种 API Provider，内置 DeepSeek 选项 | 内置 Provider |
| **Qoder** | IDE / CLI / JetBrains 插件三形态 Agentic Coding 产品，内置 DeepSeek 模型，也支持自定义模型 | 内置 Provider |
| **Qwen Code** | 阿里通义千问团队开发的终端编程 Agent，将 DeepSeek 列为内置第三方 Provider | 内置 Provider |

### 终端 Agent 类

| 工具 | 说明 | 接入模式 |
|------|------|----------|
| **Deep Code** | 专为 DeepSeek-V4 打造的终端编程助手，支持深度思考、推理力度控制和 Agent Skills | 直连 |
| **DeepSeek-TUI** | Rust 编写的终端编程助手，Codex 风格 13-crate 工作区架构，沙箱化工具执行，内置 MCP 客户端与服务器，支持完整 1M 上下文 | 直连 |
| **Reasonix** | DeepSeek 原生终端 Agent，缓存优先循环、Flash 优先的成本控制、自动修复工具调用 | 直连 |
| **Pi** | 极简且高度可扩展的终端编码框架，支持树状会话和自定义 Provider | OpenAI 兼容 |
| **Crush** | 支持多模型的终端 AI 编程 Agent，集成 LSP | OpenAI 兼容 |
| **Oh My Pi** | 基于 Pi 分支扩展的终端编程 Agent，提供 OMP 专用工具、模型角色、MCP、插件与 Agent 工作流 | OpenAI 兼容 |

### 跨平台 Agent 类

| 工具 | 说明 | 接入模式 |
|------|------|----------|
| **OpenClaw** | 开源个人 AI 助手，通过 Skill 扩展，接入飞书、微信等聊天平台 | 直连 |
| **AstrBot** | 开源一站式 Agent 助手，支持 QQ、微信、飞书、Telegram 等消息平台，可通过技能、插件和 MCP 扩展 | 直连 |
| **WorkBuddy / CodeBuddy** | 支持自定义 OpenAI 兼容模型配置的 AI Agent 与编程助手 | OpenAI 兼容 |
| **Hermes** | Nous Research 打造的开源自我进化 AI Agent，向导中选 DeepSeek Provider | 直连 |

### 其他

| 工具 | 说明 | 接入模式 |
|------|------|----------|
| **Cherry Studio** | 开源跨平台桌面 AI 客户端，内置 300+ 预设助手、知识库、MCP 服务与多模型对话 | 内置 Provider |
| **LobeHub** | Agent 编排平台，设置 → 服务模型中选择 DeepSeek | 内置 Provider |
| **nanobot** | 开源轻量级 AI 智能体，支持接入聊天工具、记忆、MCP 等 | OpenAI 兼容 |

---

## 4. Anthropic 兼容模式详解

Anthropic 兼容模式适用于原本对接 Anthropic `/v1/messages` 接口的工具。DeepSeek 在 `https://api.deepseek.com/anthropic` 部署了一个协议适配层，这些工具因此可以零改动切换到 DeepSeek 模型。

### Claude Code 配置

Claude Code 是这一模式下最典型的工具。安装后，通过环境变量将请求指向 DeepSeek（仓库指南给出的配置）：

```bash
# 安装 Claude Code（需 Node.js 18+）
npm install -g @anthropic-ai/claude-code

# 配置环境变量（指向 DeepSeek Anthropic 兼容端点）
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_AUTH_TOKEN=<your DeepSeek API Key>
export ANTHROPIC_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-v4-pro[1m]
export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-v4-flash[1m]
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
export CLAUDE_CODE_EFFORT_LEVEL=max
```

配置要点：

- `deepseek-v4-pro[1m]` 中的 `[1m]` 后缀表示使用 100 万 token 上下文窗口的变体。仓库指南把 Opus 和 Sonnet 角色都映射到 `deepseek-v4-pro`，Haiku 角色映射到 `deepseek-v4-flash[1m]`——主任务追求质量，子任务控制成本。
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` 关掉 Claude Code 的非必要请求（遥测、更新检查等），这些请求发往 Anthropic，切到 DeepSeek 后没有意义。
- `CLAUDE_CODE_EFFORT_LEVEL=max` 将推理力度拉满，充分利用 DeepSeek-V4-Pro 的推理能力。

模型名方面，2026-09-10 DeepSeek-V4.1-Flash 发布后，官方推荐新项目直接用 `deepseek-flash`：旧模型名 `deepseek-v4-flash`、`deepseek-v4-flash-vision-exp` 仍可调用，但对应模型已下线，请求由 DeepSeek-V4.1-Flash 提供服务并按 Flash 价格计费。DeepSeek 官方 API 文档的 [Claude Code 接入页](https://api-docs.deepseek.com/zh-cn/quick_start/agent_integrations/claude_code) 现行推荐的配置把三个角色全部指到 Flash，并多带两个变量：

```bash
export ANTHROPIC_MODEL=deepseek-flash[1m]
export ANTHROPIC_DEFAULT_OPUS_MODEL=deepseek-flash[1m]
export ANTHROPIC_DEFAULT_SONNET_MODEL=deepseek-flash[1m]
export ANTHROPIC_DEFAULT_HAIKU_MODEL=deepseek-flash
export CLAUDE_CODE_SUBAGENT_MODEL=deepseek-flash
export CLAUDE_CODE_EFFORT_LEVEL=max
export CLAUDE_CODE_AUTO_COMPACT_WINDOW=786432
```

如果请求传入的是 claude 系模型名，DeepSeek 的 Anthropic 端点会按名称前缀自动映射：`claude-opus` 开头的模型映射到 `deepseek-v4-pro`（按 V4 Pro 价格计费），`claude-haiku`、`claude-sonnet` 开头的模型映射到 `deepseek-flash`。这条映射也是在新版 Claude Desktop APP 的 developer 模式里接入 DeepSeek 的捷径——只改 `base_url` 和 `api_key` 即可。

Claude Code 的 Web Search 由 DeepSeek API 原生支持：模型判断需要联网搜索时会自动调用 Web Search 工具，通过 DeepSeek 提供的 API 执行搜索。调用该工具会产生额外的大模型 API 请求来总结搜索内容，因此会有额外的模型 token 费用。

### GitHub Copilot CLI 配置

Copilot CLI 同样通过 Anthropic 兼容端点接入（BYOK 模式，需 Node.js 22+，`npm install -g @github/copilot` 安装）。注意必须将 `COPILOT_PROVIDER_TYPE` 设为 `anthropic`，如果设为 `openai` 会触发 400 错误——原因是 DeepSeek 要求 `reasoning_content` 在多轮对话中原样回传，而 Copilot CLI 的 OpenAI 集成不支持这个行为。

```bash
export COPILOT_PROVIDER_TYPE=anthropic
export COPILOT_PROVIDER_BASE_URL=https://api.deepseek.com/anthropic
export COPILOT_PROVIDER_API_KEY=sk-your-deepseek-api-key
export COPILOT_MODEL=deepseek-v4-pro
```

可选：因为 `deepseek-v4-pro` 不在 Copilot CLI 的内置模型目录里，建议显式配置 token 上限，避免长上下文被截断：

```bash
export COPILOT_PROVIDER_MAX_PROMPT_TOKENS=840000
export COPILOT_PROVIDER_MAX_OUTPUT_TOKENS=128000
```

运行 `copilot help providers` 可查看全部可用环境变量。另有 `COPILOT_OFFLINE=true` 可屏蔽 GitHub API 调用（提示词仍会发送到 `api.deepseek.com`），适合只想连 DeepSeek 的场景。

### Codex 配置（Moon Bridge 转发层）

Codex 使用 OpenAI Responses API 与模型通信，不能直接填 Anthropic 端点。官方指南的做法是部署 [Moon Bridge](https://github.com/ZhiYi-R/moon-bridge) 作为转发层：Codex 把 Responses 请求发给本地的 Moon Bridge，再由它路由到 DeepSeek 的 Anthropic 兼容端点。前置要求 Node.js 18+ 和 Go 1.25+，Codex CLI 用 `npm install -g @openai/codex` 安装。

四步接入：

```bash
# 1. 克隆 Moon Bridge 并创建 config.yml（内容见下）
git clone https://github.com/ZhiYi-R/moon-bridge.git && cd moon-bridge

# 2. 启动转发层（监听 127.0.0.1:38440，提供 OpenAI Responses 兼容接口）
go run ./cmd/moonbridge --config config.yml

# 3. 另开终端，生成 Codex 的 config.toml 与 models_catalog.json 写入 ~/.codex/
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
MODEL="$(go run ./cmd/moonbridge --config config.yml --print-codex-model)"
go run ./cmd/moonbridge --config config.yml --print-codex-config "$MODEL" \
  --codex-base-url "http://127.0.0.1:38440/v1" \
  --codex-home "$CODEX_HOME_DIR" > "$CODEX_HOME_DIR/config.toml"

# 4. 进入项目目录启动 Codex
cd /path/to/my-project && codex
```

`config.yml` 的最小结构如下（`api_key` 换成你的 DeepSeek Key）：

```yaml
mode: "Transform"

server:
  addr: "127.0.0.1:38440"

models:
  deepseek-v4-pro:
    context_window: 1000000
    max_output_tokens: 384000
    default_reasoning_level: "high"
    supports_reasoning_summaries: true
    default_reasoning_summary: "auto"
    extensions:
      deepseek_v4:
        enabled: true

providers:
  deepseek:
    base_url: "https://api.deepseek.com/anthropic"
    api_key: "sk-your-deepseek-api-key"
    offers:
      - model: deepseek-v4-pro

routes:
  moonbridge:
    model: deepseek-v4-pro
    provider: deepseek

defaults:
  model: moonbridge
  max_tokens: 65536
```

两点注意：`models`（Codex 侧的模型元数据）、`providers`、`routes`、`defaults` 必须是顶层字段，旧版的 `provider.providers` 嵌套写法会报 `field provider not found`；需要图片输入、Web Search 或多 Provider 路由时，按 Moon Bridge 的 `config.example.yml` 扩展。Moon Bridge 还提供 `./scripts/start_codex_with_moonbridge.sh` 一键脚本，把启动代理、生成配置、拉起 Codex 合成一步。

### 从零接入 Claude Code

下面把上面的环境变量串成一个完整的接入流程：

1. 在 [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys) 申请 API Key，记为 `sk-xxx`。
2. `npm install -g @anthropic-ai/claude-code` 安装 Claude Code。
3. 把上面仓库指南那段 `export` 写入 `~/.zshrc` 或 `~/.bashrc`，将 `<your DeepSeek API Key>` 替换为 `sk-xxx`。
4. `source ~/.zshrc` 让环境变量生效。
5. 在项目目录运行 `claude`，第一次会引导登录——跳过 Anthropic 登录，因为 `ANTHROPIC_AUTH_TOKEN` 已经接管了认证。
6. 输入一个简单问题（如"解释这个仓库的目录结构"），如果返回正常且 `ANTHROPIC_MODEL` 被识别为 `deepseek-v4-pro[1m]`，接入完成。

如果第 6 步报 401，多半是 `ANTHROPIC_AUTH_TOKEN` 拼错或带了引号；报 404 则检查 `ANTHROPIC_BASE_URL` 末尾是否多了 `/v1`。

---

## 5. OpenAI 兼容模式详解

OpenAI 兼容模式覆盖的工具最多。将 `BASE_URL` 设为 `https://api.deepseek.com`，填入 API Key，工具便可通过标准的 OpenAI Chat Completions 协议调用 DeepSeek 模型。

### WorkBuddy / CodeBuddy 配置

WorkBuddy/CodeBuddy 通过用户级 `~/.codebuddy/models.json` 或项目级 `.codebuddy/models.json` 配置自定义模型，可以精细控制 token 上限、是否支持工具调用和图片。先将 Key 设置为环境变量 `DEEPSEEK_API_KEY`，再写入：

```json
{
  "models": [
    {
      "id": "deepseek-v4-pro",
      "name": "DeepSeek V4 Pro",
      "vendor": "DeepSeek",
      "url": "https://api.deepseek.com/v1/chat/completions",
      "apiKey": "${DEEPSEEK_API_KEY}",
      "maxInputTokens": 128000,
      "maxOutputTokens": 8192,
      "supportsToolCall": true,
      "supportsImages": false,
      "relatedModels": {
        "lite": "deepseek-v4-flash",
        "reasoning": "deepseek-v4-pro"
      }
    }
  ],
  "availableModels": ["deepseek-v4-pro", "deepseek-v4-flash"]
}
```

接口地址字段是 `url`。`apiKey` 引用 `${DEEPSEEK_API_KEY}` 可以避免 Key 落进版本库；如果 UI 中直接显示了 `${DEEPSEEK_API_KEY}` 原文，说明应用不是从设置了该变量的终端启动的，重启即可。官方文档特别提醒：`models.json` 必须保存为 UTF-8 无 BOM 编码，部分桌面版本读取带 BOM 的文件时会报"读取本地模型配置失败"。改完配置后需完全退出并重启应用，模型才会出现在选择器里。

### Oh My Pi 的兼容配置

Oh My Pi 自 v14.5 起内置了 DeepSeek 模型条目，但官方指南明确不建议直接用：内置条目缺少三个关键兼容字段，在 thinking mode 下带工具调用的长对话大概率返回 400。正确做法是创建 `~/.omp/agent/models.yml` 自定义配置，其中三项 compat 字段必配：

| 字段 | 值 | 含义 |
|------|----|------|
| `supportsToolChoice` | `false` | DeepSeek V4 的思考模式不支持 `tool_choice` 参数 |
| `requiresReasoningContentForToolCalls` | `true` | 多轮对话中必须保留 `reasoning_content` |
| `requiresAssistantContentForToolCalls` | `true` | 工具调用消息的 `content` 不能为 null |

配套要点：`baseUrl` 填 `https://api.deepseek.com`，不要加 `/v1`；`maxTokensField` 写 `max_tokens`（DeepSeek 不认 OpenAI 的 `max_completion_tokens`）；`supportsDeveloperRole` 设 `false`（系统提示词用 `system` 角色发送）。启动时用 `omp --model deepseek/deepseek-v4-pro` 指定模型，会话内 `/model` 或 `Ctrl+L` 切换。

这三项 compat 同样适用于其他走 OpenAI 兼容模式的工具——遇到工具调用报错时，优先核对工具是否踩了这三条 DeepSeek 协议边界。

---

## 6. 模型直连模式详解

直连模式的工具内置了对 DeepSeek 的支持，大多数不需要手动配置 API 端点。它们通常在首次运行时提供交互式引导，选择 DeepSeek 作为 Provider 后完成配置；个别工具（如 Hermes）仍要在向导里填一次 Base URL。

### Deep Code 配置

Deep Code 是专为 DeepSeek-V4 打造的终端编程助手，Node.js 18+ 环境安装：

```bash
npm install -g @vegamo/deepcode-cli
deepcode --version  # 验证安装
```

配置存储在 `~/.deepcode/settings.json`：

```json
{
  "env": {
    "MODEL": "deepseek-v4-pro",
    "BASE_URL": "https://api.deepseek.com",
    "API_KEY": "sk-..."
  },
  "thinkingEnabled": true,
  "reasoningEffort": "max"
}
```

配置项说明：

| 配置项 | 可选值 | 说明 |
|--------|--------|------|
| `MODEL` | `deepseek-v4-pro` / `deepseek-v4-flash` | 指定模型 |
| `BASE_URL` | API 地址 | 默认 `https://api.deepseek.com` |
| `thinkingEnabled` | `true` / `false` | 开启深度思考模式（deepseek-v4 模型默认开启） |
| `reasoningEffort` | `"max"` / `"high"` | 控制推理投入量，`max` 适合复杂任务，`high` 适合日常编码 |
| `webSearchTool` | `true` / `false` | 开启联网搜索功能 |
| `notify` | 脚本路径 | 每次模型回复完成后执行的回调脚本 |

这份 `settings.json` 与 Deep Code 的 VS Code 扩展共用。Deep Code 支持 Agent Skills 扩展机制，Skills 从 `~/.agents/skills/<name>/SKILL.md`（用户级）或 `./.deepcode/skills/<name>/SKILL.md`（项目级）自动发现，按 `/` 键打开技能选择器，或直接输入技能名（如 `/skill-writer`）。会话内常用操作：`Shift+Enter` 换行、`Ctrl+V` 粘贴图片、`Esc` 中断回复、`/new` 新对话、`/resume` 恢复历史对话。

### Reasonix 配置

Reasonix 是 DeepSeek 原生终端 Agent，无需全局安装：

```bash
npx reasonix code
```

首次运行时，Reasonix 会启动交互式向导，将配置持久化到 `~/.reasonix/config.json`。它有几个特点：

- **默认使用 Flash 模型控制成本**。日常编码任务走 `deepseek-v4-flash`，只在需要深度推理时通过 `/pro` 命令切换到 Pro 模型（仅下一轮生效），或通过 `/preset max` 让整个会话都使用 Pro。输入 `/help` 查看完整 slash 命令参考。
- **缓存优先循环**。围绕 DeepSeek API 的上下文缓存机制设计，减少重复 token 的计费。
- **自动修复工具调用**。当模型的工具调用格式出错时，Reasonix 会自动修复并继续执行，不会中断会话。

Reasonix 需要 Node.js 20.10+。

### DeepSeek-TUI 配置

DeepSeek-TUI 是 Rust 编写的开源终端编程助手，Codex 风格的 13-crate 工作区架构，原生对接 `api.deepseek.com`，支持 DeepSeek-V4-Pro 与 Flash 的完整 1M 上下文窗口，并在 macOS（Seatbelt）、Linux（Landlock）、Windows 上提供沙箱化工具执行。安装任选其一：`npm install -g deepseek-tui`（预编译二进制）、`cargo install deepseek-tui-cli`（需 Rust 1.85+）或从 GitHub Releases 下载。

首次运行 `deepseek auth` 会引导把 API Key 写入 `~/.deepseek/config.toml`，也可以直接设 `DEEPSEEK_API_KEY` 环境变量。默认模型为 DeepSeek-V4-Pro，按 `Shift+Tab` 切换推理强度（off → high → max），按 `Tab` 在 Plan（只读调研）/ Agent（工具调用需审批）/ YOLO（自动批准）三种模式间切换。它同时是 MCP 客户端与服务器（`deepseek mcp serve`），Skills 放在 `~/.deepseek/skills/<name>/SKILL.md`，`deepseek serve --http` 还能暴露 `/v1/*` 运行时 API 供 IDE 与 Web UI 集成。国内网络环境下可用 `DEEPSEEK_BASE_URL=https://api.deepseeki.com` 切换中国区端点。

### 内置 Provider 类工具

Cherry Studio、Cline、Qoder、Qwen Code、Hermes、LobeHub 这类工具把 DeepSeek 预置为可选 Provider，配置路径基本一致：在 Provider 列表里选 DeepSeek，填入 API Key。个别差异：

- **Cherry Studio**：设置 → 模型服务，在 Provider 列表找到"深度求索（DeepSeek）"，填 Key（API 地址保持默认 `https://api.deepseek.com`），点"获取模型列表"把 `deepseek-v4-pro` / `deepseek-v4-flash` 加入列表，再打开右上角开关。输入框工具栏的灯泡图标可调思维链长度，选"穷究"会自动映射为 `reasoning_effort: "max"`。
- **Cline**：设置中选 Bring my own API Key，然后二选一——API Provider 选 DeepSeek，或选 OpenAI Compatible 手动配 Base URL `https://api.deepseek.com`。注意官方指南的提醒：内置 DeepSeek Provider 的模型列表仍是 `deepseek-reasoner` / `deepseek-chat`（即将废弃），要用 V4 系列模型，需等 Cline 官方更新内置列表，或直接走 OpenAI Compatible 方式手动填 `deepseek-v4-pro`。
- **Qoder**：区分内置模型与自定义模型两种方式——内置模型在模型选择器直接选，走 Qoder Credits 计费；自定义模型在设置的"模型"面板添加（服务商选 DeepSeek，填 Key），费用由 DeepSeek API 账户结算，不占 Credits。CLI 里通过 `/model` → Custom 页签的向导添加，官方明确不建议手工改 `settings.json`。
- **Qwen Code**：Node.js 20+，`npm install -g @qwen-code/qwen-code@latest` 安装。会话内 `/auth` → Third-party Providers → DeepSeek API Key，粘贴 Key 并确认模型 ID（默认 `deepseek-v4-pro, deepseek-v4-flash`），再用 `/model` 切换。
- **Hermes**：一行脚本安装（`curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash`，唯一前置依赖是 Git），执行 `hermes setup` 选 Quick Setup，Provider 选 DeepSeek、填 Key，Base URL 填 `https://api.deepseek.com`，然后选 `deepseek-v4-pro`。
- **LobeHub**：设置 → 服务模型打开 DeepSeek Provider 页面（网页端可直达 `app.lobehub.com/settings/provider/deepseek`），填 Key，API 代理地址留空（默认端点即官方地址）。连通性检查默认用 `deepseek-v4-flash`；对话页右上角的推理强度提供 `none` / `high` / `max` 三档，复杂任务建议 `max`。自托管用户也可用 `DEEPSEEK_API_KEY` 环境变量在服务端全局配置。

### OpenClaw 和 AstrBot

两者都把 DeepSeek 预置为内置 Provider，但配置入口不同。

OpenClaw 走安装后的 setup 向导：`Model/auth provider` 选 DeepSeek、填 Key，`Default model` 填 `deepseek-v4-pro` 或 `deepseek-v4-flash`。安装用官方脚本 `curl -fsSL https://openclaw.ai/install.sh | bash`。注意版本：v2026.4.24 起才正确支持 DeepSeek V4 的 Thinking Mode，遇到 `reasoning_content` 相关的 400 报错，升级到最新版即可。日常入口有三个：`openclaw dashboard`（Web UI）、`openclaw tui`（终端 UI）和 `openclaw terminal`（终端聊天）。

AstrBot 在 Web UI 中配置：安装后打开 `http://localhost:6185`，左侧边栏进入"模型提供商"页面，点"+"新增并选择 DeepSeek，粘贴 Key 保存；再到"配置文件"页面把默认对话模型设为它。安装支持两种方式——官方脚本 `curl -LsSf https://docs.astrbot.app/install.sh | bash` 后 `astrbot init` / `astrbot run`，或克隆仓库后 `sudo docker compose up -d` 用 Docker 部署。

---

## 7. 选型建议

选工具时先看你的工具链已经有什么，再看候选工具走哪种接入模式，最后比较附加能力（Skills、多模型切换、消息平台集成）。

### 按使用场景选择

| 场景 | 推荐工具 | 理由 |
|------|----------|------|
| 已在使用 Claude Code，想降低模型成本 | Claude Code | 改几个环境变量即可，无需切换工具 |
| 从零开始，追求开箱即用 | Reasonix / Deep Code | 无需手动配置端点，向导式安装 |
| 需要接入飞书、微信、QQ 等国内平台 | OpenClaw / AstrBot | 内置消息平台集成 |
| 需要多模型切换 | Crush / Pi / Oh My Pi | 支持多个 Provider 并存 |
| 想要带沙箱和 MCP 服务端的终端 Agent | DeepSeek-TUI | 沙箱化工具执行 + 双向 MCP，开箱即用 |
| 团队统一模型底座 | WorkBuddy / CodeBuddy | 项目级 `.codebuddy/models.json` 可纳入版本管理 |

### 按接入难度排序

从低到高：

1. **Reasonix** — `npx reasonix code` 一行命令启动，向导完成配置
2. **Deep Code** — `npm install -g` 后配置 `settings.json`，字段直观
3. **DeepSeek-TUI** — `deepseek auth` 引导配置，沙箱工具开箱即用
4. **Claude Code** — 需要理解环境变量映射关系，但文档给出完整示例
5. **OpenClaw / AstrBot** — 配置简单，但涉及消息平台的额外设置
6. **WorkBuddy / Pi / Crush** — 需要手动编写 JSON 配置文件
7. **Codex** — 需要自建 Moon Bridge 转发层并维护 Go 环境

### 推荐顺序

个人开发者可以按 Reasonix → Deep Code → Claude Code 的顺序尝试：Reasonix 用来验证 DeepSeek-V4 是否满足你的编码需求，Deep Code 体验原生 Agent Skills 扩展，Claude Code 适合长期作为主力工具。团队环境优先评估 WorkBuddy / CodeBuddy，因为项目级配置可以纳入 Git 版本管理，便于团队统一模型底座。已经在用 Codex 的团队，Moon Bridge 方案多花一次部署成本，换来的是保留 Codex 工作流不变。

---

## 8. 成本参考

DeepSeek 自北京时间 2026-08-17 0 时起实行峰谷定价，2026-09-10 随 DeepSeek-V4.1-Flash 发布同步下调。以下为[官方定价页](https://api-docs.deepseek.com/zh-cn/quick_start/pricing)的现行价格（人民币，每百万 token）：

| 模型 | 计费项 | 高峰时段 | 空闲时段 |
|------|--------|----------|----------|
| `deepseek-flash`（V4.1-Flash） | 输入（缓存命中） | ¥0.04 | ¥0.02 |
| | 输入（缓存未命中） | ¥2.00 | ¥1.00 |
| | 输出 | ¥8.00 | ¥4.00 |
| `deepseek-v4-pro` | 输入（缓存命中） | ¥0.30 | ¥0.15 |
| | 输入（缓存未命中） | ¥9.00 | ¥4.50 |
| | 输出 | ¥27.00 | ¥13.50 |

- **峰谷时段**：北京时间周一至周五（不含法定节假日）9:00–12:00 与 14:00–18:00 为高峰时段；周末、法定节假日全天及其余时间为空闲时段，空闲价格为高峰的一半。批处理任务安排在空闲时段能直接省一半。
- **并发限制**：`deepseek-flash` 为 2500，`deepseek-v4-pro` 为 500。
- **模型名**：一律写 `deepseek-flash`。旧的 `deepseek-v4-flash`、`deepseek-v4-flash-vision-exp` 模型已下线，请求由 DeepSeek-V4.1-Flash 提供服务并按 Flash 价格计费。
- **Pro 的供应**：2026-09-14 之后 DeepSeek 继续提供 `deepseek-v4-pro` 的 API 调用服务，计费方式不变（官方更新日志原话）。

按缓存未命中价格算，Flash 的输入约为 Pro 的四分之一、输出约为三分之一；如果命中缓存，差距更大。日常编码任务用 Flash，遇到架构设计、复杂 bug 分析再切 Pro，是控制成本的主要手段。Reasonix 默认 Flash、需要时才切 Pro 的设计，正是基于这个价差。另外注意：图像理解能力目前只有 Flash 支持，Pro 是纯文本模型。

定价调整频繁，以上数据以 [DeepSeek 官方定价页](https://api-docs.deepseek.com/zh-cn/quick_start/pricing) 为准。

---

## 9. 常见问题

### Q：设置环境变量后 Claude Code 报认证错误

确认使用 `ANTHROPIC_AUTH_TOKEN` 字段（不要误用 `ANTHROPIC_API_KEY`），填的是 DeepSeek API Key，且没有多余的引号或空格。可以在终端运行 `echo $ANTHROPIC_AUTH_TOKEN` 检查实际值。

### Q：Copilot CLI 设为 `openai` 类型后报 400 错误

DeepSeek 要求多轮对话中的 `reasoning_content` 被原样回传，Copilot CLI 的 OpenAI 集成不处理这个字段。将 `COPILOT_PROVIDER_TYPE` 改为 `anthropic` 即可。

### Q：工具调用（Tool Call）报错或不生效

按工具类型排查。走 OpenAI 兼容模式的工具，对照 Oh My Pi 文档的三个 compat 字段（见第 5 节）：`tool_choice` 在思考模式下不支持、`reasoning_content` 必须保留、工具调用消息的 `content` 不能为空。用 OpenClaw 的，先升级到 v2026.4.24 以上。用 Cline 内置 DeepSeek Provider 的，注意其模型列表尚未包含 V4 系列。

### Q：应该选 Pro 还是 Flash？

需要深度推理（架构设计、复杂 bug 分析）用 Pro，日常补全、简单重构、文档编写用 Flash。Reasonix 的 `/pro` 命令提供了按需切换的能力，推荐先用 Flash，遇到瓶颈时再切 Pro。需要图像理解的任务只能用 Flash，Pro 是纯文本模型。

### Q：Anthropic 兼容端点和 OpenAI 兼容端点有什么区别？

两个端点都指向 DeepSeek 的同一组模型，区别在于请求/响应的协议格式。Anthropic 兼容端点（`/anthropic`）遵循 Anthropic Messages API 格式，OpenAI 兼容端点遵循 OpenAI Chat Completions 格式。选哪个取决于你的工具原生支持哪种协议，功能上没有差异。个别协议细节有边界，例如 Anthropic 端点不支持 `document` 类型的消息内容、`cache_control` 会被忽略，完整兼容性列表见[官方文档](https://api-docs.deepseek.com/zh-cn/guides/anthropic_api)。

---

## 10. 官方资源

- DeepSeek API Key 申请：[platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys)
- DeepSeek API 文档：[api-docs.deepseek.com](https://api-docs.deepseek.com/)
- 模型与价格：[api-docs.deepseek.com/zh-cn/quick_start/pricing](https://api-docs.deepseek.com/zh-cn/quick_start/pricing)
- Anthropic API 兼容性细节：[api-docs.deepseek.com/zh-cn/guides/anthropic_api](https://api-docs.deepseek.com/zh-cn/guides/anthropic_api)
- 仓库地址：[github.com/deepseek-ai/awesome-deepseek-agent](https://github.com/deepseek-ai/awesome-deepseek-agent)

---

## 参考来源与口径说明

- 仓库信息与各工具配置均对照 [deepseek-ai/awesome-deepseek-agent](https://github.com/deepseek-ai/awesome-deepseek-agent) main 分支（最后提交 2026-09-17）的 README 与 `docs/` 目录逐篇核实；"23 款"为 README 目录表行数口径（WorkBuddy/CodeBuddy 合并计一条），`docs/deepseek-droid-guide.md`（Factory AI Droid，配置 `~/.factory/settings.json` 的 `customModels`）未列入目录表。
- Stars/Forks 为 2026-09-28 GitHub API 读数；文中保留 2026-04-30 的创建初期读数作为增长对照。
- 定价与模型供应状态对照 api-docs.deepseek.com 的模型与价格页、更新日志（2026-09-28 读数）：峰谷定价自北京时间 2026-08-17 0 时生效，DeepSeek-V4.1-Flash 于 2026-09-10 发布，旧 Flash 模型名由 V4.1-Flash 接管并按 Flash 价格计费，`deepseek-v4-pro` 在 2026-09-14 之后继续提供服务且计费不变。
- 仓库 `docs/claude_code.zh-CN.md` 最后更新于 2026-05-02，其环境变量仍写 `deepseek-v4-pro` / `deepseek-v4-flash`；本文第 4 节同时给出该仓库指南口径与 api-docs 官方接入页现行推荐（`deepseek-flash` 系列），两者均为官方来源，模型名以官方定价页脚注的现行建议为准。
- 各工具的模型名（如 `deepseek-v4-pro`）沿用各接入指南原文，调用时以当期有效的模型名为准；价格、并发与模型供应状态可能调整，以官方定价页为准。
