---
title: "ComfyUI MiniMax H3 Director：一个导演台节点如何接管多段视频生成"
date: 2026-08-04T10:45:00+08:00
draft: false
categories: ["技术文章"]
tags: ["ComfyUI", "MiniMax H3", "视频生成", "工作流", "视频编辑"]
description: "拆解 AIMixer/ComfyUI_MiniMaxH3_Director 仓库的 5 套工作流与导演台节点架构，覆盖 T2V、FL2V、R2V、V2V、RV2V 五种模式的能力边界、节点拓扑、模型选型与实战陷阱。"
slug: index
---

## 仓库信息卡

| 字段 | 值 |
|------|-----|
| 仓库 | [huangserva/ComfyUI_MiniMaxH3_Director](https://github.com/huangserva/ComfyUI_MiniMaxH3_Director) |
| 上游 | [AIMixer/ComfyUI_MiniMaxH3_Director](https://github.com/AIMixer/ComfyUI_MiniMaxH3_Director) |
| Stars / Forks | 17 / 3（截至 2026-08-04） |
| 创建时间 | 2026-08-04 10:39 UTC |
| 最近 push | 2026-08-04 10:45 UTC |
| 大小 | 10 KB |
| 许可证 | Apache-2.0 |
| 模型权重 | [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) |

这个仓库创建于今天（2026 年 8 月 4 日），从创建到最后一次 push 只隔了 6 分钟。它不是上游 AIMixer 仓库的 fork，而是 README 中明确定义的「方便下载、复现和测试的副本」——仓库里没有一行 Python 代码，只有 5 份 ComfyUI 工作流 JSON 和一份 README。如果你要装插件，仍然需要从 [上游 AIMixer 仓库](https://github.com/AIMixer/ComfyUI_MiniMaxH3_Director) 拉取代码到 `custom_nodes/`。

## 这个仓库到底是什么

先澄清一个容易产生的误解：这不是一个 Python 项目，也不包含任何自定义节点实现代码。仓库的全部内容是：

- `README.md`——环境配置、模型清单、5 个工作流的用法说明
- `example_workflows/` 目录下 5 份 JSON 文件，每份是一个可直接拖进 ComfyUI 的完整工作流

真正实现 `MiniMaxH3Director` 节点的代码在上游 [AIMixer/ComfyUI_MiniMaxH3_Director](https://github.com/AIMixer/ComfyUI_MiniMaxH3_Director)。上游仓库大小约 559 KB，包含完整的 Python 插件代码、依赖声明和文档截图。huangserva 的这个副本存在的意义是：给你一套开箱即用的 JSON，下载后改改文件名就能跑。

## MiniMax H3 与导演台节点

### MiniMax H3 模型族

MiniMax H3 是 MiniMax-AI 推出的多模态音视频生成模型。ComfyUI 官方在 v0.30.0 中合并了对它的原生支持（[PR #15224](https://github.com/comfyanonymous/ComfyUI/pull/15224)、[PR #15228](https://github.com/comfyanonymous/ComfyUI/pull/15228)），模型权重由 [Comfy-Org 在 Hugging Face 上发布](https://huggingface.co/Comfy-Org/MiniMax-H3)。

模型族有两个核心变体，差异在于输入通道：

| UNET 变体 | 文件名 | 适配模式 |
|-----------|--------|---------|
| **fl2va** | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` | T2V、I2V、FL2V——纯文本或图片到视频 |
| **ref2va** | `minimax_h3_ref2va_pruned_int8_convrot.safetensors` | R2V、V2V、RV2V——需要参考素材或源视频输入 |

两个变体共用同一套辅助组件：

| 用途 | 文件 | 放置目录 |
|------|------|---------|
| 文本编码器（Qwen3-VL 32B） | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `models/text_encoders/` |
| 视频 VAE | `minimax_h3_video_vae_fp16.safetensors` | `models/vae/` |
| 音频 VAE | `minimax_h3_audio_vae_fp32.safetensors` | `models/vae/` |

CLIP Loader 节点的 `type` 参数必须选 `minimax`，不能留默认值。这个值告诉 ComfyUI 用 Qwen3-VL 而非常规 CLIP 模型做文本编码。

### 导演台节点 MiniMaxH3Director

官方 ComfyUI 对 MiniMax H3 的支持是原子级的：`MiniMaxH3ImageToVideo`、`MiniMaxH3ReferenceToVideo`、`MiniMaxH3SigmaShift`、`KSampler` 等节点各自负责一步。要生成一段 5 秒的视频，用户需要手动连接四五个节点。

AIMixer 的 `MiniMaxH3Director` 把这条链路打包进了一个节点。根据上游 README 的描述，导演台内部调用的仍然是官方的那些原子节点——`MiniMaxH3ImageToVideo` / `MiniMaxH3ReferenceToVideo` + `MiniMaxH3SigmaShift` + `KSampler` + AV 分离解码——但在外层加了一套时间轴管理 UI、分段调度逻辑和缓存机制。

导演台节点的输入输出很简洁：

**输入：** `model` → `video_vae` → `audio_vae` → `clip`

**输出：** `images` → `audio` → `fps` → `frame_count` → `source_images` → `report`

4 个输入，6 个输出。UNET、CLIP、Video VAE、Audio VAE 各一条线进来，画面、音频、帧率、帧数、源画面、运行报告各一条线出去。

## 导演台的四个核心机制

### 逐段选择运行

传统 ComfyUI 视频工作流是「一条线跑到底」：改一个参数，整段视频从头生成。导演台引入了分段时间轴——你可以把一段长视频拆成多个片段，每段写不同的提示词，然后只勾选你想跑的那几段。

工作流 JSON 中的 `runSelectEnabled` 和 `runSelection` 字段控制这个行为。`runSelectEnabled` 为 `true` 时，导演台只采样 `runSelection` 数组中列出的片段 ID；未勾选的段可以用缓存或源画面填充（在全部导出模式下）。

### 缓存复用

逐段运行的前提是缓存能命中。README 提到「改一段时缓存其他段，避免重复计算」，但没给出缓存的生命周期和失效策略的细节。从工作流 JSON 的结构推断，缓存以段 ID（如 `s0`、`s1`）为 key，当段内的提示词、参考素材或采样参数发生变化时，该段缓存失效，其他段不受影响。

一个需要注意的地方：如果全局参数（分辨率、帧率、seed）变了，所有段的缓存可能都会失效。做 A/B 测试时固定这些变量，才能让缓存真正发挥作用。

### 参考素材约束身份

在 R2V、V2V、RV2V 三种模式中，导演台通过标签系统引用参考素材：

- `<Picture N>`——引用第 N 张参考图（1–9）
- `<Video K>`——引用第 K 段参考视频（1–3）
- `<Audio J>`——引用第 J 段参考音频（1–3）

在提示词里写 `<Picture 1> walks into a neon-lit alley at night`，模型会尝试让生成画面中的人物外观与 Picture 1 一致。上游 README 同时提醒：**导演台没有硬身份锁**。人物身份一致性由模型能力和参考素材共同决定，导演台只负责把参考素材送进去。如果参考图角度偏、分辨率低，身份漂移仍然会发生。

### 段间引导

多段视频拼接时，导演台用上一段末帧作为下一段首帧的初始条件，让画面有一个交接。工作流 JSON 中 `output.continuityEnabled` 和 `output.continuityOverlapFrames` 两个字段控制这个行为：默认关闭（`false`），开启后用 `continuityOverlapFrames`（默认 9 帧）做重叠融合。

README 明确指出段间引导**不能替代人物一致性检查**。末帧交接解决的是画面连续性——镜头、光线、背景的平滑过渡——但人物长相、服装细节这些跨段一致性，仍然依赖参考素材约束和人工检视。

## 五种工作流深度对比

仓库提供了 5 份工作流 JSON，每份的节点拓扑完全一致，差异在于导演台节点的 `timelineMode` 和 `taskType` 参数。

| 工作流 | 模式 | UNET | timelineMode | 典型用途 |
|--------|------|------|-------------|---------|
| `minimax_h3_director_t2v.json` | T2V | fl2va | `gen_blank` | 纯文本生成音视频 |
| `minimax_h3_director_fl2v.json` | FL2V / I2V | fl2va | `fl2v` | 首尾帧生视频；只放首帧时退化为 I2V |
| `minimax_h3_director_r2v.json` | R2V | ref2va | `gen_blank` | 多张参考图 + 提示词生成视频 |
| `minimax_h3_director_v2v.json` | V2V | ref2va | `video` | 上传源视频，按时间轴逐段重绘 |
| `minimax_h3_director_rv2v.json` | RV2V | ref2va | `video` | 源视频 + 参考图/参考音频，视频换人 |

`timelineMode` 决定导演台 UI 的交互方式：`gen_blank` 是空白时间轴（从零创建），`fl2v` 是首尾帧分组 UI（每组一对关键帧），`video` 是源视频时间轴（上传后按帧分割）。`taskType` 是一个字符串标签，同时作为导演台节点的显示名称和内部调度逻辑的判断依据。

### 能力边界

- **T2V** 是最基础的模式：只输入文本提示词，输出带音频的视频。默认参数 864×480、124 帧、24fps（约 5 秒）。
- **FL2V** 扩展了 T2V：添加「首帧」和「尾帧」约束。首帧必传，尾帧可选——不传尾帧就是 I2V（图生视频）。可以添加多组首尾帧，每组独立计时，总时长 = 各组之和。
- **R2V** 切换到 ref2va UNET，支持上传 1–9 张参考图、1–3 段参考视频、1–3 段参考音频。提示词用 `<Picture N>` 标签引用，让模型在生成时参考指定素材的身份、风格或声音。
- **V2V** 上传一段源视频后自动按时间轴分段（支持切分、均分、PySceneDetect 智能分镜），每段源画面绑定到 `<Video 1>`。适合对已有视频做风格迁移、重新打光或镜头调整。
- **RV2V** 在 V2V 基础上叠加参考素材组——源视频提供运动轨迹和场景布局，参考图提供人物外观。README 说这适合「测试视频换人」，但请注意上一节提到的身份约束局限。

### T2V 与 FL2V 的关系

T2V 是 FL2V 的退化形态。把 FL2V 的首帧和尾帧都留空，就得到 T2V。两者共用 fl2va UNET，差异仅在导演台时间轴上是否有关键帧约束。如果你一开始没有关键帧素材，可以先跑 T2V 生成一段视频，再把输出帧作为 FL2V 的关键帧做迭代。

### V2V 与 RV2V 的关系

同理，V2V 是 RV2V 不挂参考素材时的退化形态。两者共用 ref2va UNET。RV2V 的核心区别在于导演台节点上多了参考图和参考音频的输入槽位。源视频始终自动绑定为 `<Video 1>`，参考图按上传顺序编号为 `<Picture 1>` 到 `<Picture 9>`。

## 11 节点拓扑结构

5 份工作流的节点图完全一致——11 个节点，结构相同，差异全在导演台节点的参数里。

### 节点清单

| 节点 ID | 类型 | 标题 | 作用 |
|---------|------|------|------|
| 1 | `UNETLoader` | MiniMax H3 UNET | 加载 fl2va 或 ref2va 扩散模型 |
| 2 | `CLIPLoader` | CLIP (minimax / Qwen3-VL) | 加载 Qwen3-VL 32B 文本编码器，type 选 `minimax` |
| 3 | `VAELoader` | Video VAE | 加载视频变分自编码器（fp16） |
| 4 | `VAELoader` | Audio VAE | 加载音频变分自编码器（fp32） |
| 5 | `MiniMaxH3Director` | （无标题） | 导演台核心节点 |
| 6 | `CreateVideo` | （无标题） | 将画面帧序列编码为视频 |
| 7 | `SaveVideo` | （无标题） | 保存视频文件到输出目录 |
| 8 | `PreviewAny` | Director 运行报告 | 显示导演台输出的分段计划和任务摘要 |
| 9 | `PreviewAny` | fps | 显示帧率 |
| 10 | `PreviewAny` | frame_count | 显示总帧数 |
| 11 | `MarkdownNote` | （工作流名称） | 嵌入使用说明的 Markdown 笔记节点 |

### 连接拓扑

数据流按以下路径流动：

```text
UNETLoader (1) ──model──→ MiniMaxH3Director (5)
CLIPLoader  (2) ──clip───→     │
VAELoader   (3) ──video_vae──→ │
VAELoader   (4) ──audio_vae──→ │
                                ↓
                    ┌───────────┼───────────┐
                  images      audio       fps ──→ PreviewAny (9)
                    │           │          frame_count ──→ PreviewAny (10)
                    ↓           │          report ──→ PreviewAny (8)
              CreateVideo (6)   │
                    ↓           │
              SaveVideo (7)     │
```

导演台节点是整个图的枢纽：4 条输入线（model、clip、video_vae、audio_vae），6 条输出线（images、audio、fps、frame_count、source_images、report）。3 个 PreviewAny 节点负责展示运行报告和元数据，不参与数据加工。CreateVideo 接收 images 和 audio，输出打包后的视频流，SaveVideo 写入磁盘。

拓扑的一致性意味着你可以用同一套外围节点配合不同的导演台参数：切换模式不需要重新搭图，只改导演台节点的 `taskType` 和 `timelineMode`，再换一下 UNET 文件名。

## 导演台节点的参数结构

从工作流 JSON 中提取的导演台节点 `widgets_values`，参数按顺序排列如下：

| 序号 | 参数 | 示例值 | 说明 |
|------|------|--------|------|
| 0 | task_type | `t2v — 文生视频(Text to Video)` | 任务模式标签 |
| 1 | global_prompt | （多行文本） | 全局提示词 |
| 2 | 分组标题 | `采样设置` | UI 折叠面板标题 |
| 3 | cfg | `1.0` | CFG 比例 |
| 4 | seed | `42` | 随机种子 |
| 5 | seed_control | `randomize` | 种子控制模式 |
| 6 | frame_rate | `24.0` | 帧率 |
| 7 | width | `864` | 画面宽度 |
| 8 | height | `480` | 画面高度 |
| 9 | long_edge / ref_max_size | `864` | 长边/参考图最大尺寸 |
| 10 | total_frames | `124` | 总帧数（17k+5 网格对齐） |
| 11 | timeline_data | （JSON 字符串） | 时间轴完整配置 |
| 12 | 分组标题 | `高级采样 Advanced` | UI 折叠面板标题 |
| 13 | steps | `25` | 采样步数 |
| 14 | sampler | `res_multistep` | 采样器 |
| 15 | scheduler | `simple` | 调度器 |
| 16 | shift_video | `12.0` | 视频 sigma 偏移 |
| 17 | shift_audio | `3.0` | 音频 sigma 偏移 |
| 18 | 分组标题 | `性能 Performance` | UI 折叠面板标题 |
| 19 | clear_vram_between_segments | `True` | 段间清理显存 |
| 20 | export_source_images | `False` | 是否导出源画面 |

`timeline_data` 是一个序列化 JSON 字符串，包含 `editMode`、`timelineMode`、`totalFrames`、`frameRate`、`width`、`height`、`refMaxSize`、`output`（导出设置）、`videoClips`、`video`（源视频信息）、`global`（全局提示词和参考素材）、`segments`（段数组）、`runSelectEnabled`、`runSelection` 等字段。这个 JSON 是导演台 UI 的完整状态快照——你在界面上做的每一步操作都会反映到这里。

### 帧数对齐规则

总帧数 124 不是随便选的。MiniMax H3 的扩散模型按 17k+5 网格对齐（k 为非负整数）：

- k=0 → 5 帧
- k=1 → 22 帧
- k=2 → 39 帧
- k=3 → 56 帧
- k=4 → 73 帧
- k=5 → 90 帧
- k=6 → 107 帧
- k=7 → 124 帧 ≈ 5.17 秒 @ 24fps

124 帧 @ 24fps 大约 5.17 秒，README 中简称为「5 秒」。如果输入非对齐帧数，模型会自动 round 到最近的网格点。

## RV2V 视频换人完整流程

RV2V 是 5 种模式中交互最复杂、也是最有实际应用场景的模式。README 给出了完整的操作步骤：

### 第 1 步：导入工作流

将 `minimax_h3_director_rv2v.json` 拖入 ComfyUI。确认 UNET Loader 选中 `minimax_h3_ref2va_pruned_int8_convrot.safetensors`，CLIP Loader 的 type 为 `minimax`，两个 VAE 分别指向视频和音频文件。

### 第 2 步：上传源视频并分段

在导演台节点中上传源视频。分段方式有三种：

- **手动切分**——在时间轴上拖动分割点
- **均分**——按指定段数自动等分
- **智能分割**——调用 PySceneDetect 自动检测镜头边界（需要安装 `scenedetect` 依赖）

每段的长度就是该段生成的视频时长。段越长，单段计算压力越大；段越短，段间交接次数越多，画面连续性风险越高。

### 第 3 步：上传参考素材

在导演台的参考图槽位上传人物参考图（1–9 张）。如果需要声音约束，再加参考音频（1–3 段）。参考图的拍摄角度、光线、分辨率都会影响身份一致性——正面照、均匀光线、高分辨率的效果最好。

### 第 4 步：逐段写提示词

每段分别写提示词。源视频片段自动绑定为 `<Video 1>`，参考素材用 `<Picture N>` 和 `<Audio J>` 引用。一段典型的 RV2V 提示词：

```text
Replace the person in <Video 1> with the subject from <Picture 1>.
Keep camera motion and scene layout from <Video 1>.
Match identity, hair, and outfit of <Picture 1>.
Cinematic lighting. No text or logos.
```

这段提示词来自工作流 JSON 中的默认值，结构是三句话：指定替换对象、保留源视频属性、约束参考身份。你可以按需调整，但保持这个「源→目标→约束」的三段式结构有助于模型理解意图。

### 第 5 步：先生成 5 秒，检查再扩展

README 的建议是先生成一个 5 秒片段（124 帧），检查脸部一致性、服装细节、动作连贯性和镜头边界，再决定是否扩展到更长的时间轴。原因很直接：视频生成的时间和显存成本随帧数线性增长，在不确定质量的情况下用最短的片段试错，成本最低。

音频部分有三种选择：

- **模型生成**——导演台根据提示词自动生成音频
- **沿用原声**——使用源视频的原始音轨
- **静音**——不输出音频

在 RV2V 换人场景中，如果你想保留源视频的背景音但替换人声，「模型生成」可能不是最优选择——它会完全重新生成一段音频。这时可以考虑后期混音。

## 已验证硬件环境

README 中列出的验证环境：

| 组件 | 规格 |
|------|------|
| GPU | NVIDIA RTX 4090 48GB |
| ComfyUI | 0.30.0 |
| PyTorch | 2.11.0 |
| CUDA | 12.8 |
| 验证模型 | MiniMax H3 Ref2VA INT8 |

一个细节：README 说「当前已验证的 4090 环境只有 Ref2VA」。也就是说 R2V、V2V、RV2V 三种模式（使用 ref2va UNET）有实机验证，但 T2V、I2V、FL2V 三种模式（使用 fl2va UNET）在该硬件上还没跑通——README 里写的是「需要补齐 fl2va 权重」。

RTX 4090 48GB 是定制版（零售版 4090 为 24GB 显存）。MiniMax H3 的 INT8 量化模型在这个显存容量下可以跑 864×480 分辨率、124 帧、25 步采样的配置。显存更小的卡（如 24GB 4090 或 16GB 4080）可能需要降低分辨率或帧数。

导演台节点还提供了一个 `clear_vram_between_segments` 参数（默认 `True`），在段与段之间清理显存，防止多段累积时 OOM。代价是清理和重载会增加一些时间开销。

## 默认采样参数

从工作流 JSON 中提取的默认参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 分辨率 | 864×480 | 16:9，约 0.4MP |
| 帧率 | 24 fps | 电影标准帧率 |
| 总帧数 | 124 | 17k+5 网格对齐，约 5.17 秒 |
| 采样步数 | 25 | res_multistep 采样器 |
| CFG | 1.0 | 低 CFG，减少过饱和 |
| 采样器 | `res_multistep` | 多步残差采样 |
| 调度器 | `simple` | 简单调度策略 |
| Sigma shift (video) | 12.0 | 视频噪声偏移 |
| Sigma shift (audio) | 3.0 | 音频噪声偏移 |
| seed | 42 | 默认种子，可 randomize |

这套参数是 AIMixer 在 4090 48GB 上验证过的基线。做 A/B 测试时，README 建议固定源素材、提示词、seed、分辨率、帧数和 steps 六个变量，每次只改一个维度。这样才能把效果差异归因到具体改动上。

## SageAttention 可选优化

SageAttention 是一个注意力计算加速库，可以减少扩散模型的推理时间。README 提到它作为可选项：安装后，将补丁节点插入 UNETLoader 与 MiniMaxH3Director 的 `model` 连线之间。

具体的连接方式：

```text
UNETLoader (1) ──model──→ [SageAttention 节点] ──model──→ MiniMaxH3Director (5)
```

README 的建议是先确认开启 SageAttention 后输出质量与不开时一致，再记录速度变化。注意力近似计算有时会引入微妙的画面伪影，在长视频多段拼接时这些伪影可能累积放大。

## 安装步骤

### 前提条件

- ComfyUI ≥ 0.30.0（包含官方 MiniMax H3 节点）
- NVIDIA GPU，显存 ≥ 24GB（4090 48GB 已验证；更小显存需降低参数）
- CUDA 12.x + PyTorch 2.x

### 安装导演台插件

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/AIMixer/ComfyUI_MiniMaxH3_Director.git
python -m pip install -r ComfyUI_MiniMaxH3_Director/requirements.txt
```

`requirements.txt` 中的可选依赖：

- `scenedetect`——智能分镜分割
- `opencv-python-headless`——源视频解码
- `imageio-ffmpeg`——原声抽取

安装后重启 ComfyUI，节点列表中应出现 `MiniMaxH3Director`。

### 下载模型权重

从 [Comfy-Org/MiniMax-H3](https://huggingface.co/Comfy-Org/MiniMax-H3) 下载以下文件，放到 ComfyUI 对应目录：

```text
models/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors
models/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors
models/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors
models/vae/minimax_h3_video_vae_fp16.safetensors
models/vae/minimax_h3_audio_vae_fp32.safetensors
```

### 加载工作流

将仓库 `example_workflows/` 目录下的 JSON 文件拖入 ComfyUI 界面，或使用菜单 → Load → 选择文件。工作流加载后，检查各 Loader 节点的文件名是否与本地一致。

## 局限与陷阱

### 身份一致性没有硬保证

导演台通过参考素材约束人物身份，但模型并没有一个「身份锁」机制。一段 30 秒的视频分 6 段生成，即使每段都挂了同一张参考图，人物的脸型、发色、服装细节仍可能在段间漂移。段间引导（末帧交接）解决的是画面连续性，不是身份一致性。

如果你需要严格的身份一致，目前的做法是：每段生成后人工检视，对不满意的段重跑（导演台的逐段运行和缓存机制就是为这个流程设计的），或者后期用 face-swap 工具修正。

### fl2va 模式未经验证

README 写明「当前已验证的 4090 环境只有 Ref2VA」。T2V、I2V、FL2V 三种模式需要 fl2va 权重，虽然在架构上与 ref2va 共享大部分组件，但没有实机跑通的记录。遇到问题（OOM、质量异常、注册失败）时，优先考虑这个因素。

### 帧数网格对齐的副作用

总帧数按 17k+5 对齐，意味着你输入 120 帧会自动变成 124 帧。如果需要精确控制时长（比如 4 秒 = 96 帧），最接近的网格点是 90 帧（k=5，约 3.75 秒）和 107 帧（k=6，约 4.46 秒），都不是精确 4 秒。对齐是模型架构层面的约束，不是导演台的选择——你只能选网格点，不能选任意帧数。

### PySceneDetect 和可选依赖的安装风险

智能分镜功能依赖 `scenedetect` 库。如果只按 README 的标准流程安装了 `requirements.txt`，但没有手动安装 `scenedetect`，导演台的智能分割按钮会报错。`opencv-python-headless` 和 `imageio-ffmpeg` 同理——它们不是 ComfyUI 的标准依赖，但 V2V 和 RV2V 模式的源视频解码、原声抽取功能需要这两个库。

## Takeaways

1. **仓库是工作流副本，不是插件代码。** 装插件去上游 AIMixer 仓库，huangserva 仓库只提供 5 份开箱即用的 JSON。两者配合使用：先装插件，再拖工作流。
2. **导演台节点把官方原子节点链打包成了一个黑盒。** 4 个输入（model、clip、video_vae、audio_vae），6 个输出（images、audio、fps、frame_count、source_images、report），内部分段调度、缓存、时间轴管理全自动。代价是调试粒度变粗——出了问题，你看到的是导演台的运行报告，不是每个原子节点的中间输出。
3. **五种模式本质是同一个节点的不同参数组合。** 切换模式不需要改拓扑，只改 `taskType`、`timelineMode` 和 UNET 文件名。理解了这一点，5 份工作流 JSON 就变成 1 份模板的 5 个预设。
4. **RV2V 视频换人是当前最有吸引力的应用场景，但身份一致性是软约束。** 参考素材 + 提示词的约束力取决于模型能力，导演台只负责把素材送进去。生产环境中需要配合逐段检视和可能的后处理。
5. **4090 48GB 是已验证的基线，但不是入门门槛。** INT8 量化 + 段间显存清理 + 864×480 分辨率，24GB 显存的卡理论上也能跑，只是速度更慢、能处理的段更短。先用最短片段（5 秒 / 124 帧）试错，确认质量后再扩展。