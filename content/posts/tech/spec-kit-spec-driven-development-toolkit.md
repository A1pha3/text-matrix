---
title: "Spec Kit：GitHub 官方推出的规范驱动开发工具包，让规格文档直接生成代码"
date: "2026-05-14T16:08:00+08:00"
slug: "spec-kit-spec-driven-development-toolkit"
github_repo: "github/spec-kit"
source_key: "gh:github/spec-kit"
description: "Spec Kit 是 GitHub 官方开源的规范驱动开发（SDD）工具包，通过将规格文档变成可执行资产，直接生成工作实现而非仅作为编码指导。v1.x 版本包含规范驱动开发、bug 修复、想法评估三条流程，40 个 AI 编码 Agent 集成，以及扩展、预设、工作流、捆绑包四层定制机制。"
draft: false
categories: ["技术笔记"]
tags: ["Spec-Driven Development", "GitHub", "AI Coding Agent", "Python"]
---

# Spec Kit：GitHub 官方推出的规范驱动开发工具包，让规格文档直接生成代码

## 学习目标

读完本文后，你应该能够：

1. 理解 Spec Kit 的核心思路——把规格文档提到 AI 编码流程的第一位，让代码和原始意图之间的关联不再断裂
2. 区分 Spec Kit 工作流中的两个关键角色（Specify CLI 和 AI 编码 Agent）及其产物
3. 独立完成 Spec Kit 的安装、项目初始化和与 AI Agent 的集成
4. 按 need 选对三条流程之一：规范驱动开发、bug 修复、想法评估
5. 写出一份合格的规格，包含功能描述、验收条件和边界情况
6. 判断 Spec Kit 是否适合你的团队场景，以及按什么顺序引入风险最低

## 目录

- [学习目标](#学习目标)
- [Spec Kit 解决什么](#spec-kit-解决什么)
- [系统地图：两个关键角色](#系统地图两个关键角色)
- [工作流：从规格到代码的五步](#工作流从规格到代码的五步)
- [不止写新功能：三条流程](#不止写新功能三条流程)
- [一个最小流转案例](#一个最小流转案例)
- [Specify CLI：安装与初始化](#specify-cli安装与初始化)
- [规格怎么写](#规格怎么写)
- [社区生态](#社区生态)
- [技术细节](#技术细节)
- [适合谁、什么时候用](#适合谁什么时候用)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [常见问题](#常见问题)

## Spec Kit 解决什么

大多数 AI 编码工具的工作方式是：你给一句 prompt，它生成一段代码。这种方式的问题在于，prompt 的生命周期很短——写完就丢了，代码和原始意图之间的关联也随之断裂。

Spec Kit 把规格文档提到 AI 编码流程的第一位：不是让 AI 从模糊 prompt 猜你的意图，而是从一份结构化的规格文档出发，生成符合规格的代码。规格文档不再是用完就扔的产物，而是后续所有改动的起点。

这个思路叫规范驱动开发（Spec-Driven Development，SDD）。规格在传统流程里只是编码前的一道脚手架，写完就丢；SDD 反过来把规格当作长期存活的契约，代码、测试、改动都以它为基准。Spec Kit 是这套思路的官方实现：仓库由 Den Delimarsky 于 2025 年 8 月 21 日建立初始提交，以 GitHub 官方名义开源，MIT 协议。到 2026 年 10 月，仓库约 14 万 Stars、1.25 万 Forks，仍是 AI 编码方向增长最快的项目之一。

2026 年 8 月 21 日，项目一周年当天发布 v1.0.0，此后进入 1.x 稳定线（截至 2026 年 10 月初最新 release 为 v1.1.0）。

## 系统地图：两个关键角色

Spec Kit 的工作流里有两个角色在配合，各自管不同的事：

| 角色 | 做什么 | 产物 |
|------|--------|------|
| **Specify CLI** | 管理项目初始化、生成规格与计划、提供 `/speckit-*` 技能 | 目录结构、规格、计划、任务清单 |
| **AI 编码 Agent**（Copilot / Claude Code 等） | 根据规格文件生成、修改、验证代码 | 源代码、测试、实现 |

Specify CLI 不直接生成代码——它生成的是给 AI Agent 吃的结构化输入。AI Agent 不管理项目结构——它只负责把规格翻译成实现。

## 工作流：从规格到代码的五步

Spec Kit 的工作流是一组技能驱动的阶段，每个阶段产出一份 Markdown 产物，喂给下一个阶段。官方对节奏的概括是：constitution 每个项目定一次，specify → plan → tasks → implement → converge 每个功能走一轮。最短路径是五步：

```text
1. /speckit-specify     描述要做什么（what 和 why，不谈技术栈）
2. /speckit-plan        选定技术栈，产出设计
3. /speckit-tasks       拆出带依赖顺序的任务清单 tasks.md
4. /speckit-implement   按依赖顺序执行任务，生成代码
5. /speckit-converge    对照规格核验代码，有缺口就补任务再实现
```

converge 是最后一道闸门：它核对实现是否满足 spec、plan、tasks 三份产物，通过时报告 `✅ Converged`，没通过就列出缺口。没收敛之前，回到 implement 再跑一轮。

生产级功能可以走完整路径，多出四道质量闸门：

```text
/speckit-constitution   先定项目原则，后续每一步都对照它
/speckit-specify
/speckit-clarify        针对规格里含糊的部分追问，把答案折回规格
/speckit-plan
/speckit-checklist      生成需求级质量检查清单，验证规格完备
/speckit-tasks
/speckit-analyze        只读检查 spec.md / plan.md / tasks.md 的冲突与缺口
/speckit-implement
/speckit-converge
```

两个细节值得记。其一，`/speckit-*` 是参考文档的写法，实际调用形式随 Agent 不同：Copilot 默认技能模式用 `/speckit-specify`，Codex 和 ZCode 用 `$speckit-specify`，Kimi 用 `/skill:speckit-specify`——命令名一致，前缀随宿主而定。这些是 Agent 聊天里调用的技能，不是终端命令。其二，Spec Kit 通过 `.specify/feature.json` 记录当前功能目录，切换功能时自动重写；它是本机状态，不应提交进版本库，也不依赖 Git 分支来判断在改哪个功能。

## 不止写新功能：三条流程

v1.x 把 Spec Kit 从"写新功能的工具"扩展成了三个独立的入口，各自解决一类问题：

| 你要做什么 | 流程 | 产出 |
|------|------|------|
| 开发一个功能或应用 | 规范驱动开发（SDD，核心自带） | 贯穿规划、实现、收敛全程的规格 |
| 诊断并修复一个坏掉的行为 | bug 修复（可选扩展） | 评估过的根因、有边界的修复、记录在案的验证 |
| 判断一个想法值不值得投入 | 想法评估（可选扩展） | 有证据支撑的 go / clarify / stop 决定 |

三条流程是独立入口，不是三个必经阶段。SDD 随核心安装；后两条以扩展形式按需安装，装完各得一组技能：

```bash
# 在项目目录安装 bug 修复扩展
specify extension add bug
# 技能：assess（评估根因）→ fix（按根因修复）→ test（验证原症状）
# 报告落在 .specify/bugs/<slug>/，最终结论是 verified / partial / failed

# 安装想法评估扩展
specify extension add assess
# 技能：intake → research → define → shape → decide
# 产物落在 .specify/assessments/<slug>/，最终决定是 go / needs-clarification / kill
```

想法评估这条流程不要求项目里已有代码——它可以在动手之前帮你判断一个想法值不值得做，评估产出的 go 决定可以直接交给 `/speckit-specify` 开始实现。bug 修复则刻意把诊断、修复、验证拆成三步，让 Agent 修的是评估过的根因，并回头检查原始症状；没有验证通过的修复不算修完。

v1.0.0 的 release notes 里有一段值得一读的判断：过去 semver 的主版本号是一份保险，保的是"变更成本"——破坏性变更要人逐行照着迁移指南改调用点，所以大家需要"冻结主版本"的安全感。如今把 diff 丢给 Agent，它能在几分钟内改完所有调用点，迁移指南从"你读"变成"你的 Agent 替你消费"，稳定性的溢价随之崩塌。这也是 Spec Kit 敢于在迭代一年后直接发布 1.0、又保持高频发版（v1.0.0 到 v1.1.0 之间隔了十几个 patch）的底气：对 Agent 而言，适应变化比冻结变化更便宜。

## 一个最小流转案例

假设要给一个 Python 项目加一个 `/export` API 端点，返回 JSON 和 CSV 两种格式。

**不用 Spec Kit**：打开 Copilot Chat → 输入 "add an /export endpoint that returns JSON and CSV" → Copilot 生成一段代码 → 手动检查输出字段对不对、边界情况有没有处理 → 来回改 prompt。

**用 Spec Kit 的流程**：

```text
1. specify init . --integration copilot
   → 项目里生成 Specify 配置和规格模板

2. 运行 /speckit-specify：
   → 描述 /export 端点要返回什么（what），不讨论具体实现（how）
   → 写清验收条件：空数据集返回什么、CSV 是否带 BOM

3. /speckit-plan 选定技术栈，/speckit-tasks 拆任务
   → Agent 不仅生成 endpoint，还会按验收条件生成对应的测试

4. 需求变更时，先改规格，再让 Agent 重新走 tasks → implement → converge
   → 代码和规格始终保持一致
```

整个流程里，规格文件是唯一的事实来源。AI Agent 每次生成的代码都以这份文件为准，不再依赖对话历史里散落的 prompt。

## Specify CLI：安装与初始化

Spec Kit 的核心工具是 Specify CLI，要求 Python 3.11+，官方推荐用 `uv` 从 PyPI 安装：

```bash
# 安装（依赖 uv）
uv tool install specify-cli

# 验证安装
specify version

# 初始化新项目（交互式选择 AI Agent）
specify init my-project

# 在现有项目中初始化，显式指定集成
specify init . --integration copilot
```

常用命令：

```bash
# 检查已安装的工具链
specify check

# 一步安装并运行（不常驻安装）
uvx specify init my-project --integration copilot

# 查看全部可用集成
specify integration list
```

`specify init` 会交互式让你选目标 AI Agent，也可以用 `--integration` 参数显式指定（例如 `--integration copilot`）。截至 2026 年 10 月，官方集成表收录 40 个 Agent，涵盖 Copilot、Claude Code、Gemini CLI、Codex、Cursor、Kimi Code、Trae、Zed 等；如果你的工具不在列表里，`generic` 集成作为兜底，任何 CLI 都能接入。升级已安装的 Spec Kit 参照官方文档的 Upgrade 指引，不要手动改动 `.specify/` 里由 CLI 管理的文件。

## 规格怎么写

规格不是让 AI 猜的自由文本，而是有结构的。官方仓库自带 spec、plan、tasks、constitution、checklist 五套模板，一个合格的功能规格至少回答三个问题：

- **要做什么（what）**：功能的行为描述，聚焦意图，不写技术实现。
- **验收条件**：Agent 判断代码是否达标的依据。模糊的验收条件（例如"正确处理错误"）会让 Agent 理解偏差，生成不符合预期的代码。
- **边界情况**：空输入、异常数据、格式细节（比如 CSV 的 BOM）这些容易漏掉的场景，写进规格里，Agent 才会去处理。

写法上记住一条：specify 阶段谈 what 和 why，plan 阶段才谈技术栈。在规格阶段过早决定"用什么框架、数据库"会锁死 Agent 的优化空间，也容易让规格和实现耦合。

## 社区生态

官方文档把定制机制分成五层，各管一件事：

- **集成（Integrations）**：对接不同 AI Agent 的适配层
- **扩展（Extensions）**：给 CLI 加能力，bug 修复和想法评估就是两个官方扩展；1.0 发布时社区目录已收录 157 个，出自 70 多位作者
- **预设（Presets）**：覆盖默认模板行为，1.0 时社区目录收录 33 个，适合团队统一规格风格
- **工作流（Workflows）**：把重复步骤自动化
- **捆绑包（Bundles）**：把扩展、预设、工作流按角色打成一组，例如给"评审者"或"架构师"配好整套环境

另有演练（Walkthroughs）提供逐步指南。实际用的时候按需选择，不必一开始全装上。

## 技术细节

- **语言**：Python（3.11+）
- **安装方式**：从 PyPI 发布，官方推荐 `uv tool install specify-cli`；也可用 pipx 或一次性 `uvx` 运行
- **协议**：MIT
- **版本节奏**：2026 年 8 月 21 日发布 v1.0.0，10 月初已到 v1.1.0；PyPI 包名为 `specify-cli`。迭代快，关注 Release Notes 比关注 Roadmap 更能判断当前可用程度
- **文档**：托管在 GitHub Pages [github.github.io/spec-kit](https://github.github.io/spec-kit/)
- **生态规模**：1.0 发布时（2026 年 8 月）官方数据为 157 个社区扩展、33 个预设、270+ 贡献者；官方集成表到 2026 年 10 月已收录 40 个 Agent

## 适合谁、什么时候用

**适合先上的团队**：

- 产品规格文档已经存在，但和代码实现脱节
- AI 编码 Agent 已经用起来了，但生成结果的质量波动大
- 多人协作时，不同人写 prompt 风格差异导致代码风格不一致

**可以先等等的场景**：

- 团队还在探索阶段，尚未形成稳定的规格编写习惯
- 项目规模小、单人开发、需求变化极快——此时规格维护成本可能超过收益
- 已经有一套成熟的代码审查和测试流程，且运转良好

**从哪开始**：挑一个需求明确、边界清晰的小功能，走一遍"写规格 → Agent 生成 → 验证"的完整流程。评估规格是否真的减少了返工，再决定是否推广到更大范围。

## 自测题

1. **Spec Kit 解决的核心问题是什么？对比「直接写 prompt」，它的长期优势在哪里？**
   答：规格文档是持久化的——需求变更时先改规格，再让 Agent 重新生成。Prompt 是一次性的，代码和原始意图之间的关联随对话结束而断裂。

2. **Specify CLI 和 AI Agent 的分工是什么？**
   答：Specify CLI 管理项目初始化、生成规格与计划、提供 `/speckit-*` 技能；AI Agent 根据规格文件生成、修改、验证代码。CLI 不生成代码，Agent 不管理项目结构。

3. **v1.x 的三条流程分别解决什么问题？哪条不需要项目里已有代码？**
   答：SDD 用于开发新功能，bug 修复流程把诊断、修复、验证拆开以确保修的是根因，想法评估流程在投入之前用证据决定 go / needs-clarification / kill。想法评估不需要已有代码。

4. **converge 阶段做什么？什么结果才算通过？**
   答：核对实现是否满足 spec、plan、tasks 三份产物，通过时报告 `✅ Converged`；未通过则列出缺口，回到 implement 再跑一轮，直到收敛。

5. **`--integration` 参数的作用是什么？Agent 不在支持列表里怎么办？**
   答：选择目标 AI Agent，让 Spec Kit 生成对应的技能文件和目录结构。官方集成表收录 40 个 Agent（截至 2026 年 10 月）；不在列表里的工具可用 `generic` 集成接入。

6. **如果团队还没形成稳定的规格编写习惯，直接上 Spec Kit 会遇到什么问题？**
   答：规格文件本身需要投入时间编写和维护。如果需求变化极快、项目规模小、单人开发，规格维护成本可能超过收益。

## 进阶路径

### 阶段一：基础使用（1-2 天）

- 安装 Specify CLI（推荐用 `uv tool install specify-cli`）
- 用 `specify init . --integration copilot` 在现有项目中初始化
- 写一个最小的功能规格（一个功能的描述、验收条件、边界情况）
- 让 Agent 走一遍 specify → plan → tasks → implement → converge，对比「有规格」和「没规格」的输出差异

### 阶段二：规格编写习惯（3-5 天）

- 把团队现有的一个需求写成规格，走一遍完整流程
- 学习官方文档的规格模板示例，理解验收条件怎么写才能被 Agent 正确理解
- 评估：规格是否真的减少了返工？哪些地方 Agent 仍然会理解偏差？

### 阶段三：团队推广（1-2 周）

- 挑一个边界清晰的小功能，在团队内走完整流程
- 评估不同人写的规格质量差异，是否需要统一的规格编写规范
- 如果有常用模式（例如 CRUD 端点的标准验收条件），写成预设（Presets）共享

### 阶段四：定制与贡献（可选）

- 安装 bug 修复或想法评估扩展，把 SDD 之外的场景也纳入同一套工作流
- 编写一个扩展（Extension），为团队常用的框架生成规格模板
- 写一个演练（Walkthrough），帮助新人上手 Spec Kit
- 给官方仓库提 PR——GitHub 维护，社区友好

## 常见问题

**1. `uv` 没装，还能用 Spec Kit 吗？**
   可以。Spec Kit 也支持 pipx，或直接用 `uvx` 一次性运行 `specify`，不常驻安装。装好 `uv` 是最省事的方式。

**2. 我的 Agent 不在支持列表里，怎么办？**
   用 `--integration generic` 初始化。它不生成特定 Agent 的技能文件，而是给出一套通用结构，任何能执行 shell 命令的 Agent 都能配合使用。

**3. 规格文件会不会变成新的维护负担？**
   会，这正是它的取舍。规格只有在需求稳定的团队里才划算；单人小项目、需求频繁变动的场景，规格维护成本可能超过收益。建议先挑一个小功能试点，用数据说话再推广。

**4. 我已经有成熟的测试流程，还需要 Spec Kit 吗？**
   不一定。Spec Kit 解决的是"代码与意图脱节"的问题，而不是测试问题。测试流程运转良好的团队，可以先评估现有流程是否已经能保证代码符合预期，再决定要不要引入规格层。

**5. `/speckit-*` 命令在我的 Agent 里用不了，是什么原因？**
   命令前缀随 Agent 而定：Copilot 默认技能模式用 `/speckit-specify`，Codex 和 ZCode 用 `$speckit-specify`，Kimi 用 `/skill:speckit-specify`。先确认你的 Agent 支持哪种形式，命令的实际动作是一致的。另外这些技能要在 Agent 的聊天里调用，不是在终端里敲。

**6. 怎么升级已初始化的项目里的 Spec Kit？**
   参照官方文档的 Upgrade 指引操作。`.specify/` 目录里由 CLI 管理的文件不要手动改——`feature.json` 之类的本机状态会在切换功能时自动重写，手动改动会在刷新时被覆盖。

---

**延伸阅读**：[官方文档](https://github.github.io/spec-kit/) · [GitHub 仓库](https://github.com/github/spec-kit) · [Quick Start 指南](https://github.github.io/spec-kit/quickstart.html) · [Agentic SDD 参考](https://github.github.io/spec-kit/reference/agentic-sdd.html) · [项目历史](https://github.github.io/spec-kit/history.html)
