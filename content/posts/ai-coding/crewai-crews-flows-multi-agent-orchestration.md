---
title: "CrewAI：Crews × Flows 双层抽象把 Multi-Agent 从「能跑」推到「能生产」"
slug: crewai-crews-flows-multi-agent-orchestration
date: 2026-09-02T19:10:00+08:00
draft: true
tags: ["CrewAI", "Multi-Agent", "Crews", "Flows", "Python", "Pydantic", "A2A", "MCP", "Open Source", "Agent Orchestration"]
categories: ["技术笔记"]
description: "深度解读 github.com/crewAIInc/crewAI：10 万认证开发者的 Multi-Agent 编排框架，靠 Crews（自治协作）+ Flows（事件驱动）把 Agent 从 demo 推到生产。四层抽象 LLM/Agent/Crew/Flow，Python ≥ 3.10 < 3.14，Flow 引擎三模块拆分，execution_uuid contextvars 透传，SQLite 可插拔持久化，7 个构造期校验器。"
github_repo: crewAIInc/crewAI
source_key: gh:crewAIInc/crewAI
author: 钳岳
---

# CrewAI：Crews × Flows 双层抽象把 Multi-Agent 从「能跑」推到「能生产」

> 来源：GitHub 仓库 `github.com/crewAIInc/crewAI`（MIT 协议，截至 2026-09-02 抓取 main 分支，v1.15.x，约 58k stars）。
>
> 本文基于 `README.md`、`AGENTS.md`、`lib/crewai/pyproject.toml` 与 `lib/crewai/src/crewai/` 下的关键源码（`crew.py`、`agent/core.py`、`process.py`、`execution.py`、`flow/` 全目录、`a2a/`、`skills/`）交叉核对写成。引用以章节名和函数名定位，不带行号——行号随版本漂移，章节和函数名更能活过一个 release。

## 从一个问题开始：自治和控制在哪一层分家

每个 Multi-Agent 框架都要回答同一个问题：agent 的自主推理，和业务流程的确定控制，放在同一层还是分成两层？

LangGraph 的回答是全放一层——给你一张图，节点可以是任何东西，分工由你自己画。AutoGen 的回答是对话层——agent 就是对话参与者，控制靠对话规则。CrewAI 的回答最直接：**分成两层，Crews 管自治，Flows 管控制，分工写进架构而不是写进你的代码**。

这个分家不是营销话术，README 的 "Understanding Flows and Crews" 章节把它写成了定义：

> "1. **Crews**: Teams of AI agents with true autonomy and agency, working together to accomplish complex tasks through role-based collaboration.
> 2. **Flows**: Production-ready, event-driven workflows that deliver precise control over complex automations. Flows provide: fine-grained control over execution paths for real-world scenarios; secure, consistent state management between tasks; clean integration of AI agents with production Python code; conditional branching for complex business logic."

配合项目方自述的 10 万认证开发者（通过 learn.crewai.com 社区课程认证）、MIT 协议和 MCP / A2A 双协议支持，CrewAI 是 2026 年还在积极演进的少数 Python 原生编排框架之一。

但框架的定位说明不了什么，源码才说明。这篇文章做的事：从 README 的承诺出发，逐条下到源码验证——双层抽象怎么落的、一次 kickoff 走过哪些函数、Flow 引擎怎么拆模块、持久化怎么做到可插拔。中间会指出一处 README 官方示例里真实存在的状态断链问题。

先给一张系统地图。CrewAI 实际上不是两层，是四层：

```text
┌────────────────────────────────────────────────────┐
│ Flow（事件驱动骨架）                                │
│   @start / @listen / @router / @human_feedback     │
│   Pydantic 状态托管 + checkpoint / 持久化           │
│                                                    │
│   ┌────────────────────────────────────────────┐   │
│   │ Crew（自治协作单元）                        │   │
│   │   Process.sequential / hierarchical        │   │
│   │   Task 序列 + context 依赖 + 结构化输出     │   │
│   │                                            │   │
│   │   ┌──────────────────────────────────┐     │   │
│   │   │ Agent（角色化执行者）             │     │   │
│   │   │   role / goal / backstory        │     │   │
│   │   │   tools / guardrail / planning   │     │   │
│   │   │                                  │     │   │
│   │   │   ┌────────────────────────┐     │     │   │
│   │   │   │ LLM（模型适配层）       │     │     │   │
│   │   │   │   openai/gpt-4o        │     │     │   │
│   │   │   │   anthropic/...        │     │     │   │
│   │   │   └────────────────────────┘     │     │   │
│   │   └──────────────────────────────────┘     │   │
│   └────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────┘
```

README 的 getting-started skill 把这个选择写成了一条决策路径：不需要角色就调 `LLM.call()`；单个角色带工具用 `Agent`；多角色协作组装 `Crew`；要业务控制流就用 `Flow` 把 Crew 包进去。每层都可以单独使用——`Agent` 有自己的 `kickoff()` 和 `message()`，不套 Crew 也能跑，这是很多人不知道的一点，后文细说。

---

## 1 · Crews：一个自治 Agent 团队

Crews 是 CrewAI 的智能层。源码位置：`lib/crewai/src/crewai/crew.py`（Crew 主类，约 2500 行）和 `lib/crewai/src/crewai/agent/core.py`（Agent 主类，约 2100 行）。这两个文件撑起了整个自治层的机制。

### 1.1 三种 Process

`lib/crewai/src/crewai/process.py` 不到二十行，定义了 Crew 的全部调度范式：

```python
class Process(str, Enum):
    """Class representing the different processes that can be used to tackle tasks"""

    sequential = "sequential"
    hierarchical = "hierarchical"
    # TODO: consensual = 'consensual'
```

| 模式 | 调度方式 | 适用场景 |
|---|---|---|
| `sequential` | 按任务列表顺序串行执行（默认值） | 流程化工作，先研究后写报告 |
| `hierarchical` | 自动创建 manager agent 做委派和校验 | 多任务、需要质控的场景 |
| `consensual` | 源码中仅存 TODO 注释，未实现 | — |

README 的快速上手和示例 crews（Trip Planner / Stock Analysis 等）默认演示的就是 sequential——它是框架默认值，也是最常走的路径。

hierarchical 是进阶选项，而且有一条硬约束藏在 Pydantic 校验器里（`check_manager_llm`）：使用 hierarchical 时必须提供 `manager_llm` 或 `manager_agent`，两者都没有会直接抛 `missing_manager_llm_or_manager_agent` 异常，Crew 根本构造不出来。另外两条容易踩的规则：manager agent 不能放进 `agents` 列表（`manager_agent_in_agents` 校验）；`_create_manager_agent` 会给 manager 配上 `AgentTools`（委派工具），如果你传入的自定义 manager 带了工具，源码直接记 warning 并抛异常——"Manager agent should not have tools"，委派就是 manager 唯一该干的事。

consensual 留 TODO 是有意还是遗忘，源码看不出答案。可以确认的是：多 agent 平等协商的机制在 CrewAI 里始终没有落地，团队把「质控」这条路全部押给了 manager 委派范式。

### 1.2 Agent：五要素只是入口

README 教你用五个字段构造 Agent：

| 要素 | 字段 | 作用 |
|---|---|---|
| 角色 | `role` | 系统提示里的人设锚 |
| 目标 | `goal` | 这个 agent 被设计来解决什么问题 |
| 背景故事 | `backstory` | 给 LLM 喂的"经验/性格"长文 |
| 工具 | `tools` | 可调用的 `BaseTool` 列表 |
| 模型 | `llm` | 字符串标识或 `BaseLLM` 实例 |

`llm` 传字符串即可（如 `"openai/gpt-4o"`），构造时 `create_llm()` 负责解析成实例。这五要素是心智模型的入口，不是能力边界——`agent/core.py` 里的 `Agent` 还有大量生产字段：`guardrail`（输出校验，失败自动重试 `guardrail_max_retries` 次）、`planning`（任务前先规划）、`skills`（加载 SKILL.md 指令包）、`a2a`（委派给远程 agent）、`mcps`（挂 MCP 服务器）、`memory`、`max_execution_time`、`respect_context_window`。

两个容易被忽略的执行入口：

- `Agent.kickoff(messages, response_format=...)`：脱离 Crew 直接执行，返回 `LiteAgentOutput`，支持结构化输出和文件输入。它还会自动检测当前是否在 event loop 里，是的话返回协程让上层 await——单 agent 场景不用包一层 Crew 仪式。
- `Agent.message(content)`：一条消息进去一段话出来，内部临时组装一个单任务 Crew 跑完即弃。

还有一个迁移信号值得注意：`executor_class` 字段的默认值已经从 `CrewAgentExecutor` 切到 `crewai.experimental.AgentExecutor`，前者构造时直接发 `DeprecationWarning`。老代码如果显式指定过 executor，升级时会收到警告。

### 1.3 Task：线性序列加前向依赖

一个常见的误读是把 Crew 的任务结构说成 DAG。源码里任务是**有序列表**，执行顺序就是列表顺序；`context` 字段允许一个任务引用更早任务的输出，`validate_context_no_future_tasks` 校验器会拒绝引用「未来的任务」。这构成的是带前向依赖的线性流水线，加上 `async_execution=True` 的并发窗口，不是任意拓扑的图。任意拓扑恰恰是 Flow 层的职责——这个边界在 CrewAI 里是刻意的。

结构化输出是 Crews 往生产走的关键一步：

- `output_pydantic`：任务输出强制转 Pydantic 模型
- `output_json`：输出强制为 JSON
- `output_file`：结果写到指定路径（如 `output/report.md`）
- `markdown: true`：声明输出是 markdown，避免整段被代码围栏包住

有了这些约束，agent 的输出可以直接被下游 Python 代码消费，不用再写「从 LLM 文本里抠 JSON」的胶水代码。

### 1.4 构造期校验器：一份免费的排查清单

`crew.py` 里挂了一排 Pydantic 校验器，Crew 构造时就把错误拦在 kickoff 之前。与其等运行时报错，不如把校验器当配置清单用：

| 校验器 | 拦截的错误 |
|---|---|
| `check_manager_llm` | hierarchical 缺 `manager_llm` / `manager_agent` |
| `validate_tasks` | sequential 模式下任务缺 `agent` |
| `validate_first_task` | 首个任务是 `ConditionalTask` |
| `validate_must_have_non_conditional_task` | 全部任务都是条件任务 |
| `validate_end_with_at_most_one_async_task` | 结尾挂了超过一个连续异步任务 |
| `validate_async_tasks_not_async` | `ConditionalTask` 与异步执行混用 |
| `validate_context_no_future_tasks` | `context` 引用了列表中更靠后的任务 |

这些校验信息都足够具体（错误消息里带任务描述），遇到报错对着这张表改配置即可，不需要翻源码。

### 1.5 三分钟最小可跑示例

下面这段代码只依赖 `crewai` 包（`openai` SDK 是它的硬依赖，无需单独安装），配好 `OPENAI_API_KEY` 就能跑：

```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(
    role="{topic} Senior Researcher",
    goal="Uncover cutting-edge developments in {topic}",
    backstory="You're a seasoned researcher who finds relevant info clearly.",
    llm="openai/gpt-4o-mini",  # 可换 anthropic/claude-* 等，需装对应 extra
)

writer = Agent(
    role="{topic} Report Writer",
    goal="Compose a tight 3-bullet briefing on {topic}",
    backstory="You turn scattered findings into crisp prose.",
    llm="openai/gpt-4o-mini",
)

research_task = Task(
    description="Find 5 recent breakthroughs in {topic}.",
    expected_output="A bullet list with 5 concise items.",
    agent=researcher,
)

write_task = Task(
    description="Synthesize the 5 items into a 3-bullet executive briefing.",
    expected_output="3 bullets, each <= 25 words.",
    agent=writer,
    context=[research_task],
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,
)

print(crew.kickoff(inputs={"topic": "CrewAI multi-agent framework"}))
```

```bash
uv tool install crewai
uv run --with crewai python main.py
```

`write_task` 的 `context=[research_task]` 是这个例子里最值得注意的一行——没有它，writer 拿不到 researcher 的产出，两个任务就成了各说各话。这个示例不依赖 MCP、持久化和任何外部工具，纯 LLM 调用。想判断 CrewAI 是否值得引入，跑通它是最快的路径。

---

## 2 · 一次 kickoff 的生命周期

架构文章最容易停在「模块框图」。这里换一个视角：一次 `crew.kickoff()` 调用，从进入到返回，源码里实际走过哪些节点。这条路径全部来自 `crew.py` 的 `kickoff()` 方法及其调用的函数。

```text
crew.kickoff(inputs)
  │
  ├─ apply_checkpoint()        # 有 from_checkpoint 则恢复状态后转发
  ├─ get_env_context()         # 加载环境上下文
  ├─ baggage.set_baggage()     # OpenTelemetry baggage 绑定 CrewContext(id, key)
  ├─ begin_execution()         # mint 或继承 execution_uuid（见 §4）
  ├─ _enter_runtime_scope()    # 进入事件总线 runtime 作用域
  │
  ├─ prepare_kickoff()         # 扫描 {placeholder}，把 inputs 插值进任务与 agent 文本
  │
  ├─ _run_sequential_process() # 或 _run_hierarchical_process()
  │    └─ _execute_tasks()
  │         ├─ 逐任务：_get_context() 聚合 context 任务的输出
  │         ├─ async 任务提交 Future 挂起，遇到同步任务前统一收编
  │         └─ _process_task_result() / _store_execution_log() 记录
  │
  ├─ _create_crew_output()     # 取最后有效输出，算 token 用量
  │    ├─ OUTPUT / EXECUTION_END hook 分发（可被 hook 改写 payload）
  │    ├─ _drain_memory_writes()  # 排空后台记忆写入
  │    └─ emit CrewKickoffCompletedEvent
  │
  └─ finally: end_execution() / detach baggage / 退出 runtime scope
```

四个值得记住的细节：

**占位符插值发生在 kickoff 时，不是构造时。** `fetch_inputs()` 用正则扫描任务描述、期望输出和 agent 三要素里的 `{xxx}`，凑成必填集合；缺的值由调用方补，CLI 场景就是 `crewai run` 的交互提示。所以改 prompt 里的占位符不需要动代码结构。

**异步任务有并发窗口，但收编点是同步任务。** `_execute_tasks` 遇到 `async_execution=True` 的任务就提交 Future 继续走，直到撞上第一个同步任务才 await 所有挂起的 Future。这就是「结尾最多一个连续异步任务」校验器存在的原因——结尾的异步任务没人收编。

**记忆写入是后台的，事件顺序决定正确性。** `_drain_memory_writes` 的 docstring 写得很直白：监听器（如遥测会话）在 `CrewKickoffCompletedEvent` 时拆解，如果记忆保存事件晚于这个事件发出，保存 span 就成了孤儿。所以排空动作必须卡在完成事件之前。

**hook 是输出管线的正式环节。** `OUTPUT` 和 `EXECUTION_END` 两个拦截点的 dispatch 结果会写回 `CrewOutput`，也就是说 hook 可以改写最终返回值——这是做审计、脱敏或后处理的官方通道，不用包一层函数。

看懂这条路径，后面两节的三层机制（execution_uuid、持久化、事件）就都有了挂靠点。

---

## 3 · Flows：事件驱动的控制层

Crews 回答「做什么」，Flows 回答「什么时候做、做完去哪里」。

### 3.1 模块拆分：门面、协议、引擎

`flow/flow.py` 本体只有 1.3KB——它已经退化成一个兼容旧导入路径的 re-export 门面。真正的实现按职责拆了出去，docstring 列出的拆分是：

| 模块 | 职责 | 何时改它 |
|---|---|---|
| `crewai.flow.dsl` | Python 装饰器与条件组合器（作者层） | 写 Flow 时打交道的就是它 |
| `crewai.flow.flow_definition` | 可序列化的 Flow Definition 契约（协议层） | 改序列化模型时 |
| `crewai.flow.runtime` | 执行引擎与状态（引擎层） | 改调度、状态机时 |
| `crewai.flow.conversational_mixin` | 对话式运行时扩展，mixin 方式叠加 | 扩展对话能力时 |

目录下还有四个子包没有出现在 docstring 的核心拆分里：`persistence`（持久化）、`visualization`（Flow 画图）、`templates`、`async_feedback`。公开的 `Flow` 类是空类体，靠 `_ConversationalMixin + RuntimeFlow[T]` 双继承组合出来，泛型参数 `T` 约束为 `dict[str, Any] | BaseModel`——Flow 状态既可以是裸字典也可以是 Pydantic 模型。

这种拆分的实际收益是变更隔离：写业务 Flow 的人只碰 `dsl`，改序列化协议不影响引擎，反过来也一样。和 Web 框架的「路由 → 协议 → 处理器」分层是同一个思路。

### 3.2 四个装饰器和两个组合器

`flow/dsl/__init__.py` 的 `__all__` 导出了六个名字：

| 名称 | 类型 | 作用 |
|---|---|---|
| `@start()` | 装饰器 | 标记方法为 Flow 入口 |
| `@listen(condition)` | 装饰器 | 标记方法为某条件的响应器 |
| `@router(condition)` | 装饰器 | 路由方法，返回字符串触发分支 |
| `@human_feedback` | 装饰器 | 在 Flow 步骤中引入人工反馈 |
| `or_(...)` | 组合器 | 任一条件满足即触发 |
| `and_(...)` | 组合器 | 全部条件满足才触发 |

外加一个 `HumanFeedbackResult` 结果类型。四个装饰器在 `_start.py`、`_listen.py`、`_router.py`、`_human_feedback.py` 各自实现，共同套路是把函数包成带元数据的 wrapper，再合并进不可变的 `FlowMethodDefinition`——作者层写的是 Python 方法，落盘的是可序列化的 Flow 定义，真正的调度由 `runtime` 接手。

`@human_feedback` 值得单独一提：它是 Flow 层的 human-in-the-loop 官方方案，配合 `persistence` 的 pause/resume，流程可以停在等人确认的地方，重启后接着跑。README 的 "When to Use CrewAI" 里把 human review 列为适用场景，实现落点就在这个装饰器。

### 3.3 持久化：默认 SQLite，工厂可替换

Flow 状态由 Pydantic 模型托管，`class MarketState(BaseModel)` 就是 `self.state`。持久化走工厂模式，`flow/persistence/factory.py`：

```python
def set_flow_persistence_factory(factory: FlowPersistenceFactory | None) -> None:
    """Replace the process-wide default flow persistence factory.

    Intended for one-time setup at startup. Pass ``None`` to restore the
    built-in ``SQLiteFlowPersistence``. ...
    """
    global _factory
    _factory = factory


def default_flow_persistence() -> FlowPersistence:
    """Build the default flow persistence backend."""
    factory = _factory
    if factory is not None:
        return factory()
    from crewai.flow.persistence.sqlite import SQLiteFlowPersistence
    return SQLiteFlowPersistence()
```

docstring 里藏了三条使用规则，比「可插拔」三个字有用得多：

1. **显式传入的 `persistence=` 实例永远优先**，工厂只影响走默认回退的 Flow（`@persist` 装饰器和 runtime 的 pause/resume 路径）。
2. **工厂可能被调用多次**——每处回退点都会各自解析一次默认值，所以工厂返回的实例必须背靠共享的持久状态（或做成单例），否则这一次保存的数据下一次读不到。
3. **设计给启动时一次性调用**，不是运行时热切换开关。

默认后端是 SQLite 单文件。换成远程数据库、内存 fake（测试用）或 Redis，都是在应用启动时注册一个工厂函数的事。

Crew 侧的持久化近年也补齐了：`Crew` 有 `checkpoint` 配置字段，`Crew.from_checkpoint(config)` 从检查点恢复实例，`Crew.fork(config, branch)` 还能从检查点分叉出新执行分支。「普通 Python 函数没有 checkpoint」这句话今天要打个补丁——Crew 和 Flow 都有了，恢复粒度和 API 不同而已。

---

## 4 · Crew + Flow 联合实战：官方示例里的一条暗坑

README 的 "Using Crews and Flows Together" 章节给了 AdvancedAnalysisFlow，这是联合范式的标准范本，代码如下（忠实转述）：

```python
from crewai.flow.flow import Flow, listen, start, router, or_
from crewai import Crew, Agent, Task, Process
from pydantic import BaseModel


class MarketState(BaseModel):
    sentiment: str = "neutral"
    confidence: float = 0.0
    recommendations: list = []


class AdvancedAnalysisFlow(Flow[MarketState]):

    @start()
    def fetch_market_data(self):
        self.state.sentiment = "analyzing"
        return {"sector": "tech", "timeframe": "1W"}

    @listen(fetch_market_data)
    def analyze_with_crew(self, market_data):
        analyst = Agent(
            role="Senior Market Analyst",
            goal="Conduct deep market analysis with expert insight",
            backstory="You're a veteran analyst known for identifying subtle market patterns",
        )
        researcher = Agent(
            role="Data Researcher",
            goal="Gather and validate supporting market data",
            backstory="You excel at finding and correlating multiple data sources",
        )
        analysis_task = Task(
            description="Analyze {sector} sector data for the past {timeframe}",
            expected_output="Detailed market analysis with confidence score",
            agent=analyst,
        )
        research_task = Task(
            description="Find supporting data to validate the analysis",
            expected_output="Corroborating evidence and potential contradictions",
            agent=researcher,
        )
        crew = Crew(
            agents=[analyst, researcher],
            tasks=[analysis_task, research_task],
            process=Process.sequential,
            verbose=True,
        )
        return crew.kickoff(inputs=market_data)

    @router(analyze_with_crew)
    def determine_next_steps(self):
        if self.state.confidence > 0.8:
            return "high_confidence"
        elif self.state.confidence > 0.5:
            return "medium_confidence"
        return "low_confidence"

    @listen("high_confidence")
    def execute_strategy(self):
        ...

    @listen(or_("medium_confidence", "low_confidence"))
    def request_additional_analysis(self):
        self.state.recommendations.append("Gather more data")
        return "Additional analysis required"
```

这个例子演示了 Flow 的标准动作：`@start` 入口、`@listen(method)` 响应、`@router` 按状态分支、`or_()` 多路合流、Crew 作为 Flow 的一个步骤。照着学范式没问题，但**直接照抄进生产会踩一个坑**。

看 `determine_next_steps`：它读 `self.state.confidence` 来决定走哪条分支。而全流程里没有任何一行代码把 Crew 的分析结果写回 `self.state.confidence`——`analyze_with_crew` 把 `crew.kickoff()` 的返回值直接 return 了，state 里的 `confidence` 从初始化到路由永远是 `0.0`。结论：这个示例跑起来后 router 永远命中 `low_confidence` 分支，`execute_strategy` 是死代码。

修法是把 Crew 输出接进 state。最稳的接法不走文本解析，用 `output_pydantic` 让第一个任务直接产出结构化结果（呼应 §1.3 的结构化输出）：

```python
from pydantic import BaseModel


class AnalysisResult(BaseModel):
    confidence: float
    summary: str


analysis_task = Task(
    description="Analyze {sector} sector data for the past {timeframe}",
    expected_output="Detailed market analysis with confidence score",
    output_pydantic=AnalysisResult,
    agent=analyst,
)
```

然后在 `analyze_with_crew` 里补上状态写回：

```python
result = crew.kickoff(inputs=market_data)
analysis = result.tasks_output[0].pydantic
if analysis is not None:
    self.state.confidence = analysis.confidence
return result
```

`result.tasks_output[0].pydantic` 取的就是 `output_pydantic` 强制转换后的模型实例，置信度是类型安全的 float，router 读到的是真值。

同一个例子里还有第二处松散：`research_task` 的职责是「验证分析」，但它没有声明 `context=[analysis_task]`，于是两个任务串行跑完、各说各话，验证者根本看不到待验证的分析。补上这一行，任务间的依赖才成立。

这两处不影响示例的教学价值——它本来就不是生产代码——但值得写明白：**Flow 的 router 只看 state，Crew 的返回值不会自动进 state**。两个层的接缝要自己焊，焊点就是那行 `self.state.xxx = ...`。理解了这一点，这个示例反而比官方文档更能说明 Crews 和 Flows 各自的边界。

---

## 5 · execution_uuid：一次执行的身份证

分布式追踪的第一问题是「这一堆日志哪些属于同一次执行」。CrewAI 的答案是一个 contextvar，`lib/crewai/src/crewai/execution.py`：

```python
_current_execution_uuid: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "crewai_execution_uuid", default=None
)

def begin_execution(execution_uuid: str | None = None):
    if _current_execution_uuid.get() is not None:
        return None
    return set_execution_uuid(execution_uuid or str(uuid4()))

def end_execution(token):
    if token is not None:
        clear_execution_uuid(token)
```

三条设计规则，全部写在函数 docstring 里：

- **最外层 mint，嵌套继承。** 最外层的 crew 或 flow 默认拿到新的 `uuid4()`；嵌套 kickoff（flow 里的 crew、子 flow）发现已有 uuid 就返回 `None` 不新建，`end_execution(None)` 也不做重置。重置 token 只归最外层所有，防止内层误清外层上下文。
- **宿主可以预置自己的 id。** `set_execution_uuid()` 的 docstring 明说用途："Use this from enterprise / hosts that already own the run id (e.g. Celery kickoff_id)"。商业控制面（CrewAI AMP）有自己的一次执行编号，提前 stamp 进 contextvar，两边就能用同一个 id 关联执行记录——这是 OSS 和商业面之间干净的耦合点，不绑死任何内部实现。
- **uuid 在 kickoff 调用路径上绑定，不走事件总线。** 从 §2 的生命周期图能看到，`begin_execution()` 在进入 runtime scope 的同一段同步代码里调用。为什么不在事件回调里绑？事件分发天然是异步的，监听器跑在什么线程、什么时机并不可控；而 `Agent._execute_with_timeout` 里 `contextvars.copy_context()` 的用法也说明，contextvars 跨线程要显式复制。把「执行身份」的绑定放在确定性最强的调用路径上，是这类追踪系统的常见选择。

对使用者的含义很简单：自己写监听器或日志时，取 `_current_execution_uuid.get()` 就能拿到当前执行的身份；不需要手动传递，也不需要担心嵌套 Crew 串号。

---

## 6 · AGENTS.md 里的一条硬规矩

仓库根目录的 `AGENTS.md` 是写给贡献者（和 AI 编码 agent）的指南，其中 "Message Content" 章节有一条值得所有 Agent 框架开发者阅读的规矩：

> "`LLMMessage.content` is `str | list[dict[str, Any]] | None`; the list form is multimodal content parts. Never `str()` it — that puts a Python repr (`[{'type': 'text', 'text': 'hi'}]`) in front of the model and into memory. Collapse a message to text with the helper instead:
>
> ```python
> from crewai.utilities.agent_utils import message_content_text
>
> text = message_content_text(msg)  # "" for None; joined text for a parts list
> ```"

背景是多模态普及之后，消息的 `content` 不再保证是字符串，可能是 `[{"type": "text", "text": "..."}, {"type": "image", ...}]` 这样的 parts 列表。此时直接 `str(msg)` 会把 Python 字面量送进 prompt——模型看到的不是「hi」，而是 `[{'type': 'text', 'text': 'hi'}]` 这串 repr。这对人类是乱码，对模型是噪声，还会被存进记忆持续污染后续轮次。

`message_content_text()` 的折叠规则：`None` 返回空串，字符串原样返回，列表则把各 part 的文本拼接。源码里 `_content_parts_text` 还做了一层容错——parts 来自模型、类型是 `dict[str, Any]`，`text` 键的值不保证是字符串，遇到就跳过而不是抛异常；整列表没有可用文本时返回 `"[multimodal content]"` 占位。

这条规矩的普适性大于 CrewAI 本身：任何在 prompt 组装层处理消息的代码都要回答「多模态 parts 怎么折叠」这个问题。CrewAI 的做法是在贡献指南里给它单独设章，让所有贡献者和 AI 编码 agent 在改代码前就看见。

---

## 7 · JSON-first vs Python-classic：两条路径都留着

`crewai create crew` 生成的默认脚手架已经是 JSON-first 形态：

```text
my_project/
├── .gitignore
├── .env
├── agents/
│   └── researcher.jsonc      # 每个 agent 的角色定义
├── crew.jsonc                # 任务、流程、输入默认值
├── knowledge/                # 可选：知识文件
├── pyproject.toml
├── README.md
├── skills/                   # 可选：技能文件
└── tools/                    # 自定义工具，以 "custom:" 引用
```

`agents/researcher.jsonc`：

```jsonc
{
  "role": "{topic} Senior Data Researcher",
  "goal": "Uncover cutting-edge developments in {topic}",
  "backstory": "You're a seasoned researcher who finds relevant information and presents it clearly.",
  "llm": "openai/gpt-4o",
  "tools": ["SerperDevTool"],
  "settings": { "verbose": true }
}
```

`crew.jsonc` 把任务依赖和输入默认值也收进了配置：

```jsonc
{
  "name": "Latest AI Development",
  "agents": ["researcher", "reporting_analyst"],
  "tasks": [
    {
      "name": "research_task",
      "description": "Conduct thorough research about {topic}.",
      "expected_output": "A list with 10 bullet points.",
      "agent": "researcher"
    },
    {
      "name": "reporting_task",
      "description": "Review the research and expand each topic into a report.",
      "expected_output": "A markdown report.",
      "agent": "reporting_analyst",
      "context": ["research_task"],
      "output_file": "output/report.md",
      "markdown": true
    }
  ],
  "process": "sequential",
  "inputs": { "topic": "AI Agents" }
}
```

运行方式：`.env` 里配好密钥，`crewai install` 装依赖，`crewai run` 执行。`{topic}` 这类占位符在 `crew.jsonc` 的 `inputs` 里给默认值，缺省的值 CLI 会交互式询问。

老路径没有被删除：`crewai create crew --classic` 仍然生成 `crew.py` + `config/agents.yaml` + `config/tasks.yaml` 的 Python-classic 结构。两条路径各有适用面——JSON-first 让 prompt 迭代不进代码 review，改配置文件就是改业务；Python-classic 承接继承 `Agent`、动态生成任务这类 JSON 表达不了的逻辑。混合使用也成立：静态 agent 写 JSON，动态 hook 写 Python。

`AGENTS.md` 的 "Key Guidelines" 第 7 条从贡献侧呼应了这个分层："Keep diffs as minimal as possible"。配置层和代码层分开演进，diff 才能小得起来。

---

## 8 · 两个 Skills 和两个协议

"CrewAI 支持 Skills" 这句话在 2026 年有两个完全不同的所指，源码里是两套东西，分开说。

### 8.1 面向开发者的 coding-agent Skills

README 的 "Build with AI" 章节推广的是 `crewAIInc/skills` 仓库——一套装进 AI 编码工具的提示包，教会 Claude Code、Cursor、Codex、Windsurf 怎么写 CrewAI 代码：

```shell
# Claude Code
/plugin marketplace add crewAIInc/skills
/plugin install crewai-skills@crewai-plugins
/reload-plugins

# Cursor / Codex / Windsurf 等（via skills.sh）
npx skills add crewaiinc/skills
```

四个 skill 各管一段：`getting-started`（脚手架与 LLM/Agent/Crew/Flow 选型）、`design-agent`（配置角色/目标/工具/模型）、`design-task`（任务描述/依赖/结构化输出）、`ask-docs`（查询官方文档 MCP server）。

### 8.2 面向运行时 agent 的 Skill 系统

`lib/crewai/src/crewai/skills/` 是另一回事：框架内部的指令加载机制。`Agent` 和 `Crew` 都有 `skills` 字段，接受路径、SKILL.md 内联字符串或注册表引用；`load_skills()` 负责加载，`LoadSkillTool` 作为工具暴露给模型按需取用，每个 skill 还有 disclosure level 控制指令是常驻 prompt 还是按需加载。

一句话区分：**coding-agent Skills 给「写 CrewAI 代码的人」用，运行时 Skill 系统给「跑起来的 agent」用**。两者共享 SKILL.md 这个文件格式生态，但服务对象不同，别在文档里混用。

### 8.3 A2A 与 MCP：两个协议各管一段

`lib/crewai/src/crewai/a2a/` 实现了 A2A 协议（Google 主导发布的跨 agent 通信协议），四个子包 `auth` / `extensions` / `updates` / `utils`，加上 `config.py` 和体量最大的 `wrapper.py`（约 63KB）。`Agent` 上的 `a2a` 字段接受 `A2AConfig` / `A2AClientConfig` / `A2AServerConfig`，可以把任务委派给远程 agent。

MCP 客户端在 `lib/crewai/src/crewai/mcp/`，`Agent.mcps` 字段挂服务器引用，`MCPToolResolver` 把远端工具解析成本地 `BaseTool`。

两个协议的分工已经形成行业共识：MCP 连接 agent 与工具/数据源，A2A 连接 agent 与 agent（跨进程、跨语言、跨厂商）。CrewAI 两个都实现了——在编排层保持中立，是它区别于厂商绑定框架（Claude Agent SDK 之于 Anthropic、Google ADK 之于 Gemini）的商业策略基础。也要看到中立的具体含义：框架代码不绑定厂商，但默认 `openai` SDK 是硬依赖（下一节展开）。

---

## 9 · 依赖清单里的工程信号

`lib/crewai/pyproject.toml` 能读出比功能列表更细的东西：

- **Python `>=3.10, <3.14`**，与 README 一致。
- **`openai>=2.30.0,<3` 是硬依赖**，`instructor` 随行做结构化输出。「支持所有模型」的准确含义是：OpenAI 兼容端点开箱即用（包括 Ollama 的 `/v1` 兼容层），其他厂商走可选 extras——`litellm`（网关，100+ provider）、`anthropic`、`google-genai`、`bedrock`、`azure-ai-inference`、`watson`（IBM watsonx.ai）、`voyageai`。
- **向量库双后端**：`chromadb` 与 `lancedb` 同时在依赖里，knowledge/RAG 能力有两条落地路径。
- **`mem0ai`** 出现在可选依赖，记忆能力接了第三方记忆框架。
- **`json-repair`** 在列——专门修 LLM 输出的坏 JSON。把这类容错放进核心依赖而不是示例代码，说明结构化输出走的是「先修复再解析」的路线。
- **`cel-python`**（Google CEL 表达式语言的 Python 实现）同样在核心依赖列表里。
- **OpenTelemetry 全家桶**（api / sdk / otlp-exporter）是硬依赖，tracing 不是外挂而是底座；`Crew.tracing` 字段和 `crewai traces enable` CLI 提供开关。
- **`uv` 配置里 `exclude-newer = "3 days"`**：依赖解析只考虑三天前的版本，牺牲三天的新鲜度换构建可复现。
- 一个维护细节：torch 因与 Python 3.13 不兼容，通过 `[tool.uv.sources]` 按解释器版本切换 CPU 轮子索引。

这些条目单看都小，合起来是一个信号：这个框架把「生产环境会遇到的脏问题」（坏 JSON、不可复现构建、版本漂移）当成了工程主线而不是边缘 case。

---

## 10 · 何时用，何时别用，从哪开始

README 的 "When to Use CrewAI" 章节给了官方判断：

> "Use CrewAI when you need more than a single prompt or chatbot: multi-step work, specialized agents, tool use, structured outputs, human review, or workflows that combine autonomous reasoning with explicit business logic."

翻译成负面清单更实用。

**适合**：

- 多步骤、多角色的协作流程（研究 → 写作 → 审稿）
- 输出要直接进下游代码（Pydantic / JSON / 文件）
- 业务控制流和 agent 自治需要分层管理（Flow 包 Crew）
- 需要 checkpoint、恢复、人工审核这类长流程要素

**不适合**：

- 单轮 prompt 进单输出——直接调 LLM SDK 更快
- 极致低延迟——agent 间协作意味着多次 LLM 往返
- 需要编译期类型保证的团队——Python 动态类型加 JSON 配置都是软约束，契约靠 Pydantic 校验和 §1.4 那张校验器表兜底

**如果决定采用，建议按这个顺序推进**：

1. 用 `Agent.kickoff()` 跑通单个 agent 加工具的场景，确认模型和 key 链路
2. 需要多角色时组装 sequential Crew，用 `context` 建立任务依赖，用 `output_pydantic` 锁输出结构
3. 需要质控再上 hierarchical，记得给 `manager_llm`
4. 业务分支复杂到任务列表表达不了时，引入 Flow 包住 Crew，状态写回的焊点（§4）亲手写一次
5. 上长流程前接 `checkpoint` 和持久化工厂，先在启动时注册好测试用 in-memory 后端

出问题时先查三处：§1.4 的构造期校验器表（配置错误多数在这里被拦下）、`tracing` 开关（`crewai traces enable` 或环境变量 `CREWAI_TRACING_ENABLED=true`）、以及 `execution_uuid` 对应的日志聚合。

---

## 11 · 心智地图

最后把全文收进一张模块树，按「想改什么 → 看哪里」的顺序组织：

```text
lib/crewai/src/crewai/          (Python >= 3.10, < 3.14)
├── crew.py                     # Crew 主类：校验器、kickoff、checkpoint/fork
├── agent/
│   └── core.py                 # Agent 主类：prompt 构建、执行器、独立 kickoff
├── tasks/                      # conditional_task / guardrail / output_format
├── process.py                  # sequential / hierarchical（consensual 仅 TODO）
├── flow/
│   ├── dsl/                    # @start @listen @router @human_feedback + or_/and_
│   ├── flow_definition.py      # 可序列化 Flow 定义契约
│   ├── runtime/                # 执行引擎与状态机
│   └── persistence/            # SQLite 默认 + 可插拔工厂
├── llms/                       # 模型适配：openai 内置，其余走 extras
├── memory/                     # 统一 Memory + MemoryScope/MemorySlice 视图
├── knowledge/                  # RAG：chromadb / lancedb 双后端
├── tools/                      # BaseTool 生态与 agent 委派工具
├── mcp/                        # MCP 客户端（agent ↔ 工具/数据）
├── a2a/                        # A2A 协议实现（agent ↔ agent）
├── skills/                     # 运行时 Skill 加载（SKILL.md、disclosure level）
├── execution.py                # execution_uuid contextvars
├── security/                   # fingerprint / security config
└── events/                     # 事件总线 + OpenTelemetry tracing
```

| 想做的事 | 看哪里 |
|---|---|
| 改 agent 行为 | `agent/core.py` |
| 改调度方式 | `crew.py` + `process.py` |
| 改 Flow 装饰器 | `flow/dsl/` |
| 换持久化后端 | `flow/persistence/factory.py` |
| 接新模型 | `llms/`（继承 `BaseLLM`）或直接用 extras |
| 查一次执行的日志 | `execution.py` 的 uuid + `events/` |

---

## 结语：把分工刻进架构的赌注

回到开头的问题：自治和控制在哪一层分家。CrewAI 的答案是刻意的分层——Crews 持有「怎么推理、用什么工具、写什么内容」，Flows 持有「做不做、按什么顺序、状态怎么落」，接缝处只有一件事要做：把 Crew 结果写回 state。

源码层面对应三个具体押注。其一，四层 API（LLM / Agent / Crew / Flow）每层可独立使用，从单 agent 到长流程平滑加码。其二，JSON-first 脚手架把配置和代码分开，prompt 迭代不进 code review，Python-classic 老路径保留兜底。其三，协议上 MCP、A2A 双向支持，模型适配层默认 OpenAI 兼容、其余走 extras——中立是商业策略，也是工程选择。

和竞品对比时值得记住的差异点：LangGraph 的图灵完备换来的是自己画分工；AutoGen 的对话范式换来的是控制逻辑散在对话规则里；CrewAI 用「替你画好分工」换来的，是示例代码里那行必须自己焊的 `self.state.confidence = ...`——边界清楚了，接缝也就显形了。

10 万认证开发者的数字是市场对这套取舍的投票之一。至于这套分工是否经得起更复杂的场景检验，checkpoint / fork、持久化工厂、事件总线的演进方向已经给出了团队自己的答案。

---

> **参考链接**：
> - GitHub 仓库：<https://github.com/crewAIInc/crewAI>
> - 官方文档：<https://docs.crewai.com>
> - 学习课程：<https://learn.crewai.com>
> - Examples：<https://github.com/crewAIInc/crewAI-examples>
> - 企业版 AMP：<https://crewai.com/amp>
> - 社区：<https://community.crewai.com>
> - 博客：<https://blog.crewai.com>
>
> **本文基于**：`README.md`、`AGENTS.md`、`lib/crewai/pyproject.toml`、`lib/crewai/src/crewai/` 关键源码模块（crew / agent / process / execution / flow / a2a / skills），2026-09-02 抓取 main 分支（v1.15.x）。
>
> **作者**：钳岳
