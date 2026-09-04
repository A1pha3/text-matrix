---
title: "Pydantic AI 深度解析：当验证之王决定教会 Agent 说话带类型"
slug: pydantic-ai-typed-agent-framework-deep-dive
github_repo: "pydantic/pydantic-ai"
source_key: "gh:pydantic/pydantic-ai"
date: 2026-09-03T10:45:00+08:00
lastmod: 2026-09-04T18:30:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Pydantic AI", "AI Agent", "类型安全", "LLM 框架", "Python"]
description: "Pydantic AI 是 Pydantic 团队推出的类型安全 Agent 框架：用 Pydantic Model 定义输出、用函数签名定义工具、用 Capability 组装一切，同一个 Agent 能跑在终端、语音通话和 Temporal 工作流里。本文从源码拆解它的三大抽象与工程取舍。"
---

# Pydantic AI 深度解析：当验证之王决定教会 Agent 说话带类型

## 核心判断

在 Agent 框架多如牛毛的 2026 年，Pydantic AI（GitHub 近两万 star，v2.39.0，MIT 协议）押注的不是"功能最多"，而是一个看似朴素的命题：**LLM 应用从原型到生产的距离，本质上是"无类型"到"有类型"的距离。**

这个判断有资格由 Pydantic 团队来做。他们的验证库是 OpenAI SDK、Anthropic SDK、Google ADK、LangChain 和大半个 AI 生态的验证层，也是 FastAPI 得以成立的地基。这些框架在 Python 世界推广类型注解这件事上做的事，比任何语言委员会都多。现在他们把同一套哲学搬进了 Agent 领域：**你的 IDE、类型检查器和编码 agent，都应该知道你的 agent 返回什么。**

这不是营销话术。翻开源码你会看到，"typed end to end"在这门框架里是可验证的物理事实，不是宣传页上的形容词。

进入细节前先给一张地图。这个框架值得记住的其实就是四层，每层各管一件事：

| 层 | 代表抽象 | 管什么 |
|------|------|------|
| 模型层 | `Model` / `Provider` / `ModelProfile` | 把供应商差异压成一个字符串，按能力表自动降级 |
| 扩展层 | `Capability` / `Toolset` | 把工具、指令、钩子、模型设置捆成可组合、可排序的单元 |
| 执行层 | `pydantic_graph` | 把 Agent 循环建模为类型化图，节点级可观测 |
| 运行层 | CLI / Web / 实时语音 / Temporal 等 | 同一个 Agent 定义，五种跑法、四种部署形态 |

## 一个最小样本，先看气质

不读文档，先读代码。以下是仓库 examples 目录里的轮盘赌示例（`roulette_wheel.py`）的骨架：

```python
from dataclasses import dataclass
from typing import Literal

from pydantic_ai import Agent, RunContext


@dataclass
class Deps:
    winning_number: int


roulette_agent = Agent(
    'groq:llama-3.3-70b-versatile',
    deps_type=Deps,
    retries=3,
    output_type=bool,
    system_prompt='Use the `roulette_wheel` function to determine if the customer has won.',
)


@roulette_agent.tool
async def roulette_wheel(
    ctx: RunContext[Deps], square: int
) -> Literal['winner', 'loser']:
    """Check if the bet square is a winner."""
    return 'winner' if square == ctx.deps.winning_number else 'loser'


result = roulette_agent.run_sync(
    'Put my money on square eighteen', deps=Deps(winning_number=18)
)
print(result.output)  # True，在 IDE 里被推断为 bool，不是 str
```

三处类型信息：依赖是 `Deps`（dataclass）、输出是 `bool`、工具签名是 `(ctx, square: int) -> Literal['winner', 'loser']`。工具的 JSON Schema 直接从函数签名和 docstring 生成，模型传错参数会在你的代码执行**之前**被 Pydantic 拦截；`result.output` 被推断为 `bool`——不是 `Any`，不是需要 `json.loads` 再手动转换的字符串。

大多数框架把"结构化输出"做成可选的高级功能，Pydantic AI 把它做成默认的骨架。`output_type` 接受 Pydantic Model、`TypedDict`、dataclass、标量、联合类型，运行结束前模型必须交出能通过验证的数据，否则带着校验错误重试。产出物从"一段需要人眼的文本"变成"一个可以放心参与后续程序流的值"。

结构化输出默认走工具调用：框架把输出类型注册成一次工具调用，官方文档说这一路径"在广泛模型上表现良好"（OpenAI 的模型档案里 `default_structured_output_mode` 就落在 `'tool'`）。`output_mode` 参数可以换路——**NativeOutput** 走供应商原生的 JSON Schema 输出（在支持的模型上约束更强）；**PromptedOutput** 把 Schema 写进提示词，照顾那些既不支持工具也不支持结构化输出的模型。三条路对应 ModelProfile 里的能力位：同一个 Agent，换一个模型，输出路径自动降级，业务代码不动。

## 三大抽象：这个框架真正的产品

读源码比读 README 更能看清一个框架的野心。Pydantic AI 的 monorepo 里有三个包：核心的 `pydantic_ai_slim`、评测用的 `pydantic_evals`、和图执行库 `pydantic_graph`。支撑整个体系的是三组抽象。

### 一、Model 与 Provider：把"换模型"压缩成一个字符串

`models/` 目录下躺着 Anthropic、OpenAI、Google、Bedrock、Groq、Mistral、xAI、Ollama 等二十多个模型实现；`providers/` 目录下是三十多个供应商接入。对使用者的承诺是：`Agent('openai:gpt-5.2')` 换成 `Agent('anthropic:claude-fable-5')`，其余代码一行不改。

有意思的是夹在中间的 **ModelProfile**。每家模型的能力差异——默认走哪档结构化输出、能否支持严格工具定义、思考内容用什么格式传——被建模成一个声明式的数据描述。框架据此自动降级：档案里 `default_structured_output_mode` 落在 `'tool'` 的走工具调用，落在 `'native'` 的走原生 JSON Schema，连工具都不支持的模型则落到提示词路径。**适配层差异的工程，从"每个使用者的 if-else"收拢为"框架内部的一张能力表"。** 这是把浏览器兼容性问题做成 caniuse 的思路。

### 二、Capability 与 Toolset：一个原语统治所有扩展

这是当前版本扩展系统的中心：工具、指令、钩子、原生工具、模型设置，都被收进同一个原语——**Capability**，可复用地捆绑在一起的单元。`capabilities/` 目录下的 hooks、native_tool、web_search、web_fetch、image_generation、thinking 等二十多个子类，把形形色色的扩展都做成同一种形态。

README 里那个银行客服示例最能说明问题：

```python
customer_context = Capability[SupportDependencies](
    id='customer-context',
    description="Who the customer is and what's on their account.",
)

@customer_context.instructions
async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str: ...

@customer_context.tool
async def customer_balance(ctx: RunContext[SupportDependencies], include_pending: bool) -> float: ...

refunds = Capability[SupportDependencies](
    id='refunds', description='...', defer_loading=True,
)

support_agent = Agent('openai:gpt-5.6-sol', capabilities=[customer_context, refunds])
```

两处设计值得停下来看。

**延迟加载（`defer_loading=True`）**：`refunds` 能力的工具和指令平时对模型隐藏，直到模型判断对话需要退款查询，才通过 `load_capability` 工具主动加载。这直接回应了 Agent 工程的头号痛点——工具太多导致的上下文膨胀和选择困难。它是"按需引入的 npm 包"，只不过引入的决策者是模型。

**中间件语义与拓扑排序**：Capability 链遵循中间件模型，每个能力可以包裹模型请求、工具执行、输出校验的完整生命周期。多个能力的先后顺序不再靠数组顺序碰运气——每个能力可以声明 `outermost`/`innermost` 位置约束和相互依赖，`CombinedCapability` 用标准库 `graphlib.TopologicalSorter` 做拓扑排序，声明冲突（缺依赖、成环）在构造期就抛 `UserError`。**"组合的行为可预测"从口头承诺变成构造期校验。**

工具层面同样有体系：`FunctionToolset` 把 Python 函数变成工具，`CombinedToolset`/`FilteredToolset`/`RenamedToolset`/`ApprovalRequiredToolset` 等包装器完成组合、过滤、改名、人工审批。MCP 服务器同样是 Capability：`MCP()` 传 URL 接远程服务器（Streamable HTTP/SSE），`local=` 传脚本走 stdio，再给 `native=True` 就能让支持原生 MCP 的模型直接拿到同一批工具。

### 三、Graph：Agent 循环的底座是一个独立的类型化图库

很多人不知道，Agent 的运行循环本身建立在一个独立发布的库 `pydantic_graph` 之上（约 4500 行，含 `Step`/`Decision`/`Fork`/`Join` 原语和 Fork-Join 并行归约）。Agent 循环被建模为三个节点的图：`UserPromptNode → ModelRequestNode → CallToolsNode`，工具结果回流到模型请求节点，直到产出合法输出抵达 `End`。

这个设计带来一个别人给不了的 API：`agent.iter()` 让你逐节点迭代整个运行过程，拿到每一次模型响应、每一次工具调用的完整事件流——调试 Agent 时"看看它到底干了什么"从考古变成了直播。而当简单循环不够用，你可以直接用 `pydantic_graph` 编排带类型检查的多阶段工作流，Agent 只是其中一个可以复用的节点。

同一个 Agent 定义，还以五种方式运行（`run`/`run_sync`/`run_stream`/`run_stream_events`/`iter`），部署形态覆盖终端 CLI（一行 `agent.to_cli_sync()`）、内置 Web 聊天、实时语音（OpenAI Realtime、Gemini Live、Azure、xAI Grok Voice）、以及持久化执行——挂上 `TemporalDurability`，同一段 Agent 代码进入 Temporal 工作流，每次模型调用和工具执行成为可恢复的 activity，进程崩溃、重启、跑上几天都不丢状态。DBOS 和 Prefect 以同样的方式第一方接入。

## 一次运行，穿过整个系统

抽象讲完了，看一次真实调用怎么流过这四层。以银行客服 Agent 处理"我丢卡了"为例：

`run('I just lost my card!', deps=...)` 进入后，框架先把用户输入包成 `UserPromptNode`，随后 `ModelRequestNode` 向供应商发起请求——请求发出前，Capability 链已按拓扑序包好：customer_context 能力的指令函数先查库拼出"客户是 John"，输出类型 `SupportOutput` 被注册成一次工具调用；ModelProfile 查表确认当前模型支持工具。模型返回"建议临时冻结卡片、风险等级 8"的调用请求，`CallToolsNode` 在执行你的函数前先用 Schema 校验参数，产出通过 `SupportOutput` 验证后抵达 `End`。全程每一步都是图上的一个节点，`agent.iter()` 能逐节点直播；如果挂了 `TemporalDurability`，这些节点同时是可恢复的 activity，进程崩了从断点续跑。

一个丢卡请求，穿过四层抽象，每一步都有类型、有验证、有痕迹。这就是这门框架对"生产级"的具体定义。

## 观测与评测：生产化不是可选附件

Pydantic AI 的母公司卖可观测性产品（Logfire），所以框架的埋点做得极其认真：OpenTelemetry 原生，一行开启，span 覆盖每次模型请求与工具调用，成本追踪基于他们维护的 genai-prices 数据集。配套的 `pydantic_evals` 提供数据集、评测器、报告三件套——把"agent 行为的回归测试"做成了 pytest 之于代码的对应物。

配合 `AgentSpec`（用 YAML/JSON 声明式定义 Agent）和测试专用的 `TestModel`（不需要 API key 就能跑通完整 Agent 循环），从开发、调试、评测到监控有一条完整的路径。

## 限制与代价

实事求是地讲代价。

**抽象面积不小。** Agent 构造函数的参数列表很长，Capability 的绑定分两个阶段，工具集的包装器有十来种。对"只想调一次 API"的用户，这里有学习曲线。仓库根目录的 AGENTS.md 里写着团队的价值排序——"我们偏好强原语、强抽象、通用方案与扩展点，胜过为特定用例做的窄方案"——这本身就意味着不为最小场景做特化。

**版本迭代以天计。** v2.37.0（9 月 1 日）、v2.38.0（9 月 3 日）、v2.39.0（9 月 4 日），三天三个版本，README 里的 API 面貌换得很快。好在仓库的 AGENTS.md 把兼容性写进了贡献守则——任何改动"不得改变未触及该问题的用户行为"，重构不得以破坏既有代码为代价。

**生态位上，Harness 是分开的仓库。** 记忆管理、子代理、上下文压缩、完整编码 Agent 这些"重装备"在 `pydantic-ai-harness` 里，核心库刻意保持轻。喜欢一站式全家桶的人要多装一个包；喜欢核心干净的人会感激这条边界。

## 谁该用，谁不该

适合的场景很清晰：**Python 技术栈、追求类型安全、agent 要进生产系统而不是停在 demo。** 尤其是已有 FastAPI/Pydantic 资产的团队——依赖注入的类型化设计与 FastAPI 的 `Depends` 是同一种心智模型，Agent 像又一个 Router 一样挂进现有工程。

不必强求的场景：纯探索性原型、习惯动态类型的开发者会觉得约束烦，以及只需要一次性脚本调 API 的轻量需求。

## 结语

框架的竞争迟早会从"谁的功能清单更长"转向"谁的错误更早暴露"。Pydantic AI 把类型系统从"锦上添花的工程素养"变成"Agent 框架的第一性设计"——让一整类运行时错误在写下代码的那一刻就被 IDE 划红线，让模型输出在离开框架之前必须通过验证，让能力的组合在构造期就完成一致性检查。

这不大可能立刻赢得所有开发者，但生产环境的教训会替它说话。毕竟，这套打法在 Web 开发领域已经被 FastAPI 验证过一次了。

---

**项目信息**：pydantic/pydantic-ai · MIT · Python 3.10+ · 近两万 star · 文档 [pydantic.dev/docs/ai](https://pydantic.dev/docs/ai)
