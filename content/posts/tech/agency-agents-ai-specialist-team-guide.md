---
title: "The Agency：147个专业化AI Agent组成的虚拟团队"
date: "2026-05-05T11:25:00+08:00"
slug: "agency-agents-ai-specialist-team-guide"
aliases:
  - "/posts/tech/agency-agents-complete-ai-agency-toolkit/"
  - "/posts/tech/the-agency-open-source-ai-agents-personas/"
  - "/posts/tech/ai-agent/agency-agents-multi-agent-framework-guide/"
description: "The Agency是一个包含147个专业化AI Agent的开源项目，覆盖工程、设计、销售、营销等12个领域。每个Agent拥有独特人格、专业流程和可衡量产出，可接入Claude Code、Cursor、Windsurf等主流AI编程工具。本文详解其架构设计、Agent分类、集成方式与实际应用场景。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Cursor", "多工具集成", "AI团队", "OpenClaw"]
---

# The Agency：147 个专业化 AI Agent 组成的虚拟团队

## 学习目标

读完本文后，你应当能够：

1. 说清 The Agency 与通用提示词模板在结构上的差异，并指出差异落在哪 5 个字段上。
2. 列出 12 个部门的边界，判断自己团队职能对应哪几个 Agent。
3. 在 Claude Code、Cursor、OpenClaw 三类工具中选一种完成首次安装，并解释为什么选这一种。
4. 复述一次"工程部 Agent 审查 PR"的任务流转路径，说明每个环节的输入和输出。
5. 根据团队规模和现有工具栈，给出一个分阶段的采用顺序。

## 目录

- [项目判断](#项目判断)
- [核心设计理念](#核心设计理念)
- [12 个专业部门一览](#12-个专业部门一览)
- [快速开始](#快速开始)
- [工程部 Agent 详解](#工程部-agent-详解)
- [多工具集成架构](#多工具集成架构)
- [任务如何流过系统：一次 PR 审查的完整路径](#任务如何流过系统一次-pr-审查的完整路径)
- [应用场景示例](#应用场景示例)
- [适用场景与边界](#适用场景与边界)
- [常见问题与错误排查](#常见问题与错误排查)
- [自测问题](#自测问题)
- [采用顺序与决策建议](#采用顺序与决策建议)

---

## 项目判断

[The Agency](https://github.com/msitarzewski/agency-agents) 把 AI Agent（人工智能智能体）从"一个通用助手"拆成 147 个岗位，每个岗位是一份 Markdown 文件，定义人格、使命、工作流、交付物和记忆策略。它不解决模型能力问题，解决的是"如何让同一个底层模型在不同专业场景里稳定输出符合该岗位预期的结果"。

这套仓库的实际用法不是一次装满 147 个 Agent，而是按团队职能挑几个岗位，让它们独立运行或按 pipeline（流水线）串联，再通过配置文件替换模型、输出目录和外部凭据。把它理解成一组可组合的岗位库更贴近真实用法——"超大号提示词包"的标签会让人忽略它的工程约束。

**项目数据（截至 2026 年 5 月）：**
- GitHub Stars：1,189
- Agent 总数：147 个
- 覆盖领域：12 个（工程、设计、销售、营销、产品、项目管理、测试、支持、空间计算、专业化、财务、游戏开发）
- 支持工具：Claude Code、GitHub Copilot、Antigravity、OpenClaw、Cursor、Aider、Windsurf 等 11 种主流 AI 工具
- 开源协议：MIT

本文面向已经在用 AI 编程工具、想把 Agent 能力按职能拆开使用的开发者、产品经理和技术负责人。

---

## 核心设计理念

### 从通用提示词到专业 Agent 的范式转变

传统 AI Agent 方案通常用一个提示词模板应对各种场景。The Agency 换了个思路：按岗位拆分，每个 Agent 都是某个细分领域的深度专家，定义里包含 5 个固定字段：

| 字段 | 含义 | 作用 |
|------|------|------|
| 人格（Personality） | 沟通风格和思维方式 | 让输出语气符合岗位身份，例如销售工程师和后端架构师的口吻不同 |
| 核心使命（Mission） | 职责边界和成功标准 | 限制 Agent 不会越界回答 |
| 工作流程（Workflow） | 经过生产环境验证的执行步骤 | 把"该怎么做这件事"固化成步骤，减少模型自由发挥 |
| 交付物（Deliverables） | 可量化的具体产出 | 把"给个建议"变成"给一份带字段的结构化文档" |
| 学习记忆（Memory） | 持续改进的能力积累 | 跨会话保留项目上下文 |

这 5 个字段是 The Agency 与通用提示词模板的核心差异点。通用模板通常只有"角色 + 任务"两层，The Agency 多了工作流、交付物和记忆三层约束。

---

## 12 个专业部门一览

The Agency 的组织架构模拟了真实公司结构，按职能拆成 12 个部门：

| 部门 | Agent 数量 | 代表角色 |
|------|-----------|---------|
| 💻 工程部 | 25+ | 前端开发者、后端架构师、AI 工程师、安全工程师 |
| 🎨 设计部 | 8 | UI 设计师、UX 研究员、品牌守护者 |
| 💼 销售部 | 10 | 外展策略师、交易策略师、销售工程师 |
| 📢 市场部 | 30+ | 增长黑客、内容创作者、Twitter 运营、知乎专家 |
| 📊 产品部 | 5 | Sprint 优先排序器、趋势研究员、行为推动引擎 |
| 🎬 项目管理 | 7 | 制片人、项目牧羊人、实验追踪员 |
| 🧪 测试部 | 9 | 证据收集员、性能基准测试员、API 测试员 |
| 🛟 支持部 | 7 | 支持响应员、分析报告员、财务追踪员 |
| 🥽 空间计算 | 6 | XR 界面架构师、visionOS 工程师 |
| 🎯 专业部 | 40+ | MCP 构建器、智能合同审计员、Salesforce 架构师 |
| 💵 财务部 | 5 | 簿记员、财务分析师、税务策略师 |
| 🎮 游戏开发 | 20+ | Unity/Unreal/Godot 专项工程师 |

> 表中数字为各部门 README 列出的岗位数（截至 2026 年 5 月主分支），加总约 172，高于仓库标题宣称的 147 个——部分 Agent 同时挂靠多个部门（例如 Security Engineer 同时出现在工程部和专业部），按部门计数会重复。仓库标题的 147 是去重后的总数。

12 个部门加起来覆盖了从代码到法务的常见岗位。其中工程部、市场部和专业部是数量最多的三个部门，分别对应"写代码""做增长""处理垂直领域专家任务"三类高频需求。专业部里的 MCP（Model Context Protocol，模型上下文协议）构建器和智能合同审计员是这套仓库里比较少见的岗位，前者负责把外部工具封装成 MCP 服务，后者负责审计 EVM（Ethereum Virtual Machine，以太坊虚拟机）合约的 gas（链上燃料费）消耗和安全漏洞。

---

## 快速开始

### 方式一：接入 Claude Code（推荐）

```bash
# 克隆仓库
git clone https://github.com/msitarzewski/agency-agents.git
cd agency-agents

# 安装所有Agent到Claude Code目录
./scripts/install.sh --tool claude-code

# 在Claude Code中激活
# "Hey Claude, activate Frontend Developer mode and help me build a React component"
```

推荐 Claude Code 的原因是它的 Agent 文件直接落在 `~/.claude/agents/` 下，不需要额外转换层，调试时改 Markdown 就能生效。

### 方式二：接 OpenClaw

```bash
# 先生成OpenClaw格式文件
./scripts/convert.sh --tool openclaw

# 安装
./scripts/install.sh --tool openclaw

# 重启OpenClaw网关（示意命令，具体子命令以 OpenClaw 版本为准）
openclaw gateway restart
```

Agent 会以独立 workspace（工作区）形式出现在 `~/.openclaw/agency-agents/` 下，每个 Agent 拥有自己的 `SOUL.md`、`AGENTS.md` 和 `IDENTITY.md`。

### 方式三：接入 Cursor

```bash
cd your-project
# 实际路径以仓库克隆位置为准，例如 ~/projects/agency-agents/scripts/install.sh
/path/to/agency-agents/scripts/install.sh --tool cursor
```

Agent 转化为 `.mdc` 规则文件存于 `.cursor/rules/` 目录。

---

## 工程部 Agent 详解

工程部是整个仓库最核心的部分，包含 25+ 个专业化工程师角色。

### 核心技术 Agent

**Frontend Developer** — 专精 React/Vue/Angular、UI 实现、Web Vitals 优化

```text
使用场景：现代Web应用开发、像素级精确UI实现、Core Web Vitals优化
```

**Backend Architect** — API 设计、数据库架构、可扩展性规划

```text
使用场景：服务端系统设计、微服务架构、云基础设施规划
```

**AI Engineer** — ML 模型部署、流水线构建、AI 集成

```text
使用场景：机器学习功能开发、数据管道、LLM应用集成
```

**Security Engineer** — 威胁建模、安全代码审计、安全架构

```text
使用场景：应用安全评估、漏洞分析、安全CI/CD设计
```

**Autonomous Optimization Architect** — LLM 路由、成本优化、影子测试

```text
使用场景：需要智能API选择和成本护栏的自主系统
```

### 特殊领域 Agent

| Agent | 专长 | 使用场景 |
|-------|------|---------|
| Embedded Firmware Engineer | ESP32/STM32 bare-metal | 嵌入式系统、物联网设备 |
| Solidity Smart Contract Engineer | EVM 合约、gas 优化 | DeFi 协议、安全智能合约 |
| Codebase Onboarding Engineer | 源码阅读、代码路径追踪 | 新人快速熟悉陌生代码库 |
| Feishu Integration Developer | 飞书开放平台、机器人 | 飞书生态集成开发 |
| Email Intelligence Engineer | 邮件解析、MIME 提取 | 将邮件线程转化为结构化上下文 |

特殊领域 Agent 的价值在于覆盖了通用 LLM 不擅长的窄场景。例如 Solidity Smart Contract Engineer 会把 gas 优化和重入攻击检查写进工作流，而不是泛泛地"审查合约"——这种窄场景约束是通用提示词做不到的。

---

## 多工具集成架构

The Agency 的集成脚本支持 11 种工具，通过 `convert.sh` 和 `install.sh` 两个脚本统一管理：

```bash
# Step 1: 生成各工具对应的格式文件
./scripts/convert.sh              # 串行生成
./scripts/convert.sh --parallel  # 并行生成（更快）

# Step 2: 安装（交互式，auto-detect已安装的工具）
./scripts/install.sh
```

安装脚本会扫描系统，自动检测已安装的工具，以复选框 UI 呈现。`convert.sh` 负责把统一的 Agent 定义转换成各工具需要的格式（Claude Code 用 `.md`，Cursor 用 `.mdc`，OpenClaw 用 `SOUL.md` + `AGENTS.md`），`install.sh` 负责把转换后的文件落到对应工具的配置目录。两层分离的好处是新增工具支持只需要写一个新的 converter，不用动安装逻辑。

---

## 任务如何流过系统：一次 PR 审查的完整路径

为了说明 Agent 之间如何配合，下面用一个具体任务串起来：用工程部 Agent 审查一个新增支付接口的 PR。

```text
任务：审查 PR #142（新增 /api/checkout 支付接口）

步骤 1：Codebase Onboarding Engineer
  输入：PR diff + 仓库结构
  输出：一份"这个改动影响了哪些模块"的路径报告
  动作：识别出 checkout 路由、订单模型、支付网关适配器三处变更

步骤 2：Backend Architect
  输入：步骤 1 的路径报告 + PR diff
  输出：API 设计评审（路由命名、错误码、幂等性）
  动作：指出 /api/checkout 缺少 idempotency key

步骤 3：Security Engineer
  输入：步骤 2 的评审 + PR diff
  输出：威胁建模报告（关注支付金额篡改、重放攻击）
  动作：标记 amount 字段未做服务端校验

步骤 4：Autonomous Optimization Architect
  输入：步骤 2 和 3 的报告
  输出：成本与路由建议（哪些检查走小模型，哪些走大模型）
  动作：建议金额校验走 GPT-4o，威胁建模走 Claude Opus

步骤 5：Reality Checker（测试部）
  输入：前面所有报告
  输出：验收清单 + 阻断项
  动作：列出 3 个必须修复的阻断项和 5 个建议项
```

这个流程里每个 Agent 的输入都来自上游的交付物，输出又成为下游的输入。Agent 之间不直接通信，靠 Markdown 文件传递上下文。这意味着你可以只挑其中两三个 Agent 用，也可以把整条链路跑完；中间任何一步的输出都可以单独存档，留作后续审计。

---

## 应用场景示例

### 场景一：构建创业公司 MVP

**团队配置：**
1. 🎨 Frontend Developer — 构建 React 应用
2. 🏗️ Backend Architect — 设计 API 和数据库
3. 🚀 Growth Hacker — 规划用户增长策略
4. ⚡ Rapid Prototyper — 快速迭代
5. 🔍 Reality Checker — 上线前质量验证

这个配置覆盖了从开发到上线的主链路。如果团队只有一个人，可以先跑 Frontend Developer 和 Backend Architect 两个，把 MVP 的代码骨架搭出来，再按需要补 Growth Hacker 和 Reality Checker。

### 场景二：多渠道营销活动

**团队配置：**
1. 📝 Content Creator — 活动内容策划
2. 🐦 Twitter Engager — Twitter 策略与执行
3. 🤝 Reddit Community Builder — Reddit 社区运营
4. 📊 Analytics Reporter — 效果追踪优化

营销场景下，Content Creator 的输出会被 Twitter Engager 和 Reddit Community Builder 各自改写一次，适配不同平台的语气。Analytics Reporter 在最后接入，把各渠道数据汇总成一份带归因的报告。

---

## 适用场景与边界

### 适合的场景
- 需要在不同专业领域快速获得专家级 AI 辅助
- 已使用 Claude Code/Cursor/Windsurf 等 AI 编程工具，希望按职能拆分 Agent 能力
- 需要组建临时 AI 团队完成特定项目
- 希望 AI 输出更专业化，减少泛泛建议

### 边界与局限
- Agent 本身是 Markdown 文件定义的人格和工作流，不含实际执行代码
- 输出质量依赖底层 AI 模型能力，需自备 API Key
- 部分细分 Agent（如法律、医疗）仅作参考，不能替代专业咨询
- 147 个 Agent 全部安装会带来较大的 token（令牌）消耗，建议按需安装

---

## 常见问题与错误排查

### Q1：安装后 Agent 没有出现在工具里

排查顺序：
1. 检查对应工具的配置目录是否有文件（Claude Code 看 `~/.claude/agents/`，Cursor 看 `.cursor/rules/`）
2. 确认 `convert.sh` 是否执行成功，看终端有没有报错
3. 重启对应工具或网关（OpenClaw 需要执行 `openclaw gateway restart`）

### Q2：Agent 输出和预期不符

常见原因：
- 底层模型能力不足：复杂岗位（如 Backend Architect）建议用 Claude Opus 或 GPT-4 级别模型
- 上下文不够：Agent 的工作流依赖项目上下文，首次使用时先让 Codebase Onboarding Engineer 跑一遍
- Agent 被串错了顺序：pipeline 模式下，上游交付物没传给下游，导致下游 Agent 缺信息

### Q3：token 消耗过大

控制方法：
- 按需安装，不要一次装满 147 个
- 用 Autonomous Optimization Architect 做路由，把简单检查交给小模型
- 在 Agent 定义里限制输出长度，避免长篇大论

### Q4：能否自定义 Agent

可以。Agent 本质是 Markdown 文件，复制一份现有 Agent，修改人格、使命、工作流和交付物字段即可。建议从相近岗位改起，例如从 Backend Architect 改出 Platform Engineer，比从零写一份更稳。

---

## 自测问题

读完本文后，用以下问题自测：

1. The Agency 与通用提示词模板的差异落在哪 5 个字段上？每个字段分别约束了什么？
2. PR 审查流程中，Codebase Onboarding Engineer 的输出被谁消费？如果跳过这一步，下游 Agent 会缺什么信息？
3. 工程部、市场部、专业部是数量最多的三个部门，分别对应哪三类高频需求？你的团队职能落在哪几个部门？
4. 在 Claude Code、Cursor、OpenClaw 三类工具中，你的团队会选哪一种？为什么？

答不出的章节建议重读，特别是"核心设计理念"和"任务如何流过系统"两节。

---

## 采用顺序与决策建议

如果你打算在团队里用 The Agency，建议按以下顺序推进。

**第一阶段：验证流程（1-2 周）**
- 装工程部的 3 个核心 Agent：Frontend Developer、Backend Architect、Codebase Onboarding Engineer
- 在一个真实小项目上跑通"读代码 → 写代码 → 审代码"的闭环
- 目标是确认 Agent 文件格式和你的工具链能配合，而不是看产出质量

**第二阶段：按职能扩展（2-4 周）**
- 根据团队职能补 Agent：有测试团队就装测试部，有增长需求就装市场部
- 把 pipeline 串起来，让 Agent 之间能传递交付物
- 这阶段开始关注产出质量，调整 Agent 定义里的工作流步骤

**第三阶段：定制化（4 周以后）**
- 基于现有 Agent 改造出团队专属岗位
- 用 Autonomous Optimization Architect 做模型路由，控制成本
- 把记忆策略接上团队的知识库

**谁该先用、谁可以等等：**
- 已经在用 Claude Code 或 Cursor 的团队：可以直接进第一阶段
- 还在用通用提示词、没有固定 AI 编程工具的团队：先选定工具，再考虑 The Agency
- 只有非工程需求（纯营销、纯财务）的团队：可以只装对应部门的 Agent，不必装工程部

如果你团队的痛点是同一个模型在不同任务上表现波动大，The Agency 的岗位拆分思路值得试一试。

---

**参考链接：**
- GitHub：https://github.com/msitarzewski/agency-agents
- 官方文档：https://github.com/msitarzewski/agency-agents#readme
