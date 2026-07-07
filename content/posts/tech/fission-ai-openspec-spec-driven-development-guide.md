---
title: "OpenSpec 深度拆解：把 Spec-Driven Development 写进 25+ AI 编码助手的同一套协议"
date: 2026-06-28T18:06:10+08:00
slug: "fission-ai-openspec-spec-driven-development-guide"
description: "OpenSpec 是 Fission-AI 开源的轻量级 AI 编码助手 spec 协议层，通过 specs/ 真相 + changes/ 提案 + delta specs 三件套，把「先对齐再写代码」的工作流统一带到 25+ AI 工具。本文拆解其 5 个核心概念、双半架构与跨工具适配设计。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Spec-Driven Development", "OpenSpec", "Claude Code", "Cursor"]
---

# OpenSpec：把 Spec-Driven Development 带进 25+ AI 编码助手

## 学习目标

读完本文，你应该能够：

- 说清 OpenSpec 的「轻量级 spec 协议层」定位，以及它和「给 AI 助手加一层 prompt 指令集」的本质区别
- 区分 `specs/`（当下真相）与 `changes/`（提案），以及 delta specs 为什么能直接用在 5 万行存量系统上
- 用 CLI（`openspec init / list / view`）与 slash command（`/opsx:explore / propose / apply / archive`）双半架构，走完一次完整变更闭环
- 看懂 OpenSpec 适配 25+ 工具的「Skill vs Command」两套文件生成逻辑，以及 slash 语法因工具而异的设计取舍
- 评估 OpenSpec 与 GitHub Spec Kit / AWS Kiro / 不用 spec 的差异，以及它适用与不适用的边界

## 目录

- [学习目标](#学习目标)
- [一句话判断](#一句话判断)
- [仓库速览](#仓库速览)
- [系统地图：specs/ vs changes/，CLI vs /opsx:*](#系统地图specs-vs-changescli-vs-opsx)
- [五个核心概念](#五个核心概念)
- [任务流案例：从 /opsx:explore 到 /opsx:archive](#任务流案例从-opsxexplore-到-opsxarchive)
- [CLI 与 Slash Command 的边界](#cli-与-slash-command-的边界)
- [跨 25+ 工具适配：Skill vs Command](#跨-25-工具适配skill-vs-command)
- [与同类工具的差异](#与同类工具的差异)
- [采用顺序与适用边界](#采用顺序与适用边界)
- [一些细节](#一些细节)
- [仓库地址](#仓库地址)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [常见问题](#常见问题)

## 一句话判断

OpenSpec 不是给某个 AI 编码助手加的「又一层指令集」，而是给整个 AI 编码生态引入的一个**轻量级 spec 协议层**——用 `specs/` 装真相、`changes/` 装提案、`delta specs` 装差异，再通过 CLI 与 `/opsx:*` slash command 双半架构把同一套工作流送到 25+ AI 工具里。它的真正价值不在 prompt 模板多漂亮，而在让「先同意再写代码」这件事变得**可跨工具、可回放、可归档**。

## 仓库速览

| 项目 | 信息 |
|------|------|
| 仓库 | [github.com/Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) |
| 描述 | Spec-driven development (SDD) for AI coding assistants |
| 编程语言 | TypeScript |
| License | MIT |
| 首次发布 | 2025-08-05 |
| 最新 Release | v1.4.1（2026-06-03） |
| 安装方式 | `npm install -g @fission-ai/openspec@latest` |
| 运行时 | Node.js 20.19.0+ |
| 适配 AI 工具 | 25+（Claude Code、Cursor、Windsurf、Codex、Kiro、Kimi CLI 等） |

## 系统地图：specs/ vs changes/，CLI vs /opsx:*

OpenSpec 的全部概念都可以塞进一张图。先看这张图，后面所有讨论都从这里展开。

```text
                ┌─────────────────────────────────────────────────┐
                │                    openspec/                     │
                │                                                  │
                │   ┌──────────────────┐     ┌──────────────────┐   │
                │   │     specs/       │     │    changes/      │   │
                │   │                  │ ◄── │                  │   │
                │   │  source of truth │ merge│   one folder    │   │
                │   │  (系统当下行为)  │  on │   per change     │   │
                │   │                  │archive│  proposal ·     │   │
                │   │                  │     │  design · tasks │   │
                │   └──────────────────┘     │  + delta specs  │   │
                │                            └──────────────────┘   │
                └─────────────────────────────────────────────────┘

            YOUR TERMINAL                         YOUR AI ASSISTANT'S CHAT
       ┌──────────────────────┐           ┌─────────────────────────────┐
       │  $ openspec init     │  installs │  /opsx:explore               │
       │  $ openspec list     │ ────────► │  /opsx:propose add-dark-mode │
       │  $ openspec view     │  commands │  /opsx:apply                 │
       │                      │   & skills│  /opsx:archive               │
       └──────────────────────┘           └─────────────────────────────┘
            run openspec here                  run /opsx:* here
```

两个核心二分：

1. **存储二分**：`specs/` 是系统当下的真相（how things work today），`changes/` 是正在被提议的变更（what we're proposing）。归档（archive）把后者合进前者。
2. **执行二分**：CLI 命令（`openspec init / list / view`）跑在终端里，slash 命令（`/opsx:explore / propose / apply / archive`）跑在 AI 助手的对话里。前者是引擎，后者是方向盘。

这种双半架构是 OpenSpec 能跨 25+ AI 工具的根本原因——引擎只写一次，方向盘按工具适配。

## 五个核心概念

OpenSpec 文档把所有概念收敛成五个词。理解这五个词，剩下的就是细节。

### 1. Specs 是真相

Specs 描述系统**当下**的行为，住在 `openspec/specs/`，按 domain 组织（`auth/`、`payments/`、`ui/`）。一个 spec 文件由 requirements（"系统 SHALL..."）和 scenarios（given/when/then 示例）组成。

换句话说，specs 是「这个软件究竟在做什么」的单一答案。当你六个月后再打开仓库，spec 就是给未来你和下一个 AI 助手的现成交接文档。

### 2. Change 是一个工作单元

当你想加、改、删某个行为，就创建一个 change——`openspec/changes/` 下一个独立文件夹，里面装这个工作的全部产物（proposal、design、task list、spec delta）。

一个 change、一个文件夹、一个 feature。

### 3. Delta Specs 描述「变化」而非「全部」

这是 OpenSpec 处理**存量系统**的关键设计。

在 change 内部，你不用重写整个 spec，而是写一个小的 delta：这条 requirement 是 `ADDED`，那条是 `MODIFIED`，另一条是 `REMOVED`。delta 把 spec 改造成「描述差异」而不是「描述目标」。

这条设计让 OpenSpec 能用在一个 5 万行的存量应用上——你不必先把整个系统文档化，才能开始下一项改动。

### 4. Artifacts 递进但不强约束

每个 change 包含几个文档，自然顺序是：

```text
proposal ──► specs ──► design ──► tasks ──► implement
   why        what       how       steps      do it
```

每个产物喂给下一个，但**任何时候都可以回头改**。Discover during implementation that the design was wrong? Edit `design.md` and keep going. OpenSpec 的原话叫 enablers, not gates——依赖关系只为给 AI 提供上下文，不为把人锁住。

代价是纪律：既然没有强制门禁，靠的是 change owner 主动维护聚焦。

### 5. Archive 把变更折叠回真相

工作完成后 `openspec archive`，change 的 delta spec 合进主 specs，change 文件夹搬到 `changes/archive/<日期>-<change-name>/`。specs 现在描述新现实，准备接下一个 change。循环闭合。

## 任务流案例：从 `/opsx:explore` 到 `/opsx:archive`

下面把 OpenSpec 的完整工作流走一遍，用 README 里「加 dark mode」做蓝本。

```text
$ npm install -g @fission-ai/openspec@latest
$ cd your-project && openspec init

─── AI CHAT ─────────────────────────────────────────────────────
You: /opsx:explore
AI:  What would you like to explore?
You: I want dark mode but I'm not sure how to do it cleanly.
AI:  Reads your styling setup…
     Cleanest path: CSS variables + a small theme context,
     with system-preference detection. No new deps. Scope it?
You: Yes, let's do it.

You: /opsx:propose add-dark-mode
AI:  Created openspec/changes/add-dark-mode/
       ✓ proposal.md   — why we're doing this, what's changing
       ✓ specs/        — requirements and scenarios
       ✓ design.md     — technical approach
       ✓ tasks.md      — implementation checklist
     Ready for implementation!

     (你读 proposal、改 tasks.md、删两条 scope 越界)

You: /opsx:apply
AI:  Implementing tasks…
       ✓ 1.1 Add theme context provider
       ✓ 1.2 Create toggle component
       ✓ 2.1 Add CSS variables
       ✓ 2.2 Wire up localStorage
     All tasks complete!

You: /opsx:archive
AI:  Archived to openspec/changes/archive/2026-01-23-add-dark-mode/
     Specs updated. Ready for the next feature.
```

四步闭环：**想清楚 → 写下来 → 实现 → 归档**。每一步都可逆，每一步都留痕。

## CLI 与 Slash Command 的边界

新手最常踩的坑是把 `/opsx:propose` 输进终端。OpenSpec 文档专门为这一点写了一页（`docs/how-commands-work.md`），区分得很清楚：

| 类别 | 跑在哪 | 示例 |
|------|--------|------|
| CLI | 你的终端 | `openspec init`、`openspec list`、`openspec view` |
| Slash command | AI 助手对话框 | `/opsx:propose`、`/opsx:apply`、`/opsx:archive` |

`openspec init` 在终端跑一次，把 slash command **装进** AI 工具的对应目录（`.claude/skills/openspec-*/SKILL.md`、`.cursor/commands/opsx-<id>.md` 等等）。之后日常驱动主要在对话里完成。

也没有「interactive mode」要进——你只要在 AI 助手对话框里输入 `/opsx:propose`，AI 自动识别、加载 OpenSpec skill、按工作流走。

## 跨 25+ 工具适配：Skill vs Command

OpenSpec 支持 25+ AI 编码助手（Claude Code、Cursor、Windsurf、GitHub Copilot、Codex、Kiro、Kimi CLI、OpenCode、Pi、Qoder、Trae…）。**同一份工作流，不同的文件格式**。

`openspec init --tools <list>` 会按所选工具生成对应文件：

| 工具 | Skills 路径 | Commands 路径 |
|------|------------|--------------|
| Claude Code | `.claude/skills/openspec-*/SKILL.md` | `.claude/commands/opsx/<id>.md` |
| Cursor | `.cursor/skills/openspec-*/SKILL.md` | `.cursor/commands/opsx-<id>.md` |
| Windsurf | `.windsurf/skills/openspec-*/SKILL.md` | `.windsurf/workflows/opsx-<id>.md` |
| GitHub Copilot | `.github/skills/openspec-*/SKILL.md` | `.github/prompts/opsx-<id>.prompt.md` |
| Codex | `.codex/skills/openspec-*/SKILL.md` | `$CODEX_HOME/prompts/opsx-<id>.md`（全局） |
| Kimi CLI | `.kimi/skills/openspec-*/SKILL.md` | 不生成（用 skill-style `/skill:openspec-*`） |

Skills 是新派跨工具标准（一个文件夹的指令，AI 自动发现）；Commands 是老派按工具的 slash 文件。OpenSpec 同时支持两者，取决于工具偏好。

Slash command 的**语法也因工具而异**：

| 工具 | 调用形式 |
|------|----------|
| Claude Code | `/opsx:propose`（冒号） |
| Cursor | `/opsx-propose`（连字符） |
| Windsurf | `/opsx-propose` |
| GitHub Copilot | `/opsx-propose` |
| Kimi CLI | `/skill:openspec-propose` |
| Trae | `/openspec-propose` |

意图一致，标点不同。这是设计上的取舍——统一所有工具的语法不现实，不如把转换层藏在 `openspec init` 的文件生成里。

CI/脚本场景下用 `--tools claude,cursor` 或 `--tools all` 或 `--tools none` 跳过配置。

## 与同类工具的差异

OpenSpec 文档里直接对比了两个最常被提及的竞品：

**vs GitHub Spec Kit** — Thorough but heavyweight。Spec Kit 严肃但重：phase gates 死板、大量 Markdown、Python 起步。OpenSpec 更轻、允许自由迭代，没有强 phase 门禁。

**vs AWS Kiro** — Powerful but you're locked into their IDE and limited to Claude models。Kiro 把工作流锁在自研 IDE + 仅 Claude 模型里。OpenSpec 不绑工具也不绑模型（推荐高 reasoning 模型如 Codex 5.5 / Opus 4.7，但不强求）。

**vs 不用 spec** — AI 编码没有 spec 等于「模糊 prompt + 不可预测结果」。OpenSpec 在不增加仪式感的前提下引入可预测性。

## 采用顺序与适用边界

**适合的场景**

- 跨多 AI 工具团队工作，希望工作流统一。
- 维护已有 codebase（5 万行量级），不想重写全部文档。
- 经常需要在 6 个月后回头看「为什么当初这么改」。
- 团队里有人在用 Claude Code、有的人在用 Cursor，希望 PR review 的不是聊天历史而是 change folder。

**不太适合的场景**

- 一行 hotfix：为这种改动写 proposal + specs + design + tasks 仪式过重。
- 完全 greenfield 的玩具项目：还没沉淀「当下真相」时，spec 写出来没意义。
- 模型上下文窗口紧：OpenSpec 本身不会污染上下文，但完整走一遍 explore → propose → apply 会占不少 token。

**建议的采用顺序**

1. **第 1 周**：先在个人小项目跑一遍 `/opsx:explore → propose → apply → archive` 全流程，理解 delta spec 的写法和归档语义。
2. **第 2-3 周**：把 `openspec init` 加到一个已有的中型项目（不是最关键的），挑一两个真实 feature 试用 delta spec。注意观察 archive 后主 specs 是否真的能描述新系统。
3. **第 1 个月后**：把它引入团队工作流。配置 `--tools` 时根据团队实际工具组合挑，不要一上来就 `--tools all`。
4. **不要做的事**：不要把它当项目管理工具用（proposal 不要写得像 PRD），不要强求 100% change 都走完整四步（trivial fix 直接 commit 也行），不要绕开 archive 让 specs 漂移。

## 一些细节

- **Telemetry**：默认收集匿名使用统计（仅命令名和版本号），CI 环境自动禁用。`export OPENSPEC_TELEMETRY=0` 或 `export DO_NOT_TRACK=1` 关掉。
- **多语言支持**：通过 `openspec config profile` + `openspec update` 切换 profile（`core` 默认包含 explore/propose/apply/sync/archive；expanded 含 new/continue/ff/verify/bulk-archive/onboard）。
- **Dashboard**：`openspec view` 打开交互式 dashboard，浏览 specs 和 changes（不是用来执行 propose/apply 的）。
- **Stores（beta）**：可以把 specs 和 changes 放在独立仓库，跨团队共享。功能标记为 beta，文档在 `docs/stores-beta/user-guide.md`。

## 仓库地址

[https://github.com/Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec)

---

## 自测题

读完本文后，先自己想 30 秒再展开答案：

<details>
<summary>1. OpenSpec 和「给 AI 编码助手加一层 prompt 指令集」的本质区别是什么？</summary>

本质区别在定位：它不是又一层指令集，而是一个**轻量级 spec 协议层**——用 `specs/` 装真相、`changes/` 装提案、`delta specs` 装差异，再通过 CLI 与 `/opsx:*` slash command 双半架构送到 25+ AI 工具。它的价值不在 prompt 模板多漂亮，而在让「先同意再写代码」这件事变得**可跨工具、可回放、可归档**。指令集换工具就失效，协议层只写一次引擎、按工具适配方向盘。
</details>

<details>
<summary>2. `specs/` 与 `changes/` 是什么关系？`archive` 做了什么？</summary>

`specs/` 是系统**当下**的真相（how things work today），按 domain 组织；`changes/` 是正在被提议的变更（what we're proposing），一个 change 一个文件夹。归档（`openspec archive`）把 change 的 delta spec 合进主 `specs`，并把 change 文件夹搬到 `changes/archive/<日期>-<change-name>/`。归档后 `specs` 描述新现实，循环闭合，准备接下一个 change。
</details>

<details>
<summary>3. delta specs 为什么能用在 5 万行的存量系统上？</summary>

因为 delta 描述「变化」而非「全部」。在 change 内部你不用重写整个 spec，而是写一条小的 delta：这条 requirement 是 `ADDED`、那条 `MODIFIED`、另一条 `REMOVED`。你不必先把整个 5 万行系统文档化，才能开始下一项改动——只描述这次的差异即可。
</details>

<details>
<summary>4. CLI 与 slash command 的边界是什么？新手最常踩什么坑？</summary>

CLI（`openspec init` / `list` / `view`）跑在你的终端，是引擎；slash command（`/opsx:explore` / `propose` / `apply` / `archive`）跑在 AI 助手的对话框里，是方向盘。新手最常踩的坑是把 `/opsx:propose` 输进终端——slash command 只能在 AI 助手对话里触发，终端只认 `openspec` 开头的小写命令。
</details>

<details>
<summary>5. OpenSpec 与 GitHub Spec Kit、AWS Kiro 的核心差异各是什么？</summary>

vs **GitHub Spec Kit**：Spec Kit 严肃但重（phase gates 死板、大量 Markdown、Python 起步）；OpenSpec 更轻、允许自由迭代，没有强 phase 门禁（enablers, not gates）。vs **AWS Kiro**：Kiro 把工作流锁在自研 IDE + 仅 Claude 模型；OpenSpec 不绑工具也不绑模型。vs **不用 spec**：AI 编码没有 spec 等于「模糊 prompt + 不可预测结果」，OpenSpec 在不增加仪式感的前提下引入可预测性。
</details>

---

## 练习

### 练习 1：在个人小项目跑通完整四步（约 2 小时）

挑一个你自己的小项目，依次执行 `/opsx:explore → propose → apply → archive` 全流程。重点体会 delta spec 的写法（哪条 requirement 是 `ADDED` / `MODIFIED` / `REMOVED`）和 archive 后主 `specs` 是否真的能描述新系统。

完成后回答：archive 之后，`openspec/specs/` 下多出了什么？`changes/archive/` 下多了什么？

### 练习 2：给已有项目写一次 delta spec（约 1 小时）

在一个已存在的项目里跑 `openspec init`，挑一个真实 feature，创建 change 并只写 delta spec，不重写整个 spec。

参考要点：delta 只描述这次的变化；如果某个 requirement 完全没动，就不写进 delta。

### 练习 3：对比两套工具的文件生成（约 30 分钟）

运行 `openspec init --tools claude,cursor`，打开生成的目录，对比 Claude Code（`.claude/skills/openspec-*/SKILL.md` 与 `.claude/commands/opsx/<id>.md`）和 Cursor（`.cursor/skills/...` 与 `.cursor/commands/opsx-<id>.md`）两套路径的差异。

结论记录：Skills 路径和 Commands 路径分别给 AI 什么？为什么同一份工作流要生成两种格式？

### 练习 4：故意走一次「不完整的四步」（约 15 分钟）

对一个 trivial fix（比如改一行文案），直接 commit，不走 propose / apply / archive。

目的：理解 OpenSpec 的「enablers, not gates」——它不强制 100% 的 change 都走完整四步，trivial fix 直接提交也行，关键是不要绕开 archive 让 specs 漂移。

### 练习 5：关掉 telemetry 并理解其作用（约 10 分钟）

在 shell 里执行 `export OPENSPEC_TELEMETRY=0`（或 `export DO_NOT_TRACK=1`），确认 CI 环境下 telemetry 会自动禁用。

思考：默认收集了什么（仅命令名和版本号）？为什么这对开源项目是合理的，又为什么你会想关掉？

---

## 进阶路径

读完本文后，按以下顺序动手，而不是只按阅读顺序：

### 第一步：个人项目跑通全流程（约 2 小时）

在个人小项目完整走一遍 `/opsx:explore → propose → apply → archive`，重点搞懂 delta spec 的写法和归档语义。这一步不追求用得多，先建立「先对齐再写代码」的肌肉记忆。

**验证标准**：archive 后主 `specs` 能正确描述新系统，且 `changes/archive/` 下有对应记录。

### 第二步：中型项目试用 delta spec（约 1 周）

把 `openspec init` 加到一个已有的中型项目（不是最关键的），挑一两个真实 feature 试用 delta spec。注意观察 archive 后主 specs 是否真的能描述新系统，而不是和代码现实脱节。

**验收条件**：连续 3 个 feature 走完四步后，specs 与代码保持一致，没有靠手动记忆补状态。

### 第三步：引入团队 + 配置 `--tools`（约 1 个月）

把它引入团队工作流。配置 `--tools` 时根据团队实际工具组合挑（如 `claude,cursor`），不要一上来就 `--tools all`。让 PR review 的对象从聊天历史变成 change folder。

**交付物**：一份团队内部的 OpenSpec 采用规范（哪些改动必须走 propose，哪些可直接 commit）。

### 第四步（可选）：跨团队 Stores（beta，按需）

当多个团队需要共享 specs / changes 时，用 Stores（beta）把它们放在独立仓库。功能仍标记为 beta，文档在 `docs/stores-beta/user-guide.md`，引入前先评估成熟度。

**边界提醒**：不要把它当项目管理工具用（proposal 不要写得像 PRD），不要强求 100% change 都走完整四步，不要绕开 archive 让 specs 漂移。

---

## 常见问题

**Q1：每个改动都必须写 proposal + specs + design + tasks 吗？**

不必。OpenSpec 是 enablers, not gates——依赖关系只为给 AI 提供上下文，不为把人锁住。trivial fix 可以直接 commit；只有中大型、需要团队对齐的改动才值得走完整四步。仪式感过重恰恰会劝退团队。

**Q2：不用 spec 直接让 AI 写代码会怎样？**

等于「模糊 prompt + 不可预测结果」。没有 spec 时，AI 每次都可能用不同假设落地，六个月后没人（包括未来的你和下一个 AI 助手）说得清"当初为什么这么改"。specs 是给未来自己和 AI 的现成交接文档。

**Q3：OpenSpec 适配哪些工具？**

25+ AI 编码助手，包括 Claude Code、Cursor、Windsurf、GitHub Copilot、Codex、Kiro、Kimi CLI、OpenCode、Pi、Qoder、Trae 等。`openspec init --tools <list>` 按所选工具生成对应文件，同一份工作流靠「Skill vs Command」两套格式落地。

**Q4：CLI 和 slash command 能混用吗？**

不能混。CLI（`openspec init` 等）跑在终端，slash command（`/opsx:*`）跑在 AI 助手对话框。新手最常见错误是把 `/opsx:propose` 输进终端——slash command 只在对话框里被 AI 识别并加载 OpenSpec skill 后生效。

**Q5：怎么关掉 telemetry？**

默认收集匿名使用统计（仅命令名和版本号），CI 环境自动禁用。关掉用 `export OPENSPEC_TELEMETRY=0` 或 `export DO_NOT_TRACK=1`。

**Q6：archive 之后发现 specs 漂离了代码现实怎么办？**

根因通常是绕开了 archive——直接改代码却没同步 delta，导致 specs 落后于实现。修复方式：把这次差异补成一个 change 并 archive，让 specs 重新追上代码；长期做法是约束团队"改行为必过 change"，不让 specs 漂移。