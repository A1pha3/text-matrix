---
title: "nodeterm：把终端和 AI Agent 摊开在一张无限画布上"
date: "2026-08-23T03:22:00+08:00"
lastmod: "2026-10-01T00:00:00+08:00"
slug: nodeterm-node-based-terminal-manager
github_repo: "eneskirca/nodeterm"
source_key: "gh:eneskirca/nodeterm"
description: "nodeterm 是基于 Electron + tmux 的节点式终端管理器：真实终端、AI Agent、便签、编辑器、diff 都是可拖拽的节点，铺在一张可缩放平移的无限画布上，同一个项目还能切换成看板视图。本文解析其架构分层、一次任务如何流过系统，以及一个多月里从 v0.3.2 到 v0.4.0 的演进。"
draft: false
categories: ["技术笔记"]
tags: ["终端", "AI Agent", "tmux", "Electron", "效率工具"]
---

# nodeterm：把终端和 AI Agent 摊开在一张无限画布上

## 核心判断

终端工具的默认形态是堆叠的标签页——开着十几个 tab，你记不清哪个 shell 在哪个 tab 里跑什么。nodeterm 换了一个心智模型：每个终端、每个 AI Agent 会话都是画布上一个可拖拽、可分组、可缩放的**节点**，「上下文在空间上的位置」本身就是记忆的一部分。README 把目标用户写得很直白：给 ADHD 和工作流散乱的人，一个空间化的终端管理器。

这个项目只有三个多月大（仓库 2026-06-15 创建），但迭代速度少见：截至 2026-10-01 已发布 65 个 release，9 月 23 日一天连发五个（v0.3.9 到 v0.3.13），9 月 30 日的 v0.4.0 把看板从"视图"升级成了"调度器"。TypeScript + Electron 实现，1,920 stars，授权 BUSL-1.1——可以自由使用、修改、再分发，包括生产使用；唯一禁止的是把它作为与 nodeterm 竞争的产品或服务对外提供（托管、内嵌或独立出售都算）；每个 release 发布四年后自动转为 MIT。

## 三句话理解它做什么

1. **一切皆节点**。右键画布开终端或 AI Agent，各自跑在独立的持久化 tmux 会话里；旁边可以放便签（可链接给 agent 当上下文）、Monaco 编辑器、diff 视图、web/video 节点。退出应用甚至重启机器，会话都回来。
2. **一个项目，两种视图**。每个项目既是画布，也是一块看板（`⌘⇧B` 切换）——看板上的卡片就是活会话，agent 还在跑也能拖卡换列，点开卡片进入带成员、截止日期、优先级、评论的实时会话模态框。v0.4.0 之后看板还能反向调度：把 GitHub issue 卡拖进 dispatch 列，就会启动一次 agent 运行。
3. **会话跟着你走**。手机扫一个 QR 配对，同一批活会话在 iOS 上继续，端到端加密走中继，不限于同一局域网；同一套画布也能自托管到浏览器（Server Edition），从任何地方访问。

## 系统地图：一个 codebase，多个外壳

nodeterm 最值得看的工程点是它的**服务接缝（service seam）**——同一套核心服务跑在不同的「外壳」里，UI 几乎不变：

| 位置 | 实现 | 职责 |
|------|------|------|
| `src/main` | Electron 主进程 | 桌面壳 |
| `src/preload` | 唯一桥（`window.nodeTerminal`） | IPC 通道 |
| `src/renderer` | React UI | 画布渲染 |
| `src/shared` | 类型与 IPC 通道名 | 三个上下文共用 |
| `src/core` | `CorePlatform` 接缝 | 全部服务：PTY、工作区、git、agent、hooks |
| `src/server` | WebSocket-RPC 桥 | 浏览器 Server Edition |
| `src/session-host` | 独立会话宿主 | Windows（无 tmux）的会话存续，打包中 |

`src/core` 里的服务从不 import `electron`——Electron 只是 `CorePlatform` 这个接缝的一种实现，浏览器 Server Edition 是另一种。这是"一套代码、一个 renderer、多个外壳"能成立的前提。

关于终端会话层，有一处 README 和代码对不上的地方，值得展开。README 的架构节写：renderer 只依赖 `TerminalTransport` 接口，`LocalTransport` 连本机、`RemoteTransport` 走 SSH 连远端。接口本身确实存在，renderer 也确实不直接碰 IPC 或 node-pty；但翻开源码，`transport.ts` 的注释明确写着——实现只有 `LocalTransport` 一个，远程访问的做法是"换掉 api 对象，而不是换掉 transport"：本地会话的 api 是 preload，远端标签页的 api 是中继隧道上的 WebSocket 桥（`src/renderer/bridge` 在浏览器里填同一个 `window.nodeTerminal`）。换句话说，「远端项目接入时画布 UI 完全不用改」这个结论成立，但机制不是两个 transport 类，而是同一条接口后面换数据源。README 的 `RemoteTransport` 说法是文档滞后于代码，读代码时以注释为准。

画布这边，React Flow 是活节点的唯一事实源，项目把序列化的节点持久化到磁盘，tmux 保证会话跨重启存活。

## Agent 体验：不抓输出，靠钩子

nodeterm 对 AI Agent 的状态上报是**钩子驱动**的，不做终端输出抓取：

- 运行中 / 需要你：**RUNNING / NEEDS YOU** 徽章脉冲，OS 通知提醒
- 子代理卡：带实时转录，每个节点有上下文仪表
- 点击徽章直接在节点里回答权限提示，turn 结束时被明确告知
- MacBook 上 agent 还会出现在「刘海」里

支持的 agent：Claude Code / Codex / Antigravity / Gemini / GitHub Copilot / opencode / Grok / 自定义。高级能力包括：agent 节点之间按需互读转录的**上下文链接**；Claude 专属的对话分支与多账号管理；agent 能通过内置的 canvas-control CLI 驱动画布——开节点、起团队、互相验证工作。

## 一次修复任务怎么流过这套系统

把抽象机制串起来看：假设你让一个 Claude Code 节点修一个 bug。

1. 右键画布新建 agent 节点，任务在它自己的 tmux 会话里跑；你把旁边的便签链接给它当上下文，继续在别的节点干活。
2. agent 停下来要权限时，徽章从 RUNNING 跳成 NEEDS YOU 并脉冲，macOS 通知和刘海同时提醒；你点开节点，在徽章上直接批准。
3. turn 结束你收到明确通知。想换脑子，按 `⌘⇧B` 把画布切成看板，把这张卡拖到「进行中」旁边的列——agent 没停，卡只是换个位置。v0.4.0 起你甚至可以直接把对应的 GitHub issue 卡拖进 dispatch 列重新发起一轮。
4. 合上笔记本去吃饭：agent 跑着的时候 nodeterm 会阻止机器空闲休眠，结束后放开；但合盖谁也保不住唤醒，过夜任务要么开着盖接着电源，要么把 agent 放到一台不睡觉的机器上跑 Server Edition。
5. 走到楼下，手机扫码配对过，同一个会话在 iOS 上还在跑——看它干活、回答"needs you"、或者干脆在手机上敲命令。
6. 晚上机器重启装更新，第二天打开 nodeterm：滚动缓冲恢复，agent 会话经 `claude --resume` 续上，画布还是你摆的样子。

这套流程里没有一步需要你记"刚才那个 shell 在哪"——空间位置、看板列、手机推送，都是找回调任务的线索。

## 其它值得一提的设计

- **自带 tmux**：macOS 应用捆绑自己的 tmux，无需预装；系统已有 tmux 时优先用系统的。从源码跑则要自己装，或用 `scripts/build-tmux.mjs` 现编一个。
- **免提终端**：按住 `⌘⌥` 说话，松手后端侧 Whisper 本地转录，文字打进终端提示符——**你自己**按 Enter，没有任何自动提交；语音不出机器。
- **GitHub Issues 看板**：可选的 issue 卡片，标签到列的精确映射，双向移动/关闭/重开同步。
- **Server Edition 双用途**：浏览器里的完整画布（单用户密码认证）；以及装在任何 SSH Linux 主机上的 headless 通知宿主——手机收 RUNNING / NEEDS YOU 推送，零开放端口（钩子服务只监听 loopback，推送走 HTTPS）。
- **退出成本低**：官方卸载脚本先 `--dry-run` 列出它找到的一切，再执行清理——停掉它启动的进程、撤掉合并进 agent CLI 配置的状态钩子（你自己的钩子和凭据不动）、删除它自己的状态。你仓库里的 `.nodeterm/` 画布文件夹会保留。

## 采用建议与边界

- **适合**：同时开着多个 agent 会话、想"看得见任务在哪儿"的人；远程主机上跑 agent、想被及时叫醒的人。作者自己给它的定位（服务 ADHD 人群）在同类工具里少见地诚实——如果你没有上下文管理痛点，标签页也够用。
- **上手**：macOS 可 `brew tap nodeterm/tap && brew trust nodeterm/tap && brew install --cask nodeterm`（前两条缺一不可，Homebrew ≥6 不信任的 tap 直接失败；应用自带更新，`brew upgrade` 很少需要）。Linux (x64) 用自更新 AppImage、.deb 或 .rpm（Fedora 装 AppImage 需先 `sudo dnf install fuse-libs`）。Windows (x64) 已进入 beta：有按用户安装的 Setup.exe 和便携 zip，但安装包未签名（SmartScreen 会拦）、更新手动、跨重启会话存续还在落地——Windows 没有 tmux，替代它的独立会话宿主正在打包（PR #579）。iOS 在 App Store 搜 nodeterm。
- **边界**：授权是 BUSL-1.1，受限点只在「以竞争方式对外提供」（托管、内嵌、独立出售）；拿它管理自己的终端和 agent 完全自由，商业化集成前读一遍 LICENSE 全文，商用授权联系作者。项目一天能发五个版，API 和配置变动是常态，出问题先看 release notes 再翻 issue。

从 v0.3.2（本文初稿时的最新版）到 v0.4.0，一个多月里看板学会了调度 agent、Antigravity 加入了支持列表、团队可以由 Server Edition core 托管（邀请码加入，跑会话的机器不再需要开着桌面应用）。这个节奏下，具体功能清单会很快过时，真正稳定的反而是那两条接缝——`CorePlatform` 和 `TerminalTransport`——以及"会话必须活着等你回来"这个产品执念。
