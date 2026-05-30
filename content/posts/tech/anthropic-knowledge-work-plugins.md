---
title: "Anthropic Knowledge Work Plugins：把 AI 插件从写代码改成了写 Markdown"
slug: "anthropic-knowledge-work-plugins"
description: "Anthropic 开源了 11 款知识工作插件，定义了一套无代码、纯文件驱动的 AI Agent 插件体系。本文拆解 Commands × Skills × MCP Connectors 三层架构，用三个真实任务流还原插件的工作方式，给出团队采纳路径。"
date: 2026-05-29T19:30:00+08:00
lastmod: 2026-05-30T12:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Anthropic", "Claude", "MCP", "AI Agent", "插件体系", "Skills", "Commands", "知识工作"]
hiddenFromHomePage: false
featuredImage: ""
externalUrl: ""
originLinks: []
---

# Anthropic Knowledge Work Plugins：把 AI 插件从写代码改成了写 Markdown

**GitHub**: [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)

---

市面上大部分 AI 插件系统都在走同一条路：提供 SDK、定义 API、写胶水代码、打包、发布。Anthropic 这 11 个开源插件走的完全是另一条路——**零代码，纯 Markdown + JSON 驱动**。

这不只是省掉代码的事。它背后是另一个判断：一个 AI Agent 在一个领域里能干多少活，不取决于它连了多少工具，而取决于它对这个领域的**知识编码有多细、有多准确**。而 Markdown 文件——不是 Python 脚本、不是数据库 schema、不是配置文件模板——是当前最适合做这件事的载体。

容易写、容易改、容易审、容易版本控制、容易让非工程师参与。11 个插件覆盖了产品管理、销售、客服、数据分析、工程开发、市场营销、法务、财务、生物研究、企业搜索和插件管理，每个插件都遵循同一套三层结构：Commands（用户显式触发）、Skills（AI 自动调用）、MCP Connectors（连接外部工具）。

下面把这三层拆开，然后看几个具体插件怎么跑任务流，最后说清楚不同类型团队该从哪入手。

---

## 一、三层结构：一次完整交互是怎么跑通的

先给一张总览图，避免读者看到后面把 Commands、Skills、Connectors 的关系搞混。这三层不是"上层调下层"的调用链，而是**三个不同决策者**的分工：

```
                    ┌─────────────────────────────┐
                    │          用户（人）           │
                    │    /write-spec  /analyze     │
                    │    /forecast   /standup       │
                    └─────────────┬───────────────┘
                                  │ 显式触发
                                  ▼
┌─────────────────────────────────────────────────┐
│              Commands（命令层）                   │
│  谁触发：用户                                    │
│  做什么：启动一个完整工作流                       │
│  例子：/standup → 拉 commits/PR/工单 → 生成日报   │
│        /write-spec → 对话澄清需求 → 输出 PRD      │
└──────────────────────┬──────────────────────────┘
                       │ 命令内部可能自动激活 Skills
                       ▼
┌─────────────────────────────────────────────────┐
│               Skills（技能层）                    │
│  谁触发：AI 根据上下文自主判断                   │
│  做什么：注入领域知识、最佳实践、工作流模板       │
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

**三层的关键区别**：
- Commands 是"入口"——没有用户主动触发就不会跑
- Skills 是"知识"——AI 自己判断该不该用，用户不用管
- Connectors 是"手脚"——Skills 通过它们访问外部世界

需要格外注意的边界：**Commands 和 Skills 不是一一对应的**。一个 Command 可能调用多个 Skills，一个 Skill 也可能被多个 Commands 复用。比如 `/incident`（事件响应命令）可能同时激活 `incident-response`、`system-design`、`documentation` 三个技能。

### 插件文件结构

每个插件的目录结构非常统一：

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # 插件元数据：名称、版本、作者
├── .mcp.json                # MCP 连接器配置
├── commands/                # 用户斜杠命令（Markdown）
│   ├── analyze.md
│   ├── write-spec.md
│   └── ...
└── skills/                  # AI 自动调用的领域技能（Markdown）
    ├── feature-spec/
    │   ├── SKILL.md
    │   └── ...
    └── roadmap-management/
```

没有 `package.json`、没有构建脚本、没有运行时依赖。改一个 Skill 的行为就是改一段 Markdown——改完即刻生效，不需要部署、不需要重启。

---

## 二、三个任务流：用具体案例把三层串起来

光看结构容易觉得抽象。下面用三个真实场景，看一次完整任务怎么流过 Commands → Skills → Connectors。

### 案例 1：产品经理写一份 SSO 功能的 PRD

**触发**: 用户在对话里输入 `/write-spec`

**流程**:

1. **Command 启动**：`/write-spec` 被触发，启动一个交互式对话。AI 不直接生成文档，而是先追问目标用户、约束条件、成功指标。
2. **Skill 注入**：对话进入"规格文档"上下文后，`feature-spec` 技能自动激活。这个技能编码了 PRD 的结构（问题陈述 → 用户故事 → 需求分类 → 验收标准）、MoSCoW 优先级框架、常见反模式（比如把 solution 当 requirement 写）。
3. **Connector 拉取上下文**：如果配置了 Jira 连接器，AI 可能自动拉取相关 Epic 和 Story 的当前状态；如果配置了 Figma，会拉设计稿；如果配置了 Amplitude，会拉当前版本的使用数据作为决策依据。
4. **输出**：一份结构化的 PRD Markdown 文件，包含问题陈述、用户故事、功能需求（按 P0/P1/P2 分级）、成功指标、开放问题清单。

关键点：**用户只发了一个命令，但背后 Skills 和 Connectors 协作完成了信息收集、结构补全和上下文注入**。

### 案例 2：数据分析师做一次月度收入趋势分析

**触发**: `/analyze 过去 12 个月的月度收入趋势，按产品线拆分`

**流程**:

1. **Command 启动**：`/analyze` 启动分析流程。
2. **Skill 激活**：`sql-queries` 技能注入——它携带了多数据库方言的最佳实践（Snowflake 的 partition pruning、BigQuery 的 slot 优化）、常见查询模式、反模式清单。AI 先写 SQL，再通过 Snowflake 连接器执行。
3. **结果处理**：`data-exploration` 技能介入，做描述统计和异常检测。发现产品线 A 在 3 月有一个不正常的低谷后，自动标注并建议检查是否有数据管道问题。
4. **可视化**：`data-visualization` 技能生成趋势图代码。
5. **验证**：`/validate` 可选，`data-validation` 技能做 sanity check——分母是否包含了不该包含的数据、聚合逻辑是否有偏、解释是否有 survivorship bias。
6. **输出**：分析报告 + 可视化图表 + 置信度评估。

关键点：**同一个 `/analyze` 命令，连了 Snowflake 就直接查库，没连就接受 CSV 粘贴——Commands 和 Skills 不依赖 Connectors 也能工作**。这是项目设计中一条重要原则：知识能力（Skills）和工具能力（Connectors）解耦。

### 案例 3：销售做一次周度预测

**触发**: `/forecast`，上传 CSV 或 CRM 已连接

**流程**:

1. **Command 启动**：`/forecast` 启动预测流程，AI 询问配额和时间窗口。
2. **Skill 激活**：如果 CRM 已连接，`daily-briefing` 技能自动补充近期更新过的 deal 状态；如果没连，用户粘贴 CSV。
3. **分析**：AI 生成加权预测（best case / likely / worst case），标记风险项：过期未更新的 deal、单一联系人（single-threaded）的 deal、Pipeline 覆盖倍数。
4. **输出**：预测报告 + commit vs. upside 拆解 + 缺口分析。

这个案例展示的其实是**渐进式采用**：没连 CRM 时也能用（手动提供数据），连了 CRM 就自动化——同一个 Skill 逻辑不变。

---

## 三、11 个官方插件全景

官方 Marketplace 中提供了 11 个插件。下表按角色定位、Command 数量、Skill 数量和关键连接器给出全貌：

| 插件 | 定位 | Commands | Skills | 关键 Connectors |
|------|------|----------|--------|----------------|
| **productivity** | 个人效率与任务管理 | 2 | 2 | Slack, Notion, Asana, Linear, Jira, Monday, ClickUp, Microsoft 365 |
| **product-management** | 产品经理全流程 | 7 | 7 | Slack, Linear, Jira, Notion, Figma, Amplitude, Intercom |
| **sales** | 销售自动化 | 3 | 6 | HubSpot, Close, Clay, ZoomInfo, Fireflies |
| **customer-support** | 客服工单处理 | 5 | 5 | Intercom, HubSpot, Guru, Jira, Notion |
| **marketing** | 内容与营销 | 7 | 5 | Canva, Figma, HubSpot, Amplitude, Ahrefs, Klaviyo |
| **legal** | 法务与合同 | 5 | 6 | Box, Egnyte, Jira |
| **finance** | 财务与审计 | 5 | 6 | Snowflake, Databricks, BigQuery |
| **data** | 数据分析 | 6 | 6 | Snowflake, Databricks, BigQuery, Definite, Hex, Amplitude |
| **enterprise-search** | 企业知识搜索 | 2 | 3 | Slack, Notion, Guru, Jira, Asana |
| **bio-research** | 生物医学研究 | 1 | 5 | PubMed, BioRender, bioRxiv, ClinicalTrials.gov, ChEMBL, Benchling |
| **cowork-plugin-management** | 插件创建与管理 | 0 | — | — |
| **engineering** | 软件工程 | 6 | 6 | GitHub, GitLab, Linear, Jira, Datadog, PagerDuty |

> 注：`cowork-plugin-management` 用于创建和定制插件，仓库中仅有 `skills/` 目录，无独立 Commands。`bio-research` 主要面向科研人员，通过 `/start` 查看可用工具，未按传统 Command 表格列出。仓库中还有 `design`、`human-resources`、`operations`、`partner-built`、`pdf-viewer`、`small-business` 等目录，部分由社区贡献，功能完整度不一。

---

## 四、三个代表性插件深度拆解

### 4.1 Productivity：两层记忆系统的任务管理

这是最基础的插件，但设计上藏了很多心思。

**Commands（2 个）**:

| 命令 | 行为 |
|------|------|
| `/start` | 初始化 TASKS.md + CLAUDE.md + memory/ + dashboard.html，然后问你的角色、团队和当前优先级来填充记忆 |
| `/update` | 清理过期任务，检查记忆空缺，从外部工具同步状态 |
| `/update --comprehensive` | 深度扫描邮件、日历、聊天，标记遗漏的待办，建议新的记忆条目 |

**Skills（2 个）**:

| 技能 | 机制 |
|------|------|
| `memory-management` | 双轨记忆：`CLAUDE.md`（工作记忆，轻量、高频读写） + `memory/` 目录（深度存储，按 project-context / user-preferences 等子目录组织） |
| `task-management` | 基于 TASKS.md 的任务跟踪，Markdown 格式，AI 和人共同编辑 |

**存储结构**:

```
productivity/
├── TASKS.md              # 任务清单
├── CLAUDE.md             # 工作记忆
├── memory/               # 深度记忆
│   ├── project-context/
│   └── user-preferences/
└── dashboard.html        # 可视化仪表盘
```

**值得注意的设计**：

1. **双轨记忆**：工作记忆存高频变更的东西（人名缩写、项目代号、本周优先级），深度记忆存低频但需要持久化的东西（org 结构、长期偏好、历史决策）。这和计算机体系结构里的 L1/L2 cache 思路一致——不是概念堆砌，是工程判断。
2. **Dashboard 分离**：AI 管理结构化数据（Markdown），人类通过独立 HTML 文件查看聚合指标。这两者不耦合——改文件格式不影响 Dashboard，改 Dashboard 不破坏数据。
3. **自然语言入口**：不需要记命令格式。说"让 Todd 去做 Oracle 项目的 PSR"，`memory-management` 就能把"Todd"解析为"Todd Martinez（财务负责人）"，把"PSR"解析为"Pipeline Status Report"，把"Oracle 项目"解析为"$2.3M，Q2 关单"。

### 4.2 Product Management：7 个命令覆盖 PM 全流程

所有 7 个命令都对应一个同名的 Skill。这不是形式上的一一对应——而是 **"Command 定义工作流边界，Skill 提供执行知识"** 的分工：

| Command | 对应 Skill | 核心机制 |
|---------|-----------|---------|
| `/write-spec` | `feature-spec` | 对话式澄清 → 用户故事 → MoSCoW 分级 → PRD 输出 |
| `/roadmap-update` | `roadmap-management` | RICE 优先级框架、依赖映射、Now/Next/Later 格式 |
| `/stakeholder-update` | `stakeholder-comms` | 按受众（高管/工程/客户）切换模板和粒度 |
| `/synthesize-research` | `user-research-synthesis` | 主题分析、affinity mapping、persona 构建 |
| `/competitive-brief` | `competitive-analysis` | 功能对比矩阵、定位分析、win/loss 分析 |
| `/metrics-review` | `metrics-tracking` | OKR 层级、指标仪表盘设计、审查节奏 |
| `/brainstorm` | `product-brainstorming` | How Might We、JTBD、First Principles、Opportunity Solution Tree |

**`/brainstorm` 值得单独说两句**。它不是"你说个想法我帮你展开"的那种头脑风暴。`product-brainstorming` Skill 里编码了 4 种对话模式——问题探索、方案生成、假设验证、策略推演——AI 会根据当前阶段自动切模式。比如用户问"我们要不要加 AI 搜索"，AI 不会立刻回答"加"或"不加"，而是先切到"问题探索"模式追问："用户搜不到东西时，到底是搜索算法的问题，还是信息架构的问题，还是内容可发现性的问题？"

这种"先挑战问题本身"的行为，不是靠 prompt engineering 实现的，而是 Skill 文件里明确写了"before jumping to solutions, test whether the stated problem is the real problem"。

### 4.3 Data：多数据库兼容的分析平台

`data` 插件有 6 个 Commands 和 6 个 Skills，和 Product Management 一样的对称结构。但我更想讲它处理**数据库无关性**的方式：

```yaml
# .mcp.json 中可以挂任意 SQL 兼容数据库
Connectors:
  - Snowflake
  - Databricks
  - BigQuery
  - Definite
  - 任意 Generic SQL
```

关键在于 `sql-queries` Skill 不绑定任何具体数据库。它只编码"怎么写好 SQL"——公共模式、性能反模式、方言中立的最佳实践。当用户说"我们在用 Snowflake"，AI 才从 Skill 的"方言适配"部分读取 Snowflake 特有的优化规则（比如 `QUALIFY` 子句、`CLUSTER BY` 策略）。

这套设计的工程收益：换一个数据库不需要换插件，只需要改 `.mcp.json` 中的连接目标。Skills 层保持不变。

**`/validate` 命令也不常见**。它做的事是——在分析报告发给同事之前，跑一轮方法论审查。检查的问题包括：

- 分母定义是不是漏了某个用户段
- 聚合方式会不会产生 Simpson's paradox
- 趋势解释是不是考虑到了季节性
- 有没有 survivorship bias

这些检查不是一句 prompt 能解决的——`data-validation` Skill 文件里给了具体的检查清单和反例，AI 对照着逐条验证。单就这个命令，评估后报告出错率显著降低。

---

## 五、设计模式的提炼

翻完 11 个插件的结构后，有 5 个反复出现的模式值得单独抽取出来：

### 模式 1：三层决策权分离，不是三层调用链

Commands、Skills、Connectors 不构成调用栈。它们分别由**人、AI、运维**三个不同角色控制：

| 层 | 控制者 | 触发方式 | 修改频率 |
|----|-------|---------|---------|
| Commands | 用户 | 显式 `/` 触发 | 按需使用 |
| Skills | AI | 上下文自动激活 | 团队定期 review |
| Connectors | 运维/开发者 | 配置文件绑定 | 基础设施变更时 |

这意味着一个团队可以独立优化 Commands（改交互流程），不动 Skills；可以独立调整 Connectors（换数据库或 CRM），不动 Commands 和 Skills。

### 模式 2：文件系统即状态存储

所有插件用 Markdown 文件做持久化，不用数据库、不用 API：

- 任务状态 → `TASKS.md`
- 项目记忆 → `CLAUDE.md`
- 插件配置 → `.mcp.json`

带来的收益：可 Git 版本控制、可 grep、可直接用编辑器改、迁移时就是复制文件夹。代价是并发写冲突——但当前设计下（单人使用或小团队），这个代价远小于引入数据库带来的复杂度。

### 模式 3：Standalone + Supercharged 双模式

每个插件都设计了两种运行模式。以 Engineering 插件为例：

| 能力 | Standalone（无连接器） | Supercharged（有连接器） |
|------|----------------------|------------------------|
| 日报 | 用户口述今天做了什么 | 自动拉 commits、PR、工单 |
| 代码审查 | 粘贴 diff 或代码片段 | 直接从 GitHub PR 拉取 |
| 调试 | 用户描述症状 | 从 Datadog 拉日志和指标 |
| 事件响应 | 用户描述事件 | PagerDuty 自动拉 on-call 和 Timeline |

Skills 层的逻辑在这两种模式下完全不变——它只是获取输入的方式不同。这种设计让采用路径变得很平滑：先用 Standalone 跑起来，确认价值了再投入集成。

### 模式 4：记忆的冷热分层

`productivity` 插件的双轨记忆不是孤立的设计。`engineering` 插件也有类似分层——活跃项目上下文放在 CLAUDE.md，历史 ADR 和 runbook 放在知识库连接器里。这个模式的核心判断：**AI Agent 的记忆系统不该是平铺的向量数据库，而应该是分层的、有成本的、可淘汰的**。

### 模式 5：验证技能独立于执行技能

`data` 的 `/validate`、`engineering` 的 `/deploy-checklist`、`legal` 的合同审查——这些不是"锦上添花的检查步骤"，而是独立成型的验证 Skill。做和审分离，这是工程纪律在 AI Agent 设计中的体现。

---

## 六、采用指南：不同类型的团队该从哪开始

如果读完想在自己的团队里试试，下面是一个按团队类型划分的启动路径：

### 个人用户 → 从 productivity 开始

```bash
claude plugin marketplace add anthropics/knowledge-work-plugins
claude plugin install productivity@knowledge-work-plugins
```

用 `/start` 初始化，然后正常对话。两周后回来看 TASKS.md 和 CLAUDE.md 里积累了什么东西——这两份文件本身就是你工作方式的镜像，看完往往会发现一些模式你自己都没意识到。

### 产品团队 → productivity + product-management + enterprise-search

三条并行推进：

1. 每个人装 `productivity` 管自己的任务
2. PM 装 `product-management`，先把 `/write-spec` 和 `/stakeholder-update` 用起来
3. 如果 Slack + Notion 已经配了 MCP，加 `enterprise-search`——跨工具的搜索能省掉大量"这个文档在哪"的来回问询

### 工程团队 → engineering（优先配 GitHub/GitLab MCP）

`engineering` 插件在连了源码仓库之后的价值跃升最大：

- `/standup` 自动生成日报——不是形式上的"我做了什么"，而是从 commit message 和 PR review 里提取的实际产出
- `/review` 对 PR 做结构化审查——安全检查、性能检查、代码风格、正确性——四种检查有各自的 Skill 文件，改审查标准就是改 Markdown
- `/incident` 走完整的事故响应流程——triage → 沟通 → 缓解 → 复盘——每个阶段有对应的模板

如果只能配一个 MCP 连接器，配 GitHub/GitLab。如果配两个，第二个配监控（Datadog / New Relic）。

### 数据分析团队 → data（配数据仓库 MCP）

连上 Snowflake / BigQuery / Databricks 之后，`data` 插件最直接的价值不是"自动写 SQL"（随便一个 LLM 都会写），而是 `/validate`——在报告发出去之前做一轮方法论审查。这个命令省掉的不是一个 prompt，是发出去后被同事质疑然后重新跑数的那一整天。

### 销售团队 → sales（优先配 CRM）

三个 Command 覆盖了销售最频繁的三个动作：

- `/call-summary`：会议录音或笔记 → 结构化摘要 + 待办 + 跟进邮件草稿
- `/forecast`：CSV 或 CRM 数据 → 加权预测 + 风险标记
- `/pipeline-review`：Pipeline 数据 → 健康评分 + 优先级排序 + 本周行动计划

如果 CRM 暂时连不上，三个命令都能接受手动数据，不阻塞使用。

### 什么情况下不应该用

- 你的团队还没有明确的角色分工和工作流（先梳理流程，再上插件）
- 你的数据合规要求禁止 AI 访问生产数据库（先做安全评估）
- 你的工作内容高度非标、没有任何可模板化的部分（插件帮不上忙）

---

## 七、这件事对 AI Agent 行业意味着什么

回到开头的判断——这个项目的真正意义不在 11 个插件的数量或覆盖面。

它定义了三条规则，这三条规则可能比具体插件存活得更久：

1. **AI Agent 的领域知识应该编码为文件，而不是代码**。Markdown 比 Python 更适合描述"一个好的 PRD 长什么样"或"怎么审查一份合同"。文件可以被非工程师编辑、可以被 Git 追踪、可以被 diff review。
2. **用户意图（Commands）、AI 知识（Skills）、外部工具（Connectors）应该由三个不同的角色独立控制**。混在一起的结果是谁都不敢改。
3. **AI Agent 的能力边界应该可以随着连接器的增减渐进扩展，而不需要重写核心逻辑**。Standalone 模式是门槛最低的信任建立方式。

这三条规则共同指向一个方向：AI Agent 插件体系的**工程化**。不是"写个 prompt 然后祈祷"，而是"把知识结构化、把流程可复现、把质量可验证"。

对还在观望 AI Agent 落地的团队，这条路径的最大吸引力在于——你不需要先投入一个月的集成工程才能验证价值。装一个 productivity 插件，用一周，看看 TASKS.md 和 CLAUDE.md 里长了什么。如果那两份文件里的内容让你觉得"确实比我自己维护的任务清单更准、更全"，那就继续。如果没有，卸载就行——成本就是一个文件夹。

---

*本文基于 GitHub [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) 公开信息撰写，数据截取至 2026-05-30。插件结构和功能细节来自仓库 README、plugin.json 和示例工作流。*