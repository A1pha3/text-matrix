---
title: "L2P：腾讯开源的 Latent-to-Pixel 文生图高效迁移范式"
date: "2026-05-23T03:15:00+08:00"
slug: "t2i-l2p-latent-potential-pixel-generation"
description: "腾讯音视频实验室开源的 L2P 项目，将 latent-space 扩散模型（如 Z-Image-Turbo）的知识通过参数高效微调迁移到 pixel-space 端到端生成，在 1K 分辨率下实现高质量图像合成，训练数据需求和计算开销均显著低于从零训练。"
draft: false
categories: ["技术笔记"]
tags: ["文生图", "扩散模型", "腾讯", " latent-space", "pixel-space", "参数高效微调"]
---

## 项目概览

L2P（Latent-to-Pixel）是腾讯音视频实验室（Tencent Youtu Research）开源的一个文生图（Text-to-Image）项目，GitHub 仓库地址为 [TencentYoutuResearch/T2I-L2P](https://github.com/TencentYoutuResearch/T2I-L2P)。Stars 目前为 56，语言以 Python 为主。项目的核心主张很直接：把已经训练好的 latent-space 扩散模型的知识，迁移到 pixel-space 的端到端生成框架里，从而在低数据、低算力条件下获得高质量的文生图模型。

从技术路线看，这是一个参数高效微调（PEFT）场景下的知识迁移问题。L2P 并不从零训练一个 pixel-space 扩散模型，而是以一个已经具备强大文本-图像对齐能力的 latent-space 模型为教师，通过一套专门的初始化和微调策略，让学生在 pixel-space 中继承教师的能力，同时绕过 latent-space 模型需要的 VAE 解码步骤。

目前已发布 1K 分辨率的推理代码、权重和训练流程；4K/8K/10K 超高分辨率生成以及更多 LDM 文生图模型的兼容支持仍在开发中。

---

## 为什么值得看

latent-space 扩散模型（如 Stable Diffusion、DALL-E 系列、Z-Image 等）依赖 VAE 将图像编码到低维潜在空间，在潜在空间内完成去噪过程后再通过 VAE 解码恢复像素空间图像。这种范式的好处是生成质量高、文本对齐好，坏处是端到端推理必须串一个 VAE 解码器，在某些部署场景下是额外开销。

pixel-space 扩散模型则直接在像素空间进行去噪，理论上是真正的端到端——但从零训练的难度极高，数据需求和计算成本让大多数团队无法承担。

L2P 解决的就是这个问题：如何用已训练好的 latent-space 模型（教师）来指导 pixel-space 模型（学生）的训练，让学生继承教师的文本-图像对齐能力，而不需要海量标注数据和千卡训练。

从结果看，L2P 提供的 L2P-z-image（1k 分辨率）模型只有 6B 参数，在 HuggingFace 上可以直接下载使用，推理时配合 Z-Image-Turbo 的文本编码器和 tokenizer 即可出图。如果你在研究扩散模型的部署优化、文生图模型的高效微调，或者对 latent-to-pixel 知识迁移感兴趣，L2P 是目前少数有完整开源代码和权重的实践案例。

---

## 核心机制

### 初始化：从 latent 到 pixel 的转换

L2P 训练流程的第一步，是将已训练好的 latent-space DiT（Diffusion Transformer）权重转换为 pixel-space 初始化权重。

具体来说，latent-space 扩散模型的输入是 VAE 编码后的低分辨率特征图，去噪过程在 latent 空间完成。而 pixel-space 模型的输入是原始像素，去噪维度远高于 latent 空间。L2P 通过一个专门的转换脚本（`L2P_convert_weight.py`），将 latent 空间的权重矩阵重新映射到 pixel 空间的对应结构，作为学生模型的初始化起点。这个初始化不是简单的维度拉伸，而是有结构对应关系的权重迁移。

这一步是 L2P 能够高效微调的基础——一个好的初始化意味着学生模型不需要从噪声中重新学习图像的基本表征，只需要在此基础上学会"如何在像素空间直接去噪"。

### 训练：Delta 学习与权重合并

初始化之后，L2P 采用的是典型的 delta 学习策略：学生模型在 pixel-init 权重基础上进行微调，训练的是两者之间的差值（delta）。训练完成后，推理时需要将训练得到的 delta 与 pixel-init 权重合并，生成最终的 merged checkpoint。

这种做法的好处是：训练阶段只需要优化 delta 部分，对算力和显存的要求大幅降低；合并后的权重可以直接替换原始 pixel-init 用于推理，不需要修改模型结构。

### 推理：配合 Z-Image-Turbo 的文本编码器

L2P 的推理流程需要两个部分：合并后的 pixel-space 主模型，以及 Z-Image-Turbo 的文本编码器和 tokenizer。README 中的示例使用了 `diffsynth` 库的 `ZImagePipeline`，配合 `torch.bfloat16` 和 CUDA 设备，30 步推理生成 1024×1024 图像，cfg_scale 为 2.0。

也就是说，L2P 训练只负责 pixel-space 主模型的权重，而文本编码侧直接复用了 Z-Image-Turbo 的部分，这体现了 latent-space 模型在文本理解侧的优势已经通过蒸馏或迁移被 L2P 学生模型吸收。

---

## 训练流程详解

L2P 的完整训练分为四个步骤：

**Step 1 · 准备 Z-Image 基础权重**

从 HuggingFace 下载官方 Z-Image-Turbo checkpoint。这是腾讯内部训练的一个 latent-space 文生图模型，具备较强的文本-图像对齐能力，作为 L2P 的教师模型。

**Step 2 · 离线权重转换**

将 Step 1 的 latent-space DiT 权重转换为 pixel-space 初始化权重，命令如下：

```bash
python examples/z_image/L2P_convert_weight.py \
  --latent_ckpt_files \
    /path/to/Z-Image-Turbo/transformer/diffusion_pytorch_model-00001-of-00003.safetensors \
    /path/to/Z-Image-Turbo/transformer/diffusion_pytorch_model-00002-of-00003.safetensors \
    /path/to/Z-Image-Turbo/transformer/diffusion_pytorch_model-00003-of-00003.safetensors \
  --output_path ./pretrain_weight/Z-Image-Pixel-Init/diffusion_pytorch_model.safetensors
```

**Step 3 · 启动训练**

数据集需要提供原始图像目录和 CSV 元数据文件（包含 file_name 和 text 列）。标准训练和低显存（单卡 < 24 GB VRAM）两条命令分别对应 `train_run.sh` 和 `train_run_low_VRAM.sh`。

**Step 4 · 离线权重合并**

训练产生的 delta 权重需要与 Step 2 的 pixel-init 权重合并后才能用于推理：

```bash
python merge_weights.py \
  --file_a ./models/train/L2P_Standard/step-xxx.safetensors \
  --file_b ./pretrain_weight/Z-Image-Pixel-Init/diffusion_pytorch_model.safetensors \
  --file_out ./models/train/L2P_Standard/model-merge.safetensors
```

合并后的权重文件即可通过 `ZImagePipeline` 加载推理。

---

## 任务流案例

假设你有一批自定义风格的图像，想要训练一个能够在像素空间直接生成的文生图模型，风格高度可控，不需要 VAE 解码环节：

1. **准备数据**：收集图像 + 文本描述，整理为 `images/` 目录 + `metadata.csv`（file_name, text）格式。
2. **下载 Z-Image-Turbo**：从 HuggingFace 获取教师模型权重。
3. **运行权重转换**：通过 L2P_convert_weight.py 将 latent 权重转换为 pixel-init 权重。
4. **启动训练**：执行 `bash train_run.sh`（或低显存版本），等待 delta 权重收敛。
5. **合并权重**：运行 merge_weights.py 生成最终的 merged checkpoint。
6. **推理验证**：用 `ZImagePipeline` 加载 merged 权重，输入 prompt 测试生成质量。

整个流程中，Step 2 和 Step 4 都是离线操作，不需要 GPU；真正的训练和推理在 Step 3 和 Step 6 完成。

---

## 适用边界

**适合的场景：**
- 研究参数高效微调在文生图领域的应用
- 探索 pixel-space 端到端扩散模型的训练范式
- 需要在低算力条件下微调文生图模型（单卡 < 24 GB VRAM 有专门脚本支持）
- 对腾讯 Z-Image 技术路线感兴趣

**不适合的场景：**
- 需要成熟稳定生产级文生图pipeline（当前路线图仍在推进 4K/8K/10K 支持）
- 需要兼容更多 LDM 模型（L2P 当前主要针对 Z-Image-Turbo）
- 需要从零训练全新架构（而非基于已有模型做知识迁移）

---

## 参考文献

项目引用了两篇论文：

```bibtex
@article{chen2026l2p,
  title   = {L2P: Unlocking Latent Potential for Pixel Generation},
  author  = {Chen, Zhennan et al.},
  journal = {arXiv preprint arXiv:2605.12013},
  year    = {2026}
}

@article{chen2025dip,
  title   = {DiP: Taming Diffusion Models in Pixel Space},
  author  = {Chen, Zhennan et al.},
  journal = {arXiv preprint arXiv:2511.18822},
  year    = {2025}
}
```

其中 DiP（arXiv:2511.18822）是 L2P 的前序工作，提出了在像素空间驯服扩散模型的基础方法；L2P 则在此基础上进一步实现了 latent-to-pixel 的高效知识迁移。技术报告发布于 2026 年 5 月，数据集和预训练权重托管在 HuggingFace 上（zhen-nan/L2P 和 zhen-nan/L2P-dataset）。