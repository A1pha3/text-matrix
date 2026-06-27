---
title: "Agent Skills：addyosmani的生产级AI编程工程技能框架"
date: "2026-04-12T18:02:00+08:00"
slug: agent-skills-addyosmani-production-engineering-guide
description: "66. 4k Stars 的生产级工程技能框架——23 个结构化技能和 7 条 slash 命令，强制 AI 按 Define→Plan→Build→Test→Review→Ship 的完整生命周期工作。"
draft: false
categories: ["技术笔记"]
tags: ["AI编程", "Claude Code", "工程技能", "工作流框架", "质量门控"]
---

# Agent Skills：addyosmani 的生产级 AI 编程工程技能框架

## 开篇判断

AI 编码 Agent 有个习惯：拿到需求直接写代码，跳过规格说明、省略测试、忽略安全审查。做原型够用，放到生产环境就暴露问题——没有测试的代码不敢重构，没有审查的代码藏着边界缺陷，没有 Spec 的项目在需求变更时失控。

Agent Skills 把这套习惯改过来。它由 Google 前工程师 addyosmani 开源，把资深工程师在真实项目中的工作流封装成 23 个结构化技能和 7 条命令，强制 AI 按 Define → Plan → Build → Test → Review → Ship 的完整生命周期工作。

用 Claude Code 或 Cursor 的团队最常遇到一个困境：AI 产出的代码能跑，但缺测试、没审查、没有 Spec。Agent Skills 把这些环节写成 AI 可执行的步骤，让每次产出都走同一套流程。如果 AI 想跳过测试或审查，内置的 anti-rationalization 表会把它拉回流程内。

读下去之前，先摸清几点：

- 三层组件（命令 → 技能 → 参考清单）是调度链，上一层驱动下一层
- 6 个阶段有严格的推进条件，Refine 循环允许任何阶段回退
- 完整任务流案例展示一个用户认证系统如何从头到尾穿过这套框架
- 不同团队适合的切入节奏不同——先上 `/review` 和 `/test` 的成本最低

## 学习目标

读完这篇文章，你应该能够：

1. **解释** Agent Skills 如何解决 AI 编码 Agent 跳过工程纪律的问题
2. **列举** 6 个开发阶段及其对应的 slash 命令
3. **描述** 三层组件（命令、技能、参考清单）之间的调度关系
4. **使用** 至少 3 条 slash 命令（`/spec`、`/test`、`/review`）来规范 AI 的工作流
5. **判断** 你的团队是否应该采用 Agent Skills，以及从哪个阶段开始切入

## 目录

- [开篇判断](#开篇判断)
- [项目概述](#项目概述)
- [系统总览：三层组件如何配合](#系统总览三层组件如何配合)
- [6 阶段开发生命周期](#6-阶段开发生命周期)
- [7 条 slash 命令](#7-条-slash-命令)
- [23 个结构化技能](#23-个结构化技能)
- [任务流案例：开发一个用户认证系统](#任务流案例开发一个用户认证系统)
- [安装配置](#安装配置)
- [核心工程原则与 Anti-Rationalization](#核心工程原则与-anti-rationalization)
- [质量门控](#质量门控)
- [与其他框架对比](#与其他框架对比)
- [适用边界与采用顺序](#适用边界与采用顺序)
- [常见问题](#常见问题)
- [资源链接](#资源链接)
- [结尾判断](#结尾判断)
- [实战自测](#实战自测)
- [进阶路径](#进阶路径)

---

## 项目概述

### 这套框架在解决什么问题

Agent Skills 的做法是把工程实践写成 AI 可执行的流程：每个技能是一组带步骤、检查点和退出条件的指令，AI 必须按流程走完才能产出代码。技能文件本身是纯 Markdown，通过 slash 命令和上下文感知机制被 Claude Code、Gemini CLI 等工具加载后，就变成了 AI 的工作流约束。

### 核心数据

| 指标 | 数值 |
|------|--------|
| GitHub Stars | 66.4k |
| Forks | 7.2k |
| 许可证 | MIT |
| 主要语言 | Shell |
| 技能数量 | 23 个（22 个生命周期技能 + 1 个元技能） |
| 命令数量 | 7 条 |
| 开发者 | addyosmani（Google 前工程师） |
| 仓库地址 | https://github.com/addyosmani/agent-skills |

> 数据采集于 2026-06-25。仓库技能数量会随版本迭代变化，最新数量以仓库 README 为准。

---

## 系统总览：三层组件如何配合

Agent Skills 由三层组件构成。三层的关系决定了什么时候该手动输入命令、什么时候 AI 会自己激活技能。

### 三层组件

| 层级 | 数量 | 职责 | 触发方式 |
|------|------|------|----------|
| **slash 命令** | 7 条 | 开发生命周期的入口点 | 用户手动输入 |
| **技能（Skills）** | 23 个 | 具体工程流程的执行者 | 命令激活或上下文自动激活 |
| **参考清单（References）** | 4 份 | 技能按需加载的补充材料 | 技能内部引用 |

slash 命令是用户接触框架的入口，每条命令激活一组技能，技能在执行过程中按需加载参考清单。三层之间是"调度 → 执行 → 补充"的链式关系，上一层驱动下一层。

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

7 条命令对应 6 个阶段，其中 `/code-simplify` 属于 Refine 循环，可在 Build、Verify、Review 任一阶段触发。

### 自动技能激活机制

除了手动输入命令，Agent Skills 还支持上下文感知的自动激活：当 AI 检测到当前任务匹配某个技能的触发条件时，会自动加载该技能的流程。

```text
触发场景                → 自动激活的技能
─────────────────────────────────────────────
设计 API 或模块接口      → api-and-interface-design
构建用户界面             → frontend-ui-engineering
编写或修改测试           → test-driven-development
性能优化或性能回归       → performance-optimization
处理用户输入或认证       → security-and-hardening
调试失败用例或异常行为   → debugging-and-error-recovery
```

用户不需要记住所有技能名称，描述清楚任务后 AI 会自动选择合适的工程流程。

---

## 6 阶段开发生命周期

这一节聚焦 6 个阶段的名字和推进条件。读完应该能判断手头的项目处于哪个阶段、缺少哪个阶段的产物。

### 阶段详解

| 阶段 | 命令 | 核心原则 | 关键产物 | 常用技能 |
|------|------|----------|----------|----------|
| **Define** | `/spec` | Spec before code（先写规格再写代码） | PRD（产品需求文档，Product Requirements Document） | spec-driven-development, interview-me, idea-refine |
| **Plan** | `/plan` | Small, atomic tasks（小而原子的任务） | 任务分解清单 | planning-and-task-breakdown |
| **Build** | `/build` | One slice at a time（一次一个垂直切片） | 可运行代码 | incremental-implementation, test-driven-development, context-engineering |
| **Verify** | `/test` | Tests are proof（测试即证明） | 测试通过、覆盖率达标 | test-driven-development, browser-testing-with-devtools, debugging-and-error-recovery |
| **Review** | `/review` | Improve code health（提升代码健康度） | 审查报告、修复记录 | code-review-and-quality, security-and-hardening, performance-optimization |
| **Ship** | `/ship` | Faster is safer（小步快跑更安全） | 部署上线、监控就绪 | shipping-and-launch, ci-cd-and-automation, git-workflow-and-versioning |

### Refine 循环

每个阶段都支持回退：

- 测试失败 → 返回 Build 阶段修复，重新进入 Verify
- 审查发现安全漏洞 → 返回 Build 阶段重做相关模块
- Spec 在实现中发现不可行 → 返回 Define 阶段更新 PRD

`/code-simplify` 命令属于 Refine 循环，用于在任意阶段简化复杂代码，核心原则是 Clarity over cleverness（清晰优于巧妙）。

---

## 7 条 slash 命令

### 命令一览

| 命令 | 阶段 | 核心原则 | 使用场景 |
|------|------|----------|----------|
| `/spec` | Define | Spec before code | 开始新项目、新功能或重大变更 |
| `/plan` | Plan | Small, atomic tasks | 已有 Spec，需要可执行的任务分解 |
| `/build` | Build | One slice at a time | 任何涉及多文件的变更 |
| `/test` | Verify | Tests are proof | 实现逻辑、修复 bug 或变更行为 |
| `/review` | Review | Improve code health | 代码审查、合并前 |
| `/code-simplify` | Refine | Clarity over cleverness | 代码能跑但可读性差或复杂度过高 |
| `/ship` | Ship | Faster is safer | 准备部署到生产环境 |

### 命令的执行逻辑

每条命令背后是一个工作流调度器，不是单条提示词。以 `/build` 为例：

```text
1. 读取当前 Spec 和任务分解
2. 激活 incremental-implementation 技能
3. 按垂直切片逐个实现任务
4. 每个切片完成后调用 /test 验证
5. 测试通过后提交（commit-as-save-point 模式）
6. 所有切片完成后进入 /review
```

如果 AI 在执行过程中试图跳步（例如"测试稍后再加"），anti-rationalization 表会触发，强制 AI 回到流程内。

---

## 23 个结构化技能

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
| 用途 | 编写 PRD（产品需求文档），覆盖目标、命令、结构、代码风格、测试和边界 |
| 使用场景 | 开始新项目、功能或重大变更 |

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
| 测试原则 | DAMP（Descriptive And Meaningful Phrases，描述性断言模式）优先于 DRY（Don't Repeat Yourself，不要重复自己）；Beyonce Rule（碧昂丝规则：未被测试覆盖的代码就是不存在） |
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
| 用途 | 对每个非平凡决策进行对抗式新鲜上下文审查——CLAIM → EXTRACT → DOUBT → RECONCILE → STOP |
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

---

## 任务流案例：开发一个用户认证系统

下面用一个真实任务演示 6 阶段、7 命令、23 技能如何配合：开发一个支持邮箱注册、登录、密码重置的用户认证系统。系统不含 OAuth 和第三方登录，技术栈为 Node.js + Express + PostgreSQL。

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

澄清完成后，`spec-driven-development` 技能生成 PRD 文档：

```markdown
# 用户认证系统 PRD

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
[质量] 测试覆盖率 87%，超过 80% 门槛 ✓
[建议] register.js 第 15 行可提取为 validateInput 函数（Nit）
```

### 阶段 6：Ship（/ship）

```text
/ship
```

激活的技能：`shipping-and-launch`、`ci-cd-and-automation`、`git-workflow-and-versioning`、`documentation-and-adrs`。

AI 执行上线流程：

```bash
# 1. 提交代码（commit-as-save-point）
git add -A
git commit -m "feat: 用户认证系统（注册、登录、密码重置）"

# 2. 推送并触发 CI
git push origin feature/auth

# 3. CI 流水线检查
#    - Lint（静态检查）通过
#    - 类型检查通过
#    - 单元测试通过
#    - 覆盖率 87% ≥ 80%
#    - 安全扫描无漏洞

# 4. 灰度发布
#    - 第 1 批：10% 流量，监控 30 分钟
#    - 第 2 批：50% 流量，监控 30 分钟
#    - 第 3 批：100% 流量
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
- 有没有测试？如果有，覆盖率大概多少？如果不到 80%，缺的是哪类测试——单元、集成还是端到端？
- 部署前有没有审查和上线前检查？缺了哪一步，事后有没有吃亏？

这三个问题想清楚，Agent Skills 能补上哪些缺口就清楚了。

---

## 安装配置

### 方式一：Claude Code 插件市场安装（推荐）

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

### 方式二：本地开发安装

```bash
# 克隆仓库
git clone https://github.com/addyosmani/agent-skills.git

# 以插件目录方式启动 Claude Code
claude --plugin-dir /path/to/agent-skills
```

### 方式三：Cursor

将任意 `SKILL.md` 复制到 `.cursor/rules/` 目录，或引用完整的 `skills/` 目录。详见 [docs/cursor-setup.md](https://github.com/addyosmani/agent-skills/blob/main/docs/cursor-setup.md)。

### 方式四：Gemini CLI

```bash
# 从仓库安装
gemini skills install https://github.com/addyosmani/agent-skills.git --path skills

# 从本地克隆安装
gemini skills install ./agent-skills/skills/
```

### 验证安装

```text
# 在 Claude Code 中输入
/help

# 应看到 7 条命令
/spec  /plan  /build  /test  /review  /code-simplify  /ship
```

---

## 核心工程原则与 Anti-Rationalization

Agent Skills 有七条核心原则。每条原则不是口号，而是有具体的落地方式：

| 原则 | 含义 | 落地方式 |
|------|------|----------|
| Spec before code | 先写规格再写代码 | `/spec` 命令强制生成 PRD 后才进入 `/plan` |
| Small, atomic tasks | 任务要小而原子 | `/plan` 产出每个任务必须有独立验收标准 |
| One slice at a time | 一次实现一个垂直切片 | `/build` 每个切片含实现+测试+提交 |
| Tests are proof | 测试是代码正确的证据 | `/test` 要求覆盖率 ≥ 80% |
| Improve code health | 持续提升代码健康度 | `/review` 五轴审查，变更规模 ≤ 100 行 |
| Clarity over cleverness | 清晰优先于巧妙 | `/code-simplify` 触发 Chesterton's Fence 检查 |
| Faster is safer | 小步快跑降低风险 | `/ship` 灰度发布 10% → 50% → 100% |

### Anti-Rationalization：防止 AI 偷懒的机制

AI 在执行流程时会本能地找借口跳步——"测试稍后再加"、"这个警告可以忽略"、"够好了，可以先上线"。这些借口在长任务、复杂上下文下确实会出现。

每个技能内置了常见借口和反驳：

| AI 的跳步借口 | 技能的反驳 |
|---------------|-----------|
| "测试有 bug，不是代码问题" | 先假设代码有问题，证明测试有 bug 后才能修改测试 |
| "这不是我的责任，是上游 API 的问题" | 你是当前代码的 owner，先排查再上报 |
| "这个警告可以忽略" | 所有警告都是信号，必须显式处理或记录理由 |
| "测试稍后再加" | 测试是切片的一部分，没有测试的切片不算完成 |
| "够好了，可以先上线" | 必须通过质量门控才能推进到下一阶段 |

anti-rationalization 表是硬条件，技能执行时会逐条对照检查。如果 AI 试图跳步，流程会把它拉回来。

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
│ ✅ 覆盖率 ≥ 80%                         │
│ ✅ 无安全漏洞（OWASP Top 10）           │
│ ✅ 性能基准达标（Core Web Vitals）       │
└─────────────────────────────────────────┘
```

### Ship 前检查清单

| 检查项 | 说明 | 责任技能 |
|--------|------|----------|
| 文档更新 | API/配置变更已记录 | documentation-and-adrs |
| 监控就绪 | 日志、指标、告警已配置 | shipping-and-launch |
| 回滚方案 | 能在 5 分钟内回滚 | shipping-and-launch |
| 灰度发布 | 10% → 50% → 100% | shipping-and-launch |
| 团队通知 | 相关开发者已了解变更 | git-workflow-and-versioning |
| 功能开关 | 新功能默认关闭，按需开启 | ci-cd-and-automation |

---

## 与其他框架对比

LangChain、AutoGen、CrewAI 经常和 Agent Skills 放在一起讨论，但定位不同：前三者解决"AI 如何协作和调用工具"，Agent Skills 解决"AI 写代码时如何遵循工程纪律"。两者可以组合使用——比如用 LangChain 编排多 Agent，让每个 Agent 内部走 Agent Skills 的工程流程。

---

## 适用边界与采用顺序

### 哪类团队先上

- **已有 Claude Code 或 Gemini CLI 的团队**：安装成本低，直接通过插件市场接入。
- **经常因 AI 跳过测试或审查导致返工的团队**：anti-rationalization 表和质量门控直接对应这个痛点。
- **需要让 AI 处理生产级代码的团队**：框架的设计目标就是生产级，不是原型级。
- **有明确 Spec 流程但 AI 不遵守的团队**：`/spec` 命令把 Spec 流程强制化。

### 哪类团队可以等等

- **只用 AI 做原型或 POC 的团队**：原型不需要完整工程纪律，框架的流程开销不划算。
- **没有固定 AI 编码工具的团队**：框架依赖 Claude Code、Gemini CLI 或 Cursor 的技能系统，没有这些工具无法使用。
- **单人维护的小项目**：23 个技能的流程对小项目过重，手动控制更直接。
- **代码库已进入纯维护阶段**：没有新功能开发时，Define/Plan/Build 阶段用不上。

### 从哪个阶段切入

如果不想一次性引入全部流程，建议按以下顺序逐步采用：

1. **先上 `/review` 和 `/test`**：这两个命令不改变现有开发流程，只在代码完成后增加质量门控。团队适应成本最低。
2. **再上 `/build`**：把 AI 的编码行为改造成垂直切片模式，每个切片自带测试和提交。
3. **最后上 `/spec` 和 `/plan`**：这两个命令改变需求阶段的工作方式，需要产品经理和开发者共同适应。
4. **`/ship` 按需引入**：如果团队已有 CI/CD 流程，`/ship` 用于补全灰度发布和回滚方案。

### 什么时候不该用

- **探索性研究项目**：目标不明确时，强制写 Spec 会拖慢探索速度。
- **一次性脚本**：写完就扔的代码不需要工程纪律。
- **教学演示代码**：演示代码的目的是清晰，不是生产级，工程纪律反而增加噪音。

---

## 常见问题

### Q1: Agent Skills 只能在 Claude Code 中使用吗？

不是。技能文件是纯 Markdown，任何接受系统提示或指令文件的 AI Agent 都能用。官方提供了 Claude Code、Gemini CLI、Cursor、Windsurf、OpenCode、GitHub Copilot、Kiro IDE 的接入文档。但 slash 命令（`/spec`、`/plan` 等）目前只在 Claude Code 和 Gemini CLI 中原生支持。

### Q2: 23 个技能都要手动激活吗？

不用。7 条 slash 命令是入口，命令会自动激活相关技能。此外，上下文感知机制会根据任务自动激活技能——设计 API 时自动激活 `api-and-interface-design`，构建 UI 时自动激活 `frontend-ui-engineering`。

### Q3: 安装后 AI 不执行命令怎么办？

排查步骤：

1. 确认插件已安装：输入 `/help` 查看是否有 7 条命令。
2. 检查技能目录权限：`ls ~/.claude/skills/` 确认技能文件存在。
3. 重启 Claude Code 会话：技能在会话启动时加载。
4. 查看技能加载日志：`/debug skills` 查看是否有加载错误。

### Q4: 可以只用部分技能吗？

可以。每个技能是独立的 Markdown 文件，删除不需要的技能文件即可。但不建议删除 `using-agent-skills` 元技能，它负责技能间的协调。

### Q5: 和团队现有的 Code Review 流程冲突吗？

不冲突。`/review` 命令产出的是 AI 审查报告，定位是人工审查前的预筛。建议的流程是：AI 先跑 `/review` 修复明显问题，再提交人工审查，把人工审查的精力留给真正需要判断的问题。

### Q6: 技能更新后需要重新安装吗？

需要。技能文件在本地，仓库更新后需要重新拉取或重新安装。建议关注仓库的 CHANGELOG 了解技能变更。

---

## 资源链接

| 资源 | 链接 | 说明 |
|------|------|------|
| GitHub 仓库 | https://github.com/addyosmani/agent-skills | 主仓库，含全部技能源码 |
| Cursor 接入指南 | https://github.com/addyosmani/agent-skills/blob/main/docs/cursor-setup.md | Cursor 配置文档 |
| Gemini CLI 接入指南 | https://github.com/addyosmani/agent-skills/blob/main/docs/gemini-cli-setup.md | Gemini CLI 配置文档 |
| Windsurf 接入指南 | https://github.com/addyosmani/agent-skills/blob/main/docs/windsurf-setup.md | Windsurf 配置文档 |
| OpenCode 接入指南 | https://github.com/addyosmani/agent-skills/blob/main/docs/opencode-setup.md | OpenCode 配置文档 |
| Copilot 接入指南 | https://github.com/addyosmani/agent-skills/blob/main/docs/copilot-setup.md | GitHub Copilot 配置文档 |
| 技能格式规范 | https://github.com/addyosmani/agent-skills/blob/main/docs/skill-anatomy.md | SKILL.md 文件格式说明 |
| 贡献指南 | https://github.com/addyosmani/agent-skills/blob/main/CONTRIBUTING.md | 参与贡献的方式 |

---

## 结尾判断

2026 年，让 AI 写出能跑的代码已经不是问题。Agent Skills 在做的是另一件事——把 Spec、测试、审查、灰度发布这些 AI 默认会跳过的环节，硬编码到它的工作流里。AI 想跳过，流程会把它拉回来。

用这套框架做生产级项目，最稳的切入路径是 `/review` → `/test` → `/build` → `/spec` → `/plan`。先上 `/review` 和 `/test` 不改变团队现有流程，只在代码完成后加一道质量门控，适应成本最低。跑顺了再往前推 `/spec` 和 `/plan`，把工程纪律前移到需求阶段。

23 个技能不必全用上。探索性研究、一次性脚本、教学演示代码不需要完整的 Define → Ship 流程，强行走完只会拖慢节奏。代码需要上线、需要长期维护、需要多人协作时，这套流程才值得引入。

**什么时候上**：项目有 CI/CD、团队成员≥2、代码需要部署到生产环境。

**先做什么**：装好 `/review` 和 `/test`，让 AI 在每次提交前强制跑审查和测试。习惯了再逐步往前推。

**什么时候别上**：写原型、写一次性脚本、写教学 Demo。这些场景下，手动控制比 23 个技能更直接。

## 实战自测

看完这篇文章，拿一个你正在做的项目试试看：

1. 项目里有没有 Spec？如果没有，试着跑一遍 `/spec` 看看 AI 产出的 PRD 是否符合你的预期。
2. 最近一次提交有测试吗？如果覆盖率不到 80%，跑一遍 `/test` 补上缺失的用例。
3. 合并前有没有审查过？拿一个未合并的分支跑 `/review`，看 AI 的审查报告能不能帮你发现问题。
4. 部署上线时有灰度发布和回滚方案吗？如果没有，`/ship` 的上线前清单可以当模板用。

把以上 4 步走完一轮，比再读一遍文章更能确认这套框架适不适合你的项目。

## 进阶路径

- **想深入理解单个技能**：直接打开 `skills/` 目录下的 `SKILL.md` 文件，每个技能的结构都是「触发条件 → 流程图 → 步骤 → 退出条件」。从 `spec-driven-development` 和 `test-driven-development` 开始读，这两个是大多数项目的入口。
- **想自定义技能**：参考仓库里的 `docs/skill-anatomy.md`，了解 `SKILL.md` 的格式规范，然后 fork 一份改自己的版本。
- **想从零构建技能体系**：读 `using-agent-skills` 元技能，理解技能间的调度逻辑和上下文感知机制，再设计自己的技能层级。

🦞
