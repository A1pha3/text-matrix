---
title: "Anthropic官方知识工作者插件库：knowledge-work-plugins"
date: 2026-05-24T23:07:00+08:00
description: "Anthropic 开源的 knowledge-work-plugins 是一套面向岗位工作的 Claude 插件市场：11 个官方插件、可自定义的 MCP 连接和可直接复用的技能结构。"
draft: false
categories:
  - 技术笔记
tags:
  - GitHub-Trending
  - Anthropic
  - Claude
  - 插件
  - 工作流
slug: anthropics-knowledge-work-plugins-guide
author: 钳岳星君
---
`knowledge-work-plugins` 值得关注，因为 Anthropic 把“岗位知识 + 外部工具 + 固定工作流”打包成了可以安装、可以定制、可以复用的插件市场。它首先服务 [Claude Cowork](https://claude.com/product/cowork)，同时也兼容 [Claude Code](https://claude.com/product/claude-code)。

当成聊天机器人用，这个仓库像一组模板；当成工作界面用，它更接近一套岗位操作系统的起点。

读完这篇文章，可以回答

- `knowledge-work-plugins` 到底是插件市场，还是一堆 prompt 模板。
- 它和 MCP、Claude Cowork、Claude Code 分别是什么关系。
- 11 个官方插件按什么思路划分，适合先从哪一个试起。
- 如果你想把它接进自己的团队流程，第一步应该先改哪里。

一句话判断

Anthropic 开源的 `knowledge-work-plugins`，说到底是一组面向具体岗位的 Claude 插件样板。它把技能说明、命令入口和 MCP 连接方式整理成文件化结构，让你不必每次都从空白对话开始教 Claude 怎么做销售调研、数据分析、法务初审或企业搜索。

先看结论：它解决的是“工作流太散”，不是“功能少”

很多人第一次看到插件，会下意识把它理解成浏览器扩展或聊天助手里的工具菜单。`knowledge-work-plugins` 不是这个方向。

Anthropic 在仓库 README 里给出的定位很明确：插件的作用，是告诉 Claude 你的工作应该怎么做、该接哪些工具、哪些流程需要固定下来，以及应该暴露哪些斜杠命令。它解决的核心问题是"每次都要重新提示一遍"。

这也是它和普通 prompt 模板最大的区别：

- prompt 只描述一次任务；
- 插件把一类工作长期固化下来；
- MCP 连接把 Claude 接到你的外部系统；
- 最终效果是让 Claude 更像“这个岗位的默认助手”，而不是一位每次都要重新 onboarding 的通用模型。

仓库里现在有什么

截至本文写作时，仓库 README 展示的是 11 个官方开源插件：

| 插件 | 主要用途 | 典型连接器 |
| ------ | ---------- | ------------ |
| `productivity` | 管理任务、日历、日常工作流和个人上下文 | Slack、Notion、Asana、Linear、Jira、Microsoft 365 |
| `sales` | 做销售调研、通话准备、外联草稿和竞品 battlecard | HubSpot、Close、Clay、ZoomInfo、Notion |
| `customer-support` | 处理工单、起草回复、整理升级单和知识库文章 | Intercom、HubSpot、Guru、Jira |
| `product-management` | 写需求、规划路线图、整理用户研究和竞品信息 | Linear、Asana、Jira、Figma、Amplitude |
| `marketing` | 写内容、做 campaign 规划、管品牌口径、汇报渠道效果 | Canva、Figma、HubSpot、Ahrefs |
| `legal` | 做合同审阅、NDA 分流、风险判断和模板化回复 | Box、Egnyte、Jira、Microsoft 365 |
| `finance` | 做账务处理、对账、报表和 close 流程支持 | Snowflake、Databricks、BigQuery |
| `data` | 写 SQL、做统计分析、搭图表和校验分析结论 | Snowflake、Databricks、Hex、Amplitude |
| `enterprise-search` | 跨邮件、聊天、文档和 wiki 搜索企业知识 | Slack、Notion、Guru、Jira |
| `bio-research` | 连接科研数据库和生命科学工具链 | PubMed、bioRxiv、ClinicalTrials.gov |
| `cowork-plugin-management` | 创建或改造你自己的 Cowork 插件 | 无固定连接器 |

这个列表有两个信号。

首先是定位：它是"岗位型插件市场"，不是"工具型插件市场"。Anthropic 直接围绕生产力、销售、客服、产品、法务、财务、数据等真实岗位组织能力，没有先做十几个零碎的能力开关。

其次是默认工作方式：**Claude 不是孤立做推理，而是通过 MCP 连接到团队原本就在用的系统。**

这些插件到底由什么组成

仓库 README 给出的结构非常克制，核心只有几类文件：

```text
plugin-name/
├── .claude-plugin/plugin.json
├── .mcp.json
├── commands/
└── skills/
```

这几个目录背后的含义，比文件名本身更重要。

`skills/`：把岗位经验写进 Claude

这里放的是长期有效的领域知识、工作步骤和判断标准。它把某个岗位反复会遇到的任务拆成可以复用的操作说明，不是一段“帮我写得更专业”的提示词。

比如销售插件，不限于让 Claude 会写外联邮件，还会把 call prep、客户背景整理、竞争对手对比这些动作固定成比较稳定的产出方式。

如果你想继续看 Anthropic 自己是怎么组织 `skills` 的，可以接着读 [Anthropic Skills 仓库进阶实战：18 个技能覆盖研发全链路]({{< relref "anthropics-skills-18-skills-full-stack-guide.md" >}})。那篇更偏技能设计，这篇则更偏插件市场和岗位封装。

`commands/`：给高频动作一个固定入口

README 里举的例子包括 `/sales:call-prep`、`/data:write-query`。这类命令的价值是把“什么输入会触发什么工作流”标准化，不是省几个字。团队里不同的人点同一个命令，得到的输出结构会更接近。

`.mcp.json`：把 Claude 接到外部系统

这是整套机制里最关键的一层。没有 MCP 连接，Claude 只能处理你当前会话里的信息；有了 MCP，它才能真正去读 CRM、工单系统、聊天记录、数据仓库或知识库。

插件的威力来自“模型 + 外部系统 + 固定流程”同时到位，不只是提示词写得好。

如果你对“接上如果你还想弄清楚接上 MCP 之后工作流具体会发生什么变化，可以顺手看 [n8n-MCP：让 AI 编程助手帮你构建 n8n 工作流自动化]({{< relref "n8n-mcp-claude-workflow-automation-guide.md" >}})。它更具体地展示了连接协议落地后的自动化形态。

怎么安装

Anthropic 在 README 里区分了两条路径。

在 Claude Cowork 里使用

最直接的方法是去 [claude.com/plugins](https://claude.com/plugins/) 安装。Cowork 是这批插件的主场景，适合希望在桌面端直接浏览和启用插件的人。

在 Claude Code 里使用

如果你更习惯命令行或代码工作台，README 给出的安装方法是：

```bash
先添加 marketplace
claude plugin marketplace add anthropics/knowledge-work-plugins

再安装一个具体插件
claude plugin install sales@knowledge-work-plugins
```

这里容易误解的地方：**这个仓库不是“一个安装命令把所有插件全装上”。** 准确的理解是，你先把这个仓库加入插件市场，再按需安装某个具体插件。

如果你要落地，第一刀通常改哪里

很多团队第一次 fork 这类仓库，会直觉去新增一堆命令。更有效的顺序通常相反：

1. 先改 `.mcp.json`，把连接器换成你们真的在用的系统。
2. 再改 `skills/`，把团队术语、审批边界和输出格式写进去。
3. 最后才补 `commands/`，把最高频、最稳定的动作做成固定入口。

没有真实数据源时，命令再漂亮也只是空壳；没有团队语境时，技能再完整也还是“通用岗位版本”。

举个最小例子。假设你在一个用 HubSpot、Notion 和 Slack 的销售团队里落地 `sales` 插件，你真正要固化的是这些更具体的东西，不是“Claude 会写邮件”：

- 线索分级标准是什么。
- call prep 必须包含哪些字段。
- 会后总结发给谁，格式长什么样。
- 哪些信息可以自动写，哪些判断必须人工确认。

插件化真正带来的收益，恰恰来自这些原本散落在口头经验里的细节被写成可重复执行的规则。

一个具体例子：为什么 `enterprise-search` 很像下一代企业搜索

如果只看名字，`enterprise-search` 似乎只是“帮你搜一下公司资料”。但仓库里的说明其实更接近一个统一检索层：

- 你提出一个自然语言问题；
- Claude 把问题拆成更适合不同数据源的查询；
- 然后同时去聊天、邮件、文档和 wiki 里找证据；
- 最后再把不同来源的结果综合成一个可引用的回答。

这和传统企业搜索的区别，不限于在检索结果页里多了一个模型总结，而是在“查询改写、跨源搜索、结果综合”这三步已经被合并进同一条工作流里。

对于团队内部的知识查找，这比“开 4 个标签页分别搜”更接近真正可用的助手体验。

它最适合谁

`knowledge-work-plugins` 不是人人都要装，但下面三类人会特别受益：

. 已经在用 Claude，但提示词越来越长的人

如果你已经写了一堆固定提示词，比如销售拜访准备模板、每周周报模板、法务初审模板，那么插件是更稳定的承载方式。你不需要每次复制一整段系统说明，只要把它收束进一个可安装的插件。

. 想把团队流程标准化的人

插件的重点不限于“我自己用得爽”，而是让一整个团队在同类任务上形成更接近的工作方法。对管理者或流程 owner 来说，这比散落在各人笔记里的 prompt 更容易维护。

. 已经开始接 MCP 的团队

如果你已经把 Claude 接进 Slack、Notion、Jira、HubSpot、Snowflake 之类的系统，那么插件能把这些连接真正组织起来。没有插件时，连接只是“可以访问”；有了插件，连接才变成“知道该怎么用”。

它的边界也很明确

这套仓库很强，但不该被神化。

它不是开箱即用的“行业真相”

官方插件给的是通用岗位起点，不是你公司的真实 SOP。你仍然需要补自己的术语、团队分工、审批规则和工具栈，插件才会真正贴合业务。

它也不是“有插件就能自动完成所有工作”

插件能把工作流收束得更稳，但不能替你承担业务判断。销售线索是否值得跟进、法务风险是否可接受、财务分析结论是否站得住，仍然需要人来拍板。

没有 MCP 连接时，很多价值发挥不出来

如果你不接 CRM、不接聊天记录、不接文档系统，只保留本地对话，那么插件能提供的更多还是结构化提示，而不是深度业务协作。

第一次上手，建议这样走

如果你准备试这套仓库，我更建议按下面的顺序，而不是一上来就自己造插件：

1. 先挑一个最贴近自己岗位的官方插件。
2. 只接 1 到 2 个最常用的数据源，不要第一天就把全家桶都连上。
3. 连续跑几个真实任务，观察输出是不是已经稳定优于你原来的 prompt。
4. 再去修改 `skills/` 或 `.mcp.json`，把公司术语和流程慢慢固化进去。
5. 只有当现成插件不够用时，再考虑用 `cowork-plugin-management` 自建插件。

这样做的好处是，你先验证“插件化工作流”是不是适合你，再决定要不要投入更多维护成本。

如果你更关心“把能力做成稳定流程”这件事本身，而不局限于插件形态，也可以继续读 [Claude Code Harness：给 AI 编程助手加一套有约束的交付流程]({{< relref "claude-code-harness-disciplined-delivery-loop.md" >}})。它展示的是另一种把经验收束成可复查工作流的方法。

常见问题

它和 MCP 是什么关系

可以把 MCP 理解成连接协议，把插件理解成工作流封装。MCP 负责把 Claude 接到外部工具；插件负责告诉 Claude 在这些工具之上该怎么工作。

它和普通 prompt 模板有什么区别

模板通常只解决一次任务的输入组织；插件则把角色知识、命令入口和外部系统连接一起打包，适合长期反复执行的工作。

适合个人用，还是更适合团队

两者都能用，但团队收益通常更大。个人用户能节省重复提示的时间；团队则能把分散的经验沉淀成统一入口。

自测问题

- 如果你不接任何外部系统，这套插件还能带来什么，带不来什么。
- 对你所在团队来说，最值得先固化的是连接器、技能规则，还是斜杠命令。
- 你现在最常复制粘贴的一段 prompt，是否已经适合升级成一个插件能力。

最后判断

`knowledge-work-plugins` 的价值，不在于“Anthropic 又发布了多少个插件”，而在于它把一个趋势写得很具体：**未来的 Claude 工作界面，会越来越像一层岗位操作层，而不是一个通用聊天框。**

如果你只是偶尔问几个问题，这个仓库不会立刻改变什么；如果你已经把 Claude 放进真实工作流里，尤其已经开始接 MCP，那么它非常值得细读。你真正该关注的，也不限于那 11 个官方插件本身，而是它们展示出来的组织方式：如何把岗位经验、命令入口和外部系统连接成一条能长期复用的工作流。

相关链接

- GitHub 仓库：[anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)
- 插件入口：[claude.com/plugins](https://claude.com/plugins/)
- Claude Cowork：[claude.com/product/cowork](https://claude.com/product/cowork)
- Claude Code：[claude.com/product/claude-code](https://claude.com/product/claude-code)
