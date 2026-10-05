---
title: "VoltAgent/awesome-agent-skills 解读：66 个团队把官方 Agent Skills 集中到一个索引"
slug: voltagent-awesome-agent-skills-17k
github_repo: "VoltAgent/awesome-agent-skills"
source_key: "gh:VoltAgent/awesome-agent-skills"
date: "2026-04-22T16:10:00+08:00"
lastmod: "2026-10-01T12:00:00+08:00"
summary: "基于 README、CONTRIBUTING 与 officialskills.sh 的交叉核实，本文拆解这个 Agent Skills 索引仓库的三个数量口径、66 个团队分组、跨工具 skills 路径约定、收录门槛与安全边界，并给出装 skill 前的完整审查流程。"
description: "深度解读 VoltAgent/awesome-agent-skills：它不是统一安装器，而是收录 66 个开发团队官方技能与社区技能的纯索引仓库。本文覆盖数量口径、兼容路径、收录标准、质量规范、风险边界与引入流程，帮助开发者更准确地使用 Agent Skills 生态。"
categories: ["技术笔记"]
tags: ["Agent Skills", "Claude Code", "Codex", "AI Agent", "开源"]
---

# VoltAgent/awesome-agent-skills 解读：66 个团队把官方 Agent Skills 集中到一个索引

Agent Skills 生态现在不缺技能，缺的是判断：哪些技能来自真正用它们干活的工程团队，哪些是批量生成的填充物。VoltAgent/awesome-agent-skills 押的就是这个判断——README 开头第一句话是 "Hand-picked, not AI-slop generated"（人工精选，不是 AI 垃圾批量生成），收录的全部是 Anthropic、OpenAI、Cloudflare、Stripe、Microsoft、Trail of Bits 这些团队实际发布过的技能，加上一批在社区里被真实采用过的技能。

先把定位说死：它是一个纯索引仓库，整个仓库只有 README、LICENSE、CONTRIBUTING 三个文件。每条收录就是一个 Markdown 列表项，链接指回技能各自的原始仓库，仓库本身不托管任何技能代码，也不提供安装器。配套的浏览站 officialskills.sh 按同样的口径组织这些条目。收录动作是社区驱动的大门——截至 2026-09-29，PR 编号已经排到 #1101，README 自称 "The most contributed Agent Skills repository"。

## 三个数字，三种口径

看这个仓库最容易犯的错，是拿一个数字当全部规模。实际上有三个口径，先分清：

| 口径 | 数值（2026-10-01） | 含义 |
| ---- | ---- | ---- |
| README badge | 1497+ | 仓库宣传的总收录规模 |
| README 可数条目 | 1123 条 | 逐条可点开的收录行：官方分组 859 条 + 社区 264 条 |
| officialskills.sh 首页 | 634 个 | 首页 HTML 里可解析到的技能详情链接，只是浏览面 |

badge 和逐条可数条目对不上，差额主要出在集合型收录——比如一条 `gooseworks-ai/goose-skills` 写着 "125 growth and GTM skills"，一条收录背后是一整个技能仓库。badge 怎么统计的没有公开说明，引用时建议注明口径。这三个数字都会漂：文章初版写作时（2026-04-22），badge 还是 1100+、首页可见约 581 条、星标约 1.74 万；五个月过去，badge 涨到 1497+，星标 35,080、fork 3,764，翻了一倍。仓库 2025-10-28 创建，到现在 11 个月，增长曲线相当陡。

商业信号也出现了。README 首屏挂着三个赞助商（TestMu AI、Crawlbase、SerpApi）和一个产品推广位。一个索引仓库能卖出赞助位，说明流量已经起来了——它是很多人找 skill 的第一站。

## 收录地图：66 个团队分组 + 7 个社区子类

README 用 73 个折叠分组组织内容：66 个具名来源分组（几乎都是开发团队官方发布），加 Community 下的 7 个主题子类（Vector Databases、Marketing、Productivity and Collaboration、Development and Testing、Context Engineering、Specialized Domains、n8n Automation）。先看最大的几个官方分组：

| 来源分组 | 条目数 | 方向 |
| ---- | ---- | ---- |
| Microsoft | 133 | Azure SDK 全家桶、Copilot SDK、Agent Framework、Foundry |
| OpenAI | 42 | 浏览器自动化（playwright）、Figma 全套、文档、部署、安全审查 |
| Sentry | 28 | 各语言 SDK 接入与线上问题修复 |
| TestMu AI / Paweł Huryn / Dean Peters | 48 / 65 / 46 | 测试、产品管理、产品经理技能 |
| Trail of Bits | 21 | 安全审计：差异审查、变体分析、规范符合性检查 |
| Anthropic（Official Claude Skills） | 17 | docx/pptx/xlsx/pdf、MCP 构建、前端设计、Web 应用测试 |
| Cloudflare | 9 | Workers、Agents SDK、Wrangler、Web 性能 |

半年间分组扩张明显：4 月时官方分组是 37 个，现在 66 个，Supabase、Hugging Face、DuckDB、MongoDB、Redis、NVIDIA、Google Cloud、Red Hat、Binance、Coinbase、Notion、Firebase、Flutter、GSAP 都是新添的具名分组，Garry Tan（gstack 分组）和 Addy Osmani（Web Quality）则以个人名义入驻。上一版解读里抽查过的条目——`anthropics/mcp-builder`、`openai/playwright`、`cloudflare/wrangler`、`trailofbits/differential-review`、`getsentry/sentry-sdk-setup`、`stripe/upgrade-stripe`——全部还在，没有死链。

这个分组结构本身就是一份"谁在认真做 Agent Skills"的生态名单。判断一家厂商对 agent 生态的投入程度，看它在这里有没有具名分组、条目有多少，比看营销博客可靠。

## 兼容路径：趋同的是目录，不是行为

README 给出 9 个工具的 skills 路径约定，这是全文最实用的一张表：

| 工具 | 项目级路径 | 全局路径 |
| ---- | ---- | ---- |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex | `.agents/skills/` | `~/.agents/skills/` |
| Antigravity | `.agents/skills/` | `~/.gemini/config/skills/` |
| Cursor | `.cursor/skills/` | `~/.cursor/skills/` |
| Gemini CLI | `.gemini/skills/` | `~/.gemini/skills/` |
| GitHub Copilot | `.github/skills/` | `~/.copilot/skills/` |
| OpenCode | `.opencode/skills/` | `~/.config/opencode/skills/` |
| Windsurf | `.windsurf/skills/` | `~/.codeium/windsurf/skills/` |

两个细节藏在表里。第一，Codex 和 Google 的 Antigravity 共用同一个项目级路径 `.agents/skills/`，一套技能可以同时喂给两个工具。第二，Antigravity 这一行本身在半年内就变过：4 月的 README 写的是 `.agent/skills/` 和 `~/.gemini/antigravity/skills/`，现在已经换成 `.agents/skills/` 和 `~/.gemini/config/skills/`。目录约定还在收敛期，照抄任何一张路径表之前都该对照当时的 README。

"兼容"这个词也别读重了。路径趋同只解决"文件放哪"，不解决"能不能跑"。一个 skill 往往还隐含三层前提：目标工具支持对应的技能发现机制；环境里装了它依赖的 CLI、MCP server 或配好了 API key；作者是按某个 agent 的工具能力和行为习惯写的说明。同一个 skill 在 Claude Code 里表现良好，换到另一个 agent 上可能静默降级。

## 收录门槛与质量标准

这个仓库对"收什么"有明确态度，写在 CONTRIBUTING.md 里：

- 只收链接，技能住在自己的仓库里，收录前先验证链接有效。
- 描述必须 10 个词以内，不许写长段落。
- 必须有真实社区使用——原话是"刚创建 3 小时的技能请不要提交"，品牌新技能等它被采用后再来。

README 里还有一个 Skill Quality Standards 板块，给出四条质量判据：description 用第三人称写、写明"做什么"和"何时用"、带可匹配的关键词（"PostgreSQL migration"而不是"database stuff"）；元数据控制在约 100 token 以内、正文不超过 500 行、大资源按需加载（渐进式披露）；不硬编码机器特定路径；只声明技能真正需要的工具，避免 `"tools": ["*"]` 这种全量授权。

这四条其实是 Anthropic 当初定义 Agent Skills 规范时留下的设计原则，现在被一个第三方索引仓库拿来当收录标尺，反过来约束提交者。写自己的 skill 时直接照着这四条自查，比读规范文档快。

## 风险：curated 不是 audited

README 的 Security Notice 值得逐句读：

> Skills in this list are curated, not audited.（本列表中的技能经过筛选，但未经审计。）

展开说有三层：收录后技能可能被原作者随时更新、修改甚至替换，索引不锁版本；技能可能包含 prompt injection、tool poisoning、隐藏恶意载荷或不安全的数据处理模式；安装前自己审代码，风险自担。License 部分重复了同样的立场——VoltAgent 明确声明不背书、不保证安全性和正确性。这也符合仓库架构：既然只收链接、不托管代码，它对每条收录的内容自然没有任何技术约束力。

Notice 里还给了两个扫描工具：Snyk 的 agent-scan 和 Gen Digital 的 Agent Trust Hub。给团队搭技能审查流程的话，这两个可以进工具箱，但要注意它们同样年轻，别把扫描结果当安全结论。

## 任务流：引入一个 skill 的完整路径

拿 `stripe/upgrade-stripe`（升级 Stripe SDK 与 API 版本）走一遍完整流程：

1. 在 README 的 Stripe 分组或 officialskills.sh 找到条目，顺着链接进入原始仓库——注意是 Stripe 团队的仓库，不是 awesome-agent-skills 本身。
2. 读 SKILL.md 和 README，确认四件事：维护者是谁、声明了哪些工具依赖、会碰到什么权限（这条会调 Stripe API，涉及真实账户）、许可证是什么。
3. 对照上面的路径表，把 skill 放进目标工具的 skills 目录，比如 Claude Code 就是项目里的 `.claude/skills/`。
4. 找一个低风险任务试跑——用测试项目而不是生产账户，观察它是否调用了声明之外的工具。
5. 行为符合预期再进团队工作流，并把试用结论（依赖、权限、效果）记录下来，给下一次评估用。

整个流程里最容易被跳过的是第 2 步和第 4 步，而官方出处恰恰不能替代它们——官方 skill 一样可能触发高权限操作或产生真实账单。

## 选型与治理：窄而深优先

筛 skill 的检查项可以压成一张表：

| 检查项 | 看什么 |
| ---- | ---- |
| 来源 | 官方团队、知名开源项目，还是个人仓库 |
| 目标 agent | 为哪个工具写的，你的工具在不在路径表里 |
| 外部依赖 | 要不要 MCP server、CLI、浏览器环境、API key |
| 权限边界 | 会不会碰 shell、网络、部署、支付、数据库 |
| 维护状态 | 最近提交时间，issue 处理是否活跃 |
| 范围 | 窄而深的单任务技能，还是大而全的 meta-skill |

窄而深的技能通常更稳：目标清楚，agent 不容易跑偏，行为好审查，失效了好定位。`cloudflare/wrangler`、`stripe/upgrade-stripe`、`trailofbits/differential-review` 这类单点技能，一般比"全能开发助手"值得先试。

团队引入比个人使用多一层治理问题：哪些技能允许进默认环境，哪些必须过内部审查，哪些只能在隔离环境跑，哪些要包一层内部 wrapper 限制权限。把 awesome-agent-skills 当收藏夹问题不大，但真要让团队用起来，值得把这四档边界写进工程规范，而不是凭感觉装。

## 结语：发现贬值，判断升值

回到开头的问题。这个仓库最大的价值，不是"1497 个技能随便挑"，而是把 66 个团队的工程经验集中到了一个检索面——Anthropic 教 agent 做文档，Trail of Bits 教 agent 做安全审计，Stripe 教 agent 做 SDK 升级，这些原本散在各家博客和仓库里的知识，第一次有了统一的目录。

对 Agent Skills 生态本身，这里能看到两个趋势：一是技能正在从零散技巧变成厂商正式的知识分发渠道，一家公司发布 skill 的动作越来越像发布 SDK；二是跨工具的路径约定已经出现并在收敛，skill 有潜力成为下一个跨 agent 复用的标准单元。

给两类读者的落地建议：个人开发者，从一个高频任务开始试一个技能，优先选来源清晰、依赖明确、范围可控的，别批量安装；技术负责人，先把上文的审查流程和四档治理边界立起来，再谈规模化引入。发现技能只会越来越容易，稀缺的永远是判断一个技能是否可信、是否适配、是否值得进你的工作流。

## 相关资源

- GitHub 仓库：[VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills)
- 技能索引站：[officialskills.sh](https://officialskills.sh/)
- Claude Code Skills 文档：[Anthropic Claude Code Skills](https://docs.anthropic.com/en/docs/claude-code/skills)
- Codex Skills 文档：[OpenAI Codex Skills](https://developers.openai.com/codex/skills)
- GitHub Copilot Skills 文档：[GitHub Copilot Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
