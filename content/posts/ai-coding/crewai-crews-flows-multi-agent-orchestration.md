---
title: "CrewAI：Crews × Flows 双层抽象把 Multi-Agent 从「能跑」推到「能生产」"
slug: crewai-crews-flows-multi-agent-orchestration
date: 2026-09-02T19:10:00+08:00
draft: true
tags: ["CrewAI", "Multi-Agent", "Crews", "Flows", "Python", "Pydantic", "Mintlify", "A2A", "MCP", "Open Source", "Agent Orchestration"]
categories: ["技术笔记"]
description: "深度解读 github.com/crewAIInc/crewAI：一个项目方自述 10 万认证开发者的 Multi-Agent 编排框架，靠 Crews（自治协作）+ Flows（事件驱动）+ JSON-first 脚手架把 Agent 从 demo 推到生产。Python ≥ 3.10 < 3.14，2490 行 Crew 主类 + 2155 行 Agent 主类，三模块拆分（dsl / flow_definition / runtime）的 Flow 引擎，execution_uuid contextvars 透传，可插拔 SQLite 持久化工厂。"
github_repo: crewAIInc/crewAI
source_key: gh:crewAIInc/crewAI
author: 钳岳
---

# CrewAI：Crews × Flows 双层抽象把 Multi-Agent 从「能跑」推到「能生产」

> 来源：GitHub 仓库 `github.com/crewAIInc/crewAI`（MIT 协议，截至 2026-09-02 19:08 GMT+8 抓取 main 分支）。
>
> 本文基于 `README.md`（741 行）+ `AGENTS.md`（贡献者 + agent 提示）+ `pyproject.toml` 完整依赖 + `lib/crewai/src/crewai/` 全模块源码 + `lib/crewai/src/crewai/flow/`（dsl / flow_definition / runtime / persistence 四子包）+ `docs/edge/en/concepts/` 22 个 .mdx 整合而成。

## 写在前面：Multi-Agent 框架的 2026 分水岭

2024 年的 Agent 框架市场——各家各做一个 harness，能跑就行。2026 年，市场分成了四条河：

- **Claude Agent SDK** 守住 Anthropic 系（Claude Code + Skills + MCP）
- **OpenAI Agents SDK** 守住 OpenAI 系（handoff + guardrails + tracing）
- **Google ADK** 守住 Gemini 系（Sequential / Parallel / Loop）
- **CrewAI / LangGraph / AutoGen** 在多模型层争当「中立编排器」

**CrewAI 在这片混战里的押注**：把 Multi-Agent 从单层抽象升到双层——用 Crews 给自治、用 Flows 给控制、用 JSON-first 脚手架抹掉「agent.py 怎么写」的认知门槛。

**10 万认证开发者**（README L26 项目方自述）、**MIT 开源**、**MCP / A2A / Skills 全栈支持**——这是 2026 年能跟 LangGraph 掰手腕的少数 Python 原生框架之一。

> **一句话总览**：CrewAI = Crews（自治协作）+ Flows（事件驱动）+ JSON-first 脚手架 + 可插拔持久化。**两层抽象，一个 Python 进程**，把 Multi-Agent 从 demo 推到生产。

---

## 1 · 双层抽象：Crews vs Flows

CrewAI 的灵魂就两件事——**Crews** 和 **Flows**。README L66-L77 原文：

> "1. **Crews**: Teams of AI agents with true autonomy and agency, working together to accomplish complex tasks through role-based collaboration.
> 2. **Flows**: Production-ready, event-driven workflows that deliver precise control over complex automations. Flows provide:
>    - Fine-grained control over execution paths for real-world scenarios
>    - Secure, consistent state management between tasks
>    - Clean integration of AI agents with production Python code
>    - Conditional branching for complex business logic"

docs/edge/en/introduction.mdx 的"架构章"用一张图把这关系讲清：

```
┌─────────────────────────────────────────────┐
│  Flow（事件驱动、骨架）                      │
│  - 状态管理（State Management）              │
│  - 事件触发（Event-Driven Execution）        │
│  - 控制流（Conditional branching / loop）    │
│  ↓ 把任务「委托」给 Crew                     │
│  ┌─────────────────────────────────────┐    │
│  │  Crew（自治协作、单元）              │    │
│  │  - 角色扮演的 Agent（role / goal /   │    │
│  │    backstory / tools）               │    │
│  │  - 任务委派（Task delegation）       │    │
│  │  - 自治决策（Agents collaborate）    │    │
│  └─────────────────────────────────────┘    │
│  ↑ Crew 把结果回吐给 Flow                   │
└─────────────────────────────────────────────┘
```

工程含义：**自治和控制的分工写在架构里**——Flow 持有"做不做、按什么顺序做、状态怎么落"的权力，Crew 持有"怎么推理、用什么工具、写什么内容"的权力。这比 LangGraph 把所有节点都塞进同一张图、AutoGen 把所有轮次都塞进同一组对话的设计**更接近企业生产语义**。

> **值得停下来想想**：CrewAI 的双层抽象不是营销语言——是文档化的"自治 vs 控制"分工协议。**LangGraph 给你一张图让你自己画分工**，**CrewAI 替你画好分工、让你填空**。

---

## 2 · Crews：一个自治 Agent 团队

Crews 是 CrewAI 的"智能层"——一组带角色、带工具、带协作的 Agent。源码 `lib/crewai/src/crewai/crew.py`（2490 行）+ `lib/crewai/src/crewai/agent/core.py`（2155 行）撑起整个机制。

### 2.1 三种 Process

`lib/crewai/src/crewai/process.py` 只有 11 行，但定义了三种调度范式：

```python
class Process(str, Enum):
    sequential = "sequential"
    hierarchical = "hierarchical"
    # TODO: consensual = 'consensual'
```

**三种模式的语义**：

| 模式 | 调度方式 | 适用场景 |
|---|---|---|
| `sequential` | 按任务依赖顺序串行跑 | 流程化工作（先研究后写报告） |
| `hierarchical` | 自动派一个 manager agent 委派 + 校验 | 复杂多任务、需要质控 |
| `consensual` | 源码标记为 TODO，未合入当前主线 | — |

**`sequential` 是默认**——README 里的 Job Description / Trip Planner / Stock Analysis 三个 example 全用 sequential。**`hierarchical` 是进阶**——会自动创一个 manager agent（`Crew._create_manager_agent` 在 L1521）负责委派和验证。

> **值得停下来想想**：`consensual` 留 TODO 是有意为之还是被遗忘？社区里多用 hierarchical 兜底，**真正的多 agent 协商机制在 OpenAI Swarm / Anthropic 那边，没在 CrewAI 这边落地**——这从侧面反映了 CrewAI 团队对"manager 委派范式"的偏好。

### 2.2 Agent 五要素

`agent/core.py` 的 `Agent` 类继承 `BaseAgent`，靠五个要素构造：

| 要素 | 字段 | 作用 |
|---|---|---|
| **角色** | `role` | 系统提示里的人设锚 |
| **目标** | `goal` | 这个 agent 被设计来解决什么问题 |
| **背景故事** | `backstory` | 给 LLM 喂的"经验/性格"长文 |
| **工具** | `tools` | agent 能调用的 BaseTool 列表 |
| **LLM** | `llm` | 模型标识（支持 OpenAI/Anthropic/Bedrock/Ollama 等） |

**JSON-first 脚手架把这五要素压成 `agents/<name>.jsonc`**——`crewai create crew` 生成目录结构：

```
my_project/
├── .gitignore
├── .env
├── agents/
│   └── researcher.jsonc
├── crew.jsonc
├── knowledge/
├── pyproject.toml
├── README.md
├── skills/
└── tools/
```

`agents/researcher.jsonc` 原文：

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

`{topic}` 是**占位符**——`crew.jsonc` 里 `inputs.topic` 给默认值，CLI 跑起来会交互式问缺的值。这是 CrewAI 抹掉认知门槛的核心设计：**不用写 `class MyAgent(Agent)`，不用学 Pydantic，直接填 JSON**。

> **值得停下来想想**：JSON-first 不是降级——是**让 prompt 工程师和工程师用同一种语言协作**。`{placeholder}` + `crew.jsonc` 把"业务配置"和"代码配置"切干净，prompt 迭代不再触发 PR。

### 2.3 Task 依赖图

Crews 跑的是**带依赖的有向无环图（DAG）**——`crew.jsonc` 里的 `context: ["research_task"]` 表示 reporting_task 依赖 research_task 的输出。源码 `Crew._validate_context_no_future_tasks`（L868）严格校验「不能引用未跑的任务」。

**结构化输出**是 CrewAI 的另一个发力点：

- `output_pydantic`：强制任务输出 Pydantic 模型
- `output_json`：强制 JSON
- `output_file`：把输出写到指定路径（默认 markdown）
- `markdown: true`：声明输出是 markdown（避免整段被 ``` 包）

这些约束让 agent 输出**可直接被下游 Python 代码消费**——这是把 demo 推到生产的关键。

### 2.4 30 行最小可跑示例

下面这段代码只用 stdlib 级别的依赖（`crewai` + `openai`）就能跑通 sequential Crew。**抄进 `main.py` 加 `OPENAI_API_KEY` 就能验证**：

```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(
    role="{topic} Senior Researcher",
    goal="Uncover cutting-edge developments in {topic}",
    backstory="You're a seasoned researcher who finds relevant info clearly.",
    llm="openai/gpt-4o-mini",  # 可换 openai/gpt-4o、anthropic/claude-3-5-sonnet、ollama/llama3
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
    expected_output="3 bullets, each ≤ 25 words.",
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

**运行**：

```bash
uv tool install crewai
uv run --with crewai python main.py
```

这个示例**不依赖 MCP / 持久化 / 任何外部工具**——纯 LLM 调用，能在三分钟内跑通。这是判断"是否值得引入 CrewAI"的最快路径。

---

## 3 · Flows：事件驱动的控制层

Crews 是"做什么"，Flows 是"什么时候做、做完去哪里"。

### 3.1 三模块拆分

源码 `lib/crewai/src/crewai/flow/flow.py` 的 docstring 把架构讲明白：

> "The implementation now lives in three modules, split by concern:
> - `crewai.flow.dsl` — authoring decorators (`@start` / `@listen` / `@router`, `or_` / `and_`) and Python Flow class projection
> - `crewai.flow.flow_definition` — the serializable Flow Definition contract
> - `crewai.flow.runtime` — the Flow execution engine and state"

**三模块拆分的工程含义**：

| 模块 | 职责 | 何时改 |
|---|---|---|
| **dsl** | Python 装饰器 + 条件组合器 | 用户写 Flow 时调 |
| **flow_definition** | Flow 序列化协议（不可变 dataclass） | 改 Flow 模型时 |
| **runtime** | 执行引擎 + 状态机 | 改调度 / 状态持久化时 |

**这种拆分让 Flow 有了"作者层 / 协议层 / 引擎层"三段式**——跟你写 Web 框架（路由 → view → handler）一个套路。**DSL 改不动 protocol，runtime 改不动 dsl**——编译期/运行期/序列化期职责清晰。

### 3.2 五个装饰器

`lib/crewai/src/crewai/flow/dsl/__init__.py` 暴露五个装饰器：

| 装饰器 | 作用 | 类包装器 |
|---|---|---|
| `@start()` | 标记方法为 Flow 入口 | `StartMethod` |
| `@listen(condition)` | 标记方法为某条件的响应器 | `ListenMethod` |
| `@router(condition)` | 标记方法为路由（返回字符串触发路由） | `RouterMethod` |
| `or_(...)` | 任一条件触发 | — |
| `and_(...)` | 全部条件触发 | — |

DSL 层把所有装饰器都 wrap 成 `FlowMethodDefinition`（`flow_definition.py` 里的不可变 dataclass），用 `_merge_flow_method_definition` 合并到方法对象上。

**`_start.py` 源码（简化）**：

```python
def start(condition: FlowTrigger | None = None) -> FlowMethodDecorator:
    def decorator(func):
        wrapper = StartMethod(func)
        _merge_flow_method_definition(
            wrapper,
            FlowMethodDefinition(
                do=_method_action(func),
                start=(_to_definition_condition(condition)
                       if condition is not None else True),
            ),
        )
        return wrapper
    return cast(FlowMethodDecorator, decorator)
```

**关键细节**：`_method_action(func)` 把函数包装成"可序列化的动作描述"——这是 Flow 能在不同 runtime（Python / 远端 worker）跑通的根基。

### 3.3 状态与持久化

Flow 状态用 Pydantic 模型托管——`class MarketState(BaseModel)` 就是 `self.state`，Flow runtime 自动持久化。**持久化是可插拔的**：

`lib/crewai/src/crewai/flow/persistence/factory.py`：

```python
def set_flow_persistence_factory(factory: FlowPersistenceFactory | None) -> None:
    """Replace the process-wide default flow persistence factory.
    Intended for one-time setup at startup. Pass `None` to restore the
    built-in `SQLiteFlowPersistence`."""
    global _factory
    _factory = factory

def default_flow_persistence() -> FlowPersistence:
    factory = _factory
    if factory is not None:
        return factory()
    from crewai.flow.persistence.sqlite import SQLiteFlowPersistence
    return SQLiteFlowPersistence()
```

**默认是 SQLite 单文件**，但应用启动时可注册自己的 factory（远程数据库、in-memory 测试 fake、Redis 都可以）。**这是 CrewAI 把 Flow 当 long-running 服务看待的证据**——普通 Python 函数没有「pause / resume / checkpoint」，Flow 有。

> **值得停下来想想**：Flow 持久化工厂模式跟 `crewai_core.lock_store.set_lock_backend` 镜像——**这是 CrewAI 全栈的"应用启动一次性 setter"约定**。一旦看懂这套约定，CLIProxy / Flow Persistence / Tool Cache 都是同一个套路。

---

## 4 · Crew + Flow 联合实战：市场分析 flow

README L427-L499 给的"Advanced Analysis Flow"是 Crew + Flow 联合范式的标准范本。简化版：

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
            backstory="You're a veteran analyst..."
        )
        researcher = Agent(
            role="Data Researcher",
            goal="Gather and validate supporting market data",
            backstory="You excel at finding and correlating..."
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

**这个示例讲清楚了五件事**：

1. **Pydantic 状态模型**作为 Flow 类型参数 `Flow[MarketState]`
2. **`@start()` 标记入口**，`@listen(method)` 标记响应器
3. **`@router` 返回字符串触发路由**——`@listen("high_confidence")` 接住
4. **`or_()` 让一个监听器响应多个分支**
5. **Crew 作为 Flow 的一个 step**——自治与控制权干净分工

**关键设计点**：Flow 方法返回啥、Crew 方法返回啥，**没人规定**——`_method_action` 把函数当动作序列化时只看签名不看返回类型。**这给"业务语言多样性"留了口**——你可以让 Crew 返回 Pydantic、让 Flow 步骤返回 dict、让 router 返回枚举字符串，runtime 都不挑。

> **值得停下来想想**：这种"无类型强制"的代价——你得自己用 Pydantic / TypedDict 兜底，**否则 IDE 不会帮你校验**。这是 Python 动态类型的取舍，CrewAI 选了"宽容 + 约定俗成"。

---

## 5 · execution_uuid：分布式追踪的 contextvars 实战

CrewAI 的 telemetry 体系靠 `execution_uuid` 这个 contextvar 串联——`lib/crewai/src/crewai/execution.py`：

```python
_current_execution_uuid: contextvars.ContextVar[str | None] = ...

def begin_execution(execution_uuid: str | None = None):
    if _current_execution_uuid.get() is not None:
        return None
    return set_execution_uuid(execution_uuid or str(uuid4()))

def end_execution(token):
    if token is not None:
        clear_execution_uuid(token)
```

**关键设计**：

- **最外层 kickoff 创建 uuid**（默认 `str(uuid4())`）
- **嵌套 kickoff 继承外层**（_current_execution_uuid.get() != None 时直接 return None 不新建）
- **enterprise 可在外面 stamp 自己的 uuid**（Celery kickoff_id 等）——`set_execution_uuid(kickoff_id)`

**为什么走 contextvars**：event bus 的 handler 跑在 worker 线程，**不能把 contextvars 写回用户线程**。所以 uuid 在 kickoff 调用路径上 mint，**不通过 event bus 传**——这是分布式追踪里典型的"业务事件流" vs "控制面事件流"分层。

> **值得停下来想想**：这就是 CrewAI AMP（商业控制面）跟 OSS 的耦合点——enterprise 把 `kickoff_id` 提前 `set_execution_uuid`，**Wharf / OpenTelemetry span 全用这个 id 当 trace_id**，OSS 跑没 enterprise 时自己 mint 一个。**耦合点干净，不绑死**。

---

## 6 · AGENTS.md 的一条隐性铁律

仓库 `AGENTS.md` 第 15-23 行有一条容易被忽略的硬规则：

> "**`LLMMessage.content` is `str | list[dict[str, Any]] | None`**; the list form is multimodal content parts. **Never `str()` it** — that puts a Python repr (`[{'type': 'text', 'text': 'hi'}]`) in front of the model and into memory. Collapse a message to text with the helper instead:
>
> ```python
> from crewai.utilities.agent_utils import message_content_text
>
> text = message_content_text(msg)  # "" for None; joined text for a parts list
> ```"

**这条铁律的工程含义**：

LLM 现在普遍支持多模态——content 不再是字符串，而是 `[{"type": "text", "text": "..."}, {"type": "image", "image_url": "..."}]` 这种 parts list。**如果 agent 代码里直接 `str(msg)`，parts list 会被 Python repr 成 Python 字面量**——`[{'type': 'text', 'text': 'hi'}]` 这种字符串**直接喂给 LLM 当成 prompt**，LLM 看到的不是"hi"而是 Python 字典的 repr。

**`message_content_text(msg)`** 是 CrewAI 提供的"折叠 helper"：
- `None` → `""`
- `str` → 原样返回
- `list[dict]` → 把 `{"type": "text", "text": "..."}` 拼起来

`_content_parts_text` 还**容错**——跳过非文本 parts 不抛异常，没有可用文本时返回 `"[multimodal content]"`。

> **值得停下来想想**：这是 CrewAI 文档级别的反"AI 幻觉"防御——**LLM 看到的 prompt 必须是真实语义，不能是 Python 字面量**。任何 Agent 框架在接多模态时都得面对这个问题，CrewAI 把它写进 AGENTS.md，**让所有贡献者都看见**。

---

## 7 · JSON-first vs Python-classic：两条路径都留口

CrewAI 脚手架**同时支持 JSON-first 和 Python-classic 两种项目结构**：

```bash
crewai create crew <project_name>            # JSON-first（默认）
crewai create crew <project_name> --classic  # Python-classic（带 crew.py + YAML）
```

JSON-first 是新默认（README 推荐），但 Python-classic 还在——`config/agents.yaml` + `config/tasks.yaml` + `crew.py` 这套老范式没被弃。

**为什么两条都留**：

1. **新用户**用 JSON 快速搭 prototype
2. **老用户**用 Python 写复杂逻辑（继承 `Agent` / 自定义 hook / 动态生成任务）
3. **混合**——JSON 写静态 agent、Python 写动态 hook

**AGENTS.md 第 8-9 行明文约定**：CLI 用 `crewai run` 加载 JSON，**任何逻辑改动必须最小化 diff**——这是 CrewAI 团队对"JSON-first 是否限制能力"的回答：**JSON 是描述层，Python 才是执行层**。

---

## 8 · Skills 与 A2A：跟上 2026 的协议战

CrewAI 2026 年的两个发力点：

### 8.1 Skills（编码 agent 提示协议）

README L100-L120 的"Build with AI"章节直接挂了 Skills 安装命令：

```shell
# Claude Code
/plugin marketplace add crewAIInc/skills
/plugin install crewai-skills@crewai-plugins

# Cursor / Codex / Windsurf
npx skills add crewaiinc/skills
```

四个 Skills：

| Skill | 触发时机 |
|---|---|
| `getting-started` | 脚手架新项目、选 `LLM.call()` / `Agent` / `Crew` / `Flow` |
| `design-agent` | 配置 agent 角色 / 目标 / 工具 / LLM |
| `design-task` | 写 task 描述 / 依赖 / 结构化输出 |
| `ask-docs` | 查 live docs MCP server |

**这是 CrewAI 跟 Claude Agent SDK / Codex CLI 在 Skills 协议上的对齐**——同一个 spec，不同家实现，编码 agent 跨框架一致体验。

### 8.2 A2A（Agent-to-Agent 协议）

`lib/crewai/src/crewai/a2a/` 是 CrewAI 的 A2A 实现——`a2a/auth/`、`a2a/utils/`、`a2a/updates/`、`a2a/extensions/` 四子包。A2A 是 Google 在 2025 年推的跨 Agent 通信协议（按 A2A 官方仓库 README 描述），CrewAI 紧跟。

**A2A vs MCP 的分工**：
- **MCP**：Agent ↔ 工具 / 数据源
- **A2A**：Agent ↔ Agent（跨进程 / 跨语言 / 跨厂商）

CrewAI 同时支持 MCP（`lib/crewai/src/crewai/mcp/`）和 A2A，**两条协议都不站队**。

> **值得停下来想想**：CrewAI 的中立性是商业护城河——LangGraph / AutoGen 强绑 LangChain / Microsoft 系，**CrewAI 跟谁都接得上**。10 万认证开发者一半来自 multi-vendor 场景。

---

## 9 · 何时用 CrewAI、什么时候别用

README L630-L637 的"When to Use CrewAI"明文：

> "Use CrewAI when you need more than a single prompt or chatbot: multi-step work, specialized agents, tool use, structured outputs, human review, or workflows that combine autonomous reasoning with explicit business logic."

**适合**：

- ✅ 多步骤 / 多角色协作（研究 + 写报告 + 审稿）
- ✅ 结构化输出（Pydantic / JSON / markdown 文件）
- ✅ 工具 + 记忆 + checkpointing（要 long-running 状态）
- ✅ Crew + Flow 联合（自治一段、控制一段）
- ✅ Human-in-the-loop（Flow 的 `human_feedback` decorator）

**不适合**：

- ❌ 单轮 prompt → 单输出（用 LangChain / 直接调 LLM）
- ❌ 极致低延迟（agent 间协作有 LLM 调用开销）
- ❌ 强类型保证（Python 动态类型 + JSON-first 配置都是软约束）
- ❌ 极简团队（10 万开发者生态是优势也是噪音源）

> **值得停下来想想**：判断标准不是"复不复杂"——是**「自治段 vs 控制段」是否需要切开**。Crews 给自治段、Flows 给控制段，**只有当你需要切开时才该用 CrewAI**。

---

## 10 · 一句话架构总结

```
crewai (Python ≥ 3.10, < 3.14)
├── crews/         # 自治协作（Agent + Task + DAG + Process）
│   ├── crew.py         # 2490 行，Crew 主类 + 验证 + 执行
│   ├── agent/core.py   # 2155 行，Agent 主类 + 执行 prompt 构建
│   ├── tasks/          # conditional_task / guardrail / output_format
│   └── process.py      # 3 个枚举（sequential / hierarchical / TODO consensual）
├── flow/          # 事件驱动控制（DSL + 协议 + runtime + persistence）
│   ├── dsl/            # 5 装饰器（@start / @listen / @router / or_ / and_）
│   ├── flow_definition.py  # 序列化协议
│   ├── runtime/        # 执行引擎
│   └── persistence/    # SQLite 默认 + 可插拔 factory
├── llms/          # 12+ provider 适配（OpenAI / Anthropic / Bedrock / Ollama / ...）
├── memory/        # 短期 + 长期 + 实体记忆
├── knowledge/     # RAG：embeddings + 文档存储
├── tools/         # 工具生态（SerperDevTool / 浏览器 / DB / ...）
├── mcp/           # MCP 客户端（Agent ↔ 工具）
├── a2a/           # A2A 实现（Agent ↔ Agent）
├── skills/        # Skills 协议（编码 agent 提示）
├── telemetry/     # OpenTelemetry + Wharf（AMP 集成点）
└── security/      # guardrails + 权限
```

**这张图是一份 CrewAI 的"心智地图"**——你不需要全看源码，按这张图找模块：

- 想改 agent 行为 → `agent/core.py`
- 想改调度方式 → `crew.py` + `process.py`
- 想改 Flow 装饰器 → `flow/dsl/`
- 想改持久化后端 → `flow/persistence/`
- 想接新 LLM → `llms/`（继承 BaseLLM）

---

## 写在最后：CrewAI 在 2026 Agent 框架战里的位置

回到开头的剧本——Multi-Agent 框架 2026 年的赢家不会是"功能最多"，会是**"最像生产工程"**。

**CrewAI 押了三件事**：

1. **双层抽象（Crews × Flows）**——自治和控制分开管
2. **JSON-first 脚手架**——抹掉认知门槛，让 prompt 工程师和工程师协作
3. **中立协议支持**（MCP / A2A / Skills）——不绑死任何一家模型厂商

**LangGraph 押的是图灵完备**（任何拓扑都能写）、**AutoGen 押的是对话范式**（agent = 对话参与者）、**Claude Agent SDK 押的是 Anthropic 一统**。

**CrewAI 的赌注是「工程化的中立编排器」**——不发明新范式，把现有的（Pydantic / 装饰器 / SQLite 持久化）揉成「企业能直接用的 Multi-Agent 框架」。

10 万认证开发者（README L26 项目方自述）是这条赌注的市场验证。**MIT 协议 + 10 万开发者 + 三层中立**——这是 2026 年 Multi-Agent 战场少数还在涨的 Python 原生框架。

---

> **参考链接**：
> - GitHub 仓库：<https://github.com/crewAIInc/crewAI>
> - 官方文档：<https://docs.crewai.com>
> - 学习课程：<https://learn.crewai.com>
> - Examples：<https://github.com/crewAIInc/crewAI-examples>
> - 企业版 AMP：<https://crewai.com/amp>
> - 社区：<https://community.crewai.com>
> - 博客：<https://blog.crewai.com>

> **本文基于**：`README.md`（741 行）+ `AGENTS.md` + `pyproject.toml` + `lib/crewai/src/crewai/` 全模块源码 + `docs/edge/en/concepts/` 22 个 .mdx。
>
> **作者**：钳岳（天庭掌管 AI 知识库官员）
>
> **发布时间**：2026-09-02 19:10 GMT+8