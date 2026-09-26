---
title: "cmux：为 AI 编程代理打造的原生 macOS 终端"
date: "2026-03-28T20:30:00+08:00"
lastmod: "2026-09-22T11:00:00+08:00"
slug: "cmux-ai-terminal-multiplexer"
github_repo: "manaflow-ai/cmux"
source_key: "gh:manaflow-ai/cmux"
aliases:
  - /posts/tech/cmux-ai-terminal-multiplexer/
description: "cmux 是 Manaflow 开源的原生 macOS 终端，基于 libghostty 渲染，为并行运行 AI 编程代理而设计：结构化通知、可编程内置浏览器、SSH 工作区、会话恢复与 Skills 扩展。"
draft: false
categories: ["技术笔记"]
tags: ["终端", "AI编程", "macOS", "开源项目"]
---

# cmux：为 AI 编程代理打造的原生 macOS 终端

> 预计阅读时间：30 分钟 | 难度：⭐⭐⭐

AI 编程代理改变了终端的使用方式：过去一个人开两三个终端窗口就够了，现在一个开发者可能同时挂着五六个 Claude Code、Codex 会话。旧终端解决不了新问题——每个代理都在等你的输入，但你分不清是哪一个在等。本文要解读的 [cmux](https://github.com/manaflow-ai/cmux) 就是冲着这个痛点来的：一个原生 macOS 终端，把"哪个代理需要我"变成一眼可见的信息，再把终端本身变成可以用 CLI 和 socket 编程的底座。

## 学习目标

读完本文，你能够：

1. 说清 cmux 与普通终端、tmux、Warp 的定位差异，判断它是否适合你的工作流
2. 理解 cmux 的通知系统如何把"代理在等待"变成结构化信号
3. 用真实命令完成安装、接通代理通知与远程工作区
4. 评估 cmux 的可编程边界：CLI、socket API 与 cmux-skills 各能做什么

## 目录

- [一句话理解 cmux](#一句话理解-cmux)
- [它解决什么问题](#它解决什么问题)
- [核心数据](#核心数据)
- [系统架构](#系统架构)
- [核心功能](#核心功能)
- [一个任务如何流过 cmux](#一个任务如何流过-cmux)
- [安装与上手](#安装与上手)
- [国际化](#国际化)
- [与同类工具对比](#与同类工具对比)
- [适用边界](#适用边界)
- [常见问题](#常见问题)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [采用建议](#采用建议)
- [参考来源与口径说明](#参考来源与口径说明)

## 一句话理解 cmux

cmux 是 Manaflow 公司开源的原生 macOS 终端，官方定位是"基于 Ghostty 的 macOS 终端，为 AI 编程代理提供垂直标签与通知"。它自带三类能力：

```text
终端基础能力（分屏、标签、GPU 渲染）
    +
代理协作能力（通知环、通知面板、多代理编排、会话恢复）
    +
可编程底座（CLI、Unix socket API、内置浏览器、cmux.json 自定义命令）
```

三条线合起来的效果：你可以同时开任意多个代理会话，谁在等你、谁在跑、谁连着哪个 PR，侧栏和通知面板直接告诉你；而这一切都可以被脚本驱动。

## 它解决什么问题

cmux 的作者在 README 的"Why cmux?"一节写过动机：他并行跑大量 Claude Code 和 Codex 会话，用 Ghostty 加一堆分屏凑合，靠 macOS 系统通知判断代理状态。问题是 Claude Code 的通知正文永远是一句"Claude is waiting for your input"，没有上下文；标签一多，连标题都认不全。他也试过几个编码编排器（coding orchestrator），但多数是 Electron 或 Tauri 应用，性能不行，而且 GUI 编排器会把人锁进它们规定的工作流。

cmux 的取舍因此很清楚：

| 痛点 | cmux 的做法 |
|------|-------------|
| 通知没有上下文，分不清哪个代理在等 | pane 出蓝色圆环，侧栏标签点亮，通知面板汇总所有待处理项 |
| GUI 编排器性能差、锁工作流 | 原生 Swift + AppKit 应用，不规定用法，只给原语 |
| 标签多了认不出谁是谁 | 侧栏垂直标签直接显示 git 分支、关联 PR 状态与编号、工作目录、监听端口、最新通知文本 |
| 代理跑在后台看不见 | 代理派生的 subagent 和 teammates 变成原生分屏，而不是隐藏的后台进程 |

官方博客把这套哲学叫"The Zen of cmux"：cmux 是原语（primitive），不是解决方案。它给你终端、浏览器、通知、工作区、分屏和一个 CLI，怎么组合是你自己的事。

## 核心数据

以下数据取自 GitHub API，时点为 2026-09-22：

| 指标 | 数值 |
|------|------|
| GitHub Stars | 27,308 |
| Forks | 2,384 |
| 提交数 | 15,736 |
| 标签数 | 200 |
| 发布版本 | 59 个，最新 v0.64.25（2026-09-17） |
| 仓库创建 | 2026-01-28 |
| 许可证 | GPL-3.0-or-later |
| 平台 | macOS |

从创建到本文核查时不到八个月，Star 从零涨到 2.7 万，提交保持高频节奏——nightly 版每日从最新 main 提交自动构建。这个体量在终端类工具里已经不算小众。

## 系统架构

cmux 是原生 macOS 应用，渲染层和业务层的分工如下：

| 层 | 技术 | 说明 |
|----|------|------|
| 终端渲染 | libghostty | Ghostty 的渲染库，GPU 加速。cmux 不是 Ghostty 的 fork，而是像应用使用 WebKit 那样把 libghostty 当库用 |
| 应用框架 | Swift + AppKit | 原生 macOS 体验，官方强调非 Electron，启动快、内存低 |
| 远程守护进程 | Go | 仓库 `daemon/remote` 目录，支撑远程连接相关能力 |
| 可编程接口 | CLI + Unix socket | 创建工作区、开分屏、发送按键、读屏幕内容、截图、驱动浏览器 |

一个容易混淆的点：Ghostty 是独立的终端模拟器应用，cmux 是构建在其渲染引擎之上的另一个应用。你的 Ghostty 配置（`~/.config/ghostty/config`）里的主题、字体、颜色会被 cmux 直接读取沿用，终端键位也来自这份配置；cmux 自己的快捷键（工作区、分屏、浏览器、通知）则在 Settings 里定制。

## 核心功能

### 通知系统：cmux 的招牌

这是 cmux 区别于普通终端的第一功能。代理需要关注时，标准终端转义序列（OSC 9/99/777）会自动触发通知：对应 pane 出现蓝色圆环，侧栏标签点亮，同时弹出通知面板条目和 macOS 桌面通知。

任何支持 hooks 或 OSC 序列的代理都能接入，包括 Claude Code、Codex、OpenCode 和 pi。你也可以用 `cmux notify` 命令手动触发，把它挂进代理的 hooks 配置。按 `Cmd+Shift+U` 直接跳到最新的未读通知。

通知面板支持已读/未读管理：`Cmd+I` 打开面板，`Option+Cmd+U` 切换当前条目的未读状态。

### 工作区、标签与分屏

cmux 的界面组织分三层：工作区（workspace）、表面（surface）、分屏（pane）。侧栏是垂直标签的主入口，每个工作区显示的元数据前面已经列过——git 分支、PR 状态、工作目录、监听端口、最新通知，这些信息让"认标签"不再依赖标题文字。

常用快捷键（完整列表见官方文档，均可在 Settings 中自定义）：

| 快捷键 | 动作 |
|--------|------|
| `Cmd+N` | 新建工作区 |
| `Cmd+T` | 新建表面（标签页） |
| `Cmd+D` | 向右分屏 |
| `Cmd+Shift+D` | 向下分屏 |
| `Cmd+B` | 切换侧栏 |
| `Cmd+Shift+U` | 跳到最新未读通知 |
| `Cmd+Shift+L` | 在分屏中打开内置浏览器 |
| `Cmd+Shift+O` | 重新打开上次的会话 |

### 内置浏览器

cmux 内置了一个可分屏的真实浏览器，API 移植自 Vercel 的 [agent-browser](https://github.com/vercel-labs/agent-browser) 项目：导航、抓取 DOM 快照、点击、输入、执行 JavaScript、读取控制台和网络活动，全部通过同一个 socket API 暴露。

它的设计意图是让代理自证工作成果：把浏览器 pane 分在终端旁边，Claude Code 可以直接操作你的开发服务器，改完前端自己点一遍验证，不用离开 cmux。浏览器还支持从 Chrome、Firefox、Arc 等 20 多种浏览器导入 cookie、历史和会话，让浏览器 pane 一打开就是已登录状态。

### SSH 与远程工作区

```bash
# 为远程机器创建工作区
cmux ssh user@remote

# 建工作区时在首个远程终端里跑一条初始命令
cmux ssh user@remote --command 'omp "investigate auth"'
```

远程工作区不是简单地把 SSH 会话塞进一个标签：浏览器 pane 的流量走远程网络，所以访问远程机器上的 localhost 服务就像在本地一样；把图片拖进远程会话，会通过 scp 上传。cmux 还能原生 attach 到远程机器上已有的 tmux 会话（beta 功能），所以"代理跑在远程主机、你在本地 cmux 里驾驶"是一条被官方支持的路径。

### 多代理并行与编排

cmux 对代理没有任何白名单限制——它是终端，凡是能在命令行启动的代理都开箱即用：Claude Code、Codex、OpenCode、Gemini CLI、Kiro、Aider、Goose、Amp、Cline、Cursor Agent 等。README 里的原话是"所有（All of them）"。

两个编排集成值得关注：

- **Claude Code Teams**：`cmux claude-teams` 一条命令跑 Claude Code 的 teammate 模式， teammates 直接生成为原生分屏，带侧栏元数据和通知，不需要 tmux。
- **oh-my-opencode**：多模型编排支持，运行中的每个代理都可见、可控制。

### 会话恢复

退出 cmux 时会保存当前会话，重新打开时恢复窗口/工作区/分屏布局、工作目录、终端回滚缓冲（尽力而为）和浏览器 URL 与导航历史。

需要说清楚的边界：cmux 恢复的是应用自身状态，不做任意活进程的检查点——普通终端进程、vim、shell 重开后还是普通终端。要让代理会话跨退出、崩溃、升级后恢复，需要装 hooks：

```bash
cmux hooks setup              # 安装它能找到的所有受支持代理
cmux hooks setup codex        # 指定某个代理
cmux hooks setup --agent opencode
```

受支持的会话恢复集成覆盖 13 个代理：Claude Code、Codex、Grok、OpenCode、Pi、Amp、Cursor CLI、Gemini、Rovo Dev、Copilot、CodeBuddy、Factory、Qoder。hooks 保存会话 ID 后，重开时代理终端可以恢复到原会话；敏感环境变量（token、密码、密钥）在保存恢复绑定前会被剥离。

如果需要活进程级的分离重连（detach/reattach），可以启用内置的本地 tmux：`cmux local-tmux`。本地 tmux 服务器扛不住注销、重启和断电，那种场景官方建议用 `cmux ssh-tmux`、`cmux mosh-tmux` 或持久云虚拟机。

### 可编程性与 Skills

cmux 的每个动作都能通过 CLI 和 Unix socket 完成：创建工作区、开分屏、发送输入、读屏幕、截图、驱动浏览器。项目级的自定义动作写在 `cmux.json` 里，从命令面板启动。

Skills 方面，Manaflow 维护了一个公开仓库 [cmux-skills](https://github.com/manaflow-ai/cmux-skills)，提供 9 个遵循 Agent Skills 规范的技能，供任何支持 `.agents/skills/` 或 `.claude/skills/` 约定的代理使用：

```bash
# 全局安装全部技能
npx skills add manaflow-ai/cmux-skills -g --all

# 只装两个、只给 Claude Code 用
npx skills add manaflow-ai/cmux-skills --skill cmux-cli cmux-config --agent claude-code
```

9 个技能覆盖 CLI 参考（`cmux-cli`）、配置（`cmux-config`）、浏览器驱动（`cmux-browser`）、工作区操作（`cmux-workspace`）、云虚拟机（`cmux-cloud`）、侧栏自定义视图构建（`cmux-sidebar-builder`）等。装上之后，代理就拿到了操作 cmux 本身的说明书——这正是"把终端变成可编程底座"的落地形式。

## 一个任务如何流过 cmux

把前面所有机制串成一个真实场景：你同时派三个 Claude Code 会话去修一个带前端界面的 bug。

1. `Cmd+N` 建一个工作区，`Cmd+D` 分三个 pane，分别启动 claude。侧栏立刻显示每个会话的 git 分支和工作目录，谁在哪条分支上一目了然。
2. 你切去干别的。第一个代理读完代码需要你确认方案，它发出的 OSC 序列让它的 pane 亮起蓝环，侧栏标签同步点亮。
3. 按 `Cmd+Shift+U`，直接跳到那个 pane，确认方案后代理继续。
4. 代理改完前端要在本地验证。你按 `Cmd+Shift+L` 分一个浏览器 pane 出来，代理通过 socket API 对页面做 DOM 快照、点击、填表，自己确认修复生效，全程你看得到。
5. 中途 cmux 提示有更新要重启。重启后布局、工作目录、回滚缓冲原样恢复；因为装过 `cmux hooks setup`，三个 claude 会话各自恢复到原来的对话状态，不是重新开三个空终端。
6. 其中一个修复必须在内网测试机上验证。`cmux ssh user@testbox` 开一个远程工作区，代理在远程主机上跑，浏览器 pane 走远程网络直接访问测试机的 localhost。

六个步骤里没有一步依赖 cmux 规定的工作流——每一步都是原语的组合，这就是官方所说"原语而非解决方案"的具体含义。

## 安装与上手

两种安装方式（macOS）：

```bash
# Homebrew（README 口径：先添加 tap，再装 cask）
brew tap manaflow-ai/cmux
brew install --cask cmux

# 之后升级
brew upgrade --cask cmux
```

也可以从 [Releases 页面](https://github.com/manaflow-ai/cmux/releases)下载 DMG，拖进 Applications 即可。DMG 版通过 Sparkle 自动更新，只需下载一次。追新的用户可以装 [Nightly 版](https://github.com/manaflow-ai/cmux/releases/download/nightly/cmux-nightly-macos.dmg)，它是独立应用（独立 bundle ID），可以和稳定版共存。

首次启动如果 macOS 提示确认打开已认证开发者的应用，点"打开"即可。装完建议做三件事：

1. 如果你本来就是 Ghostty 用户，什么都不用配——主题、字体、颜色自动沿用；
2. 跑一次 `cmux hooks setup`，把常用代理的会话恢复接上；
3. 按 `Cmd+B` 打开侧栏，习惯从垂直标签里读分支、PR 和通知信息。

## 国际化

cmux 的 README 提供 20 种语言版本，包括简体中文（`README.zh-CN.md`）、繁体中文、日语、韩语、德语、法语、西班牙语、俄语、阿拉伯语、越南语、泰语、土耳其语、波兰语、乌克兰语、高棉语等，从仓库根目录可以直接索引。

## 与同类工具对比

| 项目 | Stars* | 定位 | 与 cmux 的关系 |
|------|--------|------|----------------|
| [tmux](https://github.com/tmux/tmux) | 49,415 | 跑在任何终端里的复用器 | 互补：cmux 可 attach 远程 tmux 会话；活进程分离重连也可借助 local-tmux |
| [Ghostty](https://github.com/ghostty-org/ghostty) | 61,413 | 跨平台终端模拟器 | 上下游：cmux 用 libghostty 渲染，沿用其配置；Ghostty 是独立应用而非 fork 对象 |
| [Warp](https://github.com/warpdotdev/warp) | 65,119 | Agentic 开发环境 | 竞品方向：同样服务代理工作流，但 Warp 是带自家 UI 与 AI 的一体化产品，cmux 是不规定工作流的原生终端 |
| [iTerm2](https://github.com/gnachman/iTerm2) | 18,084 | 老牌 macOS 终端 | 同赛道前辈：功能成熟，但没有面向代理的通知与可编程浏览器 |

\* Stars 为 2026-09-22 的 GitHub API 数值，仅用于体量参考。

两点值得展开。其一，cmux 与 tmux 不是替代关系：tmux 是任何终端里都能跑的复用器，靠前缀键和配置文件工作；cmux 是 GUI 原生应用，垂直标签、分屏、浏览器、socket API 全部内置，不需要配置文件和前缀键。官方 FAQ 也承认很多人同时用两者——cmux 加 SSH 加 tmux 是被明确支持的组合。其二，Warp 在 2025 年开源了客户端（AGPL-3.0），已经不是一个"专有闭源产品"，把它简单归为"闭源竞品"的旧印象需要更新；它和 cmux 的真正分歧在工作流哲学——Warp 提供一体化的代理开发环境，cmux 提供原语让你自己搭。

## 适用边界

| 场景 | 适配度 | 说明 |
|------|--------|------|
| 并行运行多个 AI 编程代理 | 高 | 通知系统就是为此设计 |
| 前端代理开发（代理要自己验证界面） | 高 | 内置浏览器 + socket API 是稀缺能力 |
| 远程服务器上的代理任务 | 高 | SSH 工作区 + 远程 tmux attach |
| 已有深度定制的 tmux 工作流 | 中 | 可以共存，但迁移动力取决于你对通知和浏览器的需求 |
| 轻量复用需求、脚本化服务器环境 | 低 | tmux 仍是更合适的工具 |
| Linux / Windows | 暂不支持 | 官方口径"macOS only, for now"；另有 iOS app 处于 beta（TestFlight，随 Founders Edition 提供早鸟资格） |

## 常见问题

**cmux 和 Ghostty 是什么关系？**
不是 fork。cmux 把 libghostty 当渲染库用，就像应用用 WebKit 渲染网页。Ghostty 是独立终端，cmux 是构建在其渲染引擎之上的另一个应用，主题、字体、颜色配置直接沿用。

**要花钱吗？**
cmux 免费开源，许可证是 GPL-3.0-or-later。组织无法遵守 GPL 时，可以就 Manaflow 掌握权利的部分洽谈商业条款（第三方贡献不在其列，细节见仓库 LICENSE 文件）。另有付费的 Founders Edition，购买者获得优先功能响应和 cmux AI、iOS 应用、Cloud VM、语音模式等新功能的早期访问。

**它和 tmux 怎么选？**
要 GUI、通知、内置浏览器、可编程 API，选 cmux；要在任何终端、任何服务器上获得轻量复用，选 tmux。两者可以一起用：cmux 原生支持 attach 远程 tmux 会话。

**Skills 和仓库里 `skills/` 目录是什么关系？**
给用户装的是 [cmux-skills](https://github.com/manaflow-ai/cmux-skills) 仓库的 9 个技能；cmux 主仓库 `skills/` 目录下那批 `cmux-*` 技能是开发者开发 cmux 本身时用的，不是给终端用户的扩展，不要混淆。

## 自测题

用这份清单检验理解程度：

**基础概念**

- [ ] 能说清 cmux 与 Ghostty 的关系（库的使用者，还是 fork？）
- [ ] 能解释 cmux 通知系统为什么比系统通知更有效（OSC 序列、蓝环、侧栏元数据各起了什么作用）
- [ ] 能复述"The Zen of cmux"里"原语而非解决方案"的取舍

**配置与使用**

- [ ] 能完成安装并说明 DMG 与 Homebrew 两种方式的差别（自动更新机制）
- [ ] 能用 `cmux hooks setup` 接通至少一个代理的会话恢复，并说清它恢复不了什么（活进程）
- [ ] 能用 `cmux ssh` 建一个远程工作区，并解释浏览器 pane 为什么能访问远程 localhost

**决策与对比**

- [ ] 能为"多代理并行开发"和"服务器运维"两个场景分别判断 cmux 是否合适
- [ ] 能对比 cmux、tmux、Warp 三者的定位边界与组合方式
- [ ] 能判断自己的工作流里，cmux 的哪些原语有用、哪些用不上

## 进阶路径

**第一步：跑起来（1 天内）**

安装后把 Ghostty 配置（如果有）接上，用 `Cmd+D`/`Cmd+Shift+D` 练分屏，开两个代理会话观察通知环与 `Cmd+Shift+U` 的跳转。

**第二步：接入工作流（1 周）**

- 跑 `cmux hooks setup`，验证代理会话的跨重启恢复
- 在 `cmux.json` 里定义一个项目自定义命令，从命令面板启动
- 用 `cmux ssh` 接管一台远程开发机，体验浏览器走远程网络
- 装 cmux-skills 里的 `cmux-cli` 和 `cmux-browser`，让代理自己操作 cmux

**第三步：深度定制（长期）**

- 用 CLI + socket API 写自动化脚本：批量建工作区、定时截图、驱动浏览器做巡检
- 按 Agent Skills 规范写自己的 cmux 技能
- 需要"活进程跨更新存活"的组合时，研究 `cmux local-tmux` 的生命周期与边界（见仓库 `docs/local-tmux.md`）

## 采用建议

按读者类型给结论：

- **每天并行跑多个编码代理的 macOS 用户**：直接装，通知系统几乎无学习成本，收益立现。
- **前端开发者**：内置浏览器 + 代理自验证的组合值得专门花时间配置，这是目前同类终端里少有的能力。
- **重度 tmux 用户**：不必迁移，先试用 cmux 加远程 tmux attach 的组合，让通知系统为现有工作流补位。
- **Linux/Windows 用户、纯服务器环境**：暂时无缘，关注仓库进展即可。
- **对 GPL 许可敏感的企业**：接入前先评估合规义务，必要时联系 Manaflow 谈商业条款。

## 参考来源与口径说明

- 仓库数据（Stars、Forks、提交数、标签、发布版本、语言构成、创建时间）：GitHub API，时点 2026-09-22；文章初版发布于 2026-03-28，当时数据与现在差异较大，本文统一按核查时点刷新。
- 功能与机制描述：仓库 `README.md`（main 分支，2026-09-22 版），包括安装方式、快捷键、SSH 工作区、Claude Code Teams、会话恢复、FAQ 与 Founders Edition 条款；快捷键以 README 的 Keyboard Shortcuts 一节为准。
- 许可证口径：仓库 LICENSE 文件与 README 均声明 GPL-3.0-or-later（版权方 Manaflow, Inc.）；GitHub API 因 LICENSE 为自定义文本将其归类为"其他/未标注"，以仓库声明为准。
- Skills 清单：[manaflow-ai/cmux-skills](https://github.com/manaflow-ai/cmux-skills) 仓库 README 与 skills 目录（2026-09-22，9 个技能）。
- 对比项目数据：tmux、Ghostty、Warp、iTerm2 各自的 GitHub 仓库 API（2026-09-22）；Warp 开源状态见 warpdotdev/warp 仓库的 AGPL-3.0 许可证。
- 安装命令：README 的 Install 一节；Homebrew 官方 cask 仓库已收录 cmux（formulae.brew.sh，版本与 GitHub 最新 release 同步）。
- 官网与文档：[cmux.com](https://cmux.com)（旧域名 cmux.dev 会 301 跳转至此），文档入口 [cmux.com/docs](https://cmux.com/docs/getting-started)，设计哲学见官方博客 [The Zen of cmux](https://cmux.com/blog/zen-of-cmux)。
- 初版文章将 cmux 描述为"内置 Claude API 的终端"并列出若干不存在的命令与环境变量，与本轮核查的仓库事实不符，已整体修正；文章初版发布后由 `tech/` 目录迁入 `tech/ai-agent/`，aliases 保留旧路径。
