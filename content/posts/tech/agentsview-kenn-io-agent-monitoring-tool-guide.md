---
title: "agentsview：把 20+ 编程 Agent 的会话、Token 和成本收进一个本地面板"
date: "2026-06-12T15:11:59+08:00"
slug: "agentsview-kenn-io-agent-monitoring-tool-guide"
description: "kenn-io/agentsview 是 Go 写的本地优先 Agent 监控工具，自动索引各编程 Agent 会话到 SQLite，提供 Web UI 与 CLI 成本统计。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Go", "Svelte", "SQLite", "本地优先"]
---

## 核心判断

agentsview 解决的不是一个新需求，而是一个被掩盖的小麻烦：**当你在 Claude Code、Codex、Copilot CLI、Gemini CLI、Cursor、Kiro 几个 Agent 之间来回切，本地磁盘上其实堆了一堆 `~/.claude/projects/`、`~/.codex/sessions/`、`~/.copilot/` 这种互不相通的会话目录。**

你没法在一个地方搜索昨天问过 Claude 的某条指令，没法知道这个月在不同 Agent 上各花了多少钱，没法比较「Claude Opus 4 和 GPT-5 在我这个仓库上的实际上下文消耗」。

kenn-io/agentsview 把这件事做成一个本地优先的 Go 单文件二进制：自动扫描这 20 多个 Agent 的会话目录，把它们索引到本地 SQLite（FTS5），再开一个 127.0.0.1 的 Web 面板。无需账号、无需上传、Telemtry 只有一个匿名的 `daemon_active` PostHog 上报且默认可关。`agentsview usage daily` 一行命令直接打印每日成本，相比 ccusage 这种每次重新解析原始会话文件的工具，作者在 README 里给的数字是 **快 100 倍**（因为数据已经在 SQLite 里了）。

这不是一个玩具项目 —— 仓库 522 次 commit、Go 1.26+/Svelte 5/Tauri 的完整栈、`make bench-backends` 还自带 SQLite/DuckDB/PostgreSQL 三家对比。它更适合看作 ccusage + Claude-history-tool + claude-code-transcripts 三个想法的合并与升级。

---

## 系统地图

在动手之前，先把 agentsview 的组件摊开看一眼，省得后面被「它到底有几个后端」绕晕。

| 组件 | 角色 | 读 / 写 |
| --- | --- | --- |
| `cmd/agentsview/` | CLI 入口（`serve` / `usage` / `session` / `stats` / `pg` / `duckdb`） | — |
| `internal/parser` | 各 Agent 会话文件的解析器 | 只读 |
| `internal/db` (SQLite) | **主存**，FTS5 全文索引 | 读 + 写 |
| `internal/server` | Web API + SSE 实时推送 | 读 |
| `frontend/` (Svelte 5 SPA) | 仪表盘 / 浏览器 / 搜索 / 活动热力图 | 读 |
| `desktop/` (Tauri) | 桌面壳，包装同一份二进制 | 读 |
| `pg` 子命令 | 推送到共享 PostgreSQL / 从 PG 只读服务 | 推 / 只读 |
| `duckdb` 子命令 | 同步到 DuckDB 镜像 / Quack 协议服务 | 推 / 只读 |

边界只有一条：**SQLite 是主存，所有写入都从它出去**。PostgreSQL 和 DuckDB 都是从 SQLite 推出去的「镜像」，服务模式全部 read-only。你可以先单机玩 SQLite，需要时再决定要不要把团队数据汇到 PG 做共享面板，或者把历史分析导到 DuckDB。

Agent 接入侧，作者用一个表格直接列了 28 个 Agent 的会话根目录，全部支持环境变量覆盖；其中 Antigravity CLI 是特例 —— 新版本存 SQLite `.db`，老版本存 AES-GCM 加密的 `.pb`，后者需要外加一个 `agy-reader` sidecar 才能解密，agentsview 的 file watcher 会自动识别新出现的 `.trajectory.json` 并就地替换 summary mode。

---

## 三种安装方式

仓库的 README 把安装拆得很直白：脚本、桌面包、Docker。我把 macOS 上最稳的两条路写出来，Windows/Linux 可以照葫芦画瓢。

### 1. 一键脚本（开发机首选）

```bash
# macOS / Linux
curl -fsSL https://agentsview.io/install.sh | bash

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://agentsview.io/install.ps1 | iex"
```

装完直接：

```bash
agentsview serve           # 起服务 + 打开 Web UI
agentsview usage daily     # 看最近 30 天每日成本
```

首次 `serve` 会扫一遍本地已装的 Agent，把会话索引到 `~/.agentsview/` 下的 SQLite，自动打开 `http://127.0.0.1:8080`。CLI 是独立命令，**不需要先起服务**就能跑 `usage`、`stats`、`session usage`。

### 2. Homebrew / 桌面 App（不熟终端的人）

```bash
brew install --cask agentsview
```

或者去 [GitHub Releases](https://github.com/kenn-io/agentsview/releases) 拽 macOS / Windows 桌面包。桌面版本质就是 Tauri 包了同一份二进制，启动后行为和 CLI 完全一致。

### 3. Docker（无 GUI 服务器 / 团队共享）

README 的 compose 文件只把端口绑到 `127.0.0.1`，这是有意的 —— 默认拒绝外网访问，需要暴露给非本机浏览器时必须加 `--require-auth`。

```bash
docker run --rm -p 127.0.0.1:8080:8080 \
  -v agentsview-data:/data \
  -v "$HOME/.claude/projects:/agents/claude:ro" \
  -v "$HOME/.forge:/agents/forge:ro" \
  -e CLAUDE_PROJECTS_DIR=/agents/claude \
  -e FORGE_DIR=/agents/forge \
  ghcr.io/kenn-io/agentsview:latest
```

容器化部署的坑只有一个：**只挂载你显式声明的会话目录**。不挂载 + 不设对应 env var，那个 Agent 不会出现 —— agentsview 不会去猜你机器上还装了啥。

---

## 一次完整使用流

光看功能列表你可能抓不到重点。我按「**让 agentsview 帮我看下这周花了多少**」的最小路径走一遍，所有命令都来自 README 原文，门槛很低。

```bash
# 1. 起服务（同时把数据塞进 SQLite + 开 Web 面板）
agentsview serve

# 2. 终端里一行总览
agentsview usage daily

# Output 类似：
# Date         | Claude   | Codex   | Copilot | Total
# 2026-06-08   |   $3.21  |  $0.42  |   —     |  $3.63
# 2026-06-09   |   $5.10  |  $0.87  |  $0.12  |  $6.09
# ...

# 3. 想按模型看细项，加 --breakdown
agentsview usage daily --breakdown --agent claude

# 4. 给 status bar / 状态行用的极简格式
agentsview usage statusline
# → "Today $4.23 / Month $87.12"

# 5. 想看「这个月我到底属于哪种 Agent 用户」
agentsview stats --since 2026-06-01
# → 输出 archetype：automation / quick / standard / deep / marathon
# → 时长、消息数、峰值上下文、工具调用次数的分布

# 6. 单会话精细账
agentsview session usage <session-id>
# → total_output_tokens / peak_context_tokens / cost_usd / has_cost
```

如果脚本要用，每条都支持 `--json`；Shell 友好度上作者是认真想过的。

---

## 三个值得展开的细节

agentsview 的 README 信息密度很高，下面三个点不展开的话你装上之后大概率会撞到。

### 远程转发必须配 `--public-url`

agentsview 默认绑 `127.0.0.1:8080`，并且**校验 `Host` 头防 DNS rebinding**。SSH 端口转发、`exe.dev` / Codespaces / Coder / WSL2 转发，浏览器发的 `Host` 服务端都不认，`/api/v1/settings` 之类会直接 403。

修法：

```bash
# 假设你 ssh -L 18080:127.0.0.1:8080 host
agentsview serve --public-url http://127.0.0.1:18080

# 转发到远端域名
agentsview serve --public-url https://your-workspace.exe.dev
```

`--public-origin` 可以重复 / 逗号分隔追加受信 origin。一旦暴露到 loopback 之外，**加 `--require-auth`**，这是文档原话，没法跳过。

### PostgreSQL / DuckDB 是镜像不是替代

这一点很容易被忽略。`pg serve` 和 `duckdb serve` 都是 read-only 的 `pg push` / `duckdb push` 目标，主写还在本地 SQLite。`duckdb serve` 的搜索路径目前是 substring/regex 回退，**索引搜索仍然走 SQLite FTS5**。所以：

- 想给团队做个只读共享面板 → `pg push` + `pg serve`
- 想在远端用 DuckDB 查历史 → 同步到 `sessions.duckdb`，再 `duckdb quack serve` 暴露 Quack 协议
- 日常搜索 / 实时写 → 始终 SQLite

### Antigravity CLI 那 26 号 Agent 的破窗

`~/.gemini/antigravity/` 这个目录在仓库的「Supported Agents」表里被列成 Antigravity / Antigravity CLI 两条，但 README 单独拉了一节「Antigravity CLI: high-resolution transcripts」解释破窗。

新版本会话存 SQLite `.db`，agentsview 直接索引；**老版本存的是 AES-GCM 加密的 `.pb` 文件**，agentsview 只能 fallback 到 summary mode（用 `history.jsonl` 的 prompt + `brain/` 下的纯文本工件拼个大概）。要恢复完整会话，需要并行跑一个 `agy-reader`：

```bash
go install github.com/mjacobs/agentsview/cmd/agy-reader@latest   # 社区工具 mjacobs/agy-reader
agy-reader --sync     # 一次性把存量 .pb 解密成 <uuid>.trajectory.json
agy-reader --watch    # 持续守护，新会话实时产出 sidecar
```

sidecar 落在 `.pb` 同目录，agentsview 的 file watcher 会就地切换到完整解析，**不用重启**。这是仓库里很体现工程态度的一段：宁可对接一个外部小工具，也不把解密逻辑塞进自己进程里。

---

## 适用边界与采用决策

agentsview 不是一个「让 AI 更聪明」的工具，而是一个「让 AI 使用过程更可观察」的工具。**先判断你的痛点落在哪一类，再决定要不要装。**

适合立刻装的场景：

- 你同时用 ≥ 2 个 CLI 编程 Agent（Claude Code + Codex + Copilot CLI 是高频组合），且本地磁盘上积累了几个月会话
- 团队报销或个人记账需要按日 / 按模型看 Token 和美元成本，ccusage 只覆盖 Claude Code 不够用
- 你经常需要在历史会话里 grep 某条指令、找某个工具调用结果，但不想手动翻 `~/.claude/projects/<hash>/<hash>.jsonl`
- 你用 SSH 远程开发、Codespaces / exe.dev 之类转发环境，需要一个本地回环的「AI 工作台」

可以再等等的场景：

- 你只用单一 Agent（且就是 Claude Code），ccusage 已经够用
- 你想要的是「在 IDE 里直接看会话」（VSCode / JetBrains 集成），这不是 agentsview 的目标，方向也不太对
- 你的会话量已经在百万级，SQLite 单机 FTS5 性能没测过；想冲这个规模建议先用 DuckDB 镜像做分片
- 你对 PostHog 那个匿名 `daemon_active` 事件敏感 —— 关闭方法是 `AGENTSVIEW_TELEMETRY_ENABLED=0` 或 `TELEMETRY_ENABLED=0`，Go test 二进制会硬关闭

采用顺序（避免一次吃撑）：

1. 跑 `agentsview serve` + Web UI，确认 20 多个 Agent 的目录都能被自动发现；如果有缺失就翻 [configuration docs](https://agentsview.io/configuration/) 加环境变量
2. CLI 跑通 `usage daily` 和 `stats`，看 28 天的 archetype 分布是不是符合你的实际使用习惯
3. 想要远端访问再上 `--public-url` + `--require-auth`
4. 团队场景才上 `pg push` / `pg serve`；分析需求再上 `duckdb push` + Quack

完整文档在 [agentsview.io](https://agentsview.io)（README 反复强调的「Full docs」），仓库 license 是 MIT。安装脚本和 docker image 都在 `ghcr.io/kenn-io/agentsview`。
