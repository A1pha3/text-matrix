---
title: "SAM 3：从分割单个物体到分割一个概念"
date: "2026-05-23T13:09:23+08:00"
lastmod: "2026-09-29T12:00:00+08:00"
slug: "sam3-segment-anything-model-3"
github_repo: "facebookresearch/sam3"
source_key: "gh:facebookresearch/sam3"
description: "SAM 3 把分割从“圈出一个物体”推进到“分割一个开放词汇概念的全部实例”：一句文本或几张示例图，就能穷尽分割出所有匹配实例，并逐帧跟踪。"
draft: false
categories: ["技术笔记"]
tags: ["计算机视觉", "Meta", "开源", "图像分割", "SAM"]
---

# SAM 3：从分割单个物体到分割一个概念

SAM 3 与前两代的分水岭不在精度和速度，而在提示的含义。SAM 1 用点或框圈出一个具体对象，SAM 2 把这个对象逐帧跟下去；SAM 3 接受的是一句自然语言短语或几张示例图，然后一口气把“这个概念”在画面里的所有实例都分割出来。官方把这套能力叫可提示概念分割（Promptable Concept Segmentation，PCS）。

一段演示最能说明差别：给 SAM 3 一句 `a player in white`，它不会返回“最像的一个球员”，而是把所有穿白色球衣的球员逐个切开，并在一整段视频里保持跟踪。这是 SAM 1/2 做不到的——它们只有“实例”这一层抽象，没有“概念”。

**分类：** CV · 图像分割 / 视频分割
**地址：** https://github.com/facebookresearch/sam3 （11,834 stars，2026-09-29）
**协议：** SAM License（Meta 自定义协议，见仓库 LICENSE 文件）
**权重：** [facebook/sam3](https://huggingface.co/facebook/sam3)（需申请访问）
**论文：** https://ai.meta.com/research/publications/sam-3-segment-anything-with-concepts/

## 系统地图：两个模型部件，一条数据生产线

SAM 3 的模型本体由检测器与跟踪器两个部件组成，共享同一个视觉主干；数据引擎是训练侧的配套设施，不参与推理。理解这个分工比记住总参数量更有用。

| 组件 | 是什么 | 职责 |
|------|------|------|
| Detector（检测器） | 模型部件，基于 DETR | 在单帧图像里按提示发现概念的所有实例，接受文本、几何提示（点/框）、图像示例的任意组合 |
| Tracker（跟踪器） | 模型部件，继承 SAM 2 | 把实例的 mask 跨帧传播，支持视频分割与交互式精修 |
| Data Engine（数据引擎） | 训练数据生产线 | 自动标注概念级分割数据，已产出超过 400 万个独特概念，构成当前最大的开放词汇分割数据集 |

整个模型 848M 参数。检测与跟踪拆开（decoupled）不是工程偷懒：两者任务互相干扰，捆在一个网络里会互相拖累；拆开后每个模块能用自己最合适的数据规模和结构独立扩展。

## 概念分割难在哪

把“分割一个概念”和“分割一个实例”区分开，是理解 SAM 3 的第一步。

- **实例分割**（SAM 1/2 的活）：提示明确指向一个物体，答案唯一，歧义少。
- **概念分割**（SAM 3 的新能力）：提示是开放词汇（open-vocabulary）——一句短文本或几张示例图——答案不唯一，画面里可能有 0 个、5 个或 20 个匹配实例，全都要找出来。

这带来两个新问题。第一，开放词汇意味着提示空间巨大：概念可以具体到“左臂有纹身的男人”，也可以抽象到“正在庆祝的人”。第二，相近概念的区分变难：“a player in white”和“a player in red”只差一个颜色词，模型不能把两类都当作“球员”糊弄过去。前者靠数据引擎喂足样本，后者靠 presence token 给出显式回答。

## 核心机制：presence token

presence token（存在标记）是 SAM 3 架构里最直观的一处改动。论文对它的概括是：把识别与定位解耦——模型除了预测框和 mask（定位），还要用一个专门的 presence head 独立回答“提示所指的东西在这张图里到底存不存在”（识别）。

它压掉两类失败。一是误报：画面里有“长得像提示所指的东西”，但提示其实没有匹配对象，存在性判断直接否掉这类候选。二是负提示（negative prompts）：SA-Co 基准里专门有一类短语，画面中没有任何匹配实例，正确输出就是空——没有这路显式信号，模型只能靠置信度阈值硬猜。README 对它的定位是改善相近文本提示之间的区分，官方对照例子正是 “a player in white” 与 “a player in red”：两者都会激活“球员”的语义，区别只在颜色词，存在性信号让模型能分别回答两类球员“在不在”，而不是把相近概念混在一起。

## 核心机制：detector 与 tracker 的分工

单帧的发现由 detector 负责，跨帧的延续交给 tracker。

Detector 基于 DETR，一种以集合预测为目标的目标检测范式：一次前向输出一组定长预测，与真实实例做二部图匹配，天然适合“数量不定的实例”。它的条件输入有三种：文本（开放词汇的语义）、几何（点或框，用于交互式精修）、图像示例（给几张目标物的图，等效于“我说不清，给你看”）。三种条件可以任意组合——纯文本、文本加框、纯示例都行。

Tracker 直接继承 SAM 2 的 transformer encoder-decoder 架构。它存在的原因是视频分割是另一个任务：实例在帧间移动、被遮挡、又重现，需要时序记忆而不是逐帧重新检测。Detector 负责“发现”，tracker 负责“跟住”，两者共享视觉主干但各干各的。

## 一个任务如何流过系统

把上面的机制串成一个最小案例：输入一段足球比赛视频，提示 `all players in white`。

1. **首帧发现**：文本提示经过编码变成条件，视觉编码器提供特征，DETR 式的输出给出这一帧里所有白队球员的框、mask 和存在性分数。
2. **交互精修**：如果某个球员在首帧被队友挡住，分割不完整，用户可以在遮挡处补一个负样本点，按 SAM 系列的交互方式修正结果。
3. **跨帧传播与持续发现**：tracker 把首帧的每个实例 mask 作为初始状态，靠时序记忆逐帧传播；与此同时，新入场的球员、被遮挡后重新露出的实例，由 detector 在后续帧继续发现，再通过检测-跟踪关联（detection-tracker association）并入已跟踪的对象集合。中途出现的对象不会因为“错过了首帧”而漏掉。
4. **同一套权重**：图像和视频跑的是同一个 848M 参数的模型，区别只是 detector 与 tracker 的协作方式，不是两套网络各配一份参数。

拆分的理由随之清楚：发现靠单帧的开放词汇识别，跟住靠跨帧的时序记忆，两种能力放在一个网络里互相拖累。README 的原话是解耦设计“最小化任务干扰、随数据高效扩展”。

## 真实用法：图像与视频

图像分割：文本或框提示，返回 mask、框和分数。

```python
import torch
from PIL import Image
from sam3.model_builder import build_sam3_image_model
from sam3.model.sam3_image_processor import Sam3Processor

model = build_sam3_image_model()
processor = Sam3Processor(model)

image = Image.open("photo.jpg")
state = processor.set_image(image)
output = processor.set_text_prompt(state=state, prompt="a player in white")

masks, boxes, scores = output["masks"], output["boxes"], output["scores"]
```

视频分割：起一个会话，在任意帧加提示，后续帧自动跟踪。

```python
from sam3.model_builder import build_sam3_video_predictor

predictor = build_sam3_video_predictor()
response = predictor.handle_request(
    request=dict(type="start_session", resource_path="game.mp4")
)
response = predictor.handle_request(
    request=dict(
        type="add_prompt",
        session_id=response["session_id"],
        frame_index=0,  # 任意帧
        text="all players in white",
    )
)
output = response["outputs"]
```

## benchmark：SA-Co 在测什么

SA-Co（Segment Anything with Concepts）是随 SAM 3 发布的评估集，官方指标叫 cgF1，整体规模是 27 万个独特概念——README 的说法是比现有基准多 50 倍以上。它分三块：SA-Co/Gold 和 SA-Co/Silver 测图像（Gold 含属性、拥挤场景、维基常见词等 7 个标注域，图片来自 MetaCLIP 和 SA-1B），SA-Co/VEval 测视频（覆盖 SA-V、YT-Temporal-1B、智能眼镜第一视角三个来源）。每个数据点由 3 名独立标注者分别标注，评估时对模型取最有利的一条（oracle 设置），三人之间的一致性同时给出人类表现的参照。看数字之前，先回答三个问题。

- **测的是什么**：SA-Co 测的是开放词汇概念分割——给一个文本概念，模型能否把图像和视频里所有匹配实例都找对，包括答案是“没有”的负提示。它不同于 LVIS 那种封闭 1200 余类的检测基准；SA-Co 的类别空间是开放的，更接近真实使用时的提示分布。
- **数字反映系统的哪一部分**：SA-Co 上的表现主要归功于数据引擎（400 万概念的训练数据）和 presence token（区分相近概念、处理负提示的输出头）。单靠 SAM 2 架构加一层文本编码，很难在 27 万概念上拿到这个水平。
- **不能推出什么**：README 的总口径是 SAM 3 达到人类表现的 75%～80%，这不等于接近完美。拆开看，图像 SA-Co/Gold 上人类 cgF1 为 72.8、SAM 3 为 54.1（约为人类的 74%）；视频三个域分别是 57%、71%、62%。概念极其模糊或实例在画面里几乎不可见时，SAM 3 同样会漏。封闭集检测是另一套指标：SAM 3 在 LVIS 的 cgF1 为 37.2，高于对照模型 OWLv2 的 29.3——不过 OWLv2 带着部分训练于 LVIS 的脚注，这个领先要打折扣。

## 什么时候该升级到 SAM 3

- 要分割“一个概念的全部实例”，且概念用文本或示例描述 → 这是 SAM 3 的核心增量，直接用 SAM 3。
- 只需要在单张图里点选一个具体物体 → SAM 3 完整支持这类交互式分割（论文口径是在 SAM 2 的任务上持平或更好），但 SAM 2 权重更小、生态更成熟，单纯点选没有换模型的理由。
- 视频里持续跟踪一个已知对象 → SAM 2 的路径更省显存；要按文本跟踪一批对象、且对象数量多，用 SAM 3.1，Object Multiplex 就是为此设计的。
- 需要把分割作为工具接给多模态大模型 → SAM 3 提供 agent 式用法（SAM 3 Agent，仓库 examples 里有对应 notebook），适合这类集成。

## 安装与注意事项

- 前置条件：Python 3.12+、PyTorch 2.7+、CUDA 12.6+ 的 GPU。
- 权重不在仓库里直接分发：需要先在 Hugging Face 的 `facebook/sam3` 仓库申请访问，通过后用 `hf auth login` 认证才能下载；SAM 3.1 权重在 `facebook/sam3.1`。
- SAM 3.1（2026-03-27 发布）：核心是 Object Multiplex。此前视频流水线对每个跟踪对象独立处理，开销随对象数线性增长；3.1 把对象分进固定容量的桶联合处理，单张 H100 上 128 个对象的跟踪约为 2025 年 11 月首版的 7 倍速度。官方口径是精度不吃亏：YT-Temporal-1B 提升 2.1 cgF1，7 个 VOS 基准 6 个上涨（MOSEv2 +2.0），SA-Co/VEval 各域互有涨跌。技术细节在论文附录 H。使用 3.1 权重需要拉取仓库最新代码后重装。
- 想提速可装 `flash-attn-3`、`cc_torch` 等可选依赖，官方 README 有完整清单。

以上安装要求与模型细节按 2026-09-29 的仓库 main 分支核实；SAM 3 没有版本化发布，环境配置以仓库 README 当前内容为准。

**相关工具：** [Supervision](/posts/tech/supervision-computer-vision-toolbox/)
