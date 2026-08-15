---
title: "MarkItDown 指南：微软开源的文档转 Markdown 工具"
slug: "markitdown-microsoft-document-to-markdown-guide"
github_repo: "microsoft/markitdown"
description: "深入解析 Microsoft MarkItDown——GitHub 17 万 Star 的文档转换工具，将 PDF/Word/Excel/PowerPoint 等格式统一转换为 Markdown，专为 LLM 和 RAG 场景优化。"
date: "2026-04-10T23:50:00+08:00"
categories: ["技术笔记"]
tags: ["Python", "Markdown", "RAG", "LLM", "PDF", "Microsoft"]
---

# MarkItDown 指南：微软开源的文档转 Markdown 工具

## §1 项目概述

### 1.1 什么是 MarkItDown？

MarkItDown 是微软 AutoGen 团队开源的轻量级 Python 工具，把各种格式的文档转换成 Markdown，服务对象是 LLM（大语言模型）和文本分析管道。

| 项目 | 信息 |
|------|------|
| **Stars** | 172K+（截至 2026 年 8 月） |
| **Forks** | 12.6K |
| **官方仓库** | [microsoft/markitdown](https://github.com/microsoft/markitdown) |
| **最新版本** | v0.1.7（2026-07-30） |
| **语言** | Python |
| **贡献者** | 81 人 |
| **许可证** | MIT |

数字会随时间变化，以仓库主页为准。

### 1.2 为什么转成 Markdown？

LLM 对 Markdown 的接受度天然高于裸文本。GPT-4o 这类主流模型在大量 Markdown 语料上训练过，能直接识别标题、列表、表格、链接的结构；同样的内容用 HTML 表达要消耗更多 token（词元），而 Markdown 用极少的标记就保留了结构。

一个直观的对比：把同一份财务报告丢给模型，扁平化文本会把表头和数据混在一起，模型要自己猜结构；转成 Markdown 表格后，检索和推理都更稳。

### 1.3 MarkItDown vs Textract

MarkItDown 常被拿来和 [textract](https://github.com/deanmalmgren/textract) 比较。两者都做文本提取，差别在输出：

| 对比维度 | Textract | MarkItDown |
|---------|----------|-------------|
| **输出格式** | 纯文本 | Markdown（保留结构） |
| **文档结构** | 可能丢失 | 保留标题、列表、表格、链接 |
| **定位** | 通用文本提取 | **LLM/RAG（检索增强生成）管道优化** |
| **依赖** | 较重 | 按需安装、轻量 |

需要说明边界：MarkItDown 的目标读者是文本分析工具，不是追求高保真的人类阅读场景。复杂版式、字体、配色这类视觉信息会被丢弃。

## §2 支持格式详解

### 2.1 格式列表

MarkItDown 目前支持以下格式（README 明确列出，另有一些社区扩展）：

| 格式类型 | 说明 | 依赖 |
|---------|------|------|
| **PDF** | 文本与表格提取 | `pip install 'markitdown[pdf]'` |
| **PowerPoint** | .pptx 文件 | `pip install 'markitdown[pptx]'` |
| **Word** | .docx 文件 | `pip install 'markitdown[docx]'` |
| **Excel** | .xlsx / .xls 文件 | `pip install 'markitdown[xlsx,xls]'` |
| **图片** | EXIF 元数据 + OCR | 内置 + 可选 OCR 插件 |
| **音频** | EXIF 元数据 + 语音转录 | `pip install 'markitdown[audio-transcription]'` |
| **HTML** | 网页内容 | 内置支持 |
| **CSV / JSON / XML** | 文本格式 | 内置支持 |
| **ZIP 文件** | 遍历内部内容 | 内置支持 |
| **YouTube** | 视频转录 | `pip install 'markitdown[youtube-transcription]'` |
| **EPub** | 电子书 | 内置支持 |
| **Outlook** | .msg 邮件 | `pip install 'markitdown[outlook]'` |

### 2.2 全量安装

```bash
# 安装所有格式支持
pip install 'markitdown[all]'
```

`[all]` 会装齐全部可选依赖。磁盘或依赖冲突敏感的场景，用下面的按需安装更稳妥。

### 2.3 渐进式安装

```bash
# 只装 PDF 支持
pip install 'markitdown[pdf]'

# 只装 Office 三件套
pip install 'markitdown[pptx,docx,xlsx]'

# PDF + DOCX + PPTX
pip install 'markitdown[pdf,docx,pptx]'
```

## §3 快速上手

### 3.1 环境准备

MarkItDown 要求 **Python 3.10+**，官方建议用虚拟环境隔离依赖：

```bash
# 标准 Python
python -m venv .venv
source .venv/bin/activate  # Linux / macOS
.venv\Scripts\activate     # Windows

# 用 uv 创建（装包时用 uv pip install）
uv venv --python=3.12 .venv
source .venv/bin/activate
```

### 3.2 CLI（命令行工具）使用

```bash
# 输出到 stdout
markitdown path-to-file.pdf > document.md

# 指定输出文件
markitdown path-to-file.pdf -o document.md

# 管道输入
cat path-to-file.pdf | markitdown
```

### 3.3 Python API（应用程序接口）使用

核心用法三行：

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("test.xlsx")
print(result.text_content)
```

`convert()` 接收文件路径、URL 或字节流，按扩展名自动路由到对应转换器。

## §4 插件系统

### 4.1 插件架构

MarkItDown 从 0.1.0 起引入插件机制，第三方能通过 Python entry point 扩展转换能力。插件默认关闭，装好后要显式启用。

```bash
# 查看已安装插件
markitdown --list-plugins

# 启用插件转换
markitdown --use-plugins path-to-file.pdf

# 查找社区插件：在 GitHub 搜 #markitdown-plugin
```

### 4.2 核心插件一览

| 插件 | 功能 | 安装 |
|------|------|------|
| **markitdown-ocr** | 图片 OCR（LLM Vision） | `pip install markitdown-ocr` |
| **markitdown-mcp** | MCP 服务器 | `pip install markitdown-mcp` |
| **markitdown-sample-plugin** | 插件开发模板 | 见 `packages/markitdown-sample-plugin` |

### 4.3 OCR 插件

`markitdown-ocr` 为 PDF、DOCX、PPTX、XLSX 里的嵌入图片添加 OCR，用 LLM Vision 提取文字，不需要额外的机器学习库或二进制依赖：

```bash
pip install markitdown-ocr
pip install openai  # 或任意 OpenAI 兼容客户端
```

```python
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(
    enable_plugins=True,
    llm_client=OpenAI(),
    llm_model="gpt-4o",
)
result = md.convert("document_with_images.pdf")
print(result.text_content)
```

注意：不传 `llm_client` 时插件仍会加载，但 OCR 会被静默跳过，退回内置转换器。

### 4.4 MCP 服务器

MCP（Model Context Protocol）是连接 LLM 应用的标准协议。官方 `markitdown-mcp` 包把 MarkItDown 暴露成一个 MCP 服务器，Claude Desktop 这类应用可以直接调用它读取任意文档。

```bash
pip install markitdown-mcp
markitdown-mcp --help
```

服务器暴露一个 `convert_to_markdown(uri)` 工具，可接收 `http:`、`https:`、`file:`、`data:` 形式的 URI。默认走 STDIO；加 `--http` 可开启 Streamable HTTP 与 SSE 传输，默认监听 `127.0.0.1:3001`。服务器不做认证，以当前用户权限读文件，不要把它暴露到不受信的网络。

## §5 Azure Document Intelligence 集成

### 5.1 什么时候用它

内置转换器离线运行，覆盖常规场景。碰到扫描版 PDF、复杂表格、多栏排版这类高精度需求，可以切到 Azure 的云端文档分析服务。

### 5.2 CLI 使用

```bash
markitdown path-to-file.pdf -o document.md -d -e "<document_intelligence_endpoint>"
```

### 5.3 Python API 使用

```python
from markitdown import MarkItDown

md = MarkItDown(docintel_endpoint="<your_endpoint>")
result = md.convert("test.pdf")
print(result.text_content)
```

端点从 Azure 门户创建 Document Intelligence 资源后获取。每次调用走 Azure API，会产生费用，别在本地测试时误用。

## §6 Azure Content Understanding 集成

### 6.1 它解决了什么

v0.1.6 起新增对 [Azure Content Understanding](https://learn.microsoft.com/azure/ai-services/content-understanding/) 的支持，覆盖 Document Intelligence 够不着的场景：

- **音视频**：内置转换器不支持视频，音频只有基础转录；Content Understanding 提供云端高质量方案
- **结构化字段提取**：预置或自定义 analyzer 抽取发票金额、合同条款等字段，输出为 YAML front matter
- **单 API 多模态**：一个 `cu_endpoint` 处理文档、图片、音频、视频，按文件类型自动路由

```bash
pip install 'markitdown[az-content-understanding]'
```

### 6.2 CLI 使用

```bash
markitdown path-to-file.pdf --use-cu --cu-endpoint "<content_understanding_endpoint>"
```

### 6.3 Python API 使用

```python
from markitdown import MarkItDown

# 零配置：按文件类型自动选择预置 analyzer
md = MarkItDown(cu_endpoint="<content_understanding_endpoint>")
result = md.convert("report.pdf")   # 文档 → prebuilt-document
result = md.convert("meeting.mp4")  # 视频 → prebuilt-video
result = md.convert("call.wav")     # 音频 → prebuilt-audio
print(result.markdown)
```

自定义 analyzer 抽领域字段：

```python
md = MarkItDown(
    cu_endpoint="<content_understanding_endpoint>",
    cu_analyzer_id="my-invoice-analyzer",
)
result = md.convert("invoice.pdf")
print(result.markdown)
# 输出带 YAML front matter 的提取字段：
# ---
# contentType: document
# fields:
#   VendorName: CONTOSO LTD.
#   InvoiceDate: '2019-11-15'
# ---
```

费用提示：路由到 Content Understanding 的格式，每次 `convert()` 都是一次计费调用。只希望 PDF 走云端时，用 `cu_file_types` 限定：

```python
from markitdown.converters import ContentUnderstandingFileType

md = MarkItDown(
    cu_endpoint="<content_understanding_endpoint>",
    cu_file_types=[ContentUnderstandingFileType.PDF],  # 只有 PDF 走 CU
)
```

### 6.4 三套转换怎么选

| 能力 | 内置转换器 | Document Intelligence | Content Understanding |
|------|-----------|----------------------|----------------------|
| **文档转换** | 离线、按格式提取 | 云端布局提取 | 云端多模态提取 |
| **结构化字段** | 不支持 | 集成未暴露 | YAML front matter |
| **音视频** | 无视频、基础音频 | 不支持 | 支持 |
| **成本** | 仅本地计算 | Azure API 计费 | Azure API 计费 |

## §7 LLM 图像描述

### 7.1 功能说明

给 PPTX 和图片文件提供 `llm_client`、`llm_model`，MarkItDown 会用视觉模型生成图片的文字描述。注意：目前只对这两类文件生效。

### 7.2 配置方法

```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI()

md = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="用中文描述这张图片的内容",
)
result = md.convert("example.jpg")
print(result.text_content)
```

`llm_client` 只要兼容 OpenAI 的客户端协议即可，不必局限官方 `openai` 包。

## §8 技术架构

### 8.1 包结构

```text
packages/
├── markitdown/               # 核心包
├── markitdown-mcp/           # MCP 服务器
├── markitdown-ocr/           # OCR 插件
└── markitdown-sample-plugin/ # 插件开发模板
```

### 8.2 核心转换流程

```text
输入文件（路径 / URL / 流）
    ↓
格式检测（扩展名 → MIME → 兜底分类）
    ↓
对应 Converter 处理
    ↓
Markdown 输出
    ↓
可选：LLM 增强（OCR / 图像描述）
```

### 8.3 内置 Converter

核心包的 `DocumentConverter` 注册了十余个内置转换器，按扩展名分发：

| 转换器 | 支持格式 | 提取内容 |
|-----------|---------|---------|
| PDF | .pdf | 文本与表格 |
| PowerPoint | .pptx | 幻灯片文本 |
| Word | .docx | 全文结构 |
| Excel | .xlsx / .xls | 表格数据 |
| 图片 | .jpg / .png 等 | EXIF + 可选 OCR |
| 音频 | .mp3 / .wav | 元数据 + 转录 |
| HTML | .html | 结构化文本 |
| CSV / JSON / XML | 对应格式 | 表格 / 结构 |
| YouTube | URL | 字幕转录 |
| EPub | .epub | 全书文本 |
| Outlook | .msg | 邮件内容 |
| ZIP | .zip | 遍历内部文件 |

## §9 实践建议

### 9.1 RAG 管道集成

MarkItDown 常作为 RAG 管道的第一步：把异构文档统一转成 Markdown，再交给分块、嵌入、检索：

```python
from markitdown import MarkItDown

def extract_document(file_path: str) -> str:
    """RAG 管道的文档提取步骤"""
    md = MarkItDown(enable_plugins=True)
    result = md.convert(file_path)
    return result.text_content

content = extract_document("quarterly_report.pdf")
```

### 9.2 批处理模式

```python
from markitdown import MarkItDown
from pathlib import Path

def batch_convert(directory: str, output_dir: str) -> None:
    """批量转换目录下所有支持的文件"""
    md = MarkItDown()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for file in Path(directory).rglob("*"):
        if file.suffix.lower() in [".pdf", ".docx", ".pptx", ".xlsx"]:
            try:
                result = md.convert(str(file))
                (output_path / f"{file.stem}.md").write_text(result.text_content)
                print(f"ok: {file.name}")
            except Exception as e:
                print(f"fail: {file.name}: {e}")

batch_convert("./documents", "./markdown")
```

### 9.3 流式处理

`convert_stream()` 从 v0.1.0 起要求二进制文件对象（0.0.x 曾接受文本流，是破坏性变更）：

```python
from markitdown import MarkItDown

md = MarkItDown()
with open("document.pdf", "rb") as f:
    result = md.convert_stream(f)
    print(result.text_content)
```

### 9.4 安全注意事项

README 明确提示：MarkItDown 以当前进程权限执行 I/O，行为和 `open()` / `requests.get()` 一样。**不要直接把不受信的输入喂给它**——托管服务里用户上传的文件可能指向内网地址或元数据服务。

优先调用最窄的 API：只处理本地文件用 `convert_local()`，只处理字节流用 `convert_stream()`，而不是一律用权限宽松的 `convert()`。

## §10 FAQ 与故障排除

**Q1：转换后内容不完整？**
A1：v0.1.0 起移除了临时文件机制，`DocumentConverter` 改为直接读文件流，内容应完整返回。若仍有缺失，先确认文件本身可被读取。

**Q2：`convert_stream()` 报错？**
A2：确认传的是二进制对象（`open(file, "rb")` 或 `io.BytesIO`）。0.0.x 版本接受的文本流已经不再支持。

**Q3：只想装特定格式？**
A3：用可选依赖，如 `pip install 'markitdown[pdf,docx,pptx]'`。格式与依赖对应关系见 §2.1 表格。

**Q4：Azure 端点怎么配置？**
A4：在 Azure 门户创建 Document Intelligence 或 Content Understanding 资源，拿到端点后分别传给 `docintel_endpoint` 或 `cu_endpoint`。注意两者是独立的云服务，各有各的计费。

**Q5：OCR 没生效？**
A5：确认装了 `markitdown-ocr` 并在 `MarkItDown()` 里传了 `enable_plugins=True` 和 `llm_client`。缺任一条件 OCR 都会静默跳过。

## §11 总结

MarkItDown 解决的核心问题：把 PDF、Office、图片、音频等异构文档统一转成 Markdown，直接喂给 LLM 或 RAG 管道。三个特点是：格式覆盖广、依赖按需安装、输出保留结构（标题、列表、表格、链接不丢）。

局限同样要清楚：复杂排版的 PDF 转换精度有限，追求高保真应评估 Azure Document Intelligence 或 Content Understanding；OCR 和云端转换依赖外部服务，有额外成本与延迟。

判断依据就一条——场景是「批量文档 → Markdown → LLM 处理」，MarkItDown 是门槛最低的选择；对转换精度或音视频字段提取有硬性要求，再引入 Azure 服务。

## 附录：安装速查表

```bash
# 全量安装
pip install 'markitdown[all]'

# 常用组合
pip install 'markitdown[pdf,docx,pptx]'

# PDF + 图片 OCR
pip install 'markitdown[pdf]' markitdown-ocr openai

# Azure Document Intelligence
pip install 'markitdown[az-doc-intel]'

# Azure Content Understanding
pip install 'markitdown[az-content-understanding]'

# YouTube 视频转录
pip install 'markitdown[youtube-transcription]'
```

## 附录：术语表

| 术语 | 含义 |
|------|------|
| **LLM** | 大语言模型，本文指 GPT-4o 这类生成式模型 |
| **RAG** | 检索增强生成，先检索再生成的问答/处理管道 |
| **Token** | 词元，模型处理文本的最小单位 |
| **CLI** | 命令行工具 |
| **API** | 应用程序接口 |
| **MCP** | 模型上下文协议，LLM 应用与外部工具互通的协议 |
| **OCR** | 光学字符识别，从图片中提取文字 |

*本文基于 [microsoft/markitdown](https://github.com/microsoft/markitdown) 项目（v0.1.7）撰写，MIT 许可证。版本、Star 等数据随项目演进，以仓库主页为准。*
