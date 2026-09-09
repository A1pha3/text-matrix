---
title: "Superpowers：让Coding Agent拥有完整开发方法论的插件系统"
date: "2026-05-20T15:52:00+08:00"
slug: "superpowers-coding-agent-development-methodology"
github_repo: "obra/superpowers"
source_key: "gh:obra/superpowers"
description: "Superpowers 是一套软件开发方法论 + 插件系统，为 Claude Code、Codex、Cursor 等 14 种 Coding Agent 注入结构化开发流程。它由 7 步基本工作流与 14 个可自动触发的技能组成，让 Agent 在写代码前先理解需求、拆解任务、写出可验证的测试，实现数小时自主工作不断线。"
draft: false
categories: ["技术笔记"]
tags: ["AI Coding Agent", "Superpowers", "TDD", "Claude Code"]
---

# Superpowers：让 Coding Agent 拥有完整开发方法论的插件系统

Superpowers 解决的不是"让 Agent 多写一点"，而是"让 Agent 在写代码之前先停下来"。它把一套完整的工程纪律——先问需求、再出设计、拆小步、每步验证、做完审查——编译进 Agent 的决策链：技能自动触发，不满足条件就卡住，Agent 无法跳过。Claude Code、Codex、Cursor 等 14 种 harness 都能挂上它。

2025 年 10 月 9 日，Anthropic 发布 Claude Code 插件系统；同一天，Jesse Vincent 发布 Superpowers 第一个版本。到 2026 年 9 月，这个仓库已有约 28.3 万 star（GitHub API，2026-09-08 时点），是 Claude Code 生态中安装量居前的第三方项目。

## 它解决什么问题：为什么直接写代码是错的

大多数 Coding Agent 的行为模式极其简单：收到指令 → 开始写代码。一个没有约束的 Agent 会同时暴露三个问题。

**意图偏差。** 你说「帮我做一个用户认证系统」，Agent 的理解和你想要的可能完全不同，但它不会停下来确认——它已经在写了。等你发现方向不对时，Agent 已经写了上千行代码。

**零测试防护。** 每写一个功能，Agent 不会验证它是否破坏了已有功能。你今天修了一个 Bug，明天它可能被另一个修改覆盖。没有测试的 Agent 开发就像在沙滩上建房子——看起来很高效，但一个浪过来就全没了。

**架构漂移。** Agent 没有「设计」概念。它只是在当前文件的上下文中做出局部最优选择。但局部最优的叠加往往等于全局灾难——这是组合优化中众所周知的事实，在 Agent 编程中同样成立。

Claude、GPT-5 在代码生成上的能力已经足够强，问题在于 Agent 缺少工程纪律——动手之前先停下来想一想。写一条提示词让 Agent「永远先写测试」——它会点头，然后继续直接写生产代码。需要一个在系统层面强制执行流程的机制。

Superpowers 的做法，是把流程写成一组技能文件，塞进 Agent 的启动指令里，让它在每次决策前自动检查「当前任务命中了哪个技能」。

## 系统地图：7 步基本工作流

README 把这套流程定义为 7 个前后衔接的步骤。每个步骤都是一个技能，由 Agent 在任务开始前自动检测并触发——不是建议，是强制规程。

| 步骤 | 技能 | 何时激活 | 做什么 |
|------|------|---------|--------|
| 1 | **brainstorming** | 写代码之前 | 通过提问收敛想法、探索备选方案，把设计分段呈现给你确认，保存设计文档 |
| 2 | **using-git-worktrees** | 设计批准之后 | 在新分支上创建隔离工作区，运行项目初始化，验证干净的测试基线 |
| 3 | **writing-plans** | 持有已批准设计 | 把工作拆成 2-5 分钟一个的任务，每个任务带精确文件路径、完整代码、验证步骤 |
| 4 | **subagent-driven-development** 或 **executing-plans** | 持有计划 | 每个任务派一个新的子代理独立实现，做两阶段审查；或批量执行并在人工检查点停下 |
| 5 | **test-driven-development** | 实现期间 | 强制 RED-GREEN-REFACTOR 循环，先写失败测试；先写了生产代码就删掉重来 |
| 6 | **requesting-code-review** | 任务之间 | 对照计划审查，按严重程度报告问题，关键问题阻塞流程 |
| 7 | **finishing-a-development-branch** | 任务全部完成 | 验证测试，给出合并 / PR / 保留 / 丢弃选项，清理 worktree |

第 4 步是两个可切换的执行模式：`subagent-driven-development` 追求最快的独立迭代，`executing-plans` 在批量执行中插入人工检查点，适合需要人盯的改动。

RED-GREEN-REFACTOR 是 TDD 的标准循环：先写一个会失败的测试（红），写最小代码让它通过（绿），再在测试保护下重构。Superpowers 把「红 → 绿」的先后顺序设为硬约束。

## 技能库：14 个技能，四类分工

7 步工作流是主线，仓库实际维护着 14 个技能文件，按用途分四类：

| 分类 | 技能 | 职责 |
|------|------|------|
| 测试 | `test-driven-development` | RED-GREEN-REFACTOR 循环，附带测试反模式参考 |
| 调试 | `systematic-debugging` | 四阶段根因排查，内置根因追踪、纵深防御、条件等待等技巧 |
| 调试 | `verification-before-completion` | 确认问题真的修好了，而不是看起来修好了 |
| 协作 | `brainstorming` | 苏格拉底式设计收敛 |
| 协作 | `writing-plans` / `executing-plans` | 计划编写与批量执行 |
| 协作 | `dispatching-parallel-agents` | 并发子代理工作流 |
| 协作 | `requesting-code-review` / `receiving-code-review` | 审查前检查清单 / 回应审查反馈 |
| 协作 | `using-git-worktrees` / `finishing-a-development-branch` | 并行分支与收尾 |
| 协作 | `subagent-driven-development` | 两阶段审查的快速迭代 |
| 元 | `writing-skills` | 教你按最佳实践写新技能（含测试方法论） |
| 元 | `using-superpowers` | 技能系统的使用入门 |

这套分类本身就是设计决策：调试与测试被拆成独立技能，是因为它们各自有完整的子流程，混进主工作流里容易被跳过。`writing-skills` 的存在则让这套系统可以自我扩展——你想给 Agent 加新技能时，先读它怎么写。

## 为什么这套流程有效

人类开发者能在复杂项目中保持方向感，靠的不是智商，而是内化的工程纪律：先理解需求，再设计方案，拆成小步，每步验证，持续重构。

AI Coding Agent 没有这种肌肉记忆。它接收到指令后的行为模式是直接响应——这是对话模型的设计特性，不是 bug。Superpowers 在 Agent 的决策链路上安装了一个「工程纪律层」，在每次代码生成之前强制插入检查点。

三个机制让这个纪律层真正生效：

**技能自动触发。** 不用你手动喊「先做个计划」。Agent 每次开工前检查当前任务命中了哪个技能，命中就执行，不命中就继续。README 的原话是「Agent 在任何任务前检查相关技能。强制工作流，不是建议。」

**上下文隔离。** 每个子代理任务都在独立的对话上下文中完成，主会话不被拖长。这是 Claude Code 这类工具的天然短板——对话越长，Agent 越跑越偏——Superpowers 用「每个任务一个新的子代理」绕开了它。

**验证前置。** 测试基线在动工前就被确认，任何新增的失败都可以追溯到当前改动；TDD 循环把「验证」嵌进每个任务的收尾，而不是最后补一次。

约束在正确的流程里，Claude Code 就能自主工作数小时而不偏离方向。这不是因为 Agent 变聪明了，而是因为系统让它做了正确的事。

## 一次任务如何流过系统

下面用一次示意性的改动把 7 步串起来——给博客的文章详情页加「阅读时间估算」。这是一个演示路径，用来展示抽象机制如何配合，不代表官方示例。

**第 1 步：brainstorming。** 你告诉 Claude Code：「给文章详情页加上阅读时间显示。」Agent 没有直接写代码，而是先提问：这个估算按什么口径算（纯文本字数还是含代码块）？放页面上哪个位置？有没有现成的排版约定？你逐段确认后，设计文档保存下来，进入下一步。

**第 2 步：using-git-worktrees。** Agent 在 `feature/reading-time` 分支上建一个隔离的 worktree，跑一遍项目初始化，确认测试基线全绿。这一步的价值在后面才显出来：任何新增的测试失败，都能确定是你这次改动引入的。

**第 3 步：writing-plans。** 设计被拆成 3-4 个 2-5 分钟的小任务，每个任务写清楚改哪个文件、改成什么样、怎么验证。你批准计划，Agent 进入执行。

**第 4 步：subagent-driven-development。** 每个小任务派一个新的子代理去实现。子代理写完跑测试，然后审查代理按计划核对：规格审查（有没有多写少写）和代码质量审查（风格、性能、安全）各一轮。两轮都过，结果回到主线，继续下一个任务。

**第 5-6 步：TDD 与 code review。** 子代理先写失败测试，再写最小实现让它通过。任务之间，requesting-code-review 技能对照计划审查已有改动，按严重程度分级——关键问题当场阻塞，小问题记录在案。

**第 7 步：finishing-a-development-branch。** 全部任务完成后，Agent 跑完整测试套件，给你合并 / PR / 保留 / 丢弃四个选项，然后清理 worktree。

整条链路里你只做了两件事：回答 brainstorming 阶段的问题，批准实施计划。

## 安装

Claude Code 的官方插件市场直接收录了 Superpowers：

```
/plugin install superpowers@claude-plugins-official
```

也可以用 Superpowers 自己的市场：

```
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

其余 harness 的安装方式各不同，README 逐一给了命令。常用的几个：

| Agent | 安装方式 |
|-------|---------|
| Claude Code | 官方市场 `/plugin install superpowers@claude-plugins-official` |
| Codex CLI | `/plugins` 搜索 `superpowers` 安装 |
| Cursor | Agent 聊天里 `/add-plugin superpowers` |
| Gemini CLI | `gemini extensions install https://github.com/obra/superpowers` |
| Pi | `pi install git:github.com/obra/superpowers` |
| GitHub Copilot CLI | `copilot plugin marketplace add obra/superpowers-marketplace` 后安装 |

其余（Antigravity、Codex App、Devin CLI、Factory Droid、Grok Build CLI、Kimi Code、OpenCode、Hermes Agent）的安装命令见仓库 README。注意 README 的提醒：同时用多个 harness 时，需要分别安装。

## 适用边界

**改造收益最大的场景：**
- 持续时间超过 30 分钟、涉及多个文件修改的复杂任务
- 有明确验收标准的功能开发
- 需要测试覆盖率的项目（库、API、后端服务）

**用 Superpowers 反而浪费时间的场景：**
- 30 秒内能完成的单文件修改（改变量名、修一个 typo）
- 纯探索性任务——你还不确定要做什么，需要边试边看
- 一次性脚本或临时工具

**一个判断标准：** 如果你在开始一个任务之前，自己会先花 5 分钟做设计——那这个任务就应该用 Superpowers。

## 自检测试

安装 Superpowers 后，用以下检查项验证它是否正常工作：

**检查 1：Agent 是否在写代码前先提问？** 提出一个模糊的需求，比如「帮我加个功能」。正常工作的 Superpowers 会让 Agent 进入 brainstorming 模式，开始提问而不是直接写代码。

**检查 2：是否创建了 Git worktree？** 批准设计后，检查你的 Git 仓库是否有新的 worktree 被创建（`git worktree list`）。

**检查 3：子 Agent 是否先写测试再写代码？** 观察 Agent 的输出。如果它先写生产代码再写测试，说明 TDD 技能没有正确执行。

## 进阶路径

### 第一阶段：跑通基础流程（1-2 天）

- 安装 Superpowers 插件
- 用一个真实但不大的任务（比如「给博客加阅读时间估算」）完整走一遍 7 步工作流
- 观察 brainstorming 阶段 Agent 提问的质量，学会如何在提问阶段把需求说清楚
- 验证 Git worktree 是否正确创建，子 Agent 是否先写测试

### 第二阶段：深度配置（3-5 天）

- 阅读 Superpowers 的技能文件（`skills/` 目录），理解每个技能的触发条件和执行逻辑
- 针对你的项目特点调整技能参数（比如 TDD 严格程度、review 阈值）
- 在一个有多人协作的项目里试用，观察 Superpowers 是否能帮助统一代码风格和减少回归
- 对比使用 Superpowers 前后的代码质量差异（测试覆盖率、PR 大小、review 轮次）

### 第三阶段：与团队工作流集成（1-2 周）

- 把 Superpowers 的流程写入团队的 AI Coding 规范文档
- 配置 CI/CD 检查，确保 Agent 生成的代码通过了所有测试才允许合并
- 收集团队反馈，找出 Superpowers 流程中的痛点
- 根据团队反馈调整配置，或者考虑换更定制化的工程环境

### 第四阶段：深入原理与贡献（2-4 周）

- 阅读 `writing-skills` 技能，理解如何按最佳实践编写新技能
- 对比不同 harness 下技能的触发差异（Claude Code 有完整插件系统，Codex 和 OpenCode 需要手动配置）
- 如果你的项目有特殊需求，可以尝试修改 Superpowers 的技能文件
- 考虑向 Superpowers 仓库提交 PR——注意 README 说通常不接收新技能，改动必须兼容所有支持的 harness

---

## 相关阅读

- [ponytail：给 AI 编程代理装上「最懒资深工程师」的七级阶梯](/posts/tech/ponytail-lazy-senior-dev-decision-ladder/)
- [12-factor-agents：构建生产级LLM应用的原则](/posts/tech/12-factor-agents-production-llm-guide/)
- [Claude Code Plugins 官方目录](/posts/tech/claude-plugins-official-anthropic-plugin-directory/)
