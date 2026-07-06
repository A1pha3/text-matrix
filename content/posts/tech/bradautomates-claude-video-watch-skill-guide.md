---
title: "claude-video：让 Claude Code / Codex / Cursor 真正'看'懂视频的 /watch skill 完全指南"
date: "2026-07-07T02:59:52+08:00"
slug: "bradautomates-claude-video-watch-skill-guide"
description: "bradautomates/claude-video 是一个面向 50+ AI 编程代理的 Agent Skill，提供 /watch 指令把 YouTube/Loom/本地视频喂给 Claude：自动下载、抽帧、ASR 转写、让 Claude 真正看图听音后回答。4k stars，MIT 协议，本文拆解四档 detail 模式、frame dedup 与 token 预算权衡。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Agent Skills", "视频理解", "yt-dlp"]
---

# claude-video：把视频变成 Claude 能"看"的输入

你让 Claude 读过网页、读过 PDF、读过 GitHub 仓库，但你很少让它真正**看**一个视频——因为默认它只能拿到标题或者一份残缺的自动字幕。本文要拆解的 `bradautomates/claude-video`（4,075 stars / MIT）就是为这个缺口设计的：它不是另一个 ASR 工具，而是一个装进 Claude Code、Codex、Cursor、Copilot、Gemini CLI 等 50 多个 Agent Skills 宿主里的 `/watch` 技能，把"看视频"做成一等公民。

## 它解决的是什么问题

Claude 默认拿到一个 YouTube 链接，只有三种回答方式：

1. **根据标题猜**——经常完全偏离。
2. **抓 transcript 文本**——但自动字幕经常漏 90% 屏幕上的内容（图表、代码演示、UI 细节、镜头切换）。
3. **拒绝回答**——因为不在训练数据里。

`/watch` 的做法是把它当作一个多模态输入问题来解决：下载视频 → 抽帧 → 提取带时间戳的音频转写 → 把帧和转写一起 `Read` 进 Claude 的上下文。Claude 看到的就是**真实的画面**和**真实的音频**，回答方式就和一个真人看完视频之后回答问题没有区别。

## 安装方式：一行命令覆盖 50+ 宿主

claude-video 走的是 [Agent Skills](https://agentskills.io) 协议（和 9router、9arm、agency-agents、caveman 等用的同一个开放标准），所以一份 `SKILL.md` 加上 `scripts/` 子目录就能装到任何支持该协议的宿主：

```bash
# Claude Code（推荐）
/plugin marketplace add bradautomates/claude-video
/plugin install watch@claude-video

# Codex / Cursor / Copilot / Gemini CLI / +50 宿主
npx skills add bradautomates/claude-video -g

# claude.ai web（手动）
# 1. 在 Releases 下载 watch.skill
# 2. Settings → Capabilities → Skills → +
# 3. 需要先启用 "Code execution and file creation"
```

`-g` 表示装到全局（`~/.codex/skills/`、`~/.cursor/skills/` 等），不加 `-g` 装到当前项目。`SKILL.md` 里的脚本路径是用相对路径解析的，所以同一份 skill 装在哪个宿主里都能跑——这是 Agent Skills 协议的核心卖点：**一份 skill，所有宿主**。

首次运行时会自动通过 `brew`（macOS）装 `yt-dlp` 和 `ffmpeg`，其他平台会打印精确命令让你手动装。Whisper API key **只在视频没有字幕时**才需要。

## 四档 detail 模式：trade 时间换视觉精度

claude-video 的核心抽象是 `--detail` 这个 dial，决定调用方愿意花多少时间下载视频 + 花多少 token 让 Claude 看：

| Mode | Engine | Frames | Cap | Extraction time | Est. image tokens |
|------|--------|--------|-----|-----------------|-------------------|
| `transcript` | yt-dlp 字幕 | 0 | — | ~4.5s（不下视频） | 0（≈26.6k 文本 token） |
| `efficient` | keyframe only | 50 | 50 | ~0.5s | ~9.8k |
| `balanced` | scene-change | 100 | 100 | ~20.9s | ~19.7k |
| `token-burner` | scene-change | 116 | uncapped | ~21.0s | ~22.8k |

数字来自对一个真实 49:08 YouTube 视频（1280×720、英文自动字幕、长且静态的屏幕录像）的实测。`transcript` 模式只走字幕，根本不下视频，是最便宜的；`efficient` 只解关键帧所以快 40×；`balanced` 和 `token-burner` 都做场景切换检测，但 token-burner 不打上限，会把所有候选帧都保留。

**几个值得记住的点：**

- 默认 frame 是 512px 宽，clamp 到 1998px 高——这个尺寸是 Anthropic `Read` 工具能直接当 image 渲染的最大边界。
- 默认帧预算是按视频时长动态调的：30 秒以内 ~30 帧，30s–1min ~40 帧，1–3min ~60 帧，3–10min ~80 帧，超过 10 分钟 cap 在 100（除非用 `token-burner`）。
- 用户只要指明时间段（"around 2:30", "the last 30 seconds"），就用 `--start` / `--end` 走 Focused 模式——同样的预算投到更小的时间窗口里，每秒帧密度翻倍，远比稀疏地扫整个视频有用。

## Frame dedup：纯 stdlib 的低算力去重

抽帧再多也没用——一段 90 秒的屏幕录像，画面可能一直停在同一张幻灯片上，结果抽出十几张几乎一样的帧，每张都按独立 image 计费。claude-video 的 dedup 默认在所有 frame 模式上跑，关掉用 `--no-dedup`：

1. 用一次 `ffmpeg` 把每个 JPEG 缩到 16×16 灰度图。后续是纯 stdlib Python，没有 numpy/Pillow 依赖。
2. 对每帧，计算它和**上一个保留帧**的**平均绝对差**（0–255 scale 的亮度差）。
3. 差值 ≤ 2.0 就丢；否则保留，并把它作为新的参考帧。
4. Frame budget cap 在 dedup **之后**应用，所以预算花在不同帧上。

对比"上一个保留帧"而不是"上一帧"是为了抓缓慢的渐变（slow fade）——帧到帧差永远不超阈值，但累积起来就重复了。阈值定得很低、用亮度差而不是结构差，所以"一行代码改动""终端滚一行""两张纯色幻灯片"都能被识别成不同。

实测在 always-moving 视频上 dedup 几乎不丢帧（开销忽略），在静态视频上能砍掉一半以上重复帧。输出里会有一行 `Frames: 6 selected from 14 candidates (… 8 near-duplicates dropped …)` 告诉你砍了多少。

## 谁在用、怎么用最值

README 列了 5 个真实使用模式：

1. **分析别人的内容**：`/watch https://youtu.be/<viral-video> what hook did they open with?`——拆爆款视频的开场结构。
2. **从视频里 debug**：`/watch bug-repro.mov what's going wrong?`——不用自己打开视频，Claude 找出现 bug 的那一帧。
3. **总结长视频**：`/watch https://youtu.be/<long-thing> summarize this`——比 2x 速看还快。
4. **去 hype**：补 launch 视频只挑干货，跳过十分钟 intro 和自我吹嘘。
5. **系列视频转笔记**：`/watch ... summarize this to a note` —— 把整个课程/频道变成可搜索的笔记库。

但也有**不适合**的场景：

- 实时直播（没结束就没法 yt-dlp 抓）
- 受 DRM 保护的 Netflix/Disney+（协议层 block）
- 真的非常长（>1 小时）的视频——`efficient` 模式扫一遍也要 9.8k image tokens，预算会爆

## 与同类工具的边界

claude-video 不是要替代 NotebookLM（后者擅长做长 podcast 的可对话总结）、也不是 ScreenPipe（后者是常驻录屏 + 上下文回溯）。它的定位更窄：

- **目标宿主**：编程代理（Claude Code/Codex/Cursor/Copilot），不是普通聊天界面。
- **输入形态**：单条 URL 或本地路径，不是常驻索引。
- **输出形态**：Claude 直接基于帧+字幕回答，不是存到向量库。

这个定位的好处是**确定性**——一次调用得到一次回答，没有跨会话的状态、没有索引同步、没有 retention 策略。但坏处是**不适合反复查询**——同一个视频你问十次，它会抽十次帧。如果你的场景是"我要基于一批内部录像建一个问答库"，那 ScreenPipe 或 NotebookLM 更合适。

## 快速上手三步

```bash
# 1. 装 skill
npx skills add bradautomates/claude-video -g

# 2. 装系统依赖（macOS）
brew install yt-dlp ffmpeg

# 3. 在 Claude Code 里
/watch https://youtu.be/<video> what happens at the 2 minute mark?
```

如果你想关掉自动 dedup（比如要保存所有场景切换用作时间戳参考），加 `--no-dedup`；如果你只要字幕加对话，加 `--detail transcript` 让它完全不下视频。

## 适用边界

- **真要看图**：必须用 frame 模式，至少 `efficient`，否则 Claude 只读字幕就退化回文本模型。
- **不在乎视觉**：用 `transcript` 模式，省 100% image token。
- **生产自动化**：可以 `claude -p "/watch <url> <question>"` 直接喂脚本——claude-video 的脚本入口是无 TTY 的。
- **隐私**：视频和帧会被下载到本地临时目录，结束任务时 Claude 会清理；不要用 `transcript` 之外的模式处理敏感内部录像。