---
title: "Claude Video：给 Claude 补上「看视频」这条输入通道"
date: 2026-08-04T03:20:00+08:00
slug: "claude-video-watch-skill"
github_repo: "bradautomates/claude-video"
description: "一个开源技能，把「看视频」拆成下载、抽帧、转录三步，让 Claude 基于画面和字幕回答问题。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "AI视频分析", "开源", "技能", "自动化"]
---

Claude 能读网页、跑脚本、浏览代码库，唯独开箱看不了视频。你丢给它一个 YouTube 链接，它要么猜标题，要么拉一段丢了九成画面信息的字幕。Claude Video 的入手点，是把"看视频"拆成 Claude 真正能处理的输入——帧（图片）加字幕（文本），再让 Claude 通读。

## 快速定位

[bradautomates/claude-video](https://github.com/bradautomates/claude-video)，MIT 协议，Python 实现，2026-04 创建。截至 2026-08-07，Stars 约 1.4 万（14,366）、Forks 1,377。核心是一个 `/watch` 命令。

## 它解决什么问题

视频是动态的：连续画面加音频。Claude 的输入通道只有文本和图片，所以"让 Claude 看视频"要做的是把视频转成这两种东西——帧图、字幕文本。Claude Video 把这条转换链路做成了开箱即用：

```text
视频 URL / 本地路径 → 下载 → 抽帧 → 转录 → 帧 + 字幕交给 Claude
```

| 环节 | 做什么 | 用什么 |
|---|---|---|
| 下载 | 抓取视频文件 | yt-dlp |
| 字幕检测 | 优先取内嵌字幕，无则转音频 | yt-dlp |
| 抽帧 | 按 detail 模式截画面 | ffmpeg |
| 转录 | 无字幕时语音转文字 | Whisper（Groq / OpenAI） |
| 分析 | 帧 + 字幕交给 Claude | Claude 自身 |

## 帧是成本大头

token 开销几乎全在帧上——每帧都是一张图片。抽帧怎么选、怎么去重，直接决定一次 `/watch` 花多少。

### 四种 detail 模式

| 模式 | 抽帧引擎 | 帧上限 | 说明 |
|---|---|---|---|
| `transcript` | 不用帧 | 0 | 只取字幕，接近零成本 |
| `efficient` | 关键帧（`-skip_frame nokey`） | 50 | 只重建关键帧，约 0.5 秒，最快 |
| `balanced` | 场景切换检测 | 100 | 默认档，日常够用 |
| `token-burner` | 场景切换检测 | 不设上限 | 长视频、要细节时用 |

注意 `efficient` 只负责抽得快，不负责帧少。低动态画面里关键帧可能比场景切换点还多，所以 efficient 偶尔会返回比 balanced 更多的帧。

### 去重

同一块画面停留很久时，场景检测会产出一堆几乎一样的帧。去重在交给 Claude 之前把这些帧丢掉：先缩成 16×16 灰度缩略图，再与上一张"保留帧"算平均像素差，差值 ≤2.0（0–255 刻度）就判定为重复。逐帧对比的是上一张保留帧而不是紧邻帧，这样慢速淡入淡出也能被抓住。帧数上限在去重之后才生效，预算只花在真正不同的画面上。

## 转录：免费字幕优先

字幕优先用 yt-dlp 拉到的内嵌字幕（手动或自动生成都有），免费且即时。真正没字幕时才走 Whisper 兜底——默认 Groq 的 `whisper-large-v3`（更快更便宜），可切 OpenAI 的 `whisper-1`。连 Whisper 都不想配，用 `--no-whisper` 关掉，只留帧。所以 Whisper 的 API key 不是必需项，只有"没字幕"的场景才碰到。

## 一次"看视频"怎么流过系统

设想你收到一段屏幕录制，对方说 UI 在某处崩了。`/watch bug-repro.mov what's going wrong?`：

1. 本地文件无需下载，直接进入抽帧。
2. 屏幕录制没有字幕，走 Whisper 兜底，转出一份带时间戳的逐字稿。
3. 按默认 balanced 做场景检测抽帧，去重后留下有信息量的画面。
4. 脚本把帧路径（带 `t=MM:SS` 标记）和带时间戳的逐字稿一起交给 Claude。
5. Claude 并行 Read 每张帧，对照逐字稿定位问题出现的那一帧，通常不用你打开文件就能说出原因。

## 帧预算其实按时长走

每次并不是固定 100 帧。默认预算随视频时长调整，超过 10 分钟会在 capped 模式下被摊薄：

| 时长 | 默认帧数 |
|---|---|
| ≤30 秒 | 约 30 |
| 30 秒–1 分钟 | 约 40 |
| 1–3 分钟 | 约 60 |
| 3–10 分钟 | 约 80 |
| >10 分钟 | 100（触及上限，提示稀疏扫描） |

超长视频建议用 `token-burner`，或 `--start` / `--end` 圈定片段——片段的帧预算更密，比整段稀疏扫一遍有用得多。

## 四种模式实测下来差多少

README 给了一组真实跑数：一段 49 分 08 秒的 YouTube 视频（1280×720、英文自动字幕），长且画面基本静止，正好是压帧数上限最狠的场景。下载一次约 37 秒 / 76 MB，三种抽帧模式共用。

| 模式 | 帧数 | 抽帧耗时 | 估算图片 token |
|---|---|---|---|
| `transcript` | 0 | ~4.5 秒 | 0（约 26.6k 文本 token） |
| `efficient` | 50 | ~0.5 秒 | ~9.8k |
| `balanced` | 100 | ~20.9 秒 | ~19.7k |
| `token-burner` | 116 | ~21.0 秒 | ~22.8k |

图片 token 按 Anthropic 的"宽 × 高 / 750"估算，默认 512px 宽度下这些 720p 帧是 512×288，约 197 token/帧；`--resolution 1024` 大约再翻 4 倍。

看这段数字要分清几点：
- 测的是抽帧引擎的提取耗时和 token 开销，不是端到端问答质量。
- `efficient` 快约 40 倍，代价是只认关键帧。
- 不能推出"所有视频都这样"——这段是压迫上限的极端用例。高动态视频里 balanced 会抽满 100、token-burner 会保留全部场景切换帧（可能触发 >250 帧的 token 警告）。

## 安装

### Claude Code

```text
/plugin marketplace add bradautomates/claude-video
/plugin install watch@claude-video
```

更新用 `/plugin update watch@claude-video`。

### Codex、Cursor、Copilot、Gemini CLI 等宿主

```bash
npx skills add bradautomates/claude-video -g
```

`-g` 装到用户级（`~/.codex/skills`、`~/.cursor/skills` 等），去掉则装进当前项目。claude.ai 网页版可下载 `watch.skill` 手动导入。

### 依赖

首次 `/watch` 会跑 setup 检查。macOS 上自动 `brew install ffmpeg yt-dlp`，Linux / Windows 打印对应命令。ffmpeg 负责抽帧，yt-dlp 负责下载和字幕。

## 典型用法

- 分析别人的内容：`/watch <URL> what hook did they open with?`
- 诊断 bug：`/watch screen-recording.mov when does the UI break?`
- 总结长视频：`/watch <URL> summarize this`
- 播放列表转笔记：把系列里每个视频挨个 `/watch` 成一份带时间戳的笔记

## 什么时候值得用

- 常让 Claude 处理视频内容（分析别人的视频、诊断屏幕录制、把播放列表整理成笔记），值得装上。
- 纯音频无画面、要实时分析、无字幕且不想配 Whisper key 的场景不太适合：纯音频直接用转录工具更省；实时流式不是它的路线；超长视频建议分段处理。
- 上手顺序：先 `balanced` 快速过一遍，哪段值得细看再切 `token-burner` 精看。