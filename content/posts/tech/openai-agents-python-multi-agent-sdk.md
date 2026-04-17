---
title: "OpenAI Agents SDK：官方多智能体工作流框架——21K Stars的生产级多Agent架构指南"
date: 2026-04-17T16:30:00+08:00
slug: "openai-agents-python-multi-agent-sdk"
description: "21,475 Stars的OpenAI官方多智能体SDK。支持OpenAI Responses/Chats API及100+第三方LLM，提供Agent/SandboxAgent/Tool/Guardrail/Handoff/Human-in-the-loop等完整生态，Python 3.10+可用。"
draft: false
categories: ["技术笔记"]
tags: ["OpenAI", "多智能体", "Agent", "SDK", "Python", "工作流", "Guardrails", "MCP"]
---

# OpenAI Agents SDK：官方多智能体工作流框架

> **目标读者**：LLM应用开发者、AI Agent研究者、企业级AI工作流架构师
> **前置知识**：Python基础、LLM API使用经验、对Agent概念有基本了解
> **技术栈**：Python 3.10+ / OpenAI Responses API / MCP / Pydantic v2
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解OpenAI Agents SDK的核心定位**：与LangChain/LangGraph的区别与优势
2. **掌握Agent、Handoff、Tool三大核心概念**：构建多Agent协作的原子单元
3. **理解Sandbox Agent的隔离执行机制**：如何在安全环境中执行长时任务
4. **掌握Guardrails配置**：实现输入输出的安全校验与内容过滤
5. **理解Human-in-the-loop模式**：如何在自动化流程中引入人工介入
6. **能够构建生产级多Agent工作流**：使用Tracing监控和调试Agent行为

---

## §2 背景与动机：为何需要多Agent框架

### 2.1 单Agent的局限性

当前单Agent方案的问题：

| 问题 | 描述 | 影响 |
|------|------|------|
| **能力边界模糊** | 一个Agent试图完成所有任务 | 决策质量不稳定 |
| **工具膨胀** | 所有工具堆在一个Agent | 调用混乱、权限难控 |
| **缺乏协作** | Agent间无法有效分工 | 无法处理复杂流程 |
| **安全风险** | 无内容过滤机制 | 可能输出有害内容 |

### 2.2 多Agent协作的优势

```
用户请求
    │
    ▼
┌─────────────┐    Handoff    ┌─────────────┐
│  Router     │ ───────────→ │  Coder      │
│  Agent      │               │  Agent      │
└─────────────┘               └─────────────┘
       │                              │
       │ Handoff                      │ Handoff
       ▼                              ▼
┌─────────────┐               ┌─────────────┐
│  Reviewer   │ ←───────────  │  Tester     │
│  Agent      │   Guardrail   │  Agent      │
└─────────────┘               └─────────────┘
```

**核心优势**：
- **角色分离**：每个Agent专注单一职责
- **可编排**：通过Handoff构建复杂工作流
- **可观测**：内置Tracing追踪每个步骤
- **更安全**：Guardrails进行输入输出校验

### 2.3 OpenAI Agents SDK的定位

OpenAI Agents SDK是一个**轻量级但功能强大**的多Agent框架：

| 特性 | 说明 |
|------|------|
| **Provider Agnostic** | 支持OpenAI API + 100+第三方LLM |
| **类型安全** | 完整Pydantic v2集成 |
| **开箱即用** | 内置Sandbox/Tracing/Handoff |
| **生产可用** | 已在OpenAI内部生产验证 |

---

## §3 核心概念：Agent体系

### 3.1 Agent的定义

Agent是LLM + 指令 + 工具 + 安全配置的组合：

```python
from agents import Agent

agent = Agent(
    name="Research Assistant",      # Agent名称
    instructions="""                # 系统指令
        You are a research assistant.
        You excel at finding accurate information
        and citing your sources.
    """,
    tools=[search_web, read_file],  # 可用工具列表
    model="gpt-4o",                 # 指定模型（可选）
)
```

### 3.2 Agent的核心组件

```python
Agent(
    # 身份与指令
    name: str,                      # Agent名称（唯一标识）
    instructions: str | Callable,   # 系统提示词（静态或动态生成）
    
    # 模型配置
    model: str | Model = "gpt-4o", # 模型选择
    model_provider: str = "openai", # 模型提供商
    
    # 工具系统
    tools: list[Tool] = [],         # 可用工具列表
    tool_classes: list[type] = [],  # 工具类（自动实例化）
    
    # 安全与控制
    guardrails: list[Guardrail] = [],  # 输入输出安全校验
    handoffs: list[Agent] = [],         # 可转交的Agent列表
    
    # 记忆与会话
    session_recency_config = None,   # 记忆配置
    max_tokens = None,              # 输出token限制
)
```

### 3.3 内置Agent类型

**普通Agent**：基于LLM的对话Agent
```python
agent = Agent(name="Assistant", instructions="You are helpful.")
```

**Sandbox Agent**：隔离环境执行的Agent（v0.14.0+）
```python
from agents.sandbox import SandboxAgent, Manifest, GitRepo

sandbox_agent = SandboxAgent(
    name="Code Assistant",
    instructions="Inspect files and run commands in the sandbox.",
    default_manifest=Manifest(entries={"repo": GitRepo(repo="owner/repo", ref="main")}),
)
```

**Realtime Agent**：语音交互Agent
```python
from agents.realtime import RealtimeAgent

voice_agent = RealtimeAgent(
    name="Voice Assistant",
    instructions="You are a helpful voice assistant.",
    model="gpt-realtime-1.5",
)
```

---

## §4 工具系统：Function Calling + MCP

### 4.1 Function Tool

定义Python函数作为Agent工具：

```python
from agents import Agent, function_tool

@function_tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # 实现搜索逻辑
    return f"Results for: {query}"

@function_tool
def calculate(expression: str) -> float:
    """Evaluate a math expression."""
    return eval(expression)

agent = Agent(
    name="Assistant",
    instructions="You can use tools to help answer questions.",
    tools=[search_web, calculate],
)
```

### 4.2 MCP (Model Context Protocol) Tool

连接外部MCP服务器的工具：

```python
from agents import Agent
from agents.tools.mcp import MCPTool

# 连接MCP服务器
mcp_tool = MCPTool(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"],
)

agent = Agent(
    name="File Assistant",
    instructions="You can read and write files.",
    tools=[mcp_tool],
)
```

### 4.3 Agents as Tools

Agent本身也可以作为工具被其他Agent调用：

```python
# 定义子Agent
coder = Agent(
    name="Coder",
    instructions="You write Python code.",
    tools=[...],
)

reviewer = Agent(
    name="Reviewer", 
    instructions="You review code for bugs.",
)

# 父Agent可以使用子Agent
parent_agent = Agent(
    name="Team Lead",
    instructions="Coordinate a coding team.",
    tools=[coder, reviewer],  # Agent作为工具
    handoffs=[coder, reviewer],
)
```

---

## §5 Handoff：Agent间协作

### 5.1 Handoff机制

Handoff是Agent之间的"交接棒"机制：

```python
# Agent A
agent_a = Agent(
    name="Router",
    instructions="Classify the user's intent and hand off to the right agent.",
    handoffs=[coder_agent, writer_agent, analyst_agent],
)

# Agent B
coder_agent = Agent(
    name="Coder",
    instructions="You write code.",
)

# 从Agent A交接给Agent B
# 在Agent A的指令中触发：handoff_to(coder_agent)
```

### 5.2 带上下文的Handoff

Handoff可以传递上下文信息：

```python
from agents import Agent, RunContextWrapper, handoff

# 带配置的Handoff
handoff_to_analyst = handoff(
    agent=analyst_agent,
    # 传递额外上下文
    context={
        "priority": "high",
        "department": "engineering",
    },
)

router = Agent(
    name="Router",
    instructions="Route to analyst with priority context.",
    handoffs=[handoff_to_analyst],
)
```

### 5.3 条件Handoff

```python
async def route_to_specialist(context: RunContextWrapper) -> Agent:
    """根据用户输入决定转交给哪个Agent"""
    user_input = context.messages[-1].content.lower()
    
    if "code" in user_input or "debug" in user_input:
        return coder_agent
    elif "write" in user_input or "article" in user_input:
        return writer_agent
    else:
        return general_agent

agent = Agent(
    name="Router",
    instructions="Route to the appropriate specialist.",
    handoffs=[coder_agent, writer_agent, general_agent],
    handoff_condition=route_to_specialist,
)
```

---

## §6 Guardrails：安全校验

### 6.1 Guardrail的概念

Guardrails在输入和输出阶段进行安全校验：

```
用户输入 → [Input Guardrail] → Agent处理 → [Output Guardrail] → 用户输出
                   │                                    │
                   ▼                                    ▼
             验证/过滤/拒绝                        验证/过滤/拒绝
```

### 6.2 内置Guardrails

```python
from agents.guardrails import (
    PIIGuardrail,      # 个人身份信息检测
    ToxicityGuardrail, # 有害内容检测
    RelevanceGuardrail, # 相关性检测
)

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    guardrails=[
        PIIGuardrail(),        # 拒绝包含PII的输入
        ToxicityGuardrail(),   # 拒绝有害输出
        RelevanceGuardrail(threshold=0.3),  # 拒绝不相关输入
    ],
)
```

### 6.3 自定义Guardrail

```python
from agents.guardrails import InputGuardrail, OutputGuardrail, GuardrailFunctionOutput

class CustomInputGuardrail(InputGuardrail):
    name = "custom_input_guardrail"
    
    async def check(self, context: RunContextWrapper) -> GuardrailFunctionOutput:
        user_input = context.messages[-1].content
        
        # 自定义检查逻辑
        if contains_profanity(user_input):
            return GuardrailFunctionOutput(
                tripwire_triggered=True,
                message="Please use appropriate language.",
            )
        
        return GuardrailFunctionOutput(tripwire_triggered=False)

agent = Agent(
    name="Assistant",
    guardrails=[CustomInputGuardrail()],
)
```

---

## §7 Human-in-the-Loop：人工介入

### 7.1 介入模式

```python
from agents import Agent
from agents.human_in_the_loop import Approval, Form

# 方式1：Approval（简单批准）
agent = Agent(
    name="Assistant",
    instructions="Ask for approval before executing dangerous actions.",
    human_in_the_loop=[
        Approval(prompt="Approve this action?", tools=["delete_file"]),
    ],
)

# 方式2：Form（结构化输入）
human_feedback_form = Form(
    name="feedback",
    description="Get feedback from human",
    fields=[
        {"name": "approved", "type": "boolean", "description": "Is this correct?"},
        {"name": "correction", "type": "string", "description": "What should be changed?"},
    ],
)

agent = Agent(
    name="Assistant",
    human_in_the_loop=[human_feedback_form],
)
```

### 7.2 动态介入

```python
from agents import Agent, RunConfig

# 根据条件决定是否介入
run_config = RunConfig(
    human_in_the_loop=[
        Approval(
            prompt="Confirm deployment?",
            tools=["deploy_to_production"],
            condition=lambda ctx: "production" in ctx.messages[-1].content,
        ),
    ],
)
```

---

## §8 Sandbox Agent：隔离执行

### 8.1 Sandbox Agent概述

Sandbox Agent在隔离环境中执行任务，适合需要文件系统访问、命令执行的场景：

```python
from agents import Runner
from agents.run import RunConfig
from agents.sandbox import Manifest, SandboxAgent, SandboxRunConfig
from agents.sandbox.entries import GitRepo, LocalFiles

agent = SandboxAgent(
    name="Workspace Assistant",
    instructions="Inspect the workspace before answering.",
    default_manifest=Manifest(
        entries={
            "repo": GitRepo(repo="openai/openai-agents-python", ref="main"),
            "local": LocalFiles(path="/path/to/project"),
        }
    ),
)

result = Runner.run_sync(
    agent,
    "What files were modified in the last commit?",
    run_config=RunConfig(
        sandbox=SandboxRunConfig(
            client=UnixLocalSandboxClient(),  # 本地隔离环境
        )
    ),
)
```

### 8.2 Manifest配置

```python
from agents.sandbox import Manifest
from agents.sandbox.entries import GitRepo, URL, LocalFiles

manifest = Manifest(
    entries={
        "repo": GitRepo(
            repo="owner/repo",
            ref="main",
            include=["*.py", "*.md"],  # 只同步特定文件
        ),
        "docs": URL(url="https://docs.example.com"),
        "local": LocalFiles(path="/path/to/data"),
    }
)
```

### 8.3 Sandbox类型

| Sandbox类型 | 说明 | 适用场景 |
|-------------|------|----------|
| UnixLocalSandboxClient | 本地Unix环境 | 开发/测试 |
| DockerSandboxClient | Docker容器 | 生产隔离 |
| E2BSandboxClient | 云端沙箱 | 付费托管 |

---

## §9 Tracing：可观测性

### 9.1 内置Tracing

OpenAI Agents SDK内置Tracing，无需额外配置：

```python
from agents import Agent, Runner
from agents.tracing import trace

# 方式1：自动Tracing
agent = Agent(name="Assistant", instructions="You are helpful.")
result = await Runner.run(agent, "Hello!")

# 方式2：手动Tracing
with trace("My Agent Workflow"):
    result = await Runner.run(agent, input)
```

### 9.2 Tracing UI

SDK自动将追踪数据发送到OpenAI的Tracing服务，可在UI中查看：
- Agent调用链
- 工具执行时间
- Token消耗
- 中间输出

### 9.3 自定义Span

```python
from agents.tracing import trace, Span

with trace("Custom Workflow") as span:
    span.set_attribute("user_id", user_id)
    
    with trace("Step 1"):
        result1 = await step1()
    
    with trace("Step 2"):
        result2 = await step2(result1)
    
    span.set_status("success")
```

---

## §10 Sessions：会话管理

### 10.1 自动会话管理

```python
from agents import Agent, Runner
from agents.sessions import Session

# 自动创建和管理会话
session = await Session.create()

agent = Agent(name="Assistant", instructions="You are helpful.")

# 第一次对话
result1 = await Runner.run(agent, "My name is Alice.", session_id=session.id)

# 第二次对话（自动包含历史）
result2 = await Runner.run(agent, "What's my name?", session_id=session.id)
# → "Your name is Alice."
```

### 10.2 Redis会话存储（可选）

```bash
pip install 'openai-agents[redis]'
```

```python
from agents.sessions import RedisSessionManager

session_manager = RedisSessionManager(
    redis_url="redis://localhost:6379",
)

session = await Session.create(
    session_manager=session_manager,
    user_id="user_123",
)
```

---

## §11 完整示例：多Agent协作

### 11.1 案例：代码审查团队

```python
from agents import Agent, Runner, RunConfig, handoff

# 定义三个专业Agent
coder = Agent(
    name="Coder",
    instructions="You write clean, efficient Python code.",
)

reviewer = Agent(
    name="Reviewer",
    instructions="You review code for bugs, security issues, and style problems.",
)

tester = Agent(
    name="Tester",
    instructions="You write comprehensive tests for the code.",
    handoffs=[reviewer],  # 测试失败转回审查
)

# 协调Agent
coordinator = Agent(
    name="Coordinator",
    instructions="""You coordinate a code review team.
    1. First, hand off to Coder to write the code
    2. Then hand off to Reviewer to review it
    3. If there are issues, the Reviewer will send it back to Coder
    4. Once approved, hand off to Tester to write tests
    5. If tests fail, Tester sends back to Reviewer""",
    handoffs=[
        handoff(agent=coder),
        handoff(agent=reviewer),
        handoff(agent=tester),
    ],
)

# 执行工作流
result = await Runner.run(coordinator, "Write a function to calculate fibonacci numbers.")
```

### 11.2 带Guardrail和Tracing的完整配置

```python
from agents import Agent, Runner, RunConfig
from agents.guardrails import PIIGuardrail, ToxicityGuardrail

config = RunConfig(
    tracing_export_endpoint="https://api.openai.com/tracing",  # 可选
    human_in_the_loop=[Approval(prompt="Proceed?", tools=["delete_data"])],
)

agent = Agent(
    name="Safe Assistant",
    instructions="You are a helpful assistant.",
    guardrails=[
        PIIGuardrail(),
        ToxicityGuardrail(),
    ],
)

result = await Runner.run(agent, "Hello!", run_config=config)
```

---

## §12 部署与生产

### 12.1 环境要求

- Python 3.10+
- OpenAI API Key（或第三方LLM API Key）

### 12.2 安装

```bash
# 标准安装
pip install openai-agents

# 带语音支持
pip install 'openai-agents[voice]'

# 带Redis会话支持
pip install 'openai-agents[redis]'
```

### 12.3 与LangChain/LangGraph对比

| 特性 | OpenAI Agents SDK | LangChain | LangGraph |
|------|------------------|-----------|-----------|
| **定位** | 多Agent协作框架 | LLM应用框架 | 图编排框架 |
| **学习曲线** | 低 | 中 | 高 |
| **Guardrails** | 内置 | 需第三方 | 需第三方 |
| **Sandbox** | 内置 | 无 | 无 |
| **Tracing** | 内置 | LangSmith（付费） | LangSmith（付费） |
| **Provider** | OpenAI官方 | 社区驱动 | 社区驱动 |

---

## §13 FAQ

**Q1：OpenAI Agents SDK只能用于OpenAI模型吗？**
A：不是。它是provider-agnostic的，支持OpenAI、Azure、Anthropic以及100+第三方LLM。

**Q2：Sandbox Agent安全吗？**
A：Sandbox Agent在隔离环境中执行文件操作和命令，默认只读本地Git仓库。生产环境建议使用Docker或云端沙箱。

**Q3：Guardrails会影响性能吗？**
A：会有轻微延迟（通常<100ms），但提供了重要的安全保障，值得。

**Q4：如何调试Agent行为？**
A：使用内置Tracing，可以查看每个Agent调用、工具执行、Token消耗的详细信息。

**Q5：支持语音Agent吗？**
A：是的，使用Realtime Agent和`gpt-realtime-1.5`模型，可以构建语音交互Agent。

---

## 相关资源

- **GitHub仓库**：https://github.com/openai/openai-agents-python
- **官方文档**：https://openai.github.io/openai-agents-python/
- **JavaScript版本**：https://github.com/openai/openai-agents-js
- **示例代码**：https://github.com/openai/openai-agents-python/tree/main/examples
