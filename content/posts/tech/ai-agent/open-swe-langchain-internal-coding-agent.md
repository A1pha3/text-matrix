---
title: "open-swe：LangChain 开源的 10.7k Stars 企业编程 Agent 框架"
date: "2026-03-28T20:50:00+08:00"
lastmod: "2026-09-23T10:00:00+08:00"
slug: "open-swe-langchain-internal-coding-agent"
github_repo: "langchain-ai/open-swe"
source_key: "gh:langchain-ai/open-swe"
aliases:
  - /posts/tech/open-swe-langchain-internal-coding-agent/
description: "深度解读 LangChain 开源的 open-swe：10.7k Stars 的开源软件工厂，基于 Deep Agents 构建，支持 Slack/Linear/GitHub/Dashboard 触发，覆盖编码、PR 审查与 CI 监控。"
draft: false
categories: ["技术笔记"]
tags: ["open-swe", "LangChain", "编程Agent", "企业内部AI", "Deep Agents"]
---

# open-swe：LangChain 开源的企业编程 Agent 框架

open-swe 解决的不是"让 AI 写代码"的问题——那是基础模型已经做到的事。它解决的是"把 AI 写代码变成工程团队可控、可审计、可嵌入现有工作流的系统能力"。本文从架构决策、模块边界和任务流转三个角度拆解这套框架。文中机制描述以 2026 年 9 月的 main 分支为口径。

---

## 一、项目概览

### 1.1 这个项目在做什么

[open-swe](https://github.com/langchain-ai/open-swe) 是 LangChain 开源的编程 Agent 系统，官方现在的定位是"构建在 Deep Agents 之上的开源软件工厂"（an open-source software factory）。它本质上是一套"编排层 + 沙箱 + 工具集 + 上下文注入"的组合方案，让你在 Slack、Linear、GitHub、Web Dashboard 上直接下发编码任务，也可以用定时自动化按计划执行。

项目最初的口号是"构建企业自己的内部编程 Agent 的开源框架"，发布半年多来，能力边界已经从"替你写代码、开 PR"扩展到 PR 审查、CI 监控、桌面客户端等完整的工程工作流——这也是"软件工厂"这个新定位的由来。

| 指标 | 数值（2026-09-23 核实） |
|------|------|
| GitHub Stars | 10.7k |
| Forks | 1.3k |
| Contributors | 55 |
| Commits | 2000+ |
| License | MIT |
| 语言 | Python 66% / TypeScript 29% |

### 1.2 背景

Stripe、Ramp、Coinbase 的工程团队都在内部搭建自己的编程 Agent——Stripe 叫 Minions，Ramp 叫 Inspect，Coinbase 叫 Cloudbot。形态是 Slackbot、CLI 或 Web 应用，让工程师在日常工具链里直接调用 AI 完成编码任务。open-swe 把这些内部模式做成了开源版本：基于 LangGraph 和 Deep Agents，提供云端沙箱、多平台调用、子 Agent 编排、自动 PR 创建，可按需适配仓库和工作流。

如今的 open-swe 不止写代码。官方 README 把能力归为四类：**Build**（调查仓库、规划、改代码、跑验证、开 PR）、**Review**（按需或自动执行只读 PR 审查，并从历史反馈中学习仓库的审查风格）、**Operate**（多平台接任务、定时自动化、用 `/baby-sit` 监控 PR 与 CI）、**Customize**（模型、沙箱、工具、技能、触发器均可替换）。

### 1.3 关键设计决策

| 决策 | 说明 |
|------|------|
| **多平台触发** | Slack、Linear、GitHub、Dashboard 均可发起任务，另支持定时自动化 |
| **云端沙箱隔离** | 每线程一个持久沙箱，互不干扰 |
| **精选工具，不做工具海** | 区别于堆砌数百个工具的做法，聚焦工程高频操作 |
| **AGENTS.md 上下文注入** | 仓库级规范启动时直接注入系统提示词 |
| **子 Agent 编排** | 主 Agent 可派生子 Agent 处理独立子任务 |
| **完成后自动开 PR** | 提交变更后自动创建 PR，云端运行有兜底中间件保证 |
| **只读审查与聊天** | PR 审查者和 PR 问答 Agent 只读不写，天然安全边界 |

---

## 二、技术架构

### 2.1 整体架构

open-swe 的架构决策与几家公司内部方案一致：不自己写 Agent 循环，而是组合现有框架，在上面做编排和定制。Deep Agents 提供 Agent 基座，LangGraph 提供运行时。

```text
┌─────────────────────────────────────────────────────────────┐
│                    open-swe 架构                              │
├─────────────────────────────────────────────────────────────┤
│  1. Agent Harness（基于 Deep Agents）                         │
│     create_deep_agent(model, tools, skills, middleware)      │
├─────────────────────────────────────────────────────────────┤
│  2. Sandbox（隔离云端环境）                                   │
│     LangSmith（默认）/ Modal / Daytona / Runloop / E2B / 本地 │
│     每线程持久沙箱，并行执行，全权限隔离                       │
├─────────────────────────────────────────────────────────────┤
│  3. Tools（精选工具 + Deep Agents 内置 + 技能 + MCP）         │
│     open_pull_request | http_request | web_search | ...      │
├─────────────────────────────────────────────────────────────┤
│  4. Context Engineering（上下文工程）                          │
│     AGENTS.md + Linear issue / Slack thread / PR diff        │
├─────────────────────────────────────────────────────────────┤
│  5. Orchestration（编排层）                                  │
│     子 Agent + 20 余个中间件                                  │
├─────────────────────────────────────────────────────────────┤
│  6. Invocation（触发入口）                                    │
│     Slack / Linear / GitHub / Dashboard / Schedule / Desktop │
├─────────────────────────────────────────────────────────────┤
│  7. Validation（验证层）                                     │
│     Prompt 驱动 + PR 创建兜底 + 只读审查者                    │
└─────────────────────────────────────────────────────────────┘
```

七层职责简要区分：

- **Agent Harness**（第 1 层）：决定 Agent 如何循环、如何调用模型和工具。open-swe 自己不实现这一层，而是用 Deep Agents 的 `create_deep_agent`。
- **Sandbox**（第 2 层）：决定代码在哪执行。每线程一个云端 Linux 环境，有完整 Shell 权限但彼此隔离。
- **Tools**（第 3 层）：决定 Agent 能做什么操作——执行命令、发 HTTP 请求、开 PR、回复 Slack 等。
- **Context Engineering**（第 4 层）：决定 Agent 启动时知道什么——仓库规范（AGENTS.md）和任务上下文（Issue、线程历史、PR diff）。
- **Orchestration**（第 5 层）：决定子任务如何拆分、中间件如何介入。
- **Invocation**（第 6 层）：决定用户从哪里触发任务。
- **Validation**（第 7 层）：决定任务完成后如何检查结果。

运行时层面，LangGraph 提供持久执行与线程状态，每次调用对应线程里的一个 run。open-swe 目前提供五个 graph 入口：**Agent**（规划、实现、验证、交付）、**Reviewer**（只读 PR 审查）、**Analyzer**（学习仓库审查风格）、**Chat**（不改代码回答 PR 相关问题）、**Scheduler**（调度定时任务与 CI 监控）。

### 2.2 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 核心框架 | LangGraph | 持久执行与状态机编排 |
| Agent 框架 | Deep Agents | Agent 构建基座（规划、文件操作、Shell、子 Agent 原语） |
| 沙箱 | LangSmith / Modal / Daytona / Runloop / E2B / 本地 | 云端隔离执行环境，可插拔 |
| 后端 | Python + FastAPI | `agent/` 目录，API 与 webhook |
| Dashboard | React + Vite | `ui/` 目录，pnpm 管理 |
| 桌面端 | Electron | `desktop/` 目录，实验性，打包针对 macOS |
| 触发平台 | Slack / Linear / GitHub / Dashboard / Schedule | 多入口集成 |

### 2.3 核心目录结构

```text
open-swe/
├── agent/              # Python 后端：graph、工具、中间件、沙箱、webhook
│   ├── graphs/         # 五个 graph 入口（agent/reviewer/analyzer/chat/scheduler）
│   ├── tools/          # 30 余个条件化工具
│   ├── middleware/     # 中间件实现
│   ├── sandboxes/      # 沙箱提供商抽象与实现
│   ├── bundled_skills/ # 内置技能（如 linear-tickets）
│   └── server.py       # Agent 装配核心（create_deep_agent 调用处）
├── ui/                 # Web Dashboard（React + Vite）
├── desktop/            # Electron 桌面客户端
├── docs/               # INSTALLATION / CUSTOMIZATION / DEVELOPMENT 等文档
├── evals/              # 评测
├── examples/           # 示例
├── tests/              # 测试套件
├── swagger.json        # FastAPI 后端的 OpenAPI 3.1 契约
├── langgraph.json      # LangGraph 部署配置
└── Makefile            # 构建/运行脚本
```

仓库在 2026 年 7 月经历了一次按领域重组：原先放在根目录的 INSTALLATION.md、CUSTOMIZATION.md 移入 `docs/`，同时从纯 Python 后端演化为后端 + Dashboard + 桌面端的 pnpm monorepo。

---

## 三、七大架构模块详解

### 3.1 Agent Harness——基于 Deep Agents

open-swe 采用组合而非从零构建或 Fork。它基于 Deep Agents 框架，在 `agent/server.py` 里调用 `create_deep_agent` 装配 Agent 循环。当前形态大致是：

```python
graph = create_deep_agent(
    model=main_model,
    system_prompt="",          # 系统提示词由 PrepareAgentRunMiddleware 注入
    tools=static_tools,        # 30 余个按运行条件装配的工具
    subagents=[_general_purpose_subagent(...)],
    skills=skill_sources,      # 组织技能 / 内置技能 / 用户技能三层路由
    backend=agent_backend,     # CompositeBackend：沙箱 + 技能只读分区
    middleware=[...],          # 20 余个中间件，见 3.5 节
)
```

这样做的好处：可以拉取 Deep Agents 的上游改进（更好的上下文管理、更省 token 的规划），同时在工具、中间件和编排上做完全定制。

模型默认值：部署同时配置了 Anthropic 与 OpenAI 的 key 时默认 `openai:gpt-5.6-sol`，只配 Anthropic 时默认 `anthropic:claude-opus-5-5`，推理力度默认 medium。Dashboard 还支持按 fast / balanced / performance 三档路由到不同模型。

### 3.2 Sandbox——隔离云端环境

每个线程在独立的云端 Linux 沙箱中运行，拥有完整 Shell 访问权限。设计原则是：先隔离，再在隔离边界内给足权限。

| 特性 | 说明 |
|------|------|
| 持久化沙箱 | 每线程独立沙箱，跨后续消息复用 |
| 安全失败 | 沙箱不可达时不静默替换，宁可报错也不丢弃未提交的工作 |
| 并行执行 | 多线程并行，各自独立沙箱 |
| 凭据收敛 | 沙箱 GitHub 凭据限定在 workspace 分配的仓库范围内 |

支持的沙箱提供商：

| 提供商 | 说明 |
|--------|------|
| LangSmith | 默认提供商，同时是默认 tracing 平台 |
| Modal | 云端函数/容器平台 |
| Daytona | 开发者环境平台 |
| Runloop | AI 编程环境 |
| E2B | 2026 年 7 月新增的支持 |
| 本地执行 | 桌面端直接对白名单内的本地项目运行 |

注意一个设计变化：官方博客早期的说法是"沙箱不可达时自动重建"，当前代码和 README 的口径是**不静默替换**——自动重建会丢弃沙箱里未提交的工作，所以现在选择安全失败，由用户决定重建（`recreate_sandbox` 工具也可由 Agent 主动调用）。

### 3.3 Tools——精选而非堆砌

官方博客发布时的口径是"约 15 个精选工具"。随着能力扩展，现在主 Agent 的静态工具按运行条件装配后约有 30 个，外加 Deep Agents 内置的文件系统、Shell、子 Agent 工具，以及工作区 MCP 工具和用户个人集成。设计原则没变：工具的数量远不如工具的选取重要。

| 工具（示例） | 用途 |
|------|------|
| `open_pull_request` | 开启或更新 GitHub PR（由 PullRequestCreationGuard 兜底） |
| `http_request` | API 调用（GET、POST 等） |
| `fetch_url` | 获取网页并转为 Markdown |
| `web_search` | 网页搜索 |
| `background_execute` / `background_task` | 沙箱内后台执行命令/任务 |
| `save_plan` | 保存执行计划 |
| `request_pr_review` | 请求 PR 审查 |
| `manage_baby_sit` | 管理 CI 监控任务 |
| `slack_reply` 等 Slack 一族 | 在 Slack 中收发消息、加回应、管理线程 |
| `recreate_sandbox` | 重建不可达的沙箱 |

Deep Agents 框架内置 `read_file`、`write_file`、`edit_file`、`ls`、`glob`、`grep`、`write_todos`（待办列表）和 `task`（子 Agent 生成）。此外还有三层技能体系：组织技能（管理员配置）、内置技能（如 linear-tickets）、用户个人技能，以及工作区级 MCP 服务器配置的工具。

### 3.4 Context Engineering——上下文工程

Agent 启动时从两个来源获取上下文：

**AGENTS.md：** 如果仓库根目录存在 `AGENTS.md` 文件，从沙箱读取并追加到系统提示词。这是仓库级别的规则文件，涵盖编码规范、测试要求和架构决策。文件缺失或为空时静默跳过，不报错。

**Source Context：** 完整的 Linear Issue（标题、描述、评论）、Slack 线程历史或 PR diff。Agent 启动时就已经知道任务全貌，而不是通过工具调用逐步摸索。

### 3.5 Orchestration——子 Agent + 中间件

**子 Agent：** Deep Agents 框架原生支持通过 `task` 工具生成子 Agent。主 Agent 把独立子任务分派给隔离子 Agent，每个子 Agent 有自己的工具子集与对话卸载中间件；`task` 工具本身带自动重试（最多 2 次）。

**中间件：** 主 Agent 的中间件栈现在有 20 余个，按职责挑几个关键的：

| 中间件 | 说明 |
|--------|------|
| `PrepareAgentRunMiddleware` | 运行准备：注入系统提示词、仓库指令、任务上下文 |
| `check_message_queue_before_model` | 在模型调用前注入后续消息（Linear 评论或 Slack 消息） |
| `PullRequestCreationGuardMiddleware` | Agent 完成但未开 PR 时的兜底（仅云端运行） |
| `WorkflowPushGuardMiddleware` | 推送 CI 工作流文件前要求人工审批 |
| `ModelSelectionMiddleware` | 按 fast/balanced/performance 路由到不同模型 |
| `ModelCallLimitMiddleware` / `ModelCallTimeoutMiddleware` | 调用次数与超时上限 |
| `ToolErrorMiddleware` / `ToolRetryMiddleware` | 工具错误处理与重试 |

其中 `WorkflowPushGuardMiddleware` 值得单独一提：修改 `.github/workflows/` 这类能改变 CI 行为的文件被单独列为高风险操作，推送前强制人工确认。

### 3.6 Invocation——多平台触发入口

| 平台 | 触发方式 | 说明 |
|------|---------|------|
| **Slack** | 在频道/线程中 @ 机器人 | 支持 `repo:owner/name` 语法指定仓库，频道 topic 可固定仓库 |
| **Linear** | 在 Issue 中评论 `@openswe` | 读取完整 Issue 上下文，完成后回评；官方博客描述的体验是 Agent 以 👀 回应确认接收 |
| **GitHub** | 在 Agent 创建的 PR 中 @openswe | 处理代码审查反馈，推送修复到同一分支 |
| **Dashboard** | Web 界面发起 | 查看任务进度、管理 PR、配置用户与团队设置 |
| **Schedule** | 定时自动化 | 确定性调度重复任务与 CI 监控 |
| **Desktop（实验性）** | 本地客户端 | 打包版目前针对 macOS，源码构建支持 Windows/Linux |

仓库定位的解析规则比早期丰富了不少：`repo:owner/name`（完整指定）、`repo:name`（省略组织）、`repo owner/name`（空格语法）和 GitHub URL 都能识别。Slack 的解析顺序是：线程元数据 → 频道 topic → 用户默认仓库 → 工作区默认仓库 → 环境变量兜底，用户始终可以在消息里用 `repo:owner/name` 覆盖。

每次调用创建确定性线程 ID，同一 Issue 或线程的后续消息会路由到同一个运行中的 Agent 与沙箱。只读的 PR 问答不需要沙箱。

### 3.7 Validation——验证机制

**Prompt 驱动：** Agent 被要求在交付前运行 linter、formatter 和测试。

**PR 创建兜底：** `PullRequestCreationGuardMiddleware` 作为后盾，如果 Agent 声称完成但没有打开 PR，中间件会接管。

**只读审查者：** Reviewer 和 PR Chat 两个 graph 天然只读，审查发现基于 diff、发布回 GitHub，不会改动代码。

**人工审批关卡：** 工作流文件推送前需要人工批准；自动审查与 CI 监控均为 opt-in。

---

## 四、一次任务流转：从 Slack 消息到 PR

下面用一个具体任务来看各模块如何配合。假设场景：工程师在 Slack 线程中 @ 了 open-swe 机器人，要求"修一下 `src/auth/login.py` 里 token 过期不刷新的 bug"。

**第 1 步：触发与路由（Invocation）**

Slack 消息到达，系统按频道 topic、线程元数据、默认仓库的顺序解析出目标仓库，生成确定性线程 ID。如果这是该线程的第一条请求，启动新的 Agent 会话；否则路由到已有 Agent。

**第 2 步：沙箱启动（Sandbox）**

Agent 拿到任务后，沙箱层为它分配一个独立的云端 Linux 环境。如果线程之前已经有活跃沙箱，直接复用。沙箱内克隆目标仓库代码，准备好 Shell 环境。

**第 3 步：上下文注入（Context Engineering）**

`PrepareAgentRunMiddleware` 从沙箱中读取仓库根目录的 `AGENTS.md`（如果有），将其内容注入系统提示词。同时，完整的 Slack 线程历史（包括 bug 描述、后续消息）作为 Source Context 一并注入。Agent 在第一次调用模型之前，就已经知道仓库规范和任务背景。

**第 4 步：Agent 循环开始（Agent Harness）**

`create_deep_agent` 装配的 graph 启动循环。Agent 首先读取 `src/auth/login.py` 定位 bug 代码，然后用 `grep` 搜索相关调用点判断影响范围。

**第 5 步：工具调用与子任务（Tools + Orchestration）**

Agent 发现自己既要改核心逻辑，又要更新对应的测试用例。它用 `task` 工具生成一个子 Agent 负责更新测试文件，自己专注修改 `login.py`。两个 Agent 在各自沙箱中并行工作——如果开启了并行执行的话。

**第 6 步：中间件拦截（Orchestration - Middleware）**

如果工程师在 Slack 中追加了一条"顺便把报错信息也改得更明确些"，`check_message_queue_before_model` 中间件会在下一个模型调用前注入这条新消息，Agent 不需要重新启动就能感知到追加需求。

**第 7 步：验证与提交（Validation + Tools）**

Agent 完成修改后，运行 linter 和测试（Prompt 驱动的验证）。通过后提交变更并创建 PR；如果 Agent 因为某些原因没有成功开 PR，`PullRequestCreationGuardMiddleware` 会兜底。

**第 8 步：反馈闭环（Invocation → 回到第 1 步）**

PR 创建后，Agent 在 Slack 线程中回复 PR 链接。同事在 GitHub PR 下评论 `@openswe` 提出修改意见，触发新一轮 Agent 会话，路由到同一分支继续迭代。如果团队开启了对该 PR 的 baby-sit 监控，CI 失败也会被自动诊断。

这个流程里，每层模块各司其职：沙箱层管执行安全，上下文层管信息注入，编排层管子任务和消息续流，验证层管结果兜底。

---

## 五、与顶级公司内部方案对比

官方博客发布时把 open-swe 与三家公司内部系统做了对比（基于公开信息，2026 年 3 月口径）：

| 决策 | open-swe | Stripe (Minions) | Ramp (Inspect) | Coinbase (Cloudbot) |
|------|----------|------------------|-----------------|---------------------|
| **Harness** | 组合（Deep Agents/LangGraph） | Fork（Goose） | 组合（OpenCode） | 从零构建 |
| **Sandbox** | 可插拔（Modal/Daytona/Runloop 等） | AWS EC2 devbox（预热） | Modal 容器（预热） | 内部方案 |
| **工具数** | ~15，精选 | ~500，按 Agent 选取 | OpenCode SDK + 扩展 | MCP + 自定义 Skills |
| **上下文** | AGENTS.md + issue/thread | 规则文件 + 预注水 | OpenCode 内置 | Linear 优先 + MCP |
| **编排** | 子 Agent + 中间件 | Blueprints（确定性 + 智能） | 会话 + 子会话 | 三种模式 |
| **触发** | Slack、Linear、GitHub | Slack + 内嵌按钮 | Slack + Web + Chrome 扩展 | Slack 原生 |
| **验证** | Prompt 驱动 + PR 安全网 | 三层（本地+CI+1次重试） | 视觉 DOM 验证 | Agent 议会 + 自动合并 |

关键差异在三点：Harness 策略（组合 vs Fork vs 自研）、工具规模（精选 vs 海量）、验证强度（轻量 Prompt 检查 vs 多层验证管线）。open-swe 的策略更偏"最小可行组合"——框架用现成的，差异化的部分放在工具选取和中间件。

半年过去，open-swe 的验证强度已明显加码（人工审批关卡、只读审查者、CI 监控），工具数也早已超过博客口径的 15 个——表中被对比的三家内部系统未必同步演进，读这张表时注意时间基准。

---

## 六、快速开始

open-swe 包含一个 LangGraph 后端、一个 Web Dashboard 和一个实验性桌面客户端。一次部署用同一个 URL 同时服务 API、webhook 和 Dashboard。

### 6.1 本地开发

```bash
# 1. 克隆仓库
git clone https://github.com/langchain-ai/open-swe.git
cd open-swe

# 2. 安装依赖（后端 uv，前端 pnpm）
uv venv
source .venv/bin/activate
uv sync --all-extras

# 3. 构建 Dashboard
make build-dashboard

# 4. 运行（API + Dashboard 同在 http://localhost:2024）
make dev
```

然后创建 GitHub App 和 Slack App，按开发指南填写 `.env`，在 `http://localhost:2024` 登录。本地调试 webhook 需要一条 ngrok 隧道（`make tunnel NGROK_DOMAIN=<name>.ngrok-free.dev`，只暴露 `/webhooks/*`——开发服务器的 LangGraph API 没有认证，不要全量暴露）。

### 6.2 生产部署

生产自托管走独立的 LangGraph Agent Server，需要 license key；也支持 Docker（仓库根目录有 `Dockerfile` 和 `compose.yaml`）。完整的部署清单——LangSmith API key、GitHub App 权限、模型提供商、Slack App 配置、Linear 触发器——见 [docs/INSTALLATION.md](https://github.com/langchain-ai/open-swe/blob/main/docs/INSTALLATION.md)。

环境要求：Python（uv 管理依赖）、pnpm（前端构建）、GitHub App（OAuth 认证）、LangSmith（默认沙箱与 tracing）、模型提供商 API key。

---

## 七、定制指南

open-swe 的每个组件都可以定制，[docs/CUSTOMIZATION.md](https://github.com/langchain-ai/open-swe/blob/main/docs/CUSTOMIZATION.md) 按五条主线展开：

| 组件 | 定制选项 |
|------|----------|
| Sandbox | 换提供商（Modal/Daytona/Runloop/E2B/自研）、自定义沙箱快照 |
| Model | `provider:model` 格式任意切换，按上下文路由不同模型，走 LangSmith LLM Gateway |
| Tools | 工作区/个人 MCP 服务器、增删 Python 工具、条件化工具 |
| Triggers | 移除触发平台、配置默认仓库、自定义仓库解析 |
| Prompts | `default_prompt.md` 全局默认 + 每仓库 `AGENTS.md` |
| Middleware | 添加自定义中间件 |

其中提示词的加载顺序是：默认提示词 → 系统提示词各分节 → AGENTS.md（按仓库）。全局规则放 `default_prompt.md`，仓库特有规范放各自的 AGENTS.md，两层各管各的。

---

## 八、功能清单

- 从 Dashboard / Slack / Linear / GitHub 触发任务，或用定时自动化按计划执行
- 任务运行中可发送后续消息，Agent 在下一步拾取
- 多任务在独立云端沙箱中并行，沙箱随线程持久复用
- GitHub App 边界 + 可选的每用户 OAuth，组织/仓库白名单与操作者授权检查
- 完成后自动提交变更并打开 PR（云端运行有兜底保证）
- 支持子 Agent 处理并行子任务
- 按需或自动执行只读 PR 审查，从历史反馈学习仓库审查风格
- `/baby-sit` 监控选定 PR：诊断 CI 失败，只重跑有证据的 flaky 任务
- 只读 PR 问答（Chat），不改代码调查变更
- 桌面客户端（实验性）直接对白名单内的本地项目运行同一套 Agent

---

## 九、适用场景

| 场景 | 说明 |
|------|------|
| **代码审查自动化** | 自动处理 PR 反馈，提交修复；只读审查学习团队风格 |
| **Issue 自动化** | Linear Issue 触发，自动定位代码并提交 PR |
| **内务自动化** | 文档更新、依赖管理、CI 问题修复，可定时执行 |
| **CI 监控** | baby-sit 模式盯 PR，诊断失败并只重跑有证据的 flaky 任务 |
| **知识问答** | 只读 PR Chat，基于 diff 回答"这个改动为什么这样做" |

---

## 十、采用建议

open-swe 的架构假设了你的团队已经满足几个前置条件：有 GitHub 上的代码仓库、使用 Slack 或 Linear 作为日常工作入口、能够为每个任务分配云端沙箱资源。如果这些条件不满足，引入成本会显著上升。

**建议的采用顺序：**

1. **先跑通单仓库、单平台。** 挑一个代码结构清晰的内部仓库，只接 Slack 或只接 Linear，验证 Agent 在你们的代码规范下能否稳定完成任务。
2. **写好 AGENTS.md。** 这个文件是 Agent 的"入职文档"，里面写清楚测试怎么跑、lint 规则是什么、分支命名规范。AGENTS.md 写得越好，Agent 产出的 PR 越不需要人工返工。
3. **逐步添加中间件。** 不要一上来就写一堆自定义中间件。先观察 Agent 在什么环节反复出错，再针对性地加中间件拦截。
4. **扩展到多仓库。** 单仓库跑稳之后，再接入更多仓库。注意不同仓库的 AGENTS.md 和沙箱资源需求可能不同。
5. **最后接 GitHub PR 反馈回路。** 让 Agent 能处理 PR review 评论是最难的一步——需要模型理解代码审查语境。建议在 Slack/Linear 触发链路跑熟之后再开这个功能。

**哪类团队适合先用：**
- 已有 GitHub + Slack/Linear 工作流的中小型工程团队。
- 有内部工具或基础设施维护需求，但不想从零搭建 Agent 基础设施。
- 希望快速验证"AI 写代码"在内部代码库上的效果，而不是先投入数月自研。

**哪类团队可以等等：**
- 代码仓库分散在多平台、多工具链，且没有统一规范文件的组织——先收敛工作流再引入 Agent 更划算。
- 对云端沙箱有合规或数据驻留要求的团队——open-swe 支持自托管，但需先确认所选沙箱提供商与部署方式满足合规要求。
- 在意生产部署成本差额的团队——生产自托管需要 LangGraph Agent Server 的 license key，先评估这一层。

---

## 资源链接

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/langchain-ai/open-swe |
| 官方博客（发布公告，2026-03） | https://blog.langchain.com/open-swe-an-open-source-framework-for-internal-coding-agents/ |
| 安装指南 | https://github.com/langchain-ai/open-swe/blob/main/docs/INSTALLATION.md |
| 定制指南 | https://github.com/langchain-ai/open-swe/blob/main/docs/CUSTOMIZATION.md |
| 开发指南 | https://github.com/langchain-ai/open-swe/blob/main/docs/DEVELOPMENT.md |
| API 契约 | https://github.com/langchain-ai/open-swe/blob/main/swagger.json |

---

**相关话题标签**

#open-swe #LangChain #编程Agent #企业内部AI #Deep Agents

---

## 参考来源与口径说明

- **数据口径**：GitHub Stars（10,750）、Forks（1,282）、Contributors（55）、语言占比（Python 66% / TypeScript 29%）均为 2026-09-23 经 GitHub API 核实的读数；Commits 超过 2000（API 分页上限）。项目处于活跃开发期，数字会持续变化。
- **机制口径**：架构、工具、中间件、触发方式等机制描述以 2026-09-23 的 main 分支为口径，对照源码核实（`agent/server.py` 的 `create_deep_agent` 装配、`agent/tools/` 工具清单、`agent/graphs/` 五入口、默认模型逻辑 `agent/dashboard/options.py`）。open-swe 迭代很快，官方 README 也明确提示"API、安装方式与产品形态可能继续演进"，以仓库现行文档为准。
- **对比表口径**：§五的对比表转译自官方博客（2026-03-17 发布）基于公开信息的总结，Stripe/Ramp/Coinbase 内部系统一列未随 open-swe 的演进更新。
- **转述口径**：Linear 触发时"以 👀 回应确认接收"出自官方博客描述，现行代码中该交互已改由 Linear MCP 集成与通知系统处理，实际体验以部署版本为准；"沙箱不可达自动重建"为博客早期口径，现行行为是安全失败、不静默替换。
- **历史说明**：本文发布于 2026-03-28（官方博客发布 11 天后），2026-09-23 全面核对并更新至当前仓库状态；文中不另标注每次修订。
