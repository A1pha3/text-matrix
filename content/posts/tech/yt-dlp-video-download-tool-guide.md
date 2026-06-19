---
title: "yt-dlp：命令行音视频下载工具使用与架构指南"
date: "2026-05-23T03:05:00+08:00"
slug: "yt-dlp-video-download-tool-guide"
description: "yt-dlp 是一款开源命令行音视频下载工具，支持超过一千个站点，基于 youtube-dl 活跃 fork 而来。本文从安装、基础用法、格式选择、元数据处理、Python API、插件开发到架构解析全面覆盖，并给出适用边界与排查路径。"
draft: false
categories: ["技术笔记"]
tags: ["yt-dlp", "视频下载", "ffmpeg", "Python", "开源工具"]
---

# yt-dlp：命令行音视频下载工具使用与架构指南

需要从 YouTube、Bilibili、TikTok 等站点批量下载视频、提取音频、嵌入字幕或写元数据时，命令行工具比图形界面更可控、可脚本化、可复现。yt-dlp 是这一场景下维护最活跃的开源实现，覆盖超过一千个站点，从 youtube-dl fork 而来并持续合并上游修复。

本文覆盖安装、常用用法、格式选择、元数据处理、Python API、插件开发，并拆解其内部架构，便于在下载失败、需要自定义提取器或嵌入到自动化流水线时定位问题。读完应能选择合适的安装与更新通道，用 `-f`/`-S` 精确控制下载格式，用输出模板组织文件结构，用 Python API 把下载能力嵌入到代码，并理解 Extractor/Downloader/PostProcessor 三层如何协作——从而判断某个站点失败时该改哪层。

文章按使用深度组织，建议按顺序阅读：

| 阶段 | 章节 | 目标 |
|------|------|------|
| 入门 | 安装、最小示例 | 跑通第一次下载 |
| 进阶 | 功能详解、输出模板、网络与反封锁 | 控制格式、组织文件、绕过封锁 |
| 自动化 | 批量下载、Python API | 嵌入脚本和流水线 |
| 扩展 | 插件系统、架构解析 | 自定义提取器、定位失败层 |
| 排查 | 常见问题、适用边界 | 解决失败、判断是否选型正确 |

只想快速上手的读者，看完「安装」和「最小示例」即可开始；遇到具体问题再回到对应章节。

## 项目概览

| 指标 | 值 |
|------|------|
| GitHub | [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) |
| Stars / Forks | 164,198 / 13,806（2026 年 5 月） |
| 语言 | Python（3.10+） |
| 许可证 | Unlicense（源码） |
| 最新提交 | 2026-05-22 |

yt-dlp 是一款功能丰富的命令行音视频下载器，主要能力包括：

- 支持超过一千个站点的视频提取，每个站点对应一个 Extractor 类
- 格式选择与多维度排序（`-f` 按格式 ID，`-S` 按分辨率/codec/文件大小等维度）
- 字幕下载、嵌入与格式转换
- 元数据写入与缩略图嵌入
- 插件扩展（自定义 Extractor 和 PostProcessor）
- 内置自动更新通道（stable / nightly / master）

相比原版 youtube-dl，yt-dlp 在 YouTube 反爬应对（n-sig 反混淆、Shorts、Clips）、格式排序粒度、并发分片下载和插件系统上都做了重写，是当前 youtube-dl 生态里更新频率最高的分支。

---

## 安装

### 二进制文件（推荐）

直接下载对应平台的二进制文件，无需安装 Python：

```bash
# Linux/macOS
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp

# Windows（PowerShell）
irm https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe -o yt-dlp.exe

# macOS
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_macos -o /usr/local/bin/yt-dlp
sudo chmod a+rx /usr/local/bin/yt-dlp
```

### pip 安装

```bash
python -m pip install -U yt-dlp
```

通过 pip 安装后，更新命令为：

```bash
python -m pip install -U --pre yt-dlp
```

### 依赖：ffmpeg（必须）

yt-dlp 的多数能力依赖外部工具 ffmpeg，包括：

- 合并分离的视频和音频流
- 转换容器格式
- 提取和嵌入字幕
- 缩略图转换

之所以依赖外部 ffmpeg 而非内置，是因为 ffmpeg 本身体积大（数十 MB）、维护独立、且涉及大量编解码专利问题，作为独立进程调用更利于各自升级。yt-dlp 只负责抓取和调度，编解码与容器操作全部交给 ffmpeg，两者通过子进程通信。

建议从 [yt-dlp/FFmpeg-Builds](https://github.com/yt-dlp/FFmpeg-Builds) 下载预编译版本。安装后运行 `yt-dlp --version` 确认安装成功。

> ⚠️ 注意：PyPI 上有个名为 `ffmpeg` 的 Python 包，和 ffmpeg 命令行工具不是同一个东西，别装错了。

### 更新通道

yt-dlp 提供三个发布通道：

| 通道 | 特点 | 适用场景 |
|------|------|----------|
| `stable` | 每月一次正式发布 | 一般用户 |
| `nightly` | 每日构建，推荐日常使用 | 多数用户首选 |
| `master` | 每次 push 触发构建 | 追求最新功能的开发者 |

```bash
# 更新到 nightly（推荐）
yt-dlp --update-to nightly

# 更新到 master
yt-dlp --update-to master

# 切换回 stable
yt-dlp --update-to stable
```

超过 90 天未更新的版本会提示更新警告，可用 `--no-update` 抑制。

由于视频站点经常调整反爬策略，yt-dlp 的 Extractor 需要持续跟进修复。遇到原本能下载的站点突然失败，第一步通常是更新到 nightly 再试。

---

## 最小示例

下载单个视频用一条命令：

```bash
yt-dlp "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

不指定格式时，yt-dlp 会按内置默认排序选最佳兼容格式。要显式指定质量最高的可用格式：

```bash
yt-dlp -f "bv*+ba/b" "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

`bv*` 匹配最佳视频流（含纯视频和音视频合一），`ba` 匹配最佳音频流，`/b` 是兜底选项。YouTube 等站点的高码率流通常是视频和音频分离的——这是 DASH（Dynamic Adaptive Streaming over HTTP）和 HLS 自适应流媒体的标准做法：分离后客户端可以根据带宽单独选择视频清晰度和音频码率，避免低带宽用户被迫下载高码率音频。代价是下载后需要 ffmpeg 把两条流合并成单个文件。

## 功能详解

### 格式选择

格式选择是 yt-dlp 区别于其他下载工具的关键能力。同一视频在不同站点、不同清晰度下往往有多个可用格式，`-f` 和 `-S` 提供两种正交的控制方式：`-f` 按格式 ID 或过滤表达式精确指定，`-S` 按多个维度排序后取最优。

#### 列出可用格式

```bash
yt-dlp -F "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

输出示例（截取部分）：

```text
ID  EXT   RESOLUTION │   FPS │   CODECS    │   BR    │   SIZE
────────────────────────────────────────────────────────────
sb2 mhtml   images                │         │ unknown
18  mp4    426x240    24 │ av01   72kbps │ ~1MB
22  mp4    1280x720   22 │ avc1   ~2MB
```

第一列 ID 是后续 `-f` 选择格式的依据。

#### 选择特定格式

```bash
# 按格式 ID 选择
yt-dlp -f 18 "URL"

# 组合视频+音频
yt-dlp -f "18+251" "URL"

# 选择最佳视频，不带音频
yt-dlp -f "bv" "URL"
```

#### 格式排序（Format Sorting）

yt-dlp 在 `-S` 参数上提供格式排序机制，按多个维度排序后取最优：

```bash
# 优先选择分辨率高、codec 新的格式
yt-dlp -S "res:1080,codec:avc" "URL"

# 先按文件大小排序，再选最佳画质
yt-dlp -S "filesize:desc,res:desc" "URL"

# 优先选择 av1 编码
yt-dlp -S "codec:av01" "URL"
```

排序优先级依次为：`ext` → `fps` → `resolution` → `codec` → `filesize` → `br` → `vr` → `gen` → `sr`（可叠加使用）。

`-S` 与 `-f` 的区别：`-f` 是硬过滤，不满足条件的格式直接排除；`-S` 是软排序，所有格式都参与，只是按指定维度排先后。需要严格限制清晰度时用 `-f` 加过滤表达式，需要在多个维度间权衡时用 `-S`。

#### 格式过滤器

```bash
# 只选择大于 720p 的视频
yt-dlp -f "bestvideo[height>=720]+bestaudio/best[height>=720]" "URL"

# 排除 webm 格式
yt-dlp -f "bestvideo-webm/bestaudio-webm" "URL"
```

### 字幕处理

```bash
# 下载所有字幕
yt-dlp --write-subs "URL"

# 下载指定语言字幕
yt-dlp --write-subs --sub-langs "en,zh-cn" "URL"

# 嵌入字幕到视频文件
yt-dlp --embed-subs "URL"

# 下载自动生成的字幕
yt-dlp --write-auto-subs --embed-auto-subs "URL"
```

`--write-subs` 把字幕作为独立文件保存，`--embed-subs` 通过 ffmpeg 把字幕轨道写入容器（mp4/mkv）。两者可以同时使用：既保留独立字幕文件，又嵌入到视频里。

### 元数据与缩略图

```bash
# 写入元数据 JSON
yt-dlp --write-info-json "URL"

# 嵌入缩略图
yt-dlp --embed-thumbnail "URL"

# 全部写入
yt-dlp --write-description --write-info-json --write-thumbnail --embed-thumbnail "URL"
```

`--write-info-json` 保存的视频元数据（标题、上传者、时长、格式列表等）可以后续被 `--load-info-json` 重新加载，避免重复请求站点 API。批量下载时先抓 info-json 再决定下载哪些格式，能显著降低被站点限速的风险。

### 下载时间范围与章节

```bash
# 只下载第 10 秒到第 60 秒
yt-dlp --download-sections "*10-60" "URL"

# 按章节分割视频
yt-dlp --split-chapters "URL"
```

`--download-sections` 依赖 ffmpeg 的精确裁剪，会先下载完整流再裁剪，不会减少下载量但能减少输出文件体积。`--split-chapters` 按视频自带的章节标记切成多个文件。

### 播放列表处理

```bash
# 只下载播放列表前 10 个视频
yt-dlp -I 1:10 "PLAYLIST_URL"

# 随机顺序下载
yt-dlp --playlist-random "PLAYLIST_URL"

# 排除已下载的视频（archive）
yt-dlp --download-archive archive.txt "PLAYLIST_URL"
```

`--download-archive` 把已下载视频的 ID 写入归档文件，下次运行时跳过。批量下载长播放列表时配合使用，可以断点续传。

---

## 输出模板与文件组织

下载大量视频时，文件命名和目录结构决定了后续检索的难易度。yt-dlp 的输出文件名通过 `-o` 模板完全可定制，模板字段来自 Extractor 返回的元数据。

### 基本模板

```bash
# 默认模板：标题 [ID].扩展名
# Example: "Rick Astley - Never Gonna Give You Up [dQw4w9WgXcQ].mp4"

# 自定义文件名
yt-dlp -o "%(title)s-%(id)s.%(ext)s" "URL"

# 按日期组织
yt-dlp -o "%(upload_date>%Y/%m/%d)s/%(title)s.%(ext)s" "URL"
```

`%(upload_date>%Y/%m/%d)s` 里的 `>` 是格式化操作符，把原始的 `YYYYMMDD` 字符串重新格式化为目录路径。

### 模板字段速查

| 字段 | 说明 |
|------|------|
| `%(title)s` | 视频标题 |
| `%(id)s` | 视频 ID |
| `%(uploader)s` | 上传者 |
| `%(upload_date)s` | 上传日期（YYYYMMDD） |
| `%(resolution)s` | 分辨率 |
| `%(ext)s` | 扩展名 |
| `%(playlist_title)s` | 播放列表标题 |
| `%(playlist_index)03d` | 播放列表序号（补零 3 位）|

### 多路径配置

```bash
# 指定下载路径
yt-dlp -P "/path/to/download" "URL"

# 临时文件先下载到 temp，完成后移到 home
yt-dlp -P "home:/data/videos" -P "temp:/tmp/yt-dlp" "URL"
```

`-P` 的 `home:` 和 `temp:` 前缀分别控制最终输出目录和临时文件目录。把临时目录设到 SSD、最终目录设到 NAS，可以避免下载过程中网络抖动导致的部分写入问题。

---

## 网络与反封锁

视频站点识别非浏览器流量的常见手段包括 IP 地理限制、TLS 指纹检测、Cookie 验证和 UA 检查。yt-dlp 针对这些场景提供了对应的参数。

### 代理

```bash
# HTTP/HTTPS 代理
yt-dlp --proxy "http://proxy.example.com:8080"

# SOCKS5 代理
yt-dlp --proxy "socks5://user:pass@127.0.0.1:1080"
```

### 伪装客户端（Impersonation）

部分网站通过 TLS 指纹识别机器人流量——即使 UA 和 Cookie 都对，TLS 握手的 cipher 列表和扩展顺序暴露了客户端不是真浏览器。yt-dlp 支持伪装成主流浏览器：

```bash
# 伪装成 Chrome
yt-dlp --impersonate "chrome" "URL"

# 伪装成 Edge (Windows)
yt-dlp --impersonate "chrome:windows-10" "URL"

# 查看所有支持的伪装目标
yt-dlp --list-impersonate-targets
```

底层使用 [curl_cffi](https://github.com/lexiforest/curl_cffi)（curl-impersonate 的 Python 绑定）实现 TLS 指纹伪装。这一功能需要额外安装 `curl_cffi` 依赖，二进制发行版默认包含。

### 地理限制绕过

```bash
# 使用指定国家的 XFF 头
yt-dlp --xff "US" "URL"

# 使用代理验证 IP（针对某些需要二次验证的站点）
yt-dlp --geo-verification-proxy "http://proxy.example.com:8080" "URL"
```

`--xff` 通过添加 `X-Forwarded-For` 头模拟来自指定国家的请求，对部分只检查 HTTP 头的站点有效；对真正校验 IP 的站点仍需配合代理。

---

## 批量下载与自动化

### 批量文件

将 URL 写入文件，每行一个：

```text
# urls.txt
https://www.youtube.com/watch?v=video1
https://www.youtube.com/watch?v=video2
https://www.youtube.com/watch?v=video3
```

```bash
yt-dlp -a urls.txt
```

`-a` 会顺序处理每个 URL。配合 `--download-archive` 可以跳过已下载项，配合 `--ignore-errors` 可以在某个 URL 失败时继续处理后续项。

### 预设别名（Preset Aliases）

预定义常用选项组合，减少重复输入：

```bash
# 下载为 mp3（预设）
yt-dlp --preset-alias mp3 "URL"

# 下载为 mp4（预设）
yt-dlp --preset-alias mp4 "URL"

# 自定义别名
yt-dlp --alias my-audio "-X -S aext:mp3,abr" "URL"
```

`--alias` 把一长串选项绑定到一个短名，后续直接用 `--preset-alias <name>` 调用。适合在团队内部统一下载规格。

### 日志与输出

```bash
# 安静模式（只打印进度）
yt-dlp -q "URL"

# 打印 JSON 信息
yt-dlp -j "URL"

# 打印特定字段
yt-dlp -O "%(title)s - %(resolution)s" "URL"

# 进度模板
yt-dlp --progress-template "[%(playlist_index)d/%(playlist_count)d] %(title)s" "URL"
```

`-j` 输出的 JSON 可以管道给 `jq` 做批量处理，是脚本化场景下提取元数据的标准做法。

---

## Python API：嵌入到代码中

yt-dlp 本身就是 Python 包，命令行能力全部通过 `yt_dlp.YoutubeDL` 类暴露。需要在 Web 服务、定时任务或数据处理流水线里调用下载能力时，直接用 Python API 比起 shell 调用命令行更可控——可以拿到结构化元数据、注入进度回调、动态调整选项。

### 基础调用

```python
from yt_dlp import YoutubeDL

URLS = ['https://www.youtube.com/watch?v=BaW_jenozKc']
with YoutubeDL() as ydl:
    ydl.download(URLS)
```

`with` 语句确保下载完成后正确释放网络连接和文件句柄。

### 配置选项

```python
import yt_dlp

ydl_opts = {
    'format': 'm4a/bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'm4a',
    }],
    'outtmpl': '%(title)s.%(ext)s',
}

with YoutubeDL(ydl_opts) as ydl:
    ydl.download(['https://www.youtube.com/watch?v=BaW_jenozKc'])
```

`ydl_opts` 的字段与命令行参数一一对应，`format` 对应 `-f`，`outtmpl` 对应 `-o`，`postprocessors` 对应 `--add-metadata`、`--embed-subs` 等后处理开关。

### 获取元数据（不下载）

```python
import yt_dlp

with YoutubeDL({'quiet': True}) as ydl:
    info = ydl.extract_info('https://www.youtube.com/watch?v=BaW_jenozKc', download=False)
    print(f"标题: {info['title']}")
    print(f"时长: {info['duration']}秒")
    print(f"格式数: {len(info['formats'])}")
```

`download=False` 只提取元数据不下载文件，返回的 `info` 字典结构与 `-j` 命令行输出的 JSON 一致。批量场景下可以先 `extract_info` 拿到时长和格式列表，过滤后再决定是否下载。

### 进度钩子

```python
import yt_dlp

def progress_hook(d):
    if d['status'] == 'downloading':
        print(f"进度: {d.get('_percent_str', 'N/A')}")
    elif d['status'] == 'finished':
        print('下载完成，进入后处理...')

ydl_opts = {
    'progress_hooks': [progress_hook],
}

with YoutubeDL(ydl_opts) as ydl:
    ydl.download(['https://www.youtube.com/watch?v=BaW_jenozKc'])
```

`progress_hooks` 接收一个回调列表，下载过程中每个状态变化都会触发。`d['status']` 的取值包括 `downloading`、`finished`、`error`，可用于实现自定义进度条、Webhook 通知或失败重试逻辑。

---

## 插件系统

yt-dlp 支持通过插件扩展功能，可加载自定义的 Extractor（提取器）和 PostProcessor（后处理器）。插件机制让自定义逻辑不必修改 yt-dlp 主仓库，便于在团队内分发和版本管理。

在插件系统出现之前，要支持一个新站点只能 fork 主仓库改代码再提 PR，等合并发版周期长，企业内部分站点的提取逻辑也不适合公开。插件系统把扩展点开放出来：自定义代码放在独立目录，yt-dlp 启动时自动扫描注册，主仓库升级不会覆盖插件，团队内部站点支持可以独立维护。

### 插件目录

在以下位置放置包含 `yt_dlp_plugins` 命名空间的包：

| 平台 | 路径 |
|------|------|
| Linux/macOS | `~/.config/yt-dlp/plugins/<pkg>/yt_dlp_plugins/` |
| Windows | `%APPDATA%/yt-dlp/plugins/<pkg>/yt_dlp_plugins/` |
| 便携安装 | `<yt-dlp.exe所在目录>/yt-dlp-plugins/<pkg>/yt_dlp_plugins/` |

### 插件示例

```python
# myplugin/yt_dlp_plugins/extractor/_myplugin.py
from yt_dlp.extractor import GenericIE

class MySiteIE(GenericIE):
    _VALID_URL = r'https?://mysite\.com/watch/(?P<id>\w+)'
    _TESTS = [{
        'url': 'https://mysite.com/watch/abc123',
        'info_dict': {'id': 'abc123', 'title': 'My Video'},
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)
        # 自定义提取逻辑
        return self.url_result(f'https://mysite.com/api/video/{video_id}')
```

插件类名以 `IE` 结尾自动注册，以 `_` 开头或包含在 `__all__` 中则可控制导入行为。`_VALID_URL` 是匹配规则，`_real_extract` 是实际请求和解析逻辑，返回的字典结构与内置 Extractor 一致。

---

## 架构解析

下载失败时，判断问题出在 Extractor、Downloader 还是 PostProcessor，决定了该改 URL 格式、网络参数还是 ffmpeg 选项。下面拆解 yt-dlp 的三层结构和一次下载请求的完整流程。

### 模块结构

```text
yt_dlp/
├── YoutubeDL.py       # 主引擎：调度下载流程
├── extractor/         # 1000+ 网站提取器
│   ├── _extractors.py # 所有提取器的注册表
│   ├── youtube.py     # YouTube 专用提取器
│   └── ...
├── downloader/        # 下载器实现
│   ├── http.py        # HTTP 下载
│   ├── hls.py         # HLS 流下载
│   ├── dash.py        # DASH 流下载
│   └── fragment.py    # 分片并发下载
├── postprocessor/    # 后处理器
│   ├── ffmpeg.py      # ffmpeg 封装（合并/转码/字幕）
│   ├── embedthumbnail.py
│   └── sponsorblock.py
├── networking/       # 网络层（curl_cffi/requests）
└── utils/             # 工具函数
```

`extractor/` 目录是 yt-dlp 维护工作量最大的部分，每个站点对应一个 `*.py` 文件，注册表 `_extractors.py` 把所有 Extractor 类按字母序导入。站点改版或反爬升级时，通常改对应的那一个文件就够了。

### 下载流程

一次完整的下载请求流经以下阶段：

```text
URL 输入 → Extractor.match_id()    # 匹配 URL，确定使用哪个提取器
        → Extractor._real_extract() # 向网站请求数据，解析视频信息
        → YoutubeDL.extract_info()  # 获取视频元数据（formats、字幕等）
        → Format Selector           # 根据用户选项筛选格式
        → Downloader                # 下载视频/音频流
        → Fragment Joiner           # 分片合并（HLS/DASH）
        → PostProcessor             # ffmpeg 合并、转码、字幕嵌入、元数据写入
        → Output
```

报错位置决定了排查方向：`Unable to extract` 错误出在 Extractor 阶段，通常是站点改版需要更新 yt-dlp；`HTTP Error 403/429` 出在 Downloader 阶段，需要加 `--impersonate` 或换代理；`ffmpeg not found` 出在 PostProcessor 阶段，是 ffmpeg 未安装或不在 PATH。

### Extractor 机制

每个支持的网站都有一个对应的 Extractor 类，主要职责：

1. `match_id()`：从 URL 中提取视频 ID
2. `_real_extract()`：向目标网站发起请求，解析页面/API，返回视频信息字典
3. `url_result()`：将提取结果转换为标准化格式

以 YouTube 为例，其 Extractor 还需要处理 signature（签名）解密、n-sig（下一代签名）反混淆等逻辑。YouTube 持续更新签名算法，yt-dlp 需要跟进反混淆逻辑——这是 yt-dlp 持续维护工作量最大的部分，也是为什么遇到 YouTube 下载失败时第一反应应该是更新版本。

### Downloader 分层

yt-dlp 支持多协议和多层并发：

| 下载层 | 说明 |
|--------|------|
| HTTP Downloader | 基础 HTTP 下载，支持断点续传 |
| HLS Downloader | 下载 `.m3u8` 清单文件，按 TS 分片下载 |
| DASH Downloader | 下载 `.mpd` 清单文件，按 segment 下载 |
| Fragment Downloader | 并发下载多个分片（`-N` 参数控制并发数）|

默认 `-N 1`（单线程），对于 HLS/DASH 流可提升到 4-8 加快速度。并发数过高可能触发站点限速，需要根据目标站点的反爬策略调整。

### PostProcessor 链路

后处理在下载完成后串行执行，典型链路：

```text
FFmpegMergeDownloader  # 合并视频+音频流（若有）
  → FFmpegFixupStretched  # 修复拉伸的流
  → FFmpegFixupM4a        # 修复 M4a 元数据
  → FFmpegSubtitlesConvertor  # 字幕格式转换
  → FFmpegEmbedSubtitle   # 嵌入字幕到 mp4/mkv
  → FFmpegMetadata        # 写入元数据
  → EmbedThumbnail        # 嵌入缩略图
  → SponsorBlock          # 标记/移除赞助段落
```

每一步都是可插拔的 PostProcessor，通过 `postprocessors` 参数可以添加、移除或调整顺序。某一步失败不会阻塞后续步骤，但可能导致输出文件缺少对应的内容（如字幕没嵌入但视频正常）。

---

## 常见问题

### Q: 下载视频被限速或拒绝？

按顺序尝试以下组合，从轻到重：

```bash
# 1. 先更新到 nightly（站点反爬更新频繁）
yt-dlp --update-to nightly

# 2. 加浏览器伪装
yt-dlp --impersonate "chrome" "URL"

# 3. 配合代理
yt-dlp --impersonate "chrome" --geo-verification-proxy "http://proxy:port" "URL"
```

如果仍然失败，检查是否需要登录 Cookie：用 `--cookies-from-browser chrome` 直接读取浏览器 Cookie，或用 `--cookies cookies.txt` 加载导出的 Cookie 文件。

### Q: 只想下载音频？

```bash
yt-dlp -x --audio-format mp3 "URL"
```

`-x` 触发 `FFmpegExtractAudio` 后处理器，`--audio-format` 指定输出格式。需要更高音质时加 `-S "abr:best"` 选最高码率音频流。

### Q: PyInstaller 打包的 exe 启动太慢？

yt-dlp 启动时会导入所有 Extractor，1000+ 个类的导入开销在 PyInstaller 冻结环境下尤其明显。构建时启用懒加载提取器：

```bash
python devscripts/make_lazy_extractors.py
python -m bundle.pyinstaller
```

这会把 Extractor 导入推迟到首次匹配 URL 时，启动时间可从数秒降到毫秒级。

### Q: 报错 "No video formats"？

通常是站点反爬机制触发，可尝试：

```bash
yt-dlp --no-check-certificates --impersonate "chrome" "URL"
```

`--no-check-certificates` 跳过 TLS 证书校验，对使用了自签证书或证书过期的内部站点有用；`--impersonate` 解决 TLS 指纹检测问题。

### Q: 如何查看所有支持网站？

```bash
yt-dlp --list-extractors
```

输出包含所有已注册 Extractor 的名称和匹配的 URL 模式。完整列表也可在 [yt-dlp Supported Sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) 查看。

### Q: 文件名带特殊字符导致报错？

视频标题里的 `/`、`:`、`|` 等字符在文件系统中非法，默认输出模板会自动替换为 `#`。需要更精细控制时加 `--restrict-filenames` 把所有非 ASCII 字符和空格也替换掉，或用 `--windows-filenames` 强制兼容 Windows 命名规则。

```bash
yt-dlp --restrict-filenames -o "%(title)s.%(ext)s" "URL"
```

### Q: 批量下载到一半被站点限速？

先降低并发再加重试。`-N` 控制分片并发，`--retries` 控制重试次数，`--sleep-requests` 在请求间加随机延迟：

```bash
yt-dlp -N 2 --retries 10 --sleep-requests 1 -a urls.txt
```

配合 `--download-archive` 跳过已下载项，可以安全地多次重跑同一批 URL 直到全部完成。

## 与 youtube-dl 的主要差异

yt-dlp 相比原版 youtube-dl 的主要改进（来自官方 README）：

| 差异 | yt-dlp | youtube-dl |
|------|--------|-------------|
| Python 版本 | 3.10+ | 2.6+/3.2+ |
| 格式排序 | 默认按分辨率/codec | 默认按比特率 |
| 默认容错 | `--no-abort-on-error` | 中断 |
| YouTube 支持 | n-sig 反混淆+Clips+Shorts | 基础 |
| 浏览器 Cookie | 支持所有主流浏览器 | 有限 |
| 章节分割 | `--split-chapters` | 不支持 |
| 多线程下载 | `--concurrent-fragments` | 不支持 |
| 插件系统 | 支持 | 不支持 |

youtube-dl 的最后一次大版本更新已较久，对新站点和 YouTube 反爬更新的跟进明显慢于 yt-dlp。新项目应直接选 yt-dlp；已有 youtube-dl 脚本可以通过 `yt-dlp` 命令别名平滑替换，多数参数兼容。

## 适用边界与采用建议

yt-dlp 适合：批量下载视频、提取音频、归档播放列表、嵌入到自动化流水线、需要精确控制格式和元数据的场景。

不适合：实时流媒体录制（用 streamlink 或 OBS）、需要 GUI 的非技术用户（用 yt-dlg 等图形前端）、对下载速度有极致要求且站点支持 aria2c 加速的场景（yt-dlp 的并发主要在分片层，不如 aria2c 的多连接下载）。

遇到站点无法下载时，按以下顺序排查：

1. 更新到 nightly 版本（站点反爬更新频繁，旧版本可能已失效）
2. 查阅 [yt-dlp Issues](https://github.com/yt-dlp/yt-dlp/issues) 是否有相同站点的已知问题
3. 用 `-v` 查看详细日志，定位失败发生在 Extractor、Downloader 还是 PostProcessor 阶段
4. 站点不在支持列表时，考虑编写自定义 Extractor 插件

## 进阶路径

按以下顺序深入使用 yt-dlp：

1. **配置文件固化常用选项**：在 `~/.config/yt-dlp/config` 写入默认参数（如 `-o` 模板、`--download-archive` 路径、`--embed-subs`），避免每次命令都带一长串选项。
2. **写一个批量下载脚本**：用 Python API + `--download-archive` 实现断点续传的播放列表归档，配合 `progress_hooks` 做失败告警。
3. **开发自定义 Extractor 插件**：为一个 yt-dlp 未支持的内部站点写 Extractor，理解 `_real_extract` 的返回字典结构和 `url_result` 的用法。
4. **集成到数据处理流水线**：用 `extract_info(download=False)` 抓元数据，用 `jq` 或 Python 过滤后决定下载哪些，配合 cron 或 Airflow 调度。
5. **阅读源码理解反爬应对**：从 `extractor/youtube.py` 入手，看 signature 解密和 n-sig 反混淆的实现，理解 yt-dlp 为什么需要持续维护。