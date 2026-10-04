---
title: "OpenRig：把 Claude Code 与 Codex 编成一支常驻团队的 tmux 编排器"
date: 2026-10-05T03:25:53+08:00
slug: "openrig-multi-agent-team-orchestration"
github_repo: "mvschwarz/openrig"
source_key: "gh:mvschwarz/openrig"
description: "OpenRig 是开源的多智能体编排系统，用 YAML 定义智能体团队拓扑，在 tmux 上把 Claude Code、Codex 等编程代理组织成有角色、有共享上下文的常驻团队。本文拆解其架构分层、核心概念与安全边界。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "多智能体", "tmux", "Claude Code"]
---

# OpenRig：把 Claude Code 与 Codex 编成一支常驻团队的 tmux 编排器

用 AI 编程代理干活的人，大多经历过同一个终局：屏幕上散落七八个终端窗口，每个跑着一个 Claude Code 或 Codex 会话，谁在做什么、上次聊到哪、重启后怎么恢复，全靠记忆和翻屏。OpenRig 对此有一句精准的口号——"A harness wraps a model. A rig wraps your harnesses."（一个 harness 包裹一个模型，一个 rig 包裹你的所有 harness）。

OpenRig 是一个开源（Apache 2.0）的多智能体编排系统，约 4.9 千 Star，TypeScript 编写。它不造新模型也不替代 Claude Code/Codex，而是把这些现成的编程代理**组织成一支常驻团队**：有角色分工、有稳定地址、有共享上下文、可快照恢复。

## 核心判断

OpenRig 解决的不是"怎么让单个代理更聪明"，而是**多代理系统的运维问题**：会话生命周期管理、拓扑定义、成员间通信、崩溃恢复、权限审计。这些问题在跑两个以上代理时必然出现，而在它之前，多数人的答案是用 tmux 手工硬撑。

## 系统地图

README 给出了清晰的四层架构：

```
CLI / TUI / MCP
      |
Hono HTTP daemon
      |
  Domain services
      |
SQLite + tmux + runtime adapters
```

- **CLI**：人与代理共用的命令面（启动团队、查状态、发消息、管上下文）。
- **TUI**：终端 UI，含拓扑表格/图视图、座位详情、Feed、系统面板。
- **MCP**：暴露 `rig_up`、`rig_ps`、`rig_send` 等工具，让代理自己管理拓扑——这是"agent-managed"理念的关键一环。
- **运行时适配层**：原生 Claude Code 与 Codex 会话、终端节点，以及经 RPC 接入的 Pi 运行时；全部承载于 tmux 会话之上，SQLite 持久化状态。

## 关键概念：从"会话"到"座位"

OpenRig 的概念体系值得单独拎出来，因为它体现了与传统"多开终端"的本质区别：

- **RigSpec**：YAML 声明式团队定义——pods（座位组）、edges（关系）、continuity policies（连续性策略）、culture file（协作规范）。
- **Seat（座位）**：团队里一个稳定的角色与地址，如 `dev-owner@first-project`。占据座位的对话可以换，但座位身份与沉淀的上下文保持——这是"常驻团队"的核心抽象。
- **Pod**：相关座位的分组，共享指导与上下文；但每个代理仍有独立上下文窗口。
- **Discover/Adopt**：给现有 tmux 会话做指纹识别并纳入管理——迁移现有工作流的入口。
- **Snapshot/Restore**：`rig down --snapshot` 捕获完整拓扑，`rig up <name>` 按名恢复，逐节点报告恢复结果。
- **Culture（CULTURE.md）**：为团队定协作规范——研究型团队给探索性文化，实现型团队给保守的 trust-but-verify 文化。

## 一次任务怎么流过系统

以官方入门路径为例（两座位：owner + checker）：

```bash
npm install -g @openrig/cli
rig setup --dry-run          # 预览机器级变更
cd /path/to/your/repository
rig up first-project --cwd . # 起 tmux 会话、座位、就绪检查
rig ps --nodes               # 确认座位就绪
rig send "dev-owner@first-project" 'Implement <one useful change>. ...'
```

你只对 owner 座位下达一个有边界的产出目标；owner 把任务记入队列、实现并验证，然后请同队的 checker 座位审查确切的候选变更，最后回报结果与验证方式。下次迭代回到同一个 owner——它的上下文还在原地址。这就是"团队"与"一堆终端"的差别。

## 安全边界：它到底改了你机器上的什么

这是 README 里写得最认真的部分，也应当是使用者最关心的部分。OpenRig 在安装与启动时会写**信任设置与可执行钩子**，涉及 `~/.tmux.conf`、`~/.claude.json`、`.claude/settings.local.json`、`~/.codex/config.toml` 等多处。要点：

- **YOLO 默认关闭**。Claude 以 `acceptEdits` 权限模式启动，Codex 默认 `workspace-write` 沙箱；完全旁路（`--dangerously-skip-permissions` / danger-full-access）需要显式选择，且每次经 `rig seat set-permissions` 留审计记录。
- **代理免重复授权是可选的**：首次会让代理问你"是否允许 agent 免确认执行 rig 命令"，答 No 则设置不变。
- **遥测内容有边界**：活动钩子只上报事件类型、座位身份、时间戳与原生会话标识，**不含提示词文本与工具参数**。
- 官方仍建议**首次使用前备份相关配置文件**——钩子块保留无关条目，但信任条目与部分配置可能被替换。

## 适用边界

- **平台限制**：仅 macOS/Linux + Node.js 22 或 24 + tmux；原生 Windows 不支持，WSL2 未测试。Apple Silicon 上官方建议 Node 22。
- **0.6.0 起 Node 20 不再支持**（SQLite 绑定 better-sqlite3 13 的要求）。
- **形态偏重**：守护进程 + SQLite + TUI 的完整系统，适合"长期驻扎的项目团队"场景；只想临时并行跑两个一次性任务的话，直接开两个终端更轻。
- 项目迭代快（已至 0.6.x），跨版本有专门的迁移技能与升级流程，跟进版本需读 release notes。

## 小结

多智能体协作的瓶颈正从"单代理能力"转向"团队工程"——生命周期、寻址、恢复、权限。OpenRig 用座位抽象、声明式拓扑与 tmux 底座给出了一套自托管的完整答案，其对安全边界的坦白程度（专设"What OpenRig changes on your machine"一节）在同类项目中相当少见。如果你已经在重度使用 Claude Code 与 Codex，值得拿一个真实仓库跑一遍 `first-project` 入门路径。

仓库：<https://github.com/mvschwarz/openrig>
