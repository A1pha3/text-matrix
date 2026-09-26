---
title: "Agent Skills：addyosmani 的生产级 AI 编程工程技能框架"
date: "2026-04-12T18:02:00+08:00"
lastmod: "2026-09-20T12:00:00+08:00"
slug: agent-skills-addyosmani-production-engineering-guide
github_repo: "addyosmani/agent-skills"
source_key: "gh:addyosmani/agent-skills"
description: "9.7 万 Stars 的生产级工程技能框架——25 个结构化技能和 9 条 slash 命令，强制 AI 按 Define→Plan→Build→Verify→Review→Ship 的完整生命周期工作。"
draft: false
categories: ["技术笔记"]
tags: ["AI 编程", "Claude Code"]
---

# Agent Skills：addyosmani 的生产级 AI 编程工程技能框架

## 开篇判断

AI 编码 Agent 有个习惯：拿到需求直接写代码，跳过规格说明、省略测试、忽略安全审查。做原型够用，放到生产环境就暴露问题——没有测试的代码不敢重构，没有审查的代码藏着边界缺陷，没有 Spec 的项目在需求变更时失控。

Agent Skills 把这套习惯改过来。它由前 Google 总监 Addy Osmani 开源（GitHub 资料自述：曾负责 Gemini 与 Google Cloud），把资深工程师在真实项目中的工作流封装成 25 个结构化技能和 9 条命令，强制 AI 按 Define → Plan → Build → Verify → Review → Ship 的完整生命周期工作。

用 Claude Code 或 Cursor 的团队最常遇到一个困境：AI 产出的代码能跑，但缺测试、没审查、没有 Spec。Agent Skills 把这些环节写成 AI 可执行的步骤，让每次产出都走同一套流程。如果 AI 想跳过测试或审查，内置的 anti-rationalization 表会把它拉回流程内。

## 项目概述

### 这套框架在解决什么问题

Agent Skills 的做法是把工程实践写成 AI 可执行的流程：每个技能是一组带步骤、检查点和退出条件的指令，AI 必须按流程走完才能产出代码。技能文件本身是纯 Markdown，通过 slash 命令和上下文感知机制被 Claude Code、Gemini CLI 等工具加载后，就变成了 AI 的工作流约束。

### 核心数据

| 指标 | 数值 |
|------|--------|
| GitHub Stars | 97.1k |
| Forks | 10.2k |
| 许可证 | MIT |
| 主要语言 | JavaScript |
| 技能数量 | 25 个（24 个生命周期技能 + 1 个元技能） |
| 命令数量 | 9 条 |
| 开发者 | Addy Osmani（前 Google 总监，曾负责 Gemini 与 Google Cloud） |
| 仓库地址 | https://github.com/addyosmani/agent-skills |

> 数据采集于 2026-09-20。仓库技能数量会随版本迭代变化，最新数量以仓库 README 为准。

---

## 系统总览：三层组件如何配合

Agent Skills 由三层组件构成。三层的关系决定了什么时候该手动输入命令、什么时候 AI 会自己激活技能。

### 三层组件

| 层级 | 数量 | 职责 | 触发方式 |
|------|------|------|----------|
| **slash 命令** | 9 条 | 开发生命周期的入口点 | 用户手动输入 |
| **技能（Skills）** | 25 个 | 具体工程流程的执行者 | 命令激活或上下文自动激活 |
| **参考清单（References）** | 7 份 | 技能按需加载的补充材料 | 技能内部引用 |

slash 命令是用户接触框架的入口，每条命令激活一组技能，技能在执行过程中按需加载参考清单。三层之间是"调度 → 执行 → 补充"的链式关系，上一层驱动下一层。此外仓库还带 4 个 Agent Personas（code-reviewer、test-engineer、security-auditor、web-performance-auditor），供 `/ship` 等命令做专项审查时并行调用，本文后面单独介绍。

### 6 阶段开发周期

```text
Agent Skills 6 阶段开发周期

┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐
│ Define │───▶│ Plan   │───▶│ Build  │───▶│ Verify │───▶│ Review │───▶│ Ship   │
│ /spec  │    │ /plan  │    │ /build │    │ /test  │    │ /review│    │ /ship  │
└────────┘    └────────┘    └────────┘    └────────┘    └────────┘    └────────┘
     │                              ▲           │           │
     └────────── Refine 循环 ──────┘───────────┘───────────┘
                   （测试失败、审查不通过时回退）
```

6 条生命周期命令对应 6 个阶段，另外三条各有归属：`/constraints` 与 `/spec` 同属 Define——在动手编码前把项目的质量标准谈好并写成 `CONSTRAINTS.md`；`/code-simplify` 属于 Refine 循环，可在 Build、Verify、Review 任一阶段触发；`/webperf` 用于审查阶段的 Web 性能审计。

### 自动技能激活机制

除了手动输入命令，Agent Skills 还支持上下文感知的自动激活：当 AI 检测到当前任务匹配某个技能的触发条件时，会自动加载该技能的流程。

```text
触发场景                → 自动激活的技能
─────────────────────────────────────────────
设计 API 或模块接口      → api-and-interface-design
构建或修改界面           → frontend-ui-engineering
实现逻辑、修复 bug       → test-driven-development
性能要求或怀疑性能回归   → performance-optimization
处理用户输入或认证       → security-and-hardening
测试失败或构建中断       → debugging-and-error-recovery
```

用户不需要记住所有技能名称，描述清楚任务后 AI 会自动选择合适的工程流程。

---

## 6 阶段开发生命周期

这一节聚焦 6 个阶段的名字和推进条件。读完应该能判断手头的项目处于哪个阶段、缺少哪个阶段的产物。

### 阶段详解

| 阶段 | 命令 | 核心原则 | 关键产物 | 常用技能 |
|------|------|----------|----------|----------|
| **Define** | `/spec` | Spec before code（先写规格再写代码） | SPEC.md（产品需求文档） | spec-driven-development, interview-me, idea-refine, constraint-driven-development |
| **Plan** | `/plan` | Small, atomic tasks（小而原子的任务） | 任务分解清单 | planning-and-task-breakdown |
| **Build** | `/build` | One slice at a time（一次一个垂直切片） | 可运行代码 | incremental-implementation, test-driven-development, context-engineering |
| **Verify** | `/test` | Tests are proof（测试即证明） | 测试通过、覆盖率达标 | test-driven-development, browser-testing-with-devtools, debugging-and-error-recovery |
| **Review** | `/review` | Improve code health（提升代码健康度） | 审查报告、修复记录 | code-review-and-quality, security-and-hardening, performance-optimization |
| **Ship** | `/ship` | Faster is safer（小步快跑更安全） | 部署上线、监控就绪 | shipping-and-launch, ci-cd-and-automation, git-workflow-and-versioning |

### Refine 循环

每个阶段都支持回退：

- 测试失败 → 返回 Build 阶段修复，重新进入 Verify
- 审查发现安全漏洞 → 返回 Build 阶段重做相关模块
- Spec 在实现中发现不可行 → 返回 Define 阶段更新 SPEC.md

`/code-simplify` 命令属于 Refine 循环，用于在任意阶段简化复杂代码，核心原则是 Clarity over cleverness（清晰优于巧妙）。

---

## 9 条 slash 命令

### 命令一览

| 命令 | 阶段 | 核心原则 | 使用场景 |
|------|------|----------|----------|
| `/spec` | Define | Spec before code | 开始新项目、新功能或重大变更 |
| `/constraints` | Define | Decide it once, enforce it everywhere | 质量标准没写下来，或 AI 靠压掉检查来"变绿" |
| `/plan` | Plan | Small, atomic tasks | 已有 Spec，需要可执行的任务分解 |
| `/build` | Build | One slice at a time | 任何涉及多文件的变更 |
| `/test` | Verify | Tests are proof | 实现逻辑、修复 bug 或变更行为 |
| `/review` | Review | Improve code health | 代码审查、合并前 |
| `/webperf` | Review | Measure before you optimize（先测量再优化） | 审计 Web 性能 |
| `/code-simplify` | Refine | Clarity over cleverness | 代码能跑但可读性差或复杂度过高 |
| `/ship` | Ship | Faster is safer | 准备部署到生产环境 |

### 命令的执行逻辑

每条命令背后是一个工作流调度器，不是单条提示词。以 `/build` 为例，它有两种模式：

- **默认模式**（一次一个任务）：从计划里取下一个待办任务，走完一个固定循环——读任务的验收标准 → 加载相关代码上下文 → 先写一个失败的测试（RED）→ 写最小实现让测试通过（GREEN）→ 跑全量测试防回归 → 跑构建验证编译 → 提交 → 标记任务完成，然后停下。人在任务之间把关。
- **`/build auto` 模式**（整计划连跑）：前提是存在 `SPEC.md`（仓库根目录、docs/ 或 spec/ 下），并确认工作区干净；没有计划就先调 `planning-and-task-breakdown` 生成一份；然后只需人批准一次计划，AI 就按依赖顺序自动执行每个任务——每个任务仍然走红-绿-重构并单独提交，任何一点都可以干净回滚。遇到测试修不好、Spec 有歧义、或高风险不可逆操作（鉴权、数据迁移、支付、删除）时停下来问人，而不是硬闯。

`/constraints` 命令也值得单独说。它先读仓库里能读到的信息（技术栈、测试工具、lint 配置、当前覆盖率、CI 工作流），再最多问四个问题——每个问题都带默认值，回答"不知道"也能得到一套可用配置——然后生成 `CONSTRAINTS.md`：保底标准、强制数字、只实测不设目标的指标、带负责人和过期日期的例外表。接着给每个维度装上事实标准的工具（Semgrep 扫代码、gitleaks 查密钥、osv-scanner 查依赖、axe-core 查无障碍、Lighthouse 查 Web Vitals），并按"检查成本"放置触发点：秒级检查放在编辑循环，分钟级放在任务结束，其余放到 review 和 CI。它还有三个子命令：`/constraints check` 对当前分支跑一遍约束，`/constraints guard` 检查 diff 里有没有被弱化的标准（调低的阈值、跳过或删除的测试、新增的压制注释），`/constraints ratchet` 把今天的实测值记为不许跌破的下限。

如果 AI 在执行过程中试图跳步（例如"测试稍后再加"），anti-rationalization 表会触发，强制 AI 回到流程内。

---

## 25 个结构化技能

### Meta 阶段

#### using-agent-skills

| 属性 | 说明 |
|------|------|
| 用途 | 将 incoming work 映射到合适的技能工作流，定义共享操作规则 |
| 使用场景 | 开始会话或不确定该用哪个技能时 |

### Define 阶段技能

#### interview-me

| 属性 | 说明 |
|------|------|
| 用途 | 通过一次一个问题的访谈，提取用户真正想要的东西，直到约 95% 置信度 |
| 使用场景 | 需求不明确，或用户主动说"interview me"/"grill me" |

#### idea-refine

| 属性 | 说明 |
|------|------|
| 用途 | 用结构化发散/收敛思维，将模糊想法转化为具体提案 |
| 使用场景 | 有一个粗略概念需要探索 |

#### spec-driven-development

| 属性 | 说明 |
|------|------|
| 用途 | 编写覆盖目标、命令、结构、代码风格、测试和边界的规格文档，保存为 SPEC.md |
| 使用场景 | 开始新项目、功能或重大变更 |

#### constraint-driven-development

| 属性 | 说明 |
|------|------|
| 用途 | 把项目的质量标准写成 CONSTRAINTS.md 书面契约并盯住 diff，防止 AI 悄悄降标——新增 `@ts-ignore`、`eslint-disable` 压制注释，跳过或删除测试，抽掉断言，调低阈值 |
| 使用场景 | 没有书面质量标准；想给无障碍、性能、覆盖率等维度设门槛但不知道选什么数；AI 反复靠压掉检查换绿灯；跑 `/build auto` 这类自动循环之前 |

### Plan 阶段技能

#### planning-and-task-breakdown

| 属性 | 说明 |
|------|------|
| 用途 | 将 Spec 分解为小而可验证的任务，含验收标准和依赖排序 |
| 使用场景 | 已有 Spec，需要可执行单元 |

### Build 阶段技能

#### incremental-implementation

| 属性 | 说明 |
|------|------|
| 核心方法 | 薄垂直切片——实现、测试、验证、提交 |
| 工程实践 | 功能开关（feature flags）、安全默认值、回滚友好变更 |
| 使用场景 | 任何涉及多文件的变更 |

#### test-driven-development

| 属性 | 说明 |
|------|------|
| 核心方法 | 红-绿-重构，测试金字塔（80/15/5：单元/集成/端到端） |
| 测试原则 | DAMP（Descriptive And Meaningful Phrases，描述性、有意义的表述）优先于 DRY（Don't Repeat Yourself，不要重复自己）；Beyonce Rule（碧昂丝规则：喜欢它，就给它配个测试——自己引入的变更由自己的测试兜底，基础设施变更和重构不负责抓你的 bug） |
| 使用场景 | 实现逻辑、修复 bug 或变更行为 |

#### context-engineering

| 属性 | 说明 |
|------|------|
| 核心方法 | 在正确时间提供正确信息 |
| 技术手段 | 规则文件、上下文打包、MCP（Model Context Protocol，模型上下文协议）集成 |
| 使用场景 | 开始会话、切换任务或输出质量下降 |

#### source-driven-development

| 属性 | 说明 |
|------|------|
| 用途 | 每个框架决策都基于官方文档——验证、引用来源、标记未验证项 |
| 使用场景 | 需要权威、有来源引用的框架或库代码 |

#### doubt-driven-development

| 属性 | 说明 |
|------|------|
| 用途 | 对每个非平凡决策进行对抗式新鲜上下文审查——CLAIM → EXTRACT → DOUBT → RECONCILE → STOP，必要时经用户授权升级到跨模型交叉审查 |
| 使用场景 | 高风险场景（生产、安全、不可逆）、不熟悉的代码、自信输出比事后调试更便宜 |

#### frontend-ui-engineering

| 属性 | 说明 |
|------|------|
| 用途 | 组件架构、设计系统、状态管理、响应式设计、WCAG 2.1 AA 无障碍 |
| 使用场景 | 构建或修改用户界面 |

#### api-and-interface-design

| 属性 | 说明 |
|------|------|
| 用途 | 契约优先设计、Hyrum's Law（海勒姆定律：API 的所有可观察行为都会被依赖）、One-Version Rule（单版本规则）、错误语义、边界验证 |
| 使用场景 | 设计 API、模块边界或公共接口 |

### Verify 阶段技能

#### browser-testing-with-devtools

| 属性 | 说明 |
|------|------|
| 用途 | 通过 Chrome DevTools MCP 获取实时运行时数据——DOM 检查、控制台日志、网络追踪、性能分析 |
| 使用场景 | 构建或调试任何在浏览器中运行的代码 |

#### debugging-and-error-recovery

| 属性 | 说明 |
|------|------|
| 用途 | 五步分诊：复现、定位、缩小、修复、防护；Stop-the-line 规则、安全回退 |
| 使用场景 | 测试失败、构建中断或行为异常 |

### Review 阶段技能

#### code-review-and-quality

| 属性 | 说明 |
|------|------|
| 用途 | 五轴审查、变更规模控制（约 100 行）、严重性标签（Nit/Optional/FYI）、审查速度规范、拆分策略 |
| 使用场景 | 合并任何变更前 |

#### code-simplification

| 属性 | 说明 |
|------|------|
| 用途 | Chesterton's Fence（切斯特顿围栏：拆除前先弄清楚为什么存在）、Rule of 500（500 行规则）、在保持行为不变的前提下降低复杂度 |
| 使用场景 | 代码能跑但比应有状态更难读或难维护 |

#### security-and-hardening

| 属性 | 说明 |
|------|------|
| 用途 | OWASP Top 10 防护、认证模式、密钥管理、依赖审计、三层边界系统 |
| 使用场景 | 处理用户输入、认证、数据存储或外部集成 |

#### performance-optimization

| 属性 | 说明 |
|------|------|
| 用途 | 测量优先——Core Web Vitals 目标、性能分析工作流、包体积分析、反模式检测 |
| 使用场景 | 存在性能要求或怀疑性能回归 |

### Ship 阶段技能

#### git-workflow-and-versioning

| 属性 | 说明 |
|------|------|
| 用途 | Trunk-based 开发、原子提交、变更规模控制（约 100 行）、commit-as-save-point 模式 |
| 使用场景 | 任何代码变更（始终适用） |

#### ci-cd-and-automation

| 属性 | 说明 |
|------|------|
| 用途 | Shift Left（左移）、Faster is Safer、功能开关、质量门控流水线、失败反馈循环 |
| 使用场景 | 设置或修改构建和部署流水线 |

#### deprecation-and-migration

| 属性 | 说明 |
|------|------|
| 用途 | Code-as-liability 思维（代码即负债）、强制 vs 建议性弃用、迁移模式、僵尸代码清除 |
| 使用场景 | 移除旧系统、迁移用户或下线功能 |

#### documentation-and-adrs

| 属性 | 说明 |
|------|------|
| 用途 | ADR（Architecture Decision Records，架构决策记录）、API 文档、内嵌文档标准——记录"为什么" |
| 使用场景 | 做架构决策、变更 API 或发布功能 |

#### shipping-and-launch

| 属性 | 说明 |
|------|------|
| 用途 | 上线前清单、功能开关生命周期、灰度发布、回滚流程、监控配置 |
| 使用场景 | 准备部署到生产环境 |

#### observability-and-instrumentation

| 属性 | 说明 |
|------|------|
| 用途 | 结构化日志、RED 指标、OpenTelemetry 链路追踪、基于症状的告警——边构建边埋点 |
| 使用场景 | 添加可观测性，或为任何上生产的内容补监控 |

---

## Agent Personas：专项审查角色

除了技能，仓库还带 4 个预配置的审查角色（`agents/` 目录）。`/ship` 会把它们并行展开做专项审查，再把结果合并成一个 go/no-go 决策；`/webperf` 背后就是 web-performance-auditor 这个角色。

| Agent | 角色 | 审查视角 |
|-------|------|----------|
| code-reviewer | Senior Staff Engineer | 五轴代码审查，标准是"一位 staff engineer 会不会批准这次提交" |
| test-engineer | QA Specialist | 测试策略、覆盖率分析、Prove-It 模式 |
| security-auditor | Security Engineer | 漏洞检测、威胁建模、OWASP 评估 |
| web-performance-auditor | Web Performance Engineer | Core Web Vitals 审计，Quick/Deep 两种模式，附带"指标诚实"规则 |

这套设计缓解了单角色审查的盲区：一个上下文既当运动员又当裁判，容易对自己写的代码手下留情；四个角色各带一份独立的判断标准，互为制约。官方还规定了编排纪律——"personas don't invoke personas"，角色之间不互相调用，由命令层统一调度（详见 `references/orchestration-patterns.md`）。

## 任务流案例：开发一个用户认证系统

下面用一个演示任务展示 6 阶段、9 命令、25 技能如何配合：开发一个支持邮箱注册、登录、密码重置的用户认证系统。系统不含 OAuth 和第三方登录，技术栈为 Node.js + Express + PostgreSQL。

### 阶段 1：Define（/spec）

在 Claude Code 中输入：

```text
/spec
我想做一个用户认证系统：
- 支持邮箱注册、登录、密码重置
- 不含 OAuth 和第三方登录
- 技术栈：Node.js + Express + PostgreSQL
- 需要满足生产级安全要求
```

激活的技能：`interview-me` → `idea-refine` → `spec-driven-development`。

AI 会先通过 `interview-me` 技能逐个提问澄清需求：

```text
Q1: 密码重置通过邮件还是短信？
Q2: 是否需要登录频率限制？
Q3: 密码强度策略是什么？
Q4: 会话存储用 JWT 还是服务端 session？
```

澄清完成后，`spec-driven-development` 技能生成规格文档，保存为项目根目录的 SPEC.md：

```markdown
# 用户认证系统 SPEC

## 目标
- 邮箱注册、登录、密码重置
- 生产级安全（OWASP Top 10 防护）

## 非目标
- OAuth、第三方登录、多因素认证

## API 端点
- POST /auth/register
- POST /auth/login
- POST /auth/password-reset/request
- POST /auth/password-reset/confirm

## 边界
- 密码用 bcrypt 哈希，cost factor = 12
- 登录失败 5 次锁定 15 分钟
- 密码重置链接 30 分钟过期
```

接着跑 `/constraints`，把"生产级安全"落成可机械检查的书面标准：访谈后生成 CONSTRAINTS.md，约定测试覆盖率不低于 80%、SQL 必须参数化、密钥不得进入代码库，并给这些检查装上对应工具。后面 CI 里的覆盖率门槛就来自这份文件。

### 阶段 2：Plan（/plan）

```text
/plan
```

激活的技能：`planning-and-task-breakdown`。

AI 产出任务分解清单：

```text
任务 1: 数据库 Schema 设计（users 表）
  验收标准: 字段完整、索引合理、迁移脚本可回滚
  依赖: 无

任务 2: 密码哈希工具函数
  验收标准: bcrypt cost=12、单元测试覆盖
  依赖: 无

任务 3: 注册 API（POST /auth/register）
  验收标准: 输入验证、邮箱去重、密码哈希、返回 JWT
  依赖: 任务 1、2

任务 4: 登录 API（POST /auth/login）
  验收标准: 密码校验、失败计数、锁定逻辑、返回 JWT
  依赖: 任务 1、2

任务 5: 密码重置 API
  验收标准: 重置令牌生成、邮件发送、令牌校验、密码更新
  依赖: 任务 1、2

任务 6: 集成测试
  验收标准: 覆盖注册→登录→重置完整流程
  依赖: 任务 3、4、5
```

### 阶段 3：Build（/build）

```text
/build
```

激活的技能：`incremental-implementation`、`test-driven-development`、`context-engineering`、`api-and-interface-design`、`security-and-hardening`。

AI 按垂直切片逐个实现任务。以任务 3（注册 API）为例，`test-driven-development` 技能要求先写测试：

```javascript
// test/auth/register.test.js
const { register } = require('../../src/auth/register');

describe('register', () => {
  test('成功注册新用户', async () => {
    const result = await register({
      email: 'test@example.com',
      password: 'securePassword123',
    });
    expect(result.token).toBeDefined();
    expect(result.userId).toBeDefined();
  });

  test('邮箱已注册时抛出错误', async () => {
    await register({ email: 'dup@example.com', password: 'securePassword123' });
    await expect(
      register({ email: 'dup@example.com', password: 'securePassword123' })
    ).rejects.toThrow('EMAIL_ALREADY_REGISTERED');
  });

  test('密码短于 8 位时抛出错误', async () => {
    await expect(
      register({ email: 'short@example.com', password: '123' })
    ).rejects.toThrow('PASSWORD_TOO_SHORT');
  });
});
```

然后实现满足测试的代码：

```javascript
// src/auth/register.js
const bcrypt = require('bcrypt');
const { v4: uuidv4 } = require('uuid');
const { query } = require('../db');
const { generateToken } = require('./token');

async function register({ email, password }) {
  if (!email || !password) {
    throw new Error('EMAIL_AND_PASSWORD_REQUIRED');
  }
  if (password.length < 8) {
    throw new Error('PASSWORD_TOO_SHORT');
  }

  const existing = await query('SELECT id FROM users WHERE email = $1', [email]);
  if (existing.rows.length > 0) {
    throw new Error('EMAIL_ALREADY_REGISTERED');
  }

  const passwordHash = await bcrypt.hash(password, 12);
  const userId = uuidv4();
  await query(
    'INSERT INTO users (id, email, password_hash, created_at) VALUES ($1, $2, $3, NOW())',
    [userId, email, passwordHash]
  );

  return { token: generateToken(userId), userId };
}

module.exports = { register };
```

`security-and-hardening` 技能在这一步会检查：SQL 注入防护（参数化查询）、密码哈希强度、输入验证完整性。

### 阶段 4：Verify（/test）

```text
/test
```

激活的技能：`test-driven-development`、`browser-testing-with-devtools`（如有前端）、`debugging-and-error-recovery`。

AI 运行所有测试并报告覆盖率：

```bash
npm test

# 预期输出
# Test Suites: 6 passed, 6 total
# Tests:       24 passed, 24 total
# Coverage:    87% statements, 82% branches
```

如果测试失败，`debugging-and-error-recovery` 技能启动五步分诊：复现 → 定位 → 缩小 → 修复 → 防护。

### 阶段 5：Review（/review）

```text
/review
```

激活的技能：`code-review-and-quality`、`code-simplification`、`security-and-hardening`、`performance-optimization`。

AI 产出审查报告：

```text
审查报告
========
[安全] 密码重置令牌使用 crypto.randomBytes(32) 生成 ✓
[安全] SQL 查询全部参数化 ✓
[安全] JWT 密钥从环境变量读取 ✓
[性能] bcrypt cost=12，单次约 250ms，可接受 ✓
[质量] 函数平均长度 18 行，符合规范 ✓
[质量] 测试覆盖率 87%，高于 CONSTRAINTS.md 约定的 80% ✓
[建议] register.js 第 15 行可提取为 validateInput 函数（Nit）
```

### 阶段 6：Ship（/ship）

```text
/ship
```

激活的技能：`shipping-and-launch`、`ci-cd-and-automation`、`git-workflow-and-versioning`、`documentation-and-adrs`。

AI 执行上线流程：

```bash
# 1. 提交代码（commit-as-save-point，只暂存本任务触碰的文件）
git add src/auth/ test/auth/
git commit -m "feat: 用户认证系统（注册、登录、密码重置）"

# 2. 推送并触发 CI
git push origin feature/auth

# 3. CI 流水线检查
#    - Lint（静态检查）通过
#    - 类型检查通过
#    - 单元测试通过
#    - 覆盖率 87%，达到 CONSTRAINTS.md 约定的门槛
#    - 安全扫描无漏洞

# 4. 灰度发布
#    - 金丝雀：5% 流量（功能开关开启）
#    - 逐步放量：25% → 50%
#    - 全量：100% 流量，清理功能开关
```

`documentation-and-adrs` 技能会生成 ADR 记录关键决策：

```markdown
# ADR-001: 认证系统技术选型

## 决策
- 会话管理：JWT（无状态，水平扩展友好）
- 密码哈希：bcrypt cost=12
- 数据库：PostgreSQL

## 理由
- JWT 避免服务端 session 存储，适合微服务架构
- bcrypt cost=12 在 2026 年的硬件上约 250ms，安全性与用户体验平衡
- PostgreSQL 的 JSONB 字段便于后续扩展用户属性
```

拿一个你正在做或做过的小功能（不必是认证系统，一个 CRUD 接口也行），问自己三个问题：

- 开发过程中有没有先写 Spec 再动手？如果当时有 `/spec`，哪些需求会在编码前就暴露出来？
- 有没有测试？覆盖率大概多少？如果不到 80%，缺的是哪类——单元、集成还是端到端？
- 部署前有没有审查和上线前检查？缺了哪一步，事后有没有吃亏？

这三个问题想清楚，Agent Skills 能补上哪些缺口就清楚了。

---

## 安装配置

### 方式一：skills CLI（任何 Agent，一条命令）

官方 Quick Start 首推 Vercel 的开源 [skills CLI](https://github.com/vercel-labs/skills)，可装入 70 多种编码 Agent（Claude Code、Cursor、Codex、Copilot、Cline 等）：

```bash
npx skills add addyosmani/agent-skills            # 安装全部 25 个技能
npx skills add addyosmani/agent-skills --list    # 先浏览再决定
```

也可以只装单个技能：

```bash
npx skills add addyosmani/agent-skills --skill test-driven-development
```

注意：单技能安装只复制 `skills/<name>/` 目录，不带仓库级的 `references/` 共享清单，技能仍可用，但引用共享清单的路径会失效。要完整功能就用整仓安装或克隆仓库。这个问题官方在 issue #361 里跟踪。

### 方式二：Claude Code 插件市场

```text
# 添加插件市场
/plugin marketplace add addyosmani/agent-skills

# 安装插件
/plugin install agent-skills@addy-agent-skills
```

如果遇到 SSH 错误，改用 HTTPS URL：

```text
/plugin marketplace add https://github.com/addyosmani/agent-skills.git
/plugin install agent-skills@addy-agent-skills
```

Windows 或 macOS 上仍报 `git@github.com: Permission denied (publickey)` 时，官方建议配置 Git 把 GitHub 的 SSH 地址统一改写为 HTTPS：

```bash
git config --global url."https://github.com/".insteadOf git@github.com:
```

### 方式三：本地开发安装

```bash
# 克隆仓库
git clone https://github.com/addyosmani/agent-skills.git

# 以插件目录方式启动 Claude Code
claude --plugin-dir /path/to/agent-skills
```

### 方式四：Gemini CLI

```bash
# 从仓库安装
gemini skills install https://github.com/addyosmani/agent-skills.git --path skills

# 从本地克隆安装
gemini skills install ./agent-skills/skills/
```

### 其他工具

- **Cursor**：工作流技能放 `.cursor/skills/`（从 `agent-skills/skills/` 同步），简短策略放 `.cursor/rules/*.mdc`，不要把完整技能粘进 rules。详见 [docs/cursor-setup.md](https://github.com/addyosmani/agent-skills/blob/main/docs/cursor-setup.md)。
- **Codex**（CLI v0.122+）：`codex plugin marketplace add addyosmani/agent-skills` 注册市场后 `codex plugin add agent-skills@agent-skills` 安装，对话中用 `@技能名` 调用。
- **Antigravity CLI**：`agy plugin install https://github.com/addyosmani/agent-skills.git`。部分版本存在命令包装器不可发现的已知问题，可直接调用带命名空间的技能。
- **Windsurf、OpenCode、GitHub Copilot、Kiro、Command Code**：各有接入文档，见仓库 [docs/](https://github.com/addyosmani/agent-skills/tree/main/docs) 目录。

### 验证安装

```text
# 在 Claude Code 中输入
/help

# 应看到 9 条命令
/spec  /constraints  /plan  /build  /test  /review  /webperf  /code-simplify  /ship
```

---

## 核心工程原则与 Anti-Rationalization

Agent Skills 有八条核心原则，每条都落到具体的命令行为上：

| 原则 | 含义 | 落地方式 |
|------|------|----------|
| Spec before code | 先写规格再写代码 | `/spec` 命令强制生成 SPEC.md 后才进入 `/plan` |
| Decide it once, enforce it everywhere | 质量标准一次定好、处处强制 | `/constraints` 把标准写进 CONSTRAINTS.md，检查点按成本分布到编辑循环、任务结束和 CI |
| Small, atomic tasks | 任务要小而原子 | `/plan` 产出每个任务必须有独立验收标准 |
| One slice at a time | 一次实现一个垂直切片 | `/build` 默认模式每个切片含测试+提交，做完即停 |
| Tests are proof | 测试是行为正确的证据 | `/test` 新功能走红-绿-重构，修 bug 走 Prove-It 模式（先写失败的复现测试再修） |
| Improve code health | 持续提升代码健康度 | `/review` 五轴审查，变更规模约 100 行 |
| Clarity over cleverness | 清晰优先于巧妙 | `/code-simplify` 触发 Chesterton's Fence 检查 |
| Faster is safer | 小步快跑降低风险 | `/ship` 灰度发布 5% → 25% → 50% → 100% |

### Anti-Rationalization：防止 AI 偷懒的机制

AI 在执行流程时会本能地找借口跳步——"测试稍后再加"、"这段太简单不用测"、"这只是个原型"。这些借口在长任务、复杂上下文下确实会出现。

每个技能（SKILL.md）都内置了一张 Common Rationalizations 表，逐条列出常见借口和反驳。以 `test-driven-development` 的表为例如下：

| AI 的跳步借口 | 技能的反驳 |
|---------------|-----------|
| "等代码能跑了再补测试" | 你不会补的。事后补的测试测的是实现，不是行为。 |
| "这段太简单，不用测" | 简单代码会变复杂。测试记录的是预期行为。 |
| "测试拖慢了我的速度" | 测试现在拖慢你，之后每次改代码都在给你提速。 |
| "我手动测过了" | 手动测试不会留存。明天的变更破坏它时，你无从知晓。 |
| "代码本身一目了然" | 测试就是规格说明——它记录代码应该做什么，而不是它实际做了什么。 |
| "这只是个原型" | 原型会变成生产代码。从第一天起写测试，才能避免"测试债"危机。 |

除了借口表，每个技能还带 Red Flags 清单（出问题的信号，比如"测试一次就通过——可能没测到你以为的东西"）和 Verification 清单（完成前必须交出的证据，比如"每个新行为都有对应测试""没有跳过或禁用的测试"）。这些表是硬条件，技能执行时逐条对照。AI 试图跳步，流程会把它拉回来。

---

## 质量门控

### 代码质量门控

```text
┌─────────────────────────────────────────┐
│           Code Quality Gate             │
├─────────────────────────────────────────┤
│ ✅ 单元测试通过                          │
│ ✅ Lint（静态检查）通过                  │
│ ✅ 类型检查通过                          │
│ ✅ 覆盖率 ≥ 约定值（CONSTRAINTS.md）     │
│ ✅ 无安全漏洞（OWASP Top 10）           │
│ ✅ 性能基准达标（Core Web Vitals）       │
└─────────────────────────────────────────┘
```

### Ship 前检查清单

| 检查项 | 说明 | 责任技能 |
|--------|------|----------|
| 文档更新 | API/配置变更已记录 | documentation-and-adrs |
| 监控就绪 | 日志、指标、告警已配置 | shipping-and-launch |
| 回滚方案 | 部署前备好可执行的回滚计划 | shipping-and-launch |
| 灰度发布 | 5% → 25% → 50% → 100%，按错误率与 P95 延迟阈值决定推进或回退 | shipping-and-launch |
| 团队通知 | 相关开发者已了解变更 | git-workflow-and-versioning |
| 功能开关 | 新功能默认关闭，按需开启；全量后两周内清理 | ci-cd-and-automation |

---

## 与其他框架对比

官方在 [docs/comparison.md](https://github.com/addyosmani/agent-skills/blob/main/docs/comparison.md) 里正面比较了两个经常被一起提到的同类项目：

| | **Agent Skills** | **Superpowers**（obra） | **Matt Pocock's skills** |
|---|---|---|---|
| 核心思路 | 把资深工程师的完整生命周期编码成技能 | 一套强调自主推理的开发方法论 | 一位专家日常在用的 Claude Code 工具箱 |
| 组织方式 | 按 SDLC 阶段（Define 到 Ship）划分，元技能做路由 | 单一纪律流水线：头脑风暴 → 计划 → subagent 执行 → 审查 | 聚焦命令的工具集，以"grill me"审问循环为招牌 |
| 规模 | 25 个技能覆盖全生命周期 | 约 14 个技能，深耕内部构建循环 | 约 30 个技能，Define 和 Build 见长 |
| 适合场景 | 一个功能从头到尾走完每个阶段，人在每阶段把关 | 长链条的自主、探索性任务 | 务实的日常循环，需求澄清和 TDD 最强 |

Agent Skills 的差异化在两处：每个技能都带 anti-rationalization 表和 Red Flags 清单；仓库内建三层 eval 框架（结构校验、路由词汇查重、真实执行轨迹打分），CI 里验证技能真的按预期路由和执行——另外两个项目目前都没有这种仓库内的全目录度量。官方也坦承代价：比起 Superpowers，它的单次"运行"没那么强的整体方法论，三个项目都还没解决跨会话记忆。

至于 LangChain、AutoGen、CrewAI 这类编排框架，它们解决的是"AI 如何协作和调用工具"，Agent Skills 解决的是"AI 写代码时如何遵循工程纪律"，两者可以组合——比如用 LangChain 编排多 Agent，让每个 Agent 内部走 Agent Skills 的工程流程。

---

## 适用边界与采用顺序

### 哪类团队先上

- **已有 Claude Code 或 Gemini CLI 的团队**：安装成本低，直接通过插件市场接入。
- **经常因 AI 跳过测试或审查导致返工的团队**：anti-rationalization 表和质量门控直接对应这个痛点。
- **需要让 AI 处理生产级代码的团队**：框架的设计目标就是生产级，不是原型级。
- **有明确 Spec 流程但 AI 不遵守的团队**：`/spec` 命令把 Spec 流程强制化。

### 哪类团队可以等等

- **只用 AI 做原型或 POC 的团队**：原型不需要完整工程纪律，框架的流程开销不划算。
- **没有固定 AI 编码工具的团队**：框架依赖各 Agent 的技能系统，什么工具都不装则无从接入。
- **单人维护的小项目**：25 个技能的流程对小项目过重，手动控制更直接。
- **代码库已进入纯维护阶段**：没有新功能开发时，Define/Plan/Build 阶段用不上。

### 从哪个阶段切入

官方的 [Adoption Guide](https://github.com/addyosmani/agent-skills/blob/main/docs/adoption-guide.md) 按 codebase 所处阶段给了两条路径：

- **新项目（greenfield）**：从第一个提交起就用完整生命周期。`/build auto` 在这个阶段很好用——批准一次计划，每个任务仍然测试驱动、单独提交。
- **存量代码库（brownfield）**：增量、验证优先，分四个阶段推进：
  1. **Phase 1**：只装上下文和只读技能（如 `/review`），先让 AI 理解现有代码，不改变任何流程；
  2. **Phase 2**：变更前先补测试，让存量代码逐步被覆盖；
  3. **Phase 3**：新功能走完整生命周期，旧代码维持 Phase 1–2 的节奏——双速采用；
  4. **Phase 4**：还技术债、弃用旧代码、补可观测性。

  两条路径最终汇合：整个 codebase 都在全生命周期之内。

如果团队只想挑最小组合起步，`/review` 加 `/test` 是成本最低的切入点——不改变现有开发流程，只在代码完成后加质量门控。

### 什么时候不该用

- **探索性研究项目**：目标不明确时，强制写 Spec 会拖慢探索速度。
- **一次性脚本**：写完就扔的代码不需要工程纪律。
- **教学演示代码**：演示代码的目的是清晰，不是生产级，工程纪律反而增加噪音。

---

## 常见问题

### Q1: Agent Skills 只能在 Claude Code 中使用吗？

不是。技能文件是纯 Markdown，任何接受系统提示或指令文件的 AI Agent 都能用。官方为 Claude Code、Gemini CLI、Cursor、Windsurf、OpenCode、GitHub Copilot、Kiro、Antigravity、Codex、Command Code 都提供了接入文档，`npx skills` CLI 则覆盖 70 多种 Agent。但 slash 命令（`/spec`、`/plan` 等）只有带命令适配器的工具原生支持——Claude Code 和 Gemini CLI 各有 9 条命令包装器，Antigravity 用 legacy TOML（部分版本有可发现性限制），Command Code 在 TUI 菜单里呈现；Codex 则用 `@技能名` 直接调用技能。

### Q2: 25 个技能都要手动激活吗？

不用。9 条 slash 命令是入口，命令会自动激活相关技能。此外，上下文感知机制会根据任务自动激活技能——设计 API 时自动激活 `api-and-interface-design`，构建 UI 时自动激活 `frontend-ui-engineering`。

### Q3: 安装后 AI 不执行命令怎么办？

排查步骤：

1. 确认插件已安装：输入 `/help` 查看是否有 9 条命令。
2. 重启 Agent 会话：技能在会话启动时加载，装完不重启不会生效。
3. 仍不生效时，对照仓库 docs/ 下对应工具的 setup 文档排查安装路径和加载方式。

### Q4: 可以只用部分技能吗？

可以。每个技能是独立的 Markdown 文件，删除不需要的技能文件即可。但不建议删除 `using-agent-skills` 元技能，它负责技能间的协调。

### Q5: 和团队现有的 Code Review 流程冲突吗？

不冲突。`/review` 命令产出的是 AI 审查报告，定位是人工审查前的预筛。建议的流程是：AI 先跑 `/review` 修复明显问题，再提交人工审查，把人工审查的精力留给真正需要判断的问题。

### Q6: 技能更新后需要重新安装吗？

需要。技能文件装在本地，仓库更新后需要重新拉取或重新安装。仓库没有 CHANGELOG，技能变更看 GitHub Releases 和提交记录。

---

## 资源链接

| 资源 | 链接 | 说明 |
|------|------|------|
| GitHub 仓库 | https://github.com/addyosmani/agent-skills | 主仓库，含全部技能源码 |
| 采用指南 | https://github.com/addyosmani/agent-skills/blob/main/docs/adoption-guide.md | 新项目与存量代码库的两条落地路径 |
| 同类项目对比 | https://github.com/addyosmani/agent-skills/blob/main/docs/comparison.md | 与 Superpowers、Matt Pocock's skills 的逐项对比 |
| Personas 说明 | https://github.com/addyosmani/agent-skills/blob/main/docs/agents.md | 四个审查角色的决策矩阵与编排规则 |
| 通用接入指南 | https://github.com/addyosmani/agent-skills/blob/main/docs/getting-started.md | 不在适配列表内的 Agent 怎么接 |
| Cursor 接入指南 | https://github.com/addyosmani/agent-skills/blob/main/docs/cursor-setup.md | Cursor 配置文档 |
| Gemini CLI 接入指南 | https://github.com/addyosmani/agent-skills/blob/main/docs/gemini-cli-setup.md | Gemini CLI 配置文档 |
| 技能格式规范 | https://github.com/addyosmani/agent-skills/blob/main/docs/skill-anatomy.md | SKILL.md 文件格式说明 |
| 贡献指南 | https://github.com/addyosmani/agent-skills/blob/main/CONTRIBUTING.md | 参与贡献的方式 |

---

## 结尾判断

2026 年，让 AI 写出能跑的代码已经不是问题。Agent Skills 在做的是另一件事——把 Spec、测试、审查、灰度发布这些 AI 默认会跳过的环节，硬编码到它的工作流里。AI 想跳过，流程会把它拉回来。

用这套框架做生产级项目，存量代码库的稳妥路径是官方 Adoption Guide 的四阶段：先只读审查，再变更前补测试，然后新功能走全生命周期，最后还债和补观测。新项目则可以第一天就上全流程，`/build auto` 在这个阶段最好用。

25 个技能不必全用上。探索性研究、一次性脚本、教学演示代码不需要完整的 Define → Ship 流程，强行走完只会拖慢节奏。代码需要上线、需要长期维护、需要多人协作时，这套流程才值得引入。

**什么时候上**：项目有 CI/CD、团队成员 ≥ 2、代码需要部署到生产环境。

**先做什么**：装好 `/review` 和 `/test`，让 AI 在每次提交前强制跑审查和测试。习惯了再逐步往前推。

**什么时候别上**：写原型、写一次性脚本、写教学 Demo。这些场景下，手动控制比 25 个技能更直接。

## 资料口径说明

1. **数据口径**：本文 Stars、Forks、技能数量、命令数量均以 2026-09-20 的仓库 `main` 分支为口径（97.1k Stars、25 个技能、9 条命令）。具体技能的实现随仓库更新可能变化。
2. **事实来源**：关键细节对照仓库 README、docs/ 与 `skills/`、`commands/` 目录下的源文件核实；技能行为描述以各 SKILL.md 与命令 TOML 原文为准。
3. **适用范围**：本文的技能体系主要适用于 Claude Code、Cursor 等支持 SKILL.md 的 AI 编码工具。其他 AI 工具可能需要不同的配置方式。
4. **原文来源**：本文基于 [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) 开源项目。如需引用，请注明项目链接。

