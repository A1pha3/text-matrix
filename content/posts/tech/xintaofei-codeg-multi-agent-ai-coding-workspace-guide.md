---
title: "Codeg 多 Agent 协作工作空间指南：ACP 协议统一 11 种编码 Agent"
slug: "xintaofei-codeg-multi-agent-ai-coding-workspace-guide"
date: 2026-07-12T12:10:00+08:00
lastmod: 2026-07-12T12:10:00+08:00
categories: ["tech"]
tags: ["ai-coding", "multi-agent", "tauri", "rust", "agent-client-protocol", "codeg", "协作工作空间", "开源工具"]
author: "钳岳星君"
draft: false
summary: "基于 ACP 协议，把 Claude Code/Codex/Gemini/OpenCode 等 11 种编码 Agent 装进同一个 Tauri+Next.js 工作空间：会话聚合、跨 Agent 委托、Office 文档编辑、可视化脚手架、Docker 自托管——一个 Rust workspace 三个二进制搞定桌面+服务端+sidecar。"
description: "Codeg 多 Agent 协作工作空间：ACP 协议统一 Claude Code/Codex/Gemini 等 11 种编码 Agent 的会话聚合、跨 Agent 委托、Office 文档协作与可视化脚手架。Tauri 桌面 + codeg-server + Docker 三种部署形态，Rust workspace 三个二进制覆盖 desktop/server/sidecar 职责。"
---

## 为什么需要多 Agent 协作工作空间

如果你同时用 Claude Code、Codex CLI、Gemini CLI 这三个工具，你大概率经历过这种抓狂：Claude Code 里聊到一半的代码上下文，要复制粘贴到 Codex 才能换个角度 review；想用 Gemini 的长上下文读大型仓库，又得新开一个终端窗口另起炉灶；用 OpenCode 跑实验性 feature branch，session 记录躺在 `~/.local/share/opencode/opencode.db` 里，事后想找回当时的 prompt 链路基本靠翻 shell history。

这就是 codeg 要解决的问题：把 11 种 AI 编码 Agent 的会话、上下文、工具调用记录**统一聚合成一个工作空间**，让主 Agent 通过 ACP（Agent Client Protocol）协议把子任务**委托**给其它 Agent 跑独立 session，最终在同一个 Tauri 桌面应用或浏览器里看到所有结果。

本文基于 [xintaofei/codeg](https://github.com/xintaofei/codeg) 仓库的源码、README、架构图、三个 Rust 二进制职责定义，从实战角度拆解这套多 Agent 协作系统的设计取舍。

## 项目定位与全貌

Codeg（Code Generation）的核心定位不是又一个 Claude Code 替代品，而是**多 Agent 时代的协作中枢**。它的技术栈选型很坦诚：

- **前端**：Next.js 16（Static Export）+ React 19
- **桌面壳**：Tauri 2（窗口管理、tray、updater）
- **后端**：Rust workspace，三个二进制共享 core
- **数据库**：SeaORM + SQLite（本地优先）
- **多 Agent 协议**：ACP（Agent Client Protocol）

整个项目用一个 Rust workspace 出三个二进制：`codeg`（Tauri 桌面应用）、`codeg-server`（独立 HTTP+WS 服务端）、`codeg-mcp`（stdio MCP companion sidecar）。这种"一个 workspace 三个 binary"的拆分让桌面端、服务端、Agent 协作层互不污染编译产物。

部署形态覆盖了所有使用场景：

| 形态 | 适用人群 | 启动方式 |
|------|----------|----------|
| Tauri 桌面 | 个人开发者、追求原生体验 | `pnpm tauri dev` |
| 独立 server | 团队远程访问、容器化部署 | `codeg-server` |
| Docker | CI/CD 集成、批量部署 | `docker compose up -d` |

无论哪种形态，前端代码都是同一份 `out/` 静态导出（Next.js Static Export），区别只在于 Transport Abstraction 层走的是 Tauri IPC 还是 Axum HTTP/WS。

## 核心能力一：会话聚合（Conversation Aggregation）

Codeg 把"对话记录管理"这件事当成第一公民。它通过环境变量 + 默认路径的方式，发现并解析本地已安装的所有 Agent 的会话存储：

| Agent | 环境变量 | macOS/Linux 默认路径 |
|-------|----------|---------------------|
| Claude Code | `$CLAUDE_CONFIG_DIR/projects` | `~/.claude/projects` |
| Codex CLI | `$CODEX_HOME/sessions` | `~/.codex/sessions` |
| OpenCode | `$XDG_DATA_HOME/opencode/opencode.db` | `~/.local/share/opencode/opencode.db` |
| Gemini CLI | `$GEMINI_CLI_HOME/.gemini` | `~/.gemini` |
| OpenClaw | — | `~/.openclaw/agents` |
| Cline | `$CLINE_DIR` | `~/.cline/data/tasks` |
| Hermes Agent | `$HERMES_HOME/state.db` | `~/.hermes/state.db` |
| CodeBuddy | `$CODEBUDDY_CONFIG_DIR/projects` | `~/.codebuddy/projects` |
| Kimi Code | `$KIMI_CODE_HOME/sessions` | `~/.kimi-code/sessions` |
| Pi | `$PI_CODING_AGENT_SESSION_DIR` | `~/.pi/agent/sessions` |
| Grok Build | `$GROK_HOME/sessions` | `~/.grok/sessions` |

实现层面，Rust core 里的 Parsers 模块针对每种 Agent 写了独立的解析器，把 JSONL/SQLite/自定义格式的会话统一转成内部统一格式。这件事看似平淡，实际价值巨大：你想 review 上周用 Codex 跑的 prompt 实验，不用再 `grep` 一堆 session 文件，直接在 codeg 里搜关键词、按 Agent 类型筛选、按时间排序。

## 核心能力二：跨 Agent 委托（Multi-Agent Collaboration）

这是 codeg 最具想象力的功能。在一个 session 内，主 Agent 可以通过 MCP（Model Context Protocol）的 `delegate_to_agent` 工具把子任务**委托**给另一个类型的 Agent：

> 主 Agent（Claude Code）拆解任务 → 调用 `delegate_to_agent(agent_type="codex", prompt="review 这个 PR 的安全性")` → codeg-mcp sidecar 启动 Codex CLI 子 session → 返回结果合并到主对话流

关键设计点：`codeg-mcp` 是个**per-launch stdio MCP companion**，每次 Agent CLI 启动时被附带加载。它通过 MCP 协议暴露 `delegate_to_agent` 工具给主 Agent，自己本身作为独立进程跑（不进 Agent 主进程空间）。这种 sidecar 模式带来三个好处：

1. **崩溃隔离**：codeg-mcp 挂掉不影响主 Agent
2. **协议升级独立**：改 MCP 接口不动 Agent CLI
3. **跨平台兼容**：stdin/stdout 在所有 OS 都是同构的

部署上 codeg-mcp 必须和父二进制同目录：installers、Docker 镜像、Tauri sidecar bundler 都会自动把 `codeg-mcp-<triple>` 放到 `codeg` 或 `codeg-server` 旁边。源码自定义布局可以用 `CODEG_MCP_BIN=/abs/path/codeg-mcp` 环境变量覆盖默认查找逻辑。如果 companion 缺失，**委托功能静默降级**——只打印一行 warning，其它 Agent session 照常工作。这种 fail-soft 设计哲学在整套架构里反复出现。

## 核心能力三：Project Boot 可视化脚手架

Project Boot 是一个分屏 UI：左边是配置面板，右边是 live preview iframe。

配置项支持：

- **样式**：style、color theme、icon library、font、border radius
- **框架**：Next.js / Vite / React Router / Astro / Laravel
- **包管理器**：pnpm / npm / yarn / bun（自动检测已安装版本）
- **UI 库**：shadcn/ui

点"Create Project"后，launcher 后台跑 `shadcn init` 带上你的预设，结果直接打开进 codeg workspace。整个流程从"决定技术栈"到"能跑起来"压缩到 30 秒内，live preview 在点击配置项的瞬间就更新——所见即所得。

当前只支持 shadcn/ui 脚手架，但 tab-based design 已经预留扩展位，未来可以加更多项目类型。

## 核心能力四：Office Documents

Codeg 内置了一个叫 `officecli` 的工具集，让 Agent 能像操作代码一样操作 Office 文档：

- **创建/编辑**：生成新的 `.docx`/`.xlsx`/`.pptx`，包含图表、表格、格式化
- **分析/校对**：检查文档结构、找出格式问题、proofread 内容
- **live preview**：在 codeg 的文件 tab 里直接渲染，Agent 改了文件 preview 自动刷新

Live preview 的实现细节值得展开：背后跑一个长生命周期的 `officecli watch` 服务器，通过 reverse-proxy 暴露给前端。**Cap auth** 机制确保 web 和 standalone-server 部署下都能安全访问，不会泄露给未授权网络。

Office Tools settings 页可以管理 `(skill, agent)` 矩阵：勾选哪个 skill 暴露给哪个 agent，一键全开/全关，按 agent 维度或 skill 维度批量操作。这种"以矩阵形式管理 skill × agent"的模式是 codeg 的一个重要设计决策——它把"哪个 agent 能用什么能力"这件事从 hardcode 提到了配置层。

## 核心能力五：Scientific Research

Codeg bundle 了一套 MIT 许可证的 scientific-research skills，覆盖科研全流程：

- 假设生成（hypothesis generation）
- 实验设计（experimental design）
- 统计效力（statistical power）
- 统计分析（statistical analysis）
- 探索性数据分析（exploratory data analysis）
- 科学可视化（scientific visualization）
- 批判评审（critical appraisal）
- 同行评审（peer review）
- 引文管理（citation management）
- 学者评价（scholar evaluation）
- 论文查询（paper lookup）
- AI 示意图（AI schematics）

这些 skill 安装到共享 central skill store 后，可以像 expert skills 和 office tools 一样 link 到任意 agent。Science settings 页同样用 `(skill, agent)` 矩阵管理，badge 会标注哪些 skill 需要 API key 或 Python 环境。

这套科学 skill 的来源是 [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) 的 MIT 许可子集。Codeg 没有自己造轮子，而是站在巨人肩膀上。

## Chat Channels：把 Agent 装进聊天工具

Codeg 支持把 AI 编码 Agent 接入聊天渠道：

| 渠道 | 协议 | 状态 |
|------|------|------|
| Telegram | Bot API（HTTP long-polling） | 内置 |
| Lark（飞书） | WebSocket + REST API | 内置 |
| iLink（微信） | WebSocket + REST API | 内置 |

未来计划支持 Discord、Slack、钉钉。

接入后的能力：

- 创建 task、发送 follow-up 消息
- 批准权限请求
- 恢复 session
- 实时监控 agent 活动
- 接收实时 agent 响应，含 tool-call 详情、permission prompts、完成 summary

**不开浏览器也能用 Agent**——这是 codeg 的一个关键差异化。对国内开发者来说，飞书原生支持意味着可以一边开会一边让 Agent 跑重构，agent 在飞书里实时汇报进度。

## Automations：把 Composer 配置变成可复用任务

任何 Composer 配置（agent、model、prompt、working directory、options）都能保存成 Automation，三种触发方式：

- 手动
- Cron 定时
- Headless 后台执行

保存一次，反复使用。Automation 在后台跑后创建真实的 session，可以在 workspace 里随时打开查看。点击 start 后直接回到 workspace 继续工作——不像传统 CI 需要等构建完成。

## 部署：5 种方式覆盖所有场景

### 方式 1：一行命令安装（Linux/macOS）

```bash
curl -fsSL https://raw.githubusercontent.com/xintaofei/codeg/main/install.sh | bash
```

支持自定义版本和目录：

```bash
curl -fsSL https://raw.githubusercontent.com/xintaofei/codeg/main/install.sh | bash -s -- --version v0.5.2 --dir ~/.local/bin
```

### 方式 2：PowerShell 一行命令（Windows）

```powershell
irm https://raw.githubusercontent.com/xintaofei/codeg/main/install.ps1 | iex
```

### 方式 3：GitHub Releases 下载

预编译二进制覆盖 Linux x64/arm64、macOS x64/arm64、Windows x64 五个平台。下载、解压、跑：

```bash
tar xzf codeg-server-linux-x64.tar.gz
cd codeg-server-linux-x64
CODEG_STATIC_DIR=./web ./codeg-server
```

### 方式 4：Docker

```bash
# Compose 方式（推荐）
docker compose up -d

# 或直接 docker run
docker run -d -p 3080:3080 -v codeg-data:/data ghcr.io/xintaofei/codeg:latest

# 自定义 token + 挂载项目目录
docker run -d -p 3080:3080 \
  -v codeg-data:/data \
  -v /path/to/projects:/projects \
  -e CODEG_TOKEN=your-secret-token \
  ghcr.io/xintaofei/codeg:latest
```

Docker 镜像用 multi-stage build：Node.js + Rust 构建阶段 → 精简 Debian 运行时。镜像里包含 `git` 和 `ssh`，支持仓库操作。`/data` volume 持久化所有数据。

### 方式 5：从源码构建

```bash
pnpm install && pnpm build
cd src-tauri
cargo build --release --bin codeg-server --no-default-features
cargo build --release --bin codeg-mcp --no-default-features
CODEG_STATIC_DIR=../out ./target/release/codeg-server
```

如果两个二进制分开放，用 `CODEG_MCP_BIN=/abs/path/to/codeg-mcp` 显式指定。否则多 agent 委托功能静默关闭。

## In-place Updates：自动升级 + 自动回滚

Server 支持自升级：Settings → Software Update 下载签名 release，替换二进制和 web assets，重启。**只支持 Linux/macOS**（Windows 禁用）。上一个版本自动备份，UI 上有 Roll back 按钮。

**`--supervise` 模式的关键价值**：自动回滚。新版本启动失败超过 trial window，supervisor 自动 revert 到上一个能跑起来的版本：

```bash
CODEG_STATIC_DIR=./web ./codeg-server --supervise
```

没有 `--supervise` 也能升级，但失败时没 supervisor 兜底，是 best-effort。Docker 镜像默认带 supervisor。

**Docker 升级的特殊注意点**：in-place upgrade 写入容器 writable layer，不进 image。`docker pull` 只刷新 image 不影响运行容器，要 `docker compose up --force-recreate` 才生效。要让升级永久，重新 pull 新 image 并 recreate 容器。

## 配置：8 个环境变量全解

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CODEG_PORT` | `3080` | HTTP 端口 |
| `CODEG_HOST` | `0.0.0.0` | 绑定地址 |
| `CODEG_TOKEN` | 随机 | 鉴权 token（启动时打到 stderr） |
| `CODEG_DATA_DIR` | `~/.local/share/codeg` | SQLite 数据库目录（也作 `uploads/`、`pets/` 根） |
| `CODEG_STATIC_DIR` | `./web` 或 `./out` | Next.js 静态导出目录 |
| `CODEG_MCP_BIN` | 未设 | `codeg-mcp` 绝对路径，覆盖默认同目录 + `PATH` 查找 |
| `CODEG_SKIP_SIDECAR` | 未设 | 前端开发用，`1` 跳过 codeg-mcp 编译（发布构建必须 unset） |
| `CODEG_UPLOAD_MAX_TOTAL_BYTES` | 未设 | uploads/ 总量上限（字节），未设或 0 禁用，启动时打印状态 |
| `CODEG_UPLOAD_QUOTA_STRICT` | 未设 | truthy 时 quota 配置无法解析则 exit 2（fail-closed） |

`CODEG_UPLOAD_MAX_TOTAL_BYTES` 的分布式限制需要注意：**quota 在单个 codeg-server 进程内生效**。横向扩展共享 `uploads/` volume 需要外部协调（file lock、Redis、reverse-proxy quota）。

`CODEG_UPLOAD_QUOTA_STRICT` 是给有"quota 必须生效"安全策略的场景准备的：默认是 fail-open（配置无效只 WARN），strict 模式是 fail-closed（配置无效 exit 2）。

## 架构图解读

```
Next.js 16 (Static Export) + React 19
        |
        | invoke() (desktop) / fetch() + WebSocket (web)
        v
  ┌─────────────────────────┐
  │   Transport Abstraction  │
  │  (Tauri IPC or HTTP/WS) │
  └─────────────────────────┘
        |
        v
┌─── Tauri Desktop ───┐    ┌─── codeg-server ───┐
│  Tauri 2 Commands    │    │  Axum HTTP + WS    │
│  (window management) │    │  (standalone mode)  │
└──────────┬───────────┘    └──────────┬──────────┘
           └──────────┬───────────────┘
                      v
            Shared Rust Core
              |- AppState
              |- ACP Manager
              |- Parsers (会话解析)
              |- Chat Channels
              |- Git / File Tree / Terminal
              |- MCP marketplace + config
              |- Office Tools (officecli) + Automations
              |- SeaORM + SQLite
                      |
              ┌───────┼───────┐
              v       v       v
  Local Filesystem  Git   Chat Channels
    / Git Repos    Repos  (Telegram, Lark, iLink)
```

三层架构很清晰：前端 → Transport Abstraction → Shared Rust Core。**Shared Rust Core 是整个项目的灵魂**——AppState 管理全局状态，ACP Manager 处理 Agent 协议握手，Parsers 做会话格式转换，Chat Channels 桥接 IM，Git/File Tree/Terminal 是 IDE 级基础能力，MCP marketplace 提供扩展点。

## 开发与构建

前端开发：

```bash
pnpm install
pnpm dev                  # 仅 Next.js，不编译 Rust
pnpm build                 # 静态导出到 out/
```

完整桌面开发：

```bash
pnpm tauri dev            # 自动构建 codeg-mcp sidecar
pnpm tauri build          # release 构建
```

服务端开发：

```bash
pnpm server:dev
pnpm server:build         # 输出 src-tauri/target/release/codeg-server
```

显式构建 sidecar：

```bash
pnpm tauri:prepare-sidecars   # 输出 src-tauri/binaries/codeg-mcp-<triple>
```

跳过 sidecar（仅调试前端）：

```bash
CODEG_SKIP_SIDECAR=1 pnpm tauri dev
```

Rust 检查：

```bash
cargo check                                                # desktop
cargo check --no-default-features --bin codeg-server       # server
cargo check --no-default-features --bin codeg-mcp          # MCP companion
cargo clippy --all-targets --features test-utils -- -D warnings
```

Rust 测试：

```bash
cargo test --features test-utils                           # desktop
cargo test --no-default-features --bin codeg-server --lib  # server
cargo insta review                                         # parser snapshot 更新
```

前端测试：

```bash
pnpm test
pnpm test:watch
pnpm test:coverage
```

## 实战：30 分钟跑起来

```bash
# 1. 一键安装（macOS）
curl -fsSL https://raw.githubusercontent.com/xintaofei/codeg/main/install.sh | bash

# 2. 启动 server
codeg-server

# 3. 浏览器打开
open http://localhost:3080

# 4. 输入 stderr 打印的 token 登录
# 5. 在 Settings → Agents 里看到本地所有 Agent 自动被发现
# 6. 在 Composer 里选一个 Agent，让它通过 delegate_to_agent 委托给另一个
```

如果跑 Docker：

```bash
docker run -d -p 3080:3080 \
  -v codeg-data:/data \
  -v ~/Code:/projects \
  -e CODEG_TOKEN=$(openssl rand -hex 32) \
  ghcr.io/xintaofei/codeg:latest

# 查看 token
docker logs <container-id> 2>&1 | grep CODEG_TOKEN
```

## 关键设计哲学

**Local-first**：所有解析、存储、项目操作默认本地完成。Network access 只在用户主动触发的动作时发生。Web 部署用 token 鉴权。

**Fail-soft**：codeg-mcp 缺失时主 Agent 照常工作只 WARN；sidecar 升级失败 supervisor 自动回滚；quota 配置无效默认 WARN（除非 strict 模式）。

**Protocol as Foundation**：ACP 是连接多 Agent 的基础。Codeg 不发明 Agent 间通信协议，而是基于已有的 [Agent Client Protocol](https://agentclientprotocol.com/) 和 [Superpowers](https://github.com/obra/superpowers)。

**Skill × Agent 矩阵管理**：所有可扩展能力（office、scientific、expert）都通过 `(skill, agent)` 二维矩阵管理，避免硬编码"哪个 agent 能做什么"。

## 与同类工具的对比

| 工具 | 多 Agent 协议 | 部署形态 | 协议层 |
|------|--------------|----------|--------|
| **Codeg** | ACP | Desktop + Server + Docker | MCP + ACP |
| Claude Code | Anthropic 内部协议 | CLI 单 Agent | MCP |
| Cursor | 单 Agent | IDE 插件 | 自定义 |
| Continue | 多模型但单 Agent | IDE 插件 | MCP |
| Aider | 单 Agent | CLI | 无 |

Codeg 的独特价值在于 **跨 Agent 协议 + 跨部署形态 + 会话聚合**三位一体。如果只用 Claude Code 单 Agent，Cursor/Continue 体验更轻；如果需要 Claude Code 调 Codex 协作、或统一管理多个 Agent 的历史会话、或要在 Docker 里跑团队共享服务，Codeg 是当前最完整的选择。

## 局限与展望

- **Project Boot** 目前只支持 shadcn/ui，tab-based design 预留扩展位
- **Chat Channels** 目前只内置 Telegram/Lark/iLink，Discord/Slack/钉钉在路上
- **ACP 协议** 还在早期（agentclientprotocol.com），生态成熟度待观察
- **Windows in-place update** 禁用，Linux/macOS 独占

## 总结

Codeg 的核心贡献是给多 Agent 时代提供一个**统一工作空间**——无论是会话聚合、跨 Agent 委托、Office 文档编辑、可视化脚手架，还是 Chat Channels 接入，本质都是在解决"Agent 太多管不过来"的问题。

三个 Rust 二进制（desktop / server / sidecar）的拆分体现了清晰的职责边界：UI 归 Tauri、服务归 Axum、Agent 协议归 MCP companion。ACP + MCP 的协议组合让 Codeg 站在标准上而不是发明轮子。

如果你已经在用 2 种以上 AI 编码 Agent，并且为会话分散、上下文丢失、协作困难头疼，**强烈建议花 30 分钟跑一遍 codeg**——尤其是 Docker 模式，团队共享一个 instance 比每人装桌面版更省心。

仓库地址：[github.com/xintaofei/codeg](https://github.com/xintaofei/codeg)，Apache-2.0 许可，可以放心用、随便改。