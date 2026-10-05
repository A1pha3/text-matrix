---
title: "pdf-inspector：用 Rust 在毫秒级判定 PDF 该不该走 OCR"
date: 2026-08-11T03:22:16+08:00
lastmod: 2026-10-04
slug: "firecrawl-pdf-inspector-rust-pdf-classification"
github_repo: "firecrawl/pdf-inspector"
source_key: "gh:firecrawl/pdf-inspector"
description: "pdf-inspector 是 Firecrawl 开源的 Rust PDF 分类与文本提取库，默认采样 8 页内容流，在 10-50 毫秒内判断 PDF 是文本型、扫描型、图片型还是混合型，把文本型 PDF 直接转为 Markdown，并从 v1.15 起内置选择性 OCR 兜底。本文基于 2026-10-04 的 v1.25.2 源码与文档。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "PDF处理", "Firecrawl", "文本提取", "OCR"]
---

## 核心判断

PDF 处理管线里最浪费的操作，是把一个天生自带文本层的 PDF 送进 OCR 引擎——花几秒等结果，还平白引入识别误差。pdf-inspector 解决的问题很明确：**在调用 OCR 之前，先用十几到几十毫秒判明这个 PDF 到底需不需要 OCR**。按 Firecrawl 的统计，实际文档里约 54% 的 PDF 自带文本层，可以本地直接提取，根本不该进 OCR 队列。

这个判断的底层方法不依赖机器学习模型。PDF 的内容流本质上是一串绘制指令，pdf-inspector 只解析其中的两类操作符——`Tj`/`TJ` 表示绘制文字，`Do` 表示引用图片——按页面统计它们的有无与密度，从而把 PDF 归为 `TextBased`、`Scanned`、`ImageBased` 或 `Mixed` 四类，并附带置信度与逐页 OCR 路由建议。分类只读内容流操作符，不做渲染，也不跑模型。

值得注意的演进是：本文初版发表一周后（8 月 17 日的 v1.15.0），项目把"OCR 兜底"从调用方的责任变成了自己的内置能力——Python 和 Node 包现在自带选择性 OCR（本地推理 PP-OCRv6 Small），缺文本层的页就地渲染送 OCR，干净页完全不加载 OCR 运行时。本文按 2026-10-04 的 v1.25.2 源码与文档整理。

阅读本文你会弄明白三件事：分类为什么可以用几十毫秒完成、文本提取怎样还原出结构化 Markdown，以及这个 benchmark 究竟说明了什么、不能说明什么。

## 系统地图

pdf-inspector 的处理管线分成两层：**分类器（detector）** 和 **提取器（extractor）**。文档只加载一次，两层共享同一份解析结果，避免重复读文件。

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
              ├─► tables   → 矩形检测(union-find) + 启发式检测 → 网格分格 → Markdown 表格
              └─► markdown → 标题/列表/代码块/表格 → 最终 Markdown
```

关键设计取舍在于 detector 不做完整文档解析，只读 xref 表和页面树，按采样策略扫描内容流。这让 300+ 页的 PDF 也能在毫秒级完成分类。分类器与提取器虽然是两层，但共享同一份解析结果——这也是它能表现出"先判断、再提取"这一流畅动作的前提。

## 分类机制详解

### 为什么操作符能判断类型

PDF 页面内容流是一条操作符指令序列，PDF 阅读器按指令逐条执行来绘制页面。pdf-inspector 借助这一点，只统计两类指令：

- **文本操作符 `Tj`/`TJ`**：代表页面里有文字绘制指令，说明页面内嵌了文本层，文字可直接读出。
- **图像操作符 `Do`**：代表页面引用了图像对象，很可能是一整页被扫描成图片的扫描页。

分类逻辑因此非常朴素：一个页面如果内容流里有充足的文本操作符，判为文本页；几乎没有文本操作符却有大量图像操作符，则是扫描页。这种"只读指令、不渲染页面"的做法，正是几十毫秒内出结果的原因——它不需要真的把 PDF 画出来。

朴素不等于没有调参空间。默认配置里有三个常量在起作用（`src/detector.rs` 的 `DetectionConfig::default`）：每页至少要有 3 个文本操作符才算文本页（`min_text_ops_per_page: 3`），全文文本页占比达到 60% 才判 `TextBased`（`text_page_ratio_threshold: 0.6`），再加上决定扫哪些页的采样策略。源码里都查得到，调用方也可以按自己的语料改。

### 采样策略：默认值变过一次

不同场景对"快"和"准"的需求不同。pdf-inspector 提供四种 `ScanStrategy`：

| 策略 | 行为 | 适用场景 |
|------|------|----------|
| `Sample(n)`（**当前默认**，`Sample(8)`） | 均匀采样 n 个页面（首、尾、中间） | 通用默认；超大 PDF 也够快 |
| `EarlyExit` | 扫描所有页面，遇到第一个非文本页即停止 | 确定语料几乎全是文本型、要最快路由 |
| `Full` | 扫描所有页面，不提前退出 | 精确区分 Mixed 和 Scanned |
| `Pages(vec)` | 只扫描指定页号 | 调用方已知需检查的页面 |

默认值值得单独说一句。文章写作时（8 月）默认还是 `EarlyExit`，9 月改成了 `Sample(8)`，官方理由写在源码注释里：EarlyExit 对"图片封面 + 文本正文"的 PDF（典型如年报）过于激进——第一页就是封面图，直接提前退出，整本被误判。采样 8 页则天然免疫这种结构。有意思的是 `detector.rs` 里 `EarlyExit` 的文档注释仍写着 "current default"，注释落后于同文件 80 行外的默认值实现——读源码时以 `DetectionConfig::default()` 为准。

### 逐页 OCR 路由

分类结果不只是"这个 PDF 是什么类型"，还包含 `pages_needing_ocr`——一份具体页号列表，指出哪些页面缺少文本层、需要走 OCR。这对 Mixed 型 PDF（部分页是文本、部分页是扫描）尤其关键：不必整篇送 OCR，只对缺文本层的页码走。一个 100 页的合同如果只有最后 5 页是盖章扫描件，需要 OCR 的就只有那 5 页。

## 文本提取与 Markdown 转换

对判为 `TextBased` 或 `Mixed` 的 PDF，pdf-inspector 直接提取文本并转为结构化 Markdown。

### 提取能力

| 能力 | 实现方式 |
|------|----------|
| 位置感知 | 记录每个文本项的 X/Y 坐标、字体信息；旋转文本（页边章、图表轴标题）保留轴对齐框并报告 `rotation` 角度 |
| 多栏检测 | 基于位置聚类识别报纸式分栏，恢复顺序阅读 |
| CID 字体 | ToUnicode CMap 解码 Type0/Identity-H 字体 |
| 编码问题标记 | 自动标记损坏的字体编码，供调用方回退 OCR |
| RTL 支持 | 阿拉伯语、希伯来语等从右到左文本（内置 Unicode 双向算法） |

坐标信息不是可有可无的元数据：没有它，多栏文档的文本按内容流顺序拼出来后，左边一栏的第一行会和右边一栏的第一行混在一起，句子彻底乱掉。有了坐标，提取器才能按阅读顺序重排行。

### Markdown 结构识别

转换器通过字体大小比率识别标题层级（H1-H4），通过字体名识别粗体/斜体，通过等宽字体名（Courier、Consolas、JetBrains Mono 等）检测代码块。表格检测走两条互补路径：一条从 PDF 绘图操作里找单元格矩形（union-find 合并），适合有线表格；一条基于文本对齐的启发式检测，适合无线表格；两条路都汇入同一个网格划分器再输出 Markdown。财务、发票、法律文档里跨页延续的表格也单独做了处理。

返回值里的结构信息比"一段 Markdown"多得多：`pages_with_tables`、`pages_with_columns`、`is_complex_layout`、`has_encoding_issues`，以及每个字体 CMap 缺口的明细（`cmap_gaps`）——调用方可以在拿到 Markdown 的同时就知道哪几页布局复杂、哪几页编码可疑，据此决定要不要人工复核或回退 OCR。

## Benchmark：测什么、能说明什么

pdf-inspector 在 [opendataloader-bench](https://github.com/opendataloader-project/opendataloader-bench) 语料库（200 个 PDF）上与同类工具对比，测试环境为 Apple M4 Pro，OCR 全程关闭——只测原生文本提取能力。

| 引擎 | 总分 | 阅读顺序 (NID) | 表格 (TEDS) | 标题 (MHS) | 200 文档耗时 |
|------|------|-----------------|-------------|------------|--------------|
| pdf-inspector | **0.875** | **0.915** | **0.814** | 0.788 | **0.470s** |
| liteparse | 0.873 | 0.913 | 0.693 | **0.811** | 0.750s |
| opendataloader | 0.831 | 0.902 | 0.489 | 0.739 | 2.569s |
| pymupdf4llm | 0.735 | 0.886 | 0.401 | 0.424 | 17.117s |
| markitdown | 0.589 | 0.844 | 0.273 | 0.000 | 16.165s |

先说要怎么读这张表。它的测量口径是"原生文本 PDF、关闭 OCR、只收不做模型化 PDF 解析的本地引擎"，比的是本地直接提取时的质量和速度，不涉及扫描识别能力。数据 2026 年 7 月 31 日刷新，当时的引擎版本是 pdf-inspector 0.2.6、LiteParse 2.10.1、OpenDataLoader 2.2.1、PyMuPDF4LLM 0.2.0、MarkItDown 0.1.5；耗时取五轮交替完整跑语料的中位数（排除预热轮），每个解析器单进程顺序处理。在这个口径下，pdf-inspector 的总分、阅读顺序、表格三项领先，速度是 pymupdf4llm 的约 36 倍（17.117s ÷ 0.470s）。

需要清醒的是这张表**不能**推出什么：它没有覆盖扫描型文档（OCR 已关闭），也说明不了复杂版面——嵌套表格、数学公式的识别效果；语料库以报告、论文、财务文档为主。"快而准"的结论只在原生文本型 PDF 上成立，别把它当成对扫描件的性能承诺。

官方把完整的解析器配置、逐文档预测和评测器输出放在了[可复现结果分支](https://github.com/firecrawl/opendataloader-bench/tree/abi/pdf-parser-benchmark-results)上，还提供了成对基准工具（`docs/benchmarking.md`）让你在完全相同的语料和评测器版本上对比自己的两个构建——要质疑或复测这张表，路径是现成的。

## 一个请求如何流过系统

以 Python 调用 `process_pdf("report.pdf")` 为例：

1. **加载文档**：`load_document_from_path` 解析 PDF 结构（xref 表、页面树），加载完成后 detector 和 extractor 共享这个文档对象，不再重复读文件。
2. **分类**：detector 按默认的 `Sample(8)` 策略采样 8 个页面，统计文本/图像操作符。假设这是一本普通文本报告，返回 `PdfType::TextBased` + 高置信度 + `pages_needing_ocr: []`。
3. **提取**：类型是 TextBased，进入 extractor。解析字体编码，遍历内容流生成 TextItems，检测到双栏布局，按阅读顺序重排行。
4. **表格检测**：发现页面中有矩形绘图操作，触发 rectangle-based 检测，识别出财务表格结构。
5. **Markdown 生成**：字体统计确定标题层级，等宽字体检测到代码块，表格转为 Markdown，最终输出完整 Markdown 字符串。

分类这一步通常落在 10-50 毫秒。官方给的整体目标是文本型 PDF 本地处理（分类 + 提取 + Markdown）控制在 200 毫秒内。全程无网络请求、无 ML 推理、无 GPU 排队——这也是它能比 OCR 管道快出两三个数量级的原因。

## 什么时候该回退 OCR

即便不用内置 OCR，分类的边界也需要说得更细一点。判定是"TextBased"不等于提取结果一定干净：整页缺失文本会被判为扫描页交给 OCR，而文本层本身损坏的场景（例如乱码文本、GID 编码字体）则会返回低质量信号。这类页面会用 `needs_ocr` 标记出来，甚至标注 `suspected_garbled_text` 作为原因，由调用方决定是否兜底送 OCR。所以合理用法不是"分类文本型就绝不 OCR"，而是：**先信本地提取的信号，被标记为不可靠的页码再回退 OCR**。`ocr_reasons_by_page` 字段把每页需要 OCR 的机器可读原因一并列出，路由决策可以完全自动化。

## OCR 现在长在管线里

本文初版发表时，pdf-inspector 还只做分类和提取，OCR 完全交给调用方。一周后的 v1.15.0 改变了这一点：Python 和 Node 包内置了**选择性 OCR**——只对被路由到 OCR 的页面渲染图像并本地推理，干净页连 OCR 运行时都不加载。

用法上是一条新入口：

```python
import pdf_inspector

ocr = pdf_inspector.process_pdf_with_ocr("document.pdf")
print(ocr.pages_routed_to_ocr)   # 实际走了 OCR 的页码
```

`mode` 参数三档：`off`（等同纯提取）、`auto`（默认，仅对缺文本层的页 OCR）、`force`（全部页 OCR）。OCR 结果带逐页来源与置信度，JSON 输出信封有版本号，还会给出"建议送云端文档管线"的页码——本地小模型搞不定的页，官方倾向于承认并转给你自己的托管管线，而不是硬凑一个低质量结果。

几个部署细节值得知道：

- 模型是 PP-OCRv6 Small（PaddleOCR 系，含检测模型、识别模型、字符字典三件），首次用到时才下载，缓存位置可用 `PDF_INSPECTOR_MODEL_CACHE` 指定；气隙环境可以预填模型目录再以 `offline=True`（Python）或 `--ocr-offline --ocr-model-dir`（CLI）运行。
- 渲染依赖 PDFium、推理依赖 ONNX Runtime，这两个外部库只在真的有页被路由到 OCR 时才需要安装。也就是说，**默认路径（纯提取）依然零外部依赖**，OCR 是"按页付费"的可选层。
- Rust 和 CLI 用户走编译期开关：`cargo install pdf-inspector --features ocr --bin pdf2md`，运行时 `pdf2md scan.pdf --ocr auto`。

这改变了上一节的答案：以前"缺文本层的页怎么办"是"你自己接一个 OCR 引擎"，现在至少对扫描页不多的混合语料，答案可以是"打开 auto 模式就行"。要不要仍用独立 OCR 服务，判断依据变成了规模（大批量时专用 OCR 集群可能更划算）和质量要求（PP-OCRv6 Small 是本地小模型，复杂版面的上限摆在那里）。

## 多语言绑定

pdf-inspector 的核心是 Rust 库，同时提供三种绑定：

- **Python**（PyO3）：`pip install pdf-inspector`，`process_pdf("doc.pdf")` 返回类型 + Markdown
- **Node.js**（napi-rs）：`npm install @firecrawl/pdf-inspector`，同步 API 之外提供异步变体（在 libuv 线程池运行，不阻塞事件循环）；OCR 入口 `processPdfWithOcr` 同样是异步的
- **Browser WASM**：`npm install @firecrawl/pdf-inspector-wasm`，同一套 Rust 解析器在浏览器和 Web Worker 中运行，内置 CMap 数据随包分发，无服务端请求；不含 OCR

Node 侧的 API 面比"转 Markdown"宽：`extractTextWithPositions`（带坐标文本）、`extractTablesWithStructureAuto`（矩形+启发式自动选择的表格提取）、`extractStructureElements`（带 MCID 的结构元素）等，适合做精细后处理的场景。

## 怎么决定要不要用

什么时候值得上手：你有一个要批量过 PDF 的文档管线，且 OCR 是成本或延迟瓶颈；处理的以报告、论文、发票、法律合同这类原生文本型 PDF 为主；或者你在浏览器端解析 PDF、不想把文件上传到服务端。对这几类，pdf-inspector 可以直接降低管道延迟与 OCR 支出。

什么时候不必上：语料里几乎全是扫描件或图片型文档（它的设计目标就是跳过这类，内置 OCR 也只是兜底小模型）；需要解析数学公式、手写体或复杂嵌套表格；需要从 PDF 中抽取嵌入图片。遇到这三种场景，再叠加一个更强的 OCR/版面解析引擎来兜底更合适。它适合作为管道里的"分类 + 提取 + 兜底路由"枢纽，而不是能覆盖一切 PDF 的单体工具。

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
print(result.pdf_type)    # "text_based" / "scanned" / "image_based" / "mixed"
print(result.markdown)    # Markdown 字符串，扫描件与图片件为 None
print(result.pages_needing_ocr)  # 缺文本层的页码（1 起始）
```

Rust 下可以只做分类、不做提取，用 `detect_pdf` 拿到类型与逐页标记，再决定是否走提取：

```rust
use pdf_inspector::detect_pdf;

let info = detect_pdf("document.pdf")?;
match info.pdf_type {
    pdf_inspector::PdfType::TextBased => {
        // 本地直接提取，快而且免费
    }
    _ => {
        // 交给 OCR 服务；info.pages_needing_ocr 指明具体页码
    }
}
```

CLI 工具包括 `pdf2md`（转 Markdown）和 `detect_pdf`（仅分类），支持页面选择、JSON 输出（附带文档信息字典：标题、作者、生成器、创建/修改日期）、紧凑模式等参数。

项目基于 MIT 协议开源（当前 19,472★，2026-10-04 读数），主要语言 Rust。PDF 对象解析只依赖 `lopdf`，字体解析、双向文本等辅助能力各由一个小的专职 crate 承担；默认构建无 ML 模型、无外部服务，OCR 路径的外部依赖（PDFium、ONNX Runtime、模型文件）只在真的有页被路由到 OCR 时才登场。
