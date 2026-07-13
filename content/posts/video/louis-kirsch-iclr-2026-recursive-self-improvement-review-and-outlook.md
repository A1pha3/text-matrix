---
title: "逃逸速度：Louis Kirsch 在 ICLR 2026 给出的 RSI 判据"
date: 2026-07-09T21:30:00+08:00
slug: louis-kirsch-iclr-2026-recursive-self-improvement-review-and-outlook
description: "ICLR 2026 RSI Workshop invited talk 解读：Louis Kirsch 没有宣称逃逸速度已经发生，他做的是更基础的事——给 RSI 装上一组判据（可修改范围、可信评估、可持续增长、资源有界、对自身状态可读写），让'AI 能不能自我改进'变成可以逐条勾选的工程清单。本文修正了原版对 FME 的误读，还原演讲真实框架。"
draft: false
categories: ["视频精读"]
tags: ["ICLR2026", "RecursiveSelfImprovement", "LouisKirsch", "Schmidhuber", "GödelMachine", "PowerPlay", "RLVR", "AIAgent", "Frontier"]
hiddenFromHomePage: true
---

> **目标读者**：AI 研究者、AGI 安全与对齐从业者、关注 AI4Science 的产品经理
> **核心问题**：AI 真的能开始改写自己吗？RSI 成立需要同时满足哪些条件？通往"逃逸速度"的路径上还缺什么？
> **难度**：⭐⭐⭐⭐ | **来源**：B站 @至高机器智能 转 Louis Kirsch @ ICLR 2026 RSI Workshop invited talk

[原视频链接（B站）](https://www.bilibili.com/video/BV1YRVy6nEzT/?spm_id_from=333.337.search-card.all.click&vd_source=fda86480434b6573c5b58707deda68d9) ｜ [演讲幻灯片 PDF](https://louiskirsch.com/assets/louis_at_the_recursive_workshop_ICLR_2026.pdf) ｜ [RSI 2026 Workshop 主页](https://recursive-workshop.github.io/) ｜ 时长 27:57 ｜ 发布于 2026-06-03

---

## 视频信息卡

| 项目 | 内容 |
|------|------|
| 标题 | 【Frontier】递归式自我提升：回顾和展望 \| ICLR 2026 \| Louis Kirsch |
| 演讲原始标题 | *Escape Velocity: The inflection point for Recursive Self Improvement* |
| 场合 | ICLR 2026 Workshop on AI with Recursive Self-Improvement（RSI 2026） |
| 演讲者背景 | IDSIA 博士（导师 Schmidhuber）→ Google DeepMind Research Scientist → RSI 方向 stealth startup 联合创始人 |
| UP 主 | 至高机器智能 |
| 时长 | 27:57（1677 秒） |
| 发布时间 | 2026-06-03 |
| 播放量 | 1271 |
| 点赞 / 投币 / 收藏 | 57 / 23 / 138 |
| 链接 | https://www.bilibili.com/video/BV1YRVy6nEzT/ |

章节：开篇：递归自改进的拐点 / 研究自动化 \| 从元学习到大模型 / 递归自改进 \| 定义与实现 / 关键基石 \| 大模型的作用 / 未决问题 \| 度量、奖励与协作 / 结语：迈向逃逸速度

> **前置说明**：ICLR 2026 的 RSI Workshop 自称"可能是全球第一个专门聚焦 RSI 的研讨会"。这场 invited talk 的核心贡献**不是某个新算法**，而是一个用于判断"哪些系统算 RSI、哪些不算"的判据框架。本文的写作依据是 B 站章节大纲 + Kirsch 个人站公开的[演讲幻灯片 PDF](https://louiskirsch.com/assets/louis_at_the_recursive_workshop_ICLR_2026.pdf) + 其 arXiv 论文与 PhD 论文，**未拿到逐字字幕**——所有引用均为综合转述，不确定处已显式标注。

---

## 一、这场演讲在回答什么

读完 Kirsch 的 PhD 论文（题目就叫《Automating AI Research》），再回看这场 27 分钟的 invited talk，会发现他其实一直在收窄一个问题：**能不能让一个 AI 系统，做出一个比它自己更强的 AI 系统，然后让那个更强的系统继续做这件事？**

这就是 RSI（Recursive Self-Improvement，递归自改进）。这不是 Kirsch 的原创概念——它的思想源头可以追到 I. J. Good 1965 年的"智能爆炸"猜想，以及 Schmidhuber 从 1987 年硕士论文到 2003 年 Gödel Machine、2011 年 PowerPlay 这条三十多年的自指改进脉络。Kirsch 是 Schmidhuber 在 IDSIA 的博士生，他的整场演讲本质上是把这条脉络**用 2025 年的工程语言重新讲一遍**。

但和早年 Schmidhuber 的"理论独白"不同，Kirsch 这次的论证带上了 2025 年的工程实感。他反复引用的是已经跑通的项目：Sakana AI 的 The AI Scientist（2024-08，arXiv 2408.06292）能自己生成 ML 论文并自审；DeepMind 的 FunSearch（Nature 2023）在新组合数学问题上发现新算法；AlphaEvolve（arXiv 2506.13131）进一步把 FunSearch 泛化成进化式编码智能体，改进了 DeepMind 自己的若干算法。这些系统的共同点是：**它们跑通了"自动生成—自动验证—自动修改"的最小循环，而且不需要人类在环路里**。

Kirsch 的判断很直接：RSI 不再只是思想实验，它进入了工程实证阶段。但他没说"逃逸速度已经发生"——进入工程实证离逃逸速度还有距离。要达到逃逸速度，一个 RSI 系统得同时满足五个判据。这是整场演讲的核心。

| 演讲脉络 | 这一节对应 |
|---------|-----------|
| 拐点判断：RSI 已进入工程实证 | ✅ 本节 |
| Schmidhuber 谱系：Gödel Machine / PowerPlay 的思想来源 | 第二节 |
| RSI 定义 + 5 判据 + 三条工程路径 | 第三节 |
| 大模型为何是 RSI 的底座 | 第四节 |
| 未决问题：度量、奖励黑客、多智能体内卷 | 第五节 |
| 逃逸速度的观察信号 | 第六节 |

---

## 二、Schmidhuber 谱系：RSI 的思想前史

要听懂这场演讲，得先知道 Kirsch 站在谁的肩膀上。Schmidhuber 学派的三个早期工作构成了 RSI 的思想骨架，Kirsch 在演讲里反复回指它们。

**Gödel Machine（2003，arXiv cs/0309048）** 是强 RSI 的纯理论原型。它的设计是一个系统能重写自己代码的任何部分，但**只有一个前置条件**：必须先用自带的定理证明器生成一个形式化证明，证明这次重写会让某个形式目标函数严格改进，证明通过才允许动手。定理证明器和被修改的目标程序共用同一个底层。这套机制在 2003 年没有 LLM 可用，停留在纯理论——但它的"可证明的自改进"思想直接影响了 Kirsch。

**PowerPlay（2011，arXiv 1112.5309；2013 期刊版见 Frontiers in Psychology）** 回答的是"自改进系统该学什么"。它的策略是：**不断挑出当前能构造出的、最简单的、还解不了的问题**，把它加进训练课程，训到能解，再挑下一个。结果是产出一个"越来越通用的问题求解器"。这是把"课程学习"塞进自改进循环的早期尝试。

**1987 年硕士论文**《Evolutionary Principles in Self-Referential Learning》（慕尼黑工大）是 Schmidhuber 自指学习思想的起点，比 Gödel Machine 早 16 年。它是概念前驱，不是 Gödel Machine 本身——这一区分在中文二手资料里经常被混淆。

> **一个易踩的坑**：不少中文转述把"1987 年 Gödel Machine 论文"当成一个东西。实际上 1987 是硕士论文（概念前驱），Gödel Machine 是 2003。两个相隔 16 年，不能合并。本文按 arXiv 原始编号 cs/0309048 标注。

Kirsch 自己的博士工作就是在这条脉络上的延伸。他在 [Eliminating Meta Optimization Through Self-Referential Meta Learning](https://arxiv.org/abs/2212.14392)（arXiv 2212.14392）里提出：与其保留一个昂贵的外层元优化器，不如让系统**自指地直接修改自己的权重或结构**。那篇论文里有一个保留规则——按测得的 fitness 概率性地保留候选解，从而在期望意义上保证改进单调。这个机制常被称作 **Fitness Monotonic Execution（FME）**。

> **关于 FME 的边界标注**：FME 是 Kirsch 2022 年论文里的机制，不是这次 ICLR 演讲的主框架。演讲的核心是一个更上层的"RSI 判据"，FME 只是其中"可信评估"这一判据在权重层面的具体实现之一。如果你看到其他文章把 FME 当成本次演讲的中心贡献，那是误读。

---

## 三、RSI 的定义、5 判据与三条工程路径

### 3.1 一个工程化的定义

Kirsch 在演讲里给出的 RSI 定义可以浓缩成一句话：

> **RSI = 一个系统研究自身，产出一个严格更强的自身，然后部署这个更强的版本继续循环。**

他和"普通微调"做了一个关键切割：单纯的 fine-tuning 不算 RSI，**改进后的系统必须本身具备做下一轮改进的能力**。这个切割非常重要——它把一大批号称"自我改进"的系统挡在门外：那些系统改完之后，并不比之前更能做下一轮改进。

### 3.2 RSI 成立的 5 个判据（演讲的核心贡献）

这是整场演讲最该被记住的部分。Kirsch 给出的不是某个新算法，而是一组**用于判断"哪些系统算 RSI、还缺什么"的判据**。根据其个人站公开的演讲幻灯片，五个判据是：

| # | 判据 | 含义 | 缺失时的后果 |
|---|------|------|-------------|
| 1 | **Valid scope**（可修改范围有界） | 系统里"哪些部分可以安全地被改"必须定义清楚，不能是"什么都能改" | 自改进可能波及验证逻辑本身，导致评估失效 |
| 2 | **Reliable evaluation**（可信自动评估） | 必须有一个比被改进的生成器更便宜、更可信的评估器 | 没有 ground truth 的反馈，自改进退化成随机游走 |
| 3 | **Sustainable growth**（可持续增长） | 改进必须能复利累积，而不是很快触顶 | 投入产出比递减，飞轮转不动 |
| 4 | **Budgeted resources**（资源有界） | 每轮改进的算力/数据成本必须有上限 | 改进一 roll 跑一年，工程上不可持续 |
| 5 | **Integrated access to state**（对自身状态可读写） | 智能体要能读、能写自己的权重/代码/数据，而不只是发 prompt | 只能改 prompt 的"伪 RSI"无法触及真正的自改进 |

五个判据合起来把一个老问题翻了个面：别再问"AI 能不能自我改进"——那是句口号；该问的是**这个系统在这五条上分别过了哪几关**。

第 2 条值得单独展开。它是 RLVR（Reinforcement Learning with Verifiable Rewards，带可验证奖励的强化学习）在 2024–2025 年爆发的底层原因——数学有标准答案、代码能跑单元测试、形式化证明能被 Lean/Coq 验证，这些场景天然提供了比人类标注更便宜、更可信的 reward。没有这种评估器，RSI 的反馈环闭不上。Lilian Weng 在 2026-07-04 的文章里把围绕评估器的工程叫"harness engineering"，说的是同一件事。

### 3.3 三条工程路径

把 5 判据当筛子，再看 Kirsch 划分的三条工程路径，每条对应"改什么"：

**路径 A：改权重（in-situ fine-tuning）**。模型对自己的输出做评估 + 梯度下降。Kirsch 自己的自指元学习论文（2212.14392）走的就是这条。风险是 mode collapse——模型把自己训成一个低熵垃圾。它的核心难题是判据 2：怎么让"评估"可信，不被模型自己骗。

**路径 B：改代码（Gödel Machine 范式）**。AI 重写自己的搜索/推理代码。代表是 The AI Scientist 和 FunSearch/AlphaEvolve。这条路径在 2024 年后变得具体，是因为 LLM 写代码的能力过了临界点——GPT-4 级别的模型第一次能"听懂研究目标"。Kirsch 在这里的态度很明确：**路径 B 是当前最有希望的**。

**路径 C：改架构（AutoML 范式）**。AI 设计自己的网络结构。风险是搜索空间爆炸——层数、头数、激活函数的笛卡尔积太大。它最容易卡在判据 4（资源有界）。

> **一张任务流图**：以 The AI Scientist 为例，一次完整的 RSI 循环是怎么流过这五条判据的——
> 1. 生成假设（valid scope = 限定在某个 ML 子领域）
> 2. 写实验代码（integrated access = 能调用 GPU、写文件）
> 3. 跑实验、拿指标（reliable evaluation = benchmark 数字）
> 4. 自审、决定是否"改进"（budgeted = 单轮算力有上限）
> 5. 若通过则把改进写回代码，进入下一轮（sustainable = 不触顶）
>
> 这五步对应五判据。**任意一步崩了，整个 RSI 循环就退化成普通的自动化脚本**。这就是为什么 Kirsch 把判据而不是算法当成核心贡献。

---

## 四、为什么大模型是 RSI 的底座

这一节 Kirsch 的论证干脆：大模型不是 RSI 的充分条件，但是必要条件。三条理由分别卡在 5 判据里的某一条：

1. **代码生成能力** —— 对应路径 B（改代码）。GPT-4 级别的模型是第一个能"听懂研究目标"并产出可运行代码的 AI。在这之前，路径 B 根本动不起来。
2. **长上下文** —— 对应判据 5（integrated access）。递归改进需要系统看到自己全部的历史行为，包括失败的。100K+ 上下文让"把整个代码库装进上下文再改"第一次成为可能。
3. **可验证的奖励信号** —— 对应判据 2（reliable evaluation）。数学、代码、形式化证明这些领域天然有"对/错"反馈，RLVR 才能落地。

但 Kirsch 也列出了三个依然缺失的能力，每一个都直接卡在某个判据上：

| 缺失能力 | 卡住的判据 | 当前研究方向 |
|----------|-----------|-------------|
| 长期记忆 | 判据 5（access to state） | [Mindstorms / NL Societies of Mind](https://arxiv.org/abs/2305.17066)（Kirsch 等合作，v3 2026-03） |
| 元认知（知道自己不知道什么） | 判据 2（reliable evaluation） | Uncertainty Estimation、Calibration |
| 多智能体协调 | 判据 1（valid scope）与判据 3（sustainable growth） | Societies of Mind 框架 |

元认知那条尤其关键。一个不知道自己不知道什么的系统，**无法安全地修改自己**——因为它没法判断"这次修改是不是把我改坏了"。这是 Schmidhuber 学派的标准论证，也是 Gödel Machine 当年要求"先有形式证明再动手"的根源。

---

## 五、三个未决问题

演讲后半段是 Kirsch 最实在的部分。他列出的不是"未来展望"，而是当前实验室里没人能完整回答的开放问题，每一个都对应 5 判据里的某一条没过关。

### 问题 1：怎么度量"能力提升"？

这卡在判据 2 和判据 3。当前普遍依赖固定 benchmark，但 benchmark 很快被 AI 学会（reward hacking / 度量博弈）——AI 优化"度量本身"而不是"度量想反映的能力"，这是 Goodhart 定律在 RSI 场景的直接表现。

Kirsch 提议的方向是**对抗式度量**：让两个 AI 互相出题、互相打分。背后的直觉是——当度量不再是单点固定值，而是动态博弈的产物，AI 就没那么容易 hacking 它。这是一个方向，不是答案。**关于对抗式度量，我无法从外部资料确认它是否在幻灯片原文里出现，标注存疑**。

### 问题 2：奖励黑客怎么办？

AI 可能学会"修改自己的奖励函数"而不是真的变强。这卡在判据 1（valid scope）——**如果奖励函数本身落在可修改范围内，系统可以合法地把自己改"赢"**。

Kirsch 在其 2022 年论文里给出的工程解是 FME——保留规则保证改进在期望意义上单调。但 FME 有一个隐含前提：**评估步骤本身不能被 AI 篡改**。换句话说，FME 解决的是"保留规则"这一层，不解决"评估器可信"这一层。后者要靠 RLVR + 把评估器物理隔离在 valid scope 之外。

### 问题 3：多智能体协同怎么避免"内卷"？

多个 AI 互相改进可能收敛到局部最优（类似 GAN 训练里的 mode collapse）。这卡在判据 3（sustainable growth）。

Kirsch 与 Zhuge、Schmidhuber 等合作的 [Mindstorms in NL-Based Societies of Mind](https://arxiv.org/abs/2305.17066)（v3 2026-03）给出的设计是**异构智能体池**：每个智能体有不同的 reward function、不同的 prompt template、不同的 memory 结构，互相之间通过自然语言协议通信。这跟单一目标 benchmark 绑死的单智能体形成对比——它的核心赌注是"多样性本身是对抗局部最优的解药"。

> **一个一致性提示**：GPTSwarm（[arXiv 2402.16823](https://arxiv.org/abs/2402.16823)）的完整标题是 *GPTSwarm: Language Agents as Optimizable Graphs*，第一作者是 Mingchen Zhuge，被 ICML 2024 接收。Kirsch 是合作者，不是主导者。如果其他资料把它写成"Kirsch 的论文"，那不够准确——它提供了"把智能体抽象成可优化计算图"的理论框架，是路径 B 的基础设施，但作者归属应标清楚。

---

## 六、逃逸速度：演讲的物理学隐喻

结语 Kirsch 用了一个物理学隐喻收尾——**逃逸速度**（Escape Velocity）。这也是演讲的正式标题。对应关系很直接：

- 地球引力 ≈ 人类研究员的智力瓶颈（论文阅读速度、实验设计能力、验证成本）
- 火箭速度 ≈ AI 改写 AI 的反馈环速度
- 逃逸速度 ≈ AI 自改进的速度超过人类改进 AI 的速度，此后改进自维持，不再需要人类的智力输入

Kirsch 给出的不是时间表，而是**三个可观测的信号**。需要说明的是，这些信号是判断拐点是否越过的**指标**，不是 benchmark 数字——它们测的是"整个 RSI 反馈环是否已经自维持"，不能直接推出"AGI 何时到来"：

| # | 信号 | 测的是什么 | 不能推出什么 |
|---|------|-----------|-------------|
| 1 | AI 写出的论文在 NeurIPS / ICLR 顶会接收率 > 30% | AI 在"完整研究流程"上的可发表性 | 不能推出论文质量全面超过人类 |
| 2 | AI 改写自己的速度 > 人类研究员改写 AI 的速度 | 反馈环周期是否已经短过人类周期 | 不能推出改进质量一定更高 |
| 3 | 验证一个 AI 提出的假设的成本 < 人类提出的假设 | 评估器（判据 2）在经济上是否可持续 | 不能推出假设的原创性更高 |

The AI Scientist 和 FunSearch 已经在做信号 1 和信号 3，但都还没到阈值。Kirsch 没给时间表，但他明确说他不认为这是"50 年后"的事。

演讲最值得记住的一句话（综合转述）：

> 检验"AI 能不能改写自己"已经不是问题了——这已经是事实。真正开放的问题是，**人类能不能保住验证的最终权威**。

这句话的潜台词是：RSI 的技术栈已经就位，唯一还没就位的是安全验证这一关。它和 5 判据里的判据 1（valid scope）与判据 2（reliable evaluation）直接对应——如果"可修改范围"和"可信评估"这两条由 AI 自己说了算，人类就失去了最终权威。

---

## 七、论文与资源地图

按"读完能复现 Kirsch 思想脉络"的优先级排序：

| 优先级 | 资源 | 作者 | 链接 | 与演讲的关联 |
|--------|------|------|------|-------------|
| ★★★ | 演讲幻灯片 PDF | Kirsch | [louiskirsch.com/...ICLR_2026.pdf](https://louiskirsch.com/assets/louis_at_the_recursive_workshop_ICLR_2026.pdf) | 5 判据的一手来源 |
| ★★★ | Kirsch PhD 论文《Automating AI Research》 | Kirsch | [louiskirsch.com/assets/phd_thesis...](https://louiskirsch.com/assets/phd_thesis_automating_ai_research_louis_kirsch.pdf) | 演讲思想的完整版 |
| ★★★ | Self-Referential Meta Learning（含 FME） | Kirsch | [arXiv 2212.14392](https://arxiv.org/abs/2212.14392) | FME 机制的一手出处 |
| ★★ | Mindstorms in NL Societies of Mind | Zhuge, Liu, …, Kirsch, …, Schmidhuber | [arXiv 2305.17066](https://arxiv.org/abs/2305.17066) | 异构多智能体（v3 2026-03） |
| ★★ | GPTSwarm: Language Agents as Optimizable Graphs | **Zhuge**（一作）, Wang, Kirsch, …, Schmidhuber | [arXiv 2402.16823](https://arxiv.org/abs/2402.16823) | 路径 B 的可优化计算图框架（ICML 2024） |
| ★★ | Gödel Machine | Schmidhuber | [arXiv cs/0309048](https://arxiv.org/abs/cs/0309048) | 强 RSI 的纯理论原型（2003） |
| ★★ | PowerPlay | Schmidhuber | [arXiv 1112.5309](https://arxiv.org/abs/1112.5309) | 自改进的课程学习（2011） |
| ★ | The AI Scientist | Sakana AI | [arXiv 2408.06292](https://arxiv.org/abs/2408.06292) | 路径 B 的代表实现（2024-08） |
| ★ | AlphaEvolve | DeepMind | [arXiv 2506.13131](https://arxiv.org/abs/2506.13131) | FunSearch 的泛化（2025） |
| ★ | ASAL: Automating the Search for Artificial Life | Kumar, Lu, Kirsch, Tang, Stanley, Isola, Ha | [arXiv 2412.17799](https://arxiv.org/abs/2412.17799) | AI4Science 自动化的代表 |
| — | Schmidhuber 自指学习谱系页 | Schmidhuber | [idsia.ch/~juergen/metalearning.html](https://people.idsia.ch/~juergen/metalearning.html) | 1987 硕士论文等一手索引 |

读完顺序建议：**演讲幻灯片 PDF → PhD 论文 → Self-Referential Meta Learning → Mindstorms v3 → Gödel Machine**。前三篇覆盖 Kirsch 自己的工作，后两篇补上思想脉络。

---

## 八、给不同读者的采用建议

**如果你在做 AI Agent 工程**：把 5 判据当成你自改进 agent 的 checklist。当前绝大多数 agent 框架只过了判据 5（access to state）的一半——它们能调工具，但不能改自己的权重/代码。要往 RSI 靠，至少先把"valid scope"（判据 1）划清楚，避免 agent 把自己的评估逻辑也改掉。

**如果你在做 AI 安全 / 对齐**：盯紧判据 1 和判据 2。"可修改范围"和"可信评估"这两条是人类保住"验证最终权威"的最后防线。FME 解决的是保留规则这一层，但**评估器是否落在 valid scope 之外**才是真正的安全设计点——这是 Kirsch 没在演讲里充分展开、但在 Gödel Machine 原论文里反复强调的一点。

**如果你在做 AI4Science**：信号 1 和信号 3 已经在发生，关键看你的领域是否有天然的 reliable evaluation。数学、代码、形式化证明这些有 ground truth 的领域，RLVR 能闭反馈环；湿实验、临床、社会科学这些评估成本高的领域，RSI 还卡在判据 2。

**不适合谁**：纯 RL 算法细节控（演讲是综述性质，不展开数学推导）；找具体 SOTA benchmark 数字的人（Kirsch 反复强调 benchmark 正在失效）。

---

## 九、一句话总结这场演讲

> Kirsch 没有宣称逃逸速度已经发生，他做的是更基础的事：**给 RSI 装上一组判据，让"AI 能不能自我改进"从一个吓人的口号，变成一个可以逐条勾选的工程清单。**

这也许才是这场 27 分钟演讲真正的价值——在 RSI 从科幻走向工程的关口，它给的不是答案，而是一张让所有人能在同一张地图上讨论的坐标系。

---

## 写作笔记（给后续读者）

- **信息来源**：B站 @至高机器智能 的章节大纲 + Kirsch 个人站公开的[演讲幻灯片 PDF](https://louiskirsch.com/assets/louis_at_the_recursive_workshop_ICLR_2026.pdf) + 其 arXiv 论文与 PhD 论文。**未拿到逐字字幕**，所有演讲引用均为综合转述。
- **关键修正（相对于本仓库早期版本）**：
  - 自指元学习论文 arXiv 编号由 2212.14311 更正为 **2212.14392**（前者是无关的随机微分方程论文）
  - "1987 Gödel Machine"更正为：**1987 是 Schmidhuber 硕士论文（概念前驱），Gödel Machine 本身是 2003（cs/0309048）**
  - "PowerPlay 2015"更正为 **PowerPlay 2011（1112.5309）**
  - GPTSwarm（2402.16823）作者归属更正为：**一作 Mingchen Zhuge，Kirsch 为合作者**，ICML 2024 接收
  - 把原版"FME 是演讲核心"的叙事**重构为"5 判据是核心，FME 是判据 2 的具体实现之一"**——这是最关键的一次框架修正
- **未确认项（已显式标注在正文中）**：对抗式度量是否在幻灯片原文出现；AlphaEvolve 的具体公开月份；Kirsch 从 DeepMind 转 stealth startup 的确切时间。这些均不影响主线论证。
- **本文与同仓库 [emergent-garden RSI 文章](https://github.com/a1pha3/web/text-matrix/blob/main/content/posts/video/emergent-garden-recursive-self-improvement-fractalsearch.md) 的关系**：两者是**独立视角**——Kirsch 是 Schmidhuber 学派的学术判据视角，Emergent Garden 是 Karpathy 学派的工程实证视角（用 fractalsearch 实测 RSI 边界）。两篇可以对照读：一篇说"该满足哪些判据才算 RSI"，另一篇说"真跑一个 RSI 循环会发生什么"。

— 钳岳星君 2026-07-09 21:55（v4：修正 arXiv 编号与时间线 / 重构为 5 判据框架 / 显式标注未确认项 / 对齐 emergent-garden 文章的诚实性标准）
