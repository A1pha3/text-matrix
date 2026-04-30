---
title: "OpenAI GPT-5.5 Prompt 指南：更短、目标导向的提示词设计新范式"
date: 2026-05-01T00:52:39+08:00
slug: "openai-gpt-5-5-prompt-guide"
description: "OpenAI 官方 GPT-5.5 提示词设计指南解读，涵盖结果优先提示词、停止条件、人格与协作风格、前置语、引用预算等核心原则，帮助开发者从流程堆砌式提示词迁移到更高效的目标导向范式。"
draft: false
categories: ["技术笔记"]
tags: ["OpenAI", "GPT-5.5", "提示词工程", "Prompt Engineering", "AI Agent"]
---

# OpenAI GPT-5.5 Prompt 指南：更短、目标导向的提示词设计新范式

GPT-5.5 带来了提示词设计范式的根本转变。

OpenAI 官方文档 [Prompt guidance](https://developers.openai.com/api/docs/guides/prompt-guidance) 明确指出：GPT-5.5 与前代模型最大的区别在于——它更擅长自主选择解题路径，而非按部就班执行预设流程。这意味着传统的"步骤堆砌式"提示词反而可能限制模型发挥、增加噪声，甚至导致答案过于机械。

本文基于该文档，梳理 GPT-5.5 提示词设计的核心原则与推荐结构。

---

## 1. 核心变化：从"过程导向"到"结果导向"

### 1.1 为什么旧范式不再适用

早期模型需要大量过程指令来保持任务不偏离轨道，于是"总是检查 X，然后再检查 Y，最后再……"这类提示词大行其道。GPT-5.4 及之后的模型已经足够强大，可以自主规划路径，过度的过程约束反而让模型搜索空间变窄、输出变得机械。

### 1.2 新范式的核心逻辑

> **描述目标，而非步骤。告诉模型"好的答案长什么样"，让它自己找到路径。**

好的提示词应包含：
- **目标结果**：最终答案需要达成什么
- **成功标准**：什么条件下可以停止
- **约束条件**：真正的 invariants（安全规则、必要输出字段）
- **可用上下文**：模型可以利用的信息

❌ 不推荐（过程堆砌）：
```
First inspect A, then inspect B, then compare every field,
then think through all possible exceptions, then decide
which tool to call, then call the tool, then explain...
```

✅ 推荐（结果导向）：
```
Resolve the customer's issue end to end.

Success means:
- eligibility decision is made from available policy and account data
- any allowed action is completed before responding
- final answer includes completed_actions, customer_message, and blockers
- if evidence is missing, ask for the smallest missing field
```

---

## 2. 停止条件（Stopping Conditions）

结果导向提示词需要配套明确的停止规则，否则模型可能在找到答案后继续发散。

### 2.1 核心停止条件模板

```
Resolve the user query in the fewest useful tool loops,
but do not let loop minimization outrank correctness,
accessible fallback evidence, calculations, or required
citation tags for factual claims.

After each result, ask: "Can I answer the user's core request
now with useful evidence and citations for the factual claims?"
If yes, answer.
```

### 2.2 缺失证据行为定义

```
Use the minimum evidence sufficient to answer correctly,
cite it precisely, then stop.
```

### 2.3 使用决策规则而非绝对指令

| 场景 | 用 MUST/ALWAYS（真 invariants） | 用 Decision Rules（判断场景） |
|------|------|------|
| 安全规则 | ✅ | |
| 必要输出字段 | ✅ | |
| 何时搜索 | | ✅ 建议用决策规则 |
| 何时迭代 | | ✅ |
| 何时问用户 | | ✅ |

---

## 3. 人格与协作风格（Personality & Collaboration Style）

GPT-5.5 的默认风格是高效、直接、任务导向的。但对于客服、辅导、对话类产品，需要显式定义人格。

### 3.1 人格块（Personality）

人格控制模型如何"说话"——语调、温度、直接程度、正式程度、幽默感、同理心、修辞水平。

**任务导向型人格示例：**

```markdown
# Personality
You are a capable collaborator: approachable, steady, and direct.
Assume the user is competent and acting in good faith, and respond
with patience, respect, and practical helpfulness.

Prefer making progress over stopping for clarification when the request
is already clear enough to attempt. Use context and reasonable
assumptions to move forward. Ask for clarification only when the
missing information would materially change the answer or create
meaningful risk, and keep any question narrow.

Stay concise without becoming curt. Give enough context for the user
to understand and trust the answer, then stop. Use examples, comparisons,
or simple analogies when they make the point easier to grasp.
```

**表达型协作人格示例：**

```markdown
# Personality
Adopt a vivid conversational presence: intelligent, curious, playful
when appropriate, and attentive to the user's thinking. Ask good
questions when the problem is blurry, then become decisive once there
is enough context.

Be warm, collaborative, and polished. Conversation should feel easy and
alive, but not chatty for its own sake. Offer a real point of view
rather than merely mirroring the user, while staying responsive to
their goals and constraints.
```

### 3.2 协作风格（Collaboration Style）

协作风格控制模型如何"工作"：何时提问、何时做假设、多主动、提供多少上下文、何时检查工作、如何处理不确定性和风险。

> **保持简短**：人格指令塑造用户体验，协作指令塑造任务行为。两者都不能替代清晰的目标、成功标准、工具规则或停止条件。

---

## 4. 前置语（Preamble）：提升首 token 可见速度

在流式应用中，用户等待首响应的感知时间非常重要。对于多步骤或工具密集型任务，GPT-5.5 可能先进行推理、规划或准备工具调用，这期间没有可见输出。

### 4.2 推荐模式

对于工具密集型工作流，让模型先发送一条简短可见的前置语：

```
Before any tool calls for a multi-step task, send a short user-visible
update that acknowledges the request and states the first step.
Keep it to one or two sentences.
```

对于暴露独立消息阶段的编码 Agent，可以更明确：

```
You must always start with an intermediary update before any content
in the analysis channel if the task will require calling tools.
The user update should acknowledge the request and explain your first step.
```

---

## 5. 引用预算（Retrieval Budget）

引用预算是搜索的停止规则，告诉模型什么时候"足够好了"。

### 5.1 核心原则

对于普通问答，从一个简短、判别性关键词的宽泛搜索开始。如果顶部结果已经包含足够支撑核心请求的可引用证据，直接回答，而不是再次搜索。

### 5.2 需要再次检索的条件

仅在以下情况发起新的检索：
- 顶部结果不能回答核心问题
- 缺少必需的事实、参数、owner、日期、ID 或来源
- 用户要求穷尽性覆盖、对比或完整列表
- 必须读取特定文档、URL、邮件、会议、记录或代码产物
- 答案将包含重要的无支撑事实性声明

### 5.3 不应再次检索的场景

- 为了改善措辞
- 添加示例
- 引用非必要的细节
- 支撑可以更泛化表述的无风险措辞

---

## 6. 创意起草的护栏（Creative Drafting Guardrails）

对于需要创意起草的任务（PPT、推广文案、客户摘要等），明确区分哪些内容必须来自来源，哪些可以创意发挥。

```
For creative or generative requests such as slides, leadership blurbs,
outbound copy, summaries for sharing, talk tracks, or narrative framing:

- Use retrieved or provided facts for concrete product, customer, metric,
  roadmap, date, capability, and competitive claims, and cite those claims.
- Do not invent specific names, first-party data claims, metrics, roadmap
  status, customer outcomes, or product capabilities to make the draft
  sound stronger.
- If there is little or no citable support, write a useful generic draft
  with placeholders or clearly labeled assumptions rather than
  unsupported specifics.
```

---

## 7. Phase 参数

GPT-5.4 开始，长时间运行或工具密集型的 Responses 工作流可以使用 `phase` 参数区分中间更新和最终答案。GPT-5.5 延续此模式。

如果使用 `previous_response_id`，API 自动保留先前的 assistant 状态。如果应用程序手动将 assistant 输出项重放到下一个请求，需保留每个原始 `phase` 值不变。

| Phase 值 | 用途 |
|---------|------|
| `phase: "commentary"` | 中间用户可见更新 |
| `phase: "final_answer"` | 已完成的最终答案 |

---

## 8. 推荐的提示词结构模板

以下是复杂提示词的推荐起始结构，每个部分保持简短，只有在会改变行为时才添加细节。

```markdown
Role: [1-2 sentences defining the model's function, context, and job]

# Personality
[tone, demeanor, and collaboration style]

# Goal
[user-visible outcome]

# Success criteria
[what must be true before the final answer]

# Constraints
[policy, safety, business, evidence, and side-effect limits]

# Output
[sections, length, and tone]

# Stop rules
[when to retry, fallback, abstain, ask, or stop]
```

---

## 9. 总结：GPT-5.5 提示词设计核心要点

| 原则 | 说明 |
|------|------|
| **结果优先于过程** | 描述目标，不描述步骤 |
| **用停止条件代替过程约束** | 明确的成功标准和停止规则 |
| **决策规则代替绝对指令** | MUST/ALWAYS 仅用于真 invariants |
| **人格和协作风格要显式定义** | 客服和对话类产品特别重要 |
| **前置语提升感知响应速度** | 长任务先发送可见更新 |
| **引用预算控制搜索次数** | 足够即止，避免过度检索 |
| **创意内容加护栏** | 事实用来源，创意加标注 |
| **保留 Phase 参数** | 工具密集型工作流的中间态标识 |

**官方文档**：[Prompt guidance | OpenAI API](https://developers.openai.com/api/docs/guides/prompt-guidance)
