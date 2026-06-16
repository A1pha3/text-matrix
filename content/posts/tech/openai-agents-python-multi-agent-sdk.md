---
title: "OpenAI Agents SDK：官方多智能体工作流框架——21K Stars的生产级多Agent架构指南"
date: "2026-04-17T16:30:00+08:00"
slug: "openai-agents-python-multi-agent-sdk"
description: "21,475 Stars的OpenAI官方多智能体SDK。支持OpenAI Responses/Chats API及100+第三方LLM，提供Agent/SandboxAgent/Tool/Guardrail/Handoff/Human-in-the-loop等完整生态，Python 3.10+可用。"
draft: false
categories: ["技术笔记"]
tags: ["OpenAI", "多智能体", "Agent", "SDK", "Python", "工作流", "Guardrails", "MCP"]
---

# OpenAI Agents SDK：官方多智能体工作流框架

OpenAI Agents SDK 真正解决的问题不是"调用模型"，而是把多个 LLM 调用组织成一条可观测、可校验、可交接的流水线。它把 Agent、工具、安全检查、人工介入和会话管理打包成同一套编程模型，目标读者是已经在用 LLM API，但发现单 Agent 架构在复杂任务中不够用的开发者。

> **前置知识**：Python 基础、LLM API 使用经验、对 Agent 概念有基本了解
> **技术栈**：Python 3.10+ / OpenAI Responses API / MCP / Pydantic v2

---

## §1 阅读地图

读完这篇文章，你会对以下问题形成判断——重点在 SDK 的设计取舍，不在 API 签名：

1. OpenAI Agents SDK 和 LangChain / LangGraph 的定位差异
2. Agent、Handoff、Tool 三者的协作关系与各自边界
3. Sandbox Agent 在什么场景下比普通 Agent 更合适
4. Guardrails 的拦截时机（输入前 / 输出后）和失败后的行为
5. Human-in-the-loop 的触发条件设计与动态介入
6. 用 Tracing 定位 Agent 行为异常的实际步骤

---

## §2 背景与动机：为何需要多 Agent 框架

### 2.1 单 Agent 的局限性

当前单 Agent 方案的问题：

| 问题 | 描述 | 影响 |
|------|------|------|
| **能力边界模糊** | 一个 Agent 试图完成所有任务 | 决策质量不稳定 |
| **工具膨胀** | 所有工具堆在一个 Agent | 调用混乱、权限难控 |
| **缺乏协作** | Agent 间无法有效分工 | 无法处理复杂流程 |
| **安全风险** | 无内容过滤机制 | 可能输出有害内容 |

### 2.2 多 Agent 协作的优势

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

多 Agent 架构的核心思路简单：把一个 Agent 的职责拆散，让每个子 Agent 只做一件事，之间通过明确的交接协议协作。这带来三个直接收益：每个 Agent 的指令更短、上下文更干净、出错的爆炸半径更小。同时，Guardrails 在交接边界上做安全检查，Tracing 让每一步都有据可查。

### 2.3 SDK 定位与机制边界

OpenAI Agents SDK 是一个面向多 Agent 协作的 Python 框架，它的设计重心不在链式调用，而在交接与安全：

| 特性 | 说明 |
|------|------|
| **Provider Agnostic** | 支持 OpenAI API 及 100+ 第三方 LLM |
| **类型安全** | 完整 Pydantic v2 集成 |
| **内置能力** | Sandbox / Tracing / Handoff / Guardrails 全部内置 |
| **生产验证** | 已用于 OpenAI 内部多个生产级 Agent 系统 |

SDK 内部存在几套容易混淆的并行机制，先明确它们的边界：

| 机制 | 作用 | 触发方式 | 典型场景 |
|------|------|----------|----------|
| `tools=[agent]` (Agent as Tool) | 把子 Agent 当工具调用，父 Agent 拿到返回值后继续 | 模型自主决定调用 | 代码生成 → 代码审查（子 Agent 只出结果，不接管会话） |
| `handoffs=[agent]` | 把会话控制权完整交给另一个 Agent | 父 Agent 指令触发 `handoff_to()` | 路由分发、多轮子任务 |
| `handoff(agent, context=...)` | 带上下文交接，传递优先级/部门等元信息 | 通过 `handoff()` 包装 | 带紧急标记的任务路由 |
| 条件 Handoff | 在运行时根据输入动态选择目标 Agent | 自定义函数返回值 | 按用户意图动态分发 |

---

## §3 核心概念：Agent 体系

### 3.1 Agent 的定义

Agent 是 LLM + 指令 + 工具 + 安全配置的组合：

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

### 3.2 Agent 的核心组件

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

### 3.3 内置 Agent 类型

**普通 Agent**：基于 LLM 的对话 Agent
```python
agent = Agent(name="Assistant", instructions="You are helpful.")
```

**Sandbox Agent**：隔离环境执行的 Agent（v0.14.0+）
```python
from agents.sandbox import SandboxAgent, Manifest, GitRepo

sandbox_agent = SandboxAgent(
    name="Code Assistant",
    instructions="Inspect files and run commands in the sandbox.",
    default_manifest=Manifest(entries={"repo": GitRepo(repo="owner/repo", ref="main")}),
)
```

**Realtime Agent**：语音交互 Agent
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

定义 Python 函数作为 Agent 工具：

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

连接外部 MCP 服务器的工具：

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

Agent 本身也可以作为工具被其他 Agent 调用：

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

## §5 Handoff：Agent 间协作

### 5.1 Handoff 机制

Handoff 是 Agent 之间的"交接棒"机制：

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

### 5.2 带上下文的 Handoff

Handoff 可以传递上下文信息：

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

### 5.3 条件 Handoff

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

### 6.1 Guardrail 的概念

Guardrails 在输入和输出阶段进行安全校验：

```
用户输入 → [Input Guardrail] → Agent处理 → [Output Guardrail] → 用户输出
                   │                                    │
                   ▼                                    ▼
             验证/过滤/拒绝                        验证/过滤/拒绝
```

### 6.2 内置 Guardrails

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

### 6.3 自定义 Guardrail

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

### 8.1 Sandbox Agent 概述

Sandbox Agent 在隔离环境中执行任务，适合需要文件系统访问、命令执行的场景：

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

### 8.2 Manifest 配置

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

### 8.3 Sandbox 类型

| Sandbox 类型 | 说明 | 适用场景 |
|-------------|------|----------|
| UnixLocalSandboxClient | 本地 Unix 环境 | 开发/测试 |
| DockerSandboxClient | Docker 容器 | 生产隔离 |
| E2BSandboxClient | 云端沙箱 | 付费托管 |

---

## §9 Tracing：可观测性

### 9.1 内置 Tracing

OpenAI Agents SDK 内置 Tracing，无需额外配置：

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

SDK 自动将追踪数据发送到 OpenAI 的 Tracing 服务，可在 UI 中查看：
- Agent 调用链
- 工具执行时间
- Token 消耗
- 中间输出

### 9.3 自定义 Span

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

### 10.2 Redis 会话存储（可选）

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

## §11 完整示例：多 Agent 协作

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

### 11.2 带 Guardrail 和 Tracing 的完整配置

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
- OpenAI API Key（或第三方 LLM API Key）

### 12.2 安装

```bash
# 标准安装
pip install openai-agents

# 带语音支持
pip install 'openai-agents[voice]'

# 带Redis会话支持
pip install 'openai-agents[redis]'
```

### 12.3 与 LangChain/LangGraph 对比

| 特性 | OpenAI Agents SDK | LangChain | LangGraph |
|------|------------------|-----------|-----------|
| **定位** | 多 Agent 协作框架 | LLM 应用框架 | 图编排框架 |
| **学习曲线** | 低 | 中 | 高 |
| **Guardrails** | 内置 | 需第三方 | 需第三方 |
| **Sandbox** | 内置 | 无 | 无 |
| **Tracing** | 内置 | LangSmith（付费） | LangSmith（付费） |
| **Provider** | OpenAI 官方 | 社区驱动 | 社区驱动 |

---

## §13 FAQ

**Q1：OpenAI Agents SDK 只能用于 OpenAI 模型吗？**
A：不限于 OpenAI。它是 provider-agnostic 的，支持 OpenAI、Azure、Anthropic 及 100+ 第三方 LLM。

**Q2：Sandbox Agent 安全吗？**
A：Sandbox Agent 在隔离环境中执行文件操作和命令，默认只读本地 Git 仓库。生产环境建议使用 Docker 或云端沙箱。

**Q3：Guardrails 会影响性能吗？**
A：会有轻微延迟（通常 <100ms），但相比无防护时因有害输出导致的回滚成本，这点开销是合理的。

**Q4：如何调试 Agent 行为？**
A：使用内置 Tracing，可以查看每个 Agent 调用、工具执行、Token 消耗的详细信息。

**Q5：支持语音 Agent 吗？**
A：支持。使用 Realtime Agent 配合 `gpt-realtime-1.5` 模型即可构建语音交互 Agent。

---

## 采用顺序与适用边界

**建议先上的团队**：已经在用 OpenAI 生态、需要将单 Agent 拆分为多 Agent 协作的团队；当前工作流中有明确的角色分工（如代码生成 → 审查 → 测试），但缺乏系统化交接机制的团队。

**可以先观望的情况**：团队已深度绑定了 LangGraph 的图编排模式，并且需要更细粒度的状态管理；或者工作流仍以单 Agent + 工具调用为主、暂时不需要多 Agent 交接的场景。

**起步建议**：从 Agent + handoffs 的最小组合开始，先不引入 Sandbox 和 Human-in-the-loop；跑通一条两 Agent 交接链路后，再加入 Guardrails 和 Tracing。

## 相关资源

- **GitHub 仓库**：https://github.com/openai/openai-agents-python
- **官方文档**：https://openai.github.io/openai-agents-python/
- **JavaScript 版本**：https://github.com/openai/openai-agents-js
- **示例代码**：https://github.com/openai/openai-agents-python/tree/main/examples
