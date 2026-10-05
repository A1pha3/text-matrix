---
title: "Compound Engineering：51 个 Agent 退役之后，一套工作流协议收敛成 36 个 Skill"
date: "2026-05-30T13:13:57+08:00"
lastmod: "2026-10-04T00:00:00+08:00"
slug: "compound-engineering-plugin-agent-workflow-system"
github_repo: "EveryInc/compound-engineering-plugin"
source_key: "gh:EveryInc/compound-engineering-plugin"
description: "Every 的 Compound Engineering 插件四个月从 v3.9 走到 v3.30：51 个自定义 Agent 整体退役、核心环路从 5 步变 6 步、安装进入原生插件时代。本文以 2026-05-30 发文时点和 10-04 核查读数双时点拆解它的复利机制。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Claude Code", "Cursor", "Codex", "工作流"]
---

Compound Engineering 是 Every 团队开源的一套 AI 编程工作流插件，核心主张一句话：**每一次工程工作都应该让下一次变得更容易，而不是更难。** 它把工作量倒过来分——80% 花在规划和评审，20% 花在执行——然后让每一轮留下的需求文档、计划和踩坑笔记，成为下一轮的输入。

这个项目值得单独写一篇的原因，不只是它的方法论。它从 2026-05-30 本文发稿到 10-04 复核的四个月里，把自己重构了一遍：发文时官方宣称 37 个 Skill 配 51 个自定义 Agent；现在首页 badge 写的是 36 个 Skill，51 个 Agent 的独立形态整体退役，评审和研究行为内化成 Skill 内部的提示词资产。核心环路从 5 步变 6 步，安装从 Bun 转换器时代进入原生插件时代，版本从 v3.9.3 走到 v3.30.3。一个教别人「把经验固化成可复用资产」的项目，用四个月演示了自己怎么做这件事。

| 字段 | 发文时点（2026-05-28 commit 85987d49） | 复核读数（2026-10-04） |
|------|------|------|
| Stars / Forks | 22,071 / 1,628 | 25,388 / 2,070 |
| 版本 | v3.9.3 | v3.30.3 |
| Skill 数 | 官方宣称 37（目录实测 38） | 36（badge 与 `skills/` 目录一致） |
| 自定义 Agent | 官方宣称 51（目录实测 43），独立 `.md` 文件 | 无独立 Agent，行为内化进 Skill |
| 核心环路 | 5 步 | 6 步（新增 simplify） |
| 支持平台 | 10 个 | 官方口径 14 个 agent hosts |

## 核心环路：六步

现行版本的环路是六步：**brainstorm 想清楚需求，plan 排出实现路径，work 按计划执行，simplify 收拾刚写的代码，review 评审结果，compound 把学到的写下来**——然后带着更好的上下文进入下一轮。

| 步骤 | Skill | 做什么 | 跳过会丢什么 |
|------|-------|--------|------------|
| 1. 需求梳理 | `/ce-brainstorm` | 交互式问答，把模糊想法写成需求文档 | 方向和边界没对齐就开始写代码，返工成本高 |
| 2. 实现计划 | `/ce-plan` | 把需求文档充实为可执行的实现计划 | 代码改了一半才发现方案有问题，上下文已经耗尽 |
| 3. 执行 | `/ce-work` | 在隔离的 worktree 里按计划逐条执行，任务追踪保证不遗漏 | 多任务交叉污染，未完成的代码混进提交 |
| 4. 简化 | `/ce-simplify-code` | 评审前先收拾刚写的代码：清重复、提复用 | 能跑但难改的代码进了主干，下一轮所有人一起还债 |
| 5. 评审 | `/ce-code-review` | 多视角 Agent 评审，抓模式而不只是语法错误 | bug 进了主干，下次排查要重新理解一遍上下文 |
| 6. 知识固化 | `/ce-compound` | 把这次的经验写进 `docs/solutions/` | 换个人（或同一个 Agent 的下次会话），从零再踩一遍坑 |

第 4 步是发稿之后才进环的。`ce-simplify-code` 在发稿时点的仓库里已经存在，但官方文档的环路叙事里没有它；四个月后被官方提升为六步之一，插在执行和评审之间。这个变化本身能说明团队的取向：写完能跑不算完，写得干净才进评审。

`/ce-debug` 是独立入口，处理「从 bug 出发而不是从功能出发」的场景——系统性复现失败、追踪根因、实施修复，完成后一样接评审和固化。`/ce-ideate` 在环路之前，适合「连做什么都没想清楚」的阶段：生成一批想法、批判性评估、排序，把最强的那个送进 brainstorm。已有明确需求时直接从 brainstorm 开始。

## 知识固化是怎么闭合的

这套系统真正的杠杆不在六步本身，而在「写下来的东西下次真的会被读到」。三个机制撑住这个回路：

**STRATEGY.md 是上游锚点。** `/ce-strategy` 把产品的目标问题、方案、目标用户、关键指标写成仓库根目录的一个短文件。ideate、brainstorm、plan 在执行前都会读它——策略选择由此流进每一次功能构思，而不是散落在会议记录里。Compound Engineering 仓库自己的 `STRATEGY.md` 就躺在根目录，他们用自己的方法管理自己的开发。

**docs/solutions/ 是下游沉淀。** `/ce-compound` 把验证过的解法写成结构化文档：症状、根因、试过什么没用、最终怎么解决的、怎么预防。关键在后手——`ce-plan` 和 `ce-ideate` 会把这个目录当作机构记忆来读，同一个坑不用调查第二次。默认产物目录（`docs/solutions/`、`docs/plans/`）可以通过 `docs_root` 配置整体搬到别的位置，`docs/` 本身被内容占用的仓库不用让路。

**Compound Packs 把规则跨仓库复用（实验性）。** 一个仓库学到的团队规范、安全策略、技术栈铁律，可以声明成规则包，规划阶段作为 grounding 读入，评审阶段强制执行，每次引用都注明出处规则文件。单仓库的复利由此扩展到整个组织。

读数侧还有 `/ce-product-pulse`：按时间窗（24 小时、7 天）生成一页使用、性能、错误报告，存入 `docs/pulse-reports/`，让策略更新和下一轮 brainstorm 有真实用户信号可锚定。

## 一条典型循环

从「有个模糊想法」到「经验被固化」，日常开发最常走的是这条路径：

```text
/ce-brainstorm make background job retries safer
/ce-plan
/ce-work
/ce-simplify-code
/ce-code-review
/ce-compound
```

brainstorm 进入交互式问答——问清楚「安全」的定义、当前重试策略在哪、哪些场景会出问题、有没有幂等性保证——最后落一份需求文档。plan 读这份文档，输出按文件粒度的实现计划；计划是 markdown 文件，可以先 review 再执行。work 在隔离的 worktree 里逐条执行，simplify 收拾代码，review 出报告，compound 把「后台任务重试的安全边界取决于幂等性保证和死信队列超时配置」这类结论写进 `docs/solutions/`。

重点是这步完了回到开头：下一轮 brainstorm 会读到这次 compound 的笔记和 `STRATEGY.md` 里的最新指标，起点比上一轮高。官方 README 放的演示 GIF 说明了这件事：一次 `ce-compound` 记下一个环境变量的坑，18 天后一次毫不相干的 `ce-plan` 把这个约束带进了新计划。他们的原话是 "Run one teaches it. Run two remembers."——第一遍教它，第二遍它记得。

不想一步步走，还有自治管线 `/lfg`：交给它一个功能描述，它自己跑完整个管线——选路线、执行、简化、评审并应用修复、捕获经验、跑浏览器测试、提交；有远端就推送、开 PR、盯着 CI 做有界修复循环（不获得授权不会自己合并）。适合边界清晰、不值得人工盯全程的任务。

评审本身也有值得单独说的机制：现行 `/ce-code-review` 是 report-only 模式——评审只出报告，落盘修复需要显式执行。它按变更风险挑选评审视角（persona），支持跨模型对抗评审：把代码发给一个配置好的对等模型独立审一遍，本地结论和外部结论合并去重。发给谁、发了什么，Skill 会先向用户披露。

## 安装

发稿时点，Codex 安装要三步——注册 marketplace、用 Bun 装自定义 Agent、再去 TUI 里装插件——因为「Codex 的插件规范还不支持自定义 Agent」。四个月后这个限制连同自定义 Agent 一起消失了：Codex CLI 原生两步装完，Codex 桌面 App 在图形界面里加自定义 marketplace 即可。Bun 安装器只在给旧安装做清理时还有用。

### Claude Code

```text
/plugin marketplace add EveryInc/compound-engineering-plugin
/plugin install compound-engineering
```

已装过的注意：先刷新 marketplace 再更新插件，只跑 `/plugin update` 会停在旧版本。

### Cursor / Grok Bot

```text
/add-plugin compound-engineering
```

Grok Bot 复用 Cursor 账号的插件库，账号上装一次即可，不要在 Grok Bot 的聊天里跑这条命令。

### Codex CLI

```bash
codex plugin marketplace add EveryInc/compound-engineering-plugin
codex plugin add compound-engineering@compound-engineering-plugin
```

Codex App 走图形界面：侧边栏 Plugins → Create 旁的箭头 → Add marketplace，Source 填 `EveryInc/compound-engineering-plugin`，然后搜索安装。

### GitHub Copilot

VS Code 里走命令面板 `Chat: Install Plugin from Source`，仓库填 `EveryInc/compound-engineering-plugin`。Copilot CLI：

```bash
copilot plugin marketplace add EveryInc/compound-engineering-plugin
copilot plugin install compound-engineering@compound-engineering-plugin
```

### Factory Droid / Qwen Code

```bash
droid plugin marketplace add https://github.com/EveryInc/compound-engineering-plugin
droid plugin install compound-engineering@compound-engineering-plugin

qwen extensions install EveryInc/compound-engineering-plugin:compound-engineering
```

两者都直接读 Claude 兼容的插件清单并自动转换格式。

### OpenCode / Pi / oh-my-pi

OpenCode 在 `opencode.json` 的 `plugins` 数组里加 `compound-engineering@git+https://github.com/EveryInc/compound-engineering-plugin.git`（1.x 的键名是单数 `plugin`）。Pi：

```bash
pi install git:github.com/EveryInc/compound-engineering-plugin
pi install npm:pi-subagents   # 派发子 Agent 的 Skill 必需
pi install npm:pi-ask-user    # 推荐：让提问可以阻塞等待回答
```

oh-my-pi 走 marketplace 流程装，建议 `omp config set marketplace.autoUpdate auto` 开自动更新——默认的 notify 模式只写调试日志，不提示。

### 其他

Kimi Code CLI、Cline、Grok Build CLI（`grok`）、Devin CLI、Antigravity CLI（`agy`，Google 已用其替代消费级 Gemini CLI）都有原生安装路径，见仓库 README 的 More Install Options 一节。发稿时点文档里的 Gemini CLI 和 Kiro CLI 两条路径已不在现行安装文档中。

### 装完第一件事

```text
/ce-setup
```

检查环境、报告可选工具能力、创建 `.compound-engineering/config.yaml` 项目配置。任何平台装完都先跑这一步。

## 四个月演变说明了什么

把发文时点和现状并排看，有三件事值得记：

**Agent 数量不是能力。** 发稿时 51 个自定义 Agent 听起来阵容豪华，其中不乏以知名工程师命名的评审视角（DHH 风格 Rails、Ankane 式 README 写作）。四个月后这些独立文件全部退役，评审视角收进 `references/persona-catalog.md` 由 Skill 按风险动态挑选。官方当时自己的文档就没对齐过：主 README 写 37 Skill/51 Agent，组件参考表写 38+/50+，仓库目录实测是 38 个 Skill 和 43 个 Agent。数字在涨的清单不如机制收敛来得可信。

**平台适配在收敛，不在扩散。** 发稿时适配 10 个平台靠一个 Bun/TypeScript 转换器逐个翻译格式；现在官方口径 14 个 agent hosts，靠的是各平台原生插件机制加仓库里的原生清单文件（`.kimi-plugin/`、`.grok-plugin/`、`.devin-plugin/`、`.omp-plugin/`）。维护一个转换器矩阵和维护一组声明文件，工作量不是一个量级。

**贡献政策反转。** 发稿时 README 里有一大段 Kieran Klaassen 的个人声明：不接受任何外部贡献，原因是「没有精力 review，署的是我的名字，风险收益不对称」，PR 只会被 AI 审阅后参考。现在 README 写的是欢迎贡献，维护者变成 Kieran Klaassen 和 Trevin Chow 两个人，立场是「插件有明确主见，不是所有改动都会收」。从独写到双维护者，这个项目把「一个人怎么用 Agent 保持高速」走成了「两个人怎么维护一个有主见的开源项目」。

## 适用边界

**适合：** 持续迭代的产品项目——复利需要时间积累；写代码前愿意先把需求想清楚——brainstorm 的问答省的是返工时间；团队里有人做完功能从不总结——compound 把口头经验变成下个会话能读到的文件。

**不适合：** 一次性脚本和原型验证——走完六步的开销可能超过编码本身；单人小任务量——compound 笔记没有第二个读者；已有运转良好的评审和知识管理流程——这套插件带着自己的工作流主见，会和现有流程打架。

还有一个前置判断：这套插件的 Skill 都是提示词工程，质量取决于模型对长指令的遵循度。六步环路在能力强的模型上是流程保障，在弱模型上可能变成六次走样的模仿。先在一个不重要的仓库跑通一轮，再决定要不要进团队流程。

## 参考

- [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin)
- [Skill 文档目录（每技能一页）](https://github.com/EveryInc/compound-engineering-plugin/blob/main/docs/guides/README.md)
- [Compound engineering: how Every codes with agents](https://every.to/chain-of-thought/compound-engineering-how-every-codes-with-agents)
- [The story behind compounding engineering](https://every.to/source-code/my-ai-had-already-fixed-the-code-before-i-saw-it)
