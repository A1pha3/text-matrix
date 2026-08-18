---
title: "Fooocus：基于 SDXL 的零门槛 AI 图像工具，专注提示词与生成"
date: "2026-05-23T13:09:23+08:00"
draft: false
slug: "fooocus-ai-image-generation-focus-on-prompting"
github_repo: "lllyasviel/Fooocus"
source_key: "gh:lllyasviel/Fooocus"
description: "Fooocus 是 lllyasviel 开源的本地 AI 图像生成工具，基于 Stable Diffusion XL（SDXL）。它的取舍是把采样器、CFG、负面提示词这些参数全部收进后台，只留下提示词和风格选择，目标是让非参数型用户也能一键出高质量图。本文拆解它的简化逻辑、生成流程、安装方式和适用边界。"
categories: ["技术笔记"]
tags: ["图像生成", "开源", "SDXL"]
---

# Fooocus：基于 SDXL 的零门槛 AI 图像工具，专注提示词与生成

> **项目地址**：[github.com/lllyasviel/Fooocus](https://github.com/lllyasviel/Fooocus)
>
> **一句话定位**：SD WebUI 把参数全摆在你面前，Fooocus 把它们全藏起来——只留提示词、风格和生成按钮。

## 一句话判断

Fooocus 是 ControlNet 作者 lllyasviel 开源的本地图像生成工具，基于 **Stable Diffusion XL（SDXL）**。它和 SD WebUI、ComfyUI 走的是相反的路：后两者把采样器、CFG 引导系数、LoRA 权重这些参数暴露给你，要求你先成为参数专家；Fooocus 认为这些不该让普通用户操心，于是把一套调好的默认管线焊死在后端，用户界面只剩三件事——写提示词、选风格、点生成。最新稳定版 v2.5.5（2024-08），主仓库进入 LTS（仅修 bug），Stars 约 4 万（2026-08，以仓库为准）。

## 项目概览

| 维度 | 事实 |
|------|------|
| 仓库 | `lllyasviel/Fooocus` |
| 作者 | lllyasviel（ControlNet 作者） |
| 底层模型 | Stable Diffusion XL（SDXL） |
| 协议 | GPL-3.0 |
| 官网 | [github.com/lllyasviel/Fooocus](https://github.com/lllyasviel/Fooocus) |
| 最新版本 | v2.5.5（2024-08）；主仓库处于 LTS 维护状态 |
| GitHub Stars | 约 40k（2026-08，以仓库为准） |
| 最低显存 | 4 GB（NVIDIA） |

## 它到底简化了什么

SD 生态的门槛不在"能不能出图"，而在"出好图要懂多少参数"。SD WebUI 装完只是开始，接下来要面对采样器、步数、CFG、种子、负面提示词，再往下还有 ControlNet 的姿态控制、LoRA 的风格微调、VAE 的色彩还原——每一层都有自己的参数和兼容性要求。

Fooocus 把这些全部内置并预调好：

- 采样器、步数、CFG 在后台按"性能模式"自动选择，界面上不出现。
- 质量标签和负面提示词由内置引擎注入，不需要你背 `masterpiece, best quality`。
- Refiner（精修模型）在采样过程中自动切换，用户无感。

所以它的简化不是"删功能"，而是"替你做了默认决策"。代价也很明确：想要 ComfyUI 那种节点级控制，或 SD WebUI 那种逐参数调试，Fooocus 给不了。它的目标用户是概念设计、社媒配图、电商主图这类"要图，不要参数"的场景。

## 系统地图：一次生成请求如何流过

"写一句提示词，点生成"背后是一整条管线。以生成一张赛博朋克城市夜景为例：

```text
提示词 → 提示词扩展引擎（GPT-2 离线扩写）
      → 注入所选风格的提示词模板与负面提示词
      → SDXL base 模型多步采样
      → （可选）Refiner 精修阶段
      → 输出图像（含放大/重绘等后处理）
```

1. **提示词扩展**：Fooocus 内置一个离线 GPT-2 引擎，把短提示词扩写得更完整。你写 `cyberpunk city at night, neon lights`，它会补上构图、光线、材质的细节描述。
2. **风格注入**：选中的风格预设会往正向/负面提示词里拼入对应模板，相当于一键套用了 SD WebUI 里的成熟 prompt 配方。
3. **采样**：base 模型走完设定的采样步数。性能模式决定步数和采样器组合。
4. **Refiner 切换**：后半程换到精修模型，提升细节质感——用户全程无感，只看到最终结果。

整条管线里，用户唯一要做的决定是"画面里有什么"和"什么风格"。

## 核心特性

### 1. 零配置出图

安装完启动即可用，首次运行自动下载 SDXL 底模。不需要手动装 ControlNet、VAE 或额外模型——这些组件已集成并在后台按默认配置工作。

### 2. 内置提示词引擎

基于 GPT-2 的离线提示词扩展，自动补全描述、处理负面提示词、应用风格模板。不依赖网络，也不会把提示词发给第三方。

### 3. 风格预设

内置上百种风格预设（建筑、摄影、插画、动漫等），一键切换。每种风格是一套完整的提示词模板，省去手动拼 LoRA 和采样参数。

### 4. 性能模式

`Speed`（速度优先）、`Quality`（质量优先）、`Extreme Speed`（极速，适合低显存）三档，对应不同的采样步数与模型设置。想快想慢，点一下切换，不用理解背后的采样器差异。

### 5. 图像输入与后处理

除文生图外，还支持图生图（Image Prompt）、局部重绘（Inpainting）、外绘扩展（Outpainting）和放大（Upscaling），都走同一套"藏参数"的交互。

### 6. 基于 SDXL 的开源生态

可以放自己的 SDXL checkpoint 和 LoRA 到 `models` 目录，社区模型可直接复用。但注意它只认 SDXL 系模型——Flux、SD 3.5 等新架构不在支持范围。

## 安装

官方没有 `pip install fooocus` 这种一键装法。按平台选一种：

### Windows（最简单）

从 [GitHub Releases](https://github.com/lllyasviel/Fooocus/releases) 下载打包版，解压后运行 `run.bat`。首次启动会自动下载 SDXL 底模。

### 从源码运行（Windows / Linux / macOS）

```bash
git clone https://github.com/lllyasviel/Fooocus.git
cd Fooocus
python entry_with_update.py
```

启动后访问 `http://127.0.0.1:7860`。`entry_with_update.py` 会在每次启动时检查并更新依赖。

### 需要留意的两点

- **Python 版本**：官方建议 Python 3.10。更新版本的 Python 可能与它锁定的依赖冲突。
- **RTX 50 系（Blackwell）**：自带的 PyTorch 没有对应 kernel，可能报 `no kernel image is available`。解决方法是把环境里的 PyTorch 升级到 CUDA 12.8 构建：

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
```

### 更新与维护状态

主仓库已宣布进入 LTS（limited long-term support），只修 bug，不再引入新模型架构。社区活跃分支是 [mashb1t/Fooocus（1-Up Edition）](https://github.com/mashb1t/Fooocus)，补了大量修复和易用性改进，新装机可以优先考虑。如果你的场景需要 Flux 或 SD 3.5，直接看它的后继者（如 SD Forge、ComfyUI）。

## 提示词技巧

### 基础写法

```
正向提示词: a cosmic lighthouse at sunset, volumetric lighting, cinematic
风格选择: Cinematic（或 Photorealistic / Anime / Architectural）
点击生成
```

写实景就描述"场景 + 光线 + 构图"，写角色就描述"人物 + 表情 + 服装 + 环境"。Fooocus 的风格预设和扩展引擎会补上剩余细节。

### 让细节更可控

- **加具体对象与动作**：`a red fox sitting on a mossy rock, golden hour` 比 `a fox` 稳定得多。
- **用关键词控制镜头与光线**：`close-up`、`wide shot`、`soft lighting`、`volumetric light` 这类词对画面影响直接。
- **善用"负面提示词"输入框**：虽然默认已注入负面词，但遇到"手指变形""文字乱码"这类问题，可在界面输入框里补 `bad hands, distorted text`。
- **换 checkpoint 换味道**：写实、二次元、插画各有合适的 SDXL 底模，放进 `models/checkpoints` 后下拉选择即可。

## 常见问题

**Q: 和 SD WebUI 有什么区别？**

SD WebUI 把所有参数摊开给你，控制力强但学习成本高；Fooocus 把参数收进后台、预调好默认值，上手最快。需要逐参数调试、插件生态，用 WebUI；只想写提示词出图，用 Fooocus。

**Q: 显存不够怎么办？**

最低 4 GB（NVIDIA）可跑，用 `Extreme Speed` 性能模式、降低分辨率都能缓解。仍 OOM（显存不足）时，换更轻量的 SDXL 底模或关闭 Refiner。

**Q: 能用自己的模型吗？**

可以。SDXL checkpoint 放 `models/checkpoints`，LoRA 放 `models/loras`，启动后在界面选择。注意只支持 SDXL 系，不兼容 SD 1.5 架构的旧模型（部分功能可能不完整）。

**Q: 生成的图像能商用吗？**

取决于你用的底模授权。Fooocus 本身是 GPL-3.0，不限制生成结果商用；但 SDXL 底模的授权条款需要你自己确认，大企业商用尤其要核对。

**Q: 和 Midjourney 比怎么样？**

Midjourney 闭源、按订阅收费，交互确实极简。Fooocus 的交互理念受 Midjourney 启发——专注提示词、隐藏参数——但它是开源、本地、免费，可换模型。质量对标不适用一句"接近某个版本"，本地 SDXL 的实际效果取决于你的底模和提示词投入。不想被订阅绑住、又要本地离线，Fooocus 是更自由的选择。

**Q: 会支持 Flux 或新模型吗？**

主仓库已明确不计划迁移新架构。需要 Flux / SD 3.5，用 mashb1t fork 之外的方案更稳妥。

## 适用边界与采用顺序

**先用起来**：团队或个人需要零培训成本的本地出图、主要做概念设计 / 配图 / 风格探索、显卡是消费级——Fooocus 是最短路径。

**可以等等**：已经在用 SD WebUI / ComfyUI 且工作流稳定，迁移收益不大；需要批量 API 集成或精细管线控制，它也不是好选择。

**别用它**：需要节点级编排（ComfyUI）、需要 SD 1.5 生态的特定功能、需要最新模型架构支持。

从零接入手顺：先跑通第一个提示词，确认出图质量；再试不同风格预设和性能模式；最后按真实工作流把图生图 / 重绘用起来。

## 自测

1. 你之前用过哪个图像生成工具？让你放弃它的点是什么——参数太多、安装复杂、还是质量不稳？
2. Fooocus 和 SD WebUI 的核心差异在哪？你已经会用 WebUI，还有必要换吗？
3. 你的主力出图需求是什么？如果只是偶尔做配图，Fooocus 是否已够用？
4. 如果带团队，你会不会推荐 Fooocus？什么类型的团队适合，什么类型不适合？

## 进阶路径

**阶段一：跑通第一个提示词（当天）**

装好 Fooocus，写 5 个提示词（写实风景、动漫角色、建筑外观、产品展示、抽象艺术），分别在 `Speed` 和 `Quality` 模式下各出一张，感受差异。

**阶段二：把提示词写细（本周）**

挑一个真实场景（如电商主图），写 10 个不同细度的提示词——从 `a vase` 到完整的光线构图描述，看生成结果差多少。目标是建立"提示词细度 → 画面质量"的直觉。

**阶段三：接进你的工作流（本月）**

做内容创作、电商或游戏美术的，把图生图、局部重绘接进真实流程，批量出图、统一风格。记录哪一步卡住、哪个环节的文档不够清楚。

**阶段四：做一次工具选型（下个月）**

拿上面的对比和你的实测，写一页"我们为什么选 Fooocus / WebUI / ComfyUI"给团队。目的不是劝大家换工具，而是把选型依据讲清楚。

---

**相关工具：** [Vimax Agentic Video](/posts/tech/vimax-agentic-video-generation-hku/) · [Supervision](/posts/tech/supervision-computer-vision-toolbox/)
