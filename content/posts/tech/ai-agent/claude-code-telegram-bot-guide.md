---
title: "Claude Code Telegram Bot：远程访问 AI 编程助手的完全指南"
slug: "claude-code-telegram-bot-guide"
github_repo: "overwirehq/claude-code-telegram"
source_key: "gh:overwirehq/claude-code-telegram"
aliases:
  - /posts/tech/claude-code-telegram-bot-guide/
date: "2026-04-01T01:08:00+08:00"
lastmod: "2026-09-22T09:00:00+08:00"
categories: ["技术笔记"]
tags: ["Claude Code", "AI 编程", "Claude", "智能体", "Python", "自动化"]
description: "深度解析 Claude Code Telegram Bot（2.8k Stars，v1.7.0）：通过 Telegram 远程访问 Claude Code，支持智能体模式和经典终端模式，提供自然语言代码交互、会话持久化、Webhook 自动化、多层安全防护等 23 项功能特性，并给出部署建议与安全边界。"
---

# Claude Code Telegram Bot：远程访问 AI 编程助手的完全指南

> 预计阅读时间：25 分钟 | 难度：⭐⭐⭐

Claude Code 的能力一直在变强，但它的入口始终是那台装着终端的机器。这个项目（[overwirehq/claude-code-telegram](https://github.com/overwirehq/claude-code-telegram)）把入口搬进 Telegram：Claude Code 变成一个联系人，加错误处理、跑测试、查 issue、克隆仓库，都在对话里完成。它解决的不是"AI 编程不够好"，而是"人必须在电脑前"。

代价也要先说清楚：v1 目前一次只跑一个 Claude 请求（全局锁串行），Claude 发起的交互式提问你在 Telegram 上答不了，这两个限制官方 v2 路线图都列为要解决的问题。适合个人开发者和远程管理场景，不适合多人并发或对交互审批有强依赖的工作流。

## 学习目标

读完本文，你可以：

- 判断这个项目是否适合你的远程编程场景，以及该用哪种交互模式
- 完成安装、配置和 Claude 认证，把 bot 跑起来
- 配置 Webhook、定时任务和主动通知，实现事件驱动自动化
- 理解它的六层安全模型，以及 v1.7.0 修复工具边界检查带来的行为变化
- 用生产检查单和排查手册处理常见问题

---

## §1 项目概述

### 1.1 它是什么

**Claude Code Telegram Bot** 是一个把 Telegram 消息转发给 Claude Code 的 bot 服务。官方描述：

> A Telegram bot that gives you remote access to Claude Code. Chat naturally with Claude about your projects from anywhere -- no terminal commands needed.

背后的实现是 Claude Code Python SDK：bot 收到 Telegram 消息后交给 SDK 驱动 Claude Code 工作，Claude 的工具调用（读文件、改代码、跑命令）实时回显到聊天窗口。项目由 GitHub 用户 @RichardAtCT 发起，2026 年 9 月已迁移到 overwirehq 组织下维护。

### 1.2 核心数据

| 指标 | 数值（2026-09-22 读数） |
|------|------|
| **Stars** | 2,788 |
| **Forks** | 422 |
| **Watchers** | 13 |
| **提交数** | 255 |
| **发布版本** | 9 个（最新 v1.7.0，2026-09-11） |
| **贡献者** | 25 |
| **许可证** | MIT（README 声明；仓库未附 LICENSE 文件） |
| **测试规模** | 559 个测试，覆盖率 56%（v2 路线图基线口径） |

### 1.3 技术栈

| 类别 | 技术 | 占比 |
|------|------|------|
| **核心语言** | Python（要求 3.11+） | 99.6% |
| **构建** | Makefile（Poetry 管理依赖） | 0.4% |

### 1.4 功能概览

README 的 Working Features 清单列了 23 项，按用途归组如下：

| 类别 | 功能 |
|------|------|
| **交互** | 智能体模式（默认）、经典终端模式（13 命令 + 内联键盘）、可调详细级别的实时输出、常驻"输入中"指示器、16 个可配置工具 |
| **会话** | 按用户/项目目录自动持久化、Markdown/HTML/JSON 三种格式导出 |
| **自动化** | Webhook API 服务器、cron 定时任务、主动通知服务、事件总线 |
| **文件** | 文件上传与压缩包解压、图片/截图分析、语音消息转写 |
| **安全** | 白名单认证、令牌桶限流、目录沙箱、成本追踪、审计日志 |

规划中的增强只有一项：第三方插件系统。更大的方向变化在 v2 路线图里（见 §12.3）。

---

## §2 系统地图

在深入细节前，先看代码怎么分工。`src/` 下 12 个模块各管一摊：

| 模块 | 职责 |
|------|------|
| `bot/` | Telegram 侧：消息收发、命令路由、中间件（认证/限流/安全/突发保护） |
| `claude/` | Claude Code 集成：SDK 调用、工具边界检查（`can_use_tool` 回调） |
| `security/` | 输入验证、路径/命令清理、审计日志 |
| `storage/` | SQLite 持久化与会话存储（带迁移） |
| `events/` | 事件总线，解耦消息路由 |
| `api/` | FastAPI Webhook 服务器（GitHub 与通用 webhook） |
| `scheduler/` | cron 表达式定时任务（持久化在 SQLite） |
| `notifications/` | 主动通知分发（按聊天限速） |
| `projects/` | 项目线程模式：多项目的 topic 路由 |
| `config/` | Pydantic 配置加载与校验（SecretStr 保护敏感值） |
| `mcp/` | MCP 配置支持 |
| `utils/` | 通用工具函数 |

理解这张表后，后文的机制都能对上号：安全约束住在 `security/` 和 `claude/`，自动化三件套分别是 `api/`、`scheduler/`、`notifications/`，多项目支持在 `projects/`。

另一个贯穿全文的划分是**两种交互模式**：智能体模式（agentic，默认）面向自然语言对话，经典模式（classic）面向终端式命令操作。两者的命令集、安全层乃至未来命运都不同（v2 计划只保留智能体模式）。

---

## §3 两种交互模式

### 3.1 智能体模式（默认）

直接和 Claude 说话，不需要记命令。Claude 的工具调用实时回显：

```text
You: What files are in this project?
Bot: Working... (3s)
     📖 Read
     📂 LS
     💬 Let me describe the project structure
Bot: [Claude describes the project structure]

You: Add a retry decorator to the HTTP client
Bot: Working... (8s)
     📖 Read: http_client.py
     💬 I'll add a retry decorator with exponential backoff
     ✏️ Edit: http_client.py
     💻 Bash: poetry run pytest tests/ -v
Bot: [Claude shows the changes and test results]
```

可用命令：`/start`、`/new`、`/status`、`/verbose`、`/repo`；启用项目线程模式后追加 `/sync_threads`。

v1.6.0 起有两个值得知道的改进：一是内联 Stop 按钮，可以在 Telegram 原生界面里取消正在运行的 Claude 请求；二是未知斜杠命令会透传给 Claude——也就是说 `/run tests` 这类自定义写法不再报错，而是被当作指令交给 Claude 解释执行。

**详细级别**：`/verbose 0|1|2` 控制回显多少后台活动。

| 级别 | 显示内容 |
|------|------|
| `0` (quiet) | 仅最终响应（"输入中"指示器保持工作） |
| `1` (normal，默认) | 实时显示工具名称和推理片段 |
| `2` (detailed) | 工具名称带输入 + 更长的推理文本 |

### 3.2 经典模式

设置 `AGENTIC_MODE=false` 启用。这是一个完整的终端式界面：13 个命令、目录导航、内联键盘、快捷操作、Git 集成和会话导出。

```text
You: /cd my-web-app
Bot: Directory changed to my-web-app/

You: /ls
Bot: src/  tests/  package.json  README.md

You: /actions
Bot: [Run Tests] [Install Deps] [Format Code] [Run Linter]
```

命令清单见 §13 附录。经典模式下 Bash 命令有额外的危险模式拦截（见 §9.2），这是它和智能体模式在安全行为上的实质差异。

### 3.3 模式对比

| 方面 | 智能体模式 | 经典模式 |
|------|------------|----------|
| **交互方式** | 自然语言对话 | 终端命令 |
| **命令数量** | 5 个（+`/sync_threads`） | 13 个（+`/sync_threads`） |
| **Bash 危险模式拦截** | 不启用（依赖 OS 级沙箱） | 启用 |
| **未来** | v2 的唯一模式 | v2 计划移除 |

选哪个？新部署直接用默认的智能体模式。经典模式的目录导航和快捷按钮对纯命令流用户仍有价值，但按官方路线图它不会进入 v2，不值得围绕它做长期建设。

---

## §4 安装与部署

### 4.1 环境要求

| 要求 | 说明 |
|------|------|
| **Python** | 3.11+ |
| **Claude Code CLI** | 需安装并认证（CLI 认证方式必需，见 §5） |
| **Telegram Bot Token** | 通过 [@BotFather](https://t.me/botfather) 获取 |
| **Poetry** | 仅源码安装需要 |

### 4.2 安装

官方推荐从 release tag 安装，不要装 `main` 分支：

```bash
# 方式一：uv（推荐，装在隔离环境）
uv tool install git+https://github.com/overwirehq/claude-code-telegram@v1.7.0

# 或者 pip
pip install git+https://github.com/overwirehq/claude-code-telegram@v1.7.0

# 跟踪最新稳定版
pip install git+https://github.com/overwirehq/claude-code-telegram@latest
```

没有 uv 的话，`curl -LsSf https://astral.sh/uv/install.sh | sh` 一行装好。

方式二是源码安装（开发用，需要 Poetry）：

```bash
git clone https://github.com/overwirehq/claude-code-telegram.git
cd claude-code-telegram
make dev
```

### 4.3 配置与运行

```bash
cp .env.example .env
nano .env
```

最小必需配置四项：

```bash
TELEGRAM_BOT_TOKEN=1234567890:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_BOT_USERNAME=my_claude_bot
APPROVED_DIRECTORY=/Users/yourname/projects
ALLOWED_USERS=123456789
```

运行：

```bash
make run          # 生产环境
make run-debug    # 调试日志（首次运行推荐）
make run-watch    # 代码变动自动重启（v1.6.0 新增，开发用）
```

在 Telegram 里找到你的 bot，发 `/start`，问一个关于项目的问题，再用 `/status` 确认会话信息，就算跑通了。

### 4.4 实际效果

README 给的示例对话：

```text
You: Can you help me add error handling to src/api.py?

Bot: I'll analyze src/api.py and add error handling...
     [Claude reads your code, suggests improvements, and can apply changes directly]

You: Looks good. Now run the tests to make sure nothing broke.

Bot: Running pytest...
     All 47 tests passed. The error handling changes are working correctly.
```

---

## §5 Claude 认证

bot 用 Claude Code Python SDK 连接 Claude，认证有两种方式：

| 方式 | 做法 | 适用 |
|------|------|------|
| **SDK + CLI 认证**（推荐） | `claude auth login` 后无需 API key，SDK 直接复用 CLI 凭据 | 已有 Claude CLI 环境的个人部署 |
| **SDK + API Key** | 设置 `ANTHROPIC_API_KEY=sk-ant-api03-...` | 服务器不便登 CLI、或远程 Mac 不想解锁 keychain |

两种方式性能和流式输出一致，差异只在是否依赖 CLI。还有第三种 `USE_SDK=false` 的 CLI 子进程模式，属于遗留路径，新部署不建议。

远程 Mac 有个专门的坑：SSH 会话里 macOS keychain 是锁着的，CLI 的 OAuth 凭据读不到，Claude 调用会静默失败。解法见 §11.3。

---

## §6 事件驱动自动化

除了被动应答，bot 还能响应外部触发。三个能力全部默认关闭，按需开启：

| 能力 | 开关 | 用途 |
|------|------|------|
| **Webhook 服务器** | `ENABLE_API_SERVER=true` | 接收 GitHub push/PR/issue 等事件，转给 Claude 自动摘要或审查 |
| **定时任务** | `ENABLE_SCHEDULER=true` | 按 cron 表达式跑周期性 Claude 任务（如每日代码健康检查） |
| **主动通知** | `NOTIFICATION_CHAT_IDS=123,456` | 把 webhook 和定时任务的结果推送到指定聊天 |

### 6.1 GitHub Webhook

```bash
# 生成密钥
openssl rand -hex 32
```

```bash
GITHUB_WEBHOOK_SECRET=your-generated-secret
NOTIFICATION_CHAT_IDS=123456789
```

然后在 GitHub 仓库 **Settings > Webhooks > Add webhook** 配置：Payload URL 填 `https://your-server:8080/webhooks/github`，Content type 选 `application/json`，Secret 填刚生成的值，按需勾选 push、pull_request、issues 等事件。

签名校验是 HMAC-SHA256，payload 用 `X-Hub-Signature-256` 头验证；delivery ID 上做了原子去重（`INSERT OR IGNORE`），重放攻击进不来。

非 GitHub 的事件源走通用通道 `/webhooks/custom`，用 Bearer token 认证：

```bash
WEBHOOK_API_SECRET=your-api-secret
```

```bash
curl -X POST http://localhost:8080/webhooks/custom \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-secret" \
  -H "X-Event-Type: deployment" \
  -H "X-Delivery-ID: unique-id-123" \
  -d '{"status": "success", "environment": "production"}'
```

### 6.2 定时任务

```bash
ENABLE_SCHEDULER=true
NOTIFICATION_CHAT_IDS=123456789
```

任务用编程方式管理，持久化在 SQLite。v1.7.0 修了两个调度可靠性问题：长任务执行期间错过的触发不再被静默丢弃（`misfire_grace_time=None` + coalesce），定时任务改为后台并发执行，不再阻塞事件总线。

---

## §7 项目线程模式

一台 bot 服务多个项目时，开项目线程模式可以按项目隔离话题：

```bash
ENABLE_PROJECT_THREADS=true
PROJECT_THREADS_MODE=private        # private（默认）或 group
PROJECTS_CONFIG_PATH=config/projects.yaml
# group 模式才需要：
PROJECT_THREADS_CHAT_ID=-1001234567890
```

- **private 模式**：`/start` 会自动把你的项目同步为 bot 私聊里的话题。
- **group 模式**：项目映射到群组的论坛话题，需要指定群 ID。
- **严格路由**：映射生效后，话题之外只有 `/start` 和 `/sync_threads` 可用，防止消息串项目。

前置条件一个：在 BotFather 里给 bot 打开 `Bot Settings -> Threaded mode`。

---

## §8 文件、图片与语音

- **文件上传**：支持压缩包自动解压，文件类型有白名单校验。
- **图片/截图分析**：v1.6.0 起，发给 bot 的图片以多模态内容块传给 Claude，Claude 能真正"看到"并分析截图。
- **语音转写**：`ENABLE_VOICE_MESSAGES=true` 开启，三种转写引擎可选：

| Provider | 配置 | 默认模型 |
|------|------|------|
| **Mistral Voxtral**（默认） | `VOICE_PROVIDER=mistral` + `MISTRAL_API_KEY` | `voxtral-mini-latest` |
| **OpenAI Whisper** | `VOICE_PROVIDER=openai` + `OPENAI_API_KEY` | `whisper-1` |
| **本地 whisper.cpp** | `VOICE_PROVIDER=local`，需自建二进制 + ffmpeg | `base` |

本地 whisper.cpp 不需要 API key，适合不想让语音出网的部署，完整搭建见仓库 `docs/local-whisper-cpp.md`。云端 provider 需要额外装 voice 依赖：`pip install "claude-code-telegram[voice]"`。

---

## §9 安全模型

这是把一个能执行命令的 bot 暴露到聊天软件上，安全设计值得单独一章。官方 SECURITY.md 定义了六层纵深防御：

| 层 | 机制 |
|------|------|
| **1. 认证与授权** | 用户白名单（`ALLOWED_USERS`）、可选令牌认证、会话超时管理 |
| **2. 目录边界** | 所有操作限定在 `APPROVED_DIRECTORY` 内；路径穿越（`../`）拦截；Claude 自身工具调用的预执行检查 |
| **3. 输入验证** | 命令清理（`;`、`&&`、`$()`、`..`）、上传文件类型校验、敏感文件保护（`.env`、`.ssh`、`id_rsa`、`.pem`）、zip bomb 防护 |
| **4. 速率限制** | 令牌桶算法限请求数 + 按用户累计成本限额 + 突发容量保护 |
| **5. 审计日志** | 认证事件、命令执行、安全违规全量记录，自动风险分级 |
| **6. Webhook 认证** | GitHub HMAC-SHA256 签名 + Bearer token + delivery ID 去重 |

### 9.1 工具调用边界检查（v1.7.0 的关键修复）

最容易被误解的是第 2 层里的 `can_use_tool` 回调：它拦截的是 **Claude 自己发起**的工具调用——比如 Claude 读到的文档内容里藏了诱导指令，让它去写 `APPROVED_DIRECTORY` 之外的文件。用户消息层面的注入由第 3 层覆盖。

这个机制在 v1.7.0 之前形同虚设：SDK 只在 CLI 发出 `can_use_tool` 控制请求时才调用回调，而 CLI 会先解析允许规则——默认工具列表里的 `Read`、`Write`、`Edit`、`Bash` 全部被预批准，根本走不到回调。也就是说，默认安装下边界检查是静默失效的（issue #219）。v1.7.0 修复了它（#220）：受保护工具从传给 SDK 的 `allowed_tools` 里剥离，并禁用 `autoAllowBashIfSandboxed` 这条独立旁路，保护范围同时扩展到 `MultiEdit`、`NotebookEdit`、`NotebookRead`。

**升级影响**：修复后，指向 `APPROVED_DIRECTORY` 之外的路径的越界调用会被拒绝，而以前会成功。如果旧部署一直依赖这个缺口，升级后行为会变。`DISABLE_TOOL_VALIDATION=true` 可以恢复旧的宽松行为，但那会连路径和 Bash 边界检查一起关掉，只该在完全可信的环境用。

### 9.2 工具控制的真实语义

`docs/tools.md` 写得很坦率，两条规则和直觉不同：

- `CLAUDE_ALLOWED_TOOLS` 是预批准清单，不是边界。边界检查生效时，没列进清单的工具不会被禁用，只是被路由到 `can_use_tool` 回调，而回调放行一切通过目录检查的调用。
- 真正拒绝一个工具只有一种办法：`CLAUDE_DISALLOWED_TOOLS`。

另外，Bash 危险模式拦截（`rm -rf`、`sudo`、`chmod 777`、管道、重定向、子 shell）**只在经典模式启用**；智能体模式依赖 OS 级沙箱。但"改动文件系统的 Bash 命令目标必须在 `APPROVED_DIRECTORY` 内"这条目录边界检查在两种模式下都生效。

### 9.3 交互式工具审批（v1.7.0 新增）

`INTERACTIVE_TOOL_APPROVAL=true` 后，高风险工具调用（默认 `Bash`、`Write`、`Edit`）会先在 Telegram 里弹 Allow/Deny 按钮。60 秒无响应按 deny 处理（fail-closed）。v1.7.0 还合入了按工具粒度的审批提示（#217）。这是目前对"命令先审后跑"需求最接近的现成答案，但注意 §12.3 提到的 v1 局限：Claude 的 `AskUserQuestion` 你在 Telegram 上是答不了的，审批按钮和自由问答是两回事。

### 9.4 已知缺口：令牌认证不可用

配置里有 `ENABLE_TOKEN_AUTH`，但 SECURITY.md 明确标注它端到端不可用（#58）：token 存在内存里（`InMemoryTokenStorage`），重启即丢，也没有受支持的发放流程。**真实部署的访问控制请用 `ALLOWED_USERS` 白名单**，这也是官方推荐的唯一访问控制方式。

### 9.5 生产检查单

官方 Production Checklist 的核心项：

```bash
ENVIRONMENT=production      # 启用严格安全默认值
RATE_LIMIT_REQUESTS=5       # 生产从紧限流
RATE_LIMIT_WINDOW=60
RATE_LIMIT_BURST=10
CLAUDE_MAX_COST_PER_USER=5.0
SESSION_TIMEOUT_HOURS=12
ENABLE_TELEMETRY=true       # 安全监控
LOG_LEVEL=INFO
```

外加：`APPROVED_DIRECTORY` 不要指向 `/`、`/home` 等敏感目录；API 服务器套反向代理 + TLS；发现漏洞走 GitHub Security Advisories 私密上报（48 小时确认），不要开公开 issue。

---

## §10 日常使用：GitHub 工作流

Claude Code 本来就会用 `gh` CLI 和 `git`，服务器上 `gh auth login` 之后，仓库操作全部可以对话完成：

```text
You: List my repos related to monitoring
Bot: [Claude runs gh repo list, shows results]

You: Clone the uptime one
Bot: [Claude runs gh repo clone, clones into workspace]

You: /repo
Bot: 📦 uptime-monitor/  ◀
     📁 other-project/

You: Show me the open issues
Bot: [Claude runs gh issue list]

You: Create a fix branch and push it
Bot: [Claude creates branch, commits, pushes]
```

`/repo` 列出工作区里已克隆的仓库，`/repo <name>` 切换目录，会话自动恢复——切回去接着聊，上下文还在。

成本控制两件套：`CLAUDE_MAX_COST_PER_USER=10.0` 给每个用户设 10 美元累计花费上限（生命周期预算，非单次请求），`/status` 随时看用量。

---

## §11 排查与常见问题

### 11.1 Bot 没有响应

按顺序查：`TELEGRAM_BOT_TOKEN` 是否正确 → 你的用户 ID 是否在 `ALLOWED_USERS` 里 → Claude Code CLI 是否已安装可访问 → `make run-debug` 看日志。网络不稳的环境注意升级到 v1.7.0：此前一次 `getUpdates` 请求中断会让连接池永久卡死（"Pool timeout"），bot 就此失联，v1.7.0 修复（#214）。

### 11.2 Claude 集成不工作

- **CLI 认证**：`claude auth status`，未认证就 `claude auth login`。
- **API Key**：确认 key 以 `sk-ant-api03-` 开头。
- **权限报错**：检查 `APPROVED_DIRECTORY` 存在且可访问：`ls -la /path/to/your/projects`。
- **工具被限制**：检查 `CLAUDE_DISALLOWED_TOOLS` 是否禁了需要的工具，以及 `CLAUDE_ALLOWED_TOOLS` 自定义时是否漏了必要工具（再提醒一次 §9.2：漏出 allowed 清单的工具仍会走回调检查，真正禁用靠 disallowed）。

### 11.3 远程 Mac（SSH）的 keychain 问题

SSH 会话里 macOS keychain 是锁的，CLI 的 OAuth 凭据读不到，Claude 调用静默失败或报认证错误。三种解法：

```bash
# 解法一（最简单）：解锁 keychain 并在 detached tmux 会话里启动
make run-remote      # 管理会话：make remote-attach 看日志，make remote-stop 停止
```

```bash
# 解法二：写进 shell 配置，SSH 登录时自动解锁
if [ -n "$SSH_CONNECTION" ] && [ -z "$KEYCHAIN_UNLOCKED" ]; then
  security unlock-keychain ~/Library/Keychains/login.keychain-db
  export KEYCHAIN_UNLOCKED=true
fi
```

```bash
# 解法三：延长 keychain 自动上锁时间到 8 小时
security set-keychain-settings -t 28800 ~/Library/Keychains/login.keychain-db
```

或者干脆用 API Key 认证（§5），完全绕开 keychain。

### 11.4 如何查自己的 Telegram 用户 ID

给 [@userinfobot](https://t.me/userinfobot) 发条消息，它会回复你的数字 ID，填进 `ALLOWED_USERS` 即可。

---

## §12 采用建议

### 12.1 适合谁

- **个人开发者的移动延伸**：通勤路上审查代码、远程处理 issue、手机上盯 CI 修复结果——这是项目的主场。
- **远程服务器/家庭实验室管理**：配合 `make run-remote` 和 tmux，Mac mini 或 VPS 上的 Claude Code 变成一个随身的聊天联系人。
- **轻量自动化**：GitHub webhook 触发自动审查、每日定时健康检查，不需要时不开，开了也不占常驻资源（默认全关）。

### 12.2 谁应该缓一缓

- **多人团队共用**：v1 的全局锁把所有 Claude 请求串行化，多用户会互相排队。v2 才计划改成每会话并发。
- **依赖交互式审批的工作流**：Claude 发起的提问（`AskUserQuestion`）在 Telegram 上无法回答，计划模式和撤销流程也还没有。要等 v2 的交互式 UX。
- **合规敏感环境**：bot 能在主机上执行命令，安全模型再完整也改变了威胁面；先过一遍 SECURITY.md 的威胁模型和你们自己的边界。

### 12.3 版本演进与 v2 方向

- **v1.6.0**（2026-03-30）：Stop 按钮、未知斜杠命令透传、图片多模态分析、瞬时错误指数退避重试。
- **v1.6.1**（2026-09-11）：修复代理凭据泄漏到日志的问题。
- **v1.7.0**（2026-09-11）：工具边界检查真正生效（§9.1，行为变更）、轮询与启动稳定性修复、定时任务可靠性、交互式工具审批。
- **v2（路线图提案，2026-09）**：交互式权限与提问 UX、每会话并发、会话管理（列表/切换/分叉）、SDK 升级到 0.2.x、经典模式移除、容器镜像与包发布。

一句话判断：v1.7.0 已经把安全故事讲圆了，现在的短板集中在并发与交互，两者都在 v2 的正中央。个人用现在就可以上，团队共用等 v2。

---

## §13 附录：命令参考

### 13.1 智能体模式命令

| 命令 | 说明 |
|------|------|
| `/start` | 开始新会话 |
| `/new` | 开始新对话 |
| `/status` | 查看状态与用量 |
| `/verbose 0|1|2` | 控制详细程度 |
| `/repo` | 列出工作区仓库 |
| `/repo <name>` | 切换到指定仓库（会话自动恢复） |
| `/sync_threads` | 同步项目线程（需 `ENABLE_PROJECT_THREADS=true`） |
| 未知 `/xxx` | v1.6.0 起透传给 Claude 解释执行 |

### 13.2 经典模式命令（`AGENTIC_MODE=false`）

| 命令 | 说明 |
|------|------|
| `/start` | 开始会话 |
| `/help` | 帮助信息 |
| `/new` | 开始新对话 |
| `/continue` | 继续上次对话 |
| `/end` | 结束对话 |
| `/status` | 查看状态 |
| `/cd <dir>` | 切换目录 |
| `/ls` | 列出文件 |
| `/pwd` | 显示当前目录 |
| `/projects` | 列出项目 |
| `/export` | 导出会话（Markdown/HTML/JSON） |
| `/actions` | 快捷操作菜单 |
| `/git <cmd>` | Git 操作 |
| `/sync_threads` | 同步项目线程（需 `ENABLE_PROJECT_THREADS=true`） |

## 参考来源与口径说明

- 本文 2026-04-01 发布时基于 v1.6.0（当时最新版），2026-09-22 按 v1.7.0 全文复核更新：仓库已由 RichardAtCT/claude-code-telegram 迁移至 overwirehq/claude-code-telegram 组织（旧链接经 GitHub 重定向可达），安装命令与链接已更新为新路径。
- Stars/Forks/Watchers/提交数/贡献者/release 数来自 GitHub API，均为 2026-09-22 读数；语言占比按 GitHub languages API 字节数计算（Python 99.6%）。
- 两种模式的命令清单、verbose 级别、安装与配置项对照 README 与 `docs/setup.md`；16 个默认工具与 allowed/disallowed 语义对照 `docs/tools.md`；认证方式、Webhook/调度器/语音配置、远程 Mac SSH 方案对照 `docs/setup.md`；项目线程模式对照 README Configuration 节。
- 六层安全模型、`can_use_tool` 机制、令牌认证已知缺口（#58）与漏洞上报流程对照 SECURITY.md；v1.7.0 边界检查修复的行为变更对照 CHANGELOG [1.7.0] 条目及 issue #219；v1.6.x 特性对照 CHANGELOG 对应版本条目与 release notes。
- v1 全局锁串行、`AskUserQuestion` 不可答、v2 方向（经典模式移除、每会话并发、SDK 0.2）对照 `docs/ROADMAP-v2.md`（2026-09 提案，基线 v1.7.0）；"559 个测试、覆盖率 56%"为该路线图声明的基线数字。
- 许可证说明：README 徽章与 License 节声明 MIT，但仓库截至 2026-09-22 未附 LICENSE 文件（GitHub API license 字段为空），引用时以 README 声明为准。
