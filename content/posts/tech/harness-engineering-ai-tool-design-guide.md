---
title: "Harness Engineering：AI时代的方法论级实战手册"
slug: "harness-engineering-ai-tool-design-guide"
date: 2026-04-08T20:25:00+08:00
lastmod: 2026-04-08T20:25:00+08:00
categories: ["技术笔记"]
tags: ["AI", "Harness", "方法论", "Agent", "工作流", "提示词", "经验工程"]
description: "Harness Engineering 是方法论级实战手册，7个深度案例拆解（OpenAI Codex、Stripe、Kent Beck等），回答核心问题：AI能写代码之后，人的核心能力是什么？"
draft: false
---

# Harness Engineering：AI时代的方法论级实战手册

## 1. 核心问题

> **"AI 能写代码之后，人的核心能力是什么？"**

Harness Engineering 回答了这个核心问题：**给 AI 造缰绳**。

从「和 AI 聊天」到「给 AI 造缰绳」——这不是修辞，而是方法论的本质升级。

## 2. 什么是 Harness

**Harness（缰绳）** 是一种结构化方法，让 AI 在人类设定的边界内高效工作。

### 2.1 为什么需要 Harness

| 痛点 | Harness 解决方案 |
|------|----------------|
| AI 产出质量不稳定 | 指令层：给 AI 一张地图 |
| AI 容易偏离目标 | 约束层：明确边界 |
| 上下文丢失 | 记忆层：持久化上下文 |
| 多任务协作难 | 编排层：多 Agent 协同 |
| 重复工作 | 能力层：复用最佳实践 |

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

### 4. 编排层（Orchestration Layer）

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

## 6. 减法哲学：少即是多

**核心原则**：最少的指令，最高的产出

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
| 提取最佳实践 | 从成功项目中归纳模式 |
| 设计 Harness 模板 | 通用化、可复用 |
| 迭代优化 | 根据反馈持续改进 |
| 培训团队 | 让成员掌握 Harness 方法 |

### 8.2 经验工程的未来

```
2024: 手工设计 Harness
2025: AI 辅助生成 Harness
2026: AI 自动从项目学习生成 Harness
2027+: 经验工程成为独立学科
```

## 9. 总结：AI 时代人的核心能力

| 能力 | 说明 |
|------|------|
| ** Harness 设计** | 定义边界、指令、能力、记忆、编排 |
| **错误分析** | 从 AI 错误中提取改进规则 |
| **迭代优化** | 持续改进 Harness |
| **经验提取** | 从成功中归纳可复用模式 |
| **判断决策** | AI 提供选项，人做决策 |

**核心公式**：

```
人的价值 = Σ(Harness 设计 + 错误分析 + 迭代优化 + 经验提取)
```

**不是让 AI 替代人，而是让人 AI 协作更高效。**

---

*🦞 每日08:00自动更新*
