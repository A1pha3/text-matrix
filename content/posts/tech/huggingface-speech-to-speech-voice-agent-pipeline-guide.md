---
title: "speech-to-speech：Hugging Face 开源的 OpenAI Realtime 兼容语音 Agent 全栈 pipeline"
date: "2026-07-07T03:00:07+08:00"
lastmod: "2026-10-03"
slug: "huggingface-speech-to-speech-voice-agent-pipeline-guide"
description: "Hugging Face speech-to-speech（13.4k stars / Apache 2.0 / PyPI 已发 1.0.0）是一个低延迟、可全本地化、模块化的语音 agent pipeline：VAD→STT→LLM→TTS 四段可换，以 OpenAI Realtime 协议的 WebSocket / WebRTC 接口对外暴露。Reachy Mini 机器人以它作为生产对话后端，本文拆四段模块化设计与本地部署路径。"
draft: false
categories: ["技术笔记"]
tags: ["TTS", "Hugging Face", "语音 Agent", "Realtime"]
github_repo: "huggingface/speech-to-speech"
source_key: "gh:huggingface/speech-to-speech"
---

# speech-to-speech：一个能本地化的 OpenAI Realtime 兼容语音 Agent

OpenAI 的 Realtime API 把"语音对话"做成了单端连接调用——但 VAD、STT、LLM、TTS 全部绑死在 OpenAI 一侧，定价、隐私、定制都受限于供应商。Hugging Face 的 `speech-to-speech`（13.4k stars / Apache 2.0，2026-10-03 读数）把这条管线开源了出来：对外说的是 OpenAI Realtime 协议，对内每一环节都能换成自己选的模型。它已经在 Reachy Mini 机器人上作为对话后端跑了数千台生产实例——README 原话是 "thousands of Reachy Mini robots"。

本文拆它的四段模块化设计、本地部署路径，以及"兼容 OpenAI Realtime"这句宣传的准确含义。

## 它做了什么

一条端到端语音 agent pipeline 拆成 4 段，每段跑在自己的线程里、用队列连接：

```
麦克风音频
   ↓ VAD  Silero VAD v5（默认）/ FireRed Stream-VAD
   ↓ STT  Parakeet TDT（默认）/ Whisper 系 / Qwen3-ASR / Paraformer / …
   ↓ LLM  Responses API / Chat Completions / Transformers / mlx-lm
   ↓ TTS  Qwen3-TTS（默认）/ Kokoro / Pocket TTS / ChatTTS / OmniVoice / MMS
扬声器音频
```

对外，它通过 `serve` 命令把这条管线暴露成一个 Realtime 服务器，监听 `ws://127.0.0.1:8765/v1/realtime`，同时支持 WebSocket 和 WebRTC 两种传输。客户端用 OpenAI Realtime 协议说话，管线内部用哪些模型，客户端不需要知道。

```bash
pip install speech-to-speech
export OPENAI_API_KEY=...
speech-to-speech serve
```

这三行启动的默认配置是：Parakeet TDT 做本地 STT、`gpt-5.6-terra` 经 OpenAI Responses API 做 LLM、Qwen3-TTS 做本地语音合成。

## "兼容 OpenAI Realtime"的准确口径

这句话值得掰开说清楚，因为它决定了"你现有的客户端能不能直接换 endpoint"。

README 的口径是：服务器实现了 **Realtime 的核心事件集**——入向有 `input_audio_buffer.append`、`session.update`、`conversation.item.create`、`conversation.item.truncate`、`response.create`、`response.cancel`，出向有语音起止、流式转写、音频增量、工具调用和 `response.done`。官方 OpenAI Agents SDK 的 `RealtimeSession` 在 WebSocket 和 WebRTC 两种原生传输上过了 CI 测试。

同一句里也有限定："This is a tested core subset, not a claim of full OpenAI Realtime API equivalence"——这是经过测试的核心子集，官方不做完全等价的宣称。所以准确的说法是：使用这批核心事件的客户端可以直接把 endpoint 指过来，不用改代码；用了边缘事件的客户端需要先对照事件矩阵（在 `src/speech_to_speech/api/openai_realtime/README.md`）确认覆盖。

这个口径比文章写作时（2026 年 7 月，当时 README 只说 "OpenAI Realtime-compatible WebSocket API"）更收敛，但也更实：如今带上了 WebRTC 传输和明确的事件清单，反而更方便评估接入面。

## 模块化是它和 OpenAI Realtime 的根本区别

OpenAI Realtime 是一条黑盒：四段全部跑在 OpenAI 内部，你换不了任何一段。speech-to-speech 的每一环都有多个可换实现，用 CLI 标志选择：

| 段 | 内置实现（选装用 pip extras） | 切换标志 |
|----|------------------------------|----------|
| **VAD** | Silero VAD v5（默认）；FireRed Stream-VAD（`[fireredvad]`，另需 `--vad_firered_model_dir` 指向权重目录） | `--vad`（`silero` / `firered`） |
| **STT** | Parakeet TDT（默认）、Whisper / Whisper MLX / Faster Whisper、MLX Audio Whisper、Qwen3-ASR、Paraformer、Parakeet Unified / Nemotron / Orukeet（`[nemo]`）、任意 OpenAI 兼容转录端点、vLLM Realtime 转录（实验） | `--stt` |
| **LLM** | Responses API（默认）与 Chat Completions 两个 OpenAI 兼容后端；Transformers（CUDA/CPU）、mlx-lm（Apple Silicon）本地推理 | `--llm_backend` |
| **TTS** | Qwen3-TTS（默认）、Kokoro-82M、Pocket TTS、ChatTTS、OmniVoice（`[omnivoice]`）、MMS TTS、任意 OpenAI 兼容语音端点 | `--tts` |

两个 API 后端共享同一组 `--responses_api_*` 连接标志，README 给了一张对照表：

| Provider / server | `--responses_api_base_url` | `--responses_api_api_key` |
|---|---|---|
| OpenAI | 省略（用默认） | `$OPENAI_API_KEY` |
| HF Inference Providers | `https://router.huggingface.co/v1` | `$HF_TOKEN` |
| OpenRouter | `https://openrouter.ai/api/v1` | `$OPENROUTER_API_KEY` |
| vLLM | `http://localhost:8000/v1` | 省略或任意字符串 |
| llama.cpp | `http://127.0.0.1:8080/v1` | 空字符串 |

由此立刻能落地的三种形态：

1. **完全本地化**：Apple Silicon 上一条 `--mac-optimal-settings` 预设走 MLX（Parakeet TDT + Qwen3-4B + Qwen3-TTS），NVIDIA 上走 Transformers + GGML，全程零 API 调用。
2. **混合云**：语音两端留在本地，LLM 用托管模型。官方在 Quickstart 里写明了这条路径的数据边界——**转写文本、指令和对话历史发给提供商，麦克风音频和语音合成留在本地**。
3. **客户端零改动迁移**：已有 OpenAI Realtime 应用把 endpoint 指向 `speech-to-speech serve`，代码不动就能切到任意后端组合。

## 一次对话怎么穿过管线

把一次问答从头到尾走一遍，比罗列模块更能看清这套系统的设计取舍。

用户开口，Silero VAD 检测到语音起点，音频开始流入。用户停下来时，管线并不立刻提交这个"回合结束"——默认启用的 **Smart Turn**（pipecat-ai 的 smart-turn-v3.2，量化 ONNX 随基础包安装）会用当前轮的内容和韵律校验 Silero 的判断：确认说完了，立即开始处理，并留 800 毫秒的 `--speculative_reopen_ms` 窗口，让"等等，还有一句"能重新打开这个回合；判断为没说完，则等 600 毫秒再启动 STT/LLM，期间输出受 2 秒的 `--smart_turn_max_wait_ms` 兜底。若语音在这两个延迟里恢复，同一个回合以新修订版重开，已累积的音频重新发出，上一版的处理结果在到达用户之前丢弃。

转写阶段支持 live partial transcripts——客户端可以边听边显示未定稿的文字。文本交给 LLM 后，回复以流式文本 + 工具调用生成；工具调用和它触发的口播回答共享同一个回合修订号，服务端日志用 `response_key` 区分两者。TTS 合成出的第一块音频到达扬声器的时刻，就是日志里的 `tts_ttfa`（time to first audio）。

用户在助手说话时再次开口，`turn_detection` 的 `server_vad` 模式带 `interrupt_response: true`，当前回复被打断，管线回到倾听状态。这条打断路径是 Realtime 模式的能力——同一份代码里更早的 TCP socket 模式不提供打断、实时转写事件和工具调用事件，README 特意标注了这层差别。

## 快速上手：三条官方配置

README 的 Quickstart 按语言模型跑在哪，给了三条起点配置。三条都默认 Parakeet TDT + Qwen3-TTS，差异只在 LLM：

**Apple Silicon 全本地**（16 GB 以上统一内存）：

```bash
speech-to-speech local \
    --mac-optimal-settings \
    --model_name mlx-community/Qwen3-4B-Instruct-2507-4bit
```

预设选择 MLX 系后端：Parakeet TDT 走 MLX、Qwen3-4B 4-bit 走 MLX LM、Qwen3-TTS 6-bit 走 MLX Audio。核心权重合计约 7.5 GB。

**NVIDIA GPU 全本地**（预算 24 GB 显存给未量化 LLM + 语音模型 + 缓存）：

```bash
speech-to-speech local \
    --device cuda \
    --stt parakeet-tdt \
    --llm_backend transformers \
    --model_name Qwen/Qwen3-4B-Instruct-2507 \
    --llm_torch_dtype float16 \
    --tts qwen3 \
    --qwen3_tts_backend ggml
```

LLM 权重本身约 8 GB，Transformers 把它加载进语音进程，不需要单独的 LLM 服务。

**本地语音 + 托管 LLM**（本地语音管线约需 8 GB 可用内存，Apple Silicon 建议 16 GB 总内存）：

```bash
export OPENAI_API_KEY=...
speech-to-speech local \
    --stt parakeet-tdt \
    --llm_backend responses-api \
    --tts qwen3
```

官方对这三个数字的措辞是 "planning estimates for one conversation, not measured minimum requirements"——单次会话的规划估计，不是实测最低要求，实际取决于上下文长度、音频长度和后端版本。

### CLI 的三个子命令

2026 年 9 月起 CLI 从旧的 `--mode` 体系迁到了子命令（`--mode` 仍在迁移窗口内可用但打印弃用警告，其余旧模式值已移除）：

| 命令 | 行为 | 适用 |
|---|---|---|
| `serve` | 以 OpenAI Realtime WebSocket / WebRTC 跑管线服务器 | 构建对接 API 的应用或设备 |
| `talk --url <url>` | 打包好的麦克风/扬声器客户端 | 与现有 Realtime 服务器对话 |
| `local` | 在进程内把 `serve` 和 `talk` 组合起来（走 loopback） | 一条命令起服务并对话 |

`serve` 默认只绑 `127.0.0.1`，要对网络暴露需显式传 `--host 0.0.0.0`。把客户端换掉、只留服务器，就是部署形态：`speech-to-speech serve` 起服务器，另一个终端 `speech-to-speech talk --url ws://127.0.0.1:8765/v1/realtime` 接上去；浏览器 demo（`demo/`）也以此服务器为后端。

注意 `local` 客户端在使用 OpenAI 兼容 TTS 后端时默认缓冲 196 毫秒的接收音频来吸收 HTTP 推理的短时抖动，可用 `--playback-buffer-ms` 调整——数值越大越抗卡顿但起播越晚。

### 连本地 LLM：以 llama.cpp 为例

README 给的最低摩擦全本地方案是 llama.cpp 跑 Gemma 4，两个终端：

```bash
# 终端 1：起 LLM 并保持运行
llama-server \
    -hf ggml-org/gemma-4-E4B-it-GGUF:Q4_0 \
    --alias local-gemma \
    --host 127.0.0.1 --port 8080 \
    -ngl all -np 1 -c 8192 -fa on \
    --no-mmproj \
    --reasoning off
```

```bash
# 终端 2：语音管线接上它
speech-to-speech local \
    --stt parakeet-tdt \
    --llm_backend responses-api \
    --model_name local-gemma \
    --responses_api_base_url http://127.0.0.1:8080/v1 \
    --responses_api_api_key "" \
    --tts qwen3
```

这条配置的内存预算是 Mac 24 GB 统一内存或 NVIDIA 16 GB 显存（同为规划估计）；Q4_0 量化的 LLM 权重约 4.6 GB。示例用单路 8k 上下文并关掉推理输出以降低语音延迟，`--no-mmproj` 跳过图像/音频投影器——STT 已经把音频变成了文本。另外还有一条 Direct Audio Input 路径：`--stt none --llm_backend chat-completions` 把 VAD 切出的音频段直接交给音频输入模型，但要求模型本身吃音频，且与 Responses API 后端不兼容。

仓库自带的 Docker Compose 是第三种形态：一条 `docker compose up` 起 llama.cpp（Gemma 4）+ Realtime 服务器，暴露 8080 和 8765 两个端口，需要 NVIDIA Container Toolkit。

### Linux 上的 CUDA wheel

Qwen3-TTS 的 GGML 后端来自 `faster-qwen3-tts[ggml]`，PyPI 上的默认 `qwentts-cpp-python` wheel 针对 CUDA 12.8 和 `manylinux_2_39`（约 Ubuntu 24.04 的 glibc）。系统更旧时，先从 Hugging Face wheelhouse 装匹配版本再装本包：

```bash
# CUDA 13.x
pip install "qwentts-cpp-python==0.3.1+cu130" \
  -f https://huggingface.co/datasets/andito/qwentts-cpp-python-wheels/tree/main/whl/cu130

# CUDA 12.4
pip install "qwentts-cpp-python==0.3.1+cu124" \
  -f https://huggingface.co/datasets/andito/qwentts-cpp-python-wheels/tree/main/whl/cu124

# CPU-only fallback
pip install "qwentts-cpp-python==0.3.1+cpu" \
  -f https://huggingface.co/datasets/andito/qwentts-cpp-python-wheels/tree/main/whl/cpu

pip install speech-to-speech
```

Ubuntu 还要先装音频库：`sudo apt-get install libportaudio2 libsndfile1`。想用回旧的 CUDA-graphs 实现而非 GGML，加 `--qwen3_tts_backend torch`。Python 要求 3.10+。

## 生产部署关心的几件事

**延迟可观测**。服务器在每次 Realtime 响应结束时写一条 INFO 日志，按段拆解耗时：

```text
Turn turn_3 rev=0 latency: stt=0.18s llm=1.24s tts_ttfa=0.12s e2e=2.01s vad_decision=0.36s hold=0.24s smart_turn_status=complete status=completed response_key=...
```

（官方文档 `docs/response-latency.md` 的样例输出，非实测数据。）字段含义：`stt` 是最终转写耗时、`llm` 是语言模型耗时、`tts_ttfa` 是到第一块合成音频的时间、`e2e` 是从估计语音结束到首个生成音频的全程。各段的测量覆盖矩阵在同一文档里——比如 `tts_ttfa` 目前只有 `qwen3` 和 `openai` 两个后端有测量，Kokoro、Pocket TTS 等标 `n/a` 待补。项目不在 README 里宣传任何整体延迟数字，而是把测量工具交给部署者，这比一个无条件的"低延迟"口号有用。

**LLM 代理**。`--enable_llm_proxy` 打开后，服务器把配置的远端 LLM 以普通 OpenAI 兼容端点暴露出来（`POST /v1/chat/completions` 或 `POST /v1/responses`），客户端可以跑摘要、起标题、后台 agent 等旁路任务，与语音对话并发、不被新语音打断。要注意 README 的安全限定：代理本身**不做认证也不限流**，只应在可信网络使用，或挡在带访问控制的网关后面；请求无状态、`model` 字段会被服务器强制覆盖为自己的 `--model_name`，上游密钥不会下发给客户端。

**隐私两条线**。一是数据边界：托管 LLM 模式下只有转写文本、指令和对话历史出机器，麦克风音频和合成音频不出（前文引过 README 原话）。二是日志：默认日志**不含内容**——带转写的日志只记录字符数而非文本本身，因为日志通常被 systemd、容器或托管日志服务长期保存；调试时用 `--log_transcripts` 显式打开完整转写，启动时会打印警告。

**多语言**。语言覆盖取决于你选的后端，不取决于管线本身。README 的表里：默认的 Parakeet TDT 覆盖 **25 种欧洲语言**；Whisper 系看所选 checkpoint；Paraformer 默认中文向；TTS 侧 Qwen3-TTS 多语言且默认 `auto`，ChatTTS 支持英语和中文，Pocket TTS 只有英法德葡意西，OmniVoice 号称 600+ 语言带声音克隆。默认情况下发给 TTS 的语言代码来自用户转写，`--detect_llm_output_language` 可以改为检测助手回复的语言。中文场景的官方示例组合是：

```bash
speech-to-speech serve \
    --stt whisper-mlx \
    --stt_model_name large-v3 \
    --language zh \
    --llm_backend mlx-lm \
    --model_name mlx-community/Qwen3-4B-Instruct-2507-4bit
```

**杂项但实用**：`--num_pipelines` 调 Realtime 管线池大小；离线部署先联网跑一次所选配置缓存好模型，之后 `HF_HUB_OFFLINE=1` 启动，Smart Turn 可用 `--smart_turn_model_path` 指定本地 checkpoint 或 `--no_smart_turn` 关闭；VAD 灵敏度默认 `--min_speech_ms 384` 配 `--min_speech_continuation_ms 192`，扬声器回声干扰时客户端可加 `--local_audio_block_mic_during_playback` 在播放期间暂停收音（代价是无法再打断助手）。

## 适用边界

**适合**：

- 已有 OpenAI Realtime 应用想本地化或换供应商——客户端用的是核心事件集时，换 endpoint 即可
- 隐私敏感场景（医疗 / 法律 / 内部录音）需要语音两端全本地
- 想给机器人或硬件设备配一个开源对话后端——Reachy Mini 数千台实例是这个路径的现成参照，HF 上还有 Reachy Mini 本地对话的专门博客
- 想按段挑选模型组合（比如 Whisper 转录 + 本地 LLM + 声音克隆 TTS）而不愿自己粘合管线

**不适合**：

- 想要"完全托管、什么都不管"——直接用 OpenAI Realtime 更省事
- 用到核心事件集之外特性的存量客户端——接入前对照事件矩阵逐项确认，官方明确不做完全等价宣称
- 中文重度场景不加后端选择——默认 Parakeet TDT 不含中文，需要按上文换 STT，TTS 同理核对语言表
- 需要 OmniVoice 声音克隆的商用产品——其代码是 Apache-2.0，但预训练权重是 CC-BY-NC，README 用 WARNING 明确不可商用

**成本怎么算**。本地化的成本不在 API 账单而在硬件：三条官方配置的门槛分别是 16 GB 统一内存（Mac 全本地，7.5 GB 权重）、24 GB 显存（NVIDIA 全本地）、约 8 GB 可用内存 + 托管 LLM 的 API 费用。具体账单数字随用量、模型与提供商价差浮动太大，本文不代替读者估算——把部署形态和数据边界定下来后，成本变量只剩 LLM 一段（全本地时为零）。

## 关键事实

- **仓库**：`huggingface/speech-to-speech`
- **协议**：Apache 2.0；**主语言**：Python（3.10+）
- **stars / forks**：13,363 / 1,701（2026-10-03 读数；文章发表时约 5.4k，三个月翻倍以上）
- **PyPI**：`speech-to-speech`，2026-09-06 发布 1.0.0
- **生产用户**：数千台 Reachy Mini 机器人作为对话后端（README 原话）
- **默认栈**：Silero VAD v5 + Parakeet TDT + `gpt-5.6-terra`（Responses API）+ Qwen3-TTS
- **接口**：OpenAI Realtime 核心事件集，WebSocket / WebRTC 双传输，`ws://127.0.0.1:8765/v1/realtime`

## 一句话总结

speech-to-speech 是 OpenAI Realtime API 的开源等价接口加可拆解的内部：对外说同一套核心协议、官方 Agents SDK 过了双传输测试，对内四段管线每段可换、可全本地、可混合云。Reachy Mini 的数千台生产实例证明它不是 demo——而"tested core subset, not full equivalence"这句官方限定，是接入前最该记住的一句话。
