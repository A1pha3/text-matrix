---
title: "12-Factor Agents：构建可投产 AI 应用的设计原则"
date: "2026-05-18T19:56:00+08:00"
description: "12-factor-agents 是一份来自 Dex 的实践指南，总结了构建生产级 LLM 应用的核心工程原则，涵盖上下文管理、工具调用、状态管理、控制流等十二个维度。
slug: "12-factor-agents-llm-principles"
categories:
  - "技术笔记"
tags:
  - "LLM"
  - "AI Agent"
  - "工程实践"
  - "上下文工程"
  - "提示工程"
  - "TypeScript"
---

用 LLM 做产品，很多人容易掉进两个坑：要么迷信「给个 prompt 加一堆工具，循环到目标达成」的万能 Agent 范式，要么把 LLM 当成传统函数调用，埋进一堆 if-else 里当增强搜索。

Dex 的观察是：**真正能交付给生产用户的 LLM 软件，大多不是纯 Agent，而是软件 + LLM 步骤的混合体**。他把这个洞察系统化成了一套设计原则，叫 **12-Factor Agents**。

## 十二个原则速览

| Factor | 主题 | 核心观点 |
|--------|------|----------|
| 1 | Natural Language to Tool Calls | 用自然语言描述任务，而非硬编码工具路由 |
| 2 | Own your prompts | 提示词是自己的，不要过度依赖框架注入 |
| 3 | Own your context window | 上下文窗口是核心资产，需要精心管理 |
| 4 | Tools are just structured outputs | 工具调用本质是结构化输出，不是魔法 |
| 5 | Unify execution and business state | 执行状态和业务状态应该统一建模 |
| 6 | Launch/Pause/Resume with simple APIs | 支持暂停/恢复是最基本的可靠性要求 |
| 7 | Contact humans with tool calls | 复杂决策应该能主动联系人类 |
| 8 | Own your control flow | 控制流是软件自己的职责，不是 LLM 的 |
| 9 | Compact Errors into Context | 错误信息应该压缩进上下文，而非打断流程 |
| 10 | Small, Focused Agents | 小而专注的 Agent 比大一统的 Agent 更可靠 |
| 11 | Trigger from anywhere | 从任意地方触发，在用户所在的地方相遇 |
| 12 | Make your agent a stateless reducer | 把 Agent 做成无状态 reducer，便于推理和调试 |

## 几个值得细说的点

**Factor 3: 拥有你的上下文窗口**。这是很多人低估的一条。上下文窗口不是「塞进去就行」的资源，而是需要精心构建的数据结构。12-factor-agents 把上下文工程单独成篇，强调检索策略、上下文压缩和注入时机的设计。

**Factor 8: 拥有你的控制流**。好的 LLM 应用不是把控制权完全交给模型，而是软件定义骨架、模型填充细节。比如工作流引擎编排 Agent，而不是 Agent 自己 loop 到天荒地老。

**Factor 12: Stateless Reducer**。把 Agent 看作一个无状态的 reducer（状态 + 输入 → 新状态），这让整个系统可测试、可回放、可推理。避免把 Agent 当成有记忆的活物。

## 关于作者

Dex 长期做 AI Agent 相关工作，访谈过大量 YC 创始人和 AI 工程团队。他发现行业里真正在生产环境跑 AI Agent 的团队，大多是自己造轮子，而不是用某个框架。他把这些工程实践提炼出来，形成了这份指南。

目前已在 GitHub 获得 **20,212 stars**，有配套的 `npx/uvx create-12-factor-agent` 脚手架，还有视频讲解和 Discord 社区。

> 项目地址：[https://github.com/humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents)