---
title: "VibeVoice：微软开源前沿语音 AI，从入门到精通"
date: "2026-03-30T11:35:00+08:00"
lastmod: "2026-09-14T12:00:00+08:00"
slug: "vibevoice-microsoft-open-source-voice-ai"
github_repo: "microsoft/VibeVoice"
source_key: "gh:microsoft/VibeVoice"
description: "深度解析微软 VibeVoice 开源语音 AI 模型家族：7.5 Hz 连续语音 tokenizer 与 next-token diffusion 架构，TTS 线的 90 分钟长语音与 300 ms 实时合成，ASR 线的 60 分钟长音频转写与 CPU 边缘部署，以及使用路径与合规边界。"
draft: false
categories: ["技术笔记"]
tags: ["语音AI", "微软", "开源", "TTS", "ASR"]
---

# VibeVoice：微软开源前沿语音 AI，从入门到精通

## 一句话判断

VibeVoice（[microsoft/VibeVoice](https://github.com/microsoft/VibeVoice)）不是「一个语音助手」，而是微软把语音当作序列建模问题来解的模型家族：TTS 一条线做语音合成，从 90 分钟长语音的 VibeVoice-TTS-1.5B 到首包延迟约 300 ms 的 Realtime-0.5B；ASR 一条线做语音转写，从一次吞下 60 分钟音频的 ASR-7B 到只用 CPU 的 ASR-BitNet。让它成立的共同底座是 **7.5 Hz 连续语音 tokenizer**——帧率压得足够低，90 分钟音频才能装进 64K token 的上下文窗口，长语音的生成与转写才从「切块拼接」变成「一次建模」。

这个仓库值得关注的另一个原因是它坦诚：TTS 代码在 2025 年 9 月因滥用被官方主动移除，README 明确声明模型仅供研发用途。研究一个语音开源项目绕不开「能用来做什么、不该用来做什么」，本文把这条线也讲清楚。

截至 2026 年 9 月 14 日，仓库约 54.2k stars、6.1k forks，MIT 许可证。

## 学习目标

读完这篇，你将能：

- 说清 VibeVoice 的两条产品线（TTS / ASR）和五个模型各自的定位与状态
- 理解 7.5 Hz 双 tokenizer 和 next-token diffusion 为什么让 90 分钟语音合成成为可能
- 用 Hugging Face transformers 的几行代码跑通 ASR 与实时 TTS 的推理
- 知道 TTS 代码为什么被官方移除、Realtime-0.5B 内置了哪些防滥用设计
- 按自己的场景（长内容生产、实时交互、会议转写、边缘设备）选对模型

## 目录

- [一句话判断](#一句话判断)
- [把语音当序列问题：VibeVoice 在解决什么](#把语音当序列问题vibevoice-在解决什么)
- [全景地图：一个仓库，两条产品线](#全景地图一个仓库两条产品线)
- [架构：7.5 Hz tokenizer 与 next-token diffusion](#架构75-hz-tokenizer-与-next-token-diffusion)
- [TTS 线：从 90 分钟长语音到 300 ms 实时合成](#tts-线从-90-分钟长语音到-300-ms-实时合成)
- [ASR 线：60 分钟长音频与「谁在何时说了什么」](#asr-线60-分钟长音频与谁在何时说了什么)
- [怎么跑起来：三条真实可用的路径](#怎么跑起来三条真实可用的路径)
- [benchmark 怎么读](#benchmark-怎么读)
- [合规边界：绕不开的下架史](#合规边界绕不开的下架史)
- [怎么选：按场景给建议](#怎么选按场景给建议)
- [FAQ](#faq)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [资料口径说明](#资料口径说明)
- [附录：资源与引用](#附录资源与引用)

## 把语音当序列问题：VibeVoice 在解决什么

语音 AI 的两个基本任务——合成（TTS）和转写（ASR）——长期卡在同一个约束上：**上下文太短**。

TTS 模型传统上一次只能合成十几秒到几十秒的音频。想做一期 30 分钟的播客，就得把文本切成小段分别合成，再拼起来；代价是段与段之间的音色漂移、语速断层，多说话人场景下更明显。ASR 遇到的是镜像问题：转写一小时会议录音，主流方案要先做 VAD 切块，逐段转写，说话人归属（谁说的这句）和全局时间戳很容易在切块处丢失或错乱。

VibeVoice 的思路是：把音频压缩到语言模型能「一眼看全」的长度。它自研的连续语音 tokenizer 把语音帧率压到 **7.5 Hz**（也就是每秒语音只占 7.5 个 token，官方称压缩效率比流行的 Encodec 高约 80 倍），配合 LLM 的 64K token 上下文，90 分钟音频、60 分钟音频就都在一次推理的射程之内。TTS 和 ASR 共享这个底座，只是方向相反：TTS 从文本生成语音 token，ASR 从语音 token 读出文本。

## 全景地图：一个仓库，两条产品线

| 模型 | 线 | 开源时间 | 定位 | 关键数字 | 当前状态 |
|------|-----|---------|------|---------|---------|
| VibeVoice-TTS-1.5B | TTS | 2025-08-25 | 长语音多说话人合成 | 90 分钟、4 说话人、中英等 | 代码已移除，权重仍在 HF |
| VibeVoice-Realtime-0.5B | TTS | 2025-12-03 | 实时流式合成 | 首包约 300 ms、约 10 分钟 | 可用，仅英语 |
| VibeVoice-ASR-7B | ASR | 2026-01-21 | 长音频统一转写 | 60 分钟、50+ 语言、热词 | 可用，已进 transformers |
| VibeVoice-ASR-Streaming | ASR | 2026-09-03 | 边说边转的流式转写 | 10 语言、说话人归属 | 最新发布 |
| VibeVoice-ASR-BitNet | ASR | 2026-07-23 | CPU 边缘部署 | 4.62 GB→1.58 GB、RTF<1 | 可用，配 VibeASR.cpp |

先记住这张表的读法：TTS 线解决「说」，从能说到说得久（1.5B），再到说得即时（Realtime）；ASR 线解决「听」，从听得全（7B），到听得实时（Streaming），再到听得便宜（BitNet）。下面逐个拆。

## 架构：7.5 Hz tokenizer 与 next-token diffusion

### 双 tokenizer：语音的两种「字」

VibeVoice 用两种连续语音 tokenizer 把音频编码成 LLM 可处理的向量：

- **语义 tokenizer**：保留语言内容相关的信息，回答「说了什么」；
- **声学 tokenizer**：保留音色、韵律、情感等细节，回答「听起来怎么样」。

两种 tokenizer 都工作在 7.5 Hz 的超低帧率上。帧率低直接改变了长度的量纲：1 小时音频 ≈ 27,000 个语音 token，塞进 64K 的上下文绰绰有余；如果用传统 codec 的帧率（几百 Hz），同样的音频早就爆掉了。这是「长语音一次建模」在算术上成立的前提。

### next-token diffusion：扩散头当 token 用

光有 tokenizer 还不够，语音 token 是连续值，不是离散的文字，标准 LLM 的 softmax 输出没法直接生成它们。VibeVoice 的做法是 **next-token diffusion**：LLM（TTS 模型的骨干是 Qwen2.5 1.5B）照常自回归地逐帧生成隐藏状态，但每一帧交给一个扩散头去「展开」成连续的声学向量。扩散头负责高保真的声学细节，LLM 负责文本语义与对话流的理解，两者各干各的。

这套设计直接决定了它最出名的两个能力：90 分钟长语音不断音色（每帧都在全局上下文里生成），以及多说话人对话的「氛围感」（LLM 看得到整个对话脚本，知道轮到谁、该用什么语气接话）。

### 一次 90 分钟播客的完整流转

把机制串起来看。假设你要合成一段 4 人对谈、90 分钟的播客音频：

1. 准备脚本：每句话标注说话人（`<speaker_1>` 到 `<speaker_4>`）与文本；
2. 文本被送入 LLM，模型在 7.5 Hz 帧率下逐帧自回归推进，每一帧它都「看得见」之前的全部脚本与已生成的语音帧——这保证第 89 分钟的音色和第 1 分钟一致；
3. 每一帧的隐藏状态交给扩散头，采样出连续声学向量；
4. 声学 tokenizer 的解码端把向量流还原成波形，边生成边可写出音频。

ASR 方向相反：60 分钟录音经 tokenizer 压成约 27K 帧的连续表示，LLM 一次读完全部帧，直接输出带说话人标签和时间戳的转写文本——切块、对齐、合并这些传统工序都不需要了。

## TTS 线：从 90 分钟长语音到 300 ms 实时合成

### VibeVoice-TTS-1.5B：长语音合成，以及它的下架

VibeVoice-TTS-1.5B 是 2025 年 8 月 25 日开源的第一个模型（对应技术报告 [arXiv:2508.19205](https://arxiv.org/abs/2508.19205)，被 ICLR 2026 接收为 Oral），单次合成最长 90 分钟、支持最多 4 个不同说话人，主打英语和中文，也支持跨语言合成。发布后社区热度极高，是仓库 stars 的主要来源。

但它也是这个项目争议的中心：2025 年 9 月 5 日，微软以「发现了与既定用途不一致的使用案例」为由，**把 TTS 代码从仓库移除**。目前权重仍可在 Hugging Face（`microsoft/VibeVoice-1.5B`）获取，README 中该模型的 Quick Try 入口标注为 Disabled，官方未给出恢复时间表。社区里维护着若干第三方 fork，但那已不在官方支持范围内——使用前要自己评估代码与权重的版本对应关系。

这件事对使用者的含义很直接：**长语音多说话人合成是 VibeVoice 的招牌能力，但官方当前不提供它的可用代码路径**。

### VibeVoice-Realtime-0.5B：把帧率优势换成延迟

2025 年 12 月 3 日开源的 Realtime-0.5B 走的是另一个方向：流式文本输入，增量编码文本块的同时并行做扩散生成，硬件合适时首包音频延迟约 300 ms，8K token 上下文下单次可生成约 10 分钟语音。架构上它只保留了声学 tokenizer（7.5 Hz），扩散头轻量到 4 层、约 40M 参数（DDPM + CFG + DPM-Solver 采样）。

能力边界要认清：

- **仅支持英语**。2025 年 12 月 16 日加入的德、法、意、日、韩、荷、波兰、葡萄牙、西 9 种语言声音属实验性质，官方明确说非英语输出不受支持，可能无法理解或不恰当；另有 11 种英语风格声音。
- **单说话人**。多人对话要回到 1.5B 那条线。
- **只生成语音**，不生成音乐或音效；不建模重叠说话；朗读代码、数学公式、特殊符号前需要自己预处理文本。

防滥用上它做了三件事：生成的音频自动嵌入可听的 AI 声明和隐性水印，且发布时移除了声学 tokenizer——也就是说你拿官方权重能生成语音，但没有配套的 tokenizer 就难以随意克隆他人音色。这是「开源权重」与「防滥用」之间的一种工程折衷。

## ASR 线：60 分钟长音频与「谁在何时说了什么」

### VibeVoice-ASR-7B：把转写、说话人、时间戳装进一次推理

2026 年 1 月 21 日开源的 ASR 模型（技术报告 [arXiv:2601.18184](https://arxiv.org/abs/2601.18184)）把 ASR、说话人分离（diarization）、时间戳合成一个任务：模型直接输出结构化的「谁（Speaker）、何时（Timestamps）、说了什么（Content）」。单次处理最长 60 分钟音频（64K token 内），支持 50 种以上语言，原生处理句内和跨句的语言混杂（code-switching），还支持自定义热词来保住人名、术语这类专业词的识别率。

工程侧的配套在半年内快速铺开：2026 年 3 月 6 日进入 Hugging Face Transformers 正式发布（`pip install` 最新版 transformers 即可调用），3 月 12 日集成到 Azure AI Foundry Labs；官方还提供微调代码和 vLLM 推理支持。它是这个家族里「拿来做产品」阻力最小的模型。

### Streaming 与 BitNet：听得实时，听得便宜

- **VibeVoice-ASR-Streaming**（2026-09-03，[arXiv:2609.02812](https://arxiv.org/abs/2609.02812)）：音频到达即转写，持续输出带说话人归属的内容，支持热词，覆盖 10 种语言。会议实时字幕、直播转写这类场景的答案。
- **VibeVoice-ASR-BitNet**（2026-07-23，[arXiv:2607.21075](https://arxiv.org/abs/2607.21075)）：用异构量化（I8_S + I2_S 混合精度）把模型从 4.62 GB 压到 1.58 GB，配套的 C++ 推理引擎 [VibeASR.cpp](https://github.com/microsoft/VibeASR.cpp) 在 3 条以上 CPU 线程上即可实时推理（RTF < 1），不需要 GPU。这让树莓派级别的设备和离线场景有了选项。

## 怎么跑起来：三条真实可用的路径

**路径一：Hugging Face Playground（零代码）。** ASR 有官方在线演示 [aka.ms/vibevoice-asr](https://aka.ms/vibevoice-asr)，上传或粘贴音频就能体验长音频转写，适合动手前先看看效果。

**路径二：transformers 调用（生产推荐）。** ASR 与 Realtime TTS 都已进入 transformers 正式发布，以下代码来自官方模型卡：

```python
# ASR：pipeline 高层封装
from transformers import pipeline

pipe = pipeline("automatic-speech-recognition", model="microsoft/VibeVoice-ASR")
```

```python
# 实时 TTS：直接加载模型
from transformers import VibeVoiceStreamingForConditionalGenerationInference

model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
    "microsoft/VibeVoice-Realtime-0.5B", device_map="auto"
)
```

注意两点：ASR 模型没有托管在 Hugging Face 的 Inference Provider 上，推理要跑在自己的算力上；模型卡未给出显存数字，ASR 是 7B 级模型（BF16 权重），实际部署前请按自己的硬件实测。

**路径三：仓库 Colab 笔记本（免费 GPU）。** 仓库 `demo/` 目录提供 Colab 笔记本（`VibeVoice_colab.ipynb` 与 `vibevoice_realtime_colab.ipynb`），浏览器里免费跑通合成，不想配环境就从这里开始。

顺带排除一个常见误会：**没有 `pip install vibevoice` 这个包**，README 里也没有 Docker 镜像或 `vibevoice` 命令行工具——网上流传的那类安装命令多是对旧 TTS 版本第三方 fork 的转述，与官方仓库现状不符。

## benchmark 怎么读

README 为 ASR 线提供了三组指标图：**DER**（Diarization Error Rate，说话人归属错误率）、**cpWER**（说话人分离条件下的词错误率）、**tcpWER**（面向流式转写的词错误率）。读这组数字时建议带上三个问题：

1. **测的是什么**：DER 管的是「谁在说话」分得对不对，cpWER/tcpWER 管的是「内容转得对不对」——前者差不代表后者差，反之亦然。
2. **数字反映系统的哪部分**：说话人归属主要取决于模型对全局上下文（谁在何时发言）的建模，内容错误更多取决于声学与语言学建模；两者对应架构里不同的组件。
3. **不能推出什么**：这些基准主要覆盖英文与常见语种，中文专业领域、强口音、多人大混叠场景的表现需要你在自己的数据上实测；README 未提供完整数字表格，比较时建议直接查看仓库原图并留意测试集。

TTS 线的「效果」目前没有公开的单一分数，主观听感（音色相似度、韵律自然度）仍是主要评价方式，官方展示以样例音频为主。

## 合规边界：绕不开的下架史

VibeVoice 的 README 花了整节讲风险，这不是套话，而是有真实事件背书的：TTS 代码下架就发生在开源后的第 11 天。使用这个家族的任何模型，以下边界都是官方明文：

- **仅供研究与开发用途**。官方不建议未经充分测试就把模型用于商业或实际应用。
- **深度伪造风险由使用者承担**。语音克隆与伪造的技术门槛因开源而大幅降低，官方明确提示不要用于未经同意模仿他人声音、虚假信息、实时换声等场景，并为滥用行为设置了反馈渠道（VibeVoice@microsoft.com）。
- **模型继承基座的偏差**。官方指出模型继承了 Qwen2.5 基座模型的偏见与错误。
- **Realtime-0.5B 内置了防护**（可听 AI 声明、隐性水印、移除声学 tokenizer），这些不是 bug，不要尝试绕过。

如果你在做语音产品选型，这一节应该和架构那一节同等权重地读完。

## 怎么选：按场景给建议

- **会议/播客转写（有 GPU）**：VibeVoice-ASR-7B，60 分钟一次转完，说话人和时间戳齐全；已进 transformers，接入成本最低。
- **实时字幕、直播转写**：VibeVoice-ASR-Streaming。
- **离线设备、边缘部署、隐私敏感**：VibeVoice-ASR-BitNet + VibeASR.cpp，CPU 即可实时。
- **英语实时语音交互（做 demo 或研究）**：VibeVoice-Realtime-0.5B，注意仅英语、单说话人、研究用途。
- **中文长篇多说话人内容生产（有声书、播客）**：这是 TTS-1.5B 的能力区间，但官方代码已移除——评估社区 fork 时把维护活跃度和版本对应关系算进风险，或者先等官方恢复。
- **不建议**：把任何 VibeVoice 模型直接当作未经合规评审的生产语音组件。

## FAQ

**Q1：VibeVoice 和 GPT-4o 语音模式是一回事吗？**

不是。GPT-4o 的语音模式是闭源的端到端对话服务；VibeVoice 是开源模型家族，只提供 TTS 和 ASR 两类基础模型，不含对话管理、也不绑定任何 LLM。你可以把它生成的语音接到任何对话系统里。

**Q2：TTS 代码被移除后，还能用 VibeVoice 做语音合成吗？**

权重仍在 Hugging Face（`microsoft/VibeVoice-1.5B`），Realtime-0.5B 的代码和 transformers 支持是完整的。但 1.5B 的长语音合成当前没有官方代码路径，社区 fork 需自行评估。

**Q3：中文支持怎么样？**

分模型看：TTS-1.5B 主打英语和中文；ASR 线官方口径为支持 50+ 语言，无需显式设置语言，原生处理句内和跨句的 code-switching，但 README 与论文都未公布完整语言清单，中文识别效果建议先在 [aka.ms/vibevoice-asr](https://aka.ms/vibevoice-asr) 上用你自己的素材实测；Realtime-0.5B 仅支持英语。

**Q4：跑这些模型需要什么硬件？**

官方未发布统一的显存要求表。可确认的数字：ASR-BitNet 量化后 1.58 GB、3+ CPU 线程可实时；Realtime-0.5B 官方称 0.5B 骨干「deployment-friendly」，300 ms 首包延迟取决于硬件；ASR-7B 为 BF16 权重，推理建议 GPU。部署前在自己的硬件上实测是最可靠的做法。

**Q5：遇到问题去哪反馈？**

GitHub Issues（[microsoft/VibeVoice/issues](https://github.com/microsoft/VibeVoice/issues)）；涉及滥用报告或安全问题可邮件 VibeVoice@microsoft.com。ASR 的在线体验在 [aka.ms/vibevoice-asr](https://aka.ms/vibevoice-asr)。

## 自测题

1. VibeVoice 家族包含哪五个模型？TTS 线和 ASR 线各自的演进方向是什么？
2. 7.5 Hz 帧率为什么是 90 分钟长语音合成在算术上成立的前提？算一算：一小时音频在 7.5 Hz 下大约占多少 token？
3. next-token diffusion 里 LLM 和扩散头各自负责什么？为什么不直接让 LLM 输出音频样本？
4. TTS-1.5B 的代码为什么被移除？Realtime-0.5B 用哪三重设计防滥用？
5. DER、cpWER、tcpWER 分别衡量什么？为什么 DER 低不能推出转写质量高？

<details>
<summary>参考答案</summary>

1. TTS-1.5B（长语音多说话人合成）、Realtime-0.5B（实时流式合成）、ASR-7B（60 分钟长音频转写）、ASR-Streaming（流式转写）、ASR-BitNet（CPU 边缘推理）。TTS 线从「说得久」走向「说得即时」，ASR 线从「听得全」走向「听得实时、听得便宜」。
2. 约 27,000 token（3600 秒 × 7.5）。传统 codec 数百 Hz 的帧率下同样音频远超 64K 上下文，只能切块处理。
3. LLM 负责理解文本语义与对话流、逐帧生成隐藏状态；扩散头把隐藏状态展开为连续声学向量，保住高保真细节。音频是连续值，超出 LLM 离散 softmax 输出的表达范围。
4. 2025-09-05 因「与既定用途不一致的使用案例」被官方移除。三重设计：自动嵌入可听 AI 声明、植入隐性水印、发布时移除声学 tokenizer。
5. DER 衡量说话人归属错误率，cpWER 衡量说话人分离后的词错误率，tcpWER 是面向流式转写的词错误率。归属正确与内容正确由不同组件决定，一个低不蕴含另一个低。

</details>

## 练习

**练习 1：零成本跑通实时 TTS。** 打开仓库 `demo/vibevoice_realtime_colab.ipynb`，在 Colab 的免费 GPU 上生成一段英语语音。记录：首包延迟实际是多少？换一段更长的文本后，延迟有没有变化？

**练习 2：用 transformers 做 60 分钟转写。** 找一段带多人对话的录音（播客、访谈均可），用 `pipeline("automatic-speech-recognition", model="microsoft/VibeVoice-ASR")` 转写，对照官方 Playground（aka.ms/vibevoice-asr）的输出，检查说话人标签和时间戳是否一致。加入 3 个专业领域热词，观察识别率变化。

**练习 3：CPU 边缘部署体验。** 按 [VibeASR.cpp](https://github.com/microsoft/VibeASR.cpp) 仓库说明在自己电脑的 CPU 上跑 ASR-BitNet 模型，测量实际的 RTF。验证「3+ 线程 RTF < 1」在你的机器上是否成立。

**练习 4（开放）：写一页合规评估。** 假设你要在产品中引入语音克隆，列出 VibeVoice 的使用边界中哪些条款会构成障碍，以及你需要在工程与法务侧补充哪些控制措施。

## 进阶路径

1. **读透 TTS 技术报告**：[arXiv:2508.19205](https://arxiv.org/abs/2508.19205)，重点看 tokenizer 设计与 next-token diffusion 的训练方式，对照 next-token 扩散的原始论文（arXiv:2412.08635）理解脉络。
2. **读 ASR 三部曲**：长音频转写（[arXiv:2601.18184](https://arxiv.org/abs/2601.18184)）→ 流式转写（[arXiv:2609.02812](https://arxiv.org/abs/2609.02812)）→ CPU 量化（[arXiv:2607.21075](https://arxiv.org/abs/2607.21075)），观察同一底座如何被改造成三种部署形态。
3. **上手微调**：仓库提供 ASR 微调代码，用自己的领域数据（会议、医疗、法律录音）微调热词效果，评估领域适配收益。
4. **对比研究**：把 VibeVoice 与其他开源语音方案（如 Whisper 系的 ASR、其他开源 TTS）在你的数据上做一轮实测对比，重点看长音频与多说话人场景。
5. **关注官方动态**：TTS 代码是否恢复、Realtime 是否扩展语言支持，都会改变上面的选型建议——以仓库 README 的 News 区为最新事实来源。

## 资料口径说明

1. **核实时间**：本文事实核查截至 2026-09-14，来源为 microsoft/VibeVoice 仓库 README、Hugging Face 模型卡（`microsoft/VibeVoice-ASR`、`microsoft/VibeVoice-Realtime-0.5B`）及 arXiv 论文页。stars 数（54.2k）为核实时点数据，会持续变化。
2. **本文修订说明**：早期版本将 VibeVoice 描述为「实时语音对话框架」（含 VAD/ASR/LLM/TTS 管道、Skill 系统、pip 包等），与该项目实际形态不符，本次已按官方来源全文重写。VibeVoice 是 TTS + ASR 模型家族，不包含对话编排框架。
3. **数字的边界**：显存要求、各语种实测精度等官方未给出的数字，本文不提供；README 的 benchmark 图未附完整数字表格，具体数值请查看原图。
4. **时效提示**：TTS 代码移除后官方未公布恢复计划；Streaming ASR 为 2026-09-03 最新发布，使用前请以仓库 README 为准核对模型清单与状态。

## 附录：资源与引用

**仓库与模型**

- 代码仓库：[microsoft/VibeVoice](https://github.com/microsoft/VibeVoice)（MIT）
- CPU 推理引擎：[microsoft/VibeASR.cpp](https://github.com/microsoft/VibeASR.cpp)
- Hugging Face 模型：[VibeVoice-ASR](https://huggingface.co/microsoft/VibeVoice-ASR) ｜ [VibeVoice-Realtime-0.5B](https://huggingface.co/microsoft/VibeVoice-Realtime-0.5B) ｜ [VibeVoice-1.5B](https://huggingface.co/microsoft/VibeVoice-1.5B)（TTS 权重，代码已移除）

**论文**

- VibeVoice Technical Report（TTS）：[arXiv:2508.19205](https://arxiv.org/abs/2508.19205)，ICLR 2026 Oral，[OpenReview](https://openreview.net/forum?id=FihSkzyxdv)
- VibeVoice-ASR：[arXiv:2601.18184](https://arxiv.org/abs/2601.18184)
- ASR-Streaming：[arXiv:2609.02812](https://arxiv.org/abs/2609.02812)
- ASR-BitNet：[arXiv:2607.21075](https://arxiv.org/abs/2607.21075)

**在线体验**

- ASR Playground：[aka.ms/vibevoice-asr](https://aka.ms/vibevoice-asr)
- Colab 笔记本：仓库 `demo/` 目录（`VibeVoice_colab.ipynb`、`vibevoice_realtime_colab.ipynb`）

**反馈渠道**：[GitHub Issues](https://github.com/microsoft/VibeVoice/issues) ｜ VibeVoice@microsoft.com

---

**🦞 钳岳星君｜VibeVoice 技术解析｜2026-03-30**
