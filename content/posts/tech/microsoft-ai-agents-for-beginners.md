---
title: "Microsoft AI Agents for Beginners：一份被低估的工业范式 Agent 课"
date: "2026-09-12T14:30:00+08:00"
slug: "microsoft-ai-agents-for-beginners"
github_repo: "microsoft/ai-agents-for-beginners"
source_key: "gh:microsoft/ai-agents-for-beginners"
aliases:
    - "/posts/tech/microsoft-ai-agents-beginners/"
    - "/posts/tech/msft-ai-agents-for-beginners/"
description: "微软开源 18 课 AI Agent 入门课的工程解读：从 gpt-5-mini 切版、MAF 稳定 API、Foundry 生态收口，到 HandoffBuilder/WorkflowBuilder 真实代码骨架，看清 Microsoft 押注的工业范式 Agent 路线。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Microsoft", "MAF", "Microsoft Foundry"]
---

# Microsoft AI Agents for Beginners：一份被低估的工业范式 Agent 课

GitHub 上挂着 "AI Agents for Beginners" 旗号的仓库很多，但多数本质上是 LangChain 教程或 AutoGen 例子包装。微软在 2025 年底推出、2026 年 7 月 14 日再次大改的 [ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) 不一样——它不是讲某个框架怎么用，而是用 18 节课给 Microsoft 的"工业范式 Agent 路线"画了一张工程地图：MAF（Microsoft Agent Framework）+ Microsoft Foundry Agent Service V2 + gpt-5-mini，三者钉死，整个生态向 Azure 收口。

[仓库 README](https://github.com/microsoft/ai-agents-for-beginners) 直接点名："This course uses the following AI Agent frameworks and services from Microsoft: Microsoft Agent Framework (MAF) + Microsoft Foundry Agent Service V2"。这份判断决定了你读完 18 节课之后会被塑造出什么样的工程直觉——这是它最值得讨论、也最容易被低估的地方。

## 目录

- [一、18 课到底讲了什么：先把地图摆出来](#一18-课到底讲了什么先把地图摆出来)
- [二、技术栈的"钉子"：CHANGELOG 2026-07-14 透露的选型逻辑](#二技术栈的钉子changelog-2026-07-14-透露的选型逻辑)
- [三、课程没告诉你的"反面"：什么时候不该用 Agent](#三课程没告诉你的反面什么时候不该用-agent)
- [四、设计原则的反模式：以人为本 vs. 替代人](#四设计原则的反模式以人为本-vs-替代人)
- [五、MAF 的工程骨架：HandoffBuilder、WorkflowBuilder、ctx.request_info](#五maf-的工程骨架handoffbuilderworkflowbuilderctxrequest_info)
- [六、九宫格概念图：Agent / Tools / Knowledge / Memory / Planning / Multi-Agent / Metacognition / Protocol / Context Engineering](#六九宫格概念图agent--tools--knowledge--memory--planning--multi-agent--metacognition--protocol--context-engineering)
- [七、一个任务如何流过课程的全栈](#七一个任务如何流过课程的全栈)
- [八、课程地图：三类读者的三条路径](#八课程地图三类读者的三条路径)
- [九、采用顺序与适用边界](#九采用顺序与适用边界)
- [十、给读者的三句话](#十给读者的三句话)

---

## 一、18 课到底讲了什么：先把地图摆出来

[README](https://github.com/microsoft/ai-agents-for-beginners) 列出了 00–18 共 19 个目录（含 00-course-setup）。前 6 课是基础概念，中间 7 课讲核心设计模式，后 6 课是落地与扩展。我把它们按"读者解决的问题"重新分四组：

| 组别 | 课次 | 解决的核心问题 | 关键产出 |
|---|---|---|---|
| 基础概念 | 01-intro / 02-frameworks / 03-design-patterns | Agent 是什么、该用哪个框架、设计原则是什么 | Agent 七种分类、`MAF` vs Foundry Agent Service 对照表、四条人本设计原则 |
| 核心模式 | 04-tool-use / 05-agentic-rag / 06-trustworthy / 07-planning / 08-multi-agent / 09-metacognition | 工具调用、RAG、可信、规划、多代理、自省 | 7 种设计模式代码模板 |
| 生产与协议 | 10-production / 11-protocols / 12-context / 13-memory | 可观测、评估、MCP/A2A/NLWeb、上下文工程、记忆 | OpenTelemetry 接线、Mem0 与 Cognee 集成 |
| 落地与扩展 | 14-microsoft-agent-framework / 15-browser-use / 16-deploying-scalable-agents / 17-local-ai-agents / 18-securing-ai-agents | MAF 实战、Computer Use、规模化部署、本地代理、安全审计 | HandoffBuilder、Foundry Local + Qwen、加密收据 |

这张图能回答三个问题：你想从哪个切口进入；哪几课可以并行；哪几课之间是"读了前 6 才能读后 12"的前后关系。[STUDY_GUIDE.md](https://github.com/microsoft/ai-agents-for-beginners/blob/main/STUDY_GUIDE.md) 给出了更细的学习路径推荐，包括"想理解 Agent 是什么"的读者从 01/02/03 切入，想做 RAG 应用的从 05 切入并补 04/06/12。

---

## 二、技术栈的"钉子"：CHANGELOG 2026-07-14 透露的选型逻辑

[CHANGELOG.md](https://github.com/microsoft/ai-agents-for-beginners/blob/main/CHANGELOG.md) 2026-07-14 这条 release note 几乎是这份课程的灵魂。我把三件事拆开看：

**第一件：从 gpt-4.1 切到 gpt-5-mini**

CHANGELOG 写得直白——"`gpt-4.1` and `gpt-4.1-mini` are now deprecated (published retirement date 14 October 2026)"。整个课程（文档、`.env.example`、Python/.NET notebook）都换成了 `gpt-5-mini`；Lesson 16 的模型路由示例保留 `gpt-5-nano`（小模型） + `gpt-5-mini`（大模型）的对比。

课程假设你跑的是 2026 年 7 月之后的 Azure 模型部署。如果你还在用 `gpt-4o` 系列，notebook 跑不起来；如果是 2025 年底 fork 的旧版，更新 CHANGELOG 之前别贸然跑。

**第二件：MAF 钉到 `~=1.10.0`**

[requirements.txt](https://github.com/microsoft/ai-agents-for-beginners/blob/main/requirements.txt) 里三行很关键：

```text
agent-framework-core==1.10.0
agent-framework-foundry~=1.10.0
agent-framework-openai~=1.10.0
```

注释里说"1.11.0 introduced breaking API changes"——把版本钉到 1.10.x，是为了课程里所有 notebook 用的是一套自洽的稳定 API，避免 1.11 引入的破坏性变更（如 `ChatMessage`、`HostedWebSearchTool` 被移除、`Agent.run()` 的 `model=` 参数被砍）让新手撞墙。

**第三件：把 LangChain 拉进 Foundry**

14 课的 [README](https://github.com/microsoft/ai-agents-for-beginners/blob/main/14-microsoft-agent-framework/README.md) 给出了一个不起眼但很重要的能力：用 `langchain-azure-ai[hosting]` 把 LangGraph 代理暴露成 Microsoft Foundry hosted agent，走的是 `/responses` 协议（`ResponsesHostServer`）或 `/invocations` 协议（`InvocationsHostServer`）。

```python
from langchain.agents import create_agent
from langchain_azure_ai.agents.hosting import ResponsesHostServer

graph = create_agent(build_chat_model(), tools=[])
ResponsesHostServer(graph).run(port=8088)
```

跑起来后，Foundry 管 runtime、session、scaling、identity、protocol endpoints；你的 LangGraph 逻辑不动。这条线索告诉你：MAF 不是 Microsoft 的霸权，它给 LangChain 也开了门。这条缝很重要，因为它影响你的"该不该迁到 MAF"的判断。

**这三件事合起来看，CHANGELOG 2026-07-14 不是一次常规升级，而是 Microsoft 把 Agent 工程栈从"半成品 demo"塑造成"工业产品"的关键节点。**

---

## 三、课程没告诉你的"反面"：什么时候不该用 Agent

第 1 课的 [When to Use AI Agents](https://github.com/microsoft/ai-agents-for-beginners/blob/main/01-intro-to-ai-agents/README.md) 这一节是整份课程最锋利的地方，因为它讲了"不"。

它给的判断标准三条**用 Agent**：开放性问题（步骤无法预编程）、多步流程（需要工具 + 多轮）、可随时间改进（基于反馈自我调整）。这之外，第 6 课 [Building Trustworthy AI Agents](https://github.com/microsoft/ai-agents-for-beginners/blob/main/06-building-trustworthy-agents/README.md) 再补一刀：可观察、可信、安全、可审计，是 Agent 上生产的前提。

但课程没说出口的是另一面。如果你的任务**能用一个确定性函数描述**——比如"把 JSON 里 5 个字段映射到另一个 schema 并校验"、"按规则过滤 1 万条日志"、"按日期归档文件"——你**不需要 Agent**。直接写 Python 函数 + 几个 LLM 调参就够了。Agent 的价值在于处理"开放性 + 多步 + 可进化"，代价是延迟、成本、不可预测性、调试噩梦。

STUDY_GUIDE 的"Models and Providers"段说得更直接："GitHub Models is deprecated (retiring July 2026) and does not support the Responses API. The samples have been updated to use Azure OpenAI / Microsoft Foundry instead." 这句话的潜台词是：如果你还在用 GitHub Models，那 18 课对你来说不是"入门课"，而是"还没入门"。

---

## 四、设计原则的反模式：以人为本 vs. 替代人

[第 3 课](https://github.com/microsoft/ai-agents-for-beginners/blob/main/03-agentic-design-patterns/README.md) 给的"agentic design principles"四条值得逐字读：

> In general, agents should:
> - **Broaden and scale human capacities** (brainstorming, problem-solving, automation, etc.)
> - **Fill in knowledge gaps** (get me up-to-speed on knowledge domains, translation, etc.)
> - **Facilitate and support collaboration** in the ways we as individuals prefer to work with others
> - **Make us better versions of ourselves** (e.g., life coach/task master, helping us learn emotional regulation and mindfulness skills, building resilience, etc.)

第四条最容易被产品经理抄走时丢掉。"make us better versions of ourselves"不是"make our life more efficient"，而是"让我们变成更好的人"。这不是文案口吻——第 9 课 [Metacognition](https://github.com/microsoft/ai-agents-for-beginners/blob/main/09-metacognition/README.md) 直接把"self-reflection / adaptability / error correction / resource management"当成 Agent 的元能力来教，理由是：Agent 帮我们"reading the room"。

我读到这里感觉：**这是 Microsoft 给整个 Agent 工业写的一条软约束**——Agent 不是替代你写代码的人，而是让你变成更好的工程师；Agent 不是替你决策的人，而是让你变成更好的决策者。这条原则在 14 课、15 课、16 课反复出现：handoff 让人类保留最终决策、human-in-the-loop 让高风险动作必须人确认、evaluation gate 让 Agent 不能自己上线。

如果你正在设计的产品恰恰相反——"让 Agent 完全替代客服"、"让 Agent 自动执行金融交易无需人工"——那这份课程会通过它的"trustworthy / metacognition / human-loop"三章反向告诉你：这条路没经过 Microsoft 的工程验证。

---

## 五、MAF 的工程骨架：HandoffBuilder、WorkflowBuilder、ctx.request_info

读 14 课 [Microsoft Agent Framework](https://github.com/microsoft/ai-agents-for-beginners/blob/main/14-microsoft-agent-framework/README.md) 的代码示例，是我判断"这门课值不值得花时间"的关键。下面三块是骨架：

**骨架一：handoff 多代理（稳定 API）**

[14-handoff.ipynb](https://github.com/microsoft/ai-agents-for-beginners/blob/main/14-microsoft-agent-framework/code-samples/14-handoff.ipynb) 在 7-14 这次大改后用的是稳定 API 形态：

```python
from agent_framework.orchestrations import HandoffBuilder, HandoffAgentUserRequest

workflow = (
    HandoffBuilder(
        name="travel_support_handoff",
        participants=[customer_support_agent, booking_agent, disputes_agent, trip_check_agent],
        termination_condition=lambda conv: sum(1 for msg in conv if msg.role == "user") > 3,
    )
    .with_start_agent(customer_support_agent)     # 主代理接收初始请求
    .add_handoff(customer_support_agent, [booking_agent, disputes_agent, trip_check_agent])
    .build()
)

# event.type 流式消费
async for event in workflow.run("I want to book a flight to Paris", stream=True):
    handle(event)
```

四件事要记住：`HandoffBuilder.with_start_agent(...)` 入口代理；`.add_handoff(a, [b,c,d])` 路由表；`event.type`-based streaming 消费事件；`termination_condition` 控制对话边界。CHANGELOG 强调：稳定 API 替代了 1.0 之前的 `RequestInfoEvent` / `ChatMessage` 符号，1.11 之后这些符号被删了。

**骨架二：human-in-the-loop（也是稳定 API）**

[14-human-loop.ipynb](https://github.com/microsoft/ai-agents-for-beginners/blob/main/14-microsoft-agent-framework/code-samples/14-human-loop.ipynb) 用 `ctx.request_info(...)` 暂停代理等待人类反馈，再用 `@response_handler` 装饰器把响应回灌到 workflow。结构化输出通过 `default_options={"response_format": ...}` 约束。

```python
from agent_framework import WorkflowBuilder, response_handler

# 暂停请求人类输入
ctx.request_info(ConfirmationQuestion, ...)

# 把人类响应接回
@response_handler
async def on_human_response(ctx, payload):
    ...
```

CHANGELOG 强调这里用了"a scripted answer so the notebook runs unattended (no blocking `input()`)"——这是个值得记住的设计选择：课程不让 notebook 卡住等你，自动化测试能跑通。

**骨架三：workflow 编排（MAF 的核心）**

MAF 把"多步执行 + 多代理 + 人类介入"抽象成 workflow graph：

- **Executors** 接收输入、生产输出。可以是 AI 代理，也可以是自定义逻辑。
- **Edges** 决定消息怎么走：direct edge（点对点）、conditional edge（条件触发）、switch-case edge（多路分支）、fan-out / fan-in（广播 / 汇聚）。
- **Events** 提供可观测性：`WorkflowStartedEvent`、`ExecutorInvokeEvent`、`ExecutorCompleteEvent`、`WorkflowOutputEvent`、`WorkflowErrorEvent`、`RequestInfoEvent`。

MAF 的设计哲学是把 Agent 当成"工作流里的一个节点"。这与 LangGraph 的"图就是程序"哲学一脉相承，但 MAF 把"hosting、observability、middleware、checkpointing"都包进了 SDK。

**三个骨架组合起来，就是"MAF 能做什么"的最小答案**：handoff 解决"代理之间怎么协作"，human-loop 解决"人类怎么介入"，workflow graph 解决"复杂流程怎么编排"。这三件事加上 OpenTelemetry 接线和 middleware 钩子，构成了 MAF 与 LangChain / AutoGen 的差异化护城河。

---

## 六、九宫格概念图：Agent / Tools / Knowledge / Memory / Planning / Multi-Agent / Metacognition / Protocol / Context Engineering

读完整份 18 课，我把它讲的"Agent 工程的九个核心概念"重新排成一张矩阵。横轴是"内部能力 / 外部协同 / 元能力"，纵轴是"基础 / 编排 / 自省"。每一格都对应到具体课次：

| 维度 \ 阶段 | 基础 | 编排 | 自省 |
|---|---|---|---|
| **内部能力** | Tools（04）— 让 Agent 能调函数、读文件、调 API | Memory（13）— working/short-term/long-term/persona/episodic/entity/Structured RAG 七种类型，MAF 把短期记忆映射成 `AgentSession` | Metacognition（09）— Agent 反思自己的决策过程，记录 `corrected_choices` 切换策略 |
| **外部协同** | Knowledge（05）— RAG 把文档/数据接入 Agent 的回答 | Multi-Agent（08）— group chat / hand-off / collaborative filtering 三种模式 | Context Engineering（12）— write/select/compress/isolate 四种策略管理下一轮 LLM 输入 |
| **元能力** | Planning（07）— 用 `pydantic.BaseModel` 定义 `TravelPlan` 让 LLM 吐结构化 JSON | Protocols（11）— MCP/A2A/NLWeb 三个标准协议解决代理-工具 / 代理-代理 / 代理-网页 | Trustworthy（06）— guardrails、oversight、safer behavior，6/10/16/18 课反复强调 |

九宫格不是课程本身给的，是我读完之后倒推出来的。它的价值在于：你能用这九个格子去定位任何一个 Agent 框架——它覆盖了哪些、避开了哪些、强项弱项在哪里。

---

## 七、一个任务如何流过课程的全栈

光讲九宫格是抽象的。我用一个真实任务串一下："我要给客户规划从新加坡到墨尔本的家庭 4 天行程"。

**Step 1: 入口判断（第 1 课视角）**
这是开放性问题（行程无法预编程）+ 多步流程（航班 + 酒店 + 景点）+ 可进化（根据用户偏好调整）→ 用 Agent。

**Step 2: 角色与工具（第 2/14 课视角）**
MAF 里用 `ChatAgent(chat_client=OpenAIChatClient(), instructions=..., tools=[...])` 定义代理；工具用 Python 函数 + 类型注解声明，例如 `get_attractions(location: Annotated[str, Field(...)])` → MAF 自动转成 LLM function-calling schema。

**Step 3: 上下文准备（第 12 课视角）**
不把全部对话历史塞进上下文。先用 `Agent Scratchpad` 记录关键事项；用 `Runtime State Objects` 把每个子任务的结果分容器存，避免互相污染；用 `Memories` 把"用户偏好 Python 实例"等跨会话信息持久化到外部存储。

**Step 4: 规划（第 7 课视角）**
调用 Planner 代理，用 `pydantic` 模型定义 `TravelPlan(main_task, subtasks: List[TravelSubTask], is_greeting)`。Planner 收到请求"新加坡到墨尔本的家庭旅行"后，返回结构化 JSON：

```json
{
  "main_task": "Plan a family trip from Singapore to Melbourne.",
  "subtasks": [
    {"assigned_agent": "flight_booking", "task_details": "Book round-trip flights..."},
    {"assigned_agent": "hotel_booking", "task_details": "Find family-friendly hotels..."},
    {"assigned_agent": "car_rental", "task_details": "Arrange a car rental..."},
    {"assigned_agent": "activities_booking", "task_details": "List family-friendly activities..."}
  ]
}
```

Planner 把任务分发给对应代理。这里用的是"centralized 调度 + 任务声明"的模式，类似 Microsoft Research 的 Magentic One 论文里的 orchestrator。

**Step 5: 多代理协作（第 8 课视角）**
四个专业代理（flight / hotel / car / activities）各自调工具完成任务。Group chat 模式下，它们共享消息总线；hand-off 模式下，主代理根据用户问题路由；collaborative filtering 模式下，多个专家对结果投票。

**Step 6: 自省与修正（第 9 课视角）**
代理给出初步行程后，用户反馈"卢浮宫人太多，挤不动"。Lesson 09 的 `HotelRecommendationAgent` 示例展示了 Agent 怎么反思自己的决策过程：`reflect_on_choice()` 检查上次选的酒店是否收到差评（用户反馈为 "bad"），若差评成立就在 `corrected_choices` 列表里记录"应该切换策略"，下次同类请求自动避开"cheapest"路径。

**Step 7: 上下文压缩与长记忆（第 12/13 课视角）**
对话变长后，把早期对话做 summary 或 trim 到关键信息；用户偏好"4 岁儿童、不进赌场、咖啡要精品"等长期偏好写入 Mem0 或 Cognee，下次开新会话自动调出。

**Step 8: 工具调用与协议（第 11 课视角）**
航班 / 酒店 / 景点数据可能来自 MCP server（Model Context Protocol）或 A2A agent（Agent-to-Agent）。Lesson 11 给出了三种协议的取舍：MCP 适合"代理调外部工具"，A2A 适合"代理调另一个代理"，NLWeb 适合"代理理解网页结构"。

**Step 9: 可信与可观测（第 6/10/16 课视角）**
- 用 OpenTelemetry 把所有工具调用、LLM 调用、retrieval 调用 trace 出来；
- 加 evaluation gate——Agent 回答超过阈值才返回给用户，否则降级到 fallback；
- 高风险动作（付款、取消）走 human-in-the-loop：`ctx.request_info(...)` 暂停 + `@response_handler` 接管。

**Step 10: 部署与扩展（第 16/17 课视角）**
- 上 Foundry：Lesson 16 的 `16-python-agent-framework.ipynb` 教你把代理部署成 hosted agent；用 model routing（小模型 + 大模型）控制成本；用 response caching 降低延迟。
- 本地化：Lesson 17 的 `17-local-agent-foundry-local.ipynb` 演示 Foundry Local + Qwen 全离线——本地工具、本地 RAG（Chroma）、本地 MCP。
- 端到端 smoke test：仓库的 `tests/lesson-XX-smoke-tests.json` 是 Lesson 01/04/05/16 四个 hosted agent 的"冒烟测试集"，通过 [AI Smoke Test](https://github.com/marketplace/actions/ai-smoke-test) GitHub Action 跑——这是 GitHub Marketplace 上一个轻量级 post-deploy gate。

十步走完，整个课程的核心机制都穿了一遍。

---

## 八、课程地图：三类读者的三条路径

[STUDY_GUIDE.md](https://github.com/microsoft/ai-agents-for-beginners/blob/main/STUDY_GUIDE.md) 给出的官方推荐路径是平铺的（一张表覆盖所有目标），我把它重新切成三类读者：

**读者 A：刚接触 Agent 的初学者**
路径：01 → 02 → 03 → 04 → 05 → 06。6 节课够了。先建心智模型（Agent 是什么、什么时候用），再学两个核心能力（tools + RAG），最后加一道 trust guardrail。不要跳过 06——它是后面所有 lesson 的安全基础。

**读者 B：要上生产的中级工程师**
路径：A 的 6 课 + 07 → 08 → 09 → 10 → 12 → 13 → 14。重点是 07-09（三连：规划 / 多代理 / 元认知）、10（可观测 + 评估）、12-13（上下文 + 记忆）、14（MAF 实战）。14 课重点看 handoff / human-loop / sequential / concurrent / middleware 五个 notebook。

**读者 C：要做产品的架构师 / Tech Lead**
路径：B 的全部 + 11 → 15 → 16 → 17 → 18。重点放在 11（协议选型）、15（Computer Use + Microsoft Project Opal）、16（规模化部署的模型路由 + 评估 gate + OpenTelemetry）、17（本地化与隐私边界）、18（加密收据 + 审计）。读完你应该能回答三个问题：我的产品该不该用 MAF？哪些场景走云、哪些走本地？审计 / 合规怎么做？

[第 1 课 README](https://github.com/microsoft/ai-agents-for-beginners/blob/main/01-intro-to-ai-agents/README.md) 末尾给了一句警告："If this is your first time building with Generative AI models, check out our Generative AI For Beginners course."——别跳步。

---

## 九、采用顺序与适用边界

把这门课的工程判断翻译成可操作建议：

**适合采用的情况**

- 你的团队已经在 Azure 上跑模型，并且愿意把生产部署锁定到 Microsoft Foundry。
- 你需要 MAF 给的"middleware + OpenTelemetry + checkpointing + hosted agent + human-in-the-loop"这一整套工程化能力，而不只是"调个 LLM"。
- 你想用 `langchain-azure-ai[hosting]` 把现有 LangGraph 代理托管到 Foundry，避免自己写 deployment / scaling / auth。

**不适合采用的情况**

- 你把 Anthropic / Google / 自托管开源模型作为主模型。课程主路径是 Azure OpenAI Responses API + Microsoft Foundry；课程 README 和 Lesson 14 给了一条缝——用 OpenAI 兼容的 provider（最大 204K 上下文）作为 drop-in 替代——但 Anthropic / Gemini 的原生接入不在课程范围，需要自己看 MAF 文档。
- 你对成本敏感、要本地化部署。课程 17 课演示了 Foundry Local，但那是 dev / offline 场景，不适合规模化生产。
- 你在做研究 / 实验性 agent（如 RL-trained agent、self-play 博弈、agentic symbolic reasoning）。课程是工程导向，不是研究导向。

**采用顺序建议**

1. 先跑通 Lesson 01 的 notebook，5 分钟确认你的 Azure 环境通了；
2. 顺序读完 01–06，建立词汇表和判断标准；
3. 跳到 Lesson 14，把 MAF 的 handoff / human-loop / workflow 三个 notebook 跑一遍——这是 MAF 的"最小集大成"；
4. 按你的实际需要补 07-13 的某一两块；
5. 如果准备上生产，再读 16、18，把 model routing + evaluation gate + 加密收据的工程模式学会；
6. 如果做本地 demo，再读 17。

---

## 十、给读者的三句话

第一句：这份课程不是"Agent 教程"，是 Microsoft 给工业级 Agent 工程画的一张工程地图。它的价值不在教你怎么用某个框架，而在于让你看清 Microsoft 把 Agent 工业栈收口到 Foundry 生态的战略意图。

第二句：判断要不要读完全部 18 课，看你的工作是不是"开放性 + 多步 + 可进化"。如果是，按读者 A 或 B 的路径读；如果不是，先去看 LangChain / 直接写函数，Agent 是工具，不是负担。

第三句：CHANGELOG 2026-07-14 的版本号（`agent-framework-core==1.10.0`、gpt-5-mini、Azure Responses API）不是巧合，而是 Microsoft 把 Agent 工业栈从 demo 变成 product 的里程碑。下次有人问你"Agent 框架哪家强"，你可以把这套版本号甩过去——它是一份关于"工业级 Agent 应该长什么样"的工程回答。

---

## 附录：notebook 跑不通的常见错误

来自 [AGENTS.md](https://github.com/microsoft/ai-agents-for-beginners/blob/main/AGENTS.md) 的常见坑，以及读 CHANGELOG 时挑出的几条关键错误模式：

| 错误 | 症状 | 修复 |
|---|---|---|
| `AZURE_AI_PROJECT_ENDPOINT` 缺失 | notebook 启动立刻抛 `KeyError` | `cp .env.example .env` 后填入 Foundry 项目端点 |
| `az login` 没跑 | `AzureCliCredential` 拿不到 token | 终端跑 `az login` 并确认订阅 |
| 模型部署名错 | `gpt-4o` 系列 404 / `gpt-5-mini` 报 model not found | 把 `AZURE_AI_MODEL_DEPLOYMENT_NAME` 改成项目里实际部署的非弃用模型（推荐 `gpt-5-mini`） |
| Python 版本 < 3.12 | 部分包报错 | 用 `python3.12 -m venv venv` 显式指定 |
| `agent-framework` 升到 1.11+ | notebook 用到的 `HandoffBuilder.with_start_agent` / `ctx.request_info` 找不到 | `pip install "agent-framework-core==1.10.0"` 钉到 1.10.x |
| Lesson 05 缺 Azure AI Search | RAG 找不到索引 | 在 `.env` 里补 `AZURE_SEARCH_SERVICE_ENDPOINT` 和 `AZURE_SEARCH_API_KEY` |
| Lesson 08 Bing 接地未配置 | workflow notebook 04 失败 | 在 Foundry 项目里绑定 Bing connection |
| Lesson 13 / Lesson 17 依赖外部 runtime | 跑不起来 | Lesson 13 用 Cognee 时本地装 Cognee；Lesson 17 装 Foundry Local SDK 并 `foundry model run qwen` |
| Lesson 16 smoke test 失败 | hosted agent 没部署 | 先 `azd provision` + `azd deploy` 把 16 课的 hosted agent 推到 Foundry，再跑 GitHub Actions |

`scripts/validate-notebooks.ps1` 是仓库自带的 headless 验证脚本（PASS/FAIL matrix），把全部 Python notebook 用 `nbconvert` 跑一遍并打印结果。CI 不通过时先用它定位。

---

**参考链接**

- 课程仓库：[github.com/microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners)
- AGENTS.md：[项目元数据 + 开发工作流](https://github.com/microsoft/ai-agents-for-beginners/blob/main/AGENTS.md)
- STUDY_GUIDE.md：[学习路径推荐](https://github.com/microsoft/ai-agents-for-beginners/blob/main/STUDY_GUIDE.md)
- CHANGELOG.md：[版本演进 + 2026-07-14 大改说明](https://github.com/microsoft/ai-agents-for-beginners/blob/main/CHANGELOG.md)
- Microsoft Agent Framework 官方文档：[learn.microsoft.com/agent-framework/overview](https://learn.microsoft.com/agent-framework/overview/)
- Microsoft Foundry Agent Service V2：[aka.ms/ai-agents-beginners/ai-agent-service](https://aka.ms/ai-agents-beginners/ai-agent-service)
- AI Smoke Test Action：[github.com/marketplace/actions/ai-smoke-test](https://github.com/marketplace/actions/ai-smoke-test)