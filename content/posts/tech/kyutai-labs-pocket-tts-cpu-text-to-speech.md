---
title: "kyutai-labs/pocket-tts：把 100M 参数 TTS 装进 CPU 口袋"
date: 2026-07-10T02:58:08+08:00
lastmod: 2026-09-30
slug: "kyutai-labs-pocket-tts-cpu-text-to-speech"
github_repo: "kyutai-labs/pocket-tts"
source_key: "gh:kyutai-labs/pocket-tts"
tags: ["TTS", "PyTorch", "CPU 推理", "开源模型"]
categories: ["技术笔记"]
description: "拆解 Kyutai Pocket TTS：100M 参数、纯 CPU 推理、首块延迟约 200ms 的开源 TTS。技术路线来自 Continuous Audio Language Models 论文——放弃离散音频 token，用连续 VAE 帧换低算力下的高音质。本文核对安装、CLI、Python API、HTTP 服务与声音克隆的真实用法。"
---

大多数"轻量 TTS"只做到了轻量：要么砍掉声音克隆，要么砍掉流式输出。Pocket TTS 的价值在于它把这几样通常要 GPU 才凑齐的能力——流式、零样本克隆、六种语言——同时压进了一个 100M 参数、两个 CPU 核就能跑的模型里。它来自 Kyutai（Moshi 背后的巴黎研究实验室），技术底子是他们的 CALM 论文：不做离散音频 token，直接生成连续帧。如果你正在为"本地、离线、不上云"的语音合成选型，这个项目值得读完本文再决定。

本文所有事实以 2026-09-30 的仓库 main 分支、官方文档站与 arXiv 论文为准，仓库读数（star 数等）为当日 GitHub API 快照。

## 仓库速览

| 项 | 值 |
|---|---|
| 仓库 | [kyutai-labs/pocket-tts](https://github.com/kyutai-labs/pocket-tts) |
| 一句话 | A TTS that fits in your CPU (and pocket) |
| 许可证 | MIT |
| 语言 | Python（PyTorch 2.5+，无需 GPU 版；Python 3.10–3.14） |
| 热度 | 9,694 star / 1,019 fork（2026-09-30 读数） |
| 配套 | [论文](https://arxiv.org/abs/2509.06926)、[技术报告](https://kyutai.org/blog/2026-01-13-pocket-tts)、[Demo 页](https://kyutai.org/pocket-tts)、[文档站](https://kyutai-labs.github.io/pocket-tts/)、[HF 模型卡](https://huggingface.co/kyutai/pocket-tts) |

README 自报的核心指标（也是本文反复引用的口径）：100M 参数；首块音频延迟约 200ms；MacBook Air M4 的 CPU 上约 6 倍实时；只占 2 个 CPU 核；支持无限长文本输入，不需要切片。声音克隆开箱即用。语言支持英语、法语、德语、葡萄牙语、意大利语、西班牙语六种，README 同时说明"后续可能增加更多语言"——实际上 CLI 的 `--language` 枚举里已经出现了荷兰语模型，只是尚未写进主打清单。

## 系统地图：连续帧，不是离散 token

理解这个项目的关键，是搞清它的生成方式和主流"audio LM"不同。原论文（arXiv 2509.06926《Continuous Audio Language Models》）的出发点是：常见做法把音频压成离散 codec token（如 Mimi、EnCodec 的 token 流），压缩有损，想要更高音质就得生成更多 token，算力成本随之上去了。CALM 换了一条路：

```text
文本输入
  ↓
LUTConditioner        文本条件器（源码 pocket_tts/modules/text_conditioner.py）
  ↓
StreamingTransformer  100M 参数骨干，每个时间步产出上下文向量
  ↓
SimpleMLPAdaLN        生成头：由上下文向量条件化，直接回归 audio VAE 的下一帧（连续值）
  ↓
帧序列（每帧 80ms）
  ↓
Mimi 解码器           源码 models/mimi.py，把连续帧还原成音频
  ↓
PCM 流式输出
```

论文摘要对中间两步的原话是：模型实例化一个大型 Transformer 骨干，在每个时间步产生上下文嵌入；这些序列信息再条件化一个 MLP，通过一致性建模（consistency modeling）生成 audio VAE 的下一个连续帧。因为绕开了有损的离散化，CALM 在更低算力下拿到了比离散方案更高的保真度——这就是 100M 参数敢对标大模型的底气。

生成头支持三种解码器（源码 `pocket_tts/models/flow_lm.py`），日常使用只需知道一个参数：

- **LSD**（Lagrangian Self Distillation，默认）：1 步解码即出结果，对应 CLI 的 `--sampler-decode-steps`，默认 1，调到 5 可换更高音质；
- **drifting**：单步、无条件时间的解码头，官方 2026-09 放出的 `english_drifting_26-09` 模型用的就是它；
- **OT flow matching**：最优传输条件流的 Euler 积分，默认 16 步，研究用途为主。

仓库里还有一个意味深长的文件：`modules/dummy_quantizer.py`。一个"占位量化器"恰恰说明离散量化在这条管线里是被绕开的环节，而非核心。

声音克隆的机制也顺着这条线：给一段参考音频，模型先算出这段声音对应的 KV cache（官方叫 voice state），之后的合成都在这个状态上进行。`export-voice` 命令做的就是把 voice state 存成 safetensors 文件——加载它只是读盘，几乎不花时间；而每次从原始音频现算状态要慢得多。

## 三种使用方式

### CLI：一行命令出声音

```bash
uvx pocket-tts generate
# 或装好之后：
pocket-tts generate
```

不带参数时，它用默认文本和默认音色生成 `./tts_output.wav`，并打印速度统计。常用的调整项：

```bash
pocket-tts generate \
  --text "你好，这是一段测试。" \
  --voice alba \
  --language english
```

- `--voice` 接受内置音色名（`alba`、`giovanni`、`estelle` 等 26 个，完整清单在 README），也直接接受一个 wav 文件路径、一个 safetensors 文件、`https://` 或 `hf://` 地址——传 wav 就是即时克隆。
- `--language` 选语言模型，默认 `english`。各非英语语言另有 24 层的大号变体（如 `italian_24l`），README 的说法是音质更高但更慢，文档站则标注它们"尚未蒸馏、仅作预览"。
- 质量与采样参数：`--temperature`（默认 0.3）、`--sampler-decode-steps`（默认 1）、`--eos-threshold`（默认 -4.0）等；文本传 `-` 可从 stdin 读入。

### Python 库：TTSModel 类

README 给的最小示例原样如下——注意入口是 `TTSModel` 类，先取 voice state 再生成：

```python
from pocket_tts import TTSModel
import scipy.io.wavfile

tts_model = TTSModel.load_model()
voice_state = tts_model.get_state_for_audio_prompt(
    "alba"  # 内置音色名，也可以是本地音频路径或 hf:// 地址
)
audio = tts_model.generate_audio(voice_state, "Hello world, this is a test.")
# audio 是一维 torch tensor，内容为 PCM 数据
scipy.io.wavfile.write("output.wav", tts_model.sample_rate, audio.numpy())
```

`load_model()` 和 `get_state_for_audio_prompt()` 都比较慢，官方建议把它们的结果常驻内存；多个音色可以各持一份 voice state 并存。要做快速加载，用 `export_model_state` 把 voice state 存成 safetensors，之后读取接近零开销。

### HTTP 服务：serve 命令

```bash
pocket-tts serve
```

这会起一个 FastAPI 服务，默认监听 `localhost:8000`，模型常驻内存，网页界面直接打开就能用，比每次冷启动的 CLI 快。程序化调用走 `POST /tts`，请求体是**表单字段**而非 JSON（源码 `main.py` 的端点定义如此）：

```bash
curl -X POST http://localhost:8000/tts \
  -F "text=Hello, this is a test." \
  -F "voice_url=alba" \
  --output out.wav
```

`voice_url` 可填内置音色名、`https://` 或 `hf://` 地址；要上传音频文件做克隆则用 `voice_wav` 字段（与 `voice_url` 互斥）。服务端参数里值得一提的是 `--default-voice`（替换默认音色，启动时即加载，配置错了服务直接起不来，而不是等到第一个请求才失败）和 `--quantize`（int8 量化，降内存提速度，官方称音质影响极小）。

### 浏览器与替代运行时：社区驱动

官网 [kyutai.org/pocket-tts](https://kyutai.org/pocket-tts) 可以不装任何东西直接在浏览器里试用。想自己部署到浏览器端，README 明确说**官方尚不支持**，列出的都是社区实现：Rust 移植（XN 与 Candle 两个版本）、ONNX 导出配 ONNX Runtime Web、以及 jax-js 版本。替代运行时同样活跃：MLX 后端针对 Apple Silicon，sherpa-onnx 把它带上了树莓派、Jetson 等嵌入式板子并绑定 12 种编程语言，还有单文件 C++ 运行时和 Android 端 LiteRT 图（Pixel 8a 上约 1 倍实时）。选这些意味着离开主仓库的支持范围，但也说明模型本身足够小、足够好移植。上层生态也已有雏形：README 的"Projects using Pocket TTS"列了 18 个项目，从 ComfyUI 与 Unity 插件、Home Assistant 的 Wyoming 容器、OpenAI 兼容 API 服务器，到免装 Python 的原生 macOS 应用。

## 任务流案例：一条完全本地的播客配音流水线

假设目标是把一份文稿转成固定主播音色的播客音频，全程不出本机：

1. **安装**。Linux 上注意：PyPI 默认拉的是 CUDA 版 PyTorch，torch 2.13 下大约多装 3GB 的 NVIDIA 运行库。CPU 环境应该用
   ```bash
   pip install pocket-tts --extra-index-url https://download.pytorch.org/whl/cpu
   ```
   macOS 和 Windows 的默认 wheel 本来就是 CPU 版，无此问题。
2. **定音色**。录一段清晰的主播音频，先做降噪清洁——官方特别提醒样本的音质会被一并复现——然后导出成可快速加载的格式：
   ```bash
   pocket-tts export-voice host_sample.wav host.safetensors
   ```
   只处理前 30 秒，对本用途足够。
3. **逐段合成**。Python 里加载一次模型和 `host.safetensors`，按段落循环调用 `generate_audio`，把返回的 tensor 逐段写盘。每帧 80ms、首块约 200ms 的流式特性意味着段落级边合成边播放也可行。
4. **拼接发布**。用 ffmpeg 把各段 wav 连接、补静音、贴片头，输出成片。

有一个限制要提前知道：目前不支持在文本里插入标记来控制停顿（官方列为待实现，见 issue #6），段落间的呼吸感只能靠拼接阶段的静音处理。

## 与同类项目的定位对照

原版这类对比表常在参数量上互相打架，这里只保留各方官方来源能直接证实的信息：

| 项目 | 官方口径要点 | 克隆 | 流式 |
|---|---|---|---|
| Pocket TTS | 100M 参数，2 核 CPU 约 6 倍实时（M4），6 种语言，MIT | 零样本，参考音频即用 | 音频流式，首块约 200ms |
| Kokoro-82M | 82M 参数（模型卡原话），Apache-2.0，HF 下载量千万级 | 无（固定音色库） | — |
| XTTS-v2 | 17 种语言，6 秒音频克隆；CPML 许可（限制商用） | 零样本 | — |
| MeloTTS | 官方自述"CPU real-time inference"，中英日韩法西 | 无 | — |
| CosyVoice（Fun-CosyVoice 3.0） | 0.5B 模型，9 语言 + 18 种以上中文方言，指令控制 | 零样本 | 双向流式，官方称延迟低至 150ms |
| Piper | 轻量本地 TTS；仓库已归档，停止维护 | 无 | — |

表中"—"表示该项目官方文档未以流式为卖点宣传，不代表技术上做不到。两个容易读歪的地方：其一，CosyVoice 那个 150ms 和 Pocket TTS 的 200ms 不可直接比——前者是服务端 GPU 部署的流式延迟口径，后者是笔记本 CPU 的口径，部署前提差了一个数量级的算力；其二，"流式"本身的含义也不完全对齐，Pocket TTS 是模型原生的逐帧音频流，部分项目的"流式"指分句送入管线。选型时值得按自己的部署环境重算这笔账，而不是单看某个数字。

## 性能口径与运行边界

README 的 ~200ms/6 倍实时/2 核是官方自报，测机是 MacBook Air M4。GPU 部分，README 有一段实测数据很诚实：在单核性能强的机器（如 Apple Silicon）上，因为 batch size 为 1 且模型极小，上 GPU 没有观测到加速；但在 4 vCPU 的 x86 云主机配 Tesla T4 的组合上，GPU 带来约 2.6 倍一致加速（实时率从 CPU 的约 2.3–2.5 倍提到 GPU 的约 6.28 倍）。结论：GPU 值不值得上，完全取决于你的 CPU 有多弱。

几个实操边界：

- `--device` 选项只在 `generate` 命令上提供，`serve` 和 Docker 镜像固定跑 CPU；
- int8 量化（`--quantize`）只能在 CPU 上用，挪到 CUDA 会抛 `NotImplementedError`；
- 驱动与 CUDA 版本不匹配时 `torch.cuda.is_available()` 会静默返回 `False`，只有一条 UserWarning，不报错；
- 2026 年 8 月项目发布了训练代码（`training/` 目录），社区已经用它训练出捷克语、印地语、韩语、波斯语、印尼语、爱沙尼亚语、威尔士语、波兰语八种语言的模型，通过 `--config hf://...` 直接加载。注意预置音色是随官方权重预计算的，社区模型用不了，此时 `--voice` 会回退到 alba 的原始音频文件。

## 适用边界与采用建议

**适合先上**：产品要离线/本地合成、对隐私或云成本敏感；用户侧是普通笔记本 CPU；需要欧洲主要语言加即时克隆；对话式场景吃首块延迟。

**有一条合规红线要转述给所有商用读者**：README 的 Prohibited use 一节明确禁止未经明确合法同意的声音模拟或克隆，以及用生成内容冒充真实人物的录音。声音克隆工具的这类条款不是走过场，接入产品前应该把它写进自己的用户协议。

**建议观望或绕行**：需要中文——官方六种语言不含中文，README 列出的八个社区模型里也没有中文，这个场景应看 CosyVoice 或 MeloTTS；需要 SSML 级的韵律控制、情感标签或歌声合成，100M 模型和当前接口都覆盖不了；需要停顿控制，得自己在拼接层做；生产环境要长期稳定供货，注意 Piper 归档的前车之鉴——小团队项目有维护风险，好在 MIT 许可和活跃的社区移植留了退路。

**上手路径**：先在官网 Demo 听音质是否达标，再 `uvx pocket-tts generate` 本机验证速度，然后决定是 pip 装库还是 serve 起服务；对训练定制语言模型有兴趣，直接看 `training/` 的官方配方。

## 参考

- 仓库：<https://github.com/kyutai-labs/pocket-tts>（本文口径：main 分支，2026-09-30）
- 论文：Continuous Audio Language Models，<https://arxiv.org/abs/2509.06926>
- 技术报告：<https://kyutai.org/blog/2026-01-13-pocket-tts>
- 文档站（generate / serve / export-voice 命令参考）：<https://kyutai-labs.github.io/pocket-tts/>
- HF 模型卡：<https://huggingface.co/kyutai/pocket-tts>；音色库：<https://huggingface.co/kyutai/tts-voices>
- Demo：<https://kyutai.org/pocket-tts>
- 姊妹项目 Moshi：<https://github.com/kyutai-labs/moshi>
