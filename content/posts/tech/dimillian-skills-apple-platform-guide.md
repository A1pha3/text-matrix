---
title: "Dimillian 的 16 个 Codex 技能停在 3 月：成色、坑与能搬走的东西"
date: "2026-04-01T01:21:00+08:00"
lastmod: "2026-10-05T00:00:00+08:00"
slug: "dimillian-skills-apple-platform-guide"
github_repo: "Dimillian/Skills"
source_key: "gh:Dimillian/Skills"
description: "Dimillian/Skills 是 Ice Cubes 作者 Thomas Ricouard 的个人 Codex 技能库：16 个 Apple 平台技能、49 份参考文档、两个只读多智能体 swarm。仓库最后提交停在 2026-03-29，本文基于该最终状态逐一核实，并指出官网索引滞后、作者本机绝对路径泄漏等安装前须知。"
draft: false
categories: ["技术笔记"]
tags: ["Skills", "Apple", "iOS", "macOS", "Codex", "代码审查"]
---

# Dimillian 的 16 个 Codex 技能停在 3 月：成色、坑与能搬走的东西

[Dimillian/Skills](https://github.com/Dimillian/Skills) 是 Thomas Ricouard（GitHub ID Dimillian，开源 Mastodon 客户端 Ice Cubes 的作者）维护的个人 Codex 技能库：16 个覆盖 SwiftUI、Swift 并发、macOS 打包、iOS 调试、代码审查的技能文件夹，放进 `$CODEX_HOME/skills` 就能用。仓库描述只有四个词——"My Codex Skills"。它不是框架，没有安装器，也没有版本号。

看这个仓库，有三件事值得先说清楚。第一，它已经停更：最后提交停在 2026-03-29，此后包括 issue 和 PR 在内无人回应，所以本文核查的是它的最终状态，不存在"文章发表后项目又变了"的问题。第二，它的重心不在那 16 个 SKILL.md 提示词上，而在 49 份参考文档里——最大的技能 `swiftui-ui-patterns` 一个就带 30 份组件级 SwiftUI 参考，这批文档才是抄作业的主要对象。第三，配套的 GitHub Pages 官网展示的技能列表滞后于仓库：索引文件停在 8 技能时代，里面还列着一个早已删除的技能。

这三点决定了它的用法：拿它当"一个成熟独立开发者怎么拆解日常工作流"的样本，价值很高；拿它当持续维护的依赖，就得接受自己接手维护。

## 项目坐标

| 项 | 值 | 出处 |
|------|------|------|
| 定位 | 面向 Codex 的 Apple 平台开发技能集合 | README 首段 |
| 作者 | Thomas Ricouard（Ice Cubes for Mastodon 开发者） | LICENSE 版权行、提交作者字段 |
| 星标 / 复刻 / 关注 | 3,987 / 206 / 43 | GitHub 仓库接口，2026-10-05 取 |
| 发文时点星标 | 约 3,051 | Wayback Machine 2026-04-01 快照实拍 |
| 提交数 / 贡献者 | 55 次：作者 53 次，popey 与 musiienko 各 1 次 | contributors 接口 |
| 技能规模 | 16 个技能目录，SKILL.md 合计 1,905 行 | 仓库 main 分支实测 |
| 参考文档 | 49 份，集中在 8 个技能的 `references/` 下 | 同上 |
| 开放 issue / PR | 4 个 issue、7 个 PR，发文后新增的均无人处理 | GitHub 接口，2026-10-05 取 |
| 许可证 | MIT（2026-01-07 才补上） | `LICENSE`、提交 `c8310b3` |
| 语言占比 | Shell 84.6%、Python 12.8%、Swift 2.6% | languages 接口 |
| 配套站点 | [dimillian.github.io/Skills](https://dimillian.github.io/Skills/)（在线，索引滞后） | Pages badge、HTTP 200 实测 |

发文时点的星标值得单独说明：仓库 4 月 1 日的 Wayback 快照记录是 3,051，两天后是 3,084，现在是 3,987——停更半年还在自然增长，说明它的参考文档确实有人在用。

## 三个月建成，之后零提交

55 个提交的分布讲了一个完整的故事：2025 年 12 月 30 日一天之内建仓、迁移存量技能、上线 Pages 站点；1 月上旬集中扩写参考文档；3 月中旬开始把审查类技能改造成多智能体形态；3 月 29 日完成最后三个提交后彻底停笔。

| 时间 | 事件 | 锚点 |
|------|------|------|
| 2025-12-30 | 建仓，首批技能入库，同日上线文档站 | 提交 `052112b`、`0ac245e` |
| 2025-12-31 | 加入 gh-issue-fix-flow 技能；动态索引 + pre-commit hook | `271249b`、`26e23c0` |
| 2026-01-04~07 | SwiftUI UI Patterns 及 30 份参考文档；SwiftPM 打包模板；补 LICENSE | `70a15d0`、`f07d884`、`c8310b3` |
| 2026-03-04 | 删除 gh-issue-fix-flow（提交信息只写了 "Update"） | `343f5b3`，-52 行 |
| 2026-03-16 | 加 project-skill-audit；全库补 OpenAI agent 元数据 | `7c43dba`、`1d09141` |
| 2026-03-19~28 | 审查技能加并行 sub-agent，随后改为只读约束 | `bc7f788`、`23e5213` |
| 2026-03-29 | 最后三连：simplify-code 改名、加 review-swarm、加 bug-hunt-swarm | `4537667`、`56d971f`、`05ba982` |
| 2026-04-01 | 被收录进 Awesome Codex CLI（即本文发表当天） | issue #12 |
| 2026-05~07 | 社区提了 3 个 PR（iOS 调试加固、Software Graph Analysis、SwiftData Testing），全部无人合并 | PR #15/#16/#17 |

两个时间点之间的对比很说明问题：3 月 29 日下午 5 点 28 分，作者还在给 README 更新 swarm 技能的描述；5 月 6 日有人提议做成 Claude 的 marketplace（`/plugin` 一键安装），零回复。停止维护这件事本身，成了这个仓库现状的一部分。

## 一个技能目录里有什么

每个技能文件夹的结构是固定的三层，理解这三层比记住 16 个技能名更重要：

| 层 | 内容 | 现状 |
|------|------|------|
| `SKILL.md` | 技能本体：frontmatter 的 `description` 写明触发条件，正文是工作流指令 | 16 个技能全有，最短 51 行（ios-debugger-agent），最长 202 行（swiftui-view-refactor） |
| `agents/openai.yaml` | Codex 的 agent 接口元数据：显示名、一句话描述、默认提示词 | 15 个技能有；review-and-simplify-changes 是唯一没有的 |
| `references/` | 按主题拆分的参考文档，SKILL.md 按需引用 | 8 个技能共 49 份，其余 8 个技能为零 |

`openai.yaml` 的默认提示词展示了 Codex 的技能引用语法，比如 review-swarm 的是："Use $review-swarm to review the current diff with four focused read-only reviewers and summarize the highest-signal issues."。这层元数据是 3 月 16 日一次性补齐的，说明作者在乎这套库在 Codex 界面里的呈现，而不只是文件能跑。

规模分布也能看出侧重：审查和诊断类技能的 SKILL.md 普遍在 170 行上下（指令密度高），而 swiftui-ui-patterns 的 SKILL.md 只有 95 行——因为它把内容都拆进了 30 份参考文档，正文只负责路由。

## 三条主线

把 16 个技能按"它替你做什么"分组，比按字母排序更接近作者的实际用法。

### Apple 平台知识线：49 份参考文档的大头

这条线覆盖 SwiftUI 开发的日常循环，也是这个仓库区别于普通提示词合集的地方。

**swiftui-ui-patterns** 是最大的一个：30 份参考文档覆盖 NavigationStack、sheets、deeplinks、焦点、网格、TabView 等具体组件，SKILL.md 本体只保留两条路由（已有项目找最近邻示例，新项目按 app-wiring 骨架起手）和一张状态归属矩阵。那张矩阵值得单独看：它按"谁拥有这个状态"给出 `@State`、`@Binding`、`@Observable`、`@Environment` 的选择路径，并明确 iOS 16 及以下回退到 `ObservableObject` 家族——这种把版本边界写死在规则里的做法，比一句"优先用新 API"实用得多。

**swiftui-performance-audit** 的 7 份参考里有 4 份是 WWDC 会话与 Apple 官方指南的摘要稿（Demystify SwiftUI Performance、Instruments 优化、卡顿识别、SwiftUI 性能模式），外加代码坏味清单、性能剖析接谈清单和报告模板。它的设计分两层：代码审查能定位的就直接给结论，定位不了的引导用户自己跑 Instruments——不假装 agent 能替代采样分析。

**swift-concurrency-expert** 针对 Swift 6.2+ 并发，参考文档包含 Swift 6.2 approachable concurrency 和 WWDC SwiftUI 并发专场摘要，具体动作从修 actor isolation 到把 completion handler 迁到 async/await。

**swiftui-liquid-glass** 处理 iOS 26+ 的 Liquid Glass API 采用（modifier 顺序、分组、交互性、回退）；**swiftui-view-refactor** 把大视图文件拆成小子视图，明确偏好 MV 数据流而非 MVVM；**macos-spm-app-packaging** 附带一整套可执行模板——从 SwiftPM 脚手架、`.app` 组装、签名公证到 Sparkle 更新的 appcast 生成脚本；**macos-menubar-tuist-app** 约束 Tuist 清单归属和 store 层架构；**ios-debugger-agent** 依赖 XcodeBuildMCP 在已启动的模拟器上构建、启动、检查 UI、截图、抓日志。

### 多智能体 swarm 线：只读约束是设计核心

review-swarm 和 bug-hunt-swarm 是 3 月下旬改造的产物，也是这个仓库里最有模式感的设计。

两个 swarm 共享同一套骨架。入口先建"包"：review-swarm 组装意图包（预期改变什么、什么必须不变、有哪些约束），bug-hunt-swarm 组装 bug 包（症状、期望与实际行为、复现步骤、影响面、已有证据六项）。然后并行发四个只读 sub-agent，每个拿到相同的包，各自盯一个切面——review-swarm 的四个角色是行为回归、安全与隐私、性能与可靠性、契约与测试覆盖；bug-hunt-swarm 的是复现与范围、代码路径追踪、回归源定位、最快证明步骤。

只读不是口号，每个 sub-agent 的指令里都重复了同一组禁令：不许编辑文件、不许 `apply_patch`、不许 stage、不许 commit。发现只汇报不落地，主 agent 拥有唯一的综合权：去重、丢弃弱声明和风格评论、把幸存的发现规范成六字段（位置、类别、严重度、理由、建议、置信度），按严重度排序后给出 fix now / fix soon / optional follow-up 三档路径。bug-hunt-swarm 还额外要求按"最快证明步骤"排序——先验证哪个假设最便宜。

这套设计里有一条容易被忽略的指令："如果没有实质问题，直说，不要制造反馈。"多智能体审查最常见的失败模式是四个 agent 为了交差凑出 20 条噪音，这条指令是对症下药的。

### 工程流程线：把重复劳动脚本化

剩余六个技能处理开发流程本身。**github** 封装 `gh` CLI 的 issue、PR、workflow runs 和 API 查询；**app-store-changelog** 带一个 bash 脚本从 git 历史收集变更——`git describe --tags --abbrev=0` 找最近 tag，找不到就回退全历史，然后过滤出用户可见的变化重写成 "What's New" 要点；**orchestrate-batch-refactor** 用工作包模板把大重构拆给多个 sub-agent，附依赖感知的并行分析；**project-skill-audit** 反过来分析项目的历史 Codex 会话和 memory，推荐该造什么新技能、该更新哪些旧的——这是写给自己技能库的维护工具；**review-and-simplify-changes** 是唯一允许改代码的审查技能（安全、保持行为的修复）；**react-component-performance** 是全库唯一的非 Apple 技能，处理 React 重渲染抖动和列表瓶颈。

## 一次 review-swarm 的完整流转

用一个具体场景把这套机制串起来：改动了两个文件——`PaywallView.swift` 和 StoreKit 封装——已 stage，准备合并前跑一次审查。

第一步是范围判定。按技能定义的优先级，用户没指定文件，就取当前改动；因为改动已 stage，选 `git diff --cached` 而不是 `git diff`——技能文档专门强调要选"最小正确的 diff 命令"，混合改动时两个都要看。发 sub-agent 之前，主 agent 先读 `AGENTS.md` 和涉及的架构文档，组装意图包：这次改的是解锁逻辑，付费墙的展示行为必须不变，StoreKit 版本兼容是显式约束。

第二步是四个只读 reviewer 并行开工。行为回归角色检查调用方与被调用方的契约漂移；安全角色盯 entitlement 和收据校验；性能角色看有没有把 I/O 加进启动路径；契约角色发现 StoreKit 封装的测试没跟上。每个都只回报"文件加行号、问题、为什么重要、建议、置信度"。

第三步综合权回到主 agent。四个 reviewer 各报了三五条，重复的被合并，"建议把这个 computed property 改成函数"这类风格评论被丢弃，幸存的六条按严重度排好：两条 high（一条行为回归、一条测试缺口）进 fix now，两条 medium 进 fix soon，两条 low 挂 optional follow-up。全程没有任何文件被改动——审查的产出是排序后的判断，不是补丁。

如果四个 agent 一无所获呢？按指令直说"没有实质问题"，然后收工。

## 安装之前要知道的四件事

停更仓库照用不误，但这四件事值得在拷文件之前知道。

**官网的技能列表是过时的。** Pages 站点靠 `docs/skills.json` 渲染，这份索引最后一次生成停留在 8 技能时代：它还列着 3 月 4 日已删除的 gh-issue-fix-flow，却缺后来加入的 8 个技能（含两个 swarm）。根因是那个 pre-commit hook——它会在每次提交时自动重建索引——需要手动启用，clone 下来的仓库并不会自动跑。想核对技能清单，以仓库目录和 README 为准，别信官网。

**有一处作者本机的绝对路径没清干净。** `project-skill-audit/SKILL.md` 第 182 行链接指向 `/Users/dimillian/.codex/skills/.system/skill-creator/SKILL.md`，这只在作者机器上有效。5 月 9 日有外部用户提了 issue 指出可移植性问题，同样零回复。拷贝这个技能后需要自己把那行改成相对引用或直接删掉。

**Claude Code 用户要自己做适配。** SKILL.md 的结构（frontmatter + 工作流正文）是通用格式，参考文档与 agent 无关，直接可用；但 `agents/openai.yaml` 是 Codex 特有的接口元数据，Claude Code 不会读。3 月 30 日就有人在 issue 里问能否用于 Claude Code，5 月又有人提议做 marketplace 格式，都没有回应——适配的成本由使用者自己承担。

**三个社区 PR 停在门外。** 6 到 7 月陆续有 PR 提交：加固 ios-debugger-agent 的安装指引、新增 Software Graph Analysis 技能、新增 SwiftData Testing 技能。全部 open 状态。它们的内容质量未经验证，但如果你想自己接手维护这个库，这是现成的起点。

## 谁该怎么用

**Codex + Apple 平台开发者**：这是库的目标用户。整库拷进 `$CODEX_HOME/skills`——按 README 的原话是"place these skill folders under `$CODEX_HOME/skills`"，注意拷的是技能文件夹本身，别把 README、LICENSE、docs 一起塞进去。装完顺手修掉上面那处绝对路径。

**其他 AI 编程工具用户**：SKILL.md 里的规则和 49 份参考文档与具体 agent 解耦，价值最大的是 swiftui-ui-patterns 的组件参考和状态归属矩阵、swiftui-performance-audit 的 WWDC 消化稿。当文档库读，比当工具装更划算。

**想搭自己技能库的人**：这个仓库的结构本身就是答案。`project-skill-audit` 先回答"该写什么技能"，SKILL.md 保持百行以内的指令密度，知识重的地方拆 `references/` 按需加载，需要界面呈现的补一份 `openai.yaml`，最后用索引脚本生成站点。12 月 30 日一天建成、三个月迭代出 49 份参考文档的节奏，说明这套结构撑得起真实使用。

## 结语

Dimillian/Skills 的样本价值大于依赖价值。一个把 SwiftUI 日常循环拆成 16 个技能、给审查装上只读护栏和置信度过滤、给性能调优配上 WWDC 讲义的做法，是可以整体搬走的工程判断；而它停更之后暴露的问题——索引不同步、绝对路径泄漏、社区贡献无人接——同样是一份现成的"个人技能库维护成本"清单。抄它的结构，接住它的维护，这两件事都不需要它继续更新。
