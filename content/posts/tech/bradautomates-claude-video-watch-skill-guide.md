---
title: "claude-video：让 Claude Code / Codex / Cursor 真正'看'懂视频的 /watch skill 完全指南"
date: "2026-07-07T02:59:52+08:00"
lastmod: "2026-10-03"
slug: "bradautomates-claude-video-watch-skill-guide"
github_repo: "bradautomates/claude-video"
source_key: "gh:bradautomates/claude-video"
description: "bradautomates/claude-video 是一个装进 Claude Code、Codex、Cursor 等几十个 Agent Skills 宿主的 /watch 技能：有 Gemini API key 时让 Google 视频模型直接看完整视频，没有就走本地抽帧 + 转写。17.9k stars，MIT 协议，本文拆解双引擎架构、四档 detail 模式、帧预算与 RGB 去重。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Agent Skills"]
---

# claude-video：把视频变成 Agent 能"看"的输入

你让 Claude 读过网页、读过 PDF、读过 GitHub 仓库，但你很少让它真正**看**一个视频——默认它只能拿到标题或一份残缺的自动字幕，屏幕上的图表、代码演示、UI 细节全都丢了。`bradautomates/claude-video`（17,971 stars / MIT，2026-10-03 GitHub API 读数）就是为这个缺口设计的：一个装进 Claude Code、Codex、Cursor、Copilot、Gemini CLI 等几十个 Agent Skills 宿主的 `/watch` 技能，把"看视频"做成一等公民。

它现在有两条工作路线，选哪条取决于你有没有一把免费的 Google API key：

| | **Gemini 引擎**（v0.3.0 起，推荐默认） | **local 引擎** |
|---|---|---|
| 谁在看 | Google 的 `gemini-3.7-flash` 视频模型看完整个视频（含音频） | Agent 自己读抽出的帧 + 带时间戳的转写 |
| 需要 | `GEMINI_API_KEY`（[AI Studio](https://aistudio.google.com/apikey) 免费领） | Python 3.10+、FFmpeg、最新版 yt-dlp；转写另配后端 |
| 数据流向 | YouTube 链接直达 Google；本地文件上传 Files API，答后删除 | 一切发生在你机器上 |
| 适合 | 快速出结果，YouTube 为主 | 隐私敏感素材、无网/内网环境、要帧级证据 |

两条路线共用同一个 `/watch` 入口，由 `--engine auto|gemini|local` 或保存的偏好切换；`auto` 表示解析到 `GEMINI_API_KEY` 就走 Gemini，否则 local。下面先讲怎么装，再拆 local 引擎的细节机制——帧预算、四档 detail、去重——这部分逻辑两版引擎之间没有变过，也是这个项目最值得学的工程设计。

## 安装：按宿主选一条路

claude-video 走 [Agent Skills](https://agentskills.io) 开放标准（Anthropic 发起，SKILL.md + scripts/ 一个文件夹就是一份技能；9router、caveman 这些爆款项目用的同一个格式），所以一份技能能装进所有支持该标准的宿主。装法按你的宿主挑一种：

```bash
# Claude Code（终端内执行，推荐）
/plugin marketplace add bradautomates/claude-video
/plugin install watch@claude-video

# Codex：把这行粘进消息框（桌面版/CLI/IDE 插件通用）
# Use $skill-installer to install the watch skill from:
# https://github.com/bradautomates/claude-video/tree/main/skills/watch

# Cursor / Copilot / OpenCode 等其他宿主（需 Node.js）
npx skills add bradautomates/claude-video -g --skill watch
```

`-g` 装到用户全局（`~/.codex/skills/`、`~/.cursor/skills/` 等），去掉则装进当前项目。`SKILL.md` 用相对路径解析旁边的 `scripts/`，装到哪个宿主行为一致——这是 Agent Skills 格式的设计意图：一份技能，处处可跑。

注意两处边界：

- **Claude Chat 和 Cowork 不支持**（v0.3.2 起 README 明确删除了旧的 claude.ai 网页版手动上传 `watch.skill` 的教程）。Cowork 跑在云端环境里，Gemini key 不跨任务保留，大多数网站也屏蔽那个环境的 yt-dlp 下载。想在 Claude 生态里用，走 Claude Desktop 的 Code 会话、VS Code 插件或终端版 Claude Code。
- **安装不带依赖**。装上的只是说明书和脚本，真正干活要 Python 3.10+、FFmpeg/ffprobe 和最新版 yt-dlp；YouTube 下载还要一个 JS 运行时（macOS 的 brew formula 自带 Deno/EJS）。只打算用 Gemini 引擎看 YouTube 的话，这些都不用装。

首次运行会弹一个两问的设置向导：先问引擎（gemini 还是 local），选 local 再问 detail 默认档和无字幕视频的转写后端。macOS 上缺媒体工具时向导会用 Homebrew 补齐，其他平台打印精确命令；全程不自动用 sudo。

## local 引擎拆解

### 四档 detail：一档换一档的钱

`--detail` 是 local 引擎的核心旋钮，决定抽多少帧、花多少 token：

| Mode | 选帧方式 | Cap | 说明 |
|------|--------|-----|------|
| `transcript` | 不抽帧 | — | 字幕可用时连视频都不下，是最便宜的路线 |
| `efficient` | 关键帧（`-skip_frame nokey`） | 50 | 只解码关键帧，速度快几个量级 |
| `balanced`（默认） | 场景切换检测 | 100 | 全片解码找剪辑点，覆盖最稳 |
| `token-burner` | 场景切换检测 | 不设上限 | 保留全部候选帧，超 250 帧会触发 token 警告 |

这套档位是 v0.2.0 引入的，项目 README 当时对一段 **49:08** 的 YouTube 屏幕录像（1280×720、英文自动字幕、长且基本静止——最难伺候的类型）做过一次完整实测，数字如下。当前 README 已撤下这张表，v0.3.x 对均匀采样和去重实现做过修正，但档位结构、cap 和量级没变，数字仍可当作量级参考：

| Mode | 实测帧数 | 抽帧耗时 | 图像 token 估算 |
|------|--------|---------|----------------|
| `transcript` | 0 | ~4.5 s（一次 yt-dlp 调用，不下视频） | 0（≈26.6k 文本 token） |
| `efficient` | 50 | ~0.5 s | ~9.8k |
| `balanced` | 100 | ~20.9 s | ~19.7k |
| `token-burner` | 116 | ~21.0 s | ~22.8k |

读这组数字有三个前提。第一，**测的是抽帧环节的本地 CPU 耗时**，不含一次性的 ~37 s / 76 MB 下载（三档帧模式共享）；end-to-end 还要加上 Claude 读帧的时间。第二，**token 估算按 Anthropic 的 `(width × height) / 750` 公式**——512px 宽的 720p 帧是 512×288，约 197 token/帧；`--resolution 1024` 大约翻四倍。第三，这只是一个静态屏幕录像的样本，**不能推出高运动视频的表现**——剪辑点多的视频里 token-burner 会保留每一帧，与 balanced 的差距远大于 116 对 100。

两个值得记住的设计：`efficient` 比 scene 模式快约 40×，因为它只重建关键帧、不逐帧扫描找剪辑点——但低运动视频里关键帧可能比剪辑点还多，所以它叫 efficient 是指抽得快，不保证帧少。`token-burner` 与 `balanced` 只在越过 cap 之后分道扬镳：这段测试视频有 116 个剪辑点，balanced 均匀采样到 100，token-burner 全留。

另外别忽略 `transcript` 档——长视频下字幕常常才是大头成本（≈26.6k 文本 token），纯字幕路线最省。

### 帧预算：按时长动态分配

默认档的帧预算跟着视频时长走（`frames.py` 的 `auto_fps`，源码核实）：

| 时长 | 预算 |
|------|------|
| ≤30 s | ~30 帧（每秒约 1 帧） |
| 30 s–1 min | ~40 帧 |
| 1–3 min | ~60 帧 |
| 3–10 min | ~80 帧 |
| >10 min | 封顶 100，打印 "sparse scan" 警告 |

所有档位统一 2 fps 上限。视频超过 10 分钟，固定 cap 摊薄到全片就稀了，正确率明显下滑——README 的建议是改用聚焦窗口：

```bash
/watch video.mp4 --start 2:15 --end 2:45   # 同样的预算投进 30 秒窗口
/watch video.mp4 --detail efficient --max-frames 30
```

聚焦模式有自己更密的预算表（5 秒内窗口按每秒 6 帧计，逐步递减），同样 clamp 在 2 fps。用户话里带时刻（"around 2:30"、"the last 30 seconds"）就该走这条路，远比稀疏扫全片有用。

还有一个补帧机制：Agent 读完转写后，主讲人说"看这里"的时刻可以用 `--timestamps 4:32,7:10` 定点抽帧。这些 cue 帧优先从预算里预留；`--detail transcript` 下它们是唯一的帧来源。注意只有真下载了视频才能补帧——纯字幕的 pass 手里没有像素。

### Frame dedup：16×16 缩略图上的均值差

屏幕录像最浪费钱的场景：画面停在一张幻灯片上 90 秒，抽帧器照样吐出十几张几乎一样的图，每张按独立 image 计费。dedup 默认在所有帧模式上跑（`--no-dedup` 关闭），在帧到达 Claude 之前把重复的丢掉：

1. 一次 `ffmpeg` 调用把所有 JPEG 缩到 16×16 的 **RGB** 缩略图（v0.3.0 起从灰度改为 RGB 三通道，靠颜色区分纯色幻灯片和渐变）。之后是纯标准库 Python，无 numpy/Pillow 依赖。
2. 每帧与**上一个保留帧**算平均逐通道差（0–255 标度）。
3. 差值 ≤ 2.0（`DEDUP_THRESHOLD`，源码常量）判为近重复，丢弃；否则保留并成为新参考帧。
4. 帧预算 cap 在 dedup 之后应用，预算花在不同的帧上。

跟"上一个保留帧"而不是"上一帧"比较，是为了抓缓慢的渐变——帧到帧差永远不超阈值，但累积起来画面早变了。阈值压得很低、量的是逐通道均值而不是结构，所以一行代码改动、终端滚动一行、两张不同底色的纯色幻灯片都能存活。缩略图只有 16×16，细小的代码/文字变化可能漏掉，这种场景该用聚焦窗口或 `--no-dedup`。实现是 fail-open 的：ffmpeg 出错就直接跳过去重，宁可多花 token 也不让抽帧失败。

跑完会有一行报告告诉你砍了多少，形如 `Frames: 6 selected from 14 candidates (… 8 near-duplicates dropped …)`。一直有运动的画面几乎不丢帧，等于白付一次缩略图的钱。

### 转写：字幕优先，四个后端兜底

原生字幕永远是第一来源（同语言手动字幕优先于原语言自动字幕，最多请求一条轨道）。视频真没有字幕——本地文件、部分 TikTok、少数 YouTube 上传——才落到转写后端，首次向导四选一：

| 后端 | 代价 |
|------|------|
| `whisperx`（推荐） | 本地推理，无 API key，音频不出机器。首次装约 1.5 GB 下载，需 3 GB 磁盘 + 8 GB 内存；Apple Silicon macOS 已验证，Linux/Windows 配方未测 |
| `groq` | 云端 `whisper-large-v3`，快且便宜，要 `GROQ_API_KEY` |
| `openai` | 云端 `whisper-1`，要 `OPENAI_API_KEY` |
| `none` | 只要字幕；没字幕就没语音转写 |

选 whisperx 时，安装脚本用 uv 拉起独立的 Python 3.12 环境装 **WhisperX 3.8.6**（默认 small 模型、int8、batch 8），并用两秒静音预热模型缓存——参考测速是 Apple M5 Pro 上 9.6 秒转完 69 秒英语。云端后端有 24 MB 的上传预算，超长音频切块转写再把时间戳拼回源时间，个别块失败会在报告里标出缺失区间，而不是整体失败。

## 谁在用、怎么用最值

README 列过五个真实使用模式：

1. **拆别人的内容**：`/watch https://youtu.be/<viral-video> what hook did they open with?`——爆款的开场结构、广告创意、播客开场，凡是"怎么做的"和"做了什么"一样重要的场景。
2. **从视频里 debug**：`/watch bug-repro.mov what's going wrong?`——不用自己打开录屏，Claude 找出问题出现的那一帧。
3. **总结长视频**：`/watch https://youtu.be/<long-thing> summarize this`——比 2x 速看完还快。
4. **去 hype**：发布会对掉十分钟 intro 和自我吹嘘，只留干货。
5. **系列视频转笔记**：整个课程/频道变成一份份可搜索的摘要笔记。

不适合的场景也明确：

- **Claude Chat / Cowork / 浏览器版**——前述宿主限制。
- **受 DRM 保护的 Netflix/Disney+**——yt-dlp 拿不到加密流。
- **超长视频**——capped 模式过 10 分钟覆盖就稀；`efficient` 全片扫一遍也要 ~9.8k 图像 token，预算先爆的是上下文。

## 与同类工具的边界

claude-video 不是要替代 NotebookLM（后者擅长把长播客做成可对话的总结），也不是 ScreenPipe（后者是常驻录屏 + 上下文回溯）。它的定位更窄：

- **目标宿主**：编程代理（Claude Code/Codex/Cursor/Copilot），不是普通聊天界面。
- **输入形态**：单条 URL 或本地路径，不是常驻索引。
- **输出形态**：Agent 直接基于帧+字幕回答（Gemini 引擎则是转述 Gemini 的带时间戳观察），不落向量库。

窄定位换来的好处是确定性——一次调用一次回答，没有跨会话状态、没有索引同步。代价是不适合反复查询：同一个视频问十次，local 引擎就抽十次帧。要基于一批内部录像建问答库，ScreenPipe 或 NotebookLM 更对路。

## 隐私与数据流向

两种引擎的数据流向完全不同，选之前值得想清楚：

- **Gemini 引擎**：YouTube 链接直接交给 Google；其他 URL 先用 yt-dlp 下载再上传 Google Files API，本地文件同样上传。回答给出后删除上传（删除失败的副本 48 小时内过期）。API key 只作请求头、不写日志。私有视频、内部录像不该走这条路。
- **local 引擎**：下载、抽帧、探测全在你机器上。whisperx 后端音频不出机器；groq/openai 只上传提取出的音频。运行产物在一个一次性工作目录里，`--out-dir` 只删自己建的子目录，不碰你的源文件。
- **认证**：需要登录的私有视频用 `--cookies cookies.txt` 或 `--cookies-from-browser firefox` 显式给凭据，工具不会自动翻你的浏览器会话。

几个高频故障的排查入口（README 排查表的原口径）：

- **403 / 登录挑战**：先把 yt-dlp 升到最新版再重试一次——watch 只支持最新 release，站点一改版旧版就失效（macOS `brew upgrade yt-dlp`）。仍 403 才轮到 cookies 认证。
- **`/watch` 没出现**：确认装的是插件本身而不只是添加了 marketplace；开一个新会话再试。
- **出现两个 watch 技能**：一个宿主只保留一种安装方式，查一下是不是插件和独立技能各装了一份。
- **Gemini 报错**：key 无效、配额、视频被 Google 拒绝（私有/过长/不支持）各有独立错误类别，工具不会自己降级到 local——看类别修因，或手动 `--engine local` 重跑。

## 快速上手

```bash
# 1. 装 skill（Claude Code 终端内）
/plugin marketplace add bradautomates/claude-video
/plugin install watch@claude-video

# 2.（local 引擎）补齐依赖（macOS）
brew install python ffmpeg yt-dlp

# 3. 问第一个问题
# /watch https://youtu.be/<video> what happens at the 2 minute mark?
```

有 Gemini key 就跳过第 2 步——向导里选 gemini，YouTube 链接立刻能看。要保存所有场景切换帧作时间戳参考，加 `--no-dedup`；只要字幕，`--detail transcript` 让它完全不下视频。

## 采用建议

- **YouTube 为主、求快**：领一把免费的 Gemini key，向导选 gemini，完事。代价是视频内容出域。
- **素材不能出机器**：`--engine local` 钉死本地路线，转写选 whisperx，代价是装 1.5 GB 的模型环境和慢一些的首跑。
- **读屏上的字**：`--resolution 1024`，dedup 留着，聚焦窗口配合。
- **还没装**：先从 `transcript` 档试起——不下视频、零依赖，先验证工作流再谈帧。

---

*项目地址：[github.com/bradautomates/claude-video](https://github.com/bradautomates/claude-video)（v0.3.2，2026-09-25 发布；作者 Brad Bonanno）。文中 stars 与版本信息为 2026-10-03 读数。*
