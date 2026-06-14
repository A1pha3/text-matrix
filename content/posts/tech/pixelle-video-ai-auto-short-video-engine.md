---
title: "Pixelle-Video：AI 全自动短视频引擎，从一句话到完整视频的全流程解析"
date: "2026-05-04T10:06:00+08:00"
slug: "pixelle-video-ai-auto-short-video-engine"
description: "Pixelle-Video 是 AIDC-AI 开源的 AI 全自动短视频生成引擎，基于 ComfyUI 架构设计，支持从主题输入到配图、配音、视频合成的全自动化流程。本文深入解析其模块化架构、核心代码结构、各模块功能及典型使用场景，并提供从零安装到自定义工作流的完整指南。"
draft: false
categories: ["技术笔记"]
tags: ["AI视频生成", "ComfyUI", "短视频创作", "Python", "开源项目"]
---

# Pixelle-Video：AI 全自动短视频引擎，从一句话到完整视频的全流程解析

Pixelle-Video 是一个由 AIDC-AI 团队维护的开源项目（Stars 16,416，Forks 2,361，Apache-2.0 许可证），其核心目标是让视频创作彻底摆脱剪辑经验的要求——用户只需输入一个主题，系统便能自动完成文案撰写、AI 配图生成、语音解说合成、背景音乐添加，最终输出可发布的短视频成品。

这个目标的实现依赖于三个关键设计决策：基于 ComfyUI 的原子化能力抽象、多 LLM / 多 TTS 引擎的可插拔架构，以及 Streamlit 构建的零门槛 Web 界面。以下从项目结构、核心架构、安装使用和代码拆解几个维度，对 Pixelle-Video 进行完整解析。

## 一、项目概览与核心能力

### 1.1 一句话定位

Pixelle-Video = **主题输入 → AI 全自动 → 短视频成品**，零剪辑经验要求。

### 1.2 主要功能模块

| 功能 | 说明 |
|------|------|
| AI 文案生成 | 输入主题，大语言模型自动撰写解说词 |
| AI 配图生成 | 每个分镜自动配上 AI 插图 |
| AI 视频生成 | 支持 WAN 2.1 等视频生成模型创建动态画面 |
| AI 语音合成 | 支持 Edge-TTS、Index-TTS 等多种 TTS 方案，含声音克隆 |
| 背景音乐 | 内置 BGM 库或上传自定义音乐 |
| 数字人口播 | 上传参考音频，AI 克隆音色朗读文案 |
| 动作迁移 | 上传参考视频与图片，实现动作迁移 |
| 图生视频 | 将静态 AI 配图转化为动态视频片段 |

### 1.3 技术栈一览

- **语言**：Python
- **前端**：Streamlit（Web UI，运行在 localhost:8501）
- **媒体生成**：ComfyUI 工作流（原生涯图/视频），支持本地自部署（selfhost）或云端调用（RunningHub）
- **LLM 支持**：GPT、Qwen（通义千问）、DeepSeek、Ollama（本地免费）
- **TTS 支持**：Edge-TTS、Index-TTS 及兼容声音克隆的工作流
- **视频合成**：ffmpeg
- **发布形式**：源码 + Windows 一键整合包（v0.1.15）

### 1.4 适用人群

- 没有视频剪辑经验的内容创作者（知识科普、副业分享、个人成长类短视频）
- 希望快速生成大量短视频进行分发运营的从业者
- 研究 AI 视频生成全流程的开发者

## 二、架构设计：三层模块化

Pixelle-Video 的架构分为三层，从上到下分别是 **Web 层 → 编排层 → 能力层**，每一层都保持了清晰的边界和可替换性。

```
┌─────────────────────────────────────────────┐
│  Web 层（Streamlit）                         │
│  app.py - 用户交互、配置管理、任务触发        │
├─────────────────────────────────────────────┤
│  编排层（pipelines）                          │
│  负责把原子能力串联成完整的视频生成流水线      │
├─────────────────────────────────────────────┤
│  能力层（ComfyUI 工作流 + LLM/TTS 服务）      │
│  workflows/ - 图像生成、视频生成、TTS 等     │
│  services/ - LLM、TTS 等外部服务抽象         │
└─────────────────────────────────────────────┘
```

### 2.1 Web 层：用户入口

Web 层由 `web/app.py` 主导，用户在浏览器中完成所有操作：

- 左侧栏：输入主题或固定文案、选择 BGM
- 中间栏：配置 TTS 工作流、参考音频（声音克隆）、图像生成工作流、视觉模板
- 右侧栏：触发生成、查看进度、预览最终视频

配置项通过 Streamlit 的 session_state 持久化，保存到本地配置文件，避免每次重开都要重新填写。

### 2.2 编排层：流水线逻辑

核心编排逻辑在 `pixelle_video/pipelines/` 目录下。以默认的视频生成流水线为例，步骤如下：

1. **文案生成**：将用户输入的主题发送给 LLM，LLM 返回结构化的分镜文案（每段含文字描述、画面建议等）
2. **配图规划**：按分镜数量规划图片请求，确定每张图的尺寸、提示词前缀
3. **并行生成**：通过 ComfyUI 工作流（本地或 RunningHub）并行生成所有配图
4. **语音合成**：将每段文案通过 TTS 工作流合成语音文件（可含克隆音色）
5. **视频合成**：将配图 + 语音 + BGM 通过 ffmpeg 合成为最终 MP4

编排层的设计使得每个步骤都可以单独替换——例如把本地 ComfyUI 换成 RunningHub 云服务，或把 Edge-TTS 换成 ChatTTS，都不需要修改编排层的代码。

### 2.3 能力层：ComfyUI 工作流生态

Pixelle-Video 的图像和视频生成能力基于 ComfyUI 工作流引擎。工作流文件存放在 `workflows/` 目录下，分为两个子目录：

- `workflows/selfhost/`：本地部署的 ComfyUI 工作流，默认 `image_flux.json` 使用 FLUX 模型生成配图
- `workflows/runninghub/`：RunningHub 云端工作流，适合没有高性能显卡的用户

系统会自动扫描 `workflows/` 目录，将符合命名规则的工作流加载到 Web 界面的下拉菜单中。用户如果熟悉 ComfyUI，可以将自己设计的工作流放入该目录，即可在 UI 中直接选用——无需修改任何代码。

这种设计的核心优势在于 **原子能力的高度可复用**：Pixelle-Video 本身不实现图像生成模型，而是通过标准化的 ComfyUI API 调用任意预置或自定义的模型节点，实现真正的"替换模型而不改代码"。

## 三、安装与快速开始

### 3.1 Windows 一键整合包（推荐）

适合不想配置任何环境的用户：

1. 从 [Releases 页面](https://github.com/AIDC-AI/Pixelle-Video/releases/latest) 下载 `Pixelle-Video-v0.1.15-win64.zip`
2. 解压后双击 `start.bat`
3. 浏览器自动打开 http://localhost:8501
4. 在「⚙️ 系统配置」中填入 LLM API Key 和图像服务配置（本地 ComfyUI 或 RunningHub）
5. 输入主题，点击「🎬 生成视频」

整合包包含了所有运行时依赖，无需单独安装 Python、uv 或 ffmpeg。

### 3.2 源码安装（macOS / Linux / 开发者）

#### 前置依赖

- **uv**：Python 包管理器，执行 `uv --version` 确认已安装
- **ffmpeg**：
  - macOS：`brew install ffmpeg`
  - Ubuntu/Debian：`sudo apt update && sudo apt install ffmpeg`
  - Windows：从 https://ffmpeg.org/download.html 下载并添加 bin 到 PATH

#### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/AIDC-AI/Pixelle-Video.git
cd Pixelle-Video

# 启动 Web 界面（uv 自动安装依赖）
uv run streamlit run web/app.py
```

浏览器自动打开 http://localhost:8501。

#### 配置说明

首次使用时展开「⚙️ 系统配置」面板：

**LLM 配置**（必填）：

- 推荐方案：通义千问（Qwen），API 成本极低
- 免费方案：Ollama 本地运行，0 费用但需要本地显卡
- 手动配置需填写 API Key、Base URL 和 Model 名称

**图像配置**（必填）：

- 本地部署（推荐）：ComfyUI 运行在 `http://127.0.0.1:8188`，点击「测试连接」确认
- 云端部署：填写 RunningHub API Key

### 3.3 Docker 部署

项目提供了 `docker-compose.yml`，适合有一定容器化经验的用户：

```bash
docker-compose up -d
```

需要注意的是，Docker 方式需要本地有 GPU 支持 ComfyUI 推理，配置复杂度相对较高。

## 四、核心代码结构

### 4.1 目录结构

```
Pixelle-Video/
├── web/                  # Streamlit Web UI 入口
│   └── app.py            # 主应用文件
├── pixelle_video/        # 核心业务逻辑
│   ├── config/           # 配置管理（读取/保存用户配置）
│   ├── models/           # 数据模型（PipelineConfig, VideoResult 等）
│   ├── pipelines/        # 流水线编排（视频生成主流程）
│   ├── prompts/          # LLM 提示词模板
│   ├── services/         # 外部服务抽象（LLM、TTS、ComfyUI）
│   └── utils/            # 辅助工具函数
├── workflows/            # ComfyUI 工作流（selfhost/ + runninghub/）
├── templates/            # HTML 视频模板（static_/image_/video_ 三类）
├── bgm/                  # 内置背景音乐
├── config.example.yaml   # 配置示例文件
└── pyproject.toml        # Python 项目定义
```

### 4.2 关键模块解析

#### Services 层（services/）

Services 层负责与外部服务通信，是整个系统对外交互的边界。

`llm_service.py` 封装了大语言模型调用逻辑。支持多种后端（OpenAI GPT、通义千问、DeepSeek、Ollama），通过统一的接口屏蔽不同 API 的差异，编排层调用 LLM 时无需关心底层是哪家模型。

`comfy_service.py` 负责与 ComfyUI API 交互。工作流通过 JSON 文件定义，节点之间的连接关系（图结构）在 JSON 中描述，提交到 ComfyUI 后由其调度执行。系统会轮询节点状态，直到所有节点完成，再下载生成的图片/视频文件。

`tts_service.py` 处理文本转语音。根据选中的 TTS 工作流，将分镜文案转换为 MP3 音频文件。如果用户上传了参考音频，则在请求中加入音色克隆参数。

#### Pipelines 层（pipelines/）

`video_pipeline.py` 是最核心的文件，负责串联文案生成→配图生成→语音合成→视频合成全流程。关键逻辑：

```python
# 简化流程
def generate_video(topic, config):
    # Step 1: 生成文案
    script = llm_service.generate_script(topic, config.llm_model)
    
    # Step 2: 并发生图
    images = []
    for scene in script.scenes:
        img = comfy_service.generate_image(scene.prompt, config.workflow)
        images.append(img)
    
    # Step 3: 合成语音
    audio_files = []
    for scene in script.scenes:
        audio = tts_service.synthesize(scene.text, config.tts_workflow, config.voice_ref)
        audio_files.append(audio)
    
    # Step 4: 最终合成
    output = ffmpeg_utils.merge(images, audio_files, config.bgm, config.template)
    return output
```

所有涉及网络 I/O 和模型推理的步骤（生图、语音合成）均支持并行处理，以减少总耗时。

#### Config 层（config/）

`config_manager.py` 负责读取、保存和验证用户配置。配置以 YAML 格式持久化到本地，Web 界面每次启动时自动加载上一次保存的配置。配置的 key 包括 LLM 相关参数、ComfyUI/RunningHub 连接信息、TTS 工作流选择、默认模板等。

### 4.3 工作流自定义

对于有 ComfyUI 使用经验的用户，项目的工作流自定义非常直接：

1. 在 ComfyUI 中设计或调整工作流
2. 将工作流 JSON 文件放入 `workflows/selfhost/`（本地）或 `workflows/runninghub/`（云端）
3. 系统自动扫描并在下拉菜单中呈现
4. 在 Web 界面选择即可，无需修改代码

这种设计使得替换生图模型（如 FLUX → SDXL）、替换 TTS 引擎（如 Edge-TTS → ChatTTS）等操作都变成零代码的界面配置行为。

## 五、使用场景与效果展示

### 5.1 典型场景

| 场景类型 | 适用模板 | 效果特点 |
|---------|---------|---------|
| 知识科普 | 默认模板/竖屏 | 结构清晰，配图精准，适合涨知识类内容 |
| 个人成长 | 克隆音色/竖屏 | 声音有辨识度，提升信任感 |
| 历史故事 | 自定义模板/横屏 | 画面质感强，解说感厚重 |
| 小说解说 | 固定文案/竖屏 | 直接用现成脚本，跳过 AI 文案生成 |
| 副业赚钱 | 电影模板/横屏 | 视觉冲击力强，适合信息流分发 |

### 5.2 扩展模块

项目在 2026 年 1 月后新增了三个扩展模块：

**数字人口播**：上传参考音频（3-30 秒），系统克隆音色并将文案朗读出来，适合需要个人 IP 但不想露脸的创作者。韩语、英语、中文等多语言音色均已支持。

**图生视频**：将 AI 生成的静态配图转换为动态视频片段，适用于卡通风格和需要动效增强表达力的场景。

**动作迁移**：上传一段参考视频和一张图片，系统将视频中人物的动作迁移到图片上，生成新的视频内容。适合创意类和模仿类短视频。

### 5.3 费用说明

项目完全支持免费运行：

- **0 元方案**：LLM 使用 Ollama 本地运行 + ComfyUI 本地部署，显卡要求 8GB+ 显存
- **低价方案**：通义千问 API（成本极低）+ ComfyUI 本地部署
- **全云方案**：OpenAI GPT + RunningHub，无需本地环境但费用较高

本地有高性能显卡的用户，推荐使用 0 元方案。

## 六、优势与边界

### 6.1 核心优势

1. **零门槛上手**：Windows 一键整合包，无需配置 Python 环境，配置好 API Key 即可运行
2. **模块化可扩展**：基于 ComfyUI 工作流，任何 ComfyUI 节点都可以作为新的原子能力接入
3. **全自动化**：从主题到成品的完整流程无需人工干预
4. **多模态支持**：文案、配图、配音、背景音乐、视频合成全覆盖
5. **活跃维护**：2026 年仍在持续更新（最新提交 2026-04-13），近期新增动作迁移和数字人口播模块

### 6.2 已知边界

1. **视频生成质量依赖底层模型**：ComfyUI 工作流中使用的模型（FLUX、WAN 2.1 等）直接决定图像和视频的最终质量
2. **长视频场景未专门优化**：默认流水线适合 1-3 分钟的短视频，生成长内容时 LLM 文案的连贯性和语音合成的体验可能下降
3. **模板自定义需要 HTML 基础**：虽然提供了多种模板，但深度自定义仍需要编写 HTML，适合有前端经验的用户

## 七、总结

Pixelle-Video 代表了一种明确的工程思路：用 **ComfyUI 解决图像/视频生成的可替换性**，用 **Streamlit 解决用户体验的零门槛**，用 **流水线抽象解决复杂多步骤的编排问题**。三者结合，使得一个原本需要专业团队才能完成的视频创作流程，被压缩成"输入主题 → 点击生成"的两步操作。

对于内容创作者，Pixelle-Video 显著降低了短视频的生产成本；对于 AI 应用开发者，它的模块化设计提供了一个研究 AI 视频生成全流程的优秀范本；对于 AI 创业场景，它的核心架构（ComfyUI + LLM + TTS 可插拔编排）可以直接复用到你自己的产品中。

如果你对 AI 视频生成的工程实现感兴趣，建议从 `pixelle_video/pipelines/video_pipeline.py` 和 `workflows/selfhost/` 目录开始阅读——前者展示了如何将多个 AI 能力串联成完整流水线，后者展示了如何将 AI 生成能力标准化为可替换的工作流文件。

## 参考链接

- GitHub 仓库：https://github.com/AIDC-AI/Pixelle-Video
- 官方文档：https://aidc-ai.github.io/Pixelle-Video/zh
- 视频演示：https://www.bilibili.com/video/BV1WzyGBnEVp/
- Windows 一键整合包：https://github.com/AIDC-AI/Pixelle-Video/releases/latest