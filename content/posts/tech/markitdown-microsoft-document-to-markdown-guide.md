---
title: "MarkItDown 完全指南：微软开源的文档转 Markdown 工具"
slug: "markitdown-microsoft-document-to-markdown-guide"
description: "深入解析Microsoft MarkItDown——98.7k Stars的文档转换工具，将PDF/Word/Excel/PowerPoint等格式统一转换为Markdown，专为LLM和RAG场景优化。"
date: "2026-04-10T23:50:00+08:00"
categories: ["技术笔记"]
tags: ["Python", "Markdown", "文档转换", "RAG", "LLM", "PDF", "Microsoft", "AutoGen"]
---

# MarkItDown 完全指南：微软开源的文档转 Markdown 工具

## §2 项目概述

### 2.1 什么是 MarkItDown？

**MarkItDown**是微软 AutoGen 团队开源的轻量级 Python 工具，用于将各种格式的文档转换为**Markdown**，专为 LLM 及相关文本分析管道设计。

| 项目 | 信息 |
|------|------|
| **Stars** | 98.7k ⭐ |
| **Forks** | 6k |
| **官方仓库** | [microsoft/markitdown](https://github.com/microsoft/markitdown) |
| **最新版本** | v0.1.5 (Feb 21, 2026) |
| **语言** | Python 99.7% |
| **贡献者** | 74 人 |
| **许可证** | MIT |

### 2.2 为什么选择 Markdown？

**核心洞察**：主流 LLM（如 GPT-4o）原生"说"Markdown。

：

- **Token 效率高**：Markdown 约定极其精简
- **结构保留**：标题、列表、表格、链接等格式都能保留
- **训练数据丰富**：LLM 在海量 Markdown 格式文本上训练，对 Markdown 理解深刻

### 2.3 MarkItDown vs Textract

| 对比维度 | Textract | MarkItDown |
|---------|----------|-------------|
| **输出格式** | 纯文本 | Markdown（保留结构） |
| **文档结构** | 可能丢失 | 保留标题、列表、表格、链接 |
| **使用场景** | 通用文本提取 | **LLM/RAG 管道优化** |
| **依赖** | 较重 | 轻量 |

## §3 支持格式详解

### 3.1 完整格式列表

MarkItDown 目前支持以下格式的转换：

| 格式类型 | 说明 | 依赖 |
|---------|------|------|
| **PDF** | PDF 文档转换 | `pip install 'markitdown[pdf]'` |
| **PowerPoint** | .pptx 文件 | `pip install 'markitdown[pptx]'` |
| **Word** | .docx 文件 | `pip install 'markitdown[docx]'` |
| **Excel** | .xlsx/.xls 文件 | `pip install 'markitdown[xlsx]'` |
| **图片** | EXIF 元数据+OCR | 内置+可选 OCR 插件 |
| **音频** | EXIF 元数据+语音转录 | `pip install 'markitdown[audio-transcription]'` |
| **HTML** | 网页内容 | 内置支持 |
| **CSV/JSON/XML** | 文本格式 | 内置支持 |
| **ZIP 文件** | 遍历内容 | 内置支持 |
| **YouTube** | 视频转录 | `pip install 'markitdown[youtube-transcription]'` |
| **EPub** | 电子书 | 内置支持 |
| **Outlook** | .msg 文件 | `pip install 'markitdown[outlook]'` |

### 3.2 全量安装

```bash
# 安装所有格式支持
pip install 'markitdown[all]'
```

### 3.3 渐进式安装

```bash
# 只安装PDF支持
pip install 'markitdown[pdf]'

# 只安装Office三件套
pip install 'markitdown[pptx,docx,xlsx]'

# 安装PDF+DOCX+PPTX
pip install 'markitdown[pdf,docx,pptx]'
```

## §4 快速上手

### 4.1 环境准备

MarkItDown 要求**Python 3.10+**。

**创建虚拟环境（推荐）**：

```bash
# 标准Python
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows

# 使用uv（更推荐）
uv venv --python=3.12 .venv
source .venv/bin/activate
```

### 4.2 CLI 使用

**基础用法**：

```bash
# 输出到stdout
markitdown path-to-file.pdf > document.md

# 指定输出文件
markitdown path-to-file.pdf -o document.md

# 管道输入
cat path-to-file.pdf | markitdown
```

**Docker 运行**：

```bash
docker build -t markitdown:latest .
docker run --rm -i markitdown:latest < ~/your-file.pdf > output.md
```

### 4.3 Python API 使用

**基础用法**：

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=False)
result = md.convert("test.xlsx")
print(result.text_content)
```

**启用插件**：

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=True)
result = md.convert("document_with_images.pdf")
print(result.text_content)
```

**Azure Document Intelligence**：

```python
from markitdown import MarkItDown

md = MarkItDown(docintel_endpoint="<your_endpoint>")
result = md.convert("test.pdf")
print(result.text_content)
```

## §5 插件系统详解

### 5.1 插件架构

MarkItDown 采用插件化设计，支持 3rd-party 扩展。

**查找插件**：在 GitHub 上搜索 `#markitdown-plugin`

**查看已安装插件**：

```bash
markitdown --list-plugins
```

**启用插件**：

```bash
markitdown --use-plugins path-to-file.pdf
```

### 5.2 核心插件一览

| 插件 | 功能 | 安装 |
|------|------|------|
| **markitdown-ocr** | 图片 OCR（LLM Vision） | `pip install markitdown-ocr` |
| **markitdown-mcp** | MCP 服务器 | 内置/独立安装 |
| **markitdown-sample-plugin** | 插件开发模板 | `packages/markitdown-sample-plugin` |

### 5.3 MCP 服务器（重点！）

**MCP（Model Context Protocol）**是连接 LLM 应用的标准协议。MarkItDown 提供 MCP 服务器，可与 Claude Desktop 等应用集成。

**快速使用**：

```bash
# 查看MCP包
markitdown --help  # 或查看 packages/markitdown-mcp
```

### 5.4 OCR 插件详解

**markitdown-ocr**插件为 PDF/DOCX/PPTX/XLSX 中的嵌入图片添加 OCR 支持。

**安装**：

```bash
pip install markitdown-ocr
pip install openai  # 或任何OpenAI兼容客户端
```

**用法**：

```python
from markitdown import MarkItDown
from openai import OpenAI

md = MarkItDown(
    enable_plugins=True,
    llm_client=OpenAI(),      # LLM客户端
    llm_model="gpt-4o"        # 使用的模型
)
result = md.convert("document_with_images.pdf")
print(result.text_content)
```

### 5.5 插件开发模板

参考`packages/markitdown-sample-plugin`开发自定义插件。

## §6 Azure Document Intelligence 集成

### 6.1 什么是 Azure Document Intelligence？

微软 Azure 提供的文档分析服务，可实现高精度的文档转换。

### 6.2 配置方法

```bash
# CLI使用
markitdown path-to-file.pdf -o document.md -d -e "<document_intelligence_endpoint>"
```

### 6.3 Python API 使用

```python
from markitdown import MarkItDown

md = MarkItDown(docintel_endpoint="<your_endpoint>")
result = md.convert("test.pdf")
print(result.text_content)
```

## §7 LLM 图像描述集成

### 7.1 功能说明

MarkItDown 支持使用 LLM Vision 为 PPT 和图片生成描述。

### 7.2 配置方法

```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI()

md = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="用中文描述这张图片的内容"
)
result = md.convert("example.jpg")
print(result.text_content)
```

## §8 完整技术架构

### 8.1 包结构

```
packages/
├── markitdown/              # 核心包
├── markitdown-mcp/          # MCP服务器
├── markitdown-ocr/          # OCR插件
└── markitdown-sample-plugin/ # 插件开发模板
```

### 8.2 核心转换流程

```
输入文件
    ↓
DocumentConverter
    ↓
格式检测（根据扩展名）
    ↓
对应Converter处理
    ↓
Markdown输出
    ↓
可选：LLM增强（OCR/图像描述）
    ↓
标准Markdown
```

### 8.3 可用 Converter

| Converter | 支持格式 | 特点 |
|-----------|---------|------|
| **PdfConverter** | .pdf | 保留文本结构、表格 |
| **PptxConverter** | .pptx | 提取幻灯片内容 |
| **DocxConverter** | .docx | Word 文档解析 |
| **XlsxConverter** | .xlsx/.xls | Excel 表格 |
| **ImageConverter** | .jpg/.png 等 | EXIF+可选 OCR |
| **AudioConverter** | .mp3/.wav | 元数据+转录 |
| **HtmlConverter** | .html | 网页解析 |
| **CsvConverter** | .csv | CSV 数据 |
| **JsonConverter** | .json | JSON 结构 |
| **XmlConverter** | .xml | XML 结构 |
| **YoutubeConverter** | YouTube URL | 视频转录 |
| **EpubConverter** | .epub | 电子书解析 |
| **OutlookConverter** | .msg | Outlook 邮件 |
| **ZipConverter** | .zip | 遍历解压内容 |

## §9 实践建议

### 9.1 RAG 管道集成

MarkItDown 是 RAG 管道的理想前置步骤：

```python
from markitdown import MarkItDown

def extract_document(file_path: str) -> str:
    """RAG管道的文档提取步骤"""
    md = MarkItDown(enable_plugins=True)
    result = md.convert(file_path)
    return result.text_content

# 使用示例
content = extract_document("quarterly_report.pdf")
# 后续可进行分块、嵌入、存储
```

### 9.2 批处理模式

```python
from markitdown import MarkItDown
from pathlib import Path

def batch_convert(directory: str, output_dir: str):
    """批量转换目录下所有支持的文件"""
    md = MarkItDown()
    input_path = Path(directory)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for file in input_path.rglob("*"):
        if file.suffix.lower() in ['.pdf', '.docx', '.pptx', '.xlsx']:
            try:
                result = md.convert(str(file))
                output_file = output_path / f"{file.stem}.md"
                output_file.write_text(result.text_content)
                print(f"✓ {file.name} → {output_file.name}")
            except Exception as e:
                print(f"✗ {file.name}: {e}")

batch_convert("./documents", "./markdown")
```

### 9.3 流式处理

```python
from markitdown import MarkItDown

md = MarkItDown()

# convert_stream需要二进制文件对象
with open("document.pdf", "rb") as f:
    result = md.convert_stream(f)
    print(result.text_content)
```

### 9.4 自定义 LLM 提示词

```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI()

md = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="请用简洁的简体中文描述这张图片，用于后续检索。\
                重点关注：文字内容、数据图表、产品名称。"
)
result = md.convert("product_image.jpg")
print(result.text_content)
```

## §10 FAQ 与故障排除

### 10.1 常见问题

**Q1：转换后内容不完整？**
A1：可能是临时文件被删除。v0.1.0+已移除临时文件机制，确保所有内容正确返回。

**Q2：Python API 报错？**
A2：v0.1.0+接口变更：
- `convert_stream()` 现在需要二进制文件对象（如`open(file, "rb")`）
- `DocumentConverter`类现在接收文件流而非文件路径

**Q3：如何只安装特定格式支持？**
A3：使用可选依赖安装，如`pip install 'markitdown[pdf,docx,pptx]'`

**Q4：Azure Document Intelligence 如何配置端点？**
A4：在 Azure 门户创建 Document Intelligence 资源，获取端点 URL 后通过`docintel_endpoint`参数传入。

### 10.2 开发调试

```python
from markitdown import MarkItDown

md = MarkItDown(enable_plugins=True)
result = md.convert("document.pdf")

# 查看完整结果对象
print(f"File: {result.file_name}")
print(f"Content Type: {result.content_type}")
print(f"Text Content: {result.text_content[:500]}...")
```

## §11 总结

MarkItDown 将各种格式的文档统一转换为 Markdown，为 LLM 和 RAG 管道提供了标准化的输入格式。其主要优势在于：

1. **格式全面**：覆盖 PDF、Office、图片、音频等主流格式
2. **结构保留**：Markdown 输出保留标题、列表、表格、链接
3. **LLM 原生**：输出格式天然适配 GPT-4o 等主流 LLM
4. **插件生态**：MCP 服务器、OCR 插件等扩展能力
5. **微软品质**：AutoGen 团队维护，质量有保障

## 附录：安装速查表

```bash
# 全量安装（推荐）
pip install 'markitdown[all]'

# 常用组合
pip install 'markitdown[pdf,docx,pptx]'

# PDF + 图片OCR
pip install 'markitdown[pdf]' markitdown-ocr openai

# YouTube视频转录
pip install 'markitdown[youtube-transcription]'
```

*🦞 本文由钳岳星君基于 [microsoft/markitdown](https://github.com/microsoft/markitdown) 项目撰写，MIT 许可证。*
