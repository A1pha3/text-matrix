---
title: "Open Generative AI：无审查的开源 AI 图像视频生成工作室"
slug: "open-generative-ai-studio-guide"
description: "Open Generative AI 是一个免费、开源、无审查的 AI 图像、视频和唇同步生成工作室，支持 200+ 先进模型，包括 Flux、Midjourney、Kling、Sora 等。它是 Higgsfield AI、Freepik、Krea、Openart AI 的开源替代品。"
date: "2026-04-24T11:42:00+08:00"
categories: ["技术笔记"]
tags: ["AI图像", "AI视频", "开源工具", "唇同步", "Midjourney"]
---

# Open Generative AI：无审查的开源 AI 图像视频生成工作室

> **项目地址**：[github.com/Anil-matcha/Open-Generative-AI](https://github.com/Anil-matcha/Open-Generative-AI)
>
> **核心理念**：无内容过滤、无封闭生态、无订阅费用——让创意自由流动。

## 项目概览

Open Generative AI 是一个免费、开源、无审查的 AI 图像、视频、电影和唇同步生成工作室。它是 Higgsfield AI、Freepik、Krea、Openart AI 的开源替代品。

**核心特点**：
- **无审查** —— 无内容过滤器、无提示词拒绝、无护栏限制
- **免费开源** —— 无订阅费、无供应商锁定
- **自托管** —— 数据保留在本地，完全控制创意内容
- **200+ 模型** —— 文本生成图像、图像生成图像、文本生成视频、图像生成视频、唇同步

## 在线体验

**托管版本**：[https://dev.muapi.ai/open-generative-ai](https://dev.muapi.ai/open-generative-ai)

无需安装，直接在浏览器中使用所有四个工作室（图像、视频、唇同步、电影）。注册免费账户即可开始生成。托管版本始终使用最新模型。

## 桌面应用

### 下载安装

| 平台 | 下载链接 |
|------|----------|
| macOS Apple Silicon (M1/M2/M3/M4) | [Open Generative AI-1.0.2-arm64.dmg](https://github.com/Anil-matcha/Open-Generative-AI/releases/download/v1.0.2/Open.Generative.AI-1.0.2-arm64.dmg) |
| macOS Intel (x64) | [Open Generative AI-1.0.2.dmg](https://github.com/Anil-matcha/Open-Generative-AI/releases/download/v1.0.2/Open.Generative.AI-1.0.2.dmg) |
| Windows (x64 + ARM64) | [Open Generative AI Setup 1.0.2.exe](https://github.com/Anil-matcha/Open-Generative-AI/releases/download/v1.0.2/Open.Generative.AI.Setup.1.0.2.exe) |
| Linux (Ubuntu x64) | 使用 `npm run electron:build:linux` 本地构建 |

### macOS 安装说明

由于应用未经 Apple 公证，macOS Gatekeeper 会在首次启动时阻止它。按照以下步骤操作：

**第一步**：将 DMG 中的应用拖到 `/Applications`

**第二步**：打开终端并运行：
```bash
xattr -cr "/Applications/Open Generative AI.app"
```

**第三步**：右键点击 `/Applications` 中的应用 → 点击 **Open** → 在对话框中再次点击 **Open**

### Windows 安装

Windows SmartScreen 可能会显示警告，因为安装程序未经代码签名：

1. 点击 SmartScreen 对话框上的 **更多信息**
2. 点击 **仍要运行**

应用会静默安装到 `%LocalAppData%`，并创建开始菜单快捷方式。

## 核心功能

### 🖼️ 图像工作室

生成图像有两种模式：

| 模式 | 触发条件 | 模型数量 | 提示词 |
|------|----------|----------|--------|
| **文生图** | 默认（无图像） | 50+ 模型 | 必须 |
| **图生图** | 上传参考图像 | 55+ 模型 | 可选 |

支持的模型包括 Flux、Nano Banana 2、Seedream 5.0、Ideogram、GPT-4o、Midjourney 等。

### 🎬 视频工作室

从文本提示生成视频（40+ 模型）或动画化起始帧图像（60+ 模型）。

### 💋 唇同步工作室

使用音频动画化肖像图像或同步现有视频的唇部动作。9 个专用模型支持两种模式：肖像图像 + 音频 → 说话视频，和视频 + 音频 → 唇同步视频。

### 🎬 电影工作室

用于逼真电影镜头的界面，具有专业相机控制（镜头焦距、光圈）。

### 🔧 工作流工作室

可视化和运行多步骤 AI 管道。连接图像、视频和音频模型为自动化流程。浏览社区模板，使用节点编辑器创建自己的流程，并通过交互式 playground 运行。

### ⚡ 本地模型推理（仅限桌面应用）

桌面应用包含内置本地生成引擎，由 [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) 提供支持——无需 API 密钥即可完全在本地生成图像。

#### 支持的本地模型

| 模型 | 类型 | 大小 | 速度 |
|------|------|------|------|
| **Z-Image Turbo** ⚡ | Diffusion Transformer | 2.5 GB + 2.7 GB aux | 8步 turbo |
| **Z-Image Base** ⚡ | Diffusion Transformer | 3.5 GB + 2.7 GB aux | 50步高质量 |
| **Dreamshaper 8** | SD 1.5 | 2.1 GB | 20步通用 |
| **Realistic Vision v5.1** | SD 1.5 | 2.1 GB | 25步逼真 |
| **Anything v5** | SD 1.5 | 2.1 GB | 20步动漫/插画 |
| **SDXL Base 1.0** | SDXL | 6.9 GB | 30步高分辨率 |

> **Z-Image 模型**需要两个共享辅助文件（下载一次，多个模型共享）：
> - **Qwen3-4B 文本编码器** — 2.4 GB
> - **FLUX VAE** — 335 MB

### 硬件要求

- 支持 CPU（所有平台）和 **Metal GPU**（macOS Apple Silicon — M1/M2/M3/M4）
- Metal GPU 加速内置于 macOS 桌面版——显著快于纯 CPU
- 推荐：16 GB RAM（Z-Image 模型需要 7.4 GB 权重 + 2.4 GB 计算缓冲）

## 新增模型

| 模型 | 类型 | 关键特性 |
|------|------|----------|
| **Nano Banana 2** | 文生图 | Gemini 3.1 Flash Image · 1K/2K/4K 分辨率 · Google Search 增强 · aspect ratio `auto` |
| **Nano Banana 2 Edit** | 图生图 | 最多 **14 张参考图像** · 1K/2K/4K 分辨率 |
| **Seedream 5.0** | 文生图 | 字节跳动 · 质量 basic/high · 8 种宽高比 · 最高 4K |
| **Seedream 5.0 Edit** | 图生图 | 字节跳动 · 自然语言风格迁移 |
| **MiniMax Image 01** | 文生图 | MiniMax · 8 种宽高比 · 每请求最多 4 张图 · 1500 字符提示词 |

## 为什么选择 Open Generative AI？

| 特性 | Open Generative AI | 其他平台 |
|------|-------------------|---------|
| **内容审查** | 无限制 | 有过滤和拒绝 |
| **费用** | 免费开源 | 订阅制 |
| **部署方式** | 自托管 | 仅云端 |
| **模型数量** | 200+ | 通常有限 |
| **多图输入** | 最多 14 张参考图 | 通常 1-2 张 |

## 适用场景

- 需要无审查 AI 生成工具的创意工作者
- 希望完全控制数据和创意的开发者
- 需要本地运行（离线）能力的用户
- 想要探索多种 AI 模型的用户
- 需要自动化媒体管道的开发者（通过 API）

## 总结

Open Generative AI 是一个功能强大的开源 AI 生成工具，它提供了无审查、无限制的创意体验。无论你是设计师、开发者还是创意爱好者，都可以从中受益。其对多种模型的支持、本地推理能力和工作流自动化功能，使其成为一个全面且灵活的 AI 创作平台。

## 延伸阅读

- [在线体验](https://dev.muapi.ai/open-generative-ai)
- [GitHub 仓库](https://github.com/Anil-matcha/Open-Generative-AI)
- [Awesome GPT-Image-2 API Prompts](https://github.com/Anil-matcha/Awesome-GPT-Image-2-API-Prompts)
- [Generative-Media-Skills](https://github.com/SamurAIGPT/Generative-Media-Skills)

---

*本文由钳岳星君撰写，基于 GitHub 仓库 [Anil-matcha/Open-Generative-AI](https://github.com/Anil-matcha/Open-Generative-AI) 的 README。*
