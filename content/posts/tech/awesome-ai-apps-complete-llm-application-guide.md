---
title: "Awesome AI Apps：80+LLM应用实战项目合集"
date: "2026-04-12T02:31:39+08:00"
slug: awesome-ai-apps-complete-llm-application-guide
description: "Awesome AI Apps 收录了 80+ 个 LLM 应用实战项目，涵盖 AI Agent、RAG、聊天机器人等多个领域，适合学习和参考。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "AI", "Agent", "RAG", "开源项目"]
---

# Awesome AI Apps：80+ LLM 应用实战项目合集

## 这个合集值不值得读

挑 LLM 应用框架，或者想看"生产级 Agent 长什么样"，Awesome AI Apps 值得花两小时翻一遍。80 多个可运行项目按难度从 Starter 排到 Advanced，覆盖 Agno、CrewAI、LangChain、PydanticAI、AWS Strands、DSPy 等主流框架，集中展示 RAG、Memory、MCP、Voice 四类横向能力的工程写法。

合集的用处在于对照同一类问题在不同框架下的解法。教写 Agent 的事交给框架官方文档，合集负责提供样本。本文按这个角度重组合集内容：先给系统地图，再按难度逐层拆解，最后用一个研究任务的完整流水线把各类机制串起来。

本文代码示例展示主要调用结构，具体 API 以仓库内可运行代码为准。

## 学习目标

读完本文应能：

- 说清 Agent 框架、RAG、Memory、MCP 四类机制各自解决的问题和边界
- 根据业务场景在 Starter / Simple / Advanced 三层中找到对应参考项目
- 识别合集项目的生产化缺口（凭证管理、可观测性、错误恢复）
- 判断哪些项目受赞助关系影响，选型时不被项目分布误导

## 项目背景与核心数据

下面数据来自仓库 README，截至 2026 年 4 月。Stars、Forks、贡献者数量会随时间变化，使用时以仓库主页为准。

| 指标 | 数值 |
|------|------|
| Stars | 10.1k ⭐ |
| Forks | 1.3k |
| 项目总数 | 80+ |
| 贡献者 | 50+ |
| 许可证 | MIT |
| 语言 | Python 72.1%, Jupyter Notebook 18.5%, TypeScript 4.5% |

合集按难度分八类，项目数加总 85，与"80+"口径一致（部分项目跨类）。

| 分类 | 项目数 | 难度 | 说明 |
|------|--------|------|------|
| **Starter Agents** | 13 | ⭐ 入门 | 单框架最小可运行示例 |
| **Simple Agents** | 14 | ⭐⭐ 基础 | 日常 AI 应用实战 |
| **Voice Agents** | 2 | ⭐⭐ 基础 | 实时语音助手 |
| **MCP Agents** | 13 | ⭐⭐⭐ 中级 | Model Context Protocol 集成 |
| **Memory Agents** | 12 | ⭐⭐⭐ 中级 | 持久记忆与个性化 |
| **RAG Apps** | 12 | ⭐⭐⭐⭐ 高级 | 检索增强生成应用 |
| **Advanced Agents** | 18 | ⭐⭐⭐⭐⭐ 高级 | 生产级多 Agent 流水线 |
| **Courses** | 1 | 🎓 课程 | AWS Strands 完整课程 |

---

## 快速开始

### 环境要求

| 要求 | 版本 |
|------|------|
| Python | 3.10+（推荐 3.11+）|
| Git | 最新版 |
| 包管理器 | pip 或 uv（推荐）|

### 快速部署

```bash
# 克隆仓库
git clone https://github.com/Arindam200/awesome-ai-apps.git
cd awesome-ai-apps

# 选择项目（如 Agno Starter）
cd starter_ai_agents/agno_starter

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 安装依赖
pip install -r requirements.txt
# 或使用 uv（更快）
uv sync

# 运行项目
python main.py
# 或 Streamlit 应用
streamlit run app.py
```

每个子项目自带 `.env.example` 和 `requirements.txt`，依赖互不冲突。第一次跑建议从 `agno_starter` 开始，依赖最少。

---

## 系统地图：四类并行机制的边界

合集里的项目看起来杂，实际上在解四类独立问题。拆开看，选型时不会混。

| 机制 | 解决的问题 | 典型组件 | 合集对应分类 |
|------|-----------|---------|-------------|
| **Agent 框架** | 怎么把 LLM、工具、提示词组装成一个可调用的单元 | Agno, CrewAI, LangChain, PydanticAI | Starter / Simple / Advanced |
| **RAG** | 怎么让模型回答它训练时没见过的私有数据 | LlamaIndex, Qdrant, ChromaDB | RAG Apps |
| **Memory** | 怎么让 Agent 跨会话记住用户偏好和上下文 | Memori, GibsonAI | Memory Agents |
| **MCP** | 怎么用统一协议把外部工具（GitHub、数据库、搜索）接到 Agent | MCP Server, GitHub MCP, Couchbase MCP | MCP Agents |

四类机制可以叠加，但各自独立演进。生产级 Agent 通常同时用 Agent 框架 + RAG + Memory + MCP，每类都有自己的选型空间和失败模式。Voice 是第五类，更偏实时基础设施（LiveKit、Pipecat），与前四类不在同一维度。

```
┌─────────────────────────────────────────────────────────┐
│                   用户请求 / 任务                        │
└─────────────────────────┬───────────────────────────────┘
                          │
          ┌───────────────▼───────────────┐
          │      Agent 框架（编排层）      │
          │  Agno / CrewAI / LangChain    │
          └───┬────────┬────────┬─────────┘
              │        │        │
     ┌────────▼──┐ ┌───▼────┐ ┌─▼──────────┐
     │   RAG     │ │ Memory │ │    MCP     │
     │ 私有数据  │ │ 跨会话 │ │ 外部工具   │
     │ 检索增强  │ │ 记忆   │ │ 标准协议   │
     └───────────┘ └────────┘ └────────────┘
```

接下来按难度逐层拆解。每类先说"为什么单独成类"，再给项目列表和典型写法。

---

## 入门级：Starter Agents

### 为什么需要 Starter

每个框架都有自己的 Agent 抽象、工具注册方式和运行入口。Starter 类项目把每个框架压缩到一个最小可运行文件，50 行代码内能看清"这个框架怎么定义 Agent、怎么挂工具、怎么触发执行"。选型前的快速对照样本，生产代码另写。

### 项目列表

| 项目 | 框架 | 功能 |
|------|------|------|
| **agno_starter** | Agno | HackerNews 趋势分析 |
| **openai_agents_sdk** | OpenAI Agents SDK | 邮件助手 + Haiku 写作 |
| **llamaindex_starter** | LlamaIndex | 任务助手 |
| **crewai_starter** | CrewAI | 多 Agent 研究团队 |
| **pydantic_starter** | PydanticAI | 实时天气查询 |
| **langchain_langgraph_starter** | LangChain + LangGraph | 工作流入门 |
| **aws_strands_starter** | AWS Strands | 天气报告 Agent |
| **camel_ai_starter** | Camel AI | 模型性能基准测试 |
| **dspy_starter** | DSPy | AI 系统构建优化 |
| **google_adk_starter** | Google ADK | Google Agent 开发套件 |
| **cagent_starter** | cagent | Docker 多 Agent 运行时 |
| **sayna_starter** | Sayna | 实时语音基础设施 |
| **kaos_starter** | KAOS | Kubernetes 原生多 Agent 系统 |

### 典型项目：agno_starter

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# 创建 HackerNews 分析 Agent
hn_agent = Agent(
    name="HackerNews Analyst",
    model=OpenAIChat(id="gpt-4o"),
    instructions="分析 HackerNews 当日热门话题",
)

# 运行
response = hn_agent.run("今日有哪些热门 AI 项目？")
print(response.content)
```

Agno 的特点是 Agent 即对象，工具通过参数挂载，运行入口统一为 `run()`。对照 CrewAI 的 `Crew` + `Task` 抽象、LangGraph 的状态图抽象，能看到不同框架对"Agent 边界"的理解差异。

---

## 基础级：Simple Agents

### 这一层在教什么

Starter 只展示框架骨架，Simple 层补上真实业务场景：金融数据查询、日历调度、网页自动化、模型路由、自然语言查库。每个项目都带一个可复现的业务问题，选完框架后用来验证"这个框架能不能撑住我的场景"。

### 项目列表

| 项目 | 框架 | 功能 |
|------|------|------|
| **agno_ai_examples** | Agno | 简单到多 Agent 示例 |
| **finance_agent** | - | 股票市场实时追踪 |
| **human_in_the_loop_agent** | - | 人机协作安全执行 |
| **newsletter_agent** | - | AI 新闻简报生成 |
| **reasoning_agent** | - | 金融推理演示 |
| **agno_ui_agent** | Agno | 网页 + 金融交互界面 |
| **mastra_ai_weather_agent** | Mastra | Mastra AI 天气框架 |
| **cal_scheduling_agent** | - | 日历调度集成 |
| **email_to_calendar_scheduler** | - | Gmail → 日历自动化 |
| **browser_agent** | Nebius + browser-use | 网页自动化 Agent |
| **nebius_chat** | Nebius | Nebius 对话界面 |
| **llm_router** | RouteLLM | 智能模型路由（省成本）|
| **talk_to_db** | GibsonAI + LangChain | 自然语言数据库查询 |
| **agent_discovery_agent** | - | AI Agent 发现与对比 |

### 典型项目：llm_router

```python
from route_llm import Router

# 智能路由：根据任务复杂度选择模型
router = Router(
    easy_model="gpt-4o-mini",      # 简单任务用小模型
    hard_model="nebius-llama",     # 复杂任务用大模型
)

# 自动选择最便宜的合适模型
result = router.execute(
    "解释什么是量子计算",
    complexity="easy",  # 自动判断或手动指定
)
```

`llm_router` 解决成本问题：简单查询路由到小模型，复杂查询才调用大模型。生产环境里这一层通常独立部署，与具体 Agent 框架解耦。

---

## 语音级：Voice Agents

### 为什么语音单独成类

语音 Agent 的瓶颈集中在实时性。VAD（Voice Activity Detection，语音活动检测）、STT（Speech-to-Text，语音转文字）、TTS（Text-to-Speech，文字转语音）、流式打断、WebRTC 传输构成独立技术栈，与文本 Agent 的"调一次 API 拿结果"模式完全不同。合集只收两个项目，覆盖两种主流路径：LiveKit 的实时房间模型和 Pipecat 的流水线模型。

### 项目列表

| 项目 | 技术栈 | 功能 |
|------|--------|------|
| **livekit_gemini_agents** | LiveKit + Gemini Realtime | 低延迟语音对话 |
| **pipecat_agent** | Pipecat + Sarvam | 语音 pipeline + WebRTC |

### 典型项目：livekit_gemini_agents

```python
from livekit import agents
from livekit.agents.pipeline import VoicePipelineAgent

# 创建语音 Agent
agent = VoicePipelineAgent(
    vad=agents.io.VAD.load(),
    llm=agents.llm.LLM.load("gemini-2.0-flash"),
    tts=agents.tts.TTS.load("sarvam"),
)

# 启动实时语音房间
await agent.start(room)
```

`VoicePipelineAgent` 把 VAD → LLM → TTS 串成流水线，每一段可替换。Gemini Realtime 原生支持流式输入输出，省去中间 STT 步骤。

---

## 工具集成级：MCP Agents

### 为什么需要 MCP

Agent 要调用外部工具（GitHub、数据库、搜索引擎）时，传统做法是每个工具写一套适配代码。MCP（Model Context Protocol，模型上下文协议）把"工具如何被发现、如何被调用、如何返回结果"标准化成协议，Agent 端按 MCP 客户端规范实现，工具端按 MCP 服务器规范实现。一个 GitHub MCP 服务器可以同时被 Claude Code、Cursor、任意 MCP 兼容 Agent 调用，工具复用由此成为可能。

### 项目列表

| 项目 | MCP 集成 | 功能 |
|------|----------|------|
| **doc_mcp** | Doc MCP | 语义 RAG 文档问答 |
| **langchain_langgraph_mcp_agent** | Couchbase | LangChain ReAct Agent |
| **github_mcp_agent** | GitHub MCP | 仓库洞察分析 |
| **mcp_starter** | GitHub MCP | GitHub 仓库分析模板 |
| **docs_qna_agent** | MCP | 文档问答 Agent |
| **database_mcp_agent** | GibsonAI | 数据库项目管理 |
| **hotel_finder_agent** | MCP | 酒店搜索预订 |
| **custom_mcp_server** | - | 自定义 MCP 服务器 |
| **couchbase_mcp_server** | Couchbase | Couchbase MCP 集成 |
| **scalekit_exa_mcp_security** | ScaleKit + Exa | 安全搜索 MCP |
| **e2b_docker_mcp_agent** | E2B MCP | 沙箱 Docker 安全执行 |
| **taskade_mcp_agent** | Taskade | 项目管理工作流 |
| **telemetry_mcp_okahu** | Okahu | Text-to-SQL 云追踪 |

### MCP 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent (如 Claude Code)                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ MCP Protocol
┌─────────────────────────▼───────────────────────────────────┐
│                    MCP Server                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │ GitHub  │  │ Database│  │ Search  │  │ Custom  │       │
│  │  MCP    │  │   MCP   │  │   MCP   │  │   MCP   │       │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
    GitHub API    Couchbase    Exa Search    Custom API
```

MCP 的边界在于只覆盖"工具调用"这一段，工具内部逻辑仍由 Agent 决定。GitHub MCP 服务器封装的是 GitHub API 调用，拿到仓库数据后怎么分析，留给 Agent 自己处理。

---

## 记忆级：Memory Agents

### Memory 为什么是独立问题

LLM 本身无状态，每次调用都是独立请求。要让 Agent 记住"用户上次说预算 5 万""用户偏好简洁风格"，必须在外部存储里维护用户档案和会话历史。听起来像数据库问题，难点在于：记忆该存什么、何时召回、如何避免污染上下文。Memori 用 SQL 原生存储，GibsonAI 提供托管层，合集里 12 个项目展示不同记忆策略的写法。

### 项目列表

| 项目 | 记忆技术 | 功能 |
|------|----------|------|
| **agno_memory_agent** | Agno Memory | Agno 持久记忆 |
| **arxiv_researcher_agent_with_memori** | Memori + GibsonAI | 论文研究助手 |
| **aws_strands_agent_with_memori** | AWS Strands + Memori | AWS Strands 记忆增强 |
| **blog_writing_agent** | Memori | 品牌风格博客写作 |
| **social_media_agent** | Memori | 社交媒体自动化 |
| **job_search_agent** | Memori | 求职偏好追踪 |
| **brand_reputation_monitor** | Memori + ExaAI | 品牌舆情监控 |
| **product_launch_agent** | Memori | 竞品分析 |
| **ai_consultant_agent** | Memori v3 + ExaAI | AI 咨询顾问 |
| **customer_support_voice_agent** | Memori v3 + Firecrawl | 语音客服助手 |
| **youtube_trend_agent** | Memori + Agno + Exa | YouTube 趋势分析 |
| **study_coach_agent** | Memori v3 + LangGraph | AI 学习教练 |

### 典型项目：ai_consultant_agent

```python
from memori import Memori
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# 初始化长期记忆
memori = Memori(version="v3")

# 创建带记忆的咨询 Agent
consultant = Agent(
    name="AI Consultant",
    memory=memori,
    model=OpenAIChat(id="gpt-4o"),
)

# Agent 会自动记住之前的偏好和上下文
consultant.run("我想要一个电商网站的 AI 方案")
consultant.run("预算大概多少？")  # 自动理解上下文
```

第二次 `run` 时，Memori 从 SQL 存储里召回第一次会话的关键信息（电商、AI 方案），注入到当前上下文。这层召回逻辑对 Agent 透明，框架端只看到 `memory` 参数。

---

## 检索增强级：RAG Applications

### RAG 解决什么问题

模型训练数据有截止日期，且无法访问企业内部文档。RAG（Retrieval-Augmented Generation，检索增强生成）的思路是：先把私有文档切块向量化存入向量库，用户提问时检索相关片段，再把片段作为上下文喂给模型。合集里 12 个项目覆盖从基础 RAG 到 Agentic RAG（让 Agent 自己决定是否检索、检索什么）的演进路径。

### 项目列表

| 项目 | 技术栈 | 功能 |
|------|--------|------|
| **agentic_rag** | Agno + GPT-5 | Agentic RAG 实现 |
| **agentic_rag_with_web_search** | CrewAI + Qdrant + Exa | 混合搜索 RAG |
| **resume_optimizer** | - | AI 简历优化 |
| **llamaIndex_starter** | LlamaIndex + Nebius | RAG 入门模板 |
| **pdf_rag_analyser** | - | 多 PDF 聊天分析 |
| **qwen3_rag** | Qwen3 | PDF 聊天界面 |
| **chat_with_code** | - | 代码问答助手 |
| **gemma3_ocr** | Gemma3 | OCR 文档处理 |
| **nvidia_nemotron_ocr** | Nemotron-Nano-V2-12b | Nvidia OCR |
| **contextual_ai_rag** | Contextual AI | 企业级 RAG |
| **simple_rag** | Nebius | 基础 RAG 快速上手 |
| **wfgy_llm_debugger** | - | 16 模式 LLM 调试地图 |

### 典型项目：agentic_rag

```python
from agno.agent import Agent
from agno.knowledge import KnowledgeBase
from agno.retriever import Retriever
from agno.models.openai import OpenAIChat
from agno.vectordb.qdrant import Qdrant

# 创建知识库
kb = KnowledgeBase(
    vector_db=Qdrant(collection="docs"),
    retriever=Retriever(vector_db=Qdrant()),
)

# 创建 RAG Agent
rag_agent = Agent(
    name="Doc Assistant",
    knowledge=kb,
    model=OpenAIChat(id="gpt-4o"),
    instructions="基于知识库回答用户问题",
)

# 检索 + 生成
rag_agent.run("我们的退货政策是什么？")
```

普通 RAG 在每次调用前固定检索 Top-K 片段；Agentic RAG 让 Agent 自己判断是否需要检索、检索哪个集合、是否需要二次检索。后者在多源数据场景下召回率更高，但延迟和成本也更高。

---

## 生产级：Advanced Agents

### 这一层的特点

Advanced 层项目都是多 Agent 流水线，单个项目通常涉及 3 个以上 Agent 协作，并集成外部服务（Twilio、MongoDB、Temporal）。这些项目更接近真实生产代码，复杂度最高，适合在掌握前几层后用来研究编排模式。

### 项目列表

| 项目 | 技术栈 | 功能 |
|------|--------|------|
| **nebius_autoresearch** | Nebius + AutoResearch | NYC 出租车分析优化 |
| **agentfield_finance_research_agent** | AgentField | 金融研究 Agent |
| **due_diligence_agent** | AG2 + TinyFish | 尽职调查流水线 |
| **deep_researcher_agent** | Agno + ScrapeGraph AI | 多阶段研究 Agent |
| **candidate_analyser** | - | GitHub/LinkedIn 候选人分析 |
| **job_finder_agent** | Bright Data | LinkedIn 求职自动化 |
| **trend_analyzer_agent** | Google ADK | AI 趋势挖掘 |
| **conference_talk_generator** | Google ADK + Couchbase | 会议演讲稿生成 |
| **finance_service_agent** | Agno + FastAPI | 股票数据预测服务 |
| **price_monitoring_agent** | CrewAI + Twilio + Nebius | 价格监控告警 |
| **startup_idea_validator_agent** | - | 创业想法验证 |
| **meeting_assistant_agent** | - | 会议记录任务创建 |
| **ai_hedgefund** | - | 金融分析对冲基金 |
| **smart_gtm_agent** | - | 市场进入策略 |
| **car_finder_agent** | CrewAI + MongoDB | 二手车推荐 |
| **content_team_agent** | Agno + SerpAPI | SEO 内容优化 |
| **temporal_agents** | Temporal | Temporal 工作流 |

### 典型项目：deep_researcher_agent

```python
from agno.agent import Agent
from agno.pipeline import Pipeline

# 创建多阶段研究流水线
research_pipeline = Pipeline(
    name="Deep Research",
    agents=[
        # 阶段 1：信息收集
        Agent(
            name="Web Scraper",
            role="收集相关信息",
            tools=[ScrapeGraphAI()],
        ),
        # 阶段 2：分析
        Agent(
            name="Analyst",
            role="深度分析",
            tools=[ExaSearch()],
        ),
        # 阶段 3：综合报告
        Agent(
            name="Report Writer",
            role="生成报告",
            instructions="综合前两个 Agent 的结果生成完整报告",
        ),
    ],
)

# 执行流水线
result = research_pipeline.run("研究 AI 在医疗领域的最新进展")
```

流水线模式把"研究"拆成收集 → 分析 → 综合三个阶段，每个阶段由专门 Agent 负责。每段可独立调试和替换，代价是阶段间数据格式必须严格约定，否则下游 Agent 无法解析上游输出。

---

## 任务流案例：一个研究任务如何流过系统

把前面几类机制串起来看一个具体任务："研究 AI 在医疗领域的最新进展，生成报告并发到邮箱"，完整流水线会这样流转：

```
用户输入："研究 AI 在医疗领域的最新进展"
        │
        ▼
┌───────────────────────────────────┐
│ 1. Agent 框架（Agno Pipeline）    │
│    接收任务，拆分为三阶段          │
└───────────────┬───────────────────┘
                │
                ▼
┌───────────────────────────────────┐
│ 2. Web Scraper Agent              │
│    调用 ScrapeGraphAI 抓取网页    │
│    通过 MCP 调用 Exa Search       │
└───────────────┬───────────────────┘
                │ 原始网页文本
                ▼
┌───────────────────────────────────┐
│ 3. Analyst Agent                  │
│    用 RAG 检索内部医疗知识库      │
│    对比网页信息与内部资料         │
└───────────────┬───────────────────┘
                │ 分析结论
                ▼
┌───────────────────────────────────┐
│ 4. Report Writer Agent            │
│    综合前两阶段输出，生成报告     │
│    通过 Memory 记住用户偏好格式   │
└───────────────┬───────────────────┘
                │ 最终报告
                ▼
┌───────────────────────────────────┐
│ 5. MCP 调用 Gmail MCP 发送邮件    │
└───────────────────────────────────┘
```

这个例子里，Agent 框架负责编排，RAG 负责私有数据检索，Memory 负责用户偏好，MCP 负责外部工具调用。生产环境里每一层都可能成为瓶颈：Agent 框架的编排延迟、RAG 的召回率、Memory 的污染问题、MCP 的工具故障，需要分别监控。

---

## 赞助商与技术栈全景

### 赞助商

| 赞助商 | 产品 | 链接 |
|--------|------|------|
| **Bright Data** | 网页数据平台 | dub.sh/brightdata |
| **Nebius** | AI 推理提供商 | dub.sh/nebius |
| **ScrapeGraphAI** | AI 网页爬取框架 | dub.sh/scrapegraphai |
| **Memori** | SQL 原生记忆 | dub.sh/memorilabs |
| **CopilotKit** | Agentic 应用平台 | dub.sh/copilotkit |
| **ScaleKit** | AI 认证栈 | dub.sh/scalekitt |
| **Okahu** | AI 可观测性平台 | okahu.ai |
| **SerpApi** | Google 搜索 API | dub.sh/serpApi |
| **AgentField** | Kubernetes for AI Agents | dub.sh/agentfield |

赞助商产品在合集项目里高频出现（Memori、ScrapeGraphAI、Nebius），选型时注意区分"项目实际用了什么"和"赞助商推荐什么"。

### 技术栈全景图

```
AI 应用技术栈
├── 模型层
│   ├── OpenAI (GPT-4o, GPT-4o-mini)
│   ├── Anthropic (Claude)
│   ├── Google (Gemini, Gemma)
│   ├── Nebius (Llama)
│   └── Open Source (Qwen, DeepSeek)
│
├── 框架层
│   ├── Agent 框架: Agno, CrewAI, LangChain, PydanticAI
│   ├── 多 Agent: AWS Strands, Camel AI, DSPy
│   ├── RAG: LlamaIndex, Qdrant, ChromaDB
│   └── 语音: LiveKit, Pipecat
│
├── 工具层
│   ├── MCP (Model Context Protocol)
│   ├── 搜索: Exa, SerpAPI
│   ├── 爬取: ScrapeGraphAI, browser-use
│   └── 记忆: Memori, GibsonAI
│
└── 部署层
    ├── 云: Nebius, AWS
    ├── 容器: Docker, E2B
    └── 编排: Temporal, Kubernetes
```

---

## 学习路径建议

### 零基础路径

四周节奏，每周聚焦一类机制。第一周只跑 Starter，目标是看清不同框架的 Agent 抽象差异；第二周进入 Simple，验证框架能否撑住业务场景；第三周接触 Voice 和 MCP，理解实时性和工具协议；第四周组合 Memory 和 RAG，跑通一个带记忆的文档问答。

```
Week 1: Starter Agents
├── agno_starter (HackerNews 分析)
├── pydantic_starter (天气 Bot)
└── openai_agents_sdk (邮件助手)

Week 2: Simple Agents
├── talk_to_db (自然语言查询)
├── newsletter_agent (新闻简报)
└── cal_scheduling_agent (日历助手)

Week 3: Voice & MCP
├── livekit_gemini_agents (语音对话)
└── github_mcp_agent (GitHub 工具集成)

Week 4: Memory & RAG
├── ai_consultant_agent (带记忆的咨询)
└── pdf_rag_analyser (文档分析)
```

### 有经验路径

假设你已经熟悉至少一个 Agent 框架，三周节奏。第一周深入 RAG，重点对照 Agentic RAG 和企业级 RAG 的差异；第二周跑生产级流水线，研究多 Agent 编排和故障处理；第三周接触 Temporal 等工作流引擎，理解长时任务的持久化需求。

```
Week 1: 深入 RAG
├── agentic_rag (Agentic RAG)
├── contextual_ai_rag (企业级 RAG)
└── chat_with_code (代码助手)

Week 2: 生产级 Agent
├── deep_researcher_agent (多阶段研究)
├── due_diligence_agent (尽职调查)
└── ai_hedgefund (金融分析)

Week 3: 高级特性
├── temporal_agents (工作流编排)
├── smart_gtm_agent (市场策略)
└── product_launch_agent (竞品分析)
```

---

## 采用建议

按场景分三类建议。

**学习选型**：先跑 3 个不同框架的 Starter（Agno、CrewAI、PydanticAI），用同一个业务问题对照写法，再决定主框架。不要直接跳到 Advanced，那层项目复杂度高，容易把框架问题和业务问题混在一起。

**生产选型**：合集里的项目属于参考实现，直接 fork 上线会踩三类坑——凭证管理（合集用 `.env`，生产需要密钥管理服务）、可观测性（合集项目大多无日志和指标）、错误恢复（合集项目假设工具调用成功，生产需要重试和降级）。把合集当作"写法样本"，生产代码自己重写。

**技术栈组合**：Agent 框架 + RAG + Memory + MCP 四层各有独立选型空间，不要绑定单一供应商。合集里 Memori 和 ScrapeGraphAI 出现频率高，部分原因是赞助关系，选型时按实际需求评估，不要被项目分布误导。

---

## 常见问题

**合集项目能直接用于生产吗？** 不能。合集项目假设工具调用成功、用 `.env` 管理凭证、缺少日志和指标。生产环境需要补齐密钥管理服务、可观测性、重试与降级三块。

**Agentic RAG 一定比普通 RAG 好吗？** 不一定。Agentic RAG 在多源数据场景下召回率更高，但延迟和成本也更高。单一数据源、查询模式固定的场景，普通 RAG 更合适。

**MCP 和直接写工具适配代码相比，代价是什么？** MCP 增加了一层协议抽象，工具端需要实现 MCP 服务器规范。好处是工具可复用，坏处是简单工具的接入成本变高。工具数量少、不复用的场景，直接写适配代码更快。

**赞助商项目能不能用？** 能用，但要区分"项目实际用了什么"和"赞助商推荐什么"。Memori、ScrapeGraphAI、Nebius 出现频率高部分是赞助关系，选型时按实际需求评估。

---

## 相关资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/Arindam200/awesome-ai-apps |
| AWS Strands 课程 | YouTube 播放列表 |
| MCP 教程 | YouTube 播放列表 |
| AI Agents 教程 | YouTube 播放列表 |

---

_🦞 本文由钳岳星君撰写，基于 Awesome AI Apps (10k Stars)_
