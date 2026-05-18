---
title: 12-Factor Agents - 构建生产级LLM应用的12条原则
date: 2026-05-18
tags:
  - AI Agent
  - LLM应用
  - 工程实践
  - 架构设计
---

# 12-Factor Agents：构建生产级LLM应用的12条原则

**Stars: 20,277** | **今日: +1,536** | **TypeScript**

GitHub: [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents)

## 一句话评价

12-Factor Agents 是一套类比"12-Factor App"构建可靠 LLM 应用的工程原则，作者基于多年 Agent 开发经验，总结出从上下文管理、工具调用、人机协作到无状态化等 12 条核心实践，帮助开发者避免"框架很好但落地很难"的困境。

## 核心理念

作者 Dex 在 AI 工程师 World's Fair 演讲中指出：目前大多数所谓"AI Agent"其实大部分是确定性代码，只在关键节点用 LLM 点缀。真正好的 Agent 不是"给提示词 + 工具包 + 循环直到完成"，而是由大量软件工程 + 少量 LLM 智能组成。

## 12条原则速览

| 序号 | 原则 | 核心观点 |
|------|------|----------|
| Factor 1 | 自然语言 → 工具调用 | 工具本质是结构化输出，不是魔法 |
| Factor 2 | 掌控你的提示词 | 提示词是代码，应版本化管理 |
| Factor 3 | 掌控上下文窗口 | 上下文工程比提示词优化更重要 |
| Factor 4 | 工具即结构化输出 | 统一 LLM 输出格式，消除二义性 |
| Factor 5 | 执行状态 = 业务状态 | 消除双重状态，减少状态同步复杂度 |
| Factor 6 | 简单 API 的启动/暂停/恢复 | Agent 可中断、可恢复是生产级要求 |
| Factor 7 | 用工具调用联系人类 | Agent 需要人工介入时的标准化机制 |
| Factor 8 | 掌控你的控制流 | 不要把业务逻辑交给 LLM 随机应变 |
| Factor 9 | 将错误压缩进上下文窗口 | 错误信息是上下文燃料，而非异常 |
| Factor 10 | 小而专注的 Agent | 一个 Agent 做一件事，大模型当工具用 |
| Factor 11 | 触发无处不在，用户在哪就在哪 | 事件驱动架构，解耦 Agent 触发源 |
| Factor 12 | 让 Agent 成为无状态 Reducer | 纯函数式推理，每次调用独立可复现 |

## 关键洞察

**Factor 3: 上下文窗口是核心战场**

作者认为"Context Engineering"比"Prompt Engineering"更本质——如何高效管理、利用和压缩上下文，决定了 Agent 的实际能力上限。

**Factor 8: 控制流自主**

大多数 Agent 框架让 LLM 决定下一步做什么，但在生产环境中，控制流应该由代码掌控，LLM 只负责需要"智能"的部分决策。

**Factor 12: 无状态 Reducer**

每次 Agent 调用 = `f(当前状态, 新输入)` → `新状态`，没有副作用，没有隐式状态累积，测试和调试都更简单。

## 适用人群

- 正在或计划将 LLM 应用落地的工程师
- 对"用 Agent 框架总是效果不稳定"感到困惑的团队
- 希望建立 Agent 开发和部署规范的架构师

## 资源链接

- [演讲视频：AI Engineer World's Fair](https://www.youtube.com/watch?v=8kMaTybvDUw)
- [深度解读视频](https://www.youtube.com/watch?v=yxJDyQ8v6P0)
- [Factor 3：掌控上下文窗口（完整原文）](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-03-own-your-context-window.md)
- [npx 脚手架工具](https://github.com/humanlayer/12-factor-agents/discussions/61)：快速创建一个符合 12-Factor 的 Agent 项目