---
title: "Claude API基础专题（七）：Agent架构与智能体设计"
date: "2026-03-25T10:00:00+08:00"
slug: "claude-api-agent-architecture-design"
aliases:
  - /posts/tech/claude-api-agent-architecture-design/
description: "Claude API Agent 架构设计深度指南：单 Agent 与多 Agent 系统、并行与链式执行模式、条件路由与状态管理、错误处理与恢复机制，以及生产环境的安全考量与部署方案。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "AI Agent", "Python"]
---

# Claude API 基础专题（七）：Agent 架构与智能体设计

> **目标读者**：构建复杂 AI 应用系统的架构师与高级开发者
> **前置知识**：已完成第一篇《API基础》、第二篇《提示词工程》、第三篇《工具调用》、第四篇《RAG系统》、第五篇《MCP协议》、第六篇《Claude Code与Computer Use》

---

## 学习目标

1. 说清 Agent 与单次工具调用的边界，指出五个必备要素中缺一项会导致什么后果
2. 写出一个状态外部化、终止条件前置的最小 Agent 主循环
3. 根据任务特征在星型、链式、网状三种多 Agent 架构中做出取舍，并说明各自的失败模式
4. 针对上下文溢出、限流、工具失败三类常见错误，给出对应的重试与回退策略
5. 列出生产环境 Agent 系统上线前必须配置的权限、沙箱与监控项

---

## 章节导航

| 小节 | 主题 | 重要程度 |
|------|------|----------|
| 7.1 | 从工具调用到 Agent：跨越的关键一步 | ⭐⭐⭐⭐⭐ |
| 7.2 | 单 Agent 系统架构 | ⭐⭐⭐⭐⭐ |
| 7.3 | 多 Agent 协作系统 | ⭐⭐⭐⭐⭐ |
| 7.4 | 执行模式：并行与链式 | ⭐⭐⭐⭐⭐ |
| 7.5 | 状态管理与上下文 | ⭐⭐⭐⭐⭐ |
| 7.6 | 错误处理与容错机制 | ⭐⭐⭐⭐⭐ |
| 7.7 | 安全与权限管理 | ⭐⭐⭐⭐ |
| 7.8 | 生产环境推荐做法 | ⭐⭐⭐⭐⭐ |

---

## 7.1 从工具调用到 Agent：跨越的关键一步

### 为什么需要 Agent？

工具调用能解决不少问题，但遇到多步骤、有分支、需要保留中间状态的任务时就会卡住。先看工具调用的典型模式：

```python
result = await client.messages.create(
    model="claude-opus-4-20250514",
    messages=[{"role": "user", "content": "帮我查一下北京天气"}],
    tools=[{"name": "get_weather", ...}]
)
```

这个模式里，LLM 是被动响应者：用户提问 → LLM 调用工具 → 工具返回结果 → LLM 回答。LLM 不持有状态，不主动决策，只根据当前输入决定调用哪个工具。

现实任务往往比这复杂：

| 任务特征 | 工具调用的局限 | Agent 能补上的能力 |
|----------|----------------|-------------------|
| 多步骤决策 | 每次决策独立 | 保持目标状态 |
| 条件分支 | 无法根据结果跳转 | 动态规划路径 |
| 长期任务 | 上下文会丢失 | 持久化状态 |
| 多工具协同 | 缺乏编排能力 | 编排执行流程 |
| 错误恢复 | 失败即终止 | 重试和回退 |

### Agent 的本质定义

Agent 可以拆成五个要素：

> **Agent = LLM + 状态 + 工具 + 执行循环 + 终止条件**

```
┌─────────────────────────────────────────────────────────────┐
│                        Agent 系统                           │
│   ┌───────────┐   ┌───────────┐   ┌───────────┐            │
│   │    LLM    │   │   状态    │   │   工具    │            │
│   │ 理解/推理  │   │ 目标/上下文 │   │ 搜索/代码  │            │
│   └─────┬─────┘   └─────┬─────┘   └─────┬─────┘            │
│         └───────┬───────┘               │                  │
│           ┌─────▼─────┐                 │                  │
│           │  执行循环  │─────────────────┘                  │
│           │ 观察→决策→执行│                                 │
│           └─────┬─────┘                                    │
│           ┌─────▼─────┐                                    │
│           │  终止条件  │                                    │
│           │ 完成/出错/超时│                                 │
│           └───────────┘                                    │
└─────────────────────────────────────────────────────────────┘
```

缺了任何一个都跑不起来：没有 LLM 就没有智能决策，没有状态就无法处理多步骤任务，没有工具就无法影响外部世界，没有执行循环就无法持续工作，没有终止条件就会无限循环。

### Agent vs 传统软件

| 维度 | 传统软件 | Agent |
|------|---------|-------|
| 决策方式 | 确定性的 if-else | 基于 LLM 的概率推理 |
| 流程定义 | 预先设计 | 运行时动态规划 |
| 错误处理 | 显式 try-catch | 自我纠错能力 |
| 状态管理 | 显式变量 | 隐式上下文 |
| 扩展方式 | 模块化 | 添加工具/提示词 |
| 可预测性 | 高 | 中（有一定随机性） |

---

## 7.2 单 Agent 系统架构

### 最小可运行 Agent

```python
from anthropic import Anthropic
from dataclasses import dataclass, field
from typing import Any
import asyncio

@dataclass
class AgentState:
    goal: str
    messages: list[dict] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    results: list[dict] = field(default_factory=list)
    iterations: int = 0
    max_iterations: int = 10

class SimpleAgent:
    def __init__(self, api_key: str, tools: list[dict]):
        self.client = Anthropic(api_key=api_key)
        self.tools = tools

    async def run(self, goal: str) -> dict[str, Any]:
        state = AgentState(goal=goal)
        state.messages.append({"role": "user", "content": f"目标：{goal}\n\n请决定下一步行动。"})

        while not self._should_terminate(state):
            state.iterations += 1
            response = await self._think(state)

            tool_blocks = [b for b in response.content if b.type == "tool_use"]
            if tool_blocks:
                state.messages.append({"role": "assistant", "content": response.content})
                tool_results = []
                for tb in tool_blocks:
                    result = await self._execute_tool(tb)
                    state.results.append(result)
                    tool_results.append({"type": "tool_result", "tool_use_id": tb.id, "content": str(result)})
                state.messages.append({"role": "user", "content": tool_results})
            else:
                text = "".join(b.text for b in response.content if b.type == "text")
                return {"status": "completed", "goal": goal, "result": text, "iterations": state.iterations}

        return {"status": "terminated", "goal": goal, "reason": "max_iterations_reached", "iterations": state.iterations}

    def _should_terminate(self, state: AgentState) -> bool:
        return state.iterations >= state.max_iterations

    async def _think(self, state: AgentState) -> Any:
        return self.client.messages.create(
            model="claude-opus-4-20250514", max_tokens=4096,
            messages=state.messages, tools=self.tools,
        )

    async def _execute_tool(self, tool_use: Any) -> dict:
        return {"tool": tool_use.name, "args": tool_use.input, "output": f"Tool {tool_use.name} executed"}
```

上面这段代码有两处与 Anthropic Messages API 规范相关的细节，容易踩坑：

1. **tool_result 必须以 `role: "user"` 回传**，且 `content` 是 `tool_result` 类型的块数组，每块带 `tool_use_id` 指向对应的工具调用。如果直接把工具返回值塞进 `role: "assistant"`，API 会报 400。
2. **`_think` 必须传入完整的 `state.messages`**，否则 LLM 看不到上一轮的工具调用和结果，会重复发起相同的调用。

参考来源：[Anthropic Messages API - Tool use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)

### 为什么要这样设计？

**1. 状态外部化**

```python
# 好
state = AgentState(goal=goal)
while not self._should_terminate(state): ...

# 不好：状态散落在 self 属性里
while self.iterations < self.max_iterations:
    self.messages.append(...)
```

把状态收进 dataclass，是为了能序列化保存（断点续跑）、热切换（修改状态不影响逻辑）、并行运行多个 Agent 实例。

**2. 终止条件前置判断**

```python
# 好：先检查再执行
while not self._should_terminate(state): ...

# 不好：先执行再检查
while True:
    response = await self._think(state)
    if self._should_terminate(state): break
```

先检查再执行，避免在达到终止条件后还多跑一次 LLM 推理——既浪费 token，又可能触发不必要的工具调用。

**3. 完整记录对话历史**

每次工具调用后，assistant 响应和 tool_result 都要追加到 `state.messages`，否则 LLM 看不到之前的结果，会重复发起相同调用。

---

## 7.3 多 Agent 协作系统

### 为什么需要多 Agent？

单个 Agent 处理复杂任务时会遇到几个具体问题：要同时精通多个领域、上下文越来越长导致响应变慢、一个环节出错可能污染整个对话。以旅行规划为例：

```
单个Agent的问题：
- 需要同时是旅行专家 + 酒店专家 + 天气专家 + 预算专家
- 知识过于分散，难以精通所有领域
- 单一Agent处理所有任务，响应会变慢

多Agent方案：
- 主Agent负责任务分解和协调
- 酒店Agent负责搜索和推荐酒店
- 天气Agent负责查询天气预报
- 预算Agent负责计算和控制预算
```

拆分后每个 Agent 的上下文更短、职责更窄，主 Agent 的工作收敛到分解任务和汇总结果，不必自己精通每个领域。

### 多 Agent 架构模式

**模式一：星型架构（主从模式）**

```text
                    ┌─────────────┐
                    │  主Agent    │
                    │ (协调者)    │
                    └──────┬──────┘
          ┌────────────────┼────────────────┐
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │ 子Agent1  │   │ 子Agent2  │   │ 子Agent3  │
    │ (酒店)    │   │ (天气)    │   │ (预算)    │
    └───────────┘   └───────────┘   └───────────┘
```

```python
class MasterAgent:
    def __init__(self):
        self.sub_agents = {"hotel": HotelAgent(), "weather": WeatherAgent(), "budget": BudgetAgent()}

    async def run(self, task: str) -> dict:
        subtasks = await self._decompose_task(task)
        results = await asyncio.gather(*[
            self._run_subagent(name, subtask) for name, subtask in subtasks.items()
        ])
        return await self._aggregate_results(results)
```

**模式二：链式架构（流水线模式）**

```text
┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│  Agent1   │ →  │  Agent2   │ →  │  Agent3   │ →  │  Agent4   │
│ (预处理)   │    │ (核心处理) │    │ (验证)    │    │ (输出)    │
└───────────┘    └───────────┘    └───────────┘    └───────────┘
```

```python
class ChainAgent:
    def __init__(self):
        self.chain = [PreprocessAgent(), CoreAgent(), ValidationAgent(), OutputAgent()]

    async def run(self, input_data: Any) -> Any:
        current = input_data
        for agent in self.chain:
            current = await agent.process(current)
            if not self._is_valid(current):
                return await self._handle_error(current, agent)
        return current
```

**模式三：网状架构（对等模式）**

```python
class PeerNetwork:
    """没有中心协调者，Agent 之间可直接通信"""
    async def run(self, task: str) -> dict:
        queue = MessageQueue()
        agents = [Agent(i) for i in range(3)]
        tasks = [agent.run(queue) for agent in agents]
        await queue.publish("task", task)
        results = await asyncio.gather(*tasks)
        return self._merge_results(results)
```

### 如何选择架构模式？

| 场景 | 推荐架构 | 原因 |
|------|----------|------|
| 任务明确、子任务独立 | 星型 | 便于并行、易于管理 |
| 处理流程固定 | 链式 | 清晰、易于调试 |
| 横向协作、无固定流程 | 网状 | 灵活、适应性强 |
| 需要高可靠性 | 星型+链式混合 | 主备冗余 |

---

## 7.4 执行模式：并行与链式

### 并行执行

当多个子任务彼此独立时，并行执行能把总耗时从 N×T 压到接近 T：

```python
async def parallel_execution(tasks: list[dict]) -> list[dict]:
    async def execute_single(task: dict) -> dict:
        agent = create_agent(task["type"])
        result = await agent.run(task["input"])
        return {"task_id": task["id"], "result": result}

    return await asyncio.gather(*[execute_single(t) for t in tasks])
```

判断一个任务能不能并行，看的是它是否依赖其他任务的输出：

```python
# 适合并行：任务之间无依赖
parallel_tasks = [
    {"id": 1, "type": "search", "input": "北京天气"},
    {"id": 2, "type": "search", "input": "上海天气"},
    {"id": 3, "type": "search", "input": "广州天气"},
]

# 不适合并行：存在依赖关系
sequential_tasks = [
    {"id": 1, "type": "search", "input": "用户ID"},
    {"id": 2, "type": "fetch", "input": "依赖任务1的结果"},
    {"id": 3, "type": "save", "input": "依赖任务2的结果"},
]
```

### 链式执行

```python
async def chain_execution(tasks: list[dict]) -> dict:
    context = {}
    for task in tasks:
        task_input = await self._prepare_input(task, context)
        agent = create_agent(task["type"])
        result = await agent.run(task_input)
        context[task["id"]] = result
        if not self._is_success(result):
            if task.get("retry"):
                result = await self._retry(task, context)
            else:
                raise ExecutionError(f"Task {task['id']} failed")
    return context
```

### 并行与链式的混合模式

```python
class HybridExecutor:
    """并行 + 链式结合：先并行执行独立任务，再按依赖链式执行"""
    async def run(self, workflow: dict) -> dict:
        parallel_results = await self._parallel_phase(workflow["parallel_tasks"])
        context = {"parallel": parallel_results}
        chain_result = await self._chain_phase(workflow["chain_tasks"], context)
        return {"parallel_results": parallel_results, "chain_result": chain_result}

    async def _parallel_phase(self, tasks: list[dict]) -> dict:
        results = await asyncio.gather(*[self._execute(task) for task in tasks])
        return {task["id"]: result for task, result in zip(tasks, results)}

    async def _chain_phase(self, tasks: list[dict], context: dict) -> dict:
        for task in tasks:
            context[task["id"]] = await self._execute(task, context)
        return context
```

---

## 7.5 状态管理与上下文

### 状态持久化的重要性

Agent 跑得越久，对话历史越长，迟早会撞上上下文窗口上限。撞上后有两条路：把旧历史压缩成摘要，或按相关性挑出一部分留下。

**方案一：状态压缩与摘要**

```python
class StateManager:
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.summaries = []
        self.working_memory = {}

    def add_interaction(self, user_msg: str, assistant_msg: str):
        self.summaries.append({"user": user_msg, "assistant": assistant_msg, "timestamp": now()})
        if len(self.summaries) > self.max_history:
            self._compress()

    def _compress(self):
        recent = self.summaries[-self.max_history:]
        older = self.summaries[:-self.max_history]
        summary = self.client.messages.create(
            model="claude-opus-4-20250514",
            messages=[{"role": "user", "content": f"请总结以下对话的关键信息：{self._format_conversation(older)}\n提取：1.用户的主要目标 2.已完成的关键步骤 3.当前状态 4.重要的中间结果"}]
        )
        self.working_memory["conversation_summary"] = summary.content[0].text
        self.summaries = recent

    def get_context_for_llm(self) -> str:
        parts = []
        if "conversation_summary" in self.working_memory:
            parts.append(f"对话摘要：{self.working_memory['conversation_summary']}")
        for item in self.summaries[-self.max_history:]:
            parts.append(f"用户：{item['user']}\n助手：{item['assistant']}")
        return "\n".join(parts)
```

**方案二：按相关性挑选上下文**

```python
class SmartContextManager:
    def __init__(self, max_tokens: int = 150000):
        self.max_tokens = max_tokens
        self.priority_levels = {
            "critical": ["目标", "关键约束", "核心决策"],
            "important": ["中间结果", "用户偏好", "当前状态"],
            "normal": ["一般对话", "解释说明"],
            "discardable": ["问候", "重复确认"],
        }

    def build_context(self, all_items: list[dict], current_task: str) -> str:
        weights = {"critical": 1.0, "important": 0.7, "normal": 0.4, "discardable": 0.0}
        scored = []
        for item in all_items:
            relevance = self._calculate_relevance(item, current_task)
            priority = self._get_priority(item)
            scored.append((relevance * weights.get(priority, 0.5), item))

        scored.sort(key=lambda x: x[0], reverse=True)
        selected, total = [], 0
        for _, item in scored:
            tokens = self._estimate_tokens(item)
            if total + tokens <= self.max_tokens:
                selected.append(item)
                total += tokens
        return self._format_selected(selected)
```

---

## 7.6 错误处理与容错机制

```python
from enum import Enum

class ErrorType(Enum):
    LLM_TIMEOUT = "llm_timeout"
    LLM_RATE_LIMIT = "llm_rate_limit"
    TOOL_EXECUTION_FAILED = "tool_failed"
    TOOL_TIMEOUT = "tool_timeout"
    CONTEXT_OVERFLOW = "context_overflow"
    MAX_ITERATIONS = "max_iterations"

class ErrorAction(Enum):
    RETRY = "retry"
    RETRY_WITH_FALLBACK = "retry_fallback"
    FAIL = "fail"
    RETURN_BEST_RESULT = "return_best"

class ErrorHandler:
    def __init__(self):
        self.error_counts = {}

    async def handle(self, error: Exception, state: AgentState) -> ErrorAction:
        error_type = self._classify(error)
        self._log_error(error_type, error, state)
        handlers = {
            ErrorType.LLM_TIMEOUT: self._handle_timeout,
            ErrorType.LLM_RATE_LIMIT: self._handle_rate_limit,
            ErrorType.TOOL_EXECUTION_FAILED: self._handle_tool_failure,
            ErrorType.CONTEXT_OVERFLOW: self._handle_context_overflow,
            ErrorType.MAX_ITERATIONS: self._handle_max_iterations,
        }
        return await handlers.get(error_type, self._handle_unknown)(error, state)

    async def _handle_timeout(self, error, state):
        state.context["retry_count"] = state.context.get("retry_count", 0) + 1
        if state.context["retry_count"] < 3:
            await asyncio.sleep(2 ** state.context["retry_count"])  # 指数退避
            return ErrorAction.RETRY
        return ErrorAction.FAIL

    async def _handle_rate_limit(self, error, state):
        await asyncio.sleep(getattr(error, "retry_after", 60))
        return ErrorAction.RETRY

    async def _handle_tool_failure(self, error, state):
        if self._has_fallback(getattr(error, "tool_name", None)):
            state.context["using_fallback"] = True
            return ErrorAction.RETRY_WITH_FALLBACK
        return ErrorAction.FAIL

    async def _handle_context_overflow(self, error, state):
        manager = state.context.get("state_manager")
        if manager:
            manager._compress()
            return ErrorAction.RETRY
        return ErrorAction.FAIL

    async def _handle_max_iterations(self, error, state):
        return ErrorAction.RETURN_BEST_RESULT
```

### 重试与回退机制

```python
class RetryPolicy:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0,
                 exponential_base: float = 2.0, max_delay: float = 60.0, jitter: bool = True):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.exponential_base = exponential_base
        self.max_delay = max_delay
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
        if self.jitter:
            import random
            delay *= 0.5 + random.random()
        return delay

class FallbackManager:
    def __init__(self):
        self.fallback_map = {
            "primary_search": ["fallback_search_1", "fallback_search_2"],
            "primary_translate": ["fallback_translate"],
            "primary_code_exec": ["fallback_sandbox"],
        }
        self.usage_stats = {}

    async def execute_with_fallback(self, primary_tool: str, args: dict) -> Any:
        last_error = None
        for tool in [primary_tool] + self.fallback_map.get(primary_tool, []):
            try:
                result = await self._execute_tool(tool, args)
                self._record_success(tool)
                return result
            except Exception as e:
                last_error = e
                self._record_failure(tool, e)
        raise AllToolsFailedError([primary_tool] + self.fallback_map.get(primary_tool, []), last_error)
```

---

## 7.7 安全与权限管理

```python
from enum import Enum

class PermissionScope(Enum):
    NONE = "none"
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"

class Permission:
    def __init__(self, scopes: list[PermissionScope] = None, file_paths: list[str] = [],
                 allowed_tools: list[str] = [], allowed_domains: list[str] = [],
                 max_execution_time: int = 300, max_api_calls: int = 100):
        self.scopes = scopes or [PermissionScope.READ]
        self.file_paths = file_paths
        self.allowed_tools = allowed_tools
        self.allowed_domains = allowed_domains
        self.max_execution_time = max_execution_time
        self.max_api_calls = max_api_calls

class SecurityManager:
    def __init__(self, permission: Permission):
        self.permission = permission
        self.audit_log = []

    def check_file_access(self, path: str, mode: str) -> bool:
        if mode == "write" and PermissionScope.WRITE not in self.permission.scopes:
            return False
        import os
        real = os.path.realpath(path)
        return any(real.startswith(os.path.realpath(p)) for p in self.permission.file_paths)

    def check_tool_usage(self, tool_name: str) -> bool:
        return tool_name in self.permission.allowed_tools

    def check_network_access(self, domain: str) -> bool:
        return any(domain.endswith(a) or domain == a for a in self.permission.allowed_domains)

    def audit(self, operation: str, details: dict):
        self.audit_log.append({"timestamp": now(), "operation": operation, "details": details})
```

### 沙箱隔离

```python
class SandboxConfig:
    def __init__(self, use_sandbox: bool = True, network_isolation: bool = True,
                 filesystem_boundary: str = "/workspace/sandbox", memory_limit: str = "2GB"):
        self.use_sandbox = use_sandbox
        self.network_isolation = network_isolation
        self.filesystem_boundary = filesystem_boundary
        self.memory_limit = memory_limit

class SandboxExecutor:
    def __init__(self, config: SandboxConfig):
        self.config = config

    async def execute(self, code: str, language: str) -> Any:
        if not self.config.use_sandbox:
            return await self._execute_direct(code, language)
        sandbox = await self._prepare_sandbox()
        sandbox.set_memory_limit(self.config.memory_limit)
        sandbox.set_network_isolation(self.config.network_isolation)
        sandbox.set_filesystem_boundary(self.config.filesystem_boundary)
        try:
            return await sandbox.run(code, language)
        finally:
            await sandbox.cleanup()
```

---

## 7.8 生产环境推荐做法

### 架构设计原则

1. **分离关注点**：Agent 核心逻辑与工具实现分离，状态管理与执行逻辑分离，安全检查与业务逻辑分离
2. **失败设计**：每个组件都可能失败，优雅降级而非整体崩溃，快速失败便于诊断
3. **可观测性**：日志记录每个关键步骤，指标追踪 QPS/延迟/错误率，请求全链路追踪
4. **资源管理**：限制并发请求数，控制内存使用，防止资源泄漏
5. **安全第一**：最小权限原则，纵深防御，审计追踪

### 监控与告警

```python
class AgentMonitor:
    metrics = {
        "requests_total": "总请求数", "requests_success": "成功请求数", "requests_failed": "失败请求数",
        "average_latency": "平均延迟", "p99_latency": "P99 延迟", "active_agents": "活跃Agent数",
        "tools_usage": "工具使用统计", "error_distribution": "错误分布",
    }

class AlertManager:
    rules = {
        "high_error_rate": {"condition": "error_rate > 0.05", "severity": "critical", "action": "notify_oncall"},
        "high_latency":    {"condition": "p99_latency > 30s", "severity": "warning",  "action": "notify_team"},
        "agent_timeout":   {"condition": "timeout_count > 10/min", "severity": "warning", "action": "investigate"},
    }
```

### 部署架构

```
负载均衡层（Nginx/云负载均衡）
    → API网关层（认证、限流、日志、路由）
        → Agent服务集群（Agent-1 ... Agent-N）
            → 工具服务（搜索服务、代码执行、API服务）
```

### 性能优化建议

| 优化项 | 方法 | 效果 |
|--------|------|------|
| 缓存 LLM 响应 | 对相同输入缓存响应 | 减少 API 调用 |
| 并行工具调用 | 不依赖结果的工具并行执行 | 降低延迟 |
| 状态压缩 | 对话历史压缩摘要 | 减少 token 消耗 |
| 预热机制 | 定期预加载模型 | 降低冷启动延迟 |
| 连接池复用 | 复用 HTTP/数据库连接 | 提高吞吐 |

缓存 LLM 响应需注意：如果工具结果会随时间变化（如查天气），缓存命中反而返回过期数据。建议只对纯函数式工具（固定文档检索、数学计算）开启缓存，并设 TTL。

### 常见问题排查

| 现象 | 可能原因 | 排查步骤 |
|------|----------|----------|
| Agent 反复调用同一个工具 | `_think` 没传完整 messages | 检查 `messages=state.messages` 是否传入 |
| API 报 400 `tool_use_id` not found | tool_result 的 `tool_use_id` 对不上 | 检查 `tool_use.id` 是否正确透传 |
| 上下文溢出 | 没有压缩历史 | 接入 StateManager 或每轮估算 token 数 |
| 工具超时导致 Agent 挂掉 | 没有重试策略 | 接入 RetryPolicy，做指数退避 |
| 危险操作 | 权限检查不完整 | 检查 `allowed_tools` 和 `file_paths` 白名单 |
| 并行子 Agent 结果丢失 | gather 中协程异常未被捕获 | 用 `return_exceptions=True` |

### 最小可运行示例

```python
import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

tools = [{
    "name": "get_weather",
    "description": "查询指定城市的天气",
    "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}
}]

def execute_tool(tool_use):
    if tool_use.name == "get_weather":
        return f"{tool_use.input['city']} 今天晴，25°C"
    raise ValueError(f"未知工具: {tool_use.name}")

def run_agent(goal: str, max_iterations: int = 10):
    messages = [{"role": "user", "content": goal}]
    for i in range(max_iterations):
        response = client.messages.create(
            model="claude-opus-4-20250514", max_tokens=1024, tools=tools, messages=messages,
        )
        tool_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_blocks:
            text = "".join(b.text for b in response.content if b.type == "text")
            print(f"[最终回答] {text}")
            return text
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for tb in tool_blocks:
            result = execute_tool(tb)
            print(f"[工具调用] {tb.name}({tb.input}) → {result}")
            results.append({"type": "tool_result", "tool_use_id": tb.id, "content": result})
        messages.append({"role": "user", "content": results})
    print("达到最大迭代次数，Agent 终止")

if __name__ == "__main__":
    run_agent("帮我查一下北京和上海的天气，然后总结哪个更适合出行")
```

运行前确保已安装 `anthropic` 并设置 `ANTHROPIC_API_KEY` 环境变量。

---

## 本章总结

### 核心知识点

| 知识点 | 关键点 |
|--------|--------|
| Agent 定义 | LLM + 状态 + 工具 + 执行循环 + 终止条件 |
| 单 Agent 架构 | 状态外部化、终止条件前置 |
| 多 Agent 协作 | 星型/链式/网状架构 |
| 执行模式 | 并行与链式混合 |
| 状态管理 | 压缩、摘要、智能选择 |
| 错误处理 | 分类处理、重试回退 |
| 安全机制 | 权限模型、沙箱隔离 |
| 生产实践 | 监控、告警、优化 |

### 自测题

**Q1**：Agent 的五个必备要素中，去掉"终止条件"会出现什么现象？

**Q2**：下面这段代码会导致什么问题？如何修复？
```python
response = client.messages.create(
    model="claude-opus-4-20250514",
    messages=[{"role": "user", "content": "继续"}],
    tools=tools,
)
```

**Q3**：星型架构和链式架构分别适合什么场景？如何组合？

**Q4**：`asyncio.gather` 中某个子 Agent 抛异常，默认行为是什么？如何避免单点失败拖垮全部？

**Q5**：为什么 tool_result 必须以 `role: "user"` 回传？

<details>
<summary>参考答案</summary>

**A1**：Agent 会无限循环，直到撞上 API 限流或上下文溢出。终止条件是防止 Agent 失控的最后一道闸。

**A2**：每次只发一条"继续"消息，LLM 看不到之前的工具调用和结果。修复方法：传入完整的 `state.messages`。

**A3**：星型适合子任务独立（同时查酒店、天气、景点）；链式适合有严格顺序依赖（查用户 → 查订单 → 生成报告）。组合：先并行跑独立子任务，再按依赖顺序跑链式任务。

**A4**：默认情况第一个异常时 gather 立即返回，其他协程被取消。用 `return_exceptions=True` 避免。

**A5**：Anthropic Messages API 要求 user 和 assistant 角色严格交替。tool_result 属于用户侧反馈，必须以 user 角色回传，否则 API 返回 400。

</details>

### 进阶路径

1. **MCP 协议与 Agent 结合**：把子 Agent 替换为 MCP 服务器，参考 [MCP 官方规范](https://modelcontextprotocol.io/)
2. **长时任务与断点续跑**：将 `AgentState` 序列化到数据库，实现崩溃恢复
3. **多 Agent 评估与调优**：搭建离线评估管线，参考 [Anthropic Agent 评估指南](https://docs.anthropic.com/en/docs/build-with-claude/agent-evals)
4. **成本控制**：监控 token 消耗，简单任务用 Haiku，复杂推理用 Opus
5. **安全加固**：加入人工审批环节（human-in-the-loop），高危操作强制确认

### 参考资料

- [Anthropic 官方文档 - Tool use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Anthropic 官方文档 - Agent patterns](https://docs.anthropic.com/en/docs/build-with-claude/agent-patterns)
- [Anthropic 官方文档 - Agent evals](https://docs.anthropic.com/en/docs/build-with-claude/agent-evals)
- [Anthropic 官方文档 - Models](https://docs.anthropic.com/en/docs/about-claude/models)
- [Model Context Protocol 规范](https://modelcontextprotocol.io/)
