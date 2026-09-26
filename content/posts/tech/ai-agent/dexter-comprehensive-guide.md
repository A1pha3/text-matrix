---
title: "Dexter 全面解读：从零到一的 AI 研究代理平台（含架构设计、工具生态与扩展开发）"
date: "2026-03-26T16:15:00+08:00"
lastmod: "2026-09-26T12:00:00+08:00"
slug: "dexter-comprehensive-guide"
github_repo: "A1pha3/dexter"
source_key: "gh:A1pha3/dexter"
author: "钳岳"
canonical: "https://txtmix.com/posts/tech/ai-agent/dexter-comprehensive-guide/"
aliases:
  - /posts/tech/dexter-comprehensive-guide/
  - /posts/tech/dexter-ai-research-agent-platform/
description: "系统学习 Dexter 项目全部中文文档，涵盖：多模型路由、金融工具链、网页工具、技能系统、持久记忆、WhatsApp 网关、心跳与定时任务、Agent 循环机制、扩展开发与故障排查的完整技术指南。"
keywords: ["Dexter", "AI Agent", "金融研究", "virattt", "LangChain", "Claude Code", "WhatsApp 网关", "持久记忆", "定时任务"]
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "自动化"]
---

# Dexter 全面解读：从零到一的 AI 研究代理平台（含架构设计、工具生态与扩展开发）

> 预计阅读时间：15 分钟 | 难度：⭐⭐⭐⭐

> **目标读者**：AI 开发者、金融科技研究者、想在本地搭建 Agent 系统的用户

---

## 概述：Dexter 解决什么问题

Dexter 是一个运行在终端的自主金融研究代理。它的定位和 Claude Code 相似：Claude Code 替程序员改代码、跑命令，Dexter 替研究者拆解问题、查数据、汇总结论，只是专业方向落在金融研究上。

为什么需要它，而不是直接问一个对话模型？模型给出的回答依赖训练数据，时效性有限，也难以验证来源。Dexter 把一次提问当成一次"研究"来处理：先拆成执行步骤，再用实时行情、财报文件、网页搜索这些真实工具逐项执行，反复核对，直到给出有依据的结论。它留下的是可以逐条回溯的执行记录，而不只是一段答案文字。

一点溯源：Dexter 由开发者 virattt 发起（上游仓库 virattt/dexter，2025 年 10 月创建，至今保持活跃开发）。本文以社区 fork 仓库 [A1pha3/dexter](https://github.com/A1pha3/dexter) 为准——它在主线基础上同步能力，并附带了完整的中文文档集，后文内容均对应该仓库代码与这份文档。需要说明的是，该 fork 同步自 2026 年 3 月末的主线快照，此后上游仍在继续演进；本文描述的是这个快照的行为，使用上游新能力时请以官方 README 为准。

---

## 能力全景

Dexter 的能力可以拆成 8 个子系统，模型层先按下不表，单独在架构一节讲：

| # | 子系统 | 核心能力 | 代表工具 / 组件 |
| --- | --- | --- | --- |
| 1 | **多模型路由** | 8 家提供商统一接入 | OpenAI、Anthropic、Google、xAI、Moonshot、DeepSeek、OpenRouter、Ollama |
| 2 | **金融工具链** | 财报、价格、新闻、筛选 | `get_financials`、`get_market_data`、`read_filings`、`stock_screener` |
| 3 | **网页工具** | 搜索、抓取、渲染 | `web_search`、`web_fetch`、`browser`（配好 X API 后另有 `x_search`） |
| 4 | **文件系统** | 本地文件读写编辑 | `read_file`、`write_file`、`edit_file` |
| 5 | **技能系统** | 可复用工作流 | `skill`（读取 SKILL.md） |
| 6 | **持久记忆** | 跨会话知识积累 | `memory_search`、`memory_get`、`memory_update` |
| 7 | **WhatsApp 网关** | 消息通道接入 | 自聊模式、专用 bot 号码、群聊模式 |
| 8 | **自动化引擎** | 心跳监控 + 定时任务 | `heartbeat`、`cron` |

这张表的目的是建立"什么问题该找哪个工具"的判断，不用背工具名。后面各节会解释每个子系统为什么这样设计。

---

## 快速入门

动手之前，先确认一套可运行的环境。Dexter 用 [Bun](https://bun.com/)（v1.0 及以上）作为运行时，`bun install` 的 postinstall 脚本会自动安装 playwright 的 chromium，供 `browser` 工具渲染网页使用。

### 前置条件

- 安装了 Bun 运行时
- 至少一个模型提供商 API Key（默认 OpenAI）
- （强烈建议）[Financial Datasets](https://financialdatasets.ai/) 的 API Key，用于金融数据——官方 README 注明 AAPL、NVDA、MSFT 三只股票的数据免费
- （强烈建议）一个搜索服务 Key：Exa（首选）、Perplexity 或 Tavily

### 安装与配置

```bash
# 1. 安装依赖（包含 playwright chromium）
bun install

# 2. 生成 .env 并填入必需项
cp env.example .env
# 至少填写：
# OPENAI_API_KEY=your-key
# FINANCIAL_DATASETS_API_KEY=your-key（强烈建议）
# EXASEARCH_API_KEY=your-key（强烈建议）
```

`.env` 里还有几组可选 Key，按需填写：`PERPLEXITY_API_KEY`、`TAVILY_API_KEY`（搜索备选）；`X_BEARER_TOKEN`（启用 `x_search` 工具，用于公开舆论研究）；`LANGSMITH_API_KEY`（评估跟踪）。记忆功能的嵌入向量复用已有的模型 Key，不需要额外申请——优先级依次是 OpenAI、Gemini、Ollama。

```bash
# 3. 启动 CLI 交互模式
bun run start
```

开发时可用 `bun run dev` 进入带热更新的 watch 模式。

### 验证能跑起来

启动后，用一条能命中金融工具的最小问题验证，例如：

```text
Tesla 最近一季的营收是多少？
```

观察作答过程中是否调用了 `get_financials` 或 `get_market_data`。如果只返回一个没有数据来源的普通回答，说明对应工具没有真正启用，先回到 §故障排查。

---

## 系统架构：六层协同设计

### 分层总览

```text
┌─────────────────────────────────────────────────────────────┐
│                        入口层                                │
│           src/index.tsx、src/gateway/index.ts               │
├─────────────────────────────────────────────────────────────┤
│                        交互层                                │
│            CLI 终端 UI、输入历史、状态显示                   │
├─────────────────────────────────────────────────────────────┤
│                        代理层                                │
│         规划、迭代执行、上下文管理、工具协同                 │
├─────────────────────────────────────────────────────────────┤
│                        模型层                                │
│          多提供商适配、调用路由、重试策略                    │
├─────────────────────────────────────────────────────────────┤
│                        工具层                                │
│      金融工具、网页工具、文件工具、自动化工具、记忆工具       │
├─────────────────────────────────────────────────────────────┤
│                      扩展能力层                              │
│           技能系统、记忆系统、网关系统、调度系统             │
└─────────────────────────────────────────────────────────────┘
```

下面自上而下拆开讲每一层，重点放在"为什么这样设计"。

### 模型层：LangChain 之上做前缀路由

模型层构建在 LangChain 之上（`@langchain/openai`、`@langchain/anthropic` 等官方适配包），再由一份统一的提供商注册表（`src/providers.ts`）做路由。关键设计是**按模型名前缀判断提供商**，而不是先让用户选提供商、再选模型：

| 提供商 | 模型名前缀 | 对应 API Key |
| --- | --- | --- |
| OpenAI | 无前缀（如 `gpt-5.4`，也是默认模型） | `OPENAI_API_KEY` |
| Anthropic | `claude-` | `ANTHROPIC_API_KEY` |
| Google | `gemini-` | `GOOGLE_API_KEY` |
| xAI | `grok-` | `XAI_API_KEY` |
| Moonshot | `kimi-` | `MOONSHOT_API_KEY` |
| DeepSeek | `deepseek-` | `DEEPSEEK_API_KEY` |
| OpenRouter | `openrouter:` | `OPENROUTER_API_KEY` |
| Ollama | `ollama:` | 无需云端 Key |

前缀匹配不中时一律回落到 OpenAI。xAI、Moonshot、DeepSeek、OpenRouter 四家走的是 OpenAI 兼容端点，复用同一套 `ChatOpenAI` 适配、只换 baseURL——这让"新增一家提供商"的改动收敛到注册表里加一个条目。

三个值得注意的细节：

- 除 Ollama 外，每家提供商都定义了 `fastModel`，供摘要、快速分类这类低成本轻量场景使用（如 OpenAI 的 `gpt-4.1`、Anthropic 的 `claude-haiku-4-5`）；没有配置 fastModel 时回落到主模型。
- 对 Anthropic，系统提示会被显式标记为 `cache_control: ephemeral`。原因是系统提示很长——包含工具描述、技能元数据、记忆信息和频道约束——缓存前缀能明显降低重复输入的云上成本（源码注释给出的量级是输入成本降低约 90%）；其他主流厂商走各自 SDK 的自动缓存。
- 所有模型调用套一层统一重试：最多 3 次尝试，指数退避（500ms 起步逐次翻倍），认证、计费这类错误不重试直接抛出。

### 工具层：工具装配原则

工具层有一个容易被忽略的设计约束：**只把"当前真的能用"的工具暴露给模型**。

原因在代理机制。Agent 的规划来自系统提示，如果系统提示列出它根本没法调用的工具，模型就会据此做出错误的计划——体验比"压根不展示这个工具"更差。这个原则直接决定了游戏规则：

- 对用户：先确认问题与工具职责是否匹配，再决定措辞。
- 对开发者：新增工具时，除了实现功能，还要写清楚 rich description。工具描述本身就是代理行为的一部分，不是附属注释。

落到代码上，`src/tools/registry.ts` 里有 14 个工具无条件注册（金融 4 个、`web_fetch`、`browser`、文件 3 个、`heartbeat`、`cron`、记忆 3 个），另外三个按环境注入：

- `web_search`：Exa、Perplexity、Tavily 三家任一配了 Key 就出现，检查顺序 Exa → Perplexity → Tavily，配了谁就用谁，供应商差异挡在规划层之外。
- `x_search`：配了 `X_BEARER_TOKEN` 才出现，专门搜 X/Twitter 上的公开讨论。
- `skill`：目录里发现至少一个技能才出现。

### 代理层：Agent 循环与上下文

代理层是研究过程发生的核心，完整链路见下一节《Agent 循环机制》。

### 扩展能力层：四件事各司其职

技能、记忆、心跳、定时任务这 4 个概念容易被混为一谈，职责其实不同：

| 能力 | 作用 |
| --- | --- |
| 技能 | 提供专业工作流说明（如 DCF 估值） |
| 记忆 | 保存用户长期信息和历史上下文 |
| 心跳 | 按周期检查一份监控清单 |
| 定时任务 | 创建通用计划任务，触发时执行 Agent 询问 |

### 技能系统工作流

技能的存在是为了让复杂方法论可沉淀、可复用，而不是每次从零解释：

```text
1. 发现   → 扫描包含 SKILL.md 的目录
2. 暴露   → 仅注入技能名称和描述到系统提示
3. 按需   → Agent 匹配后调用 skill 工具
4. 执行   → 返回技能正文，解析相对路径
```

发现机制有两级目录：仓库内置的 `src/skills/`（自带 `dcf` 和 `x-research` 两个技能），以及项目级的 `.dexter/skills/`——后者的同名技能会覆盖内置版本，方便定制而不改源码。SKILL.md 的 frontmatter 必须带 `name` 和 `description` 两个字段，缺任一项整个技能会被跳过。系统提示里的技能使用政策还要求：任务与技能相关时立即调用，同一次提问里不重复调用同一个技能。

### Agent 循环机制

```text
用户输入 → CLI 接收 → Agent.create() 初始化
    ↓
构建系统提示（工具描述 + SOUL.md + 记忆 + 技能元数据 + 频道约束）
    ↓
模型生成响应 → 判断是否有工具调用
    ↓
执行工具 → 结果写入 scratchpad
    ↓
估算上下文超过 10 万 token？
    ├─ 是 → 先做一次 memory flush（写入持久记忆）
    │       再清理最早的工具结果（保留最近 5 条）
    └─ 否 → 继续
    ↓
收敛后生成最终答案 → 返回给用户
```

这串流程描述的是迭代执行，单次提问最多迭代 10 轮。上下文管理参考了 Anthropic 的做法：用"字符数 ÷ 3.5"粗估 token 数，估算值超过 10 万 token 阈值时触发清理；清理前会先跑一次 memory flush，把这轮研究里值得长期保留的事实和偏好写进记忆（每次清理至多触发一次），然后丢弃最早的工具结果、保留最近 5 条。如果模型端直接抛出上下文溢出错误，还有一条反应式路径：最多重试 2 次，每次都丢弃最旧的工具结果再试。

肉眼可见的代价是：一次研究可能来回执行多轮工具调用，比"问一句答一句"慢。换取的是回答能引用真实数据、能自我核对。

---

## 金融研究工作流

Dexter 的差异点在于金融。好的研究提问，通常同时具备四个要素：对象、时间范围、判断维度、期望输出。

先看一个反例——它太单薄，工具很难据此拆出有价值的研究步骤：

```text
What is Tesla's latest revenue?
```

再看一个更完整的研究提示词，它隐含了"拆步骤 + 给结论"的要求：

```text
What does Tesla's latest revenue, gross margin, and operating income
suggest about demand quality and pricing power?
```

```text
对象 + 时间范围 + 比较维度 + 目标判断 + 期望输出格式
```

区别在于：前者只要"查个数"，后者要"基于多个指标做判断"。研究价值来自后者。

### 一次研究的完整路径

把抽象机制串起来看。假设在 CLI 里输入：

```text
Compare Apple and Microsoft revenue growth over the last 5 years
```

1. `Agent.create()` 构建系统提示：注册表里的工具描述、SOUL.md 的角色设定、`.dexter/memory/` 里的记忆文件清单、技能元数据、CLI 频道的输出约束，一次性组装完毕并注入当前日期。
2. 模型收到问题后决定调用 `get_financials`。系统提示明确要求**多公司、多指标合并成一次调用**——"一次带完整自然语言查询的调用内部会自行处理"，不拆成多个工具请求。
3. 工具结果连同入参、原始返回写入 `.dexter/scratchpad/` 下的 JSONL 文件；模型的中间推理（如果伴随工具调用产生）记为 `thinking` 事件。
4. 迭代提示把全部工具结果带回给模型，让它判断数据是否足够；不够就继续调工具，够就直接作答。
5. 最终答案在 CLI 渲染，scratchpad 里的 `sourceUrls` 记录了每条数据的出处。

这条路径上每一步都有文件可查：系统提示的组装在 `src/agent/prompts.ts`，迭代与上下文管理在 `src/agent/agent.ts`，执行记录在 `.dexter/scratchpad/`。

### 金融工具如何分工

- `get_financials`：财务、指标、估值、分析师预期类问题——营收利润现金流趋势、财务比率、估值指标。
- `get_market_data`：价格、新闻、市场动态、内幕交易等更偏"市场表层状态"的问题。
- `read_filings`：读 SEC 原始文件，适合对 10-K、10-Q、8-K 做文本层研究。有些结论不能只靠结构化指标得出，必须回到公司自己披露的文本。
- `stock_screener`：按条件筛选股票，而不是研究某个单一对象。

### 网页工具如何分工

- `web_search`：通用网页搜索。只要 Exa、Perplexity、Tavily 中任一可用，就以同一个名字暴露，把供应商差异挡在规划层之外。
- `web_fetch`：抓取页面正文。当搜索结果标题已足够回答时，不必再抓全文。
- `browser`：处理依赖 JavaScript 渲染或交互的页面，比如需要点击、滚动、访问单页应用的场景。不要默认全用它——成本更高、更慢、失败面更多，系统提示也要求仅在必要时使用。

> 一个更普遍的判断：`get_financials` 管"公司基本面"，`get_market_data` 管"市场和价格"，`read_filings` 管"原始披露文本"。问之前先想清楚你的问题落在哪一层。

---

## WhatsApp 网关

Dexter 可以通过 WhatsApp 接收消息并回传结果，把你从终端里解放出来。官方文档支持三种使用形态：**自聊模式**（用个人手机给自己发消息）、**专用 bot 号码**（Dexter 绑一张独立 SIM 卡，别人可以给它发私信）和**群聊模式**（拉进群，@它才回答）。

快速接入：

```bash
# 1. 扫码绑定你的 WhatsApp 账号
bun run gateway:login

# 2. 启动网关
bun run gateway
```

自聊模式：打开 WhatsApp，在和自己聊天的会话里发问题，Dexter 处理完后就回发到同一个会话。`gateway:login` 扫码后会询问使用方式，选自聊会自动把本机号码加入允许列表；选专用号码则要填允许给 bot 发信的号码清单。

群聊模式需要在 `.dexter/gateway.json`（登录后自动生成）里配置：`groupPolicy` 设为 `open`（任何群）或 `allowlist`（指定群），默认 `disabled`。群里有消息时 Dexter 保持沉默，只有被 @-mention 才响应——注意必须用 WhatsApp 输入框的 @ 选择器选联系人，手打名字不会触发。回复时它能读到群里最近的消息作为上下文。

消息访问控制由 `dmPolicy` 管：`pairing`（默认）、`allowlist`、`open`、`disabled` 四档。遇到连接问题时的恢复路径在网关的独立 README 里写得很细：重新扫码登录、或做一次全重置（手机端退出关联设备 + 删除 `.dexter/credentials/` 下的凭据和 `gateway.json`）。

详细的配置项和排错步骤，见 WhatsApp 网关的独立 README。

---

## 心跳与定时任务

这两套机制让 Dexter 从"被动等待提问"变成"主动汇报"。

### heartbeat：周期性检查

心跳读一份监控清单——`.dexter/HEARTBEAT.md`——按周期逐项检查。清单里写什么它查什么，比如"NVDA 跌破某价位提醒我""每天看看大盘异动"。没建清单时它会用一份默认清单：主要指数单日波动超 2% 报警、突发重大财经新闻（财报爆冷、美联储决议）报警。

配套细节有三个，都朝着"少打扰"设计：

- `heartbeat` 工具支持 `view` 和 `update` 两个操作，直接跟 Dexter 说"帮我盯着 NVDA"就能改清单；
- 写入非空清单后，网关配置会自动启用心跳，不用手动开关；
- Agent 检查后认为没什么值得报告的，就回复约定好的 `HEARTBEAT_OK` 令牌，网关把它吞掉、不给你发消息；同一内容 24 小时内也不会重复推送。

### cron：定时任务

三个 kind 覆盖了三种最常见的定时需求：

```json
// 一次性时间点
{ "kind": "at", "at": "2026-04-01T14:00:00Z" }

// 固定间隔
{ "kind": "every", "everyMs": 3600000 }

// Cron 表达式 + 时区
{ "kind": "cron", "expr": "0 9 * * 1-5", "tz": "America/New_York" }
```

`cron` 触发时执行一次 Agent 询问，适合在固定时刻（如开盘前）生成一次研究结果。任务还有三个维度的配置值得知道：

- **fulfillment 模式**：`keep` 触发后保留任务（长期监控）、`once` 触发一次自动停用（价格提醒）、`ask` 触发后询问是否继续。很多提醒任务既不是无限重复也不是一次性的，这层抽象就是为它准备的。
- **activeHours 生效时段**：限定任务在哪些时段运行，时区默认 America/New_York、默认周一到周五，配合起止时间正好框住美股常规交易时段。
- **运行状态**：每个任务记录上次运行结果（`ok`/`error`/`suppressed`）和连续错误计数，排查自动化问题时先看这个。

`cron` 工具提供 `list`、`add`、`update`、`remove`、`run` 五个操作。心跳和定时任务在底层是联动的——心跳本质上是同步进 cron 体系的一个高级入口，cron 才是调度层。

---

## 调试：scratchpad

Dexter 把每次执行都记录成 scratchpad，方便复查数据来源——这也是它"可追溯"逻辑的来源。每条查询在 `.dexter/scratchpad/` 下生成一个 JSONL 文件：

```text
.dexter/scratchpad/
├── 2026-01-30-111400_9a8f10723f79.jsonl
├── 2026-01-30-143022_a1b2c3d4e5f6.jsonl
└── ...
```

每条 JSONL 记录三类事件：

- `init`：原始提问
- `tool_result`：工具调用、入参与原始返回
- `thinking`：Agent 的推理步骤

例如：

```json
{"type":"tool_result","timestamp":"2026-01-30T11:14:05.123Z","toolName":"get_financials","args":{"query":"Compare Apple and Microsoft revenue growth over the last 5 years"},"result":{"data":{...},"sourceUrls":["https://financialdatasets.ai/..."]}}
```

排查问题时，先看某次回答引用的 `sourceUrls`，再回看当时的 `init` 与 `tool_result`，就能判断是数据源问题、工具问题还是提问本身的问题。

长期运行还有两处状态值得知道：记忆以 Markdown 文件存在 `.dexter/memory/`（含每日日志），网关的调试日志写在 `.dexter/gateway-debug.log`。

---

## 故障排查

从高频到低频，按这个顺序排查：

```text
1. 检查 .env 是否缺少关键 Key
2. 重新运行 bun install（确认依赖完整）
3. 重新启动 CLI 或网关
4. 用一条最小可验证问题重试
5. 必要时重建网关登录状态
```

常见判断：

- 回答里只有模型自述、看不到数据来源 → 对应工具没有真正启用，检查该提供商的 API Key。
- 网页结果为空 → 检查搜索服务是否配了某一家的 Key；`web_search` 只要三家之一可用就会暴露。
- WhatsApp 收不到回复 → 先确认扫码登录状态，再检查 `allowFrom` 里有没有你的号码；持续失败就按"全重置"流程清掉凭据重来。
- 自动化任务创建了但没收到通知 → 这类链路依赖网关回传，确认网关在跑；再看任务的 `lastRunStatus` 和心跳抑制规则（无事可报、24 小时内重复内容都会被压下）。

---

## 扩展开发

给 Dexter 加能力，核心是熟练使用两条接入路径：**新增工具**和**新增技能**。工具补"单一能力"，技能沉淀"整套工作流"，两者在代理行为里各管一段。

开发前先回到《工具装配原则》：新增工具必须写清 rich description，因为它直接参与 Agent 的规划；实现体放进 `src/tools/` 对应子目录，再在 `src/tools/registry.ts` 注册（记得判断是否该按环境条件注入）。技能则是往 `.dexter/skills/` 放一个含 SKILL.md 的目录，frontmatter 写全 `name` 和 `description`，正文写工作流说明（如 DCF 估值），同名即可覆盖内置技能。

改完怎么验证？仓库自带一套评估机制：`src/evals/` 下有金融问答数据集（`finance_agent.csv`）和评估脚本，用 LangSmith 做跟踪、LLM-as-judge 打分：

```bash
# 全量跑
bun run src/evals/run.ts

# 随机抽样 10 题
bun run src/evals/run.ts --sample 10
```

日常开发还有 `bun run typecheck` 和 `bun test` 两道静态与单元检查。

完整的接入方法、评估与发布边界，见官方文档的《开发与评估》《新增工具与技能》。

---

## 常见问题

**Dexter 和直接问"GPT"有什么区别？**

直接问对话模型，回答依赖训练知识且难溯源；Dexter 用真实工具逐项执行，结果可回溯、可核对。代价是更慢、更绕。

**我该用哪个模型？**

默认 OpenAI（`gpt-5.4`）；任务重推理可切 Anthropic/DeepSeek，本地敏感场景可切 Ollama。选型参考"模型层"一节的前缀路由表。

**为什么不能强制 Dexter 用某个工具？**

可以靠提问措辞引导，但最终由代理决定。更可靠的做法是把任务目标写清楚，而不是替它做所有规划。

**技能、记忆、心跳、定时任务是一回事吗？**

不是。看"四件事各司其职"表格，它们分别管工作流、信息记忆、周期检查、计划触发。

**fork 和上游仓库是什么关系？**

上游 virattt/dexter 是项目主线，仍在活跃开发；A1pha3/dexter 是同步了主线能力并补全中文文档的快照分支。本文以快照为口径，想追上游新特性就看官方 README 和提交记录。

---

## 适用边界与采用建议

Dexter 值得上手的场景：需要频繁做个股/行业研究、希望结论带数据出处、愿意本地放一套常驻服务的研究者；想学习"金融版 Claude Code"如何组织工具、记忆与自动化的 Agent 开发者——它的代码量不大，六层结构每个目录职责清晰，适合当范本读。

可以先等等的场景：需要生产级并发与多租户（单机单用户的设计）、依赖非英文市场的本地化数据源（金融数据走 Financial Datasets，以美股为主）、希望手机上零配置可用（WhatsApp 网关需要自己维护一个常驻进程和登录状态）。

落地顺序建议：先跑通 CLI（半天，重点验证金融工具真的被调用），再用 scratchpad 观察一两周真实的提问-执行链路，顺手把值得记住的偏好交给记忆系统；之后按需挂心跳盯几个标的，最后才考虑 WhatsApp 网关和 cron 这类常驻自动化。

---

## 延伸阅读

- **Dexter GitHub**：[A1pha3/dexter](https://github.com/A1pha3/dexter)（fork 自 virattt/dexter，附中文文档集）
- **中文文档中心**：[docs/cn](https://github.com/A1pha3/dexter/tree/main/docs/cn)
- **系统架构详解**：[system-architecture.md](https://github.com/A1pha3/dexter/blob/main/docs/cn/architecture/system-architecture.md)
- **Agent 循环机制**：[agent-loop-and-context.md](https://github.com/A1pha3/dexter/blob/main/docs/cn/architecture/agent-loop-and-context.md)
- **心跳与定时任务**：[heartbeat-and-cron.md](https://github.com/A1pha3/dexter/blob/main/docs/cn/automation/heartbeat-and-cron.md)
- **新增工具与技能**：[adding-tools-and-skills.md](https://github.com/A1pha3/dexter/blob/main/docs/cn/development/adding-tools-and-skills.md)
