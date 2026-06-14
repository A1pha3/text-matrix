---
title: "Cognee：16K Stars的AI Agent记忆引擎——让大模型拥有持续学习的知识图谱"
date: "2026-04-17T16:32:00+08:00"
slug: "cognee-ai-agent-memory-knowledge-engine"
description: "16,026 Stars的开源知识引擎。6行代码实现Agent记忆系统，结合向量搜索+知识图谱+认知科学，支持remember/recall/forget/improve四大操作，可部署至Modal/Railway/Fly.io等平台。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Agent", "记忆系统", "知识图谱", "向量搜索", "LLM", "Python", "RAG"]
---

# Cognee：16K Stars 的 AI Agent 记忆引擎

> **目标读者**：LLM 应用开发者、RAG 系统工程师、AI Agent 研究者、企业知识管理
> **前置知识**：Python 基础、LLM API 使用经验、对 RAG 有基本了解
> **技术栈**：Python 3.10-3.13 / 向量数据库 / 图数据库 / Pydantic
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解 AI Agent 记忆系统的必要性**：为何长期记忆对 Agent 至关重要
2. **掌握 Cognee 的核心架构**：向量搜索+知识图谱的双轨机制
3. **理解四大核心操作**：remember、recall、forget、improve
4. **掌握 Cognee 的部署方式**：本地部署 vs 云端托管
5. **能够集成 Cognee 到 AI Agent**：使用 Python SDK 实现持久记忆
6. **了解 Cognee 的研究基础**：知识图谱与 LLM 推理优化

---

## §2 背景与动机：为何 AI 需要记忆

### 2.1 当前 LLM 的局限性

| 问题 | 描述 | 影响 |
|------|------|------|
| **上下文窗口限制** | 无法记住所有历史对话 | Agent 无法积累经验 |
| **RAG 的痛点** | 检索质量参差不齐 | 回答准确率不稳定 |
| **知识孤岛** | 每个会话独立无关联 | 无法跨会话学习 |
| **幻觉问题** | 缺乏事实校验机制 | 回答不可靠 |

### 2.2 人类记忆的启示

人类记忆系统有多个层次：

```
工作记忆 ────→ 短期记忆 ────→ 长期记忆
  (当前)         (今日)        (永久)
     │              │              │
     ▼              ▼              ▼
  即时处理       重要信息       知识图谱
  快速遗忘       选择性保留     语义关联
```

**Cognee 的设计灵感**：模拟人类记忆的层次结构

### 2.3 Cognee 的核心定位

> **Cognee = Knowledge Engine for AI Agent Memory**

```
用户数据（任意格式）
      │
      ▼
┌─────────────────────────────────────────┐
│            Cognee Knowledge Engine       │
├─────────────────────────────────────────┤
│  向量搜索 ──→ 语义相似性检索              │
│  知识图谱 ──→ 关系网络推理               │
│  认知科学 ──→ 记忆巩固与遗忘             │
└─────────────────────────────────────────┘
      │
      ▼
  AI Agent可用的"记忆"
```

---

## §3 核心概念：四大操作

### 3.1 remember - 记忆存储

```python
import cognee
import asyncio

async def main():
    # 永久存储到知识图谱
    await cognee.remember(
        "Cognee turns documents into AI memory."
    )
    
    # 会话级快速缓存
    await cognee.remember(
        "User prefers detailed explanations.",
        session_id="chat_1"
    )

asyncio.run(main())
```

**两种存储模式**：

| 模式 | 存储位置 | 速度 | 持久性 |
|------|----------|------|--------|
| **永久存储** | 知识图谱 | 较慢 | 永久 |
| **会话缓存** | 内存 | 快速 | 随会话结束消失 |

### 3.2 recall - 记忆召回

```python
# 自动路由（智能选择最佳搜索策略）
results = await cognee.recall("What does Cognee do?")
for result in results:
    print(result)

# 指定会话优先
results = await cognee.recall(
    "What does the user prefer?",
    session_id="chat_1"  # 先查会话缓存，未命中再查图谱
)
```

**recall 的搜索策略**：

```python
async def recall(query, session_id=None):
    # 1. 如果有session_id，先查会话缓存
    if session_id:
        session_results = await search_session_cache(query, session_id)
        if session_results:
            return session_results
    
    # 2. 自动路由到最佳搜索策略
    search_strategy = await determine_strategy(query)  # 语义/关键词/混合
    return await search_knowledge_graph(query, strategy=search_strategy)
```

### 3.3 forget - 记忆遗忘

```python
# 删除指定数据集
await cognee.forget(dataset="main_dataset")

# 删除特定记忆
await cognee.forget(memory_id="memory_123")

# 按条件删除
await cognee.forget(
    predicate=lambda m: m.created_at < threshold_date
)
```

**为什么需要 forget？**
- 隐私合规（GDPR 等）
- 释放存储空间
- 去除过时信息
- 减少干扰噪声

### 3.4 improve - 记忆优化

```python
# 基于反馈优化记忆
await cognee.improve(
    memory_id="memory_456",
    feedback="This is incorrect, the correct answer is...",
    context={"correction_reason": "outdated_information"}
)
```

**improve 的机制**：
1. 分析反馈内容
2. 更新记忆向量
3. 调整图谱关系
4. 标记正确性权重

---

## §4 技术架构：双轨搜索系统

### 4.1 向量搜索轨

```python
class VectorSearchPipeline:
    """语义相似性搜索"""
    
    def __init__(self, embedding_model="text-embedding-3-small"):
        self.embedder = load_embedder(embedding_model)
        self.vector_store = load_vector_store()  # 支持多种后端
    
    async def add(self, text: str, metadata: dict):
        # 1. 文本向量化
        embedding = await self.embedder.embed(text)
        
        # 2. 存储到向量数据库
        await self.vector_store.insert(
            embedding=embedding,
            text=text,
            metadata=metadata,
        )
    
    async def search(self, query: str, top_k: int = 5):
        # 1. 查询向量化
        query_embedding = await self.embedder.embed(query)
        
        # 2. 相似性搜索
        results = await self.vector_store.search(
            embedding=query_embedding,
            top_k=top_k,
        )
        
        return results
```

### 4.2 知识图谱轨

```python
class KnowledgeGraphPipeline:
    """关系网络搜索"""
    
    def __init__(self, graph_db):
        self.graph = graph_db  # 支持Neo4j/NetworkX等
    
    async def add(self, text: str, metadata: dict):
        # 1. 实体抽取
        entities = await extract_entities(text)
        
        # 2. 关系抽取
        relations = await extract_relations(entities)
        
        # 3. 存入图数据库
        for entity in entities:
            await self.graph.upsert_node(entity)
        
        for relation in relations:
            await self.graph.upsert_edge(relation)
    
    async def search(self, query: str, top_k: int = 5):
        # 1. 查询解析
        query_entities = await extract_entities(query)
        
        # 2. 图遍历
        subgraph = await self.graph.traverse(
            start_nodes=query_entities,
            depth=3,
        )
        
        # 3. 返回相关节点
        return subgraph.nodes[:top_k]
```

### 4.3 双轨融合

```python
class HybridSearch:
    """向量搜索 + 知识图谱融合"""
    
    async def search(self, query: str, top_k: int = 5):
        # 并行执行两种搜索
        vector_results, graph_results = await asyncio.gather(
            self.vector_search.search(query, top_k * 2),
            self.knowledge_graph.search(query, top_k * 2),
        )
        
        # RRF融合算法
        fused = self.rrf_fusion(
            results_list=[vector_results, graph_results],
            k=60,  # RRF参数
        )
        
        return fused[:top_k]
    
    def rrf_fusion(self, results_list, k=60):
        """Reciprocal Rank Fusion"""
        scores = defaultdict(float)
        
        for results in results_list:
            for rank, item in enumerate(results):
                scores[item.id] += 1 / (k + rank + 1)
        
        return sorted(scores.items(), key=lambda x: -x[1])
```

---

## §5 认知科学原理

### 5.1 记忆巩固模型

Cognee 借鉴了认知科学的记忆巩固理论：

```
编码 ───→ 巩固 ───→ 提取
  │          │          │
  ▼          ▼          ▼
输入处理   睡眠期整合   线索触发
```

**Cognee 的实现**：
- **编码阶段**：实体+关系抽取
- **巩固阶段**：`improve`操作整合反馈
- **提取阶段**：多策略检索

### 5.2 重要性评估

```python
class MemoryImportanceScorer:
    """基于认知科学的重要性评估"""
    
    async def score(self, memory: Memory) -> float:
        factors = []
        
        # 新近性（Recency）
        factors.append(self.recency_factor(memory))
        
        # 情感强度（Emotional Intensity）
        factors.append(self.emotional_factor(memory))
        
        # 使用频率（Usage Frequency）
        factors.append(self.frequency_factor(memory))
        
        # 关联数量（Association Count）
        factors.append(self.association_factor(memory))
        
        # 加权平均
        return sum(f * w for f, w in zip(factors, WEIGHTS))
```

### 5.3 主动遗忘机制

```python
class CognitiveForgetting:
    """模拟人类主动遗忘"""
    
    # 基于重要性阈值的遗忘
    MINIMUM_IMPORTANCE = 0.3
    
    # 基于时间的衰减
    HALF_LIFE_DAYS = 30
    
    async def should_forget(self, memory: Memory) -> bool:
        if memory.importance < self.MINIMUM_IMPORTANCE:
            return True
        
        age = datetime.now() - memory.created_at
        decay = 0.5 ** (age.days / self.HALF_LIFE_DAYS)
        
        return memory.importance * decay < self.MINIMUM_IMPORTANCE
```

---

## §6 与 AI Agent 集成

### 6.1 OpenClaw 插件

```bash
# 安装
npm install @cognee/cognee-openclaw
```

```javascript
// openclaw配置
{
  "plugins": {
    "cognee": {
      "provider": "local",  // 或 "cloud"
      "cloudUrl": "https://your-instance.cognee.ai",
      "apiKey": "ck_..."
    }
  }
}
```

### 6.2 Claude Code 插件

```bash
# 安装cognee
pip install cognee

# 配置API Key
export LLM_API_KEY="your-openai-key"

# 克隆插件
git clone https://github.com/topoteretes/cognee-integrations.git

# 启用插件
claude --plugin-dir ./cognee-integrations/integrations/claude-code
```

**生命周期钩子**：
- `SessionStart`：初始化记忆
- `PostToolUse`：捕获工具调用
- `UserPromptSubmit`：注入相关上下文
- `PreCompact`：跨上下文保留记忆
- `SessionEnd`：桥接会话数据到永久图谱

### 6.3 Hermes Agent 集成

```yaml
# ~/.hermes/config.yaml
memory:
  provider: cognee
```

```bash
export LLM_API_KEY="your-openai-key"
hermes  # 会话感知+知识图谱持久化自动开启
```

---

## §7 部署方案

### 7.1 部署选项对比

| 平台 | 特点 | 适用场景 |
|------|------|----------|
| **Cognee Cloud** | 全托管、无基础设施 | 快速启动、生产环境 |
| **Modal** | 无服务器、自动扩缩容、GPU 支持 | 弹性 workloads |
| **Railway** | 最简 PaaS、原生 Postgres | 简单部署 |
| **Fly.io** | 边缘部署、持久卷 | 全球低延迟 |
| **Render** | 简单 PaaS、托管 Postgres | 简单部署 |
| **Daytona** | 云沙箱 | 开发/测试 |

### 7.2 本地部署

```bash
# 安装
uv pip install cognee

# 配置
export LLM_API_KEY="your-key"

# 启动本地UI
cognee-cli -ui
```

### 7.3 Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install cognee
CMD ["cognee-cli", "-ui"]
```

```bash
# 使用docker-compose
version: '3.8'
services:
  cognee:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
    volumes:
      - cognee_data:/data

volumes:
  cognee_data:
```

---

## §8 案例研究

### 8.1 案例 1：客服 Agent 记忆

```python
"""
场景：客服Agent记住用户历史交互
"""
async def customer_support_workflow():
    # 用户发起咨询
    user_message = "My invoice looks wrong"
    
    # 1. 召回相关记忆（历史交互、产品问题）
    relevant_memories = await cognee.recall(
        f"Customer invoice issues and resolutions for {user_id}"
    )
    
    # 2. 构建上下文
    context = {
        "current_issue": user_message,
        "history": relevant_memories,
        "product": get_product_info(user_id),
    }
    
    # 3. Agent生成回复
    response = await agent.generate(context)
    
    # 4. 记住这次交互
    await cognee.remember(
        f"Customer {user_id} asked about: {user_message}, Response: {response}",
        session_id=user_id,
    )
```

**效果**：Agent 能够记住用户历史问题，避免重复询问。

### 8.2 案例 2：专家知识蒸馏

```python
"""
场景：学习专家的SQL查询模式
"""
async def knowledge_distillation_workflow():
    # 1. 提取专家查询
    expert_queries = extract_expert_queries(expert_id)
    
    # 2. 记忆专家模式
    for query in expert_queries:
        await cognee.remember(
            f"Expert {expert_id} uses pattern: {query.pattern}",
            metadata={"schema": query.schema, "success_rate": query.success_rate}
        )
    
    # 3. 新手查询时检索相似模式
    novice_query = "How to calculate customer retention?"
    similar_patterns = await cognee.recall(
        f"SQL patterns for: {novice_query}",
        filter_fn=lambda m: m.metadata.get("schema") == target_schema
    )
    
    # 4. 适配到当前上下文
    adapted_pattern = adapt_pattern(similar_patterns[0], current_schema)
```

**效果**：新手分析师能复用专家级查询逻辑，性能接近专家水平。

---

## §9 研究论文

Cognee 团队发表了重要的研究论文：

```bibtex
@article{markovic2025optimizinginterfaceknowledgegraphs,
    title={Optimizing the Interface Between Knowledge Graphs and LLMs for Complex Reasoning},
    author={Vasilije Markovic and Lazar Obradovic and Laszlo Hajdu and Jovan Pavlovic},
    year={2025},
    eprint={2505.24478},
    archivePrefix={arXiv},
    primaryClass={cs.AI},
    url={https://arxiv.org/abs/2505.24478},
}
```

**核心贡献**：
- 知识图谱与 LLM 的接口优化
- 复杂推理任务的性能提升
- RAG 系统的知识图谱增强

---

## §10 CLI 工具

### 10.1 基本命令

```bash
# 记住信息
cognee-cli remember "Cognee is a knowledge engine."

# 召回记忆
cognee-cli recall "What is Cognee?"

# 遗忘所有
cognee-cli forget --all

# 启动UI
cognee-cli -ui
```

### 10.2 Python API 完整示例

```python
import os
import asyncio
import cognee

async def full_example():
    # 配置
    os.environ["LLM_API_KEY"] = "your-key"
    
    # 1. 存储记忆
    await cognee.remember(
        "Alice works in the engineering department."
    )
    await cognee.remember(
        "Alice prefers detailed technical explanations.",
        session_id="alice_session"
    )
    
    # 2. 召回记忆
    results = await cognee.recall(
        "Who is Alice and what does she prefer?"
    )
    print(f"Found {len(results)} relevant memories")
    
    # 3. 优化记忆
    await cognee.improve(
        memory_id=results[0].id,
        feedback="Alice actually prefers concise summaries."
    )
    
    # 4. 遗忘
    await cognee.forget(dataset="main_dataset")

asyncio.run(full_example())
```

---

## §11 FAQ

**Q1：Cognee 和其他 RAG 框架有什么区别？**
A：Cognee 不仅做向量检索，还结合知识图谱实现关系推理，并且内置记忆管理（remember/recall/forget/improve）而不仅仅是搜索。

**Q2：支持哪些向量数据库后端？**
A：支持 Qdrant、Milvus、Pinecone、Chroma 等主流向量数据库。

**Q3：需要多少 API 费用？**
A：主要费用是 LLM API 调用。Cognee Cloud 有免费额度，自托管需要自己的 LLM API Key。

**Q4：如何保证隐私安全？**
A：支持完全本地部署，数据不出本地。支持租户隔离、审计日志。

**Q5：可以处理多模态数据吗？**
A：是的，支持文档、音频、视频等多种格式的 ingestion。

---

## 相关资源

- **GitHub 仓库**：https://github.com/topoteretes/cognee
- **官方文档**：https://docs.cognee.ai/
- **在线 Demo**：https://colab.research.google.com/drive/12Vi9zID-M3fpKpKiaqDBvkk98ElkRPWy
- **研究论文**：https://arxiv.org/abs/2505.24478
- **Discord 社区**：https://discord.gg/NQPKmU5CCg
- **OpenClaw 插件**：https://www.npmjs.com/package/@cognee/cognee-openclaw
