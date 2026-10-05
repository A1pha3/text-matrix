---
title: "MoneyPrinterTurbo：把 5 个服务模块装成一条命令的 AI 短视频工厂"
date: 2026-06-25T21:07:55+08:00
lastmod: 2026-10-03T00:00:00+08:00
slug: "harry0703-moneyprinterturbo-short-video-automation-guide-2026"
github_repo: "harry0703/MoneyPrinterTurbo"
source_key: "gh:harry0703/MoneyPrinterTurbo"
description: "harry0703/MoneyPrinterTurbo 把 LLM 文案、TTS 配音、素材获取、字幕生成、MoviePy 视频合成 5 个服务模块装进 WebUI / API / CLI / AI Agent 四种入口。给定主题就能吐出可发布的短视频。本文按 main 分支源码与 v1.3.7 Release 拆开 5 个模块的边界、素材从库存检索到 AI 生成的扩展、以及单条全自动 vs 系列化的适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["FastAPI", "TTS", "Whisper", "短视频", "MoviePy"]
---

# MoneyPrinterTurbo：把 5 个服务模块装成一条命令的 AI 短视频工厂

> **数据来源**：本文依据 [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) main 分支的 README、`config.example.toml`、`cli.py`、`app/services/` 源码与 GitHub Releases 记录整理，关键数据核验于 2026-10-03（详细出处见文末事实核验表）。文中不带出处标注的耗时数字一律不写——推理速度取决于你的网络、模型和机器，任何"实测 X 秒"离开具体环境都没有意义。

## 学习目标

读完本文后，你应该能够：

- 说出 MoneyPrinterTurbo 的 5 个服务模块各自的任务边界和可替换点
- 解释为什么 `app/services/task.py` 是四种入口（WebUI / API / CLI / AI Agent）的唯一握手点
- 在 edge 字幕和 whisper 字幕之间按场景做取舍
- 判断素材该走库存检索还是 AI 生成，以及各自的计费方式
- 判断你的内容类型是否适合用 MoneyPrinterTurbo 批量生产

## 目录

- [§1 先给判断](#1-先给判断)
- [§2 系统地图：5 个服务模块 × 4 种入口](#2-系统地图5-个服务模块--4-种入口)
- [§3 第 1 段：LLM 文案与搜索关键词](#3-第-1-段llm-文案与搜索关键词)
- [§4 第 2 段：素材——库存检索与 AI 生成两条路](#4-第-2-段素材库存检索与-ai-生成两条路)
- [§5 第 3 段：TTS 配音](#5-第-3-段tts-配音)
- [§6 第 4 段：字幕生成](#6-第-4-段字幕生成)
- [§7 第 5 段：视频合成](#7-第-5-段视频合成)
- [§8 任务流案例：一次"主题 → 成片"的完整流转](#8-任务流案例一次主题--成片的完整流转)
- [§9 跨平台发布：Upload-Post 集成](#9-跨平台发布upload-post-集成)
- [§10 演进时间线：版本史里的四个工程动作](#10-演进时间线版本史里的四个工程动作)
- [§11 部署路径](#11-部署路径)
- [§12 常见问题与故障恢复](#12-常见问题与故障恢复)
- [§13 硬件门槛与耗时结构](#13-硬件门槛与耗时结构)
- [§14 成本结构：钱花在哪个环节](#14-成本结构钱花在哪个环节)
- [§15 与同类的对比](#15-与同类的对比)
- [§16 适用边界与采用顺序](#16-适用边界与采用顺序)
- [§17 自测清单](#17-自测清单)
- [§18 参考链接](#18-参考链接)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [事实核验与引用](#事实核验与引用)

## §1 先给判断

`harry0703/MoneyPrinterTurbo` 在做的事很具体：**把"主题 → 文案 → 配音 → 素材 → 字幕 → 合成"这一整条链压成一条命令**。截至 2026-10-03，仓库 128,059 Stars、20,028 Forks、MIT 协议，最新 Release v1.3.7（2026-09-13），README 有简体中文、英文、日文三个版本。

仓库本身不发明任何"AI 视频模型"——它把开源世界已经成熟的几段（LLM 文本生成、多供应商 TTS、素材获取、whisper / edge 字幕、MoviePy 2.x 视频合成）按"短视频工厂"的产品形态串起来，再通过 `config.toml` 把 31 个 LLM 提供商配置段、11 家 TTS 服务、11 种素材源、2 套字幕方案、3 个发布平台（TikTok / Instagram / YouTube）全部暴露成可配置项。

这背后的定位是：**MoneyPrinterTurbo 不是"AI 视频生成模型"，而是"AI 短视频生产流水线的集成层"**。看清这一条，才能解释它为什么能在 12.8 万 Stars 的量级上保持 production-ready，以及为什么单条全自动适合、系列化 / 强品牌化不适合——后者要求"每一条都有自己的风格"，而流水线工具天然是"所有条共享同一种风格"。

文章要拆开的事：

1. 5 个服务模块（LLM / 素材 / TTS / 字幕 / 合成）各自的边界和可替换点
2. 四种入口共享 service 层的实际范围
3. 一次"主题 → 成片"任务在流水线上的具体流转
4. 素材源从库存检索扩展到 AI 生成、TTS 从 2 家扩到 11 家这些关键演进
5. 适用边界——什么场景下用、用到什么程度、什么时候改用其他工具

## §2 系统地图：5 个服务模块 × 4 种入口

MoneyPrinterTurbo 的代码组织是 MVC 风格，更准确的描述是"**5 个服务模块 + 4 种入口**"。服务模块是底座，入口是表面的不同切法：

```text
┌────────────────────────────────────────────────────────────────┐
│  4 种入口（共享同一份 service，按使用场景选）                        │
│                                                                │
│    webui/Main.py    Streamlit · 浏览器交互 · 默认 8501            │
│    app/api          FastAPI  · REST + Swagger · 默认 8080       │
│    cli.py           argparse  · 无浏览器 · 批处理清单             │
│    docs/skill/      AI Agent · SKILL.md + mpt_agent.py         │
├────────────────────────────────────────────────────────────────┤
│  编排层（所有模块在这里握手）                                       │
│                                                                │
│    app/services/task.py   6 个阶段：script → terms → audio      │
│                           → subtitle → materials → video        │
├────────────────────────────────────────────────────────────────┤
│  5 个服务模块（可独立替换）                                        │
│                                                                │
│   ┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐ ┌────────┐ │
│   │ llm.py  │ │material  │ │voice   │ │ subtitle │ │ video  │ │
│   │ 文案+   │ │  .py     │ │  .py   │ │   .py    │ │  .py   │ │
│   │ 关键词  │ │ 素材获取  │ │ 配音   │ │  字幕     │ │  合成   │ │
│   └─────────┘ └──────────┘ └────────┘ └──────────┘ └────────┘ │
│                                                                │
│   31 个     3 库存库+    11 家 TTS   edge(快)    MoviePy 2.2.1  │
│   LLM 配置段 7 种 AI     +无配音/    whisper(准)  + Pillow       │
│             生成源+本地  上传配音   +纠错+动画  + FFmpeg          │
├────────────────────────────────────────────────────────────────┤
│  基础设施                                                        │
│                                                                │
│    config.toml      配置驱动：provider / 素材源 / 字幕 / 声音     │
│    resource/songs   默认背景音乐                                 │
│    resource/fonts   默认字幕字体                                 │
│    models/          本地 whisper 模型（可选）                     │
│    Dockerfile*      ghcr.io 预构建镜像（含 gpu 变体）             │
└────────────────────────────────────────────────────────────────┘
```

**两个最关键的边界**：

1. **`task.py` 是唯一编排点**——5 个服务模块不互相调用，`task.py` 决定执行顺序和数据交接。`llm.py` 出文案和搜索关键词，`voice.py` 出音频，`material.py` 出素材片段，`subtitle.py` 出字幕文件，`video.py` 把前三者按时间轴合成。换其中任何一个模块，其余四个不动。
2. **`config.toml` 是唯一配置入口**——首次启动时程序会根据 `config.example.toml` 自动创建 `config.toml`，WebUI 基础设置里填的 API Key 也写回这份文件。没有"藏在 webui/Main.py 里的隐藏开关"。

这套分层直接决定了一件事：在 WebUI 调好的参数，可以原样写进 CLI 命令跑批处理——因为编排层只有一个。这是它和"Web 工具"的本质区别。

### 2.1 代码侧的文件布局

```text
MoneyPrinterTurbo/
├── app/
│   ├── api/                        # FastAPI 路由（v1/video.py 等）
│   ├── controllers/                # 任务管理器（memory / redis 二选一）
│   ├── models/                     # Pydantic 模型与 LLM 提供商注册表
│   ├── services/
│   │   ├── task.py                 # 编排层：6 阶段流水线（约 1,850 行）
│   │   ├── llm.py                  # 第 1 段：文案 + 搜索关键词
│   │   ├── material.py             # 第 2 段：素材获取（约 3,000 行）
│   │   ├── voice.py                # 第 3 段：11 家 TTS（约 3,600 行）
│   │   ├── subtitle.py             # 第 4 段：edge / whisper + 纠错
│   │   ├── video.py                # 第 5 段：合成（约 1,900 行）
│   │   └── upload_post.py 等       # 发布、缓存、AI 素材源 adapter
│   └── utils/                      # task_dir、文件安全等公共工具
├── webui/Main.py                   # Streamlit 入口（约 8,400 行）
├── cli.py                          # 命令行入口（约 1,800 行）
├── main.py                         # FastAPI 服务入口
├── config.example.toml             # 配置模板（首次启动自动复制为 config.toml）
├── pyproject.toml + uv.lock        # 依赖定义与锁文件（uv 主用）
├── requirements.txt                # 旧 pip 兼容
├── Dockerfile / Dockerfile.gpu     # 容器镜像（含 GPU 变体）
├── docker-compose.release.yml      # 拉取 ghcr.io 预构建镜像
├── webui.bat / webui.sh            # WebUI 启动脚本
├── resource/{songs,fonts}/         # 默认配乐与字幕字体
├── docs/skill/SKILL.md             # AI Agent 入口的技能文档
├── docs/voice-list.txt             # Edge TTS 全部音色
└── docs/MoneyPrinterTurbo.ipynb    # Google Colab 体验
```

**新进开发者最先读的两份文件**：`app/services/task.py`（执行流）+ `config.example.toml`（全部可配置项的真相）。5 个服务模块的代码是"用到了再翻"。

## §3 第 1 段：LLM 文案与搜索关键词

`app/services/llm.py` 集中处理"主题 → 视频文案"和"文案 → 搜索关键词"两步。`config.example.toml` 里有多少个提供商？数一下 LLM 配置段：**31 个**。README 把它们分成两类：

- **模型服务直连**：Kimi / Moonshot、OpenAI、Anthropic Claude、Google Gemini、DeepSeek、通义千问、Azure OpenAI、火山引擎方舟、xAI Grok、MiniMax、小米 MiMo
- **网关 / 聚合 / 本地**：胜算云、APIMart、Cloudflare AI Gateway、魔搭 ModelScope、AIHubMix、AIML API、EvoLink、OpenRouter、Fluxion AI、Ollama、Claude Code 订阅、OneAPI、LiteLLM、Groq、Pollinations 等

其中 `litellm` 一条配置就能接入其文档列出的 100+ 兼容网关，`claude_code` 则不走 API Key——它调用本机已登录的 `claude` CLI（headless 模式），消耗的是 Claude 订阅额度。

**默认提供商是 `moonshot`（Kimi）**。`config.example.toml` 里 `llm_provider = "moonshot"`，并且仓库首页的赞助位就是 Kimi——默认值是商业化合作的一部分，新用户开箱不需要先去注册五家服务。提供商的默认模型与 Base URL 维护在 `app/models/llm_provider.py` 的注册表里，`config.toml` 只在需要覆盖时才写 `model_name` / `base_url`。

**统一 prompt 模板**。文案生成都走 `build_script_prompt()` 组装的模板：目标时长、语言、段落数（`paragraph_number`，1-10，默认 1）、可选的自定义要求和完整 system prompt。模板里有一条容易被忽略的硬约束——提示词明确要求模型不要在回复里提及 prompt 本身、不要谈段落数，保证输出是干净的旁白稿。文案之外的搜索关键词（terms）也由 LLM 一并产出，这是素材段的输入。

LLM 这一段的边界是**只生成文本**（文案 + 关键词），不生成视频帧。画面来自下一节的素材模块——这是它和 Sora / Runway 的根本区别：MoneyPrinterTurbo 走的是"现有素材（或 AI 生成素材）+ 编排"路线，不是端到端生成像素。

## §4 第 2 段：素材——库存检索与 AI 生成两条路

`app/services/material.py` 是全仓库第二大的服务模块（约 3,000 行），因为它现在要伺候 **11 种 `video_source` 取值**（`config.example.toml` 明确列出）：

| 素材源 | 类型 | 计费 | 备注 |
|--------|------|------|------|
| **Pexels** | 在线库存 | 免费（需 API key） | 默认源 |
| **Pixabay** | 在线库存 | 免费（需 API key） | 备用源 |
| **Coverr** | 在线库存 | 免费（key 可选） | v1.3.0 新增 |
| **本地素材** | 用户自有 | 免费 | 上传图片 / 视频 |
| **火山方舟 Seedance** | AI 文生视频 | 按片段计费 | v1.3.6 原生接入，2-12 秒、最高 1080p |
| **OFox** | AI 文生视频 | 按片段计费 | 一个 key 调 Seedance / Wan 等多模型 |
| **秘塔 MiniMax H3** | AI 文生视频 | 按片段计费 | 768P / 2K，4-15 秒，三种画幅 |
| **WaveSpeed AI** | AI 文生视频 | 按请求计费 | v1.3.5 接入 |
| **MuAPI** | AI 文生视频 | 按片段计费 | 异步接口，3-12 秒 |
| **LoomLoom**（胜算云） | AI 视频 + 脚本候选 | 付费 | 生成前需在 WebUI 显式确认 |
| **OpenAI 兼容文生图** | AI 生图转视频 | 按图片计费 | 可指向本地 ComfyUI / SD 网关 |

这是 v1.3.x 最重要的一组演进：**素材从"检索库存"扩到了"AI 生成"**。早期版本只有 Pexels / Pixabay 拉库存片段；现在同一条流水线可以直接用 Seedance 之类的文生视频模型按脚本片段生成原创画面。两类源走的是同一个接口，后面的配音、字幕、合成流程完全不变。

**库存检索的机制**：LLM 产出的搜索关键词逐个向素材库发起搜索，下载后按目标画幅筛选。v1.3.4 加了两处工程改进：素材搜索结果持久缓存（减少重复请求和限流压力），以及优先挑选与目标横竖屏方向一致的素材。`match_materials_to_script = true` 可以让素材顺序贴合文案叙事顺序，TwelveLabs 集成（可选依赖）还能用视频理解模型对素材做语义重排。

**片段时长**由 `video_clip_duration` 控制：API 模型默认 5 秒，WebUI 偏好默认 3 秒。短视频"切换快 = 节奏紧"的观感主要靠这个参数调。AI 生成源各有自己的时长区间（如 Seedance 2-12 秒），超出区间的请求会被自动截到区间内，多余长度在剪辑时裁掉。

**计费注意**：库存三源免费；所有 AI 生成源都按量收费（config 注释里逐个写明 billed per clip / request / image），其中 MuAPI、秘塔 MiniMax H3、LoomLoom 三家要求在 WebUI 或 CLI 里显式确认后才会扣费生成。用 AI 素材跑批量前，先把单价和预算算清。

## §5 第 3 段：TTS 配音

`app/services/voice.py` 是全仓库最大的服务模块（约 3,600 行），因为要适配 **11 家 TTS 服务**。README 的原话列表：Edge TTS（免费、无需 API Key）、Azure Speech、SiliconFlow、Google Gemini、小米 MiMo、MiniMax、ElevenLabs、自托管 Chatterbox、自托管 Kokoro、Fish Audio、ModelBest VoxCPM。另有**上传配音**和**无配音**两种不走 TTS 的模式。

**关键命名澄清**（README 明确写了）：WebUI 里的 **Azure TTS V1 就是 Edge TTS**——走 Edge 浏览器内置的免费接口，无需付费 key。v1.1.2（2024-04）接入的付费 Azure Speech 服务叫 **V2**。两个名字容易混，按 Edge TTS / Azure TTS V2 记。

**声音选择**：Edge TTS 音色全表在 `docs/voice-list.txt`；API 层的默认音色是 `zh-CN-XiaoxiaoNeural-Female`（WebUI 里显示"女生-晓晓"），英文常用 `en-US-JennyNeural`，WebUI 里可以实时试听。自托管 Kokoro / Chatterbox 走 OpenAI 兼容协议，音色列表直接从服务端拉取。

**v1.3.x 的配音增强**：v1.3.3 加了整段配音预览（设置不变时可复用预览音频）；v1.3.7 支持在脚本里写 `[pause: 2s]` 或 `[停顿: 2s]` 原生插入停顿，旁白和字幕保持对齐；VoxCPM 还支持上传参考音频做音色复刻。

**给下游的接口**：TTS 生成音频的同时产出带时间戳的字幕对象（`sub_maker`），这是字幕段 edge 模式的输入。选了上传配音时没有 `sub_maker`，此时想要字幕就必须走 whisper 转写——两个模块的耦合点就在这里。

## §6 第 4 段：字幕生成

`app/services/subtitle.py` 实现两套字幕方案，理解它们的差异是调好短视频字幕的关键。

### 6.1 edge 模式（默认）

直接复用上一节 Edge TTS 返回的时间戳，对齐文案分段生成字幕。

- **速度**：零额外计算，CPU 无关，TTS 完成即得
- **缺点**：时间戳是 TTS 引擎"说这个词的时刻"，多音字、缩写、停顿密集的句子偶发错位
- **适用**：批量生成、对精度要求不高的内容

### 6.2 whisper 模式

用本地 `faster-whisper`（v1.1.0）转写已生成的音频，得到"声音实际出现的时刻"。

- **优点**：时间轴是测量值而非预估值，复杂句子更准
- **代价**：默认模型 `large-v3` 约 3 GB，首次使用要下载；`large-v3-turbo` 约 1.6 GB 更小更快，在 `[whisper]` 段改 `model_size` 即可切换；默认 CPU + int8 计算
- **上传配音场景**：没有 TTS 时间戳可用，whisper 是唯一能自动出字幕的路
- **v1.3.4 增强**：`initial_prompt` 可以往转写器里注入品牌名、术语表，减少专有名词识别错误

网络无法访问 Hugging Face 时，可手动下载模型目录放到 `models/whisper-large-v3/`（程序按这个路径找本地模型）。

**一个容易被忽略的中间步骤**：`subtitle.py` 里有 `correct()` 函数——whisper 转写结果会用编辑距离（Levenshtein）与 LLM 文案逐句对齐纠错，把"听错但意思对"的词拉回原稿。因为文案本来就是生成的，脚本即真值，这是流水线工具特有的免费校准。

### 6.3 字幕渲染

成片里的字幕是烧进画面的（任务目录里同时会留一份 `.srt` 文件）。渲染用 MoviePy 2.x 的 TextClip，底层是 Pillow——不再依赖 ImageMagick（v1.2.7 及更早的 README 还要求安装 ImageMagick 并配置 `imagemagick_path`，v1.3.0 前后这一系统依赖从文档中移除）。字体、位置、颜色、描边、背景、圆角都走 `config.toml` 的 `[ui]` 段；自定义字体扔进 `resource/fonts/` 即可被识别。v1.3.7 新增逐字字幕（word-by-word）和 pop_spring 弹出动画，位置支持五档预设加百分比自定义。

## §7 第 5 段：视频合成

`app/services/video.py`（约 1,900 行）是流水线最后一站：把前四段产物按时间轴拼成片。

**技术栈**：MoviePy 2.2.1（`pyproject.toml` 锁定）+ Pillow + FFmpeg。

**核心流程**：

1. **时间轴规划**：音频时长决定成片时长；素材片段循环或切换填满时间轴
2. **素材处理**：按段落顺序拼接，画幅适配可选 cover（裁切填满）或 contain（加黑边），转场支持 None / Shuffle / FadeIn 及 v1.3.3 新增的 ZoomIn / ZoomOut，片段速度全局可调
3. **字幕叠加**：按时间戳把字幕帧画到视频帧上
4. **配音 + 背景音乐混音**：BGM 从 `resource/songs/` 随机或指定（v1.3.3 起支持 WebUI 上传自定义 BGM、试听预设曲），也可用 Sonilo 或 ElevenLabs（music 模型）按视频内容生成原创配乐，失败自动回落；`bgm_volume` 默认 0.2，与配音音量独立
5. **FFmpeg 编码**：导出 mp4

**编码器是显式可配置的**：`video_codec` 支持 libx264（默认）、h264_nvenc、h264_amf、h264_qsv、h264_mf、h264_videotoolbox 六种，覆盖 NVIDIA / AMD / Intel / Windows Media Foundation / macOS VideoToolbox 的硬件编码。配置的编码器在当前环境不可用时，程序自动探测并回落到 libx264，而不是直接报错。拼接过慢还有 `ffmpeg_concat_timeout_seconds`（默认 3600 秒）兜底，卡死的任务会被标记失败而不是永远停在 50%。

**并发**：API 服务端有 `max_concurrent_tasks = 5`、`max_queued_tasks = 100` 的任务并发与排队上限；单条视频内部的片段处理并发由 `video_clip_concurrency` 控制。CLI 的批处理清单则是顺序执行——单个任务失败不阻断后续条目。

**为什么用 MoviePy 而不是裸调 FFmpeg**——MoviePy 是 FFmpeg 的 Python 封装，把"读视频 → 切片 → 拼接 → 混合 → 写出"变成可组合的 Python API，`task.py` 才能用一套代码编排所有源。代价是多一层抽象，收益是整个合成逻辑可测试、可移植（拼接环节实际上用 FFmpeg concat demuxer 做了专门优化，连路径转义都处理了）。

## §8 任务流案例：一次"主题 → 成片"的完整流转

`cli.py` 把流水线定义为 6 个阶段，`--stop-at` 可以停在任何一段之后：

```text
script → terms → audio → subtitle → materials → video
 文案     关键词   配音     字幕       素材下载    合成
```

注意两个容易想当然的地方：

- **配音和字幕排在素材下载之前**——audio/subtitle 不依赖素材，先跑完可以把等待 API 的时间压缩掉；也正因如此，`--stop-at materials` 得到的是"有声有字幕无画面素材"的中间产物
- **`--stop-at video` 是跑完全程**（video 是最后一段），不是"停在合成前"；想检查素材挑得对不对，停在 `materials`

下面用一条命令串起来（文案内容为示意）：

```bash
uv run python cli.py --video-subject "AI 编程入门" --voice-name zh-CN-XiaoxiaoNeural-Female
```

```text
## generating video script        script: LLM 产出分段文案（默认 1 段，可设 1-10 段）
## generating video terms         terms:  LLM 从文案提取搜索关键词
## generating audio               audio:  Edge TTS 生成配音 + 时间戳
## generating subtitle            subtitle: edge 模式直接复用时间戳；whisper 模式在此转写
## downloading videos from pexels materials: 按关键词检索下载，缓存到 storage/cache_videos/
## combining video: 1 => ...      video:  拼接 → 字幕 → 混音 → 编码
   final-1.mp4 落在 storage/tasks/<task_id>/
```

**几个具体细节**：

- 产物集中写在 `storage/tasks/<task_id>/`（`utils.task_dir()`），素材缓存默认在 `storage/cache_videos/`，`material_directory = "task"` 可改为按任务隔离，或指定绝对路径
- `--stop-at script` / `--stop-at materials` 这类断点是 CLI 独有的调试手段：先检查文案和素材是否符合预期，再决定是否合成
- 批量任务用 `--batch-file` 提供一个 JSON 数组或 JSONL 清单（最多 100 个任务、不超过 1 MiB），CLI 参数作全局默认，每个对象可覆盖 `VideoParams` 字段；所有条目在启动前统一预检，结束后输出 JSON 汇总
- 参数取值优先级（README 明确写了）：**命令行显式参数 > `config.toml` 里 `[ui]` 保存的 WebUI 设置 > 内置默认值**。WebUI 里选的"上传自备音频"不会被保存，CLI 要显式传 `--custom-audio-file`

## §9 跨平台发布：Upload-Post 集成

发布能力在 2026-03 加入（`app/services/upload_post.py` 首次提交），v1.3.1 补上 YouTube Shorts 支持，让"生成 + 发布"形成闭环。

```toml
upload_post_enabled = false          # 默认关闭，显式开启
upload_post_api_key = ""             # https://upload-post.com/ 注册
upload_post_username = ""
upload_post_platforms = ["tiktok", "instagram"]   # 可加 "youtube"
upload_post_auto_upload = false      # 成功后自动上传
upload_post_youtube_privacy_status = "public"     # public / unlisted / private
upload_post_youtube_made_for_kids = false         # 儿童内容需显式设 true
upload_post_max_pending_tasks = 10   # 单进程发布并发上限
```

**合规细节**：YouTube 隐私级别和"是否面向儿童"都是显式配置项——未配置时上传默认声明为非面向儿童。跨平台发布任务有独立并发上限（`upload_post_max_pending_tasks`），达到上限时视频生成照常成功、只拒绝发布请求；进程重启后未完成的发布任务不恢复。发布失败不影响本地成片——文件在任务目录里已经落盘。

**对内容矩阵号的价值**：多平台发同一段视频是矩阵号的基本操作，这条链路从"手动下载 mp4 → 三个 App 分别上传"压成一次配置。是否值得接入，取决于你的发布频率和 Upload-Post 的订阅价格——它是流水线里少数需要月度订阅的外部服务。

## §10 演进时间线：版本史里的四个工程动作

MoneyPrinterTurbo 不是"一次写完、慢慢死掉"的演示项目。下表时间与内容全部对照 GitHub Releases 与提交记录核实：

| 时间 | 版本 | 关键动作 |
|------|------|----------|
| 2024-03 | — | 仓库创建，3 月底已支持通义千问、Gemini 等多家 LLM |
| 2024-04 | v1.1.0 / v1.1.2 | 便携版；Azure 新增 9 种付费音色 |
| 2024-05 | v1.1.9 | 依赖里出现 MoviePy 2.0 dev 版（前瞻性升级） |
| 2024-12 | v1.2.2 | MoviePy 固定到 2.1.1 稳定线 |
| 2025-05 | v1.2.4 - v1.2.6 | 性能优化、SiliconFlow TTS、素材循环补齐音频时长 |
| 2026-03 | — | Upload-Post 跨平台发布引入 |
| 2026-04 | v1.2.7 | 全量迁移 uv 依赖管理（pyproject + uv.lock）、Edge TTS 兼容修复 |
| 2026-05 | v1.2.8 / v1.2.9 | LiteLLM（100+ 网关）、Grok、自定义音频上传、高级脚本设置 |
| 2026-06 | v1.3.0 | Coverr 素材源、无配音模式、6 种编码器 + 硬编自动回落、AIHubMix |
| 2026-07 | v1.3.1 - v1.3.3 | **纯 CLI 工作流**、YouTube Shorts、TwelveLabs、WebUI 重设计 + 任务管理、AI 配乐（Sonilo / ElevenLabs）、ZoomIn/ZoomOut 转场 |
| 2026-08 | v1.3.4 / v1.3.5 | whisper initial_prompt、素材缓存与朝向优先、Claude 原生接入、WaveSpeed / 胜算云 AI 视频素材、MiniMax / Fish Audio TTS |
| 2026-09 | v1.3.6 / v1.3.7 | **火山方舟 Seedance 原生、OFox、秘塔 MiniMax H3、文生图素材**；逐字字幕 + 动画、`[pause]` 停顿标记、Kokoro / VoxCPM |

四个版本段背后的工程动作值得单独看：

1. **依赖工程化**（2026-04）：从 requirements.txt 收敛到 pyproject.toml + uv.lock，`uv sync --frozen` 锁死依赖组合。一个 10 万 Stars 量级的项目做这个迁移，是为了让"不同机器跑出同一套环境"有保障。
2. **入口扩张**（2026-03 → 07）：WebUI 和 API 之外，先接 Upload-Post 补发布闭环，再加纯 CLI（v1.3.1），最后给出 AI Agent 技能文档（`docs/skill/SKILL.md`）。同一个 service 层，四条路进来。
3. **素材扩容**（2026-08 → 09）：两个月内接入 7 种 AI 生成素材源。这改变了项目的性质——从"库存视频的编排器"变成"库存 + 生成混合的画面供给层"，是整条流水线里变化最大的一段。
4. **声音与字幕精细化**（2026-07 → 09）：TTS 从 2 家扩到 11 家，配音预览、停顿标记、逐字字幕、音色复刻逐个补上——旁白质量是短视频观感的另一半。

**判断这类流水线项目"是否 production-ready"的信号**，MoneyPrinterTurbo 都具备：多供应商可替换、配置驱动、系统依赖最小化（ImageMagick 移除）、发布合规（隐私级别与儿童内容显式声明）、依赖锁文件。

## §11 部署路径

README 现在给出五种官方入口，按"想省事"到"想可控"排序：

### 11.1 AI Agent 生成（零安装）

把 `docs/skill/SKILL.md` 的链接发给支持读取 Skill 文档并操作本地终端的 AI Agent，它会自动完成安装、配置和生成，只在缺 API Key 时询问。目前支持 macOS 和 Windows。这是 README 推荐给"不想手动安装"用户的首选。

### 11.2 Google Colab（免配置体验）

`docs/MoneyPrinterTurbo.ipynb`，浏览器里直接跑，对只想试一次的用户最方便。

### 11.3 Windows 一键启动包

从 Release 页 Assets 下载 `.7z`（注意：GitHub 自动生成的 Source code 压缩包里只有 `webui.bat`，不含 `start.bat` / `update.bat`）。解压到无中文、无空格、无特殊字符的路径，先双击 `update.bat` 更新代码，再双击 `start.bat` 自动打开浏览器。`webui.bat` 的探测顺序：项目 `.venv` 或一键包内置 Python → 没有则回退到已安装的 `uv run streamlit`。`MPT_WEBUI_HOST=0.0.0.0` 可暴露给局域网。

### 11.4 Docker（环境隔离）

```bash
cd MoneyPrinterTurbo
docker compose -f docker-compose.release.yml up   # 拉取 ghcr.io/harry0703/moneyprinterturbo:latest
```

本地构建用 `docker compose up`；GPU 变体看 `Dockerfile.gpu` + `docker-compose.gpu.yml`。首次启动前把 `config.example.toml` 复制为 `config.toml` 供挂载。WebUI 在 8501，API 文档在 `http://127.0.0.1:8080/docs` 或 `/redoc`。

### 11.5 uv 本地部署（开发者）

```bash
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo
uv python install 3.11
uv sync --frozen
```

```bash
sh webui.sh                                              # WebUI（Windows 用 .\webui.bat）
uv run python main.py                                    # API 服务
uv run python cli.py --video-subject "人工智能如何改变日常生活"   # 纯命令行
```

`uv sync --frozen` 按 `uv.lock` 锁依赖；不走 uv 也可以 `venv + pip install -r requirements.txt`（`requirements.txt` 仅为兼容保留）。首次启动自动从 `config.example.toml` 生成 `config.toml`。

**API 侧的两个安全配置**值得部署时看一眼：`[app] api_key` 配置后，API 路由和 `/tasks` 产物下载都要求 `x-api-key` 请求头（浏览器地址栏无法带自定义头，鉴权模式下产物要用 HTTP 客户端下载）；API 默认只允许同源网页访问，独立前端才需要配 `CORS_ALLOWED_ORIGINS`。

## §12 常见问题与故障恢复

README 列了 3 个高频坑，加上部署时常见的几个问题：

- **`No ffmpeg exe could be found`**：FFmpeg 默认自动下载，失败时从 gyan.dev 手动下载，把路径写进 `[app]` 段的 `ffmpeg_path`（Windows 注意 `\\` 转义）
- **`OSError: [Errno 24] Too many open files`**：系统文件句柄限制过低，批量生成时易触发，`ulimit -n 10240` 调高
- **whisper 模型下载失败**：Hugging Face 访问受限时手动下载模型目录，放到 `models/whisper-large-v3/`（或对应 `model_size` 的目录名）
- **WebUI 打开空白**：README 建议换 Chrome 或 Edge（部分 Firefox / Safari 版本对 Streamlit 组件渲染异常）
- **国内访问素材库慢 / 超时**：`config.toml` 有专门的 `[proxy]` 段，给 Pexels / Pixabay / Coverr 和素材下载单独配 HTTP(S) 代理，不用动系统代理
- **从 v1.2.7 及更早版本升级后 ImageMagick 相关报错**：旧版 README 要求安装 ImageMagick，v1.3.0 起字幕渲染已改用 Pillow，先 `git pull`（一键包用户跑 `update.bat`）再按新文档检查配置
- **某个编码器报错或不生效**：`video_codec` 配了当前环境不支持的硬件编码器时，程序会自动回落 libx264 并在日志里说明原因，不需要手动排查驱动
- **Upload-Post 调用失败但本地生成成功**：先确认 `upload_post_enabled = true`、账号订阅有效；发布失败不影响已成片的本地文件

**批量任务的容错**：`--batch-file` 清单里的相对路径以清单所在目录为基准；所有条目在第一个任务启动前完成参数与本地文件预检；单个任务失败记录在 JSON 汇总的 `failed_stage` / `error` 字段里，不会中断后续条目。

## §13 硬件门槛与耗时结构

README 给出的硬件建议：

| 项目 | 最低 | 推荐 | 理想 |
|------|------|------|------|
| CPU | 4 核 | 6-8 核 | 8 核+ |
| RAM | 4 GB | 8 GB | 16 GB+ |
| GPU | 非必须 | 4 GB 显存+ | 8 GB 显存+ |

**怎么读这张表**——README 同时给了判断依据：如果主要依赖云端 LLM、云端 TTS 和在线素材，CPU 和内存比 GPU 重要；启用 `faster-whisper` 本地转写、批量生成或更重的本地处理链路时，GPU 提升明显。一键包和 Colab 对硬件要求最低，因为默认走云端 API。

**一条流水线里时间花在哪**，按阶段定性排：

- **LLM 文案与关键词**：瓶颈在模型服务的响应速度，与本地硬件无关
- **素材**：库存检索取决于素材库 API 与带宽；AI 生成源是异步任务，提交后按轮询间隔等待结果（config 里各家轮询 5-10 秒一次、单次任务超时上限 1800 秒），实际等待取决于服务商排队——它往往是整条流水线里最不可控的一段
- **TTS**：云端服务取决于网络；本地 whisper 转写在 CPU 上明显慢于 GPU（README 的原话是"GPU 会明显提升速度"）
- **合成编码**：软件编码（libx264）吃 CPU；配置硬件编码器（NVENC / VideoToolbox 等）后编码段显著减负，不支持的设备自动回落
- **发布**：Upload-Post 按 10 个并发上限排队，与生成硬件无关

具体的"一条件耗时 X 秒"我不写——它取决于你的网络、所选模型和机器，换一个环境数字就作废。要建立自己的预期，用 `--stop-at` 分段计时跑一遍最准。

## §14 成本结构：钱花在哪个环节

配置文件把每个环节的计费方式写得很清楚，按"免费 → 按量 → 订阅"分三档：

| 环节 | 计费方式 | 说明 |
|------|----------|------|
| LLM 文案 | 按 token | DeepSeek、Kimi 等按量计费；`claude_code` 走订阅额度；Ollama 本地零成本 |
| Edge TTS | 免费 | 无需 key，Azure TTS V1 即它 |
| Azure TTS V2 等云端 TTS | 按字符 / 用量 | 各平台计费规则不同 |
| Pexels / Pixabay / Coverr | 免费 | 需注册 API key，有平台侧限流 |
| 本地素材 | 免费 | 无 API 调用 |
| AI 生成素材（Seedance / OFox / MiniMax H3 / WaveSpeed / MuAPI / 文生图） | 按片段或按图片 | config 注释逐项写明 billed per clip/request/image；MuAPI、LoomLoom 生成前需显式确认 |
| whisper 字幕 | 免费 | 本地计算，成本是时间与电费 |
| Upload-Post 发布 | 订阅 | 流水线里少数月费环节 |

**关键判断**：全免费组合（DeepSeek/Kimi + Edge TTS + Pexels + edge 字幕 + libx264 + 不接发布）下，单条视频的现金成本接近于零，只有上游 LLM 的 token 费。真正要预算的是两处——**AI 生成素材**（按条计费，批量场景下线性放大）和 **Upload-Post 订阅**。用 AI 素材前在 WebUI 里单条试跑确认单价，再决定是否批量。

## §15 与同类的对比

从工程定位看几个关键差异（定位描述基于各家公开资料，不构成横向评测）：

| 维度 | MoneyPrinterTurbo | ComfyUI 系视频工作流 | Canva AI | HeyGen |
|------|------------------|----------------------|----------|--------|
| 核心定位 | 流水线集成层 | 节点编排 | SaaS 模板 | 数字人 SaaS |
| 是否开源 | ✅ MIT | ✅ 多为开源 | ❌ | ❌ |
| 本地部署 | ✅ 五种入口 | ✅ | ❌ | ❌ |
| 画面来源 | 库存 + AI 生成混合 | 完全自定义 | 模板 + 素材库 | AI 数字人口播 |
| 供应商锁定 | 无（31 个 LLM 段、11 家 TTS 可换） | 无 | 内置 | 内置 |
| 上手成本 | 配置 + 一条命令 | 需理解节点图 | 最低 | 最低 |
| 适用人群 | 自媒体 / 矩阵号 / 开发者 | 创作者 / 研究者 | 普通用户 | 企业 / 营销 |

- **vs ComfyUI 系工作流**：节点编排灵活度更高（任意接视频生成模型），但学习曲线和部署复杂度也高。MoneyPrinterTurbo 是"流水线写死、供应商可换"的路线——想改流水线结构本身，得 fork 改 `task.py`
- **vs Canva AI**：SaaS 模板路线，浏览器里拖模板出片。MoneyPrinterTurbo 是本地流水线路线，换取的是批量能力、私有部署和供应商自由
- **vs HeyGen**：数字人口播是"AI 人物出镜"，MoneyPrinterTurbo 做的是"旁白 + 素材"。需要"人"在场的内容，它给不出

**对自媒体内容工厂**——MoneyPrinterTurbo 是当前开源世界里投入产出比突出的选择：现金成本集中在 LLM token 和可选的 AI 素材费，没有月费门槛（除非接 Upload-Post）；天花板也明确——做不出 Canva 的视觉精致度，做不出 HeyGen 的数字人，画面质感上限取决于你愿意为 AI 素材付多少。

## §16 适用边界与采用顺序

### 16.1 适合采用

- **短视频矩阵号**（TikTok / Reels / Shorts）：批量生成 + 跨平台发布是核心场景
- **自媒体内容工厂**：LLM 批量出选题，`--batch-file` 一晚跑一批，挑好的发布
- **不想碰 FFmpeg 命令行但要精细控制字幕样式**的开发者：Pillow 渲染 + `config.toml` 字体配置
- **需要 API 集成到自有平台 / Agent**：FastAPI 自带 Swagger，`docs/skill/` 直接给了 Agent 接入文档

### 16.2 谨慎采用

- **真人出镜 / 强表演类内容**：流水线做的是"素材 + 旁白"，不做人物合成
- **强版权要求的内容**：库存素材的许可以 Pexels / Pixabay / Coverr 各自条款为准；AI 生成素材的商用边界取决于所选模型服务商的条款，生成前逐家确认
- **需要深度品牌化模板的团队**：可改（Apache/MIT 协议无障碍），但改流水线要动 `task.py` 和 `webui/Main.py`，成本高于 SaaS

### 16.3 不适用

- **电影级长视频（>5 分钟）**：架构针对短视频，长视频的字幕同步 / 素材管理需要专业工具链（DaVinci Resolve、Premiere）
- **完全离线内网**：LLM、TTS、素材库都默认云端，纯内网要自己换成本地栈（Ollama + 自托管 Kokoro/Chatterbox + 本地素材 + 本地 ComfyUI 文生图——理论上能拼出来，配置量不小）
- **强人格化 IP 系列**：脚本、配音、字幕都是生成物，没有"我自己的声音"和"我自己的风格"的位置——这是流水线工具的天然限制

### 16.4 一个具体的"系列化失败"案例

假设你的系列叫"张三聊财经"，要求每条都有张三的声音和张三的金句。MoneyPrinterTurbo 会在这里失败：

- **声音**：默认音色是"晓晓"，那是微软训练的声音模型，不是张三（除非你走 VoxCPM 参考音频复刻，且复刻质量需自行验证）
- **金句**：文案是 LLM 生成的，不会有张三的原话
- **节奏**：张三"开场打招呼 + 叙事 + 结尾反问"的节奏是反复打磨的个人风格，prompt 调得再细也不如真人口播自然
- **视觉**：字幕字体、配色、转场默认值全网趋同，品牌团队会觉得"都是同一个调调"

它能做好的是"知识科普 / 行业解读 / 资讯速报"这类"旁白 + 素材"型内容的高质量批量化；做不了"人格化 IP"的差异化。前者看日产量，后者看个人辨识度，两个方向。

### 16.5 采用顺序建议

**第一步（半天）**：Colab 或一键包跑通默认配置，对成片质量建立直观感受。只为看效果，不投入配置。

**第二步（2-3 天）**：本地 uv 部署，按内容主题调 `config.toml`——选 LLM 提供商、定字幕模式（edge 还是 whisper）、选 TTS 声音、配素材源（先库存，预算允许再试 AI 生成）。

**第三步（1-2 周）**：接入生产流程——`--batch-file` 批量生成、配 Upload-Post 发布、把 FastAPI 对接到自有系统或用 SKILL.md 接入 Agent。

**第四步（按需）**：深入 `app/services/` 做定制——自定义字幕样式、素材筛选规则、接入企业 LLM 网关。

**什么时候该停**：如果你的内容 80% 是真人出镜 / 强个性化，这个工具不合适；如果 80% 是"旁白 + 素材"型内容，它能一直用下去。

## §17 自测清单

- 说出流水线 6 个阶段的名称和顺序，以及为什么 audio/subtitle 排在 materials 之前
- 解释 "Azure TTS V1" 和 "Azure TTS V2" 的实际区别
- 解释 edge 字幕和 whisper 字幕的取舍，以及什么场景下 whisper 是唯一选项
- 说出 `--stop-at video` 和 `--stop-at materials` 各停在哪里
- 解释 `task.py` 为什么是四种入口的唯一握手点
- 说出 AI 生成素材与库存素材在计费方式上的差异
- 说出 v1.2.7 → v1.3.0 之间砍掉了哪个系统依赖
- 解释 Upload-Post 集成对 YouTube 的两个显式合规配置

## §18 参考链接

- [GitHub: harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) —— 主仓库（v1.3.7，MIT）
- [README 中文](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/README.md) / [English](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/README-en.md) / [日本語](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/README-ja.md)
- [config.example.toml](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/config.example.toml) —— 全部可配置项与计费说明的真相
- [cli.py](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/cli.py) —— 6 阶段流水线与批处理清单
- [AI Agent Skill](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/docs/skill/SKILL.md) —— Agent 接入文档
- [音色列表](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/docs/voice-list.txt) —— Edge TTS 全部音色
- [Google Colab Notebook](https://colab.research.google.com/github/harry0703/MoneyPrinterTurbo/blob/main/docs/MoneyPrinterTurbo.ipynb) —— 免配置体验
- [Upload-Post](https://upload-post.com/) —— 跨平台发布 API
- [MoviePy](https://zulko.github.io/moviepy/) —— 视频合成底层
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) —— whisper 字幕底层
- [edge-tts](https://github.com/rany2/edge-tts) —— 免费 TTS Python 封装

## 练习

### 练习 1：部署并生成第一条视频

本地用 uv 部署，完成：
1. 首次启动让程序自动生成 `config.toml`，在 WebUI 里配一个 LLM 提供商（默认 Kimi，或换 DeepSeek）
2. 用 Edge TTS + edge 字幕 + Pexels 素材的默认组合生成一条 60 秒竖屏视频
3. 用 `--stop-at` 分段计时（script / materials 各停一次），记录每段耗时，得出你环境里的单条总耗时

### 练习 2：对比 edge 和 whisper 字幕

同一条文案生成两个版本（改 `[app] subtitle_provider`），对比：
- 中英文混排句子的时间轴对齐
- 数字和缩写（"AI"、"LLM"、"2026"）
- 在脚本里加 `[pause: 2s]` 后，两种模式的时间轴表现

再用 `[whisper] initial_prompt` 注入几个专有名词，观察识别变化。

### 练习 3：批量生成

1. 写一个含 5 个主题的 JSONL 清单，故意让其中一个的参数非法
2. `uv run python cli.py --batch-file tasks.jsonl` 跑完
3. 检查 JSON 汇总：`total` / `succeeded` / `failed` 与 `failed_stage` 字段，验证"单任务失败不阻断"

### 练习 4：读编排层

阅读 `app/services/task.py`，完成：
1. 画出 6 个阶段各自读写的产物文件（提示：都在 `storage/tasks/<task_id>/` 下）
2. 找到 `--stop-at` 的判断位置（`cli.py` 的 `_PIPELINE_STAGES`）
3. 观察素材缓存：同一主题跑两遍，第二遍的 materials 阶段快在哪里（v1.3.4 的持久缓存）

## 进阶路径

### 路径 1：从用户到贡献者

1. **深入一个服务模块**：`subtitle.py`（383 行）最短，先读它；`voice.py`（约 3,600 行）最大，按 provider 分块读
2. **接一个新 provider**：TTS 或素材源，照着现有 adapter 的接口写；`app/models/llm_provider.py` 的注册表模式也值得学
3. **提交 PR**：仓库活跃（2026-10 仍在持续合入），issue 和 PR 通道都开着

### 路径 2：从工具到平台

1. **选题池**：LLM 批量出选题，打分筛选后写进 `--batch-file` 清单
2. **质量卡口**：`--stop-at subtitle` 后先检查文案与字幕，再放行合成；用 JSON 汇总做流水线监控
3. **发布编排**：Upload-Post 之上做定时与平台差异化
4. **数据闭环**：跟踪播放 / 完播，反馈到 prompt 与选题——这一步的技术栈已超出工具本身

### 路径 3：从编排到生成

MoneyPrinterTurbo 的画面供给已经混合了库存与 AI 生成，如果你要更进一步：
1. **可控视频生成**：Seedance、Wan 这类模型的直连用法（本项目里的 `volcengine_seedance.py` / `oflox` adapter 就是现成参考）
2. **数字人**：HeyGen、D-ID 一类产品，或开源的口播合成方案——需要"人物出镜"时的方向
3. **专业后期**：DaVinci Resolve、Premiere——编排工具的天花板之上

MoneyPrinterTurbo 是入口，不是终点。

## 事实核验与引用

### 核验表

| 关键数据 | 来源 | 核验状态 |
|---------|------|---------|
| 128,059 Stars / 20,028 Forks / MIT（2026-10-03） | GitHub API `repos/harry0703/MoneyPrinterTurbo` | ✅ |
| 最新 Release v1.3.7（2026-09-13）；全版本日期 | GitHub API releases 列表 | ✅ |
| 仓库创建 2024-03-11 | GitHub API `created_at` | ✅ |
| Python ≥3.11；moviepy==2.2.1；faster-whisper==1.1.0；litellm==1.86.2 | `pyproject.toml`（v1.3.7） | ✅ |
| 默认 `llm_provider = "moonshot"`；LLM 配置段共 31 个 | `config.example.toml` + 逐项清点 | ✅ |
| 11 家 TTS（含无配音 / 上传两种非 TTS 模式） | README「语音合成」节 + config `[azure]` 等段落 | ✅ |
| `video_source` 11 种取值；AI 生成源按量计费、部分需确认 | `config.example.toml`「Video Materials」注释 | ✅ |
| 流水线 6 阶段顺序；`--stop-at` 语义（停在该阶段之后） | `cli.py` epilog「Pipeline stages」 | ✅ |
| 批处理清单 ≤100 任务、≤1 MiB、单任务失败不阻断 | `cli.py` + README「纯命令行方式」 | ✅ |
| API 并发 `max_concurrent_tasks=5` / 排队 100；发布并发上限 10 | `config.example.toml` | ✅ |
| 任务产物 `storage/tasks/<task_id>/`；素材默认 `storage/cache_videos/` | `app/utils/utils.py` `task_dir()`、`material.py` | ✅ |
| 默认音色 `zh-CN-XiaoxiaoNeural-Female`；段落数 1-10 | `app/models/schema.py` | ✅ |
| whisper 默认 large-v3（约 3 GB）/ large-v3-turbo（约 1.6 GB） | README「字幕生成」 | ✅ |
| 字幕纠错用 Levenshtein 对齐脚本 | `app/services/subtitle.py` `correct()` | ✅ |
| 6 种 video_codec + 不可用自动回落 libx264 | `config.example.toml` 注释 + `video.py` `_write_videofile_with_codec_fallback` | ✅ |
| ImageMagick 要求到 v1.2.7 README 仍在，v1.3.0 前后移除 | v1.2.7 / v1.3.0 README 对比 | ✅ |
| Upload-Post 首次提交 2026-03-25；YouTube Shorts 于 v1.3.1 | 提交历史 + v1.3.1 Release notes | ✅ |
| MoviePy 2.0 dev 自 v1.1.9（2024-05）启用，v1.2.2 起 2.1.x | v1.1.9 / v1.2.2 `requirements.txt` | ✅ |
| Azure 9 种新音色于 v1.1.2（2024-04-16） | v1.1.2 Release notes | ✅ |
| 硬件建议表 | README「配置要求」 | ✅ |

### 引用说明

- 所有 Stars / Forks / 版本号均为 2026-10-03 快照，会随时间漂移，引用前请重新查询
- 本文不包含无出处的耗时与成本数字；涉及计费的表述以 `config.example.toml` 注释与各服务商定价页为准
- 上游 API（Pexels / Pixabay / Upload-Post / 各模型服务）的限流与价格由对应服务商随时调整，商用前逐家确认

> **本文定位**：MoneyPrinterTurbo 架构拆解 + 素材供给演进分析 + 适用边界决策
> **更新记录**：v1.2 - 2026-10-03 依据 main 分支源码、config.example.toml、GitHub Releases 复核并校正全部事实（版本时间线、提供商清单、流水线阶段、存储路径、计费方式），删除无来源的耗时与成本数字；后续随官方发布滚动更新
