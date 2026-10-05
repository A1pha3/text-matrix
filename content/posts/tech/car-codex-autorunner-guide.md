---
title: "CAR（Codex Auto-Runner）拆解：把 Ticket 队列当控制平面的智能体协调框架"
date: "2026-03-31T12:40:00+08:00"
lastmod: "2026-09-29T00:00:00+08:00"
slug: "car-codex-autorunner-guide"
github_repo: "Git-on-my-level/codex-autorunner"
source_key: "gh:Git-on-my-level/codex-autorunner"
description: "CAR（codex-autorunner）不是又一个编码智能体，而是给 Codex、OpenCode、Hermes、OMP 这些现成智能体套上的执行框架：计划写成 Ticket 文件，状态机按文件名顺序把任务喂给智能体，人只在与要输入时被 Telegram/Discord 叫醒。本文拆解它的四层架构、Ticket 机制、状态落盘设计与上手路径，并给出适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["Codex", "OpenCode", "AI智能体", "自动化"]
---

# CAR（Codex Auto-Runner）拆解：把 Ticket 队列当控制平面的智能体协调框架

## 核心判断

CAR 要解决的问题很具体：你已经有了顺手用的编码智能体（Codex、OpenCode、Hermes、OMP），但让它跑一个跨几天的大任务时，你得一直盯着——上下文会溢出，进程会断，进度会丢。CAR 的答案是自己不当智能体，而是做一层"元协调"（README 原话是 meta-harness for coding agents）：把计划拆成一批 Markdown Ticket 文件，状态机循环地取下一个未完成任务喂给智能体，人只在智能体需要输入时收到 Telegram/Discord 通知。

它的架构立场浓缩在 README 的一句话里：*Tickets are the control plane. Agents are the execution layer.* 任务队列本身是可编辑、可版本控制的文件系统状态，智能体只是无状态的执行器。这带来一个直接推论——CAR 是放大器而不是保险器：模型强，它跑得欢；模型会偷懒或者把没做完的 Ticket 标成完成（README 用的词是 reward-hacks），CAR 不会替你兜住。

本文以 v2.2.3（2026-06-25 发布）为口径，关键事实核实于 2026-09-29。项目迭代很快（2026 年 5 月刚发布过 UI 重写的 v2.0.0），命令行细节以你安装版本的 `car --help` 为准。

## 目录

- [项目坐标](#项目坐标)
- [系统地图：四层架构与两级部署](#系统地图四层架构与两级部署)
- [Ticket 机制：编号即顺序](#ticket-机制编号即顺序)
- [一个 Ticket 的完整流转](#一个-ticket-的完整流转)
- [状态与数据：文件系统是唯一真相](#状态与数据文件系统是唯一真相)
- [三种交互面与 PMA](#三种交互面与-pma)
- [智能体集成与扩展](#智能体集成与扩展)
- [安装与上手](#安装与上手)
- [Telegram 与 Discord 集成](#telegram-与-discord-集成)
- [采用顺序与边界](#采用顺序与边界)
- [常见问题](#常见问题)
- [参考资源](#参考资源)

## 项目坐标

| 维度 | 数据 |
|------|------|
| 仓库 | Git-on-my-level/codex-autorunner |
| Stars / Forks | 878 / 73（2026-09-29 读数） |
| 最新版本 | v2.2.3（2026-06-25 发布） |
| 提交 / 贡献者 | 约 2,090 commits / 7 人 |
| 许可证 | MIT |
| 语言 | Python 约 91%，TypeScript 约 5.8%，Svelte 约 2.3%（字节占比） |
| Python 要求 | ≥ 3.10（pyproject.toml `requires-python`） |
| 安装 | `pipx install codex-autorunner`（PyPI 包名 codex-autorunner，命令名 `car`） |
| 技术栈 | Typer（CLI）、FastAPI + Svelte（Web UI）、SQLite（状态） |

三个读数值得展开。其一，这是个单人主导的项目——release notes 里列的 PR 几乎全部由 Git-on-my-level 一人提交，而且发版密集，2026 年 4 月到 6 月两个月间发了 15 个版本，v1.11.x 到 v2.2.x 之间没有断档。其二，Web 前端是 Svelte 写的，源码在 `src/codex_autorunner/web_frontend/`，构建产物落在 `web_static/`——看到"Svelte"别意外，Python 占比高是因为前端是编译后静态托管。其三，v2.0.0（2026-05-20）是一次 Major UI Rewrite，网上早于 5 月的 CAR 截图和教程大概率已过时。

## 系统地图：四层架构与两级部署

官方架构文档（`docs/ARCHITECTURE_BOUNDARIES.md`）把代码切成四层，依赖严格单向：

```mermaid
flowchart LR
    A["Surfaces<br/>Hub / Web UI / CLI / Telegram / Discord"] --> B["Adapters<br/>GitHub / Telegram / App Server"]
    B --> C["Control Plane<br/>.codex-autorunner/ 文件 + tickets/"]
    C --> D["Engine<br/>core/ 核心循环、状态、锁"]
```

- **Engine**：`src/codex_autorunner/core/`。核心执行循环、状态和锁都在这层，官方要求它保持稳定、可被整体替换的只有外层。
- **Control Plane**：不是一个服务，而是 `.codex-autorunner/` 目录里的一组文件（Ticket 队列、contextspace 文档、SQLite 库），实现在 `src/codex_autorunner/tickets/`。这就是"控制平面"的字面意思——数据在磁盘上，不在进程里。
- **Adapters**：对接外部世界的通道（GitHub SCM 自动化、Telegram、Discord、Codex app-server）。
- **Surfaces**：人（和智能体）接触 CAR 的入口——Hub、Web UI（FastAPI 路由 + Svelte 前端）、CLI（Typer 命令）、聊天应用。

部署上有两级概念，这是上手前最该分清的一件事：

- **Hub**（推荐模式）：一个中心目录，管理多个仓库。`car init --mode hub` 生成的结构包含 `manifest.yml`（受管仓库清单）、`config.yml`、默认的 `repos/` 目录。Web UI 由 Hub 提供，默认端口 8765。
- **Repo**：被管理的单个仓库，各自有 `.codex-autorunner/` 目录存 Ticket、contextspace 和状态。单仓库模式主要用于开发 CAR 本身，官方安装指南明说"不推荐一般用户使用"。

## Ticket 机制：编号即顺序

Ticket 就是 Markdown 文件，放在 `<repo>/.codex-autorunner/tickets/` 下，文件名格式 `TICKET-###*.md`（如 `TICKET-001.md`、`TICKET-120-api-parity.md`）。官方的 CAR Ticket Skill 文档（`docs/car-ticket-skill.md`）给出了可直接贴给任意 AI 助手的格式契约：

```markdown
---
title: "登录接口返回规范化"
agent: "codex"
done: false
goal: "所有 /api 返回统一 error code 和 message 结构。"
---

## Tasks
- 抽出公共响应构造函数
- 替换各 handler 的裸返回

## Acceptance criteria
- 错误响应均含 code 与 message 字段

## Tests
- pytest tests/api/test_responses.py
```

必填字段只有三个，且会被 linter 检查：`ticket_id`（稳定逻辑标识，正常由 CAR 写入流程自动生成）、`agent`（仓库里注册的智能体 id，如 `codex`、`opencode`，或特殊值 `user` 表示人工签收）、`done`（布尔值）。可选字段有 `title`、`goal`、`model`。

执行顺序的规则只有一条：**按文件名编号升序，取第一个 `done != true` 的 Ticket**。前置任务放在编号更小的文件里，编号可以留空洞方便日后插队。这里有个容易踩的坑：2026-02-07 起 `depends_on` 字段被移除（`docs/migrations/depends-on-removal.md`），linter 会直接拒绝带这个字段的 Ticket——如果你在其他教程里看到用 `depends_on` 表达依赖的 CAR 示例，那是移除前的旧机制，现在依赖关系只能用编号顺序表达，或者在正文里写清楚。

这和我们熟悉的看板工具（Jira 之类）是两种东西：没有拖拽排序，没有依赖图，就是文件名的字典序。代价是表达力，收益是任何编辑器、任何智能体、`git diff` 都能直接操作任务队列——这正是它"文件系统是唯一真相"哲学的落点。

## 一个 Ticket 的完整流转

把机制串起来看一次真实运行。假设 Hub 已经管着一个仓库，里面有 `TICKET-001.md` 到 `TICKET-003.md` 三个未完成任务：

1. **启动**：在仓库里执行 `car ticket-flow bootstrap`（播种 Ticket 并启动）或 `car ticket-flow start`（启动/恢复最近的 flow）。
2. **选票**：状态机扫描 `tickets/` 目录，按编号升序找到第一个 `done: false` 的，这里是 TICKET-001。
3. **组装提示词**：智能体收到的输入由四部分组成——CAR 自身的操作知识（怎么汇报完成、怎么拆子任务）、该仓库 `contextspace/` 目录的预定义上下文、当前 Ticket 正文、以及（可选）上一个智能体的最终输出。
4. **执行**：按 Ticket 的 `agent` 字段唤起对应智能体（Codex 走 app-server，Hermes/OMP 走 ACP——Agent Client Protocol，一个跨厂商的智能体对接协议），在仓库或工作树里干活。
5. **收尾**：Ticket 被标记 `done: true` 后状态机取下一张票，循环往复。智能体也可以在运行中创建新 Ticket，把大任务拆成后续编号的子任务。
6. **停止条件**：官方架构文档列出的停止规则包括退出码、`stop_after_runs` 等限制。一个值得知道的细节：如果当前 Ticket 标了 `done: true` 但工作树还有未提交改动，CAR 会把它拦在 commit barrier 后面不往前走。

中途崩了怎么办？运行元数据和崩溃产物存在 `.codex-autorunner/flows/<run_id>/` 下作为证据，恢复决策只由 supervisor/reconciler 这条路径负责。卡在活跃 run 上时，`car ticket-flow status --json --repo <path>` 先看冲突 run 是否健康，确认僵死（`worker.status: absent`）才用 `--force-new`。

## 状态与数据：文件系统是唯一真相

CAR 的状态散落在几个约定位置，全部可以 `git` 管、肉眼查：

```
<hub-root>/
├── codex-autorunner.yml          # 默认配置（提交进 git）
├── codex-autorunner.override.yml # 本地覆盖（gitignore）
├── .codex-autorunner/            # Hub 状态
│   ├── manifest.yml              # 受管仓库清单
│   ├── config.yml
│   ├── orchestration.sqlite3     # 编排元数据、线程绑定、投递账本
│   └── templates/                # Hub 级模板
├── repos/<name>/.codex-autorunner/
│   ├── tickets/                  # TICKET-###.md 队列（必需）
│   ├── contextspace/             # active_context.md / decisions.md / spec.md（可选）
│   ├── config.yml
│   ├── state.sqlite3             # 仓库运行时状态
│   ├── flows.db                  # flow 引擎执行史（flow_runs/flow_events/flow_artifacts 三表）
│   ├── flows/<run_id>/           # 运行工件与崩溃证据
│   └── telegram_state.sqlite3 / discord_state.sqlite3
└── ~/.codex-autorunner/          # 全局：更新缓存、共享 app-server 工作区
```

配置优先级也有明确的链：内置默认 < `codex-autorunner.yml` < override < `.codex-autorunner/config.yml` < 环境变量。

contextspace 值得多说一句。它是每个仓库的三份共享文档：`active_context.md` 放短期上下文（当前这轮活儿干什么）、`decisions.md` 放持久的架构与产品决策、`spec.md` 放需求规格。人和智能体都能读写，Web UI 里也能编辑。实践上它就是"给智能体的长期记忆"——比每次把背景塞进提示词省事，也比塞进提示词可靠，因为改了就是改了，`git log` 可查。

`flows.db` 的表结构（`flow_runs`、`flow_events`、`flow_artifacts`）在 `docs/RUN_HISTORY.md` 里有契约定义，`flow_events` 用单调递增的 `seq` 排序，做外部看板或审计工具时直接查这套表即可。

## 三种交互面与 PMA

| 交互面 | 定位 | 适用 |
|--------|------|------|
| Web UI | 主控制平面。加仓库、聊智能体、跑 flow、看用量都从这里开始 | 默认入口，`car serve` 后开 http://localhost:8765 |
| CLI | 智能体友好的入口。README 直说"不太是给人用的" | 让 AI 助手替你操作 CAR、写脚本 |
| Telegram / Discord | 多设备持久聊天，不需要把 Hub 暴露到公网 | 手机上盯任务、远程批准 |
| PMA | 对话式管理 CAR 自身的界面，Web UI 和聊天应用里都可用 | 用自然语言建票、管仓库、派活 |

PMA（Project Manager Agent）值得一节。它是"管理者的智能体"：你说"把这个特性拆成票、明早跑完"，它替你操作 CAR。README 特别推荐 Hermes 做 PMA，理由是 Hermes 通过共享的 `HERMES_HOME` 维护跨会话全局记忆——它能记住你所有 CAR 项目的偏好和模式，换项目不用重新教。在 v2 的 Web UI 里，`/pma` 就是默认落地页，官方安装指南称其为"primary web experience"。

Web UI 还有些锦上添花的能力：语音输入（Whisper，依赖 `voice` extras，Apple Silicon 上有 `voice-mlx`）、内置终端、用量统计（`car usage`）。安全上要注意 Web UI 能操控你机器上的智能体进程，暴露前先读 `docs/web/security.md`。

## 智能体集成与扩展

开箱支持四个智能体，README 的现行清单：

- **Codex**：一线支持，功能最全（走 OpenAI 的 app-server 协议）
- **OpenCode**：开源替代，无审批流的 repo/worktree 运行时
- **Hermes**：ACP 后端，持久线程、审批、事件流俱全
- **OMP**（Oh My Pi）：ACP 后端，原生持久会话（`~/.omp/agent`）

关键设计是 **CAR 检测已配置的运行时，但不负责安装它们**。四个智能体都得先装好并在 PATH 里可执行——官方检查命令是 `codex --version`、`opencode --version`，ACP 系的还要 `hermes acp --help`、`omp acp --help` 能跑通。

扩展新智能体走 Harness 模型，`docs/adding-an-agent.md` 有完整教程。每个智能体集成由三部分组成：**Harness**（底层协议客户端包装，继承 `AgentHarness` 基类，实现 `new_conversation`、`resume_conversation`、`model_catalog` 等接口）、**Supervisor**（管理子进程生命周期）、**Registry**（集中注册并声明能力）。代码放在 `src/codex_autorunner/agents/<name>/harness.py`，现成的参考实现就在同目录的 `codex/`、`hermes/`、`omp/`、`opencode/` 里。

前置门槛值得注意：CAR 的持久线程契约要求智能体支持创建、恢复、执行回合这三类会话操作。单会话或易失性的包装式运行时（聊完即丢那种）被明确划为 v1 编排的范围之外。ACP 协议本身由 [agentclientprotocol/agent-client-protocol](https://github.com/agentclientprotocol/agent-client-protocol) 维护（原 zed-industries 仓库已迁移至该组织）。

## 安装与上手

```bash
# 安装（pipx 推荐，pip 亦可）
pipx install codex-autorunner
car --version

# 初始化 Hub
mkdir ~/car-hub && cd ~/car-hub
car init --mode hub

# 体检：验证配置和智能体可用性
car doctor

# 起服务，浏览器开 http://localhost:8765
car serve
```

然后在 Web UI 里添加仓库（扫描本地 git 仓库 / 从 URL 克隆 / 新建），或者走 CLI：

```bash
car hub clone <你的仓库URL>   # 从远端克隆
car hub create my-new-project # 在 Hub 里新建
car hub scan                  # 发现 Hub 目录附近的既有仓库
```

跑任务用 ticket-flow 命令组（在仓库内执行，或用 `--repo` 指定）：

```bash
car ticket-flow bootstrap   # 播种 Ticket 并启动
car ticket-flow start       # 启动/恢复（元数据僵死时才用 --force-new）
car ticket-flow status      # 看进度
car ticket-flow stop        # 停止
```

写计划这步官方推荐的路径很实用：把 [CAR Ticket Skill](https://github.com/Git-on-my-level/codex-autorunner/blob/main/docs/car-ticket-skill.md) 文档连同你的实现计划一起贴给任意 AI 助手，让它按格式契约产出 `TICKET-###.md` 文件。另外还有一条"让智能体帮你装"的路径：把 `docs/AGENT_SETUP_GUIDE.md` 的链接发给 Codex/Cursor 等助手，它会交互式地引导完成安装配置。

想让某个仓库的智能体跑在容器里（隔离依赖、锁定环境），配 Docker 执行目标：

```bash
car hub destination set <repo_id> docker --image <registry/image:tag> --path <hub_root>
car hub destination show <repo_id>   # 验证生效
```

高级参数（`--profile`、`--mount`、`--env-map` 等）见 `car hub destination set --help` 与 `docs/configuration/destinations.md`。注意 Docker 在 CAR 里是**执行目标**而不是安装方式——PyPI 包加源码 shim 就是全部安装形态，Docker Hub 上没有官方 CAR 镜像。

## Telegram 与 Discord 集成

两个聊天面的定位是"不把 Hub 暴露到公网的多设备入口"，配置路径大同小异，以 Telegram 为例：

1. **装 extras**：Telegram/Discord 依赖是可选的，pipx 用户要重装——`pipx uninstall codex-autorunner && pipx install "codex-autorunner[telegram]"`。
2. **建 Bot**：BotFather `/newbot` 建机器人，然后 `/setprivacy` 选 **Disable**——隐私模式开着时群聊里 Bot 只收得到斜杠命令，收不到普通消息，而 CAR 的对话回合需要普通消息。
3. **选拓扑**：个人模式（DM 或单人专用 topic）开箱即用，配基本 allowlist 就行；协作模式（多人共享超级群组/guild）要配 `collaboration_policy.*`，按 topic/channel 指定 `active`、`command_only` 或 `silent`。
4. **激活**：个人模式下用 `/bind` 或 `/pma on` 激活会话，然后就能在聊天里对话、收通知、批准操作。

官方建议 Telegram 和 Discord 二选一。运行层面有现成的服务单元模板（`docs/ops/systemd-*.service`，macOS 有 launchd 示例），适合把 Hub 挂成常驻服务。

## 采用顺序与边界

适合先用起来的团队和场景：

- 已经重度使用 Codex/OpenCode 等智能体，痛点明确是"盯人式"监督——每个回合都要人确认才能继续；
- 有可以拆成一批独立可验证子任务的工作：特性开发、技术债偿还、批量重构、测试补齐；
- 乐于把任务队列当 git 里的文件管理，接受"编号即顺序"的简单调度；
- 想要手机上远程批准和通知，但不想把 Web 服务暴露公网。

可以先等等的：

- 依赖复杂依赖图和优先级调度的团队——Ticket 流程只有文件名顺序，`depends_on` 已移除，看板式工作流别硬套；
- 模型能力偏弱或不可靠的场景——README 的警告值得原样记住：模型会 scope-creep 或 reward-hack（把没做完的票标成做完），CAR 是放大器，不会纠偏。用 `user` agent 的收尾票做人工签收是官方给的缓解手段；
- 需要 Windows 原生环境的——pyproject 声明 OS Independent，但官方文档的操作面基本是 macOS 与 Linux（systemd/launchd 单元、VM/CI 环境说明），Windows 无专门文档，想用先备好 WSL 或容器；
- 想要多人权限隔离、审计合规这类"企业特性"的——项目没有这层，单人或小团队互信环境下用。

上手顺序建议：先用 pipx 装上跑通 `car init --mode hub` + `car doctor` + `car serve`，在 Web UI 里对一个玩具仓库跑通三张票的 flow；顺手了再接 Telegram；最后才是把真实项目的计划和 contextspace 文档喂进去。

## 常见问题

**CAR 和直接用 Codex/OpenCode 的区别？** 智能体管单次对话，CAR 管任务队列：进度落在文件系统和 SQLite 里，进程断了能恢复；多个任务自动轮转，不用人挨个发起；任务完成或卡住时主动通知，而不是等人盯。

**需要多强的模型？** CAR 自己不做推理，效果上限取决于你接的智能体。官方口径是"强模型上如虎添翼，会爬边界或刷完成的模型上不会有用"——没有具体型号推荐，用自己的主力编码模型即可。

**离线能用吗？** 核心循环完全本地：Ticket、contextspace、状态库都在本机磁盘。需要网络的只有三样——智能体本身的模型调用、Telegram/Discord 通知、从远端克隆仓库或拉模板。

**Ticket 模板去哪找？** 作者维护了一组"blessed templates"：[Git-on-my-level/car-ticket-templates](https://github.com/Git-on-my-level/car-ticket-templates)，任何 CAR 部署都能取用。跑顺了自己的通用票也可以往回贡献。

**怎么报告问题？** 走 [GitHub Issues](https://github.com/Git-on-my-level/codex-autorunner/issues)。上手卡住先跑 `car doctor`，大部分配置问题它会直接指出来。

## 参考资源

- 仓库：<https://github.com/Git-on-my-level/codex-autorunner>
- PyPI：<https://pypi.org/project/codex-autorunner/>
- 安装指南（可整份发给 AI 助手）：[docs/AGENT_SETUP_GUIDE.md](https://github.com/Git-on-my-level/codex-autorunner/blob/main/docs/AGENT_SETUP_GUIDE.md)
- Ticket 格式契约：[docs/car-ticket-skill.md](https://github.com/Git-on-my-level/codex-autorunner/blob/main/docs/car-ticket-skill.md)
- 架构边界：[docs/ARCHITECTURE_BOUNDARIES.md](https://github.com/Git-on-my-level/codex-autorunner/blob/main/docs/ARCHITECTURE_BOUNDARIES.md)、[架构地图](https://github.com/Git-on-my-level/codex-autorunner/blob/main/docs/car_constitution/20_ARCHITECTURE_MAP.md)
- 运行历史契约：[docs/RUN_HISTORY.md](https://github.com/Git-on-my-level/codex-autorunner/blob/main/docs/RUN_HISTORY.md)
- 扩展智能体：[docs/adding-an-agent.md](https://github.com/Git-on-my-level/codex-autorunner/blob/main/docs/adding-an-agent.md)、[插件 API 契约](https://github.com/Git-on-my-level/codex-autorunner/blob/main/docs/plugin-api.md)
- Ticket 模板集：<https://github.com/Git-on-my-level/car-ticket-templates>
