---
title: "Claude Code Skills & Plugins：AI 编程智能体技能库完全指南"
slug: "claude-code-skills-agent-plugins-guide"
aliases:
  - /posts/tech/claude-code-skills-agent-plugins-guide/
date: "2026-03-31T12:35:00+08:00"
categories: ["技术笔记"]
tags: ["Claude Code", "AI编程", "Skills", "OpenClaw", "Cursor"]
description: "全面解析 Claude Code Skills 项目：205 个生产级 AI 编程技能，支持 11 个平台，涵盖工程、产品、营销等 9 大领域。从入门到精通，包含安装配置、原理分析、架构设计、开发扩展和最佳实践。"
---

# Claude Code Skills & Plugins：AI 编程智能体技能库完全指南

> 预计阅读时间：40分钟 | 难度：⭐⭐⭐⭐

AI 编程工具缺的不是知识，是工作流。Claude Code Skills 把 205 个领域的专家工作流写成了 AI 能直接执行的指令文件——每个技能本质上是一份写死的检查清单、决策框架和工具链的组合。本文不逐个介绍技能功能（官方文档已经做了这件事），而是解析这套系统的设计思路、三层架构分工，以及你在自己项目里应该按什么顺序引入。

---

## 学习目标

学完本文档后，你将能够：

- 理解 Claude Code Skills 的核心概念与设计理念
- 掌握在 Claude Code、OpenAI Codex、Gemini CLI、OpenClaw 等 11 个 AI 编程工具中安装和使用技能的方法
- 了解 205 个技能的分类体系与核心功能
- 学会使用 `convert.sh` 脚本将技能转换为不同工具的原生格式
- 掌握开发新技能的规范与工作流程
- 理解 Skills、Agents、Personas 三层架构的适用场景
- 能够在团队中推广和应用这套技能系统

---

## §2 项目概述

### 2.1 什么是 Claude Code Skills

Claude Code Skills（官方仓库：[alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills)，简称 **Skills**）是**目前最全面的开源 AI 编程智能体技能库**，收录了 205 个生产级技能（Skills）和插件（Plugins），支持 11 个主流 AI 编程工具。项目获得了 8,200+ GitHub Stars，973 Forks，由开发者 [alirezarezvani](https://github.com/alirezarezvani) 维护，采用 MIT 许可证开源。

这个项目做的事情很直接：**把领域专家的知识写成 AI 能读懂的指令文件，配上一组零依赖的 Python 工具脚本**。AI 加载一个技能后，不需要依赖自身训练数据中的模糊记忆，而是按照文件里的检查清单、决策框架和工具链执行任务。每个技能本质上是一个指令包（SKILL.md + tools/ + references/），AI 加载后就在对应领域按专家路径工作。

### 2.2 支持的平台

项目天然支持 11 个主流 AI 编程工具，覆盖市面上几乎所有重要的 AI 辅助编程产品：

| 平台 | 插件名称 | 技能数量 | 官方推荐 |
|------|---------|---------|---------|
| **Claude Code** | Plugins | 205 | ✅ 推荐 |
| **OpenAI Codex** | Agent Skills | 205 | ✅ 推荐 |
| **Gemini CLI** | Native Skills | 205 | 🆕 新增 |
| **OpenClaw** | OpenClaw Skills | 205 | 支持 |
| **Cursor** | .mdc Rules | 156 | 支持 |
| **Aider** | CONVENTIONS.md | 156 | 支持 |
| **Windsurf** | .windsurf/skills | 156 | 支持 |
| **Kilo Code** | .kilocode/rules | 156 | 支持 |
| **OpenCode** | .opencode/skills | 156 | 支持 |
| **Augment** | .augment/rules | 156 | 支持 |
| **Antigravity** | ~/.gemini/antigravity/skills | 156 | 支持 |

> **注意**：部分工具（如 Cursor、Aider）不支持 Python 工具脚本，仅支持指令规则转换，因此技能总数为 156 个而非完整的 205 个。

### 2.3 核心数据

```
Stars:     8,200+
Forks:     973
Commits:   587
最新提交:   2026-03-26
许可证:    MIT
开发者:    alirezarezvani
```

### 2.4 为什么需要 AI 编程技能

用 AI 编程工具写过实际项目的人都会碰到一个瓶颈：通用模型知道概念，但不知道怎么落地。举个例子：

- AI 知道"要写测试"，但面对遗留代码时，它不知道该怎么写一份能跑、可维护的 Playwright 集成测试
- AI 理解"SEO 优化"这个词，但不清楚 Google Core Web Vitals 的评分细则和具体修复步骤
- AI 会写代码，但设计数据库表结构或 API 版本管理时缺乏工程判断

Skills 解决的就是这个"知道概念 vs 知道怎么干"的落差。它不是给 AI 补充背景知识，而是直接给出工作流。每个技能包含：

| 组件 | 说明 |
|------|------|
| **SKILL.md**（技能定义文件） | 技能的核心指令文件，包含工作流程、决策框架和执行步骤 |
| **Python 工具**（纯标准库 stdlib-only） | 268 个纯 Python 标准库 CLI 脚本（无任何第三方依赖），提供自动化能力 |
| **参考文档**（references） | 模板、检查清单、最佳实践文档等支撑材料 |

---

## §3 原理分析

### 3.1 技能的本质：模块化专家知识封装

Claude Code Skills 的设计思路很朴素：你给 AI 的指令越具体，它的输出越靠谱。与其希望 AI "恰好知道"某个领域的最佳实践，不如把专家的决策流程写成一份标准化文件，AI 照着执行。

一个典型的技能结构如下：

```
engineering/
├── SKILL.md              # 技能核心定义
├── README.md             # 使用说明
├── CLAUDE.md             # AI 智能体配置
├── tools/                # Python 工具脚本
│   ├── analyze.sh
│   └── generate.sh
├── references/           # 参考文档
│   ├── template.md
│   └── checklist.md
└── package.json          # 元数据配置
```

**SKILL.md 是技能的核心**，它定义了 AI 在该领域应该如何思考、提问、执行和验证。一个高质量的 SKILL.md 包含：

- **目标声明**：明确技能要解决什么问题
- **前置条件**：使用技能前需要满足什么
- **执行流程**：分步骤的工作流程，每步都有明确的输入输出
- **决策框架**：遇到分歧时如何判断
- **验证标准**：如何确认任务完成质量

### 3.2 Skills vs Agents vs Personas：三层架构

项目区分了三种不同层次的智能增强方式，适用于不同场景：

| 维度 | **Skills** | **Agents** | **Personas** |
|------|------------|------------|--------------|
| **核心问题** | 如何执行任务 | 应该执行什么任务 | 谁在思考 |
| **范围** | 单领域 | 单领域 | 跨领域 |
| **语气** | 中性专业 | 专业严肃 | 个性化驱动 |
| **适用场景** | 标准化执行 | 自动化流程 | 创意咨询 |
| **示例指令** | "Follow these steps for SEO" | "Run a security audit" | "Think like a startup CTO" |

**Skills** 解决"怎么做"。加载 `/seo-auditor` 后，AI 会按文件里写好的流程——检查 meta 标签、跑 Lighthouse、输出按优先级排列的修复列表——而不是随口说一句"优化一下 SEO"。它的价值是把一次性的提示词变成了可重复执行的检查清单。

**Agents** 在 Skills 之上加了"该做什么"的判断。`/security-agent` 不等人命令，它会自己扫描项目里值得审计的地方，然后按需拉起对应的 Skills。你可以把它理解为给 AI 装了一组触发规则。

**Personas** 改的是思考框架，不绑定特定任务。给 AI 设定 `"Think like a startup CTO"` 后，它在讨论技术选型时会自动带上成本、团队能力、迁移风险的权衡——这不是任何一个 Skill 能单独做到的，因为它跨了工程、产品和商业三个维度。

### 3.3 技能分类体系

205 个技能划分为 9 大领域：

| 领域 | 技能数 | 代表技能 | 覆盖方向 |
|------|--------|---------|---------|
| **Engineering — Core** | 26 | 架构设计、前后端开发、QA、DevOps | 软件工程全生命周期 |
| **Playwright Pro** | 9+3 | 测试生成、flaky 修复、Cypress 迁移 | 企业级 UI 自动化测试 |
| **Self-Improving Agent** | 5+2 | 自动记忆管理、模式提炼、技能提取 | 让 AI 在对话中积累经验 |
| **Engineering — POWERFUL** | 30 | Agent 设计器、RAG 架构师、CI/CD 构建器 | 复杂系统设计与实现 |
| **Product** | 14 | 产品经理、UX 研究员、SaaS 脚手架 | 产品思维与用户洞察 |
| **Marketing** | 43 | SEO 审计、内容营销、社交媒体 | 增长与获客 |
| **RA/QM** | 12 | 监管合规、质量管理 | 企业合规与质量保障 |
| **Project Management** | 6 | 敏捷教练、Sprint 规划 | 项目交付管理 |
| **C-level Advisory** | 28 | CTO/CFO/COO 顾问 | 高管决策支持 |
| **Finance** | 2 | 金融分析师、SaaS 指标 | 财务分析与商业智能 |
| **Business & Growth** | 4 | 增长策略、商业模式 | 商业战略 |

### 3.4 Python 工具的设计约束

268 个 Python 工具脚本承载了技能的大部分自动化能力。它们有几条硬约束：

**纯标准库**：所有脚本仅使用 Python 标准库（`stdlib`），**不依赖任何第三方包**。这确保了脚本在任何 Python 环境中都能运行，不会因为 pip 安装问题而失败。

**零外部依赖命令**：工具脚本调用的外部命令（如 `curl`、`jq`、`git`）在脚本内部有fallback处理或明确的依赖声明。

**原子化设计**：每个脚本只做一件事，通过管道组合实现复杂功能。这种 Unix 哲学让工具可预测、可测试、可组合。

**跨平台兼容**：脚本经过测试可在 Linux、macOS、Windows（WSL）环境下正常运行。

### 3.5 一次真实任务如何流过三个技能

只看静态结构容易觉得技能就是"进阶版提示词"。放到一次具体任务里看，区别会更清楚。

假设你要给一个新项目设计用户认证系统。你加载了 `database-designer`、`api-designer` 和 `backend-dev` 三个技能，然后对 AI 说："设计一套用户注册登录的数据库和 API。"

AI 不会像没加载技能时那样直接给出一个大概方案。`database-designer` 的 SKILL.md 里写好了：先确认业务实体、再画关系图、再输出 DDL、最后给索引建议。AI 会按这个顺序提问——"用户有几种角色？需要支持第三方登录吗？会话管理用什么策略？"——等你回答完，它产出的是一份带主键、外键、索引策略的完整 schema，而不是一句 "users 表应该有 id、email、password"。

接着 `api-designer` 接管。它的 SKILL.md 规定了 RESTful 端点命名规范、版本号策略和错误响应格式。AI 读入上一步的 schema，输出 `/api/v1/auth/register`、`/api/v1/auth/login` 等端点的完整定义——请求体、响应体、状态码、rate limit 建议——格式与团队已有的 OpenAPI 规范一致。

最后 `backend-dev` 上场。它的指令文件告诉 AI：先检查数据库 schema 和 API 定义是否存在、再决定用什么 ORM、再生成带参数校验和错误处理的代码骨架。AI 发现前两步的产物都在上下文里，直接生成了 Express + Prisma 的实现，每个端点都带了输入校验中间件。

这三个技能单独用也能工作，但串联起来效果不一样：每个技能的输出格式被下一个技能识别为"已知输入"，AI 不需要在每一步重新猜测上下文。这就是技能和零散提示词的根本差别——技能把工作流写进了文件，AI 只需要按检查清单推进。实际使用中，你可以按任务组合不同的技能链：SEO 审计链（auditor → copywriter）、安全评估链（auditor → fixer）、产品设计链（pm → ux → api-designer），每个链的交接点都是预定义的输出格式。

---

## §4 架构分析

### 4.1 仓库整体结构

```
claude-skills/
├── .autoresearch/           # AutoResearch SEO 相关技能
│   └── seo/
├── .claude-plugin/          # Claude Code 插件配置
├── .claude/                 # Claude Code 配置
│   └── commands/            # Slash commands
├── .codex/                  # OpenAI Codex 格式
├── .gemini/                 # Gemini CLI 格式
├── agents/                  # Agent 智能体模板
│   ├── cs-product-manager/
│   └── ...
├── business-growth/          # 商业增长技能
├── c-level-advisor/          # C-level 高管顾问技能
├── commands/                # 命令行工具
├── custom-gpt/               # 自定义 GPT 资源
├── docs/                     # MkDocs 文档站点
├── documentation/            # 参考文档库
├── engineering/              # 工程技能（POWERFUL 级）
├── engineering-team/          # 工程团队技能（核心）
├── eval-workspace/            # 评估工作区
├── finance/                  # 金融技能
├── marketing-skill/           # 营销技能
├── orchestration/            # 多智能体编排协议
├── product-team/             # 产品团队技能
├── project-management/        # 项目管理技能
├── ra-qm-team/              # 监管与质量管理技能
├── scripts/                  # 安装与转换脚本
├── standards/                # 开发规范
├── templates/                # 项目模板
├── CHANGELOG.md              # 版本变更日志
├── CLAUDE.md                 # Claude 配置入口
├── GEMINI.md                 # Gemini 配置入口
├── INSTALLATION.md           # 安装指南
├── README.md                 # 项目说明
├── SKILL-AUTHORING-STANDARD.md # 技能开发规范
├── SKILL_PIPELINE.md         # 技能开发流程
├── STORE.md                  # 技能商店目录
└── mkdocs.yml               # 文档站点配置
```

### 4.2 多格式转换架构

项目实现了一套巧妙的**多工具格式转换系统**。核心是 `scripts/convert.sh` 脚本，它能自动将基础技能转换为目标工具的原生格式：

```
源格式（SKILL.md）
       ↓
scripts/convert.sh
       ↓
┌──────────────────────────────────────┐
│  Cursor (.mdc)                       │
│  Aider (CONVENTIONS.md)              │
│  Windsurf (.windsurf/skills/)        │
│  Kilo Code (.kilocode/rules/)        │
│  OpenCode (.opencode/skills/)        │
│  Augment (.augment/rules/)           │
│  Antigravity (~/.gemini/antigravity/) │
└──────────────────────────────────────┘
```

转换过程是**无损的**：SKILL.md 中的结构化指令被转换为目标工具的等价格式，Python 工具脚本被包装为符合目标工具规范的执行方式。

### 4.3 安装脚本体系

| 脚本 | 用途 | 支持平台 |
|------|------|---------|
| `scripts/gemini-install.sh` | Gemini CLI 快速安装 | Gemini CLI |
| `scripts/openclaw-install.sh` | OpenClaw 快速安装 | OpenClaw |
| `scripts/codex-install.sh` | OpenAI Codex 安装 | Codex |
| `scripts/convert.sh` | 转换为所有工具格式 | 多平台 |
| `scripts/install.sh` | 安装到目标项目 | 多平台 |

安装流程设计为**幂等操作**：重复执行不会产生副作用，可安全重试。

### 4.4 版本管理策略

项目采用语义化版本号（SemVer），通过 CHANGELOG.md 记录每个版本的变更。最新稳定版本信息可在 GitHub Releases 页面查看。每个技能的版本通过 `package.json` 中的 `version` 字段管理，支持依赖锁定。

---

## §5 功能详解

### 5.1 核心工程技能（Engineering — Core）

26 个核心工程技能覆盖软件开发的各个阶段：

**架构与设计**
- `architecture-design` — 系统架构设计决策
- `database-designer` — 数据模型与 Schema 设计
- `api-designer` — RESTful API 设计与版本管理

**前端开发**
- `frontend-dev` — React/Vue/Angular 最佳实践
- `css-architect` — CSS 架构与样式指南
- `accessibility-audit` — WCAG 合规性审计

**后端开发**
- `backend-dev` — 服务端架构与实现
- `microservices` — 微服务设计模式
- `api-security` — API 安全实践

**质量保障**
- `qa-strategy` — 测试策略制定
- `e2e-testing` — 端到端测试框架
- `performance-testing` — 性能基准与优化

**DevOps**
- `ci-cd-builder` — 持续集成/持续部署流水线
- `docker-best-practices` — Docker 容器化指南
- `kubernetes-deployment` — K8s 部署配置

### 5.2 Playwright Pro 测试技能

Playwright Pro 是面向 UI 自动化测试的一组高级技能，提供：

- **智能测试生成** — 根据页面行为自动生成测试用例
- **Flaky 测试修复** — 自动识别并修复不稳定的测试
- **框架迁移** — Cypress/Selenium 到 Playwright 的自动迁移
- **测试管理集成** — TestRail、BrowserStack 等平台对接
- **55+ 测试模板** — 覆盖常见测试场景

```bash
# 安装 Playwright Pro 技能
/plugin install playwright-pro@claude-code-skills
```

### 5.3 自我提升智能体（Self-Improving Agent）

项目里有一套专门让 AI 在多次对话中积累经验的技能：

| 技能 | 功能 | 效果 |
|------|------|------|
| `auto-memory-curation` | 自动整理对话记忆，提炼可复用的模式 | AI 记住关键决策上下文 |
| `pattern-promotion` | 将成功的解决模式提升为可复用技能 | 经验转化为能力 |
| `skill-extraction` | 从成功案例中提取新技能 | 持续扩展技能库 |
| `memory-health` | 检测并修复记忆中的过期/错误信息 | 保持知识准确性 |
| `self-review` | AI 主动复盘任务执行，识别改进点 | 自我优化闭环 |

### 5.4 产品经理技能（Product Skills）

14 个产品相关技能覆盖需求分析到实验设计的完整链条：

- `product-manager` — PRD 撰写与需求管理
- `ux-researcher` — 用户研究方法与洞察提取
- `analytics-setup` — 数据分析与指标体系
- `experiment-designer` — A/B 测试设计与分析
- `roadmap-communicator` — 技术方案与产品路线图的沟通

### 5.5 营销技能（Marketing Skills）

43 个营销技能覆盖数字营销全渠道：

**SEO 与搜索优化**
- `seo-auditor` — 全方位 SEO 审计，输出可执行的优化建议
- `keyword-researcher` — 关键词研究与竞争分析
- `technical-seo` — 技术性 SEO 问题诊断与修复

**内容营销**
- `content-strategist` — 内容策略规划
- `blog-writer` — 技术博客撰写模板
- `copywriter` — 转化率优化文案

**社交媒体**
- `social-media-strategy` — 多平台社交媒体运营
- `twitter-growth` — Twitter/X 增长策略

### 5.6 C-level 高管顾问技能

28 个高管顾问技能模拟不同职能高管的专业视角：

| 技能 | 模拟角色 | 核心决策维度 |
|------|---------|-------------|
| `cto-advisor` | CTO | 技术选型、架构决策、人才战略 |
| `cfo-advisor` | CFO | 财务规划、预算分配、投资回报 |
| `coo-advisor` | COO | 运营效率、流程优化、供应链 |
| `cmo-advisor` | CMO | 品牌策略、市场定位、获客成本 |
| `ciso-advisor` | CISO | 安全合规、风险控制 |

这些技能能够帮助 AI 在技术方案评审、商业计划审查等场景中提供多维度的高管级建议。

---

## §6 使用说明

### 6.1 环境要求

- **Python 3.8+**（用于运行工具脚本）
- **Git**（用于克隆仓库）
- **对应平台的 AI 编程工具**（Claude Code / Codex / Gemini CLI 等）

### 6.2 Claude Code 快速安装（推荐）

Claude Code 是项目官方推荐的平台，安装最简单：

```bash
# 1. 添加技能市场
/plugin marketplace add alirezarezvani/claude-skills

# 2. 安装全套技能（按领域分组安装）
/plugin install engineering-skills@claude-code-skills    # 26 个核心工程技能
/plugin install engineering-advanced-skills@claude-code-skills  # 30 个 POWERFUL 级技能
/plugin install product-skills@claude-code-skills      # 14 个产品技能
/plugin install marketing-skills@claude-code-skills     # 43 个营销技能
/plugin install ra-qm-skills@claude-code-skills         # 12 个监管/质量技能
/plugin install pm-skills@claude-code-skills           # 6 个项目管理技能
/plugin install c-level-skills@claude-code-skills     # 28 个 C-level 顾问技能
/plugin install business-growth-skills@claude-code-skills  # 4 个商业增长技能
/plugin install finance-skills@claude-code-skills      # 2 个金融技能

# 或安装单个技能
/plugin install skill-security-auditor@claude-code-skills
/plugin install playwright-pro@claude-code-skills
/plugin install self-improving-agent@claude-code-skills
```

### 6.3 OpenClaw 安装

```bash
# 一键安装脚本
bash <(curl -s https://raw.githubusercontent.com/alirezarezvani/claude-skills/main/scripts/openclaw-install.sh)
```

### 6.4 Gemini CLI 安装

```bash
# 克隆仓库
git clone https://github.com/alirezarezvani/claude-skills.git
cd claude-skills

# 运行安装脚本
./scripts/gemini-install.sh

# 在 Gemini CLI 中激活技能
> activate_skill(name="senior-architect")
```

### 6.5 OpenAI Codex 安装

```bash
# 使用 npx 安装
npx agent-skills-cli add alirezarezvani/claude-skills --agent codex

# 或手动克隆
git clone https://github.com/alirezarezvani/claude-skills.git
cd claude-skills
./scripts/codex-install.sh
```

### 6.6 Cursor / Aider 等工具的转换安装

```bash
# 1. 克隆仓库
git clone https://github.com/alirezarezvani/claude-skills.git
cd claude-skills

# 2. 转换为目标工具格式（以 Cursor 为例）
./scripts/convert.sh --tool cursor

# 3. 安装到项目
./scripts/install.sh --tool cursor --target /path/to/project

# 4. 验证安装
find .cursor/rules -name "*.mdc" | wc -l
# 应该输出 156（转换的技能总数）
```

**支持的工具转换**：

| 工具 | 命令 | 格式 |
|------|------|------|
| Cursor | `--tool cursor` | `.mdc` |
| Aider | `--tool aider` | `CONVENTIONS.md` |
| Windsurf | `--tool windsurf` | `.windsurf/skills/` |
| Kilo Code | `--tool kilocode` | `.kilocode/rules/` |
| OpenCode | `--tool opencode` | `.opencode/skills/` |
| Augment | `--tool augment` | `.augment/rules/` |
| Antigravity | `--tool antigravity` | `~/.gemini/antigravity/skills/` |

### 6.7 手动安装单个技能

如果只想安装特定技能而不是整个技能包：

```bash
# 1. 克隆仓库
git clone https://github.com/alirezarezvani/claude-skills.git
cd claude-skills

# 2. 复制技能文件夹到对应目录
# Claude Code
cp -r engineering ~/.claude/skills/

# OpenAI Codex
cp -r engineering ~/.codex/skills/

# 3. 验证
ls ~/.claude/skills/engineering/
```

---

## §7 开发扩展

### 7.1 技能开发规范

创建一个新技能需要遵循 `SKILL-AUTHORING-STANDARD.md` 中定义的规范。一个标准技能的结构：

```
<skill-name>/
├── SKILL.md           # 必须：技能核心定义
├── README.md          # 必须：人类可读的使用说明
├── CLAUDE.md         # 必须：AI 智能体的配置与指令
├── tools/            # 可选：Python 工具脚本
│   ├── script1.py
│   └── script2.sh
├── references/       # 可选：参考文档
│   ├── template.md
│   └── checklist.md
└── package.json      # 必须：技能元数据
```

### 7.2 SKILL.md 编写指南

SKILL.md 是技能的核心，需要包含：

```markdown
# 技能名称

## 概述
简要说明技能的用途和核心价值（2-3 句话）

## 前置条件
- 使用本技能前需要满足什么？
- 需要什么样的上下文？

## 适用场景
- 什么时候应该使用本技能？
- 什么情况下不应该使用？

## 执行流程

### 步骤 1：阶段名称
**做什么**：详细说明这一步的具体动作

**输入**：
- 什么信息/文件是必需的？

**输出**：
- 这一步应该产出什么？

**检查点**：
- 如何验证这一步完成了？

### 步骤 2：...

## 决策框架
遇到以下情况时如何判断：
- 情况 A vs 情况 B？
- 优先级的判断标准？

## 验证标准
任务完成前必须满足的条件列表

## 相关技能
- 本技能依赖的其他技能
- 可以与哪些技能配合使用
```

### 7.3 Python 工具编写规范

```python
#!/usr/bin/env python3
"""
技能名称 - 工具描述

功能：简明描述工具做什么
输入：命令行参数或标准输入
输出：结构化结果（JSON/TOML）
依赖：仅使用 Python 标准库
"""

import sys
import json
from pathlib import Path


def main():
    # 实现工具逻辑
    pass


if __name__ == "__main__":
    main()
```

**关键原则**：
- 必须使用 `#!/usr/bin/env python3` shebang
- 仅导入标准库模块
- 输入/输出使用 JSON 或纯文本
- 添加 `--help` 参数显示使用说明
- 脚本必须是可执行的（`chmod +x`）

### 7.4 package.json 元数据格式

```json
{
  "name": "skill-<skill-name>",
  "version": "1.0.0",
  "description": "技能的简短描述",
  "author": "你的 GitHub 用户名",
  "license": "MIT",
  "homepage": "https://github.com/alirezarezvani/claude-skills",
  "repository": {
    "type": "git",
    "url": "https://github.com/alirezarezvani/claude-skills"
  },
  "keywords": ["skill", "domain", "ai", "claude-code"],
  "engines": {
    "claude-code": ">=1.0.0"
  },
  "dependencies": {},
  "tools": [
    {
      "name": "script-name",
      "file": "tools/script.py",
      "description": "工具功能描述"
    }
  ]
}
```

### 7.5 提交技能到社区

如果希望将开发的技能贡献回主仓库：

1. Fork 仓库
2. 在对应目录下创建技能文件夹
3. 确保符合 `SKILL-AUTHORING-STANDARD.md` 规范
4. 添加测试（如果有）
5. 创建 Pull Request
6. 等待 Code Review

贡献者需要签署 CLA（Contributor License Agreement）。

### 7.6 技能评估与验证

项目提供了 SkillCheck 验证框架，用于确保技能质量：

```bash
# 在本地验证技能
./scripts/validate-skill.sh --skill <skill-name>

# 运行完整的技能测试套件
./scripts/run-tests.sh
```

---

## §8 最佳实践

### 8.1 技能选用策略

**按需加载**：不要一次性加载所有技能，这会增加 AI 的上下文负担。只安装当前任务需要的技能。

**领域组合**：某些领域技能天然搭配使用。例如：
- `database-designer` + `api-designer` + `backend-dev` 组合用于后端开发
- `seo-auditor` + `content-strategist` + `copywriter` 组合用于内容营销

**渐进式深化**：先安装核心技能，熟悉后再扩展到 POWERFUL 级和顾问级技能。

### 8.2 团队协作建议

**技能版本锁定**：在团队中共享技能时，使用 Git submodule 或特定的提交锁定版本：

```bash
# 添加为 submodule
git submodule add https://github.com/alirezarezvani/claude-skills.git vendor/claude-skills

# 切换到稳定版本
cd vendor/claude-skills
git checkout v2.1.1
```

**团队自定义技能库**：在主仓库基础上创建团队分支，添加公司特定技能：

```
team-claude-skills/
├── README.md
├── CLAUDE.md
├── skills/              # 团队共享技能
│   ├── internal-api-docs/
│   └── compliance-checker/
└── scripts/
    └── install.sh
```

### 8.3 性能优化

**按需转换**：不需要在所有工具中安装全套技能。使用 `convert.sh` 只转换你实际会用的工具格式。

**工具脚本缓存**：将常用工具脚本符号链接到 PATH 中，减少路径查找开销：

```bash
# 在 ~/.local/bin/ 创建符号链接
mkdir -p ~/.local/bin
ln -s ~/.claude/skills/engineering/tools/* ~/.local/bin/
```

### 8.4 故障排查

**技能不生效**：

1. 检查是否正确安装：`/plugin list`
2. 检查技能目录结构是否完整
3. 查看 Claude Code 日志：Settings → Debug → View Logs
4. 尝试重新安装：`/plugin uninstall <skill>` && `/plugin install <skill>`

**工具脚本报错**：

1. 检查 Python 版本：`python3 --version`（需要 3.8+）
2. 检查脚本权限：`ls -la tools/`
3. 手动运行脚本查看错误输出
4. 确认所有工具依赖已安装

---

## §9 常见问题

### Q1：技能和插件有什么区别？

在 Claude Code 语境下，"技能（Skills）"和"插件（Plugins）"基本等价，都指这种模块化的专家知识包。主要差异在于实现方式：
- **Skills** 通过 `/skill activate` 命令激活
- **Plugins** 通过 `/plugin` 命令管理

项目仓库同时包含两种实现，以兼容不同版本的 Claude Code。

### Q2：为什么部分工具的技能数量是 156 而不是 205？

Cursor、Aider、Windsurf 等工具不支持 Python 工具脚本，仅支持指令规则转换。因此：
- 可转换的技能总数：156 个（不含纯 Python 工具类技能）
- Claude Code / Codex / Gemini CLI：205 个完整技能
- 其他工具：156 个规则类技能

### Q3：技能会更新吗？如何同步更新？

项目通过 Git 追踪更新。你可以：

```bash
# 克隆仓库后
git pull origin main

# 或更新到特定版本
git fetch --all
git checkout v2.1.1

# 更新已安装的技能
./scripts/update-installed.sh
```

### Q4：可以离线使用这些技能吗？

可以。克隆仓库后，所有技能都存储在本地。离线环境下：
- 技能指令和参考文档完全可用
- Python 工具脚本完全可用（纯标准库，无网络依赖）
- 部分需要外部 API 的工具（如 `seo-auditor` 调用 Google PageSpeed API）需要网络

### Q5：如何报告技能的问题或提出改进建议？

- **GitHub Issues**：https://github.com/alirezarezvani/claude-skills/issues
- **功能请求**：提交 Feature Request 类型 Issue
- **Bug 报告**：提交 Bug 类型 Issue，包含复现步骤

### Q6：技能支持中文吗？

技能指令本身是英文编写，因为 AI 理解英文指令的效果最佳。但技能生成的内容可以是任何语言，包括中文。你可以在 `CLAUDE.md` 中指定输出语言偏好。

---

## §10 从哪里开始

Skills 不是装得越多越好。205 个技能全部加载会给 AI 带来很大的上下文负担，反而降低输出质量。按以下顺序逐步引入比较合理：

**第一步：工程核心（26 个）**。覆盖日常开发最常见的需求——架构设计、前后端、测试、CI/CD。这是最稳的起点。

**第二步：按角色扩展。** 如果你的日常工作包含 UI 测试，加 Playwright Pro；如果想让 AI 在多次对话中逐步改进自己的输出质量，加 Self-Improving Agent。

**第三步：跨域技能。** Product 和 Marketing 技能适合需要 AI 参与产品讨论或内容生产的团队。C-level 顾问技能在技术方案评审、架构决策等场景中有实际价值，但不必日常加载。

**谁该等一等**：如果团队刚接触 AI 编程工具，或者日常任务以简单 CRUD 为主，先装 Engineering Core 就够了。Powerful 级技能和 Agent 模板的收益要在你已经习惯了按技能驱动 AI 工作之后才会体现出来。

**开源协议与社区**：MIT 许可证，可自由使用和修改。仓库活跃度较高（8,200+ Stars，587 commits，截至 2026-03-26）。遇到问题走 GitHub Issues，Pull Request 需要签 CLA。

**链接资源**：

- GitHub 仓库：https://github.com/alirezarezvani/claude-skills
- 官方文档：https://alirezarezvani.github.io/claude-skills/
- SkillCheck 验证：https://getskillcheck.com

---

*基于仓库 commit 110348f (2026-03-26) 撰写*
