---
title: "Superpowers：让AI编程智能体真正学会「做软件工程」的能力框架"
date: "2026-05-21T13:13:00+08:00"
slug: "superpowers-agentic-skills-framework"
description: "Superpowers是一个完整的AI编程智能体软件工程方法论，通过7个强制触发技能让AI从「拿到需求就写代码」转变为「先理解问题、再制定计划、后执行验收」的工程化流程。支持Claude Code、Codex CLI、Cursor等所有主流AI编程工具，200k Stars，MIT协议开源。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "软件开发方法论", "TDD", "智能体框架"]
---

# Superpowers：让AI编程智能体真正学会「做软件工程」的能力框架

> 200,348 Stars · 17,861 Forks · MIT License · Shell · by obra (Jesse Vincent)

## 背景：AI编程助手最大的问题是什么？

Andrej Karpathy 在一条著名的推文中精准描述了这个困境：

> "模型会代替用户做出错误假设，然后不加检查地跑下去。它们不管理自己的困惑，不寻求澄清，不暴露不一致性，不呈现权衡方案，在应该反驳的时候也不反驳。"

> "它们非常喜欢过度复杂化代码和API，堆砌抽象层次，不清理死代码……实现一个1000行的臃肿构造，而实际上100行就够了。"

**Superpowers** 正是为解决这些问题而生的。它是一个完整的**AI编程智能体软件工程方法论**，通过一套强制触发的技能（Skills），让AI编程助手真正像一个资深工程师一样工作——先理解需求，再设计方案，最后写代码并验证。

## 核心价值主张：改变AI的工作模式

传统AI编程助手的工作模式是：**拿到需求 → 直接写代码 → 输出结果**。

Superpowers改变了这个模式为：**理解问题 → 制定规格 → 制定计划 → 执行 → 验收测试 → 代码审查 → 完成开发分支**。

关键在于：这7个技能是**强制触发**的，不是建议。AI在执行任何任务之前都会先检查是否有相关技能被激活。

## 工作流深度解析

### 第一步：Brainstorming（头脑风暴）

当用户提出一个需求时，AI不会立即跳进去写代码，而是通过苏格拉底式提问来厘清需求：

- 你真正想解决的问题是什么？
- 有哪些替代方案？
- 设计方案分块展示，用户逐块确认

最终形成一份设计文档，作为后续所有工作的基础。

### 第二步：制定计划（Writing Plans）

在设计方案获得用户确认后，AI将工作分解为2-5分钟颗粒度的小任务，每个任务都包含：
- 精确的文件路径
- 完整的代码实现
- 验证步骤

这些任务小到可以被一个「热情洋溢但品味不佳的高级工程师」无歧义地执行——没有项目背景、没有判断力、讨厌测试。

### 第三步：子智能体驱动开发（Subagent-Driven Development）

当用户说"go"时，Superpowers启动**子智能体驱动开发**流程：

1. 为每个任务分配一个**全新的子智能体**
2. 子智能体执行两阶段审查：**规格合规性检查 → 代码质量检查**
3. 或者批量执行，在关键节点设置人工检查点

这使得AI能够**自主连续工作数小时而不偏离计划**。

### 测试驱动开发（TDD）

激活条件：实现过程中。

强制执行**红-绿-重构**循环：
1. 写一个失败的测试，看着它失败
2. 写最小化的代码，看着测试通过
3. 重构优化

**删除测试通过前写的任何代码**——这确保了测试先行而非事后补测试。

## 技能库：Superpowers的核心

### 协作类技能

| 技能 | 用途 |
|------|------|
| `brainstorming` | 苏格拉底式设计精炼 |
| `writing-plans` | 详细实现计划 |
| `executing-plans` | 带检查点的批量执行 |
| `dispatching-parallel-agents` | 并发子智能体工作流 |
| `requesting-code-review` | 预审查清单 |
| `receiving-code-review` | 响应反馈 |
| `using-git-worktrees` | 并行开发分支 |
| `finishing-a-development-branch` | 合并/PR决策工作流 |
| `subagent-driven-development` | 两阶段审查的快速迭代 |

### 调试类技能

| 技能 | 用途 |
|------|------|
| `systematic-debugging` | 4步根本原因分析 |
| `verification-before-completion` | 确保真正修复 |

### 测试类技能

| 技能 | 用途 |
|------|------|
| `test-driven-development` | 红-绿-重构循环 |

### 元技能

| 技能 | 用途 |
|------|------|
| `writing-skills` | 创建新技能的最佳实践 |
| `using-superpowers` | 技能系统入门 |

## 哲学理念

Superpowers的设计哲学浓缩为四条原则：

1. **测试驱动开发** — 始终先写测试
2. **系统化优于临时** — 流程优于猜测
3. **简化复杂度** — 简洁是首要目标
4. **证据优于主张** — 验证后再宣布成功

## 安装支持：所有主流AI编程工具

Superpowers支持几乎所有主流AI编程平台：

- **Claude Code**：官方插件市场安装 `/plugin install superpowers@claude-plugins-official`
- **Codex CLI**：官方插件市场搜索安装
- **Cursor**：插件市场搜索"superpowers"安装
- **GitHub Copilot CLI**：`copilot plugin install superpowers@superpowers-marketplace`
- **Factory Droid**：`droid plugin install superpowers@superpowers`
- **Gemini CLI**：`gemini extensions install https://github.com/obra/superpowers`
- **OpenCode**：读取安装指令文件

## 核心洞察：给出目标而非指令

Superpowers的设计哲学最核心的一句话来自Andrej Karpathy：

> "LLMs非常擅长循环直到达到特定目标……不要告诉它要做什么，给它成功标准，然后看它行动。"

这就是「目标驱动执行」（Goal-Driven Execution）原则的本质：**不要命令AI怎么做，给AI验收标准，让AI自主循环直到达标。**

## 与Agency Agents的对比

| 维度 | Superpowers | Agency Agents |
|------|------------|--------------|
| **定位** | 软件工程方法论 + 技能框架 | 多智能体工作流编排 |
| **触发机制** | 技能自动触发（强制流程） | 智能体显式调用 |
| **核心创新** | TDD + 子智能体驱动开发 | 多个专业角色Agent协作 |
| **工作模式** | 先设计→再计划→后执行 | Agent直接执行任务 |
| **适用场景** | 复杂软件开发 | 自动化业务流程 |

Superpowers更专注于**提升单个AI编程助手的工作质量**，而Agency Agents更专注于**多Agent协作完成复杂任务**。两者互补。

## 适用场景

✅ **Superpowers适用的场景**：
- 需要AI完成复杂、 多文件、长期软件项目开发
- 希望AI先理解需求再动手，而不是拿到代码就跑
- 需要AI遵循工程化流程（TDD、代码审查、计划执行）
- 希望AI工作数小时不需要人工干预

❌ **Superpowers不太适用的场景**：
- 简单的一次性代码生成任务
- 快速原型验证
- 单文件脚本编写

## 总结

Superpowers通过将**软件工程方法论编码为可自动触发的技能**，解决了AI编程助手「过于急躁、不管理困惑、过度复杂化」的问题。200k Stars的社区认可证明了这一方向的巨大价值。

如果你发现AI编程助手总是在你没有确认设计之前就开始写代码，或者输出的代码总是比需要的复杂，推荐试试Superpowers——它会让你的AI助手真正像一个训练有素的软件工程师一样工作。

---

原文：[GitHub - obra/superpowers](https://github.com/obra/superpowers)
