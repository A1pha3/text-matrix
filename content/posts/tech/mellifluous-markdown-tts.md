---
title: "mellifluous：本地运行的 Markdown TTS 工具，让文档自己\"出声\""
date: "2026-05-17T12:05:30+08:00"
slug: "mellifluous-markdown-tts-apple-silicon"
description: "mellifluous 是一个运行在 macOS Apple Silicon 上的本地 Markdown 转语音工具，基于 Qwen3-TTS 和 MLX 框架，支持语音克隆，可以把 Markdown 文档解析为结构化朗读节奏，支持公式、代码、链接等内联内容的语音处理。"
draft: false
categories: ["技术笔记"]
tags: ["TTS", "Markdown", "Apple Silicon", "MLX", "Python", "语音克隆", "Qwen3"]
---

> **项目信息卡**
>
> - **GitHub**: [alexr314/mellifluous](https://github.com/alexr314/mellifluous)
> - **Stars**: 3+ | **Forks**: 0+ | **License**: MIT
> - **语言**: Python | **平台**: macOS Apple Silicon (M1+)
> - **核心依赖**: MLX-Audio, markdown-it-py, Qwen3-TTS

## 学习目标

读完本文后，你应该能够：

1. 理解 mellifluous 的核心设计思路——为什么 Markdown 结构化朗读比通用 TTS 更适合技术文档
2. 区分 mellifluous 架构中的关键模块职责（synth、parse、Detector 链）
3. 独立完成 mellifluous 的安装、演示和运行
4. 配置自定义语音克隆样本，并理解 WAV 格式要求
5. 判断 mellifluous 是否适合你的使用场景，以及它的平台限制

## 目录

- [学习目标](#学习目标)
- [项目概览](#项目概览)
- [核心特性](#核心特性)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
- [适用场景与限制](#适用场景与限制)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [总结](#总结)

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

## 常见问题

**Q1：mellifluous 的语音输出质量取决于什么？**

主要取决于 Qwen3-TTS 模型的发音准确度和 Detector 链对内联内容的处理效果。对于技术文档中常见的代码、URL、数学公式，Detector 链会做专门处理，但复杂公式需要配置 LLM 支持才能正确朗读。

**Q2：为什么首次运行要下载约 2GB 的模型权重？**

Qwen3-TTS 是一个完整的 TTS 模型，约 2GB。首次运行时 mellifluous 通过 MLX 框架自动下载。下载后权重会缓存在本地，后续运行不需要重新下载。

**Q3：除了 macOS Apple Silicon，还有其他方式运行吗？**

可以，但需要替换 `mellifluous/synthesize/` 部分。你可以尝试用 PyTorch + CPU 推理，但语音质量和延迟会显著下降。作者目前没有计划官方支持 Linux/Windows，社区如有需求可以提 PR。

**Q4：语音克隆会不会有法律风险？**

会。你必须有权限使用目标声音样本。用他人的声音克隆并分发，可能涉及肖像权、隐私权等法律问题。建议只用自己的声音，或者获得明确授权。

**Q5：公式朗读的 LLM 调用成本高吗？**

公式朗读结果按 LaTeX 哈希做磁盘缓存，同一个公式不会重复调用 LLM。如果只是偶尔遇到公式，成本很低。如果文档大量包含公式，建议批量预处理。

## 自测题

1. **mellifluous 和普通 TTS 工具的核心区别是什么？**
   答：mellifluous 理解 Markdown 结构（标题、段落、列表、代码块），按阅读节奏插入停顿；普通 TTS 把文字一股脑送进去，读起来像机器报菜名。

2. **Detector 链的作用是什么？举两个 Detector 的例子。**
   答：Detector 链按优先级处理 Markdown 中的内联元素，让语音输出更符合阅读习惯。例如 `NumberDetector` 正确处理 `$1,200`、`5%`；`SymbolDetector` 把 `->` 读成 "arrow"。

3. **语音克隆对 WAV 样本有什么要求？**
   答：5-30 秒、24kHz、单声道、PCM_16 格式的 WAV 文件。

4. **mellifluous 为什么只能在 macOS Apple Silicon 上运行？**
   答：TTS 推理通过 MLX 框架在 Apple Silicon 上运行。MLX 是苹果为 Apple Silicon 优化的机器学习框架，不跨平台。

5. **如果公式朗读结果不正确，可能是什么原因？**
   答：公式朗读需要配置 Groq API Key 和 LLM 支持。如果没有配置，`EquationDetector` 默认说 "equation"，不会真正朗读公式内容。

## 进阶路径

### 阶段一：基础使用（1-2 天）
- 完成 `python demo.py` 一键演示
- 用 `Reader()` 默认声音朗读一篇自己的技术文档
- 调整 `Policy` 参数，找到舒服的语速和停顿

### 阶段二：自定义语音（3-5 天）
- 录制自己的 20 秒语音样本，用 ffmpeg 转成要求格式
- 配置自定义声音，对比克隆效果和默认 alex 声音的差异
- 如果有技术文档需要"听审"，用 mellifluous 跑一遍，检查哪些地方朗读效果不好

### 阶段三：扩展和贡献（1-2 周）
- 阅读 `synth/` 和 `parse/` 目录的代码，理解 TTS 推理和 Markdown 解析的实现
- 如果需要支持新的 Markdown 元素（例如 footnotes、definition lists），编写新的 Detector
- 如果需要在 Linux/CUDA 上运行，研究如何替换 `mellifluous/synthesize/` 部分

### 阶段四：集成到工作流（2-4 周）
- 把 mellifluous 集成到文档生成流水线（例如用 Sphinx 生成文档后自动转成语音）
- 为团队内部知识库添加语音版本
- 如果有兴趣，给项目提 PR——作者活跃，社区友好

## 总结

mellifluous 解决的是一个很具体的问题：怎么把书面文档变成听起来自然的语音。它不是通用 TTS，而是针对 Markdown 结构做了专门优化的"文档朗读器"。对于需要大量阅读技术资料、又不想一直盯着屏幕的人来说，这个工具提供了一个用耳朵"读"文章的方式。

**链接汇总：**

- GitHub：[alexr314/mellifluous](https://github.com/alexr314/mellifluous)
- 依赖：mlx-audio、markdown-it-py、Qwen3-TTS 权重（自动下载）
