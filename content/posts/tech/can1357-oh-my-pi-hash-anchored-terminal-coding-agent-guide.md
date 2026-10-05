---
title: "oh-my-pi：把 hash-anchored 编辑做进终端 AI 编程 Agent"
date: "2026-06-25T18:05:11+08:00"
slug: "can1357-oh-my-pi-hash-anchored-terminal-coding-agent-guide"
github_repo: "can1357/oh-my-pi"
source_key: "gh:can1357/oh-my-pi"
description: "can1357/oh-my-pi（omp）是 Stencil Labs 维护的终端 AI 编程 Agent，fork 自 Mario Zechner 的 pi-mono，33.9k Stars（2026-10-01）。它用 hashline 锚定编辑把 str_replace 的失败模式（whitespace 不一致、anchor 漂移、整段重打）从根上拆掉；用 31 个内置工具 + 14 LSP + 28 DAP + 约 80k 行 Rust 内核构建\"Agent 真的能调的工具\"。文章拆 hashline 的 [PATH#TAG] 格式与 PUT/CUT 操作符、基准数据的读法、与同类 Agent 的对比，以及在生产 Agent 中的适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["AI Coding Agent", "Rust", "TypeScript", "LSP", "MCP", "工具调用"]
---

# oh-my-pi：把 hash-anchored 编辑做进终端 AI 编程 Agent

## 先给判断

`can1357/oh-my-pi`（命令名 `omp`，项目主页 [omp.sh](https://omp.sh)）是 Can Bölük 创建、[Stencil Labs](https://stencil.so) 维护的终端 AI 编程 Agent，2025-12-31 立项，九个月做到 33.9k Stars、3.7k Forks（2026-10-01 核实）。它 fork 自 Mario Zechner 的 [pi-mono](https://github.com/badlogic/pi-mono)，把 "Pi" 从一个底层 LLM 客户端重写成"开箱即用的编码工作流"。

它值得专门拆开看的工程原因有三条：

1. **编辑格式动了根**。绝大多数终端 Agent 给模型一个 `str_replace(old, new)`：模型必须把要替换的整段代码原样抄进调用，缩进、空格、换行、emoji 差一个字符就 `String not found`，然后进入重试循环，每试一次就把同样的原文重新烧一遍 token。omp 的解法是 `hashline`——行号加内容哈希做成一等公民锚点，模型只说"第 12 行换成这一句"，不重抄原文。
2. **harness（工具编排层）当产品做**。14 个 LSP 操作 + 28 个 DAP 操作、流级规则中断、advisor 第二模型盯梢、APFS 级 subagent 隔离，这些在其他工具里算插件生态的事，在 omp 里是内置的。
3. **热路径不走 fork-exec**。约 80k 行 Rust 内核把 bash、ripgrep、glob、find、tree-sitter、BPE 计数全部 in-process 链接，模型每调一次工具不用起一个新进程。

作者给出的基准最能说明第 1 条的分量：Grok Code Fast 1 换上 hashline 后，编辑 pass rate 从 **6.7%** 跳到 **68.3%**——模型没换，换的只是编辑格式。这篇文章拆开 hashline 的格式与状态机、harness 的分层结构、这批数字该怎么读，以及什么时候不该选 omp。

## 快速信息卡

| 项目 | 信息 |
|------|------|
| **Stars / Forks** | 33,917 / 3,658（2026-10-01，GitHub API） |
| **许可证** | MIT |
| **语言** | TypeScript（主体）+ Rust（内核约 80k 行） |
| **运行时** | Bun ≥ 1.3.14，macOS / Linux / Windows 原生 |
| **来源** | fork 自 [badlogic/pi-mono](https://github.com/badlogic/pi-mono)，由 Stencil Labs 维护 |
| **仓库** | [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) |

## 系统地图：四层组织

omp 是一个 monorepo：16 个 npm 包加一组 Rust crate，按"交互 → 编排 → 工具 → 内核"四层组织：

```
oh-my-pi
├── 交互层
│   ├── packages/coding-agent/        # CLI 入口与 SDK（omp、omp -p、omp acp）
│   ├── packages/tui/                 # 差分渲染 TUI（Kitty 键盘协议 + PHF 完美哈希）
│   └── packages/collab-web/          # 浏览器 guest client + relay
│
├── 编排层
│   ├── packages/agent/               # Agent runtime、tool calling、状态机
│   ├── packages/mnemopi/             # 本地 SQLite 记忆引擎
│   └── packages/snapcompact/         # 位图帧上下文压缩 + SQuAD 评测
│
├── 工具层（31 个内置工具）
│   ├── read / write / edit / ast_edit / ast_grep / grep / glob
│   ├── bash / eval                   # 运行时（持久 Python + JavaScript 双 kernel）
│   ├── lsp / debug / security_scan   # 代码智能
│   ├── task / wait / todo / ask      # 协调
│   ├── browser / computer / web_search / github / generate_image / tts
│   └── checkpoint / rewind / retain / recall / reflect / memory_edit / learn / manage_skill
│
├── 模型层
│   ├── packages/ai/                  # 多 provider LLM 客户端（流式 + 工具调用）
│   ├── packages/catalog/             # 模型目录 + provider 描述符
│   └── packages/wire/                # collab 协议类型
│
└── Rust 内核（核心 6 crate，~80k 行 + 同量级 vendored 代码）
    ├── crates/pi-natives/           # N-API cdylib 聚合（约 25k 行）
    ├── crates/pi-shell/             # brush-shell 包装的 bash + PTY（约 38k 行）
    ├── crates/pi-ast/               # tree-sitter + ast-grep 包装
    ├── crates/pi-iso/               # APFS/btrfs/zfs/overlayfs 工作区隔离
    ├── crates/pi-walker/            # 并行文件遍历 + grep/glob/workspace 共享缓存
    ├── crates/pi-edit/              # edit 工具引擎：hashline / apply_patch / patch / replace / sloppy 五种模式
    └── crates/vendor/brush-core/    # vendored brush-shell fork
```

四层的职责切割：

- **交互层**只管输入输出：TUI、CLI 参数、ACP/JSON-RPC 协议、Node SDK
- **编排层**管"Agent 这一轮走哪些工具、context 长什么样"
- **工具层**管每一类操作的具体语义：`read` 读 PDF/notebook/URL/SQLite，`debug` 跟 lldb-dap 对话
- **Rust 内核**管高频底层操作：搜索、shell、AST、文本宽度、BPE 计数全部 in-process

一个值得注意的迁移：hashline 引擎最早是 TypeScript 包（`packages/hashline`），2026 年下半年已重写进 Rust crate `pi-edit`——现在编辑落地、快照管理、stale 恢复都跑在内核里，`packages/hashline` 已从仓库消失。引用旧路径的资料（包括本文的早期版本）需要更新。

四层之间的调用方向严格自上而下，所有 native 调用经过编排层的 N-API 绑定。

## hashline：把锚点做成一等公民

str_replace 失败的根本原因是"模型必须重打一遍要替换的原文"。任何空白、缩进、引号、转义的差异都会让锚点漂移，触发 `String not found`，模型进入"再试一次"循环——每次都把同样的原文重新放进 prompt 烧 token。

hashline 的解法是**双重锚定**：

1. **行号**——`read` 返回的每行带 `LINE:TEXT` 前缀（`12:const greeting = "hi";`）
2. **快照标签**——文件头 4 位十六进制哈希，记录"我看到的文件状态"

完整 patch 用 `*** Begin Patch` / `*** End Patch` 包裹，文件 section 的头是 `[PATH#TAG]`。TAG 由快照存储对规范化后的全文算 XXH32 得到：LF 统一换行、剥 BOM、剥行尾空白——所以模型抄不抄错行尾空格根本不影响匹配。

文件 section 内部的操作符（当前语法，来自 [crates/pi-edit/prompts/hashline.md](https://github.com/can1357/oh-my-pi/blob/main/crates/pi-edit/prompts/hashline.md)）：

| 操作 | 语法 | 含义 |
|------|------|------|
| 替换行 | `PUT N.=M:` | 用 body 替换 N 到 M 行（含两端），单行写 `PUT N.=N:` |
| 替换块 | `PUT N*:` | 替换 N 行所在的整个语法块（tree-sitter 定位） |
| 前插 / 后插 | `PUT <N:` / `PUT >N:` | 在 N 行之前 / 之后插入 body |
| 块后插 | `PUT >N*:` | 在 N 行所在块的末尾之后插入（同级深度） |
| 文件头 / 尾 | `PUT <1:` / `PUT >$:` | 文件首尾插入 |
| 删除 | `CUT N.=M` / `CUT N*` | 删除行范围 / 块，无 body，可加 `@名字` 存入寄存器 |
| 寄存器粘贴 | `PUT <N @r` / `PUT N.=M @r` | 把寄存器内容粘到空隙 / 覆盖范围 |
| 文件级 | `REM` / `MV DEST` | 删文件 / 改名 |

核心规则只有一条：**body 行只有 `+TEXT`**。没有 `-old` 行，没有上下文行，没有 unified diff 头——parser 见到 `-` 行直接拒绝，因为行范围本身已经指名了要改哪些行。

### 快照的生命周期

每次 `read` 或 `search` 返回时，快照存储记录一份文件版本。模型拿到的响应长这样：

```
[greet.py#A1B2]
1:def greet(name):
2:    msg = "Hello, " + name
3:    print(msg)
4:greet("world")
```

模型编辑时必须带上 `#A1B2`。编辑成功一次，引擎给文件算出新哈希、作废旧行号，模型要么从编辑响应里取新行号，要么重新 `read`。prompt 规则写得很硬：

> After EVERY edit tag/numbers change: use edit response or fresh `read`; stale tag/surprise → STOP, re-read.

如果模型拿旧 tag 编辑，而文件已经被另一个进程（或前一次编辑）改掉了，引擎检测到哈希不匹配：不静默应用，不做"尽力匹配"，直接拒绝。Claude Code / Gemini CLI 这类工具在 str_replace 失败时通常会重试两三次再放弃，hashline 在第一次 stale 就 STOP。

拒绝之后还有一层恢复：pi-edit 的 recovery 模块会把旧快照上的锚点尝试映射到当前文件——文件被外部改过、行号偏移、会话链断裂分别有对应的告警路径；映射不干净才真正报错。快照本身有 LRU 上限（每路径 4 个版本、总量 64 MB、单文件 4 MB 以上不快照），连续三次完全相同的 no-op 编辑会触发硬上限中断，防止模型烧 token 打转。

## 一次真实编辑：str_replace vs hashline

假设模型要在一个 Python 文件里加一行守卫，并把字符串拼接换成 f-string。原文：

```python
def greet(name):
    msg = "Hello, " + name
    print(msg)

greet("world")
```

str_replace 风格（Claude Code / Gemini CLI / Aider）：

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

每次调用都要把原文重打一遍。第二次调用的 `old_string` 必须是第一次插入**之后**的实际内容，第三次同理。三次调用三段原文。

hashline 风格（omp，一个 patch 搞定）：

```text
*** Begin Patch
[greet.py#A1B2]
PUT >1:
+    if not name: name = "stranger"
PUT 2.=2:
+    greeting = "Hi"
+    msg = f"{greeting}, {name}"
CUT 3
*** End Patch
```

模型不重打任何已有行——所有锚点都是行号，输入不到 str_replace 一半。

更重要的差异是失败率。str_replace 在这些场景会失败：缩进用了 tab 而原文是空格、原文有模型看不见的 BOM、行尾有 trailing whitespace、CRLF 对 LF、文件在 Agent 思考期间被 formatter 改过、原文里的中文注释或 emoji 被转义错。hashline 对这些不敏感——它操作的是规范化后的行号与行内容，读入时怎么规范化，编辑时就怎么还原。

## 基准数据怎么读

作者在 [The Harness Problem](https://blog.can.ac/2026/02/12/the-harness-problem/) 里给的数字（README 同步引用）：

| 模型 | 指标 | 数字 | 说明 |
|------|------|------|------|
| Grok Code Fast 1 | 编辑 pass rate | 6.7% → 68.3% | 换编辑格式，其余不动 |
| Gemini 3 Flash | pass rate | +5pp | 超过 Google 自家的 str_replace 实现 |
| Grok 4 Fast | 输出 token | −61% | 重试循环消失后输出塌缩 |
| MiniMax | pass rate | 2.1× | 同权重同 prompt，仅 harness 变 |

这批数字测的是**同一批编辑任务在只更换编辑格式时的通过率**——模型、权重、prompt 不变，变的只有 harness。所以数字反映的是锚定机制的质量，而不是模型能力的变化；6.7% 到 68.3% 的跃迁说明这些模型本来就能做对，之前是死在 anchor 漂移上。

反过来，有三件事不能从这批数字推出：一，omp 在端到端软件工程基准上整体优于 Claude Code——这里只测了"编辑落地"这一环；二，hashline 对强模型收益一样大——Gemini 3 Flash 只涨 5pp，说明 harness 的收益上限受模型自身格式遵循能力影响；三，这是作者自家的基准，尚无第三方复现，读的时候打折是应该的。

## 与 Claude Code / Gemini CLI / Aider 的对比

| 维度 | oh-my-pi | Claude Code | Gemini CLI | Aider |
|------|----------|-------------|------------|-------|
| 锚定方式 | hashline（行号 + 4-hex tag） | str_replace（字符串匹配） | str_replace | search/replace 块 |
| 工具面 | 31 内置 + 14 LSP + 28 DAP | Bash/Read/Write/Edit/Grep/Glob 等 | 同 Claude Code | Shell 命令 + architect 编辑模式 |
| LSP rename 走 willRenameFiles | ✅ | ❌ | ❌ | ❌ |
| 内置 DAP 调试（lldb/dlv/debugpy） | ✅ | ❌ | ❌ | ❌ |
| 持久 Python + JavaScript 双 kernel | ✅（eval） | ❌ | ❌ | ❌ |
| 浏览器自动化 | ✅（Puppeteer + stealth） | ❌ | ❌ | ❌ |
| 工作区隔离（APFS clone / reflink） | ✅（pi-iso） | ❌ | ❌ | ❌ |
| bash / ripgrep in-process | ✅（brush + pi-builtins） | ❌（fork-exec） | ❌ | ❌ |
| Provider 数 | 60+ | Anthropic 为主 | Google 为主 | 任意 OpenAI 兼容 |
| per-role 路由 | ✅（9 个角色） | ❌ | ❌ | ❌ |
| License | MIT | 商业 | Apache-2.0 | Apache-2.0 |

几个关键差异：

- **LSP rename**：其他工具的 rename 是文本替换，不知道 re-exports 和 barrel 文件的拓扑。omp 调 `workspace/willRenameFiles`，TypeScript 项目的 import alias、barrel re-export、跨文件引用一次性正确更新。
- **DAP 调试**：其他工具遇到 segfault 还是让 Agent 加 print。omp 可以 attach lldb-dap 到二进制、设断点、单步、读 frame 变量；Go 服务挂起就 attach dlv 走 goroutine。
- **In-process bash**：brush（vendored 的 Rust bash 实现）让 session 状态跨调用保留，`cd`、环境变量、alias 不丢；ls、sed、sort、xargs、jq 等数十个常用命令被移植成 in-process builtin。其他工具每条命令 fork 一个新 bash 进程。
- **APFS 隔离**：pi-iso 在 macOS 用 `clonefile(2)`，Linux 用 btrfs/zfs reflink，几乎零成本给每个 subagent 一份独立 worktree；其他工具的 subagent 共用工作区，会互相踩。

代价也实在：monorepo 体积大，首次安装要 bun ≥ 1.3.14（也有 curl/brew/nix/PowerShell 安装脚本），自定义 provider 要写 YAML。但对长任务——多文件重构、debug session、subagent fan-out——这些代价换回的是模型不重打原文、不反复 read 验证环境、不等 fork-exec。

## Rust 内核：约 80k 行在做什么

`packages/natives` 是 N-API addon，把 Rust crate 暴露给 Node。核心 6 个 crate 的分布（README per-crate 表，仅代码行）：

| Crate | 功能 | 约行数 |
|-------|------|-------:|
| pi-shell | 内嵌 bash 引擎 · 持久 session · in-process coreutils 分发 | 38,000 |
| pi-natives | N-API 表面——下表所有模块的宿主 | 25,000 |
| pi-walker | 并行 ignore 感知遍历 + grep/glob/workspace 共享扫描缓存 | 5,200 |
| pi-iso | 工作区隔离：apfs / btrfs / zfs / reflink / overlayfs / projfs | 3,300 |
| pi-ast | tree-sitter + ast-grep 匹配、块解析、结构化摘要 | 2,900 |
| pi-voice | 音频采集/播放 · Opus · WebRTC | 1,000 |

`pi-natives` 内部按模块划分（glue 和测试不计）：

| 模块 | 功能 | 底层库 | 约行数 |
|------|------|--------|-------:|
| desktop | 窗口/显示枚举 · 截图 · 原生输入 · AX 树（computer 工具背后） | xcap · enigo · OS AX FFI | 10,600 |
| grep | regex 搜索 · 并行/串行 · glob/type 过滤 · fuzzy | grep-regex · grep-searcher | 3,280 |
| text | ANSI 感知宽度 · 截断 · 列切片 · SGR 保留 wrap | unicode-width · segmentation | 2,070 |
| snapcompact | 位图帧光栅化 + PNG 编码（上下文压缩用） | image · png | 1,760 |
| keys | Kitty 键盘协议 + xterm fallback · PHF 完美哈希 | phf | 1,740 |
| ast | ast-grep 模式匹配与结构化改写 | ast-grep-core | 1,510 |
| diff | 结构化文件 diff | in-tree | 1,030 |
| pty | sudo / ssh 交互式 prompt 的 PTY | portable-pty | 630 |
| crash_handler | 原生 crash 捕获与上报 | in-tree | 610 |
| highlight | 语法高亮 · 11 语义类别 · 30+ aliases | syntect | 550 |
| appearance | Mode 2031 + macOS 深浅色（CoreFoundation FFI） | core-foundation | 450 |
| task | libuv 线程池阻塞任务 · 取消 · 超时 · profiling | tokio · napi | 440 |
| glob | glob 发现 + type 过滤 + mtime 排序 + gitignore | ignore · globset | 430 |
| fd | find 工具的文件遍历 | ignore | 385 |
| clipboard | 系统剪贴板文本/图片（不依赖 xclip/pbcopy） | arboard | 370 |
| workspace | gitignore + AGENTS.md 单遍扫描 | ignore | 275 |
| power | macOS 电源断言（阻止休眠） | IOKit FFI | 270 |
| prof | 环形 buffer profiler + folded-stack + SVG 火焰图 | inferno | 240 |
| file_lock | 跨进程咨询锁 | in-tree | 210 |
| ps | 跨平台进程树 kill + 后代列举 | libc · libproc · CreateToolhelp32Snapshot | 195 |
| tokens | O200k / Cl100k BPE 计数（两表内嵌） | tiktoken-rs | 70 |
| html | HTML → Markdown（可选内容清理） | html-to-markdown-rs | 60 |
| sixel | 终端图像渲染（PNG/JPEG/WebP/GIF → SIXEL） | icy_sixel · image | 55 |

几个值得注意的设计选择：

- **shell 用 brush 而非 tokio::process**：brush-shell 的 fork 被 vendored 进仓库，bash 是图灵完备的，跑一个进程内实现比每次 fork 外部 bash 更可控，session 状态可以持久；常用外部命令也被移植进 builtins crate，热路径零 fork/exec。
- **tokens 内嵌 BPE 表**：O200k 和 Cl100k 两张表常驻内存，token 计数不需要调外部服务或起 Python。
- **iso 用平台抽象层**：macOS APFS clone、Linux btrfs/zfs reflink、overlayfs、projfs 各走各的系统调用，接口统一。
- **desktop 是新的大头**：1.06 万行，撑起 `computer` 工具——枚举窗口、截屏、原生输入、走系统无障碍树，让 Agent 直接操作桌面。
- **phf 完美哈希**：keys 模块编译时生成 O(1) 查表，键盘事件零间接跳转。

平台编译目标：linux-x64/arm64、darwin-x64/arm64、win32-x64/arm64，x64 附带 AVX2 与 baseline 双二进制。同一个 omp 二进制在三大平台原生跑，不要求用户机器上装好 rg/grep/find/bash。

## 长任务工作流

hashline 是底座，omp 在它之上放了一组长任务能力：

**Time-traveling stream rules**。规则平时休眠，模型输出流一旦匹配某个 regex（比如 `Box::leak`），流在 token 级立即中断，规则作为 system reminder 注入，模型从同一位置重试。README 的演示：模型正要写 `Box::leak`，流被截断并注入"不要在生产代码路径用 Box::leak"，模型改用 `Arc<str>` 并向用户确认。注入跨 compact 存活，同一规则下次触发不用重学。

**/advisor**。给 advisor 角色配一个 review 模型（比如 openai-codex/gpt-5.5），它在自己独立的 context 和模型上读主 Agent 的每一轮，注入 inline 备注——aside、concern、blocker 三档。主 Agent 看到备注要么修正，要么解释为什么不改。做事的模型不被 review prompt 污染上下文。

**/collab**。把 live session 挂到本地 relay，发回 `omp join <id>` 命令、my.omp.sh 链接和 QR 码。队友从另一台终端 `omp join` 接入，或浏览器只读围观；`/collab view` 是纯只读链接。帧在客户端封存，relay 拿不到你的密钥。

**/review**。起 reviewer subagent 并行扫 branch / 单个 commit / 未提交改动，每个输出带 P0–P3 优先级和置信度的结构化 issue，主 Agent 聚合成排序清单加一句 verdict：ships / ships with fixes / blocks。

**记忆**。`retain` 写事实，`recall` 拉原始记忆，`reflect` 在记忆库上合成答案，`learn` 沉淀可复用经验并可以晋升为托管 skill。记忆引擎用 `memory.backend` 选择——本地 SQLite（mnemopi）、Hindsight 或其他后端，按项目隔离：A 项目学到的不会污染 B 项目。session 结束时压缩成 mental model，下次该项目第一轮自动加载。

**Subagent 与 Agent Hub**。`task` 把工作拆给并行 worker，各自跑在隔离 worktree 里，返回 schema 校验过的结构化结果，父级直接读字段不用解析散文。`Alt+A` 打开 Agent Hub 看每个 worker 的实时转录、用量，可以插话或停掉卡住的 worker。

**统一 `://` 命名空间**。`read pr://1428` 和 `read src/foo.ts` 返回同一结构；`agent://<id>/findings.0.path` 直接按路径取 subagent 输出的某个字段。PR、issue、skill、冲突（`conflict://N` 配 `@theirs`/`@ours`/`@base`）都是文件系统形状，模型学一个接口就够。

接入方式五个入口：`omp` 交互 TUI、`omp -p` 单次 prompt、Node SDK（`@oh-my-pi/pi-coding-agent`，session 发 typed event）、`omp --mode rpc`（NDJSON over stdio）、`omp acp`（Agent Client Protocol，Zed 等编辑器驱动）。

## 适用边界与选型

适合 omp 的场景：

- **多文件长任务**：跨 5+ 文件的重构、debug session、workspace 级搜索替换
- **吃 LSP/DAP 的项目**：TypeScript / Rust / Go / C++，rename 引用、attach debugger 是日常
- **强 harness 需求**：advisor、流级规则、项目记忆、隔离 subagent 你都要
- **多 provider 切换**：plan 角色用 Opus、smol subagent 用便宜模型、reviewer 用另一家，9 个角色各配各的
- **Windows 原生环境**：omp 原生跑 win32-x64/arm64，不用 WSL 桥

不适合的场景：

- **要 IDE 原生体验**：Zed（ACP）能拿到 in-editor 体验，但和 Cursor / Windsurf 的"左边编辑器右边聊天"比，omp 还是 terminal first
- **要零配置开箱**：安装要 bun 或安装脚本，自定义 provider 要手写 YAML；Claude Code 的开箱度更高
- **锁定单一厂商**：想保持 Anthropic-only 团队，omp 的 60+ provider 开放度是负担不是特性
- **轻量小项目**：200 行的 Python 脚本，str_replace 足够，hashline 加 31 个工具的复杂度过剩
- **要云端托管**：omp 是本地 CLI，没有 hosted 版

选型速查：

| 需求 | 首选 | 次选 |
|------|------|------|
| 长任务 + 多文件 + 强 harness | oh-my-pi | Claude Code |
| 强 IDE 集成 + 云端 | Cursor | Windsurf |
| 终端 + 多 provider + 跨平台 | oh-my-pi | Aider |
| 一次性脚本、低学习成本 | Claude Code / Gemini CLI | Aider |
| 真实 LSP rename / DAP 调试 | oh-my-pi | Cursor |

一句话收尾：omp 把"模型改文件"这一件最频繁的事从概率游戏改成了确定性协议——行号和哈希不会含糊，stale 就拒绝，恢复有兜底。如果你的日常工作是多文件长任务，它值得装一次试试；如果你的场景是单文件小修，str_replace 系工具依然是更省心的选择。

## 常见问题

**stale tag 报错怎么处理？**
这是设计行为而非故障：文件在模型读之后被改过（手动编辑、formatter、另一个 Agent）。让模型重新 `read` 目标文件再发 patch 即可；正常情况下 recovery 会自动重映射锚点，只有映射不干净才需要人工介入。

**生产环境要注意什么？**
模型成本按角色分开预算（9 个角色的用量在 Agent Hub 里能看到）；`github`、`generate_image`、`tts`、记忆工具等默认关闭，启用前确认数据出境策略；hashline 拒绝 patch 是保护机制，不要在包装层里绕过它。

**许可证和商用？**
MIT。vendored 的 brush-core 等第三方代码保留各自上游许可证，细节见仓库的 THIRD-PARTY-NOTICES.txt。

**遇到问题去哪？**
文档在 [omp.sh](https://omp.sh)，源码和 issue 在 [GitHub 仓库](https://github.com/can1357/oh-my-pi)，社区在 [Discord](https://discord.gg/4NMW9cdXZa)。

## 参考链接

- 仓库：[can1357/oh-my-pi](https://github.com/can1357/oh-my-pi)
- 项目主页与文档：[omp.sh](https://omp.sh)（工具参考 [omp.sh/docs/tools](https://omp.sh/docs/tools)，provider 与路由 [omp.sh/docs/providers](https://omp.sh/docs/providers)）
- hashline prompt 与语法：[crates/pi-edit/prompts/hashline.md](https://github.com/can1357/oh-my-pi/blob/main/crates/pi-edit/prompts/hashline.md)
- 作者对 harness 问题的完整论述：[The Harness Problem](https://blog.can.ac/2026/02/12/the-harness-problem/)
- 上游项目：[badlogic/pi-mono](https://github.com/badlogic/pi-mono)

文中 stars/forks、工具数、LoC 数据核实于 2026-10-01 的 GitHub API 与 main 分支 README；hashline 语法以 `crates/pi-edit` 当前源码为准。
