---
title: "Spec Kit：GitHub 官方的 Spec-Driven Development 全栈指南"
date: 2026-05-14T11:40:00+08:00
lastmod: 2026-09-29T14:30:00+08:00
slug: "github-spec-kit-spec-driven-development"
github_repo: "github/spec-kit"
source_key: "gh:github/spec-kit"
description: "Spec Kit 是 GitHub 官方开源的规格驱动开发工具包，v1.0 后提供三条独立流程：规格驱动开发、缺陷修复与想法评估，配合 AI 编码智能体把需求变成有工件、可核查、可收敛的实现。本文解析其核心命令、收敛循环、扩展生态与采用建议。"
draft: false
categories: ["技术笔记"]
tags: ["GitHub", "Spec-Driven Development", "AI Agent", "Python"]
---

## 项目概览

AI 编码智能体最擅长的是把一句模糊需求膨胀成一堆看似能跑的代码。缺的不是生成速度，而是过程约束：需求停在聊天记录里，决策没有留痕，写完没人对账。[github/spec-kit](https://github.com/github/spec-kit) 要解决的就是这个问题——它是 GitHub 官方开源的规格驱动开发（Spec-Driven Development，SDD）工具包，给 AI 智能体配上结构化的流程、可复用的模板和可追溯的工件，官方口号是 "Build with a spec, fix a bug, or assess an idea — with your coding agent"。

| 指标 | 数值（2026-09-29 快照） |
|------|------|
| Stars | 139,310 |
| Forks | 12,479 |
| 语言 | Python（CLI 本体）；项目脚手架脚本可选 Bash / PowerShell / Python |
| 许可证 | MIT |
| 创建时间 | 2025-08-21 |
| 最新版本 | v1.0.12（2026-09-25） |
| 官方文档 | [github.github.io/spec-kit](https://github.github.io/spec-kit/) |

> 本文以 v1.0.12 为口径、核实于 2026-09-29。初版写作时项目还在 v0.8.10（2026-05-14），v1.0.0（2026-08-21，项目一周年）是个分水岭：命令改为 agent skills 形态，新增 converge 收敛环节，并把 bug 修复与想法评估做成独立的扩展流程。读者如在使用旧版本，部分命令名会对不上。

## 系统地图：三条流程，四种自定义机制

Spec Kit v1.0 的 README 开篇就放了一张“选流程”的表，把定位挑明：修 bug、评估想法和从零开发新功能一样，都是这个工具包的一级公民——

| 你要做的事 | 流程 | 产出 |
|------|------|------|
| 开发一个功能或应用 | 规格驱动开发（SDD，核心内置） | 一份贯穿规划、实现与收敛的规格 |
| 诊断并修复缺陷 | Bug fixing（按需安装的捆绑扩展） | 评估过的原因、限定范围的修复、留档的验证 |
| 判断一个想法值不值得投入 | Idea assessment（按需安装的捆绑扩展） | 有证据支撑的 go / 澄清 / 放弃决策 |

README 特别强调这三者是**独立入口，不是三个必经阶段**——修 bug 不需要先跑一遍 SDD 功能流程，想法评估甚至可以在没有源码的项目里使用。SDD 之外的两条以捆绑扩展形式提供，`specify extension add bug` 和 `specify extension add assess` 各一条命令装上。

在流程之外，定制体系有四种机制，各管一层：

| 机制 | 作用 | 一句话边界 |
|------|------|------|
| Extension | 添加新命令与新能力 | 做加法，如 Jira 同步、架构守护 |
| Preset | 覆盖模板、命令与术语 | 改行为，不添能力 |
| Workflow | 把命令、提示、shell 步骤、人工检查点串成自动化序列 | 支持条件、循环、fan-out/fan-in，可暂停恢复 |
| Bundle | 把上述组件打包成一个版本化安装单元 | 只做分发组合，不引入新运行时行为 |

后文逐一展开。先看主线 SDD。

## SDD 主线：十个命令，一条收敛循环

### 核心思路

传统流程里规格是“先写后扔”的过渡产物，编码一开始就进抽屉。Spec Kit 把规格变成贯穿全程的可执行工件：需求先落在 spec.md，技术方案落在 plan.md，拆解落在 tasks.md，实现照着做，最后还有一个对账环节检查代码与工件是否一致。spec-driven.md 方法论文件把这层意图写得直白——SDD "eliminates the gap by making specifications … executable"，规格与实现之间没有缝隙，只有转换。

SDD 的三条原则没有变：

1. **意图驱动**：先定"做什么、为什么"，技术选型（怎么做）推后。
2. **多步细化**：不让 AI 一步生成完整代码，而是按阶段逐层逼近，每步留工件。
3. **规格即产出物**：spec、plan、tasks 都是开发过程的正式输出，可追踪、可验证。

### 安装

前提只有两条：Python 3.11+，以及 [uv](https://docs.astral.sh/uv/)（或 pipx）。Git 反而是可选的——只有启用 git 扩展时才需要。

官方现在维护两条安装渠道：GitHub 源码（推荐，钉版本）和 PyPI 包。值得注意的是 PyPI 上的 [`specify-cli`](https://pypi.org/project/specify-cli/) 现在就是官方发布的——2026 年 5 月之前的 README 还警告"PyPI 同名包与本项目无关"，这个口径在项目上了 PyPI 之后反转，旧文读者需要更新认知：

```bash
# 渠道一：GitHub 源码，钉到具体 release（保留前导 v）
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.0.12

# 渠道二：PyPI
uv tool install specify-cli        # 或 pipx install specify-cli / pip install specify-cli
```

试而不装可以走 `uvx` 一次性运行（`uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>`）；物理隔离的网络环境则按官方 air-gapped 指南，在联网机器上构建 wheel 并用 `pip download` 打包全部依赖，目标机 `pip install --no-index --find-links=./dist specify-cli` 离线安装。

装好后初始化项目：

```bash
specify init my-project --integration copilot
cd my-project
```

`--integration` 指定要对接的编码智能体。没有传参时交互式终端会让你选，非交互环境（CI、管道）默认 Copilot。注意 git 扩展默认**不**安装，需要分支管理就手动 `specify extension add git`。

### 命令体系：6 个核心 + 4 个辅助

启动编码智能体后在对话里调用这些命令。README 强调它们是 **agent skills，不是终端命令**。调用语法因集成而异：官方命令参考以 `/speckit.specify`（点号）标注命令名，README 的 skills 模式示例与多数 skills 型集成用连字符 `/speckit-specify`，Codex CLI、ZCode 等部分智能体则用 `$speckit-*` 前缀——以 integrations 参考文档里你的 agent 说明为准。

| 命令 | Agent skill | 作用 |
|------|------|------|
| `/speckit.constitution` | `speckit-constitution` | 建立或更新项目原则 |
| `/speckit.specify` | `speckit-specify` | 定义需求与用户故事 |
| `/speckit.plan` | `speckit-plan` | 生成技术实现方案 |
| `/speckit.tasks` | `speckit-tasks` | 把方案拆成可执行任务 |
| `/speckit.implement` | `speckit-implement` | 执行任务 |
| `/speckit.converge` | `speckit-converge` | 对照工件检查实现，把缺口补成新任务 |
| `/speckit.taskstoissues` | `speckit-taskstoissues` | 可选：把任务转成 GitHub issues |
| `/speckit.clarify` | `speckit-clarify` | 可选质量门：规划前消除歧义（前身是 `/quizme`） |
| `/speckit.analyze` | `speckit-analyze` | 可选质量门：检查 spec/plan/tasks 三工件间的一致性 |
| `/speckit.checklist` | `speckit-checklist` | 可选质量门：生成需求质量清单，官方比喻是 "unit tests for English" |

官方给的记忆口诀是：**Constitution 每个项目一次；specify → plan → tasks → implement → converge 每个功能一轮**。

### 五步最小流程

以官方示例为例，五个命令走完一个照片整理应用：

**第一步，立宪法。** 定义治理原则，写入 `.specify/memory/constitution.md`，后续所有阶段拿它当决策依据：

```text
/speckit-constitution Create principles focused on code quality, testing, and maintainability.
```

**第二步，写规格。** 只说"做什么、为什么"，不碰技术栈。生成的规格落在 `specs/<feature>/spec.md`：

```text
/speckit-specify Build a photo organizer with albums grouped by date and a tile preview of each album.
```

**第三步，做规划。** 这一步才轮到技术选型，产出 plan.md 以及 research、data-model 等支撑工件：

```text
/speckit-plan Use Vite with vanilla JavaScript. Keep images local and store metadata in SQLite.
```

**第四步，拆任务。** 生成依赖排序的 `tasks.md`：

```text
/speckit-tasks
```

**第五步，实现与收敛。** `/speckit-implement` 按 tasks.md 的依赖顺序执行，实现前还会检查 checklist 复选框状态作为门禁。然后是 v1.0 新增的关键环节：

```text
/speckit-converge
```

`/speckit-converge` 把代码库对照 spec、plan、tasks 三份工件检查，结果两种：报告 **Converged** 表示实现满足全部工件，tasks.md 一字不改，可以直接进评审或开 PR；发现缺口则把缺口**追加**为 tasks.md 里 Convergence 节下的新任务，此时再跑一轮 `/speckit-implement`，实现后再次 converge。官方对循环成本的预期写在文档里："Each pass finds fewer items"——每轮发现的缺口递减，直到报告 Converged。这个循环把“AI 说做完了”变成“对照规格核验过做完了”，是 1.0 最值得用的改进。

### 一轮真实流转：工件怎么接力

把上面的流程走成一条工件链会更直观。假设团队要给现有产品加照片整理功能：

1. 宪法已就位（`.specify/memory/constitution.md`），规定了测试标准与性能要求；
2. `/speckit-specify` 把"按日期分组相册、平铺预览"写成 `specs/001-photo-albums/spec.md`，含用户故事与验收口径；
3. 觉得规格里"平铺预览"含义模糊，跑 `/speckit-clarify`，它按覆盖度逐项提问，答案记录进规格的 Clarifications 节；
4. `/speckit-plan` 选定 Vite + 原生 JS + SQLite，写出 `plan.md`，`research.md` 记录选型依据，`data-model.md` 定义相册与照片的数据结构；
5. 对质量有疑虑就加 `/speckit-checklist` 生成需求清单，`/speckit-analyze` 只读检查三工件之间的冲突与缺口；
6. `/speckit-tasks` 把设计拆成带依赖序的 `tasks.md`，并行任务有标记；
7. `/speckit-implement` 逐任务实现；`/speckit-converge` 发现"拖拽重排"没实现，追加为 Convergence 新任务；
8. 再一轮 implement 后 converge 报告 Converged，全链路每一步都有 Markdown 工件可回溯。

哪一步出问题，就回到哪一步的工件上修，而不是对着聊天记录重新口述需求。

## 两条扩展流程：修 bug 与评估想法

### Bug fixing：assess → fix → test

```bash
specify extension add bug
```

装上后按 slug 走三个 skill：

```text
/speckit-bug-assess "Submitting an empty password crashes the login form." slug=login-crash
/speckit-bug-fix slug=login-crash
/speckit-bug-test slug=login-crash
```

设计意图是让诊断、修复、验证三个阶段彼此分离——智能体修的是"评估过的原因"，并且必须回头检查原始症状。报告存在 `.specify/bugs/login-crash/`，结论三态：`verified`、`partial`、`failed`。README 里有句值得贴在团队手册里的话："Missing verification is not a successful fix"——没有验证的修复不算修复。

### Idea assessment：先取证，再决定

```bash
specify extension add assess
```

五个 skill 走完 intake → research → define → shape → decide，工件存在 `.specify/assessments/<slug>/`，最终给出 **go / needs-clarification / kill** 三态决策：

```text
/speckit-assess-intake "Let users work offline and sync when they reconnect." slug=offline-mode
/speckit-assess-research slug=offline-mode
/speckit-assess-define slug=offline-mode
/speckit-assess-shape slug=offline-mode
/speckit-assess-decide slug=offline-mode
```

这条流程刻意独立于代码库，没有源码的项目也能用——评估一个想法值不值得做，本就该发生在写第一行代码之前。未知项的处理方式是直接完善既有的 Markdown 工件，而不是重新生成整个阶段。`go` 决策可以无缝交给 `/speckit-specify` 开工；带着记录充分的理由停在 kill 上，官方也认为是有用的结果。

## 自定义生态：四种机制与一条信任边界

### 扩展：176 个社区条目，五类能力

```bash
specify extension search [query]     # 支持 --tag / --author / --verified 过滤
specify extension add <name>         # 支持 --from <url> / --dev / --priority
specify extension list / info / update / enable / disable / remove
```

社区目录（`catalog.community.json`，2026-09-28 更新）现有 **176 个扩展**，可在[社区扩展网站](https://speckit-community.github.io/extensions/)浏览检索，按官方五类划分：

| 类别 | 说明 |
|------|------|
| `docs` | 读取、校验、生成规格工件 |
| `code` | 审查、验证、修改源码 |
| `process` | 跨阶段工作流编排 |
| `integration` | 与外部平台同步（Azure DevOps、Jira 等） |
| `visibility` | 项目健康度与进度报告 |

每个扩展还带 `effect` 标注（read-only / read-write），一眼能看出它会不会改你的文件。目录里的典型条目：把决策记录拉进智能体上下文的 adrkit、给现有代码库渐进式引入 SDD 的 Brownfield Bootstrap、规格转 Gherkin 场景的 BDD、CI 里做规格合规门禁的 CI Guard。

**用之前必须知道信任边界**：官方 README 写明，维护者只验证目录条目的完整与格式正确，**不审查、不审计、不为社区扩展的代码背书**。内置的 `community` 目录是刻意设计的 discovery-only——只能搜索发现，不能一键安装。要用里面某个扩展，正确姿势是用 `specify extension info <name>` 拿到候选归档 URL，人工审查源码后 `specify extension add <name> --from <archive-url>` 安装；或者在组织内自建一个标记 `install_allowed: true` 的可信目录。这条边界和 npm 的 `postinstall` 风险是同一类问题，值得当团队安全规范执行。

### 预设：不添能力，改行为

预设覆盖模板、命令与术语，不改任何工具链——用来固化组织标准、适配方法论，或把整个工作流本地化成其他语言。多个预设可叠优先级；文件级支持 replace 之外的 prepend/append/wrap 组合策略。命令与扩展同构：`specify preset search / add / update / remove / list`。

### Workflow 与 Bundle

Workflow 把多步流程串成可重复的序列：条件逻辑、循环、fan-out/fan-in，支持在任意检查点暂停、修复后续跑（运行状态持久在 `state.json`，`specify workflow resume <run_id>` 从断点继续）。适合把"实现 → 测试 → 审查"这类固定组合固化成一键操作。

Bundle 则是分发层：一份 `bundle.yml` 清单把扩展、预设、workflow 声明成一个版本化单元，按钉住的版本一次装齐。官方一方目录里已有两个 verified bundle：`bugfix`（bug 扩展 + bugfix 工作流）和 `assess`（assess 扩展 + 评估工作流），`examples/bundles/` 下还有面向产品经理、业务分析师、安全研究员、开发者的角色化示例。

### 解析优先级

当同名文件出现在多层，官方定义的解析栈从高到低是：

1. **项目本地覆盖**：`.specify/templates/overrides/`（一次性改动首选）
2. **已安装预设**（按优先级，数字小者先）
3. **已安装扩展**（同上）
4. **Spec Kit 核心**：`.specify/templates/`

排错时用 `specify preset resolve <name>` 追踪解析栈，能看到某个文件最终由哪层提供。

## 智能体集成：40+ 个 key，含通用接入

`specify integration` 子命令族管理集成（list / search / info / install / uninstall / use / upgrade / status）。内置支持的智能体超过 40 个，常见的都在：Claude Code（`.claude/skills`）、GitHub Copilot（默认 skills 布局）、Codex CLI（`.agents/skills`，调用前缀是 `$speckit-*`）、Cursor、Gemini CLI、Qwen Code、Kimi Code、Trae、Zed、Devin、Droid 等。不在名单里的 agent 走 `generic` 集成，用 `--integration generic --integration-options="--commands-dir <path>"` 指定命令目录即可接入。Claude Code 与 Copilot 的安装方式就是 init 时指定一次 `--integration`，之后扩展与预设的命令会自动注册到当前集成。

## 适用场景与边界

### 适合

- **从零开始的功能开发**：结构化的多步流程天然匹配 greenfield，AI 在每个阶段都有明确输入输出。
- **需求模糊但方向明确**：`/speckit-clarify` 的覆盖式提问能把模糊处逐项收敛成记录在案的澄清。
- **团队要统一 AI 开发规范**：Constitution 固化原则，Preset 固化模板与术语，Bundle 把这套东西按角色分发。
- **要留痕与可追溯**：从 spec 到实现全链路都是 Markdown 工件，评审、审计、复盘都有抓手。

### 慎用

- **快速原型验证**：五个阶段的结构化开销在探索期偏重，一个 prompt 能验证的想法没必要先立宪法。
- **巨型遗留代码库的全量迁移**：官方提供了 existing-projects 指南和 Brownfield 类扩展，建议按功能渐进引入，不要一次性给整个代码库补规格。
- **离线/强管控环境**：CLI 本身支持 air-gapped 安装，但社区扩展的发现与安装要额外自建可信目录，成本不低。

## 采用建议

按团队状态给一个落地顺序：

1. **个人开发者/小团队**：PyPI 装 CLI（`uv tool install specify-cli`），挑一个常用 agent 集成，从五步最小流程开始跑一个真实功能，重点体验 converge 循环——它是这套方法论里投入产出比最高的环节。
2. **已有规范体系的团队**：先写 Constitution 把现有工程原则翻成 AI 可读的版本，再用 Preset 覆盖默认模板对齐团队文档格式，暂不引入社区扩展。
3. **平台/工程效能团队**：研究 Workflow 与 Bundle 的组合，把团队级的开发流程（含检查点）做成可分发资产；社区扩展按"discovery-only 人工审查后 --from 安装"的流程治理。
4. **暂时不必上**：纯探索期项目、以结对为主几乎不用 AI 智能体的团队——这套工具的前提是你已经在让智能体写代码。

## 总结

Spec Kit 一年走完从实验项目到 1.0 的路，靠的不是功能多，而是把"AI 写代码缺过程"这件事拆成了具体可执行的动作：需求落成规格，规格长出方案，方案拆成任务，实现对账收敛。对于已经把智能体纳入日常开发、又被"它到底做对了没有"困扰的团队，这套以规格为中心的工作流值得认真试一轮。

**参考来源与口径说明**

- 仓库与文档：[github/spec-kit](https://github.com/github/spec-kit)（v1.0.12，2026-09-25）· [官方文档](https://github.github.io/spec-kit/) · [SDD 方法论全文](https://github.com/github/spec-kit/blob/main/spec-driven.md)
- 命令与安装：本文命令、参数、目录约定对照 main 分支 README 与 docs/（`installation.md`、`install/pypi.md`、`install/one-time.md`、`install/air-gapped.md`、`reference/agentic-sdd.md`、`reference/core.md`、`reference/extensions.md`、`reference/presets.md`、`reference/workflows.md`、`reference/bundles.md`、`reference/integrations.md`、`quickstart.md`、`spec-driven.md`），核实于 2026-09-29
- 扩展数量：176 为 `extensions/catalog.community.json`（updated_at 2026-09-28）实测条目数；Stars/Forks 为 GitHub API 2026-09-29 读数
- 历史口径：初版（2026-05-14，对应 v0.8.10）中"PyPI 同名包与本项目无关"的警告是当时 README 原文，现已反转；"80+ 扩展"为旧读数，现为 176
