---
title: "Matt Pocock Skills：Claude Code Agent 技能集合完全指南"
date: "2026-04-06T19:55:00+08:00"
slug: "mattpocock-skills-claude-code-agent-guide"
description: "全面介绍 Matt Pocock Skills 开源技能集合，涵盖17个Agent技能的定位、场景和用法，以及完整的开发流程工作流。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "Agent Skills", "Matt Pocock", "TDD", "PRD"]
---

# Matt Pocock Skills：Claude Code Agent 技能集合完全指南

## 学习目标

通过本文，你将全面掌握以下核心能力：

- 深入理解 Matt Pocock Skills 的设计理念与架构
- 掌握全部 17 个技能的定位、使用场景和调用方式
- 学会在 Planning & Design 阶段使用 PRD、计划分解、接口设计等技能
- 掌握 TDD、问题诊断、代码架构改进等开发技能
- 熟练运用 Git 保护、预提交钩子等工具链技能
- 学会构建技能写作、知识管理的工作流
- 理解 Agent Skills 的安装、配置与管理方法

---

## 1. 项目概述

### 1.1 是什么

**Matt Pocock Skills** 是由 TypeScript 专家 [Matt Pocock](https://github.com/mattpocock) 创建的 Claude Code Agent 技能集合。这些技能来自他个人的 `.claude` 目录，涵盖了从需求规划、设计评审、开发实现到知识管理的完整开发流程。

每个技能都是一个独立的功能模块，可以增强 Claude Code 在特定任务上的能力。这些技能经过精心设计，强调**渐进式披露**（Progressive Disclosure）——只在需要时加载相关文档，而非一股脑塞入上下文。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | 12.4k |
| GitHub Forks | 1k |
| Watchers | 157 |
| 贡献者 | 2 位（mattpocock, claude）|
| License | MIT |
| 语言 | Shell 100% |
| 最新提交 | 2026-04-01 |

### 1.3 设计哲学

Matt Pocock Skills 的设计遵循以下核心原则：

**渐进式披露**：每个技能的说明文档分为多个层级——元数据（名称、描述）始终在上下文 (~100 tokens)，完整指令在技能触发时加载，bundled resources 按需使用。

**垂直切片思维**：问题分解和任务规划都强调"垂直切片"（Vertical Slices），即按功能边界而非技术层级来组织工作。

**对话式交互**：多个技能通过"追问"（Grill）机制确保决策树被充分探索，避免早停。

**GitHub 原生集成**：技能结果直接以 GitHub Issues 形式输出，便于追踪和管理。

---

## 2. Planning & Design 技能详解

规划与设计阶段是高质量软件的基础。这 6 个技能帮助你在写代码之前充分思考、分解需求。

### 2.1 write-a-prd

**功能**：通过交互式访谈、代码库探索和模块设计，创建产品需求文档（PRD）。

**核心流程**：
1. **交互式访谈**：Claude 会追问需求细节，直到理解完整背景
2. **代码库探索**：检查现有代码，理解上下文约束
3. **模块设计**：设计模块接口和数据结构
4. **输出**：以 GitHub Issue 形式提交 PRD

**使用场景**：
- 开始新功能前
- 需要与利益相关者对齐需求时
- 不确定技术方案需要讨论时

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/write-a-prd
```

### 2.2 prd-to-plan

**功能**：将 PRD 转化为多阶段实施计划，使用 tracer bullet 垂直切片。

**核心概念**：

| 概念 | 说明 |
|------|------|
| Tracer Bullet | 先实现一个端到端可用的最小功能，再逐步扩展 |
| Vertical Slice | 按功能边界组织代码，而非按技术层级（Controller/Service/Repo）|

**使用场景**：
- PRD 已完成，需要分解为可执行的任务
- 希望以增量方式交付价值

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/prd-to-plan
```

### 2.3 prd-to-issues

**功能**：将 PRD 分解为独立可认领的 GitHub Issues，使用垂直切片。

**与 prd-to-plan 的区别**：

| 技能 | 输出形式 | 粒度 |
|------|---------|------|
| prd-to-plan | 多阶段实施计划 | 阶段 |
| prd-to-issues | 独立 Issues | 可认领的任务 |

**使用场景**：
- 需要多人协作时
- 任务可以并行开发时
- 需要明确分工和依赖关系时

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/prd-to-issues
```

### 2.4 grill-me

**功能**：通过"连续追问"机制，直到决策树的每个分支都被解决。

**核心机制**：
- 当你提出一个方案时，Claude 会问"如果有 X 情况怎么办？"
- 当你说"我认为..."时，Claude 会挑战你的假设
- 追问直到没有新的分支出现

**典型问题模式**：
```
用户：这个 API 应该返回用户列表
Claude：如果列表为空怎么办？
用户：返回空数组
Claude：如果用户超过 1000 个怎么办？
用户：需要分页
Claude：如果用户同时在更新怎么办？需要加锁吗？
...（继续直到所有分支都被覆盖）
```

**使用场景**：
- 方案设计早期
- 技术选型讨论
- 架构决策记录

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/grill-me
```

### 2.5 design-an-interface

**功能**：使用并行子 Agent 生成模块的多个截然不同的接口设计。

**核心流程**：
1. 启动多个并行的 Claude 实例
2. 每个实例独立探索不同的设计方向
3. 汇总所有方案供选择

**设计方向示例**：
- 方案 A：命令式 API（明确的步骤）
- 方案 B：声明式 API（描述目标）
- 方案 C：函数式 API（纯函数、无副作用）
- 方案 D：OOP 风格（封装、继承、多态）

**使用场景**：
- 模块接口不明确时
- 需要探索多种设计方案时
- 团队对接口形式有争议时

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/design-an-interface
```

### 2.6 request-refactor-plan

**功能**：通过用户访谈创建详细的重构计划，包含微小提交粒度，然后作为 GitHub Issue 提交。

**与其他规划技能的关系**：

| 技能 | 输入 | 输出 |
|------|------|------|
| write-a-prd | 需求描述 | PRD 文档 |
| prd-to-plan | PRD | 实施计划 |
| request-refactor-plan | 重构需求 | 重构计划 |

**微小提交原则**：
每个重构任务应该足够小，可以单独提交、测试和回滚。这降低了重构风险。

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/request-refactor-plan
```

---

## 3. Development 技能详解

开发阶段是实现价值的核心环节。这 5 个技能覆盖了从测试驱动开发到问题诊断的完整开发流程。

### 3.1 tdd

**功能**：遵循红-绿-重构循环的测试驱动开发，以垂直切片方式构建功能或修复 Bug。

**TDD 三定律**：
1. 在写任何产品代码之前，先写一个会失败的测试
2. 只写足够的测试让测试从红变绿
3. 只写足够的 产品代码让测试从绿变绿，然后重构

**垂直切片在 TDD 中的应用**：
```
切片 1：实现最简单路径 → 测试通过
切片 2：添加错误处理 → 测试通过
切片 3：优化性能 → 测试通过
...
```

**使用场景**：
- 实现新功能时
- 修复 Bug 时
- 重构遗留代码时

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/tdd
```

### 3.2 triage-issue

**功能**：通过探索代码库调查 Bug，识别根本原因，并提交带有 TDD 修复计划的 GitHub Issue。

**调查流程**：
1. **复现**：确认 Bug 可以复现
2. **定位**：探索代码找到问题所在
3. **分析**：理解为什么这个问题会发生
4. **计划**：制定 TDD 方式的修复计划

**输出格式**：
```markdown
## Bug 描述
...

## 根本原因
...

## 复现步骤
1. ...
2. ...

## 修复计划（ TDD 方式）
- [ ] 添加测试：...
- [ ] 实现修复：...
- [ ] 重构：...
```

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/triage-issue
```

### 3.3 improve-codebase-architecture

**功能**：探索代码库寻找架构改进机会，聚焦于深化浅层模块和提升可测试性。

**分析维度**：

| 维度 | 检查点 |
|------|-------|
| 模块深度 | 是否承担足够的职责？还是只是一个代理？|
| 可测试性 | 依赖是否可注入？副作用是否可控？|
| 内聚性 | 相关功能是否放在一起？ |
| 耦合度 | 模块间的依赖是否清晰？ |

**使用场景**：
- 技术债务积累时
- 代码难以测试时
- 需要系统性改进代码质量时

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/improve-codebase-architecture
```

### 3.4 migrate-to-shoehorn

**功能**：将测试文件从 TypeScript 的 `as` 类型断言迁移到 `@total-typescript/shoehorn`。

**Shoehorn 简介**：
Shoehorn 是一个类型收窄工具，可以在运行时验证类型断言，提升类型安全。

**迁移示例**：
```typescript
// 之前：as 断言（运行时无检查）
const value = something as string;

// 之后：shoehorn 断言（运行时验证）
import { shoehorn } from '@total-typescript/shoehorn';
const value = shoehorn(string, something);
```

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/migrate-to-shoehorn
```

### 3.5 scaffold-exercises

**功能**：创建练习目录结构，包含章节、问题、解决方案和解析。

**目录结构**：
```
exercises/
├── README.md
├── 01-basic/
│   ├── problem.ts
│   ├── solution.ts
│   └── explainer.md
├── 02-intermediate/
│   ├── problem.ts
│   ├── solution.ts
│   └── explainer.md
└── 03-advanced/
    ├── problem.ts
    ├── solution.ts
    └── explainer.md
```

**使用场景**：
- 创建代码练习材料
- 构建学习路径
- 编写技术博客配套代码

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/scaffold-exercises
```

---

## 4. Tooling & Setup 技能详解

工具链是开发效率的倍增器。这 2 个技能帮助配置安全和一致的开发环境。

### 4.1 setup-pre-commit

**功能**：配置 Husky 预提交钩子，包含 lint-staged、Prettier、类型检查和测试。

**配置内容**：
```bash
# 安装后自动配置：
- Husky (.husky/)
- lint-staged
- Prettier
- TypeScript 类型检查
- 测试（Vitest/Jest）
```

**工作流程**：
```bash
git add .
git commit -m "fix: resolve bug"
# 自动触发：
# 1. Prettier 格式化
# 2. ESLint 检查
# 3. TypeScript 类型检查
# 4. 运行测试
# 全部通过才允许提交
```

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/setup-pre-commit
```

### 4.2 git-guardrails-claude-code

**功能**：配置 Claude Code 钩子，在危险 Git 命令执行前进行拦截。

**保护的命令**：
| 命令 | 危险操作 | 保护措施 |
|------|---------|---------|
| `git push --force` | 覆盖远程历史 | 要求确认 |
| `git reset --hard` | 丢失未提交的更改 | 要求确认 |
| `git clean -f` | 删除未跟踪文件 | 要求确认 |
| `git stash drop` | 丢失 stash | 要求确认 |

**使用场景**：
- 团队成员可能不熟悉 Git
- 避免误操作导致代码丢失
- Claude Code 自动执行命令时需要安全确认

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/git-guardrails-claude-code
```

---

## 5. Writing & Knowledge 技能详解

写作和知识管理是长期知识积累的关键。这 4 个技能帮助创建和维护项目文档。

### 5.1 write-a-skill

**功能**：创建具有正确结构、渐进式披露和 bundled resources 的新技能。

**技能结构规范**：
```
skill-name/
├── SKILL.md              # 必需：技能说明
├── scripts/              # 可选：可执行脚本
├── references/           # 可选：按需加载的文档
└── assets/               # 可选：输出使用的文件
```

**SKILL.md 格式**：
```markdown
---
name: skill-name
description: 技能的简短描述（触发条件）
---

# 技能名称

## 何时使用
...

## 使用方法
...
```

**渐进式披露示例**：
```markdown
---
name: my-skill
description: 当你需要...
---

# My Skill

## 快速参考（始终加载）
...

## 详细说明（按需加载）
### 高级用法
...
```

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/write-a-skill
```

### 5.2 edit-article

**功能**：通过重构章节、提高清晰度和精简文章来编辑和改进文章。

**编辑维度**：

| 维度 | 检查点 |
|------|-------|
| 结构 | 章节是否清晰？逻辑是否连贯？ |
| 清晰度 | 是否用简单语言解释复杂概念？ |
| 精简度 | 是否有冗余表达？能否更简洁？ |

**使用场景**：
- 技术博客润色
- 文档改进
- 论文修改

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/edit-article
```

### 5.3 ubiquitous-language

**功能**：从当前对话中提取 DDD 风格的通用语言词汇表。

**DDD 通用语言概念**：
通用语言是团队共享的、精确的业务术语表。每个术语在整个代码库和文档中使用相同的含义。

**输出格式**：
```markdown
## 通用语言词汇表

| 术语 | 定义 | 同义词 |
|------|------|--------|
| Order（订单）| 客户提交的购买请求 | Purchase |
| Line Item（行项目）| 订单中的单个商品 | Item |
```

**使用场景**：
- 项目初期建立通用语言
- DDD 工作坊
- 技术文档审查

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/ubiquitous-language
```

### 5.4 obsidian-vault

**功能**：在 Obsidian 保险库中搜索、创建和管理笔记，支持 wikilinks 和索引笔记。

**核心能力**：
- 搜索现有笔记
- 创建带 wikilinks 的笔记
- 自动维护索引笔记
- 管理双向链接

**典型工作流**：
```
1. 创建新笔记 → 自动生成 wikilinks
2. 引用现有笔记 → 自动建立反向链接
3. 更新索引 → 自动汇总相关笔记
```

**Obsidian Vault 简介**：
Obsidian 是一种本地优先的笔记工具，使用 Markdown 和 wikilinks（[[双括号]]语法）来创建笔记之间的连接。

**安装命令**：
```bash
npx skills@latest add mattpocock/skills/obsidian-vault
```

---

## 6. 技能管理体系

### 6.1 安装技能

所有技能使用统一的 `npx skills@latest add` 命令安装：

```bash
# 安装单个技能
npx skills@latest add mattpocock/skills/<skill-name>

# 示例
npx skills@latest add mattpocock/skills/tdd
npx skills@latest add mattpocock/skills/write-a-prd
```

### 6.2 技能加载机制

Matt Pocock Skills 遵循**渐进式披露**原则：

```
┌─────────────────────────────────────────┐
│  元数据层（始终加载 ~100 tokens）      │
│  - name: skill-name                    │
│  - description: 何时使用这个技能         │
├─────────────────────────────────────────┤
│  指令层（技能触发时加载 <500 lines）   │
│  - 详细使用说明                        │
│  - 最佳实践                            │
├─────────────────────────────────────────┤
│  Resources 层（按需加载）              │
│  - scripts/                            │
│  - references/                         │
│  - assets/                            │
└─────────────────────────────────────────┘
```

### 6.3 技能目录结构

在 Claude Code 中，技能通常存储在 `~/.claude/skills/` 或项目 `.claude/skills/` 目录：

```
~/.claude/skills/
├── mattpocock/
│   ├── write-a-prd/
│   │   └── SKILL.md
│   ├── tdd/
│   │   └── SKILL.md
│   └── ...
└── your-custom-skills/
    └── your-skill/
        ├── SKILL.md
        ├── scripts/
        └── references/
```

---

## 7. 技能组合工作流

### 7.1 新功能开发完整流程

```
┌─────────────────────────────────────────────────────────┐
│  1. write-a-prd                                       │
│  → 创建 PRD，理解需求和约束                              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. grill-me                                          │
│  → 追问需求细节，确保决策树被充分探索                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. design-an-interface                                │
│  → 探索多种接口设计，选择最佳方案                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  4. prd-to-plan                                        │
│  → 将 PRD 转化为实施计划                                │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  5. prd-to-issues                                     │
│  → 分解为可认领的 GitHub Issues                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  6. tdd（每个 Issue）                                  │
│  → TDD 方式实现功能                                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  7. ubiquitous-language                               │
│  → 更新团队通用语言词汇表                               │
└─────────────────────────────────────────────────────────┘
```

### 7.2 Bug 修复完整流程

```
┌─────────────────────────────────────────────────────────┐
│  1. triage-issue                                      │
│  → 调查 Bug，定位根因，制定修复计划                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. tdd                                               │
│  → TDD 方式修复 Bug                                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. improve-codebase-architecture（如需要）             │
│  → 防止类似 Bug 再次发生                               │
└─────────────────────────────────────────────────────────┘
```

### 7.3 重构工作流

```
┌─────────────────────────────────────────────────────────┐
│  1. request-refactor-plan                             │
│  → 创建详细重构计划                                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. prd-to-issues                                     │
│  → 分解为小任务                                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. git-guardrails-claude-code                         │
│  → 配置安全保护（防止误操作）                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  4. tdd（每个任务）                                   │
│  → 小步重构，每步可测试可回滚                           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  5. setup-pre-commit                                  │
│  → 确保新代码质量标准                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 8. 与其他技能集合的对比

### 8.1 Anthropic Skills

| 维度 | Matt Pocock Skills | Anthropic Skills |
|------|-------------------|-----------------|
| 定位 | 完整的开发流程 | 通用能力扩展 |
| 数量 | 17 个专注技能 | 更多但更通用 |
| 深度 | 深入开发实践 | 广泛覆盖 |
| 风格 | 渐进式披露 | 模板化 |

### 8.2 VibeCode 技能

| 维度 | Matt Pocock Skills | VibeCode 技能 |
|------|-------------------|---------------|
| 重点 | Planning + TDD | 快速验证 |
| 适用场景 | 生产级开发 | 快速原型 |
| 文档质量 | 强调可测试性 | 强调速度 |

---

## 9. 常见问题

### Q: 如何创建自己的技能？

A: 使用 `write-a-skill` 技能，它会引导你完成技能创建流程，包括：
- 编写 SKILL.md
- 设计渐进式披露结构
- 组织 bundled resources

### Q: 技能之间有依赖关系吗？

A: 大部分技能是独立的，可以单独使用。但规划类技能通常在开发类技能之前使用：
- write-a-prd → prd-to-plan → prd-to-issues → tdd

### Q: 如何贡献自己的技能到社区？

A:
1. 创建一个公开的 GitHub 仓库
2. 按照 Matt Pocock Skills 的结构组织
3. 使用 `npx skills@latest add owner/repo/skill-name` 格式发布
4. 在 Matt Pocock Skills 仓库提交 PR 添加你的技能链接

### Q: 技能支持自定义吗？

A: 完全支持。你可以：
- Fork 技能仓库并修改
- 按需调整技能描述和指令
- 添加自己的 scripts 和 references

---

## 10. 总结

Matt Pocock Skills 代表了 Claude Code 技能生态的一个重要方向——不是简单地提供提示词模板，而是提供**完整的开发方法论**。

**关键价值回顾**：

- **Planning & Design**：从需求到实现的完整规划体系
- **Development**：TDD、问题诊断、架构改进的开发实践
- **Tooling & Setup**：安全的工具链配置
- **Writing & Knowledge**：知识管理和文档写作

**适用人群**：

- 追求代码质量的开发者
- 希望标准化团队开发流程的 Tech Lead
- 需要系统化工作流的独立开发者

**开始使用**：
```bash
# 先安装 CLI
npm install -g @skills/cli

# 添加第一个技能
npx skills@latest add mattpocock/skills/tdd

# 在 Claude Code 中使用
/claude
> tdd
```

随着 Claude Code 技能的生态发展，Matt Pocock Skills 为我们展示了如何将 AI 能力与工程实践建议结合，打造真正提升生产力的开发体验。

---

**附录：相关资源**

- GitHub 仓库：https://github.com/mattpocock/skills
- Matt Pocock Twitter：https://twitter.com/mattpocock
- 官方文档：参见各技能的 SKILL.md