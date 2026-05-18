---
title: "12-Factor Agents：构建可投产 AI 应用的全方位工程原则"
date: "2026-05-18T21:10:00+08:00"
slug: "12-factor-agents-llm-production-principles"
description: "12-factor-agents 是 GitHub 20k+ stars 的热门项目，它没有造轮子，而是系统总结了一套构建生产级 LLM 软件的设计原则。本文从核心判断入手，逐因子深度解析其原理与实践，助你从 demo 跨越到真正可交付用户的 AI 产品。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "LLM", "工程实践", "上下文工程", "TypeScript"]
---

用 LLM 做产品，很多人容易掉进两个坑：要么迷信「给个 prompt、加一堆工具、循环到目标达成」的万能 Agent 范式；要么把 LLM 当成增强搜索，塞进一堆 if-else 里。

Dex（humanlayer/12-factor-agents 作者）的观察是：**真正能交付给生产用户的 LLM 软件，大多数不是纯 Agent，而是软件 + LLM 步骤的混合体**——好的 AI 产品，本质是软件，只是恰好在某些关键节点引入了 LLM。

这套洞察，被他系统化成了一份指南，就是 **12-Factor Agents**。目前已在 GitHub 斩获 **20.3k stars**、**1.5k forks**，并附有视频讲解、Discord 社区和 `npx/uvx create-12-factor-agent` 脚手架。

---

## 核心判断

> **12-factor-agents 是一套 LLM 应用工程化的设计原则体系，而非框架。它的核心命题是：如何从 demo 质量（70-80%）跨越到真正可交付生产用户的质量。**

这个判断基于三个事实：

1. **好 Agent 的本质是软件，不是 LLM**：真正在生产环境跑 AI Agent 的团队，大多数是自己造轮子，而非依赖某个框架（YC 创始人访谈中反复出现的模式）。
2. **"Prompt + 工具 + 循环"范式不够用**：Anthropic 在 [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents#agents) 中也承认，那种"给 LLM 一袋工具、让它自己 loop"的模式在生产环境中表现不佳。
3. **模块化原则比框架更重要**：把 Agent 开发的最佳实践拆解成独立原则，比提供一个新框架更有价值——工程师可以把它们自由组合进现有产品，而不是全量迁移。

---

## 系统地图：12 个原则一览

| Factor | 主题 | 一句话总结 |
|--------|------|------------|
| **1** | Natural Language to Tool Calls | 自然语言 → 结构化工具调用，是 Agent 的原子操作 |
| **2** | Own your prompts | 提示词是自己的资产，不要交给框架黑盒注入 |
| **3** | Own your context window | 上下文窗口是核心工程对象，不是"塞进去就行"的资源 |
| **4** | Tools are just structured outputs | 工具调用本质是结构化输出，不是魔法 |
| **5** | Unify execution and business state | 执行状态和业务状态应该统一建模 |
| **6** | Launch/Pause/Resume with simple APIs | 暂停/恢复能力是生产级 Agent 的基本要求 |
| **7** | Contact humans with tool calls | 复杂决策应能主动联系人类，而非卡死或乱跑 |
| **8** | Own your control flow | 控制流是软件的职责，不是 LLM 的 |
| **9** | Compact Errors into Context | 错误信息应压缩进上下文，而非打断工作流 |
| **10** | Small, Focused Agents | 小而专注的 Agent 比大一统 Agent 更可靠 |
| **11** | Trigger from anywhere | 从任意地方触发，在用户所在的地方相遇 |
| **12** | Make your agent a stateless reducer | 把 Agent 做成无状态 reducer，便于推理和调试 |
| **Bonus** | Pre-fetch all the context | 在用户请求前预取所有可能需要的上下文 |

---

## 从代码到 DAG，再到 Agent Loop

理解 12 个原则之前，需要先理解 Dex 的一个核心框架：**软件 → DAG → Agent Loop** 的演化逻辑。

### 软件即有向图

程序本质是有向图（Directed Graph）。20 年前，DAG 编排器开始流行（Airflow、Prefect、Dagster、Inngest、Windmill），带来了可观测性、模块化、重试、管理界面等工程保障。

### Agent 的承诺

Agent 的出现带来一个承诺：**扔掉 DAG，让 LLM 决定路径**。工程师只给 LLM 提供"边"（edges），让模型自己在运行时决定"节点"（nodes）。理论上：写更少代码，LLM 找Novel解，可恢复错误。

### Agent Loop 的三步

但这个承诺没有完全兑现。实际上，Agent Loop 是这样的：

```python
initial_event = {"message": "..."}
context = [initial_event]

while True:
    next_step = await llm.determine_next_step(context)
    context.append(next_step)

    if next_step.intent == "done":
        return next_step.final_answer

    result = await execute_step(next_step)
    context.append(result)
```

三步循环：
1. LLM 决定下一步（结构化输出 / "tool calling"）
2. 确定性代码执行工具调用
3. 结果追加进上下文窗口
4. 重复，直到 LLM 判断"完成"

### 70-80% 质量墙

问题在于，这套模式**通常只能做到 70-80% 的质量**，而 customer-facing 功能通常需要更高水准。Dex 在构建 HumanLayer 时访谈了 100+ SaaS 创始人，他们的共同路径是：

1. 决定做 Agent → 产品设计 → 拿框架快速开发 → 达到 70-80% 质量
2. 发现 80% 对客户场景不够用
3. 开始逆向工程框架的 prompts、flow、机制
4. 从头重写

这正是 12-factor-agents 要解决的问题：**不是再做一个框架，而是把好 Agent 的工程原则提炼出来，让工程师不必从零摸索**。

---

## 逐因子深度解析

### Factor 1：Natural Language to Tool Calls

**核心观点**：把用户的一句话需求，转换为结构化工具调用对象，是 Agent 的原子操作。

例如，用户说：

> "create a payment link for $750 to Terri for sponsoring the february AI tinkerers meetup"

Agent 应该输出：

```json
{
  "function": {
    "name": "create_payment_link",
    "parameters": {
      "amount": 750,
      "customer": "cust_128934ddasf9",
      "product": "prod_8675309",
      "price": "prc_09874329fds",
      "quantity": 1,
      "memo": "Hey Terri - see below for the payment link for the february AI tinkerers meetup"
    }
  }
}
```

之后确定性代码接手：

```python
next_step = await llm.determineNextStep(
    "create a payment link for $750 to Terri "
    "for sponsoring the february AI tinkerers meetup"
)

if next_step.function == 'create_payment_link':
    stripe.paymentlinks.create(next_step.parameters)
    return
```

注意：这里故意**跳过了 Agent 向用户返回自然语言结果的步骤**——这属于后续 Factor 的职责，Factor 1 只解决"自然语言 → 结构化调用"的转换问题。

---

### Factor 2：Own your prompts

**核心观点**：提示词是工程资产，不是框架的注入黑盒。

当你在生产环境调试 Agent 行为时，你需要能够精确控制每一条指令。框架通常会在你不知情的情况下注入 system prompt（角色设定、行为约束等），这会导致：

- 行为不稳定：框架更新后，Agent 行为改变
- 难以复现：同样的输入，不同的行为
- 调试困难：不知道哪条规则来自哪里

Own your prompts 的意思是：**把提示词当成第一公民的代码资产，用 Git 管理，在代码中显式声明**。

---

### Factor 3：Own your context window

**核心观点**：上下文窗口是核心工程对象，需要精心构建，而不是"塞进去就行"的资源。

这是 12 个 Factor 中被强调最多的一条，也是 Context Engineering（上下文工程）领域的核心议题。

#### 标准消息格式 vs 自定义格式

大多数 LLM 客户端默认使用标准消息格式：

```json
[
  {"role": "system", "content": "You are a helpful assistant..."},
  {"role": "user", "content": "Can you deploy the backend?"},
  {
    "role": "assistant",
    "content": null,
    "tool_calls": [{"id": "1", "name": "list_git_tags", "arguments": "{}"}]
  },
  {
    "role": "tool",
    "name": "list_git_tags",
    "content": "{\"tags\": [{\"name\": \"v1.2.3\", \"commit\": \"abc123\"}]}",
    "tool_call_id": "1"
  }
]
```

但如果你想**真正压榨模型的能力**，需要把上下文打包成对任务最友好的格式。12-factor-agents 建议使用 XML 风格的自定义格式：

```python
# 用事件列表构建线程
class Thread:
    events: List[Event]

class Event:
    type: Literal["list_git_tags", "deploy_backend", ...]
    data: Any

def event_to_prompt(event: Event) -> str:
    data = event.data if isinstance(event.data, str) else stringifyToYaml(event.data)
    return f"<{event.type}>\n{data}\n</{event.type}>"

def thread_to_prompt(thread: Thread) -> str:
    return '\n\n'.join(event_to_prompt(e) for e in thread.events)
```

这样，每个上下文窗口都类似：

```xml
<slack_message>
    From: @alex
    Channel: #deployments
    Text: Can you deploy the latest backend to production?
</slack_message>

<list_git_tags_result>
    tags:
      - name: "v1.2.3"
        commit: "abc123"
      - name: "v1.2.2"
        commit: "def456"
</list_git_tags_result>

what's the next step?
```

上下文工程还包括：
- RAG（检索增强生成）
- 记忆（相关但独立会话的历史）
- Schema 对齐解析（BAML 等工具）

**关键**：你需要对上下文的构建方式拥有完全控制权，才能持续优化 token 效率和注意力分配。

---

### Factor 4：Tools are just structured outputs

**核心观点**：工具调用本质是 LLM 的结构化输出，不是 Agent 独有的魔法。

Function Calling / Structured Outputs / JSON Mode 都是实现这一能力的不同技术路径。工具调用并不意味着"有 Agent 在运行"，它只是 LLM 输出结构化数据的一种形式。

这把 Agent 的复杂性解开了：当你给 LLM 一个工具时，你只是在要求它以特定格式输出数据；执行工具的是确定性代码，不是 LLM 本身。

---

### Factor 5：Unify execution and business state

**核心观点**：Agent 的执行状态和业务状态应该统一建模，而不是分开管理。

典型问题：Agent 内部有一个"执行历史"（哪些步骤已完成），同时业务数据库里有另一个"业务状态"（订单状态、用户资料等）。维护两套状态的同步是 Bug 的温床。

更好的做法：**把执行状态也当成业务状态的一部分**，使用单一数据源来描述"任务当前在哪里、业务当前是什么状态"。

---

### Factor 6：Launch/Pause/Resume with simple APIs

**核心观点**：Agent 必须支持暂停和恢复，这是生产级可靠性的基础。

场景举例：
- Agent 需要用户批准才能继续
- Agent 需要等待外部 webhook
- Agent 进程需要重启恢复

实现方式：把 Agent 执行状态序列化，通过简单 API 存储/恢复。Factor 5（统一状态）是实现这一条的技术前提。

---

### Factor 7：Contact humans with tool calls

**核心观点**：当 Agent 遇到无法自主决策的情况时，应该能主动联系人类，而不是卡死或乱猜。

实现方式：把"联系人类"也建模为一个工具调用——`contact_human(reason="需要批准折扣", context=...)`。这让整个流程保持一致性：Agent 通过同一套工具调用机制与人类交互，而不是引入额外的异常处理逻辑。

---

### Factor 8：Own your control flow

**核心观点**：控制流（什么时候做什么）是软件的职责，不是 LLM 的。

好的 LLM 应用不是"把控制权完全交给模型"，而是：**软件定义骨架（骨架 = 控制流），模型填充细节（细节 = 内容生成和决策）**。

类比：工作流引擎编排 Agent，而不是 Agent 自己 loop 到天荒地老。DAG 回来了——但这一次，节点是 LLM 调用，边是确定性代码。

---

### Factor 9：Compact Errors into Context Window

**核心观点**：错误信息应该被压缩进上下文窗口，而不是打断工作流。

传统做法：Agent 出错 → 抛异常 → 中断 → 人工介入。

更好的做法：Agent 出错 → 把错误压缩进上下文 → 继续 loop → 让模型决定如何处理。

压缩方式：把原始错误转换为摘要描述（错误类型 + 关键参数 + 影响范围），而不是把整个 stack trace 塞进 context window。

---

### Factor 10：Small, Focused Agents

**核心观点**：小而专注的 Agent 比大一统的"通用 Agent"更可靠、更可预测。

这与软件工程中的单一职责原则（SRP）一脉相承。一个 Agent 如果同时做"处理支付 + 回答用户问题 + 写报告"，它每个环节都会做得更差。

实践中：
- 按功能域拆分 Agent（支付 Agent、客服 Agent、报告 Agent）
- 每个 Agent 有清晰的输入/输出契约
- 通过消息总线或共享状态协调

---

### Factor 11：Trigger from anywhere, meet users where they are

**核心观点**：Agent 的触发源应该是多元的（webhook、cron、用户消息、API），并且在用户所在的地方（slack、邮件、UI）交付结果，而不是强制用户适应 Agent 的接口。

这是现代产品体验的要求：**用户不需要知道背后有 Agent，他们只需要结果**。

---

### Factor 12：Make your agent a stateless reducer

**核心观点**：把 Agent 建模为无状态 reducer（`状态 + 输入 → 新状态`），而不是有记忆的活物。

无状态 reducer 的好处：
- **可测试**：给定相同状态和输入，总是有相同输出
- **可回放**：可以重放任何历史状态
- **可推理**：整个执行轨迹是确定性的，不存在"Agent 脑子里在想什么"的模糊空间
- **可并行**：同一状态可以 fork 出多个并行执行路径

```python
# Agent = pure function (reducer)
def agent_step(state: State, event: Event) -> State:
    """给定当前状态和事件，返回新状态"""
    next_step = llm.determine_next_step(state.context)
    if next_step.is_tool_call:
        result = execute_tool(next_step.tool, next_step.args)
        return state.append(event=result)
    elif next_step.is_done:
        return state.mark_done(final_answer=next_step.answer)
    else:
        return state  # no change
```

---

### Factor 13（荣誉提及）：Pre-fetch all the context

**核心观点**：在用户发出请求之前，就预取所有可能需要的上下文。

这与 Web 性能优化中的"预加载"思路一致。例如：当用户开始填写表单时，后台 Agent 可以预取该用户的历史记录、相关文档等；当用户提交时，Agent 已经拥有完整上下文，响应更快、更准确。

---

## 为什么这些原则值得重视

### 从框架到原则的范式转换

大多数 Agent 框架（LangChain、Langraph、CrewAI 等）提供了完整的运行时和抽象层。使用它们可以快速启动，但当需要精细控制时，你往往发现自己在大规模逆向工程框架的内部机制。

12-factor-agents 的价值在于：**它不提供框架，而是告诉你好框架为什么好、差框架为什么差，以及你自己实现时应该注意什么**。

这与 12-Factor App（Heroku 提出的 Web 应用开发原则）对 Web 开发的影响类似——不是强制规范，而是经过验证的设计哲学。

### 适用人群

| 人群 | 适合度 |
|------|--------|
| 正在从 0 到 1 构建 AI 产品的工程师 | ★★★★★ |
| 已在用框架但遇到质量瓶颈的团队 | ★★★★★ |
| 想在现有产品中引入 AI 能力的开发者 | ★★★★☆ |
| AI 研究者 / 框架开发者 | ★★★★☆ |
| 完全没有编程经验的 AI 爱好者 | ★★☆☆☆ |

### 不覆盖什么

- **MCP（Model Context Protocol）**：作者明确表示 MCP 是另一个话题，12-factor-agents 不讨论它，但可以看到 MCP 在其中如何对应。
- **各框架的深度对比**：本文聚焦原则，不做 LangChain vs Langraph vs CrewAI 的功能对比。
- **模型训练 / Fine-tuning**：12-factor-agents 假设使用的是现有模型，专注于工程层面的优化。

---

## 快速上手

项目提供了 `npx/uvx create-12-factor-agent` 脚手架，可以快速生成符合这些原则的 Agent 项目骨架：

```bash
# npm
npx create-12-factor-agent

# uv (Python)
uvx create-12-factor-agent
```

配套资源：
- [AI Engineer World's Fair 演讲视频](https://www.youtube.com/watch?v=8kMaTybvDUw)
- [Deep Dive 视频](https://www.youtube.com/watch?v=yxJDyQ8v6P0)
- [Discord 社区](https://humanlayer.dev/discord)
- [The Outer Loop 博客](https://theouterloop.substack.com)
- [got-agents/agents](https://github.com/got-agents/agents)：用此方法论构建的开源 Agent

---

## 总结

12-factor-agents 的核心一句话：**好的 LLM 产品，是软件，只是在关键节点引入了 LLM**。

如果你正在构建 AI 产品，遇到了"质量瓶颈"——从 70-80% 向生产级跨越的困难——这套原则值得你认真研究。它不能帮你绕过工程工作，但能帮你把工程工作做对方向。

> **项目地址**：[https://github.com/humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents）
> **内容许可**：CC BY-SA 4.0 | **代码许可**：Apache 2.0
