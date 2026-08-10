---
title: "pdf-inspector：用 Rust 在 50 毫秒内判定 PDF 该不该走 OCR"
date: 2026-08-11T03:22:16+08:00
slug: "firecrawl-pdf-inspector-rust-pdf-classification"
github_repo: "firecrawl/pdf-inspector"
source_key: "gh:firecrawl/pdf-inspector"
description: "pdf-inspector 是 Firecrawl 开源的 Rust PDF 分类与文本提取库，通过采样内容流中的文本/图像操作符，在毫秒级判断 PDF 是文本型、扫描型还是混合型，并将文本型 PDF 直接转为 Markdown，省去不必要的 OCR 开销。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "PDF处理", "Firecrawl", "文本提取", "OCR"]
---

## 核心判断

PDF 处理管线里最浪费的事，是把一个天生就有文本层的 PDF 送进 OCR 引擎——花几秒等结果，还引入识别误差。pdf-inspector 解决的问题很明确：**在调用 OCR 之前，先用几十毫秒判定这个 PDF 到底需不需要 OCR**。根据 Firecrawl 的统计，约 54% 的 PDF 其实自带文本层，完全可以本地直接提取。

这个判断的底层方法不依赖机器学习模型，而是解析 PDF 内容流中的操作符（`Tj`/`TJ` 表示文本绘制，`Do` 表示图像引用），按页面统计文本操作符的有无和密度，输出 `TextBased`、`Scanned`、`ImageBased` 或 `Mixed` 四种类型，附带置信度和逐页 OCR 路由建议。

## 系统地图

pdf-inspector 的处理管线分两层：**分类器（detector）** 和 **提取器（extractor）**。文档只需加载一次，两层共享同一份解析结果。

```
PDF bytes
  │
  ├─► detector → PdfType (TextBased / Scanned / ImageBased / Mixed)
  │                 + pages_needing_ocr (逐页 OCR 路由)
  │
  └─► extractor
        ├─ fonts           → 字体宽度、编码
        ├─ content_stream  → 遍历 PDF 操作符 → TextItems + PdfRects
        ├─ xobjects        → Form XObject 文本、图像占位
        ├─ links           → 超链接、AcroForm 字段
        └─ layout          → 列检测 → 行分组 → 阅读顺序
              │
              ├─► tables   → 矩形检测 + 启发式检测 → Markdown 表格
              └─► markdown → 标题/列表/代码块/表格 → 最终 Markdown
```

关键设计取舍：detector 不做完整文档解析，只读 xref 表和页面树，按采样策略扫描内容流。这意味着 300+ 页的 PDF 也能在毫秒级完成分类。

## 分类机制详解

### 操作符检测

PDF 内容流是一系列操作符指令。pdf-inspector 关注两类：

- **文本操作符 `Tj`/`TJ`**：表示页面中有文字绘制指令，说明 PDF 内嵌了文本层。
- **图像操作符 `Do`**：表示页面引用了图像对象（可能是扫描页的整页图片）。

分类逻辑：如果一个页面的内容流里有充足的文本操作符，判定为文本页；如果几乎没有文本操作符但有大量图像操作符，判定为扫描页。

### 扫描策略

不同场景对"快"和"准"的需求不同。pdf-inspector 提供四种 `ScanStrategy`：

| 策略 | 行为 | 适用场景 |
|------|------|----------|
| `EarlyExit`（默认） | 扫描所有页面，遇到第一个非文本页即停止 | 快速路由文本型 PDF 到直接提取 |
| `Full` | 扫描所有页面，不提前退出 | 精确区分 Mixed 和 Scanned |
| `Sample(n)` | 均匀采样 n 个页面（首、尾、中间） | 超大 PDF，速度优先 |
| `Pages(vec)` | 只扫描指定页号 | 调用方已知需检查的页面 |

### 逐页 OCR 路由

分类结果不只是"这个 PDF 是什么类型"，还包括 `pages_needing_ocr`——一个具体页号列表，指出哪些页面缺乏文本层需要 OCR。这对 Mixed 型 PDF（部分页文本、部分页扫描）特别有用：不必整文档走 OCR，只对需要的页面走。

## 文本提取与 Markdown 转换

对于判定为 TextBased 或 Mixed 的 PDF，pdf-inspector 直接提取文本并转为结构化 Markdown。

### 提取能力

| 能力 | 实现方式 |
|------|----------|
| 位置感知 | 记录每个文本项的 X/Y 坐标、字体信息 |
| 多栏检测 | 基于位置聚类识别报纸式分栏，恢复顺序阅读 |
| CID 字体 | ToUnicode CMap 解码 Type0/Identity-H 字体 |
| RTL 支持 | 阿拉伯语、希伯来语等从右到左文本 |

### Markdown 结构识别

转换器通过字体大小比率识别标题层级（H1-H4），通过字体名识别粗体/斜体，通过等宽字体名（Courier、Consolas、JetBrains Mono 等）检测代码块。表格检测有两条路径：基于 PDF 绘图操作中的矩形结构，以及基于文本对齐的启发式检测。

## Benchmark：测什么、能说明什么

pdf-inspector 在 [opendataloader-bench](https://github.com/opendataloader-project/opendataloader-bench) 语料库（200 个 PDF）上与同类工具对比，测试环境为 Apple M4 Pro，OCR 全程关闭——只测原生文本提取能力。

| 引擎 | 总分 | 阅读顺序 (NID) | 表格 (TEDS) | 标题 (MHS) | 200 文档耗时 |
|------|------|-----------------|-------------|------------|--------------|
| pdf-inspector | **0.875** | **0.915** | **0.814** | 0.788 | **0.470s** |
| liteparse | 0.873 | 0.913 | 0.693 | **0.811** | 0.750s |
| opendataloader | 0.831 | 0.902 | 0.489 | 0.739 | 2.569s |
| pymupdf4llm | 0.735 | 0.886 | 0.401 | 0.424 | 17.117s |
| markitdown | 0.589 | 0.844 | 0.273 | 0.000 | 16.165s |

**这个 benchmark 说明了什么**：在原生文本型 PDF 上，pdf-inspector 的综合提取质量（阅读顺序、表格结构、标题层级）领先，且处理速度比 pymupdf4llm 快 36 倍。

**不能推出什么**：这个 benchmark 不包含扫描型 PDF（OCR 关闭），也不能说明对复杂版面（多栏嵌套表格、数学公式）的识别效果——语料库以报告、论文、财务文档为主。

## 多语言绑定

pdf-inspector 的核心是 Rust 库，同时提供三种绑定：

- **Python**（PyO3）：`pip install pdf-inspector`，`process_pdf("doc.pdf")` 返回类型 + Markdown
- **Node.js**（napi-rs）：`npm install @firecrawl/pdf-inspector`，支持异步变体不阻塞事件循环
- **Browser WASM**：`npm install @firecrawl/pdf-inspector-wasm`，同一套 Rust 解析器在浏览器和 Web Worker 中运行，内嵌 CMap，无服务端请求

CLI 工具包括 `pdf2md`（转 Markdown）和 `detect-pdf`（仅分类），支持页面选择、JSON 输出、紧凑模式等参数。

## 一个请求如何流过系统

以 Python 调用 `process_pdf("report.pdf")` 为例：

1. **加载文档**：`load_document_from_path` 解析 PDF 结构（xref 表、页面树），加载完成后 detector 和 extractor 共享这个文档对象。
2. **分类**：detector 按 `EarlyExit` 策略遍历页面内容流，采样文本/图像操作符，返回 `PdfType::TextBased` + 置信度 0.95 + `pages_needing_ocr: []`。
3. **提取**：因为类型是 TextBased，进入 extractor。解析字体编码，遍历内容流生成 TextItems，检测到双栏布局，按阅读顺序重排行。
4. **表格检测**：发现页面中有矩形绘图操作，触发 rectangle-based 检测，识别出财务表格结构。
5. **Markdown 生成**：字体统计确定标题层级，等宽字体检测到代码块，表格转为 Markdown 格式，最终输出完整 Markdown 字符串。

整个过程在 Apple M4 Pro 上约 2-3 毫秒（单文档），无网络请求，无 ML 推理。

## 适用边界

**适合**：

- 需要快速判断 PDF 是否需要 OCR 的文档处理管线
- 批量处理原生文本型 PDF（报告、论文、发票、法律文档）并转为 Markdown
- 浏览器端 PDF 解析（WASM 绑定），不想把文件上传到服务端
- 对处理速度敏感、希望跳过不必要 OCR 的场景

**不适合**：

- 扫描型 PDF（需要 OCR，pdf-inspector 的设计目标就是跳过这类文档）
- 需要解析数学公式、手写体或复杂嵌套表格的文档
- 需要从 PDF 中提取嵌入图片的场景（pdf-inspector 关注文本层）

## 安装与快速开始

```bash
# Python
pip install pdf-inspector

# Node.js
npm install @firecrawl/pdf-inspector

# Rust
cargo add pdf-inspector

# CLI
cargo install pdf-inspector
```

```python
import pdf_inspector

result = pdf_inspector.process_pdf("document.pdf")
print(result.pdf_type)    # "text_based"
print(result.markdown)    # Markdown 字符串
```

项目基于 MIT 协议开源，当前版本 0.2.6，Stars 14.3K，主要语言 Rust，活跃维护中（最近提交在 2026-08-10）。
