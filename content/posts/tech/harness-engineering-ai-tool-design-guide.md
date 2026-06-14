---
title: "Harness Engineering：AI时代的方法论级实战手册"
slug: "harness-engineering-ai-tool-design-guide"
date: "2026-04-08T20:25:00+08:00"
lastmod: 2026-04-08T20:25:00+08:00
categories: ["技术笔记"]
tags: ["AI", "Harness", "方法论", "Agent", "工作流", "提示词", "经验工程"]
description: "Harness Engineering 是方法论级实战手册，7个深度案例拆解（OpenAI Codex、Stripe、Kent Beck等），回答核心问题：AI能写代码之后，人的核心能力是什么？"
draft: false
---

# Harness Engineering：AI 时代的方法论级实战手册

## 1. 核心问题

> **"AI 能写代码之后，人的核心能力是什么？"**

Harness Engineering 回答了这个核心问题：**给 AI 造缰绳**。

从「和 AI 聊天」到「给 AI 造缰绳」，跨过的是一道工程鸿沟：把对话经验固化为可复用、可迭代、可传承的系统设计。

## 2. 什么是 Harness

**Harness（缰绳）** 是一种结构化方法，让 AI 在人类设定的边界内高效工作。

### 2.1 为什么需要 Harness

| 痛点 | Harness 解决方案 |
|------|----------------|
| AI 产出质量不稳定 | 指令层：给 AI 一张地图 |
| AI 容易偏离目标 | 约束层：明确边界 |
| 上下文丢失 | 记忆层：持久化上下文 |
| 多任务协作难 | 编排层：多 Agent 协同 |
| 重复工作 | 能力层：复用实践建议 |

### 2.2 六十年演变

从 1960 年代到现在，人和工具的关系经历了三次命名革命：

1. **编程语言**：机器语言 → 汇编 → 高级语言
2. **开发范式**：面向过程 → 面向对象 → 函数式
3. **AI 协作**：Prompt → Harness → Experience Engineering

## 3. Harness 的五个组件

```
┌─────────────────────────────────────────────────┐
│                  Experience Engineering            │
│                   经验工程                        │
├─────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │ 指令层  │→│ 约束层  │→│ 能力层  │         │
│  │ 给地图  │  │ 定边界  │  │ 复能力  │         │
│  └─────────┘  └─────────┘  └─────────┘         │
│         ↑              ↓              ↓         │
│  ┌─────────────────────────────┐  ┌─────────┐ │
│  │        记忆层               │→│ 编排层  │ │
│  │ 持久化上下文/学习/偏好      │  │ 多Agent │ │
│  └─────────────────────────────┘  └─────────┘ │
└─────────────────────────────────────────────────┘
```

## 4. 五个组件详解

### 4.1 指令层（Instruction Layer）

**核心原则**：给 AI 一张地图

指令不是告诉 AI「怎么做」，而是告诉 AI「做什么」和「在哪里」。

**好指令 vs 坏指令**：

```markdown
❌ 坏指令：
"帮我写一个用户登录功能"

✅ 好指令：
"实现用户认证系统：
- 用户表：id, email, password_hash, created_at
- 登录接口：POST /auth/login
- JWT token 有效期 7 天
- 密码需要 bcrypt 哈希
- 参考 src/auth/legacy_auth.go 的错误处理模式"
```

### 4.2 约束层（Constraint Layer）

**核心原则**：建议和约束是两回事

```markdown
# 约束类型

## 强制约束（Must Not）
- 不修改 src/core/ 目录
- 禁止直接操作数据库
- 不得绕过认证

## 质量约束（Should）
- 测试覆盖率 > 80%
- 响应时间 < 200ms
- 遵循 src/patterns/ 的代码风格

## 建议（May）
- 可以使用 X 库简化代码
- 建议用缓存优化性能
```

### 4.3 能力层（Capability Layer）

**核心原则**：复用过往经验

```yaml
# .harness/capabilities/
capabilities:
  - name: error-handling
    description: 统一的错误处理模式
    examples:
      - src/errors/validation.ts
      - src/errors/network.ts
    rules:
      - Always use Result type
      - Log with context
      
  - name: api-design
    description: RESTful API 设计规范
    patterns:
      - CRUD 映射
      - 分页规范
      - 错误码体系
```

### 4.4 记忆层（Memory Layer）

**核心原则**：让 AI 记住上下文

```markdown
# 记忆类型

## 项目记忆
- 项目结构
- 技术栈决策
- 架构模式

## 任务记忆
- 当前任务进度
- 已完成的步骤
- 遇到的问题

## 偏好记忆
- 代码风格偏好
- 常用工具选择
- 工作流习惯
```

### 4.5 编排层（Orchestration Layer）

**核心原则**：让十匹马同时跑

```yaml
# 多 Agent 协作模式

agents:
  - name: architect
    role: 系统设计
    tools: [read, write, plan]
    
  - name: coder
    role: 代码实现
    tools: [read, write, execute]
    depends_on: [architect]
    
  - name: reviewer
    role: 代码审查
    tools: [read, analyze]
    depends_on: [coder]
    
  - name: tester
    role: 测试验证
    tools: [execute, assert]
    depends_on: [coder]
```

### 4.6 五层如何协同：一次修 Bug 的完整路径

以一个真实场景串起五个组件。假设你要修复一个支付模块的空指针异常：

1. **指令层** 定位任务：任务卡里写明了报错日志路径、涉及的模块范围（`src/payment/`）和验收标准（单测覆盖异常分支）。
2. **约束层** 划定边界：AI 被禁止修改 `src/core/transaction.go`（核心交易引擎），强制使用项目统一的错误包装函数 `errors.Wrap()`。
3. **能力层** 提供模板：`CAPABILITIES.md` 里有「支付模块错误处理模式」和「空指针修复范例」，AI 可以直接参考已有的 `src/payment/refund.go#L45-L62`。
4. **记忆层** 携带上下文：`MEMORY.md` 记录了上次修复支付超时问题时引入的副作用，AI 在生成修复代码前会自动检查是否会触发同样的问题。
5. **编排层** 分配角色：Architect Agent 先分析影响范围，Coder Agent 实现修复，Reviewer Agent 检查是否引入了新的 nil 路径，Tester Agent 运行回归用例。

五层不是串行流水线——记忆层和约束层在整个过程中持续生效，编排层在修复完成后触发审查回路。如果 Reviewer 发现代码里仍有未处理的 nil 路径，这条反馈会作为新规则写入约束层，进入 Mitchell Hashimoto 式的「犯错 → 加规则」循环。

## 5. 七大深度案例

### 5.1 OpenAI Codex：零行手写代码的百万行产品

**核心洞察**：Codex 能生成代码，但不等于能设计系统。

**经验**：
- 用 Harness 定义系统边界
- 指令层描述架构，Codex 填充实现
- 结果：零行手写代码，百万行产品

### 5.2 Mitchell Hashimoto：每次犯错加一条规则

**核心洞察**：Mistake → Rule 的循环是 Harness 进化的核心机制。

**工作流**：
```
1. AI 犯错
2. 分析错误原因
3. 添加新约束到 Harness
4. 下次避免
```

### 5.3 Anthropic：让 AI 查 AI

**核心洞察**：AI 的输出需要 AI 来验证。

**实践**：
- Agent A 生成代码
- Agent B 审查代码
- Agent A 根据审查修正

### 5.4 Stripe Minions：每周 1300 个 PR 的流水线

**核心洞察**：规模化 AI 协作需要标准化流程。

**数字**：
- 每周 1300 个 PR
- 90% 由 AI 生成
- 人工审查 < 5 分钟/PR

### 5.5 LangChain：同一匹马，换套缰绳

**核心洞察**：工具可以换，但 Harness 逻辑可以复用。

**思想**：
- LangChain 定义了 Agent 的抽象
- 不同的 LLMs 可以插拔
- Harness 设计保持一致

### 5.6 Kent Beck：极限编程教父的 CLAUDE.md

**核心洞察**：XP 的核心原则可以转化为 Harness 指令。

**CLAUDE.md 模板**：
```markdown
# 项目原则

## 代码质量
- 简单设计
- 测试先行
- 重构不断

## 协作规范
- 频繁提交
- 结对编程
- 代码共享

## 反馈循环
- 快速反馈
- 持续集成
- 迭代改进
```

### 5.7 花叔：零代码经验到百万用户

**核心洞察**：Harness 让没有编程背景的人也能构建产品。

**路径**：
1. 用自然语言描述需求
2. Harness 转化为具体任务
3. AI 执行任务
4. 人工审核和调整

## 6. 减法哲学

**核心原则**：每一条指令、约束和能力定义都有维护成本。删掉一条不必要的规则，比新增一条规则更能提升 Harness 质量。

### 6.1 为什么减法有效

| 指令过多 | 减法之后 |
|---------|----------|
| AI 困惑，不知道哪个优先 | 明确的核心任务 |
| 上下文爆炸 | 精简的上下文 |
| 过度约束限制创造力 | 最小约束保留创意空间 |

### 6.2 如何做减法

```markdown
# 减法检查清单

1. 这条指令是否已经在其他地方定义过？
2. 这条约束是否真正必要？
3. 删除这条会影响系统完整性吗？
4. 能否合并相似的指令？

# 精简后的指令示例

## Before（10条）
- 要用 TypeScript
- 要用 ESLint
- 要用 Prettier
- 要用 Jest
- ...

## After（2条）
- 使用团队技术栈（见 team.yml）
- 遵循 src/PATTERNS/ 中的模式
```

## 7. 从空白开始：你的第一个 Harness

### 7.1 创建步骤

```bash
# 1. 初始化 Harness 目录
mkdir -p myproject/.harness
cd myproject/.harness

# 2. 创建核心文件
touch INSTRUCTIONS.md
touch CONSTRAINTS.md
touch CAPABILITIES.md
touch MEMORY.md
touch ORCHESTRATION.yaml

# 3. 定义项目 Harness
cat > INSTRUCTIONS.md << 'EOF'
# 项目指令

## 项目概述
这是一个...

## 核心目标
1. ...
2. ...
EOF

cat > CONSTRAINTS.md << 'EOF'
# 约束

## 强制约束
- ...

## 质量标准
- ...
EOF
```

### 7.2 Harness 迭代循环

```
┌─────────────┐
│   使用      │
│  Harness   │
└─────────────┘
      ↓
┌─────────────┐
│   AI 执行   │
│   任务     │
└─────────────┘
      ↓
┌─────────────┐
│   出现错误  │
│   或问题    │
└─────────────┘
      ↓
┌─────────────┐
│   更新      │
│  Harness   │
└─────────────┘
      ↓
   回到起点
```

## 8. 经验工程：谁来设计下一代的缰绳

**核心问题**：谁来设计 Harness？

### 8.1 经验工程师的职责

| 职责 | 说明 |
|------|------|
| 提取实践建议 | 从成功项目中归纳模式 |
| 设计 Harness 模板 | 通用化、可复用 |
| 迭代优化 | 根据反馈持续改进 |
| 培训团队 | 让成员掌握 Harness 方法 |

### 8.2 经验工程的演进方向

当前阶段的重心是把成功项目的 Harness 模板化、可移植化。随着模板积累，从手工设计过渡到半自动生成是自然方向；但经验工程的瓶颈不在生成 Harness，而在从散落项目里提取出经得起复用的模式。

## 9. 从哪里开始

| 团队情况 | 建议起点 |
|------|------|
| 个人开发者，刚接触 AI 编程 | 从指令层和约束层开始：写一份 INSTRUCTIONS.md 和 CONSTRAINTS.md，迭代 3-5 个任务后回头看效果 |
| 小团队，已有 AI 编码习惯但产出不稳定 | 补能力层和记忆层：把项目中反复出现的模式写成 CAPABILITIES.md，把架构决策记录写入 MEMORY.md |
| 多项目并行，需要规模化 | 引入编排层：定义 Agent 角色分工，建立 Harness 模板库，让不同项目共享同一套约束体系 |
| 已有成熟 Harness 但感觉指令膨胀 | 进入减法回路：逐条审查现有指令，合并同类项，删掉已被能力层覆盖的冗余规则 |

Harness 不是一次性工程产物，而是在每一次 AI 犯错后生长出来的东西。Mitchell Hashimoto 的「每次犯错加一条规则」和 Kent Beck 的「简单设计、测试先行、重构不断」指向同一件事：把用完就丢的聊天记录，变成下一次能直接用的基础设施。

---

*🦞 每日 08:00 自动更新*
