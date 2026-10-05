---
title: "OpenAI Codex 拆解：终端编程智能体的能力、配置与安全边界"
date: "2026-04-02T12:00:00+08:00"
lastmod: "2026-09-30T00:00:00+08:00"
slug: openai-codex-lightweight-coding-agent
github_repo: "openai/codex"
source_key: "gh:openai/codex"
description: "对着 openai/codex 仓库与官方文档逐条核查后的项目解读：四种产品形态、脚本化安装与三条认证路径、approval 与 sandbox 双轴安全模型、50 余个 slash 命令、codex exec 自动化要点（--full-auto 已废弃），以及从 155 个 workspace 成员看模块划分。"
draft: false
categories: ["技术笔记"]
tags: ["OpenAI", "Codex", "AI 编程", "智能体", "终端工具"]
---

# OpenAI Codex 拆解：终端编程智能体的能力、配置与安全边界

> **判断**：Codex CLI 解决的不是"让模型写代码"——这是所有编码代理的及格线——而是把两个更容易失控的问题做成了可配置的工程边界：模型能自己执行哪些命令（approval），执行时能碰哪些文件和网络（sandbox）。这两条轴线各有明确的配置项、默认值和组合矩阵，配合 `codex exec` 的非交互模式和 JSONL 输出，它才能从"终端里的聊天窗口"变成能放进 CI 的工具。代价是配置面铺得很开：50 余个 slash 命令、十几类子命令、分层的配置优先级，上手时值得先弄清楚安全模型，再谈自动化。

截至 2026-09-30，`openai/codex` 仓库 127,198 Stars、19,875 Forks，Apache-2.0 协议，最新版本 0.159.2（2026-09-29 发布）。仓库 2025-04-13 创建，npm 上 `@openai/codex` 的首个版本发布于 2025-04-16——一年半时间，版本号从 0.1 走到 0.159，发布节奏按天计。

## 一、Codex CLI 是什么

**Codex CLI** 是 OpenAI 提供的本地编程智能体，仓库描述只有一句：**Lightweight coding agent that runs in your terminal**。它面向真实的软件开发任务，不是单行代码补全工具。

Codex 这个名字下至少有四种容易混淆的形态：

| 形态 | 入口 | 适合什么场景 |
|------|------|--------------|
| **Codex CLI** | 终端里的 `codex` | 在仓库里读代码、改代码、审查变更、跑自动化任务 |
| **IDE 扩展** | VS Code、Cursor、Windsurf | 已经在编辑器里工作，想要内联的 Codex 体验 |
| **Codex Web** | chatgpt.com/codex | OpenAI 托管的云端代理，不占用本地机器 |
| **桌面 App** | `codex app` 或 ChatGPT 桌面端 | 图形界面里管理会话，macOS 与 Windows 可用 |

这四种形态共享同一套账号认证与配置分层。本文只展开 CLI：它是最完整的形态，也是其他形态的底层。

### 终端形态的定位

终端是开发者最接近代码库、构建系统、测试工具和 Git 工作流的地方。Codex CLI 把"理解仓库、规划步骤、调用工具、输出结果"这条链路放到本地环境里完成。如果主要诉求是边写边补全，IDE 扩展更顺手；如果诉求是围绕仓库执行一段完整任务，终端形态更自然。

## 二、核心能力、适用场景与边界

按官方文档，Codex 主要覆盖五类能力：

| 能力 | 说明 | 对开发工作的意义 |
|------|------|------------------|
| 写代码 | 根据需求生成或修改代码 | 脚手架、补实现、定向重构 |
| 理解代码库 | 阅读并解释陌生代码 | 接手旧项目或跨团队协作 |
| 审查代码 | `codex review` 面向未提交改动、单个提交或基准分支 | 提交前自查，不改动工作区 |
| 调试修复 | 定位根因、提出修复路径 | 测试失败或行为异常时排障 |
| 自动化任务 | `codex exec` 执行重构、测试、迁移等重复工作 | 把常规工程动作流程化 |

### 更适合用 Codex 的场景

1. **仓库导向任务**："解释这个服务怎么处理认证""找出最危险的几个模块"。
2. **多步工程动作**："先跑测试，再定位失败，再修最小改动"。
3. **脚本化流水线**：在 CI 中生成风险摘要、发布说明、失败原因分析。
4. **需要终端上下文的操作**：配合 Git diff、shell 命令、配置文件、日志目录一起工作。

### 不应夸大它的地方

- 它不是纯离线工具，认证和模型调用都依赖 OpenAI 侧服务。
- 早期第三方资料里的不少命令已经失效：`--full-auto` 被标记为废弃，`codex mcp-server` 子命令已从发行版中移除，`untrusted` 审批策略也已退役。照搬旧教程前先对一遍官方文档。
- 仓库文档演进极快，本文数据截至 2026-09-30 的 main 分支，具体命令以官方文档为准。

## 三、安装与认证

### 3.1 官方推荐安装方式

README 首推独立安装脚本，从 `releases.openai.com` 下载二进制，下载不可用时回退 GitHub Releases：

```bash
# macOS / Linux
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

```powershell
# Windows（PowerShell）
powershell -ExecutionPolicy ByPass -c "irm https://chatgpt.com/codex/install.ps1 | iex"
```

包管理器是备选路径：

```bash
npm install -g @openai/codex
```

```bash
brew install --cask codex
```

也可以从 GitHub Release 直接下载对应平台的二进制（每个 Release 同时提供 DotSlash 文件，方便团队把固定版本的二进制提交进版本控制）。`codex update` 可对支持自更新的安装方式做在线升级。

### 3.2 从源码构建

要研究源码或参与贡献，官方 `docs/install.md` 给出的流程是：

```bash
git clone https://github.com/openai/codex.git
cd codex/codex-rs

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"
rustup component add rustfmt
rustup component add clippy
cargo install --locked just
cargo install --locked dotslash
cargo install --locked cargo-nextest

cargo build
cargo run --bin codex -- "explain this codebase to me"
```

相比早期版本，构建依赖多了 `dotslash`（按需拉取固定版本的开发工具）和 `cargo-nextest`（`just test` 的测试运行器）。

### 3.3 认证方式

三条主路径：

1. **ChatGPT 账号登录**：首次运行 `codex` 时选择 **Sign in with ChatGPT**，用量计入 Plus、Pro、Business、Edu 或 Enterprise 套餐。这是本地交互使用的默认推荐。
2. **API key**：按平台标准 API 费率计费，适合 CI/CD 等程序化场景。登录方式是 `printenv OPENAI_API_KEY | codex login --with-api-key`。注意部分依赖 ChatGPT 工作区或云服务的功能在此路径下受限。
3. **企业 Access Token**：Enterprise 工作区的管理员可以授权成员创建 Codex access token，给受信任的脚本、定时任务和私有 CI runner 用，免浏览器登录。

两个安全细节值得记住：凭据默认缓存在 `~/.codex/auth.json`（明文）或操作系统凭据库，官方原话是"Treat `~/.codex/auth.json` like a password"；`codex login status` 在有凭据时以退出码 0 结束，脚本里可以拿它做健康检查。

## 四、配置与安全模型

### 4.1 配置文件位置

用户级配置在 `~/.codex/config.toml`；项目级配置放在仓库的 `.codex/config.toml`。关键约束是：**只有被信任的项目才会加载项目级配置层**——把一个仓库标记为不信任后，它本地的 config、hooks、rules 全部跳过，用户级和系统级配置照常加载。这个设计直接决定了一个克隆下来的仓库能否改变你机器上 Codex 的执行策略。

### 4.2 配置优先级

官方文档给出的解析顺序，从高到低：

1. CLI flag 与 `-c`/`--config` 一次性覆盖
2. 项目级 `.codex/config.toml`（从项目根到当前目录逐层合并，越近优先级越高，仅限受信任项目）
3. `--profile <name>` 指定的 profile 文件（`~/.codex/<name>.config.toml`）
4. 用户级 `~/.codex/config.toml`
5. 云端托管的 config 默认值（企业工作区下发时）
6. 系统级配置（Unix 上的 `/etc/codex/config.toml`）
7. 内置默认值

容易记错的一点：项目级排在 profile 前面。企业环境还有一层 `requirements.toml` 强约束，可以禁掉 `approval_policy = "never"` 这类危险配置，它的优先级独立于上面这条链。

### 4.3 一个贴近官方文档的配置示例

```toml
model = "gpt-6.1-sol"
approval_policy = "on-request"
sandbox_mode = "workspace-write"
web_search = "cached"
personality = "friendly"

[features]
shell_snapshot = true
multi_agent = true
```

每项都出自官方配置文档。`shell_snapshot` 和 `multi_agent` 的默认值已经是 `true`，显式写出只是为了声明；`web_search` 有四档——`cached`（默认，返回 OpenAI 维护的索引缓存，不实时抓网页）、`indexed`（经搜索索引门控的外部访问）、`live`（实时抓取，等同 `--search`）、`disabled`。`personality` 支持 `friendly`、`pragmatic`、`none` 三种沟通风格。

### 4.4 为什么这些配置重要

| 配置项 | 作用 | 如何理解它 |
|--------|------|------------------|
| `model` | 设定默认模型 | 决定成本、速度与推理能力的平衡，`model_reasoning_effort` 可再调推理力度 |
| `approval_policy` | 决定哪些动作需要人工确认 | 影响自动化程度与安全感，`on-request` / `never` 等取值 |
| `sandbox_mode` | 决定命令的执行边界 | 安全模型的另一半，`read-only` / `workspace-write` / `danger-full-access` 三档 |
| `web_search` | 控制 Web 搜索模式 | 缓存模式降低提示注入暴露面，实时模式更强但更危险 |
| `[windows] sandbox` | Windows 原生沙箱档位 | 原生运行时设 `elevated`（推荐），无管理员权限时退回 `unelevated` |

### 4.5 安全边界要点

approval 和 sandbox 是两个独立轴线，官方文档给了几张典型组合：

| 预设 | 命令 | 行为 |
|------|------|------|
| Auto | `--sandbox workspace-write --ask-for-approval on-request` | 工作区内读写执行全自动，越界或联网需确认 |
| 安全只读 | `--sandbox read-only --ask-for-approval on-request` | 只读浏览与命令执行，适合聊天和规划 |
| CI 只读 | `--sandbox read-only --ask-for-approval never` | 全自动但碰不到写权限 |
| 全开 | `--sandbox danger-full-access` | 仅建议放在隔离容器或 CI runner 里 |

几个容易踩的细节：

- `workspace-write` 模式默认**关闭网络**，要联网需在配置里显式开启。
- 可写根目录内有递归保护路径：`.git`、`.codex`、`.agents` 一律只读，代理改不掉自己的护栏和你的版本历史。
- 打开新仓库时，版本控制目录默认进 Auto 预设，非版本控制目录默认 `read-only`，也可能在你显式信任目录之前一直保持只读。
- `--dangerously-bypass-approvals-and-sandbox` 等于两道防线全拆，官方建议只放在专用沙箱虚拟机里用；需要扩大读写范围时，优先加 `--add-dir` 而不是直接全开。
- 旧的 `untrusted` 审批策略已退役，官方给了迁移组合：`sandbox_mode = "read-only"` 加 `approval_policy = "on-request"`。

## 五、交互式使用：在终端里怎么工作

### 5.1 最基础的启动方式

```bash
codex
```

进入 TUI 后可以直接提问，也可以键入 `/` 唤出 slash 命令面板。会话进行中还能按 Tab 把后续指令排队、按 Enter 向当前回合注入新指令、连按两次 Escape 编辑上一条消息并从那里分叉对话。

### 5.2 常用 slash 命令

官方命令参考收录了 50 余个内置 slash 命令，下面是高频子集：

| 命令 | 用途 | 适用时机 |
|------|------|----------|
| `/model` | 切换模型与推理力度 | 不同任务需要不同模型时 |
| `/permissions` | 调整审批与沙箱档位 | 在 Auto、只读之间切换时 |
| `/plan` | 进入计划模式 | 先规划再动手 |
| `/review` | 审查工作区改动 | 提交前做一轮本地 review |
| `/diff` | 查看 Git diff（含未跟踪文件） | 核对改动是否符合预期 |
| `/status` | 查看会话配置与 token 用量 | 确认模型、权限、剩余上下文 |
| `/compact` | 压缩可见对话释放 token | 长会话之后 |
| `/mcp` | 列出已配置的 MCP 工具 | 确认当前能调用哪些外部工具 |
| `/agent`、`/subagents` | 切换或查看子代理线程 | 用了多代理协作时 |
| `/goal` | 设置、查看、暂停任务目标 | 长任务需要持续跟踪目标时 |
| `/skills` | 浏览并套用本地技能 | 让下个请求按技能指令执行 |
| `/init` | 在当前目录生成 `AGENTS.md` 脚手架 | 给仓库留下持久指令 |
| `/import` | 从 Claude Code 或 Cursor 迁移配置与聊天 | 换工具时搬历史资产 |
| `/exit`、`/quit` | 退出 | 结束会话 |

完整列表见官方 Developer commands 参考页，那里还标注了每个命令的成熟度（Stable / Beta / Experimental）。输入侧还有几个非命令的快捷方式：`@` 搜索工作区文件插入路径，`!` 前缀按当前沙箱策略跑本地 shell，`Ctrl+R` 搜提示历史。

### 5.3 提示写法

Codex 不是读心工具，提示越具体越稳：

```bash
codex "Read the repository, find the auth flow, and explain where token refresh happens."
```

```bash
codex "Review my working tree and identify only correctness or security risks."
```

相比之下，这类指令更容易让结果发散：

```bash
codex "Improve the whole codebase"
```

范围过大、成功标准不清、上下文不足，是发散的三个直接原因。

## 六、非交互模式：`codex exec` 才是自动化主入口

脚本、CI、定时任务里应该使用 `codex exec`（短形式 `codex e`）：

```bash
codex exec "summarize the repository structure and list the top 5 risky areas"
```

### 6.1 `codex exec` 的关键特性

| 能力 | 说明 |
|------|------|
| 非交互执行 | 不打开 TUI，直接在脚本中运行 |
| 输出分流 | 进度写到 `stderr`，最终结果写到 `stdout` |
| 默认只读 | 官方原话："By default, codex exec runs in a read-only sandbox." |
| JSONL 事件流 | `--json` 后 stdout 变成 JSON Lines，含 `thread.started`、`turn.completed` 等事件 |
| 结构化输出 | `--output-schema <file>` 强制最终结果符合指定 JSON Schema |
| 会话续跑 | `codex exec resume --last "..."` 接着上次任务继续，`--all` 跨目录搜索 |
| 免持久化 | `--ephemeral` 不把会话 rollout 文件写到磁盘 |
| stdin 两种模式 | 给 prompt 参数时管道内容作上下文；单独 `codex exec -` 时整个 stdin 就是 prompt |

一个版本演进要注意：`--full-auto` 已是**废弃的兼容 flag**，运行时会打印警告，官方建议改用 `--sandbox workspace-write`。网上还能搜到大量带 `--full-auto` 的旧示例，照搬前先看警告。

### 6.2 几个实用的命令

```bash
codex exec --ephemeral "triage this repository and suggest next steps"
```

```bash
codex exec --json "summarize the repo structure"
```

```bash
codex exec --sandbox workspace-write \
  "Read the repository, run the test suite, identify the minimal change needed to make all tests pass, implement only that change, and stop."
```

CI 里把机器可读进度和自然语言摘要分开 capture，官方推荐的组合是 `--json` 配 `--output-last-message`：

```bash
codex exec --json --output-last-message summary.txt "review the last 10 commits and draft release notes"
```

### 6.3 自动化场景的安全注意

官方文档对 CI 场景的提醒相当具体：

- 需要认证时在命令内联 `CODEX_API_KEY=<key> codex exec ...`，不要把它设成 job 级环境变量——同一个 job 里被检出的仓库代码可以读到它。官方原话："Do not set `OPENAI_API_KEY` or `CODEX_API_KEY` as a job-level environment variable in workflows that check out or run repository-controlled code"。
- GitHub Actions 建议直接用官方 `codex-action`，它内置 Responses API 代理来减少密钥暴露。
- 官方示例工作流的分工值得抄：跑 Codex 的 job 只拿 `contents: read`，diff 存成 patch artifact，由另一个有写权限、不接触 API key 的 job 应用 patch 并开 PR。
- 给 `danger-full-access` 的前提是运行环境本身隔离——独立容器或 CI runner。能力越强，边界越要外置。

## 七、扩展生态：MCP、Apps、Skills 与插件

### 7.1 当前官方稳定的扩展入口

早期的 Codex 文档里扩展能力只有 MCP 一条腿，如今官方稳定支持的入口有四个：

1. **MCP servers**：`codex mcp add` 或在 `config.toml` 写 `[mcp_servers.<name>]` 表，支持 stdio（`command` 必填）和 streamable HTTP（`url` 必填）两种传输，HTTP 服务端支持 OAuth 登录。把某个 server 设 `required = true` 后，它初始化失败会让整个会话直接报错退出，而不是静默跳过。
2. **Apps / Connectors**：ChatGPT 侧的应用连接器，TUI 里用 `/apps` 浏览，提示中以 `$app-slug` 引用。
3. **Skills**：把可复用的指令打包成技能，`/skills` 浏览套用，仓库里有独立的 `skills` 与 `ext/skills` 模块。
4. **插件与市场**：`codex plugin` 提供 install、list、remove，`codex plugin marketplace` 管理市场源，支持 `owner/repo` 这样的 GitHub 简写、Git URL 和本地目录。这条命令链早期只是仓库内部的实验 crate，现在已写进官方命令参考。

另有 `/hooks`（生命周期钩子）、`/experimental`（特性开关）等会话内入口，以及 `codex features enable/disable` 持久化特性开关。

### 7.2 MCP 的作用

MCP（Model Context Protocol）把"模型理解任务"与"外部系统能力"连接起来。没有 MCP 时，Codex 依赖本地仓库、shell、Git 和内置工具；有了 MCP，它可以在沙箱与审批的同一套约束下接入外部能力。

### 7.3 源码里有 ≠ 用户可用

仓库里存在某个 crate，不等于它对应一条公开稳定的用户命令——`codex mcp-server` 就是反例：crate 和二进制都存在过，现已整体移除，官方指路 `codex app-server`。写技术文档时必须区分"源码里有什么"和"官方文档把什么定义为稳定接口"，这也是 AI 生成资料里最常见的错误来源。

## 八、架构分析：从公开仓库结构看 Codex 是怎么拆的

`openai/codex` 公开了完整的 Rust workspace。`codex-rs/Cargo.toml` 的 members 列表在 2026-09-30 已有 **155 个成员**——它不是一个单体二进制，而是一组围绕 CLI、执行、安全和扩展协同工作的 crate。

### 8.1 可以确认的高层模块

| 模块方向 | 代表 crate | 作用 |
|----------|------------|------|
| CLI / 终端界面 | `cli`、`tui` | 命令行入口与终端交互体验 |
| 核心编排 | `core`、`tools`、`code-mode` | 模型交互、任务编排、工具调用 |
| 命令执行 | `exec`、`exec-server`、`shell-command`、`shell-escalation` | 非交互执行、shell 命令与提权策略 |
| 配置与状态 | `config`、`state`、`login`、`keyring-store`、`secrets` | 配置分层、认证与本地状态 |
| MCP / 外部连接 | `codex-mcp`、`ext/mcp`、`rmcp-client`、`connectors` | MCP 与外部工具生态 |
| 安全与隔离 | `sandboxing`、`linux-sandbox`、`process-hardening`、`network-proxy` | 权限边界、进程加固与网络代理 |
| 技能与扩展 | `skills`、`ext/skills`、`hooks`、`features` | 技能、生命周期钩子与特性开关 |
| 云与协作 | `cloud-tasks`、`app-server`、`apply-patch`、`execpolicy` | 云任务、应用服务、补丁应用与执行策略 |

对照一年前的仓库，`ext/` 命名空间（子代理、记忆、目标、队列、图像生成等）和 `cloud-tasks`、`hooks`、`agent-graph-store` 这批 crate 都是后来才出现的——扩展生态的模块化是这一年的主线之一。

### 8.2 这套架构说明了什么

1. Codex 的工程重点是把模型、工具、权限和状态管理拆开，而不是做一个"会说话的命令包装器"。
2. 安全是架构层面的一等公民——sandbox、process hardening、execpolicy 都有独立 crate，不是配置项的事后补丁。
3. 扩展是独立模块——MCP、connectors、skills、plugins 各自成块，面向可组合的工作流。

### 8.3 源码分析应该写到什么程度

基于公开资料，稳妥的写法是模块级分析：解释目录和 crate 的职责边界。没有逐个 crate 深入阅读并交叉验证之前，不要把某条具体执行路径写成"内部一定如此实现"。

## 九、使用场景分析

### 场景一：接手陌生仓库

```bash
codex "Read this repository and explain the architecture, deployment flow, and top risk areas."
```

有效的原因：任务被限定在"理解和解释"，风险低、回报高。

### 场景二：本地变更审查

```bash
codex "Review my working tree and only call out correctness, reliability, or security issues."
```

这是 Codex 的强项之一。专用的 `codex review` 子命令做得更细：`--uncommitted`、`--base`、`--commit` 或自定义 prompt 四选一，输出按优先级排序的发现清单，不改动工作区。

### 场景三：CI 中做结构化自动化

1. 用 `codex exec` 读取仓库并分析失败原因。
2. 用 `--json` 或 `--output-schema` 输出机器可消费的结果。
3. 按上面 6.3 节的官方模式拆分 job：分析只读，修复走 patch artifact 加受控的写权限 job。

### 场景四：让它代替你"全自动改一切"

这通常不是好用法。任务范围失控、审批边界过宽、测试约束不明确，三者占其二，编程智能体就会偏离目标。Codex 把审批和沙箱做成一等配置，本意就是让使用者主动收窄边界，而不是默认信任。

## 十、FAQ

### Q1：Codex 和 GitHub Copilot 的关系怎么理解？

**答：** 互补而非替代。Copilot 更贴近编辑器内的实时辅助；Codex CLI 围绕终端、Git、shell、仓库分析和自动化任务展开。一个更像"写代码时的搭档"，另一个更像"在终端里帮你做完整工程动作的代理"。

### Q2：Codex 可以离线用吗？

**答：** 不能。认证、模型调用以及 Apps 等外部能力都依赖 OpenAI 侧服务。本地能离线完成的是配置和源码构建，跑任务不行。

### Q3：配置文件应该放哪？

**答：** 个人默认放 `~/.codex/config.toml`；项目范围覆盖放仓库的 `.codex/config.toml`，但项目必须先被信任。命令行一次性覆盖用 `-c key=value`，它的优先级最高。

### Q4：自动化场景里应该优先用什么方式认证？

**答：** CI/脚本里优先 API key 路径：登录用 `printenv OPENAI_API_KEY | codex login --with-api-key`，运行时内联 `CODEX_API_KEY`，注意不要设成 job 级环境变量。GitHub Actions 用官方 codex-action。企业工作区可以考虑 Codex access token。本地交互场景走 ChatGPT 登录即可。

### Q5：为什么早期文档里的 `codex serve`、`codex plugin install` 说法要小心？

**答：** 因为它们一度只是源码里的实验实现，不是文档化的稳定接口。现在情况变了：`codex plugin`（含 add/list/remove 与 marketplace 管理）已经写进官方命令参考，可以放心用；本地服务化的稳定入口则是 `codex app-server`（`codex mcp-server` 已移除）。判断标准始终是同一条：官方文档明确列为稳定能力的才写成"已支持"。

## 十一、总结

Codex CLI 把终端、仓库、权限边界、自动化和模型能力放进同一条工作流。它能不能成为日常可依赖的工程工具，取决于三件事：

1. 任务边界要清楚
2. 权限边界要保守
3. 事实边界要尊重官方文档

第三条在这类迭代按天计的项目上尤其重要：一年前写的 Codex 教程，今天照抄大概率会在安装方式、审批策略和自动化 flag 上踩坑。

---

## 参考资料

- OpenAI Codex GitHub 仓库：<https://github.com/openai/codex>
- Developer commands（CLI 命令与 slash 命令参考）：<https://learn.chatgpt.com/docs/developer-commands?surface=cli>
- Config basics（配置基础与优先级）：<https://learn.chatgpt.com/docs/config-file/config-basic>
- Configuration Reference（配置项全集）：<https://learn.chatgpt.com/docs/config-file/config-reference>
- Non-interactive mode（codex exec）：<https://learn.chatgpt.com/docs/non-interactive-mode>
- Sandbox and approvals（审批与沙箱）：<https://learn.chatgpt.com/docs/agent-approvals-security>
- Authentication（认证）：<https://learn.chatgpt.com/docs/auth>
- MCP（Model Context Protocol）：<https://learn.chatgpt.com/docs/extend/mcp>
- Installing & building（docs/install.md）：<https://github.com/openai/codex/blob/main/docs/install.md>

---

🦞 **由钳岳星君🦞撰写 | 2026 年 9 月 30 日更新**
