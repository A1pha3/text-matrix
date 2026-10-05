---
title: "CC-Connect：把本地 AI 编程 Agent 接进聊天软件的桥接器"
date: "2026-04-12T02:31:39+08:00"
lastmod: 2026-10-04
slug: cc-connect-multi-platform-ai-agent-bridge-guide
github_repo: "chenhg5/cc-connect"
source_key: "gh:chenhg5/cc-connect"
description: "CC-Connect 用出向长连接把 Claude Code、Codex、Gemini CLI 等本地 Agent 桥接进飞书、Telegram、微信等 13 个聊天平台，免公网 IP；真正值得学的是它以聊天软件为主界面的会话、权限与安全隔离设计。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Go", "IM 集成"]
hiddenFromHomePage: false
---

Claude Code、Codex 这类 Agent 的算力在你的机器上，人却经常不在——通勤、吃饭、开会的间隙想让它继续干活，隔着终端就是够不着。CC-Connect 解决的就是这最后一公里：它是一个 Go 写的桥接进程，把本地 Agent 的输入输出转接到聊天软件里，你在群里发一句"帮我看看这个报错"，它转给本机的 Claude Code，再把回答发回群里。

这个项目 2026 年 2 月 28 日建仓，本文初版写于 4 月 12 日，当时是 7 个 Agent、10 个平台、v1.2.1。到 2026-10-04 复核时它已经长到 15,747★、1,595 forks、183 位贡献者、1,280 次提交，稳定版 v1.5.0（2026-08-16），beta 线 v1.5.1-beta.3（2026-09-29）。半年 51 个 release（13 个稳定版），节奏很密。下文全部按现行版本口径写，涉及旧版差异的地方单独标注。

判断先给：CC-Connect 的价值不在"支持了多少平台"——桥接本身不难写——而在它把聊天软件当成 Agent 的完整管理界面来做：会话切换、目录跳转、权限档位、定时任务、进程隔离全部塞进 slash 命令。看完它的配置模型和权限设计，比看平台列表有收获得多。

## 系统地图：三层职责

```text
聊天平台（13 个内置）              CC-Connect 进程（Go）                本地 AI Agent
┌──────────────────┐   出向长连接   ┌──────────────────────┐   子进程/ACP   ┌──────────────┐
│ 飞书  WebSocket   │◄────────────►│ 会话管理 · slash 路由  │◄────────────►│ Claude Code  │
│ 钉钉  Stream      │              │ 权限控制 · cron/心跳   │              │ Codex        │
│ TG   Long Polling │              │ Web Admin (:9820)     │              │ Gemini CLI   │
│ 微信个人 HTTP 轮询 │              │ OS-User 隔离          │              │ …… + 任意    │
└──────────────────┘              └──────────────────────┘              │ ACP 兼容代理  │
                                                                        └──────────────┘
```

三层各管一件事：

- **平台适配器**（`platform/` 目录，20 个实现，README 官方口径列 13 个内置平台）只做协议转换：把飞书卡片、Telegram 消息翻译成统一的内部消息结构。
- **核心引擎**（`core/`，约 30 个模块）持有全部业务逻辑：会话状态、命令路由、权限判断、任务调度。491 个 Go 文件里大头在这里。
- **Agent 适配器**（`agent/` 目录，16 个实现）以子进程方式驱动各家 CLI，`acp` 适配器让任何支持 Agent Client Protocol 的代理即插即用；Devin 就是走 ACP 接入的。

所有连接都是出向的——WebSocket、Stream、Long Polling、Gateway，平台消息推到 CC-Connect，它不需要公网 IP。例外只有两个：LINE 的 Webhook 模式和企业微信的 Webhook 模式需要公网可达（企业微信选 WebSocket 连接则不需要）。

## 版本主线：从 v1.2.1 到 v1.5.x

| 版本 | 日期 | 关键变化 |
|------|------|----------|
| v1.2.1 | 2026-03-09 | 本文初版时的最新版；微信个人号（ilink）刚进 beta |
| v1.3.0 | 2026-04-19 | Web Admin UI 进驻二进制；`[[hooks]]` 生命周期事件；Kimi CLI、Pi 两个新 Agent；TOML 支持 `${ENV_VAR}` 占位 |
| v1.4.0 | 2026-06-28 | Cisco Webex、Matrix（含 E2EE）两个平台；Agent 配置统一为 `cmd` 字段（`cli_path` 弃用）；智谱 GLM provider 预设；附件上限 `max_attachment_size_mb` |
| v1.5.0 | 2026-08-16 | 腾讯元宝、Google Chat、WPS Agentspace、推推（360）、cloud_web 自托管网关等一批平台；Reasonix Agent；Pi RPC 模式 |

v1.4.0 修掉的一个 bug 值得一提：飞书的撤回探测在卡住的会话上每月烧掉约 130 万次 OpenAPI 调用（项目自述，修复后探测间隔从 2 秒改为 60 秒加去重）。另一次是核心发送协程的空指针竞态，会让整个进程崩溃、所有平台连接尽断。这类问题说明桥接层的稳定性并不平凡——平台 API 的怪癖比想象中多。

读数刷新：Stars 从发文时的约 5.3k（Wayback 4 月 28 日快照 6,549★ 可佐证量级）涨到 15,747；贡献者 50 → 183。贡献榜第一不是作者 chenhg5（213 次提交），而是一个叫 `claude` 的账号，281 次——AI 自己提交的代码比人多，在这个项目里是字面意义的事实。

## 配置模型：[[projects]] 一层套一层

CC-Connect 的全部行为由 `~/.cc-connect/config.toml` 驱动（首次运行会自动生成，也可用 `cc-connect config-example` 导出模板）。一个进程可以同时跑多个项目，每个项目是一对"Agent + 平台"组合：

```toml
[[projects]]
name = "my-backend"
admin_from = "alice,bob"        # 特权命令白名单，见下文

[projects.agent]
type = "claudecode"             # codex / gemini / cursor / qoder / opencode / iflow / kimi / pi / copilot / devin / acp …
[projects.agent.options]
work_dir = "/path/to/backend"
mode = "default"                # 权限档位，见下文

[[projects.platforms]]
type = "feishu"
[projects.platforms.options]
app_id = "cli_xxxxxxxx"
app_secret = "xxxxxxxx"
```

本文初版把这段写成了 `[projects.claude]` 加顶层 `[platforms.feishu]` 的嵌套结构——那是错的，仓库里从来没有这种写法，照抄只会得到解析错误。真实结构就是上面这样的三层：项目数组、Agent 小节、平台数组，平台凭证一律放在 `[projects.platforms.options]` 下。各平台的凭证键名不变：飞书 `app_id`/`app_secret`，Telegram `bot_token`，Discord `bot_token` 加可选 `guild_id`（设了可以让 slash 命令秒级注册，不设走全局注册要等最多一小时），企业微信 `corp_id`/`corp_secret`/`agent_id`。

安全模型的要点在 `admin_from`，有三个容易踩的细节：

1. **默认全拒绝**。不设置时，所有特权命令对所有人禁用——包括你自己。特权命令指 `/dir`、`/shell`、`/restart`、`/upgrade`、`/commands addexec`、`/cron addexec` 这六个，它们能改文件系统、杀进程。
2. **位置敏感**。`admin_from` 必须写在 `[[projects]]` 这一层，写进 `[projects.platforms.options]` 会被静默忽略。
3. **`admin_from = "*"` 是核按钮**。配置文件原话警告：这等于把主机完整 shell 权限交给所有已允许的用户，只适合完全信任的单人部署。

用户 ID 不知道填什么？在聊天里发 `/whoami` 或 `/status`，机器人会告诉你。多人的群还可以配 `[projects.users]` 角色：每个角色一组 `user_ids`、`disabled_commands` 和速率限制（比如 member 角色限每分钟 10 条消息、禁用全部内置命令）。

## 会话、目录与权限

聊天里的命令面比大多数桥接器大得多，常用的这些：

```text
/new [name]        开新会话            /list             列出会话
/switch <id>       切换会话            /current          当前会话
/delete <id>       删除会话            /search <kw>      搜索历史
/dir               显示工作目录与历史    /dir <path>       切换目录
/dir -             回上一个目录         /dir <n>          按历史序号跳转
/model             列模型              /model switch <别名>  切模型
/reasoning         调推理强度           /mode             查看/切换权限档位
/memory            查看/编辑记忆文件     /compress         压缩当前上下文
```

两处容易误解的语义：`/dir -` 回退的是**上一个工作目录**，不是上一个会话——本文初版把这两个概念写混了；`/memory` 的子命令是 `add`、`global`、`global add`（读改 Agent 的记忆文件），初版写的 `/memory read`、`/memory write` 在源码里不存在。

会话有个默认行为值得知道：`reset_on_idle_mins` 未设置时是 **30 分钟**，闲置超过后项目自动转到新会话，旧会话保留、可随时 `/switch` 回去。设计动机写在 README 里——靠 `--continue` 续命的长会话会把失败的命令、调试噪声反复塞回模型注意力，上下文漂移越来越重。设为 0 关闭这个行为。配套的 `agent_session_idle_timeout_mins` 则相反：默认禁用，开启后闲置时关掉 Agent 进程省资源，下次消息来了再续接同一会话。

权限模式有六档，比初版写的两档多：

| 档位 | 行为 |
|------|------|
| `default` | 每次工具调用都要确认 |
| `acceptEdits` | 文件编辑自动通过，其他仍要确认 |
| `plan` | 只规划不执行，批准后再动手 |
| `auto` | 模型自行判断何时需要确认 |
| `bypassPermissions`（`yolo`） | 全部自动通过 |
| `dontAsk` | 未预授权的工具直接拒绝 |

在 IM 里权限确认有专门的交互：Agent 请求授权时直接回复"允许"或"allow"放行，不用跳回终端。

## 进程级隔离：run_as_user

权限档位管的是 Agent 自己守不守规矩，`run_as_user` 管的是它越界时的损失半径。Linux/macOS 上一个项目可以用另一个 Unix 用户身份跑 Agent，做到文件系统级隔离：

```toml
[[projects]]
name = "claude-sandboxed"
run_as_user = "partseeker-coder"
run_as_env = ["PGSSLROOTCERT"]    # 显式声明要传给目标用户的环境变量
```

前置条件不少：supervisor 用户要有对目标用户的免密 sudo，目标用户自己不能有 sudo，要对 `work_dir` 有读写权，还得有自己的 `~/.claude/settings.json`；用 claude.ai OAuth 认证的话，要把凭证文件 symlink 过去保持 token 刷新同步。目前只有 Claude Code 适配器支持。这套机制是 2026-04-11（本文初版发表前一天）才合入的，v1.4.0 还修过一个让所有 `run_as_user` 用户启动即失败的 EACCES 回归——上生产前先跑一遍预检：

```bash
cc-connect doctor user-isolation
```

它会跑三道 go/no-go 门禁加一次隔离探测（实际报告目标用户能读到什么、不能读到什么），任何一道不过或探测发现跨用户泄漏，CC-Connect 直接拒绝启动。

## 三条触发线：聊天、定时、Webhook

除了人在聊天里说话，还有三种方式让 Agent 动起来：

**定时任务**走 `/cron`：`/cron add 0 6 * * * 总结 GitHub trending`，子命令有 `add`/`list`/`exec`/`del`/`enable`/`disable`/`mute`/`unmute`/`setup`。本文初版说定时任务"每次在新会话中运行"——那是当时的口径，现在有一个全局开关：

```toml
[cron]
session_mode = "reuse"    # 默认 reuse：复用活跃会话；new_per_run：每次新建
```

每个任务可单独设 `timeout_mins`（不设默认等 30 分钟，0 为不限）和权限档位覆盖。`/cron setup` 把 CC-Connect 的使用说明写进 Agent 记忆文件，让模型自己知道怎么回传附件。

**心跳**（`[projects.heartbeat]`）和 cron 相反：不在隔离会话里跑，而是在主会话里按固定间隔（默认 30 分钟）唤醒 Agent 巡检，共享完整上下文，适合"看看后台任务跑完没有、继续没干完的活"这类连续性工作，任务描述为空时读 `work_dir` 下的 `HEARTBEAT.md`。

**Webhook**（`[webhook]`）把方向反过来，让外部系统触发 Agent：监听 9111 端口（默认），token 认证，POST 一个 JSON 就能让 Agent 执行 prompt 或跑 shell 命令——git hook、CI 流水线接进来就是几行 curl 的事。

横切这三条线的是 `[[hooks]]` 生命周期事件：`message.received/sent`、`session.started/ended`、`cron.triggered`、`permission.requested`、`error` 七种（加 `*` 全匹配），处理器可以是 shell 命令或 HTTP 回调，事件上下文通过 `CC_HOOK_*` 环境变量传递，默认异步、失败不阻塞主流程。

## 一条消息的完整路径

把机制串一遍：你在 Telegram 群里 @机器人 发"review 最新一次提交"。

Telegram 适配器用 Long Polling 拉到消息，先过白名单（`allow_from`）——不在名单里的人直接无视。消息不是 slash 命令，路由到当前会话；引擎检查 `admin_from` 不需要（特权判断只对六个特权命令生效），然后找到项目绑定的 Claude Code 子进程：活着就复用，闲置被 `agent_session_idle_timeout_mins` 关了就重启并续接会话 ID。prompt 经适配器传给 `claude` CLI，权限档位随启动参数注入。Claude Code 跑完 `git log`、写完审查意见，回复带着页脚状态行（模型名 · token 用量 · 上下文百分比）发回 Telegram；如果它生成了补丁文件，还能调 `cc-connect send --file /abs/path/review.patch` 把文件直接甩回群里（上限 50 MiB，`attachment_send` 全局开关默认开着，目前支持飞书和 Telegram 两家）。消息发出后，`message.sent` 钩子异步触发，你的审计脚本收到一条通知。全程你只碰了聊天软件。

## 平台矩阵与能力边界

13 个内置平台的连接方式和公网需求：

| 平台 | 连接方式 | 公网 IP | 备注 |
|------|----------|:------:|------|
| 飞书/Lark | WebSocket | 不需要 | 卡片、话题隔离最完善 |
| 钉钉 | Stream | 不需要 | |
| WPS 协作 | WebSocket | 不需要 | 不支持图片/文件收发 |
| Telegram | Long Polling | 不需要 | 语音、论坛话题支持全 |
| Slack | Socket Mode | 不需要 | 流式预览 + 聚合卡片 |
| Discord | Gateway | 不需要 | Markdown、图片、群聊全支持 |
| 企业微信 | WebSocket / Webhook | WS 免 / Webhook 需 | 支持私有化 `api_base_url` |
| LINE | Webhook | **需要** | 群聊能力受限 |
| 微博 | WebSocket | 不需要 | 仅文本私聊 |
| 微信个人（ilink） | HTTP 长轮询 | 不需要 | `cc-connect weixin setup` 扫码接入 |
| QQ（NapCat） | WebSocket | 不需要 | 非官方桥，行为取决于你的 NapCat 部署 |
| QQ Bot（官方） | WebSocket | 不需要 | |
| Matrix | /sync 长轮询 | 不需要 | v1.4.0 起带 E2EE |

这张表修正了初版的几处错误：Discord 的 Markdown、图片、群聊在官方矩阵里都是全绿（初版打了三个 ⚠️）；"只有 LINE 需要公网 IP"的说法不对，企业微信的 Webhook 模式同样需要——初版 FAQ 和它自己的平台配置节互相矛盾。

代码库里还有 7 个 README 矩阵之外的适配器：Google Chat（有官方配置指南）、腾讯元宝、360 推推、MAX messenger、Cisco Webex、cloud_web、WPS Agentspace。要用 README 没列的平台，以 `config.example.toml` 里的配置段为准，每个都有逐行注释。

微信个人号值得单独说：本文初版时它只能装 `npm install -g cc-connect@beta` 才有，稳定版不带；现在已经转正，稳定版直接支持，README 里的 beta 限定标记已删。它是走 ilink 通道的 HTTP 长轮询，不用公网 IP，但个人微信协议毕竟不是官方开放 API，风险自担。

## 部署、升级与排查

**安装顺序有讲究**：先装好至少一个 Agent CLI 并完成认证（`claude login` 之类），再装 CC-Connect。顺序反了，服务起得来但 Web 管理界面（`http://localhost:9820`）永远出不来，日志里是 `claudecode: claude CLI not found in PATH` 这样的报错。

```bash
npm install -g cc-connect        # 或 brew install cc-connect（已进 Homebrew 核心）
cc-connect                       # 首次运行自动生成 ~/.cc-connect/config.toml
cc-connect web                   # 打开 Web 管理界面（只开浏览器，不启动服务）
```

Web Admin 是 v1.3.0 塞进二进制的管理面板：项目管理、会话监控、cron 编辑器、provider 管理、聊天界面，监听 `[management]` 段配置的端口（默认 9820，token 必填）。不想手写 TOML 的话，在面板里点选平台、贴 token，保存即热加载。界面有五种语言——英、中文简体、中文繁体、日、西（v1.4.0 又给管理面板加了韩语）。

升级与自更新：

```bash
npm install -g cc-connect        # npm 升级
cc-connect update                # 二进制自更新（稳定线）
cc-connect update --pre          # 跟 beta 线
```

排查用这三个真实存在的命令，别用初版写的 `cc-connect logs`——CLI 子命令注册表里没有它：

```bash
cc-connect daemon logs -f        # daemon 模式下跟日志
cc-connect doctor user-isolation # 隔离预检
cc-connect check-update          # 只检查不升级
```

常驻部署走 `cc-connect daemon install/start/stop/restart/status/uninstall`，配置路径建议写绝对路径——systemd/launchd 环境下 HOME 变量可能不传播，相对路径会被解析到 `work_dir` 下面。语音转文字要用的话记住 ffmpeg 是前置依赖（AMR/OGG 转 MP3），STT 支持 Groq/Qwen/Gemini 三家，TTS 支持 Qwen/MiniMax/MiMo/espeak/pico/edge 六种。

## 采用建议

**适合现在就上**：个人开发者想在外面遥控自己的 Agent、小团队想在群里共享一个 Claude Code。前者五分钟配完 Telegram 就能用；后者把 `admin_from` 收紧、开 `[projects.users]` 角色限流，再按上一节的办法给项目套 `run_as_user`。

**建议等等**：想把 QQ 个人号当正式客服通道的——NapCat 是非官方桥，协议风险始终在；想托管给不信任成员的——特权命令面太大，隔离机制也只有 Claude Code 一家支持。

**硬风险两条**。一是法律边界：README 和 npm、Homebrew 元数据都标 MIT，但仓库根目录没有 LICENSE 文件，GitHub API 因此读出 license=None——严格场景下先向作者确认。二是架构约束：它是本地桥接器，Agent 必须跑在一台开机的机器上，没有云托管版本；仓库里出现 Cloudflare 的地方只有运维文档教 LINE、企业微信这类 Webhook 用户拿 cloudflared 隧道暴露公网 URL——是可选工具，不是部署目标，本文初版练习里“部署到 Cloudflare 账号”的说法是错的。另外从源码构建需要 Go 1.25（`go.mod` 口径，README 仍写 1.22+，以 go.mod 为准）。

最常拿来对比的是 OpenClaw：它自带常驻 Gateway 和 Agent 循环，模型与 agent harness（Claude、Codex、本地模型）是可替换插件；CC-Connect 反过来自己不做 Agent，专门把外部 CLI 原样接进聊天软件。只是想在手机上用已有的 Claude Code，后者的改动面小得多。

---

**资源**：[GitHub](https://github.com/chenhg5/cc-connect) · [npm](https://www.npmjs.com/package/cc-connect) · [INSTALL.md](https://raw.githubusercontent.com/chenhg5/cc-connect/refs/heads/main/INSTALL.md)（给 AI Agent 看的安装指令） · [Discord](https://discord.gg/kHpwgaM4kq) / [Telegram 群](https://t.me/+odGNDhCjbjdmMmZl)

*核实口径：GitHub API 与 main 分支读数为 2026-10-04；era 对照取 2026-04-11 的 README 提交（4cf879b2）；命令、配置键、cron 会话语义逐项对照浅克隆源码（v1.5.1-beta.3 之后的 main，679 文件）；stars 历史读数经 Wayback 2026-04-28 快照佐证。*
