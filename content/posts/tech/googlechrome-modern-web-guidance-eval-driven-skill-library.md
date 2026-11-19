---
title: "Modern Web Guidance：把「别再用老写法」做成有基线、有校准、有淘汰机制的 Web 技能库"
date: "2026-11-20T01:27:19+08:00"
slug: "googlechrome-modern-web-guidance-eval-driven-skill-library"
description: "Modern Web Guidance 是 Chrome、Edge、Firefox 与 MDN 团队共同维护的 Web 平台技能库，覆盖 262 个现代 Web 特性，用 Playwright grader 做闭环校准并自动淘汰模型已掌握的内容。本文拆解它的评测管线、uplift 指标口径、gd dev 五步流水线和 token 效率取舍。"
draft: false
categories: ["技术笔记"]
tags: ["Web 平台", "AI Agent", "评测体系", "Chrome", "性能优化"]
github_repo: "GoogleChrome/modern-web-guidance-src"
source_key: "gh:GoogleChrome/modern-web-guidance-src"
---

## 核心判断

编码 Agent 写前端有个系统性的偏差：它倾向于写**过时但安全**的代码。`document.querySelector` 加事件监听能解决的事，它不会去用 `<dialog>`；手写 focus trap 而不是用原生 `popover`；用 jQuery 时代的方式处理日期。而这些写法的代价不只是「不够优雅」——原生平台 API 往往自带浏览器优化和内置的无障碍语义。

GoogleChrome 的 modern-web-guidance 项目的判断是：光告诉模型「要用现代 API」不够，因为模型的问题不是不知道某个 API 存在，而是**不知道生产级的实现密度**——知道 `popover` 是什么，但不知道 popover 的顶层渲染语义怎么和 `::backdrop` 配合、什么时候该用 `popover="manual"` 而不是 `"auto"`。

所以这个项目的核心不是一份 API 清单，是一条**内容淘汰流水线**：哪些指南值得写、哪些写了也没用，由实测决定。

它最值得学的设计是三个指标的用法：

- **opportunity**（无引导通过率）：模型本来就能做对的程度。越高，说明这份指南越可能是冗余的。
- **uplift**（有引导 − 无引导）：指南的实际增量。
- **校准要求**：grader 必须在 golden patch 上 100% 通过、在未修改的基线应用上 100% 失败。

第三条常被忽略，但它决定了整套评测是否可信。**一个在原始代码上也能通过的 grader 什么也证明不了。**

截至 2026 年 11 月 20 日，这个仓库有 9048 stars、751 forks，TypeScript 为主，Apache-2.0 许可，2026 年 1 月创建，11 月 19 日仍有提交（包括当天移除 `focus-without-user-activation` 的安全指南）。

## 它解决的是哪一层问题

README 对问题的描述很准确：

> 编码 Agent 经常默认使用旧模式，因为 LLM 训练数据里塞满了旧代码。这经常导致它们为那些现在有原生、高性能 Web 平台方案的任务生成臃肿的 JavaScript。

即便模型知道某个 API 存在，它也缺少**真实世界现代实现模式所需的密度** —— 也就是那份「生产级代码长什么样」的语料。

这个项目填的正是这个缺口。三条主线：

- **现代浏览器 API**：帮模型正确组织它经常误用的 API
- **性能与无障碍**：优先用浏览器能优化、且自带无障碍能力的平台级 API
- **负责任的回退**：引导模型用轻量合理的回退，而不是重量级 polyfill 或遗留库

注意第三条。**它没有教人「永远用新 API」**，而是教「知道新 API 什么时候该退」——这是个成熟得多的立场。

## 内容规模与形态

覆盖的是过去几年 Web 平台的特性，一直延伸到最前沿。README 里有一张 262 个特性的清单，按学科分六大类：

| 学科 | 覆盖内容 |
|---|---|
| 用户体验 | View Transitions、进出场动画、视差滚动、CSS `scrollbar-color` |
| CSS 布局 | 容器查询、`subgrid`、`oklch` 等现代色彩空间、text-wrap 调节、line-height trimming |
| 性能 | 预加载、INP（Interaction to Next Paint）诊断、`scheduler.yield` 调度 |
| 表单与 UI | Anchor Positioning（tooltip）、Popover API、dialog、`:user-invalid` 校验、自适应尺寸字段 |
| 无障碍 | 屏幕阅读器与键盘可操作性、内容导航与可发现性 |
| 内置 AI | 本地客户端模型（原生翻译、摘要、语言检测 API） |

CSS 与布局一类就占了 140 个特性，包括 `::backdrop`、`content-visibility`、`progress()`、`::details-content`、`contrast-color()`、`reading-flow`、`::file-selector-button`、`::placeholder`、`currentColor`、相对颜色等等。

这里有个容易被忽略的设计目标：**指南是为 token 效率设计的**。README 说得很直白 —— 他们跑评测来**剪掉模型已经掌握的低常识内容**。这是与「把文档全塞进上下文」相反的思路。

## 评测闭环：整条流水线

这是这个项目区别于普通技能库的地方。README 用一张图概括：

```
  [ 专家撰写的指南与 demo ]
            │
            ▼
  [ 目标生成 ] ──> 真实 webapp 上的任务、golden solution、Playwright grader
            │
            ▼
  [ 校准循环 ] ───> 对 golden solution 跑 grader（必须 100% 通过）
            │      对未修改的基线应用跑 grader（必须 100% 失败）
            ▼
  [ E2E agent 评测 ] ──> 让编码 agent 在有引导 / 无引导两种模式下跑
                          比较通过率与无障碍表现
```

四个环节的具体设计：

**1. 模拟开发者任务。** 针对完整基线应用（`daily-grind`、`devtools-times`）定义真实的开发者提示，比如「让我的图片加载更快」。关键在于**提示不点名任何 API 或特性** —— 测试的是 agent 能不能自己发现并应用正确的指南，而不是会不会照着关键词检索。

**2. 静态与浏览器内检查。** Playwright grader 验证每条实现要求是否被遵守，检查源码头模式、计算样式、运行时 DOM 行为和无障碍状态。

**3. 自愈式校准。** grader 针对多 agent（Claude / Codex / AGY）产出的 golden solution 校准（目标 100% 通过），并针对未修改的基线应用校准（目标 0% 通过）。

**4. 端到端测试。** 在真实任务上测量 agent 有引导与无引导的表現。

### uplift 的口径

README 把两个指标讲得很精确：

> **opportunity**（100% − 无引导通过率）与 **uplift**（有引导 − 无引导通过率）是关键：如果模型在无引导时已经能成功，就剪掉冗余建议；在 agent 挣扎的地方，精修指南以最大化 uplift。

这个设计解决了「内容越多越好」的错觉。**模型本来就会的内容，写进上下文是纯成本。** opportunity 就是用来识别这种冗余的。

### 实测数据

README 里嵌了一张自动更新的评测结果表（INJECT_EVAL_RESULTS_START 标记之间）。11 月 8 日的快照：

| Agent + 模型 | 任务 / 检查数 | 无引导 → 有引导（uplift） |
|---|---|---|
| antigravity_cli (gemini-4-argon) | 214 / 1673 | 58% → 94%（**+36pp**） |
| codex_cli (gpt-6.1-sol) | 215 / 1795 | 54% → 82%（**+28pp**） |
| claude_code (opus-5-5) | 215 / 1801 | 57% → 88%（**+31pp**） |

往前几天的数据也稳定在同一区间（uplift 在 +27pp 到 +36pp 之间浮动）。**注意这个数字是相对基线的增量，不是绝对正确率** —— 换个模型、换个任务集，这个数字不可直接迁移。

## `gd dev`：五步流水线

`src/harness/` 目录是评测工具箱。`gd dev` 是完整的内容开发入口：

```bash
# 完整跑一遍：生成、校准、评测
gd dev guides/<category>/<use-case-slug>

# 只验证 grader 校准（golden patch 100% 通过、零通过率基线 0% 通过）
gd dev guides/<category>/<use-case-slug> --test-grader

# 校准后跳过评测与报告生成
gd dev guides/<category>/<use-case-slug> --no-test

# 只针对指定的基线应用（逗号分隔）
gd dev guides/<category>/<use-case-slug> --targets daily-grind
```

五个步骤：

1. **生成方案**：在基线应用上生成 golden solution patch 与零通过率基线 patch
2. **生成 grader**：依据 `expectations.md` 生成 `grader.ts` 里的 Playwright 检查
3. **校准 grader**：确保 golden patch 100% 通过、零通过率基线 100% 失败
4. **Agent 评测**：跑有引导与无引导两组 agent 试跑，测通过率与指南工具使用率
5. **生成报告**：调用一个 evaluator agent 分析失败的检查，输出改进建议到 `results/guides/<category>/<slug>/report.md`

`gd pr` 把结果变成 PR：自动建/切分支、提交并推送目标指南目录、打上 `gd-dev-content` 和/或 `gd-dev-eval` 标签、创建 PR（已有则更新描述和标签、移除 `needs-dev-rerun`）。它会拒绝推送那些已合并或已关闭 PR 的分支内容 —— 这种情况下要另起一个基于 `main` 的分支。

`gd dev-gap` 是补齐漏网之鱼的工具：扫描磁盘上的 `guides/`，找出那些有 `guide.md` 和 `expectations.md` 但缺评测（非 draft 状态）的指南，逐个跑 `gd dev` 和 `gd pr`。

## 失效检测：stale evals

`src/ci/sync-pipeline-issue.ts` 维护一个规范性的流水线 issue（#1815），其中一项机制是**标记「Stale evals」**：`expectations.md` 有实质性改动、但改动时间比 `grader.ts` 或 `targets/` 更晚时，就标记。

这条规则的价值在于：改了期望却没重新评测，是这类评测体系最常见的静默失效方式。人的直觉是「期望变了，grader 大概也还行」，但 grader 是在旧期望上校准的。

类似地，`gd dev` 的重跑粒度是**按文件类型分级的**：

| 改了什么 | 重新生成什么 |
|---|---|
| `guide.md` 的 `description` | 清空 `targets/<target>/`，全部重来 |
| `guide.md` 或 `expectations.md` 的其它改动 | 保留 `task.md`，重新生成 patch 和 `grader.ts` |
| 只改 `task.md` | 重新生成方案 patch 和 `grader.ts` |
| 只改 `grader.ts` | 只重跑校准和 agent 评测 |

## 工具面

CLI 的三个命令值得记住，因为它们把「知识检索」和「代码审计」分开了：

```shell
# 按语义检索指南
npx modern-web-guidance@latest search "animate a dialog modal backdrop"

# 按 ID 取具体指南
npx modern-web-guidance@latest retrieve "animate-to-from-top-layer"

# 扫描代码库里的遗留写法
npx modern-web-guidance@latest legacy-scan .
```

`search` 用的是自然语言描述（「给 dialog 动画化 modal 遮罩」）而不是关键词，这符合这个项目的整体思路：指南是按**任务**组织的，不是按 API 名字组织的。

安装路径覆盖了绝大多数主流 agent harness：交互式向导 `npx modern-web-guidance@latest install`，以及 Vercel Skills CLI（`npx skills add`）、GitHub CLI（`gh skill install`）、Google Antigravity（`agy plugin install`）、Claude Code 插件、Copilot CLI、Grok Build CLI、Kimi Code、Pi、OpenAI Codex。

## 采用顺序

1. **先不安装，试一次检索**：`npx modern-web-guidance@latest search "..."`。这能让你在不污染环境的前提下判断这批指南对你的技术栈是否适用。
2. **在你的代码库上跑 `legacy-scan .`**，看它标出的遗留写法有多少。如果你的项目本来就新，这可能说明你不需要这套东西。
3. **装上并绑定到你的 harness**（注意 Claude Code 的 marketplace 陷阱，见下）。
4. **先读 `guides/` 目录的组织方式**，理解指南按什么颗粒度切分。这决定了它在你的实际任务里能不能被检索到。
5. **如果你要给这个项目贡献指南**，先读 `.agents/skills/project-evals/SKILL.md` —— 那是规范性规范（normative specification），不是建议。

## 两个维护陷阱

**Claude Code 的 marketplace 分叉。** Anthropic 于 10 月 12 日停止在内置 `claude-plugins-official` marketplace 中更新第三方插件，导致通过该渠道安装的版本**停留在 `v0.0.194`**。切换方法：

```shell
/plugin uninstall modern-web-guidance@claude-plugins-official
/plugin marketplace add GoogleChrome/modern-web-guidance
/plugin install modern-web-guidance@googlechrome
/plugin  # 选 GoogleChrome marketplace，回车，开启 AutoUpdate
/reload-plugins
```

**注意这是 `modern-web-guidance` 仓库**，不是 `-src`。前者是发布出去给用户装的技能包，后者是源仓库 —— 两者都要盯。

## 边界

- **它只覆盖 Web 平台**。不是通用前端规范，不覆盖 React 模式、状态管理、测试策略。
- **它是建议库，不是 linter**。它把内容送进 agent 的上下文，最终用不用是 agent 决定的；`legacy-scan` 是发现问题的工具，不是强制门禁。
- **评测数据绑定特定模型与任务集**。+36pp 的 uplift 是 antigravity + gemini-4-argon + `daily-grind`/`devtools-times` 这组条件下的结果。换模型要重测。
- **它由浏览器厂商团队维护**。这不构成内容不可信 —— Chrome、Edge、Firefox、MDN 团队共同参与，还有 web 开发者社区 —— 但阅读时知道它的立场有助于判断优先级。

## 参考

- 发布仓库（给用户装）：<https://github.com/GoogleChrome/modern-web-guidance>
- 源仓库：<https://github.com/GoogleChrome/modern-web-guidance-src>
- 官方文档：<https://developer.chrome.com/docs/modern-web-guidance>
- 评测看板：<https://googlechrome.github.io/modern-web-guidance-src/>
- 治理与贡献：仓库内 `GOVERNANCE.md` 与 `CONTRIBUTING.md`
