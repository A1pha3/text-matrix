---
title: "nodeterm：把终端和 AI Agent 摊开在一张无限画布上"
date: "2026-08-23T03:22:00+08:00"
slug: nodeterm-node-based-terminal-manager
github_repo: "eneskirca/nodeterm"
source_key: "gh:eneskirca/nodeterm"
description: "nodeterm 是基于 Electron + tmux 的节点式终端管理器，把真实终端、AI Agent、便签、编辑器、diff 都做成可拖拽的节点，铺在一张可缩放平移的无限画布上，同一个项目还能切换成看板视图。本文解析其架构分层与三种使用形态。"
draft: false
categories: ["技术笔记"]
tags: ["终端", "AI Agent", "tmux", "Electron", "效率工具"]
---

# nodeterm：把终端和 AI Agent 摊开在一张无限画布上

## 核心判断

终端工具的传统形态是**堆叠的标签页**——开着十几个 tab，你根本记不清哪个 shell 在哪个 tab 里跑什么。nodeterm 换了一个心智模型：把每个终端、每个 AI Agent 会话都变成画布上一个可拖拽、可分组、可缩放的**节点**，让「上下文在空间上的位置」成为记忆的一部分。它的定位坦白直接：给「注意力分散、工作流散乱」的人，一个空间化的终端管理器。

项目约 1000+ stars，TypeScript + Electron 实现，活跃开发（最新 release v0.3.2 发布于 2026-08-17，最近提交 2026-08-20）。授权为 BUSL-1.1（Business Source License）：可自由使用、修改、再分发，甚至生产使用，唯一禁止的是把它作为与 nodeterm 竞争的独立产品或服务出售；每个 release 在发布四年后自动变为 MIT。

## 三句话理解它做什么

1. **一切皆节点**：右键画布可开终端或 AI Agent，每个都跑在自己的持久化 tmux 会话里；旁边还能放便签（可链接给 agent 当上下文）、Monaco 编辑器、diff 视图、web/video 节点。退出应用甚至重启机器，会话都回来。
2. **一个项目，两种视图**：每个项目既是画布，也是一块看板——看板上的卡片就是你的**活会话**，agent 还在跑也能拖卡换列，打开卡片进入带成员、截止日期、优先级、评论的实时会话模态框。`⌘⇧B` 切换。
3. **会话跟着你走**：手机扫一个 QR 配对，同一批活会话在 iOS 上继续；同一套画布也能自托管到浏览器（Server Edition），从任何地方访问。

## 系统地图：一个 codebase，三个 shell

nodeterm 最值得看的工程点是它的**服务接缝（service seam）**设计——同一套核心服务，通过不同的「外壳」运行，UI 几乎不变：

| 层面 | 实现 | 职责 |
|------|------|------|
| `src/main` | Electron 主进程 | 桌面壳 |
| `src/preload` | 唯一桥（`window.nodeTerminal`） | IPC 通道 |
| `src/renderer` | React UI | 画布渲染 |
| `src/core` | `CorePlatform` 接缝 | 全部服务：PTY、工作区、git、agent、hooks |
| `src/server` | WebSocket-RPC 桥 | 浏览器 Server Edition |

关键抽象是 **`TerminalTransport`**：renderer 只依赖这个接口，从不直接碰 IPC 或 node-pty。`LocalTransport` 连接本机，`RemoteTransport` 通过 SSH 连远端——所以远端项目（SSH）接入时，画布 UI 完全不用改。React Flow 是画布节点的唯一事实源，项目把序列化节点持久化到磁盘，tmux 保证会话跨重启存活。

## Agent 体验：不靠输出抓取，靠钩子驱动

nodeterm 对 AI Agent 的处理方式值得一提——它的状态上报是**钩子驱动**的，不做终端输出抓取：

- 运行中 / 需要你：**RUNNING / NEEDS YOU** 徽章脉冲，OS 通知提醒
- 子代理卡：带实时转录的卡片，还有每节点上下文仪表
- 点击徽章直接在节点里回答权限提示，turn 结束时被明确告知
- MacBook 上 agent 还会出现在「刘海」里

Agent 类型覆盖 Claude Code / Codex / Gemini / GitHub Copilot / opencode / Grok / 自定义。高级能力包括：agent 节点之间按需互读转录的**上下文链接**；Claude 专属的对话分支与多账号管理；agent 能通过内置的 canvas-control CLI 驱动画布（开节点、起团队、互相验证工作）。

## 其它值得一提的设计

- **自带 tmux**：macOS 应用捆绑自己的 tmux，无需预装；系统已有 tmux 时优先用系统的。机器重启后恢复滚动缓冲并续上 agent 会话（`claude --resume`）
- **免提终端**：按住 `⌘⌥` 说话，端侧 Whisper 本地转录，确认后再发送，语音不出机器
- **GitHub Issues 看板**：可选的 issue 卡片，标签到列的精确映射，双向移动/关闭/重开同步
- **防睡眠**：agent 工作时阻止机器进入空闲休眠，任务结束即放开；合盖无法保持唤醒，过夜运行建议 Server Edition
- **Server Edition 双用途**：浏览器里的完整画布；以及装在任何 SSH Linux 主机上的 headless 通知宿主——手机收 RUNNING / NEEDS YOU 推送，零开放端口（钩子服务只监听 loopback，推送走 HTTPS）

## 采用建议与边界

- **适合**：同时开着多个 agent 会话、希望「看得见任务在哪儿」的人；远程 SSH 主机上跑 agent、想被及时叫醒的人
- **上手**：macOS 可 `brew tap nodeterm/tap && brew trust nodeterm/tap && brew install --cask nodeterm`（前两条缺一不可，Homebrew ≥6 不信任的 tap 会直接失败）；Linux 用 AppImage 或 .deb
- **边界**：桌面端目前以 macOS / Linux x64 为主，Windows 支持在建（bootstrap-windows.bat 已在仓库）；BUSL-1.1 授权在「以竞争性方式再分发/托管」上受限，商业化前应读 LICENSE 全文；项目迭代快，API/配置可能变动

本文聚焦架构分层与三种使用形态（桌面 / Server Edition / 移动），不展开具体节点的实现源码。
