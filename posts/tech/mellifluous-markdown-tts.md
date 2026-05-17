---
title: "mellifluous：本地运行的 Markdown TTS 工具，让文档自己"出声""
date: "2026-05-17T12:05:30+08:00"
slug: "mellifluous-markdown-tts-apple-silicon"
description: "mellifluous 是一个运行在 macOS Apple Silicon 上的本地 Markdown 转语音工具，基于 Qwen3-TTS 和 MLX 框架，支持语音克隆，可以把 Markdown 文档解析为结构化朗读节奏，支持公式、代码、链接等内联内容的语音处理。"
draft: false
categories: ["技术笔记"]
tags: ["TTS", "Markdown", "Apple Silicon", "MLX", "Python", "语音克隆", "Qwen3"]
---

## 项目概览

**mellifluous**（[alexr314/mellifluous](https://github.com/alexr314/mellifluous)）是一个 macOS Apple Silicon 上的本地 Markdown 转语音（TTS）工具。它的核心思路是把 Markdown 文档解析为"有结构的朗读"——不是把文字一股脑送进 TTS，而是理解文档的层次（标题、段落、列表、代码块），按阅读节奏插入停顿，让语音输出听起来更像真人朗读。

TTS 模型跑在本地（通过 MLX 框架），语音克隆只需要一段 5-30 秒的 WAV 样本。开发者自己用它来"听"技术文档，节省眼睛。

## 核心特性

**结构化朗读**：Markdown-it-py 解析文档结构，不同元素（标题、段落、代码块、列表）有不同的停顿时长，读起来不像机器在报菜名。

**内联内容处理**：内置一系列 Detector，按优先级链式处理 Markdown 中的内联元素：

| Detector | 处理方式 |
|---|---|
| `EquationDetector` | 数学公式可接入 LLM 做语音朗读（默认说"equation"） |
| `UrlDetector` | URL 变成"link to example dot com" |
| `InlineCodeDetector` | `df.merge()` 变成"df merge" |
| `NumberDetector` | `$1,200`、`5%`、`10kg` 正确朗读 |
| `SymbolDetector` | `->`、`==`、`&&` 等符号读成对应英文 |

**语音克隆**：提供 5-30 秒 WAV（24kHz 单声道 PCM_16），即可克隆任意声音。项目中自带了作者自己的 `alex` 声音样本。

**本地运行**：TTS 模型通过 MLX 在 Apple Silicon 上运行，不需要调用云端 API。Qwen3-TTS 权重约 2GB，首次运行时自动下载。

## 技术架构

核心依赖：

- [mlx-audio](https://github.com/Blaizzy/mlx-audio)：Apple MLX 框架的音频推理后端
- [markdown-it-py](https://github.com/executablebooks/markdown-it-py)：Markdown 解析

项目结构：

```
mellifluous/
├── synth/              # TTS 推理封装
├── parse/              # Markdown 解析与 Detector 链
├── voices/             # 语音样本（alex 已包含）
└── demo.py             # 一键演示脚本
```

要移植到 Linux/CUDA，只需替换 `mellifluous/synthesize/` 部分，其余代码无 Apple 依赖。

## 快速开始

### 安装

```bash
git clone <this repo>
cd mellifluous
python3 -m venv .venv
.venv/bin/pip install -e .
```

### 一键演示

```bash
python demo.py
```

首次运行会下载 Qwen3-TTS 权重（约 2GB），然后用内置的 alex 声音朗读一个展示所有功能的示例文档。

### 基础使用

```python
from mellifluous import Reader

r = Reader()
r.speak("# Hello\n\nThis is a *test*.")
```

`Reader()` 默认选择 `voices/` 目录下第一个声音，显式指定：`Reader(voice="alex")`。

其他调用方式：

```python
r.synthesize(text)       # 返回 AudioChunk 迭代器（numpy float32 单声道）
r.to_wav(text, "out.wav") # 保存为 WAV 文件
r.utterances(text)       # 只解析不生成音频（调试用）
r.speak(token_iter, as_markdown=False)  # 接收 LLM token 流
```

### 自定义语速和停顿

```python
from mellifluous import Reader, Policy
Reader(policy=Policy(paragraph_post=900, heading_pre={1: 1500})).speak(text)
```

### 自定义语音

```bash
ffmpeg -i your_clip.mp3 -ar 24000 -ac 1 -c:a pcm_s16le voices/myname/sample.wav
```

然后 `Reader(voice="myname")`。

### 公式朗读（可选，需 LLM）

需要安装 LLM 支持并配置 Groq API Key：

```bash
.venv/bin/pip install -e '.[llm]'
echo "GROQ_API_KEY=sk-..." >> ~/.env
```

接入方式示例：

```python
from mellifluous.extras.groq_equation_reader import make_reader
eq_reader = make_reader(model="openai/gpt-oss-120b")
# 配置到 EquationDetector
```

公式朗读结果按 LaTeX 哈希做磁盘缓存，同一个公式不会重复调用 LLM。

## 适用场景与限制

**适合的场景：**

- 技术写作者"听"自己的文章，检查文字是否通顺
- 研究者把论文转成语音，在通勤或运动时听
- 开发者把 README 和文档变成音频，随手听

**限制：**

- 仅支持 macOS Apple Silicon（M1+）
- 个人项目，未发布 PyPI，需要从源码安装
- 语音克隆必须使用有权限使用的声音样本

## 总结

mellifluous 解决的是一个很具体的问题：怎么把书面文档变成听起来自然的语音。它不是通用 TTS，而是针对 Markdown 结构做了专门优化的"文档朗读器"。对于需要大量阅读技术资料、又不想一直盯着屏幕的人来说，这个工具提供了一个用耳朵"读"文章的方式。

**链接汇总：**

- GitHub：[alexr314/mellifluous](https://github.com/alexr314/mellifluous)
- 依赖：mlx-audio、markdown-it-py、Qwen3-TTS 权重（自动下载）