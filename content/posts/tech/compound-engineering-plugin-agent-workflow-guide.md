---
title: "Compound Engineering Plugin: 让每次工程工作都为后续铺路的Agent工作流系统"
date: "2026-05-30T13:13:57+08:00"
slug: "compound-engineering-plugin-agent-workflow-system"
description: "Compound Engineering 是 EveryInc 出品的跨智能体工程工作流系统，提供37个技能和51个Agent，覆盖规划、评审、知识沉淀全链路，适用于 Claude Code、Cursor、Codex、OpenCode 等主流编程智能体。"
draft: false
categories: ["技术笔记"]
tags: ["AI智能体", "Claude Code", "Cursor", "Codex", "工作流", "自动化", "工程效能"]
---

## 核心判断

Compound Engineering 的本质是**一套让工程工作产生复利的协议**：80% 的工作量在前置规划和复盘，20% 在实际编码。每次迭代都为后续降低难度，而不是累积技术债。

它不是一堆配置模板，而是一套覆盖规划→执行→评审→知识固化的完整闭环，适用于 Claude Code、Cursor、Codex、OpenCode 等主流 AI 编程智能体。

## 系统架构

### 核心理念：工作的复合增长

传统开发中，每做一个功能，代码库变大，下一个功能更难改。Compound Engineering 反转这个逻辑——通过充分的前置规划和严格的复盘评审，让每个功能都为后续铺路，而不是挖坑。

### 核心工作环路

```
 brainstorm（需求梳理） → plan（详细实现计划） → work（执行） → code-review（评审） → compound（知识固化） → repeat
```

每轮循环都会让下一个循环更快，因为brainstorm更精准、plan更清晰、review抓到更多模式、知识被固化复用。

### 技能矩阵

| 技能 | 用途 |
|------|------|
| `/ce-strategy` | 创建/维护 STRATEGY.md——产品的目标问题、方案、指标、追踪锚点 |
| `/ce-ideate` | （可选）大型头脑风暴：在动手前生成并批判性评估更大范围的想法 |
| `/ce-brainstorm` | 交互式问答，梳理需求后写出需求文档 |
| `/ce-plan` | 将功能想法转化为详细实现计划 |
| `/ce-work` | 用 worktree 和任务追踪执行计划 |
| `/ce-debug` | 系统性复现失败、追踪根因、实施修复 |
| `/ce-code-review` | 多人 Agent 代码评审 |
| `/ce-doc-review` | 文档评审 |
| `/ce-compound` | 将学到的经验文档化，供后续复用 |

### 上游与下游

`/ce-strategy` 是整个环路上游——它维护一个短小耐用的策略锚点文档（STRATEGY.md），包含目标问题、方案思路、用户画像、关键指标和追踪记录。ideate、brainstorm、plan 在执行前都会读取这个锚点，确保策略选择能流进功能构思和优先级排序。

`/ce-product-pulse` 是读侧配套——生成指定时间窗口（24h、7d 等）的使用、性能、错误和跟进报告，保存到 `docs/pulse-reports/` 形成可浏览的时间线，为下一轮策略更新和头脑风暴提供真实信号。

## 安装方式

### Claude Code

```
/plugin marketplace add EveryInc/compound-engineering-plugin
/plugin install compound-engineering
```

### Cursor

```
/add-plugin compound-engineering
```

### Codex（三步）

```bash
# 1. 注册 marketplace
codex plugin marketplace add EveryInc/compound-engineering-plugin
# 2. 安装 Agent
bunx @every-env/compound-plugin install compound-engineering --to codex
# 3. 通过 Codex TUI 安装插件（/plugins → 找 Compound Engineering → Install）
```

> 三步缺一不可：marketplace + TUI 安装处理 skills，Bun 步骤添加 review/research/workflow agents。

## 设计取舍

### 优势

- **跨智能体**：同一套工作流逻辑可在 Claude Code、Cursor、Codex、OpenCode 之间迁移，降低切换成本
- **知识可累积**：`/ce-compound` 确保经验不被遗忘，后续 Agent 不必重复踩坑
- **Review 质量**：多人 Agent 评审可以在合并前捕获模式和 Bug，不只是语法错误

### 局限

- 需要团队接受并坚持使用这套协议，学习曲线较陡
- `/ce-product-pulse` 需要项目历史数据积累才有价值，冷启动阶段效果有限
- Codex 的插件安装流程最复杂，需要三步才能完整配置

## 采用建议

1. 先在小型项目上跑通完整环路（brainstorm → plan → work → review → compound）
2. `/ce-setup` 会检查环境和引导项目配置，建议首次使用
3. STRATEGY.md 应由团队共识维护，不要由单个 Agent 独立生成
4. 初期坚持不用 `/ce-ideate` 直接跳到 brainstorm，降低仪式感门槛

---

项目地址：[EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin)，⭐ 18.2k。