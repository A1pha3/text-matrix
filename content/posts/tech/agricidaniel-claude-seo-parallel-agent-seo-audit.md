---
title: "Claude SEO：把「SEO 审计」拆成 20 个并行专职 agent，而不是一个长 prompt"
date: "2026-11-20T01:27:19+08:00"
slug: "agricidaniel-claude-seo-parallel-agent-seo-audit"
description: "Claude SEO 是 Claude Code 的 SEO 审计插件，由 29 个子技能与 20 个专职 agent 组成，一次审计最多 17 个 agent 并行跑站点。本文拆解其扇出式审计架构、按业务类型自适应检查项、扩展机制与漂移监控，并指出免费方案在覆盖面与数据口径上的边界。"
draft: false
categories: ["技术笔记"]
tags: ["SEO", "AI Agent", "Claude Code", "审计工具", "GEO"]
github_repo: "AgriciDaniel/claude-seo"
source_key: "gh:AgriciDaniel/claude-seo"
---

## 核心判断

「给 AI 一个长 prompt，让它帮我做 SEO 审计」和「让 20 个专职 agent 并行跑同一个站点」是两种不同的东西，差别不在覆盖范围，在**冲突消解**。

单 agent 做全站审计的典型失败模式是：它在一个上下文里同时处理抓取、渲染、性能测量、schema 校验和内容评估，最后输出一份几千条的告警列表 —— 每条单看都对，合在一起无法执行。因为在单一上下文里，所有发现共享同一份注意力，没有优先级。

Claude SEO 的做法是**扇出**。一次 `/seo audit` 最多 17 个专职 agent 同时跑站点各自的维度，每个 agent 只管一件事：技术 SEO、内容质量、结构化数据、性能、AI 搜索、本地、电商、国际。汇总层再把它们的输出**打分排序**成一份行动清单。

这个转换的关键在最后一环 —— README 写得很清楚：「你得到的是一份计划，不是一堆警告」，每条建议都说清楚**依据是什么、依赖什么、你怎么知道它生效了**。

最后一条是这个项目比同类工具诚实的地方：多数 SEO 工具给你一个分数就结束了，「你怎么验证这个修复有效」是用户自己要去想的额外工作。

需要先说清立场：**它跑在你自己的机器上**（README 对比表里「你的数据留在你这里：Yes」对软件方案是 No），产出是 Markdown / PDF / JSON 文件，没有按站点计费、没有用量限制、没有追踪。代价是它只在 Claude Code 里跑。

截至 2026 年 11 月 20 日，这个仓库有 30864 stars、3844 forks，Python 为主，MIT 许可，2026 年 2 月创建，11 月 19 日仍在更新。

## 系统地图

```
/seo audit <url>
      │
      ├─ ① 学习站点类型（SaaS / 本地 / 电商 / 出版 / 代理）→ 调整检查项
      │
      ├─ ② 扇出：最多 17 个专职 agent 并行
      │      technical · content · schema · performance · visual
      │      geo · agentic · local · maps · google · backlinks
      │      ecommerce · cluster · sxo · drift · content-brief · …
      │
      └─ ③ 汇总：打分 → 排序 → 行动清单（每条带依据 / 依赖 / 验证方式）
                └→ Markdown 报告 · `/seo google report` → PDF
```

第一步「学习你的站点」值得单独说。README 说它会检测业务类型（SaaS、本地、电商、出版、代理）并**相应调整检查项**。这是很朴素的思路，但很有效：给本地餐厅做电商审查、或给 SaaS 做 Google Business Profile 审查，都是噪音。

## 并行专职 agent

仓库的 `agents/` 目录里是 20 个 agent 定义文件，每个是一份 Markdown。README 给了完整的角色、模型和命令对照表：

| Agent | 角色 | 模型 | 命令 |
|---|---|---|---|
| `seo-technical` | 技术 SEO 负责人 | Sonnet | `/seo technical` |
| `seo-content` | 内容编辑 | Opus | `/seo content` |
| `seo-schema` | 结构化数据工程师 | Sonnet | `/seo schema` |
| `seo-sitemap` | 站点地图架构师 | Sonnet | `/seo sitemap` |
| `seo-performance` | 性能工程师 | Sonnet | `/seo audit` |
| `seo-visual` | 视觉质检 | Sonnet | `/seo audit` |
| `seo-geo` | AI 搜索分析师 | Opus | `/seo geo` |
| `seo-agentic` | Agent 就绪度分析师 | Sonnet | `/seo agentic` |
| `seo-local` | 本地 SEO 专家 | Sonnet | `/seo local` |
| `seo-maps` | 地图分析师 | Sonnet | `/seo maps` |
| `seo-google` | Google 数据分析师 | Sonnet | `/seo google` |
| `seo-backlinks` | 链接分析师 | Sonnet | `/seo backlinks` |

其余是扩展类：`seo-dataforseo`、`seo-posthog`、`seo-image-gen`、`seo-cluster`、`seo-flow`、`seo-drift`、`seo-ecommerce`、`seo-sxo` 等。

**模型分配的规律很清楚**：需要主观判断和写作的任务用 Opus（`seo-content`、`seo-geo`），需要确定性的检查用 Sonnet。这个分配本身就是一条可借鉴的经验 —— 把最强的模型留给需要判断力的环节，而不是无差别地全用最强模型。

子技能有 29 个（`seo-agentic`、`seo-audit`、`seo-backlinks`、`seo-bing`、`seo-cluster`、`seo-competitor-pages`、`seo-content`、`seo-content-brief`、`seo-dataforseo`、`seo-drift`、`seo-ecommerce`、`seo-flow`、`seo-geo`、`seo-google`、`seo-hreflang`、`seo-image-gen`、`seo-images`、`seo-local`、`seo-maps`、`seo-page`、`seo-plan`、`seo-posthog`、`seo-programmatic`、`seo-schema`、`seo-shopify`、`seo-sitemap`、`seo-sxo`、`seo-technical` 等）。

## 30 条命令分六组

| 组 | 命令数 | 内容 |
|---|---|---|
| 审计与规划 | 5 | `/seo setup`（建隔离 Python 运行时和 Chromium）、`/seo doctor`（只检查不改动）、`/seo audit`（并行 agent 全站审计）、`/seo page`（单页深析）、`/seo plan`（按 saas/local/ecommerce/publisher/agency 规划） |
| 技术 SEO | 7 | `technical`（9 个类别）、`sitemap`（分析或生成 XML）、`images`、`hreflang`（多语言审计与生成）、`programmatic`（程序化 SEO 分析与规划）、`google`（GSC / PageSpeed / CrUX / Indexing / GA4 / PDF 报告）、`drift`（SEO 漂移监控，SQLite 快照） |
| 内容与 E-E-A-T | 6 | `content`（E-E-A-T 与内容质量）、`content-brief`（目标关键词、大纲、内链）、`cluster`（基于 SERP 的语义聚类）、`sxo`（页面类型、用户故事、角色画像）、`flow`（FLOW 框架提示，CC BY 4.0）、`competitor-pages` |
| Schema 与 AI 搜索 | 3 | `schema`（检测、校验、生成 Schema.org 标记）、`geo`（AI Overviews 与生成式引擎优化）、`agentic`（Lighthouse Agentic Browsing X/N、AI agent 可访问性、llms.txt、Markdown、WebMCP） |
| 本地、链接、电商 | 4 | `local`（GBP、引用、评论、地图包）、`maps`（geo-grid、GBP 审计、评论、竞品）、`backlinks`（Moz、Bing、Common Crawl）、`ecommerce` |
| 扩展 | 5 | `image-gen`、`seranking`（AI 份额声量）、`profound`（LLM 引用追踪）、`bing`（Bing Webmaster + IndexNow）、`unlighthouse`（本地多页 Lighthouse） |

`/seo setup` 这个设计值得留意：**它建一个隔离的 Python 运行时和 Chromium**。`/seo doctor` 明确「检查运行时就绪状态但不改系统」。对一个要往你机器上装 Chromium 和 Python 依赖的工具来说，先给一个只读的体检命令是对的。

## 扩展机制：留缺口，不硬编

`extensions/` 目录里有 11 个可选扩展：

```
ahrefs · banana · bing-webmaster · dataforseo · firecrawl
matomo · posthog · profound · seranking · shopify · unlighthouse
```

README 的「Extensions」一节只重点介绍了其中 6 个（Banana、SE Ranking、Profound、Bing Webmaster、Unlighthouse、Shopify Crawler Access），其余按「可选插件」定位存在。

**依赖是单向的**：核心功能不调用它们，是它们接入核心。这是正确的方向 —— 核心不该被任何一个付费服务的 SDK 绑架。

README 说得很直接：有些扩展连到付费服务，**你自己的账号自己付费**，但**没有它们一切照常工作**。

另外注意仓库里还有一份 `docs/COMMUNITY-INTEGRATIONS.md`：那里面列的是**别人自己维护的集成**，README 明确说「它们不是 Claude SEO 的一部分，也不被它审计」。

需要付费的只有一类：真实的场外数据（Ahrefs 反链、Semrush、数据forSEO 排名、SERP 数据）。免费的部分是页面级检查、渲染、schema 校验、性能测量。

### AI 搜索这一块

`/seo geo` 和 `/seo agentic` 是相对新的部分，也是这个项目跟传统 SEO 工具拉开差距的地方。

README 给的思路是：Google 说优化 AI 搜索**仍然是 SEO**，所以 Claude SEO 从 AI 答案依赖的基础开始 —— 被索引、快、清晰。然后 `/seo geo` 评分你的页面**有多容易被引用**，检查 AI 爬虫能不能到达，以及品牌在 Wikipedia、Reddit、YouTube、LinkedIn 上的存在。`/seo agentic` 检查 AI agent 能多好地使用你的站点。

后者涉及一批新指标：Lighthouse Agentic Browsing 的 X/N 得分、AI agent 可访问性、`llms.txt`、Markdown 可读性、WebMCP。

`/seo agentic` 背后的判断值得记住：**站点是给人和爬虫读的，也越来越多是给 AI agent 用的**。一个 agent 要用你的站点，得能以机器友好的方式拿到内容 —— 这是传统 SEO 检查表里没有的一类问题。

## 漂移监控

`/seo drift baseline | compare | history <url>` 是我在这 29 个子技能里觉得最有价值的一个，因为它解决的是**SEO 工作最大的现实问题**：SEO 是一次性项目，不是。

它用 SQLite 存快照，能做三件事：`baseline` 建基线、`compare` 对比当前状态、`history` 看历史趋势。

这解决的实际困境是：SEO 的修复往往在三个月后被某次发版悄悄回退，而没有人会注意到。没有快照对比，这个回归就永远查不出来。

## 报告长什么样

README 展示了一份 schema 审计报告的开头：

```markdown
# Schema Markup Report: rankenstein.pro/about

| Metric              | Value                                       |
|---------------------|---------------------------------------------|
| JSON-LD Blocks      | 3                                           |
| Schema Types        | Organization, WebSite, SoftwareApplication  |
| Critical Issues     | 2                                           |
| Warnings            | 5                                           |
| Passed Checks       | 18                                          |
| Overall Grade       | B+ (solid foundation, actionable gaps)      |
```

注意 `Overall Grade` 后面那个括注 —— **B+ 配了一句人话解释**，说清楚这个分数意味着什么。这是给人看的，不是给仪表盘看的。

报告存为 Markdown，`/seo google report` 能转成排版好的 PDF。

## 边界与需要留意的地方

**免费 ≠ 覆盖完整。** 没有付费扩展时，反链数据、真实排名、SERP 历史都拿不到。`/seo backlinks` 在没有 Ahrefs/Semrush 的情况下能做的有限。README 的对比表里「Covers AI search」一栏对「SEO audit software」写的是「Often months behind」—— 这类断言是项目自述，不是独立测评。

**它不修复问题。** 它产出的是计划和报告，代码修改仍然要人来做（`/seo schema` 能生成 Schema.org 标记，但应用它还是你的事）。

**SEO 效果的归因很弱。** README 提到自家站点 claude-seo.md 首 12 周拿到 10.8K Search Console 点击、移动端 PageSpeed 99 分。这是个可参考的样本，但**单站点、无对照组的结果不能推广**。把它当成「工具作者的一个成功案例」，而不是「使用这个工具能获得的预期收益」。

**它不做付费 API 调用的额度管理。** 扩展接的是你自己的付费账号，跑大批量任务时费用由你承担。

**JavaScript 站点支持靠 headless browser。** README 说 Next.js / React / Vue 站点会自动开 headless 浏览器渲染。这是正确的做法，但意味着审计速度会明显慢于纯静态站点。

**`seo-content` 用 Opus、`seo-geo` 用 Opus，其余用 Sonnet。** 如果你的 Claude Code 套餐配额有限，跑一次全站审计的 token 消耗要认真估算 —— README 自己说一次审计 10 到 15 分钟。

## 采用顺序

1. **先读 `/seo doctor` 的输出**。这个命令只读不改，跑一次确认运行时没问题，比直接开审计省事。
2. **先跑单页**：`/seo page <url>`。快、便宜、输出具体，能让你判断这个工具的检查项是否适合你的站点类型。
3. **再跑全站**：`/seo audit <url>`，但先想清楚配额。这一步会扇出 17 个 agent。
4. **接着建基线**：`/seo drift baseline <url>`。**这一步是长期价值最大的一步**，一定要在第一次修复之前做，否则后面没法量化效果。
5. **需要真实数据再接扩展**。核心功能先用着，别一开始就为 Ahrefs 付费。
6. **每条建议都问一句「我怎么知道它生效了」**。报告里应该已经写了 —— 如果某条没写，那就是这条建议本身还不够可执行。

## 排查：按现象定位

| 现象 | 先查这里 |
|---|---|
| 审计卡住不动 | `/seo doctor`；`/seo setup` 会建隔离的 Python 运行时和 Chromium，第一次没跑过就会卡 |
| SPA 站点被抓成空页 | 它会自动开 headless 浏览器，但需要 Chromium 就绪；先确认 `/seo setup` 跑过 |
| 某些维度结果很薄 | 大概率是没接对应的扩展（反链、排名、SERP 属于付费扩展），不是工具坏了 |
| 想要 PDF | `/seo google report`，不是主审计命令的输出 |
| 修复后想确认生效 | `/seo drift compare <url>`，而不是重跑一次全站审计 |
| 想知道某个 agent 具体做了什么 | `agents/` 目录下 20 个 Markdown，每个对应一个角色的完整定义 |

## 参考

- 仓库：<https://github.com/AgriciDaniel/claude-seo>
- 完整命令参考：<https://github.com/AgriciDaniel/claude-seo/blob/main/docs/COMMANDS.md>
- 作者站点：<https://claude-seo.md>
- Google AI 优化指南（README 称其跟随此文档）：<https://developers.google.com/search/docs/fundamentals/ai-optimization-guide>
