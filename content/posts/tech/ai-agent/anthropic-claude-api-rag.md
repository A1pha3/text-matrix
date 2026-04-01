---
title: "Claude API基础专题（四）：RAG检索增强生成系统"
date: 2026-03-25T13:00:00+08:00
slug: "claude-api-rag-retrieval-augmented-generation"
aliases:
  - /posts/tech/claude-api-rag-retrieval-augmented-generation/
description: "本文全面介绍了RAG（检索增强生成）系统的构建方法，涵盖文档分块、嵌入向量生成、向量数据库选择、语义搜索策略、重排序技术等关键环节，附带完整的Python代码实现示例。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "RAG", "向量数据库", "Python"]
---

# Claude API基础专题（四）：RAG检索增强生成系统 ⭐⭐⭐⭐

> **目标读者**：希望让Claude基于私有知识库回答问题的开发者
> **前置知识**：已完成第一篇《API基础》、第二篇《提示词工程》、第三篇《工具调用》
> **学习提醒**：RAG是生产级应用的核心技术，建议动手实践完整的RAG流程

---

## 章节导航

| 小节 | 主题 | 重要程度 |
|------|------|----------|
| 4.1 | RAG概述与核心概念 | ⭐⭐⭐⭐⭐ |
| 4.2 | RAG架构详解 | ⭐⭐⭐⭐⭐ |
| 4.3 | 文档分块策略 | ⭐⭐⭐⭐⭐ |
| 4.4 | 向量嵌入与检索 | ⭐⭐⭐⭐⭐ |
| 4.5 | Claude API中的RAG实现 | ⭐⭐⭐⭐ |
| 4.6 | RAG系统评估与优化 | ⭐⭐⭐⭐ |
| 4.7 | 常见问题与解决方案 | ⭐⭐⭐⭐ |

---

## 4.1 RAG概述与核心概念

### 什么是RAG

RAG（Retrieval-Augmented Generation，检索增强生成）是一种将信息检索与语言模型生成相结合的技术架构。它的核心思想是：在生成回答之前，先从外部知识库中检索相关信息，然后用这些信息增强模型的回答。

**为什么需要RAG？**

| 问题 | 传统LLM的局限 | RAG的解决方案 |
|------|-------------|---------------|
| 知识时效性 | 训练数据有截止日期 | 实时检索最新文档 |
| 知识覆盖度 | 无法涵盖所有领域知识 | 检索私有/专业知识库 |
| 幻觉问题 | 可能生成错误信息 | 基于真实检索内容回答 |
| 可解释性 | 不知道回答从何而来 | 答案可溯源到原文 |

### RAG的工作流程

```
用户提问
    ↓
问题编码 → 查询向量
    ↓
向量数据库检索 → 相关文档片段
    ↓
将检索结果注入提示词
    ↓
Claude生成回答
    ↓
返回附有来源的回答
```

### RAG vs 微调 vs 上下文学习

| 特性 | RAG | 微调（Fine-tuning） | 上下文学习（ICL） |
|------|-----|---------------------|------------------|
| 更新知识 | 快（更新文档） | 慢（重新训练） | 即时（放入提示词） |
| 成本 | 低（只需向量数据库） | 高（GPU训练） | 高（Token消耗大） |
| 适用场景 | 知识库问答 | 风格/领域适应 | 单次特定任务 |
| 实时性 | ✅ 实时 | ❌ 需要训练 | ✅ 实时 |

---

## 4.2 RAG架构详解

### 完整RAG系统架构

一个完整的RAG系统包含以下组件：

```python
# RAG系统组件
class RAGSystem:
    def __init__(self):
        self.document_processor = DocumentProcessor()   # 文档处理
        self.chunker = ChunkingStrategy()              # 分块策略
        self.embedder = EmbeddingModel()                # 嵌入模型
        self.vector_store = VectorDatabase()            # 向量数据库
        self.retriever = RetrievalEngine()             # 检索引擎
        self.generator = ClaudeGenerator()             # 生成模型
    
    def add_documents(self, documents):
        """添加文档到知识库"""
        # 1. 文档处理
        processed = self.document_processor.process(documents)
        
        # 2. 文档分块
        chunks = self.chunker.chunk(processed)
        
        # 3. 生成嵌入
        embeddings = self.embedder.embed(chunks)
        
        # 4. 存储到向量数据库
        self.vector_store.add(embeddings, chunks)
    
    def query(self, question):
        """问答流程"""
        # 1. 将问题转为向量
        query_embedding = self.embedder.embed([question])
        
        # 2. 检索相关文档
        relevant_chunks = self.vector_store.search(query_embedding, top_k=5)
        
        # 3. 构建提示词
        prompt = self.build_prompt(question, relevant_chunks)
        
        # 4. 生成回答
        response = self.generator.generate(prompt)
        
        return response
```

### 核心组件详解

**1. 文档处理器（Document Processor）**

负责将各种格式的文档转换为可处理的文本：

```python
from abc import ABC, abstractmethod
import re

class DocumentProcessor:
    """文档处理器基类"""
    
    def process(self, content: str, source: str = None) -> dict:
        """处理文档，返回结构化内容"""
        return {
            "content": self.clean_text(content),
            "source": source,
            "metadata": self.extract_metadata(content, source)
        }
    
    def clean_text(self, text: str) -> str:
        """清洗文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符（保留中文、英文、数字、常用标点）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s.,!?;:\'\"-]', '', text)
        return text.strip()
    
    @abstractmethod
    def extract_metadata(self, content: str, source: str) -> dict:
        """提取元数据，子类实现"""
        pass

class PDFProcessor(DocumentProcessor):
    """PDF文档处理器"""
    
    def extract_metadata(self, content: str, source: str) -> dict:
        return {
            "source": source,
            "type": "pdf",
            "char_count": len(content)
        }

class MarkdownProcessor(DocumentProcessor):
    """Markdown文档处理器"""
    
    def extract_metadata(self, content: str, source: str) -> dict:
        # 提取标题
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else "Untitled"
        
        return {
            "source": source,
            "type": "markdown",
            "title": title,
            "char_count": len(content)
        }
```

---

## 4.3 文档分块策略

### 分块的重要性

分块（Chunking）是RAG中最关键的步骤之一。好的分块策略能显著提升检索效果。

**分块太大**：引入过多无关上下文，检索精度下降
**分块太小**：丢失上下文，模型无法理解完整语义

### 常用分块策略

```python
from typing import List, Callable
import re

class ChunkingStrategy(ABC):
    """分块策略基类"""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size  # 每块的目标大小（字符或词）
        self.overlap = overlap         # 相邻块之间的重叠大小
    
    @abstractmethod
    def chunk(self, documents: List[dict]) -> List[dict]:
        """执行分块"""
        pass
    
    def create_chunk(self, text: str, metadata: dict, chunk_id: int) -> dict:
        """创建块对象"""
        return {
            "id": f"chunk_{chunk_id}",
            "content": text,
            "metadata": metadata,
            "char_count": len(text)
        }

class FixedSizeChunker(ChunkingStrategy):
    """固定大小分块（字符级）"""
    
    def chunk(self, documents: List[dict]) -> List[dict]:
        chunks = []
        chunk_id = 0
        
        for doc in documents:
            text = doc["content"]
            metadata = doc.get("metadata", {})
            metadata["source"] = doc.get("source")
            
            # 按固定大小分割
            start = 0
            while start < len(text):
                end = start + self.chunk_size
                chunk_text = text[start:end]
                
                # 如果不是最后一块，尝试在句号或换行处断开
                if end < len(text):
                    chunk_text = self._split_at_sentence_boundary(chunk_text)
                
                chunks.append(self.create_chunk(chunk_text, metadata, chunk_id))
                chunk_id += 1
                
                # 滑动窗口移动（考虑重叠）
                start = start + self.chunk_size - self.overlap
        
        return chunks
    
    def _split_at_sentence_boundary(self, text: str) -> str:
        """在句子边界处断开"""
        # 查找最后一个句号、问号、感叹号或换行
        pattern = r'([.!?。！？])\s+'
        matches = list(re.finditer(pattern, text))
        
        if matches:
            last_match = matches[-1]
            return text[:last_match.end()]
        return text

class RecursiveChunker(ChunkingStrategy):
    """递归分块（按层级结构）"""
    
    def chunk(self, documents: List[dict]) -> List[dict]:
        chunks = []
        chunk_id = 0
        
        for doc in documents:
            text = doc["content"]
            metadata = doc.get("metadata", {})
            
            # 先按段落分割
            paragraphs = self._split_by_paragraph(text)
            
            current_chunk = ""
            for para in paragraphs:
                # 如果加上这个段落会超过大小限制，先保存当前块
                if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                    chunks.append(self.create_chunk(current_chunk.strip(), metadata, chunk_id))
                    chunk_id += 1
                    # 重叠：保留上一段的结尾
                    current_chunk = current_chunk[-self.overlap:] if self.overlap > 0 else ""
                
                current_chunk += para + "\n\n"
            
            # 处理最后一块
            if current_chunk.strip():
                chunks.append(self.create_chunk(current_chunk.strip(), metadata, chunk_id))
        
        return chunks
    
    def _split_by_paragraph(self, text: str) -> List[str]:
        """按段落分割"""
        # 先按双重换行分割
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

class SemanticChunker(ChunkingStrategy):
    """语义分块（基于主题变化）"""
    
    def __init__(self, embedder, threshold: float = 0.7, **kwargs):
        super().__init__(**kwargs)
        self.embedder = embedder
        self.threshold = threshold  # 语义相似度阈值
    
    def chunk(self, documents: List[dict]) -> List[dict]:
        """基于语义相似度自动分块"""
        chunks = []
        chunk_id = 0
        
        for doc in documents:
            sentences = self._split_into_sentences(doc["content"])
            metadata = doc.get("metadata", {})
            
            current_group = [sentences[0]] if sentences else []
            
            for i in range(1, len(sentences)):
                # 计算当前句与前一句的语义相似度
                similarity = self._compute_similarity(
                    sentences[i-1], sentences[i]
                )
                
                # 如果相似度低于阈值，创建新块
                if similarity < self.threshold:
                    chunk_text = " ".join(current_group)
                    if len(chunk_text) > 50:  # 忽略过短的块
                        chunks.append(self.create_chunk(chunk_text, metadata, chunk_id))
                        chunk_id += 1
                    current_group = []
                
                current_group.append(sentences[i])
            
            # 处理最后一组
            if current_group:
                chunk_text = " ".join(current_group)
                if len(chunk_text) > 50:
                    chunks.append(self.create_chunk(chunk_text, metadata, chunk_id))
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """将文本分割为句子"""
        pattern = r'([.!?。！？]\s+)'
        parts = re.split(pattern, text)
        sentences = []
        for i in range(0, len(parts)-1, 2):
            sentences.append(parts[i] + parts[i+1])
        if len(parts) % 2 == 1 and parts[-1].strip():
            sentences.append(parts[-1])
        return sentences
    
    def _compute_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的语义相似度"""
        emb1 = self.embedder.embed([text1])[0]
        emb2 = self.embedder.embed([text2])[0]
        return self._cosine_similarity(emb1, emb2)
    
    def _cosine_similarity(self, v1: list, v2: list) -> float:
        """余弦相似度"""
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        return dot_product / (norm1 * norm2 + 1e-8)
```

### 分块策略对比

| 策略 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 固定大小 | 简单、均匀 | 可能切断句子 | 通用场景 |
| 递归分块 | 保留段落结构 | 计算开销 | 长文档 |
| 语义分块 | 主题一致性好 | 需要嵌入模型 | 高质量需求 |
| 文档结构感知 | 完美保留结构 | 需要解析文档格式 | Markdown/HTML |

---

## 4.4 向量嵌入与检索

### 嵌入模型选择

```python
class EmbeddingModel:
    """嵌入模型封装"""
    
    # 常用嵌入模型对比
    MODELS = {
        "text-embedding-ada-002": {
            "provider": "OpenAI",
            "dimensions": 1536,
            "max_tokens": 8191,
            "cost_per_1k": 0.0001
        },
        "text-embedding-3-small": {
            "provider": "OpenAI",
            "dimensions": 1536,
            "max_tokens": 8191,
            "cost_per_1k": 0.00002
        },
        "claude-embeddings": {
            "provider": "Anthropic",
            "dimensions": 1536,
            "max_tokens": 2048,
            "cost_per_1k": 0.00008
        },
        "bge-large-zh": {
            "provider": "BAAI",
            "dimensions": 1024,
            "max_tokens": 512,
            "cost_per_1k": 0  # 开源模型
        }
    }
    
    def __init__(self, model_name: str = "text-embedding-ada-002"):
        self.model_name = model_name
        self.config = self.MODELS.get(model_name, self.MODELS["text-embedding-ada-002"])
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """生成嵌入向量"""
        if self.model_name.startswith("text-embedding"):
            return self._openai_embed(texts)
        elif self.model_name == "claude-embeddings":
            return self._anthropic_embed(texts)
        else:
            return self._custom_embed(texts)
    
    def _openai_embed(self, texts: List[str]) -> List[List[float]]:
        """使用OpenAI API生成嵌入"""
        import openai
        
        response = openai.Embedding.create(
            model=self.model_name,
            input=texts
        )
        return [item["embedding"] for item in response["data"]]
```

### 向量数据库

```python
from abc import ABC, abstractmethod
import json

class VectorDatabase(ABC):
    """向量数据库抽象接口"""
    
    @abstractmethod
    def add(self, embeddings: List[List[float]], documents: List[dict]):
        """添加向量和文档"""
        pass
    
    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[dict]:
        """检索最相似的文档"""
        pass

class SimpleVectorDB(VectorDatabase):
    """简单内存向量数据库（适合小规模场景）"""
    
    def __init__(self):
        self.vectors = []
        self.documents = []
    
    def add(self, embeddings: List[List[float]], documents: List[dict]):
        self.vectors.extend(embeddings)
        self.documents.extend(documents)
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[dict]:
        """计算余弦相似度并返回top_k结果"""
        scores = []
        for i, vec in enumerate(self.vectors):
            similarity = self._cosine_similarity(query_embedding, vec)
            scores.append((i, similarity))
        
        # 按相似度降序排列
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # 返回top_k结果
        results = []
        for idx, score in scores[:top_k]:
            result = self.documents[idx].copy()
            result["score"] = score
            results.append(result)
        
        return results
    
    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        return dot_product / (norm1 * norm2 + 1e-8)

class ChromaDB(VectorDatabase):
    """Chroma向量数据库（开源、生产可用）"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        import chromadb
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection("documents")
    
    def add(self, embeddings: List[List[float]], documents: List[dict]):
        ids = [doc["id"] for doc in documents]
        contents = [doc["content"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas
        )
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[dict]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # 格式化返回结果
        formatted = []
        for i in range(len(results["ids"][0])):
            formatted.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i]  # Chroma用L2距离，转为相似度
            })
        
        return formatted

class PineconeDB(VectorDatabase):
    """Pinecone云向量数据库"""
    
    def __init__(self, api_key: str, environment: str, index_name: str):
        from pinecone import Pinecone
        
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.index = self.pc.Index(index_name)
    
    def add(self, embeddings: List[List[float]], documents: List[dict]):
        vectors = []
        for i, (embedding, doc) in enumerate(zip(embeddings, documents)):
            vectors.append({
                "id": doc["id"],
                "values": embedding,
                "metadata": {
                    "content": doc["content"],
                    **doc.get("metadata", {})
                }
            })
        
        self.index.upsert(vectors=vectors)
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[dict]:
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        return [{
            "id": match["id"],
            "content": match["metadata"]["content"],
            "metadata": {k: v for k, v in match["metadata"].items() if k != "content"},
            "score": match["score"]
        } for match in results["matches"]]
```

### 检索策略

```python
class RetrievalEngine:
    """检索引擎"""
    
    def __init__(self, vector_db: VectorDatabase, embedder: EmbeddingModel):
        self.vector_db = vector_db
        self.embedder = embedder
    
    def retrieve(self, query: str, top_k: int = 5, 
                 min_score: float = 0.0) -> List[dict]:
        """基础检索"""
        # 1. 将查询转为嵌入向量
        query_embedding = self.embedder.embed([query])[0]
        
        # 2. 向量相似度检索
        results = self.vector_db.search(query_embedding, top_k)
        
        # 3. 过滤低分结果
        return [r for r in results if r["score"] >= min_score]

class HybridRetrieval(RetrievalEngine):
    """混合检索（向量 + 关键词）"""
    
    def __init__(self, vector_db: VectorDatabase, 
                 embedder: EmbeddingModel, bm25_weight: float = 0.3):
        super().__init__(vector_db, embedder)
        self.bm25_weight = bm25_weight
    
    def retrieve(self, query: str, top_k: int = 5) -> List[dict]:
        """混合检索"""
        # 向量检索
        vector_results = super().retrieve(query, top_k * 2)
        
        # 关键词检索（简化版BM25）
        keyword_results = self._bm25_search(query, top_k * 2)
        
        # 合并结果
        combined = self._merge_results(vector_results, keyword_results, top_k)
        
        return combined
    
    def _bm25_search(self, query: str, top_k: int) -> List[dict]:
        """简化的BM25关键词检索"""
        # 这里使用简化版本，实际生产环境可以用 rank_bm25 库
        query_terms = query.lower().split()
        all_docs = self.vector_db.documents
        
        scores = []
        for doc in all_docs:
            doc_terms = doc["content"].lower().split()
            # 计算词重叠数
            overlap = len(set(query_terms) & set(doc_terms))
            score = overlap / (len(doc_terms) + 1)
            scores.append(score)
        
        # 排序返回top_k
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [all_docs[i] for i, _ in indexed_scores[:top_k]]
    
    def _merge_results(self, vector_results: List[dict], 
                      keyword_results: List[dict], top_k: int) -> List[dict]:
        """合并向量检索和关键词检索结果"""
        # 为每个结果计算综合分数
        seen_ids = set()
        merged = []
        
        for v_result, k_result in zip(vector_results, keyword_results):
            # 向量分数（权重更高）
            if v_result["id"] not in seen_ids:
                v_result["final_score"] = v_result["score"] * (1 - self.bm25_weight)
                merged.append(v_result)
                seen_ids.add(v_result["id"])
            
            # 关键词分数
            if k_result["id"] not in seen_ids:
                k_result["final_score"] = self.bm25_weight * min(k_result.get("score", 0) * 10, 1.0)
                merged.append(k_result)
                seen_ids.add(k_result["id"])
        
        # 按综合分数排序
        merged.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        return merged[:top_k]
```

---

## 4.5 Claude API中的RAG实现

### 构建RAG提示词

```python
def build_rag_prompt(question: str, context_docs: List[dict]) -> str:
    """构建带检索上下文的提示词"""
    
    # 构建上下文字符串
    context_parts = []
    for i, doc in enumerate(context_docs, 1):
        source = doc.get("metadata", {}).get("source", "Unknown")
        content = doc["content"]
        context_parts.append(f"[文档{i}]（来源：{source}）\n{content}")
    
    context_str = "\n\n".join(context_parts)
    
    prompt = f"""你是一个助手，基于提供的文档内容回答用户问题。

## 检索到的上下文信息
---
{context_str}
---

## 用户问题
{question}

## 回答要求
1. 只根据提供的上下文信息回答，不要编造信息
2. 如果上下文中没有相关信息，明确告知用户"我没有找到相关信息"
3. 在回答中引用相关文档来源
4. 回答要准确、完整、简洁

## 回答
"""
    return prompt

# 使用示例
context_docs = [
    {"content": "Claude API支持多种编程语言，包括Python、JavaScript、Go等。", 
     "metadata": {"source": "API文档"}},
    {"content": "Python SDK的安装命令是：pip install anthropic", 
     "metadata": {"source": "安装指南"}}
]

prompt = build_rag_prompt("Claude API支持哪些编程语言？", context_docs)
print(prompt)
```

### 完整RAG问答流程

```python
from anthropic import Anthropic
import os

class ClaudeRAG:
    """基于Claude API的RAG系统"""
    
    def __init__(self, vector_db: VectorDatabase, embedder: EmbeddingModel):
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.retriever = RetrievalEngine(vector_db, embedder)
    
    def query(self, question: str, top_k: int = 5, 
              model: str = "claude-sonnet-4-20250514") -> dict:
        """执行RAG问答"""
        
        # 1. 检索相关文档
        retrieved_docs = self.retriever.retrieve(question, top_k)
        
        if not retrieved_docs:
            return {
                "answer": "我没有找到与您问题相关的文档信息。",
                "sources": [],
                "has_answer": False
            }
        
        # 2. 构建提示词
        prompt = build_rag_prompt(question, retrieved_docs)
        
        # 3. 调用Claude生成回答
        response = self.client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # 4. 提取回答和来源
        answer = response.content[0].text
        sources = [doc.get("metadata", {}).get("source", "Unknown") 
                   for doc in retrieved_docs]
        
        return {
            "answer": answer,
            "sources": list(set(sources)),  # 去重
            "has_answer": True,
            "num_docs_retrieved": len(retrieved_docs)
        }

# 使用示例
def main():
    # 初始化组件
    embedder = EmbeddingModel("text-embedding-ada-002")
    vector_db = ChromaDB(persist_directory="./my_vector_db")
    rag = ClaudeRAG(vector_db, embedder)
    
    # 问答
    question = "Claude API的速率限制是多少？"
    result = rag.query(question)
    
    print(f"问题：{question}")
    print(f"回答：{result['answer']}")
    print(f"参考来源：{', '.join(result['sources'])}")

if __name__ == "__main__":
    main()
```

### 高级RAG技术

```python
class AdvancedRAG:
    """高级RAG技术"""
    
    def __init__(self, vector_db: VectorDatabase, embedder: EmbeddingModel):
        self.vector_db = vector_db
        self.embedder = embedder
    
    def query_with_reranking(self, question: str, top_k: int = 10, 
                            rerank_top_k: int = 5) -> dict:
        """重排序RAG（先检索更多，再重排序精选）"""
        # 1. 初步检索（多取一些）
        initial_results = self._vector_search(question, top_k * 2)
        
        # 2. 使用Claude做重排序（可选）
        reranked = self._claude_rerank(question, initial_results, rerank_top_k)
        
        return reranked
    
    def _claude_rerank(self, question: str, documents: List[dict], 
                       top_k: int) -> List[dict]:
        """使用Claude对检索结果进行重排序"""
        prompt = f"""请根据以下文档与问题的相关性进行排序。
        
问题：{question}

文档列表：
{chr(10).join([f"[{i+1}] {doc['content']}" for i, doc in enumerate(documents)])}

请按相关性从高到低输出文档编号，用逗号分隔，例如：3,1,2
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # 解析响应得到排序
        ranking_text = response.content[0].text.strip()
        # 提取数字
        import re
        numbers = re.findall(r'\d+', ranking_text)
        
        # 按响应顺序返回
        reranked = []
        for num_str in numbers[:top_k]:
            idx = int(num_str) - 1
            if 0 <= idx < len(documents):
                reranked.append(documents[idx])
        
        # 补充未在响应中的文档
        for doc in documents:
            if doc not in reranked:
                reranked.append(doc)
        
        return reranked[:top_k]
    
    def query_with_query_expansion(self, question: str) -> dict:
        """查询扩展RAG（用Claude生成多个相关查询）"""
        # 1. 使用Claude生成多个相关查询
        expanded_queries = self._generate_related_queries(question)
        
        # 2. 并行检索所有查询
        all_results = []
        for query in expanded_queries:
            results = self._vector_search(query, top_k=5)
            all_results.extend(results)
        
        # 3. 去重（基于文档ID）
        seen_ids = set()
        unique_results = []
        for doc in all_results:
            if doc["id"] not in seen_ids:
                unique_results.append(doc)
                seen_ids.add(doc["id"])
        
        # 4. 按分数排序
        unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return unique_results[:5]
    
    def _generate_related_queries(self, question: str) -> List[str]:
        """使用Claude生成相关查询"""
        prompt = f"""请为以下问题生成3个不同的表达方式，这些表达方式应该：
1. 保持原问题的核心意图
2. 使用不同的词汇或句式
3. 涵盖问题的不同方面

原问题：{question}

请输出3个独立的查询，每行一个：
"""
        
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        queries = response.content[0].text.strip().split('\n')
        return [q.strip() for q in queries if q.strip()] + [question]
```

---

## 4.6 RAG系统评估与优化

### 评估指标

```python
class RAGEvaluator:
    """RAG系统评估器"""
    
    def evaluate(self, rag_system, eval_dataset: List[dict]) -> dict:
        """
        评估RAG系统
        
        eval_dataset格式：
        {
            "question": "问题",
            "ground_truth": "标准答案",
            "context": ["相关文档1", "相关文档2"]
        }
        """
        results = {
            "retrieval_precision": [],
            "retrieval_recall": [],
            "answer_accuracy": [],
            "faithfulness": []  # 回答对上下文的忠诚度
        }
        
        for item in eval_dataset:
            question = item["question"]
            ground_truth = item["ground_truth"]
            
            # 执行RAG
            rag_result = rag_system.query(question)
            
            # 计算检索指标
            retrieved_contexts = rag_result.get("retrieved_docs", [])
            precision, recall = self._calc_retrieval_metrics(
                retrieved_contexts, item["context"]
            )
            results["retrieval_precision"].append(precision)
            results["retrieval_recall"].append(recall)
            
            # 计算回答质量（可以用LLM评估或人工评估）
            # 这里用简化的文本相似度
            answer_similarity = self._text_similarity(
                rag_result["answer"], ground_truth
            )
            results["answer_accuracy"].append(answer_similarity)
        
        # 汇总结果
        return {
            "avg_retrieval_precision": sum(results["retrieval_precision"]) / len(results["retrieval_precision"]),
            "avg_retrieval_recall": sum(results["retrieval_recall"]) / len(results["retrieval_recall"]),
            "avg_answer_accuracy": sum(results["answer_accuracy"]) / len(results["answer_accuracy"])
        }
    
    def _calc_retrieval_metrics(self, retrieved: List[str], 
                                relevant: List[str], k: int = None) -> tuple:
        """计算检索的精确率和召回率"""
        retrieved_set = set(retrieved[:k] if k else retrieved)
        relevant_set = set(relevant)
        
        # 精确率 = |检索到的相关文档| / |检索到的文档总数|
        precision = len(retrieved_set & relevant_set) / len(retrieved_set) if retrieved_set else 0
        
        # 召回率 = |检索到的相关文档| / |所有相关文档|
        recall = len(retrieved_set & relevant_set) / len(relevant_set) if relevant_set else 0
        
        return precision, recall
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度（简化版）"""
        # 使用词重叠
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
```

### 常见优化策略

```python
# 1. 查询改写优化
def optimize_query(query: str) -> str:
    """优化用户查询"""
    # 可以使用Claude来改写查询
    prompt = f"""请优化以下搜索查询，使其更加清晰、具体。

原查询：{query}

优化后的查询：
"""
    # 调用Claude处理...
    return optimized_query

# 2. 检索参数调优
retrieval_configs = {
    "top_k": [3, 5, 7, 10],  # 测试不同的top_k
    "min_score_threshold": [0.5, 0.6, 0.7, 0.8],  # 测试不同的阈值
    "chunk_size": [256, 512, 1024],  # 测试不同的分块大小
    "overlap": [0, 25, 50, 100]  # 测试不同的重叠大小
}

# 3. 混合检索权重调优
hybrid_configs = {
    "bm25_weight": [0.1, 0.
hybrid_configs = {
    "bm25_weight": [0.1, 0.2, 0.3, 0.4],  # 关键词检索权重
    "vector_weight": [0.6, 0.7, 0.8, 0.9]  # 向量检索权重
}

# 4. 嵌入模型选择
embedding_models = {
    "openai": {
        "ada-002": {"dimensions": 1536, "cost": "低", "quality": "中"},
        "text-embedding-3-small": {"dimensions": 1536, "cost": "很低", "quality": "中高"},
        "text-embedding-3-large": {"dimensions": 3072, "cost": "中", "quality": "高"}
    },
    "open-source": {
        "bge-large-zh": {"dimensions": 1024, "cost": "免费", "quality": "高（中文）"},
        "m3e": {"dimensions": 1024, "cost": "免费", "quality": "中"}
    }
}
```

### 生产环境建议

| 场景 | 推荐方案 | 说明 |
|------|----------|------|
| 小规模（<1万文档） | ChromaDB + ADA-002 | 简单、免费 |
| 中等规模（10万-100万） | Pinecone + text-embedding-3 | 可扩展、成本适中 |
| 大规模（>100万） | Weaviate/Qdrant + bge-large | 高性能、开源 |
| 高隐私需求 | Milvus + 开源嵌入模型 | 数据不出境 |

---

## 4.7 常见问题与解决方案

### FAQ

**Q1：检索不到相关文档怎么办？**

```python
# 解决方案1：降低相似度阈值
results = retriever.retrieve(question, top_k=10, min_score=0.3)

# 解决方案2：使用查询扩展
expanded_queries = generate_related_queries(question)
all_results = parallel_retrieve(expanded_queries)

# 解决方案3：混合关键词检索
hybrid_results = hybrid_retriever.retrieve(question)
```

**Q2：回答中出现幻觉怎么办？**

```python
# 在提示词中加强约束
prompt = """你是一个助手，基于提供的文档内容回答用户问题。

重要约束：
1. 只根据提供的上下文回答，不要编造信息
2. 如果上下文中没有相关信息，明确说"我没有找到相关信息"
3. 回答时必须引用相关文档来源

上下文：
{context}

问题：{question}
"""
```

**Q3：检索结果重复怎么办？**

```python
# 去重策略
def deduplicate_results(results: List[dict], threshold: float = 0.95) -> List[dict]:
    """基于相似度去重"""
    unique = []
    for doc in results:
        is_duplicate = False
        for unique_doc in unique:
            if compute_similarity(doc["content"], unique_doc["content"]) > threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            unique.append(doc)
    return unique
```

**Q4：文档更新后向量数据库如何同步？**

```python
class VectorDBSync:
    """向量数据库同步"""
    
    def __init__(self, vector_db, embedder):
        self.vector_db = vector_db
        self.embedder = embedder
    
    def update_document(self, doc_id: str, new_content: str):
        """更新单个文档"""
        # 1. 删除旧向量
        self.vector_db.delete(doc_id)
        
        # 2. 嵌入新内容
        new_embedding = self.embedder.embed([new_content])[0]
        
        # 3. 添加新向量
        self.vector_db.add([new_embedding], [{"id": doc_id, "content": new_content}])
    
    def full_reindex(self, documents: List[dict]):
        """全量重索引"""
        # 1. 清空数据库
        self.vector_db.clear()
        
        # 2. 重新嵌入所有文档
        chunks = self.chunker.chunk(documents)
        embeddings = self.embedder.embed([c["content"] for c in chunks])
        
        # 3. 重新存储
        self.vector_db.add(embeddings, chunks)
```

**Q5：如何处理中文文档的分词？**

```python
import jieba

class ChineseTextProcessor:
    """中文文本处理器"""
    
    def __init__(self):
        jieba.setLogLevel(jieba.logging.INFO)
    
    def tokenize(self, text: str) -> List[str]:
        """中文分词"""
        return list(jieba.cut(text))
    
    def add_custom_words(self, words: List[str]):
        """添加自定义词典（用于专业术语）"""
        for word in words:
            jieba.add_word(word)
    
    def extract_keywords(self, text: str, top_k: int = 5) -> List[str]:
        """提取关键词"""
        import jieba.analyse
        return jieba.analyse.extract_tags(text, topK=top_k)
```

---

## 本章总结

### 核心知识点

| 知识点 | 掌握程度 | 关键点 |
|--------|----------|--------|
| RAG概述 | ⭐⭐⭐⭐⭐ | 工作流程、vs微调、vs上下文学习 |
| RAG架构 | ⭐⭐⭐⭐⭐ | 文档处理、分块、嵌入、检索、生成 |
| 分块策略 | ⭐⭐⭐⭐⭐ | 固定大小、递归、语义分块 |
| 向量检索 | ⭐⭐⭐⭐⭐ | 嵌入模型、向量数据库、相似度计算 |
| RAG实现 | ⭐⭐⭐⭐ | 提示词构建、完整流程 |
| 评估优化 | ⭐⭐⭐⭐ | 精确率、召回率、重排序、查询扩展 |

### 关键代码模板

| 功能 | 模板 |
|------|------|
| RAG提示词 | `build_rag_prompt(question, context_docs)` |
| 检索流程 | `retriever.retrieve(query, top_k)` |
| 问答 | `rag.query(question)` |

### 下一步

- 继续阅读：MCP协议专题（五）- 深入了解MCP架构
- 实践项目：用向量数据库搭建本地知识库
- 参考资料：[Anthropic RAG最佳实践](https://docs.anthropic.com/)

---

**文档元信息**
难度：⭐⭐⭐⭐ | 类型：专家设计 | 更新日期：2026-03-25 | 预计阅读时间：60分钟 | 字数：约8000字
