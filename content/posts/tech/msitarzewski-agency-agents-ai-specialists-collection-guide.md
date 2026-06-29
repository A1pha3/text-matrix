---
title: "Agency Agents：一组可直接装进 Claude Code / Cursor 的「人格化」AI Agent 角色库"
slug: "msitarzewski-agency-agents-ai-specialists-collection-guide"
date: 2026-06-29T21:02:57+08:00
lastmod: 2026-06-29T21:02:57+08:00
draft: false
categories: ["技术笔记"]
tags: ["GitHub", "AI-Agent", "Claude-Code", "Cursor", "Prompt-Engineering", "开源"]
description: "msitarzewski/agency-agents 是一个把 AI 角色定义做成可分发资产的仓库，它不训练模型，而是把每个 Agent 写成独立 Markdown 文件，配上 install.sh / convert.sh 即可一行命令装进 Claude Code、Cursor、Codex 等十余种工具。"
---

## 这个仓库在解决什么问题

多数团队在使用 Claude Code、Cursor、Codex 这一类「自带 Agent 能力」的 IDE/Coding Agent 时，会遇到一个非常现实的摩擦：你想让模型长期扮演某个专家角色，但每次开新会话都得在提示词里反复声明"你是前端工程师，请按某某规范出活"——这套人设既容易忘，也不利于团队复用。

`msitarzewski/agency-agents`（截至本文写作时已 11 万+ Star）选择的解法非常朴素：**把"角色定义"作为可版本化的资产**——一个 Agent 一个 Markdown 文件，每个文件里写清 Identity、Personality、Workflow、Deliverable、Success Metrics，写完丢到 `~/.claude/agents/`、`~/.cursor/rules/`、`~/.codex/AGENTS.md` 等目标位置，下次会话工具启动时就"自带这个人设"。再配上一个原生桌面客户端 App（macOS/Linux/Windows 都有），就能让非终端用户也享受同等待遇。

它不是框架、不是 SDK、也不是 prompt 自动生成器，本质上是一个**「人格化 Agent 提示词资产」的目录与分发机制**。

## 仓库结构与抽象层级

仓库根目录下按"部门（division）"组织角色，目前公开 16 个 division，覆盖工程、产品、设计、增长、安全、客服等。比较有代表性的目录：

| Division | 代表 Agent | 典型场景 |
|---------|-----------|---------|
| `engineering/` | Frontend Developer、Backend Architect、DevOps Engineer、Mobile Developer | 编码实施、架构评审、CI/CD |
| `security/` | Penetration Tester、Security Engineer | 红队演练、代码审计 |
| `marketing/` | Reddit Community Ninja、Twitter Engager | 增长投放、社区互动 |
| `product/` | Product Manager、UX Researcher | PRD、用户访谈 |
| `design/` | UI Designer、Brand Guardian | 视觉、UI 规范 |
| `qa/` | Senior QA、Reality Checker | 测试与"挑刺" |

每个 Agent 文件大致都遵循这套骨架：

```
# Role Identity
- 角色定位 / 人格特质 / 沟通风格
# Core Mission
- 核心目标 / 工作流 / 关键约束
# Technical Deliverables
- 输出物清单 + 代码片段示例
# Success Metrics
- 如何判断"这活儿做得行"
```

这种"长 Markdown 当 Agent"的写法与一些 DSL（如 DSPy、Guidance）路线相反——它把可读性、可审计性、可 fork 性放在第一位，不引入新的运行时。

## 安装与集成路径

README 给出了三种主流使用方式：

### 1. 安装原生 App（对非终端用户最友好）

仓库 `msitarzewski/agency-agents-app` 是一个独立的桌面客户端，浏览全部 Roster 后一键把 Agent 灌进 Claude Code、Cursor、Codex、Gemini CLI、OpenCode、Qwen、Osaurus 等工具，并自动升级。macOS 用户还可 `brew install --cask msitarzewski/agency-agents/agency-agents`。这是 README 推荐的"零门槛"路径。

### 2. 仅选择部分部门（脚本式）

仓库自带两个脚本：

```bash
./scripts/convert.sh        # 生成各工具的集成文件
./scripts/install.sh        # 交互式选择工具 + 团队
./scripts/install.sh --tool claude-code --division engineering,security
./scripts/install.sh --tool cursor --agent frontend-developer,ui-designer
./scripts/install.sh --list teams
./scripts/install.sh --tool opencode --division engineering --dry-run
```

支持的工具清单：Claude Code、Antigravity、Gemini CLI、OpenCode、GitHub Copilot、OpenClaw、Cursor、Aider、Windsurf、Kimi Code、Codex。换言之，它不绑定任何一家 Coding Agent，而是把它们视为"角色文件的下游消费者"。

### 3. 复制粘贴单文件（最低门槛）

如果只想先试一个，直接 `cp engineering/frontend-developer.md ~/.claude/agents/`，下次在 Claude Code 会话里说"切换到 Frontend Developer 模式"即可。

## 它和"自动 Agent 框架"的差异

很多人会把它和 LangChain Agents、AutoGen、CrewAI 这类框架混为一谈，但设计哲学其实完全不一样：

- **框架派**：提供执行引擎（tool calling、记忆、规划），让用户"组合" Agent 的能力边界；关心的是运行时。
- **Agency Agents 派**：不提供运行时，而是给模型"人设卡"，上下文窗口里多了这个 Markdown，模型就会按人设走；关心的是**上下文资产**。

因此它和框架完全不冲突——你完全可以把它的"角色 Markdown"作为 system prompt 第一段，下面接 LangGraph 的工作流；也可以直接让 Claude Code 裸读 `frontend-developer.md` 启动会话。

## 实用边界

值得用的场景：

- 团队希望统一"AI 在每个工程师手里的人设"，而不是每人各自调 prompt；
- 想要沉淀带"评审/测试/文案"等下游协作角色，而不只是单兵 coding agent；
- 想给非工程师同事（非 Cursor 老手）一个能点点选选就分发的客户端。

不适合的场景：

- 需要严格自动调度的多 Agent 协作（仍需 LangGraph/AutoGen 之类的运行时）；
- 角色语义需在代码层被引用与断言（它没有类型系统）；
- 与项目强耦合的代码规约（这部分更适合放 `AGENTS.md` / `conventions.md`，由各工具原生支持）。

## 小结

如果把"AI 角色"当成可以 diff、review、fork 的资产，而不是藏在某位员工的桌面配置里——`agency-agents` 给出了一个最低成本的实现：Markdown 写角色、一行命令装进工具、桌面 App 做分发。它做得不深，但覆盖面广，对希望快速在团队里跑通"角色化 Coding Workflow"的项目，是一个值得先试用再决定是否深度的入口。

## 链接

- 仓库：https://github.com/msitarzewski/agency-agents
- 桌面客户端：https://github.com/msitarzewski/agency-agents-app
- App 官网：https://agencyagents.app
- License：MIT
