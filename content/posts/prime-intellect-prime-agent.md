---
title: "Prime Agent：用 Python REPL 当 Agent 编程模型的 RLM 范式"
date: 2026-08-07T20:50:00+08:00
draft: false
tags: ["AI Agent", "RLM", "TypeScript", "Python", "IPython", "Self-Improving", "Open Source"]
categories: ["技术笔记"]
description: "GitHub 5.2k stars、Karpathy 站台的 Prime Agent 用 RLM 范式重写 Agent 编程模型——把 Python REPL 当 Agent 的控制平面，让模型程序化管理自己的 context。"
slug : prime-intellect-prime-agent

---

# Prime Agent：用 Python REPL 当 Agent 编程模型的 RLM 范式

`PrimeIntellect-ai/prime-agent` 在 GitHub 上是 5.2k stars / 416 forks 的项目。

2026-05-08 创建，到 2026-08-07 共 92 天。MIT 协议，TypeScript 占 11.5M 行（约 97%）。版本节奏 3 天一版（v0.7.0 8-05、v0.6.x 8-04/05、v0.5.x 8-03/04）。**Karpathy、John Schulman、Dylan Patel、Founders Fund、NVIDIA** 在投资人/站台人名单上。

这是它的定位、栈位、和架构文档三件套读完后的三条判断：

1. 它不是"又一个 Claude Code"，是 **Agent 编程模型的重写**——把 function calling + tools 范式换成 persistent REPL + 程序化调用。
2. 它背后是 Prime Intellect 全栈——RL 训练、推理、计算、沙箱、Agent 五层同步开源。
3. 它在 5 个维度同时领先 self-improving / long-running / agent-to-agent / 子代理 / 开源协议——同时全做的不多。

后面 12 节展开这三条。

---

## 一、它是什么——先把定位装进脑子

Prime Agent 的官方描述只有一行：

> "A self-improving RLM agent for coding workflows and long-running autonomous tasks."

三个关键词：

- **RLM agent** — Recursive Language Model Agent，递归语言模型驱动
- **self-improving** — `/refine` 命令让 agent 自己改 harness 的可重用 lesson
- **long-running** — 后台守护，关掉终端不杀 session，跨天跨周持续工作

这三个词组合在一起覆盖一个完整的链路：写代码 → 持续写 → 越写越好。Claude Code、Codex、Cursor 都不做"自改进"这条线；Prime Agent 直接跨过去。

---

## 二、它背后是 Prime Intellect 全栈

Prime Agent 是 Prime Intellect 公司开源的旗舰项目，是 **The Open Superintelligence Stack** 的 Agent 编程模型层。

Prime Intellect 把整套 AI Infra 开源了：

| 模块 | 仓库 | 做什么 |
|---|---|---|
| **Prime Agent** | `PrimeIntellect-ai/prime-agent` | Agent 编程模型（TUI + CLI） |
| **Verifiers** | `PrimeIntellect-ai/verifiers` | RL 环境库（2,500+ 社区环境） |
| **Prime-RL** | `PrimeIntellect-ai/prime-rl` | 大规模异步 RL 训练框架 |
| **Sandboxes** | （内置） | 安全代码执行（deepswe/deepcoder/i3-math） |
| **Inference** | （托管） | 专用 GPU + LoRA 适配器 + Serverless API |
| **Compute** | （全球网络） | 1-256 GPU 即时调度 |

Anthropic / OpenAI 走闭源路线，Prime Intellect 走 **全栈开源 + 训练托管**。

投资人和站台人：

- **Founders Fund / Radical / NVIDIA / Intel** — 顶级机构 + 顶级算力供应商
- **Andrej Karpathy / John Schulman / Dylan Patel / Clem Delangue** — AI 教育 + OpenAI 联创 + SemiAnalysis 创始人 + Hugging Face CEO

这不是一个"明星项目"，是一整支**明星团队在押一条范式路线**。

---

## 三、架构四层——TUI 客户端永远不负责执行

Prime Agent 文档里的架构图把执行边界划得明明白白：

```
Interactive TUI / Headless clients
         ↓ (AgentConnection 客户端边界)
Local daemon protocol (TCP/unix socket)
         ↓
Daemon Supervisor (routing / recovery / catalog)
         ↓
Session Worker (one root session tree)
  ├─ AgentSessionRuntime
  ├─ Root AgentSession
  ├─ Scheduler
  ├─ Root IPython Kernel
  └─ RLM child runtimes (session + optional kernel)
         ↓
Model Providers + JSONL Storage
```

四层分工：

1. **TUI / 客户端** — 只负责渲染、键盘、UI 偏好。**不持有任何执行状态**。关闭 UI = 客户端 detach，不影响 worker。
2. **Supervisor（守护）** — 持有发现、路由、attachments、worker 健康、跨 agent 消息路由。常驻进程。
3. **Session Worker** — 一个 root session tree 的 owner。runtime + scheduler + IPython kernel + 全部子会话都在这层。
4. **AgentSession** — 负责 provider 调用、队列、tools、compaction、goals、child lifecycles、transcript 写入。

这是 **"前端 UI 跟执行彻底解耦"** 的实现。比 Claude Code 的"everything in one process"领先一代——客户端崩了、终端断了、网络断了，agent 自己继续。

Worker 和 Kernel 是 **独立进程**——为了 lifecycle 和 failure 隔离，不是安全沙箱。文档原句："they normally run with the same operating-system permissions as the client"。

### 端到端跑一次

```bash
# 1. 安装（macOS / Linux）
curl -fsSL https://app.primeintellect.ai/prime-agent/install.sh | sh

# 2. 在 disposable clone 里启动（推荐）
git worktree add ../prime-agent-test -b test/prime-agent
cd ../prime-agent-test
prime-agent

# 3. 首次启动跑 /login 选订阅或 API-key provider
# 4. 跑任务：直接输入 prompt
# 5. 想看后台服务
prime-agent status
prime-agent doctor [--fix]
prime-agent shutdown
```

---

## 四、RLM 编程模型——把 Python REPL 当 Agent 的控制平面

Prime Agent 的核心是 RLM 范式。

RLM（Recursive Language Models）是 Prime Intellect 团队 2025-10 在博客首次提出，2026-01 升级为正式论文。核心定义：

> **让 LLM 在一个持久的 Python REPL 里检查和转换它的输入数据，并在 REPL 里调用 sub-LLM。**

README 原句：

> "The Recursive Language Model (RLM) treats context as variables (prompt-as-a-variable) and tools like recursive subagents as function calls (programmatic tool / sub-agent calling) inside a persistent REPL."

翻译成工程师语言：

1. **Context 不进 prompt 字符串**——它进 Python 变量。
2. **Tools 不在系统 prompt 里声明**——它们是 REPL 里的 Python 函数。
3. **Subagent 不是 JSON-RPC 调用**——它是 `await rlm(...)` 函数调用。
4. **持久状态**——同一个 IPython kernel 跨多个对话回合保留 Python 变量、import、parsed results。

实际效果示例：

```python
from pathlib import Path

config_files = list(Path(".").rglob("*.toml"))
large_files = [path for path in config_files if path.stat().st_size > 10_000]
```

```bash
%%bash
npm run check
```

`%%bash` cell 是临时子 shell，Python state 跨 cell 持续。Agent 在跨 100 回合的对话里**仍然能引用上面那个 `large_files` 列表**。

RLM 论文博客对此有个关键判断：

> "We at Prime Intellect believe that the simplest, most flexible method for context folding is the Recursive Language Model (RLM)... it enables training directly with the RLM scaffolding and getting better and better, learned context folding; and **it never actually summarizes context, which leads to information loss**. Instead, it pro-actively delegates context to Python scripts and sub-LLMs."

**RLM 不摘要 context**——这是它和 Claude Code / Codex 完全不同的设计：

| 范式 | 代表 | 怎么处理长 context |
|---|---|---|
| 外部文件 + LLM 摘要 | Claude Code / Codex | 定期总结进文件，靠文件状态连接 |
| Context Folding | AgentFold / Scaling Long-Horizon | 把 context 当 active 对象管理（带 summary） |
| **RLM** | **Prime Agent** | **直接让模型在 REPL 里程序化处理 context，不摘要** |

第三条比前两条激进——**它假设模型能学会自己管 context**，这条假设会通过 RL 训练被进一步强化。Prime Intellect 不只是用 RLM，是在用 RL 训练 RLM。

---

## 五、子代理——`rlm(...)` 函数化

传统 Agent 框架的子代理都是 JSON-RPC 风格：

```json
{
  "tool": "spawn_subagent",
  "args": {"task": "...", "context": "..."}
}
```

Prime Agent 把子代理变成 Python 函数：

```python
handle = await rlm("Review the authentication flow for security issues", name="auth-reviewer")
print(handle.rlm_child_id, handle.name, handle.session_dir, handle.model)
```

关键设计：

- **`rlm()` 立刻返回 admission handle**——不等待子 agent 完成。调用方拿到 handle 后可以继续做别的事。
- **结果回来靠 `agent_message`**——子 agent 主动发消息给 parent，不是返回值。
- **并行 spawn 多 agent**：

```python
api_review = await rlm("Review the public API", name="api-reviewer")
test_review = await rlm("Review the test coverage", name="test-reviewer")
integration_audit = await rlm("Run the slow integration audit", name="integration-audit")
```

三个子 agent 同时跑，结果**通过 agent_message 异步回传**。

- **子 agent 跨 compaction/kernel restart/parent restoration 仍然 addressable**——子注册表持久化。

```python
children = await rlm.list_subagents()
for child in children:
    print(child.session_name, child.status, child.active_session_id)
```

这是把"Agent 当协程"的设计哲学。Python asyncio 程序员看到这 API 会很熟悉——`await rlm(...)` 就像 `await fetch(...)`，整个 Agent 系统是一个 async 程序。

子 agent 还支持递归（root → child → grandchild），文档原句："the default recursion depth allows a root agent to create children. Raising the configured depth allows descendants to recurse further."——这是一个**可调节的递归深度限制**，模型如果失控想死循环 spawn 子 agent，深度限制兜底。

---

## 六、Continual Harness——让 Agent 自己改自己的 lesson

Prime Agent 的第二条灵魂设计是 **Continual Harness**。

README 原句：

> "The Continual Harness stores supplemental prompts, memories, skill descriptions, and reusable subagent specifications as durable state that Prime Agent can refine through small, evidence-backed updates, local to the session by default."

四个可持久化的状态：

1. **Supplemental prompts** — 补充指令
2. **Memories** — 跨对话的关键事实
3. **Skill descriptions** — 可重用 skill 的描述
4. **Reusable subagent specifications** — 可重用子 agent 模板

`/refine` 命令让 agent **基于当前 trajectory** 提出小颗粒、证据支撑的更新。文档关键承诺：

> "`/refine` reviews the current trajectory and can apply small, evidence-backed updates to supplemental harness state. It **never rewrites the immutable base system prompt**, and recorded snapshots support rollback."

三个限制：

- 只能改 supplemental（不可改 base prompt）——base 是不可变锚点
- 只能小颗粒、有证据的更新——不允许大重构
- 所有快照可回滚——任何 refine 都能撤销

这是把"Agent 自我改进"做成 **有安全网的工程实现**。

论文里把这条路线叫 **Agentic Context Engineering**：

> "Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models: a three-agent system with a Generator that uses the current knowledge base for creating the rollout, a Reflector which takes lessons and information about the generation and about the current state of the knowledge base, and a Curator for taking the Reflector's lessons and adapting the knowledge base with them in a structured manner."

Generator + Reflector + Curator 三 agent 协作。Prime Agent 的 `/refine` 是这条学术路线的产品级落地。

---

## 七、长期运行——daemon + heartbeat + goal + autonomous

Prime Agent 的第三条故事线是 **long-running**。`long-running-agents.md` 文档详细描述了 5 个机制。

### 7.1 Daemon-backed 会话

关掉 TUI = 客户端 detach，**worker 继续持有 root session + IPython kernel + schedules + RLM 子会话**。重启 supervisor 后可以从 JSONL transcript 恢复 session。

CLI 治理命令：

```bash
prime-agent list                 # 列出所有 running/idle/saved 会话
prime-agent attach <agent>       # 重新挂载 running 会话
prime-agent --resume <path|id>   # 恢复 saved 会话
prime-agent status               # 看后台服务状态
prime-agent doctor [--fix]       # 诊断/修复后台服务
prime-agent shutdown [--force]   # 关掉所有 agent + worker + 后台服务
```

### 7.2 心跳 + 调度

三种调度面：

| 表面 | 拥有者 | 用途 |
|---|---|---|
| `/heartbeat` | 用户 | 当前会话的单个可见 recurring instruction |
| `rlm_heartbeat` | Agent | 多个 program-manage 内部 recurring instructions |
| `prime-agent schedule` | 用户或自动化 | 通用 cron / 一次性 prompt |

Agent 自己创建多个内部 heartbeat：

```python
first = await rlm_heartbeat.create(
    "check whether the test run finished",
    interval="5m",
    label="tests",
)
```

### 7.3 持久目标

```text
/goal Ship the release and verify every published artifact
/goal --budget 200000 Complete the repository migration
/goal status
/goal pause
/goal resume
/goal clear
```

Goal 是 **跨 turn 持续呈现的目标**——agent 在普通回合后会被 harness 重新提示这个 goal，直到 `goal.complete()` 才算成功。文档原句：

> "Creating a persistent goal is an explicit user or host action, **not something the agent should infer from every task**."

Agent 不会自动创建 goal，避免"AI 决定人类应该有什么目标"的失控。

### 7.4 自治模式

`/autonomous` 在配置的 turn / token / time budget 内继续，**支持 user-defined quality gates**：

> "A passed gate checks only what that gate verifies; reaching a limit does not imply task success."

Gate 通过 ≠ 任务成功。文档这句戳破了一个假象——很多产品把"token 跑完了"当"任务完成"卖，Prime Agent 不这么做。

### 7.5 Agent-to-agent 直接通信

```bash
prime-agent send <agent> "Please verify the latest migration"
```

```python
receipt = await agent_message.send(
    "Recheck the endpoint after the latest edit",
    receiver_role="sibling",
    receiver_name="api-reviewer",
    mode="auto",
)
print(receipt["deliveryStatus"])
```

三种投递模式：

- `auto` — target 忙就 steer，空闲就立即投递
- `steer` — 显式注入当前工作
- `follow_up` — 等 target 当前工作完成再投递

Receipt 是 `delivered` / `queued` 之一——区分"已经到达 context"和"排队等投递"两种状态。

`agent_message.send("all", message)` 广播只限 family roster——避免全员广播风暴。

---

## 八、安全边界——不是 sandbox 而是 process isolation

README 大字警告：

> "Prime Agent executes model-generated Python and project commands with your user permissions. Its worker and kernel processes improve lifecycle isolation and recovery; they are **not** a security sandbox. Review changes and use trusted repositories, instructions, skills, and extensions only. Run untrusted code or instructions in an external sandbox or restricted environment."

边界声明分两层：

- ✅ **进程隔离**——worker 和 kernel 各自独立进程，崩溃不影响其他
- ✅ **跨 turn 持久状态**——kernel 状态和变量保留
- ❌ **不是 sandbox**——和 TUI 客户端用同一套 OS 权限
- ❌ **不隔离文件系统**——可以读写 ~/.ssh、~/.aws 等敏感目录

跑 untrusted 代码必须套外部 sandbox（Docker、gVisor、Firecracker）。Prime Agent 把这责任明确抛给用户，文档原句（`rlm.md`）：

> "The IPython kernel runs model-generated Python and project commands with the worker's operating-system permissions. It is a durable control environment, not a security sandbox."

**这是 Prime Agent 团队最诚实的地方——他们不假装 sandboxing 解决了**。

---

## 九、协议设计取舍——RLM vs compaction vs file-state

读 RLM 论文 + Prime Agent 架构文档，最让我停下来思考的是：为什么他们坚持 **不摘要 context**？

### 9.1 三种长 context 处理范式

| 范式 | 代表项目 | 核心做法 | 优点 | 缺点 |
|---|---|---|---|---|
| **外部文件 + LLM 摘要** | Claude Code, Codex | 定期 summarize 进文件，靠文件 state 连接 | 兼容任何模型 | 摘要丢失信息 |
| **Context Folding** | AgentFold, Scaling Long-Horizon | 模型主动 fold/unfold context window | 保留"长 session" | 仍是 summary-style |
| **RLM** | **Prime Agent** | 模型在 REPL 里程序化处理 context，**不摘要** | 信息零丢失 | 要求模型能学会 |

### 9.2 Prime Agent 的论文立场

> "We at Prime Intellect believe that the simplest, most flexible method for context folding is the Recursive Language Model (RLM)... it enables training directly with the RLM scaffolding and getting better and better, learned context folding; and it never actually summarizes context, which leads to information loss."

三个核心论点：

1. **"Never actually summarizes"** — 信息零损失
2. **"training directly with the RLM scaffolding"** — 可以 RL 训练模型学会更好管理 context
3. **"The Bitter Lesson"** — 通用方法 + 大量算力 > 手工设计

第三条呼应 Sutton 的 Bitter Lesson。RLM 不是为某个模型设计的——它是为**未来所有模型**设计的，因为它假设模型会越来越好地使用 REPL。

### 9.3 工程取舍

代价：

- **不是所有模型都擅长用 REPL**——小模型（如 7B）调用 REPL 经常出错
- **Python skill 包管理**——第三方 skill 要 `pip install` 进 kernel 环境，依赖冲突是真实风险
- **持久 kernel 的内存开销**——长 session 累积变量、import、缓存，可能 OOM

论文里承认："It is still an experimental work-in-progress, but we have already added our own flavor to it."

Prime Intellect 知道 RLM 是**实验性范式**——他们押的是这条路线本身。

---

## 十、版本节奏——3 天一版的迭代速度

Prime Agent 92 天发布了 13+ 个版本（v0.1.0 到 v0.7.0）。从 v0.3.1（7-15）到 v0.7.0（8-05）短短 21 天发 9 个版本。

支撑这种节奏的是：

- **AGENTS.md**（12724 字节）—— 详细工程准则，AI 和人协作者都遵守
- **`install.sh`**（45280 字节）—— 一键安装 + SHA-256 校验
- **`docs/architecture.md` / `rlm.md` / `long-running-agents.md`** —— 三个核心文档结构清晰
- **CI workflow** + **build-binaries workflow** —— GitHub Actions 自动构建 + 发布

Prime Agent 的工程深度不在 star 数，在 **文档当规约用**。

---

## 十一、它没做对的事

5.2k stars 不等于完美。读完材料后看到四个明显不足：

1. **Windows 不支持**——README 只说 "macOS or Linux"。Windows 用户被挡在外。
2. **IPython 当 control environment**——意味着 prime agent 实际是 Python-centric 工具，**TypeScript / Go / Rust 项目跑起来体验不完整**（bash cell + shell 是补充但不是核心）。
3. **Sandbox 不完整**——worker 和 kernel 不隔离 OS 权限，跑 untrusted 代码必须套外部 sandbox。设计选择不是 bug，但对终端用户而言是个摩擦点。
4. **Open issues 213**——社区活跃但维护压力也大。

合在一起意味着：**它适合"信任的工作流"，不适合"高风险任务自动化"**。

---

## 十二、把它放在更大的地图里

读完 Prime Agent，我想到四个相邻项目：

- **Claude Code**（Anthropic）—— 商用闭源，最成熟的商业 AI Agent，但不做 self-improving harness。
- **Codex CLI**（OpenAI）—— 商用闭源，云端为主，跟 Claude Code 直接竞争。
- **Cursor Background Agent**（Anysphere）—— SaaS，GitHub PR 模式，跟 Prime Agent 的 worktree 模式有共鸣。
- **pi-mono**（`badlogic/pi-mono`，`earendil-works/pi`）—— Prime Agent 底座，**最小化 TUI Agent 框架**。

放在 2026 年 AI Agent 赛道：

| 维度 | Claude Code | Codex CLI | Cursor BG Agent | **Prime Agent** |
|---|---|---|---|---|
| 编程模型 | Function calling + tools | Function calling + tools | Cloud VM + sandbox | **RLM / 持久 REPL** |
| Self-improving | ❌ | ❌ | ❌ | **✅ `/refine`** |
| Long-running | ❌ | ❌ | ❌ | **✅ daemon** |
| Agent-to-agent | ❌ | ❌ | ❌ | **✅ `agent_message`** |
| 子代理 | tool call | tool call | 多 PR | **`rlm(...)`** |
| 开源 | ❌ | ❌ | ❌ | **✅ MIT** |

Prime Agent 在 5 个维度同时领先。这是它 92 天 5.2k stars 的真正原因——**不是做得最好，是**做别人没做**的**。

---

## 十三、FAQ——读者大概率会问的几个问题

**Q1: Prime Agent 跟 Claude Code 最大的区别是什么？**

A: 三件事：（1）编程模型——Claude Code 是 JSON-RPC + tools，Prime Agent 是持久 IPython + `await rlm(...)`；（2）自改进——Claude Code 没有 `/refine`，Prime Agent 有；（3）长期运行——Claude Code 跟终端绑定，Prime Agent 关闭 UI 不杀 worker。

**Q2: 我跑 Prime Agent 会不会把 ~/.ssh 删了？**

A: 会，因为它没有 sandbox。所有 Python 和 shell 命令都以你的 OS 权限跑。**只在 disposable clone / worktree / 外部 sandbox 里跑**。

**Q3: 一定要用 Prime Intellect 自己的模型吗？**

A: 不一定。Prime Agent 通过 provider 抽象接 OpenAI / Anthropic / Google / OpenRouter 等多家模型（`docs/providers.md`）。但 Prime Intellect 的 RLM 训练主要针对自家 INTELLECT 系列——RLM 范式需要模型能学会用 REPL，小模型可能掉链。

**Q4: 一定要 macOS / Linux 吗？**

A: 是。Windows 不在支持范围（README 明确）。如果你在 Windows 上需要类似工具，可以试 Cursor Background Agent 或 Cloud-based Codex。

**Q5: 我能用 Prime Agent 跑 long-running 的 RL 训练吗？**

A: 不能直接跑——Prime Agent 是 Agent 编程模型，RL 训练请用 `PrimeIntellect-ai/prime-rl`。但 Prime Agent 是用 Prime-RL 训练的产物之一。

**Q6: 5.2k stars 是真人气还是营销？**

A: 真人气。证据：92 天 416 forks（fork 率 8%——AI Agent 赛道里偏高）、213 open issues（社区真在用）、13+ 版本（项目真在迭代）、Karpathy 站台（业界背书）。它的 star 数跟它做的事匹配。

---

## 写在最后

Prime Agent 让我重新思考了一件事：**Agent 编程模型**到底应该长什么样。

过去 3 年，Agent 框架默认是"function calling + tools"——模型选 tool、tool 跑完结果回 context。这个范式简单、兼容性好，但**模型被工具列表淹没、context 被工具结果淹没**。

RLM 范式（持久 Python REPL + 函数化子代理 + self-improving harness）给了另一种可能——**Agent 不是一个调用 JSON-RPC 的客户端，是一个跑在 Python REPL 里的程序**。

Karpathy 站台 Prime Agent 不是偶然——**他看到的是 Bitter Lesson 在 Agent 时代的具体实现**。

---

**仓库**：[PrimeIntellect-ai/prime-agent](https://github.com/PrimeIntellect-ai/prime-agent) · 5.2k stars · MIT
**官网**：[primeintellect.ai](https://primeintellect.ai)
**RLM 论文博客**：[primeintellect.ai/blog/rlm](https://www.primeintellect.ai/blog/rlm)
**架构文档**：[docs/architecture.md](https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/docs/architecture.md)
**关联仓库**：[verifiers](https://github.com/PrimeIntellect-ai/verifiers) · [prime-rl](https://github.com/PrimeIntellect-ai/prime-rl) · [pi-mono](https://github.com/badlogic/pi-mono)
**团队站台**：Andrej Karpathy · John Schulman · Dylan Patel · Clem Delangue · Founders Fund · NVIDIA