---
title: "Shubhamsaboo/awesome-llm-apps：可运行的 LLM 应用精选集"
date: "2026-07-14T03:14:51+08:00"
slug: "shubhamsaboo-awesome-llm-apps-collection-guide"
description: "Shubhamsaboo/awesome-llm-apps 是一个 100+ 可直接运行的 LLM 应用精选集，覆盖 AI Agent、MCP、Voice、RAG、Memory、Multi-Agent 等 15 类能力，按能力轴拆解其项目结构与适用人群。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "AI Agent", "RAG", "MCP", "Multi-Agent"]
---

## 核心判断

`Shubhamsaboo/awesome-llm-apps` 不是 LLM 应用框架，而是一份「**能 clone、能跑、能改**」的 LLM 应用模板集。它把 100+ 个独立示例工程按 Agent、RAG、MCP、Voice、Memory、Multi-Agent、Always-on 等 15 条能力轴组织起来，每个模板都自包含完整源码、可在三步内启动。这种结构决定了它的核心价值是「**对照学习与起手脚手架**」，而不是替代 LangGraph / Google ADK / OpenAI Agents SDK 等生产框架。

下文先给项目地图，再按能力轴拆解 6 条主线的代表模板，最后给一条「从需求到选型」的阅读路径与适用边界。

## 项目定位

仓库作者 Shubham Saboo 把这个集合定位为「**Cookbook of ready-to-run templates**」，强调三点：

- **Hand-built, not curated** —— 每个模板都是原创代码并端到端测试，不是从其他项目搬运。
- **Runs in 3 commands** —— `git clone` → `pip install -r requirements.txt` → `streamlit run xxx.py`，没有半成品脚手架。
- **Provider-agnostic** —— Claude / Gemini / GPT / Llama / Qwen / xAI 等主流模型通过配置切换。

许可协议是 Apache-2.0，允许 fork / ship / sell；与同类「awesome-xxx」清单相比，它把 README 写成「带运行步骤的代码索引」而非「项目网址链接列表」。

## 项目地图：15 条能力轴

仓库根目录以一级目录划分模板类别，下表按 README 的目录顺序汇总。

| 能力轴 | 代表模板 | 解决什么 |
|--------|----------|----------|
| Agent Skills | Project Graveyard、Advisor Orchestrator Worker、Self-Improving Agent Skills | 给 Claude Code / Codex / Cursor 等编程 Agent 加可复用技能 |
| Starter AI Agents | AI Travel Agent、AI Blog to Podcast、AI Meme Generator | 单文件入门 Agent，配一个 API key 就能跑 |
| Advanced AI Agents | AI Home Renovation (Nano Banana Pro)、AI VC Due Diligence Team | 多工具 / 多步推理 / 多 Agent 的生产形态模板 |
| Always-on Agents | Always-on Hacker News Briefing Agent | 按计划 / 事件触发的后台 Agent，主动投递摘要 |
| Multi-agent Teams | AI Finance Team、AI Legal Team、AI Real Estate Team | 多 Agent 协作完成跨领域任务 |
| Voice AI Agents | AI Audio Tour、Customer Support Voice、Insurance Claim Live Team | 实时语音进 / 语音出，基于 Gemini Live 等实时 API |
| Generative UI | Generative UI Starter、AI MCP App Builder、AI Dashboard Canvas | Agent 渲染表单 / 卡片 / 图表等交互组件 |
| Autonomous Game Agents | AI 3D Pygame、AI Chess、AI Tic-Tac-Toe | 端到端玩游戏的 Agent（推理 + 策略 + 动作） |
| MCP AI Agents | Browser MCP、GitHub MCP、Notion MCP、Multi-MCP Router | 通过 Model Context Protocol 连接外部工具 |
| RAG Tutorials | Agentic RAG、CRAG、Hybrid Search、Knowledge Graph RAG | 从基础链到多源 / 多模态 / 图谱的检索增强 |
| Memory Tutorials | ArXiv Agent with Memory、Local ChatGPT Clone with Memory | 跨会话记忆与用户状态 |
| Chat with X | Chat with GitHub / Gmail / PDF / ArXiv / Substack / YouTube | 把任意数据源变成聊天界面 |
| Optimization Tools | Toonify (TOON 格式)、Headroom Context Optimization | 减 token、压上下文、降 API 成本 |
| Fine-tuning Tutorials | Gemma 3 Fine-tuning、Llama 3.2 Fine-tuning | 开源模型的端到端微调 |
| Framework Crash Courses | Google ADK Crash Course、OpenAI Agents SDK Crash Course | 主流 Agent 框架的系统教程 |

从分布看，仓库在 Agent（特别是多 Agent + Voice）+ RAG + MCP 这三条轴最厚实，Fine-tuning 和 Optimization Tools 相对单薄但仍是稀缺内容。

## 核心能力拆解

下面选 6 条主线深入，每条挑一个代表性模板说明它在做什么、跑得起来需要什么。

### 1. Starter AI Agents：最小可跑单元

`starter_ai_agents/` 下的模板几乎都是单文件 Streamlit 应用，典型结构是 `xxx_agent.py` + `requirements.txt` + 一段 Prompt。`ai_travel_agent` 是 README 给出的 Quick Start 示例：

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/starter_ai_agents/ai_travel_agent
pip install -r requirements.txt
streamlit run travel_agent.py
```

这一层适合用来快速验证「**一个 LLM + 工具调用的 Agent 长什么样**」，不需要你懂框架源码。每个目录的 README 通常会注明用哪个模型、是否需要 Tavily / SerpAPI 等外部 Key。

### 2. Advanced AI Agents：工具 + 记忆 + 多步推理

`advanced_ai_agents/` 下的模板开始接近生产形态。`ai_home_renovation_agent` 用 Nano Banana Pro 做视觉重设计，`ai_vc_due_diligence_agent_team` 是多 Agent 尽调流水线，`ai_self_evolving_agent` 强调自我进化。这一层的代码量明显上一个台阶，通常会拆出 `agents/`、`tools/`、`tasks/` 等子目录，并用 LangGraph / CrewAI / AutoGen 等编排框架。

### 3. Always-on Agents：后台调度 + 主动投递

`always_on_agents/` 是仓库较新且差异化最强的一类。`always_on_hn_briefing_agent` 用 Google ADK 跑一个 Hacker News 监听器，按计划抓取 → 过滤「AI Agent / LLM App」信号 → 生成可直接发布的 daily brief。它的工程意义不在于 HN 抓取本身，而在于示范了「**Agent + Schedule + Output Pipeline**」的最小组合，适合想搭 cron-like Agent 的工程师参考。

### 4. Voice AI Agents：实时语音链路

`voice_ai_agents/` 下的模板多依赖 Gemini Live、OpenAI Realtime 等实时语音 API。`insurance_claim_live_agent_team` 把语音进 + 语音出 + 多 Agent 协作串成一条理赔受理流程。如果你在做语音客服、语音陪练、实时口译，这层提供了「**链路完整、可拆解**」的参考实现。

### 5. MCP AI Agents：Model Context Protocol 接入

`mcp_ai_agents/` 下的模板集中示范 MCP 接入：

- `browser_mcp_agent` —— 通过 MCP 驱动浏览器
- `github_mcp_agent` —— 让 Agent 调用 GitHub API
- `notion_mcp_agent` —— 把 Notion 当数据源
- `multi_mcp_agent_router` —— 多 MCP 路由器

这一层对正在评估「MCP 到底值不值得接入」的团队最有价值：你可以在不写新框架的前提下，逐个克隆对照接入成本与延迟。

### 6. RAG Tutorials：从基础到图谱

`rag_tutorials/` 是仓库最厚的目录之一，覆盖：

- 基础：`basic_rag_chain`、`rag_database_routing`
- Agentic：`agentic_rag_embedding_gemma`、`agentic_rag_with_reasoning`、`autonomous_rag`
- 多模态：`vision_rag`、`multimodal_agentic_rag`
- 高级：`knowledge_graph_rag_citations`、`rag_failure_diagnostics_clinic`、`rag-as-a-service`

值得特别看的是 `rag_failure_diagnostics_clinic`：它把「RAG 失败模式」做成了可对照排错的清单，比起能跑起来的 RAG，它更像一份事后复盘手册。

## 任务流案例：如何用这个仓库做一个新项目

把仓库当成「**能力拼图库**」使用，而非「一键生成器」。下面是一个典型任务流：

1. **明确能力需求**：先决定你要的是「**单 Agent 跑通**」还是「**多 Agent 协作 + 长期记忆 + 实时语音**」。前者看 `starter_ai_agents/`，后者看 `advanced_ai_agents/` 或 `multi-agent`。
2. **挑最近的模板做底座**：选一个目录结构、依赖、Prompt 风格最接近你目标的模板，clone 后改，而不是从零写。
3. **替换模型 / 数据源**：因为模板都是 provider-agnostic，把 OpenAI 换成 Claude / Gemini 通常只需要改环境变量和 Prompt 细节。
4. **横向看其他模板补能力**：比如起步用了 Starter AI Agents，跑通后想加记忆，就去 `advanced_llm_apps/llm_apps_with_memory_tutorials/` 找同名变体（如 `ai_travel_agent_memory/`）。
5. **遇到能力轴空白**：如果目标是「优化成本 / Token」，跳到 `llm_optimization_tools/`；目标是「接入外部工具」，跳到 `mcp_ai_agents/`。
6. **遇到框架选型问题**：翻 `ai_agent_framework_crash_course/` —— Google ADK 与 OpenAI Agents SDK 各有一个体系化教程，能帮你做框架级决策。

这条路径的核心收益是「**少写胶水代码**」：每个模板都自带一个能跑通的小世界，你只需要替换核心变量。

## 技术栈与依赖

从 README 与子目录的 `requirements.txt` 来看，这个仓库没有强约束一个统一技术栈，而是按模板分别选择：

- **Agent 编排**：LangGraph、CrewAI、AutoGen、Google ADK、OpenAI Agents SDK 都有覆盖
- **Web 界面**：Streamlit 占绝大多数，少量用 Gradio
- **检索**：Chroma、FAISS、Pinecone、Qdrant、`pgvector`
- **语音**：Gemini Live、OpenAI Realtime、ElevenLabs
- **模型**：Claude / Gemini / GPT / Llama / Qwen / xAI 均可适配

这种「按能力选型」的策略让仓库更像「**实战样本库**」而非「**统一框架教学**」。

## 适用人群

| 人群 | 这个仓库的用法 |
|------|----------------|
| 刚接触 LLM 应用的开发者 | 从 `starter_ai_agents/` 入手，看每个 Agent 怎么拼工具 / Prompt |
| 想评估 MCP 接入成本 | 翻 `mcp_ai_agents/`，逐个 clone 看配置 |
| 想学 Google ADK / OpenAI Agents SDK | 走 `ai_agent_framework_crash_course/` |
| 做 Agent 产品化的工程师 | 用 `advanced_ai_agents/` + `multi-agent/` 当起点 |
| 研究 RAG 失败模式 | 重点看 `rag_failure_diagnostics_clinic/` |
| 想搭 Always-on / 后台 Agent | `always_on_agents/` 是少数公开样本 |

## 适用边界与不适用场景

下面几类需求用这个仓库价值不大，读者应另选工具：

- **生产级框架选型**：如果你需要成熟的工程化、监控、可观测性、权限控制，应当直接评估 LangGraph、Google ADK、OpenAI Agents SDK、CrewAI 等官方框架，不要从 awesome 集合里拼装。
- **大型单体项目**：仓库内每个模板都假设「独立运行」，把多个模板拼成一个大项目需要自己做集成层。
- **企业级安全 / 合规**：模板默认使用公开 API Key 与云服务，没有内置审计、SSO、数据脱敏。
- **离线 / 边缘部署**：少数模板支持本地模型（如 `deepseek_local_rag_agent`），但整体仍偏向云端 API 路线。

## 阅读路径建议

如果你只有 1 小时，从这里开始：

1. 跑通 `starter_ai_agents/ai_travel_agent` —— 30 秒把第一个 Agent 启动
2. 看 `starter_ai_agents/multimodal_ai_agent` —— 理解多模态 Prompt
3. 翻 `rag_tutorials/basic_rag_chain` —— 对照一个最小 RAG 实现
4. 读 `rag_tutorials/rag_failure_diagnostics_clinic` —— 建立「什么会失败」的心智模型

如果你有半天，按这条路径读会更有体系感：

`starter_ai_agents` → `rag_tutorials/basic_rag_chain` → `rag_tutorials/agentic_rag_with_reasoning` → `mcp_aiagents/github_mcp_agent` → `multi-agent/ai_legal_agent_team` → `voice_ai_agents/customer_support_voice_agent` → `always_on_agents/always_on_hn_briefing_agent` → `ai_agent_framework_crash_course/google_adk_crash_course`

## 仓库地址

<https://github.com/Shubhamsaboo/awesome-llm-apps>