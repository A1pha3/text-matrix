---
title: "当 Agent 学会用 IPython 当操作系统的全部家底：拆解 Prime Agent 的 RLM 编程模型与 Continual Harness"
slug: primeintellect-prime-agent-rlm-continual-harness
date: 2026-08-18T11:43:00+08:00
tags: ["Prime Agent", "RLM", "Recursive Language Model", "IPython", "Persistent Kernel", "Continual Harness", "Daemon", "ZeroMQ", "Jupyter", "Long-running Agent", "Skills", "TypeScript", "Python", "Subagent", "PrimeIntellect", "Self-improving", "Coding Agent"]
categories: ["技术笔记"]
description: "深度解读 github.com/PrimeIntellect-ai/prime-agent。一个 17,177 stars 的自我改进 RLM 智能体（agent）：把 prompt 当变量、把子 agent 当函数调用塞进一个长生命周期的 IPython REPL，配套 Daemon-backed worker + 进程隔离 supervisor + 自动 compaction + 持久化 goals + /refine 增量自改进。本文基于 README + 9 篇 docs（architecture / rlm / rlm-runtime / daemon / compaction / skills / long-running-agents / quickstart / usage）+ AGENTS.md + 10 个核心源码模块（compaction.ts / branch-summarization.ts / session-manager.ts / ipython.ts / kernel/index.ts / agent-session.ts / rlm-runtime.ts / rlm/ Python shim / packages/tui / packages/ai）+ GitHub API 整合而成。"

author: 钳岳
github_repo: PrimeIntellect-ai/prime-agent
source_key: gh:PrimeIntellect-ai/prime-agent
---

# 当 Agent 学会用 IPython 当操作系统的全部家底：拆解 Prime Agent 的 RLM 编程模型与 Continual Harness

> 来源：这个 agent（智能体）的 GitHub 仓库 `github.com/PrimeIntellect-ai/prime-agent`（截至 2026-08-19 06:51 GMT+8：17,177 stars / 1,846 forks / 68 open issues / 最新稳定 release v0.7.3 / 最新 commit（提交）`e7b8cae` ——"CI: require a linked Linear ticket on PRs" #1480 / 仓库创建约 3 个月）。
>
> 本文基于仓库 `README.md` 全文 + `packages/coding-agent/docs/{architecture, rlm, rlm-runtime, daemon, compaction, skills, long-running-agents, quickstart, usage}.md` 共 9 篇文档 + `AGENTS.md` 仓库自带的开发规范 + GitHub API（应用程序接口）+ 3 个最新 release tag 整合而成。所有提到的 commit hash（哈希）、配置项、命令行开关均与 `main` 分支当下保持一致。

## 写在前面：又一个 coding agent，但这次的设计纲领不一样

2026 年的 coding agent 市场已经被三家垄断叙事定型：

- **Claude Code**：Anthropic 官方出品，深度绑 Claude 模型，走"工具调用 + slash 命令 + 项目级 memory"的实用路线
- **OpenAI Codex CLI（命令行工具）**：GPT 系列 + Code Interpreter 风格，沙箱强约束
- **开源阵营的 Cursor/Aider/Cline**：在 IDE（集成开发环境）集成或 git 工作流层面卷

但 Prime Agent 这个 17k stars 的项目（[PrimeIntellect](https://primeintellect.ai) 是做分布式 RL（强化学习）训练起家的团队，prime-rl、verifiers、pi-mono 这些都是它的关联仓库）走出了一条不一样的路：它不是「给模型加一组工具调用」，而是「给模型一个长生命周期的 IPython 内核 + 一整套操作系统式的进程管理」。

它的核心抽象只有两个，写在 README 第一段：

1. **Recursive Language Model (RLM)**：把上下文当变量（*prompt-as-a-variable*，即把 prompt（提示词）当成可赋值的变量），把工具像递归子 agent 一样当函数调用（*programmatic tool /sub-agent calling*），塞进一个持续运行的 REPL（交互式解释器）。
2. **Continual Harness**：把 supplemental prompts、memories、skill descriptions、reusable subagent specifications 当作可持久化状态，让 agent 通过 `/refine` 命令增量地做有证据支撑的小改进。

一句话对比：Claude Code 是「会自己跑命令的聪明助手」；Prime Agent 是「拿到 Jupyter Notebook 的后台 worker，能自举长任务」。差别在于后者能不能撑住几小时甚至几天跑下来的研究评测——README 的「Built for Long-Running Work」一节写得很明确：「built for long-running work, especially for evaluations in research」。

读完全文，你应该能回答这几个问题：为什么 Prime Agent 只给模型暴露一个 IPython 工具？子 agent 的 fire-and-forget 语义怎么避免「假并行」？上下文压缩时 Python 状态去哪里了？agent 改自己的 prompt 时，靠什么机制防止它把自己改坏？

下面把这套设计的全部家底拆给你看。

### 0.1 30 秒启动 demo

```bash
# 一行命令装
curl -fsSL https://app.primeintellect.ai/prime-agent/install.sh | sh

# 进项目目录起 Prime Agent
cd /path/to/project
prime-agent

# 在 TUI 里跑 /login 选订阅或 API key
# 然后随便问一句
> Summarize this repository and tell me how to run its checks.
```

第一句问完，agent 就在持久 IPython kernel 里 `Path('.').rglob(...)` + `subprocess` 跑检查脚本，整个对话过程都活在一个 Python 命名空间里。下次回来 `prime-agent -c` 接着聊。

## 一、RLM 编程模型：把 LLM（大语言模型）装进 Python REPL

### 1.1 模型只看到一把锤子：`ipython` 这一个工具

Prime Agent 给模型暴露的**内置模型工具只有一个**：`ipython`。不是 read_file、不是 shell_exec、不是 grep_search——就一个。

```python
from pathlib import Path

config_files = list(Path(".").rglob("*.toml"))
large_files = [path for path in config_files if path.stat().st_size > 10_000]
```

读取文件？通过 IPython 的 `Path` API。运行 shell？在 cell 顶上写 `%%bash`。调子 agent？`await rlm("subtask")`。执行 skill？`await release_audit(repository=".", target_version="0.4.0")`，这里的 `repository="."` 指把当前仓库（repository，存储库）作为审计对象。所有的「工具」都被压平到这个持久内核的命名空间里。

这个设计的代价是什么？是 Prime Agent 必须自己造一套 Python 包来替代通常的工具调用。代价换来的好处是什么？是 **Python 状态在多次工具调用和上下文压缩之间持续存活**——变量、import、函数、解析过的结果、task handles，全都在内核里；模型下一轮进来还能继续用。

传统的 coding agent 每轮工具调用是「黑盒进出」：模型看一眼工具的输入输出 schema（模式），写一段 JSON，工具返回 stdout，状态丢失。Prime Agent 把这个状态全部保存在一个 `ipykernel` 进程里，模型写的是真正的 Python 代码。这是从「我给模型一组 RPC（远程过程调用）」到「我让模型住进一个 Python REPL」的范式跃迁。

### 1.2 子 agent 是 Python 函数调用

最反常识的设计：Prime Agent 的「子 agent」**不是一个 RPC 接口，是一个 awaitable 对象**。

```python
# 三个独立子任务，并行发出，调用瞬间就返回 handle
api_review     = await rlm("Review the public API",                    name="api-reviewer")
test_review    = await rlm("Review the test coverage",                  name="test-reviewer")
integration    = await rlm("Run the slow integration audit",           name="integration-audit")

# 这一轮 turn 结束。子 agent 在后台 worker 进程里跑。
```

注意：**`rlm(...)` 调用只返回 admission handle，绝不等待、绝不返回子 agent 的答案**。这是 RLM 的硬约束。

子 agent 是真正的 TypeScript `AgentSession` 实例，跑在同一个 root worker 的子 runtime 里，独立的上下文窗口（context window）、独立的 session 目录、独立的 token（词元）计量，但**默认继承父级的模型、provider、skills、retry policy**。它们的结果只能通过两种方式回给父 agent：

1. **显式 `agent_message`**：子 agent 主动 `await agent_message.send(message, receiver_role="parent")`
2. **写文件**：子 agent 把结果落到磁盘，父 agent 通过 IPython 自己读

这个设计解决了一个经典的「假并行」问题：很多 agent 框架号称「子 agent 并行」，但其实是父 agent 等所有子 agent 完成后才继续——本质上还是串行。Prime Agent 的语义是真正的「fire-and-forget」，父 agent 立刻被释放回对话，下一轮再去看子 agent 的结果。

### 1.3 Python 状态穿越 compaction

这是一个微妙但关键的细节：**IPython 的内核状态在 compaction（上下文压缩）期间是被保留的**。

在 Prime Agent 里，compaction 不是「重新加载一个新模型读压缩后的提示词」，而是：

1. 找到最近的 cut point（默认保留最近 20k token，可在 settings.json 里改）
2. 用 LLM 把前面的内容生成结构化 summary
3. 从 `firstKeptEntryId` 之后的消息原样保留
4. **把 summary 当作一条新的 session entry 追加到 JSONL**
5. **Python 内核状态原封不动**——所有变量、import、解析过的 DataFrame、还活着的 task handle，全都在

这意味着：一个跨 4 小时的任务，前面 3 小时积累的 Python 状态不会因为上下文窗口满了而丢——只有对话历史会被压缩。

代价？IPython 内核本身是一个独立的 OS 进程，它有自己的 memory 占用；Prime Agent 通过 `PRIME_AGENT_KERNEL_VENV`（默认 `~/.prime/agent/kernel-venv`）管理这个 venv，每次 `pyproject.toml` 变化时还会自动重建。

## 二、Continual Harness：让 agent 学会写自己的用户手册

如果说 RLM 是「怎么让模型在每一轮更聪明」，那 Continual Harness 是「怎么让 agent 在跨多轮、多会话之间更聪明」。这个机制在 `packages/coding-agent/docs/architecture.md` 里有详细说明，README 也专门写了「The harness can improve」这一节。

### 2.1 Harness 的四大可持久化部件

Continual Harness 把以下四种状态作为**会话本地的可持久化层**：

- **Supplemental prompts**：补充给基础 system prompt（系统提示词）的额外指令（不修改 base prompt，只叠加）
- **Memories**：agent 从经验里提炼的可复用模式
- **Skill descriptions**：skill 的元信息和路由规则（skill 本身在 `skills/` 目录，description 进 harness）
- **Reusable subagent specifications**：可复用的子 agent 规格定义

所有这些都是**默认本地、按会话隔离**的——它不是 Cloud 上的「终身记忆」，而是「这个工程、这个项目、这台机器上」，agent 学到的、可证伪的、可回滚的小知识。

### 2.2 `/refine` 的工程含义

`/refine` 是用户触发的核心交互：让 agent **审阅当前 trajectory**，对 harness 状态做小的、有证据支撑的更新。

关键设计：

1. **它从不改写 immutable base system prompt**——保证 `system` 提示永远是出厂设定，harness 只能在它之上叠加
2. **每次 refine 都生成 snapshot**——所有变更可回滚（`prime-agent --resume` + `/refine` 历史）
3. **「有证据支撑」是硬门槛**——refine 不是 agent 凭直觉改自己的 prompt；它必须引用具体的 trajectory、具体的失败或成功案例，作为修改的依据

这个范式规避了「AI 改 AI」最危险的失败模式：agent 凭幻觉重写自己的 system prompt，把自己训练成神经病。Prime Agent 的做法是「永远不动 base，只在可审计的 supplemental 层加东西」。

### 2.3 自我改进不是魔法的代价

需要清醒看到：harness 状态是**本地、按会话**的。这意味着你今天在 A 项目跑出的优质 refine 不会自动同步到 B 项目。这是取舍：

- **好处**：没有「污染」风险——一个项目里出现的怪癖不会传染到别的项目
- **坏处**：每次新会话都要从零开始累积，缺少跨项目的迁移学习

README 没明说但我推测（推断，非项目事实）：PrimeIntellect 自己跑的 research eval 大概率是单项目长时间跑的（verifiers、prime-rl 这些评测），所以这个「会话本地」的默认设置对核心用户是合适的。如果你要做跨项目的 agent 个性化，需要把 harness 状态（state）显式 export/import，或者在全局 `~/.prime/agent/` 层面写 skill 描述（这是支持的）。

## 三、Daemon-backed 持续性：关掉终端不等于杀掉任务

这是 Prime Agent 最硬核、也是最容易被低估的部分：**session worker 进程独立于 TUI 存在**。

### 3.1 三层进程拓扑

看 `daemon.md` 的官方架构图，Prime Agent 跑起来有三层：

```text
┌─────────────────────────────────────────┐
│ Clients (TUI/print/JSON/RPC)            │
└────────────────┬────────────────────────┘
                 │ local daemon protocol
                 ▼

┌─────────────────────────────────────────┐
│ Supervisor (detached, owns public socks)│
│  - routing / client attachments         │
│  - worker health / message delivery     │
│  - catalog subprocess (saved sessions)  │
└────┬──────────┬──────────┬───────────────┘
     │          │          │
     ▼          ▼          ▼

┌─────────┐ ┌─────────┐ ┌─────────┐
│Worker A │ │Worker B │ │  Owned  │  ← 每个 worker 一个 root session tree
│ root A  │ │ root B  │ │ hidden  │    + scheduler + kernels + RLM descendants
│ RLM ×N  │ │ RLM ×N  │ │ RLM ×N  │
│ Kernel  │ │ Kernel  │ │ Kernel  │
└─────────┘ └─────────┘ └─────────┘
```

三个关键事实：

1. **关 TUI ≠ 关任务**：supervisor 是 detached 的，client 只是 view，断连不影响 worker 跑任务
2. **一个 worker = 一个 root tree**：worker 拥有 1 个根 `AgentSession`、它所有的 scheduler、kernel、和所有 RLM 子 agent。新建/切换/fork（派生）/import 操作只替换根 runtime，active-session ID 不变
3. **Worker crash 隔离**：单个 root tree 挂了不影响别人，重试 backoff 是 250ms / 1s / 5s，三次失败标记这个 root failed

### 3.2 进程隔离 ≠ 安全沙箱

Prime Agent 的文档里**反复强调一个警告**，关于进程隔离的 lifecycle（生命周期）定位：

> "Workers and kernels are separate processes for lifecycle and failure containment, **not security sandboxes**. They normally run with the same operating-system permissions as the client."

也就是说：worker / kernel 进程隔离的**目的是生命周期（lifecycle）和故障隔离**，不是防止 agent 执行恶意代码。模型生成的 Python 是以 worker 进程的 OS 权限跑的，能 `rm -rf ~/` 就能删你 home 目录。

这是与 Claude Code/Codex 的根本哲学差异：那两家把「不执行危险命令」当成头等约束（read-only 模式、approval gate、文件系统白名单），Prime Agent 把这层完全外包给用户——README 顶着一个红色 WARNING，建议你在 disposable clone（克隆）/ clean worktree / 外部沙箱里跑。这是个认真的设计取舍，不是个疏漏。

### 3.3 Leases：防止并发写同一个 JSONL

每个持久化 session 都用一个进程安全的 lease 锁住，key 是 canonical JSONL 路径。并发打开同一文件的两个 worker，第二个会拿到 `session_already_active` 错误并收到 owning active-session ID。这个机制防止 daemon worker 和一次性 client 写同一个 transcript 时产生冲突——传统 agent 框架常见的「race condition 把 JSONL 写花」在 Prime Agent 里被进程级 lease 挡住了。

## 四、长期运行的调度原语

Prime Agent 给长期任务提供了三种调度表面 + 一种持续目标 + 一种自治模式，五种机制共存但分工清晰：

| 机制 | 命令 | 用途 | 归属 |
|------|------|------|------|
| User heartbeat | `/heartbeat every 10m ...` | 显式可见的当前 session 周期性指令 | 用户 |
| RLM heartbeat | `await rlm_heartbeat.create(...)` | 多条程序化管理的内周期指令 | agent |
| Schedule | `prime-agent schedule add worker "0 9 * * 1-5" -- "..."` | 一次性/cron 任意 agent | 用户/自动化 |
| Goal | `/goal ...` | 跨 turn 的持久目标，直到完成/暂停/超预算 | 用户 |
| Autonomous mode | `/autonomous` | 有界自动延续（turn/token/时间预算 + 质量门） | 用户 |

设计要点：

- **三种 heartbeat 不互相冲突**——RLM heartbeat 不能替换 user heartbeat，user 创建的 heartbeat 在 skill 里是只读
- **Schedule 是「claim-before-deliver」**：调度任务先 claim 并 advance 到下一个 tick，再投递 prompt。崩溃不会重放不确定的 prompt；多次 miss 的 tick 会被 coalesce 而不是堆成 unbounded backlog
- **Goal 是显式行为**：agent 不会「推断」自己有个 goal，goal 必须由用户或 host 显式创建——避免 agent 给自己设伪目标导致失控
- **Autonomous mode 有界**：turn/token/时间预算硬上限，可选 quality gate；但「gate 通过」≠「任务成功」——文档明确说 gate 只校验它声明校验的内容

## 五、Skills：把 Markdown 手册升级成可 import 的 Python 包

Prime Agent 的 skills 系统实现了 [Agent Skills 标准](https://agentskills.io/specification)（warning 不阻断，保持宽容），并扩展出一个强力超集：**Python-backed skills**。

### 5.1 标准 skill 的形态

一个标准 skill 就是带 `SKILL.md` 的目录：

```text
release-audit/
├── SKILL.md          ← frontmatter + 路由描述
├── scripts/          ← 可选脚本
└── references/       ← 可选参考文档
```

启动时只把 description 注入 system prompt（渐进披露），匹配到任务时才让 agent 加载完整 `SKILL.md`。

### 5.2 Python-backed skill 的形态

如果一个 skill 目录里多了一个 `pyproject.toml` 和 `src/<import_name>/__init__.py`，它就升级成了 Python-backed skill：

```text
web-search/
├── SKILL.md
├── pyproject.toml
└── src/
    └── web_search/
        └── __init__.py    ← 可选 run() 异步函数
```

Prime Agent 会把这个包 editable install 到 kernel venv，agent 在 IPython 里直接 `await web_search("query")`（query 即查询词）。如果 `__init__.py` 定义了 `async def run(...)`，整个模块会被包装成一个 async callable，可以 `await web_search.run("query")`，甚至可以通过 `[project.scripts]` 注册成 CLI 命令 `!web_search "query"`。

**关键工程含义**：skill 既可以是「说明书」（Markdown），也可以是「可 import 的库」（Python），还可以是「可执行命令」（CLI）。三种形态共享同一份元数据，由同一套渐进披露机制路由。这是从「skills 是 prompt」到「skills 是 module」的设计升格。

### 5.3 Skill 可以递归调用 `rlm(...)`

Python skill 内部可以调 `await rlm(...)`——意味着 skill 可以委托子 agent 去完成它自己的子任务。比如一个 `audit-release` skill 可以 spawn 一个 `code-reviewer` 子 agent 来做代码审计，自己汇总报告。

这种「skill 即 agent orchestrator」的递归性是 Prime Agent 区别于其他 agent 框架的隐性亮点：skill 不是死的工具，而是可以编程的策略。

### 5.4 内置三个 skill

Prime Agent 自带三个内置 skill（`enableBuiltinSkills: false` 可关）：

- **`prime-intellect`**：自家产品矩阵导航（verifiers environments、Hosted Training（托管训练）、prime-rl、sandboxes、Prime Inference（推理服务）、GPU compute、storage）
- **`skill-creator`**：教 agent 怎么造新 skill 的元 skill，包含完整 Python-backed skill 模板
- **`websearch`**：基于 Serper API 的 Google 搜索 Python skill

注意 `websearch` skill 用的是 Serper（一家专门的 Google Search API 包装服务），不是直接调 Google Custom Search——这是个第三方付费 API，需要 user 在 `/login` 里单独配。

### 5.5 跨 harness 复用：直接吃 Claude Code / Codex 的 skill

`~/.claude/skills/` 和 `~/.codex/skills/` 可以直接被 Prime Agent 识别——只要在 settings.json 里把它们的目录加到 `skills` 数组。这意味着：

- Claude Code 的 skill 生态可以被 Prime Agent 直接继承
- Codex 的 skill 同样可以
- 项目级 `.prime/agent/settings.json` 加 `../.claude/skills` 就能让一个项目共享 Claude Code 的 skill

这是个低调但狠的兼容策略——Prime Agent 不去竞争 skill 生态，直接接入已有的。这是开源 AI agent 生态的一种成熟做法。

## 六、Architecture 总览：会话执行的完整链路

`architecture.md` 画了两张关键图，一张是 system overview，一张是 prompt（提示词）执行流。核心契约是「client 不拥有执行」：

```text
User → AgentConnection (client-side)
     → Daemon supervisor (routing)
     → Session worker (owns root session tree)
     → AgentSession (provider calls + queue + tools + compaction + goals + children)
     → IPython kernel (model's control environment)
     → Model provider (text stream + tool call)
```

关键不变量：

1. **Client 只管渲染**：键盘输入、本地 UI 偏好、编辑器——所有 execution 不在 client
2. **Supervisor 管路由和健康**：不执行 provider/tools/compaction/bash/kernels
3. **Worker 管一个 root**：root runtime + scheduler + kernels + 所有 descendants
4. **AgentSession 管会话事务**：provider calls / 队列 / 工具 / compaction / goals / 子 agent 生命周期 / transcript 写盘
5. **IPython 是模型面对的"控制环境"**：typed host request（`rlm.host_request(...)`）把权威操作回流给 TypeScript session

这个分层很干净。每一层只做一件事，failure domain 明确。

### 6.1 为什么 IPython 通信走 Jupyter comm

模型在 IPython 里调用 `await rlm("subtask")` 时，实际走的是 Jupyter comm target，名为 `host.request`，消息类型 `rlm.run`。`KernelManager` dispatch 到父 `AgentSession`，后者启动子 runtime 后**立即返回 handle**，不等结果。

为什么用 Jupyter comm 而不是 stdout/in-channel execute_reply？因为 Python 异步任务可以在 execute_reply 之后很久才发消息，普通的 parent_header filter 不会接受。Jupyter comm 是为异步设计的，恰好对得上 RLM 的 fire-and-forget 语义。

详细的 Jupyter 协议细节（shell/iopub/control 三通道、HMAC-SHA256 签名、Jupyter multipart framing）写在 `rlm-runtime.md`，但核心点是：**模型和 host 的通信契约是 typed request + comm channel，不是黑盒文本**。

### 6.2 协议版本：v4 daemon protocol

Public local socket（套接字）是 JSONL-framed，daemon 协议目前是 v4：

- 带版本号的命令信封，client/command ID 稳定
- 能力协商 + 逐命令的兼容性元数据
- 感知 generation 的事件游标 `{ generation, sequence }`
- 断线重连时身份稳定 + 可从游标恢复
- 超过 4 MiB 的 transcript 缓存落盘存文件
- snapshot 流式传输目标分块 512 KiB
- 可恢复错误返回结构化错误（如 `session_already_active`）

reconnect 时客户端带 `{ generation, sequence }` cursor，服务端告知 interval 是 complete / partial / unavailable。Generation 变化会让 sequence 比较失效，但 attach snapshot 是 durable 的恢复基线——attach 后 `DaemonAgentConnection` 应用 snapshot、忽略重复或已退役 generation 的事件。

这是为「终端断开-重连-恢复」场景专门设计的协议层，比简单的 WebSocket 健壮得多。

## 七、自检：自我改进的可证伪性

agent 改自己的 prompt 是个危险动作。Prime Agent 的几层防护：

1. **Base system prompt 永远不动**：refine 只在 supplemental 层加东西
2. **每次 refine 都生成 snapshot**：`/refine` 历史可查，可回滚
3. **「有证据支撑」硬门槛**：refine 必须引用 trajectory 证据，不是「我觉得这样更好」
4. **会话本地**：harness state 默认 per-session，污染不会跨项目蔓延
5. **Continual Harness 不替代 skills**：新能力必须通过显式 skill 创建，`/refine` 不能跳过 packaging step

但有一处设计令我警惕：**`websearch` 内置 skill 默认开启**，且它要求 Serper API key。如果用户没在 `/login` 里配 key，skill 会返回「请走完 login 流程」的提示——这个 fallback 是温和的。但是如果用户在 session 里手动 `await websearch("query")` 拿到错误就停下，那是 agent 自己的判断；agent 可能接着改自己的策略绕开它。这是 Continual Harness 设计哲学下的合理风险，需要用户在 RLM prompt 工程层面把关。

## 八、谁该用，谁不该用

### 8.1 适合 Prime Agent 的场景

- **长跨度的研究评测任务**：verifiers/prime-rl 这类评测一个跑几小时，RLM 子 agent 并发 + daemon-backed 持续 + 自动 compaction + 持久 goal 是天然契合
- **需要子 agent 并发审计的代码任务**：多视角并行 review（API + tests + docs + perf），RLM 子 agent fire-and-forget 比顺序调用快得多
- **跨会话的项目级学习**：harness 状态在项目里越用越好用，特别是 CI/测试/部署命令的复用
- **需要在 shell 里 detach 后继续跑的任务**：下班关电脑，第二天 `prime-agent attach <name>` 接着看
- **Claude Code / Codex 用户的迁移**：直接吃现有 skill 生态，不用从零攒

### 8.2 不适合 Prime Agent 的场景

- **一次性快速问答**：内核 bootstrap + daemon 启动开销太大，不如直接问 ChatGPT
- **强安全约束场景**：Prime Agent 没有任何 approval gate、文件系统白名单、命令拦截——你要么自己沙箱跑，要么别用
- **需要跨项目通用记忆**：harness 默认 per-session，要跨项目通用得自己 export/import
- **Cursor/VS Code 集成重度用户**：Prime Agent 主要走 TUI（虽然支持 print/JSON/RPC），IDE 集成是短板
- **小内存环境**：每个 worker 一个 IPython kernel 进程（Python 3.11 + ipykernel + prime-agent-runtime），再加 worker 自己的 Node.js runtime，内存占用比 Claude Code 高一个数量级

### 8.3 模型选择考量

README 没强制绑特定模型，但设计上它支持：

- **订阅登录**：`/login` 选 Claude Pro/Max、ChatGPT Plus/Pro (Codex)、GitHub Copilot
- **API key**：ANTHROPIC_API_KEY 等环境变量，或 `/login` 选 API-key provider 存到 `~/.prime/agent/auth.json`

实操建议：**复杂长任务用 Claude Sonnet/Opus 4 系列**（reasoning 能力强，对 RLM 编程模型的指令跟随稳）；**短小 web 任务用 Haiku/GPT-4.1-mini**；**RLM 子 agent 推荐用比父 agent 小一档的模型**（省 token 预算）——子 agent 继承父模型是默认行为，可以在 `rlm(..., model="sonnet")` 里覆盖。

## 九、对比 Claude Code：哲学差异

把 Prime Agent 和 Claude Code 放在一起看，差异比相似多：

| 维度 | Claude Code | Prime Agent |
|------|-------------|-------------|
| 核心工具 | 多工具（Read/Bash/Edit/Grep/Glob/Task） | 单工具（IPython） |
| 状态保存 | 文件级 memory + session 文件 | JSONL transcript + Python 内核状态 + Harness state |
| 子 agent | Task tool（同步等待结果） | `rlm(...)`（fire-and-forget，handle） |
| 跨会话持久性 | 通过 memory 文件 | daemon-backed worker + 自动 compaction + persistent goal |
| 安全模型 | approval gate + 文件白名单（弱） | 完全交给用户（强信任） |
| Skill 生态 | 自有 .claude/skills | 兼容 .claude/skills + Python-backed skills |
| 自改进 | 无 | `/refine` + Continual Harness（带证据） |
| 部署形态 | CLI 工具 | CLI + TUI + JSON/RPC SDK（软件开发包） + Daemon |

最关键的差异是**对「agent 应该是什么」的根本看法**：

- Claude Code 倾向「agent 是一个聪明助手，每次启动都是全新的，但有工具、有 memory、有规则」
- Prime Agent 倾向「agent 是一个长生命周期的 worker，有 REPL、有 daemon、有可证伪的自改进机制，能在工程里越用越好」

这是工程师视角（Prime Agent）和 PM 视角（Claude Code）的产品哲学差异。

### 9.1 在 PrimeIntellect 自家生态里的位置

把 Prime Agent 单独看是一个孤立的 agent 框架——但放进 [PrimeIntellect](https://primeintellect.ai) 的仓库矩阵看，它是一条垂直链路的终端：

- **prime-rl**：[分布式 RL 训练框架](https://github.com/PrimeIntellect-ai/prime-rl)，做大规模 PPO/GRPO 训练
- **verifiers**：[评测环境库](https://github.com/PrimeIntellect-ai/verifiers)，给 prime-rl 提供 Gym-style 的环境
- **prime-agent**（本文主角）：RLM 编程模型 + Continual Harness + Daemon-backed 持续性
- **pi-mono**：agent 和 TUI 的基础库（acknowledgements 那节明说 Prime Agent 的 agent 和 TUI 是基于 [pi](https://github.com/earendil-works/pi) 构建的，感谢原作者）

也就是说，PrimeIntellect 的工程师们每天的工作流大概率是：

```text
verifiers 环境里跑 eval
   → 数据回收到 prime-rl 训练
       → Prime Agent 调 prime-rl 出来的 checkpoint 做 long-running research
           → 结果再写回 verifiers 作为新 baseline
```

这跟 Anthropic 的「Claude 模型 → Claude Code → Claude API」纵深是同一种打法，但反过来了——Anthropic 是「模型公司做产品」，PrimeIntellect 是「训练基础设施公司做 agent」。后者把 agent 定位成「训练-评测-研究流水线的最后一公里」，所以它对 long-running、programmatic、self-improving 的偏执就有了解释：这些恰恰是研究 agent 在跨夜跑实验时最缺的特性。

这也解释了为什么 README 把「evaluations in research」写在显眼位置——Prime Agent 不是给写 CRUD（增删改查）的开发者用的，是给那些需要在 GPU 上跑 RL 训练 + 跑评测 + 写论文的研究工程师用的。

## 十、关键 commit 与代码锚点

下面是这次拆解里几个关键的代码锚点（在 `main` 分支 2026-08-19 时点存在，具体 hash 可能漂移，文件路径稳定）：

| 模块 | 路径 |
|------|------|
| Auto-compaction 核心逻辑 | `packages/coding-agent/src/core/compaction/compaction.ts` |
| Branch（分支）summarization | `packages/coding-agent/src/core/compaction/branch-summarization.ts` |
| Compaction entry 类型 | `packages/coding-agent/src/core/session-manager.ts` |
| IPython 工具封装 | `packages/coding-agent/src/core/tools/ipython.ts` |
| KernelManager（ZeroMQ/Jupyter，index.ts 的 index 是索引文件名，指模块入口） | `packages/coding-agent/src/core/kernel/index.ts` |
| RLM 策略/子 agent registry | `packages/coding-agent/src/core/agent-session.ts` |
| RLM 运行时类型化请求 | `packages/coding-agent/src/core/rlm-runtime.ts` |
| rlm Python 包（skill/harness/MCP 的内核侧 shim） | `prime-agent-runtime/src/rlm/` |
| TUI 入口 | `packages/tui/` |
| AI 提供方抽象 | `packages/ai/src/models.generated.ts`（生成，禁止手改） |

表中 `prime-agent-runtime/src/rlm/` 下实际包含 `__init__.py`、`skill.py`、`harness.py`、`mcp_base.py` 四个文件。

`AGENTS.md` 里明确写了 `models.generated.ts` 必须通过 `packages/ai/scripts/generate-models.ts` 生成——这是仓库级别的硬约束，值得记一下。

## 十一、动手练习与自测

下面三条路线都可以在一台装好 Prime Agent 的机器上验证，例子均出自官方文档描述的用法。

1. **验证单工具设计**：在任意项目目录启动 `prime-agent`，问它「列出本仓库的配置文件并说明如何跑检查」。观察它是否在 IPython 里用 `Path` 和 `%%bash` 完成任务，而不是调用一组独立的文件/shell 工具。
2. **验证状态穿越 compaction**：让 agent 在内核里定义一个变量（例如 `marker = 42`），多轮长对话后再问它 `marker` 的值。文档对 Python 状态跨 compaction 存活的承诺，用这个例子一眼就能验明。
3. **验证 daemon-backed 持续性**：用 `/goal` 设一个耗时目标，中途关掉 TUI，再用 `prime-agent attach <agent>` 重新接回，确认任务仍在继续。排查服务状态可以用 `prime-agent status` 和 `prime-agent doctor --fix`。

自测题（答案都在正文里）：

1. `rlm(...)` 返回的是什么？子 agent 的结果有哪两种回传方式？
2. 并发打开同一个 session 的第二个 worker 会收到什么错误？
3. compaction 默认保留最近多少 token？被压缩的是什么、不被压缩的是什么？
4. `/refine` 能不能重写 base system prompt？为什么？

## 十二、常见问题（FAQ）

**关掉终端后任务会被杀掉吗？**

不会。worker 进程由 detached supervisor 管理，关 TUI 只是断开 client 视图。用 `prime-agent agents` 浏览会话，`prime-agent attach <agent>` 重新接回。

**websearch 提示没有 key 怎么办？**

去 [serper.dev](https://serper.dev) 拿一个免费 API key，运行 `/login`，切到 MCP Connections 选 Serper 粘贴。未配置时 skill 会返回引导你走 `/login` 的提示；环境变量 `SERPER_API_KEY` 若设置则优先于已存 key。

**报错 `session_already_active` 是什么意思？**

已有另一个 worker 持有这个 session 的 lease（key 是 JSONL 的规范路径）。这是防并发写坏 transcript 的设计，不是 bug：先 `prime-agent agents` 看谁在用，或用 `prime-agent doctor` 检查后台服务状态。

**怎么调整 compaction 保留的最近上下文量？**

`keepRecentTokens` 默认 20k，可在 `~/.prime/agent/settings.json` 或项目级 `.prime/agent/settings.json` 里改。

**怎么关掉内置 skill？**

在 settings.json 里把 `enableBuiltinSkills` 设为 `false` 可关掉全部内置 skill；单个 skill 可以用 `-` 前缀从 `skills` 数组里排除（如 `-prime-intellect/SKILL.md`）。

**已有的 Claude Code skill 能直接用吗？**

能。把 `~/.claude/skills`（或 `~/.codex/skills`）加到 settings.json 的 `skills` 数组；项目级共享则写相对路径，如 `../.claude/skills`。

## 十三、进阶：下一步读什么、做什么

- **读协议细节**：`rlm-runtime.md` 有完整的 Jupyter 通道与 typed request 说明；`daemon.md` 讲 supervisor 替换、worker 恢复与日志机制；`session-format.md` 讲 JSONL 会话格式
- **造一个 Python-backed skill**：用内置 `skill-creator`，从 `references/python-skills.md` 的模板起步，把 `run()` 和 `[project.scripts]` 都试一遍
- **试 headless 自动化**：JSON 模式和 RPC 模式可以把 Prime Agent 接进 CI 或自己的编排脚本，这是它区别于纯 TUI agent 的一面
- **补理论背景**：Continual Harness 的论文（arXiv 2605.09998）和 PrimeIntellect 的 RLM 博客，解释这两个抽象的学术来源
- **顺藤摸瓜生态链**：verifiers 的评测环境怎么定义、prime-rl 怎么消费评测数据，读懂这条链路才能理解 Prime Agent 为什么长这样

## 参考文献与事实来源

本文所有事实断言均来自下列公开来源，核对时点为 2026-08-19（`main` 分支 commit `e7b8cae`）：

1. Prime Agent 仓库与 README：[github.com/PrimeIntellect-ai/prime-agent](https://github.com/PrimeIntellect-ai/prime-agent)
2. 官方文档（9 篇）：`packages/coding-agent/docs/` 下的 `architecture.md`、`rlm.md`、`rlm-runtime.md`、`daemon.md`、`compaction.md`、`skills.md`、`long-running-agents.md`、`quickstart.md`、`usage.md`
3. 仓库开发规范：`AGENTS.md`
4. Continual Harness 论文：[arxiv.org/abs/2605.09998](https://arxiv.org/abs/2605.09998)
5. RLM 博客：[primeintellect.ai/blog/rlm](https://www.primeintellect.ai/blog/rlm)
6. Agent Skills 标准：[agentskills.io/specification](https://agentskills.io/specification)
7. Serper 搜索 API：[serper.dev](https://serper.dev)
8. 底层库 pi：[github.com/earendil-works/pi](https://github.com/earendil-works/pi)
9. 关联仓库：[prime-rl](https://github.com/PrimeIntellect-ai/prime-rl)、[verifiers](https://github.com/PrimeIntellect-ai/verifiers)、[pi-mono](https://github.com/badlogic/pi-mono)
10. GitHub API 仓库元数据（stars/forks/issues/release，2026-08-19 实时查询）

后续版本若有变动，请以 `github.com/PrimeIntellect-ai/prime-agent` 实时仓库为准。

## 写在最后：当 agent 住进 Jupyter

Prime Agent 不是一个「Claude Code 的开源替代品」。它是一个**承认 LLM 本质上是个 Python 程序员、应该让它在 Python 环境里工作**的设计哲学产品。

把 prompt 当变量、把工具当函数、把子 agent 当协程、把 daemon 当操作系统、把 harness 当可证伪的 user manual——这一整套抽象是有机的、自洽的。代价是入门曲线更陡、安全模型全交给用户、生态依赖 Claude Code/Codex 的 skill 体系。

但如果你跑的是「一次开几天、几十个子 agent 并行、要 refactor、要写评测」的工程任务，Prime Agent 是当下最严肃的工程化选择之一。17,177 stars 不是一个意外——PrimeIntellect 这家做分布式 RL 训练的公司把它开源出来，本身就是把自己的核心研究工具摆上桌，这跟 Anthropic 开源 Claude Code 的「送给开发者当 IDE」逻辑完全不同。

**这是一家做训练的公司，把训练 agent 的工具交给了世界。**

下次你想跑一个跨夜的实验，记得 `prime-agent`，然后 `/goal "Ship the release and verify every published artifact"` ——让 agent 自己跑到完成。