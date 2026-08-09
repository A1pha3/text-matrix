---
title: "Orca：让多个 AI 编程 Agent 并行跑在同一张桌面上的编排器"
date: 2026-08-10T03:35:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["orca", "ai-agent", "parallel-agents", "developer-tools", "open-source"]
description: "Orca 是一个开源桌面应用，将 Claude Code、Codex、Cursor 等命令行 AI 编程代理统一编排到隔离的 git worktree 中并行执行，配合移动端伴侣、SSH 远程工作树和差异标注审查，覆盖从多代理竞速到远程运维的完整工作流。"
github_repo: "stablyai/orca"
source_key: "gh:stablyai/orca"
slug : index

---

## 它解决什么问题

AI 编程代理（coding agent）正在从单兵作战走向多代理协作。一个典型场景：你有一个功能需求，想同时让 Claude Code 和 Codex 各写一版，比较结果后合并更好的那个。手动操作的话，你需要开两个终端、切两个分支、分别粘贴 prompt、再逐个 diff——每次都这样来回，摩擦感很大。

Orca（[stablyai/orca](https://github.com/stablyai/orca)）把这套流程收进一个桌面应用。核心能力是 **parallel worktree**：一条 prompt 扇出到 N 个代理，每个代理跑在独立的 git worktree 里，互不干扰；结果在同一个界面里横向对比，选中最佳的合并即可。

## 核心架构

Orca 不是一个代理框架，而是一个 **编排层**（orchestrator）。它不替代 Claude Code 或 Codex，而是在它们之上提供并行隔离、统一监控和差异审查。

### 系统地图

| 层 | 职责 | 具体实现 |
|---|---|---|
| **代理层** | 实际执行编码任务 | Claude Code、Codex、Grok、Cursor、Copilot、OpenCode 等任意 CLI 代理 |
| **隔离层** | 每个代理跑在独立 worktree | git worktree，文件系统级隔离 |
| **终端层** | 每个代理拥有独立终端 | WebGL 渲染的 Ghostty 级终端，支持无限分屏 |
| **编辑器层** | VS Code 编辑器内嵌 | 文件浏览、拖拽文件到代理 prompt、Markdown 预览 |
| **编排层** | 代理间对比、标注、合并 | 差异视图、行级批注、worktree 切换 |
| **远程层** | SSH 远程工作树 | 自动重连 + 端口转发，代理在远程机器上跑 |
| **通知层** | 移动端伴侣 | iOS/Android app，代理完成后推送通知 |

### 并行 worktree 机制

这是 Orca 的核心。一条 prompt 发出后，Orca 为每个代理创建一个 git worktree（不是分支，是工作树——同一仓库的多个检出目录），代理在各自的 worktree 里操作文件，互不影响。完成后，你在 Orca 的差异视图里对比各代理的输出，逐行审查后合并到主分支。

这个设计的关键在于：代理之间 **不需要知道彼此的存在**。每个代理看到的是一个完整的 git 仓库，只是工作目录不同。没有锁竞争，没有合并冲突的运行时开销。

## 关键能力

### 移动端伴侣

Orca 提供独立移动端 app（[iOS App Store](https://apps.apple.com/us/app/orca-ide/id6766130217)、Android APK），代理跑完会推通知到手机，你可以在路上发后续指令。这不是远程桌面——是一个轻量的任务监控和对话界面。

### SSH 远程工作树

如果你的本地机器算力不够（比如需要跑大模型推理的代理），可以把 worktree 挂到远程服务器上。Orca 通过 SSH 连接远程机器，文件编辑、git 操作和终端全都在远程执行，断线自动重连。这对 "本地写代码 + 远程跑代理" 的工作流非常有用。

### Design Mode

Orca 内嵌了一个真实的 Chromium 窗口。你点击页面上的任何 UI 元素，它的 HTML、CSS 和截图会直接注入代理的 prompt。这比手动截图 + 描述 UI 问题高效得多——代理拿到的是结构化数据，不是模糊的自然语言描述。

### 差异标注与审查

代理生成的 diff 可以逐行标注——在任意行上打评论，发给代理让它修改。审查、编辑、提交全在 Orca 内完成，不需要切到外部 diff 工具。

### GitHub 与 Linear 原生集成

直接在 Orca 里浏览 PR、Issue 和 Linear 项目看板，从任务卡开一个 worktree 开始干活。这消除了任务跟踪工具和编辑器之间的上下文切换。

### Orca CLI

代理自己也可以驱动 Orca。`orca worktree create`、`orca snapshot`、`orca click`、`orca fill` 等命令让代理能脚本化整个工作流——比如一个代理创建 worktree、跑测试、截图、填充表单。

## 安装

### 桌面端（macOS / Windows / Linux）

```bash
# macOS (Homebrew)
brew install --cask stablyai/orca/orca
```

或直接下载：

- [macOS Apple Silicon](https://github.com/stablyai/orca/releases/latest/download/orca-macos-arm64.dmg)
- [macOS Intel](https://github.com/stablyai/orca/releases/latest/download/orca-macos-x64.dmg)
- [Windows (.exe)](https://github.com/stablyai/orca/releases/latest/download/orca-windows-setup.exe)
- [Linux AppImage](https://github.com/stablyai/orca/releases/latest/download/orca-linux.AppImage)

### 移动端

- iOS：[App Store](https://apps.apple.com/us/app/orca-ide/id6766130217) 或 [TestFlight](https://testflight.apple.com/join/YjeGMQBA)
- Android：[APK 下载](https://github.com/stablyai/orca/releases/download/mobile-android-v0.0.37/app-release.apk)

## 支持的代理

Orca 的代理兼容性很宽——只要能在终端里跑的 CLI 代理都支持。目前经过测试的包括：

Claude Code、Codex、Grok、Cursor、GitHub Copilot、OpenCode、Pi、Amp、Goose、Cline、Continue、Droid、Kimi、Qwen Code、Devin 等 30+ 种。这个列表在持续扩展，核心逻辑很简单：终端能跑，Orca 就能编排。

## 适用边界

### 适合

- 需要同时跑多个代理做 A/B 对比
- 团队使用不同代理（Claude Code + Codex），想要统一界面
- 需要远程 SSH 跑代理但想本地监控
- 需要 Design Mode 做 UI 驱动的编码
- 想在手机上监控代理进度

### 不适合

- 只用一个代理且不需要并行——Orca 的编排能力在这里没有增量价值
- 需要 IDE 级别的深度代码理解——Orca 的编辑器是 VS Code 级别，但它不是 IntelliJ
- 团队需要 CI/CD pipeline 编排——Orca 编排的是人机交互式代理，不是 CI 流水线

## 项目数据

| 指标 | 数值 |
|---|---|
| Stars | ~40,700 |
| Forks | ~2,860 |
| 主语言 | TypeScript |
| 许可证 | MIT |
| 最新版本 | v1.4.177（2026-08-08） |
| 更新频率 | 日级（每日发布） |

## 判断

Orca 解决的问题真实存在：AI 代理从单兵到多兵的编排摩擦。它的 parallel worktree 隔离设计简洁有效，不侵入代理本身，降低了采用门槛。移动端伴侣和 SSH 远程工作树扩展了使用场景，Design Mode 是 UI 驱动开发的实用创新。

局限在于它是一个桌面应用（Electron 架构），资源占用不低；如果只使用单一代理，额外的编排层未必值得。对于已经在使用多个 CLI 代理、或者想要 A/B 对比代理输出质量的开发者，Orca 值得一试。
