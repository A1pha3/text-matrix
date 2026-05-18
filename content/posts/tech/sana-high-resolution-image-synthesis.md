---
title: "SANA：线性扩散Transformer驱动的高分辨率图像生成"
date: "2026-05-18T19:56:00+08:00"
slug: "sana-high-resolution-image-synthesis"
description: "SANA是NVIDIA实验室开源的高效扩散模型系列，支持最高4K分辨率文生图，比Flux-12B模型小20倍、快100倍，同时保持领先的生成质量，已被ICLR 2025/2026接收为Oral论文。"
categories: ["技术笔记"]
tags: ["扩散模型", "图像生成", "线性注意力", "DiT", "NVlabs", "高分辨率"]
---

# SANA：线性扩散Transformer驱动的高分辨率图像生成

说起高分辨率图像生成，很多人第一时间会想到 FLUX 或者 Stable Diffusion。但这两个模型要么体积庞大（FLUX-12B），要么生成速度感人。NVIDIA 实验室开源的 **SANA** 给出了一种截然不同的路线——用线性注意力（Linear Attention）替换 Transformer 中的标准注意力机制，配合 32× 压缩率的 DC-AE 自编码器，在仅 1.6B 参数规模下实现 **4K 分辨率、20 倍体积压缩、100 倍速度提升**。

## 核心架构：从标准注意力到线性注意力的改造

SANA 的核心创新在于用**线性注意力**替代传统 DiT 中的全注意力。在标准扩散 Transformer 中，随着分辨率提升，注意力计算的复杂度呈平方增长——生成 1024×1024 图像已经是负担，4K 分辨率几乎不可行。

SANA 的解决方案是：

1. **线性注意力机制**：将 softmax 注意力改写为线性形式，复杂度从 O(N²) 降到 O(N)，显著降低高分辨率下的计算成本
2. **DC-AE 32× 压缩自编码器**：传统 VAE 通常压缩 8 倍，SANA 团队提出的 DC-AE 可压缩 32 倍，将 4K 图像的潜空间 token 数量减少到原来的 1/16
3. **Decoder-only 文本编码器**：使用现代 LLM（如 Google 的 T5）作为文本编码器，而非传统的 BERT 系列模型，获得更强的图文对齐能力

这三个设计共同作用，使得 SANA-1.6B 能在消费级 GPU 上完成 4K 图像生成，且 FID、CLIP、GenEval 等指标全面超越 FLUX-dev。

## 家族成员：不止是文生图

SANA 并不是一个单一模型，而是一个完整的生成模型体系：

| 成员 | 定位 | 亮点 |
|------|------|------|
| **SANA** | 文生图基础模型 | 最高 4K 分辨率，1.6B 参数 |
| **SANA-1.5** | 推理时扩展 | 推理步数压缩，质量反而提升 |
| **SANA-Sprint** | 单步/少步生成 | sCM 蒸馏技术，H100 上 0.1s/张 |
| **SANA-Video** | 视频生成 | Block Causal Linear Attention |
| **SANA-WM** | 可控世界模型 | 720p、1分钟、6-DoF 相机控制 |

特别是 **SANA-Sprint**，通过连续时间一致性蒸馏（sCM）技术，将图像生成压缩到单步或少数几步，同时保持视觉质量。H100 上 1024px 图像仅需 0.1 秒，RTX 4090 上也只需 0.3 秒，这是目前开源方案中最快的几步生成方案之一。

## 性能对比：速度与质量的双重碾压

在 1024×1024 分辨率下，SANA 的 benchmark 数据相当有说服力：

- **SANA-0.6B**：吞吐量 1.7 samples/s，延迟仅 0.9s，比 FLUX-dev 快 39.5 倍
- **SANA-1.5-1.6B**：CLIP Score 达到 29.12，GenEval 0.82，全面领先 FLUX-dev
- **SANA-1.5-4.8B**：4.8B 规模的顶配版本，DPG 得分 84.7，为系列最高

在视频生成任务上，SANA-Video-2B 的 VBench 总分 84.05，延迟 36 秒，仅用 2B 参数就超越了 14B 的 Wan-2.1 模型，效率提升约 50 倍。

## 易用性：diffusers 原生支持

SANA 已完整集成到 Hugging Face diffusers 生态，一行代码即可调用：

```python
from diffusers import SanaPipeline

pipe = SanaPipeline.from_pretrained(
    "Efficient-Large-Model/SANA1.5_1.6B_1024px_diffusers",
    torch_dtype=torch.bfloat16,
)
pipe.to("cuda")

image = pipe(prompt="a cyberpunk cat with neon signs", height=1024, width=1024)[0]
image[0].save("sana.png")
```

同时支持 ComfyUI、SGLang（OpenAI 兼容 API）、Cosmos-RL 强化学习训练等多种部署方式。4-bit 量化后只需 8GB 显存，笔记本 GPU 也能跑。

## 技术演进路线

从 2024 年 10 月首次发布至今，SANA 保持着极高的迭代速度：

- **2024/12**：diffusers 集成、LoRA/DreamBooth 微调支持
- **2025/01**：4K 模型发布、4-bit 量化方案、DCAE-1.1 升级
- **2025/03**：SANA-Sprint（单步生成）、SANA-1.5（推理时扩展）
- **2025/10**：SANA-Video 视频生成、LongSANA（分钟级长视频）
- **2026/03**：SANA-Video 720p + LTX-VAE 2K 超分
- **2026/04**：Sol-RL（NVFP4 推理 + BF16 训练的强化学习 pipeline）
- **2026/05**：SANA-WM（2.6B 可控世界模型，支持 6-DoF 相机控制）

## 总结

SANA 的出现重新定义了"高效扩散模型"的标准。线性注意力的引入不仅是工程上的优化，更是一种架构思路的转变——它证明了在高分辨率生成任务上，不是只有 scale up 才能提升质量，**架构效率的提升同样可以带来质的飞跃**。如果你正在寻找一个既快又好的开源图像/视频生成方案，SANA 家族值得重点关注。

**GitHub**：https://github.com/NVlabs/Sana
**论文**：https://arxiv.org/abs/2410.10629
**HuggingFace**：https://huggingface.co/collections/Efficient-Large-Model/sana