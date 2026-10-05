---
title: "Agentic Awesome Skills 拆解：2,488 个 agent 技能、AAS Core 的信任边界，和八个月里的三次变形"
date: "2026-04-12T18:01:00+08:00"
lastmod: "2026-09-30T12:00:00+08:00"
slug: antigravity-awesome-skills-ai-tools-ecosystem-guide
github_repo: "sickn33/agentic-awesome-skills"
source_key: "gh:sickn33/agentic-awesome-skills"
description: "sickn33/agentic-awesome-skills 的 2026-09-30 快照：从 1 月的 179 个技能到 9 月的 2,488 个，7 月改名并转向 AAS Core——本地 MCP 只做目录发现、结构校验和计划预览，把「选哪个技能」留给 agent 自己。附安装命令、分类与 risk 分布实统、一次完整任务流和采用边界。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "Claude Code", "Codex", "MCP", "AI 工具"]
toc: true
---

## 这篇文章在回答什么

`sickn33/agentic-awesome-skills`（下文简称 AAS）是社区维护的 agent 技能目录，截至 2026-09-29 收录 2,488 个可安装的 `SKILL.md` 文件，47,075 stars（GitHub API）。它容易和两类东西混淆：一是 awesome 清单——只给链接不管安装；二是「技能商店」——替你挑好、打包、一键启用。AAS 两个都不是，它的 README 把自己放在中间：目录可搜索、可安装、机器可读，但**选哪个技能这件事，项目刻意不替你做**。

这个立场在 2026 年 7 月变得明确。v15.0.0 引入 AAS Core——一个本地 CLI 加 stdio MCP（Model Context Protocol，agent 连接外部工具的标准协议），把「给 agent 配技能」变成一条可审查的流水线：agent 读你的项目、自己挑技能，Core 只校验所选 ID 的结构和身份，生成一份不可变的计划预览供人过目。搜索结果没有相关性评分，Core 不做排名，manifest 上限 128 个技能，`apply`（应用）和 `recover`（恢复）至今是实验性的可选项。一句话概括这个设计取舍：**AAS 把目录和校验做成了基础设施，把判断留在你和你的 agent 手里**。

名字里的「Antigravity」是历史遗留。项目 1 月创建时叫 Antigravity Awesome Skills，7 月 9 日 v14.0.0 改名 Agentic Awesome Skills，README 同时声明这是独立社区项目，与 Google 没有隶属或背书关系。旧仓库地址 301 重定向到新地址。

这篇文章回答四个问题：这个项目半年多经历了什么；AAS Core 具体怎么工作、边界画在哪；2,488 个技能的目录里实际有什么；真要用，从哪一步开始。

## 快速信息卡

| 指标 | 数值 | 来源与快照时间 |
|------|------|----------------|
| 仓库 | [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills)（旧名 301 重定向） | GitHub API，2026-09-29 |
| Stars / Forks | 47,075 / 6,856 | 同上 |
| 当前版本 | v18.9.0（2026-09-29 发布） | Releases 页 |
| 技能总数 | 2,488 | README registry-sync 注释，v18.9.0 |
| 许可证 / 主语言 | MIT / Python | GitHub API |
| npm 包 | `agentic-awesome-skills`，latest 18.9.0（2026-07-09 首版，62 个版本） | npm registry |
| 托管目录 | [aaskills.tech](https://aaskills.tech/)（Vercel OSS 项目托管） | README |
| 分类标签 | 107 个 category 值 | 本文对 `skills_index.json` 实统 |

## 从 179 到 2,488：八个月三次变形

AAS 的变化速度是这个项目最容易被低估的属性。三个 tag 把演变切成三段：

| 时间 | 版本 | 发生了什么 |
|------|------|------------|
| 2026-01-14 | — | 建仓 |
| 2026-01-19 | v1.0.0 "Marketing Edition" | 首发 179 个技能，定位「Antigravity Awesome Skills」，靠复制文件安装 |
| 2026-04-14 | v10.1.0 | 1,410 个技能、32,985 stars（README registry-sync 注释）；有了 npm 安装器 `npx antigravity-awesome-skills` |
| 2026-06-21 | v13.1.0 | 1,681 个技能；npm 包名仍是旧名 |
| 2026-07-09 | v14.0.0 | **改名**：项目身份、npm 包、公开 URL 全部切到 Agentic Awesome Skills；1,936 个技能 |
| 2026-07-18 | v15.0.0 | **转型**：发布 AAS Core，仓库围绕「本地、确定性的 Core」重新定位，保留目录、插件、bundle 等原有入口 |
| 2026-09-08 | v17.0.0 | 证据（evidence）与便携 bundle；2,115 个技能 |
| 2026-09-27 | v18.7.0 | 全目录分类完成，`uncategorized` 清零；2,474 个技能 |
| 2026-09-29 | v18.9.0 | 目录迁到 Vercel 托管的 aaskills.tech；2,488 个技能 |

发布节奏同样值得注意：323 个 tag，9 月下旬几乎一天一个 release。按 `skills_index.json` 的 `date_added` 字段统计，技能增长有两个高峰——2 月净增 923 个（最早的批量收录潮），9 月净增 596 个。这不是一个「稳定维护」的项目，而是一个高速膨胀中的项目；下文的信任边界设计，也要放在这个背景下理解。

## 系统地图：五层各管一件事

AAS 的仓库容易看晕，因为它同时是技能库、网站、CLI、插件仓库。拆开是五层：

| 层 | 组成 | 职责 |
|----|------|------|
| 目录层 | `skills/` 下 2,488 个 `SKILL.md`；`skills_index.json`（配 v1 JSON schema）；`CATALOG.md` | 技能正典与机器可读清单 |
| 核心层 | AAS Core：`aas` CLI + 本地 stdio MCP | 目录搜索、结构校验、计划预览 |
| 分发层 | `npx agentic-awesome-skills` 安装器；Claude Code / Codex 插件镜像；`plugins/` 下 60 个插件目录 | 把技能文件放进各 host 的技能目录 |
| 发现层 | aaskills.tech 托管目录；Workbench（浏览器本地） | 网页端浏览与栈/计划审查 |
| 治理层 | Skills Registry CI、Skill Review、CodeQL、Socket、Snyk | 收录审查与依赖安全 |

数据流向是单向的：目录层是唯一的正典来源，核心层只读它，分发层把审查过的结果落盘到你的技能目录，发现层是同一份目录的网页视图。Workbench 在浏览器内存里审查工件，不碰你的文件系统。

## AAS Core 的工作方式：五步，外加一排「不做」

Core 的完整流程（v18.9.0 的 [Core 指南](https://github.com/sickn33/agentic-awesome-skills/blob/v18.9.0/docs/users/aas-core.md)）：

1. **配置本地 MCP**。把 AAS 的 MCP server 挂进 Codex 或 Claude Code：

```bash
npm exec --yes --ignore-scripts --package=agentic-awesome-skills@18.9.0 -- aas mcp configure \
  --host codex \
  --scope user \
  --config /absolute/path/to/codex/config.toml \
  --cache-root /absolute/path/to/aas-cache
```

2. **让 agent 挑技能**。你描述目标，agent 用 `search_skills` 查目录、按自己的项目理解挑出具体 ID。搜索结果按稳定的目录顺序返回，没有相关性评分——Core 明确不替你做语义判断。
3. **校验所选集合**。只读工具 `compose_stack` 校验 ID 是否存在、结构是否合法，产出一份 schema 2 的 stack manifest（`aas-stack.json`），上限 128 个技能。
4. **生成计划预览**。`aas stack plan` 写一份不可变（immutable）的预览，`aas stack validate` 复查 manifest。这一步的产物是给人看的，不落盘到任何技能目录。
5. **审查后安装**。确认无误后走 `aas stack install-preview`，把选中的 ID 交给直接安装器，永远以 `--dry-run` 预览开头；你复查文件清单后，去掉 `--dry-run` 真正安装。

第 5 步里藏着一个容易被误读的边界：**Core 本体不安装任何东西**。MCP 调用不装不删、不改 host 配置；真正动文件系统的是独立的直接安装器，而且走预览-确认两步。`stack apply` 和 `stack recover` 这两条 Core 自己的应用路径至今是实验性 opt-in，官方文档明确把它们排除在受支持的安全声明之外。

把 v18.9.0 文档里的边界汇成一张表：

| 能力 | 状态 |
|------|------|
| 排名 / 推荐 / 语义适配认证 | 不提供，agent 自己判断 |
| stack manifest 上限 | 128 个技能 |
| 技能正文（经 MCP 返回时） | 标记为不可信内容（untrusted content），不因经过 MCP 而获得指令权威 |
| MCP 调用的副作用 | 无——不安装、不删除、不改配置、不更新目录 |
| apply / recover | 实验性，需显式 opt-in |
| 守护进程 / 隐式自动更新 | 无 |
| 结构校验的含义 | 只证明 ID 存在、结构合法，不证明语义匹配、兼容性、设置正确或运行安全 |

最后一条是全文最值得记住的：Core 的校验是**结构和身份**层面的。一份通过校验的 stack manifest 不保证里面的技能适合你的项目，甚至不保证技能内容本身安全——这层判断被刻意留在了流程之外。

## 目录里有什么：分类、risk 与来源的实统

107 个 category 标签长尾很重，头部集中：

| category | 技能数 | category | 技能数 |
|----------|-------:|----------|-------:|
| security | 263 | marketing | 104 |
| development | 214 | business | 82 |
| devops | 163 | content | 77 |
| cloud | 147 | web-development | 69 |
| ai-ml | 136 | workflow | 68 |

（按 v18.9.0 的 `skills_index.json` 统计，2026-09-29 快照。）

每个技能还带一个 `risk` 字段，官方分档语义写在 getting-started 指南里：`none`（纯文本/推理指引）、`safe`（只读或低风险操作）、`critical`（改变状态或影响部署）、`offensive`（带 Authorized Use Only 警告的渗透测试/红队指引）、`unknown`（待维护者分诊的存量内容）。实测分布：`critical` 1,235、`safe` 971、`offensive` 142、`none` 103、`unknown` 37。这个字段是信息性的——Core 不用它排名或排除技能——但安装器认它：OpenCode 这类支持过滤的 host 可以 `--risk safe,none` 只装低风险档。近半技能标 `critical` 不必慌，它说的是「这份指引会教你做改状态的事」，装之前值得看一眼 `SKILL.md` 自己写了什么；安装器还提供 `npx agentic-awesome-skills audit --skills <ids>` 做静态审计，官方同时说明它「报告高风险能力，但不证明技能安全」。

来源结构：`source` 字段里 1,430 个标 `community`，165 个标 `self`，其余按收录出处标注具体仓库——包括 anthropics/skills、openai/skills、microsoft/skills、google-gemini/gemini-skills、vercel-labs/agent-skills、supabase、expo、huggingface、weaviate 等官方技能库的整批收录，也包括 BagelHole/DevOps-Security-Agent-Skills（163 个）这样单次贡献上百个技能的社区仓库。出处和许可证集中在 [attribution ledger](https://github.com/sickn33/agentic-awesome-skills/blob/main/docs/sources/sources.md) 里逐条可查，其中不少批次明确标注 docs-only（只收文档、不带运行时）。2,488 个技能里只有 20 个标了 `manual` 设置，其余开箱即用；插件分发覆盖面也高——2,426 个支持 Claude 插件目标，2,401 个支持 Codex。

### 专项插件：13 个推荐位，58 个 bundle

README 的「Recommended Specialized Plugins」推荐表列了 13 个领域插件，按技能数打包：

| 插件 | 技能数 | 面向 |
|------|-------:|------|
| AAS Web App Builder | 10 | 前端与全栈开发 |
| AAS Product Design Studio | 10 | 产品 UI、品牌、无障碍 |
| AAS Security Engineer | 10 | 授权范围内的安全测试与加固 |
| AAS Agent & MCP Builder | 10 | agent 应用、MCP 工具、RAG |
| AAS API Platform Builder | 10 | API 设计、OpenAPI 契约、鉴权 |
| AAS SaaS Launch & Revenue | 10 | SaaS MVP、定价、支付、SEO |
| AAS AI Product & Evaluation Ops | 10 | AI 产品指标、评测、追踪 |
| AAS Data Analytics / QA & Test / DevOps & Cloud | 各 10 | 数据分析、测试自动化、基础设施 |
| AAS Secure App Builder / Documents & Presentations | 各 9 | 安全内建开发、办公文档 |
| AAS Accessibility & Inclusive UX | 8 | WCAG 审计与无障碍 QA |

`plugins/` 目录下实际有 60 个插件目录：2 个主插件加 58 个 bundle 形态的领域包，13 个推荐位是其中打过「可兼容」标签的子集。

### Bundles 与 Workflows：两个容易被混用的词

[Bundles](https://github.com/sickn33/agentic-awesome-skills/blob/main/docs/users/bundles.md) 按**角色**打包技能——Essentials、Web Wizard、Security Engineer、OSS Maintainer 等；[Workflows](https://github.com/sickn33/agentic-awesome-skills/blob/main/docs/users/workflows.md) 按**顺序**组织技能——比如先用 `concise-planning` 做规划、再用 `verification-before-completion` 做验收。官方对两者的定位：bundle 是「工具箱」，workflow 是「执行手册」；它们是安装子集和激活预设，不是 `@web-wizard` 这种可以整体调用的超大技能。Antigravity 用户如果装多了导致上下文过载，可以用 `./scripts/activate-skills.sh --clear "Web Wizard"` 只保留一个 bundle 的技能处于激活态。

## 任务流案例：给 Codex 配一套带验收的规划技能

把上面的机制串成一次真实操作。目标：给 Codex CLI 配上「规划 + 完成前验证」两个技能，全程不装多余的东西。

**第一步，配 MCP**（跑一次即可，命令见上文「AAS Core 的工作方式」）。

**第二步，让 agent 自己选**。在 Codex 里说：检查我的项目，从 AAS 目录里挑出做实现规划和完成前验证的技能。agent 通过 MCP 搜目录、读技能描述，返回它选中的 ID——比如 `concise-planning` 和 `verification-before-completion`。这一步它的判断依据是技能的元数据和正文，Core 没有参与推荐。

**第三步，校验并预览**：

```bash
aas stack validate   # 复查 manifest 的结构与 ID
aas stack plan       # 写出不可变的计划预览
```

**第四步，预览安装，确认执行**：

```bash
aas stack install-preview   # 生成 dry-run 预览，不落盘
npx agentic-awesome-skills --codex \
  --skills concise-planning,verification-before-completion --dry-run
# 复查预览里的目标路径与文件清单后，去掉 --dry-run 重新执行
```

整条链路上，人审了两次：一次审 plan（agent 的选择是否合理），一次审 dry-run（文件将落到哪里）。Core 负责的是让这两次审查有可靠的依据——ID 真实存在、结构合法、计划不可被中途篡改。

## 安装：一条 npx 命令对十二个目标

不经过 Core 也可以直接安装。安装器按 host 区分目标：

```bash
npx agentic-awesome-skills --cursor    # Cursor
npx agentic-awesome-skills --gemini    # Gemini CLI
npx agentic-awesome-skills --codex     # Codex CLI
npx agentic-awesome-skills --agy       # Antigravity CLI
npx agentic-awesome-skills --path .agents/skills --category development --risk safe,none
```

README 的「Choose Your Tool」表列了十二个具名目标：Claude Code（另有插件市场入口）、Cursor、Gemini CLI、Codex CLI、Autohand Code、Antigravity IDE 与 Antigravity CLI（`agy`）、Kiro CLI 与 Kiro IDE、GitHub Copilot（preview，`gh skill install` 需 `--pin` 锁版本）、OpenCode、AdaL CLI，外加任意 `--path` 自定义目录。

两个实操提醒。其一，**Antigravity 的技能目录是被监听的**，装太多会撑爆上下文，所以对 Antigravity 目标安装器默认要求显式选择（`--skills` 列表、过滤器或 `--all` 覆盖），这是有意设计而非限制。其二，裸安装必须带明确的选择——不带 `--skills` 的全量安装需要显式 `--all`，这个约束挡住了「一键把 2,488 个技能全塞进去」的误操作。

## 采用建议：谁该用，谁不必急

**适合现在就上手**：

- 每天用 Codex / Claude Code / Cursor，想系统性给 agent 配技能，而不是每次手写长 prompt 的人。
- 要给团队定一份可审查的技能清单的人——`aas-stack.json` 就是现成的清单载体，plan 预览可以直接当评审材料。
- 插件作者想一次覆盖多个 host 的——Claude / Codex 插件镜像加机器可读的 `skills_index.json` 省掉自己写分发的工作。

**不必急，或只用一半**：

- 只需要一两个具体技能——跳过 Core，直接 `npx` + `--dry-run` 装完即走。
- 期待「精选高质量技能」——2,488 个技能的目录里，docs-only 的转载数量庞大、质量参差是结构性的；Core 的结构校验不等于质量认证，README 也没有做任何排名。挑技能仍要自己读 `SKILL.md`。
- 受监管行业的生产环境——技能是别人写的 Markdown 指令，可能要求调用付费 API、向外部服务发数据；`offensive` 档的 142 个技能是安全测试用途，装之前先过 [安全指引](https://github.com/sickn33/agentic-awesome-skills/blob/main/docs/users/security-and-antivirus.md) 和你自己的合规流程。

**起步顺序**：先用 `npx` 挑两三个技能装到当前项目跑一周，确认这个形式对你的工作流有用；需要规模化选型时再配 Core 的 MCP；把 bundles 和 workflows 当起点，而不是追求装满 128 个的上限。

## 质量与维护：CI 挡在收录前面，发布一天一个

收录侧的自动化相当完整：PR 要过 Skills Registry CI、Skill Review、Dependency Review、CodeQL、Socket、Snyk 六道检查，贡献者被要求跑 `npm run validate`、从官方模板起步，并且「技能内容与高风险指引需要人工逻辑与安全审查」。18.7.0 把全目录 `uncategorized` 清零，说明元数据纪律在收紧。

维护结构是「单主体 + 机器人 + 社区」：sickn33 个人 930 次提交居首，github-actions bot 811 次居次，社区贡献者 sck000 468 次居第三，其余三百多名贡献者的提交量都在数十次以下。发布节奏几乎一天一个版本——好处是新技能收录快、问题修复快；代价是版本漂移也快，把 AAS 接进自动化流程时应该锁版本号（npm 命令里显式写 `@18.9.0`，而不是追 latest）。文档是对这个项目的好评点：`docs/users/` 下十余篇指南覆盖安装、Core 信任边界、插件兼容、过载恢复、Windows 截断恢复等实际问题，另有 [docs_zh-CN](https://github.com/sickn33/agentic-awesome-skills/tree/main/docs_zh-CN) 中文文档。

## 常见问题

**免费吗？** 技能本体是 Markdown 文档，各自带许可证（MIT 居多，attribution ledger 逐条可查）。但相当一部分技能会驱动你调用外部服务——有的需要 API key，README 里明确标注 paid 的也不少。装技能免费，跑技能的成本取决于它调什么。

**和 awesome-claude-skills 这类清单的差别？** AAS 官方有一篇[对比文档](https://github.com/sickn33/agentic-awesome-skills/blob/main/docs/users/agentic-awesome-skills-vs-awesome-claude-skills.md)。差别可以归到三点：可安装（npx 直达各 host 目录）、机器可读（schema 化的索引给集成方用）、有 Core 这层校验与计划流程。纯清单的浏览体验更轻，AAS 的分发设施更重。

**结构校验通过就安全吗？** 不是。官方文档反复强调：结构与身份合法不证明语义匹配、兼容性、设置正确或运行安全。技能正文按不可信内容处理——这层判断留给使用者和使用者的 agent。

**中文资料？** 仓库自带 [docs_zh-CN](https://github.com/sickn33/agentic-awesome-skills/tree/main/docs_zh-CN) 目录，核心用户文档有官方中文版；托管目录 aaskills.tech 界面是英文的。

## 资料口径说明

- 本文数据快照为 2026-09-29/30：仓库元数据、贡献者、release 列表来自 GitHub API；技能数、分类与 risk 分布来自对 v18.9.0 `skills_index.json`（2,488 条）的本地统计；历史规模数据取自各版本 README 的 registry-sync 注释与 CHANGELOG。
- 仓库曾用名 Antigravity Awesome Skills（2026-01 至 2026-07），旧地址 301 重定向；本文 frontmatter 的 slug 沿用首发时的旧名，正文一律使用现名。
- 命令均摘自 v18.9.0 README 与 docs/users/ 指南原文；执行前请以当时的最新文档为准。
- 本文首发于 2026-04-12，当时仓库处于 v9.x、约 1,400 个技能的阶段；2026-09-30 按当前状态全文重写。
