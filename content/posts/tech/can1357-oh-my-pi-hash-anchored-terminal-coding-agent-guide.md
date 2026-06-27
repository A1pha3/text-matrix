---
title: "oh-my-pi：把 hash-anchored 编辑做进终端 AI 编程 Agent"
date: "2026-06-25T18:05:11+08:00"
slug: "can1357-oh-my-pi-hash-anchored-terminal-coding-agent-guide"
description: "can1357/oh-my-pi（omp）是 14.5k+ Stars 的终端 AI 编程 Agent，fork 自 Mario Zechner 的 pi-mono。它用 hashline 锚定编辑把 str_replace 的失败模式（whitespace 不一致、anchor 漂移、整段重打）从根上拆掉；用 32 个工具 + 14 LSP + 28 DAP + ~55k 行 Rust 内核构建\"Agent 真的能调的工具\"。文章拆 hashline 的 [PATH#TAG] 格式、SWAP/INS/DEL 操作符、与同类 Agent 的精度/成本对比、以及在生产 Agent 中的适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["oh-my-pi", "hashline", "AI Coding Agent", "终端 Agent", "Rust", "TypeScript", "LSP", "DAP", "MCP", "工具调用"]
---

# oh-my-pi：把 hash-anchored 编辑做进终端 AI 编程 Agent

## 快速信息卡

| 项目 | 信息 |
|------|----------|
| **Stars** | 14,781+ |
| **Forks** | 1,302+ |
| **许可证** | MIT |
| **语言** | TypeScript + Rust |
| **仓库** | [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) |

## 学习目标

阅读本文后，你将能够：

1. **解释 hashline 锚定编辑的原理和优势**，掌握其 `[PATH#TAG]` 格式、状态机和 stale-tag 恢复机制
2. **描述 oh-my-pi 的四层架构**（交互层、编排层、工具层、Rust 内核），并解释每层的核心职责
3. **对比 hashline 与 str_replace 的精度和成本**，通过真实编辑示例理解为什么 hashline 能显著降低 token 消耗和失败率
4. **列出 oh-my-pi 的 32 个内置工具 + 14 LSP + 28 DAP 操作**，理解"Agent 真的能调的工具"的含义
5. **判断什么时候选 omp，什么时候 Claude Code / Cursor / Aider 更合适**，基于项目类型、任务长度、工具需求做决策

## 目录

- [核心判断](#核心判断)
- [阅读路径](#阅读路径)
- [系统地图](#系统地图)
- [hashline 格式](#hashline-格式)
- [hashline 状态机](#hashline-状态机)
- [真实编辑示例](#真实编辑示例)
- [hashline 的真实效果](#hashline-的真实效果)
- [与 Claude Code / Gemini CLI / Aider 的对比](#与-claude-code--gemini-cli--aider-的对比)
- [Rust 内核](#rust-内核)
- [工作流特性](#工作流特性)
- [适用场景与边界](#适用场景与边界)
- [自测清单](#自测清单)
- [进阶路径](#进阶路径)
- [常见问题](#常见问题)
- [参考链接](#参考链接)

---

## 核心判断

`can1357/oh-my-pi`（命令名 `omp`，项目主页 [omp.sh](https://omp.sh)）是 Can Bölük 维护的终端 AI 编程 Agent，2025-12-31 立项，到 2026-06 已经 14.5k+ Stars、1.2k+ Forks。它 fork 自 Mario Zechner 的 [pi-mono](https://github.com/badlogic/pi-mono)，把"Pi"从一个底层 LLM 客户端重写成"开箱即用的编码工作流"。

oh-my-pi 解决的核心问题不是"让模型更聪明"，而是"让模型改文件时不再白做工"。绝大多数终端 AI Agent 给模型一个 `str_replace(old, new)` 工具：模型必须把要替换的整段代码**原样**抄进调用里——缩进、空格、换行、emoji 都要一致，差一个字符就 `String not found`，进入无限重试循环。oh-my-pi 的解法是 `hashline`：把"行号 + 行内容哈希"做成一等公民的锚点，模型只需要说"第 12 行的整行换成这一句"，**永不**重新抄原文。

配套的核心创新是工具编排层（harness）：

- 32 个内置工具（read/write/edit/bash/eval/lsp/debug/browser/web_search/github/...）
- 14 个 LSP 操作 + 28 个 DAP 操作，模型调 `lsp rename` 真的走 `workspace/willRenameFiles`，处理 re-exports 和 barrel 文件
- ~55k 行 Rust 内核（shell、grep、glob、ast、iso、tokens、sixel...），把 `ripgrep`、`bash`、`find`、`ast-grep`、`tiktoken` 全部 in-process 链接，热路径上 0 次 fork-exec
- 40+ 模型 provider + per-role 路由（default / smol / slow / plan / commit）

数字上最直观的验证：Grok Code Fast 1 在 hashline 启用后，pass rate 从 **6.7% 跳到 68.3%**；Grok 4 Fast 输出 token 下降 **61%**；在 MiniMax 上 pass rate 翻 2.1 倍。这些数字来自 [blog.can.ac/2026/02/12/the-harness-problem/](https://blog.can.ac/2026/02/12/the-harness-problem/)，是同一作者的基准数据。

文章要拆开的事：

1. 核心创新——hashline 锚定编辑的格式、状态机和 stale-tag 恢复
2. 系统地图——agent loop、tool harness、context 管理、provider 路由四层
3. 与现有工具的精度 / 速度 / 成本对比
4. 真实编辑示例——普通 str_replace 和 hashline 的区别
5. 工具编排层——LSP/DAP/Rust 内核如何把"AI 写代码"从 demo 拉进生产
6. 适用边界——什么时候选 omp，什么时候 Claude Code / Cursor / Aider 更合适

## 阅读路径

- **想看 hashline 算法**：§4 格式 + §5 状态机 + §6 真实编辑示例
- **想看系统地图**：§3 整体架构 + §4-§7 逐层拆解
- **想看性能数据**：§8 基准数据 + §9 与 Claude Code/Gemini CLI/Aider 的精度对比
- **想看 Rust 内核**：§10 工具编排层 + §11 55k 行 Rust 在做什么
- **想看选型决策**：§12 适用场景 + §13 不适用场景

## 系统地图

oh-my-pi 是一个 monorepo，14 个 npm 包 + 6 个 Rust crate，按"交互 → 编排 → 工具 → 内核"四层组织：

```
oh-my-pi
├── 交互层
│   ├── packages/coding-agent/        # CLI 入口（omp、omp -p、omp acp）
│   ├── packages/tui/                 # 差分渲染 TUI（Kitty 键盘协议 + PHF 完美哈希）
│   └── packages/collab-web/          # 浏览器 guest client + relay
│
├── 编排层
│   ├── packages/agent/               # Agent runtime、tool calling、状态机
│   ├── packages/hashline/            # 锚定 patch 语言 + applier
│   ├── packages/mnemopi/             # 本地 SQLite 长期记忆
│   └── packages/snapcompact/         # 位图帧上下文压缩 + SQuAD 评测
│
├── 工具层（32 个内置工具）
│   ├── read / write / edit / ast_edit / ast_grep / search / find
│   ├── bash / eval / ssh             # 运行时
│   ├── lsp / debug                   # 代码智能（DAP/LSP）
│   ├── task / irc / todo / job / ask # 协调
│   ├── browser / web_search / github / generate_image / inspect_image / tts
│   ├── checkpoint / rewind / retain / recall / reflect  # 记忆与状态
│   └── resolve / search_tool_bm25    # 杂项
│
├── 模型层
│   ├── packages/ai/                  # 多 provider LLM 客户端（流式 + 工具调用）
│   ├── packages/catalog/             # 模型目录 + provider 描述符
│   └── packages/wire/                # collab 协议类型
│
└── Rust 内核（~55k LoC，4 个 crate + 平台 N-API addon）
    ├── crates/pi-natives/            # N-API cdylib 聚合
    ├── crates/pi-shell/              # brush-shell 包装的 bash + PTY
    ├── crates/pi-ast/                # tree-sitter + ast-grep 包装
    ├── crates/pi-iso/                # APFS/btrfs/zfs/overlayfs 工作区隔离
    └── crates/brush-*-vendored/      # vendored brush-shell
```

四层的职责切割：

- **交互层**只关心输入输出：TUI、CLI 参数、ACP/JSON-RPC 协议、Node SDK
- **编排层**关心"Agent 这一轮要走哪些工具、context 该长什么样"——hashline 的 applier 在这里
- **工具层**关心"这一类操作的具体语义"——`read` 知道怎么读 PDF/notebook/URL/SQLite，`debug` 知道怎么跟 lldb-dap 对话
- **Rust 内核**关心"高频底层操作别走 fork-exec"——ripgrep、bash、find、tiktoken 全 in-process

四层之间的调用方向是严格自上而下的：交互层不直接调 Rust，所有 native 调用经过编排层的 Node N-API 绑定。

## hashline 格式

普通 str_replace 失败的根本原因是"模型必须重打一遍要替换的原文"。任何空白、缩进、引号、转义、注释的差异都会让 anchor 漂移，触发 `String not found`，模型进入"再试一次"循环——每次都把同样的原文重新放进 prompt 烧 token。

hashline 的解法是**双重锚定**：

1. **行号**——`read` 返回的每行带 `LINE:TEXT` 前缀（`12:const greeting = "hi";`）
2. **快照标签**——文件头 4-hex hash，记录"我看到的文件状态"

完整 patch 的语法（来自 [packages/hashline/grammar.lark](https://github.com/can1357/oh-my-pi/blob/main/packages/hashline/src/grammar.lark)）：

```lark
start: begin_patch file_patch+ end_patch
begin_patch: "*** Begin Patch" LF
end_patch:   "*** End Patch" LF?
file_patch: file_header hunk+
file_header: "[" filename "#" file_hash "]" LF
file_hash: /[0-9A-F]{4}/
```

`#TAG` 是 4 位十六进制（0000–FFFF），是 `SnapshotStore` 给完整规范化文件文本算的哈希。`PATCHER` 在应用前先 resolve tag，验证 live 文件内容哈希是否还匹配——不匹配直接拒绝 patch，防止模型基于过期 `read` 改错文件。

文件 section 内部的操作符：

| 操作 | 语法 | 含义 |
|------|------|------|
| 替换行 | `SWAP N.=M:` | 替换原始 N 到 M 行（含两端），下面 `+TEXT` 行是新内容 |
| 替换块 | `SWAP.BLK N:` | 替换 N 行开始的整个语法块（tree-sitter 解析闭区间） |
| 删除行 | `DEL N.=M` | 删除 N 到 M 行，无 body |
| 删除块 | `DEL.BLK N` | 删除 N 行开始的整个块 |
| 前插 | `INS.PRE N:` | 在 N 行**之前**插入 body |
| 后插 | `INS.POST N:` | 在 N 行**之后**插入 body |
| 块后插 | `INS.BLK.POST N:` | 在 N 行开始的块的**末尾之后**插入（同级） |
| 文件头/尾 | `INS.HEAD:` / `INS.TAIL:` | 文件首尾插入 |

最关键的规则：**body 行只有 `+TEXT`**。没有 `-old` 行，没有上下文行，没有 unified diff 头。

## hashline 状态机

hashline 不是"行号 + 文本"的玩具，它有完整的生命周期管理：

### 5.1 快照的 mint 与销毁

每次 `read` 或 `search` 返回时，`SnapshotStore.record(path, content)` 计算 4-hex hash 并存储。模型拿到的响应里每行都带 `LINE:TEXT` 前缀：

```
[greet.py#A1B2]
1:def greet(name):
2:    msg = "Hello, " + name
3:    print(msg)
4:greet("world")
```

模型编辑时**必须**复用 `#A1B2`。编辑成功一次，`Patcher` 给文件计算**新** hash 并 mint 新 tag，原始行号全部作废。模型必须 re-`read` 拿新行号——**这是 prompt.md 的第一条 critical rule**：

> Every apply mints a fresh `#TAG` and renumbers — take the next edit's numbers from the edit response or a fresh `read`. Stale tag or surprise? STOP, re-`read`.

### 5.2 stale tag 拒绝

如果模型用 `#A1B2` 编辑，但文件已经被另一进程（或同一进程的前一个 edit）改成 hash `#C3D4`，`Patcher` 检测到 tag 不匹配：

- **不** 静默应用
- **不** 尝试"尽力匹配"
- 拒绝 patch，返回 mismatch error

模型看到错误后必须 `read` 一次拿新状态，再重新构造 patch。这一步把"过期记忆"和"实际文件"完全隔开——Claude Code / Gemini CLI 这类工具在 str_replace 失败时通常会重试 2-3 次然后放弃，hashline 在第一次 stale 就 STOP。

### 5.3 session-aware recovery

`SnapshotStore` 缓存了**编辑前**的快照。当 live 文件 hash 不匹配时，recovery 模块用 3-way merge 尝试恢复：

- base = 缓存的 pre-edit 内容
- theirs = 现在的 live 文件
- yours = 模型想改成的目标

如果 yours 在 theirs 上能干净 3-way 合上，自动 apply；否则仍然拒绝。`Patcher` 接口支持 in-memory、disk、S3、LSP text-document protocol、Git tree 等任意 `Filesystem` 子类——同一个 patch 语言可移植到任何 backend。

### 5.4 范围紧凑性检查

`prompt.md` 显式禁止"宽范围 + 重打 keepers"的反模式：

> WRONG — a pure insertion done as a widened `SWAP`: you want to add one line after 2, but you replace 2.=4, retype the keepers, and drop one (here line 4, `greet("world")`).

`Patcher` 检测"body 里有近似于未修改范围外行的内容"时**自动 drop** 并发 warning，但 prompt 明确要求**不要依赖这个修复**——发出去的 patch 应该只覆盖"要改的行"。

## 真实编辑示例

假设模型要在一个 Python 文件里加一行，并把某行的字符串替换掉。原文：

```python
def greet(name):
    msg = "Hello, " + name
    print(msg)

greet("world")
```

### 6.1 用 str_replace 工具（Claude Code / Gemini CLI / Aider 风格）

```python
# 调用 1：插入守卫
str_replace(
  file_path="greet.py",
  old_string='def greet(name):\n    msg = "Hello, " + name',
  new_string='def greet(name):\n    if not name: name = "stranger"\n    msg = "Hello, " + name'
)

# 调用 2：替换字符串拼接为 f-string
str_replace(
  file_path="greet.py",
  old_string='    msg = "Hello, " + name',
  new_string='    greeting = "Hi"\n    msg = f"{greeting}, {name}"'
)

# 调用 3：删除 print
str_replace(
  file_path="greet.py",
  old_string='    print(msg)\n\ngreet',
  new_string='greet'
)
```

每次调用都要把原文重打一遍。注意第二次调用时 `old_string` 必须是**当前**文件的实际内容（已经经过第一次插入），第三次同理。三次调用三段原文，总输入 token 约 380 字符。

### 6.2 用 hashline（oh-my-pi 风格）

```text
*** Begin Patch
[greet.py#A1B2]
INS.POST 1:
+    if not name: name = "stranger"
SWAP 2.=2:
+    greeting = "Hi"
+    msg = f"{greeting}, {name}"
DEL 3
*** End Patch
```

模型**不**重打任何已有行——所有锚点都是"行号"。输入 token 约 180 字符，不到 str_replace 的一半。

更重要的差异是**失败率**。str_replace 在以下场景会失败：

- 缩进用了 tab，原文用了空格
- 原文有 BOM，模型看不到
- 原文末尾有 trailing whitespace
- 原文有 CRLF，模型用 LF 写
- 文件在 Agent 思考期间被另一进程改过（pre-commit hook、formatter on save）
- 原文里有非 ASCII 字符（中文注释、emoji）模型用 `\u` 转义失败

hashline 对这些都不敏感——它操作的是行号 + tree-sitter 解析后的行内容，行内容在 read 时规范化，编辑时还原规范化。

## hashline 的真实效果

[blog.can.ac/2026/02/12/the-harness-problem/](https://blog.can.ac/2026/02/12/the-harness-problem/) 的基准（来自 oh-my-pi 同一作者）：

| 模型 | 指标 | 数字 | 原因 |
|------|------|------|------|
| Grok Code Fast 1 | pass rate | 6.7% → 68.3% | hashline 替换 str_replace 格式 |
| Gemini 3 Flash | pass rate | +5pp | 超过 Google 自家 str_replace 实现 |
| Grok 4 Fast | output tokens | -61% | 输出在 retry 循环消失后塌缩 |
| MiniMax | pass rate | 2.1× | 同权重同 prompt，仅 harness 变 |

`6.7% → 68.3%` 的跃迁本质是"模型本来能做对，但 str_replace 格式让 90% 的尝试死在 anchor 漂移上"——把 harness 修对，模型能力立刻显现。

## 与 Claude Code / Gemini CLI / Aider 的对比

| 维度 | oh-my-pi | Claude Code | Gemini CLI | Aider |
|------|----------|-------------|------------|-------|
| 锚定方式 | hashline（行号 + 4-hex tag） | str_replace（字符串匹配） | str_replace | search/replace（diff 格式） |
| 工具数 | 32 个内置 + 14 LSP + 28 DAP | Bash/Read/Write/Edit/Grep/Glob 等 | 同 Claude Code | Read/Write/Shell/Architect |
| LSP rename 走 willRenameFiles | ✅ | ❌（只 sed） | ❌ | ❌ |
| 内置 DAP 调试（lldb/dlv/debugpy） | ✅ | ❌ | ❌ | ❌ |
| 持久 Python + JavaScript 双 kernel | ✅（eval） | ❌ | ❌ | ❌ |
| 浏览器自动化（CDP） | ✅（Puppeteer + stealth） | ❌ | ❌ | ❌ |
| 工作区隔离（APFS clone / reflink） | ✅（pi-iso） | ❌ | ❌ | ❌ |
| bash / ripgrep in-process | ✅（brush-shell + pi-natives） | ❌（fork-exec） | ❌ | ❌ |
| Provider 数 | 40+ | Anthropic 为主 | Google 为主 | 任意 OpenAI 兼容 |
| per-role 路由 | ✅（default/smol/slow/plan/commit） | ❌ | ❌ | ❌ |
| License | MIT | 商业 | Apache-2.0 | Apache-2.0 |

几个关键差异：

- **LSP rename**：Aider / Claude Code / Gemini CLI 的 rename 是 sed + 文本替换，**不知道** re-exports 和 barrel 文件的拓扑关系。oh-my-pi 调 `workspace/willRenameFiles`，TypeScript 项目的 import alias、barrel re-export、跨文件符号引用会**一次性**正确更新。
- **DAP 调试**：其他工具遇到 segfault 还是让 Agent 加 print。oh-my-pi 可以 attach lldb-dap 到二进制、设断点、单步、读 frame 变量。
- **In-process bash**：`brush-shell` 是 vendored 的 Rust bash 实现，session 状态跨多次调用保留；其他工具每条命令 fork 一个新 bash 进程，环境变量、alias、`cd` 状态全部丢失。
- **APFS 隔离**：`pi-iso` 在 macOS 上用 `clonefile(2)`，在 Linux 上用 btrfs/zfs reflink，几乎零成本地给每个 subagent 一份独立 worktree；其他工具共用工作区，subagent 之间会互相踩。

代价是 oh-my-pi 的 monorepo 体积大、首次安装需要 bun ≥ 1.3.14、定制 provider 要写 YAML。但对**长任务**（多文件重构、debug session、subagent fan-out）来说，这些代价换回的是模型不用反复重打原文、不用反复 read 验证环境、不用 fork-exec 等 bash 启动。

## Rust 内核

`packages/natives` 是一个 N-API addon，把 4 个 Rust crate 暴露给 Node。各模块的 LoC 分布（来自 README 的 per-module breakdown，**不含** glue 和 tests）：

| 模块 | LoC | 功能 | 底层库 |
|------|----:|------|--------|
| shell | 3,700 | embedded bash + 持久 session + timeout/abort + custom builtins | brush-shell（vendored） |
| grep | 1,900 | regex 搜索 + 并行/串行 + glob/type 过滤 + fuzzy | grep-regex · grep-searcher |
| keys | 1,490 | Kitty 键盘协议 + xterm fallback + PHF 完美哈希 | phf |
| text | 1,450 | ANSI-aware 宽度 + 截断 + 列切片 + SGR wrap | unicode-width · segmentation |
| summary | 1,040 | tree-sitter 结构化源码摘要 + elision | tree-sitter · ast-grep-core |
| ast | 1,000 | ast-grep 模式匹配 + 结构化改写 | ast-grep-core |
| fs_cache | 840 | mtime-keyed 文件缓存，read/grep/lsp 共享 | in-tree |
| highlight | 470 | 语法高亮 + 11 语义类别 + 30+ aliases | syntect |
| pty | 455 | sudo / ssh 交互式 prompt 的 PTY | portable-pty |
| glob | 410 | glob 发现 + type 过滤 + mtime 排序 + gitignore | ignore · globset |
| workspace | 385 | gitignore + AGENTS.md 单 pass 扫描 | ignore |
| appearance | 270 | Mode 2031 + macOS dark/light（CoreFoundation FFI） | core-foundation |
| power | 270 | macOS power-assertion（IOKit FFI） | IOKit FFI |
| task | 260 | libuv 线程池 + cancellation + timeout + profiling | tokio · napi |
| fd | 250 | find 工具的 fs walker | ignore |
| iso | 245 | 工作区隔离（APFS/btrfs/zfs/overlayfs/projfs/rcopy） | pi-iso（PAL） |
| prof | 240 | 环形 buffer profiler + folded-stack + SVG 火焰图 | inferno |
| ps | 195 | 跨平台进程树 kill + 后代列举 | libc · libproc · CreateToolhelp32Snapshot |
| clipboard | 80 | 系统剪贴板 + image read（无 xclip/pbcopy） | arboard |
| tokens | 65 | O200k / Cl100k BPE token 计数（两表内嵌） | tiktoken-rs |
| sixel | 55 | 终端图像渲染（PNG/JPEG/WebP/GIF → SIXEL） | icy_sixel · image |
| html | 50 | HTML → Markdown（可选内容清理） | html-to-markdown-rs |

几个值得注意的设计选择：

- **shell 用 brush 而非 tokio::process**：bash 是图灵完备的，写一个完整 bash 实现比"调外部 bash"更可控，session 状态可以序列化/反序列化（持久 session）
- **tokens 用 tiktoken-rs 内嵌表**：避免每次调 OpenAI 编码前 fork Python；O200k 和 Cl100k 都是 ~1MB 体积，常驻即可
- **iso 用 PAL（Platform Abstraction Layer）**：macOS APFS clone、Linux btrfs/zfs reflink、container overlayfs、WSL projfs 各自走不同系统调用，但接口统一
- **sixel 内置**：TUI 可以直接在终端里渲染截图（用 `imgcat` 风格），不需要切换到外部 viewer
- **phf 完美哈希**：`keys` 模块编译时生成 O(1) 查表，键盘事件 0 间接跳转

平台编译目标：linux-x64、linux-arm64、darwin-x64、darwin-arm64、win32-x64——同一个 omp 二进制在三大主流平台跑，**不依赖**用户机器上有 rg/grep/find/bash。

## 工作流特性

hashline 是底座，oh-my-pi 在它之上构建了几个长任务关键能力：

### 10.1 Time-traveling stream rules

规则平时 dormant，模型输出流里一旦匹配某 regex（比如 `Box::leak`），流**立即**在 token 级 abort，把规则作为 system reminder 注入，让模型从**同一位置**重试。规则 injection 跨 compact 存活，下次同一规则触发时不用重学。

README 给的演示：模型准备 `Box::leak`，流 abort + 注入"不要在 production code 路径里用 Box::leak"，模型重新生成时改用 `Arc<str>` 并问用户确认。

### 10.2 /advisor：第二双眼睛

`/advisor <model>` 配一个 review 模型（比如 openai-codex/gpt-5.5）作为 advisor，advisor 在自己的 context、自己的 model 上读主 Agent 的每一轮，注入 inline 备注（concern、aside、blocker 三档）。主 Agent 看到备注就 course-correct，或者解释为什么不改。

这是 "reviewer model 跟 doer model 解耦" 的实现——做事的模型不被 review prompt 污染上下文。

### 10.3 /collab：会发链接的 terminal session

`/collab` 把 live session 挂到本地 relay，发回 `omp join <id>` 命令 + my.omp.sh 链接 + QR 码。队友 `omp join` 从另一台 terminal 接入，或者浏览器打开链接 watch-only（read-only）/ pair（read-write）。Frame 在 client 端加密，relay 看不到内容。

### 10.4 /review：P0–P3 优先级 + verdict

`/review` 起 reviewer subagent 在 branch / single commit / uncommitted work 上并行扫，每个 subagent 输出 schema-validated 对象（issue + priority + confidence），主 Agent 聚合出 P0–P3 排序的清单 + 一句 verdict："ships / ships with fixes / blocks"。

### 10.5 Hindsight：项目级长期记忆

`retain` 写事实，`recall` 拉原始记忆，`reflect` 让 Hindsight 合成答案。每个项目独立 memory bank——A 项目学到的不会污染 B 项目。Session 结束时 compact 成 mental model，下次该项目的第一次 turn 自动加载。

### 10.6 ACP / RPC / SDK 四种接入

- `omp` —— TUI
- `omp -p` —— 单次 prompt 即退出
- `@oh-my-pi/pi-coding-agent` —— Node SDK，session 发出 typed event
- `omp --mode rpc` —— NDJSON over stdio
- `omp acp` —— JSON-RPC over Agent Client Protocol（Zed 等编辑器驱动）

`read pr://can1357/oh-my-pi/1063` 跟 `read src/foo.ts` 返回相同 shape——PR、issue、subagent findings、conflict、skill、rule 都是统一 `://` 协议名空间。`agent://<id>/findings.0.path` 直接按 path 拉 subagent 输出的某个字段。

## 适用场景与边界

### 11.1 适合 oh-my-pi 的场景

- **多文件长任务**：跨 5+ 文件的重构、debug session、workspace 级别的搜索替换
- **需要 LSP/DAP 的语言项目**：TypeScript / Rust / Go / C++ 项目，rename 引用、attach debugger 是日常
- **强 harness 需求**：你想要 advisor、time-traveling rules、Hindsight memory、APFS-isolated subagent
- **多 provider 切换**：不同任务用不同模型（planner 用 Opus、smol subagent 用 Haiku、reviewer 用 GPT-5.5）
- **本地 + 浏览器混合**：让 Agent 读 PDF、读 arxiv、读 GitHub PR、点网页、跑 headless browser
- **Windows 不可绕过**：oh-my-pi 在 Windows 上原生跑（`win32-x64`），其他工具普遍依赖 WSL

### 11.2 不适合 oh-my-pi 的场景

- **想要 IDE 原生体验**：用 Zed（ACP）能拿到 in-editor 体验，但和 Cursor / Windsurf 那种 "left side editor + right side chat" 比还是 terminal first
- **完全零配置**：oh-my-pi 安装需要 bun ≥ 1.3.14，macOS / Linux / Windows 各有不同 install script，商用开箱度不如 Claude Code
- **团队希望保持 Anthropic-only**：oh-my-pi 40+ provider 全开放，模型混用需要 per-role 路由 + fallback chain 配置
- **轻量小项目**：一个 200 行的 Python script，str_replace 足够，hashline + 32 工具的复杂度过剩
- **需要云端托管**：oh-my-pi 是本地 CLI，没有 hosted 版；云端体验请用 Claude Code / Cursor

### 11.3 选型决策矩阵

| 需求 | 首选 | 次选 |
|------|------|------|
| 长任务 + 多文件 + 强 harness | oh-my-pi | Claude Code（claude-code-harness） |
| 强 IDE 集成 + 云端 | Cursor | Windsurf |
| 终端 + 多 provider + 跨平台 | oh-my-pi | Aider |
| 学术 / 一次性 script | Claude Code / Gemini CLI | Aider |
| 企业 Claude 锁定 | Claude Code | oh-my-pi（Anthropic oauth） |
| 想要真实 LSP rename / DAP | oh-my-pi | 直接用 Cursor |

## 自测清单

- 说出 hashline 的 `[PATH#TAG]` 中 TAG 的生成方式和 4-hex 限制
- 解释为什么 `SWAP N.=M` 必须包含两端，且 body 不允许 `-old` 行
- 描述 stale tag 拒绝和 session-aware 3-way recovery 的触发条件
- 列出 oh-my-pi 的 4 层架构（交互 / 编排 / 工具 / 内核），说出每层至少一个包
- 解释为什么 hashline 让 Grok Code Fast 1 从 6.7% 跳到 68.3%
- 对比 oh-my-pi 与 Claude Code / Aider 在 LSP rename 和 DAP 上的差异
- 说出 pi-natives 的 shell 模块用的是哪个 vendored bash 实现
- 解释 time-traveling stream rules 与普通 system prompt 注入的区别

---

## 进阶路径

跑通基础用法后，下面三个方向值得深入，按收益和难度排序。

### 方向一：hashline 算法深入

- 阅读 [hashline README](https://github.com/can1357/oh-my-pi/blob/main/packages/hashline/README.md)，理解 `SnapshotStore` 的 mint 与销毁逻辑
- 深入研究 `Patcher` 的 apply 逻辑：如何验证 tag、如何执行 SWAP/INS/DEL 操作
- 对比 str_replace 与 hashline 的失败模式差异
- 进阶：理解 tree-sitter 如何解析闭区间、如何与 hashline 协作

### 方向二：贡献到 oh-my-pi 项目

- 从 [GitHub 仓库](https://github.com/can1357/oh-my-pi) 克隆代码
- 阅读贡献指南（如果有）
- 从简单 issue 开始：修复文档错误、添加单元测试、优化错误处理
- 理解代码结构：14 个 npm 包 + 6 个 Rust crate

### 方向三：将 omp 集成到生产环境

- 评估需求：长任务、多文件、需要 LSP/DAP、多 provider 切换
- 测试稳定性：在实际项目中运行 omp，记录崩溃、内存泄漏、性能瓶颈
- 集成到开发流：配置 per-role 路由、设置 advisor、配置 Hindsight memory
- 监控性能：关注 token 消耗、pass rate、retry 次数

### 方向四：开发自定义工具

- 理解 tool harness 的扩展机制
- 开发自定义工具：继承 `BaseTool`，实现 `execute` 方法
- 将自定义工具集成到 omp：修改 `packages/agent/` 中的工具注册逻辑
- 测试自定义工具：确保 hashline 编辑与自定义工具协同工作

### 方向五：探索高级功能

- **Time-traveling rules**：配置 stream 级别的规则注入
- **Advisor**：配置 review 模型，提供 inline 备注
- **Collab**：启动 collaborative session，邀请队友加入
- **Review**：配置 P0-P3 优先级，自动化代码审查

---

## 常见问题

### oh-my-pi 与 Claude Code 有什么区别？

Claude Code 使用 str_replace 格式，模型必须重打原文；oh-my-pi 使用 hashline 格式，模型只需要指定行号。根据基准数据，hashline 让 Grok Code Fast 1 的 pass rate 从 6.7% 跳到 68.3%。

### oh-my-pi 的学习曲线如何？

oh-my-pi 的概念较多（hashline、tool harness、LSP/DAP、Rust 内核），学习曲线中等。建议先通过 `omp` 命令行体验基本用法，然后逐步深入工具编排层和 Rust 内核。

### 生产环境使用 oh-my-pi 需要注意什么？

需要注意：
1. **模型成本**：oh-my-pi 支持 40+ 模型 provider，但每个模型的定价不同
2. **性能监控**：需要监控 token 消耗、pass rate、retry 次数
3. **错误处理**：hashline 在 stale tag 时会拒绝 patch，需要确保模型正确处理错误
4. **团队采用**：建议先在小范围团队内试用，再逐步推广

### oh-my-pi 的许可证是什么？

MIT License。可以免费用于商业项目。

### 如何获取 oh-my-pi 的技术支持？

- 阅读 [oh-my-pi 文档](https://omp.sh)
- 在 [GitHub 仓库](https://github.com/can1357/oh-my-pi) 提交 issue
- 加入 Discord 社区（如果有）

---

## 参考链接

- [oh-my-pi GitHub](https://github.com/can1357/oh-my-pi) —— 主仓库
- [omp.sh](https://omp.sh) —— 项目主页 + TUI 截图 / 视频
- [@oh-my-pi/hashline README](https://github.com/can1357/oh-my-pi/blob/main/packages/hashline/README.md) —— hashline 算法 + 快速上手
- [hashline grammar.lark](https://github.com/can1357/oh-my-pi/blob/main/packages/hashline/src/grammar.lark) —— 形式语法
- [hashline prompt.md](https://github.com/can1357/oh-my-pi/blob/main/packages/hashline/src/prompt.md) —— 模型侧 prompt 设计
- [The Harness Problem](https://blog.can.ac/2026/02/12/the-harness-problem/) —— hashline 启用的基准数据
- [pi-mono](https://github.com/badlogic/pi-mono) —— oh-my-pi fork 的源项目
- [brush-shell](https://github.com/reubeno/brush) —— vendored 的 Rust bash 实现
- [Agent Client Protocol](https://github.com/zed-industries/agent-client-protocol) —— `omp acp` 用的协议
