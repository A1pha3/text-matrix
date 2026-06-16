---
title: "herdr 深度解析：5.7K Stars 的终端原生 AI Agent 多路复用器，tmux 之后为什么需要它"
date: "2026-06-15T21:08:29+08:00"
slug: herdr-rust-agent-multiplexer-guide
description: "ogulcancelik/herdr 是 Rust 写的 AI Agent 终端多路复用器，补 tmux 缺 agent 状态、GUI 客户端缺真终端语义。本文拆解它的设计取舍、状态识别与适用场景。"
tags: ["herdr", "tmux", "终端复用器", "AI Agent", "Rust"]
categories: ["技术笔记"]
author: 钳岳星君
---

# herdr 深度解析：5.7K Stars 的终端原生 AI Agent 多路复用器，tmux 之后为什么需要它

**判断**：herdr 不是"另一个 tmux fork"，也不是"又一个 TUI agent 客户端"。它精确地卡在 **tmux（持久 + pane）** 与 **GUI agent 客户端（agent 状态可视化）** 之间的空白里——保留 tmux 的 pane 真实终端语义，加上 GUI 那种"哪个 agent blocked / working / done"的侧栏，再通过 **Unix socket + 自家 CLI** 让 agent 自己编排自己。2026-03-27 立项，2026-06-15 已经 5,695 stars、339 forks，3 个月跑出这种增长曲线，**意味着"AI 时代的 tmux"这个空位确实存在**。

如果你属于下面任何一种情况，这篇值得读：

- 在终端里同时跑 2 个以上 Claude Code / Codex / Cursor Agent 的人
- 用 tmux 跑 agent 进程、但又羡慕 GUI 那种侧栏状态的人
- 想给 agent 写"自己开 tab、起 pane、等另一个 agent 完成"这种 orchestrator 的人
- 想用 Rust 写 TUI 应用的工程师，想看 ratatui + crossterm + tokio 怎么组合的样本

---

## 阅读导航

- **5 分钟判断值不值得装**：看「先看结论」
- **理解它在生态里卡的位置**：看「为什么 tmux 不够、GUI 又太重」
- **想了解它的核心抽象**：看「核心模型：server / workspace / tab / pane」
- **想知道它怎么"看到"agent 在干嘛**：看「agent 状态识别机制」
- **想给自己的 agent 接上 herdr**：看「socket API + SKILL.md」
- **想评估二次开发价值**：看「架构拆解」和「Cargo 依赖全景」
- **要决定采用顺序**：看「适合谁 / 不适合谁 / 怎么装」

---

## 先看结论

| 维度 | 实际情况 |
|------|----------|
| Stars | 5,695+（2026-06-15） |
| Forks | 339+ |
| 语言 | Rust（0.6.10，Cargo 2021 edition） |
| 协议 | AGPL-3.0-or-later + 商业双许可（不可合规 AGPL 的组织可买商业证） |
| 仓库 | <https://github.com/ogulcancelik/herdr> |
| 官网 | <https://herdr.dev> |
| 主要 TUI 栈 | ratatui 0.30 + crossterm 0.29 + tokio 1 + portable-pty 0.9 + interprocess 2.4 |
| 安装 | `curl -fsSL https://herdr.dev/install.sh \| sh` / Homebrew / mise / 直接下 binary |
| 平台 | macOS / Linux 稳定；Windows preview beta |
| 目标用户 | 同时跑 ≥2 个 AI coding agent、且不愿意离开终端的人 |
| 与 tmux 关系 | 兼容运行在 tmux 内部；不替代 tmux，是上层 |

一句话：**它是给"AI coding agent 多任务场景"重新做的终端复用器，把 tmux 缺的 agent 状态补上，把 GUI agent 客户端的真终端语义补回来**。

---

## 为什么 tmux 不够、GUI 又太重

把当前市面上的方案放一起，空白点很清晰：

| 方案 | 持久会话 | pane / 切分 | 真实终端视图 | agent 状态可视化 | 留在终端里 | 轻量 |
|------|----------|------------|--------------|-------------------|------------|------|
| tmux | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Warp / Wave Terminal | 部分 | ✅ | ❌（自带模拟） | 部分 | ❌（自带外壳） | ❌ |
| Cursor / Claude Desktop | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| VS Code + Copilot | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **herdr** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

herdr README 里有同一张表，原话：

> tmux gives you persistence and panes, but it was built before agents existed. gui managers show agent state, but they make you leave your terminal and use their wrapped view. herdr is persistence and awareness in one tool that stays out of your way.

这句话点出了 3 个真实痛点：

1. **tmux 不会告诉你哪个 pane 里的 agent 在等你回复**。`tmux ls` 只看进程名，但 Claude Code / Codex / Droid 这种 TUI 跑起来后，进程名都是 `node` / `python` / `bash`，tmux 完全区分不出来。
2. **GUI 客户端（Cursor / Claude Desktop）会拦截终端**。你看到的是它们"重新渲染"的输出，不是 agent 自己 TUI 的真实字符流。某些 ANSI 序列、转义码、progressive output 会失真。
3. **同时跑多个 agent 时，"哪个先好了"这件事在 tmux 和 GUI 里都不直观**。tmux 没侧栏，GUI 多个窗口切来切去累。

herdr 一次性解决这三点：**保留 tmux 风格的 pane 真实终端，加 GUI 风格的侧栏 agent 状态，再加一个 Unix socket 让 agent 自己也参与编排**。

---

## 核心模型：server / workspace / tab / pane

herdr 的 4 层抽象要记牢，文档里所有命令都对应这 4 层。

### 1. server（后台服务进程）

`herdr` 启动时默认 attach 到一个**后台 server**。`prefix q`（detached client）只关掉客户端，不关 server。这是它和 tmux 不同的关键点：

- tmux：session 既是 server 又是 client
- herdr：server 是常驻进程，client 可以是多个终端窗口

关掉终端 ≠ 关掉 agent 进程。`herdr server stop` 才会真正停掉 server 杀掉所有 pane。

### 2. workspace（项目级容器）

workspace 围绕 **git 仓库或文件夹** 组织，**默认按第一个 tab 的根 pane 命名**（通常是 repo 名）。一个 workspace = 一个项目。

```bash
herdr workspace list
```

### 3. tab（workspace 内子上下文）

tab 在 workspace 内部做"语义分组"。例如一个 repo 里有 frontend / backend / infra 三个方向，可以建 3 个 tab，每个 tab 独立 pane 树。

```bash
herdr tab create --workspace 1 --label backend
herdr tab list --workspace 1
```

### 4. pane（真实终端进程）

pane 是**真正跑 shell / agent / server / log tail 的终端**。这层最关键：

> Panes are real terminal processes, not rewritten agent views.

herdr 用 `portable-pty` 跑 PTY 进程，**不解析也不改写 agent 的 ANSI 输出**。你看到的就是 agent 自己的 TUI。

### ID 编码

仓库 SKILL.md 里专门有一段警告：

> ids can compact when tabs, panes, or workspaces are closed. do not treat them as durable ids. re-read ids from `workspace list`, `tab list`, `pane list`, or create/split responses when you need a current id. do not guess that an older `1-3` is still the same pane later.

ID 格式：

- workspace: `1`, `2`, `3`...
- tab: `1:1`, `1:2`...
- pane: `1-1`, `1-2`...

这是**会话内紧凑 ID**，关掉中间的 tab/pane 会让后续 ID 复用。**写 orchestrator 时必须每次重新读**。

---

## agent 状态识别机制

herdr 把 pane 里的进程按 4 个状态归类：

| 状态 | 颜色 | 含义 |
|------|------|------|
| `blocked` | 🔴 | agent 等待你输入或批准 |
| `working` | 🟡 | agent 正在跑 |
| `done` | 🔵 | agent 跑完但你还没看 |
| `idle` | 🟢 | 跑完且已看过 |

**默认检测不靠任何 hook**——完全是读 foreground 进程名 + 解析 terminal output 的启发式。零配置。

如果你装了官方 integration（`herdr integration install claude`），状态还会升级到**更准的语义层**：

- **session identity 恢复**：知道这个 pane 对应的是哪次 Claude Code session，重启 server 后能继续
- **semantic state 报告**：直接读 agent 内部状态而不是从输出猜

目前的 official integration 列表（`README` 表格）：

| agent | idle/done | working | blocked | 备注 |
|-------|-----------|---------|---------|------|
| pi | ✅ | ✅ | partial | 双向 |
| claude code | ✅ | ✅ | ✅ | session identity |
| codex | ✅ | ✅ | ✅ | session identity |
| droid | ✅ | ✅ | ✅ | session identity |
| amp | ✅ | ✅ | ✅ | 默认检测 |
| opencode | ✅ | ✅ | ✅ | 双向 |
| grok cli | ✅ | ✅ | ✅ | 默认检测 |
| hermes agent | ✅ | ✅ | ✅ | 双向 |
| kilo code cli | ✅ | ✅ | ✅ | 双向 |
| cursor agent | ✅ | ✅ | ✅ | session identity |
| antigravity cli | ✅ | ✅ | ✅ | 默认检测 |
| kimi code cli | ✅ | ✅ | ✅ | session identity |
| github copilot cli | ✅ | ✅ | ✅ | session identity |
| qodercli | ✅ | ✅ | ✅ | session identity |
| kiro cli | ✅ | ✅ | — | session identity |

双向 = 同时支持 session identity + semantic state；session identity = 只能恢复 session，状态还是从 screen 推。

> ⚠️ "detected but not fully tested: gemini cli, cline."——这两家当前未充分测试。

对未在列表里的 agent，herdr 仍然能当终端复用器用，只是状态识别会回到进程名 + 输出启发式，准确性会下降。

---

## socket API + SKILL.md：让 agent 自己编排

herdr 的一个**反常规设计**是给 agent 暴露了一个**本地 Unix socket**，让 agent 自己能用 CLI 编排 herdr：

```text
The local Unix socket lets agents create workspaces,
split or zoom panes, spawn helpers, read output,
and wait for state changes.
```

CLI 例子（节选自 `SKILL.md`）：

```bash
# 看自己当前在哪个 pane
herdr pane list

# 在当前 workspace 开个新 tab
herdr tab create --workspace 1 --label "test-runner"

# 在指定 tab 竖着切 pane 跑命令
herdr pane split --tab 1:2 --vertical
herdr pane run --pane 1-2 -- pytest -x

# 等另一个 agent 跑完
herdr pane wait --pane 2-1 --state done
```

这意味着 **agent 可以起后台 test runner pane、读它的输出、等它完成再继续**。这是 tmux 完全做不到、GUI 客户端又不开放的能力。

仓库里有独立的 [`SKILL.md`](https://github.com/ogulcancelik/herdr/blob/master/SKILL.md) 文件，专门给 agent 看——这是给"AI 知道怎么用 herdr"准备的入口，自带版本和 IDE 集成（`.codex/`、`.pi/`、`.zed/` 目录说明 repo 已针对这些 agent 配置）。

协议细节在 <https://herdr.dev/docs/socket-api/>，包括 event 订阅、状态机、错误码。**这一层是 herdr 真正的"AI 时代差异化"**。

---

## 架构拆解

`src/` 目录按职责切得非常清楚：

```text
src/
├── main.rs              # 入口
├── cli.rs / cli/        # CLI 解析 + 子命令
├── server/              # 后台 server：会话、pane 进程管理
├── client/              # TUI 客户端（ratatui 渲染）
├── pane/                # pane 抽象 + 进程生命周期
├── persist.rs / persist/  # 会话持久化 + pane 状态恢复
├── detect/              # agent 状态识别启发式
├── integration/         # 官方 agent 集成
├── protocol/            # socket 协议定义
├── ipc.rs               # Unix socket IPC
├── api/                 # socket API 实现
├── config.rs / config/  # 配置文件 + 主题
├── input/               # 键盘 / 鼠标输入
├── render_prof.rs       # 渲染性能分析
├── remote.rs / remote/  # SSH remote attach
├── update.rs            # 自更新 + channel 管理
├── handoff_runtime.rs   # live handoff（旧 server → 新 server）
├── agent_resume.rs      # agent session resume
├── worktree.rs          # git worktree 集成
├── workspace.rs / workspace/  # workspace 模型
├── ghostty/             # Ghostty 终端兼容层
├── terminal/            # 终端能力探测
├── terminal_theme.rs    # 主题解析
├── terminal_notify.rs   # 系统通知
├── sound.rs             # 声音事件
├── selection.rs         # 文本选择 / 复制
├── plugin_command.rs / plugin_paths.rs  # 插件命令系统
├── product_announcements.rs / release_notes.rs  # 公告 / release notes
└── ...（约 50 个文件）
```

几个值得单独点出来的：

- **`persist/` + `persist.rs`**：session 持久化，让 server 重启后 pane 能恢复。**支持 opt-in 恢复最近屏幕历史**。
- **`handoff_runtime.rs`**：实验性 live handoff——`herdr update --handoff` 尝试把旧 server 上的 pane 进程（包括前台进程如 dev server）迁移到新 server。这是 tmux 一直想做但没做好的功能。
- **`agent_resume.rs`**：配合 integration 的 session identity 实现，server 重启或更新后，agent pane 能从 native session 恢复上下文。
- **`detect/`**：状态识别启发式的核心。**没读源码不要随便改这块**，因为这是 herdr 相对 tmux 的关键差异。
- **`protocol/`** + **`ipc.rs`**：socket 协议实现，CLI 和 TUI 客户端都通过它和 server 通信。

---

## Cargo 依赖全景

`Cargo.toml` 关键依赖：

| 依赖 | 版本 | 用途 |
|------|------|------|
| `ratatui` | 0.30 | TUI 渲染（带 `unstable-rendered-line-info` feature） |
| `crossterm` | 0.29 | 跨平台终端操作 |
| `tokio` | 1 | async runtime（`rt-multi-thread` + `macros` + `sync` + `time`） |
| `portable-pty` | 0.9 | 跨平台 PTY |
| `interprocess` | 2.4.2 | 跨平台 IPC（含 Unix socket、named pipe） |
| `serde` + `serde_json` + `bincode` | 1 / 1 / 2 | 序列化（bincode 走 socket 协议，json 走配置） |
| `toml` | 0.8 | 配置文件 |
| `png` | 0.17 | kitty graphics protocol（图片渲染） |
| `sha2` | 0.10 | checksum（自更新校验） |
| `base64` | 0.22.1 | 编码 |
| `regex` | 1 | 状态识别 |
| `ctrlc` | 3 | SIGINT 处理 |
| `libc` | 0.2 | Unix 系统调用 |

依赖数控制在 14 个左右，**对一个终端复用器来说非常克制**。`ratatui` + `crossterm` + `tokio` + `portable-pty` + `interprocess` 这 5 个是核心，其他都是补足。

---

## 怎么装

按 README 顺序有 4 种官方通道：

### 1. 一键安装（macOS / Linux）

```bash
curl -fsSL https://herdr.dev/install.sh | sh
```

### 2. Homebrew

```bash
brew install herdr
```

### 3. mise

```bash
mise use -g herdr
```

如果 mise 报 `herdr not found in mise tool registry`，**更新 mise 再重试**——老版本 mise 的 herdr registry 条目不存在。临时回退：

```bash
mise use -g github:ogulcancelik/herdr
```

### 4. 源码构建

```bash
git clone https://github.com/ogulcancelik/herdr
cd herdr
cargo build --release
./target/release/herdr
```

仓库根目录有 `justfile`，提供：

```bash
just test    # 单元测试
just check   # formatting + tests + maintenance checks
```

### 5. Windows

preview-only beta。PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -c "irm https://herdr.dev/install.ps1 | iex"
```

目前**没有原生稳定 Windows 版**。

### 6. 更新

直接装：

```bash
herdr update
```

但 README 写了一个关键点：

> a running server keeps using the old process until it is stopped or handed off.

**光跑 `herdr update` 不等于升级了 server**。要真用新版本，必须先：

```bash
herdr server stop
herdr          # 重启 attach，新 server
```

或者用实验性的 live handoff：

```bash
herdr update --handoff
```

Homebrew / mise / Nix 装的不走 herdr 自己的 updater，要用 `brew upgrade herdr` / `mise upgrade herdr` / `nix upgrade`。

### 7. Preview channel

直接装的可以切预览版：

```bash
herdr channel set preview   # 切到 master 分支构建
herdr channel set stable    # 切回稳定
```

Homebrew / mise / Nix 仍走稳定版。

---

## 快速上手：3 分钟跑起来

```bash
# 在你的项目根目录
cd ~/code/my-project
herdr
```

启动后：

- 默认 attach 后台 server
- 没有 workspace 时自动开一个
- 根 pane 跑你当前的 shell

切 pane / workspace 用 `ctrl+b` 前缀：

| 键 | 动作 |
|----|------|
| `prefix c` | 新 tab |
| `prefix n` / `prefix p` | 下/上一个 tab |
| `prefix 1..9` | 直接跳 tab |
| `prefix shift+n` | 新 workspace |
| `prefix shift+g` | 新 worktree |
| `prefix shift+w` | 重命名 workspace |
| `prefix h/j/k/l` | 切 pane 焦点 |
| `prefix shift+h/j/k/l` | 交换 pane |
| `prefix v` / `prefix minus` | 竖/横切 pane |
| `prefix x` | 关 pane |
| `prefix b` | 切侧栏 |
| `prefix z` | zoom pane（最大化当前 pane） |
| `prefix r` | resize 模式 |
| `prefix w` | workspace 导航 |
| `prefix g` | session 导航 |
| `prefix q` | **detach client**（server 继续跑） |

想恢复 attach：

```bash
herdr    # 默认 attach 默认 server
```

```bash
herdr session attach work    # attach 命名 session
herdr session stop work      # 停命名 session
herdr session list           # 列出所有 session
```

命名 session 是**独立的 server namespace**——你有一个主 session 跑日常、一个 work session 跑长任务、一个 review session 跑 review agent，互不干扰。

---

## 远程 attach

README 给的 SSH 用法：

```bash
ssh you@yourserver
herdr
```

本地直接 attach 远端：

```bash
herdr --remote workbox
herdr --remote ssh://you@yourserver:2222
```

实现细节在 `src/remote.rs` + `src/remote/`，通过 SSH keepalive 维持连接，**默认会 fallback 管理 SSH config**，可用配置项关闭：

```toml
[remote]
manage_ssh_config = false
```

直接 attach 到 server-owned terminal：

```bash
herdr agent attach <target>
herdr terminal attach <terminal_id>
```

适合"远端跑 dev server、本地看输出"的场景。

---

## 配置文件

```text
~/.config/herdr/config.toml
```

打印默认配置：

```bash
herdr --default-config
```

主题内置 18 种：catppuccin、terminal、tokyo night、gruvbox、one、solarized、kanagawa、rosé pine、vesper，加上 light 变体。In-app 还能切 theme / sound / toast 偏好。

日志：

```text
~/.config/herdr/herdr-client.log
~/.config/herdr/herdr-server.log
```

持久 session 模式下，这俩是最常用的排查文件。

---

## 主题和扩展点

- **18 个内置主题**——覆盖主流暗色 + 几套 light 变体
- **keybindings** 配置：完全自定义，包括 `prefix+n` 风格的前缀模式和 `ctrl+alt+n` 风格的直绑模式
- **plugin commands**：`plugin_command.rs` 暴露的扩展点（README 写得比较简略，需要看源码）
- **integration 系统**：`herdr integration install <agent>` 是给 agent 添加 session identity / semantic state 的官方通道

---

## 适合谁

✅ **适合**：

- 在终端里同时跑 2+ 个 Claude Code / Codex / Droid / Cursor Agent 的工程师——`blocked / working / done` 侧栏比 tmux 强太多
- 想要 tmux 的 pane + persist，但嫌 tmux 不会识别 agent 状态的人
- 想给自己的 agent 写 orchestrator（开 tab、起 pane、等状态）的 prompt 工程师
- macOS / Linux 终端重度用户，每天 8+ 小时在 TUI 里
- 想要"agent 跑在真实终端、不是被 GUI 改写的输出"——这点 herdr 严格做到了

## 不适合谁

❌ **不适合**：

- 只想跑单个 agent、不在乎多 pane 状态的人——直接用 Claude Code / Codex CLI 就够了
- Windows 用户想用稳定版——目前只有 preview beta
- 不能接受 AGPL-3.0 又不愿意买商业证的组织——双许可明确写了这种限制
- 想要"零学习成本"的 GUI 党——herdr 是 prefix + 键位驱动的，**必须接受 tmux 风格键位**
- 想要"开箱即用支持所有 agent"——目前官方 integration 覆盖 15 个，gemini cli / cline 还没充分测试，未列出的 agent 只能走默认启发式

---

## 采用顺序建议

按用户类型给 3 条不同的路径：

### 路径 A：终端重度用户、想一步到位

1. `curl -fsSL https://herdr.dev/install.sh | sh` 装上
2. `cd` 到项目根跑 `herdr` 试一下默认 session
3. 安装 1-2 个最常用的 agent integration：`herdr integration install claude` / `codex`
4. 把手头 tmux session 逐步迁过来，对比 blocked / working / done 状态识别准确度
5. 读 `SKILL.md` 试着自己用 `herdr pane run` 跑后台 test runner

### 路径 B：AI agent 编排工程师、想自己接 socket

1. 装上 herdr
2. **读 [`SKILL.md`](https://github.com/ogulcancelik/herdr/blob/master/SKILL.md)** 全文——这是给 agent 看的入口文档
3. 看 [socket API 文档](https://herdr.dev/docs/socket-api/)，关注事件订阅和状态机
4. 在自己的 agent prompt 里加入"开新 pane → 起后台任务 → 等 done"的工作流
5. 跑 `herdr update --handoff` 试一下 live handoff 是否对你的 agent 稳定

### 路径 C：Rust TUI 应用开发者、想参考架构

1. `git clone` 仓库
2. 先读 `Cargo.toml` 确认依赖面
3. 从 `src/main.rs` 顺到 `src/server/`、`src/client/`、`src/pane/` 三块
4. 看 `src/protocol/` + `src/ipc.rs` 学 Unix socket 协议设计
5. 看 `src/agent_resume.rs` + `src/handoff_runtime.rs` 学 server 升级时的进程迁移
6. **`AGENTS.md`** + **`CLAUDE.md`** 看作者留给 AI agent 的协作约定

---

## 风险与边界

- **AGPL-3.0-or-later 商业分发限制**：如果你的产品集成 herdr 源码并通过网络对外提供服务，AGPL-3.0 要求你也开源。**这种情况下必须买商业证**。README 末尾留了 `hey@herdr.dev` 联系方式。
- **Windows 仅 preview**：生产用 Windows 必须自己测稳定性。
- **agent 状态识别依赖 heuristic**：未在官方 integration 列表里的 agent，blocked / working / done 准确度会下降。**写关键工作流前，先在真实环境跑一天验证状态切换**。
- **live handoff 是实验性**：`herdr update --handoff` 文档明确写了 experimental，生产环境慎用。
- **pty 输出不被改写**：这是优势也是边界——某些 agent 在 GUI 客户端里会用到 `kitty graphics protocol` 显示图片，herdr 的 `kitty_graphics.rs` 是支持的但有版本限制，老的 agent 可能显示异常。
- **依赖数虽然克制，但 ratatui 升级频繁**：跟着 ratatui 升级的 fork 要注意 breaking change，herdr 用了 `unstable-rendered-line-info` 这种 unstable feature，**未来 ratatui 大版本升级时可能需要适配**。

---

## 总结

herdr 的真正价值不是"又一个终端复用器"——它把 **AI coding agent 多任务场景** 里的 4 个真实痛点（持久 pane、agent 状态可视化、真实终端语义、agent 自我编排）一次性解决了。**5.7K stars / 3 个月**的增速说明这个空位确实存在。

如果你符合"同时跑 ≥2 个 AI coding agent、不愿离开终端、想自己 orchestrator 编排"中的任意一条，建议：

- **先花 30 分钟**用 `install.sh` 装上，跑 `herdr` 体验一下侧栏状态
- **再花 1 小时**读 `SKILL.md` + `socket-api` 文档，判断你的 agent 工作流能不能用 socket 接上
- **最后**判断要不要把 tmux session 迁过来

对 Rust TUI 开发者，**这套代码也是 ratatui + crossterm + tokio + portable-pty + interprocess 五件套组合的完整工程样本**，比单独读 ratatui 文档学到的东西多得多。
