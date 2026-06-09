+++
date = '2026-06-09T21:00:00+08:00'
draft = false
title = 'x1xhlol/system-prompts-and-models-of-ai-tools 深度导读：30+ 主流 AI 编程工具的 system prompt 与工具定义大合集'
slug = 'x1xhlol-system-prompts-ai-tools-leak-archive'
description = 'x1xhlol/system-prompts-and-models-of-ai-tools 是 2026-06 GitHub 日榜上最“特殊”的项目——它没有可运行的代码，而是把 Claude Code、Cursor、Devin、Lovable、Replit、Windsurf、Trae、Manus 等 30+ 主流 AI 编程/Agent 产品的 system prompt、Tools JSON、Agent Loop 原样归档，star 数突破 13.9 万，是观察 AI 编程工具设计演化的最佳资料库。'
categories = ['技术笔记']
tags = ['system-prompt', 'AI编程工具', 'Agent', 'Claude Code', 'Cursor', 'Devin', 'Lovable', '资源集合', 'prompt-engineering', '开源']
+++

# x1xhlol/system-prompts-and-models-of-ai-tools 深度导读：30+ 主流 AI 编程工具的 system prompt 与工具定义大合集

> **目标读者**：做 AI 编程工具、Agent 框架、Prompt Engineering、模型评测的研究者与产品经理
> **核心问题**：现在 30 多个 AI 编程/Agent 产品（Claude Code、Cursor、Devin、Replit Agent、Lovable、Windsurf、Trae、Manus…）到底用 prompt 把模型“训”成了什么形状？它们的工具定义、Agent 循环、能力边界到底有多不同？
> **难度**：⭐⭐（入门；不要求写代码）
> **预计阅读时间**：15 分钟

---

## 一、这个仓库是什么

`x1xhlol/system-prompts-and-models-of-ai-tools`（GitHub：[x1xhlol/system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools)）是 Lucas Valbuena（x1xhlol / Lucknite）维护的一个**纯资源型**仓库——它不提供任何可 import、可运行的 SDK 或 CLI，而是把市面上 30 多个 AI 编程 / Agent / 桌面助手产品的**原始 system prompt、Tools JSON schema、Agent 循环描述、内部模型配置文件**直接以 `.txt` / `.json` 形式归档在 34 个子目录下。

截至 2026-06-09，仓库状态：

| 指标 | 数值 |
|---|---|
| 仓库 | [x1xhlol/system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools) |
| Stars | 139,016 |
| Forks | 34,544 |
| 许可证 | GPL-3.0 |
| 创建时间 | 2025-03-05 |
| 最近推送 | 2026-06-09（仍在每日更新） |
| 顶层子目录数 | 34（每个目录对应一个 AI 产品） |
| Topics | `cursor`, `claude-code`, `windsurf`, `replit`, `lovable`, `devin`, `trae`, `v0`, `system-prompts`, `perplexity` 等 20+ |

> 数据来源：GitHub 仓库页面与顶层目录列表（截至 2026-06-09）。

它的“卖点”在仓库自述里写得很直白：

> FULL Augment Code, Claude Code, Cluely, CodeBuddy, Comet, Cursor, Devin AI, Junie, Kiro, Leap.new, Lovable, Manus, NotionAI, Orchids.app, Perplexity, Poke, Qoder, Replit, Same.dev, Trae, Traycer AI, VSCode Agent, Warp.dev, Windsurf, Xcode, Z.ai Code, Dia & v0. (And other Open Sourced) System Prompts, Internal Tools & AI Models

直白翻译：所有你能叫得出名字的 AI 编程/Agent 工具，它的 system prompt、内部 Tools schema、Agent 循环伪代码，能拿到的都归档在这里了。

---

## 二、仓库结构：34 个子目录对应 30+ 个产品

顶层目录一览（按字母序，截取自 `https://api.github.com/repos/.../contents/`）：

| 子目录 | 对应产品 | 文件类型 |
|---|---|---|
| `Amp` | Sourcegraph Amp | prompt / tools |
| `Anthropic` | Claude Code / Claude Sonnet 4.5/4.6 / Claude for Chrome | prompt + 子目录 |
| `Augment Code` | Augment Code | prompt / tools |
| `Cluely` | Cluely（隐形 AI 助手） | prompt |
| `CodeBuddy Prompts` | 腾讯 CodeBuddy | prompt |
| `Comet Assistant` | Perplexity Comet | prompt |
| `Cursor Prompts` | Cursor（Agent / Chat / Wave 11） | prompt / tools |
| `Devin AI` | Cognition Devin | prompt / DeepWiki prompt |
| `Emergent` | Emergent | prompt |
| `Google` | Gemini CLI / Jules 等 | prompt |
| `Junie` | JetBrains Junie | prompt |
| `Kiro` | AWS Kiro | prompt |
| `Leap.new` | Leap.new | prompt |
| `Lovable` | Lovable（前端 AI） | prompt |
| `Manus Agent Tools & Prompt` | Manus（通用 Agent） | Agent loop + Modules + tools.json |
| `NotionAi` | Notion AI | prompt |
| `Open Source prompts` | Bolt / Cline / Codex CLI / Gemini CLI / Lumo / RooCode | 子目录聚合 |
| `Orchids.app` | Orchids | prompt |
| `Perplexity` | Perplexity（搜索式） | prompt |
| `Poke` | Poke | prompt |
| `Qoder` | Qoder | prompt |
| `Replit` | Replit Agent | prompt + tools.json |
| `Same.dev` | Same.dev | prompt |
| `Trae` | Trae IDE / Trae Agent | prompt |
| `Traycer AI` | Traycer | prompt |
| `VSCode Agent` | VS Code Agent 模式 | prompt |
| `Warp.dev` | Warp 终端 Agent | prompt |
| `Windsurf` | Windsurf Cascade | Prompt Wave 11 + Tools Wave 11 |
| `Xcode` | Apple Xcode AI | prompt |
| `Z.ai Code` | Z.ai Code | prompt |
| `dia` | dia browser | prompt |
| `v0 Prompts and Tools` | Vercel v0 | prompt / tools |

子目录内文件命名也透露出版本节奏。比如 `Cursor Prompts/` 里有：

- `Agent Prompt 2.0.txt`（38 KB）
- `Agent Prompt v1.0.txt` / `v1.2.txt`
- `Agent Prompt 2025-08-07.txt` / `2025-09-03.txt`
- `Agent Tools v1.0.json`（23 KB）
- `Chat Prompt.txt`

`Anthropic/` 里的 `Claude Sonnet 4.6.txt` 已经接近 100 KB（98,989 字节），基本就是当前 Claude 顶级模型在 Claude Code 里的完整 system prompt 原文。

> 文件大小是 2026-06-09 抓取时的快照；产品方在每次模型升级时都会推新文件，所以这个仓库本质上是一份**带时间戳的 industry prompt timeline**。

---

## 三、它不是工具，而是“行业标本库”

理解了它是什么之后，关键问题就变了：**为什么 13.9 万 star？它在被谁、用在什么场景？**

### 3.1 对研究者：横向比较 30+ 产品的 prompt 设计

把同一时间点的 `Cursor Agent Prompt 2.0.txt`、`Windsurf Prompt Wave 11.txt`、`Replit Prompt.txt`、`Manus Prompt.txt`、`Devin AI Prompt.txt` 摆在一起读，会发现几件有意思的事：

- **工具数量差异巨大**：Cursor 的 Tools JSON 列了 30+ 个工具，Devin 的 tools schema 接近 50 个（包含 shell、browser、editor、notebook 等），而某些轻量产品只暴露 5–8 个工具。
- **Agent 循环写法不一样**：Manus 在 `Agent loop.txt` 里直接写出了 `observe → think → act → reflect` 的伪代码；Replit 在 `Prompt.txt` 里把循环拆成 `plan → execute → verify → respond`；Claude Code 的 system prompt 则要求模型“自检 + 反思错误 + 主动询问用户”。
- **安全/越狱指令的位置不同**：有的产品把“红队越狱防御”写在最前 500 token 内，有的塞在“Capabilities”章节末尾，反映出各家对 prompt injection 的优先级判断不同。

这种**横向快照**在学术论文（尤其是 Agent 架构综述、Prompt Engineering 实证研究）里非常有用——你不用再挨个爬博客、追 changelog，而是直接拿到原始 prompt 文本。

### 3.2 对产品经理：监控竞品“能力边界”的演变

如果你是 AI 编程工具的产品经理，这个仓库基本就是免费的竞品情报中心：

- 看 `Anthropic/Claude Code 2.0.txt` 就知道 Claude Code 2.0 多了哪些工具、哪些限制；
- 看 `Cursor Prompts/Agent Prompt 2025-09-03.txt` 就能看出 Cursor 在 9 月那次更新里是不是把“规划步骤”提到了 prompt 头部；
- 看 `Windsurf/Prompt Wave 11.txt` 能看到 Wave 11 给 Cascade 加了什么新行为指令。

把每个产品的 `Prompt v1.0 → v1.2 → Wave 11` 串起来读，等于免费拿到一份**过去 14 个月的 AI 编程工具产品演进史**。

### 3.3 对独立开发者：复现“某产品的 agent 心智”

现在有一类常见需求：**“我想模仿 Cursor Agent 的行为，但用更便宜的模型 / 本地模型 / 我自己的 RAG 知识库”**。

- 直接把 `Cursor Prompts/Agent Prompt 2.0.txt` 当成 system prompt 喂给本地 Llama/Qwen/DeepSeek，加上一份精简后的 `tools.json`，就能跑出一个 80% 行为相似的 Cursor 风格 Agent；
- 把 `Manus Agent Tools & Prompt/tools.json`（18 KB）喂给一个支持 function calling 的开源模型，就能复现 Manus 的多步骤任务循环；
- 拿 `Replit Prompt.txt` + `tools.json`（25 KB）可以做“代码 + 部署一体化”的 Agent 实验。

注意：仓库许可证是 **GPL-3.0**——这意味着如果你把其中的 prompt 内容**直接作为可分发软件的一部分**，理论上需要遵守 GPL 协议（具体边界以律师意见为准）。如果只是“读一读、改造 prompt 措辞、丢掉原版表达”，风险极低。

### 3.4 对模型厂商：评测集 / 红队语料

很多团队在做模型评测时，苦于找不到贴近真实产品的 prompt 语料。这个仓库相当于：

- 30 套不同长度、不同工具定义、不同行为约束的 system prompt，可以直接用来测**模型对长 system prompt 的遵循度**；
- 30 套配套的 tools.json，可以用来测**模型在工具调用上的稳定性和格式正确性**；
- 30 套产品方精心设计过的“红队越狱防御指令”，可以直接当成 prompt injection 评测的 baseline。

> 顺带一提，仓库首页主动挂了 [ZeroLeaks](https://zeroleaks.ai/) 的广告位——这是一家专门帮 AI 创业公司“检测自家 system prompt 是否被反向提示工程” 的安全服务。从这个广告位就能看出，作者很清楚这类仓库对**模型安全团队**的价值。

---

## 四、值得专门读的 5 个文件

如果你只想花 30 分钟入门，下面这 5 个文件能让你快速建立“AI 编程工具 prompt 设计”的整体认知：

1. **`Anthropic/Claude Code 2.0.txt`**（57 KB）—— 当前最强 AI 编程 Agent 的完整 system prompt。读完你就知道 Claude Code 行为里“反思 + 主动询问 + 工具组合”的具体写法。
2. **`Cursor Prompts/Agent Prompt 2.0.txt`**（38 KB）—— Cursor Agent 的第二代 prompt。与 Claude Code 对比读，能看出“同一赛道、不同产品哲学”的差异。
3. **`Devin AI/Prompt.txt`**（34 KB）—— Devin 是“自主软件工程师”定位的鼻祖，工具定义最齐全，适合研究“当 Agent 拥有 shell/browser/editor/notebook 全套工具时，prompt 该怎么约束它不越权”。
4. **`Manus Agent Tools & Prompt/Agent loop.txt`** + **`tools.json`** + **`Modules.txt`** —— 这是少有的“把 Agent 循环、模块拆分、工具定义分三个文件”的产品。读完你就理解“模块化 Agent” 的 prompt 架构长什么样。
5. **`Windsurf/Prompt Wave 11.txt`** + **`Tools Wave 11.txt`**（32 KB）—— Wave 11 是 Windsurf 在 2025-10 前后的一次大更新，对比 Wave 10（如果还能找到）能看到“Flows + Cascade”这种 IDE 集成式 Agent 的 prompt 演进。

---

## 五、争议与边界

虽然 star 很高，但使用这个仓库时需要明确几件事：

1. **这些 prompt 是不是“官方版本”？** 多数文件没有官方背书，作者通过公开博客、泄露、用户分享、devtools 抓取等渠道收集。对于“是否代表产品当前真实行为”这一点，**官方从未确认**。把它当成“行业采样”，不要当成“权威真相”。
2. **产品方随时可能改 prompt**。`v1.0` → `v1.2` → `Wave 11` 这种节奏说明，**同一份 prompt 文本的半衰期大约只有几周到几个月**。引用时务必标注抓取日期。
3. **GPL-3.0 许可证**。仓库本身是 GPL-3.0 分发，但其中收录的 prompt 文本**很可能**对应各家产品方的版权作品（system prompt 通常是企业商业秘密）。**直接拿这些 prompt 去训练模型 / 重打包成商业产品**，存在版权与商业秘密争议的风险。把它当成**研究 / 学习 / 内部参考**用，是目前最稳妥的定位。
4. **作者在 README 里挂的赞助与广告位**。包括 BTC/LTC/ETH 钱包地址、Patreon、Ko-fi，以及 ZeroLeaks 的 banner。仓库**自述是“开源维护但接受赞助”**的模式，不是完全非商业化。引用时建议注明来源。

---

## 六、适用人群与阅读路径

### 适合

- 想知道 30+ AI 编程 / Agent 产品**到底用 prompt 怎么调教模型**的研究者；
- 想做**竞品监测 / 能力对比**的产品经理与解决方案架构师；
- 想用本地模型**复刻某个 Agent 行为**的独立开发者；
- 需要**长 system prompt / tools.json 评测语料**的模型厂商与评测团队。

### 不适合

- 想找“开箱即用”的 AI 编程 SDK / CLI / 框架——这不是工具型仓库，请去看 [openai/codex](https://github.com/openai/codex)、[anthropics/claude-code](https://github.com/anthropics/claude-code) 等。
- 想做“新闻快讯 / 趋势观察”——这个仓库更新太快、内容太杂，不适合直接写新闻。
- 想要未公开的“内部产品决策 / 路线图”——README 里写得很清楚：“Latest Update 10/05/2026”，但 prompt 之外的产品决策不会出现在仓库里。

### 推荐阅读路径

1. **快速入门（30 分钟）**：先读第 4 节列的 5 个文件，建立整体认知；
2. **横向比较（2 小时）**：选 3 个你最关心的产品，把它们的 v1.0 → 最新版 prompt 串起来读；
3. **复刻实验（半天）**：挑一个 prompt 喂给本地模型，加一个 tools.json 跑通最小任务，看哪些行为“复刻得对”、哪些“跑偏”；
4. **深度研究（一周+）**：把 30 套 prompt + tools.json 全部下载，建立本地索引，用脚本做关键词 / 工具数量 / 长度等维度的统计，能直接产出一篇像样的 prompt engineering 实证研究。

---

## 七、结语

`x1xhlol/system-prompts-and-models-of-ai-tools` 这个仓库的特殊之处在于：**它不生产任何新东西，它只是把已经存在但分散在各家博客、泄露、devtools 输出里的“AI 产品 prompt 真容”集中归档**。

在 AI 编程工具同质化越来越严重的 2026 年，它的存在有点像互联网早期的“搜索引擎快照”——你不一定能从它身上直接获得商业价值，但你**能从一个集中窗口看清整个赛道的设计哲学与演进节奏**。

如果你是认真在做 AI 编程 / Agent 的人，建议把它 star 起来，每周刷一次 `git log` 看看谁家又发了新版 prompt。这比追 30 个 changelog 博客省事多了。
