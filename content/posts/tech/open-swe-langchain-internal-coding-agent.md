---
title: "open-swe：LangChain 开源的 8.7k Stars 企业内部编程 Agent 框架"
date: 2026-03-28T20:50:00+08:00
slug: "open-swe-langchain-internal-coding-agent"
description: "深度解读 LangChain 开源的 open-swe：8.7k Stars 的企业内部编程 Agent 框架，复刻 Stripe/Ramp/Coinbase 内部 Agent 模式，支持 Slack/Linear/GitHub 触发。"
draft: false
categories: ["技术笔记"]
tags: ["open-swe", "LangChain", "编程Agent", "企业内部AI", "Deep Agents"]
---

# open-swe：LangChain 开源的 8.7k Stars 企业内部编程 Agent 框架

> **目标读者**：希望构建企业内部编程 Agent 的工程师和架构师
> **核心问题**：如何像 Stripe/Ramp/Coinbase 一样构建自己的内部编程 Agent？
> **难度**：⭐⭐⭐⭐（专家设计）
> **来源**：GitHub langchain-ai/open-swe，2026-03-28

---

## 一、项目概览

### 1.1 为什么这个项目值得关注

[open-swe](https://github.com/langchain-ai/open-swe) 是 LangChain 开源的企业内部编程 Agent 框架，源自 Stripe、Ramp、Coinbase 等顶级工程团队构建内部编程 Agent 的实践经验。

**核心数据：**

| 指标 | 数值 |
|------|------|
| GitHub Stars | 8.7k |
| Forks | 1k |
| Contributors | 20 |
| Commits | 614 |
| License | MIT |
| 语言 | Python 98.6% |

**项目定位：**

> Open-source framework for building your org's internal coding agent.
> 构建企业自己的内部编程 Agent 的开源框架

### 1.2 背景故事

Stripe、Ramp、Coinbase 等顶级工程组织都在构建自己的内部编程 Agent——Slackbots、CLI 和 Web 应用，让工程师在熟悉的工作环境中直接使用 AI 能力。

**open-swe 是这些内部模式的 开源版本**，基于 LangGraph 和 Deep Agents 构建，提供了与这些公司内部构建相同的架构：云端沙箱、Slack/Linear 调用、子 Agent 编排、自动 PR 创建——可定制适配自己的代码库和工作流程。

### 1.3 核心特色

| 特色 | 说明 |
|------|------|
| **三大平台触发** | Slack、Linear、GitHub 无缝触发 |
| **云端沙箱隔离** | 每任务独立沙箱，并行执行 |
| **15+ 精选工具** | 不是堆砌工具，而是精选聚焦 |
| **AGENTS.md 上下文** | 仓库级规范注入 |
| **子 Agent 编排** | 并行子任务，隔离执行 |
| **自动 PR 创建** | 完成后自动提交并打开 Draft PR |

---

## 二、技术架构

### 2.1 整体架构

open-swe 做出了与顶级内部编程 Agent 相同的核心架构决策：

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

### 2.2 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 核心框架 | LangGraph（状态机编排框架） | 状态机编排 |
| Agent 框架 | Deep Agents（Deep Agents 框架） | Agent 构建基座 |
| 沙箱 | Modal/Daytona/Runloop/LangSmith | 云端隔离环境（隔离云端执行环境） |
| 语言 | Python 98.6% | 主要开发语言 |
| 触发平台 | Slack/Linear/GitHub | 三大平台集成 |

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

open-swe **组合（compose）** 而非从零构建或 Fork，基于 Deep Agents 框架构建。

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

**组合优势：**
- 保持升级路径（可拉取上游改进）
- 完全定制编排、工具和中间件

### 3.2 Sandbox——隔离云端环境

每个任务在独立的**隔离云端沙箱**中运行——远程 Linux 环境，提供完整 Shell 访问。

**核心原则：先隔离，再在边界内给予完整权限。**

| 特性 | 说明 |
|------|------|
| 持久化沙箱 | 每线程独立沙箱，跨后续消息复用 |
| 自动重建 | 沙箱不可达时自动重建 |
| 并行执行 | 多任务并行，各自独立沙箱 |

**支持的沙箱提供商：**

| 提供商 | 说明 |
|--------|------|
| Modal | 云端函数/容器平台 |
| Daytona | 开发者环境平台 |
| Runloop | AI 编程环境 |
| LangSmith | LangChain 监控平台 |

### 3.3 Tools——精选而非堆砌

**Stripe 的关键洞察：工具 curation（精选）比工具数量更重要。**

open-swe 遵循这一原则，提供少量聚焦的工具集：

| 工具 | 用途 |
|------|------|
| `execute` | 在沙箱中执行 Shell 命令 |
| `fetch_url` | 获取网页并转为 Markdown |
| `http_request` | API 调用（GET、POST 等） |
| `commit_and_open_pr` | Git 提交 + 打开 GitHub Draft PR |
| `linear_comment` | 向 Linear 工单发布更新 |
| `slack_thread_reply` | 在 Slack 线程中回复 |

**内置 Deep Agents 工具：**
- `read_file`、`write_file`、`edit_file`、`ls`、`glob`、`grep`
- `write_todos`（待办列表）
- `task`（子 Agent 生成）

### 3.4 Context Engineering——上下文工程

open-swe 从两个来源收集上下文：

**AGENTS.md：**
- 如果仓库根目录存在 `AGENTS.md` 文件，从沙箱读取并注入系统提示词
- 这是仓库级别的规则文件：编码规范、测试要求、架构决策

**Source Context：**
- 完整的 Linear Issue（标题、描述、评论）或 Slack 线程历史
- Agent 从丰富的上下文开始，而非通过工具调用逐步发现

### 3.5 Orchestration——子 Agent + 中间件

**子 Agent：**
- Deep Agents 框架原生支持通过 `task` 工具生成子 Agent
- 主 Agent 可以将独立子任务分散到隔离子 Agent
- 每个子 Agent 有自己的中间件栈、待办列表和文件操作

**中间件：**
- 确定性中间件钩子环绕 Agent 循环运行

| 中间件 | 说明 |
|--------|------|
| `check_message_queue_before_model` | 在下一个模型调用前注入后续消息（Linear 评论或 Slack 消息） |
| `open_pr_if_needed` | Agent 完成但未打开 PR 时的安全网 |
| `ToolErrorMiddleware` | 优雅地捕获和处理工具错误 |

### 3.6 Invocation——三大触发入口

| 平台 | 触发方式 | 说明 |
|------|---------|------|
| **Slack** | 在线程中 @ 机器人 | 支持 `repo:owner/name` 语法指定仓库 |
| **Linear** | 在 Issue 中评论 `@openswe` | 读取完整 Issue 上下文，👀 确认，完成后回评 |
| **GitHub** | 在 Agent 创建的 PR 中 @openswe | 处理代码审查反馈，推送修复到同一分支 |

每次调用创建确定性线程 ID，同一 Issue 或线程的后续消息路由到同一运行中的 Agent。

### 3.7 Validation——验证机制

**Prompt-driven：**
- Agent 被指示在提交前运行 linter、formatter 和测试

**PR Safety Net：**
- `open_pr_if_needed` 中间件作为后盾
- 如果 Agent 完成但未打开 PR，中间件自动处理

---

## 四、与顶级公司对比

| 决策 | open-swe | Stripe (Minions) | Ramp (Inspect) | Coinbase (Cloudbot) |
|------|----------|------------------|-----------------|---------------------|
| **Harness** | Deep Agents/LangGraph | Forked (Goose) | OpenCode | 从零构建 |
| **Sandbox** | Modal/Daytona/Runloop | AWS EC2 devboxes | Modal containers | 内部方案 |
| **工具数** | ~15，精选 | ~500，按 Agent 精选 | OpenCode SDK + 扩展 | MCPs + 自定义 Skills |
| **上下文** | AGENTS.md + issue/thread | Rule files + pre-hydration | OpenCode 内置 | Linear-first + MCPs |
| **编排** | 子 Agent + 中间件 | Blueprints | Sessions + 子会话 | 三种模式 |
| **触发** | Slack, Linear, GitHub | Slack + 内嵌按钮 | Slack + web + Chrome 扩展 | Slack-native |
| **验证** | Prompt驱动 + PR安全网 | 三层（本地+CI+1次重试） | 视觉 DOM 验证 | Agent 议会 + 自动合并 |

---

## 五、快速开始

### 5.1 环境要求

| 工具 | 要求 |
|------|------|
| Python | ≥3.10 |
| uv | 最新版（包管理器） |
| GitHub App | 用于 OAuth 认证 |
| LangSmith | 可选，用于监控 |

### 5.2 安装步骤

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

### 5.3 配置三大触发平台

**Slack：**
- 在 Slack 工作区安装 Bot
- 配置 `SLACK_BOT_TOKEN` 和 `SLACK_SIGNING_SECRET`

**Linear：**
- 创建 Linear App
- 配置 `LINEAR_API_KEY`

**GitHub：**
- 创建 GitHub App
- 配置 `GITHUB_APP_ID` 和 `GITHUB_PRIVATE_KEY`

详见 [INSTALLATION.md](https://github.com/langchain-ai/open-swe/blob/main/INSTALLATION.md)

---

## 六、定制指南

open-swe 的每个组件都可以定制，详见 [CUSTOMIZATION.md](https://github.com/langchain-ai/open-swe/blob/main/CUSTOMIZATION.md)

### 6.1 可定制的组件

| 组件 | 定制选项 |
|------|----------|
| Sandbox 提供商 | Modal / Daytona / Runloop / 自定义 |
| 模型 | 支持的 LLM 提供商 |
| 工具 | 添加/修改工具 |
| 触发器 | 扩展触发平台 |
| 系统提示词 | 定制 repo 级规范 |
| 中间件 | 添加自定义中间件 |

### 6.2 中间件扩展

```python
from open_swe.middleware import CustomMiddleware

class MyMiddleware(CustomMiddleware):
    async def before_model(self, state):
        # 自定义逻辑
        return state
```

---

## 七、核心功能一览

| 功能 | 说明 |
|------|------|
| ✅ 从 Linear/Slack/GitHub 触发 | 评论 `@openswe` 即可启动任务 |
| ✅ 即时确认 | 拾取消息时用 👀 回应 |
| ✅ 运行中可消息 | 发送后续消息，Agent 在下一步拾取 |
| ✅ 多任务并行 | 每任务在独立云端沙箱中运行 |
| ✅ GitHub OAuth 内置 | 自动用你的 GitHub 账号认证 |
| ✅ 自动打开 PR | 完成时提交变更并打开 Draft PR |
| ✅ 子 Agent 支持 | Agent 可生成子 Agent 处理并行子任务 |

---

## 八、适用场景

| 场景 | 说明 |
|------|------|
| **代码审查自动化** | 自动处理 PR 反馈，提交修复 |
| **Issue 自动化** | Linear Issue 触发，自动定位代码并提交 PR |
| **内务自动化** | 文档更新、依赖管理、CI 问题修复 |
| **知识问答** | 基于代码库的问答 Agent |

---

## 九、总结与展望

### 9.1 核心价值

open-swe 的核心价值在于**将顶级工程公司的内部 Agent 模式开源**，让每家企业都能构建自己的编程 Agent。

| 传统方式 | open-swe 方式 |
|----------|--------------|
| 从零构建 | 基于成熟框架组合 |
| 单点解决方案 | 完整架构（7大模块） |
| 闭源内部工具 | 完全开源可定制 |
| 单一触发 | 三大平台无缝触发 |

### 9.2 技术亮点

1. **LangGraph 状态机**：成熟的 Agent 编排能力
2. **Deep Agents 组合**：站在开源巨人的肩膀上
3. **云端沙箱隔离**：安全与权限的完美平衡
4. **中间件架构**：灵活扩展的验证和编排
5. **三大平台集成**：覆盖主流工作流

### 9.3 资源链接

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

---

*open-swe 由 LangChain 团队开源，采用 MIT 许可证，基于 LangGraph 和 Deep Agents 构建。*
