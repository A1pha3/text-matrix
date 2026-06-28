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

## 学习目标

读完本文，你将能够：

- 说清 Open Generative AI 和其他 AI 图像/视频平台的差异
- 在 macOS 或 Windows 上完成桌面应用安装
- 用四个工作室（图像、视频、唇同步、电影）生成内容
- 在本地跑起 Z-Image 或 SD 1.5 模型，不依赖任何 API 服务
- 给工作室接入新模型

## 目录

1. [项目概览](#项目概览)
2. [在线体验](#在线体验)
3. [桌面应用安装](#桌面应用)
4. [核心功能](#核心功能)
5. [本地模型推理](#本地模型推理)
6. [新增模型](#新增模型)
7. [为什么选择 Open Generative AI？](#为什么选择-open-generative-ai)
8. [适用场景](#适用场景)
9. [常见问题](#常见问题)
10. [自测题](#自测题)
11. [进阶路径](#进阶路径)
12. [总结](#总结)

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
| **Z-Image Turbo** ⚡ | Diffusion Transformer | 2.5 GB + 2.7 GB aux | 8 步 turbo |
| **Z-Image Base** ⚡ | Diffusion Transformer | 3.5 GB + 2.7 GB aux | 50 步高质量 |
| **Dreamshaper 8** | SD 1.5 | 2.1 GB | 20 步通用 |
| **Realistic Vision v5.1** | SD 1.5 | 2.1 GB | 25 步逼真 |
| **Anything v5** | SD 1.5 | 2.1 GB | 20 步动漫/插画 |
| **SDXL Base 1.0** | SDXL | 6.9 GB | 30 步高分辨率 |

> **Z-Image 模型**需要两个共享辅助文件（下载一次，多个模型共享）：
> - **Qwen3-4B 文本编码器** — 2.4 GB
> - **FLUX VAE** — 335 MB

#### 硬件要求

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

## 常见问题

### Q1：Open Generative AI 真的完全免费吗？

是的。项目采用开源许可证，你可以免费使用、修改和分发。在线版本需要注册免费账户，但生成额度未明确限制。桌面应用完全免费，本地模型推理无需任何 API 费用。

### Q2：无审查意味着什么？有什么风险？

无审查意味着：
- 没有内容安全过滤器阻止特定提示词
- 不会拒绝生成特定类型的图像/视频
- 没有平台侧的审核机制

风险：你需要自行承担使用责任，确保不生成违法或侵权内容。

### Q3：macOS 安装时提示"无法验证此 App"怎么办？

这是 macOS Gatekeeper 的安全机制。按照本文档的 [macOS 安装说明](#macos-安装说明) 执行 `xattr -cr` 命令即可。这一步移除扩展属性，让系统允许运行未公证的应用。

### Q4：本地模型推理对硬件要求高吗？

取决于模型：
- **Z-Image Turbo**：推荐 16 GB RAM，Metal GPU 加速
- **SD 1.5 系列**：8 GB RAM 即可，CPU 可运行但较慢
- **SDXL Base**：推荐 32 GB RAM 或 16 GB + 交换空间

### Q5：可以在商业项目中使用生成的图片吗？

取决于具体模型的许可证。项目文档未明确说明各模型的授权方式。商业使用前，建议检查具体模型的许可证（通常在模型仓库中）。

### Q6：在线版本和桌面应用有什么区别？

| 对比维度 | 在线版本 | 桌面应用 |
|----------|----------|----------|
| 安装 | 无需安装 | 需要下载安装 |
| 数据隐私 | 上传到服务器 | 本地处理 |
| 模型访问 | 200+ 云端模型 | 本地模型 + 部分云端模型 |
| 离线使用 | 不支持 | 支持（本地模型） |
| API 访问 | 需要账户 | 本地 API 可用 |

### Q7：如何为工作室添加自定义模型？

项目是开源的，你可以通过修改源码添加自定义模型。具体步骤：
1. Fork 仓库
2. 在模型配置文件中添加新模型定义
3. 本地构建或使用你的 fork 版本

目前项目未提供插件系统或配置文件方式添加模型。

## 自测题

### 基础概念

1. Open Generative AI 的核心特点是什么？（多选）
   - A. 无内容审查
   - B. 免费开源
   - C. 仅支持云端运行
   - D. 支持 200+ 模型

2. 本地模型推理使用哪个引擎？
   - A. TensorRT
   - B. ONNX Runtime
   - C. stable-diffusion.cpp
   - D. PyTorch

### 安装配置

3. macOS 安装未公证应用时，需要执行什么命令？
   - A. `chmod +x`
   - B. `xattr -cr`
   - C. `codesign --force`
   - D. `spctl --add`

4. Windows SmartScreen 警告出现时，如何继续安装？
   - A. 不可能继续
   - B. 点击"更多信息" → "仍要运行"
   - C. 禁用防火墙
   - D. 以管理员身份运行

### 功能使用

5. 图像工作室支持哪些生成模式？
   - A. 仅文生图
   - B. 文生图和图生图
   - C. 仅图生图
   - D. 文生图、图生图、视频生图

6. 唇同步工作室支持几种输入模式？
   - A. 1 种
   - B. 2 种
   - C. 3 种
   - D. 4 种

### 参考答案

1. A, B, D（自托管，非仅云端）
2. C
3. B
4. B
5. B
6. B（肖像 + 音频；视频 + 音频）

## 进阶路径

### 第一步：深入模型定制

- 研究 [stable-diffusion.cpp](https://github.com/leejet/stable-diffusion.cpp) 的模型转换流程
- 学习如何将自定义模型（Checkpoint、LoRA）转换为 GGUF 格式
- 探索量化对生成质量和速度的影响

### 第二步：工作流自动化

- 使用工作流工作室的可视化编辑器创建多步骤管道
- 学习节点编辑器的使用方法
- 参考社区模板，构建自己的媒体生成工作流

### 第三步：集成到生产环境

- 使用本地 API 将生成能力集成到自己的应用
- 研究项目的 API 文档（如果可用）
- 为团队搭建共享的 Open Generative AI 实例

### 相关资源

| 资源 | 链接 | 用途 |
|------|------|------|
| 项目 GitHub | https://github.com/Anil-matcha/Open-Generative-AI | 源码、Issue、PR |
| 在线体验 | https://dev.muapi.ai/open-generative-ai | 快速试用 |
| stable-diffusion.cpp | https://github.com/leejet/stable-diffusion.cpp | 本地推理引擎 |
| Awesome GPT-Image-2 API Prompts | https://github.com/Anil-matcha/Awesome-GPT-Image-2-API-Prompts | 提示词参考 |
| Generative-Media-Skills | https://github.com/SamurAIGPT/Generative-Media-Skills | 媒体生成技能 |

## 总结

Open Generative AI 是一个功能强大的开源 AI 生成工具，它提供了无审查、无限制的创意体验。无论你是设计师、开发者还是创意爱好者，都可以从中受益。其对多种模型的支持、本地推理能力和工作流自动化功能，使其成为一个全面且灵活的 AI 创作平台。

如果你在寻找 Higgsfield AI、Freepik、Krea 或 Openart AI 的开源替代品，Open Generative AI 值得一试。

## 延伸阅读

- [在线体验](https://dev.muapi.ai/open-generative-ai)
- [GitHub 仓库](https://github.com/Anil-matcha/Open-Generative-AI)
- [Awesome GPT-Image-2 API Prompts](https://github.com/Anil-matcha/Awesome-GPT-Image-2-API-Prompts)
- [Generative-Media-Skills](https://github.com/SamurAIGPT/Generative-Media-Skills)

---

*本文由钳岳星君撰写，基于 GitHub 仓库 [Anil-matcha/Open-Generative-AI](https://github.com/Anil-matcha/Open-Generative-AI) 的 README。优化版本增加了学习目标、目录、常见问题、自测题和进阶路径。*
