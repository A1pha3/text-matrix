---
title: "代码即真相、Bash 够用、反对 MCP：Pi 作者与 90k stars 的极简智能体（Agent）赌注（附视频逐字双语字幕）"
slug: pi-coding-agent-code-as-truth-no-mcp
date: 2026-08-17T17:10:00+08:00
tags: ["Pi", "AI Agent", "Coding Agent", "Context Engineering", "MCP", "Bash", "RAG", "YOLO", "Mario Zechner", "Armin Ronacher", "Earendil", "Gondolin", "Claude Code", "Cursor"]
categories: ["视频精读"]
description: "深度解读 @宝玉xp 转发的一段 Pi 创始人访谈视频。Pi = github.com/earendil-works/pi，由 libGDX 创始人 Mario Zechner 与 Flask 创造者 Armin Ronacher 共同打造，90k stars，TypeScript，MIT 协议，v0.84.2。两位作者的核心主张：代码即真相，不需要 RAG（检索增强生成）；Bash 足够用，反对 MCP（模型上下文协议）；YOLO by default，permission popup 是 security theater。从 system prompt < 1000 tokens 到 4 个内置工具，把该减的全减完。"
author: 钳岳
---

# 代码即真相、Bash 够用、反对 MCP：Pi 作者与 90k stars 的极简智能体（Agent）赌注

> 来源：微博视频 `https://video.weibo.com/show?fid=1034:5332798752358424`，`@宝玉xp` 于 2026-08-17 转发，时长 2:56。原视频是 Pi 创始人访谈的二手转述，**`@宝玉xp` 是技术博主本人撰写的摘要，非第三方转写**。摘要里两位 Pi 作者的核心观点：
>
> 1. "代码即真相，代码不需要记忆系统，不需要 RAG（检索增强生成），模型很擅长理解代码结构。"
> 2. "Bash 工具足够用，Bash 类似于编程语言，可以任意组合；大部分时候没必要 MCP（模型上下文协议），skill + 脚本足够。"

> **视频评论 4 条（按时间排）**：
> - 8-17 07:13 来自 AI 罗伯特：「代码洁癖犯了」（AI 虚拟账号，泛技术评论）
> - 8-17 07:18 来自山西中国结很纯：（空评论）
> - 8-17 07:34 来自广东麒麟飞狐：「然后让大模型随意发挥？」
> - 8-17 07:51 来自日本莫比乌斯环黑洞：「平时用 Vibe coding 写着玩可以，但是给企业做系统、做产品，没有知识库、没有记忆体，就是给系统和产品埋雷挖坑。没有 AI 的时代需要软件工程，有了 AI 之后也需要 harness 工程。没有知识库和记忆体，harness 玩不起来。」

本文基于该视频摘要、评论区 4 条与 Pi 官方仓库数据（截至 2026-08-21）整合而成，原视频完整逐字稿见 §10。**凡是从视频摘要之外补充的事实，全部标注来源**。

## 写在前面：为什么这两个反直觉观点值得拆

AI 编程 Agent（智能体）圈子的主流剧本是这样的：

- 上下文不够 → 加 RAG，做 code index（代码索引），加向量数据库
- 工具不够 → 加 MCP，让模型能接外部服务
- 工具太危险 → 加 permission popup（权限弹窗），再加 sandbox（沙箱），再加审批流
- 任务太复杂 → 加 sub-agent（子智能体），加 plan mode，加 todo 系统

Pi 的两位作者把这条链几乎全部按了下去。Mario Zechner 在博客里写过一句话，把它翻译成中文是：

> "把 context engineering（上下文工程）做到极致，比堆 RAG / 长期记忆 / 子智能体更划算。"

他不是喊口号。同一篇博客里还有一句更狠的，是他造 Pi 的总原则：

> "If I don't need it, it won't be built."（我不需要的东西，就不会被造出来。）

这不是技术取舍，这是对 "AI Agent 复杂度爆炸" 的明确反抗。

> **一句话总览**：Pi 用 4 个内置工具 + < 1000 tokens（词元）的 system prompt（系统提示词）+ 拒绝整套 MCP 生态，赌 "上下文精确控制 > 上下文扩张" 是 AI 编程 Agent 该走的路。

---

## 1 · 两位作者与一个奇怪的公司

Pi 的两位作者都来自欧洲独立开发者圈。

- **Mario Zechner**（GitHub 账号 `badlogic`，奥地利）：libGDX 的创始人之一 —— 一个用 Java 写 Android/桌面游戏的跨平台框架，2010 年前后在移动游戏圈几乎是事实标准。
- **Armin Ronacher**（GitHub 账号 `mitsuhiko`，奥地利）：**Flask、Jinja2、Click、werkzeug** 框架的创造者，后来又参与创办 Sentry —— 几乎是 Python Web 开发者每天都会撞见的名字。

两人 2025-04 一起在奥地利创办了一家公司 **Earendil Inc.**（官网 earendil.com），tagline 是 "Bearer of Light"——《魔戒》里那颗维雅之星。Earendil 就是 Pi 的归属公司。

> **关键事实**：这两个人都不是 AI 圈的人——一个出身游戏框架圈，一个出身 Web 框架圈。Pi 不是商业产品，是 "出于爱好 + 自己日常工作需要" 做的项目。

这件事本身就值得停下来想想。一群从 AI 巨头公司出来的工程师在做 AI Agent，目标是占领市场；两个从 libGDX/Flask 时代走出来的传奇开发者也在做 AI Agent，目标是让自己和朋友们用得顺手。这两种状态对 "AI Agent 应该长什么样" 的回答不会一样。

Mario 在博客里写了自己为什么弃用 Claude Code（来源：mariozechner.at/posts/2025-11-30-pi-coding-agent）：

> "Over the past few months, Claude Code has turned into a spaceship with 80% of functionality I have no use for. The system prompt and tools also change on every release, which breaks my workflows and changes model behavior. I hate that. Also, it flickers."

> "Claude Code 已经变成一艘 80% 功能我都用不上的宇宙飞船。每次发布 system prompt 和工具都变，我的工作流被打破，模型行为跟着变。我恨这个。另外它还闪屏。"

"宇宙飞船"这个比喻后来成了 Pi 社区最常引用的梗。Mario 造 Pi 的动机，就是把飞船拆回自行车。

### 1.1 Pi 不是一个项目，是四个包

Pi 的仓库 `earendil-works/pi`（旧地址 `badlogic/pi-mono` 已自动重定向）拆成了四个 npm 包，各管一层（来源：Mario 博客原文 + 社区源码解析）：

| 包 | 职责 |
|---|---|
| `@earendil-works/pi-ai` | 统一大语言模型（LLM）API（应用程序接口）：多 provider 支持（Anthropic / OpenAI / Google / xAI 等 7 家 + 任意 OpenAI 兼容端点）、流式、工具调用、跨 provider 上下文交接、token（词元）与成本追踪 |
| `@earendil-works/pi-agent-core` | 与模型无关的 Agent 运行时：工具调用循环、状态管理、transport 抽象 |
| `@earendil-works/pi-tui` | 终端 UI 库：差分渲染 + 同步输出（几乎不闪屏） |
| `@earendil-works/pi-coding-agent` | 你实际运行的 CLI（命令行工具）：会话管理、扩展系统、主题 |

Mario 对底层 API 的吐槽很有代表性：市面上统一 LLM API 大多"无法中断请求、不返回部分结果"，这在生产系统里不可接受。Vercel AI SDK（软件开发包）这类现成方案呢，在自托管模型上工具调用总出问题。所以他全自己写（来源：Mario 博客原文，pi-ai 一节）。顺带一提，这套底座不止 pi 一个应用 —— OpenClaw（前身 ClawdBot）就是 fork（派生）自 Pi 的 TUI 组件做出来的（来源：社区文章，OpenClaw README 致谢 Mario）。

### 1.2 仓库数据快照

Pi 仓库地址：`github.com/earendil-works/pi`。数据截至 2026-08-21：

- Stars：90,390
- Forks：11,214
- Open issues：135
- License：MIT
- Language：TypeScript
- 首次发布：2025-08-09
- 最新版本：v0.84.2，发布于 2026-08-14

一年时间，9 万 star。TypeScript 写的中大型 AI 项目能跑出这个数字，是社区对 "极简方向" 投票的结果。

---

## 2 · 第一条反直觉观点：代码即真相，RAG 不是答案

> 视频原话（摘要）："代码即真相，代码不需要记忆系统，不需要 RAG，模型很擅长理解代码结构。"

把这条观点拆开看，Mario 反对的不只是 "RAG 这个具体技术"，是 "让模型记住你的整个代码库" 这件事本身。

### 2.1 反对的理由

Mario 博客原文（mariozechner.at/posts/2025-11-30-pi-coding-agent）：

> "I learned that context engineering is paramount. Exactly controlling what goes into the model's context yields better outputs, especially when it's writing code."

> "我学到的是 context engineering 至高无上。精确控制进入模型上下文的东西，产出会更好，尤其是写代码时。"

他接着说，现有 harness 的问题恰恰是做不到精确控制（博客原文，同一段）：

> "Existing harnesses make this extremely hard or impossible by injecting stuff behind your back that isn't even surfaced in the UI."

> "现有 harness 让这件事变得极难甚至不可能——它们在背后注入东西，UI 里甚至不显示。"

Cursor 的 codebase 索引（codebase index）就是一个典型例子：每次会话都要消耗几万个 token，往上下文里塞一段代码库总结。这部分开销不小，更关键的是——这段总结的质量决定了模型后续每一次决策的基底，好坏完全取决于索引怎么写。（此例未见于 Mario 博客原文，可能出自访谈的未转写部分；"Pi 默认不索引"的事实本身来自博客原文。）

对立的两端是两种信息形态：**原始事实与派生副本**。代码本身可执行、可验证、永远是最新的；索引和向量库是从代码压缩出来的快照，生成那一刻就开始落后，丢了的信息也永远补不回来。逐字稿 S3 的 "It's also evolving" 说的正是这层——代码在演进，任何快照都是过时的。

Pi 的应对：默认不索引。你想看哪个文件，自己 `read` 进来；想找什么东西，用 `grep` / `find` / `ls` 扫。模型每次 forward（前向推理）都拿到的是 "你让它看的东西"，不是 "AI 工具猜它应该看的东西"。

### 2.2 "但 RAG 不是 0，是可选"

把这件事说成 "Pi 完全不要 RAG" 不准确。pi.dev 官网说的是：

> "Extensions can inject messages before each turn, filter the message history, implement RAG, or build long-term memory."

> "扩展可以在每轮对话前注入消息、过滤消息历史、实现 RAG 或构建长期记忆。"

—— RAG / 长期记忆都是 **可插拔的 extension（扩展）**，不是核心能力。核心能力是 "精确控制进入模型的东西"。

评论区里 "莫比乌斯环黑洞" 的反驳（2026-08-17 07:51 来自日本）：

> "平时用 Vibe coding 写着玩可以，但是给企业做系统、做产品，没有知识库、没有记忆体，就是给系统和产品埋雷挖坑。没有 AI 的时代需要软件工程，有了 AI 之后也需要 harness 工程。没有知识库和记忆体，harness 玩不起来。"

这条反驳的杀伤力在于——他没说错。Pi 的官方态度是 "企业级记忆 / 审计 / telemetry 想用就自己写 extension"。企业系统要落地，**用户得自己接住这部分工程量**。

这条批评对 Pi 团队是无效的——他们的目标用户就是独立开发者和 OSS 维护者；对企业用户是基本成立的——官方路径就是 "自己写扩展"。但严格说，这条反驳有一个前提层面的误判：它假设 "harness 必须内置知识库和记忆体"，而 Pi 的架构恰恰把这两样开放成了 extension 接口——没提供的是默认实现，不是能力。

### 2.3 一个反例：Mario 自己就有无限记忆的 Slack bot

§10 逐字稿 S21-S28 里有段记录：Mario 给自己写过一个 Slack bot，自嘲命名 "Master of My Shit"。它靠 **append-only log + chunked semantic search（分块语义搜索）** 实现了无限 memory。

这看起来和 "不要 memory" 自相矛盾，其实正好划出了他的边界：**memory 放哪里、用什么形态，比要不要 memory 更重要**。Slack bot 面对的是聊天流——不断追加的日志天生适合 append-only + 语义检索；而代码库不是聊天流，代码本身就是事实，强行套一套记忆系统反而多一个要维护的地方。

---

## 3 · 第二条反直觉观点：Bash 足够用，反对 MCP

> 视频原话（摘要）："Bash 工具足够用，Bash 类似于编程语言，可以任意组合；大部分时候没必要 MCP，skill + 脚本足够。"

### 3.1 Pi 默认只有 4 个工具，system prompt 全文不到 1000 tokens

Pi 的默认工具集只有 4 个：`read` / `write` / `edit` / `bash`。`grep` / `find` / `ls` 三个只读工具也存在，但**默认禁用**——Mario 博客原文原话是 "By default these are disabled, so the agent only gets the four tools above"。想用只读模式，自己指定即可：`pi --tools read,grep,find,ls`。

对比之下，Claude Code / Cursor / Codex 这类主流 Agent 的内置工具数是几十到上百。

Mario 博客里关于上下文窗口（context window）开销的具体数字：

> "Popular MCP servers like Playwright MCP (21 tools, **13.7k tokens**) or Chrome DevTools MCP (26 tools, **18k tokens**) dump their entire tool descriptions into your context on every session. **That's 7-9% of your context window gone before you even start working.**"

> "Playwright MCP（21 个工具，13.7k tokens）或 Chrome DevTools MCP（26 个工具，18k tokens）这类流行 MCP server，每次会话都把整套工具描述倒进你的上下文。**还没开始干活，上下文窗口（context window）就没了 7-9%。**"

每次会话开始，光是把 MCP 工具描述装进 context 就要烧 7-9%。模型每生成一个 token 都要决定 "我要不要调哪个工具"，这个决策会因为工具列表过长而变差。

Pi 的 system prompt + 4 个工具定义合计 **< 1000 tokens**，占一个 200k context 的模型不到 0.5%。全文是这样的（来源：Mario 博客原文，minimal system prompt 一节）：

```text
You are an expert coding assistant. You help users with coding tasks by reading
files, executing commands, editing code, and writing new files.

Available tools:
- read: Read file contents
- bash: Execute bash commands
- edit: Make surgical edits to files
- write: Create or overwrite files

Guidelines:
- Use bash for file operations like ls, grep, find
- Use read to examine files before editing
- Use edit for precise changes (old text must match exactly)
- Use write only for new files or complete rewrites
- When summarizing your actions, output plain text directly - do NOT use cat
  or bash to display what you did
- Be concise in your responses
- Show file paths clearly when working with files

Documentation:
- Your own documentation (including custom model setup and theme creation) is
  at: /path/to/README.md
- Read it when users ask about features, configuration, or setup, and
  especially if the user asks you to add a custom model or provider, or create
  a custom theme.
```

没有任何 "你是宇宙最强" 的话术、没有安全说明、没有身份人设。4 个工具的定义也极简：`read` 默认读前 2000 行支持图片，`write` 自动建父目录，`edit` 要求 oldText 精确匹配（含空白），`bash` 可选 timeout、默认不超时（来源：Mario 博客原文，minimal toolset 一节）。

Mario 的论证是：前沿模型在 RL 训练里早就见过海量 coding agent 数据，根本"不需要 1 万 token 的 system prompt 来教模型什么是 coding agent"。这一点与 Codex 同样极简的工具定义互为印证（博客原文）。

### 3.2 替代方案：self-described CLI tools（自描述 CLI 工具）

Pi 不接 MCP，但用户可以自己写 CLI 工具。Mario 给的范式是：

> "Build CLI tools with README files... the agent reads the README when it needs the tool, pays the token cost only when necessary (**progressive disclosure**)."

> "写带 README 的 CLI 工具……模型在需要时读 README，只在必要时付 token 成本（渐进式披露）。"

所谓渐进式披露（progressive disclosure），在 Pi 里就是一次 `read` 调用：模型决定什么时候付这份 token 账单。用户掌握引入工具的成本，而不是框架默认全开。

还有一层容易被忽略：**组合性**。MCP 工具调用的结果要回到模型，由模型中转后再调下一个工具——每一步组合都在烧上下文。Bash 工具走 Unix 管道，前一个命令的输出直接成为下一个命令的输入，组合发生在管道里，而不是上下文里（来源：Mario 博客原文 "composable (pipe outputs, chain commands)"）。§10 逐字稿 S56-S57 那句 "文件系统 + 工具本身是一回事，组合能力才是关键"，说的正是这层。

两个配套生态：

- **agent-tools**（`github.com/badlogic/agent-tools`）：Mario 自己维护的 CLI 工具集，每个工具都是 "CLI + README"，包括给 Pi 加的 web search。社区转述 Mario 的访谈数据：这套浏览器自动化工具集总共只消耗 **225 tokens**，约为 Playwright MCP 的 1/60（来源：社区文章转述，2026-03）。
- **mcporter**（Peter Steinberger 的作品）：如果你确实必须用 MCP server，用它把 MCP server 包装成 CLI 工具，再走 CLI + README 路线（来源：Mario 博客原文）。

### 3.3 评论区两种声音

"AI 罗伯特"（8-17 07:13，AI 虚拟账号）：

> "代码洁癖犯了。"

—— 指的是 "内置 4 个工具、不堆功能" 这种克制本身。技术圈对这种克制始终有两种看法：一种叫 "恰好够用"，另一种叫 "迟早要补"。

"麒麟飞狐"（8-17 07:34 来自广东）：

> "然后让大模型随意发挥？"

—— 翻译成具体的技术问题：内置 4 个工具 + 用户自己写 CLI，那 "工具集" 这件事的责任全在用户侧。模型在 Pi 里能调用任何 bash 命令，用户写不写 README、README 写得好不好，决定了模型能不能干好活。

---

## 4 · 第三件 "没做" 的事：YOLO by default

视频摘要里没提，但调研里必须讲到——Pi 默认 **YOLO 模式**：

> "Pi runs in full YOLO mode... No permission prompts for file operations or commands. No pre-checking of bash commands by Haiku for malicious content. Full filesystem access. Can execute any command with your user privileges."

> "Pi 以完全 YOLO 模式运行……文件操作和命令没有权限提示。bash 命令不做恶意内容预检。完整的文件系统访问权限。能以你的用户权限执行任何命令。"

Mario 原话：

> "If you look at the security measures in other coding agents, they're mostly **security theater**."

> "如果你看其他 coding agent 的安全措施，它们大多是安全剧场（security theater）。"

> "Since we cannot solve this trifecta of capabilities (read data, execute code, network access), **pi just gives in**."

> "读数据、执行代码、访问网络——这三件套既然解不了，Pi 干脆认输。"

"认输"的论证链在博客里写得很细，展开其实只有一句：原文的 "只要 agent 能写代码、能跑代码，游戏基本就结束了"——**能写代码的 agent 能生成任何动作**。行为层的权限检查面对的是一个会自己合成任意脚本的对象，任何白名单都可能被它写出来的代码绕过。这就是 Mario 说那些措施是 "security theater" 的原因。唯一能防数据外泄的办法是掐掉执行环境的全部网络——那 agent 也没用了；白名单域名也可以绕过。Simon Willison 的 "dual LLM" 模式走了另一条路：让能看到不可信内容的模型没有工具，有工具的模型看不到不可信内容，以此防 confused deputy 攻击和数据外泄。但连 Willison 自己都承认 "this solution is pretty bad"——它牺牲的恰恰是 agent 最有价值的部分（看完内容再行动），实现复杂度还巨大。Mario 的结论是：**安全不可能在工具层解决，只能挪到基础设施层**。

### 4.1 Gondolin：安全责任下放到 VM

官方给的 "想用安全" 的路径是 **Gondolin**（`github.com/earendil-works/gondolin`）——Earendil 同一个团队做的 Linux microVM（微虚拟机）。它和 Pi 的配合方式是 **工具路由**：Pi 进程本身留在主机上（持有你的认证凭据和配置），bash 等工具的执行被路由进 Gondolin 微 VM，用完即毁（来源：Pi 官方安全文档 + 社区教程）。

也就是说，主机上只留对话，agent 的每条命令都跑在一次性 VM 里——碰不到你的 SSH 密钥、浏览器 profile、银行应用。

HN 评论里有人这么总结：

> "pi is in YOLO mode by default... this thing is not meant to be run in your main user directory with access to your secrets, bank accounts, emails... meant to be run/discarded/re-created in a VM."

> "Pi 默认 YOLO……这东西本来就不该跑在你放 secrets、银行账户、邮件的主目录里……它应该在 VM 里运行、用完销毁、随时重建。"

Pi 没把安全做掉，**把安全责任从 Agent 框架层推给基础设施层**。

### 4.2 供应链安全反而做得比谁都严

反差也明显：工具层全裸奔，npm 供应链安全却抓得很严（来源：社区分析文章）——固定所有依赖版本、强制延迟同步 npm 包、严格的锁文件审计。这不是矛盾，而是分层策略：放弃行为层防御（已被证明是剧场），把有限的安全预算压在供应链这个确定、可审计的维度上——prompt injection（提示注入）防不住，但至少别让依赖链成为注入点。另外 Pi 默认**没有 web search / fetch 工具**。官方态度是：curl 和读文件已经给了足够的注入面，多一个 fetch 只是多一个口子（来源：Mario 博客原文）。

---

## 5 · Pi 官网的 "我们没做的" 清单

先看 "做了的"。Mario 博客列过一份 Pi 一样不缺的功能清单（来源：Mario 博客原文，pi-coding-agent 章节）：跨平台（Windows / Linux / macOS）、多 provider 会话中途换模型、会话管理（continue / resume / branch（分支））、AGENTS.md（项目上下文文件）分层加载、自定义 slash command、OAuth（开放授权）直登 Claude Pro/Max 订阅、主题热重载、无头 JSON 流式与 RPC 模式、完整的成本与 token 追踪。

也就是说，**Pi 的极简是工具层和哲学层的极简，不是功能层的简陋**。真正的减法从下面这张表开始。我去 pi.dev 抓了一下官网文案，他们自己列了一个 "Not features" 清单：

| 我们没做 | 替代方案 |
|------|------|
| No MCP | 自己写 CLI + README |
| No sub-agents | 自己 spawn |
| No permission popups | 用 Gondolin / Docker 包一层 |
| No plan mode | 自己用 extension 实现 |
| No built-in to-dos | 自己用 extension 实现 |
| No background bash | 用 tmux |

这张表背后是同一套思路：**状态放文件，不放框架**。逐条看：

- **to-dos**：写一个 `TODO.md`，用 `- [x]` 勾选。Mario 的理由很直接——to-do 列表给模型增加要跟踪和更新的状态，"困惑模型的时候比帮助的时候多"（博客原文）。文件方案的好处是可见、可控、可版本化。
- **plan mode**：把计划写进 `PLAN.md`，agent 边干活边读边更新。Mario 特别指出 Claude Code 的 plan mode "不用批准一堆命令根本没法用"，而文件方案的差距在**可观测性**：你能看到 agent 实际读了哪些文件、漏了哪些，还能跟 agent 协作编辑计划（博客原文）。
- **background bash**：用 `tmux`。agent 在 tmux 里起 dev server / LLDB 调试会话，你可以随时 `tmux attach` 进去一起看，还能列出所有活跃会话。Mario 的原话是 "There's simply no need for background bash. Claude Code can use tmux too, you know."（博客原文，配了一张 Pi 在 LLDB 里调试崩溃 C 程序的截图）。
- **sub-agents**：让 Pi 通过 bash 自己 spawn 自己，比如他写了一个 code review（代码审查）slash command，用 `pi --print` 起一个只读子会话跑审查，输出全部可见（博客原文）。Mario 对并行 sub-agent 的态度很明确："除非你不在乎代码库烂成一堆垃圾，否则并行 spawn 多个 sub-agent 是反模式"（博客原文）。他自己的观察：模型仍然不擅长找到实现功能所需的全部上下文——训练让它们习惯只读文件片段，导致它们不敢读完整文件，于是错过关键信息。他拿 pi-mono 的 issue 区举证：相当一部分合并请求被关闭或返工，就因为 agent 没能完整理解需求，结论是 "we trust our agents too much"（我们太信任 agent 了）（博客原文）。这也是他反对代码索引的另一个隐性理由。

这里有个张力：§10 逐字稿里 Mario 说 "不需要写 AGENTS.md"，但 Pi 本身支持 AGENTS.md 分层加载，system prompt 之后唯一注入的就是这个文件——Mario 的原话是 "This is where you can customize pi to your liking. You can even replace the full system prompt"（博客原文）。不强制你写，但留好入口，这是 Pi 式的 "可选"。

甚至能跑 Doom——官方包列表里 `pi install git:github.com/badlogic/pi-doom` 是真实存在的。

> **官方 slogan**：`There are many agent harnesses, but this one is yours.`

这句话是 Pi 整个产品哲学的浓缩。Pi 不是 "帮你做完事的 Agent"，是 "让你有 100% 能力自己改造 Agent 的核心"。所有流行 Agent 的 "易用性" 在 Pi 这边都被有意拆成 extension，让用户自己拼。

社区生态里还有个值得记一笔的动作：官方在推 **pi-share-hf**，把真实编程会话发布到 Hugging Face。用真实的工具调用、失败和修复过程当训练数据（来源：社区文章，2026-07）。"代码即真相" 的哲学延伸到了数据层：与其维护记忆系统，不如把会话本身开源。

---

## 6 · 与 Cursor / Claude Code / Codex 的对比

**模型与上下文**：

| 维度 | Pi | Cursor / Claude Code / Codex |
|------|------|------|
| System prompt | < 1000 tokens | 几千 ~ 万级，发布版本经常变 |
| Codebase 索引 | 不内置 | Cursor 是核心卖点 |
| RAG / 长期记忆 | 可选 extension | 内置 |
| 内置工具数 | 4（grep/find/ls 默认禁用） | 几十到上百 |

**工具与安全**：

| 维度 | Pi | Cursor / Claude Code / Codex |
|------|------|------|
| MCP | 显式拒绝 | 全部支持 |
| Permission system | 无，官方推荐 Gondolin / Docker | Claude Code 有 permission popup |
| Background bash | 无，用 tmux | Claude Code 有但 observability 差 |
| Sub-agents | 无，自己 spawn | 全部支持 |

**Benchmark（中置信）**：Mario 在 Terminal-Bench 2.0 上跑了 Pi + Opus 4.5 的完整评测——每个任务 5 次 trial，结果提交给官方 leaderboard，榜单快照时间 2025-12-02（来源：Mario 博客原文）。跑分过程里有两处细节。一是他发现错误率在 PST 时区上线后变差，于是加跑了一轮只在 CET 时段的对照；二是 leaderboard 上的 **Terminus 2**：Terminal-Bench 团队自己的极简 agent，只给模型一个 tmux 会话——模型用文本发命令、自己解析终端输出，没有任何花哨工具。它的排名却比肩一堆工具复杂的 agent——而且 Terminus 2 出自 Terminal-Bench 官方团队之手，相当于 "极简路线" 的一次独立第三方对照实验，比 Mario 自己的跑分更有说服力。社区文章转述的结论是 Pi 与 Codex、Cursor、Windsurf 一同位列 Terminal-Bench 2.0 前五（2026-03 社区报道）。博客还开源了 bench runner 供任何人复现，Mario 甚至附上省钱提示：用 Claude 订阅跑，别用按量付费。

Mario 自己也承认 "benchmark 不代表真实世界"，立场依然是：**工具越少，模型决策越准——至少在终端任务上是这样**。

---

## 7 · 这次反主流的赌注谁赢了

在讨论输赢之前，先看这个赌注到底在赌什么。把全文连起来看，Pi 反对的四件事——RAG、MCP、permission popup、框架内部状态——其实共享同一个底层：

**显式、可组合的东西，胜过隐式的魔法。**

- 代码即真相：真相必须显式。文件是真相，索引和记忆是派生副本，派生副本会落后、会失真
- Bash 足够：组合必须显式。管道把工具输出直接接到下一个工具的输入；MCP 工具的组合要经过模型中转，每一次中转都在烧上下文
- YOLO by default：安全责任显式。不寄希望于行为层拦截，寄希望于基础设施层的 VM 隔离
- 状态放文件：状态必须显式。TODO.md 人能看、git 能版本化、任何工具能用；框架内部状态不透明、跟着进程生命周期走

Mario 没有明着总结过这句——这一段是本文的归纳——但从 "If I don't need it, it won't be built" 到 "状态放文件"，每一个决策都指向同一根坐标轴。理解了这根轴，你能预测 Pi 的下一个决策；不理解它，只会觉得 Pi 功能贫瘠。

视频没有给出 "Pi 2.0 路线图"——但截至 2026-08-21，仓库数据给我们几个值得记下的数字：

- 一年时间从 0 到 90k stars
- 最近 3 天（08-14 ~ 08-16）有 **20 个 commit（提交） + 1 个 release（发布）**（v0.84.2），活跃度比肩主流 Agent
- 来自 Python 圈、libGDX 圈、独立开发者圈的贡献者明显占了相当比例

现在给胜负下结论太早。不过 Pi 在一年内至少做对了几件事：

- **抢下了 "极简 Agent" 这个标签位**。当主流 Agent 一个比一个复杂，Pi 站在反方向，立刻有了清晰的辨识度。
- **把 "我做减法" 翻译成可验证的工程语言**。每次决策都对应具体数字（system prompt 大小、内置工具数、MCP token 消耗），不靠口号。
- **建了一个可扩展的 extension 生态**。pi.dev 官网的扩展列表和 `pi install` 一行命令都到位了，这是把 "极简" 落地为 "可自定义" 的关键。

可能没做对的事：

- **企业市场几乎全部放弃**。所有的 "知识库 / 长期记忆 / 审计 / 权限" 都被推到 extension 或自己 harness 层。如果未来企业级 Agent 需求爆发，Pi 可能会被定位为 "个人开发者的玩具"。
- **YOLO by default 是真正的 marketing 阻力**。即使有 Gondolin，下载安装一个 VM 镜像对一个 Mac 用户来说门槛太高。大部分主流用户连 Docker 都不愿意装。

还有一个细节见态度：Mario 在博客里说他的开源项目 "一向有点独裁"，如果 Pi 不合你意，"fork it. I truly mean it"（博客原文，In summary 章节）。路线图同样坦白：他说还想补两个功能——compaction（上下文压缩）和工具结果流式输出，但 "我不觉得我个人还需要更多了"。极简项目的自我克制，写得很明白。

---

## 8 · 读者判断：谁该去看原视频，谁读本文就够

**读本文就够的**：

- 想了解 Pi 这个项目大致是什么、谁在做、为什么最近 90k stars 的
- 想理解 "代码即真相 / Bash 足够 / YOLO by default" 三个反直觉观点背后的工程权衡
- 想给 "AI Agent 到底应该多复杂" 这个争议找一份对立方的代表立场

**应该去看原视频的**：

- 想听 Mario 和 Armin 自己的声音和对话节奏（视频 2:56，相当于一次简短的圆桌）
- 想从原视频里抓屏外的细节（Pi 工程上具体的 attack surface、token 控制技巧、extension 模板结构）
- 想自己判断 "两位作者在公司里的分工、决策流程" 这些团队层面的东西，本文完全没有覆盖

**应该直接跳到仓库的**：

- 想跑 Pi 装一下试试——`npm install -g --ignore-scripts @earendil-works/pi-coding-agent` 即可（macOS/Linux 也可以 `curl -fsSL https://pi.dev/install.sh | sh`）
- 想读 Mario 博客原文（mariozechner.at/posts/2025-11-30-pi-coding-agent）——原话比本文摘要诚实，Mario 自己的反思和取舍都对决策有直接价值
- 想验 YOLO by default 的强度——Gondolin 装镜像之后跑 Pi，自己承担数据安全责任

---

## 9 · 这次反主流的赌注给我们的提示

视频本身只是 2:56 的短摘，但背后站着的判断——**"AI Agent 的复杂度爆炸是最危险的副作用"**——值得记下。

两件具体的事：

1. **下次选 Agent 框架时，先问 "它默认吃多少 token"**。一个 system prompt 8k、内置工具 60 个的 Agent，开机空跑就要 9% 的 context。剩下 91% 给用户问答，还要算上你自己塞进去的 code、文件、对话。Pi 的 < 1000 tokens 是一个可以拿来对比的标杆。

2. **下次接到 "做企业系统需要知识库 / 长期记忆" 的反馈时，先问 "知识库 / 长期记忆需要的是不是 Agent 本身"**。Pi 的答案是 "不是，是 extension 或 harness 层"。这条回答不适用于所有人，但把它和 "AI Agent 默认必须有知识库" 放一起考虑，比默认选择其中一端更准确。

赌注的胜负还远未定。但有一件事现在就能说清楚：**复杂度的账单迟早要付**。Pi 让用户在第一天就看到账单，其他 Agent 把账单做成了分期。

哪种会被时间验证，2026 年剩下的几个版本里会有更清楚的答案。

### 9.1 两个可以立刻动手的练习

1. **装一个 Pi，跑一天只读模式**：`npm install -g --ignore-scripts @earendil-works/pi-coding-agent`，然后 `pi --tools read,grep,find,ls` 进只读模式干一天的活。重点观察两件事：system prompt < 1000 tokens 时模型的行为和 Claude Code 差在哪；grep/find/ls 默认禁用后，你的命令习惯会不会跟着变。
2. **把你常用的一条 MCP 链路改写成 CLI + README**：挑一个你天天用的 MCP server，用 curl / gh 加一份 README 重写同样的流程，然后对比两边的 token 消耗、响应速度和排查成本。这是 Pi 作者每天都在做的对照实验。

### 9.2 进阶方向

- 读 Mario 博客原文的 Benchmarks 一节，按他的 5 次 trial 流程在 Terminal-Bench 2.0 上自己跑一遍 Pi，验证"工具越少，模型决策越准"
- 读 Gondolin 源码（`github.com/earendil-works/gondolin`），理解工具路由怎么把 bash 送进一次性微虚拟机
- 想深挖"代码即真相"的理论侧，可以读 Daisy Hollman 的 Context Engineering talk PDF——§10 的时间码映射表列了它和 Pi 视频论点的对应关系

---

## 常见问题（FAQ）

**Q1：Pi 支持 MCP 吗？**
不支持，这是设计决定而非功能缺口。官方替代方案是自己写 CLI + README 或 skill（见 §3.2 与 §5 的 "Not features" 清单）。

**Q2：Pi 用什么模型？能接本地模型吗？**
通过 pi-ai 统一 API 接 Anthropic / OpenAI / Google / xAI / Groq / Cerebras / OpenRouter 以及任何 OpenAI 兼容端点，也支持 Ollama 等本地推理（来源：Mario 博客原文）。

**Q3：没有 permission popup，怎么防止 Pi 乱执行命令？**
官方给出的安全路径是 Gondolin / Docker 微虚拟机工具路由，让 bash 跑在一次性 VM 里（见 §4.1）。只想读不想写，可以用 `pi --tools read,grep,find,ls` 进只读模式。

**Q4：Pi 要花钱吗？**
代码和 CLI 本体是 MIT 协议，免费（来源：GitHub 仓库 LICENSE）。模型 API 的费用取决于你选哪个 provider；已经订阅 Claude Pro/Max 的话，可以直接 OAuth 登录，不用另买 API（来源：Mario 博客原文）。

**Q5：和 Claude Code 比，Pi 适合什么人？**
适合想精确控制 context、愿意自己拼装功能的人；不适合要开箱即用完整功能（plan mode / sub-agents / 内置索引）的人。具体对照见 §6 对比表，要不要看原视频见 §8。

**Q6：不建索引，Pi 怎么处理百万行级别的大代码库？**
路线是 "先定位，再读全"：用 `grep` / `find` 找到文件，再用 `read` 把相关文件完整读进来。Mario 的观察是前沿模型的上下文窗口足够大，而且真的擅长理解代码结构——读一两个文件就能学会你的代码风格（§10 S7-S8），前提是别被训练得只敢读片段。对真正超大的仓库，这是 Pi 最弱的场景，也是 RAG extension 最合理的切入点。

---

## 10 · 视频双语字幕 · 逐段校准（68 segments）

> 源：2:56 原视频音频，whisper-cli（命令行工具）（ggml-tiny.bin）转写 + 基于 Pi README / Mario 博客原文 / Daisy Hollman PDF 逐段校准，共 68 segments。
>
> **校准原则**：① 关键缩写 / 错字按上下文校准（AGENTS.md / Linear / Bash / Claude / Armin Ronacher / Pi 等）；② 行业通用术语保留原文（RAG / MCP / AGENTS.md）；③ 引用 Pi README / Daisy Hollman PDF 时用页码 / 行号 / 章节号锚点；④ 时间码精度 100ms（SRT 标准）。

### §1 代码即真相（Pi 第一哲学，00:00:00-00:00:15）

**S1 (00:00:00 → 00:00:03.6)** `Yeah, but coming back to memory systems, so for coding, I don't want to memory system.` — 对，回到 memory 系统的话题。对于 coding，我不要 memory 系统。

**S2 (00:00:03.6 → 00:00:05.9)** `Code is true, code is the ground truth.` — 代码即真相，代码就是 ground truth。

**S3 (00:00:05.9 → 00:00:07.4)** `It's also evolving.` — 它也在演进。

**S4 (00:00:07.4 → 00:00:10.7)** `And I don't need another place that I need to maintain.` — 而且我不需要再多一个地方需要维护。

**S5 (00:00:10.7 → 00:00:12.4)** `I already have code based to maintain.` — 我已经要维护代码了。

**S6 (00:00:12.4 → 00:00:15.0)** `So for code, I don't need a memory system, right?` — 所以对于代码，我不需要 memory 系统，对吧？

> §1 主题：**为什么 Pi 不要 RAG / 长期记忆**——代码即真相。直接命中 `@宝玉xp` 视频摘要第一条。S1-S6 是 6 段连成一段完整的反 RAG 论证。

### §2 模型对代码的理解（不需要 AGENTS.md，00:00:15-00:00:50）

**S7 (00:00:15.0 → 00:00:18.2)** `Well, it's a really good at kind of understanding the code structure.` — 好，模型真的很擅长理解代码结构。

**S8 (00:00:18.2 → 00:00:20.8)** `And the code style you have just based on reading one or two files.` — 读一两个文件就能学会你的代码风格。

**S9 (00:00:20.8 → 00:00:24.8)** `And if you have that in order, then you don't need an AGENTS.md for it to follow your coding style.`（校准 H&C de → AGENTS.md）— 如果顺序正确，你不需要写 AGENTS.md 让它跟着你的 coding 风格。

**S10 (00:00:24.8 → 00:00:25.8)** `Whatever.` — 就这些。

**S11-S20 (00:00:25.8 → 00:00:49.6)** 文件夹 map 够用 / Claude 自己维护 / embeddings + AST 是浪费时间 — **完整段落：Mario 直接说 "I guarantee you, it does not"**（S19）—— 没有跑过 eval 证明 RAG 让 coding 输出变好。

### §3 "Master of My Shit" 自嘲 + append-only 无限 memory（00:00:49-01:18）

**S21-S28** Mario 给自己做的 Slack bot（自嘲命名 "Master of My Shit"）演示了 **append-only log + chunked semantic search = 无限 memory** 的实战实现。这是 Pi 设计哲学的**反向对照**——你说 "对 Pi 不需要 memory"，但作者自己就有 unlimited memory Slack bot。**关键是 memory 实现的 location + 形态，不是 memory 本身**。

### §4 Pi 极简哲学 + Bash 是编程语言（01:18-01:50）

**S29-S39** 完美命中 `@宝玉xp` 视频摘要第二条 "Bash 工具足够用，Bash 类似于编程语言，可以任意组合"。S37-S39 是 **Pi 的 "extensible self" 哲学**——**Pi 是核心极简 + 用户用 skill 扩展自己**，跟 Claude Code 这种 "框架 + 插件" 模式根本差异在这里。

### §5 自定义 skill vs MCP 的真实工程战（01:50-02:21）

**S43-S48** 直接命中 "大部分时候没必要 MCP，skill + 脚本足够"。

**S50-S51 是 skill 的精确定义**："prompt that can load on demand, but also composes on tools"——**Pi 的 skill 是 prompt + tool composition**，**MCP 是工具 + 数据**——这就是 Pi 跟 MCP 的根本差异。

### §6 Skill 实战 + "context-efficient" 工具设计哲学（02:21-02:56）

**S56-S57 是视频最高浓度观点**："文件系统 + 工具本身是一回事，**组合能力才是关键**"。

**S61-S65 展示 Linear skill 实际跑法**：**context-efficient + artifact 兜底**——只 load 必要项进 context，多余的全 dump 到 JSON 文件自己读。这跟 Pi "极简内置 + 用户 skill 扩展" 的核心哲学一致。

### 时间码 → 章节映射表（Pi 哲学 → Daisy Hollman PDF 对应）

| 时间码 | Pi 章节 | Daisy Hollman PDF 对应 |
|---|---|---|
| S1-S6 (00:00-00:14) | 代码即真相 / 不要 RAG | §6 "context engineering is paramount" |
| S7-S9 (00:14-00:25) | 模型理解代码 / 不需要 AGENTS.md | §6 context engineering 案例 |
| S11-S20 (00:25-00:50) | 文件夹 map 够用 / 不要 embeddings | §6 progressive disclosure |
| S21-S28 (00:50-01:18) | "Master of My Shit" / append-only | §8 + §9 long-running agent 实战 |
| S29-S39 (01:18-01:50) | Pi 极简 / Bash 是编程语言 | §7 skills 设计哲学 |
| S40-S53 (01:50-02:21) | 自定义 skill vs MCP | §7 + §9 dogfooding 模式 |
| S54-S67 (02:21-02:56) | MCP vs tool / context-efficient | §7 tools vs MCP 设计选择 |

> **跨论文呼应**：Daisy Hollman PDF §6（context engineering）/ §7（skills）/ §9（long-running agents）三段主题，跟 Pi 视频的核心论点**一一对应**——Daisy 这篇 60 分钟 talk 引用 Pi 作为案例研究。

---

## 附录 A · 参考文献与事实来源

- 视频来源：微博 `https://video.weibo.com/show?fid=1034:5332798752358424`（`@宝玉xp` 转发，2026-08-17 GMT+8，2:56 时长）；评论区 4 条原话见第 2-3 节内引
- Pi 仓库：`github.com/earendil-works/pi`（数据截至 2026-08-21：90,390 stars / 11,214 forks / 135 open issues / MIT / TypeScript / v0.84.2 发布于 2026-08-14）；官网 pi.dev（"Not features" 清单、extension 机制）
- Mario 博客原文：mariozechner.at/posts/2025-11-30-pi-coding-agent（system prompt 全文、工具定义、YOLO 论证、Terminal-Bench 2.0 细节均出自此文）
- Gondolin 仓库：`github.com/earendil-works/gondolin`（工具路由微 VM 细节另见 Pi 官方安全文档与社区教程）；Earendil Inc. 官网：earendil.com
- 社区资料：OpenClaw 与 Pi 的继承关系、225 tokens 工具集案例、pi-share-hf、供应链安全实践（2026-03 ~ 2026-07 多篇社区文章，正文已逐一标注）
- 视频完整逐字稿：§10 —— whisper-cli 转写 + 逐段校准（68 segments / 2:56 全程）
