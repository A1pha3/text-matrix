---
title: "Getting the Most Out of Codex：把 Codex 放进真实工作流"
date: "2026-05-24T10:30:00+08:00"
slug: "getting-most-out-of-codex"
description: "基于 jxnlco 长帖与 OpenAI 官方文档，拆解 Codex 的 durable threads、Steering、thread automations、Goals、shared memory 与 side panel，说明它怎样在真实工作流里接住长任务。"
summary: "这篇文章不按功能菜单介绍 Codex，而是顺着一条真实工作流去看：上下文怎么保留，任务怎么纠偏，长任务怎么继续跑，结果又怎么被审查和留下。"
tags: ["OpenAI", "Codex", "AI Coding Agent", "持久线程", "自动化"]
categories: ["技术笔记"]
draft: false
---

<!-- markdownlint-disable-file MD003 MD041 -->

> 本文基于 [Getting the most out of Codex](https://x.com/jxnlco/status/2057153744630890620) 一文，并结合 [OpenAI Codex 官方页面](https://openai.com/codex/) 与相关开发者文档整理。这里不按功能菜单介绍 Codex，而是顺着一条真实工作流往下看：上下文怎么留住，任务怎么纠偏，长任务怎么继续跑，结果又怎么被审查和记住。
> **延伸阅读**：[OpenAI Codex：轻量级终端编程智能体完全指南]({{< relref "openai-codex-lightweight-coding-agent.md" >}}) ｜ [Superpowers 深度解析：把 AI 编程助手纳入软件工程流程]({{< relref "superpowers-agentic-skills-framework.md" >}}) ｜ [agentmemory：基于真实世界基准的AI编码Agent持久记忆方案]({{< relref "agentmemory-persistent-memory-ai-coding-agent.md" >}})

## 先给结论

看 Codex 时，别只盯着代码生成。更重要的变化是，它把散在编辑器、终端、浏览器、消息系统和待办列表里的动作，收拢到同一条线程里。写代码仍是中心，但最后能不能跑顺，取决于上下文能不能续上、工具能碰到哪里、结果怎么验证、信息又留在哪。

## 先看整体结构

逐条记功能名没什么帮助。把 Codex 看成五层结构，更容易看清它在团队里该怎么落地：

| 层级 | 代表能力 | 主要作用 | 如果没有这一层会发生什么 |
| ---- | ---- | ---- | ---- |
| 持续上下文层 | durable threads、pinned threads | 让工作跨会话延续，不必每次重建背景 | 每次回来都要重新解释项目、目标和偏好 |
| 人在回路控制层 | voice input、Steering、Queuing | 在任务进行中纠偏，或把下一步排进队列 | Agent 一旦走偏，只能等它做完再返工 |
| 执行层 | $browser、@chrome、@computer、MCP | 把动作从 repo 扩到网页、桌面和业务系统 | 线程只能停留在“提出建议”，无法继续执行 |
| 长任务层 | automations、Goals、verifiers | 让工作在你离开后继续推进，并有明确停线 | 长任务只能靠人工反复催促，且没有完成标准 |
| 产物审查层 | side panel、artifact review | 让代码、文档、网页、表格等产物留在原地审查 | 产物与对话分离，修改变成新的交接成本 |

这五层最好按一条工作链来看：先保住上下文，再给人纠偏手段，再把执行范围扩出去，接着用自动化和验证器接住长任务，最后把产物留在原地完成审查。

## 为什么 Codex 的边界已经不只在“写代码”

多数人第一次用 coding agent，仍然会从熟悉的动作开始：读仓库、改代码、跑测试、开 Pull Request。官方页面对 Codex 的定位也是沿着这条主线展开，例如功能开发、复杂重构、代码迁移、代码审查和长时间后台任务。OpenAI 在产品页里把 Codex app 描述为智能体式编码的指挥中心，强调的是多任务并行、技能复用和长时间执行。官方功能文档里还有一个很直接的信号：线程可以选 Local、Worktree、Cloud 运行模式，也自带终端、diff 和 Git 面板。这个产品从一开始就放在执行场景里。

变化出现在“代码之外的那半圈工作”开始被同一系统接住之后。现实里的工程任务，很少只包含编辑源码：

- 你要去浏览器里看预览页，确认渲染后的问题到底是什么。
- 你要查 Slack、邮件或评论系统，搞清楚反馈来自谁、发生在哪个版本。
- 你要执行 shell 命令、导出文档、上传产物，或者在没有 API 的地方补最后一脚。
- 你要在几小时甚至几天后回来，接着同一件事继续做，而不是重新开题。

这些动作一旦进到同一线程里，Codex 处理的就不再只是代码片段，而是一段还没结束的工作。把它当成一次性问答工具，用不上 durable threads、thread automations 或 shared memory 也就不奇怪了。

## 持久线程：把同一件事留在原地

durable thread 更像长期工作区。固定线程后，Codex 能把最容易丢的三类信息留在原地：

- 已经做过的决策。
- 用户偏好和团队约束。
- 正在进行中的上下文与下一步动作。

原帖把 pinned thread 放得很靠前，不是偶然。少了这层，后面的自动化、Goals、审查和交接都得反复补前情。它也不只是“收藏一下”：原帖提到可以用 Command-1 到 Command-9 直接跳进固定线程。高频线程能像常用标签页一样被瞬间召回时，release、审稿、监控这类任务才会真的留在同一条线上。

几个典型线程值得单独建立：

| 线程类型 | 更适合装什么 | 为什么值得单独保留 |
| ---- | ---- | ---- |
| Release thread | 发布节奏、回滚条件、待确认项 | 发布是一条跨天、跨人、跨系统的长链路 |
| Documentation review | 审稿意见、术语约定、待补例子 | 文档质量往往靠多轮回看，而不是一次成稿 |
| Chief of Staff thread | Slack、邮件、会议纪要、待回复问题 | 这类信息最容易碎在不同工具里 |
| External monitoring | 外部渠道、竞品、依赖变化 | 监控类工作天然需要反复回来续做 |

区别在于，你回来时它还停在原来的现场：知道做到哪里、哪些决定已经做过、下一步是什么。

## 语音、Steering 和 Queuing，让人始终留在回路里

voice input 最适合任务还没完全成形的时候。你只记得一个模糊线索，例如“Slack 里好像有人提过这个问题，去帮我找出来”。这类信息如果先被整理成一条过于干净的 prompt，很多关键的不确定性反而会一起被抹掉。

把语音和 Steering、Queuing 放在一起看，会更完整。

### Steering：别等错完了再修

Steering 就是在任务没做完时直接改方向。动作不复杂，但很实用。传统自动化一旦跑偏，用户往往只能等它完成，再从结果里找问题。Codex 的工作模式更接近有人在旁边连续协作：

- 页面审查时，直接在侧边栏标注某个按钮太大、某段 copy 不对、某块间距失衡。
- 文档生成时，在正文尚未收束前指出术语不统一，或者要求把某一节改成面向运营而非面向开发者。
- 调试时，在错误定位路径明显走偏时立刻打断，而不是等一轮无关搜索结束。

这样能少掉一整段走偏后的返工。

### Queuing：下一步别靠人记着

Queuing 不打断当前任务，而是把下一件事排进队列。例如当前构建完成后，自动把预览链接发给 reviewer，或者在修复完成后整理成一段待发送的状态更新。和 Steering 的区别也很直接：

- Steering 改的是“现在做什么”。
- Queuing 改的是“接下来做什么”。

把这两个动作用顺之后，Codex 更像在旁边持续协作。

## 工具外延：从仓库走到网页、桌面和业务系统

线程能持续下去之后，接下来看的就是它到底能碰到哪些表面：仓库、网页、桌面，还是 Slack 这类业务系统。

| 工具层 | 适合处理的事 | 不该期待它解决的事 |
| ---- | ---- | ---- |
| $browser | 在侧边栏里检查和标注网页、预览静态产物、直接看渲染结果 | 依赖你本机登录态的复杂账户流程 |
| @chrome | 需要用户已登录 Chrome 状态的浏览器工作流 | 桌面原生应用或只存在于 GUI 的操作 |
| @computer | 没有 API、只能通过图形界面完成的任务 | 稳定、可脚本化、已经有接口的工作 |
| MCP / connectors | Slack、Gmail、Calendar 等业务系统接入 | 像素级界面操作或本机私有 GUI 交互 |

工具越往外延，越得克制。能用稳定 API 或命令完成的事，不值得回退到 GUI。@computer 更适合补“最后一公里只能手点”的步骤，不适合把原本可维护的流程改成脆弱的录屏脚本。

MCP 和 connectors 的用处，也不在“又多连了几个工具”。很多工程问题最早是从 Slack 消息、Gmail 邮件、日历或评论系统里冒出来的。线程如果能从这些入口直接接住任务，中间就少了一次人工转述。

还要记住 approvals 与 sandbox 的边界。官方文档明确建议大多数任务都收敛在当前 project 或 worktree 里；如果工作跨多个仓库或目录，更稳妥的做法是拆成独立 project，或者为并行任务创建 worktree，而不是让同一线程在项目根之外自由游走。

## Skill 和 Shared Memory：让流程能反复接着做

durable threads 只能保证一条线程不丢上下文，还不够。多条线程之间怎么共享稳定信息，才是 shared memory 出场的地方。

原帖给出的做法很务实：把长期上下文放进一组普通文件里，例如一个 Obsidian vault，线程再围绕这套可检查、可移动、可同步的文件工作。这样的设计有几个直接好处：

- 重要上下文不会只留在聊天记录里。
- 团队可以用 Git、云盘或其他同步层管理它。
- 记忆内容是显式文件，不是黑箱状态，随时能审查和修正。
- AGENTS.md 可以直接规定什么信息该沉淀、什么不该制造噪音。

shared memory 如果只是散乱笔记，意义不大。更值得留下的是这些东西：

- 正在推进的项目与 owner。
- 已做出的决策和原因。
- 仍未关闭的 blocker。
- 后续要追的 open loops。
- 对人、项目和流程有价值的稳定偏好。

原帖同时提到 Codex 自带的 memory 功能与 Chronicle 这类本地 recall 层。更实际的分工是：这类一方记忆适合存偏好、习惯和近期上下文；需要跨线程、跨成员复查的事实，仍然放进显式文件系统。对团队协作来说，这样更稳。

Skill 则负责把已经跑通的流程固化下来。一次次重复描述同一个步骤没有意义；直接把它打包成 Skill，更接近工程资产。

## 移动端：让长任务不中断

移动端很容易被看成功能补充。它更实际的作用，是把长任务从“必须守在电脑前”改成“人可以离开，线程继续跑”。你可以在 Mac 上启动一条依赖本地文件、权限和环境的线程，出门后在手机上查看进度、批准下一步或临时 Steering，回到桌前再接着处理。

官方文档里提到的 floating pop-out window，其实也是同一类设计：线程跟着工作位置走，人不用一直守在同一个窗口里。对长时间任务来说，这种连续性比单个功能点更重要，因为它直接决定了人什么时候必须在场，什么时候只需要做判断。

## Automations 和 Goals，让线程在你离开后继续推进

看 automations 时，先分清它是定时启动新任务，还是定时回到同一条线程。这个差别会直接影响你怎么设计工作流。

这就是 scheduled automation 和 thread automation 的根本差异：

| 类型 | 更像什么 | 适合什么任务 |
| ---- | ---- | ---- |
| Scheduled automation | 定时启动一个新的工作实例 | 每日报表、固定巡检、周期性仓库检查 |
| Thread automation | 定时唤醒同一条线程 | 需要承接上轮上下文的持续性工作 |

上下文收集成本越高，thread automation 越好用。比如一个 Chief of Staff thread 每 30 分钟检查 Slack 和 Gmail，把未回复的问题、优先级和回复草稿准备好。人回来时，最费时间的那部分通常已经做掉了：梳理来龙去脉、排优先级、把回复草稿准备好。

Goals 则给这条线程一个可以停下来的条件。它和“定时继续跑一会儿”不是一回事。弱目标只会说“照着这个 Markdown 文件把计划做完”；强目标会把结果和停线写明，例如：

```text
把内部工具从 Python 迁移到 Rust，
直到新的实现通过全部单元测试为止。
```

强 Goal 至少包含三件事：

- outcome：最终想得到什么结果。
- stopping condition：什么条件满足才算结束。
- verifier：什么信号能证明事情在变好。

原帖列出的 verifier 很实用：测试套件、benchmark、bug 复现、验证矩阵、端到端工作流。benchmark 最容易被讲成宣传数字。更合适的用法，是把它当成局部验证信号。

没有 verifier，Goal 很容易退化成一句愿望。

## Side Panel：让产物留在原地

side panel 最顺手的地方，是它把工件留在生成它的线程旁边。代码、Markdown、PDF、演示文稿、数据表、浏览器页面都可以留在原地继续检查、标注和修改。

这一点会直接改变协作节奏。以往很多工作都要经历一次额外交接：

1. 先生成产物。
2. 导出或发给别人。
3. 在另一个窗口或另一个系统里审查。
4. 把修改意见重新贴回任务上下文。

side panel 把这个回路缩短成同一个线程里的连续动作。大致就是四类工作：

- 查看产物（inspect artifacts）
- 标注修改点（annotate changes）
- 直接操作网页（operate web surfaces）
- 审查变更（review changes）

尤其在文档、轻量网页、Storybook、浏览器幻灯片和数据应用这类产物上，这个机制会比“生成后再切出去看”顺畅得多。

## 一次真实任务怎样流过 Codex

如果前面这些能力还是显得抽象，可以看一个更完整的任务流。假设团队正在推进一次版本发布，外部 reviewer 在 Slack 里反馈预览页有问题。

### 任务流转

1. 团队先有一条固定的 release thread，里面保存版本目标、回滚条件、已知风险和 reviewer 名单。
2. thread automation 每隔一段时间检查 Slack 回复、PR 评论和相关邮箱。
3. reviewer 在 Slack 里指出预览页文案有误、某个按钮间距不对。
4. Codex 在同一线程里拉起 repo，定位改动点，并用 $browser 打开预览页确认是样式问题还是内容问题。
5. 如果问题依赖登录态或浏览器上下文，就切到 @chrome；如果最后上传动作只能走桌面图形界面，再交给 @computer 收尾。
6. 修复完成后，Goal 的 verifier 不是“我觉得差不多了”，而是测试通过、预览页检查通过，必要时再补一个端到端回归。
7. diff、预览页和待发送消息都留在 side panel 附近审查，用户可以直接 Steering 某个细节，或 Queuing 下一步动作。
8. 这次发布过程中新增的决定、风险和 follow-up 再写回 shared memory，而不是散在聊天记录里。

这个例子里要看的，是这些能力怎么在一条线程里接起来。线程负责把事情留在原地，工具负责碰到具体表面，Goals 给出停线，side panel 让审查不离场，shared memory 把长期上下文留下。

## 采用顺序：别一上来就追求全自动

这类系统最容易踩的坑，是还没建立线程与验证器，就急着追求全自动。更稳的采用顺序通常是下面这样：

1. 先建立一两条 pinned thread。选最常反复发生的工作流，例如 release review 或文档审稿，让上下文先固定下来。
2. 再把 Steering 和 Queuing 用起来。先学会在任务进行中纠偏，而不是只会下达起始 prompt。
3. 然后扩工具边界。优先接入浏览器与业务系统，把“发现问题”到“开始处理”的断点打通。
4. 最后再上 automations 与 Goals。等线程结构稳定后，再让任务在你离开时继续跑，否则只是把混乱放大。

对应地，也有几类场景不该过度寄望于 Codex：

- 你自己对目标系统几乎没有基本判断，无法分辨结果是偏了还是对了。
- 任务要求每一步都做强审计留痕，且不能容忍 Agent 的中间不确定性。
- 实时性极高，延迟本身就是主要成本，例如高频交易式操作。
- 明明有稳定 API 或脚本入口，却仍然试图用 GUI 自动化取代一切。

工具边界越往外走，人越需要保留判断权，而不是把判断一起外包出去。

## 最后的判断

放回真实工作里看，Codex 更像一条持续运行的任务线：代码改动、审查、记忆和自动推进都围着同一个上下文展开。它当然还不是万能助手，但也早就不只是单次代码生成器了。

真正决定它能不能进团队流程的，不只是写代码水平，还看 durable threads、shared memory、Steering、Goals 这些基础件有没有一起到位。代码生成只是入口；上下文能不能续上、动作能不能验证、记忆能不能复查，才是它稳定落地的关键。

## 参考资料

- [Getting the most out of Codex](https://x.com/jxnlco/status/2057153744630890620)
- [OpenAI Codex 官方页面](https://openai.com/codex/)
- [Codex App Features](https://developers.openai.com/codex/app/features/)
- [Codex Automations](https://developers.openai.com/codex/app/automations)
- [Codex Skills](https://developers.openai.com/codex/skills)

## 继续阅读

- [OpenAI Codex：轻量级终端编程智能体完全指南]({{< relref "openai-codex-lightweight-coding-agent.md" >}})：如果你更关心 CLI 安装、配置、安全模型和终端用法，先读这一篇。
- [Superpowers 深度解析：把 AI 编程助手纳入软件工程流程]({{< relref "superpowers-agentic-skills-framework.md" >}})：如果你想把 Codex 放进更严格的 brainstorming、worktree、TDD 与 review 流程里，这篇更直接。
- [agentmemory：基于真实世界基准的AI编码Agent持久记忆方案]({{< relref "agentmemory-persistent-memory-ai-coding-agent.md" >}})：如果你对本文里的 shared memory 特别感兴趣，可以继续看持久记忆层怎么落到编码 Agent 上。
