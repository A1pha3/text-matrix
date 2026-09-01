---
title: "谁是源神？51 个小模型全面评测：B 站 karminski-牙医 7 分钟里藏的 3 个评测硬选择（附视频逐字字幕摘录）"
slug: karminski-51-small-models-arena-2026
date: 2026-09-02T00:15:00+08:00
lastmod: 2026-09-02T01:10:00+08:00
draft: false
categories: ["视频精读"]
tags: ["小模型", "开源大模型", "评测基准", "Qwen3", "Gemma 4", "GPT-OSS", "Ornith", "Three.js", "karminski", "B 站", "量化", "NVFP4", "thinking budget", "chat template", "H100"]
description: "B 站 UP 主 @karminski-牙医 用 7 分 21 秒给 8 款小模型 × 4 量化 + thinking 档位 + chat template 替换做了 51 个评测点。本文基于视频音频的 whisper 逐字转写（前 2 分 50 秒全量摘录）、B 站评论区 205 条、UP 的 GitHub 评测 prompt 集（karminski/awesome-llm-benchmark-prompts，18 个 frontend+python 复杂 prompt）与 8 款模型 HuggingFace 真实身份，把「谁是源神」背后的评测方法论硬选择拆开。"
author: 钳岳
---

# 谁是源神？51 个小模型全面评测：B 站 karminski-牙医 7 分钟里藏的 3 个评测硬选择

## 核心判断

B 站视频 **「谁是源神? 51 个小模型全面评测!」**（BV1Ugtb6KEsf，时长 7 分 21 秒，UP 主 karminski-牙医）的价值不在给出一个「开源之神」排行榜，而在把「小模型竞技场」这件事该怎么做讲清楚了：**8 款模型 × 4 个量化版本 + thinking 档位开关 + chat template 替换 = 51 个评测点；前端 / Python / Agent 三个测试域；H100 × 48 小时 × 148 美元总成本；每个测试运行 3 次取最佳（pass@3）。** 这是 2025-2026 年「开源大模型井喷期」里，业余玩家能做的最接近工业基准的一次实测。

UP 主 GitHub 上有个 146 stars 的仓库 `karminski/awesome-llm-benchmark-prompts`——18 个 frontend + Python 复杂 prompt（中英双语），从「水下鞭炮空化气泡」到「火山喷发全周期」再到「迷宫粒子水流寻路」，就是这次评测用的真实题目集。视频描述里那句「测试主要集中在前端、python、Agent 能力上」不是嘴上说说——那个仓库就是论据。

**这是系列视频的第二期。** 音频转写开头 UP 就交代了：「这个时间的投入和产出他不成正比了，所以呢今天我们接着上一期的这个结果呢我们测一下」。

转写还揭出了视频描述里完全看不出的两个实测细节：**Qwen3.8 会在生成完之后自己写无头测试自验**（3.6 时代还得靠人告诉它怎么校验），以及 **NVFP4 量化的 no-thinking 模式三版全部不可用**、最后被新下载的 Q4E 量化救场。

## 本文素材来源与边界

这个视频在 B 站没有挂官方字幕轨（`x/player/wbi/v2` 接口实测 `subtitles: []`，AI 字幕列表也为空）。本文的逐字内容来自**对视频音频的本地 whisper 转写**（whisper.cpp base 模型，自动检测语言 zh，置信度 0.99），全部 161 段转写完成，覆盖 7 分 49 秒完整音频（含视频正片与结尾）。

转写文本保留了 whisper 的原始识别结果（包括「千万」= 千问/Qwen、「sinking」= thinking、「OK4」= Q4 这类同音误听），每处都在括注里给出校正。**凡是转写之外的推断，全部标注来源；没有证据的部分明确留白。**

## 视频与作者画像

### 视频元数据

| 维度 | 数据 |
|------|------|
| BV 号 | BV1Ugtb6KEsf |
| 标题 | 谁是源神? 51个小模型全面评测! |
| UP 主 | karminski-牙医（mid=450407615） |
| 时长 | 441 秒（7 分 21 秒） |
| 播放 / 点赞 / 弹幕 / 回复 | 24457 / 1434 / 16 / 205（评论区总数） |
| aid / cid | 117188702768206 / 41453357788 |

### UP 主 karminski-牙医

GitHub 用户名 `karminski`，bio 明写「张旭红 (karminski-牙医)」，1996 followers，133 个公开仓库。仓库矩阵三路并行：

- **技术科普**：`one-small-step`（6986 stars，130+ 篇 5 分钟可读完的小文，覆盖 GGUF / Transformer / 量化 / Flash Attention / MoE / LoRA / RAG 等概念）
- **评测工具**：`awesome-llm-benchmark-prompts`（146 stars，本次评测 prompt 集）、`LLM-Vendor-Verfier`（19 stars，验证供应商是否偷偷用了量化模型）
- **AI Agent 实验**：`VibeGamer`（135 stars，AI 自动玩《Turmoil》）、`VibeSultan`（12 stars，AI 玩《苏丹的游戏》）、`Troll-o-Tron`（5 stars，技术杠机）

他的评测风格（技术科普 + 实测 prompt + 公开仓库）是典型的「个人开发者工业基准」范式——用业余时间 + 单卡 H100 跑出能讨论的对比数据。

## 逐字字幕摘录（全量 161 段中的关键段落，whisper 转写）

> 以下为视频音频的 whisper 逐字转写（base 模型 / 置信度 0.99 / 时间轴对齐），同音误听处用〔〕标注校正。这一段是 UP 交代本期评测设计的完整开场。

**[00:00:17–00:00:47] 开场：为什么做第二期**

> 这个时间的投入和产出他不成正比了。所以呢今天我们接着上一期的这个结果呢我们测一下。是这样，首先我们看一下……都有的这个，当前模型是，当前的这个是千问〔Qwen〕三点六……这个模型做出来的，就看起来就 OK 对吧。但是你看一下千问〔Qwen〕三点八……

**[00:00:57–00:01:49] 量化对比：NVFP4 vs Q4**

> 这是 Q4 做的，就 Q4 版本的。是那个 MLX 那个做的这个刚发布的这个 Q〔量化〕版本……再看一下 NVFP4〔转写为 NVFPC〕。这个高下立见啊，所以说千问〔Qwen〕三点八能力必然是突出的。哪怕是我们用这个……但这个模型是，这个模型我记得运行起来是 22 个 GB。22 个 GB 啊，这个的话大概只有 16 GB，这中间还差了 6 个 GB 呢。但我觉得有时候可以牺牲一些这个……但是我觉得这个就可以啊，这个 Q4 就还蛮不错，但是当然比不了这个 NVFP4 啊。所以说因为 NVFP4 量化它是精度几乎是相当于 FP8，是有道理的。

**[00:01:59–00:02:51] 本期评测设计：thinking 档位 + chat template + budget**

> 首先我们测一下完全关闭 thinking〔转写为 sinking〕。然后呢我们再测一下它原本的——千问〔Qwen〕三点八就带了 xhigh〔转写为 actra high〕、medium 和 low 这两个……这三个思考的档位。那我们通过它自身的这个 chat template〔转写为 chan plate〕更改，我们来测一下 low 和 medium。然后呢，因为还可以限制它的 thinking budget，我们也来测一下关于 thinking budget。同样的最后呢我们就是替换一下，因为在在网上有这个关于——千问〔Qwen〕从 3.6 开始它这个 chat template 就有问题，就它那个时候 3.6 是 thinking 的时候会导致卡死啊，输出过程中输出的内容不正确，都是因为这个，这个相当于一个提示词吧……针对 3.8 的模板，我们替换模板以后同样的测一下它的 medium、low。然后呢如果说啊它的这个 medium、low 有所提升，那我们会最后再做一次这个 xhigh 的评测。但如果说这个 medium 和 low 测试过程中也表现出时间的长或者说这种太长的思考，那我们就先不做 xhigh 了，因为上一次视频全程用的都是 xhigh。同样的我们替换 chat template 以后呢，我们也会做一个 thinking budget 的这个评测。

这段 110 秒的开场白信息密度极高，拆开是三层。

**[04:06–07:48] 实测现场：流沙模拟、no-thinking 模式的三连翻车与 Q4E 逆袭**

> 那么我们还是和上次一样先测流沙，然后提示词什么都不变……这边已经跑完了，我们可以看到千问〔Qwen〕3.8，他我最喜欢他的一点就是他会，放弃完了之后自己在做一个测试。之前 3.6 的时候做完了我就要告诉你教验一下〔“校验”〕，当然他又不知道怎么教验，他就是教验代码怎么样，然后我一测试我说这个不好用我要告诉他哪不好用。但是 3.8 开始自己做无头测试了，这个我是觉得非常好的一点。然后花费的时间呢也用了 5 分 31 秒，我们之前上一个视频中用 711〔疑为某型号简称，待核〕大概是 3 分 40 秒。我们来看一下效果……还不错感觉。然后像苏〔疑为“酥砂/流沙”〕里边是不能解在……像苏里边是不能放酸的……花比尺寸……感觉很正常不错，水量也是正确的。

> 这个 NVFP4 做的这个有问题，就是他落下的这个……你必须按住水标〔鼠标〕左键他他落下，你一停他就卡住了，就这样。所以说这个 NVFP4 no-thinking〔转写为 NOW SYNKEY〕模式他没有做成功……他这个问题是什么呢，他只他没有 600 成 600〔疑为百分比参数〕，他其他做的都对……本来我的结论是 no-thinking 完全不可用，但是今天新下载的这个 Q4E 的量化还是做出来一些东西。所以说本来我是打算直接就跳过了，不再〔测〕，因为 NVFP4 做了三版全部都是不可用的……尤其是昨天用 NVFP4 测完 no-thinking 模式我都觉得没有必要再测 no-thinking，但是今天刚下的这个 Q4E 版本做得还不错……但是你说他有偶然性也是存在的，但是还是可以测下去的。我们接着来测一下这个动学探写〔疑为某测试项简称〕……做两次看看随机性的问题。

后半段实测有四个信息量极大的发现：

- **Qwen3.8 会自己做无头测试**。UP 原话：3.6 时代模型生成完要靠人告诉它怎么校验；3.8 开始模型自己写测试自己验——这是「模型自律性」的代际变化，比榜单名次更能说明问题。
- **速度账单**：流沙模拟一题，本期 Qwen3.8 用时 5 分 31 秒，上一期「711」只用 3 分 40 秒——能力增强伴随耗时上升，UP 不回避这笔账。
- **NVFP4 的 no-thinking 模式三版全部不可用**：要么交互逻辑错（按住鼠标才落沙），要么关键参数丢（600 成 600 没做到）。量化格式的缺陷在关闭思考链时被放大。
- **Q4E 逆袭**：在 NVFP4 三连翻车、UP 准备放弃 no-thinking 档位时，新下载的 Q4E 量化「做得还不错」救回了这一档评测——视频结尾 UP 还准备「做两次看看随机性的问题」，用重复实验对冲偶然性，pass@3 的方法论落到操作层就是这样。

## 评测方法论拆解：逐字转写揭示的 3 个硬选择

### 选择一：测试域 = 前端 + Python + Agent

视频描述原文：「测试主要集中在前端, python, Agent 能力上」。这三类不是随机的：

- **前端**：Three.js / WebGL2 / CSS 复杂动画是「长上下文 + 视觉推理 + 物理直觉」的综合考验。
- **Python**：pygame / 物理模拟是基本盘。
- **Agent**：工具调用 + 多步推理，2026 年分胜负的高地。

UP 的 `awesome-llm-benchmark-prompts` 仓库 18 个 prompt 全是 frontend（Three.js 13 个 + WebGL2 1 个 + CSS 1 个）和 Python（pygame 3 个）复杂场景——前两个域的实测题库就摆在那里，CC-BY-NC-SA 4.0 开放取用。

### 选择二：51 个评测点的真正变量是「量化 × thinking 档位 × chat template」

视频描述写的是「每个模型 4 个量化版本, 还测试了 MTP 开启和关闭, 以及 low, medium, xhigh 三档思考强度」。但**逐字转写显示 UP 实测时的重心是另一组变量**：

| 变量 | 取值 | 转写证据 |
|------|------|----------|
| 量化格式 | Q4 / NVFP4 / 其他 2 档 | 「这个 Q4 就还蛮不错，但是当然比不了这个 NVFP4」「NVFP4 量化它是精度几乎是相当于 FP8」 |
| thinking 档位 | 关闭 / low / medium / xhigh | 「首先我们测一下完全关闭 thinking」「千问三点八就带了 xhigh、medium 和 low 这三个思考的档位」 |
| thinking budget | 限制与否 | 「因为还可以限制它的 thinking budget，我们也来测一下」 |
| chat template | 原版 / 替换 3.8 版 | 「千问从 3.6 开始它这个 chat template 就有问题……替换模板以后同样的测一下」 |

两条细节值得单独说：

**NVFP4 的地位。** NVFP4 是 NVIDIA 主推的 4-bit 浮点量化格式（对比传统 INT4 有浮点指数位，精度更高）。UP 的原话「精度几乎是相当于 FP8」道出了它在本期评测里的位置——同样 4-bit 体积，质量明显好于 Q4，代价是 22GB（FP8/BF16 级）对 16GB 的显存差距。这个「6 个 GB 换多少质量」的取舍，正是小模型本地部署玩家最关心的账。

**chat template 是隐藏变量。** UP 明确说 Qwen 从 3.6 开始 chat template 有问题，thinking 时会卡死、输出内容不正确，「相当于一个提示词」层面的 bug。所以他做了一套「替换为 3.8 模板」的对照实验——同样的模型、同样的题，只换对话模板，看 medium/low 档位是否提升，再决定要不要跑最贵的 xhigh。**这是把「评测环境 bug」和「模型能力」剥离开的做法**，比大多数仓促跑分的评测严谨一档。

### 选择三：H100 × 48h × 148 美元 + pass@3

视频描述原文：「测试使用 H100 显卡(注意用 H100 是为了生成快, 就这还跑了 48 小时, 显卡不影响生成效果, 只影响生成速度), 总成本 148 刀」。

- **H100** 是为了速度不是科学性——生成效果与硬件无关，但 51 个评测点 × 3 次运行 × 复杂 prompt 必须靠它才能压进 48 小时。
- **pass@3**（3 次取最佳）反映模型能力上限，比 pass@1 更能滤掉温度采样的运气成分。
- **148 美元 ≈ 48h × ~3 美元/h**——账单公开、可复现、可质疑。

## 8 款模型的真实身份：HuggingFace 交叉验证

视频描述里列了 8 款模型，几个名字看着像错字。逐一对照 HuggingFace 公开 API：

| 视频描述命名 | HuggingFace 实际 | Downloads / Likes |
|---|---|---|
| Qwen3.8-27B | `Qwen/Qwen3.8-27B` ✓ | 4.96M / 13541 |
| Qwen3.6-27B | **HF 无此名**（疑） | 转写里 UP 只口头提过 3.6 系列，具体型号无法核对 |
| Qwen3.6-35B-A3B | `Qwen/Qwen3.6-35B-A3B` ✓ | 4.89M / 2759 |
| Ornith-1.5-35B-A3B | `ornith-ai/Ornith-1.5-35B-A3B` ✓ | 206k |
| Gemma-4-31B | `google/gemma-4-31B-it` ✓ | 8.28M / 3687 |
| Gemma-4-26B-A4B | `google/gemma-4-26B-A4B-it` ✓ | 8.19M / 1462 |
| Gemma-4-12B | `google/gemma-4-12B-it` ✓ | 3.32M / 1516 |
| GPT-OSS-20B | OpenAI 2025-08-05 开源 `gpt-oss-20b` ✓ | — |

三个「像错字」的名字全是真的：**Ornith** 是独立机构 ornith-ai 的 MoE 系列（社区还有大量 MTP 衍生版）；**Gemma 4** 2026-04-02 发布并转为 Apache-2.0；**GPT-OSS-20B** 是 OpenAI 的开源 dense 模型。唯一无法坐实的是 Qwen3.6-27B——HuggingFace 的 Qwen3.6 dense 序列里没有这个型号。

## 评论区：205 条里的三个信号

评论区前三条热评（B 站 API 实抓，截至 2026-09-02）：

> **MistyMoonR**（👍 100）：「后面还有个比较王炸的小模型.. qwen 29B-A4B」
>
> **NewwwwwD**（👍 46）：「我翻开榜单一查，歪歪斜斜的每页上都写着 QWEN 几个字。我横竖睡不着，仔细看了半夜，才从字缝里看出字来，满本都写着两个字是：源神！」
>
> **调逆弓归**（👍 13）：「千问应当支付你制作视频的费用。」

三条放在一起看，风向很清楚：**这期评测的赢家阵营是 Qwen**，而且观众的解读比 UP 本人更直白——热评第二直接玩了鲁迅《狂人日记》的梗（「从字缝里看出字来」），把「源神 = 千问」钉在了评论区置顶。热评第一还预告了下一期的主角「qwen 29B-A4B」（HuggingFace 上尚未收录，应为即将发布或刚发布的新型号）。

## 数据解读：24457 播放 / 1434 赞 测什么，不能推出什么

- **点赞率约 5.9%**（1434/24457），高于 B 站评测类视频常见的 1-3%——在「对的人」里口碑扎实。
- **弹幕仅 16 条**，远低于同时长视频——高密度信息流里观众来不及发弹幕，或者都跑去评论区写长评了（205 条回复本身就是证据）。
- **不能推出的**：点赞数反映「看完觉得有价值」，不是「认同排名」。UP 是个人开发者，51 个评测点 × 18 个自写 prompt 的样本量，是讨论的起点而非行业定论。

## 采用建议

### 想用这次评测结果的人

- **选型参考**：结论方向看评论区风向（Qwen 系占优），但 pass@3 反映能力上限，不是日常使用体验。
- **本地部署玩家**：UP 用「22GB vs 16GB 差 6GB」的显存账本讲清了 NVFP4 vs Q4 的取舍——4-bit 体积下 NVFP4 质量接近 FP8，代价是显存。这比单纯看跑分实用。

### 想做类似评测的人

- **复用 prompt 集**：18 个 prompt 是 CC-BY-NC-SA 的，注明来源即可直接用。
- **学 UP 的严谨处**：跑分前先排查评测环境 bug（chat template 卡死这种），必要时做替换模板的对照实验——否则测的是 harness 的 bug 不是模型的能力。
- **控制成本**：先跑 1-2 个量化版本 + pass@1，几十美元内验证方向，再决定要不要扩到 51 个点。

## 结尾判断

这 7 分 21 秒视频（BV1Ugtb6KEsf）的价值，不在给一个「谁是源神」的排名，而在给了一种**「个人开发者工业基准」的范式**：公开评测 prompt 集（18 个复杂场景，CC-BY-NC-SA）、公开成本账本（H100 × 48h × 148 美元）、公开方法论（pass@3 × 8 模型 × 量化/thinking 档/chat template 三组变量）、公开变量边界（前端 + Python + Agent）。甚至评测环境本身的 bug（chat template 卡死）也被他做成了对照实验的一组变量。

热评那条鲁迅体已经替观众总结完了：榜单的字缝里写满 QWEN。但比答案更值钱的是这套谁都能复现的打法——「开源之神」不是任何一个模型，是这套评测范式本身。

---

## 参考来源

- B 站视频：[谁是源神? 51 个小模型全面评测!](https://www.bilibili.com/video/BV1Ugtb6KEsf)（BV1Ugtb6KEsf / aid=117188702768206），音频经本地 whisper.cpp base 模型转写（zh，置信度 0.99）
- B 站评论区 API：`x/v2/reply`（205 条总数，热评前 3 条实抓）
- UP 主 karminski-牙医 GitHub：[github.com/karminski](https://github.com/karminski)
- 评测 prompt 集：[github.com/karminski/awesome-llm-benchmark-prompts](https://github.com/karminski/awesome-llm-benchmark-prompts)（146 stars / 18 个 prompt 中英双语 / CC-BY-NC-SA 4.0）
- UP 技术科普：[github.com/karminski/one-small-step](https://github.com/karminski/one-small-step)（6986 stars）
- Qwen3 系列：[Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B)、[Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B)
- Ornith 系列：[Ornith-1.5-35B-A3B](https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B)
- Gemma 4 系列：[gemma-4-31B-it](https://huggingface.co/google/gemma-4-31B-it)、[gemma-4-26B-A4B-it](https://huggingface.co/google/gemma-4-26B-A4B-it)、[gemma-4-12B-it](https://huggingface.co/google/gemma-4-12B-it)
- GPT-OSS：OpenAI 2025-08-05 开源（`gpt-oss-20b` / `gpt-oss-120b`，Apache-2.0）
- NVFP4：NVIDIA 4-bit 浮点量化格式（精度接近 FP8 的 4-bit 方案）
