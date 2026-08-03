---
title: "Claude Video：让Claude真正"看懂"视频的开源技能"
date: 2026-08-04T03:20:00+08:00
slug: "claude-video-watch-skill"
github_repo: "bradautomates/claude-video"
description: "Claude Video 是一个开源技能，让 Claude 能够"观看"视频内容——提取帧画面和字幕，基于画面内容回答问题，支持 YouTube、TikTok 等多种视频源。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "AI视频分析", "开源", "技能", "自动化"]
---

## 一句话概览

[Claude Video](https://github.com/bradautomates/claude-video) 是一个开源技能（Skill），让 Claude 能够"观看"任意视频——自动下载视频、提取关键帧、转录音频，再把画面和文字一起交给 Claude 分析。支持 YouTube、TikTok、Loom、X、Instagram 等主流视频源，GitHub 星标超 1.3 万。

## 它解决什么问题

Claude 是一个强大的语言模型，但它有一个先天缺陷：**看不了视频**。

你在 YouTube 上看到一段精彩的技术演讲，想让 Claude 帮你总结要点——它做不到。你录了一段屏幕操作视频想排查 bug，把链接丢给 Claude——它只能告诉你"我无法访问视频内容"。

这不是某个功能的缺失，而是架构层面的限制。Claude 处理的是文本和图片，而视频是动态的、包含连续画面和音频的信息流。两者之间存在一道鸿沟。

Claude Video 做的事情，就是在鸿沟上架一座桥：**把视频拆解成 Claude 能理解的格式——帧（图片）+ 字幕（文本）**，然后让 Claude 像看一本图文并茂的书一样"读完"整段视频。

## 安装

### Claude Code 用户（推荐）

两行命令搞定：

```bash
# 添加技能市场源
/plugin marketplace add bradautomates/claude-video

# 安装 watch 技能
/plugin install watch@claude-video
```

安装完成后，在任意对话中输入 `/watch` 即可触发。

### 其他平台（Cursor、Windsurf 等）

通过 npx 安装：

```bash
npx skills add bradautomates/claude-video -g
```

`-g` 表示全局安装，所有项目都能用。

### 依赖说明

首次运行时，脚本会**自动检查并安装**以下工具（macOS 通过 Homebrew）：

- **ffmpeg** — 视频帧提取
- **yt-dlp** — 视频下载

你不需要手动装任何东西，第一次跑 `/watch` 时一切自动就位。

唯一需要你操心的是 **Whisper API key**：当视频本身没有内嵌字幕时，需要调用 Whisper 做语音转文字。如果视频已有字幕（大多数 YouTube 视频都有），这一步完全免费，不需要任何 key。

## 工作原理

整个流水线分五步，对用户完全透明：

```
视频 URL → 下载 → 字幕检测 → 帧提取 → 转录 → 交给 Claude
```

| 步骤 | 做什么 | 用什么 |
|------|--------|--------|
| 下载 | 抓取视频文件 | yt-dlp |
| 字幕检测 | 检查视频是否自带字幕 | yt-dlp |
| 帧提取 | 按策略截取画面 | ffmpeg |
| 转录 | 无字幕时转文字 | Whisper API |
| 分析 | 帧 + 字幕交给 Claude | Claude 自身 |

关键设计：**帧去重**。视频里大量连续帧画面几乎一模一样（比如一个人坐在镜头前说话）。Claude Video 会自动丢弃视觉相似的重复帧，只保留有信息量的画面。这不是省着玩——每一帧都是要花 token 的。

## 四种详情模式

这是 Claude Video 最核心的配置项，决定了"看多细"：

| 模式 | 帧提取策略 | 帧上限 | 适用场景 |
|------|-----------|--------|---------|
| `transcript` | 不提取帧 | 0 | 只要文字内容，零成本 |
| `efficient` | 关键帧 | 50 | 快速浏览，省 token |
| `balanced` | 场景切换检测 | 100 | 日常默认选择 |
| `token-burner` | 场景切换检测 | 无上限 | 不差钱，细节拉满 |

默认模式是 `balanced`。大多数场景下它就够了——100 帧足以覆盖一个 10 分钟视频的所有关键画面变化。

如果你只想要文字内容（比如播客、讲座），用 `transcript` 模式，完全不消耗图片 token。

## 用法示例

### 场景一：总结一个技术演讲

```
/watch https://www.youtube.com/watch?v=xxxxx --mode balanced
```

Claude 会看完整个视频，给你一份结构化总结：核心观点、关键论据、时间线。

### 场景二：诊断屏幕录制中的 bug

```
/watch https://www.loom.com/share/xxxxx --mode token-burner
```

你录了一段操作复现 bug 的视频，用 `token-burner` 模式不漏任何细节。Claude 能看到每一帧画面变化，帮你定位问题。

### 场景三：只提取文字内容

```
/watch https://www.youtube.com/watch?v=xxxxx --mode transcript
```

播客、讲座、纯对话类视频——画面没有信息量，字幕就是一切。这个模式不提取任何帧，零图片消耗。

### 场景四：分析特定片段

```
/watch https://www.youtube.com/watch?v=xxxxx --start 2:15 --end 2:45
```

只看视频中 2 分 15 秒到 2 分 45 秒的内容。适合定位到关键片段后深入分析，避免浪费 token 在无关部分上。

### 场景五：播放列表转笔记

把整个播放列表的视频逐个丢给 Claude，让它统一整理成一份结构化笔记。对于系列教程、会议录像这类场景，效率极高。

## 帧预算与成本

每提取一帧画面，Claude 都需要用图片 token 来"看"它。所以帧的数量直接决定了 token 消耗：

- **transcript 模式**：0 帧，纯文本，几乎不花钱
- **efficient 模式**：上限 50 帧，适合控制成本
- **balanced 模式**：上限 100 帧，大多数视频的最佳平衡点
- **token-burner 模式**：无上限，长视频可能提取数百帧，适合重要内容

实际帧数取决于视频内容。一个画面变化很少的讲座视频，即使 `balanced` 模式可能也只提取 20-30 帧（因为去重）。而一个画面快速切换的 MV，可能轻松触及上限。

**建议策略**：先用 `balanced` 快速过一遍，发现需要深入分析的视频再切 `token-burner` 精看。

## 适用边界

### 支持的视频源

基于 yt-dlp，理论上支持数百个平台，实测覆盖：

- YouTube（含播放列表）
- TikTok
- Loom
- X / Twitter
- Instagram

只要 yt-dlp 能下载的，Claude Video 就能看。

### 不擅长的场景

- **纯音频无画面**——技术上能转录，但 Claude Video 的优势在于"看画面"。纯音频场景直接用转录工具更合适
- **需要实时分析**——流程是先下载再处理，不是实时流式分析
- **超长视频**——一部两小时的电影即使 `transcript` 模式也会产生大量文本。建议配合 `--start` / `--end` 分段处理
- **无字幕且无 Whisper key**——没有字幕的视频需要 Whisper API 做转录，缺少 key 时只能提取帧画面，无法获取音频内容

## 小结

Claude Video 的价值在于：它把"让 AI 看视频"这件本来需要自己搭建流水线的事情，变成了一条 `/watch` 命令。下载、帧提取、转录、去重——全部自动化。

14k 星标说明了一切。如果你在日常工作中需要让 Claude 处理视频内容，这个技能几乎是必装的。
