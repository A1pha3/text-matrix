---
title: "RAG-Anything：港大开源多模态RAG框架，一站式处理文本/图像/表格/公式"
slug: rag-anything-multimodal-rag-framework
date: "2026-04-22T16:25:00+08:00"
description: "全面解析 RAG-Anything：港大开源的多模态 RAG 框架，基于 LightRAG，支持 PDF、Office、图像等全类型文档，构建多模态知识图谱，实现跨模态检索与问答。"
categories: ["技术笔记"]
tags: ["RAG", "多模态", "LightRAG", "RAG框架", "文档处理", "知识图谱"]
---

# RAG-Anything：港大开源多模态 RAG 框架，一站式处理文本/图像/表格/公式

## 概述

**RAG-Anything** 是香港大学（HKUDS）开发的多模态 RAG（检索增强生成）框架，基于 LightRAG，处理文本、图像、表格、公式、图表等多种文档内容，构建多模态知识图谱，实现跨模态检索与问答。

> **GitHub**: [HKUDS/RAG-Anything](https://github.com/HKUDS/RAG-Anything)  
> **Stars**: 17,159 ⭐  
> **arXiv**: [2510.12323](https://arxiv.org/abs/2510.12323)  
> **基于**: LightRAG  
> **语言**: Python 3.10+

### 一句话定位

**"All-in-One Multimodal RAG System"** —— 传统 RAG 只处理文本，RAG-Anything 覆盖文档中的所有内容类型。

### 核心特点

| 特点 | 说明 |
|------|------|
| **端到端多模态流程** | 从文档解析到多模态问答的完整流程 |
| **全类型文档支持** | PDF、Office、图片、表格、公式 |
| **多模态知识图谱** | 自动提取实体和跨模态关系 |
| **自适应处理模式** | MinerU 解析或直接注入 |
| **混合智能检索** | 文本+多模态跨模态检索 |

---

## 系统架构

### 核心流程

```
文档解析 → 内容分析 → 知识图谱构建 → 智能检索 → 问答生成
```

### 1. 文档解析阶段

使用 **MinerU** 进行高保真文档结构提取：
- 智能分块：文本块、视觉元素、表格、公式
- 上下文关系保留
- 通用格式支持：PDF、Office (DOC/DOCX/PPT/PPTX/XLS/XLSX)、图片

### 2. 多模态内容理解

- **自主内容分类与路由**：自动识别内容类型并路由到最优处理通道
- **并发多管道架构**：文本和多模态内容并行处理
- **文档层次结构提取**：保留原始文档层次结构

### 3. 多模态分析引擎

| 分析器 | 功能 |
|--------|------|
| **视觉内容分析器** | 图像描述生成、空间关系提取 |
| **结构化数据解释器** | 表格解析、趋势分析、依赖关系识别 |
| **公式分析器** | LaTeX 公式解析与理解 |

---

## 快速开始

### 安装

```bash
pip install raganything

# 或使用 uv
uv pip install raganything
```

### 基本使用

```python
from raganything import RAGAnything

# 初始化
rag = RAGAnything()

# 添加文档
rag.add_documents("path/to/document.pdf")

# 多模态问答
result = rag.query(
    "这份文档中的图表展示了什么趋势？",
    use_vlm=True  # 启用视觉语言模型
)
```

### 支持的文档类型

| 类型 | 状态 | 说明 |
|------|------|------|
| PDF | ✅ | 完整支持 |
| Word (DOCX) | ✅ | 文本+表格 |
| PowerPoint (PPTX) | ✅ | 幻灯片+图表 |
| Excel (XLSX) | ✅ | 表格数据 |
| 图片 | ✅ | VLM 增强 |
| Markdown | ✅ | 文本+代码 |
| LaTeX | ✅ | 公式支持 |

---

## 应用场景

### 1. 学术论文解析

RAG-Anything 可以理解论文中的：
- 图表和图示
- 数学公式
- 表格数据
- 参考文献

### 2. 财务报告分析

处理年报、季报中的：
- 财务报表
- 趋势图表
- 数据表格

### 3. 技术文档问答

支持技术文档中的：
- 架构图理解
- 代码片段
- API 文档

### 4. 医疗记录处理

支持医疗文档中的：
- 检查报告图像
- 检验数据表格
- 处方公式

---

## 资源链接

| 资源 | 链接 |
|------|------|
| GitHub | [HKUDS/RAG-Anything](https://github.com/HKUDS/RAG-Anything) |
| arXiv 论文 | [2510.12323](https://arxiv.org/abs/2510.12323) |
| PyPI | [raganything](https://pypi.org/project/raganything/) |
| Discord | [社区讨论](https://discord.gg/yF2MmDJyGJ) |

---

*RAG-Anything：多模态 RAG 框架，覆盖文档中的文本、图像、表格、公式等所有内容类型。*
