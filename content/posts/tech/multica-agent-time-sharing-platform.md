---
title: "Multica：用「时间共享」把 AI coding agent 从工具变成队友"
date: "2026-05-22T03:00:00+08:00"
slug: "multica-agent-time-sharing-platform"
description: "Multica 是一个开源的 agent 管理平台，通过把 AI coding agent 当作正式员工一样指派任务、跟踪进度、沉淀技能，实现多 agent 协同工作。核心创新是将 Unix 的时间共享模型重新带回 AI 时代，让小团队也能拥有大型开发团队的速度。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "多 agent 协作", "Coding Agent", "任务管理", "Go"]
---

## 开场判断

Multica 真正解决的不是「如何调用更好的模型」，而是：当团队里同时跑了五六个 coding agent 时，谁给它们分配任务、谁跟踪进度、谁在它们跑偏时知道、谁把某次成功的修复变成团队里所有 agent 都能复用的技能？

它的回答是把 agent 当正式员工上板，而不是当工具托管。你创建一个 issue，assign 给 `@alice`，但 `@alice` 可以是一个 Claude Code、Codex 或 OpenClaw 实例——它们会 pick up 任务、执行工作、在阻塞时主动 report。

这背后是一个有意思的思路：Multica 这个名字来自 Multics，1960 年代的多用户分时操作系统。Unix 的诞生就是简化 Multics——一个用户、一个任务、一个模型。Multica 认为历史在重复：多用户分时正在变成多 agent 分时，小团队配上一组合适的 agent，应该能跑出二十个人的速度。

## 系统地图

```
┌──────────────────────────────────────────────────────────────┐
│                         Multica Cloud / Self-hosted           │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────────┐  │
│  │  Next.js     │◄──►│  Go Backend  │◄──►│  PostgreSQL   │  │
│  │  Frontend    │    │  (Chi + WS)  │    │  (pgvector)   │  │
│  └──────────────┘    └──────┬───────┘    └────────────────┘  │
│                              │                                  │
│                    ┌─────────┴──────────┐                     │
│                    │    Agent Daemon     │  ← runs locally    │
│                    │  (Claude/Codex/Copilot│                   │
│                    │   OpenClaw/Gemini/… )│                    │
│                    └─────────────────────┘                     │
└──────────────────────────────────────────────────────────────┘
```

| 层 | 技术栈 |
|---|---|
| 前端 | Next.js 16（App Router） |
| 后端 | Go（Chi 路由 + gorilla/websocket） |
| 数据库 | PostgreSQL 17 + pgvector |
| Agent 运行时 | 本地 daemon，通过检测 PATH 上的 CLI 来注册 |

## 核心机制

### 1. Agent 作为第一类公民

在 Multica 里，每个 agent 有 profile、出现在看板上的卡片、能被 assign issue、能在 issue 下评论、能在阻塞时主动报告。这是和其他「agent 工具」最根本的区别——agent 不是被调用的对象，而是有自己身份、能动性、能负责任的工作单元。

当你在看板或 CLI 上 assign 一个 issue 给 agent，daemon 会在后台轮询 server，认领这个任务，在本地为它创建独立的 workspace 目录，然后启动对应的 agent CLI（比如 `claude` 或 `codex`）执行工作。全程结果通过 WebSocket streaming 回传，看板上能实时看到进度。

### 2. Squad：稳定的路由层

当团队 agent 数量增长，一对一 assign 的方式会变得难以维护——human 需要记住谁擅长什么、当前谁有空。

Squad 是解决这个问题的一个设计：把一组 agents 和 humans 组织在一个 leader agent 下，然后你把 issue assign 给 Squad，而不是单个 agent。leader 根据任务类型决定谁 pick it up。比如 `@FrontendTeam` 下面有负责 UI 的、有负责样式验证的，分配工作时 leader 会路由到最合适的成员。

这样 human 不需要记住 agent 的组合逻辑，只需要知道「这件事交给 @FrontendTeam」。路由稳定性由 leader 保证，不随成员增减而失效。

### 3. Reusable Skills：让成功可积累

当一个 agent 解决了某个问题（比如一次数据库迁移），这个解法可以沉淀为团队级别的 Skill，供其他 agent 在遇到类似任务时调用。Skills 是跨 session 的——不依赖某次具体的执行上下文，可以在不同 issue、不同 runtime 中被复用。

这让团队的学习曲线不是线性重复，而是有复利效应。每解决一次问题，团队整体能力往上走。

### 4. 统一 Runtimes：本地和云端一体管理

Multica 的 daemon 运行在本地机器上，auto-detect PATH 上的 agent CLIs（支持 Claude Code、Codex、GitHub Copilot CLI、OpenClaw、OpenCode、Hermes、Gemini、Pi、Cursor Agent、Kimi、Kiro CLI）。但它不限于本地——Cloud Runtimes 也纳入同一套 dashboard，跨本地和云端的 compute 资源统一可见。

## 任务流案例

一次典型的 agent 工作流程是这样的：

1. **Human 在看板创建 issue**：「重构 packages/auth 的错误处理」并 assign 给 `@backend-agent`
2. **daemon 检测到任务分配**，在 server 轮询中发现这个 claim，启动本地 Claude Code 实例
3. **Claude Code 在独立 workspace**（`~/multica_workspaces/<issue-id>/`）中执行任务，streaming 进度回 Multica
4. **若 agent 遇到阻塞**：它主动在 issue 下 comment 说明原因，而不是静默失败
5. **Human 通过看板看到进度**，必要时 comment 引导方向
6. **完成后 issue 状态更新**，这次重构中产生的数据库迁移脚本可以沉淀为 Skill

整个过程 human 不需要复制粘贴 prompt，不需要盯着 terminal 等结果，不需要事后手动同步进度——全部在 Multica 的看板和 comment 系统里完成。

## 技术架构的关键选择

### Go 后端 + PostgreSQL/pgvector

Go 的优势在于高并发、低内存占用，以及单二进制部署的便利性——daemon 和 server 都可以打包成独立二进制。PostgreSQL 17 内置 pgvector，agent 相关的向量语义搜索（比如从历史 issue 中找相似解法）不需要额外基础设施。

### 前端 monorepo（pnpm + Turborepo）

`apps/web`（Next.js）、`apps/desktop`（Electron）、`packages/core`（无 React 依赖的业务逻辑）、`packages/ui`（原子组件）、`packages/views`（跨平台的业务页面）——这种切分让核心业务逻辑可以脱离 React 环境复用。内部包（internal packages）模式意味着 shared packages 输出 raw TS/TSX 文件，不需要预编译，bundler 直接消费。

### 状态管理：QueryClient + Zustand 分离

所有 server state 走 TanStack Query，WS 事件通过 invalidation 保持缓存新鲜，不直接写入 store。Zustand 只管客户端状态（UI 选择、modal、draft）。这个分离保证了 workspace 切换时 cache key 自然变化，不需要手动 invalidation——换 workspace 就是换 key，干净利落。

### Workspace 隔离

每个 workspace 有独立的 agents、issues、settings。不同团队成员进不同的 workspace，本地 daemon 可以在不同 workspace 之间分发任务。多个 workspace 可以同时运行而不互相干扰。

## 适用边界

**Multica 适合：**
- 小团队（2~10 人）希望用 AI coding agent 承接重复任务
- 开发者日常使用多个 coding agent（Claude Code、Codex 等），想统一管理任务分配和进度
- 需要把每次成功的修复变成团队可复用技能的场景

**Multica 不适合：**
- 单 agent 场景——直接用 agent CLI 更轻量，不需要额外的管理层
- 超大型团队（几十人以上）需要复杂权限和流程控制——目前 Multica 的 ACL 模型相对简单
- 对 self-hosting 有严格要求但没有 Docker 基础设施的团队

## 快速上手

```bash
# macOS / Linux
brew install multica-ai/tap/multica

# Windows
irm https://raw.githubusercontent.com/multica-ai/multica/main/scripts/install.ps1 | iex

# 一键配置（登录 + 启动 daemon）
multica setup
```

在 web dashboard 的 **Settings → Agents** 创建第一个 agent，选择 runtime（本地 daemon 会自动检测 PATH 上的 CLI），然后在看板 assign issue 给这个 agent。

如果是自部署：

```bash
curl -fsSL https://raw.githubusercontent.com/multica-ai/multica/main/scripts/install.sh | bash -s -- --with-server
multica setup self-host
```

## 小结

Multica 最值得看的地方不是「又一个 agent 工具」，而是它把「agent as teammate」这个思路真正落地了：看板、issue assign、comment、blocker report——这些不是给 human 用的协作工具，也是 agent 的工作界面。从这个角度看，它的野心是一个开源的 AI-native 团队协作基础设施，而不是一个单纯的 agent 调度器。

名字确实起得有意思：Multics 引出了 Unix，Unix 引出了 Linux，Linux 引出了云原生，云原生现在重新在 AI 时代遇到了多 agent 分时的老问题。Multica 能不能接住这一棒，取决于它能不能在复杂团队场景下证明 Squad 路由的稳定性，以及 Skills 的积累速度够不够快。

数据：30.6k Stars（2026-05），Go + TypeScript，主仓库最近更新 2026-05-21。