---
title: "GSD Core：用五步循环和文件化状态，治住 AI 编程的 context rot"
date: "2026-05-23T03:15:00+08:00"
lastmod: "2026-09-30T20:00:00+08:00"
slug: "get-shit-done-redux-productivity-framework"
github_repo: "open-gsd/gsd-core"
source_key: "gh:open-gsd/gsd-core"
description: "GSD Core（原 get-shit-done-redux）是 open-gsd 维护的 AI 编程工作流框架。它把重活分给干净上下文的子 agent，用 .planning 目录跨会话保存项目状态，以 discuss → plan → execute → verify → ship 循环逐个推进 phase，并对每轮结果做人工验收。本文覆盖核心机制、上手路径、配置要点与 2026 年这次社区接管的背景。"
draft: false
categories: ["技术笔记"]
tags: ["AI 编程", "Claude Code", "工作流", "上下文工程", "Spec-Driven Development"]
---

# GSD Core：用五步循环和文件化状态，治住 AI 编程的 context rot

## 先给判断

GSD Core（前身 get-shit-done-redux，下文简称 GSD）解决的不是"怎么让 AI 写出第一版代码"，而是"怎么让 AI 在多轮开发里持续交付可验收的结果"。

它最强的地方，不是"比别的 AI 更会写代码"，而是把 AI 编程里最容易失控的三件事收紧了：上下文漂移、需求走样、验收缺席。做法也很明确：**把任务拆成 phase，把 phase 拆成 plan，把真正的执行扔进干净上下文的子 agent，再用文件化状态和人工验收把结果兜住。**

所以，与其说 GSD 是一个工具，不如说它是一套让 AI 编程可预测、可回放、可重启的工作流协议。它尤其适合独立开发者和 2 到 5 人的小团队，也适合那些已经被"AI 前面很能写，后面越来越飘"折腾过的人。

如果你只想用一句话理解它：**GSD 不是帮你把 prompt 写得更花，而是给 AI 编程加了一套外部记忆、分工执行和验收门。**

> 参考入口：[open-gsd/gsd-core](https://github.com/open-gsd/gsd-core) · [README](https://github.com/open-gsd/gsd-core/blob/next/README.md) · [User Guide](https://github.com/open-gsd/gsd-core/blob/next/docs/USER-GUIDE.md) · [Architecture](https://github.com/open-gsd/gsd-core/blob/next/docs/ARCHITECTURE.md)

## 读完你应该能回答三件事

- GSD 解决的核心问题到底是不是 `context rot`
- discuss、plan、execute、verify、ship 这五步各自锁定了什么风险
- 第一次上手时，应该从安装、建项目、首个 phase 还是现有代码库接入开始

## 系统地图

表面上看，GSD 是一堆 slash 命令——到 v1.15.0 已经有 65 个；真正起作用的是 3 层结构：命令层、工作流层、状态层。

### 第一层：你看到的是命令

核心循环只有六条（官方称之为 five-step loop，加上项目初始化这一步）：

| 指令 | 环节 | 作用 |
| ---- | ---- | ---- |
| `/gsd-new-project` 或 `/gsd-onboard` | 初始化 | 提问、研究、抽需求、生成路线图；现有仓库走 onboard |
| `/gsd-discuss-phase N` | 讨论 | 把"你心里怎么想的"写成实现约束 |
| `/gsd-plan-phase N` | 规划 | 研究、拆任务、做计划校验 |
| `/gsd-execute-phase N` | 执行 | 按波次并行执行 plan，每个任务原子提交 |
| `/gsd-verify-work N` | 验证 | 逐项做人工验收（官方叫 Manual UAT），不通过就生成修复计划回到执行 |
| `/gsd-ship N` | 交付 | 从已验证的 phase 创建 PR，归档并进入下一个 phase |

围绕这六条，还有 UI 扩展（`/gsd-ui-phase`、`/gsd-ui-review`）、里程碑收尾（`/gsd-audit-milestone`、`/gsd-complete-milestone`）、导航与恢复（`/gsd-next`、`/gsd-pause-work`、`/gsd-resume-work`）和一批工具命令（`/gsd-quick`、`/gsd-debug`、`/gsd-undo` 等），完整清单见 [COMMANDS.md](https://github.com/open-gsd/gsd-core/blob/next/docs/COMMANDS.md)。

### 第二层：后台跑的是工作流

GSD 的工作流不是"一条大 prompt 从头写到尾"，而是由一组薄编排器驱动不同 agent：

- research agent 负责找资料、查依赖、补风险
- planner 负责把目标拆成可执行的 plan
- plan-checker 负责拦住不够小、不够清晰、不可验证的计划（校验循环最多 3 轮）
- executor 负责在干净上下文里实现每个 plan——官方口径是每个 executor 从干净的 200k token 上下文起步
- verifier 和 debug agent 负责把"能跑"继续压成"符合目标"

这一层的关键不是 agent 多，而是**每类 agent 都拿到刚好够用的上下文**。这也是它和纯聊天式 AI 编程最大的差别。

### 第三层：真正稳定系统的是文件化状态

执行层面，GSD 在项目的 `.planning/` 目录下持续维护一组结构化文档，贯穿 session 边界：

- `PROJECT.md`：项目愿景
- `REQUIREMENTS.md`：需求范围，带 v1/v2 编号
- `ROADMAP.md`：阶段路线图与状态追踪
- `STATE.md`：当前位置、决策与阻塞记录
- `phases/XX/`：每个 phase 自己的目录，装着 plan、执行摘要、研究材料和验证结果；你这个 phase 的实现偏好写在里面的 `CONTEXT.md`

这些文件不是"顺手生成的文档"，而是系统的外部记忆。你关掉窗口、`/clear`、隔天再回来，GSD 不是靠聊天记录回忆项目，而是靠这些 planning 文件重新定位项目状态。

## 目录

1. [先给判断](#先给判断)
2. [读完你应该能回答三件事](#读完你应该能回答三件事)
3. [系统地图](#系统地图)
4. [六条命令不是重点，三条约束才是重点](#六条命令不是重点三条约束才是重点)
5. [一个 phase 是怎么流过去的](#一个-phase-是怎么流过去的)
6. [为什么这个思路有效](#为什么这个思路有效)
7. [安装与初始化](#安装与初始化)
8. [第一次上手，建议这样走](#第一次上手建议这样走)
9. [谁适合用 GSD](#谁适合用-gsd)
10. [2026 年这次社区接管，值得单独看一眼](#2026-年这次社区接管值得单独看一眼)
11. [常见误解和踩坑](#常见误解和踩坑)
12. [自测：检验你的理解](#自测检验你的理解)
13. [如果你只读三份文档](#如果你只读三份文档)
14. [最后判断](#最后判断)

## 六条命令不是重点，三条约束才是重点

很多人第一次看到 GSD，会把注意力放在命令数量上——光 COMMANDS.md 里收录的 slash 命令就有 65 个。其实核心循环那六条本身并不新鲜，真正有价值的是它把 AI 编程压进了 3 条约束。

### 1. 重活放到干净上下文里

GSD 的执行阶段会把 plan 分发给独立 executor。每个 executor 都从一个干净的上下文起步，不继承主会话里那些已经变得臃肿的聊天历史。主上下文只负责协调、确认和验收，不再背着所有细节一路前进。

这件事看起来像"优化 prompt"，本质上更接近**任务调度**。你不是在一条越来越长的对话里逼 AI 同时记住需求、分支、异常、临时决定和测试结果，而是在不断给不同 agent 发一份足够小、足够明确的工单。

### 2. 决策先落文件，再进入执行

`/gsd-discuss-phase` 的价值在这里很容易被低估。很多 AI 编程翻车，不是模型不会写，而是"你脑子里有约束，但你没把它说实"。比如：

- 错误处理要不要暴露原始报错
- 这个 phase 是先追求性能，还是先把接口稳定下来
- 允许引入新依赖，还是优先用标准库
- UI 上哪些地方是品味问题，哪些地方是硬约束

这些决定如果不提前落进 `CONTEXT.md`，后面的 planner 和 executor 只能猜。GSD 做的事很朴素：先把灰区变成白纸黑字，再让 AI 按这个边界去写。

### 3. 验证不是"顺手跑一下测试"，而是单独一个 gate

不少 AI 编程流程最大的问题，是把"实现"当成"完成"。GSD 则把 verify 单独拎出来。它要求你按可观察结果去做人工验收，任何不通过的项都会被整理成新的修复计划，再回到执行阶段。

这一步非常关键，因为它在纠正一个常见错觉：**代码生成是自动化的，但"是否符合预期"仍然需要人为判断。**

## 一个 phase 是怎么流过去的

官方教程 [Your first project](https://github.com/open-gsd/gsd-core/blob/next/docs/tutorials/your-first-project.md) 用的例子是一个 Node.js 命令行 to-do 应用：`todo add`、`todo list`、`todo done` 三个子命令，数据存本地 `todos.json`，只用 Node 标准库。例子很小，但正好能看清 GSD 的任务流。

### 第一步：先建项目，不先写代码

```bash
/gsd-new-project
```

GSD 会先问你要做什么、给谁用、边界在哪，然后并行跑研究，最后产出 `PROJECT.md`、`REQUIREMENTS.md` 和 `ROADMAP.md`。这一步的产物不是代码，而是项目合同。

### 第二步：清掉上下文，再把"实现偏好"锁死

```bash
/clear
/gsd-discuss-phase 1
```

教程在这里特意先跑 `/clear`：建项目阶段的上下文已经用完了，讨论应该在干净上下文里进行。discuss 要做的是把路线图没有说清的选择写成文字。拿 to-do 应用来说，值得提前锁死的问题类似这样：

- 数据存 `todos.json` 还是上 SQLite
- 命令输出用纯文本还是带颜色
- 非法输入是报错退出还是给友好提示
- `todo done` 遇到不存在的编号怎么处理

这些决定如果不提前落进 `CONTEXT.md`，后面的 planner 和 executor 只能猜。GSD 做的事很朴素：先把灰区变成白纸黑字，再让 AI 按这个边界去写。

### 第三步：plan 不是列 TODO，而是生成可执行任务单

```bash
/gsd-plan-phase 1
```

GSD 会先跑并行研究，再把任务拆成多个 plan 文件，落在 `.planning/phases/01-xxx/` 下。每个 plan 都会明确到：

- 涉及哪些文件
- 要完成什么动作
- 怎样验证
- 达成什么条件才算 done

如果 plan 太大、太模糊、无法验证，plan-checker 会把它打回去，整个校验循环最多跑 3 轮。这一点很重要，因为它决定了后面的 executor 是在做"实现"，还是在继续帮你想需求。

### 第四步：execute 才是真正的并行入口

```bash
/gsd-execute-phase 1
```

这一步里，多个 plan 会按依赖关系被分成不同波次。互不阻塞的任务并行执行；存在依赖的任务顺序推进。每个任务在独立子 agent 里完成，并生成原子提交。这样做有两个直接好处：

- 主上下文不会被实现细节塞满
- Git 历史更清楚，回滚和审查更容易

### 第五步：verify 把"看起来没问题"变成"真的过线"

```bash
/gsd-verify-work 1
```

verify 在官方文档里叫 Manual UAT。它逐项问你实际行为，比如：

- `todo add` 能不能正常写入 `todos.json`
- `todo list` 是不是只展示未完成项
- `todo done 1` 之后条目是否被正确标记

如果你回答"第三项没有通过，编号标记了但列表还在显示它"，GSD 会把这个失败整理成修复计划，再回到 execute。也就是说，**verify 不是结尾的勾选框，而是下一轮执行的输入口。**

### 第六步：ship 是把 phase 交付出去，而不是宣布大功告成

```bash
/gsd-ship 1
```

当某个 phase 通过验证后，你再创建 PR（加 `--draft` 可以先建草稿 PR）、归档这个 phase、进入下一个。这样，交付动作发生在"已验证结果"之后，而不是发生在"模型说写完了"之后。

## 为什么这个思路有效

大多数 AI 编程工具的问题，不是"模型太弱"，而是"上下文越长，约束越容易丢"。这件事通常会体现在 4 个层面。

### 第一，长会话会稀释优先级

当一个 session 里混入探索、临时修补、日志、解释、跑偏讨论和情绪化反馈以后，模型很难继续稳定地区分"真正重要的约束"和"刚刚发生但不重要的噪音"。这就是大家常说的 `context rot`。

GSD 的解法是把执行搬去 fresh context，把主会话降级为协调器。这样主会话不再承担"记住一切"的责任。

### 第二，文件化状态比聊天记录更可靠

聊天记录擅长对话，不擅长做长期项目状态。`PROJECT.md`、`REQUIREMENTS.md`、`ROADMAP.md`、`STATE.md` 这些文件看起来很"老派"，但正因为它们是显式文件，才适合在上下文重启、多人协作、PR 审查里反复引用。

### 第三，计划校验把大量返工拦在执行前

如果没有 plan-checker，executor 经常会遇到一种很尴尬的任务：目标看似明确，实际上缺边界、缺验证条件、缺依赖前提。GSD 把这类问题尽量前置到 planning 阶段解决，减少"执行到一半才发现任务定义不完整"的返工。

### 第四，人工验收重新回到了流程中央

GSD 从来没有假装"有了自动化测试就不需要人判断"。它的 verify 设计承认一件现实：产品行为、交互是否顺手、异常是否符合预期，很多时候仍然需要人来做最终裁决。

## 安装与初始化

标准安装只有一条命令：

```bash
npx @opengsd/gsd-core@latest
```

安装器会提示选择运行时和安装方式（全局或本地）。以 Claude Code 为例，全局安装可以一步到位：

```bash
npx @opengsd/gsd-core@latest --claude --global
```

skills 会落进 `~/.claude/`，重启会话后命令以 `/gsd-*` 形式出现。当前安装器覆盖 16 种运行时，README 点名的包括 Claude Code、OpenCode、Codex、Copilot、Cursor、Windsurf、Antigravity、Kimi CLI、Kilo 等，完整清单见 [Install on your runtime](https://github.com/open-gsd/gsd-core/blob/next/docs/how-to/install-on-your-runtime.md)。

如果你在现有仓库试用，不要一上来就跑 `/gsd-new-project`，先跑二选一：

```bash
/gsd-map-codebase   # 快速摸底现有代码库，可加 --fast
/gsd-onboard        # 完整接入，产出 .planning/onboarding/SUMMARY.md
```

它会先分析现有项目的技术栈、结构和约定，再让后续的问题更贴近真实代码库。

GSD 的配置文件位于 `.planning/config.json`，可以通过 `/gsd-settings` 或 `/gsd-config` 交互式更新，也可以手动编辑。几个常用配置项如下：

| 配置项 | 默认值 | 说明 |
| ---- | ---- | ---- |
| `mode` | `interactive` | `interactive` 需你确认每步，`yolo` 自动放行 |
| `model_profile` | `balanced` | 模型档位，可选 `quality` / `balanced` / `budget` / `adaptive` / `inherit` |
| `parallelization.enabled` | `true` | 开启独立 plan 的并行执行 |
| `code_quality.fallow.enabled` | `false` | 开启 `/gsd-code-review` 前的结构预检 |
| `workflow.research` / `plan_check` / `verifier` | `true` | 分别控制研究、计划校验、验证 agent 是否参与流程 |

成本敏感的时候，`/gsd-config --profile budget` 一条命令切到省钱档。

在 Claude Code 里，官方文档的示例直接配合下面这个启动参数跑：

```bash
claude --dangerously-skip-permissions
```

这是因为 GSD 本来就面向自动化执行，很多动作默认假定 agent 有足够权限推进工作流。

还有一个容易踩的坑：**不要手动把仓库里的 `agents/` 或 `commands/` 文件直接复制进别的运行时目录。**官方安装器会按运行时写入不同位置、转换命令形态——比如 Antigravity 的 skills 装在 `~/.gemini/config/skills/`，而不是 Claude Code 的 `~/.claude/`。这一点在 [README](https://github.com/open-gsd/gsd-core/blob/next/README.md) 和 [安装文档](https://github.com/open-gsd/gsd-core/blob/next/docs/how-to/install-on-your-runtime.md)里都写得很明确。绕过安装器，往往会直接撞上命令不被识别或格式不对的问题。

## 第一次上手，建议这样走

如果你今天第一次试 GSD，更建议走下面这条路径，而不是一上来就背整套命令。

1. 安装 `@opengsd/gsd-core`
2. 如果在现有仓库试用，先跑 `/gsd-map-codebase` 或 `/gsd-onboard`
3. 执行 `/gsd-new-project`，确认路线图是否说的是同一个项目
4. 只挑一个小 phase，`/clear` 后运行 `/gsd-discuss-phase 1`
5. 紧接着跑 `/gsd-plan-phase 1`，看输出的 plan 是否够小、够清楚
6. 用 `/gsd-execute-phase 1` 完成第一轮实现
7. 用 `/gsd-verify-work 1` 做一次真正的人工验收
8. 通过后跑 `/gsd-ship 1`，把交付动作做完

这样做的好处是，你能在第一个 phase 里直接理解 GSD 的节奏，而不是靠读文档想象它会怎么工作。

## 谁适合用 GSD

GSD 面向的是**已经在用 AI 编程工具，但不满足于"让它自己跑一跑"这种不稳定结果**的开发者。

它特别适合：

- solo developer，想把"灵感驱动开发"收束成可持续节奏
- 小团队，希望保留速度，但不想让 AI 把项目写散
- 已经习惯 Claude Code、Cursor、Codex 这类工具，但受够了长会话后质量下滑的人

它不太适合：

- 只写一次性脚本、临时实验、十分钟能完成的小修小补
- 已经有成熟企业研发流程，而且强依赖 Jira、Sprint ceremony、多角色审批的大组织
- 完全不想做人工验收，只想"让 AI 自己决定对不对"的使用方式

说得更直白一点：GSD 不是为了把 AI 编程变成"零管理"，而是为了把管理工作尽量沉到系统里，让你的注意力回到决策和验收上。

## 2026 年这次社区接管，值得单独看一眼

现在活跃维护的仓库是 `open-gsd/gsd-core`，npm 主包名是 `@opengsd/gsd-core`（v1.15.0，2026-09-26 发布）。这不是简单的改名，而是一次公开的项目延续。

项目最初发布在 `gsd-build/get-shit-done`。根据维护者在 [continuity announcement](https://github.com/open-gsd/gsd-core/discussions/109) 里的公开说明，open-gsd 是在原上游出现信任与所有权问题之后，以 community-maintained continuation 的方式接手维护的。旧 npm 包不再获得更新，Issue 和 PR 编号已重新编排，每一条都链回原仓库的对应项。仓库还公开了 [Security Audit Transparency Report](https://github.com/open-gsd/gsd-core/discussions/119)（2026-05-22），方便你自己核对安全说明。

接管至今四个多月，这个仓库涨到 10,028 stars、717 forks（2026-09-30 读数），运行时适配从最初的几种扩到 16 种，版本推进到 v1.15.0。社区接管的成色，可以用这些数字直接检验。

对普通用户来说，这段背景最重要的现实含义只有两条：

- **安装和升级时，认准 `@opengsd/gsd-core` 这个包名**
- **如果你以前装的是 `@opengsd/get-shit-done-redux` 或更早的包，尽快迁移，不要混用新旧命名**

这类信息放进文章里，不是为了放大戏剧性，而是因为它直接影响安装命令、升级路径和信任边界。

## 常见误解和踩坑

### 误解一：装完以后就可以"完全放手"

GSD 会自动研究、自动拆任务、自动执行，但它并没有取消人的职责。你仍然需要拍板路线图、锁定 discuss 决策、做 verify 验收。它自动化的是流程推进，不是责任归属。

### 误解二：跳过 discuss 也没关系

可以跳，但你要知道你在放弃什么。跳过 discuss，planner 和 executor 会尽量给出"合理默认"，可很多项目最怕的正是这些"看起来合理"的默认值。你的产品判断、接口偏好、错误处理风格，往往就是在 discuss 里固化下来的。

### 误解三：verify 就是跑测试

不是。自动化测试很重要，但 verify 的重点是验收"实际行为是否符合目标"。很多问题恰恰发生在测试通过但交互不对、异常路径不对、输出格式不对的时候。

### 误解四：直接复制命令文件就等于安装

官方文档明确不建议这么做。GSD 安装器会为不同运行时写入不同目录、转换命令形态，手动复制文件通常只会让你在非 Claude Code 运行时里踩命令不被识别或格式不对的问题。

## 自测：检验你的理解

以下问题用于检验你是否真正理解了 GSD 的工作方式，而不只是记住了命令名。尝试回答后再看提示。

**问题 1：GSD 解决的核心问题是什么？**

用一句话描述，并解释为什么"给 AI 写更长的 prompt"不是这个问题的正确答案。

> **提示**：想一下为什么 AI 编程在第三轮、第五轮之后质量会下滑。

**问题 2：`/gsd-discuss-phase` 这一步经常被跳过，跳过会失去什么？**

举两个"跳过 discuss 后 planner 只能给合理默认，但这个默认恰好不对"的具体例子。

> **提示**：想一下你的项目里有哪些"看起来合理但对你这个业务不对"的默认选择。

**问题 3：为什么 executor 要用独立子 agent，而不是在主会话里直接实现 plan？**

如果不这样做，会有哪两个具体问题？

> **提示**：一个是上下文长度的问题，一个是"前面讨论过的约束在第十轮对话里还有没有"的问题。

**问题 4：verify 和"跑一下测试"的本质区别是什么？**

举一个"测试全绿但 verify 不通过"的场景。

> **提示**：测试验证代码行为是否符合预期，verify 验证的是产品行为是否符合目标。这两个不完全一样。

**问题 5：GSD 的六个核心命令里，哪两个是"门"，卡着后续流程能不能继续？**

> **提示**：一个是"决策有没有落文件"，一个是"实现结果有没有通过人工验收"。

---

能清晰回答这五个问题，说明你理解了 GSD 的设计逻辑，而不只是它的命令列表。

## 如果你只读三份文档

GSD 的文档到 v1.15 已经铺得很大（tutorials / how-to / reference / explanation 四类），第一次上手盯住下面 3 份就够了：

1. **[README](https://github.com/open-gsd/gsd-core/blob/next/README.md)**：先确认项目定位、安装命令、支持的运行时和当前维护链
2. **[Your first project](https://github.com/open-gsd/gsd-core/blob/next/docs/tutorials/your-first-project.md)**：把第一轮完整工作流从头到尾走一遍
3. **[User Guide](https://github.com/open-gsd/gsd-core/blob/next/docs/USER-GUIDE.md)**：生命周期全景、安全注意事项和配置参考

等你已经能接受它的主张，再去看 [Architecture](https://github.com/open-gsd/gsd-core/blob/next/docs/ARCHITECTURE.md)（为什么这样设计）、[Context engineering](https://github.com/open-gsd/gsd-core/blob/next/docs/explanation/context-engineering.md)（设计理念的完整推理），以及 [COMMANDS.md](https://github.com/open-gsd/gsd-core/blob/next/docs/COMMANDS.md) 和 [CONFIGURATION.md](https://github.com/open-gsd/gsd-core/blob/next/docs/CONFIGURATION.md) 就行。先把主循环跑通，比先把所有开关背下来更重要。

## 最后判断

GSD 值得关注，不是因为它承诺"AI 会替你把项目全做完"，而是因为它把一个更现实的命题做得比较完整：**怎样让 AI 在长周期开发里持续输出稳定结果。**

它抓住的核心矛盾也确实成立。AI 编程最难的部分，从来不是第一段代码，而是第二轮、第五轮、第十轮之后还能不能守住边界。GSD 给出的回答不是更长的 prompt，而是 fresh context、文件化状态、计划校验和人工验收。

还有一个信号值得注意：接管四个多月，它的命令涨到 65 个、运行时适配扩到 16 种，但核心循环还是 `discuss → plan → execute → verify → ship` 那六条，一条没动。外围在快速生长，主干保持稳定——这对一个工作流框架来说是好状态。如果你已经在 AI 编程里撞过 `context rot`、需求漂移、验收缺席这些墙，这套框架值得你认真试一轮。最好的试法不是读完所有文档，而是找一个真实的小 phase，从 `/gsd-new-project` 或 `/gsd-onboard` 开始，完整走一遍 `discuss → plan → execute → verify → ship`。
