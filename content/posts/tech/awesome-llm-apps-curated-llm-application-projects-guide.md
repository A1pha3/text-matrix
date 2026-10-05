---
title: "awesome-llm-apps：140k Stars 的 LLM 应用模板库"
date: "2026-04-06T22:40:00+08:00"
slug: "awesome-llm-apps-curated-llm-application-projects-guide"
github_repo: "Shubhamsaboo/awesome-llm-apps"
source_key: "gh:Shubhamsaboo/awesome-llm-apps"
description: "awesome-llm-apps 收录 100+ 个可独立运行的 AI Agent、Agent Skills 与 RAG 应用模板，覆盖 Agent、RAG、MCP、语音、记忆、生成式 UI 等方向，附带 Google ADK 与 OpenAI Agents SDK 两套框架速成课程。本文基于 2026-09-29 的仓库状态与源码整理。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "AI Agent", "RAG", "MCP", "Multi-Agent", "Google ADK", "Agent Skills"]
---

想看一个 RAG Agent、一个多 Agent 团队、一个语音问答应用分别长什么样，翻框架官方文档只能拿到抽象描述，翻这个仓库能直接拿到 100 多个可运行的完整实现。**awesome-llm-apps 把 LLM 应用的常见形态拆成一个个独立目录，每个目录是单文件或少数几个文件的最小模板，配 requirements.txt，填一个 API key 就能跑。** Apache-2.0 协议，README 原话是 "Fork it, ship it, sell it"——拿来改造成自己的产品在协议上没有障碍。

它的价值集中在两个场景：学 Agent 开发时，把抽象概念对应到能跑的代码；做项目选型时，把某个形态（比如语音 RAG）的参考实现直接拿走改。反过来说，如果你要找的是生产级框架的工程深度——错误处理、并发、监控、评估——这个仓库不提供这些，它的定位是模板库，README 对自己的描述也是 "templates"。

本文基于 2026-09-29 的仓库快照（GitHub API 与 main 分支源码）写成，项目清单和数字以仓库当前状态为准。

## 仓库地图

README 把全部内容分成 16 个小节。三块主线之外，其余小节按应用形态细分：

| 章节 | 数量 | 定位 |
|------|------|------|
| Agent Skills | 8 | 给 Claude Code、Codex、Cursor 等**编程 Agent** 装的能力包 |
| Starter AI Agents | 13 | 单文件入门 Agent，一个 API key 就能跑 |
| Advanced AI Agents | 21+1 | 生产风格的单 Agent 与多 Agent 应用 |
| Always-on Agents | 2 | 定时或事件驱动的后台 Agent |
| Multi-agent Teams | 14 | 跨领域分工协作的 Agent 团队 |
| Voice AI Agents | 4+1 | 语音进、语音出的 Agent |
| Generative UI / Agentic Frontends | 7 | Agent 输出交互式界面而非纯文本 |
| Autonomous Game-Playing Agents | 3 | 用 LLM 玩游戏的 Agent |
| MCP AI Agents | 6 | 通过 Model Context Protocol 连接外部工具 |
| RAG | 21 | 检索增强生成，从基础链到 Agentic RAG |
| AI Browser Tools | 2 | 浏览器场景的轻量 AI 工具 |
| LLM Apps with Memory | 6 | 跨会话记忆的应用 |
| Chat with X | 6 | 把某个数据源接成对话界面 |
| LLM Optimization / Fine-tuning | 2+2 | Token 优化工具与微调教程 |
| Framework Crash Courses | 2 套 | Google ADK 与 OpenAI Agents SDK 速成 |

> 数量按 README 2026-09-29 版本统计；"4+1""21+1" 中的 1 是外部仓库链接。README 说 "New templates drop weekly"，更新频率高，以仓库现状为准。

核心数据（GitHub API，2026-09-29）：Stars 140,325，Forks 20,613，License Apache-2.0，最近一次 push 在查询当天——这是一个仍在高频维护的活仓库。语言构成按字节计：Python 约 55%，TypeScript 约 20%，JavaScript 约 18%，其余是 HTML/CSS。Python 项目大多在各自子目录里 `pip install -r requirements.txt` 后即可运行；JS/TS 集中在 Generative UI 章节这类需要前端界面的应用。

先说模块间的结构关系：Agent Skills 服务的是编程 Agent（你要先有 Claude Code 一类的宿主）；Starter → Advanced → Multi-agent Teams 是同一个 Agent 结构复杂度递增的三级台阶；MCP、Voice、Memory、Generative UI 是给 Agent 加某一种能力的横切面；两套 Crash Course 是框架层的学习材料。多数章节共享同一个基本结构——LLM 决策、工具执行、结果回流循环。

## Agent Skills：给编程 Agent 装能力

这是 README 的头牌章节，也是这个仓库近期演化的重心。Agent Skill 是一个带说明文件和脚本的目录，宿主 Agent（Claude Code、Codex、Cursor 等）按需加载。README 给的安装方式是一行命令：

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/project-graveyard
```

装上之后就可以用自然语言调用，比如问它 "why do I never finish my side projects?"。README 声称每个 skill 都通过安全与评估的 CI 门禁（"passes a security + eval CI gate"）。

8 个 skill 的选题明显偏向开发者日常工作流：

| Skill | 干什么 |
|-------|--------|
| Project Graveyard | 找出你弃坑的副业项目，分析每个死因，帮你挑出值得捡回来的那个 |
| First Reader | 模拟真实读者读你的草稿，报告哪里失去兴趣、哪里弃读、读后记住了什么 |
| Scope Creep Detector | 检查一个 diff 是否长出了声明范围之外的东西，建议保留、拆分还是说明理由 |
| Commit Archaeologist | 从引入 commit、后续修改、共变文件和意图线索重建某段代码为什么存在 |
| Dependency Doctor | 检查依赖清单里的标准库误固定、过时 backport、未固定版本、重复约束和已撤回版本 |
| Advisor Orchestrator Worker | 三模型协作的 Meta Loop，按 README 描述以 Claude Fable 5.1 为顾问、GPT-6 Astra 为编排、Gemini 3.8 Flash 为执行 |
| Thinking Out Loud | 把语音随想整理成可扫读的简报，模型的猜测单独隔离，你的自我推翻会被标出 |
| Self-Improving Agent Skills | 用 Gemini 和 ADK 自动优化其他 skill |

这批东西的看点不在单个 skill 的完成度，而在分发模式：`npx skills add` 一个 URL 就完成安装，skill 以纯文本描述接口，宿主 Agent 自己决定何时调用。这和传统的"装一个 Python 包、import、调 API"是两条路线——前者把能力单元从代码库变成了 Agent 可读的目录。

## Starter AI Agents：最小可运行结构

13 个入门 Agent 全是单文件、单工具链、线性流程，用来理解 "Agent = LLM + 工具 + 循环" 这个基本结构。项目清单：

| Agent | 功能 |
|-------|------|
| AI Blog to Podcast Agent | 把博客 URL 转成播客音频 |
| AI Breakup Recovery Agent | 陪聊度过分手低谷的 Agent 团队 |
| AI Data Analysis Agent | 用自然语言查询任意 CSV/Excel 文件 |
| AI Medical Imaging Agent | 用 Gemini 做 X 光与扫描影像的诊断分析 |
| AI Meme Generator Agent | 开真浏览器做表情包，不调图像 API |
| AI Music Generator Agent | 提示词进，MP3 出 |
| AI Travel Agent | 本地与云端双版本，生成逐日行程 |
| AI x402 Paying Agent | 带钱包的 Agent，按调用付费获取数据，不需要 API key |
| Gemini Multimodal Agent | 视频分析加网络搜索 |
| Mixture of Agents | 多个 LLM 各自回答，一个负责聚合最优解 |
| xAI Finance Agent | Grok 驱动的实时股票分析 |
| OpenAI Research Agent | 基于 OpenAI Agents SDK 的多 Agent 主题研究 |
| Web Scraping AI Agent | 描述要提取什么，Agent 负责爬 |

以 AI Travel Agent 为例看真实结构。它用 Agno 框架搭了两个分工的 Agent（`starter_ai_agents/ai_travel_agent/travel_agent.py`）：

```python
researcher = Agent(
    name="Researcher",
    role="Searches for travel destinations, activities, and accommodations based on user preferences",
    model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
    description=dedent(
        """\
    You are a world-class travel researcher. Given a travel destination and the number of days the user wants to travel for,
    generate a list of search terms for finding relevant travel activities and accommodations.
    Then search the web for each term, analyze the results, and return the 10 most relevant results.
    """
    ),
    instructions=[
        "Given a travel destination and the number of days the user wants to travel for, first generate a list of 3 search terms related to that destination and the number of days.",
        "For each search term, `search_google` and analyze the results.",
        "From the results of all searches, return the 10 most relevant results to the user's preferences.",
        "Remember: the quality of the results is important.",
    ],
    tools=[SerpApiTools(api_key=serp_api_key)],
    add_datetime_to_context=True,
)
```

后面还有个 `planner`，拿研究结果草拟逐日行程；界面是 Streamlit，行程能导出成 ICS 日历文件。同目录的 `local_travel_agent.py` 只换了一处——模型从 `agno.models.openai.OpenAIChat` 换成 `agno.models.ollama.Ollama`，其余逻辑不变。这就是 "Local & Cloud" 的全部含义，也顺带演示了框架层屏蔽厂商差异的价值。

分工上有个细节：Researcher 负责搜集信息、Planner 负责组织输出，各挂各的指令。这是这个仓库反复出现的"拆角色"模式的最小版本。

AI Data Analysis Agent 的实现思路不同：它不追求通用循环，而是 Streamlit + pandas 预处理上传文件，再把 DuckDB 和 pandas 工具交给 Agno Agent（`agno.tools.duckdb.DuckDbTools`、`agno.tools.pandas.PandasTools`），让 LLM 用 SQL 和 DataFrame 操作回答自然语言问题。结构化数据分析场景里，让 LLM 生成 SQL 比让它直接推理事实更可靠——这个项目是这个判断的具体化。

## Advanced AI Agents：从单文件到生产风格

进阶级 21 个仓库内项目（另有 1 个外部链接），README 的定位是 "Production-style agents with tools, memory, and multi-step reasoning"。单 Agent 应用包括深度研究（OpenAI Agents SDK + Firecrawl）、商业咨询、系统架构评审（DeepSeek R1 推理 + Claude）、财务教练、电影制作、投资分析（基于 Yahoo Finance 数据）、财报电话会分析、健康计划、新闻写作、会议简报、欺诈调查（交叉核对公共记录）等。多 Agent 应用包括房屋装修（照片进、照片级改造方案出，用 Nano Banana Pro）、信号情报聚合、产品发布情报、心理健康支持团队、播客生成、以及带哈希链审计的 Trust-Gated 研究团队。

挑两个机制上有代表性的。

**AI Self-Evolving Agent**——Agent 改写自己的工作流。机制来自 EvoAgentX 框架，项目本身是调用示范（`advanced_ai_agents/multi_agent_apps/ai_self_evolving_agent/ai_Self-Evolving_agent.py`）：

```python
wf_generator = WorkFlowGenerator(llm=llm)
workflow_graph: WorkFlowGraph = wf_generator.generate_workflow(goal=goal)

# [optional] display workflow
workflow_graph.display()
# [optional] save workflow 
# workflow_graph.save_module(f"{target_directory}/workflow_demo_4o_mini.json")
#[optional] load saved workflow 
# workflow_graph: WorkFlowGraph = WorkFlowGraph.from_file(f"{target_directory}/workflow_demo_4o_mini.json")

agent_manager = AgentManager()
agent_manager.add_agents_from_workflow(workflow_graph, llm_config=openai_config)

workflow = WorkFlow(graph=workflow_graph, agent_manager=agent_manager, llm=llm)
output = workflow.execute()
```

流程是：从目标生成工作流图，按图实例化一批 Agent，执行，再用 `CodeExtraction` 和 `CodeVerification` 验证产出的代码。demo 的目标是生成一个能在浏览器里玩的俄罗斯方块。所谓"自我进化"落在这个框架里，就是工作流图本身是 LLM 生成且可再生的对象。

**Earnings Call Analyst Agent**——把 YouTube 上的财报电话会转成与播放进度同步的分析工作台。这个项目代表了进阶级的另一类价值：不是新机制，而是把 LLM 塞进一个此前没有自动化工具的职业工作流。

## Multi-agent Teams：跨领域协作的固定套路

14 个 Agent 团队，覆盖竞情分析、金融分析、游戏设计、法律、招聘、房产、教学、代码评审、设计评审、行程规划等场景。README 对其中几个的描述很具体：AI Finance Agent Team 强调"20 行 Python"；LLM Panel Agent Team 让三家厂商的模型盲审同一段 diff 再匿名互怼；AG2 Adaptive Research Team 演示带路由和回退的团队协作。

机制上最完整的是 **AI VC Due Diligence Agent Team**——但它不是 CrewAI，而是 Google ADK 的 `SequentialAgent` 模式（`advanced_ai_agents/multi_agent_apps/agent_teams/ai_vc_due_diligence_agent_team/agent.py`，README 注明基于 Gemini 3）：

```python
due_diligence_pipeline = SequentialAgent(
    name="DueDiligencePipeline",
    description="Complete due diligence pipeline: Research → Market → Financials → Risks → Memo → Report → Infographic",
    sub_agents=[
        company_research_agent,
        market_analysis_agent,
        financial_modeling_agent,
        risk_assessment_agent,
        investor_memo_agent,
        report_generator_agent,
        infographic_generator_agent,
    ],
)
```

七个 `LlmAgent` 子代理按固定顺序执行：公司研究 → 市场分析 → 财务建模 → 风险评估 → 投资备忘录 → 报告生成 → 信息图生成，全部用 `gemini-3-flash-preview`。前一个阶段的产出通过 `output_key` 存入状态，供后一个阶段在 instruction 里引用——比如市场分析 Agent 的指令里直接写着 `COMPANY RESEARCH (from previous stage): {company_info}`。工具侧，公司研究用 `google_search`，财务建模挂 ADK 的 `BuiltInCodeExecutor` 让模型跑代码算数字。序列末端直接产出给投资人看的三件套：备忘录、报告、信息图。

这个案例说明多 Agent 团队的第一种编排形态：顺序流水线，阶段间靠共享状态传递。它不需要复杂的协调算法，可预测性好，适合能自然拆成阶段的任务。需要动态分工的场景，则看 AG2 那个带路由回退的团队。

## Always-on Agents：定时与事件驱动

两个项目，代表"后台常驻"这一类：Always-on Hacker News Briefing Agent 定时扫描 HN，把分级日报推到 Slack 或邮箱；Release Radar Agent 盯依赖发布，发现 breaking change、弃用、安全更新或大版本变化时主动简报。

这类 Agent 的技术难点不在 LLM 而在外围：调度、去重、推送通道、失败重试。两个项目各只覆盖一种形态（定时扫描、事件监听），当成脚手架用合适，直接上生产需要自己补运维层。

## Voice AI Agents：语音通道的三种接法

4 个仓库内项目加 1 个外部链接，正好展示语音接 Agent 的三种路线：

- **AI Audio Tour Agent**——根据位置、兴趣和步速生成自助语音导览。
- **Customer Support Voice Agent**——基于你自己的文档做语音问答，用 OpenAI Agents SDK 搭建，检索侧是 Qdrant 向量库 + Firecrawl 抓取 + fastembed 本地 embedding（见其 `requirements.txt`）。
- **Insurance Claim Live Agent Team**——README 描述它在 Gemini 3.8 Live 上做实时语音理赔：写现场笔记、通过摄像头查看损伤、绘制事故示意图，是多模态实时 API 的展示位。
- **Voice RAG Agent**——对着 PDF 提问、听语音回答。先看它的 import 列表，技术栈一目了然（`voice_ai_agents/voice_rag_openaisdk/rag_voice.py`）：

```python
import streamlit as st
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from fastembed import TextEmbedding
from openai import AsyncOpenAI
from openai.helpers import LocalAudioPlayer
from agents import Agent, Runner
```

文档切分与向量化用 LangChain 的 splitter 加 fastembed（本地 embedding，不花钱），检索存 Qdrant，语音进出用 OpenAI 的音频模型加 `LocalAudioPlayer`，Agent 编排用 OpenAI Agents SDK。语音链路里 STT 和 TTS 都由 OpenAI 的 audio 能力承担，不是传统的"Whisper 转文字 → 文本 LLM → ElevenLabs 合成"三件套——对想要一套供应商搞定语音闭环的场景，这是个更简单的参考。
- **OpenSource Voice Dictation Agent**——外部仓库链接（`jarvis-ai-assistant`），按 README 说法是 Wispr Flow 的开源复刻，说话即打字。

## Generative UI：Agent 的输出从文本变成界面

7 个项目探索同一个想法：Agent 不该只吐 markdown，而应该渲染可交互的组件。清单里有聊天驱动的看板（你和 Agent 共同操作）、渲染成交互卡片的理财方案、聊天里描述仪表盘就组装图表的画布 Agent、描述一个 MCP 应用就返回沙箱实例的构建器、把工具调用过程实时渲染成工作区卡片的深度研究 Agent，以及 shadcn 组件生成器。

这个章节的代码全是 TypeScript/JavaScript，也是仓库里前端占比高的原因。做 Agent 产品界面的，这一章优先翻；只关心后端逻辑的可以跳过。

## Autonomous Game-Playing Agents

3 个项目，机制上最有意思的是 **AI Chess Agent**：AutoGen 的 `ConversableAgent` 登场，白方 Agent 对黑方 Agent，走子前做规则校验（`advanced_ai_agents/autonomous_game_playing_agent_apps/ai_chess_agent/`，用 `python-chess` 校验、`chess.svg` 渲染）。项目内置提示默认 5 个回合，并提醒完整对局可能需要 200 回合以上，API 费用和时间都要有预期——LLM 对战的成本结构在这里表现得很直白。

另外两个：AI 3D Pygame Agent 让 DeepSeek R1 写 PyGame 游戏代码、浏览器 Agent 实时运行；Tic-Tac-Toe 是两个不同 LLM 逐格对战。游戏环境的价值在于胜负可量化、规则确定，是观察 LLM 决策行为的最干净实验场——但也仅此而已，别指望这里有什么超越搜索算法的棋力。

## MCP AI Agents：工具连接的标准协议

MCP（Model Context Protocol）是 Anthropic 提出的开放协议：工具方实现 MCP Server，Agent 方通过 MCP Client 调用，双方不必为每个工具写定制集成。仓库的 6 个项目覆盖了从单连接到多路由的场景：

| Agent | 连接对象 |
|-------|---------|
| Browser MCP Agent | 真实浏览器（Playwright），自然语言驱动网页操作 |
| GitHub MCP Agent | GitHub 仓库的探索与分析 |
| Notion MCP Agent | 终端里对话你的 Notion 页面 |
| AI Travel Planner MCP Agent | 基于实时 Airbnb 与 Google Maps 数据做行程 |
| Multi-MCP Agent Router | 多个 MCP Server 的专家分工路由 |
| OpenAI Remote MCP Tool Bridge | 把 OpenAI function calling 直连远程 MCP Server |

**Browser MCP Agent** 用的是 `mcp-agent` 框架而非裸 MCP SDK，Streamlit 界面 + Playwright 控制 Chromium（`mcp_ai_agents/browser_mcp_agent/main.py`）。

**Multi-MCP Agent Router** 的实现（`mcp_ai_agents/multi_mcp_agent_router/agent_forge.py`，内部叫 Agent Forge）把"路由"理解成"专家分工"：每个 Agent 只连自己领域的 MCP Server，查询先分给对口专家，而不是给一个全能 Agent 挂全部工具：

```python
@dataclass
class Agent:
    """A specialized agent with its own system prompt and MCP server configs."""
    name: str
    description: str
    system_prompt: str
    icon: str = "\U0001f916"
    mcp_servers: list = field(default_factory=list)
```

比如 Code Reviewer 连 GitHub 和 filesystem 两个 MCP Server，Security Auditor 另配自己的。LLM 侧用 Anthropic SDK。这个设计回应的是工具数量增长后的上下文污染问题——工具描述全塞进一个 Agent 的上下文，选择准确率会掉；按领域切小上下文是当前更稳的做法。

## RAG：21 个变体的坐标系

RAG 章节是仓库里最大的单一主题，21 个项目基本构成一张变体地图。先说共同结构：文档切分 → embedding → 存向量库 → 检索 → 拼 prompt → 生成。各项目在这个流水线的不同环节做变体：

| 变体方向 | 代表项目 | 改的是什么 |
|---------|---------|-----------|
| 检索决策交给 LLM | Agentic RAG with Reasoning、Gemini Agentic RAG | LLM 决定是否检索、改写查询、不够就回退网络搜索 |
| 检索结果自评自纠 | Corrective RAG (CRAG)、Autonomous RAG | 给检索结果打分，不合格重检或换网络搜索 |
| 混合检索 | Hybrid Search RAG、Local Hybrid Search RAG | 关键词 + 向量双路召回再喂给模型 |
| 类型安全与引用 | Typed Agentic RAG with Pydantic AI | 答案带精确引用，证据不足时明确拒答 |
| 多模态 | Multimodal Agentic RAG、Vision RAG | 文本、PDF、图像、音频、视频都能进索引 |
| 知识图谱 | Knowledge Graph RAG with Citations | 多跳推理，每个论断可回溯出处 |
| 全本地 | Llama 3.1 Local RAG、Local RAG Agent、Deepseek Local RAG | 无 API key、数据不出机器 |
| 服务化 | RAG-as-a-Service | 50 行以内的生产 RAG 服务骨架 |
| 运维诊断 | RAG Failure Diagnostics Clinic | 系统化定位 RAG 管线哪里出了问题 |

几个项目的定位容易被名字误导，点名说清：**Autonomous RAG** 是 GPT-4o 项目（PDF 回答、不够就自动补网络搜索），和本地 Llama 方案无关；**Hybrid Search RAG** 喂的是 Claude（关键词 + 向量检索的云版本），本地版是另一个项目；**Vision RAG** 用 Embed-4 做图像与 PDF 页面问答；**Gemini Agentic RAG** 的卖点是查询改写加网络回退（Gemini Flash Thinking）。

**Knowledge Graph RAG with Citations** 的实现比"向量 + 图谱混合检索"的俗套说法更具体：Ollama 本地推理 + Neo4j 图数据库，实体、关系、引用都是显式的 dataclass，回答里的每个论断都挂着可回溯的出处，推理链透明可见。向量检索找"相似"，图谱走"关系"做多跳，这个项目里两者各管一段，引用统一归口。

RAG 这章的读法建议：先跑一个 Basic RAG Chain 建立基线，再按你的痛点挑变体——答案不可信看 CRAG 和 Typed Agentic，文档类型杂看 Multimodal，数据敏感看三个全本地项目，管线莫名变差看 Diagnostics Clinic。

## AI Browser Tools 与 Chat with X

**AI Browser Tools** 是两个浏览器扩展形态的小工具：Needle 按语义搜索网页内容并高亮"最强的来源句子"；Ripple 在你编辑 Google Doc 时找出相关的 inconsistency 并建议修改。两者都用 TypeSafe Jev，Ripple 另用了 Gemini。体量小，思路独立，适合当轻量参考。

**Chat with X** 六件套（GitHub、Gmail、PDF、ArXiv 论文、Substack、YouTube）本质是 RAG 的特化：数据源固定、检索路径固定，把"接一个数据源聊起来"的通用需求做成最小模板。README 给的量级：Chat with GitHub 和 Chat with PDF 都是 30 行级别的实现。这组项目的价值是"30 行能到什么程度"的锚点——功能上够 demo，边界（权限、增量更新、多文档）要自己补。

## Memory：跨会话记忆的参考实现

6 个记忆应用按粒度递进：对话历史（Llama3 Stateful Chat）、个人偏好（LLM App with Personalized Memory）、全本地每用户隔离（Local ChatGPT Clone with Memory）、多模型共享同一份记忆（Multi-LLM Application with Shared Memory）、垂直场景（ArXiv 论文记忆、旅行偏好记忆）。

个性化记忆的实现用的是 Mem0（`advanced_llm_apps/llm_apps_with_memory_tutorials/llm_app_personalized_memory/llm_app_memory.py`）：

```python
config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "llm_app_memory",
            "host": "localhost",
            "port": 6333,
        }
    },
}

memory = Memory.from_config(config)

user_id = st.text_input("Enter your Username")
prompt = st.text_input("Ask ChatGPT")

if st.button('Chat with LLM'):
    with st.spinner('Searching...'):
        relevant_memories = memory.search(query=prompt, user_id=user_id)
        # Prepare context with relevant memories
        context = "Relevant past information:\n"

        for mem in relevant_memories:
            context += f"- {mem['text']}\n"
```

记忆的写入交给 Mem0 自动提取，读取侧按 `user_id` 过滤检索，拼进 prompt 前缀。这套"向量库存记忆 + 用户维度过滤 + 检索注入"是当前个性化记忆的通用形态，比手写对话历史数组的版本（Stateful Chat）多了一层语义检索，比纯画像版本多了原始交互细节。要理解几种记忆方案的差异，把这 6 个项目对照跑一遍比读综述文章直接。

## LLM Optimization Tools：两个降本工具

README 把它们单列一节，都是第三方工具的集成示范：

- **Toonify Token Optimization**——用 TOON（Token-Oriented Object Notation）格式替代 JSON 序列化结构化数据。按其 README 的基准：平均 token 减少 63.9%，表格类数据最高 73.4%，格式对人类可读、开销低于 1ms。来源是 ScrapeGraphAI 的 [toonify](https://github.com/ScrapeGraphAI/toonify)。适合 prompt 里反复传大段 JSON 的场景，自由文本没有收益。
- **Headroom Context Optimization**——上下文压缩代理层，宣称降低 API 成本 50-90%（其 README 给的实测区间是 47-92%）。机制包括 SmartCrusher（统计方式压缩 JSON 工具输出，保留首尾项、异常值与查询相关项）、CacheAligner（稳定前缀提高供应商缓存命中）、CCR 可逆压缩（LLM 需要原文时可取回）。以透明代理方式工作，声称零代码改动，兼容 LangChain、Agno、MCP 与任意 OpenAI 客户端。`pip install headroom-ai`。

两个工具的数字都来自各自项目 README 的自述基准，不是独立测评，选型前建议用自己的真实负载压一遍。

## LLM Fine-tuning

两个微调教程：Gemma 3 用 Unsloth 做 4-bit LoRA（README 的说法是 small and readable）；Llama 3.2 是 30 行代码、Colab 免费跑通的入门款。都是 notebook 形态的配方，覆盖的是"最小可复现"而不是生产微调管线。

## Framework Crash Courses：两套框架课

仓库内置两套框架速成课，结构都从 Starter Agent 走到多 Agent 模式，但覆盖面不同：

**Google ADK Crash Course** 按目录数共 9 个模块加一组 YAML 示例：starter、model-agnostic agent、structured output、tool using、memory、callbacks、plugins、simple multi-agent、multi-agent patterns（sequential / loop / parallel 三种工作流 Agent），外加 `adk_yaml_examples` 演示用 YAML 声明 Agent。README 强调它是 model-agnostic 的——工具覆盖 built-in、function、third-party、MCP 四类。

**OpenAI Agents SDK Crash Course** 有 11 个模块：starter、structured output、tool using、running agents、context management、guardrails & validation、sessions、handoffs & delegation、multi-agent orchestration、tracing & observability、voice。它没有 YAML 声明式，但多了 guardrails、tracing 和 voice 三块——分别对应生产化的输入校验、可观测性和语音出口。

选课的依据就是生态归属：主用 Gemini 或想要声明式 Agent 定义，学 ADK；主用 OpenAI 或看重 guardrails/tracing 这套生产设施，学 Agents SDK。两套都过一遍的价值在于对照——同一个概念（工具、记忆、多 Agent）在两个框架里的抽象差异，比任何对比文章都直观。

## 任务流案例：客服语音问答机器人

把前面各章串起来。假设要做：用户在网页上说语音提问，机器人基于公司知识库回答，记住用户历史偏好，必要时能查工单系统。

按能力拆：

| 需求 | 参考项目 |
|------|---------|
| 语音问答，知识库接地 | Customer Support Voice Agent（OpenAI Agents SDK + Qdrant + Firecrawl + fastembed） |
| 语音 RAG 的另一实现 | Voice RAG Agent（OpenAI 音频模型，STT/TTS 一体） |
| 记住用户偏好 | LLM App with Personalized Memory（Mem0） |
| 查工单系统 | Multi-MCP Agent Router 模式：把工单系统封装成 MCP Server，挂给领域专家 Agent |

组合路径：

1. **语音通道与检索内核**：直接以 Customer Support Voice Agent 为骨架——它的定位就是"语音回答 grounded in 你自己的文档"，文档抓取（Firecrawl）、向量化（fastembed）、检索（Qdrant）都是现成的。换知识库只需要换数据源。
2. **记忆层**：把 Mem0 的 `memory.search(query, user_id)` 检索结果注入 Agent 的 system prompt，用户维度隔离已内置。
3. **工具接入**：工单系统写一个 MCP Server，按 Agent Forge 的专家模式挂载，避免与知识库检索工具混在一个大工具列表里。
4. **要补的洞**：仓库内项目没有电话接入层。如果需求是接电话而非网页语音，Twilio 一类的电话网关要自己加；多轮打断、实时性这类语音工程问题，两个语音项目都只覆盖了基础形态。

这个案例的意图是展示仓库的正确用法：每个项目是能力积木，组合成系统时，接缝处（电话层、并发、会话管理）是你要自己写的部分。

## 本地运行

README 的 quick start（任一 Agent 项目同理，各子目录自带 requirements.txt）：

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/ai_travel_agent
pip install -r requirements.txt
streamlit run travel_agent.py
```

注意三点：仓库根目录没有统一的 requirements.txt，必须进入项目子目录安装；多数项目是 Streamlit 应用，入口是 `streamlit run`；API key 一般通过界面输入或 `.env` 提供（Travel Agent 需要 `OPENAI_API_KEY` 和 SerpAPI key 两个）。模型支持面随各项目所用框架而定——README 的说法是 "Works with Claude, Gemini, GPT, DeepSeek, Llama, Qwen and other open-source models"，本地运行优先找目录名带 local 或项目内带 `local_` 前缀文件的版本。

## 采用建议

按目的给顺序：

1. **学 Agent 开发**：Starter 的 AI Travel Agent 或 AI Data Analysis Agent 跑通第一个，然后按 Advanced → Multi-agent Teams 的顺序读代码，重点看角色拆分和状态传递方式（Travel Agent 的双 Agent、VC 团队的 SequentialAgent 是两个基本型）。
2. **找特定形态的参考实现**：直接按上面"仓库地图"定位章节，挑 README 描述最接近需求的 2-3 个项目对照，别只看第一个。
3. **做 Agent 产品**：Generative UI 章节加两套 Crash Course 优先；工具多了之后参考 Agent Forge 的专家分治模式。
4. **给编程 Agent 装能力**：Agent Skills 章节一行命令安装，从 Project Graveyard 或 Dependency Doctor 这类低风险 skill 试起。

适用边界也要说清。这套模板的教学密度高、生产密度低：错误处理、并发、监控、评估在每个项目里都是省略项；数字基准（token 节省比例等）是各项目自述，未经独立复现；README 每周上新，单个项目的维护状态参差，采用前以仓库当前状态为准。把它当"参考实现的检索引擎"用，价值最大；把它当生产代码直接搬，会踩到所有这些坑。

**官方资源**：

- GitHub：https://github.com/Shubhamsaboo/awesome-llm-apps
- 步骤教程站：https://www.theunwindai.com
