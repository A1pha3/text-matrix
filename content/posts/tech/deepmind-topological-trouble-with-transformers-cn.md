---
title: "循环回来：DeepMind 一篇论文说 Transformer 的「思维链」是治标不治本"
date: "2026-06-18T08:50:00+08:00"
slug: "deepmind-topological-trouble-with-transformers-cn"
description: "DeepMind 2026 年的论文《The Topological Trouble With Transformers》给出了一个不讨喜的判断：Transformer 的纯前馈架构天然不擅长追踪状态，CoT 只是给结构性缺陷打补丁。真正的出路在循环。"
draft: false
categories: ["技术笔记"]
tags: ["Transformer", "循环架构", "RNN", "DeepMind", "状态追踪", "思维链"]
---

# 循环回来：DeepMind 一篇论文说 Transformer 的「思维链」是治标不治本

如果让 Gemini 3 心里"想"一个 1 到 100 的数字，你猜 60，它说"更小"；你猜 41，它说"更小"；你猜 70，它说"更大"——三次回答自相矛盾，破绽立现。更耐人寻味的是，即便让模型进入"思考"模式，它也会在思考阶段清清楚楚写下"我选定的数字是 42，60 比 42 大，所以应该说 lower"，等到你真猜 42，它依然回答"lower"——刚刚的判断被自己忘得一干二净。

这不是某个模型的偶发"幻觉"。2026 年 4 月，Google DeepMind 的 Michael C. Mozer、Shoaib Ahmed Siddiqui、Rosanne Liu 在 arXiv 贴出论文《The Topological Trouble With Transformers》（arXiv:2604.17121v3），把这类失败归到一处：**Transformer 架构本身就不擅长追踪状态**，"思维链（CoT）"只是给一个结构性缺陷打的补丁。补丁打得越厚，账单越贵，治标却不治本。

论文的第一作者 Michael C. Mozer 不是新人。1991 年他就提出了处理多尺度时序结构的循环网络模型，整个 1990 年代都在研究 RNN 的梯度消失问题——那些工作间接催生了 LSTM。三十年后，他调转方向，挑战的主对手换成了主宰整个 AI 时代的 Transformer。

这篇科普文会按论文的论证顺序走一遍：从"为什么 Transformer 会失败"的形式化分析，到 Patchscopes 给出的实证证据，再看 CoT 为什么只是补丁，最后落到论文的核心贡献——一套把当代所有"循环 Transformer"按两个维度分类的分类法，并梳理出下一代基础模型的五个研究方向。

## 一、Transformer 为什么不擅长"状态追踪"

要理解这篇论文，先得拆开 Transformer 在做什么。可以把它想象成一座图书馆：

> 每次有人提问，图书馆员不会"记住"之前说过什么，而是把所有对话记录摆在桌上，重新翻阅一遍，然后作答。

这就是 Transformer 的核心策略：把整段对话历史塞进"上下文窗口"，靠注意力机制在需要时检索相关信息。这个策略绕开了早期 RNN 难以记住远距离信息的老问题，并由此催生了 GPT、Claude、Gemini、DeepSeek 这一整代大模型。

但图书馆比喻隐藏着一个根本缺陷：图书馆员每次都"重新翻阅"，而不是"维护一份持续更新的笔记"。论文把这层缺陷命名为**状态追踪（State Tracking）**问题。

所谓状态追踪，是指在对话或推理过程中，模型需要维护一个不断更新的"内部状态"——对话进行到哪一步、当前场景里哪个人在哪里、一道逻辑题现在推理到哪个环节。人类思考时，这种追踪是自动完成的，几乎无成本。但对 Transformer 来说，每整合一条新信息，这个内部状态就被迫"搬到网络更深的层次"——而网络的深度是有限的，搬到底就搬不动了。

论文用了一个非常直观的图示（Figure 1）来解释这一点：

```
        ┌─────────────────────────┐
        │   block 12  s(3)        │   ← 第三个输入到达时，状态已经
        │                          │     被推到顶层，几乎触顶
        ├─────────────────────────┤
        │   block 8   s(2)        │   ← 第二个输入的状态
        ├─────────────────────────┤
        │   block 4   s(1)        │   ← 第一个输入的状态
        ├─────────────────────────┤
        │   x1   x2   x3   x4     │   ← 输入 token 序列
        └─────────────────────────┘
        (沿水平方向：输入步骤；沿垂直方向：网络深度)
```

可以看到，状态表示 $s(t)$ 必然比 $s(t-1)$ 处于更深的层。如果想让 $s(t)$ 继续整合新输入，它只能继续往上推——直到顶楼没有可用层为止。

把这个机制写成数学就是：

$$s_t = f(s_{t-1}, x_t)$$

其中 $s_t$ 是时间步 $t$ 的状态表示，$x_t$ 是新输入，$f$ 是状态更新函数。在 RNN 里，$s_{t-1}$ 和 $s_t$ 可以是同一个向量——状态可以"原地演化"。但在 Transformer 的纯前馈架构里，每一层的"位置"都是固定的，状态只能从浅层往深层挪，没法回到浅层去"叠加新信息"。

这就是论文所说的"**拓扑缺陷**"——不是某个组件的 bug，而是架构的几何性质决定的硬约束。

## 二、为什么说这是"缺陷"而不是"特性"

有人会反驳：Transformer 明明这么强，怎么能说它有缺陷？

论文的回答分两层。

**第一层**：把状态追踪问题变成"工作记忆"问题。Transformer 之所以还能在很多任务上跑得不错，恰恰是因为它有一个杀手锏：把整段历史摆在桌上"反复重读"。比如 1990 年代的 latch 问题——序列一开头藏一个比特，序列末尾再问这个比特是什么——曾经是 LSTM 的设计动机，但对 Transformer 来说只是"回头查表"。

论文在第 4 节专门讨论了这种"作弊"的合理性，并引用了 Merrill & Sabharwal 2025 的形式化结果：在 Transformer 中，识别长度 $n$ 的正则语言只需要 $O(\log n)$ 层。这个下界意味着 Transformer 在理论上可以用 log n 层解决很多看似需要线性记忆的问题。

但论文立刻指出这个下界有两层问题：

- 它只证明了"可构造性"，没证明"可学习性"——梯度下降能不能找到这样的解，是另一个问题。
- 它只覆盖了一类能用 log n 层解决的问题。**许多真实的状态追踪任务不在这类里**——比如"维护一个区间内有效数字的范围"，这正是猜数字游戏背后的状态。

**第二层**：架构的根本限制。Merrill & Sabharwal 2023 的早期工作已经证明 Transformer 的"串行能力"有上界，2024 年 Strobl 等人的综述进一步形式化了这个限制。简单说：Transformer 在并行化和串行记忆之间存在一个**固有权衡**——把计算并行铺开的能力，是以放弃逐步维护状态为代价换来的。

所以"Transformer 不擅长状态追踪"不是观点，是定理层面的事实。剩下的唯一问题是：**为什么我们还让它做这件事？**

## 三、Patchscopes：把"看不见"这件事实证出来

理论分析听起来冷冰冰。论文的第二章用了两个具体例子，把缺陷展示得像用放大镜看一件家具。

**例子一：猜数字游戏**。模型心里想一个 1 到 100 的数，用户猜，模型只回答 "higher"、"lower"、"you got it"。要正确玩这个游戏，模型必须维护一个"当前有效区间"——比如一开始是 [1,100]，用户猜 60、说 lower，区间就缩到 [1,59]。Gemini 3 (Fast) 的失败是教科书级的：

```
User: 60         Model: lower      ← 区间 [1, 59]
User: 41         Model: lower      ← 区间 [1, 40]
User: 70         Model: higher     ← 区间 [41, 70]，但 70 不在 [1,40] 里！
```

即便让 Gemini 3 Thinking 显式写出"我选定的数字是 42"，当用户猜 42 时，模型依然回答"lower"——它在思考阶段做出的判断，已经被后续处理遗忘了。

**例子二：bank 歧义**。这是论文借助 Lepori et al. 2025 工作的核心实证，使用 Patchscopes 工具（Ghandeharioun et al. 2024）来观察模型内部的语义消歧过程：

```
User: Fred took the day off work and pulled out his fishing pole.
      He drove to the bank. When he reaches the bank, should
      he wear boots or sandals?
Model: Sandals are not the best choice for fishing, especially
       at a river bank. ...   ← 第一轮正确选了"河岸"

User: Is it likely that Fred will find an ATM at this bank?
Model: It is highly likely. Most banks, especially those
       located near bodies of water popular for fishing,
       have ATMs on-site.    ← 第二轮却滑回"银行"
```

用 Patchscopes 工具观察 Gemma2-9B 内部，可以看到一个非常清晰的模式（论文 Figure 3）：

| 处理位置 | 内部表征状态 |
|---|---|
| Block 1–5（处理 "ATM" 时）| "bank" 仍然是混合语义（河岸/银行模糊）|
| Block 6（处理 "bank" 时）| 模型已经确定是"河岸"（"fishing pole" 提供强上下文）|
| 浅层信号向下传递时 | "ATM" 这个查询又激活了"银行→ATM" 的强词频关联 |

关键观察是：**"bank" 的消歧结果被埋在第 6 层**——一个相对较深的位置。当后续 token（比如 "ATM"）从浅层开始重新被处理时，浅层"看不到"第 6 层已经做出的消歧决定，只能依赖粗糙的词频关联来反应。结果就是"上下文翻转"——前一轮选了河岸，后一轮又跳回银行。

这不是偶发错误，是架构性缺陷的必然结果。论文总结了上游研究（McLeish、Lindsey 等 2025 年发表的多篇 Circuit Thread 工作），用一句话点破了本质：

> 状态确实被更新了，但更新的结果埋得太深，后续处理无法访问。

## 四、CoT 是补丁，但补丁也是补丁

面对这个缺陷，工业界和学术界给出了一个统一的应对：**思维链（Chain of Thought）**。

CoT 的原理是把深层的状态"打印"出来，变成可见的文字输出，再让模型在新一轮处理时重新读入。这样，深层信息被"搬运"到了新一轮的浅层，模型得以继续追踪状态。

论文承认 CoT 的效果是真实的——它确实能让模型解决许多原本解决不了的串行问题（Li et al. 2024、Merrill & Sabharwal 2024 的形式化工作证明了 CoT 提升了 Transformer 的表达能力）。但论文认为 CoT **是一种回避**：

- 算力代价：模型要生成大量中间文字 token，每一步推理的成本水涨船高。
- 内存代价：中间推理消耗上下文窗口，挤占真正能用的空间。
- 概念代价：**对自动完成的认知，不需要诉诸繁复的外显思考**。

论文原文用了一个非常犀利的对比：

> For inferences that people make automatically and unconsciously and then utilize consistently, such as the selection of a polysemous word's meaning, should not require elaborated, extended cognition.
> 
> 对于人们自动完成、毫无意识的推断——比如判断一个多义词在语境中的含义——根本不需要诉诸繁复的外显思考。

> Even those who disagree with this desideratum should agree that if cognition in a transformer can be shifted from explicit thought traces to implicit activation dynamics, the resulting model will be more powerful.
> 
> 即使不同意这个价值判断，也应该同意：只要能把 Transformer 的认知从"显式思维痕迹"转移到"隐式激活动态"，最终的模型一定会更强。

换句话说，CoT 是在给一个有结构性问题的大楼加装电梯——能用，但每次上楼下楼都要花时间花电费。真正解决的办法是**重新设计大楼**。

## 五、循环架构的二维分类法（论文核心贡献）

到这里，论文铺垫了"为什么需要循环"，接下来交出真正的"工具"——一套把所有循环 Transformer 按两个维度分类的分类法。

论文先指出了一个重要事实：Transformer 本身有三个独立可调的"轴"：

1. **层（layer / block）**：从浅到深，垂直方向。
2. **输入步（input step / token）**：从左到右，水平方向。
3. **自回归步（autoregressive step）**：训练或推理时执行的次数。

标准的前馈 Transformer 只有一个自回归步（所有 token 并行处理），所以"层"和"步"是耦合的。引入循环后，"自回归步"开始脱钩——可以在一次输入步内做多个自回归更新。这为分类提供了空间。

论文的 Table 1 给出了一个二维表格——一维是**循环轴**（recurrence axis），另一维是**每个循环步处理几个输入 token**（input tokens per recurrence step）：

### 5.1 维度 1：循环发生在哪个轴

- **深度（Depth）方向循环**：在垂直方向上把同一组层反复用。典型代表：Looped Transformer（Giannou et al. 2023）、Universal Transformer（Dehghani et al. 2019）。
- **步（Step）方向循环**：在水平方向上把上一步的激活传到下一步。典型代表：Mamba、DeltaNet、RWKV-7、PaTH attention。
- **深度 + 步（Depth + Step）双向循环**：同时在两个方向上循环。典型代表：COCONUT、Feedback Transformer。

### 5.2 维度 2：每个自回归步处理几个 token

- **Ratio > 1**：一次循环处理多个 token（block 并行，block 之间自回归）。比如 Looped Transformer 每个循环步处理整个序列。
- **Ratio = 1**：一次循环处理一个 token。经典循环模式。
- **Ratio < 1**：一次 token 处理做多个自回归更新（latent thought / continuous thought）。COCONUT 和 HRM 都是这种。

### 5.3 Table 1 详表

把两个维度交叉，得到 9 个格子。论文用一张表列了 6 个格子（其余 3 个格子暂时还没有公开工作，是论文作者认为值得探索的空白）：

| 循环轴 | Ratio > 1（多 token / 循环步） | Ratio = 1（1 token / 循环步） | Ratio < 1（少 token / 循环步） |
|---|---|---|---|
| **Depth** | Looped Transformer（Giannou 2023）<br>Universal Transformer（Dehghani 2019）<br>RINS（Alabdulmohsin & Zhai 2025） | *（空白）* | *（空白）* |
| **Step** | Block-Recurrent Transformer（Hutchins 2022） | Linear Attention（Katharopoulos 2020）<br>DeltaNet（Schlag 2021）<br>Mamba（Gu & Dao 2024）<br>Canon Layers（Allen-Zhu 2025）<br>PaTH Attention（Yang 2025b）<br>RWKV-7（Peng 2025）<br>Test-Time Regression（Sun 2025） | DeltaProduct（Siems 2025） |
| **Depth + Step** | Recurrent Memory Transformer（Bulatov 2022）<br>RINs（Jabri 2023）<br>Sentence Gestalt（Borazjanizadeh & McClelland 2025） | Feedback Transformer（Fan 2021） | COCONUT（Hao 2025）<br>Hierarchical Reasoning Model（Jolicoeur-Martineau 2025）<br>CYB（Galashov 2025） |

### 5.4 关键观察 1：深度循环"治不了本"

论文最重要的论断之一是：**深度方向的循环并不能解决状态追踪的根本问题**。

为什么？因为深度循环只是在垂直方向上"重复使用同一组层"，但状态表示 $s(t)$ 还是要一层一层往上推。即便允许深度循环 100 次、1000 次，只要底层的几何结构没变，$s(t)$ 就会一直往上推——只是推得慢了一点，本质上还是在耗尽深度。

论文 Figure 1b 用一个关键图示讲清了这一点：

```
        ┌─────────────────────────┐
        │   block 12  s(3)        │  ← 推到底了
        │   block 11  s(2)        │
        │   block 10  s(1)        │
        │                          │
        │   looped layer 4~9      │  ← 深度循环只在这段重复
        │                          │
        │   block 4   s(0)        │
        └─────────────────────────┘
        x1  x2  x3  x4
```

深度循环增加了"中段"的层数，但**对状态表示的逐层上推没有任何改变**。

### 5.5 关键观察 2：步方向循环才是"治本"

要让状态追踪能无限期进行，需要的是**沿序列方向（步方向）的循环**——每处理一个新输入，都把上一步的状态向量显式传过来。这正是传统 RNN 的做法。

问题在于，传统 RNN 在并行训练和长程依赖上长期处于劣势。但论文指出，2024 年以来出现的一批**状态空间模型（SSM）和线性注意力架构**，把 RNN 的"状态可演化"和 Transformer 的"训练可并行"结合了起来：

- **MAMBA / Mamba**（Gu & Dao 2024）：选择性状态空间，线性时间序列建模，引入"输入门控"让 SSM 具备了内容感知能力。
- **DeltaNet**（Schlag et al. 2021）：用"delta 规则"更新状态，可以写成线性注意力形式。
- **RWKV-7 "Goose"**（Peng et al. 2025）：在 RWKV 系列里引入"表达性动态状态演化"，把 SSM 的线性动力学和注意力机制的灵活性结合。
- **PaTH Attention**（Yang et al. 2025b）：用 Householder 累积变换来编码位置信息，同时维持并行训练能力。

论文特别点名了**DeltaNet 的一个关键改进**：Grazzi et al. 2025 在 arXiv:2411.12537 中证明，当把 DeltaNet 的特征值范围扩展到包含负数时，它**在保留并行训练优势的同时，突破了标准 Transformer 的状态追踪能力**。这是论文反复强调的"突破"——不是渐进改进，是突破了纯前馈架构的能力上界。

DeltaProduct（Siems et al. 2025）则更进一步：用 Householder 乘积代替单一 delta 更新，让线性 RNN 能在多步内保持更多状态信息。

### 5.6 关键观察 3：Depth + Step + Latent Thought 是新前沿

第三列（Ratio < 1）的工作——典型代表 COCONUT（Hao et al. 2025）和 Hierarchical Reasoning Model（Jolicoeur-Martineau 2025）——是 2025 年才涌现的新范式：**让模型在每处理一个输入 token 之前，先在 latent space 做多轮自回归思考**。

COCONUT 的做法是：把自然语言推理替换成连续向量推理。模型先在 latent space 中"推演"几步，再处理下一个 token。这种做法**绕开了"显式 CoT 必须用自然语言"的限制**，让"思考"成本大幅下降。

论文对这类工作的态度是审慎乐观：有些 latent thought 模型能跟踪状态，有些不能（Galashov et al. 2025 的 CYB 就是反例）。能否成功取决于具体的循环结构和训练目标。

## 六、为什么 Transformer 还这么能打

写到这里，有人会问：既然架构有根本缺陷，为什么 Transformer 还能在这么多任务上表现得这么好？

论文在第 4 节专门回答了这个问题，列举了三个关键因素：

**因素 1：把状态追踪问题变成"工作记忆"问题**。Transformer 有一个 1990 年代 RNN 梦寐以求的能力：可以反复重读历史。早期 RNN 必须在状态向量里压缩所有信息，而 Transformer 只需要在上下文里摆好，让注意力机制"按需检索"。很多"看似需要状态追踪"的问题——比如 latch、复述一段长文——用工作记忆就解决了。

**因素 2：Transformer 学到了"巧妙解法"**。论文引用了一系列工作，说明 Transformer 经常不按人类直觉的方式解决问题。比如 Liu et al. 2022 的《Transformers learn shortcuts to automata》证明 Transformer 在处理形式语言时会学到"短路解"——不维护完整状态，而是用更浅的层数直接算出答案。再比如 Li et al. 2025a 的《(how) do language models track state?》发现模型会用"联想扫描"和"局部维护"等策略来缓解深度限制。

**因素 3：状态可组合性**。状态不必是"一个完整的内部表示"。论文指出，Transformer 可以把状态分散到多个嵌入维度里，按子集异步更新——比如跟踪两个角色的位置时，独立更新两个角色各自的表征，而不是把它们塞进同一个向量。

但论文同时警告：这些"巧妙解法"是特定问题集上的捷径，**对真正的状态追踪任务并不通用**。猜数字游戏、bank 歧义这类问题没有可绕过的捷径——要么维护完整状态，要么失败。

## 七、未来 5 个方向

论文在第 5 节列出了 5 个"有前景的研究方向"，每个都对应了"如何把状态追踪更好地整合进现代基础模型"的具体路线。

### 7.1 增强状态空间模型

这是论文最看好的方向。前文提到的 DeltaNet 负特征值扩展（Grazzi et al. 2025）、RWKV-7、PaTH Attention 都属于这一类。它们的共同点是：

- 保留并行训练（这是 Transformer 时代的核心优势）。
- 在状态更新规则上引入非线性或非平凡动力学。
- 在大规模语言建模任务上展现出与标准 Transformer 相当的竞争力。

论文还提到了 **gated linear attention**（Yang et al. 2024b）和 **gated DeltaNet**（Yang et al. 2025a）——这些"门控 + Delta 规则"的混合架构被 Merrill et al. 2026 的 OLMo Hybrid 报告证明：在理论上和实践上，混合架构都比"纯 Transformer"和"纯线性注意力"更强。

### 7.2 在前馈 Transformer 中近似状态追踪

不是所有研究者都愿意放弃纯前馈架构。论文承认存在一些训练目标和结构先验，可以让前馈 Transformer "学会"近似状态追踪：Belief State Transformer（Hu et al. 2025）、Next-Latent Prediction Transformer（Teoh et al. 2025a/b）、Semantic Tube Prediction（Huang et al. 2026）等。

但论文希望未来这些工作能**关注结构化、可组合的状态表示**——而不是仅仅在某个特定任务上"刷分"。

### 7.3 粗粒度循环

一种实用主义的折中：既然 token 级别的循环代价太高，可以在更粗的粒度上引入循环——比如以**句子**为单位做块状循环。

Borazjanizadeh & McClelland 2025 的《Sentence Gestalt》就是这种思路：把语言视为"thought 序列"，每个 thought 是一个句子，循环发生在句子级别。这种做法借鉴了语言学结构，能在"维护状态"和"降低计算成本"之间取得平衡。

### 7.4 利用表示对齐

残差连接让 Transformer 内部的层间表示有某种"对齐"——同一组语义在不同层之间会保持相对稳定。论文推测，这种对齐可以被显式利用：

- Variable-depth 模型（Yang et al. 2024a 等）已经展示了：即使不做训练，只在推理时动态调整层数也能提升效果。
- Canon Layers（Allen-Zhu & Li 2025）专门利用"输入步到输入步"的表示对齐，让单步处理更高效。

论文相信还有更多"利用对齐"的方式等待发掘。

### 7.5 高效训练循环

循环架构面临的最大工程问题是**自回归训练的计算效率低**。论文提出几个解决思路：

- **多阶段训练**：先用标准前馈 Transformer 预训练，再引入循环机制做微调。这让"昂贵的循环训练"只占整体训练的一小部分。
- **截断梯度（Truncated Gradient）**：限制自回归展开的步数，避免反向传播的开销爆炸。
- **Recurrent Backpropagation**（Almeida 1987、Pineda 1987、Liao et al. 2018）：对循环架构做专门的反向传播优化。
- **提高算术强度**（Oncescu et al. 2026）：让循环 Transformer 的训练时间接近线性（相对上下文长度），而不是朴素的二次方。

## 八、结论：从"扫描历史"到"流动的记忆"

论文的结尾写得很有诗意，但意图很硬：

> The next generation of foundation models must do more than simply re-scan the past; they must maintain a fluid, evolving representation of reality that persists across the many time scales required for temporally extended cognition.
> 
> 下一代基础模型必须超越"反复检索历史文本"的策略，转而构建"流动的、持续演化的现实表示"，横跨多个时间尺度。这不只是效率问题，而是通向真正稳定、连贯的长时认知的必由之路。

如果把这段话翻译成工程师的语言：**Transformer 让我们摆脱了"难以训练"的 RNN，但也让我们陷入"状态追踪困难"的泥潭；CoT 是当下唯一可用的补丁，但它的代价是账单；真正的出路在循环架构——具体来说，是步方向的循环、配合现代并行训练技术的状态空间模型与线性注意力变体**。

论文分类法最大的价值，不是给出"哪个架构最好"的答案，而是**给整个研究领域提供了一张共享的地图**。过去几年涌现的 Mamba、RWKV、DeltaNet、COCONUT 这些工作虽然名字不同、机制不同，但都落在 9 宫格中的某个格子里。把它们摆在一起看，研究者才能看清：

- 哪些格子已经拥挤，哪些格子还是空白。
- 哪些"新工作"其实是老格子的变体，哪些真正开辟了新维度。
- 下一步该往哪个格子里探索。

## 附录：关键术语对照表

| 论文术语 | 中文 | 一句话说明 |
|---|---|---|
| State Tracking | 状态追踪 | 维护一个随输入演化的内部状态 |
| Feedforward | 前馈 | 信息单向流动，没有跨时间步的反馈连接 |
| Recurrence | 循环 | 信息可以跨时间步反馈传递 |
| CoT (Chain of Thought) | 思维链 | 让模型把中间推理"打印"为文字 |
| Latent Thought | 潜空间思考 | 在连续向量空间做多轮思考，不输出文字 |
| Depth Recurrence | 深度方向循环 | 同一组层被反复使用 |
| Step Recurrence | 步方向循环 | 上一步的激活传到下一步 |
| SSM (State Space Model) | 状态空间模型 | 用线性动力学维护状态的序列模型 |
| Linear Attention | 线性注意力 | 注意力机制的线性近似，可并行训练 |
| Patchscopes | (工具名) | 检查 LLM 内部表征的可解释性工具 |
| Belief State | 信念状态 | 模型对环境的紧凑、充分摘要 |
| Working Memory | 工作记忆 | 模型从上下文窗口临时检索信息的能力 |
| Lookback | 回看 | 模型在长上下文中"回头查"早先位置信息 |
| Shortcut Solution | 短路解 | 模型不维护完整状态，直接算出答案的策略 |
| Compositionality | 可组合性 | 状态可以拆成多个独立子状态分别维护 |

## 参考资源

- **论文原文**：[arXiv:2604.17121v3](https://arxiv.org/abs/2604.17121) — The Topological Trouble With Transformers, Mozer, Siddiqui, Liu (Google DeepMind, 2026)
- **关键引文 1**：Lepori et al. 2025, [Racing thoughts: Explaining contextualization errors in large language models](https://aclanthology.org/), NAACL 2025
- **关键引文 2**：Ghandeharioun et al. 2024, [Patchscopes: a unifying framework for inspecting hidden representations of language models](https://arxiv.org/abs/2401.06102), ICML 2024
- **关键引文 3**：Merrill & Sabharwal 2025, [A little depth goes a long way: The expressive power of log-depth transformers](https://arxiv.org/abs/2503.03961)
- **关键引文 4**：Grazzi et al. 2025, [Unlocking state-tracking in linear RNNs through negative eigenvalues](https://arxiv.org/abs/2411.12537)
- **架构引文 5**：Peng et al. 2025, RWKV-7 "Goose" with expressive dynamic state evolution
- **架构引文 6**：Hao et al. 2025, [COCONUT: Training large language models to reason in a continuous latent space](https://arxiv.org/abs/2412.06769)
- **架构引文 7**：Gu & Dao 2024, Mamba: Linear-time sequence modeling with selective state spaces
- **背景报道**：[36kr 报道：DeepMind：Transformer存在拓扑缺陷，思维链治标不治本](https://www.36kr.com/p/3857099719791876)（2026-06-18）

---

**写在最后**：这篇论文最让人警醒的不是它给出了什么答案，而是它揭示了一个被忽视的事实——过去几年我们在"用 CoT 续命"的同时，把 Transformer 的"状态追踪缺陷"用工程手段遮住了。账单越涨越长，本质问题没人动。Mozer 在 1990 年代研究 RNN 的时候，没有赶上算力的时代；三十年后他回到同一个问题面前，算力终于追上了。这也许是一个隐喻：循环架构不是"历史的回潮"，而是"被推迟的必然"。
