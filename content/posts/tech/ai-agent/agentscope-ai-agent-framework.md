---
title: "AgentScope：生产级 AI Agent 框架完全指南"
date: 2026-04-01T00:04:44+08:00
slug: "agentscope-ai-agent-framework"
aliases:
  - /posts/tech/agentscope-ai-agent-framework/
description: "系统解读 AgentScope 的 ReAct Agent、MCP、A2A、记忆、Realtime、TTS、Tuner 与多 Agent 架构，涵盖核心抽象层、能力层、编排层的设计解析。"
draft: false
categories: ["技术笔记"]
tags: ["AgentScope", "AI Agent", "ReAct", "MCP", "A2A", "多智能体"]
---

# AgentScope：生产级 AI Agent 框架完全指南

> 预计阅读时间：60分钟 | 难度：⭐⭐⭐⭐

---

## 一、先给结论：AgentScope 值不值得看

如果你只想要一句判断，那么答案是：**值得，而且非常值得认真读官方设计**。

截至 2026-04-01，AgentScope 的 GitHub 页面显示约 **22.6k Stars**、**2.3k Forks**。它不是一个只会“调模型 + 调提示词”的轻量封装，而是一套面向生产环境的 **Agent 开发框架 + 协议集成层 + 运行时生态**。

官方给它的定位很清楚：

> AgentScope is a production-ready, easy-to-use agent framework with essential abstractions that work with rising model capability and built-in support for finetuning.

这句话里有 3 个关键词：

| 关键词 | 含义 | 为什么重要 |
| -------- | ------ | ------------ |
| **production-ready** | 不只关心 Demo，还关心部署、可观测性、运行时能力 | 很多 Agent 项目能跑起来，但很难长期维护 |
| **easy-to-use** | 官方提供现成的 ReAct Agent、MCP、A2A、记忆、TTS、Realtime、Tuner | 降低从 0 到 1 的门槛 |
| **essential abstractions** | 抽象的是消息、状态、工具、格式化器、记忆、协议，而不是写死工作流 | 更适合复杂 Agent 系统演进 |

从工程视角看，AgentScope 最值得关注的地方不是“功能很多”，而是 **功能背后的抽象比较统一**。消息、状态、工具、协议、工作流、实时交互，最终都被收敛到一套比较清晰的模型里。

---

## 二、先把概念讲清楚

很多人第一次看 Agent 框架容易混淆“Agent、Workflow、Tool、Memory、Protocol”之间的边界。AgentScope 的长处之一，就是这些概念分层比较明确。

### 2.1 核心术语表

| 概念 | 在 AgentScope 里的含义 | 你应该怎么理解 |
| ------ | ------------------------ | ---------------- |
| **State** | 运行时状态快照机制 | 不是聊天记录，而是对象恢复与持久化的基础 |
| **Msg** | 统一消息结构 | Agent 间通信、UI 展示、记忆存储、模型输入都围绕它展开 |
| **Tool** | 任意可调用对象 | 可以是同步、异步、流式、实例方法、可调用类 |
| **Toolkit** | 工具注册与管理容器 | 让 Agent 可以统一获得本地工具和远端 MCP 工具 |
| **Formatter** | 消息到模型 API 的转换层 | 它决定同一份消息如何适配不同模型接口 |
| **AgentBase** | 所有异步 Agent 的基础抽象 | 规定 reply / observe / print / handle_interrupt 这些核心行为 |
| **ReActAgent** | 官方现成的推理 + 行动 Agent | 大多数通用 Agent 应用的默认入口 |
| **MsgHub** | 多 Agent 消息广播中枢 | 让多 Agent 对话不必手工互相 observe |
| **Long-Term Memory** | 长期记忆系统 | 用于跨会话偏好、知识与上下文保留 |
| **MCP** | Model Context Protocol | 标准化接入外部工具服务 |
| **A2A** | Agent-to-Agent 协议 | 标准化接入远端 Agent |
| **RealtimeAgent** | 面向实时事件流的 Agent | 更适合实时语音、实时会话，不等同于普通 ReActAgent |

### 2.2 一个非常重要的认识

AgentScope 不是在说“每个任务都应该变成多 Agent”，也不是在说“所有能力都应该被 DSL 编排”。它真正强调的是：

1. **先把 Agent 的基础抽象做好**，包括消息、状态、工具、记忆、格式化器。
2. **再把复杂能力作为模块增量接入**，例如 MCP、A2A、TTS、Realtime、Tuner。
3. **最后把部署、观测、可运维能力外接到生态里**，例如 AgentScope Runtime、Studio、Samples。

这就是它比“只会写链式流程”的框架更强的一点：**它先建模，再扩展，而不是先拼功能。**

---

## 三、架构分析：它到底是怎么分层的

从官方 README、教程导航和公开源码结构综合来看，AgentScope 可以理解成下面这 5 层：

```text
应用层
├─ 业务 Agent、工作流、提示词、场景逻辑
│
核心抽象层
├─ AgentBase / ReActAgent / Msg / Formatter / Toolkit / Memory / State
│
能力层
├─ MCP / A2A / TTS / Realtime / RAG / Evaluation / Tuner / Plan
│
编排层
├─ MsgHub / sequential_pipeline / fanout_pipeline / ChatRoom
│
生态与运行时层
└─ AgentScope Runtime / Studio / Samples / CoPaw / OTel
```

### 3.1 核心库和生态库不是一回事

这是理解 AgentScope 的关键。

| 部分 | 角色 | 典型内容 |
| ------ | ------ | ---------- |
| **AgentScope** | 核心开发框架 | Agent、消息、格式化器、工具、记忆、协议接入、工作流 |
| **AgentScope Runtime** | 生产运行时基础设施 | 沙箱、Agent-as-a-Service、部署、状态与服务治理 |
| **AgentScope Studio** | 可视化开发与调试环境 | 原型开发、监控、调试 |
| **AgentScope Samples** | 官方示例集合 | 从最小样例到更完整应用 |
| **CoPaw** | 基于生态构建的 AI 助手产品 | 展示框架在真实产品中的落地方式 |

所以，**AgentScope 本体负责“怎么开发 Agent”，Runtime 负责“怎么把 Agent 可靠跑起来”**。这两个部分是协同关系，不是替代关系。

### 3.2 它的设计重点不是“工作流先行”，而是“Agent 先行”

很多框架会从 DAG、节点流、状态图出发组织系统。AgentScope 不是完全排斥这些东西，但它的重心更偏向：

- Agent 本身的能力边界；
- 工具调用和记忆机制；
- 多 Agent 之间如何交换消息；
- 如何让远端工具和远端 Agent 接入；
- 如何把实时交互和生产部署接上去。

因此，它更适合构建 **有自主性、有工具调用、有状态、有协作需求** 的 Agent 系统。

---

## 四、功能特点：官方到底提供了什么

这一部分只讲 **已在官方 README、教程或公开源码中明确出现的能力**。

### 4.1 ReActAgent：默认主角

官方教程明确说明，`ReActAgent` 是 AgentScope 里最重要的现成 Agent 实现之一。它把 Agent 行为拆成两个核心阶段：

1. **reasoning**：思考、构造工具调用、生成下一步动作。
2. **acting**：执行工具，并将结果回灌到后续推理。

官方教程列出的 `ReActAgent` 关键能力包括：

| 能力 | 说明 |
| ------ | ------ |
| **Realtime Steering** | 支持用户在回复过程中实时打断 |
| **Memory Compression** | 对过长上下文做自动压缩 |
| **Parallel Tool Calls** | 支持并行工具调用 |
| **Structured Output** | 支持结构化输出 |
| **Fine-grained MCP Control** | 支持更细粒度的 MCP 工具接入 |
| **Meta Tool** | Agent 可自主管理工具 |
| **Long-Term Memory** | 支持 agent_control / static_control / both 三种模式 |
| **Automatic State Management** | 状态可管理、可恢复 |

这意味着它不是一个“能调一次工具就结束”的简单 ReAct 封装，而是已经把 **中断、记忆、工具、结构化输出、协议集成** 这些真实应用会遇到的问题考虑进去了。

### 4.2 工作流与多 Agent 编排

官方 `pipeline` 教程里，AgentScope 提供了几类核心编排能力：

| 能力 | 作用 |
| ------ | ------ |
| **MsgHub** | 多 Agent 间自动广播消息 |
| **sequential_pipeline** | 顺序执行多个 Agent |
| **fanout_pipeline** | 将同一输入并发分发给多个 Agent |
| **ChatRoom** | 面向 Realtime 场景的集中式会话管理 |

这里最重要的是 `MsgHub`。它不是“另一个 Agent”，而是一个 **异步上下文管理器**。进入上下文后，一个参与者产出的消息会自动广播给其他参与者，开发者不必手工一个个调用 `observe()`。

### 4.3 MCP：把远端工具变成 Agent 的本地能力

AgentScope 对 MCP 的支持是它非常强的一张牌。

官方教程明确给出以下事实：

- 支持 **HTTP** 的 `streamable_http` 和 `sse` 两种传输。
- 支持 **StdIO** MCP 服务。
- 支持 **stateful client** 与 **stateless client**。
- 支持 **服务器级** 和 **函数级** 的 MCP 工具管理。

更实用的是，它不只支持“把 MCP 接上”，还支持两种接入方式：

1. **直接拿远端函数当本地可调用函数**。
2. **把 MCP 工具批量注册进 Toolkit**，让 ReActAgent 像使用普通工具一样使用它们。

这背后的工程意义很大：**MCP 在 AgentScope 里不是外挂，而是被并入统一工具系统。**

### 4.4 记忆系统：短时记忆、长期记忆、压缩记忆

从官方教程与源码可以看到，AgentScope 的记忆设计分成三个层面：

| 层面 | 作用 |
| ------ | ------ |
| **短时记忆** | 保存当前会话上下文 |
| **长期记忆** | 保存跨会话偏好、知识、经验 |
| **压缩记忆** | 当上下文过长时，对旧消息进行结构化压缩 |

长期记忆方面，官方教程展示了：

- `Mem0LongTermMemory`
- ReMe 相关示例
- `agent_control`
- `static_control`
- `both`

这 3 种模式非常值得理解：

| 模式 | 含义 | 适合谁 |
| ------ | ------ | -------- |
| **agent_control** | Agent 通过工具调用自主决定记录和检索什么 | 希望增强自主性的场景 |
| **static_control** | 开发者显式控制记录和检索 | 希望可控、稳定、可审计 |
| **both** | 两者同时启用 | 复杂系统、混合控制需求 |

压缩记忆方面，官方教程强调它不是简单删除旧消息，而是：

- 保留最近若干条消息；
- 将更早消息总结成结构化摘要；
- 旧消息被标记为 `COMPRESSED`；
- 摘要作为额外记忆保存。

从公开源码里的 `SummarySchema` 来看，压缩摘要至少关注这几类信息：

- `task_overview`
- `current_state`
- `important_discoveries`
- `next_steps`
- `context_to_preserve`

这说明它不是“缩短聊天记录”这么简单，而是更接近 **任务型 Agent 的上下文摘要机制**。

### 4.5 实时能力：Realtime Agent 和 TTS 是两条线

很多人会把“实时语音”“流式输出”“语音合成”混成一个东西。AgentScope 把这些概念拆得比较清楚。

#### Realtime Agent

官方 Realtime 教程说明：

- `RealtimeAgent` 用于实时交互，例如实时语音、实时聊天；
- 支持 OpenAI、DashScope、Gemini 等实时模型；
- 提供统一事件接口；
- 支持工具调用；
- 支持多 Agent 互动；
- 当前该模块仍在持续开发中。

#### TTS

官方 TTS 教程说明：

- TTS 提供统一语音合成接口；
- 区分 **非实时 TTS** 和 **实时 TTS**；
- 支持 DashScope、OpenAI、Gemini 等提供方；
- 实时 TTS 适合流式文本生成场景，以降低端到端延迟。

所以：

- **RealtimeAgent** 更偏“会话事件编排”；
- **TTS** 更偏“文本到音频的统一抽象”。

这是两个相邻但不相同的模块。

### 4.6 A2A：让 Agent 直接接远端 Agent

官方 A2A 教程很明确：A2A 是一个实验性能力，而且它有边界。

AgentScope 中的 `A2AAgent` 主要负责：

- 获取和使用 `Agent Card`；
- 连接远端 A2A Agent；
- 在 AgentScope 消息格式和 A2A 消息格式之间做转换；
- 处理任务生命周期、流式响应和轮询状态。

但官方同时明确说明了限制：

| 限制 | 说明 |
| ------ | ------ |
| **聊天场景优先** | 目前主要面向 1 个用户和 1 个 Agent 的对话 |
| **不支持实时中断** | 不能完全对齐本地 ReActAgent 的中断能力 |
| **不支持 agentic structured output** | 远端协议层本身有限制 |
| **observe 先本地缓存** | 多次 `observe()` 若不触发 `reply()`，远端看不到这些消息 |

这部分很重要，因为它提醒你：**A2AAgent 不是“把远端 Agent 变成本地 ReActAgent 的完全等价替代品”**。

### 4.7 Tuner：Agent 的强化学习调优入口

官方 `tuner` 教程给出的设计非常清晰。它把强化学习调优抽象成 3 个核心组件：

| 组件 | 作用 |
| ------ | ------ |
| **Task Dataset** | 训练 / 评估数据集 |
| **Workflow Function** | 被调优的 Agent 工作流 |
| **Judge Function** | 评估输出并给出奖励信号 |

这意味着 AgentScope 的调优不是“给模型一个新参数”，而是把 **Agent 行为本身** 作为调优对象。

这比“只调一个模型的生成效果”更贴近 Agent 应用的真实目标。

---

## 五、使用说明：怎么从 0 到 1 跑起来

### 5.1 安装

官方要求 **Python 3.10+**。

```bash
pip install agentscope
```

或者：

```bash
uv pip install agentscope
```

如果需要从源码安装：

```bash
git clone -b main https://github.com/agentscope-ai/agentscope.git
cd agentscope
pip install -e .
```

### 5.2 第一个可用的 ReAct Agent

下面这个示例遵循官方教程写法，重点是 **模型、Formatter、Toolkit、Memory** 四件套一起出现。

```python
import asyncio
import os

from agentscope.agent import ReActAgent, UserAgent
from agentscope.formatter import DashScopeChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit, execute_python_code


async def main() -> None:
    """运行一个最小可用的 ReAct Agent。"""
    toolkit = Toolkit()
    toolkit.register_tool_function(execute_python_code)

    agent = ReActAgent(
        name="Friday",
        sys_prompt="You're a helpful assistant named Friday.",
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ["DASHSCOPE_API_KEY"],
            stream=True,
            enable_thinking=False,
        ),
        formatter=DashScopeChatFormatter(),
        toolkit=toolkit,
        memory=InMemoryMemory(),
    )

    user = UserAgent(name="user")
    msg = None

    while True:
        msg = await agent(msg)
        msg = await user(msg)
        if msg.get_text_content() == "exit":
            break


asyncio.run(main())
```

### 5.3 为什么 `Formatter` 不能省略

这是新手最容易忽略的地方之一。

在 AgentScope 中，`Formatter` 不是锦上添花，而是 **模型兼容层**。官方教程明确把它定义为“负责把消息对象转换成模型 API 所需格式”的核心组件。

你可以把它理解为：

- `Msg` 负责表达“系统里真正的消息语义”；
- `Formatter` 负责把这份语义翻译成不同模型能吃的格式。

如果你把模型换了，但 `Formatter` 不匹配，最容易出现的问题就是：

- 消息角色不兼容；
- 工具调用结构不兼容；
- 多身份消息表达不正确；
- 结构化输出异常。

### 5.4 多 Agent 对话：用 MsgHub 管理广播

下面这个例子展示 `MsgHub` 的典型写法：

```python
import asyncio
import os

from agentscope.agent import ReActAgent
from agentscope.formatter import DashScopeMultiAgentFormatter
from agentscope.memory import InMemoryMemory
from agentscope.message import Msg
from agentscope.model import DashScopeChatModel
from agentscope.pipeline import MsgHub, sequential_pipeline


def create_agent(name: str, role_desc: str) -> ReActAgent:
    """创建一个参与群聊的 Agent。"""
    return ReActAgent(
        name=name,
        sys_prompt=role_desc,
        model=DashScopeChatModel(
            model_name="qwen-max",
            api_key=os.environ["DASHSCOPE_API_KEY"],
        ),
        formatter=DashScopeMultiAgentFormatter(),
        memory=InMemoryMemory(),
    )


async def main() -> None:
    """运行一个最小多 Agent 广播示例。"""
    alice = create_agent("Alice", "You're Alice, a product manager.")
    bob = create_agent("Bob", "You're Bob, a backend engineer.")
    charlie = create_agent("Charlie", "You're Charlie, a designer.")

    async with MsgHub(
        participants=[alice, bob, charlie],
        announcement=Msg(
            "host",
            "Please introduce yourself briefly and explain your role.",
            "user",
        ),
    ):
        await sequential_pipeline([alice, bob, charlie])


asyncio.run(main())
```

这里最重要的不是 `sequential_pipeline`，而是你要理解：

- `MsgHub` 负责广播；
- Agent 负责生成回复；
- `Formatter` 负责多身份消息格式；
- `Memory` 负责上下文保留。

### 5.5 把远端 MCP 工具注册进 Toolkit

```python
import asyncio
import os

from agentscope.mcp import HttpStatelessClient
from agentscope.tool import Toolkit


async def main() -> None:
    """注册远端 MCP 工具到 Toolkit。"""
    toolkit = Toolkit()

    client = HttpStatelessClient(
        name="map_services",
        transport="streamable_http",
        url=f"https://mcp.amap.com/mcp?key={os.environ['GAODE_API_KEY']}",
    )

    await toolkit.register_mcp_client(client)
    print(len(toolkit.get_json_schemas()))


asyncio.run(main())
```

这段代码体现出 AgentScope 的一个核心优势：**远端 MCP 工具会被统一纳入 Toolkit，而不是成为单独的一套调用体系。**

---

## 六、原理分析：为什么它比“提示词 + 几个函数”更像工程框架

### 6.1 消息是全系统的统一介质

官方 Key Concepts 明确指出，`Message` 是系统里的基础数据结构，用于：

- Agent 之间交换信息；
- 在用户界面展示信息；
- 存入记忆；
- 作为 AgentScope 和不同模型 API 之间的统一介质。

这意味着 AgentScope 的抽象不是“函数传字符串”，而是“系统传消息对象”。这会带来很大的工程收益：

- 更容易统一工具调用结果；
- 更容易统一多模态块，例如文本、音频、图像；
- 更容易接观察、记忆、追踪、前端。

### 6.2 Agent 的本质是 4 个行为

从官方 Key Concepts 和源码来看，`AgentBase` 的核心行为可以概括成：

| 行为 | 作用 |
| ------ | ------ |
| `reply` | 接收输入并生成回复 |
| `observe` | 只接收、不立刻返回回复 |
| `print` | 将消息输出到终端或界面 |
| `handle_interrupt` | 处理中断后的收尾逻辑 |

这个抽象非常有价值，因为它把“一个 Agent 能做什么”说清楚了。

很多框架把 Agent 混成一个“大黑箱调用”。AgentScope 则把 **回复、观察、输出、中断** 分开，这样才有机会把实时 Steering、Hook、可观测性、UI 转发做扎实。

### 6.3 Formatter 解决的是“模型接口分裂”问题

不同模型供应商对消息格式、角色字段、工具调用协议、流式结构的要求并不完全一致。AgentScope 单独抽出 `Formatter`，本质上是在做：

- 统一上层消息语义；
- 隔离底层模型 API 差异；
- 把兼容性问题从业务代码里拿出去。

这也是为什么官方强调：**多 Agent 编排不等于 multi-agent formatter**。工作流层的多 Agent 和消息格式层的多身份问题，是两个不同维度。

### 6.4 协议接入不是附属插件，而是能力并入

无论是 MCP 还是 A2A，AgentScope 的设计都不是“额外加一个网络客户端就算完事”，而是：

- 远端工具最终进入 Toolkit；
- 远端 Agent 最终进入 Agent 抽象；
- 事件流最终进入 Realtime 统一事件接口。

这就是为什么它更适合做长期演化的 Agent 平台，而不只是一次性的技术实验。

---

## 七、源码分析：从公开源码能读出什么设计取舍

下面这部分基于公开源码结构和原始文件头部实现信息进行分析。

### 7.1 核心源码入口一览

| 路径 | 角色 | 读源码时应该关注什么 |
| ------ | ------ | ---------------------- |
| `src/agentscope/agent/_agent_base.py` | 所有异步 Agent 的基础抽象 | 核心行为、Hook、中断、输出 |
| `src/agentscope/agent/_react_agent.py` | ReActAgent 的主要实现 | 推理 / 行动循环、记忆压缩、工具与计划整合 |
| `src/agentscope/pipeline/_msghub.py` | 多 Agent 广播中枢 | 自动广播与参与者管理 |
| `src/agentscope/mcp/_http_stateless_client.py` | HTTP 无状态 MCP 客户端 | 每次调用创建 / 关闭会话 |
| `src/agentscope/agent/_a2a_agent.py` | A2A 协议 Agent | 远端 Agent 接入与格式转换 |
| `src/agentscope/agent/_realtime_agent.py` | 实时 Agent | 事件驱动、队列、会话生命周期 |

### 7.2 `AgentBase`：基础抽象比很多人想的更重

从 `_agent_base.py` 可以直接看到：

- `AgentBase` 继承自 `StateModule`；
- 使用 `_AgentMeta` 元类；
- 支持 `pre_reply`、`post_reply`、`pre_print`、`post_print`、`pre_observe`、`post_observe` 这些 Hook；
- 处理音频、图像、视频、工具调用等多种消息块。

这说明两件事：

1. AgentScope 一开始就不是只围绕文本设计的。
2. 它把 Hook 和状态管理放在了非常核心的位置。

也就是说，**可插拔性和可观测性并不是后补功能，而是基础设计的一部分**。

### 7.3 `ReActAgent`：不是一个薄薄的 while loop

从 `_react_agent.py` 的导入和结构可以看到，`ReActAgent` 直接整合了：

- `FormatterBase`
- `MemoryBase`
- `LongTermMemoryBase`
- `PlanNotebook`
- `Toolkit`
- `KnowledgeBase`
- `TTSModelBase`
- `ToolResponse`

这非常能说明问题：官方把 `ReActAgent` 定位成一个 **能力聚合中心**。

进一步看 `SummarySchema`，它不是只存“摘要文本”，而是显式拆成任务总览、当前状态、重要发现、下一步、需要保留的上下文。这种结构非常适合：

- 长任务；
- 多步骤工作流；
- 可恢复执行；
- 中断后续跑。

### 7.4 `MsgHub`：本质是消息广播上下文

从 `_msghub.py` 可以明确看到：

- `MsgHub` 是一个类，不是装饰器；
- 它接受 `participants`、`announcement`、`enable_auto_broadcast`、`name`；
- 进入上下文时会广播公告；
- 支持动态管理参与者。

这说明 `MsgHub` 的定位很明确：**负责消息传播，而不是负责推理决策。**

这是非常健康的设计。因为一旦把“消息路由”和“Agent 行为”搅在一起，系统会很快失控。

### 7.5 `HttpStatelessClient`：MCP 的无状态封装很工程化

从 `_http_stateless_client.py` 可以看到：

- 支持 `streamable_http` 和 `sse`；
- `stateful` 被显式标记为 `False`；
- 每次工具调用会新建并销毁会话；
- `headers`、`timeout`、`sse_read_timeout` 都是正式参数。

这意味着它不是一个“实验性质的 HTTP wrapper”，而是真正面向远端 MCP 服务的工程组件。

它的核心价值是：

- 简化调用生命周期；
- 避免长连接状态污染；
- 适合按需调用远端工具。

### 7.6 `A2AAgent`：强调协议适配，而不是假装本地等价

从 `_a2a_agent.py` 的文档字符串就能看出设计态度非常诚实。官方直接把限制写在类说明里：

- 主要支持聊天场景；
- 不支持 `reply()` 的结构化输出；
- `observe()` 先缓存，`reply()` 时再统一发送。

这种设计态度很值得肯定。它没有把 A2A 包装成“什么都支持”，而是明确告诉开发者协议边界。

### 7.7 `RealtimeAgent`：它不是 `AgentBase` 的一个简单子类

从 `_realtime_agent.py` 可以直接看到一个重要事实：`RealtimeAgent` 继承的是 `StateModule`，不是 `AgentBase`。

这背后反映的是架构判断：

- 普通 Agent 主要围绕“请求 → 回复”；
- Realtime Agent 主要围绕“事件流、队列、生命周期、前后端交互”。

所以它单独成系是合理的。否则为了兼容普通 Agent 抽象，实时系统反而会被绑住手脚。

---

## 八、开发扩展：如果你要二次开发，应该从哪里下手

### 8.1 先决定你扩展的是哪一层

| 目标 | 推荐扩展点 |
| ------ | ------------ |
| 自定义普通 Agent 行为 | `AgentBase` |
| 自定义 ReAct 推理 / 行动过程 | `ReActAgentBase` |
| 自定义模型兼容逻辑 | `Formatter` |
| 自定义本地工具 | `Toolkit` |
| 接远端工具 | `MCP Client` + `Toolkit` |
| 接远端 Agent | `A2AAgent` |
| 做实时语音 / 实时交互 | `RealtimeAgent` |
| 做训练与调优 | `tuner` |

### 8.2 什么时候继承 `AgentBase`

当你需要：

- 完全自定义回复逻辑；
- 自定义 `observe()` 行为；
- 自定义中断处理；
- 复用 Hook、状态管理和输出机制。

这时继承 `AgentBase` 是最自然的。

### 8.3 什么时候直接用 `ReActAgent`

当你要的是：

- 工具调用；
- 结构化输出；
- 记忆管理；
- 中断恢复；
- 长任务执行；
- 多 Agent 协同中的单 Agent 节点。

换句话说，**大多数应用起点都应该先用 `ReActAgent`，而不是上来就自定义 Agent 类**。

### 8.4 什么时候需要 Runtime

如果你的目标已经不是“跑一个 Agent 脚本”，而是：

- 对外提供 API；
- 需要沙箱执行工具；
- 需要部署到本地、Kubernetes 或 Serverless；
- 需要更强的生产级运行能力；

这时候就应该看 **AgentScope Runtime**，而不是只盯着核心框架本体。

---

## 九、使用场景：它适合什么，不适合什么

### 9.1 适合的场景

| 场景 | 为什么适合 |
| ------ | ------------ |
| **带工具调用的通用助手** | `ReActAgent` + `Toolkit` 是天然组合 |
| **多 Agent 协作** | `MsgHub`、`pipeline`、多身份 `Formatter` 都已就位 |
| **接外部工具生态** | MCP 支持成熟，且能并入 Toolkit |
| **跨会话 Agent 应用** | 长期记忆和压缩记忆设计清晰 |
| **实时语音 / 实时交互** | `RealtimeAgent`、TTS 与统一事件接口已成体系 |
| **需要训练 Agent 工作流** | `tuner` 将数据集、工作流、评判函数抽象出来 |

### 9.2 不太适合的场景

| 场景 | 原因 |
| ------ | ------ |
| **完全确定性的固定流程** | 用纯函数或普通工作流引擎通常更简单 |
| **只有单次调用、无状态需求的小脚本** | AgentScope 的抽象会显得偏重 |
| **完全不需要模型自主决策** | ReAct、记忆、协议能力的收益会下降 |
| **对协议与生态没有需求的极简项目** | 更轻量的封装也许更省心 |

这里没有“绝对不适合”，只有“抽象成本是否值得”。

---

## 十、从入门到精通：推荐学习路径

### 10.1 新手路径

#### 第一步：先跑通最小 ReActAgent

目标不是做复杂功能，而是吃透这 4 个对象：

- `ReActAgent`
- `ChatModel`
- `Formatter`
- `Toolkit`

#### 第二步：加入一个真实工具

例如：

- Python 执行器；
- Shell 工具；
- 一个你自己写的查询函数。

做到这一步，你会真正理解 AgentScope 的“推理 + 行动”闭环。

### 10.2 进阶路径

#### 第三步：理解记忆

建议分别体验：

1. 只用短时记忆；
2. 加长期记忆；
3. 打开压缩记忆。

这样你会理解“上下文保留”和“上下文治理”不是一回事。

#### 第四步：理解多 Agent

建议先用 `MsgHub` 做一个最小三人对话，再观察：

- 谁在广播；
- 谁在观察；
- 谁负责真正回复；
- `Formatter` 怎样表达多身份消息。

### 10.3 专家路径

如果你已经完成前面的步骤，下一阶段建议这样走：

| 阶段 | 学习重点 |
| ------ | ---------- |
| **高级开发** | 自定义 `AgentBase` / `ReActAgentBase` |
| **协议集成** | MCP、A2A、远端服务接入 |
| **实时系统** | `RealtimeAgent`、TTS、事件流 |
| **生产化** | Runtime、可观测性、部署 |
| **能力优化** | `tuner`、评估、长期记忆治理 |

### 10.4 自测清单

如果下面 8 个问题你都能答出来，就说明你已经真正入门了：

1. `Msg` 为什么是统一介质？
2. `Formatter` 为什么不能省？
3. `MsgHub` 负责的是广播还是推理？
4. `A2AAgent` 为什么不能完全等同于本地 Agent？
5. `RealtimeAgent` 为什么单独成系？
6. 长期记忆的 3 种模式差别是什么？
7. MCP 工具为什么要进入 `Toolkit`？
8. `tuner` 为什么调优的是工作流，而不只是模型？

---

## 十一、常见误区与排查建议

### 11.1 误区一：多 Agent 就等于 MsgHub

不是。

`MsgHub` 负责的是 **消息广播机制**，而不是全部多 Agent 能力。多 Agent 系统还涉及：

- 角色分工；
- 任务路由；
- 记忆隔离；
- 模型配置；
- 输出汇总。

### 11.2 误区二：A2A 支持了，就说明远端 Agent 和本地 Agent 完全一致

不是。

官方已经明确说明了 A2A 的边界。远端协议是远端协议，本地实现是本地实现，二者能对接，不代表二者等价。

### 11.3 误区三：有长期记忆就应该全开

不一定。

长期记忆会引入：

- 记录策略问题；
- 检索质量问题；
- 记忆污染问题；
- 可审计性问题。

如果业务要求强可控，优先考虑 `static_control`；如果你确实想把更多控制权交给 Agent，再考虑 `agent_control` 或 `both`。

### 11.4 误区四：Realtime 和 TTS 是一个东西

不是。

Realtime 更偏会话事件处理，TTS 更偏语音合成。它们可以组合，但不该混为一谈。

### 11.5 误区五：只要能回答问题，就是生产级 Agent

不是。

生产级至少要考虑：

- 状态管理；
- 中断恢复；
- 记忆治理；
- 工具失败处理；
- 可观测性；
- 部署与运行时安全。

恰好这些，正是 AgentScope 重点投入的方向。

---

## 十二、资源与延伸阅读

| 资源 | 链接 |
| ------ | ------ |
| GitHub 仓库 | [agentscope-ai/agentscope](https://github.com/agentscope-ai/agentscope) |
| 官方文档首页 | [doc.agentscope.io](https://doc.agentscope.io/) |
| 官方教程 | [tutorial](https://doc.agentscope.io/tutorial/) |
| API 文档 | [API](https://doc.agentscope.io/api/agentscope.html) |
| 论文 | [arXiv 2402.14034](https://arxiv.org/abs/2402.14034) |
| Discord | [社区入口](https://discord.gg/eYMpfnkG8h) |

建议阅读顺序：

1. 先读 README，建立整体认知。
2. 再读 Key Concepts，搞清术语。
3. 然后读 Create ReAct Agent、Pipeline、MCP、Long-Term Memory。
4. 最后再读 A2A、Realtime、TTS、Tuner。

---

## 十三、总结：AgentScope 的真正价值是什么

AgentScope 的真正价值，不是“功能表很长”，而是它把 **Agent 应用最难工程化的几件事** 放到了一个相对统一的抽象体系里：

- 用 `Msg` 统一消息；
- 用 `Formatter` 隔离模型差异；
- 用 `Toolkit` 统一本地工具和 MCP 工具；
- 用 `MsgHub` 做多 Agent 广播；
- 用长期记忆与压缩记忆治理上下文；
- 用 `A2A` 与 `Realtime` 打通更大的 Agent 网络；
- 用 `Runtime` 和可观测性走向生产部署。

如果你只是想写一个一次性的 LLM 小脚本，它可能显得有点重。

但如果你想构建的是：

- 可扩展的 Agent 系统，
- 可协作的多 Agent 应用，
- 可接入协议生态的工具平台，
- 可调试、可观测、可部署的生产级服务，

那么 AgentScope 的设计就会显得非常有价值。

**一句话总结**：AgentScope 不是"又一个 Agent Demo 框架"，而是一套认真回答"Agent 应用如何工程化"的体系化方案。

---

## 相关话题标签

AgentScope、AI Agent、ReAct、MCP、A2A、多智能体、Agent Engineering

## 来源

- [GitHub](https://github.com/agentscope-ai/agentscope)
- [Docs](https://doc.agentscope.io/)
