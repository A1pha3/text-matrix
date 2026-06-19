---
title: "LangGraph：构建有状态智能体的图形框架——29K Stars 的 AI Agent 编排框架从入门到精通"
date: "2026-04-15T00:15:00+08:00"
slug: "langgraph-stateful-agents-framework"
description: "LangGraph 真正解决的不是如何调用 LLM，而是把多步 Agent 执行改造成可观测、可恢复、可干预的状态机。受 Pregel/Apache Beam/NetworkX 启发，提供 StateGraph、Checkpoint、Node、Edge、Reducer 五个核心抽象，支撑 Durable Execution、Human-in-the-Loop、Comprehensive Memory 三项生产级能力。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Agent", "LangChain", "LLM", "Python", "图形框架", "状态管理"]
---

# LangGraph：构建有状态智能体的图形框架

LangGraph 解决的问题和 LangChain 不同。LangChain 回答「如何调用 LLM」，LangGraph 回答的是另一个问题：把多步 Agent 执行改造成可观测、可恢复、可干预的状态机。从 demo 走到生产，这一步往往比换一个更强的模型更关键，也是 29K Stars 背后的工程价值所在。

一个典型的 Agent 失败场景是这样的：用户问「帮我订下周去上海的机票并通知同事」，Agent 调了 5 个工具，第 6 步调用邮件 API 时网络抖动。在传统链式实现里，前 5 步的中间结果全部丢失，用户只能从头再来。生产环境里这种体验直接等于流失。LangGraph 把链式执行拆成节点和边，每个节点执行完都把状态写进 Checkpoint，下一次恢复时从最近的成功节点继续——Agent 从「一次性脚本」变成了「可断点续传的状态机」。

本文先拆开 LangGraph 的五个核心抽象和三项关键能力，再用一条完整的 Checkpoint 恢复流程把它们串起来，最后说明它和 LangChain Agent、CrewAI、AutoGen 的真实工程取舍，以及什么样的场景该用、什么样的场景不该用。

## 全景地图：五个抽象与三项能力

LangGraph 的 API 表面不大，但抽象层次需要先理清。五个核心抽象构成图的骨架，三项关键能力构建在骨架之上。

```mermaid
graph TB
    subgraph "五个核心抽象（图的骨架）"
        SG["StateGraph<br/>有向图容器"]
        N["Node<br/>处理步骤 f(state)→delta"]
        E["Edge<br/>固定边 / 条件边"]
        S["State<br/>TypedDict 共享数据"]
        R["Reducer<br/>多写者合并策略"]
    end

    subgraph "三项关键能力（建立在 Checkpoint 之上）"
        DE["Durable Execution<br/>断点续传"]
        HITL["Human-in-the-Loop<br/>NodeInterrupt 暂停"]
        MEM["Comprehensive Memory<br/>Working + Persistent"]
    end

    SG --> N
    N --> E
    S --> N
    R --> S
    N --> CP["Checkpoint"]
    CP --> DE
    CP --> HITL
    CP --> MEM
```

| 抽象 | 角色 | 类比 |
|------|------|------|
| **StateGraph** | 整个 Agent 的有向图容器 | 函数集合 |
| **Node** | 图中的处理步骤，接收状态返回状态更新 | 函数体 |
| **Edge** | 节点间的流转，分固定边和条件边 | 调用关系 |
| **State** | 贯穿全图的共享数据结构，由 TypedDict 定义 | 函数参数 + 返回值 |
| **Reducer** | 多个节点写同一字段时的合并策略 | reduce 函数 |

三项关键能力都建立在 Checkpoint 之上：

- **Durable Execution**：每个节点执行后自动持久化状态，故障后从检查点恢复
- **Human-in-the-Loop**：通过 `NodeInterrupt` 暂停执行，等待人工输入后继续
- **Comprehensive Memory**：Working Memory 由 Checkpoint 管理，Persistent Memory 接外部存储

理清这张地图之后，接下来看每个抽象在真实场景里怎么用、用错会出什么问题。

## 为什么 Agent 需要图形模型而不是线性链

LangChain 的 `AgentExecutor` 是一条链：模型决定下一步 → 执行工具 → 把结果塞回 prompt → 再问模型。这条链在 demo 阶段够用，但生产环境会撞上三堵墙。

第一堵墙是**控制流不可见**。链式执行里，「先查数据库还是先调外部 API」「失败后是重试还是降级」这些决策全部塞在 prompt 里，由模型决定。出了问题，你拿到的只有一段对话历史，看不到执行路径。LangGraph 把这些决策外化成 Edge，每条边的选择都被记录在 Checkpoint 里，调试时能精确看到「第 3 步为什么走了 search 节点而不是 recall 节点」。

第二堵墙是**状态不可恢复**。链式执行的状态在内存里，进程崩了就没了。LangGraph 的每个节点都返回一个 State delta，框架把这个 delta 合并进全量 State 后写入 Checkpointer。PostgresSaver 把状态写进数据库，进程重启后用同一个 `thread_id` 调用 `invoke(None, config)` 就能从断点继续。

第三堵墙是**人工介入无法插入**。链式执行一旦启动就跑到底，中间想暂停等人工确认，得自己造一套暂停-恢复机制。LangGraph 的 `NodeInterrupt` 是框架级原语：节点抛出这个异常，框架把当前状态写进 Checkpoint，外部审核完成后调 `update_state` 修改状态，再 `invoke(None)` 继续——图的其它节点感知不到暂停发生过。

这三堵墙的共同根因是：链式模型把「执行」「状态」「控制流」三件事耦合在一起，图形模型把它们拆开。Node 只管计算，Edge 只管路由，State 只管数据，Checkpoint 只管持久化。生产级 Agent 需要的正是这种正交分解——任何一部分出问题都能独立定位和修复。

## 五个抽象的工程用法

### StateGraph：图的容器，不是配置对象

`StateGraph` 看起来像配置对象，但它的真正角色是编译器入口。`compile()` 之后返回的 `app` 是一个不可变的可执行图，所有节点、边、Reducer 在编译时已经固定。运行时不能再修改图结构——这种约束是有意为之的，目的是保证同一次编译产出的 `app` 在多线程环境下行为一致，避免运行时改图带来的竞态条件。

```python
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]  # Reducer 指定追加而非覆盖
    current_step: str
    context: dict

graph = StateGraph(AgentState)
graph.add_node("chat", chat_node)
graph.add_node("search", search_node)
graph.add_edge(START, "chat")
graph.add_conditional_edges("chat", router_fn, {"continue": "search", "end": END})
app = graph.compile(checkpointer=checkpointer)
```

`Annotated[list, add_messages]` 这一行容易被忽略，但它是 State 设计的关键。默认情况下，节点返回的字段会覆盖原 State；指定 Reducer 后，多个节点写同一字段时按策略合并。`add_messages` 会按 message id 去重追加，避免每次节点返回都把整个消息列表重写一遍。

Reducer 在多 Agent 场景下尤其重要。假设 Supervisor 同时调度 researcher 和 coder 两个子 Agent，两者都往 `messages` 字段写结果，没有 Reducer 时后写的会覆盖先写的；指定 `add_messages` 后，两条结果都会保留，调用方能看到完整的协作轨迹。

### Node：纯函数，不是方法

Node 的契约是 `f(state) -> state_delta`。它接收完整 State，返回需要更新的字段子集。不返回的字段保持不变。这个约束看起来限制性强，但正是它让 Checkpoint 恢复变得可能——每个节点的输出是自包含的，重放时不需要依赖隐式状态。

```python
def search_node(state: AgentState) -> dict:
    query = state["messages"][-1].content
    results = search_tool.invoke(query)
    # 只返回需要更新的字段，messages 由 add_messages Reducer 追加
    return {"messages": [ToolMessage(content=str(results))], "current_step": "search_done"}
```

Node 内部不应该有跨调用的可变状态。如果需要计数器、缓存这类东西，写进 State 让 Checkpoint 管理。把状态藏在闭包或全局变量里，故障恢复时这些状态会丢失，行为不可复现——这是 LangGraph 新手最容易踩的坑之一，平时跑得好好的，第一次故障恢复时才暴露。

### Edge：路由的两种形态

固定边 `add_edge("chat", "search")` 表示 chat 完成后必然到 search，用于线性流程。条件边 `add_conditional_edges("router", fn, mapping)` 用于分支：`fn` 接收 State 返回字符串，`mapping` 把字符串映射到目标节点。

```python
def router(state: AgentState) -> str:
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return "end"

graph.add_conditional_edges(
    "agent",
    router,
    {"tools": "tools_node", "end": END}
)
```

条件边的 `mapping` 参数可以省略，省略时 `fn` 返回的字符串直接当节点名。但显式写出 mapping 是更稳妥的做法——它把所有可能的路由路径在编译时暴露出来，配合 `compile()` 的图校验能提前发现「漏了一个分支」这类错误。线上出过这样的 bug：模型偶尔返回一个未在 mapping 里的字符串，框架抛 `KeyError`，整个会话中断。显式 mapping 让这种错误在编译期就被拦住。

### Checkpoint：持久化的最小单位

Checkpointer 是 LangGraph 区别于其它 Agent 框架的关键机制。每次节点执行后，框架把当前完整 State 写进 Checkpointer，附带执行到哪个节点、走了哪条边。恢复时按 `thread_id` 找到最近的 Checkpoint，从下一个节点继续。

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver

# 开发环境用内存，重启即丢
checkpointer = MemorySaver()

# 生产环境用 Postgres，跨进程跨重启
checkpointer = PostgresSaver.from_conn_string("postgresql://user:pass@host/db")

app = graph.compile(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "user_123_session_456"}}
result = app.invoke({"messages": [HumanMessage(content="你好")]}, config=config)
```

`thread_id` 是会话维度的标识。同一个用户的多次请求用同一个 `thread_id`，Agent 自动延续上下文；不同用户用不同 `thread_id`，状态互相隔离。这种设计让多租户场景天然支持，不需要自己在业务层做状态分桶。

官方支持的 Checkpointer 包括 Memory、Postgres、SQLite。社区有 Redis、MongoDB、Cassandra 实现。选型上，单机开发用 Memory，单机持久化用 SQLite，多实例生产用 Postgres——后两者支持跨进程恢复，Memory 只在进程内有效。一个容易忽略的细节：Checkpoint 写入是同步的，每个节点都要等 IO 完成才能进入下一步。对延迟敏感的场景，要么把多个轻量节点合并成一个，要么用更高吞吐的存储后端（Redis 比 Postgres 快，但持久性保证弱一些）。

## Durable Execution：从一次性脚本到可断点续传

Durable Execution 是 Checkpoint 机制的必然结果，不是 LangGraph 的某个开关。每个节点执行完都持久化，故障后从最近的成功节点继续，这就是「durable」的全部含义。

### 一条完整的 Checkpoint 恢复流程

假设有一个客服 Agent，流程是：分类用户问题 → 查询订单 → 查询物流 → 生成回复。用户问「我的订单 #12345 物流到哪了」，Agent 执行到「查询物流」时数据库连接超时。

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from typing import TypedDict

class ServiceState(TypedDict):
    messages: list
    order_info: dict
    logistics_info: dict
    reply: str

def classify_node(state): ...
def query_order_node(state): ...
def query_logistics_node(state):
    # 这里抛出数据库超时异常
    raise ConnectionError("DB timeout")
def generate_reply_node(state): ...

graph = StateGraph(ServiceState)
graph.add_node("classify", classify_node)
graph.add_node("query_order", query_order_node)
graph.add_node("query_logistics", query_logistics_node)
graph.add_node("reply", generate_reply_node)
graph.add_edge(START, "classify")
graph.add_edge("classify", "query_order")
graph.add_edge("query_order", "query_logistics")
graph.add_edge("query_logistics", "reply")
graph.add_edge("reply", END)

checkpointer = PostgresSaver.from_conn_string("postgresql://...")
app = graph.compile(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "user_abc_ticket_789"}}
```

执行过程：

1. `classify` 执行成功，State 写入 Checkpoint：`{messages: [...], order_info: {}, logistics_info: {}, reply: ""}`，当前节点 `classify`，下一节点 `query_order`
2. `query_order` 执行成功，State 更新为 `{..., order_info: {id: "12345", status: "shipped"}, ...}`，写入 Checkpoint
3. `query_logistics` 抛出 `ConnectionError`，异常向上抛，但 Checkpoint 仍停留在第 2 步的状态
4. 业务层捕获异常，记录日志，向用户返回「正在处理中」的临时响应
5. 几分钟后数据库恢复，业务层用同一个 `thread_id` 再次调用：

```python
# input=None 表示从 Checkpoint 继续，不重新输入
result = app.invoke(None, config=config)
```

6. 框架从 Checkpoint 读取状态，发现执行到 `query_logistics` 的入口，重新执行这个节点
7. 这次数据库正常，`query_logistics` 成功，`reply` 节点继续执行，最终返回完整回复

整个恢复过程对业务代码透明。业务层要做的只有两件事：捕获异常时记录 `thread_id`，恢复时用同一个 `thread_id` 调 `invoke(None)`。中间状态由 Checkpoint 管，从哪一步继续由框架判断。

### 幂等性是 Durable Execution 的隐含契约

Checkpoint 恢复会重新执行失败的那个节点。如果这个节点有副作用（发邮件、扣款、写数据库），重试时可能产生重复操作。Node 设计必须满足幂等性：

- 写数据库：用唯一键 upsert，不用 insert
- 调外部 API：传幂等键（idempotency key），让对端去重
- 发消息：先查是否已发，再决定是否重发

不满足幂等性的节点在重试时会出问题，而且问题往往在第一次故障恢复时才暴露——平时跑得好好的，一上生产就出 bug。这是 LangGraph 新手最常见的坑：开发环境一切正常，因为没触发过重试；生产环境第一次数据库抖动，同一个邮件发了两次，同一个订单扣了两次款。

## Human-in-the-Loop：生产门槛而非可选功能

很多团队把 Human-in-the-Loop（HITL）当成「高级功能」，觉得 demo 阶段不需要。这个判断在生产环境会反转：HITL 在金融、医疗、法律、HR 这些领域属于合规和安全的硬性要求，没它过不了审查，谈不上上线。

考虑一个财务 Agent，自动审批员工报销。如果完全自动化，Agent 误判一笔 5 万元的报销直接打款，损失由谁承担？监管和内部风控都要求关键决策必须有人工签字。

### NodeInterrupt：暂停是框架级行为

LangGraph 的 HITL 通过 `NodeInterrupt` 异常实现。节点内部抛出这个异常，框架捕获后把当前状态写入 Checkpoint，然后把控制权交回调用方。图的其它节点感知不到暂停发生过——它们只看到状态在某个时刻被更新了，然后继续执行。

```python
from langgraph.errors import NodeInterrupt

def send_email_node(state):
    email_draft = compose_email(state)
    if state["amount"] > 10000:
        raise NodeInterrupt(
            f"金额超过 1 万元，需要人工确认。收件人：{state['recipient']}，"
            f"金额：{state['amount']}，邮件内容：\n{email_draft}"
        )
    # 金额小，直接发送
    send_email(state["recipient"], email_draft)
    return {"sent": True}
```

调用方捕获异常后，把 `thread_id` 和待审核内容推给人工审核队列。审核员在后台系统看到这条待办，决定批准、修改还是拒绝。

```python
config = {"configurable": {"thread_id": "user_abc_ticket_789"}}

try:
    result = app.invoke(input, config=config)
except NodeInterrupt as e:
    # 推送到审核队列，记录 thread_id 供后续恢复
    enqueue_for_review(thread_id="user_abc_ticket_789", message=e.message)
```

### 三种恢复路径

审核员有三种操作路径，对应三种不同的恢复方式：

**批准继续**：不修改状态，直接从 Checkpoint 继续。

```python
result = app.invoke(None, config=config)
```

**修改后继续**：先调 `update_state` 修改 State，再继续。比如审核员改了邮件内容。

```python
app.update_state(config, {"email_content": "审核员修改后的内容"})
result = app.invoke(None, config=config)
```

**拒绝终止**：不调 `invoke`，状态停留在 Checkpoint。可以调 `update_state` 写入一个「已拒绝」标记，供后续审计。

```python
app.update_state(config, {"status": "rejected_by_reviewer"})
# 不再 invoke，流程终止
```

这三种路径覆盖了生产环境 HITL 的绝大部分场景。暂停和恢复都是框架级行为，业务代码不需要自己实现状态保存和恢复逻辑——这是 LangGraph 把 HITL 做成原语级能力后，业务层能省掉的最大一块工作量。

## Memory：Working Memory 与 Persistent Memory 的边界

LangGraph 的 Memory 模型容易混淆，因为「记忆」这个词在 LLM 语境下被用得太泛。LangGraph 把 Memory 明确分成两层，两层有不同的生命周期和存储后端。

**Working Memory** 是单次会话内的状态，由 Checkpoint 自动管理。一个 `thread_id` 对应一份 Working Memory，会话结束（用户离开）后是否保留取决于 Checkpointer 配置——MemorySaver 进程退出就丢，PostgresSaver 永久保留。Working Memory 里放的是当前对话的消息历史、中间工具调用结果、当前执行到哪一步。

**Persistent Memory** 是跨会话的长期记忆，需要业务层主动集成。LangGraph 本身不提供向量数据库，需要接 LangChain 的 `VectorStoreRetrieverMemory` 或自己实现。典型用法是：会话结束时把关键信息（用户偏好、历史决策）写入向量库，下次会话开始时检索相关内容填进上下文。

```python
from langchain.memory import VectorStoreRetrieverMemory

# 长期记忆：跨会话检索
long_term_memory = VectorStoreRetrieverMemory(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5})
)

def recall_node(state: AgentState) -> dict:
    """会话开始时检索长期记忆，填入上下文"""
    query = state["messages"][-1].content
    relevant = long_term_memory.load_memory_variables({"input": query})
    return {"context": relevant["history"]}

def persist_node(state: AgentState) -> dict:
    """会话结束时把关键信息写回长期记忆"""
    long_term_memory.save_context(
        {"input": state["messages"][-2].content},
        {"output": state["messages"][-1].content}
    )
    return {}
```

两层的边界要划清楚：Working Memory 放「这次对话需要的东西」，Persistent Memory 放「下次对话可能需要的东西」。把所有历史都塞进 Working Memory 会导致 Context 爆炸；把当前会话的中间结果写进 Persistent Memory 会导致检索噪声。框架不会替你做这个判断，需要根据业务场景设计 State 结构和持久化策略。

## 和 LangChain Agent / CrewAI / AutoGen 的工程取舍

Agent 框架不止 LangGraph 一个，选型时需要清楚每个框架的定位差异。这里给出的是生产环境真实使用中的取舍，不是 feature 对比表。

**LangChain Agent**（`AgentExecutor`）是高层抽象，开箱即用。适合 demo、原型、简单场景：单步工具调用、不需要持久化、不需要 HITL。它的局限是控制流不透明、状态不可恢复、人工介入难插入。LangChain 自己的 Agent 底层也是用 LangGraph 实现的——当你需要 LangChain Agent 的便利但又撞上它的三堵墙时，就该直接用 LangGraph。

**CrewAI** 强调多 Agent 角色协作，每个 Agent 有 role、goal、backstory，通过任务分配和角色对话完成复杂工作。适合内容生成、创意协作这类「多个角色一起讨论」的场景。它的局限是状态管理和故障恢复不如 LangGraph 细粒度——CrewAI 的抽象层次更高，调试时不容易看到具体哪一步出了问题。核心需求是「精细控制单 Agent 的执行流程」时，LangGraph 更合适；核心需求是「多个角色协作产出内容」时，CrewAI 更顺手。

**AutoGen**（Microsoft）主打多 Agent 对话，Agent 之间互相发消息完成工作。适合研究探索、对话式协作场景。它的对话模型灵活但缺乏图形化的控制流约束，复杂流程下容易出现「Agent 之间聊偏了」的情况。LangGraph 的图形模型对控制流有强约束，不容易跑偏，但灵活性低于 AutoGen 的自由对话。

| 维度 | LangGraph | LangChain Agent | CrewAI | AutoGen |
|------|-----------|-----------------|--------|---------|
| 抽象层次 | 底层（图） | 高层（链） | 中层（角色） | 中层（对话） |
| 控制流 | 显式图 | 隐式链 | 角色任务 | 自由对话 |
| 状态持久化 | Checkpoint | 无 | 有限 | 无 |
| HITL | 框架级 | 需自建 | 有限 | 需自建 |
| 适用场景 | 生产级单/多 Agent | 快速原型 | 多角色协作 | 研究探索 |

选型判断：先用 LangChain Agent 跑通 demo；当遇到状态丢失、控制流不可见、需要 HITL 这三个问题之一时，迁移到 LangGraph；如果场景天然是「多角色讨论」，考虑 CrewAI 或 AutoGen，但生产化时仍可能需要 LangGraph 做底座。

## 适用边界：什么时候不该用 LangGraph

LangGraph 不是银弹，下面这些场景用它属于过度设计。

**单步工具调用**。用户问一句话、调一个工具、返回结果，这种场景用 LangChain 的 `chain` 或直接调 LLM API 就够了。引入 StateGraph 反而增加心智负担。

**纯流式对话**。没有工具调用、没有多步推理、就是聊天，用 OpenAI SDK 的 streaming 接口更直接。LangGraph 的图模型对这种场景没有增值。

**强确定性流程**。如果流程是固定的「步骤 A → 步骤 B → 步骤 C」，没有条件分支、没有 LLM 决策，用普通的工作流引擎（Airflow、Temporal）更合适。LangGraph 的条件边是为「LLM 参与路由」设计的，纯确定性流程用不上。

**极低延迟场景**。Checkpoint 持久化有 IO 开销，每个节点都要写一次数据库。如果要求毫秒级响应，Checkpoint 会成为瓶颈。可以禁用 Checkpointer（`compile()` 时不传），但这样就失去了 Durable Execution——回到链式执行的困境。

反过来，下面这些场景 LangGraph 是当前最成熟的选择：

- 多步工具调用，中间步骤可能失败需要重试
- 需要 HITL 的合规场景（金融、医疗、HR）
- 长对话需要跨会话恢复上下文
- 多 Agent 协作需要精细控制流转
- 需要可观测的执行路径用于调试和审计

## 三个真实场景的架构形态

前面讲了抽象和机制，这里用三个典型场景看 LangGraph 在真实业务里怎么落地。每个场景对应一种常见的图结构：单图多节点 + HITL、ReAct 循环、Supervisor 多 Agent 协作。

### 客服 Agent：单图多节点 + HITL

电商客服 Agent 的典型流程：分类 → 查询订单 → 查询物流 → 生成回复。其中「退款」「投诉」类问题需要人工介入。

```python
graph = StateGraph(ServiceState)
graph.add_node("classify", classify_node)
graph.add_node("query_order", query_order_node)
graph.add_node("query_logistics", query_logistics_node)
graph.add_node("escalate", escalate_node)  # 升级到人工
graph.add_node("reply", generate_reply_node)

graph.add_edge(START, "classify")
graph.add_conditional_edges(
    "classify",
    lambda s: "escalate" if s["intent"] == "complaint" else "query_order",
    {"escalate": "escalate", "query_order": "query_order"}
)
graph.add_edge("query_order", "query_logistics")
graph.add_edge("query_logistics", "reply")
graph.add_edge("escalate", "reply")
graph.add_edge("reply", END)
```

`escalate` 节点内部抛 `NodeInterrupt`，等待人工接管。人工处理后用 `update_state` 写入处理结果，`reply` 节点基于这个结果生成最终回复。用户只看到「正在为您处理」然后「已解决」，感知不到中间的暂停和恢复。

### 代码生成 Agent：ReAct 循环 + 工具节点

代码生成 Agent 的核心是 ReAct 循环：模型决定调用什么工具 → 执行工具 → 把结果塞回上下文 → 再问模型。LangGraph 用条件边实现这个循环。

```python
def agent_node(state):
    response = llm.bind_tools(tools).invoke(state["messages"])
    return {"messages": [response]}

def should_continue(state):
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return "end"

graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_executor_node)
graph.add_edge(START, "agent")
graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
graph.add_edge("tools", "agent")  # 工具执行完回到 agent，形成循环
```

`tools` 节点执行完回到 `agent`，形成循环。循环退出条件由 `should_continue` 判断：模型不再请求工具调用时走 `end`。这种模式是 LangGraph 官方推荐的 ReAct 实现方式，比 LangChain 的 `AgentExecutor` 更容易调试——每个循环迭代都有独立的 Checkpoint，可以精确看到第几次迭代出了问题。

### 多 Agent 协作：Supervisor 模式

多个 Agent 协作时，常见模式是 Supervisor：一个调度 Agent 决定把任务分给哪个子 Agent，子 Agent 完成后把结果交回 Supervisor。

```python
def supervisor(state):
    """决定下一步交给哪个子 Agent"""
    response = llm.invoke([
        SystemMessage(content="你是任务调度器。根据当前状态决定下一步交给谁：researcher / coder / end"),
        *state["messages"]
    ])
    return {"next": response.content.strip()}

graph = StateGraph(TeamState)
graph.add_node("supervisor", supervisor)
graph.add_node("researcher", researcher_agent)
graph.add_node("coder", coder_agent)
graph.add_edge(START, "supervisor")
graph.add_conditional_edges(
    "supervisor",
    lambda s: s["next"],
    {"researcher": "researcher", "coder": "coder", "end": END}
)
graph.add_edge("researcher", "supervisor")  # 子 Agent 完成后回到 Supervisor
graph.add_edge("coder", "supervisor")
```

Supervisor 模式的优势是控制流集中：所有路由决策都经过 Supervisor，调试时看 Supervisor 的输出就能理解流程走向。劣势也在这里——每个子任务都要经过它，延迟会累积。对延迟敏感的场景可以考虑 Swarm 模式（Agent 之间直接传递控制权），但 Swarm 的控制流更难追踪，调试成本会上升。

## 调试与部署

### LangSmith：可观测性的标配

LangGraph 的执行路径天然适合可视化，但框架本身不提供 UI。LangSmith 是配套的可观测性平台，启用后每次 `invoke` 的完整轨迹都会被记录：每个节点的输入输出、Edge 的选择、Checkpoint 的写入、耗时分布。

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key"
os.environ["LANGCHAIN_PROJECT"] = "my-agent-prod"

# 启用后所有 invoke 自动被追踪
app.invoke(input, config=config)
```

生产环境强烈建议开启。线上 Agent 出问题时，没有 LangSmith 你只能看日志猜；有 LangSmith 可以直接看到「第 3 步的 LLM 调用花了 8 秒，返回的 tool_calls 字段格式不对，导致第 4 步解析失败」这种级别的细节。可观测性是后续所有优化的前提——看不到执行路径，性能调优和 bug 定位都无从谈起。

### LangGraph Platform：部署的三种形态

| 形态 | 适用场景 | 运维成本 |
|------|----------|----------|
| **LangGraph Cloud** | 快速上线、不想运维 | 低 |
| **Self-hosted** | 数据敏感、合规要求 | 高 |
| **Local (`langgraph dev`)** | 开发测试 | 无 |

```bash
# 本地开发服务器，热重载
langgraph dev

# 部署到 LangGraph Cloud
langgraph deploy --name my-agent
```

Self-hosted 需要自己跑 LangGraph Server（基于 Redis 和 LangGraph Runtime），适合金融、医疗等不能把数据传出内网的场景。Cloud 适合快速验证和中小规模生产。两种形态的 API 接口一致，迁移成本主要在数据层。

## 常见问题与排查

### Q1：LangGraph 和 LangChain Agent 有什么区别？

LangChain Agent 是高层抽象，封装好的开箱即用方案，适合 demo 和简单场景。LangGraph 是底层框架，提供精细控制。LangChain Agent 底层也是用 LangGraph 实现的——当你撞上「状态丢失」「控制流不可见」「HITL 难插入」这三堵墙时，就该直接用 LangGraph。

### Q2：什么时候该用 LangGraph？

满足以下任一条件就该考虑：需要持久化状态跨进程恢复、需要 HITL、需要可观测的执行路径、多 Agent 协作需要精细控制流转。如果只是单步工具调用或纯聊天，用 LangChain 或直接调 API 更合适——LangGraph 的图模型在这种场景下是过度设计。

### Q3：Checkpoint 恢复时节点重试，副作用怎么处理？

Node 必须设计成幂等。写数据库用 upsert，调外部 API 传幂等键，发消息前先查是否已发。不满足幂等性的节点在重试时会出重复操作，而且问题往往在第一次故障恢复时才暴露。

### Q4：支持哪些 Checkpointer？

官方支持 Memory、Postgres、SQLite。社区有 Redis、MongoDB、Cassandra。选型：单机开发用 Memory，单机持久化用 SQLite，多实例生产用 Postgres。

### Q5：能用于生产环境吗？

可以。Klarna（电商客服）、Replit（代码生成）、Elastic（搜索增强）等公司在生产环境使用。LangGraph Platform 提供企业级部署支持。

### Q6：有 JavaScript 版本吗？

有，见 [LangGraph.js](https://github.com/langchain-ai/langgraphjs)。API 与 Python 版本基本对齐，但生态和社区资源不如 Python 版本丰富。

### Q7：`invoke(None)` 和 `invoke(input)` 有什么区别？

`invoke(input)` 是新会话或追加输入，框架从图的入口开始执行。`invoke(None)` 是从 Checkpoint 恢复，框架读取 `thread_id` 对应的最新 Checkpoint，从下一个节点继续。`None` 不是「没有输入」的意思，是「不提供新输入，从断点继续」的信号。

### Q8：节点抛出异常后状态会丢吗？

不会。Checkpoint 在节点执行成功后才写入。节点抛异常时，Checkpoint 仍停留在上一个成功节点的状态。异常向上抛给调用方，调用方处理完异常后用 `invoke(None)` 恢复，会重新执行失败的那个节点。

## 从哪里开始落地

把一个 LLM 应用推上生产时，建议按以下顺序引入 LangGraph：

**第一步：把现有链式 Agent 改造成 StateGraph**。不改业务逻辑，只是把 `chain.invoke()` 拆成节点和边。改完之后配合 LangSmith 能看到完整执行路径——这是后续所有优化的前提，没有可观测性，性能调优和 bug 定位都无从谈起。

**第二步：接入 Checkpointer**。先用 MemorySaver 在开发环境验证，再切到 PostgresSaver。接入后进程重启不丢上下文，状态持久化这一关才算过——否则任何一次部署或重启都会让用户会话中断。

**第三步：在关键节点加 HITL**。识别出有合规风险或不可逆操作的节点，用 `NodeInterrupt` 加暂停点。这一步解决的是合规和安全性——在很多行业，没有 HITL 就没有上线资格。

**第四步：优化 Reducer 和 State 设计**。检查哪些字段需要 Reducer 合并、哪些字段应该排除在 Checkpoint 之外（比如大文件内容）。优化后性能和 Context 卫生都会改善，但属于精细化工作，可以等基础流程跑稳再做。

**第五步：考虑多 Agent 协作**。单 Agent 稳定运行后，再拆分出子 Agent 用 Supervisor 模式协作。不要一开始就上多 Agent——单 Agent 都没跑稳，多 Agent 的调试复杂度会指数级上升。

团队还在选框架阶段、Agent 还没上线时，先把第一步和第二步走通。这两步能让你在生产环境第一次遇到故障时，体会到 LangGraph 真正的价值——故障时能恢复，而不是让用户从头再来。

## 相关资源

- GitHub：[langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)
- 文档：[docs.langchain.com/oss/python/langgraph](https://docs.langchain.com/oss/python/langgraph/overview)
- API 参考：[reference.langchain.com/python/langgraph](https://reference.langchain.com/python/langgraph)
- 快速入门：[docs.langchain.com/oss/python/langgraph/quickstart](https://docs.langchain.com/oss/python/langgraph/quickstart)
- LangGraph.js：[github.com/langchain-ai/langgraphjs](https://github.com/langchain-ai/langgraphjs)
- LangChain Academy：[academy.langchain.com](https://academy.langchain.com/courses/intro-to-langgraph)
