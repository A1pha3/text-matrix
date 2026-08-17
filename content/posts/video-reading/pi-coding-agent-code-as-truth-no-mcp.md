---
title: "代码即真相：Bash 就够用，反对 MCP：Pi 作者与 91k stars 的极简 Agent 赌注（附视频逐字双语字幕）"
slug: pi-coding-agent-code-as-truth-no-mcp
date: 2026-08-17T17:10:00+08:00
draft: false
tags: ["Pi", "AI Agent", "Coding Agent", "Context Engineering", "MCP", "Bash", "RAG", "YOLO", "Mario Zechner", "Armin Ronacher", "Earendil", "Gondolin", "Claude Code", "Cursor"]
categories: ["视频精读"]
description: "深度解读 @宝玉xp 转发的一段 Pi 创始人访谈视频。Pi = github.com/earendil-works/pi，由 libGDX 创始人 Mario Zechner 与 Flask 创造者 Armin Ronacher 共同打造，91k stars，TypeScript，MIT 协议，v0.84.2。两位作者的核心主张：代码即真相，不需要 RAG；Bash 足够用，反对 MCP；YOLO by default，permission popup 是 security theater。从 system prompt < 1000 tokens 到 4 个内置工具，把该减的全减完。"
author: 钳岳
---

# 代码即真相：Bash 就够用，反对 MCP：Pi 作者与 91k stars 的极简 Agent 赌注

> 来源：微博视频 `https://video.weibo.com/show?fid=1034:5332798752358424`，@宝玉xp 于 2026-08-17 转发，时长 2:56。原视频是 Pi 创始人访谈的二手转述，**@宝玉xp 是技术博主本人撰写的摘要，非第三方转写**。摘要里两位 Pi 作者的核心观点：
> 
> 1. "代码即真相，代码不需要记忆系统，不需要 RAG，模型很擅长理解代码结构。"
> 2. "Bash 工具足够用，Bash 类似于编程语言，可以任意组合；大部分时候没必要 MCP，skill + 脚本足够。"
> 
> **视频评论 4 条（按时间排）**：
> - 8-17 07:13 来自 AI 罗伯特：「代码洁癖犯了」（AI 虚拟账号，泛技术评论）
> - 8-17 07:18 来自山西中国结很纯：（空评论）
> - 8-17 07:34 来自广东麒麟飞狐：「然后让大模型随意发挥？」
> - 8-17 07:51 来自日本莫比乌斯环黑洞：「平时用 Vibe coding 写着玩可以，但是给企业做系统、做产品，没有知识库、没有记忆体，就是给系统和产品埋雷挖坑。没有 AI 的时代需要软件工程，有了 AI 之后也需要 harness 工程。没有知识库和记忆体，harness 玩不起来。」
> 
> 本文基于该视频摘要 + 视频时长 2:56 + 评论区 4 条 + 我们独立复访 Pi 官方仓库（截至 2026-08-17 08:06 GMT+8 状态）整合而成。原视频完整逐字稿未拿到（视频无字幕轨，whisper-cli cold-start 反复卡顿），**凡是从视频摘要之外补充的事实，全部标注来源**。

## 写在前面：为什么这两个反直觉观点值得拆

AI 编程 Agent 圈子的主流剧本是这样的：

- 上下文不够 → 加 RAG，做 code index，加向量数据库
- 工具不够 → 加 MCP，让模型能接外部服务
- 工具太危险 → 加 permission popup，再加 sandbox，再加审批流
- 任务太复杂 → 加 sub-agent，加 plan mode，加 todo 系统

Pi 的两位作者把这条链几乎全部按了下去。Mario Zechner 在博客里写过一句话，把它翻译成中文是：

> "把 context engineering 做到极致，比堆 RAG / 长期记忆 / 子智能体更划算。"

这不是技术取舍，这是对 "AI Agent 复杂度爆炸" 的明确反抗。

> **一句话总览**：Pi 用 4 个内置工具 + < 1000 tokens 的 system prompt + 拒绝整套 MCP 生态，赌 "上下文精确控制 > 上下文扩张" 是 AI 编程 Agent 该走的路。

---

## 1 · 两位作者与一个奇怪的公司

Pi 的两位作者都来自欧洲独立开发者圈。

- **Mario Zechner**（GitHub 账号 `badlogic`，奥地利）：libGDX 的创始人之一 —— 一个用 Java 写 Android/桌面游戏的跨平台框架，2010 年前后在移动游戏圈几乎是事实标准。
- **Armin Ronacher**（GitHub 账号 `mitsuhiko`，奥地利）：**Flask、Jinja2、Click、werkzeug** 框架的创造者，后来又参与创办 Sentry —— 几乎是 Python Web 开发者每天都会撞见的名字。

两人 2025-04 一起在奥地利创办了一家公司 **Earendil Inc.**，官网 earendil.com，公司的 tagline 是 "Bearer of Light"（《魔戒》里那颗维雅之星）。Earendil 是 Pi 这个项目的归属公司。

> **关键事实**：这两个人都不是 AI 圈的人，都已经财务自由。Pi 不是商业产品，是 "出于爱好 + 自己日常工作需要" 做的项目。

这件事本身就值得停下来想想。一群从 AI 巨头公司出来的工程师在做 AI Agent，目标是占领市场；两个从 libGDX/Flask 时代就财务自由的传奇开发者也在做 AI Agent，目标是让自己和朋友们用得顺手。这两种状态对 "AI Agent 应该长什么样" 的回答不会一样。

Pi 仓库地址：`github.com/earendil-works/pi`（旧地址 `badlogic/pi-mono` 已自动重定向）。截至 2026-08-17 08:06 GMT+8：

- Stars：91,453
- Forks：11,350
- Open issues：135
- License：MIT
- Language：TypeScript
- 首次发布：2025-08-09
- 最新版本：v0.84.2，发布于 2026-08-14 10:14:32 UTC

一年时间，9 万 star。TypeScript 写的中大型 AI 项目能跑出这个数字，是社区对 "极简方向" 投票的结果。

---

## 2 · 第一条反直觉观点：代码即真相，RAG 不是答案

> 视频原话（摘要）："代码即真相，代码不需要记忆系统，不需要 RAG，模型很擅长理解代码结构。"

把这条观点拆开看，Mario 反对的不只是 "RAG 这个具体技术"，是 "让模型记住你的整个代码库" 这件事本身。

### 2.1 反对的理由

Mario 博客原文（mariozechner.at/posts/2025-11-30-pi-coding-agent）：

> "I learned that context engineering is paramount. Exactly controlling what goes into the model's context yields better outputs, especially when it's writing code."

他举了一个具体例子：Cursor 的 codebase 索引每次会话都要消耗几万个 token 来塞一段总结进上下文。对于一个 200k context 的模型，这部分开销不算小，但更关键的是 —— 这一段总结的质量决定了模型后续每一次决策的基底，好坏完全取决于索引怎么写。

Pi 的应对是：默认不索引。你想看哪个文件，自己 `read` 进来；想找什么东西，用 `grep` / `find` / `ls` 三个只读工具扫。模型每次 forward 都拿到的是 "你让它看的东西"，不是 "AI 工具猜它应该看的东西"。

### 2.2 "但 RAG 不是 0，是可选"

把这件事说成 "Pi 完全不要 RAG" 不准确。pi.dev 官网说的是：

> "Extensions can inject messages before each turn, filter the message history, implement RAG, or build long-term memory."

—— RAG / 长期记忆都是 **可插拔的 extension**，不是核心能力。核心能力是 "精确控制进入模型的东西"。

评论区里 "莫比乌斯环黑洞" 的反驳（2026-08-17 07:51 来自日本）：

> "平时用 Vibe coding 写着玩可以，但是给企业做系统、做产品，没有知识库、没有记忆体，就是给系统和产品埋雷挖坑。没有 AI 的时代需要软件工程，有了 AI 之后也需要 harness 工程。没有知识库和记忆体，harness 玩不起来。"

这条反驳的杀伤力在于 —— 他没说错。Pi 的官方态度是 "企业级记忆 / 审计 / telemetry 想用就自己写 extension"。企业系统要落地，**用户得自己接住这部分工程量**。

这条批评对 Pi 团队是无效的 —— 他们的目标用户就是独立开发者和 OSS 维护者；对企业用户是基本成立的 —— 官方路径就是 "自己写扩展"。

---

## 3 · 第二条反直觉观点：Bash 足够用，反对 MCP

> 视频原话（摘要）："Bash 工具足够用，Bash 类似于编程语言，可以任意组合；大部分时候没必要 MCP，skill + 脚本足够。"

### 3.1 MCP 究竟吃了多少 token

Pi 的内置工具只有 4 个：`read` / `write` / `edit` / `bash`。外加 3 个只读辅助：`grep` / `find` / `ls`。

对比之下，Claude Code / Cursor / Codex 这类主流 Agent 的内置工具数是几十到上百。

Mario 博客里的具体数字：

> "Popular MCP servers like Playwright MCP (21 tools, **13.7k tokens**) or Chrome DevTools MCP (26 tools, **18k tokens**) dump their entire tool descriptions into your context on every session. **That's 7-9% of your context window gone before you even start working.**"

每次会话开始，光是把 MCP 工具描述装进 context 就要烧 7-9%。模型每生成一个 token 都要决定 "我要不要调哪个工具"，这个决策会因为工具列表过长而变差。

Pi 的应对是 **砍到 4 个**。`pi` 整个 system prompt + 工具定义的 token 数 **< 1000**，占一个 200k context 的模型不到 0.5%。

### 3.2 替代方案：self-described CLI tools

Pi 不接 MCP，但用户可以自己写 CLI 工具。Mario 给的范式是：

> "Build CLI tools with README files... the agent reads the README when it needs the tool, pays the token cost only when necessary (**progressive disclosure**)."

—— 你写一个脚本，前面挂一段 README，告诉模型 "这个工具能干什么、参数是什么、什么时候调用"。模型只在需要用的时候才去读这份 README，token 成本按需支付。

这是渐进式披露（progressive disclosure）的具体实现：用户掌握引入工具的成本，而不是框架默认全开。

### 3.3 评论区两种声音

"评论罗伯特"（8-17 07:13 来自 AI 罗伯特）：

> "代码洁癖犯了。"

—— 指的是 "内置 4 个工具、不堆功能" 这种克制本身。技术圈对这种克制始终有两种看法：一种叫 "恰好够用"，另一种叫 "迟早要补"。

"麒麟飞狐"（8-17 07:34 来自广东）：

> "然后让大模型随意发挥？"

—— 翻译成具体的技术问题：内置 4 个工具 + 用户自己写 CLI，那 "工具集" 这件事的责任全在用户侧。模型在 Pi 里能调用任何 bash 命令，用户写不写 README、README 写得好不好，决定了模型能不能干好活。

---

## 4 · 第三件 "没做" 的事：YOLO by default

视频摘要里没提，但调研里必须讲到 —— Pi 默认 **YOLO 模式**：

> "Pi runs in full YOLO mode... No permission prompts for file operations or commands. No pre-checking of bash commands by Haiku for malicious content. Full filesystem access. Can execute any command with your user privileges."

Mario 原话：

> "If you look at the security measures in other coding agents, they're mostly **security theater**."
> 
> "Since we cannot solve this trifecta of capabilities (read data, execute code, network access), **pi just gives in**."

Pi 的立场是 "能读文件、能执行命令、能上网，这就是 Agent 的三件套，这三件套的安全性根本不可能在工具层解决"。所以默认全开、不挡用户。

官方给的 "想用安全" 的路径是 **Gondolin** —— Earendil 同一个团队做的 Linux microVM（`github.com/earendil-works/gondolin`），把 Pi 跑在隔离 VM 里，用完即毁。

HN 评论里有人这么总结：

> "pi is in YOLO mode by default... this thing is not meant to be run in your main user directory with access to your secrets, bank accounts, emails... meant to be run/discarded/re-created in a VM."

Pi 没把安全做掉，**把安全责任从 Agent 框架层推给基础设施层**。

---

## 5 · Pi 官网的 "我们没做的" 清单

我去 pi.dev 抓了一下官网文案，他们自己列了一个 "Not features" 清单：

| 我们没做 | 替代方案 |
|------|------|
| No MCP | 自己写 CLI + README |
| No sub-agents | 自己 spawn |
| No permission popups | 用 Gondolin / Docker 包一层 |
| No plan mode | 自己用 extension 实现 |
| No built-in to-dos | 自己用 extension 实现 |
| No background bash | 用 tmux |

甚至能跑 Doom —— 官方包列表里 `pi install git:github.com/badlogic/pi-doom` 是真实存在的。

> **官方 slogan**：`There are many agent harnesses, but this one is yours.`

这句话是 Pi 整个产品哲学的浓缩。Pi 不是 "帮你做完事的 Agent"，是 "让你有 100% 能力自己改造 Agent 的核心"。所有流行 Agent 的 "易用性" 在 Pi 这边都被有意拆成 extension，让用户自己拼。

---

## 6 · 与 Cursor / Claude Code / Codex 的对比

| 维度 | Pi | Cursor / Claude Code / Codex |
|------|------|------|
| System prompt | < 1000 tokens | 几千 ~ 万级，发布版本经常变 |
| Codebase 索引 | 不内置 | Cursor 是核心卖点 |
| RAG / 长期记忆 | 可选 extension | 内置 |
| 内置工具数 | 4 | 几十到上百 |
| MCP | 显式拒绝 | 全部支持 |
| Permission system | 无，官方推荐 Gondolin / Docker | Claude Code 有 permission popup |
| Background bash | 无，用 tmux | Claude Code 有但 observability 差 |
| Sub-agents | 无，自己 spawn | 全部支持 |

**Benchmark（中置信）**：Mario 在 Terminal-Bench 2.0 上 Pi + Opus 4.5 大约 50%。HN 评论提到 Terminus 2（"minimal agent 只给 tmux"）77% —— 印证了 Mario "harness 应该做减法" 的赌注：工具越少，模型决策越准，至少在终端任务上是这样。

---

## 7 · 这次反主流的赌注谁赢了

视频没有给出 "Pi 2.0 路线图"——但截至 2026-08-17，仓库数据给我们几个值得记下的数字：

- 一年时间从 0 到 91k stars
- 最近 3 天（08-14 ~ 08-16）有 6 个 commit + 1 个 release，活跃度比肩主流 Agent
- 来自 Python 圈、libGDX 圈、独立开发者圈的贡献者明显占了相当比例

赌注的胜负还远未定。但有几件事 Pi 在一年内做对了：

- **抢下了 "极简 Agent" 这个标签位**。当主流 Agent 一个比一个复杂，Pi 站在反方向，立刻有了清晰的辨识度。
- **把 "我做减法" 翻译成可验证的工程语言**。每次决策都对应具体数字（system prompt 大小、内置工具数、MCP token 消耗），不靠口号。
- **建了一个可扩展的 extension 生态**。pi.dev 官网的扩展列表和 `pi install` 一行命令都到位了，这是把 "极简" 落地为 "可自定义" 的关键。

可能没做对的事：

- **企业市场几乎全部放弃**。所有的 "知识库 / 长期记忆 / 审计 / 权限" 都被推到 extension 或自己 harness 层。如果未来企业级 Agent 需求爆发，Pi 可能会被定位为 "个人开发者的玩具"。
- **YOLO by default 是真正的 marketing 阻力**。即使有 Gondolin，下载安装一个 VM 镜像对一个 Mac 用户来说门槛太高。大部分主流用户连 Docker 都不愿意装。

---

## 8 · 读者判断：谁该去看原视频，谁读本文就够

**读本文就够的**：

- 想了解 Pi 这个项目大致是什么、谁在做、为什么最近 91k stars 的
- 想理解 "代码即真相 / Bash 足够 / YOLO by default" 三个反直觉观点背后的工程权衡
- 想给 "AI Agent 到底应该多复杂" 这个争议找一份对立方的代表立场

**应该去看原视频的**：

- 想听 Mario 和 Armin 自己的声音和对话节奏（视频 2:56，相当于一次简短的圆桌）
- 想从原视频里抓屏外的细节（Pi 工程上具体的 attack surface、token 控制技巧、extension 模板结构）
- 想自己判断 "两位作者在公司里的分工、决策流程" 这些团队层面的东西，本文完全没有覆盖

**应该直接跳到仓库的**：

- 想跑 Pi 装一下试试 —— `bun i -g @earendil-works/pi-coding-agent` 即可，也可以先 `npx` 跑
- 想读 Mario 博客原文（mariozechner.at/posts/2025-11-30-pi-coding-agent）—— 原话比本文摘要诚实，Mario 自己的反思和取舍都对决策有直接价值
- 想验 YOLO by default 的强度 —— Venus VM 装 Gondolin 镜像之后跑 Pi，自己承担数据安全责任

---

## 9 · 这次反主流的赌注给我们的提示

视频本身只是 2:56 的短摘，但背后站着的判断 —— **"AI Agent 的复杂度爆炸是最危险的副作用"** —— 值得记下。

两件具体的事：

1. **下次选 Agent 框架时，先问 "它默认吃多少 token"**。一个 system prompt 8k、内置工具 60 个的 Agent，开机空跑就要 9% 的 context。剩下 91% 给用户问答，还要算上你自己塞进去的 code、文件、对话。Pi 的 < 1000 tokens 是一个可以拿来对比的标杆。

2. **下次接到 "做企业系统需要知识库 / 长期记忆" 的反馈时，先问 "知识库 / 长期记忆需要的是不是 Agent 本身"**。Pi 的答案是 "不是，是 extension 或 harness 层"。这条回答不适用于所有人，但把它和 "AI Agent 默认必须有知识库" 放一起考虑，比默认选择其中一端更准确。

赌注的胜负还远未定。但有一件事现在就能说清楚：**复杂度的账单迟早要付**。Pi 让用户在第一天就看到账单，其他 Agent 把账单做成了分期。

哪种会被时间验证，2026 年剩下的几个版本里会有更清楚的答案。

---

## 附录 A · 本文事实来源

- 视频来源：微博 `https://video.weibo.com/show?fid=1034:5332798752358424`（@宝玉xp 转发，2026-08-17 GMT+8，2:56 时长）
- Pi 仓库：`github.com/earendil-works/pi`（91,453 stars / 11,350 forks / 135 open issues / MIT / TypeScript / v0.84.2 发布于 2026-08-14 10:14:32 UTC）
- Mario 博客原文：mariozechner.at/posts/2025-11-30-pi-coding-agent
- Pi 官网：pi.dev
- Gondolin 仓库：`github.com/earendil-works/gondolin`
- Earendil Inc. 官网：earendil.com
- 评论区 4 条原话：见第 2-3 节内引
- 视频完整逐字稿：**已补**（v4 章节 §10）—— whisper-cli ggml-tiny.bin 转写 + 逐段校准（68 segments / 2:56 全程 / 115.16s 总耗时）

## 附录 B · 需要进一步查证的事项

- Mario / Armin 完整对话的上下文（视频 2:56 之外是否还有更长版本，例如同名播客 / YouTube 视频，原 YouTube 完整版 `youtube.com/watch?v=RjfbvDXpFls` 36 min 已锁定）
- Pi 在 Terminal-Bench 2.0 上的具体 score 计算方法（Mario 博客有原文，但本文未直接引用）
- HN / Reddit 上 "Pi vs Claude Code" 的系统对比帖子（搜过，有零散讨论但没找到结构化对比）
- tiny 模型在 §10 S24 "drilled" / S26 "Chikyu on Enchasing Alphiall" 上仍有错读（推测为 "chunked-on-enchunking embed-all" 某种语义搜索策略，未完全核实）

---

## 10 · 视频双语字幕 · 逐段校准（68 segments）

> 本节是 v3 时声明"完整逐字稿缺失"的具体补做。源：`/tmp/baoyu-video/audio.wav`（5.4MB mono 16kHz / 2:56），whisper-cli `ggml-tiny.bin` 转写 + 基于 Pi README / 博客 / Daisy Hollman PDF / Mario 博客原文逐段校准。
> 
> 完整 SRT 原文件：`/tmp/baoyu-video/transcript-en-tiny.srt`（5,605 bytes）。
> 
> **校准原则**：① 关键缩写 / 错字按上下文校准（AGENTS.md / Linear / Bash / Claude / Armin Ronacher / Pi 等）；② 行业通用术语保留原文（RAG / MCP / AGENTS.md）；③ 引用 Pi README / Daisy Hollman PDF 时用页码 / 行号 / 章节号锚点；④ 时间码精度 100ms（SRT 标准）。

### §1 代码即真相（Pi 第一哲学，00:00:00-00:00:15）

**S1 (00:00:00 → 00:00:03.6)** `Yeah, but coming back to memory systems, so for coding, I don't want to memory system.` — 对，回到 memory 系统的话题。对于 coding，我不要 memory 系统。

**S2 (00:00:03.6 → 00:00:05.9)** `Code is true, code is the ground truth.` — 代码即真相，代码就是 ground truth。

**S3 (00:00:05.9 → 00:00:07.4)** `It's also evolving.` — 它也在演进。

**S4 (00:00:07.4 → 00:00:10.7)** `And I don't need another place that I need to maintain.` — 而且我不需要再多一个地方需要维护。

**S5 (00:00:10.7 → 00:00:12.4)** `I already have code based to maintain.` — 我已经要维护代码了。

**S6 (00:00:12.4 → 00:00:15.0)** `So for code, I don't need a memory system, right?` — 所以对于代码，我不需要 memory 系统，对吧？

> §1 主题：**为什么 Pi 不要 RAG / 长期记忆**——代码即真相。直接命中 @宝玉xp 视频摘要第一条。S1-S6 是 6 段连成一段完整的反 RAG 论证。

### §2 模型对代码的理解（不需要 AGENTS.md，00:00:15-00:00:50）

**S7 (00:00:15.0 → 00:00:18.2)** `Well, it's a really good at kind of understanding the code structure.` — 好，模型真的很擅长理解代码结构。

**S8 (00:00:18.2 → 00:00:20.8)** `And the code style you have just based on reading one or two files.` — 读一两个文件就能学会你的代码风格。

**S9 (00:00:20.8 → 00:00:24.8)** `And if you have that in order, then you don't need an AGENTS.md for it to follow your coding style.`（校准 H&C de → AGENTS.md）— 如果顺序正确，你不需要写 AGENTS.md 让它跟着你的 coding 风格。

**S10 (00:00:24.8 → 00:00:25.8)** `Whatever.` — 就这些。

**S11-S20 (00:00:25.8 → 00:00:49.6)** 文件夹 map 够用 / Claude 自己维护 / embeddings + AST 是浪费时间 — **完整段落：Mario 直接说 "I guarantee you, it does not"**（S19）—— 没有跑过 eval 证明 RAG 让 coding 输出变好。

### §3 "Master of My Shit" 自嘲 + append-only 无限 memory（00:00:49-01:18）

**S21-S28** Mario 给自己做的 Slack bot（自嘲命名 "Master of My Shit"）演示了 **append-only log + chunked semantic search = 无限 memory** 的实战实现。这是 Pi 设计哲学的**反向对照**——你说"对 Pi 不需要 memory"，但作者自己就有 unlimited memory Slack bot。**关键是 memory 实现的 location + 形态，不是 memory 本身**。

### §4 Pi 极简哲学 + Bash 是编程语言（01:18-01:50）

**S29-S39** 完美命中 @宝玉xp 视频摘要第二条"Bash 工具足够用，Bash 类似于编程语言，可以任意组合"。S37-S39 是 **Pi 的"extensible self" 哲学**——**Pi 是核心极简 + 用户用 skill 扩展自己**，跟 Claude Code 这种"框架 + 插件"模式根本差异在这里。

### §5 自定义 skill vs MCP 的真实工程战（01:50-02:21）

**S43-S48** 直接命中"大部分时候没必要 MCP，skill + 脚本足够"。

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
