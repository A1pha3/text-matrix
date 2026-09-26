---
title: "SANA：线性扩散 Transformer 如何把 4K 生成拉回笔记本 GPU"
date: "2026-05-18T19:56:00+08:00"
slug: "sana-high-resolution-image-synthesis"
github_repo: "NVlabs/Sana"
source_key: "gh:NVlabs/Sana"
description: "SANA 是 NVIDIA 实验室开源的高效扩散模型体系，靠线性注意力与 32× 深度压缩自编码器，在 0.6B 参数下做到与 FLUX-12B 可比的质量，把 4K 文生图从多卡集群压回一片消费级 GPU。文本编码器用 decoder-only 的 Gemma 替换 T5，配 Flow-DPM-Solver 压步数。论文被 ICLR 2025/2026 等多次接收为 Oral。"
categories: ["技术笔记"]
tags: ["扩散模型", "图像生成", "DiT", "线性注意力"]
---

# SANA：线性扩散 Transformer 如何把 4K 生成拉回笔记本 GPU

SANA 解决的不是"再做一个更强的生成模型"。它解决的是**单位成本下的生成效率**。FLUX-12B 这类模型靠堆参数换质量，代价是显存和延迟都下不来；SANA 反着走，用 0.6B 参数做出与 12B 模型可比的输出，把 4K 图像的推理从多卡集群压进一片消费级 GPU，甚至一块 16GB 显存的笔记本独显。

这不是某一处技巧的功劳，而是压缩、注意力、文本编码、采样四条线同时改。下面先把这套体系拆开，再讲每条线怎么工作。

## 家族成员：一套分工明确的体系，不是线性升级

不少资料把 SANA、SANA-1.5、SANA-Sprint 当成"新版本旧模型"，实际它们目的各不相同，是互补工具而非替代关系。先给张总览表，读者往后看到任何一员，都知道它站哪个生态位。

| 成员 | 定位 | 关键机制 | 一口能说清的能力 |
|------|------|----------|------------------|
| SANA-0.6B / 1.6B | 文生图基础模型 | 线性注意力 + DC-AE 32× 压缩 | 最高 4K；0.6B 比 FLUX-12B 快约 100 倍 |
| SANA-1.5 | 推理时扩展 | 深度增长训练、推理时重复采样 | GenEval 0.81，可从 1.6B 扩到 4.8B |
| SANA-Sprint | 单步/少步生成 | sCM + LADD 混合蒸馏 | H100 上 1024×1024 单步约 0.1 秒 |
| SANA-Video | 视频生成 | Block Linear Attention + 常驻 KV cache | 720p 分钟级，2B 参数 |
| SANA-WM | 可控世界模型 | 线性/软max 混合注意力 | 720p、1 分钟、6-DoF 相机控制 |
| SANA-Streaming | 实时流式编辑 | 混合注意力 + 流式推理 | 720p 视频实时编辑 |

这整套体系共享同一套效率哲学：凡能把序列长度或去噪步数压下来的地方都压，让越小的算力能跑越大的分辨率。

## 高分辨率为什么贵：先拆两个易混的机制

讲 SANA 的文章常把"压缩"和"注意力"放一起说，其实是两个独立问题，卡着两个不同瓶颈。

- **压缩（DC-AE）** 决定潜空间里有多少 token。分辨率每高一倍，像素翻四倍，token 跟着涨，训练和推理都会先撑不住显存。
- **注意力** 决定 token 之间怎么交互。全注意力对 N 个 token 要算两两相似度，成本随 N 平方增长，token 一多，光"两两看一遍"就把延迟拖到不可用。

SANA 两头同时压：压缩把 token 总数砍下来，线性注意力把"每个 token 的交互成本"从平方降成线性。少了任何一头，4K 都做不动。

## 核心机制逐条

### 深度压缩自编码器 DC-AE：从 8× 到 32×

传统自编码器把图像在宽度、高度上整体压 8×，潜空间面积约到原图的 1/64；DC-AE 把尺度因子拉到 32×，潜空间面积约到 1/1024。与常见的 AE-F8 相比，token 数大约降到 1/16。4K 图因此只剩很小的 token 量交给 Transformer 处理，这是整套效率的地基。

代价和优势同源：压缩越狠，重建时丢的高频细节越多。写实人像、手部这类细节密集区域是 SANA 的已知短板——这是设计取舍，不是缺陷，后文 benchmark 部分再展开。

### 线性 DiT：注意力从 O(N²) 到 O(N)

标准自注意力在 N 个 token 上计算两两相似度，成本 O(N²)；线性注意力把它拆成可累积的前缀形式，成本降为 O(N)。分辨率越高、token 越多，这一步省掉的量越是数量级。这也是 SANA 整套思路里最核心的一环。

### Decoder-only 文本编码器：用 Gemma 换掉 T5

FLUX、PixArt 用的是 T5 这类编码器—解码器结构。这里容易记反：SANA **替换掉的正是 T5**，替代者是现代 decoder-only 的小型 LLM（如 Gemma-2B），再配合复杂指令模板与上下文学习来增强图文对齐。相比 T5，Gemma 对密集指令的跟随能力更强，直接影响图文对齐质量。

## 一次生成如何流过系统

用一个具体任务把上面的环节串起来：一条 prompt 从 diffusers 进去，到读出 4K 图。

1. prompt 先进 Gemma 文本编码器，转成文本 token 的嵌入。
2. 潜空间里初始化一段随机噪声；此刻它已经是 32× 压缩后的低分辨率特征网格，token 很少，Transformer 处理得起。
3. 线性 DiT 在这个特征网格上按 Flow-DPM-Solver 的调度迭代去噪；每一轮用线性注意力在 token 之间交换信息。
4. 去噪结束，DC-AE 解码器把特征网格重建回像素图，就是你要的 4K 图。

代码上，diffusers 原生支持，已修正为可运行版本：

```python
from diffusers import SanaPipeline
import torch

pipe = SanaPipeline.from_pretrained(
    "Efficient-Large-Model/SANA1.5_1.6B_1024px_diffusers",
    torch_dtype=torch.bfloat16,
)
pipe.to("cuda")

image = pipe(prompt="a cyberpunk cat with neon signs", height=1024, width=1024)[0]
image.save("sana.png")
```

当成插件脚本跑即可：第一行从 HuggingFace 拉权重，prompt 走完上面四步，输出落到 `sana.png`。4-bit 量化后约 8GB 显存就能跑，笔记本 GPU 也能出图。

## 性能数字怎么读：先问它测了什么

不罗列分数就结束，先分清这些数字在测什么。

**延迟与吞吐（系统能力）。** SANA 的加速来自"模型更小 + token 更少 + 每 token 成本更低"三者叠加，不是单一魔法。论文在 A100、batch 1 下把 4096×4096 的生成从约 469 秒优化到约 9.6 秒，相对当时的 SOTA 展示的是系统级联合优化，不是某个组件的单点收益。0.6B 在 16GB 笔记本 GPU 上出 1024×1024 图不足 1 秒，这条可以直接复测。

**质量（对齐与真实感）。** SANA-1.5 在 GenEval 上图文对齐做到 0.81，配合推理时扩展还能再冲高；SANA-Sprint 单步 FID 7.59、GenEval 0.74，反超 FLUX-schnell（7.94 / 0.71），并在 H100 上快约 10 倍。这些数字指向"给定步数和硬件，SANA 的增益来自每一步都更省"。

**不能推出什么：**

- 对齐类指标反映的是整体图文匹配，照不到写实人像与高频细节——那恰是 32× 压缩的代价区间。
- NVIDIA 给出的对 FLUX 等的加速倍数，是在自家硬件、协议和分辨率档位下测得；换卡、换版本、换采样步数不一定复现同样的倍率。
- 拿 SANA 上产品前，必须在自己那张卡、自己常用的分辨率和步数上实测，再定取舍。

## 谁该先用，谁可以等

按任务性质分：

- 需要**速度快、批量迭代、低显存**（设计稿批量出图、素材迭代、端侧工具）：SANA 是目前最优档之一，4-bit 约 8GB 显存即可运行。
- 追求**照片级写实人像/手部**：这是当前弱项区间，建议候选对比竞品，或等官方新一代高保真自编码器。
- 要**实时交互、长视频、可控相机**：SANA-Sprint、SANA-Streaming、SANA-WM 各管一段，按任务选型即可。

一个省事的采用顺序：先用 SANA-0.6B 或 SANA-Sprint 验证速度和显存是否达标，再决定是否升到 1.5 的更大档位，或转去 Video / WM 路线做视频类任务。

## 结尾判断

SANA 的价值不在于"又多了一个生成模型"，而在把高分辨率生成的成本刻度往下挪了一档。它把效率当第一性原理，每一处省下的算力，都换成了能在更小硬件上跑更大的分辨率。追质量上限，SANA 不是终点；但在"单位算力下能拿到的质量"这条线上，它是开源里走得最激进的一支。

**GitHub**：https://github.com/NVlabs/Sana（Apache 2.0）

**论文**：

- SANA：https://arxiv.org/abs/2410.10629
- SANA 1.5：https://arxiv.org/abs/2501.18427
- SANA-Sprint：https://arxiv.org/abs/2503.09641
- SANA-Video：https://arxiv.org/abs/2509.24695

**HuggingFace**：https://huggingface.co/collections/Efficient-Large-Model/sana