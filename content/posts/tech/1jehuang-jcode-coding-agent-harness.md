---
title: "jcode：把内存压到 27.8 MB 的 Coding Agent Harness 怎么做到"
date: 2026-07-20T03:02:36+08:00
categories: ["技术笔记"]
tags: ["Coding Agent", "Rust", "TUI", "MCP"]
description: "jcode 是一个用 Rust 写的 next-generation coding agent harness，单 session 仅占 27.8 MB PSS，比 Claude Code 低 13.9 倍。它专为多 session 工作流设计，把启动速度和内存控制在毫秒/百兆级。"
slug: 1jehuang-jcode-coding-agent-harness
github_repo: "1jehuang/jcode"

---

# jcode：把内存压到 27.8 MB 的 Coding Agent Harness 怎么做到

## 一句话判断

jcode 是 1jehuang 在 2026 年交出的 Rust 系 coding agent harness，单 session PSS（按比例的内存占用）低至 **27.8 MB**（关掉本地 embedding 后），是 Claude Code 386.6 MB 的约 1/14，OpenCode 371.5 MB 的约 1/13。在多 session 并行的场景里，省下的内存就是能同时开的 agent 数。

## 项目定位

- **仓库**：`1jehuang/jcode`，MIT 协议，Rust 实现
- **平台**：Linux / macOS / Windows 三平台原生支持
- **核心特性**：multi-session workflows、performance-first、infinite customizability

官网 [jcode.sh](https://jcode.sh) 把安装命令压成一行 `curl | bash`，落地门槛和 Claude Code / Codex CLI 一样低；但它多了一组围绕"资源开销"做的工程权衡。

## 系统地图

按 README 的叙述层次还原，jcode 由四块组成：

| 模块 | 责任 | 关键事实 |
|------|------|----------|
| Harness runtime | 启动 session、解析 CLI、加载 provider、调度 agent 循环 | PSS 27.8 MB / 单 session |
| Memory subsystem | 跨 session 的语义记忆，把对话变成可检索的图 | 每轮嵌入为向量，余弦相似度检索命中后才注入上下文 |
| Provider / MCP 适配层 | 接入 Claude / OpenAI / Gemini 等 LLM 与外部 MCP 工具 | 内置多家 OAuth 登录，复用 MCP 协议 |
| TUI 界面 | 终端交互、侧边栏、内联渲染 | 侧边栏可当 diff 查看器，mermaid 图内联渲染 |

把模块按资源视角排序，关键问题就是"哪一块在吃 RAM"。README 的对比表给出了答案：单 session 时，绝大部分 RAM 不是模型本身（模型在云端），而是 harness 的本地状态。其中最大的变量是本地 embedding——关掉它，PSS 从 167.1 MB 直接降到 27.8 MB，差出 6 倍。jcode 把本地 embedding 做成可关闭的开关，不做默认依赖。

## 性能对比的关键数字

README 的对比表直接反映了内存开销的差异：

- **1 active session**：
  - jcode（关本地 embedding）：**27.8 MB**
  - jcode（默认）：167.1 MB（6.0× baseline）
  - pi：144.4 MB（5.2×）
  - Codex CLI：140.0 MB（5.0×）
  - OpenCode：371.5 MB（13.4×）
  - GitHub Copilot CLI：333.3 MB（12.0×）
  - Cursor Agent：214.9 MB（7.7×）
  - **Claude Code：386.6 MB（13.9×）**
  - Antigravity CLI：243.7 MB（8.8×）
- **10 active sessions**：
  - jcode（关 embedding）：**117.0 MB**（baseline）→ 带 embedding 260.8 MB
  - Codex CLI：334.8 MB / pi：833.0 MB / Antigravity CLI：1.0 GB
  - Cursor Agent：1.6 GB / GitHub Copilot CLI：1.7 GB
  - **Claude Code：2.3 GB** / **OpenCode：3.2 GB**

README 还测了"启动到首帧"的耗时：jcode 14.0 ms，Claude Code 3.4 s（约 245 倍）。

**jcode 的内存曲线接近 O(session 数 × 常数)，而同类工具接近线性甚至超线性增长**。README 的单 session 增量数据说得很清楚：jcode 每加一个 session 约 9.9 MB，OpenCode 约 318 MB，Claude Code 约 213 MB。对同时跑 5-10 个 agent session 的开发者，这是决定性优势。

这组数字来自 README 作者在同一台 Linux 机器上、各工具固定版本下的实测（10 次交互式 PTY 启动），衡量的是空闲 session 的静态 PSS，不是任务进行中的峰值占用。换系统、换配置、换工作负载，数值都会变。它只能说明"开 N 个闲置 session 谁更省内存"这一个维度，不能推出 jcode 在真实任务里更快，也不能推出它在任何机器上都能复制同样的差距。

## 安装与快速开始

jcode 把安装压成两行：

```bash
# macOS / Linux
curl -fsSL https://jcode.sh/install | bash

# Windows 11 PowerShell 5.1+
irm https://jcode.sh/install.ps1 | iex
```

它支持 Homebrew、源码构建、provider 预设等多种入口，README 把"让一个 agent 帮你装好"也作为合法路径。Windows 的安装脚本走 PowerShell，覆盖了 WSL / Windows Terminal 全场景。

## 关键机制拆解

### 1. 为什么是 Rust

Coding agent 的 runtime 分为两类：

- **Node / TS 系**（OpenCode、Claude Code、Cursor Agent）：开发快、依赖成熟，但内存开销天然大（V8 baseline + 大量 transitive deps）。
- **Rust 系**（jcode）：启动到首帧约 14 ms、PSS 接近 native binary、不需要 JIT 预热。

jcode 选 Rust 的原因是：多 session 的瓶颈是**内存**而不是吞吐。10 session 并行时，3 GB 内存和 260 MB 内存的差别就是"你能不能同时跑 3 个项目和 1 个项目的差别"。

### 2. 记忆系统：把对话变成可检索的图

jcode 的记忆不是把对话原样囤起来。每轮回复会被嵌入成向量，存进一张记忆图；新一轮对话进来时做一次余弦相似度查询，命中后再喂回上下文。为了让检索更稳，它还配了一个记忆侧 Agent：先校验命中的记忆是否真的相关，必要时再做一轮信息提取，才注入对话。记忆的沉淀是后台进行的——检测到语义漂移、隔了若干轮、或 session 结束时，侧 Agent 抽取新记忆并合并进图；还有 ambient 模式定期整理图，清理过期和互相冲突的条目。另外它保留了显式的记忆工具和跨 session 的 RAG 搜索，Agent 可以主动查，不依赖后台被动索引。

关掉本地 embedding 后，这个记忆图就不加载，这是 PSS 从 167.1 MB 掉到 27.8 MB 的主因。能关掉，说明记忆不是单点依赖——你要的是省内存还是跨 session 记忆，可以自己权衡。

### 3. MCP 兼容性

jcode 走标准 MCP 协议，这意味着它可以直接复用社区里所有的 MCP server——浏览器自动化（chrome-devtools-mcp）、文档检索（context7）、任务管理（linear / github）。这一点和 Claude Code / Codex CLI / Gemini CLI 没有差别，但 jcode 多了"在多 session 下仍然能跑"的稳定性优势。

### 4. 多 session 不是多开终端：一个 server 管一群人

jcode 的规模优势不只在 malloc 上。它有独立的 server 进程做中枢，管理所有活跃 session——消息路由、session 生命周期、文件变更通知都是它负责。于是"几个 agent 同时改一个仓库"不是各改各的：A 会话改了文件，B 会话能收到变更通知；多个 agent 在同一代码库里协作、交换消息、合并冲突，用的是共享的那一张记忆图和状态。对多智能体（swarm）协作来说，这解决的已经不是"内存够不够"，而是"会不会互相踩脚"。

### 5. 自举：agent 改它自己的 harness

jcode 的 self-dev 模式允许 agent 直接修改项目源码。作者本人拿它来加构建内存预算、修 CI 护栏这类自身维护，等于把 release 工程交给 agent 去跑。对普通用户，它更像一道上限证明——不是"能不能这么做"，而是作者已经把这条路完整走通了一遍。

## 一次任务流案例

假设你同时在三个仓库上工作：一个 Rust 后端、一个 React 前端、一个 Python 数据处理脚本。用 jcode 开三个 session，每个 session 挂不同的 provider（Claude、GPT、Gemini），各自跑 MCP server（git、linter、test runner）。

同等条件下，Claude Code 跑三个 session 大约 812 MB（第一个 386.6 MB，每加一个约 213 MB），16 GB 笔记本还能扛，但已经能感觉到占用。jcode 三个 session 约 48 MB（关 embedding，每加一个约 9.9 MB）或 188 MB（开 embedding）——差距是十几倍。扩到 10 个 session，差别从"有点紧"变成"能不能跑"：Claude Code 涨到 2.3 GB，OpenCode 直接 3.2 GB，jcode 关 embedding 总共才 117 MB。后者意味着你可以在同一台笔记本上同时维护 10 个 agent 工作流，前者已经让机器开始卡顿。

这个案例揭示 jcode 的核心设计取舍：它牺牲了"单 session 的功能丰富度"（默认不带 embedding、不做 IDE 集成），换取了"多 session 并行时内存不爆炸"。

## 适用人群

- **多任务并行开发者**：需要同时跑 3+ 个 session（不同 repo、不同任务）
- **资源敏感用户**：MacBook Air 8GB、Linux 笔记本 16GB、容器里跑 agent 的 CI 环境
- **追求冷启动速度的人**：jcode 启动到首帧约 14 ms，可以把它当成 shell 工具嵌进 zsh / nushell
- **不愿意被 vendor lock-in 的人**：jcode 把 provider 抽象做成可插拔，可以同时用 Claude / GPT / Gemini

## 不适合谁

- **只要"一个能用的 CLI"的人**：Claude Code / Codex CLI 仍然是更主流的选择，文档、插件、prompt 工程生态都更厚
- **重度依赖 GUI / IDE 集成的人**：jcode 是纯 TUI，不做 VS Code / JetBrains 插件
- **愿意为 RAM 换更丰富原生功能的人**：jcode 的"无限 customizability"来自你愿意写配置；如果只是想"开箱即用"，反而更累

## 常见疑问

**这些内存数字是它自己测的吧？能信多少？** 数字来自 README 作者在同一台 Linux 上、固定版本、10 次交互式 PTY 启动的实测，衡量的是空闲 session 的静态 PSS。同一个逻辑在不同系统、配置和负载下会变，它只回答"开 N 个闲置 session 谁省内存"这一个问题。真要到买不买的程度，最好在你自己的机器和任务上再量一次。

**关掉 embedding 记忆功能还在吗？** 还在，只是从"自动后台索引"降级。显式的记忆工具和跨 session 的 RAG 搜索仍然可用，agent 可以主动去查；少的只是每轮对话的自动嵌入。要省内存还是保留记忆，是文档里明确留给你权衡的开关，不是砍功能。

**它是 Claude Code 的替代品吗？** 不完全是。它连模型时仍可接 Claude / OpenAI / Gemini，替代的是承载模型的运行时。如果你主要是单 session、重度依赖 IDE 集成或开箱即用的生态，Claude Code / Codex CLI 那一套更省心；它的优势只在"多 session 并行 + 资源敏感"这条赛道上特别明显。

**GitHub 上 star 涨得这么快，会不会是刷的？** 仓库 7100+ 次提交、持续到本月的 commit 记录都在，和 star 数量对得上活跃度。但 star 不等于你能直接用的稳定性，用之前的预期应当是"一个正在极速演进的项目"，配置和工作流可能随版本变化。

## 仓库地址

https://github.com/1jehuang/jcode

## 采用建议

**谁该先用**：多任务并行开发者（3+ session）、资源敏感用户（8-16 GB 内存设备）、CI 环境下跑 agent 的团队。如果每天只开 1 个 session，jcode 的优势不大，Claude Code 或 Codex CLI 的生态更成熟。

**谁可以等等**：重度依赖 IDE 集成的人、开箱即用型用户、单 session 工作流占主导的开发者。

**从哪里开始**：
1. 先看 README 的 Performance 表，确认你的使用场景是否值得为内存买单
2. 跑 `curl -fsSL https://jcode.sh/install | bash`，5 分钟内完成 first run
3. 试 `jcode memory` 子命令，理解它的跨 session 记忆是怎么落地的
4. 在 3 个不同 session 里跑同一个任务，观察 PSS 是否真的不随 session 数线性增长