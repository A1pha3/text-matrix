---
title: "get-shit-done-redux 极速上手：用一个六指令循环把 AI 编程拉回巅峰状态"
date: "2026-05-23T03:15:00+08:00"
slug: "get-shit-done-redux-productivity-framework"
description: "get-shit-done-redux 是一个面向 AI 编程工具的元提示词与上下文工程框架，通过六个指令构成的结构化循环，在子 agent 的独立上下文中完成并行执行与验证，从而解决 AI 编程中的 context rot 问题。本文介绍其核心工作流、安装配置与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["AI编程", "Claude Code", "工作流", "上下文工程", "效率工具"]
---

# get-shit-done-redux 极速上手：用一个六指令循环把 AI 编程拉回巅峰状态

## 先给判断

get-shit-done-redux（以下简称 GSD）解决的不是"怎么写代码"的问题，而是"怎么让 AI 持续写出好代码"的问题。

它的核心思路很直接：**把一个完整的开发任务拆成多个小批次，在每个批次里给 AI 一个干净的上下文窗口，让它在独立的子 agent 里并行执行，完成后由你验收，最后才合入主干。** 这六个步骤构成了一个循环：`new-project` → `discuss-phase` → `plan-phase` → `execute-phase` → `verify-work` → `ship`。

与其说 GSD 是一个工具，不如说它是一套**让 AI 编程变得可预测的工作流协议**。作者是 solo developer，目标用户也是不想被流程拖累的个人开发者或小团队。

## 系统地图

GSD 的工作流由六条指令驱动，每条指令对应开发过程中的一个固定环节：

| 指令 | 环节 | 作用 |
|------|------|------|
| `/gsd-new-project` | 初始化 | 提问 → 研究 → 需求 → 路线图，你拍板后再开干 |
| `/gsd-discuss-phase N` | 讨论 | 捕捉设计决策（布局、API 形状、错误处理），为 Planning 喂料 |
| `/gsd-plan-phase N` | 规划 | 研究 → 规划 → 验证，循环直到方案通过 |
| `/gsd-execute-phase N` | 执行 | 并行波次执行，每个任务原子 commit，主上下文保持在 30–40% |
| `/gsd-verify-work N` | 验证 | 逐项检查已构建内容，自动生成诊断修复方案 |
| `/gsd-ship N` | 交付 | 从已验证相位创建 PR，合入主干 |

在执行层面，GSD 在后台维护一组结构化文档，贯穿 session 边界：

- `PROJECT.md`：项目愿景
- `REQUIREMENTS.md`：需求范围
- `ROADMAP.md`：阶段路线图
- `STATE.md`：当前位置与决策记录
- `CONTEXT.md`：各相位的实现决策

这些文档是 AI 每次新 session 的起点。你关闭窗口再回来，AI 知道项目在哪、做到哪一步、下一步干什么。

## 适用场景：一个具体的开发循环

假设你要做一个笔记应用，功能包括 Markdown 渲染、本地存储和搜索。以下是在 GSD 里的完整走法：

**第一步：初始化**

```bash
/gsd-new-project
```

GSD 会问一组问题：技术栈偏好、数据库方案、UI 框架要求等。回答完毕后生成 `PROJECT.md` 和 `ROADMAP.md`。你 review 确认，这个项目的方向就定下来了。

**第二步：讨论第一个相位**

```bash
/gsd-discuss-phase 1
```

第一个相位是"搜索功能"。你可能有一些具体想法：搜索框固定在顶栏、支持中文分词、搜索结果高亮关键词。这些在路线图里只是一句话，在 discuss 里你会把它展开成具体的实现约束。GSD 把这些决策写入 `CONTEXT.md`，后续 Planning 阶段直接引用，不再靠 AI 猜测。

**第三步：规划**

```bash
/gsd-plan-phase 1
```

GSD 在研究阶段会检查依赖包的合法性——推荐依赖经过审计，未知包会触发人工确认。方案通过后，`ROADMAP.md` 里对应的任务项被标记为 ready。

**第四步：并行执行**

```bash
/gsd-execute-phase 1
```

GSD 把第一个相位的任务拆成多个 plan，每个 plan 在独立的子 agent（fresh 200k token 上下文）里执行。多条任务并行跑，你的主上下文窗口始终保持在 30–40%。每个任务完成后单独 commit，不存在跨任务的大块上下文堆积。

**第五步：验收**

```bash
/gsd-verify-work 1
```

你逐项检查功能：搜索框是否在顶栏、中文分词是否生效、高亮显示是否正确。任何不通过的部分，GSD 会生成诊断报告和修复方案，直接进入下一轮 execute。这一步不靠你手动 debug，只靠你判断结果是否符合预期。

**第六步：交付**

```bash
/gsd-ship 1
```

创建 PR，review 代码，然后进入下一个相位的循环。

## 为什么这个思路有效

大多数 AI 编程工具的问题不是"能力不够"，而是"上下文窗口越长，质量下降越快"。这个问题被称为 **context rot**——当 session 里的历史记录越来越多，AI 开始混淆优先级，忘记早期的设计约束，生成越来越像"凑合能跑"的代码。

GSD 的解法是把**重活搬到子 agent 的干净上下文里**，主 session 只负责协调和验收。真正执行的那段代码是从未被打扰过的上下文里生成的，质量自然更稳定。

另一个常见问题是**没有验证环节**。AI 跑完代码说"已完成"，你就信了，但跑通不等于正确。GSD 的 verify 步骤强制你做一次人工接受测试，任何broken的部分都有诊断和修复方案等着你重跑 execute。

## 安装与初始化

```bash
npx get-shit-done-redux@latest
```

安装过程会提示你选择运行时（Claude Code、OpenCode、Gemini CLI、Cursor、Windsurf 等）和安装方式（全局或本地）。大多数场景推荐全局安装：

```bash
npm install -g get-shit-done-redux
```

由于 GSD 内置了自动化执行流程，运行时要加上 `--dangerously-skip-permissions`（或对应运行时的等效参数）：

```bash
claude --dangerously-skip-permissions
```

GSD 支持模块化安装，按需加载功能：

| 参数 | 包含内容 |
|------|----------|
| `--profile=core` | 六个核心循环指令（最小集） |
| `--profile=standard` | core + 相位管理 |
| `--profile=full`（默认） | 全部功能 |

GSD 的配置文件位于 `.planning/config.json`，可以通过 `/gsd-settings` 交互式更新，也可以手动编辑。几个常用配置项：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `mode` | `interactive` | `interactive` 需你确认每步，`yolo` 自动通过 |
| `parallelization.enabled` | `true` | 开启任务并行执行 |
| `code_quality.fallow.enabled` | `false` | 开启 structural review 预检 |

如果你已经有代码，想在现有项目里接入 GSD，先跑 `/gsd-map-codebase`，它会分析你的代码库结构和约定，生成对应的 `STATE.md`，确保后续 Planning 阶段问的问题与你的实际技术栈匹配。

## 谁适合用 GSD

GSD 面向的是**已经有 AI 编程工具（Claude Code、Cursor 等），但不满足于"让它自己跑"的结果质量**的开发者。

它不适合：
- 习惯了手动 debug、靠 session 记忆管理项目的团队
- 需要 sprint 仪式感的中大型组织（GSD 的理念是"复杂度在系统里，不在流程里"）

它特别适合：
- Solo developer，想让 AI 持续产出可用代码
- 小团队，2–5 人，希望有一套轻量但不随意的开发节奏
- 任何被"AI 写到一半开始乱来"这个问题困扰过的人

## 一个值得注意的背景

这个仓库（`open-gsd/get-shit-done-redux`）是原仓库的一个分叉（fork）。原仓库 `gsd-build/get-shit-done` 的维护者在 2026 年 4 月后失联，关联的 `$GSD` token 出现了 rug-pull 迹象。当前维护者 trek-e 公开说明了这一情况，并将包名从 `get-shit-done-cc` 迁移到了 `get-shit-done-redux`，npm 主包同步更新。如果你是从旧包名安装的，需要迁移到新包名以获取后续更新。

## 从哪里开始

GSD 的文档结构很清晰，首次使用建议按这个顺序阅读：

1. **[docs/USER-GUIDE.md](https://github.com/open-gsd/get-shit-done-redux/blob/main/docs/USER-GUIDE.md)**：完整的端到端操作路径，包括所有运行时的安装参数
2. **[docs/COMMANDS.md](https://github.com/open-gsd/get-shit-done-redux/blob/main/docs/COMMANDS.md)**：全部指令与参数手册
3. **[docs/ARCHITECTURE.md](https://github.com/open-gsd/get-shit-done-redux/blob/main/docs/ARCHITECTURE.md)**：多 agent 编排与上下文工程的内部机制

如果你是从 Claude Code 起步，直接跑 `/gsd-new-project` 是最快的切入方式——回答完问题，你就有了第一版路线图，接下来按 `discuss → plan → execute → verify → ship` 的循环走完第一个相位，基本上就理解了这套工作流的节奏。