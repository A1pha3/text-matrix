---
title: "Datawhale hello-agents：44K星从零构建智能体完全指南"
date: "2026-05-09T03:20:00+08:00"
slug: "datawhale-hello-agents-from-zero-to-agent"
description: "hello-agents 是 Datawhale 出品的 44K 星智能体教程，覆盖从基础理论到多智能体系统的完整学习路径。15 章内容包括 ReAct/Reflection 范式、低代码平台、AutoGen/LangGraph 框架、MCP/A2A 协议、Agentic RL 训练与 3 个综合实战项目。本文梳理该教程的核心脉络与关键知识点。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Datawhale", "ReAct", "MCP", "Agentic RL", "多智能体"]
---

## 项目概览

hello-agents（https://github.com/datawhalechina/hello-agents）是 Datawhale 社区出品的**系统性智能体学习教程**，GitHub 星标 44,483，中文编写，完全开源免费。教程目标是帮助读者从「大语言模型的使用者」蜕变为「智能体系统的构建者」。

**核心定位**：专注于 **AI Native Agent**（真正以 AI 驱动的智能体），而非 Dify/Coze/n8n 这类流程驱动的软件开发模式。教程穿透框架表象，从智能体的核心原理出发，理解经典范式，并最终构建属于自己的多智能体应用。

**关键数据**：
- Stars：44,483
- 编程语言：Python（主语言）
- 许可证：开源免费
- 章节数：15 章 + 额外章节（Extra）
- 在线阅读：[国际版](https://datawhalechina.github.io/hello-agents/) / [国内加速版](https://hello-agents.datawhale.cc)
- PDF 下载：https://github.com/datawhalechina/hello-agents/releases/latest/

---

## 教程结构：五部分学习路径

### 第一部分：智能体与语言模型基础（第一章至第三章）

**第一章：初识智能体** 讲解智能体的定义、类型、范式与应用场景。你会理解为什么 2025 年被称为「Agent 元年」——技术焦点从训练更大的基础模型转向构建更聪明的智能体应用。

**第二章：智能体发展史** 从符号主义到 LLM 驱动的智能体演进，分析各个阶段的核心突破与局限。这部分帮助你在历史脉络中理解当前技术的位置。

**第三章：大语言模型基础** 覆盖 Transformer 架构、提示工程、主流 LLM 及其局限。这里需要理解的是，LLM 是智能体的「大脑」，但大脑本身不能完成行动——这正是智能体框架需要解决的问题。

### 第二部分：构建你的大语言模型智能体（第四章至第七章）

**第四章：智能体经典范式构建** 是本教程的核心章节，手把手实现三种经典范式：

- **ReAct**：推理（Reasoning）与行动（Action）交替进行，让模型在思考下一步做什么的同时，调用工具并根据结果调整策略
- **Plan-and-Solve**：先制定计划再执行，将复杂任务分解为子任务序列，然后逐步完成
- **Reflection**：引入自我反思机制，模型在执行后评估结果质量，必要时回退或调整

这三个范式是理解现代 AI Agent 的基础，几乎所有主流框架（LangChain、AutoGen、AgentScope）都在这些范式上扩展。

**第五章：基于低代码平台的智能体搭建** 介绍 Coze、Dify、n8n 等低代码智能体平台的使用。这些平台适合快速原型验证，但本质是**流程驱动的软件开发**——LLM 充当数据处理后端，而非真正的 AI Native Agent。教程将两者做了明确区分。

**第六章：框架开发实践** 覆盖 AutoGen、AgentScope、LangGraph 等主流框架的应用。这些框架封装了第四章中的经典范式，提供了更高级的抽象，但理解底层范式是正确使用这些框架的前提。

**第七章：构建你的 Agent 框架** 基于 OpenAI 原生 API 从零构建自己的智能体框架。这是对前几章知识的综合应用，目标是让你拥有一个完全可控、不依赖第三方框架的智能体运行时。

### 第三部分：高级知识扩展（第八章至第十二章）

**第八章：记忆与检索** 讲解智能体的记忆系统设计，包括短期的上下文窗口、长期的知识存储，以及 RAG（检索增强生成）在这其中的角色。你会理解为什么「记忆」是让 Agent 区别于单次 LLM 调用的重要因素。

**第九章：上下文工程** 探讨如何在持续交互中维持情境理解。上下文工程不仅包括 prompt 优化，还涉及如何组织对话历史、如何在长程任务中保持焦点。

**第十章：智能体通信协议** 解析 MCP（Model Context Protocol）、A2A（Agent to Agent）、ANP（Agent Network Protocol）等协议。这些协议定义了智能体之间的通信标准，是构建多智能体系统的基础设施。

**第十一章：Agentic RL** 讲解从 SFT（监督微调）到 GRPO（Group Relative Policy Optimization）的 LLM 训练全流程。这是让智能体能够持续自我改进的关键技术，也是当前 Agent 训练的前沿方向。

**第十二章：智能体性能评估** 介绍核心评估指标、基准测试与评估框架。评估是迭代改进的基础，也是你在构建自己的 Agent 系统时必须解决的问题。

### 第四部分：综合案例进阶（第十三章至第十五章）

**第十三章：智能旅行助手** 展示 MCP 与多智能体协作的真实世界应用。你会看到如何将第三章的协议知识用于设计一个实际的多智能体系统——旅行助手需要调用航班 API、天气 API、地图 API，不同 Agent 负责不同模块，通过 MCP 协议通信协作。

**第十四章：自动化深度研究智能体** 复现与解析 DeepResearch Agent，理解如何让 AI 自动完成复杂的信息检索、分析与综合任务。这是当前最接近「AI 研究员」场景的应用之一。

**第十五章：构建赛博小镇** 展示 Agent 与游戏结合的尝试——模拟社会动态的虚拟小镇，每个居民是一个 Agent，有自己的目标、记忆和社会关系。这章是理解多 Agent 交互涌现行为的案例。

### 第五部分：毕业设计（第十六章）

要求读者构建一个完整的多智能体应用，综合运用教程中的所有知识。这是学习闭环——最好的学习方式就是动手实践。

---

## 核心范式详解：ReAct 与 Reflection

### ReAct 的工作原理

ReAct（Reasoning + Acting）的核心循环是：

```
观察（Observation）→ 推理（Reasoning）→ 行动（Action）→ 观察（Observation）→ ...
```

以一个航班查询为例：

1. **观察**：用户说「帮我查一下下周上海到东京的机票」
2. **推理**：这是一个需要调用外部 API 的任务，我需要先确认日期和具体要求
3. **行动**：向用户确认「哪天出发？」或直接调用航班 API（取决于上下文）
4. **观察**：API 返回了结果
5. **推理**：结果显示有 3 个航班可选，我需要总结关键信息呈现给用户

LangChain 的 `AgentType.CONVERSATIONAL_REACT` 和 `AgentType.CHAT_REACT` 都基于这个思路。

### Reflection 的自我改进机制

Reflection 范式引入了一个关键能力：**让 Agent 评估自己的输出质量**。

结构上，Agent 由两个角色组成：
- **Actor**：根据当前状态生成响应或行动
- **Critic**：评估 Actor 的输出，给出改进建议

当 Critic 发现输出不够好时，会触发 Actor 重新生成。这个过程可以迭代，直到输出质量达标或达到最大迭代次数。

实际的实现中，Critic 的评估可以基于：
- 规则检查（格式、安全性等）
- LLM 自我评估（让模型判断答案是否合理）
- 外部工具验证（代码执行结果、API 返回值等）

---

## 通信协议：MCP 与 A2A

### MCP（Model Context Protocol）

MCP 是由 Anthropic 主导的智能体与外部工具之间的通信协议。在 hello-agents 教程中，MCP 是智能旅行助手章节的核心——它定义了 Agent 如何调用外部 API、数据库、文件系统。

MCP 的设计目标：**让智能体与任何数据源或工具的交互标准化**。就像 USB 定义了设备与计算机的物理接口，MCP 定义了 AI Agent 与数字生态系统的交互接口。

关键概念：
- **Host**：AI 应用本身（如 LobeHub）
- **Client**：与远程 MCP Server 通信的客户端
- **Server**：提供工具或数据源的远程服务

一个 MCP Server 可以提供多个 Tool，每个 Tool 有自己的名称、描述和参数定义。Agent 通过标准化的 JSON-RPC 消息调用这些工具。

### A2A（Agent to Agent）

A2A 协议处理智能体之间的直接通信。当多个 Agent 需要协作完成一个复杂任务时，它们需要一个标准来交换状态、分配任务和同步进度。

A2A 解决的核心问题：**多个 Agent 如何在没有一个中心协调者的情况下协作**。这与 MCP 的定位不同——MCP 定义 Agent 与工具的接口，A2A 定义 Agent 与 Agent 的接口。

---

## Agentic RL：让 Agent 自我改进

Agentic RL（Agentic Reinforcement Learning）是将强化学习应用于智能体训练的技术方向。与传统的 SFT（监督微调）不同，Agentic RL 让智能体通过与环境交互获得反馈，然后调整自己的策略。

**GRPO（Group Relative Policy Optimization）** 是当前主流的 Agentic RL 方法之一，其核心思想是：让多个策略变体同时探索，然后比较它们的相对表现，选择表现更好的策略进行扩展。

这个方向的重要性在于：**它让 Agent 能够持续从真实任务中学习，而不是依赖人工标注的数据**。当你部署了一个智能体客服，它每天处理 1000 个对话，Agentic RL 可以让这个智能体从这 1000 个对话的结果中持续改进自己的表现。

---

## 综合案例：智能旅行助手

智能旅行助手是教程中最完整的实战案例。它展示了如何将多个 Agent、多个工具和 MCP 协议组合成一个真正可用的系统。

**系统架构**：

```
用户界面
    ↓
┌────────────────────────────────────────────┐
│           Orchestrator Agent               │
│  (负责任务分解、结果汇总、用户交互)        │
└────────────────────────────────────────────┘
    ↓                    ↓                    ↓
┌────────────┐   ┌────────────┐   ┌────────────┐
│ Flight Agent│   │ Hotel Agent│   │ Weather Agent│
│  (航班查询) │   │  (酒店预订)│   │  (天气查询) │
└────────────┘   └────────────┘   └────────────┘
         ↓               ↓               ↓
    MCP Server       MCP Server       MCP Server
    (航班API)        (酒店API)       (天气API)
```

Orchestrator 收到用户请求后，先分析任务类型，然后并行调用 Flight Agent、Hotel Agent 和 Weather Agent。每个子 Agent 通过自己的 MCP Server 连接外部 API，获取数据后返回给 Orchestrator，由 Orchestrator 汇总结果后呈现给用户。

---

## 学习建议

### 适合人群

- 已掌握 Python 基础，想要系统学习 AI Agent 开发
- 了解 LLM 基础概念（如 ChatGPT 使用），想进一步理解 Agent 原理
- 正在使用 Dify/Coze 等平台，想从「使用者」升级为「构建者」

### 前置知识

教程假设读者有基本的 Python 编程能力，对 LLM 有基础了解。如果你不熟悉 Python 或从未使用过 LLM API，建议先补充这些基础。

### 学习路径建议

1. **第一遍**：通读全部章节，建立整体认知
2. **第二遍**：重点完成第四章（ReAct/Reflection）和第十章（MCP/A2A协议），这是理解后续内容的基础
3. **第三遍**：选择一个综合案例（第十三或第十四章），从零构建一遍
4. **第四遍**：基于第十六章毕业设计要求，开发自己的多智能体应用

---

## 总结

hello-agents 提供了从理论到实践的完整智能体学习路径。它的核心价值在于：

1. **系统性**：不是零散的工具介绍，而是从原理到框架、从单 Agent 到多 Agent 的完整知识体系
2. **实践导向**：每个章节都有可运行的代码，理论之后立即有实践验证
3. **中文友好**：完全中文编写，降低了技术概念的理解门槛
4. **持续更新**：Datawhale 社区维护，遇到问题可以在 GitHub 提 Issue

对于想要深入理解 AI Agent 并具备构建能力的技术人员，hello-agents 是目前中文社区最完整的教程之一。

**延伸阅读**：

- GitHub 仓库：https://github.com/datawhalechina/hello-agents
- 在线阅读（国际版）：https://datawhalechina.github.io/hello-agents/
- 在线阅读（国内加速）：https://hello-agents.datawhale.cc
- PDF 下载：https://github.com/datawhalechina/hello-agents/releases/latest/
- Datawhale 官网：https://datawhale.cn/