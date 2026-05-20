---
title: "AI Engineering From Scratch：从零构建AI工程能力"
date: "2026-05-20T20:00:00+08:00"
slug: "ai-engineering-from-scratch-complete-guide"
description: "AI Engineering From Scratch是一个689页的免费AI工程教程，覆盖LLM基础、提示工程、RAG、Agent开发、微调部署等内容。开源3个月斩获8963 Stars，以Learn it. Build it. Ship it为理念。本文详解其内容结构、学习路径和快速上手。"
draft: false
categories: ["技术笔记"]
tags: ["AI工程", "LLM", "RAG", "Agent", "提示工程", "教程"]
---

## 项目概览

[AI Engineering From Scratch](https://github.com/rohitg00/ai-engineering-from-scratch)是一个从零开始学习AI工程的免费教程，由Rohit Gupta创建并维护。与其他教程不同，它不是简单罗列概念，而是**真正带着你动手构建**：从LLM基础到RAG实现，从提示工程到Agent开发，从模型微调到生产部署。

**核心数据：**
- GitHub Stars：8,963（3个月）
- 内容体量：689页
- 语言：Python
- 官网：https://aiengineeringfromscratch.com
- 开源协议：MIT

**为什么值得写：**
- 覆盖AI工程完整学习路径，理论与实践并重
- 免费、开源、持续更新
- 社区活跃，1859 forks验证了内容质量
- 适合想转入AI工程领域的开发者

---

## 内容结构

### 第一部分：LLM基础（~120页）

**Chapter 1-3：LLM入门**
- Transformer架构详解（Attention、Feed-Forward、Positional Encoding）
- GPT系列 vs BERT对比
- Tokenization原理与实践

**Chapter 4-6：提示工程**
- Zero-shot / Few-shot prompting
- Chain-of-Thought / Tree-of-Thought
- Prompt注入与安全基础

```python
# Few-shot example
messages = [
    {"role": "system", "content": "你是JSON转换助手"},
    {"role": "user", "content": "输入: 红色大象\n输出:"},
    {"role": "assistant", "content": '{"color": "红色", "size": "大"}'},
    {"role": "user", "content": "输入: 蓝色小猫\n输出:"},
]
```

### 第二部分：RAG与向量数据库（~180页）

**Chapter 7-9：RAG核心**
- 文档分块策略（recursive character、semantic）
- Embedding模型选择（OpenAI、BGE、M3E）
- 向量检索优化（HNSW、IVF）

**Chapter 10-12：高级RAG**
- 查询转换（query expansion、multi-query）
- 混合搜索（keyword + vector）
- Reranking与置信度排序

```python
# 简单RAG实现
def simple_rag(query: str, top_k: int = 5):
    # 1. 向量化查询
    query_embedding = embed_model.encode(query)
    # 2. 向量检索
    results = vector_db.search(query_embedding, top_k)
    # 3. 上下文组装
    context = "\n".join([r.content for r in results])
    # 4. 生成答案
    response = llm.invoke(f"Context: {context}\nQuestion: {query}")
    return response
```

### 第三部分：Agent开发（~200页）

**Chapter 13-15：Agent基础**
- ReAct范式（Reason + Act）
- Tool定义与调用
- 记忆系统设计

**Chapter 16-18：高级Agent**
- 多Agent协作（Planner + Executor）
- 自反思机制（self-reflection）
- Agent安全与护栏

```python
# 简单Agent实现
class SimpleAgent:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools
    
    def run(self, task: str):
        # ReAct loop
        thought = self.llm.invoke(f"Task: {task}\nThink:")
        action = self.llm.invoke(f"Thought: {thought}\nAction:")
        if action.startswith("tool:"):
            tool_name = action.split(":")[1]
            result = self.tools[tool_name].execute()
            return self.run(f"{task}\nResult: {result}")
        return action
```

### 第四部分：微调与部署（~189页）

**Chapter 19-21：模型微调**
- LoRA/QLoRA原理
- 分布式训练（DeepSpeed、FSDP）
- 微调数据准备与质量评估

**Chapter 22-24：生产部署**
- vLLM / TGI推理引擎
- 模型量化（GPTQ、AWQ）
- A/B测试与监控

---

## 学习路径建议

### 路线一：前端开发者转型AI

```
Week 1-2: LLM基础 + 提示工程
Week 3-4: RAG实现（用LangChain快速上手）
Week 5-6: Agent开发（从ReAct开始）
Week 7-8: 部署实战（vLLM + FastAPI）
```

### 路线二：数据科学家增强AI能力

```
Week 1-2: LLM API调用 + 提示工程
Week 3-4: 向量数据库 + RAG
Week 5-6: 微调基础（LoRA）
Week 7-8: 生产部署 + 监控
```

### 路线二：全栈开发者AI能力升级

```
Week 1-2: 理论（Transformer + LLM基础）
Week 3-4: RAG + 向量数据库实战
Week 5-6: Agent架构设计
Week 7-8: 微调 + 部署
```

---

## 快速开始

### 克隆仓库

```bash
git clone https://github.com/rohitg00/ai-engineering-from-scratch.git
cd ai-engineering-from-scratch
```

### 查看目录结构

```bash
ls -la
# 01-llm-foundations/
# 02-rag-vector-databases/
# 03-agents/
# 04-finetuning-deployment/
# resources/
```

### 按章节学习

```bash
# 打开第一章
open 01-llm-foundations/README.md

# 运行第一个示例
cd 01-llm-foundations/code/01_basic_prompting
python 01_simple_completion.py
```

---

## 与其他资源的对比

| 资源 | 特点 | 适合人群 |
|------|------|---------|
| 本项目 | 689页系统性教程，代码驱动 | 想系统学习的开发者 |
| Coursera LLMs | 学术导向，理论深入 | 研究人员 |
| LangChain文档 | API文档，快速上手 | 快速原型 |
| Fast.ai | 实践驱动，notebook优先 | 视觉导向学习者 |

---

## 社区与生态

- **GitHub Stars**：8,963（持续增长）
- **Forks**：1,859（说明内容被广泛参考）
- **Issues**：活跃（作者回应快）
- **Discord**：有官方社区

---

## 适用场景

- 想转入AI工程领域的软件开发者
- 有ML基础但缺LLM实践的数据科学家
- 需要系统化AI知识的全栈工程师
- 团队内部AI培训资料

---

## 总结

AI Engineering From Scratch提供了从零构建AI工程能力的完整路径。689页内容覆盖LLM基础、提示工程、RAG、Agent、微调和部署，理论与实践并重。

**核心价值：**
- 系统性学习路径，无需零散拼凑
- 代码驱动，每个概念都有可运行示例
- 免费开源，持续更新
- 社区活跃，1.8k forks验证内容质量

**参考链接：**
- GitHub：https://github.com/rohitg00/ai-engineering-from-scratch
- 官网：https://aiengineeringfromscratch.com