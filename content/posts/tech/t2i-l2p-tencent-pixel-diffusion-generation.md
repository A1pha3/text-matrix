---
title: "L2P：不训 VAE、不采真实数据，8 张卡把 6B 潜在扩散模型搬进像素空间"
date: 2026-05-22T20:15:00+08:00
lastmod: 2026-09-15T00:00:00+08:00
slug: "t2i-l2p-tencent-pixel-space-diffusion-generation"
github_repo: "TencentYoutuResearch/T2I-L2P"
source_key: "gh:TencentYoutuResearch/T2I-L2P"
description: "L2P（Latent-to-Pixel）是腾讯优图实验室与南京大学开源的迁移范式：丢弃 VAE、改用大图块切分、冻结中层只训浅层，训练数据全部由源模型合成，8 张 GPU 就把 Z-Image 迁移成像素空间扩散模型。DPG-Bench 86.00 略超源模型，GenEval 保留 93.6%，原生支持 4K 生成。"
draft: false
categories: ["技术笔记"]
tags: ["文生图", "扩散模型", "计算机视觉"]
---

从零训练一个像素空间的扩散模型，账很难算平：没有 VAE 帮忙压缩，模型要直接消化原始像素；拟合自然图像分布需要海量真实数据；分辨率一高，显存开销更是失控。腾讯优图实验室与南京大学合作的 L2P（Latent-to-Pixel，潜在空间到像素空间的迁移范式）绕开了这笔账——不从零训练，而是把现成的潜在扩散模型（LDM，Latent Diffusion Model）整体搬进像素空间：transformer 骨干权重直接复用，丢弃 VAE 改用大图块切分，训练数据全部用源模型自己生成的合成图，8 张 GPU 就完成了 6B 模型的迁移训练。

论文口径的成绩：DPG-Bench 86.00 分，略高于源模型 Z-Image-Turbo 的 84.86；GenEval 保留源模型约 93.6% 的水平。代码、6B 权重、合成数据集、在线 demo 全部公开。本文依据 2026-09-15 的仓库与论文状态写成，命令与代码均照录 README 原文。

## 资产总览

| 资产 | 位置 | 状态 |
|------|------|------|
| 技术报告 | [arXiv:2605.12013](https://arxiv.org/abs/2605.12013)，2026-05-12 提交 | ✅ |
| 代码（推理 + 训练） | [TencentYoutuResearch/T2I-L2P](https://github.com/TencentYoutuResearch/T2I-L2P) | ✅ |
| 1K 分辨率权重（6B） | HuggingFace [zhen-nan/L2P](https://huggingface.co/zhen-nan/L2P)，单文件 19.57 GB | ✅ |
| 合成训练数据集 | HuggingFace [zhen-nan/L2P-dataset](https://huggingface.co/datasets/zhen-nan/L2P-dataset)，1 万–10 万张量级 | ✅ |
| 在线 demo | HF Space [z-image-6b-pixel-space](https://huggingface.co/spaces/multimodalart/z-image-6b-pixel-space) | ✅ |
| 4K/8K/10K 超高分辨率扩展 | [PixVerve-95K](https://github.com/HaojunChen663/PixVerve-95K) 仓库 `L2P-ZImage-HR` 目录 + HF [PixVerve-L2P](https://huggingface.co/HaojunChen/PixVerve-L2P) | ✅ 2026-07-11 发布 |

仓库 2026-05-22 创建，共 6 个 commit，最后一个停在 2026-07-11（UHR 发布），当前 193 star、15 fork。项目页托管在南京大学 PCALab 域名下，作者列表见论文引用条目。时间线本身就能说明这个项目的节奏：5 月 12 日发报告，5 月 22 日放代码、权重和数据，5 月 23 日上 demo，7 月 11 日补齐超高分辨率——每一步都兑现了。

## 迁移范式的三个关键取舍

主流文生图模型（SD3、FLUX、Sana、Z-Image 本身）都在潜在空间做扩散：VAE（variational autoencoder，变分自编码器）先把图像压成低维潜张量，transformer 在小得多的网格上去噪，最后由 VAE 解码回像素。L2P 想要像素空间端到端的能力，又不想付从零训练的代价，靠三个取舍把代价压下来。

**其一，丢弃 VAE，改用大图块 tokenization（large-patch tokenization）。** 代码里 `in_channels=3`，图像不经过任何压缩，直接按 16×16 的图块（patch）切分——一张 1024×1024 的图切出 64×64 共 4096 个 token，每个 token 携带 16×16×3 = 768 维原始 RGB，经线性层投到 3840 维。对比源模型的潜在路线（16 通道潜变量按 2×2 切块，输入维度 64），token 数量持平，计算量没有爆炸；差别在输入层要从头学，而中间 30 层 transformer 的知识全部保留。

**其二，冻结中层，只训浅层。** 论文摘要的原话是 "freezes the source LDM's intermediate layers, exclusively training shallow layers"。落到代码上分两步：离线转换脚本逐 key 对照源权重与像素模型结构，形状一致的参数（全部 transformer 块、时间步嵌入、文本适配层）原样拷贝，形状不一致的（输入层的 64 维变 768 维）和新增模块保留新初始化；训练脚本里文本编码器明确冻结（`requires_grad_(False)`），可训练范围由 `--trainable_models "dit"` 控制。

**其三，训练数据全部由源 LDM 合成。** 不采集任何真实图片，用 Z-Image 自己生成的图像做唯一训练语料。论文对此的解释是：要学的不是图像分布本身，而是"把 LDM 已经会的东西表达成像素"，合成数据恰好落在一个已经平滑的流形上，收敛快，且零数据采集成本。发布的数据集为 1 万–10 万张量级（HF 页面口径），训练脚本的示例数据路径名为 `L2P_20k_save_seed`。

这三条合起来的直接收益：迁移训练只需 8 张 GPU；VAE 一旦不在，它的显存瓶颈也随之消失，为后面的原生 4K 生成铺了路。

## 代码里长什么样

仓库是 [DiffSynth-Studio](https://github.com/modelscope/DiffSynth-Studio) 的裁剪版（致谢里注明），核心就三个文件，一个下午能读完。

**主干 `ZImageDiT`**：dim 3840、30 层 transformer 块、30 头，另有 2 层 noise refiner 与 2 层 context refiner 预处理图像 token 和文本 token。原版 DiT 末尾把 token 还原成图像的 `unpatchify` 输出层被注释掉了，换成了下面这个模块。

**解码头 `MicroDiffusionModel`**：一个 64→512 通道、四级下采样再四级上采样的小卷积 U-Net。它接收两路输入——DiT 输出的 64×64×3840 特征图，以及当前带噪图像——直接输出 RGB 预测。名字里 "local" 的含义即在于此：全图语义由 transformer 管，逐像素的细节由这个轻量卷积头补。

**管线 `ZImagePipeline`**：调度器是 `FlowMatchScheduler("Z-Image")`（流匹配），四个处理单元依次执行——ShapeChecker 把宽高对齐到 16 的倍数、PromptEmbedder 用 Z-Image-Turbo 的文本编码器（输出特征维度 2560）编码 prompt、NoiseInitializer 在像素域生成初始噪声、InputImageEmbedder 处理图生图输入。管线签名默认 8 步推理，README 示例用 30 步、cfg 2.0（cfg 指 classifier-free guidance，无分类器引导的强度参数）。

一次 1024×1024 文生图推理的完整数据流：

```text
prompt ──► 文本编码器 ──► 文本 token（维度 2560 经适配层升至 3840）
图像噪声 ──► 切成 64×64 个 16×16 图块 ──► 线性层升至 3840 维
       ↓
2 层 refiner 预处理 ──► 30 层 transformer 去噪（图像与文本 token 拼接，RoPE 位置编码）
       ↓
取回图像 token，重排为 64×64×3840 特征图
       ↓
MicroDiffusionModel(特征图, 带噪图像) ──► 像素域预测
       ↓
重复 8–30 步，输出 PIL 图像。全程无 VAE。
```

## 上手：推理与训练

系统要求以仓库实际声明为准：

| 组件 | 要求 | 出处 |
|------|------|------|
| Python | ≥ 3.10 | `pyproject.toml` 的 `requires-python` |
| PyTorch | ≥ 2.0.0 | `pyproject.toml` 依赖声明 |
| GPU（训练） | 单卡 ≥ 24 GB 走标准脚本；不足 24 GB 走低显存脚本 | README 与训练脚本 |
| GPU（推理） | 官方未给数字；仅权重单文件就有 19.57 GB，加载后另需文本编码器与激活值显存 | HuggingFace |

安装：

```bash
git clone https://github.com/TencentYoutuResearch/T2I-L2P.git
cd T2I-L2P
pip install -e .
```

推理。先从 HF 下载 [zhen-nan/L2P](https://huggingface.co/zhen-nan/L2P) 的权重和 [Tongyi-MAI/Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo) 的文本编码器与 tokenizer，然后照抄 README 示例：

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

想先看效果不想装环境，直接用 [HF Space 在线 demo](https://huggingface.co/spaces/multimodalart/z-image-6b-pixel-space)。想自己起服务，仓库的 `app.py` 是一个多卡 Gradio 服务：通过 `nvidia-smi` 检测空闲 GPU（已用显存低于 100 MB 视为空闲），一卡加载一条管线，请求自动分发到空闲卡，界面开在 `http://0.0.0.0:23231`。

```bash
pip install gradio
python app.py
```

训练分四步，每一步在做什么值得说清楚：

**第一步，准备 Z-Image 基座权重。** 下载官方 Z-Image-Turbo checkpoint（🤗 [Tongyi-MAI/Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)）。

**第二步，离线权重转换（latent → pixel init）。** 把潜在空间的 DiT 权重转换成像素空间初始化：形状一致的参数拷贝源值，输入层和新增的解码头保留初始化——这一步就是"骨干复用"的落点。

```bash
python examples/z_image/L2P_convert_weight.py \
  --latent_ckpt_files \
    /path/to/Z-Image-Turbo/transformer/diffusion_pytorch_model-00001-of-00003.safetensors \
    /path/to/Z-Image-Turbo/transformer/diffusion_pytorch_model-00002-of-00003.safetensors \
    /path/to/Z-Image-Turbo/transformer/diffusion_pytorch_model-00003-of-00003.safetensors \
  --output_path ./pretrain_weight/Z-Image-Pixel-Init/diffusion_pytorch_model.safetensors
```

**第三步，启动训练。** 流匹配 SFT（supervised fine-tuning，监督微调）：合成图像在像素域加噪，模型预测，按流匹配损失回传。文本编码器冻结，`trainable_models` 设为 `dit`，学习率 5e-5，每 5000 步存档，`max_pixels 1048576` 即 1024² 上限。

```bash
bash train_run.sh
```

单卡显存不足 24 GB 时用低显存变体：文本编码器 offload 到 CPU，配合 `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`，README 原话是 "Recommended for 24GB cards"。

```bash
bash train_run_low_VRAM.sh
```

数据集就是图片目录加一个 CSV：

```text
data/
├── images/                # raw image folder
└── metadata.csv           # columns: file_name, text, ...
```

**第四步，离线权重合并。** 训练产物与第二步的像素初始化按 key 合并成单文件，供推理使用：

```bash
python merge_weights.py \
  --file_a ./models/train/L2P_Standard/step-xxx.safetensors \
  --file_b ./pretrain_weight/Z-Image-Pixel-Init/diffusion_pytorch_model.safetensors \
  --file_out ./models/train/L2P_Standard/model-merge.safetensors
```

## benchmark 数字怎么读

论文在 1024×1024 分辨率下报了两组数，各管一件事。

**DPG-Bench**（Hu et al., 2024）考 dense prompt 的细粒度语义跟随，百分制。L2P 拿到 86.00（子项：Global 92.02、Entity 90.84、Attribute 89.48、Relation 93.00、Other 91.55），源模型 Z-Image-Turbo 是 84.86——迁移之后不降反微升。

**GenEval**（Ghosh et al., 2023）考可程序判定的指令项（对象、计数、颜色、位置等），Overall 0–1 分制。L2P 拿到 0.76，论文原话是保留源模型约 93.6% 的水平——摘要里 "93% performance" 指的就是这个保留率，不是绝对分。

在像素系文生图的同行里，这两个数字都是最好的：对比表中的 PixelDiT 为 DPG-Bench 83.50、GenEval 0.74。论文据此称 L2P 在像素系模型中创下 DPG-Bench 的新纪录。

三件事需要分清。这组数字反映的是**语义跟随能力在迁移中有没有丢**——答案是基本没丢；它**不反映美学质量**——出图好不好看、文字渲染稳不稳，GenEval 和 DPG-Bench 都不管；它也**不能外推到别的骨干**——论文虽声称配方在多款主流 LDM 上验证过，但公开表格只列了 Z-Image 这一条线，换骨干要自己重跑。

## 4K/8K/10K：超高分辨率已经发布

本文初版写作时（2026-05）路线图里 UHR 一栏还是"开发中"，这个状态已经过时：2026-07-11，4K/8K/10K 的训练与推理代码、权重、数据集一并放出，落在 [PixVerve-95K](https://github.com/HaojunChen663/PixVerve-95K) 仓库的 `L2P-ZImage-HR` 目录。

机制上，换分辨率只动两处：图块大小（4K 用 64、8K 用 128、10K 用 160）和分辨率感知的 U-Net 解码器（10K 版在瓶颈处把 64×64 特征图上采样到 160×160，并逐级开梯度检查点）；transformer 部分的特征图恒为 64×64，骨干不动。加载时按 checkpoint 的 key/shape 签名自动选结构，不需要手动指定分辨率。权重在 HF [HaojunChen/PixVerve-L2P](https://huggingface.co/HaojunChen/PixVerve-L2P)，训练与 UHR 推理官方建议 8 卡。论文还提到 4K 合成训练数据由模型原生自产，不再依赖外部分辨率放大。

这批工作同时对应 PixVerve 论文（向 100MP 原生超高分辨率生成推进）。顺带理一下脉络：同一一作团队 2025 年 11 月的 [DiP](https://arxiv.org/abs/2511.18822)（Taming Diffusion Models in Pixel Space）在做像素空间扩散的从头训练，2026 年 5 月的 L2P 把问题改写成"迁移"，两个月后 PixVerve 把分辨率推到 10K——大半年三级跳，这是一条持续迭代的研究线，不是一次性的论文配套开源。

## 许可证：一个真实的坑

仓库根目录没有 LICENSE 文件，GitHub 因此不显示任何许可证；`pyproject.toml` 里声明的却是 Apache-2.0；HF 上的[权重页](https://huggingface.co/zhen-nan/L2P)和[数据集页](https://huggingface.co/datasets/zhen-nan/L2P-dataset)也都标着 Apache-2.0。三处对不上，实际采用前建议在仓库开 issue 向作者确认一次，再决定是否引入商业项目。这一步花不了十分钟，能省掉后面所有关于授权的扯皮。

## 适用边界与采用顺序

**适合**：

- 研究像素空间生成，或想复现"骨干复用 + 冻结中层 + 纯合成数据"这套迁移配方——代码体量小，结构清楚；
- 手上有 Z-Image 系骨干，想要一个无 VAE、像素域直出的变体；
- 需要 4K+ 原生分辨率、又被 VAE 显存卡住的场景——直接用 UHR 版。

**不适合**：

- 想要开箱即用的生产文生图——没有 ControlNet、社区 LoRA、ComfyUI 节点这些生态，出图质量的目标也是"与源 LDM 相当"而非超越；
- 对授权有硬性要求的商业产品——先把上一节的许可证问题解决；
- 指望它比 Z-Image-Turbo 出图更漂亮——这不是这个项目回答的问题。

采用顺序建议：先花五分钟在 HF Space 上看出图效果；觉得有价值，再下载 19.57 GB 权重本地跑通 README 示例；确实要做研究或微调，才进四步训练流程。

## 结尾判断

L2P 最有价值的不是 GenEval 0.76 这个分数，而是它验证了一条降低入场门槛的路径：像素空间扩散不必从零训练，骨干可以白拿，数据可以自产，8 张卡够用，VAE 的分辨率瓶颈顺手一起解决。对研究者是可复现的迁移配方，对算力有限的团队是能照抄的工程路线。1K 主线的路线图还剩一项没勾——兼容更多 LDM 模型；把这套配方套到 FLUX、SD3 等别的骨干上，是目前最值得期待的后续。

## 关键资源

- 仓库：[TencentYoutuResearch/T2I-L2P](https://github.com/TencentYoutuResearch/T2I-L2P)（含推理、训练、Gradio demo）
- 论文：[arXiv:2605.12013](https://arxiv.org/abs/2605.12013)《L2P: Unlocking Latent Potential for Pixel Generation》
- 项目页：[nju-pcalab.github.io/projects/L2P](https://nju-pcalab.github.io/projects/L2P/)
- 1K 权重：[zhen-nan/L2P](https://huggingface.co/zhen-nan/L2P)；数据集：[zhen-nan/L2P-dataset](https://huggingface.co/datasets/zhen-nan/L2P-dataset)
- 在线 demo：[HF Space z-image-6b-pixel-space](https://huggingface.co/spaces/multimodalart/z-image-6b-pixel-space)
- 超高分辨率扩展：[L2P-ZImage-HR](https://github.com/HaojunChen663/PixVerve-95K/tree/main/L2P-ZImage-HR)（代码）、[HaojunChen/PixVerve-L2P](https://huggingface.co/HaojunChen/PixVerve-L2P)（权重）
- 前作：[DiP: Taming Diffusion Models in Pixel Space](https://arxiv.org/abs/2511.18822)（arXiv:2511.18822）
- 基座模型：[Tongyi-MAI/Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)；代码基于 [DiffSynth-Studio](https://github.com/modelscope/DiffSynth-Studio) 裁剪
