---
title: "近年 AI 应用技术学习路线：从 LLM、RAG 到 Agent 工程"
date: "2026-04-14T10:30:00+08:00"
slug: "ai-application-technology-learning-path-guide"
summary: "一篇面向工程师的 AI 应用技术路线图：先把 LLM、Prompt、RAG、Function Calling 与 MCP 打稳，再进入 Agent、Workflow、Context、Skill 与评估工程。"
description: "系统梳理 LLM、Prompt Engineering、Fine-tuning、RAG、MCP、Agent、Multi-Agent、Workflow Engineering、Context Engineering、Agent Skill、OpenClaw、Harness Engineering 等核心主题，给出从入门到进阶的学习顺序、工程边界、练习题与实战示例。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "LLM", "Agent", "Prompt Engineering", "MCP", "RAG", "AI应用"]
---

> **目标读者**：希望系统掌握 AI 应用技术的开发者与工程师
> **前置知识**：掌握至少一门编程语言，了解基本的数据结构和算法
> **预计完成时间**：3 到 6 个月，取决于每周投入时间和已有工程基础

<!-- truncate -->

---

## 目录

- [前言](#前言)
- [学习路线总览](#学习路线总览)
- [§1 LLM：大语言模型基础](#1-llm 大语言模型基础-)
- [§2 Prompt Engineering：提示词工程](#2-prompt-engineering 提示词工程-)
- [§3 Fine-tuning：微调技术](#3-fine-tuning 微调技术-)
- [§4 RAG：检索增强生成](#4-rag 检索增强生成-)
- [§5 Function Calling 与 MCP](#5-function-calling-与-mcp-)
- [§6 Agent：智能体架构](#6-agent 智能体架构-)
- [§7 Multi-Agent：多智能体系统](#7-multi-agent 多智能体系统-)
- [§8 Workflow Engineering：工作流编排](#8-workflow-engineering 工作流编排-)
- [§9 Context Engineering：上下文工程](#9-context-engineering 上下文工程-)
- [§10 Agent Skill：智能体技能](#10-agent-skill 智能体技能-)
- [§11 OpenClaw：开源智能体框架](#11-openclaw 开源智能体框架-)
- [§12 Harness Engineering：评估工程](#12-harness-engineering 评估工程-)
- [端到端实战：构建企业知识库问答智能体](#端到端实战构建企业知识库问答智能体)
- [学习路线总结](#学习路线总结)
- [常见问题 FAQ](#常见问题-faq)
- [推荐学习资源](#推荐学习资源)
- [进阶路径指引](#进阶路径指引)
- [核心术语表](#核心术语表)

---

## 前言

过去几年，AI 应用开发从“会调用一个聊天接口”迅速演化成一套完整工程体系：模型选择、提示词、检索、工具调用、上下文管理、工作流、智能体、评估集，任何一环薄弱，最终产品都会在稳定性、成本或可维护性上出问题。

这篇文章把近年最常见的 AI 应用技术主题串成一条学习路线。它适合两类读者：一类是想从零建立系统认知的开发者，另一类是已经做过 Prompt、RAG 或 Agent 项目，但希望补齐工程全貌的人。

读完后，至少应该能做到下面几件事：

- 建立 AI 应用技术的系统认知框架
- 理解每个技术的核心原理与适用边界
- 掌握从理论到实践的完整学习顺序
- 可直接复用的代码示例与配置方案
- 每个主题的练习题与自测检查清单

**本文定位**：这是一篇技术路线图，不是单点深度教程。每个主题都会交代核心概念、为什么需要它、适用边界和最小实践；真正进入生产系统时，还需要结合具体模型、数据、权限、安全和成本约束继续细化。

---

## 学习路线总览

这条路线可以拆成三种阅读深度。初学者先拿到概念地图，有经验的开发者重点看实现取舍，架构师和团队负责人则更应该关注边界、评估和治理。

| 路径 | 目标人群 | 核心问题 | 难度范围 |
| ---- | ---- | ---- | ---- |
| 入门路径 | AI 初学者 | 这个技术是什么？ | ⭐ 到 ⭐⭐ |
| 进阶路径 | 有经验的开发者 | 这个怎么实现？ | ⭐⭐ 到 ⭐⭐⭐ |
| 专家路径 | 架构师与团队负责人 | 为什么这样设计？ | ⭐⭐⭐ 到 ⭐⭐⭐⭐ |

**建议的学习顺序**：LLM 基础 → Prompt Engineering → RAG → Function Calling / MCP → Agent → Workflow / Context → Multi-Agent → Skill / Evaluation

**依赖关系图**：

```text
LLM 基础 ──────→ Prompt Engineering ──────→ Fine-tuning
    │                    │                      │
    │                    ▼                      ▼
    │              Function Calling          RAG
    │                    │                      │
    │                    ▼                      │
    │                   MCP ────────────────────┤
    │                    │                      │
    ▼                    ▼                      ▼
  智能体 ←──────────── Context Engineering
    │
    ▼
  Multi-Agent ──→ Workflow Engineering ──→ Agent Skill
    │
    ▼
  OpenClaw ──→ Harness Engineering
```textmermaid
graph TD
    A[Transformer 原始架构] --> B[Encoder-Only<br/>如 BERT]
    A --> C[Encoder-Decoder<br/>如 T5]
    A --> D[Decoder-Only<br/>当前主流: GPT、Llama]
    style D stroke:#f66,stroke-width:2px
```texttext
输入序列：["我", "喜欢", "AI", "技术"]

自注意力计算（简化）：
每个 Token 都会"关注"所有其他 Token，计算相关性权重：

"我"   → 关注 [我:0.3, 喜欢:0.5, AI:0.1, 技术:0.1]  → 主要是"喜欢"的施事者
"喜欢" → 关注 [我:0.4, 喜欢:0.1, AI:0.3, 技术:0.2]  → "我"喜欢"AI"和"技术"
"AI"   → 关注 [我:0.1, 喜欢:0.3, AI:0.2, 技术:0.4]  → "AI"是一种"技术"
"技术" → 关注 [我:0.1, 喜欢:0.2, AI:0.4, 技术:0.3]  → 与"AI"强关联

→ 每个 Token 的表示 = 所有 Token 的加权求和
→ 权重越大，表示该 Token 对当前 Token 越重要
```textmarkdown
# 示例：翻译任务

# 示例 1
用户：把"早上好"翻译成英文
AI：Good morning

# 示例 2
用户：把"晚安"翻译成英文
AI：Good night

# 正式请求
用户：把"你好"翻译成英文
AI：
```textmarkdown
# 示例：数学问题

用户：计算 245 + 178，请展示计算过程。
AI：让我一步步思考：

第 1 步：245 + 100 = 345
第 2 步：345 + 70 = 415
第 3 步：415 + 8 = 423

答案是 423
```textmarkdown
# 角色
你是一位资深的前端工程师，擅长 React 和 TypeScript。

# 任务
审查以下代码，找出潜在的性能问题。

# 约束
- 只关注性能问题，不关注代码风格
- 每个问题给出具体的修改建议
- 按严重程度排序（高 → 中 → 低）

# 输出格式
| 问题 | 严重程度 | 位置 | 修改建议 |
| ---- | ---- | ---- | ---- |

# 代码
{待审查的代码}
```texttext
原始更新：ΔW (100×100 = 10,000 参数)
LoRA 分解：A (100×2 = 200 参数) × B (2×100 = 200 参数)
实际训练：400 参数 = 10,000 参数的 4%
```textmermaid
graph LR
    subgraph 原始权重 W (d×d)
        W0[冻结的 W₀]
    end
    
    subgraph LoRA 旁路分支
        A[A 矩阵 r×d<br/>可训练] --> B[B 矩阵 d×r<br/>可训练]
    end
    
    Input(输入 x) --> W0
    Input --> A
    B --> Add((+))
    W0 --> Add
    Add --> Output(输出 y)
```textpython
import torch
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Meta-Llama-3-8B",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# 输出示例：trainable params: 6,815,744 || all params: 8,075,097,856 || trainable%: 0.084%
```texttext
┌─────────────────────────────────────────────────────────────┐
│                      RAG 工作流程                              │
└─────────────────────────────────────────────────────────────┘

用户问题 ──→ 编码为向量 ──→ 在向量数据库中检索 ──→ 获取相关文档
                                            │
                                            ▼
                        ┌───────────────────────────────┐
                        │         LLM 生成答案            │
                        │  (基于检索结果 + 自身知识)        │
                        └───────────────────────────────┘
                                            │
                                            ▼
                                        最终回答
```textmermaid
graph TD
    subgraph 离线索引阶段
        Doc[原始文档] --> Split[文本分割]
        Split --> Embed[Embedding 编码]
        Embed --> DB[(向量数据库)]
    end

    subgraph 在线查询阶段
        Q[用户问题] --> QEmbed[Embedding 编码]
        QEmbed --> Search[向量相似度检索]
        DB --> Search
        Search --> TopK[Top-K 候选文档]
        TopK --> ReRank{重排序 Re-Ranker}
        ReRank --> FinalDocs[精选文档]
        FinalDocs --> LLM[LLM 生成]
        Q --> LLM
        LLM --> Ans(最终回答)
    end
```textpython
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", "。", "！", "？", ".", " "]
)

chunks = text_splitter.split_text(your_document_text)

vectorstore = Chroma.from_texts(
    texts=chunks,
    embedding=OpenAIEmbeddings()
)

results = vectorstore.similarity_search("如何配置 LoRA？", k=3)
for doc in results:
    print(doc.page_content)
```textpython
from openai import OpenAI

client = OpenAI()

messages = [
    {"role": "user", "content": "今天北京的天气怎么样？"}
]

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4.1",
    messages=messages,
    tools=tools
)

tool_call = response.choices[0].message.tool_calls[0]
print(tool_call.function.name)    # → "get_weather"
print(tool_call.function.arguments)  # → '{"location": "北京"}'
```texttext
Agent = LLM（大脑）+ Planning（规划）+ Memory（记忆）+ Tools（工具）
```textmermaid
graph TD
    Start((接收目标)) --> Think[思考 Thought<br/>LLM 分析当前状态]
    Think --> Plan[规划 Plan<br/>分解为可执行步骤]
    Plan --> Act[行动 Action<br/>调用工具执行]
    Act --> Obs[观察 Observation<br/>获取执行结果]
    Obs --> Check{任务完成?}
    Check -- 是 --> End((结束))
    Check -- 否 --> Think
```texttext
┌─────────────────────────────────────────────────────────────┐
│                    ReAct 执行示例                              │
└─────────────────────────────────────────────────────────────┘

用户：北京明天的天气适合户外运动吗？

Thought 1：我需要先查北京明天的天气，再判断是否适合户外运动。
Action 1：调用 get_weather(location="北京", date="明天")
Observation 1：明天北京晴，气温 25°C，湿度 40%，风速 3 级

Thought 2：天气晴朗、温度适宜、湿度低、风速小，非常适合户外运动。
Action 2：无需更多工具调用
Answer：明天北京天气晴朗，气温 25°C，湿度适中，非常适合户外运动！
        推荐活动：跑步、骑行、徒步。
```textmermaid
graph TD
    subgraph 层级模式 Hierarchical
        H_Main[主智能体] --> H_Sub1[子智能体 A]
        H_Main --> H_Sub2[子智能体 B]
    end

    subgraph 协作模式 Collaborative
        C_A[智能体 A] <--> C_B[智能体 B]
        C_A --> C_Sum(汇总结果)
        C_B --> C_Sum
    end

    subgraph 竞争模式 Competitive
        Comp_A[智能体 A] --> Comp_Eval{选择最佳结果}
        Comp_B[智能体 B] --> Comp_Eval
        Comp_C[智能体 C] --> Comp_Eval
    end
```textpython
from crewai import Agent, Task, Crew

researcher = Agent(
    role="研究员",
    goal="收集并分析最准确的信息",
    backstory="你是一位专业的研究员，擅长从多个来源收集信息。"
)

writer = Agent(
    role="技术写手",
    goal="将复杂技术用易懂的语言解释清楚",
    backstory="你是一位资深技术作家，擅长将复杂概念通俗化。"
)

research_task = Task(
    description="研究 LLM 最新发展趋势",
    agent=researcher
)

write_task = Task(
    description="撰写一篇 LLM 科普文章",
    agent=writer
)

crew = Crew(agents=[researcher, writer], tasks=[research_task, write_task])
result = crew.kickoff()
```textxml
<task>
  审查以下代码的安全问题
</task>

<context>
  <project>Web API 服务</project>
  <language>Python</language>
  <framework>FastAPI</framework>
</context>

<code>
  {待审查代码}
</code>

<constraints>
  只关注 OWASP Top 10 安全风险
</constraints>
```texttext
my_skill/
├── SKILL.md        # 技能定义文件（必需）
├── tools/          # 工具脚本目录
│   ├── script1.py
│   └── script2.sh
├── knowledge/      # 知识文件目录
│   └── guide.md
└── config.yaml      # 配置文件
```textmarkdown
---
name: code-reviewer
version: 1.0.0
description: 自动代码审查技能
triggers:
  - "审查代码"
  - "code review"
---

# Code Reviewer Skill

## 功能
审查代码的安全性和性能问题。

## 使用方式
1. 提供待审查的代码文件
2. 智能体自动调用审查工具
3. 输出审查报告

## 依赖
- Python 3.10+
- ruff, bandit
```texttext
┌─────────────────────────────────────────────────────────────┐
│                     OpenClaw 系统架构                         │
└─────────────────────────────────────────────────────────────┘

  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │   消息平台   │     │   消息平台   │     │   消息平台   │
  │ (Telegram)  │     │  (Discord)  │     │  (WhatsApp) │
  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │    Gateway     │  ← 控制平面（WebSocket）
                    │  (控制中枢)     │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
  ┌──────▼──────┐     ┌──────▼──────┐     ┌──────▼──────┐
  │   智能体   │     │   Tools     │     │   Memory    │
  │   (大脑)    │     │  (工具集)   │     │  (记忆)     │
  └─────────────┘     └─────────────┘     └─────────────┘
```textbash
# 安装（官方推荐 Node.js 24，兼容 Node.js 22.14+）
npm install -g openclaw@latest

# 初始化配置
openclaw onboard --install-daemon

# 启动 Gateway
openclaw gateway --port 18789 --verbose

# 打开本地控制台
openclaw dashboard
```textjson
[
  {
    "id": "eval_001",
    "input": "帮我查一下北京明天的天气",
    "expected_tool": "get_weather",
    "expected_params": {"location": "北京"},
    "difficulty": "easy"
  },
  {
    "id": "eval_002",
    "input": "帮我规划一个北京三日游，预算 5000 元",
    "expected_tools": ["search_attractions", "search_hotels", "calculate_budget"],
    "difficulty": "hard"
  }
]
```texttext
┌─────────────────────────────────────────────────────────────┐
│                   评估驱动的开发循环                            │
└─────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │ 1. 定义评估集  │ ← 包含多样化用例、边界案例、期望输出
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 2. 运行评估   │ ← 执行所有用例，收集结果
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 3. 分析失败   │ ← 定位失败用例，分析根因
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ 4. 修改配置   │ ← 调整提示词/智能体配置/工具定义
  └──────┬───────┘
         │
         ▼
    ┌─────────┐
    │ 成功率？ │
    └────┬────┘
    ╱         ╲
  达标       未达标
   │           │
   ▼           └──→ 返回步骤 2
 发布
```texttext
┌─────────────────────────────────────────────────────────────┐
│              企业知识库问答智能体架构                            │
└─────────────────────────────────────────────────────────────┘

用户提问 ──→ 智能体（LLM）
                │
                ├──→ 工具 1：知识库检索（RAG）
                │       └── 向量数据库 → 返回相关文档
                │
                ├──→ 工具 2：数据库查询（Function Calling）
                │       └── SQL 数据库 → 返回结构化数据
                │
                └──→ 工具 3：网络搜索（Function Calling）
                        └── 搜索 API → 返回最新信息
```textpython
import json
from openai import OpenAI
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

client = OpenAI()

vectorstore = Chroma(
    collection_name="company_docs",
    embedding_function=OpenAIEmbeddings()
)

def execute_sql_safely(sql: str) -> str:
    normalized_sql = sql.strip().lower()
    if not normalized_sql.startswith("select"):
        return "安全策略拒绝：只允许 SELECT 查询。"

    # 真实项目中应在这里接入只读数据库连接，并加入参数化查询、超时和审计。
    return "这里返回只读 SQL 查询结果。"

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "在企业知识库中检索相关文档",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "检索关键词"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": "查询企业数据库获取结构化数据，如订单、客户信息等",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL 查询语句"
                    }
                },
                "required": ["sql"]
            }
        }
    }
]

def execute_tool(tool_name: str, arguments: dict) -> str:
    if tool_name == "search_knowledge_base":
        results = vectorstore.similarity_search(arguments["query"], k=3)
        return "\n\n".join([doc.page_content for doc in results])
    elif tool_name == "query_database":
        return execute_sql_safely(arguments["sql"])
    return "未知工具"

def run_agent(user_message: str, max_iterations: int = 5) -> str:
    messages = [{"role": "user", "content": user_message}]

    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            tools=tools
        )

        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content

        messages.append(msg.model_dump(exclude_none=True))

        for tool_call in msg.tool_calls:
            result = execute_tool(
                tool_call.function.name,
                json.loads(tool_call.function.arguments)
            )
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

    return "达到最大迭代次数，请尝试更具体的问题。"
```textjson
[
  {
    "id": "e2e_001",
    "input": "公司的年假政策是什么？",
    "expected_tool": "search_knowledge_base",
    "difficulty": "easy"
  },
  {
    "id": "e2e_002",
    "input": "上个月销售额最高的产品是什么？",
    "expected_tool": "query_database",
    "difficulty": "medium"
  },
  {
    "id": "e2e_003",
    "input": "对比我们产品和竞品的市场表现，给出分析报告",
    "expected_tools": ["search_knowledge_base", "query_database"],
    "difficulty": "hard"
  }
]
```

⬆️ [返回目录](#目录)

---

## 常见问题 FAQ

### Q1：我应该从哪个技术开始学？

如果你完全没有 AI 开发经验，从 **Prompt Engineering** 开始。它不需要复杂基础设施，只要能调用一个 LLM API 就能练习，而且能很快反馈出任务边界。掌握提示词技巧后，再按顺序学习 RAG → Function Calling → Agent。

### Q2：微调和 RAG 到底该选哪个？

一个实用判断是：如果问题是“模型不知道某个知识”（如公司内部文档、最新新闻），优先选 RAG；如果问题是“模型的行为方式不对”（如输出格式、对话风格），再考虑微调。两者也可以组合使用。

### Q3：学智能体开发需要什么基础？

你需要：1）熟练使用至少一门编程语言（Python 推荐）；2）理解 API 调用和异步编程；3）基本的 LLM 使用经验（至少用过 ChatGPT 或 Claude 的 API）。Function Calling 是智能体开发的前置知识，务必先掌握。

### Q4：OpenClaw 和 LangChain 有什么区别？

LangChain 是一个**开发库**，提供构建智能体的工具和抽象；OpenClaw 是一个**完整框架**，提供从消息接入到智能体运行的端到端解决方案。如果你要快速搭建一个能接入 Telegram/Discord 的智能体，OpenClaw 更方便；如果你要深度定制智能体逻辑，LangChain 更灵活。

### Q5：如何评估我的 AI 应用是否足够好？

建立评估集（Evaluation Set），包含 20 到 50 个覆盖不同场景的测试用例。每个用例定义输入、期望行为和评分规则，运行后统计成功率。成功率低于 80% 的场景需要重点优化。参考 §12 Harness Engineering 了解详细方法。

### Q6：上下文窗口不够用怎么办？

优先尝试：1）增量摘要——对历史对话进行压缩；2）相关性检索——只检索与当前问题相关的上下文；3）结构化模板——用 XML/JSON 减少冗余描述。如果仍然不够，考虑 Multi-Agent 架构将上下文分散到不同智能体。

---

## 推荐学习资源

### 官方文档与论文

| 资源 | 类型 | 链接 |
| ---- | ---- | ---- |
| Attention Is All You Need | 论文 | [arXiv](https://arxiv.org/abs/1706.03762) |
| OpenClaw 文档 | 框架文档 | [docs.openclaw.ai](https://docs.openclaw.ai/) |
| Anthropic Cookbook | 示例代码 | [GitHub](https://github.com/anthropics/anthropic-cookbook) |
| PEFT 库文档 | 微调工具 | [GitHub](https://github.com/huggingface/peft) |
| LangChain 文档 | 框架文档 | [python.langchain.com](https://python.langchain.com/) |
| MCP 规范 | 协议文档 | [modelcontextprotocol.io](https://modelcontextprotocol.io/specification/) |

### 在线学习平台

| 平台 | 课程 | 特点 |
| ---- | ---- | ---- |
| Fast.ai | Practical Deep Learning | 实践导向 |
| Coursera | Deep Learning Specialization | 系统全面 |
| Hugging Face | Transformers 课程 | 专注于 LLM |
| DeepLearning.AI | ChatGPT Prompt Engineering | 提示词专项 |

### 开源项目推荐

| 项目 | 用途 | 链接 |
| ---- | ---- | ---- |
| LlamaIndex | RAG 开发 | [GitHub](https://github.com/run-llama/llama_index) |
| LangGraph | 工作流与 Agent 编排 | [GitHub](https://github.com/langchain-ai/langgraph) |
| Dify | 零代码/低代码 AI 平台 | [GitHub](https://github.com/langgenius/dify) |
| CrewAI | Multi-Agent 开发 | [GitHub](https://github.com/crewAIInc/crewAI) |
| RAGAS | RAG 评估 | [GitHub](https://github.com/explodinggradients/ragas) |

---

## 进阶路径指引

掌握基础路线后，可选择以下三大进阶方向：

### 路径 A：AI 基础设施方向

深入理解模型训练和部署的工程实践：

1. **模型量化与推理优化**：学习 GPTQ、AWQ、vLLM 等推理加速技术
2. **分布式训练**：学习 DeepSpeed、FSDP 等大规模训练框架
3. **模型服务化**：学习 Triton Inference Server、BentoML 等部署方案

### 路径 B：AI 应用产品方向

深入理解 AI 产品的设计和用户体验：

1. **AI 产品设计**：学习人机交互设计、AI UX 实践建议
2. **多模态应用**：学习视觉、语音等多模态 AI 应用开发
3. **AI 安全与对齐**：学习 RLHF、Constitutional AI 等对齐技术

### 路径 C：AI 智能体深度方向

深入理解智能体系统的高级架构：

1. **智能体评估与优化**：深入学习 Harness Engineering，建立 CI/CD for AI 流程
2. **复杂 Multi-Agent 系统**：学习 LangGraph 等图编排框架
3. **自主智能体**：探索 AutoGPT、BabyAGI 等自主智能体架构

---

## 核心术语表

| 术语 | 英文 | 释义 |
| ---- | ---- | ---- |
| 大语言模型 | Large Language Model (LLM) | 参数规模达数十亿以上的语言模型，能理解和生成自然语言 |
| 提示词工程 | Prompt Engineering | 通过优化输入提示词来引导 LLM 产生期望输出的技术 |
| 微调 | Fine-tuning | 在特定数据集上继续训练预训练模型，使其适应特定任务 |
| 低秩适配 | LoRA (Low-Rank Adaptation) | 只训练少量低秩参数的参数高效微调方法 |
| 检索增强生成 | RAG (Retrieval-Augmented Generation) | 结合外部知识库检索来增强 LLM 回答质量的方法 |
| 函数调用 | Function Calling | LLM 根据上下文决定调用外部工具或 API 的机制 |
| 模型上下文协议 | MCP (Model Context Protocol) | Anthropic 提出的 Agent 与工具连接的开放标准 |
| 智能体 | Agent | 能自主感知、决策和执行动作的 AI 系统 |
| 多智能体 | Multi-Agent | 多个专业智能体协作完成复杂任务的系统 |
| 上下文工程 | Context Engineering | 系统性管理 LLM 上下文信息的工程实践 |
| 智能体技能 | Agent Skill | 将特定功能封装为可复用单元的标准格式 |
| 评估工程 | Harness Engineering | 通过系统化评估驱动 AI 系统开发的工程实践 |
| 思维链 | Chain-of-Thought (CoT) | 引导模型展示推理过程的提示词技巧 |
| 少样本学习 | Few-Shot Learning | 通过少量示例引导模型学习特定输出模式 |
| 向量数据库 | Vector Database | 专门存储和检索向量嵌入的数据库 |
| 词元 | Token | LLM 处理文本的基本单位 |
| 上下文窗口 | Context Window | LLM 一次能处理的最大 Token 数量 |
| 幻觉 | Hallucination | LLM 生成看似合理但实际错误的内容 |
| 自注意力 | Self-Attention | Transformer 中计算序列内部元素相关性的机制 |
| 重排序 | Re-Ranker | 对初步检索结果进行精细相关性排序的模型 |

⬆️ [返回目录](#目录)

---

**文档元信息**：

- 难度等级：⭐⭐⭐
- 类型：技术笔记
- 更新日期：2026-04-26
- 预计阅读时间：90 分钟
