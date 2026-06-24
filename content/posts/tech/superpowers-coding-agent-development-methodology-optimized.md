---
title: "Superpowers：让Coding Agent拥有完整开发方法论的插件系统"
date: "2026-05-20T15:52:00+08:00"
slug: "superpowers-coding-agent-development-methodology"
description: "Superpowers是一个软件开发方法论+插件系统，为Claude Code、Codex、Cursor等Coding Agent注入结构化开发流程。包含6个可自动触发的技能（brainstorming→spec→plan→TDD→review），让Agent在写代码前先理解需求、拆解任务、写出可验证的测试，实现数小时自主工作不断线。"
draft: false
categories: ["技术笔记"]
tags: ["AI Coding Agent", "Superpowers", "开发方法论", "TDD", "Claude Code"]
---

# Superpowers：让 Coding Agent 拥有完整开发方法论的插件系统

## 学习目标

读完本文后，你应该能够：

- 理解为什么直接让 Coding Agent 写代码会导致意图偏差、零测试防护和架构漂移
- 掌握 Superpowers 的 6 个技能及其强制流程
- 通过一个完整案例理解 Superpowers 的实际工作流程
- 对比 Superpowers、Harness Engineering 和 Compound Engineering 的异同
- 判断 Superpowers 是否适合你的项目和团队

---

2025 年 10 月 9 日，Anthropic 正式发布 Claude Code 插件系统。同一天，Jesse Vincent 发布了 Superpowers 的第一个版本。截至 2026 年 5 月，这个项目在 GitHub 上积累了超过 199,000 个 Star，成为 Claude Code 生态中安装量仅次于 Anthropic 官方插件的第三方项目。

Superpowers 给 Coding Agent 装上了一套开发流程——6 个强制检查点，Agent 每次起飞都遵循同一条航线，每一步都不可跳过。

## 为什么直接写代码是错的

大多数 Coding Agent 的行为模式是：收到指令 → 开始写代码。一个没有约束的 Agent 会同时暴露三个问题：

1. **意图偏差**。你说「帮我做一个用户认证系统」，Agent 的理解和你想要的可能差了十万八千里，但它不会停下来问——它已经在写了。
2. **零测试防护**。每写一个功能，Agent 不会验证它是否破坏了已有功能。你今天修了一个 Bug，明天它悄悄被另一个修改覆盖了。
3. **架构漂移**。Agent 没有「设计」概念。它只是在当前文件的上下文中做出局部最优选择，但局部最优的叠加往往等于全局灾难。

这些问题不是 Agent 能力不够导致的——Claude、GPT-5 在代码生成上的能力已经足够强。缺的是工程纪律：动手之前先停下来想一想的肌肉记忆。

Jesse Vincent 的洞察是：靠更好的 prompt 解决不了这个问题。写一条提示词让 Agent「永远先写测试」——它会点头，然后继续直接写生产代码。需要一个在系统层面强制执行流程的机制。

## 6 个技能构成的强制流程

Superpowers 在 Agent 的决策链路中埋入了 6 个检查点，从需求到交付逐步推进。每个技能是强制规程，不满足条件，流程不会继续。

### brainstorming：先问清楚，再动手

brainstorming 在 Agent 检测到你要构建东西时自动触发。Agent 不会写代码，而是退后一步，像有经验的产品经理一样提问：

- 你真正想解决的问题是什么？不要描述你想要的方案，描述你遇到的困境。
- 技术栈有什么约束？团队规范是什么？有不可以改的遗留代码吗？
- 「完成」的定义是什么？什么情况下这个功能算交付了？

Agent 用一个关键技巧呈现设计文档：每段不超过 200-300 字。传统 AI 对话中，Agent 一上来就丢给你一堵墙一样的文字，你根本不会读完。Superpowers 把设计文档拆成短段落，一段一段让你确认，确保你真的消化了每个决策点。

### writing-plans：拆成 2-5 分钟能完成的小任务

需求确认后，Agent 把整个实现计划拆成若干个原子任务。每个任务包含三个要素：精确的文件路径、完整的代码改动描述、可执行的验证步骤。

这个颗粒度的选择经过了精心设计。2-5 分钟是一个「人类愿意看一眼」的时间窗口——太长了你会跳过检查，太短了拆解本身就是浪费。每个任务完成后，Agent 会自动进入验证环节，确认结果符合预期后再推进下一个。

### using-git-worktrees：隔离不是可选项

设计批准后，Agent 不会在你的主分支上操作。它使用 Git worktree 创建一个隔离的工作空间，在新分支上运行项目初始化，验证干净的测试基线。具体效果：

- 不同功能的工作完全隔离，互不污染
- 测试基线在开始前就被确认，任何新增的失败都可以追溯到当前改动
- 如果方向错了，丢弃整个 worktree 零成本回退

### subagent-driven-development：每个任务一个干净的上下文

这是 Superpowers 最激进的设计决策。传统 AI 编程助手的上下文会随着对话越来越长，Agent 越跑越偏。Superpowers 的做法是：每个任务派一个全新的子 Agent 去独立实现——零上下文污染。

主 Agent 把任务描述发给子 Agent，子 Agent 在自己的会话中实现、自测、提交、自审。然后派发另一个子 Agent 做规格审查（第一轮）和代码质量审查（第二轮）。两轮审查都通过后，结果返回主 Agent，继续下一个任务。

这样多个独立任务可以并行执行。主 Agent 不再是线性地一个一个做，而是像工程经理一样分配工作、收集结果、做质量把控。

### TDD：不是建议，是铁律

Superpowers 的 TDD 是 RED-GREEN-REFACTOR 循环：

1. 先写失败测试
2. 运行测试，确认它失败（红色）
3. 写最小代码让测试通过（绿色）
4. 重构，保持测试通过
5. 提交

如果 Agent 先写了生产代码再写测试，Superpowers 要求**删除生产代码**，从测试开始重来。这不是教学示范，是强制执行。同时强调 YAGNI（You Aren't Gonna Need It）和 DRY（Don't Repeat Yourself），防止 Agent 过度设计。

### reviewing：两阶段审查

每个子 Agent 完成任务后，代码不会直接进入主线。Superpowers 启动两阶段审查：

1. **规格审查**：代码是否按照计划实现了？有没有遗漏或多余的功能？
2. **代码质量审查**：代码风格是否一致？有没有潜在的性能问题或安全漏洞？

审查结果按严重程度分级。严重问题会阻塞流程，Agent 必须修复后才能继续。轻微问题记录在案，不阻塞但会在后续任务中提醒。

## 为什么这套流程有效

人类开发者能在复杂项目中保持方向感，靠的是内化的工程纪律：先理解需求，再设计方案，拆成小步，每步验证，持续重构。AI Coding Agent 没有这种肌肉记忆——它接收到指令后的行为模式是直接响应，这是对话模型的设计特性。Superpowers 在 Agent 的决策链路上安装了一个「工程纪律层」，在每次代码生成之前强制插入检查点。

约束在正确的流程里，Claude Code 就能自主工作数小时而不偏离方向。

## 实战案例：从一句需求到合并 PR

下面用一个真实场景走完 Superpowers 的完整流程。假设你正在开发一个博客平台，需要添加一个「文章阅读时间估算」功能。

### 第 1 步：brainstorming——对话还原

你告诉 Claude Code：「给文章详情页加上阅读时间显示。」

Agent 没有直接写代码，而是开始了 brainstorming，逐段确认需求细节。你逐段确认后，brainstorming 阶段完成。

### 第 2 步：using-git-worktrees

Agent 创建了一个名为 `feature/reading-time` 的 Git worktree，切换到新分支，运行测试确认测试基线全部通过。

### 第 3 步：writing-plans

Agent 将实现拆成 4 个原子任务，你批准计划后，Agent 进入执行阶段。

### 第 4-6 步：TDD + reviewing + 合并

子 Agent 依次完成测试编写、组件集成、集成测试。每个子 Agent 都在干净的上下文中工作。所有任务完成后，审查 Agent 启动，审查通过后 Agent 运行完整测试套件，然后提交 PR。

整个过程从你提出需求到 PR 提交，你只做了两件事：回答 brainstorming 阶段的问题，批准实施计划。

## 与其他方法论的对比

### Superpowers vs Harness Engineering

Harness Engineering 由 Mitchell Hashimoto 在 2026 年初正式提出。其公式是：`Agent = Model + Harness`。

| 维度 | Superpowers | Harness Engineering |
|------|------------|-------------------|
| 定位 | 开箱即用的开发流程插件 | 系统级工程方法论框架 |
| 适用场景 | 个人开发者，快速上手 | 团队/组织，定制化工程环境 |

Superpowers 可以理解为 Harness Engineering 的一个具体实现。独立开发者想立刻获得工程纪律，Superpowers 是最快的路径。

### Superpowers vs Compound Engineering

Compound Engineering 是 2026 年兴起的另一个范式，其思想是「每次完成的任务都让下一次变得更快」。

| 维度 | Superpowers | Compound Engineering |
|------|------------|---------------------|
| 增长模型 | 线性质量保障 | 指数级加速 |
| 时间维度 | 单次任务的正确性 | 多次任务的累积效应 |

Compound Engineering 解决的是「如何让第 100 个任务比第 1 个任务快 10 倍」，Superpowers 解决的是「如何让第 1 个任务做对」。两者不冲突。

## FAQ

**Q1：Superpowers 适合所有项目吗？**

不适合。Superpowers 的 overhead 是真实存在的——brainstorming 阶段可能需要 5-10 分钟，计划拆解也需要时间。对于改动一个变量名、写一个工具函数这类 30 秒能完成的任务，用 Superpowers 是过度设计。它的最佳适用场景是持续时间超过 30 分钟、涉及多个文件的复杂任务。

**Q2：Agent 真的能自主工作数小时吗？**

Jesse 在 README 中的表述是「a couple hours at a time」。实际体验取决于任务复杂度、Agent 的能力（不同模型差异很大）和你的项目结构。结构清晰、测试覆盖好的项目，Agent 自主工作时间更长。

**Q3：如果我不认同 Agent 的设计方案怎么办？**

brainstorming 阶段的设计文档是逐段确认的，你可以在任何一步提出修改。这不是一个「Agent 说了算」的流程——你始终是决策者，Agent 是执行者。

## 自检测试

安装 Superpowers 后，你可以用以下检查项验证它是否正常工作：

**检查 1：Agent 是否在写代码前先提问？**

提出一个模糊的需求，比如「帮我加个功能」。正常工作的 Superpowers 会让 Agent 进入 brainstorming 模式，开始提问而不是直接写代码。

**检查 2：是否创建了 Git worktree？**

批准设计后，检查你的 Git 仓库是否有新的 worktree 被创建（`git worktree list`）。

**检查 3：子 Agent 是否先写测试再写代码？**

观察 Agent 的输出。如果它先写生产代码再写测试，说明 TDD 技能没有正确执行。

## 支持的 Harness

| Agent | 安装方式 |
|-------|---------|
| Claude Code | `/plugin install superpowers@claude-plugins-official` |
| Codex CLI | `/plugins` 搜索安装 |
| Cursor | `/add-plugin superpowers` |

## 适用边界

**改造收益最大的场景：**

- 持续时间超过 30 分钟、涉及多个文件修改的复杂任务
- 有明确验收标准的功能开发（知道「做完」长什么样）
- 需要测试覆盖率的项目（库、API、后端服务）

**用 Superpowers 反而浪费时间的场景：**

- 30 秒内能完成的单文件修改（改变量名、修一个 typo）
- 纯探索性任务——你还不确定要做什么，需要边试边看
- 一次性脚本或临时工具（写完就扔的代码不需要工程纪律）

**一个判断标准：** 如果你在开始一个任务之前，自己会先花 5 分钟做设计——那这个任务就应该用 Superpowers。

## 相关阅读

- [12-factor-agents：构建生产级LLM应用的原则](/posts/tech/12-factor-agents-production-llm-guide/)
- [Andrej Karpathy Skills：提升Claude Code的实战指南](/posts/tech/andrej-karpathy-skills-guide/)
- [Claude Code Plugins 官方目录](/posts/tech/anthropics-claude-plugins-official-guide/)
