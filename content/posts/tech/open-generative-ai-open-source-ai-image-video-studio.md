---
title: "Open Generative AI：一站式开源 AI 图片和视频生成平台"
date: 2026-05-17T03:05:00+08:00
slug: "open-generative-ai-open-source-ai-image-video-studio"
description: "Open Generative AI 是开源 AI 图片、视频、口型同步和影院工作室，支持200+模型，提供桌面客户端和网页版，内置本地推理引擎 sd.cpp 和 Wan2GP，无需 API Key 即可离线生成 AI 媒体内容。"
draft: false
categories: ["技术笔记"]
tags: ["Open Generative AI", "AI生成", "图片生成", "视频生成", "开源", "Electron", "Flux", "Kling"]
---

# Open Generative AI：一站式开源 AI 图片和视频生成平台

[Open Generative AI](https://github.com/Anil-matcha/Open-Generative-AI) 是一个免费、开源的 AI 媒体生成套件，覆盖图片生成、视频生成、口型同步（Lip Sync）和影院控制四大场景。项目口号是"The free, open-source alternative to AI Video Platforms"，核心主张是：无内容过滤、无封闭生态、无订阅费用，200+ SOTA 模型开箱即用。

---

## 快速信息卡

| 项目 | 信息 |
|------|------|
| **Stars** | 20,689+ |
| **Forks** | 3,552+ |
| **License** | MIT |
| **语言** | JavaScript (Next.js/Electron) |
| **最后更新** | 2026-06-25 |
| **模型数量** | 200+ |

---

## 学习目标

读完本文后，你应该能够：

1. **理解 Open Generative AI 的核心定位和四大工作室功能**
2. **判断 Open Generative AI 是否适合你的 AI 生成需求**
3. **完成桌面客户端安装并运行第一个生成任务**
4. **配置本地推理引擎（sd.cpp / Wan2GP）**
5. **在需要时使用 Workflow Studio 构建自动化 AI 流水线**

---

## 目录

1. [项目概览](#1-项目概览)
2. [四大工作室](#2-四大工作室)
3. [本地推理：sd.cpp 和 Wan2GP](#3-本地推理sdcpp-和-wan2gp)
4. [架构解析](#4-架构解析)
5. [安装与快速开始](#5-安装与快速开始)
6. [常见问题](#6-常见问题)
7. [自测题](#自测题)
8. [进阶路径](#进阶路径)
9. [总结](#7-总结)

---

## 1. 项目概览

Open Generative AI 提供两种使用形态：

- **桌面客户端**（Electron）：支持 macOS、Windows、Linux，一键安装，本地推理引擎即开即用
- **网页版**（Next.js）：免安装，通过 [dev.muapi.ai/open-generative-ai](https://dev.muapi.ai/open-generative-ai) 直接访问，支持云端 API 调用

**核心特性：**
- 无内容过滤、无 prompt 拦截、无审查机制
- 100% 开源，支持自托管，数据留在本地
- 支持 200+ 模型：Flux、Nano Banana、Kling、Sora、Veo、Midjourney、Seedream 等
- 本地推理：sd.cpp（SD 1.5/SDXL/Z-Image）和 Wan2GP（Flux、Wan 2.2 视频）
- 多参考图输入：部分模型支持同时输入最多 14 张参考图
- 工作流工作室：可视化节点编辑器，链式调用多个 AI 模型

## 2. 四大工作室

### Image Studio

Image Studio 自动在两种模式间切换：

| 模式 | 触发条件 | 模型数量 | 是否需要 Prompt |
|------|----------|----------|----------------|
| Text-to-Image | 无参考图 | 50+ | 必须 |
| Image-to-Image | 上传参考图 | 55+ | 可选 |

主要模型包括 Flux（Kontext Dev、Flux 2）、Nano Banana 2、Seedream 5.0、Ideogram、GPT-4o、Midjourney 等。新增的 MiniMax Image 01 支持单次请求生成 4 张图、1500 字符超长 prompt。

**多图参考输入**是 Image Studio 的一大亮点。部分模型支持最多 14 张参考图同时输入，用于精确控制风格、内容和构图。例如 Nano Banana 2 Edit 支持 14 张、Kling O1 Edit Image 支持 10 张、Flux Kontext Dev I2I 支持 10 张。

### Video Studio

Video Studio 同样采用双模式设计：

| 模式 | 触发条件 | 模型数量 | 是否需要 Prompt |
|------|----------|----------|----------------|
| Text-to-Video | 无起始帧 | 40+ | 必须 |
| Image-to-Video | 上传起始帧 | 60+ | 可选 |

覆盖 Kling、Sora、Veo、Wan、Seedance 2.0、Hailuo、Runway、Midjourney 等主流视频模型。Seedance 2.0 为字节跳动出品，支持 5/10/15 秒时长、多档质量和多比例。Grok Imagine T2V/I2V 来自 xAI，提供有趣/正常/辣味三种模式。

### Lip Sync Studio

口型同步工作室专门解决"让照片说话"或"给视频配音"的需求，基于音频驱动生成口型匹配的视频。有两种输入模式：

- **Portrait Image 模式**：肖像图 + 音频 → 说话视频
- **Video 模式**：已有视频 + 音频 → 口型同步视频

支持 9 个专用模型，涵盖 Infinite Talk、Wan 2.2 Speech to Video、LTX 2.3 Lipsync、LatentSync、Sync Lipsync、Veed Lipsync 等，分辨率最高支持 1080p。

### Cinema Studio

Cinema Studio 提供电影级摄影机参数控制，用于生成具有专业镜头感的图像和视频。支持调节：

- **机身**：8K 数字、Full Frame 数字、70mm 胶片、16mm 胶片等
- **镜头**：Anamorphic、Macro、Cinema Prime、Vintage Prime、Swirl Bokeh 等
- **焦距**：8mm 超广角到 85mm 人像特写
- **光圈**：f/1.4 浅景深到 f/11 深景深

### Workflow Studio

工作流工作室是可视化 AI 流水线编辑器，通过节点图将多个模型串联成自动化管道。用户可以：

- 选用预置模板（社区贡献）
- 使用节点编辑器拖拽构建自定义工作流
- 通过 Playground 表单界面交互式运行
- 调用 Muapi API 以编程方式触发工作流

底层的开源工作流引擎是 [Vibe Workflow](https://github.com/SamurAIGPT/Vibe-Workflow)。

## 3. 本地推理：sd.cpp 和 Wan2GP

桌面客户端内置两个独立的本地推理引擎，用户可根据自身硬件选择。

### sd.cpp（内置）

sd.cpp 是 stable-diffusion.cpp 的 C++ 引擎，随桌面应用一起分发，调用设备原生 GPU：

| 平台 | 加速后端 |
|------|----------|
| macOS Apple Silicon | Metal GPU |
| Linux / Windows | CUDA / Vulkan / ROCm |
| 全平台 | CPU（兜底） |

支持 SD 1.5、SDXL、Z-Image 三类模型。Z-Image（Diffusion Transformer 架构）质量最高但内存需求最大（16GB RAM 推荐）；SD 1.5 最轻量（M2 Mac 约 1-2 秒/step）。

### Wan2GP（自建远程服务器）

Wan2GP 是远程 Gradio 服务器，需要用户自行在配备 NVIDIA/AMD GPU 的机器上部署。桌面客户端作为 HTTP 客户端连接该服务器，传输 prompt 并接收结果。

由于 Wan2GP 的运行时依赖（flash attention、AWQ/GGUF 内核）仅支持 CUDA/ROCm，无法在 Apple Silicon 上运行，因此设计为独立远程进程。支持的模型包括 Flux.1 Dev、Qwen Image、Wan 2.2（文生视频/图生视频）、Hunyuan Video、LTX Video。

## 4. 架构解析

Open Generative AI 是一个基于 Next.js 的 monorepo，关键目录结构：

```
Open-Generative-AI/
├── app/                        # Next.js App Router
│   └── studio/page.js          # 工作室页面 → StandaloneShell
├── components/
│   ├── StandaloneShell.js      # Tab 导航 + API Key 管理（localStorage）
│   └── ApiKeyModal.js          # API Key 输入弹窗
└── packages/
    └── studio/                 # 共享 React 组件库
```

核心交互逻辑：用户在 UI 选择模型和参数 → 组件调用 Muapi API（或本地 sd.cpp CLI）→ 返回生成结果并展示。API Key 存储在浏览器 `localStorage` 中，仅发送给 Muapi，不经过任何第三方服务器。

## 5. 安装与快速开始

### 桌面客户端（推荐）

从 [Releases 页面](https://github.com/Anil-matcha/Open-Generative-AI/releases) 下载对应平台的安装包：

| 平台 | 安装包 |
|------|--------|
| macOS Apple Silicon | DMG (arm64) |
| macOS Intel | DMG (x64) |
| Windows | EXE 安装包 |
| Linux | AppImage / .deb |

macOS 首次启动需执行：

```bash
xattr -cr "/Applications/Open Generative AI.app"
```

然后在 Applications 中右键打开。

### 开发者从源码构建

```bash
# 需要包含子模块
git clone --recurse-submodules https://github.com/Anil-matcha/Open-Generative-AI.git
cd Open-Generative-AI

# 必须运行 setup 构建 workspace 包
npm run setup

# 启动桌面客户端（Electron）
npm run electron:dev

# 或启动网页版（Next.js）
npm run dev
```

**注意**：`npm run setup` 是必须的——仅 `npm install` 不足以构建 workspaces，`studio`、`workflow`、`agents` 等包需要在 dev 脚本前完成构建。

### 本地推理验证（Mac）

sd.cpp 安装正确后，可通过命令行直接验证 Metal GPU 是否被调用：

```bash
APP_DATA="$HOME/Library/Application Support/open-generative-ai/local-ai"

# 下载 SD 1.5 测试模型
curl -L -o "$APP_DATA/models/DreamShaper_8_pruned.safetensors" \
  "https://huggingface.co/Lykon/DreamShaper/resolve/main/DreamShaper_8_pruned.safetensors"

# 运行推理
DYLD_LIBRARY_PATH="$APP_DATA/bin" "$APP_DATA/bin/sd-cli" \
  -m "$APP_DATA/models/DreamShaper_8_pruned.safetensors" \
  -p "a serene mountain lake at sunrise, oil painting" \
  -o /tmp/sd15-test.png \
  --steps 12 -H 512 -W 512 --cfg-scale 7.5 --seed 42 \
  --sampling-method euler_a
```

健康输出应显示 `VRAM 1969.78MB, RAM 0.00MB (Metal-backed)`。如果 `VRAM` 为 0，则说明回退到了 CPU，需检查 Metal dylib 是否正确加载。

## 6. 常见问题

### macOS 无法打开应用

执行 `xattr -cr "/Applications/Open Generative AI.app"` 后右键打开即可。

### Ubuntu 24.04 AppImage 启动失败

Ubuntu 24.04 默认启用 `apparmor_restrict_unprivileged_userns`，会阻止 Chromium 的用户命名空间沙箱。安装 `.deb` 包（自带 AppArmor profile）或执行：

```bash
sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0
```

### 桌面客户端与网页版的功能差异

本地推理（sd.cpp、Wan2GP）仅在桌面客户端可用；网页版依赖云端 API 调用，始终需要 Muapi API Key。

### Z-Image 在 8GB Mac 上挂起

Z-Image 模型需要约 7.4GB 权重 + 2.4GB 计算缓冲区，基础 8GB M 系列 Mac 无法承载，应使用 SD 1.5 系列模型。

---

## 自测题

1. **Open Generative AI 不支持以下哪项功能？**
   - A. 图片生成
   - B. 视频生成
   - C. 音频生成
   - D. 口型同步
   - **答案：C**

2. **Image Studio 的多图参考输入最多支持几张参考图？**
   - A. 5 张
   - B. 10 张
   - C. 14 张
   - D. 20 张
   - **答案：C**

3. **sd.cpp 在 macOS Apple Silicon 上使用哪种加速后端？**
   - A. CUDA
   - B. Metal GPU
   - C. ROCm
   - D. Vulkan
   - **答案：B**

4. **Wan2GP 为什么设计为远程服务器？**
   - A. 因为代码过于复杂
   - B. 因为运行时依赖仅支持 CUDA/ROCm，无法在 Apple Silicon 上运行
   - C. 因为需要多用户访问
   - D. 因为需要高速网络
   - **答案：B**

5. **Open Generative AI 的 License 是什么？**
   - A. Apache-2.0
   - B. GPL 3.0
   - C. MIT
   - D. BSD 3-Clause
   - **答案：C**

---

## 进阶路径

1. **基础使用**：下载桌面客户端，安装后运行第一个图片生成任务（Flux 或 SD 1.5）。
2. **本地推理**：配置 sd.cpp 引擎，在 Mac 上实现本地图片生成（无需 API Key）。
3. **远程 Wan2GP**：在配备 NVIDIA GPU 的服务器上部署 Wan2GP，从桌面客户端远程调用。
4. **Workflow Studio**：使用可视化节点编辑器构建自定义 AI 流水线，实现多模型串联自动化。

---

## 7. 总结

Open Generative AI 是一个功能全面的开源 AI 媒体生成平台，优势在于：

- **无审查**：无 prompt 过滤，适合需要创作自由的场景
- **200+ 模型集成**：覆盖图片、视频、口型同步，头部模型均有覆盖
- **本地优先**：sd.cpp 引擎让 AI 生成不再依赖云端，本地即可出高质量图
- **自托管**：数据不经过第三方服务器，完全可控

其定位介于 Midjourney/Runway 等封闭平台与纯 API 调用之间——提供了一个开箱即用的客户端体验，同时保留了开源定制和自托管的灵活性。适合不想手动拼装 API、但又希望拥有数据控制权的创作者和开发者。