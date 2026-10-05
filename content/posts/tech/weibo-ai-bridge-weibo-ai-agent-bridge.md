---
title: "kangjinshan/weibo-ai-bridge：微博私信与AI Agent的桥接服务，支持Claude/Codex/Hermes/Gemini"
slug: weibo-ai-bridge-weibo-ai-agent-bridge
github_repo: "kangjinshan/weibo-ai-bridge"
source_key: "gh:kangjinshan/weibo-ai-bridge"
date: "2026-04-22T20:57:00+08:00"
lastmod: "2026-09-28"
description: "weibo-ai-bridge 是用 Go 语言开发的微博私信与 AI Agent 桥接服务，通过 WebSocket 连接微博开放平台，把私信路由给 Claude Code、Codex、Hermes、Gemini 四种 CLI Agent，支持流式回复、交互式审批和原生会话续接。"
categories: ["技术笔记"]
tags: ["Go", "AI Agent", "WebSocket"]
---

# 用 weibo-ai-bridge 把微博私信接进 Claude、Codex、Hermes 或 Gemini

你想在微博私信里直接聊天、让 AI 帮忙写东西或者回答粉丝提问，但 Claude Code 这类 Agent 只活在命令行里，微博用户够不到。`weibo-ai-bridge` 解决的就是这一段距离——它是开发者 [kangjinshan](https://github.com/kangjinshan) 开源的 Go 服务，架在微博开放平台和本地 Agent CLI 之间：私信从微博进来，路由给 Claude Code、Codex、Hermes 或 Gemini，Agent 的输出再流式地送回去。

学完本文你可以：搭起这个桥接服务、把微博私信接给任意一种 Agent、理解每条私信如何流过五层组件，并能在连接断开或卡顿的时候定位问题。

> **GitHub**: [kangjinshan/weibo-ai-bridge](https://github.com/kangjinshan/weibo-ai-bridge)  
> **Stars**: 4 ⭐（2026-09-28 读数）  
> **语言**: Go（另含 Shell、JavaScript 脚本）  
> **创建时间**: 2026-04-20  
> **最新版本**: v1.2.0（2026-06-23）  
> **许可证**: MIT（README 声明，仓库无独立 LICENSE 文件）

本文以 v1.2.0 为口径。这个项目迭代很快，命令、配置项以你拉到的版本为准。

---

## 为什么需要这个桥接层

直接让微博业务代码去调 Agent 命令行会踩三个坑：

1. **微博是长连接**：微博开放平台靠 WebSocket 推送私信，需要一直维持连接、处理心跳和重连。这套逻辑不该散落在业务代码里。
2. **Agent 是异步的**：Claude 回复是一段一段吐出来的，中间耗时可能几十秒。微博私信要求你在收到消息时尽快回应，不然可能被当作超时。
3. **会话要跨消息续接**：同一用户连续问几轮，Agent 要知道前面聊了什么。会话记在哪里、什么时候清，必须有个统一的地方管。

`weibo-ai-bridge` 把这三点收敛成一个独立服务，业务侧只对接一个稳定的 WebSocket 入口。

---

## 核心架构

代码按目录分成五层，消息在层与层之间单向流动，每层只管自己那一件事。

```
┌─────────────────────────────────────────────────────────┐
│                    Weibo AI Bridge                       │
├─────────────────────────────────────────────────────────┤
│  Platform Layer  │  平台接入（微博 WebSocket / 本地调试） │
├─────────────────┼──────────────────────────────────────┤
│  Router Layer    │  消息路由、命令处理、审批与流式回传    │
├─────────────────┼──────────────────────────────────────┤
│  Agent Layer     │  Agent 接口封装（Claude/Codex/       │
│                  │  Hermes/Gemini）                     │
├─────────────────┼──────────────────────────────────────┤
│  Session Layer   │  会话索引与状态持久化                │
├─────────────────┼──────────────────────────────────────┤
│  Config Layer    │  配置加载（环境变量 / TOML / 默认值） │
└─────────────────────────────────────────────────────────┘
```

一条私信的完整路径是：

```
微博私信 → WebSocket → Platform (platform/weibo/client.go)
                                ↓
                     Router (router/router_core.go)
                                ↓
                     Session Manager (session/session.go)
                                ↓
                     Agent Manager (agent/manager.go)
                                ↓
                     Claude / Codex / Hermes / Gemini Agent
                                ↓
                     Router 流式回传 → Platform → WebSocket → 微博用户

会话持久化:
Session Manager → ~/.config/weibo-ai-bridge/sessions/
```

收到消息后，Router 先确认是普通聊天还是 `/` 开头的命令，再按会话把消息交给 Agent；Agent 的回复沿原路流式返回，会话状态按用户落盘。

---

## 核心行为

### 私信是实时接的

通过微博开放平台的 **WebSocket API** 接收和发送私信，项目维护了长连接、心跳和超时，断线会自动重连。服务启动成功后，Bridge 会连上微博 WebSocket，并给 bot 自己发一条启动通知——看到这条通知就知道链路通了。

### 四种 Agent 都能接

| Agent | CLI 命令 | 说明 |
|-------|---------|------|
| **Claude Code** | `claude` | 找不到 `claude` 时会退而尝试 `cc` |
| **Codex** | `codex` | 支持本地 app-server WebSocket 协议 |
| **Hermes** | `hermes` | 走 ACP 主链路 |
| **Gemini** | `gemini` | 沿用本机 Gemini CLI 的登录态或 `GEMINI_API_KEY` |

启动时逐个探测本机 PATH 里有没有对应 CLI（内部用 Go 的 `exec.LookPath()`），探测得到才注册进 Agent 管理器；多种同时可用时默认用 Claude Code。你可以在私信里随时切换 Agent，详见后文的命令表。

### 会话按用户续接

Bridge 优先使用各 Agent 自己的 session/thread ID 来续接上下文，自己只维护一份索引、当前活动会话和必要上下文——也就是说，多轮对话的"记忆"由 Agent CLI 原生管理，Bridge 负责把正确的会话 ID 绑定到正确的微博用户。会话索引持久化到 `SESSION_STORAGE_PATH`（默认 `~/.config/weibo-ai-bridge/sessions`），重启服务不丢。

### 回复是流式的，且对微博友好

收到私信先回一句「正在处理中」的提示，正文再按增量持续推给对方，优先在句号、换行、段落边界推送；中文按**字符**（rune）而不是字节计数分片，避免把一个字切成两半出乱码。为了让长回复可读，项目会引导 Agent 用简洁的 Markdown。

另一个容易忽略的点：Agent 请求授权（执行命令、写文件）时，审批提示会直接发到微博私信里，回复`允许`、`取消`或`允许所有`即可放行或拒绝，不用守在电脑前。

---

## 快速开始

### 你要先有

- **Go 1.22+**
- **微博开放平台 App ID / App Secret**
- **至少装好一个 Agent CLI**：`claude`、`codex`、`hermes` 或 `gemini`

### 装 Claude Code（如果还没装）

官方推荐的安装方式是脚本直装：

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

macOS 也可用 `brew install --cask claude-code`，Windows 用 `winget install Anthropic.ClaudeCode`。npm 方式（`npm install -g @anthropic-ai/claude-code`）仍可用，但官方已标记为不推荐。装完跑一次 `claude --version` 并完成登录认证。

### 拉取并构建

```bash
git clone https://github.com/kangjinshan/weibo-ai-bridge.git
cd weibo-ai-bridge

# 构建产物位于 build/weibo-ai-bridge
make build

# 开发时边改边跑可以用
make dev
```

### 获取微博凭证并填配置

在微博私信里找到「微博龙虾助手」，发送「连接龙虾」，即可拿到 App ID 和 App Secret。然后把示例配置复制一份：

```bash
cp .env.example .env
```

编辑 `.env`，至少填入微博凭证并启用一个 Agent：

```bash
# 微博平台配置（必填）
WEIBO_APP_ID=your-app-id
WEIBO_APP_SECRET=your-app-secret

# 启用至少一个 Agent
CLAUDE_ENABLED=true
CODEX_ENABLED=false
HERMES_ENABLED=false
GEMINI_ENABLED=false
```

Claude 的 API Key 与模型由 Claude Code CLI 自己管理（`~/.config/claude/config.json` 或 `ANTHROPIC_API_KEY` 环境变量），Bridge 不重复配置。

验证这一步：`.env` 里微博凭证已填真实值，且 `claude --version` 能正常输出——任一缺失，对应链路都起不来。

### 启动

```bash
./build/weibo-ai-bridge
```

服务默认监听 `127.0.0.1:5533`，可用 `SERVER_PORT` 修改。

### 安装为常驻服务

Linux 和 macOS 用统一脚本（Linux 走 systemd，可用 `--scope system` 或 `--scope user` 选择作用域；macOS 走用户级 launchd）：

```bash
bash scripts/install.sh
scripts/service.sh start
scripts/service.sh status
scripts/service.sh logs
```

Windows 11 先构建再注册为 Windows 服务：

```powershell
go build -o build\weibo-ai-bridge.exe .\cmd\server
.\scripts\service.ps1 install
.\scripts\service.ps1 start
```

注意：如果 Agent CLI 的登录态只存在于当前桌面用户环境，优先前台运行；确实要装后台服务时，确保服务账号也完成对应 CLI 的登录。

---

## 配置项速查

配置优先级：**环境变量 > TOML 配置文件 > 默认值**。启动时自动读取 `.env`，TOML 路径用 `CONFIG_PATH` 指定（默认 `config/config.toml`），完整示例见 `.env.example` 和 `config/config.example.toml`。

### 微博平台与服务器

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `WEIBO_APP_ID` | 微博应用 ID | 必填 |
| `WEIBO_APP_SECRET` | 微博应用密钥（兼容旧名 `WEIBO_APP_Secret`） | 必填 |
| `SERVER_PORT` | HTTP 端口 | `5533` |
| `HTTP_API_KEY` | `/stats`、`/chat/stream` 的 Bearer Token，留空不启用认证 | 空 |
| `CONFIG_PATH` | TOML 配置文件路径 | `config/config.toml` |

### Agent

Agent 的 API Key、模型和 provider 通常由各自 CLI 管理，除非需要覆盖，`CODEX_MODEL`、`HERMES_MODEL`、`HERMES_PROVIDER`、`GEMINI_MODEL` 建议留空，沿用本机 CLI 默认配置。

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `CLAUDE_ENABLED` | 启用 Claude Code | `true` |
| `CODEX_ENABLED` | 启用 Codex | `false` |
| `HERMES_ENABLED` | 启用 Hermes | `false` |
| `GEMINI_ENABLED` | 启用 Gemini | `false` |

Codex 若走 Azure OpenAI provider，还需按 `.env.example` 里的注释补 `AZURE_OPENAI_*` 四个变量。

### 会话与日志

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `SESSION_STORAGE_PATH` | 会话索引持久化目录 | `~/.config/weibo-ai-bridge/sessions` |
| `SESSION_TIMEOUT` | 会话超时（秒） | `3600` |
| `SESSION_MAX_SIZE` | 最大会话历史条数 | `1000` |
| `LOG_LEVEL` | 日志级别 | `info` |
| `LOG_FORMAT` | 日志格式 | `json` |
| `LOG_OUTPUT` | 日志输出 | `stdout` |

---

## HTTP 调试接口

服务默认监听 **127.0.0.1:5533**，暴露三个接口。

| 接口 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/stats` | GET | 会话数量与消息统计 |
| `/chat/stream` | GET/POST | SSE 调试流 |

设置 `HTTP_API_KEY` 后，`/stats` 和 `/chat/stream` 需要带 `Authorization: Bearer <api_key>`；`/health` 始终免认证。

**健康检查**

```bash
curl http://localhost:5533/health
```

**模拟一条私信调试**

```bash
curl -N \
  -H "Content-Type: application/json" \
  -d '{"user_id":"123456","content":"请用中文写三段文字"}' \
  http://127.0.0.1:5533/chat/stream
```

SSE 事件类型有八种：`session`、`delta`、`message`、`approval`、`tool_start`、`tool_end`、`error`、`done`。排障时先看 `/stats`，能快速判断到底是 Agent 慢还是连接断了。

---

## 私信命令

用户在微博私信里发这些命令控制服务行为：

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助 |
| `/new [claude\|codex\|hermes\|gemini]` | 准备下一条消息使用的新原生会话 |
| `/list` | 查看可切换的原生会话列表 |
| `/switch <编号>` / `/<编号>` | 切换到 `/list` 中的会话 |
| `/switch <agent>` | 切换当前会话的 Agent 类型 |
| `/claude`、`/codex`、`/hermes`、`/gemini` | 快速切换 Agent |
| `/dir [path]` | 查看或设置当前会话工作目录 |
| `/model` | 显示当前模型 |
| `/status` | 显示当前会话状态 |
| `/btw <内容>` | 向运行中的 turn 注入补充说明 |
| `/listen [编号]` / `/unlisten` | 旁听本机已有原生会话日志 / 停止旁听 |
| `/simple [on\|off\|status]` | 简洁模式：只发最终回复 |
| `/super [on\|off\|status]` | Super 模式：自动审批 + 对侧 Agent 复盘 |
| `/upgrade [--ref branch\|tag]` | 比对本地与目标 commit，有新版才构建并延迟重启 |

审批提示出现时，直接回复即可：`允许` / `同意` / `yes` / `approve` 放行，`取消` / `no` / `reject` 拒绝，`允许所有` / `allow all` 对当前会话放行所有后续审批。Claude 发起结构化选择题时，选项会被渲染成编号文本，回复编号即可，多选用逗号分隔。

---

## 微博能力：让 Agent 也会刷微博

内置的 `skills/weibo-skill-api/` 是 Agent 使用微博开放能力的入口。`scripts/install.sh` 安装 Bridge 时，会把这些 skill 同步到 `~/.claude/skills/`、`~/.codex/skills/` 等目录，四种 Agent 共享同一套微博凭证与 token 缓存，不需要在各 Agent 侧单独登录。

装好之后，Agent 能做的事情超出"聊天"很多：查热搜榜和微博智搜、查单条微博状态、超话发帖评论点赞、上传图片视频、管理定时微博，还能拉创作者数据分析（金橙 V 升级、V 榜、粉丝群、内容效率）和激励计划数据。让微博上的粉丝问一句"今天热搜有什么"，Agent 真的去查了再回答。

skill 单独损坏或需要修复时：

```bash
bash scripts/install-skills.sh
```

---

## 测试与代码质量

```bash
# 运行测试（含 -race 和覆盖率统计）
make test

# 生成覆盖率 HTML 报告
make test-coverage

# 生成可读测试报告到 reports/
make test-report
```

```bash
# 格式化代码
make fmt

# 运行 golangci-lint
make lint

# 交叉编译 Linux / Windows
make build-linux
make build-windows

# 清理构建产物
make clean
```

改代码前先 `make fmt && make lint`，改完跑 `make test`，问题会提前暴露在本地，而不是部署之后。

---

## 常见问题排查

| 问题 | 解决方法 |
|------|---------|
| 配置验证失败 | 检查 `WEIBO_APP_ID` 和 `WEIBO_APP_SECRET` 是否已填 |
| Claude 不可用 | 确认 `claude --version` 可用，且 Claude Code CLI 已完成认证 |
| Codex 不可用或模型不匹配 | 确认 `codex` 可用；`CODEX_MODEL` 优先留空，沿用 CLI 默认配置 |
| Hermes 不可用 | 确认 `hermes --version` 和 `hermes acp` 可用 |
| Gemini 不可用 | 确认 `gemini --version` 可用，检查登录状态或 `GEMINI_API_KEY` |
| WebSocket 频繁断连 | 查网络稳定性、微博凭证与 token 是否过期、是否撞上微博 API 调用限制 |
| 回复慢或卡住 | 先看 `/stats` 接口定位是 Agent 慢还是连接断；再排查服务器资源 |
| 会话丢失 | 检查 `SESSION_STORAGE_PATH` 目录和服务运行账号是否有写权限 |

需要更细的日志时，把 `LOG_LEVEL` 调成 `debug` 重启。

---

## 接入新 Agent 的扩展点

要接第三种、第五种 Agent，有四步：

1. 在 `agent/` 下新建文件，实现 `Agent` 接口：

```go
type Agent interface {
    // Name 返回 Agent 名称
    Name() string

    // ExecuteStream 执行 AI 任务并返回事件流
    ExecuteStream(ctx context.Context, sessionID string, input string) (<-chan Event, error)

    // IsAvailable 检查 Agent 是否可用
    IsAvailable() bool
}
```

事件是结构化的 `Event`，类型涵盖 `session`、`delta`（增量文本）、`approval`（审批请求）、`tool_start`/`tool_end`、`error`、`done` 等。要支持多轮原生会话和运行中审批，再实现 `InteractiveAgent` 接口（提供 `StartSession`，返回可 `Send`、可 `RespondApproval`、可 `Events` 的 `InteractiveSession`）。

2. 在 `cmd/server/main.go` 里按配置构造实例，调用 `agent/manager.go` 的 `Register()` 注册；必要时用 `SetDefault()` 指定默认 Agent
3. 在 `.env.example`、`config/config.example.toml` 和 `config/config.go` 补新 Agent 的配置项
4. 补上测试

按这个接口，Agent 层面只关心"收到一条消息、吐出一条事件流"，接入微博和路由的复杂度都留在下层，所以新 Agent 的接入成本被压得很低——仓库里 Claude、Codex、Hermes、Gemini 四个实现就是四份现成的参考。

---

## 项目结构

```
weibo-ai-bridge/
├── cmd/server/              # 应用入口
│   ├── main.go              # 服务主程序，组装各层并注册 Agent
│   ├── platform.go          # 平台初始化
│   └── windows_service.go   # Windows 服务支持
├── platform/                # 平台适配器
│   ├── weibo/               # 微博 WebSocket 接入
│   │   ├── client.go        # 连接、心跳与重连
│   │   └── message.go       # 消息定义和解析
│   └── local/               # 本地调试平台适配
├── agent/                   # AI Agent 集成
│   ├── agent.go             # Agent/InteractiveAgent 接口与事件定义
│   ├── manager.go           # Agent 管理器（注册、解析、默认选择）
│   ├── claude.go            # Claude Code 实现
│   ├── codex.go             # Codex 实现
│   ├── codex_appserver.go   # Codex 本地 app-server 协议
│   ├── hermes.go            # Hermes 实现
│   ├── gemini.go            # Gemini 实现
│   └── prompt.go            # 提示词引导
├── session/                 # 会话管理
│   └── session.go           # 会话索引与持久化
├── router/                  # 消息路由
│   ├── router_core.go       # 路由主逻辑
│   ├── command.go           # / 命令处理
│   ├── router_approval.go   # 审批交互
│   ├── router_stream.go     # 流式回传
│   ├── native_sessions.go   # 原生会话索引与切换
│   └── self_update.go       # /upgrade 自升级
├── config/                  # 配置管理
│   ├── config.go            # 配置加载（环境变量 > TOML > 默认值）
│   └── config.example.toml  # TOML 示例
├── skills/weibo-skill-api/  # 微博能力 skill（文档 + 脚本）
├── scripts/                 # install.sh / service.sh / self-update.sh 等
├── deploy/                  # systemd / launchd 服务模板
├── docs/                    # 设计文档与维护记录
├── .env.example             # 环境变量示例
├── Makefile                 # 构建脚本
└── AGENTS.md                # 面向编码代理的仓库结构与约定
```

构建产物约定：`build/` 放本地构建产物，`dist/` 放发布包，仓库根目录不放可执行文件。

---

## 相关资源

| 资源 | 链接 |
|------|------|
| GitHub | [kangjinshan/weibo-ai-bridge](https://github.com/kangjinshan/weibo-ai-bridge) |
| Claude Code | [anthropics/claude-code](https://github.com/anthropics/claude-code) |
| Codex CLI | [openai/codex](https://github.com/openai/codex) |
| Gemini CLI | [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) |
| 微博开放平台 | [open.weibo.com](https://open.weibo.com/) |

---

## 自测清单

- 我能说出为什么需要独立桥接层，而不是让业务代码直接调 Agent
- 一条私信从微博到 Agent 再回微博，五层各做什么我能口述清楚
- `.env` 里微博凭证已填，`claude --version` 在本机有输出
- 审批提示来到私信里时，我知道回「允许」「取消」「允许所有」分别意味着什么
- 断线、回复慢时，我知道先查 `/stats` 接口，再看 `SESSION_STORAGE_PATH` 和 CLI 认证状态
- 想接第五种 Agent，我清楚改哪四处、以仓库里哪四个现成实现为参考

若需要继续深入，可以把这个项目当作一个"长连接 + 外部异步进程"的样例去读：先看 `platform/weibo/client.go` 的心跳与重连实现，再看 `agent/agent.go` 里 `Agent` 与 `InteractiveSession` 两级接口如何把"一次性问答"和"可审批的多轮会话"分开，最后读 `router/native_sessions.go` 理解 Bridge 怎么在微博用户和 Agent 原生会话之间牵线。
