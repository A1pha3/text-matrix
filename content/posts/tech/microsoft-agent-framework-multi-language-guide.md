---
title: "Microsoft Agent Framework：把多步 Agent 执行改造成可观测系统"
date: "2026-04-12T02:31:39+08:00"
slug: microsoft-agent-framework-multi-language-guide
github_repo: "microsoft/agent-framework"
description: "微软官方 Agent 框架（Python / .NET / Go）深度解读：统一 Semantic Kernel 的企业基座与 AutoGen 的多 Agent 编排，核心是让长流程工作流可观测、可检查点、可人工干预。"
draft: false
categories: ["技术笔记"]
topics: ["open-source-ai-tools"]
tags: ["Microsoft", "AI Agent", "Python", ".NET", "工作流"]
---

# Microsoft Agent Framework：把多步 Agent 执行改造成可观测系统

## 学习目标

读完本文你应该能够：

- 说清 Microsoft Agent Framework 的定位，以及它跟 Semantic Kernel、AutoGen 的关系。
- 分别用 Python 和 .NET 跑通一个最小 Agent，并完成一次流式调用的接入。
- 区分单个 Agent、多 Agent 工作流、Harness Agent 三者的边界，说清在什么场景用哪一个。
- 用 `SequentialBuilder` 把一个序列化多 Agent 流程改成可观测、可流式的工作流。
- 接入 OpenTelemetry 拿到分布式追踪，并用 DevUI 做交互式调试。
- 判断自己的项目该不该迁移，以及从 Semantic Kernel / AutoGen 迁移时从哪里切入。

## 一套框架，两个来源，三种机制

先给判断：**Microsoft Agent Framework（简称 MAF）真正解决的，不是把一次「呼叫模型」封装成对象，而是把多步、多 Agent、可能跨小时执行的工作流变成可观测、可检查点、可人工干预的系统。**

它不是一个从零写的新框架。2025 年 10 月微软把两条产品线并到同一个开源 SDK 里：**Semantic Kernel 的企业基座**——类型化、中间件、内置遥测，与 **AutoGen 的编排能力**——轻量多 Agent 抽象。到 2026 年初 .NET 与 Python 双双发布 1.0 稳定版，Go 仍处于公开预览。

这套框架里最容易被混淆的是三套东西：单个 **Agent**、多 Agent 编排的 **Workflow**、以及内置了长任务能力的 **Harness Agent**。它们解决的问题不同，接口也不同。下面先把各自的边界划开，再逐个展开。

## 项目概览

| 维度 | 说明 |
|------|------|
| 仓库 | github.com/microsoft/agent-framework |
| 许可证 | MIT |
| 语言 | Python、.NET / C#（1.0 稳定）；Go（公开预览） |
| 版本 | 1.0（2026-04-03 发布公告）；API 承诺向后兼容 |
| 官方文档 | learn.microsoft.com/agent-framework |

框架对外分四个层面：

| 层面 | 解决什么 | 要不要代码 |
|------|---------|-----------|
| **Agents** | 单个智能体：读 LLM、调工具、接 MCP 服务器 | 核心 |
| **Harness Agent** | 开箱即用的「多步骤长任务」智能体：规划、记忆、文件访问、权限确认 | 声明式为主 |
| **Workflows** | 把多个 Agent 和确定性函数编排成执行路径 | 核心 |
| **Integrations** | 模型提供商、Agent 服务、工具、中间件、评估、UI 的接入 | 按需 |

## 单个 Agent：最小的组合单元

一个 Agent 由两部分组合而成：**模型客户端**（怎么连到 LLM）加 **instructions**（系统提示词）。再往上，可选的**工具**、**会话状态（Agent Session）** 和**上下文提供者（Context Provider）**控制它能做什么、记住什么。

### 用 Foundry 的最小 Agent（Python）

```python
# pip install agent-framework
# 先运行 az login 完成 Azure CLI 认证

import asyncio
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

agent = Agent(
    client=FoundryChatClient(
        project_endpoint="https://your-foundry-service.services.ai.azure.com/api/projects/your-foundry-project",
        model="gpt-5.4-mini",
        credential=AzureCliCredential(),
    ),
    name="HelloAgent",
    instructions="You are a friendly assistant. Keep your answers brief.",
)

result = await agent.run("What is the largest city in France?")
print(f"Agent: {result}")
```

### 用 OpenAI 的最小 Agent（Python）

不走 Azure 时换一个客户端类即可，框架从环境变量读取 `OPENAI_API_KEY` 与 `OPENAI_CHAT_MODEL`：

```python
import asyncio
from dotenv import load_dotenv
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

load_dotenv()

async def main():
    agent = Agent(
        client=OpenAIChatClient(),
        name="HelloAgent",
        instructions="You are a friendly assistant. Keep your answers brief.",
    )
    result = await agent.run("What is the largest city in France?")
    print(f"Agent: {result}")

asyncio.run(main())
```

### 用 Foundry 的最小 Agent（.NET）

```csharp
// dotnet add package Microsoft.Agents.AI.Foundry --prerelease

using System;
using Azure.AI.Projects;
using Azure.Identity;
using Microsoft.Agents.AI;

var agent = new AIProjectClient(
        new Uri("https://your-foundry-service.services.ai.azure.com/api/projects/your-foundry-project"),
        new AzureCliCredential())
    .AsAIAgent(
        model: "gpt-5.4-mini",
        name: "HelloAgent",
        instructions: "You are a friendly assistant. Keep your answers brief.");

Console.WriteLine(await agent.RunAsync("What is the largest city in France?"));
```

1.0 的 Python 侧简化了命名：`ChatAgent` 改成 `Agent`，`ChatMessage` 改成 `Message`，`run_stream()` 并入 `run(..., stream=True)`，`@ai_function` 改成 `@tool`。读旧文档或旧示例时如果看到 `Chat*` 前缀，多半是 1.0 改名前的写法。

### 工具与 MCP

工具用 `@tool` 装饰普通函数注册，让 LLM 在回答过程中调用。框架层面把三种接入路径收拢在一起：**函数工具**、**托管工具（Hosted Tools）**、以及 **MCP 服务器**——后者让 Agent 直接消费现有的 MCP 生态，不用为每个服务手写适配层。

## 让一个任务流过系统：多 Agent 工作流

单个 Agent 来回调模型是线性的；一到「先让 A 起草，再让 B 评审」这类真实协作，就需要工作流。下面的例子来自官方 1.0 示例，正好演示一个任务如何穿过两个 Agent：

```python
import asyncio
from typing import cast

from agent_framework import Agent, Message
from agent_framework.foundry import FoundryChatClient
from agent_framework.orchestrations import SequentialBuilder
from azure.identity import AzureCliCredential

async def main() -> None:
    client = FoundryChatClient(credential=AzureCliCredential())

    writer = Agent(
        client=client,
        name="writer",
        instructions="You are a concise copywriter. Provide a single, punchy marketing sentence.",
    )
    reviewer = Agent(
        client=client,
        name="reviewer",
        instructions="You are a thoughtful reviewer. Give brief feedback on the previous message.",
    )

    workflow = SequentialBuilder(participants=[writer, reviewer]).build()

    # stream=True：节点产出边生成边推送
    async for event in workflow.run(
        "Write a tagline for Microsoft Agent Framework 1.0.",
        stream=True,
    ):
        if event.type == "output":
            for msg in cast(list[Message], event.data):
                print(f"[{msg.author_name or 'user'}]: {msg.text}")

asyncio.run(main())
```

这里能看出工作流相比裸调用的两个好处：顺序由**编排器显式声明**，每个 Agent 的产出都变成可枚举的 `Message` 事件，天然可观测；同时 `stream=True` 让长流程边跑边回流，而不是等到最后才吐一整段。

## 功能工作流与图工作流：两条不同的 API

MAF 1.0 同时提供两种工作流 API，**写法差异大于能力差异**，很多人在这里绕弯：

| | 功能工作流 | 图工作流 |
|---|-----------|---------|
| 声明方式 | `@workflow` / `@step` 装饰器，线性描述步骤 | `WorkflowBuilder` + 执行器 + 显式边 |
| 适合 | 步骤固定、逻辑接近函数流水线 | 分支、循环、路由复杂的拓扑 |
| 关键节点 | 普通函数步骤 | `AgentExecutor`、`FunctionExecutor`、`HumanInTheLoopExecutor` |

以图工作流为例，它把一个执行点建模成**执行器（Executor）**，再用 `set_start_executor` 与 `add_edge` 显式连接：

```python
frontend_executor = AgentExecutor(frontend_agent, id="frontend_agent")
concierge_executor = AgentExecutor(concierge_agent, id="concierge_agent")

workflow = (
    WorkflowBuilder()
    .set_start_executor(frontend_executor)
    .add_edge(frontend_executor, concierge_executor)
    .build()
)
```

当某一步需要人来拍板，就在流程里插入 `HumanInTheLoopExecutor`，执行会暂停在人工节点上等待确认，而不是让模型擅自往下走。**选择依据是拓扑复杂度**：步骤是固定线性流水线，用功能工作流更省；一旦出现根据分支路由、循环、需要人工确认的路径，才值得上图工作流。

## 可观测性：OpenTelemetry

框架内置 OpenTelemetry 支持，按 GenAI 语义约定输出 traces / metrics / logs，每个 Agent 执行、每个工作流节点都变成一个 span。开发期最省事的接法是设好导出地址后直接初始化：

```python
# 设置环境变量 OTEL_EXPORTER_OTLP_ENDPOINT 后
from agent_framework.observability import configure_otel_providers

configure_otel_providers()   # 此后所有 agent / workflow 执行自动打 trace
```

.NET 侧通过 builder 链挂载 OpenTelemetry：

```csharp
// 示例基于 AIProjectClient
var instrumentedChatClient = new AIProjectClient(new Uri(endpoint), new DefaultAzureCredential())
    .GetProjectOpenAIClient()
    .GetProjectResponsesClient()
    .AsIChatClient(deploymentName)
    .AsBuilder()
    .UseOpenTelemetry(sourceName: SourceName,
        configure: (cfg) => cfg.EnableSensitiveData = true)
    .Build();
```

两个要注意的点：

- **敏感数据开关**：`EnableSensitiveData` 会连同提示词、响应、函数参数一起入库，只应在开发/测试环境打开，否则生产日志可能泄露用户输入。
- **避免重复埋点**：如果同时给聊天客户端和 Agent 都开了遥测，同一段 prompt 会被记录两次，属正常现象；按需只在其中一侧开启。

本地可视化推荐 .NET 生态的 **Aspire Dashboard**，或者搭配 DevUI。

## 三件辅助件：中间件、DevUI、AF Labs

- **中间件（Middleware）**：一个请求/响应管道，用于拦截、变换、加认证、加日志和指标，同时服务单 Agent 与工作流。跨横切关注点逻辑（鉴权、重试、限流）放在这里，而不是散落在业务步骤里。
- **DevUI**：交互式开发者 UI，用来测试 Agent、可视化排错工作流。它不替代 SDK 能力——追踪、检查点、重放都通过代码暴露——只是在本地开发时把执行过程变成可点选的可视化界面。安装与启动命令以官方 DevUI 包的 Readme 为准。
- **AF Labs**：实验性包，涵盖基准测试、强化学习、研究功能。API 未承诺稳定，只建议做对比实验，不建议进生产链路。

## 多提供商与跨运行时互操作

框架通过**服务连接器（Service Connector）**抽象模型接入，1.0 自带 Microsoft Foundry、Azure OpenAI、OpenAI、Anthropic Claude、Amazon Bedrock、Google Gemini、Ollama、GitHub Copilot SDK 等首方连接器。替换模型通常只换一个客户端类，Agent 与工作流逻辑不因此改动。

跨运行时方面，**A2A（Agent-to-Agent）协议**让不同生态、不同语言的 Agent 之间可以通信，**MCP** 则负责工具互操作。想评估只出不进的新配置时，用哪个 Provider 取决于你已有资源：在 Azure 生态就直接用 Foundry / Azure OpenAI，私有推理或本地实验则走 Ollama 或 OpenAI 兼容端点。

## 从 Semantic Kernel / AutoGen 迁移

官方分别提供了迁移指南，两条路径的切入点不同：

- **从 Semantic Kernel**：你的 Agent 定义、工具、内存大多能平移，先迁 Agent 定义，再迁工具与插件，最后迁内存与存储。
- **从 AutoGen**：最大的差异在编排层——AutoGen 的隐式多 Agent（如 group chat）要用框架的**显式工作流**重新表达。官方建议先迁单 Agent 定义，再迁工作流，最后跑测试验证，已有的函数工具可以保留。

两类迁移共同的原则：**先让最小闭环跑通，再搬重逻辑**，别一次把整套资产搬过去。

## 故障排查

| 问题 | 常见原因 | 处理 |
|------|---------|------|
| Azure 认证 401 | 未登录或权限不足 | 先 `az login`，确认账号对 Foundry 项目有贡献者权限 |
| `dotnet add package` 失败 | 需要预发布版本 | 加 `--prerelease` 拉取 1.0 RC/预览包 |
| 环境变量缺失 | 未设置 key / model | 确认 `OPENAI_API_KEY` / `OPENAI_CHAT_MODEL` 或 Foundry 端点变量已配置 |
| trace 里看不到 span | 未初始化 OTel provider | 调用 `configure_otel_providers()`，并确认导出地址可达 |

**凭据提示**：`DefaultAzureCredential` 适合开发，生产环境换成特定凭据（如 `ManagedIdentityCredential`），可以避免未预期的凭据探测、额外延迟和回退链引入的安全风险。

## 采用建议

- **已在 .NET 生态、急需企业级 Agent 基座**的团队，MAF 是目前少有的官方选择：类型化、内置遥测、中间件与 Graph Workflow 都是现成的，优先上手。
- **Python 侧已在用 LangGraph / CrewAI** 的团队不必急着切换；图编排和内置 OpenTelemetry 是其优势，社区生态和第三方集成积累则相对薄弱，取舍要按项目实际边界算。
- **零散写 `requests` 调用**的团队别一步登天上工作流，先从单 Agent + 工具起步，跑出真实调用路径后，再按拓扑复杂度决定要不要引入 `SequentialBuilder` 或图工作流。
- **多轮的 AutoGen / Semantic Kernel 存量**：先出最小迁移用例，确认新框架能承接，再按官方指南渐进切换。

## 总结

Microsoft Agent Framework 1.0 的差异化在三点：**多语言官方实现（Python / .NET / Go）**、**统一两种工作流表达（功能 & 图）**、以及**把可观测性做成内置而非插件**。它把 Semantic Kernel 的企业基座与 AutoGen 的编排思路合到一个 SDK，价值不在多一个新调用库，而在让「多步、跨 Agent、可能跨小时」的执行变成一种可观察、可恢复、可人工把关的工程对象。

**相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/microsoft/agent-framework |
| 官方文档 | https://learn.microsoft.com/en-us/agent-framework/ |
| PyPI | https://pypi.org/project/agent-framework/ |
| NuGet | https://www.nuget.org/profiles/MicrosoftAgentFramework/ |
| 1.0 发布公告 | https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/ |

## 自测题

1. Microsoft Agent Framework 的「多语言」具体指哪几种？Go 的成熟度和 Python / .NET 一样吗？
2. 单个 Agent、多 Agent 工作流、Harness Agent 三者解决的分别是哪类问题？
3. 功能工作流和图工作流在什么情况下应该换着用？「某一步需要人工确认」更接近哪一种场景？
4. `run(..., stream=True)` 与 `run(...)` 的输出方式有什么不同？为什么长流程更适合流式？
5. 为什么 OpenTelemetry 的 `EnableSensitiveData` 只能在开发环境开？
6. 从 AutoGen 迁移时，最需要重写的是哪一层？为什么？

### 参考答案

1. 指 Python 与 .NET / C#（1.0 稳定）以及 Go（公开预览）。Go 仍处预览期，声明式 Agent、RAG、CodeAct、功能工作流等在 Go 侧还未落地。
2. 单个 Agent 解决「一次模型调用 + 工具」；多 Agent 工作流解决「多个步骤/多个角色的确定性编排」；Harness Agent 是开箱即用的长任务载体，内置规划、记忆、文件访问和权限确认。
3. 步骤固定、接近线性流水线时用功能工作流；分支、循环、路由复杂时用图工作流。需要人工确认的节点用 `HumanInTheLoopExecutor` 插进图里，属于图工作流的典型场景。
4. `run(..., stream=True)` 边生成边返回事件（`event.type == "output"`），不用等整段生成完；`run(...)` 一次性返回完整响应。长流程跨多个节点、耗时长，流式能在产出前让终端有反馈，也便于对外部系统逐步输出。
5. 打开后提示词、响应、函数参数和结果都会进入 trace；生产日志一旦外泄，就等于泄露用户输入和内部逻辑，所以只适合开发/测试环境。
6. 编排层。AutoGen 的隐式多 Agent（如 group chat）在 MAF 里要用显式工作流重新表达；单 Agent 定义、工具函数大多能保留。

## 练习

1. 用 Python 装好 `agent-framework`，把 OpenAI 客户端的 `instructions` 换成你自己项目的职责描述，用 `run(...)` 跑通一次完整回答，再改成 `stream=True` 观察输出差异。
2. 用 `SequentialBuilder` 造一个「起草 → 评审」两个 Agent 的流程，把返回的 `Message` 事件按发言人打印出来。
3. 给工作流加可观测性：设置 `OTEL_EXPORTER_OTLP_ENDPOINT`，调用 `configure_otel_providers()`，把 trace 导出到你本地的 Jaeger 或 Aspire Dashboard，确认一次执行能展开成一棵 span 树。
4. 写一个 `@tool` 包装你本地一个真实函数（比如读一个配置文件），让 Agent 在回答中调用它，验证工具返回值和模型输出能拼成一次完整回答。
5. 判断你要做的任务属于哪种形状：画一张流程图，标出哪个节点必须人工确认、哪个节点可能循环；据此决定用功能工作流还是图工作流。

## 进阶路径

- **深读编排**：读仓库 `python/packages/orchestrations` 下 `SequentialBuilder` 与 `WorkflowBuilder` 的调度实现，理解事件流、检查点与 `HumanInTheLoopExecutor` 的阻塞等待如何落地。
- **可观测性落地**：把 trace 接到你们现有 APM，做「一次对话 → 各 span → Token / 延迟」的下钻看板，而不是只在本机 DevUI 看一眼。
- **托管与生产化**：从本地 DevUI 走向 A2A、Durable 托管，重点处理凭据、横向扩展与状态持久化。
- **迁移评估**：如果你有 Semantic Kernel 或 AutoGen 存量，跑一个最小迁移用例，用框架自带的评估能力对比迁移前后行为差异。

## 常见问题 FAQ

**Q1：Azure 一直报 401？**
先确认跑过 `az login` 且账号对该 Foundry 项目有贡献者权限；开发期可用 `DefaultAzureCredential`，生产建议换 `ManagedIdentityCredential`。

**Q2：Python 和 .NET 的能力完全对等吗？**
API 设计保持一致，但两个生态的成熟度不是同步推进的，Go 侧更是预览状态。落地前以官方文档的版本说明为准，别默认一端的示例能直接翻译到另一端。

**Q3：图工作流和普通链式调用有什么区别？**
链式调用是固定线性的；图工作流把执行点建模成执行器并用显式边连接，支持分支、汇聚、循环和人工节点，适合多 Agent 协作与长流程。

**Q4：一个 Agent 想接多个模型怎么办？**
通过服务连接器抽象，多为换客户端类即可；需要跨运行时通信时用 A2A，工具互操作用 MCP。

**Q5：不用 DevUI 能调试吗？**
可以。DevUI 只是交互式辅助，追踪、检查点、重放的入口都通过 SDK 暴露，完全可以在单测或脚本里触发和断言。

**Q6：从 AutoGen 迁过来，工作流要重写吗？**
编排层要重写：AutoGen 的隐式 group chat 要用显式工作流表达。单 Agent 定义和工具函数大多能保留，主要改的是「谁在什么顺序调用谁」这一层。