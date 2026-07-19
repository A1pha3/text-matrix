---
title: "把 /goal 当开关用是错的：Fable 5 与 GPT-5.6 Sol 在一个 NP-Hard 优化题上的对照实验"
date: 2026-07-19T19:00:00+08:00
tags: ["claude-code", "codex-cli", "benchmark", "optimization", "agent-evaluation", "fable-5"]
categories: ["tech"]
slug: fable-5-gpt-5-6-sol-goal
description: "持续机制在 NP-Hard 优化任务上是赌博：胜率 4/6、均值两次都变差。Claude Code 的 /goal 走独立评估器，Codex 走持久化工具。"
---

# 把 `/goal` 当开关用是错的：Fable 5 与 GPT-5.6 Sol 在一个 NP-Hard 优化题上的对照实验

**适合读者**：正在给 agent 选 / 评估 CLI 工具或设计持续机制的工程团队；做 OR / 优化类基准的人；维护 Claude Code、Codex 类 Coding Agent 的人。读完要能说出"持续机制对什么任务有效、对什么任务拉均值"，并能讲清楚 Claude Code 与 Codex 的 `/goal` 在实现层属于两个东西。

## 一句话定调

Charles Azam 在 2026 年 7 月的一篇博客里把同一道题分别丢给 Claude Fable 5 和 GPT-5.6 Sol 做各自 30 分钟、开了各自原生 `/goal` 与不打开的对照。结论不长，但有几条对工程实践有冲击：

- Fable 5 在这道题上是真正的"野兽"，它的 baseline（不开 /goal）已经把 Sol 的 baseline 拉开 1875 分，并且方差收敛到 319 分。
- `/goal` 在 6 次配对里赢了 4 次——但两次模型的平均成绩都比不开时更差。
- 同一个 `/goal` 命令，背后是两套完全不同的实现：Claude Code 走外挂评估器，Codex 走持久化工具调用。

把这篇博客翻译成中文不会有任何增量。把其中能在工程判断里直接借鉴的部分拆开来讲，才有意义。

### 这道题长什么样

KIRO 是 Charles 在 2018 年作为工程学生做过的光纤网络设计题，作为黑客松题目提交。它给三座城市（Grenoble、Nice、Paris）的有向距离矩阵，要求把若干分配点和若干终端用"环 + 短链"两种结构连起来，满足一坨结构性约束，目标函数是电缆总长度，越短越好。

一组合法方案长这样：

- 每个城市若干分配中心（hub）作为根。
- 从每个 hub 出发建若干**有向冗余环**。
- 从环上某些塔上**短分支**挂着短的链状结构（链长有限制，文章里给的是 ≤ 30）。
- 每个塔只能出现一次。
- 同一个线段方向反过来，总成本可能不一样——这是一个**非对称代价**的问题，不是常见教科书的 Steiner 树。

光把每个终端塞给哪个 hub 这一个变量，巴黎一个城市就有 `11^532` 种选法。如果再把"必须恰好 19 个 28 节点的环、没有分支"这个偏窄但合法的子集取出来，光这一支的有效解就有：

```
(532! / 19!) × 11^19  ≈  10^1223
```

这是个 10 的 1223 次方量级的搜索空间。Charles 当年自己写 C++ 搞了一周才给出个不错的基准解。

题本身不公开，但它的结构性约束（hub root + 有向环 + 短分支 + 非对称线段代价）是 OR / 网络流优化里典型的一类题。文章附录的 CLIArena 仓库里给的是模型可执行版本。

## 实验怎么搭的

Charles 把实验设计得非常窄。这是这件事最值得学的地方之一——他没去搞 6×6 全因子扫，他只盯着旗舰对：

| 项 | 取值 |
| --- | --- |
| 模型 | Claude Fable 5、Opus 4.8、Sonnet 5；GPT-5.6 Sol、Terra、Luna |
| 模式 | Plain、原生 `/goal` |
| 优化预算 | 30 分钟 |
| 外层 agent 超时 | 1900 秒 |
| 推理档位 | 每个模型都调到最高 |
| 运行环境 | Harbor 0.1.43 + Docker + 订阅登录 |

判断很直白：先把旗舰两条打三对配对（每对 = plain + /goal），其余四个模型每个打一对 30 分钟对照，画一张总览图。后面所有深度比较只看旗舰那三对。

## 一次配对比三句话更能说明问题

先把最重要的东西摆出来。旗舰对的六次 30 分钟运行（每对 = 同一次环境、同一段时间、只有 plain 与 `/goal` 的开关差异），结果如下：

| 模型 | Pair | Plain | `/goal` | Δ（Goal − Plain） |
| --- | --- | --- | --- | --- |
| Fable 5 | 1 | 32,197 | **31,934** | −263 |
| Fable 5 | 2 | 32,516 | **32,324** | −192 |
| Fable 5 | 3 | **32,446** | 35,178 | +2,732 |
| GPT-5.6 Sol | 1 | **33,581** | 39,371 | +5,790 |
| GPT-5.6 Sol | 2 | 35,539 | **32,703** | −2,836 |
| GPT-5.6 Sol | 3 | 33,663 | **33,313** | −350 |

指标是总电缆长度，**越小越好**。负值代表 `/goal` 这一把赢了。

摆完这张表，三句话可以直接照念给团队：

- **胜率看着像 4/6，挺好——但均值两次都变差**。开 `/goal` 的那一把，确实有较大概率更短；但偶尔会拉到比不开时糟糕得多。
- **模型本身的差距比 `/goal` 造成的差距大一个数量级**。Fable 的 baseline 已经把 Sol 的 baseline 拉开 1875 分，Fable 的全程最佳得分 31,934 来自加 `/goal` 那把，最稳的得分来自不开 `/goal`。
- **方差上是两个形状**。Fable 6 次结果挤在 319 分窗口里；Sol 6 次横跨 1958 分窗口。这跟"哪一把要开 `/goal`"是同一个问题，同一面镜子。

把这三条压成一页 PPT 给决策者就够用。后面展开的不外乎两个：为什么均值比胜率重要、为什么不同的 CLI 实现会在 benchmark 里产生这种差。

### 旗舰配对的均值与方差

| 模型 | Plain 均值 | `/goal` 均值 | 均值差 | 中位数差 |
| --- | --- | --- | --- | --- |
| Fable 5 | **32,386** | 33,145 | +759（变差） | −192（变好） |
| GPT-5.6 Sol | **34,261** | 35,129 | +868（变差） | −350（变好） |

模型差距：

- Fable plain 比 Sol plain 均值低 **1875 分**；
- Fable plain 的 6 次成绩挤在 **319 分**区间，Sol plain 横跨 **1958 分**；
- 全场最佳（**31,934**）来自 Fable goal；最稳的配置是 Fable plain。

结论一句话：**Fable 是不开 /goal 的最佳默认，要搏一次爆款才开 /goal**。

## 旗舰三对配对结果（原文对应表）

上面那张表是原文复刻。读自己反写这一版时，可以跳到下一节读"为什么均值和胜率会错位"。

## 同一个 `/goal` 背后是两套完全不同的东西

**先抛结论**：Claude Code 和 Codex 都暴露一个叫 `/goal` 的命令，但代码读下去会发现这俩的实现是两种本质上不同的系统。模型差距不到 2000 分时，CLI 实现的差距往往会吃掉一部分。

Claude Code 和 Codex 都暴露一个叫 `/goal` 的命令，但代码读下去会发现它俩的实现是两种本质上不同的系统。

### Claude Code：独立评估器 + 会话级 Stop hook

Anthropic 的 Claude Code 把 `/goal` 实现成一个**会话级 Stop hook**：

- 主模型每跑完一轮回复，控制权交给一个叫**评估器**的小模型（默认是 Haiku）；
- 评估器读这一轮的结论与对话上下文，输出 yes/no 加理由；
- 评估器答 no，主模型再跑一轮；
- 评估器答 yes，把 goal 清掉、任务结束。

评估器**不能用工具、不能读文件**，只能看见对话记录。这是一条提前固化下来的边界——评估器看不到 agent 在文件系统里查了什么、跑了什么测试、改了什么代码。它只能在主模型已经在 transcript 里写出来的证据上做判断。

这个设计的好处是评估器和主模型相互独立，ground truth 不来自自己。坏处是它对**外部进展**一无所知：评估器判断"再试一次"还是"够了"，它永远不会知道"再调用一亿次 solver 迭代是不是能再多砍 200 分"，因为它根本看不到那部分工作。

文章里特意提醒一句："Claude Code 不开源，我们只能信 Anthropic 自己公开的文档。"——这是评估 Claude Code 实现时不可省略的注释。

### Codex：持久化状态 + 生命周期工具

Codex 这一侧，Charles 直接读了被测的那个版本的源码（Codex CLI 0.144.4）：

- 目标字符串保存在**线程级 TUI 状态**里；
- 完成状态、剩余预算被写进一个 **SQLite** 表里；
- 主模型能看到三个原生工具：`create_goal`、`get_goal`、`update_goal`；
- 如果线程空闲而 goal 还活着，Codex 注入一个**续轮 prompt**，把目标原文 + 一次完成审计塞回主模型。

这两套实现的关键差异，对照着读比较快：

| 维度 | Claude Code `/goal` | Codex `/goal` |
| --- | --- | --- |
| 评估由谁完成 | 独立的小模型（默认 Haiku） | 主模型自己（通过续轮 prompt） |
| 评估能看到什么 | 仅对话记录 | 全部文件、shell、工具返回 |
| 目标存在哪 | 会话级 Stop hook 状态 | TUI 线程状态 + SQLite 账本 |
| 预算控制 | 自然语言条件字符串 | 显式 `update_goal` 工具调用 |
| 评分 | 独立评估，看 transcript | 主模型自评，可能反复 commit |
| 适合判断 | 答了什么 | 干了什么 |

文章里那句判断很精炼："Claude delegates completion to another model. Codex lets the working model declare completion, then resumes it."——一外包，一自包。

### 一个任务分别怎么流过这两套系统

把 KIRO 这种"主模型先选 solver、再花 30 分钟迭代"的优化任务，分别喂进两套 `/goal`，流转会差很多：

**Claude Code 这次的开 /goal 流程**：

1. 用户侧：`/goal minimize total cable length under all constraints`。
2. 主模型第 1 轮：读题，决定用一个启发式局部搜索 + 邻域扰动的 Python solver，开始迭代。
3. 主模型第 1 轮结束：Claude Code 调度 Haiku 评估器读 transcript，问"目标达到了吗？"——评估器看到主模型刚提交了一个 checkpoint，但还没说完成，回 `no: 主模型还在迭代中`。
4. 主模型第 2 轮：继续跑 10 分钟，再交 checkpoint。
5. Haiku 再判一次，回 `no`；如此往复。
6. 第 N 轮，主模型发现邻域已经饱和、改换更慢的精确搜索 → 评估器仍然只看 transcript，看不出"换 solver 是个坏主意"的事实，只会回 `no: 还没收敛`，让主模型继续往这个坏方向走。

**Codex 这次的开 /goal 流程**：

1. 用户侧：`/goal minimize total cable length`。
2. Codex 把目标字符串 + 状态写进线程 TUI + SQLite 账本。
3. 主模型拿到 `create_goal / get_goal / update_goal` 三个工具，开始迭代。
4. 主模型觉得接近最优，调用 `update_goal` 把状态置为 `satisfied`，任务结束。
5. 或者线程意外空闲：Codex 注入续轮 prompt，把 goal 原文 + "你声称已满足，请 audit" 塞回去，让主模型自己盘一次。
6. 主模型在 Sol 那次开了 `/goal`，盯死了一个穷举扫锚点策略，长时间不更新 goal——Codex 没有独立评估器能指出"这是错的"，只能等超时。

两个流程在 Charles 实验里区分得很清：

- Fable 在 Claude Code 里开 `/goal`：评估器看见主模型没撒谎（每次回复都说"还在跑"），就一直放行；
- Sol 在 Codex 里开 `/goal`：主模型自己估算 anchor 还能榨，就一直 commit。

问题在于**两套都是按"对话级/线程级叙事"在判**，而不是按"迭代质量是否在下降"在判。对于"决定一个 solver 之后不能再回退"的优化任务，这种评估几乎一定会在坏方向上多走一段。

## 为什么均值和胜率会错位

把 `/goal` 的胜率（4/6）和均值（两次都变差）摆在一起，逻辑上只能存在一种解释：**赢的时候赢一点，输的时候输一大截**。

在编码任务里，每多一轮通常能多修复一个测试、多推进一步迁移，进步是肉眼可见的。优化任务不一样：

一旦 agent 选定一个 solver（用什么启发式、什么邻域结构、什么扰动算子），**多出来的时间只会放大这个决定**：

- 决定好的 solver，多 30 分钟会把搜索推到更深的盆地，给到历史最佳；
- 决定烂的 solver，多 30 分钟会沿着错误的结构搜得更深，给到历史最烂。

Charles 的三对配对把这条打到了：

- `/goal` 帮到的时候：Fable 的 编译期并行 solver、或 Sol 的"链重新分配到别的 hub"；
- `/goal` 害到的时候：Fable 选了一个慢的 solver、或 Sol 盯死在一个穷举扫锚点策略上。

中位数轻微正移，**坏尾拉得很长**。这就是为什么 `/goal` 在 6 次里赢了 4 次，却让两个均值都变差。换成日常语言：

> **对一个会选 solver 的 agent，多续一次并不能保证"再想一会儿"就更聪明。它只是在 commit 的方向上再深一层。**

### 立刻能抄走的两条工程经验

1. **持续机制的产品名别再用"自动续 + 必胜"那种叙事**。它实际是个有约束的赌：每次续都在 commit 当前方向，赢要小赢、输可能大输。
2. **优化类 benchmark 看均值，不看胜率**。4/6 这种胜率对销售很香、给决策很毒；均值和方差才是真正决定 SLA 的数。

## 这套 benchmark 的边界

文章自己留了几条限制，写下来比照搬结论更负责：

- 只有 Fable 5 和 Sol 各三对配对；其余四个模型各一对，存在 prompt / wrapper / 时间上限不严格对齐；
- 任务跑在订阅服务的串行调度上，调度可能漂移；
- 容器实际给了 **8 个 CPU**，但任务元数据声明是 1 个——这显然偏向 Fable 的多解并行策略；
- 所有 Fable 与 Sol 的最终输出都合规，部分因为 wrapper 强制要求早 checkpoint 与最终 verify；
- 测的是**完整系统**：模型 + CLI 工具 + prompt + 订阅服务 + Harness，**不是单模型裸跑**。

读这种带广告味的 benchmark 结论时，有一条通则可以套：作者测的是**整链路**，工程师看到的"模型强 10%"其实是 CLI、prompt、调度、Harness 拼接后的结果，不要拆开归因。

## 怎么复现

Charles 把全部任务定义、wrapper、分析脚本、图表生成、原始评分备忘录都开在 GitHub 仓库 [`charles-azam/CLIArena`](https://github.com/charles-azam/CLIArena)。原始运行目录因为体积不进 Git，备忘录里完整记录了每一条可发布的成绩、城市拆分、耗时、所用策略、被排除项和 run ID。

复现入口三行：

```bash
RUN_ID=article-kiro-YYYYMMDD-clean \
PHASE=nohint-all \
./scripts/run_subscription_article_matrix.sh

uv run python scripts/summarize_subscription_article_results.py RUN_ID...
uv run python scripts/analyze_subscription_article_results.py RUN_ID...
```

照搬这套设置时要注意：8 CPU 容器 + 订阅登录态，两条都会强烈影响结果方差，前者是设备差异、后者是订阅端调度差异。

## 留给工程决策的一句话

> "The result I would put in the headline is not that goal helps or hurts. It is that a persistence feature can win most individual trials while making observed average performance worse."

中文版：

> 这件事的标题不应该是"`/goal` 是开关"。真正要摆在标题里的是：**一个让 agent 不停做事的特性，可以一边在大多数单次试验里赢、一边把长期平均表现拖坏**。

放到自己的 agent 选型表里翻译一次：

- 当任务"还有下一轮能改"（写代码、迁移、修 bug），`/goal` 这类持续机制多数情况下是安全的；
- 当任务"决定一个 solver 之后不能再回退"，`/goal` 的边际收益应该是 0，但**方差上限可能放宽很多**——这就是均值变差、胜率看起来还行的来源；
- 在优化类 benchmark 上，**用均值而不是胜率评估持续机制**几乎是唯一不骗自己的方式。

Charles 当年自己花了 1 周手写 C++ 才能交出可比较的解。今天的旗舰模型用 30 分钟就把这个量级的 OR 题交出一个挑不出毛病的最好成绩。接下来的工程问题不是"模型够不够聪明"，而是"我们能不能读懂持续机制背后到底在 commit 哪条路径"。基准表先要把均值和方差分开摆，结论才不会跑偏。

## 学完之后能做什么

- **拆机制**：拿到任意一家 agent 的"持续机制"宣传（autonomous loop、/goal、loop agent、auto-continue），能在 5 分钟内判断它是"评估器外包"还是"主模型自包"，进而推断它对优化类任务的边际收益和方差行为。
- **拆报告**：看到"我们的方法在 N 次试验里胜率 X/Y"这种说法时，能直接追问均值与方差，而不是只盯着胜率拍板。
- **拆自己 benchmark**：给你自己的优化任务写一份"6 对配对、30 分钟预算、最高推理档"的可复现矩阵，知道哪些数字必须摆、哪些可以省。

## 三道自测

1. 你公司给一个新任务挑 agent 时，看到"Anthropic Claude 的 /goal 在 SWE-bench 上胜率领先 70%"。**只看胜率**拍板和**同时看均值**拍板，分别会得出什么不同的结论？
2. 读 Codex CLI 0.144.4 源码中的 goal SQLite 表时，你发现 `update_goal` 被调用 12 次但 `status=satisfied` 始终没出现。**这说明什么？**
3. 一个 532 终端 / 11 hub 的 OR 题，朴素枚举是 `11^532`，文章给的下界 `(532! / 19!) × 11^19 ≈ 10^1223` 似乎并没有变简单。**这是因为下界变松了，还是表达式的实际值反而更小？**

## 进阶路径

- 直接照搬这道题：克隆 [CLIArena](https://github.com/charles-azam/CLIArena) 跑一次 `RUN_ID=article-kiro-YYYYMMDD-clean PHASE=nohint-all ./scripts/run_subscription_article_matrix.sh`，会得到一组自己的对照成绩。
- 横向读：[Charles 的上一篇文章](https://charlesazam.com/blog/kiro-benchmark/)给了 baseline benchmark，本篇的配对在它之上叠加了 `/goal` 维度。
- 纵向读：Anthropic 关于 Claude Code `/goal` 的官方文档，明确写了"评估器看不到文件、只能看 transcript"——这是评估它适用边界的最直接依据。
- 工具对照：想测自己 CLI 的 `/goal` 实现，按 `create_goal / get_goal / update_goal` + SQLite 状态这条线索去源码里找；找不到这套工具的 CLI，往往用的是评估器外挂的实现。
