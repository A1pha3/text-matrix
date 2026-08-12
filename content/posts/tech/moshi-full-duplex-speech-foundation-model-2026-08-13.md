---
title: "Moshi 深度解读：第一个开源的 full-duplex 实时语音对话 foundation model，它怎么做到 200ms 延迟同时建模用户 + Moshi + 内心独白三条流"
date: 2026-08-13T00:25:00+08:00
draft: false
tags: ["AI Agent", "Speech", "Foundation Model", "Audio Codec", "Real-time", "Full-duplex", "开源项目深拆", "MLX", "Rust", "PyTorch"]
categories: ["技术笔记"]
description: "kyutai-labs/moshi 是 2024-2025 年开源的 first full-duplex real-time speech-text foundation model，同时建模用户音频流 + Moshi 自己音频流 + 自己 inner monologue 文本流，理论延迟 160ms，实测 200ms on L4 GPU。三层架构：Mimi 神经音频编解码（12.5Hz / 1.1kbps）+ Depth Transformer（建模 codebook 内时间步）+ Temporal Transformer（7B 参数，建模跨时间步）。三个 inference stack：PyTorch（研究）+ MLX（iPhone/Mac 本地）+ Rust/Candle（生产）。本文拆 Moshi 怎么做到'边听边说边思考'、为什么 inner monologue 是关键设计、以及它跟 Hibiki / Delayed Streams Modeling 的家族关系。"
slug: "moshi-full-duplex-speech-foundation-model"
band: "review"
gates: ["事实性", "去AI味", "观点依据"]
github_repo: "kyutai-labs/moshi"
---

## 这篇文章在回答什么

`kyutai-labs/moshi` 是 2024-2025 年开源的第一个真正做到 **full-duplex** 的实时语音对话 foundation model。它不是"语音版 ChatGPT"——它是同时建模 **三条流** 的统一架构：

1. **用户音频流**——你说话的声音
2. **Moshi 自己的音频流**——Moshi 回复你的声音
3. **Moshi 的 inner monologue 文本流**——Moshi 心里想的文字（**Moshi 没说出来的话**）

这条 inner monologue 是 Moshi 跟其他实时语音模型最大的差别——Moshi 不是"先在脑子里想好再说话"，而是"一边听一边想一边说"。它让 Moshi 的语音生成质量**显著提升**——inner monologue 起到语言模型 grounding 的作用。

技术指标：

| 指标 | 数值 |
|---|---|
| 理论延迟 | **160ms**（80ms Mimi frame + 80ms acoustic delay） |
| 实测延迟 | **200ms on L4 GPU** |
| Mimi codec | 24kHz → 12.5Hz / **1.1 kbps** 带宽 |
| Temporal Transformer | **7B 参数** |
| 模型变体 | Moshiko（男声）/ Moshika（女声） |
| Inference stack | PyTorch / MLX / Rust+Candle |

把这三个数字放一起——160ms 理论延迟 + 12.5Hz frame rate + 7B Temporal Transformer——你大概能猜到 Moshi 解决的是什么：**让 7B 参数的大模型在实时音频流上不卡顿**。

这篇文章做四件事：

1. 拆「**full-duplex**」到底是什么——为什么它不是又一轮"实时语音"
2. 拆 Moshi 的三层架构：Mimi codec + Moshi LM（Depth + Temporal Transformer）+ streaming inference
3. 拆三个 inference stack（PyTorch / MLX / Rust）的工程含义
4. 把 Moshi 放到语音 AI 家族——它和 Hibiki / Delayed Streams Modeling / 闭源 GPT-4o voice 的关系

## 一、什么是 full-duplex，为什么 Moshi 是第一个

「实时语音对话」这个词 2024-2025 年被用烂了。把它拆开，至少有三种"实时"：

| 类型 | 含义 | 代表 |
|---|---|---|
| **Turn-taking** | 你说一句，AI 说一句；互相等待对方说完 | 早期 Siri / 现在的 GPT-4o voice mode（部分场景） |
| **Half-duplex streaming** | AI 流式生成语音，但**只能在你说完后**才开始 | Cascade ASR + LLM + TTS（OpenAI Realtime API 部分模式） |
| **Full-duplex** | 你说话的同时 AI 也能说话，**两路音频流同时存在** | Moshi / Kyutai Hibiki |

**full-duplex** 的工程含义是**同时建模两条音频流**——Moshi 模型有两个 audio stream：

> Moshi models **two streams of audio**: one corresponds to Moshi speaking, and the other one to the user speaking.

这听起来抽象，实际工程意义巨大：

- **传统 turn-taking**：你闭嘴 → ASR 检测停顿 → LLM 生成回复 → TTS 合成语音。总延迟 = ASR 停顿 + LLM 首 token + TTS 首帧 ≈ 800-2000ms
- **Half-duplex streaming**：你闭嘴 → ASR stream → LLM stream → TTS stream。但 ASR 还要等你说完才能开始
- **Full-duplex**：Moshi 从不"等你说完"——它持续接收你的音频流，同时持续生成自己的音频流。延迟 = 1 帧 + 声学延迟 ≈ 160-200ms

200ms 是什么量级？人类对话的自然轮换间隔是 200-500ms。**Moshi 已经接近真人对话的反应速度**。

这是为什么 Moshi 不是"又一轮"实时语音——它是第一个开源的、把 full-duplex 做成 foundation model 形态的项目。闭源 GPT-4o voice 的 full-duplex 模式也是这个方向，但 Moshi 是**开源 + 可复现 + 可微调**的。

## 二、Mimi codec：把音频变成可建模的 token

Moshi 的核心依赖是 **Mimi**——一个流式神经音频编解码器。README 给的关键指标：

| Codec | 采样率 | Frame rate | Bitrate | Streaming |
|---|---|---|---|---|
| **Mimi** | 24 kHz | **12.5 Hz** | **1.1 kbps** | ✅ 80ms latency |
| SpeechTokenizer | — | 50 Hz | 4 kbps | ❌ non-streaming |
| SemantiCodec | — | 50 Hz | 1.3 kbps | ❌ non-streaming |

Mimi 在 **frame rate（12.5 Hz vs 50 Hz）** 上显著低于现有 codec——这一项决定了 Moshi 的 autoregressive 步数。

为什么 12.5 Hz 是关键？因为**文本 token 的典型生成速度是 3-4 Hz**。Mimi 把音频 frame rate 拉低到接近文本，让 Moshi 的 autoregressive 步数**接近 LLM**——而不是 50 Hz 那种"每秒 50 步"的疯狂开销。

Mimi 的技术细节（README 摘录）：

> Mimi builds on previous neural audio codecs such as SoundStream and EnCodec, adding a Transformer both in the encoder and decoder, and adapting the strides to match an overall frame rate of 12.5 Hz.
>
> Similarly to SpeechTokenizer, Mimi uses a distillation loss so that the first codebook tokens match a self-supervised representation from WavLM, which allows modeling semantic and acoustic information with a single model.
>
> Finally, and similarly to EBEN, Mimi uses **only an adversarial training loss**, along with feature matching, showing strong improvements in terms of subjective quality despite its low bitrate.

三个关键设计：

1. **Transformer in encoder & decoder**——区别于 SoundStream / EnCodec 的纯 CNN 架构。Transformer 让 Mimi 能捕捉长程依赖。
2. **WavLM distillation**——第一个 codebook token 匹配 WavLM 自监督特征，让 Mimi **同时建模语义（语言内容）和声学（音色 / 韵律）**。一个模型，两个用途。
3. **纯对抗训练 + feature matching**——不用重建损失（L1 / L2），只用对抗损失。EBEN 也证明了这条路能显著提升主观质量。

把 1.1kbps 跟 SoundStream / EnCodec 的几 kbps 摆在一起看——**Mimi 的压缩比是同行的 3-5 倍**，主观质量更好。

## 三、Moshi 的两层 Transformer

Moshi 的 LM 由两个 Transformer 组成：

> A small **Depth Transformer** models inter-codebook dependencies for a given time step, while a large, **7B-parameter Temporal Transformer** models the temporal dependencies.

两个 Transformer 的分工：

| Transformer | 角色 | 大小 |
|---|---|---|
| **Depth Transformer** | 同一时间步内，跨 codebook（codebook 0-15）的依赖 | 小（具体参数 README 未明示，估计 <100M） |
| **Temporal Transformer** | 跨时间步的依赖 | **7B 参数** |

Mimi 把音频 tokenize 成 **多个 codebook**（类似 SoundStream / EnCodec 的 RVQ——residual vector quantization）。每个时间步有多个 codebook token。Depth Transformer 负责**同一时间步内不同 codebook 之间的关系**（先 codebook 0、再 codebook 1、...、再 codebook 15），Temporal Transformer 负责**跨时间步的 token 序列**。

这跟语言模型里的 **detokenization 顺序**类似——先预测第一个 sub-token，再预测第二个 sub-token，最后 token 才完整。

7B Temporal Transformer 是 Moshi 的主要参数负担。README 的 FAQ 解释为什么不进一步量化：

> Can Moshi run on a M1, or smaller GPUs?
> Sadly we do not think this is currently possible. Quantizing beyond 4 bits lead to dramatic decrease in quality, see PR #58.

**4-bit 是 quality 的底线**——再压缩质量就崩了。这是 foundation model 的常见困境：模型大了能力变强，但部署成本变高。

## 四、Inner monologue：Moshi 的灵魂设计

Moshi 最反直觉的设计是 **inner monologue**——Moshi 不仅生成 audio token，还同时生成 **text token** 对应自己"心里想的"。README：

> Along with these two audio streams, Moshi predicts text tokens corresponding to its own speech, its **inner monologue**, which greatly improves the quality of its generation.

inner monologue 的工作机制：

- Moshi 的输入：用户音频流（来自 mic）+ Moshi 自己之前的音频流 + Moshi 自己之前的 inner monologue
- Moshi 的输出：Moshi 自己的音频流（合成回复）+ Moshi 自己的 inner monologue（心声）

注意：**inner monologue 是 Moshi 自己的，不是用户的**。Moshi 听你说话 + 自己内心 OS + 自己说出声。三个流并行。

为什么 inner monologue 能显著提升质量？

类比到 LLM：**inner monologue 起到 chain-of-thought 的作用**。让模型"先想好再说话"，比"边想边说"更连贯。Moshi 把这个机制搬到了流式语音场景——inner monologue 是它的"实时 chain-of-thought"。

但 inner monologue 不暴露给用户——用户只听到 Moshi 的音频。inner monologue 是 **grounding 通道**，不是输出通道。

这是 Moshi 跟其他 "streaming TTS" 模型最大的区别。其他模型要么 turn-based（先想好再说）、要么 streaming without thought（Moshi 的反面）。**Moshi 是 streaming with thought**——这是它能保持 200ms 延迟同时高质量的关键。

## 五、三个 inference stack：研究 / 本地 / 生产

Moshi 的代码组织对应三种使用场景：

| Stack | 路径 | 场景 | 关键指标 |
|---|---|---|---|
| **PyTorch** | `moshi/` | 研究 / 实验 | 24GB GPU 起步，不支持量化 |
| **MLX** | `moshi_mlx/` | iPhone / Mac 本地 | int4 / int8 / bf16，MacBook Pro M3 测试 |
| **Rust / Candle** | `rust/` | 生产部署 | int8 + CUDA / Metal，Python bindings (`rustymimi`) |

### 5.1 PyTorch stack

路径：`moshi/moshi/`（Python），核心模块：

| 文件 | 行数 | 作用 |
|---|---|---|
| `models/lm.py` | 850 | Moshi 语言模型 |
| `models/tts.py` | 833 | TTS 模块 |
| `quantization/core_vq.py` | 528 | 矢量量化（RVQ） |
| `models/loaders.py` | 514 | 模型加载 |
| `models/compression.py` | 488 | Mimi compression |
| `server.py` | 287 | Gradio server |
| `client.py` | 189 | 命令行 client |
| `client_gradio.py` | 161 | 浏览器 client |

启动命令：

```bash
python -m moshi.server [--gradio-tunnel] [--hf-repo kyutai/moshika-pytorch-bf16]
```

PyTorch 版本不持量化——需要 24GB 显存起步。FAQ 解释了为什么不：

> Can we run quantized Moshi with PyTorch?
> At the moment no, we might look into adding this feature when we get the time. At the moment it is however possible to use the Rust backend, which should run in int8 with CUDA.

PyTorch 是**研究 + tinkering**栈——让研究者用熟悉的框架调 Moshi 的内部，部署交给 Rust/Candle。

### 5.2 MLX stack

路径：`moshi_mlx/`，专为 Apple Silicon 设计。MLX 是 Apple 的 ML 框架，类似 PyTorch 但专为 M-series 芯片优化。

启动命令：

```bash
python -m moshi_mlx.local -q 4   # int4 量化
python -m moshi_mlx.local -q 8   # int8 量化
```

支持 int4 / int8 / bf16 三种量化。在 MacBook Pro M3 上测试过。这是**消费级 Mac 本地跑 full-duplex 7B 语音模型**的可行路径。

### 5.3 Rust / Candle stack

路径：`rust/`，15,803 行 Rust。核心模块：

| 文件 | 行数 | 作用 |
|---|---|---|
| `moshi-server/src/main.rs` | 1164 | Server 入口 |
| `moshi-core/src/lm.rs` | 1117 | Moshi 语言模型 |
| `moshi-core/src/transformer.rs` | 1115 | Temporal Transformer |
| `moshi-backend/src/stream_both.rs` | 828 | 双流 streaming |
| `moshi-server/src/tts.rs` | 797 | TTS |
| `moshi-core/src/conv.rs` | 724 | 卷积层 |
| `moshi-server/src/batched_asr.rs` | 664 | 批处理 ASR |
| `moshi-server/src/py_module.rs` | 650 | Python bindings |
| `moshi-server/src/py_basr_module.rs` | 650 | 批处理 ASR Python bindings |
| `moshi-cli/src/multistream.rs` | 638 | 多流 client |
| `moshi-core/src/seanet.rs` | 468 | Mimi SEANet codec |
| `moshi-core/src/tts_streaming.rs` | 417 | streaming TTS |
| `moshi-core/src/quantization.rs` | 394 | 量化 |
| `mimi-pyo3/src/lib.rs` | 385 | Mimi Python bindings（PyO3） |
| `moshi-core/src/lm_generate_multistream.rs` | 343 | 多流生成 |

启动命令：

```bash
cargo run --features cuda --bin moshi-backend -r -- --config moshi-backend/config.json standalone
# macOS 用 --features metal
```

Rust 是**生产部署**栈——CUDA / Metal 加速 + 量化 + Python bindings（`rustymimi`）。

### 5.4 三个 stack 的工程含义

| 维度 | PyTorch | MLX | Rust |
|---|---|---|---|
| 目标用户 | 研究者 | Apple 开发者 | 生产部署 |
| 量化 | ❌ | ✅ int4/int8/bf16 | ✅ int8 |
| 加速 | CUDA | Metal | CUDA / Metal |
| Python bindings | — | — | ✅ `rustymimi` |
| 延迟优化潜力 | 最低 | 中 | **最高** |

**Mimi 的 Rust 实现 + Python bindings**是关键工程决策——`rustymimi` 让 Python 生态用 Rust 的性能。具体做法：Mimi codec（最热的 inner loop）在 Rust 里跑，wrapper 是 PyO3。

## 六、生产部署：服务端 standalone 模式

Rust 服务器支持 standalone 模式：

```bash
cargo run --features cuda --bin moshi-backend -r -- --config moshi-backend/config.json standalone
```

standalone = Moshi 后端自包含在 standalone worker 里，不需要外部编排。适合小规模部署。

FAQ 提到一个细节：

> Moshi stopped talking after 5 min.
> This is expected on the MLX and Rust implementation. We only use a fixed buffer, and we do not discard past entries.

MLX 和 Rust 实现有 **5 分钟对话窗口限制**——fixed buffer 不丢弃条目，5 分钟后就满了。PyTorch 版本理论上 unlimited 但会衰减，因为**没有 attention sink 机制**。

这是一个有意识的取舍——5 分钟对话窗口对 95% 的真实对话场景够用（电话、客服、辅导），但**超长会议 / 长程任务**需要 attention sink 之类的机制。FAQ 说"We have no attention sink or other mechanism to improve the streaming beyond the finite context used at training"——**当前训练数据是 5 分钟 context**，部署限制是训练限制的忠实映射。

## 七、Moshi 家族：Hibiki / Delayed Streams Modeling

README 末尾给了三个相关项目：

> - **Hibiki: simultaneous speech translation.** Check out the Hibiki repo for more info.
> - **Kyutai Text-To-Speech and Speech-To-Text.** Check out the Delayed Streams Modeling repo for more info.

三个项目共享 Moshi 的 **multi-stream 架构**——同时建模多个 audio stream。

### 7.1 Hibiki：同声传译

Hibiki 把 Moshi 的 full-duplex 架构用到 **simultaneous interpretation**（同声传译）——听英文音频流的同时输出英文音频流 + 输出法文音频流（翻译）。这是 Moshi 架构的自然延伸：**从"两个 speaker 对话"扩展到"两个语言同传"**。

### 7.2 Delayed Streams Modeling：TTS / ASR

Delayed Streams Modeling 是 **TTS + ASR 的统一架构**——同时建模输入音频流（ASR）+ 输出音频流（TTS），跟 Moshi 的 full-duplex 对话模型是同一种架构思想。Kyutai 用同一套 multi-stream 思路解决了三个不同的语音任务：对话 / 同传 / TTS+ASR。

这是 **"one architecture, many tasks"** 的体现——**Moshi 架构的抽象层次比"对话模型"更通用**。它本质上是一个 **multi-stream streaming audio model**，应用到不同任务就是不同的产品。

### 7.3 与 GPT-4o voice 的关系

闭源 GPT-4o voice 模式（2024 年下半年）支持 full-duplex。Moshi 是**开源复现**这一思路的最早项目之一（甚至更早发布，因为 Kyutai 在 2024 年 9 月就 release 了 Moshi demo）。

但**架构选择不同**：

| 维度 | Moshi | GPT-4o voice |
|---|---|---|
| 开源 | ✅ | ❌ |
| 可微调 | ✅ | ❌ |
| Inner monologue | ✅ | 未知 |
| Frame rate | 12.5 Hz | 未知 |
| Temporal model | 7B Transformer | 未知 |
| 延迟 | 160-200ms | ~300ms |

OpenAI 没有公开 GPT-4o voice 的架构细节，但 Moshi 公开了几乎所有——这是**开源 vs 闭源** 在 frontier model 上的又一次分水岭。

## 八、Moshi 的工程取舍

### 8.1 模型 + 数据 + 部署 的三方平衡

Moshi 的设计在三个维度上做平衡：

1. **模型能力**——7B Temporal Transformer + inner monologue，质量优先
2. **数据需求**——训练数据未公开，但 FAQ 暗示是 5 分钟 context 的训练样本
3. **部署成本**——24GB GPU 起步（PyTorch），4-bit 量化是质量底线

**取舍**：Moshi 选了**能力优先 + 部署成本妥协**。这跟大多数 frontier model 一样——能力提升的边际回报超过部署成本上升。但**5 分钟对话窗口**是这条线的硬约束——超过这个窗口质量衰减，意味着 Moshi 不适合**长程 agent 任务**。

### 8.2 不公开训练数据

FAQ 明确：

> Will you release the dataset?
> We will not release the pre-training dataset.

这是基础模型的常见做法——**训练数据是核心 IP**。Moshi 开放了模型权重 + 推理代码 + 架构细节，但不开放训练数据。这跟 Mistral / Llama 系列的策略一致。

### 8.3 不开放微调代码

FAQ：

> Will you release training code?
> Some finetuning code can be found in the kyutai-labs/moshi-finetune repo.

**finetune 是开放**的，但**pretrain 训练代码不开放**。这是合理的——finetune 代码有助于社区构建应用，pre训练代码揭示的是**最核心的工程能力**。

### 8.4 inner monologue 训练成本

Moshi 的 inner monologue 需要 **speech-text paired data**——同一段语音 + 对应的文本。**这种数据的获取成本极高**（需要人工标注，或者用 ASR 转写但 ASR 误差影响 inner monologue 质量）。这是 Moshi 的**核心数据资产**，不开放是合理的。

## 九、Moshi 在 AI 生态的位置

把 Moshi 放到 2025 年的 AI 生态：

| 维度 | Moshi | OpenAI Voice | ElevenLabs | Kyutai Hibiki |
|---|---|---|---|---|
| **形态** | 开源 FM | 闭源产品 | 闭源产品 | 开源 FM |
| **Full-duplex** | ✅ | ✅ | ❌ | ✅ |
| **实时延迟** | 160-200ms | ~300ms | N/A (TTS) | 160-200ms |
| **Inner monologue** | ✅ | 未知 | ❌ | ✅ |
| **本地部署** | ✅ (MLX/Rust) | ❌ | ❌ | ✅ |
| **可微调** | ✅ | ❌ | ❌ | ✅ |
| **多语言** | English only | 多语言 | 多语言 | 多语言 |

Moshi 的差异化一句话总结：**开源 + full-duplex + inner monologue + 实时延迟 160ms**——这是 2025 年开源语音 AI 的**完整技术栈**。

## 十、落地路径

按代价从小到大排：

**1. 在线 demo（最快）。** https://moshi.chat 直接跟 Moshi 对话——latency 200ms 级。零成本。

**2. MLX 本地（MacBook）。** `pip install -U moshi_mlx`，跑 `python -m moshi_mlx.local -q 4`。MacBook Pro M3 可跑 int4 量化。

**3. Rust + CUDA 自建。** 装 Rust toolchain + CUDA，`cargo run --features cuda --bin moshi-backend -r -- --config moshi-backend/config.json standalone`。L4 GPU 实测 200ms 延迟。

**4. 浏览器 web UI。** Moshi server 自动提供 `localhost:8998`，浏览器打开即用。注意 **HTTPS**（Rust 版本默认）会有"unsafe site"警告，FAQ 给出了 Chrome bypass 步骤。

**5. 微调自己的 Moshi。** `git clone https://github.com/kyutai-labs/moshi-finetune`。可以定制声音 / 个性 / domain vocabulary。

**6. 集成到产品。** 用 `rustymimi` 把 Mimi codec 嵌入 Python 应用，或用 Moshi API 接入 full-duplex 语音交互。

## 十一、一章小结

Moshi 是 2024-2025 年开源的第一个真正做到 **full-duplex** 的实时语音对话 foundation model。它把"语音 AI"从"先想再说"推到"边听边想边说"——inner monologue 是这个推力的核心。

四件事连起来：

1. **架构**——Mimi codec（12.5Hz / 1.1kbps）+ Moshi LM（Depth Transformer + 7B Temporal Transformer）+ 双流 streaming
2. **灵魂**——inner monologue 让 Moshi 在 200ms 延迟下保持高质量，是 Moshi 跟其他 streaming voice model 的最大差别
3. **部署**——三个 stack：PyTorch（研究）/ MLX（Mac 本地）/ Rust+Candle（生产），覆盖从研究到生产的全链路
4. **家族**——Moshi 架构是 multi-stream streaming audio model，Hibiki（同传）/ Delayed Streams Modeling（TTS+ASR）/ Moshi（对话）是同一架构的不同应用

一句话版本：**Moshi 把"语音对话"从 turn-based 推到 full-duplex，把"实时生成"从无脑 streaming 推到 streaming with thought——开源的 GPT-4o voice 替代品的雏形**。

## 为什么不去

> **为什么 Moshi 选 12.5Hz 而不是 25Hz / 50Hz？** 因为**自回归步数直接决定延迟**。12.5Hz 让 Moshi 每秒只做 12.5 步自回归（接近 LLM），25Hz 是 25 步，50Hz 是 50 步。**理论延迟 160ms 拆解：80ms Mimi frame + 80ms acoustic delay**——如果 frame rate 翻倍到 25Hz，理论延迟就到 240ms（40ms + 200ms），用户对话体验明显下降。**frame rate 是低延迟的根本工程决策，不是优化**。
>
> **为什么 Moshi 不直接用 EnCodec / SoundStream 现有 codec？** 因为现有 codec 的 **frame rate 太低**（50Hz）或 **不支持 streaming**。Mimi 的核心创新是**把 frame rate 拉到接近文本 token 的 12.5Hz**，同时保持 streaming（80ms latency）。这是 Mimi 跟其他 codec 的根本差异——**不是简单的"再训练一个 codec"，是按 Moshi 需求定制的 codec**。
>
> **为什么不开放训练数据 + pretrain 代码？** 因为**训练数据是基础模型最核心的 IP**。开放权重 + 推理代码 + 架构细节 = 让社区能复现 + 微调 + 部署；开放训练数据 + pretrain 代码 = 让竞争对手能 pretrain 自己的同架构模型。**Moshi 的策略是"开放推理、保留训练"——这是开源基础模型的常见平衡点**。moshi-finetune 仓库是开放 finetune 的妥协——社区可以基于 Moshi 训自己的下游任务，但不能从零 pretrain。