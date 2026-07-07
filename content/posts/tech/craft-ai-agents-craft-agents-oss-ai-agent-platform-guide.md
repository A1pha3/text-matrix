---
title: "Craft Agents OSS 实战指南：从 6.6K Stars 的开源 Agent 桌面平台，到 Headless Server + CLI 的工程化落地"
date: "2026-07-02T21:02:26+08:00"
lastmod: "2026-07-02T21:02:26+08:00"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "MCP", "Electron", "Claude Agent SDK", "多LLM"]
description: "Craft Agents OSS 从 Electron 桌面拆到 Bun Headless Server + WebSocket RPC + CLI 三端，覆盖多 LLM 接入层与 Sources。"
slug: "craft-ai-agents-craft-agents-oss-ai-agent-platform-guide"
author: text-matrix
weight: 1
---

> **作者**：钳岳星君 🦞
> **仓库**：craft-ai-agents/craft-agents-oss（GitHub 主仓库 owner 由 lukilabs 迁至 craft-ai-agents，Apache 2.0）
> **数据来源**：仓库 `main` 分支 README、官方文档站 agents.craft.do、抓取时间 2026-07-02
> **版本对应**：本文对应 `main` 分支当前快照（README 与原 lukilabs 版本内容一致，主要变化是 owner 命名空间迁移 + 仓库内新增 Remote Server / CLI 子模块）

---

## 学习目标

读完本文，你应该能够：

- 说清 Craft Agents 的"Agent Native 软件原则"与"为人类设计"的传统软件到底差在哪。
- 画出 Desktop / Server / CLI 三端共用 WebSocket RPC 的结构，讲清它们如何共享 `packages/shared/`。
- 区分 Sources / Skills / Permission / Automations 四个子系统各自解决什么问题。
- 用 `craft-cli run` 一条命令跑通"自起 server → 发 prompt → 流式响应 → 退出"的完整链路。
- 判断哪些场景适合采用、哪些边界它覆盖不到（不是 Agent 框架、核心 LLM 不开源）。

## 目录

- [一句话压住全文](#一句话压住全文)
- [§1 Agent Native 原则到底改变了什么](#§1-agent-native-原则到底改变了什么)
- [§2 整体架构：Desktop / Server / CLI 三端共用 RPC](#§2-整体架构：desktop-server-cli-三端共用-rpc)
- [§3 核心子系统](#§3-核心子系统)
  - [3.1 Sources：把外部世界接进来](#31-sources：把外部世界接进来)
  - [3.2 Skills：可复用的 Agent 指令](#32-skills：可复用的-agent-指令)
  - [3.3 Permission Modes：三级权限 + 自定义规则](#33-permission-modes：三级权限-自定义规则)
  - [3.4 Automations：事件驱动的 Agent 工作流](#34-automations：事件驱动的-agent-工作流)
  - [3.5 Sessions：JSONL 持久化 + 动态状态](#35-sessions：jsonl-持久化-动态状态)
  - [3.6 大响应自动摘要](#36-大响应自动摘要)
- [§4 LLM 多提供商与第三方路由](#§4-llm-多提供商与第三方路由)
- [§5 安装、远程 Server 与 CLI 实战](#§5-安装、远程-server-与-cli-实战)
  - [5.1 一行安装](#51-一行安装)
  - [5.2 Headless Server 部署](#52-headless-server-部署)
  - [5.3 TLS（远程访问的标配）](#53-tls（远程访问的标配）)
  - [5.4 Docker](#54-docker)
  - [5.5 CLI 实战](#55-cli-实战)
  - [5.6 Debug 模式](#56-debug-模式)
- [§6 适用边界与上手建议](#§6-适用边界与上手建议)
  - [6.1 它解决了什么](#61-它解决了什么)
  - [6.2 它没解决的（边界）](#62-它没解决的（边界）)
  - [6.3 上手顺序建议](#63-上手顺序建议)
- [自测题](#自测题)
- [进阶学习路径](#进阶学习路径)

## 一句话压住全文

Craft Agents OSS 是一个**把 Agent Native 软件原则落到桌面 + Server + CLI 三端的开源平台**——用 Claude Agent SDK 和 Pi SDK 拼出多 LLM 接入层，把 MCP、REST API、本地文件系统统一抽象为 Sources，把可复用的指令变成 Skills，再用事件驱动的 Automations 把它们串起来；客户端可以是 Electron 桌面应用、Headless 远程服务器，也可以是命令行工具，三者共用同一套 WebSocket RPC。

下面按六条线展开：

- §1 Agent Native 原则到底改变了什么
- §2 整体架构：Desktop / Server / CLI 三端共用 RPC
- §3 核心子系统：Sources / Skills / Permission / Automations
- §4 LLM 多提供商与第三方路由
- §5 安装、远程 Server 与 CLI 实战
- §6 适用边界与上手建议

---

## §1 Agent Native 原则到底改变了什么

传统软件设计的隐含假设是"人类是操作者"：UI 按钮、菜单、表单、状态机，全都按人点击的节奏排列。当 AI Agent 接入这套软件，开发者要做的事情是把操作拆解成 API 调用、维护上下文状态、处理错误恢复——Agent 只是被外挂到一个为人类设计的系统里。

Craft Agents 的文档直接把这件事定义为"Agent Native 软件原则"：

> 自然语言优先 + 工具即服务 + 无配置体验 + 变更即时生效。

落到产品里，这条原则把三件事做实：

1. **不再写配置向导**。用户说"把 Linear 加成 Source"，Agent 自己找公共 API 文档、找 MCP server、读 OpenAPI 规范、配凭据。
2. **不再写配置文件迁移工具**。Claude Code 的 MCP config JSON 直接贴过来就能用，Skills 也是一句话导入。
3. **不再写"重启生效"逻辑**。新增 Source 或 Skill 用 `@` 在会话中即时挂载。

这条原则和仓库里强调的"We ourselves are building Craft Agents with Craft Agents only - no code editors"是同一件事——**自举开发**。如果产品本身用着别扭，作者会第一个知道。

---

## §2 整体架构：Desktop / Server / CLI 三端共用 RPC

仓库的 monorepo 结构非常清晰，能直接看出设计意图：

```
craft-agent/
├── apps/
│   ├── cli/                   # 终端客户端
│   └── electron/              # 桌面 GUI（主端）
│       └── src/
│           ├── main/          # Electron main 进程
│           ├── preload/       # context bridge
│           └── renderer/      # React UI（Vite + shadcn）
└── packages/
    ├── core/                  # 共享类型
    └── shared/                # 业务逻辑
        └── src/
            ├── agent/         # CraftAgent、权限
            ├── auth/          # OAuth、tokens
            ├── config/        # 存储、偏好、主题
            ├── credentials/   # AES-256-GCM 加密存储
            ├── sessions/      # 会话持久化
            ├── sources/       # MCP、API、本地源
            └── statuses/      # 动态状态系统
```

三个产品形态都接同一套 `packages/shared/`：

| 形态 | 角色 | 关键特性 |
|---|---|---|
| **Electron 桌面** | 主力客户端 | 多会话收件箱、可视化工具调用、状态工作流 |
| **Headless Server** | 远程宿主 | 在 VPS/服务器上常驻进程，桌面端以 thin-client 连入 |
| **CLI** | 脚本/CI 入口 | `craft-cli run` 一条命令自起 server + 发 prompt + 流式输出 + 退出 |

Server 与桌面端之间的通信走 WebSocket（`ws://` 或 `wss://`），端口默认 9100，鉴权用 Bearer Token，配置项集中在 7 个环境变量（`CRAFT_SERVER_TOKEN`、`CRAFT_RPC_HOST`、`CRAFT_RPC_PORT`、`CRAFT_RPC_TLS_CERT/KEY/CA`、`CRAFT_DEBUG`）。这种**前后端分离到不同进程**的做法，让"长会话跑在远端算力强的机器、UI 在笔记本上随手打开"成为默认形态，而不是要装额外插件。

值得注意的细节：

- **TLS 不是默认开**——`wss://` 需要自己提供 PEM 证书或前置 nginx/Caddy 反代。开发环境用仓库自带的 `./scripts/generate-dev-cert.sh` 生成 365 天自签证书。
- **本地 MCP server 与 server 进程隔离**：当 stdio MCP 在 server 端被 spawn 时，会过滤掉 `ANTHROPIC_API_KEY`、`AWS_ACCESS_KEY_*`、`GITHUB_TOKEN`、`OPENAI_API_KEY` 等敏感环境变量，避免泄漏到子进程。需要显式透传某个变量时，在 source config 里写 `env` 字段。

---

## §3 核心子系统

### 3.1 Sources：把外部世界接进来

Source 是统一抽象，分三类：

| 类型 | 示例 |
|---|---|
| **MCP Servers** | Craft、Linear、GitHub、Notion、自定义 server |
| **REST APIs** | Google（Gmail/Calendar/Drive/YouTube/Search Console）、Slack、Microsoft |
| **本地文件** | Filesystem、Obsidian vaults、Git repos |

接 MCP server 时可以选本地 stdio（npx、python 脚本、本地二进制）或远程 SSE。接 REST API 时把 OpenAPI 规范、endpoint URL 或文档截图直接给 Agent，让它读完自己拼好认证。Google 这类 OAuth 服务需要用户自己申请 Client ID/Secret——Agent 在 source 的 `config.json` 里写入 `googleOAuthClientId` / `googleOAuthClientSecret`，整套流程在 UI 内引导完成，不需要打开 Cloud Console 之外的工具。

凭据存储用 AES-256-GCM 加密，文件落在 `~/.craft-agent/credentials.enc`。主配置 `config.json` 不含敏感字段，可以进版本控制。

### 3.2 Skills：可复用的 Agent 指令

Skill 是 per-workspace 的专门指令，从 Claude Code 一键迁移过来。一个 Skill 本质上是带元数据的 Markdown 提示词，Agent 在判断场景相关时会自动加载。用 `@skill-name` 在会话中显式激活，可以跳过相关性判断。

文档给了一个直观的工作流：

> 用户：创建一个 GitHub PR 审查 Skill
> Agent → 理解需求 → 生成 Skill 定义 → 保存到工作区

不写代码、不改配置文件，所有变更即时生效。

### 3.3 Permission Modes：三级权限 + 自定义规则

权限系统三档默认模式，按 `SHIFT+TAB` 切换：

| 模式 | 显示 | 行为 |
|---|---|---|
| `safe` | Explore | 只读，拦截所有写操作 |
| `ask` | Ask to Edit | 每次写操作询问（默认） |
| `allow-all` | Auto | 自动放行所有命令 |

可以写自定义规则对特定工具/路径/参数做白名单或黑名单。在 Server 模式下也走同一套规则——权限不是客户端 UI 的装饰，是 Server 端真正的执行闸门。

### 3.4 Automations：事件驱动的 Agent 工作流

`automations.json` 把工作流从"会话内即时任务"扩展到"事件触发的新会话"。支持的事件覆盖了会话生命周期和外部钩子的全部主要节点：

| 事件类型 | 触发时机 |
|---|---|
| `LabelAdd` / `LabelRemove` | 会话标签变更 |
| `PermissionModeChange` | 权限模式切换 |
| `FlagChange` | 标记变化 |
| `SessionStatusChange` | 会话状态变更 |
| `SchedulerTick` | cron 触发（支持时区） |
| `PreToolUse` / `PostToolUse` | 工具调用前后 |
| `SessionStart` / `SessionEnd` | 会话起止 |

事件 action 是 `prompt`——触发时创建一个新的 Agent 会话，执行给定 prompt，prompt 内支持 `@source` 和 `@skill` 引用，环境变量 `$CRAFT_LABEL` / `$CRAFT_SESSION_ID` 自动展开。

文档里给的例子很典型：

```json
{
  "version": 2,
  "automations": {
    "SchedulerTick": [
      {
        "cron": "0 9 * * 1-5",
        "timezone": "America/New_York",
        "labels": ["Scheduled"],
        "actions": [
          { "type": "prompt", "prompt": "Check @github for new issues assigned to me" }
        ]
      }
    ],
    "LabelAdd": [
      {
        "matcher": "^urgent$",
        "actions": [
          { "type": "prompt", "prompt": "An urgent label was added. Triage the session and summarise what needs attention." }
        ]
      }
    ]
  }
}
```

每周一至五 9 点钟自动跑一次 GitHub 巡检；任何会话被贴上 `urgent` 标签就立刻拉起 triage 会话。这种"事件 → 新 Agent" 的模式把 Agent 从"被动等待用户提问的工具"变成了"能主动响应业务事件的工作单元"。

### 3.5 Sessions：JSONL 持久化 + 动态状态

会话数据按 JSONL 写入 `~/.craft-agent/workspaces/{id}/sessions/`，便于做时间旅行或事后审计。状态字段（Todo / In Progress / Needs Review / Done）是用户可定义的——`statuses/` 子模块允许每个工作区配自己的工作流阶段。状态本身也能触发 Automation。

会话命名支持 AI 自动生成（基于首条消息内容）或手动改名，标记（Flag）用于跨会话快速召回。

### 3.6 大响应自动摘要

超过约 60 KB 的工具响应会被自动用 Claude Haiku 摘要。MCP tool schema 注入 `_intent` 字段，让摘要保留与原始调用相关的关键信息，避免把最重要的部分砍掉。这是一个工程上很容易被忽略但很影响实际体验的细节——长上下文工具（MCP 搜索类、批量 list 类）常见返回几 MB，模型一旦直接吞就会卡顿或丢精度。

---

## §4 LLM 多提供商与第三方路由

Craft Agents 内部跑两套 agent 后端：

- **Claude backend**：Claude Agent SDK，支持 Anthropic API key、Claude Max/Pro OAuth、任意 Anthropic 兼容端点（OpenRouter / Vercel AI Gateway / Ollama / 自定义 URL）。
- **Pi backend**：Pi SDK 处理 Google AI Studio、ChatGPT Plus（Codex OAuth）、GitHub Copilot OAuth、OpenAI API key。

第三方和自托管通过 Claude backend 的自定义 base URL 接进来：

| 提供商 | Endpoint |
|---|---|
| OpenRouter | `https://openrouter.ai/api` |
| Vercel AI Gateway | `https://ai-gateway.vercel.sh` |
| Ollama | `http://localhost:11434` |
| Custom | 任意 OpenAI / Anthropic 兼容端点 |

这种"两套 backend + 任意兼容端点"的设计覆盖了几乎所有主流供给侧。CLI 层的 `--provider` 和 `--model` 直接透传到 SDK，`--base-url` 切到任意代理。

CLI 自带的 `--validate-server` 是 21 步集成测试，自动 spawn server（如果没指定 `--url`）然后跑完整 RPC 流程。这条命令的工程价值在于：把"启动 server、发请求、收响应、断连"做成可重放的冒烟测试，CI 里能直接挂。

---

## §5 安装、远程 Server 与 CLI 实战

### 5.1 一行安装

macOS / Linux：

```bash
curl -fsSL https://agents.craft.do/install-app.sh | bash
```

Windows PowerShell：

```powershell
irm https://agents.craft.do/install-app.ps1 | iex
```

从源码装（Bun 必备）：

```bash
git clone https://github.com/craft-ai-agents/craft-agents-oss.git
cd craft-agents-oss
bun install
bun run electron:start
```

### 5.2 Headless Server 部署

在远程 Linux VPS 上：

```bash
# 生成 token 并启动
CRAFT_SERVER_TOKEN=$(openssl rand -hex 32) bun run packages/server/src/index.ts
```

启动后打印：

```
CRAFT_SERVER_URL=ws://203.0.113.5:9100
CRAFT_SERVER_TOKEN=<generated-token>
```

桌面端以 thin-client 模式连入：

```bash
CRAFT_SERVER_URL=wss://203.0.113.5:9100 \
CRAFT_SERVER_TOKEN=<token> \
bun run electron:start
```

thin-client 模式下 UI 渲染仍在本地，但所有会话逻辑、工具调用、LLM 请求都跑在远端。

### 5.3 TLS（远程访问的标配）

生成自签证书（开发）：

```bash
./scripts/generate-dev-cert.sh
# 输出 certs/cert.pem 和 certs/key.pem（365 天有效）
```

启动带 TLS 的 server：

```bash
CRAFT_SERVER_TOKEN=<token> \
CRAFT_RPC_HOST=0.0.0.0 \
CRAFT_RPC_TLS_CERT=certs/cert.pem \
CRAFT_RPC_TLS_KEY=certs/key.pem \
bun run packages/server/src/index.ts
```

生产环境建议走 Let's Encrypt 或在前面挂 nginx/Caddy，由反向代理终结 TLS。

### 5.4 Docker

```bash
docker run -d \
  -p 9100:9100 \
  -e CRAFT_SERVER_TOKEN=<token> \
  -e CRAFT_RPC_HOST=0.0.0.0 \
  -v craft-data:/root/.craft-agent \
  craft-agents-server
```

挂证书：

```bash
docker run -d \
  -p 9100:9100 \
  -e CRAFT_SERVER_TOKEN=<token> \
  -e CRAFT_RPC_HOST=0.0.0.0 \
  -e CRAFT_RPC_TLS_CERT=/certs/cert.pem \
  -e CRAFT_RPC_TLS_KEY=/certs/key.pem \
  -v ./certs:/certs:ro \
  -v craft-data:/root/.craft-agent \
  craft-agents-server
```

### 5.5 CLI 实战

CLI 是 Craft Agents 区别于其他 Agent 桌面端最显著的一点——一条命令就能跑完整流程。

```bash
# 自包含：spawn server → 建会话 → 发 prompt → 流式响应 → 退出
craft-cli run "Summarize the README"

# 指定 workspace + source
craft-cli run --workspace-dir ./my-project --source github "List open PRs"

# 多 provider
craft-cli run --provider openai --model gpt-4o "Summarize this repo"
GOOGLE_API_KEY=... craft-cli run --provider google --model gemini-2.0-flash "Hello"
craft-cli run --provider anthropic --base-url https://openrouter.ai/api/v1 --api-key $OR_KEY "Hello"

# 验证 server 集成（21 步冒烟测试）
craft-cli --validate-server
```

`--validate-server` 不带 `--url` 时会自动 spawn server，对 CI 特别友好——可以把"server 能起来 + RPC 全链路通"做成 PR 检查。

### 5.6 Debug 模式

桌面端 debug 启动（注意是 `-- --debug`，双破折号把参数透传给 Electron 主进程）：

```bash
# macOS
/Applications/Craft\ Agents.app/Contents/MacOS/Craft\ Agents -- --debug

# Linux
./craft-agents -- --debug
```

日志位置：

| 系统 | 路径 |
|---|---|
| macOS | `~/Library/Logs/@craft-agent/electron/main.log` |
| Windows | `%APPDATA%\@craft-agent\electron\logs\main.log` |
| Linux | `~/.config/@craft-agent/electron/logs/main.log` |

---

## §6 适用边界与上手建议

### 6.1 它解决了什么

- **统一多 LLM 工作流**：不再为每个 provider 维护一个客户端。
- **外部服务零配置接入**：Sources + Skills 让"Agent 能做什么"变成可声明的。
- **远程长会话**：Server + WebSocket 把 Agent 从"绑在桌面"解放出来。
- **自动化事件响应**：Automations 让 Agent 从被动工具变为主动工作单元。

### 6.2 它没解决的（边界）

- **不是 Agent 框架**：和 LangChain、LlamaIndex 不在一个抽象层。它是端到端的 Agent 产品，不暴露底层 agent loop 给开发者改写。
- **不开源的核心是 LLM**：Claude Agent SDK 和 Pi SDK 都不是开源项目；OSS 部分是它们之上的封装和 UI 层。如果想完全自托管，需要把 Pi backend 替换掉或绕过。
- **OAuth 服务有摩擦**：Slack、Microsoft 的 OAuth 凭据需要在构建时烘入；Google 需要用户自己创建 OAuth client（README 给了完整 5 步流程）。生产部署前要评估这些摩擦。
- **CLI 是单机范式**：`craft-cli run` 每次都 spawn server，适合脚本/CI，不适合高频调用场景；高频场景应直接连已有的 server。

### 6.3 上手顺序建议

1. **第 1 天**：跑通一行安装 + 用 Anthropic API key 创建一个会话，验证基础 UI。
2. **第 2-3 天**：接一个 MCP server（推荐 Linear 或 GitHub），用 Skill 包装一个常用工作流。
3. **第 1 周**：写第一个 Automation（cron tick 或 Label 触发），体验事件驱动 Agent。
4. **第 2 周**：部署 Headless Server 到 VPS，桌面端切到 thin-client 模式；挂上 wss://。
5. **第 3 周**：用 CLI 把"读 GitHub issue + 写总结"集成到 CI pipeline，加 `--validate-server` 做冒烟测试。

到这一步，Craft Agents 才算从"高级聊天工具"升级成"团队 Agent 工作流平台"——这也正是它和其它 AI Agent 桌面应用拉开差距的真正分水岭。

---

## 自测题

1. Craft Agents 在 LLM 接入层用了哪两套 SDK？为什么不合并成一套？
2. Sources 的三类分别对应什么场景？Google OAuth 为什么要求用户自己建 client？
3. Automations 的 `SchedulerTick` 和 `LabelAdd` 触发后，实际做了什么动作？
4. thin-client 模式下，桌面端和远端 Server 的职责如何划分？
5. 为什么 CLI 的 `--validate-server` 在 CI 里特别有用？

## 练习

1. 用一行安装脚本装好桌面端，用 Anthropic API key 建第一个会话，确认 UI 能正常收发消息。
2. 接一个 MCP server（GitHub 或 Linear），然后用 `@skill` 在会话里激活一个你自己写的"PR 审查"Skill，验证 Skill 能即时挂载、即时生效。
3. 写一个 `automations.json`：给任意会话贴 `urgent` 标签时，自动拉起一个 triage 会话，把新消息归纳成三条要点。用 `LabelAdd` 的 `^urgent$` 匹配器验证触发链。
4. 在远程 VPS 上起 Headless Server（带 `CRAFT_SERVER_TOKEN`），本地桌面端用 `wss://` + thin-client 连入，确认长会话跑在远端、UI 在本地。
5. 用 `craft-cli run --provider openai --model gpt-4o "Summarize this repo"` 跑通一条非 Anthropic 后端的链路，再挂上 `--validate-server` 确认 RPC 全链路通。

## 进阶学习路径

- 仓库 `apps/cli/src/index.ts` 看 CLI 命令注册流程，理解 RPC channel 设计
- `packages/shared/src/sources/` 读 MCP、REST、local file 的统一抽象
- `packages/shared/src/agent/` 看 `CraftAgent` 类的权限注入和工具调度
- 翻一遍 `~/.craft-agent/workspace/{id}/automations.json` 真实事件触发链
- 在 VPS 上跑一遍 Server + TLS + thin-client 完整链路

## 常见问题 FAQ

**Q：Craft Agents 是 Agent 框架吗？能像 LangChain 那样改 agent loop 吗？**
不是。它和 LangChain / LlamaIndex 不在同一抽象层——是端到端的 Agent 产品，不把底层 agent loop 暴露给开发者改写。想完全自定义调度逻辑，得在它之外自己搭。

**Q：没有 Claude / Pi 的 SDK 能完全自托管吗？**
OSS 部分是 Claude Agent SDK 和 Pi SDK 之上的封装与 UI 层，这两个 SDK 本身不开源。只跑 Claude backend + 自托管兼容端点（OpenRouter / Ollama 等）是可行的；要把 Pi backend 也换掉，得自己替换或绕过那一层。

**Q：本地 MCP server 的敏感环境变量会泄漏到子进程吗？**
不会。Server 在 stdio 模式 spawn 本地 MCP 时，会过滤掉 `ANTHROPIC_API_KEY`、`AWS_ACCESS_KEY_*`、`GITHUB_TOKEN`、`OPENAI_API_KEY` 等，避免泄漏到子进程。需要透传某个变量，在 source config 里显式写 `env` 字段。

**Q：TLS 默认开吗？远程访问要怎么配？**
默认不开。`wss://` 需要自己提供 PEM 证书或前置 nginx / Caddy 反代；开发环境可用仓库自带 `./scripts/generate-dev-cert.sh` 生成 365 天自签证书。

**Q：`craft-cli run` 每次都起 server，高频调用会不会很慢？**
会。CLI 是单机 / 脚本范式，每次 spawn server，适合低频脚本与 CI。高频场景应直接连一个已常驻的 Server，而不是每条命令都重新起进程。

**Q：OAuth 接入（Slack / Microsoft / Google）摩擦大吗？**
有摩擦。Slack、Microsoft 的 OAuth 凭据需要在构建时烘入；Google 要求用户自己创建 OAuth client（README 给了完整 5 步流程）。生产部署前要先把这批接入成本评估进去。