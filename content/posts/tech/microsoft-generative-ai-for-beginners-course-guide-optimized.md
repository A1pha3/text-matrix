---
title: "microsoft/generative-ai-for-beginners：109k Stars 生成式AI入门完全指南"
date: "2026-04-06T22:35:00+08:00"
slug: "microsoft-generative-ai-for-beginners-course-guide"
description: "微软官方109k Stars生成式AI入门课程完全指南，涵盖21节系统课程、Python/TypeScript双代码示例、Azure OpenAI/GitHub Models/OpenAI API三种平台、RAG/Agent/微调等高级主题。"
draft: false
categories: ["技术笔记"]
tags: ["Generative AI", "LLM", "提示工程", "RAG", "AI Agent", "微软", "Azure OpenAI", "OpenAI API"]
---

# microsoft/generative-ai-for-beginners：109k Stars 生成式AI入门完全指南

## 学习目标

读完本文，你将能够：

1. 说清生成式 AI 和 LLM 的核心概念，以及 Transformer 架构的基本作用
2. 在 Azure OpenAI、GitHub Models、OpenAI API 三种平台中做出选择并配置开发环境
3. 理解提示工程的基础和进阶技术（Few-shot、Chain-of-Thought、Function Calling）
4. 构建文本生成、聊天、搜索（RAG）、图片生成等实际应用的原型
5. 解释 RAG、Agent、微调等高级主题的基本思想和适用场景

## 目录

1. [学习目标](#学习目标)
2. [阅读前提](#阅读前提)
3. [项目概述](#项目概述)
4. [环境准备](#环境准备)
5. [课程大纲（21 节）](#课程大纲21-节)
6. [实战项目（第 6-11 节）](#实战项目第-6-11-节)
7. [高级主题（第 12-18 节）](#高级主题第-12-18-节)
8. [模型专题（第 19-21 节）](#模型专题第-19-21-节)
9. [配套资源](#配套资源)
10. [常见问题](#常见问题)
11. [自测题](#自测题)
12. [进阶路径](#进阶路径)
13. [总结](#总结)

---

## 阅读前提

本文覆盖以下内容：

- 生成式 AI 和大语言模型（LLM）的工作原理
- 在不同平台上运行 AI 应用（Azure OpenAI、GitHub Models、OpenAI API）
- 提示工程的核心技巧和进阶方法
- 构建文本生成、聊天、搜索、图片生成等实际应用
- RAG、Agent、微调等高级主题
- AI 应用安全

---

## 1. 项目概述

### 1.1 是什么

**microsoft/generative-ai-for-beginners** 是微软官方推出的生成式 AI 入门课程，21 节课程覆盖从基础到实战。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **109k** |
| GitHub Forks | **58.5k** |
| Contributors | **148+** |
| Commits | **2,177** |
| License | **MIT** |
| 最新更新 | **2026-03-28** |
| 课程语言 | **50+ 种语言** |

### 1.3 项目特色

| 特色 | 说明 |
|------|------|
| **微软官方课程** | Microsoft Cloud Advocates 团队打造 |
| **21 节系统课程** | 从入门到实战全覆盖 |
| **多语言支持** | 简体中文、English、日语等 50+ 语言 |
| **双代码示例** | Python + TypeScript 同时提供 |
| **视频配套** | 每节课程都有视频讲解 |
| **多平台支持** | Azure OpenAI、GitHub Models、OpenAI API |

### 1.4 课程体系

课程分为两种类型：

| 类型 | 说明 |
|------|------|
| **Learn（学习）** | 理论概念讲解 + 视频 |
| **Build（构建）** | 实战项目 + 代码示例 |

---

## 2. 环境准备

### 2.1 开发环境要求

```bash
# Python 基础（推荐）
# 了解变量、函数、类基本概念

# TypeScript/JavaScript 基础
# 了解异步编程、API 调用

# Azure 账号或 OpenAI API Key
# 注册地址：https://aka.ms/genai-beginners/azure-open-ai
```

### 2.2 三种运行环境

| 平台 | 说明 | 适用场景 |
|------|------|----------|
| **Azure OpenAI Service** | 微软云 + 企业级安全 | 生产环境 |
| **GitHub Models** | GitHub 官方模型市场 | 快速实验 |
| **OpenAI API** | OpenAI 官方 API | 原生开发 |

### 2.3 环境配置

```bash
# 克隆课程仓库（不含翻译，减小体积）
git clone --filter=blob:none --sparse \
  https://github.com/microsoft/generative-ai-for-beginners.git

cd generative-ai-for-beginners

# 只下载英文版
git sparse-checkout set --no-cone \
  '/*' '!translations' '!translated_images'

# 安装依赖
pip install -r requirements.txt
# 或
npm install
```

---

## 3. 课程大纲（21 节）

### 3.1 基础理论（第 1-5 节）

**第 00 节：课程设置**

```bash
# 设置开发环境
# 安装 VS Code、Python、Node.js
# 配置 API 访问凭证
```

**第 01 节：生成式 AI 和 LLM 入门**

核心概念：

| 概念 | 说明 |
|------|------|
| **生成式 AI** | 能够创建新内容（文本、图像、代码）的 AI |
| **大语言模型 (LLM)** | 基于大规模文本训练的语言模型 |
| **Transformer** | 支撑 GPT 的核心架构 |
| **Token** | 文本处理的最小单位 |

**第 02 节：探索和比较不同 LLM**

如何选择合适的模型：

| 因素 | 考虑点 |
|------|--------|
| **任务类型** | 文本生成 vs 对话 vs 代码 |
| **延迟要求** | 实时交互 vs 批处理 |
| **成本** | API 调用费用 |
| **隐私需求** | 数据是否敏感 |

**第 03 节：负责任地使用生成式 AI**

AI 伦理和安全：

| 风险 | 缓解措施 |
|------|----------|
| **幻觉** | RAG、事实核查 |
| **偏见** | 多样化训练数据 |
| **滥用** | 输入输出过滤 |
| **隐私泄露** | 数据脱敏 |

**第 04 节：提示工程基础**

核心原则：

```python
# 清晰具体的指令
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "你是一个助手。"},
        {"role": "user", "content": "解释量子计算，简洁明了。"}
    ]
)
```

**第 05 节：高级提示技术**

| 技术 | 说明 |
|------|------|
| **Few-shot** | 提供示例让模型学习 |
| **Chain-of-Thought** | 引导模型展示推理过程 |
| **角色扮演** | System Prompt 设定角色 |
| **结构化输出** | JSON Mode 指定格式 |

---

## 4. 实战项目（第 6-11 节）

### 4.1 构建文本生成应用

**第 06 节：文本生成应用**

```python
# Python 示例：Azure OpenAI
from openai import AzureOpenAI

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-02-01",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "写一首关于 AI 的诗"}
    ]
)
print(response.choices[0].message.content)
```

### 4.2 构建聊天应用

**第 07 节：聊天应用开发**

聊天界面核心组件：

| 组件 | 说明 |
|------|------|
| **消息历史** | 维护对话上下文 |
| **流式响应** | 实时显示生成内容 |
| **Markdown 渲染** | 美化输出格式 |
| **代码高亮** | 代码片段着色 |

```python
# 流式响应实现
def stream_chat(messages):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        stream=True
    )
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

### 4.3 构建搜索应用

**第 08 节：向量数据库和 Embedding**

Embedding 核心流程：

```python
# 1. 文本转向量
from openai import OpenAI
client = OpenAI()

response = client.embeddings.create(
    model="text-embedding-3-small",
    input="要嵌入的文本"
)
vector = response.data[0].embedding

# 2. 存储到向量数据库
# 支持：Pinecone、Milvus、Chroma、FAISS

# 3. 相似度搜索
query_vector = get_embedding("搜索 query")
results = vector_db.search(
    query_vector,
    top_k=5
)
```

### 4.4 构建图片生成应用

**第 09 节：DALL-E 图片生成**

```python
# 调用 DALL-E 3 生成图片
response = client.images.generate(
    model="dall-e-3",
    prompt="一个宇航员在火星上骑自行车的插画风格图片",
    size="1024x1024",
    quality="standard",
    n=1
)
image_url = response.data[0].url
```

### 4.5 低代码 AI 应用

**第 10 节：Power Platform 集成**

| 工具 | AI 能力 |
|------|---------|
| **Power Apps** | AI Builder 拖拽式开发 |
| **Power Automate** | AI Flow 自动化流程 |
| **Copilot Studio** | 自定义 Copilot |

### 4.6 Function Calling

**第 11 节：外部函数集成**

Function Calling 使 LLM 能够调用外部工具：

```python
# 定义可调用的函数
functions = [
    {
        "name": "get_weather",
        "description": "获取城市天气",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称"
                }
            },
            "required": ["city"]
        }
    }
]

# LLM 自动选择调用
response = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=messages,
    tools=functions,
    tool_choice="auto"
)
```

---

## 5. 高级主题（第 12-18 节）

### 5.1 AI 应用 UX 设计

**第 12 节：用户体验设计**

| 原则 | 说明 |
|------|------|
| **透明度** | 明确告知用户这是 AI |
| **不确定性** | 展示置信度 |
| **可解释性** | 解释 AI 决策 |
| **容错性** | 优雅处理错误 |

### 5.2 AI 应用安全

**第 13 节：安全实践建议**

| 威胁 | 防护措施 |
|------|----------|
| **提示注入** | 输入验证和过滤 |
| **数据泄露** | 敏感信息脱敏 |
| **API 滥用** | 限流和认证 |
| **模型劫持** | System Prompt 保护 |

### 5.3 LLMOps 和生命周期管理

**第 14 节：LLM 应用生命周期**

```
规划 → 开发 → 测试 → 部署 → 监控 → 迭代
```

关键指标：

| 指标 | 说明 |
|------|------|
| **延迟** | P50/P95/P99 响应时间 |
| **成本** | 每千 Token 费用 |
| **质量** | 任务完成率 |
| **安全** | 攻击拦截率 |

### 5.4 RAG 和向量数据库

**第 15 节：RAG 架构**

完整 RAG 流程：

```python
# 1. 文档加载和分块
from langchain.document_loaders import PDFLoader
loader = PDFLoader("document.pdf")
documents = loader.load()

# 2. 文本分块
from langchain.text_splitter import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
chunks = splitter.split_documents(documents)

# 3. 向量化并存储
from langchain.vectorstores import Chroma
db = Chroma.from_documents(chunks, embeddings)

# 4. 检索增强生成
retrieved = db.similarity_search(query)
context = "\n".join([doc.page_content for doc in retrieved])
prompt = f"基于以下上下文回答：{context}\n\n问题：{query}"
```

### 5.5 开源模型

**第 16 节：Hugging Face 开源模型**

| 模型 | 特点 | 适用场景 |
|------|------|----------|
| **Llama 3** | 开源可商用 | 本地部署 |
| **Mistral** | 高性能小模型 | 边缘设备 |
| **Falcon** | 阿拉伯语优化 | 多语言 |
| **MPT** | 商业友好 | 企业应用 |

### 5.6 AI Agent

**第 17 节：AI Agent 开发**

Agent 核心组件：

| 组件 | 说明 |
|------|------|
| **规划** | 分解复杂任务 |
| **记忆** | 存储和检索上下文 |
| **工具** | 调用外部 API |
| **执行** | 循环执行直到完成 |

```python
# 简化 Agent 框架
class SimpleAgent:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools

    def run(self, task):
        # 1. 规划
        plan = self.llm_planner(task, self.tools)

        # 2. 执行
        for step in plan:
            result = self.execute_step(step)

        # 3. 返回结果
        return result
```

### 5.7 微调

**第 18 节：LLM 微调技术**

| 方法 | 成本 | 效果 |
|------|------|------|
| **全参数微调** | 高 | 最好 |
| **LoRA** | 中 | 接近全参数 |
| **QLoRA** | 低 | 良好 |
| **Prompt Tuning** | 最低 | 有限 |

```python
# LoRA 微调示例（使用 PEFT）
from peft import LoraConfig, get_peft_model

config = LoraConfig(
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(base_model, config)
```

---

## 6. 模型专题（第 19-21 节）

### 6.1 小语言模型（SLM）

**第 19 节：Phi-3 和 SLM**

| 模型 | 参数 | 特点 |
|------|------|------|
| **Phi-3-mini** | 3.8B | 手机可运行 |
| **Phi-3-small** | 7B | 笔记本可运行 |
| **Phi-3-medium** | 14B | 高性能 |

### 6.2 Mistral 模型

**第 20 节：Mistral 系列**

| 模型 | 上下文 | 优势 |
|------|--------|------|
| **Mistral 7B** | 8K | 高效率 |
| **Mixtral 8x7B** | 32K | MoE 架构 |
| **Mistral Large** | 32K | 顶级性能 |

### 6.3 Meta 模型

**第 21 节：Llama 3 系列**

| 版本 | 参数 | Context |
|------|------|---------|
| **Llama 3 8B** | 80 亿 | 8K |
| **Llama 3 70B** | 700 亿 | 8K |
| **Llama 3.1 405B** | 4050 亿 | 128K |

---

## 7. 配套资源

### 7.1 微软相关课程

| 课程 | 说明 |
|------|------|
| **LangChain for Beginners** | LLM 应用开发框架 |
| **Azure AI Foundry** | 企业级 AI 平台 |
| **MCP for Beginners** | Model Context Protocol |
| **AI Agents for Beginners** | AI Agent 开发 |

### 7.2 开发者社区

| 社区 | 链接 |
|------|------|
| **Microsoft Foundry Discord** | discord.gg/nTYy5BXMWG |
| **Azure AI Foundry Forum** | aka.ms/foundry/forum |
| **GitHub Discussions** | 课程仓库内讨论区 |

---

## 8. 常见问题

### 8.1 需要编程基础吗

**问题**：我是编程零基础，能学这个课程吗？

**答案**：需要基本的 Python 或 JavaScript 基础。课程提供了预备知识链接：

- Python 入门：aka.ms/genai-beginners/python
- TypeScript 入门：aka.ms/genai-beginners/typescript

如果你完全没有编程基础，建议先花 1-2 周学习 Python 基础（变量、函数、类、基本语法），再来学习这个课程。

### 8.2 需要付费吗

**问题**：课程免费吗？需要购买 API 吗？

**答案**：

- 课程本身：**完全免费**（MIT 协议）
- API 调用：需要付费（Azure/GitHub/OpenAI）
- GitHub Models：有一定免费额度（适合学习和实验）
- Azure OpenAI：新用户有免费额度和学生优惠

### 8.3 如何选择 API

**问题**：Azure OpenAI、GitHub Models、OpenAI API 哪个好？

| 场景 | 推荐 |
|------|------|
| 企业生产环境 | Azure OpenAI（企业级安全、SLA 保障） |
| 快速实验测试 | GitHub Models（免费额度、简单配置） |
| 原生 OpenAI 开发 | OpenAI API（最新模型、最快更新） |

### 8.4 课程学完能找到 AI 相关工作吗

**问题**：学完这个课程后，我能达到什么水平？

**答案**：这个课程是入门级，学完后你能：

- 理解生成式 AI 的核心概念
- 使用 API 构建基础的 AI 应用
- 知道提示工程、RAG、Agent 等高级主题的基本思想

但要找到 AI 相关工作，还需要：

1. 深入某一个方向（例如 RAG、Agent 或微调）
2. 构建 2-3 个完整的项目（放进作品集）
3. 学习更多进阶课程（例如 DeepLearning.AI、Fast.ai）
4. 参与开源项目或实习

### 8.5 学完后应该继续学什么

参见下面的「进阶路径」章节。

---

## 9. 自测题

### 基础概念

1. Transformer 架构的核心机制是什么？
   - A. 卷积
   - B. 注意力机制
   - C. 循环神经网络
   - D. 对抗训练

2. Token 在 LLM 中的作用是什么？
   - A. 存储模型权重
   - B. 文本处理的最小单位
   - C. 控制生成速度
   - D. 管理 API 调用

### 提示工程

3. Chain-of-Thought 提示技术的核心思想是什么？
   - A. 提供多个示例
   - B. 引导模型展示推理过程
   - C. 设定角色身份
   - D. 指定输出格式

4. Few-shot 提示是指什么？
   - A. 只提供一个示例
   - B. 提供零个示例
   - C. 提供少量示例（2-5 个）
   - D. 提供大量示例（>10 个）

### RAG 和 Agent

5. RAG 的核心流程是哪四步？
   - A. 加载 → 分块 → 向量化 → 检索生成
   - B. 训练 → 微调 → 部署 → 监控
   - C. 规划 → 执行 → 验证 → 修正
   - D. 编码 → 加密 → 传输 → 解密

6. AI Agent 和单次 LLM 调用的核心区别是什么？
   - A. Agent 更便宜
   - B. Agent 有循环执行和工具调用能力
   - C. Agent 只能用开源模型
   - D. Agent 不需要提示词

### 参考答案

1. B（注意力机制是 Transformer 的核心）
2. B（Token 是文本分词后的最小单位）
3. B（Chain-of-Thought 让模型展示中间推理步骤）
4. C（Few-shot = 提供少量示例）
5. A（加载文档 → 分块 → 向量化存储 → 检索增强生成）
6. B（Agent 可以循环调用工具直到任务完成）

---

## 10. 进阶路径

### 第一阶段：巩固基础（2-4 周）

- 完整学完 `generative-ai-for-beginners` 的 21 节课程
- 每节课程都动手运行代码（不要只看不动手）
- 加入 Microsoft Foundry Discord 社区，提问交流
- 构建一个小项目：例如「基于 RAG 的文档问答系统」

### 第二阶段：深入方向（1-3 个月）

根据兴趣选择方向：

**方向 A：RAG 和向量搜索**
- 学习 LangChain 或 LlamaIndex 框架
- 深入理解 Embedding 模型、分块策略、混合检索
- 构建项目：企业知识库问答系统

**方向 B：AI Agent 开发**
- 学习 `ai-agents-for-beginners`（微软另一门课程）
- 理解 ReAct、Plan-and-Execute、Multi-Agent 等模式
- 构建项目：自动化任务执行 Agent

**方向 C：模型微调**
- 学习 LoRA、QLoRA 微调技术
- 使用 Hugging Face PEFT 库
- 构建项目：基于专有数据微调 LLM

### 第三阶段：生产实践（3-6 个月）

- 学习 LLMOps：模型部署、监控、版本管理
- 学习 AI 应用安全：提示注入防护、数据泄露防护
- 学习成本和延迟优化：模型选择、缓存策略、批处理
- 参与开源项目（例如 LangChain、LlamaIndex）

### 相关资源

| 资源 | 链接 | 用途 |
|------|------|------|
| 课程 GitHub | https://github.com/microsoft/generative-ai-for-beginners | 源码、视频、作业 |
| 中文版 | translations/zh-CN/README.md | 中文翻译 |
| Discord 社区 | https://discord.gg/nTYy5BXMWG | 提问交流 |
| LangChain 课程 | microsoft/langchain-for-beginners | 下一门推荐课程 |
| AI Agents 课程 | microsoft/ai-agents-for-beginners | Agent 方向进阶 |

---

## 11. 总结

**microsoft/generative-ai-for-beginners** 是目前最完整的生成式 AI 入门课程之一：21 节课程、Python + TypeScript 双代码示例、Azure OpenAI / GitHub Models / OpenAI API 三种平台、50+ 语言翻译、MIT 协议、109k stars。

**适用人群**：想入门生成式 AI 的开发者、准备 AI 相关面试的求职者、想了解 AI 应用的企业人员、对 AI 感兴趣的学生。

**学习建议**：按顺序学习并动手实践，善用视频讲解，加入 Discord 社区提问交流，完成课程后尝试构建自己的项目。不要只「看」课程，要「跑」代码、「改」代码、「建」项目。

**官方资源**：

- GitHub：https://github.com/microsoft/generative-ai-for-beginners
- 中文版：translations/zh-CN/README.md
- Discord：https://discord.gg/nTYy5BXMWG
