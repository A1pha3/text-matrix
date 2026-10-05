---
title: "MoneyPrinterTurbo 上手：把一个主题变成一条可发布的短视频"
date: "2026-03-28T16:40:00+08:00"
lastmod: "2026-10-02T00:00:00+08:00"
slug: "moneyprinterturbo-ai-video-generator"
github_repo: "harry0703/MoneyPrinterTurbo"
source_key: "gh:harry0703/MoneyPrinterTurbo"
description: "MoneyPrinterTurbo 上手指南：四种使用方式怎么选、三条安装路径各自的前置条件与验证方法、config.toml 必填项、API 异步任务的正确调用姿势，以及 FFmpeg、Whisper 模型等常见故障的排查。数据核对自 2026-10-02 的 GitHub API 与 main 分支。"
draft: false
categories: ["技术笔记"]
tags: ["AI视频生成", "Python"]
---

[harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) 做的事情一句话能说完：给它一个主题或一段现成文案，它把脚本生成、配音、素材匹配、字幕、配乐、合成整条链跑完，交给你一条 9:16、16:9 或 1:1 的高清短视频。它自己不训练任何视频模型，而是把成熟的云服务（大语言模型、语音合成（TTS）、素材库、可选的文生视频 API）和本地的 MoviePy/FFmpeg 串成一条流水线——理解这一点，后面所有配置项的用途都由此展开。

本文是上手指南，回答四个问题：选哪个入口、怎么装、填什么配置、怎么跑通第一条视频，外加出错了去哪查。想看流水线内部结构（五个 stage 的边界、可插拔点），可以读本站另一篇[架构拆解](/posts/tech/harry0703-moneyprinterturbo-short-video-automation-guide-2026/)。文中仓库数据在 2026-10-02 通过 GitHub API 核对：127,933 stars / 20,016 forks，MIT 协议，最新 release v1.3.7（2026-09-13），`main` 分支最近推送 2026-10-01。本文的命令与配置对照的正是这一天前后的 `main` 分支。

## 一、四种使用方式，先选一条

同一套生成能力暴露成四个入口，选哪个取决于你怎么用它：

| 方式 | 适合谁 | 需要装什么 |
|------|--------|-----------|
| AI Agent | 不想碰安装配置，手头有支持 Skill 的编码智能体 | 无，把 Skill 文档链接发给 Agent |
| WebUI | 大多数个人用户，边调参数边看效果 | 一键启动包，或 Docker，或 uv 本地部署 |
| API | 要把生成能力接进自己的服务或自动化流程 | 同上，另起 8080 端口的 FastAPI 服务 |
| CLI | 无浏览器环境（服务器、端口转发），或要批量跑任务 | 同上 |

WebUI、API、CLI 三端共享同一份配置和同一条流水线，在 WebUI 里验证过的参数可以直接搬进 API 请求或 CLI 参数。自动沿用只有一处：命令行下，配音与字幕样式按「显式参数 > `config.toml` 中 `[ui]` 保存的 WebUI 设置 > 内置默认值」的顺序取值，其余生成设置（背景音乐、视频数量、段落数量）不会自动沿用 WebUI 的保存值。

AI Agent 方式是四条路里唯一免安装的：如果你的智能体支持读取 Skill 文档并操作本地终端，把 README 里那段 Skill 链接和主题一起发过去，Agent 会自己完成安装、配置和生成，只在缺 API Key 时来问你。目前支持 macOS 和 Windows。

只想先试试效果、什么都不想装：录咖（reccloud.cn）基于本项目提供了免费的在线 AI 视频生成器，或者直接开 [Google Colab](https://colab.research.google.com/github/harry0703/MoneyPrinterTurbo/blob/main/docs/MoneyPrinterTurbo.ipynb) 在云端跑。

## 二、安装：三条路径

无论哪条路径，先记住两条共同的前置条件：

- Python 3.11 或更高版本（本地部署需要；Docker 和一键包不用管）
- Windows 用户的项目路径不要包含中文、特殊字符或空格

硬件不是门槛。GPU 非必需——主要依赖云端大模型、云端 TTS 和在线素材时，CPU 和内存比显卡更重要；只有当你启用本地 Whisper 转写或批量生成时，独立显卡（4 GB 显存起步）才明显提速。CPU 4 核、内存 4 GB 是底线，8 核 16 GB 属于舒适区。

### 路径 A：Windows 一键启动包

适合 Windows 上想最快跑起来的用户。

1. 到 [Releases 页面](https://github.com/harry0703/MoneyPrinterTurbo/releases/latest)下载 **Assets** 区域的 `.7z` 压缩包。注意别下成 `Source code (zip)`——那只是源码，解压后只有 `webui.bat`，没有 `start.bat` 和 `update.bat`。
2. 解压到纯英文路径。
3. 双击 `update.bat` 更新到最新代码，再双击 `start.bat` 启动。

验证：浏览器自动打开 WebUI。如果页面空白，换 Chrome 或 Edge。

### 路径 B：Docker

适合想把运行环境隔离开的用户，推荐直接拉预构建镜像：

```shell
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo
docker compose -f docker-compose.release.yml up
```

`docker-compose.release.yml` 拉取的是 GitHub Container Registry 上的预构建镜像 `ghcr.io/harry0703/moneyprinterturbo:latest`，省去本地构建。想自己构建镜像再用普通的 `docker compose up`。

Docker 部署有一个与本地部署不同的细节：首次启动前要手动执行 `cp config.example.toml config.toml`，供容器挂载；本地部署则会自动创建这个文件（见下一节）。

验证：浏览器打开 http://127.0.0.1:8501 是 WebUI，http://127.0.0.1:8080/docs 是 API 文档。

### 路径 C：uv 本地部署（macOS / Linux / Windows）

官方现在推荐 [uv](https://docs.astral.sh/uv/) 管理环境：

```shell
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo
uv python install 3.11
uv sync --frozen
```

依赖定义在 `pyproject.toml`，`uv.lock` 锁定版本，`requirements.txt` 只保留给旧的 pip 方式。不想用 uv 的话，`python3.11 -m venv .venv` 加 `pip install -r requirements.txt` 也仍然可行。

启动两个服务（在项目根目录）：

```shell
sh webui.sh          # Windows 用 .\webui.bat，会自动找项目 .venv 或一键包内置 Python
uv run python main.py   # API 服务；已手动激活虚拟环境则直接 python main.py
```

验证：WebUI 出现在 http://127.0.0.1:8501。想让局域网内其他设备访问，启动前设 `MPT_WEBUI_HOST=0.0.0.0`（Windows CMD 用 `set`）。

## 三、配置：填哪些 Key

本地部署不需要手动建配置文件——首次启动时程序会照着 `config.example.toml` 自动生成 `config.toml`，Key 也可以直接在 WebUI 的基础设置面板里填，不必手改文件。Docker 部署按上一节手动复制后编辑 `config.toml`。

最少要填两类凭据，缺一不可：

**脚本生成用的大模型 Key。** 当前默认提供商是 `moonshot`，但完整列表长得多为：Kimi/Moonshot、OpenAI、Anthropic Claude、Google Gemini、DeepSeek、阿里云通义千问、Azure OpenAI、火山引擎方舟、xAI Grok、MiniMax、小米 MiMo，外加 Ollama（本地运行）、ModelScope、OpenRouter、Groq、OneAPI、LiteLLM、Pollinations 等一批网关与聚合平台。换提供商就是改 `[app]` 段的 `llm_provider` 并填对应 Key，例如：

```toml
llm_provider = "deepseek"
deepseek_api_key = "sk-xxxx"
```

**素材库的 Pexels Key。** 默认素材源是 Pexels，在 [pexels.com/api](https://www.pexels.com/api/) 免费申请，填进 `pexels_api_keys`（列表格式，支持多个 Key 轮换）：

```toml
pexels_api_keys = ["your_pexels_api_key"]
```

素材源不止 Pexels 一个。`video_source` 可以在 `pexels`、`pixabay`、`coverr`（三家都是免费库存素材）、`local`（上传本地图片视频）之间切换，也可以接到 WaveSpeed、火山引擎 Seedance、OFox、秘塔 MiniMax H3、MuAPI 这些文生视频服务上——后者按次计费，生成的是原创画面而不是库存片段，适合素材库搜不到的画面。

其余常见项的位置，留作速查：

| 想改什么 | 在哪里 |
|----------|--------|
| 手动指定 FFmpeg 路径 | `[app]` 段 `ffmpeg_path`（通常自动下载，无需设置） |
| 字幕方式切换 | `[app]` 段 `subtitle_provider`，`"edge"`（默认）或 `"whisper"` |
| Whisper 模型大小 | `[whisper]` 段 `model_size`，默认 `large-v3`，可选更小的 `large-v3-turbo` |
| API 服务的 API 鉴权 | `[app]` 段 `api_key`，配置后客户端需带 `x-api-key` 请求头 |
| 跨来源网页调用 API | 环境变量 `CORS_ALLOWED_ORIGINS`（默认仅允许同源） |

## 四、生成第一条视频

### WebUI

打开 http://127.0.0.1:8501，输入视频主题，选好画幅和配音，点生成。生成设置支持导入导出，可以备份或在多台机器间迁移；任务历史里能回看之前的成品。一条任务默认出 1 条视频，`video_count` 最多可一次生成 5 条供挑选。

### CLI

最短的完整命令：

```shell
uv run python cli.py --video-subject "人工智能如何改变日常生活"
```

批量任务用 `--batch-file` 传一个 UTF-8 JSON 数组或 JSONL 清单，CLI 参数作为全局默认值，清单里每个对象可覆盖单个任务的参数。清单上限 100 个任务、1 MiB，所有条目会在第一个任务启动前完成预检，单个失败不阻断后续，最后输出统一的 JSON 汇总：

```shell
uv run python cli.py --batch-file ./tasks.json --stop-at video
```

完整参数看 `uv run python cli.py --help`。

### API

有一个容易踩的坑：**视频生成是异步任务**。`POST /api/v1/videos` 立刻返回的是 `task_id`，不是视频路径；要拿成片，得拿这个 ID 去轮询任务状态。

```python
import time
import requests

base = "http://127.0.0.1:8080"

# 1. 创建任务，立即返回 task_id
resp = requests.post(
    f"{base}/api/v1/videos",
    json={
        "video_subject": "如何增加生活的乐趣",
        "video_aspect": "9:16",        # 可选 "9:16" / "16:9" / "1:1"，默认竖屏
        "voice_name": "zh-CN-XiaoxiaoNeural-Female",
    },
).json()
task_id = resp["data"]["task_id"]

# 2. 轮询任务状态：1 = 完成，4 = 处理中（progress 0~100），-1 = 失败
while True:
    task = requests.get(f"{base}/api/v1/tasks/{task_id}").json()["data"]
    print(task["state"], task.get("progress"))
    if task["state"] == 1:
        break
    if task["state"] == -1:
        raise RuntimeError("任务失败，详情见服务端日志")
    time.sleep(5)

# 3. 任务成功后，videos 字段就是成片的下载地址
for url in task.get("videos", []):
    print(f"成片地址: {url if url.startswith('http') else base + url}")
```

成片与中间产物（配音、字幕）的地址就挂在任务查询响应的 `videos`、`audio_file`、`subtitle_path` 字段上，文件本体在服务端 `tasks/{task_id}` 目录下；`GET /api/v1/tasks` 可以分页列出全部任务。若启用了 `[app]` 段的 `api_key` 鉴权，以上每个请求都要加 `x-api-key` 请求头。

API 还有两个单项端点：`POST /api/v1/subtitle` 只生成字幕，`POST /api/v1/audio` 只生成配音，适合只想复用某一环的场景。

## 五、配音、字幕、配乐的选项

**配音**有三种形态：自动配音、上传自己的音频、无配音。TTS 服务商给了 11 个：WebUI 里的 Azure TTS V1 底层是 Edge TTS，免费、无需 API Key，是默认选项；其余——Azure TTS V2、SiliconFlow、Google Gemini、小米 MiMo、MiniMax、ElevenLabs、自托管的 Chatterbox 和 Kokoro、Fish Audio、ModelBest VoxCPM——都需要对应平台的凭据。WebUI 里可以逐个试听音色再选。Edge TTS 的完整音色列表在仓库 `docs/voice-list.txt`。

**字幕**有两种生成方式，切换在 `subtitle_provider`：

- `edge`（默认）：直接用 TTS 返回的时间戳，快，不需要 GPU；
- `whisper`：本地 `faster-whisper` 转写配音音频，时间轴更准，首次使用要下载模型——默认 `large-v3` 约 3 GB，对速度敏感可以改用约 1.6 GB 的 `large-v3-turbo`。

字幕样式（字体、位置、颜色、大小、描边、背景）都在 WebUI 里调；自定义字体放进 `resource/fonts` 即可被选用。

**配乐**三选一：随机用项目自带的（`resource/songs` 目录，来自 YouTube，版权敏感环境建议清空后放自己的）、指定本地音乐文件、或让 AI 生成。背景音乐音量独立可调。

## 六、常见问题

**`RuntimeError: No ffmpeg exe could be found`**
FFmpeg 通常会被自动下载并检测到，报这个错说明自动下载在你的环境里失败了。从 [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 手动下载，解压后在 `config.toml` 里设置：

```toml
[app]
ffmpeg_path = "C:\\Users\\your_name\\Downloads\\ffmpeg.exe"
```

**`OSError: [Errno 24] Too many open files`**
系统打开文件数限制太低。`ulimit -n` 查看当前值，过低就调高，比如 `ulimit -n 10240`。

**Whisper 模型下载失败**
首次使用 Whisper 时程序会从 Hugging Face 自动下载模型，网络不通时会报 `LocalEntryNotFoundError` 一类的错。解法是手动下载：从 [Systran/faster-whisper-large-v3](https://huggingface.co/Systran/faster-whisper-large-v3) 下载后解压，整个目录放到 `.\MoneyPrinterTurbo\models\` 下，最终路径形如 `models\whisper-large-v3\`（内含 `config.json`、`model.bin` 等文件）；如果配置了 `large-v3-turbo`，目录名对应改为 `whisper-large-v3-turbo`。

**网页调用 API 被跨域拦截**
API 默认只允许同源网页访问，这是安全默认而非故障。只有独立网页前端需要从其他来源直接调 API 时，才设置环境变量 `CORS_ALLOWED_ORIGINS`（如 `http://localhost:3000`）；curl、Postman、n8n 这类服务端调用不受影响。

**早先教程里的 ImageMagick 步骤**
旧版合成基于 MoviePy 1.x，字幕渲染依赖 ImageMagick，老教程会让人先装 ImageMagick、再改它的 `policy.xml` 安全策略。当前版本基于 MoviePy 2.x，不再需要 ImageMagick，这两步整体跳过——照旧教程装不上的，先检查版本差异。

## 七、适用与不适用

它擅长的：批量生产「文案 + 库存素材 + 配音 + 字幕」结构的短视频——自媒体日更、知识科普、商品介绍这类对产能敏感、对画面独特性要求不高的内容。全流程可以零人工介入，提交主题后到出片之间只有等待；想逐环节把关时，每个环节也都留了替换入口（自带脚本、上传配音、本地素材）。

它的边界同样清楚：素材以库存片段匹配为主（配了文生视频服务才能产原创画面），做不出需要逐帧设计的专业动效；没有直播能力；定位就是分钟级短视频，不是长视频工具。内容同质化是流水线工具的天然属性——所有条目共享同一套风格参数，想要「每条都不一样」的品牌化内容，它只能当半成品生产线用。

## 维护指引

本文所有随时间失效的点集中在以下几处，按此复查即可：

- **仓库数据**（stars、forks、最新 release、最近推送）：`GET https://api.github.com/repos/harry0703/MoneyPrinterTurbo` 与 `/releases?per_page=1`。stars 与版本号是全文最容易过期的两处。
- **功能清单与安装命令**：对照仓库 `README.md`（简体中文版）的「功能特性」「快速开始」「安装部署」三节。
- **配置项与默认值**：对照 `config.example.toml`——`llm_provider` 默认值、`video_source` 可选值、`subtitle_provider`、`[whisper]` 段都可能随版本调整。
- **API 端点与字段**：对照 `app/router.py`（前缀 `/api/v1`）、`app/controllers/v1/video.py`（端点清单）、`app/models/schema.py`（`TaskVideoRequest` 字段与默认值）。
- **依赖版本**：对照 `pyproject.toml`。MoviePy 大版本升级（如 2.x → 3.x）通常意味着合成行为或依赖变化。
- **失效条件**：README 里移除「AI Agent 使用方式」或「一键跨平台发布」任一小节时，本文第一、四节需重写；`subtitle_provider` 的可选值变化时，第五节需重写。

## 参考来源

- 仓库：[harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)，MIT License
- README（简体中文）：功能特性、配置要求、快速开始、安装部署、配音字幕配乐、常见问题各节
- 源码（main 分支，2026-10-02 核对）：`config.example.toml`、`pyproject.toml`、`cli.py`、`app/router.py`、`app/controllers/v1/video.py`、`app/models/schema.py`
- GitHub API：仓库元数据与 release 列表，2026-10-02 读取
