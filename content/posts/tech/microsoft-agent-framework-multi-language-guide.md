---
title: "Microsoft Agent Framework：微软官方·双语言支持·图工作流"
date: "2026-04-12T02:31:39+08:00"
slug: microsoft-agent-framework-multi-language-guide
description: "Microsoft Agent Framework 是微软官方的 Agent 框架，支持 Python 和 .NET 双语言，提供图工作流和多种 Provider 支持。"
draft: false
categories: ["技术笔记"]
tags: ["Microsoft", "Agent", "Python", ".NET", "工作流"]
---

# Microsoft Agent Framework：Python + .NET 双语言 Agent 框架

## 学习目标

读完本文你应该能够：

- 说清 Microsoft Agent Framework 的定位，以及「Python + .NET 双语言实现」对团队选型意味着什么。
- 用 Python 或 .NET 跑通一个最小 Agent，并完成一次带流式输出的调用。
- 用 Graph-based Workflows 把 Agent 节点和确定性函数编排成数据流，并利用检查点与人在回路。
- 接入 OpenTelemetry 拿到分布式追踪，并用 DevUI 做交互式调试与重放。
- 判断自己的项目是否适合采用它，以及从 Semantic Kernel / AutoGen 迁移时需要注意什么。

## 本文目录

- [一、项目概述](#一项目概述)
- [二、核心功能](#二核心功能)
- [三、快速开始](#三快速开始)
- [四、Python 示例项目](#四python-示例项目)
- [五、.NET 示例项目](#五net-示例项目)
- [六、图工作流](#六图工作流)
- [七、DevUI](#七devui)
- [八、可观测性](#八可观测性)
- [九、中间件](#九中间件)
- [十、多 Provider 支持](#十多-provider-支持)
- [十一、AF Labs](#十一af-labs)
- [十二、托管选项](#十二托管选项)
- [十三、故障排除](#十三故障排除)
- [十四、迁移指南](#十四迁移指南)
- [十五、文档资源](#十五文档资源)
- [十六、实践建议](#十六实践建议)
- [十七、总结](#十七总结)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [常见问题 FAQ](#常见问题-faq)

## 一、项目概述

### 1.1 Microsoft Agent Framework 是什么

**Microsoft Agent Framework** 是微软的多语言 Agent 框架，同时提供 **Python** 和 **.NET/C#** 实现，API 设计保持一致。主要能力是图编排（graph-based workflow），支持流式输出、检查点、人在回路和时间旅行调试。

> "Welcome to Microsoft's comprehensive multi-language framework for building, orchestrating, and deploying AI agents with support for both .NET and Python implementations."

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | 9.3k |
| Forks | 1.5k |
| 贡献者 | 125 |
| 最新版本 | dotnet-1.1.0 / Python 1.0.1 (2026-04-11) |
| 提交数 | 1,864 commits |
| 许可证 | MIT |
| 语言 | Python 50.5%, C# 45.3%, TypeScript 3.7% |

### 1.3 定位

| 维度 | 说明 |
|------|------|
| **双语言** | Python + .NET/C# 双实现，API 一致 |
| **图工作流** | 基于数据流的图编排，支持流式、检查点、人在回路 |
| **多 Provider** | Azure OpenAI、OpenAI、Anthropic 等 |
| **可观测** | 内置 OpenTelemetry 分布式追踪 |
| **DevUI** | 交互式开发者 UI |

## 二、核心功能

### 2.1 完整功能矩阵

| 功能 | 说明 |
|------|------|
| **Graph-based Workflows** | 基于数据流的图编排，支持流式、检查点、人在回路、时间旅行 |
| **AF Labs** | 实验性包，包含基准测试、强化学习、研究功能 |
| **DevUI** | 交互式开发者 UI，用于测试和调试工作流 |
| **Python + C#** | 双语言实现，一致 API |
| **Observability** | 内置 OpenTelemetry，分布式追踪、监控、调试 |
| **Multi-Provider** | Azure OpenAI、OpenAI、Anthropic 等，持续添加 |
| **Middleware** | 灵活的中间件系统，请求/响应处理、异常处理、自定义管道 |

### 2.2 与同类框架的差异

| 特性 | 说明 |
|------|------|
| **双语言实现** | Python 和 .NET 双实现，API 完全一致，.NET 生态的 Agent 框架目前较少 |
| **图编排** | 数据流图编排，支持检查点恢复和时间旅行调试 |
| **OpenTelemetry** | 内置分布式追踪，不需要额外接入 |
| **多 LLM** | Azure OpenAI、OpenAI、Anthropic 等 |
| **DevUI** | 可视化调试和测试 |
| **迁移路径** | 官方提供从 Semantic Kernel 和 AutoGen 迁移的指南 |

## 三、快速开始

### 3.1 安装

```bash
# Python
pip install agent-framework

# .NET
dotnet add package Microsoft.Agents.AI
```

### 3.2 基本 Agent - Python

```python
# pip install agent-framework
# 使用 `az login` 进行 Azure CLI 认证

import os
import asyncio
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

async def main():
    # 初始化 Azure Foundry Chat Agent
    agent = Agent(
        client=FoundryChatClient(
            credential=AzureCliCredential(),
            # project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
            # model=os.environ["FOUNDRY_MODEL_DEPLOYMENT_NAME"],
        ),
        name="HaikuBot",
        instructions="You are an upbeat assistant that writes beautifully."
    )
    print(await agent.run("Write a haiku about Microsoft Agent Framework."))

if __name__ == "__main__":
    asyncio.run(main())
```

### 3.3 基本 Agent - .NET

```csharp
// dotnet add package Microsoft.Agents.AI.Foundry
// 使用 `az login` 进行 Azure CLI 认证

using Azure.AI.Projects;
using Azure.Identity;

var endpoint = Environment.GetEnvironmentVariable("AZURE_AI_PROJECT_ENDPOINT") 
    ?? throw new InvalidOperationException("AZURE_AI_PROJECT_ENDPOINT is not set.");
var deploymentName = Environment.GetEnvironmentVariable("AZURE_AI_MODEL_DEPLOYMENT_NAME") ?? "gpt-5.4-mini";

var agent = new AIProjectClient(new Uri(endpoint), new DefaultAzureCredential())
    .AsAIAgent(model: deploymentName, name: "HaikuBot", instructions: "You are an upbeat assistant that writes beautifully.");

Console.WriteLine(await agent.RunAsync("Write a haiku about Microsoft Agent Framework."));
```

### 3.4 使用 OpenAI - .NET

```csharp
// dotnet add package Microsoft.Agents.AI.OpenAI

using OpenAI;

var agent = new OpenAIClient("<your-api-key>")
    .GetResponsesClient()
    .AsAIAgent(model: "gpt-5.4-mini", name: "HaikuBot", instructions: "You are an upbeat assistant that writes beautifully.");

Console.WriteLine(await agent.RunAsync("Write a haiku about Microsoft Agent Framework."));
```

## 四、Python 示例项目

### 4.1 示例列表

| 示例 | 说明 |
|------|------|
| **Getting Started** | 从 Hello World 到托管的渐进教程 |
| **Agent Concepts** | 深度主题（工具、中间件、Provider 等） |
| **Workflows** | 工作流创建和 Agent 集成 |
| **Hosting** | A2A、Azure Functions、Durable Task 托管 |
| **End-to-End** | 完整应用、评估和演示 |

### 4.2 Agent 概念示例

深入学习 Agent 开发的各个方面：

```python
# 工具使用
from agent_framework import Agent

agent = Agent(instructions="You are a helpful assistant.")
result = await agent.run("What's the weather in Tokyo?")
```

### 4.3 Provider 示例

```python
# 多 Provider 支持
from agent_framework import Agent
from agent_framework.providers import OpenAI, AzureOpenAI, Anthropic

# 使用 OpenAI
agent = Agent(provider=OpenAI(api_key="..."))

# 使用 Azure OpenAI
agent = Agent(provider=AzureOpenAI(endpoint="...", key="..."))

# 使用 Anthropic
agent = Agent(provider=Anthropic(api_key="..."))
```

## 五、.NET 示例项目

### 5.1 示例列表

| 示例 | 说明 |
|------|------|
| **Getting Started** | 从 Hello Agent 到托管的渐进教程 |
| **Agent Concepts** | 基础 Agent 创建和工具使用 |
| **Agent Providers** | 不同 Agent Provider 示例 |
| **Workflows** | 高级多 Agent 模式和工作流编排 |
| **Hosting** | A2A、Durable Agents、Durable Workflows |
| **End-to-End** | 完整应用和演示 |

### 5.2 Agent Provider 示例

```csharp
// 使用不同的 Provider
var agent = new OpenAIClient("<api-key>")
    .GetResponsesClient()
    .AsAIAgent(model: "gpt-4", name: "Assistant", instructions: "...");

// 使用 Azure OpenAI
var azureAgent = new AIProjectClient(new Uri(endpoint), new DefaultAzureCredential())
    .AsAIAgent(model: "gpt-4", name: "Assistant", instructions: "...");
```

## 六、图工作流

### 6.1 关键概念

**Graph-based Workflows** 是框架的核心特性，允许连接 Agent 和确定性函数，使用数据流进行编排。

| 特性 | 说明 |
|------|------|
| **Streaming** | 流式输出，实时反馈 |
| **Checkpointing** | 检查点保存，恢复执行 |
| **Human-in-the-loop** | 人在回路，关键决策人工介入 |
| **Time-travel** | 时间旅行，回溯调试 |

### 6.2 工作流示例

```python
# Python 工作流
from agent_framework.workflows import Workflow, AgentNode, FunctionNode

workflow = Workflow(name="customer-support")

# 添加 Agent 节点
support_agent = workflow.add_node(
    AgentNode(name="support", instructions="You are a support agent.")
)

# 添加函数节点
classify = workflow.add_node(
    FunctionNode(name="classify", func=classify_ticket)
)

# 定义连接
support_agent.input >> classify.output
classify.output >> support_agent.input

# 执行工作流
result = await workflow.run(ticket)
```

## 七、DevUI

### 7.1 DevUI 是什么

**DevUI** 是框架提供的交互式开发者 UI，用于 Agent 开发、测试和调试工作流。

| 功能 | 说明 |
|------|------|
| **Testing** | 交互式测试 Agent |
| **Debugging** | 可视化调试工作流 |
| **Monitoring** | 实时监控执行状态 |
| **Replay** | 重放历史执行 |

### 7.2 DevUI 使用

```bash
# 安装 DevUI
pip install agent-framework[devui]

# 启动 DevUI
python -m agent_framework.devui
# 访问 http://localhost:8080
```

## 八、可观测性

### 8.1 OpenTelemetry 集成

框架内置 **OpenTelemetry** 支持，可直接进行分布式追踪。

| 功能 | 说明 |
|------|------|
| **Distributed Tracing** | 分布式追踪 |
| **Metrics** | 指标收集 |
| **Logging** | 日志记录 |
| **Correlation** | 关联分析 |

### 8.2 Python 可观测性示例

```python
from agent_framework import Agent
from agent_framework.observability import Tracing

# 启用追踪
with Tracing(service_name="my-agent"):
    agent = Agent(instructions="You are a helpful assistant.")
    result = await agent.run("What's the weather?")
```

### 8.3 .NET 遥测示例

```csharp
// 启用 OpenTelemetry
var agent = new AIProjectClient(new Uri(endpoint), new DefaultAzureCredential())
    .AsAIAgent(model: "gpt-4")
    .WithTracing(serviceName: "my-agent");

var result = await agent.RunAsync("What's the weather?");
```

## 九、中间件

### 9.1 中间件系统

框架提供灵活的**中间件系统**，用于请求/响应处理、异常处理和自定义管道。

| 中间件类型 | 说明 |
|-----------|------|
| **Request/Response** | 请求/响应处理 |
| **Exception** | 异常处理 |
| **Auth** | 认证授权 |
| **Logging** | 日志记录 |
| **Metrics** | 指标收集 |

### 9.2 Python 中间件示例

```python
from agent_framework import Agent, Middleware

class CustomMiddleware(Middleware):
    async def on_request(self, request):
        # 处理请求
        print(f"Request: {request}")
        return request
    
    async def on_response(self, response):
        # 处理响应
        print(f"Response: {response}")
        return response

agent = Agent(
    instructions="You are a helpful assistant.",
    middleware=[CustomMiddleware()]
)
```

### 9.3 .NET 中间件示例

```csharp
// Python: agent.add_middleware(CustomMiddleware())
// .NET: Use代理模式或包装器
agent.Use(async (context, next) =>
{
    Console.WriteLine($"Before: {context.Request}");
    await next(context);
    Console.WriteLine($"After: {context.Response}");
});
```

## 十、多 Provider 支持

### 10.1 支持的 Provider

| Provider | Python | .NET | 说明 |
|----------|---------|-------|------|
| **Azure OpenAI** | ✅ | ✅ | Azure 托管的 OpenAI |
| **OpenAI** | ✅ | ✅ | OpenAI API |
| **Anthropic** | ✅ | ✅ | Claude 系列 |
| **Azure Foundry** | ✅ | ✅ | Microsoft Foundry |
| **更多** | 持续添加 | 持续添加 | - |

### 10.2 Provider 配置

```python
# Python 多 Provider
from agent_framework import Agent
from agent_framework.providers import OpenAI, AzureOpenAI, Anthropic

# OpenAI
agent1 = Agent(provider=OpenAI(api_key="sk-..."))

# Azure OpenAI
agent2 = Agent(provider=AzureOpenAI(
    endpoint="https://xxx.openai.azure.com",
    api_key="..."
))

# Anthropic
agent3 = Agent(provider=Anthropic(api_key="sk-ant-..."))
```

## 十一、AF Labs

### 11.1 AF Labs 是什么

**AF Labs** 是框架的**实验性包**，包含前沿功能：

| 功能 | 说明 |
|------|------|
| **Benchmarking** | 性能基准测试 |
| **Reinforcement Learning** | 强化学习 |
| **Research** | 研究功能 |

### 11.2 Labs 目录

```python
# 安装 Labs
pip install agent-framework[lab]

# 使用实验性功能
from agent_framework.lab import Benchmarking, ReinforcementLearning
```

## 十二、托管选项

### 12.1 托管模式

| 模式 | 说明 |
|------|------|
| **A2A** | Agent-to-Agent 通信协议 |
| **Azure Functions** | 无服务器托管 |
| **Durable Task** | 持久化任务托管 |

### 12.2 Azure Functions 托管

```python
# Python Azure Functions
import azure.functions as func
from agent_framework import Agent

app = func.AsgiFunctionApp()

@app.http_trigger()
async def run_agent(req: func.HttpRequest):
    agent = Agent(instructions="You are a helpful assistant.")
    body = await req.get_json()
    result = await agent.run(body["message"])
    return func.HttpResponse(result)
```

### 12.3 .NET Durable Agents

```csharp
// .NET Durable Agents
var agent = new AIProjectClient(new Uri(endpoint), new DefaultAzureCredential())
    .AsDurableAgent(model: "gpt-4");

var instanceId = await agent.StartAsync();
await agent.WaitAsync();
```

## 十三、故障排除

### 13.1 认证问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 认证错误（Azure） | 未登录 Azure CLI | 运行 `az login` |
| API Key 错误 | Key 错误或缺失 | 验证 Key 正确 |

### 13.2 环境变量

| 变量 | 用于 | 说明 |
|------|------|------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI | Azure OpenAI 资源 URL |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Azure OpenAI | 模型部署名称 |
| `AZURE_AI_PROJECT_ENDPOINT` | Foundry | Foundry 项目端点 |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | Foundry | 模型部署名称 |
| `OPENAI_API_KEY` | OpenAI | OpenAI API Key |

### 13.3 提示

> **提示：** `DefaultAzureCredential` 适合开发，但在生产环境中考虑使用特定凭据（如 `ManagedIdentityCredential`）以避免延迟问题、未预期的凭据探测和潜在安全风险。

## 十四、迁移指南

### 14.1 从 Semantic Kernel 迁移

Microsoft Agent Framework 提供**从 Semantic Kernel 迁移**的官方指南：

| 步骤 | 说明 |
|------|------|
| 1 | 安装 `agent-framework` |
| 2 | 迁移 Agent 定义 |
| 3 | 迁移工具和插件 |
| 4 | 迁移内存和存储 |
| 5 | 测试验证 |

```python
# Semantic Kernel
from semantic_kernel import Kernel

# Microsoft Agent Framework
from agent_framework import Agent
```

### 14.2 从 AutoGen 迁移

同样提供**从 AutoGen 迁移**的官方指南：

| 步骤 | 说明 |
|------|------|
| 1 | 安装 `agent-framework` |
| 2 | 转换 Agent 定义 |
| 3 | 迁移工作流 |
| 4 | 测试验证 |

## 十五、文档资源

### 15.1 完整文档链接

| 资源 | 链接 |
|------|------|
| **官方文档** | https://learn.microsoft.com/en-us/agent-framework/ |
| **快速开始** | https://learn.microsoft.com/agent-framework/tutorials/quick-start |
| **用户指南** | https://learn.microsoft.com/en-us/agent-framework/user-guide/overview |
| **迁移指南** | https://learn.microsoft.com/en-us/agent-framework/migration-guide/ |

### 15.2 社区资源

| 资源 | 链接 |
|------|------|
| **Discord** | https://discord.gg/b5zjErwbQM |
| **Office Hours** | 每周社区会议 |
| **GitHub Issues** | https://github.com/microsoft/agent-framework/issues |

## 十六、实践建议

### 16.1 开发实践建议

1. **使用 ManagedIdentityCredential** 在生产环境
2. **配置 OpenTelemetry** 以便调试和监控
3. **使用 Middleware** 处理横切关注点
4. **利用 DevUI** 进行交互式测试

### 16.2 生产实践建议

1. **使用特定凭据** 而不是 DefaultAzureCredential
2. **配置检查点** 以支持恢复
3. **启用人在回路** 用于关键决策
4. **监控和追踪** 使用 OpenTelemetry

## 十七、总结

Microsoft Agent Framework 与同类框架的区别在于 **Python + .NET 双语言实现 + 图工作流**。如果你的团队已经在 .NET 生态内，这是目前少数提供官方 Agent 框架的选择；Python 侧则需要和 LangGraph、CrewAI 等已有方案做取舍——图编排和内置 OpenTelemetry 是它的优势，社区生态和第三方集成则是短板。

**相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/microsoft/agent-framework |
| 文档 | https://learn.microsoft.com/en-us/agent-framework/ |
| PyPI | https://pypi.org/project/agent-framework/ |
| NuGet | https://www.nuget.org/profiles/MicrosoftAgentFramework |
| Discord | https://discord.gg/b5zjErwbQM |
| 视频介绍 | https://www.youtube.com/watch?v=AAgdMhftj8w |

_本文基于 Microsoft Agent Framework (9.3k Stars)_

## 自测题

1. Microsoft Agent Framework 的「双语言实现」具体指哪两种语言？它和只支持单一语言的 Agent 框架相比，最大价值在哪里？
2. Graph-based Workflows 里的「检查点（Checkpointing）」和「时间旅行（Time-travel）」分别解决什么问题？
3. 框架默认支持哪几类 Provider？如果要用一个 OpenAI 兼容的私有部署，应该走哪条接入路径？
4. OpenTelemetry 在框架里承担什么角色？为什么官方把它做成内置能力而不是可选插件？
5. Middleware 能插在请求/响应链路的哪些位置？举一个用中间件统一处理异常的例子。
6. 从 Semantic Kernel 或 AutoGen 迁移到 Agent Framework，官方迁移指南通常建议按什么顺序推进？

### 参考答案

1. 指 Python 和 .NET/C# 两套实现，API 设计保持一致。最大价值是让已经深度使用 .NET 的团队不用为了上 Agent 而整套切换到 Python 生态，同时 Python 侧也能复用同一套编排心智。
2. 检查点把工作流执行状态落盘，崩溃或人工介入后能从断点恢复，而不是从头重跑；时间旅行让你回到任意历史节点重新执行，便于定位某一步的决策为什么会那样。
3. 默认支持 Azure OpenAI、OpenAI、Anthropic、Azure Foundry 等。私有 OpenAI 兼容部署一般走 `OpenAI` Provider，把 `base_url` 指向你的网关即可（具体参数以官方文档为准）。
4. 它负责分布式追踪、指标和日志，让 Agent 的每一次调用、每一段 Span 都能被观测。做成内置而不是插件，是为了降低接入门槛——不用自己接 exporter 就能拿到端到端链路。
5. 中间件可以挂在请求发出前、响应返回后、异常抛出时。例如统一捕获 `Agent.run` 的异常，记录错误上下文后决定是否重试或熔断，避免散落在业务代码里。
6. 通常是：先装包 → 迁移 Agent 定义 → 迁移工具/插件 → 迁移内存与存储 → 跑测试验证。先让最小闭环跑通，再逐步搬重逻辑。

## 练习

1. 用 Python 装好 `agent-framework`，把「基本 Agent」示例换成你自己的 System Prompt，让它能回答你项目里的一个真实问题，并确认流式输出可用。
2. 把上一题的 Agent 包成一个 Graph Workflow：先接一个 `FunctionNode` 做意图分类，再按分类结果路由到不同的 `AgentNode`，最后汇总输出。
3. 给工作流加一个检查点，故意在中间节点抛错，验证能否从检查点恢复而不是整条重跑。
4. 用 OpenTelemetry 给 Agent 打开追踪，把 trace 导出到一个你能看到的后端（如本地 Jaeger 或 Grafana Tempo），确认一次调用能完整展开成 Span 树。
5. 写一个中间件，统计每次 `run` 的 Token 消耗和耗时，把结果打到日志里，作为后续做成本告警的基础。

## 进阶路径

- **深入图编排**：读 `packages/shared` 里 Workflow 的调度与检查点实现，理解数据流节点如何被并发调度，以及人在回路节点如何阻塞等待。
- **可观测性落地**：把 OpenTelemetry trace 接到你们现有的 APM，建立「单次对话 → 各 Span → Token/延迟」的下钻看板，而不只是本地 DevUI 看一眼。
- **生产化托管**：从本地 `python -m agent_framework.devui` 走向 Azure Functions / Durable Task / A2A，重点解决凭据、横向扩展和持久化。
- **迁移与评估**：如果你已经有 Semantic Kernel 或 AutoGen 资产，按官方迁移指南做渐进切换，并用框架的评估能力对比迁移前后的行为差异。

## 常见问题 FAQ

**Q1：Azure 认证一直报 401，怎么办？**
先确认跑过 `az login` 且账号对该 Foundry 项目有贡献者权限；开发期可以用 `DefaultAzureCredential`，但生产环境建议换成 `ManagedIdentityCredential` 避免凭据探测带来的延迟和安全风险。

**Q2：Python 和 .NET 的能力是完全对等的吗？**
API 设计保持一致，但两个生态的成熟度不完全同步，某些实验性能力可能某一侧先有。落地前以官方文档的版本说明为准，别假设一侧的示例能直接翻译成另一侧。

**Q3：Graph Workflow 和普通 Agent 链式调用有什么区别？**
普通链式调用是线性的；Graph Workflow 是数据流图，节点之间用端口连接，支持分支、汇聚、检查点和人在回路，更适合多 Agent 协作和长流程。

**Q4：OpenTelemetry 数据量太大，成本扛不住怎么办？**
利用框架的采样能力，对低价值调用做概率或成本感知采样，只对重要用户和生产错误强制全采。具体采样策略在可观测性章节已有说明。

**Q5：能不能不用 DevUI，直接用代码调试？**
可以。DevUI 只是交互式辅助，真正的能力（追踪、检查点、重放）都通过 SDK 暴露，你完全可以在单测或脚本里触发和断言。

**Q6：从 AutoGen 迁过来，工作流要重写吗？**
不需要整体重写。官方迁移指南建议先迁 Agent 定义，再迁工作流，最后做测试验证；已有的工具函数可以保留，主要改的是编排层的表达。
