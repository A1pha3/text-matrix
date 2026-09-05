---
title: "agentsview：把 20+ 编程 Agent 的会话、Token 和成本收进一个本地面板"
date: "2026-06-12T15:11:59+08:00"
slug: "agentsview-kenn-io-agent-monitoring-tool-guide"
github_repo: "kenn-io/agentsview"
description: "kenn-io/agentsview 是 Go 写的本地优先 Agent 监控工具，自动索引各编程 Agent 会话到 SQLite，提供 Web UI 与 CLI 成本统计。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Go", "Svelte", "SQLite", "本地优先"]
---

## 核心判断

> **快速信息卡**
>
> | 项目 | 信息 |
> |------|------|
> | 仓库 | [kenn-io/agentsview](https://github.com/kenn-io/agentsview) |
> | Stars | 5.8k+ |
> | Forks | 650+ |
> | 许可证 | MIT |
> | 语言 | Go / Svelte |
> | 核实 | 2026-09-05（数字随仓库增长而变化） |

agentsview 解决的是一个被掩盖的小麻烦：**当你在 Claude Code、Codex、Copilot CLI、Gemini CLI、Cursor、Kiro 几个 Agent 之间来回切，本地磁盘上其实堆了一堆 `~/.claude/projects/`、`~/.codex/sessions/`、`~/.copilot/` 这种互不相通的会话目录。**

你没法在一个地方搜索昨天问过 Claude 的某条指令，没法知道这个月在不同 Agent 上各花了多少钱，也没法比较不同模型在同一个仓库上的实际上下文消耗。

kenn-io/agentsview 把这件事做成一个本地优先的 Go 单文件二进制：自动扫描这 20 多个 Agent 的会话目录，把它们索引到本地 SQLite（FTS5），再开一个 127.0.0.1 的 Web 面板。无需账号、无需上传，Telemetry 只有一个匿名的 `daemon_active` PostHog 上报，默认开启、可用环境变量关掉。`agentsview usage daily` 一行命令直接打印每日成本。相比 ccusage 这类每次都要重新解析原始会话 JSONL 的工具，agentsview 首次把会话索引进 SQLite 后后续查询走数据库、不重解析，重复统计自然更快；README 自带的 `make bench-backends` 比较的是 SQLite / DuckDB / PostgreSQL 三家的读取延迟，并不和 ccusage 对标。

这不是一个玩具项目 —— 仓库 1175 次 commit、Go 1.27 / Svelte 5 / Tauri 的完整栈，`make bench-backends` 还自带 SQLite / DuckDB / PostgreSQL 三家读取对比（默认 fixture 1000 会话、64000 消息，需要 Docker）。它更适合看作 ccusage + Claude-history-tool + claude-code-transcripts 三个想法的合并与升级。

---

## 学习目标

读完这篇文章后，你应该能够：

- 说出 agentsview 的核心价值：为什么需要在多个 AI Coding Agent 之间统一监控会话和成本
- 解释 agentsview 的架构：SQLite 主存、PostgreSQL/DuckDB 镜像、只读服务模式
- 通过 `agentsview serve` 和 `agentsview usage daily` 快速查看 Agent 使用成本和会话统计
- 配置远程访问（`--public-url`）和团队共享（PostgreSQL 镜像）
- 判断 agentsview 是否适合你的场景，并制定采用顺序

## 目录

- [系统地图](#系统地图)
- [三种安装方式](#三种安装方式)
- [一次完整使用流](#一次完整使用流)
- [三个值得展开的细节](#三个值得展开的细节)
- [适用边界与采用决策](#适用边界与采用决策)

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

新版 README 把写入侧的常驻进程拆成了 `daemon` 子命令族（`daemon start` / `status` / `restart` / `stop`）：桌面 App 和需要新鲜数据的命令（`sync`、`usage`、`pg push`、`duckdb push`）在有必要时自动拉起它；`serve --background` 仍保留，适用于那些需要 serve 专属 flag（如 `--no-sync`、非回环 `--host`）的一次性后台任务。

Agent 接入侧，README 的「Supported Agents」表列出了 50+ 个会话条目（同款工具的 CLI / IDE 变体会占多行），目录全部支持环境变量覆盖。其中 Antigravity CLI 是特例：新版本把轨迹存成 SQLite `.db`，旧版本是 AES-GCM 加密的 `.pb`，两种格式的完整转写都依赖一个 `<uuid>.trajectory.json` sidecar；没有 sidecar 时 agentsview 只能降级到 summary mode。要补完整转写，需要并行跑一个 `agy-reader`，它连上本地 Antigravity daemon 逐段解密，把 sidecar 写到源文件旁边，agentsview 的 file watcher 会自动切换到完整解析，不用重启。

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
# → total_output_tokens / peak_context_tokens / cost / has_cost
#   金额以整数 microdollar 对象返回（如 {"cost":{"microdollars":2410000}}），CLI 渲染成美元
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

### Antigravity CLI：靠 sidecar 补完整转写

README 在「Supported Agents」表里把 Antigravity 和 Antigravity CLI 分成两个条目（后者目录在 `~/.gemini/antigravity-cli/`），还单独拉了一节「Antigravity CLI: high-resolution transcripts」解释它为什么特殊。

Antigravity CLI 的会话轨迹有两种落盘格式：新版本存 SQLite `.db`，旧版本是 AES-GCM 加密的 `.pb`。无论哪种，**完整转写（结构化工具调用、结果、推理、diff）都来自一个 `<uuid>.trajectory.json` sidecar**；没有 sidecar 时，agentsview 只能降级到 summary mode——用 `history.jsonl` 的 prompt 加纯文本工件拼个大概。要补上完整转写，需要并行跑 `agy-reader`：

```bash
go install github.com/mjacobs/agy-reader@latest   # 社区工具，独立仓库，不在 agentsview 里
agy-reader --sync      # 给存量会话批量生成 sidecar
agy-reader --watch     # 持续守护，新会话实时产出
```

agy-reader 不是直接把 `.pb` 文件解开，而是连上本地 Antigravity daemon 逐段解密，把 `<uuid>.trajectory.json` 写到源文件旁边；它通过解析 `~/.gemini/antigravity-cli/cli.log` 发现 daemon 地址，发现不了（比如日志轮转）就打印定位端口的手动办法，再配合 `ANTIGRAVITY_DAEMON_URL` 环境变量指定。sidecar 落在源文件同目录，agentsview 的 file watcher 会自动切到完整解析，**不用重启**。这是仓库里很体现工程态度的一段：宁可对接一个外部小工具，也不把解密逻辑塞进自己进程里。

---

## 适用边界与采用决策

agentsview 是一个「让 AI 使用过程更可观察」的工具。**先判断你的痛点落在哪一类，再决定要不要装。**

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

## 自测题

下面 5 道题用来检验你对 agentsview 核心概念和使用方式的掌握程度。点击参考答案前的三角展开查看解析。

1. agentsview 的架构中，哪个组件是主存储？PostgreSQL 和 DuckDB 镜像的角色是什么？

<details>
<summary>参考答案</summary>

- **主存储**：SQLite（位于 `~/.agentsview/` 下），使用 FTS5 全文索引
- **PostgreSQL 镜像**：通过 `pg push` 推送数据，提供只读共享面板，适合团队场景
- **DuckDB 镜像**：通过 `duckdb push` 同步历史数据，支持 Quack 协议查询
- **关键边界**：所有写入都从 SQLite 出去，PG 和 DuckDB 都是只读镜像，不能替代 SQLite 作为主存

（对应章节：系统地图）

</details>

2. 在 SSH 远程转发场景下，`agentsview serve` 为什么要配置 `--public-url`？不配置会出现什么错误？

<details>
<summary>参考答案</summary>

- **原因**：agentsview 默认绑 `127.0.0.1:8080` 并校验 `Host` 头防 DNS rebinding。SSH 转发后浏览器发的 `Host` 与服务端预期不符，会导致 `/api/v1/settings` 等接口返回 403
- **配置方式**：`agentsview serve --public-url http://127.0.0.1:18080`（假设 SSH 转发端口为 18080）
- **安全注意**：一旦暴露到 loopback 之外，必须加 `--require-auth`

（对应章节：三个值得展开的细节）

</details>

3. agentsview 与 ccusage 相比，性能优势来自哪里？

<details>
<summary>参考答案</summary>

- **ccusage**：每次运行重新解析原始会话文件（JSONL），随着会话积累变慢
- **agentsview**：首次运行将会话索引到 SQLite（FTS5），后续查询走数据库、不重解析，重复成本统计自然更快（README 未给出与 ccusage 的对比数字，其 `bench-backends` 只比较 SQLite / DuckDB / PostgreSQL 三家）
- **实际影响**：会话量大的用户（几个月累积、多个 Agent）感受明显；新安装、会话少的场景下差异不大

（对应章节：核心判断）

</details>

4. Antigravity CLI 的老版本会话文件为什么需要 `agy-reader` sidecar？新版本是怎么处理的？

<details>
<summary>参考答案</summary>

- **两种格式**：Antigravity CLI 会话轨迹可能存为 SQLite `.db`（新版本）或 AES-GCM 加密的 `.pb`（旧版本），但完整转写（结构化工具调用、结果、推理、diff）都来自 `<uuid>.trajectory.json` sidecar
- **没有 sidecar 时**：无论 `.db` 还是 `.pb`，agentsview 都只能降级到 summary mode——用 `history.jsonl` 的 prompt 加纯文本工件拼个大概
- **agy-reader 方案**：独立社区仓库，连接本地 Antigravity daemon 逐段解密，为两类会话生成 `.trajectory.json` sidecar；`--sync` 批量、`--watch` 持续，agentsview 的 file watcher 自动切到完整解析，无需重启

（对应章节：三个值得展开的细节）

</details>

5. 说出 agentsview 的采用顺序，并解释为什么 SQLite 单机是第一步。

<details>
<summary>参考答案</summary>

**采用顺序**：
1. 跑 `agentsview serve` + Web UI，确认 Agent 目录自动发现
2. CLI 跑通 `usage daily` 和 `stats`，看 archetype 分布
3. 需要远端访问再上 `--public-url` + `--require-auth`
4. 团队场景才上 `pg push` / `pg serve`；分析需求再上 `duckdb push` + Quack

**为什么 SQLite 单机是第一步**：agentsview 的所有写入都在本地 SQLite，PG/DuckDB 是镜像。先确认本地索引、成本统计、会话搜索都正常工作，再考虑远程访问和团队共享。跳过第一步直接上 PG 镜像，出问题时不方便定位是解析器、SQLite 还是 PG 推送的故障。

（对应章节：适用边界与采用决策）

</details>

[↑ 回到目录](#目录)

## 练习

### 练习1：评估你的 Agent 使用场景

回顾你最近一个月使用 AI 编程 Agent 的经历，回答以下问题：

1. 你同时在使用几个 AI 编程 Agent？（Claude Code、Cursor、Copilot CLI 等）
2. 你是否需要在多个 Agent 之间查找之前的问题和回答？
3. 你是否需要跟踪不同 Agent 的成本消耗？
4. 你的会话历史是否已经积累了几个月？

如果以上问题的答案多为"是"，那么 agentsview 可能适合你的场景。

### 练习2：配置远程访问

假设你需要在远程服务器上运行 agentsview，并通过 SSH 端口转发在本地浏览器访问。请完成以下配置：

1. 在远程服务器上启动 agentsview，并配置 `--public-url` 参数
2. 在本地机器上配置 SSH 端口转发
3. 在本地浏览器中访问 agentsview Web UI
4. 确认成本统计和会话搜索功能正常工作

### 练习3：分析你的 Agent 使用模式

使用 agentsview 的 `stats` 命令分析你的 Agent 使用模式：

1. 运行 `agentsview stats --since <起始日期>` 查看你的使用档案
2. 分析你的 archetype（automation / quick / standard / deep / marathon）
3. 查看你的时长、消息数、峰值上下文、工具调用次数的分布
4. 根据分析结果，调整你的 Agent 使用策略

## 进阶路径

### 阶段1：深入理解 agentsview 架构

- **目标**：理解 agentsview 的组件结构和数据流
- **行动**：
  1. 阅读 agentsview 源码中的 `cmd/agentsview/` 和 `internal/` 目录
  2. 理解 SQLite 主存、PostgreSQL/DuckDB 镜像的架构设计
  3. 分析 `internal/parser` 如何解析不同 Agent 的会话文件
  4. 理解 file watcher 如何自动识别新会话文件
- **参考资源**：
  - [agentsview GitHub 仓库](https://github.com/kenn-io/agentsview)
  - [agentsview 架构文档](https://agentsview.io/architecture/)

### 阶段2：优化性能和扩展性

- **目标**：让你的 agentsview 部署更高效、更可扩展
- **行动**：
  1. 调整 SQLite 的 FTS5 索引配置，优化搜索性能
  2. 配置 PostgreSQL 镜像，实现团队共享面板
  3. 使用 DuckDB 镜像，实现历史数据分析
  4. 优化 file watcher 的性能，减少资源消耗
- **参考资源**：
  - [SQLite FTS5（全文搜索）文档](https://www.sqlite.org/fts5.html)
  - [agentsview 语义搜索说明](https://agentsview.io/semantic-search/)
  - [agentsview 命令参考](https://agentsview.io/commands/)

### 阶段3：集成到团队工作流

- **目标**：让团队成员共享 agentsview 数据，提升协作效率
- **行动**：
  1. 配置 PostgreSQL 镜像，让团队成员共享会话和成本数据
  2. 设置访问控制和认证，保护敏感数据
  3. 将会话数据导出到团队知识库，便于知识共享
  4. 配置自动化报告，定期发送成本统计和使用分析
- **参考资源**：
  - [agentsview 团队共享（PostgreSQL）文档](https://agentsview.io/postgresql/)
  - [agentsview 信任模型与安全说明（仓库 SECURITY.md）](https://github.com/kenn-io/agentsview/blob/main/SECURITY.md)

## 资料口径说明

为避免把 README 文案直接写成结论，本文的几个关键判断采用了下面的取径方式：

- agentsview 的架构、安装命令、CLI 命令、Web UI 功能、PostgreSQL/DuckDB 镜像、Antigravity CLI 支持，直接以其 GitHub README 和官方文档为准。
- `make bench-backends` 是 README 自带的 SQLite / DuckDB / PostgreSQL 三家读取对比（fixture 1000 会话、64000 消息，需要 Docker），本文不把它的数字当作与 ccusage 的性能对标；重复成本统计"走库更快"仅依据索引后不再重解析这一事实推断。
- Supported Agents 表的条目数、Go 版本、commit 数、Stars/Forks 以 2026-09-05 核实的 GitHub 数据为准，会随仓库增长变化。
- 本文的适用场景和采用顺序，结合 README 的功能列表和实际使用场景进行交叉比对。

完整文档在 [agentsview.io](https://agentsview.io)（README 反复强调的「Full docs」），仓库 license 是 MIT。安装脚本和 docker image 都在 `ghcr.io/kenn-io/agentsview`。

