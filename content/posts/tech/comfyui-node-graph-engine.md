---
title: "ComfyUI：用节点图驱动 AI 内容创作的模块化引擎"
date: 2026-08-09T03:22:48+08:00
lastmod: 2026-09-29
slug: "comfyui-node-graph-engine"
github_repo: "Comfy-Org/ComfyUI"
source_key: "gh:Comfy-Org/ComfyUI"
description: "ComfyUI 是一个基于节点图界面的 AI 内容创作引擎，支持图像、视频、3D、音频等多种模态的模型编排。本文解析其节点图架构设计、模型支持范围与本地运行能力。"
draft: false
categories: ["技术笔记"]
tags: ["ComfyUI", "AI图像生成", "节点图", "扩散模型", "开源"]
---

## 先看结论

ComfyUI 解决的不是"给扩散模型加个界面"，而是把一次生图从"一段跑完就扔的脚本"变成"一张可编辑、可复用、可分享的图"。它把模型推理的每一步——加载检查点、文本编码、采样、VAE 解码——都拆成独立节点，用户连线编排，系统按拓扑序执行。界面只是入口，真正的工作发生在节点之间的数据流上。

这套设计带来三个直接结果：

- 换模型只动一个节点：从 SDXL 换到 Flux.2，替换加载节点即可，其余结构不动
- 工作流可序列化为 JSON：既能保存复用，也能通过 API 远程驱动
- 改参数只重跑受影响子图，不必整个流程从头再来

[ComfyUI](https://github.com/Comfy-Org/ComfyUI) 用 Python 编写，以 GPL-3.0 许可发布，截至 2026 年 9 月 29 日在 GitHub 上获得约 13.5 万 Star。展开细节之前，先把它拆成四层，后面各节都对应其中一层：

| 层级 | 负责什么 | 典型组件 |
|------|---------|---------|
| 前端画布 | 节点编排、连线校验、参数编辑 | Web 前端、节点类型注册表 |
| 后端执行 | 队列调度、拓扑排序、部分图重执行 | 执行器、异步队列 |
| 模型层 | 模型加载、文本编码、采样、解码 | Load Checkpoint、KSampler、VAE Decode |
| 生态层 | 自定义节点、模板、App Mode、API | Custom Nodes、工作流模板 |

## 节点图架构：从画布到推理

ComfyUI 的界面是一张无限画布。用户从搜索面板拖出节点，用连线（Wire）把上游节点的输出端口连到下游节点的输入端口，形成一张有向无环图（DAG）。按下 `Ctrl+Enter` 后，系统对这张图做拓扑排序，依次执行每个节点。

每个节点只声明输入类型和输出类型，连线合法性由系统自动校验——类型不匹配的端口连不上。这一步把"参数传错"这类错误从运行时提前到了编辑时。复杂工作流因此保持可读：看得见的数据流，就是执行顺序。

一个典型的文生图工作流：

1. **Load Checkpoint** 加载 `.safetensors` 模型文件，输出 MODEL、CLIP、VAE 三个对象
2. **CLIP Text Encode** 接收 CLIP 对象和提示词文本，输出条件向量（Conditioning）
3. **Empty Latent Image** 生成一张空白潜空间图像，指定分辨率
4. **KSampler** 接收 MODEL、正向条件、负向条件、潜空间图像，执行扩散采样
5. **VAE Decode** 把采样后的潜空间数据解码为像素图像
6. **Save Image** 保存结果到磁盘

## 一条任务如何流过系统

以"把 SDXL 工作流换成 Flux.2 重新出图"为例，看各层如何配合：

1. 用户在画布上把 Load Checkpoint 节点从 SDXL 检查点切换为 Flux.2 检查点
2. 前端把改动提交给后端，后端重新校验下游连线的类型兼容性（Flux 系模型通常不需要负面条件）
3. 拓扑排序后只重跑受影响子图——从新的 Load Checkpoint 开始，经文本编码、采样到 VAE 解码，其余节点不动
4. 结果图片保存，同时把整张工作流图（模型路径、提示词、采样参数、随机种子）写进 PNG 元数据

这条路径串起了三套机制：连线校验保证图始终合法，部分图重执行避免全量重跑，PNG 元数据让结果可以完整复现。

## 模型支持：广度与分层

ComfyUI 原生支持的模型覆盖当前主流生成模型家族，按模态大致分为（官方口径为代表名单，完整支持随版本持续扩充）：

| 模态 | 代表模型 |
|------|---------|
| 图像生成 | Stable Diffusion 1.5 / SDXL / SD3.5、Flux.1 / Flux.2、Qwen Image（v0.37.0 起支持 2.1）、Z-Image、Hunyuan Image 2.1、HiDream、Ideogram 4、Krea 2 |
| 图像编辑 | Flux Kontext、Flux.2 Klein、Qwen Image Edit、OmniGen2、HiDream E1.1 |
| 视频生成 | Wan 2.1 / 2.2、LTX-Video 2 / 2.3、HunyuanVideo 1.5、CogVideoX、Cosmos Predict2、Mochi |
| 音频生成 | ACE-Step 1.5、Stable Audio 3、MiniMax Music 3、YuE 2 |
| 3D 与视觉 | Hunyuan3D 2.1、TripoSplat、SAM 3 / 3.1、Depth Anything 3、MoGe 3、SeedVR2、SUPIR |
| 文本生成 | Gemma 3 / 4、Qwen3 / Qwen3.5 / Qwen3-VL（含多模态输入） |

闭源模型走另一条路：Partner Nodes（API 节点）按调用计费接入，名单包括 Nano Banana、Seedance、Kling、Runway、Wan 2.7、Hunyuan3D 等，`comfy_api_nodes/` 目录下有四十多个服务接入文件。这些节点需要联网且可能产生费用；想完全离线使用，启动时加 `--disable-api-nodes` 参数即可——它会同时阻止加载所有 API 节点和前端访问互联网。

模型文件不限于完整检查点，也支持分散加载：Text Encoder、VAE、LoRA、ControlNet、Adapter、Upscaler 都能作为独立节点接入，按需组合。`extra_model_paths.yaml` 配置允许指定额外的模型目录，方便与 Automatic1111 WebUI 等其他工具共享模型文件。

## 本地执行与资源管理

执行层有几个关键设计：

- **异步队列**：生成任务排队执行，不阻塞 UI 线程，提交后可以继续编辑工作流
- **部分图重执行**：只重新执行受影响的子图，参数微调不必从头跑
- **异步权重卸载**：权重按需在内存与显存之间流动，由独立数据流搬运（NVIDIA 卡默认开启，默认 2 条流，可用 `--async-offload` 调节）。README 的口径是 4 GB 显存加 8 GB 内存即可较快运行最大的开源模型
- **磁盘直读**：`--fast-disk` 让权重跳过内存驻留、直接从 NVMe 流式读取；v0.37.0 起检测到快盘会自动启用
- **量化**：原生量化系统支持 FP8 / INT8，并在 `QUANTIZATION.md` 里定义了分层量化元数据标准，让第三方量化工具的检查点能被直接识别；GGUF 格式则由社区节点 ComfyUI-GGUF 提供

显存卸载把本地运行的门槛从"显存够大"压到"显存够用"。GPU 覆盖 NVIDIA、AMD、Intel、Apple Silicon（M1–M4）、华为昇腾（Ascend），README 另附寒武纪 MLU 与天数智芯 Iluvatar Corex 的安装指南。最低 PyTorch 版本要求 2.7，官方建议用更新版本以启用完整优化；NVIDIA 20 系及以上还需要 cu130 以上的 PyTorch。

## 安装方式

三种安装路径：

**桌面应用（推荐新手）**：从 [comfy.org/download](https://www.comfy.org/download) 下载，支持 Windows 和 macOS（Apple Silicon），安装过程最简单。

**Windows 便携包**：从 GitHub Releases 下载 `.7z` 压缩包，解压后直接运行，自带 Python 3.13 和 PyTorch（CUDA 13.0）。分四个版本：NVIDIA（20 系及以上）、AMD、Intel，以及面向 10 系及更老显卡的 cu126 + Python 3.12 版。

**手动安装（全平台）**：

```bash
git clone https://github.com/Comfy-Org/ComfyUI
cd ComfyUI
pip install -r requirements.txt
python main.py
```

Python 3.13 支持最完善；3.14 可以运行，但部分自定义节点的依赖可能出兼容问题。也可以用官方 CLI：

```bash
pip install comfy-cli
comfy install
```

安装后默认监听 `http://127.0.0.1:8188`，浏览器打开即可看到节点图编辑器。

## 工作流的保存与复用

工作流以 JSON 格式保存，包含节点类型、参数和连线关系。一个实用能力：生成的 PNG 文件内嵌完整工作流元数据，把图片拖回编辑器就能恢复整个工作流（包括模型路径、提示词、采样参数和随机种子），复现和分享都很直接。

输出格式上，除常规 8-bit 图像外，还支持 16-bit PNG、32-bit EXR、10-bit AVIF 以及 HDR 视频，满足后期制作对位深的要求。

此外，Subgraph 功能允许把一组节点封装成单个自定义节点，在多个工作流中复用；App Mode 则把复杂工作流暴露为简化界面，非技术用户填几个输入框就能使用。

## 版本节奏

ComfyUI 按周节奏发布（目标周一），稳定大版约每两周一个，补丁版主要承载回迁到稳定版的修复——具体节奏随模型发布调整。截至 2026 年 9 月 29 日，最新稳定版为 v0.37.0（2026 年 9 月 21 日发布），此前三版为 v0.34.0（8 月 26 日）、v0.35.0（9 月 9 日）、v0.36.0（9 月 15 日）。

项目由三个相互关联的仓库构成：

- **ComfyUI Core**：推理引擎和节点系统（即本文介绍的仓库）
- **[Comfy Desktop](https://github.com/Comfy-Org/Comfy-Desktop)**：桌面应用封装，跟随最新稳定版 Core 发布
- **[ComfyUI Frontend](https://github.com/Comfy-Org/ComfyUI_frontend)**：Web 前端界面，每两周左右合并进 Core 仓库

## 适用边界与采用顺序

ComfyUI 适合需要对生成过程精细控制的人：调参、切换模型、组合 ControlNet、设计复杂工作流。如果只是输入提示词快速出图，Automatic1111 WebUI 或模型官方 Demo 更直接；如果连本地环境都不想搭，直接用在线平台。

按场景决定先上哪套：

- **本地创作者**：从桌面应用或便携包开始，跑官方模板，再逐步引入自定义节点
- **开发者**：用手动安装，通过 API 把工作流嵌进自己的服务
- **只做轻量尝试**：先别装，用云端在线版验证工作流是否满足需求，再决定是否自建

自定义节点生态（Custom Nodes）是另一大优势，社区贡献了大量扩展节点，覆盖后处理、动画、批量处理等场景。节点管理也已收编进主仓库：ComfyUI-Manager 并入 Core 后，装上 manager 依赖（`pip install -r manager_requirements.txt`）、用 `--enable-manager` 启动，就能在界面里安装和更新自定义节点。但非稳定版本 Core 可能与部分自定义节点不兼容，生产工作流建议钉在稳定版上。

## 常见问题

**想完全离线、不产生 API 费用？** 启动参数加 `--disable-api-nodes`，付费 API 节点会被整体屏蔽，前端也不再联网。

**显存不够跑大模型？** NVIDIA 卡上异步权重卸载默认已开启；仍不够就依次尝试：用 FP8 量化版本（GGUF 版本装社区节点 ComfyUI-GGUF）、降低输出分辨率、用分块（Tiled）VAE 解码。

**老显卡（10 系及更早）能用吗？** 用 cu126 + Python 3.12 版便携包；新卡不要用这个版本。

**想和 A1111 WebUI 共用模型文件？** 在 `extra_model_paths.yaml` 里把模型目录指到同一个路径，两边都能读到。

**浏览器打不开页面？** 默认端口是 8188，先确认端口没被占用，再检查服务是否真的启动成功（终端最后几行会打印监听地址）。

**自定义节点装不上或报错？** 多数情况是依赖冲突或版本不兼容，先看该节点的 README 要求的 Python / PyTorch 版本再对照自己环境——Python 3.14 上出问题时可退回 3.13 或 3.12；确认在稳定版 ComfyUI 上运行。

## 结尾判断

回到开头那句判断：ComfyUI 把"推理管线"变成了"可编辑对象"。节点图让它可组合，JSON 序列化让它可复用，PNG 元数据让它可复现，异步权重卸载再把硬件门槛压到主流办公机的水平。要不要自建，取决于你是否需要这份控制力；需要，它就是当前最完整的开源选择之一。

---

*项目地址：[github.com/Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) · 官网：[comfy.org](https://www.comfy.org/) · 许可证：GPL-3.0*

## 参考来源与口径说明

- Star 数、许可证、最新版本：GitHub API，2026-09-29 读数（135,413 Star；最新稳定版 v0.37.0，2026-09-21 发布）
- 模型支持名单、运行要求、快捷键：仓库 README（main 分支，2026-09-29 读取）
- 量化系统与启动参数：仓库 `QUANTIZATION.md`、`comfy/cli_args.py`、`comfy/model_management.py`；GGUF 加载不在主仓库代码中，由社区节点 [city96/ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF) 提供
- API 节点服务商名单：仓库 `comfy_api_nodes/` 目录（2026-09-29）
