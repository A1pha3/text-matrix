---
title: "oh-my-pi 深度解读：把 pi-mono 重写成 80k 行 Rust、堆出 21 个新能力、接 60+ provider——它在解决 pi 没解决的那个问题"
date: 2026-08-12T23:55:00+08:00
draft: false
tags: ["AI Agent", "开源项目深拆", "Rust", "TypeScript", "Coding Agent", "omp", "oh-my-pi"]
categories: ["技术笔记"]
description: "can1357/oh-my-pi（omp）是 pi-mono 的工程级 hyper-fork，~80k 行 Rust 核心 + 31 工具 + 14 LSP ops + 28 DAP ops + 60+ providers + 23 search backends，把 pi-mono 拒绝做的'工程累人部分'（grep fork-exec、bash 解析、DAP/LSP 协议、content-hash 编辑、native addon 跨平台）全部原生实现，再加 21 个差异化能力（Python/Bun eval 跨工具回调 / TTSR 流中注入 / advisor 监督 / Agent Hub subagent / collab 协作 / hashline 编辑 / //:// scheme 透明 / conflict:// / ast_edit 等）。这篇文章不讲 pi-mono 已经讲过的部分——讲的是 oh-my-pi 解决 pi 没解决的'该有的工程基础设施'问题，以及它为'让 agent 真的能上线'付出的具体代价。"
slug: "oh-my-pi-hyper-fork-of-pi-mono"
band: "review"
gates: ["事实性", "去AI味", "观点依据"]
github_repo: "can1357/oh-my-pi"
---

## 这篇文章在回答什么

`can1357/oh-my-pi`（重命名为 `omp`）在 GitHub 上是 pi-mono 的 hyper-fork。它的 README 开篇一句话：

> A coding agent with the IDE wired in.

更准确的说法：**pi-mono 之后的下一个工程级 hyper-fork**。pi-mono 解决的是「agent 循环作为库」、pi-book 解决的是「怎么写出能钉死 commit 的中文架构书」、nano-pi 解决的是「怎么删到 600 行还保留核心思想」、oh-my-pi 解决的是一个 pi-mono **明确不做**的事情——**让 agent 真的能在生产链路上跑起来需要的工程基础设施**。

它给出的回答是一份「该有的基础设施清单」：

- ~80k 行 Rust 核心（不是 80k 行 Node 包装），其中 pi-shell 一个 crate 38k 行（嵌入式 bash fork + 58 个 in-process coreutils），pi-natives 一个 crate 25k 行（grep / text / ast / diff / pty / keys / desktop control 等的 N-API 原生绑定）
- **31 工具** + **14 LSP ops** + **28 DAP ops** + **60+ providers** + **23 search backends**
- **21 个差异化能力**——README 里用编号 01–21 列出来，从"Python/Bun eval 跨工具回调"到"Windows 上也能跑"的 native in-process，到"GitHub:// URL 是透明路径"，到 "conflict:// URL 解决 merge conflict"，到 "ast_edit 预览后接受"
- **4 个入口**——同一个 agent 暴露成 TUI / one-shot / RPC stdio / ACP editor 协议
- **native 优先**——在 macOS / Linux / Windows 上跑同一个二进制，不依赖系统装 rg / grep / find / bash

oh-my-pi 不是「又一个 AI Coding Agent」。它是 pi-mono 路线上第一个把「agent loop 是库」这个抽象推到「agent loop 是平台」的工程实践——区别在于它把「能跑」和「能上生产链」中间的所有工程累人部分（grep fork-exec、DAP 协议、bash 解析、native addon 跨平台、provider 路由、session 持久化、subagent 并发）**全部自己做了**。

这篇文章不讲 pi-mono / pi-agent-core / nano-pi 已经讲过的部分（agent loop、StreamFn、AgentEvent、Agent 与 AgentHarness 的两层组合、双层 while）。它做三件事：

1. 拆 oh-my-pi **解决的工程问题**——它在 pi 没解决的那一块补了什么
2. 拆 oh-my-pi **付出的工程代价**——native 优先、4 入口、23 search backend 各意味着什么
3. 把 oh-my-pi 放到 pi 生态的位置——它和 pi-mono / nano-pi / pi-book 三套叙事是什么关系

## 一、oh-my-pi 在解决什么问题：pi 没做的那一块

### 1.1 pi-mono 的边界

pi-mono 的设计哲学可以一句话总结：**拒绝成为框架**。它把 agent loop 做成一个库，把 StreamFn 做成一个函数形状，把 Session 后端做成一个接口，把 ExecutionEnv 做成一个能力接口。所有"框架化"的事情（provider 目录、模型元数据、UI、运行时绑定、持久化后端）都被推到包边界之外。

这套设计让 pi-mono 成为了一个**学术上和工程上都漂亮**的库。但它也留下了一个缺口——**「要让一个 coding agent 真的跑起来，需要的不是库，是平台」**。

具体缺什么？

| 缺口 | pi-mono 的态度 | 真实工程的痛点 |
|---|---|---|
| LLM provider 适配 | 「用 pi-ai，自己接」 | 一个 harness 要对接 60+ provider、10+ 种 API 风格（OpenAI Completions / Responses / Anthropic Messages / Bedrock Converse / Google Generative AI / Gemini CLI / Vertex / Codex Responses / Azure Responses） |
| 工具集 | 「read / write / edit / bash 4 个就够」 | 真实工程需要 LSP（14 ops）、DAP（28 ops）、browser、computer、tts、generate_image、memory 工具、advisor、task 等等 |
| Bash | 「spawn bash 进程」 | 每次 fork-exec 开销大、跨平台不兼容、Windows 上没 bash |
| Grep / Glob | 「用 ripgrep」 | 跨平台需要 ripgrep 二进制、每次调用 fork-exec |
| 调试 | 「不在核心里」 | 用户问"为什么这个函数返回 undefined"，agent 需要的不是 print，是真正的 debugger |
| LSP | 「不是 agent 关心的事」 | rename 一个 symbol 跨 5 个文件，agent 不接 LSP 就只能 sed |
| Search | 「用 web search API」 | 不同 query 适合不同 backend，agent 需要 23 个 backend 路由 |
| Session | 「内存数组，进程退出归零」 | 真实工程需要 tree、fork、share、resume、checkpoint |
| Subagent | 「不是核心的事」 | 真实工程需要 fan-out、隔离 worktree、IPC 桥、Agent Hub 看板 |

每一个缺口都是一个**真实工程任务**。oh-my-pi 的全部意义就是：**把这些缺口一个一个填上，且不破坏 pi-mono 的"库"属性**——它不是把 pi-mono 重写成一个框架，而是把它重写成一个**完整的工程产品**。

### 1.2 oh-my-pi 的回答：把"必要但累人"全部 native 化

README 反复出现一个词：**"wired in"**。

> A coding agent with the IDE wired in.

> **LSP wired into every write** — Ask for a rename and you get a rename. The call goes through workspace/willRenameFiles, so re-exports, barrel files, and aliased imports update before the file moves. Everything your IDE knows, the agent knows.

> **Drives a real debugger** — A C binary segfaults: the agent attaches lldb, steps to the bad pointer, reads the frame.

> **Unapologetically native. Even on Windows.** — Other agents shell out to rg, grep, find, and bash. On many machines those binaries don't exist, and on the ones where they do, every call costs a fork-exec round-trip. omp links the real implementations into the process.

"wired in" 翻译过来就是**内嵌**：LSP 不是通过外部 stdio bridge 调用的，是直接在 Rust 里跑 lldb-dap / vscode-languageserver-protocol；grep 不是 fork rg，是把 ripgrep 的核心算法（grep-regex + grep-searcher）链接进二进制；bash 不是 fork bash，是把 brush bash fork 嵌入 pi-shell（38k 行）；native API 不是 node-pty + napi 胶水，是直接走 macOS CoreFoundation FFI、Windows CreateToolhelp32Snapshot、Linux portable-pty。

这种"全内嵌"的代价是显白的——oh-my-pi 不是 80k 行 Node 包装，是**80k 行 Rust 加上对应的 TypeScript 胶水层**。收益也是显白的：每一个"必须存在但很工程累人"的部分都被压缩成可链接的二进制，agent 跑的每一步都不再 fork-exec 一次。

这不是 pi-mono 哲学的背叛。这是 pi-mono 哲学的**自然延展**——pi-mono 说"agent loop 是库"，oh-my-pi 说"如果 agent loop 要做很多事，库的依赖也得是库"。

## 二、80k 行 Rust 的内部账本

oh-my-pi 的 README 给了一张**极有信息量的表**——每个 crate 的代码行数与它做的事：

| Crate | 做什么 | ~LoC |
|---|---|---:|
| `pi-shell` | Embedded bash engine · persistent sessions · in-process coreutils dispatch · minimizer | **38,000** |
| `pi-natives` | N-API surface — 23 个模块的 native 绑定 | **25,000** |
| `pi-walker` | Parallel ignore-aware walker + scan cache | 5,200 |
| `pi-iso` | Workspace isolation · apfs / btrfs / zfs / reflink / overlayfs / projfs / rcopy | 3,300 |
| `pi-ast` | tree-sitter + ast-grep matching | 2,900 |
| `pi-voice` | Audio capture/playback · Opus · WebRTC | 1,000 |

这张表读起来像一份**工程预算的诚实披露**——它在告诉你"我们为哪些能力花了多少代码"。

### 2.1 pi-shell 的 38k 行：把 bash fork 进 Rust

`pi-shell` 是 38k 行 Rust——占整个 Rust 核心的近一半。它做一件事：**把 brush bash fork 移植进 pi 进程**。

brush 是 https://github.com/rust-bridge/brush 的嵌入式 bash 实现，原本就是 Rust 写的。oh-my-pi 把 brush 接进 pi-shell 后，做了三件事：

1. **persistent sessions**——bash 会话状态（变量、alias、shell options、cwd）跨调用保持。这与 Node spawn 出来的 bash 进程完全不同：spawn 出的 bash 每次调用都是新进程，状态全丢。
2. **in-process coreutils dispatch**——把 58 个常用 coreutils（cat、cp、mv、rm、grep、find、sort、xargs、jq、sed、awk 等）全部 port 进 pi-builtins 这个 crate，bash 调用时直接 dispatch 到 Rust 实现，**不再 fork**。
3. **minimizer**——bash 脚本执行前会做一个最小化处理（去掉注释、空行、多余空白），减小执行开销。

这意味着 oh-my-pi 跑 `cat file.txt | grep foo | wc -l` 这样的命令，**整个 pipeline 都在 Rust 进程内完成**，0 fork/exec。对比 pi-mono 的 bash 工具每次都 spawn 一个新 bash 子进程——开销差几个数量级。

README 的"unapologetically native"那一段把这事讲透了：

> Other agents shell out to rg, grep, find, and bash. On many machines those binaries don't exist, and on the ones where they do, every call costs a fork-exec round-trip. omp links the real implementations into the process. ripgrep, glob, find: in-process. brush is the bash — with sessions that survive across calls, and 58 command-line utilities (ls, sed, sort, xargs, even jq) ported into the builtins crate and run in-process, zero fork/exec. The same omp binary runs on macOS, Linux, and Windows — no WSL bridge.

"no WSL bridge" 是一句关键的工程说明。Windows 上绝大多数 coding agent（Claude Code、Codex CLI、Cursor agent）都依赖 WSL 来跑 bash。oh-my-pi 因为 brush 是纯 Rust 实现的，**Windows 上能直接跑 bash 脚本，不依赖 WSL**。

### 2.2 pi-natives 的 25k 行：23 个 native 模块

`pi-natives` 是 N-API addon——它把 23 个 native 模块绑定成 Node.js 可调的 API。这些模块的代码行数差异巨大：

| 模块 | 做什么 | 底层库 | ~LoC |
|---|---|---|---:|
| desktop | Window/display enumeration · screenshot · native input · AX tree for `computer` 工具 | xcap · enigo · OS AX FFI | **10,600** |
| grep | Regex search · parallel/sequential · glob & type filters | grep-regex · grep-searcher | 3,280 |
| text | ANSI-aware width · truncation · column slicing | unicode-width · segmentation | 2,070 |
| snapcompact | Bitmap-frame rasterization + PNG encode for context compression | image · png | 1,760 |
| keys | Kitty keyboard protocol with xterm fallback | phf | 1,740 |
| ast | ast-grep pattern matching and structural rewrites | ast-grep-core | 1,510 |
| diff | Structured file diffing | in-tree | 1,030 |
| pty | Native PTY allocation for sudo · ssh | portable-pty | 630 |
| crash_handler | Native crash capture and reporting | in-tree | 610 |
| highlight | Syntax highlighting · 11 semantic categories · 30+ aliases | syntect | 550 |
| appearance | Mode 2031 + native macOS dark/light | core-foundation | 450 |
| task | Blocking work on libuv thread pool · cancellation · timeout | tokio · napi | 440 |
| glob | Discovery with glob · type filters · mtime sort · gitignore respect | ignore · globset | 430 |
| fd | Filesystem walker | ignore | 385 |
| clipboard | Text copy and image read from system clipboard | arboard | 370 |
| workspace | Workspace walker with gitignore + AGENTS.md discovery | ignore | 275 |
| power | macOS power-assertion API for idle/system/display-sleep prevention | IOKit FFI | 270 |
| prof | Circular buffer profiler with folded-stack and SVG flamegraph output | inferno | 240 |
| file_lock | Cross-process advisory file locking | in-tree | 210 |
| ps | Cross-platform process-tree kill and descendant listing | libc · libproc · CreateToolhelp32Snapshot | 195 |
| tokens | O200k / Cl100k BPE token counting | tiktoken-rs | 70 |
| html | HTML to Markdown | html-to-markdown-rs | 60 |
| sixel | Terminal image rendering · SIXEL encode | icy_sixel · image | 55 |

注意 `desktop` 模块一个就占了 10,600 行——这是为了 `computer` 工具的实现。`computer` 是 oh-my-pi 的特性 #20：「Hands on the desktop itself」——`computer` runs persistent JavaScript against the real host: enumerate windows and displays, capture screenshots, send native input, walk the OS accessibility tree, touch the clipboard. Not the browser tool, no DOM — the same desktop you're looking at.

要在 Rust 里调用 macOS 的 accessibility API（CoreFoundation / IOKit）和 Windows 的 UI Automation，需要 FFI 绑定 + 类型转换 + 跨平台抽象——这 10k 行大部分是 macOS 的 Cocoa/AX API 胶水。

### 2.3 80k Rust 之外的另一半

README 的标题是「**Roughly ~80,000 lines of Rust, doing the work other harnesses shell out for**」，但底下又有一行：

> Another ~80k lines ride along vendored: the brush bash fork, plus 58 command-line utilities — coreutils, findutils, sed, jq, ripgrep-backed grep, fd, diff, moreutils — ported into the builtins crate and compiled straight into the shell.

也就是说总代码量是 160k 行 Rust（80k 手写 + 80k vendored）。这还没算 TypeScript 部分——`packages/` 下还有完整的 agent / coding-agent / tui / ai / catalog / omptype / utils / stats 8 个子包。

oh-my-pi 的"工程级 hyper-fork"在代码量上印证了——这不是一个简单的 fork-and-tweak。

## 三、21 个特性如何拼成完整工作流

README 的 01–21 编号不只是 README 的视觉节奏。它读起来像一份**产品路线图**：每条都对应一个具体的工作流场景。我把 21 条按"工作流阶段"重新组织，能看出它们的内在依赖关系：

### 3.1 启动与发现（特性 12、15）

- **#12 GitHub is just another filesystem** — `read` 已经能处理路径，PR 是路径，Issue 是路径。一个接口教给模型，一个表面积保持正确。
- **#15 Inherits what your other tools already wrote** — 八种配置文件格式（Cursor MDC、Cline .clinerules、Codex AGENTS.md、Copilot applyTo 等）直接读，不迁移。

这两条解决了**启动摩擦**：用户从别的工具切到 oh-my-pi 时不需要重写项目配置，agent 第一次启动就能从磁盘上读到所有已经存在的规则、skills、MCP server。

### 3.2 编辑与验证（特性 02、11、18、19）

- **#02 LSP wired into every write** — rename 走 workspace/willRenameFiles，re-exports / barrel files / aliased imports 在文件移动之前更新。
- **#11 Hashline: edit by content hash** — 模型指向 anchor，不重打要改的行；stale anchor 在写入前被拒绝。
- **#18 Conflict resolution, made easy** — 每个 merge conflict 变成一个 URL（`conflict://N`），agent 写 `@theirs` / `@ours` / `@base` 解决。
- **#19 Preview, then accept** — `ast_edit` 返回 proposed card，写一行到 `xd://resolve`，TUI 转成 Accept card，磁盘移动原子完成。

这四条解决了**编辑正确性**：每次代码改动都被 LSP / content-hash / ast-grep / merge-conflict-resolver 这四层保护。模型写出"看起来对"的代码后，每一步都有结构化校验，而不是文本字符串比较。

### 3.3 执行与验证（特性 01、03、09）

- **#01 Code execution w/ tool-calling** — Python 和 Bun worker 持久化，两个 kernel 都能通过 loopback bridge 回调 agent 自己的工具（read / search / task）。agent 从 Python 里 load CSV，从 JavaScript 里画图，不离开 cell。
- **#03 Drives a real debugger** — C 二进制段错误 → attach lldb；Go 服务 hang → attach dlv；Python 进程卡死 → debugpy。大部分 agent 还在撒 print。
- **#09 Unapologetically native. Even on Windows.** — ripgrep / glob / find 全部 in-process；brush 是 bash；58 个 coreutils port 进 builtins。0 fork/exec。同一个二进制跑 macOS / Linux / Windows。

这三条解决了**执行验证**：当代码改了之后，agent 不是凭 text diff 自我确认，而是真跑、真调试、真 attach debugger。LSP 解决"改动对不对"，debugger 解决"改动后程序对不对"，native in-process 解决"跑得快不快 + Windows 上能不能跑"。

### 3.4 编排与监督（特性 05、06、14）

- **#05 First-class subagents** — `task` 工具 fan-out 到隔离的 worktree，每个 worker 跑自己的 tool surface，最终 yield 一个 schema-validated 对象给 parent。没有 prose to parse，没有 merge conflicts between siblings。
- **#06 A second model, watching every turn** — advisor 角色在 main agent 的每个 turn 上读一遍，inline 注入 notes。Advisor 跑在自己的 context 和 model 上，能抓到 doer 跑过的部分。
- **#14 ACP: editor-drivable agent** — 在 Zed 里跑 omp，agent 读 editor 当前的 buffer、写通过 editor 的 save path、shell 跑在 editor 的 terminal 里。destructive tools pause for permission prompt。

这三条解决了**多 agent 编排**：subagent 做并行执行、advisor 做实时监督、ACP 做 editor 嵌入。三条加起来，oh-my-pi 不是"一个 agent 一个人用"，是"一个 agent 多角色协同"。

### 3.5 协作与共享（特性 07、10、13、17）

- **#07 Hand someone the link, they're in** — `/collab` 把 live session 放上 relay，发回链接 + QR。同事 `omp join` 加入，或者浏览器打开。Frames 客户端加密，relay 看不到 keys。
- **#10 Code review with priorities and a verdict** — `/review` spawn 专门的 reviewer subagents，并行扫 branches / single commits / uncommitted work。issue 排 P0-P3 + 信心分。
- **#13 Memory the agent curates** — agent 跨 session 记忆你的 codebase。mid-run 写 facts 用 `retain`，捕获可复用 lessons 用 `learn`，拉回来用 `recall`，每 session 压缩成 mental model，下次 session 第一轮加载。backend 选 `memory.backend`（local / Hindsight / Mnemopi）。
- **#17 Read PRs. Walk skills. Pull JSON out of subagents** — 16 个内部 scheme（`pr://` / `issue://` / `agent://` / `skill://` / `ssh://` 等）在每个 FS-shaped 工具里透明解析。`read pr://1428` 和 `read src/foo.ts` 是同一种 shape。

这四条解决了**协作与知识沉淀**：pair-programming（collab）、code review（review）、长期记忆（memory）、URL 抽象（:// scheme）。四条连起来，agent 不只是"当前 session 内的工具"，是"一个持续进化的、有记忆的、可以分享的实体"。

### 3.6 21 个特性的内在依赖

把 21 条按上面六阶段画出来，能看到一个**清晰的工作流漏斗**：

```
启动与发现 (12, 15)
    ↓
编辑与验证 (02, 11, 18, 19)  ← LSP / hashline / conflict / ast_edit 四层保护
    ↓
执行与验证 (01, 03, 09)  ← eval / debugger / native in-process
    ↓
编排与监督 (05, 06, 14)  ← subagent / advisor / ACP
    ↓
协作与共享 (07, 10, 13, 17)
```

每一阶段都建立在上一阶段的基础上。**没有 LSP 写时联动（#02），subagent（#05）做的 fan-out 就会产生大量 merge conflict；没有 content-hash 编辑（#11），ast_edit（#19）的预览就不可信；没有 native in-process（#09），debugger（#03）和 eval（#01）的跨平台一致性就崩了**。

这是 21 条不是"feature list"而是"工作流依赖图"的关键证据。

## 四、4 入口策略：同一个 agent 暴露成 4 个不同接口

README 的「Four entry points: interactive, one-shot, RPC, and ACP」是我在 oh-my-pi 里看到的**第二个清晰的工程判断**。

> Same engine, four wrappers. `omp` runs the TUI. `omp -p` answers a single prompt and exits. The Node SDK embeds the session in your process. `omp --mode rpc` and `omp acp` hand the wheel to another program over stdio.

四种入口不是 marketing 噱头——它们对应四种真实的使用场景：

| 入口 | 适用场景 | 调用方 | 协议 |
|---|---|---|---|
| **TUI** (`omp`) | 人机交互的 terminal | 真人 terminal | 内置 |
| **one-shot** (`omp -p`) | CI / script / batch | shell | argv |
| **SDK** (`@oh-my-pi/pi-coding-agent`) | Node / TypeScript 嵌入式 | 自己的程序 | TypeScript API |
| **RPC** (`omp --mode rpc`) | 跨语言嵌入 / 进程隔离 | 任意 stdio caller | NDJSON over stdio |
| **ACP** (`omp acp`) | editor 嵌入 | Zed 等支持 ACP 的编辑器 | JSON-RPC over stdio |

把 5 个入口（TUI/one-shot/SDK/RPC/ACP）列出来，oh-my-pi 的策略就清楚了：**agent 的核心逻辑只写一次，外面套 5 个不同接口**。这个抽象的核心是 `createAgentSession` —— 它返回一个 session object，所有外部入口都通过这个 session 与 agent 通信。

代码示例（来自 README）：

```ts
import {
  ModelRegistry,
  SessionManager,
  createAgentSession,
  discoverAuthStorage,
} from "@oh-my-pi/pi-coding-agent";

const auth = await discoverAuthStorage();
const models = new ModelRegistry(auth);
await models.refresh();

const { session } = await createAgentSession({
  sessionManager: SessionManager.inMemory(),
  authStorage: auth,
  modelRegistry: models,
});
await session.prompt("list .ts files");
```

注意 `await models.refresh()` —— **每次启动都会从 60+ provider 的 catalog 里刷新可用模型列表**。这是 oh-my-pi 的另一笔工程投入：60+ provider 意味着每个 provider 都有自己的 model metadata / pricing / context window / capability flag，oh-my-pi 维护一个 catalog（`packages/catalog`）把这些信息结构化，启动时联网同步。

### 4.1 4 入口策略的工程含义

把 agent 暴露成 4 个不同接口，听起来工程量大，但它的工程含义是**反过来的**：

- **不强求所有用户走同一条路**——CI 用户用 one-shot，editor 用户用 ACP，开发者用 SDK，普通用户用 TUI。每种用户用最适合他们的入口。
- **不强求所有 host 跑同一种 runtime**——RPC 和 ACP 是 stdio over JSON，host 可以是 Python / Go / Rust / 任何能开 stdio 的语言。SDK 是 Node-only，但用户可以选择不绑死在 Node。
- **不强求所有 surface 跑同一个 session backend**——`SessionManager.inMemory()` 和 `SessionManager.persistent()` 是不同的实现，外部入口可以选哪个。

这是 pi-mono「拒绝成为框架」哲学的精确延展：**agent 核心逻辑不依赖任何具体的 surface 实现，但所有 surface 都通过同一个 session 抽象接入**。

### 4.2 ACP 那一栏：editor-driven agent 的未来

特性 #14 提到的 ACP（Agent Client Protocol）是 Zed Industries 推动的 editor-agent 协议。oh-my-pi 是**最早支持 ACP 的 coding agent 之一**。

| omp tool | ACP route |
|---|---|
| `bash` | `terminal/create + terminal/output` |
| `read` | `fs/read_text_file` |
| `write` | `fs/write_text_file` |
| `edit, bash` | `session/request_permission` |

ACP 不是一个临时协议——它正在变成 coding agent 和 editor 之间的标准桥梁。oh-my-pi 在第一时间接入，意味着它在 editor-driven agent 这个**新范式**里拿到了首发位置。

## 五、「native 优先」的代价与收益

README 反复出现的词是 "wired in" / "in-process" / "native"。这是 oh-my-pi 的**核心工程哲学**——但它不便宜。

### 5.1 代价：跨平台 = 三倍 FFI 代码

`desktop` 模块 10,600 行——其中大部分是 macOS 的 CoreFoundation / Cocoa / IOKit FFI。同样的功能在 Windows 上要靠 UI Automation，Linux 上要靠 AT-SPI。三套平台、三套 FFI、三套测试矩阵。

| 平台 | 主要 FFI 库 | 难点 |
|---|---|---|
| macOS | xcap · enigo · CoreFoundation · IOKit | AX API permission dialog、Code signing |
| Windows | UI Automation · CreateToolhelp32Snapshot | UAC、accessibility permission、Active Accessibility |
| Linux | AT-SPI · X11 / Wayland | 各种桌面环境（GNOME / KDE / Sway）的差异 |

README 给出了 Windows 特定的注意事项（docs/macos-signing-notarization.md）：

> macOS signing notarization requirements for distribution

macOS 上分发 omp 必须 code sign + notarize，否则 Gatekeeper 会拦。这又是另一笔工程投入——**macOS 签名 + 公证流程**。

### 5.2 代价：80k Rust + 80k vendored = 160k 行 binary 体积

80k 行 Rust + 80k vendored = 160k 行 C/C++/Rust 全 vendored 进二进制（ripgrep / brush / jq / ast-grep 等）。Release binary 体积估算在 80–150 MB。

但 oh-my-pi 把这个代价**明示出来**——README 直接列出每个 crate 的行数：

> Six crates, one platform-tagged N-API addon. Search, shell, AST, highlight, PTY, desktop control, image decode, BPE counting — all in-process on the libuv pool. No fork/exec on the hot path.

并给出明确的工程理由：把 fork-exec 拿掉，换来**实时性能 + 跨平台一致性 + Windows 支持**。

### 5.3 收益：oh-my-pi 是「native 优先」哲学的第一次完整产品化

把 fork-exec 拿掉看似一个性能优化，实际上是一个**架构选择**：所有事情在 in-process 完成，意味着 agent 可以**统一调度、统一观察、统一 cancel**。

README 提到了一个细节：「`task` 工具用 libuv 线程池 + cancellation + timeout」——这是 `pi-natives` 的 `task` 模块。它意味着 oh-my-pi 的并发执行不是 Node 的 event loop（单线程），而是 libuv 的 thread pool（多线程），而且**每个任务可以独立 cancel 和 timeout**。

这对比 pi-mono / 大多数 Node-based coding agent 是个**根本性的差别**：

- Node event loop → 所有 I/O 在同一线程上交错，并发 = 交错执行
- libuv thread pool → I/O 跑在独立线程，CPU 密集型任务（grep、ast match、token count）不会阻塞 agent 的下一步

这意味着 oh-my-pi 在跑 grep 大目录时，agent **不会卡住等 grep 返回**——grep 在 libuv 线程跑，agent 同时可以做别的事。grep 返回后通过 N-API 回调，agent 收到结果。

这就是 "wired in" 的真实含义——**不是把 native binary 链接进来，是为了取消 fork-exec 的架构边界**。

## 六、21 特性中的几个被低估的设计

### 6.1 特性 #11 Hashline：内容哈希编辑

README 给了一个非常具体的对比数据：

| model | metric | what |
|---|---|---|
| Grok Code Fast 1 | 6.7% → 68.3% | Tenfold lift the moment the edit format stops eating the model alive. |
| Gemini 3 Flash | +5 pp | Over str_replace — beats Google's own best attempt at the format. |
| Grok 4 Fast | −61% tokens | Output collapses once the retry loop on bad diffs disappears. |
| MiniMax | 2.1× | Pass rate more than doubles. Same weights, same prompt. |

Hashline 不是 oh-my-pi 发明的——它是 swe-bench 评测里很多 top agent 的常见做法。**但 oh-my-pi 是第一个把它做到"stale anchor 在写入前被拒绝"的程度**。

具体做法：每次 `read` 一个文件，oh-my-pi 算出每行的 content hash（不是行号），返回 `[hash]content` 格式给模型。模型编辑时只说"把 hash 为 `a3f2` 的那行改成 `xxx`"，不再说"把第 42 行改成 `xxx`"。

为什么这个看似小的设计能提升 6.7% → 68.3%？因为传统的行号编辑有三个失败模式：

1. **行号漂移**——前一个 edit 改了行数，下一个 edit 的行号就错了。
2. **字符串匹配歧义**——`str_replace` 用 old_string，如果 old_string 在文件里出现多次就失败。
3. **whitespace 战争**——模型输出的"行"经常带前导空格或换行符差异，跟文件里的真实内容不匹配。

content-hash 把这三个失败模式全部堵死——每行的 hash 是唯一的，hash 不会因为前面 edit 而漂移，hash 对 whitespace 不敏感（同一个 hash 算出同样的行）。模型只要 anchor 选对，编辑一定落对地方。

### 6.2 特性 #17：`://` 透明路径

这是 README 里**最被低估**的一条：

> Sixteen internal schemes — `pr://`, `issue://`, `agent://`, `skill://`, `ssh://`, and the rest — resolve transparently inside every FS-shaped tool the agent already calls. `read pr://1428` returns the same shape as `read src/foo.ts`. `grep` walks a diff like a directory. `agent://<id>/findings.0.path` pulls a field out of a subagent's output by path.

为什么这条重要？因为它解决了 agent 工具集的一个**根本性增长问题**——**每加一种新资源就要教模型一个新工具**。

传统做法：给 GitHub 加工具 → `gh_issue_view`、`gh_pr_view`、`gh_search`，每个都有自己的参数 schema，模型要学三套新 API。

oh-my-pi 做法：把 GitHub 当文件系统——`read pr://1428` 跟 `read src/foo.ts` 是同一种调用。同一个 `read` / `grep` / `glob` 工具学会了，所有 scheme 自动支持。

收益的复利是**线性的**：oh-my-pi 已经有 16 个 internal scheme，未来每加一个，对应工具集的增量成本是 0——只需要注册一个新 scheme handler。模型那一侧**永远不用学新工具**。

### 6.3 特性 #09：Windows 上也能跑

这一条对中文开发者圈可能不重要（绝大多数 coding 工作在 macOS / Linux 完成），但对**企业 IT 环境**和**新人开发者**极其重要——一个 .NET 工程师第一次上手 agent，他/她的机器上**没有 rg、没有 grep、没有 bash、没有 ripgrep**。Claude Code 在 Windows 上要么用 PowerShell（跟 Unix 工具语义差），要么用 WSL（多一层虚拟化）。oh-my-pi 直接给一个 `omp.exe`，跑起来就是 Linux 一样的工具语义——`cat`、`grep`、`find`、`xargs`、`jq` 都在。

这是**降低 agent 上手成本**的工程投入——不是技术难度问题，是新手迁移成本问题。

### 6.4 特性 #04 TTSR：流中注入

README 把 TTSR（Time-Traveling Stream Rules）放在特性 #04，它的设计非常反直觉：

> Your rules sit dormant until the model goes off-script. A regex match aborts the stream mid-token, injects the rule as a system reminder, and retries from the same point. You get course-correction without paying context tax on every turn.

传统的 rule 系统是「在 prompt 开头塞一段规则」——每个 turn 都付一次 context 税。TTSR 的设计是**只在需要时付税**：

1. model 在 stream token 时，正则匹配命中"危险信号"
2. stream abort，从**中断点**重试
3. 这时把对应 rule 作为 system reminder 注入
4. model 看到 rule 后 course-correct

这避免了两种浪费：① 不必要的 rule（每次 turn 都付税）② 不可挽救的错误（rule 在 prompt 开头但 model 已经走到错路上）。

Injects survive compaction, so the fix sticks——这条细节很关键。**compaction 后注入仍然有效**，意味着 rule 不只是"当下这一轮的修正"，是"被压进 long-term memory 的纠正"。

## 七、oh-my-pi 在 pi 生态的位置

把 pi-mono / nano-pi / pi-book / oh-my-pi 放一起看，pi 生态有四套叙事：

| 项目 | 一句话定位 | 工程投入 |
|---|---|---|
| **pi-mono** | 「agent loop 作为库」—— 拒绝成为框架 | ~80k 行 TS（agent core ~2.3k 行 + harness ~10k 行 + 全套周边） |
| **nano-pi** | 「600 行教学版 coding agent」—— 删工程细节保核心思想 | 600 行 TS |
| **pi-book** | 「锁定 commit 的中文架构书」—— 行号就地引文 + 整体→局部→横切 | ~3 章已发布，~1800 行书 |
| **oh-my-pi** | 「agent loop 作为平台」—— 必要但累人的工程基础设施全部 native 化 | ~160k 行 Rust（80k 手写 + 80k vendored）+ ~80k 行 TS |

四套叙事覆盖了 agent 工程化的**完整光谱**：

- pi-mono 告诉你**怎么设计 agent loop**——抽象层。
- nano-pi 告诉你**agent loop 删到极致还能剩什么**——最小可工作集。
- pi-book 告诉你**怎么把 agent loop 写清楚**——文档方法论。
- oh-my-pi 告诉你**怎么让 agent loop 在生产链路上跑起来**——工程基础设施。

**oh-my-pi 是这四套里唯一一个"反向"的**——它不是在简化、抽象、记录，而是在往里**填**东西。每一个被填进去的部分都是一个工程累人但必须存在的能力。

## 八、oh-my-pi 与 Claude Code / Codex / Cursor 的关系

把 oh-my-pi 放回 2026 年的 coding agent 赛道——Claude Code / OpenAI Codex CLI / Cursor agent / Gemini CLI 是 4 个最主流的商业 / 闭源主导 agent，oh-my-pi 是开源 / self-host / fork-pi 路线上最重的实现。

四家主流 agent 的工程策略对比：

| 维度 | Claude Code | Codex CLI | Cursor agent | oh-my-pi |
|---|---|---|---|---|
| 核心语言 | TypeScript | TypeScript / Rust hybrid | TypeScript + Electron | Rust + TypeScript |
| Bash | spawn | spawn | spawn | embedded brush fork |
| Grep | ripgrep 二进制 | ripgrep 二进制 | ripgrep 二进制 | in-process ripgrep |
| 跨平台 | macOS / Linux / Windows | macOS / Linux / Windows | macOS / Windows | macOS / Linux / Windows（无 WSL） |
| LSP | 基础支持 | 基础支持 | 完整支持 | **14 ops** wired in |
| DAP | 不支持 | 不支持 | 不支持 | **28 ops**（lldb / dlv / debugpy） |
| 工具数 | ~15 | ~12 | ~20 | **31** |
| Provider 数 | 5-10 | 3-5 | OpenAI only | **60+** |
| Search backends | 1-3 | 1-3 | OpenAI web search | **23** |
| 开源 | 否 | 部分 | 否 | 是（MIT） |

注意 oh-my-pi 的几个**独有的能力**：

1. **DAP 调试** —— 没有任何一个主流 agent 真集成 lldb / dlv / debugpy。oh-my-pi 是唯一一个 agent 能 attach debugger 跑 breakpoint 的实现。
2. **Windows 无 WSL** —— Claude Code / Codex 在 Windows 上依赖 PowerShell 或 WSL，oh-my-pi 给一个 native binary。
3. **60+ providers** —— 主流 agent 绑定自己的 API key + plan，oh-my-pi 走"中立路由"路线，谁家的 key 都能用。
4. **23 search backends** —— 主流 agent 走自家 search，oh-my-pi 走"perplexity + exa + tavily + brave + jina + kagi + duckduckgo"等多后端链。
5. **MIT + 可 fork** —— 这是路线上的根本差异。oh-my-pi 不是产品，是**开源 platform**，可以 fork、可以改、可以编译自己的 binary。

## 九、什么场景下选 oh-my-pi / 什么场景下选别的

把选择标准落到具体决策：

**选 oh-my-pi 当 ① 必须 self-host / air-gapped** ② 多 provider / plan（同时订阅 Claude / GPT / Gemini / Kimi 等）③ Windows-first 环境 ④ 真实调试需求（attach debugger）⑤ 想要 fork / 改 / 编译自己的 binary。

**选 Claude Code / Codex 当 ① 想要 polish 最高的 UX ② 用 Anthropic / OpenAI plan 已足够 ③ 不打算改 agent 代码 ④ 公司环境锁定 vendor**。

**选 Cursor agent 当 ① 主要工作流在 editor 内 ② 不需要 command line ③ 想要 AI inline editing**。

oh-my-pi 不是"取代 Claude Code"的产品——它是**完全不同的路线**。Claude Code 是"产品路线"——Anthropic 决定 roadmap，用户付月费。oh-my-pi 是"platform 路线"——用户决定 fork / 改 / 编译，付工程时间。

## 十、落地路径

读完上面那些，最常见的反应是"我也想装一个"或者"我也想 fork"。下面是按代价从小到大排的几条路径。

**1. 只装，不改。**

```sh
curl -fsSL https://omp.sh/install | sh
brew install can1357/tap/omp
bun install -g @oh-my-pi/pi-coding-agent
```

装完跑 `omp --version` / `omp setup` / `omp models`，三步走完。oath provider 用 `/login` 登录（Claude / ChatGPT / Cursor / Gemini / xAI / Devin / Kimi 等）。

**2. 接入已有的工作流。** omp 自动 inherit 已经在磁盘上的配置文件（Cursor MDC / Cline .clinerules / Codex AGENTS.md / Copilot applyTo 等），不需要迁移。直接把 omp 加进你团队的 CI / dev shell，跑 `omp -p "执行某个任务"`。

**3. 改 fork。** `git clone https://github.com/can1357/oh-my-pi` → `bun setup` → `bun dev`。改了 Rust crate 后跑 `bun run build:native`，改了 TypeScript 后跑 `bun run dev`。AGENTS.md 第一段给的是必读的工程规矩（用 Bun 不要用 node:*、worker 通过 `workerHostEntry()` 重入 cli.ts、prompts 放 `.md` 文件用 handlebars、token-by-token 类型优先 `Promise.withResolvers()`、central utility 不重复实现等）。

**4. 写自己的 fork。** oh-my-pi 的代码组织方式（Rust crates 做 native，TypeScript 做 session / TUI / config）可以套到任何 coding agent 工程上。门槛不在 Rust 编写（80k 行 Rust 主要是 vendored），在 **「知道哪些事必须 native、哪些事可以 TypeScript」的工程判断**。

## 十一、一章小结

oh-my-pi 不是「又一个 AI Coding Agent」。它是 **pi-mono 路线上第一个把"agent loop 作为库"推到"agent loop 作为平台"的工程级 hyper-fork**——把 pi-mono 拒绝做的"该有的工程基础设施"全部 native 化。

三件事连起来：

1. **它解决了什么**——把 pi-mono 留下的 9 大缺口（provider / 工具集 / Bash / Grep / 调试 / LSP / Search / Session / Subagent）一个一个填上。
2. **它付出了什么代价**——80k 行 Rust 手写 + 80k vendored = 160k 行 native 代码，3 平台 FFI（macOS / Linux / Windows），binary 体积大，macOS 签名 + 公证成本。
3. **它在 pi 生态的位置**——pi-mono / nano-pi / pi-book / oh-my-pi 四套叙事覆盖 agent 工程化的完整光谱：抽象 / 极简 / 文档 / 工程基础设施。oh-my-pi 是其中唯一一个「往里填」的。

把这句话换成更短的版本：**oh-my-pi 是 pi-mono 哲学的产品化终点——"拒绝成为框架"的意思不是"不做工程累人的事"，而是"让 agent 核心不依赖任何具体 surface，但所有必要的工程能力都有 first-class 实现"**。

## 为什么不去

> **为什么 oh-my-pi 不 fork 自 Claude Code 或 Codex CLI？** 因为那两家的核心是商业产品，fork 等于重写整个 product。pi-mono 是 MIT 库 + 明确拒绝框架的代码结构，**oh-my-pi 的"hyper-fork"在工程上是自然延展**——它的 native 实现是在 pi 哲学"agent 是库"基础上加一层"让库依赖也是 first-class 库"，而不是给某个产品换 UI。这条路线只有开源 + 哲学清晰的 pi-mono 能接住。
>
> **为什么不用 Bun / Node 原生能力把 brush / ripgrep 都 port 进 Node？** Node 的 N-API + Bun 的 FFI 是支持这个方向的，但**生产环境的 native 代码体积、跨平台 FFI 稳定性、binary 分发可控性**都指向 Rust。Rust 的 `unsafe` FFI 模型、LLVM 后端、cargo 工具链——这些是为 native addon 设计的。Node 做 native binding 不是不行，是**生命周期管理、GC 与 native 内存混用、ABI 稳定性**都更痛。oh-my-pi 选 Rust 是工程现实，不是意识形态。
>
> **为什么不直接用现成的 brush / ripgrep 二进制而不是 vendored？** 因为"in-process + 0 fork-exec"是 oh-my-pi 的核心承诺。vendored 到 pi-shell / pi-natives 里才能在 libuv 线程池上跑、被 agent 的 cancel / timeout 协议接管、被 session 状态共享。如果 fork 出去跑，就回到 pi-mono 时代"每次 fork 一个新进程"的范式——那 6.7% → 68.3% 的提升就不存在了。**"native 优先"不是性能优化，是架构选择**。
