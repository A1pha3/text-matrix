---
title: "VibeVoice：微软开源前沿语音AI模型家族，ASR支持60分钟长音频"
date: "2026-04-29T11:30:00+08:00"
lastmod: 2026-04-29T11:30:00+08:00
draft: false
tags: ["语音AI", "微软", "ASR", "TTS", "开源", "VibeVoice"]
categories: ["技术笔记"]
description: "VibeVoice 是微软开源的前沿语音AI模型家族，包含ASR语音识别（支持60分钟长音频、50+语言）和Realtime实时语音合成，已被接纳为ICLR 2026 Oral论文。"
slug: vibevoice-microsoft-voice-ai
author: ""
---

# VibeVoice：微软开源前沿语音 AI 模型家族，ASR 支持 60 分钟长音频

## 概述

**VibeVoice** 是微软开源的**前沿语音 AI 模型家族**，包含语音识别（ASR）和语音合成（TTS）两大核心模型。与传统短片段处理的 ASR 不同，VibeVoice-ASR 支持**单次通过处理 60 分钟连续音频**，保留完整的说话人跟踪和语义连贯性。

该项目的核心技术亮点是**7.5 Hz 超低帧率音频分词器**，结合 Next-token Diffusion 框架，显著提升长序列处理效率。VibeVoice-ASR-7B 已于 2026 年 3 月正式进入 Hugging Face Transformers 版本，意味着可以直接通过 Transformers 库调用。

> 🔥 **VibeVoice-TTS** 已于 2025 年 9 月从本仓库移除（因发现被滥用于不一致的目的），但 VibeVoice-ASR 和 VibeVoice-Realtime 仍在活跃维护中。

**GitHub**: [microsoft/VibeVoice](https://github.com/microsoft/VibeVoice)  
**项目主页**: [microsoft.github.io/VibeVoice](https://microsoft.github.io/VibeVoice)  
**Hugging Face**: [huggingface.co/collections/microsoft/vibevoice-68a2ef24a875c44be47b034f](https://huggingface.co/collections/microsoft/vibevoice-68a2ef24a875c44be47b034f)

---

## 核心模型

| 模型 | 参数量 | 链接 | 状态 |
|------|--------|------|------|
| VibeVoice-ASR-7B | 7B | [HuggingFace](https://huggingface.co/microsoft/VibeVoice-ASR) | ✅ 活跃 |
| VibeVoice-TTS-1.5B | 1.5B | [HuggingFace](https://huggingface.co/microsoft/VibeVoice-1.5B) | ❌ 已下架 |
| VibeVoice-Realtime-0.5B | 0.5B | [HuggingFace](https://huggingface.co/microsoft/VibeVoice-Realtime-0.5B) | ✅ 活跃 |

---

## 技术原理

### 7.5 Hz 超低帧率音频分词器

VibeVoice 的核心设计之一是**连续音频分词器**（Acoustic Tokenizer 和 Semantic Tokenizer），以仅 **7.5 Hz** 的超低帧率运行。相比传统分词器，这降低了计算复杂度，同时保留了高保真音频特征。

### Next-token Diffusion 框架

VibeVoice 采用 **Next-token Diffusion** 架构：
1. 大语言模型（LLM）理解文本上下文和对话流程
2. Diffusion Head 生成高保真 acoustic details
3. 两者结合实现流畅的语音合成和识别

### 60 分钟长音频单次处理

传统 ASR 模型将音频切分为短片段（通常丢失全局上下文），VibeVoice-ASR 可在 **64K token 长度内**单次处理**最长 60 分钟**的连续音频，确保全时段说话人跟踪和语义一致性。

---

## VibeVoice-ASR：长音频语音识别

**VibeVoice-ASR** 是统一的多语言语音转文本模型，主要功能：

- 🕒 **60 分钟单次处理**：突破传统 ASR 的片段切割限制
- 👤 **自定义热词（Customized Hotwords）**：支持用户添加人名、术语、背景信息，显著提升垂直领域识别准确率
- 🌍 **原生多语言**：支持**50+语言**的语音识别
- 📝 **结构化输出**：生成包含 Who（说话人）、When（时间戳）、What（内容）的格式化转录文本
- ⚡ **vLLM 推理加速**：支持 vLLM 推理后端，显著提升推理效率

**ASR 技术报告**： [arXiv:2601.18184](https://arxiv.org/pdf/2601.18184)

### 支持的语言（部分）

英语、中文、日语、韩语、法语、德语、西班牙语、意大利语、葡萄牙语、俄语、阿拉伯语、印地语、越南语、泰语等 50 余种语言。

---

## VibeVoice-Realtime：实时语音合成

**VibeVoice-Realtime-0.5B** 是参数量仅 **0.5B** 的实时语音合成模型：

- ⚡ **流式文本输入**：支持流式输入，实时输出语音
- 🌍 **多语言支持**：已支持英语、德语、法语、意大利语、日语、韩语、荷兰语、波兰语、葡萄牙语、西班牙语等 10 种语言
- 🎭 **多风格人声**：已上线 11 种不同风格的英语语音，以及 9 种语言的多语言语音
- 📄 **长文本合成**：robust long-form speech generation

**Colab 体验**：[VibeVoice-Realtime Colab](https://colab.research.google.com/github/microsoft/VibeVoice/blob/main/demo/vibevoice_realtime_colab.ipynb)

---

## 学术认可：ICLR 2026 Oral

VibeVoice-TTS 论文已被 **ICLR 2026** 接纳为 **Oral（口头报告）** 论文，论文发表在 OpenReview：[VibeVoice-TTS Paper](https://openreview.net/forum?id=FihSkzyxdv)

---

## 快速上手

### 通过 Hugging Face Transformers 使用 ASR

```python
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import torch

# 加载模型
model_id = "microsoft/VibeVoice-ASR"
model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    device_map="auto"
)
processor = AutoProcessor.from_pretrained(model_id)

# 构建 pipeline
pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch.float16,
    device_map="auto"
)

# 推理
result = pipe("path/to/your/audio.wav", return_timestamps=True)
print(result["text"])
```

### vLLM 加速推理

VibeVoice-ASR 支持 vLLM 后端加速，参考 [vllm-asr 文档](docs/vibevoice-vllm-asr.md)。

### 本地微调

VibeVoice-ASR 的微调代码已开源，参考 [finetuning-asr/README.md](finetuning-asr/README.md)。

---

## 与同类项目的比较

| 特性 | VibeVoice-ASR | Whisper | FunAudioLLM |
|------|--------------|---------|-------------|
| 最长输入 | 60 分钟 | 30 分钟 | 未知 |
| 帧率 | 7.5 Hz | 50 Hz | 未知 |
| 多语言 | 50+ | 100+ | 有限 |
| vLLM 支持 | ✅ | ❌ | ❌ |
| 结构化输出 | ✅ | ❌ | ❌ |
| ICLR Oral | ✅ | ❌ | ❌ |

---

## 应用场景

1. **会议记录与转写**：60 分钟单次处理，告别片段拼接
2. **播客/视频字幕**：长音频一键转文字，支持多语言
3. **客服语音分析**：结构化输出便于检索和分析
4. **语音助手**：实时语音合成，低延迟交互
5. **无障碍辅助**：为听障用户提供实时字幕服务

---

## 总结

VibeVoice 在长音频处理和超低帧率分词上有明确的技术差异。VibeVoice-ASR 的 60 分钟单次处理、50+ 语言支持、vLLM 加速，以及 ICLR 2026 Oral 认可，使其在开源语音识别领域占一席之地。VibeVoice-Realtime 的 0.5B 实时 TTS 模型为低延迟语音合成提供了新选项。

**适用人群**：语音 AI 研究者、长音频处理开发者、多语言语音应用工程师

---

> 📌 **更多信息**
> - GitHub: [microsoft/VibeVoice](https://github.com/microsoft/VibeVoice)
> - 项目主页： [microsoft.github.io/VibeVoice](https://microsoft.github.io/VibeVoice)
> - HuggingFace: [hf.co/microsoft/VibeVoice-ASR](https://huggingface.co/microsoft/VibeVoice-ASR)
> - ASR 技术报告： [arXiv:2601.18184](https://arxiv.org/pdf/2601.18184)
> - ICLR 2026 论文： [OpenReview](https://openreview.net/forum?id=FihSkzyxdv)
