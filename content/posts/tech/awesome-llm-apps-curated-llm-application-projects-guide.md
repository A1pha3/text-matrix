---
title: "awesome-llm-apps：105k Stars LLM应用精选合集完全指南"
date: "2026-04-06T22:40:00+08:00"
slug: "awesome-llm-apps-curated-llm-application-projects-guide"
description: "全面介绍105k Stars的awesome-llm-apps精选合集，涵盖100+ LLM应用项目，包括AI Agent、RAG、MCP、Voice Agents、多Agent协作等，详解Google ADK、OpenAI Agents SDK等框架。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "AI Agent", "RAG", "MCP", "Multi-Agent", "Voice AI", "Google ADK", "OpenAI Agents SDK"]
---

---

. 项目概述

. 是什么

**awesome-llm-apps** 是一个精心策划的 LLM 应用精选合集，收录了大量基于 RAG、AI Agents、Multi-agent Teams、MCP、Voice Agents 等技术构建的 AI 应用。项目作者 Shubhamsaboo 来自 The Unwind AI 团队。

. 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **105k** |
| GitHub Forks | **15.3k** |
| Contributors | **200+** |
| Commits | **963** |
| License | **Apache-2.0** |
| 最新更新 | **2026-03-28** |

. 技术栈

| 语言 | 占比 |
|------|------|
| Python | **68.7%** |
| JavaScript | **21.9%** |
| TypeScript | **8.1%** |

. 支持的模型

| 厂商 | 模型 |
|------|------|
| **OpenAI** | GPT-4o, GPT-4, GPT-3.5 |
| **Anthropic** | Claude 3.5, Claude 3 |
| **Google** | Gemini 1.5, Gemma |
| **xAI** | Grok |
| **Meta** | Llama 3.2, Llama 3.1 |
| **Alibaba** | Qwen |
| **开源本地模型** | Ollama 支持的所有模型 |

---

. 项目架构

. 目录结构

```
awesome-llm-apps/
├── starter_ai_agents/ # 🌱 入门级 AI Agent
├── advanced_ai_agents/ # 🚀 进阶 AI Agent
├── advanced_llm_apps/ # 💾 LLM 应用 + Memory
├── ai_agent_framework_crash_course/ # 🧑‍🏫 Agent 框架课程
├── awesome_agent_skills/ # 🧩 Agent Skills
├── mcp_ai_agents/ # 🤖 MCP AI Agents
├── rag_tutorials/ # 📀 RAG 教程
├── voice_ai_agents/ # 🗣️ 语音 AI Agents
└── docs/ # 文档资源
```

. 项目分类

| 类别 | 说明 | 项目数量 |
|------|------|----------|
| 🌱 Starter AI Agents | 入门级 AI Agent | 12+ |
| 🚀 Advanced AI Agents | 进阶 AI Agent | 20+ |
| 🤝 Multi-agent Teams | 多 Agent 协作 | 15+ |
| 🎮 Autonomous Game Agents | 自主游戏 Agent | 3+ |
| 🗣️ Voice AI Agents | 语音交互 Agent | 4+ |
| 🤖 MCP AI Agents | MCP 协议 Agent | 5+ |
| 📀 RAG | 检索增强生成 | 20+ |
| 💾 Memory Apps | 带记忆的 LLM 应用 | 6+ |
| 💬 Chat with X | 对话式应用 | 6+ |
| 🎯 LLM Optimization | LLM 优化工具 | 2+ |
| 🔧 Fine-tuning | 模型微调 | 2+ |

---

. Starter AI Agents（入门级）

. 项目列表

| Agent | 功能 | 特点 |
|-------|------|------|
| **AI Blog to Podcast Agent** | 博客转播客 | 自动转换文章为语音 |
| **AI Breakup Recovery Agent** | 情感恢复助手 | 心理健康支持 |
| **AI Data Analysis Agent** | 数据分析 | 自动分析数据集 |
| **AI Medical Imaging Agent** | 医学影像 | CT/MRI 图像分析 |
| **AI Meme Generator Agent** | 表情包生成 | 浏览器自动化生成 |
| **AI Music Generator Agent** | 音乐生成 | AI 作曲 |
| **AI Travel Agent** | 旅行规划 | 本地+云端双模式 |
| **Gemini Multimodal Agent** | 多模态 Agent | Gemini 视觉+语音 |
| **Mixture of Agents** | 混合专家 Agent | 多模型协作 |
| **xAI Finance Agent** | 金融分析 | xAI Grok 驱动 |
| **OpenAI Research Agent** | 科研助手 | ArXiv 论文分析 |
| **Web Scraping AI Agent** | 网页爬虫 | 本地+云端 SDK |

. AI Travel Agent 详解

```python
AI Travel Agent 核心架构
class TravelAgent:
 def __init__(self, llm, search_tool, booking_tool):
 self.llm = llm
 self.search = search_tool
 self.booking = booking_tool

 def plan_trip(self, destination, dates, budget):
 # 1. 搜索目的地信息
 info = self.search.search(destination)

 # 2. 制定行程
 itinerary = self.llm.generate(
 f"根据信息 {info} 制定 {dates} 的行程，预算 {budget}"
 )

 # 3. 预订机票酒店
 bookings = self.booking.book(itinerary)

 return {"itinerary": itinerary, "bookings": bookings}
```

. AI Data Analysis Agent

```python
AI Data Analysis Agent 核心流程
from langchain.agents import Agent
from langchain.tools import PythonREPLTool

创建数据分析 Agent
data_agent = Agent(
 llm=llm,
 tools=[
 PythonREPLTool(), # 执行 Python 代码
 DataLoader(), # 加载数据集
 VisualizationTool() # 生成可视化
 ],
 prompt="你是一个专业的数据分析师，可以加载、清洗、分析数据并生成可视化"
)

分析数据
result = data_agent.run(
 "加载 sales.csv，计算月环比增长率，生成趋势图"
)
```

---

. Advanced AI Agents（进阶级）

. Single Agent 应用

| Agent | 功能 | 场景 |
|-------|------|------|
| **AI Deep Research Agent** | 深度研究 | 市场调研、竞品分析 |
| **AI Consultant Agent** | 商业咨询 | 战略建议 |
| **AI System Architect Agent** | 系统架构 | 技术方案设计 |
| **AI Financial Coach Agent** | 财务规划 | 投资建议 |
| **AI Movie Production Agent** | 电影制作 | 剧本生成、剪辑 |
| **AI Investment Agent** | 投资分析 | 股票、基金分析 |
| **AI Health & Fitness Agent** | 健康管理 | 健身计划、饮食建议 |
| **AI Journalist Agent** | 新闻写作 | 文章创作 |
| **AI Meeting Agent** | 会议助手 | 会议记录、总结 |
| **AI Self-Evolving Agent** | 自我进化 | 持续学习改进 |

. Multi-Agent Teams（多 Agent 协作）

| Agent Team | 功能 | Agent 数量 |
|------------|------|-----------|
| **AI VC Due Diligence Agent Team** | 投资尽调 | 3+ |
| **AI Finance Agent Team** | 金融分析团队 | 3+ |
| **AI Legal Agent Team** | 法律咨询团队 | 3+ |
| **AI Recruitment Agent Team** | 招聘团队 | 3+ |
| **AI Real Estate Agent Team** | 房产咨询团队 | 3+ |
| **AI Teaching Agent Team** | 教学团队 | 3+ |
| **AI Competitor Intelligence Team** | 竞情分析 | 3+ |
| **AG2 Adaptive Research Team** | 自适应研究 | 3+ |

. AI VC Due Diligence Agent Team

```python
多 Agent 协作架构
from crewai import Agent, Task, Crew

创建多个专业 Agent
market_agent = Agent(
 role="Market Analyst",
 goal="分析目标公司的市场份额和竞争格局",
 backstory="你是一名资深的行业分析师"
)

financial_agent = Agent(
 role="Financial Analyst",
 goal="评估公司的财务健康状况",
 backstory="你是一名资深的财务分析师"
)

legal_agent = Agent(
 role="Legal Analyst",
 goal="识别潜在的法律风险",
 backstory="你是一名资深律师"
)

组建团队
crew = Crew(
 agents=[market_agent, financial_agent, legal_agent],
 tasks=[market_task, financial_task, legal_task],
 process="hierarchical" # 层级协作
)

执行任务
result = crew.kickoff()
```

. AI Self-Evolving Agent

```python
自我进化 Agent 核心机制
class SelfEvolvingAgent:
 def __init__(self, llm):
 self.llm = llm
 self.performance_history = []
 self.skills = {}

 def execute_task(self, task):
 result = self.llm.execute(task)

 # 1. 评估表现
 score = self.evaluate_performance(result)

 # 2. 记录经验
 self.performance_history.append({
 "task": task,
 "result": result,
 "score": score
 })

 # 3. 如果表现不佳，改进策略
 if score < threshold:
 self.improve_strategy(task, result)

 return result

 def improve_strategy(self, task, result):
 # 分析失败原因
 failure_analysis = self.analyze_failure(task, result)

 # 生成改进建议
 improvement = self.llm.generate(
 f"分析以下失败案例并提出改进建议：{failure_analysis}"
 )

 # 更新 Agent 策略
 self.update_strategy(improvement)
```

---

. Autonomous Game Playing Agents

. 游戏 Agent 列表

| Agent | 游戏 | 难度 |
|-------|------|------|
| **AI 3D Pygame Agent** | 3D Pygame | 高 |
| **AI Chess Agent** | 国际象棋 | 中 |
| **AI Tic-Tac-Toe Agent** | 三子棋 | 低 |

. AI Chess Agent 核心逻辑

```python
import chess
from langchain.agents import Agent

创建棋类 Agent
chess_agent = Agent(
 llm=llm,
 tools=[chess_ai_engine],
 prompt="你是一名国际象棋大师，可以分析棋局并制定最优策略"
)

对弈
board = chess.Board()
while not board.is_game_over():
 # Agent 思考下一步
 move = chess_agent.execute(
 f"当前棋局：{board.fen()}，请给出下一步棋"
 )

 # 执行棋步
 board.push_san(move)

 print(f"Agent 走棋：{move}")
```

---

. Voice AI Agents

. 语音 Agent 项目

| Agent | 功能 | 技术栈 |
|-------|------|--------|
| **AI Audio Tour Agent** | 语音导览 | Whisper + GPT |
| **Customer Support Voice Agent** | 客服语音 | Twilio + ElevenLabs |
| **Voice RAG Agent** | 语音问答 | OpenAI Realtime API |
| **OpenSource Voice Dictation** | 开源语音输入 | Whisper + .jarvis-ai-assistant |

. Voice RAG Agent 架构

```python
Voice RAG Agent 核心流程
class VoiceRAGAgent:
 def __init__(self):
 self.stt = WhisperSTT() # 语音转文字
 self.rag = RAGPipeline() # RAG 检索
 self.tts = ElevenLabsTTS() # 文字转语音

 def handle_voice_query(self, audio):
 # 1. 语音转文字
 query = self.stt.transcribe(audio)

 # 2. RAG 检索答案
 answer = self.rag.retrieve_and_generate(query)

 # 3. 文字转语音
 response_audio = self.tts.speak(answer)

 return response_audio
```

---

. MCP AI Agents

. MCP 概述

**MCP（Model Context Protocol）** 是一种开放协议，允许 AI Agent 与外部工具和数据源连接。

. MCP Agent 列表

| Agent | 数据源 | 功能 |
|-------|--------|------|
| **Browser MCP Agent** | 浏览器 | 网页自动化 |
| **GitHub MCP Agent** | GitHub | 代码托管自动化 |
| **Notion MCP Agent** | Notion | 笔记管理 |
| **AI Travel Planner MCP Agent** | 旅行数据 | 智能规划 |
| **Multi-MCP Agent Router** | 多数据源 | 智能路由 |

. Browser MCP Agent

```python
Browser MCP Agent 示例
from mcp.client import MCPClient

连接浏览器 MCP 服务器
browser_mcp = MCPClient("http://localhost:3000")

创建 Browser Agent
browser_agent = Agent(
 llm=llm,
 tools=[
 browser_mcp.navigate(url), # 导航到 URL
 browser_mcp.screenshot(), # 截图
 browser_mcp.click(selector), # 点击元素
 browser_mcp.type_text(text), # 输入文本
 browser_mcp.get_content(), # 获取页面内容
 ]
)

执行任务
result = browser_agent.run(
 "访问 GitHub，搜索 awesome-llm-apps 仓库，获取 star 数量"
)
```

. Multi-MCP Agent Router

```python
Multi-MCP Agent Router
class MultiMCPRouter:
 def __init__(self, mcps):
 self.mcps = mcps

 async def route(self, query):
 # 分析查询类型
 intent = self.classify_intent(query)

 # 选择合适的 MCP
 if "github" in intent:
 return await self.mcps["github"].process(query)
 elif "notion" in intent:
 return await self.mcps["notion"].process(query)
 elif "web" in intent:
 return await self.mcps["browser"].process(query)
 else:
 # 多 MCP 协作
 results = await asyncio.gather(*[
 mcp.process(query) for mcp in self.mcps.values()
 ])
 return self.synthesize(results)
```

---

. RAG 检索增强生成

. RAG 项目列表（+）

| 项目 | 模型 | 特点 |
|------|------|------|
| **Agentic RAG with Gemma** | Gemma | Agent 化 RAG |
| **Agentic RAG with Reasoning** | GPT-4 | 推理增强 |
| **Autonomous RAG** | Llama 3 | 自主检索 |
| **Contextual AI RAG** | Claude | 上下文感知 |
| **Corrective RAG (CRAG)** | 多模型 | 错误纠正 |
| **Deepseek Local RAG** | Deepseek | 本地部署 |
| **Gemini Agentic RAG** | Gemini | 多模态 |
| **Hybrid Search RAG** | GPT-4 | 混合检索 |
| **Llama 3.1 Local RAG** | Llama 3.1 | 本地部署 |
| **Knowledge Graph RAG** | GPT-4 | 知识图谱 |
| **Vision RAG** | GPT-4V | 图像问答 |
| **RAG with Database Routing** | GPT-4 | 多数据库 |

. Agentic RAG 架构

```python
Agentic RAG 核心流程
from langchain.agents import Agent
from langchain.retrievers import VectorStoreRetriever

创建 Agentic RAG
agentic_rag = Agent(
 llm=llm,
 tools=[
 VectorStoreRetriever(vectorstore), # 向量检索
 WebSearchTool(), # 网络搜索
 KnowledgeGraphTool(), # 知识图谱
 ],
 prompt="""你是一个研究助手。当用户提问时：
 1. 先检索向量数据库
 2. 如需最新信息，使用网络搜索
 3. 如需关系信息，查询知识图谱
 4. 综合所有来源生成答案"""
)

检索增强生成
result = agentic_rag.run(
 "查找 2024 年 AI Agent 领域的最新研究进展"
)
```

. Knowledge Graph RAG

```python
Knowledge Graph RAG with Citations
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Chroma

初始化知识图谱和向量数据库
graph = Neo4jGraph(url="bolt://localhost:7687", username="neo4j", password="password")
vectorstore = Chroma(persist_directory="./chroma_db")

知识图谱增强检索
def kg_enhanced_retrieval(query, top_k=5):
 # 1. 向量相似度检索
 vector_results = vectorstore.similarity_search(query, k=top_k)

 # 2. 知识图谱关系检索
 entities = extract_entities(query)
 kg_results = []
 for entity in entities:
 kg_results.extend(graph.query(f"""
 MATCH (e)-[r]-(related)
 WHERE e.name = '{entity}'
 RETURN e, r, related
 LIMIT 5
 """))

 # 3. 合并结果并去重
 combined = merge_results(vector_results, kg_results)

 # 4. 生成带引用的答案
 answer = llm.generate(
 f"基于以下上下文回答：{combined}\n\n 问题：{query}"
 )

 return answer
```

---

. LLM Apps with Memory

. Memory 应用列表

| 应用 | 功能 | 记忆类型 |
|------|------|----------|
| **AI ArXiv Agent with Memory** | 论文阅读助手 | 论文记忆 |
| **AI Travel Agent with Memory** | 旅行记忆 | 偏好记忆 |
| **Llama 3 Stateful Chat** | 有状态对话 | 对话历史 |
| **LLM App with Personalized Memory** | 个性化记忆 | 用户画像 |
| **Local ChatGPT Clone with Memory** | 本地 ChatGPT | 全历史 |
| **Multi-LLM with Shared Memory** | 多模型共享 | 团队记忆 |

. 个性化记忆系统

```python
LLM App with Personalized Memory
class PersonalizedMemory:
 def __init__(self, llm, vectorstore):
 self.llm = llm
 self.memory_store = vectorstore
 self.user_profile = {}

 def update_memory(self, interaction):
 # 1. 提取关键信息
 key_info = self.extract_key_info(interaction)

 # 2. 存储到向量数据库
 self.memory_store.add_documents(key_info)

 # 3. 更新用户画像
 self.user_profile.update(self.infer_preferences(interaction))

 def generate_response(self, query):
 # 1. 检索相关记忆
 relevant_memory = self.memory_store.similarity_search(
 query,
 filter={"user_id": self.user_id}
 )

 # 2. 构建个性化提示
 personalized_prompt = self.build_prompt(
 query=query,
 memory=relevant_memory,
 profile=self.user_profile
 )

 # 3. 生成响应
 return self.llm.generate(personalized_prompt)
```

---

. Chat with X 应用

. 对话式应用列表

| 应用 | 数据源 | 功能 |
|------|--------|------|
| **Chat with GitHub** | GitHub | 代码问答 |
| **Chat with Gmail** | Gmail | 邮件处理 |
| **Chat with PDF** | PDF 文档 | 文档理解 |
| **Chat with Research Papers** | ArXiv | 论文分析 |
| **Chat with Substack** | Substack | 文章订阅 |
| **Chat with YouTube** | YouTube | 视频摘要 |

. Chat with GitHub

```python
Chat with GitHub 核心功能
class ChatWithGitHub:
 def __init__(self, llm, github_token):
 self.github = GitHubAPI(token=github_token)
 self.llm = llm

 def chat_about_repo(self, repo_url, question):
 # 1. 获取仓库信息
 repo_info = self.github.get_repo_info(repo_url)

 # 2. 获取相关代码
 code_snippets = self.github.search_code(
 repo=repo_url,
 query=question
 )

 # 3. 生成答案
 answer = self.llm.generate(
 f"仓库信息：{repo_info}\n\n 相关代码：{code_snippets}\n\n 问题：{question}"
 )

 return answer
```

---

. AI Agent 框架课程

. Google ADK Crash Course

| 模块 | 内容 |
|------|------|
| **Starter Agent** | 基础 Agent 开发 |
| **Function Calling** | 函数调用 |
| **Structured Outputs** | 结构化输出（Pydantic） |
| **Built-in Tools** | 内置工具 |
| **MCP Tools** | MCP 工具集成 |
| **Memory** | 记忆系统 |
| **Callbacks** | 回调机制 |
| **Plugins** | 插件开发 |
| **Multi-agent Patterns** | 多 Agent 模式 |

. OpenAI Agents SDK Crash Course

| 模块 | 内容 |
|------|------|
| **Starter Agent** | 入门开发 |
| **Function Calling** | 函数调用 |
| **Structured Outputs** | 结构化输出 |
| **Third-party Integrations** | 第三方集成 |
| **Memory** | 记忆系统 |
| **Evaluation** | 评估机制 |
| **Agent Handoffs** | Agent 转交 |
| **Swarm Orchestration** | Swarm 编排 |
| **Routing Logic** | 路由逻辑 |

. ADK 开发示例

```python
Google ADK 开发示例
from google.adk.agents import Agent
from google.adk.tools import google_search, python_repl

创建 Agent
research_agent = Agent(
 name="research_agent",
 model="gemini-2.0-flash",
 description="专业的研究助手",
 tools=[google_search, python_repl]
)

创建 App
app = Agent(
 name="research_team",
 model="gemini-2.0-flash",
 agents=[research_agent],
 instruction="你是一个研究团队，可以协调多个专业研究员完成任务"
)

运行
result = app.run("研究 2024 年 AI Agent 领域的最新进展")
```

---

. LLM 优化工具

. Toonify Token 优化

**Toonify** 可以将文本转换为更紧凑的格式，降低 30-60% 的 API 成本：

```python
Toonify Token 优化
from toonify import Toonifier

toonifier = Toonifier()

原始文本
original = """
The user wants to create a new machine learning project.
We need to set up the environment, install dependencies,
configure the model, train the model, evaluate the results,
and deploy to production.
"""

Toonify 压缩
compressed = toonifier.compress(original)
输出：USER→ML_PROJECT→ENV+DEPS+MODEL+TRAIN+EVAL+DEPLOY

恢复
restored = toonifier.restore(compressed)
```

. Headroom Context 优化

**Headroom** 通过智能上下文管理，可降低 50-90% 的 API 成本：

```python
Headroom Context 优化
from headroom import HeadroomOptimizer

optimizer = HeadroomOptimizer(
 max_tokens=8192,
 strategy="importance_based" # 基于重要性的保留策略
)

优化上下文
optimized_context = optimizer.optimize(
 full_context=long_context,
 query=current_query
)

只保留与当前查询最相关的上下文
response = llm.generate(optimized_context)
```

---

. 常见问题

. 如何选择合适的 Agent 类型

| 场景 | 推荐 |
|------|------|
| 学习入门 | Starter AI Agents |
| 生产环境 | Advanced AI Agents |
| 复杂任务 | Multi-agent Teams |
| 语音交互 | Voice AI Agents |
| 数据检索 | RAG Tutorials |
| 本地部署 | Local RAG + Ollama |

. 如何本地运行

```bash
. 克隆仓库
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps

. 安装依赖
pip install -r requirements.txt

. 设置环境变量
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

. 运行示例
cd starter_ai_agents/ai_travel_agent
python app.py
```

. 如何贡献

1. Fork 仓库
2. 创建新分支：`git checkout -b feature/new-agent`
3. 添加你的 Agent 项目
4. 更新 README.md
5. 提交 Pull Request

---

. 总结

**awesome-llm-apps** 是 LLM 应用开发的优秀资源库：

| 维度 | 评价 |
|------|------|
| **项目数量** | ⭐⭐⭐⭐⭐ 100+ 应用 |
| **覆盖范围** | ⭐⭐⭐⭐⭐ Agent、RAG、MCP、Voice |
| **代码质量** | ⭐⭐⭐⭐⭐ 详细注释、可运行 |
| **学习价值** | ⭐⭐⭐⭐⭐ 入门到进阶全覆盖 |
| **社区活跃** | ⭐⭐⭐⭐⭐ 持续更新 |

**适用人群**：

- 想入门 LLM 应用开发的开发者
- 想构建 AI Agent 的工程师
- 对 RAG、MCP 等技术感兴趣的研究者
- 想了解 AI 应用落地实践的产品经理

**官方资源**：

- GitHub：https://github.com/Shubhamsaboo/awesome-llm-apps
- 作者网站：https://www.theunwindai.com
- LinkedIn：https://www.linkedin.com/in/shubhamsaboo/