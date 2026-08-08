---
title: "ComfyUI：用节点图驱动 AI 内容创作的模块化引擎"
date: 2026-08-09T03:22:48+08:00
slug: "comfyui-node-graph-engine"
github_repo: "Comfy-Org/ComfyUI"
source_key: "gh:Comfy-Org/ComfyUI"
description: "ComfyUI 是一个基于节点图界面的 AI 内容创作引擎，支持图像、视频、3D、音频等多种模态的模型编排。本文解析其节点图架构设计、模型支持范围与本地运行能力。"
draft: false
categories: ["技术笔记"]
tags: ["ComfyUI", "AI图像生成", "节点图", "扩散模型", "开源"]
---

## 项目定位

[ComfyUI](https://github.com/Comfy-Org/ComfyUI) 把扩散模型（Diffusion Model）的推理流程拆成可视化节点，让用户通过连线编排图像生成、视频合成、3D 重建等工作流，而不必写代码。截至本文写作时，项目在 GitHub 上获得超过 12.4 万 Star，用 Python 编写，以 GPL-3.0 许可发布。

它的核心价值不在"又提供了一个 GUI"，而在于把模型推理的每一步——加载检查点（Checkpoint）、文本编码（Text Encoding）、采样（Sampling）、VAE 解码——都暴露为可组合、可复用的节点。这意味着同一个工作流可以快速切换底层模型（从 SDXL 换到 Flux.2 只需替换加载节点），也可以把完整工作流序列化为 JSON 供 API 调用。

## 节点图架构：从画布到推理

ComfyUI 的界面是一张无限画布。用户从左侧搜索面板拖出节点，用连线（Wire）把上游节点的输出端口连到下游节点的输入端口，形成一张有向无环图（DAG）。按下 `Ctrl+Enter` 后，ComfyUI 对这张图做拓扑排序，依次执行每个节点。

一个典型的文生图工作流长这样：

1. **Load Checkpoint** 节点加载 `.safetensors` 模型文件，输出 MODEL、CLIP、VAE 三个对象
2. **CLIP Text Encode** 节点接收 CLIP 对象和提示词文本，输出条件向量（Conditioning）
3. **Empty Latent Image** 节点生成一张空白潜空间图像，指定分辨率
4. **KSampler** 节点接收 MODEL、正向条件、负向条件、潜空间图像，执行扩散采样
5. **VAE Decode** 节点把采样后的潜空间数据解码为像素图像
6. **Save Image** 节点保存结果到磁盘

每个节点只需声明输入类型和输出类型，ComfyUI 自动校验连线合法性——类型不匹配的端口无法连接。这种设计让复杂工作流也保持可读性。

## 模型支持：广度与分层

ComfyUI 原生支持的模型覆盖了当前主流的生成模型家族，按模态大致分为：

| 模态 | 代表模型 |
|------|---------|
| 图像生成 | Stable Diffusion 1.5 / SDXL / SD3.5、Flux.1 / Flux.2、Qwen Image、Z-Image、Hunyuan Image 2.1 |
| 图像编辑 | Flux Kontext、Qwen Image Edit、OmniGen2 |
| 视频生成 | Wan 2.1/2.2、LTX-Video 2/2.3、HunyuanVideo 1.5 |
| 音频生成 | ACE-Step 1.5、Stable Audio 3 |
| 3D 与视觉 | Hunyuan3D 2.1、TripoSplat、SAM 3/3.1、Depth Anything 3 |
| 文本生成 | Gemma 3/4、Qwen3/Qwen3.5（含多模态输入） |

除了开源模型，ComfyUI 还通过 API Nodes 接入闭源模型（如 Nano Banana、Seedance、Hunyuan3D），不过这需要联网且可能产生费用。如果只想完全离线使用，启动时加 `--disable-api-nodes` 参数即可屏蔽所有付费 API 节点。

模型文件不限于完整检查点，也支持分散加载：Text Encoder、VAE、LoRA、ControlNet、Adapter、Upscaler 都可以作为独立节点接入，按需组合。`extra_model_paths.yaml` 配置文件允许指定额外的模型目录，方便与 Automatic1111 WebUI 等其他工具共享模型文件。

## 本地执行与资源管理

ComfyUI 的执行层有几个值得注意的工程设计：

- **异步队列**：生成任务排队执行，不阻塞 UI 线程，提交后可以继续编辑工作流
- **部分图重执行**：修改某个节点的参数后，只需重新执行受影响的子图，不必从头跑整个工作流
- **显存管理**：自动检测可用 VRAM，在 GPU 和 CPU 之间做模型卸载（Offload），支持在显存有限的设备上运行大模型
- **量化模型**：支持 FP8、GGUF 等量化格式，降低显存占用

GPU 支持方面覆盖 NVIDIA、AMD、Intel 以及 Apple Silicon（通过 MPS 后端）和华为昇腾（Ascend）。最低 PyTorch 版本要求 2.7，但官方建议使用最新版本以获得完整优化。

## 安装方式

ComfyUI 提供三种安装路径：

**桌面应用（推荐新手）**：从 [comfy.org/download](https://www.comfy.org/download) 下载，支持 Windows 和 macOS，安装过程最简单。

**Windows 便携包**：从 GitHub Releases 下载 `.7z` 压缩包，解压后直接运行，自带 Python 3.13 和 PyTorch。分 NVIDIA、AMD、Intel 三个版本。

**手动安装（全平台）**：

```bash
git clone https://github.com/Comfy-Org/ComfyUI
cd ComfyUI
pip install -r requirements.txt
python main.py
```

或者使用官方 CLI 工具：

```bash
pip install comfy-cli
comfy install
```

安装后默认监听 `http://127.0.0.1:8188`，浏览器打开即可看到节点图编辑器。

## 工作流的保存与复用

ComfyUI 的工作流以 JSON 格式保存，包含节点类型、参数和连线关系。值得注意的一个能力是：生成的图片文件（PNG）内嵌了完整的工作流元数据，可以直接把图片拖回编辑器恢复整个工作流（包括模型路径、提示词、采样参数和随机种子）。这对于复现和分享生成结果非常实用。

此外，Subgraph 功能允许把一组节点封装成单个自定义节点，在多个工作流中复用。App Mode 则把复杂工作流暴露为简化 UI，让非技术用户只需填写几个输入框就能使用。

## 版本节奏

ComfyUI 采用周更发布周期（通常在周一），但大版本可能因模型适配或重大改动而调整。当前最新版本为 v0.31.0（2026 年 8 月 8 日发布）。

项目由三个相互关联的仓库构成：

- **ComfyUI Core**：推理引擎和节点系统（即本文介绍的仓库）
- **Comfy Desktop**：桌面应用封装
- **ComfyUI Frontend**：Web 前端界面，定期合并进 Core 仓库

## 适用边界

ComfyUI 适合需要对生成过程有精细控制的用户——调参、切换模型、组合 ControlNet、设计复杂工作流是它的核心使用场景。如果只是想输入提示词快速出图，Automatic1111 WebUI 或各模型的官方 Demo 可能更直接。

自定义节点生态（Custom Nodes）是 ComfyUI 的另一大优势，社区贡献了大量扩展节点，支持后处理、动画、批量处理等场景。但需要注意的是，非稳定版本的 Core 可能与部分自定义节点不兼容，建议在稳定版上构建生产工作流。

---

*项目地址：[github.com/Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) · 官网：[comfy.org](https://www.comfy.org/) · 许可证：GPL-3.0*
