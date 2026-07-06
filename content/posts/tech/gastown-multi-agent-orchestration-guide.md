---
title: "Gas Town：把 4–10 个 Claude Code 实例变成 20–30 个协同 agent 的工作空间管理器原理拆解"
date: "2026-07-07T03:00:02+08:00"
slug: "gastown-multi-agent-orchestration-guide"
description: "Gas Town（gastownhall/gastown，16.6k stars / MIT，Go）是一个面向 Claude Code、Copilot、Codex、Gemini 等 AI 编程代理的多 agent 工作空间管理器：用 git-backed Hooks 持久化 agent 状态、用 Beads ledger 持久化 work item、用 Mayor+Rig+Polecat 三层抽象管理 20–30 个并行 agent。本文拆解其架构、角色分工与上下文保留机制。"
draft: false
categories: ["技术笔记"]
tags: ["Multi-Agent", "AI Agent", "Claude Code", "Git Worktree", "Go"]
---

# Gas Town：让 Claude Code 真正能并行协作

AI 编程代理 2025–2026 的最大使用痛点是什么？不是单个 agent 不够强，而是**多个 agent 一起跑会崩**——它们之间没有共享状态、没有清晰的职责划分、没有持久化层、上下文全在内存里。Gas Town（gastownhall/gastown，16.6k stars / MIT，Go）就是为这个痛点设计的工作空间管理器：把 4–10 个 Claude Code 实例扩展到**稳定 20–30 个协同 agent**，每个 agent 有自己的"邮箱"和"工单"，重启不丢上下文。本文做原理拆解。

## 它要解决的具体问题

| 挑战 | Gas Town 的解决方案 |
|------|---------------------|
| Agent 重启就丢上下文 | 用 git-backed Hooks 持久化 work state |
| Agent 之间协调混乱 | 内置 mailbox / identity / handoff 协议 |
| 4–10 个 agent 已经混乱 | 设计上能 scale 到 20–30 个 |
| Work state 存在 agent memory 里 | 移到 Beads ledger（git 仓库里） |

## 系统地图：三层抽象 + 一种持久化层

Gas Town 的世界分四层实体：

```
┌─────────────────────────────────────────────────┐
│ Town  ~/gt/   工作空间根目录                     │
├─────────────────────────────────────────────────┤
│  ├── Mayor 🎩   主协调 AI（单个 Claude Code）    │
│  ├── Rig A (Project A)                          │
│  │    ├── Crew 👤   你的个人 workspace           │
│  │    ├── Polecats 🦨   worker agent（并行跑）   │
│  │    └── Hooks 🪝   git-backed 持久化层        │
│  └── Rig B (Project B)                          │
└─────────────────────────────────────────────────┘
                │
                ▼
        Beads ledger (git worktree)
        work item / status / handoff 全部存这里
```

### Town：工作空间根

`~/gt/` 目录，装着所有项目（每个项目一个 Rig）、全局配置、Mayor 的上下文。

### Rig：一个项目的容器

对应一个真实的代码仓库。Rig 内部有：

- **Crew Member** 👤：你自己用的 workspace，绑定到 IDE。你写的代码、提的 PR 都在这里。
- **Polecats** 🦨：worker agent，每个 Polecat 是一个独立的 Claude Code / Codex / Gemini 实例，**有自己的 git worktree**——所以它们不会相互覆盖对方的改动。
- **Hooks** 🪝：git-backed 的持久化层，存 agent 之间的消息、handoff、work item。

### Mayor 🎩：唯一的协调 AI

只有一个 Mayor，就是你的主 Claude Code 实例。它"看到"整个 Town，知道每个 Rig 有什么 Polecat 在跑、什么工单 pending、什么被阻塞。你跟 Mayor 对话："Rig A 的 #123 工单卡住了，看看 Polecat 4 是不是被限流了"，Mayor 会去查 Beads ledger + 当前进程状态，给你一个判断。

### Beads ledger 📿：持久化层

**关键设计**：所有 work item / agent state / handoff 都不存在 agent 内存里，存在 git 仓库（Beads ledger）里。这意味着：

- agent 崩溃可以重启，从 ledger 恢复 work item
- 你 `git log` 可以看到所有 agent 的工作历史
- agent 之间通过 ledger 的 entry 通信（不是 RPC）
- 离线操作可恢复

这是 Gas Town 和市面其他多 agent 框架（LangGraph、CrewAI、AutoGen）的核心区别——**那些框架的状态在内存或 DB 里，agent 重启 = 丢上下文**；Gas Town 把状态做成 first-class git 资产。

## 角色分工：Mayor / Crew / Polecat / Hook

| 角色 | 数量 | 职责 | 上下文 |
|------|------|------|--------|
| Mayor | 1 | 协调、监控、决策 | 全 Town |
| Crew | 1 per Rig | 你的个人 workspace | 单 Rig |
| Polecat | N per Rig | 跑工单、写代码 | 单 work item + Rig 上下文 |
| Hook | 1 per Rig | 持久化、消息路由 | 全 Rig 历史 |

**典型工作流**：

1. 你跟 Mayor 说："把 Rig A 的 issue #456 修了，要 unit test 通过"。
2. Mayor 看 Beads ledger 看 Polecat 哪个空闲，分配一个 Polecat 跑这个工单。
3. Polecat 从 ledger 读工单详情 → 在自己的 git worktree 写代码 → 跑 test → 改完把状态写回 ledger → handoff 给下一个工单或汇报给 Mayor。
4. 全程你不用盯着。如果 Polecat 跑 30 分钟没动静，Mayor 会主动 ping 它。

## 关键设计取舍

### 为什么是 git 而不是 SQLite / Redis

README 里写得很直白：git 提供的事务性、版本历史、可 diff 能力是 SQLite / Redis 给不了的。Agent 之间的消息如果存在 Redis 里崩了就真没了；存在 git 里你可以 `git log --grep "Polecat-3"` 看某个 agent 历史上做了啥。这对 debugging 极其友好。

代价是 git 操作比 Redis 慢几个数量级，但 agent 工作是分钟级 / 小时级，不是毫秒级，git 的延迟可接受。

### 为什么是 git worktree 而不是 docker container

每个 Polecat 是一个独立 git worktree（不是独立 docker container / VM）。worktree 共享同一个 `.git/` 目录但 working tree 独立，所以：

- 创建 Polecat 是 `git worktree add`，毫秒级
- 不同 Polecat 改同一个文件不会冲突（worktree 物理隔离）
- 你 `git diff main..polecat-3` 能直接看某个 Polecat 的全部改动
- 不需要任何 container runtime

代价是 Polecat 不能装不同的 OS 依赖。但 Claude Code / Codex 这类纯文本 agent 不需要 OS 隔离，worktree 足够。

### 为什么 Polecat 不共享 memory

Polecat 之间不直接通信，所有沟通通过 Beads ledger。这避免了两个常见 bug：

1. **状态不一致**：agent A 在内存里改了状态，agent B 不知道。
2. **回不去的状态**：agent A 的内存是 transient，重启就丢。

把状态全推到 ledger → agent 都是 stateless 的执行单元 → 重启永远 OK。

## 适用边界

**适合**：

- 你已经在重度使用 Claude Code / Cursor / Codex，每天跑 10+ 个 session
- 你在做"大量独立 issue / 大量独立 fix / 大量独立 PR"的并行开发
- 你想用 git log 审计 agent 行为
- 你接受"agent 是 stateless worker"的设定

**不适合**：

- 你只有 1–2 个 agent 在跑（overhead 比收益大）
- 你的 agent 之间需要紧密实时通信（ledger 不适合毫秒级 sync）
- 你的 agent 需要强 OS 隔离（worktree 不隔离环境）
- 你想做 to C 的 multi-agent 产品（Gas Town 是开发工具，不是产品框架）

## 与同类工具的差异

| 工具 | 定位 | 持久化层 | 适合规模 |
|------|------|----------|----------|
| **Gas Town** | 工作空间管理器 | git (Beads ledger) | 20–30 agent |
| **LangGraph** | Agent 框架 | 内存 / DB | 1–10 agent |
| **CrewAI** | Agent 框架 | 内存 | 1–5 agent |
| **AutoGen** | Agent 框架 | 内存 | 1–5 agent |
| **MetaGPT** | Agent 框架 | 文件 + git | 1–10 agent |

Gas Town 的位置是**多 agent 工作空间**而不是**agent 框架**——它不帮你写 agent 的 prompt、不帮你定义 tool、不帮你接 LLM API，它只管"agent 在哪个目录跑 / 跑完之后状态写哪 / 怎么分配 work item"。如果你要的是 prompt 编排能力，去用 LangGraph；你要的是规模化并发执行 + 状态可审计，来 Gas Town。

## 快速上手

```bash
# 安装
go install github.com/gastownhall/gastown/cmd/gt@latest

# 初始化 Town
gt init ~/gt

# 添加一个 Rig（指向你已有的 git 仓库）
gt rig add ~/gt/myproject ~/code/myproject

# 启动 Mayor
gt mayor start

# 现在可以在 Claude Code 里跟 Mayor 对话了
```

详细教程看 [Gas Town README](https://github.com/gastownhall/gastown)。

## 仓库地址

- 仓库：`gastownhall/gastown`
- 协议：MIT
- 主语言：Go（CLI + Hooks daemon）
- stars：16.6k / forks 1.5k
- 默认分支：main
- 最近更新：持续活跃（README 写"Pushed at 2026-07-06"）

如果你的现状是"Claude Code session 跑多了自己也搞不清哪个在干嘛"，Gas Town 是当前 GitHub 上唯一把这个问题当作头等公民来解的项目——其他 multi-agent 框架还在纠结 prompt 编排，它已经在管"20 个 agent 的工作流"了。