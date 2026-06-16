---
title: "RTK：Rust 写的高性能 CLI 代理，Claude Code 场景节省 80% Token"
date: "2026-04-27T01:03:00+08:00"
slug: rtk-rust-token-killer
description: "RTK 是一个 Rust 写的高性能 CLI 代理，通过过滤和压缩命令输出让 LLM 节省 60-90% Token。一行命令安装，零依赖，单二进制，支持 Claude Code、Cursor、Copilot 等 12 种 AI 编码工具。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "CLI", "Token", "Claude Code", "LLM", "效率工具"]
---

# RTK：Rust 写的高性能 CLI 代理，Claude Code 场景节省 80% Token

一个 Claude Code 会话（30 分钟）里，开发者的 shell 命令会消耗约 118,000 tokens。用了 RTK，同样的操作只消耗约 23,900 tokens，节省 **80%**。

这就是 RTK（Rust Token Killer）做的事。

GitHub 35.9k stars，MIT 协议，单个 Rust 二进制文件，零依赖，支持 100+ 命令的智能过滤和压缩。

---

## 一、问题：LLM 在命令行场景里 Token 浪费在哪里？

当你用 Claude Code / Cursor 等 AI 编码工具工作时，每次让 LLM 执行一个 shell 命令，命令的输出会被完整地塞进 LLM 的 context window。问题是：

- `git diff` 输出 50 行，但只有 3 行真正关键（文件路径 + 变更统计）
- `cargo test` 输出 200 行，但 LLM 真正需要的是"哪几个测试失败了"
- `ls -la` 输出 40 行，但 LLM 只需要知道"这个目录有哪些文件"
- `pytest` 输出几百行测试日志，但大部分是 passed 的冗余信息

这些输出的噪音密度极高，消耗大量 Token 但信息价值极低。**LLM 在读它不需要看到的东西。**

RTK 解决这个问题的方式是：**在命令输出进入 LLM 之前，先经过一层智能过滤和压缩**。

---

## 二、RTK 工作原理：四层过滤策略

```
  Without rtk:                                    With rtk:

  Claude  --git status-->  shell  -->  git         Claude  --git status-->  RTK  -->  git
    ^                                   |            ^                      |          |
    |        ~2,000 tokens (raw)        |            |   ~200 tokens        | filter   |
    +-----------------------------------+            +------- (filtered) ---+----------+
```

RTK 对每种命令类型应用四层过滤策略：

### 2.1 Smart Filtering（智能过滤）

移除噪音内容：注释、空格、模板代码、冗余的 ASCII 分隔线。保留对 LLM 有意义的内容。

### 2.2 Grouping（分组聚合）

将相似项聚合：
- 文件按目录分组（而不是逐行列出）
- 错误按类型分组（同类错误只显示一次）
- 测试结果按状态分组（passed/failed 分块显示）

### 2.3 Truncation（截断）

保持相关上下文，裁掉冗余部分。例如 `git log` 输出 50 行 commit 历史，RTK 只保留关键信息压缩到几行。

### 2.4 Deduplication（去重）

将重复的日志行折叠为一行，附带出现次数：
```
[repeated 47 times] Failed to connect to database
```
这样 LLM 知道这个问题出现了 47 次，但只占用 1 行的 Token。

---

## 三、Token 节省实测（30 分钟 Claude Code 会话）

| 操作 | 频率 | 原始 Token | RTK 后 | 节省 |
|------|------|-----------|--------|------|
| `ls` / `tree` | 10x | 2,000 | 400 | -80% |
| `cat` / `read` | 20x | 40,000 | 12,000 | -70% |
| `grep` / `rg` | 8x | 16,000 | 3,200 | -80% |
| `git status` | 10x | 3,000 | 600 | -80% |
| `git diff` | 5x | 10,000 | 2,500 | -75% |
| `git log` | 5x | 2,500 | 500 | -80% |
| `git add/commit/push` | 8x | 1,600 | 120 | -92% |
| `cargo test` / `npm test` | 5x | 25,000 | 2,500 | -90% |
| `ruff check` | 3x | 3,000 | 600 | -80% |
| `pytest` | 4x | 8,000 | 800 | -90% |
| `go test` | 3x | 6,000 | 600 | -90% |
| `docker ps` | 3x | 900 | 180 | -80% |
| **Total** | | **~118,000** | **~23,900** | **-80%** |

> 数据来源：基于中大型 TypeScript/Rust 项目的实测估算，实际节省因项目规模而异。

---

## 四、安装与快速开始

### 4.1 安装方式

```bash
# Homebrew（推荐）
brew install rtk

# 快速安装（Linux/macOS）
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh

# Cargo
cargo install --git https://github.com/rtk-ai/rtk

# Windows（推荐用 WSL 获取完整支持）
# 或下载 releases 里的 .zip，解压后将 rtk.exe 加入 PATH
```

验证安装：
```bash
rtk --version   # rtk 0.28.2
rtk gain        # 显示 token 节省统计
```

### 4.2 初始化（为 AI 工具启用）

```bash
rtk init -g                     # Claude Code / Copilot（默认）
rtk init -g --gemini            # Gemini CLI
rtk init -g --codex             # Codex (OpenAI)
rtk init -g --agent cursor      # Cursor
rtk init --agent windsurf       # Windsurf
rtk init --agent cline          # Cline / Roo Code
rtk init --agent kilocode       # Kilo Code
rtk init --agent antigravity    # Google Antigravity

# OpenClaw 用户
openclaw plugins install ./openclaw
```

初始化后会安装一个 hook，自动拦截 Bash 命令并重写为 rtk 版本，重启 AI 工具后生效。

### 4.3 工作示例

```bash
# 普通 git push（~200 tokens）→ rtk git push（~10 tokens）
# 普通 cargo test（200+ 行失败输出）→ rtk cargo test（~20 行精简输出）
# 普通 pytest（几百行测试日志）→ rtk pytest（只显示失败测试）

# 可以直接调用 rtk 命令
rtk git status
rtk ls .
rtk read file.rs
rtk cargo test
rtk pytest
```

---

## 五、支持的 AI 工具（12 个）

| 工具 | 安装方式 | 集成方法 |
|------|---------|---------|
| **Claude Code** | `rtk init -g` | PreToolUse hook (bash) |
| **GitHub Copilot (VS Code)** | `rtk init -g --copilot` | PreToolUse hook |
| **GitHub Copilot CLI** | `rtk init -g --copilot` | deny-with-suggestion（CLI 限制）|
| **Cursor** | `rtk init -g --agent cursor` | preToolUse hook (hooks.json) |
| **Gemini CLI** | `rtk init -g --gemini` | BeforeTool hook |
| **Codex** | `rtk init -g --codex` | AGENTS.md + RTK.md |
| **Windsurf** | `rtk init --agent windsurf` | .windsurfrules（项目级别）|
| **Cline / Roo Code** | `rtk init --agent cline` | .clinerules |
| **OpenCode** | `rtk init -g --opencode` | Plugin TS (tool.execute.before) |
| **OpenClaw** | `openclaw plugins install ./openclaw` | Plugin TS (before_tool_call) |
| **Kilo Code** | `rtk init --agent kilocode` | .kilocode/rules/rtk-rules.md |
| **Google Antigravity** | `rtk init --agent antigravity` | .agents/rules/antigravity-rtk-rules.md |

> Mistral Vibe 支持：已在规划中（受限于 upstream 问题）。

---

## 六、支持命令列表（100+）

RTK 支持的命令覆盖以下类别：

### 文件操作
- `rtk ls` / `rtk tree` — 目录树精简版
- `rtk read` — 智能文件读取（支持 aggressive 模式，只显示签名）
- `rtk smart` — 启发式 2 行代码摘要
- `rtk find` / `rtk grep` — 分组搜索结果
- `rtk diff` — 压缩 diff 输出

### Git 操作
- `rtk git status` — 精简状态
- `rtk git log -n 10` — 单行 commit 历史
- `rtk git diff` — 压缩 diff
- `rtk git add/commit/push` — → "ok" 格式（push 显示分支）

### 测试运行器
- `rtk jest` / `rtk vitest` — 只显示失败
- `rtk playwright test` — E2E 结果（只显示失败）
- `rtk pytest` — Python 测试（-90%）
- `rtk go test` — Go 测试（NDJSON，-90%）
- `rtk cargo test` — Rust 测试（-90%）
- `rtk rspec` — Ruby 测试（JSON，-60%+）
- `rtk err <cmd>` — 过滤任意命令的错误行

### 构建与 Lint
- `rtk lint` — ESLint 按规则/文件分组
- `rtk tsc` — TypeScript 错误按文件分组
- `rtk cargo build` — Cargo 构建（-80%）
- `rtk ruff check` — Python linting（JSON，-80%）
- `rtk golangci-lint run` — Go linting（-85%）

### AWS / Docker / kubectl
- `rtk aws ec2 describe-instances` — 精简实例列表
- `rtk docker ps` — 精简容器列表
- `rtk kubectl pods` — 精简 pod 列表

### 数据分析
- `rtk json` — 显示结构而非值
- `rtk deps` — 依赖摘要
- `rtk log` — 去重日志
- `rtk curl` / `rtk wget` — 截断 + 保存完整输出

---

## 七、Token 节省统计与发现

RTK 内置了分析工具，帮助你了解实际节省了多少 Token：

```bash
rtk gain                        # 汇总统计
rtk gain --graph                # ASCII 图（过去 30 天）
rtk gain --history              # 最近命令历史
rtk gain --daily                # 按天分解
rtk gain --all --format json    # JSON 导出（接入 Dashboard）

rtk discover                    # 发现未被 rtk 覆盖的命令
rtk discover --all --since 7    # 扫描所有项目，过去 7 天

rtk session                     # 显示最近会话中 RTK 的覆盖率
```

---

## 八、失败输出保留（TEE 机制）

当命令失败时，RTK 默认保存完整未过滤的输出到 `~/.local/share/rtk/tee/`：

```
FAILED: 2/15 tests
[full output: ~/.local/share/rtk/tee/1707753600_cargo_test.log]
```

这样 LLM 在分析失败原因时可以直接读取完整日志，而不需要重新执行命令。可以通过 `~/.config/rtk/config.toml` 配置：

```toml
[tee]
enabled = true          # 默认 true
mode = "failures"       # "failures"（仅失败时）/ "always" / "never"
```

---

## 九、Windows 支持说明

| 功能 | WSL（完整支持） | 原生 Windows |
|------|---------------|-------------|
| 过滤器（cargo、git 等）| 完整 | 完整 |
| Auto-rewrite hook | 支持 | 不支持（降级为 CLAUDE.md 注入模式）|
| `rtk init -g` | Hook 模式 | CLAUDE.md 模式 |
| `rtk gain` / 分析 | 完整 | 完整 |

**推荐使用 WSL** 以获得完整体验。原生 Windows 下 RTK 可以工作，但 auto-rewrite 不生效，需要手动调用 `rtk` 命令。

---

## 十、与同类工具的对比

| 工具 | 语言 | 依赖 | Token 节省 | AI 工具支持 |
|------|------|------|-----------|-----------|
| **RTK** | Rust | 无（单二进制）| 60-90% | 12 种 |
| n/a（无直接竞品）| — | — | — | — |

RTK 的优势在于：

1. **零依赖**：Rust 编译成单个二进制，不依赖 Node.js 或 Python 运行时
2. **支持面广**：覆盖 100+ 命令，包括测试/构建/lint/Git/AWS/Docker/K8s
3. **AI 工具集成深**：不只是 CLI 过滤器，而是通过 PreToolUse hook 透明拦截 Bash 命令
4. **Token 分析**：内置 `rtk gain` 帮助量化节省效果
5. **失败保留**：TEE 机制确保 LLM 在命令失败时能读到完整日志

---

## 总结

RTK 是一个解决实际问题的小而美的工具：LLM 在 shell 命令输出里浪费大量 Token，RTK 用四层过滤策略（智能过滤 + 分组 + 截断 + 去重）把输出压缩到最小，同时保留 LLM 需要的关键信息。

对于一个 30 分钟的 Claude Code 会话，118k tokens 的消耗可以降到 24k，节省 80%，直接降低 AI 编码成本。对 Claude Code 用户来说，这基本是必装的效率工具。

单二进制、零依赖、安装简单、支持 12 种 AI 编码工具，值得一试。

**相关链接：**

- GitHub：https://github.com/rtk-ai/rtk（35.9k stars）
- 官网：https://www.rtk-ai.app
- 文档：https://www.rtk-ai.app/guide

🦞 每日 08:00 自动更新