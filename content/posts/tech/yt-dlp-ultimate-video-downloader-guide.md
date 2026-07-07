+++
date = '2026-05-24T00:00:00+08:00'
draft = false
title = 'yt-dlp：开源视频下载器'
slug = 'yt-dlp-ultimate-video-downloader-guide'
description = 'yt-dlp 是 youtube-dl 的社区活跃分支，支持 YouTube、Twitter、B 站等全球 1500+ 平台，是目前维护最活跃的开源视频音频下载工具。'
categories = ['技术笔记']
tags = ['开源', 'Python', '工具', '视频']
+++

# yt-dlp：开源视频下载器

## 学习目标

读完本文你应该能够：

- 说清 yt-dlp 与 youtube-dl 的关系，以及为什么今天它几乎成了命令行下载的事实标准
- 用 `-f` 选择合并特定清晰度与编码，而不是只会无脑下「最高清」
- 把播放列表、字幕、区间下载、登录内容这些常见需求做成可复用的命令
- 判断哪些平台 yt-dlp 能下、哪些受 DRM（数字版权管理）限制根本下不了
- 在批量归档时避开常见的坑：命名冲突、断点续传、限速与并发的取舍

## 目录

- [它解决什么问题](#它解决什么问题)
- [核心能力](#核心能力)
- [它是怎么工作的](#它是怎么工作的)
- [快速上手](#快速上手)
- [六个常用命令示例](#六个常用命令示例)
- [三个真实任务流](#三个真实任务流)
- [常见问题与排查](#常见问题与排查)
- [自测题](#自测题)
- [练习](#练习)
- [继续深入](#继续深入)
- [相关资源](#相关资源)

## 它解决什么问题

视频网站从来没打算让你把内容存到本地。它们用 HLS / DASH 把视频切成几百个几秒长的小分片，再用签名令牌保护播放地址，过期就失效。浏览器能播，是因为前端按既定顺序把这些分片拼起来——但如果你想离线看、做素材库、或者批量归档一个 UP 主的全部作品，手动做这件事根本不现实。

yt-dlp 做的事情就是把「浏览器怎么拿到并拼接视频」这一整套流程自动化：解析页面拿到真实播放地址、选分辨率、下载分片、用 `ffmpeg` 合并成单个文件、顺手把字幕和元数据也带上。它最早的母体 youtube-dl 在 2021 年后基本停更，yt-dlp 接手后修了大批兼容性 bug、补了大量站点支持，现在是命令行视频下载里维护最活跃的那个。

## 核心能力

### 平台覆盖

支持 1500+ 站点，覆盖主流视频、社交、直播与课程平台：

| 类别 | 代表平台 |
|------|---------|
| 国际视频 | YouTube、Vimeo、Dailymotion、Twitch |
| 社交 | Twitter / X、Instagram、Facebook、TikTok |
| 中国平台 | B 站（哔哩哔哩）、抖音、快手、小红书、微博视频 |
| 音乐 | SoundCloud、Bandcamp（注意：Spotify、Apple Music 这类 DRM 保护的流媒体不在支持范围） |
| 课程 | Coursera、Udemy、Skillshare 的部分公开内容 |
| 其他 | 各国电视台、新闻网站、PeerTube 实例 |

一个容易踩的坑：DRM 保护的付费流媒体（Netflix、Spotify、Apple Music 等）yt-dlp 下不了，这不是 bug，是协议层就禁止了。需要这类内容时得换专用工具，而且要先确认你当地的合法使用边界。

### 格式与质量

- **封装**：输出 MP4 / WebM / MKV 等，可指定浏览器兼容格式
- **纯音频**：`-x` 抽取音轨，转成 MP3 / M4A / FLAC / Opus / WAV
- **质量选择**：按分辨率、帧率、编码、文件后缀精确挑选，而不是只有「最好」一档
- **字幕**：可下载内嵌字幕与自动生成字幕（`--write-auto-subs`），多语言时按 `--sub-langs` 过滤

### 下载健壮性

- 断点续传：中断后重跑同一条命令会从已下载处继续
- 自动重试：网络抖动时按 `--retries` 反复尝试
- 并发分片：`-N` 同时拉多个分片，带宽够时明显提速
- 登录内容：通过 `--cookies-from-browser` 或 `--cookies` 复用浏览器登录态
- 直播与回放：支持追下载进行中的直播，结束后拿到完整回放
- 区间与章节：用 `--download-sections` 按时间戳截一段，或按章节拆分

### 输出模板

文件名和目录结构由 `-o` 的模板变量控制，可以全自动归类：

```bash
# 按上传者分目录、标题命名
yt-dlp -o "%(uploader)s/%(title)s.%(ext)s" URL

# 抽音频并内嵌封面
yt-dlp -x --embed-thumbnail -o "%(title)s.%(ext)s" URL
```

`%(uploader)s`、`%(title)s`、`%(ext)s` 这类占位符在文档里有完整清单，常用的还有 `%(playlist_title)s`、`%(epoch)s`、`%(height)s`，用来避免批量下载时文件名撞车。

## 它是怎么工作的

yt-dlp 不是「一个巨大的下载函数」，而是一条可拆解的流水线，理解它对排查问题很有用：

1. **Extractor（提取器）**：每个站点对应一个 Python 类，负责解析页面、拿到分片地址和元数据。所谓「支持某平台」本质上就是存在对应的 Extractor。
2. **Downloader（下载器）**：拿到地址后实际拉取分片，处理续传、重试、并发。
3. **PostProcessor（后处理器）**：下载完之后做合并、转码、内嵌字幕/封面、改格式等，多数后处理依赖 `ffmpeg`。

也就是说，你下到一个奇怪结果（比如只有音频没有画面、字幕没嵌进去），先想清楚它卡在 Extractor 解析、Downloader 拉取，还是 PostProcessor 合并，定位会快很多。项目用 Python 3.8+ 开发，运行时依赖极少，核心外部依赖就是 `ffmpeg`。

## 快速上手

```bash
# 推荐用 pipx 隔离安装，避免污染全局 Python
pipx install yt-dlp

# 一条命令下单个视频
yt-dlp "https://www.youtube.com/watch?v=VIDEO_ID"

# 合并最高画质视频流与音频流
yt-dlp -f "bestvideo+bestaudio/best" URL

# 只抽音频并转成 MP3
yt-dlp -x --audio-format mp3 URL

# 列出所有可选格式，挑之前先看一眼
yt-dlp --list-formats URL
```

`--list-formats`（简写 `-F`）是排错第一步：它把服务器提供的每条音视频流、分辨率、编码、文件大小都打出来，你再据此写 `-f` 表达式，比盲猜稳得多。

## 六个常用命令示例

```bash
# 1. 下整个播放列表，按序号命名，断点续传
yt-dlp -o "%(playlist_index)03d-%(title)s.%(ext)s" PL_URL

# 2. 只下 720p 及以下的合并流，适合存手机
yt-dlp -f "bestvideo[height<=720]+bestaudio/best[height<=720]" URL

# 3. 下载中文字幕并内嵌（无字幕则跳过不报错）
yt-dlp --write-subs --sub-langs "zh-Hans,zh-CN" --embed-subs URL

# 4. 只截取 01:00 到 02:30 这一段
yt-dlp --download-sections "*00:01:00-00:02:30" URL

# 5. 复用浏览器登录态下会员内容
yt-dlp --cookies-from-browser chrome URL

# 6. 限速到 2MB/s 并 8 线程并发，避免把带宽占满
yt-dlp -r 2M -N 8 URL
```

`-f` 的过滤语法值得花十分钟读文档：`[height<=720]` 按高度过滤、`+` 表示合并、`/best` 是兜底。写对了能省下大量重复下载的流量。

## 三个真实任务流

**归档一个 UP 主的全部公开视频**：用频道页 URL 配合播放列表模板，加 `-N 4` 并发、`--retries 3` 容错，挂一晚上基本能跑完。关键是模板里带 `%(upload_date)s`，以后重跑同一条命令，已存在的文件会被跳过（用 `--no-overwrites` 或默认行为），只补新作品。

**把课程视频转成可离线学习的素材库**：先 `-F` 看清有没有 1080p 的 `bestvideo+bestaudio`，再统一 `-f` 下载并 `--embed-subs` 带上字幕。如果课程在付费墙后，先确认是否允许下载，再用 `--cookies-from-browser` 取登录态。

**从采访视频里抽音频做转写**：`-x --audio-format opus` 抽成体积小、语音保真的 Opus，后续喂给 Whisper 之类做转写。这里不需要高码率视频，纯音频能省 90% 以上体积。

## 常见问题与排查

### Q1：提示 `ffmpeg` 没找到 / 合并失败？

yt-dlp 合并和转码依赖 `ffmpeg`。装好并确保 `ffmpeg` 在 `PATH` 里，再跑 `--version` 验证。只下单一流（不合并）时其实不强制需要它。

### Q2：为什么有的视频下下来没有声音？

你大概率选了纯视频流（`bestvideo` 本身不含音轨）。用 `bestvideo+bestaudio` 让后处理器合并音视频，或者直接写 `/best` 让它自己选带声的合并流。

### Q3：`--cookies-from-browser chrome` 报错？

常见原因是浏览器正在运行、cookie 被锁，或者系统上有多个 Chrome 配置。先关掉浏览器再试，或导出 cookie 文件用 `--cookies cookies.txt`。

### Q4：下载一半断了，要重头再来吗？

不用。`-c`（默认开启）会断点续传。重跑同一条命令即可从已下载处继续；用播放列表模板时，已完成的条目通常会被跳过。

### Q5：下 Spotify / Netflix 提示不支持？

这些是 DRM 保护的流媒体，yt-dlp 在协议层面就下不了。这不是配置问题，换专用工具前请先确认当地的合法使用范围。

### Q6：如何避免批量下载把带宽占满？

用 `-r 2M` 限速、`-N 8` 控制并发分片数，两者配合既能跑满空闲带宽，又不至于把家里网络挤死。

## 自测题

**概念题**

1. yt-dlp 的「支持某平台」本质上是支持什么？排查「下下来只有画面没声音」时，应该先怀疑流水线里的哪一段？
2. `bestvideo+bestaudio/best` 里 `+` 和 `/` 各表示什么语义？如果只写 `bestvideo` 会发生什么？
3. 为什么 Spotify、Netflix 这类平台 yt-dlp 下不了，但这不被视为 bug？

**场景题**

4. 你要离线归档一个 200 集的教程播放列表，希望断点续传、按序号命名、不重复下载已有文件。写出核心命令，并说明模板里你会放哪些占位符。
5. 你只想要某视频 1 分 30 秒到 2 分的片段做素材。用哪个参数实现？它依赖哪一段流水线？
6. 合并报 `ffmpeg` 相关错误，但单流下载正常。请说明原因和最简修复步骤。

**进阶判断**

7. 下面哪个需求 yt-dlp 适合、哪个不适合，为什么：把 B 站 UP 主全部视频存本地；把网易云会员歌曲批量转 MP3；给团队做课程离线库并带字幕。

## 练习

1. 挑一个你常看的 YouTube 频道的单个视频，用 `-F` 列出格式，挑一条 1080p 的 `bestvideo+bestaudio` 合并下载，确认成品有声画。
2. 用 `--download-sections` 截取任意视频里 30 秒的一段，验证区间下载是否如预期。
3. 写一个 shell 函数 `yta()`，接收 URL，自动抽 Opus 音频并内嵌封面，把常用参数固化下来。
4. 对一个需要登录才能看的视频，用 `--cookies-from-browser` 复现下载；再故意不传 cookie 跑一次，对比报错差异。
5. 用 `-o` 模板把一个播放列表下成「序号-标题」结构，故意制造一次同名冲突，观察 yt-dlp 的默认覆盖/跳过行为，再决定要不要加 `--no-overwrites`。

## 继续深入

能答对上面自测题里大部分内容后，可以往这几个方向走：

- 读官方文档的 [Format Selection](https://github.com/yt-dlp/yt-dlp#format-selection) 一节，把 `-f` 的过滤、合并、排序语法吃透，这是 80% 日常问题的来源
- 研究 Extractor 源码结构，当你关心的站点支持变差时，能自己定位是页面改版还是选择器失效
- 把 yt-dlp 接进 `ffmpeg` 流水线，做批量转码、片段拼接、字幕烧录的工程化处理
- 了解 `yt-dlp` 的插件机制（如 `yt-dlp-get-pot` 处理签名挑战），在站点加强反爬时仍有可行路径

## 相关资源

- 仓库：https://github.com/yt-dlp/yt-dlp
- 文档与格式选择：https://github.com/yt-dlp/yt-dlp#readme
- 发布页（更新日志与最新构建）：https://github.com/yt-dlp/yt-dlp/releases
- ffmpeg：https://ffmpeg.org
