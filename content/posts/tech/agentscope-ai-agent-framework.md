---
title: "AgentScope：21.4k Stars 生产级 AI Agent 框架"
date: 2026-03-28T21:45:00+08:00
slug: "agentscope-ai-agent-framework"
description: "深度解读 AgentScope：21.4k Stars 的生产级 AI Agent 框架，支持 ReAct/Voice/Realtime Agent、MCP/A2A 协议、模型微调、人机交互、多 Agent 编排。"
draft: false
categories: ["技术笔记"]
tags: ["AgentScope", "AI Agent", "多Agent", "MCP", "模型微调"]
---

# AgentScope：21.4k Stars 生产级 AI Agent 框架

> **目标读者**：构建 AI Agent、多 Agent 系统、Agentic应用的开发者
> **核心问题**：如何快速构建生产级 AI Agent 应用？
> **难度**：⭐⭐⭐⭐（专家设计）
> **来源**：GitHub agentscope-ai/agentscope，2026-03-28

---

## 一、项目概览

### 1.1 为什么这个项目值得关注

[AgentScope](https://github.com/agentscope-ai/agentscope) 是**生产级、易用的 AI Agent 框架**，具备关键抽象设计，配合日益增长的模型能力，内置模型微调支持。

**核心数据：**

| 指标 | 数值 |
|------|------|
| GitHub Stars | **21.4k** |
| Forks | 2.1k |
| 最新版本 | v1.0.18（2026-03-26） |
| License | Apache-2.0 |
| 语言 | Python 100% |

**核心定位：**

> We design for increasingly agentic LLMs. Our approach leverages the models' reasoning and tool use abilities rather than constraining them with strict prompts and opinionated orchestrations.

### 1.2 三大核心特色

| 特色 | 说明 |
|------|------|
| **Simple** | 5分钟快速上手，内置 ReAct Agent、Tools、Skills、人机交互、Memory、Planning、实时语音、评估与模型微调 |
| **Extensible** | 丰富的生态集成（Tools/Memory/可观测性）、内置 MCP 和 A2A 协议支持、Message Hub 灵活多 Agent 编排 |
| **Production-ready** | 支持本地部署、Serverless 云端、K8s 集群，内置 OTel 可观测性 |

---

## 二、核心架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentScope 框架                              │
├─────────────────────────────────────────────────────────────┤
│  Agent 层                                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ ReAct   │ │ Voice    │ │ Realtime │ │ Deep    │       │
│  │ Agent   │ │ Agent    │ │ Voice    │ │ Research │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├─────────────────────────────────────────────────────────────┤
│  编排层                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ MsgHub      │  │ Pipeline     │  │ Workflow     │       │
│  │ 多Agent消息中枢 │  │ 顺序/并行管道  │  │ 工作流编排   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
├─────────────────────────────────────────────────────────────┤
│  能力层                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Tools   │ │ Memory   │ │ Planning │ │ Skills   │       │
│  │ 工具调用 │ │ 记忆管理  │ │ 规划能力  │ │ 技能系统  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├─────────────────────────────────────────────────────────────┤
│  协议层                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │ MCP     │ │ A2A      │ │ OTel     │                   │
│  │ 模型上下文协议│ │ Agent间协议│ │ 可观测性协议│                   │
│  └──────────┘ └──────────┘ └──────────┘                   │
├─────────────────────────────────────────────────────────────┤
│  部署层                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │ Local    │ │ Serverless│ │ K8s      │                   │
│  │ 本地运行  │ │ 云端无服务器 │ │ Kubernetes│                   │
│  └──────────┘ └──────────┘ └──────────┘                   │
├─────────────────────────────────────────────────────────────┤
│  模型层                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │ DashScope│ │ OpenAI   │ │ Gemini   │                   │
│  │ 阿里通义  │ │ GPT系列  │ │ 谷歌Gemini│                   │
│  └──────────┘ └──────────┘ └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 内置 Agent 类型

| Agent 类型 | 说明 | 示例 |
|-----------|------|------|
| **ReAct Agent** | 推理+行动基础Agent | 通用对话、工具调用 |
| **Voice Agent** | 语音交互Agent | 语音助手、游戏NPC |
| **Realtime Voice Agent** | 实时语音Agent | 实时对话系统 |
| **Deep Research Agent** | 深度研究Agent | 自动化调研 |
| **Browser-use Agent** | 浏览器自动化Agent | 网页操作、数据抓取 |
| **Meta Planner Agent** | 元规划Agent | 复杂任务分解 |
| **A2A Agent** | Agent间通信Agent | 多Agent协作 |

### 2.3 核心组件

| 组件 | 说明 |
|------|------|
| **MsgHub** | 多 Agent 消息中枢，支持动态添加/删除参与者 |
| **Pipeline** | 顺序/并行执行管道 |
| **Memory** | 短时记忆、长期记忆（含压缩）、SQLite 持久化 |
| **Toolkit** | 工具函数注册与管理 |
| **Formatter** | 聊天格式化（支持多种模型 API） |
| **Tuner** | 模型微调（Reinforcement Learning） |

---

## 三、核心特性详解

### 3.1 MCP 协议支持

MCP（Model Context Protocol，模型上下文协议）支持：

```python
from agentscope.mcp import HttpStatelessClient
from agentscope.tool import Toolkit

# 初始化 MCP 客户端
client = HttpStatelessClient(
    name="gaode_mcp",
    transport="streamable_http",
    url=f"https://mcp.amap.com/mcp?key={os.environ['GAODE_API_KEY']}",
)

# 获取 MCP 工具作为本地可调用函数
func = await client.get_callable_function(func_name="maps_geo")

# 使用方式1：直接调用
await func(address="天安门广场", city="北京")

# 使用方式2：注册到 Agent
toolkit = Toolkit()
toolkit.register_tool_function(func)
```

### 3.2 A2A 协议支持

A2A（Agent-to-Agent）协议实现多 Agent 间的通信与协作：

```python
from agentscope.agent import A2AAgent

agent = A2AAgent(
    name="assistant",
    model=...,
    ...
)
```

### 3.3 人机交互

支持实时中断与恢复：

- Conversation can be interrupted via cancellation in realtime
- Resumed seamlessly via robust memory preservation

### 3.4 实时语音 Agent

| 功能 | 说明 |
|------|------|
| **语音识别** | 语音输入理解 |
| **语音合成** | TTS 支持 |
| **实时对话** | Web 界面实时交互 |
| **多 Agent 狼人杀** | 语音游戏Demo |

### 3.5 模型微调（Agentic RL）

集成 Trinity-RFT 库实现强化学习微调：

| 示例 | 描述 | 模型 | 效果 |
|------|------|------|------|
| Math Agent | 数学解题Agent | Qwen3-0.6B | Accuracy: 75% → 85% |
| Frozen Lake | 导航环境 | Qwen2.5-3B-Instruct | Success: 15% → 86% |
| Learn to Ask | LLM-as-judge反馈 | Qwen2.5-7B-Instruct | Accuracy: 47% → 92% |
| Werewolf Game | 策略多Agent游戏 | Qwen2.5-7B-Instruct | Win rate: 50% → 80% |
| Data Augment | 合成训练数据 | Qwen3-0.6B | AIME-24: 20% → 60% |

---

## 四、快速开始

### 4.1 安装

**环境要求：** Python 3.10+

**从 PyPI 安装：**

```bash
pip install agentscope

# 或使用 uv
uv pip install agentscope
```

**从源码安装：**

```bash
git clone -b main https://github.com/agentscope-ai/agentscope.git
cd agentscope
pip install -e .
# 或使用 uv
uv pip install -e .
```

### 4.2 第一个 Agent

```python
from agentscope.agent import ReActAgent, UserAgent
from agentscope.model import DashScopeChatModel
from agentscope.memory import InMemoryMemory
from agentscope.tool import Toolkit, execute_python_code, execute_shell_command
import os

# 创建工具包
toolkit = Toolkit()
toolkit.register_tool_function(execute_python_code)
toolkit.register_tool_function(execute_shell_command)

# 创建 ReAct Agent（推理+行动）
agent = ReActAgent(
    name="Friday",
    sys_prompt="You're a helpful assistant named Friday.",
    model=DashScopeChatModel(
        model_name="qwen-max",
        api_key=os.environ["DASHSCOPE_API_KEY"],
        stream=True,
    ),
    memory=InMemoryMemory(),
    toolkit=toolkit,
)

# 创建用户代理
user = UserAgent(name="user")

# 对话循环
msg = None
while True:
    msg = await agent(msg)
    msg = await user(msg)
    if msg.get_text_content() == "exit":
        break
```

### 4.3 多 Agent 工作流

```python
from agentscope.pipeline import MsgHub, sequential_pipeline
from agentscope.message import Msg

async def multi_agent_conversation():
    # 创建多个 Agent
    agent1 = ...
    agent2 = ...
    agent3 = ...
    agent4 = ...

    # 创建消息中枢
    async with MsgHub(
        participants=[agent1, agent2, agent3],
        announcement=Msg("Host", "Introduce yourselves.", "assistant")
    ) as hub:
        # 顺序对话
        await sequential_pipeline([agent1, agent2, agent3])

        # 动态管理参与者
        hub.add(agent4)
        hub.delete(agent3)
        await hub.broadcast(Msg("Host", "Goodbye!", "assistant"))
```

---

## 五、示例项目

### 5.1 Agent 类

| 示例 | 说明 |
|------|------|
| ReAct Agent | 基础推理+行动Agent |
| Voice Agent | 语音交互Agent |
| Deep Research Agent | 深度研究自动化 |
| Browser-use Agent | 浏览器自动化 |
| Meta Planner Agent | 任务规划与分解 |
| A2A Agent | Agent间通信 |
| Realtime Voice Agent | 实时语音对话 |

### 5.2 功能类

| 示例 | 说明 |
|------|------|
| MCP | 模型上下文协议 |
| Anthropic Agent Skill | Anthropic技能支持 |
| Plan | 任务规划 |
| Structured Output | 结构化输出 |
| RAG | 检索增强生成 |
| Long-Term Memory | 长期记忆（ReMe） |
| Memory Compression | 记忆压缩 |
| TTS | 语音合成 |
| Session with SQLite | 持久化会话 |

### 5.3 游戏类

| 示例 | 说明 |
|------|------|
| Nine-player Werewolves | 九人狼人杀 |

### 5.4 工作流类

| 示例 | 说明 |
|------|------|
| Multi-agent Debate | 多 Agent 辩论 |
| Multi-agent Conversation | 多 Agent 对话 |
| Multi-agent Concurrent | 多 Agent 并发 |
| Multi-agent Realtime | 多 Agent 实时对话 |

### 5.5 评估与微调

| 示例 | 说明 |
|------|------|
| ACEBench | 评估基准 |
| Tune ReAct Agent | 模型微调 |

---

## 六、与同类框架对比

| 特性 | AgentScope | LangChain | AutoGen | CrewAI |
|------|------------|-----------|---------|---------|
| **内置 Agent** | ReAct/Voice/Realtime | 多种 |Conversational/Agent | Agent |
| **MCP 支持**（Model Context Protocol） | ✅ | 有限 | ❌ | ❌ |
| **A2A 支持**（Agent-to-Agent） | ✅ | ❌ | 有限 | ❌ |
| **语音支持** | ✅ TTS/Realtime | ❌ | ❌ | ❌ |
| **人机交互** | ✅ 实时中断 | 有限 | ❌ | ❌ |
| **模型微调**（Trinity-RFT） | ✅ | ❌ | ❌ | ❌ |
| **多 Agent 编排** | ✅ MsgHub | ✅ | ✅ | ✅ |
| **K8s 部署** | ✅ | 有限 | ❌ | ❌ |
| **OTel 可观测性**（OpenTelemetry） | ✅ | 有限 | ❌ | ❌ |

---

## 七、最新动态

| 时间 | 类型 | 内容 |
|------|------|------|
| 2026-03 | 发布 | CoPaw（Co Personal Agent Workstation）开源 |
| 2026-02 | 功能 | Realtime Voice Agent 支持 |
| 2026-01 | 社区 | Biweekly Meetings 启动 |
| 2026-01 | 功能 | Database 支持 + Memory 压缩 |
| 2025-12 | 集成 | A2A（Agent-to-Agent）协议支持 |
| 2025-12 | 功能 | TTS（Text-to-Speech）支持 |
| 2025-11 | 集成 | Anthropic Agent Skill 支持 |
| 2025-11 | 发布 | Alias-Agent、Data-Juicer Agent 开源 |
| 2025-11 | 集成 | Trinity-RFT（Agentic RL） |
| 2025-11 | 功能 | ReMe 长期记忆增强 |

---

## 八、资源链接

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/agentscope-ai/agentscope |
| 官网 | https://doc.agentscope.io/ |
| 教程 | https://doc.agentscope.io/tutorial/ |
| API 文档 | https://doc.agentscope.io/api/agentscope.html |
| Discord | https://discord.gg/eYMpfnkG8h |
| arxiv | https://arxiv.org/abs/2402.14034 |

---

## 九、总结

### 9.1 核心价值

AgentScope 的核心价值在于**为开发者提供生产级、易用的 AI Agent 构建框架**，充分利用日益强大的模型推理和工具调用能力，而非用严格的提示词约束模型。

| 传统方式 | AgentScope 方式 |
|----------|----------------|
| 复杂配置 | 5分钟快速上手 |
| 分散集成 | 内置 MCP/A2A/OTel |
| 单一 Agent | 多 Agent 编排（MsgHub） |
| 被动调用 | 实时语音+人机交互 |
| 无法微调 | Trinity-RFT 模型微调 |

### 9.2 技术亮点

1. **MCP 协议**：Model Context Protocol 原生支持
2. **A2A 协议**：Agent-to-Agent 通信标准
3. **实时语音**：TTS + Realtime Voice Agent
4. **人机交互**：实时中断与记忆恢复
5. **模型微调**：Trinity-RFT 强化学习微调
6. **多 Agent 编排**：MsgHub + Pipeline
7. **生产级部署**：Local/Serverless/K8s + OTel

---

**相关话题标签**

#AgentScope #AI Agent #多Agent #MCP #A2A #模型微调 #语音Agent

**来源**

- GitHub：https://github.com/agentscope-ai/agentscope

---

*AgentScope 由 agentscope-ai 开发，采用 Apache-2.0 许可证。*
