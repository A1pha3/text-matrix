---
title: "VoxCPM2：放弃离散音频分词，用连续扩散合成 30 种语言的语音"
date: "2026-04-12T11:50:00+08:00"
slug: voxcpm2-tokenizer-free-tts-guide
github_repo: "OpenBMB/VoxCPM"
description: "OpenBMB 开源的 2B 参数 Tokenizer-Free TTS 模型，基于 MiniCPM-4 骨干，在超 200 万小时多语种数据上训练。支持 30 种语言、音色设计、可控声音克隆，原生输出 48kHz 音频。"
draft: false
categories: ["技术笔记"]
tags: ["TTS", "语音合成", "多语言", "扩散模型"]
---

# VoxCPM2：放弃离散音频分词，用连续扩散合成 30 种语言的语音

VoxCPM 这条线真正动的地方，是 TTS 里最经不起折腾的一环——离散分词。传统语音合成要把音频切成 token，用语言模型在 token 序列上生成，再把 token 拼回波形。VoxCPM 把这个环节整个拿掉，让模型直接在连续表征上做扩散自回归。VoxCPM2 在此基础上把 30 种语言、音色设计、声音克隆和 48kHz 输出装进了同一个 2B 模型。

文章基于官方仓库与文档事实核验（GitHub API 2026-08-06 验证），代码示例均取自官方 README 与 ReadTheDocs。

## 一、这个项目解决了什么

传统 TTS 的链路里，最麻烦的往往不是模型本身，而是中间的离散化。语音要先被编码成 token（音素、Codec 码），语言模型在 token 序列上生成，再把 token 解码回波形。切法、字典、跨语言的 token 表，每一项都牵动系统复杂度和迁移成本。多语言更是要面对不同语言的 token 字典问题。

VoxCPM 走的是另一条路：不把音频离散成 token，而是让模型直接在连续表征空间里生成。端到端的扩散自回归架构，输入文本，输出连续语音表征，再经 AudioVAE 解码成波形。tokenizer 这一层被拿掉了。

VoxCPM2 是这系列的最新大版本，OpenBMB 开源，2B 参数，基于 MiniCPM-4 骨干，在超过 200 万小时（约 236 万小时：180 万小时中英基础语料 + 56 万小时多语言）数据上训练。原生输出 48kHz 音频，并加入音色设计（Voice Design）与可控声音克隆。权重和代码均为 Apache-2.0，可商用。

核心数据（GitHub API 2026-08-06 验证）：

| 项 | 值 |
|---|---|
| Stars | 34,717 |
| Forks | 3,986 |
| 主语言 | Python |
| 协议 | Apache-2.0 |
| 默认分支 | main（创建于 2025-09，最近推送 2026-07） |

## 二、系统地图

VoxCPM 的合成是一条四阶段流水线，文本先编码，再逐级生成，最后经 AudioVAE 解码：

```mermaid
graph LR
    A[文本] --> B[Local Encoder<br/>局部编码器]
    B --> C[Text-Semantic LM<br/>文本语义语言模型]
    C --> D[Residual Acoustic LM<br/>残差声学语言模型]
    D --> E[Local DiT CFM<br/>局部扩散 Transformer]
    E --> F[AudioVAE V2<br/>16k 编码 / 48k 解码]
    F --> G[48kHz 音频]
```

四个阶段各管一段：

| 模块 | 全称 | 职责 |
|---|---|---|
| Local Encoder | 局部编码器 | 提取文本局部特征 |
| TSLM | Text-Semantic LM | 建模文本到语义的信息流 |
| RALM | Residual Acoustic LM | 在语义基础上补充声学细节 |
| Local DiT | 局部扩散 Transformer（CFM） | 在连续空间中生成声学表征 |

这里有一条主线值得记：VoxCPM 不把声音切成 token，而是把"语义"和"声学"分两层写进连续表征，再用扩散把声学细节补满。tokenizer 去掉之后，剩下的工作量集中在"连续表征里怎么塞进更多信息"。

## 三、去 tokenizer 到底去掉了什么

| 维度 | 传统 TTS（如 VALL-E 一类） | VoxCPM |
|---|---|---|
| 文本处理 | 音素/Codec tokenizer | 局部编码器，直接建模文本 |
| 音频生成 | 在离散 token 上自回归 | 在连续表征上扩散自回归 |
| 多语言 | 常需按语言维护 token 字典 | 30 种语言统一建模 |
| 可控性 | 依赖额外模块 | 文本内括号指令控制音色/风格 |

去掉 tokenizer 换来的是部署和迁移的简化，但代价是生成难度上移：连续空间的建模比离散类别更难稳定。VoxCPM 用扩散来兜住这部分不确定性，同时 AudioVAE 负责把连续表征可靠地还原成波形。

## 四、VoxCPM2 的核心改动

保留四阶段流水线之外，VoxCPM2 相比 1.x 改了三处信息流，目的都是减少信息在传递中被打折。

**Residual LM 融合：加法改为拼接 + 投影。** 1.x 把基础 LM 输出和局部编码特征相加。VoxCPM2 改为先拼接、再过一层线性投影，让残差 LM 自己学怎么融合语义与声学，不再受逐元素加法约束。

**DiT 条件化：单 token 改为多 token 前缀。** 1.x 把 LM 隐状态和残差 LM 隐状态求和成单一条件向量，作为单个前缀 token 喂给 DiT。VoxCPM2 把它们分别投影后拼接成多个前缀 token，让 DiT 的注意力能分别看语义层和声学层，避免早期融合导致信息坍缩。

**参考音频：prompt 续写改为隔离参考通道。** 1.x 克隆靠把 prompt 音频拼进生成序列。VoxCPM2 引入专用特殊 token 隔离参考音频，把"音色参考"和"续写上下文"解耦，支持四种模式——无参考的 zero-shot、带 prompt 的续写、只用参考片段的隔离克隆、以及参考定音色 + prompt 提供上下文的组合模式。

**AudioVAE V2：非对称编解码。** 编码端在 16kHz 运行（下采样 640 倍，LM token 速率保持 6.25Hz），解码端直接上采样到 48kHz。因为加入了采样率条件化，同一模型可以按不同目标采样率解码，无需外部上采样器。

## 五、可控生成：音色、风格、三档克隆

VoxCPM2 的可控能力都写在 `generate()` 的调用方式里，控制指令放在目标文本开头的括号内。

**音色设计（Voice Design）。** 不需要任何参考音频，用自然语言描述凭空造一把声音。描述放括号里，越具体越好：

```python
from voxcpm import VoxCPM
import soundfile as sf

model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False)
wav = model.generate(
    text="(年轻女性，温柔甜美)你好，欢迎使用 VoxCPM2！",
    cfg_value=2.0,
    inference_timesteps=10,
)
sf.write("voice_design.wav", wav, model.tts_model.sample_rate)
```

**可控声音克隆。** 传参考音频克隆音色，再叠加括号里的指令控制怎么说话——参考音频决定谁在说，括号决定怎么说：

```python
wav = model.generate(
    text="(稍快一点，欢快的语气)这是带风格控制的克隆语音。",
    reference_wav_path="path/to/voice.wav",
    cfg_value=2.0,
    inference_timesteps=10,
)
```

**极致克隆。** 同时提供参考音频和精确转录，让模型接着参考音频续写，保留更多声音细节。为拿到最高相似度，可以把同一段音频同时传给 `reference_wav_path` 和 `prompt_wav_path`：

```python
wav = model.generate(
    text="这是使用 VoxCPM2 的极致克隆演示。",
    prompt_wav_path="path/to/voice.wav",
    prompt_text="参考音频的文本转录。",
    reference_wav_path="path/to/voice.wav",  # 可选，提升相似度
)
sf.write("hifi_clone.wav", wav, model.tts_model.sample_rate)
```

`generate()` 的主要参数：

| 参数 | 默认值 | 说明 |
|---|---|---|
| `text` | 必填 | 待合成文本，30 种语言之一 |
| `reference_wav_path` | `None` | 克隆用参考音频，模型提取音色，无需转写 |
| `prompt_wav_path` | `None` | 续写式克隆的 prompt 音频，须与 `prompt_text` 配对 |
| `prompt_text` | `None` | `prompt_wav_path` 的逐字转写 |
| `cfg_value` | `2.0` | 引导强度，越高越贴条件，常用 1.0–3.0 |
| `inference_timesteps` | `10` | 扩散步数，越多细节越好、越慢，建议 4–30 |
| `normalize` | `False` | 文本规范化，展开数字、日期等 |
| `denoise` | `False` | 生成前对参考音频降噪 |
| `retry_badcase` | `True` | 生成明显偏短/偏长时自动重试 |

## 六、一次任务怎么流过系统

拿最常用的场景举例：给一段英文文本配一个固定音色的声音，并让它带一点欢快语气。

首先 `VoxCPM.from_pretrained("openbmb/VoxCPM2")` 加载模型，权重和配置从 Hugging Face 或 ModelScope 拉取。合成时，`reference_wav_path` 指向一段 5–30 秒的干净参考音频，模型据此提取音色；括号里的中文指令控制风格。文本进入 Local Encoder 提取局部特征，TSLM 生成语义信息流，RALM 补充声学细节，Local DiT（CFM）在连续空间里分布扩散采样，最后 AudioVAE V2 把 16kHz 编码的连续表征解码成 48kHz 波形。`generate()` 返回的 `wav` 用 `model.tts_model.sample_rate` 作为采样率写入文件。

```python
wav = model.generate(
    text="(稍快一点，欢快的语气)Hello, welcome to VoxCPM2!",
    reference_wav_path="speaker.wav",
    cfg_value=2.0,
    inference_timesteps=10,
)
sf.write("out.wav", wav, model.tts_model.sample_rate)
```

如果不传参考音频，模型每次会随机一种声音，音色在不同调用间不稳定——需要固定音色就必须复用同一段参考音频，或者走 LoRA 微调。

## 七、性能与 benchmark 解读

官方给出的速度指标是实时系数（RTF，Real-Time Factor）：

| 运行方式 | RTF（RTX 4090） |
|---|---|
| 标准 PyTorch 实现 | ~0.30 |
| Nano-vLLM / vLLM-Omni 加速 | ~0.13 |
| llama.cpp-omni（Apple M4 Pro / Metal，Q8_0） | ~1.76 |

先看这些数字在测什么。RTF 是"生成 1 秒音频所需的计算时间"，小于 1 意味着比实时快。标准实现 ~0.30 表示能实时合成，~0.13 表示加速后更富余。llama.cpp-omni 那行是端侧 GGUF 量化权重在 Apple M4 Pro 上的结果，~1.76 说明在那种硬件上并非实时，属于边跑边等。

从这些数字不能直接推出：实际业务的端到端延迟、跨语种和长文本下的稳定性，或者"任何 GPU 都有这个速度"。RTF 只反映单机推理吞吐，不涵盖模型加载、参考音频处理和服务端排队。要判断合不合适，最好的办法是在自己的硬件和文本长度上跑一遍，而不是照搬官方数字。

## 八、怎么跑起来

**安装。** 模型和代码都在 `voxcpm` 这个包，环境要求 Python ≥ 3.10（<3.13）、PyTorch ≥ 2.5.0、CUDA ≥ 12.0：

```bash
pip install voxcpm
```

国内网络可以先从 ModelScope 下载权重到本地，再加载本地路径。

**CLI。** `voxcpm` 命令覆盖三种模式，适合脚本化：

```bash
voxcpm design --text "VoxCPM2 带来全新语音合成体验。" --output out.wav
voxcpm clone --text "这是一个声音克隆的演示。" --reference-audio voice.wav --output out.wav
voxcpm batch --input examples/input.txt --output-dir outs
```

**Web Demo。** 一条命令起 Gradio 界面：

```bash
python app.py --port 8808 --device auto
```

`--device` 支持 `auto`、`cpu`、`mps`、`cuda`、`cuda:N`。Apple Silicon 上 `auto` 会在可用时用 MPS。

**生产部署。** 高吞吐走 Nano-vLLM-VoxCPM 或 vLLM-Omni。后者是官方 vLLM 的全模态扩展，原生支持 VoxCPM2，提供 PagedAttention 和 OpenAI 兼容接口：

```bash
vllm serve openbmb/VoxCPM2 --omni --port 8000
curl http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"model":"openbmb/VoxCPM2","input":"你好，欢迎使用 VoxCPM2！","voice":"default"}' \
  --output out.wav
```

**端侧推理。** 需要无 Python 的消费级部署时，用 llama.cpp-omni 跑 GGUF 权重（CPU / Metal / CUDA / Vulkan）。从 Hugging Face 或 ModelScope 下载一个 BaseLM（F16 或 Q8_0）加一个 Acoustic 文件，Q8_0 体积减半、质量损失可忽略。

## 九、微调

需要稳定复现某个声音或适配特定领域时，官方提供 LoRA 和全量微调两条路，共用同一套训练脚本 `scripts/train_voxcpm_finetune.py` 和 JSONL 数据格式。

| 目标 | 数据量 | 做法 |
|---|---|---|
| 克隆单个说话人 | 5–50 条片段 | LoRA（r=32） |
| 适配领域/风格 | 50–500 条片段 | LoRA（r=64） |
| 新增语言 | 500+ 小时 | 全量微调，混入部分中英数据 |

LoRA 冻结基座，只训练少量附加参数，显存需求远低于全量。官方内部单说话人克隆基准里，LoRA（r=32）的说话人相似度约为全量微调的 98%，显存约减半。多数任务从 LoRA 起步即可。VoxCPM2 做 LoRA 训练约需 20GB 显存，全量约 40GB（batch_size=16、max_batch_tokens=8192 下的估算）。

微调数据是 JSONL，每行一条：`{"audio": "path/audio.wav", "text": "该音频的转写"}`。预处理有几个要点：去掉尾部静音、音量归一化、转写必须与音频逐字一致、剔除噪声样本。尾静音过长是微调后"生成停不下来"最常见的原因。

微调后推理有两种方式：命令行用 `scripts/test_voxcpm_lora_infer.py`，或 Python 里加载时传 `lora_weights_path`。LoRA 权重支持运行时热切换，`load_lora`、`unload_lora`、`set_lora_enabled` 都能在不停模型的情况下完成。

## 十、该不该用

VoxCPM2 适合的场景：需要多语言同时覆盖、需要把声音控制（音色、风格、克隆）做进同一个模型、或者想绕开离散 tokenizer 那套工程复杂度，直接用命令行或 API 出 48kHz 音频的场景。

可以先用命令行或 Web Demo 验证音质和音色，再决定是否接入。生产级固定音色建议直接上 LoRA 微调，而不是依赖随机音色或反复传参考音频。想省 GPU 显存、追求高并发，优先看 Nano-vLLM / vLLM-Omni；要边缘端无 Python 部署，再看 llama.cpp-omni。

需要注意的边界：模型在极长文本、情绪或语气变化较大的输入下仍可能偶发不稳定，官方建议把长文切成短段再拼接。零样本声音克隆能力可以被用来伪造语音，官方明确要求公开分享的生成内容标注为 AI 生成，并禁止用于冒充、欺诈或传播虚假信息。另外，30 种语言统一建模，不代表每种语言效果都一样——非中英语言的效果会受训练数据覆盖影响，正式使用前值得在目标语言上实测。

**文档信息**

- 难度：⭐⭐⭐
- 类型：技术解读
- 更新日期：2026-04-12（事实核验 2026-08-06）
- 前置知识：Python 基础、TTS 概念、深度学习基础