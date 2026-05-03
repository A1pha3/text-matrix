---
title: "Pixelle-Video：AI 全自动短视频引擎完全指南"
date: 2026-05-03T20:00:00+08:00
slug: "pixelle-video-ai-short-video-engine-guide"
description: "Pixelle-Video是由AIDC-AI团队开发的AI全自动短视频引擎，基于Python和ComfyUI架构，用户只需输入主题即可自动完成文案撰写、AI配图生成、语音合成、背景音乐添加和视频合成全部流程。"
draft: false
categories: ["技术笔记"]
tags: ["AI视频", "短视频", "AIGC", "ComfyUI", "Python"]
---
# Pixelle-Video：AI 全自动短视频引擎完全指南

只需输入一个主题，Pixelle-Video 就能自动完成从**文案撰写**到**视频合成**的全部流程——包括 AI 配图生成、AI 语音解说、背景音乐添加，最终输出一段完整的短视频。零门槛，无需任何剪辑经验。

## 项目概览

**Pixelle-Video**是由 AIDC-AI 团队开发的开源项目，定位为"AI 全自动短视频引擎"（AI Fully Automated Short Video Engine）。该项目基于 Python 开发，以 Apache 2.0 协议开源，核心架构依托 **ComfyUI** 的节点式工作流设计，提供高度模块化的视频生成管线。

截至 2026 年 5 月，项目在 GitHub 上已获得约 **9,418 Stars** 和 **1,487 Forks**，topics 覆盖 `aigc`、`comfyui`、`image-generation`、`tts`、`video-generation`，属于 AIGC 视频创作领域的活跃项目。

| 属性 | 值 |
|------|------|
| GitHub | [AIDC-AI/Pixelle-Video](https://github.com/AIDC-AI/Pixelle-Video) |
| 语言 | Python |
| 协议 | Apache 2.0 |
| Stars | ~9,418 |
| Forks | ~1,487 |
| 创建时间 | 2025-11-07 |
| 最后更新 | 2026-05-03 |
| Web 框架 | Streamlit |

## 核心能力与解决问题

短视频创作传统上需要经历**写脚本→找素材→配音→剪辑→导出**等多个环节，对非专业用户存在较高门槛。Pixelle-Video 将这一流程压缩为"输入主题→点击生成"的一键操作：

1. **输入主题**：用户只需提供一句话主题或已有文案
2. **AI 文案生成**：大语言模型自动创作解说词，按语义切分为多个分镜
3. **AI 配图生成**：为每个分镜生成配套 AI 插图（支持 Flux、WAN 2.1 等模型）
4. **AI 语音合成**：将文案转换为自然语音（支持 Edge-TTS、Index-TTS 等）
5. **背景音乐**：内置 BGM 或用户自定义音乐
6. **视频合成**：将图文音按分镜顺序合并，输出 MP4

## 技术架构解析

### 整体架构

Pixelle-Video 采用**三层模块化设计**：

```
┌─────────────────────────────────────────┐
│          Web UI（Streamlit）            │  用户交互层
├─────────────────────────────────────────┤
│  内容生成 → 图像生成 → 语音合成 → 合成   │  业务逻辑层
├─────────────────────────────────────────┤
│  LLM（通义千问/GPT/DeepSeek/Ollama）     │
│  图像（ComfyUI / RunningHub）           │  模型服务层
│  语音（Edge-TTS / Index-TTS）           │
└─────────────────────────────────────────┘
```

### 视频生成流程

整个流程在 README 中有清晰展示（`resources/flow.png`），五个步骤依次执行：

- **文案生成**：LLM 根据用户主题创作解说词，并切分为 N 个分镜
- **配图规划**：为每个分镜规划对应 AI 图像的提示词（Prompt）
- **逐帧处理**：调用图像生成服务（ComfyUI/RunningHub）生成各分镜配图
- **语音合成**：调用 TTS 服务将分镜文案转为语音
- **视频合成**：按模板（HTML/视频背景）将图文音合并为 MP4

### ComfyUI 工作流扩展机制

项目的核心技术亮点在于对 **ComfyUI 工作流**的深度整合。用户可以在 `workflows/` 目录下放置自定义工作流，实现能力替换：

- **替换生图模型**：将默认 Flux 工作流替换为 FLUX、Stable Diffusion 等任意模型
- **替换 TTS**：将 Edge-TTS 替换为 ChatTTS、Index-TTS 等
- **添加新能力**：如替换视频生成为自训练模型

这种设计将 AI 视频生成的核心能力（模型选择）从代码中解耦，用户无需修改源码即可切换后端模型。

### 扩展模块

2026 年 1 月，项目新增三个扩展模块：

| 模块 | 功能描述 |
|------|----------|
| **数字人口播** | 上传参考音频克隆音色，生成数字人解说视频 |
| **图生视频** | 将 AI 生成的图片转换为动态视频内容 |
| **动作迁移** | 上传参考视频和图片，将视频中的人物动作迁移到图片 |

## 安装与快速开始

### Windows 一键整合包（推荐）

无需安装 Python、uv 或 ffmpeg，下载整合包后双击 `start.bat` 即可：

```bash
# 1. 下载最新整合包
# https://github.com/AIDC-AI/Pixelle-Video/releases/latest

# 2. 解压后运行
双击 start.bat

# 3. 浏览器自动打开 Web 界面
# http://localhost:8501
```

### 源码安装（macOS / Linux）

#### 前置依赖

```bash
# 安装 uv（Python 包管理器）
# 参考：https://docs.astral.sh/uv/getting-started/installation/

# 安装 ffmpeg
# macOS
brew install ffmpeg
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg
```

#### 启动步骤

```bash
# 克隆项目
git clone https://github.com/AIDC-AI/Pixelle-Video.git
cd Pixelle-Video

# 使用 uv 运行（自动安装依赖）
uv run streamlit run web/app.py

# 浏览器打开 http://localhost:8501
```

首次使用需要在 Web 界面的「⚙️ 系统配置」中填写：
- **LLM 配置**：选择模型（通义千问/GPT/DeepSeek/Ollama）并填入 API Key
- **图像配置**：本地 ComfyUI 地址（`http://127.0.0.1:8188`）或 RunningHub API Key

## 使用方法详解

Web 界面采用三栏布局，从左到右依次为：内容输入 → 语音/视觉设置 → 生成预览。

### 内容输入

支持两种模式：

- **AI 生成内容**：输入主题（如"为什么要养成阅读习惯"），AI 自动创作文案
- **固定文案内容**：直接粘贴现成文案，跳过 AI 创作环节

### 语音设置（TTS）

- 从下拉菜单选择 TTS 工作流（Edge-TTS、Index-TTS 等）
- 可上传参考音频进行**声音克隆**（支持 MP3/WAV/FLAC）
- 预览功能支持输入测试文本试听效果

### 视觉设置

- **图像生成**：选择 ComfyUI 工作流（默认 `image_flux.json`），支持本地或 RunningHub 云端
- **图像尺寸**：默认 1024×1024，可根据视频尺寸调整
- **提示词前缀**：通过英文 Prompt 控制图像整体风格（如"Minimalist black-and-white sketch style"）
- **视频模板**：`static_*.html`（纯文字）、`image_*.html`（图片背景）、`video_*.html`（视频背景），按竖屏/横屏/方形分组

### 生成视频

点击「🎬 生成视频」后，界面实时显示进度：`生成文案 → 生成配图 → 合成语音 → 合成视频`。完成后自动播放预览，并展示时长、文件大小、分镜数等信息。视频文件保存在 `output/` 目录。

## 费用方案

项目完全支持免费运行，主要有三种方案：

| 方案 | LLM | 图像生成 | 费用 |
|------|-----|----------|------|
| **完全免费** | Ollama（本地） | ComfyUI（本地） | 0 元 |
| **推荐方案** | 通义千问（云） | ComfyUI（本地） | LLM 成本极低 |
| **云端全方案** | OpenAI（云） | RunningHub（云） | 费用较高 |

有本地显卡的用户建议采用完全免费方案；无显卡用户推荐通义千问 + 本地 ComfyUI 的组合。

## 适用场景与边界

### 适用场景

- 知识科普类短视频批量生产（输入主题即可生成）
- 自媒体内容创作（文案+配图+配音一站式完成）
- 教育培训视频快速制作
- 小说/故事类视频解说

### 项目边界

- 视频合成质量取决于所选 AI 模型（图像/TTS）的实际效果
- 动作迁移和数字人口播属于扩展模块，功能稳定性可能因模型而异
- 不提供视频剪辑级别的精细控制（如转场、特效、时间线编辑）
- 自定义工作流需要用户具备 ComfyUI 基础

## 项目依赖与技术栈

| 类别 | 技术 |
|------|------|
| Web UI | Streamlit |
| 图像生成 | ComfyUI（Flux、WAN 2.1 等） |
| 语音合成 | Edge-TTS、Index-TTS、ChatTTS |
| 大语言模型 | OpenAI GPT、通义千问、DeepSeek、Ollama |
| 视频处理 | ffmpeg |
| 视频合成 | HTML 模板 + 图像/视频素材 |
| 扩展机制 | ComfyUI JSON 工作流 |

## 总结

Pixelle-Video 将 AI 短视频创作的五个关键环节（文案、配图、配音、BGM、视频合成）整合为一个高度模块化的工作流。其核心价值在于：

1. **零门槛**：用户只需输入主题，无需任何视频剪辑技能
2. **高度可扩展**：基于 ComfyUI 架构，支持任意替换 AI 模型和工作流
3. **灵活部署**：支持本地免费运行（Ollama + ComfyUI），也支持全云端方案
4. **持续活跃**：2026 年 1 月仍保持更新，新增动作迁移等前沿功能

对于需要批量生产短视频、或希望快速验证 AI 视频生成概念的用户，Pixelle-Video 是一个值得关注的开源选择。

---

**延伸阅读：**
- Pixelle-Video GitHub：https://github.com/AIDC-AI/Pixelle-Video
- Pixelle-MCP（ComfyUI MCP 服务器）：https://github.com/AIDC-AI/Pixelle-MCP
- Windows 一键整合包：https://github.com/AIDC-AI/Pixelle-Video/releases/latest
