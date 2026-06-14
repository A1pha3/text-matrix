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

```text

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

```text

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
```textbash
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
```textpython
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

#open-swe #LangChain #编程 Agent #企业内部 AI #Deep Agents

**来源**

- GitHub：https://github.com/langchain-ai/open-swe