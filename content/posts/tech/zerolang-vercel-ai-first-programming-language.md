---
title: "zerolang：Vercel 实验性 AI 优先编程语言，为 Agent 时代重新设计语言体验"
date: "2026-05-22T11:00:00+08:00"
slug: "zerolang-vercel-ai-first-programming-language"
description: "zerolang 是 Vercel Labs 推出的实验性编程语言，以「Agent 优先」为核心理念：让 AI 智能体能够边学边用、即时调试、结构化输出，构建一个不依赖外部依赖栈的标准库生态。本文详解其设计哲学、核心语法与快速上手路径。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "编程语言", "Vercel", "Agent", "C语言"]
---

## 什么是 zerolang

zerolang（[vercel-labs/zerolang](https://github.com/vercel-labs/zerolang)）是 Vercel Labs 推出的实验性编程语言，项目自我介绍是「an experiment in building an agent-first programming language」——专为 AI 智能体从头设计的编程语言，目前处于 pre-1.0 的不稳定状态。

核心定位：**让 AI 智能体成为语言的第一公民用户**，而非事后接入 API 的附加工具。

| 基础信息 | |
|---|---|
| 仓库 | [vercel-labs/zerolang](https://github.com/vercel-labs/zerolang) |
|Stars|约 4,200+（2026-05-22）|
| 主要语言 | C |
| 许可证 | Apache-2.0 |
| 官网 | [zerolang.ai](https://zerolang.ai) |
| 创始团队 | Vercel Labs |
| 状态 | pre-1.0，不适合生产环境 |

## 为什么需要专门为 Agent 设计编程语言

传统编程语言（Python、JavaScript、Rust 等）在设计之初假设的用户是人类程序员。AI 时代带来了新的使用模式：

- AI 智能体需要**即时理解代码在做什么**，而非依赖大量文档
- AI 需要**结构化、可机器解析的诊断信息**来执行修复
- AI 需要**无需先搜索依赖**就能直接运行的程序

zerolang 的设计哲学正是回应这三个需求。

## 核心设计目标

### 1. Agent 可快速从示例中学习

语言表面小而规则。AI 智能体可以从少量示例、文档和编译器反馈中快速上手，不必经历传统语言的「依赖搜索→安装→配置」流程。

### 2. 标准库做深，减少依赖依赖栈

常见能力（HTTP、JSON、文件 I/O、网络请求等）都内建于文档完善的标准库中，而不是分散在数千个 npm/pip 包里。zerolang 的愿景是：大多数程序启动时**不需要先搜索依赖**。

### 3. 结构化工具输出，可被 Agent 解析

检查（check）、运行（run）、格式化（fmt）、检查（inspect）、修复（repair）这些操作的输出都是**结构化的 JSON**，方便 AI 读取并采取行动。

### 4. 确定性行为

同一段代码在任何环境下行为一致，诊断信息可预期，工具链输出稳定。减少 AI 需要处理的「边缘情况」和「意外行为」。

### 5. 规则性优先于简洁性

宁可代码更显式，也要让 AI 有唯一的理解路径。「一种明显的表达方式」比「人类可能偏好的糖语法」更受青睐。

## 快速上手

zerolang 官方提供一键安装脚本：

```bash
curl -fsSL https://zerolang.ai/install.sh | bash
export PATH="$HOME/.zero/bin:$PATH"
zero --version
```

### 检查程序

```bash
zero check examples/hello.0
```

### 运行程序

```bash
zero run examples/add.0
# 输出：math works
```

### 构建为可执行文件

```bash
zero build --emit exe --target linux-musl-x64 examples/add.0 --out .zero/out/add
```

### 查看结构化信息

```bash
zero graph --json examples/systems-package
zero size --json examples/point.0
zero skills get zero --full
zero doctor --json
```

## 当前状态与风险提示

> ⚠️ **重要声明**：zerolang 目前明确不适合生产环境使用。README 原文：*"Security vulnerabilities should be expected. zerolang is not ready for production systems, sensitive data, or trusted infrastructure."*

如需体验或开发 zerolang，请务必在**隔离的、一次性的环境**中进行。

## 适用场景与不适用场景

**适合**：
- AI 智能体通过代码与系统交互的场景
- 快速原型验证 Agent 工作流
- 研究 Agent-first 语言设计思路

**不适合**：
- 生产系统
- 处理敏感数据
- 信任基础设施

## 总结

zerolang 是 Vercel Labs 在「AI 时代编程语言」方向的一次严肃探索。它的关键价值不在于取代现有语言，而在于回答一个前瞻性问题：**如果从零设计一门让 AI 智能体作为第一用户语言，会有什么不同？**

关注点包括：内置深度标准库（减少依赖搜索）、结构化工具输出（方便 AI 解析）、小而规则的语言表面（降低 AI 学习成本）。对于 AI 应用开发者和语言设计研究者而言，这个项目值得关注和跟踪。