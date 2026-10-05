---
title: "BiliSummary：把 B 站视频变成可检索的 Markdown 笔记"
slug: "bilibili-summary-ai-video-summarizer-guide"
github_repo: "jackwener/bilibili-summary"
source_key: "gh:jackwener/bilibili-summary"
date: "2026-04-08T13:10:00+08:00"
lastmod: 2026-09-28T08:00:00+08:00
categories: ["技术笔记"]
tags: ["Python", "B站", "FastAPI", "知识管理"]
description: "BiliSummary 是一个桌面优先的 B 站视频 AI 摘要工具：字幕优先、ASR 兜底，把视频整理成结构化 Markdown，支持 URL、UP 主、收藏夹三种输入模式。"
draft: false
---

# BiliSummary：把 B 站视频变成可检索的 Markdown 笔记

BiliSummary 把"B 站视频 → 结构化 Markdown 笔记"这条链路做成了桌面应用。它优先读视频的 CC 字幕，拿不到字幕时下载音频做语音识别（ASR，Automatic Speech Recognition），再把文本交给大模型整理成摘要，落盘为 Markdown。README 给自己的定位是：

> Desktop-first Bilibili summarizer with AI-generated Markdown output, favorites workflow, and unified browse/reading UX.

README 把 ASR 写成兜底（fallback），但兜底动作并不在批量摘要管道里：批量跑到的无字幕视频会被记入 `no_subtitle/` 待重试清单，真正的语音识别由阅读页的交互触发——打开无字幕摘要时出现的按钮，或"重新总结"字幕失败后的自动切换。兜底放在交互层而不是管道里，是这个项目最值得注意的取舍，下文按管道顺序拆开讲。

## 系统地图：一条管道，两条文本路径

三种输入（URL、UP 主、收藏夹）最终都汇成一批 BV 号，进入同一条摘要管道。管道先解决"文本从哪来"，再解决"笔记怎么生成"：

| 环节 | 职责 | 所在代码 |
|------|------|---------|
| 输入层 | URL / UP 主 / 收藏夹三种方式凑齐一批 BV 号 | `summarize.py`、`routes/` |
| 文本获取 | 先取 CC 字幕；批量管道拿不到就记入 `no_subtitle/` 计数，由阅读页触发 GLM-ASR 转写兜底 | `summarize.py` 的 `get_subtitle`、`routes/asr.py` |
| 摘要生成 | 文本交给 Anthropic 兼容接口，产出三段式笔记 | `summarize.py` 的 `summarize_with_claude` |
| 落盘与展示 | `.md` + `.meta.json` 写入 `summary/`，内嵌网页读取展示 | `routes/deps.py`、`server.py`、`static/` |

界面层做的事围绕"读摘要"展开：统一的卡片浏览（缩略图 / 紧凑两种视图切换）、带全局返回按钮的阅读页、收藏夹批量处理后短窗口内可撤销的取消收藏。它不碰笔记编辑——编辑交给 Obsidian、VS Code 这类下游工具。

## 快速信息卡

- GitHub：[jackwener/bilibili-summary](https://github.com/jackwener/bilibili-summary)
- Stars / Forks：22 / 6
- License：README 声明 MIT；仓库根目录没有 LICENSE 文件
- 主要语言：Python
- 创建 / 最近提交：2026-02-15 / 2026-02-24
- 描述：AI-powered Bilibili video summarizer with ASR support

## 技术栈

| 组件 | 选型 |
|------|------|
| 后端 | FastAPI + Uvicorn |
| 前端 | Vanilla JS + CSS（tokenized design system） |
| 桌面壳 | pywebview |
| B 站集成 | bilibili-api-python |
| AI 摘要 | Anthropic 兼容 API |
| ASR | GLM ASR |
| 音频处理 | PyAV |

选 pywebview 而不是 Electron，是为了桌面窗口和浏览器访问共用同一份 FastAPI 代码：窗口里嵌的就是本地起在 `127.0.0.1:18520` 的服务，前端没有构建步骤。

## 项目结构

```text
app.py          # 桌面入口（pywebview + 后台线程起 FastAPI）
server.py       # FastAPI 应用与路由注册
summarize.py    # 摘要管道：字幕提取、CLI、批量处理
routes/         # API 路由模块
  deps.py       # 共享状态：登录凭证、AI 客户端、SSE 进度、批处理
  asr.py        # ASR 摘要路由
  auth.py       # 登录
  favorites.py  # 收藏夹相关
  settings.py   # 设置
static/         # 前端资源（index.html / app.js / style.css）
docs/           # 设计系统与项目状态
config.toml     # 默认待处理视频列表
summary/        # 生成的摘要，按 standalone / favorites / users 分组
```

## 摘要管道

### 先试字幕：批量管道的快路径

B 站相当一部分视频带 AI 生成的 CC 字幕。字幕接口是现成的 JSON，取文本几乎零成本；音频下载加语音识别要花时间、花 API 额度。所以管道先试字幕。

字幕获取在 `get_subtitle` 里完成：取分 P 信息拿 cid（B 站对视频分 P 的内容标识）→ 用 cid 请求播放器信息、读字幕列表 → 优先选中文字幕，下载字幕 JSON，把逐条文本拼成纯文本。同一份字幕还会转存成 ASS 文件（`ass/<分组>/`），供后续编辑或查看。

批量管道拿不到字幕时不转向 ASR：摘要步骤收到空文本，生成一条占位提示，产物落进 `<分组>/no_subtitle/` 子目录，重试计数加一，记在 `no_subtitle/.retries.json`。下次批量跑到同一视频，正常产物存在就直接跳过；只有 `no_subtitle/` 里的旧产物且计数未到 3 次才再试，3 次之后放弃。

### ASR 兜底：由阅读页触发

真正调用语音识别的入口是 `POST /api/asr-summarize/{bvid}`，触发它的不是批量管道，而是前端阅读页：

- 打开一篇 `no_subtitle` 摘要，阅读页会多出一个"语音识别总结"按钮，点下即发起；此时点"重新总结"也一样，直接转 ASR；
- 对正常摘要点"重新总结"，先走字幕管道，返回仍是 no_subtitle 时，前端自动切换到语音识别。

`routes/asr.py` 拿到请求后的链路：

1. 取音频流。刻意选最低码率（64K，禁杜比、禁 Hi-Res），控制下载体积；DASH 格式取音频轨，FLV/MP4 取合并流。
2. 用 PyAV 解码，重采样成 16 kHz 单声道，按 29 秒切成 wav 段。GLM-ASR 单文件限 30 秒，切短一档留余量。
3. 每段 5 路并发调 GLM-ASR（模型 `glm-asr-2512`），429 或 5xx 指数退避重试 3 次。
4. 转写文本拼接后交给摘要步骤；成功后删掉 `no_subtitle/` 里的旧产物，把新摘要存进正常目录。

ASR 路径要求登录（`/api/asr-summarize` 未登录直接返回 401），因为拉取音频流通常要带凭证。

### 摘要生成

`summarize_with_claude` 把文本和标题一起发给 Anthropic 兼容接口，发送前文本截断到前 3 万字符（`subtitle[:30000]`），超长视频后面的内容不会进入摘要。提示词要求输出三段式笔记：**内容整理**（去口语化、按话题分段）、**核心观点**（先一句话概括，再列支撑的例子、数据或类比）、**行动建议**（有方法论才写）。默认模型 `GLM-4-FlashX-250414`，`max_tokens` 8192；命中限流（429）按指数退避重试，最多 5 次，其他 API 错误直接失败、不重试。

### 落盘

每个视频产出两个文件到 `summary/<分组>/`：

- `<标题>.md`：Markdown 摘要，头部带 BV 号、视频链接、作者、时长、生成时间；
- `<标题>.meta.json`：标题、BV 号、链接、时长、作者、封面等元数据，前端卡片用它渲染缩略图。

## 一条无字幕视频的完整流转

把上面的机制串起来。假设收藏夹批量任务里有一条没有 CC 字幕的 40 分钟视频：

1. 服务端并发处理这批视频（默认 12 路），轮到它时正常摘要不存在，进入"获取字幕"步骤；
2. 播放器信息里字幕列表为空，`get_subtitle` 返回空文本，摘要步骤生成占位提示，产物落进 `favorites/no_subtitle/`，计数记为 1；
3. SSE 进度流把这条标记为 `no_subtitle`，任务结束的汇总里计入"无字幕"一栏；
4. 你点开这篇占位摘要，阅读页给出"语音识别总结"按钮，点下后前端发起 ASR：下载 64K 音频流 → PyAV 切成 80 多段 29 秒的 wav → 5 路并发转写 → 拼接出转写文本；
5. 文本截到 3 万字符后交给 `GLM-4-FlashX-250414` 生成三段式笔记，`no_subtitle/` 旧文件删除，正式摘要落进 `favorites/`，阅读页就地刷新。

这个案例也回答了一个容易误判的问题：批量汇总里的"无字幕"计数不代表失败——它只是把转写动作推迟到你真正打开这篇摘要的时候。

## 三种输入模式

| 模式 | 输入 | 登录要求 | 适用场景 |
|------|------|---------|---------|
| URL | 单个视频链接 | 否 | 临时摘要某个视频 |
| UP 主 | UP 主名称或 UID | 否 | 跟踪连载；给名称时自动搜索 UID |
| 收藏夹 | 默认收藏夹 | 必须 | 批量沉淀自己收藏的视频 |

名称转 UID 走搜索接口，拿不到会明确报"未找到 UP 主"。命令行和 `/api/summarize/favorites` 固定拉默认收藏夹；网页端浏览页会列出全部收藏夹，可以任选一个挑视频批量摘要（走 `/api/favorites/*` 路由）。

## 安装与启动

源码用了 `list[str]`、`Path | None` 这类新式类型标注，需要 Python 3.10+。安装：

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

在项目根目录建 `.env.local`：

```bash
ANTHROPIC_AUTH_TOKEN=your_api_key
ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic
```

AI 客户端按 `base_url` + `api_key` 初始化，只要是 Anthropic 兼容网关都能接；示例指向智谱开放平台的 Anthropic 端点。

可选环境变量：

| 变量 | 作用 |
|------|------|
| `DEFAULT_MODEL` | 覆盖默认模型 `GLM-4-FlashX-250414` |
| `BILIBILI_SESSION_TOKEN` / `BILIBILI_BILI_JCT` / `BILIBILI_AC_TIME_VALUE` | B 站登录凭证（cookie 三件套） |
| `BILISUMMARY_DATA_DIR` | 数据目录（默认项目根目录；打包后为 `~/Library/Application Support/BiliSummary`） |

启动：

```bash
python app.py      # 桌面窗口，内嵌 FastAPI（127.0.0.1:18520）
python server.py   # 只跑服务，浏览器访问 http://127.0.0.1:18520
```

## 配置：config.toml

`config.toml` 只做一件事：放默认待处理的视频 URL。命令行不带参数运行时处理的就是这份列表。

```toml
summary-videos = [
  "https://www.bilibili.com/video/BV1xxxxxxxxx",
]
```

## 命令行用法

`summarize.py` 可以直接当脚本跑（脚本头 `#!/usr/bin/env python3`）：

```bash
python summarize.py                        # 处理 config.toml 里的视频
python summarize.py --user UID --count N   # 处理某 UP 主最新 N 个视频
python summarize.py --login                # 扫码登录，自动保存凭证
python summarize.py --favorite             # 处理收藏夹里的视频
```

另有几个调控行为的参数：`--count` 缺省时 UP 主取 50 个、收藏夹取 20 个；`--concurrency` 控制批量并发（默认 12）；`--model` 指定模型；`--benchmark` 对比 `GLM-4.7-Flash` 与 `GLM-4-FlashX-250414` 的生成耗时，此时忽略 `--model`。

## 网页端 API

桌面和浏览器访问的是同一个 FastAPI 服务。`server.py` 注册的路由：

| 方法与路径 | 作用 |
|-----------|------|
| `GET /` | 返回前端页面 |
| `GET /api/status` | 是否已登录、AI 是否已配置 |
| `GET /api/summaries` | 按分类列出全部摘要（独立视频 / 收藏 / UP 主） |
| `GET /api/summary/{path}` | 读取某篇摘要的 Markdown |
| `POST /api/summarize/url` | 批量摘要一批 URL（最多 200 个） |
| `POST /api/summarize/user` | 按 UP 主名或 UID 摘要，默认最近 50 个 |
| `POST /api/summarize/favorites` | 收藏夹批量（需登录），默认 20 个 |
| `POST /api/retry/{bvid}` | 重新总结：先试字幕，仍无字幕时前端自动转 ASR |
| `GET /api/progress/{task_id}` | SSE 实时进度流 |
| `POST /api/asr-summarize/{bvid}` | 对无字幕视频走 ASR 摘要（需登录） |

批量任务异步执行，通过 SSE（Server-Sent Events，服务器单向推送）推进度：启动、逐条 skip / processing / completed、结束时带汇总（成功 / 跳过 / 无字幕 / 失败计数）。进度按事件历史保存，前端断了可以带 `Last-Event-ID` 续传，连接空闲时服务端每 15 秒发一次心跳。并发默认 12，请求体里用 `concurrency` 调到 1-20。

登录、设置、收藏夹浏览的路由分别在 `routes/auth.py`、`routes/settings.py`、`routes/favorites.py`，数量不少但模式一致，此处不展开。

## 开发要点

- 新增路由按 FastAPI `APIRouter` 写在 `routes/` 下，在 `server.py` 里 `include_router` 注册。
- 换 AI 模型不用改代码：设 `DEFAULT_MODEL` 即可；换网关改 `.env.local` 的 `ANTHROPIC_BASE_URL`。
- 无字幕重试、SSE 进度、批量调度都集中在 `routes/deps.py`，是理解全项目最快的入口。
- 打包用 `BiliSummary.spec`（PyInstaller）+ `build_mac.sh`；`benchmark_all.py`、`benchmark_rate_limits.py` 用来对比模型、摸清接口限流。

## 常见问题

**收藏夹 / ASR 提示未登录？** 这两条路径都要 B 站凭证。命令行先跑 `python summarize.py --login` 扫码；网页端走登录接口。凭证存进 `.env.local`（`BILIBILI_*`），过期了重新登录。

**无字幕视频最后能拿到真摘要吗？** 分两层。批量管道只做记录：产物落 `no_subtitle/`，计数至多 3 次。要拿到转写摘要，在阅读页打开它，点"语音识别总结"按钮发起 ASR（需登录），成功后产物从 `no_subtitle/` 移到正常目录，之后批量任务直接跳过。

**摘要接口被限流？** 429 会自动指数退避重试 5 次；批量场景把并发从 12 调低。

**端口冲突？** 服务固定监听 `127.0.0.1:18520`，被占用时需要改 `app.py` / `server.py` 里的 `uvicorn.run` 端口。

**想换模型？** 设 `DEFAULT_MODEL`，例如：

```bash
DEFAULT_MODEL=GLM-4-Flash python app.py
```

## 适用边界

适合：个人把关注的 UP 主、收藏夹沉淀成可检索的本地文本，之后用 Obsidian、VS Code 继续整理。批量处理（已有摘要直接跳过）是它的主场。

不适合：

- 只支持 B 站（`bilibili-api-python`），其他平台不行；
- 本地单机应用，没有账号体系，不适合团队协作；
- 摘要走"下载字幕 / 音频 + 调用模型"的链路，秒级延迟，不适合实时场景；
- 长视频的转写文本截断到 3 万字符，播客类超长内容会丢后半段。

项目规模还小（22 stars），功能迭代频繁，行为和配置都可能变化，动手前以仓库最新 README 为准。

## 自测题

1. `config.toml` 里只能配什么？
2. 批量管道遇到无字幕视频会做什么？ASR 转写由谁在什么时机触发？
3. 收藏夹批量摘要默认取多少个视频？并发默认多少、能怎么调？
4. 服务监听哪个端口？桌面和纯服务模式怎么切换？
5. `DEFAULT_MODEL` 和 `ANTHROPIC_BASE_URL` 分别解决什么问题？
6. 发给摘要模型的文本有什么长度限制？对哪类视频影响最大？

## 资料口径

- 事实来源：GitHub 仓库的 README、源码（`summarize.py`、`server.py`、`app.py`、`routes/*`、`static/app.js`、`config.toml`）与仓库元数据。仓库最近一次提交为 2026-02-24；Stars / Forks 为 2026-09-28 查询值。
- 文中的命令、环境变量、API 路径均来自源码核对，未核验的细节没有写入。
- License 一行按 README 声明记录；GitHub API 未识别出 LICENSE 文件，集成前请自行确认许可条款。
- README 里指向 `docs/design-system.md`、`docs/project-status.md` 的链接是本机绝对路径（`/Users/jakevin/...`），发布到 GitHub 后不可用，本文不引用。
