---
title: "SAM 3：从分割单个物体到分割一个概念"
date: "2026-05-23T13:09:23+08:00"
slug: "sam3-segment-anything-model-3"
github_repo: "facebookresearch/sam3"
description: "SAM 3 把分割从“圈出一个物体”推进到“分割一个开放词汇概念的全部实例”：一句文本或几张示例图，就能穷尽分割出所有匹配实例，并逐帧跟踪。"
draft: false
categories: ["技术笔记"]
tags: ["计算机视觉", "Meta", "开源", "图像分割", "SAM"]
---

# SAM 3：从分割单个物体到分割一个概念

SAM 3 与前两代的分水岭不在精度和速度，而在提示的含义。SAM 1 用点或框圈出一个具体对象，SAM 2 把这个对象逐帧跟下去；SAM 3 接受的是一句自然语言短语或几张示例图，然后一口气把“这个概念”在画面里的所有实例都分割出来。官方把这套能力叫可提示概念分割（Promptable Concept Segmentation）。

一段演示最能说明差别：给 SAM 3 一句 `a player in white`，它不会返回“最像的一个球员”，而是把所有穿白色球衣的球员逐个切开，并在一整段视频里保持跟踪。这是 SAM 1/2 做不到的——它们只有“实例”这一层抽象，没有“概念”。

**分类：** CV · 图像分割 / 视频分割
**地址：** https://github.com/facebookresearch/sam3
**论文：** https://ai.meta.com/research/publications/sam-3-segment-anything-with-concepts/

## 阅读指引

读完下面这些问题应该有答案：

- SAM 3 为什么把检测和跟踪拆成两个模块，而不是合成一个网络
- presence token 解决的是哪一类提示歧义
- SA-CO 基准比 LVIS 大 50 倍的概念量，意味着它在测什么
- 你的任务在什么条件下从 SAM 2 升级到 SAM 3 才有收益

## 系统地图：先分清三块部件

SAM 3 由三块各自独立的部件组成，理解它们的分工比记住总参数量更关键。

| 部件 | 职责 | 说明 |
|------|------|------|
| Detector（检测器） | 在单帧图像里按提示发现并分割概念的所有实例 | 基于 DETR，输入是文本、几何提示（点/框）、图像示例的组合 |
| Tracker（跟踪器） | 把实例的 mask 跨帧传播，支持视频分割与交互式精修 | 继承 SAM 2 的 transformer encoder-decoder 架构 |
| Data Engine（数据引擎） | 自动标注概念级分割训练数据 | 已产出超过 400 万个独特概念，构建当前最大的开放词汇分割数据集 |

三者共享同一个视觉编码器，模型总参数 848M。检测与跟踪拆开（decoupled）不是工程偷懒，而是刻意为之：两者任务互相干扰，捆在一个网络里会互相拖累；拆开后每个模块能用自己最合适的数据规模和结构独立扩展。

## 概念分割难在哪

把“分割一个概念”和“分割一个实例”区分开，是理解 SAM 3 的第一步。

- **实例分割**（SAM 1/2 的活）：提示明确指向一个物体，答案唯一，歧义少。
- **概念分割**（SAM 3 的新能力）：提示是开放词汇（open-vocabulary）——一句短文本或几张示例图——答案不唯一，画面里可能有 0 个、5 个或 20 个匹配实例，全都要找出来。

这带来两个新问题。第一，开放词汇意味着提示空间巨大：概念可以具体到“左臂有纹身的男人”，也可以抽象到“正在庆祝的人”。第二，相近概念的区分变难：“a player in white”和“a player in red”只差一个颜色词，模型不能把两类都当作“球员”糊弄过去。前者靠数据引擎喂足样本，后者靠 presence token 给出显式回答。

## 核心机制：presence token

presence token（存在标记）是 SAM 3 架构里最直观的一处改动。模型在预测框和 mask 的同时，为每个候选实例额外输出一个存在性信号，显式回答“这个实例是否真的匹配提示”，用来压掉那些“模型觉得像、但提示里其实没有”的误报。

官方给出的对照例子正是“a player in white”与“a player in red”：两者都会激活“球员”的语义，区别只在颜色。presence token 让模型能分别回答“白队球员存在/不存在”，而不是靠全局概率把相近概念混在一起。代价是多一个输出头，换来相近提示之间更干净的区分。

## 核心机制：detector 与 tracker 的分工

单帧的分割由 detector 负责，跨帧的延续交给 tracker。

Detector 基于 DETR，一种以集合预测为目标的目标检测范式：一次前向输出一组定长预测，与真实实例做二部图匹配，天然适合“数量不定的实例”。它的条件输入有三种：文本（开放词汇的语义）、几何（点或框，用于交互式精修）、图像示例（给几张目标物的图，等效于“我说不清，给你看”）。三种条件可以任意组合——纯文本、文本加框、纯示例都行。

Tracker 直接继承 SAM 2 的架构。它存在的原因是视频分割是另一个任务：实例在帧间移动、被遮挡、又重现，需要时序记忆而不是逐帧重新检测。Detector 负责“首帧发现”，tracker 负责“之后一直跟住”，两者共享视觉特征但各干各的。

## 一个任务如何流过系统

把上面的机制串成一个最小案例：输入一段足球比赛视频，提示 `all players in white`。

1. **首帧发现**：detector 在用户指定帧上运行。文本提示经过编码变成条件，视觉编码器提供特征，DETR 式的输出给出这一帧里所有白队球员的框、mask 和存在性分数。
2. **交互精修**：如果某个球员在首帧被队友挡住，分割不完整，用户可以在遮挡处点一个负样本，detector 只精修这一帧的 mask，不需要重跑全集。
3. **跨帧传播**：首帧结果交给 tracker，它把每个实例的 mask 作为初始状态逐帧传播。遮挡后重现的对象靠时序记忆接续。
4. **稀疏与稠密分离**：全程只有一个 848M 参数的模型在跑，但检测只在关键帧（首帧、用户交互帧）触发，其余帧走跟踪路径，避免每帧都做全集检测。

这个案例回答的是“为什么一个模型要拆两个模块”：检测是稀疏的（只在需要时触发），跟踪是稠密的（每帧都在跑），把两者捆在一起会让稀疏和稠密互相迁就。

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

## benchmark：SA-CO 在测什么

SA-CO（Segment Anything with Concepts）是随 SAM 3 发布的评估集，核心数字是 270,000 个独特概念，比此前的最大基准多 50 倍以上。官方的公开结论是 SAM 3 在 SA-CO 上达到人类表现的 75%～80%。看数字之前，先回答三个问题。

- **测的是什么**：SA-CO 测的是开放词汇概念分割——给一个文本概念，模型能否把图像和视频里所有匹配实例都找对。它不同于 LVIS 那种封闭 1200 类的检测基准；SA-CO 的类别空间是开放的，更接近真实使用时的提示分布。
- **数字反映系统的哪一部分**：SA-CO 上的表现主要归功于数据引擎（400 万概念的训练数据）和 presence token（区分相近概念的输出头）。单靠 SAM 2 架构加一层文本编码，不可能在 27 万概念上拿到这个水平。
- **不能推出什么**：75%～80% 是对人类水平而言，不等于接近完美。概念极其模糊（比如“这张图里的主体”）或实例在画面里几乎不可见时，SAM 3 同样会漏。这个数字也不能说明它在 LVIS 这类封闭集检测上优于专用模型——那是另一套指标：SAM 3 在 LVIS 的 cgF1 为 37.2，高于 OWLv2 的 29.3，但和专用检测模型的极限仍有差距。

## 什么时候该升级到 SAM 3

- 要分割“一个概念的全部实例”，且概念是开放词汇的（用文本描述）→ 这是 SAM 3 相对 SAM 2 的唯一增量来源，直接升级。
- 只需要在单张图里点选一个具体物体 → SAM 2 或 SAM 1 足够。SAM 3 模型更大（848M），这种场景没有收益。
- 视频里持续跟踪一个已知对象、不需要概念抽象 → SAM 2 的成熟路径更省显存、生态更稳。
- 需要把分割作为工具接给多模态大模型 → SAM 3 提供 agent 式用法（SAM 3 Agent），适合这类集成。

## 安装与注意事项

- 前置条件：Python 3.12+、PyTorch 2.7+、CUDA 12.6+ 的 GPU。
- 权重不在仓库里直接分发：需要先在 Hugging Face 的 `facebook/sam3` 仓库申请访问，通过后用 `hf auth login` 认证才能下载。
- SAM 3.1（2026-03 发布）：新增 Object Multiplex，用共享内存方式做多目标联合跟踪，官方口径是显著更快且精度不降。使用 3.1 权重需要拉取仓库最新代码后重装。
- 想提速可装 `flash-attn-3`、`cc_torch` 等可选依赖，官方 README 有完整清单。

**相关工具：** [Supervision](/posts/tech/supervision-computer-vision-toolbox/)
