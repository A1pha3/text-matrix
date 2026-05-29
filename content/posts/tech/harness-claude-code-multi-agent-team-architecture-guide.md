---
title: "Harness：让Claude Code拥有「多Agent舰队」的工具箱"
date: "2026-05-29T09:06:54+08:00"
slug: "harness-claude-code-multi-agent-team-architecture-guide"
description: "Harness是一个Claude Code插件，作用是把一句「为此项目构建Harness」变成一套完整的多Agent协作架构。它预置了6种团队组织模式（Pipeline、Fan-out、Expert Pool等），自动生成对应Agent定义和Skill文件。本文覆盖其定位、架构模式和工作流。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI Agent", "Multi-Agent", "插件", "工作流自动化"]
---

# Harness：让Claude Code拥有「多Agent舰队」的工具箱

给Claude Code说一句话，它就能帮你生成一套多Agent团队——这就是Harness在做的事。

Harness的定位是「**L3 Meta-Factory / Team-Architecture Factory**」。它不是某一个具体任务Agent，而是一个生成Agent团队的工厂。你告诉它项目领域，它给你一套可以协作的Agent定义和配套Skill。

## 核心判断

Harness解决的是一个具体问题：当任务变得复杂，单一Agent的记忆容量和专注度开始吃力的时候，需要多个Agent协同工作。但手工定义多Agent的协作架构、编写Agent定义和Skill文件是繁琐的。Harness把这个过程自动化了——你描述领域，它生成团队。

## 系统分层

Harness所在的技术生态层级：

| 层级 | 说明 |
|------|------|
| L1 | 单任务Agent |
| L2 | Cross-Harness Workflow（跨Harness标准化） |
| **L3** | **Meta-Factory：生成其他Harness的工厂** |
| L3 — Runtime-Configuration Factory | 生成确定性运行时配置（如coleam00/Archon） |
| **L3 — Team-Architecture Factory** | **生成多Agent团队架构（Harness所在）** |

同一个L3层，Archon负责「运行时配置」，Harness负责「团队架构」，两者可以组合使用。

## 6种团队架构模式

Harness预置了6种经过验证的多Agent协作模式，每种适合不同场景：

| 模式 | 适用场景 |
|------|---------|
| **Pipeline** | 顺序依赖的任务链，前一步输出决定下一步输入 |
| **Fan-out/Fan-in** | 并行独立子任务，全部完成后合并结果 |
| **Expert Pool** | 根据上下文动态选择最合适的专家Agent |
| **Producer-Reviewer** | 生产者生成内容，审查者质量把关 |
| **Supervisor** | 中央调度Agent负责动态分配任务 |
| **Hierarchical Delegation** | 层级递归委托，父Agent拆解任务给子Agent |

## 任务流案例：Harness如何把领域描述变成Agent团队

以「深度研究」场景为例：

```
Phase 1: Domain Analysis（分析项目领域和任务边界）
    ↓
Phase 2: Team Architecture Design（选择团队组织模式：Producer-Reviewer + Supervisor）
    ↓
Phase 3: Agent Definition Generation（生成.claude/agents/下的Agent定义文件）
    ↓
Phase 4: Skill Generation（生成.claude/skills/下的Skill文件，含Progressive Disclosure）
    ↓
Phase 5: Integration & Orchestration（配置Agent间数据传递和错误处理）
    ↓
Phase 6: Validation & Testing（触发验证和Dry-run测试）
```

最终产出的是一个可直接使用的 `.claude/` 目录，包含多个Agent定义和配套Skill。

## Skill的Progressive Disclosure设计

Harness生成的Skill使用「渐进披露」（Progressive Disclosure）策略管理上下文——Agent只会看到当前步骤需要的信息，而不是把所有上下文一股脑塞进去。这对防止Agent分心和控制token消耗很关键。

## 安装方式

### 方式一：Plugin Marketplace

```shell
/plugin marketplace add revfactory/harness
/plugin install harness@harness-marketplace
```

### 方式二：直接复制Skill目录

```shell
cp -r skills/harness ~/.claude/skills/harness
```

## 使用方式

在Claude Code中输入自然语言指令即可触发：

```
Build a harness for deep research
Design an agent team for this domain
Set up a harness
```

Harness会自动分析领域并生成对应的Agent团队配置。

## 适用边界

**值得使用Harness的场景：**
- 复杂任务需要多个专家Agent协同处理
- 任务涉及并行探索、交叉验证环节（如深度研究、内容审查）
- 需要在Claude Code中构建可复用的多Agent工作流

**不适合的场景：**
- 简单单任务，单独一个Agent就能完成
- 已有现成的固定Harness配置，不需要动态生成
- 只需要单次调用的临时任务

## 与同类工具的关系

- **Archon**（L3同层）：Archon生成确定性运行时配置，Harness生成多Agent团队架构。两者互补，可以同时启用。
- **ECC**（L2）：ECC做跨Harness的技能标准化，适合管理多个Harness场景下的统一规则和Hook。

## 阅读路径

- [Harness GitHub仓库](https://github.com/revfactory/harness)
- [Claude Code Plugin文档](https://docs.claude.com)
- [Agent设计模式参考](https://github.com/revfactory/harness/tree/main/skills/harness/references)