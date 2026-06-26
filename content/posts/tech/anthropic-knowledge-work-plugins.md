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

Anthropic Knowledge Work Plugins：把 AI 插件从写代码改成了写 Markdown

**GitHub**: [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)

> **快速信息卡**
> - **Stars**: 21,961+
> - **Forks**: 2,563+
> - **License**: Apache-2.0
> - **语言**: Python
> - **最后更新**: 2026-06-26

**学习目标**：读完后你能回答——
- Commands、Skills、MCP Connectors 三层各自的职责是什么，为什么这三层要分开控制
- 11 个官方插件按什么思路划分，你的团队该从哪一个试起
- 一个完整的任务流（如 Pitch Agent）从触发到产出经历了什么，哪些环节必须人工审核
- 怎么把这个仓库接进自己的团队流程——先改哪一层，后改哪一层
- 这个插件体系的设计判断有哪些可以迁移到别的行业

**目录**
- [一、三层结构：一次完整交互是怎么跑通的](#一三层结构一次完整交互是怎么跑通的)
- [二、三个任务流：用具体案例把三层串起来](#二三个任务流用具体案例把三层串起来)
- [三、11 个官方插件全景](#三11-个官方插件全景)
- [四、三个代表性插件深度拆解](#四三个代表性插件深度拆解)
- [五、五个设计模式](#五五个设计模式)
- [六、采用指南](#六采用指南)
- [七、这件事能活多久](#七这件事能活多久)
- [自测题](#自测题)
- [进阶路径](#进阶路径)

---

市面上大部分 AI 插件系统都在走同一条路：提供 SDK、定义 API、写胶水代码、打包、发布。Anthropic 这 11 个开源插件走的是另一条路——**零代码，纯 Markdown + JSON 驱动**。

省掉代码是表层。更实际的考虑是：一个 AI Agent 在一个领域里能干多少活，取决于它对这个领域的**知识编码有多细、有多准确**。Markdown 文件——可读、可改、可进 Git——是当前最适合做这件事的载体。相比 Python 脚本、数据库 schema、配置文件模板，Markdown 的门槛最低，非工程师也能直接改。

11 个插件覆盖了产品管理、销售、客服、数据分析、工程开发、市场营销、法务、财务、生物研究、企业搜索和插件管理，每个插件都遵循同一套三层结构：Commands（用户显式触发）、Skills（AI 自动调用）、MCP Connectors（连接外部工具）。

下面把这三层拆开，看几个具体插件怎么跑任务流，最后说清楚不同类型团队该从哪入手。

---

## 一、三层结构：一次完整交互是怎么跑通的

先给一张总览图。Commands、Skills、Connectors 分属三个不同角色，三层之间是协作关系：

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

一个容易踩的坑：Commands 和 Skills 之间没有一对一映射。`/incident` 一个命令下去，可能同时激活 `incident-response`、`system-design`、`documentation` 三个技能。反过来，一个 Skill 也可以被不同 Command 复用。这种多对多关系是设计上的故意选择——让 Skill 成为可复用的知识单元，让 Command 成为可编排的流程入口。

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

没有 `package.json`、没有构建脚本、没有运行时依赖。改一个 Skill 的行为就是改一段 Markdown——改完即刻生效，不需要部署、不需要重启。这种"文件即配置"的设计让插件迭代速度极快，但也意味着没有类型检查、没有单元测试，质量完全靠 code review 和实际运行把关。

---

## 二、三个任务流：用具体案例把三层串起来

结构讲完，看三个真实场景，把完整任务怎么流过 Commands → Skills → Connectors 串起来。

### 案例 1：产品经理写一份 SSO 功能的 PRD

**触发**: 用户在对话里输入 `/write-spec`

**流程**:

1. **Command 启动**：`/write-spec` 被触发，启动一个交互式对话。AI 先追问目标用户、约束条件、成功指标，再生成文档——直接出 PRD 容易把 solution 当 requirement 写。
2. **Skill 注入**：对话进入"规格文档"上下文后，`feature-spec` 技能自动激活。这个技能编码了 PRD 的结构（问题陈述 → 用户故事 → 需求分类 → 验收标准）、MoSCoW 优先级框架、常见反模式（比如把 solution 当 requirement 写）。
3. **Connector 拉取上下文**：如果配置了 Jira 连接器，AI 可能自动拉取相关 Epic 和 Story 的当前状态；如果配置了 Figma，会拉设计稿；如果配置了 Amplitude，会拉当前版本的使用数据作为决策依据。
4. **输出**：一份结构化的 PRD Markdown 文件，包含问题陈述、用户故事、功能需求（按 P0/P1/P2 分级）、成功指标、开放问题清单。

用户只敲了一个命令。Skills 和 Connectors 在背后协作完成了信息收集、结构补全、上下文注入。用户不需要知道这些层怎么配合——三层分离的好处在这里：复杂度对用户不可见，对插件作者可改。

### 案例 2：数据分析师做一次月度收入趋势分析

**触发**: `/analyze 过去 12 个月的月度收入趋势，按产品线拆分`

**流程**:

1. **Command 启动**：`/analyze` 启动分析流程。
2. **Skill 激活**：`sql-queries` 技能注入——它携带了多数据库方言的实践建议（Snowflake 的 partition pruning、BigQuery 的 slot 优化）、常见查询模式、反模式清单。AI 先写 SQL，再通过 Snowflake 连接器执行。
3. **结果处理**：`data-exploration` 技能介入，做描述统计和异常检测。发现产品线 A 在 3 月有一个不正常的低谷后，自动标注并建议检查是否有数据管道问题。
4. **可视化**：`data-visualization` 技能生成趋势图代码。
5. **验证**：`/validate` 可选，`data-validation` 技能做 sanity check——分母是否包含了不该包含的数据、聚合逻辑是否有偏、解释是否有 survivorship bias。
6. **输出**：分析报告 + 可视化图表 + 置信度评估。

同一个 `/analyze`，连了 Snowflake 就直查库，没连就收 CSV 粘贴。Commands 和 Skills 离开 Connectors 照样跑——知识编码和工具接入是两层独立的能力。这个分离让插件可以先在 Standalone 模式下验证知识逻辑，再接 Connectors 走自动化。

### 案例 3：销售做一次周度预测

**触发**: `/forecast`，上传 CSV 或 CRM 已连接

**流程**:

1. **Command 启动**：`/forecast` 启动预测流程，AI 询问配额和时间窗口。
2. **Skill 激活**：如果 CRM 已连接，`daily-briefing` 技能自动补充近期更新过的 deal 状态；如果没连，用户粘贴 CSV。
3. **分析**：AI 生成加权预测（best case / likely / worst case），标记风险项：过期未更新的 deal、单一联系人（single-threaded）的 deal、Pipeline 覆盖倍数。
4. **输出**：预测报告 + commit vs. upside 拆解 + 缺口分析。

没连 CRM 也能跑，连了就自动化。同一个 Skill 逻辑从头到尾没变过——Connector 只改变数据来源，不改变分析逻辑。

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

> 注：`cowork-plugin-management` 用于创建和定制插件，仓库中仅有 `skills/` 目录，无独立 Commands。`bio-research` 主要面向科研人员，通过 `/start` 查看可用工具，未按传统 Command 表格列出。仓库中还有 `design`、`human-resources`、`operations`、`partner-built`、`pdf-viewer`、`small-business` 等目录，部分由社区贡献，功能完整度不一。表中数据基于 2026-05-30 仓库快照，后续可能变化。

---

## 四、三个代表性插件深度拆解

### 1. Productivity：两层记忆系统的任务管理

最基础的插件，几个设计点值得拆开看。

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

**双轨记忆**：高频变更的东西（人名缩写、项目代号、本周优先级）放 CLAUDE.md，低频但需要持久化的东西（org 结构、长期偏好、历史决策）放 memory/ 目录。这和 CPU 的 L1/L2 cache 一个思路——L1 小而快，L2 大而慢，两者配合才能既响应快又不丢上下文。

**Dashboard 分离**：AI 管结构化数据（Markdown），人通过独立 HTML 看聚合指标。改文件格式不影响 Dashboard，改 Dashboard 不破坏数据。

**自然语言入口**：不需要记命令格式。说"让 Todd 去做 Oracle 项目的 PSR"，`memory-management` 就能把"Todd"解析为"Todd Martinez（财务负责人）"，把"PSR"解析为"Pipeline Status Report"，把"Oracle 项目"解析为"$2.3M，Q2 关单"（示例数据，非真实业务数字）。这种解析能力来自 `memory/` 目录里持久化的实体关系，每次对话都会加载。

### 2. Product Management：7 个命令覆盖 PM 全流程

所有 7 个命令都对应一个同名的 Skill。Command 画工作流边界，Skill 往里填执行知识：

| Command | 对应 Skill | 核心机制 |
|---------|-----------|---------|
| `/write-spec` | `feature-spec` | 对话式澄清 → 用户故事 → MoSCoW 分级 → PRD 输出 |
| `/roadmap-update` | `roadmap-management` | RICE 优先级框架、依赖映射、Now/Next/Later 格式 |
| `/stakeholder-update` | `stakeholder-comms` | 按受众（高管/工程/客户）切换模板和粒度 |
| `/synthesize-research` | `user-research-synthesis` | 主题分析、affinity mapping、persona 构建 |
| `/competitive-brief` | `competitive-analysis` | 功能对比矩阵、定位分析、win/loss 分析 |
| `/metrics-review` | `metrics-tracking` | OKR 层级、指标仪表盘设计、审查节奏 |
| `/brainstorm` | `product-brainstorming` | How Might We、JTBD、First Principles、Opportunity Solution Tree |

**`/brainstorm` 多说两句**。它的设计目标比"你说个想法我帮你展开"更前置。`product-brainstorming` Skill 里编了 4 种对话模式——问题探索、方案生成、假设验证、策略推演——AI 看阶段自动切。用户问"我们要不要加 AI 搜索"，AI 先切到问题探索追问："用户搜不到东西，是算法的问题，还是信息架构的问题，还是内容可发现性的事？"

Skill 文件里有一行："before jumping to solutions, test whether the stated problem is the real problem"。这个行为来自 Skill 文件的硬编码约束，靠 prompt engineering 临时调不出来——Skill 文件每次都会被加载，prompt 工程的指令在长对话里会被稀释。

### 3. Data：多数据库兼容的分析平台

`data` 插件 6 个 Commands、6 个 Skills，和 Product Management 对称。值得看的是它处理数据库无关性的方式：

```yaml
.mcp.json 中可以挂任意 SQL 兼容数据库
Connectors:
  - Snowflake
  - Databricks
  - BigQuery
  - Definite
  - 任意 Generic SQL
```

`sql-queries` Skill 不绑任何数据库。它只管"怎么写好 SQL"——公共模式、性能反模式、方言中立的写法。用户说"我们用 Snowflake"时，AI 才从 Skill 的方言适配部分调 Snowflake 特有的优化（`QUALIFY` 子句、`CLUSTER BY`）。

实际收益就一条：换数据库不动插件，改 `.mcp.json` 的连接目标就行。Skills 层纹丝不动。这让数据团队在迁移数据仓库时不用重写分析逻辑——知识沉淀在 Skill 里，工具切换在 Connector 里。

**`/validate`** 做的事不常见：分析报告发出去之前，跑一轮方法论审查。检查项包括：

- 分母定义是不是漏了某个用户段
- 聚合方式会不会产生 Simpson's paradox
- 趋势解释是不是考虑到了季节性
- 有没有 survivorship bias

`data-validation` Skill 文件里给了逐条的检查清单和反例，AI 对着验证。验证项是"分母定义是不是漏了免费用户"这种硬约束，靠"你觉得数据对不对"这种软问题问不出来。把方法论审查固化成 Skill，相当于给每个分析师配了一个不会偷懒的 reviewer。

---

## 五、五个设计模式

翻完 11 个插件，有 5 个模式反复出现。

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
- 项目记忆 → `CLAUDE.md`
- 插件配置 → `.mcp.json`

收益：Git 可追踪、grep 能搜、编辑器直接改、迁移就是拷文件夹。代价是并发写冲突——但当前设计面向单人使用或小团队，这个代价比引入数据库的复杂度小得多。一旦团队规模上来，需要引入锁机制或迁到数据库，这是当前架构的明确上限。

### 模式 3：Standalone 和 Supercharged 双模式

每个插件都有两套运行模式。以 Engineering 为例：

| 能力 | Standalone（无连接器） | Supercharged（有连接器） |
|------|----------------------|------------------------|
| 日报 | 用户口述今天做了什么 | 自动拉 commits、PR、工单 |
| 代码审查 | 粘贴 diff 或代码片段 | 直接从 GitHub PR 拉取 |
| 调试 | 用户描述症状 | 从 Datadog 拉日志和指标 |
| 事件响应 | 用户描述事件 | PagerDuty 自动拉 on-call 和 Timeline |

Skills 层逻辑在两种模式下不变，只是拿输入的方式不同。先 Standalone 跑起来，确认有用再接 Connectors——采用路径没有前置依赖。这个设计降低了试用门槛，团队可以先验证知识逻辑是否对，再投入 Connector 集成成本。

### 模式 4：记忆的冷热分层

`productivity` 的双轨记忆在 `engineering` 里也有对应——活跃项目上下文放 CLAUDE.md，历史 ADR 和 runbook 放知识库连接器。核心判断一致：AI Agent 的记忆系统需要分层、有成本、能淘汰，平铺成向量数据库反而不好用。向量库擅长语义召回，但召回结果没有结构、没有优先级、没有淘汰策略。文件系统的分层记忆补上了这一块。

### 模式 5：做和审分开

`data` 的 `/validate`、`engineering` 的 `/deploy-checklist`、`legal` 的合同审查——这些都是独立成型的验证 Skill，和执行 Skill 分开。做和审分成两个 Skill，工程纪律在 AI Agent 里照样成立。这个分离的好处是审查逻辑可以独立演进——审查清单更新不需要动执行逻辑，执行逻辑改动也不会偷偷绕过审查。

---

## 六、采用指南

想在自己的团队试，按类型走。

### 个人用户 → 从 productivity 开始

```bash
claude plugin marketplace add anthropics/knowledge-work-plugins
claude plugin install productivity@knowledge-work-plugins
```

用 `/start` 初始化，然后正常对话。两周后打开 TASKS.md 和 CLAUDE.md——这两份文件是你工作方式的镜像，看完经常能发现自己没意识到的模式。如果两周后这两份文件还是空的或者不准，说明你的工作内容可能不适合这种结构化记录方式。

### 产品团队 → productivity + product-management + enterprise-search

1. 每个人装 `productivity` 管自己的任务
2. PM 装 `product-management`，先把 `/write-spec` 和 `/stakeholder-update` 用起来
3. 如果 Slack + Notion 已经配了 MCP，加 `enterprise-search`——跨工具的搜索能省掉大量"这个文档在哪"的来回问询

### 工程团队 → engineering（优先配 GitHub/GitLab MCP）

`engineering` 连了源码仓库之后变化最大：

- `/standup` 自动生成日报——从 commit message 和 PR review 里提取实际产出，避开"I did X"的形式主义模板
- `/review` 对 PR 做结构化审查——安全、性能、代码风格、正确性，四个维度各有一个 Skill 文件，改审查标准就是改 Markdown
- `/incident` 走完整的事故响应流程——triage、沟通、缓解、复盘，每个阶段对应一个模板

如果只能配一个 MCP 连接器，配 GitHub/GitLab。如果配两个，第二个配监控（Datadog / New Relic）。

### 数据分析团队 → data（配数据仓库 MCP）

连上 Snowflake / BigQuery / Databricks 之后，`data` 插件最有用的部分是 `/validate`——报告发出去之前做一轮方法论审查。自动写 SQL 随便哪个 LLM 都会，省掉的是被同事质疑后重新跑数的那一整天。如果团队还没有固定的分析审查流程，先从 `/validate` 的检查清单入手，把方法论纪律建立起来再接 Connector。

### 销售团队 → sales（优先配 CRM）

三个 Command 够覆盖销售最高频的动作：

- `/call-summary`：会议录音或笔记 → 结构化摘要 + 待办 + 跟进邮件草稿
- `/forecast`：CSV 或 CRM 数据 → 加权预测 + 风险标记
- `/pipeline-review`：Pipeline 数据 → 健康评分 + 优先级排序 + 本周行动计划

如果 CRM 暂时连不上，三个命令都能接受手动数据，不阻塞使用。

### 什么情况下不应该用

- 你的团队还没有明确的角色分工和工作流（先梳理流程，再上插件）
- 你的数据合规要求禁止 AI 访问生产数据库（先做安全评估）
- 你的工作内容高度非标、没有任何可模板化的部分（插件帮不上忙）

---

## 七、这件事能活多久

回到开头的判断——这个项目真正有价值的是它定下的三条规则，11 个插件只是规则的实例化：

1. **领域知识写成文件，不写成代码**。Markdown 比 Python 适合描述"好的 PRD 长什么样"或"怎么审一份合同"。文件可以被非工程师编辑、进 Git、做 diff review。
2. **用户意图（Commands）、AI 知识（Skills）、外部工具（Connectors）由三个角色独立控制**。三层耦合在一起时，任何改动都需要跨角色协商，迭代速度会塌掉。
3. **能力边界随 Connectors 增减渐进扩展，核心逻辑保持不动**。Standalone 模式是成本最低的信任建立方式。

这三条绑在一起指向一件事：AI Agent 插件体系的工程化。把知识写成结构，把流程写成可复现，把质量写成可验证——写个 prompt 跑一遍看运气，这条路走不远。

如果还在观望 AI Agent 落地，这条路径的验证成本极低——不需要先投一个月的集成工程。装一个 productivity 插件，用一周，打开 TASKS.md 和 CLAUDE.md 看看里面长了什么。如果那两份文件比你自己的任务清单更准更全，就继续。如果没有，卸载。成本就一个文件夹。

---

*本文基于 GitHub [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) 公开信息撰写，数据截取至 2026-05-30。插件结构和功能细节来自仓库 README、plugin.json 和示例工作流。文中示例数据（如人名、项目代号、金额）为说明性内容，非真实业务数字。*

---

## 八、常见问题和故障排查

### 问题1：装了插件，但 Commands 不出现

**原因**：只装了命名 agent，没有装对应的 vertical plugin。

**解决**：命名 agent 打包了自己的 skills 副本，但 slash commands 定义在 `vertical-plugins/<vertical>/commands/` 下。如果想用 `/comps`、`/dcf` 这类命令，需要装对应的 vertical plugin。

### 问题2：改了 skill 文件，但 agent 行为没变化

**原因**：命名 agent 读的是 `agent-plugins/<slug>/skills/` 下的副本，不是 `vertical-plugins/<vertical>/skills/` 源文件。

**解决**：改完源文件后，运行 `python3 scripts/sync-agent-skills.py` 把更新推到所有打包了该 skill 的 agent。

### 问题3：Connector 配置了，但 AI 没有调用

**原因**：Skills 层逻辑不变，但 Connector 需要在 `.mcp.json` 中正确配置，且 AI 需要根据上下文自动判断何时调用。

**解决**：检查 `.mcp.json` 配置是否正确，确认 MCP 服务器已启动，查看 AI 的推理过程了解为何没有调用。

### 问题4：Markdown 文件存储状态，会不会有并发写冲突

**原因**：当前设计面向单人使用或小团队，确实存在并发写冲突的风险。

**解决**：对于团队使用，建议引入锁机制或迁移到数据库。但当前架构的明确上限是：一旦团队规模上来，需要引入锁机制或迁到数据库。

---

## 自测题

1. **Commands、Skills、MCP Connectors 三层的控制者分别是谁？**  
   → 用户（显式触发）、AI（上下文自动激活）、运维/开发者（配置文件绑定）

2. **为什么三层要分开控制，而不是写成一个整体？**  
   → 三层耦合在一起时，任何改动都需要跨角色协商，迭代速度会塌掉。分开后，团队可以独立改 Commands（交互流程），不碰 Skills；可以独立换 Connectors（换数据库、换 CRM），不碰 Commands 和 Skills。

3. **产品团队的 PM 用 `/write-spec` 写一个功能 PRD，整个流程经历了什么？**  
   → Command 启动 → Skill 注入（feature-spec）→ Connector 拉取上下文（Jira/Notion/Figma）→ 输出结构化 PRD

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
- 改 `.mcp.json`，把连接器换成你们真的在用的系统
- 改 `skills/`，把团队术语、审批边界和输出格式写进去
- 添加自定义 `commands/`，把最高频、最稳定的动作做成固定入口

### 阶段四：生态扩展（3 个月+）
-  fork 仓库，创建自定义插件
- 使用 `cowork-plugin-management` 插件管理插件创建和定制
- 把团队的工作流固化成可复用的插件，分享给更多团队

