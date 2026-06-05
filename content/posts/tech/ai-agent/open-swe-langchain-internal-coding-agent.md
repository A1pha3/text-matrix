---
title: "open-swe：LangChain 开源的 8.7k Stars 企业内部编程 Agent 框架"
date: "2026-03-28T20:50:00+08:00"
slug: "open-swe-langchain-internal-coding-agent"
aliases:
  - /posts/tech/open-swe-langchain-internal-coding-agent/
description: "深度解读 LangChain 开源的 open-swe：8.7k Stars 的企业内部编程 Agent 框架，复刻 Stripe/Ramp/Coinbase 内部 Agent 模式，支持 Slack/Linear/GitHub 触发。"
draft: false
categories: ["技术笔记"]
tags: ["open-swe", "LangChain", "编程Agent", "企业内部AI", "Deep Agents"]
---

# open-swe：LangChain 开源的内部编程 Agent 框架

open-swe 解决的不是"让 AI 写代码"的问题——那是基础模型已经做到的事。它解决的是"把 AI 写代码变成工程团队可控、可审计、可嵌入现有工作流的系统能力"。本文从架构决策、模块边界和任务流转三个角度拆解这套框架。

---

## 一、项目概览

### 1.1 这个项目在做什么

[open-swe](https://github.com/langchain-ai/open-swe) 是 LangChain 开源的内部编程 Agent 框架，源自 Stripe、Ramp、Coinbase 等团队构建内部编程 Agent 的工程实践。它本质上是一套"编排层 + 沙箱 + 工具集 + 上下文注入"的组合方案，让你在 Slack、Linear、GitHub 这些工程师日常使用的平台上直接触发编码任务。

| 指标 | 数值 |
|------|------|
| GitHub Stars | 8.7k |
| Forks | 1k |
| Contributors | 20 |
| Commits | 614 |
| License | MIT |
| 语言 | Python 98.6% |

> Open-source framework for building your org's internal coding agent.
> 构建企业自己的内部编程 Agent 的开源框架

### 1.2 背景

Stripe、Ramp、Coinbase 的工程团队都在内部搭建自己的编程 Agent，形态是 Slackbot、CLI（命令行接口）或 Web 应用，让工程师在日常工具链里直接调用 AI 来完成编码任务。open-swe 把这些内部模式做成了开源版本，基于 LangGraph 和 Deep Agents，提供云端沙箱、Slack/Linear 调用、子 Agent 编排、自动 PR 创建——可按需适配仓库和工作流。

### 1.3 关键设计决策

| 决策 | 说明 |
|------|------|
| **三大平台触发** | Slack、Linear、GitHub 均可发起任务 |
| **云端沙箱隔离** | 每任务独立沙箱，互不干扰 |
| **15 个工具，不做工具海** | 区别于堆砌数百个工具的做法，聚焦高频操作 |
| **AGENTS.md 上下文注入** | 仓库级规范直接注入系统提示词 |
| **子 Agent 编排** | 主 Agent 可派生子 Agent 处理独立子任务 |
| **完成后自动开 PR** | 提交变更后自动创建 Draft PR |

---

## 二、技术架构

### 2.1 整体架构

open-swe 的架构决策与几家公司内部方案一致：不自己写 Agent 循环，而是组合现有框架，在上面做编排和定制。

```
┌─────────────────────────────────────────────────────────────┐
│                    open-swe 架构                              │
├─────────────────────────────────────────────────────────────┤
│  1. Agent Harness（基于 Deep Agents）                         │
│     ┌─────────────────────────────────────────────────┐     │
│     │  create_deep_agent(model, system_prompt, tools) │     │
│     └─────────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────────┤
│  2. Sandbox（隔离云端环境）                                   │
│     Modal / Daytona / Runloop / LangSmith                   │
│     每任务独立沙箱，并行执行，全权限隔离                       │
├─────────────────────────────────────────────────────────────┤
│  3. Tools（精选 ~15 个工具）                                │
│     execute | fetch_url | http_request                       │
│     commit_and_open_pr | linear_comment | slack_thread_reply │
├─────────────────────────────────────────────────────────────┤
│  4. Context Engineering（上下文工程）                          │
│     AGENTS.md + Linear issue / Slack thread                 │
├─────────────────────────────────────────────────────────────┤
│  5. Orchestration（编排层）                                  │
│     子 Agent + Middleware                                   │
├─────────────────────────────────────────────────────────────┤
│  6. Invocation（触发入口）                                    │
│     Slack / Linear / GitHub                                 │
├─────────────────────────────────────────────────────────────┤
│  7. Validation（验证层）                                     │
│     Prompt-driven + PR Safety Net                           │
└─────────────────────────────────────────────────────────────┘
```

七层职责简要区分：

- **Agent Harness**（第 1 层）：决定 Agent 如何循环、如何调用模型和工具。open-swe 自己不实现这一层，而是用 Deep Agents 的 `create_deep_agent`。
- **Sandbox**（第 2 层）：决定代码在哪执行。每任务一个云端 Linux 环境，有完整 Shell 权限但彼此隔离。
- **Tools**（第 3 层）：决定 Agent 能做什么操作——执行命令、发 HTTP 请求、提交 PR、回复 Slack 等。
- **Context Engineering**（第 4 层）：决定 Agent 启动时知道什么——仓库规范（AGENTS.md）和任务上下文（Issue/线程历史）。
- **Orchestration**（第 5 层）：决定子任务如何拆分、中间件如何介入。
- **Invocation**（第 6 层）：决定用户从哪里触发任务。
- **Validation**（第 7 层）：决定任务完成后如何检查结果。

### 2.2 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 核心框架 | LangGraph | 状态机编排 |
| Agent 框架 | Deep Agents | Agent 构建基座 |
| 沙箱 | Modal / Daytona / Runloop / LangSmith | 云端隔离执行环境 |
| 语言 | Python 98.6% | 主要开发语言 |
| 触发平台 | Slack / Linear / GitHub | 三大平台集成 |

### 2.3 核心目录结构

```
open-swe/
├── agent/              # Agent 核心实现
├── scripts/            # 工具脚本
├── static/             # 静态资源
├── tests/             # 测试套件
├── .github/workflows/  # CI/CD 工作流
├── CUSTOMIZATION.md    # 定制指南
├── INSTALLATION.md     # 安装指南
├── Makefile           # 构建脚本
├── pyproject.toml     # Python 项目配置
└── uv.lock            # 依赖锁定
```

---

## 三、七大架构模块详解

### 3.1 Agent Harness——基于 Deep Agents

open-swe 采用组合而非从零构建或 Fork。它基于 Deep Agents 框架，调用 `create_deep_agent` 来启动 Agent 循环。

```python
create_deep_agent(
    model="anthropic:claude-opus-4-6",
    system_prompt=construct_system_prompt(repo_dir, ...),
    tools=[
        http_request,
        fetch_url,
        commit_and_open_pr,
        linear_comment,
        slack_thread_reply,
    ],
    backend=sandbox_backend,
    middleware=[
        ToolErrorMiddleware(),
        check_message_queue_before_model,
        ...
    ],
)
```

这样做的好处：可以拉取 Deep Agents 的上游改进，同时在工具、中间件和编排上做完全定制。

### 3.2 Sandbox——隔离云端环境

每个任务在独立的云端 Linux 沙箱中运行，拥有完整 Shell 访问权限。设计原则是：先隔离，再在隔离边界内给足权限。

| 特性 | 说明 |
|------|------|
| 持久化沙箱 | 每线程独立沙箱，跨后续消息复用 |
| 自动重建 | 沙箱不可达时自动重建 |
| 并行执行 | 多任务并行，各自独立沙箱 |

支持的沙箱提供商：

| 提供商 | 说明 |
|--------|------|
| Modal | 云端函数/容器平台 |
| Daytona | 开发者环境平台 |
| Runloop | AI 编程环境 |
| LangSmith | LangChain 监控平台 |

### 3.3 Tools——聚焦高频操作

Stripe 团队的一个关键判断：工具的数量远不如工具的选取重要。open-swe 给 Agent 配备了少量聚焦的工具：

| 工具 | 用途 |
|------|------|
| `execute` | 在沙箱中执行 Shell 命令 |
| `fetch_url` | 获取网页并转为 Markdown |
| `http_request` | API 调用（GET、POST 等） |
| `commit_and_open_pr` | Git 提交 + 打开 GitHub Draft PR |
| `linear_comment` | 向 Linear 工单发布更新 |
| `slack_thread_reply` | 在 Slack 线程中回复 |

Deep Agents 框架还内置了 `read_file`、`write_file`、`edit_file`、`ls`、`glob`、`grep`、`write_todos`（待办列表）和 `task`（子 Agent 生成）。

### 3.4 Context Engineering——上下文工程

Agent 启动时从两个来源获取上下文：

**AGENTS.md：** 如果仓库根目录存在 `AGENTS.md` 文件，从沙箱读取并注入系统提示词。这是仓库级别的规则文件，涵盖编码规范、测试要求和架构决策。

**Source Context：** 完整的 Linear Issue（标题、描述、评论）或 Slack 线程历史。Agent 启动时就已经知道任务全貌，而不是通过工具调用逐步摸索。

### 3.5 Orchestration——子 Agent + 中间件

**子 Agent：** Deep Agents 框架原生支持通过 `task` 工具生成子 Agent。主 Agent 把独立子任务分派给隔离子 Agent，每个子 Agent 有自己的中间件栈、待办列表和文件操作。

**中间件：** 中间件是环绕 Agent 循环运行的钩子：

| 中间件 | 说明 |
|--------|------|
| `check_message_queue_before_model` | 在模型调用前注入后续消息（Linear 评论或 Slack 消息） |
| `open_pr_if_needed` | Agent 完成但未打开 PR 时的后盾 |
| `ToolErrorMiddleware` | 捕获和处理工具错误 |

### 3.6 Invocation——三大触发入口

| 平台 | 触发方式 | 说明 |
|------|---------|------|
| **Slack** | 在线程中 @ 机器人 | 支持 `repo:owner/name` 语法指定仓库 |
| **Linear** | 在 Issue 中评论 `@openswe` | 读取完整 Issue 上下文，👀 确认，完成后回评 |
| **GitHub** | 在 Agent 创建的 PR 中 @openswe | 处理代码审查反馈，推送修复到同一分支 |

每次调用创建确定性线程 ID，同一 Issue 或线程的后续消息会路由到同一个运行中的 Agent。

### 3.7 Validation——验证机制

**Prompt-driven：** Agent 被要求在执行前运行 linter、formatter 和测试。

**PR Safety Net：** `open_pr_if_needed` 中间件作为兜底，如果 Agent 声称完成但没有打开 PR，中间件会接管。

---

## 四、一次任务流转：从 Slack 消息到 Draft PR

下面用一个具体任务来看各模块如何配合。假设场景：工程师在 Slack 线程中 @ 了 open-swe 机器人，要求"修一下 `src/auth/login.py` 里 token 过期不刷新的 bug"。

**第 1 步：触发与路由（Invocation）**

Slack 消息到达，系统解析出仓库名（通过 `repo:owner/name` 或预设默认仓库），生成确定性线程 ID。如果这是该线程的第一条请求，启动新的 Agent 会话；否则路由到已有 Agent。

**第 2 步：沙箱启动（Sandbox）**

Agent 拿到任务后，沙箱层为它分配一个独立的云端 Linux 环境。如果线程之前已经有活跃沙箱，直接复用。沙箱内克隆目标仓库代码，准备好 Shell 环境。

**第 3 步：上下文注入（Context Engineering）**

系统从沙箱中读取仓库根目录的 `AGENTS.md`（如果有），将其内容注入系统提示词。同时，完整的 Slack 线程历史（包括 bug 描述、后续消息）作为 Source Context 一并注入。Agent 在第一次调用模型之前，就已经知道仓库规范和任务背景。

**第 4 步：Agent 循环开始（Agent Harness）**

`create_deep_agent` 启动 Agent 循环。Agent 首先读取 `src/auth/login.py` 定位 bug 代码，然后用 `grep` 搜索相关调用点判断影响范围。

**第 5 步：工具调用与子任务（Tools + Orchestration）**

Agent 发现自己既要改核心逻辑，又要更新对应的测试用例。它用 `task` 工具生成一个子 Agent 负责更新测试文件，自己专注修改 `login.py`。两个 Agent 在各自沙箱中并行工作——如果开启了并行执行的话。

**第 6 步：中间件拦截（Orchestration - Middleware）**

如果工程师在 Slack 中追加了一条"顺便把报错信息也改得更明确些"，`check_message_queue_before_model` 中间件会在下一个模型调用前注入这条新消息，Agent 不需要重新启动就能感知到追加需求。

**第 7 步：验证与提交（Validation + Tools）**

Agent 完成修改后，运行 linter 和测试（Prompt-driven validation）。通过后调用 `commit_and_open_pr`，生成 commit 并创建一个 Draft PR。如果 Agent 因为某些原因没有成功开 PR，`open_pr_if_needed` 中间件会兜底。

**第 8 步：反馈闭环（Invocation → 回到第 1 步）**

PR 创建后，Agent 在 Slack 线程中回复 PR 链接。同事在 GitHub PR 下评论 `@openswe` 提出修改意见，触发新一轮 Agent 会话，路由到同一分支继续迭代。

这个流程里，每层模块各司其职：沙箱层管执行安全，上下文层管信息注入，编排层管子任务和消息续流，验证层管结果兜底。

---

## 五、与顶级公司对比

| 决策 | open-swe | Stripe (Minions) | Ramp (Inspect) | Coinbase (Cloudbot) |
|------|----------|------------------|-----------------|---------------------|
| **Harness** | Deep Agents/LangGraph | Forked (Goose) | OpenCode | 从零构建 |
| **Sandbox** | Modal/Daytona/Runloop | AWS EC2 devboxes | Modal containers | 内部方案 |
| **工具数** | ~15 | ~500，按 Agent 选取 | OpenCode SDK + 扩展 | MCPs + 自定义 Skills |
| **上下文** | AGENTS.md + issue/thread | Rule files + pre-hydration | OpenCode 内置 | Linear-first + MCPs |
| **编排** | 子 Agent + 中间件 | Blueprints | Sessions + 子会话 | 三种模式 |
| **触发** | Slack, Linear, GitHub | Slack + 内嵌按钮 | Slack + web + Chrome 扩展 | Slack-native |
| **验证** | Prompt 驱动 + PR 安全网 | 三层（本地+CI+1次重试） | 视觉 DOM 验证 | Agent 议会 + 自动合并 |

关键差异在三点：Harness 策略（组合 vs Fork vs 自研）、工具规模（精选 vs 海量）、验证强度（轻量 Prompt 检查 vs 多层验证管线）。open-swe 的策略更偏"最小可行组合"——框架用现成的，差异化的部分放在工具选取和中间件。

---

## 六、快速开始

### 6.1 环境要求

| 工具 | 要求 |
|------|------|
| Python | ≥3.10 |
| uv | 最新版（包管理器） |
| GitHub App | 用于 OAuth 认证 |
| LangSmith | 可选，用于监控 |

### 6.2 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/langchain-ai/open-swe.git
cd open-swe

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入必要的 API keys

# 4. 运行
make run
```

### 6.3 配置三大触发平台

**Slack：** 在 Slack 工作区安装 Bot，配置 `SLACK_BOT_TOKEN` 和 `SLACK_SIGNING_SECRET`。

**Linear：** 创建 Linear App，配置 `LINEAR_API_KEY`。

**GitHub：** 创建 GitHub App，配置 `GITHUB_APP_ID` 和 `GITHUB_PRIVATE_KEY`。

详见 [INSTALLATION.md](https://github.com/langchain-ai/open-swe/blob/main/INSTALLATION.md)

---

## 七、定制指南

open-swe 的每个组件都可以定制，详见 [CUSTOMIZATION.md](https://github.com/langchain-ai/open-swe/blob/main/CUSTOMIZATION.md)

### 7.1 可定制的组件

| 组件 | 定制选项 |
|------|----------|
| Sandbox 提供商 | Modal / Daytona / Runloop / 自定义 |
| 模型 | 支持的 LLM 提供商 |
| 工具 | 添加/修改工具 |
| 触发器 | 扩展触发平台 |
| 系统提示词 | 定制 repo 级规范 |
| 中间件 | 添加自定义中间件 |

### 7.2 中间件扩展

```python
from open_swe.middleware import CustomMiddleware

class MyMiddleware(CustomMiddleware):
    async def before_model(self, state):
        # 自定义逻辑
        return state
```

---

## 八、功能清单

- 从 Linear / Slack / GitHub 触发任务（评论 `@openswe`）
- 拾取消息时用 👀 回应
- 任务运行中可发送后续消息，Agent 在下一步拾取
- 多任务在独立云端沙箱中并行
- GitHub OAuth 内置，自动用你的 GitHub 账号认证
- 完成后自动提交变更并打开 Draft PR
- 支持子 Agent 处理并行子任务

---

## 九、适用场景

| 场景 | 说明 |
|------|------|
| **代码审查自动化** | 自动处理 PR 反馈，提交修复 |
| **Issue 自动化** | Linear Issue 触发，自动定位代码并提交 PR |
| **内务自动化** | 文档更新、依赖管理、CI 问题修复 |
| **知识问答** | 基于代码库的问答 Agent |

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
- 对云端沙箱有合规或数据驻留要求的团队——先确认沙箱提供商是否满足合规需求。

---

## 资源链接

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/langchain-ai/open-swe |
| 官方博客 | https://blog.langchain.com/open-swe-an-open-source-framework-for-internal-coding-agents/ |
| 安装指南 | https://github.com/langchain-ai/open-swe/blob/main/INSTALLATION.md |
| 定制指南 | https://github.com/langchain-ai/open-swe/blob/main/CUSTOMIZATION.md |
| Twitter | https://x.com/langchain |

---

**相关话题标签**

#open-swe #LangChain #编程Agent #企业内部AI #Deep Agents

**来源**

- GitHub：https://github.com/langchain-ai/open-swe