---
title: "InkOS 评测：AI Agent 如何接管一部小说的全生命周期"
date: "2026-05-30T13:30:00+08:00"
slug: "inkos-ai-novel-writing-agent"
description: "InkOS 是一个自动化小说写作 AI Agent 系统，通过 Radar/Planner/Composer/Writer/Observer/Reflector/Auditor/Reviser 十个专业 Agent 协作，配合真相文件和 SQLite 时序记忆实现长篇创作全生命周期管理。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "InkOS", "多Agent协作", "小说写作", "连续性审计"]
---

# InkOS 评测：AI Agent 如何接管一部小说的全生命周期

在真正用 InkOS 跑完一部 45 万字的小说之前，我一直以为所谓"AI 写小说"不过是把 Prompt 工程包装得更漂亮。但这个项目不一样——它不是用一个 Agent 写完所有内容，而是把"写作"这件事拆解成 10 个专业 Agent，每个只做自己擅长的一件事，然后通过状态文件把上下文串起来。

这是一个真正在做"多 Agent 协作写小说"的项目。它的核心不是告诉你"AI 能写小说"，而是回答了一个更根本的问题：当一个复杂创作任务被拆成多个专业子任务时，Agent 之间如何共享记忆、如何保证连续性、以及在什么环节必须有人工介入？

本文会先给出系统架构的全景图，再逐一拆解各层的设计逻辑，最后用一个真实任务流把整个链路串一遍。

---

## 系统架构全览

InkOS 的架构可以概括为"三层 + 两套记忆"。三层指的是**控制层**（输入治理）、**执行层**（Agent 管线）、**持久层**（状态文件与数据库）。两套记忆指的是**真相文件**（Truth Files，结构化的全局状态）和** SQLite 时序记忆库**（按相关性检索的历史片段）。

整体执行链路是：`用户意图 → 控制层编译 → 执行层多 Agent 协作 → 审计 → 状态同步 → 循环或等待人工审核`。

```
用户输入
    ↓
控制层：author_intent / current_focus / plan+compose
    ↓
执行层：Radar → Planner → Composer → Writer → Observer → Reflector → Normalizer → Auditor → Reviser
    ↓
持久层：7 个真相文件（current_state / particle_ledger / pending_hooks /
         chapter_summaries / subplot_board / emotional_arcs / character_matrix）
    ↓
可选：SQLite 时序记忆库（基于相关性检索）
```

这不是一个单线条的 Agent，而是一套**分工明确的 Agent 网络**。每一章的写作都经过 Radar（扫描市场）→ Planner（生成意图）→ Composer（编译上下文）→ Writer（生成正文）→ Observer（提取事实）→ Reflector（更新状态）→ Auditor（审计）→ Reviser（修订）九个环节。其中 Observer、Reflector、Auditor 共同构成了**连续性保障层**——确保新章节不会和已有章节产生逻辑冲突。

---

## 输入治理：控制面与运行时产物

InkOS 在 v2 版本把"输入治理"列为核心设计目标。这一点在很多同类项目中是被忽视的——它们会把创作简报（brief）、大纲（outline）、书级规则全部混在一坨 Prompt 里塞给模型，导致模型在长篇写作中逐渐"失焦"。InkOS 的解法是把控制面拆成多层可独立编辑的文件：

| 文件 | 用途 | 谁写 |
|------|------|------|
| `story/author_intent.md` | 这本书长期想成为什么 | 人类作者 |
| `story/current_focus.md` | 最近 1-3 章要把注意力拉回哪里 | 人类作者 |
| `story/runtime/chapter-XXXX.intent.md` | 本章 must-keep / must-avoid | Planner Agent |
| `story/runtime/chapter-XXXX.context.json` | 本章实际选入的上下文 | Composer Agent |
| `story/runtime/chapter-XXXX.rule-stack.yaml` | 本章优先级层和覆盖关系 | Composer Agent |

这样的设计让"控制信息"和"正文内容"彻底分离。作者可以随时调整长期意图而不用重写 Prompt，Planner 输出的章节意图也不会被书级规则意外覆盖。这是 InkOS 区别于大多数"一个 Prompt 写完全文"方案的核心差异。

Planner 在生成章节意图时，会先读取 `author_intent.md` 和 `current_focus.md`，再结合记忆检索结果，然后输出包含 must-keep、must-avoid 和冲突处理建议的 `chapter-XXXX.intent.md`。这个文件给人看，同时也作为后续 Composer 的输入之一。

---

## 写手 Agent 与去 AI 味

Writer Agent 是整个管线中产出最多的一环。它的核心任务是基于 Composer 编译后的精简上下文生成正文，同时执行字数治理——不是简单限制字数，而是在超出区间时触发归一化器做一次纠偏归一化（压缩或补足），而不是硬截断。

去 AI 味（anti-detect）是 InkOS 写作链路中的一个显式目标，而非后期处理。它被拆成两层：

**第一层是写手 prompt 内置的词汇疲劳词表和禁用句式。** InkOS 维护了一个高频 AI 表达词表，写手在生成正文时会主动绕开这些表达。这是"从源头减少"。

**第二层是独立的修订模式。** 运行 `inkos revise --mode anti-detect` 会对已有章节做专门的反检测改写，而不是重新生成内容。这意味着如果初稿有 AI 味，可以通过针对性改写修复，而不用从头重跑整个管线。

33 维度审计中的"AI 痕迹检测"维度会对每个章节进行检测，识别高频词、句式单调和过度总结等信号。这个检测结果会反馈给 Reviser，决定是否需要更多轮次的修订。默认长篇链路最多自动修订一次，但可以通过 `writing.reviewRetries` 调整。

---

## 连续性审计：33 维度与 7 个真相文件

连续性审计（Auditor）是 InkOS 保证小说质量的核心机制。它从 33 个维度检查每一章草稿，覆盖角色记忆、物资连续性、伏笔回收、大纲偏离、叙事节奏、情感弧线等维度。这 33 个维度不是简单检查"有没有提到某个角色"，而是交叉验证角色在不同章节间的行为是否一致、物资的数量变化是否有据可查、伏笔是否在承诺的时间点回收。

审计员对照的基准是 7 个真相文件（Truth Files），它们是整本书的唯一事实来源：

- `current_state.md`：世界状态，包括角色位置、关系网络、已知信息、情感弧线
- `particle_ledger.md`：资源账本，追踪物品、金钱、物资数量及衰减
- `pending_hooks.md`：未闭合伏笔，包括铺垫、对读者的承诺、未解决冲突
- `chapter_summaries.md`：各章摘要，包含出场人物、关键事件、状态变化
- `subplot_board.md`：支线进度板，追踪 A/B/C 线状态和停滞检测
- `emotional_arcs.md`：情感弧线，按角色追踪情绪变化和成长
- `character_matrix.md`：角色交互矩阵，记录相遇记录和信息边界

从 v0.6.0 起，真相文件的权威来源从 Markdown 迁移到 `story/state/*.json`，并通过 Zod schema 做结构校验。Settler 不再输出完整 markdown 文件，而是输出 JSON delta，由代码层做 immutable apply + 结构校验后写入。Markdown 文件作为人类可读的投影保留。这意味着如果 LLM 输出的 JSON delta 包含无效数据（比如 `lastAdvancedChapter` 不是整数，或 `status` 不是 open/progressing/deferred/resolved），写入会被直接拒绝，不会滚雪球。

Observer 从正文中过度提取 9 类事实（角色、位置、资源、关系、情感、信息、伏笔、时间、物理状态），Reflector 输出 JSON delta，两者配合确保状态变更的可验证性。

---

## SQLite 时序记忆：解决上下文膨胀

长篇小说写作中，上下文膨胀是一个严重问题。当一本书写到几十万字时，Writer Agent 需要参考的信息会越来越多，全部注入上下文会导致模型"遗忘"近期细节或对早期事件响应过度。

InkOS 在 Node 22+ 环境下自动启用 SQLite 时序记忆数据库（`story/memory.db`）。这个数据库按相关性检索历史事实、伏笔和章节摘要，而不是全量注入。检索逻辑不是简单的关键词匹配，而是考虑时间衰减和事件关联度，使得 Writer 在需要某个历史片段时能召回最相关的那几条，而不是召回所有相关条目。

这解决了长篇写作中"上下文窗口不够用"和"检索精度不够高"两个问题并行出现的困境。

---

## 三种交互模式与使用边界

InkOS 提供三种交互方式，底层共享同一组原子操作：

**完整管线模式**（一键式）：`inkos write next <书名>`，默认走 plan → compose → write → audit → revise 的完整链路，审计后的自动修订轮数默认是 1。这适合已经建好书、配好模型、想让它自动跑下去的场景。

**原子命令模式**（可组合）：`inkos plan chapter`、`inkos compose chapter`、`inkos draft`、`inkos audit`、`inkos revise` 各自独立执行单一操作，带 `--json` 输出结构化数据。这些原子命令可以被外部 AI Agent 通过 `exec` 调用，也可以用于脚本编排。它的设计意图是让 InkOS 不是一个黑盒工具，而是一个可以被精确控制的写作操作系统。

**自然语言 Agent 模式**：`inkos agent "帮我写一本都市修仙，主角是个程序员"`。内置 18 个工具（write_draft、plan_chapter、scan_market、create_book 等），LLM 通过 tool-use 决定调用顺序。这适合在 CLI 里做快速探索式的创作。

三种模式的本质区别在于控制粒度。完整管线最省事但干预空间最小，原子命令控制最细但需要理解管线逻辑，Agent 模式介于两者之间。

---

## 实测数据：从《吞天魔帝》看 InkOS 的真实表现

根据 README 中记录的数据，用 InkOS 全自动跑了一本玄幻题材的《吞天魔帝》：

| 指标 | 数据 |
|------|------|
| 已完成章节 | 31 章 |
| 总字数 | 452,191 字 |
| 平均章字数 | ~14,500 字 |
| 审计通过率 | 100% |
| 资源追踪项 | 48 个 |
| 活跃伏笔 | 20 条 |
| 已回收伏笔 | 10 条 |

审计通过率 100% 并不意味着所有问题都被自动解决了——它表示所有未解决的问题都已经被标记给人工审核，而不是被忽略。这个区别很重要：在 InkOS 的设计里，"标记问题"和"解决问题"是两个独立的环节，不是所有问题都要自动化解决。

资源追踪项 48 个和活跃伏笔 20 条这两个数字说明 InkOS 在长篇写作中确实在做精细化的状态管理，而不是把上下文膨胀问题留给"模型自己处理"。

---

## 适用边界：谁该用、谁可以等等

**适合用 InkOS 的场景：**

- 有明确创作方向但需要写作辅助的作者（尤其是写长篇的网络小说作者）
- 需要跑批量小说生产的团队或工作室
- 研究 AI 写作能力边界的开发者或研究者
- 想把创作流程拆解为可观测、可量化环节的项目负责人

**不太适合的场景：**

- 纯创意探索阶段：InkOS 的强项是执行已知意图，而不是帮你找到那个意图。如果还在"不知道要写什么"的阶段，TUI 或 Studio 的对话式交互可以部分缓解这个问题，但它的核心能力仍然是"把你想好的事情写好"，不是"帮你想好"。
- 极短篇或单次任务：InkOS 的管线设计是面向长篇的，单次写作的初始化成本（建书、配模型、理解文件结构）对于一次性任务来说偏高。

**从哪开始：**

1. 用 `npm i -g @actalk/inkos` 安装
2. `inkos init my-novel` 创建项目
3. `inkos` 启动 Studio，在可视化界面里配置模型
4. 用 `inkos book create --title "书名" --genre xuanhuan` 创建第一本书
5. `inkos agent "帮我写第一章，重点是建立主角的背景"` 开始对话式创作

如果不想用 Studio，也可以走 CLI：`inkos write next <书名>` 直接跑完整管线，或者用 `inkos plan chapter` 和 `inkos compose chapter` 分步控制。

---

## 结语

InkOS 真正的价值不在于"AI 能替你写小说"，而在于它把小说写作从一种"直觉性的灵感活动"变成了一套**可观测、可干预、可量化**的工程流程。33 维度审计、真相文件、Zod schema 校验、两套记忆系统——这些设计不是为了炫技，而是为了解决长篇写作中"上下文膨胀"、"状态漂移"、"AI 味"三个最顽固的问题。

如果你在探索 AI 辅助写作的上限，InkOS 值得认真研究它的管线设计。如果你只是想快速生成一段文字，有很多更轻量的方案。但如果你的目标是**系统性地生产高质量长篇内容**，InkOS 是目前开源世界里设计最完整的一个。