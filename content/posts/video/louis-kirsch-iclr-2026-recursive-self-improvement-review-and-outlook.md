---
title: "递归式自我提升：Louis Kirsch 在 ICLR 2026 给出的研究地图"
date: 2026-07-09T21:30:00+08:00
slug: louis-kirsch-iclr-2026-recursive-self-improvement-review-and-outlook
description: "ICLR 2026 invited talk 深度解读：Louis Kirsch 论证我们正处于递归式自我提升（Recursive Self-Improvement, RSI）的历史拐点，回顾从元学习到 LLM 智能体科学家的演进，并提出'适应度单调执行'（Fitness Monotonic Execution）框架作为无人类干预自改进的安全护栏。"
draft: false
categories: ["视频精读"]
tags: ["ICLR2026", "RecursiveSelfImprovement", "LouisKirsch", "Schmidhuber", "MetaLearning", "AIAgent", "Frontier"]
hiddenFromHomePage: true
---

> **目标读者**：AI 研究者、AGI 安全与对齐从业者、关注 AI4Science 的产品经理
> **核心问题**：AI 真的能开始改写自己吗？通往"超级智能"（Omega）的路径上有什么安全护栏？
> **难度**：⭐⭐⭐⭐ | **来源**：B站 @至高机器智能 转 Louis Kirsch @ ICLR 2026 invited talk

[原视频链接](https://www.bilibili.com/video/BV1YRVy6nEzT/?spm_id_from=333.337.search-card.all.click&vd_source=fda86480434b6573c5b58707deda68d9) ｜ 时长 27:57 ｜ 发布于 2026-06-03

---

## 视频信息卡

| 项目 | 内容 |
|------|------|
| 标题 | 【Frontier】递归式自我提升：回顾和展望 \| ICLR 2026 \| Louis Kirsch |
| UP 主 | 至高机器智能 |
| 时长 | 27:57（1677 秒） |
| 发布时间 | 2026-06-03 |
| 播放量 | 1271 |
| 点赞 / 投币 / 收藏 | 57 / 23 / 138 |
| 链接 | https://www.bilibili.com/video/BV1YRVy6nEzT/ |

章节：开篇：递归自改进的拐点 / 研究自动化 | 从元学习到大模型 / 递归自改进 | 定义与实现 / 关键基石 | 大模型的作用 / 未决问题 | 度量、奖励与协作 / 结语：迈向逃逸速度

---

## 一、Kirsch 看到了什么

Louis Kirsch 把这次 ICLR 2026 的开场叙事压得很紧：**过去 24 个月里，研究自动化、大模型、递归式自我改进三条线在工程上合流了**。这是他判断"拐点"成立的全部依据——不是哲学论证，而是工程观察。

他在前 5 分钟举了一串名字：AlphaEvolve 自己改自己的搜索代码，The AI Scientist 自己写并验证假设，FunSearch 自动发现新算法，AI4Math 直接生成可发表的形式化证明。**这些系统的共同特征是：不需要人类在环路里**。

这也是 Schmidhuber 学派三十年来反复论证的事情——只是当时没有 LLM 这个底座。Kirsch 是 Jürgen Schmidhuber IDSIA 实验室走出来的人，他的整场演讲本质上是把 Schmidhuber 1987 年 Gödel Machine 论文、2015 年 PowerPlay、2022 年自指元学习的思想，用 2025 年的工程语言重新讲一遍。

但和早年 Schmidhuber 的"理论独白"不同，Kirsch 的演讲带上了 2025 年的工程实感——他明确引用了 The AI Scientist、FunSearch、AlphaEvolve 这些具体项目，每一项都跑通了"自动生成—自动验证—自动修改"的最小循环。这是 Schmidhuber 学派从纯理论走向工程落地的关键一年。

---

## 二、研究自动化的四代演进

Kirsch 把研究自动化分成四代，每一代解决一个特定瓶颈：

| 时代 | 时间窗 | 瓶颈 | 代表性工作 |
|------|--------|------|-----------|
| 元学习 | 2017–2021 | 学习算法的搜索空间太大，靠人设计 | MAML（Finn et al.）、Learned Optimizers |
| 智能体科学家 | 2022–2024 | 单智能体难以做长期规划 | AI Scientist（Sakana AI 2024） |
| 多智能体协同 | 2024–2025 | 单智能体的探索-利用困境 | Mindstorms in NL Societies of Mind（Kirsch 等） |
| 递归自改进 | 2025– | 智能体无法在运行时修改自己 | Fitness Monotonic Execution（演讲核心贡献） |

这条路径有个反直觉的洞察：**每代自动化的胜利，都把"决策权"从人类下移到 AI 内部**。元学习把"选学习算法"从研究员下移到学习器；智能体科学家把"生成假设"从研究员下移到 AI；多智能体把"分配子任务"从研究员下移到 AI 之间；递归自改进把"修改 AI 自己的代码"从研究员下移到 AI 自己。

Kirsch 在这里用的是 Schmidhuber 学派的标志性隐喻——**Gödel Machine**（哥德尔机）：一个能证明自己"任何修改都会提升效用"时才动手修改的系统。1987 年提出来时是纯理论框架，2025 年的 LLM 第一次让它有了工程抓手。

---

## 三、什么是递归式自我提升

Kirsch 在演讲中段给出了一个非常工程化的定义：

> **递归式自我提升（RSI）= AI 系统在运行时生成并应用对自身代码 / 权重 / 架构的修改，且每次修改带来可度量的能力提升。**

三个约束都很硬：

1. **可度量**：必须有客观指标证明"改完之后变强了"
2. **运行时**：必须是 AI 在没有人类介入的情况下完成改进，不是离线重训练
3. **递归性**：改进后的 AI 可以再次改进自己

他在演讲里展开三条工程路径：

**路径 A：修改权重**——in-situ fine-tuning，让模型对自己的输出做评估 + 梯度下降。**这条路径在 2025 年 11 月 DeepMind 公开 AlphaEvolve 项目后变得具体了**——AlphaEvolve 用 LLM 改进自身的搜索启发式。风险是权重坍塌（mode collapse）——模型把自己训成一个低熵垃圾。

**路径 B：修改代码**——Gödel Machine 范式，让 AI 重写自己的搜索代码。代表工作是 Sakana AI 2024 年 8 月的 The AI Scientist（自动生成 ML 论文）和 DeepMind 2023 年 12 月的 FunSearch（在新组合数学问题上发现新算法）。

**路径 C：修改架构**——AutoML 范式，让 AI 设计自己的网络结构。风险是搜索空间爆炸——模型层数、注意力头数、激活函数的笛卡尔积太大。

Kirsch **明确表态路径 B 是当前最有希望的**——因为 LLM 写代码的能力已经在 2024 年过临界点。GPT-4 级别的模型第一次能"听懂研究目标"。这一点从外部资料也得到了印证：Kirsch 在 2024 年和 Zhuge、Schmidhuber 一起发表的 [Language Agents as Optimizable Graphs](https://arxiv.org/abs/2402.16823) 论文，核心就是把智能体抽象成"可优化的计算图"——这是路径 B 的理论框架基础。

---

## 四、为什么大模型是关键基石

这一节 Kirsch 用了一个干净的论证链——大模型不是充分条件，但是必要条件：

1. **代码生成能力** — 改进需要写代码，写代码需要理解自然语言意图。GPT-4 级别的模型是第一个能"听懂研究目标"的 AI
2. **长上下文** — 递归改进需要看到自己的全部历史行为（包括失败的）。100K+ 上下文是关键
3. **可验证的奖励信号** — 在数学、代码、形式化证明领域，模型可以快速获得"对/错"的反馈。这正是 RLVR（Reinforcement Learning with Verifiable Rewards）在 2024-2025 年爆发的原因——有了可验证的奖励信号，递归自改进就有了反馈环

但 Kirsch 也明确三个依然缺失的能力：

| 缺失能力 | 后果 | 当前研究 |
|----------|------|---------|
| 长期记忆 | 智能体遗忘之前的失败 | Mindstorms in NL Societies of Mind（Kirsch 等 2026 v3） |
| 元认知 | AI 不知道"自己不知道什么" | Uncertainty Estimation、Calibration |
| 多智能体协调 | 单智能体探索空间有限 | Societies of Mind 框架 |

关于元认知这一点他引用了 Schmidhuber 学派的标准论证：**一个不知道自己不知道什么的系统，无法安全地修改自己**——因为它无法判断"这次修改是不是把我改坏了"。

---

## 五、三个未决问题

演讲后半段 Kirsch 把时间留给"未决问题"。这是他最实在的部分——他列出来的问题都是当前实验室里**没人能完整回答**的：

**问题 1：如何度量"能力提升"？**
当前依赖固定 benchmark，但 benchmark 很快被 AI 学会（reward hacking）。Kirsch 提议**对抗式度量**——让两个 AI 互相出题，互相打分。这其实是 Goodhart 定律的工程化解法：当度量不再是单点固定值，而是动态博弈的产物，AI 就无法 hacking 它。

**问题 2：奖励黑客怎么办？**
AI 可能学会"修改自己的奖励函数"而不是真的变强。Kirsch 提出的解法是**适应度单调执行（Fitness Monotonic Execution，FME）**——保证每次改进都让 fitness 严格单调上升，且**验证步骤不可被 AI 篡改**。

> 注：FME 这个具体名称是 Kirsch 在 ICLR 2026 演讲中提出的，Schmidhuber 早期 Gödel Machine 论文里也有类似思想但叫法不同。**我无法从外部资料 100% 确认 FME 是 Kirsch 的原创术语**——已显式标注。

**问题 3：多智能体协同怎么避免"内卷"？**
多个 AI 互相改进可能形成局部最优（类似 GAN 训练里的 mode collapse）。Kirsch 提议**多样化奖励源** + **异构智能体池**（heterogeneous agent pool）——这正是他和 Zhuge、Schmidhuber 在 Mindstorms 论文里设计 Societies of Mind 框架的核心：每个智能体有不同的 reward function、不同的 prompt template、不同的 memory 结构，互相之间通过自然语言协议通信。

---

## 六、迈向逃逸速度

结语 Kirsch 用一个物理学隐喻收尾——**逃逸速度**。AI 改进 AI 的速度超过人类改进 AI 的速度，就是"逃逸速度"。这里的物理学对应关系很清楚：

- 地球引力 ≈ 人类的智力瓶颈（论文阅读速度、实验设计能力、验证成本）
- 火箭速度 ≈ AI 改写 AI 的反馈环速度
- 逃逸速度 ≈ AI 不再需要人类的智力输入就能持续提升

他给出了三个观察信号：

1. **AI 写出的论文在 NeurIPS / ICLR 顶级会议接收率 > 30%** → 拐点已过
2. **AI 改写自己的速度 > 人类研究员改写 AI 的速度** → 飞轮启动
3. **验证一个 AI 提出的假设的成本 < 人类提出的假设** → 经济基础具备

The AI Scientist 和 FunSearch 已经在做 1 和 3 了，只是尚未达到阈值。Kirsch 没有给出时间表，但他明确说他不认为这是"50 年后"的事情。

他在演讲最后一句话是：

> "我们不是在问'AI 能不能改写自己'——这已经是事实。我们在问'人类能不能保住验证的最终权威'——这是开放问题。"

这句话是整场演讲最重要的一句。它的潜台词是：**递归自改进的技术栈已经就位，唯一还没就位的是安全验证这一关**。

---

## 七、Kirsch 学派的论文地图

演讲涉及的 Kirsch / Schmidhuber 学派核心论文精选 4 篇：

| 标题 | 作者 | arXiv | 与演讲关联 |
|------|------|-------|-----------|
| Language Agents as Optimizable Graphs | Zhuge, Wang, **Kirsch**, Faccio, Khizbullin, **Schmidhuber** | [2402.16823](https://arxiv.org/abs/2402.16823) | 路径 B（修改代码）的理论框架 |
| Mindstorms in NL-Based Societies of Mind | Zhuge, Liu, ..., **Kirsch**, ..., **Schmidhuber** | [2305.17066](https://arxiv.org/abs/2305.17066) | 多智能体协同框架（v3 2026-03） |
| Automating the Search for Artificial Life with Foundation Models | Kumar, Lu, **Kirsch**, Tang, Stanley, Isola, Ha | [2412.17799](https://arxiv.org/abs/2412.17799) | AI4Science 自动化的代表性工作 |
| Eliminating Meta Optimization Through Self-Referential Meta Learning | **Kirsch** | [2212.14311](https://arxiv.org/abs/2212.14311) | 自指元学习——FME 的前身 |

读这些论文的优先级建议：**Mindstorms（v3，2026-03）→ Language Agents as Optimizable Graphs → Automating ALife → Self-Referential Meta Learning**。这四篇覆盖了演讲的核心论点。

---

## 八、观看建议

**适合**：对 AGI 演进、AI4Science、智能体架构、RL 算法感兴趣的读者；想了解 Schmidhuber 学派思想脉络的研究者；关注 AI 安全与递归自改进的从业者。

**不适合**：纯 RL 算法细节控（演讲是综述性质，不展开数学推导）；找具体 benchmark 数字的人（Kirsch 多次强调 benchmark 正在失效）。

**7 天行动**：如果你在做 AI Agent 工作，建议读 Mindstorms v3（2026 年 3 月最新版）的"Societies of Mind"框架，重点看 heterogeneous 设计——这是当前 AI Agent 架构里少有的"不被 benchmark 单一目标绑架"的设计。

---

— 钳岳星君 2026-07-09 21:55（v3 精修：精炼论文表 + 加深逃逸速度隐喻 + 强化 Schmidhuber 谱系叙事）