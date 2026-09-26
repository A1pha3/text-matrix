---
title: "Anthropic Knowledge Work Plugins：把 Claude 变成岗位专家的完整指南"
date: "2026-03-24T17:30:00+08:00"
lastmod: "2026-09-22T00:00:00+08:00"
slug: "anthropic-knowledge-work-plugins-guide"
github_repo: "anthropics/knowledge-work-plugins"
source_key: "gh:anthropics/knowledge-work-plugins"
aliases:
  - /posts/tech/anthropic-knowledge-work-plugins-guide/
description: "解读 Anthropic 官方开源的 11 款 Knowledge Work Plugins：为 Claude Cowork 与 Claude Code 提供岗位级 skills、连接器与命令，覆盖销售、客服、产品、法务、财务等 11 类职能。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "Cowork", "MCP", "工作流", "AI 工具"]
---

# Anthropic Knowledge Work Plugins：把 Claude 变成岗位专家的完整指南

> 预计阅读时间：25 分钟 | 难度：⭐⭐⭐

Anthropic 在 2026 年 1 月开源了 [knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) 仓库：一套面向知识工作者的官方插件集合。它为 Claude 补上特定岗位的领域知识、工作流程和工具连接，覆盖销售、客服、产品、市场、法务、财务、数据分析等 11 类职能。截至 2026 年 9 月，这个仓库已经积累 25,000+ stars。它把"怎么让一个通用模型在具体岗位上顶用"这件事，从散落的个人提示词，变成一套可安装、可读、可改的文件。

## 学习目标

读完这篇文章，你可以做到三件事：

1. 看懂 `knowledge-work-plugins` 的结构和运行方式，以及它最近的形态变化。
2. 快速判断 11 个插件分别适合什么场景，该配哪些工具连接。
3. 按步骤装上插件，并在真实工作里用起来。

## 先建立一个正确认知

这个仓库的重点是"给不同岗位一套标准化能力包"，不是"把 Claude 变得无所不能"。官方的定位是 Built for Claude Cowork, also compatible with Claude Code——主要为 Cowork（Anthropic 的桌面智能体应用）设计，也能在 Claude Code 里用。

每个插件围绕一个岗位职能打包三类东西：

- **skills**：岗位知识、方法论、执行步骤，Claude 判断相关时自动调用
- **commands**：显式触发的斜杠命令
- **connectors**：通过 MCP 服务器连接企业工具栈

所有组件都是文件——markdown 和 JSON，没有代码、没有基础设施、没有构建步骤（官方原话 "no code, no infrastructure, no build steps"）。README 也提过子代理（sub-agents）协作，但当前 11 个官方插件里没有独立的 agents 目录，实际能力以 skills、commands、connectors 三类为主。这意味着你可以直接读、直接改每个插件的行为，这也是它适合作为企业定制起点的原因。

你可以把它理解成：给 Claude 安装"岗位操作系统"。

## 安装与启动（新手必看）

### 在 Claude Cowork 安装（推荐入口）

Cowork 用户直接从 [claude.com/plugins](https://claude.com/plugins/) 一键安装，这是官方的第一推荐渠道。

### 在 Claude Code 安装

```bash
# 先添加插件市场
claude plugin marketplace add anthropics/knowledge-work-plugins

# 再安装具体插件
claude plugin install sales@knowledge-work-plugins
```

把 `sales` 换成 `productivity`、`data` 等任意插件名即可。

### 安装后如何生效

- 自动触发：提问命中某个场景时，相关 skills 自动参与。
- 按名调用：skills 也能直接当命令用，例如 `/sales:call-summary`、`/data:write-query`。
- 逐步扩展：新手建议先装 1-2 个插件，用顺后再加。

## 插件结构（懂这个就不容易用错）

官方结构模板：

```text
plugin-name/
├── .claude-plugin/plugin.json   # 清单文件
├── .mcp.json                    # 工具连接
├── commands/                    # 显式触发的斜杠命令
└── skills/                      # Claude 自动调用的领域知识
```

这个结构在 2026 年 3 月之后有一个重要变化：仓库做了一次 **commands 到 skills 的迁移**，命令和技能的边界被淡化。以 sales 为例，早期它有 3 个 commands 加 6 个 skills，如今 commands 目录已经消失，36 个 skills 既自动触发、也可以按名调用（`/sales:call-prep`）。你现在去看仓库，多数插件只有 `skills/` 加 `.mcp.json`。读旧教程时留意这个差异。

另外，`.mcp.json` 不是每个插件都有——`cowork-plugin-management` 就没有，它不需要连接外部工具。

## 11 个插件完整指南

11 个插件在能力成熟度和连接器组合上差别不小，下面按职能逐个过一遍，每个都落在同一个问题上：它解决谁的什么麻烦。

### 1. productivity：任务、记忆与仪表盘

这一款贴近日常工作：任务、日历、工作流和个人上下文都归它管，目标是你少重复自己。

核心是三件东西：

- **任务管理**：一份 markdown 任务清单 `TASKS.md`，Claude 读写并跟踪状态、清理过期项、与外部工具同步。
- **工作记忆**：两级记忆系统——`CLAUDE.md` 存工作记忆，`memory/` 目录做深度存储。记忆建好后，你说"ask todd to do the PSR for oracle"，Claude 能直接解码出"让财务负责人 Todd Martinez 准备 Oracle Systems 项目的 Pipeline Status Report（230 万美元，Q2 关单）"。
- **可视化面板**：本地 `dashboard.html`，看任务看板和 Claude 对你工作的理解，双端同步。

命令入口：`/start` 初始化任务和记忆并打开面板；`/update` 每日同步；`/update --comprehensive` 深扫邮件、日历、聊天记录，找出遗漏的待办。

连接器：Slack、Notion、Asana、Linear、Jira、Monday、ClickUp、Microsoft 365。

任务多、优先级乱，整天在多个工具之间来回找进度的岗位都适用，也想有固定节奏的日/周复盘。多数人可以拿它当第一个插件。

### 2. sales：覆盖整个销售日

调研客户、准备通话、复盘管道、起草外联、制作竞品对比卡（battlecard）——销售一天里要干的杂活，它都排了技能。

它是迭代最快的一款，已经发布 2.0：技能从 9 个扩到 **36 个**，新增交易复盘（deal-review）、收单计划（close-plan）、干系人地图（stakeholder-map）、续约雷达（renewal-radar）、客户健康度（customer-health）、线索分流（lead-triage）。典型的一天这样流转：

- `daily-briefing`：早报——今天的会议与客户背景、临近关单的交易、待回邮件、头等动作
- `call-prep`：通话前简报——参会人、客户历史、公开商机状态、探索性问题
- `call-summary`：把通话录音转写或笔记变成跟进邮件草稿、团队纪要和 CRM 更新建议
- `forecast`：给出 commit、best-case 和管道叙事

2.0 还有两个务实的设计：技能读取 CRM 自己的阶段和字段，不绑某一家厂商；没连任何工具时，上传一份管道导出、一份通话记录也能干活。外部内容（邮件、转写、聊天）只被当作信息、不当成指令——内容里要求执行的动作会先展示给你确认。

连接器：Slack、HubSpot、Close、Clay、ZoomInfo、Notion、Jira、Fireflies、Microsoft 365。

适合新销售不会做 call prep、外联话术质量不稳、管道会议准备成本高的团队。

### 3. customer-support：从响应到沉淀的闭环

工单分流、起草回复、打包升级、调研客户上下文、把已解决问题变成知识库文章，这条客服闭环被拆成五个 skills：`ticket-triage` 分流工单，`draft-response` 起草回复（按官方 skill 定义，会根据情境、紧急程度和渠道调整语气与结构），`customer-escalation` 打包升级信息，`customer-research` 补客户背景，`kb-article` 把处理完的问题沉淀成知识库候选。

连接器：Slack、Intercom、HubSpot、Guru、Jira、Notion、Microsoft 365。

适合客服峰值时段压力大、回复风格不统一、已解决问题没有形成组织记忆的情况。

### 4. product-management：把需求串成证据链

写规格、规划路线图、综合用户研究、同步干系人、追踪竞争格局，PM 的核心产出物各有各的技能，一共 8 个：`write-spec` 写需求规格，`roadmap-update` 更新路线图，`synthesize-research` 综合用户研究，`stakeholder-update` 做干系人同步，`metrics-review` 看指标，`competitive-brief` 出竞争简报，`sprint-planning` 排迭代，`product-brainstorming` 做头脑风暴（也提供 `/brainstorm` 命令入口）。

连接器覆盖也很广：Slack、Linear、Asana、Monday、ClickUp、Jira、Notion、Figma、Amplitude、Pendo、Intercom、Fireflies。

适合信息源分散、写文档成本高、需求评审缺统一上下文、利益相关方更新频繁的 PM。

### 5. marketing：内容生产加运营分析

起草内容、策划活动、执行品牌语调、做竞品简报、出跨渠道效果报告，8 个 skills 里最有特色的是 `brand-review`——把"品牌调性"从口头要求落成可执行的审查步骤；其余覆盖 `draft-content` 内容起草、`campaign-plan` 活动策划、`email-sequence` 邮件序列、`seo-audit` SEO 审查、`performance-report` 效果汇报、`competitive-brief` 竞品简报。

连接器：Slack、Canva、Figma、HubSpot、Amplitude、Notion、Ahrefs、SimilarWeb、Klaviyo。

适合多角色协作口径不一、活动复盘靠手工拼数据、需要更快响应市场热点的团队。

### 6. legal：高频标准场景提速

审合同、分流 NDA、处理合规、评估风险、准备会议、起草模板化回复，法务的日常动作都列成了 skills：`review-contract` 合同审查、`triage-nda` NDA 分流、`legal-risk-assessment` 风险评估、`compliance-check` 合规检查、`meeting-briefing` 会前简报、`legal-response` 标准回复、`vendor-check` 供应商审查、`signature-request` 签署请求处理。

连接器：Slack、Box、Egnyte、Jira、Microsoft 365。

适合合同量大、人工初筛吃力、业务团队反复问同类合规问题的场景。它给高频标准流程提速，不能替代律师判断。

### 7. finance：流程化财务动作

准备分录、对账、生成财报、分析差异、管理月结、支持审计，8 个 skills 里容易被忽略的是 `sox-testing`——SOX（萨班斯法案）合规测试支持。其余覆盖 `journal-entry` 与 `journal-entry-prep` 分录准备、`reconciliation` 对账、`financial-statements` 财报草稿、`variance-analysis` 差异分析、`close-management` 月结管理、`audit-support` 审计支持。

连接器：Snowflake、Databricks、BigQuery、Slack、Microsoft 365——它直接面向数据仓库取数。

适合月末结账节奏紧、重复动作多、报表解释要跨系统取数、审计季资料组织压力大的岗位。

### 8. data：从提问到验证的分析链路

查询、可视化、解读数据——写 SQL、跑统计分析、搭仪表盘、分享前先验证，10 个 skills 覆盖这么一条链路：`write-query` 与 `sql-queries` 写查询，`explore-data` 与 `analyze` 探索分析，`statistical-analysis` 统计检验，`build-dashboard`、`create-viz`、`data-visualization` 做可视化，`validate-data` 验证结果，`data-context-extractor` 提取数据上下文。官方把"分享前先验证"（validate your work before sharing）写进设计目标，堵住的是"只给结论不做校验"这类常见风险。

连接器：Snowflake、Databricks、BigQuery、Definite、Hex、Amplitude、Jira。

适合非数据同学做自助分析、数据团队要提升交付一致性、要给管理层做可解释汇报的场景。

### 9. enterprise-search：先找得到，再谈其他

跨邮件、聊天、文档和 wiki 找东西——一次查询覆盖全公司的工具。5 个 skills：`search` 执行检索，`search-strategy` 规划检索策略，`digest` 做摘要，`knowledge-synthesis` 综合知识，`source-management` 管理信息源。它管"找得到"，不管"写得漂亮"，所以适合放在其他插件前面：先用它把公司上下文拉齐，再交给岗位插件产出。

连接器：Slack、Notion、Guru、Jira、Asana、Microsoft 365。

适合信息分散在多个系统、新员工要快速建立上下文、会议前要快速拉齐历史信息的情况。

### 10. bio-research：专攻生命科学研发

连接临床前研究工具与数据库（文献检索、基因组学分析、靶点优先级排序），加速早期生命科学研发。

别被"文献检索"带偏，它是 11 个插件里技术含量最高的一个：skills 直接对着计算生物学的真实工作流——`single-cell-rna-qc` 做单细胞 RNA 测序质控，`scvi-tools` 对接单细胞分析框架 scvi-tools，`nextflow-development` 开发 Nextflow 生信流水线，`instrument-data-to-allotrope` 把仪器数据转成 Allotrope 标准格式，`scientific-problem-selection` 做科学问题筛选。

连接器也全是领域专属：PubMed、BioRender、bioRxiv、ClinicalTrials.gov、ChEMBL、Synapse、Wiley、Owkin、Open Targets、Benchling。

适合生物医药早期研发团队，尤其是要对着文献、组学数据、靶点证据一起讨论的场景。

### 11. cowork-plugin-management：把经验变成资产

为组织的特定工具与流程创建新插件，或改造现有插件。skills 只有 2 个：`create-cowork-plugin` 从零新建插件，`cowork-plugin-customizer` 改造现有插件。它不需要 `.mcp.json`——本身不连接外部工具，是 11 个里的例外。定制流程多、通用插件不够用的团队，靠它把一次经验沉淀成长期资产。

## 插件 × 连接器总表

连接器决定插件能不能读到你的真实数据，选型时和功能同样重要。下表整理自仓库 README：

| 插件 | 连接器 |
| --- | --- |
| productivity | Slack、Notion、Asana、Linear、Jira、Monday、ClickUp、Microsoft 365 |
| sales | Slack、HubSpot、Close、Clay、ZoomInfo、Notion、Jira、Fireflies、Microsoft 365 |
| customer-support | Slack、Intercom、HubSpot、Guru、Jira、Notion、Microsoft 365 |
| product-management | Slack、Linear、Asana、Monday、ClickUp、Jira、Notion、Figma、Amplitude、Pendo、Intercom、Fireflies |
| marketing | Slack、Canva、Figma、HubSpot、Amplitude、Notion、Ahrefs、SimilarWeb、Klaviyo |
| legal | Slack、Box、Egnyte、Jira、Microsoft 365 |
| finance | Snowflake、Databricks、BigQuery、Slack、Microsoft 365 |
| data | Snowflake、Databricks、BigQuery、Definite、Hex、Amplitude、Jira |
| enterprise-search | Slack、Notion、Guru、Jira、Asana、Microsoft 365 |
| bio-research | PubMed、BioRender、bioRxiv、ClinicalTrials.gov、ChEMBL、Synapse、Wiley、Owkin、Open Targets、Benchling |
| cowork-plugin-management | 无 |

规律很明显：Slack 和 Microsoft 365 几乎是标配，各岗位插件再按职能补齐 CRM、数据仓库或设计工具。

## 仓库不止 11 个：发布后的演进

以 2026 年 9 月的仓库为口径，除了 README 正式列出的 11 个插件，发布后还有几批值得关注的新增：

- **pdf-viewer**：交互式 PDF 查看器插件，支持批注、填表、签名、盖章，提供 `/pdf-viewer:open`、`/pdf-viewer:annotate` 等 4 个命令。
- **design / engineering / human-resources / operations**：2026 年 4 月到 6 月陆续加入的四个岗位插件，分别覆盖设计评审与交接、代码评审与事件响应、招聘与绩效、供应商与流程管理。
- **small-business**：2026 年 5 月起加入的小微企业一站式插件，一口气带 44 个 skills（记账、催款、招聘、税务准备、库存规划），外加一个听懂大白话的路由——你说"我这个月工资发不出来"，它自己挑对的技能。每个技能执行前都会暂停确认：不经过你同意，不发送、不发布、不付款。
- **partner-built/**：合作方插件目录，已有 Apollo、BrandVoice、Common Room、Slack、Zoom 五个。

这个仓库 2026 年 1 月 23 日建仓，3 月完成 commands 到 skills 的架构迁移，此后几个月里持续新增插件与大版本迭代。读任何基于早期版本的教程，都建议先对照仓库现状。

## 新手怎么选：一张决策表

| 你的问题 | 优先插件 |
| --- | --- |
| 我今天事情太多，不知道先做什么 | productivity |
| 我需要准备客户沟通、写外联话术 | sales |
| 工单太多，回复和升级质量不稳定 | customer-support |
| 我要写需求规格、做路线图沟通 | product-management |
| 我要做内容/活动/品牌一致性输出 | marketing |
| 我要做合同初审或 NDA 处理 | legal |
| 我要对账、做月结与财务解释 | finance |
| 我要写 SQL、做分析并验证结论 | data |
| 我先要把公司资料快速找全 | enterprise-search |
| 我做生物医药早期研究相关工作 | bio-research |
| 我要自己搭或改公司内部插件 | cowork-plugin-management |

## 新手上手路径

1. 先选一个你每周都会重复做的场景。
2. 只装 1 个主插件，连续用 1 周。
3. 把高频任务固化成命令或技能调用习惯。
4. 再补一个"配套插件"形成组合。

常见组合：

- 销售团队：`enterprise-search + sales`
- 产品团队：`enterprise-search + product-management + data`
- 客服团队：`customer-support + enterprise-search`
- 管理岗位：`productivity + enterprise-search`

## 如何把它们用出"团队级价值"

官方在 README 里给了四条定制路径：

- **换连接器**：编辑 `.mcp.json`，指向你们实际在用的工具栈。
- **补公司上下文**：把内部术语、组织结构、流程写进 skill 文件，让 Claude 理解你的世界。
- **改工作流**：修改 skill 指令来匹配团队的真实做法，而不是教科书做法。
- **建新插件**：用 `cowork-plugin-management` 或照着目录结构，为还没覆盖的岗位做插件。

团队范围使用后，这些上下文会进入每一次相关交互——管理者可以把盯流程的时间省下来，花在改进流程上。

## 常见问题

**插件装了，`/sales:call-prep` 却不生效？**
先确认安装时用了正确的插件名拼写，再确认你是在 Claude Code 还是 Cowork 里调用。Claude Code 里技能可以按名调用，但如果该插件用的是自动触发（skill）而不是命令，`/` 前缀的调用可能不匹配——用场景化提问比硬敲命令名更稳。

**不想接公司的 CRM 或数据仓库，还能用吗？**
可以。多数插件在没连任何工具时也能跑基础流程，只是少了真实数据：sales 可以上传管道导出和通话记录，data 可以喂一份 CSV。连接器的作用是把"上传文件"换成"直接读取线上数据"。

**官方连接器不匹配我们用的工具，怎么换？**
直接编辑插件根目录的 `.mcp.json`，把服务器改成你实际在用的工具栈。连接器是 MCP 服务器配置，不是写死的代码。

**同一个用户能同时装几个插件吗？**
能，也建议按需组合（参考上文"新手上手路径"的组合）。装太多会稀释每种能力的触发概率，一般从一个主插件起步。

**想改插件的行为，从哪下手？**
插件的全部逻辑都在 `skills/` 目录的 markdown 文件里。改工作流、补公司术语、调整步骤，都直接改对应 skill 文件即可；改完重载即可生效，没有编译或部署步骤。

## 总结

`knowledge-work-plugins` 把"岗位经验"变成"可安装、可复用、可迭代"的协作系统：所有能力都是 markdown 和 JSON 文件，装上即用，改文件即定制。

对新手，把三句话串起来就够用：**先按场景选插件，再按流程用插件，最后按团队实践改插件。**

## 参考来源与口径说明

- 仓库地址：[anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)；安装命令、插件结构、11 插件清单与连接器表均以仓库 README 为准。
- 本文数据（25,291 stars、3,007 forks）与 skills 数量（sales 36 个、small-business 44 个等）核对于 2026-09-21 的 main 分支；仓库仍在活跃迭代，以最新状态为准。
- productivity 的任务/记忆/仪表盘机制、sales 2.0 的变更清单引自各插件 README；customer-support 的回复语气口径引自其 `draft-response` skill 定义。
- 文章初稿发布于 2026-03-24，当时仓库为 11 个官方插件加 commands/skills 双结构；2026-09 更新时补入了 commands 迁移与后续插件演进。正文把每个插件归纳为 skills、commands、connectors 三类；README 中也出现过 sub-agents 的说法，但 11 个官方插件里没有独立的 agents 目录。
