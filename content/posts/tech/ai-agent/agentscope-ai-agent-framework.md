---
title: "AgentScope 2.0：生产级 AI Agent 框架完全指南"
date: "2026-09-01T00:04:44+08:00"
lastmod: "2026-09-22T00:00:00+08:00"
slug: "agentscope-ai-agent-framework"
github_repo: "agentscope-ai/agentscope"
source_key: "gh:agentscope-ai/agentscope"
aliases:
  - /posts/tech/agentscope-ai-agent-framework/
description: "基于 AgentScope v2.0.8，系统解读统一 Agent 类、Toolkit、MCP、权限系统、Workspace、上下文压缩、长期记忆、Realtime 与 A2A，覆盖 SDK、Agent Service 与生态的三层设计。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "ReAct", "MCP", "多智能体", "AgentScope"]
---

# AgentScope 2.0：生产级 AI Agent 框架完全指南

---

## 一、AgentScope 解决了什么问题

AgentScope 是阿里通义实验室开源的 Agent 开发框架。截至 2026-09-22，GitHub 上约 **3.2 万 Stars**、**3.5 千 Forks**，Apache-2.0 协议，主分支几乎每天都有提交。

先交代版本边界，这直接影响你该读哪份文档：

- PyPI 上 `pip install agentscope` 装到的是 **AgentScope 2.0**，当前稳定版 **v2.0.8**（2026-09-08 发布），要求 **Python 3.11+**。
- 2.0 是一次 breaking change：1.0 的 `ReActAgent`、`MsgHub`、`memory` 模块等在 2.0 里被重构或移除。官方文档明确提示"Do not mix AgentScope 1.x and 2.x APIs"。
- 文档站也分两条线：`docs.agentscope.io` 是 2.0 文档（stable 目前指向 2.0.8），`doc.agentscope.io` 是 1.0 旧站。本文全部以 **v2.0.8** 的文档、README 与源码为准，类名和代码可以直接对号入座。

官方 README 对 2.0 的定位是：

> AgentScope 2.0 is a production-ready, easy-to-use agent framework with essential abstractions that keep up with rising model capability.

这句话值得注意的有两处。一是 production-ready 不只是宣传词：2.0 的文档里，权限系统、沙箱隔离、多租户多会话服务、分布式部署都是一等公民，而不是外围话题。二是 "keep up with rising model capability"——官方设计思路是利用模型自身的推理和工具使用能力，而不是用严格的提示词和写死的编排去约束模型。这条线索贯穿整个 2.0 的 API 设计。

官方用四个词概括 2.0 的目标，每个都能对应到具体模块：

- **Secure**：工具级检查、人机协同确认、沙箱隔离，三层防护。
- **Efficient**：根据工具性质自动编排顺序或并发执行。
- **Flexible**：通过 middleware 在不改源码的前提下改 Agent 行为。
- **Complete**：开发 SDK、前端 UI、多租户多会话后端、分布式部署全栈覆盖。

---

## 二、先把概念讲清楚

Agent 框架的术语容易混。AgentScope 2.0 的概念分层比较清楚，先建立词汇表，后面所有章节都会用到这些名字。

| 概念 | 在 AgentScope 2.0 里的含义 |
| ------ | ------------------------ |
| **Agent** | 统一的 ReAct 循环引擎，接消息、调工具、出结果，核心只有这一个类 |
| **Msg** | 一轮完整对话消息，由类型化的内容块（Block）组成，可持久化 |
| **Event** | 流式交互的最小单位：文本增量、工具调用片段、权限请求都走事件流 |
| **Toolkit** | 工具容器，统一管理 Python 函数、MCP 工具和 Skill |
| **ToolGroup** | 工具分组，按需激活，内置 `basic` 组常驻 |
| **MCPClient** | MCP 服务器客户端，有状态与无状态两种连接方式 |
| **Skill** | Markdown 指令集，运行时从文件系统或沙箱加载 |
| **Middleware** | 挂在 Agent 生命周期各节点的拦截器，替代 1.0 的 Hook |
| **Permission** | 权限系统，对每次工具调用给出放行、拒绝或询问三种裁决 |
| **Workspace** | 工具执行环境，本地、Docker、E2B 等后端共用一套接口 |
| **Context** | 上下文治理：压缩、卸载、环境感知注入 |
| **AgentState** | 显式的 Agent 状态对象，取代 1.0 的 `state_dict` 机制 |
| **RealtimeAgent** | 实时语音 Agent，双向事件流（实验性） |
| **A2AAgent** | 连接远端 A2A 协议 Agent 的客户端适配器 |
| **Agent Service** | 基于 FastAPI 的多租户、多会话 Agent 后端服务 |

其中最需要纠正的一个惯性认知是：**2.0 里没有 `ReActAgent` 这个类了**。1.0 的 `ReActAgent` 被重构成统一的 `Agent` 类，ReAct 循环就是这个类的默认行为。同理，1.0 的 `AgentBase`、`UserAgent`、`MsgHub` 也都不在了。如果你按 1.0 的教程写 `from agentscope.agent import ReActAgent`，在 2.0 下会直接 ImportError。

### 2.1 设计思路

2.0 的架构可以拆成三步：

1. **把 Agent 做成一个无状态的循环引擎**：模型、工具、状态、配置全部从外部注入，引擎本身不持有会话数据。
2. **把横切能力做成可组合的模块**：权限、压缩、记忆、追踪都是 middleware 或独立配置对象，按需挂载。
3. **把服务化能力内置进框架**：多租户后端、IM 渠道、MCP/Skill 市场属于 `app` 模块，一条命令起服务。

这个顺序和很多框架相反：先有引擎和模块边界，再有服务化；而不是先做一个 Demo 编排器，等上生产再补治理能力。

---

## 三、架构分析：SDK、服务与生态三层

从源码结构和文档导航看，AgentScope 2.0 分三层：

```text
生态层
├─ AgentScope Runtime（生产运行时）/ Studio（可视化调试）
├─ Samples（官方示例）/ QwenPaw（个人 AI 助手产品）
│
服务层（src/agentscope/app）
├─ Agent Service：多租户多会话 HTTP 服务、调度、后台任务
├─ Channel：飞书 / 钉钉 / Discord / 自定义 IM 接入
├─ Hub：MCP 市场 / Skill 市场
│
SDK 层（building blocks）
├─ Agent / A2AAgent / RealtimeAgent
├─ Message & Event / Toolkit / Model / Formatter
├─ Context（压缩、卸载、环境感知）/ Long-Term Memory
├─ Permission / Workspace / Pipeline / RAG / Plan
```

SDK 层的模块划分可以直接在源码里验证。v2.0.8 的 `src/agentscope/` 下有 `agent`、`message`、`event`、`tool`、`model`、`formatter`、`mcp`、`middleware`、`permission`、`workspace`、`context` 相关配置、`skill`、`rag`、`realtime`、`pipeline`、`app`、`console` 等目录，与文档的 building blocks 一一对应。

### 3.1 核心库和生态库是两回事

| 仓库 | 角色 | Stars（2026-09-22） |
| ------ | ------ | ------ |
| **agentscope** | 核心 SDK，本文主角 | 约 3.2 万 |
| **agentscope-runtime** | 生产运行时：沙箱执行、部署、服务治理 | 约 900 |
| **agentscope-studio** | 开发向可视化工具 | 约 650 |
| **agentscope-samples** | 官方示例集合 | 约 350 |
| **QwenPaw** | 基于生态的个人 AI 助手产品（前身 CoPaw） | 约 3.5 万 |
| **ReMe** | Agent 记忆管理套件，可作 2.0 长期记忆后端 | 约 3.5 千 |

多语言方面，官方组织下还有 agentscope-java（约 5.7 千 Stars）、agentscope-typescript、agentscope-go。核心 Python SDK 之外的这些仓库独立发版，选型时不要把版本号混在一起看。

**SDK 负责"怎么开发 Agent"，服务层负责"怎么把 Agent 当服务跑起来"，生态负责产品和运维**。三层协同，不互相替代。

### 3.2 设计重点：Agent 先行，编排其次

很多框架从 DAG、状态图出发组织系统。AgentScope 的重心不同：它先把单个 Agent 的能力边界做扎实——工具调用、权限、上下文治理、状态管理、中断恢复——再谈多 Agent 组合。多 Agent 编排在 2.0 里反而是收敛的：1.0 的 `MsgHub`、`sequential_pipeline`、`fanout_pipeline` 全部移除，只留下一个实验性的 pipeline 模块，用固定逻辑把几个 Agent 串成一条事件流。

因此它更适合构建有自主性、有工具调用、有状态、需要上生产的 Agent 系统；如果你的需求只是把几个 LLM 调用按固定顺序串起来，纯代码或更轻的封装反而更直接。

---

## 四、功能特点：官方到底提供了什么

本节内容全部来自 v2.0.8 官方文档、README 和源码，不含推测。

### 4.1 Agent：一个类承载整个 ReAct 循环

官方文档对 `Agent` 的定义是"无状态的 reasoning-acting 循环引擎"。它统一整合模型、工具、权限、人机协同、上下文管理、中间件、状态管理和事件系统，公开方法只有四个：

| 方法 | 作用 |
| ------ | ------ |
| `reply()` | 运行循环，返回最终 `Msg` |
| `reply_stream()` | 同样运行循环，但以事件流形式逐步产出过程 |
| `observe()` | 只把消息加入上下文，不触发推理 |
| `compress_context()` | 手动触发上下文压缩 |

构造函数能看出 2.0 的全部设计重心：

```python
Agent(
    name="Friday",
    system_prompt="...",
    model=...,                # 聊天模型，必选
    toolkit=...,              # 工具集，可选
    middlewares=[...],        # 中间件列表，可选
    state=...,                # AgentState，显式状态
    offloader=...,            # 上下文卸载器
    model_config=...,         # 模型兜底与重试
    context_config=...,       # 压缩与截断
    react_config=...,         # 推理-行动循环参数
    injection_config=...,     # 运行时状态注入
)
```

几个值得注意的能力，全部有文档明确支持：

- **结构化输出**：`reply()` 接受 `structured_schema`，最终消息的 `structured_output` 字段带校验后的结果。
- **中断与恢复**：正在运行或暂停的 Agent 可以被干净地停下，再从一致状态恢复。
- **人机协同（HITL）**：权限询问通过 `RequireUserConfirmEvent` 走事件流，Agent 暂停等待用户确认或外部执行结果，收到 `UserConfirmResultEvent` 后继续。
- **工具编排**：模型一轮产出的多个工具调用，框架按工具性质自动编排为顺序或并发执行。
- **纯生产者**：1.0 的 `print` 接口被弃用，Agent 只产出事件，渲染交给外部（比如 Console）。

### 4.2 工具系统：Toolkit 统一管理四类东西

2.0 的 `Toolkit` 把 Python 函数、MCP 工具、Skill 和工具组都收进一个容器，Agent 只看这一个入口。

内置工具已经很接近一个编码 Agent 的标配：

```python
from agentscope.tool import Toolkit, Bash, Grep, Glob, Read, Write, Edit

toolkit = Toolkit(tools=[Bash(), Grep(), Glob(), Read(), Write(), Edit()])
```

另有 `TaskCreate` / `TaskGet` / `TaskList` / `TaskUpdate` 四个任务管理工具，配合 Plan 模块做任务追踪。

工具组（ToolGroup）是 2.0 的新设计：工具可以分组，按需激活，名为 `basic` 的组常驻；Agent 自带一个 `ResetTools` 元工具，可以在运行时自己切换要用的工具组。这个设计缓解了工具太多时的上下文膨胀——不需要的工具不进 prompt。

Skill 是 Markdown 指令集，`LocalSkillLoader` 支持从目录加载并监控更新，Skill 还能打包成 ToolGroup 参与按需激活。

### 4.3 MCP：一个 MCPClient 类收编所有连接方式

1.0 里 MCP 客户端分成 `HttpStatelessClient` 等多个类。2.0 收敛为统一的 `MCPClient`，配置用声明式的 `StdioMCPConfig` / `HttpMCPConfig`：

```python
from agentscope.mcp import MCPClient, HttpMCPConfig
from agentscope.tool import Toolkit

client = MCPClient(
    name="search",
    is_stateful=False,
    mcp_config=HttpMCPConfig(url="https://api.search.com/mcp"),
)

toolkit = Toolkit(mcps=[client])
```

两种连接方式的边界文档写得很清楚：

| 方式 | 传输 | 生命周期 |
| ------ | ------ | ------ |
| 有状态 | STDIO 或 HTTP | 持久会话，显式 `connect()` / `close()` |
| 无状态 | 仅 HTTP | 每次工具调用临时建会话，无需管理生命周期 |

三个工程细节值得留意：

- MCP 工具注册后带命名空间前缀 `mcp__{server_name}__{tool_name}`，避免和本地工具撞名。
- 带 `readOnlyHint` 注解的工具会被权限系统识别为只读：`EXPLORE` 和 `ACCEPT_EDITS` 模式下自动放行，`DEFAULT` 模式仍走询问。
- 令牌轮换不需要重建客户端，`set_runtime_headers()` 可以运行时替换 HTTP 头。

`enable_tools` / `disable_tools` 参数可以在客户端层面过滤暴露给 Agent 的工具子集。

### 4.4 上下文管理：压缩、截断、卸载三件事

长任务跑久了上下文必然膨胀，2.0 用 `ContextConfig` 治理，机制分三层：

**自动压缩**。每次推理前检查 token 用量，超过 `trigger_ratio × 模型上下文` 就触发：旧消息交给模型生成结构化摘要，五个字段固定——`task_overview`、`current_state`、`important_discoveries`、`next_steps`、`context_to_preserve`——摘要替换掉被压缩的消息，最近消息按 `reserve_ratio` 保留，工具调用与结果对不会被拆散。

**工具结果截断**。单条工具结果超过 `tool_result_limit` token 就截断；上下文里的图片数量由 `max_image_num` 控制（默认 5）。更大的卸载需求交给 `Offloader`：被压缩的内容和超大工具结果可以落盘，Agent 需要时再读回来。

**Agentic 压缩**。自动压缩的问题在于触发时机经常落在工作半途，摘要容易丢细节。把 `compression_tool_enabled` 设为 `True`，Agent 会得到一个 `CompressContext` 工具，自己选择在两段工作之间主动压缩。

压缩摘要失败时默认回退为截断最旧消息并留一条说明（`compression_fallback_to_truncation=True`），保证 Agent 不中断；设为 `False` 则直接报错，宁可失败也不悄悄丢信息。

此外还有环境感知注入：时间、任务进度、上下文用量会在推理前注入上下文，让 Agent 对"现在几点、做到哪一步、还剩多少额度"有感知。

### 4.5 长期记忆：从内置模块变成中间件

这是 1.x 用户最需要注意的变化：**1.0 的 `memory` 模块在 2.0 里被弃用**，官方 changelog 给的理由是它与 Agent 逻辑耦合太紧。跨会话记忆改为通过 middleware 实现，目前官方支持三种：

| 实现 | 代码入口 | 说明 |
| ------ | ------ | ------ |
| **Agentic Memory** | `AgenticMemoryMiddleware` | 原生实现，基于 Markdown 文件，Agent 自主创建、维护、检索 |
| **ReMe** | `ReMeMiddleware` | 由 ReMe 仓库提供，从对话中自动提取记忆并写回 |
| **Mem0** | `Mem0Middleware` | 接入 mem0 的即插即用后端 |

Agentic Memory 的机制值得展开，因为它和 Claude Code 等编码 Agent 的记忆方案思路一致：Agent 用内置的 `Read` / `Write` / `Edit` 工具维护一组 Markdown 记忆文件，每个文件带 frontmatter（`name`、`description`、`type`）；一个固定的 `MEMORY.md` 只做索引，自动注入系统提示词，这就是"渐进式披露"——先给 Agent 看目录，需要哪条再去读哪篇。

检索是异步的：`reply` 调用时中间件起一个异步任务，由 LLM 按当前输入挑相关文件，在推理开始前的检查点把结果作为 `HintBlock` 注入。官方文档也明确标注了边界：如果这轮回复没有进入后续推理轮次（比如模型没发起工具调用），检索结果可能来不及注入这一轮。

`backend` 参数让同一套记忆跑在本地、Docker 或 E2B 沙箱里，默认 `LocalBackend`。

RAG 方面，2.0 把 RAG 和长期记忆统一进一个模块，官方说明迁移仍在进行中，知识库、文档读取器等能力会在 2.0 架构上回归。现阶段 `rag` 目录已存在于源码，文档里也有 RAG building block 页面，但选型时建议确认当前版本的具体完成度。

### 4.6 Realtime 与 TTS：实验性的语音线

`RealtimeAgent` 是语音 Agent：一端接实时模型，一端接音频传输，中间是轮流说话状态机。它和普通 `Agent` 的本质区别是双向——音频持续流入、事件持续流出，没有"请求 → 回复"的边界。README 的 News 显示 2026-09 已支持 DashScope、OpenAI、Gemini、xAI 四家实时 API。

官方文档在页面顶部标注了警告：**Realtime 是实验性能力，接口可能变化**。当前支持 speech-to-speech 实现（音频直接进出端到端语音模型）；级联方案（ASR + LLM + TTS）标注"coming soon"。已实现的能力包括：

- VAD 轮次检测（用供应商自带的，或插入本地 VAD）；
- Barge-in：用户开口即打断当前回复，上下文只保留用户真正听到的那部分；
- 工具调用走 `Toolkit` 和权限系统，语音对话中也能执行工具；
- HITL 确认不暂停音频流；
- 会话断开后自动重连，历史保留在 Agent 状态里。

TTS 则是 Model 层的 building block，提供统一合成接口，分标准与实时流式两种模式。RealtimeAgent 管会话与轮次，TTS 管文本到音频的转换，两条线相邻但各管各的。

### 4.7 A2A：正式支持的远端 Agent 接入

A2A（Agent2Agent）是 Google 提出的 Agent 互联协议。2.0 的 README News 显示 2026-09 正式支持，通过 `A2AAgent` 作为客户端连接任何实现了 A2A 1.0 以上的远端 Agent（对端只提供 0.3 时，官方 SDK 自动回退到兼容传输）。

`A2AAgent` 的自我定位很克制，源码 docstring 原话是"intentionally provides Agent-like interaction methods without inheriting Agent"——刻意只提供类 Agent 的交互方法而不继承 `Agent` 类。它只是远端 Agent 的本地代理，自己不持有任何逻辑。官方文档给出了与本地 Agent 的差异表：

| 能力 | 本地 `Agent` | `A2AAgent` |
| ------ | ------ | ------ |
| `reply()` / `reply_stream()` | 支持 | 发给远端，流式转译回来 |
| `observe()` | 支持 | 先缓冲，随下次 `reply()` 一并发送 |
| `compress_context()` | 支持 | 空操作，上下文由远端维护 |
| 模型、工具、中间件、权限、结构化输出 | 支持 | 不提供，全部由远端决定 |
| 中断恢复、HITL | 支持 | 不支持；远端等待输入会表现为一次普通回复 |

依赖单独装：`pip install "agentscope[a2a]"`。连接从获取 Agent Card 开始（远端的自描述 JSON），实例是一次性的——退出上下文管理器时关闭客户端，不能重开。仓库的 `examples/a2a` 有完整的两端示例。

这部分的价值在于诚实：明确告诉你协议边界在哪，而不是把远端 Agent 包装成本地能力的完全等价物。

### 4.8 权限系统：每次工具调用都要过一道裁决

权限系统是 2.0 新增的，拦截每一次工具调用，产出三种裁决之一：放行、拒绝、询问用户。裁决由三个组件协同：

- **Permission Rule**：按工具和调用参数写 allow/deny/ask 模式，优先级最高；
- **Permission Mode**：全局策略，决定哪些裁决点生效、兜底行为是什么；
- **工具级检查**：每个工具对实际入参做动态分析——只读识别、危险路径保护、工作目录自动放行，由工具自己实现 `check_read_only()` / `check_permissions()`。

全局模式五种：`DEFAULT`（兜底询问）、`ACCEPT_EDITS`（工作目录内编辑放行）、`EXPLORE`（只读快速放行，其余拒绝）、`BYPASS`（全部放行）、`DONT_ASK`（一切询问转为拒绝）。每种模式下的决策矩阵在文档里有完整表格，六层决策点自上而下，第一个有答案的生效。

一个贴心的设计：ASK 裁决会附带给用户自动生成的 suggested rules，用户接受后规则持久化，同样的调用下次不再打扰。

### 4.9 Agent as Service：从脚本到服务只差一个模块

`app` 模块是 2.0 把"生产部署"做进框架的部分。核心是 `create_app` FastAPI 工厂，起一个多租户、多会话的 Agent HTTP 服务：agent、chat、model、credential、session、schedule、workspace 等路由齐备，事件流走 SSE，存储支持 Redis，生命周期由 SessionManager、SchedulerManager 等组件托管。

围绕服务层还有几块：

- **Agent Team**：leader Agent 通过内置团队工具生成并协调 worker Agent；
- **Channel**：把服务里的 Agent 接到飞书、钉钉、Discord，自定义平台实现 `ChannelBase` 即可；消息路由决定哪条消息交给哪个 Agent、进哪个会话；
- **MCP & Skill Hub**：让用户从注册表安装 MCP 服务器和 Skill（内置 GitHub MCP Registry 与 ClawHub 源），各自带凭证管理；
- **RAG Service**：一键起多租户分布式 RAG 服务。

这一层意味着：如果你想给 Agent 配一个带用户体系的 HTTP 后端、再接上企业 IM，这些不再需要自己从零搭——框架自带，或者至少自带了参考实现。

### 4.10 1.0 能力去向速查

| 1.0 能力 | 2.0 现状 |
| ------ | ------ |
| `ReActAgent` / `AgentBase` | 重构为统一 `Agent` 类 |
| `MsgHub`、`sequential_pipeline`、`fanout_pipeline` | 移除；新的 pipeline 模块（实验性）提供固定编排与 `GoalPipeline` |
| `memory` 模块（短时/长期/压缩三层） | 弃用；长期记忆改为 middleware，压缩并入 Context |
| `Formatter` 手动配置 | 集成进模型类，每个供应商有默认 formatter，仍可显式指定 |
| Hook 机制 | 改为 middleware 系统，`TracingMiddleware` 接管 OpenTelemetry |
| `state_dict` / `load_state_dict` | 改为显式 `AgentState` |
| Tuner（强化学习调优） | 核心库移除；RL 训练能力在组织下的 Trinity-RFT 等仓库 |
| `ImageBlock` / `AudioBlock` / `VideoBlock` | 统一为 `DataBlock`（带 `media_type`） |
| `ToolUseBlock` | 更名 `ToolCallBlock`，块上增加状态字段 |

---

## 五、使用说明：怎么从 0 到 1 跑起来

### 5.1 安装

Python 3.11+，官方推荐用 uv 安装：

```bash
uv pip install agentscope
```

验证：

```python
import agentscope
print(agentscope.__version__)
```

从源码安装：

```bash
git clone -b main https://github.com/agentscope-ai/agentscope.git
cd agentscope
uv pip install -e .
```

可选依赖用 extra 安装，比如 `agentscope[full]`（模型 API、工具函数等全量依赖）和 `agentscope[a2a]`（A2A 协议支持）。

### 5.2 第一个 Agent：reply 与 reply_stream

官方 Quickstart 的最小示例，值得逐行看——模型、凭证、工具、消息、两种运行方式都在里面：

```python
import asyncio
import os

from agentscope.agent import Agent
from agentscope.credential import DashScopeCredential
from agentscope.event import EventType
from agentscope.message import UserMsg
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit, Bash, Read, Write, Edit


async def main() -> None:
    agent = Agent(
        name="Friday",
        system_prompt="You are a helpful assistant named Friday.",
        model=DashScopeChatModel(
            credential=DashScopeCredential(
                api_key=os.getenv("DASHSCOPE_API_KEY"),
            ),
            model="qwen-plus",
        ),
        toolkit=Toolkit(tools=[Bash(), Read(), Write(), Edit()]),
    )

    user_msg = UserMsg(name="user", content="Hello, who are you?")

    # 方式一：直接等最终回复
    reply_msg = await agent.reply(user_msg)

    # 方式二：流式消费事件
    async for event in agent.reply_stream(user_msg):
        match event.type:
            case EventType.TEXT_BLOCK_DELTA:
                ...  # 文本增量，追加到 UI
            case EventType.TOOL_CALL_START:
                ...  # 工具调用开始
            case _:
                ...  # 思考块、工具结果、结束事件等


asyncio.run(main())
```

和 1.0 的写法对比，有三个变化最能说明 2.0 的取向：凭证从模型参数里拆出来单独成模块（`Credential`）；消息从字符串变成带角色的 `UserMsg` / `AssistantMsg` / `SystemMsg` 工厂方法，内容由类型化块组成；流式输出从"打印文本"变成"分发事件"，事件类型覆盖思考、工具调用、权限请求的全过程。

### 5.3 用 Console 调试：不用自己写事件循环

终端调试不需要手写事件分发，`launch_console` 一步到位（README 官方示例）：

```python
import asyncio
import os

from agentscope.agent import Agent
from agentscope.console import launch_console
from agentscope.tool import Toolkit, Bash, Grep, Glob, Read, Write, Edit
from agentscope.credential import DashScopeCredential
from agentscope.model import DashScopeChatModel


async def main() -> None:
    agent = Agent(
        name="Friday",
        system_prompt="You're a helpful assistant named Friday.",
        model=DashScopeChatModel(
            credential=DashScopeCredential(
                api_key=os.environ["DASHSCOPE_API_KEY"]
            ),
            model="qwen3.6-plus",
        ),
        toolkit=Toolkit(
            tools=[Bash(), Grep(), Glob(), Read(), Write(), Edit()],
        ),
    )

    # 流式输出、工具调用确认、Ctrl+C 中断都由 console 处理
    await launch_console(agent)


asyncio.run(main())
```

这是上手 AgentScope 成本最低的路径：装好库、配一个 API Key，就能在终端里和一个带完整工具链的 Agent 对话，直观看到 ReAct 循环怎么转。

### 5.4 注册远端 MCP 工具

有状态连接（以 STDIO 为例）需要先 `connect()` 再构造 Toolkit：

```python
from agentscope.mcp import MCPClient, StdioMCPConfig
from agentscope.tool import Toolkit

client = MCPClient(
    name="filesystem",
    is_stateful=True,
    mcp_config=StdioMCPConfig(
        command="mcp-server-filesystem",
        args=["--root", "/my/project"],
    ),
)

await client.connect()
toolkit = Toolkit(mcps=[client])
```

无状态 HTTP 连接则不需要生命周期管理，构造后直接交给 Toolkit（见 4.3 节示例）。注册完成后，MCP 工具以 `mcp__{server}__{tool}` 的名字出现在 Agent 的工具列表里，和本地工具没有使用上的区别。

### 5.5 加上长期记忆

用 `AgenticMemoryMiddleware` 给 Agent 装上跨会话记忆，示例改编自官方文档，`my_chat_model` 换成你已有的任意聊天模型实例即可：

```python
from agentscope.agent import Agent
from agentscope.middleware import AgenticMemoryMiddleware
from agentscope.tool import Read, Write, Edit, Toolkit

workdir = "/tmp/agentscope_ltm_demo"

agent = Agent(
    name="assistant",
    system_prompt="You are a helpful assistant.",
    model=my_chat_model,
    toolkit=Toolkit(tools=[Read(), Write(), Edit()]),
    middlewares=[AgenticMemoryMiddleware(workdir=workdir)],
)

await agent.reply("记住我住在杭州，喜欢简洁的中文回答。")

# 重启进程后，用同一个 workdir 重建 Agent，记忆还在
new_agent = Agent(
    name="assistant",
    system_prompt="You are a helpful assistant.",
    model=my_chat_model,
    toolkit=Toolkit(tools=[Read(), Write(), Edit()]),
    middlewares=[AgenticMemoryMiddleware(workdir=workdir)],
)
await new_agent.reply("还记得我的位置和回答偏好吗？")
```

生产环境建议把 `workdir` 换成 Docker 或 E2B 沙箱后端（`backend` 参数），并按安全策略配置写权限，示例中放开的 `ACCEPT_EDITS` 模式只适合本地试验。

### 5.6 Formatter：大多数时候不用管，直到多 Agent

1.0 里 Formatter 是必须显式传入的四件套之一；2.0 把它集成进了模型类，每个供应商自带默认 formatter，单 Agent 场景完全不用管。

它仍然存在的场景是**多身份对话**：默认 formatter 把消息映射到裸的 `user`/`assistant` 角色，名字会被丢掉，多个说话者在模型眼里无法区分。这时换对应供应商的 `MultiAgentFormatter`，历史会被合并成带名字的单份转录（`Alice: ...`、`Bob: ...`）：

```python
from agentscope.model import DashScopeChatModel
from agentscope.credential import DashScopeCredential
from agentscope.formatter import DashScopeMultiAgentFormatter

model = DashScopeChatModel(
    credential=DashScopeCredential(api_key="YOUR_API_KEY"),
    model="qwen-max",
    formatter=DashScopeMultiAgentFormatter(),
)
```

DashScope、OpenAI、Anthropic、Gemini、Ollama、DeepSeek、Moonshot、XAI 八家都有 Chat / MultiAgent 一对 formatter。

---

## 六、原理分析：为什么它比"提示词 + 几个函数"更像工程框架

### 6.1 消息与事件构成两级数据结构

官方文档把 `Msg` 和 `Event` 并列为两个基本数据结构：Msg 是通信与持久化的单位，Event 是前端交互与流式的单位。关键约束是：**一次 `reply` 产生的全部事件，累积起来恰好等于一条 assistant `Msg`**。这条约束保证了消息状态永远可以从事件流完整重建——前端断线重连、会话回放、事件溯源都建立在这个不变量上。

`Msg` 本身也比"一段文本"重得多：`id`、`role`、类型化的 `content` 块列表、`created_at` / `finished_at` 时间戳、token `usage`、`finished_reason`（`completed` / `interrupted` / `exceed_max_iters` / `error`）、结构化输出与错误信息都有字段。做计费、审计、可观测性时不需要再额外埋点。

内容块全部继承自 Pydantic `BaseModel`，类型与角色约束在构造时强制：user 消息只能有文本和数据块，system 只能有文本，assistant 才能包含思考块和工具调用。错误的消息结构在构造时就报错，而不是在模型 API 调用时才炸。

### 6.2 无状态引擎 + 显式状态

`Agent` 类自己不保存会话数据，状态全部放在注入的 `AgentState` 里。这个分离直接支撑了 2.0 的几个卖点：多租户服务里，一个引擎实例可以服务任意多会话；中断恢复就是保存和恢复状态对象；权限上下文也挂在状态上，随状态一起持久化。

1.0 的 `state_dict` / `load_state_dict` 之所以被弃用，就是因为隐式状态管理在大规模场景下说不清楚"哪些东西算状态"。2.0 把答案写进了类型系统。

### 6.3 权限是循环内的一等步骤

在 `Agent` 的主循环里，权限检查发生在工具执行之前，裁决结果是 `ALLOW` / `DENY` / `ASK` 三者之一：`ASK` 时 Agent 暂停，发出 `RequireUserConfirmEvent`，等用户结果事件回来再继续。也就是说权限不是部署时的外挂开关，而是 ReAct 循环内部的一个环节——这也是 HITL 能和工具调用无缝衔接的原因。

### 6.4 Middleware 取代 Hook

1.0 的 Hook 机制（`pre_reply`、`post_reply` 等固定几个点）升级为 middleware 系统，支持七个挂点：reply、reasoning、acting、model call、permission check、context compression、system prompt。长记忆、RAG、追踪（TracingMiddleware）、TTS 都以 middleware 形式接入，横切能力与 Agent 主逻辑解耦——这也是 1.0 memory 模块被弃用的直接原因：它耦合在 Agent 逻辑里，改不动。

### 6.5 协议接入是能力并入，不是外挂

MCP 工具最终进入 Toolkit，命名空间隔离；远端 Agent 通过 `A2AAgent` 进入统一的 reply/reply_stream 接口；实时音频进入统一事件流。对外协议再多样，对内都是同一套消息与事件模型。这个一致性是它敢于自称"essential abstractions"的底气。

---

## 七、源码分析：从公开源码能读出什么设计取舍

以下基于 v2.0.8 tag 的源码。

### 7.1 核心源码入口一览

| 路径 | 角色 | 读源码时关注什么 |
| ------ | ------ | ------ |
| `src/agentscope/agent/_agent.py` | 统一 Agent 类，单文件约 15 万字符 | ReAct 循环、批量工具执行、权限检查、压缩 |
| `src/agentscope/agent/_a2a_agent.py` | A2A 客户端适配器 | Part 到 Block 的转译、会话生命周期 |
| `src/agentscope/agent/_realtime/` | 实时 Agent | 轮流说话状态机、传输抽象 |
| `src/agentscope/pipeline/` | 编排 | `PipelineProtocol` 协议、`GoalPipeline` |
| `src/agentscope/workspace/` | 执行环境 | 九种后端共用一套 Agent 侧接口 |
| `src/agentscope/middleware/` | 中间件 | 长期记忆、追踪、RAG、预算 |

### 7.2 `_agent.py`：一个类装下整个循环

v2.0.8 的 `_agent.py` 约 15 万字符，`reply` / `reply_stream` / `observe` / `compress_context` 四个公开方法之外，循环的实现全部是私有方法：`_reasoning_impl`、`_acting`、`_batch_tool_calls`、`_execute_sequential_tool_calls`、`_execute_concurrent_tool_calls`、`_check_permission`、`_compress_context_impl`、`_inject_runtime_state`。文件顶部定义了内置压缩工具名 `_COMPRESSION_TOOL_NAME = "CompressContext"`，与文档描述的 agentic 压缩对上。

单一文件承载全部循环逻辑，好处是循环里的顺序、状态转换、异常路径一眼可以看全；代价是这个文件会成为整个库最热的修改区。读它的时候建议从 `_reply_impl` 入口往下追，配合文档的主循环流程图。

### 7.3 `_a2a_agent.py`：把限制写在 docstring 里

`A2AAgent` 的类文档开篇就说明它"刻意不继承 Agent"，只持有远端会话的 `context_id` 和 `task_id`，状态放在 `A2AAgentState`；"adapter owns its A2A client and closes it in aclose, so it is single-use"——实例关闭后不可重用。这些限制都是设计决定，不是没做完：本地 Agent 拥有模型、工具和推理循环，适配器把这些全权交给远端，自己只管协议转译。

### 7.4 `_realtime/`：三种生命周期刻意分开

`RealtimeAgent` 的 docstring 把三种生命周期讲得非常清楚：Agent 拥有模型会话和状态；传输层归创建者所有；一次 `reply_stream` 调用只在两者都存活期间借用它们。好处写在明面上——客户端断开重连不丢模型会话，模型会话在长静默后超时重建也不碰传输层。模块里还有 `TurnAggregator` 和 `TurnMetrics` 两个伴生类，分别处理轮次聚合与轮次指标。

### 7.5 `workspace/`：八种沙箱，一套接口

源码目录下能看到 local、docker、applecontainer、bubblewrap、e2b、k8s、opensandbox、daytona 八种沙箱实现加 MCP 网关。文档里 Workspace 的承诺是"给 Agent 一个可以行动和持久化的执行环境"，所有后端暴露给 Agent 的工具接口一致，切换只换构造参数。多租户场景由对应的 WorkspaceManager 提供 agent 级隔离。

---

## 八、开发扩展：如果你要二次开发，应该从哪里下手

### 8.1 扩展点速查

| 目标 | 扩展点 |
| ------ | ------ |
| 改 Agent 行为（不改源码） | `MiddlewareBase` 的七个挂点 |
| 自定义本地工具 | 继承 `ToolBase` 或用 `FunctionTool` 包装函数 |
| 接远端工具 | `MCPClient` + `Toolkit(mcps=[...])` |
| 自定义模型兼容逻辑 | `FormatterBase` 子类，传入模型构造 |
| 自定义执行环境 | 实现 Workspace 接口，或选用内置八种沙箱后端 |
| 接远端 Agent | `A2AAgent` |
| 做实时语音 | `RealtimeAgent` + 传输层 |
| 服务化部署 | `app.create_app` 或 agentscope-runtime |

### 8.2 Middleware 是首选扩展点

大多数"我想改 Agent 的行为"类需求，正确做法是写 middleware 而不是继承 `Agent`。七个挂点覆盖了请求全链路，官方自己的长期记忆、RAG、追踪、TTS 都是这么接进去的——跟随官方用法，升级时踩坑最少。

### 8.3 什么时候需要 Runtime

核心 SDK 加 `app` 模块已经能起多租户服务。如果你的需求更进一步——大规模沙箱调度、分布式部署、更重的服务治理——这时候看 **agentscope-runtime**。它独立发版，和核心 SDK 的版本号没有对齐关系，选型时分开评估。

---

## 九、使用场景：它适合什么，不适合什么

### 9.1 适合

- **带工具调用的通用助手**：`Agent` + `Toolkit` 是天然组合，权限与 HITL 开箱即用。
- **编码 / 运维类 Agent**：内置 Bash、Read、Write、Edit、Grep、Glob，配合 Workspace 沙箱就是参考实现。
- **要上生产的服务**：多租户多会话、SSE 事件流、IM 渠道、Hub 生态，服务层现成。
- **跨会话个性化**：Agentic Memory / ReMe / Mem0 三条长期记忆路线可选。
- **实时语音**：speech-to-speech 路线已通，能接受实验性接口的话。

### 9.2 不太适合

- **完全确定性的固定流程**：用纯函数或工作流引擎更简单，Agent 的抽象成本不划算。
- **单次调用、无状态的小脚本**：SDK 的概念面（状态、权限、事件）对这种需求偏重。
- **重度依赖 MsgHub 式自由多 Agent 对话的团队**：2.0 的编排收敛为固定逻辑 pipeline（且实验性），需要自由广播模式的得自己搭或观望。
- **一定要用 1.x API 的存量项目**：官方明确不建议混用 1.x/2.x API，迁移是必选项。

---

## 十、从入门到精通：推荐学习路径

### 10.1 新手：跑通最小闭环

1. 装库，跑 5.3 节的 Console 示例，在终端里和一个带工具的 Agent 对话。
2. 读 Key Concepts 页，把 `Msg` / `Event` / `Toolkit` / `Agent` 四个词的关系理顺。
3. 自己写一个 Python 函数工具注册进 Toolkit，观察工具调用在事件流里的样子。

### 10.2 进阶：治理与记忆

4. 打开权限系统，体验 `DEFAULT` 模式下工具调用被询问、suggested rule 被接受后不再打扰的过程。
5. 配置 `ContextConfig`，用一个超长任务观察自动压缩生成的五字段摘要。
6. 挂上 `AgenticMemoryMiddleware`，跨进程验证记忆的消失与重现。

### 10.3 专家：协议与生产

| 阶段 | 重点 |
| ------ | ------ |
| 服务化 | `app.create_app`、session 管理、Channel 接入 |
| 协议 | MCP Hub、A2A 双端示例 |
| 实时 | `RealtimeAgent`、传输层自定义 |
| 规模化 | agentscope-runtime、WorkspaceManager、分布式部署 |

### 10.4 自测清单

下面 8 个问题都能答上来，说明你真的入门了：

1. `reply` 和 `reply_stream` 的关系是什么？为什么说消息可以从事件流重建？
2. 2.0 里 `ReActAgent` 去哪了？
3. MCP 工具为什么带命名空间前缀？`readOnlyHint` 和权限系统怎么联动？
4. 上下文压缩的三个字段比例（trigger / reserve / buffer）各自管什么？
5. 1.0 的 `memory` 模块为什么被弃用，长期记忆现在怎么接？
6. `A2AAgent` 为什么刻意不继承 `Agent`？哪些能力因此不可用？
7. 权限系统的五种模式在兜底行为上有什么差别？
8. `RealtimeAgent` 为什么要把 Agent、传输、`reply_stream` 调用三种生命周期分开？

---

## 十一、常见误区与排查建议

### 11.1 按 1.0 教程写代码，ImportError

最常见的一条。2.0 移除或改名了大量 1.0 API（见 4.10 节速查表）。排查方法：先 `pip show agentscope` 确认版本；看文档时认准域名——`docs.agentscope.io` 是 2.0，`doc.agentscope.io` 是 1.0 旧站。

### 11.2 找不到 `MsgHub`

2.0 的多 Agent 编排只有 pipeline 模块（实验性）和 `GoalPipeline`，自由广播模式没有对应物。如果业务真的需要 MsgHub 语义，要么基于事件流自己实现，要么重新评估是否真的需要自由广播——固定逻辑编排能覆盖大多数场景，还更容易调试。

### 11.3 以为长期记忆还是 `InMemoryMemory` + `Mem0LongTermMemory`

那是 1.0 的类。2.0 里短时上下文就是 Agent 的上下文列表，长期记忆用 `AgenticMemoryMiddleware` / `ReMeMiddleware` / `Mem0Middleware` 挂载，压缩是 `ContextConfig` 的事。三件事三个入口，别再找一个统一的 Memory 类。

### 11.4 把 Realtime 当稳定 API 用

官方文档在 Realtime 页面顶部明确标注实验性、接口可能变化。生产使用要锁定版本、做好接口变更预案。

### 11.5 以为 A2A 接上就等于本地 Agent

`A2AAgent` 没有远端的结构化输出、中断恢复和 HITL，压缩也是空操作。把远端 Agent 当一个只能对话的黑盒来设计交互，才不会在集成时踩坑。

### 11.6 能回答问题就是生产级

不是。状态管理、中断恢复、权限治理、工具失败处理、可观测性、部署安全，这些才是"生产级"的实际内容。AgentScope 的价值在于把这些做进了框架默认值——但你要真的去配置它们，而不是只调一个 `reply()`。

---

## 十二、资源与延伸阅读

| 资源 | 链接 |
| ------ | ------ |
| GitHub 仓库 | [agentscope-ai/agentscope](https://github.com/agentscope-ai/agentscope) |
| 2.0 官方文档（stable） | [docs.agentscope.io](https://docs.agentscope.io/stable/en/index) |
| 官方示例 | [examples 目录](https://github.com/agentscope-ai/agentscope/tree/main/examples) |
| 论文 | [arXiv 2402.14034](https://arxiv.org/abs/2402.14034)（AgentScope：以消息交换为核心的灵活多 Agent 平台） |
| 论文 | [arXiv 2508.16279](https://arxiv.org/abs/2508.16279)（AgentScope 1.0：开发者中心的 Agentic 应用框架） |
| 生产运行时 | [agentscope-runtime](https://github.com/agentscope-ai/agentscope-runtime) |
| 社区 | [Discord](https://discord.gg/eYMpfnkG8h) |

建议阅读顺序：README 建立整体认知 → Key Concepts 理顺术语 → Agent 的 overview / configure / run 三篇 → Context 与 Long-Term Memory → 最后按需读 A2A、Realtime、Agent Service。每篇文档页都提供 Markdown 版本（URL 加 `.md`），适合让 AI 助手带着你读。

---

## 十三、总结

AgentScope 2.0 把 Agent 工程化里最难的那部分——状态、权限、上下文、记忆、协议、部署——从"开发者自己想办法"变成了"框架的默认值"。统一 `Agent` 类收敛了 1.0 的抽象分层，事件系统把可观测性和 HITL 变成基础设施，middleware 把横切能力从主逻辑里摘干净，`app` 模块把服务化的门槛压到一条命令。

代价是 1.x 用户的迁移成本，以及文档、教程、生态案例新旧并存带来的辨别成本。判断标准很简单：认准 v2.0.8，认准 `docs.agentscope.io`，本文的类名和代码都可以直接对照。

如果你想写的是一次性 LLM 脚本，它的抽象偏重；如果你想构建的是可治理、可恢复、可部署的 Agent 系统，这套设计正好对得上。

---

## 相关话题标签

AgentScope、AI Agent、ReAct、MCP、A2A、多智能体、Agent Engineering

## 来源

- [GitHub](https://github.com/agentscope-ai/agentscope)
- [Docs（2.0 stable）](https://docs.agentscope.io/stable/en/index)
