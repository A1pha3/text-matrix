---
title: "Shannon：KeygraphHQ 出品的多智能体框架，让 AI 系统具备分层记忆与人类反馈能力"
date: "2026-04-07T15:50:00+08:00"
slug: shannon-keygraph-multi-agent-framework-guide
description: "Shannon 是 KeygraphHQ 推出的多智能体框架，核心创新包括三层记忆架构（Working/Episodic/Semantic）和 Human-in-the-Loop 机制，让 AI Agent 真正具备长期记忆和关键决策的人类监督能力。"
categories: ["技术笔记"]
tags: ["AI Agent", "多智能体", "Shannon", "记忆系统", "Human-in-the-Loop"]
draft: false
hiddenFromHomePage: true
---

# Shannon：KeygraphHQ 出品的多智能体框架，让 AI 系统具备分层记忆与人类反馈能力

## 概述

Shannon 是由前 DeepMind 团队创立的 KeygraphHQ 开发的一款多智能体框架，专注于构建**可扩展、可靠、正确**的分布式 AI 系统。与传统 Agent 框架不同，Shannon 引入了**分层记忆系统**和**人类反馈循环**（Human-in-the-Loop），让 AI Agent 能够维护长期上下文，并在关键决策点接受人类指导与纠正。

**基础信息：**
- GitHub：github.com/KeygraphHQ/shannon
- Stars：3.2k
- Fork：272
- License：MIT
- 语言：Python 100%
- 创始人背景：前 DeepMind 研究团队

**设计目标**：Build scalable, reliable, and correct distributed systems with AI agents.

---

## 1. 为什么需要分层记忆系统？

### 1.1 传统 Agent 的记忆困境

传统 Agent 系统面临的主要问题是**上下文长度限制**。即使 context window 再大，也不可能将所有历史信息都放入 prompt 中。当对话历史超过一定长度后，模型会"遗忘"早期的重要信息，导致：

- **连贯性丧失**：Agent 无法回忆之前的关键决策
- **重复工作**：Agent 反复询问相同信息
- **推理倒退**：基于不完整信息的决策质量下降

### 1.2 Shannon 的解决方案：三层记忆架构

Shannon 提出了**三层记忆架构**：

```
┌─────────────────────────────────────────────────────────────┐
│                    Working Memory                        │
│              (当前上下文，快速衰减)                      │
│         存储当前对话、正在执行的任务、即时状态             │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑ 遗忘/固化
┌─────────────────────────────────────────────────────────────┐
│                   Episodic Memory                         │
│              (事件记忆，中期保留)                          │
│     存储关键事件、决策点、任务里程碑，按重要性衰减          │
└─────────────────────────────────────────────────────────────┘
                            ↓ ↑ 抽象/总结
┌─────────────────────────────────────────────────────────────┐
│                   Semantic Memory                          │
│               (语义记忆，长期持久)                         │
│   存储事实知识、常识、长期目标、核心价值观（持久存储）      │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 记忆衰减机制

Shannon 的记忆不是静态存储，而是**动态衰减**的：

- **Importance Decay**：每条记忆都有重要性评分（0-1），定期衰减
- **Retrieval Threshold**：低于阈值的记忆被"遗忘"
- **Consolidation**：重要 episodic 记忆可晋升为 semantic 记忆

```python
# 记忆配置示例
memory_config = {
    "episodic_decay": 0.15,      # 事件记忆衰减率 15%/天
    "semantic_persistence": True,   # 语义记忆持久化
    "importance_threshold": 0.3,   # 重要性阈值
}
```

---

## 2. Human-in-the-Loop：让人类参与关键决策

### 2.1 为什么需要人类介入？

即使是最强大的 LLM，也会在某些情况下做出**不安全、不可靠或有偏见的决策**。Shannon 引入了 `humancore` 机制，允许 Agent 在关键决策点暂停并向人类请求指导。

### 2.2 humancore 工作原理

```python
from shannon import Agent
from shannon.humancore import HumanApproval

agent = Agent(
    model="claude-sonnet-4-20250514",
    role="financial_advisor",
    tools=["stock_api", "news_scraper"],
    humancore=HumanApproval(
        approval_types=["trade", "risk_assessment"],
        timeout_seconds=300
    )
)

# Agent 在执行交易前会暂停，等待人类批准
result = agent.run("Buy 100 shares of NVDA")
# → Agent pauses: "我想执行这笔交易，请确认：[批准/修改/取消]"
```

### 2.3 应用场景

| 场景 | 无 Human-in-Loop | 有 Human-in-Loop |
|------|-----------------|-----------------|
| 金融交易 | 可能执行危险交易 | 人类批准大额交易 |
| 医疗建议 | 可能给出不当建议 | 关键医疗决策需确认 |
| 内容生成 | 可能产生有害内容 | 敏感内容需审核 |
| 系统操作 | 可能执行破坏性操作 | 危险操作需批准 |

---

## 3. 核心架构解析

### 3.1 组件架构

```
┌──────────────────────────────────────────────────────────────┐
│                        Agent                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Memory   │  │  Tools   │  │   LLM    │  │Humancore│ │
│  │  System  │  │ Registry │  │ Interface│  │         │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│        ↓            ↓             ↓              ↓            │
│  ┌────────────────────────────────────────────────────┐  │
│  │               Supervisor (生命周期管理)               │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│                      Executor                               │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │ Task Queue  │  │ Retry Logic │  │Circuit Breaker│   │
│  └──────────────┘  └──────────────┘  └────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 核心类定义

```python
class Agent:
    """Shannon Agent 核心类"""
    def __init__(
        self,
        model: str,                    # LLM 模型标识
        role: str,                     # Agent 角色描述
        goal: str,                     # Agent 目标
        memory: Memory = None,          # 记忆系统（可选）
        tools: List[Tool] = None,     # 可用工具列表
        humancore: HumanCore = None,   # 人类反馈配置
        **config
    ):
        self.model = model
        self.role = role
        self.goal = goal
        self.memory = memory or HierarchicalMemory()
        self.tools = ToolRegistry(tools)
        self.humancore = humancore
        self.supervisor = Supervisor(self)
        self.executor = Executor(self)
```

### 3.3 记忆系统实现

```python
class HierarchicalMemory:
    """三层记忆系统"""
    def __init__(
        self,
        episodic: EpisodicMemory,
        semantic: SemanticMemory,
        working: WorkingMemory
    ):
        self.episodic = episodic    # 事件记忆
        self.semantic = semantic    # 语义记忆
        self.working = working     # 工作记忆
    
    def store(self, content: str, memory_type: str, importance: float):
        """存储记忆，自动分类到对应层级"""
        if memory_type == "event":
            self.episodic.add(content, importance)
        elif memory_type == "fact":
            self.semantic.add(content, importance)
        else:
            self.working.update(content)
    
    def retrieve(self, query: str, depth: str = "all") -> List[str]:
        """检索记忆"""
        results = []
        if depth in ["all", "working"]:
            results.extend(self.working.query(query))
        if depth in ["all", "episodic"]:
            results.extend(self.episodic.query(query))
        if depth in ["all", "semantic"]:
            results.extend(self.semantic.query(query))
        return results
```

---

## 4. 工具注册与动态发现

### 4.1 传统工具调用的局限

传统 Agent 需要预先定义所有工具，缺少灵活性。当需要新工具时，必须修改代码并重启系统。

### 4.2 Shannon 的动态工具注册

Shannon 提供了**运行时工具注册**机制：

```python
# 方式一：装饰器注册
@agent.tool_registry.register
def web_search(query: str) -> str:
    """网络搜索工具"""
    return search(query)

# 方式二：运行时注册
agent.tools.register(
    name="database_query",
    func=execute_sql,
    description="执行 SQL 数据库查询",
    parameters={"type": "object", "properties": {...}}
)

# 方式三：远程工具注册
agent.tools.register_remote(
    url="https://api.example.com/tools",
    auth=api_key
)
```

### 4.3 工具注册表

```python
class ToolRegistry:
    """工具注册表"""
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._metadata: Dict[str, ToolMetadata] = {}
    
    def register(self, tool: Tool, name: str = None):
        name = name or tool.name
        self._tools[name] = tool
        self._metadata[name] = ToolMetadata(
            name=name,
            description=tool.description,
            parameters=tool.parameters,
            tags=tool.tags or []
        )
    
    def discover(self, query: str) -> List[Tool]:
        """基于查询语义发现相关工具"""
        return semantic_search(
            query, 
            self._metadata,
            threshold=0.7
        )
```

---

## 5. 流式响应与可观测性

### 5.1 思考流（Thought Streaming）

Shannon 支持**实时思考流**，让用户能够观察 Agent 的推理过程：

```python
# 启用思考流
for event in agent.run_stream("分析今年的 AI 发展趋势"):
    if event.type == "thought":
        print(f"🤔 思考: {event.content}")
    elif event.type == "action":
        print(f"⚡ 行动: {event.content}")
    elif event.type == "observation":
        print(f"📝 观察: {event.content}")
    elif event.type == "final":
        print(f"✅ 最终回答: {event.content}")
```

输出示例：
```
🤔 思考: 用户询问 AI 发展趋势，我需要从多个维度分析...
🤔 思考: 首先考虑技术进步维度：模型能力、效率提升...
⚡ 行动: 调用 search_tools['web_search'] 搜索最新 AI 报告
📝 观察: 找到 15 篇相关报告，开始阅读...
🤔 思考: 基于报告内容，我需要提炼核心趋势...
✅ 最终回答: 2026 年 AI 发展的三大趋势是...
```

### 5.2 内置 Tracing

Shannon 提供开箱即用的**分布式追踪**：

```python
from shannon.observability import tracer

# 启用追踪
tracer.enable(
    service_name="shannon-agent",
    exporter="jaeger",  # 支持 jaeger, zipkin, console
    endpoint="http://localhost:14268/api/traces"
)

# 自动追踪所有 Agent 操作
with tracer.start_as_current_span("agent_run") as span:
    span.set_attribute("agent.role", agent.role)
    span.set_attribute("agent.model", agent.model)
    result = agent.run(task)
    span.set_attribute("result.length", len(result))
```

---

## 6. 容错与稳定性

### 6.1 重试机制

```python
from shannon.retry import RetryConfig, exponential_backoff

@agent.retry(
    config=RetryConfig(
        max_attempts=3,
        backoff=exponential_backoff(base=2),
        retry_on=["RateLimitError", "NetworkError"]
    )
)
def uncertain_operation():
    """不稳定操作，自动重试"""
    return risky_api_call()
```

### 6.2 熔断器（Circuit Breaker）

```python
from shannon.circuit_breaker import CircuitBreaker

# 为外部 API 设置熔断器
api_breaker = CircuitBreaker(
    failure_threshold=5,      # 5 次失败后打开
    recovery_timeout=60,     # 60 秒后尝试半开
    expected_exception=APIError
)

@api_breaker
def call_external_service():
    return http_get("https://api.example.com")
```

---

## 7. 快速入门

### 7.1 安装

```bash
pip install shannon-ai

# 或从源码安装
git clone https://github.com/KeygraphHQ/shannon.git
cd shannon
pip install -e .
```

### 7.2 首个 Agent

```python
from shannon import Agent

# 创建研究助手 Agent
researcher = Agent(
    model="claude-sonnet-4-20250514",
    role="research_assistant",
    goal="帮助用户高效地进行研究和信息收集",
    tools=["web_search", "document_reader", "note_taker"]
)

# 运行任务
result = researcher.run(
    "研究 GPT-5 的最新进展及其对教育领域的影响"
)

print(result)
```

### 7.3 带记忆的 Agent

```python
from shannon import Agent
from shannon.memory import HierarchicalMemory

# 创建带持久记忆的 Agent
memory = HierarchicalMemory(
    episodic=EpisodicMemory(capacity=1000),
    semantic=SemanticMemory(persistent=True),
    working=WorkingMemory(max_size=10)
)

assistant = Agent(
    model="claude-sonnet-4-20250514",
    role="personal_assistant",
    goal="成为用户的私人助理",
    memory=memory
)

# 后续对话中，Agent 会记住之前的重要信息
assistant.run("我的名字叫张三")
assistant.run("我最近在学习 Python")  # Agent 会记住这些信息
assistant.run("我叫什么名字？我在学什么？")  # → "您叫张三，在学 Python"
```

---

## 8. 与其他框架的对比

| 特性 | Shannon | LangChain | AutoGPT | CrewAI |
|------|---------|-----------|---------|--------|
| **分层记忆** | ✅ 三层架构 | ❌ 无 | ❌ 无 | ❌ 无 |
| **Human-in-Loop** | ✅ humancore | ❌ 无 | ❌ 无 | ❌ 无 |
| **流式响应** | ✅ 思考流 | ✅ | ✅ | ❌ |
| **分布式追踪** | ✅ 内置 | 需额外配置 | ❌ | ❌ |
| **熔断器** | ✅ 内置 | ❌ 无 | ❌ 无 | ❌ 无 |
| **记忆持久化** | ✅ Semantic | ✅ | ❌ | ❌ |
| **动态工具注册** | ✅ | ❌ | ❌ | ❌ |

---

## 9. 适用场景

### 9.1 推荐使用 Shannon 的场景

- **复杂多步骤任务**：需要 Agent 维护长期上下文的任务
- **需要人类监督的关键决策**：金融、医疗、法律等高风险领域
- **需要记忆的系统**：客服、个人助理、研究助手
- **需要可观测性的生产系统**：需要追踪和调试的生产环境

### 9.2 不推荐使用的场景

- **简单单次任务**：不需要记忆的简单查询
- **资源受限环境**：Shannon 的记忆系统需要额外资源
- **完全自主运行**：需要完全无人值守的场景（需配合 humancore）

---

## 10. 常见问题

**Q: Shannon 与 LangChain 的区别是什么？**

A: LangChain 是一个通用的 LLM 应用框架，而 Shannon 专注于**多智能体编排**。Shannon 的主要差异是分层记忆系统和 Human-in-the-Loop 机制，这两个特性在 LangChain 中没有原生支持。

**Q: 记忆系统会无限增长吗？**

A: 不会。Shannon 使用**重要性衰减**机制，重要性低于阈值的记忆会被自动清除。同时可以通过配置设置各层记忆的容量上限。

**Q: Human-in-the-Loop 会影响 Agent 的自主性吗？**

A: 不会。humancore 支持**选择性触发**——只有特定类型的关键操作（如大额交易、敏感数据访问）才会暂停等待人类批准，普通操作仍然自动执行。

**Q: Shannon 支持哪些 LLM？**

A: 目前支持 Claude 系列、GPT-4 系列，以及兼容 OpenAI API 接口的其他模型。

---

## 总结

Shannon 代表了多智能体框架的一个方向——关注**记忆管理**和**人类协作**，而非仅仅关注 Agent 的**推理能力**。其分层记忆系统让 Agent 能够维护长期上下文，而 humancore 机制则确保了关键决策的安全可控。对于需要构建复杂 AI 系统的开发者来说，Shannon 提供了一个可直接用于生产的选择。

**相关资源：**
- GitHub：github.com/KeygraphHQ/shannon
- 文档：docs.shannon.ai
- Discord：discord.gg/keygraphhq

---

*文章更新时间：2026-04-07*
*本文档使用 cn-doc-writer 技能生成*
