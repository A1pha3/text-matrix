---
title: "Agent Skills：addyosmani的生产级AI编程工程技能框架"
date: "2026-04-12T18:02:00+08:00"
slug: agent-skills-addyosmani-production-engineering-guide
description: "16.8k Stars的生产级工程技能框架，为AI编程Agent提供Define→Plan→Build→Test→Review→Ship的完整生命周期管理。20个结构化技能，7条slash命令，让AI编码遵循专业工程师的最佳实践。"
draft: false
categories: ["技术笔记"]
tags: ["AI编程", "Claude Code", "工程技能", "工作流框架", "质量门控"]
---

# Agent Skills：addyosmani 的生产级 AI 编程工程技能框架

## 📋 学习目标

- 理解 Agent Skills 的核心定位——将资深工程师的实践建议封装成 AI 可复用的技能
- 掌握 6 阶段开发生命周期的理念与实施方法
- 学会使用 7 条 slash 命令驱动不同的开发阶段
- 理解 20 个结构化技能如何协同工作
- 掌握在 Claude Code 中安装和配置 Agent Skills 的方法
- 理解自动技能激活机制如何提升 AI 响应质量

---

## 📖 项目概述

### 什么是 Agent Skills

**Agent Skills**是一套**生产级工程技能框架**，由 Google 前工程师 addyosmani 创建。它将资深软件工程师在真实项目中使用的**工作流、质量门控和实践建议**封装成 AI Agent 可复用的结构化技能。

核心理念：
> "Skills encode the workflows, quality gates, and best practices that senior engineers use when building software."

### 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | 16.1k |
| Forks | 2,060 |
| 许可证 | MIT |
| 技能数量 | 20 个 |
| 命令数量 | 7 条 |
| 开发者 | addyosmani (Google 前工程师) |

### 技术架构

```
Agent Skills 6阶段开发周期

┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐
│ Idea │───▶│ Spec │───▶│ Code │───▶│ Test │───▶│ QA   │───▶│ Go   │
│Refine│    │ PRD  │    │ Impl │    │Debug │    │ Gate │    │ Live │
└──────┘    └──────┘    └──────┘    └──────┘    └──────┘    └──────┘

命令: /spec   /plan    /build    /test    /review   /code-simplify  /ship
```

---

## 🔄 6 阶段开发生命周期

### 阶段详解

| 阶段 | 命令 | 核心原则 | 关键产物 |
|------|------|----------|----------|
| **Define** | `/spec` | Spec before code | PRD 文档 |
| **Plan** | `/plan` | Small, atomic tasks | 任务分解 |
| **Build** | `/build` | One slice at a time | 可运行代码 |
| **Test** | `/test` | Tests are proof | 测试通过 |
| **Review** | `/review` | Improve code health | 代码审查 |
| **Ship** | `/ship` | Faster is safer | 部署上线 |

### 循环迭代

每个阶段都支持**Refine（精化）**循环：
- 如果测试失败 → 返回 Build 阶段修复
- 如果审查发现问题 → 返回相关阶段重做
- 如果 Spec 需要调整 → 返回 Define 阶段更新

---

## ⚡ 7 条 Slash 命令

### 命令一览

| 命令 | 阶段 | 核心原则 | 使用场景 |
|------|------|----------|----------|
| `/spec` | Define | Spec before code | 开始新项目、功能或重大变更 |
| `/plan` | Plan | Small, atomic tasks | 有 Spec，需要可执行的任务分解 |
| `/build` | Build | One slice at a time | 任何涉及多文件的变更 |
| `/test` | Test | Tests are proof | 实现逻辑、修复 bug 或变更行为 |
| `/review` | Review | Improve code health | 代码审查，合并前 |
| `/code-simplify` | Refine | Clarity over cleverness | 需要简化复杂代码 |
| `/ship` | Ship | Faster is safer | 准备部署到生产环境 |

### 自动技能激活

Agent Skills 支持**上下文感知的自动技能激活**：

```
触发条件 → 自动激活技能
─────────────────────────────────────
设计API → api-and-interface-design
构建UI → frontend-ui-engineering  
编写测试 → test-driven-development
性能优化 → performance-optimization
安全修复 → security-best-practices
```

---

## 🛠️ 20 个结构化技能

### Define 阶段技能

#### 1. idea-refine

| 属性 | 说明 |
|------|------|
| 用途 | 将模糊想法转化为具体提案 |
| 方法 | 结构化发散/收敛思维 |
| 使用场景 | 有一个粗略概念需要探索 |

#### 2. spec-driven-development

| 属性 | 说明 |
|------|------|
| 用途 | 编写 PRD，覆盖目标、命令、结构、代码风格、测试和边界 |
| 使用场景 | 开始新项目、功能或重大变更 |

### Plan 阶段技能

#### 3. planning-and-task-breakdown

| 属性 | 说明 |
|------|------|
| 用途 | 将 Spec 分解为小、可验证的任务，含验收标准和依赖排序 |
| 使用场景 | 有 Spec，需要可执行单元 |

### Build 阶段技能

#### 4. incremental-implementation

| 属性 | 说明 |
|------|------|
| 核心方法 | 薄垂直切片——实现→测试→验证→提交 |
| 工程实践 | 功能开关、安全默认值、回滚友好变更 |
| 使用场景 | 任何涉及多文件的变更 |

#### 5. test-driven-development

| 属性 | 说明 |
|------|------|
| 核心方法 | 红-绿-重构，测试金字塔(80/15/5) |
| 测试原则 | DAMP over DRY，Beyonce Rule |
| 使用场景 | 实现逻辑、修复 bug 或变更行为 |

#### 6. context-engineering

| 属性 | 说明 |
|------|------|
| 核心方法 | 在正确时间提供正确信息 |
| 技术手段 | 规则文件、上下文打包、MCP 集成 |
| 使用场景 | 开始会话、切换任务或输出质量下降 |

### 更多技能

| 技能名称 | 阶段 | 功能描述 |
|----------|------|----------|
| api-and-interface-design | Build | API 和接口设计 |
| frontend-ui-engineering | Build | 前端 UI 工程 |
| backend-api-development | Build | 后端 API 开发 |
| database-schema-design | Build | 数据库 Schema 设计 |
| performance-optimization | Build | 性能优化 |
| security-best-practices | Build | 安全实践建议 |
| observability-engineering | Build | 可观测性工程 |
| code-review-checklist | Review | 代码审查清单 |
| refactoring-patterns | Refine | 重构模式 |
| technical-debt-management | Refine | 技术债务管理 |

---

## 📦 安装配置

### 方式一：Claude Code npx 安装（推荐）

```bash
# 安装到全局
npx skills add addyosmani/agent-skills --skill agent-skills -g

# 或安装到当前项目
npx skills add addyosmani/agent-skills --skill agent-skills
```

### 方式二：手动安装

```bash
# 克隆仓库
git clone https://github.com/addyosmani/agent-skills.git

# 复制技能到Claude Code技能目录
cp -r agent-skills/skills ~/.claude/skills/

# 复制命令
cp -r agent-skills/.claude/commands ~/.claude/
```

### 验证安装

```bash
# 在Claude Code中输入
/help

# 应该看到7条新命令
/spec, /plan, /build, /test, /review, /code-simplify, /ship
```

---

## 🎯 核心工程原则

### 七大黄金原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **Spec before code** | 代码前先明确 Spec | `/spec` 启动定义阶段 |
| **Small, atomic tasks** | 小而原子的任务 | 每次只做一件事 |
| **One slice at a time** | 一次一片 | 垂直切片而非水平分层 |
| **Tests are proof** | 测试即证明 | TDD 驱动开发 |
| **Improve code health** | 提升代码健康度 | 持续审查和重构 |
| **Clarity over cleverness** | 清晰优于巧妙 | 简单胜于复杂 |
| **Faster is safer** | 更快更安全 | 频繁部署降低风险 |

### Anti-Rationalization 表

Agent Skills 包含**anti-rationalization 表**，防止 AI 在测试失败时编造借口：

| AI 错误倾向 | 正确做法 |
|------------|----------|
| "测试有 bug" | 首先假设代码有问题 |
| "这不是我的责任" | 你是代码的 owner |
| "忽略这个警告" | 所有警告都是信号 |
| "够好了" | 达到质量门控才推进 |

---

## 📊 质量门控

### 代码质量门控

```
┌─────────────────────────────────────┐
│           Code Quality Gate         │
├─────────────────────────────────────┤
│ ✅ 单元测试通过                      │
│ ✅ Lint检查通过                     │
│ ✅ 类型检查通过                     │
│ ✅ 覆盖率 ≥ 80%                    │
│ ✅ 无安全漏洞                       │
│ ✅ 性能基准达标                    │
└─────────────────────────────────────┘
```

### Ship 前检查清单

| 检查项 | 说明 |
|--------|------|
| 文档更新 | API/配置变更已记录 |
| 监控就绪 | 日志、指标、告警配置 |
| 回滚方案 | 能在 5 分钟内回滚 |
| 灰度发布 | 10% → 50% → 100% |
| 团队通知 | 相关开发者已了解变更 |

---

## 🔧 与其他框架对比

| 框架 | 特点 | 与 Agent Skills 对比 |
|------|------|---------------------|
| **LangChain Agents** | LLM 调用链 | 专注 LLM，Agent Skills 专注工程 |
| **AutoGen** | 多 Agent 协作 | 专注对话，Agent Skills 专注代码 |
| **CrewAI** | Role-based Agents | 专注角色，Agent Skills 专注流程 |
| **Agent Skills** | 生产级工程技能 | 结构化工作流+质量门控 |

---

## 💡 实践建议

### 1. 从/spec 开始

```bash
# 不要直接写代码
# 先明确要做什么

/spec
# 输入: "我想做一个用户认证系统"
```

### 2. 小步快跑

```bash
# 每次只做一个功能
/build
# 任务: 实现登录功能（不包含注册、OAuth等）

# 测试通过后再做下一个
```

### 3. 测试驱动

```bash
# 先写测试
/test
# 先定义期望行为

# 然后实现满足测试
```

### 4. 频繁提交

```bash
# 每完成一个小切片就提交
git commit -m "feat: 实现登录表单基础样式"
git commit -m "feat: 添加表单验证"
git commit -m "feat: 集成登录API"
```

---

## 📚 资源链接

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/addyosmani/agent-skills |
| SKILL.md 规范 | agentskills.io |
| Claude Skills | claude.ai/skill |

---

## ✅ 总结

Agent Skills 是将**专业软件工程师的工程实践**转化为 AI 可复用技能的框架：

1. **结构化生命周期**：Define→Plan→Build→Test→Review→Ship
2. **7 条 slash 命令**：直观触发不同开发阶段
3. **20 个结构化技能**：每个技能都是实践建议的封装
4. **自动技能激活**：上下文感知，智能响应
5. **质量门控**：防止 AI 降低代码质量
6. **Anti-Rationalization**：确保 AI 诚实面对错误

这是一套让 AI 编码**专业化、工程化、可信赖**的实战框架。

🦞
