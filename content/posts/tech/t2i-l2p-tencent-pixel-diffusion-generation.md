---
title: "L2P：腾讯优图开源的高效像素空间扩散生成模型"
date: 2026-05-22T20:15:00+08:00
slug: "t2i-l2p-tencent-pixel-space-diffusion-generation"
description: "L2P是腾讯优图实验室开源的文生图研究，提出了潜在潜在传递（Latent-to-Latent-to-Pixel）范式，通过最小化计算开销和数据需求实现高质量端到端像素空间扩散。技术报告已发布，代码和权重已开源。"
draft: false
categories: ["技术笔记"]
tags: ["文生图", "扩散模型", "腾讯优图", "L2P", "计算机视觉"]
---

# L2P：腾讯优图开源的高效像素空间扩散生成模型

L2P（Latent-to-Latent-to-Pixel）是腾讯优图实验室的开源文生图研究，2026-05-22 创建，22 星。提出了"潜在潜在传递"范式，在像素空间做端到端扩散。

## 核心判断

主流文生图（SD3、FLUX、Sana）都在潜在空间（latent space）做扩散——把图像压缩到低维潜在空间，在那里计算生成，再解码回像素空间。L2P 的核心观点是：潜在空间扩散对某些能力有隐式约束，如果能直接在像素空间做扩散，可以解锁更强的细粒度控制能力，但代价是计算开销更高。L2P 的目标是找到一种高效传递范式，让像素空间扩散的细粒度和潜在空间扩散的计算效率兼得。

## 技术路线

L2P = Latent-to-Latent-to-Pixel

```
输入文本 → 文本编码器 → 潜在空间初始化
                           ↓
                   潜在空间扩散（低维）
                           ↓
                   像素空间初始化（转换）
                           ↓
                   像素空间微调扩散
                           ↓
                      输出图像
```

**核心洞察：** 用潜在扩散做高效粗略生成，再用像素级扩散做细粒度增强。两阶段分工明确，计算量可控。

## 系统要求

| 组件 | 要求 |
|------|------|
| GPU | 至少 24GB VRAM（低显存训练需单独配置） |
| Python | 3.8+ |
| PyTorch | 最新版 |
| CUDA | 11.8+ |

## 安装

```bash
git clone https://github.com/TencentYoutuResearch/T2I-L2P.git
cd T2I-L2P
pip install -e .
```

## 推理

### 权重

| 模型 | 参数量 | HuggingFace |
|------|--------|-------------|
| L2P-z-image (1k) | 6B | 🤗 huggingface.co/zhen-nan/L2P |

### 代码示例

```python
import torch
from diffsynth.pipelines.z_image_L2P import ZImagePipeline, ModelConfig

main_model_path = "/path/model-1k-merge.safetensors"

text_encoder_paths = [
    "/path/Z-Image-Turbo/text_encoder/model-00001-of-00003.safetensors",
    "/path/Z-Image-Turbo/text_encoder/model-00002-of-00003.safetensors",
    "/path/Z-Image-Turbo/text_encoder/model-00003-of-00003.safetensors",
]

tokenizer_path = "/path/Z-Image-Turbo/tokenizer"

pipe = ZImagePipeline.from_pretrained(
    torch_dtype=torch.bfloat16,
    device="cuda",
    model_configs=[
        ModelConfig(path=[main_model_path]),
        ModelConfig(path=text_encoder_paths),
    ],
    tokenizer_config=ModelConfig(path=tokenizer_path),
)

prompt = "an origami pig on fire in the middle of a dark room with a pentagram on the floor"

image = pipe(
    prompt=prompt,
    seed=42,
    rand_device="cuda",
    num_inference_steps=30,
    cfg_scale=2.0,
    height=1024,
    width=1024,
)

image.save("example.png")
```

### Gradio Demo

```bash
pip install gradio
python app.py
```

自动检测空闲 GPU，多卡请求分发，Gradio 界面在 `http://0.0.0.0:23231`。

## 训练流程

完整训练分四步：

**Step 1：准备 Z-Image 权重**
下载官方 Z-Image-Turbo checkpoint：
- 🤗 [Tongyi-MAI/Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)

**Step 2：离线权重转换（latent → pixel init）**

```bash
python examples/z_image/L2P_convert_weight.py \
  --latent_ckpt_files \
    /path/to/Z-Image-Turbo/transformer/diffusion_pytorch_model-00001-of-00003.safetensors \
    /path/to/Z-Image-Turbo/transformer/diffusion_pytorch_model-00002-of-00003.safetensors \
    /path/to/Z-Image-Turbo/transformer/diffusion_pytorch_model-00003-of-00003.safetensors \
  --output_path ./pretrain_weight/Z-Image-Pixel-Init/diffusion_pytorch_model.safetensors
```

**Step 3：启动训练**

标准训练：
```bash
bash train_run.sh
```

低显存（单卡 < 24GB）：
```bash
bash train_run_low_VRAM.sh
```

数据集格式：
```
data/
├── images/                # 原始图片目录
└── metadata.csv           # 列：file_name, text, ...
```

**Step 4：离线权重合并（推理用）**

```bash
python merge_weights.py \
  --file_a ./models/train/L2P_Standard/step-xxx.safetensors \
  --file_b ./pretrain_weight/Z-Image-Pixel-Init/diffusion_pytorch_model.safetensors \
  --file_out ./models/train/L2P_Standard/model-merge.safetensors
```

## 路线图

| 状态 | 项目 |
|------|------|
| ✅ | 1K 推理代码 & 权重 |
| ✅ | 训练代码 |
| 🛠️ | 4K/8K/10K UHR 生成 |
| 🛠️ | 更多 LDM T2I 模型兼容 |

## 适用边界

**适合：**
- 细粒度文生图研究
- 像素级控制需求
- 学术研究（已有 arXiv 论文 arXiv:2605.12013）

**不适合：**
- 需要快速生成（30 步推理比纯 latent 模型慢）
- 超高分辨率（4K+ 还在开发）

## 结论

L2P 是一个有明确技术路线的研究项目：不是做产品，而是探索"latent→latent→pixel"这条路径的可行性。它的关键价值在于提出了像素空间扩散的细粒度优势和潜在空间扩散的计算效率是否可以兼得的问题。