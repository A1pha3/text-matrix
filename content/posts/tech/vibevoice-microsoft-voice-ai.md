---
title: "VibeVoice：微软开源语音模型家族，把 60 分钟长音频带进 ASR"
date: "2026-04-29T11:30:00+08:00"
lastmod: 2026-10-02T00:00:00+08:00
draft: false
tags: ["语音AI", "微软", "ASR", "TTS", "开源"]
categories: ["技术笔记"]
description: "VibeVoice 是微软开源的语音模型家族：ASR 单次转写 60 分钟长音频、支持 50+ 语言与热词，2026 年扩展出流式识别与 CPU 端 BitNet 推理；Realtime-0.5B 提供实时 TTS。本文拆解其架构、用法与适用边界。"
slug: vibevoice-microsoft-voice-ai
github_repo: "microsoft/VibeVoice"
source_key: "gh:microsoft/VibeVoice"
author: ""
---

# VibeVoice：微软开源语音模型家族，把 60 分钟长音频带进 ASR

多数开源 ASR 把长音频切成 30 秒片段逐段转写，说话人跟踪和上下文在切片处断掉。VibeVoice 的差异化就压在这一处：**单次通过处理 60 分钟连续音频**，全时段说话人跟踪、结构化输出"谁在何时说了什么"。这个能力来自 7.5 Hz 的超低帧率音频分词器——同样是转写一小时音频，别人要处理十几万个声学帧，它只要约 2.7 万个 token。

这个仓库一年的走向也值得注意：2025 年 8 月以 TTS 开源，一个月后因滥用风险撤下 TTS 代码，随后转向 ASR 主线，2026 年内连发流式识别、CPU 端推理引擎，并进入 Azure AI Foundry Labs。模型家族的现状、每条线的可用性差异，下文逐个拆。

> 核对快照：GitHub 读数与源码取自 2026-10-02（main 分支最新提交 2026-09-03）。仓库 54,606★ / 6,147 forks，MIT 许可，Python 编写。

## 模型家族现状：两条主线，五个模型

| 模型 | 形态 | Hugging Face 权重 | 状态 |
|------|------|------------------|------|
| VibeVoice-ASR-7B | 离线长音频 ASR | [microsoft/VibeVoice-ASR](https://huggingface.co/microsoft/VibeVoice-ASR) | 主力，72 万+ 下载 |
| VibeVoice-ASR-Streaming | 流式 ASR | [microsoft/VibeVoice-ASR-Streaming-7B](https://huggingface.co/microsoft/VibeVoice-ASR-Streaming-7B) | 2026-09-03 发布 |
| VibeVoice-ASR-BitNet | CPU 端 ASR | [microsoft/VibeVoice-ASR-BitNet](https://huggingface.co/microsoft/VibeVoice-ASR-BitNet) | 2026-07-23 发布 |
| VibeVoice-TTS-1.5B | 长音频多说话人 TTS | [microsoft/VibeVoice-1.5B](https://huggingface.co/microsoft/VibeVoice-1.5B) | 代码已撤，权重仍可下载 |
| VibeVoice-Realtime-0.5B | 实时流式 TTS | [microsoft/VibeVoice-Realtime-0.5B](https://huggingface.co/microsoft/VibeVoice-Realtime-0.5B) | 活跃维护 |

一眼看去是两条主线：**ASR 线在扩张**（离线、流式、边缘三个形态各有权重），**TTS 线在收缩**（完整版只剩权重，活跃开发的只剩 0.5B 的实时模型）。

## 技术底座：7.5 Hz 分词器 + Next-token Diffusion

VibeVoice 用两个连续语音分词器（Acoustic 和 Semantic）把音频压缩到 **7.5 Hz** 的帧率。这个数字是 60 分钟单次转写的算术前提：7.5 Hz × 3600 秒 = 27,000 个音频 token，装得进 64K token 的上下文窗口，还留出一半空间给模型输出转录文本。对照组是常见的 50 Hz 帧率——同样一小时就是 18 万帧，早就爆窗了，所以传统方案只能切片。

生成侧沿用 [Next-token Diffusion](https://arxiv.org/abs/2412.08635) 框架：LLM 负责理解文本上下文和对话流，diffusion head 负责生成高保真的声学细节。语言模型基座是 Qwen2.5，各模型命名里的数字对应基座尺寸：ASR-7B 用 Qwen2.5-7B，TTS-1.5B 用 Qwen2.5-1.5B，Realtime-0.5B 用 Qwen2.5-0.5B。

## VibeVoice-ASR：60 分钟怎么做到的

模型接受最长 60 分钟的连续音频输入（64K token 限制内），同时做三件事：转写（ASR）、说话人分离（diarization）、时间戳标记。输出是结构化列表，每个片段带 Start/End/Speaker/Content 四个字段（下面是官方模型卡示例的截短版）：

```json
[{"Start": 0, "End": 15.43, "Speaker": 0, "Content": "Hello everyone and welcome to the Vibe Voice podcast..."},
 {"Start": 15.43, "End": 21.05, "Speaker": 1, "Content": "Thanks so much for having me, Alex..."}]
```

长音频的工程实现是把音频切成 60 秒的段（24 kHz 下 1,440,000 个采样点），段间缓存卷积状态，所以上下文不会在切缝处丢失。显存吃紧时可以调小 `tokenizer_chunk_size`（须为 3200 的倍数）。

其他要点：

- **50+ 语言，无需指定语言**：模型自动识别，原生支持语内和语间的语码转换（code-switching），中英混杂录音不用分段处理。
- **自定义热词**：人名、术语、背景信息可以注入识别过程。三条使用路径参数各不相同，后文分别给出。
- **vLLM 推理加速**：官方提供插件，无需改 vLLM 源码。

### 官方评测怎么读

README 与技术报告（[arXiv:2601.18184](https://arxiv.org/pdf/2601.18184)）给出四个指标，分别测不同的东西：

| 数据集 | 语言 | DER | cpWER | tcpWER | WER |
|--------|------|-----|-------|--------|-----|
| MLC-Challenge | 英语 | 4.28 | 11.48 | 13.02 | 7.99 |
| MLC-Challenge（11 语言平均） | — | 3.42 | 14.81 | 15.66 | 12.07 |
| AISHELL-4 | 中文 | 6.77 | 24.99 | 25.35 | 21.40 |
| AliMeeting | 中文 | 10.92 | 29.33 | 29.51 | 27.40 |

- **DER**（说话人日志错误率）测"谁在说话"分得准不准；**WER** 测纯文字转得对不对；**cpWER** 按说话人拼接后算词错率；**tcpWER** 在 cpWER 基础上加时间约束。tcpWER 略高于 cpWER（如英语 13.02 vs 11.48）说明内容归属基本对，但时间边界有松动。
- 这些数字来自会议、对话类基准（MLC、AMI、AISHELL-4、AliMeeting），**不能直接外推**到嘈杂单声道、电话录音、歌声这类场景；README 也没有给与 Whisper 等模型在同一基准上的对比表。

## 2026 年的三条延伸

**流式识别（2026-09-03）**：[VibeVoice-ASR-Streaming](https://github.com/microsoft/VibeVoice/blob/main/docs/vibevoice-asr-streaming.md) 在音频还在到达时就开始转写，每个音频块输出一次文本，边说边出稿。技术报告见 [arXiv:2609.02812](https://arxiv.org/abs/2609.02812)。块的切分和前瞻参数写在 checkpoint 的 `preprocessor_config.json` 里，模型跑在它训练时的块长上。

**CPU 端推理（2026-07-23）**：[VibeVoice-ASR-BitNet](https://github.com/microsoft/VibeASR.cpp) 用异构量化（I8_S + I2_S）把模型从 4.62 GB 压到 1.58 GB，在 3 线程以上的 CPU 上达到实时（RTF < 1），不需要 GPU。技术报告见 [arXiv:2607.21075](https://arxiv.org/abs/2607.21075)。

**Azure AI Foundry Labs（2026-03-12）**：ASR 能力进入微软云侧的[实验平台](https://labs.ai.azure.com/innovations/vibevoice-asr/)，可以在线试用。

## 上手路径

### Transformers（集成版）

2026 年 3 月起，ASR 以 [microsoft/VibeVoice-ASR-HF](https://huggingface.co/microsoft/VibeVoice-ASR-HF) 进入 Transformers（需要 **v5.3.0 及以上**）。注意模型 ID 是 `VibeVoice-ASR-HF`，原版权重仓库 `VibeVoice-ASR` 是给仓库自带推理代码用的，两者不可混用：

```python
from transformers import AutoProcessor, VibeVoiceAsrForConditionalGeneration

model_id = "microsoft/VibeVoice-ASR-HF"
processor = AutoProcessor.from_pretrained(model_id)
model = VibeVoiceAsrForConditionalGeneration.from_pretrained(model_id, device_map="auto")

# apply_transcription_request 接受本地路径或 URL
inputs = processor.apply_transcription_request(
    audio="meeting.wav",
    prompt="About VibeVoice",   # 热词与背景信息走 prompt 参数
).to(model.device, model.dtype)

output_ids = model.generate(**inputs)
generated_ids = output_ids[:, inputs["input_ids"].shape[1]:]

# 三种返回格式：raw / parsed（结构化列表）/ transcription_only（纯文本）
transcription = processor.decode(generated_ids, return_format="parsed")[0]
for seg in transcription:
    print(seg)
```

官方模型卡给过一个热词效果实例：德语口音朗读 "VibeVoice"，无上下文时被转成 "Revevoices"，加 `prompt="About VibeVoice"` 后转写正确。批量推理传列表即可；`apply_transcription_request` 本质是 `apply_chat_template` 的便捷封装。

### 仓库自带推理（原版权重）

需要 NVIDIA PyTorch 容器（24.07–25.12 验证过）管理 CUDA 环境：

```bash
git clone https://github.com/microsoft/VibeVoice.git
cd VibeVoice
pip install -e .
apt update && apt install ffmpeg -y

# Gradio 网页 demo
python demo/vibevoice_asr_gradio_demo.py --model_path microsoft/VibeVoice-ASR --share

# 文件直接转写
python demo/vibevoice_asr_inference_from_file.py --model_path microsoft/VibeVoice-ASR --audio_files your_audio.wav
```

推理脚本支持 `--device cuda/mps/cpu/xpu/auto`（Mac 可走 MPS，此时用 float32），默认温度 0.0（贪心解码），`--max_new_tokens` 默认 32768。

### vLLM 服务化

仓库内置 vLLM 插件（pyproject 注册在 `vllm.general_plugins` 入口点），提供 OpenAI 兼容的 `/v1/chat/completions` 端点，单请求支持 60 分钟以上音频。官方推荐直接用 vLLM 镜像跑：

```bash
docker run -d --gpus all --name vibevoice-vllm \
  --ipc=host -p 8000:8000 \
  -e VIBEVOICE_FFMPEG_MAX_CONCURRENCY=64 \
  -v $(pwd):/app -w /app --entrypoint bash \
  vllm/vllm-openai:v0.14.1 \
  -c "python3 /app/vllm_plugin/scripts/start_server.py"
```

扩展吞吐有 `--tp N`（张量并行，单个模型切到多卡）和 `--dp N`（数据并行，N 个副本，启动器自动挂 nginx 做负载均衡）两种，可组合（总卡数 = dp × tp）。长音频偶发的重复循环可用自带的 `test_api_auto_recover.py` 自动恢复；这条路径下热词参数是 `--hotwords "Microsoft,VibeVoice"`。

### LoRA 微调

[finetuning-asr/](https://github.com/microsoft/VibeVoice/blob/main/finetuning-asr/README.md) 提供 LoRA 微调脚本（依赖 peft），数据是音频文件 + 同名 JSON 标签，标签里按段标注 speaker/起止时间/文本，热词和领域背景放进可选的 `customized_context` 数组。注意自带的 `toy_dataset/` 是用 VibeVoice TTS 合成的演示数据，只用于跑通流程，不能当真实训练集用。

## VibeVoice-Realtime-0.5B：实时 TTS 这条线

实时模型的定位是低延迟流式合成：文本流式输入、边收边合成，官方文档口径首块语音约 200 毫秒（README 概览写 ~300 毫秒，均硬件相关），8k 上下文窗口约支撑 10 分钟连续语音。**单说话人**，安装时加 streamingtts extra（`pip install -e .[streamingtts]`，此路径锁 transformers 4.51.3）：

```bash
python demo/vibevoice_realtime_demo.py --model_path microsoft/VibeVoice-Realtime-0.5B
python demo/realtime_model_inference_from_file.py --model_path microsoft/VibeVoice-Realtime-0.5B \
  --txt_path demo/text_examples/1p_vibevoice.txt --speaker_name Carter
```

三个容易踩的边界：

1. **英语为主**。9 种多语言 voice（德法意日韩荷波兰葡西）+ 11 种英语风格 voice 是 2025-12-16 加的实验性探索，官方明确"未充分测试，谨慎使用"，非英语输入"可能产生不可预测的结果"。
2. **不读代码和公式**。数学式、特殊符号、罕见的转义序列要先预处理掉；三个词以内的超短输入稳定性会下降；背景音乐、噪声、音效不在能力范围内。
3. **音色不可自选**。为抑制 deepfake 风险并压低首响延迟，voice prompt 以嵌入格式内置，自定义音色需要联系团队。

评测方面，官方模型卡给出 LibriSpeech test-clean（WER 2.00，说话人相似度 0.695）和 SEED test-en（WER 2.05，相似度 0.633）两表，对比对象包括 VALL-E 2、Seed-TTS、CosyVoice2 等。这两组数字是短句基准的表现，而该模型的主战场是长文本流式合成——短句分数不能说明长文本下的稳定性。

## TTS 主模型为什么只剩权重

这是开源语音社区少见的一段公开轨迹，值得单独记：2025-08-25 微软开源 VibeVoice-TTS（90 分钟、4 说话人的长音频合成），论文后被评为 **ICLR 2026 Oral**（[OpenReview](https://openreview.net/forum?id=FihSkzyxdv)，技术报告 [arXiv:2508.19205](https://arxiv.org/pdf/2508.19205)）。十一天后的 2025-09-05，官方在 README 声明"发现该工具被用于与既定意图不一致的场景"，以负责任 AI 为由**从仓库移除了 TTS 代码**。

现状是三层的：GitHub 上的 TTS 推理代码没了；Hugging Face 上的权重没删（至今 72 万+ 下载，README 模型表的 Quick Try 栏标 Disabled）；论文和 Oral 荣誉保留。TTS 的能力描述（90 分钟、4 说话人）如今只能对着权重和论文看，官方推理路径已经不在仓库里。

## 与 Whisper 的位置关系

拿 Whisper 做参照不是比高下，而是看两类架构的差异怎么落到使用上。数字口径全部注明来源：

| 维度 | VibeVoice-ASR | Whisper |
|------|--------------|---------|
| 长音频机制 | 60 分钟单次通过（60 秒分段 + 卷积状态缓存） | 30 秒窗口，长音频靠外部切片拼接 |
| 上下文保留 | 全时段说话人跟踪与语义连贯 | 切片处上下文断裂 |
| 语言数 | 50+（官方口径） | tokenizer 实测 100 个语言代码 |
| 说话人分离 | 原生输出 Speaker 标签 | 无，需外部 diarization（如 pyannote） |
| 结构化输出 | Start/End/Speaker/Content 四元组 | 有时间戳，无说话人归属 |
| 热词 | 支持（三条路径，参数各异） | 无原生支持 |
| 推理栈 | Transformers、vLLM 插件、BitNet CPU | Transformers、faster-whisper、vLLM（官方支持列表在列） |
| 生态成熟度 | 2026 年起，模型家族仍在快速演进 | 2022 年发布，下游工具链非常成熟 |

Whisper 赢在生态：语言覆盖更广、工具链（faster-whisper、whisperX 等）经过三年打磨、vLLM 官方支持列表在列。VibeVoice-ASR 赢在结构：切片不再丢失说话人和上下文，输出即结构化数据。选型的分界线是"要不要说话人归属和长上下文"——纯转写场景 Whisper 仍是省心选项；会议纪要、多人对话分析这类要"谁说了什么"的任务，VibeVoice-ASR 省掉一整条 diarization 流水线。

另一类常被放在一起的对比是阿里的 SenseVoice：其[已发布的 SenseVoiceSmall 权重](https://github.com/FunAudioLLM/SenseVoice)只覆盖中、粤、英、日、韩五种语言（研究层面的 50+ 语言口径是另一回事），但自带情感与音频事件检测标签，这是 VibeVoice-ASR 没有的能力。

## 采用建议

**适合现在就用**：

- 会议转写、播客归档这类长音频 + 多说话人场景，直接从 ASR 主模型开始；要边说边出稿上 Streaming 版。
- 部署目标没有 GPU 的，看 BitNet 版（1.58 GB、CPU 实时）。
- 想做领域适配的，LoRA 微调路径完整（数据格式、脚本、演示集齐全）。

**先等等或绕开**：

- 生产环境要认识到 README 的明确声明：模型"仅供研究与发展用途"，"不建议在未进一步测试的情况下用于商业或实际应用"。继承 Qwen2.5 基座的偏差，合成语音存在 deepfake 与虚假信息风险，分发 AI 生成音频时披露来源是官方建议的最佳实践。
- 需要多说话人 TTS 的，仓库里已经没有对应推理代码，只剩权重和论文；实时单说话人需求才对应活跃维护的 Realtime-0.5B。
- 短音频、单说话人、纯转写的轻量场景，Whisper 系工具链更省事。

仓库一年内从 TTS 起家、收缩、转 ASR、再长出流式与边缘形态——判断它的长期走向为时尚早，但 ASR 这条线在 2026 年的发布节奏（1 月开源、3 月进 Transformers 与 Azure、7 月上 CPU、9 月出流式）是实打实的投入信号。

## 资源

- 仓库：[microsoft/VibeVoice](https://github.com/microsoft/VibeVoice)（MIT）
- 项目主页：[microsoft.github.io/VibeVoice](https://microsoft.github.io/VibeVoice/)
- 在线 Playground：[aka.ms/vibevoice-asr](https://aka.ms/vibevoice-asr)
- 模型集合：[Hugging Face](https://huggingface.co/collections/microsoft/vibevoice-68a2ef24a875c44be47b034f)
- 技术报告：[ASR（arXiv:2601.18184）](https://arxiv.org/pdf/2601.18184) · [Streaming（arXiv:2609.02812）](https://arxiv.org/abs/2609.02812) · [BitNet（arXiv:2607.21075）](https://arxiv.org/abs/2607.21075) · [TTS（arXiv:2508.19205）](https://arxiv.org/pdf/2508.19205)
- ICLR 2026 Oral：[OpenReview](https://openreview.net/forum?id=FihSkzyxdv)
