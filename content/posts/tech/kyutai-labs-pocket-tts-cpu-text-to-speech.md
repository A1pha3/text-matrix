---
title: "kyutai-labs/pocket-tts：把 100M 参数 TTS 装进 CPU 口袋"
date: 2026-07-10T02:58:08+08:00
slug: "kyutai-labs-pocket-tts-cpu-text-to-speech"
tags: ["TTS", "Kyutai", "PyTorch", "CPU 推理", "语音克隆", "开源模型"]
categories: ["技术笔记"]
description: "拆解 Kyutai Pocket TTS 的核心机制——一个 100M 参数、纯 CPU 推理、首块延迟 ~200ms 的开源 TTS 框架，及其多语言、流式、声音克隆能力。"
---

## 核心判断

Pocket TTS 不是“又一个开源 TTS”。它的赌注很明确：**让 TTS 回归本地、CPU、零网关**。100M 参数、首块 ~200ms、6× 实时率（M4 MacBook Air）、支持英语/法语/德语/葡萄牙语/意大利语/西班牙语、声音克隆、Python API + CLI + HTTP 服务三入口——这些数字合起来，对标的是商业 TTS API（ElevenLabs、Azure TTS、Google Cloud TTS），但**完全跑在用户的 CPU 上**。它的工程价值在于：把流式自回归 TTS 模型裁剪到了消费级笔记本能撑住的水位。

## 基本盘

- GitHub：<https://github.com/kyutai-labs/pocket-tts>
- 仓库描述：A TTS that fits in your CPU (and pocket)
- 模型大小：100M 参数
- 平台：CPU（PyTorch 2.5+，无需 GPU 版本 PyTorch）
- Python：3.10 / 3.11 / 3.12 / 3.13 / 3.14
- 训练机构：Kyutai（法国 Moshi 团队）
- 配套产物：Demo、HF Model Card、技术报告、论文（arXiv 2509.06926）

## 关键能力指标（README 自报）

| 维度 | 数值 |
|---|---|
| 模型大小 | 100M 参数 |
| 首块延迟 | ~200ms |
| 实时率 | ~6× 实时率（MacBook Air M4 CPU） |
| CPU 占用 | 仅 2 核 |
| 输入 | 文本流（无限长度，无切片需要） |
| 多语言 | 英、法、德、葡、意、西 |
| 声音克隆 | 支持，提供 voice 列表可调 |
| 部署形态 | Python API + CLI + HTTP serve + 浏览器 WASM |

## 系统地图

Pocket TTS 的运行链路（结合其论文 + README 推断）：

```
文本输入
    ↓
[Tokenizer] SentencePiece / 自研 BPE
    ↓
[声学模型] ~100M 参数 Transformer（推测 Mimi codec + 文本条件）
    ↓
[Mimi Audio Token] → 离散 token 流
    ↓
[Codec 解码器] 流式生成 wav 帧
    ↓
输出 PCM（流式，可边生成边播）
```

几个关键设计信号：

1. **自回归 + 流式**：模型是自回归的，但通过流式 codec 解码保证首块延迟 ~200ms
2. **音频 token 化**：复用 Kyutai 团队在 Moshi 里打磨过的 Mimi audio codec，所以模型可以用“文本 token + 音频 token”统一表征
3. **CPU 优化**：核心解码路径用纯 PyTorch + 极少自定义 C++/CUDA 算子，所以 CPU 是首选目标
4. **声音克隆**：voice 文件就是一个预录制的参考 wav + 文本 pair，推理时拼接

## 三种使用方式

### 1. CLI 一键试

```bash
uvx pocket-tts generate
# 或装到环境后
pocket-tts generate
```

默认会读内置默认文本 + 默认 voice，输出 `./tts_output.wav`，并打印速度统计。

### 2. Python API

```python
from pocket_tts import generate_audio

# 加载默认英文模型
audio = generate_audio(text="Hello world.", voice="alba")
# audio 是 numpy 数组，可直接写到 wav
```

### 3. HTTP 服务

```bash
pocket-tts serve --port 8080
# 然后
curl -X POST http://localhost:8080/tts -d '{"text":"...","voice":"giovanni"}' --output out.wav
```

这一层让“本地 TTS 服务 + 任何客户端”成为可能，消除了对 ElevenLabs 那种托管 API 的依赖。

### 4. 浏览器 WASM

README 提到支持 in-browser 实现，配合 Pyodide + ONNX export 或原生 WASM build，等于把 TTS 部署到静态网站都不需要后端。

## 任务流案例：构建一个不依赖云端的播客配音工具

1. **安装**：`pip install pocket-tts`（或 `uvx pocket-tts ...`）
2. **克隆主播声音**：准备一段 30 秒参考 wav，用 `pocket-tts export-voice --ref-wav xxx.wav --name myhost` 导出一个 voice
3. **批处理**：写一个 50 行的 Python 脚本，按段落读 txt，调用 `generate_audio` 流式合成 wav
4. **拼接**：用 `pydub` 或 `ffmpeg` 把 wav 拼起来，加静音
5. **发布**：整套链路完全本地，文本不离开机器

整个流程对标商用 ElevenLabs 的“Professional Voice Cloning”，但没有云端账单、没有隐私顾虑、没有 monthly quota 限制。

## 与相似项目的对比

| 项目 | 大小 | 平台 | 多语言 | 声音克隆 | 流式 |
|---|---|---|---|---|---|
| Pocket TTS | 100M | CPU | 6 种 | ✅ | ✅ ~200ms 首块 |
| Coqui XTTSv2 | ~1.5B | GPU 优先 | 16 种 | ✅ | ❌（整段合成） |
| Kokoro | 82M | CPU | 8 种 | ❌（固定 voice 列表） | ❌ |
| MeloTTS | ~250M | CPU/GPU | 6 种 | ❌ | ❌ |
| CosyVoice | ~300M | GPU | 中/英/日 | ✅ | ✅ |
| ChatTTS | ~1B | GPU | 中/英 | 部分 | ✅ |
| Piper | ~60M | CPU | 多 | 部分 | ❌ |

Pocket TTS 在这张表里的位置是：**与 Piper 同档的轻量级 + 与 Kokoro 一样的 CPU 友好 + 与 XTTS/CosyVoice 一样的流式和声音克隆**。它的差异化是“参数小 + CPU + 流式 + 克隆”四个维度同时达成。

## 适用边界

适合：

- 想做**离线 / 本地 TTS** 的产品（隐私、零云端账单）
- 终端用户机器 CPU 够用、不想推用户装 GPU
- 需要流式首块延迟的场景（对话式语音助手、字幕配音）
- 多语言产品想用一个模型覆盖欧洲主流语言

不适合：

- 需要**情感控制、韵律细节、歌声合成**等高表现力场景（100M 模型的天花板）
- 需要**SSML 精细控制**（重音、停顿、whisper 等）——目前 voice + text 是主接口
- 想要企业级 SLA 保障（开源项目没有 SLA，参考论文 + 自行 benchmark）

## 关键技术观察

1. **CPU 优化关键**：Mimi codec 解码是用 SIMD 友好的实现，单核 6× 实时率意味着可以一边合成一边播放，不需要 buffer 等待
2. **多语言统一**：6 种语言共享同一套声学模型，只是 tokenizer 不同——训练时多语料混合
3. **声音克隆方法**：从 README 看是“reference wav + 文本”的 in-context learning 风格，而不是 fine-tuning 风格，所以克隆过程无需训练
4. **无限长文本**：依赖流式 codec 解码的“自回归 + 缓存”机制，不强制分块

## 学习路径建议

1. **第 1 天**：`pip install pocket-tts` → `pocket-tts generate` → 听 wav
2. **第 2 天**：用 Python API 写一个 30 行批量合成脚本，对比你自己的中文模型
3. **第 4 天**：`pocket-tts serve` 起本地服务，做一个简单的 Web UI
4. **第 7 天**：录制一段自己的声音，做 voice 克隆，验证质量
5. **第 14 天**：读 Mimi codec 论文（同期 Moshi 论文），理解 audio tokenization 的设计选择

## 参考

- 仓库：<https://github.com/kyutai-labs/pocket-tts>
- 论文：<https://arxiv.org/abs/2509.06926>
- 技术报告：<https://kyutai.org/blog/2026-01-13-pocket-tts>
- Hugging Face Model：<https://huggingface.co/kyutai/pocket-tts>
- Voice 列表：<https://huggingface.co/kyutai/tts-voices>
- Demo：<https://kyutai.org/pocket-tts>
- 配套 Moshi 项目：<https://github.com/kyutai-labs/moshi>
