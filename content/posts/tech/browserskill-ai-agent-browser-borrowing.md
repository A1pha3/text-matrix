---
title: "BrowserSkill：让 AI Agent 借用你已登录的浏览器，而不是接管它"
date: 2026-09-21T04:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["BrowserSkill", "AI Agent", "浏览器自动化", "Tencent"]
description: "腾讯开源的 BrowserSkill 用 Rust CLI 守护进程加 MV3 浏览器扩展，让任意 shell 型 AI Agent 复用真实登录态操作浏览器：显式借还标签页、独立 Agent Window、扩展侧确认开关、网站调试取证与远程配对。本文拆解它的三层架构、一次工具调用的完整链路、隐私模型与适用边界。"
github_repo: "Tencent/BrowserSkill"
source_key: "gh:Tencent/BrowserSkill"
slug : browserskill-ai-agent-browser-borrowing
---

## 核心判断

BrowserSkill 处理的是 AI Agent 落地里最别扭的一环：浏览器操作。现有方案要么让 Agent 驱动一个干净的自动化浏览器实例（Playwright 这类，没有登录态，内部系统什么都打不开），要么直接接管用户正在用的浏览器（Agent 一动，人就没法工作）。BrowserSkill 的答案是「借用」——Agent 在独立的可见窗口里操作，复用真实登录态，但必须显式借还标签页，其余浏览器活动不受干扰。

它的第二个关键决策是不绑定任何 Agent 框架：只要有 shell 就能调 `bsk` CLI。Cursor、Claude Code、Codex、OpenClaw、CodeBuddy、WorkBuddy、Pi、Hermes Agent 都在官方支持之列，DeepSeek Harness 另有带原生浏览器工具的专用插件。README 把这层关系说得很直白：Agent 和模型由你选，BrowserSkill 只负责连接浏览器。这个定位让它更像基础设施，而非某个生态的插件。

## 项目概览

| 项 | 数据（2026-09-29 取自 GitHub） |
|---|---|
| 仓库 | [Tencent/BrowserSkill](https://github.com/Tencent/BrowserSkill) |
| 定位 | Let AI agents work in your logged-in browser while you keep working |
| Stars / Forks | 7,766 / 552 |
| 实现 | Rust（CLI / 守护进程 / 协议层）+ TypeScript（WXT MV3 扩展），pnpm workspace |
| License | MIT |
| 当前版本 | CLI / 扩展 / DSH 插件 0.3.1（2026-09-23 发布，三者共享版本号） |
| 首个公开版本 | CLI 0.1.5 / 扩展 0.1.2（2026-06-22） |
| 运行形态 | `bsk` CLI + 守护进程 + 浏览器扩展，本地运行；0.3.0 起支持守护进程上服务器、浏览器留本地的远程模式 |

运行环境覆盖 macOS（Apple Silicon 与 Intel）、Linux（x64/ARM64）、Windows x64；浏览器扩展要求 Chromium 125 及以上的 Chrome 或 Edge，其他 Chromium 系浏览器「可能可用，不保证兼容」。扩展界面有英、简繁中文、韩、日、法、意、西、德、巴西葡语九种语言。

## 架构：三个组件，两条链路

先把组件分清楚，后面所有机制都挂在这张图上：

| 组件 | 实现 | 职责 |
|---|---|---|
| `bsk` CLI | Rust，动词-名词子命令 | 解析命令，经 IPC 交付守护进程，输出人类可读文本或 `--json` |
| 守护进程 daemon | 与 CLI 同一个二进制 | 会话路由、请求排队、维护已连接浏览器列表 |
| 浏览器扩展 | TypeScript，WXT 构建 MV3 | 真正执行浏览器操作：CDP 加 WebExtension API，21 个工具处理器 |
| SKILL.md | 随 CLI 分发 | 教会 Agent 框架什么时候、怎么调 `bsk` |

两条链路分别是：CLI 到守护进程走 JSON Lines over Unix domain socket（`$BSK_HOME/run/daemon.sock`，默认主目录 `~/.bsk`；Windows 走命名管道）；守护进程到扩展走 loopback WebSocket，默认端口 52800，握手时校验 `Origin: chrome-extension://`，扩展侧保存匹配端口。守护进程按会话串行化发往同一会话的工具调用（会话级引用存储的一致性依赖这个），不同会话之间并行。

这个结构决定了两件事。一是浏览器操作始终发生在用户自己的浏览器进程里，cookie 不离开浏览器 profile——守护进程经手的是指令和结果，不是凭证。二是 CLI 只做转发，所以 Agent 沙箱、远程服务器这些部署形态才有可能：把守护进程留在持久环境里，CLI 在哪儿都能连。

## 核心机制：借还、确认、分发

### 1. 借用而非接管

会话是权限的基本单位：一个会话 = 一个 4 字母小写 ID + 一个专属 Agent Window + 会话级引用存储 + 借用表。默认情况下，写操作只能作用于 Agent Window 内的标签页；要操作用户已打开的页面，必须先把那个标签页显式借入借用表，用完归还。`tab list` 的作用域也照此分三档：`user`（用户的窗口）、`agent`（本会话 Agent Window）、`all`。多个会话可以并存于同一浏览器，各自开各自的 Agent Window，完全隔离。

Agent Window 与用户窗口共享所选 profile 的登录态——官方在 README 里特意加粗提醒：它不是一个独立账号，也不是安全沙箱，Agent 能以已登录网站的权限行事。所以选可信的 Agent 和可信的任务，这层没有兜底。

### 2. human-in-the-loop 由扩展说了算

任务撞上验证码、登录、确认对话框这类只有人能处理的步骤时，Agent 可以发起求助，人处理完，Agent 继续余下任务。0.3.0 把控制权从 Agent 侧收回了用户侧：扩展设置里两个独立开关——「借用标签页前确认」「允许发起人工求助」，默认都开，同时对已有会话和新会话生效。`--unattended`、`tab borrow --no-confirm`、`BSK_REQUEST_HELP=off` 这些旧参数降级为兼容输入，无法再覆盖浏览器里保存的设置。CHANGELOG 提醒依赖无人值守工作流的用户升级后去浏览器偏好里重新设置。另外注意：关闭人工求助并不代表 Agent 自已完成那个步骤，只是不再来问。

### 3. Skill 分发：可校验、可保留修改

`bsk install-skill` 把官方 SKILL.md 连同 `references/` 装进各框架的 skills 目录，交互选择目标，脚本化安装用 `--harness cursor --json` 这样显式指定。同步策略值得展开说：安装时写一份 `.bsk-source` 清单，逐文件记录 SHA-256；守护进程启动、`session start` 和 `doctor` 会自动更新托管技能，但更新前逐文件校验——内容仍与上次安装基线一致的才替换，用户本地改过的副本暂停自动更新并保留修改。中断的写入有 pending manifest 支持断点续装。对定制工作流的人来说，这比「每次升级覆盖」友好得多；`doctor` 会报告处于暂停状态的技能更新。

## 一次点击的完整链路

把上面的组件串起来，看官方架构文档给的例子：Agent 执行 `bsk click @e1 --tab-id 42 --session ab12`。

1. CLI 确认守护进程在跑（不在则按需拉起，`BSK_AUTO_START=0` 可禁用隐式启动），打开 UDS，发一行 JSON 请求。
2. 守护进程把会话 `ab12` 解析到对应的浏览器连接，把 `tool.click` 经 WebSocket 转发给扩展。
3. 扩展的工具分发器校验沙箱规则——`@e1` 这个引用必须是本会话创建或已借入的标签页——然后经浏览器驱动层调 CDP 完成点击。
4. 响应原路返回：扩展 → 守护进程 → CLI，CLI 打印结果退出。

Agent 工作流里 `bsk session stop` 是强制收尾动作，空闲超时（默认 5 分钟）只是安全网；借用中的标签页会在会话结束时归还原窗口。任务失败也要停会话，README 对此单独强调了一遍。

## 能做什么

**全页长截图**。扩展 Quick Actions 里的 Full-page screenshot 不依赖 Agent 或守护进程，单独就能用；Agent 会话里则是 `bsk screenshot --session <id> --full-page --out page.png`。0.3.0 起流式输出 PNG、可取消，后台标签页截图不用把窗口切到前台，截完恢复原滚动位置。嵌套滚动面板和虚拟化长列表是已声明的限制。

**网站调试取证**（0.3.1 新增）。这是同类工具里少见的方向：不只替你操作页面，还给 Agent 提供查 bug 的证据。开始捕获后复现问题，扩展记录请求与响应体、控制台输出、表单字段值、页面变化，按操作分组并标注来源；配套任务级 HTTP 规则、请求重放、页面加载指标、API 耗时汇总和重复请求分析。证据存浏览器本地，任务结束后仍可回看，可导出 JSON；停止的记录 30 天过期，保留预算 50 条 / 50 MiB。CLI 入口是 `bsk debug start --session <id> --name 'Save fails'`。请求重放会以页面当前会话真实发出请求，可能改动服务器数据——文档原文的警告，用之前掂量一下。

**浏览器 profile 与远程模式**。多 profile 用户可以在扩展里给实例命名（这个名字是 BrowserSkill 里的，不自动取自 Chrome profile 名），`bsk session start --browser "Work profile"` 显式绑定。0.3.0 的远程模式则是另一种形态：浏览器和登录态留在本地电脑，Agent、CLI、守护进程跑在服务器上，扩展经认证 WSS 反向连过去——连接由浏览器发起，本地不用开任何入站端口，内置服务器支持设备配对、续期和吊销。远程会话不支持文件上传下载，本地会话支持。

**文件传输的边界设计**值得单独看一眼。0.2.0 引入的上传下载只限本地连接，且 CLI 是唯一读上传源、写下下载目的地的组件，扩展永远拿不到 Agent 侧的路径；守护进程签发会话级不透明传输 ID，分块暂存，校验路径、文件类型、符号链接边界和字节上限后才落盘。传输结果带 `effect_state`（none / committed / unknown），超时后 unknown 状态不允许盲目重试——这套设计明显是冲着「浏览器传输是副作用操作」这个问题去的。

## 隐私模型

没有强制云服务，没有产品遥测，扩展不独立调用 AI 提供商；自动化结果只流向你选的守护进程或网关，以及使用它的 Agent——后者按它自己的策略处理数据，这是你选择 Agent 时要一并评估的。两类可选历史分开存放：网站调试证据在浏览器 profile 里（远程模式下也在本地浏览器），操作审计默认关闭，开启后记在守护进程主机的 `BSK_HOME/audit`，只有任务与操作元数据，不含输入值、页面内容、截图和文件内容，30 天过期。两者都支持导出和删除。

已知密钥会从调试证据中过滤，但官方明说脱敏不能保证清除所有敏感数据。停止任务或断开连接不会删除已存历史，已导出的副本和已被 Agent 接收的副本要自己管。

## 快速上手

已经在用 Cursor / Claude Code / Codex 等 shell 型 Agent 的用户，官方推荐把这一行直接发给 Agent，让它照文档完成安装：

```text
Set up browser-skill on this machine by following https://raw.githubusercontent.com/Tencent/BrowserSkill/main/AGENT_INSTALL.md
```

手动安装四步（命令取自 README）：

```bash
# 1. 安装 bsk CLI（macOS/Linux）
curl -fsSL https://raw.githubusercontent.com/Tencent/BrowserSkill/main/install.sh | sh
export PATH="${BSK_INSTALL_DIR:-$HOME/.local/bin}:$PATH"

# Windows PowerShell
irm https://raw.githubusercontent.com/Tencent/BrowserSkill/main/install.ps1 | iex
```

```text
# 2. 安装浏览器扩展
# Chrome Web Store: https://chromewebstore.google.com/detail/hhcmgoofomhgciiibhipgmgkgnoenaoi
# Edge Add-ons: https://microsoftedge.microsoft.com/addons/detail/browserskill/emacgiaaaiojkkpkddmmdfhmokgmnikg
```

```bash
# 3. 安装 skill 到你的 Agent 框架（交互选择 harness；查看支持列表用 --list）
bsk install-skill

# 4. 验证连接
bsk doctor
```

两个容易踩的点：扩展 popup 里要开启本地连接并确认状态为 Connected；`bsk doctor` 全绿只证明 CLI—守护进程—扩展链路通，不证明 Agent 能发现 `browser-skill` skill——要开一个新 Agent 会话验证。已在运行的 Agent 装完 CLI 后找不到 `bsk`，重启它加载新 PATH，或配置绝对路径。

验证任务就用 README 的原话发给 Agent：

```text
Use browser-skill to open https://example.com, summarize the page, and end the browser session when finished.
```

预期行为：Agent 打开一个 Agent Window，读页面，返回摘要，结束会话。支持 skill 斜杠命令的框架也可以直接 `/browser-skill`。想绕开 Agent 直接触碰 CLI：`bsk session start --no-focus --json` 拿到 `session_id`，接着 `bsk navigate`、`bsk observe`、`bsk screenshot`、`bsk session stop`。

Agent 沙箱环境（每条命令结束就回收后台进程的那种，WorkBuddy 的 bubblewrap 沙箱就出过 issue #214）按 sandboxed-agents 文档处理：守护进程放宿主机持久运行，沙箱内用共享 `BSK_HOME` 加 `BSK_AUTO_START=0` 连接——注意宿主机和沙箱必须看到同一个底层目录，只有环境变量文本相同而挂载不同是不行的。

日常更新用 `bsk update --yes`，它会重启运行中的守护进程；扩展走浏览器商店更新。新特性要求 CLI、守护进程、扩展版本匹配，升级后用 `bsk --version`、`bsk status`、`bsk doctor` 核对。

## 适用边界

- **权限即登录态**：Agent Window 复用你的真实登录态，不是独立账号也不是沙箱。借用确认默认开启，建议保持；高敏感账号场景先想清楚交给哪个 Agent。操作审计默认关闭，合规敏感的团队可以评估开启。
- **Chromium 限定**：要求 Chromium 125+，官方支持 Chrome 与 Edge；其他 Chromium 系浏览器属「可能可用」，Firefox 无官方支持计划。
- **沙箱与远程的形态差异**：文件上传下载仅限本地连接，远程模式不支持；嵌套滚动面板、虚拟化长列表的全页截图有已知限制。
- **版本联动**：CLI、守护进程、扩展要匹配版本，商店上架的扩展构建可能滞后于仓库，对照 CHANGELOG 和 releases 页确认。

## 结语

BrowserSkill 的价值不在「又一个浏览器自动化工具」，而在它给「人与 Agent 共用一台浏览器」定了一套可执行的规矩：显式借还、独立可见窗口、确认权在扩展、证据可审计。配合 Agent 无关的 CLI 和可校验的 skill 分发，它适合作为各类 Agent 工作流的通用浏览器层来评估。

落到采用顺序：已经在用 shell 型 Agent 且需要操作内部登录系统的团队，可以直接上，装完跑一遍 example.com 验证任务就能测通链路；需要 Agent 查线上前端问题的，0.3.1 的网站调试取证是明确加分项；Agent 跑在服务器上的部署，先在测试环境验证远程配对链路再铺开。主要的不确定性在项目尚年轻——从首个公开版本到现在三个月，协议和 CLI 面还在快速变，把版本锁定写进部署流程比追新更重要。
