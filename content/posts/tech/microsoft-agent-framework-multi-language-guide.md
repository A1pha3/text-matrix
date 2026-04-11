# Microsoft Agent Framework：微软官方·双语言支持·图工作流·多 Provider 支持完全指南

## 一、项目概述

### 1.1 Microsoft Agent Framework 是什么

**Microsoft Agent Framework** 是微软官方的**多语言 Agent 框架**，用于构建、编排和部署 AI Agent，支持 **Python** 和 **.NET/C#** 双语言实现。从简单的聊天 Agent 到复杂的多 Agent 工作流，提供图编排能力。

> "Welcome to Microsoft's comprehensive multi-language framework for building, orchestrating, and deploying AI agents with support for both .NET and Python implementations."

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | 9.3k ⭐ |
| Forks | 1.5k |
| 贡献者 | 125 |
| 最新版本 | dotnet-1.1.0 / Python 1.0.1 (2026-04-11) |
| 提交数 | 1,864 commits |
| 许可证 | MIT |
| 语言 | Python 50.5%, C# 45.3%, TypeScript 3.7% |

### 1.3 核心定位

| 维度 | 说明 |
|------|------|
| 🤖 **微软官方** | Microsoft 官方维护的 Agent 框架 |
| 🌐 **双语言** | Python + .NET/C# 双实现，API 一致 |
| 🔄 **图工作流** | 基于数据流的图编排，支持流式、检点、人在回路 |
| 🔌 **多 Provider** | 支持多种 LLM 提供商 |
| 📊 **可观测** | 内置 OpenTelemetry 分布式追踪 |
| 🛠️ **DevUI** | 交互式开发者 UI |

---

## 二、核心功能

### 2.1 完整功能矩阵

| 功能 | 说明 |
|------|------|
| 🤖 **Graph-based Workflows** | 基于数据流的图编排，支持流式、检点、人在回路、时间旅行 |
| 🧪 **AF Labs** | 实验性包，包含基准测试、强化学习、研究功能 |
| 🖥️ **DevUI** | 交互式开发者 UI，用于测试和调试工作流 |
| 🐍 **Python + C#** | 双语言实现，一致 API |
| 📊 **Observability** | 内置 OpenTelemetry，分布式追踪、监控、调试 |
| 🔌 **Multi-Provider** | 支持多种 LLM 提供商，持续添加 |
| ⚙️ **Middleware** | 灵活的中间件系统，请求/响应处理、异常处理、自定义管道 |

### 2.2 为什么选择 Microsoft Agent Framework

| 特性 | 说明 |
|------|------|
| 🏢 **微软官方** | Microsoft 官方维护，企业级支持 |
| 🌐 **双语言支持** | Python 和 .NET 双实现，API 完全一致 |
| 🔄 **图编排** | 强大的工作流编排，复杂业务逻辑轻松实现 |
| 📊 **OpenTelemetry** | 开箱即用的可观测性，分布式追踪 |
| 🔌 **多 LLM** | Azure OpenAI、OpenAI、Anthropic 等多提供商 |
| 🖥️ **DevUI** | 可视化调试和测试，提升开发效率 |
| 📚 **丰富文档** | 官方文档、迁移指南、示例代码 |

---

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

---

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

---

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

---

## 六、图工作流（Graph-based Workflows）

### 6.1 核心概念

**Graph-based Workflows** 是 Microsoft Agent Framework 的核心特性，允许连接 Agent 和确定性函数，使用数据流进行编排。

| 特性 | 说明 |
|------|------|
| 📝 **Streaming** | 流式输出，实时反馈 |
| 🔍 **Checkpointing** | 检点保存，恢复执行 |
| 👤 **Human-in-the-loop** | 人在回路，关键决策人工介入 |
| ⏪ **Time-travel** | 时间旅行，回溯调试 |

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

---

## 七、DevUI - 交互式开发者 UI

### 7.1 DevUI 是什么

**DevUI** 是 Microsoft Agent Framework 提供的**交互式开发者 UI**，用于 Agent 开发、测试和调试工作流。

| 功能 | 说明 |
|------|------|
| 🧪 **Testing** | 交互式测试 Agent |
| 🔍 **Debugging** | 可视化调试工作流 |
| 📊 **Monitoring** | 实时监控执行状态 |
| 🔄 **Replay** | 重放历史执行 |

### 7.2 DevUI 使用

```bash
# 安装 DevUI
pip install agent-framework[devui]

# 启动 DevUI
python -m agent_framework.devui
# 访问 http://localhost:8080
```

---

## 八、可观测性（Observability）

### 8.1 OpenTelemetry 集成

Microsoft Agent Framework 内置 **OpenTelemetry** 支持，开箱即用进行分布式追踪。

| 功能 | 说明 |
|------|------|
| 🔍 **Distributed Tracing** | 分布式追踪 |
| 📊 **Metrics** | 指标收集 |
| 📝 **Logging** | 日志记录 |
| 🔗 **Correlation** | 关联分析 |

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

---

## 九、中间件（Middleware）

### 9.1 中间件系统

Microsoft Agent Framework 提供灵活的**中间件系统**，用于请求/响应处理、异常处理和自定义管道。

| 中间件类型 | 说明 |
|-----------|------|
| 🔄 **Request/Response** | 请求/响应处理 |
| ⚠️ **Exception** | 异常处理 |
| 🔒 **Auth** | 认证授权 |
| 📝 **Logging** | 日志记录 |
| 📊 **Metrics** | 指标收集 |

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

---

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

---

## 十一、AF Labs - 实验性功能

### 11.1 AF Labs 是什么

**AF Labs** 是 Microsoft Agent Framework 的**实验性包**，包含前沿功能：

| 功能 | 说明 |
|------|------|
| 📊 **Benchmarking** | 性能基准测试 |
| 🧠 **Reinforcement Learning** | 强化学习 |
| 🔬 **Research** | 研究功能 |

### 11.2 Labs 目录

```python
# 安装 Labs
pip install agent-framework[lab]

# 使用实验性功能
from agent_framework.lab import Benchmarking, ReinforcementLearning
```

---

## 十二、托管选项（Hosting）

### 12.1 托管模式

| 模式 | 说明 |
|------|------|
| 🔄 **A2A** | Agent-to-Agent 通信协议 |
| ⚡ **Azure Functions** | 无服务器托管 |
| 🔧 **Durable Task** | 持久化任务托管 |

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

---

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

> ⚠️ **Tip:** `DefaultAzureCredential` 适合开发，但在生产环境中考虑使用特定凭据（如 `ManagedIdentityCredential`）以避免延迟问题、未预期的凭据探测和潜在安全风险。

---

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

---

## 十五、文档资源

### 15.1 完整文档链接

| 资源 | 链接 |
|------|------|
| 📚 **官方文档** | https://learn.microsoft.com/en-us/agent-framework/ |
| 🚀 **快速开始** | https://learn.microsoft.com/agent-framework/tutorials/quick-start |
| 📖 **用户指南** | https://learn.microsoft.com/en-us/agent-framework/user-guide/overview |
| 🔄 **迁移指南** | https://learn.microsoft.com/en-us/agent-framework/migration-guide/ |

### 15.2 社区资源

| 资源 | 链接 |
|------|------|
| 💬 **Discord** | https://discord.gg/b5zjErwbQM |
| 📅 **Office Hours** | 每周社区会议 |
| 🐛 **GitHub Issues** | https://github.com/microsoft/agent-framework/issues |

---

## 十六、最佳实践

### 16.1 开发最佳实践

1. **使用 ManagedIdentityCredential** 在生产环境
2. **配置 OpenTelemetry** 以便调试和监控
3. **使用 Middleware** 处理横切关注点
4. **利用 DevUI** 进行交互式测试

### 16.2 生产最佳实践

1. **使用特定凭据** 而不是 DefaultAzureCredential
2. **配置检查点** 以支持恢复
3. **启用人在回路** 用于关键决策
4. **监控和追踪** 使用 OpenTelemetry

---

## 十七、总结

Microsoft Agent Framework 是**微软官方的多语言 Agent 开发框架**：

| 维度 | 说明 |
|------|------|
| 🏢 **微软官方** | Microsoft 官方维护，企业级支持 |
| 🌐 **双语言** | Python + .NET 双实现，API 一致 |
| 🔄 **图编排** | 强大的工作流编排能力 |
| 📊 **可观测** | 内置 OpenTelemetry，开箱即用 |
| 🔌 **多 Provider** | Azure、OpenAI、Anthropic 等 |
| 🖥️ **DevUI** | 可视化开发和调试 |
| 📚 **文档完善** | 官方文档 + 迁移指南 + 示例 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/microsoft/agent-framework |
| 文档 | https://learn.microsoft.com/en-us/agent-framework/ |
| PyPI | https://pypi.org/project/agent-framework/ |
| NuGet | https://www.nuget.org/profiles/MicrosoftAgentFramework |
| Discord | https://discord.gg/b5zjErwbQM |
| 视频介绍 | https://www.youtube.com/watch?v=AAgdMhftj8w |

---

_🦞 本文由钳岳星君撰写，基于 Microsoft Agent Framework (9.3k Stars)_
