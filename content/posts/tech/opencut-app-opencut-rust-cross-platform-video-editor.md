---
title: "OpenCut 拆解：91K Stars 的开源 CapCut 替代品，正在推倒重来"
date: 2026-07-24T03:02:00+08:00
lastmod: 2026-10-03T00:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["OpenCut", "视频编辑", "Rust", "GPUI", "开源项目解读"]
description: "OpenCut 是定位「开源 CapCut 替代品」的开源视频编辑器，91K Stars。本文对照 main 分支源码拆解它的重写：六项架构承诺各自落到哪一步、经典版留下了什么底子、现在该用哪个版本、以及怎么跟踪重写进展。"
slug: opencut-app-opencut-rust-cross-platform-video-editor
github_repo: "OpenCut-app/OpenCut"
source_key: "gh:OpenCut-app/OpenCut"

---

## 一个判断先放在前面

OpenCut 的看点不是「又一个开源视频编辑器」，而是它正在做一次高风险的路线切换：**把编辑器从「带界面的工具」改造成「可编程的渲染引擎 + 编辑 API」**，并且把 AI agent 接口（MCP，Model Context Protocol，模型上下文协议）直接写进架构目标——这在开源视频编辑器里没有先例。代价是：主仓库 `main` 分支已经不再是那个 91K Stars 时被克隆的代码库。旧版被整体搬进 `opencut-classic` 归档仓库，新代码从零起步。截至 2026-10-03，重写版在源码里的落点是**一套选型完毕的技术底座加一个 UI 骨架**，六项架构承诺还没有一项变成可用功能。README 那句 "What's coming" 说的是路线图，不是现状。

这篇文章按 main 分支源码、changelog 与官方 README 把两套代码库各自的真实状态拆开，最后回答一个实际问题：现在该用哪个版本，以及怎么判断重写什么时候值得再看一眼。

## 仓库现状与核实口径

下表数字在 2026-10-03 通过 GitHub API 读取，源码断言对照 `main` 分支当日快照。这类高速变动的项目，数字口径比数字本身重要。

| 项 | 主仓库 `OpenCut-app/OpenCut` | 归档仓库 `opencut-classic` |
|---|---|---|
| 定位 | 重写版（当前开发主线） | 原版代码存档（"Original OpenCut codebase"） |
| Stars / Forks | 91,303 / 9,037 | 263 / 331 |
| 主语言 | TypeScript（Rust 文件 15 个） | TypeScript |
| License | MIT | MIT |
| 建仓时间 | 2025-06-22 | 2026-05-16 |
| 最近推送 | 2026-09-24 | 2026-05-17 |
| 在线地址 | [new.opencut.app](https://new.opencut.app) | [opencut.app](https://opencut.app) |

三个容易读错的口径细节：

- 91K Stars 是主仓库的，但 `opencut.app` 上跑的是经典版。关注重写的 star 数和可用产品的 star 数在这里是同一个数字，读其他人的报道时容易混淆。
- `opencut-classic` 建于 2026-05-16、次日完成最后一次推送——旧代码是在这个时间点被整体移出主仓库的，不是「一直躺在本体里」。
- 主仓库最新 release 不是版本号，是 `ffmpeg-8.1.3-1`（2026-09-24）。版本号 release 停在 `v0.3.0`（2026-04-15），那是经典版的最后一个功能版本。

本文的数字漂移最快，复核优先看四处：上表的 Stars/推送时间（GitHub API 一条命令）；`Cargo.toml` 的 members 列表（`crates/*` 是否取消注释）；`apps/desktop/README.md` 顶部的 WARNING 是否还在；release 页有没有出现版本号新条目。后三处的具体看法定义在「现在该用哪个，怎么跟踪重写」一节。

## 时间线：从 CapCut 替代品到推倒重来

仓库 description 只有一句话：**The open-source CapCut alternative**。2025-06-22 建仓后靠这个定位积累了 91K Stars——剪映（CapCut）没有 Linux 版、导出加水印、隐私争议不断，一个浏览器里就能剪视频的开源替代品正好接住这批需求。

经典版按 changelog 走了三个版本：

| 版本 | 日期 | 主题 | 关键能力 |
|---|---|---|---|
| v0.1.0 | 2026-02-23 | Editor foundation | 属性面板重构（数值框支持数学表达式与拖拽调节）、字体从 7 款扩到 1000+、混合模式（暂只对文本生效）、预览区内直接移动/缩放/旋转元素 |
| v0.2.0 | 2026-03-01 | Motion & effects | 关键帧动画、效果系统（首个效果是 Blur，可挂片段也可作独立时间线元素）、涟漪编辑模式 |
| v0.3.0 | 2026-04-15 | Masks, animation & more | 遮罩、关键帧曲线图编辑器、音量/速度控制（保音高选项）、RMS 音频波形重写、修复 Firefox 的 MP4 导出 |

2026-05 中旬，旧代码拆进 `opencut-classic`，main 分支清空重来。这一步的公开解释只有 README 里的一句 "OpenCut is being rewritten from the ground up"，以及贡献政策的变化：**架构设计期不接受外部贡献**，想参与只能进 Discord 或提 issue。

## 新架构承诺了什么

README 列出六项。前四项经常被二手文章混着讲，实际是两类东西：前三项是运行架构，后三项（连同 API）是自动化接口。

| 承诺 | README 原文 | main 分支现状（2026-10-03） |
|---|---|---|
| Editor API | An Editor API | 未见公开接口定义 |
| 插件优先 | First-class third party plugins | 架构设计期，未接受外部贡献 |
| 一套代码覆盖三端 | Desktop, mobile, and browser from one codebase (Rust core) | `apps/` 下已有 web、api、desktop 三端目录，Rust 核心库 `crates/media` 仅有 `setup/` 子目录且未挂进 workspace |
| MCP server | MCP server (for AI agents) | 全仓库文件树中无任何 MCP 命名路径 |
| Headless 模式 | Headless mode (automation, batch rendering) | 未见实现 |
| 编辑器内脚本面板 | A scripting tab directly in the editor | 未见实现 |

六项承诺，零项落地。这不是贬义——它准确地说明了现在读这个仓库该用什么预期：读选型，不读功能。

## 重写走到哪一步：源码里的四个信号

**信号一：Rust workspace 只挂了桌面端。** 根目录 `Cargo.toml` 的 members 列表里只有 `apps/desktop`，`crates/*` 那行被注释着。也就是说，被宣传为「一套代码覆盖三端」核心的 Rust 库（`crates/media`）还没有进入编译体系，目录里只有一个 `setup/` 子目录。三个端里真正在用 Rust 的只有桌面端。

**信号二：桌面端用 GPUI，且官方自述极早期。** `apps/desktop/Cargo.toml` 依赖 `gpui = "0.2.2"`——Zed 编辑器的 UI 框架，README 写着 "built with GPUI"。但同一份 README 的警告框写着：**"Very early. Right now this is just a window that opens."** 源码侧与此吻合：`apps/desktop/src/` 下 15 个 `.rs` 文件，除 `main.rs` 外是一组 UI 组件（badge、button、context_menu、resizable、separator）和三块面板骨架（preview、inspector、browser）。有界面壳子，没有时间线和媒体引擎。

**信号三：Web 与 API 端换了整套技术栈。** `apps/web` 的 `package.json` 是 React 19 + TanStack Start/Router + Tailwind 4，部署目标经 `@cloudflare/vite-plugin` 指向 Cloudflare；`apps/api` 是 Elysia + wrangler（`wrangler.jsonc`），跑在 Cloudflare Workers 上。对照经典版的 Next.js + better-auth，这是一次框架级更换，不是渐进升级。

**信号四：MCP 的落点是零。** 对全仓库 157 个文件路径按 `mcp` 检索，命中 0 处。「AI agent 可以操作编辑器」目前是 README 里的一行文字，没有任何代码对应。唯一的间接进展是媒体管线的：9 月的 `ffmpeg-8.1.3-1` release 说明 FFmpeg 集成在动，而媒体引擎是 MCP 操作的对象，先有引擎才有得操作。

工具链是重写版里最「完成」的部分：`proto` 统一钉死 moon 2.3.3、Bun 1.3.11、Rust 1.97.0，所有开发者和 CI 拿到同一套版本。

## 任务流：clone 之后的第一次 `moon run desktop:dev`

把抽象进展落到一次真实操作上。按官方 README：

```sh
proto use              # 按 .prototools 装 moon 2.3.3 / bun 1.3.11 / rust 1.97.0
moon run desktop:dev   # 实际执行 cargo run
```

首次运行会把 GPUI 从源码编译一遍（仓库提示这需要相当时间；根 `Cargo.lock` 已提交，依赖版本固定）。编译完成后得到一个能打开的窗口，由三块面板骨架组成。想跑 Web 端是 `moon run web:dev`（localhost:5173），API 端是 `moon run api:dev`（localhost:8787）——但这两个端目前是脚手架，完整的编辑能力仍在 `opencut-classic` 里。

这一趟走完，对「重写进展」的判断就从读 README 变成了读代码：底座选型完毕、UI 骨架就位、编辑功能未接。这比任何路线图都具体。

## 经典版的底子：Rust 不是新路线

「Rust 核心」不是重写才开始的想法——这是读 `opencut-classic` 仓库才会发现的：那里也躺着一个 Cargo workspace，members 是六个 crate——`time`、`bridge`、`effects`、`gpu`、`masks`、`compositor`——外加 `rust/wasm`；前端 `package.json` 依赖 `opencut-wasm ^0.2.10`，说明 Rust 代码编译成 WebAssembly 后作为 npm 包接进了浏览器端。

所以两条路线的关系是这样的：经典版把 Rust 当作 **Web 端的性能加速模块**（关键计算下沉到 WASM，界面仍是 Next.js）；重写版要把 Rust 提升为**三端唯一的逻辑核心**，界面退化为各平台的一层壳。方向是同一个，幅度完全不同。这也回答了「浏览器端怎么跑 Rust」的疑问——项目自己已经有先例，只是新架构的官方实现说明还没有出现。

## 与现有开源编辑器的差异

| 项目 | 核心语言 | 界面/框架 | 现状（2026-10-03 核实） |
|---|---|---|---|
| Kdenlive | C++ | Qt，KDE 生态，底层 MLT | 活跃（GitHub 为镜像，主开发在 KDE 自己的 GitLab；5.8K stars） |
| Shotcut | C++ | Qt，底层 MLT | 活跃（15.3K stars） |
| Olive | C++ | Qt | 停滞：最后推送 2024-12-05，近两年无更新（9.1K stars） |
| OpenCut 经典版 | TypeScript + Rust/WASM | Next.js | 可用，功能见上文时间线 |
| OpenCut 重写版 | Rust + TypeScript | GPUI / React 19 | 底座阶段，无可用编辑功能 |
| DaVinci Resolve | 闭源商业软件（有免费版） | 自研 | 不在开源阵营，是这些项目共同的参照系 |

OpenCut 的差异化不在「做得比它们好」——目前任何一条编辑能力都比不过成熟项目——而在两个方向：**浏览器原生**（不装东西就能剪，经典版已验证）和 **为自动化设计**（Headless、MCP、脚本面板都是给程序和 agent 用的入口，现有编辑器几乎没有认真做这个）。

「用 Rust 保证内存安全、减少 C++ 编辑器常见的崩溃」是社区常提的理由，方向合理，但对重写版而言还是愿景——崩溃率的改善要等媒体引擎真正跑起来才有得谈。

## 现在该用哪个，怎么跟踪重写

**现在要剪视频：用经典版。** [opencut.app](https://opencut.app) 跑的就是它，具备时间线、关键帧、遮罩、效果、导出（v0.3.0 水平）。对新架构的期待不要投射到它上面——MCP、插件、Headless 它都没有。本地开发用 [opencut-classic](https://github.com/opencut-app/opencut-classic) 仓库，技术栈是 Next.js + Bun。

**想跟重写：盯三个客观信号**，比刷社媒可靠。

1. 根目录 `Cargo.toml` 的 members 里 `crates/*` 何时取消注释——那意味着媒体核心进入编译体系。
2. `apps/desktop` README 顶部的 WARNING 何时消失——维护者自己对成熟度的标尺。
3. release 页何时出现 MCP 或 plugin 相关的版本——功能承诺兑现的第一手证据。

**适合现在投入的**：想做浏览器端视频工具的开发者（经典版代码可读、技术栈主流）、研究 agent 操作创作工具这一方向的探索者（MCP server 是明确写进目标的）、以及愿意读源码跟架构演进的人。

**不适合的**：需要稳定生产工具的团队（成熟度差距是数量级的）、Linux 桌面重度用户（经典版功能有限，Kdenlive/Shotcut 更成熟）、以及任何「现在就要」的场景——重写版连第一个里程碑都还没打出来。

91K Stars 投的是「开源 CapCut 替代品」这个定位，不是重写后的架构。定位能不能撑住第二次押注，取决于那六项承诺兑现的速度——跟踪信号已经列在上面了。

## 参考来源

- 主仓库：<https://github.com/OpenCut-app/OpenCut>（README、`Cargo.toml`、`.prototools`、`apps/` 各端 `package.json` 与源码树，2026-10-03 快照）
- 经典版归档仓库：<https://github.com/opencut-app/opencut-classic>（`rust/` crate 结构、`package.json` 的 `opencut-wasm` 依赖）
- 在线版本：经典版 <https://opencut.app>；重写版 <https://new.opencut.app>
- 经典版功能变更记录：主仓库 `changelog/0.1.0.md`、`0.2.0.md`、`0.3.0.md`
- GitHub API 数据（stars/forks/时间/语言）：<https://api.github.com/repos/OpenCut-app/OpenCut>、<https://api.github.com/repos/opencut-app/opencut-classic>
- 对比项目仓库：<https://github.com/mltframework/shotcut>、<https://github.com/olive-editor/olive>、Kdenlive（GitHub 镜像 <https://github.com/KDE/kdenlive>）
