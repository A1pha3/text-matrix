---
title: "Claw Code：一个由 AI 打理门面的 Rust CLI Harness"
date: "2026-04-30T20:00:00+08:00"
slug: "claw-code-rust-ai-agent-cli"
github_repo: "ultraworkers/claw-code"
source_key: "gh:ultraworkers/claw-code"
description: "Claw Code（ultraworkers/claw-code）是 claw CLI agent harness 的公开 Rust 实现。项目自述是「博物馆展品」：代码由 AI Agent 打理，定位偏研究而非日常工具。本文讲清它的真实架构、能跑的 CLI、多模型接入方式，以及为什么生产环境应转向 LazyCodex 或 Gajae-Code。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Rust", "CLI工具"]
---

## 快速信息卡

| 属性 | 值 |
|------|-----|
| GitHub Stars | 约 19 万（持续变化） |
| 主要语言 | Rust（`rust/` 规范工作区，约 2 万行，9 个 crate） |
| 开源协议 | MIT |
| 维护方式 | 由 AI Agent 自动打理（agent-managed） |
| 项目定位 | 博物馆展品 / 研究性 artifacts |
| 默认模型 | `claude-opus-4-7` |
| 默认权限 | `workspace-write` |

> ⚠️ **先说清楚**：这不是拿来当日常开发工具的项目。README 第一屏就写着「museum exhibit / 博物馆展品」，并明确建议要干活就去找 LazyCodex 或 Gajae-Code。想用稳定的 AI 编码 CLI，请从那两个仓库开始。

---

## 目录

- [它到底是什么](#它到底是什么)
- [为什么不建议当生产工具](#为什么不建议当生产工具)
- [快速开始：从源码构建](#快速开始从源码构建)
- [真实架构：9 个 crate 的 Rust 工作区](#真实架构9-个-crate-的-rust-工作区)
- [模型接入：不止 Claude](#模型接入不止-claude)
- [CLI 与交互层](#cli-与交互层)
- [权限系统](#权限系统)
- [与 Anthropic Claude Code 的区别](#与-anthropic-claude-code-的区别)
- [能力边界](#能力边界)
- [常见问题](#常见问题)
- [自测题](#自测题)

---

## 它到底是什么

Claw Code 是 **`claw` 这个 CLI agent harness 的公开 Rust 实现**，规范代码在仓库的 `rust/` 目录，仓库本身（`ultraworkers/claw-code`）是当前的事实标准源。

它做的事和 Claude Code 一样：你在终端里给它指令，它自己读写文件、跑命令、调 LLM，把多轮工具调用串起来完成一个任务。区别在于——

- **它不是 Anthropic 的东西**。仓库明确声明不主张对原始 Claude Code 源码的所有权，也与 Anthropic 无任何关联。
- **它是「干净室重写」的产物**。社区报道的背景是：2026 年初 Claude Code 的 TypeScript 源码被意外公开，引发了大量基于公开文档和行为独立重写的开源项目，Claw Code 是其中 Star 增长最快的一个（一度被称"史上最快破十万 Star"）。

对多数人来说，只要记住一点就够：**这个仓库是被人当"展品"打理的研究项目，不是给你日常搬砖用的工具。**

---

## 为什么不建议当生产工具

README 的原话大致是：这个仓库离产品更像一件展品，代码由 agent 自动清扫、贴标签、归档，背后有一批 gajae（桃树下的螃蟹）在维持运作。

翻译成风险清单：

1. **没有人工兜底**。功能、文档、测试都可能是 AI 生成的，出问题不及时修。
2. **文档会漂移**。你可能看到文档写的和实际行为对不上，遇到矛盾以代码和 `--help` 输出为准。
3. **界面在快速变动**。CLI 命令和 slash 命令一直在加，教程跟不上也正常。

作者本人的态度很直接：要真跑活，去 [LazyCodex](https://github.com/code-yeongyu/lazycodex) 或 [Gajae-Code](https://github.com/Yeachan-Heo/gajae-code)。想观察 Claw Code 这个"历史瞬间"，可以继续往下读。

---

## 快速开始：从源码构建

> ⚠️ **不要 `cargo install claw-code`**。crates.io 上的 `claw-code` 是个废弃的占位包，装出来是 `claw-code-deprecated.exe`，运行只打印一句 `"claw-code has been renamed to agent-code"`，根本不是 `claw`。要么从源码构建，要么 `cargo install agent-code`（注意：装出来的是 `agent` / `agent.exe`，不是 `agent-code`）。

Claw Code 只支持从源码构建：

```bash
# 1. 克隆并构建（debug 模式即可）
git clone https://github.com/ultraworkers/claw-code
cd claw-code/rust
cargo build --workspace

# 2. 设置 API Key（用 Anthropic API Key，不是 Claude 网页版登录）
export ANTHROPIC_API_KEY="sk-ant-..."

# 3. 先做健康检查：校验 API Key、模型权限和工具配置
./target/debug/claw doctor

# 4. 跑一次 prompt
./target/debug/claw prompt "say hello"

# 5. 或进入交互式 REPL
./target/debug/claw
```

二进制位置：

- **Debug（默认）**：`rust/target/debug/claw`（Windows 是 `rust\target\debug\claw.exe`）
- **Release**：`cargo build --workspace --release` 后是 `rust/target/release/claw`；编译会慢不少（5–10 分钟）

Windows（PowerShell）里命令名是 `claw.exe`，路径分隔符是 `\`：

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
.\target\debug\claw.exe prompt "say hello"
```

`claw doctor` 是安装后的第一道检查：它会验证 API Key、模型可访问性和工具配置，比起自己慢慢试错省事得多。

---

## 真实架构：9 个 crate 的 Rust 工作区

`rust/` 是一个约 2 万行、9 个 crate 的 Cargo 工作区。核心分工如下：

```
rust/
├── Cargo.toml
└── crates/
    ├── api/               # Provider 客户端、SSE 流式、认证、请求预检
    ├── commands/          # slash 命令注册表 + help 渲染
    ├── compat-harness/    # 与上游对照的兼容性/一致性工具
    ├── mock-anthropic-service/ # 本地确定性的 /v1/messages 假服务（测试用）
    ├── plugins/           # 插件元数据、安装/启用/禁用
    ├── runtime/           # 会话、配置、权限、MCP、系统提示词、运行循环
    ├── rusty-claude-cli/  # 主二进制 `claw`
    ├── telemetry/         # 会话追踪与用量统计
    └── tools/             # 内置工具：Bash/Read/Write/Edit/Grep/Glob/WebSearch 等
```

理解它并不需要逐 crate 读。一条主路径：`rusty-claude-cli` 收命令 → `runtime` 管会话与权限 → `api` 调模型（SSE 流式返回 token）→ `tools` 执行工具调用并回填到对话。

一个很实用的设计是 **mock-anthropic-service**：一个本地假接口，不联网也能跑一遍端到端 parity 测试，用来验证"给模型的请求长什么样、工具回包怎么拼"。想自己搭本地 harness 的人可以直接抄这套。

仓库根目录另外有配套的 Python `src/` + `tests/` 参考工作区，但那是辅助审计用的，**主运行时在 Rust 这一侧**。

---

## 模型接入：不止 Claude

仓库里有一句常被人漏掉的话：**Claw 不是一个 Claude 专属产品**。它原生支持 Anthropic，也可以通过 OpenAI 兼容协议接不少模型。

认证方式有几种：

- `ANTHROPIC_API_KEY`——Anthropic API Key
- `ANTHROPIC_AUTH_TOKEN`——OAuth / 代理的 bearer token
- `ANTHROPIC_BASE_URL`——指向代理或本地服务
- `OPENAI_API_KEY` / `OPENAI_BASE_URL`——OpenAI 兼容端点

想接本地 OpenAI 兼容服务（Ollama、llama.cpp、vLLM、Apple Silicon 上的 mlx-lm），最省事的做法是设置 `OLLAMA_HOST`，Claw 会自动把所有请求路由到本地端点，且不需要 API Key：

```bash
ollama pull qwen3:latest
ollama serve

# 另开一个终端
export OLLAMA_HOST="http://127.0.0.1:11434"
./target/debug/claw --model "qwen3:latest" prompt "Reply exactly HELLO_WORLD_123"
```

通用做法是显式指定 `OPENAI_BASE_URL` 指向某个 `/v1` 端点：

```bash
export OPENAI_BASE_URL="http://127.0.0.1:8080/v1"
export OPENAI_API_KEY="local-dev-token"
./target/debug/claw --model "qwen2.5-coder" prompt "解释一下这个函数"
```

几点要注意：

- `--model` 必须填服务端实际暴露的模型名（比如 `qwen3:latest`），填错会先报 `model not found`。
- 含斜杠的模型 ID 建议加 `local/` 前缀路由，例如 `--model "local/Qwen/Qwen2.5-Coder-7B-Instruct"`。
- 走 OpenAI 兼容网关时可用 `openai/` 前缀，如 `--model "openai/gpt-4.1-mini"`。
- 工具调用比纯对话更容易触发兼容性问题。一句 prompt 能通不代表 slash / 工具流程能通——得看服务端是否支持 OpenAI 兼容的 tool-call 格式。

一句话：**它不是"多 Provider trait 统一抹平"，而是靠环境变量做路由**，官方把 OpenAI 兼容这条路明确当作可扩展的接入方式。

---

## CLI 与交互层

`claw` 提供一次性 prompt、交互式 REPL（基于 rustyline）、以及一批直接可用的子命令。

常用命令：

```bash
./target/debug/claw prompt "总结这个仓库"          # 一次性 prompt
./target/debug/claw --model sonnet prompt "..."   # 指定模型
./target/debug/claw --output-format json status   # 机器可读输出
./target/debug/claw doctor                        # 健康检查
./target/debug/claw init                          # 初始化 .claw/ 配置 + CLAUDE.md
```

模型别名：

| 别名 | 解析到 |
|------|--------|
| `opus` | `claude-opus-4-7` |
| `sonnet` | `claude-sonnet-4-6` |
| `haiku` | `claude-haiku-4-5-20251213` |

交互式 REPL 里则是一堆 slash 命令：`/status`、`/cost`、`/compact`（压缩历史）、`/resume`、`/memory`、`/diff`、`/mcp`、`/agents`、`/skills`、`/doctor`、`/plugin`、`/subagent` 等等，tab 可以补全命令、模型别名、权限模式和最近的 session ID。

---

## 权限系统

权限是 `--permission-mode` 一把控制的，运行工具前会拦截为你批准：

- **read-only**：只读，适合审查
- **workspace-write**（默认）：允许改工作区文件
- **danger-full-access**：完全放行，适合受信任的自动化流程

你可以用 `--allowedTools` 收紧允许的工具集（如 `read,glob`），或用 `--dangerously-skip-permissions` 跳过全部拦截（慎用）。看当前工作区的隔离快照，跑 `claw sandbox`。

这套东西对一个"跑你的 shell"的工具是刚需——尤其你连的都是敏感数据时。

---

## 与 Anthropic Claude Code 的区别

**Claw Code ≠ Anthropic Claude Code。** 两者完全独立：

| 维度 | Claw Code | Anthropic Claude Code |
|------|-----------|----------------------|
| 维护方 | UltraWorkers 社区，agent 自动打理 | Anthropic 官方团队 |
| 主语言 | Rust | TypeScript（官方闭源） |
| 开源 | MIT | 部分开源 |
| 定位 | 博物馆展品 / 研究项目 | 生产级 AI 编码助手 |
| 获取 | `git clone` + `cargo build` | `npm i -g @anthropic-ai/claude-code` |

按仓库自己的口径，Claw Code 更像是给 Claude Code 这套交互范式做了一个公开的、可读源码的参考实现；要日常用，还是回到官方或 LazyCodex / Gajae-Code。

---

## 能力边界

**值得学的部分**

- Rust 写 CLI harness 的完整范式：`api` 做流式、`runtime` 做会话与权限、`tools` 做工具注册，层次干净，约 2 万行也容易读。
- mock 服务做端到端测试的思路（`mock-anthropic-service`）。
- 一套不绑定单模型的接入方式（Anthropic + OpenAI 兼容），适合当"搭你自己的 coding agent"的起点。

**不推荐的部分**

- 当日常开发工具。文档会漂移，界面在变，没人负责。
- 期望稳定的 MCP/ACP 支持。MCP 有生命周期与 `/mcp` 检查，但完整协议仍列在路线图里；ACP/Zed 目前只有一个 `claw acp` 探路命令，真协议支持还在路上。
- 依赖某个"精确版本"的 CLI 行为。命令面变化很快，教程里的写法和实际 `--help` 可能不一致。

---

## 常见问题

**Q: `claw doctor` 报 API Key 无效？**

检查三点：环境变量是否真的 export 了（`echo $ANTHROPIC_API_KEY`）；是不是把 Claude 网页版登录会话当成了 API Key；如果走代理，`ANTHROPIC_BASE_URL` 是否对。用手边可用的模型名做一次最小的 `claw doctor`，比拿 curl 手搓快。

**Q: 想用本地模型，最省事怎么配？**

装 Ollama，`export OLLAMA_HOST="http://127.0.0.1:11434"`，然后 `claw --model "<服务端暴露的名字>" prompt ...`。不需要 API Key。

**Q: 会话存在哪？怎么恢复？**

会话默认写在项目内的 `.claw/sessions/`（用户级在 `~/.claw/` 相关目录）。用 `--resume` 或 REPL 里的 `/resume`、`/session` 恢复最近的对话。想在自动化里 readonly 看一眼状态，`claw status --output-format json`。

**Q: Windows 上能不能跑？**

能。装好 Rust，用 PowerShell 构建，命令名是 `claw.exe`；Git Bash / WSL 走 bash 风格路径也可以。

---

## 自测题

1. `cargo install claw-code` 和从源码构建，有什么区别？
2. "museum exhibit / 博物馆展品"这个自述，落到使用者身上意味着哪三类风险？
3. Claw 支持接 Claude 以外模型吗？要接本地 Ollama，最少要设置哪个环境变量？
4. 默认权限模式是什么？想临时只读、或完全放行，各用什么旗标？
5. 你要一个能日常用的 AI 编码 CLI，作者推荐的替代品是哪两个？

---

## 参考链接

- 仓库：https://github.com/ultraworkers/claw-code
- USAGE.md：https://github.com/ultraworkers/claw-code/blob/main/USAGE.md
- rust/README.md（crate 地图与 CLI 面）：https://github.com/ultraworkers/claw-code/blob/main/rust/README.md
- 本地 OpenAI 兼容模型设置：https://github.com/ultraworkers/claw-code/blob/main/docs/local-openai-compatible-providers.md
- LazyCodex（推荐的日常工具）：https://github.com/code-yeongyu/lazycodex
- Gajae-Code（推荐的日常工具）：https://github.com/Yeachan-Heo/gajae-code

---

*本文依据 ultraworkers/claw-code 仓库的 README、USAGE 与 rust/README 实读整理（2026-09-15 核实）。命令面变动较快，实际操作以 `claw --help` 与仓库最新文档为准。*