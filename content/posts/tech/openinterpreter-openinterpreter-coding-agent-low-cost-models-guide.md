---
title: 'openinterpreter/openinterpreter 深度拆解：把低成本模型包装成 Claude Code 的 "harness emulation" 是怎么做到的'
date: 2026-07-16T02:50:00+08:00
lastmod: 2026-07-16T02:50:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Open Interpreter", "Coding Agent", "Rust", "Codex", "Harness", "Anthropic Messages"]
description: "Open Interpreter 是 OpenAI Codex CLI 的 Rust fork，65k+ stars，核心创新是 harness emulation：在同一 runtime 里把低成本模型（DeepSeek/Kimi/Qwen/SWE-agent 等）路由到 Claude Code、Codex、Anthropic Messages 不同 wire format 上，让小模型也能跑出大模型的 agent 工作流。"
weight: 1
author: text-matrix
---

## 一句话判断

**Open Interpreter（[openinterpreter/openinterpreter](https://github.com/openinterpreter/openinterpreter)）是一个 fork 自 OpenAI Codex CLI 的 Rust 重写版 coding agent runtime。它的核心不是"又一个 Codex clone"，而是把"低成本模型 + Claude Code harness"这件事做到了 wire format 级别。** 用一句官方 README 的话说："Open Interpreter is a fork of OpenAI's Codex, with a focus on emulating the agent harness that gets the best performance out of low-cost models." 65k+ stars，Apache-2.0，原 Python 版（OpenInterpreter/open-interpreter）已迁出为社区维护的 `endolith/open-interpreter`，主线就是这个 Rust 版本。

它和"传统 Codex CLI"最大的区别：**Codex CLI 是 OpenAI 一家的客户端，Open Interpreter 是一个 harness router**——同一份 runtime，依据 `harness` 配置把请求改写成 Responses API、Chat Completions、Anthropic Messages 等不同 wire format，并复用对应的 prompt schema、tool schema、message conversion 和 response handling。

如果你正在选型"给小模型接 Claude Code 级别 agent loop"，这篇文章值得读完整。

---

## 系统地图

```
┌──────────────────────────────────────────────────────────────────────┐
│                       Open Interpreter (Rust runtime)                  │
│                                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐                │
│  │ TUI (`i`)   │  │ `interpreter` │  │ `interpreter acp`│  ← 入口       │
│  │ slash cmd   │  │   CLI binary  │  │  (ACP agent)    │                │
│  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘                │
│         └─────────────────┼────────────────────┘                          │
│                           ▼                                              │
│              ┌────────────────────────────┐                              │
│              │   Harness Router（核心创新） │                              │
│              │   ───────────────────────── │                              │
│              │   native / claude-code      │                              │
│              │   claude-code-bare / zcode  │                              │
│              │   kimi-cli / qwen-code      │                              │
│              │   deepseek-tui / swe-agent  │                              │
│              │   minimal                   │                              │
│              └──────────────┬──────────────┘                              │
│                             ▼                                             │
│         ┌─────────────────────────────────────────┐                       │
│         │  Wire Format Adapter                    │                       │
│         │   Responses API  (native)               │                       │
│         │   Chat Completions  (generic chat)      │                       │
│         │   Anthropic Messages  (claude-code*)   │                       │
│         └──────────────┬──────────────────────────┘                       │
│                        ▼                                                  │
│        ┌────────────────────────────────────────┐                         │
│        │  Sandbox + Approval Policy             │                         │
│        │   read-only / workspace-write /         │                         │
│        │   danger-full-access                    │                         │
│        │   + untrusted / on-request / never      │                         │
│        └──────────────┬─────────────────────────┘                         │
│                       ▼                                                   │
│       ┌────────────────────────────────────┐                              │
│       │  Model Manager (live + bundled)    │                              │
│       │   provider /models + provider_info │                              │
│       │   + model_compatibility_catalog    │                              │
│       └────────────────────────────────────┘                              │
└──────────────────────────────────────────────────────────────────────┘
                          ▼
                External provider / model
```

这张图最重要的一条路径：**TUI/CLI/ACP 三个入口 → Harness Router → Wire Format Adapter → 模型**。三者（harness / wire format / model）解耦后，"用 Kimi CLI 的 prompt 风格去驱动一个 Qwen 模型、用 Claude Code 的工具 schema 去约束一个 DeepSeek"这样的组合就成为可能。

---

## 边界与角色划分

Open Interpreter 的设计边界可以用四个"不变项"概括：

| 维度 | 不变项 | 含义 |
|------|--------|------|
| 模型来源 | 多 provider + 低成本优先 | 同一 runtime 接 GPT-5.x、Claude、DeepSeek、Kimi、Qwen、本地 OSS |
| Agent harness | 9 种内置 + 自定义 | 在 prompt schema / tool schema / message conversion 三个层面切换 |
| Wire format | 三种 adapter | Responses / Chat Completions / Anthropic Messages |
| 安全边界 | Sandbox × Approval 双轴 | `read-only` / `workspace-write` / `danger-full-access` × `untrusted` / `on-request` / `never` |

不变项之外，**它明确不做**的事：

- ❌ **不**自己托管外部 agent CLI。"The public runtime does not shell out to the real external agent CLI"——harness emulation 是 prompt/schema 层面的复刻，不是 `exec("claude", ...)` 转发。
- ❌ **不**维护一份手写 model list。"Open Interpreter does not keep one hand-written Rust list of every model"——model metadata 是分层拉取的：live `/models` endpoint + bundled provider_catalog.json + compatibility_catalog.json + 用户 config `model_catalog`。
- ❌ **不**锁死 OS。原 Python 版跨平台用 subprocess，新 Rust 版通过 `bwrap` / native sandboxing 在 macOS、Linux、Windows 三端都跑。

这三条"不做"恰好决定了它的设计取舍——下面拆开看。

---

## 关键机制：Harness Emulation 是怎么做到的

### 1. Harness ID 与 wire_api 的二维路由

`docs/harness.md` 公开了一张路由表，是整个 runtime 最值得读的几行：

| Harness ID | Wire API | Request route | 对应的真实产品 |
| --- | --- | --- | --- |
| `unset / ""` | `responses` | Responses API | Native Codex 兼容面 |
| `unset / ""` | `chat` | Chat Completions | 通用 OpenAI 兼容 chat provider |
| `claude-code` | `messages` | Anthropic Messages | Claude Code 完整 agent surface |
| `claude-code-bare` | `messages` | Anthropic Messages | Claude Code bare profile |
| `deepseek-tui` | `chat` | Chat harness | DeepSeek TUI / CodeWhale |
| `kimi-cli` | `chat` | Chat harness | MoonshotAI kimi-cli |
| `qwen-code` | `chat` | Chat harness | QwenLM qwen-code |
| `swe-agent` | `chat` | Chat harness | SWE-agent |
| `minimal` | `chat` | Chat harness | Open Interpreter minimal chat-tool |
| 任意其它字符串 | `chat` | Chat Completions | 自定义 marker |

**关键设计**：`harness` 是产品面（Claude Code / Kimi / Qwen）的"风格复刻"，`wire_api` 是协议面（Responses / Chat / Messages）的"传输方式"。两者正交。

配置方式：

```toml
# ~/.openinterpreter/config.toml
harness = "kimi-cli"
harness_guidance = true
```

或者一次性：

```bash
interpreter -c harness='"kimi-cli"' "solve this task"
```

### 2. Wire Format Adapter 的实战含义

不同 wire format 对 agent loop 的影响是**结构性的**，不是"换个请求格式"那么简单：

- **Responses API**：原生支持 reasoning summary、verbosity、tool calls 流式拼接。
- **Chat Completions**：最薄的兼容层，所有 provider 都能接，但 tool schema 需要手工转译成 `tools: [{type: "function", function: {name, parameters}}]`。
- **Anthropic Messages**：`<tool_use>` / `<tool_result>` 是 XML 风格块；system prompt 是一级字段而不是 message role；input 是分块的 content array。

`harness = "claude-code"` 走 Messages，意味着 Open Interpreter 在内部要把 Chat 风格 message 转成 Anthropic 的 content blocks——这一步**不是简单的格式转换**，而是 schema 层面的改写。这就是 README 里那句"emulating the agent harness"的真实含义。

### 3. 三层 model metadata 是怎么拼起来的

`docs/models.md` 显式说明 model 元数据不集中存：

| 数据源 | 角色 |
|---|---|
| Provider `/models` endpoint | 活跃 provider 的 live model id |
| `model-provider-info/provider_catalog.json` | 由 `models.dev` + live provider 源生成的 bundled seed data |
| `codex-api/model_compatibility_catalog.json` | 兼容性元数据：支持参数、search 支持、reasoning levels、input modalities |
| `models-manager/models.json` | OpenAI-style model preset 元数据 |
| Config `model_catalog` | 用户可选的静态 catalog |

这条分层是为了解决一个具体问题：**模型市场变化太快，硬编码列表永远是错的**。把"模型 id"放在 provider 端，把"能力描述"放在 bundled 文件，把"用户偏好"放在 config，每层独立失效不影响其它层。

### 4. Sandbox × Approval 的双轴矩阵

`docs/sandbox.md` 公开了 9 个安全组合里 6 个有意义的状态：

| | `untrusted` | `on-request` | `never` |
|---|---|---|---|
| `read-only` | 强约束 + 全程问 | 强约束 + 升级时问 | 强约束 + 不问（不推荐） |
| `workspace-write` | 工作区内可写 + 全程问 | 工作区内可写 + 升级时问 | 工作区内可写 + 不问 |
| `danger-full-access` | 无沙箱 + 全程问 | 无沙箱 + 升级时问 | 无沙箱 + 不问（仅可信环境） |

`on-request` 是 Open Interpreter 的默认值：sandbox 是技术边界，`on-request` 是协作边界——运行在 sandbox 里，但升级到写盘 / 网络 / 系统调用时主动问用户。这是大多数本地 coding agent 的标准姿态。

技术实现上，macOS 用原生 sandbox，Linux 用 `bwrap`（看 `codex-rs/bwrap/` 目录），Windows 用等价封装。

---

## 任务流案例：用 Kimi CLI harness 驱动 Qwen 模型

把上面的零件拼起来跑一次完整 loop：

**Step 1：安装**

```bash
curl -fsSL https://www.openinterpreter.com/install | sh
```

**Step 2：选 harness + model**

```bash
interpreter -c 'harness="kimi-cli"' \
  -c 'model_provider="dashscope"' \
  -c 'model="qwen-coder-plus"' \
  "重构 auth 模块，把所有 sync 函数改成 async"
```

**Step 3：内部发生了什么**

1. Harness Router 加载 `kimi-cli` 风格 system prompt（不是 Qwen 的，也不是 Claude Code 的）。
2. Wire Format Adapter 把 chat-style message 转成目标 provider 的 request。
3. 第一次需要 `read_file` 时触发 sandbox 决策（`workspace-write` + `on-request` 升级为 ask）。
4. 用户 approve 后，agent 在 sandbox 里执行 read，模型收到 tool result，继续。
5. 模型连续 3 次产生 tool call（read / edit / run pytest），都被 sandbox 隔离。
6. 最终输出 diff，sandbox 不撤销（因为在 workspace-write 范围内）。

**Step 4：模型切换**

如果中途觉得 Qwen 不够好，按 `/model` 切到 `claude-sonnet-4`：

- harness 保持 `kimi-cli`（prompt 风格不变）
- wire_api 切到 `messages`
- 后面的 tool call 用 Anthropic content blocks 序列化

**这是 Open Interpreter 的关键卖点**：在不改 prompt 风格的前提下，按 wire format 切换 model provider，对低成本模型验证 prompt 假设、然后切到大模型做最终执行，是同一个 runtime。

---

## 与同类项目的横向对照

| 维度 | Open Interpreter | OpenAI Codex CLI | Claude Code | SWE-agent |
|---|---|---|---|---|
| 语言 | Rust | Rust | TS + Python | Python |
| 主模型支持 | 任意 provider | OpenAI | Anthropic | 任意 chat |
| Harness 切换 | ✅ 9 种内置 | ❌ 仅 native | ❌ 单一 | ❌ SWE 风格固定 |
| Wire format | Responses / Chat / Messages | Responses | Messages | Chat |
| ACP agent | ✅ `interpreter acp` | ✅ | ✅ | ❌ |
| 沙箱 | 三模式 + 三策略 | 三模式 | permission 系统 | Docker |
| 配置目录 | `~/.openinterpreter` | `~/.codex` | `~/.claude` | 项目级 |

这张表想表达一件事：**Claude Code 是"产品"（自带 prompt / tool schema / IDE 集成），Open Interpreter 是"router"（把产品的表面复刻到任意模型上）**。两者定位互补不重叠。

---

## 适用边界

**推荐使用**：

- 已有 Claude Code prompt 假设，想验证在 Kimi / Qwen / DeepSeek 上效果
- 多 provider 备份策略（GPT-5.x 限流时切 Claude，切 Sonnet 限流时切 Qwen）
- 想用同一份 TUI 体验多种 harness prompt 风格（学习 / 对比用）
- 在 sandbox + on-request 默认姿态下做本地 coding 工作流

**不推荐使用**：

- 只用 OpenAI 模型 → 直接 Codex CLI 更省事
- 需要完整的 Claude Code 生态（IDE 深度集成、Plugin、Skills）→ 直接 Claude Code
- 不熟悉 Rust 工具链 → 改 prompt / harness 比改 Codex / Claude Code 困难
- 在没有 sandbox 概念的 CI runner 里跑 `danger-full-access` → 等于裸跑

---

## 决策建议

按团队现状选：

1. **以 OpenAI 模型为主、偶用 Claude** → Codex CLI + 手动 export ANTHROPIC_API_KEY
2. **以 Anthropic 模型为主、写代码靠 Claude Code** → Claude Code，不要绕
3. **多模型混用、想对比 harness prompt 假设** → Open Interpreter 是当前唯一直接覆盖这件事的产品
4. **多模型但只用 chat 风格** → Open Interpreter + `harness="minimal"` 或 unset，比直接接各 provider CLI 更省心
5. **研究目的** → 看 `codex-rs/harness/` 下的 prompt schema 实现，是少数公开的"Claude Code 风格复刻"参考实现

---

## 阅读路径

按需读：

- **只想上手**：README + `docs/install.md` + `docs/getting-started.md` + `docs/harness.md`
- **想理解架构**：`docs/harness.md` + `docs/models.md` + `docs/sandbox.md` + `codex-rs/cli/src/main.rs`
- **想写自定义 harness**：在 `codex-rs/` 下加一个 crate（参考 `kimi-cli` / `qwen-code` 的实现）+ 注册到 harness router
- **想理解 Rust workspace 划分**：`codex-rs/Cargo.toml` 的 `members` 是 40+ 个 crate 的功能切分

---

## 边界声明

本文基于 `openinterpreter/openinterpreter` 仓库 README（2026-07-16 抓取）、`docs/harness.md` / `docs/models.md` / `docs/sandbox.md` / `codex-rs/Cargo.toml` / `codex-rs/cli/Cargo.toml` 公开文件。仓库处于活跃迭代期，harness ID 列表 / wire_api 矩阵 / model metadata 分层可能在未来版本变化；具体实现请以仓库当时版本为准。

Open Interpreter 仍是 **fork 自 OpenAI Codex CLI** 的分支版本，长期路线与上游 Codex 的差异会持续扩大；如果你的工作流强依赖 Codex 官方语义，需要同时跟踪 `openai/codex` 主线变更。