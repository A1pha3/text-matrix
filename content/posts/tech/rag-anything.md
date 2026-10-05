---
title: "RAG-Anything：港大开源的全能多模态 RAG 框架，一站式处理文本/图片/表格/公式"
date: "2026-04-27T01:10:00+08:00"
lastmod: "2026-09-28T11:00:00+08:00"
slug: rag-anything-hku-multimodal-rag
github_repo: "HKUDS/RAG-Anything"
source_key: "gh:HKUDS/RAG-Anything"
description: "RAG-Anything 是港大数据智能实验室（HKUDS）开发的 All-in-One 多模态 RAG 框架，基于 LightRAG，一站式处理 PDF、Office 文档、图片、表格、数学公式及音视频，构建多模态知识图谱，实现跨模态检索。本文以 v1.4.1 为口径。"
draft: false
categories: ["技术笔记"]
tags: ["RAG", "多模态", "知识图谱", "Python"]
---

# RAG-Anything：港大开源的全能多模态 RAG 框架，一站式处理文本/图片/表格/公式

传统 RAG 系统只索引文本，图片、表格、公式的内容在索引阶段就丢了。论文里的图表、金融报告里的数据表格、产品手册里的公式——这些模态在 text-focused RAG 里根本不进检索库。

RAG-Anything 的做法是：用一个统一管道把所有模态解析成结构化实体，再建跨模态知识图谱做检索。GitHub 23,440 stars（2026-09-28 读数），港大数据智能实验室（HKUDS）开发，基于 LightRAG，MIT 协议，PyPI 一行安装，当前版本 v1.4.1。

它真正解决的不是"再多接一个 OCR 工具"，而是把多模态内容变成知识图谱里的一等公民：图片、表格、公式和文本一样拥有实体、关系和页码定位，检索时同库同查。

---

## 一、系统地图：两条路径，三层结构

用 RAG-Anything 有两条路，先分清再谈细节：

| 路径 | 入口 | 适用场景 |
|------|------|----------|
| 完整解析管道 | `process_document_complete()` | 手头有原始文档（PDF/Office/图片/音视频），从解析开始跑 |
| 直接内容注入 | `insert_content_list()` | 已有预解析的内容列表——外部解析器产出、历史缓存复用、程序生成的多模态数据 |

两条路径最终汇入同一套三层结构：

| 层 | 职责 | 关键组件 |
|----|------|----------|
| 解析层 | 把文档拆成文本块、图片、表格、公式等结构化元素 | MinerU / Docling / PaddleOCR 三种解析器 |
| 图谱层 | 元素转实体、建跨模态关系、维护文档层级 | 基于 LightRAG 的知识图谱索引 |
| 查询层 | 文本检索、VLM 看图、多模态内容联合查询 | 三种查询方式（下文详述） |

---

## 二、现有 RAG 处理多模态文档的缺口

现代文档包含四类模态：
- **文本**：正文、标题、列表
- **视觉元素**：照片、插图、图表
- **结构化数据**：表格、数据矩阵
- **数学公式**：LaTeX 格式的公式和推导

现有方案的局限：
- **Text-only RAG**：只索引文本，图片和表格内容在摄取阶段就丢了
- **专用工具拼接**：需要多种工具组合，流程复杂，各模态数据之间没有语义关联
- **跨模态理解缺失**：文本和图片之间没有实体链接，检索时只能各查各的

RAG-Anything 的解法：**统一管道处理所有模态，构建跨模态知识图谱。**

---

## 三、完整解析管道：五阶段

```
文档解析 → 内容理解与路由 → 多模态分析引擎 → 知识图谱索引 → 模态感知检索
```

### 阶段 1：文档解析（Document Parsing）

默认用 MinerU 做文档结构提取，保留复杂版面的语义层级。解析后自动将文档分割为文本块、视觉元素、结构化表格、数学公式，同时保留上下文关系。支持 PDF、Office 文档（DOC/DOCX/PPT/PPTX/XLS/XLSX）、图片，以及 v1.4 起的音频、视频文件。

### 阶段 2：内容理解与路由

自动识别内容类型并路由到对应处理管道。文本和多模态内容走独立管道并发执行，提取文档层级和元素间关系。

### 阶段 3：多模态分析引擎

四类处理器各司其职：

- **视觉内容分析器**：调用视觉模型生成图像描述，提取视觉元素间的空间关系和层级结构
- **结构化数据解释器**：对表格做统计模式识别，识别跨表格数据集的语义关系
- **数学表达式解析器**：解析 LaTeX 公式，建立数学方程与领域知识库之间的概念映射
- **可扩展模态处理器**：插件架构，自定义内容类型可在运行时动态接入

### 阶段 4：多模态知识图谱索引

将多模态元素转换为知识图谱实体，附带语义注释和元数据。在文本实体与多模态组件之间建立语义连接（通过自动关系推理算法）。文档层级通过 "belongs_to" 关系链维护。关系类型带语义接近度评分。

### 阶段 5：模态感知检索

向量相似度搜索与图遍历算法结合做综合检索。排名时根据查询的模态偏好调整权重，维护检索元素之间的语义和结构关系。

---

## 四、主要特性

| 特性 | 说明 |
|------|------|
| 端到端多模态管道 | 文档摄取→解析→知识图谱→检索→应答的完整工作流 |
| 通用文档支持 | PDF、Office 文档、图片、文本文件，v1.4 起含音频/视频 |
| 专用内容分析器 | 图片、表格、数学公式各有独立处理器 |
| 多模态知识图谱 | 自动实体提取和跨模态关系发现 |
| 自适应处理模式 | MinerU 解析或直接多模态内容注入 |
| 直接内容列表插入 | 跳过解析，直接插入外部来源的预解析内容 |
| 混合检索 | 向量相似度 + 图遍历融合 |

---

## 五、快速开始

### 安装（PyPI）

```bash
# 基础安装（已含 LightRAG 与 MinerU 核心依赖）
pip install raganything

# 含所有 Python 可选依赖
pip install 'raganything[all]'

# 扩展图片格式（BMP, TIFF, GIF, WebP）
pip install 'raganything[image]'

# 文本文件（TXT, MD）
pip install 'raganything[text]'

# 音频（mp3/wav/flac/m4a/ogg，本地 Whisper 转写）
pip install 'raganything[audio]'

# 视频（mp4/mov/webm/avi/mkv，另需 PATH 中有 ffmpeg）
pip install 'raganything[video]'
```

两件 `[all]` 管不到的事：

- **Office 文档（.doc/.docx/.ppt/.pptx/.xls/.xlsx）需要单独安装 LibreOffice**，这是外部程序依赖，pip 装不来；
- **PaddleOCR 解析器**需要 `pip install 'raganything[paddleocr]'` 之后，再按官方指引单独装 paddlepaddle（CPU/GPU 包随平台不同）。

### 从源码安装

```bash
git clone https://github.com/HKUDS/RAG-Anything.git
cd RAG-Anything
uv sync --all-extras

# 运行示例
uv run python examples/raganything_example.py --help
```

MinerU 模型在首次使用时自动下载，离线环境可参考仓库 `docs/offline_setup.md` 预配置。`examples/` 下的三个解析测试脚本（office/image/text format test）不需要 API key，装完解析器就能验证环境。

### 配置

仓库根目录的 `env.example` 是环境变量样例（注意文件名没有前导点）。解析相关的核心项：

```bash
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=your_base_url  # 可选
OUTPUT_DIR=./output             # 解析结果输出目录
PARSER=mineru                   # 解析器：mineru / docling / paddleocr
PARSE_METHOD=auto               # 解析方式：auto / ocr / txt
```

音频与视频处理默认关闭，要用需显式开启并装对应 extras：

```bash
ENABLE_AUDIO_PROCESSING=false   # 开启需 raganything[audio]
WHISPER_MODEL=base              # tiny/base/small/medium/large-v3
# WHISPER_LANGUAGE=zh           # 中文音频建议 medium 以上并显式设语言，
                                # 小模型对非拉丁文字专名的转写会明显劣化
ENABLE_VIDEO_PROCESSING=false   # 开启需 raganything[video]
```

---

## 六、三种查询方式

这是选型时最容易低估的部分——同一份知识库，三种问法走的是不同链路：

**纯文本查询**：`aquery()` 走 LightRAG 的四种检索模式，`hybrid`（混合）、`local`（局部）、`global`（全局）、`naive`（朴素向量）。基础知识库检索用这个。

**VLM 增强查询**：当检索到的上下文里带图片路径时，系统自动加载图片、base64 编码，连同文本上下文一起发给视觉模型综合分析。构造 `RAGAnything` 时提供了 `vision_model_func` 就默认启用，也可以用 `vlm_enhanced=True/False` 强制开关。问"文档里那张架构图在讲什么"这类问题，靠的是这条链路。

**多模态查询**：`aquery_with_multimodal()` 把查询时的临时内容（一段表格数据、一个公式）作为附加上下文与知识库联合检索，适合"拿这个表和文档里的结论对比"类任务。

---

## 七、解析器三选一

`PARSER` 环境变量（或 `RAGAnythingConfig(parser=...)`）决定解析层用谁，三者定位不同：

| 解析器 | 强项 | 注意 |
|--------|------|------|
| MinerU（默认） | PDF/图片/Office 全能，OCR 与表格提取强，支持 GPU 加速 | 模型较大，首次下载需要时间；v3.x 的 content list v2 输出已原生支持 |
| Docling | Office 文档与 HTML 优化，文档结构保留更好 | 解析结果同样进入 content_list 管道 |
| PaddleOCR | 专注 OCR 的轻量选择，适合图片与 PDF | 需额外 extras 与 paddlepaddle；Office/TXT/MD 会先转 PDF 再解析 |

MinerU 路径下还有细粒度参数可调：`lang`（OCR 语言优化，如 "ch"/"en"/"ja"）、`device`（cpu/cuda/npu/mps）、`start_page`/`end_page`（页码范围）、`formula`/`table`（公式与表格解析开关）、`backend`（pipeline 到 vlm-http-client 五种推理后端）。

---

## 八、与传统 RAG 的对比

| 对比 | 传统 RAG | RAG-Anything |
|------|---------|--------------|
| 处理内容 | 仅文本 | 文本 + 图片 + 表格 + 公式 + 音视频 |
| 知识组织 | 扁平向量索引 | 多模态知识图谱 |
| 跨模态理解 | 无 | 有（实体链接 + 关系映射）|
| 检索方式 | 纯向量相似度 | 向量 + 图遍历融合 |
| 适用文档 | 简单文本文档 | 论文、金融报告、技术文档等富媒体文档 |

代价也要说清楚：多模态实体抽取意味着每个图片、表格都要过一遍视觉模型或 LLM，索引成本远高于纯文本切分嵌入；`belongs_to` 层级与关系边会让图谱规模超过纯文本 RAG。文档量大、查询以纯文本为主时，这套开销未必划算。框架的缓解办法是：已完整处理的文档重复摄入时，默认跳过多模态处理，避免重复的 LLM 调用。

---

## 九、技术基础：LightRAG

RAG-Anything 基于 [LightRAG](https://github.com/HKUDS/LightRAG)——同属港大数据智能实验室的图 RAG 框架（EMNLP 2025），当前约 39,900 stars（2026-09-28 读数），支持增量更新、混合检索和 OpenAI 兼容接口。

两层关系值得注意：

- **RAG-Anything 是 LightRAG 的多模态扩展**：解析、模态处理、内容注入都发生在 RAG-Anything 层，实体与关系的存储检索复用 LightRAG。2026 年 6 月起，LightRAG 官方原生集成了 RAG-Anything，多模态 RAG 成为 LightRAG 的内置能力。
- **存储后端可插拔**：LightRAG 的 KV/向量/文档状态/图四类存储各自可选实现，默认文件存储，可切 PostgreSQL+pgvector、Neo4j、Milvus、Qdrant、Redis 等。从文件存储迁到 Neo4j 这类图库时，注意新后端不含旧的多模态实体——需要用 `force_multimodal_reprocess=True` 重跑已处理文档的多模态处理（对应 issue #154）。

---

## 十、任务流：一份论文 PDF 的完整流转

把机制串起来看一份典型输入（学术论文 PDF）怎么走完全程：

1. **摄入**：`process_document_complete(file_path="paper.pdf", parser="mineru", parse_method="auto")`。MinerU 解析版面，输出 content list——文本块带页码，图表带路径与题注，公式带 LaTeX。页眉、页脚、页码这类版面噪音默认剔除，不进图谱。
2. **路由**：content list 按类型分发，文本块与多模态元素并发处理。
3. **模态分析**：图片经视觉模型生成描述性题注；表格由结构化解释器识别数据模式；公式解析出 LaTeX 并挂接领域概念。
4. **入图**：每个多模态元素变成图谱实体，与正文实体建立跨模态关系；`belongs_to` 链记录"这张图属于第 3 节"，页码信息保留。
5. **查询**：读者问"实验部分哪个方法效果最好"，`hybrid` 检索同时命中正文陈述和结果表格实体；若问题涉及图（"图 4 的曲线说明了什么"），VLM 增强链路自动把该图喂给视觉模型，图文一起作答。
6. **复用**：解析产物（content list JSON）落盘在 `OUTPUT_DIR`。下次换 LLM 重建知识库时，直接 `insert_content_list()` 注入缓存结果，跳过解析与模态分析，不再花一遍视觉模型的钱。

---

## 十一、适用边界与采用建议

**值得采用**

- 文档以富媒体为主（论文、财报、技术手册），图表表格承载关键信息；
- 需要跨模态关联查询（"这句话引用的图"、"这组数据的来源章节"）；
- 团队已在用或计划用 LightRAG，想平滑获得多模态能力——2026 年 6 月后两者已官方打通。

**可以先等等**

- 文档基本纯文本，现有 text-only RAG 够用——多模态管道的索引成本是纯增量；
- 需要生产级多租户、权限隔离——RAG-Anything 专注摄取与检索本身，这类能力要在上层自建；
- 强离线/国产化环境——MinerU 模型下载与视觉模型依赖需先按 `docs/offline_setup.md` 评估，PaddleOCR 路线可作解析层备选。

**落地顺序**：先拿 `examples/` 里不需要 API key 的解析测试脚本验证文档类型覆盖，再跑一个最小端到端示例（几十页 PDF）确认视觉模型的描述质量满足预期，最后才考虑批量摄入与存储后端选型。视觉模型的描述质量直接决定图谱里多模态实体的成色，这一步值得多试几个模型。

---

## 十二、总结

RAG-Anything 针对的是文档中多模态内容在传统 RAG 里被丢弃的问题。港大数据智能实验室在 LightRAG 之上补齐了从文档解析、模态分析、知识图谱到检索的完整管道，v1.4.1 把模态范围从图文表公式扩到音视频，并支持跳过解析直接注入内容列表。23,440 stars，MIT 协议，PyPI 一键安装。

**相关链接：**

- GitHub：https://github.com/HKUDS/RAG-Anything
- 基于 LightRAG：https://github.com/HKUDS/LightRAG
- 论文：https://arxiv.org/abs/2510.12323

---

## 参考来源与口径说明

- 仓库元数据（stars 23,440、forks 2,729、MIT、v1.4.1 发布于 2026-09-02、main 分支最近提交 2026-09-15）为 GitHub API 2026-09-28 读数，star 数随时间增长，引用时以最新读数为准；
- 架构五阶段、四类模态处理器、三种解析器、查询方式、安装 extras、环境变量与默认值（音频/视频处理默认关闭、`WHISPER_MODEL` 默认 base、`parser` 默认 mineru）均对照仓库 README 与 `pyproject.toml`、`raganything/config.py` 源码核实，本文以 v1.4.1（main 分支）为口径；
- 开发者归属：HKUDS 为港大数据智能实验室（Data Intelligence Lab@HKU），论文作者 Zirui Guo、Xubin Ren、Lingrui Xu、Jiahao Zhang、Chao Huang（arXiv 2510.12323，2025-10-14 提交）；
- LightRAG 数据（约 39,900 stars、EMNLP 2025）与"2026 年 6 月原生集成"出自 LightRAG 仓库 README 与 RAG-Anything 的 News 章节；
- 音视频转写的行为描述（faster-whisper 本地转写、SceneDetect 场景切分、按时间戳合并）出自 README 与 `env.example` 内注释。
