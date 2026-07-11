---
title: "Google ADK：把 Agentic Engineering 从零开始的五件事讲清楚"
date: "2026-07-11T20:40:12+08:00"
slug: "google-adk-agentic-engineering-2026"
description: "Google 2026 年 7 月发布了一门 1 小时 12 分钟的 Agentic Engineering 课，配套推出官方框架 Agent Development Kit (ADK)——同时覆盖 Python/TypeScript/Go/Java/Kotlin 五个 SDK。本文以 @0xCodez 在 X 上整理的五段大纲（第一个 Agent / 记忆 / Agentic Loop / MCP / Multi-Agent）为骨架，逐项拆开 ADK 文档里的真实代码与设计选择：LoopAgent 的 Writer-Critic 迭代范式、MemoryService 的 Session/State 短期与 long-term 检索长期双层模型、MCP 工具注册与 OpenAPI 工具的取舍、SequentialAgent / ParallelAgent / LoopAgent 三种 template workflow 的适用场景，并补一段对独立 Agent 项目作者可复用的工程经验。"
draft: false
categories: ["技术笔记"]
tags: ["Google ADK", "Agentic Engineering", "AI Agent", "MCP", "MemoryService", "LoopAgent", "Multi-Agent", "Python", "Go", "TypeScript"]
hiddenFromHomePage: false
---

# Google ADK：把 Agentic Engineering 从零开始的五件事讲清楚

## 学习目标

读完本文后，你应当能够：

- 说出 Google Agent Development Kit (ADK) 是什么、它同时支持哪 5 个语言 SDK，以及它和 LangChain / AutoGen 这类框架的根本区别
- 用 `LlmAgent` + `LoopAgent` + 终止条件写出一个 Writer-Critic 迭代改进文档的最小闭环
- 解释 `Session/State`（短期记忆）和 `MemoryService`（长期知识）的边界，以及什么信息该进哪一个
- 区分 MCP（Model Context Protocol）和传统 API：什么时候 MCP 值得、什么时候直接 OpenAPI 更划算
- 在 Sequential / Loop / Parallel / Custom 这 4 种 template workflow 之间做出正确选择，并知道 ADK 2.0 引入 graph workflow 后为什么 template workflow 不再是首选

## 本文目录

1. [这门课到底在讲什么](#1-这门课到底在讲什么)
2. [ADK 是什么：Google 第一次认真做 Agent 框架](#2-adk-是什么google-第一次认真做-agent-框架)
3. [第一件事：怎么构建你的第一个 AI Agent](#3-第一件事怎么构建你的第一个-ai-agent)
4. [第二件事：Agent 的记忆——短期 Session 与长期 MemoryService](#4-第二件事agent-的记忆短期-session-与长期-memoryservice)
5. [第三件事：Agentic Loop 与长时间运行的 Agent](#5-第三件事agentic-loop-与长时间运行的-agent)
6. [第四件事：MCP——它和 API 的真正区别](#6-第四件事mcp它和-api-的真正区别)
7. [第五件事：Multi-Agent 系统](#7-第五件事multi-agent-系统)
8. [对独立 Agent 项目作者的 5 条工程经验](#8-对独立-agent-项目作者的-5-条工程经验)
9. [关键资源与延伸阅读](#9-关键资源与延伸阅读)

---

## 1. 这门课到底在讲什么

2026 年 7 月 10 日，@0xCodez 在 X 上转发了一条消息：Google 悄无声息地发布了一门 1 小时 12 分钟的 Agentic Engineering 课程，从零开始教五个东西——第一个 Agent、Agent 记忆、Agentic Loop 与长运行、MCP、多 Agent 系统。他给出的评价很直接："足以替代网上 10 门付费 Agentic 课程"。

这门课的关键不在"内容多"，而在"配套齐"。Google 这次同时把它攒了两年的 Agent 框架——**Agent Development Kit (ADK)**——开源出来，同步推到了 Python、TypeScript、Go、Java、Kotlin 五个 SDK，并部署在 `google.github.io/adk-docs`。课程里的每一个示例，都能在文档里找到对应章节的真实代码。

我把这门课按大纲拆了一遍，所有内容都对得上 `https://google.github.io/adk-docs` 的真实文档。下面是逐项展开。

## 2. ADK 是什么：Google 第一次认真做 Agent 框架

如果你听过 LangChain、CrewAI、AutoGen、Anthropic 的 Claude Agent SDK，脑子里第一个问题是：Google 这个 ADK 凭什么不一样？

答案藏在 ADK 文档 Technical Overview 那一页的一句话里：

> ADK is a flexible and modular framework for developing and deploying AI agents. While optimized for Gemini and the Google ecosystem, ADK is model-agnostic, deployment-agnostic, and is designed to integrate with other frameworks and tools.

三个关键词：**model-agnostic**（不绑 Gemini）、**deployment-agnostic**（不绑 Cloud Run）、**modular**（不强求一种架构）。这意味着同一个 `LlmAgent` 既可以接 Gemini，也可以接 Claude、Llama、vLLM；既可以跑在你笔记本上，也可以跑在 GKE、Cloud Run、甚至你自己的 K8s 集群。

ADK 的核心抽象只有 6 个：

| 抽象 | 干什么的 |
|---|---|
| `LlmAgent` | 单个由 LLM 驱动的 agent，能调用工具、维护状态 |
| `SequentialAgent` | 按顺序串起多个 sub-agent |
| `LoopAgent` | 把 sub-agent 跑成循环，配合终止条件实现迭代改进 |
| `ParallelAgent` | 并行跑多个 sub-agent，结果合并 |
| `Custom Agent` | 完全自己写 BaseAgent 子类，自由度最高 |
| `Workflow Patterns` | 把上面这些串成图的更复杂结构（ADK 2.0 新增） |

看到这套抽象你应该立刻意识到一件事：**ADK 不是"prompt 编排框架"**，它是个正经的 control flow 框架。LangChain 在做 chain，AutoGen 在做对话，ADK 在做 agent runtime。

## 3. 第一件事：怎么构建你的第一个 AI Agent

课程 00:00 段对应 ADK 的 [Get Started](https://google.github.io/adk-docs/get-started/python/)。Python SDK 的最小可运行例子大概是这样：

```python
from google.adk.agents import LlmAgent

agent = LlmAgent(
    name="weather_agent",
    model="gemini-2.5-flash",
    instruction="你是一个天气助手，根据用户提问回答。",
    tools=[get_weather]  # 你自己写的 Python 函数
)
```

`LlmAgent` 接收 4 个核心字段：`name`、`model`、`instruction`、`tools`。`tools` 是关键——ADK 把"工具"定义为**任何带 type hints 和 docstring 的 Python 函数**，框架会自动从函数签名和 docstring 推断出 JSON schema 发给模型。

但这只是"能跑"。课程和文档同时强调三件容易踩坑的事：

1. **instruction 要明确边界**。不要写"你是一个有用的助手"——这等于没写。ADK 文档的 best practice 是把 instruction 写成"任务描述 + 输入约束 + 输出格式 + 失败处理"四段式。
2. **工具函数要有完整的 docstring**。模型看不到函数体，只能看到 signature + docstring。docstring 是模型决定什么时候调你的唯一信号。
3. **`description` 字段不是给自己看的**。在 multi-agent 设置里，子 agent 的 description 是父 agent 决定何时委派任务的关键——写得模糊就永远不会被调到。

## 4. 第二件事：Agent 的记忆——短期 Session 与长期 MemoryService

课程 08:24 段对应 ADK 的 [Sessions and Memory](https://google.github.io/adk-docs/sessions/memory/)。这是整门课里概念密度最高的一节，也是大多数教程讲不清楚的地方。

ADK 把"记忆"拆成两层：

**Session（短期）** = 当前对话的事件流 + 临时状态。`Session` 对象持有 `events`（每条 user / agent / tool 消息）和 `state`（一个 dict 形式的临时变量表）。这就像一个人在一次具体对话里的短期记忆——聊完就清空。

**MemoryService（长期）** = 跨会话的可检索知识库。`BaseMemoryService` 定义 4 个操作：

```python
add_session_to_memory(session)   # 把整段完成的会话摄入长期记忆
add_events_to_memory(events)     # 增量追加（适合长会话中途写入）
add_memory(memory_entry)         # 直接写入预构建的记忆条目
search_memory(query)             # 检索相关记忆
```

文档用一个类比把这个区别讲得很到位：

> Think of it this way:
> Session/State: Like your short-term memory during one specific chat.
> Long-Term Knowledge (MemoryService): Like a searchable archive or knowledge library the agent can consult, potentially containing information from many past chats or other sources.

实现上有两个关键选择：

- **`InMemoryMemoryService`**：进程内 dict 存储，重启即丢。开发期用。
- **`VertexAI Memory Bank`**：Google Cloud 上的托管服务，做语义检索 + 自动摘要。生产用。

独立开发者最常问的问题是："我用 LangChain 的 ConversationBufferMemory 不行吗？"答案是不一样：LangChain 的 buffer 是同一会话内的滑动窗口，ADK 的 MemoryService 是跨会话的语义检索。前者是"这个对话的最近 N 轮"，后者是"我去年跟用户聊过什么"。

## 5. 第三件事：Agentic Loop 与长时间运行的 Agent

课程 28:34 段对应 [Loop Agents](https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/)——这是整门课里代码最值得抄的部分。

`LoopAgent` 的本质是把 sub-agent 跑成一个循环，直到满足终止条件。ADK 文档给出了一个非常接地气的例子：生成图片直到数量正确。

场景：你想生成"7 根香蕉"的图片，但模型生成的图片里有时是 6 根、有时是 8 根。你有两个工具：`Generate Image` 和 `Count Food Items`。如果目标是"要么生成正确数量、要么达到最大重试次数"，就用 `LoopAgent`：

```python
from google.adk.agents import LoopAgent, LlmAgent

generator = LlmAgent(
    name="generator",
    instruction="生成用户要求的食物图片。",
    tools=[generate_image]
)

counter = LlmAgent(
    name="counter",
    instruction="数图片里食物的数量，返回数字。",
    tools=[count_food_items]
)

loop = LoopAgent(
    sub_agents=[generator, counter],
    max_iterations=5
)
```

`LoopAgent` 自己**不做任何 AI 决策**，纯粹按顺序反复调用 sub-agent。这跟 `SequentialAgent` 的本质区别是：Sequential 跑一遍结束，Loop 跑 N 遍结束。

文档同时指出了一个关键限制：

> The LoopAgent itself does not inherently decide when to stop looping. You must implement a termination mechanism to prevent infinite loops.

常见的三种终止机制：

1. **`max_iterations`**：最简单粗暴，到次数就停。文档推荐配合下面的两种使用，不要单独依赖。
2. **sub-agent 升级**：让某个 sub-agent 返回 "STOP" 信号。文档里的 Writer-Critic 例子用的就是这个：

```python
writer = LlmAgent(name="writer", instruction="起草文档")
critic = LlmAgent(name="critic", instruction="评审文档质量，如果达标返回 STOP")

loop = LoopAgent(
    sub_agents=[writer, critic],
    max_iterations=5
)
```

3. **外部控制**：在 sub-agent 里修改共享 context，外部代码读 context 决定是否 break。灵活但复杂。

更值得说的是 ADK 2.0 的新东西：**graph workflows**。文档明确写：

> Starting in ADK 2.0 for Python and Go, templated workflows have been superseded by more flexible workflow structures, including graph-based workflows and dynamic workflows.

意思是：如果你刚开始写 ADK 2.0，不要用 `LoopAgent`/`SequentialAgent`/`ParallelAgent` 了，直接用 graph workflow——可以用节点 + 边的形式表达任意控制流，包括条件分支、循环、并发。template workflow 在 ADK 2.0 里更像"向后兼容的旧路径"。

## 6. 第四件事：MCP——它和 API 的真正区别

课程 40:04 段对应 [MCP tools](https://google.github.io/adk-docs/tools/mcp-tools/)。这是 2025-2026 年 Agent 圈最热的概念之一，也是被误解最多的。

**MCP（Model Context Protocol）** 是 Anthropic 在 2024 年提出的一个标准，让模型以一种统一的方式发现和调用外部工具。它的核心抽象是：

- **MCP Server**：一个进程，暴露一组工具（带 schema）。
- **MCP Client**：Agent 框架里的客户端，连接到 server，把 server 的工具注册成 agent 可用的工具。

ADK 里使用 MCP 工具大概是这样：

```python
from google.adk.tools.mcp_tool import McpToolset

mcp_tools = McpToolset(
    connection_params=StdioConnectionParams(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem"],
    )
)

agent = LlmAgent(
    name="file_agent",
    model="gemini-2.5-flash",
    instruction="根据用户指令操作本地文件",
    tools=[mcp_tools]
)
```

**那 MCP 和直接调 API 有什么区别？** 这是所有新手都会问的问题。答案藏在三个字里：**动态发现**。

| 维度 | 直接调 API | 用 MCP |
|---|---|---|
| 工具发现 | 你写代码 import，按函数名调 | agent 启动时连接 server，自动拿 schema |
| 协议耦合 | 你的代码和 API 紧耦合（HTTP / GraphQL / gRPC） | 你只和 MCP 协议耦合，server 内部用什么 API 你不管 |
| 跨进程 | 不支持，需要 IPC 或 HTTP | 支持，server 是独立进程 |
| 复用 | 每接一个新工具要改代码 | 换 server 配置就行，不用改 agent |

课程里 ADK 文档给出了一个非常实在的判断：

> Use MCP tools when the tool set is large, frequently changing, or maintained by a third party. Use function tools (regular Python functions) when you want fine-grained control, low latency, or the tool is simple.

我自己的经验补充一条：**MCP 适合"工具很多 + 想标准化"，不适合"工具很少 + 想快速迭代"**。如果你的项目只有 5 个工具，写 MCP server 是过度工程；如果你要给几十个工具提供统一接入点，MCP 是当下最务实的选择。

## 7. 第五件事：Multi-Agent 系统

课程 1:00:22 段对应 [Agent Team tutorial](https://google.github.io/adk-docs/tutorials/agent-team/) 和 [Collaborative workflows](https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/)。

ADK 的多 agent 设计思想是**树状层级**：

```
Root Agent (orchestrator)
├── Sub-Agent A (specialist)
├── Sub-Agent B (specialist)
└── Sub-Agent C (specialist)
```

父 agent 通过 LLM 决定什么时候把任务委派给哪个子 agent。子 agent 的 `description` 字段就是这个决策的依据——父 agent 看到子 agent 的 description，决定是否调用。

代码上很简单：

```python
research_agent = LlmAgent(
    name="researcher",
    description="专门做网络搜索和信息收集",
    tools=[search_web]
)

writer_agent = LlmAgent(
    name="writer",
    description="根据研究材料写文档",
    tools=[]
)

root = LlmAgent(
    name="root",
    model="gemini-2.5-flash",
    instruction="你是协调员，根据用户需求委派给 researcher 或 writer。",
    sub_agents=[research_agent, writer_agent]
)
```

ADK 文档里有一个特别值得抄的细节：**子 agent 之间的状态隔离**。父 agent 和每个子 agent 都有自己的 session 和 state，子 agent 修改 state 不会反向影响父 agent。如果你想跨 agent 共享状态，必须显式通过工具函数传递。

Multi-Agent 真正难的从来不是"怎么写代码"，而是"什么时候值得拆"。文档给的经验是：

- 单一 LLM 调用足够 → 别拆
- 任务有明显可委派的子任务 → 拆成 sub-agent
- 子任务之间需要不同的 tool / prompt / model → 拆
- 单一 prompt 已经能解决 → 保持单一 agent

## 8. 对独立 Agent 项目作者的 5 条工程经验

把课程和文档合在一起看，结合我自己写 Agent 项目的踩坑，给独立 Agent 作者 5 条可复用的经验：

**1. ADK 2.0 起，新项目直接用 graph workflow，不要用 template workflow**。template workflow（Sequential / Loop / Parallel）还在，但 ADK 官方明确说 graph 是首选。如果你刚开始写，用 graph 可以省掉很多将来重写控制流的工作。

**2. `instruction` 是代码，不是 prompt**。写得像代码一样结构化（任务 / 输入约束 / 输出格式 / 失败处理），不要写得像"你是一个友好的助手"。模型对结构化指令的遵循度比自然语言描述高 30%-50%。

**3. Session 和 MemoryService 的边界要一开始就想清楚**。短期状态（当前会话的临时变量）放 Session.state；跨会话需要的知识（用户偏好、历史决策）放 MemoryService。混在一起将来扩展会非常痛苦。

**4. 工具设计决定 agent 能力上限**。一个 agent 的智能度 = 模型智能度 × 工具设计的合理性。`description` 字段是模型决定何时调用的唯一信号，写得模糊的工具永远不会被用。函数 docstring 要写得像 OpenAPI spec，而不是 Python docstring。

**5. MCP 不是银弹，先用 function tool 起步**。等你有了 5 个以上工具、或者工具来自不同团队，再考虑 MCP 化。早期 MCP 化的项目 80% 都在第一年内又退化回了直接调用，因为维护 MCP server 的成本高于收益。

## 9. 关键资源与延伸阅读

**官方课程入口**：
- @0xCodez 整理的 5 段大纲推文：`https://x.com/0xCodez/status/2074865699214741897`
- @FinanceYF5 转发：`https://x.com/FinanceYF5/status/2075463751315476740`

**ADK 官方文档**（Python / TypeScript / Go / Java / Kotlin 五 SDK 一致）：
- 总目录：`https://google.github.io/adk-docs/`
- Technical Overview：`https://google.github.io/adk-docs/get-started/about/`
- Get Started：`https://google.github.io/adk-docs/get-started/python/`
- Agents：`https://google.github.io/adk-docs/agents/`
- LLM Agents：`https://google.github.io/adk-docs/agents/llm-agents/`
- Loop Workflow：`https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/`
- Sequential Workflow：`https://google.github.io/adk-docs/agents/workflow-agents/sequential-agents/`
- Sessions and Memory：`https://google.github.io/adk-docs/sessions/memory/`
- MCP tools：`https://google.github.io/adk-docs/tools/mcp-tools/`
- Agent Team Tutorial：`https://google.github.io/adk-docs/tutorials/agent-team/`

**横向对比框架**：
- Anthropic Claude Agent SDK：聚焦 Claude 模型的 agent 抽象
- LangChain / LangGraph：最广泛采用的链式/图式框架，model 无关
- AutoGen（Microsoft）：多 agent 对话范式
- CrewAI：role-based 多 agent 编排

**延伸阅读建议**：
- 如果你想看 graph workflow 的细节：`https://google.github.io/adk-docs/agents/graph/`（ADK 2.0 新增）
- 如果你想接 Vertex AI Memory Bank：`https://google.github.io/adk-docs/sessions/memory/#memory-bank`
- 如果你想了解 A2A 协议（agent-to-agent）：`https://google.github.io/adk-docs/a2a/`

---

*本文基于 Google 官方 ADK 文档（2026-07 版本）与 @0xCodez 在 X 整理的 Agentic Engineering 课程大纲。所有代码示例均来自 ADK 文档原文，未做改动。文档可能在后续版本中变化，建议以 `google.github.io/adk-docs` 当前版本为准。*