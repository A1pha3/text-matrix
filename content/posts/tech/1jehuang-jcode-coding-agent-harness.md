---
title: "jcode：把内存压到 27.8 MB 的 Coding Agent Harness 怎么做到"
date: 2026-07-20T03:02:36+08:00
lastmod: 2026-09-07T23:45:00+08:00
categories: ["技术笔记"]
tags: ["Coding Agent", "Rust", "TUI", "MCP"]
description: "jcode 是一个用 Rust 写的 coding agent harness，单 session 空载 PSS 低至 27.8 MB，约为 Claude Code 的 1/14，启动到首帧 14 ms。本文拆解它的内存取舍、记忆系统、多 session server 架构与 MCP 支持边界。"
slug: 1jehuang-jcode-coding-agent-harness
github_repo: "1jehuang/jcode"
source_key: "gh:1jehuang/jcode"
---

# jcode：把内存压到 27.8 MB 的 Coding Agent Harness 怎么做到

## 一句话判断

jcode 是 1jehuang 在 2026 年初开源的 Rust 系 coding agent harness。按 README 的实测，关掉本地 embedding 后，单 session 的 PSS（Proportional Set Size，把共享内存按比例分摊给进程后的物理内存占用）只有 **27.8 MB**；同一张表里 Claude Code 是 386.6 MB，OpenCode 是 371.5 MB，约为它的 14 倍和 13 倍。多 session 并行时，省下的内存就是同一台机器上能同时开的 agent 数。

## 项目定位

| 维度 | 数据（2026-09-07 快照） |
|------|------|
| 仓库 | [1jehuang/jcode](https://github.com/1jehuang/jcode) |
| Stars / Forks | 19,279 / 2,215 |
| 提交数 | 7,421（master） |
| 创建时间 | 2026-01-05 |
| 最新版本 | v0.84.0（2026-09-07） |
| 协议 / 语言 | MIT / Rust |
| 平台 | Linux x86_64/aarch64、macOS、Windows（原生 + WSL2）、Termux |

仓库创建 8 个月拿下 1.9 万 star，发版节奏相当密：2026-09-03 到 09-07 五天里连发 v0.81.5 到 v0.84.0 六个版本。官网 [jcode.sh](https://jcode.sh) 把安装压成一行 `curl | bash`，上手门槛和 Claude Code、Codex CLI 一样低；差别在于它围绕资源开销做了一连串具体的工程取舍。

## 系统地图

按 README 的叙述层次还原，jcode 由四块组成：

| 模块 | 责任 | 关键事实 |
|------|------|----------|
| Harness runtime | 启动 session、解析 CLI、加载 provider、调度 agent 循环 | 空载 PSS 27.8 MB / 单 session（关本地 embedding） |
| Memory subsystem | 跨 session 的语义记忆 | 本地 all-MiniLM-L6-v2 嵌入，GPT-5.3 Codex Spark 做 sidecar 校验 |
| Provider / MCP 适配层 | 接入 30+ 家 LLM 服务与外部 MCP 工具 | 内置 OAuth 登录；MCP 当前只支持 stdio 类型 |
| TUI 界面 | 终端交互、侧边栏、内联渲染 | 侧边栏可当 diff 查看器，mermaid 图内联渲染 |

单 session 时，内存大头不是模型本身（模型在云端），而是 harness 的本地状态，其中最大的变量就是本地 embedding：关掉它，PSS 从 167.1 MB 降到 27.8 MB。jcode 把本地 embedding 做成可关闭的开关，不做默认依赖。多 session 那头另有结构：所有 session 由一个常驻 server 进程统一托管，MCP 连接也由 server 池化共享（见下文〈多 session：一个 server 进程管所有会话〉）。

## 性能对比的关键数字

README 的对比表直接反映了内存开销的差异：

- **1 active session**：
  - jcode（关本地 embedding）：**27.8 MB**（baseline）
  - jcode（默认）：167.1 MB（6.0×）
  - pi：144.4 MB（5.2×）
  - Codex CLI：140.0 MB（5.0×）
  - OpenCode：371.5 MB（13.4×）
  - GitHub Copilot CLI：333.3 MB（12.0×）
  - Cursor Agent：214.9 MB（7.7×）
  - **Claude Code：386.6 MB（13.9×）**
  - Antigravity CLI：243.7 MB（8.8×）
- **10 active sessions**：
  - jcode（关 embedding）：**117.0 MB**（baseline）→ 带 embedding 260.8 MB
  - Codex CLI：334.8 MB / pi：833.0 MB / Antigravity CLI：约 1.0 GB
  - Cursor Agent：约 1.6 GB / GitHub Copilot CLI：约 1.7 GB
  - **Claude Code：约 2.3 GB** / **OpenCode：约 3.2 GB**

比"10 session 总量"更能说明问题的是每新增一个 session 的固定开销，README 单独给了这张增量表：

| 工具 | 每新增一个 session 的 PSS 增量 |
|------|------|
| jcode（关 embedding） | 约 9.9 MB |
| jcode（默认） | 约 10.4 MB |
| Codex CLI | 约 21.6 MB |
| pi | 约 76.5 MB |
| Antigravity CLI | 约 86.4 MB |
| Cursor Agent | 约 157.5 MB |
| GitHub Copilot CLI | 约 158.1 MB |
| Claude Code | 约 212.7 MB |
| OpenCode | 约 318.4 MB |

九个工具的曲线都是线性的，jcode 并没有改变增长的形状；它做的是把斜率压下来——同样是加一个 session，jcode 花 9.9 MB，OpenCode 花 318.4 MB，差 32 倍。对同时跑 5-10 个 agent session 的开发者，这个斜率决定了机器的承受能力。

启动速度是另一个维度。README 测得"启动到首帧"：jcode 14.0 ms（区间 10.1–19.3 ms），最快的对手 Antigravity CLI 也要 383.5 ms，Claude Code 3436.9 ms（245.5 倍）。到"可接受输入"（输入探测文本出现在屏幕上）的口径，jcode 是 48.7 ms。

这组数字来自 README 作者在同一台 Linux 机器上的实测（每工具 10 次交互式 PTY 启动），各工具固定版本：jcode v0.9.1888-dev、pi 0.62.0、codex-cli 0.120.0、opencode 1.0.203、GitHub Copilot CLI 1.0.24/1.0.27、Cursor Agent 2026.04.08、Claude Code 2.1.86、Antigravity CLI 1.0.0。它衡量的是 session 启动后的空载 PSS，不是任务进行中的峰值占用。换系统、换配置、换工作负载，数值都会变。它能回答"开 N 个闲置 session 谁更省内存"，不能推出 jcode 在真实任务里更快，也不能推出任何机器都能复制同样的差距。

## 安装与快速开始

```bash
# macOS / Linux
curl -fsSL https://jcode.sh/install | bash

# Windows 11（PowerShell 5.1+）
irm https://jcode.sh/install.ps1 | iex
```

不想用脚本的还有两条路：Homebrew（`brew tap 1jehuang/jcode` 后 `brew install jcode`），以及源码构建（`cargo build --release`）。Windows 安装器会按 SHA256SUMS 校验下载，Alacritty 和全局热键这类可选项需要显式同意才装；Termux 需要先 `pkg install glibc patchelf`。卸载脚本默认保留配置和会话记录，`--purge` 才全清。

装完之后的常用入口，README 的 Quick Start 原样如下：

```bash
jcode                     # 启动 TUI
jcode run "say hello"     # 非交互跑一条命令
jcode --resume fox        # 按名字恢复历史 session
jcode serve               # 常驻 server 模式
jcode connect             # 另开客户端连接 server
jcode dictate             # 语音输入（走你配置的 STT 命令）
```

## 关键机制拆解

### 1. 为什么是 Rust

Coding agent 的 runtime 分为两类：

- **Node / TS 系**（OpenCode、Claude Code、Cursor Agent）：开发快、依赖成熟，但 V8 基线加上一串 transitive deps，内存开销天然大。
- **Rust 系**（jcode）：启动到首帧 14 ms、PSS 接近原生二进制、没有 JIT 预热。

jcode 选 Rust 的理由很直接：多 session 场景的瓶颈是内存而不是吞吐。10 session 并行时，3 GB 和 260 MB 的差距，就是"同时跑三个项目"和"只跑得起一个"的差距。

### 2. 记忆系统：本地嵌入 + sidecar 校验 + 已落地的记忆图

jcode 的记忆不是把对话原样囤起来。架构文档（`docs/MEMORY_ARCHITECTURE.md`）描述的实现分几层：

- **嵌入与检索**：每轮回复用本地 all-MiniLM-L6-v2 模型（tract-onnx 推理，不依赖外部服务）嵌入成向量，逐轮对记忆做余弦相似度查询。命中之后不是直接返回，而是沿记忆之间的语义边做一次 BFS 级联检索，把间接相关的条目一并带出来。
- **sidecar 校验**：命中结果先交给一个轻量 sidecar 模型（当前是 GPT-5.3 Codex Spark）核对是否真的相关，必要时再补一轮信息抽取，才注入对话。
- **写入与合并**：记忆抽取在后台进行——检测到语义漂移、隔了若干轮、或 session 结束时触发。写入时有合并逻辑：语义相似的记忆被强化而不是重复存储，矛盾的记忆用 `Supersedes` 关系替代旧条目，并留下来源追踪。
- **写入前过滤**：架构文档的 Privacy 一节写明，API 密钥、密码、个人身份信息、标记为敏感的文件内容不进记忆库，写入前先做正则扫描。
- **图结构**：记忆、标签、聚类三类节点，用 `HasTag`、`InCluster`、`RelatesTo`、`Supersedes`、`Contradicts` 这几种边连起来。架构文档的 Implementation Status 清单把这一层标记为已实现；置信度还会随时间按类别的半衰期衰减。
- **显式入口**：`jcode memory` 子命令可以列出、检索（支持语义搜索）、导入导出记忆，agent 也有主动的记忆工具和跨 session 的 RAG 搜索，不依赖后台被动索引。

ambient 整理和全图深度整理是两回事，文档分得很清：README 说 ambient 模式会定期整理记忆（重组、查过期、查冲突），架构文档则把全图级的深度整理——全图合并去重、跨图矛盾消解、对代码库做事实核验——列在 Phase 8 待办里。也就是说，"定期整理已有，全图深度整理还在路上"。

关掉本地 embedding 后，嵌入和自动检索这一层不加载，这正是 PSS 从 167.1 MB 掉到 27.8 MB 的主因。显式记忆工具和 RAG 搜索仍在。要省内存还是保留自动记忆，是文档里明确留给用户的权衡。

### 3. MCP：标准协议，但当前只走 stdio

jcode 读标准的 `mcpServers` 配置，兼容成本做得很足：全局配置在 `~/.jcode/mcp.json`，项目级在 `.jcode/mcp.json`；它会直接读取 Claude Code 的 `~/.claude.json` 和仓库根的 `.mcp.json`（每次加载实时读取，改动即时生效），并支持从 Codex CLI 一次性导入。每个 MCP 请求默认 30 秒超时，慢工具可以在配置里调 `timeout_secs`。

但边界要写明：README 原话是 "jcode currently supports stdio (command-based) servers only; HTTP/SSE entries are recognized and skipped"。npx 拉起的 chrome-devtools-mcp、本地跑的 github-mcp-server 这类 stdio server 可以直接挂；纯远程的 HTTP/SSE server 目前会被识别然后跳过，并在日志里留一行提示。选型时如果你依赖的是远程 MCP 服务，这条要先确认。

### 4. 多 session：一个 server 进程管所有会话

jcode 的规模优势不只来自 Rust 的 malloc，还来自架构。`docs/SERVER_ARCHITECTURE.md` 写明它是 single-server、multi-client：`jcode serve` 起一个常驻 server，通过 Unix socket（`/run/user/$UID/jcode.sock`）服务所有 TUI 客户端，断线或 server 热重载后客户端透明重连。session 用"形容词 + 动物"命名（比如 "blazing fox"），注册表存在 `~/.jcode/servers.json`。

在这个结构下，"几个 agent 同时改一个仓库"不是各改各的：A 会话改了 B 读过的文件，server 会通知 B，B 可以拉 diff 确认冲突；agent 之间可以私信、按仓库广播。MCP 连接也由 server 池化共享，多个 session 复用同一批 MCP server，不必各起一份。再往上是 swarm：agent 能用 swarm 工具自主拉起 teammates 并行干活，自己转成协调者，整组 agent 的消息通道和完成状态由框架管理，headless 和有头模式都支持。

### 5. 自举：self-dev 是一个正式的 CLI 子命令

README 里的 self-dev 不是营销词，`jcode self-dev` 是 dispatch 表里的真实子命令。进入这个模式后，agent 会修改 jcode 自己的源码——编辑、构建、测试、重载二进制，全自动循环。官方文档同时给了警告：jcode 代码库不简单，建议用 frontier 模型（GPT-5.5 或更新）来做这件事，弱模型会引入隐蔽的破坏性改动。

仓库里能看到自举留下的维护产物：`docs/MEMORY_BUDGET.md` 定义了一套内存回归预算，状态标注 "active guardrail"，预算绑定到代码里已有的计数器和上限，配套 `:debug memory` 这样的 TUI 调试面和排障 runbook。对普通用户，self-dev 更像一道上限证明——维护 harness 本身这件事，作者已经用这个 harness 走通了。

### 6. 内置 browser 工具

jcode 内置了一个 `browser` 工具做会话内的浏览器控制，当前后端是 Firefox（Firefox Agent Bridge），动作集覆盖 open、snapshot、click、type、fill_form、eval、screenshot 等十六项，`jcode browser setup` 一键配置。UI 对浏览器调用做紧凑摘要，输入敏感文本不回显。provider 架构留了扩展位，Chrome bridge 类后端可以后续接入。

### 7. Provider 生态与跨 harness 迁移

内置 OAuth 登录覆盖 Claude、OpenAI、Gemini、GitHub Copilot、Azure、阿里云 Coding Plan 等；另有一批 OpenAI 兼容的现成 profile（openrouter、deepseek、kimi、moonshotai 等），再往下的内置 provider 集成还有 groq、mistral、perplexity、xai 等二十余家，本地模型走 Ollama / LM Studio，任意 OpenAI 或 Anthropic 兼容网关可以用 `jcode provider add` 配置。配额用完时 `/account` 一键切到下一个账号。

迁移方向上有个少见的特性：跨 harness 恢复会话。codex、claude code、opencode、pi 的历史 session 都能从 jcode 里 resume——Claude Code 中途坏了，用 jcode 接着跑。Skills 的加载方式也和记忆同构：启动时不全量载入，对话语义命中才注入对应 skill，也可以手动用 skill 工具或斜杠命令激活。

### 8. 零散细节，同一个方向

README 的 Misc 一节列了一批互不相干的小改动，方向却一致：省内存、省 token、省等待。

- **agent grep**：自研的 grep 工具，返回结果附带文件结构信息（函数列表、偏移量），agent 不读整个文件也能推断里面有什么；harness 再按 agent 已经看过的内容自适应截断输出。省的是上下文 token。
- **输入调度**：输入默认在不打断 KV cache 的时机插进对话，想排队等当前轮跑完再发，用 shift+enter。为的是保住 provider 端的 prompt cache。
- **cache 冷却提醒**：Anthropic 的 prompt cache 5 分钟就冷，jcode 会在 cache 冷掉时警告，出现预期外的 cache miss 也会提示——冷掉的 token 账单不至于来得莫名其妙。
- **自研 mermaid 渲染器**：TUI 内联渲染 mermaid 图靠作者另写的 Rust 库 [mermaid-rs-renderer](https://github.com/1jehuang/mermaid-rs-renderer)，README 称渲染速度提升 1800 倍，不依赖浏览器和 TypeScript。

单看每一项都不大；合起来看，性能在这个项目里是一项持续维护的纪律，架构决策只是起点。

## 一次任务流案例

假设你同时在三个仓库上工作：一个 Rust 后端、一个 React 前端、一个 Python 数据处理脚本。用 jcode 开三个 session，每个 session 挂不同的 provider（Claude、GPT、Gemini），各自跑 MCP server（git、linter、test runner）。

按 README 的增量数据折算：Claude Code 跑三个 session 大约 812 MB（首个 386.6 MB，之后每个约 212.7 MB），16 GB 的笔记本扛得住，但已经能感觉到占用。jcode 三个 session 约 48 MB（关 embedding：27.8 + 9.9 × 2）或约 188 MB（开 embedding：167.1 + 10.4 × 2）。扩到 10 个 session，差别从"有点紧"变成"能不能跑"：Claude Code 涨到约 2.3 GB，OpenCode 约 3.2 GB，jcode 关 embedding 总共 117 MB——在 16 GB 的机器上，前者已经开始挤占 IDE 和浏览器的空间，后者还有大把余量。

这个案例背后是 jcode 的一组默认取舍：不带 embedding、不做 IDE 集成、纯 TUI，换来的是多 session 并行时内存不失控。

## 常见疑问

**这些内存数字是它自己测的吧？能信多少？** 数字来自 README 作者在同一台 Linux 上、固定版本、每工具 10 次交互式 PTY 启动的实测，衡量的是 session 启动后的空载 PSS。同一逻辑在不同系统、配置和负载下会变，它只回答"开 N 个闲置 session 谁省内存"这一个问题。真要到选型的程度，最好在你自己的机器和任务上再量一次。

**关掉 embedding 记忆功能还在吗？** 还在，只是从自动后台索引降级。显式的记忆工具和跨 session 的 RAG 搜索仍然可用，agent 可以主动去查；少的是每轮对话的自动嵌入和相关联的内存开销。这是文档明确留给用户的开关，不是砍功能。

**它是 Claude Code 的替代品吗？** 不完全是。它连模型时仍可接 Claude、OpenAI、Gemini，替代的是承载模型的运行时。如果你主要是单 session、重度依赖 IDE 集成或开箱即用的生态，Claude Code、Codex CLI 更省心；jcode 的优势集中在"多 session 并行 + 资源敏感"这条赛道。

**8 个月 1.9 万 star，涨得这么快，会不会是刷的？** star 数本身没法自证清白，但工程节奏是可以核对的：仓库 2026-01-05 创建，7,400 余次提交延续到本文写作当天（2026-09-07），五天六版的发布频率，changelog 按版本逐条可查。对它的正确预期是"一个正在极速演进的项目"，配置和工作流可能随版本变化。

## 采用建议

**谁该先用**：需要同时跑 3 个以上 session 的人——不同仓库、不同任务，内存斜率决定一台机器能同时摊开多少 agent。内存敏感的场景同理：8 GB 的 MacBook Air、16 GB 的 Linux 笔记本、跑 agent 的 CI 容器。想把 agent 当脚本组件用的人也合适，首帧 14 ms 意味着冷启动开销接近无。provider 灵活性算最后一条：30+ 个 provider 可插拔，历史会话能从 codex、claude code、opencode、pi 那边直接接管。

**谁可以等等**：单 session 工作流占主导的人，jcode 的优势发挥不出来；重度依赖 VS Code、JetBrains 的人，它是纯 TUI，不做 IDE 插件；依赖远程 HTTP/SSE MCP 服务的人，stdio 之外的类型会被识别后跳过，等官方支持前要另找方案；想要厚生态的开箱即用型用户，Claude Code、Codex CLI 的文档、插件和 prompt 工程积累都更厚——做 agent 工程的系统设计前，先读 [12-Factor Agents](/posts/tech/12-factor-agents-production-llm-guide/) 再选型会更稳。

**从哪里开始**：
1. 先看 README 的 Performance 表或 [jcode.sh/bench](https://jcode.sh/bench)，确认你的场景是否值得为内存买单
2. 三条安装路径任选其一（脚本、Homebrew、源码），然后跑 `jcode run "say hello"` 做冒烟测试
3. 用 `jcode memory list` 和 `jcode memory search` 看看跨 session 记忆实际存了什么
4. 在多个 session 里跑同一个任务，观察 PSS 是否与 session 数保持低斜率线性
5. 系统性补齐 agent 工程背景，可以配合 [从零开始的 AI 工程课程实测](/posts/tech/ai-engineering-from-scratch-guide/) 一起看
