---
title: "Claude API基础专题（四）：RAG检索增强生成系统"
date: "2026-03-25T13:00:00+08:00"
slug: "claude-api-rag-retrieval-augmented-generation"
aliases:
  - /posts/tech/claude-api-rag-retrieval-augmented-generation/
description: "RAG 系统的完整构建指南：从文档分块策略、嵌入向量生成、向量数据库选型到语义搜索与重排序，附带生产级 Python 代码实现。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "RAG", "向量数据库", "Python"]
---

# Claude API 基础专题（四）：RAG 检索增强生成系统

> **目标读者**：希望让 Claude 基于私有知识库回答问题的开发者
> **前置知识**：已完成第一篇《API基础》、第二篇《提示词工程》、第三篇《工具调用》

---

## 4.1 RAG 概述与核心概念

### 什么是 RAG

RAG（Retrieval-Augmented Generation）将信息检索与语言模型生成结合：在生成回答前，先从外部知识库检索相关信息，再用这些内容增强模型回答。

**为什么需要 RAG？**

| 问题 | 传统 LLM 的局限 | RAG 的解决方案 |
|------|----------------|----------------|
| 知识时效性 | 训练数据有截止日期 | 实时检索最新文档 |
| 知识覆盖度 | 无法涵盖所有领域知识 | 检索私有知识库 |
| 幻觉问题 | 可能生成错误信息 | 基于检索内容回答 |
| 可解释性 | 回答来源不明 | 答案可溯源到原文 |

### RAG 工作流程

```
用户提问 → 问题编码 → 查询向量 → 向量数据库检索 → 相关文档片段
    → 注入提示词 → Claude 生成回答 → 返回附有来源的回答
```

### RAG vs 微调 vs 上下文学习

| 特性 | RAG | 微调（Fine-tuning） | 上下文学习（ICL） |
|------|-----|---------------------|------------------|
| 更新知识 | 快（更新文档） | 慢（重新训练） | 即时（放入提示词） |
| 成本 | 低（仅向量数据库） | 高（GPU 训练） | 高（Token 消耗大） |
| 适用场景 | 知识库问答 | 风格/领域适应 | 单次特定任务 |
| 实时性 | ✅ 实时 | ❌ 需重新训练 | ✅ 实时 |

---

## 4.2 RAG 架构详解

### 完整 RAG 系统架构

```python
class RAGSystem:
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.chunker = ChunkingStrategy()
        self.embedder = EmbeddingModel()
        self.vector_store = VectorDatabase()
        self.retriever = RetrievalEngine()
        self.generator = ClaudeGenerator()

    def add_documents(self, documents: list) -> None:
        processed = self.document_processor.process(documents)
        chunks = self.chunker.chunk(processed)
        embeddings = self.embedder.embed(chunks)
        self.vector_store.add(embeddings, chunks)

    def query(self, question: str) -> str:
        query_embedding = self.embedder.embed([question])
        relevant_chunks = self.vector_store.search(query_embedding, top_k=5)
        prompt = self.build_prompt(question, relevant_chunks)
        return self.generator.generate(prompt)
```

### 核心组件详解

**1. 文档处理器**

```python
from abc import ABC, abstractmethod
import re

class DocumentProcessor:
    def process(self, content: str, source: str | None = None) -> dict:
        return {
            "content": self.clean_text(content),
            "source": source,
            "metadata": self.extract_metadata(content, source),
        }

    def clean_text(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s.,!?;:\'\"-]', '', text)
        return text.strip()

    @abstractmethod
    def extract_metadata(self, content: str, source: str) -> dict:
        ...

class PDFProcessor(DocumentProcessor):
    def extract_metadata(self, content: str, source: str) -> dict:
        return {"source": source, "type": "pdf", "char_count": len(content)}

class MarkdownProcessor(DocumentProcessor):
    def extract_metadata(self, content: str, source: str) -> dict:
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else "Untitled"
        return {"source": source, "type": "markdown", "title": title, "char_count": len(content)}
```

---

## 4.3 文档分块策略

分块是 RAG 中最关键的步骤之一。块太大则引入无关上下文、精度下降；块太小则丢失上下文，模型无法理解完整语义。

```python
from typing import List
import re

class ChunkingStrategy(ABC):
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    @abstractmethod
    def chunk(self, documents: List[dict]) -> List[dict]:
        ...

    def _create_chunk(self, text: str, metadata: dict, chunk_id: int) -> dict:
        return {"id": f"chunk_{chunk_id}", "content": text, "metadata": metadata, "char_count": len(text)}

class FixedSizeChunker(ChunkingStrategy):
    """固定字符数分块，在句子边界处对齐"""
    def chunk(self, documents: List[dict]) -> List[dict]:
        chunks, chunk_id = [], 0
        for doc in documents:
            text, metadata = doc["content"], doc.get("metadata", {})
            metadata["source"] = doc.get("source")
            start = 0
            while start < len(text):
                end = start + self.chunk_size
                chunk_text = text[start:end]
                if end < len(text):
                    chunk_text = self._split_at_sentence_boundary(chunk_text)
                chunks.append(self._create_chunk(chunk_text, metadata, chunk_id))
                chunk_id += 1
                start += self.chunk_size - self.overlap
        return chunks

    def _split_at_sentence_boundary(self, text: str) -> str:
        matches = list(re.finditer(r'([.!?。！？])\s+', text))
        if matches:
            return text[:matches[-1].end()]
        return text

class RecursiveChunker(ChunkingStrategy):
    """按段落层级递归分块，保留文档结构"""
    def chunk(self, documents: List[dict]) -> List[dict]:
        chunks, chunk_id = [], 0
        for doc in documents:
            text, metadata = doc["content"], doc.get("metadata", {})
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
            current_chunk = ""
            for para in paragraphs:
                if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                    chunks.append(self._create_chunk(current_chunk.strip(), metadata, chunk_id))
                    chunk_id += 1
                    current_chunk = current_chunk[-self.overlap:] if self.overlap > 0 else ""
                current_chunk += para + "\n\n"
            if current_chunk.strip():
                chunks.append(self._create_chunk(current_chunk.strip(), metadata, chunk_id))
        return chunks

class SemanticChunker(ChunkingStrategy):
    """基于语义相似度自动分块，在主题变化处断开"""
    def __init__(self, embedder, threshold: float = 0.7, **kwargs):
        super().__init__(**kwargs)
        self.embedder = embedder
        self.threshold = threshold

    def chunk(self, documents: List[dict]) -> List[dict]:
        chunks, chunk_id = [], 0
        for doc in documents:
            sentences = self._split_into_sentences(doc["content"])
            metadata = doc.get("metadata", {})
            current_group = [sentences[0]] if sentences else []
            for i in range(1, len(sentences)):
                similarity = self._cosine_similarity(
                    self.embedder.embed([sentences[i-1]])[0],
                    self.embedder.embed([sentences[i]])[0],
                )
                if similarity < self.threshold:
                    chunk_text = " ".join(current_group)
                    if len(chunk_text) > 50:
                        chunks.append(self._create_chunk(chunk_text, metadata, chunk_id))
                        chunk_id += 1
                    current_group = []
                current_group.append(sentences[i])
            if current_group:
                chunk_text = " ".join(current_group)
                if len(chunk_text) > 50:
                    chunks.append(self._create_chunk(chunk_text, metadata, chunk_id))
        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        parts = re.split(r'([.!?。！？]\s+)', text)
        sentences = [parts[i] + parts[i+1] for i in range(0, len(parts)-1, 2)]
        if len(parts) % 2 == 1 and parts[-1].strip():
            sentences.append(parts[-1])
        return sentences

    @staticmethod
    def _cosine_similarity(v1: list, v2: list) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = sum(a * a for a in v1) ** 0.5
        n2 = sum(b * b for b in v2) ** 0.5
        return dot / (n1 * n2 + 1e-8)
```

| 策略 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 固定大小 | 简单均匀 | 可能切断句子 | 通用场景 |
| 递归分块 | 保留段落结构 | 计算开销略高 | 长文档 |
| 语义分块 | 主题一致性好 | 需额外嵌入模型 | 高质量需求 |
| 文档结构感知 | 完美保留结构 | 需解析文档格式 | Markdown/HTML |

---

## 4.4 向量嵌入与检索

### 嵌入模型选择

> **注意**：Anthropic 官方当前并不提供 embedding API，其 RAG 文档推荐使用第三方嵌入服务或本地开源模型完成向量化。因此下面的选型以 OpenAI 与开源模型为主，Claude 仅负责最后的生成环节。

```python
class EmbeddingModel:
    # cost_per_1k 为公开定价（单位：美元 / 1K tokens），bge 为首创本地模型，记为 0
    MODELS = {
        "text-embedding-3-small":  {"provider": "OpenAI", "dimensions": 1536, "max_tokens": 8191, "cost_per_1k": 0.00002},
        "text-embedding-3-large":  {"provider": "OpenAI", "dimensions": 3072, "max_tokens": 8191, "cost_per_1k": 0.00013},
        "text-embedding-ada-002":  {"provider": "OpenAI", "dimensions": 1536, "max_tokens": 8191, "cost_per_1k": 0.0001},
        "bge-large-zh":            {"provider": "BAAI",   "dimensions": 1024, "max_tokens": 512,  "cost_per_1k": 0},
    }

    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        self.config = self.MODELS.get(model_name, self.MODELS["text-embedding-3-small"])

    def embed(self, texts: List[str]) -> List[List[float]]:
        if self.model_name.startswith("text-embedding"):
            return self._openai_embed(texts)
        return self._local_embed(texts)

    def _openai_embed(self, texts: List[str]) -> List[List[float]]:
        import os
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        # 单次请求输入不应超过 8191 token，超长需分批发送
        response = client.embeddings.create(model=self.model_name, input=texts)
        return [item.embedding for item in response.data]

    def _local_embed(self, texts: List[str]) -> List[List[float]]:
        # 本地开源模型，中文场景常选 BAAI/bge-large-zh-v1.5
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("BAAI/bge-large-zh-v1.5")
        return model.encode(texts, normalize_embeddings=True).tolist()
```

### 向量数据库

```python
from abc import ABC, abstractmethod

class VectorDatabase(ABC):
    @abstractmethod
    def add(self, embeddings: List[List[float]], documents: List[dict]): ...
    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[dict]: ...

class SimpleVectorDB(VectorDatabase):
    """内存向量数据库，适合小规模场景"""
    def __init__(self):
        self.vectors, self.documents = [], []

    def add(self, embeddings: List[List[float]], documents: List[dict]):
        self.vectors.extend(embeddings)
        self.documents.extend(documents)

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[dict]:
        scores = [(i, self._cosine_similarity(query_embedding, vec)) for i, vec in enumerate(self.vectors)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return [{**self.documents[idx].copy(), "score": score} for idx, score in scores[:top_k]]

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = sum(a * a for a in v1) ** 0.5
        n2 = sum(b * b for b in v2) ** 0.5
        return dot / (n1 * n2 + 1e-8)

class ChromaDB(VectorDatabase):
    """Chroma 开源向量数据库"""
    def __init__(self, persist_directory: str = "./chroma_db"):
        import chromadb
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection("documents")

    def add(self, embeddings: List[List[float]], documents: List[dict]):
        self.collection.add(
            ids=[doc["id"] for doc in documents],
            embeddings=embeddings,
            documents=[doc["content"] for doc in documents],
            metadatas=[doc.get("metadata", {}) for doc in documents],
        )

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[dict]:
        results = self.collection.query(query_embeddings=[query_embedding], n_results=top_k)
        return [
            {
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i],
            }
            for i in range(len(results["ids"][0]))
        ]

class PineconeDB(VectorDatabase):
    """Pinecone 云向量数据库"""
    def __init__(self, api_key: str, environment: str, index_name: str):
        from pinecone import Pinecone
        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)

    def add(self, embeddings: List[List[float]], documents: List[dict]):
        vectors = [
            {"id": doc["id"], "values": emb, "metadata": {"content": doc["content"], **doc.get("metadata", {})}}
            for emb, doc in zip(embeddings, documents)
        ]
        self.index.upsert(vectors=vectors)

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[dict]:
        results = self.index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
        return [
            {"id": m["id"], "content": m["metadata"]["content"],
             "metadata": {k: v for k, v in m["metadata"].items() if k != "content"}, "score": m["score"]}
            for m in results["matches"]
        ]
```

### 检索策略

```python
class RetrievalEngine:
    def __init__(self, vector_db: VectorDatabase, embedder: EmbeddingModel):
        self.vector_db, self.embedder = vector_db, embedder

    def retrieve(self, query: str, top_k: int = 5, min_score: float = 0.0) -> List[dict]:
        query_embedding = self.embedder.embed([query])[0]
        results = self.vector_db.search(query_embedding, top_k)
        return [r for r in results if r["score"] >= min_score]

class HybridRetrieval(RetrievalEngine):
    """向量检索 + BM25 关键词检索混合。

    BM25 需要对全量文档做词频扫描，因此仅支持在内存中持有全部原文的
    SimpleVectorDB；连续库（Chroma/Pinecone）请自行实现基于元数据的关键词召回。
    """
    def __init__(self, vector_db: VectorDatabase, embedder: EmbeddingModel, bm25_weight: float = 0.3):
        if not hasattr(vector_db, "documents"):
            raise TypeError("HybridRetrieval 需要内存型 SimpleVectorDB（含 documents 字段）")
        super().__init__(vector_db, embedder)
        self.bm25_weight = bm25_weight

    def retrieve(self, query: str, top_k: int = 5) -> List[dict]:
        vector_results = super().retrieve(query, top_k * 2)
        keyword_results = self._bm25_search(query, top_k * 2)
        return self._merge_results(vector_results, keyword_results, top_k)

    def _bm25_search(self, query: str, top_k: int) -> List[dict]:
        query_terms = set(query.lower().split())
        scores = [
            len(query_terms & set(doc["content"].lower().split())) / (len(doc["content"].split()) + 1)
            for doc in self.vector_db.documents
        ]
        indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [self.vector_db.documents[i] for i, _ in indexed[:top_k]]

    def _merge_results(self, vector_results: List[dict], keyword_results: List[dict], top_k: int) -> List[dict]:
        seen, merged = set(), []
        for vr, kr in zip(vector_results, keyword_results):
            if vr["id"] not in seen:
                vr["final_score"] = vr["score"] * (1 - self.bm25_weight)
                merged.append(vr)
                seen.add(vr["id"])
            if kr["id"] not in seen:
                kr["final_score"] = self.bm25_weight * min(kr.get("score", 0) * 10, 1.0)
                merged.append(kr)
                seen.add(kr["id"])
        merged.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        return merged[:top_k]
```

---

## 4.5 Claude API 中的 RAG 实现

### 构建 RAG 提示词

```python
def build_rag_prompt(question: str, context_docs: List[dict]) -> str:
    context_parts = []
    for i, doc in enumerate(context_docs, 1):
        source = doc.get("metadata", {}).get("source", "Unknown")
        context_parts.append(f"[文档{i}]（来源：{source}）\n{doc['content']}")

    context_str = "\n\n".join(context_parts)

    return f"""你是一个助手，基于提供的文档内容回答用户问题。

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

# 使用示例
context_docs = [
    {"content": "Claude API支持多种编程语言，包括Python、JavaScript、Go等。",
     "metadata": {"source": "API文档"}},
    {"content": "Python SDK的安装命令是：pip install anthropic",
     "metadata": {"source": "安装指南"}},
]

prompt = build_rag_prompt("Claude API支持哪些编程语言？", context_docs)
print(prompt)
```

### 完整 RAG 问答流程

```python
from anthropic import Anthropic
import os

class ClaudeRAG:
    def __init__(self, vector_db: VectorDatabase, embedder: EmbeddingModel):
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.retriever = RetrievalEngine(vector_db, embedder)

    def query(self, question: str, top_k: int = 5,
              model: str = "claude-sonnet-4-20250514") -> dict:
        retrieved_docs = self.retriever.retrieve(question, top_k)

        if not retrieved_docs:
            return {"answer": "我没有找到与您问题相关的文档信息。", "sources": [], "has_answer": False}

        prompt = build_rag_prompt(question, retrieved_docs)
        response = self.client.messages.create(
            model=model, max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        answer = response.content[0].text
        sources = list(set(doc.get("metadata", {}).get("source", "Unknown") for doc in retrieved_docs))

        return {"answer": answer, "sources": sources, "has_answer": True, "num_docs_retrieved": len(retrieved_docs)}

# 使用示例
def main():
    embedder = EmbeddingModel("text-embedding-ada-002")
    vector_db = ChromaDB(persist_directory="./my_vector_db")
    rag = ClaudeRAG(vector_db, embedder)

    result = rag.query("Claude API的速率限制是多少？")
    print(f"回答：{result['answer']}")
    print(f"参考来源：{', '.join(result['sources'])}")

if __name__ == "__main__":
    main()
```

### 高级 RAG 技术

```python
class AdvancedRAG:
    def __init__(self, vector_db: VectorDatabase, embedder: EmbeddingModel):
        self.vector_db, self.embedder = vector_db, embedder
        self.client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def query_with_reranking(self, question: str, top_k: int = 10, rerank_top_k: int = 5) -> dict:
        """先检索更多文档，再用 LLM 重排序精选"""
        initial_results = self._vector_search(question, top_k * 2)
        return self._claude_rerank(question, initial_results, rerank_top_k)

    def _claude_rerank(self, question: str, documents: List[dict], top_k: int) -> List[dict]:
        prompt = f"""请根据以下文档与问题的相关性进行排序。

问题：{question}

文档列表：
{chr(10).join(f"[{i+1}] {doc['content']}" for i, doc in enumerate(documents))}

请按相关性从高到低输出文档编号，用逗号分隔，例如：3,1,2
"""
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )

        import re
        numbers = [int(n) for n in re.findall(r'\d+', response.content[0].text.strip())]
        reranked = [documents[i - 1] for i in numbers if 0 <= i - 1 < len(documents)]
        reranked.extend(d for d in documents if d not in reranked)
        return reranked[:top_k]

    def query_with_query_expansion(self, question: str) -> List[dict]:
        """用 Claude 生成多个相关查询，扩大检索覆盖面"""
        expanded_queries = self._generate_related_queries(question)

        all_results = []
        for query in expanded_queries:
            all_results.extend(self._vector_search(query, top_k=5))

        seen = set()
        unique = []
        for doc in all_results:
            if doc["id"] not in seen:
                unique.append(doc)
                seen.add(doc["id"])

        unique.sort(key=lambda x: x.get("score", 0), reverse=True)
        return unique[:5]

    def _generate_related_queries(self, question: str) -> List[str]:
        prompt = f"""请为以下问题生成3个不同的表达方式：
1. 保持原问题的核心意图
2. 使用不同的词汇或句式
3. 涵盖问题的不同方面

原问题：{question}

每行一个查询：
"""
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        queries = [q.strip() for q in response.content[0].text.strip().split('\n') if q.strip()]
        return queries + [question]
```

---

## 4.6 RAG 系统评估与优化

### 评估指标

```python
class RAGEvaluator:
    def evaluate(self, rag_system, eval_dataset: List[dict]) -> dict:
        """
        eval_dataset 格式：
        {"question": "...", "ground_truth": "...", "context": ["相关文档1", "相关文档2"]}
        """
        results = {"retrieval_precision": [], "retrieval_recall": [], "answer_accuracy": []}

        for item in eval_dataset:
            rag_result = rag_system.query(item["question"])
            precision, recall = self._calc_retrieval_metrics(
                rag_result.get("retrieved_docs", []), item["context"]
            )
            results["retrieval_precision"].append(precision)
            results["retrieval_recall"].append(recall)
            results["answer_accuracy"].append(
                self._text_similarity(rag_result["answer"], item["ground_truth"])
            )

        return {
            "avg_retrieval_precision": sum(results["retrieval_precision"]) / len(results["retrieval_precision"]),
            "avg_retrieval_recall": sum(results["retrieval_recall"]) / len(results["retrieval_recall"]),
            "avg_answer_accuracy": sum(results["answer_accuracy"]) / len(results["answer_accuracy"]),
        }

    @staticmethod
    def _calc_retrieval_metrics(retrieved: List[str], relevant: List[str], k: int = None) -> tuple:
        retrieved_set = set(retrieved[:k] if k else retrieved)
        relevant_set = set(relevant)
        precision = len(retrieved_set & relevant_set) / len(retrieved_set) if retrieved_set else 0
        recall = len(retrieved_set & relevant_set) / len(relevant_set) if relevant_set else 0
        return precision, recall

    @staticmethod
    def _text_similarity(text1: str, text2: str) -> float:
        words1, words2 = set(text1.lower().split()), set(text2.lower().split())
        if not words1 or not words2:
            return 0
        return len(words1 & words2) / len(words1 | words2)
```

### 常见优化策略

```python
# 检索参数调优网格
retrieval_configs = {
    "top_k": [3, 5, 7, 10],
    "min_score_threshold": [0.5, 0.6, 0.7, 0.8],
    "chunk_size": [256, 512, 1024],
    "overlap": [0, 25, 50, 100],
    "bm25_weight": [0.1, 0.2, 0.3, 0.4],
}
```

### 生产环境建议

| 场景 | 推荐方案 | 说明 |
|------|----------|------|
| 小规模（<1 万文档） | ChromaDB + ADA-002 | 简单、免费 |
| 中等规模（10 万-100 万） | Pinecone + text-embedding-3 | 可扩展、成本适中 |
| 大规模（>100 万） | Weaviate/Qdrant + bge-large | 高性能、开源 |
| 高隐私需求 | Milvus + 开源嵌入模型 | 数据不出境 |

---

## 4.7 常见问题与解决方案

**Q1：检索不到相关文档怎么办？**

```python
# 降低相似度阈值
results = retriever.retrieve(question, top_k=10, min_score=0.3)
# 查询扩展
expanded_queries = generate_related_queries(question)
all_results = parallel_retrieve(expanded_queries)
# 混合关键词检索
hybrid_results = hybrid_retriever.retrieve(question)
```

**Q2：回答中出现幻觉怎么办？**

在提示词中加强约束，要求模型只基于上下文回答并明确标注"未找到相关信息"的情况。

**Q3：检索结果重复怎么办？**

```python
def deduplicate_results(results: List[dict], threshold: float = 0.95) -> List[dict]:
    unique = []
    for doc in results:
        if not any(compute_similarity(doc["content"], u["content"]) > threshold for u in unique):
            unique.append(doc)
    return unique
```

**Q4：文档更新后向量数据库如何同步？**

```python
class VectorDBSync:
    def __init__(self, vector_db, embedder):
        self.vector_db, self.embedder = vector_db, embedder

    def update_document(self, doc_id: str, new_content: str):
        self.vector_db.delete(doc_id)
        new_embedding = self.embedder.embed([new_content])[0]
        self.vector_db.add([new_embedding], [{"id": doc_id, "content": new_content}])

    def full_reindex(self, documents: List[dict]):
        self.vector_db.clear()
        chunks = self.chunker.chunk(documents)
        embeddings = self.embedder.embed([c["content"] for c in chunks])
        self.vector_db.add(embeddings, chunks)
```

**Q5：如何处理中文文档的分词？**

```python
import jieba

class ChineseTextProcessor:
    def __init__(self):
        jieba.setLogLevel(jieba.logging.INFO)

    def tokenize(self, text: str) -> List[str]:
        return list(jieba.cut(text))

    def add_custom_words(self, words: List[str]):
        for word in words:
            jieba.add_word(word)

    def extract_keywords(self, text: str, top_k: int = 5) -> List[str]:
        import jieba.analyse
        return jieba.analyse.extract_tags(text, topK=top_k)
```

---

## 本章总结

### 要点回顾

| 知识点 | 关键内容 |
|--------|----------|
| RAG 概述 | 工作流程、vs 微调、vs 上下文学习 |
| RAG 架构 | 文档处理、分块、嵌入、检索、生成 |
| 分块策略 | 固定大小、递归、语义分块 |
| 向量检索 | 嵌入模型、向量数据库、相似度计算 |
| RAG 实现 | 提示词构建、完整流程 |
| 评估优化 | 精确率、召回率、重排序、查询扩展 |

### 下一步

- 继续阅读：MCP 协议专题（五）
- 实践项目：用向量数据库搭建本地知识库
- 参考资料：[Anthropic RAG 推荐做法](https://docs.anthropic.com/)
