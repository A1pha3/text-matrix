---
title: "Orca：让多个 AI 编程 Agent 并行跑在同一张桌面上的编排器"
date: 2026-08-10T03:35:00+08:00
lastmod: 2026-10-03T00:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["orca", "ai-agent", "parallel-agents", "developer-tools", "open-source"]
description: "Orca 是 Stably AI 开源的桌面编排器：把 Claude Code、Codex 等 CLI 代理扇出到隔离的 git worktree 并行执行，本地、SSH、自建服务器、按需云虚拟机四种运行模式承接算力，配合移动端伴侣与开源 relay 覆盖远程监控。本文梳理其架构、CLI 机制与适用边界。"
github_repo: "stablyai/orca"
source_key: "gh:stablyai/orca"
slug: "orca-parallel-ai-agent-orchestrator"
---

> 本文初版发表于 2026-08-10（v1.4.177 时点）；2026-10-03 对照仓库 main 分支、v1.4.219 release 与官方文档全面修订。Orca 处于日更节奏，具体命令与界面以 [官方 changelog](https://github.com/stablyai/orca/releases) 为准。

## 它解决什么问题

让多个 AI 编程代理并行干活，想法不新，难的是工程细节：每个代理要独立的检出目录，输出要能横向对比，代理跑完要有人审查，审查意见要能送回去改，人不在电脑前还得知道进度。这些环节任何一处靠手工衔接，并行的收益就被摩擦吃掉了。

Orca（[stablyai/orca](https://github.com/stablyai/orca)）把这整条链路收进一个桌面应用。核心机制是 **worktree-native**：官方文档的原话是"不再在一个检出上反复分支和 stash，每个任务通过 git worktree 拿到仓库自己的磁盘副本"。一条 prompt 可以扇出到 N 个代理，各自在独立 worktree 里干活，结果在同一界面横向对比，选中赢家合并即可。

开发商 Stably AI 是 YC 孵化的旧金山团队。仓库 2026 年 3 月 17 日创建，8 月中旬约 4.2 万星，10 月初已到 8.4 万——增速本身说明"多代理编排"这个位置正变得拥挤而重要。官方对它的定位也一直在换措辞：README 标语叫 "The AI Orchestrator for 100x builders"，仓库描述改称 "ADE（agent development environment）"，package.json 里写的是 "Next-gen IDE for parallel agentic development"。三个说法指向同一件事：它不做模型，也不替代代理，做的是代理之上那一层。

## 系统地图

| 层 | 职责 | 具体实现 |
|---|---|---|
| **代理层** | 实际执行编码任务 | Claude Code、Codex、Cursor、Grok 等 CLI 代理，靠自己的订阅运行 |
| **隔离层** | 每个任务独立工作区 | git worktree，文件系统级隔离，可用原生 git 直接操作 |
| **界面层** | 终端、编辑器、差异审查 | xterm WebGL 终端、Monaco 编辑器、内嵌 Chromium 浏览器、diff 标注 |
| **运行模式** | 决定文件和代理在哪台机器上 | 本地桌面 / SSH 主机 / 自建 Orca 服务器 / 按工作区拉起的云虚拟机 |
| **移动层** | 手机监控与跟进 | iOS/Android 伴侣 app，配对流量走仓库内开源的 relay |
| **自动化层** | 让代理反过来驱动 Orca | orca CLI：worktree、终端、文件、内嵌浏览器全可脚本化 |

前两层是设计上的亮点，后面几层是两个月里快速长出来的：SSH、服务器模式、移动端在文章初版时已在，云虚拟机模式、relay 开源、Computer Use 则是此后陆续补充的。

## 核心机制

### worktree 隔离：代理之间不需要知道彼此存在

一条 prompt 扇出后，Orca 为每个代理创建一个 git worktree——不是分支，是同一仓库的多个检出目录。代理在各自的目录里操作文件，互不影响；完成后在差异视图里对比，逐行审查后合并。

这个设计的关键是每个代理看到的都是一个完整的 git 仓库，只是工作目录不同。没有锁竞争，也没有运行时的合并开销。官方在文档里专门划了边界：Orca "不是 git 的替代品"，每个 worktree 都是真实的 git worktree，你随时可以 `cd` 进去用原生 git。这带来一个实际的可逆性保证——就算哪天不用 Orca 了，磁盘上留下的只是普通的 worktree 和分支，`git worktree remove` 就能清理干净。

### 四种运行模式：算力放在哪台机器上

这是初版文章漏掉的框架。SSH 远程只是 Orca 四种运行方式之一，官方在 "Ways to run Orca" 里给出的完整地图是：

| 模式 | 文件和代理在哪 | 机器归谁 | 适合 |
|---|---|---|---|
| 本地桌面 | 你的电脑 | 你 | 日常编码，快速迭代 |
| SSH target | 通过 SSH 连接的远程主机 | 你或团队 | 开发机、GPU 机器、常开的 VPS |
| Remote Orca Server | 跑着 Orca 桌面版或 `orca serve` 的机器 | 你或团队 | 常驻共享运行时、移动端、自动化 |
| Cloud VM | 每个工作区一个一次性 VM 或沙箱 | 你自己的云账号（自带 provider） | 隔离、用完即弃的代理算力 |

两条硬边界值得注意：SSH 模式下代理和 git 在远端跑，编辑器、diff 和 UI 留在本地，断线自动重连、端口转发官方明说是内置的；同时 Orca **不卖托管 VPS**——远程模式永远用你自己控制的机器和云账号。这意味着采用 Orca 不会把你的代码引入一个第三方托管环境，代价则是远程模式需要自己备机器。

`orca serve` 是服务器模式的入口：前台启动一个不带桌面窗口的运行时，官方为无头 Linux 服务器单独写了部署指南。

### 移动端与 relay：配对服务端也是开源的

移动端伴侣（iOS App Store、Android APK）做的不是远程桌面，而是一套轻量的任务监控：代理跑完推送通知，你在路上看进度、发后续指令、把卡住的 worktree 解开。

有意思的是服务端。手机和桌面从不直接通信——各自向 relay 的一个 cell 发起 outbound WebSocket，relay 把两个会话配对后在中间拼接帧；一个 director 组件负责把主机分配到 cell、协调迁移。这套 relay（连同持有 APNs key 的推送网关）2026 年 8 月之后整体开源进了仓库的 `cloud/` 目录，文章初版时它还不在。几个细节能看出设计的认真程度：推送网关用桌面主机与 relay 相同的 X25519 密钥应答加密挑战换取 24 小时会话，手机上永远不持有 Orca 凭据；日志只写聚合计数器，token、通知标题、正文和完整主机指纹不进任何一行日志。

### Design Mode：把 UI 元素变成结构化上下文

Orca 内嵌一个真实的 Chromium 窗口。打开 Design Mode 后点击页面上的任何 UI 元素，它的 DOM、计算样式（computed styles）和裁剪后的元素截图会直接注入代理的 prompt。这解决了"改 UI"场景的上下文传递问题——代理拿到的是精确的结构化数据，而不是一张整页截图加一段人肉描述。

### 差异审查：标注可以送回代理

代理生成的 diff 可以逐行评论，评论打包发回代理修改；审查、编辑、提交都可以不离开 Orca。集成面上除了 GitHub 的 PR、Issue 和 Actions，还有 Linear 和 Jira 两个任务看板的抽屉式集成——从任务卡直接开一个 worktree 开始干活。

### Orca CLI：代理也能驱动编排器

CLI 的定位不是给人装包用的工具，而是让 shell 脚本和代理自己驱动 Orca。注册入口在 Settings → Experimental → CLI——目前仍是实验性功能，这点在评估时要知道。几个机制值得展开：

```bash
# 选择器系统：脚本不必持有长 ID
orca worktree show --worktree branch:feature-name --json
orca worktree show --worktree issue:123 --json

# 创建即派活：--agent 启动代理，--prompt 直接下任务
orca worktree create --name child-task --agent codex \
  --prompt "Investigate the flaky login test" --json

# 内嵌浏览器自动化：快照 → 操作 → 再快照的循环
orca goto --url http://localhost:3000 --worktree active --json
orca snapshot --worktree active --json
orca click --element @e3 --worktree active --json
orca fill --element @e1 --value "user@example.com" --worktree active --json
```

浏览器命令遵循严格的 snapshot → act → snapshot 循环：`@e3` 这类元素引用来自 `snapshot` 的输出，页面导航、点击导致页面变化、或引用失效后都必须重新快照。终端命令同样为机器消费设计：`terminal read` 默认返回去掉转义序列的累积输出，`--screen` 读当前渲染帧，长输出用 `--cursor` 游标分页；`terminal wait --for tui-idle` 可以等代理空闲再继续。

还有两处容易被忽略：`orca search` 能在 shell 里检索已索引的代理会话记录，且授权后可以跨已连接的电脑和配对服务器搜；`orca host list` 一次列出本机、SSH target 和已配对服务器，远程选择器形如 `id:<repoId>::<绝对路径>`。

### 盒子里还有的

README 的 "Also in the box" 列了几项初版文章没覆盖的能力：Quick open 全局搜索（worktree、文件、代理、命令一处可达）；账号切换器与用量跟踪（查看 Claude 和 Codex 的用量与限额重置时间，免重登热切换账号）；Computer Use（`orca computer` 通过辅助功能树、截图和安全 UI 操作让代理控制本地桌面应用，处理必须真实交互的流程）；以及通知与未读状态管理。

## 一次三代理竞速的完整流转

官方 Recipes 里最有代表性的一篇是"三个代理赛同一个任务"，步骤本身就解释了这套系统怎么用：

1. 从同一个起始 ref 创建三个 worktree，命名 `fix-bug`、`fix-bug-2`、`fix-bug-3`；
2. 每个里启动一个不同代理——Claude Code、Codex、Cursor CLI；
3. 把同一段 prompt 粘进三个终端，拖拽标签页分屏，看着它们同时干活；
4. 跑完后逐个审查 diff，对赢家用 Annotate AI Diff 逐行标注需要改的地方；
5. 从赢家 worktree 里提交、推送、开 PR；
6. 一键删除两个输家——worktree 和分支一起清掉。

官方对"为什么有效"的解释值得抄录：不同代理犯不同的错，同一任务并行跑比串行重试便宜，而分歧本身就是信号——三个代理一致的地方答案大概率是对的，它们分裂的地方就是你问题里真正难的部分。

这个流程里 Orca 做的事情没有一件是不可替代的（worktree、终端、diff、git 全是现成工具），但它把六步压缩成了一个界面里的连续操作，这才是编排器的价值所在。

## 安装

### 桌面端（macOS / Windows / Linux）

```bash
# macOS (Homebrew)
brew install --cask stablyai/orca/orca

# Arch Linux (AUR)，或用 stably-orca-git 从源码构建
yay -S stably-orca-bin
```

或从[官网下载页](https://onorca.dev/download)获取。以 v1.4.219 为例，发布物矩阵是：macOS 提供 Apple Silicon 与 Intel 两个 dmg；Windows 是经过 [SignPath](https://signpath.io) 签名的 setup.exe；Linux 除了 x86_64 与 arm64 两个 AppImage，还有 deb 与 rpm 包，均为双架构。

### 移动端

- iOS：[App Store](https://apps.apple.com/us/app/orca-ide/id6766130217)。初版文章提到的 TestFlight 入口已从现行 README 移除（链接本身仍可访问）。
- Android：APK 随发布线迭代（写作时 README 指向 0.0.50，最新已到 0.0.52），官方提供了单独的[安装指南](https://www.onorca.dev/docs/android-apk)。

## 支持的代理

官方口径是"任何 CLI 代理——能在终端里跑，就能在 Orca 里跑"，README 上的长列表更像生态展示而非测试清单。文章初版时列表为 29 个，现在已列到 34 个：Claude Code、Codex、Grok、Cursor、GitHub Copilot、Meta Muse、DeepSeek Harness、ZCode、OpenCode、小米 MiMo Code、Amp、OpenClaude、Antigravity、Pi、oh-my-pi、Hermes Agent、Devin、Goose、Auggie、Autohand Code、Charm、Cline、CodeBuddy、Codebuff、Freebuff、Command Code、Continue、Droid、Kilocode、Kimi、Kiro、Mistral Vibe、Qwen Code、Rovo Dev。

两个月新增的五个名字（Muse、DeepSeek Harness、ZCode、CodeBuddy、Freebuff）全是 8 月之后加入的，列表扩张速度和星数增速一致。对中文用户还有一个细节：仓库提供了[官方中文 README](https://github.com/stablyai/orca/blob/main/docs/readme/README.zh-CN.md)，社区微信群已开到第 11 个。

## 适用边界

### 适合

- 需要同时跑多个代理做同题竞速，或对同一任务做 A/B 对比
- 团队混用多种代理（比如 Claude Code + Codex），想要统一的监控、审查和提交入口
- 代理需要跑在远程机器（GPU 盒子、开发服务器）上，但人想留在本地界面
- 大量工作围绕 UI 修改，Design Mode 的元素级上下文能省掉来回截图
- 需要在手机上跟进代理进度、路上发后续指令

### 不适合

- 只用一个代理且不需要并行——编排层在这没有增量价值，直接用终端更轻
- 期望它补足代码理解——编辑器是 Monaco，深度静态分析、重构这类 IDE 级能力不是它的方向
- 需要 CI 流水线编排——Orca 编排的是人在回路里的交互式代理，不是 pipeline
- 想要托管服务——官方明说不卖托管 VPS，远程算力全部自带机器和云账号
- 对遥测敏感又不看文档的团队——Orca 收集匿名使用数据，好在[隐私文档](https://www.onorca.dev/docs/telemetry)写明了内容与退出方式，采用前值得读一遍

官方对"Orca 不是什么"的自我界定可以直接用作判断依据：不是模型（代理用你自己的订阅）、不是 git 替代品（worktree 随时可退回原生 git）、不是托管 VPS 产品。目标用户是"已经以写代码为生、把 AI 当杠杆而非替代品的人"——文档假设你读 diff、在乎提交、保持 worktree 整洁。

## 项目数据

以下为 2026-10-03 快照：

| 指标 | 数值 |
|---|---|
| Stars | 83,948（8 月 11 日约 42,200，近两个月接近翻倍） |
| Forks | 5,414 |
| 贡献者 | 397 |
| 主语言 | TypeScript（Electron 43 + xterm WebGL + Monaco） |
| 许可证 | MIT |
| 桌面最新版 | v1.4.219（2026-10-02），日更节奏 |
| Android APK | v0.0.52（2026-10-03） |

"日更"是官方自觉的发布策略，README 甚至自嘲"我们每天发货，所以这个功能清单永远滞后，changelog 才是真正的功能列表"。对使用者的含义是：别指望任何第三方文章（包括本文）长期保持精确，功能面向 changelog 对齐才是可靠的做法。

## 判断

Orca 解决的问题真实存在：代理从单兵到多兵之后，隔离、对比、审查、远程、监控这五个环节的摩擦是每个认真用代理的人都撞过的。它的 worktree 隔离设计简洁且可逆——不侵入代理本身，留下的全是标准 git 资产；四种运行模式把"算力放哪"做成了显式选择而不是隐式绑定；移动端连 relay 都开源的做法，在同类工具里少见。

代价也清楚：Electron 桌面应用的资源占用不低；CLI 仍在实验区；日更节奏意味着界面和命令可能每几周就变一次；仓库的 issue 积压（当前约 7,400 个 open issue 与 PR）说明迭代速度已经超出了社区消化能力。如果只使用单一代理，这层编排确实没有存在的必要。

采用顺序上，建议分三步：先在本地桌面模式跑官方文档称为"全文档最重要一页"的[首个三代理会话](https://www.onorca.dev/docs/first-session)，验证同题竞速对你手头的任务是否真的有效；有效，再把周期长、吃算力的任务迁到 SSH target 或 `orca serve`；最后才考虑移动端配对——它是体验的锦上添花，不是前两步的前提。已经在用多个 CLI 代理的团队可以直接从第二步开始；仍在单代理阶段的，等出现第一个真实的并行需求再装不迟。
