---
title: "Codeg 解读：收住 15 个编码 Agent 的不是 ACP，而是 15 个解析器和一条异步委托链"
slug: "xintaofei-codeg-multi-agent-ai-coding-workspace-guide"
github_repo: "xintaofei/codeg"
source_key: "gh:xintaofei/codeg"
date: 2026-07-12T12:10:00+08:00
lastmod: 2026-09-19T20:30:00+08:00
categories: ["技术笔记"]
tags: ["AI 编程", "Multi-Agent", "Tauri", "Rust", "开源工具"]
author: "钳岳星君"
draft: false
summary: "读 xintaofei/codeg v0.30.10 的源码：15 个内置 Agent 各自的会话存放方式与解析器、Claude Code/Codex 的 ACP 适配器关系、codeg-mcp 九工具与异步委托语义、To-dos 的 worktree 与两阶段合并、skill × agent 矩阵的符号链接实现、`--supervise` 升级回滚。"
description: "Codeg 用 ACP（Agent Client Protocol）把 15 种编码 Agent 收进同一个工作空间，真正的工程量在别处：15 个会话解析器、按 Agent 白名单排除凭据文件、codeg-mcp 的异步委托工具与深度上限、To-dos 的 git worktree 隔离与两阶段合并、Tauri/HTTP/远程三条传输通路。桌面、codeg-server、Docker 与移动端共用一份 Rust core。"
---

## 先说结论

Codeg 常被介绍成"用 ACP 协议统一多家编码 Agent（智能体）的工作空间"。这句话没错，但它把难度放错了地方。协议是现成的，[Agent Client Protocol](https://agentclientprotocol.com/) 定义了编辑器与 Agent 之间的握手和事件流，谁都可以实现。真正吃掉这个项目工程量的是两件更脏的活：把 15 家 Agent 各写各的会话文件读回来，以及在一次对话里把子任务安全地交给另一个进程去跑。

`src-tauri/src/parsers/` 下有 19 个文件，其中 15 个对应 15 个内置 Agent，每家一份手写解析器，剩下的是 `mod.rs`、自定义 Agent 的 `acp_native.rs`、Codex 的一种变体 `codex_code_mode.rs` 和 `summary_cache.rs`；`src-tauri/src/acp/delegation/` 下有 13 个 Rust 模块加一份 MCP 工具清单的 JSON，处理委托的 broker、线格式、深度计算与父进程看护。前者决定了"历史会话能不能被搜索和续用"，后者决定了"多个 Agent 能不能真的并行干活而不是互相踩文件"。

本文基于 `main` 分支 `385eb4f3`（v0.30.10 之后）的源码、`README.md`、`AGENTS.md` 与 `.github/workflows/release.yml`，把这两条主线拆开来看，并顺带纠正几处流传较广的过时说法。

## 阅读目标：读完你要能判断这四件事

1. Codeg 能不能接住你手上那几个 Agent——这取决于该 Agent 有没有 ACP 入口，以及它的会话存在哪、什么格式。
2. 跨 Agent 委托在生产里能不能开——默认是关的，而且链深度上限默认是 1。
3. 自建服务器会不会踩凭据泄露——`uploads/` 配额只在单进程内生效，备份白名单存在的理由正是各家 home 目录里混着密钥。
4. 桌面版、`codeg-server`、Docker 和手机之间该选哪个——它们共用同一份 Rust core，差别只在传输通路和谁持有文件。

## 系统地图：三个二进制，一份共享核心

Codeg 的一个 Rust workspace 出三个二进制，前端只有一份 Next.js 静态导出产物。

| 二进制 | feature 条件 | 职责 | 谁启动它 |
|--------|-------------|------|----------|
| `codeg` | `tauri-runtime`（默认） | 桌面应用：窗口、tray、通知、`tauri-plugin-updater` | 用户 |
| `codeg-server` | `--no-default-features` | Axum HTTP + WebSocket + 静态文件 + 原地升级 | 用户、`install.sh`、Docker |
| `codeg-mcp` | `--no-default-features` | 每次启动注入到 Agent CLI（命令行工具）的 stdio MCP 伴生进程 | 父进程注入，Agent CLI 拉起 |

```text
Next.js 16（output: "export"）+ React 19 + Tailwind v4
      │
      │  invoke()  /  fetch()+WebSocket  /  远程代理
      ▼
Transport 抽象层（3 个实现）
      │
      ├── Tauri 2 Commands ──┐        ┌── Axum HTTP + WS ──┐
      │     codeg（桌面）    │        │  codeg-server      │
      └──────────┬───────────┘        └─────────┬──────────┘
                 └──────────────┬───────────────┘
                                ▼
                        Shared Rust Core（codeg_lib）
        app_state · acp/{registry,connection,delegation} · parsers
        work_task · automation · chat_channel · office_watch
        commands/*_core · db（SeaORM + SQLite）
                                │
                 ┌──────────────┼──────────────┐
                 ▼              ▼              ▼
          本地文件系统      git 仓库      Telegram/Lark/微信
```

两个模式共用业务逻辑的做法写在 `AGENTS.md` 里：核心函数取 `_core` 后缀、参数是普通的 `&AppDatabase` 与 `&EventEmitter`，Tauri 命令和 Axum handler 都调它；`#[cfg_attr(feature = "tauri-runtime", tauri::command)]` 让同一个函数只在桌面构建里被标成命令。事件回传靠 `EventEmitter` 枚举分叉成 `Tauri(AppHandle)` 或 `WebOnly(Arc<WebEventBroadcaster>)`。这是"三个二进制互不污染"能成立的实际原因，不是修辞。

技术栈其余部分：SeaORM + SQLite 本地优先、next-intl 十种语言、pnpm、TypeScript strict 且开 `noUnusedLocals`。

## 15 个内置 Agent，和 15 种会话存放方式

`models/agent.rs` 里 `AgentType` 有 15 个具名变体，常量 `BUILTIN_AGENT_TYPES` 按声明顺序列出它们；第 16 个变体 `Custom(&'static str)` 是开放端。README 的 Supported Agents 一行给的 15 个名字与这份常量成员一致，只是顺序不同、用的是短名（`Codex` 而非 `Codex CLI`）。

| Agent | 覆盖变量 | 默认位置 | 载体 |
|-------|----------|----------|------|
| Claude Code | `CLAUDE_CONFIG_DIR` | `~/.claude/projects` | JSONL 目录 |
| Codex CLI | `CODEX_HOME` | `~/.codex/sessions` | JSONL 目录 |
| OpenCode | `XDG_DATA_HOME` | `~/.local/share/opencode/opencode.db` | SQLite 单文件 |
| Gemini CLI | `GEMINI_CLI_HOME` | `~/.gemini`，只取 `tmp/`、`history/`、`projects.json` | 混合目录 |
| OpenClaw | — | `~/.openclaw/agents` | 目录 |
| Cline | `CLINE_DIR` | `~/.cline/data`，取 `sessions/`、`db/`、`state/`、`tasks/`，后两个是 3.x 之前的状态布局 | SQLite + 目录 |
| Hermes Agent | `HERMES_HOME` | `~/.hermes/state.db` | SQLite 单文件 |
| CodeBuddy | `CODEBUDDY_CONFIG_DIR` | `~/.codebuddy/projects` | JSONL，目录布局同 Claude Code，记录结构是 OpenAI Agents SDK（软件开发包）的 item |
| Kimi Code | `KIMI_CODE_HOME` | `~/.kimi-code`，取 `sessions/` 与 `session_index.jsonl` | 目录 + 索引 |
| Pi | `PI_CODING_AGENT_SESSION_DIR`、`PI_CODING_AGENT_DIR` | `~/.pi/agent/sessions` | 每会话一个 JSONL |
| Grok | `GROK_HOME` | `~/.grok/sessions/<编码后 cwd>/<uuid>/` | 目录 |
| Cursor | `CURSOR_CONFIG_DIR` | `~/.cursor/chats`、`~/.cursor/acp-sessions` | 每会话一个 SQLite blob 库 |
| DeepSeek Harness | `DSH_HOME`、`DEEPSEEK_ACP_SESSIONS_ROOT` | `~/.dsh/sessions/<编码后 cwd>/<uuid>/` | 目录，`session[.vN].jsonl`，可带 `.zstd` |
| Qoder | `QODER_CONFIG_DIR` | `~/.qoder/projects/<编码后 cwd>/<sessionId>.jsonl` | 每会话 JSONL |
| Google Antigravity | `GEMINI_HOME` | `~/.gemini/antigravity-acp/conversations` | SQLite + `.meta` 侧车 |

用户自己注册的 Agent 走 `custom:<registry-id>`，没有原生存储可逆向，历史由 codeg 自己的 ACP 转录提供，解析器是 `acp_native`。README 明说这条路的入口是把公共 ACP registry 的 `distribution` 对象原样粘进来——`custom_registry.rs` 的注释专门写了"paste-compatible"。

### 白名单存在的理由，是隔壁就躺着密钥

上表最后一列不是"支持哪些格式"的清单，而是一圈排除边界。`parsers/mod.rs::external_transcript_sources()` 给每个源配了 `include_top` 白名单，注释逐条点名了要防的东西：Gemini 的 base 目录里混着 `oauth_creds.json`，Cline 的同级有 `secrets.json`、`settings/`、`locks/`，Grok 的 home 下有 `auth.json` 与 `bin/`，Kimi Code 旁边是 `config.toml` 和 `credentials/`、`oauth/`，Cursor 的同级是 `cli-config.json` 与 `mcp.json`，DeepSeek 的 `~/.dsh` 里有 `.credentials.yaml`，Qoder 的 `~/.qoder` 下有 `security/`。

SQLite 的源还多标一个 `sqlite: true`。原因很具体：直接拷主文件会把它对应的 `-wal` 留在另一个时刻，恢复出来是一个坏库。标了之后备份走只读连接的 page-copy，把 WAL 里的帧一并收进同一个归档条目。Hermes 的注释就是拿这条写的——它的会话库自己管理，只有 WAL 里有最近几帧。

对读者的实际意义：同一份 home 目录布局也决定了 codeg 的**解析**边界。当你在界面上搜不到某个 Agent 的历史，先确认它落在白名单的那几个子树里，而不是"codeg 支持这个 Agent"。

## 适配器与启动元数据：Agent 到底是怎么被拉起来的

`acp/registry.rs` 2796 行，装着 15 个内置 Agent 的启动元数据。形状只有两种：`Npx { package, cmd, args, env, node_required }` 与 `Binary { cmd, args, env, platforms, dir_entry }`。`node_required` 记的是该适配器要求的 Node.js 下限，`Binary` 的 `dir_entry` 区分"单文件解出来直接跑"和"整棵目录树要保完整"——Cursor 的 agent-cli-package 属于后者。版本全部锁死，例如 `@agentclientprotocol/claude-agent-acp@0.78.0`、`@agentclientprotocol/codex-acp@1.12.0`、`@google/gemini-cli@0.60.0`、`cline@3.0.62`、`@tencent-ai/codebuddy-code@2.151.0`、`@moonshot-ai/kimi-code@2.0.0`、`@qoder-ai/qodercli@1.1.54`，OpenCode 与 Cursor 走 `Binary`。README 里"Codeg installs, pins, and updates most of them for you"对应的就是 `acp/binary_cache.rs` 按版本建缓存目录。

### Claude Code 与 Codex 走的是另一条路

`acp_adapter_relation()` 只对这两个 Agent 返回 `Some`。它们的 npx 包提供的命令是 `claude-agent-acp`、`codex-acp`，而不是用户自己装的 `claude`、`codex`——也就是 codeg 启动的是一个把 Anthropic/OpenAI 原生 CLI 桥接到 ACP 的适配器。`shared_config_dir` 填 `~/.claude` 与 `~/.codex`，注释解释得很直白：适配器与原生命令读同一份配置和凭据，装了适配器不需要第二次登录。`extra_dirs` 列出厂商安装器会写、但 GUI（图形用户界面）应用的 `PATH` 通常不含的位置（`~/.local/bin`、旧版的 `~/.claude/local`），`preflight` 靠它把"你没装 CLI"和"装了但 codeg 找不到"这两种错误分开报。有一条测试专门断言适配器命令不等于原生命令。

其余 13 个 Agent 的 npm 包或发行物自己就是 ACP 入口，没有这层桥接。这个区分决定了故障排查的走向：Claude Code 连不上，要同时怀疑原生命令的登录态和适配器的版本；Gemini 连不上，只有一个包要看。

## 委托链路：从输入框里的 @ 到子 Agent 的会话

Codeg 有两条委托入口，共用一个开关和一个执行体。

用户在输入框里 `@` 某个 Agent 时，`acp/agent_mentions.rs::append_agent_routes()` 把可见的 `codeg://agent/...` 引用收敛成一张路由表，作为额外一个 text block 追加到 prompt（提示词）上。这张表用 `U+001E` 记录分隔符包住，带 `kind`、`version` 与一个 nonce；一帧最多 16 个去重后的不同 Agent、256 次引用、16 KB。追加发生在连接循环里，广播、预览和乐观显示的用户消息都看不到它。

Agent 自己也能发起委托：`codeg-mcp` 通过 MCP 把工具暴露给 LLM（大语言模型）。注释点明了分工——Agent 从工具清单里本来就能发现 `delegate_to_agent`，它们做错的是改用自家的 sub-agent 机制，所以路由帧只绑通道，不催 Agent 去委托。

### 路由帧的字节身份就是它的版本

`parse_internal_agent_routes()` 只接受能**逐字节重渲染**成当前样子的候选帧。好处是解析器可以放心地从 Agent 自己的转录里删掉 codeg 写进去的帧，永不误删用户写的相似文本；代价是任何措辞改动都会让已经落盘的旧帧再也匹配不上，变成可见历史。文件注释直接把这条后果写在那里，并要求改动必须 bump `ROUTE_FRAME_VERSION`，由 `route_frame_wording_is_pinned_to_its_version` 守着。目前没有兼容渲染器，注释的理由是"还没发布过值得保留的历史"。

### 九个工具与异步语义

`delegation/tool_schema.json` 里是九个工具，不是 `delegate_to_agent` 一个：

| 工具 | 语义 |
|------|------|
| `delegate_to_agent` | 立刻返回 `task_id`，子 Agent 在独立会话里继续跑；可一次扇出多个 |
| `get_delegation_status` | 传 `task_ids` 批量取；不带 `wait_ms` 是快照，`0` 阻塞到某个任务终态，正值是有界等待 |
| `cancel_delegation` | 取消 |
| `resume_delegation` | 续跑 |
| `check_user_feedback` | 拉用户中途写下的转向备注 |
| `ask_user_question` | 阻塞在一张多选卡片上 |
| `get_session_info` | 按 id 解析被引用的会话 |
| `create_automation` | 建自动化 |
| `create_work_task` | 建待办 |

把 `delegate_to_agent` 写成同步调用是常见误解。它是异步的：一次调用不阻塞，结果靠 `get_delegation_status` 长轮询收。工具按 `--features` 分成 `delegation`/`feedback`/`ask`/`sessions`/`tasks`/`automations`/`taskboard` 七组，父进程按设置决定注入哪些组，关掉的那组直接从 Agent 的 MCP 目录里消失。

### 一个示例：这条调用长什么样

`delegate_to_agent` 收三个字段，`agent_type` 与 `task` 必填，`working_dir` 默认继承本会话的目录：

```json
{
  "agent_type": "codex",
  "task": "在 /Users/me/code/billing 里 review 未提交的 diff，重点是 refresh token 轮换的并发问题。列出你认为必须改的行，给出替代写法。"
}
```

返回值是一个 `task_id`，然后要另起一次收集：

```json
{ "task_ids": ["<task_id>"], "wait_ms": 30000 }
```

响应永远是 `{"tasks": [...]}`，一个 id 一个条目，按你提问的顺序排。`wait_ms` 的三档语义是这份工具清单自己写明的：省略就是非阻塞快照；正值最多等这么久，上限 60000 毫秒，要接着等就再调一次；`0` 是无超时阻塞，直到子 Agent 跑完。多个 id 一起等时，任意一个到终态就返回，所以拿剩下几个还得再问。

同一份清单里还有一条对怎么写 `task` 影响最大的约束：子 Agent 看不到这段对话、你看开的文件、也看不到之前的轮次，它是冷启动的，`task` 必须自带全部所需上下文。适合派出去的是能一次讲清的独立可并行工作，不适合的是需要你持续来回的步步推进。

伴生进程与主进程之间不走 stdio。`delegation/transport.rs` 的帧格式是一个小端 `u32` 长度加 UTF-8 JSON，每次 `tools/call` 重开一次连接；Unix 上是 UDS，Windows 上是命名管道。选长度前缀而不是换行分隔的理由写在注释里：大模型给的 `task` 参数本身可以含换行。父进程拉起它时要交三个必填参数——父连接 id、套接字路径和一个临时令牌：

```text
codeg-mcp \
  --parent-connection-id <uuid> \
  --socket-path <绝对路径> \
  --token <一次性密钥>
```

另外两个可选参数 `--custom-agents` 与 `--disabled-agents` 把可委托目标算进工具清单：已注册的自定义 Agent 成为额外候选，设置里关掉的内置 Agent 从清单里减掉，这样内置名单和顺序只有一处真相。`parent_watcher` 让它在父进程消失时退出，注释给的动机是 Windows 上孤儿伴生会锁住二进制文件、直接让升级失败。

### 默认关闭、深度 1、找不到伴生进程只留一行 WARN

`DelegationConfig::default()` 是 `enabled: false`、`depth_limit: 1`。也就是说装完就试的读者，第一步要在设置里把多 Agent 协作打开——`enableHint` 的原文是关掉时 `delegate_to_agent` 从 Agent 的 MCP 目录里隐藏。深度按会话的父子链算，`depth_limit = 2` 才允许 root → 子 → 孙，孙再往下被拒；向上多走一层就够 broker 判定，所以调用方传 `depth_limit + 1` 作为遍历封顶，防的是链上有环或历史过深。

查找伴生二进制的顺序是 `CODEG_MCP_BIN` → 当前可执行文件的同级目录 → `PATH`。三处都没有就在日志里写一行 WARN，跳过工具注入，会话照常跑。函数注释对调用方提了硬要求：拿到 `None` 必须当成"这里没有委托能力"，不能塞一个幻影路径，那会在 Agent 的 MCP 启动循环里炸掉，严格一点的 Agent 会连整个 ACP 会话一起带走。所有功能组都关着时，代码在查二进制之前就短路返回，连那行 WARN 都不发。

## To-dos：把不用盯着的活放进独立 worktree

`work_task/` 是 v0.30 线里新增的一块，README 把它列在 To-dos 一节。状态机是 `todo → queued → preparing → running ⇄ awaiting_input → review → merging → done`，失败原因限 `agent_error`、`setup_error`、`verdict_blocked`、`interrupted` 四种。

几个设计点值得单独看：

- **一进程一引擎，用文件锁选主**。`work_task/mod.rs` 写明引擎由 data 目录上的独占文件锁选举，桌面和 server 模式都在启动时建。多实例共享同一份数据目录时不会双跑。
- **`run_seq` 代次**。每次领取都递增 `run_seq`，事件按 `(connection_id, run_seq)` 匹配再走 CAS 落库，于是一个取消和一条迟到的 `TurnComplete` 撞在一起是无副作用的空操作。`preparing` 阶段（建 worktree、跑目录的 init 命令、拉起 CLI）也持并发槽、可取消，进程重启时和 `queued` 一样算被打断。
- **`awaiting_input` 由后端驱动**。引擎订阅 Question/Permission/PlanApproval 的请求与解决事件，用 outstanding-request-id 集合翻转 `running ⇄ awaiting_input`。注释的理由是前端没有全局的未打开会话待答问题通道。
- **合并是两段式，且先落意图**。A 段把 base 分支合进任务自己的 worktree，冲突永远先落在那里；B 段在项目目录里、按目录粒度的 git 互斥锁落到 base 分支上，合并意图在执行前持久化，崩了由恢复流程拿 git 的事实重放。`base_sha` 在建 worktree 之前就记下来，防的是并发切分支把基准漂移掉。
- **不轻信 Agent 的自述**。README 的表述是 Codeg 去查 git 而不是接受 Agent 说"合完了"；确认不了的合并退回 review 列，而不是报成功。

`automation/` 的引擎结构与此对称，同样由文件锁选主、同样是事件总线加一个 reconcile tick。它的完成按 `connection_id` 关联（`TurnComplete` 事件里没有 conversation_id），`stop_reason` 是权威；每 tick 的回溯兜底去读产出会话的终态，把广播丢帧漏掉的运行结算掉。空闲清理不会误伤：在跑的轮次停在 `Prompting`，`sweep_idle` 只收 `Connected`。

## 一次完整流转：@codex 审一个改动，然后进 review 列

把上面的机制串成一次真实动作。假设你在桌面版里开着 `~/code/billing`，Claude Code 刚改完一个鉴权函数。

1. 你在输入框写"帮我 review 这段改动 @Codex"，`@Codex` 在前端渲染成一条 `codeg://agent/codex` 引用。
2. 连接循环调 `append_agent_routes()`，识别出 `codex`，在 prompt blocks 尾部追加一帧路由描述。界面上的乐观气泡里没有它。
3. Claude Code 侧的 MCP 目录里有 `delegate_to_agent`（`delegation` 组已开），它按帧里的通道调用它，参数是 `agent_type="codex"` 加一段自包含的任务描述。
4. `codeg-mcp` 把请求按长度前缀写到 UDS，主进程的 broker 收到，先算链深度：本次是 root → 子，`depth_limit = 1` 允许；如果它再往下派一次就会被拒，错误码 `depth_limit`。
5. broker 用 `registry.rs` 里 Codex 的元数据起子会话——`@agentclientprotocol/codex-acp@1.12.0`，缓存命中就不装，`shared_config_dir` 是 `~/.codex`，沿用你已有的登录态。
6. `delegate_to_agent` 当场返回 `task_id`。Claude Code 可以继续干活，也可以按注释鼓励的样子一次扇出多个。
7. 子会话在独立标签里流式跑，父侧调 `get_delegation_status`（带 `wait_ms`）收终态报告，结果合并回你正在看的那条对话流。
8. 如果这条改动你想让它直接落地，更合适的是记成一条 To-do：它会拿到 `~/code/billing` 旁边的一个 worktree 和自己的分支，跑完停在 review 列等你看 diff、退回或者接受。

## 能力层：skill × agent 矩阵的物理实现

设置页上那张 `(skill, agent)` 矩阵，落到文件系统只有一件事：**符号链接**（Windows 上是 junction），从各 Agent 自己的 skill 目录指向中心仓库 `~/.codeg/skills/<id>/`。四类来源共用这一个仓库和这一套链接引擎。

| 来源 | 数量 | 进入中心仓库的方式 |
|------|------|--------------------|
| experts（来自 [Superpowers](https://github.com/obra/superpowers)） | 14 | `include_dir!` 编进二进制，启动时解出 |
| science（来自 [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) 的 MIT 子集） | 13 | 同上 |
| office（由 OfficeCLI 提供） | 动态 | 运行时从 `officecli load_skill <id>` 读出来放 |
| custom（用户自己写） | 不限 | 直接就是一个目录，按"排除法"识别 |

按排除法识别的意思很实用：中心仓库里任何含 `SKILL.md`、且 id 未被三个内置包占用的目录，都算自定义 skill。往 `~/.codeg/skills` 里丢一个文件夹，刷新就出现。启动时的内置包提取是 id 粒度的（哈希 + manifest + 备份，绝不整体清空），所以不会碰用户放的目录。`include_dir!` 不带 Unix 权限位，注释专门标了这一点，捆绑脚本的执行位要另外修。

科研包的来源记在 `science/NOTICE.md`：vendored、逐字节一致、钉在某个提交（commit）`4d97e293dc6f604fb6b63dcd49b9028df413d65b` 上、MIT、只收"自包含且无跨 skill 依赖"的项，重同步走 `scripts/sync-science-skills.sh`。13 个 skill 的中文名以 `science.toml` 的 `zh-CN` 为准：科学头脑风暴、假设生成、实验设计、统计功效、统计分析、探索性数据分析、科学可视化、批判性思维、论文检索、同行评审、引用管理、学术评估、科学示意图。矩阵上的两个徽章各有明确触发条件：`needs_key` 只有 scientific-schematics 一个（要 OpenRouter 密钥），`needs_env` 标的是"自带脚本可能需要 Python/uv 环境"。

Office 那一格容易被误读成"内置了 Office 工具"。`office_tools.rs` 的模块标题是 detect、install/uninstall the binary——`officecli` 是外部二进制，先在 `PATH` 上找，再回落到官方安装器的已知位置；找不到还要往被派生 Agent 的 `PATH` 前面拼一个目录，注释的理由是 `install.ps1` 改的用户级 `PATH` 到不了一个已经在跑的进程。预览侧同理：`office_watch/` 维护的是长生命周期的 `officecli watch <file> --port N` 子进程，一个文件一个，按引用计数共享与回收。它替代的是旧的 `officecli view html` 渲染路径——那条路径每次变更重开一个进程去重读整个 OpenXML zip，Agent 正在写同一个文件时两边抢盘，Windows 上直接 "file is in use"。预览 URL 上挂的 `cap` 是 watch 首次拉起时铸造的高熵 UUID：泄漏一个 `cap` 只放出那一个打开的文档，桌面模式则完全忽略它。

## Project Boot、Chat Channels 与 Automations 的准确边界

Project Boot 是配置面板加 live preview 的分屏页。preview iframe 指向的是 `ui.shadcn.com/preview/radix/preview-02?preset=...`，改配置就是换 preset 参数；创建走 `shadcn@latest init -n <name> -t <template> -p <pm> -y`，由所选包管理器的 runner 拉起（pnpm/yarn 用 `dlx`，bun 用 `bunx`，否则 `npx`）。`shadcn/constants.ts` 导出的两组选项是：

```text
FRAMEWORK_OPTIONS      next | vite | start | react-router | laravel | astro
PACKAGE_MANAGER_OPTIONS  pnpm | npm | yarn | bun
```

同一个页面下还有一个 HyperFrames 标签，选完分辨率预设，用 `skills` CLI 把全局 skill 装给六个 Agent。

Chat Channels 是三个后端，不是计划中的五个。`backends/telegram.rs` 走 Telegram 的应用程序接口，用 `getUpdates` 长轮询；`backends/lark.rs` 连 `open.feishu.cn`，WebSocket 与 HTTP 两种通路并用；`backends/weixin.rs` 走 iLink 的 `ilinkai.weixin.qq.com`，纯 HTTP，`context_token` 过期期间最多缓冲 50 条消息。README 里"驱动你的 Agent"能做的四件事是建任务、发后续消息、批权限请求、收带工具调用细节的实时回复。

Automations 常被写成"三种触发方式"，字段其实分两层。`TriggerKind` 只有 `Schedule` 与 `Manual`；`Schedule` 时 `cron` 存五段表达式，另有一列 `timezone` 存 IANA 时区名，`next_run_at` 以 UTC 存调度键、每次触发后向前重算，所以进程重启的追赶最多补一次。执行动作是另一个字段 `AutomationAction`，取 `LaunchSession`（无头会话，也是旧行的默认值）或 `EnqueueTask`（只在目录看板上放一条待办，交给 work-task 引擎）。`IsolationMode` 再决定落在哪：`WorktreePerRun` 每次生成 `automation/<id>/run-<run_id>` 分支的新 worktree，`SharedInRoot` 在根仓库切分支、按目录串行。侧栏那个失败角标是 `unseen_failures`，打开视图清零。

## 前端传输层：三条通路和一个 60 秒的耦合

`src/lib/transport/` 下是三个实现，不是两个：`tauri-transport.ts` 走 `invoke()`；`web-transport.ts` 把命令 `fetch()` 到后端的应用程序接口 `/api/<command>`、事件走 WebSocket，访问令牌放在 WS 子协议里带上（`buildCodegWebSocketProtocols`），另有 `/api/health` 探活；`remote-desktop-transport.ts` 是桌面版通过 `commands/remote_proxy.rs` 代理到远端 `codeg-server` 的第三条路。

三个数字值得记。`WEB_CALL_TIMEOUT_MS = 60_000`，注释解释它必须不短于后端 `ConnectionManager::probe_agent_options` 的 60 秒——Gemini 这类 Agent 光 Initialize 握手就要烧掉 8 到 10 秒，前端上限低了会在后端还握着一个活的探测进程时先报超时。`READY_TIMEOUT_MS = 5_000` 是等服务器 `__ready__` 帧的上限，超时就在没有确认的情况下继续，防的是老版本服务端、卡住的后端任务或缓冲的代理把界面永久锁死。桌面版起的 Web Service 与独立 server 是同一套 HTTP/WS，手机上的原生客户端连的就是它。

## 部署：桌面、独立服务、Docker 与移动端

桌面安装走 Releases；`codeg-server` 在 Linux/macOS 上有一条 curl 管道，Windows 上有一条 PowerShell 管道。两个脚本的参数名与默认目录不一样：`install.sh` 收 `--version` 与 `--dir`，默认 `/usr/local/bin`，也认 `CODEG_INSTALL_DIR`；`install.ps1` 收 `-Version` 与 `-InstallDir`，默认 `$env:LOCALAPPDATA\codeg`，并且会在这个目录不在用户 `PATH` 里时补进去。服务端预编译产物五个平台：`codeg-server-linux-x64`、`-linux-arm64`、`-darwin-x64`、`-darwin-arm64`、`-windows-x64`。

```bash
# Linux / macOS
curl -fsSL https://raw.githubusercontent.com/xintaofei/codeg/main/install.sh | bash -s -- --version v0.30.10
CODEG_STATIC_DIR=/usr/local/share/codeg/web codeg-server

# Windows（PowerShell）
irm https://raw.githubusercontent.com/xintaofei/codeg/main/install.ps1 | iex
$env:CODEG_STATIC_DIR="$env:LOCALAPPDATA\codeg\web"; codeg-server
```

Docker 是三阶段构建，运行阶段仍带着 Node.js 运行时——被托管的 Agent 大多是 npx 包，容器里得能跑起来。

```dockerfile
FROM node:24-alpine AS frontend          # pnpm build → /app/out
FROM rust:slim-bookworm AS backend       # codeg-server + codeg-mcp
FROM node:24-bookworm-slim               # libsqlite3-0 git openssh-client
                                         # ca-certificates curl python3
                                         # python3-pip libicu72

ENV CODEG_STATIC_DIR=/app/web
ENV CODEG_DATA_DIR=/data
ENV CODEG_PORT=3080
ENV CODEG_HOST=0.0.0.0
ENV CODEG_RUNTIME=docker
ENV CODEG_RESTART_DELAY_MS=2000
VOLUME /data
CMD ["codeg-server", "--supervise"]
```

`CODEG_RUNTIME=docker` 是给升级逻辑做部署形态判定的标记，容器检测的兜底是 `/.dockerenv`。

```bash
docker run -d -p 3080:3080 \
  -v codeg-data:/data \
  -v /path/to/projects:/projects \
  -e CODEG_TOKEN=your-secret-token \
  ghcr.io/xintaofei/codeg:latest
```

`docker-compose.yml` 里那行注释值得读：原地升级改写的是容器的可写层，不是镜像；`codeg-data` 卷留着，升级只活在这个运行中的容器里，`--force-recreate` 或者 pull 之后重建都会把它丢掉。要永久生效得构建或拉取新版本的镜像再重建。compose 另设了 `restart: unless-stopped`。

源码构建三步：`pnpm install && pnpm build` 出静态目录 `out/`，进 `src-tauri` 分别 `cargo build --release --bin codeg-server --no-default-features` 与 `--bin codeg-mcp --no-default-features`，然后让 `CODEG_STATIC_DIR` 指向上一步的 `out/` 再启动 `./target/release/codeg-server`。日常开发的命令在 `AGENTS.md` 里，值得一提的是解析器快照用 `cargo insta review` 复核，桌面测试要带 `--features test-utils`。

移动端的 iOS 与 Android 客户端是开源的（[codeg-ios](https://github.com/xintaofei/codeg-ios)、[codeg-android](https://github.com/xintaofei/codeg-android)），连的是桌面 Web Service 或你自己的 `codeg-server`；文件、Agent CLI 和会话都留在跑 codeg 的那台机器上，访问令牌存进 iOS Keychain 或 Android Keystore。

## 配置：常用环境变量与三个容易踩的默认值

`CODEG_*` 的变量名全仓 grep 一大片，其中还混着 `CODEG_DIR_NAME` 这类 Rust 常量，所以别把它当清单看。下面这张表只挑部署 `codeg-server` 会用到的那一层，其余属于运行时调优。

| 变量 | 默认 | 说明 |
|------|------|------|
| `CODEG_PORT` | `3080` | HTTP 端口 |
| `CODEG_HOST` | `0.0.0.0` | 绑定地址 |
| `CODEG_TOKEN` | 未设则生成 | 生成的那个会持久化并跨重启复用，只在 stderr 打一次 |
| `CODEG_DATA_DIR` | `dirs::data_dir()/codeg` | SQLite 数据目录，同时是 `uploads/`、`pets/` 的根 |
| `CODEG_HOME` | 未设 | 桌面侧配置根 `~/.codeg`，优先级在 `CODEG_DATA_DIR` 之前 |
| `CODEG_STATIC_DIR` | `./web` 或 `./out` | 前端静态导出目录 |
| `CODEG_MCP_BIN` | 未设 | 伴生进程绝对路径，覆盖"同级 + `PATH`" |
| `CODEG_SKIP_SIDECAR` | 未设 | 只在 `prepare-sidecars.mjs` 里生效，发布构建必须不设 |
| `CODEG_UPLOAD_MAX_TOTAL_BYTES` | 未设 | `uploads/` 总量上限，字节 |
| `CODEG_UPLOAD_QUOTA_STRICT` | 未设 | 置真则配额解析不出来就退出码 2 |
| `CODEG_RESTART_DELAY_MS` | `2000` | supervisor 重拉 worker 的间隔 |
| `CODEG_UPGRADE_TRIAL_SECS` | `30` | 升级后判定"起得来"的窗口 |

三个容易踩的地方：

`CODEG_DATA_DIR` 的默认值不是固定字符串。Linux 上 `dirs::data_dir()` 是 `~/.local/share`，所以是 `~/.local/share/codeg`；macOS 上是 `~/Library/Application Support/codeg`；桌面路径另有一套，`CODEG_HOME` 未设时回落 `~/.codeg`。容器里被烤成 `/data`。

`CODEG_TOKEN` 未设时生成的令牌会落库复用，所以一次原地升级重启不会把访问口令换掉。它只走 `eprintln!`，注释的理由是 bearer 凭据不能进持久化日志和应用内日志查看器。

`CODEG_UPLOAD_MAX_TOTAL_BYTES` 的配额是**单进程内**生效。横向扩多个 `codeg-server` 共享同一个 `uploads/` 目录时不会互相感知，`files.rs` 的注释点名要外部协调（文件锁、Redis 或反向代理层限额）。默认 fail-open：值写错只 WARN；`CODEG_UPLOAD_QUOTA_STRICT` 改成 fail-closed，服务直接不起。

## 原地升级与 `--supervise`

只有 `codeg-server` 与 Docker 走这条路，桌面版由 `tauri-plugin-updater` 管。流程是下载、验签、解包、原子换文件，换的是 `codeg-server` + `codeg-mcp` + `web/` 三件，各留一个 `.bak`。签名是 release 流水线用 `tauri signer sign` 产的分离 `.sig`，公钥就是 `tauri.conf.json` 里那把，两边都是"minisign 文本再套一层 base64"，验不过不碰任何活文件。下载与解包分别有 600 MB 与 1536 MB 的字节上限，注释写明挡的是坏 `Content-Length` 和误打包，不是真实体积。

重启方式取决于运行形态：`--supervise` 之下 worker 以退出码 86 请求重拉（这个值仓库自己没用），supervisor 等 `CODEG_RESTART_DELAY_MS` 再从被换掉的路径起进程；没有 supervisor 时 worker 自己 re-exec。supervisor 在 Docker 里是 PID 1，所以还要转发 `SIGTERM`/`SIGINT`、回收过继来的孤儿进程。

自动回滚只覆盖一种失败：因为升级而重拉的 worker 处于观察期，在 `CODEG_UPGRADE_TRIAL_SECS`（默认 30 秒）内异常退出，就从 `.bak` 恢复上一版再起一次。注释强调这是唯一一条不依赖那个已经死掉的 HTTP 回滚端点的恢复路径；过了窗口才崩，按普通运行时故障向上抛出，让容器的重启策略退回镜像，而不是在启动循环里热转。窗口默认值给得宽，理由是能起不来的二进制几乎立刻就会失败。

Windows 的原地升级没有被禁用。`update/install.rs` 的产物映射里有 `("windows", "x86_64") => "codeg-server-windows-x64"`，扩展名 `.zip`，目标文件 `codeg-server.exe` 与 `codeg-mcp.exe`。Linux/macOS 独占的只是那个原子交换目录的快速路径（`RENAME_EXCHANGE` / `renamex_np`），别处返回 `Unsupported` 然后退到非原子移动。伴生进程看护父 PID 那段的注释，说的恰恰是 Windows 上文件被锁导致升级失败——如果这条路根本不走，不会有这段代码。

## 与同类工具的边界

对照的轴不是"谁功能多"，而是三类工具各自站在哪一层。后两列是类别而不是评测结论，能写的判断只限于 Codeg 自己的代码能反推出来的部分。

| 维度 | Codeg | 编码 Agent CLI | 编辑器内插件 |
|------|-------|----------------|--------------|
| 会话归谁 | 读回 15 家自己的存储，汇成一个可搜索工作区 | 只写自己那一份，格式互不相通 | 依附编辑器的会话，跨工具不可见 |
| 跨 Agent 协作 | ACP 通道，子 Agent 起独立会话并成卡 | 可派自家的 sub-agent，但那是同一家机制 | 无此层 |
| 承载形态 | 桌面、独立 HTTP 服务、Docker、移动端连前者 | 终端进程 | 编辑器进程内 |
| 并行任务隔离 | 每任务一个 `git worktree`，两阶段合并、评审后落地 | 不是这类工具的内置流程 | 不是这类工具的内置流程 |

第一行是这张表里唯一有硬证据的一行：Codeg 需要 15 个手写解析器这件事本身就说明各家存储互不相通。第二行的措辞取自 `agent_mentions.rs` 的注释——Agent 会"改用自家的 sub-agent 机制"，README 也点了 Claude Code、Codex、Grok、OpenCode 四家确实自己会派子 Agent；区别在于 Codeg 把子任务落成**另一个类型 Agent 的独立会话**，于是那段转录能被同一个工作空间搜到。

Codeg 不做模型路由，也不替代任何一家 CLI，它假设你已经在用这些工具并且为它们各自付订阅。真正把它和"给 Agent 套个壳"区分开的是 worktree 那条链：To-do 与 Automation 的执行体都跑在自己的分支和目录里，合并前先看 git。如果你只需要一个更强的终端 Agent，这套复杂度对你是净负担。

## 按现象排查

最常见的两类是"看不见"和"接不上"。

**某个 Agent 的历史没出现在搜索结果里。** 先确认它落在自己那份白名单列出的子树里——各家允许的位置不同，Gemini 是 `tmp/`、`history/` 与 `projects.json`，Cline 是 `sessions/`、`db/`、`state/`、`tasks/`，Antigravity 只有 `conversations`。再确认覆盖变量指对了：`GEMINI_CLI_HOME` 给的是父目录，codeg 会把 `.gemini` 拼上去；Antigravity 读的 `GEMINI_HOME` 给的就是目录本身。同一家厂商的两个变量含义差一层，是最容易静默读空的地方。`CODEG_HOME` 则是 codeg 自己用作配置根的，与 Agent 侧那些 `*_HOME` 不是一层。

**`delegate_to_agent` 在 Agent 的工具列表里没有。** 设置里那组开关默认是关的。关掉时它不进 MCP 目录；`@` 提及同样失效，因为 `append_agent_routes()` 第一行就按 `delegation_enabled` 返回。

**日志里出现 `codeg-mcp companion binary not found`。** 三处查找（`CODEG_MCP_BIN`、同级、`PATH`）都没命中。用 `CODEG_MCP_BIN` 指一个绝对路径即可，其余功能不受影响。如果两个二进制确实分开放，这一步不能省。

**子 Agent 报 `depth_limit`。** 当前链已经在允许的最深处。这是设置里的一个数字，不是错误。

**Gemini / Claude Code 连不上。** 前者查 `@google/gemini-cli` 这个包本身；后者要同时查 `claude` 是否登录和 `claude-agent-acp` 是否装对，两者共享 `~/.claude`。`preflight` 的诊断输出会把"没装"和"装了但 `PATH` 里没有"分开说。

**Docker 里升级完，重建容器就退回旧版。** 这是预期行为，可写层不落镜像。按 `docker-compose.yml` 的注释：拉新版本镜像并 `--force-recreate`。

**Web 模式下偶发"Request timed out"。** 前端的调用上限是 60 秒，与后端 Agent 探测的上限对齐；如果你的反向代理有更短的读超时，长握手会被中间层先切掉，调代理而不是调 codeg。

## 采用顺序与适用边界

按这个顺序推，每一步都能单独验收：

1. 先用桌面版一次安装，什么协议都不改。验收点是本地已装的 Agent 是否都出现在选择器里、历史能不能搜到。这一步只验证解析器覆盖面，不碰委托。
2. 单独打开多 Agent 协作，先只放开一个目标 Agent，做一次 `@` 委托。验收点是子会话是否成卡、`get_delegation_status` 能否拿到终态、深度超限是否被拒。
3. 需要"提交后不盯着"再上 To-dos。验收点是任务是否真的在自己的 worktree 里、review 列的 diff 是否只含它自己的改动、接受后 base 分支是否只有那次合并。
4. 要团队共享或从手机上看，才起 `codeg-server` 或 Docker。这一步引入访问令牌、绑定地址和 `uploads/` 配额三件事，务必显式设 `CODEG_TOKEN`、按单进程口径估配额。

不适合的情况也很具体：只用一个 Agent 且不需要跨会话检索；仓库不允许 Agent 碰 git 历史（worktree 与两阶段合并整条链都用得上 git 写操作）；需要把编排策略写进代码仓库受审——Codeg 的自动化存在 SQLite 与设置页里，不是可评审的声明式配置。

## 几个自测题

1. 为什么 `parsers/` 里一个 Agent 一个解析器，而不是统一读一种格式？这 15 个解析器共享哪一层逻辑？
2. Cline、Hermes、OpenCode 的备份为什么必须标 `sqlite: true`？不标会得到什么结果？
3. `@` 提及与 Agent 自己调 `delegate_to_agent`，谁先看到用户写的内容？两者共用的是哪个开关？
4. 一个 `depth_limit = 2` 的链上，孙 Agent 能不能再往下派任务？判定为什么只要走 `depth_limit + 1` 层？
5. 升级后 worker 在第 40 秒崩了，supervisor 会不会回滚？给出依据。
6. 同一台机器上开两个 `codeg-server` 共享一个 `uploads/` 目录，`CODEG_UPLOAD_MAX_TOTAL_BYTES` 的实际语义是什么？

## 下一步读哪份代码

按投入产出排序：`src-tauri/src/parsers/mod.rs`（`external_transcript_sources()` 与 `build_agent_parser()` 两个函数就是会话聚合的全部入口）→ `src-tauri/src/models/agent.rs`（15 个内置 Agent 的唯一真相，含 wire 名与显示名）→ `src-tauri/src/acp/agent_mentions.rs`（委托的语义从这里开始）→ `src-tauri/src/acp/delegation/transport.rs` 与 `broker.rs`（异步委托的线格式与状态机）→ `src-tauri/src/work_task/engine.rs`（模块开头三段注释，是理解 To-dos 最快的路）→ `src-tauri/src/update/install.rs` 与 `supervise.rs`（原地升级与自动回滚）。`AGENTS.md` 与 `CLAUDE.md` 除抬头两行外内容一致，121 行，是核对功能开关与条件编译约定的入口。

## 事实口径与失效条件

文中所有断言在 2026-09-19 对 `xintaofei/codeg` 的 `main` 分支 `385eb4f3` 浅克隆逐条核对，命令与文件行号以该提交为准；仓库版本 `0.30.10`，最近一次发布 v0.30.10 在 2026-09-17，创建时间 2026-02-09，许可证 Apache-2.0，Stars 3,531、forks 449。

这些数字要单独看。仓库七个月攒到 3.5k Stars、发布间隔常在一天到几天，说明的是迭代速度，不是功能稳定；`ROUTE_FRAME_VERSION` 的注释明说没有旧版本兼容渲染器，因为它判定"还没发布过值得保留的历史"。委托路由帧、自动升级回滚、To-dos 状态机这三块处在"设计写得很清楚、契约随时会换版本"的阶段。据此不能推出的是：接口在 v1.0 之前保持不变，或者某个 Agent 的适配器版本能被你锁定——`registry.rs` 里的版本是 codeg 锁的，不是你的锁。

三处最容易失效的地方，复核方法也不同：内置 Agent 名单要看 `BUILTIN_AGENT_TYPES`，不要只看 README 第一段（两处都改才有意义）；会话默认路径要看 `external_transcript_sources()` 与各家 resolver；环境变量没有权威清单，`grep` 出来的名字混着 Rust 常量和测试专用项，把它当量级而不是名录。

参考资料里给出全部出处。

## 参考资料

- [xintaofei/codeg](https://github.com/xintaofei/codeg) — 仓库主页，`385eb4f3`
- [`AGENTS.md`](https://github.com/xintaofei/codeg/blob/main/AGENTS.md) — 技术栈、双模式构建、条件编译约定与 `_core` 规范
- [`parsers/mod.rs`](https://github.com/xintaofei/codeg/blob/main/src-tauri/src/parsers/mod.rs) — 外部会话源白名单与解析器构造入口
- [`models/agent.rs`](https://github.com/xintaofei/codeg/blob/main/src-tauri/src/models/agent.rs) — `AgentType` 与 `BUILTIN_AGENT_TYPES`
- [`acp/registry.rs`](https://github.com/xintaofei/codeg/blob/main/src-tauri/src/acp/registry.rs) — 15 个内置 Agent 的启动元数据与 `acp_adapter_relation()`
- [`acp/agent_mentions.rs`](https://github.com/xintaofei/codeg/blob/main/src-tauri/src/acp/agent_mentions.rs) — 路由帧的格式、上限与版本绑定
- [`acp/delegation/`](https://github.com/xintaofei/codeg/tree/main/src-tauri/src/acp/delegation) — `tool_schema.json`、`transport.rs`、`broker.rs`、`depth.rs`
- [`work_task/engine.rs`](https://github.com/xintaofei/codeg/blob/main/src-tauri/src/work_task/engine.rs) — To-dos 状态机与两阶段合并
- [`automation/engine.rs`](https://github.com/xintaofei/codeg/blob/main/src-tauri/src/automation/engine.rs) 与 [`db/entities/automation.rs`](https://github.com/xintaofei/codeg/blob/main/src-tauri/src/db/entities/automation.rs) — 触发、动作与隔离模式
- [`update/`](https://github.com/xintaofei/codeg/tree/main/src-tauri/src/update) 与 [`supervise.rs`](https://github.com/xintaofei/codeg/blob/main/src-tauri/src/supervise.rs) — 验签、换文件、观察期回滚
- [`src/lib/transport/`](https://github.com/xintaofei/codeg/tree/main/src/lib/transport) — 三条传输通路与超时耦合
- [`src-tauri/science/NOTICE.md`](https://github.com/xintaofei/codeg/blob/main/src-tauri/science/NOTICE.md) — 13 个科研 skill 的 vendored 出处与许可证
- [Agent Client Protocol](https://agentclientprotocol.com/) — 公共 registry 与 `distribution` 对象格式
- [obra/superpowers](https://github.com/obra/superpowers) — experts 包来源
- [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) — science 包来源
- [iOfficeAI/OfficeCLI](https://github.com/iOfficeAI/OfficeCLI) — Office 文档与 `officecli watch` 预览
