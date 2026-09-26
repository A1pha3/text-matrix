---
title: "herdr 拆解：终端复用器之上的智能体运行时，状态权威是一条把它讲清的主线"
date: "2026-08-01T22:28:00+08:00"
lastmod: "2026-09-26T00:00:00+08:00"
draft: false
categories: ["技术笔记"]
tags: ["herdr", "终端复用器", "AI智能体", "tmux", "Rust", "开发者工具", "终端", "Socket API"]
slug: herdr-agent-terminal-multiplexer
description: "对着 herdrdev/herdr 的 README 与 herdr.dev/docs 逐条核对后拆解它：状态权威（Status Authority）一条线把智能体感知、状态机、检测清单、会话恢复串成一体。22 种开箱即用的智能体各自靠什么判定状态，五种状态谁该让人看，会话恢复的四条路径分别在哪个文件、由哪个配置键开关，以及 live handoff 与 64 块窗格上限这层语义。结论都附官方文档出处或可直接复跑的命令。"
author: text-matrix
hiddenFromHomePage: false
github_repo: "herdrdev/herdr"
source_key: "gh:herdrdev/herdr"
---

> **目标读者**：同时跑两个以上 AI 编程智能体、需要在终端里把它们的状态和协作管起来的人；以及打算把 herdr 当多智能体运行时装进自己工作流、要先判断它承受到哪一步的人。
>
> **本文口径**：核对对象是 [herdrdev/herdr](https://github.com/herdrdev/herdr) 的默认分支 `master`（注意，不是 `main`）与 [herdr.dev/docs](https://herdr.dev/docs/)。仓库数字取自 GitHub 官方接口在 2026-09-18 的快照，版本与最近推送时间同源；架构、状态机、命令与配置键取自 docs 各页原文。没有实跑支撑的部分——例如 herdr 客户端实际渲染效果——标题或句子里不会虚写。

## 一句话判断

herdr 不是又慢又厚的 `tmux`，是**给人和 AI 编程智能体一起用的终端复用器**。它在 tmux 那套"分屏、分离、重连"之上加了三个维度：理解窗格里跑的是什么、主动告诉你哪个智能体需要人看、以及把一条命令接口开放给智能体自己用。

它的设计价值来自一件事做对了：**状态权威**。每个窗格同一时刻只有一个权威来源——要么是装了官方集成的生命周期钩子，要么是对屏幕快照跑 TOML 检测清单。这一条主线向后引出五种状态、22 种开箱即用识别与 manifests 远程更新，向前引出会话恢复的四条路径和 live handoff。把这条线捋清，herdr 的文档就不再是散页。

所以更准的读法是：herdr 会把智能体当成窗格之上的一等公民去管，但**它不封装也不替换任何智能体**——Claude Code、Codex 各自跑各自的，herdr 只拥有它们的终端。本文按"状态权威"这条主线展开，先讲它管什么，再讲它怎么判，最后讲断了怎么接。

## 项目坐标

| 项 | 值（2026-09-18 核对） |
|:---|:---|
| 仓库 | [herdrdev/herdr](https://github.com/herdrdev/herdr)，默认分支 `master` |
| 自述定位 | the runtime your coding agents live on——编码智能体赖以运行的运行时（README `agent instructions` 一节下有更朴素的表述：a terminal multiplexer for coding agents） |
| 许可 | Apache-2.0 |
| 关注度 | 39,460 stars、2,974 forks、339 个未关闭 issue；回者 105 人 |
| 时间线 | 建仓 2026-03-27，最近推送 2026-09-18 |
| 最新版 | v0.9.1（2026-09-16 发布），仍处 0.x 快速迭代期 |
| 语言与形态 | 纯 Rust 单二进制，无 Electron、无 GUI；跑在你已有的终端里 |
| 官网/文档 | <https://herdr.dev/docs/>：quick-start、concepts、agents、keyboard、configuration、session-state、connecting-machines、remote、integrations、plugins、socket-api |
| 平台 | 安装脚本 + Homebrew + mise + Windows beta；远程经 SSH 协商 |

仓库用号源数据常变，正文里的星标数只作 2026-09-18 的快照用。版本策略方面，v0.9.1 意味着核心接口与实验性开关（handoff、pane history）都可能继续变动，跟着版本走要有心理准备。

## 它管的是"窗格"，不是"智能体"

herdr 的分层是 Workspace → Tab → Pane，共三层，Pane 之上才是被"管"的 Agent：

| 层 | 是什么 | 职责 |
|:---|:---|:---|
| Workspace | 顶层项目容器 | 一个仓库或一项任务一个；侧栏状态向上汇总自其内智能体 |
| Tab | 工作区内的布局 | 把视图分开——`agents`、`logs`、`server`、`review`；可被 CLI 与 Socket API 寻址 |
| Pane | 真实终端 | 渲染输出、回写输入、跨客户端分离保持存活；可向右/向下拆分、重命名、读、喂输入 |
| Agent | 被识别出的进程 | 是 Pane 里的一个被识别进程，有一等公民的状态机 |

这里的顺序是刻意反过来的：**Pane 是真实终端，进程住在 Pane 里；Agent 只是对这堆进程的一员做了识别。** 所以 herdr 不在你的智能体和你的 `tmux` 之外再造一层壳，它只是让复用器"看得懂"其中一类窗格。

架构上，herdr 是"后台服务器 + 一个或多个挂载客户端"。服务器持有窗格与进程状态；客户端是附在服务器上的终端 UI。多个客户端可以各自看不同工作区/标签，各自维护"哪些完成已经显示过"的标记——在一个客户端看过某个 `done`，不会消掉另一个客户端的角标；而 CLI/API 读的是服务器侧的统一 seen 状态，所以可能与某个客户端的角标不一致。

交互有三种模式：`terminal`（按键直达聚焦窗格）、`prefix`（前缀键后跟一个动作，默认前缀 `ctrl+b`，`c` 新建标签、`w` 打开工作区导航）、`navigate`（常驻的工作区导航面）。键鼠都是第一等输入：点窗格、拖分割线、按选择文本、右键菜单全都默认可用；只想用键盘或不想让 herdr 拦截鼠标，在配置里关掉即可：

```toml
[ui]

mouse_capture = false
```

## 状态机：五种状态，两条信号

herdr 给每个被识别的智能体维护一个状态标签，五种状态覆盖其全部生命周期。文档原表的定义如下：

| 状态 | 含义 |
|:---|:---|
| `blocked` | 智能体需要输入、批准或决策 |
| `working` | 智能体正在运行 |
| `done` | 智能体已完成、但你还没看过 |
| `idle` | 智能体已完成或等待中、且已被看过 |
| `unknown` | herdr 无法确信地分类 |

它的设计很克制：不试图理解智能体在"想"什么，只解决一个对外接口问题——**这个智能体现不需要人看一眼？** `blocked` 和 `done` 是要人介入的信号；`working` 说明在跑；`idle` 与 `done` 按官方口径都表示可接收输入，区别只在你看没看过。点 `done` 的完成标志，直到你查看它才消。

侧栏把状态向上聚合：一个 `blocked` 的智能体会让它的窗格、标签、工作区都标为需要关注；`working` 让工作区显示为活跃。你扫一眼侧栏就知道三个项目里有几个智能体在等你。

## 状态权威：同一个窗格只有一条判定来源

这是理解 herdr 智能体感知的钥匙。识别分两步：先在窗格里检测前台进程，然后给这个窗格**一个**状态权威。官方文档明确写了"avoids two competing sources of truth"——避免两个互相打架的真值来源。

权威有两类，二选一：

- **完整生命周期钩子的集成（authoritative）**：装了官方集成、且在给当前窗格活跃上报时，集成上报就是权威。它给 `idle`、`working`、`blocked` 和会话身份，同时**不会**再对同一窗格跑屏幕清单兜底。
- **屏幕清单（screen manifest）**：没有完整钩子的智能体，herdr 识别前台进程后，对**窗格底部缓冲区的实时快照**跑 TOML 规则来分类。注意快照取自底部缓冲区，不是滚动视口——你往回翻，检测仍然跟着底部的实时智能体界面走。

两者都上报时只能留一个，这正是"状态权威"一词要表达的取舍。官方还说了一句反直觉的：表里标了 `session` 作用的集成（下面会讲）**有意不是**生命周期权威——它们提供原生会话身份用于恢复，但钩子覆盖不全生命周期，可能漏掉权限批准结果、Esc 中断等转折，所以这类智能体仍然走屏幕清单检测。

对屏幕清单类智能体，`blocked` 的判定刻意从严：只有当底部快照**精确命中**已知的审批/提问/权限 UI 时才标 `blocked`；没有规则命中时退回 `idle`，并在 `explain` 输出里把这个回退标成 `default_known_agent_idle_fallback`。代价是：某种从未见过的智能体提示，一开始可能显示成 `idle` 而不是 `blocked`，直到 herdr 学到那个界面形状。官方明确说这只会影响可见状态和等待，不会因此误发输入或执行破坏性操作。

想看某个状态判错了的成因，用 `herdr agent explain`：

```bash
herdr agent explain <target>
herdr agent explain --file screen.txt --agent codex --json
```

输出会列出：智能体、最终状态、屏幕检测是否被完整生命周期权威跳过、清单来源与版本、本地覆盖是否遮蔽、远程更新状态、命中的规则、可见证据标志、`idle` 回退原因等。它由运行中的服务器求值，反映的是当前活跃的清单缓存，不是文件里的静态文本。

## 22 种开箱即用：识别靠什么，集成管什么

官方文档给了一张 22 行的表，标记哪些信号决定每个智能体的 `idle/working/blocked`，以及集成扮演什么角色。它比"支持多少种"更有用——同一列里藏着两种权威的分布：

| 智能体 | 状态由什么决定 | 集成角色 |
|:---|:---|:---|
| Pi | 装了则为生命周期钩子，否则屏幕清单 | state + session |
| OMP | 生命周期钩子（装了） | state + session |
| GitHub Copilot CLI | 屏幕清单 | session |
| Devin CLI | 屏幕清单 | session |
| Kimi Code CLI | 生命周期钩子（装了），否则屏幕清单 | state + session |
| Hermes Agent | 屏幕清单 | session |
| Qoder CLI | 屏幕清单 | session |
| Qwen Code | 屏幕清单 | session |
| Letta Code | 屏幕清单 | session |
| Droid | 屏幕清单 | session |
| OpenCode | 生命周期插件（装了），否则屏幕清单 | state + session |
| Kilo Code CLI | 生命周期插件（装了），否则屏幕清单 | state + session |
| MastraCode | 生命周期钩子（装了） | state + session |
| Claude Code | 屏幕清单 | session |
| Codex | 屏幕清单 | session |
| Cursor Agent CLI | 屏幕清单 | session |
| Amp | 屏幕清单 | none |
| Grok CLI | 屏幕清单 | session |
| Antigravity CLI | 屏幕清单 | session |
| Kiro CLI | 屏幕清单 | none |
| Maki | 屏幕清单 | none |
| Muse | 屏幕清单 | none |

两个细节值得记：`Amp`/`Kiro`/`Maki`/`Muse` 这类标 `none` 的已能识别、但集成不参与会话恢复；文档还点名 Gemini CLI 与 Cline 属"被检测但测试得较少"。标了 `session` 而不标 `state` 的集成，正是上一节说的"有意非生命周期权威"——这是把 22 种智能体分成"完整钩子""屏幕清单"两类权威的直接证据。

集成是可选装的，`none` 到 `state+session` 的差别正是识别精度与恢复能力的差别：

```bash
herdr integration install claude   # 给当前正在用的智能体装官方集成
herdr integration status           # 查已装集成版本，过旧可重装
```

自定义一个智能体可以用 `HERDR_AGENT` 环境变量。Linux/macOS 上，宿主可见的 wrapper 会藏掉真实智能体进程，在 wrapper 命令上设 `HERDR_AGENT=<agent>` 即可让 herdr 复用已知清单——例如 `HERDR_AGENT=claude fence -- claude`（Linux）或 `HERDR_AGENT=claude nono run --profile claude-code -- claude`（macOS）。这个提示只作用于当前前台进程；在 VM 或容器内部设它，宿主的 herdr 看不到。另一条相关的服务器级变量是 `HERDR_PROCESS_DETECTION=child-groups`，供某些不暴露终端前台进程组的受限 Linux 运行时开启直接子进程组推断（默认 `native` 永不推断，且此变量要重启服务器生效）。

## 检测清单：内置、远程更新、本地覆盖三层

识别规则不是一个写死的文件，而是可更新的三层，优先级从高到低：

1. **本地覆盖**：`~/.config/herdr/agent-detection/<agent>.toml`（debug 构建可能用 `herdr-dev` 目录）。本地覆盖**永远胜出**；无效文件会被忽略并告警，回退到下面两层。
2. **远程清单**：herdr 会去 herdr.dev 拉远程清单更新，命中后自动应用于已知智能体的规则，无需重启。远程清单存在 herdr 的状态目录里；想关掉用 `[update] manifest_check = false`。
3. **内置清单**：随二进制分发，作为没有本地覆盖时与远程清单里"较新且兼容"者的基准。

远程清单能补丁"herdr 已经认识"的智能体的检测规则；要新增一个她完全不认识的智能体，仍需一次二进制更新来带进程检测、标签与集成行为。运行中的服务器启动时把活跃清单加载进内存，远程更新写好后会重载缓存；手动喂本地覆盖后可用 `herdr server reload-agent-manifests` 让运行中的服务器立即应用，`herdr server update-agent-manifests` 则立刻拉远程更新并重载。

两个边界提醒：一是 herdr 可以跑在 tmux 外层，但它**不会**去检测 herdr 窗格内部再套的 tmux 会话——如果某个 shell 框架在 herdr 窗格里自动进了 tmux，herdr 看到的窗格进程是 `tmux` 而不是背后的智能体；二是"加新智能体要等二进制更新"意味着你永远不能只靠清单就让一个全新 agent 被识别。

## 三份接入：从布局到智能体逐层递进

把智能体当客户端的接口分三层，共用同一套控制面，大多数自动化从 CLI 起就够。`HERDR_ENV=1` 时，智能体知道自己在 herdr 管理的窗格里运行，可以开始用 herdr 的能力；`npx skills add herdrdev/herdr --skill herdr -g` 把技能装进任何支持 skills 的智能体，`herdr --skill` 打印与当前二进制版本匹配的技能副本。

- **布局组**管拓扑：创建工作区、加标签、分割窗格。
- **窗格组**管终端控制：在已存在窗格里执行命令、发按键、读输出、等特定输出出现。这是智能体与终端交互的原语。
- **智能体组**管生命周期：按名启动智能体、发 prompt、等它进入特定状态、读它的输出。这一层让"智能体控制智能体"成为可能。

一个可复现的编排例子（摘自官方 Agent Skill 的命令形态）：

```bash
herdr workspace create --cwd ~/my-project --label "review-session"
herdr tab create --workspace w1 --label "reviewers"
herdr pane split --current --direction right --cwd "$PWD"
herdr pane split --current --direction down --cwd "$PWD"
herdr agent start security-reviewer --kind codex --pane w1:p1
herdr agent start style-reviewer --kind codex --pane w1:p2
herdr agent prompt security-reviewer "审查所有认证相关代码的安全风险" --wait --timeout 120000
```

`--wait` 的语义是等到智能体进入第一个稳定的 `idle`、`done` 或 `blocked` 状态；提交后迟迟观察不到它开始工作，会以 `agent_prompt_stalled` 返回，避免空等。读取输出用 `herdr agent read <name> --source recent-unwrapped --lines 120`；若干智能体都 `done` 后，可再起一个"编排者"智能体依次等待、读取、汇总——链式编排完全可编程。

安全边界是内置的几条硬规则：先查 `HERDR_ENV=1`，不在 herdr 窗格里就停止；不关闭不是自己创建的工作区/标签/窗格；不从活动会话里 `herdr server stop`。这保证了多智能体协作不会互相拆台。

## Session State：四条恢复路径，各自一个文件

这是 herdr 最值得逐项读的部分——"服务器重启了，智能体进度怎么办"在这种面向长任务的工具里直接决定可用性。文档按"什么幸存了什么"给了四张并列的场景表：

| 场景 | 进程存活 | 布局恢复 | 屏幕历史回放 | 对话恢复 |
|:---|:---|:---|:---|:---|
| 分离/重连 | ✅ | ✅ | ✅，来自实时终端 | ✅，进程没停 |
| 服务器重启 | ❌ | ✅ | 仅开了 pane history | 仅原生会话恢复 |
| 更新（无 `--handoff`） | 兼容版服务器保持运行 | ✅（重启后） | 仅 pane history | 仅原生会话恢复 |
| 更新（有 `--handoff`） | 尽力迁移 | ✅ | ✅（handoff 成功） | ✅（进程没停） |

四条路径各有落点，可以当四个文件来记：

1. **Live persistence（最强）**：正常分离只停客户端，服务器、窗格、shell、智能体、测试全继续在服务器里跑。`ctrl+b q` 分离、`herdr` 重连。这是唯一"原进程从未停止"的路径。
2. **Snapshot restore（布局回流）**：服务器停了，窗格进程没了。herdr 从 `session.json` 恢复形状——工作区、标签、窗格、cwd、布局、焦点；恢复不回来的窗格以新 shell 回到原目录。要点：`session.json` 读不出或版本过新时，herdr 会在保存/清空前把原字节备份到 `session-backups/` 并记 `persist.backup`，只保留最近三份回收副本，且恢复副本**不会**自动还原、也不含 pane history。
3. **Pane screen history（屏幕回放）**：默认关，因窗格输出可能含密钥、token、prompt。开启后存在 `session-history.json`（紧邻 `session.json`），并把它当终端历史对待：

   ```toml
   [experimental]

   pane_history = true
   ```

4. **Native agent session restore（对话接回）**：默认**开**，用集成上报的原生会话引用，在服务器重启后重新拉起可续期的智能体窗格。想关掉：

   ```toml
   [session]

   resume_agents_on_restore = false
   ```

   它只续那些通过**当前官方集成**上报过原生会话引用的窗格，接回手段是各智能体自己的 resume 命令。文档给了一张 18 行的表，把每种智能体的最低 herdr 集成版本与续期命令都列了出来，值得整表抄走：

   | 智能体 | 最低集成版本 | 续期命令 |
   |:---|:---|:---|
   | Claude Code | 6 | `claude --resume <id>` |
   | Codex | 5 | `codex resume <id>` |
   | Cursor Agent CLI | 1 | `cursor-agent --resume <id>` |
   | OpenCode | 5 | `opencode --session <id>` |
   | Grok CLI | 2 | `grok --resume <id>` |
   | GitHub Copilot CLI | 2 | `copilot --resume=<id>` |
   | Devin CLI | 2 | `devin --resume <id>` |
   | Kimi Code CLI | 3 | `kimi --session <id>` |
   | Qwen Code | 1 | `qwen --resume <id>` |
   | Kilo Code CLI | 1 | `kilo --session <id>` |
   | Hermes Agent | 2 | `hermes --resume <id>` |
   | Pi | 2 | `pi --session <path-or-id>` |
   | Antigravity CLI | 1 | `agy --conversation <id>` |
   | OMP | 3 | `omp --resume=<path-or-id>` |
   | Droid | 2 | `droid --resume <id>` |
   | Letta Code | 1 | `letta --conversation <id>` |
   | MastraCode | 1 | `mastracode --thread <id>` |
   | Qoder CLI | 2 | `qodercli --resume <id>` |

   不支持、缺失、无效、重复或过期的会话引用，会以普通 shell 回到保存窗格的目录；能续的窗格优先续会话而非回放历史。`herdr integration status` 可查集成版本，过旧用 `herdr integration install <agent>` 重装。

**Live handoff** 是另一回事——它面向"更新 / 远程挂载要换掉运行中的服务器"时**尽量不让进程断**，与上面四条"重建状态"在语义上正好相反。`herdr update --handoff` 请求旧服务器把活动的窗格 PTY、进程、智能体身份与元数据、以及插件/会话状态转交给新服务器；它**不**保留跨替换边界的临时协调——正在进行的 CLI/API 请求、等待、订阅流、客户端 socket、窗格间消息都可能被中断，客户端需重连重试。两个限制：handoff 是实验性 opt-in；且只有 herdr 自管更新生效（Homebrew/mise/Nix 走包管理器，`herdr update` 被禁用，做不了 handoff）。更新版 Unix 服务器可以成批一次转移超过 64 个窗格，但旧服务器自身仍执行 64 块上限。

## 远程：几台机器，一个窗口

远程机器是 9 月版本重点强化的场景。官方路径是先把机器存成配置，再从本地窗口直连：

```bash
herdr machine add workbox --label "Build machine"   # 交互式确认，可自动装远端
herdr --remote workbox                              # 本地窗口直连远端，键位走本地配置
```

每台机器有独立的服务器、会话和进程，一台断线不影响其他。脚本与智能体也能用 `herdr --machine workbox ...` 把单条命令转发到远端。`herdr --remote workbox --handoff` 则把 live handoff 也搬到远端。

## 跟 tmux 的关系

herdr 公开继承了 tmux 的设计遗产：前缀键模型、分离/重连、窗格分割。个别键位是**有意重排**的——分屏是 `v`/`-`，分离是 `q` 而不是 `d`。差异在三维度：

- **智能体感知**：tmux 把窗格当无差别字符流；herdr 识别 22 种智能体、维护五种状态、侧栏实时聚合。
- **鼠标原生**：文档把键鼠并列为两种第一等输入，鼠标支持默认开；tmux 鼠标默认关、定位是键盘补充。无优劣，纯键盘流的人用 tmux 模型依然顺手。
- **面向程序的接口**：这是最大差异。tmux 有控制模式（`tmux -C`），但设计目标是被**人**操作。herdr 的 CLI + Socket API 是为智能体编排设计的，从建拓扑到控智能体的完整操作链都有覆盖。

换个说法：tmux 是给人用的终端复用器，herdr 是给人和智能体一起用的终端复用器。

## 插件生态

插件是带 `herdr-plugin.toml` 清单的目录，实现语言不限——Bash、JavaScript、Lua、Rust 二进制都可以；官方明确"整个 herdr CLI 就是插件的 API"，市场在 <https://herdr.dev/plugins/>。生态已有第三方插件：只读文件树侧栏、针对 herdr 的 diff 审查侧栏、在窗格里渲染 Chromium 的浏览器插件、从菜单栏或手机遥控智能体的工具等。信任模型和编辑器扩展同级：装第三方插件前先审它的清单与脚本——它有权触达你的终端环境与 herdr 控制面。

## 安装与上手

安装（与官方 install 完全一致）：

```bash
curl -fsSL https://herdr.dev/install.sh | sh     # 官方脚本
brew install herdr                              # 或 Homebrew
mise use -g herdr                                # 或 mise
# Windows（beta）：
powershell -ExecutionPolicy Bypass -c "irm https://herdr.dev/install.ps1 | iex"
```

然后到工作目录启动：`herdr` 会连默认会话；命名会话用 `herdr session list` / `herdr session attach <name>`，它们是完全独立的运行时命名空间（独立的窗格、socket 与持久化状态）。分离 `ctrl+b q`，重连再跑一次 `herdr`。在窗格里直接跑 `claude` 或 `codex`，herdr 自动检测并开始跟状态，不需要额外配置。

## 复核口径与失效条件

本文每条事实都能在公开处复现：仓库数字用 `gh api repos/herdrdev/herdr`（期望 39,460 stars / 2,974 forks / 最近推送 2026-09-18 / master 分支）；其余架构、状态机、命令、配置键逐条对 `herdr.dev/docs/` 的 concepts、agents、session-state、remote、configuration 各页；集成与 resume 命令表对 session-state 页；22 种智能体及状态权威表对 agents 页。

六处最可能随版本漂移，重看本文优先查它们：默认分支是否仍是 `master`；22 种智能体清单与 `state+session`/`session`/`none` 的集成角色分布；原生会话恢复的集成表是否新增/改了 resume 命令；`handoff` 是否转正（转正则不再算实验性 opt-in）；`pane_history`/`resume_agents_on_restore`/`mouse_capture` 三个配置键是否改名；以及 64 块窗格的 handoff 批量上限是否被取消。星标数、版本号、issue 数每次都可能变，正文里的值只作 2026-09-18 的这一份快照。