---
title: "WrenAI：让 AI Agent 真正可信任的 GenBI Context Layer"
date: 2026-07-20T03:02:36+08:00
categories: ["技术笔记"]
tags: ["genbi", "text-to-sql", "agent", "context-layer", "rag"]
description: "WrenAI 是 Canner 开源的 GenBI 引擎，核心是在 LLM 和数据仓库之间塞一层 reviewable 的 context layer（MDL + 业务语义），让 Agent 生成的 SQL 和 Dashboard 不是幻觉，而是可治理、可版本化的产物。"
---

# WrenAI：让 AI Agent 真正可信任的 GenBI Context Layer

## 一句话判断

WrenAI 的核心不是"又一个 text-to-SQL"，而是**在 LLM Agent 和数据仓库之间塞一层 reviewable 的 context layer**——业务定义、单位、enum、已验证 join 全部以 MDL（Modeling Definition Language，语义建模定义）+ `instructions.md` + memory 的形式落到 Git 里。它解决的不是"SQL 怎么生成"，而是"AI 生成的 SQL 为什么可以被信任、被审计、被部署"。

## 项目定位

- **仓库**：`Canner/WrenAI`，Apache-2.0 协议，Python 主代码
- **GitHub Stars**：16.1K，Forks 1.8K（2026-07-17 数据）
- **覆盖数据源**：22+（BigQuery / Snowflake / PostgreSQL / ClickHouse / Amazon Redshift / Databricks / DuckDB …）
- **核心产品**：[getwren.ai](https://getwren.ai) 商业版 + [PyPI `wrenai`](https://pypi.org/project/wrenai/) 开源版
- **重大变更**：2026-05-07 Wren Engine 已 merge 进主仓库；旧的 Docker chat-first BI 保留在 `legacy/v1` 分支作为 GenBI Classic

## 系统地图

| 层 | 责任 | 关键组件 |
|----|------|----------|
| Agent Driver | 接 Claude Code / Cursor / MCP client，按业务问题生成 SQL + 图表 | `wren genbi` CLI（Command-Line Interface，命令行工具）+ MCP server |
| Context Layer | MDL + `instructions.md` + memory，把业务语义"翻译"给 LLM | reviewable、Git-friendly、可 diff |
| Wren Engine | SQL 规划、dry-plan 验证、结构化错误 | `core/` 子目录 |
| Deployment Layer | 生成可分享 dashboard URL，部署到 Vercel / Cloudflare Pages | `wren-core-wasm` 浏览器侧渲染 |
| Governance | 字段血统、值域、enum、单位审计 | `eval runner` + structured errors with hints |

这张地图的关键在于 **Context Layer 是单独的一层**，而不是和 SQL generation 混在一起。这让 WrenAI 和 raw LLM agent 的差距变得可视化——后者没有这一层，所以"业务定义"散落在 prompt 里、版本管理之外、没法审计。

## 关键机制拆解

### 1. MDL：把业务语义从 prompt 搬到 Git

MDL（Modeling Definition Language）是 WrenAI 自定义的语义建模文件。它的关键字段：

- **模型（model）**：一个 SQL 表或视图
- **字段（column）**：字段名、类型、**业务含义**
- **关系（relationship）**：哪些字段对应业务上的"同一件事"
- **视图（view）**：派生指标的 SQL + 描述

把 MDL 文件 commit 到 Git 之后，业务定义的演化有完整审计链——谁改了一个字段的含义、改动对应哪个 commit、谁批准了改动，全都看得到。这和"prompt 里写一段业务定义"是完全不同的工程范式。

### 2. `instructions.md`：非结构化知识的标准容器

有些业务知识不在 schema 里——enum 的实际取值、单位换算、特定 join 的最佳实践。AstrBot 把这些写到 `instructions.md` 里，由 context engine 在 query 时检索补全。这一层对应的是 README 里的"Know"能力：

> The knowledge that makes all of this correct lives in versionable, evidence-linked files: semantic models (MDL), company definitions (`instructions.md`), and a memory of what worked.

### 3. dry-plan 验证

Agent 生成的 SQL 不直接执行，而是先经过 dry-plan：

- **语法检查**：SQL 解析是否合法
- **schema 验证**：用到的字段、表是否在 MDL 里声明过
- **plan 估算**：行数扫描估算，避免 `SELECT *` 跑爆 warehouse
- **结构化错误**：失败时返回的不是 string error，而是带 hint 的结构化错误，Agent 可以重试

这一层把"Agent 生成 SQL"和"SQL 跑得动、跑得对"分成了两个独立模块，前者用 LLM 解决，后者用经典数据库工具解决。

### 4. Deploy 阶段：可分享的 dashboard URL

当 SQL 通过 dry-plan 后，WrenAI 会把 dashboard 渲染到浏览器侧（`wren-core-wasm`），并生成一个可分享的 URL。这一步用 Cloudflare Pages / Vercel 部署，自己掌握前端域名。这和传统 BI 工具"everything is in-tool"的封闭模型完全相反——生成的 dashboard 是一个**真实存在的 URL**，可以发到 IM / 邮件 / Slack。

## 它和传统方案怎么比

README 给的对比表很关键：

| 能力 | raw LLM agent | 传统 BI | 裸语义层 | **WrenAI** |
|------|--------------|---------|---------|------------|
| 帮你写 SQL | ✅（常错） | ❌ | ❌ | ✅ governed |
| 知道业务定义 | ❌ | 部分（in-tool） | ✅（仅 schema） | ✅ + 非 schema 知识 |
| 生成 + 部署 dashboard | ❌ | ✅（手动） | ❌ | ✅ Agent-driven |
| 走你自己的 Agent（Claude Code / Cursor / MCP） | ✅ | ❌ | ❌ | ✅ |
| 开放、可审、Git-friendly | ❌ | ❌ | 部分 | ✅ |
| 22+ 数据源统一治理 | ❌ | per-connector | ✅（仅定义） | ✅ |

这张表的关键不是"WrenAI 比传统 BI 多了几列 ✓"，而是它清晰界定了**自己解决的问题**——"让 AI Agent 能产出可信任的 BI 答案 + 可分享的 dashboard"。如果你的需求只是"出个报表"，传统 BI 仍然是更便宜的路径；如果你需要"Agent 生成 + 治理 + 分享"三位一体，WrenAI 是当前最完整的开源实现。

## 适用人群

- **数据团队想给业务方开放"自然语言问数"能力**：WrenAI 提供 reviewable 的 context，避免业务方问出错的指标
- **AI 应用开发者要把 BI 嵌进自己的 Agent**：走 MCP server，WrenAI 是当前最成熟的开源实现
- **数据合规 / 治理要求高的行业（金融 / 医疗 / 政企）**：MDL + `instructions.md` + dry-plan 三层组成可审计链
- **需要 self-host GenBI 的团队**：Apache-2.0 + 自托管 + 不依赖任何云服务

## 不适合谁

- **业务方只需要"看几个固定报表"**：传统 BI 工具（Metabase / Superset）的 ROI（投资回报率）更高
- **数据源 < 3 个且没有 governance 需求**：自己写 text-to-SQL + RAG 即可
- **不能接受 LLM 调用成本的团队**：WrenAI 每一轮 question-answer 都要走一次 LLM + 一次 dry-plan，token 成本敏感场景需要谨慎评估

## 仓库地址

https://github.com/Canner/WrenAI

## 阅读路径建议

1. 读 README 的 "How Wren compares" 表格，确认你的需求和 Wren 的定位匹配
2. 跑 `pip install wrenai` 起一个本地 demo，喂一个 PostgreSQL sample database
3. 写一份 MDL，定义一个最简单的模型，看生成的 SQL 是否会引用你写的业务定义
4. 读 [Vision 文章](https://www.getwren.ai/post/the-missing-context-layer-for-ai-agents-over-business-data)，理解 context layer 的设计动机