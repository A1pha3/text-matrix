---
title: "MoneyPrinterTurbo：把 LLM + TTS + FFmpeg 打包成一条主题到成片的流水线"
date: "2026-06-25T21:13:09+08:00"
slug: "harry0703-moneyprinterturbo-short-video-automation-guide-2026"
description: "harry0703/MoneyPrinterTurbo 是 92k+ Stars 的开源短视频自动生成工具，给定主题或关键词就能完成文案生成、素材搜索、TTS 配音、字幕渲染和视频合成全流程。本文拆开它的 7 步任务流水线、20+ LLM provider 路由、3 种素材源、双 TTS 引擎和 MoviePy 2.x 合成链路，附上一个完整的任务流案例和选型决策。"
draft: false
categories: ["技术笔记"]
tags: ["MoneyPrinterTurbo", "AI视频生成", "短视频自动化", "FFmpeg", "MoviePy", "TTS", "LLM", "Python"]
---

# MoneyPrinterTurbo：把 LLM + TTS + FFmpeg 打包成一条主题到成片的流水线

## §1 先给判断

MoneyPrinterTurbo 解决的问题很具体：你给它一个主题——"金钱的作用"、"如何增加生活的乐趣"——它就帮你生成文案、搜索素材、合成语音、渲染字幕、拼接视频，最后吐出一个带配音带字幕的高清短视频。

这件事拆开来看，每一步都有成熟的开源工具：LLM 写文案、Edge TTS 做语音合成、Pexels/Pixabay 提供素材、FFmpeg 合成视频。MoneyPrinterTurbo 的价值不在发明新技术，而在把这些环节串成一条可配置、可批量、可编程的流水线，并且把每一步的 provider 做成可插拔设计——TTS 不行就换、素材源不行就换、LLM 不行就换。

92k+ Stars 和 13k+ Forks 的数字背后是一个清晰的定位：它不做视频编辑器，不做特效引擎，也不跟 Sora / Runway 竞争生成质量。它做的是"内容创作者的自动化流水线"——目标用户是自媒体、营销团队和教育内容生产者，痛点是"每天手剪 5 条短视频太累了"。

这篇文章拆开 MoneyPrinterTurbo 的 7 步任务流水线（从 `start()` 到 `final.mp4`），分析它的 provider 抽象设计（20+ LLM、3 种素材源、双 TTS 引擎），并用一个完整的任务流案例把全链路串起来。

## §2 项目定位与系统边界

| 项目 | 内容 |
|------|------|
| **仓库** | github.com/harry0703/MoneyPrinterTurbo |
| **当前版本** | v1.3.0（2026-06-10） |
| **Stars / Forks** | 92.4k+ / 13.3k+ |
| **语言** | Python（FastAPI 后端 + Streamlit WebUI） |
| **License** | MIT |
| **视频合成** | MoviePy 2.x + FFmpeg + Pillow |
| **目标用户** | 自媒体创作者、营销团队、教育内容生产者 |
| **输入** | 视频主题或关键词（可选自定义文案） |
| **输出** | 竖屏 9:16（1080×1920）/ 横屏 16:9（1920×1080）/ 正方形 1:1（1080×1080）|
| **LLM provider** | OpenAI、DeepSeek、Moonshot、通义千问、Gemini、Ollama、MiniMax、文心一言、Groq、Cloudflare、LiteLLM、Pollinations、ModelScope、AIHubMix、AIML API、EvoLink、Azure、one-api、gpt4free、MiMo 等 20+ |
| **TTS 引擎** | Edge TTS（免费）/ Azure TTS V2（付费）/ ElevenLabs / SiliconFlow / MiMo |
| **素材源** | Pexels、Pixabay、Coverr、本地文件 |
| **部署方式** | Windows 一键包 / Docker / uv + venv / Google Colab |

MoneyPrinterTurbo 不是一个视频编辑器，也不是一个 AI 模型。它是一个编排层——把 LLM 文案生成、TTS 语音合成、素材搜索、字幕渲染和视频拼接编排成一条端到端的流水线，每一步的 provider 都可以替换。

这决定了它的工程取舍：不在视频质量上竞争（输出是素材拼接 + 字幕 + 配音，不是 AI 生成画面），不在模型能力上竞争（LLM、TTS、素材都是外部服务，它做的是粘合），在流水线完整性和 provider 可插拔性上竞争（一条主题到成片的链路，每个环节都能换供应商）。

### 本文阅读路径

- **想看流水线全貌**：§3 总览图 → §4 七步任务流
- **想看 provider 设计**：§5 LLM 路由 → §6 TTS 引擎 → §7 素材源
- **想看视频合成**：§8 MoviePy 链路
- **想看部署和配置**：§9 部署方式 → §10 配置体系
- **想看完整案例**：§11 任务流案例
- **想看选型决策**：§12 适用场景

## §3 一张总览图：MoneyPrinterTurbo 的东西怎么分

在深入代码之前，先看系统全貌。MoneyPrinterTurbo 分三层：

```
MoneyPrinterTurbo
│
├── 入口层
│   ├── webui/                    # Streamlit Web 界面（主交互入口）
│   │   ├── Main.py               # Streamlit 入口
│   │   └── i18n/                 # 9 种语言（zh/en/de/es/id/pt/ru/tr/vi）
│   ├── main.py                   # FastAPI ASGI 服务（API 入口）
│   └── cli.py                    # 纯命令行入口（无浏览器）
│
├── 服务层（app/services/）
│   ├── task.py                   # 7 步任务编排器（核心，480 行）
│   ├── llm.py                    # LLM provider 路由（20+ provider，1132 行）
│   ├── voice.py                  # TTS 引擎（Edge TTS / Azure / ElevenLabs / SiliconFlow / MiMo）
│   ├── material.py               # 素材搜索（Pexels / Pixabay / Coverr）
│   ├── subtitle.py               # 字幕生成（edge / whisper）
│   ├── video.py                  # 视频合成（MoviePy 2.x + FFmpeg）
│   └── upload_post.py            # 跨平台发布（TikTok / Instagram / YouTube Shorts）
│
└── 模型层
    ├── app/models/schema.py      # Pydantic 数据模型（VideoParams 等）
    ├── app/models/const.py       # 任务状态常量
    └── app/config/config.py      # TOML 配置加载
```

入口层有 3 个入口：WebUI（Streamlit）、API（FastAPI）、CLI。三个入口共享同一套服务层，服务层共享同一套数据模型。无论从哪个入口进来，任务执行的链路完全一致。

任务编排的核心在 `task.py` 的 `start()` 函数——7 步流水线在这里依次执行：

```
主题/关键词
  │
  ▼
┌───────────────────────────────────────────────────┐
│ 1. 文案生成（LLM）                                  │
│    └─ llm.generate_script() → video_script        │
├───────────────────────────────────────────────────┤
│ 2. 关键词生成（LLM）                                │
│    └─ llm.generate_terms() → video_terms[]         │
├───────────────────────────────────────────────────┤
│ 3. 语音合成（TTS）                                  │
│    └─ voice.tts() → audio.mp3 + sub_maker          │
├───────────────────────────────────────────────────┤
│ 4. 字幕生成（edge / whisper）                        │
│    └─ subtitle.create() → subtitle.srt             │
├───────────────────────────────────────────────────┤
│ 5. 素材获取（Pexels / Pixabay / Coverr / 本地）      │
│    └─ material.download_videos() → [video clips]   │
├───────────────────────────────────────────────────┤
│ 6. 视频拼接（MoviePy + FFmpeg）                     │
│    └─ video.combine_videos() → combined-N.mp4      │
├───────────────────────────────────────────────────┤
│ 7. 字幕+配音合成 → 最终输出                          │
│    └─ video.generate_video() → final-N.mp4         │
│    └─ (可选) upload_post.cross_post_video()         │
└───────────────────────────────────────────────────┘
  │
  ▼
final-1.mp4（1080×1920 或 1920×1080）
```

每一步都有 `stop_at` 检查点——可以只跑前几步。`stop_at="script"` 只生成文案，`stop_at="audio"` 只生成到音频，`stop_at="materials"` 只下载素材。这个设计让 MoneyPrinterTurbo 也可以作为"文案生成器"、"TTS 工具"、"素材下载器"单独使用。

## §4 七步任务流：从 `start()` 到 `final.mp4`

`app/services/task.py` 的 `start()` 函数是整个项目的核心——480 行代码完成了从主题到成片的全部编排。

### Step 1: 文案生成

```python
video_script = generate_script(task_id, params)
```

如果用户提供了 `video_script`（自定义文案），直接使用；否则调用 `llm.generate_script()`，传入主题、语言、段落数、自定义 prompt。LLM 返回纯文本文案，经过 `_normalize_text_response()` 清理 `<think>` 标签和空内容。

失败处理：LLM 返回空字符串或 "Error: " 前缀 → 标记任务失败，终止。

### Step 2: 关键词生成

```python
video_terms = generate_terms(task_id, params, video_script)
```

如果用户提供了 `video_terms`，直接使用（支持逗号分隔字符串或列表）；否则调用 `llm.generate_terms()`，基于主题和文案生成搜索关键词。

当 `match_materials_to_script=True`（按文案顺序匹配素材）时，关键词数量从默认的 5 个增加到 8 个，并且要求 LLM 按脚本叙事顺序排列。源码注释说明了原因——如果关键词不按叙事顺序排列，后续即使顺序下载和顺序拼接，也只能复用一组全局主题词，无法改善"后面内容的画面提前出现"的问题。

### Step 3: 语音合成

```python
audio_file, audio_duration, sub_maker = generate_audio(task_id, params, video_script)
```

TTS 引擎把文案转成 `audio.mp3`，同时返回 `sub_maker`（字幕对齐对象，包含每个词的时间戳）。如果用户提供了 `custom_audio_file`，跳过 TTS 直接使用自定义音频——此时 `sub_maker` 为 `None`，后续字幕生成会走 whisper 路径。

失败处理：源码的 error message 写得很直白——"check if the language of the voice matches the language of the video script"和"check if the network is available"。

### Step 4: 字幕生成

```python
subtitle_path = generate_subtitle(task_id, params, video_script, sub_maker, audio_file)
```

两种字幕模式：

- **edge 模式**：用 Edge TTS 返回的 `sub_maker` 时间戳直接生成 SRT。速度快、不需要 GPU，但复杂句子的时间戳偶尔不准。
- **whisper 模式**：用本地 `faster-whisper` 转写音频生成 SRT。需要下载模型（large-v3-turbo 约 250MB），速度慢但准确度更高。

edge 模式失败时自动 fallback 到 whisper——保证了字幕生成的鲁棒性。

### Step 5: 素材获取

```python
downloaded_videos = get_video_materials(task_id, params, video_terms, audio_duration)
```

两种素材来源：

- **本地素材**：`video_source="local"`，用户已提供 `video_materials` 列表，`video.preprocess_video()` 做裁剪。
- **在线素材**：`video_source="pexels"` / `"pixabay"` / `"coverr"`，`material.download_videos()` 根据关键词搜索并下载无版权视频。

素材总时长需要覆盖音频时长 × 视频数量。如果 `video_count=3`（一次生成 3 个视频），素材需求量 = `audio_duration × 3`。

### Step 6: 视频拼接

```python
combined_video_path = video.combine_videos(...)
```

`video.combine_videos()` 把素材片段按 `video_concat_mode` 拼接：

- **random**：随机打乱素材顺序（默认，增加多视频差异）
- **sequential**：按下载顺序拼接（`match_materials_to_script=True` 时强制使用）

每个片段的时长由 `video_clip_duration` 控制（默认 5 秒）。支持的转场：FadeIn、FadeOut、SlideIn、SlideOut、Shuffle。

### Step 7: 字幕 + 配音合成

```python
final_video_path = video.generate_video(...)
```

`video.generate_video()` 把 `combined-N.mp4`、`audio.mp3`、`subtitle.srt` 合成最终视频：

- 音频：TTS 配音和背景音乐混合（`bgm_volume` 控制音量比）
- 字幕：用 Pillow 渲染（MoviePy 2.x 不再依赖 ImageMagick）
- 输出：H.264 + AAC 192k，30fps

如果配置了 Upload-Post 服务，最后一步还会自动上传到 TikTok / Instagram / YouTube Shorts。YouTube 上传时自动标注 `containsSyntheticMedia=True`。

## §5 LLM provider 路由：20+ 供应商的统一接口

`app/services/llm.py` 是全项目最复杂的文件——1132 行代码，处理 20+ 种 LLM provider 的接入。

### 5.1 provider 分类

| 类型 | provider | 特点 |
|------|----------|------|
| **OpenAI 兼容** | openai、aihubmix、aimlapi、oneapi、evolink、mimo、deepseek、minimax | 共享 OpenAI SDK 调用链路，只需换 `base_url` 和 `api_key` |
| **独立 SDK** | moonshot、azure、gemini、qwen、cloudflare、ernie、modelscope | 各自走原生 SDK 或 HTTP API |
| **本地模型** | ollama | 走本地 Ollama HTTP API，不需要 API key |
| **网关聚合** | litellm | 一个网关接 100+ provider |
| **免费/实验** | gpt4free、pollinations | 不需要 API key，稳定性和质量不保证 |

OpenAI 兼容的 provider 占了 8 个。这不是巧合——2024 年以后大部分国产和第三方 LLM 服务商都提供了 OpenAI 兼容接口，改 `base_url` 和 `api_key` 就能接入。MoneyPrinterTurbo 把这个生态红利吃满了。

### 5.2 文案 prompt 的 7 条约束

文案生成的 system prompt（`DEFAULT_SCRIPT_SYSTEM_PROMPT`）有 7 条约束，确保 LLM 输出可以直接送入 TTS：

- 第 4 条"never use a title"和第 6 条"do not include voiceover"排除了 LLM 最常见的格式化倾向——不加这两条约束，LLM 几乎一定会输出 `# 金钱的作用\n\nVoiceover: 金钱作为...` 这种格式。
- 第 8 条"respond in the same language as the video subject"确保中文主题生成中文文案，英文主题生成英文文案。

关键词生成走不同的 prompt：要求 LLM 从文案中提取搜索词并按 JSON 数组返回。`_strip_code_fence()` 函数处理了 Claude / Gemini 等模型把 JSON 包在 markdown code fence 里的情况。

### 5.3 `<think>` 标签清理

DeepSeek R1、MiniMax M3 等 reasoning 模型会把推理过程包在 `<think>...</think>` 里返回。`_normalize_text_response()` 用两个正则处理：

```python
_THINK_BLOCK_RE = re.compile(r"<think\b[^>]*>.*?</think>", re.IGNORECASE | re.DOTALL)
_UNCLOSED_THINK_BLOCK_RE = re.compile(r"<think\b[^>]*>.*$", re.IGNORECASE | re.DOTALL)

content = _THINK_BLOCK_RE.sub("", content)
content = _UNCLOSED_THINK_BLOCK_RE.sub("", content).strip()
```

第二个正则处理未闭合标签——模型输出被截断时可能只有开标签没有闭标签。

### 5.4 错误信息脱敏

`_sanitize_error_message()` 清理返回给 WebUI/API 的错误信息，避免自定义 `base_url` 中的凭据泄露。一些 OpenAI 兼容 SDK 会把请求 URL 原样拼进异常信息——如果用户配了 `https://user:pass@example.com/v1`，直接返回 `str(e)` 就会把密码暴露：

```python
message = _URL_USERINFO_RE.sub(r"\1***:***@", message)
message = _SENSITIVE_QUERY_RE.sub(r"\1***", message)
```

两个正则分别清理 URL 中的用户名密码和 query 参数里的 API key。对接了 20+ 第三方服务的项目不能省这层防护——用户配的代理网关 URL 里可能有凭据，一旦 LLM SDK 把 URL 拼进异常信息，密钥就会泄露到 WebUI 或日志里。

## §6 TTS 引擎：从免费 Edge TTS 到 ElevenLabs

| 引擎 | 费用 | 质量 | 延迟 | 特点 |
|------|------|------|------|------|
| **Edge TTS** | 免费 | 中等 | 低 | 默认引擎，300+ 声音，不需要 API key |
| **Azure TTS V2** | 付费 | 高 | 低 | 需要 Azure Speech 订阅，9 种声音更自然 |
| **ElevenLabs** | 付费 | 很高 | 中 | v1.3.0 新增，高质量多语言声音克隆 |
| **SiliconFlow** | 付费 | 高 | 中 | CosyVoice2 模型，8 种声音 |
| **MiMo** | 付费 | 高 | 中 | 小米 MiMo TTS v2.5 |

WebUI 里 "Azure TTS V1" 就是 Edge TTS（免费），"Azure TTS V2" 是付费 Azure Speech SDK。README 明确标注了两者是不同选项。

v1.3.0 新增的 `no-voice` 模式让视频可以只出画面不出声音。代码用 `_NO_VOICE_ALIASES = {"no-voice", "none"}` 做兼容——`none` 是 PR #981 里曾使用的标识，这里短期兼容避免已调用过该分支的 API 用户升级后立即失效。

Edge TTS 有 30 秒超时保护（`_DEFAULT_EDGE_TTS_TIMEOUT_SECONDS = 30.0`）。网络异常或服务端限流时 edge_tts 可能长期卡住，超时避免 WebUI 任务无反馈。

## §7 素材搜索：3 个无版权视频源 + API key 轮询

| 源 | API 免费额度 | 特点 | 适合 |
|------|------------|------|------|
| **Pexels** | 免费无限制 | 大量竖屏素材，搜索结果丰富 | 默认首选 |
| **Pixabay** | 免费无限制 | 混合横屏/竖屏，覆盖面广 | 备选 |
| **Coverr** | Demo 50 次/小时 | HD/4K 横屏为主，电影级 | 横屏/电影风格（v1.3.0 新增） |

API key 轮询是线程安全的：

```python
_api_key_counter = 0
_api_key_lock = threading.Lock()

def get_api_key(cfg_key: str):
    api_keys = config.app.get(cfg_key)
    if isinstance(api_keys, str):
        return api_keys
    global _api_key_counter
    with _api_key_lock:
        _api_key_counter += 1
        return api_keys[_api_key_counter % len(api_keys)]
```

配置多个 key 可以避免单 key 触发 rate limit。批量生成视频时，多个搜索请求分散到不同 key 上。

素材搜索和下载默认开启 TLS 证书校验（`tls_verify=True`），防止 API key 被中间人攻击窃取。只有企业代理或自签证书环境才需要临时关闭。

## §8 视频合成链路：MoviePy 2.x + FFmpeg + Pillow

### 8.1 MoviePy 2.x 迁移

v1.2.8 之后从 MoviePy 1.x 升级到 2.x。最大的变化是字幕渲染不再依赖 ImageMagick，改用 Pillow。这减少了部署的外部依赖——ImageMagick 在 Windows 上的安装和配置一直是用户痛点。

### 8.2 时长安全余量

```python
_VIDEO_DURATION_SAFETY_MARGIN = 0.1  # 秒

def _get_required_video_duration(audio_duration: float) -> float:
    return max(0.0, float(audio_duration) + _VIDEO_DURATION_SAFETY_MARGIN)
```

FFmpeg 按帧率拼接/转码时，最终时长可能比 MoviePy 读到的理论时长短几十毫秒。0.1 秒余量避免音频末尾出现黑屏或最后一段旁白没有画面。

### 8.3 编码器选择

| 编码器 | 平台 | 硬件 |
|--------|------|------|
| `libx264` | 全平台 | CPU 软编（默认 fallback） |
| `h264_nvenc` | Linux/Windows | NVIDIA GPU |
| `h264_amf` | Windows | AMD GPU |
| `h264_qsv` | Linux/Windows | Intel QSV |
| `h264_mf` | Windows | Media Foundation |
| `h264_videotoolbox` | macOS | VideoToolbox |

运行时自动检测可用编码器，失败时 fallback 到 `libx264`。音频固定 AAC 192k——Docker 环境下默认配置容易出现质量波动，显式抬高码率避免失真。

## §9 部署方式：4 条路径

### 9.1 Windows 一键启动包

下载 Release 包 → 双击 `update.bat` → 双击 `start.bat`。`webui.bat` 会优先使用项目 `.venv` 或一键包内置 Python；如果没找到但已安装 `uv`，会自动切换为 `uv run streamlit`。

### 9.2 Docker

```shell
docker compose -f docker-compose.release.yml up
```

拉取预构建镜像 `ghcr.io/harry0703/moneyprinterturbo:latest`。GPU 加速用 `docker-compose.gpu.yml`。

### 9.3 uv + venv

```shell
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo
uv python install 3.11
uv sync --frozen
```

推荐给 macOS / Linux 用户。`uv` 比 `pip` 快 10-100 倍，`uv.lock` 确保依赖版本一致。

### 9.4 Google Colab + CLI

Colab 链接在 README 里，点开即用。CLI 适合无浏览器的场景：

```shell
uv run python cli.py --video-subject "金钱的作用"
uv run python cli.py --video-subject "金钱的作用" --video-source local \
  --video-materials "1.mp4,2.mp4" --stop-at video
```

## §10 配置体系与任务管理

所有配置集中在 `config.toml`。WebUI 也支持运行时修改。任务管理支持两种模式：

```python
if _enable_redis:
    task_manager = RedisTaskManager(
        max_concurrent_tasks=5, redis_url=redis_url, max_queued_tasks=100)
else:
    task_manager = InMemoryTaskManager(
        max_concurrent_tasks=5, max_queued_tasks=100)
```

内存模式适合单机开发，Redis 模式支持多实例部署和任务持久化。

## §11 一个完整任务流案例：从"金钱的作用"到 final-1.mp4

**输入**：主题 `"金钱的作用"`，声音 `zh-CN-XiaoyiNeural-Female`，竖屏 9:16，Pexels 素材源，`video_count=1`。

1. **文案生成**（→ 10%）：LLM 收到主题 + 7 条约束的 system prompt，返回纯文本"金钱，作为交换媒介和价值尺度..."。`_normalize_text_response()` 清理 `<think>` 标签和换行符。

2. **关键词生成**（→ 20%）：LLM 收到主题 + 文案，返回 `["money", "currency", "shopping", "business", "investment"]`。

3. **语音合成**（→ 30%）：Edge TTS 用 `zh-CN-XiaoyiNeural-Female` 把文案转成 `audio.mp3`（约 62 秒），返回词级时间戳 `sub_maker`。

4. **字幕生成**（→ 40%）：用 `sub_maker` 时间戳生成 `subtitle.srt`。edge 模式失败则 fallback 到 whisper。

5. **素材获取**（→ 50%）：5 个关键词搜 Pexels，每个下载 3-5 个片段，总时长约 65 秒覆盖音频。

6. **视频拼接**（→ 75%）：random 模式打乱素材，每片段裁剪到 5 秒，拼接后裁剪到 62.1 秒（音频 + 0.1 秒安全余量）。

7. **最终合成**（→ 100%）：画面 + 配音 + 背景音乐（20% 音量）+ 字幕（STHeetiMedium 60px 白字黑描边）。编码 H.264 + AAC 192k，30fps，1080×1920。输出 `final-1.mp4`。

总耗时（CPU）：约 2-4 分钟，瓶颈在素材下载和 FFmpeg 编码。

## §12 适用场景与边界

### 12.1 适合的场景

- **自媒体短视频批量生产**：每天需要产出多条 YouTube Shorts / TikTok / 抖音内容
- **教育/知识类内容**：文案为主、画面为辅——画面只需相关素材拼接
- **营销/推广内容**：产品介绍、品牌宣传，需要批量变体做 A/B 测试
- **多语言内容**：同一主题生成中英文版本——Edge TTS 300+ 声音覆盖几十种语言
- **作为开发框架二次开发**：MIT 协议 + FastAPI 后端 + 模块化设计

### 12.2 不适合的场景

- **需要 AI 生成画面**：MoneyPrinterTurbo 做素材拼接，不是 Sora / Runway 那种从文本生成画面
- **需要精确的视频编辑**：没有时间轴编辑、关键帧动画、特效合成
- **需要专业级配音**：Edge TTS 质量中等，专业级配音仍需人工录制
- **素材版权要求严格**：Pexels / Pixabay / Coverr 素材虽标无版权，商业场景仍需逐一核实
- **实时生成**：单视频耗时 2-4 分钟，不适合"10 秒出结果"的实时场景

### 12.3 选型决策

| 需求 | 首选 | 次选 |
|------|------|------|
| 批量生产知识类短视频 | MoneyPrinterTurbo | 半自动脚本 + 手剪 |
| AI 生成视频画面 | Sora / Runway / Pika | 不适用 |
| 专业视频编辑 | DaVinci Resolve / Premiere | Final Cut Pro |
| 免费 TTS 演示 | MoneyPrinterTurbo（Edge TTS） | edge-tts CLI |
| 多语言内容批量生产 | MoneyPrinterTurbo | 自建 LLM + TTS pipeline |
| 需要实时或低延迟 | 不适用 | 预生成 + 缓存 |

## §13 安全设计

### 13.1 文件路径安全

`app/utils/file_security.py` 的 `resolve_path_within_directory()` 确保用户提供的文件路径不会逃出预期目录。两级约束：先约束在 task 目录内，再约束在项目根目录内。

### 13.2 上传文件名清理

```python
def _sanitize_upload_filename(filename: str, request_id: str) -> str:
    normalized_name = (filename or "").replace("\\", "/").split("/")[-1].strip()
    if not normalized_name or normalized_name in {".", ".."}:
        raise HttpException(...)
    return normalized_name
```

只保留纯文件名，阻止 `../` 路径穿越攻击。

### 13.3 错误信息脱敏 + gpt4free 默认禁用

前文 §5.4 提到的 `_sanitize_error_message()` 防止密钥通过错误信息泄露。gpt4free 通过逆向工程调用 ChatGPT，默认禁用（`enable_g4f=true` 才能启用），error message 明确标注供应链和服务条款风险。

## §14 跨平台发布：从生成到分发

v1.3.0 通过 [Upload-Post](https://upload-post.com) 第三方服务实现跨平台发布：

```toml
upload_post_enabled = true
upload_post_api_key = "your-key"
upload_post_platforms = ["tiktok", "instagram", "youtube"]
upload_post_auto_upload = true
upload_post_youtube_privacy_status = "public"
```

发布前 LLM 生成社交媒体元数据（标题、描述、标签）。YouTube 发布自动标注 `containsSyntheticMedia=True`——这是 YouTube 对 AI 生成内容的合规要求。

取舍：用第三方服务而不是自己实现各平台 API，好处是维护成本低——TikTok / Instagram / YouTube 的发布 API 各自变化频繁，交给 Upload-Post 适配比自己维护 3 套 SDK 划算。坏处是多一层第三方依赖和费用。

## §15 谁该用 MoneyPrinterTurbo，谁不该

**该现在就用的**：
- 自媒体创作者，每天需要批量产出短视频，手剪效率太低
- 教育/知识类内容生产者，文案为主画面为辅
- 需要多语言版本内容，想用免费 TTS 快速出稿
- 开发者想在此基础上做定制化视频生成服务

**可以等等的**：
- 需要 AI 生成画面（等 Sora / Runway 开源或降价）
- 需要专业级视频编辑（用 DaVinci Resolve / Premiere）
- 需要实时生成（等硬件和模型推理速度跟上来）

**如果想把 MoneyPrinterTurbo 的设计思路用到自己的项目**：

1. 先看 §4 的 7 步任务流——理解每一步的输入输出和失败处理
2. 再看 §5 的 provider 分类——理解"OpenAI 兼容 = 换 base_url + api_key"这个核心模式
3. 最后看 §8 的视频合成链路——理解 MoviePy + FFmpeg + Pillow 的分工

---

**参考来源**：

- [GitHub 仓库](https://github.com/harry0703/MoneyPrinterTurbo) —— harry0703/MoneyPrinterTurbo（v1.3.0，MIT License）
- [README.md](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/README.md) —— 功能特性、安装部署、配置说明
- [`app/services/task.py`](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/app/services/task.py) —— 7 步任务编排器（480 行）
- [`app/services/llm.py`](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/app/services/llm.py) —— LLM provider 路由（1132 行）
- [`app/models/schema.py`](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/app/models/schema.py) —— Pydantic 数据模型
- [`config.example.toml`](https://github.com/harry0703/MoneyPrinterTurbo/blob/main/config.example.toml) —— 完整配置项说明
- [v1.3.0 Release Notes](https://github.com/harry0703/MoneyPrinterTurbo/releases/tag/v1.3.0) —— Coverr 素材源、Groq LLM provider、ElevenLabs TTS、no-voice 模式
