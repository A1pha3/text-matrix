---
title: "LongLive 2.0：给长视频生成补上 NVFP4 并行基础设施"
date: "2026-05-23T20:17:28+08:00"
lastmod: 2026-09-30T20:00:00+08:00
slug: "nvlabs-longlive-2-nvfp4-long-video-generation"
github_repo: "NVlabs/LongLive"
source_key: "gh:NVlabs/LongLive"
description: "LongLive 2.0 是 NVlabs 开源的长视频生成基础设施：Balanced 序列并行 + NVFP4 量化贯穿训练与推理，NVFP4-2Step 模型推理 45.7 FPS，论文实测训练最高提速 2.15 倍、推理 1.84 倍。本文拆解其并行训练、量化推理、多 shot 一致性机制与部署边界。"
draft: false
categories: ["技术笔记"]
tags: ["视频生成", "推理优化", "NVFP4", "量化"]
---

# LongLive 2.0：给长视频生成补上 NVFP4 并行基础设施

长视频生成走到 2026 年，瓶颈已经不在"能不能生成"，而在训练和推理的基础设施：序列一长，KV cache 和激活值就把显存吃穿，精度一压，质量又肉眼可见地下滑。NVlabs 在 2026 年 5 月 13 日发布的 LongLive 2.0（仓库 [`NVlabs/LongLive`](https://github.com/NVlabs/LongLive) 的 `LongLive2.0/` 目录）针对的正是这一层——用 Balanced 序列并行解决训练侧的显存与通信，用 NVFP4 量化把推理侧的权重和 KV cache 都压到 4 位。论文口径：这是第一个覆盖训练与推理全流程的 NVFP4 长视频生成系统，训练最高提速 2.15 倍，推理提速 1.84 倍；NVFP4 两步蒸馏模型推理 45.7 FPS。

它不是 LongLive 1.0 的简单升级。1.0 是拿 1.3B 模型做实时交互生成（ICLR 2026 论文），2.0 换成 5B 基座，重心从"交互式出片"转向"把长视频训练和部署做成一套能扛负载的工程栈"。读这篇之前值得先分清：仓库里现在住着三代工作，本文谈的是中间那一代。

> 本文数据按仓库 main 分支（2026-09-29 推送）与 arXiv:2605.18739 核实于 2026-09-30；Stars/Forks 为当日 GitHub API 读数。仓库无正式 release，安装与配置以 main 分支文档为准。

## 快速信息卡

| 项目 | 信息 |
|------|------|
| **仓库** | [NVlabs/LongLive](https://github.com/NVlabs/LongLive)（2.0 代码在 `LongLive2.0/` 子目录） |
| **Stars / Forks** | 2,644 / 259（2026-09-30） |
| **License** | Apache-2.0 |
| **语言** | Python |
| **基座模型** | Wan2.2-TI2V-5B（致谢 Wan-Video；AR 训练代码基于 Self-Forcing） |
| **2.0 论文** | [arXiv:2605.18739](https://arxiv.org/abs/2605.18739)（2026-05-18 提交，预印本） |
| **最后推送** | 2026-09-29 |

## 三代 LongLive：先分清在谈哪一个

这个仓库现在是三代工作的合集，每个目录自带代码、文档和权重：

| 目录 | 是什么 | 状态 |
|------|--------|------|
| `LongLive1.0/` | 实时交互式长视频生成，1.3B 模型，单 H100 20.7 FPS、最长 240 秒 | ICLR 2026 接收（[arXiv:2509.22622](https://arxiv.org/abs/2509.22622)） |
| `LongLive2.0/` | NVFP4 并行训练与推理基础设施，5B 模型 | arXiv 预印本，2026-05-13 发代码 |
| `LongLive-Plug/` | 一次蒸馏、多下游复用的插件化方案 | 2026-09-28 发布训练与推理代码 |

三代共享的机制值得留意：1.0 论文提出的三个关键设计——KV-recache（切换提示词时刷新缓存状态）、streaming long tuning（训练与推理都对齐长视频，train-long-test-long）、短窗口注意力配帧级注意力锚点（frame-level attention sink，官方简称 frame sink）——构成了后面 2.0 多 shot 机制的地基。ICLR 2026 接收的是 1.0；2.0 与 1.0 的接收无关，目前是预印本。

## 核心机制：三条主线

2.0 的技术面容易混在一起看，拆开其实是三条独立的线：训练并行、量化推理、多 shot 一致性。前两条解决速度与显存，第三条解决长视频的内容连贯。

### Balanced SP：把 teacher-forcing 配平到每张卡

自回归视频训练要用 teacher-forcing：每一步都拿干净的历史帧做条件、预测带噪的目标帧。朴素的做法是各卡各管一段序列，但干净输入和噪声目标的计算量不对称，负载不均。

2.0 论文给的答案是 Balanced SP（序列并行）：把"干净历史块"和"噪声目标块"**成对地**放到同一个 rank 上。这样每张卡的计算量天然平衡，teacher-forcing 的掩码不用额外通信就能构造，VAE 编码也按块加 halo（chunk-halo）完成，与并行切分对齐。配置层面，`infra.sequence_parallel_size` 控制 SP 组大小，`infra.vae_halo_latents` 控制 halo 预算。这套并行同时服务 T2V 和 I2V 两条训练路径。

需要划清的边界是：Balanced SP 是**训练侧**的方案。推理侧另有 SP 路径（Ulysses 序列并行，`inference_sp.py`，进程数等于 `sp_size × dp_size`），两者不是一回事。

### NVFP4：一条从训练贯穿到 KV cache 的量化线

NVFP4 是 NVIDIA 定义的 4 位浮点格式，带硬件 Tensor Core 支持——但支持它的硬件是 Blackwell（B200/GB200/GB300），官方文档构建 NVFP4 扩展时明确要求 `CUDA_ARCHS=100`。这是部署前最需要确认的一条边界。

2.0 把 NVFP4 用在了三处：

1. **训练**：`infra.model_quant` 开启生成器 NVFP4 训练；DMD 蒸馏阶段还可分别指定 `infra.generator_quant`、`infra.real_score_quant`、`infra.fake_score_quant`，选择哪几个网络吃量化。官方 NVFP4 训练示例用 4 卡。
2. **权重推理（W4A4）**：checkpoint 有两种后端——`model_te.pt`（TransformerEngine 运行时量化，加载的是合并后的 BF16 权重）和 `model_4o6.pt`（FourOverSix 预物化的紧凑量化权重）。两种后端靠 `model_quant_use_transformer_engine` 开关区分，且不可混用：4o6 checkpoint 存的是 `quantized_weight_*` 缓冲，只能走 FourOverSix 路径加载。
3. **KV cache**：`inference.kv_quant` 开启 FP4 KV cache 存储，配合融合反量化扩展。视频序列一长，KV cache 往往比权重更占显存，这一项的收益随视频变长而放大。

工程上的对应代价是**两套环境**：BF16 环境用 Python 3.10 + PyTorch 2.8.0（cu128）；NVFP4 环境单独建，Python 3.12 + PyTorch 2.10.0 + CUDA Toolkit 12.8 + FlashAttention 2.8.3 源码编译，再本地构建 `fouroversix` 包和 `utils/kernel` 扩展。版本敏感，官方明确建议不要混在一个环境里。

不在 Blackwell 上怎么办？两条现成的路：**FP8 PTQ 推理**（2026-07 加入）从 BF16 checkpoint 出发，用 TorchAO 做逐行动态 W8A8 量化——5B 模型里 300 个核心线性层转 FP8、6 个小的条件/输出投影留在 BF16 保稳定；验证栈是 H100（SM90），要求算力 8.9 以上。**SP 推理**则是论文给出的非 Blackwell 方案：不开量化，用序列并行把速度拉到与 Blackwell 接近的水平，量化后的 KV cache 还能降低 SP 的卡间通信量。

2026-05-25 官方还优化过一轮 NVFP4 推理路径——融合 Triton RoPE/adaLN 核、降低 KV cache 同步开销、原地量化更新、更快的 FP4 反量化——整体吞吐提升 18.6%。这类数字说明推理路径仍在快速迭代，部署前值得看一眼最新 changelog。

### 多 shot 一致性：从 frame sink 到 multi_shot_sink

多段视频（multi-shot）生成的老问题是段与段之间风格断裂。1.0 的解法是 frame sink：把序列开头的若干帧固定为注意力锚点，永不淘汰，后续内容都"看得见"它们，长程一致性由此维持。2.0 沿用并扩展了这套机制，推理配置里对应三个开关：

- `inference.sink_size`：标准 attention sink 的长度（锚点帧数）；
- `inference.multi_shot_sink`：启用多 shot attention sink；
- `inference.multi_shot_rope_offset`：多 shot 场景下的 RoPE 位置偏移。

段与段的衔接还有一个容易被忽略的细节：shot 边界处，管线会自动给新 shot 的第一个 chunk 前置 `scene_cut_prefix`，等于明确告诉模型"这里换镜头了"，而不是指望模型自己从 prompt 变化里猜出来。

### 两阶段训练：AR teacher-forcing 先行，DMD 蒸馏收尾

T2V 和 I2V 共用同一套两阶段配方：

1. **AR 扩散训练**（`configs/train_ar.yaml` / `train_i2v_ar.yaml`）：块级自回归，teacher-forcing，训练完得到一个长视频 AR 扩散模型。论文强调这一步是"直接把扩散模型调成长视频、多 shot、交互式的 AR 模型"，不走 Self-Forcing 系列的 ODE 初始化路线。
2. **DMD 蒸馏**（`configs/train_dmd.yaml` / `train_i2v_dmd.yaml`）：以 AR checkpoint 初始化学生，蒸馏成少步生成器。蒸馏全程开 AR 掩码（`algorithm.all_causal: true`）。

DMD 有两种 LoRA 设置，产出都能用于推理但初始化路径不同：**Direct DMD** 的学生/评论家/教师都从 stage-1 AR 模型初始化；**Standalone LoRA injection** 三者都回到 Wan2.2-TI2V-5B 基座，练出的 LoRA 权重可独立携带——推理时 4 步去噪的模型靠这份 LoRA 进一步压到 2 步，45.7 FPS 的 NVFP4-2Step 就是这么来的。官方文档特别提醒两种设置的视觉效果可能有差异，选型时按自己的基座和部署形态试。

I2V 路径还有个反直觉的配置细节：`data.image_or_video_shape[1]` 填的是**完整生成 latent 序列长度**（如 96），不是 96+1——首帧的干净 latent 在去噪时替换第一个位置，且被排除在损失之外（含 SP 训练的 rank-0）。填 97 是官方 Troubleshooting 里点名的高频错误。

## 快速开始

所有命令以 `LongLive2.0/` 为工作目录。克隆时只取 main 分支即可——demo page 分支带大体积资源：

```bash
git clone --single-branch --branch main --depth 1 https://github.com/NVlabs/LongLive.git
cd LongLive/LongLive2.0
```

环境按上一节的"两套环境"搭建（BF16：Python 3.10 + torch 2.8.0；NVFP4：Python 3.12 + torch 2.10.0 + CUDA 12.8 + FA 2.8.3 源码编译），另需从 Hugging Face 下载基座组件：

```bash
huggingface-cli download Wan-AI/Wan2.2-TI2V-5B \
  --local-dir wan_models/Wan2.2-TI2V-5B
```

权重仓库在 `Efficient-Large-Model/` 组织下：[LongLive-2.0-5B](https://huggingface.co/Efficient-Large-Model/LongLive-2.0-5B)（BF16 权重 `model_bf16.pt`）、[NVFP4-S4](https://huggingface.co/Efficient-Large-Model/LongLive-2.0-5B-NVFP4-S4) 与 [NVFP4-S2](https://huggingface.co/Efficient-Large-Model/LongLive-2.0-5B-NVFP4-S2)（各含 `model_te.pt` 与 `model_4o6.pt` 两份量化 checkpoint）。

### BF16 推理（官方 Quick Start 原样）

```python
import torch
from omegaconf import OmegaConf

from pipeline import CausalDiffusionInferencePipeline
from utils.config import normalize_config
from utils.inference_utils import (
    load_generator_checkpoint,
    place_vae_for_streaming,
    prepare_single_prompt_inputs,
    save_video,
)

prompt = "A compact silver robot walks through a clean robotics lab."
merged_checkpoint_path = "LongLive-2.0-5B/model_bf16.pt"

config = normalize_config(OmegaConf.load("configs/inference.yaml"))
device = torch.device("cuda")

torch.set_grad_enabled(False)
pipe = CausalDiffusionInferencePipeline(config, device=device)
load_generator_checkpoint(pipe.generator, merged_checkpoint_path)
pipe = pipe.to(device=device, dtype=torch.bfloat16)
place_vae_for_streaming(pipe, config)  # streaming_vae 开启时才生效
pipe.generator.model.eval().requires_grad_(False)

noise, prompts = prepare_single_prompt_inputs(config, prompt, device)
video = pipe.inference(noise=noise, text_prompts=prompts)
save_video(video[0], "videos/quickstart/sample.mp4", fps=24)
```

三处细节值得注意：入口是 `pipe.inference`，输入是 `prepare_single_prompt_inputs` 备好的 noise 与 prompts，而不是一个 prompt 字符串；输出视频帧率由 `save_video` 的 `fps=24` 指定；`place_vae_for_streaming` 只有在 yaml 里开了 `inference.streaming_vae` 才起作用。

### NVFP4 推理

```python
import torch
from omegaconf import OmegaConf

from pipeline import CausalDiffusionInferencePipeline
from utils.config import normalize_config
from utils.inference_utils import prepare_single_prompt_inputs, save_video, setup_nvfp4_pipeline

prompt = "A compact silver robot walks through a clean robotics lab."

config = normalize_config(OmegaConf.load("configs/nvfp4/inference_nvfp4.yaml"))
device = torch.device("cuda")

torch.set_grad_enabled(False)
pipe = CausalDiffusionInferencePipeline(config, device=device)
setup_nvfp4_pipeline(pipe, config, device)
pipe.generator.model.eval().requires_grad_(False)

noise, prompts = prepare_single_prompt_inputs(config, prompt, device)
video = pipe.inference(noise=noise, text_prompts=prompts)
save_video(video[0], "videos/quickstart/sample_nvfp4.mp4", fps=24)
```

加载必须走 `setup_nvfp4_pipeline`——官方文档原话警告：BF16 那套 `pipe.to(...)` 的快捷方式在这里**不安全**，因为它会把量化缓冲一起转型（cast）。checkpoint 指到下载的 `model_te.pt` 或 `model_4o6.pt`，并让 `model_quant_use_transformer_engine` 与之匹配。

### 训练

```bash
# Stage 1：AR teacher-forcing（8 卡示例）
torchrun --standalone --nnodes=1 --nproc_per_node=8 train.py \
  --config_path configs/train_ar.yaml \
  --logdir logs/train_ar \
  --wandb-save-dir wandb \
  --disable-wandb

# Stage 2：DMD 蒸馏
torchrun --standalone --nnodes=1 --nproc_per_node=8 train.py \
  --config_path configs/train_dmd.yaml \
  --logdir logs/train_dmd \
  --wandb-save-dir wandb \
  --disable-wandb
```

I2V 换成 `train_i2v_ar.yaml` / `train_i2v_dmd.yaml`，NVFP4 训练用 `configs/nvfp4/` 下对应配置（示例 4 卡）。训练前要先把配置里的 `/path/to/...` 占位符换成真实数据集、prompt 和 checkpoint 路径——占位符不换，启动即失败，这也是官方 Troubleshooting 的第一条。

训练数据是 `video/` 与 `caption/` 成对的目录结构，每段视频配一个同名的 JSON caption 文件（必填 `caption` 字段）；长视频可用 `max_chunks_per_shot` 拆成虚拟 shot。[官方文档的 Training Data 一节](https://nvlabs.github.io/LongLive/LongLive2/docs/#training-data)提供了一个专门用来核对数据格式的 toy dataset。多 shot 推理的 prompt 则按"每 case 一个文件夹 + 编号 JSON + `shot_durations.txt`"组织，每个 shot 的 caption 官方建议约 300 token、按六段式写（风格、场景、人物、物件、动作、镜头）。

## 一次多 shot 生成的完整流转

把上面的机制串成一个具体任务：生成"机器人在实验室走动，镜头切到特写，再切回全景"的三段视频。

1. **准备 prompt 目录**：`prompts/robot_demo/` 下放 `0.json`、`1.json`、`2.json`（三段 caption），`shot_durations.txt` 写 `40 10 20`——三段各占多少个时间块。加载器按文件名顺序读 shot；如果目录里有 `caption/` 外层，它也能识别。
2. **配置推理**：`configs/inference.yaml` 里 `checkpoints.generator_ckpt` 指向合并后的 checkpoint（或 AR base + `lora_ckpt`），开 `inference.multi_shot_sink`，按需调 `sink_size`。
3. **生成**：管线按 shot 顺序做块级 AR 生成。跨过 shot 边界时自动前置 `scene_cut_prefix`；sink 帧始终在注意力窗口里锚定风格与主体；`multi_shot_rope_offset` 管住跨段的位置编码不串味。
4. **解码落盘**：默认一次性解码；若开了 `streaming_vae`，latent 按块边生成边解码，`async_vae` 再把解码叠到生成的 CUDA 流上——追求吞吐时可把 VAE 挪到独立 GPU（`vae_device`）。最终 `save_video` 以 24 fps 写出成片。

这条链路上任何一环出错都有对应的排查入口，见文末。

## 性能数字怎么读

官方模型表（README，2026-09-30 读数）：

| 模型 | FPS ↑ | 参数量 | VBench ↑ | 多 shot |
|------|------:|------:|------:|:-----:|
| [LongLive-1.3B](https://huggingface.co/Efficient-Large-Model/LongLive-1.3B) | 20.7 | 1.3B | 84.87 | — |
| [LongLive-2.0-5B](https://huggingface.co/Efficient-Large-Model/LongLive-2.0-5B)（BF16） | 24.8 | 5B | 85.06 | ✅ |
| [LongLive-2.0-5B-NVFP4-4Step](https://huggingface.co/Efficient-Large-Model/LongLive-2.0-5B-NVFP4-S4) | 29.7 | 5B | 84.51 | ✅ |
| [LongLive-2.0-5B-NVFP4-2Step](https://huggingface.co/Efficient-Large-Model/LongLive-2.0-5B-NVFP4-S2) | **45.7** | 5B | 83.14 | ✅ |

读这张表先问三个问题。

**测的是什么？** FPS 是端到端推理吞吐，VBench 是视频生成质量的综合评分。45.7 FPS 属于 NVFP4 **两步蒸馏**变体（S2），不是"NVFP4 推理"的通用成绩——四步版是 29.7 FPS，BF16 基线 24.8 FPS。论文层面的加速口径是：训练最高 2.15 倍、推理 1.84 倍。

**数字变化反映什么？** 表格前两列的落差几乎全部来自蒸馏步数：4 步到 2 步，去噪计算减半，FPS 从 29.7 涨到 45.7；NVFP4 量化则在同等步数下比 BF16 更快（4 步 29.7 对 5B BF16 的 24.8）。代价在同一张表的 VBench 列里：85.06 → 84.51 → 83.14，步数越激进、量化越深，质量分单调下滑。官方没有隐藏这个 trade-off，选型时本质是在速度-质量曲线上挑点。

**不能推出什么？** 官方表格没有给出测速硬件与显存读数，任何"单卡显存占用 X GB"的推算都不是官方口径；FPS 也不能直接换算成"多少秒能生成多长的视频"——它取决于去噪步数、块大小与硬件。另外 45.7 FPS 这一数字出自发布日（2026-05-13）的 News 与论文摘要，其后推理路径还有 18.6% 的吞吐优化，复现时以当前代码为准。

## TriAttention：KV cache 压缩的外挂

2026 年 4 月 12 日起，LongLive 支持用 [TriAttention](https://github.com/WeianMao/triattention/tree/main/longlive)（三角函数频域 KV 压缩，[arXiv:2604.04921](https://arxiv.org/abs/2604.04921)）压缩 KV cache，官方口径是 50% KV 削减、质量无明显下降。这不是随便找的第三方项目——TriAttention 一作 Weian Mao 同样在 LongLive 2.0 论文作者列表里，两个项目出自同一团队，后来 TriAttention 还被官方集成进了 NVIDIA TensorRT-LLM 的 KV 压缩方法列表。

集成方式与直觉不同：它用 monkey-patch 把三角函数 KV 评分注入 LongLive 的因果推理管线，**叠加在** LongLive 的局部注意力窗口之上——压缩器决定窗口内哪些 token 保留，不改上游模型代码。核心配置都在 YAML 的 `model_kwargs` 里：`local_attn_size`（局部窗口帧数，默认 12，必须大于 0）、`kv_compression_mode: compress`、`kv_budget_tokens`（压缩后保留的 token 数，须严格小于窗口总量）、`sink_size`（锚点帧数，默认 3，永不驱逐）。以随仓库配置为例，窗口 12 × 1560 = 18,720 token，预算 9,360 正好保留一半。

注意适用对象：这套集成跑在 LongLive 1.0 的 1.3B 管线（Wan2.1-T2V-1.3B 基座）上，有自己的 `run_interactive` / `run` 两个入口，与 2.0 的 5B 管线是两条路径。想在 2.0 上省 KV 显存，官方自己的 `inference.kv_quant`（NVFP4 KV cache）才是同管线的选项。

## 生态与现状

README 的 "Awesome work using LongLive" 已经排了十几项后续工作，方向相当发散：KlingAI 研究院的 [MemFlow](https://github.com/KlingAIResearch/MemFlow)（加自适应记忆检索做长叙事）和 [ShotStream](https://github.com/KlingAIResearch/ShotStream)（沿用蒸馏流程做实时多 shot）；SANA-Video 与 LongLive 结合出的 LongSANA（常数显存 KV cache 的分钟级实时生成）；Daydream Scope 把 LongLive 包装成交互式流水线；KVPO 在其上做 GRPO 式对齐。一个基础设施项目能同时被世界模型、视频编辑、RL 对齐采纳，说明"块级 AR + 实时"这条路线本身的通用性。

仓库现状两点提醒：**没有正式 release**（releases 页为空，代码直接在 main 上演进，配置与 API 变动以官方文档为准）；2.0 论文目前是预印本。项目推进很活跃——2026 年 9 月 28 日刚发布第三代 LongLive-Plug（一次蒸馏、跨下游复用），同月主仓库仍在推送。

## 采用建议

按硬件和目标分三种情形：

- **有 Blackwell（B200/GB200/GB300）且要训自己的长视频模型**：这是 2.0 的主场——NVFP4 训练加 Balanced SP，加上官方 NVFP4 环境的搭建成本，值得。从 toy dataset 核对数据格式开始。
- **H100/Ada 及以上，只要推理**：走 FP8 PTQ（算力 8.9+）或 BF16；对吞吐有更高要求再考虑 SP 推理。不必为 NVFP4 强上 Blackwell——论文明确说非 Blackwell 用 SP 推理补速度。
- **要实时交互生成（边输入 prompt 边出片）**：1.0 管线才是对口的工具，2.0 的重心是吞吐而非交互；跨下游模型复用蒸馏能力则看 9 月新出的 LongLive-Plug。

共性前提要摆在明面上：两套环境、配置占位符、NVFP4 本地扩展编译，这些工程成本都不小；数据侧 caption 质量直接影响多 shot 一致性，官方那套六段式 caption 规范值得照抄。

## 故障排查

官方文档 Troubleshooting 节的五条，均为高频项：

1. **配置占位符**：训练或推理启动即失败，先查 `configs/` 里 `/path/to/...` 是否全部替换为本地路径。
2. **GPU 数量**：`--nproc_per_node` 要与实际卡数一致，且与 AR 训练的 `infra.sequence_parallel_size` 兼容；SP 推理的进程数须等于 `sp_size × dp_size`。
3. **I2V 帧数**：`data.image_or_video_shape[1]` 填生成 latent 总长（如 96），不要加上下文帧写成 97。
4. **FlashAttention 编译失败**：先核对 CUDA、PyTorch 与编译器版本匹配；NVFP4 环境要求从源码构建 v2.8.3。
5. **NVFP4 内核缺失**：开启 `inference.kv_quant` 前，确认 `fouroversix` 包与 `utils/kernel` 扩展都已构建。

## 延伸阅读

- 官方文档（安装/训练/推理全流程）：https://nvlabs.github.io/LongLive/LongLive2/docs/
- 2.0 论文（arXiv:2605.18739）：https://arxiv.org/abs/2605.18739
- 1.0 论文（arXiv:2509.22622，ICLR 2026）：https://arxiv.org/abs/2509.22622
- BF16 / NVFP4 / S2 / S4 权重：[Efficient-Large-Model 组织](https://huggingface.co/Efficient-Large-Model)（2.0 系列 2026-05-19 上传）
- TriAttention 及 LongLive 集成：https://github.com/WeianMao/triattention/tree/main/longlive
- 基座模型：https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B
