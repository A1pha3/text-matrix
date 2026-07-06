---
title: "speech-to-speech：Hugging Face 开源的 OpenAI Realtime 兼容语音 Agent 全栈 pipeline"
date: "2026-07-07T03:00:07+08:00"
slug: "huggingface-speech-to-speech-voice-agent-pipeline-guide"
description: "Hugging Face speech-to-speech（5.4k stars / Apache 2.0）是一个低延迟、可全本地化、模块化的语音 agent pipeline：VAD→STT→LLM→TTS 四段可换，并通过 OpenAI Realtime 兼容 WebSocket API 暴露。已在 Reachy Mini 机器人的生产环境跑了数千实例，本文拆四段模块化设计与本地部署路径。"
draft: false
categories: ["技术笔记"]
tags: ["Voice Agent", "OpenAI Realtime", "STT", "TTS", "Hugging Face"]
---

# speech-to-speech：一个能本地化的 OpenAI Realtime 兼容语音 Agent

OpenAI 的 Realtime API 把"语音对话"做成了单端 WebSocket 调用——但它强绑 OpenAI 的 STT/TTS/LLM，定价、隐私、定制都受限于供应商。Hugging Face 的 `speech-to-speech`（5.4k stars / Apache 2.0）做了一个**接口形态完全兼容 OpenAI Realtime**、但**每一段模块都能换**的开源替代。本文拆它的四段模块化设计与本地部署路径。

## 它做了什么

一条端到端语音 agent pipeline 拆成 4 段：

```
麦克风音频
   ↓ VAD (Silero VAD v5)
   ↓ STT (Parakeet TDT 本地 / OpenAI Whisper / Groq Whisper)
   ↓ LLM (OpenAI 兼容协议 / HF Inference Providers / vLLM / llama.cpp 本地)
   ↓ TTS (Qwen3-TTS / Pocket TTS / Kokoro / ChatTTS / MMS)
扬声器音频
```

它把这个 pipeline 暴露成一个 `ws://localhost:8765/v1/realtime` 的 WebSocket server——和 OpenAI Realtime API **完全兼容**。这意味着任何 OpenAI Realtime 客户端（包括官方 SDK、各种开源 voice agent 框架）都可以把 endpoint 指向这个 server，**不需要改 client 代码**。

## 模块化是它和 OpenAI Realtime 的根本区别

OpenAI Realtime 是一条**黑盒**：VAD/STT/LLM/TTS 全部跑在 OpenAI 内部，你换不了任何一段。

speech-to-speech 是**完全模块化**的——每一段都有多个可换实现：

| 段 | 内置实现 | 替换方式 |
|----|----------|----------|
| **VAD** | Silero VAD v5（默认） | 改 config 换其他 VAD |
| **STT** | Parakeet TDT（本地）、Whisper API（OpenAI / Groq） | 改 `--stt` 标志 |
| **LLM** | 任何 OpenAI 兼容协议 | 改 endpoint URL，可指向 vLLM / llama.cpp / HF Inference Providers |
| **TTS** | Qwen3-TTS（Apple Silicon 用 mlx-audio，Linux 用 GGML）、Pocket TTS、Kokoro-82M、ChatTTS、MMS | 改 `--tts` 标志，可装额外 backend |

这意味着几个立刻能落地的场景：

1. **完全本地化**：STT 用 Parakeet TDT + TTS 用 Qwen3-TTS + LLM 用 vLLM 跑 Gemma 4 → 全离线运行，零 API 费用，零数据外泄。
2. **混合云**：STT/TTS 用本地（保护声音），LLM 用 OpenAI（用更强模型）→ 平衡成本和隐私。
3. **开发测试**：全用 OpenAI API 但 endpoint 指向 speech-to-speech server → 不用改 client 代码就能切本地。

## 快速上手

最简方式（5 行）：

```bash
pip install speech-to-speech
export OPENAI_API_KEY=...
speech-to-speech
```

这条命令会启动一个 OpenAI Realtime 兼容 server 在 `ws://localhost:8765/v1/realtime`，默认配：Parakeet TDT (STT) + OpenAI 兼容 LLM + Qwen3-TTS (TTS)。

用任意 OpenAI Realtime 客户端连上去：

```bash
# 官方 openai-realtime-python demo
python scripts/listen_and_play_realtime.py --host 127.0.0.1 --port 8765
```

想完全本地化（连 LLM 都不用 OpenAI）：

```bash
# 1. 起一个本地 LLM server
llama-server -hf ggml-org/gemma-4-E4B-it-GGUF -np 2 -c 65536 -fa on --swa-full

# 2. 把 speech-to-speech 的 LLM endpoint 指向它
speech-to-speech --llm-base-url http://127.0.0.1:8080/v1
```

完整本地化就完成了：VAD / STT / LLM / TTS 全部在你机器上跑，零外部 API 调用。

## 生产部署的几个细节

### Apple Silicon 优化

TTS 段在 Apple Silicon 上用 mlx-audio 后端跑 Qwen3-TTS，Linux 上用 GGML 后端（faster-qwen3-tts[ggml]）。所以同一份代码在 M-series Mac 上跑得比 Linux 服务器还快——Reachy Mini 机器人就是这个选择。

### CUDA wheel 陷阱

Qwen3-TTS 的 GGML 默认 wheel 绑 CUDA 12.8。如果你的 Linux 没装 CUDA 12 运行时，需要从 Hugging Face wheelhouse 装对应版本：

```bash
# CUDA 13.x
pip install qwentts-cpp-python-cu13

# CUDA 12.4
pip install qwentts-cpp-python-cu12

# CPU-only fallback
pip install qwentts-cpp-python-cpu
```

这块坑不少，README 单独列了一个 "CUDA Note for Qwen3-TTS" 章节处理。

### Realtime 流式 vs Request-Response

OpenAI Realtime API 是**流式**的——客户端发一段音频流，server 流式回音频流；不是"发完一段、等结果"。speech-to-speech 完整支持这个语义，包括：

- partial transcripts（边听边打字到 UI）
- 工具调用（LLM 在生成响应时可以调 tool）
- interruption（用户开口说话打断当前回复）

所以你可以直接拿它做"实时对话机器人"，不需要任何额外的流式层。

## 适用边界

**适合**：

- 已经有 OpenAI Realtime 应用想本地化（直接换 endpoint URL 就行）
- 隐私敏感场景（医疗 / 法律 / 内部录音）需要全本地化 STT/TTS
- 想换 LLM（用 Llama / Gemma / Qwen 本地模型）但不想改 client 代码
- 想用更强的 TTS（Qwen3-TTS 比 OpenAI TTS 便宜得多）
- 机器人 / 嵌入式场景（Reachy Mini 已经验证）

**不适合**：

- 想要"开箱即用 + 不在乎数据出公司"——直接用 OpenAI Realtime。
- 想要中文 TTS 顶级质量——Qwen3-TTS 在中文上比 Kokoro / Pocket TTS 好很多，但跟商用 ElevenLabs 顶级模型仍有差距。
- 想要超低延迟 < 200ms——本地化 STT/TTS 延迟通常在 300-500ms，比 OpenAI Realtime 的 ~250ms 略慢。

## 关键事实

- **仓库**：`huggingface/speech-to-speech`
- **协议**：Apache 2.0（自托管友好）
- **主语言**：Python
- **stars**：5.4k / forks 670
- **生产用户**：数千 Reachy Mini 机器人作为对话后端
- **默认 VAD**：Silero VAD v5（轻量、本地、CPU 友好）
- **默认 STT**：Parakeet TDT（NVIDIA 本地模型）
- **默认 TTS**：Qwen3-TTS（多平台 backend）

## 它和直接用 Realtime API 的成本对比

以一个中等使用强度（每天 2 小时语音对话）为例：

- **OpenAI Realtime 全栈**：约 $50-100/月（取决于模型选择）
- **OpenAI Realtime + 本地 STT/TTS**：约 $10-20/月（只剩 LLM 成本）
- **全本地化**：$0 API + 电费

后者把成本压到接近零，但延迟会略增、模型质量取决于本地硬件。如果你能跑 M2 Ultra / 4090 这种级别，本地模型质量已经不输 GPT-4o-mini。

## 一句话总结

speech-to-speech 是 OpenAI Realtime API 的"开源 + 模块化"等价物——它让你用**同一套客户端代码**切换到任意 STT/TTS/LLM 组合，本地化、混合云、全云三种部署模式无缝切换。在 Hugging Face 已经有数千台 Reachy Mini 机器人把它当生产后端跑——这不是 demo 项目，是真正在用的 voice agent 基础设施。