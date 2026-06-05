+++
date = '2026-05-18T00:00:00+08:00'
draft = false
title = 'Sana：NVIDIA 高效图像与视频生成框架'
slug = 'nvlab-sana-efficient-image-video-generation'
description = 'Sana 是 NVIDIA MVFX 实验室出品的效率优先型图像/视频生成框架，支持 4K 分辨率、1.6B 参数模型可在 8GB GPU 显存运行，ICLR 2025/2026 双 Oral 论文。'
categories = ['技术笔记']
+++

# Sana：NVIDIA 高效图像与视频生成框架

GitHub: [NVlabs/Sana](https://github.com/NVlabs/Sana)

Sana 是 NVIDIA MVFX 实验室出品的效率优先型图像/视频生成框架，支持 4K 分辨率、1.6B 参数模型可在 8GB GPU 显存运行，ICLR 2025/2026 双 Oral 论文，并在 diffusers、SGLang、ComfyUI 均有原生集成。

## 核心能力

### Sana-Image：高效图像生成
- **1.6B 参数**，支持最高 4K (4096×4096) 分辨率
- **8GB GPU 显存可跑 4K**（通过 4bit 量化 + model offload）
- 20 秒生成 4K 图片（H100）/ 1 分钟内 RTX 4090
- 支持 ControlNet、LoRA 微调

### Sana-1.5：推理时缩放（Inference-time Scaling）
ICML 2025 收录，通过推理时计算资源调度提升生成质量，无需额外训练。

### Sana-Sprint：单步生成
ICCV 2025 Highlight，0.1 秒生成 1024px 图片（H100），0.3 秒 RTX 4090，接近实时的生成速度。

### Sana-Video：视频生成
- 720p 长视频生成（LTX-VAE 压缩）
- 支持文生视频、图生视频
- ICLR 2026 Oral 收录

### Sana-WM：世界模型（2026-05 新发布）
- **2.6B 可控世界模型**，支持 720p、1分钟视频生成
- 6-DoF 相机控制
- 定位为 Embodied AI 和 World Modeling 新基准

### Sol-RL：强化学习后训练
完整的 RL 后训练基础设施，支持 SANA、FLUX.1、SD3.5-L 模型。

## 技术特色

**Linear DiT 架构**：替代传统 attention，显著降低计算复杂度，支持无限上下文（用于长视频生成）。

**DC-AE 变分自编码器**：高效的图像/视频压缩，降低 VAE 重建开销。

**多后端支持**：原生集成 diffusers、SGLang（OpenAI 兼容 API）、ComfyUI（节点式工作流）。

## 快速上手

```python
# diffusers 方式
from diffusers import SanaPipeline, SanaPAGPipeline

pipe = SanaPipeline.from_pretrained("Efficient-Large-Model/Sana_1600M_1024px_BF16_diffusers")
image = pipe("a beautiful sunset over the ocean").images[0]

# 4K 生成（8GB 显存可用）
pipe_4k = SanaPipeline.from_pretrained("Efficient-Large-Model/Sana_1600M_4Kpx_BF16_diffusers")
image_4k = pipe_4k("a detailed landscape at 4k resolution").images[0]
```

```bash
# SGLang 服务
python -m sglang.launch_server --model-path Efficient-Large-Model/Sana_1600M_1024px_BF16
# OpenAI 兼容 API，curl 调用
curl -X POST http://localhost:30000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "a cat"}]}'
```

## 最新动向（2026-05）

**SANA-WM 发布**：2.6B 可控世界模型，支持 6-DoF 相机控制和 1 分钟 720p 视频，作为 Embodied AI 研究新基准。论文：arXiv:2605.15178

## 为什么值得关注

Sana 在"质量 vs. 效率"的取舍中明显偏向效率——1.6B 级别模型、8GB 显存约束、1 秒级出图，让高分辨率 AI 图像生成从 H100 普及到消费级 GPU。NVIDIA 持续更新（Sana-WM 刚发布），生态集成完善，是当前最实用的高分辨率生成方案之一。