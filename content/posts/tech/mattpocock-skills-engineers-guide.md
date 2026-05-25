---
title: "mattpocock/skills：让 AI 编码代理真正靠谱的技能库"
date: "2026-05-14T20:32:00+08:00"
slug: "mattpocock-skills-claude-code-engineers-guide"
description: "mattpocock/skills 是一个面向真实工程师的 Claude Code 技能集，涵盖需求对齐、代码质量控制、架构守护等工程实践核心环节。本文详解四大失败模式与对应技能、目录结构、安装配置方式，以及工程实践中的具体用法。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "AI 编码", "技能系统", "工程实践", "TDD"]
---

# mattpocock/skills：让 AI 编码代理真正靠谱的技能库

> **目标读者**：已接触 Claude Code / Codex 等 AI 编码代理，想进一步提升工程交付质量的开发者
> **预计阅读时间**：20 分钟
> **前置知识**：了解 Claude Code 基本用法，有实际项目开发经验

---

## 项目概览

[mattpocock/skills](https://github.com/mattpocock/skills) 是前端 TypeScript 知名布道者 Matt Pocock维护的一个技能（Skill）集合，目前在 GitHub 上已获得 **80,000+** 星标。项目的核心主张是：

> **Developing real applications is hard. These skills are designed to be small, easy to adapt, and composable.**

这个 repo 里的每一个 skill 都以 slash command（斜杠命令）的形式存在，可以直接插入 Claude Code 的对话上下文中。与市面上追求"全自动"的其他方案不同，这里的技能刻意保持小粒度、高可控：每个 skill 只解决一个问题，工程师可以按需挑选、自由组合。

项目以 MIT 许可证开源，代码以 Shell 脚本为主，结构清晰，文档自给自足。

---

## 为什么需要这些技能

Matt Pocock 在项目 README 中总结了 AI 辅助开发最容易出问题的四个场景，每个场景都对应一种根本性的工程缺陷，而不仅仅是"AI 不够聪明"。

### 失败模式 1：Agent 做的事不是你想的

**问题**：你以为 AI 理解了你的需求，实际上它构建出了一个完全不是你想要的产物——这和人类开发中的"需求 misalignment"问题如出一辙。

**解法**：`/grill-me` 和 `/grill-with-docs`。通过系统性追问，让 AI 在动手前把每个决策分支都想清楚，形成需求共识。

### 失败模式 2：Agent 输出过于冗长

**问题**：项目初期，开发者（领域专家）和 AI 使用的是同一套词汇体系中的不同方言——AI 倾向于用 20 个词去表达 1 个词就能说清的概念。

**解法**：`/grill-with-docs` 内置的"共享语言"（Shared Language）机制。它要求在项目中维护一份 `CONTEXT.md`，专门记录项目专属术语的精确定义，让 AI 和人类使用一致的词汇表。

### 失败模式 3：代码跑不通

**问题**：即便目标和方向都对齐了，缺少反馈循环的 AI 会持续生产有问题的代码，却意识不到自己在飞盲。

**解法**：`/tdd`（测试驱动开发）和 `/diagnose`（结构化诊断）。前者强制 AI 先写失败的测试再动手实现，形成红-绿-重构循环；后者构建了一套可执行的"反馈回路构建"方法论。

### 失败模式 4：代码库变成泥球

**问题**：AI 加速了编码过程，但同时也在加速软件熵增——代码库以超出预期的速度变得越来越难维护。

**解法**：`/to-prd`、`/zoom-out`、`/improve-codebase-architecture` 等一系列架构守护技能，从设计阶段到日常维护全程控制复杂度。

---

## 核心概念：什么是 Skill

在 Matt Pocock 的体系中，一个 **Skill** 是一个结构化的行为定义，存放在 `skills/` 目录下，每个 skill 独占一个文件夹，内含至少一个 `SKILL.md`。

`SKILL.md` 的格式没有强制标准，但通常包含：

- **`name`**：命令名称（不含斜杠），如 `grill-me`
- **`description`**：一句话说明，在 AI agent 启动时被读取，决定何时调用
- **`<what-to-do>`**：核心行为指令块，告诉 agent 在这个 skill 激活时应该做什么
- **`<supporting-info>`**：支持性信息——文件结构规范、最佳实践边界等

Skill 的粒度非常小，一个 skill 对应一个 slash command，对应一个明确目标。你不需要一次性引入全部，可以按需挑选。

---

## 目录结构

```
mattpocock/skills/
├── CLAUDE.md              # Skill 注册机制说明
├── CONTEXT.md             # 领域术语与 Issue Tracker 的定义
├── README.md              # 项目总览（入口文档）
├── docs/                  # 文档目录（含 ADR 等）
│   └── adr/               # 架构决策记录
├── scripts/               # 安装脚本（skills.sh 等）
└── skills/                # 技能本体
    ├── deprecated/        # 已废弃，不再维护
    ├── engineering/       # 代码开发类技能（主仓库）
    ├── in-progress/      # 正在开发中的草稿
    ├── misc/              # 辅助工具类
    ├── personal/          # 私人使用，未推广
    └── productivity/      # 通用工作流类技能
```

官方维护的技能集中在 `engineering/`、`productivity/`、`misc/` 三个目录。每个目录顶层有 `README.md`，列出该目录下所有 skill 及其一句话描述。

---

## 快速上手（30 秒安装）

### 第一步：安装

```bash
npx skills@latest add mattpocock/skills
```

### 第二步：选择要引入的技能

安装脚本会列出所有可选 skill，提示你选择将哪些安装到哪些编码 agent。**务必选择 `/setup-matt-pocock-skills`**，否则其他 skill 无法正常初始化配置。

### 第三步：运行初始化

```bash
/setup-matt-pocock-skills
```

初始化过程会依次询问：

- **Issue Tracker 使用哪种**：GitHub Issues / Linear / 本地文件
- **Triage 标签体系**：给 Issue 打标签时用什么词汇表
- **文档存放位置**：由 skill 新建的所有文档（如 `CONTEXT.md`、ADR 等）存放路径

完成后，就可以按需调用各个 skill 了。

---

## Engineering 类技能详解

> 位置：[skills/engineering/](https://github.com/mattpocock/skills/tree/main/skills/engineering)

这是最核心也是最常用的技能集合。

### `/grill-with-docs` — 需求对齐 + 共享语言建设

**适用场景**：当你有一个新功能或重构计划需要和 AI 讨论时使用。

核心工作方式是一轮接一轮的追问——AI 每次只问一个问题，你回答后它基于答案生成下一个问题，直到把决策树的每个分支都覆盖到。

过程中有两个关键动作：

1. **术语对齐**：如果你的回答中出现了与 `CONTEXT.md` 现有定义矛盾的词汇，AI 会立刻指出并要求澄清
2. **更新文档**：每澄清一个术语，AI 立即更新 `CONTEXT.md`，不批量处理

这个 skill 还会在追问过程中创建 ADR（Architecture Decision Record）文档，记录重要设计决策及其理由。

### `/grill-me` — 纯追问，简洁版

**适用场景**：不需要写文档，只需要把需求本身对齐的场景。

工作方式和 `/grill-with-docs` 一致，但没有更新文档的步骤，更轻量。

### `/tdd` — 测试驱动开发

**适用场景**：构建新功能或修复 bug。

核心原则：测试应该通过公共接口验证行为，而不是验证实现细节。好的测试读起来像规格说明书——"用户可以用有效购物车结算"，这才是正确的测试姿势。

工作流遵循 **红-绿-重构**（Red-Green-Refactor）循环，每次只处理一个功能点（vertical slice），不允许"先写完全部测试再写实现"的水平分片式做法。

相关文件：
- `tests.md`：好/坏测试示例与判断标准
- `mocking.md`：mock 使用边界指南
- `deep-modules.md`：深模块设计原则

### `/diagnose` — 结构化调试

**适用场景**：出现 bug 或性能问题时使用。

最核心的观点是：**构建反馈回路就是调试本身**，一切其他步骤都是机械执行。

`diagnose` skill 将反馈回路的构建方式分成了 10 个优先级递减的策略，从"失败的测试"到"人工辅助脚本"，并强调对反馈回路本身进行迭代优化（更快、更准、更稳定）。

### `/triage` — Issue 分诊

**适用场景**：管理项目 Issue 时使用。

通过一个状态机对 Issue 进行分类，每个状态对应 Issue Tracker 中的一个标签字符串。分诊结果帮助团队决定先处理什么、后处理什么。

### `/to-prd` — 对话转 PRD

**适用场景**：已有的讨论内容需要转化为正式的 PRD 文档并提交为 GitHub Issue。

不需要追问，直接将对话中已讨论的内容合成一份 PRD，省去中间访谈环节。

### `/to-issues` — PRD 转独立 Issue

**适用场景**：PRD 写好后，需要拆解为独立可取的 GitHub Issue。

使用"垂直分片"（vertical slice）原则，将一个大需求拆成多个可独立开发、测试、上线的最小工作单元。

### `/zoom-out` — 系统级视角

**适用场景**：AI 在某个局部代码区域工作太久，失去了对整体系统的感知时使用。

强制 AI 放大视野，从整个系统的角度解释当前代码的上下文和关联。

### `/improve-codebase-architecture` — 架构拯救

**适用场景**：代码库已经出现"泥球"迹象，需要系统性重构时使用。

分析 `CONTEXT.md` 中的领域语言、`docs/adr/` 中的历史决策，找出代码库中深层机会（deep modules），并给出重构建议。Matt 建议每隔几天跑一次。

### `/prototype` — 原型验证

**适用场景**：设计阶段需要快速验证可行性时使用。

构建一个可丢弃的原型，可以是：针对状态/业务逻辑问题的命令行终端应用，或者多个差异较大的 UI 方案（通过路由切换）。

### `/setup-matt-pocock-skills` — 初始化配置

**适用场景**：每个项目只需要运行一次，放在其他工程技能之前。

它的职责是脚手架式配置：确定 Issue Tracker、标签词汇表、文档布局。这些信息被其他所有工程 skill 消费。

---

## Productivity 类技能详解

> 位置：[skills/productivity/](https://github.com/mattpocock/skills/tree/main/skills/productivity)

### `/caveman` — 极简沟通模式

把沟通压缩到极致，削减约 75% 的 token 消耗，同时保持完整的技术准确性。适合在上下文窗口紧张时使用。

### `/handoff` — 交接文档

将当前对话压缩成一份交接文档，另一位 agent（或下次对话）可以基于这份文档继续工作，而不是从头复盘。

### `/write-a-skill` — 编写新 Skill

帮助你创建结构正确、渐进式披露、配套资源完整的 skill。Matt 建议：如果某个模式在你的工作流中重复出现三次以上，就值得写成一个 skill。

---

## Misc 类技能

> 位置：[skills/misc/](https://github.com/mattpocock/skills/tree/main/skills/misc)

| Skill | 说明 |
| ---- | ---- |
| `git-guardrails-claude-code` | 为 Claude Code 配置 Git 守卫，阻止危险命令（`push`、`reset --hard`、`clean` 等）执行 |
| `migrate-to-shoehorn` | 将测试文件中的 `as` 类型断言迁移到 `@total-typescript/shoehorn` |
| `scaffold-exercises` | 创建练习目录结构（sections、problems、solutions、explainers） |
| `setup-pre-commit` | 配置 Husky pre-commit hooks，含 lint-staged、Prettier、类型检查、测试 |

---

## 工程实践：典型工作流

### 场景：接手一个新功能

```
1. /setup-matt-pocock-skills      # 初始化项目配置（仅首次）
2. /grill-with-docs               # 对齐需求，建立共享语言
3. /to-prd                        # 将讨论合成 PRD
4. /to-issues                     # PRD 拆解为可独立开发的 Issue
5. /tdd                           # 逐个 Issue 实现，遵循红-绿-重构
```

### 场景：修复一个疑难 bug

```
1. /diagnose                      # 构建反馈回路，找到根因
2. /tdd                           # 加一个回归测试保护
```

### 场景：日常架构健康检查

```
/improve-codebase-architecture    # 每隔几天跑一次，避免泥球化
/zoom-out                         # 需要时放大视角，理解全局
```

---

## 定制化：让技能成为你自己的

这些 skill 是**可修改的**。Matt 的设计哲学是：

> Hack around with them. Make them your own.

Skill 的文件全部在本地 `~/.claude/skills/` 目录下，每个 skill 的 `SKILL.md` 直接可见，可以按需删改指令、调整工作流。你不需要等待上游合并，自己 fork 一份改完直接用。

如果想把自己重复三次以上的行为写成 skill，`/write-a-skill` 可以指导你完成结构设计。

---

## 写在最后

Matt Pocock 在 README 结尾引用了 Kent Beck 的一句话：

> "Invest in the design of the system _every day_."

这套技能库的核心价值，不是让 AI 替你做更多事，而是**让 AI 的输出符合真实工程师的质量标准**。它用工程纪律去约束 AI 的随机性——通过需求对齐控制方向，通过反馈循环控制质量，通过架构守护控制复杂度。

80,000+ 星标背后，是大量真实项目中反复验证过的工程实践。如果你还没试过，值得花 30 秒安装、挑一个 skill 体验一下。

---

**相关链接**

- GitHub 仓库：[https://github.com/mattpocock/skills](https://github.com/mattpocock/skills)
- 安装方式：`npx skills@latest add mattpocock/skills`
- Matt Pocock  newsletter：~60,000 开发者订阅，[Sign Up](https://www.aihero.dev/s/skills-newsletter)