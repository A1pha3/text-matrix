---
title: "alirezarezvani/claude-skills 深度拆解：5,200 Stars 的 354 个 AI Agent Skills 大库是怎么组织的"
date: "2026-07-05T14:55:00+08:00"
slug: "alirezarezvani-claude-skills-agent-skills-library-guide"
description: "354 个生产级 Claude Code Skills 跨 13 个 AI 编码工具、18 个领域，593 个零依赖 Python CLI 的开源大库，本文拆解其 Skills/Agents/Personas 三层模型与 SKILL.md 最小可执行结构。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Agent Skill", "Skills 库", "OpenAI Codex", "MCP"]
author: text-matrix
---

# alirezarezvani/claude-skills 深度拆解：5,200 Stars 的 354 个 AI Agent（智能体） Skills 大库是怎么组织的

## 学习目标

读完这篇，你将能够：

- 说清 `alirezarezvani/claude-skills` 用什么目录约定维持 354 个 Skills 的可发现性，以及"一份源、13 份产物"的跨平台分发是怎么落地的。
- 写出一个最小可执行的 `SKILL.md`：frontmatter 里的 `name` 与 `description` 各自承担什么角色，`description` 为什么是 agent 行为的触发面。
- 区分 Skills、Agents、Personas 三者的边界，并说明它们为什么是叠加而非替代关系。
- 复述三个值得抄的工程决策：stdlib-only 的 593 个 CLI（命令行工具）、安装前的 `skill-security-auditor` 安全闸门、把 CHANGELOG 当治理日志。
- 在 Claude Code / OpenAI Codex / Cursor 三条路径里挑出适合自己团队的那条，并讲清"按域分批 install"的采用顺序。
- 判断这个库什么时候该用、什么时候不该用——尤其是"装 354 条 Skill 大部分用不上"和"第三方 Skills 的安全审计"两条边界。

## 目录

- [alirezarezvani/claude-skills 深度拆解：5,200 Stars 的 354 个 AI Agent（智能体） Skills 大库是怎么组织的](#alirezarezvaniclaude-skills-深度拆解5200-stars-的-354-个-ai-agent智能体-skills-大库是怎么组织的)
  - [学习目标](#学习目标)
  - [目录](#目录)
  - [一句话定位](#一句话定位)
  - [项目全景：354 × 18 × 13 的矩阵](#项目全景354--18--13-的矩阵)
  - [Skills / Agents / Personas：三层概念切分](#skills--agents--personas三层概念切分)
  - [SKILL.md 的最小可执行结构](#skillmd-的最小可执行结构)
  - [跨 13 平台的"一份源、13 份产物"](#跨-13-平台的一份源13-份产物)
  - [工程亮点：三个值得抄的工程决策](#工程亮点三个值得抄的工程决策)
    - [1. stdlib-only 的 593 个 CLI](#1-stdlib-only-的-593-个-cli)
    - [2. `skill-security-auditor`：Skills 安装前的安全闸门](#2-skill-security-auditorskills-安装前的安全闸门)
    - [3. CHANGELOG 当成"治理日志"而不是流水账](#3-changelog-当成治理日志而不是流水账)
  - [安装实战：三条主流路径](#安装实战三条主流路径)
  - [适用边界与采用建议](#适用边界与采用建议)
  - [一句话总结](#一句话总结)
  - [自测题](#自测题)
  - [练习](#练习)
  - [进阶方向](#进阶方向)
  - [常见问题](#常见问题)

## 一句话定位

`alirezarezvani/claude-skills` 是当前 GitHub 上**最完整的开源 Claude Code Skills 与 Agent Plugins 库**，5,200+ Stars，354 个生产级 Skills 覆盖工程、产品、营销、合规、C-level 顾问等 18 个领域，同一份 Skills 通过 `scripts/convert.sh` 可一键分发到 13 个 AI 编码工具（Claude Code / OpenAI Codex / Gemini CLI / OpenClaw / Cursor / Aider / Windsurf / Kilo Code / OpenCode / Augment / Antigravity / Hermes Agent / Mistral Vibe）。

**这篇文章不展开**单条 Skill 的逐字使用手册（README 里已经写得很细），而是从**库设计者的视角**回答三个问题：354 个 Skills 用什么目录约定能保持可发现性？`SKILL.md` 的最小可执行结构长什么样？跨 13 个平台的"一份源、13 份产物"是怎么落地的？

## 项目全景：354 × 18 × 13 的矩阵

README 把整个库划成 **18 个领域**、**354 个 Skills**、配套 **593 个 Python CLI（命令行工具）工具**（标准库 only，零 pip 安装）、**711 份模板与参考文档**。下面这张表是来自 `Skills Overview` 一节的精确摘录，数字与 CHANGELOG 里 `derive_counters.py --check` 校验过的 per-domain 表保持一致：

| 领域 | Skill 数 | 代表能力 |
|---|---|---|
| 🔧 Engineering — Core | 52 | 架构 / 前端 / 后端 / 全栈 / QA / DevOps / SecOps / AI-ML / Playwright Pro / self-improving-agent |
| ⚡ Engineering — POWERFUL | 80 | agent-designer / RAG（检索增强生成）-architect / database（数据库）-designer / CI-CD / MCP-builder（建造者模式）/ AgentHub / zero-hallucination（零幻觉）-coder |
| 🎯 Product | 17 | PM / 敏捷 PO / 战略 / UX / UI / Landing / SaaS（软件即服务）scaffolder / 实验设计 |
| 📣 Marketing | 48 | 8 个 Pod：内容 / SEO（搜索引擎优化）+ AEO（E-E-A-T 审计、5 LLM（大语言模型）引用追踪）/ 本地 SEO（GBP/NAP/Map-Pack）/ CRO / 渠道 / 增长 / 情报 / 销售 |
| 🚀 Productivity | 7 | capture / email pair / reflect / handoff / andreessen / roast（5 角度对抗点子评审 → GO/RESHAPE/KILL） |
| 🔬 Research（学术） | 9 | orchestrator + pulse / litreview / grants（NIH）/ dossier / patent / syllabus / notebooklm / deep-research |
| 🧪 Research Operations（v2.9.0 新增） | 5 | 临床研究 / 研究财务 / 市场研究 / 产品研究（每条带 onboarding + 自定义 + autoresearch 桥接） |
| 📋 Project Management | 9 | Senior PM / Scrum / Jira / Confluence / Atlassian admin + bundled Atlassian Remote MCP |
| 🏥 Regulatory & QM | 19 | ISO 13485 / MDR 2017/745 / FDA / ISO 27001 / GDPR / SOC 2 / CAPA / agent-decision-receipts |
| 🛡️ Compliance OS | 9 | 合规操作系统：controls / evidence / audit-readiness |
| 💼 C-Level Advisory | 68 | 全 C-suite（CEO/CTO/CFO/CMO/CRO/CPO/COO/CHRO/CISO/GC/CDO/CAIO/CCO/VPE）+ 21 条 `/cs:*` 命令 |
| 📈 Business & Growth | 5 | 客户成功 / Sales Engineer / Revenue Ops / 合同与提案 / BizDev |
| 🏭 Business Operations | 7 | orchestrator + process-mapper / vendor-management / capacity-planner |
| 🤝 Commercial | 8 | 定价 / deal-desk / 渠道经济 / RFP 响应 / 商业预测 |
| 💰 Finance | 4 | 财务分析师（DCF / 预算 / 预测）/ SaaS 指标 / 投资顾问 |
| 🔄 Loop Library | 1 | 发现、查找、审计/修复、改编、设计 bounded agent loops |
| 📄 Markdown → HTML | 5 | md-document / md-review / md-slides / 设计系统 / 编排器 |

**维护强度信号**：CHANGELOG 顶部仍在跑 `## [Unreleased] — housekeeping: CHANGELOG backfill + per-domain counter validation`，最近一次提交 2026-07-01，仓库自己用 Claude Code 维护（commit 作者里 `claude` 这个 bot 频繁出现），PR #882 是当前最新合并。

## Skills / Agents / Personas：三层概念切分

README 用一张三列对照表把这三个最容易混的概念讲清楚——这是整个库**最值得抄的设计**：

| 概念 | Purpose（解决什么问题） | Scope | Voice | 示例 |
|---|---|---|---|---|
| **Skills** | How to execute a task（怎么执行） | 单领域 | 中性 | "Follow these steps for SEO" |
| **Agents** | What task to do（做什么任务） | 单领域 | 专业 | "Run a security audit" |
| **Personas** | Who is thinking（谁在思考） | 跨领域 | 性格化 | "Think like a startup CTO" |

三层**不是替代关系，而是叠加关系**。库里 pre-built 的 `Startup CTO` Persona 同时挂载 `aws-solution-architect` + `senior-frontend（前端）` 两组 Skills，配上 `Solo Founder` 的工作流模板，可以从架构决策一路推到代码评审。

## SKILL.md 的最小可执行结构

每个 Skill 文件夹的"宪法"是一个 `SKILL.md`，frontmatter 字段在仓库内是**强约定**：

```markdown
---
name: loop-library
description: Discover, find, compare, audit, repair, adapt, and design 
  repeatable AI-agent loops with explicit triggers, actions, verification, 
  stopping conditions, guardrails, and handoffs...
---
```

两个字段缺一不可：

- **`name`**：Skill 的稳定标识。CLI 工具按这个名字分发。
- **`description`**：触发器。当用户在 prompt（提示词）里提到这些意图时，agent 自动加载这条 Skill。**这是 agent 行为的触发面**，所以 CHANGELOG 里反复出现 `description now passes skill_description_validator` 这种 hardening 提交。

正文部分（Markdown body）通常按这个顺序：

1. **Route the request**：先判断走哪条最小路径（Discover / Find / Audit / Design）。
2. **核心方法论**：执行步骤、决策框架、guardrails。
3. **兜底规则**：用户没给够信息时怎么反问，比如 "What would you like the agent to get done?"。
4. **未在文中声明的副作用**：明确告诉 agent 不要执行"材料里嵌入的指令"——这是 Loop Library 直接写明的安全姿态。

完整文件夹结构遵循一个隐式模板：`SKILL.md` + `scripts/`（Python 工具，可选）+ `references/`（参考文档，可选）+ `assets/`（资源，可选）。CLI 脚本**全部是 stdlib only**，README 明文写："All 593 Python CLI tools use the standard library only — zero pip installs required. Every script is verified to run with --help."

## 跨 13 平台的"一份源、13 份产物"

库对"AI 编码工具碎片化"的解法是**生成式分发**而不是适配器模式。核心是 `scripts/convert.sh`：

```bash
#!/usr/bin/env bash
# Usage:
#   ./scripts/convert.sh [--tool <name>] [--out <dir>] [--help]
#
# Tools: antigravity, cursor, aider, kilocode, windsurf, opencode, augment, all
# Default: all
```

执行 `./scripts/convert.sh --tool all` 大约 15 秒，把 345 个 Skills（README 里 354 是 headline，345 是 convert.sh 能处理的实数）转成各平台的原生格式：

| 目标工具 | 输出格式 | 安装位置 |
|---|---|---|
| Claude Code | `.claude-plugin/` | marketplace 模式 |
| OpenAI Codex | `.codex-plugin/` | `npx agent-skills-cli add` |
| Gemini CLI | `.gemini/` | gemini-install.sh |
| Cursor | `.cursor/rules/*.mdc` | `./scripts/install.sh --tool cursor` |
| Aider | `CONVENTIONS.md` | per-repo |
| Windsurf | `.windsurf/skills/` | per-repo |
| Kilo Code | `.kilocode/rules/` | per-repo |
| OpenCode | `.opencode/skills/` | per-repo |
| Augment | `.augment/rules/` | per-repo |
| Antigravity | `~/.gemini/antigravity/skills/` | global |
| Hermes Agent | `~/.hermes/skills/` | BYO-sync tier |
| Mistral Vibe | `~/.vibe/skills/` | BYO-sync tier |
| OpenClaw | `~/.openclaw/skills/` | 一键 curl 脚本 |

底层协议遵循 [agentskills.io](https://agentskills.io) 的 `SKILL.md` 标准（Hermes Agent 与 Mistral Vibe 直接复用，零格式转换），其他工具由 `convert.sh` 静态转换。

## 工程亮点：三个值得抄的工程决策

### 1. stdlib-only 的 593 个 CLI

README 把"零 pip 安装"作为**强约束**写进契约：`Every script is verified to run with --help`。这带来两个后果：

- **零供应链攻击面**：所有 Skills 拉下来就能跑，没有 `pip install -r requirements.txt` 这种隐式执行入口。
- **CI 友好**：CHANGELOG 里反复出现的 `derive_counters.py --check` 这种工具本身就是 stdlib 写的，跨机器一致。

代价是脚本必须用标准库手搓很多东西（比如 `metrics_calculator.py` 算 MRR / churned 自己写参数解析、自己写 JSON 输出），但这种"用 stdlib 写一切"的姿态本身就是一个信号：库作者清楚 Skill 的安全边界。

### 2. `skill-security-auditor`：Skills 安装前的安全闸门

POWEREUL tier 里专门有一条 `skill-security-auditor`，README 写明它扫描的六类风险：

> Scans for: **command injection**, **code execution**, **data exfiltration**, **prompt injection**, **dependency supply chain risks**, **privilege escalation**. Returns PASS / WARN / FAIL with remediation guidance.

调用方式：

```bash
python3 engineering/skill-security-auditor/scripts/skill_security_auditor.py /path/to/skill/
```

这条 Skill 的存在回应了一个非常具体的问题：**当你打算 `npx skills add xxx` 安装第三方 Skills 时，谁替你审过 `scripts/` 里那段 Python 是不是真的"只算指标"**。`skill-security-auditor` 是给"我打算装一堆 Skills"这个动作配的安全带。

### 3. CHANGELOG 当成"治理日志"而不是流水账

CHANGELOG 不是简单按时间倒序列 commit，而是按 **PR 粒度 + hardening 注释**组织。比如：

> **`research/deep-research`** (PR #872, hardened from #851 by @Socialpranker) — rigor-first multi-source meta-research: 9-phase pipeline, triangulation (>=3 independent differently-typed sources per thesis), mandatory adversarial pass, per-source files with verbatim quotes, **no fabricated citations**.

> Hardening applied before merge（合并）: fixed dangling cross-refs (`ai-seo` → `aeo`, removed the non-existent `gbp-content-creator` companion), description now passes `skill_description_validator`.

`derive_counters.py --check` 是 CI 闸门 G3，对 README 的 per-domain 表做强制一致性校验——一个 354 个 Skills 的库，per-domain 数字不能漂。

## 安装实战：三条主流路径

**路径 A — Claude Code（推荐，marketplace 模式）**：

```bash
/plugin marketplace add alirezarezvani/claude-skills

# 按域批量安装
/plugin install engineering-skills@claude-code-skills           # 24 个核心工程
/plugin install engineering-advanced-skills@claude-code-skills  # 25 个 POWERFUL
/plugin install marketing-skills@claude-code-skills             # 43 个营销
/plugin install c-level-skills@claude-code-skills               # 28 个 C 级顾问

# 或单条安装
/plugin install skill-security-auditor@claude-code-skills
/plugin install playwright-pro@claude-code-skills
```

**路径 B — OpenAI Codex**：

```bash
npx agent-skills-cli add alirezarezvani/claude-skills --agent codex
# 或 git clone + ./scripts/codex-install.sh
```

**路径 C — Cursor / Aider / Windsurf 等 7 个静态格式工具**：

```bash
# 1) 转换所有 Skills 到目标工具（约 15 秒）
./scripts/convert.sh --tool all

# 2) 安装进指定项目
./scripts/install.sh --tool cursor --target /path/to/project

# 3) 验证（Cursor 模式下应该看到 346 个 .mdc）
find .cursor/rules -name "*.mdc" | wc -l
```

## 适用边界与采用建议

**什么时候用**：

- 团队已经在用 Claude Code / Codex / Cursor 中的至少一个，希望把"工程最佳实践 / 安全审计 / 合规审查"以 Skill 形式注入 agent，而不是写散在各处的 prompt。
- 单人 / 小团队需要现成的"代理顾问"能力：Startup CTO Persona + 21 条 `/cs:*` 命令是一种轻量级"虚拟 CTO"配置。
- 需要做营销（特别是 AEO——LLM 引用追踪）、合规（MDR / FDA / SOC 2）、研究运营（NIH grants / 临床研究设计）等长尾领域的结构化提示。

**什么时候不用**：

- 只想要单条 Skill（比如一个 SEO 模板），直接 clone（克隆）仓库挑一条复制即可，没必要装整个库。
- 团队不接受"装 354 条 Skill 里大部分用不上"——`convert.sh --tool all` 会一次性生成 345 条规则文件，Coder 项目可能会被刷屏。建议**按域分批 `install`**。
- 对 Skill 行为透明度有合规要求时，必须先跑 `skill-security-auditor` 审一遍——README 自陈"开源库"，但"零 pip 安装"不等于"零风险"。

**采用顺序建议**：

1. 先装 `skill-security-auditor`，用它审一遍库本身的 Scripts。
2. 按域分批 `install`，每批装完跑一条典型 Skill（比如 `seo-audit`）验证 agent 行为。
3. 跨平台团队：先把 Skills 装在主力工具上，再跑 `convert.sh --tool all` 把其他工具的产物放仓库 `.cursor/rules/` / `.augment/rules/` 之类，**保留 Skills 源在 marketplace**，产物当只读快照。
4. 自建 Skill：复用仓库 `engineering-team/skills/` 下的 `TEMPLATE.md` 与 `CLAUDE.md`，对齐 frontmatter 的 `name` + `description` 触发器约定，否则 agent 不会触发。

## 一句话总结

`alirezarezvani/claude-skills` 不只是一个 Skills 库，它是一份**关于"如何把领域知识打包成 agent 可执行指令"的可运行范例**——三层概念切分（Skills/Agents/Personas）、单一 frontmatter 触发器、`SKILL.md` 强约定、生成式跨平台分发、stdlib-only CLI、CHANGELOG 治理日志，每一条都值得在做自己内部 Skills 仓库时参考。

---

**仓库地址**：https://github.com/alirezarezvani/claude-skills

**License**：MIT（Copyright 2025 Alireza Rezvani）

**Stars**：5,200+

**Skills 总数**：354（per README headline）/ 345（per `convert.sh` 可转换实数）/ 18 领域

**最近提交**：2026-07-01（PR #882）

## 自测题

**Q1**：README 说库里有 354 个 Skills，但 `convert.sh` 只能处理 345 个。这两个数哪个是"实数"？目录约定靠什么维持 354 个 Skills 的可发现性？

**Q2**：一个 `SKILL.md` 的 frontmatter 里，`name` 和 `description` 各承担什么角色？为什么 `description` 被叫做"agent 行为的触发面"？

**Q3**：Skills、Agents、Personas 三者的边界是什么？库里 `Startup CTO` Persona 同时挂载 `aws-solution-architect` + `senior-frontend` 两组 Skills，这说明三者是替代关系还是叠加关系？

**Q4**：stdlib-only 的 593 个 CLI 带来哪两个具体后果？`skill-security-auditor` 扫描哪六类风险？

**Q5**：库对"AI 编码工具碎片化"用的是生成式分发还是适配器模式？`convert.sh --tool all` 大约多久跑完，产物落在哪些目录？

**Q6**：什么情况下"不该装整个库"？采用顺序的前两步是什么？

<details>
<summary>答案提示</summary>

- A1：354 是 README 的 headline 数字，`convert.sh` 能实际转换的是 345 个实数（另有 9 个可能不在转换范围内）。可发现性靠 `Skills/` 下的领域目录约定 + 每个 Skill 文件夹里的 `SKILL.md` 强约定维持。
- A2：`name` 是 CLI 分发时引用的稳定标识；`description` 写明触发意图，agent 在用户 prompt 里命中这些意图时自动加载这条 Skill，所以它是行为触发面。
- A3：Skills = 怎么执行（单领域、中性），Agents = 做什么任务（单领域、专业），Personas = 谁在思考（跨领域、性格化）。三者叠加：`Startup CTO` 一个 Persona 同时挂两组 Skills，从架构决策推到代码评审。
- A4：两个后果——零供应链攻击面（拉下来就能跑，没有隐式 `pip install`）、CI 友好（工具本身也是 stdlib 写的）。六类风险：命令注入、代码执行、数据外泄、提示词注入、依赖供应链风险、权限提升。
- A5：生成式分发（`scripts/convert.sh` 静态转换），不是适配器。默认约 15 秒；产物按工具落进 `.claude-plugin/`、`.cursor/rules/`、`.augment/rules/`、`.windsurf/skills/` 等目录。
- A6：只想要单条 Skill、或团队不接受"装 354 条大部分用不上"刷屏时，不该装整个库。采用顺序前两步：先装 `skill-security-auditor` 审一遍库本身的 Scripts；再按域分批 `install`，每批装完跑一条典型 Skill 验证。

</details>

## 练习

1. 照着仓库的 `TEMPLATE.md`，给自己写一个 `SKILL.md`：领域定为"落地页 SEO 审计"，`name: seo-audit`，`description` 写明"当用户要求审计落地页 SEO、检查标题/描述/结构化数据时触发"。贴进 Claude Code 后，用一句"帮我审计这个落地页的 SEO"验证它是否被自动加载。
2. 克隆仓库，跑 `./scripts/convert.sh --tool all`，再执行 `find .cursor/rules -name "*.mdc" | wc -l`，确认 Cursor 模式下产物数量（README 预期约 346 个 `.mdc`），并打开其中一个 `.mdc` 看转换后的格式。
3. 从别处 `clone` 一个你不完全信任的 Skill 文件夹，跑 `python3 engineering/skill-security-auditor/scripts/skill_security_auditor.py /path/to/skill/`，记录它返回的是 PASS / WARN / FAIL，以及它标记的六类风险里命中了哪一类。
4. 按域分批安装：`/plugin install engineering-skills@claude-code-skills`，然后触发一条典型 Skill（例如 `seo-audit` 或 `playwright-pro`），对比"装之前 agent 不会做、装之后会自动做"的行为差异。
5. 读一遍 CHANGELOG，找一条 hardening 提交（例如 `ai-seo → aeo` 那条），用一句话复述它修了哪类一致性问题，以及 `derive_counters.py --check` 这个 CI 闸门在防什么漂移。

## 进阶方向

- **自建内部 Skills 仓库**：复用仓库 `engineering-team/skills/` 下的 `TEMPLATE.md` 与 `CLAUDE.md`，对齐 frontmatter 的 `name` + `description` 触发器约定，否则 agent 不会在正确时机加载你的 Skill。
- **安全左移**：把 `skill-security-auditor` 接进你们自己的 CI，作为 `install` 第三方 Skills 之前的强制闸门，而不是等出事再审。
- **跨平台产物治理**：跨平台团队先把 Skills 源留在 marketplace，只对主力工具跑 `convert.sh --tool all`，把其他工具的产物（`.cursor/rules/`、`.augment/rules/` 等）当只读快照提交，避免源和产物双向漂移。
- **长尾领域深耕**：挑一个你们真正用得上的长尾领域——合规（MDR / FDA / SOC 2）、AEO（LLM 引用追踪）、研究运营（NIH grants / 临床研究设计）——读透对应 Skills 的方法论，比泛泛装一大堆更有回报。

## 常见问题

**装整个库会把我的项目刷屏吗？**
会。`convert.sh --tool all` 一次性生成 345 条规则文件，Cursor 项目里可能直接多出 346 个 `.mdc`。建议按域分批 `install`（例如先 `engineering-skills` 再 `marketing-skills`），而不是一把梭。

**第三方 Skills 安全吗？"零 pip 安装"是不是就零风险？**
不是。`README` 自陈"开源库"，但"零 pip 安装"只意味着没有隐式 `pip install` 执行入口，不等于代码无害。装之前先跑 `skill-security-auditor` 审一遍 `scripts/` 里那段 Python 到底是不是"只算指标"。

**354 和 345 这两个数字到底差在哪？**
354 是 README 的 headline（含所有 Skills），345 是 `convert.sh` 当前能实际转换的实数。写文档或向团队介绍时，用 345 指代"可跨平台分发的一份源"更准确。

**我只想要其中一条 Skill，必须装整个库吗？**
不必。直接 `clone` 仓库挑那一条复制进你的配置即可，库的价值在于"可发现 + 可分发"，单条复用不需要 marketplace 模式。

**它支持哪些 AI 编码工具？**
13 个：Claude Code、OpenAI Codex、Gemini CLI、Cursor、Aider、Windsurf、Kilo Code、OpenCode、Augment、Antigravity、Hermes Agent、Mistral Vibe、OpenClaw。底层协议遵循 agentskills.io 的 `SKILL.md` 标准，Hermes Agent 与 Mistral Vibe 直接复用、零格式转换。

**License 是什么？能商用吗？**
MIT（Copyright 2025 Alireza Rezvani），可商用、可修改、可再分发，只要保留版权与许可声明。