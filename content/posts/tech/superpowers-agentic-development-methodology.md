---
title: "Superpowers：给编程智能体装上一套完整开发方法论"
date: 2026-05-14T11:40:00+08:00
slug: "superpowers-agentic-development-methodology"
description: "Superpowers是由Jesse Vincent开发的开源项目，通过可组合的技能库让主流AI编程工具自动遵循TDD、设计优先、子智能体驱动等开发原则，实现数小时自主工作不偏离计划。本文解析其核心理念、工作流与技能体系。"
draft: false
categories: ["技术笔记"]
tags: ["AI编程", "智能体开发", "TDD", "Superpowers", "开源工具"]
---

# Superpowers：给编程智能体装上一套完整开发方法论

如果你用 Claude Code、Cursor、Codex 或其他 AI 编程工具，是否有过这样的体验：模型上来就写代码，写完才发现需求理解偏了，或者代码质量参差不齐，后续大量返工？

**Superpowers** 的做法是给智能体一套**可自动触发的工作流技能**，让它在动手之前先理解需求、设计方案、写好计划，然后按部就班执行，最终产出经过评审的代码。

截至 2026 年 5 月，这个项目在 GitHub 上已积累 **189k Stars**、16.9k Forks，是近期最受关注的 AI 编程辅助开源项目之一。

---

## 项目概览

| 项目信息 | |
|---|---|
| 仓库 | [obra/superpowers](https://github.com/obra/superpowers) |
| 作者 | Jesse Vincent（Prime Radiant） |
| Stars | 189,790 |
| 主语言 | Shell |
| License | MIT |
| 首次发布 | 2025 年 10 月 |

Superpowers 的定位是"面向编程智能体的完整软件开发方法论"（a complete software development methodology for your coding agents）。它不是一个新模型，也不是 GUI 工具，而是一组可以在主流 AI 编程工具中自动激活的技能（skills）。

---

## 核心问题：AI 编程工具缺的是约束

大多数 AI 编程工具的问题在于：

- **上来就写**：没有设计阶段，直接生成实现，容易返工
- **计划模糊**：任务拆解粗糙，执行中不断偏离原始目标
- **测试缺失**：代码写完没有测试，或者测试后补，违反 TDD 原则
- **质量不一**：每次生成的代码质量波动大，缺乏统一审查流程

Superpowers 的解决思路是：不给智能体更多 prompt，而是预先植入一套**强制性工作流**，让它在**任何任务开始前**自动检查是否有相关技能需要激活。

---

## 工作流程：七步强制触发

Superpowers 将软件开发拆解为七个阶段，每个阶段对应一个可自动触发的技能。**强制执行，不是建议**——智能体在任意任务前都会先检查是否有适用的技能。

### 1. brainstorming（设计前阶段）

在写任何代码之前激活。通过苏格拉底式提问理清需求，将设计文档分段展示给用户确认，避免在需求模糊时就开始实现。

### 2. using-git-worktrees（隔离工作区）

设计确认后，创建独立的 Git worktree 分支，初始化项目环境，验证干净的测试基线，确保多人并行开发不互相干扰。

### 3. writing-plans（任务规划）

将工作拆解为 2-5 分钟的小任务，每个任务包含：精确文件路径、完整代码、验证步骤。计划足够详细，让"一个缺乏判断力、讨厌测试的初级工程师"也能执行。

### 4. subagent-driven-development / executing-plans（执行与审查）

启动子智能体驱动开发流程：每个任务由新的子智能体完成，经两阶段审查（是否符合规格 → 代码质量）后才进入下一个任务。支持批量执行加人工检查点，实践中 Claude 可以自主工作数小时而不偏离计划。

### 5. test-driven-development（TDD 执行）

强制执行 RED-GREEN-REFACTOR 循环：先写失败的测试 → 运行看到失败 → 写最少量代码让它通过 → 重构。测试写完之前的代码必须删除。

### 6. requesting-code-review（代码评审）

任务之间触发评审，对照计划检查实现，**严重问题直接阻止继续**。评审结果按严重程度分类，Critical 级别必须修复才能推进。

### 7. finishing-a-development-branch（收尾）

任务完成后验证测试，提供四个选项：合并、提 PR、保留分支或丢弃。自动清理工作区。

---

## 技能库一览

Superpowers 的技能分为四类：

**测试**
- `test-driven-development`：RED-GREEN-REFACTOR 全流程，含测试反模式参考

**调试**
- `systematic-debugging`：四阶段根因分析（含 root-cause-tracing、defense-in-depth、条件等待技术）
- `verification-before-completion`：确认问题真的修复了

**协作**
- `brainstorming`、`writing-plans`、`executing-plans`、`subagent-driven-development`、`dispatching-parallel-agents`、`requesting-code-review`、`receiving-code-review`、`using-git-worktrees`、`finishing-a-development-branch`

**元**
- `writing-skills`：如何创建新技能（含测试方法论）
- `using-superpowers`：技能系统入门

所有技能都设计为**跨智能体兼容**——在 Claude Code、Codex CLI、Cursor、GitHub Copilot CLI 等工具中表现一致。

---

## 安装与支持

Superpowers 支持主流 AI 编程工具，安装方式各异：

| 工具 | 安装方式 |
|---|---|
| Claude Code | `/plugin install superpowers@claude-plugins-official` |
| Codex CLI | `/plugins` → 搜索 superpowers |
| Cursor | `/add-plugin superpowers` |
| GitHub Copilot CLI | `copilot plugin install superpowers@superpowers-marketplace` |
| Gemini CLI | `gemini extensions install https://github.com/obra/superpowers` |
| OpenCode | 引导从 INSTALL.md 获取指令 |
| Factory Droid | `droid plugin install superpowers@superpowers` |

---

## 设计哲学

README 明确列出了四个原则：

- **Test-Driven Development**：永远先写测试
- **Systematic over ad-hoc**：流程优先于猜测
- **Complexity reduction**：简单性是首要目标
- **Evidence over claims**：验证后再宣告成功

这些不是写在墙上的标语，而是通过强制触发的技能嵌入到每个任务的执行路径中。

---

## 适用场景与局限

### 适合的场景

- 需要 AI 编程工具完成**多文件、较复杂**的项目开发
- 团队希望 AI 产出**可审查、可复现**的代码
- 需要 AI 在长时间自主工作中**保持计划不偏移**

### 本文未覆盖的

- 各智能体 harness 的具体集成细节（需参考各工具文档）
- `writing-skills` 技能的具体用法（官网有专项文档）
- 项目路线图与未来特性预测

---

## 总结

Superpowers 的关键价值在于**把软件开发中积累的实践建议自动化**，让 AI 编程工具从"随时可能偏离计划的代码生成器"变成"遵循强制工作流的开发搭档"。189k Stars 的关注度说明这个方向击中了大量开发者的痛点。

如果你用 Claude Code 或类似工具，尝试安装 Superpowers，观察它如何改变智能体的行为模式——可能比任何新模型都更有立竿见影的效果。

**官网**：[https://superpowers.github.io](https://superpowers.github.io)（文中未直接提供，从 repo 推断）  
**Discord 社区**：https://discord.gg/35wsABTejz  
**作者博客**：[blog.fsck.com](https://blog.fsck.com)