---
title: "firstmate：一个 agent distro 如何让你只跟一个 AI 对话，却指挥一支开发舰队"
date: 2026-08-13T03:23:44+08:00
slug: "firstmate-agent-crew-distro"
github_repo: "kunchenguid/firstmate"
source_key: "gh:kunchenguid/firstmate"
description: "firstmate 不是框架、不是 CLI、不是 MCP 服务器，而是一套 agent distro——通过 AGENTS.md 指令集、tmux 会话后端和 git worktree 隔离，让你只跟一个「大副」对话，它自动派遣多条并行 agent 分别在独立 worktree 中完成任务，交回 PR 或调研报告。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "多智能体协作", "Git Worktree", "tmux", "Coding Agent"]
---

# firstmate：一个 agent distro 如何让你只跟一个 AI 对话，却指挥一支开发舰队

> **阅读时间**：约 16 分钟
>
> **适用读者**：Coding Agent 重度用户、多 repo 并行开发困局中的人、对 agent 编排模式好奇的工程师
>
> **前置知识**：用过至少一种 coding agent（Claude Code / Codex / Cursor 等），了解 tmux 基本概念和 git worktree

## 核心判断

当一个 coding agent 已经能独立完成"改代码→跑测试→提交 PR"的全流程时，瓶颈不再是单 agent 的能力，而是**人类同时管理多个 agent 会话的上下文切换成本**。

firstmate 的解法不是再做一个 agent 框架，而是定义一种叫 **agent distro**（agent 发行版）的东西：一个可移植的指令集目录，把通用 coding agent 变成专门化的大副（first mate），由它替你调度一整支 crew（船员队列），每名船员在独立的 tmux 窗口和 git worktree 中干活，互不干扰。

你的角色从"tab 切换员"变成"船长"：只跟大副说目标，大副负责分拆任务、派遣船员、监督进度、汇总交付。

## 系统地图

```
            你（船长）
                │  聊天：提需求、做决策、"merge it"
                ▼
 ┌─────────────────────────────────────┐
 │ firstmate（大副）    (本仓库)        │
 │ 读取 projects/ + firstmate 路由规则   │
 │ 写入受保护的 backlog/briefs/state     │
 └──┬──────────────┬───────────────┬───┘
    │ 后端发送 / 状态文件               │
    ▼              ▼               ▼
 ┌────────┐   ┌────────┐      ┌────────┐
 │fm-task1│   │fm-task2│  ... │fm-taskN│  tmux 窗口 / herdr/zellij 标签
 │船员     │   │船员     │      │船员     │  每个窗口一个自治 agent
 └───┬────┘   └───┬────┘      └───┬────┘
     ▼            ▼               ▼
  treehouse worktree（每个任务独享）
     │
     ├─ ship 任务 → 项目模式 ► PR / 本地合并 ► 清理
     │
     └─ scout 任务 → 调研报告 ► 决策清单 ► 转达发现 ► 清理
```

核心组件及其职责：

| 组件 | 职责 | 关键设计 |
|------|------|----------|
| **大副（first mate）** | 唯一对话入口，拆解需求、派遣船员、监督进度 | 读 `AGENTS.md` 指令集驱动，不是独立程序 |
| **船员（crewmate）** | 在独立会话端点中执行单个任务 | 每个船员有自己的 tmux 窗口 + git worktree |
| **treehouse worktree** | 为每个任务创建干净的 git 工作树 | 基于 [treehouse](https://github.com/kunchenguid/treehouse)，隔离并行工作 |
| **监督引擎（supervisor）** | 零 token 事件驱动看护 | bash watcher 休眠在舰队上，仅在需要时唤醒大副 |
| **secondmate（可选）** | 持久化副官，可部署在本地或远程 SSH 主机 | 独立 `FM_HOME`、独立状态、独立会话锁 |

## 它到底是什么：agent distro

firstmate 反复强调自己"不是模型、不是 harness、不是 skill、不是 MCP 服务器、不是 CLI"。它是一份 **agent distro**——一个可移植的目录，包含：

- `AGENTS.md`——always-loaded 操作契约和路由索引
- `.agents/skills/`——agent 加载的内置技能（`/afk`、`/ahoy`、`/bearings` 等）
- `.claude/`、`.grok/`、`.pi/`、`.codex/`、`.opencode/`——各 harness 的项目级配置
- `bin/`——helper 脚本工具带
- `skills/`——面向公开安装的独立技能（如 `skills/stow`）

"安装"就是 `git clone` + 在目录内启动一个已认证的 coding agent。agent 读到 `AGENTS.md` 后自动进入大副角色——不需要额外 app、不需要 daemon、不需要 API key。

这个设计意味着 firstmate 本身零运行时成本：它是一组指令和约定，靠 agent 的服从性来执行。

## 两种任务形态：ship 与 scout

firstmate 把所有工作分为两类，走不同的交付路径：

### ship 任务——交付代码变更

ship 任务的目标是产生授权的代码修改。每名船员在独立 worktree 中完成开发后，按项目模式交付：

- **`no-mistakes` 模式**：通过 [no-mistakes](https://github.com/kunchenguid/no-mistakes)（同作者的 git 评审闸门）跑 review → test → docs → lint → PR → CI 全流程 AI 检查，全部通过后才推到 remote。这是默认的项目模式。
- **`direct-PR` 模式**：直接创建 PR，不经过 no-mistakes 闸门。
- **`local-only` 模式**：变更只在本地 worktree 完成，不推送远端。

三种模式都可叠加 `+yolo` 自治标志，允许船员在更少人工确认下推进。

### scout 任务——交付调研报告

当请求更像"调查一下"而非"修好它"时，大副会派出 scout 船员。scout 不修改代码，而是在 `data/<id>/report.md` 产出独立调研报告，再由大副汇入决策清单转达给你。

这个分离很关键：避免让一个 agent 同时"调查"和"修改"，降低不可控变更的风险。

## 并行隔离：treehouse worktree

firstmate 的并行能力建立在 git worktree 之上。每个任务通过 [treehouse](https://github.com/kunchenguid/treehouse) 获得一个干净的 worktree——不是 `git worktree add` 的裸调用，而是封装了分支命名、清理、冲突检测的工作流。

隔离效果：

- 三名船员可以同时对同一个 repo 的不同分支工作
- 一名船员的依赖安装不影响其他船员的 worktree
- 任务完成后 worktree 被清理，不留下残留分支

这解决了一个真实的痛点：当你想让 agent 同时修 bug、写新功能、做代码审计时，如果不隔离工作目录，三条改动会互相覆盖。

## 零 token 监督引擎

这是 firstmate 在工程上最有趣的设计。

传统多 agent 编排往往需要一个"调度 agent"持续轮询各子 agent 的状态，这本身会消耗大量 token。firstmate 用了一个完全不同的方案：

1. 一个 **bash watcher**（纯 shell 脚本）休眠在 tmux 会话上
2. 它监控船员的状态文件变化（不是 agent 输出）
3. 只在有事件需要船长决策时，才唤醒大副（coding agent）

"零 token"的含义是：监督本身不经过 LLM 推理，纯靠 shell 完成。大副只在"需要你拍板"或"船员完成/失败"时才被激活。

对于已验证的主线 harness（Claude Code、Grok、Pi），还有 **turn-end backstop**：如果大辅在工作进行中突然停止响应（比如 context window 溢出导致静默退出），backstop 会拦截这种"盲停"，要么阻止退出，要么触发后续补救。

## 会话后端选择

firstmate 支持五种会话后端，tmux 是参考默认：

| 后端 | 状态 | 特点 |
|------|------|------|
| **tmux** | 参考实现 | 最稳定，watcher 和 turn-end guard 支持最完整 |
| **herdr** | 实验性 | 自动检测或手动选择 |
| **zellij** | 实验性 | 需显式选择 |
| **Orca** | 实验性 | 独立终端应用，支持 Orca-managed worktree |
| **cmux** | 实验性 | 基于套接字的工作区 |

选 tmux 不是因为它最新潮，而是因为它最稳定、生态最广。这个选择体现了务实的工程判断：在编排多 agent 这种复杂度已经很高的场景下，会话后端应该是"无聊但可靠"的基础设施。

## 内置技能

firstmate 自带几个有用的 slash command：

| 技能 | 用途 |
|------|------|
| `/afk` | 进入离岗监督模式：自动处理例行通知，只把需要你决策的事打包成摘要 |
| `/ahoy` | 回顾上次你离开后的会话事件，引导你处理待决策项 |
| `/bearings` | 生成四段式状态摘要（可写文件 + 可含 PR 实时状态） |
| `/updatefirstmate` | 自更新大辅和所有 secondmate 到最新版本 |
| `/stow` | 扫描会话中未捕获的持久知识，分层归档（热/温/冷） |

这些技能在 Claude Code 和 Grok 中用 `/` 触发，在 Codex 中用 `$` 触发。

## 与 no-mistakes 的关系

如果你读过 [no-mistakes 的文章](https://txtmix.com/posts/tech/kunchenguid-no-mistakes-git-ai-gate/)，会发现两者出自同一作者（kunchenguid），且 firstmate 默认使用 no-mistakes 作为 ship 任务的项目模式。它们的关系是：

- **no-mistakes**：git push 前的 AI 评审闸门，解决"AI 生成的代码质量怎么保证"
- **firstmate**：多 agent 编排层，解决"怎么让多个 agent 并行工作而不乱套"

两者可独立使用，但组合使用时形成完整链路：firstmate 派遣 → 船员开发 → no-mistakes 评审 → 合格后交付。

## 安装与快速上手

```sh
gh auth login
git clone https://github.com/kunchenguid/firstmate
cd firstmate
```

然后启动一个受支持的 harness：

```sh
# Claude Code（推荐）
claude

# Grok（推荐）
grok --trust

# Pi（推荐）
pi
```

首次启动时，大副会检测工具链，征求你同意后安装缺失依赖。然后你可以直接提需求：

```sh
> ahoy! 看一下我的 github 项目 xyz，修复 flaky login test 并加个暗色模式

# firstmate 检查工具链 → 克隆项目到 projects/ → 在后端中派出两名隔离船员
# 几分钟后：

  PR ready for review, captain: https://github.com/you/xyz/pull/42
  (fix flaky login test - risk: low - CI green)

> alright merge it
```

## 适用边界

firstmate 不是万能的。以下场景它不擅长：

- **单任务场景**：如果你只跑一个 agent 做一件事，firstmate 是过度设计，直接用 coding agent 更高效
- **需要精细控制每步操作**：firstmate 的核心卖点是"你只说目标，大辅自己想办法"，如果你要逐步控制执行细节，它的抽象层反而碍事
- **非 git 项目**：worktree 隔离依赖 git，没有版本管理的项目无法使用并行隔离
- **Windows 环境**：当前仅支持 macOS 和 Linux

## 设计取舍观察

firstmate 做了几个有趣的设计取舍：

**指令优先于代码。** 它不是一个可执行程序，而是一组 agent 遵循的指令。好处是极度可移植——任何能读 `AGENTS.md` 的 agent 都能当大辅。代价是依赖 agent 的指令服从质量。

**tmux 优先于自建调度。** 没有自己造一个 session manager，而是用 tmux 的窗口/标签做隔离层。减少了自己的代码量，但依赖 tmux（或替代品）的稳定性。

**事件驱动优先于轮询。** 监督用 bash watcher 而非 LLM 推理，省了 token 但限制了监督逻辑的复杂度——复杂判断仍需唤醒大副。

**ship/scout 二分法。** 把"调查"和"修改"强制拆成两种任务类型，简化了单任务的复杂度，但也意味着跨类型的复合任务需要人工拆解。

这些取舍反映了一个清晰的判断：**在 agent 编排这件事上，最大的风险不是性能不够，而是不可控**。firstmate 的每个设计都在降低"agent 在你看不见的地方做了你不想让它做的事"的概率。
