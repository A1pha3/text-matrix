---
title: "yt-dlp：最强大的命令行视频下载工具完全指南"
date: 2026-05-23T03:05:00+08:00
slug: "yt-dlp-video-download-tool-guide"
description: "yt-dlp是一款开源命令行音视频下载工具，支持数千个网站，基于youtube-dl活跃fork而来。本文从安装、基础用法、格式选择、元数据处理、插件开发到架构设计全面解析，覆盖从入门到精通的全部核心知识。"
draft: false
categories: ["技术笔记"]
tags: ["yt-dlp", "视频下载", "ffmpeg", "Python", "开源工具"]
---

# yt-dlp：最强大的命令行视频下载工具完全指南

**如果你需要下载互联网上几乎任何视频，yt-dlp几乎是唯一的选择。**

这是一款命令行工具，支持超过一千个视频网站，从YouTube、TikTok到各种小众站点通吃。它从youtube-dl fork而来，目前GitHub Stars已超过16万，是同类工具中最活跃的分支。本文覆盖安装、核心用法、格式选择、元数据处理、插件开发，并深入解析其架构设计，帮助你从入门走向精通。

---

## 1. 项目概览

| 指标 | 值 |
|------|------|
| GitHub | [yt-dlp/yt-dlp](https://github.com/yt-dlp/yt-dlp) |
| Stars / Forks | 164,198 / 13,806（2026年5月） |
| 语言 | Python（3.10+） |
| 许可证 | Unlicense（源码） |
| 最新提交 | 2026-05-22 |

yt-dlp是一个**功能丰富的命令行音视频下载器**（feature-rich command-line audio/video downloader），核心能力包括：

- 支持**超过一千个网站**的视频提取
- 丰富的格式选择与排序机制
- 字幕提取与嵌入
- 元数据写入与缩略图嵌入
- 支持插件扩展
- 内置自动更新机制

它从youtube-dl fork，并持续合并社区上游的改进。相比原版youtube-dl，yt-dlp在维护活跃度、功能深度和反封锁能力上都领先一个身位。

---

## 2. 安装

### 2.1 二进制文件（推荐）

直接下载对应平台的二进制文件，无需安装Python：

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

### 2.2 pip安装

```bash
python -m pip install -U yt-dlp
```

通过pip安装后，更新命令为：

```bash
python -m pip install -U --pre yt-dlp
```

### 2.3 依赖：ffmpeg（必须）

yt-dlp的绝大多数能力都依赖外部工具**ffmpeg**，包括：

- 合并分离的视频和音频流
- 转换容器格式
- 提取和嵌入字幕
- 缩略图转换

建议直接从 [yt-dlp/FFmpeg-Builds](https://github.com/yt-dlp/FFmpeg-Builds) 下载预编译版本。安装后在终端输入 `yt-dlp --version` 确认安装成功即可。

> ⚠️ 注意：PyPI上有个名为`ffmpeg`的Python包，和ffmpeg命令行工具不是同一个东西，别装错了。

### 2.4 更新通道

yt-dlp提供三个发布通道：

| 通道 | 特点 | 适用场景 |
|------|------|----------|
| `stable` | 每月一次正式发布 | 一般用户 |
| `nightly` | 每日构建，推荐日常使用 | 多数用户首选 |
| `master` | 每次push触发构建 | 追求最新功能的开发者 |

```bash
# 更新到nightly（推荐）
yt-dlp --update-to nightly

# 更新到master
yt-dlp --update-to master

# 切换回stable
yt-dlp --update-to stable
```

超过90天未更新的版本会提示更新警告，可用 `--no-update` 抑制。

---

## 3. 最小示例

下载单个视频只需一条命令：

```bash
yt-dlp "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

下载时指定质量最高的可用格式：

```bash
yt-dlp -f "bv*+ba/b" "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

这条命令的含义是：优先选择**最佳视频（bv\*）+ 最佳音频（ba）**的组合格式。

---

## 4. 核心功能详解

### 4.1 格式选择

yt-dlp的格式选择机制极为灵活，是其最强大的能力之一。

#### 列出可用格式

```bash
yt-dlp -F "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

输出示例（截取部分）：

```
ID  EXT   RESOLUTION │   FPS │   CODECS    │   BR    │   SIZE
────────────────────────────────────────────────────────────
sb2 mhtml   images                │         │ unknown
18  mp4    426x240    24 │ av01   72kbps │ ~1MB
22  mp4    1280x720   22 │ avc1   ~2MB
```

#### 选择特定格式

```bash
# 按格式ID选择
yt-dlp -f 18 "URL"

# 组合视频+音频
yt-dlp -f "18+251" "URL"

# 选择最佳视频，不带音频
yt-dlp -f "bv" "URL"
```

#### 格式排序（Format Sorting）

yt-dlp 3.0+ 引入了强大的格式排序机制，用 `-S` 参数按多个维度排序：

```bash
# 优先选择分辨率高、codec新的格式
yt-dlp -S "res:1080,codec:avc" "URL"

# 先按文件大小排序，再选最佳画质
yt-dlp -S "filesize:desc,res:desc" "URL"

# 优先选择av1编码
yt-dlp -S "codec:av01" "URL"
```

排序优先级依次为：`ext` → `fps` → `resolution` → `codec` → `filesize` → `br` → `vr` → `gen` → `sr`（可叠加使用）。

#### 格式过滤器

```bash
# 只选择大于720p的视频
yt-dlp -f "bestvideo[height>=720]+bestaudio/best[height>=720]" "URL"

# 排除webm格式
yt-dlp -f "bestvideo-webm/bestaudio-webm" "URL"
```

### 4.2 字幕处理

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

### 4.3 元数据与缩略图

```bash
# 写入元数据JSON
yt-dlp --write-info-json "URL"

# 嵌入缩略图
yt-dlp --embed-thumbnail "URL"

# 全部写入
yt-dlp --write-description --write-info-json --write-thumbnail --embed-thumbnail "URL"
```

### 4.4 下载时间范围与章节

```bash
# 只下载第10秒到第60秒
yt-dlp --download-sections "*10-60" "URL"

# 按章节分割视频
yt-dlp --split-chapters "URL"
```

### 4.5 播放列表处理

```bash
# 只下载播放列表前10个视频
yt-dlp -I 1:10 "PLAYLIST_URL"

# 随机顺序下载
yt-dlp --playlist-random "PLAYLIST_URL"

# 排除已下载的视频（archive）
yt-dlp --download-archive archive.txt "PLAYLIST_URL"
```

---

## 5. 输出模板与文件组织

yt-dlp的输出文件名完全可定制，这是其最受高级用户喜爱的功能之一。

### 5.1 基本模板

```bash
# 默认模板：标题 [ID].扩展名
# Example: "Rick Astley - Never Gonna Give You Up [dQw4w9WgXcQ].mp4"

# 自定义文件名
yt-dlp -o "%(title)s-%(id)s.%(ext)s" "URL"

# 按日期组织
yt-dlp -o "%(upload_date>%Y/%m/%d)s/%(title)s.%(ext)s" "URL"
```

### 5.2 模板字段速查

| 字段 | 说明 |
|------|------|
| `%(title)s` | 视频标题 |
| `%(id)s` | 视频ID |
| `%(uploader)s` | 上传者 |
| `%(upload_date)s` | 上传日期（YYYYMMDD） |
| `%(resolution)s` | 分辨率 |
| `%(ext)s` | 扩展名 |
| `%(playlist_title)s` | 播放列表标题 |
| `%(playlist_index)03d` | 播放列表序号（补零3位）|

### 5.3 多路径配置

```bash
# 指定下载路径
yt-dlp -P "/path/to/download" "URL"

# 临时文件先下载到temp，完成后移到home
yt-dlp -P "home:/data/videos" -P "temp:/tmp/yt-dlp" "URL"
```

---

## 6. 网络与反封锁

### 6.1 代理

```bash
# HTTP/HTTPS代理
yt-dlp --proxy "http://proxy.example.com:8080"

# SOCKS5代理
yt-dlp --proxy "socks5://user:pass@127.0.0.1:1080"
```

### 6.2 伪装客户端（Impersonation）

部分网站通过TLS指纹识别机器人流量。yt-dlp支持伪装成主流浏览器：

```bash
# 伪装成Chrome
yt-dlp --impersonate "chrome" "URL"

# 伪装成Edge (Windows)
yt-dlp --impersonate "chrome:windows-10" "URL"

# 查看所有支持的伪装目标
yt-dlp --list-impersonate-targets
```

底层使用 [curl_cffi](https://github.com/lexiforest/curl_cffi)（curl-impersonate的Python绑定）实现TLS指纹伪装。

### 6.3 地理限制绕过

```bash
# 使用指定国家的XFF头
yt-dlp --xff "US" "URL"

# 使用代理验证IP（针对某些需要二次验证的站点）
yt-dlp --geo-verification-proxy "http://proxy.example.com:8080" "URL"
```

---

## 7. 批量下载与自动化

### 7.1 批量文件

将URL写入文件，每行一个：

```
# urls.txt
https://www.youtube.com/watch?v=video1
https://www.youtube.com/watch?v=video2
https://www.youtube.com/watch?v=video3
```

```bash
yt-dlp -a urls.txt
```

### 7.2 预设别名（Preset Aliases）

预定义常用选项组合，减少重复输入：

```bash
# 下载为mp3（预设）
yt-dlp --preset-alias mp3 "URL"

# 下载为mp4（预设）
yt-dlp --preset-alias mp4 "URL"

# 自定义别名
yt-dlp --alias my-audio "-X -S aext:mp3,abr" "URL"
```

### 7.3 日志与输出

```bash
# 安静模式（只打印进度）
yt-dlp -q "URL"

# 打印JSON信息
yt-dlp -j "URL"

# 打印特定字段
yt-dlp -O "%(title)s - %(resolution)s" "URL"

# 进度模板
yt-dlp --progress-template "[%(playlist_index)d/%(playlist_count)d] %(title)s" "URL"
```

---

## 8. Python API：嵌入到代码中

yt-dlp不仅是命令行工具，还是一个功能完整的Python库。

### 8.1 基础调用

```python
from yt_dlp import YoutubeDL

URLS = ['https://www.youtube.com/watch?v=BaW_jenozKc']
with YoutubeDL() as ydl:
    ydl.download(URLS)
```

### 8.2 配置选项

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

### 8.3 获取元数据（不下载）

```python
import yt_dlp

with YoutubeDL({'quiet': True}) as ydl:
    info = ydl.extract_info('https://www.youtube.com/watch?v=BaW_jenozKc', download=False)
    print(f"标题: {info['title']}")
    print(f"时长: {info['duration']}秒")
    print(f"格式数: {len(info['formats'])}")
```

### 8.4 进度钩子

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

---

## 9. 插件系统

yt-dlp 3.0+ 支持通过插件扩展功能，可加载自定义的 Extractor（提取器）和 PostProcessor（后处理器）。

### 9.1 插件目录

在以下位置放置包含 `yt_dlp_plugins` 命名空间的包：

| 平台 | 路径 |
|------|------|
| Linux/macOS | `~/.config/yt-dlp/plugins/<pkg>/yt_dlp_plugins/` |
| Windows | `%APPDATA%/yt-dlp/plugins/<pkg>/yt_dlp_plugins/` |
| 便携安装 | `<yt-dlp.exe所在目录>/yt-dlp-plugins/<pkg>/yt_dlp_plugins/` |

### 9.2 插件示例

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

插件类名以 `IE` 结尾自动注册，以 `_` 开头或包含在 `__all__` 中则可控制导入行为。

---

## 10. 架构解析

理解yt-dlp的架构，有助于在复杂场景下排错和自定义扩展。

### 10.1 模块结构

```
yt_dlp/
├── YoutubeDL.py       # 核心引擎：调度下载流程
├── extractor/         # 1000+ 网站提取器
│   ├── _extractors.py # 所有提取器的注册表
│   ├── youtube.py     # YouTube专用提取器
│   └── ...
├── downloader/        # 下载器实现
│   ├── http.py        # HTTP下载
│   ├── hls.py         # HLS流下载
│   ├── dash.py        # DASH流下载
│   └── fragment.py    # 分片并发下载
├── postprocessor/    # 后处理器
│   ├── ffmpeg.py      # ffmpeg封装（合并/转码/字幕）
│   ├── embedthumbnail.py
│   └── sponsorblock.py
├── networking/       # 网络层（curl_cffi/requests）
└── utils/             # 工具函数
```

### 10.2 下载流程

一次完整的下载请求流经以下阶段：

```
URL输入 → Extractor.match_id()   # 匹配URL，确定使用哪个提取器
       → Extractor._real_extract() # 向网站请求数据，解析视频信息
       → YoutubeDL.extract_info()  # 获取视频元数据（formats、字幕等）
       → Format Selector           # 根据用户选项筛选格式
       → Downloader                # 下载视频/音频流
       → Fragment Joiner           # 分片合并（HLS/DASH）
       → PostProcessor             # ffmpeg合并、转码、字幕嵌入、元数据写入
       → Output
```

### 10.3 Extractor机制

每个支持的网站都有一个对应的Extractor类，核心职责：

1. `match_id()`：从URL中提取视频ID
2. `_real_extract()`：向目标网站发起请求，解析页面/API，返回视频信息字典
3. `url_result()`：将提取结果转换为标准化格式

以YouTube为例，其Extractor还需要处理signature（签名）解密、n-sig（下一代签名）反混淆等复杂逻辑——这也是yt-dlp持续维护工作量最大的部分之一。

### 10.4 Downloader分层

yt-dlp支持多协议和多层并发：

| 下载层 | 说明 |
|--------|------|
| HTTP Downloader | 基础HTTP下载，支持断点续传 |
| HLS Downloader | 下载`.m3u8`清单文件，按TS分片下载 |
| DASH Downloader | 下载`.mpd`清单文件，按segment下载 |
| Fragment Downloader | 并发下载多个分片（`-N`参数控制并发数）|

默认`-N 1`（单线程），对于HLS/DASH流可提升到4-8以加快速度。

### 10.5 PostProcessor链路

后处理在下载完成后串行执行，典型链路：

```
FFmpegMergeDownloader  # 合并视频+音频流（若有）
  → FFmpegFixupStretched  # 修复拉伸的流
  → FFmpegFixupM4a        # 修复M4a元数据
  → FFmpegSubtitlesConvertor  # 字幕格式转换
  → FFmpegEmbedSubtitle   # 嵌入字幕到mp4/mkv
  → FFmpegMetadata        # 写入元数据
  → EmbedThumbnail        # 嵌入缩略图
  → SponsorBlock          # 标记/移除赞助段落
```

每一步都是可插拔的PostProcessor，通过 `postprocessors` 参数可以添加、移除或调整顺序。

---

## 11. 常见问题

### Q: 下载视频被限速/拒绝？

尝试以下组合：

```bash
yt-dlp --impersonate "chrome" --geo-verification-proxy "http://proxy:port" "URL"
```

### Q: 只想下载音频？

```bash
yt-dlp -x --audio-format mp3 "URL"
```

### Q: PyInstaller打包的exe启动太慢？

构建时启用懒加载提取器：

```bash
python devscripts/make_lazy_extractors.py
python -m bundle.pyinstaller
```

### Q: 报错"No video formats"？

通常是网站反爬机制触发，可尝试：

```bash
yt-dlp --no-check-certificates --impersonate "chrome" "URL"
```

### Q: 如何查看所有支持网站？

```bash
yt-dlp --list-extractors
```

---

## 12. 与youtube-dl的核心差异

yt-dlp相比原版youtube-dl的主要改进（来自官方README）：

| 差异 | yt-dlp | youtube-dl |
|------|--------|-------------|
| Python版本 | 3.10+ | 2.6+/3.2+ |
| 格式排序 | 默认按分辨率/codec | 默认按比特率 |
| 默认容错 | `--no-abort-on-error` | 中断 |
| YouTube支持 | n-sig反混淆+Clips+Shorts | 基础 |
| 浏览器Cookie | 支持所有主流浏览器 | 有限 |
| 章节分割 | `--split-chapters` | 不支持 |
| 多线程下载 | `--concurrent-fragments` | 不支持 |
| 插件系统 | 支持 | 不支持 |

---

## 结语

yt-dlp是命令行视频下载领域最成熟、维护最活跃的工具。它的强大来自于：超过一千个Extractor支撑的网站覆盖、极其精细的格式选择机制、灵活的后处理管道，以及一个始终跟得上网站反爬更新的维护团队。

掌握本文内容后，你应该能够：

- 独立完成各平台的视频下载
- 根据质量、编码、文件大小精确筛选格式
- 使用Python API将yt-dlp嵌入自己的工具
- 编写自定义Extractor插件
- 在复杂网络环境下稳定下载

如果遇到某个网站无法下载，建议先查阅 [yt-dlp Supported Sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) 确认是否在支持列表中，并检查是否有已知的Issue或Workaround。