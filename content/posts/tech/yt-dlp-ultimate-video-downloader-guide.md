+++
date = '2026-05-24T00:00:00+08:00'
draft = false
title = 'yt-dlp：开源视频下载器'
slug = 'yt-dlp-ultimate-video-downloader-guide'
description = 'yt-dlp 是 youtube-dl 的社区活跃分支，支持 YouTube、Twitter、B站等全球 1500+ 平台，是目前最强大的开源视频音频下载工具。'
categories = ['技术笔记']
+++

# yt-dlp：开源视频下载器

## 基本信息

- **语言**: Python
- **作者**: yt-dlp Team
- **链接**: https://github.com/yt-dlp/yt-dlp
- **前身**: youtube-dl（已停止维护）

## 这是什么

yt-dlp 是 youtube-dl 的社区活跃分支，是目前最活跃的开源视频音频下载工具。项目在 youtube-dl 基础上修复了大量兼容性问题，新增了平台支持，持续高速迭代。

## 核心能力

### 海量平台支持
支持 **1500+** 网站和平台，涵盖：

| 类别 | 代表平台 |
|------|---------|
| 视频 | YouTube, TikTok, Twitter/X, Instagram, Facebook |
| 中国平台 | B站(哔哩哔哩)、抖音、快手、小红书、微博视频 |
| 流媒体 | Twitch, Vimeo, Dailymotion, Peertube |
| 音乐 | Spotify, SoundCloud, Bandcamp |
| 课程 | Coursera, Udemy, Skillshare |
| 其他 | 各国电视台、新闻网站、私人服务器等 |

### 多格式与质量选择
- **视频**: MP4/WebM/AVI 和所有浏览器兼容格式
- **音频**: MP3/M4A/FLAC/Opus/WAV，可提取纯音频
- **质量**: 支持选择特定分辨率、帧率、编码器
- **字幕**: 自动下载字幕，支持翻译

### 高级下载功能
- 📡 断点续传 / 分段下载
- 🔄 自动重试与恢复
- ⚡ 多线程并发下载（`-N` 参数）
- 🔗 处理登录内容（Cookie 支持）
- 📺 下载直播回放
- 🎯 选择性下载章节/时间段
- 🖼️ 下载缩略图和元数据

### 模板化输出
强大的输出模板系统，可自定义文件名、目录结构和元数据保存方式：

```bash
# 按频道/播放列表自动建立目录
yt-dlp -o "%(uploader)s/%(title)s.%(ext)s" URL

# 只下载音频并嵌入封面
yt-dlp -x --embed-thumbnail -o "%(title)s.%(ext)s" URL
```

## 🏗️ 技术亮点

```python
# Python 项目，架构清晰，扩展性强
# 核心提取器（Extractor）以插件形式存在
# 新增平台只需实现对应 Extractor 类
```

项目采用 Python 3.8+ 开发，依赖极少（仅需 ffmpeg 用于转码），安装包体积小。

## 💡 使用场景

| 场景 | 说明 |
|------|------|
| 离线观看 | 下载视频到本地，无网也能看 |
| 音乐提取 | 从 MV 提取无损音乐音频 |
| 学习资料 | 下载 Coursera / B站课程离线观看 |
| 备份收藏 | 收藏珍贵视频内容到本地 |
| 内容分析 | 配合 FFmpeg 提取帧/音频流做二次分析 |

## 🚀 快速上手

```bash
# 安装（pipx 方式推荐）
pipx install yt-dlp

# 基本下载
yt-dlp "https://www.youtube.com/watch?v=VIDEO_ID"

# 下载最高质量 MP4
yt-dlp -f "bestvideo+bestaudio/best" URL

# 只下载音频（MP3）
yt-dlp -x --audio-format mp3 URL

# 查看所有可用格式
yt-dlp --list-formats URL
```

## 📝 适用人群

- 🎬 内容创作者（素材采集与备份）
- 📚 学生党（下载课程离线学习）
- 🎵 音乐爱好者（提取无损音频）
- 🔧 开发者（媒体处理流水线集成）
- 🕵️ 研究者（数据集构建与内容分析）

## ⭐ 亮点

- 🌟 GitHub Stars 持续增长，社区极度活跃
- 🔌 插件式架构，1500+ 平台即装即用
- 🛠️ 功能最全的视频下载工具，没有之一
- ⚡ 持续更新，修复及时，支持最新平台
- 🎯 中国平台（B站/抖音/小红书等）支持完善

> GitHub: https://github.com/yt-dlp/yt-dlp