---
title: "Caveman Coding Agent：让 Agent 少讲废话的输出压缩 Skill"
date: "2026-07-09T02:55:00+08:00"
slug: "caveman-coding-agent-output-token-compression"
description: "JuliusBrussee/caveman 是一套给 Claude Code / Codex / Cursor 等 Agent 装的输出压缩 skill，主打嘴变小脑子不变。在 README 公开的 10 prompt benchmark 上平均节省 65% 输出 token，并把代码、命令、错误信息 byte 级保留。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Token 优化", "Prompt Skill"]
---

# Caveman Coding Agent：让 Agent 少讲废话的输出压缩 Skill

## 一句话核心判断

Coding Agent 在终端里最常见的"消耗源"不是它的思考，是它的废话——"Sure, I'd be happy to help"、"Let me take a look"、"You're absolutely right" 这种前缀对单轮成本影响小，对长 session 的累计输出 token 影响巨大。JuliusBrussee/caveman（仓库 `JuliusBrussee/caveman`）做的事情恰好是给 Agent 装一张"嘴变小"的 mask：**让 Agent 沿用同样的脑子，把答复压缩成 caveman 风格（短、碎、不变形），同时保留代码、命令、错误信息 byte-for-byte 准**。在仓库公开的 10 prompt benchmark 上平均节省 65% 输出 token（区间 22%–87%），但 README 反复强调"只是输出减省、推理不受损，且 skill 自身会增加 1–1.5k input token"。

如果你的 Agent session 长期跑、对话来回很多、又不需要礼貌填充语，这套 skill 值得评估；如果 Agent 主要产出代码 diff 或结构化命令，节省幅度会随任务而波动。

## 系统地图：单 skill + 五条命令

caveman 在 Agent 视图里是一张"装配好的插件"——既有手动开关命令，也有语境自动化覆盖：

```
┌────────────────────────────────────────────────────────────────┐
│  Claude Code / Codex / Gemini / Cursor / Windsurf / Cline / 30+ │
└─────────────────────────────────────────────────┬──────────────┘
                                                  │
                                                  ▼
                ┌─────────────────────────────────────────┐
                │  /caveman [lite|full|ultra|wenyan]      │
                │  /caveman-commit                        │
                │  /caveman-review                        │
                │  /caveman-stats                         │
                │  /caveman-compress <file>               │
                │  caveman-shrink  (MCP middleware)       │
                │  cavecrew-*   (subagents)               │
                └─────────────────────────────────────────┘
                                                  │
                                                  ▼
                ┌─────────────────────────────────────────┐
                │  Agent LLM                              │
                │  —— 脑子不变（reasoning token 不动）   │
                │  —— 嘴变小（output style 压缩）        │
                └─────────────────────────────────────────┘
```

六条主命令 + 一套子代理生态，已经足够覆盖大多数"压缩风格"场景。

## 关键判断：为什么 caveman 不是"多一档 prompt"

压缩 Agent 输出这事在工具圈并不少见。caveman 的差异化在两点：

1. **可调的六档"语法风格"**：每档不只字数，而是语序 / 句子结构变化。
2. **跨多 Agent 形态全覆盖**：plugin、extension、rule file、`npx skills add` 多个分发渠道，30+ Agent 即装即用。

### 六档 caveman 语法示例

举 README 里最直观的同一个句子在不同档下的差异：

| 级别 | 同句改造 |
| --- | --- |
| normal agent | You should wrap the object in `useMemo`, since a new reference is created on every render. |
| `lite` | Wrap object in `useMemo`. New ref created every render. |
| `full`（默认） | New ref each render. Wrap object in `useMemo`. |
| `ultra` | New ref/render. `useMemo` it. |
| `wenyan` | New ref every render, so wrap in `useMemo` — rendered in classical Chinese, shorter still. |

`wenyan` 是为"文言文密度高"准备的特殊档，对中文或古汉语习惯的工程师有意义。其余四档只是断句与冗词削减，不会跨语言翻译，这点 README 写得很明确。

### 跨语言保留

caveman 压缩的是"风格"，不会翻译内容。写葡萄牙语、法语还是德语，输出仍然是同语种。这一条排除了"压缩导致跨语言失效"的常见担忧。

## 节省幅度真伪：仓库公开 benchmark

README 收录的 10 prompt benchmark（output tokens）：

| Task | Normal | Caveman | Saved |
| --- | ---: | ---: | ---: |
| Explain React re-render bug | 1180 | 159 | 87% |
| Fix auth middleware token expiry | 704 | 121 | 83% |
| Set up PostgreSQL connection pool | 2347 | 380 | 84% |
| Explain git rebase vs merge | 702 | 292 | 58% |
| Refactor callback to async/await | 387 | 301 | 22% |
| Architecture: microservices vs monolith | 446 | 310 | 30% |
| Review PR for security issues | 678 | 398 | 41% |
| Docker multi-stage build | 1042 | 290 | 72% |
| Debug PostgreSQL race condition | 1200 | 232 | 81% |
| Implement React error boundary | 3454 | 456 | 87% |
| **Average** | **1214** | **294** | **65%** |

需要看清几个关键边界：

- **只是输出减省**：input 与 reasoning token 没动。
- **skill 自身增加 ~1-1.5k input/turn**：在原本就简洁的任务上有可能净负。
- **整 session 节省比 output 数字小**：评估全 session 节省要看平均交互长度。

这意味着 caveman 不是"装了就省"，而是"在合适的工作流里大幅省"。

## 几个值得单独说的能力

### `/caveman-compress <file>`——把 memory 文件也压

这条命令专门针对长期 memory 文件（CLAUDE.md、项目笔记），压缩后这些文件"之后每个 session 都加载得更小"。README 给的真实压缩比：

| 文件 | 原 | 压 | 节省 |
| --- | ---: | ---: | ---: |
| `claude-md-preferences.md` | 706 | 285 | 59.6% |
| `project-notes.md` | 1145 | 535 | 53.3% |
| `claude-md-project.md` | 1122 | 636 | 43.3% |
| `todo-list.md` | 627 | 388 | 38.1% |
| `mixed-with-code.md` | 888 | 560 | 36.9% |
| **Average** | **898** | **481** | **46%** |

注意：压缩只动散文 / 解释，**代码、URL、路径字节级保留**。

### `caveman-shrink`——MCP middleware

这是 npm 包形式的中间件，可以套在任意 MCP server 上、把工具描述压缩。对**已注册大量 MCP 工具**（每个 tool description 都要在 system prompt 里出现）的场景，这个中间件可以省一大笔 input token：

```bash
# 注册方式（一行）
# 包名：caveman-shrink
```

### `/caveman-stats`——量化追踪

在 Claude Code 上，状态栏还会显示 `[CAVEMAN] ⛏ 12.4k`（lifetime token saved），能直接看到累计节省——不像黑盒。

## 安装路径

一行安装到 30+ 主流 Agent：

```bash
# macOS / Linux / WSL / Git Bash
curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash

# Windows PowerShell
irm https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.ps1 | iex
```

单个 Agent 安装示例（Claude Code plugin）：

```bash
claude plugin marketplace add JuliusBrussee/caveman
claude plugin install caveman@caveman
```

Cursor / Windsurf / Cline / Codex 通过 skills registry：

```bash
npx skills add JuliusBrussee/caveman -a cursor
```

## 适用边界

**适合**：

- 长 session 工程师工作流（如 `/build` / `/refactor` / `/review` 多轮）
- Agent 经常"礼貌填充"，占输出的比例明显
- 已经有 memory 文件要长期压缩，`/caveman-compress` 一次省 46%
- 已经注册多个 MCP server，`caveman-shrink` 可减少 system prompt 体积

**不太适合**：

- 一次性短问答——input 增长（+1-1.5k/turn）可能抵掉 output 节省
- 输出本身已经简洁（如 commit message 严格 50 字符）
- 已经高度依赖别的 style system——避免互相覆盖
- 对"礼貌语" 有强需求（写作类、客户对话类场景）

## 一句话总结

caveman 把 Agent 输出的"礼貌填充"换成"短小碎句"，对长 session 的工程师工作流能在 output 上省 60%+ token，对 input 也有 memory 压缩的二次收益；前提是工作流确实跑长、且能接受 skill 自身约 1.5k input 的成本。

## 参考链接

- 仓库：<https://github.com/JuliusBrussee/caveman>
- npm 包：`caveman-shrink`
- benchmark：`benchmarks/` / `evals/`
- License：MIT
- 引用论文：<https://arxiv.org/abs/2604.00025>（Brevity Constraints Reverse Performance Hierarchies）
