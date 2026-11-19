---
title: "AG-UI：给 Agent 与前端之间补一层事件协议，把「流式输出」从各家私活变成公共契约"
date: "2026-11-20T01:27:19+08:00"
slug: "ag-ui-protocol-agent-user-interaction-protocol"
description: "AG-UI 是 Agent 与前端之间的双向事件协议，用生命周期、文本消息、工具调用、状态同步、子智能体等事件类别统一各家框架的私有接线方式。本文拆解其事件分类、状态双轨同步、1.0 规范冻结与向后兼容边界，并指出它与 MCP、A2A 的分工关系。"
draft: false
categories: ["技术笔记"]
tags: ["AG-UI", "AI Agent", "事件协议", "前端集成", "SSE"]
github_repo: "ag-ui-protocol/ag-ui"
source_key: "gh:ag-ui-protocol/ag-ui"
---

## 核心判断

前端要接一个 Agent，麻烦的不是模型能力，而是接线。Agent 会流式吐 token、会在响应中途调工具、会改共享状态、会在需要人确认时挂起、还会派生子智能体——每家框架对这些的编码方式都不一样。你用 LangGraph 写的 Agent，换成 CrewAI 就要重写一遍前端事件处理。

AG-UI 的判断是：这套接线值得有一个公共协议。它不试图发明新的 Agent 能力，而是把「Agent 运行时 ↔ 用户界面」这一段标准化，让同一个 Agent 能不改前端地接到 Web、Mobile、终端、Slack 上。

值得肯定的是 1.0 的处理方式。协议冻结了规范、SDK 从 JSON Schema 生成、并且明确写下了 0.x 与 1.0 双向兼容的边界与废弃时间表——这比大多数「刚出 1.0 就把老 API 砍了」的协议库要克制。

不过得先把边界说清楚：**AG-UI 解决的是传输与事件语义，不是智能体框架本身**。它不负责 agent 怎么规划、怎么调工具、怎么决策，那是 MCP（给 agent 工具）和 A2A（agent 之间协作）以及各家框架自己的事。如果你的场景只有一个固定流程的 chatbot，这套协议的收益可能撑不起它的复杂度。

截至 2026 年 11 月 20 日，这个仓库有 20587 stars、2120 forks，TypeScript 为主，MIT 许可，2025 年 5 月创建，11 月 17 日仍在提交（1.0 之后的发布分支）。

## AG-UI 在协议栈里的位置

README 用了一张图讲清了三个协议的关系，这个划分是理解 AG-UI 的关键前提：

| 协议 | 解决的问题 | 负责的边界 |
|---|---|---|
| **MCP** | Agent 拿到什么工具和上下文 | Agent ↔ 工具/数据 |
| **A2A** | Agent 如何与其他 Agent 协作 | Agent ↔ Agent |
| **AG-UI** | Agent 如何与用户交互 | Agent ↔ 应用界面 |

一个 agent 常常同时用上这三种。AG-UI 也不排斥其它「生成式 UI 规范」——比如 Google 的 A2UI、MCP Apps、Open-JSON-UI，这些描述的是「agent 想展示什么 UI」，而 AG-UI 是**把这些 payload 连同其它一切一起搬进前端的运行时协议**。前者是数据格式，后者是传输通道。

## 事件分类：协议的骨架

协议的核心是事件。AG-UI 把事件分成八个类别：

| 类别 | 作用 |
|---|---|
| Lifecycle Events | 跟踪 agent 运行的起止 |
| Text Message Events | 流式文本内容 |
| Tool Call Events | 管理工具执行 |
| State Management Events | 在 agent 与 UI 间同步状态 |
| Activity Events | 表示进行中的活动进度 |
| Subagent Events | 跟踪子智能体并归属其产出 |
| Special Events | 支撑自定义功能 |
| Draft Events | 尚在开发中的提案事件 |

每个事件共享一组基础属性：`type`（事件类型标识）、`timestamp`（可选时间戳）、`rawEvent`（可选，事件被转换时的原始数据）、`metadata`（可选的开放键值对象）。

`metadata` 这个设计值得单说一句。它被声明在基础事件上，所以**每种事件类型都带它**。消费端把事件的 metadata 逐键合并进该事件所构建的消息，后写覆盖先写。这带来一个具体好处：生产者可以在一条消息的**最后一个事件**上发送 token 用量，而不必事先知道用量——生产者不需要提前算。

大多数事件还接受可选的 `subagentRunId`，标识是哪个子智能体产生的。没有这个字段的事件属于父 agent。

### 生命周期事件的形状

一次典型的 agent 运行有可预期的结构：

```
RunStarted
  → [StepStarted → StepFinished] × 0..n   （步进是可选的）
  → RunFinished（成功）或 RunError（失败）
```

生命周期事件的价值在于给前端提供了统一的结构——loading 指示器、进度追踪、错误恢复都可以基于这套结构写，不必每家框架一套。

## 状态同步：两条路

状态管理是 AG-UI 里最容易被忽略、却最影响实际体验的部分。它提供了两种互补的方式。

**状态快照（State Snapshot）** 交付 agent 当前状态的完整表示：

```typescript
interface StateSnapshotEvent {
  type: EventType.STATE_SNAPSHOT
  snapshot: any // 完整状态对象
}
```

**状态增量（State Delta）** 描述的是变化量而非全量。

这个双轨设计解决的是真实工程问题：全量快照实现简单但传输冗余，尤其在状态对象大的时候；增量高效但要求两端状态一致性好。前端按需选择，或者两者配合。

`docs/concepts/state.mdx` 对共享状态的定义有四条：跨交互持久化、agent 与前端都能访问、随交互实时更新、为双方决策提供上下文。双方都能改，这就把状态变成了真正的协作通道而非单向回显。

## 1.0：规范冻结与兼容边界

1.0 的核心动作是**把规范本身变成 source of truth**：JSON Schema 是唯一真相来源，TypeScript、Python 和 .NET 的 SDK 全部从它生成。行为规则不再只活在 TypeScript client 里，而是被写进了规范文档。

向后兼容是双向的，README 与迁移文档都写得很明确：

- **0.x agent 接 1.0 client**：TypeScript client 带了一个常开的兼容边界，把遇到的已废弃形态翻译过去——五个 `THINKING_*` 事件转成对应的 `REASONING_*`，旧版 `binary` 内容分片转成媒体分片，历史上接受的整型 `null` 可选字段在校验前转为缺省。每次入站翻译都会告警。这些兼容垫片的到期日是暂定的——写下来时起算 12 个月，若推迟则在 1.0 发布时重新计算——到期后旧形态彻底失效。
- **1.0 agent 接 0.x client**：1.0 新增的一切——`RUN_FINISHED.outcome`、子智能体事件、`protocolVersion`、activity 事件——要么是可选的，要么是新事件类型，旧 client 不认识的东西直接忽略。
- **传输层没变**：JSON over SSE 和 protobuf binding 的 framing 没动，今天发的字段名就是 1.0 读的字段名，除了迁移文档列出的那几处。

**版本声明有一条容易踩的规矩**：1.0 的生产者**必须**在 `RUN_STARTED` 上声明自己说的协议版本。schema 里这个字段是可选的，因为「缺省」正是识别 pre-1.0 生产者的方式——也就是说没有哪个 SDK 会替你在自己手搓事件时自动补上它。要用 SDK 的常量，永远不要手打字符串；也**永远不要**把 `RunAgentInput.protocolVersion` 回显出去，那个声明说的是生产者自己的版本。

## 最小可运行示例

协议本身很轻：一个接收 `RunAgentInput`、流式返回事件的 HTTP 端点就是 agent。README 给了一个不依赖任何 API key 的 Python 服务端：

```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from ag_ui.core import (
    PROTOCOL_VERSION, RunAgentInput, RunStartedEvent, RunFinishedEvent,
    TextMessageStartEvent, TextMessageContentEvent, TextMessageEndEvent,
)
from ag_ui.encoder import EventEncoder

app = FastAPI()

@app.post("/")
async def run_agent(input_data: RunAgentInput, request: Request):
    encoder = EventEncoder(accept=request.headers.get("accept"))

    async def events():
        yield encoder.encode(RunStartedEvent(
            thread_id=input_data.thread_id,
            run_id=input_data.run_id,
            protocol_version=PROTOCOL_VERSION,
        ))
        message_id = str(uuid.uuid4())
        yield encoder.encode(TextMessageStartEvent(message_id=message_id, role="assistant"))
        for chunk in ["Hello ", "from ", "AG-UI!"]:
            yield encoder.encode(TextMessageContentEvent(message_id=message_id, delta=chunk))
        yield encoder.encode(TextMessageEndEvent(message_id=message_id))
        yield encoder.encode(RunFinishedEvent(thread_id=input_data.thread_id, run_id=input_data.run_id))

    return StreamingResponse(events(), media_type=encoder.get_content_type())
```

客户端侧，TypeScript SDK 的 `HttpAgent` 把这套事件消费掉：

```typescript
import { HttpAgent } from "@ag-ui/client";

const agent = new HttpAgent({ url: "http://localhost:8000/" });
agent.addMessage({ id: crypto.randomUUID(), role: "user", content: "Hi there!" });

await agent.runAgent({}, {
  onRunStartedEvent: ({ event }) => console.log(`run started (AG-UI ${event.protocolVersion})`),
  onTextMessageContentEvent: ({ event }) => { process.stdout.write(event.delta); },
  onRunFinishedEvent: () => console.log("\nrun finished"),
});
```

**服务端换成任何一个受支持的框架，客户端不用改。** 这正是协议存在的意义。

生态上，README 列出 Google、Microsoft、Amazon、Oracle 都已采用，LangChain、CrewAI、Microsoft Agent Framework、Google ADK、AWS Strands 等主流框架都有内置支持，每个框架在 [Dojo](https://dojo.ag-ui.com) 有可跑的 demo。

## 适用边界

**什么时候值得上：**

- 你的前端要接多个 Agent 框架，或者要在 Web / Mobile / 终端之间复用同一套前端事件处理
- 你需要生成式 UI（agent 动态决定展示什么）、共享状态、human-in-the-loop 暂停与恢复
- 你的 agent 会派生子智能体，需要在 UI 上归属产出

**什么时候可以不上：**

- 单一框架 + 单一前端，事件种类就那么几种，自己写一个 adapter 更快
- 只是把模型的流式输出显示出来——用框架自带的 SDK 就够，引入协议是净增复杂度
- 你真正的问题在 agent 的规划能力上。协议不解决那个问题

## 采用顺序

1. 先读 `docs/concepts/events.mdx`，把八个事件类别和它们的触发时机弄清楚。这是协议的语义核心，读不懂事件分类就看不懂任何集成。
2. 用 `npx create-ag-ui-app@latest` 起一个模板，用它自带的那套 demo 把事件流在浏览器里看一遍。事件流用眼睛看比用脑子想快得多。
3. 确认你需要的框架在 README 的集成列表里。如果不在，先看 Dojo 里相邻框架的实现方式，确认事件映射是可行的——**协议覆盖的是事件类型，不是每个框架的每个特性**，框架独有的东西最终还是要落到 AG-UI 的扩展机制上。
4. 再看 `docs/concepts/state.mdx` 和 `docs/concepts/subagents.mdx`，确认你的状态同步需求是快照、增量还是两者混合。
5. 生产接入前，把 `DEPRECATIONS.md` 抄进自己的技术债清单——兼容垫片的到期日是暂定的，这是有意为之的临时设计。

## 排查：按现象定位

| 现象 | 先查这里 |
|---|---|
| 前端收不到事件 | `RUN_STARTED` 有没有发；`EventEncoder` 的 `accept` 头协商结果；是否用了 `StreamingResponse` 而不是一次性返回 |
| 版本不匹配报错 | 生产者有没有在 `RUN_STARTED` 上声明 `protocol_version`；手打的字符串是否拼错（应始终用 SDK 常量） |
| 状态不同步 | 快照与增量的选择是否一致；两端是否都消费了同一类状态事件；metadata 合并的「后写覆盖」是否符合预期 |
| 子智能体产出归属错乱 | 事件是否带 `subagentRunId`；没有该字段的事件默认归父 agent |
| 旧事件形态被拒 | 查 `DEPRECATIONS.md` 确认该兼容垫片是否已过到期日 |

## 参考

- 协议规范：<https://docs.ag-ui.com/spec/1.0>
- 迁移指南：<https://docs.ag-ui.com/migrating-to-1-0>
- 事件语义：<https://docs.ag-ui.com/concepts/events>
- 三协议关系：<https://docs.ag-ui.com/agentic-protocols>
- 源码：<https://github.com/ag-ui-protocol/ag-ui>
