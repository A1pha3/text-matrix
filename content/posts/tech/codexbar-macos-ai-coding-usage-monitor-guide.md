---
title: "CodexBar：把 57 家 AI 编程服务的 quota 和重置时间塞进 macOS 菜单栏的小工具"
date: "2026-07-07T03:00:17+08:00"
slug: "codexbar-macos-ai-coding-usage-monitor-guide"
description: "CodexBar（steipete/CodexBar，MIT）是一个 macOS 14+ 菜单栏小工具，统一显示 Codex / Claude / Cursor / Gemini / Copilot / Grok / ElevenLabs / AWS Bedrock / OpenRouter / LiteLLM 等 57 家 AI 编程服务的 quota、spend、reset countdown。隐私优先（不复用 provider session 之外的任何凭证），支持 CLI + Linux/Windows 集成。"
draft: false
categories: ["技术笔记"]
tags: ["macOS", "Menu Bar", "AI Coding", "Usage Monitor", "CodexBar"]
---

# CodexBar：把 AI 编程服务的 quota 塞进菜单栏

2026 年的 AI 编程用户有个新问题：**我同时用 Codex / Claude / Cursor / Gemini / Copilot / Grok / OpenRouter / LiteLLM / ElevenLabs / MiniMax ... 怎么知道每个服务还剩多少 quota、什么时候 reset、下一次长任务该不该起？** 这就是 CodexBar（steipete/CodexBar，MIT）要解决的问题——一个 macOS 菜单栏小工具，统一监控 57 家 AI 编程服务的 quota、spend 和 reset countdown。

## 它要解决的核心痛点

AI 编程服务 2025–2026 进入"多 provider 混用"时代。一个重度用户典型的一天可能是：

- 早上用 **Codex CLI** 跑长任务（5-hour window）
- 切换到 **Claude Code** 写文档（weekly window）
- 中午用 **Cursor** debug（subscription plan）
- 下午调 **OpenRouter** 跑 gpt-oss（API token 计费）
- 晚上用 **ElevenLabs** 给 demo 加语音（character credits）

**问题**：每个 provider 各自有 web dashboard、各自有 session / weekly / monthly / API spend / credit balance ... 你要同时记 5–10 个窗口的 reset 时间，根本记不住。

**CodexBar 把它做成一个状态栏**：每个 provider 一个图标（或 merge 成一个），鼠标悬停看 usage bar 和 reset countdown，永远不用切 dashboard。

## 支持的 57 家 provider

README 列了一个完整 provider 列表，挑有代表性的几个：

### 主流 coding CLI / IDE

- **Codex** — OAuth API 或本地 Codex CLI + 可选 OpenAI dashboard extras
- **Claude** — OAuth API / 浏览器 cookies / CLI PTY fallback；session + weekly window
- **Cursor** — 浏览器 session cookies 拿 plan + usage + billing reset
- **OpenCode** / **OpenCode Go** — 浏览器 cookies / 本地 SQLite
- **Gemini** — OAuth-backed quota API（不用浏览器 cookies）
- **Copilot** — GitHub device flow + Copilot internal usage API
- **Devin** — Chrome localStorage session 或手动 Bearer token

### 编程 plan 服务

- **z.ai** — API token，5-hour + hourly usage windows
- **MiniMax** — API token / cookie header / 浏览器 cookies
- **Kiro** — CLI usage，monthly + bonus credits
- **Vertex AI** — gcloud OAuth + 本地 Claude 日志
- **Augment** — CLI 或浏览器 cookies
- **Kilo / Kode / Codebuff / Crof / Command Code** — 各种 coding subscription API

### API provider

- **OpenAI** — Admin API key usage/cost graphs
- **OpenRouter** — API token credit-based tracking
- **LiteLLM** — Virtual key + proxy URL 个人/团队预算
- **AWS Bedrock** — Cost Explorer spend + monthly budgets + 可选 CloudWatch Claude activity
- **Grok / GroqCloud** — CLI billing RPC + Prometheus metrics
- **DeepSeek / Moonshot / Mistral / Deepgram / Doubao / StepFun / Poe / Chutes** — 各家 API key tracking

### Voice / Speech

- **ElevenLabs** — character credits + voice slots

每个 provider 都有独立文档（`docs/<provider>.md`），说明它用什么凭证、怎么拿到 quota 数据。

## 关键设计取舍

### 隐私优先：复用 provider session 而不是新认证

CodexBar 的关键设计是**复用你已经登录的 provider session**——它不创建新账户、不存密码、不收集数据。具体来说：

- **Codex**：读你本地的 `~/.codex` config（已经登录过的 CLI）
- **Claude**：读 `~/.claude` config + 可选浏览器 cookies
- **Cursor**：读浏览器 localStorage session
- **OpenAI**：如果已有 Admin API key 就用它，否则 fallback 到 OAuth

这意味着：**只要你之前登录过这个 provider，CodexBar 就能直接看到你的 quota**，不用再走一遍 OAuth flow。

代价是：CodexBar 会要求 Full Disk Access 权限（Safari cookies）、Keychain 访问（Chrome "Safe Storage" key decryption）。README 详细写了为什么需要这些权限、怎么 set-and-forget 避免 macOS 反复弹窗。

### 不存密码 / 不存 API key（除非用户显式 set）

CodexBar 默认**不存**任何凭证——它只读 provider 已经存好的 OAuth token / browser cookies / 本地 config。

唯一例外是用户显式调 `codexbar config set-api-key --provider elevenlabs` 存的 API key——这种 key 存在 `~/.config/codexbar/config.json` 里 with restrictive file permissions（自动 chmod 600）。

### 跨平台：macOS GUI + Linux/Windows CLI

GUI（菜单栏 app）只支持 macOS 14+，但 CLI 在 macOS / Linux / Windows 都有 pre-built binary：

```bash
# macOS (Homebrew)
brew install --cask codexbar

# Linux (Homebrew)
brew install steipete/tap/codexbar

# Arch (AUR)
yay -S codexbar-cli

# 通用：GitHub Releases 下载 tarball
```

CLI 可以拿来做脚本自动化：

```bash
# 列出所有 provider 状态
codexbar config providers

# 启用 / 禁用 provider
codexbar config enable --provider grok
codexbar config disable --provider cursor

# 设置 API key
printf '%s' "$ELEVENLABS_API_KEY" | codexbar config set-api-key --provider elevenlabs --stdin

# 跑本地 cost usage 扫描
codexbar cost --provider codex
codexbar cost --provider claude
codexbar cost --provider both
```

CLI 的存在让 CodexBar 不只是一个 GUI 玩具——你能把它接进脚本、CI、tmux 状态栏（已经有 community 插件：tmux / SketchyBar / waybar / GNOME extension / KDE Plasma widget / Noctalia）。

## 真实使用场景

### 场景 1：避免跑到 quota 0 才发现

```
Claude weekly window: ████████░░ 78% used, resets in 2d 4h
Codex 5-hour window:  ██░░░░░░░░ 19% used, resets in 3h 12m
Cursor:               ██████░░░░ 56% used, resets in 4d
OpenRouter credits:   $12.34 left
```

光看这四行，你就能在启动长任务前判断"现在跑 Claude 还是 Codex"，"今晚 cursor reset 后再跑大任务"。

### 场景 2：管理多个订阅

如果你是 freelancer 给客户做不同项目，每个项目用不同 provider，CodexBar 帮你**全局视角**——不用每次打开 5 个 dashboard。

### 场景 3：开源项目 cost control

如果你在跑一个开源项目，每天用 OpenAI API + Anthropic + ElevenLabs，把 `codexbar cost --provider both` 加进 cron 就能拿到本地 cost 快照，对账用。

## 与同类工具的对比

| 工具 | 平台 | Provider 数 | 类型 |
|------|------|-------------|------|
| **CodexBar** | macOS GUI + 全平台 CLI | 57 | 通用 AI coding 监控 |
| **ccusage** | CLI | 主要 OpenAI 兼容 | cost tracking（CodexBar 灵感来源） |
| **CCT（Claude Code Tracker）** | macOS GUI | 仅 Claude | 单一 provider |
| **OpenAI Dashboard** | Web | 仅 OpenAI | 官方 dashboard |

CodexBar 是当前**唯一一个**同时支持 macOS GUI + 全平台 CLI + 57 个 provider 的 quota monitor。单一 provider 工具有很多，跨 provider 监控没有对手。

## 适用边界

**适合**：

- macOS 14+ 用户
- 同时用 3+ AI 编程服务
- 想在一个菜单栏看所有 quota
- 关心隐私（不希望新工具存自己的 OAuth/API key）
- 想用 CLI 集成进 workflow / tmux / SketchyBar / waybar

**不适合**：

- Windows-only 用户（GUI 不支持，CLI 可以凑合用）
- 只用 1–2 个 provider（overkill）
- Linux-only 不愿意接 waybar / tmux integration 的（GUI 没出 Linux）
- 想监控非 AI 服务（CodexBar 不做 CPU/RAM/网络监控）

## 关键事实

- **仓库**：`steipete/CodexBar`
- **协议**：MIT
- **主语言**：Swift 6.2+（GUI）+ bundled CLI（跨平台）
- **要求**：macOS 14+（Sonoma）
- **灵感来源**：[ccusage](https://github.com/ryoppippi/ccusage)（MIT）的 cost tracking 部分
- **作者**：Peter Steinberger（steipete）—— 同时维护 Trimmy / MCPorter / oracle 等开发者工具
- **状态**：活跃维护，README 写 "May your tokens never run out."

## 同作者的其他工具

CodexBar 作者还维护了几个相邻项目，都值得顺手装：

- **Trimmy** — "Paste once, run once." 把多行 shell snippet 压平，让粘贴到终端直接跑（不会触发中断确认）
- **MCPorter** — TypeScript toolkit + CLI for Model Context Protocol servers
- **oracle** — 调 GPT-5 Pro 配合自定义 context 答疑

这些项目放一起看，作者的清晰方向是：**让 AI 编程工作流的"基础设施层"无感化**——你不需要记每次 Claude 多少 quota、不需要 trim 多行 paste、不需要自己写 MCP server。

## 一句话总结

CodexBar 是当下**唯一一个**把 57 家 AI 编程服务的 quota 塞进 macOS 菜单栏的工具——如果你在多 provider 混用时代已经被"我今天还能跑多少"的问题困扰，CodexBar 是当前摩擦最低的解决方案。