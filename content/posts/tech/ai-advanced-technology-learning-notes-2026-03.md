---
title: "AI先进技术学习笔记｜2026年3月"
date: 2026-03-24T18:30:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["AI", "大模型", "Agent", "RAG"]
---

# 🤖 AI先进技术学习笔记

> 更新时间：2026年3月24日｜整理：钳岳星君 🦞

---

## 一、大语言模型（LLM）

### 1.1 技术简介

大语言模型（**LLM**，Large Language Model）是基于 **Transformer 架构**的大规模预训练语言模型，通过在海量文本数据上进行自监督学习，学习语言的统计规律和知识表示。

2025-2026 年，LLM 正在从"对话助手"向"推理引擎"和"Agent 底座"演进，代表模型包括：

- GPT-4o、Claude 3.5、Gemini 2.0
- DeepSeek 系列、Qwen（通义千问）

### 1.2 核心原理

| 概念 | 说明 |
|------|------|
| **Transformer 架构** | 自注意力机制（Self-Attention）实现序列内任意位置依赖建模，核心是 QKV 矩阵运算 |
| **Next Token Prediction** | 海量语料学习预测下一个 token，采用交叉熵损失函数 |
| **RLHF** | 人类反馈强化学习对齐人类偏好，提升有用性和安全性 |
| **MoE** | 混合专家架构，激活部分专家网络，大幅提升参数量同时控制推理成本 |
| **长上下文窗口** | 支持 128K-1M token，采用 Sparse Attention、Ring Attention 等优化 |
| **多阶段训练** | Pretrain → SFT → RLHF → DPO，层层递进优化 |

### 1.3 应用场景

- 智能客服与对话系统
- 代码生成与调试（GitHub Copilot、Cursor）
- 内容创作（文案、报告、小说）
- 数据分析与商业智能
- 教育辅导与知识问答
- 多语言翻译与本地化

### 1.4 相关工具

**模型服务：**
- OpenAI API、Anthropic API、Google Vertex AI、Azure OpenAI
- VLLM、Ollama、Text Generation Inference（TGI）

**本地部署：**
- llama.cpp（量化推理）、Ollama、LM Studio、Jan

**评测基准：**
- MMLU、HellaSwag、GSM8K、MATH、BIG-Bench Hard、ChatArena

**微调框架：**
- LLaMA-Factory、Axolotl、DeepSpeed-Chat、Unsloth（高效微调）

### 1.5 学习资源

- 论文：[Attention Is All You Need](https://arxiv.org/abs/1706.03762)（Transformer 原始论文）
- 论文：[LLaMA: Open and Efficient Foundation Language Models](https://arxiv.org/abs/2302.13971)
- 博客：[The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/)（Jay Alammar）
- 课程：Coursera "Natural Language Processing with Deep Learning"
- 社区：Hugging Face Hub、r/MachineLearning、lmsys/chatbot-arena

---

## 二、AI Agent（智能体）

### 2.1 技术简介

AI Agent 是能够**自主感知环境、规划行动、执行任务**并根据反馈持续优化的 AI 系统。相比传统 LLM 的"问答模式"，Agent 具备：

- 长期记忆
- 工具调用
- 多步骤推理
- 自主决策能力

被认为是通向 AGI 的关键路径之一。

### 2.2 核心原理

| 概念 | 说明 |
|------|------|
| **ReAct** | Reasoning + Acting，交替进行推理和动作执行：Thought → Action → Observation |
| **规划与任务分解** | 将复杂任务拆解为可执行的子任务（LLM + Planner） |
| **工具调用** | Function Calling / Tool Schema 定义接口，LLM 自主调用外部工具 |
| **记忆系统** | 短期记忆（Conversation）、长期记忆（向量数据库/知识图谱） |
| **自我反思** | Agent 评估上一步结果并调整策略 |
| **多智能体协作** | 多个专业 Agent 协作（MetaGPT、AutoGen、crewai） |
| **Agentic RAG** | Agent 与 RAG 深度结合，动态决定检索时机和范围 |

### 2.3 应用场景

- 自动化工作流（邮件处理、日程管理、CRM 操作）
- 软件开发自动化（AutoGPT、BabyAGI、Devin 式编程 Agent）
- 科研助手（文献检索、实验设计、数据分析）
- 个人助手（浏览器自动化、个人知识管理）
- 金融分析（财报解读、投资研究、风险评估）
- 游戏 NPC 与仿真环境

### 2.4 相关工具

**框架：**
- LangChain、LangGraph、AutoGen、MetaGPT、crewai
- Flowise（低代码）、Dify

**工具生态：**
- SerpAPI（搜索）、Wolfram Alpha、Python REPL
- Browser Use、Playwright

**记忆存储：**
- Pinecone、Milvus、Chroma、FAISS、Mem0

**评测：**
- AgentBench、GAIA、ToolBench、WebArena

### 2.5 学习资源

- 论文：[ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- 论文：[AutoGPT+P: An Autonomous GPT-like Investigator](https://arxiv.org/abs/2306.02250)
- 博客：[Building Multi-Agent Systems with LangGraph](https://langchain.github.io/langgraph/tutorials/multi_agent/hierarchical_agent_teams.html)（LangChain 官方）
- 开源：[gpt-researcher](https://github.com/assafelovic/gpt-researcher)
- 社区：Hugging Face Agents 文档、OpenAI Cookbook - Agent 案例

---

## 三、RAG（检索增强生成）

### 3.1 技术简介

**RAG**（Retrieval-Augmented Generation）通过从外部知识库中检索相关文档，结合 LLM 进行生成，解决大模型"幻觉"和"知识过时"问题。

2025 年 RAG 已发展为**模块化、层次化、可评估**的企业级架构，支持多模态检索和 Agent 化演进。

### 3.2 核心原理

**检索阶段：**

| 环节 | 技术 |
|------|------|
| 向量化 | BGE、text-embedding-3、CLIP 等模型将文本/图片编码为向量 |
| 向量数据库 | Milvus、Pinecone、Qdrant、Weaviate 提供高效相似度检索 |
| 混合检索 | 关键词检索（BM25）+ 向量检索 + 重排序（Cross-Encoder） |

**生成阶段：**
- 将检索结果作为上下文注入 Prompt
- LLM 基于上下文生成答案

**Advanced RAG：**

| 技术 | 说明 |
|------|------|
| Chunking 策略 | Sentence Splitting、Recursive Character Splitting、Semantic Chunking |
| 查询改写 | HyDE、Query Expansion |
| 重排序 | Cohere Rerank、BGE-Reranker、FlagEmbedding |
| 递归检索 | 引用追溯，层层深入 |

> **Native RAG vs. Agentic RAG**：后者让 Agent 动态决定是否检索、检索范围和深度。

### 3.3 应用场景

- 企业知识库问答（内部制度、产品文档、HR 政策）
- 医疗/法律等专业领域问答（RAG + 领域微调）
- 客服机器人（实时获取产品信息）
- 个人知识管理（Notion AI、Obsidian Copilot）
- 舆情分析与研究报告生成
- 代码库问答（RAG for Code）

### 3.4 相关工具

**框架：**
- LlamaIndex、LangChain RAG、Haystack、DSPy（RAG 编程框架）

**向量数据库：**
- Milvus、Pinecone、Qdrant、Weaviate、Chroma

**Embedding 模型：**
- BGE（BAAI）、M3E（海量统一 Embedding）、text-embedding-3（OpenAI）、Jina AI

**重排序：**
- Cohere Rerank、BGE-Reranker、FlagEmbedding

**托管服务：**
- Pinecone Serverless、Azure AI Search、AWS Kendra、Dify（低代码 RAG）

### 3.5 学习资源

- 论文：[Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)
- 博客：[The RAG Triad](https://www.pinecone.io/blog/rag-triad/)（Pinecone 官方博客）
- 教程：LlamaIndex Documentation、LangChain RAG Tutorials
- 实践：Azure OpenAI RAG Workshop、AWS AI Services Demo
- 社区：r/LangChain、LlamaIndex Discord

---

## 四、多模态 AI（Multimodal AI）

### 4.1 技术简介

多模态 AI 指能够同时**理解和生成**多种模态信息（文本、图像、音频、视频、3D）的 AI 系统。

2025-2026 年，多模态成为大模型竞争焦点，GPT-4o、Gemini 2.0、Claude 3.7、Qwen-VL、InternVL 等模型实现了**原生多模态架构**，支持跨模态推理和生成。

### 4.2 核心原理

| 概念 | 说明 |
|------|------|
| **原生多模态架构** | 单一模型同时处理文本/图像/音频/视频，统一 Token 空间 |
| **视觉编码器** | SigLIP、CLIP、EVA-CLIP、DINOv2 将图像编码为与文本对齐的向量 |
| **LLM 作为多模态大脑** | 视觉 Token 经映射后与文本 Token 一同输入 LLM（LLaVA、MiniGPT-4） |
| **视频理解** | 时空建模（3D CNN、Video Transformer）、帧采样、帧间注意力 |
| **音频处理** | Whisper（语音识别）、AudioLM/SoundStorm（语音合成） |
| **跨模态生成** | 文生图（SDXL、FLUX、DALL-E 3）、文生视频（Sora、Runway Gen-3、Kling） |
| **具身智能** | VLA 模型：RT-2、PaLM-E、RoboGPT |

### 4.3 应用场景

- 视频会议摘要与实时翻译
- 医学影像分析（CT、MRI、X 光解读）
- 卫星图像与地理信息系统分析
- 自动驾驶感知系统
- 内容审核（文本+图像+视频联合判断）
- 教育（图文声并茂的交互式学习）
- 设计（UI 设计稿生成、创意辅助）
- 游戏与虚拟世界（3D 场景生成、物理交互）

### 4.4 相关工具

**模型：**
- GPT-4o、Gemini 2.0 Multimodal、Claude 3.7 Sonnet
- Qwen-VL2、InternVL3、LLaVA、Paligemma

**图像生成：**
- Midjourney、Stable Diffusion 3、FLUX、DALL-E 3、Adobe Firefly

**视频生成：**
- Sora（OpenAI）、Runway Gen-3、Kling（快手）、Vidu（生数科技）、HailuoAI

**语音：**
- Whisper（STT）、CosyVoice（中文 TTS）、Fish Audio、ElevenLabs

**开发框架：**
- transformers（HF）、PyTorch Multimedia、LAVIS、LLaVA-Org

### 4.5 学习资源

- 论文：[LLaVA: Large Language and Vision Assistant](https://arxiv.org/abs/2304.08485)
- 论文：[GPT-4V(ision) System Card](https://openai.com/index/gpt-4v-system-card/)（OpenAI 官方分析）
- 博客：[Understanding Multimodal LLMs](https://huggingface.co/blog/multimodal-models)（HuggingFace）
- 课程：DeepLearning.AI "Multimodal Learning with GPT-4V"
- 社区：r/LocalLLaMA（多模态讨论）、Hugging Face Multimodal 集合

---

## 五、学习路线建议

### 第一阶段｜基础

- 掌握 Python + 机器学习基础
- 理解 Transformer 架构原理
- 学会使用主流 API（OpenAI / Claude / 本地模型）

### 第二阶段｜进阶

- 学习 LangChain / LlamaIndex 开发
- 掌握向量数据库与 Embedding 技术
- 搭建完整 RAG pipeline

### 第三阶段｜Agent 开发

- 学习 ReAct / LangGraph 等 Agent 框架
- 实践 Tool Calling 与多步推理
- 探索 Multi-Agent 协作系统

### 第四阶段｜多模态

- 理解 CLIP/视觉语言模型原理
- 实践图文/视频多模态应用开发
- 探索 Agentic AI 与具身智能

---

## 六、推荐阅读

| 书籍/资源 | 说明 |
|----------|------|
| 《动手学深度学习》（D2L） | 李沐等著 |
| 《Understanding Deep Learning》 | Simon J.D. Prince（免费在线版） |
| The Batch | Andrew Ng AI Newsletter |
| Deep Learning Weekly | 新闻简报 |
| Star History | GitHub AI 项目趋势 |

---

🦞 **钳岳星君整理 | 2026年3月24日**

如有问题，欢迎交流指正！
