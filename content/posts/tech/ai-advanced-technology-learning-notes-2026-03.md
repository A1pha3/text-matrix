---
title: "AI先进技术学习笔记｜2026年3月"
date: "2026-03-24T18:30:00+08:00"
lastmod: "2026-09-21T12:00:00+08:00"
slug: "ai-advanced-technology-learning-notes-2026-03"
github_repo: "modelcontextprotocol/servers"
source_key: "gh:modelcontextprotocol/servers"
description: "一份面向工程师的 AI 先进技术学习笔记：从大语言模型的核心原理（Transformer、RLHF、MoE）出发，过一遍 AI Agent（ReAct、工具调用、MCP）、RAG 完整技术栈与多模态进展，附对齐入门、学习路线、练习与自测题。"
draft: false
categories: ["技术笔记"]
tags: ["LLM", "RAG", "多模态", "AI Agent", "AI 安全"]
---

# AI 先进技术学习笔记

> 初稿 2026-03-24｜修订 2026-09-21（全文外链与模型名单已按 2026 年 3 月口径复核）
>
> 阅读建议：无基础先读一、五，做完练习一再进二；有基础可直接跳三、四，卡在哪一节就回头翻对应的"相关工具"与"学习资源"。

## 学习目标

读完这份学习笔记后，你应该能够：

- 理解大语言模型（LLM）的核心原理（Transformer、RLHF、MoE）和代表模型
- 解释 AI Agent 的工作机制（ReAct、工具调用、MCP 协议、记忆系统）
- 掌握 RAG（检索增强生成）的完整技术栈（向量数据库、混合检索、Agentic RAG）
- 了解多模态 AI 的进展（图像理解、视频生成、语音交互、具身智能）
- 制定个性化的 AI 技术学习路线

## 目录

- [一、大语言模型（LLM）](#一大语言模型llm)
- [二、AI Agent（智能体）](#二ai-agent智能体)
- [三、RAG（检索增强生成）](#三rag检索增强生成)
- [四、多模态 AI（Multimodal AI）](#四多模态-ai-multimodal-ai)
- [五、AI Safety 与对齐](#五ai-safety-与对齐)
- [六、学习路线建议](#六学习路线建议)
- [七、常见问题 FAQ](#七常见问题-faq)
- [八、练习](#八练习)
- [九、进阶路径](#九进阶路径)
- [十、资料口径与参考来源](#十资料口径与参考来源)
- [自测题](#自测题)

---

## 一、大语言模型（LLM）

### 1.1 技术简介

大语言模型（**LLM**，Large Language Model）是基于 **Transformer 架构**的大规模预训练语言模型，通过在海量文本数据上进行自监督学习，学习语言的统计规律和知识表示。

2025-2026 年，LLM 的定位从"对话助手"扩展到推理和 Agent 底座。截至 2026 年 3 月，代表模型包括：

| 厂商 | 代表模型 | 特点 |
|------|----------|------|
| OpenAI | GPT-5 系列、o3 / o4-mini | GPT-5（2025 年 8 月发布）把对话与推理统一到一个模型里，按问题复杂度自动分配思考量；o3 曾在 ARC-AGI 基准上取得突破性成绩 |
| Anthropic | Claude Opus 4.6、Sonnet 4.5 | Constitutional AI 对齐，200K 上下文，编码与 Agent 任务表现突出 |
| Google | Gemini 3.1 Pro、Gemini 2.5 Flash | 原生多模态，最高百万级 token 输入，推理速度快 |
| DeepSeek | DeepSeek V3.2、DeepSeek R1 | 开源权重模型，主打高性价比推理，R1 以 RLVR 训练路线出圈 |
| Meta | Llama 4 | 开源多模态，Scout 版上下文最高 1000 万 token |
| 阿里巴巴 | Qwen3、Qwen3-VL | 中文优化，开源生态完善，全尺寸覆盖 |

### 1.2 核心原理

| 概念 | 说明 |
|------|------|
| **Transformer 架构** | 自注意力机制（Self-Attention）实现序列内任意位置依赖建模，核心是 QKV 矩阵运算 |
| **Next Token Prediction** | 海量语料学习预测下一个 token，采用交叉熵损失函数 |
| **RLHF** | 人类反馈强化学习对齐人类偏好，InstructGPT 核心方法 |
| **DPO / ORPO** | 直接偏好优化，绕过 Reward Model 直接优化策略 |
| **MoE** | 混合专家架构，按需激活部分专家参数，参数量做大同时控制推理成本（DeepSeek V3、GPT-OSS 明确采用；闭源主力模型架构未公开，业界普遍认为也是 MoE） |
| **长上下文窗口** | 主流模型支持 128K 以上，Gemini 3 Pro 达 1M，Llama 4 Scout 宣称 10M；靠 Sparse Attention、Ring Attention 等优化撑起 |
| **推理模型** | 思维链（Chain-of-Thought）显式化，用 Test-Time Compute 换推理能力 |
| **多阶段训练** | Pretrain → SFT → 偏好对齐（RLHF 或 DPO 二选一或并用），层层递进优化 |

### 1.3 应用场景

- 智能客服与对话系统
- 代码生成与调试（GitHub Copilot、Cursor）
- 内容创作（文案、报告、小说）
- 数据分析与商业智能
- 教育辅导与知识问答
- 多语言翻译与本地化

### 1.4 相关工具

**模型服务：**
- OpenAI API、Anthropic API、Gemini API、Azure OpenAI
- VLLM、Ollama、Text Generation Inference（TGI）

**本地部署：**
- llama.cpp（量化推理）、Ollama、LM Studio、Jan

**评测基准：**
- MMLU、HellaSwag、GSM8K、MATH、BIG-Bench Hard
- **新基准**：ARC-AGI（通用推理）、SWE-bench（软件工程）、GPQA（研究生水平问答）
- **人类偏好榜**：Chatbot Arena（LMArena），匿名对战投票产生排名

**微调框架：**
- LLaMA-Factory、Axolotl、DeepSpeed-Chat、Unsloth（高效微调）

### 1.5 学习资源

- 论文：[Attention Is All You Need](https://arxiv.org/abs/1706.03762)（Transformer 原始论文）
- 论文：[InstructGPT](https://arxiv.org/abs/2203.02155)（RLHF 奠基之作）
- 论文：[DeepSeek-R1](https://arxiv.org/abs/2501.12599)（推理模型突破）
- 博客：[The Illustrated Transformer](https://jalammar.github.io/illustrated-transformer/)（Jay Alammar 的可视化讲解，入门首选）
- 课程：斯坦福 CS224n《Natural Language Processing with Deep Learning》（公开课）
- 社区：Hugging Face Hub、r/MachineLearning、LMArena

---

## 二、AI Agent（智能体）

### 2.1 技术简介

AI Agent 是能够**自主感知环境、规划行动、执行任务**并根据反馈持续优化的 AI 系统。相比传统 LLM 的"问答模式"，Agent 具备：

- 长期记忆
- 工具调用
- 多步骤推理
- 自主决策能力

Claude 4.5、GPT-5、DeepSeek V3.2 等模型的工具调用能力大幅提升，Agent 从研究走向落地。

### 2.2 核心原理

| 概念 | 说明 |
|------|------|
| **ReAct** | Reasoning + Acting，交替进行推理和动作执行：Thought → Action → Observation |
| **规划与任务分解** | 将复杂任务拆解为可执行的子任务（LLM + Planner） |
| **工具调用** | Function Calling / Tool Schema 定义接口，2026 年 MCP 协议成为事实标准 |
| **MCP 协议** | Model Context Protocol，Anthropic 主导的 Agent 工具调用标准 |
| **记忆系统** | 短期记忆（Conversation）、长期记忆（向量数据库/知识图谱） |
| **自我反思** | Agent 评估上一步结果并调整策略 |
| **多智能体协作** | 多个专业 Agent 协作（MetaGPT、AutoGen、crewai、Manus） |
| **Agentic RAG** | Agent 与 RAG 深度结合，动态决定检索时机和范围 |

### 2.3 应用场景

- 自动化工作流（邮件处理、日程管理、CRM 操作）
- 软件开发自动化（Devin、Cursor、Windsurf）
- 科研助手（文献检索、实验设计、数据分析）
- 个人助手（浏览器自动化、个人知识管理）
- 金融分析（财报解读、投资研究、风险评估）
- 计算机使用（Claude Computer Use、ChatGPT agent——2025 年 8 月底接棒已下线的 OpenAI Operator）

### 2.4 相关工具

**框架：**
- LangChain、LangGraph、AutoGen、MetaGPT、crewai
- Flowise（低代码）、Dify

**MCP 生态：**
- [MCP Servers](https://github.com/modelcontextprotocol/servers)（官方维护的参考实现与社区服务器合集）
- 各种 MCP 工具集成（文件系统、数据库、API 等）

**工具生态：**
- SerpAPI（搜索）、Wolfram Alpha、Python REPL
- Browser Use、Playwright

**记忆存储：**
- Pinecone、Milvus、Chroma、FAISS、Mem0

**评测：**
- AgentBench、GAIA、ToolBench、WebArena、SWE-bench

### 2.5 学习资源

- 论文：[ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- 论文：[AutoGPT+P: Affordance-based Task Planning with Large Language Models](https://arxiv.org/abs/2402.10778)（用可供性建模改进任务规划）
- 协议：[Model Context Protocol](https://modelcontextprotocol.io/)（官方协议文档）
- 博客：[Multi-Agent Architectures](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)（LangGraph 官方多智能体概念文档）
- 开源：[gpt-researcher](https://github.com/assafelovic/gpt-researcher)、[Manus](https://manus.im/)、[OpenManus](https://github.com/FoundationAgents/OpenManus)
- 社区：Hugging Face Agents 文档、OpenAI Cookbook - Agent 案例

---

## 三、RAG（检索增强生成）

### 3.1 技术简介

**RAG**（Retrieval-Augmented Generation）通过从外部知识库中检索相关文档，结合 LLM 进行生成，解决大模型"幻觉"和"知识过时"问题。

2025-2026 年 RAG 向模块化、层次化方向演进，企业级落地支持：

- 多模态检索（文本、图像、表格、PDF）
- Agent 化演进（动态决策检索策略）
- 知识图谱增强（GraphRAG）

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
| 查询改写 | HyDE（Hypothetical Document Embeddings）、Query Expansion |
| 重排序 | Cohere Rerank、BGE-Reranker、FlagEmbedding |
| 递归检索 | 引用追溯，层层深入 |
| **GraphRAG** | 利用知识图谱增强检索质量，解决复杂关联问答 |
| **CRAG** | Corrective RAG，自动纠正检索结果质量 |

Native RAG 与 Agentic RAG 的区别在于：后者让 Agent 动态决定是否检索、检索范围和深度。

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
- BGE（BAAI）、M3E（Moka Massive Mixed Embedding，中文场景常用）、text-embedding-3（OpenAI）、Jina AI

**重排序：**
- Cohere Rerank、BGE-Reranker、FlagEmbedding

**托管服务：**
- Pinecone Serverless、Azure AI Search、Amazon Bedrock Knowledge Bases、Dify（低代码 RAG）

### 3.5 学习资源

- 论文：[Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)
- 概念：[The RAG Triad](https://www.trulens.org/getting_started/core_concepts/rag_triad/)（TruLens：上下文相关性、忠实度、答案相关性三指标评估 RAG 质量）
- 博客：[GraphRAG: Unlocking LLM discovery on narrative private data](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/)（Microsoft Research）
- 教程：LlamaIndex Documentation、LangChain RAG Tutorials
- 社区：r/LangChain、LlamaIndex Discord

---

## 四、多模态 AI（Multimodal AI）

### 4.1 技术简介

多模态 AI 指能够同时**理解和生成**多种模态信息（文本、图像、音频、视频、3D）的 AI 系统。

2025-2026 年，多模态成为大模型竞争最激烈的方向之一：

| 领域 | 代表进展 |
|------|----------|
| **图像理解** | GPT-5、Gemini 3、Claude Sonnet 4.5 原生支持图像理解 |
| **视频生成** | Sora 2（OpenAI）、可灵 Kling（快手）、Vidu（生数科技）、Runway Gen-4 |
| **语音交互** | GPT Realtime 实时语音对话、CosyVoice（中文 TTS） |
| **3D/具身** | 单目 3D 重建、RT-2、PaLM-E、OpenVLA、Gemini Robotics |

### 4.2 核心原理

| 概念 | 说明 |
|------|------|
| **原生多模态架构** | 单一模型同时处理文本/图像/音频/视频，统一 Token 空间（如 Chameleon、Emu3） |
| **视觉编码器** | SigLIP、CLIP、EVA-CLIP、DINOv2 将图像编码为与文本对齐的向量 |
| **LLM 作为多模态大脑** | 视觉 Token 经映射后与文本 Token 一同输入 LLM（LLaVA、MiniGPT-4） |
| **视频理解** | 时空建模（3D CNN、Video Transformer）、帧采样、帧间注意力 |
| **音频处理** | Whisper（语音识别）、CosyVoice（中文 TTS）、Fish Audio、ElevenLabs |
| **跨模态生成** | 文生图（SDXL、FLUX、GPT Image）、文生视频（Sora、Runway Gen-4、可灵） |
| **具身智能** | VLA 模型：RT-2、PaLM-E、OpenVLA、Gemini Robotics |

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
- GPT-5、Gemini 3、Claude Sonnet 4.5
- Qwen3-VL、Qwen2.5-VL、InternVL3、LLaVA、PaliGemma

**图像生成：**
- Midjourney V7、Stable Diffusion 3.5、FLUX、GPT Image（OpenAI）、Adobe Firefly

**视频生成：**
- Sora 2（OpenAI）、Runway Gen-4、可灵 Kling（快手）、Vidu（生数科技）、海螺 Hailuo（MiniMax）

**语音：**
- Whisper（STT）、CosyVoice（中文 TTS）、Fish Audio、ElevenLabs

**开发框架：**
- transformers（Hugging Face）、torchvision、LAVIS（Salesforce）

### 4.5 学习资源

- 论文：[LLaVA: Large Language and Vision Assistant](https://arxiv.org/abs/2304.08485)
- 页面：[GPT-4V(ision) System Card](https://openai.com/index/gpt-4v-system-card/)（OpenAI 官方安全性分析）
- 页面：[Sora](https://openai.com/index/sora-video-generation-model/)（OpenAI 官方介绍）
- 博客：[Vision Language Models Explained](https://huggingface.co/blog/vlms)（Hugging Face，视觉语言模型入门）
- 社区：r/LocalLLaMA（多模态讨论）、Hugging Face Multimodal 集合

---

## 五、AI Safety 与对齐

### 5.1 技术简介

AI Safety（AI 安全）与 Alignment（对齐）研究如何确保 AI 系统行为符合人类意图和价值观。

2026 年，AI Safety 从学术议题进入工程实践，成为模型部署时的关键评估维度。

### 5.2 核心概念

| 概念 | 说明 |
|------|------|
| **Constitutional AI** | Anthropic 提出的对齐方法，通过一组规则（Constitution）指导模型行为 |
| **RLHF** | 人类反馈强化学习对齐人类偏好（InstructGPT 核心方法） |
| **DPO / ORPO** | 直接优化人类偏好，绕过 Reward Model |
| **可解释性** | Mechanistic Interpretability，研究模型内部工作原理 |
| **对齐假象** | Alignment Faking，模型表面服从训练目标、实际按另一套逻辑运行（Anthropic 2024 年 12 月论文提出） |

### 5.3 实践方法

- **Prompt Injection 防护**：防止恶意指令注入
- **输出过滤**：防止生成有害内容
- **模型规范**：Anthropic Model Spec、Google Model Card
- **红队测试**：模拟攻击测试模型安全性
- **横向对比评测**：用同一套红队用例测试多个模型，比较安全表现

### 5.4 学习资源

- 论文：[Constitutional AI: Harmlessness from AI Feedback](https://arxiv.org/abs/2212.08073)
- 论文：[Learning to Summarize with Human Feedback](https://arxiv.org/abs/2009.01325)（RLHF 奠基）
- 论文：[Toy Models of Superposition](https://transformer-circuits.pub/2022/toy_model/index.html)（可解释性经典）
- 页面：[Anthropic Research](https://www.anthropic.com/research)（官方安全与对齐研究入口）
- 社区：Alignment Forum、LessWrong

---

## 六、学习路线建议

### 第一阶段｜基础

- 掌握 Python + 机器学习基础
- 理解 Transformer 架构原理
- 学会使用主流 API（OpenAI / Claude / Gemini / 本地模型）

验收标准：能不看资料画出 Self-Attention 的 QKV 计算流程，并用一条 API 请求跑通一个问答。

### 第二阶段｜进阶

- 学习 LangChain / LlamaIndex 开发
- 掌握向量数据库与 Embedding 技术
- 搭建完整 RAG pipeline

验收标准：能对着自定义文档库跑通一次带重排序的 RAG 问答，并说清改 chunk 粒度后会怎样影响命中率。

### 第三阶段｜Agent 开发

- 学习 ReAct / LangGraph 等 Agent 框架
- 理解 MCP 协议
- 实践 Tool Calling 与多步推理
- 探索 Multi-Agent 协作系统

验收标准：能让 Agent 通过工具调用完成一个需要两步以上子任务的例子，并能在中间环节注入错误观察让它纠正。

### 第四阶段｜多模态

- 理解 CLIP/视觉语言模型原理
- 实践图文/视频多模态应用开发
- 探索 Agentic AI 与具身智能

验收标准：能给一张图片补上文字描述并解释视觉编码器与 LLM 之间的对齐方式，或跑通一个图文问答示例。

### 第五阶段｜AI Safety（可选）

- 学习 Constitutional AI / RLHF / DPO 原理
- 了解可解释性研究方法
- 关注 AI Safety 最新论文和实践

验收标准：能区分 RLHF 与 DPO 的优化目标差异，并指出一次实践中的对齐风险（如奖励模型过拟合）。

---

## 七、常见问题 FAQ

### Q1：这篇文章适合完全没有 AI 基础的人吗？

不适合。本文假设读者已经有基本的编程能力和数学基础。如果你完全没有 AI 经验，建议先学习 Python 编程、线性代数、概率统计，再回头看本文。

### Q2：我应该先学 LLM、Agent，还是 RAG？

推荐顺序：LLM 是基础，RAG 是 LLM 的重要应用，Agent 是进阶使用方式，多模态是扩展方向。

### Q3：需要多少数学基础才能看懂 Transformer 原理？

需要线性代数（矩阵运算、向量空间）、概率统计（概率分布、期望）、优化理论（梯度下降）的基础。如果数学基础薄弱，可以先看[Jay Alammar 的可视化教程](https://jalammar.github.io/illustrated-transformer/)，再回头补数学。

### Q4：本地部署 LLM 需要多少资源？

本地部署的资源需求因模型参数量而异（以下为量化推理的经验值，具体以模型卡片为准）：
- 7B 级别小模型：8GB 内存可用，推荐 16GB
- 13B 级别：16GB 内存可用，推荐 32GB
- 70B 级别：至少 48GB 内存，推荐 64GB 以上或更激进的量化方案

使用 Ollama 或 llama.cpp 选择合适的量化等级，可以大幅降低资源需求。

### Q5：如何跟上 AI 技术的快速迭代？

1. 关注关键会议：NeurIPS、ICML、ICLR、ACL、CVPR
2. 订阅高质量 Newsletter：The Batch（Andrew Ng）、Deep Learning Weekly
3. 加入社区：Hugging Face、Reddit r/MachineLearning、Discord 服务器
4. 动手实践：每学一个新技术，立即用代码验证

---

## 八、练习

### 练习一：搭建本地 LLM 推理环境

1. 安装 Ollama 并下载一个小参数模型（如 Qwen3 8B）
2. 用 Python 调用 Ollama API 完成一个简单的问答任务
3. 对比相同任务下本地模型和云端 API（如 GPT-5 mini）的响应质量差异
4. 记录：响应速度、答案准确性、推理成本

完成标志：本地模型能稳定返回同一问题的上下文中合理答案，且你能给出它在响应质量与成本上当与不当的结论。

### 练习二：用 LlamaIndex 搭建个人知识库 RAG

1. 准备 5-10 篇技术文档（PDF 或 Markdown）
2. 用 LlamaIndex 建立向量索引
3. 设计一个或多组问答对，测试 RAG 系统的检索准确性
4. 尝试不同的 Chunking 策略（按句子、按段落、语义分块），对比检索效果
5. 记录：检索准确率、响应时间、Token 消耗

完成标志：对不在训练数据里的新文档，回答能引用到正确段落；换 chunk 粒度后你能解释命中率变化的原因。

### 练习三：用 LangGraph 写一个多步推理 Agent

1. 设计一个需要多步推理的任务（如"分析某个 GitHub 仓库的代码结构并生成文档"）
2. 用 LangGraph 构建 ReAct 循环：Thought → Action → Observation
3. 集成至少一个工具（如 GitHub API 或文件系统工具）
4. 测试 Agent 的任务完成能力和错误恢复能力
5. 记录：任务完成率、平均步数、失败原因分析

完成标志：Agent 能独立完成至少一轮 Thought → Action → Observation，并在工具返回异常时能修正下一步，而不是无限循环。

---

## 九、进阶路径

### 深入理解 LLM 内部工作机制

- 阅读 Transformer 原始论文和后续改进论文（PaLM、Llama、DeepSeek）
- 学习 Mechanistic Interpretability，理解模型内部如何表示知识
- 实践模型微调（用 Unsloth 或 LLaMA-Factory 微调一个小型模型）

### 掌握 Agent 工程化部署

- 学习 LangGraph 的高级特性（人工介入、状态持久化、多智能体协作）
- 理解 MCP 协议的完整规范，尝试开发一个自定义 MCP Server
- 实践 Agent 的评估与监控（用 AgentBench 或自定义评估框架）

### 探索多模态与具身智能

- 动手实践 LLaVA 或 Qwen3-VL，理解视觉语言模型的对齐方法
- 学习视频理解的基础模型（如 VideoMAE、TimeSformer）
- 关注具身智能的最新进展（RT-2、OpenVLA）

### 参与 AI Safety 社区

- 加入 Alignment Forum，跟踪最新的对齐研究
- 实践 Red Teaming，测试模型的安全边界
- 阅读 Anthropic 和 OpenAI 的 Safety 报告，理解工业界的安全实践

---

## 十、资料口径与参考来源

本文以 **2026 年 3 月 24 日**为资料截止口径整理，2026 年 9 月修订时逐条核对了模型名单与全部外链。关键判断的取径方式：

- **模型能力描述**：来自官方博客和论文，如 GPT-5 的发布信息来自 OpenAI 官方博客，DeepSeek R1 的 RLVR 训练路线来自 DeepSeek 团队发表的论文。
- **模型版本与发布时间**：以各家官方发布页为准；文中模型名单反映 2026 年 3 月时点的最新一代，不代表当前最新。
- **评测基准结果**：来自各模型的官方技术报告或独立评测（如 LMArena、Hugging Face Open LLM Leaderboard）。
- **工具推荐**：基于社区采用率，不构成商业推荐。
- **学习路线建议**：基于作者个人的学习路径和社区反馈整理，不同背景的读者可能需要调整顺序。
- **时效边界**：AI 领域发展极快，模型版本数字尤其容易过时；引用本文的模型名单时，建议先查对应厂商的官方页面确认现状。

各章节"学习资源"小节列出的论文、文档与博客即主要参考来源，涵盖 OpenAI、Anthropic、Google DeepMind、DeepSeek 的官方页面，Hugging Face、LangChain、LlamaIndex 的技术文档，以及 arXiv 学术论文，此处不再重复罗列。

---

## 自测题

完成以下自测题，评估你对本文核心概念的理解：

**问题 1**: 能解释 Transformer 的 Self-Attention 机制和 Next Token Prediction 训练目标吗？
<details>
<summary>查看答案</summary>
答：Self-Attention 机制让模型能够关注输入序列中的所有位置，计算每个位置对其他位置的注意力权重，从而捕捉长距离依赖关系。Next Token Prediction 是 LLM 的训练目标，通过预测下一个 token 来学习语言的统计规律。
</details>

**问题 2**: 能说出 ReAct 循环（Thought → Action → Observation）和 MCP 协议的作用吗？
<details>
<summary>查看答案</summary>
答：ReAct 循环让 Agent 能够交替进行推理（Thought）和行动（Action），并根据观察结果（Observation）调整下一步行动。MCP 协议是 Agent 工具调用的标准，定义了工具如何暴露给 LLM。
</details>

**问题 3**: 能列出 RAG 的完整流程（向量化 → 检索 → 重排序 → 生成）和常用工具吗？
<details>
<summary>查看答案</summary>
答：RAG 流程包括：1) 向量化：将文档和查询编码为向量；2) 检索：根据向量相似度检索相关文档；3) 重排序：对检索结果进行重新排序；4) 生成：将检索结果作为上下文，让 LLM 生成答案。常用工具：LlamaIndex、LangChain、Milvus、Pinecone。
</details>

**问题 4**: 能举例说明 2026 年图像理解、视频生成、语音交互的代表模型吗？
<details>
<summary>查看答案</summary>
答：图像理解：GPT-5、Gemini 3、Claude Sonnet 4.5；视频生成：Sora 2、Runway Gen-4、可灵 Kling；语音交互：GPT Realtime 实时语音、CosyVoice、Fish Audio。
</details>

**问题 5**: 能根据自己的背景制定合理的 AI 技术学习顺序吗？
<details>
<summary>查看答案</summary>
答：推荐顺序：1) 基础：Python + 机器学习基础 + Transformer 架构；2) 进阶：LangChain/LlamaIndex + 向量数据库 + RAG；3) Agent 开发：ReAct/LangGraph + MCP 协议；4) 多模态：CLIP + 图文/视频应用；5) AI Safety（可选）。
</details>

> **下一步**：从一个小项目开始实践（如用 LlamaIndex 搭建个人知识库 RAG，或用 LangGraph 写一个多步推理 Agent），比单纯阅读更有效。