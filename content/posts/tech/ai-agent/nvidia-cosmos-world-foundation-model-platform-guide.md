---
title: "NVIDIA Cosmos 3 实战指南：把世界模型、机器人策略和自动驾驶拉到同一根 Transformer 线上"
date: "2026-06-04T23:00:00+08:00"
lastmod: "2026-09-22T10:00:00+08:00"
slug: "nvidia-cosmos-world-foundation-model-platform-guide"
github_repo: "NVIDIA/cosmos"
source_key: "gh:NVIDIA/cosmos"
aliases:
  - /posts/tech/nvidia-cosmos-world-foundation-model-platform-guide/
description: "NVIDIA Cosmos 是 NVIDIA 的开源世界模型平台（约 11.9K stars），Cosmos 3 用统一 MoT 架构联合处理与生成语言、图像、视频、音频和动作序列，提供 Super 64B / Nano 16B / Edge 4B 三档规格，覆盖机器人、自动驾驶、智慧城市等 Physical AI 场景。"
draft: false
categories: ["技术笔记"]
tags: ["NVIDIA", "世界模型", "Physical AI", "VLM", "机器人"]
---

# NVIDIA Cosmos 3 实战指南：把世界模型、机器人策略和自动驾驶拉到同一根 Transformer 线上

## 核心判断

`NVIDIA Cosmos`（仓库 [NVIDIA/cosmos](https://github.com/NVIDIA/cosmos)，约 11.9K stars，2026-09-22 读数）回答了一个被 VLM 和 Sora 类项目绕开的问题：**「让 AI 理解并预测真实物理世界」这件事，到底是扩散模型做、还是自回归模型做、还是一个统一架构做？**

Cosmos 3（2026-05-31 发布）给出的答案是统一架构。它把 **理解（Reasoner）** 与 **生成（Generator）** 两条路径装进同一个 **Mixture-of-Transformers（MoT）checkpoint**：自回归 Transformer 负责推理，扩散 Transformer 负责多模态生成，两种模式共享同一套多模态注意力层和统一的 3D mRoPE 位置编码——把空间与时间结构编进同一套位置表征，图像、视频、音频流和动作轨迹因此在同一个坐标系里对齐。官方的定位说得更直白：它把视觉语言模型、视频生成器、世界模拟器、世界动作模型收进了一个框架。

它跟别的视频生成项目拉开距离的，是三件凑齐了的事：

1. **三档规格 + 六个专用 checkpoint**：Super 64B / Nano 16B / Edge 4B，从数据中心到 Jetson 边缘设备；文生图、图生视频、4 步蒸馏加速版、DROID 机器人策略各有专用权重
2. **动作是一等公民**：策略动作、正逆动力学、相机运动、第一人称运动都是可输入可输出的模态，相机 9D、自驾 9D、第一人称 57D、单臂 10D、双臂 20D、人形 29D 各有维度约定
3. **六条推理路径全部给出可跑配方**：Diffusers 和 Transformers 做研究，vLLM-Omni、SGLang 做生成服务，vLLM、TensorRT-LLM 做理解服务，NIM 容器开箱即用

## 系统地图

| 表面 | 输入 | 输出 | 典型场景 |
| --- | --- | --- | --- |
| **Reasoner** | 文本 + 图像/视频 | 文本 | 视频描述、时间定位、2D 空间定位、下一步动作预测、物理合理性判断、具身决策 |
| **Generator** | 文本 + 图像/视频 + 声音 + 动作 | 图像 + 视频 + 声音 + 动作 | 文生图/视频、图生视频、视频转写、正逆动力学、合成数据、策略训练 |

两个表面的分工可以用一句话记：**要文字答案找 Reasoner，要像素、声音和动作找 Generator**。Reasoner 只加载理解塔，遵循 Qwen3-VL 风格的消息约定；Generator 加载完整 checkpoint，把扩散生成、声音和动作头一起带上。

## 关键能力

- **世界理解**：视频 / 图像 → 描述、时序事件、下一步动作、空间定位、物理合理性、因果结果
- **世界生成**：文本 / 图像 / 视频 → 图像、视频、与画面同步生成的声音、按动作条件推演的未来画面
- **动作建模**：策略动作、逆动力学、正动力学（输入动作块 → 推演未来画面）、相机运动、第一人称运动、自驾
- **后训练**：Cosmos Framework 已提供 SFT 配方（视觉生成、DROID 策略、Reasoner 对齐）、Super → 4-Step 的 DMD2 蒸馏配方和 checkpoint 导出脚本，训练基准配置为 8×H100
- **输入维度**：相机运动 9D / 自动驾驶 9D / 第一人称 57D / 单臂 10D（DROID/UR/Fractal/Bridge/UMI）/ 双臂 20D / 人形 29D（AgiBot）

## 模型族

| 模型 | 规模 | 推荐硬件 | 定位 |
| --- | --- | --- | --- |
| `Cosmos3-Super` | 64B | 数据中心：H200 / B200 / GB200 | 高质量合成数据生成、蒸馏教师模型 |
| `Cosmos3-Nano` | 16B | 工作站到数据中心：RTX Pro 6000 / H100 / B200 | 速度与质量均衡，后训练首选底座 |
| `Cosmos3-Edge` | 4B | 边缘：Jetson AGX Orin / Thor / RTX Pro 6000 | 实时机器人策略、实时视觉推理 |

六个专用 checkpoint：

| Checkpoint | 用途 |
| --- | --- |
| `Cosmos3-Super-Text2Image` / `Cosmos3-Super-Image2Video` | 专用文生图、图生视频 |
| `Cosmos3-Super-Text2Image-4Step` / `Cosmos3-Super-Image2Video-4Step` | DMD2 蒸馏学生模型，官方标称 17–25 倍加速 |
| `Cosmos3-Nano-Policy-DROID` | 视觉-语言-动作机器人策略（DROID 操作数据） |
| `Cosmos3-Edge-Policy-DROID` | 边缘端实时策略版 |

FP8 / NVFP4 量化 checkpoint 标注为 coming soon；目前 FP8 精度只在 NIM 容器里可用（`NIM_PRECISION=fp8` 为默认，`nvfp4` 需 Blackwell）。

## 支持的生成参数

| 维度 | 可选 |
| --- | --- |
| 分辨率档 | 256p / 480p / 720p（默认 480p） |
| 比例 | 16:9 / 4:3 / 1:1 / 3:4 / 9:16（默认 16:9） |
| 帧率 | 10 / 16 / 24 / 30 FPS（默认 24） |
| 帧数 | 5–300（默认 189，即 24 FPS 下约 7.9 秒） |
| 精度 | BF16（官方测试口径） |
| 操作系统 | Linux |
| GPU | NVIDIA Ampere / Hopper / Blackwell |

Edge 档受限：只支持 256p / 480p、12–30 FPS、50–150 帧，没有声音塔，也不支持 video-to-video。

输入输出约定：图像走 JPG/PNG/WEBP，视频走 MP4，动作是 JSON 数组；视频条件固定用 5 帧；声音以 AAC 立体声 48 kHz 与视频一起生成，不单独出音频。

## 先选路径：六条推理路线

同一个模型，官方给的研究、服务、开箱三条路线各有两条，先对号入座再往下看代码：

| 目标 | 用什么 | 说明 |
| --- | --- | --- |
| 研究 / 改 Generator | Diffusers | Python 优先，可检查、可改生成行为 |
| Generator 生产服务 | vLLM-Omni / SGLang | OpenAI 兼容 API，覆盖图像、视频、声音、动作输出 |
| Generator 开箱部署 | NIM | 预置 NGC 容器，只做 Text2Video / Image2Video |
| 研究 / 改 Reasoner | Transformers | Python 优先，只加载理解塔 |
| Reasoner 生产服务 | vLLM / TensorRT-LLM | OpenAI 兼容端点，Nano 单卡、Super 默认 4 卡 |
| Reasoner 开箱部署 | NIM | 预置优化容器，免 vLLM/CUDA 配置 |

## 快速开始

### 0. 环境

官方全链路基于 `uv`（Cosmos Framework 要求 `uv >= 0.11.3`），Python 3.13。Generator 路径需要先在 Hugging Face 上申请 gated 仓库 [nvidia/Cosmos-1.0-Guardrail](https://huggingface.co/nvidia/Cosmos-1.0-Guardrail) 的访问权限——安全护栏会筛查 prompt 并对生成画面中的人脸打码，默认开启。

```shell
uvx hf@latest auth login

uv venv --python 3.13 --seed --managed-python
source .venv/bin/activate
uv pip install --torch-backend=auto \
  "diffusers @ git+https://github.com/huggingface/diffusers.git" \
  accelerate \
  av \
  cosmos_guardrail \
  huggingface_hub \
  imageio \
  imageio-ffmpeg \
  torch \
  torchvision \
  transformers
```

`--torch-backend=auto` 让 uv 按驱动装匹配的 CUDA 版 torch；仓库没有 `requirements.txt`，各路径的依赖以 README 对应小节为准。Cosmos 3 的 Diffusers 集成目前要装 git 主干版，Transformers 侧 Nano/Super 需要 `>= 5.11.0`，Edge 要装主干版。

### 1. Diffusers：文生视频（研究路径）

```python
import torch
from diffusers import Cosmos3OmniPipeline
from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler
from diffusers.utils import export_to_video

pipe = Cosmos3OmniPipeline.from_pretrained(
    "nvidia/Cosmos3-Nano",
    torch_dtype=torch.bfloat16,
    device_map="cuda",
)
pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=10.0)

result = pipe(
    prompt="A mobile robot navigates a warehouse aisle and stops at a shelf.",
    negative_prompt="",
    image=None,
    num_frames=189,
    height=720,
    width=1280,
    fps=24,
    num_inference_steps=35,
    guidance_scale=6.0,
    enable_sound=False,
    add_resolution_template=False,
    add_duration_template=False,
    generator=torch.Generator(device="cuda").manual_seed(1234),
)

export_to_video(result.video, "cosmos3_t2v.mp4", fps=24, macro_block_size=1)
```

同一个 pipeline 覆盖四种模式：`num_frames=1` 出单张图，给 `image` 条件走图生视频，`enable_sound=True` 在支持的 checkpoint 上连带生成声音。

### 2. vLLM-Omni：生成服务（生产路径）

官方推荐从 Docker 镜像启动，加载完整 checkpoint（含 Qwen3-VL 理解路径和扩散生成路径）：

```shell
docker run --runtime nvidia --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v "$(pwd):/workspace" \
  -p 8000:8000 \
  --ipc=host \
  -w /workspace \
  vllm/vllm-omni:cosmos3 \
  vllm serve nvidia/Cosmos3-Nano \
  --omni \
  --model-class-name Cosmos3OmniDiffusersPipeline \
  --allowed-local-media-path / \
  --port 8000 \
  --init-timeout 1800
```

64B 的 Super 加 `--tensor-parallel-size 4 --enable-layerwise-offload` 把权重切到 4 卡并分层卸载。服务就绪后用 multipart 表单向 `/v1/videos/sync` 发请求：

```shell
curl -sS -X POST http://localhost:8000/v1/videos/sync \
  --form-string "prompt=A small warehouse robot moves a blue box across a clean floor." \
  --form-string "negative_prompt=blurry, distorted, low quality" \
  --form-string "size=1280x720" \
  --form-string "num_frames=189" \
  --form-string "fps=24" \
  --form-string "num_inference_steps=35" \
  --form-string "guidance_scale=6.0" \
  --form-string "flow_shift=10.0" \
  --form-string "seed=0" \
  --form-string 'extra_params={"use_resolution_template":false,"use_duration_template":false,"guardrails":true}' \
  -o cosmos3_t2v_output.mp4
```

动作模式走异步的 `POST /v1/videos`：在 `extra_params` 里传 `action_mode`（`policy` / `inverse_dynamics` / `forward_dynamics`）、`domain_name`（如 `bridge_orig_lerobot`、`av`、`camera_pose`）和 `raw_action_dim`，完成的作业里取回动作块。

### 3. Transformers：Reasoner 本地推理

```python
from pathlib import Path

import torch
from transformers import AutoProcessor, Cosmos3OmniForConditionalGeneration

model_id = "nvidia/Cosmos3-Nano"
image_path = Path("robot_153.jpg").resolve()

processor = AutoProcessor.from_pretrained(model_id)
model = Cosmos3OmniForConditionalGeneration.from_pretrained(
    model_id,
    dtype=torch.bfloat16,
    device_map="auto",
)

messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "path": str(image_path)},
            {"type": "text", "text": "Caption the image in detail."},
        ],
    }
]

inputs = processor.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_dict=True,
    return_tensors="pt",
).to(model.device, torch.bfloat16)

generated_ids = model.generate(**inputs, do_sample=False, max_new_tokens=512)
output = processor.batch_decode(generated_ids, skip_special_tokens=True)
print(output[0])
```

这条路径只加载 Reasoner 塔，返回文本；换视频输入时把 content 块换成 `{"type": "video", ...}` 并在 `apply_chat_template` 传抽帧的 `fps`。Edge 用的是另一套类（`AutoModelForImageTextToText` / `Cosmos3EdgeForConditionalGeneration`），不能用上面的 Omni 类加载。

### 4. NIM：开箱即用

两个预置容器：`cosmos3-generator:1.0.0` 只做 Text2Video / Image2Video，请求发 `POST /v1/infer`，从 JSON 响应的 `b64_video` 字段解出 MP4；`cosmos3-reasoner:1.7.0` 提供 OpenAI 兼容的 `/v1/chat/completions`，`NIM_MODEL_SIZE=nano|super` 二选一。两者都要 NGC API key 登录 `nvcr.io` 拉取。

## 一次请求的流转

以「一句话生成一段 720p 机器人视频」为例，请求穿过的是这样一条链：

1. **请求进入 vLLM-Omni**，`guardrails: true` 让护栏模型先过一遍 prompt，生成完成后还要对人脸区域打码；
2. **理解路径接手**——prompt（超长会被截断到 512 token 并警告）先经 prompt upsampling 扩写成稠密的结构化场景描述，官方示例的采样上限是 20000 token；
3. **扩散路径出画面**——噪声化的图像、视频、音频 token 在全注意力下去噪，与理解塔共享同一套 mRoPE 位置表征，所以时间轴上帧与帧、声道与画面是对齐的；
4. **动作与声音同权重组装**——`enable_sound` 打开时声音流直接随视频生成（不是事后配音），动作模式的输出则是 JSON 动作块，可以直接喂给机器人执行栈；
5. **返回**——同步端点直接回 MP4（示例里 189 帧 / 24 FPS 约 7.9 秒的片子），异步端点回作业 ID，轮询后取结果。

同一个 checkpoint 换一组参数就是另一条流水线：把 `action_mode` 设成 `policy`、`domain_name` 设成机器人本体、附上相机帧，返回的就是可执行的动作块而不是视频。这正是「世界模型」和「视频生成器」的分界——前者输出的是对未来状态的预测，画面只是预测的一种渲染。

## 推理基准怎么看

官方在仓库的 `inference_benchmarks.md` 里按 GPU × 引擎 × 分辨率给出了延迟表，读它之前先弄清三件事：

**测的是什么。** 生成侧是单卡延迟（秒），口径为 BF16、batch size 1、189 帧 @ 24 FPS（Edge 用 121 帧 @ 480p）；NIM 一列用的是 FP8 精度。理解侧是 vLLM 在并发 1/64/128/256 下的 TTFT、请求延迟和吞吐。空格表示没测，不是不支持。

**数字反映了什么。** 以 Nano 文生视频为例：256p 单卡只要 4–11 秒，720p 要 200–786 秒（B200 上 PyTorch 114.85 秒、NIM FP8 93.33 秒）——扩散推理的成本随分辨率和帧数陡增，引擎差异（同一张卡上 NIM 比 PyTorch 参考实现快 15–25%）只是二阶因素。Super 64B 的 720p 文生视频在 B200 上是 314–407 秒，贵在规模而不在流程。Edge 4B 的 121 帧图生视频在 B300 上 6.84 秒、RTX Pro 6000 上 21.92 秒，这是它能谈「实时策略」的本钱。

**不能推出什么。** 单卡延迟不等于服务吞吐，并发能力要看 Reasoner 的 vLLM 指标；这些是 NVIDIA 自测的特定 prompt 与设置，换成你的场景、你的 prompt 长度，数字要自己重跑；Jetson 平台上的 Edge 生成数字官方还是空的，「边缘可跑」目前有据的是 Reasoner 侧和策略侧。

## 它在解决谁的什么问题

- **机器人 / 具身智能团队**：要带动作标注的训练数据。`Cosmos3-Nano-Policy-DROID` 提供 SoTA 口径的世界动作模型，forward dynamics 能按动作块推演未来画面（AV、DROID、UMI、人手姿态各有配方），SFT 配方可基于自己的数据后训练
- **自动驾驶团队**：要做 corner case 仿真。video-to-video 支持条件帧保留 + transfer 控制（`edge` / `blur` / `depth` / `seg` / `wsm` 五类提示），拿真实路况视频改天气、改布局；逆动力学能从自驾视频回归自车运动轨迹
- **多模态理解团队**：Reasoner 的九类工作流（描述、时间定位、2D 定位、describe anything、action CoT、物理合理性分类等）都是现成配方，OpenAI 兼容接口直接接现有调用栈
- **视频内容团队**：图生视频 + 同步声音 + 4-Step 蒸馏版（官方标称 17–25 倍加速），是这套模型里离内容生产最近的一档

## 关键事实

| 维度 | 数据 |
| --- | --- |
| Stars / Forks | 11,891 / 890（2026-09-22 读数） |
| 创建 / Cosmos 3 发布 | 仓库 2024-12-30；Cosmos 3 2026-05-31 |
| 主要语言 | Jupyter Notebook（核心实现是 PyTorch） |
| 许可证 | 源码与模型均为 [OpenMDW-1.1](https://openmdw.ai/license/1-1/)；自定义许可联系 cosmos-license@nvidia.com |
| 模型族 | Super 64B / Nano 16B / Edge 4B + 6 个专用 checkpoint |
| 架构 | Mixture-of-Transformers（AR 推理塔 + 扩散生成塔，共享 mRoPE） |
| 理解塔基座 | Qwen3-VL（消息约定与 vLLM-Omni 集成均为 Qwen3-VL 口径） |
| 推理后端 | Diffusers / Transformers（研究）；vLLM-Omni / SGLang（生成服务）；vLLM / TensorRT-LLM（理解服务）；NIM（开箱即用） |
| 支持 GPU | Ampere / Hopper / Blackwell（FP8/NVFP4 的 NVFP4 需 Blackwell） |

## 它和竞品的边界

- **vs Sora / Veo / Kling**：闭源视频生成产品；Cosmos 把理解、生成、动作做进同一 checkpoint 并开放权重，代价是要自己备卡部署
- **vs Wayve GAIA / Tesla Dojo**：自驾厂商的内部世界模型，不对外；Cosmos 是同构能力的开放替代
- **vs LeRobot / OpenVLA**：纯策略模型与工具链；Cosmos 把数据策源（Cosmos Curator）、世界模型、评估（Cosmos Evaluator）连成一条线，策略只是输出模态之一
- **vs Stable Video Diffusion**：传统扩散视频模型；Cosmos 的 MoT 架构让画面、声音、动作在同一套位置表征下联合生成，且推理路径有服务化配方
- **vs Isaac Sim / CARLA**：传统仿真引擎靠手工建模场景；Cosmos 从数据学世界动力学，更适合长尾场景的批量合成，但物理精度要按官方 Limitations 打折扣看

## 适合与不适合

**适合**

- 做 Physical AI（机器人 / 自驾 / 工业）的团队，需要带动作标注的合成视频或可后训练的世界模型底座
- 已有 Ampere 及以上的 NVIDIA 集群，想要 OpenAI 兼容的生成/理解服务且不被闭源 API 锁定
- 想用同一个模型覆盖「视频理解 + 视频生成」两类下游任务

**不适合**

- 只有消费级显卡：Nano 16B 官方推荐从 RTX Pro 6000 起步，Super 64B 按官方口径是 H200 / B200 / GB200 的数据中心配置，服务化部署 TensorRT-LLM/vLLM 默认按 4 卡张量并行规划
- macOS / Windows 桌面环境：官方只支持 Linux + NVIDIA 驱动
- 想要「零部署上手」：申请 Guardrail 权限、拉数十 GB 权重、装 CUDA 匹配的 torch，门槛比网页版视频生成产品高一个量级
- 需要严格物理正确性的场景：官方 Limitations 明说这类应用要额外的验证与系统级安全分析

## 已知边界

- **长视频、高分辨率、复杂物理场景会出 artifacts**：官方列的常见失效模式包括时序不一致、相机或物体运动不稳、声画对齐不准、动作状态不一致、物体形变、3D 结构失真、物理动力学失真
- **prompt 约束**：世界生成 prompt 官方建议少于 300 词；vLLM-Omni 侧超过 512 token 会截断并警告
- **声音不能单独生成**：声音与视频一起产出，没有独立的文本转音频路径
- **量化 checkpoint 未发**：FP8 / NVFP4 权重标注 coming soon，当前省显存靠 NIM 容器的 FP8 精度或 vLLM-Omni 的分层卸载
- **Generator 默认带护栏**：筛查 prompt + 人脸打码，关闭护栏要按路径分别处理（Diffusers 的 `enable_safety_checker=False`、vLLM-Omni 的 `guardrails: false`、TensorRT-LLM 的环境变量），作为安全特性不建议轻易关
- **训练要用 Cosmos Framework**：SFT、蒸馏、导出脚本都在 [NVIDIA/cosmos-framework](https://github.com/NVIDIA/cosmos-framework) 仓库，本仓库只管推理与示例

## 与文本矩阵的关联

文本矩阵里 `nvidia-video-search-summarization-blueprint-guide.md` 写过 NVIDIA 的视频检索 blueprint；`sana-high-resolution-image-synthesis.md` 写过 NVIDIA 的高分辨率图像合成；Cosmos 是这条线索的**「世界基础模型」那一站**——从内容理解（VLM）跨到「预测下一秒会发生什么」（世界模型），是 Physical AI 时代 NVIDIA 给开发者铺好的下一段路。

## 资源

- 仓库：<https://github.com/NVIDIA/cosmos>
- Cosmos 3 项目页：<https://research.nvidia.com/labs/cosmos-lab/cosmos3/>
- 技术报告：<https://research.nvidia.com/labs/cosmos-lab/cosmos3/technical-report.pdf>
- HuggingFace 模型合集：<https://huggingface.co/collections/nvidia/cosmos3>
- Cosmos Framework（训练/评估）：<https://github.com/NVIDIA/cosmos-framework>
- Cosmos Curator（数据策源）：<https://github.com/NVIDIA/cosmos-curator>
- Cosmos Evaluator（评估）：<https://github.com/NVIDIA/cosmos-evaluator>
- 推理基准：<https://github.com/NVIDIA/cosmos/blob/main/inference_benchmarks.md>

## 参考来源与口径说明

- 本文代码与参数以 **2026-09-22 的 NVIDIA/cosmos main 分支 README** 为口径，Cosmos 3 于 2026-05-31 发布；stars/forks 为 GitHub API 同日读数。
- 全部代码示例取自官方 README 的 Quickstart 段（Diffusers、vLLM-Omni、Transformers 三处），未改动参数语义；模型存在性经 Hugging Face API 逐一核验（6 个 checkpoint 均 200）；外链与技术报告 PDF 已复测可访问。
- 原稿以下内容查无官方出处，已删除：「Super 起步 4×H100」「4-bit 量化后 2–4 张」「300 帧/24FPS 在 8×B200 上才实时」「DROID 数据可生成 10K–100K 小时视频」「Reasoner 16B 实时决策」「Sora 级时序一致性」「声音需 ffmpeg 5.0+ 解析」「NIM 支持 K8s 自动扩缩容」「prompt 超 300 词导致时序一致性下降」（官方只给建议值，未给因果）、「trending 当日新增 138 star」。
- 原稿的许可证口径「NVIDIA Cosmos License / 按各模型卡为准」已更正为 README 明文的 OpenMDW-1.1；「后训练配方尚未开源」已过时，Cosmos Framework 现提供 SFT、DMD2 蒸馏与 checkpoint 导出的完整配方。
