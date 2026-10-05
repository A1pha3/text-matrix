---
title: "tuios：一个知道你的 Agent 在干什么的终端窗口管理器"
description: "tuios 是用 Go 写的终端复用器与平铺式窗口管理器，基于 Charm 技术栈，内置 Agent 状态感知、统一收件箱与多机会话同步。本文拆解它的 Agent 可观测性设计、BSP 平铺模型与事件驱动渲染架构，并给出上手路径与适用边界。"
date: 2026-10-06T03:25:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["tuios", "terminal", "Go", "agent", "开发工具"]
github_repo: "Gaurav-Gosain/tuios"
source_key: "gh:Gaurav-Gosain/tuios"
slug : tuios-agent-aware-terminal-window-manager
---

## 核心判断

当编码 Agent（Claude Code、Codex、Gemini CLI……）成为终端里的常驻进程，传统终端复用器暴露出一个结构性缺陷：**它们管理的是「窗格」，而不知道窗格里的进程是什么、处于什么状态**。你开了六个窗格跑六个 Agent，哪个在等审批、哪个已经跑完、哪个报错了——tmux 一概不知，你只能逐个窗格肉眼巡视。

tuios（Terminal UI Operating System）针对的正是这个缺口。它是一个用 Go 编写的终端复用器加平铺式窗口管理器，核心理念写在 README 第一句：**a terminal window manager that knows what your agents are doing**。它把 Agent 状态做成了窗口管理器的一等公民：每个窗格的标题栏显示其中 Agent 的工作/等待/完成/出错状态，所有会话、所有机器上等待你处理的事项汇总进一个统一收件箱（Inbox）。

这不是又一个 tmux 皮肤换色。它值得关注的点在于：**把「多 Agent 并行开发」从口令技巧变成了窗口管理器的原生职责**。项目约 4,800 stars，v0.8.5 发布于 2026 年 10 月 2 日，最近提交在 2026 年 10 月 5 日，处于活跃迭代期。

## 系统地图

先给一张总览，tuios 的能力可以切成四层：

| 层 | 能力 | 对应的 tmux 概念 |
|----|------|-----------------|
| 窗口管理 | BSP 平铺、9 工作区、vim 模态键位、命令面板 | 布局与快捷键 |
| 终端仿真 | 内置 VT 仿真器（或可选 libghostty-vt 后端）、kitty 图形协议、Sixel | 无（依赖外层终端） |
| 会话持久化 | daemon 模式、断线重连、会话复活、跨机器 attach | server/session 模型 |
| Agent 层 | 状态上报、Inbox、Agent 间消息、fan-out 舰队、权限授予 | **无对应** |

前三层是「把 tmux + 平铺式窗口管理器 + 图形协议支持做扎实」，第四层才是差异化的部分。下文重点拆第四层，前三层只讲关键取舍。

## Agent 层：状态、收件箱、舰队

### 状态上报的两种来源

tuios 对 Agent 的感知不依赖各 Agent 厂商的配合：

- **集成上报**：`tuios integration install` 为 19 种 Agent 线束（harness，指 Claude Code、Codex、Gemini CLI、opencode 等）安装挂钩，让它们主动报告状态；
- **进程探测**：对未安装集成的场景，tuios 通过进程信息与屏幕内容识别 24 种 Agent CLI，尽力推断状态。

双来源设计是务实的选择：状态上报这种能力，等所有厂商统一标准是不现实的，先用启发式兜底、再让愿意配合的线束更精确，是合理的渐进路径。

### Inbox：把审批从「同步阻塞」变成「队列处理」

`Prefix+i` 打开收件箱，列出所有会话、所有机器上等待你的事项：审批请求、问题、错误、完成的回合。`Prefix+o` 直接跳到最旧的一条。审批可以在收件箱里直接应答，不必切到对应窗格；对 Claude Code、opencode、Kilo、Qwen Code 的权限请求，配置 `[agents.approvals]` 后可以一键应答。

这个交互模型改变的是人的工作方式：从「盯着 Agent」变成「批量处理待办」。当你并行运行多个 Agent 时，这是注意力管理上的实质改进，而不是锦上添花。

### Agent 间通信与舰队

- `tuios ask-human`：Agent 向人类提一个带固定选项的问题，进 Inbox；
- `tuios send-agent-message` / `ask-agent`：Agent 之间互发消息、互相提问。设计上避免了「往一个正在等待提示符的窗格里盲打字」这一经典事故，来自人类的回复会被标记为已验证；
- `tuios fan`：把同一个提示词分发到多个 Agent（可混用不同线束），每个 Agent 各自跑在独立的 git worktree 里——这是并行探索式开发（同一任务多种实现路线赛马）的直接支持；
- **Pane Grants**：按窗格声明 Agent 可通过 tuios 做什么（`read` / `write` / `fan` / `respond` / `admin`），给辅助 Agent 的权限可以比主 Agent 更少；
- **MCP Server**：`tuios mcp` 把同样的能力以 MCP 工具形式暴露，默认只读、且限定在 Agent 自己的会话内。

### tmux Shim

`tuios tmux-shim` 让那些依赖 tmux 做编排的工具（README 点名 Claude Code agent teams）在 tuios 上运行，它们的 tmux 窗格被映射为 tuios 窗格。生态兼容层的存在说明作者清楚：迁移成本是这类工具最大的敌人。

## 窗口管理与终端仿真：几个值得记的取舍

**模态界面**。借 vim 的思路：窗格管理操作（新建、切换、缩放）在 Window Management 模式下单键完成；进入终端交互时切到 Terminal 模式。这回避了 tmux「prefix 键 + 组合键」的记忆负担，代价是多一层模式概念。

**BSP 平铺**。二叉空间分割树（Binary Space Partitioning）配螺旋布局与预选区（preselection，指定下一个窗格从哪里分出来），另有 master-stack 与 niri 风格的滚动列布局可选。这是平铺式窗口管理器（i3、BSPWM）的成熟做法移植到终端内部。

**事件驱动渲染**。PTY 读取 goroutine 通过缓冲 channel 通知 Bubble Tea 渲染，没有固定频率的轮询 tick——README 明确宣称空闲时 CPU 占用为零。这对长时间挂机的多 Agent 场景是有意义的指标。

**kitty 图形协议直通**。图像 ID 跨帧复用做到无闪烁的视频播放（`mpv --vo=kitty` 可用），配合 mode 2026 同步输出防撕裂。终端里看图看视频仍是小众需求，但无闪烁直通的技术含量不低，也解释了为什么作者提供一个基于 libghostty-vt 仿真器后端的构建变体。

**多机会话**。`tuios hosts add` 通过 SSH 接入其它机器，远程会话可以直接画在本地客户端里；全局会话（`--global`）可以把多台机器上的窗格聚在一个会话内；Agent 也可以跑到别的机器上，其 Inbox 条目回流到本地。对「本地开发 + 远程算力」的工作流，这是完整的覆盖。

## 快速上手

```bash
# macOS / Linux
brew install tuios

# 或快速安装脚本
curl -fsSL https://raw.githubusercontent.com/Gaurav-Gosain/tuios/main/install.sh | bash

# 启动（挂到 daemon，会话存活于终端窗口之外）
tuios

# 不想装，先在浏览器里体验（WASM 构建）
# https://tuios.dev/learn
```

关键键位（prefix 默认 `Ctrl+B`）：

- `Ctrl+P`：命令面板，模糊搜索所有动作——记不住键位时的万能出口
- WM 模式下 `n`：新窗格；`z`：缩放当前窗格
- `Prefix+i`：打开 Inbox
- `Prefix+[`：vim 风格复制模式
- `Prefix+S`：会话切换器

跑 Agent 前先装集成：`tuios integration install`。给窗格里的 Agent 看 `tuios --skill` 输出的简短指南，它就知道怎么驱动 tuios 了。

不想引入 daemon 时可以 `tuios --standalone` 单次运行。

## 适用边界

- **项目仍在 0.x 阶段**（v0.8.5，2026 年 10 月），API 与配置格式可能变动，生产环境的日常重度使用前建议先在次要场景试运行一两周；
- 构建需要 Go 1.26.6+；完整体验（图形协议等）依赖 Ghostty、Kitty、WezTerm 这类现代终端；
- 如果你的工作流是「一个终端窗口一个 Agent、逐个照看」，tuios 的核心价值兑现不了——它的收益与并行 Agent 数量正相关；
- tmux 深度用户注意：配置体系是 TOML 而非 tmux.conf，键位习惯需要重新建立（shim 只解决工具兼容，不迁移你的肌肉记忆）。

## 结语

tuios 对「终端里跑 Agent」这个新常态的回应是认真的：不是给 tmux 加个状态脚本，而是把 Agent 可观测性、审批路由、跨机协同做进窗口管理器的内核里。四千八百颗星说明需求真实。即便你暂不迁移，它的 Inbox 与 Pane Grants 设计也值得任何多 Agent 编排工具借鉴——**当窗格里的进程会自己思考，窗口管理器就必须理解进程的意图**。

仓库：[Gaurav-Gosain/tuios](https://github.com/Gaurav-Gosain/tuios)，文档站 [tuios.dev](https://tuios.dev)，MIT 协议。
