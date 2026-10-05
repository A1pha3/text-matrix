---
title: "Cursor 官方插件仓库：两级清单如何撑起一个 96 插件的市场"
date: "2026-08-23T03:21:00+08:00"
lastmod: "2026-10-02T00:00:00+08:00"
slug: cursor-plugins-official-marketplace-repo
github_repo: "cursor/plugins"
source_key: "gh:cursor/plugins"
description: "cursor/plugins 是 Cursor 插件体系的规范与官方市场仓库：仓库根的 marketplace.json 登记全部插件，每个插件目录用 plugin.json 声明 skills、rules、agents、commands、hooks 与 MCP 集成。本文解析两级清单、schema 约束、CI 校验与插件创建的完整流程。"
draft: false
categories: ["技术笔记"]
tags: ["Cursor", "插件", "MCP", "AI 编程", "Agent"]
---

# Cursor 官方插件仓库：两级清单如何撑起一个 96 插件的市场

## 核心判断

cursor/plugins 同时扮演两个角色：**插件规范**（schemas/ 下两份 JSON Schema 加一条 CI 流水线，定义什么是一份合法的插件）和**官方市场**（`.cursor-plugin/marketplace.json` 登记 96 个插件，从分支审查工具到 Gmail 集成）。Cursor 官方仓库描述里 "plugin specification and official plugins" 这个措辞，把两层都说全了。

读懂这个仓库只需要抓住一个结构：**两级清单**。仓库根的 `marketplace.json` 回答"市场上有什么"，每个插件目录里的 `.cursor-plugin/plugin.json` 回答"这个插件由什么组成"。组件本身——技能、规则、agent 定义、命令——都是普通文件，靠清单里的路径声明挂进插件。清单是身份证，目录约定是默认布局。

仓库 2026 年 1 月 23 日建仓，2026-10-02 的 GitHub API 读数为 9,296 stars / 879 forks，最新提交停在 2026-10-01（PR #478）。插件数从 8 月下旬的 33 个涨到现在的 96 个，六周近三倍——这个增速与 Cursor 被 SpaceX 收购后的生态整合直接相关，后文展开。

## 规模与生态：两个月，插件数从 33 到 96

先看两份相隔六周的读数（后者为本轮核查时点）：

| 时点 | 插件总数 | 根目录插件 | third_party 集成 | 数据来源 |
|------|---------|-----------|-----------------|---------|
| 2026-08-21 | 33 | 13 | 20 | 当日最后提交 46125561 的 marketplace.json |
| 2026-10-01 | 96 | 16 | 80 | main 分支 marketplace.json |

增量几乎全部来自 `third_party/`：60 个新 SaaS 集成在六周内进入市场，其中 X 系产品（X、X Ads、X Money）和一批金融类（Robinhood、Coinbase、Interactive Brokers、S&P Global、Webull、eToro）密集出现。部分集成的描述直接点名 Grok——`finance` 插件写 "so Grok can help with questions about your spending"，`shopify-store` 写 "so Grok can answer questions"。

背景在仓库外面：Cursor 官方博客 2026-08-14 宣布被 SpaceX 收购完成，程序始于当年 4 月与 SpaceXAI 的合作公告，Grok 4.6 被列为合作后的首个模型成果。收购完成后，这份市场仓的集成清单开始向 Grok 与 X 生态倾斜——时间线对得上，尽管单个集成的接入动机只能看到结果、看不到决策。

顺带修正一个容易想错的点：`third_party/` 指的是"被集成的第三方服务"，而不是"第三方维护"。这 80 个插件的 `plugin.json` 作者字段清一色是 Cursor（`plugins@cursor.com`）——Cursor 替这些 SaaS 做集成包装，替它们维护。

## 系统地图：两级清单、六类组件、一道 CI

| 部件 | 位置 | 职责 |
|------|------|------|
| `marketplace.json` | 仓库根 `.cursor-plugin/` | 市场总清单：name、source 目录、description |
| `plugin.json` | 每个插件目录 `.cursor-plugin/` | 单插件清单：元数据 + 组件路径声明 |
| 两份 JSON Schema | `schemas/` | 约束上面两份清单的字段与格式 |
| `validate-plugins.mjs` | `scripts/` | CI 校验脚本（Ajv 实现） |
| 组件文件 | 插件目录内 | skills/rules/agents/commands/hooks/mcpServers 六类 |

README 里画了一张目录树，树的第一层写着 `plugins/`——实际仓库没有这层目录，插件目录直接放在仓库根。那张图描述的是"一个多插件仓库的通用布局"，照着找文件会扑空，按根目录找就行。

单个插件的目录长这样（以 `third_party/gmail` 为例，这是结构最全的一类）：

```
gmail/
├── .cursor-plugin/
│   └── plugin.json    # 清单：mcpServers 指向 ./mcp.json
├── mcp.json           # MCP 服务器定义
├── assets/logo.svg
├── README.md
├── CHANGELOG.md
└── LICENSE
```

工具类插件则是另一套组件组合。比如 `thermos` 声明 `skills: "./skills/"` 和 `agents: "./agents/"`，没有 rules 也没有 MCP——它靠三个技能文件和两个 subagent 定义工作。组件按需取用，清单只声明用了哪些。

## plugin.json：21 个字段，只有 1 个必填

`schemas/plugin.schema.json` 定义了全部约束。完整字段如下：

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | string | kebab-case 唯一标识，**唯一必填项** |
| `displayName` | string | 人类可读的插件名 |
| `description` | string | 一句话描述 |
| `version` | string | 语义化版本 |
| `minClientVersions` | object | 各客户端标识对应的最低版本 |
| `author` | object/string | 作者信息 |
| `publisher` | string | 发布方 |
| `homepage` / `repository` | string | 主页与源码仓库 URL |
| `license` | string | SPDX 标识符（如 "MIT"） |
| `logo` | string | 相对路径或绝对 URL |
| `keywords` / `tags` | array | 发现与过滤 |
| `category` | string | 市场分类 |
| `commands` / `agents` / `skills` / `rules` | string/array | 组件文件的 glob 或路径 |
| `hooks` | string/object | 钩子配置的路径或内联对象 |
| `mcpServers` | string/object/array | MCP 配置：路径、内联对象或两者混排的数组 |
| `variables` | object | 用户可配置变量的 JSON Schema |

`required` 数组里只有 `name`。schema 还设了 `additionalProperties: false`——清单里多写一个字段，CI 直接报错。官方脚手架的推荐写法是补上 `version`、`description`、`author`、`license`、`keywords`。

真正省力的设计在组件发现机制上。`create-plugin` 脚手架的技能文件里写明：组件放在默认目录（`skills/`、`rules/`、`agents/`、`commands/`）就会被自动发现，**只有需要非默认路径时才在 plugin.json 里显式声明**。所以 `thermos` 的清单里只有两行路径声明，`gmail` 只有一行 `mcpServers: "./mcp.json"`——不是偷懒，是约定覆盖了大多数场景。

组件文件的格式也有约定：规则是 `.mdc` 文件（frontmatter 带 `description`、`alwaysApply`，可选 `globs`）；技能是 `skills/<名字>/SKILL.md`（frontmatter 带 `name`、`description`）；agent 定义和命令是普通 Markdown。

`minClientVersions` 这一层还藏着一个信号。字段按客户端标识分别声明门槛，而标识不止 `cursor` 一个：多数集成要求 `cursor: 3.13.0` 以上，微软系（OneDrive、Outlook、SharePoint）要 3.19.0，Google 文档三件套要 3.22.0——但 `x-money`、`finance`、`shopify-store` 三个 Grok 生态插件把 `cursor` 标成了 `never`，只面向 `grokbot` 和 `sand` 两个客户端。市场的清单里已经出现了不打算进 Cursor 的插件：这份市场服务的客户端面，比 Cursor 本体要宽。

## CI 如何保证 96 份清单不打架

`.github/workflows/validate-plugins.yml` 只在 PR 触及 `marketplace.json`、任何 `plugin.json` 或 `schemas/**` 时运行，跑一遍 `scripts/validate-plugins.mjs`。脚本用 Ajv 做三件事：

1. 校验 `marketplace.json` 符合市场 schema；
2. 遍历清单里每个插件，检查 source 目录存在、`.cursor-plugin/plugin.json` 存在、清单符合插件 schema（多余字段会连同字段名一起报错）；
3. 比对市场登记的 name 与插件自己的 name 是否一致。

三道闸门都不重，但合起来保证了一件事：marketplace.json 里登记的每一个名字，都对应一个真实存在、清单合法、名字对得上的插件目录。96 个插件、两个月 60 个新增，没有这层自动化，清单漂移几乎必然发生。

## 一次分支审查如何流过插件：thermos 案例

装插件的入口是 Cursor 内的 `/add-plugin <name>` 命令。装完之后组件进入上下文，技能可以被调用，agent 可以被派活。以官方的 `thermos`（分支深度审查插件）为例，一次"把这个分支审一遍"的请求会这样流动：

1. `thermos` 技能作为总入口接收请求，按 README 描述编排整个流程；
2. 并行派出两个 subagent——`thermo-nuclear-review-subagent`（安全与正确性审计，覆盖 bug、破坏性变更、特性开关泄漏）和 `thermo-nuclear-code-quality-review-subagent`（可维护性与抽象质量审计）；
3. 两个审计技能的 SKILL.md 都标了 `disable-model-invocation: true`——模型不能自作主张触发，只能由用户显式调用。审查这种重操作不留给自动决策；
4. 汇总结果后可选进入 merge-ready PR 流程。

这个案例能看出插件体系的分工方式：SKILL.md 定义"什么时候用、按什么标准做"，agents/ 目录定义"派谁去做"，plugin.json 把两者挂在一起。三层各管一段，互不掺杂。

## 官方插件全景：10 个官方出品，6 个个人精选

根目录 16 个插件并不全是 Cursor 自研，按 `plugin.json` 的作者字段分两类：

- **Cursor 官方（10 个）**：`thermos`（分支审查）、`pr-review-canvas`（PR diff 按重要性分组的审查画布）、`docs-canvas`（文档导航画布）、`orchestrate`（跨云并行派发，含 planner/worker/verifier 角色）、`ralph-loop`（迭代自指循环）、`agent-compatibility`（仓库兼容性扫描）、`advisor`（重大决策前咨询更强模型）、`teaching`（技能映射与练习计划）、`create-plugin`（脚手架）、`cursor-sdk`（TypeScript SDK）
- **个人作者精选（6 个）**：`continual-learning`、`cursor-team-kit`、`cli-for-agent`、`grok-voice` 均出自 Eric Zakariasson，`pstack` 出自 Lauren Tan（"想快就先做深"的严格 agent 工作流），`dyl-stack` 是 Dylan Gattey 在 pstack 之上的个人风格变体

给个人的插件收录进官方仓库根目录，这个信号值得注意：市场在收编社区里被验证过的工作流，而不只是官方产品的延伸。

`third_party/` 的 80 个按用途大致分四档：Google 全家桶（Gmail/Drive/Calendar/Docs/Sheets/Slides/BigQuery）、微软与办公协作（GitHub、Teams、SharePoint、OneDrive、Outlook、Craft、Mem、Readwise）、销售与营销（Salesforce、HubSpot、Attio、Klaviyo、Semrush、Ahrefs）、金融交易（前述 X Money、Robinhood、Coinbase 等）。大而不深——每个集成基本是 MCP 服务器定义加一份说明，能力上限取决于对应 SaaS 的 API。

## 从零到可发布：创建插件的完整路径

`create-plugin` 把流程拆成三步（对应 README 的 Typical flow）：

1. 用 `/create-plugin` 命令，带上插件名、用途和目标组件类型；
2. 生成或更新 `plugin.json`，按需添加 rules / skills / agents / commands；
3. 发布或提交市场前，跑 `review-plugin-submission` 做提交前质量检查。

支撑它的还有两个部件：`plugin-quality-gates` 规则（标记 `alwaysApply: true`，写插件期间全程生效）负责守住六条底线——清单存在且 name 合法；路径必须是插件目录内的相对路径（禁止 `..` 穿越）；声明的组件路径必须对应真实文件；四类组件都要带合规 frontmatter；插件职责保持聚焦，README 写清安装与用法；新插件默认存到 `~/.cursor/plugins/local/` 以便即刻可用。`plugin-architect` agent 则在动手前帮你定结构。

脚手架的默认落点就在本地：`~/.cursor/plugins/local/<插件名>/`，放进去即刻可用，不需要安装动作。先本地验证，再决定是否提交 PR 进官方市场——提交后等的就是上一节那道 CI。

## 采用建议与边界

- **想写 Cursor 插件**：从 `~/.cursor/plugins/local/` 里的本地插件起步成本最低，组件放默认目录就生效；想发布再 clone 本仓库对照 schema 和现有插件补齐细节，提交前跑 `review-plugin-submission`。
- **想研究 agent 工作流设计**：根目录那 16 个插件比 third_party 有料得多——orchestrate 的角色分工、pstack 的深度优先工作流、thermos 的"重操作禁止自动触发"，都是可以直接抄进自己 agent 体系的设计。
- **边界一**：这是市场仓，不是 Cursor 客户端源码。插件如何被加载执行要看客户端与 `cursor-sdk`。
- **边界二**：许可证状态有点含糊——仓库根没有 LICENSE 文件（GitHub 因此不识别许可证），但 README 有 License 一节自述 MIT，各插件清单的 `license` 字段也都写着 MIT。要复用代码，以插件目录内的 LICENSE 文件为准。
- **边界三**：集成类插件的能力上限是对应 SaaS 的 API，期待"深度自动化"会失望；它们解决的是"不用自己写 MCP 配置"。

六周 60 个新集成的增速说明这份清单还在扩张期，X 与 Grok 生态的接入只是开始。对关注 Cursor 插件体系的人来说，这个仓库值得定期回看——它现在是 Cursor 生态里变化最快的地图。

## 阅读路径

- [GitHub 仓库](https://github.com/cursor/plugins) — 两级清单、schema 与全部插件源文件
- [官方博客：Cursor is now a part of SpaceX](https://cursor.com/blog/joining-spacex) — 收购公告与 Grok 合作背景
- [Cursor 文档](https://cursor.com/docs) — 客户端侧的插件安装与使用
