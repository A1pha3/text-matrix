---
title: "QMD：本地文档语义搜索完全指南"
date: "2026-04-06T21:33:00+08:00"
slug: "qmd-local-document-semantic-search-guide"
description: "全面介绍 21.8k Stars 的 QMD 本地文档语义搜索工具，涵盖语义搜索+BM25 混合搜索、10+ 文档格式支持、Python API、MCP Server 集成，以及 Ollama 向量嵌入的工作原理。"
draft: false
categories: ["技术笔记"]
tags: ["QMD", "语义搜索", "本地搜索", "Ollama", "BM25", "MCP"]
---

## 学习目标

通过本文，你将全面掌握以下核心能力：

- 深入理解 QMD 的项目定位、技术架构和工作原理
- 学会安装和配置 QMD（pip/curl 两种方式）
- 掌握 QMD 的语义搜索和关键词搜索（BM25）混合搜索功能
- 学会使用 CLI 和 Python API 进行文档搜索
- 理解 MCP Server 与 AI Agent 的集成方式
- 掌握增量索引和实时更新的配置
- 支持的文档格式详解（PDF、Markdown、Office 文件等）

---

## 1. 项目概述

### 1.1 是什么

QMD（Query Matching on Documents）是一个**本地文档语义搜索工具**，它结合了语义搜索和关键词搜索，让用户能够快速在本地文档中找到相关内容。

**核心理念**：你的数据永远留在你自己的机器上，不会上传到任何云服务。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **21.8k** |
| GitHub Forks | **17** |
| 最新提交 | **2026-04-04**（2 天前） |
| License | **Apache-2.0** |
| 语言 | **Python 100%** |

### 1.3 技术栈

| 组件 | 技术 | 作用 |
|------|------|------|
| **嵌入模型** | Ollama | 将文本转换为向量 |
| **向量存储** | SQLite + vecsimgrocerydemo | 高效存储和检索 |
| **关键词搜索** | BM25 | 传统关键词匹配 |
| **文档格式** | pdfminer/docling | 解析各类文档 |

### 1.4 与竞品对比

| 特性 | QMD | Semantic Scholar | Elasticsearch |
|------|-----|-----------------|----------------|
| **部署方式** | 本地 | 云服务 | 自托管 |
| **数据隐私** | 完全本地 | 上传云端 | 自托管 |
| **语义搜索** | ✅ Ollama | ✅ | ⚠️ 需要插件 |
| **BM25 搜索** | ✅ | ❌ | ✅ |
| **多格式支持** | ✅ 10+ 格式 | ❌ 仅 PDF | ⚠️ 需插件 |
| **MCP 支持** | ✅ | ❌ | ❌ |

---

## 2. 核心功能详解

### 2.1 混合搜索

QMD 的核心特点是**语义搜索 + 关键词搜索（BM25）**的混合搜索：

```bash
# 语义搜索示例
qmd search "machine learning optimization techniques"
# 返回语义上相关的内容，不一定包含这些词

# 关键词搜索示例
qmd search "machine learning" --method bm25
# 只返回包含 "machine" 和 "learning" 的文档
```

### 2.2 支持的文档格式

| 格式 | 扩展名 | 支持情况 |
|------|--------|---------|
| **PDF** | .pdf | ✅ |
| **Markdown** | .md, .markdown | ✅ |
| **纯文本** | .txt | ✅ |
| **Word** | .docx | ✅ |
| **Excel** | .xlsx, .xls | ✅ |
| **PowerPoint** | .pptx | ✅ |
| **EPUB** | .epub | ✅ |
| **CSV** | .csv | ✅ |
| **JSON** | .json | ✅ |
| **HTML** | .html, .htm | ✅ |
| **XML** | .xml | ✅ |

### 2.3 实时索引

```bash
# 初始化索引（扫描文档并创建数据库）
qmd index ~/documents

# 增量更新（只索引新文档或修改过的文档）
qmd index ~/documents --incremental

# 查看索引状态
qmd stats
```

### 2.4 MCP Server

QMD 内置 **MCP Server**，可以与 AI Agent（如 Claude Code）集成：

```bash
# 启动 MCP Server
qmd mcp

# 输出示例
QMD MCP Server running on http://localhost:8080
MCP JSON-RPC endpoint: http://localhost:8080/mcp
```

在 Claude Code 的 CLAUDE.md 中配置：

```markdown
<!-- CLAUDE.md -->
For any question about your local documents, use the qmd tool.
```

---

## 3. 工作原理深度解析

### 3.1 整体架构

```
┌─────────────────────────────────────────────────┐
│                   QMD 用户                       │
│            (CLI / Python API)                   │
└─────────────────┬───────────────────────────────┘
                    │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐     ┌─────────────────┐
│  CLI 接口     │     │  Python API     │
└───────┬───────┘     └────────┬────────┘
        │                      │
        └──────────┬───────────┘
                   │
        ┌─────────┴──────────┐
        ▼                    ▼
┌───────────────┐     ┌─────────────────┐
│ BM25 索引    │     │  Ollama 嵌入    │
│ (关键词搜索)  │     │ (语义搜索)       │
└───────────────┘     └────────┬────────┘
        │                      │
        └──────────┬───────────┘
                   │
        ┌─────────┴──────────┐
        ▼                    ▼
┌───────────────┐     ┌─────────────────┐
│  SQLite      │     │  向量数据库     │
│ (BM25 结果)   │     │ (语义相似度)    │
└───────────────┘     └─────────────────┘
```

### 3.2 语义搜索流程

```python
# QMD 语义搜索流程
def semantic_search(query, top_k=5):
    # 1. 使用 Ollama 将查询文本转换为向量
    query_embedding = ollama.embeddings(
        model="nomic-embed-text",
        prompt=query
    )
    
    # 2. 在向量数据库中搜索最相似的文档片段
    results = vector_db.search(
        query_embedding,
        n=top_k
    )
    
    # 3. 返回最相关的文档
    return results
```

### 3.3 BM25 关键词搜索

BM25（Best Matching 25）是一种经典的**概率关键词排序算法**：

```python
# BM25 算法核心思想
def bm25_score(doc, query, k1=1.5, b=0.75):
    """
    - k1: 词频饱和参数（控制词频影响力）
    - b: 文档长度归一化参数
    """
    scores = []
    for term in query:
        tf = doc.term_freq(term)           # 词频
        df = corpus.doc_freq(term)        # 文档频率
        idf = log((N - df + 0.5) / (df + 0.5))  # 逆文档频率
        
        # BM25 公式
        score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc.len / avg_doc_len))
        scores.append(score)
    
    return sum(scores)
```

### 3.4 混合搜索融合

```python
def hybrid_search(query, alpha=0.5):
    """
    alpha: 语义搜索权重 (1-alpha 是 BM25 权重)
    """
    # 获取语义搜索结果
    semantic_results = semantic_search(query)
    
    # 获取 BM25 结果
    bm25_results = bm25_search(query)
    
    # RRFR 融合
    fused_results = []
    for doc in corpus:
        rrf_score = 0
        for rank, result in enumerate(semantic_results[:k]):
            if result.doc == doc:
                rrf_score += 1 / (k + rank + 1)
        
        for rank, result in enumerate(bm25_results[:k]):
            if result.doc == doc:
                rrf_score += alpha / (k + rank + 1)
        
        fused_results.append((doc, rrf_score))
    
    return sorted(fused_results, key=lambda x: x[1], reverse=True)
```

---

## 4. 安装指南

### 4.1 pip 安装（推荐）

```bash
# 安装 QMD
pip install qmd

# 验证安装
qmd --version
```

### 4.2 curl 脚本安装（无需 pip）

```bash
# 一键安装
curl -fsSL https://raw.githubusercontent.com/tobi/qmd/main/install.sh | sh

# 安装到指定目录
curl -fsSL https://raw.githubusercontent.com/tobi/qmd/main/install.sh | sh -s -- --prefix ~/.local
```

### 4.3 Ollama 安装（必需）

QMD 需要 **Ollama** 作为嵌入模型的后端：

```bash
# macOS/Linux 安装 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Windows: 下载安装包 https://ollama.com/download

# 启动 Ollama 服务
ollama serve

# 下载嵌入模型（推荐）
ollama pull nomic-embed-text

# 验证
ollama list
```

### 4.4 Shell 自动补全

```bash
# Bash
qmd --completion bash >> ~/.bashrc

# Zsh
qmd --completion zsh >> ~/.zshrc

# Fish
qmd --completion fish > ~/.config/fish/completions/qmd.fish
```

---

## 5. 快速上手

### 5.1 初始化索引

```bash
# 创建索引（会扫描所有支持的文件）
qmd index ~/documents

# 指定目录
qmd index /path/to/papers

# 递归扫描子目录
qmd index ~/documents --recursive

# 查看索引统计
qmd stats
```

### 5.2 基本搜索

```bash
# 语义搜索（默认）
qmd search "What is transformer architecture?"

# 关键词搜索
qmd search "transformer attention" --method bm25

# 混合搜索
qmd search "neural network optimization" --method hybrid

# 显示更多结果
qmd search "machine learning" --top 10
```

### 5.3 搜索输出

```bash
# 简短输出
qmd search "python async"

# 输出示例
---
Score: 0.89
File: /docs/python-guide.md
Line: 42
Snippet: "Python's async/await syntax provides..."
---

Score: 0.85
File: /docs/advanced-python.md
Line: 128
Snippet: "Asynchronous programming in Python uses..."
```

### 5.4 增量更新

```bash
# 增量索引（只处理新文件）
qmd index ~/documents --incremental

# 强制重建索引
qmd index ~/documents --rebuild
```

---

## 6. Python API 使用

### 6.1 基本用法

```python
from qmd import QMD

# 初始化
qmd = QMD(
    data_dir="~/.local/share/qmd",  # 数据目录
    embed_model="nomic-embed-text"    # 嵌入模型
)

# 添加文档
qmd.add("~/documents/python-guide.md")
qmd.add("~/documents/notes/")

# 搜索
results = qmd.search("async programming in Python")
for result in results:
    print(f"{result.file}:{result.line} - {result.snippet}")
```

### 6.2 高级配置

```python
from qmd import SearchMethod

# 配置搜索参数
results = qmd.search(
    query="machine learning optimization",
    method=SearchMethod.HYBRID,  # 混合搜索
    alpha=0.7,                    # 语义权重
    top_k=10,                     # 返回结果数
    min_score=0.5                 # 最低分数阈值
)

# 只搜索特定格式
results = qmd.search(
    "Python best practices",
    extensions=[".md", ".txt"]    # 只搜索 Markdown 和文本
)

# 排除特定目录
results = qmd.search(
    "API design",
    exclude_dirs=[".git", "node_modules", "__pycache__"]
)
```

### 6.3 索引管理

```python
# 查看索引统计
stats = qmd.stats()
print(f"文档数: {stats['num_docs']}")
print(f"索引大小: {stats['index_size']} bytes")

# 重建索引
qmd.rebuild()

# 清理缓存
qmd.clean()
```

---

## 7. MCP Server 集成

### 7.1 启动 MCP Server

```bash
# 启动 Server
qmd mcp --port 8080

# 后台运行
qmd mcp --port 8080 &
```

### 7.2 MCP Tools

QMD MCP Server 提供以下工具：

| 工具名 | 功能 |
|--------|------|
| `qmd_search` | 搜索文档 |
| `qmd_add` | 添加文档到索引 |
| `qmd_stats` | 查看索引统计 |
| `qmd_rebuild` | 重建索引 |

### 7.3 在 AI Agent 中使用

在 Claude Code 的 CLAUDE.md 中添加：

```markdown
# Local Document Search
For questions about code, documentation, or technical topics, use qmd to search local documents:

1. First, index the documents if not already done:
   `qmd index ~/path/to/documents`

2. Search using semantic or keyword search:
   `qmd search "your question here"`

3. For technical queries, prefer semantic search for best results.
```

### 7.4 MCP 配置示例

```json
{
  "mcpServers": {
    "qmd": {
      "command": "qmd",
      "args": ["mcp", "--port", "8080"],
      "env": {
        "QMD_DATA_DIR": "~/.local/share/qmd"
      }
    }
  }
}
```

---

## 8. 配置选项

### 8.1 配置文件

QMD 配置文件位于 `~/.config/qmd/config.toml`（Linux/macOS）或 `%APPDATA%\qmd\config.toml`（Windows）：

```toml
[general]
# 数据目录
data_dir = "~/.local/share/qmd"

# 索引目录
index_dir = "~/.local/share/qmd/index"

# 日志级别
log_level = "INFO"

[search]
# 默认搜索方法 (semantic, bm25, hybrid)
default_method = "hybrid"

# 默认返回结果数
default_top_k = 5

# 语义搜索权重（用于混合搜索）
semantic_weight = 0.7

[embed]
# Ollama 服务地址
ollama_base_url = "http://localhost:11434"

# 嵌入模型
model = "nomic-embed-text"

# 批处理大小
batch_size = 32

[index]
# 并行线程数
num_workers = 4

# 文件大小限制（MB）
max_file_size = 50

# 排除的目录
exclude_dirs = [".git", "node_modules", "__pycache__", ".venv"]
```

### 8.2 环境变量

| 变量 | 说明 | 默认值 |
|------|------|---------|
| `QMD_DATA_DIR` | 数据目录 | ~/.local/share/qmd |
| `QMD_OLLAMA_URL` | Ollama 地址 | http://localhost:11434 |
| `QMD_LOG_LEVEL` | 日志级别 | INFO |

---

## 9. 性能优化

### 9.1 索引性能

```bash
# 使用多线程加速索引
qmd index ~/documents --num-workers 8

# SSD vs HDD
# SSD: ~1000 docs/min
# HDD: ~200 docs/min
```

### 9.2 搜索性能

| 索引规模 | 首次搜索 | 缓存后 |
|----------|---------|--------|
| 1,000 文档 | ~200ms | ~10ms |
| 10,000 文档 | ~500ms | ~20ms |
| 100,000 文档 | ~2s | ~50ms |

### 9.3 内存使用

```bash
# 查看内存使用
qmd stats

# 典型内存占用
# 10,000 文档: ~500MB RAM
# 100,000 文档: ~4GB RAM
```

---

## 10. 常见问题

### 10.1 Ollama 连接失败

```bash
# 检查 Ollama 是否运行
ollama list

# 如果没有运行，启动它
ollama serve

# 检查端口
curl http://localhost:11434
```

### 10.2 嵌入模型加载失败

```bash
# 重新下载嵌入模型
ollama pull nomic-embed-text

# 使用其他模型
export QMD_EMBED_MODEL="mxbai-embed-large"
```

### 10.3 索引损坏

```bash
# 备份并重建索引
cp -r ~/.local/share/qmd ~/.local/share/qmd.bak
qmd index ~/documents --rebuild
```

---

## 11. 总结

QMD 是一个**功能完备的本地文档语义搜索工具**，具有以下优势：

**为什么选择 QMD：**

| 优势 | 说明 |
|------|------|
| **完全隐私** | 数据永不离开本地机器 |
| **混合搜索** | 语义 + BM25，取长补短 |
| **多格式支持** | PDF、Office、EPUB 等 10+ 格式 |
| **MCP 集成** | 与 AI Agent 无缝配合 |
| **增量索引** | 自动处理新文档 |
| **轻量级** | 纯 Python 实现 |

**适用场景：**

- 代码库文档搜索
- 技术文档检索
- 个人知识库搜索
- AI Agent 文档问答

**官方资源：**

- GitHub：https://github.com/tobi/qmd
- 文档：https://github.com/tobi/qmd#readme
- PyPI：https://pypi.org/project/qmd
- Ollama：https://ollama.com