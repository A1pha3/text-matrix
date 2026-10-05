---
title: "Agent Skills 的最小可学样本：一门两小时课程和它背后的三个仓库"
slug: "datawhale-agent-skills-with-anthropic-guide"
github_repo: "https-deeplearning-ai/sc-agent-skills-files"
source_key: "gh:https-deeplearning-ai/sc-agent-skills-files"
description: "解读 DeepLearning.AI × Anthropic 的 agent-skills-with-anthropic 课程与 Datawhale 中文版：一条营销数据主线贯穿十个课时，对照课程文件仓库、中文翻译仓库和官方 skills 参考实现，看清 Skill 的渐进式披露机制与组合用法。"
date: "2026-04-10T21:15:00+08:00"
lastmod: "2026-10-05T00:00:00+08:00"
categories: ["技术笔记"]
tags: ["AI Agent", "Skills", "Claude", "MCP", "Datawhale"]
---

# Agent Skills 的最小可学样本：一门两小时课程和它背后的三个仓库

Agent Skills 这个概念本身一小时就能讲完：一个文件夹、一份 `SKILL.md`、三层按需加载。真正值得花时间的是课程之外的东西——官方把整套课程材料（包括每个 Skill 的真实文件）放在 [https-deeplearning-ai/sc-agent-skills-files](https://github.com/https-deeplearning-ai/sc-agent-skills-files) 里，你可以直接翻看"一个教出来生产可用的 Skill 长什么样"，再把 [anthropics/skills](https://github.com/anthropics/skills) 当参考实现对照。这门课（DeepLearning.AI × Anthropic，Elie Schoppik 主讲，2026 年 1 月 28 日更新，总长约 2 小时 19 分钟）用一条"营销活动分析"主线把 Skill 从本地 CSV 一路讲到 BigQuery、Claude Code、API 和 Agent SDK，比读规范文档更能建立手感。Datawhale 社区在 2026 年 2 月起组织了中文翻译与知识整理（[datawhalechina/agent-skills-with-anthropic](https://github.com/datawhalechina/agent-skills-with-anthropic)），本文即以中文版为线索、以三个仓库为对照。

## 三个仓库，三种角色

看这门课之前先分清三个仓库各自承担什么，混在一起容易把教学示意当成生产实现：

| 仓库 | 角色 | 当前状态（2026-10-05） |
|------|------|----------------------|
| [https-deeplearning-ai/sc-agent-skills-files](https://github.com/https-deeplearning-ai/sc-agent-skills-files) | 课程配套材料：各课时的 Skill 文件、提示词、输出样例 | 1,406★/610 forks；按 L1–L7 课时组织，2026-06-08 后停更 |
| [datawhalechina/agent-skills-with-anthropic](https://github.com/datawhalechina/agent-skills-with-anthropic) | 中文翻译 + 知识点梳理 + 示例代码解读 | 1,532★/200 forks；十章各配负责人与核查人 |
| [anthropics/skills](https://github.com/anthropics/skills) | Anthropic 官方参考实现与开放规范 | 179,655★；skills/ 目录 19 个 Skill + spec/ 规范 + template/ 模板 |

一个容易踩的坑：课程文件仓库直到 2026 年 6 月 8 日才补上 README，此前只有目录本身；而 Datawhale 中文版的"知识点梳理"部分是社区自编内容，并非官方材料的直译。下文会标出这类落差。

## 课程教什么：三层加载与两个特性

### 渐进式披露

Skills 的全部机制建立在一个观察上：你可能同时装着几十上百个 Skill，但单个任务只需要其中一两个。如果全部塞进上下文，窗口早就爆了。所以 [Agent Skills 规范](https://agentskills.io)把加载拆成三层：

| 层 | 何时加载 | 开销 |
|----|---------|------|
| 元数据（YAML frontmatter 的 `name` + `description`） | 启动时，所有 Skill | 每个 Skill 约 100 tokens |
| 指令（`SKILL.md` 正文） | 触发时 | 官方建议控制在 5,000 tokens 内、500 行内 |
| 资源（`scripts/`、`references/`、`assets/` 下的文件） | 按需 | 只有真正用到才读 |

代价是触发质量直接取决于 `description` 写得好不好——描述含糊，该触发的任务触不到；规范因此给 `description` 设了 1,024 字符上限，并要求说清"做什么、何时用"。`name` 也有约束：最长 64 字符，只能小写字母、数字和连字符，且须与目录名一致。写完可以用官方的 `skills-ref validate` 命令做格式校验。

### 可移植与可组合

课程材料里 Skills 的两个关键特性是 **Portable** 和 **Composable**：

- **可移植**：Agent Skills 已于 2025 年 12 月发布为开放标准（agentskills.io，Anthropic 首次发布 Skills 是 2025 年 10 月 16 日）。同一个文件夹可以在 Claude Code、Claude.ai、Claude API 和 Agent SDK 里无修改使用，其他兼容该标准的智能体产品也能加载。
- **可组合**：一个复杂工作流可以拆成几个 Skill 叠加——课程给的例子是"公司品牌 Skill 提供字体颜色规范 + PowerPoint Skill 负责生成幻灯片 + BigQuery Skill 提供营销数据表结构 + 营销分析 Skill 做计算"，四者各管一段。

没有 Skills 的痛点课程也讲得直白：每次都要重新描述一遍要求、重新打包参考资料、靠人肉保证产出一致。Skill 把这三件事变成写一次、反复用。

## Skills 与 Tools、MCP、子代理的分工

这是课程第 4 课的内容，也是理解 Skills 定位的关键一节。官方阅读材料的原话是：**MCP provides access, Skills provide expertise**——MCP 负责把智能体连到外部系统和数据，Skills 负责教智能体拿到数据之后怎么处理。

| 对比 | 一方 | 另一方 |
|------|------|--------|
| Skills vs MCP | MCP 连接外部数据库、API、服务 | Skills 定义处理这些数据的工作流 |
| Skills vs Tools | 工具定义（名称、参数）常驻上下文窗口 | Skills 按需动态加载，可把脚本包装成"按需工具" |
| Skills vs 子代理（Subagents） | 子代理拥有隔离的上下文和独立权限，可并行 | Skills 提供知识，主代理和子代理都能用 |

Datawhale 第 4 章给了一个好记的类比：Tools 是锤子、锯子和钉子，Skills 是"如何建造一个书架"——原子能力与组合方法的关系。

课程材料末尾用"客户洞察分析器"把三者拼在一起，组件只有三个：

- **一个 Skill**：指导如何对客户反馈分类、如何汇总结论；
- **一个 MCP Server**：Google Drive MCP，读取一个装有客户访谈记录和问卷回答的 Drive 文件夹；
- **两个子代理**：Interview Analyzer 处理访谈记录，Survey Analyzer 处理问卷数据，相互独立、可并行。

这个案例在材料里只是一张表，但它说明了架构思路：数据接入交给 MCP，方法论写进 Skill，执行隔离交给子代理，主代理只做拆解与汇总。课程第 9 课把这个思路推进了一步——Agent SDK 版的研究型智能体（L7 目录）配了 `docs_researcher`、`repo_analyzer`、`web_researcher` 三个子代理和一个 `learning-a-tool` 技能，主代理的提示词明确规定"有匹配的 Skill 就必须照着执行"，并把每类信息源映射给对应子代理。

## 一条主线的演进：营销分析 Skill

课程最有教学价值的部分，是同一个"分析营销活动" Skill 在不同课时里的形态变化。文件都在课程仓库里，可以直接对照。

**L1：最小形态。** 一个文件夹、一个 `SKILL.md`、一份参考规则，没有脚本：

```
analyzing-marketing-campaign/
├── SKILL.md
└── references/
    └── budget_reallocation_rules.md
```

`SKILL.md` 的 frontmatter 只有两个字段：

```yaml
---
name: analyzing-marketing-campaign
description: Analyze weekly marketing campaign performance data across channels. Use when analyzing multi-channel digital marketing data to calculate funnel metrics (CTR, CVR) and compare to benchmarks, compute cost and revenue efficiency metrics (ROAS, CPA, Net Profit), or get budget reallocation recommendations based on performance rules.
---
```

注意 `description` 的写法：先说做什么（按渠道分析周度营销数据），再用 "Use when..." 列出触发场景（算漏斗指标、算效率指标、要预算调整建议）。正文则写清输入要求（CSV 各列含义）、数据质量检查、漏斗与效率指标的计算口径，甚至连基准值都内置了——Facebook 广告 CTR 按 2.5%、Google 广告按 5.0%、邮件按 15.0%，用户没给基准时按这套默认值比。预算再分配的完整决策规则单独放在 `references/budget_reallocation_rules.md`，只有用户问到时才读。

这里要点名一处常见的误导：Datawhale 中文版第 2 章把 `SKILL.md` 示意成了带 `inputs:`/`outputs:` 字段的中文版，又画了一棵带 `scripts/process_data.py`、`recalc.py` 的 `excel-skill/` 目录树。前者是社区自编的教学示意（官方 frontmatter 没有 inputs/outputs 字段），后者是一个假想的通用 Excel Skill 结构，与课程仓库里真实的 `analyzing-marketing-campaign` 无关——真实结构就是上面那两样。读中文版时留意"示例"与"官方文件"的边界。

**L3：换数据源。** 改进版把本地 CSV 换成了 BigQuery：Skill 正文改为指导模型用 `bigquery:execute_sql` 工具查询指定数据集，附上表结构和查询规则（必须按日期范围过滤、禁止全表扫描、日期有歧义先反问用户）。Skill 本身没变复杂，变的是它调度的工具。这也顺手演示了 Skill 的一个设计原则：方法论写在 Skill 里，易变的东西（数据在哪、怎么连）也写成指令，而不是脚本。

**L4–L5：自己写。** 从第 6 课开始动手写自定义 Skill，仓库里给了两个完整成品：`generating-practice-questions`（从讲义出题，带 `assets/` 和 `references/`）和 `analyzing-time-series`（时序分析，带 `scripts/` 目录，`visualize.py`、`diagnose.py`、`ts_utils.py` 用 pandas 做诊断、可视化和工具函数）。这两个目录就是"什么该进 scripts、什么该进 references"的活例。

**L6：在真实项目里用。** 这一课的场景是给一个 Python CLI 项目加功能，`.claude/skills/` 下放了三个项目级 Skill（加命令、审查命令、生成测试），`.claude/agents/` 下配了两个子代理（code-reviewer、test-generator-runner）。Skills 从"个人技巧"变成了随仓库分发的团队资产。

Excel 处理相关的实践建议（工具选型 pandas 或 openpyxl、公式重算、错误报告）出自中文版第 2 章的梳理。其中"openpyxl 只写公式字符串、需另跑重算"这一条与官方 `xlsx` Skill 的做法吻合——`anthropics/skills` 的 `skills/xlsx/scripts/` 里确实有一个 `recalc.py` 专门干这件事。

## 在 Claude Code 里装和用

Claude Code 是 Skills 最日常的运行环境，这部分课程第 8 课讲，中文版第 8 章整理。几个高频问题按官方文档核对如下。

**装在哪。** Skill 文件夹放对位置就会被发现：个人级 `~/.claude/skills/`（本机所有项目可用），项目级 `.claude/skills/`（随 Git 仓库分发给团队），企业级托管目录，另有子目录级、`--add-dir` 临时目录和插件四种来源。同名冲突时官方文档的优先序是 **企业 > 个人 > 项目**——个人目录会覆盖项目目录，这点和很多人"项目配置优先"的直觉相反。插件 Skill 则以 `/插件名:技能名` 的命名空间共存，不参与竞争。

**从官方仓库装。** 把 anthropics/skills 注册为插件市场再安装（在 Claude Code 会话里执行）：

```
/plugin marketplace add anthropics/skills
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills
```

`document-skills` 打包四个文档 Skill，`example-skills` 打包其余示例。不想走插件也可以手动克隆后复制单个目录（例如 `cp -r skills/skills/xlsx ~/.claude/skills/`）。

**frontmatter 能配什么。** `name` 和 `description` 之外，Claude Code 支持一批可选字段（字段名一律 kebab-case）：

| 字段 | 作用 |
|------|------|
| `disable-model-invocation` | 设 `true` 禁止模型自动加载，只许用户 `/name` 手动调用 |
| `user-invocable` | 设 `false` 反向限制：只有模型能用，用户菜单里隐藏 |
| `allowed-tools` | 本轮免批准工具清单（空格或逗号分隔），不是"限制只能用这些工具" |
| `disallowed-tools` | Skill 生效期间从工具池移除某些工具 |
| `model` / `effort` | 覆盖本轮使用的模型与推理力度（`effort` 取值 `low` 到 `max`） |
| `context: fork` + `agent` | 把 Skill 放进隔离子代理执行，可配后台运行 |
| `argument-hint` / `arguments` | 斜杠命令的参数提示与命名参数替换 |

常见误用有两个：把 `allowed-tools` 当白名单（它其实是"免批准"，收回权限要用 `disallowed-tools`）；写字段名用驼峰（`disallowedTools` 会被静默忽略，Claude Code 对不认识的字段不报错）。

**怎么判断触发失败。** 大多数"Skill 不触发"的原因是 `description` 写得不够具体——Claude 只看元数据决定是否加载。排查顺序：先看描述里有没有覆盖目标任务的关键词，再确认目录位置，最后在对话里直接点名 Skill 名称强制触发。

## 对照官方参考实现

课程之外，[anthropics/skills](https://github.com/anthropics/skills) 是理解"生产级 Skill 长什么样"的最佳材料。发文时（2026 年 4 月）仓库有 17 个 Skill，到 10 月已增至 19 个（新增 `academy-guide`，推荐 Claude Academy 的课程教程；`discernment-nudge`，在给出可被采纳的建议或草稿前触发一轮审慎检查）。阅读时注意官方的分类口径：

**文档四件套**（`docx`、`pptx`、`xlsx`、`pdf`）：README 明说这些是 Claude.ai"创建文档"能力背后的实现，以 **source-available** 形式公开——可参考学习，但不是开源许可。它们的共同特征是脚本密集：`xlsx` 的脚本处理公式重算，`pdf` 的脚本处理表单字段提取与填写，逻辑都在 Python 里，`SKILL.md` 只负责指挥。

**示例类**（其余，Apache 2.0 开源）：覆盖创意（`algorithmic-art`、`canvas-design`、`theme-factory`）、开发（`mcp-builder`、`webapp-testing`、`web-artifacts-builder`、`claude-api`、`skill-creator`）、企业协作（`brand-guidelines`、`internal-comms`、`doc-coauthoring`）等方向。其中 `skill-creator` 是"元 Skill"——引导你走完创建新 Skill 的流程；`brand-guidelines` 正好对应课程里"品牌 Skill"的组合角色。

仓库还带 `spec/`（开放规范文本）和 `template/`（空白 Skill 模板），想从规范入手的可以直接读这两处。Claude.ai 付费用户无需安装即可使用其中的示例 Skill，API 侧走 Skills API。

## 社区生态一瞥

这门课发布前后，Skills 生态已经起来了。几个可对照的坐标（读数截至 2026-10-05）：

- **obra/superpowers**（约 29.5 万★）：把 TDD、YAGNI 等工程方法论做成一整套 Skill 与命令，是"用 Skill 固化开发流程"路线的代表。
- **nextlevelbuilder/ui-ux-pro-max-skill**（约 13.3 万★）：面向 UI/UX 设计的单一 Skill，内置可检索的设计风格、配色与字体配对数据（当前 README 标注 79 种 UI 风格、192 条推理规则），有官方中文 README。
- **numman-ali/openskills**（约 1.1 万★）：自称"SKILL.md 的通用安装器"，`npx openskills install <repo>` 从任意仓库装 Skill，默认装到项目的 `.claude/skills/`，`--global` 装到 `~/.claude/skills/`，主打跨智能体工具通用。

第三方 Skill 的脚本安全与安装任何第三方代码等价：装之前读一遍 `SKILL.md` 和脚本源码，留意网络请求与文件写入。

## 该怎么用这条学习路径

**适合谁**：已经用过 Claude Code 或 API、想让自己的智能体稳定复现某类工作流的开发者。课程不要求机器学习背景，两小时出头可以过完。

**建议顺序**：先读 agentskills.io 规范建立三层模型（半小时）→ 过一遍课程或 Datawhale 中文版（第 1、2、4 课是概念主干）→ 打开课程文件仓库对照 L1 和 L3 的营销 Skill，理解"指令替代脚本"与"换数据源不换方法论"→ 装官方 `skill-creator`，从自己工作里挑一个重复流程写第一个 Skill → 需要深入再翻 anthropics/skills 里同领域的参考实现。

**不必急着学的情况**：如果你的场景只是一次性任务，直接写 Prompt 更省事；需要实时外部数据或复杂鉴权时，先考虑 MCP Server 而不是把所有东西塞进 Skill——课程第 4 课的分工表就是为这个判断准备的。

Agent Skills 的标准本身很薄，薄到规范全文一个下午能读完。这门课和它的三个仓库真正的价值，是展示了薄标准之上如何长出结构：一个 Skill 文件夹怎么长成脚本与参考资料的组合，几个 Skill 怎么叠成完整工作流，以及一套方法怎么从教学案例走到生产实现。标准会演进（半年就从 17 个官方 Skill 涨到 19 个），但"渐进披露 + 指令优先 + 按需加载"这条骨架目前没有变过的迹象。

---

*本文基于 [Datawhale/agent-skills-with-anthropic](https://github.com/datawhalechina/agent-skills-with-anthropic) 项目与 [https-deeplearning-ai/sc-agent-skills-files](https://github.com/https-deeplearning-ai/sc-agent-skills-files) 课程材料撰写，原始课程来自 DeepLearning.AI × Anthropic（[agent-skills-with-anthropic](https://www.deeplearning.ai/short-courses/agent-skills-with-anthropic/)）。仓库读数与官方文档口径核对日期：2026-10-05。*
