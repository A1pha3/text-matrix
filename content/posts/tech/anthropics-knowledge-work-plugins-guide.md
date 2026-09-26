---
title: "Anthropic官方知识工作者插件库：knowledge-work-plugins"
date: 2026-05-24T23:07:00+08:00
description: "Anthropic 开源的 knowledge-work-plugins 是面向岗位工作的 Claude 插件市场：README 主推 11 个岗位插件，仓库另有 design、engineering、HR 等 6 个扩展插件与伙伴共建区，全部由 markdown 和 JSON 组成，无需代码和构建。"
draft: false
categories:
  - 技术笔记
tags:
   - GitHub-Trending
   - Anthropic
   - Claude
   - 工作流
slug: anthropics-knowledge-work-plugins-guide
github_repo: "anthropics/knowledge-work-plugins"
source_key: "gh:anthropics/knowledge-work-plugins"
author: 钳岳星君
---
`knowledge-work-plugins` 是 Anthropic 开源的岗位插件市场。它把三样东西打包成可安装的单元：岗位知识（写成技能文件）、外部工具（通过 MCP 连接）、固定工作流（斜杠命令入口）。它首先服务 [Claude Cowork](https://claude.com/product/cowork)——Anthropic 的桌面端代理应用，同时兼容 [Claude Code](https://claude.com/product/claude-code)。

当成聊天机器人的配置看，这个仓库像一组模板；当成工作界面看，它更接近一层岗位操作系统的雏形。

> **快速信息卡**（2026 年 9 月 22 日经 GitHub API 核实）
>
> - **Stars**: 25,335
> - **Forks**: 3,013
> - **License**: Apache-2.0
> - **语言**: Python（插件本体为 markdown 与 JSON）
> - **最后推送**: 2026-09-21

**学习目标**：读完这篇文章，可以回答——

- `knowledge-work-plugins` 到底是插件市场，还是一堆 prompt 模板。
- 它和 MCP、Claude Cowork、Claude Code 分别是什么关系。
- 仓库里的插件按什么思路划分，适合先从哪一个试起。
- 如果你想把它接进自己的团队流程，第一步应该先改哪里。

## 一句话判断

Anthropic 在仓库描述里给这批插件的定位是"主要供知识工作者在 Claude Cowork 中使用"。落到实现上，它是一组面向具体岗位的 Claude 插件样板：把技能说明、命令入口和 MCP 连接方式整理成文件化结构，让你不必每次都从空白对话开始教 Claude 怎么做销售调研、数据分析、法务初审或企业搜索。

## 先看结论：它解决的是"工作流太散"

很多人第一次看到插件，会下意识把它理解成浏览器扩展或聊天助手里的工具菜单。`knowledge-work-plugins` 走的是另一条路：把岗位工作流整体封装。

README 的表述是：插件告诉 Claude 你喜欢的工作方式、该从哪些工具和数据拉取内容、关键流程怎么处理、应该暴露哪些斜杠命令——目的是让团队得到更好、更一致的结果。它对准的痛点是"每次都要重新提示一遍"。

这是它和普通 prompt 模板的区别：

- prompt 只描述一次任务；
- 插件把一类工作长期固化下来；
- MCP 连接把 Claude 接到你的外部系统；
- 最终效果是让 Claude 更像"这个岗位的默认助手"，而不是每次都要重新交代的通用模型。

## 四层结构地图：插件、MCP、Cowork、Code

在展开插件清单之前，先把这套体系里四个东西的边界说清楚，否则后面的讨论容易混在一起。

| 层级 | 角色 | 谁来负责 |
| ------ | ------ | ------ |
| 插件（plugin） | 把岗位经验、命令入口、技能说明打包成一个可安装单元 | Anthropic 提供官方插件，团队可以 fork 改造 |
| MCP（Model Context Protocol） | 连接协议，让 Claude 读写外部系统 | 工具厂商或团队自己实现连接器 |
| Claude Cowork | 桌面端运行时，插件的主场景 | Anthropic |
| Claude Code | 命令行运行时，同样支持插件 | Anthropic |

一句话概括：**插件告诉 Claude 该做什么，MCP 决定 Claude 能访问什么，Cowork 和 Code 是承载插件机制的两套运行时。**

## 仓库里现在有什么

README 主推 11 个岗位插件（下表按 2026 年 9 月 21 日的 README 主分支状态核对）：

| 插件 | 主要用途 | 连接器 |
| ------ | ---------- | ------------ |
| `productivity` | 管理任务、日历、日常工作流和个人上下文 | Slack、Notion、Asana、Linear、Jira、Monday、ClickUp、Microsoft 365 |
| `sales` | 销售调研、通话准备、pipeline 检视、外联草稿、竞品 battlecard | Slack、HubSpot、Close、Clay、ZoomInfo、Notion、Jira、Fireflies、Microsoft 365 |
| `customer-support` | 工单分流、起草回复、整理升级单、把已解决问题沉淀为知识库文章 | Slack、Intercom、HubSpot、Guru、Jira、Notion、Microsoft 365 |
| `product-management` | 写需求、规划路线图、综合用户研究、同步干系人、跟踪竞品 | Slack、Linear、Asana、Monday、ClickUp、Jira、Notion、Figma、Amplitude、Pendo、Intercom、Fireflies |
| `marketing` | 写内容、campaign 规划、品牌口径、竞品简报、渠道效果汇报 | Slack、Canva、Figma、HubSpot、Amplitude、Notion、Ahrefs、SimilarWeb、Klaviyo |
| `legal` | 合同审阅、NDA 分流、合规指引、风险评估、会议准备 | Slack、Box、Egnyte、Jira、Microsoft 365 |
| `finance` | 记账凭证、对账、报表生成、差异分析、close 流程、审计支持 | Snowflake、Databricks、BigQuery、Slack、Microsoft 365 |
| `data` | 写 SQL、统计分析、搭图表、分享前校验分析结论 | Snowflake、Databricks、BigQuery、Definite、Hex、Amplitude、Jira |
| `enterprise-search` | 跨邮件、聊天、文档和 wiki 的一次性检索 | Slack、Notion、Guru、Jira、Asana、Microsoft 365 |
| `bio-research` | 连接临床前研究工具与数据库（文献检索、基因组分析、靶点优先级） | PubMed、BioRender、bioRxiv、ClinicalTrials.gov、ChEMBL、Synapse、Wiley、Owkin、Open Targets、Benchling |
| `cowork-plugin-management` | 创建或改造你自己的 Cowork 插件 | 无固定连接器 |

README 只把上面 11 个列入主表，但仓库主分支上实际还有 6 个同样结构的插件目录，2026 年 9 月核对时可以直接浏览：

| 插件 | 主要用途 |
| ------ | ---------- |
| `design` | 设计评审、设计系统管理、UX 文案、无障碍检查、研究综合、开发交接 |
| `engineering` | 站会、代码评审、架构决策、事故响应、调试、技术文档 |
| `human-resources` | 招聘、入职、绩效管理、政策指引、薪酬分析 |
| `operations` | 供应商管理、流程文档、变更管理、容量规划、合规跟踪 |
| `pdf-viewer` | 在交互式查看器中查看、批注、签署 PDF，盖章审批、填表 |
| `small-business` | 面向小企业主的一体化经营助手 |

另有一个 `partner-built/` 目录，存放与外部伙伴共建的插件，包括 Apollo（销售线索）、Slack、Zoom 等。

这个清单透露两个信号。一是定位：它是按岗位组织能力的插件市场——生产力、销售、客服、产品、法务、财务、数据、工程、HR、运营，一个岗位一个插件，而不是先做一堆零碎的能力开关。二是默认工作方式：**Claude 通过 MCP 连到团队原本就在用的系统，在真实数据上完成动作，会话内推理只是其中一环。**

## 这些插件到底由什么组成

README 给出的通用结构只有几类文件：

```text
plugin-name/
├── .claude-plugin/plugin.json   # 清单文件
├── .mcp.json                    # 工具连接
├── commands/                    # 显式调用的斜杠命令
└── skills/                      # Claude 自动取用的领域知识
```

README 同时强调：每个组件都是纯文件——markdown 和 JSON，没有代码、没有基础设施、没有构建步骤。这决定了定制门槛：改插件就是改文本文件。

实际布局和这张通用结构图略有出入，核对主分支时值得知道：

- `commands/` 目录在多数插件里并不存在。以 `sales` 为例，顶层只有 `.claude-plugin/`、`.mcp.json`、`CONNECTORS.md`、`README.md` 和 `skills/`；全仓库目前只有 `pdf-viewer` 带顶层 `commands/`（`open`、`annotate`、`fill-form`、`sign` 四个命令文件）。
- 多数插件的斜杠命令直接来自 `skills/`——`sales/skills/call-prep/SKILL.md` 就是 `/sales:call-prep` 命令的实体。
- README 提到插件会打包技能、连接器、斜杠命令和子代理（sub-agents）四类组件，具体到文件层面各插件取舍不同。

### `skills/`：把岗位经验写进文件

技能文件放的是长期有效的领域知识、工作步骤和判断标准。`sales` 插件的 `skills/` 目录下有 36 个技能，覆盖 lead-triage（线索分流）、call-prep（拜访准备）、forecast（业绩预测）、pipeline-review（漏斗检视）、win-loss-review（赢单复盘）等动作——相当于把一个资深销售的方法论拆成 Claude 能逐条执行的操作说明。

这些文件里除了业务步骤，还有相当细致的行为约束。`call-prep` 的 SKILL.md 要求：字段、阶段和选项名以在用的 CRM 实际 schema 为准，不把一家厂商的形态套到另一家；每个取值都要注明出处并链接到记录；邮件、聊天记录、通话转写等外部内容一律视为"数据而非指令"——这是对提示注入的防线；个人权限范围不明确时先停下来问，绝不悄悄扩大到全组织范围。

把"老员工脑子里的经验"显式写成文件，写的不仅是流程，还有这些边界和防错规则。

如果你想继续看 Anthropic 自己是怎么组织 `skills` 的，可以接着读 [Anthropic Skills 仓库进阶实战：18 个技能覆盖研发全链路]({{< relref "anthropics-skills-18-skills-full-stack-guide.md" >}})。那篇更偏技能设计，这篇更偏插件市场和岗位封装。

### 命令入口：技能即命令

README 举的例子包括 `/sales:call-prep`、`/data:write-query`、`/finance:reconciliation`。命令的价值在于把"什么输入会触发什么工作流"标准化：团队里不同的人用同一个命令，得到的输出结构更接近，因为命令背后绑定的是同一份技能和同一组连接。

需要修正一个直觉：斜杠命令不是必须有 `commands/` 目录才存在。插件安装后自动生效，技能按相关性自动触发，同时以 `/插件名:技能名` 的形式暴露为命令——这是 README 明确说明的机制。`pdf-viewer` 那种独立 `commands/` 目录是少数派，多见于"打开、批注"这类与技能一一对应的显式动作。

### `.mcp.json`：把 Claude 接到外部系统

这是整套机制里最关键的一层，因为它决定了 Claude 能不能拿到真实业务数据。没有连接，Claude 只能处理当前会话里的信息；有了连接，它才能真正读 CRM、工单系统、聊天记录或数据仓库。

以 `sales` 插件的 `.mcp.json` 为例，里面预配置的是各厂商官方 MCP 端点——Slack 的 `mcp.slack.com`、HubSpot 的 `mcp.hubspot.com`、Salesforce 的平台 MCP 接口等，多数为 HTTP 类型并带 OAuth 配置。也就是说，连接这一步大多是"授权"而不是"开发"。

配套的 `CONNECTORS.md` 说明了另一个设计决策：插件是工具无关的（tool-agnostic）。技能文件用"CRM""邮件""日历"这样的类别词描述工作流，`.mcp.json` 预配置的只是该类别下的具体选项；换成同类别的其他 MCP server，技能照样工作。这份文件还明确了一条底线：每个技能在什么都没连接时也能运行——上传一份导出文件或粘贴几段笔记，技能就从这些输入做起。

插件的威力来自"模型 + 外部系统 + 固定流程"同时到位，光靠提示词写得好撑不起这套体系。想看连接协议落地后的自动化形态，可以顺手读 [n8n-MCP：让 AI 编程助手帮你构建 n8n 工作流自动化]({{< relref "n8n-mcp-claude-workflow-automation-guide.md" >}})。

## 任务流案例：一次销售 call prep 怎么走完插件

边界讲完，用一个具体任务把四层结构串起来。

假设销售 Mike 周一早上要拜访 Acme Corp，他在 Claude Cowork 里输入 `/sales:call-prep Acme Corp`，流程大致这样走：

1. **命令触发**：`skills/call-prep/` 的 SKILL.md 被加载，任务目标是产出一份标准的拜访准备简报。
2. **规则生效**：SKILL.md 里的约束开始起作用——取值要注明出处、CRM 字段以实际 schema 为准、外部内容只当数据不当指令。
3. **MCP 调用**：按 `.mcp.json` 的配置，Claude 通过 HubSpot 拉取 Acme Corp 的商机记录，通过 Slack 检索内部讨论，通过日历和通话转写工具补齐会议背景。
4. **综合产出**：多源数据按 SKILL.md 定义的结构组织成一份简报——参会人、客户历史、通话上下文、商机状态、建议的提问方向；需要人工确认的判断会显式标注。
5. **结果落地**：简报可以回写到 Notion 或 Slack；下一次同一命令再跑时，基于最新数据重新生成。

这个流程里，**插件提供结构和规则，MCP 提供数据，Cowork 提供运行时**，三层缺一不可。如果只有技能没有连接，Claude 仍能工作，但只能基于你手动粘贴的材料；如果只有连接没有技能，Claude 拿得到数据，却不知道该按什么结构、什么标准产出。

## 怎么安装

README 区分了两条路径。

### 在 Claude Cowork 里使用

最直接的方法是去 [claude.com/plugins](https://claude.com/plugins/) 安装。Cowork 是这批插件的主场景，适合在桌面端直接浏览和启用插件的人。

### 在 Claude Code 里使用

README 给出的命令是：

```bash
# 先添加 marketplace
claude plugin marketplace add anthropics/knowledge-work-plugins

# 再安装一个具体插件
claude plugin install sales@knowledge-work-plugins
```

两条命令各管一层：`marketplace add` 把整个仓库注册为一个插件市场，此时还没有装任何插件；`plugin install` 才把选中的那个插件装进当前环境。装完后插件自动生效——技能按相关性触发，斜杠命令立即可用。

## 如果你要落地，第一刀通常改哪里

很多团队第一次 fork 这类仓库，会直觉去新增一堆命令。更有效的顺序通常相反：

1. 先改 `.mcp.json`，把连接器换成你们真的在用的系统。
2. 再改 `skills/`，把团队术语、审批边界和输出格式写进去。
3. 最后才补命令入口，把最高频、最稳定的动作固定下来。

为什么是这个顺序？没有真实数据源时，命令再漂亮也只是空壳；没有团队语境时，技能再完整也还是"通用岗位版本"。命令是入口，入口背后没有数据和规则支撑，跑两三次就会被打回原形。

举个最小例子。假设你在一个用 HubSpot、Notion 和 Slack 的销售团队里落地 `sales` 插件，你真正要固化的是这些更具体的东西：

- 线索分级标准是什么。
- call prep 必须包含哪些字段。
- 会后总结发给谁，格式长什么样。
- 哪些信息可以自动写，哪些判断必须人工确认。

插件化真正的收益，来自这些原本散落在口头经验里的细节被写成可重复执行的规则。

## 一个具体例子：为什么 `enterprise-search` 很像下一代企业搜索

如果只看名字，`enterprise-search` 似乎只是"帮你搜一下公司资料"。但仓库里的说明更接近一个统一检索层：

- 你提出一个自然语言问题；
- Claude 把问题拆成适合不同数据源的查询；
- 同时去聊天、邮件、文档和 wiki 里找证据；
- 最后把不同来源的结果综合成一个可引用的回答。

它和传统企业搜索的区别在于："查询改写、跨源搜索、结果综合"这三步被合并进同一条工作流。传统搜索只完成检索这一步，剩下的综合判断还要人来做。对团队内部的知识查找，这比"开 4 个标签页分别搜"更接近可用的助手体验。

## 它最适合谁

`knowledge-work-plugins` 并不适合所有人，但下面三类人会特别受益：

### 1. 已经在用 Claude，但提示词越来越长的人

如果你已经攒了一堆固定提示词——销售拜访准备模板、每周周报模板、法务初审模板，插件是更稳定的承载方式。你不需要每次复制一整段系统说明，只要把它收束进一个可安装的插件。

### 2. 想把团队流程标准化的人

插件让整个团队在同类任务上形成更接近的工作方法。对管理者或流程 owner 来说，这比散落在各人笔记里的 prompt 更容易维护、更容易迭代。

### 3. 已经开始接 MCP 的团队

如果你已经把 Claude 接进 Slack、Notion、Jira、HubSpot、Snowflake 之类的系统，插件能把这些连接真正组织起来。没有插件时，连接只是"可以访问"；有了插件，连接才变成"知道该怎么用"。

## 它的边界也很明确

这套仓库覆盖面广，但有几个边界需要说清楚。

### 它不是开箱即用的"行业真相"

官方插件给的是通用岗位起点，不是你公司的真实 SOP。你仍然需要补自己的术语、团队分工、审批规则和工具栈，插件才会贴合业务。

### 它也不能替你承担业务判断

插件能把工作流收束得更稳，但业务判断仍是人的责任。销售线索是否值得跟进、法务风险是否可接受、财务结论是否站得住，插件产出的是材料和结构，拍板的还是人。技能文件自己也这么要求：关键动作要么先问过你，要么把改动连同证据摆到你面前。

### 离开连接器，价值打折扣但没有归零

`CONNECTORS.md` 明确说每个技能在无连接时也能运行：上传一份导出文件、粘贴几段笔记，技能就从这些输入做起。但要形成"读真实 CRM、写回真实工单"的深度业务协作，连接器不可缺。无连接的插件是结构化提示，有连接的插件才是岗位助手——这个差别值得在评估预期时就分清。

### 插件来源不同，用前先读文件

README 说明主表的 11 个插件是 Anthropic 基于自身工作实践构建的；`partner-built/` 下的插件来自外部伙伴（Apollo、Slack、Zoom 等），维护方和迭代节奏与官方不同。选型时先分清来源，启用任何一个插件前，读一遍它的 README 和技能文件——反正它们都是 markdown，读起来不贵。

## 第一次上手，建议这样走

如果你准备试这套仓库，建议按下面的顺序，避免一上来就自己造插件：

1. 先挑一个最贴近自己岗位的官方插件。
2. 只接 1 到 2 个最常用的数据源，不要第一天就把全家桶都连上。
3. 连续跑几个真实任务，观察输出是不是已经稳定优于你原来的 prompt。
4. 再去修改 `skills/` 或 `.mcp.json`，把公司术语和流程慢慢固化进去。
5. 只有当现成插件不够用时，再考虑用 `cowork-plugin-management` 自建插件。

这样做的好处是，你先验证"插件化工作流"是否适合你，再决定要不要投入更多维护成本。插件就是 markdown 文件，fork 仓库、改完提 PR 即可贡献——试错成本主要是时间，不是工程。

如果你更关心"把能力做成稳定流程"这件事本身，不局限于插件形态，也可以继续读 [Claude Code Harness：给 AI 编程助手加一套有约束的交付流程]({{< relref "claude-code-harness-disciplined-delivery-loop.md" >}})。它展示的是另一种把经验收束成可复查工作流的方法。

## 常见问题

### 它和 MCP 是什么关系

MCP 是连接协议，插件是工作流封装。MCP 负责把 Claude 接到外部工具；插件负责告诉 Claude 在这些工具之上该怎么工作。

### 它和普通 prompt 模板有什么区别

模板通常只解决一次任务的输入组织；插件把角色知识、命令入口和外部系统连接一起打包，适合长期反复执行的工作。

### 适合个人用，还是更适合团队

两者都能用，但团队收益通常更大。个人用户能节省重复提示的时间；团队则能把分散的经验沉淀成统一入口。

## 自测问题

- 如果你不接任何外部系统，这套插件还能带来什么，带不来什么。
- 对你所在团队来说，最值得先固化的是连接器、技能规则，还是命令入口。
- 你现在最常复制粘贴的一段 prompt，是否已经适合升级成一个插件能力。

## 最后判断

`knowledge-work-plugins` 把一个方向写得很具体：**Claude 的工作界面正在从通用聊天框，往"按岗位组织"的操作层走。** Anthropic 自己的动作是佐证——Cowork 作为桌面端代理应用成为插件主场景，开源的这批插件按销售、法务、财务这样的岗位划分，README 里反复出现的词是"specialist for your role, team, and company"。

如果你只是偶尔问几个问题，这个仓库不会立刻改变什么；如果你已经把 Claude 放进真实工作流里，尤其已经开始接 MCP，它值得细读。你真正该关注的，不止是那十几个插件本身，而是它们展示的组织方式：如何把岗位经验、命令入口和外部系统连接，写成一条能长期复用、可以逐文件审查的工作流。

## 相关链接

- GitHub 仓库：[anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)
- 插件入口：[claude.com/plugins](https://claude.com/plugins/)
- Claude Cowork：[claude.com/product/cowork](https://claude.com/product/cowork)
- Claude Code：[claude.com/product/claude-code](https://claude.com/product/claude-code)
- Model Context Protocol：[modelcontextprotocol.io](https://modelcontextprotocol.io/)
