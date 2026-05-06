---
title: "LangGraph：构建有状态智能体的图形框架——29K Stars 的 AI Agent 编排框架从入门到精通"
date: "2026-04-15T00:15:00+08:00"
slug: "langgraph-stateful-agents-framework"
description: "LangGraph 是 29K Stars 的开源图形框架，用于构建有状态的、持久化的 AI Agent。受 Pregel/Apache Beam/NetworkX 启发，提供 Durable Execution、Human-in-the-Loop、Comprehensive Memory 核心特性，支持 Klarna/Replit/Elastic 等生产级应用。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Agent", "LangChain", "LLM", "Python", "图形框架", "状态管理"]
---

# LangGraph：构建有状态智能体的图形框架——29K Stars 的 AI Agent 编排框架从入门到精通

> **目标读者**：LLM 应用开发者、AI Agent 研究者、想要构建复杂多步骤 AI 系统的工程师
> **预计阅读时间**：50-70 分钟
> **前置知识**：Python 基础、LLM API 使用经验、对 Agent 概念有了解
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解 LangGraph 的核心定位**：为何需要一个"图形框架"来构建 Agent
2. **掌握 LangGraph 的核心概念**：StateGraph、Node、Edge、Checkpoint
3. **理解持久化执行原理**：Durable Execution 如何实现故障恢复
4. **掌握 Human-in-the-loop**：如何在执行过程中介入和修改 Agent 状态
5. **能够构建生产级 Agent**：使用 LangGraph 构建可靠的多步骤 AI 系统
6. **理解调试和部署**：LangSmith 调试、LangGraph Platform 部署

---

## §2 背景与动机：为何需要 LangGraph

### 2.1 LLM Agent 的问题

当前 LLM Agent 面临的核心挑战：

| 问题 | 描述 | 影响 |
|------|------|------|
| **执行不可靠** | 长对话中 API 失败导致上下文丢失 | Agent 无法完成复杂任务 |
| **状态管理混乱** | 多轮对话中如何维护状态 | Agent 行为不一致 |
| **缺乏持久化** | 服务重启后 Agent 记忆消失 | 用户体验差 |
| **调试困难** | Agent 执行路径不透明 | 线上问题难以排查 |
| **人工介入难** | 执行过程中无法灵活干预 | 自动化程度受限 |

### 2.2 传统方案的局限

**基于 LangChain 的方案**：
- LangChain 提供了抽象层，但不够底层
- 难以精细控制 Agent 的执行流程
- 状态管理依赖外部实现

**基于 LangGraph 的方案**：
- 图形模型天然适合表达 Agent 的多步骤流程
- 内置 Checkpoint 持久化
- 支持 Human-in-the-loop
- 可视化调试和追踪

### 2.3 LangGraph 的设计哲学

LangGraph 受到了三个系统的启发：

| 启发来源 | 借鉴内容 |
|----------|----------|
| **Pregel**（Google）| 图计算的分步执行模型 |
| **Apache Beam** | 统一的批处理/流处理抽象 |
| **NetworkX** | 声明式图操作接口 |

LangGraph 的核心理念：**将 Agent 建模为图形，用节点（Node）表示步骤，用边（Edge）表示流转，用状态（State）维护上下文。**

---

## §3 核心概念：StateGraph 体系

### 3.1 三大核心概念

LangGraph 的核心是 **StateGraph**——一个用 Python 定义的有向图：

```python
StateGraph(State)
    ├── .add_node(name, func)     # 添加节点（Agent 步骤）
    ├── .add_edge(source, target)  # 添加边（固定流转）
    ├── .add_conditional_edges()   # 添加条件边（动态路由）
    └── .compile()                # 编译成可执行的图
```

### 3.2 State（状态）

State 是贯穿整个 Agent 执行过程的共享数据结构：

```python
from typing import TypedDict
from langgraph.graph import StateSchema

class AgentState(TypedDict):
    messages: list[str]           # 对话历史
    current_step: str             # 当前步骤
    context: dict                 # 额外上下文
    checkpoint: str               # 持久化检查点
```

### 3.3 Node（节点）

Node 是 Agent 中的一个处理步骤：

```python
from langgraph.graph import StateGraph

def should_continue(state: AgentState) -> str:
    """路由节点：根据状态决定下一步"""
    if len(state["messages"]) > 10:
        return "end"
    return "continue"

# 定义节点
graph = StateGraph(AgentState)
graph.add_node("chat", chat_node)           # 聊天节点
graph.add_node("search", search_node)        # 搜索节点
graph.add_node("router", should_continue)    # 路由节点
```

### 3.4 Edge（边）

Edge 定义了节点之间的流转关系：

```python
# 固定边：必然发生的流转
graph.add_edge("chat", "search")             # chat 完成后必然到 search

# 条件边：根据状态动态决定
graph.add_conditional_edges(
    "router",
    lambda state: "chat" if state["needs_human"] else "search"
)
```

### 3.5 Checkpoint（检查点）

Checkpointer 实现了状态的持久化和恢复：

```python
from langgraph.checkpoint.memory import MemorySaver

# 内存 Checkpointer（开发用）
checkpointer = MemorySaver()

# 持久化 Checkpointer（生产用）
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver.from_conn_string("postgresql://...")

# 编译时绑定 Checkpointer
app = graph.compile(checkpointer=checkpointer)

# 从检查点恢复并继续执行
config = {"configurable": {"thread_id": "user_123"}}
app.invoke(input, config=config)
```

---

## §4 核心特性：Durable Execution

### 4.1 什么是 Durable Execution

Durable Execution = **持久化 + 可恢复**

传统的 Agent 执行：

```
用户请求 → 执行到第5步 → API 超时 → ❌ 第1-5步全部丢失
```

LangGraph 的 Durable Execution：

```
用户请求 → 执行到第5步 → API 超时 → 💾 状态已持久化
                                                ↓
恢复后 → 从第5步继续 → ✅ 完成剩余步骤
```

### 4.2 实现原理

| 层级 | 技术 |
|------|------|
| **状态快照** | 每次节点执行后自动保存完整状态 |
| **边缘持久化** | 边的选择结果也被记录 |
| **幂等设计** | 节点可以安全重试 |
| **检查点存储** | 支持 Memory、Postgres、SQLite 等 |

### 4.3 代码示例

```python
from langgraph.graph import StateGraph
from langgraph.checkpoint.postgres import PostgresSaver

# 1. 定义 Agent
class AgentState(TypedDict):
    messages: list
    step: int

def chat_node(state):
    response = llm.invoke(state["messages"])
    return {"messages": [response], "step": state["step"] + 1}

# 2. 构建图
graph = StateGraph(AgentState)
graph.add_node("chat", chat_node)
graph.set_entry_point("chat")
graph.add_edge("chat", END)

# 3. 配置持久化
checkpointer = PostgresSaver.from_conn_string("postgresql://user:pass@host/db")
app = graph.compile(checkpointer=checkpointer)

# 4. 持久的用户会话
config = {"configurable": {"thread_id": "user_123"}}
for message in conversation:
    app.invoke({"messages": [message]}, config=config)
```

### 4.4 故障恢复示例

```python
# 场景：执行到一半网络断开
try:
    result = app.invoke(input, config=config)
except APITimeoutError:
    pass  # 记录异常但不做处理

# 后续：用户重新连接
config = {"configurable": {"thread_id": "user_123"}}
# LangGraph 自动从上一个检查点恢复
result = app.invoke(None, config=config)  # input=None 表示继续
```

---

## §5 Human-in-the-Loop：人工介入机制

### 5.1 为什么需要 Human-in-the-Loop

某些场景下需要人工确认或修改：

| 场景 | 说明 |
|------|------|
| **敏感操作** | 发送邮件、转账等需要人工确认 |
| **不确定决策** | Agent 对结果不确定，需要人工判断 |
| **错误修正** | 发现 Agent 理解错误，人工介入修正 |
| **内容审核** | Agent 生成的文案需要人工审核 |

### 5.2 中断与恢复机制

```python
from langgraph.errors import NodeInterrupt

def sensitive_node(state):
    """发送邮件节点"""
    email_content = draft_email(state)

    # 中断执行，等待人工确认
    raise NodeInterrupt(
        f"即将发送邮件给 {state['recipient']}，内容：\n{email_content}"
    )

# 在 Agent 执行中
config = {"configurable": {"thread_id": "user_123"}}

# 执行到 sensitive_node 时会抛出 NodeInterrupt
try:
    app.invoke(input, config=config)
except NodeInterrupt as e:
    print(f"需要人工确认：{e.message}")

    # 人工审核后，可以：
    # 1. 批准继续（修改状态后继续）
    # 2. 修改内容后继续
    # 3. 中止执行
```

### 5.3 状态修改

```python
# 人工审核时，可以修改 Agent 状态
from langgraph.constants import Edit

# 假设审核时发现邮件内容有误，修正后继续
app.update_state(
    config,
    {"email_content": "修正后的邮件内容"}
)

# 批准后继续执行
result = app.invoke(None, config=config)
```

### 5.4 典型工作流

```
┌─────────────────────────────────────────────────────────┐
│                    Human-in-the-Loop 工作流              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Agent 执行 ──▶ 遇到敏感节点 ──▶ NodeInterrupt 抛出      │
│                        │                               │
│                        ▼                               │
│                   人工介入队列 ←── 通知人工审核员        │
│                        │                               │
│                        ▼                               │
│              人工确认/修改/批准/拒绝                     │
│                        │                               │
│                        ▼                               │
│                 恢复执行或终止                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## §6 内存管理：Comprehensive Memory

### 6.1 两种内存类型

| 类型 | 作用 | 持久化 |
|------|------|--------|
| **Working Memory** | 当前会话内的短期记忆 | Checkpoint 自动管理 |
| **Persistent Memory** | 跨会话的长期记忆 | External Store（向量数据库等）|

### 6.2 消息历史管理

```python
from langgraph.graph import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# messages 自动去重和追加
def chat_node(state: AgentState):
    new_messages = [HumanMessage(content="Hello")]
    # add_messages 策略自动处理
    return {"messages": new_messages}
```

### 6.3 长期记忆集成

```python
from langchain.memory import VectorStoreRetrieverMemory

# 连接向量数据库作为长期记忆
memory = VectorStoreRetrieverMemory(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5})
)

def recall_memory(state: AgentState) -> dict:
    """从长期记忆检索相关内容"""
    query = state["messages"][-1].content
    relevant = memory.load_memory_variables({"input": query})
    return {"context": relevant["history"]}

# 在图中添加记忆节点
graph.add_node("recall", recall_memory)
graph.add_edge("recall", "chat")
```

---

## §7 快速开始：5 分钟上手

### 7.1 安装

```bash
pip install -U langgraph
```

### 7.2 最小示例：ReAct Agent

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# 1. 定义状态
class AgentState(TypedDict):
    input: str
    agent_outcome: str
    intermediate_steps: list

# 2. 定义节点
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4")
tools = [search, calculate]  # 你的工具

def agent(state):
    messages = [{"role": "user", "content": state["input"]}]
    response = llm.bind_tools(tools).invoke(messages)
    return {"agent_outcome": response}

def should_continue(state):
    if hasattr(state["agent_outcome"], "tool_calls"):
        return "continue"
    return "end"

# 3. 构建图
graph = StateGraph(AgentState)
graph.add_node("agent", agent)
graph.add_node("action", tool_node)  # 工具执行节点
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("action", "agent")  # 工具执行完返回 agent
graph.add_edge("agent", END)

# 4. 编译并运行
app = graph.compile()
result = app.invoke({"input": "北京今天天气怎么样？"})
```

---

## §8 调试与部署

### 8.1 LangSmith 集成

LangSmith 提供了可视化的调试能力：

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key"

# 启用后，所有执行都会被追踪
app.invoke(input, config=config)  # LangSmith 自动记录完整轨迹
```

### 8.2 LangGraph Platform

生产环境部署方案：

| 方案 | 适用场景 |
|------|----------|
| **LangGraph Cloud** | 快速部署，无需运维 |
| **Self-hosted** | 数据敏感，完全自控 |
| **Local** | 开发测试 |

```bash
# 部署到 LangGraph Cloud
langgraph deploy --name my-agent

# 本地开发服务器
langgraph dev
```

---

## §9 生态与集成

### 9.1 LangGraph 生态图

```
┌──────────────────────────────────────────────────────────┐
│                     LangGraph 生态系统                    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│   │  LangGraph  │◄──►│  LangChain  │◄──►│ Deep Agents │ │
│   │  (核心框架) │    │   (集成层)  │    │ (预置Agent) │ │
│   └──────┬──────┘    └─────────────┘    └─────────────┘ │
│          │                                              │
│          ▼                                              │
│   ┌──────────────────────────────────────────────────┐  │
│   │                    LangSmith                      │  │
│   │  (调试 / 追踪 / 评估 / 部署)                       │  │
│   └──────────────────────────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 9.2 集成案例

| 公司 | 使用场景 |
|------|----------|
| **Klarna** | 电商客服 Agent |
| **Replit** | 代码生成与调试 Agent |
| **Elastic** | 搜索增强的 AI 助手 |

---

## §10 常见问题（FAQ）

### Q1：LangGraph 和 LangChain Agent 有什么区别？

A：LangChain Agent 是高层抽象，封装好的开箱即用方案。LangGraph 是底层框架，提供更精细的控制。LangChain Agent 底层也是用 LangGraph 实现的。

### Q2：什么时候该用 LangGraph？

A：当需要：精细控制执行流程、持久化状态、支持 Human-in-the-Loop、复杂的多 Agent 协作时。

### Q3：LangGraph 支持哪些 Checkpointer？

A：官方支持 Memory、Postgres、SQLite。社区还有 Redis、MongoDB、Cassandra 等。

### Q4：LangGraph 能用于生产环境吗？

A：可以。Klarna、Replit、Elastic 等公司已在生产环境使用。LangGraph Platform 提供企业级部署支持。

### Q5：LangGraph 有 JavaScript 版本吗？

A：有。见 [LangGraph.js](https://github.com/langchain-ai/langgraphjs)。

---

## §11 相关资源

| 资源 | 链接 |
|------|------|
| **GitHub** | [github.com/langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) |
| **文档** | [docs.langchain.com/oss/python/langgraph](https://docs.langchain.com/oss/python/langgraph/overview) |
| **API 参考** | [reference.langchain.com/python/langgraph](https://reference.langchain.com/python/langgraph) |
| **快速入门** | [docs.langchain.com/oss/python/langgraph/quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart) |
| **LangGraph.js** | [github.com/langchain-ai/langgraphjs](https://github.com/langchain-ai/langgraphjs) |
| **LangChain Academy** | [academy.langchain.com](https://academy.langchain.com/courses/intro-to-langgraph) |

---

**文档信息**
难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-04-15 | 预计阅读时间：50-70 分钟
