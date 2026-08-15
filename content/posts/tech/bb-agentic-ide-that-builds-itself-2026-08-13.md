---
title: "bb 深度解读：那个能 build 自己的 agentic IDE——它用 Server/Daemon 双进程 + Thread 模型 + experimental_ Plugin SDK，把「agent 编排自己」做成了产品"
date: 2026-08-13T00:32:00+08:00
draft: false
tags: ["AI Agent", "开源项目深拆", "Self-host", "Electron", "Plugin SDK", "Coding Agent", "Architecture"]
categories: ["技术笔记"]
description: "get-bb/bb 是 2025-2026 年的 agentic IDE——能 control / customize / automate 自己，为用户的「software factory」铺路。它跟 Paseo / Orca 同赛道但设计不同：四个 first-class surface（App / CLI / Desktop / HTTP API）+ Server / Host Daemon 双进程物理隔离 + Thread 模型（standard / manager / child delegation）+ experimental_ 前缀的 Plugin SDK。本文拆 bb 的「builds itself」理念、Server/Daemon 双进程 + 双 contract 的工程含义、Thread 模型 + manager 委托链、Plugin SDK 的显式稳定化流程，以及它在 2026 年 agent 编排器赛道的位置。"
slug: "bb-agentic-ide-that-builds-itself"
band: "review"
gates: ["事实性", "去AI味", "观点依据"]
github_repo: "get-bb/bb"
---

## 这篇文章在回答什么

`get-bb/bb` 的 README 第一句话：

> bb is an agentic IDE that builds itself. It can control, customize, and automate itself, laying the groundwork for your own software factory.

把它和前面反写的几个项目放一起看：

- **Claude Code**——单一 Terminal agent
- **oh-my-pi**——pi-mono 的工程级 hyper-fork，把 native / LSP / DAP 全部原生化
- **Orca**——多 agent 编排器（30+ adapter，桌面 IDE + Mobile + CLI）
- **Paseo**——voice-first + privacy-first + mobile-first 的多 agent 编排器
- **bb**——**自指**的 agentic IDE

"自指"是这个词的关键。**bb 的目标不是"控制外部 agent"，是"让 agent 编排自己、为用户的 software factory 铺路"**。

具体差异化落到三个产品决策：

1. **四个一等公民 surface**——App（web UI）/ CLI / Desktop（Electron wrapper）/ HTTP API。任何 surface 都能 drive bb，没有"主 surface"。
2. **Server / Host Daemon 双进程物理隔离**——server 是 stateless 的中心 hub（SQLite + WebSocket），daemon 在每台执行机器上跑，通过双 contract 包（`@bb/server-contract` + `@bb/host-daemon-contract`）通信。
3. **Thread 模型**——unit of work 是 Thread，append-only event stream，standard / manager 两种，manager 可以 own child threads 做 delegation。

这篇文章做三件事：

1. 拆 bb 的「**builds itself**」到底是什么——为什么这不是又一轮"agent IDE"
2. 拆 Server / Daemon 双进程 + Thread 模型 + Plugin SDK 实验性管理的工程含义
3. 把 bb 放到 AI Coding Agent 赛道——它和 Paseo / Orca / oh-my-pi / Claude Code 的位置

## 一、「builds itself」是什么

bb 的自指设计有三个具体含义。

### 1.1 bb 用 bb 写自己

`apps/server` / `apps/app` / `apps/desktop` 这些 surface 全是 bb 自己的代码。bb 自己用 bb 跑 thread / manager / agent 来 develop bb。这是**言行一致**——产品宣称"agentic IDE"，bb 团队就用 agentic IDE 来 develop 自己的 IDE。

### 1.2 bb 让用户用 bb 写自己的 software factory

VISION.md 给的描述：

> bb is a programmable workspace for coding agents. It should be a system that users, teams, and agents can shape around their own tools, infrastructure, and workflows.

「用户的 software factory」——每个用户的开发流水线不一样（CI / 内部工具 / 部署系统 / 测试套件）。bb 提供**可编程的工作空间**，让 agent 自己编排这些流水线。bb 不替你做事，它让你的 agent 替你的团队把流水线编排起来。

### 1.3 bb 的"control / customize / automate"三件套

README 给的三个核心能力：

- **Control**——bb 能 control 自己（agent 用 bb 跑 thread 来管理 bb 的开发）
- **Customize**——Plugin SDK 让用户扩展 bb（自定义 providers / environments / UI surfaces / LLM services）
- **Automate**——bb 能 automate 自己（cron / scheduled threads / manager threads 自动跑任务）

三个能力的统一是：**agent 是 bb 的 first-class operator**。CLI 不是 sidecar，HTTP API 不是 webhook，agent 用 bb 跟用户用 bb **等价**。

VISION.md 把这个写成了第一原则：

> Users and agents are both first-class operators: bb is meant to be used directly by users and programmatically by agents. The web app, CLI, managers, and future surfaces should expose the same core functionality.

## 二、Server / Host Daemon 双进程

`docs/system-overview.md` 给的双进程架构：

```
┌──────────────────┐         ┌──────────────────┐
│      Server       │◀──────▶│   Host Daemon    │
│  (central hub)    │  WS    │  (exec machine)  │
│                  │ RPC    │                  │
│ - SQLite (truth) │        │ - workspaces     │
│ - HTTP API       │        │ - provider run   │
│ - WebSocket push │        │ - session mgmt   │
│ - Stateless      │        │ - workspace exec │
└──────────────────┘        └──────────────────┘
        ▲                            ▲
        │ HTTP + WS                  │ local HTTP
        │                            │
   ┌────┴────┐                  ┌────┴────┐
   │   App   │                  │   CLI   │
   │ (web UI)│                  │  (`bb`) │
   └─────────┘                  └─────────┘
```

### 2.1 Server 的职责

Server 是 **central hub**——所有持久状态在 SQLite 里，server 暴露 HTTP API + WebSocket 推送变更通知。

> Stores all state in a SQLite database, exposes an HTTP API, and pushes change notifications over WebSocket. Stateless itself; the DB is the source of truth.

三个关键点：

1. **Stateless**——server 进程可以重启，状态不丢（DB 是 truth）
2. **Push 模式**——不用客户端轮询，server 主动推变更
3. **DB 单一源**——避免多 server 节点状态同步问题

### 2.2 Host Daemon 的职责

Daemon 在每台执行机器上跑——一台 server 配多台 daemon。

> Connects to the server, handles host RPC requests, provisions workspaces, runs agent provider processes, and posts events back.

Daemon 做四件事：

1. 连 server（enroll 流程）
2. 接 host RPC（server 命令：provision workspace / start thread / stop thread）
3. 跑 agent provider（spawn child process / maintain session / stream output）
4. 回事件（thread progress / provider output / lifecycle）

### 2.3 物理隔离的工程含义

`AGENTS.md` 给了一条铁律：

> The server owns product policy: defaults, instructions, manager behavior, tool lists, and thread behavior.
> The host daemon owns host-local primitives, provider translation, runtime/session management, and workspace execution.
> If the server needs host-local data, the daemon should return raw data and the server should assemble product behavior.

物理隔离的边界：

| 维度 | Server | Daemon |
|---|---|---|
| **默认 / 指令 / 工具列表** | ✅ | ❌ |
| **Manager 行为 / Thread 策略** | ✅ | ❌ |
| **Workspace provisioning** | ❌ | ✅ |
| **Provider session** | ❌ | ✅ |
| **Provider translation** | ❌ | ✅ |

**两个 contract 包强制这条边界**：

- `@bb/server-contract` — HTTP + WebSocket API between clients and server
- `@bb/host-daemon-contract` — protocol between server and host daemons

> Implementation packages never import across these boundaries. The server doesn't know how workspaces are provisioned. The daemon doesn't know about threads or projects beyond what commands tell it.

这是**明确的工程纪律**——server 不该知道 workspace 怎么创建（这是 host-local 操作），daemon 不该知道 thread 是什么（这是 product 概念）。

### 2.4 HOST_DAEMON_PROTOCOL_VERSION 铁律

`AGENTS.md` 有一条非常具体的协议版本铁律：

> Always increment `HOST_DAEMON_PROTOCOL_VERSION` when a change can alter anything sent between the server and host daemon. This includes adding, removing, renaming, or changing the type, requiredness, default, or meaning of fields in session payloads, WebSocket messages, host RPC commands, or host RPC results. A shared TypeScript build passing is not evidence of wire compatibility: enrolled machines can still be running an older daemon. The version mismatch is what triggers their automatic update; without a bump, an old daemon may connect successfully and then enter an `invalid-message` reconnect loop.

这条铁律揭示了一个真实的工程问题：**TypeScript build 通过 ≠ wire compatible**。两个进程（server / daemon）独立发布，已经 enroll 的 daemon 可能还在跑旧版本。如果 server 改了 protocol，TypeScript build 照过（双方都用最新 type），但**老 daemon 不知道协议变了**，连上 server 之后收到 `invalid-message` 进入 reconnect loop。

解决：**强制 bump 版本号 → daemon 自动 update → 老 daemon 退出 → 新 daemon 连上**。

这是**distributed system wire compatibility** 的纪律。OpenAI / Anthropic / Google 都有类似的 protocol version 铁律，但 bb 把这条**写在 AGENTS.md 里强制执行**，不是事后补的。

## 三、Thread 模型：unit of work

`docs/system-overview.md` 给的数据模型：

> **Thread**: the unit of work. Each thread tracks a conversation with an agent provider, has lifecycle state, and produces an append-only stream of **events** (messages, tool calls, file changes, etc.). Threads can be **standard** (does work directly) or **manager** (coordinates other threads). Threads can own child threads for delegation.

Thread 是 bb 的 **work unit**，独立于 session：session 是 provider 侧的概念，Thread 是 bb 自己定义、跨 provider 边界的存在。

### 3.1 Thread 的两个角色

| 角色 | 职责 |
|---|---|
| **Standard thread** | 直接做工作——对话 agent / 调工具 / 改文件 |
| **Manager thread** | 协调其他 thread——可以 own child threads，**做 delegation** |

Manager thread 是 bb 的**核心自指能力**——**agent 用 bb 跑 bb 的开发任务**就是 manager thread 在工作。

### 3.2 Event stream

每个 Thread 产生 **append-only event stream**——消息 / 工具调用 / 文件变更。Append-only 意味着：

- 不可变历史（不能改已发生的事件）
- 可重放（从 event 1 开始重放到任意点）
- 审计友好（每条事件可追溯）

跟传统数据库的"row update"模型不同，event stream 是 **event sourcing** 模式——Thread 的状态由事件流推导，而不是直接存储。

### 3.3 Child delegation

Manager thread 可以 **own child threads**——把子任务 delegate 给 child thread。这是 bb 实现"agent-of-agents"的方式：

```
Manager thread
  ├─ Child thread 1（实现 feature A）
  ├─ Child thread 2（写测试）
  └─ Child thread 3（跑 CI）
```

Manager 监控 child threads 的 progress，决定是否介入 / 继续 / 取消。这是显式的层级管理，和并行调度器的隐式协调是两回事。

### 3.4 Environment

Thread 在 **Environment** 里执行——Environment 绑定 workspace（磁盘目录） + host（执行机器）。

> **Environment**: the execution context for a thread. It binds a workspace (a directory on disk) to a host. An environment can be **unmanaged** (point at an existing directory), or **managed**. Environments managed by bb will be cleaned up when there are no longer any unarchived threads using it.

Environment 分两种：

- **Unmanaged**——指向已有目录，不管理生命周期
- **Managed**——bb 管生命周期，**最后一个 unarchived thread 退场时自动清理**

这个设计允许**用户自定义 workspace**（unmanaged）和 **bb 创建 workspace**（managed）共存。

### 3.5 一次委托任务怎么流过系统

把前面几段串起来。假设你要 bb 修一个跨模块的 bug。请求先从任一 surface 进到 server，server 在 SQLite 里建一条 Thread 记为 manager；manager thread 把工作拆成几段，各开一条 child thread（改代码、写测试、跑 CI）。每条 child thread 落到一台 host daemon，daemon 在对应 workspace 里拉起 agent provider 进程，把输出作为事件推回 server。server 把事件追加进这条 child thread 的 append-only 流，manager 读到子线程的进度，决定推进、介入还是取消。所有事件都落在 server 的 SQLite 里，所以无论从哪个 surface 打开，看到的都是同一份状态；线程中途退出，也能从事件流重放到断点。

这条流程里，server 只负责状态与编排，真正动手的是 daemon 上的 provider 进程——这就是双进程隔离放进一次真实任务后的样子。

## 四、Plugin SDK：显式稳定化流程

`AGENTS.md` 的 Plugin API 铁律：

> Any new public plugin API member (a `@bb/plugin-sdk/app` export, an `app.slots.*` method, or a `BbPluginApi` property) ships with an `experimental_` name prefix and an entry in [docs/api_to_audit.md](docs/api_to_audit.md) describing what it does and what to audit before stabilizing. Dropping the prefix is the deliberate stabilization step: audit the entry, rename project-wide, and remove it from the doc in the same change.

bb 的 Plugin SDK 用 **explicit stabilization workflow**——每个新公开 API：

1. 加 `experimental_` 前缀（如 `experimental_runThread`）
2. 进 `docs/api_to_audit.md` 登记
3. 用户用一段时间，收集反馈
4. **显式审计**（audit the entry）
5. **项目范围 rename**（去掉 `experimental_` 前缀）
6. 从 `api_to_audit.md` 删除该条目

**所有 6 步在一个 PR 里完成**。

这个流程跟大多数项目的"悄悄转正"形成对比——很多项目的 deprecated API 在版本号 bump 时悄悄消失，没有显式审计。bb 把"显式审计"做成代码 review 的一部分。

`@bb/plugin-sdk/app` 的 API 设计（`app.slots.*` / `BbPluginApi`）是 bb 给插件作者的扩展点——UI slots / new surfaces / custom providers / new environments 都可以加。Plugin SDK 的扩展能力是 bb 的"可编程 workspace"哲学的载体。

## 五、四个一等公民 Surface

bb 不像 Claude Code / Codex CLI 那样只有一个主 surface，它有**四个 first-class surface**：

| Surface | 入口 | 用户群 |
|---|---|---|
| **App** (web UI) | `localhost:38886` | 真人 + agent（HTML 通用） |
| **CLI** (`bb`) | `npx bb-app@latest` | 开发者 + agent（脚本化） |
| **Desktop** (Electron wrapper) | 下载桌面 app | macOS Apple Silicon 用户 |
| **HTTP API** | server REST + WebSocket | 第三方集成 + agent |

四个 surface 都走同一个 server backend，**能力等价**——用户在 web UI 能做的事，CLI / Desktop / HTTP API 都能做。

为什么多 surface？

- **CLI**——脚本化友好，agent 用得最多
- **App**——图形界面，实时观察 thread 进度
- **Desktop**——macOS 用户原生体验，bundle daemon 自动启动
- **HTTP API**——第三方集成（CI / monitoring / webhooks）

AGENTS.md 强调：

> Every end-user feature must also be usable by agents through both the SDK and the `bb` CLI; ship and document those surfaces in the same change as the UI.

**每个 UI feature 必须同时通过 SDK + CLI 可用**——这是 bb 让"user 和 agent 都是一等公民"的具体落地。

## 六、Thread 模型 + Event Sourcing 的工程代价

bb 的 Thread 模型不是免费的，它付出几个具体代价。

### 6.1 数据迁移复杂度

Append-only event stream 的代价是**数据迁移**。如果改 Thread 的 schema，**已存在的事件不能改**——只能写 migration event（transform old event → new representation）。

AGENTS.md 的纪律：

> Do not manually edit Drizzle snapshot JSON. Change the schema, then regenerate migrations/snapshots with Drizzle so the snapshot chain stays consistent.

bb 用 **Drizzle migrations** 处理 SQLite schema 变更——SQLite schema 变了，event stream 的格式也要跟着 migration 走。这是个**工程税**，但换来 audit-friendly 的特性。

### 6.2 跨 machine Thread 状态

Thread 在 manager / child 之间跨越多个 daemon（host machines）。Server 在中间同步——所有 event 都过 server 的 SQLite。

**跨 machine 的 event 顺序**需要一个全局编号来保证可重放。bb 的文档没有说明这个机制由谁维护、怎么实现，这里先标注 unresolved——想深挖的读者可以去 `apps/server/src/services/` 目录看 runtime 实现。

### 6.3 Archive vs Delete

Thread 有 **archive** 和 **delete** 两种结束方式：

- **Archive**——event stream 保留，UI 显示在 archive 里，可恢复
- **Delete**——event stream 删掉，不可恢复

bb 的设计是 **archive-first**——默认 archive，让用户显式 delete。这种"保守默认"是为了**保护用户的工作历史**，但增加了**存储成本**（archive 的 Thread 永久存在）。

FAQ 没出现 archive 限制（README 提了"no archive cleanup yet"），意味着 archive 会无限累积。这是**长期用户运营成本**。

## 七、bb 在 AI Coding Agent 赛道的位置

把 bb 和前面反写的几个项目放一起：

| 维度 | Claude Code | oh-my-pi | Orca | Paseo | bb |
|---|---|---|---|---|---|
| **形态** | Terminal | Terminal (Rust) | Desktop + Mobile | Mobile + CLI + Web | 4 surfaces |
| **目标** | 单一 agent | 工程化 hyper-fork | 多 agent 编排 | 多 agent 编排 + voice | **agent 编排自己** |
| **Agents** | 1（Anthropic） | 1（pi-mono） | 30+ | 5 | **不限，plugin 自定义** |
| **后端** | 单进程 | 单进程 | 单进程 | daemon | **server + host daemon** |
| **Work unit** | session | conversation | worktree | session | **Thread** |
| **工作模式** | turn-based | turn-based | parallel worktrees | parallel | **manager delegation** |
| **License** | 闭源 | MIT | MIT | AGPL-3.0 | **未明（README 无声明）** |
| **开源** | ❌ | ✅ | ✅ | ✅ | ✅ |

bb 的差异化：

1. **四个一等公民 surface**——vs Claude Code 单一 Terminal
2. **Server / Daemon 双进程**——vs 所有其他项目的单进程
3. **Thread 模型 + manager delegation**——vs Orca 的 parallel worktrees / Paseo 的 multi-stream
4. **Plugin SDK 的显式稳定化流程**——vs 多数项目的"悄悄转正"
5. **builds itself 自指**——vs 所有其他项目"用项目 + 编排别人 agent"

**哲学差异**：

- Claude Code / Codex / Cursor——"做一个最好的 agent"
- oh-my-pi——"把工程基础设施做到极致"
- Orca——"编排多个外部 agent"
- Paseo——"让 agent 在手机/语音里跑"
- **bb——"让用户用 agent 建自己的 software factory"**

bb 不争"谁是最好的 agent"——它给用户一个**可编程的工作空间**，让用户的 agent 替用户的团队干活。

## 八、落地路径

按代价从小到大排：

**1. 在线 demo。** 下载 mac桌面 app [releases/tag/desktop-latest](https://github.com/get-bb/bb/releases/tag/desktop-latest)。macOS Apple Silicon only。

**2. npx 一键。** `npx bb-app@latest`，浏览器打开 `http://localhost:38886`。Intel Mac / Linux / WSL2 用户用这条路。

**3. 接 provider CLI。** bb 用你已经认证的 provider CLI（Claude Code / Codex / Copilot / OpenCode / Pi），不需要额外的 API key。

**4. Telemetry opt-out。** `BB_TELEMETRY=false` 一次跑；permanent install 用 `BB_TELEMETRY=false npm install -g bb-app`。

**5. 多 device 协作。** `docs/multiple-devices.md`——server 在一台机器，host daemon enroll 到多台机器（局域网 / Tailscale / VPN），所有 daemon 共享同一个 server DB。

**6. 自定义 Plugin。** `@bb/plugin-sdk` 写 custom provider / environment / UI surface。`AGENTS.md` 给了完整的 `experimental_` 前缀 → audit → stabilize 流程。

**7. 跑 bb 自己。** `pnpm dev` + `pnpm dev:desktop`——用 bb 跑 bb 的开发任务，体验 manager thread 协调 child thread。

适用边界：这条路径适合已经在用 Claude Code / Codex 等 provider CLI、想把这几个 agent 统一进一个可编排、可回放的 workspace 的团队。单人单机、也不需要跨机器协作时，继续用单一 provider CLI 就够了——bb 的四个 surface 和双进程配置是为"agent 编排 agent"和多机器协作准备的，先用不上。

## 九、一章小结

bb 不是又一个 agent IDE。它是**自指的、可编程的、四个 surface 等价的 agentic workspace**——让你用 agent 建自己的 software factory。

四件事连起来：

1. **自指**——bb 用 bb 写 bb，agent 用 bb 跑 bb 的开发任务，user 用 bb 控制 bb 的生命周期
2. **Server / Daemon 双进程**——server 持有 SQLite 状态，daemon 在每台机器跑 agent provider；双 contract 包强制边界 + `HOST_DAEMON_PROTOCOL_VERSION` 铁律防 wire drift
3. **Thread 模型**——standard / manager 两种，manager 协调 child threads 做 delegation；append-only event stream 给 audit / replay / migration
4. **Plugin SDK**——`experimental_` 前缀 + `api_to_audit.md` 显式审计流程，plugin 稳定化是刻意为之的工程动作，不是版本号 bump 的副产品

一句话版本：**Orca 让 agent 编排别人，Paseo 让 agent 在 mobile/voice 里跑，bb 让 agent 编排自己**——前两个是"做产品"，第三个是"做平台"。

## 为什么不去

> **为什么 bb 用 Server / Daemon 双进程而不是单进程？** 因为 bb 想定位为"user 的 software factory"——多机器协作是必需能力。一台 server + 多台 daemon 是**分布式系统的标准形态**：server 持有状态（SQLite），daemon 持有执行（workspace + provider session）。单进程版本简单，但**没法跨机器**。双进程的代价是 wire protocol 必须严格管理——`HOST_DAEMON_PROTOCOL_VERSION` 铁律 + 双 contract 包就是为了这个代价。选分布式架构是 product 定位的工程后果，不是技术偏好。
>
> **为什么 bb 用 Thread 模型而不是 session 模型？** 因为 bb 的核心能力是 **manager delegation**——一个 agent 协调多个 agent 干活。session 概念是 provider 的（provider 管自己的 session），但**跨 provider 协调**需要 bb 自己的概念。Thread 就是这个概念——**bb 拥有的、跨 provider 边界的、可 manager 的 work unit**。session 是 Thread 的实现细节，Thread 是 product 概念。
>
> **为什么 bb 的 Plugin SDK 用 `experimental_` 前缀？** 因为 bb 强调"plugin 是 first-class extension"——但 plugin 又是**最容易做错的事**。一旦 plugin 用了某个 API，那个 API 改了，所有 plugin 都崩。`experimental_` 前缀 + audit doc 把"plugin 用的 API 可能变"显式化——plugin 作者看到 `experimental_` 知道"这 API 还可能变"。**稳定化是 deliberate 流程（audit + rename + remove from doc）**，不是悄悄转正。bb 把"plugin API 兼容"做成**代码 review 的一部分**，不是 release notes 的一句话。