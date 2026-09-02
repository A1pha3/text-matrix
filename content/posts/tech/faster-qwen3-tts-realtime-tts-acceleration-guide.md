---
title: "Faster Qwen3-TTS：用 CUDA Graph 把 Qwen3-TTS 压到实时"
date: "2026-03-31T14:20:00+08:00"
lastmod: "2026-08-08"
slug: "faster-qwen3-tts-realtime-tts-acceleration-guide"
github_repo: "andimarafioti/faster-qwen3-tts"
description: "Faster Qwen3-TTS 用 torch.cuda.CUDAGraph 捕获解码步骤，不依赖 Flash Attention、vLLM、Triton，在 RTX 4090 上把 0.6B 模型推到 RTF 4.78、首音频 156ms。本文拆解它的 CUDA Graph 与静态 KV Cache 机制，给出全硬件基准与流式 chunk_size 的取舍。"
draft: false
categories: ["技术笔记"]
tags: ["TTS", "语音合成", "Qwen3"]
---

# Faster Qwen3-TTS：用 CUDA Graph 把 Qwen3-TTS 压到实时

Faster Qwen3-TTS 要解决的问题很具体：Qwen3-TTS 官方推理代码跑不到实时。它在 Jetson AGX Orin 上 RTF 只有约 0.18——生成 1 秒音频要等 5.7 秒。瓶颈不在模型本身，而在 Python 逐次启动 CUDA 内核的开销。这个项目用 `torch.cuda.CUDAGraph` 把整个解码步骤捕获进一张图统一重放，并配上 `transformers` 的静态 KV Cache，不改任何注意力层就拿到了实时性能。

先读结论：

- **加速对象**：非算子本身，而是解码单步约 500 次 CUDA 内核的启动空隙。GPU 比 CPU 快得越多，能找回的空闲越多，加速越明显。
- **0.6B 实时标杆**：RTX 4090 单流 RTF 4.78、首音频 156ms；H100 单流反而不及 4090，强项在批量。`RTF > 1.0` 即快于实时。
- **流式是分层的**：CUDA Graph 每步照常重放，只是把码本 ID 按 `chunk_size` 聚块、用 25 帧左上下文滑窗解码成音频。chunk 越小延迟越低、解码开销越大。
- **适合场景**：单卡单流实时合成；大批量 batch 或已在用 vLLM 的团队，收益不大。

核心数据（GitHub API 2026-08-08 验证）：

```
Stars:     1,293
Forks:     190
许可证:   MIT
主要语言: Python
默认分支: main
创建:      2026-02-16
最新版本: v0.3.1 (2026-07-15)
```

## 项目定位

官方描述是 **"Real-time text-to-speech with Qwen3-TTS"**——用 CUDA graph capture 做实时推理，不依赖 Flash Attention、vLLM 或 Triton，只用 `torch.cuda.CUDAGraph`，同时支持流式和非流式生成。

它和别的加速路线的区别在于不换引擎：

| 方案 | 依赖 | 加速方式 | 流式 |
|------|------|----------|------|
| **Faster Qwen3-TTS** | PyTorch + transformers | CUDA Graph + StaticCache | 支持 |
| Qwen3-TTS 原生 | PyTorch | 无 | 不支持 |
| vLLM 加速 | vLLM | 换 serving 引擎 | 支持 |

它不重写模型、不接 vLLM、不手写注意力内核，完全留在 PyTorch/HuggingFace 生态内。这是它和"上 vLLM 换引擎"路线最大的差别，也是它只在一张卡上跑单流时更有优势的原因。

## 支持的模型与三种生成模式

| 模型 | 大小 | 用途 |
|------|------|------|
| Qwen/Qwen3-TTS-12Hz-0.6B-Base | 0.6B | 基础模型，语音克隆 |
| Qwen/Qwen3-TTS-12Hz-1.7B-Base | 1.7B | 基础大模型，语音克隆 |
| Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice | 1.7B | 预定义音色 |
| Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign | 1.7B | 指令式音色设计 |

三种生成模式共用同一套 CUDA Graph 机制，速度几乎相同（见下文 benchmark）。

## 加速原理：捕获解码步骤，而不是优化单个内核

Qwen3-TTS 每个解码步骤跑两个自回归 Transformer：

| 组件 | 层数 | 作用 |
|------|------|------|
| **Talker** | 28 层 | 从文本生成第一个码本 token |
| **Code Predictor** | 5 层 | 生成 15 个额外码本 token，组成一帧完整音频 |

每个步骤要启动约 **500 次小型 CUDA 内核**。在标准 Python 循环里，GPU 大部分时间在等 CPU 下发下一条指令，而不是在算。瓶颈是内核启动开销（kernel launch overhead），不是算子本身慢。

CUDA Graph 的思路是把这个固定形状的步骤录制成一张图，之后每次直接重放，删掉 Python 与内核之间的往返：

```
捕获前：Python → 内核1 → Python → 内核2 → ... → Python → 内核500
捕获后：一次 CUDAGraph 重放，GPU 串行执行全部 500 个内核
```

能这样做的前提是**张量形状全程不变**。项目直接用 `transformers` 自带的 `StaticCache`：预先分配固定大小的 KV 张量，注意力层内部用 `cache.update()` 原地写入，配合固定的 `cache_position` 缓冲，单 token 解码时所有形状都固定，天然可捕获。外加一个小的优化：把逐 token 的重复惩罚（repetition penalty）从 Python 循环改成 `torch.where` 一次性向量化，去掉每步的 CPU↔GPU 同步。

## 为什么加速比从 1.2x 到 9.8x 不等

CUDA Graph 消除的是 CPU 到 GPU 的内核分发空隙，加速比取决于 CPU/GPU 之间的失衡程度。GPU 比 CPU 快得越多（或 CPU 越弱），能找回的空闲时间越多，加速越明显。

benchmark 里两个例外是 Jetson AGX Orin 和 DGX Spark——它们恰好配了很强的 CPU 配上相对普通的 GPU。DGX Spark（GB10）的 20 核 Arm CPU 本身就能把基线推到 RTF 1.19（已经快于实时），可消除的分发开销不多，所以只加 1.2–1.9x。反过来，RTX 4090、H100 这类 GPU 头快、CPU 分发跟不上的组合，加速比普遍落在 3–9x。

## 基准测试：0.6B 模型

| GPU | 基线 RTF | 基线 TTFA | CUDA Graph RTF | CUDA Graph TTFA | 加速比 |
|-----|---------|-----------|----------------|-----------------|--------|
| RTX 4090 | 0.82 | 800ms | **4.78** | **156ms** | 5.8x / 5.1x |
| H100 80GB HBM3 | 0.435 | 1,474ms | **3.884** | **228ms** | 8.9x / 6.5x |
| RTX 4060 (Windows) | 0.23 | 2,697ms | **2.26** | **413ms** | 9.8x / 6.5x |
| DGX Spark (GB10) | 1.17 | 567ms | 2.56 | 280ms | 2.2x / 2.0x |
| Jetson AGX Orin 64GB | 0.179 | 3,641ms | 1.307 | 597ms | 7.3x / 6.1x |
| Tesla T4 16GB | 0.467 | 1,671ms | **1.068** | **901ms** | 2.3x / 1.9x |

## 基准测试：1.7B 模型

| GPU | 基线 RTF | 基线 TTFA | CUDA Graph RTF | CUDA Graph TTFA | 加速比 |
|-----|---------|-----------|----------------|-----------------|--------|
| RTX 4090 | 0.82 | 850ms | **4.22** | **174ms** | 5.1x / 4.9x |
| H100 80GB HBM3 | 0.439 | 1,525ms | **3.304** | **241ms** | 7.5x / 6.3x |
| RTX 4060 (Windows) | 0.23 | 2,905ms | **1.83** | **460ms** | 7.9x / 6.3x |
| DGX Spark (GB10) | 1.01 | 661ms | 1.87 | 400ms | 1.9x / 1.7x |
| Jetson AGX Orin 64GB | 0.183 | 3,573ms | 1.089 | 693ms | 6.0x / 5.2x |
| Tesla T4 16GB | 0.453 | 1,811ms | **0.925** | **1,096ms** | 2.0x / 1.7x |

**怎么读这张表**：
- `RTF` = Real-Time Factor，生成 1 秒音频所用的秒数。**RTF > 1.0 表示快于实时**，越大越快。例如 RTF 4.78 意味着生成 1 秒音频只需要约 0.21 秒。
- `TTFA` = Time-to-First-Audio，从开始生成到第一块可播放音频出来的延迟。
- 加速比格式是「吞吐量加速 / TTFA 加速」。

这里有三点要提醒自己别过度推断：

- 基线 TTFA 用的是社区 `Qwen3-TTS-streaming` 分支（或本项目无 CUDA Graph 的动态缓存流式路径）。官方 `Qwen3-TTS` 仓库目前不支持流式，只看官方的话它的"TTFA"其实是整段音频全部生成完的时间。
- RTX 4090 单流 RTF 反超 H100，是因为它的 boost 时钟更高（约 2.5 GHz vs 1.8 GHz）。H100 的强项是批量处理，不是单流。
- 这些数字是特定版本、固定文本的实测，不能直接推出"我的长文本也快这么多"。T4 上 0.6B 只到 RTF 1.068，边缘设备仍要按自己的硬件实测。

## 流式生成

CUDA Graph 天然支持流式：predictor 和 talker 的图每步照常重放，只是把生成的码本 ID 每 `chunk_size` 步聚一个块，再用滑动窗口（25 帧左上下文，对齐上游 codec 的 `chunked_decode`）解码成音频吐出来。图的逻辑不变，变的只是控制流。

**chunk_size 与性能（Jetson AGX Orin，0.6B）**：

| chunk_size | TTFA | RTF | 每 chunk 音频时长 |
|------------|------|-----|----------------|
| 1 | 240ms | 0.750 | 83ms |
| 2 | 266ms | 1.042 | 167ms |
| 4 | 362ms | 1.251 | 333ms |
| 8 | 556ms | 1.384 | 667ms |
| 12 | 753ms | 1.449 | 1000ms |
| 非流式 | — | 1.57 | 全部一次 |

规律是：chunk 越小延迟越低，但解码开销越大。`chunk_size=2` 是 Jetson 上保持实时的最小值；在更快的 GPU 上 `chunk_size=1` 通常仍在 RTF 1.0 以上。Python 的流式方法是拉取式生成器，调用方要下一个块才准备下一个块；本地实时播放建议用 `StreamPlayer` 这种队列式播放器，避免每块阻塞导致生成和播放无法重叠。

---

## 语音克隆：两种模式

`generate_voice_clone` 通过 `xvec_only` 参数暴露两种克隆模式：

| 模式 | xvec_only | 特点 |
|------|-----------|------|
| **Simple（x-vector）** | True | 只取 speaker embedding，prefill 更短、语言切换干净、不需要 ref_text |
| **Advanced（ICL）** | False（默认） | 整段参考音频放进上下文，需要准确的 ref_text，开头可能有一点伪影 |

默认是 ICL 模式，和上游 Qwen3-TTS 一致。x-vector 模式作为可选留在那，用于更干净的语言切换和更短的 prefill。

### ICL 模式的解码上下文

12Hz codec 用因果的 `chunked_decode`：每帧用前面的帧作为声学上下文重建。ICL 模式下参考音频的 codec token 会被拼到生成 token 前面，解码完再裁剪掉参考部分。没有这一步，codec 解码器冷启动没有声音上下文，模型生成的 token 对会被用错误的音色重建。这一步是自动处理的。

### ICL 音素伪影与修复

ICL 模式下模型的 prefill 以参考音频最后一个 codec token 结尾，所以第一个生成的 token 会以参考末尾的音素为条件。如果参考音频在单词中间结束，那个音素会渗进生成的语音开头——比如参考以 "thumbs" 结尾，开头会带出类似 "mz" 的声音。

修复很简单：**在编码前给参考音频末尾拼 0.5 秒静音**。这样模型起始上下文是静音，生成的语音从第一帧就干净。项目在 `_prepare_generation()` 里自动应用，不需要用户手动处理。

### 预计算 Speaker Embedding

生产环境可以一次性提取 speaker embedding 并复用，省掉每次请求都编码参考音频的开销：

```python
# 1. 一次性提取 speaker embedding
python examples/extract_speaker.py --ref_audio voice.wav --output speaker.pt

# 2. 之后用 embedding 实时生成（多语言各跑一次）
python examples/generate_with_embedding.py --speaker speaker.pt --text "Hello!" --language English --output en.wav
python examples/generate_with_embedding.py --speaker speaker.pt --text "Bonjour!" --language French --output fr.wav
```

x-vector 模式的优势在于：每种语言用原生发音（无口音漂移）、prefill 更短视频填充少、运行时不需要参考音频，只带一个很小的 embedding 文件。

---

## 安装

环境要求：Python 3.10+、PyTorch 2.5.1+、带 CUDA 的 NVIDIA GPU。

```bash
pip install faster-qwen3-tts
```

**PyTorch 版本**：CUDA-graph capture 在 `torch<=2.5.0` 上不可靠，捕获可能报 "operation not permitted when stream is capturing"。项目验证 2.5.1+ 可用，把它定为最低支持版本。

**Blackwell（RTX 50xx）**：需要 CUDA 12.8 的 PyTorch wheel。默认安装在这类卡上失败的话，装 `cu128` 构建（PyTorch 2.7+）。

**Driver / CUDA 不匹配（T4、A10G 等 CUDA 12.4 主机）**：`pip install` 拉到的默认 PyTorch wheel 基于较新的 CUDA toolkit。如果驱动比 toolkit 旧——AWS、Azure ML、很多 Colab/T4 机器常见——`torch.cuda.is_available()` 会返回 False 并报 "CUDA initialization: The NVIDIA driver on your system is too old"。按 `nvidia-smi` 右上角的 CUDA Version 装匹配的 wheel：

```bash
pip install "torch==2.5.1" "torchaudio==2.5.1" --index-url https://download.pytorch.org/whl/cu124
```

### 可选的 GGML 后端

项目还带一个实验性的 GGML 适配器，接 Pascal 的 `qwentts.cpp` 运行时。Torch/CUDA-graph 仍是默认后端，GGML 是选装，用独立的原生 wheel 包，不影响主安装路径：

```bash
pip install "faster-qwen3-tts[ggml]"
faster-qwen3-tts --backend ggml --quant BF16 design \
  --model Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign \
  --instruct "Warm, confident narrator" \
  --text "Welcome to the show." \
  --language English \
  --output out.wav
```

GGML 后端会缓存参考音频的 `.spk` 说话人 latent 和 `.rvq` 声学 latent，也支持直接传预计算的引用。注意它的 ABI 缺口：没有 `non_streaming_mode` 开关、拒绝 base 模型的 `instruct`、KV 缓存长度固定，所以还不能算完全对齐 Torch 后端。

---

## 使用

### Python API

```python
from faster_qwen3_tts import FasterQwen3TTS

model = FasterQwen3TTS.from_pretrained("Qwen/Qwen3-TTS-12Hz-0.6B-Base")

ref_audio = "ref_audio.wav"
ref_text = (
    "I'm confused why some people have super short timelines, yet at the same time "
    "are bullish on scaling up reinforcement learning atop LLMs. "
    "If we're actually close to a human-like learner, then this whole approach "
    "of training on verifiable outcomes is doomed."
)

# 非流式——一次返回全部音频
audio_list, sr = model.generate_voice_clone(
    text="Hello world!",
    language="English",
    ref_audio=ref_audio,
    ref_text=ref_text,
)
```

流式用 `generate_voice_clone_streaming`，配合仓库 `examples/` 里的 `StreamPlayer` 实时播放：

```python
from examples.audio import StreamPlayer

play = StreamPlayer()
try:
    for audio_chunk, sr, timing in model.generate_voice_clone_streaming(
        text="What do you mean that I'm not real?",
        language="English",
        ref_audio=ref_audio,
        ref_text=ref_text,
        chunk_size=8,  # 8 步 ≈ 每 chunk 667ms 音频
    ):
        play(audio_chunk, sr)
finally:
    play.close()
```

服务前可以显式调用 `model.warmup(prefill_len=100)` 预配模型（Torch 后端捕获 CUDA Graph，GGML 后端是安全的空操作）；普通生成也会按需做惰性准备。

### CLI

语音克隆（参考音频）：

```bash
faster-qwen3-tts clone \
    --model Qwen/Qwen3-TTS-12Hz-1.7B-Base \
    --text "What do you mean that I'm not real?" \
    --language English \
    --ref-audio ref_audio.wav \
    --ref-text "I'm confused why some people have super short timelines..." \
    --output out.wav
```

CustomVoice（预定义音色）：

```bash
faster-qwen3-tts custom --model Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice --list-speakers
faster-qwen3-tts custom \
    --model Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice \
    --speaker aiden \
    --text "What do you mean that I'm not real?" \
    --language English \
    --output out.wav
```

VoiceDesign（指令式）：

```bash
faster-qwen3-tts design \
    --model Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign \
    --instruct "Warm, confident narrator with slight British accent" \
    --text "Welcome to the show." \
    --language English \
    --output out.wav
```

流式生成并写 WAV（写完后打印 RTF）：

```bash
faster-qwen3-tts custom \
    --model Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice \
    --speaker aiden \
    --text "What do you mean that I'm not real?" \
    --language English \
    --output out.wav \
    --streaming
```

### Demo UI

一个最小 Web UI，实时流式出音频并显示 TTFA、RTF 指标。默认走 GGML/qwentts.cpp，带一个后端开关可以和 Torch CUDA-graph 后端对比：

```bash
pip install -e ".[demo,ggml]"
python demo/server.py --backend ggml
# 打开 http://localhost:7860
```

功能：上传 WAV 或接麦克风做语音克隆、Voice Design、GGML/Torch 后端切换、流式/非流式切换、可调 chunk_size、实时 TTFA/RTF、WAV 下载。

### OpenAI 兼容 API 服务器

`examples/openai_server.py` 暴露遵循 OpenAI TTS 契约的 `POST /v1/audio/speech`，可直接配 OpenWebUI、llama-swap 等客户端：

```bash
pip install "faster-qwen3-tts[demo]"
python examples/openai_server.py \
    --ref-audio ref_audio.wav \
    --ref-text "I'm confused why some people..." \
    --language English \
    --port 8000
```

调用：

```bash
curl http://localhost:8000/v1/audio/speech \
    -H "Content-Type: application/json" \
    -d '{"model": "tts-1", "input": "Hello world.", "voice": "alloy", "response_format": "wav"}' \
    --output speech.wav
```

暴露多音色时，用 `--voices voices.json` 传一个把音色名映射到参考音频配置的 JSON，请求里的 `voice` 值会路由到对应条目。WAV/PCM 边生成边流式出块，MP3 需要 `pydub`。

---

## 在自己的硬件上跑基准

基准从源码跑，只需要 `uv` 和 `./setup.sh`：

```bash
git clone https://github.com/andimarafioti/faster-qwen3-tts
cd faster-qwen3-tts
./setup.sh
./benchmark.sh            # 全部模型；或 ./benchmark.sh 0.6B / 1.7B 只测单个
```

Windows 原生对应 `setup_windows.bat` 和 `benchmark_windows.bat`。结果存成 `bench_results_<GPU_NAME>.json`，音频样本存为 `sample_0.6B.wav` / `sample_1.7B.wav`。

三种生成模式速度几乎一致，用 `benchmarks/compare_modes.py` 可复现。0.6B、`chunk_size=8` 的示例：

| 模式 | TTFA (ms) | RTF | ms/step |
|------|----------|------|---------|
| VoiceClone xvec | 152 ± 11 | 5.470 ± 0.032 | 15.2 ± 0.1 |
| VoiceClone full ICL | 149 ± 1 | 5.497 ± 0.026 | 15.2 ± 0.1 |
| CustomVoice | 148 ± 1 | 5.537 ± 0.020 | 15.0 ± 0.1 |

---

## 常见问题

**为什么需要 PyTorch 2.5.1+？** CUDA-graph capture 在 `torch<=2.5.0` 上不可靠，会报 "operation not permitted when stream is capturing"。2.5.1+ 已验证可用。

**静态缓存和动态缓存有什么区别？** 数学上等价，但内核路径不同。静态缓存用固定最大长度的 KV 缓冲加显式注意力掩码，动态缓存按当前序列长度、常走 `is_causal=True` 免掩码。在 BF16/TF32 下不同内核的求和处理顺序不位精确，输出可能略有差异。项目用动态缓存 parity 模式在测试里保证和上游逻辑一致，快路径优先吞吐。

**`non_streaming_mode` 是控制音频输出流式吗？** 不是，它继承自上游 Qwen3-TTS，控制的是**文本输入**是整段喂还是逐步喂（`non_streaming_mode=None` 时各方法保留上游默认值）。和这里的音频输出流式是两回事。在 RTX 4090、1.7B、ICL、chunk_size=8 下，两种文本喂法对性能几乎没影响（TTFA ≈159ms，RTF 4.87 vs 4.85）。

**chunk_size 怎么选？** 实时交互用小一点的（延迟低），追求吞吐用大的。`chunk_size=2` 是 Jetson 上保持实时的下限，快速设备上 `chunk_size=1` 也行。

**x-vector 和 ICL 模式用哪个？** 不需要指令微调的话 x-vector 更稳，prefill 短、无伪影风险、语言切换干净；ICL 质量上限更高但要求 ref_text 准确，且用 `xvec_only=True` 时 `instruct` 指令遵循不稳定（实验性），ICL 模式下指令遵循更可预测。

---

## 什么时候值得用

**推荐用**：单卡、单流的实时语音合成——实时语音助手、Demo、本地服务。它的优势正好落在"不想为此上 vLLM 换引擎"的场景，且 4090 级消费卡就能跑到 RTF 4+。

**先等等**：需要大规模批量推理的，H100 这类卡的优势在批量才体现，且它的单流 RTF 反而不如 4090；已经在用 vLLM 的团队，加一个 CUDA Graph 后端多半不如直接复用现有推理栈。GGML 后端目前还是实验性的，别在生产里当默认。

---

## 参考资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/andimarafioti/faster-qwen3-tts |
| 工程博客 | https://github.com/andimarafioti/faster-qwen3-tts/blob/main/BLOG.md |
| Qwen3-TTS 原生仓库 | https://github.com/QwenLM/Qwen3-TTS |
| PyTorch CUDAGraph 文档 | https://pytorch.org/docs/stable/generated/torch.cuda.CUDAGraph.html |