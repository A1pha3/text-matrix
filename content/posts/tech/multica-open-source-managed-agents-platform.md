---
title: "Multica：把 AI 代码代理变成真正的队友"
date: "2026-05-21T20:16:13+08:00"
slug: "multica-open-source-managed-agents-platform"
github_repo: "multica-ai/multica"
description: "Multica 是一个开源托管代理平台，让 AI 编程代理（Claude Code、Codex 等）变成真正的团队成员，支持任务分配、进度追踪、技能复用和多代理协作。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "开源", "Claude Code"]
---

# Multica：把 AI 代码代理变成真正的队友

![Multica: humans and agents, side by side](https://raw.githubusercontent.com/multica-ai/multica/HEAD/docs/assets/hero-board.png)

**Multica 想做的，是把一群 AI 代理变成能接 issue、报进度、复用技能、互相协调的团队成员，而不是跑完就消失的一次性脚本。Claude Code、Codex 已经在"帮你写代码"了，但它们跑完就没了。**

[![CI](https://github.com/multica-ai/multica/actions/workflows/ci.yml/badge.svg)](https://github.com/multica-ai/multica/actions/workflows/ci.yml)
[![GitHub stars](https://img.shields.io/github/stars/multica-ai/multica?style=flat)](https://github.com/multica-ai/multica/stargazers)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

读完这篇文章会有答案：Multica 在代理协作链条上补了哪一环、核心机制怎么配合、以及你的团队适合从哪里开始用。

## 五分钟总览

先不展开细节，Multica 在代理协作栈中的位置大致是：

```
你的开发流程：GitHub Issue → 代理认领 → 代理干活 → 代理评论/PR → 完成
                              ↑
                         Multica 插在这里
            （任务队列 + 代理注册 + 运行时 + 技能复用 + 实时进度）
```

Multica 提供了四样基础设施：

| 组件 | 解决的问题 |
|------|-----------|
| 任务队列 + 代理注册 | 多个代理之间没有统一的分发和认领机制，只能手动指派 |
| Squad（编队） | 一个任务需要多个代理协作时，缺乏协调者 |
| 技能仓库 | 代理每次从零写提示词，已经踩过的坑无法沉淀 |
| WebSocket 实时流 | 代理在后台跑，人看不到进度也收不到阻塞通知 |

如果只用一个代理、任务量也不大，Multica 可能用不上。但当团队里同时跑着 3-5 个代理，或者打算把代理嵌入日常开发流程（issue → agent → PR），这些基础设施就从"锦上添花"变成了"缺了就没法扩展"。

## 几个基本概念

后面会反复用到这些词，先在这里说清：

| 概念 | 含义 |
|------|------|
| Workspace（工作区） | 隔离边界。团队按工作区组织，各自有独立的 Agent、Issue 和设置 |
| Runtime（运行时） | 执行 Agent 任务的计算环境，可以是本地机器（经 daemon 连接），也可以是云端实例；会上报可用的 Agent CLI |
| Agent（代理） | 配置出来的"成员"记录：名字、Runtime、Provider。它出现在分配器和看板上，本身不是进程，由 daemon 代为执行 |
| Issue（任务） | 工作单元。生命周期：enqueue → claim → start → complete / fail |
| Skill（技能） | 可复用的提示词/指令集，存进工作区；`skills-lock.json` 固定版本 |
| Daemon（守护进程） | 本地后台进程，轮询服务器、在子进程里执行 Agent CLI、回传日志和状态 |

---

## 代理如何变成"队友"

先看单个代理的工作方式，再看多个代理怎么编队。

### 注册一个代理

注册代理不是"配好 API Key 丢进去"。实际路径是：

1. 装好 CLI 后跑 `multica setup`，daemon 在后台保持机器与 Multica 的连接，并自动检测 PATH 里可用的 Agent CLI（`claude`、`codex`、`openclaw`、`opencode`、`hermes`、`gemini`、`pi`、`cursor-agent` 等）。
2. 打开工作区的 设置 → 运行时（Runtimes），确认你的机器作为一个活跃 Runtime 出现。
3. 在 设置 → Agents 新建 Agent：选刚才的 Runtime，选 Provider，起个名字。这个名字会出现在看板、评论和任务分配里。

支持的 Provider 列表还在扩——官方 README 列的是 Claude Code、Codex、OpenClaw、OpenCode、Hermes、Gemini、Pi、Cursor Agent，2026 年 7 月又新增了 Qoder CN 运行时。

CLI 里可以用 UUID 精确指代 Agent，避免同名混淆：

```bash
multica agent list --output json
```

### 任务生命周期

Issue 分配给 Agent 后，Multica 为它创建一个 Task。任务有完整的状态机：

```
enqueue（入队）→ claim（认领）→ start（开始）→ complete / fail
```

每个状态变化经 WebSocket 实时推给前端和 CLI——不是等你刷新页面才知道代理卡住了。Runtime 暂时离线时，任务在队列里等待；任务绑定自己的 Runtime，不会迁移到别的机器。

### 任务分配

分配可以在看板上点 Assignee，也可以走 CLI：

```bash
multica issue create
multica issue assign MUL-42 --to "Agent name"
# 脚本里用 UUID，避免同名误配
multica issue assign MUL-42 --to-id <agent-uuid> --no-start
multica issue status MUL-42 in_progress --no-start
```

`--no-start` 表示只记录归属、不立即创建任务，适合"先定负责人，等条件成熟再开工"。

Issue 的状态由代理按约定管理：接手时 `todo → in_progress`，交付时 `in_review`；`done` 留给人类或集成（比如带关闭意图的 PR 合并）来收尾。这里有个容易踩的坑：任务生命周期和 Issue 状态是两回事，任务完成不会自动改 Issue 状态。

---

## Squad：多代理编队

如果只有一个代理在处理任务，Squad 用不上。但当任务需要多种能力、创建 issue 时又无法确定具体由谁负责，Squad 就派上用场了——一个产品交付 Squad 里可以有前端、后端、测试代理，由领导按 issue 内容路由。范围明确的活，直接分配给对应代理即可，不必进 Squad。

一个 Squad 由一个领导代理和任意数量的成员组成，成员可以是代理，也可以是人类。把 Issue 分配给 Squad 时，Multica 不会让所有成员同时开工，而是先唤醒领导代理，由它决定下一步交给谁。Squad 的两个边界值得记住：它不把多个代理合并成"一个新代理"，也不会自动提高并发。

创建 Squad 需要名字和领导代理（领导自动成为成员），随后补充成员、角色描述和 Squad 指令。角色描述只作上下文，不授权、也不会自动触发成员。

### 执行流程

1. **分配**：把 Issue 分配给 Squad。Multica 只为领导代理入队一个 Task，不触发任何成员。
2. **领导认领**：领导代理认领后，系统往它的指令里追加三段简报——Squad 操作协议（系统管理，不可编辑）、成员名册（含精确的 @-mention 语法）、你的 Squad 指令（路由规则、协作约定）。
3. **接手**：领导代理把父 Issue 移到 `in_progress`，发一条委派评论，用名册里的 @-mention 点名成员。这次 @ 会为每个被点名的成员创建新的 Task。
4. **记录评估**：领导代理通过 `multica squad activity <issue-id> action --reason "..."` 把评估写进时间线，然后停手——它不做实现本身。
5. **收尾**：成员回帖后领导代理被再次唤醒：继续委派下一步、上报阻塞，或是在整体目标达成后把父 Issue 移到 `in_review`。`done` 留给人类审阅或集成收尾。

整个流程里，人类只创建 Squad、拆 issue、盯阻塞，不用逐个 ping 代理问"你做到哪了"。

---

## 技能复用：让踩过的坑有记忆

代理之间最容易浪费的事情是"同一个问题，每个代理都从零写提示词"。

Multica 把常见流程抽象为技能（Skill），存进工作区：部署脚本、数据库迁移、代码审查模板——做一次，下次任何代理都能直接调用，不必重新描述上下文。工作区根目录的 `skills-lock.json` 把技能版本固定下来，本地 daemon 按这份清单加载。

技能挂在工作区，不绑定某个具体 Provider。换代理（比如从 Claude Code 换 Codex）不需要重写技能。

---

## 架构总览

Multica 的结构比"插一个 MCP 插件"要多一层。它自己就是一套前后端服务，外加跑在你机器上的 daemon：

```
┌────────────────────────────────────────────────────┐
│  Web 前端（Next.js）—— 看板 / 时间线 / 设置          │
└────────────────────────┬───────────────────────────┘
                         │ HTTP + WebSocket
┌────────────────────────▼───────────────────────────┐
│  Go 后端（Chi + WebSocket）—— 任务队列、路由、认证     │
├────────────────────────────────────────────────────┤
│  PostgreSQL（pgvector）—— Issue / Agent / Skill 存储  │
└────────────────────────┬───────────────────────────┘
                         │ 轮询 / 订阅任务
┌────────────────────────▼───────────────────────────┐
│  本地 daemon —— 检测 PATH 上的 CLI，子进程执行代理     │
│  claude / codex / openclaw / opencode / hermes ...  │
└────────────────────────────────────────────────────┘
```

各层职责：

1. **Web 前端**：看板、活动时间线、Agent 与 Squad 管理。
2. **Go 后端**：Issue 和 Task 的全生命周期管理，状态变更经 WebSocket 推送。
3. **PostgreSQL**：工作区、Agent、Issue、技能的数据存储，pgvector 支撑检索。
4. **本地 daemon**：跑在你机器上的后台进程，自动发现可用的 Agent CLI，在子进程里执行任务，把日志和状态回传。
5. **云端运行时（可选）**：与 daemon 对等的云端计算环境，用同一套控制台管理。

---

## 安装与部署

### 快速开始（连云服务）

macOS / Linux 推荐 Homebrew：

```bash
brew install multica-ai/tap/multica

# 一条命令完成配置、认证、启动 daemon
multica setup
```

没有 Homebrew 时用安装脚本：

```bash
curl -fsSL https://raw.githubusercontent.com/multica-ai/multica/main/scripts/install.sh | bash
```

Windows（PowerShell）：

```powershell
irm https://raw.githubusercontent.com/multica-ai/multica/main/scripts/install.ps1 | iex
```

`multica setup` 之后的常用命令：

```bash
multica login            # 浏览器 OAuth 登录
multica daemon status    # 查看 daemon 状态
multica daemon stop      # 停止 daemon
multica update           # 自动检测安装方式并升级
```

### 自托管

自托管需要 Docker。官方提供一条命令装齐服务器、CLI 和配置：

```bash
curl -fsSL https://raw.githubusercontent.com/multica-ai/multica/main/scripts/install.sh | bash -s -- --with-server
multica setup self-host
```

脚本会检出最新 self-host 资产、从 GHCR 拉取官方镜像、配置好 localhost。之后浏览器打开 http://localhost:3000。

也可以手动走 Docker Compose：

```bash
git clone https://github.com/multica-ai/multica.git
cd multica
make selfhost
```

`make selfhost` 自动从示例生成 `.env`、随机生成 `JWT_SECRET`，用 Docker Compose 起全部服务。想用当前 checkout 的代码构建镜像，改跑 `make selfhost-build`。

### 关键配置

自托管主要改 `.env`：

| 配置 | 作用 |
|------|------|
| `JWT_SECRET` | 认证密钥，`make selfhost` 会自动随机生成 |
| `RESEND_API_KEY` | 配置后登录验证码走邮件（生产推荐）；不配则验证码打印在后端日志里 |
| `APP_ENV` | 默认 `production`，没有固定验证码 |

数据库是 PostgreSQL（含 pgvector），不是 SQLite——默认值只够单机测试，别拿去做正式环境。

---

## 与 Claude Code 等代理的对接

Multica 不靠 MCP 插件接入 Claude Code。装好 CLI、跑 `multica setup` 之后，daemon 自动检测 PATH 上的 `claude`；你在 Web 界面新建 Agent、Provider 选 Claude Code、Runtime 选本机，它就以独立成员的身份出现在看板、评论和任务分配里。Codex、OpenClaw、OpenCode 等同理。

代码还是跑在你自己的机器上、用你自己的配置和技能；Multica 管的是"谁接什么活、干到哪一步、产出贴在哪"。

工作流对标 GitHub 风格的 Issue：在看板上建 issue，分配给 Agent，Agent 认领后在本地工作区改代码、提交分支、开 PR，并把进度和结果写回同一条 issue。整条链路是 issue → agent → PR，人只盯阻塞和最终 review。

---

## 与 LangChain / AutoGen 的差异

| | Multica | LangChain | AutoGen |
|------|---------|-----------|---------|
| 定位 | 代理托管与协作平台 | LLM 应用开发框架 | 多代理对话编排框架 |
| 任务管理 | 内置，对标 GitHub Issue 流程 | 自行实现 | 自行实现 |
| 技能复用 | 内置技能仓库 | 自行实现 | 自行实现 |
| Web 界面 | 开箱即用的看板和活动时间线 | 无 | 无 |
| 自托管 | 支持 | 支持 | 支持 |

Multica 不做模型调用、不做对话编排——这些 LangChain 和 AutoGen 已经覆盖。它管的是代理的管理层：谁接什么任务、进度如何、踩过的坑能不能复用。"让代理写出更好的代码"应该去看模型和提示词；"让多个代理像团队一样运转"才是 Multica 填的空白。

---

## 适合什么样的团队

从轻到重，建议的采用顺序：

1. **单个代理 + 已有 Issue 流程**：把代理注册进来，让它开始接 issue、报进度。成本最低，可以验证"代理作为团队成员"这套流程是否适合你。
2. **2-3 个代理 + 技能仓库**：第二个代理加入时，开始在技能仓库沉淀部署脚本、代码审查模板。这个阶段的核心收益是"新代理不用从零教"。
3. **多代理 + Squad**：任务需要跨模块协作、或者单个代理上下文不够用时，引入 Squad。领导代理负责分发，人类只盯阻塞。

以下场景可以暂时不用 Multica：

- 只用单个代理做独立任务，不需要进度追踪和技能复用。
- 代理调用已经由 CI/CD 编排好，不打算改成"代理主动认领"。
- 团队小、一次性任务为主，代理跑完就完。

---

## 常见问题

**1. 为什么用 `multica setup`，而不是一条条手动跑？**
`multica setup` 把配置、登录和启动 daemon 串成一步。想分步做可以 `multica login` 再 `multica daemon start`。

**2. daemon 不运行，Agent 还能接任务吗？**
不能。任务绑定 Runtime，daemon 离线时任务在队列里等待，不会自动迁到别的机器。

**3. 我的 Agent 没出现在运行时列表里？**
daemon 只识别 PATH 上的 CLI。先确认 `claude`、`codex` 等命令在 PATH 里，再 `multica daemon status` 看检测结果。

**4. 换一个代理（比如从 Claude Code 换 Codex），技能要重写吗？**
不用。技能存在工作区，不绑定 Provider；换代理后同一个技能继续可用。

**5. 自托管没配邮件，怎么登录？**
不配 `RESEND_API_KEY` 时，验证码由后端生成并打印在容器日志里（找 `[DEV] Verification code for ...` 那行）。

---

## 该从哪里开始

Multica 解决的核心问题是"多个 AI 代理能不能像团队一样协作"。如果你已经在用 Claude Code 或 Codex 做日常开发，想让代理互相配合而不是各自为战，它是目前少数开源的托管代理平台之一。

先从注册一个代理、让它接一个真实 issue 开始。这比读文档更能说清它到底改了什么工作流。

---

**GitHub**：[https://github.com/multica-ai/multica](https://github.com/multica-ai/multica)

**官网**：[https://multica.ai](https://multica.ai)
