---
title: "Anthropic Knowledge Work Plugins：把 AI 插件从写代码改成了写 Markdown"
slug: "anthropic-knowledge-work-plugins"
github_repo: "anthropics/knowledge-work-plugins"
source_key: "gh:anthropics/knowledge-work-plugins"
description: "Anthropic 开源了 11 款知识工作插件，定义了一套无代码、纯文件驱动的 AI Agent 插件体系。本文拆解 Commands × Skills × MCP Connectors 三层架构，用三个真实任务流还原插件的工作方式，给出团队采纳路径。"
date: 2026-05-29T19:30:00+08:00
lastmod: 2026-09-19T00:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Anthropic", "Claude", "MCP", "AI Agent", "Skills"]
hiddenFromHomePage: false
featuredImage: ""
externalUrl: ""
originLinks: []
---

Anthropic Knowledge Work Plugins：把 AI 插件从写代码改成了写 Markdown

**GitHub**: [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)

> **快速信息卡**（2026-09-19 抓取）
> - **Stars**: 24,826
> - **Forks**: 2,965
> - **License**: Apache-2.0
> - **语言**: Python
> - **最近推送**: 2026-09-18
> - **定位**: 为 Claude Cowork 构建，兼容 Claude Code

**学习目标**：读完后你能回答——
- Commands、Skills、MCP Connectors 三层各自的职责是什么，为什么这三层要分开控制
- 11 个官方插件按什么思路划分，你的团队该从哪一个试起
- 一个完整的任务流（如 write-spec）从触发到产出经历了什么，哪些环节必须人工审核
- 怎么把这个仓库接进自己的团队流程——先改哪一层，后改哪一层
- 这个插件体系的设计判断有哪些可以迁移到别的行业

**目录**
- [一、三层结构：一次完整交互是怎么跑通的](#一三层结构一次完整交互是怎么跑通的)
- [二、三个任务流：用具体案例把三层串起来](#二三个任务流用具体案例把三层串起来)
- [三、11 个官方插件全景](#三11-个官方插件全景)
- [四、三个代表性插件深度拆解](#四三个代表性插件深度拆解)
- [五、五个设计模式](#五五个设计模式)
- [六、采用指南](#六采用指南)
- [七、常见问题和故障排查](#七常见问题和故障排查)
- [八、这件事能活多久](#八这件事能活多久)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [练习](#练习)
- [资料口径说明](#资料口径说明)

---

市面上大部分 AI 插件系统都在走同一条路：提供 SDK、定义 API、写胶水代码、打包、发布。Anthropic 这个开源仓库走的是另一条路——**零代码，纯 Markdown + JSON 驱动**。README 原话是："Every component is file-based — markdown and JSON, no code, no infrastructure, no build steps."

先交代背景：这批插件主要为 Claude Cowork（Anthropic 的桌面端 Agent 产品）设计，也能在 Claude Code 里用。README 宣布开源 11 个官方插件，覆盖产品管理、销售、客服、数据分析、市场营销、法务、财务、企业搜索、生物研究和插件管理。

省掉代码是表层。更实际的考虑是：一个 AI Agent 在一个领域里能干多少活，取决于它对这个领域的**知识编码有多细、有多准确**。Markdown 文件——可读、可改、可进 Git——是当前最适合做这件事的载体。相比 Python 脚本、数据库 schema、配置文件模板，Markdown 的门槛最低，非工程师也能直接改。

11 个官方插件都遵循同一套三层结构：Commands（用户显式触发）、Skills（AI 自动调用）、MCP Connectors（连接外部工具）。

下面把这三层拆开，看几个具体插件怎么跑任务流，最后说清楚不同类型团队该从哪入手。

---

## 一、三层结构：一次完整交互是怎么跑通的

先给一张总览图。Commands、Skills、Connectors 分属三个不同角色，三层之间是协作关系：

```
                    ┌─────────────────────────────┐
                    │          用户（人）           │
                    │    /start   /analyze         │
                    │    /write-spec   /standup    │
                    └─────────────┬───────────────┘
                                  │ 显式触发
                                  ▼
┌─────────────────────────────────────────────────┐
│              Commands（命令层）                   │
│  谁触发：用户                                    │
│  做什么：启动一个完整工作流                       │
│  例子：/standup → 拉 commits/PR/工单 → 生成日报   │
│        write-spec → 对话澄清需求 → 输出 PRD      │
└──────────────────────┬──────────────────────────┘
                       │ 命令内部可能自动激活 Skills
                       ▼
┌─────────────────────────────────────────────────┐
│               Skills（技能层）                    │
│  谁触发：AI 根据上下文自主判断                   │
│  做什么：注入领域知识、实践建议、工作流模板       │
│  例子：当对话涉及 SQL → 加载 sql-queries 技能     │
│        当对话涉及代码审查 → 加载 code-review 技能 │
└──────────────────────┬──────────────────────────┘
                       │ Skills 可能调用外部工具
                       ▼
┌─────────────────────────────────────────────────┐
│           MCP Connectors（连接器层）              │
│  谁配置：开发者/运维                             │
│  做什么：把外部工具暴露为标准 MCP 接口            │
│  例子：Snowflake → 数据查询                      │
│        GitHub → PR diff、提交历史                │
│        Slack → 消息搜索、频道上下文               │
└─────────────────────────────────────────────────┘
```

三层各自抓一件事：

- Commands 是入口——没人触发就不跑
- Skills 是知识——AI 自己判断什么时候用，用户不用管
- Connectors 是手脚——Skills 靠它们碰到外部世界

命令的形式有两种：插件自己的 README 通常写裸命令（`/standup`、`/analyze`），在 Cowork 或 Claude Code 会话里则带插件名前缀，比如主 README 给的例子 `/sales:call-prep`、`/data:write-query`，productivity 技能文件里写的 `/productivity:update`。看到哪种都不奇怪，指的都是同一个东西。

一个容易踩的坑：Commands 和 Skills 之间没有一对一映射。`/incident` 一个命令下去，可能同时用到 `incident-response`、`system-design`、`documentation` 几个技能的知识。反过来，一个 Skill 也可以被不同 Command 复用。这种多对多关系是设计上的故意选择——让 Skill 成为可复用的知识单元，让 Command 成为可编排的流程入口。

### 插件文件结构

每个插件的目录结构非常统一（主 README 给出的模板）：

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # 插件元数据：名称、版本、作者
├── .mcp.json                # MCP 连接器配置
├── CONNECTORS.md            # 连接器说明：占位符怎么用、哪些已配置
├── commands/                # 用户斜杠命令（Markdown）
│   └── brainstorm.md
└── skills/                  # 领域技能（Markdown）
    ├── write-spec/
    │   └── SKILL.md
    └── roadmap-update/
```

没有 `package.json`、没有构建脚本、没有运行时依赖。改一个 Skill 的行为就是改一段 Markdown——改完下次触发即生效，不需要部署、不需要重启。这种"文件即配置"的设计让插件迭代速度极快，但也意味着没有类型检查、没有单元测试，质量完全靠 code review 和实际运行把关。

值得单独说的是 `.mcp.json` 的真实形态。以 data 插件为例，里面 pre-configure 的是一串 HTTP 型 MCP 端点：BigQuery 指向 `https://bigquery.googleapis.com/mcp`，Amplitude 指向 `https://mcp.amplitude.com/mcp`，而 Snowflake 和 Databricks 两项的 URL 是空字符串。CONNECTORS.md 解释了原因：官方把这两个当作占位符（"MCP URL not yet configured"），因为各家自建数仓的接入方式不同，需要团队自己填。

配套的 CONNECTORS.md 还定了一套 `~~category` 占位符语法：技能文件里写 `~~data warehouse`、`~~notebook` 这样的类别占位，不写死具体产品。`~~data warehouse` 可以是 Snowflake、BigQuery，也可以是任何带 MCP 服务器的数仓。插件因此是工具无关的——`.mcp.json` 预配置的是推荐选项，换工具不动技能文件。

---

## 二、三个任务流：用具体案例把三层串起来

结构讲完，看三个真实场景，把完整任务怎么流过 Commands → Skills → Connectors 串起来。案例中的数据均为说明性示例。

### 案例 1：产品经理写一份 SSO 功能的 PRD

**触发**: 用户在对话里输入 `/write-spec`（会话中显示为 `/product-management:write-spec`）

**流程**:

1. **Command/Skill 启动**：`write-spec` 被触发，启动一个交互式对话。技能文件明确要求"Be conversational — do not dump all questions at once"——先问目标用户、约束条件、成功指标，再生成文档。技能描述里写明它的用途是"turning a vague idea or user request into a structured document"。
2. **结构注入**：这个技能编码了 PRD 的结构（问题陈述、目标、用户故事、需求分级、成功指标、开放问题）、需求按 Must-Have（P0）/ Nice-to-Have（P1）/ Future Considerations（P2）分级的规则，以及每级的判断标准——比如 P0 的检验问题是"如果砍掉这个，功能还能解决核心问题吗"。
3. **Connector 拉取上下文**：如果配置了 Linear 或 Jira 连接器，AI 可以拉取相关工单的当前状态；如果配置了 Figma，可以看设计稿。没连这些工具时，技能文件的要求是直接用手头信息继续，不要打断用户去要连接。
4. **输出**：一份结构化的 PRD Markdown 文件，包含问题陈述、用户故事、功能需求（按 P0/P1/P2 分级）、成功指标、开放问题清单——每个开放问题还会标注该由谁（工程/设计/法务/数据）来回答。

用户只敲了一个命令。Skills 和 Connectors 在背后协作完成了信息收集、结构补全、上下文注入。用户不需要知道这些层怎么配合——三层分离的好处在这里：复杂度对用户不可见，对插件作者可改。

### 案例 2：数据分析师做一次月度收入趋势分析

**触发**: `/analyze 过去 12 个月的月度收入趋势，按产品线拆分`

**流程**:

1. **Command 启动**：`/analyze` 启动分析流程（data 插件 README 命令表列了 6 个命令：`/analyze`、`/explore-data`、`/write-query`、`/create-viz`、`/build-dashboard`、`/validate`）。
2. **SQL 生成**：`sql-queries` 技能注入——它自称覆盖所有主流数仓方言（Snowflake、BigQuery、Databricks、PostgreSQL），携带各方言的实践建议，比如 Snowflake 下按聚类键过滤做分区裁剪、BigQuery 下过滤分区列以减少扫描量。AI 先写 SQL，再通过数据仓库连接器执行。
3. **结果处理**：`explore-data` 技能负责理解数据集的形状、质量和模式，做描述统计和异常检查。如果某产品线在某月出现不寻常的低谷，分析会标注出来并提示检查数据管道。
4. **可视化**：`/create-viz` 生成出版级的 Python 可视化，`/build-dashboard` 可以进一步组装成交互式 HTML 仪表盘。
5. **验证**：`/validate` 可选，`validate-data` 技能在报告发出前做方法论审查。
6. **输出**：分析报告 + 可视化 + 置信度评估。

同一个 `/analyze`，连了 Snowflake 就直查库，没连就收 CSV 粘贴。Commands 和 Skills 离开 Connectors 照样跑——知识编码和工具接入是两层独立的能力。这个分离让插件可以先在没有连接器的情况下验证知识逻辑，再接 Connectors 走自动化。

### 案例 3：销售做一次周度预测

**触发**: `/forecast`，上传 CSV 或 CRM 已连接

**流程**:

1. **Command 启动**：`/forecast` 启动预测流程。技能描述写明场景是"forecast call 或和经理的 1:1"——哪些单子在关、哪些有风险、和上次比变了什么。
2. **Skill 激活**：如果 CRM 已连接，`daily-briefing` 技能可以补充当天背景——近期要关的 deal（带过期未更新标记）、等待回复的客户邮件；如果没连，用户直接粘贴 pipeline 导出。
3. **分析**：AI 把 pipeline 按 Closed Won / Commit / Best Case / Pipeline 四桶归类，生成 commit 与 upside 的叙事：每个 Commit 和 Best Case 的 deal 配一句话状态，标记风险（比如长期未更新的 deal），并和上一次快照对比变化——哪些升了、哪些滑了、哪些关了。
4. **输出**：数字表（四桶的金额与数量，commit 总额加粗）+ 变化明细 + 风险提示。

没连 CRM 也能跑，连了就自动化。同一个 Skill 逻辑从头到尾没变过——Connector 只改变数据来源，不改变分析逻辑。

---

## 三、11 个官方插件全景

README 宣布开源的官方插件是 11 个。下表按角色定位、技能数量和关键连接器给出全貌（技能数为 2026-09-19 主干实测，连接器清单来自各插件 README）：

| 插件 | 定位 | Skills | 代表性技能 | 关键 Connectors |
|------|------|--------|-----------|----------------|
| **productivity** | 个人效率与任务管理 | 4 | start, update, task-management, memory-management | Slack, Notion, Asana, Linear, Jira, Monday, ClickUp, Microsoft 365 |
| **product-management** | 产品经理全流程 | 8 | write-spec, roadmap-update, product-brainstorming | Slack, Linear, Asana, Monday, ClickUp, Jira, Notion, Figma, Amplitude, Pendo, Intercom, Fireflies |
| **sales** | 销售自动化 | 36 | call-prep, forecast, pipeline-review | Slack, HubSpot, Close, Clay, ZoomInfo, Notion, Jira, Fireflies, Microsoft 365 |
| **customer-support** | 客服工单处理 | 5 | ticket-triage, draft-response, kb-article | Slack, Intercom, HubSpot, Guru, Jira, Notion, Microsoft 365 |
| **marketing** | 内容与营销 | 8 | draft-content, brand-review, seo-audit | Slack, Canva, Figma, HubSpot, Amplitude, Notion, Ahrefs, SimilarWeb, Klaviyo |
| **legal** | 法务与合同 | 9 | review-contract, triage-nda, compliance-check | Slack, Box, Egnyte, Jira, Microsoft 365 |
| **finance** | 财务与审计 | 8 | reconciliation, variance-analysis, audit-support | Snowflake, Databricks, BigQuery, Slack, Microsoft 365 |
| **data** | 数据分析 | 10 | write-query, validate-data, build-dashboard | Snowflake, Databricks, BigQuery, Definite, Hex, Amplitude, Jira |
| **enterprise-search** | 企业知识搜索 | 5 | search, digest, knowledge-synthesis | Slack, Notion, Guru, Jira, Asana, Microsoft 365 |
| **bio-research** | 生物医学研究 | 6 | scientific-problem-selection, single-cell-rna-qc | PubMed, BioRender, bioRxiv, ClinicalTrials.gov, ChEMBL, Synapse, Wiley, Owkin, Open Targets, Benchling |
| **cowork-plugin-management** | 插件创建与管理 | 2 | create-cowork-plugin, cowork-plugin-customizer | —（无 .mcp.json） |

几点说明：

- sales 的 36 个技能覆盖了从潜客研究、通话准备到复盘的整条链路；bio-research 面向科研人员，有一个 `start` 技能用来查看可用工具。
- 仓库主干上还有 `engineering`、`design`、`human-resources`、`operations`、`small-business`、`pdf-viewer` 等目录（各有完整 README），以及收录第三方插件的 `partner-built`。它们不在 README 宣布的 11 个官方清单里，但 marketplace 清单（`.claude-plugin/marketplace.json`）现在已经收录了 115 个插件——官方 11 个之外，还有 Zapier、Figma、Canva、Datadog、Box 等大量第三方生态。
- 仓库在 2026 年上半年经历过一轮重构：早期版本里每个功能各有一个 `commands/` 目录，现在大部分命令形态的功能并入了 `skills/`，用 SKILL.md 的 `user-invocable` 元数据区分"用户可显式调用"和"仅 AI 自动调用"。各插件 README 的命令表（如 data 的 6 个命令）描述的仍是用户视角的入口，本文两种叫法按上下文使用。

---

## 四、三个代表性插件深度拆解

### 1. Productivity：两层记忆系统的任务管理

最基础的插件，几个设计点值得拆开看。

**命令**（README 命令表）:

| 命令 | 行为 |
|------|------|
| `/start` | 初始化 TASKS.md + CLAUDE.md + memory/ + dashboard.html，然后从你现有的任务清单出发建立工作记忆 |
| `/update` | 清理过期任务，检查记忆空缺，从外部工具同步状态 |
| `/update --comprehensive` | 深度扫描邮件、日历、聊天，标记遗漏的待办，建议新的记忆条目 |

**技能**（4 个）:

| 技能 | 机制 |
|------|------|
| `memory-management` | 双轨记忆：`CLAUDE.md`（工作记忆，存约 30 个最常用缩写和词条） + `memory/` 目录（深度存储，含 glossary.md 全量解码表、people/ 人物档案等） |
| `task-management` | 基于 TASKS.md 的任务跟踪，Markdown 格式，AI 和人共同编辑 |
| `start` | 首次初始化，从既有任务清单引导建立记忆 |
| `update` | 日常同步，带 `--comprehensive` 深度扫描模式 |

**存储结构**（`/start` 在工作目录中生成的产物）:

```
productivity/
├── TASKS.md              # 任务清单
├── CLAUDE.md             # 工作记忆
├── memory/               # 深度记忆
│   ├── glossary.md       # 全量术语解码表
│   └── people/           # 人物档案
└── dashboard.html        # 可视化仪表盘（从插件目录拷贝到工作目录）
```

**双轨记忆**：高频变更的东西（人名缩写、项目代号、本周优先级）放 CLAUDE.md，低频但需要持久化的东西（完整术语表、人物档案、长期偏好）放 memory/ 目录。技能文件里管 glossary.md 叫 "decoder ring"（解码环）：Claude 遇到不认识的缩写，先查 CLAUDE.md 里的高频表，查不到再搜 memory/glossary.md。这和 CPU 的 L1/L2 cache 一个思路——L1 小而快，L2 大而慢，两者配合才能既响应快又不丢上下文。

**Dashboard 分离**：AI 管结构化数据（Markdown），人通过独立 HTML 看聚合指标。改文件格式不影响 Dashboard，改 Dashboard 不破坏数据。`/start` 还特意处理了一个 Cowork 的环境细节：Agent 跑在虚拟机里，`open` 命令打不开用户的浏览器，所以它会提示用户自己从文件浏览器打开 dashboard.html。

**自然语言入口**：不需要记命令格式。说"让 Todd 去做 Oracle 项目的 PSR"，`memory-management` 就能按记忆里的解码表把"Todd"解析为对应的人、把"PSR"解析为对应的内部术语（示例数据，非真实业务数字）。这种解析能力来自 memory/ 目录里持久化的实体关系，每次对话都会加载。

### 2. Product Management：8 个技能覆盖 PM 全流程

当前主干上这个插件有 8 个技能和 1 个独立命令（`/brainstorm`）。核心的几个：

| 技能/命令 | 对应能力 |
|---------|---------|
| `write-spec` | 对话式澄清 → 用户故事 → P0/P1/P2 分级 → PRD 输出 |
| `roadmap-update` | 路线图维护、依赖梳理、Now/Next/Later 格式 |
| `stakeholder-update` | 按受众（高管/工程/客户）切换模板和粒度 |
| `synthesize-research` | 主题分析、affinity mapping、persona 构建 |
| `competitive-brief` | 功能对比矩阵、定位分析、win/loss 分析 |
| `metrics-review` | OKR 层级、指标仪表盘设计、审查节奏 |
| `product-brainstorming` | How Might We、JTBD、First Principles、Opportunity Solution Tree |

**`/brainstorm` 多说两句**。它是 product-management 里少数保留独立 `commands/` 目录的命令，设计目标比"你说个想法我帮你展开"更前置。命令文件编了 4 种起点模式——问题探索、方案生成、假设验证、策略推演——AI 看 PM 带来的是什么自动切。用户问"我们要不要加 AI 搜索"，AI 先切到问题探索追问："用户搜不到东西，是算法的问题，还是信息架构的问题，还是内容可发现性的事？"

`product-brainstorming` 技能文件里有一句："The goal is to understand the problem space deeply before jumping to solutions."（先深挖问题空间，再跳到方案。）这个行为来自技能文件的硬编码约束，靠 prompt engineering 临时调不出来——技能文件每次触发都会被加载，而临时指令在长对话里会被稀释。

### 3. Data：多数据库兼容的分析平台

`data` 插件有 10 个技能，README 命令表列了 6 个命令。值得看的是它处理数据库无关性的方式：

```json
{
  "mcpServers": {
    "snowflake": { "type": "http", "url": "" },
    "databricks": { "type": "http", "url": "" },
    "bigquery": { "type": "http", "url": "https://bigquery.googleapis.com/mcp" },
    "hex": { "type": "http", "url": "https://app.hex.tech/mcp" },
    "amplitude": { "type": "http", "url": "https://mcp.amplitude.com/mcp" }
  }
}
```

这是 data 插件 `.mcp.json` 的实际结构（节选）。Snowflake 和 Databricks 官方留空待填，BigQuery、Hex、Amplitude 给了现成端点。

`sql-queries` 技能不绑任何数据库。它只管"怎么写好 SQL"——窗口函数、CTE、聚合这些公共模式，加各方言的性能要点。用户说"我们用 Snowflake"时，AI 才从技能的方言章节里调 Snowflake 特有的建议（按聚类键过滤、分区裁剪）。技能文件的自我定位是"Write correct, performant SQL across all major data warehouse dialects"。

实际收益就一条：换数据库不动插件，改 `.mcp.json` 的连接目标就行。Skills 层纹丝不动。这让数据团队在迁移数据仓库时不用重写分析逻辑——知识沉淀在 Skill 里，工具切换在 Connector 里。

**`/validate`** 做的事不常见：分析报告发出去之前，跑一轮方法论审查。`validate-data` 技能文件里有一份明确的陷阱清单，检查项包括：

- 分母正确性：比率计算用的分母对不对、会不会为零
- Denominator shifting：两期对比时分母变了，比率不可比
- Survivorship bias（幸存者偏差）
- Simpson's paradox：聚合看和拆开看趋势相反
- Join explosion、时区错位、周期不完整对比、平均的平均

技能文件给每个陷阱配了"问题是什么、怎么查、怎么修"的说明，AI 对着逐项过，最后给出置信度评估。验证项是"分母定义是不是漏了免费用户"这种硬约束，靠"你觉得数据对不对"这种软问题问不出来。把方法论审查固化成 Skill，相当于给每个分析师配了一个不会偷懒的 reviewer。

---

## 五、五个设计模式

翻完这批插件，有 5 个模式反复出现。

### 模式 1：三层分别由三个角色控制

Commands、Skills、Connectors 归三个不同角色管，三层之间是协作关系：

| 层 | 控制者 | 触发方式 | 修改频率 |
|----|-------|---------|---------|
| Commands | 用户 | 显式 `/` 触发 | 按需使用 |
| Skills | AI | 上下文自动激活 | 团队定期 review |
| Connectors | 运维/开发者 | 配置文件绑定 | 基础设施变更时 |

所以团队可以独立改 Commands（交互流程），不碰 Skills；可以独立换 Connectors（换数据库、换 CRM），不碰 Commands 和 Skills。三层耦合在一起时，任何改动都需要跨角色协商，迭代速度会塌掉。

### 模式 2：文件系统即状态存储

所有插件用 Markdown 文件做持久化，不用数据库、不用 API：

- 任务状态 → `TASKS.md`
- 项目记忆 → `CLAUDE.md` + `memory/`
- 插件配置 → `.mcp.json`

收益：Git 可追踪、grep 能搜、编辑器直接改、迁移就是拷文件夹。代价是并发写冲突——但当前设计面向单人使用或小团队，这个代价比引入数据库的复杂度小得多。一旦团队规模上来，需要引入锁机制或迁到数据库，这是当前架构的明确上限。

### 模式 3：Standalone 和 Supercharged 双模式

"Standalone + Supercharged" 是官方 README 里反复出现的说法——engineering 插件的原话是 "Works with any engineering team — standalone with your input, supercharged when you connect your source control, project tracker, and monitoring tools."。以 engineering 为例：

| 能力 | Standalone（无连接器） | Supercharged（有连接器） |
|------|----------------------|------------------------|
| 日报 | 用户口述今天做了什么，AI 负责排版 | 自动拉 commits、PR、工单 |
| 代码审查 | 粘贴 diff 或代码片段 | 直接给 PR 链接拉取 |
| 调试 | 用户描述症状 | 从监控工具拉日志和指标 |
| 事件响应 | 用户描述事件 | 自动拉 on-call 和时间线 |

Skills 层逻辑在两种模式下不变，只是拿输入的方式不同。engineering README 的示例工作流里写得很直白："If your tools are connected, I'll pull your recent commits... Otherwise, tell me what you worked on and I'll format it." 先 Standalone 跑起来，确认有用再接 Connectors——采用路径没有前置依赖。`/brainstorm` 命令文件里甚至画了一张 STANDALONE / SUPERCHARGED 对照框图，哪些能力不依赖工具、接上工具后多出什么，一目了然。

### 模式 4：记忆的冷热分层

`productivity` 的双轨记忆（CLAUDE.md 热层 + memory/ 冷层）体现了一个判断：AI Agent 的记忆系统需要分层、有成本、能淘汰，平铺成向量数据库反而不好用。向量库擅长语义召回，但召回结果没有结构、没有优先级、没有淘汰策略；文件系统的分层记忆补上了这一块——热层只放约 30 个高频词条，冷层全量收编，查找路径固定：先热后冷。

其他插件有各自对应的形态。engineering 插件把架构决策写成 ADR（`/architecture` 命令，输出标准 ADR 格式加权衡分析），把运维知识写成 runbook（`documentation` 技能的职责之一）——这些是"该长期记住的东西被固化成文件"，只是记忆的载体从个人记忆换成了团队文档。

### 模式 5：做和审分开

`data` 的 `/validate`、`engineering` 的 `/deploy-checklist`、`legal` 的 `review-contract`——这些都是独立成型的验证类技能，和执行类技能分开。做和审分成两个技能，工程纪律在 AI Agent 里照样成立。这个分离的好处是审查逻辑可以独立演进——审查清单更新不需要动执行逻辑，执行逻辑改动也不会偷偷绕过审查。

---

## 六、采用指南

想在自己的团队试，按类型走。

### 个人用户 → 从 productivity 开始

```bash
claude plugin marketplace add anthropics/knowledge-work-plugins
claude plugin install productivity@knowledge-work-plugins
```

用 `/start` 初始化，然后正常对话。两周后打开 TASKS.md 和 CLAUDE.md——这两份文件是你工作方式的镜像，看完经常能发现自己没意识到的模式。如果两周后这两份文件还是空的或者不准，说明你的工作内容可能不适合这种结构化记录方式。

配置连接器时留意一件事：`.mcp.json` 里 Snowflake、Databricks 这几项 URL 是官方故意留空的占位符，要么填自己团队的接入点，要么先不连、用 Standalone 模式跑。

### 产品团队 → productivity + product-management + enterprise-search

1. 每个人装 `productivity` 管自己的任务
2. PM 装 `product-management`，先把 `write-spec` 和 `stakeholder-update` 用起来
3. 如果 Slack + Notion 已经配了 MCP，加 `enterprise-search`——跨工具的搜索能省掉大量"这个文档在哪"的来回问询

### 工程团队 → engineering（优先配 GitHub/GitLab MCP）

`engineering` 连了源码仓库之后变化最大（README 命令表列了 6 个命令）：

- `/standup` 自动生成日报——从 commit message 和 PR review 里提取实际产出，避开"I did X"的形式主义模板
- `/review` 对 PR 做结构化审查——安全、性能、风格、正确性四个维度，写在 `code-review` 技能里，改审查标准就是改 Markdown
- `/incident` 走完整的事故响应流程——triage、沟通、缓解、复盘，每个阶段对应一个模板
- `/deploy-checklist` 上线前核对——测试、变更、依赖、回滚方案

如果只能配一个 MCP 连接器，配 GitHub/GitLab。如果配两个，第二个配监控（Datadog / New Relic）。

### 数据分析团队 → data（配数据仓库 MCP）

连上 Snowflake / BigQuery / Databricks 之后，`data` 插件最有用的部分是 `/validate`——报告发出去之前做一轮方法论审查。自动写 SQL 随便哪个 LLM 都会，省掉的是被同事质疑后重新跑数的那一整天。如果团队还没有固定的分析审查流程，先从 `/validate` 的陷阱清单入手，把方法论纪律建立起来再接 Connector。

### 销售团队 → sales（优先配 CRM）

sales 有 36 个技能，挑三个最高频的先跑起来：

- `call-summary`：会议录音或笔记 → 结构化摘要 + 待办 + 跟进邮件草稿
- `forecast`：CSV 或 CRM 数据 → 四桶预测 + commit/upside 拆解 + 风险标记
- `pipeline-review`：Pipeline 数据 → 健康评分 + 优先级排序 + 本周行动计划

如果 CRM 暂时连不上，这些技能都能接受手动数据，不阻塞使用。

### 什么情况下不应该用

- 你的团队还没有明确的角色分工和工作流（先梳理流程，再上插件）
- 你的数据合规要求禁止 AI 访问生产数据库（先做安全评估）
- 你的工作内容高度非标、没有任何可模板化的部分（插件帮不上忙）

---

## 七、常见问题和故障排查

### 问题 1：装了插件，但命令打出来没反应

**原因**：常见于两类情况——只执行了 `marketplace add` 没执行 `plugin install`（前者只是注册了市场，后者才装插件）；或者命令形式写错，会话里实际生效的是带插件前缀的形式（如 `/productivity:update`）。

**解决**：先确认插件已安装（`claude plugin install <插件名>@knowledge-work-plugins`），再按会话里的命令补全提示输入；技能没有自动触发时，检查对话内容是否命中技能 description 里的场景词，或者直接显式调用。

### 问题 2：想定制技能内容，从哪改起

**原因**：官方插件的技能是通用起点，团队术语、审批边界、输出格式都要自己写进去才有生产价值——README "Making Them Yours" 一节明确建议把公司术语和组织结构写进 skill 文件。

**解决**：Fork 仓库，改对应插件的 `skills/<name>/SKILL.md`（Markdown，改完即生效），定制深的可以按 `cowork-plugin-management` 插件的引导创建自己的插件。改动想回馈上游就提 PR。

### 问题 3：Connector 配置了，但 AI 没有调用

**原因**：Skills 层逻辑不变，但 Connector 需要在 `.mcp.json` 中正确配置且可用。特别注意 data 等插件的 `.mcp.json` 里 Snowflake、Databricks 的 URL 是空字符串占位符——不算"已配置"。

**解决**：检查对应连接器的 URL 是否为空、MCP 服务器是否可达，确认 AI 有权限访问；仍不触发时，看 AI 的推理过程了解它为什么判定不需要调用。

### 问题 4：Markdown 文件存状态，会不会有并发写冲突

**原因**：当前设计面向单人使用或小团队，多人同时编辑同一份 TASKS.md 或 CLAUDE.md 确实可能互相覆盖。

**解决**：单人场景不用处理；小团队把工作目录放进 Git，靠提交和合并解决冲突；团队规模再往上，就该考虑把状态迁到真正的存储系统——这是当前架构的明确上限，插件本身没有提供锁机制。

---

## 八、这件事能活多久

回到开头的判断——这个项目真正有价值的是它定下的三条规则，11 个插件只是规则的实例化：

1. **领域知识写成文件，不写成代码**。Markdown 比 Python 适合描述"好的 PRD 长什么样"或"怎么审一份合同"。文件可以被非工程师编辑、进 Git、做 diff review。
2. **用户意图（Commands）、AI 知识（Skills）、外部工具（Connectors）由三个角色独立控制**。三层耦合在一起时，任何改动都需要跨角色协商，迭代速度会塌掉。
3. **能力边界随 Connectors 增减渐进扩展，核心逻辑保持不动**。Standalone 模式是成本最低的信任建立方式。

这三条绑在一起指向一件事：AI Agent 插件体系的工程化。把知识写成结构，把流程写成可复现，把质量写成可验证——写个 prompt 跑一遍看运气，这条路走不远。

如果还在观望 AI Agent 落地，这条路径的验证成本极低——不需要先投一个月的集成工程。装一个 productivity 插件，用一周，打开 TASKS.md 和 CLAUDE.md 看看里面长了什么。如果那两份文件比你自己的任务清单更准更全，就继续。如果没有，卸载。成本就一个文件夹。

---

## 自测题

1. **Commands、Skills、MCP Connectors 三层的控制者分别是谁？**  
   → 用户（显式触发）、AI（上下文自动激活）、运维/开发者（配置文件绑定）

2. **为什么三层要分开控制，而不是写成一个整体？**  
   → 三层耦合在一起时，任何改动都需要跨角色协商，迭代速度会塌掉。分开后，团队可以独立改 Commands（交互流程），不碰 Skills；可以独立换 Connectors（换数据库、换 CRM），不碰 Commands 和 Skills。

3. **产品经理用 write-spec 写一个功能 PRD，整个流程经历了什么？**  
   → 命令/技能启动 → 对话式澄清需求 → 按 P0/P1/P2 分级组织需求 → Connector 拉取上下文（已连接时）→ 输出带开放问题清单的结构化 PRD

4. **Standalone 模式和 Supercharged 模式的核心区别是什么？**  
   → Skills 层逻辑不变，只是拿输入的方式不同。先 Standalone 跑起来验证知识逻辑，再接 Connectors。

5. **什么时候不应该用这个插件体系？**  
   → 团队还没有明确的角色分工和工作流；数据合规要求禁止 AI 访问生产数据库；工作内容高度非标、没有任何可模板化的部分。

---

## 进阶路径

### 阶段一：个人验证（1-2 周）
- 安装 `productivity` 插件，用 `/start` 初始化
- 连续使用一周，打开 TASKS.md 和 CLAUDE.md 看看里面长了什么
- 如果两份文件比你自己的任务清单更准更全，继续；如果没有，卸载

### 阶段二：团队试用（2-4 周）
- 产品团队：每个人装 `productivity` 管自己的任务，PM 装 `product-management`
- 工程团队：装 `engineering`（优先配 GitHub/GitLab MCP）
- 数据分析团队：装 `data`（配数据仓库 MCP）

### 阶段三：定制化（1-3 个月）
- 改 `.mcp.json`，把连接器换成你们真的在用的系统（注意官方留空的占位符项）
- 改 `skills/`，把团队术语、审批边界和输出格式写进去
- 添加自定义 `commands/`，把最高频、最稳定的动作做成固定入口

### 阶段四：生态扩展（3 个月+）
- Fork 仓库，创建自定义插件（README Contributing 一节：改动以 PR 提交）
- 用 `cowork-plugin-management` 插件辅助创建和定制
- 把团队的工作流固化成可复用的插件，分享给更多团队

---

## 练习

### 练习 1：创建一个自定义 Command

**任务**：为你的团队创建一个自定义 Command，用于生成周报。

**要求**：
1. 在 `productivity/commands/` 下创建 `weekly-report.md`
2. 定义 Command 的触发方式、输入参数、输出格式
3. 在 `productivity/skills/` 下创建对应的 Skill，编码周报的结构模板
4. 测试 Command 是否能正确触发并生成周报

<details>
<summary>参考答案</summary>

**Command 文件** (`commands/weekly-report.md`)：

```markdown
---
description: 汇总本周完成情况、下周计划和风险，生成周报
argument-hint: "[补充说明，如收件人或重点]"
---

# /weekly-report

## 输入来源
- 本周完成的任务（从 TASKS.md 和 Git 提交记录中拉取）
- 下周计划（从 TASKS.md 未完成项和 CLAUDE.md 中读取）
- 遇到的问题和风险（从记忆中读取）

## 输出格式
- 本周完成情况（按项目分组）
- 下周计划（按优先级排序）
- 风险和建议（如果有）
```

**Skill 文件** (`skills/weekly-report/SKILL.md`)：

```markdown
---
name: weekly-report
description: 生成结构化周报。当用户要求汇总本周工作、写周报或准备周会材料时使用。
---

# 周报生成技能

## 周报结构
1. 本周亮点（3-5 条）
2. 按项目分组的完成情况
3. 数据指标（如果有）
4. 下周计划
5. 需要帮助的地方

## 写作风格
- 量化结果，用数据说话
- 突出价值和影响，不只是罗列任务
- 风险要具体，附上建议方案
```

</details>

---

### 练习 2：配置一个 MCP 连接器

**任务**：为 `data` 插件配置一个真实可用的 MCP 连接器，让 AI 能够查询你的数据。

**要求**：
1. 阅读 `data/.mcp.json` 和 `data/CONNECTORS.md`，理解 HTTP 型连接器的配置方式和占位符约定
2. 确认哪些连接器已有官方端点（如 BigQuery）、哪些是留空待填的占位符（如 Snowflake、Databricks）
3. 把你们团队实际在用的数据仓库接入 `.mcp.json`
4. 测试连接器是否能正常工作（AI 是否能执行 SQL 查询）

<details>
<summary>参考答案</summary>

**配置思路**（以 BigQuery 为例，官方已提供 MCP 端点）：

data 插件自带的 `.mcp.json` 中 BigQuery 一项已指向 `https://bigquery.googleapis.com/mcp`，接入时主要完成鉴权配置。如果你们用的是 Snowflake，则把空占位符换成自己团队的 MCP 接入点：

```json
{
  "mcpServers": {
    "snowflake": {
      "type": "http",
      "url": "https://your-snowflake-mcp-endpoint.example.com/mcp"
    }
  }
}
```

注意：`@modelcontextprotocol` 官方服务器列表里没有 Snowflake 实现，不要照抄其他插件的包名；优先确认你们的数据平台是否提供官方 MCP 端点，或使用经过审查的社区实现。

**测试步骤**：
1. 启动 Claude Cowork 或 Claude Code，确认插件已安装
2. 输入 `/analyze 过去 30 天的用户增长趋势`
3. 检查 AI 是否调用了刚配置的连接器
4. 检查生成的 SQL 是否符合 `sql-queries` 技能中的方言实践

</details>

---

### 练习 3：分析一个插件的三层结构

**任务**：选择一个官方插件（除了 `productivity`），分析它的命令、技能和连接器三层结构。

**要求**：
1. 列出所有命令和它们对应的技能
2. 列出所有技能和它们的触发条件（看 SKILL.md 的 description 字段）
3. 列出所有连接器和它们提供的工具
4. 画一张类似本文"三层结构"的图，但针对你选择的插件

<details>
<summary>参考答案（以 `engineering` 插件为例，基于 2026-09-19 主干）</summary>

**命令**（README 命令表）：
- `/standup` → 从近期活动生成站会日报
- `/review` → 代码审查（安全、性能、风格、正确性）
- `/debug` → 结构化调试：复现、隔离、定位、修复
- `/architecture` → 架构决策记录（ADR 格式加权衡分析）
- `/incident` → 事故响应：triage、沟通、缓解、复盘
- `/deploy-checklist` → 上线前核对清单

**技能**（skills/ 目录，10 个）：
- `standup`、`code-review`、`debug`、`architecture`、`incident-response`、`deploy-checklist`：与命令同名，承载各流程的执行知识
- `system-design`：系统与服务设计，架构图、API 设计、数据建模
- `tech-debt`：技术债的识别、分类与还债计划
- `testing-strategy`：测试策略，单元/集成/e2e 覆盖与测试计划
- `documentation`：技术文档维护，README、API 文档、runbook、onboarding 指南

**Connectors**（README）：
- 源码托管：GitHub/GitLab → commits、PR、issues
- 项目跟踪：Linear/Jira → 工单、里程碑
- 监控：Datadog、New Relic → 日志、指标
- 事件管理：PagerDuty → on-call 信息、事件时间线

**三层结构图**：

```
用户 → /standup
         ↓
    Commands (显式触发)
         ↓
    Skills (注入日报生成知识)
         ↓
    Connectors (拉取 GitHub/Jira 数据；未连接时改为口述)
         ↓
    输出：结构化日报
```

</details>

---

## 资料口径说明

1. **来源标注**：本文以 [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) 仓库的 README、CONNECTORS.md、plugin.json 和各 SKILL.md 为准，并基于 2026-09-19 的仓库主干和 GitHub API 做了逐项事实校验（Stars/Forks、插件与技能清单、命令表、.mcp.json 结构、关键引文）。
2. **时效性**：仓库迭代很快——2026 年 5 月本文初稿时多数功能还在 `commands/` 目录，9 月主干上大部分已并入 `skills/`，marketplace 收录也从 11 个官方扩展到 115 个。文中数量与命令形式均以 2026-09-19 主干为准，后续可能变化。
3. **示例数据**：文中涉及的人名、项目代号、金额等示例数据均为说明性内容，非真实业务数字；三个任务流中的对话细节是按技能文件描述的流程还原，非逐字实录。
4. **功能边界**：本文描述的是仓库当前状态，Anthropic 可能在不通知的情况下调整插件功能、增加或下线某些 Commands/Skills/Connectors。
5. **适用场景**：本文的采用路径和建议基于仓库官方文档和常见团队实践，你的团队可能需要根据实际情况调整。
6. **合规要求**：如果您的团队在受监管行业（金融、医疗、政府等），在连接生产数据库或使用 AI 处理敏感数据前，请先完成安全评估和合规审批。
