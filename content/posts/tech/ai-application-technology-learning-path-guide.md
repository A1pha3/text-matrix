+++
date = '2026-08-16T01:01:46+08:00'
draft = false
title = 'Ai Application Technology Learning Path Guide'
slug = 'ai-application-technology-learning-path-guide'
categories = ['技术笔记']

+++

   1→---
   2→title: "近年 AI 应用技术学习路线：从 LLM、RAG 到 Agent 工程"
   3→date: "2026-04-14T10:30:00+08:00"
   4→slug: "ai-application-technology-learning-path-guide"
   5→github_repo: "anthropics/anthropic-cookbook"
   6→summary: "一篇面向工程师的 AI 应用技术路线图：先把 LLM、Prompt、RAG、Function Calling 与 MCP 打稳，再进入 Agent、Workflow、Context、Skill 与评估工程。"
   7→description: "系统梳理 LLM、Prompt Engineering、Fine-tuning、RAG、MCP、Agent、Multi-Agent、Workflow Engineering、Context Engineering、Agent Skill、OpenClaw、Harness Engineering 等核心主题，给出从入门到进阶的学习顺序、工程边界、练习题与实战示例。"
   8→draft: false
   9→categories: ["技术笔记"]
  10→tags: ["LLM", "AI Agent", "Prompt Engineering", "MCP", "RAG"]
  11→---
  12→
  13→> **目标读者**：希望系统掌握 AI 应用技术的开发者与工程师
  14→> **前置知识**：掌握至少一门编程语言，了解基本的数据结构和算法
  15→> **预计完成时间**：3 到 6 个月，取决于每周投入时间和已有工程基础
  16→
  17→<!-- truncate -->
  18→
  19→## 学习目标
  20→
  21→读完本文后，你应该能够：
  22→
  23→- 画出 AI 应用技术栈的三层核心组成（模型层、应用层、基础设施层）并解释分层的必要性
  24→- 对比 RAG 与 Fine-tuning 的适用边界，能为具体场景选择合适方案
  25→- 解释 MCP 协议解决的本质问题，并说明为什么它需要成为开放标准
  26→- 设计一个包含工具调用和记忆管理的简单 Agent 系统
  27→- 制定一条从课程学习到生产部署的完整迁移路径
  28→
  29→---
  30→
  31→## 目录
  32→
  33→- [前言](#前言)
  34→- [学习路线总览](#学习路线总览)
  35→- [§1 LLM：大语言模型基础](#1-llm 大语言模型基础-)
  36→- [§2 Prompt Engineering：提示词工程](#2-prompt-engineering 提示词工程-)
  37→- [§3 Fine-tuning：微调技术](#3-fine-tuning 微调技术-)
  38→- [§4 RAG：检索增强生成](#4-rag 检索增强生成-)
  39→- [§5 Function Calling 与 MCP](#5-function-calling-与-mcp-)
  40→- [§6 Agent：智能体架构](#6-agent 智能体架构-)
  41→- [§7 Multi-Agent：多智能体系统](#7-multi-agent 多智能体系统-)
  42→- [§8 Workflow Engineering：工作流编排](#8-workflow-engineering 工作流编排-)
  43→- [§9 Context Engineering：上下文工程](#9-context-engineering 上下文工程-)
  44→- [§10 Agent Skill：智能体技能](#10-agent-skill 智能体技能-)
  45→- [§11 OpenClaw：开源智能体框架](#11-openclaw 开源智能体框架-)
  46→- [§12 Harness Engineering：评估工程](#12-harness-engineering 评估工程-)
  47→- [端到端实战：构建企业知识库问答智能体](#端到端实战构建企业知识库问答智能体)
  48→- [学习路线总结](#学习路线总结)
  49→- [练习](#练习)
  50→- [自测题](#自测题)
  51→- [常见问题 FAQ](#常见问题-faq)
  52→- [推荐学习资源](#推荐学习资源)
  53→- [进阶路径指引](#进阶路径指引)
  54→- [核心术语表](#核心术语表)
  55→
  56→---
  57→
  58→## 前言
  59→
  60→过去几年，AI 应用开发从"会调用一个聊天接口"迅速演化成一套完整工程体系：模型选择、提示词、检索、工具调用、上下文管理、工作流、智能体、评估集。任何一环薄弱，最终产品都会在稳定性、成本或可维护性上出问题。
  61→
  62→这篇文章把近年最常见的 AI 应用技术主题串成一条学习路线。它适合两类读者：一类是想从零建立系统认知的开发者，另一类是已经做过 Prompt、RAG 或 Agent 项目，但希望补齐工程全貌的人。
  63→
  64→读完后，至少应该能做到下面几件事：
  65→
  66→- 建立 AI 应用技术的系统认知框架
  67→- 理解每个技术的核心原理与适用边界
  68→- 掌握从理论到实践的完整学习顺序
  69→- 可直接复用的代码示例与配置方案
  70→- 每个主题的练习题与自测检查清单
  71→
  72→**本文定位**：这是一篇技术路线图，不是单点深度教程。每个主题都会交代核心概念、为什么需要它、适用边界和最小实践；真正进入生产系统时，还需要结合具体模型、数据、权限、安全和成本约束继续细化。
  73→
  74→---
  75→
  76→## 学习路线总览
  77→
  78→这条路线可以拆成三种阅读深度。初学者先拿到概念地图，有经验的开发者重点看实现取舍，架构师和团队负责人则更应该关注边界、评估和治理。
  79→
  80→| 路径 | 目标人群 | 核心问题 | 难度范围 |
  81→| ---- | ---- | ---- | ---- |
  82→| 入门路径 | AI 初学者 | 这个技术是什么？ | ⭐ 到 ⭐⭐ |
  83→| 进阶路径 | 有经验的开发者 | 这个怎么实现？ | ⭐⭐ 到 ⭐⭐⭐ |
  84→| 专家路径 | 架构师与团队负责人 | 为什么这样设计？ | ⭐⭐⭐ 到 ⭐⭐⭐⭐ |
  85→
  86→**建议的学习顺序**：LLM 基础 → Prompt Engineering → RAG → Function Calling / MCP → Agent → Workflow / Context → Multi-Agent → Skill / Evaluation
  87→
  88→**依赖关系图**：
  89→
  90→```text
  91→LLM 基础 ──────→ Prompt Engineering ──────→ Fine-tuning
  92→    │                    │                      │
  93→    │                    ▼                      ▼
  94→    │              Function Calling          RAG
  95→    │                    │                      │
  96→    │                    ▼                      │
  97→    │                   MCP ────────────────────┤
  98→    │                    │                      │
  99→    ▼                    ▼                      ▼
 100→  智能体 ←──────────── Context Engineering
 101→    │
 102→    ▼
 103→  Multi-Agent ──→ Workflow Engineering ──→ Agent Skill
 104→    │
 105→    ▼
 106→  OpenClaw ──→ Harness Engineering
 107→```
 108→
 109→---
 110→
 111→## §1 LLM：大语言模型基础
 112→
 113→LLM 是整条路线的地基。理解它，重点不在背参数，而在知道它"能做什么、不能做什么"。
 114→
 115→现代主流 LLM 几乎都基于 Transformer 的 **Decoder-Only** 架构——只保留自回归解码部分，输入一段文本，逐个 Token 预测下一个 Token。相比 BERT 的 Encoder-Only 和 T5 的 Encoder-Decoder，Decoder-Only 在生成式任务上表现更稳，也成为 GPT、Llama 等模型的一致选择。
 116→
 117→```mermaid
 118→graph TD
 119→    A[Transformer 原始架构] --> B[Encoder-Only<br/>如 BERT]
 120→    A --> C[Encoder-Decoder<br/>如 T5]
 121→    A --> D[Decoder-Only<br/>当前主流: GPT、Llama]
 122→    style D stroke:#f66,stroke-width:2px
 123→```
 124→
 125→Decoder-Only 的核心机制是**自注意力（Self-Attention）**：序列中每个 Token 都会对序列内所有其他 Token 计算相关性权重，再按权重加权求和得到自己的新表示。这正是它能"理解上下文"的根源——捕捉长距离依赖就是靠这一步。
 126→
 127→```text
 128→输入序列：["我", "喜欢", "AI", "技术"]
 129→
 130→自注意力计算（简化）：
 131→每个 Token 都会"关注"所有其他 Token，计算相关性权重：
 132→
 133→"我"   → 关注 [我:0.3, 喜欢:0.5, AI:0.1, 技术:0.1]  → 主要是"喜欢"的施事者
 134→"喜欢" → 关注 [我:0.4, 喜欢:0.1, AI:0.3, 技术:0.2]  → "我"喜欢"AI"和"技术"
 135→"AI"   → 关注 [我:0.1, 喜欢:0.3, AI:0.2, 技术:0.4]  → "AI"是一种"技术"
 136→"技术" → 关注 [我:0.1, 喜欢:0.2, AI:0.4, 技术:0.3]  → 与"AI"强关联
 137→
 138→→ 每个 Token 的表示 = 所有 Token 的加权求和
 139→→ 权重越大，表示该 Token 对当前 Token 越重要
 140→```
 141→
 142→**工程边界**：LLM 自己是"无状态函数"——它不知道训练数据截止之后的事，也不知道你的私有数据。这让"如何把外部知识、工具、上下文喂给它"成为后续所有章节的主题。
 143→
 144→---
 145→
 146→## §2 Prompt Engineering：提示词工程
 147→
 148→提示词工程的目标是：**不改模型参数，仅通过组织输入来引导正确的输出**。它的杠杆来自一个事实——LLM 是从海量文本里学出来的，对输入的"模式"极其敏感。
 149→
 150→最有效的三种手段：
 151→
 152→1. **Few-Shot 示例**：给出输入输出对，让模型模仿格式。适合翻译、分类、抽取等结构化任务。
 153→2. **思维链（CoT）**：要求模型"展示推理过程"，能显著提升数学、逻辑类问题的正确率。
 154→3. **角色设定与约束**：用明确的角色、任务、约束、输出格式把任务边界说清楚。
 155→
 156→```markdown
 157→# 示例：翻译任务
 158→
 159→# 示例 1
 160→用户：把"早上好"翻译成英文
 161→AI：Good morning
 162→
 163→# 示例 2
 164→用户：把"晚安"翻译成英文
 165→AI：Good night
 166→
 167→# 正式请求
 168→用户：把"你好"翻译成英文
 169→AI：
 170→```
 171→
 172→```markdown
 173→# 示例：数学问题
 174→
 175→用户：计算 245 + 178，请展示计算过程。
 176→AI：让我一步步思考：
 177→
 178→第 1 步：245 + 100 = 345
 179→第 2 步：345 + 70 = 415
 180→第 3 步：415 + 8 = 423
 181→
 182→答案是 423
 183→```
 184→
 185→```markdown
 186→# 角色
 187→你是一位资深的前端工程师，擅长 React 和 TypeScript。
 188→
 189→# 任务
 190→审查以下代码，找出潜在的性能问题。
 191→
 192→# 约束
 193→- 只关注性能问题，不关注代码风格
 194→- 每个问题给出具体的修改建议
 195→- 按严重程度排序（高 → 中 → 低）
 196→
 197→# 输出格式
 198→| 问题 | 严重程度 | 位置 | 修改建议 |
 199→| ---- | ---- | ---- | ---- |
 200→
 201→# 代码
 202→{待审查的代码}
 203→```
 204→
 205→**工程边界**：提示词工程受上下文窗口限制，也无法让模型"记住"长期知识。当提示词怎么调都达不到效果、或需要模型固化某种行为时，就要考虑 §3 的微调。
 206→
 207→---
 208→
 209→## §3 Fine-tuning：微调技术
 210→
 211→微调是在**特定数据集上继续训练预训练模型**，让它适应特定任务。它解决的是提示词解决不了的问题：模型行为方式不对（输出风格、专业用语、固定格式）。
 212→
 213→全参微调代价极高。现实里更常用**参数高效微调（PEFT）**，其中 **LoRA（Low-Rank Adaptation）** 是最主流的一种：冻结原权重，只在旁边加一条低秩旁路，训练的参数占比常在 1% 以下。
 214→
 215→```text
 216→原始更新：ΔW (100×100 = 10,000 参数)
 217→LoRA 分解：A (100×2 = 200 参数) × B (2×100 = 200 参数)
 218→实际训练：400 参数 = 10,000 参数的 4%
 219→```
 220→
 221→```mermaid
 222→graph LR
 223→    subgraph 原始权重 W (d×d)
 224→        W0[冻结的 W₀]
 225→    end
 226→    
 227→    subgraph LoRA 旁路分支
 228→        A[A 矩阵 r×d<br/>可训练] --> B[B 矩阵 d×r<br/>可训练]
 229→    end
 230→    
 231→    Input(输入 x) --> W0
 232→    Input --> A
 233→    B --> Add((+))
 234→    W0 --> Add
 235→    Add --> Output(输出 y)
 236→```
 237→
 238→配合 Hugging Face 的 `peft` 库，用 LoRA 微调一个模型只需几行代码：
 239→
 240→```python
 241→import torch
 242→from peft import LoraConfig, get_peft_model
 243→from transformers import AutoModelForCausalLM
 244→
 245→model = AutoModelForCausalLM.from_pretrained(
 246→    "meta-llama/Meta-Llama-3-8B",
 247→    torch_dtype=torch.bfloat16,
 248→    device_map="auto"
 249→)
 250→
 251→lora_config = LoraConfig(
 252→    r=16,
 253→    lora_alpha=32,
 254→    target_modules=["q_proj", "v_proj"],
 255→    lora_dropout=0.05,
 256→    bias="none",
 257→    task_type="CAUSAL_LM"
 258→)
 259→
 260→model = get_peft_model(model, lora_config)
 261→model.print_trainable_parameters()
 262→# 输出示例：trainable params: 6,815,744 || all params: 8,075,097,856 || trainable%: 0.084%
 263→```
 264→
 265→**RAG vs 微调怎么选**：模型"不知道某个知识"（内部文档、最新新闻）→ 用 RAG；模型"行为方式不对"（输出格式、语气）→ 用微调。两者常组合使用。
 266→
 267→---
 268→
 269→## §4 RAG：检索增强生成
 270→
 271→RAG 解决 LLM 的两个天然短板：**知识有截止日期**、**无法访问私有数据**。思路是把答案的来源从"模型记忆"移到"外部知识库"。
 272→
 273→标准流程分两条流水线：
 274→
 275→```text
 276→┌─────────────────────────────────────────────────────────────┐
 277→│                      RAG 工作流程                              │
 278→└─────────────────────────────────────────────────────────────┘
 279→
 280→用户问题 ──→ 编码为向量 ──→ 在向量数据库中检索 ──→ 获取相关文档
 281→                                            │
 282→                                            ▼
 283→                        ┌───────────────────────────────┐
 284→                        │         LLM 生成答案            │
 285→                        │  (基于检索结果 + 自身知识)        │
 286→                        └───────────────────────────────┘
 287→                                            │
 288→                                            ▼
 289→                                        最终回答
 290→```
 291→
 292→```mermaid
 293→graph TD
 294→    subgraph 离线索引阶段
 295→        Doc[原始文档] --> Split[文本分割]
 296→        Split --> Embed[Embedding 编码]
 297→        Embed --> DB[(向量数据库)]
 298→    end
 299→
 300→    subgraph 在线查询阶段
 301→        Q[用户问题] --> QEmbed[Embedding 编码]
 302→        QEmbed --> Search[向量相似度检索]
 303→        DB --> Search
 304→        Search --> TopK[Top-K 候选文档]
 305→        TopK --> ReRank{重排序 Re-Ranker}
 306→        ReRank --> FinalDocs[精选文档]
 307→        FinalDocs --> LLM[LLM 生成]
 308→        Q --> LLM
 309→        LLM --> Ans(最终回答)
 310→    end
 311→```
 312→
 313→- **离线索引**：把文档切块（Chunk）、编码成向量、存入向量数据库。
 314→- **在线查询**：把问题编码成向量，检索 Top-K 近似文档，可选重排序，再拼进上下文让 LLM 生成。
 315→
 316→用 LangChain 搭一条最小 RAG 管道：
 317→
 318→```python
 319→from langchain_community.vectorstores import Chroma
 320→from langchain_openai import OpenAIEmbeddings
 321→from langchain_text_splitters import RecursiveCharacterTextSplitter
 322→
 323→text_splitter = RecursiveCharacterTextSplitter(
 324→    chunk_size=500,
 325→    chunk_overlap=50,
 326→    separators=["\n\n", "\n", "。", "！", "？", ".", " "]
 327→)
 328→
 329→chunks = text_splitter.split_text(your_document_text)
 330→
 331→vectorstore = Chroma.from_texts(
 332→    texts=chunks,
 333→    embedding=OpenAIEmbeddings()
 334→)
 335→
 336→results = vectorstore.similarity_search("如何配置 LoRA？", k=3)
 337→for doc in results:
 338→    print(doc.page_content)
 339→```
 340→
 341→**工程要点**：切片大小、重叠窗口、检索 Top-K、重排序是否必要，都直接影响回答质量，是需要反复实验的维度。
 342→
 343→---
 344→
 345→## §5 Function Calling 与 MCP
 346→
 347→LLM 只能"想"，不能"做"。Function Calling 给了它调用外部工具的能力：模型根据用户意图，输出一个结构化调用（工具名 + 参数），由你的代码真正执行。
 348→
 349→```python
 350→from openai import OpenAI
 351→
 352→client = OpenAI()
 353→
 354→messages = [
 355→    {"role": "user", "content": "今天北京的天气怎么样？"}
 356→]
 357→
 358→tools = [
 359→    {
 360→        "type": "function",
 361→        "function": {
 362→            "name": "get_weather",
 363→            "description": "获取指定城市的天气信息",
 364→            "parameters": {
 365→                "type": "object",
 366→                "properties": {
 367→                    "location": {
 368→                        "type": "string",
 369→                        "description": "城市名称，如'北京'、'上海'"
 370→                    }
 371→                },
 372→                "required": ["location"]
 373→            }
 374→        }
 375→    }
 376→]
 377→
 378→response = client.chat.completions.create(
 379→    model="gpt-4.1",
 380→    messages=messages,
 381→    tools=tools
 382→)
 383→
 384→tool_call = response.choices[0].message.tool_calls[0]
 385→print(tool_call.function.name)    # → "get_weather"
 386→print(tool_call.function.arguments)  # → '{"location": "北京"}'
 387→```
 388→
 389→**MCP（Model Context Protocol）** 在 Function Calling 之上解决一个更系统的问题：**工具如何被标准化地发现、连接和复用**。在 MCP 之前，每个框架有自己的一套工具格式，工具无法跨框架复用。MCP 把"模型 ↔ 工具/数据源"的连接抽成开放协议，让工具生态产生网络效应——一次开发，到处使用。
 390→
 391→**为什么需要开放标准**：工具生态需要网络效应。越多框架和工具支持 MCP，开发者越能避免为每个框架重写一遍工具适配层。
 392→
 393→---
 394→
 395→## §6 Agent：智能体架构
 396→
 397→Agent 把前面所有的能力拼成一个闭环：**LLM 提供大脑，工具提供手脚，记忆提供上下文，规划提供行动路线**。
 398→
 399→```text
 400→Agent = LLM（大脑）+ Planning（规划）+ Memory（记忆）+ Tools（工具）
 401→```
 402→
 403→最经典的执行范式是 **ReAct（Reasoning + Acting）**：思考 → 行动 → 观察 → 再思考，循环直到任务完成。
 404→
 405→```mermaid
 406→graph TD
 407→    Start((接收目标)) --> Think[思考 Thought<br/>LLM 分析当前状态]
 408→    Think --> Plan[规划 Plan<br/>分解为可执行步骤]
 409→    Plan --> Act[行动 Action<br/>调用工具执行]
 410→    Act --> Obs[观察 Observation<br/>获取执行结果]
 411→    Obs --> Check{任务完成?}
 412→    Check -- 是 --> End((结束))
 413→    Check -- 否 --> Think
 414→```
 415→
 416→一个具体例子能直观看到这个循环：
 417→
 418→```text
 419→┌─────────────────────────────────────────────────────────────┐
 420→│                    ReAct 执行示例                              │
 421→└─────────────────────────────────────────────────────────────┘
 422→
 423→用户：北京明天的天气适合户外运动吗？
 424→
 425→Thought 1：我需要先查北京明天的天气，再判断是否适合户外运动。
 426→Action 1：调用 get_weather(location="北京", date="明天")
 427→Observation 1：明天北京晴，气温 25°C，湿度 40%，风速 3 级
 428→
 429→Thought 2：天气晴朗、温度适宜、湿度低、风速小，非常适合户外运动。
 430→Action 2：无需更多工具调用
 431→Answer：明天北京天气晴朗，气温 25°C，湿度适中，非常适合户外运动！
 432→        推荐活动：跑步、骑行、徒步。
 433→```
 434→
 435→---
 436→
 437→## §7 Multi-Agent：多智能体系统
 438→
 439→单个 Agent 在复杂任务上常显得力不从心。Multi-Agent 的核心思路是**拆**：把一个大任务拆给多个各司其职的智能体。常见的协作模式有三种：
 440→
 441→```mermaid
 442→graph TD
 443→    subgraph 层级模式 Hierarchical
 444→        H_Main[主智能体] --> H_Sub1[子智能体 A]
 445→        H_Main --> H_Sub2[子智能体 B]
 446→    end
 447→
 448→    subgraph 协作模式 Collaborative
 449→        C_A[智能体 A] <--> C_B[智能体 B]
 450→        C_A --> C_Sum(汇总结果)
 451→        C_B --> C_Sum
 452→    end
 453→
 454→    subgraph 竞争模式 Competitive
 455→        Comp_A[智能体 A] --> Comp_Eval{选择最佳结果}
 456→        Comp_B[智能体 B] --> Comp_Eval
 457→        Comp_C[智能体 C] --> Comp_Eval
 458→    end
 459→```
 460→
 461→- **层级模式**：一个主 Agent 调度多个子 Agent，职责清晰，适合有明确分工的场景。
 462→- **协作模式**：平级 Agent 互通消息、汇总结果，适合需要观点碰撞的场景。
 463→- **竞争模式**：多个 Agent 各自产出，由评估者挑选最佳，适合"比质量"的场景。
 464→
 465→用 CrewAI 定义一个"研究员 + 写手"的协作团队：
 466→
 467→```python
 468→from crewai import Agent, Task, Crew
 469→
 470→researcher = Agent(
 471→    role="研究员",
 472→    goal="收集并分析最准确的信息",
 473→    backstory="你是一位专业的研究员，擅长从多个来源收集信息。"
 474→)
 475→
 476→writer = Agent(
 477→    role="技术写手",
 478→    goal="将复杂技术用易懂的语言解释清楚",
 479→    backstory="你是一位资深技术作家，擅长将复杂概念通俗化。"
 480→)
 481→
 482→research_task = Task(
 483→    description="研究 LLM 最新发展趋势",
 484→    agent=researcher
 485→)
 486→
 487→write_task = Task(
 488→    description="撰写一篇 LLM 科普文章",
 489→    agent=writer
 490→)
 491→
 492→crew = Crew(agents=[researcher, writer], tasks=[research_task, write_task])
 493→result = crew.kickoff()
 494→```
 495→
 496→**工程边界**：多 Agent 不等于更可靠。协调开销、上下文传递、错误传播都会放大。能用单 Agent 解决就先用单 Agent，拆智能体是"为了拆而拆"的反模式。
 497→
 498→---
 499→
 500→## §8 Workflow Engineering：工作流编排
 501→
 502→Agent 擅长"自主决策"，但很多任务其实是**确定性流程**——固定步骤、固定依赖，不需要模型每一次都重新规划。工作流工程就是把这类流程写成代码：定义步骤、状态、转换和异常处理。
 503→
 504→```python
 505→# 一个确定性工作流的抽象示意：
 506→# 输入 → 校验 → 检索 → 生成 → 校验输出 → 完成
 507→# 每一步失败都走明确的降级或重试路径
 508→```
 509→
 510→**Agent vs Workflow 怎么选**：路径固定、可预期 → 用 Workflow，稳定可控、成本低；路径开放、需要临场决策 → 用 Agent。两者可以组合——把 Agent 作为工作流中的一个"节点"。
 511→
 512→---
 513→
 514→## §9 Context Engineering：上下文工程
 515→
 516→上下文工程的本质是回答一个问题：**往窗口里放什么，才能让模型表现最好**。它在上下文窗口有限的前提下，系统性地管理"该放的信息、不该放的信息、以什么结构放"。
 517→
 518→一个实用做法是用结构化标签（如 XML）组织上下文，让模型能清晰区分"任务、背景、代码、约束"：
 519→
 520→```xml
 521→<task>
 522→  审查以下代码的安全问题
 523→</task>
 524→
 525→<context>
 526→  <project>Web API 服务</project>
 527→  <language>Python</language>
 528→  <framework>FastAPI</framework>
 529→</context>
 530→
 531→<code>
 532→  {待审查代码}
 533→</code>
 534→
 535→<constraints>
 536→  只关注 OWASP Top 10 安全风险
 537→</constraints>
 538→```
 539→
 540→**上下文窗口不够怎么办**：优先 1）增量摘要压缩历史；2）相关性检索只取相关片段；3）结构化标签减少冗余。仍不够时，可用 Multi-Agent 把上下文分散到不同智能体。
 541→
 542→---
 543→
 544→## §10 Agent Skill：智能体技能
 545→
 546→Skill 是把"特定功能封装成可复用单元"的标准格式。它让智能体具备"可被调用、可发现、可组合"的能力，核心是一份 `SKILL.md` 定义文件 + 配套的工具与知识目录。
 547→
 548→```text
 549→my_skill/
 550→├── SKILL.md        # 技能定义文件（必需）
 551→├── tools/          # 工具脚本目录
 552→│   ├── script1.py
 553→│   └── script2.sh
 554→├── knowledge/      # 知识文件目录
 555→│   └── guide.md
 556→└── config.yaml      # 配置文件
 557→```
 558→
 559→`SKILL.md` 用 frontmatter 声明技能元信息（名称、版本、描述、触发器），正文描述功能、使用方式和依赖：
 560→
 561→```markdown
 562→---
 563→name: code-reviewer
 564→version: 1.0.0
 565→description: 自动代码审查技能
 566→triggers:
 567→  - "审查代码"
 568→  - "code review"
 569→---
 570→
 571→# Code Reviewer Skill
 572→
 573→## 功能
 574→审查代码的安全性和性能问题。
 575→
 576→## 使用方式
 577→1. 提供待审查的代码文件
 578→2. 智能体自动调用审查工具
 579→3. 输出审查报告
 580→
 581→## 依赖
 582→- Python 3.10+
 583→- ruff, bandit
 584→```
 585→
 586→Skill 的价值在于**沉淀**：一次调试好的能力封装成 Skill 后，可以被多次、跨任务复用，避免反复从零写提示词和工具。
 587→
 588→---
 589→
 590→## §11 OpenClaw：开源智能体框架
 591→
 592→从 §6 到 §10，我们都在讨论"怎么设计一个智能体"。OpenClaw 则回答"怎么把智能体跑起来接到真实消息流里"——它是一个从**消息接入到智能体运行**的端到端框架。
 593→
 594→```text
 595→┌─────────────────────────────────────────────────────────────┐
 596→│                     OpenClaw 系统架构                         │
 597→└─────────────────────────────────────────────────────────────┘
 598→
 599→  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
 600→  │   消息平台   │     │   消息平台   │     │   消息平台   │
 601→  │ (Telegram)  │     │  (Discord)  │     │  (WhatsApp) │
 602→  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
 603→         │                   │                   │
 604→         └───────────────────┼───────────────────┘
 605→                             │
 606→                    ┌────────▼────────┐
 607→                    │    Gateway     │  ← 控制平面（WebSocket）
 608→                    │  (控制中枢)     │
 609→                    └────────┬────────┘
 610→                             │
 611→         ┌───────────────────┼───────────────────┐
 612→         │                   │                   │
 613→  ┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
 614→  │   智能体   │     │   Tools     │     │   Memory    │
 615→  │   (大脑)    │     │  (工具集)   │     │  (记忆)     │
 616→  └─────────────┘     └─────────────┘     └─────────────┘
 617→```
 618→
 619→核心是 **Gateway（控制中枢）**：它通过 WebSocket 连接各消息平台，把消息路由给智能体，智能体再调用工具、读写记忆。安装与启动很简单：
 620→
 621→```bash
 622→# 安装（官方推荐 Node.js 24，兼容 Node.js 22.14+）
 623→npm install -g openclaw@latest
 624→
 625→# 初始化配置
 626→openclaw onboard --install-daemon
 627→
 628→# 启动 Gateway
 629→openclaw gateway --port 18789 --verbose
 630→
 631→# 打开本地控制台
 632→openclaw dashboard
 633→```
 634→
 635→**LangChain vs OpenClaw**：LangChain 是开发库，给你构建智能体的抽象；OpenClaw 是完整框架，给你从消息接入到运行的端到端方案。快速落地接 Telegram/Discord 用 OpenClaw，深度定制逻辑用 LangChain。
 636→
 637→---
 638→
 639→## §12 Harness Engineering：评估工程
 640→
 641→越复杂的 Agent 系统越需要客观度量。Harness Engineering（评估工程）的核心主张是：**用评估驱动开发，而不是靠手感调参**。
 642→
 643→第一步是建立**评估集**——一组覆盖不同难度和场景、带期望行为的测试用例：
 644→
 645→```json
 646→[
 647→  {
 648→    "id": "eval_001",
 649→    "input": "帮我查一下北京明天的天气",
 650→    "expected_tool": "get_weather",
 651→    "expected_params": {"location": "北京"},
 652→    "difficulty": "easy"
 653→  },
 654→  {
 655→    "id": "eval_002",
 656→    "input": "帮我规划一个北京三日游，预算 5000 元",
 657→    "expected_tools": ["search_attractions", "search_hotels", "calculate_budget"],
 658→    "difficulty": "hard"
 659→  }
 660→]
 661→```
 662→
 663→然后进入"定义 → 运行 → 分析失败 → 修改配置"的循环，直到成功率达标：
 664→
 665→```text
 666→┌─────────────────────────────────────────────────────────────┐
 667→│                   评估驱动的开发循环                            │
 668→└─────────────────────────────────────────────────────────────┘
 669→
 670→  ┌──────────────┐
 671→  │ 1. 定义评估集  │ ← 包含多样化用例、边界案例、期望输出
 672→  └──────┬───────┘
 673→         │
 674→         ▼
 675→  ┌──────────────┐
 676→  │ 2. 运行评估   │ ← 执行所有用例，收集结果
 677→  └──────┬───────┘
 678→         │
 679→         ▼
 680→  ┌──────────────┐
 681→  │ 3. 分析失败   │ ← 定位失败用例，分析根因
 682→  └──────┬───────┘
 683→         │
 684→         ▼
 685→  ┌──────────────┐
 686→  │ 4. 修改配置   │ ← 调整提示词/智能体配置/工具定义
 687→  └──────┬───────┘
 688→         │
 689→         ▼
 690→    ┌─────────┐
 691→    │ 成功率？ │
 692→    └────┬────┘
 693→    ╱         ╲
 694→  达标       未达标
 695→   │           │
 696→   ▼           └──→ 返回步骤 2
 697→ 发布
 698→```
 699→
 700→这相当于把软件工程里的 CI/CD 思想引入 AI 应用：**每次改动都跑评估，用数据说话，而不是靠感觉**。
 701→
 702→---
 703→
 704→## 端到端实战：构建企业知识库问答智能体
 705→
 706→把前面所有技术串起来：一个企业知识库问答智能体，同时使用 RAG（查知识库）、Function Calling（查数据库、联网搜索）和 Agent 循环。
 707→
 708→架构如下：
 709→
 710→```text
 711→┌─────────────────────────────────────────────────────────────┐
 712→│              企业知识库问答智能体架构                            │
 713→└─────────────────────────────────────────────────────────────┘
 714→
 715→用户提问 ──→ 智能体（LLM）
 716→                │
 717→                ├──→ 工具 1：知识库检索（RAG）
 718→                │       └── 向量数据库 → 返回相关文档
 719→                │
 720→                ├──→ 工具 2：数据库查询（Function Calling）
 721→                │       └── SQL 数据库 → 返回结构化数据
 722→                │
 723→                └──→ 工具 3：网络搜索（Function Calling）
 724→                        └── 搜索 API → 返回最新信息
 725→```
 726→
 727→用 OpenAI Function Calling 实现一个最小可运行版本：
 728→
 729→```python
 730→import json
 731→from openai import OpenAI
 732→from langchain_community.vectorstores import Chroma
 733→from langchain_openai import OpenAIEmbeddings
 734→
 735→client = OpenAI()
 736→
 737→vectorstore = Chroma(
 738→    collection_name="company_docs",
 739→    embedding_function=OpenAIEmbeddings()
 740→)
 741→
 742→def execute_sql_safely(sql: str) -> str:
 743→    normalized_sql = sql.strip().lower()
 744→    if not normalized_sql.startswith("select"):
 745→        return "安全策略拒绝：只允许 SELECT 查询。"
 746→
 747→    # 真实项目中应在这里接入只读数据库连接，并加入参数化查询、超时和审计。
 748→    return "这里返回只读 SQL 查询结果。"
 749→
 750→tools = [
 751→    {
 752→        "type": "function",
 753→        "function": {
 754→            "name": "search_knowledge_base",
 755→            "description": "在企业知识库中检索相关文档",
 756→            "parameters": {
 757→                "type": "object",
 758→                "properties": {
 759→                    "query": {
 760→                        "type": "string",
 761→                        "description": "检索关键词"
 762→                    }
 763→                },
 764→                "required": ["query"]
 765→            }
 766→        }
 767→    },
 768→    {
 769→        "type": "function",
 770→        "function": {
 771→            "name": "query_database",
 772→            "description": "查询企业数据库获取结构化数据，如订单、客户信息等",
 773→            "parameters": {
 774→                "type": "object",
 775→                "properties": {
 776→                    "sql": {
 777→                        "type": "string",
 778→                        "description": "SQL 查询语句"
 779→                    }
 780→                },
 781→                "required": ["sql"]
 782→            }
 783→        }
 784→    }
 785→]
 786→
 787→def execute_tool(tool_name: str, arguments: dict) -> str:
 788→    if tool_name == "search_knowledge_base":
 789→        results = vectorstore.similarity_search(arguments["query"], k=3)
 790→        return "\n\n".join([doc.page_content for doc in results])
 791→    elif tool_name == "query_database":
 792→        return execute_sql_safely(arguments["sql"])
 793→    return "未知工具"
 794→
 795→def run_agent(user_message: str, max_iterations: int = 5) -> str:
 796→    messages = [{"role": "user", "content": user_message}]
 797→
 798→    for _ in range(max_iterations):
 799→        response = client.chat.completions.create(
 800→            model="gpt-4.1",
 801→            messages=messages,
 802→            tools=tools
 803→        )
 804→
 805→        msg = response.choices[0].message
 806→
 807→        if not msg.tool_calls:
 808→            return msg.content
 809→
 810→        messages.append(msg.model_dump(exclude_none=True))
 811→
 812→        for tool_call in msg.tool_calls:
 813→            result = execute_tool(
 814→                tool_call.function.name,
 815→                json.loads(tool_call.function.arguments)
 816→            )
 817→            messages.append({
 818→                "role": "tool",
 819→                "tool_call_id": tool_call.id,
 820→                "content": result
 821→            })
 822→
 823→    return "达到最大迭代次数，请尝试更具体的问题。"
 824→```
 825→
 826→对应地，为这个智能体准备一组端到端评估用例：
 827→
 828→```json
 829→[
 830→  {
 831→    "id": "e2e_001",
 832→    "input": "公司的年假政策是什么？",
 833→    "expected_tool": "search_knowledge_base",
 834→    "difficulty": "easy"
 835→  },
 836→  {
 837→    "id": "e2e_002",
 838→    "input": "上个月销售额最高的产品是什么？",
 839→    "expected_tool": "query_database",
 840→    "difficulty": "medium"
 841→  },
 842→  {
 843→    "id": "e2e_003",
 844→    "input": "对比我们产品和竞品的市场表现，给出分析报告",
 845→    "expected_tools": ["search_knowledge_base", "query_database"],
 846→    "difficulty": "hard"
 847→  }
 848→]
 849→```
 850→
 851→---
 852→
 853→## 学习路线总结
 854→
 855→把全篇串成一句话：**先让模型"会说话"（LLM 与提示词），再让它"有知识"（RAG 或微调），接着让它"能动手"（Function Calling / MCP），再让它"会规划"（Agent），人多力量大就拆智能体（Multi-Agent），复杂任务用流程固化（Workflow），最后用评估兜底（Harness Engineering）**。
 856→
 857→建议的产品落地顺序：最小可用 → 提示词工程 → 需要时加 RAG → 需要时加工具 → 封装成 Agent → 用评估集固化质量。每一步都先做小、做对，再谈扩展。
 858→
 859→⬆️ [返回目录](#目录)
1388→
1389→---
1390→
1391→---
1392→---
1393→
1394→## 常见问题 FAQ
1395→
1396→### Q1：我应该从哪个技术开始学？
1397→
1398→如果你完全没有 AI 开发经验，从 **Prompt Engineering** 开始。它不需要复杂基础设施，只要能调用一个 LLM API 就能练习，而且能很快反馈出任务边界。掌握提示词技巧后，再按顺序学习 RAG → Function Calling → Agent。
1399→
1400→### Q2：微调和 RAG 到底该选哪个？
1401→
1402→一个实用判断是：如果问题是“模型不知道某个知识”（如公司内部文档、最新新闻），优先选 RAG；如果问题是“模型的行为方式不对”（如输出格式、对话风格），再考虑微调。两者也可以组合使用。
1403→
1404→### Q3：学智能体开发需要什么基础？
1405→
1406→你需要：1）熟练使用至少一门编程语言（Python 推荐）；2）理解 API 调用和异步编程；3）基本的 LLM 使用经验（至少用过 ChatGPT 或 Claude 的 API）。Function Calling 是智能体开发的前置知识，务必先掌握。
1407→
1408→### Q4：OpenClaw 和 LangChain 有什么区别？
1409→
1410→LangChain 是一个**开发库**，提供构建智能体的工具和抽象；OpenClaw 是一个**完整框架**，提供从消息接入到智能体运行的端到端解决方案。如果你要快速搭建一个能接入 Telegram/Discord 的智能体，OpenClaw 更方便；如果你要深度定制智能体逻辑，LangChain 更灵活。
1411→
1412→### Q5：如何评估我的 AI 应用是否足够好？
1413→
1414→建立评估集（Evaluation Set），包含 20 到 50 个覆盖不同场景的测试用例。每个用例定义输入、期望行为和评分规则，运行后统计成功率。成功率低于 80% 的场景需要重点优化。参考 §12 Harness Engineering 了解详细方法。
1415→
1416→### Q6：上下文窗口不够用怎么办？
1417→
1418→优先尝试：1）增量摘要——对历史对话进行压缩；2）相关性检索——只检索与当前问题相关的上下文；3）结构化模板——用 XML/JSON 减少冗余描述。如果仍然不够，考虑 Multi-Agent 架构将上下文分散到不同智能体。
1419→
1420→---
1421→
1422→## 推荐学习资源
1423→
1424→### 官方文档与论文
1425→
1426→| 资源 | 类型 | 链接 |
1427→| ---- | ---- | ---- |
1428→| Attention Is All You Need | 论文 | [arXiv](https://arxiv.org/abs/1706.03762) |
1429→| OpenClaw 文档 | 框架文档 | [docs.openclaw.ai](https://docs.openclaw.ai/) |
1430→| Anthropic Cookbook | 示例代码 | [GitHub](https://github.com/anthropics/anthropic-cookbook) |
1431→| PEFT 库文档 | 微调工具 | [GitHub](https://github.com/huggingface/peft) |
1432→| LangChain 文档 | 框架文档 | [python.langchain.com](https://python.langchain.com/) |
1433→| MCP 规范 | 协议文档 | [modelcontextprotocol.io](https://modelcontextprotocol.io/specification/) |
1434→
1435→### 在线学习平台
1436→
1437→| 平台 | 课程 | 特点 |
1438→| ---- | ---- | ---- |
1439→| Fast.ai | Practical Deep Learning | 实践导向 |
1440→| Coursera | Deep Learning Specialization | 系统全面 |
1441→| Hugging Face | Transformers 课程 | 专注于 LLM |
1442→| DeepLearning.AI | ChatGPT Prompt Engineering | 提示词专项 |
1443→
1444→### 开源项目推荐
1445→
1446→| 项目 | 用途 | 链接 |
1447→| ---- | ---- | ---- |
1448→| LlamaIndex | RAG 开发 | [GitHub](https://github.com/run-llama/llama_index) |
1449→| LangGraph | 工作流与 Agent 编排 | [GitHub](https://github.com/langchain-ai/langgraph) |
1450→| Dify | 零代码/低代码 AI 平台 | [GitHub](https://github.com/langgenius/dify) |
1451→| CrewAI | Multi-Agent 开发 | [GitHub](https://github.com/crewAIInc/crewAI) |
1452→| RAGAS | RAG 评估 | [GitHub](https://github.com/explodinggradients/ragas) |
1453→
1454→---
1455→
1456→## 练习
1457→
1458→下面三个练习用来检验你对 AI 应用技术栈的理解，建议动手实现后再对照行为：
1459→
1460→1. **搭建本地 LLM 环境并跑通一个 Q&A 任务**：用 Ollama 安装 Llama 3（8B），用 Python 写一个调用本地 LLM 的简单 Q&A 脚本。要求：能接收用户输入，发给本地 LLM，打印回答。完成后试试：如果用户输入的问题需要外部知识（例如"今天天气怎么样"），你的脚本能否处理？
1461→
1462→2. **用 LlamaIndex 搭建一个简单 RAG 管道**：选一个你熟悉的文档集（例如公司技术文档、个人笔记），用 LlamaIndex 搭建一个 RAG 管道。要求：能接收用户问题，从文档集检索相关片段，拼成上下文发给 LLM，返回回答。观察：检索返回的片段是否真的相关？需不需要调整 chunk 大小和 overlap？
1463→
1464→3. **用 LangGraph 实现一个简单 Agent**：用 LangGraph 写一个只调用一个工具（例如 `get_weather(city: str)`）的 ReAct 循环。要求：处理 `Observation → Reasoning → Action` 三步，设置终止条件（循环次数上限或任务完成标记）。完成后对比：和直接用 OpenAI API function calling 实现同样功能，哪边代码更清晰？
1465→
1466→---
1467→
1468→## 自测题
1469→
1470→下面 5 道题用来检验你对全文核心概念的掌握程度。点击参考答案前的三角展开查看解析。
1471→
1472→1. AI 应用技术栈的三层核心组成是什么？为什么需要分这三层？
1473→
1474→<details>
1475→<summary>参考答案</summary>
1476→
1477→三层是：**模型层**（LLM，负责推理）、**应用层**（Prompt Engineering / RAG / Agent / Fine-tuning，负责任务设计）、**基础设施层**（GPU、向量数据库、部署平台，负责运行和扩展）。分三层是因为：模型层的能力通用但不可控，应用层负责把通用能力适配到具体任务，基础设施层负责把应用层的能力规模化。三层可以独立演进——例如换模型不影响应用层代码，换部署平台不影响模型和能力选型。
1478→
1479→（对应章节：§1 LLM 基础 + §6 Agent 架构 + 学习路线总览）
1480→
1481→</details>
1482→
1483→2. RAG（检索增强生成）解决的本质问题是什么？它的两个核心步骤是什么？
1484→
1485→<details>
1486→<summary>参考答案</summary>
1487→
1488→RAG 解决的本质问题是：**LLM 的知识有截止日期，且无法访问私有数据**。如果不做 RAG，LLM 只能基于训练数据回答，无法回答"我们公司去年 Q3 的营收是多少"这类问题。
1489→
1490→两个核心步骤：
1491→1. **检索（Retrieve）**：根据用户问题，从外部知识库（向量数据库）检索相关片段
1492→2. **增强生成（Augment & Generate）**：把检索到的片段拼成上下文，发给 LLM，生成回答
1493→
1494→（对应章节：§4 RAG：检索增强生成）
1495→
1496→</details>
1497→
1498→3. Prompt Engineering 和 Fine-tuning 的区别是什么？什么场景用哪个？
1499→
1500→<details>
1501→<summary>参考答案</summary>
1502→
1503→- **Prompt Engineering**：不改模型参数，只优化输入提示词。成本低、速度快、适合快速迭代。但受上下文窗口限制，且无法让模型"记住"专业知识。
1504→- **Fine-tuning**：在特定数据集上继续训练预训练模型，使其适应特定任务。成本高、需要数据集、效果持久。适合需要模型"记住"专业知识的场景（例如法律、医疗）。
1505→
1506→选择依据：先试 Prompt Engineering，如果效果不够再考虑 Fine-tuning。LoRA 等参数高效微调方法可以降低成本，值得优先尝试。
1507→
1508→（对应章节：§2 Prompt Engineering + §3 Fine-tuning）
1509→
1510→</details>
1511→
1512→4. MCP（模型上下文协议）解决的本质问题是什么？为什么它需要成为开放标准？
1513→
1514→<details>
1515→<summary>参考答案</summary>
1516→
1517→MCP 解决的本质问题是：**LLM 如何以标准化方式发现、连接和调用外部工具与数据源**。在 MCP 之前，每个框架（LangChain、CrewAI、AutoGen）有自己的工具格式，工具无法跨框架复用。
1518→
1519→它需要成为开放标准，因为：工具生态需要网络效应——越多框架和工具支持 MCP，开发者越能一次开发、到处使用。如果 MCP 只是某个框架的私有协议，网络效应起不来，工具复用和生态协作都受限制。
1520→
1521→（对应章节：§5 Function Calling 与 MCP）
1522→
1523→</details>
1524→
1525→5. 从课程学习到生产部署，需要补哪些工程能力？
1526→
1527→<details>
1528→<summary>参考答案</summary>
1529→
1530→课程通常覆盖：概念理解、示例跑通、基础代码实现。但生产部署还需要补：
1531→1. **日志和可观测性**：能把每次 LLM 调用、工具调用、错误记录下来
1532→2. **监控和告警**：能监控 Token 消耗、延迟、错误率，并在异常时告警
1533→3. **容错和重试**：能处理 LLM 调用失败、工具调用超时、网络错误
1534→4. **成本控制和预算**：能给每个用户、每个任务设定 Token 预算，避免失控
1535→5. **安全和权限控制**：能控制 Agent 能访问哪些工具、能操作哪些数据
1536→
1537→（对应章节：§8 Workflow Engineering + §12 Harness Engineering）
1538→
1539→</details>
1540→
1541→---
1542→
1543→## 进阶路径指引
1544→
1545→掌握基础路线后，可选择以下三大进阶方向：
1546→
1547→### 路径 A：AI 基础设施方向
1548→
1549→深入理解模型训练和部署的工程实践：
1550→
1551→1. **模型量化与推理优化**：学习 GPTQ、AWQ、vLLM 等推理加速技术
1552→2. **分布式训练**：学习 DeepSpeed、FSDP 等大规模训练框架
1553→3. **模型服务化**：学习 Triton Inference Server、BentoML 等部署方案
1554→
1555→### 路径 B：AI 应用产品方向
1556→
1557→深入理解 AI 产品的设计和用户体验：
1558→
1559→1. **AI 产品设计**：学习人机交互设计、AI UX 实践建议
1560→2. **多模态应用**：学习视觉、语音等多模态 AI 应用开发
1561→3. **AI 安全与对齐**：学习 RLHF、Constitutional AI 等对齐技术
1562→
1563→### 路径 C：AI 智能体深度方向
1564→
1565→深入理解智能体系统的高级架构：
1566→
1567→1. **智能体评估与优化**：深入学习 Harness Engineering，建立 CI/CD for AI 流程
1568→2. **复杂 Multi-Agent 系统**：学习 LangGraph 等图编排框架
1569→3. **自主智能体**：探索 AutoGPT、BabyAGI 等自主智能体架构
1570→
1571→---
1572→
1573→## 核心术语表
1574→
1575→| 术语 | 英文 | 释义 |
1576→| ---- | ---- | ---- |
1577→| 大语言模型 | Large Language Model (LLM) | 参数规模达数十亿以上的语言模型，能理解和生成自然语言 |
1578→| 提示词工程 | Prompt Engineering | 通过优化输入提示词来引导 LLM 产生期望输出的技术 |
1579→| 微调 | Fine-tuning | 在特定数据集上继续训练预训练模型，使其适应特定任务 |
1580→| 低秩适配 | LoRA (Low-Rank Adaptation) | 只训练少量低秩参数的参数高效微调方法 |
1581→| 检索增强生成 | RAG (Retrieval-Augmented Generation) | 结合外部知识库检索来增强 LLM 回答质量的方法 |
1582→| 函数调用 | Function Calling | LLM 根据上下文决定调用外部工具或 API 的机制 |
1583→| 模型上下文协议 | MCP (Model Context Protocol) | Anthropic 提出的 Agent 与工具连接的开放标准 |
1584→| 智能体 | Agent | 能自主感知、决策和执行动作的 AI 系统 |
1585→| 多智能体 | Multi-Agent | 多个专业智能体协作完成复杂任务的系统 |
1586→| 上下文工程 | Context Engineering | 系统性管理 LLM 上下文信息的工程实践 |
1587→| 智能体技能 | Agent Skill | 将特定功能封装为可复用单元的标准格式 |
1588→| 评估工程 | Harness Engineering | 通过系统化评估驱动 AI 系统开发的工程实践 |
1589→| 思维链 | Chain-of-Thought (CoT) | 引导模型展示推理过程的提示词技巧 |
1590→| 少样本学习 | Few-Shot Learning | 通过少量示例引导模型学习特定输出模式 |
1591→| 向量数据库 | Vector Database | 专门存储和检索向量嵌入的数据库 |
1592→| 词元 | Token | LLM 处理文本的基本单位 |
1593→| 上下文窗口 | Context Window | LLM 一次能处理的最大 Token 数量 |
1594→| 幻觉 | Hallucination | LLM 生成看似合理但实际错误的内容 |
1595→| 自注意力 | Self-Attention | Transformer 中计算序列内部元素相关性的机制 |
1596→| 重排序 | Re-Ranker | 对初步检索结果进行精细相关性排序的模型 |
1597→
1598→⬆️ [返回目录](#目录)
1599→
1600→---
1601→
1602→## 资料口径说明
1603→
1604→本文基于多个 AI 应用技术课程和开源项目撰写。需要说明的边界：
1605→
1606→1. **课程和资源版本时效性**：本文提到的课程（微软 AI Agents for Beginners、LangChain for Beginners、DeepLearning.AI 等）和开源项目（LlamaIndex、LangGraph、Dify、CrewAI）都在快速迭代，章节结构、代码示例、API 接口可能随版本变化，请以各项目 GitHub 仓库的最新 commit 为准。
1607→2. **代码示例的语言和框架依赖**：本文提到的代码示例主要基于 Python 生态（LlamaIndex、LangGraph、CrewAI 均为 Python 框架），如果团队用其它语言（TypeScript/Java/C#），需要自己翻译示例。
1608→3. **MCP 协议生态成熟度**：文中讲到的 MCP 协议在 2024 年 11 月才推出，生态仍在早期。工具数量、稳定性、兼容性都在快速变化，本文提到的 MCP 工具示例以 2026 年 4 月的状态为准。
1609→4. **基准数据和性能对比**：文中可能提到的性能数据（例如 Token 消耗、延迟、并发能力）来自特定测试环境，实际表现会因任务特征、模型选择、硬件条件而变化。
1610→5. **生产部署能力缺口**：学习路径覆盖了从概念到生产的关键知识点，但生产部署还需要自己补日志、监控、容错、成本控制等工程能力。
1611→6. **多语言支持**：部分资源（例如 DeepLearning.AI 课程、Hugging Face 课程）以英文为主，中文翻译可能不完整或滞后。请以各项目官方文档的语言版本为准。
1612→
1613→---
1614→
1615→---
1616→
1617→**文档元信息**：
1618→
1619→- 难度等级：⭐⭐⭐
1620→- 类型：技术笔记
1621→- 更新日期：2026-04-26
1622→- 预计阅读时间：90 分钟