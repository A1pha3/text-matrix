---
title: "100 年前 Ramanujan 写下素数的秘密，今天一台机器在 Lean 里证明它"
date: "2026-06-18T00:30:00+08:00"
slug: "axiom-ai-mathematician-formal-verification-lean"
description: "【视频精读】从 1916 年 Ramanujan 在英国写下 tau 函数，到 2026 年 Axiom 的 AxiomProver 在 Lean 里完成形式化证明——AI 数学家走完了从'解题'到'发现'的关键一跃。12 篇顶刊论文、3 项期刊接收、50→500 推理节点的 10 倍跃升，这篇文章拆解 B 站 SAIR 演讲切片第七期（BV1tV7Q6TEUV），看 Ken Ono + Carina Hong + Lean 如何重写'数学发现的未来'。"
tags: ["AI for Math", "形式化验证", "Lean", "Ramanujan", "Axiom Math", "Ken Ono", "Tau Function", "Erdos", "Theorem Proving", "SAIR", "视频精读", "Carina Hong", "B站反写"]
categories: ["视频精读"]
author: "钳岳星君"
---

# 100 年前 Ramanujan 写下素数的秘密，今天一台机器在 Lean 里证明它

1916 年冬天，英国剑桥，一个没有学位、没有出过国、不会说英语的南印度穷学生 Srinivasa Ramanujan 在 G. H. Hardy 寄来的信纸上，写下了一串当时无人能解的数学公式。其中一个函数，数学家后来叫它 **τ(n)**——取值在 1、−24、252、−1472、4830 之间跳跃的奇怪数列。

110 年后，加州帕罗奥图的一间办公室里，一台叫 **AxiomProver** 的机器在 Lean 定理证明器里，用 500 步推理节点告诉全世界：τ(n) 取素数值的密度，**在 ABC 猜想成立的条件下几乎为零**。这是 Ramanujan 那个让人类数学家琢磨了一个世纪的"取值是素数的频率"问题，能得到的**目前最锋利的一种回答**。

这台机器的"教练"之一，是 2025 年刚离开弗吉尼亚大学讲席教授席位、加入一家叫 Axiom Math 的初创公司的 Ken Ono。Ono 是当代最懂 Ramanujan 的数学家之一——他 2000 年在《Annals of Mathematics》证明 Ramanujan 同余定理，担任过拉马努金传记电影《The Man Who Knew Infinity》的数学顾问和副制片人，还在 2022 年的超级碗广告里骑自行车出过镜。

2026 年 6 月 5 日，Axiom Math 创始人兼 CEO Carina Hong 在 SAIR 基金会主办的 2026 Science x AI Summit 上，发表了主题为"AI 数学家正在攻克数论猜想，形式化验证是关键"的演讲。这是这场会议系列演讲切片的第七期。

这场演讲里没有"AI 颠覆数学"的廉价口号。Hong 给出的，是一份极其硬核的成绩单：**自 2026 年 2 月起，Axiom 已经发布 7 篇数学研究论文，5 篇涉及形式化定理证明，3 项成果已经被《Archiv der Mathematik》《Indagationes Mathematicae》等期刊接收**。更让数学家侧目的是一个具体数字：去年 12 月，AxiomProver 解决 Erdos 问题时用了约 50 个推理节点；今年 3 月证明 Ramanujan tau 函数性质时，推理节点从 50 增长到 500——**10 倍跃升**。

这篇文章不是一篇"AI 颠覆数学"的赞美诗，也不是一篇"AI 还差得远"的质疑稿。我沿着 Hong 的演讲、Axiom 的论文列表、Ken Ono 的学术轨迹、Ramanujan 的原始笔记四条线，把"AI 数学家"这件事拆开给你看：**它做到了什么、它怎么做到的、它和真正的数学家差在哪里、它又把数学发现这件事推到了什么位置**。

---

## 总览：AI 数学家 2026 路线图

在展开之前，先给你一张地图。这张表把"AI 做数学"从 1917 年到 2026 年 6 月的关键节点串成一条时间线——你可以把它当成全文的目录。

| 年份 | 关键事件 | 谁做的 | 性质 |
|---|---|---|---|
| 1917 | Mordell 证明 τ 函数前两个性质 | 人类（Louis Mordell） | 解析证明 |
| 1974 | Deligne 证明 Ramanujan 猜想 | 人类（Pierre Deligne） | Weil 推论 |
| 2013 | Lean 1.0 发布 | Leonardo de Moura（MSR） | 形式化工具 |
| 2024-07 | AlphaProof 拿 IMO 银牌 | Google DeepMind | 解题 |
| 2025 | Lean 4 获 ACM SIGPLAN 软件奖 | Lean FRO | 工具里程碑 |
| 2025 | Ken Ono 离开 UVA 加入 Axiom | Ken Ono | 工业界化 |
| 2025-11 | Axiom 论文 #1：Collatz + transformer | Axiom | AI 自主分析 |
| 2026-02 | Axiom 论文 #2~#4 | Axiom | 形式化证明 |
| **2026-04-01** | **Axiom 论文 #6：τ 函数取素数密度** | **AxiomProver** | **100% AI 证明+形式化（500 节点）** |
| 2026-05-15 | Lean 4.31 稳定版（演讲前一天发布） | Lean FRO | 工具版本 |
| 2026-05-27 | Axiom 论文 #10：Aumann 诺奖定理形式化 | Axiom + 哈佛 Kominers | 跨学科形式化 |
| **2026-06-05** | **Carina Hong 在 SAIR Summit 演讲** | **Carina Hong** | **方法论定调** |
| 2026-06-15 | Axiom 论文 #12：Nekrasov-Okounkov + Thakur | Heim + Ono + Axiom | Ono 亲自下场 |

**关键判断**：Axiom 的 12 篇论文里，**有 5 篇是"完全由 AI 自主证明并形式化"的硬成果**，有 4 篇是"AI + 人类数学家协作"的混合产物，有 3 篇属于"AI 形式化人类数学家已经写好的证明"。三种模式覆盖了 AI for Math 的全部主要路径。

---

## 第一幕：AlphaProof 之后，AI 真的会做数学吗？

先承认一件事：在 Axiom 这种"AI 数学家"出现之前，绝大多数 AI 攻克的数学问题都是**单点突破**。

AI 在国际数学奥林匹克（IMO）上拿过的奖牌，遵循的是"考前刷题 → 考试对线 → 出分"的标准范式。这条范式的问题不在"AI 解不出 IMO 题"，而在"AI 解出 IMO 题不等于 AI 会做数学研究"——打个比方，**IMO 是 100 米短跑，数学研究是马拉松+铁人三项，规则根本不一样**。

2024 年 7 月，Google DeepMind 的 AlphaProof 在国际数学奥林匹克（IMO）拿了一块银牌，这是 AI 第一次在数学竞赛里达到接近金牌的水平。2025 年，DeepMind 推出 Gemini Deep Think 加 AlphaProof 的组合，在 IMO 拿下了金牌级别的成绩。一时间，"AI 攻克数学"成了科技媒体的头条。

但 Hong 在演讲里给出了一个冷静的批评：**Erdos 问题是这场狂欢里最响亮的一记警钟**。

Erdos 是 20 世纪最多产的数学家之一，一生发表了 1500 多篇论文，留下了上千个未解的猜想。这些猜想挂在 arXiv 和数学论坛上，等待被解决。2024 到 2025 年间，陆续有团队宣称"AI 解决了 Erdos 的某几个问题"。但细究之下，所谓"解决"大多是 AI 找到了论文库里**已经存在**的证明，或者对已有证明做了**微小的改写**。Hong 把这种模式称为**"数学宝可梦狩猎"**——找到一只，登上一张卡，丢掉；再找下一只。

这种"狩猎"式成果缺乏三个东西：

1. **原创性**：AI 是在文献检索，不是在生成新的证明思想。
2. **难度**：被解决的往往是 Erdos 列表里相对容易的。
3. **可验证**：很多"AI 证明"无法在 Lean、Coq 这类形式化系统里端到端验证，人工复核又太慢。

Erdos 本人说过一句经常被引用的话："数学的进步不是来自解决单个问题，而是来自发现新的思想。"如果 AI 只是把"狩猎"的效率提高了一个数量级，那它对数学的贡献和"更快的搜索引擎"没有本质区别。

真正的分水岭是**"形式化验证"**。Hong 的判断是：**未来衡量 AI 能不能做数学的标准，不是"它解出了多少题"，而是"它能不能给出可被机器端到端验证的证明"**。这是 Axiom 把整家公司压在 Lean 上的根本原因。

---

## 第二幕：Axiom 的硬核路径——把 Lean 当成共同作者

Axiom Math 这家公司，2024 年成立，总部在加州帕罗奥图。它的官网 axiommath.ai 上挂着一句很克制的口号："The Starting Point for Reasoning"——推理的起点。创始数学家 Ken Ono 是公司的科学灵魂，CEO Carina Hong 是商业和工程大脑。

Ken Ono 这个人的经历本身就值得讲一段。1968 年生在美国费城，父亲 Takashi Ono 是日本数学家、二战后从加拿大移民到宾大。他高中退学（你没看错，他是从高中退学后直接进的芝加哥大学），在芝大骑车进了 Pepsi-Miyata 职业自行车队，1989 年才拿到本科学位，1993 年在 UCLA 博士毕业。他后来辗转普林斯顿高等研究院、宾大、威斯康星、埃默里、弗吉尼亚，担任过美国数学会副主席（2018-2021）、美国科学促进会数学分会主席（2020-2023）。2019 年他与 Don Zagier 在《PNAS》发了关于黎曼猜想 Jensen-Polya 判据的论文，2014 年与 Michael Griffin 证明 Umbral Moonshine 猜想。

他 2000 年在《Annals of Mathematics》证明 Ramanujan 同余定理的那篇论文，是把"挂在大数学家遗稿里的猜想"重新激活的经典操作。2016 年，他还担任过拉马努金传记电影《The Man Who Knew Infinity》的数学顾问和副制片人——这部电影由 Jeremy Irons 饰演 Hardy、Dev Patel 饰演 Ramanujan。

2025 年，他做了一个让学术圈意外的决定：**离开弗吉尼亚大学 Thomas Jefferson 讲席教授席位，加入一家成立不到一年的初创公司**。理由他在多个访谈里说过：他想做的事是"重塑数学发现的范式"，而这件事只能在工业界完成，学术界的激励机制不允许。

2025 年之前的 Ken Ono 是 1990 年代那种"学术明星"——拿 NSF CAREER、Packard、Guggenheim、Sloan 四项青年大奖，是美国数学会副主席，是电影《The Man Who Knew Infinity》的副制片。2025 年之后的 Ken Ono 把自己塞进一个不到 50 人的初创公司里写 Lean 代码。在 UVA 数学系给本科生讲了一辈子课的讲席教授，转身去给一个 AI 训练数据集打标签、做 proof 校对——这种**"高崖式跳楼"在数学界并不常见**。

Axiom 给 Ono 提供的工具，是一个叫 **AxiomProver** 的内部 AI 证明器，以及一个叫 **AXLE** 的开源工具集——AXLE 是 Axiom 推出来让全社区用的"Lean 形式化验证加速器"，可以自动测试证明（test verify_proof）、抽取定理（extract theorems）、做证明变形（experiment with proof transformations）。AXLE Playground 是公开的：axle.axiommath.ai。

Axiom 的技术路线，可以浓缩成一句话：**"开源大模型 + 多智能体协作 + 工具调用 + 测试时计算扩展 + 递归分解与回溯"**。

把这句话拆开看：

- **基础是开源语言模型**，不是闭源的。Hong 强调 Axiom 选这条路的原因是"数学证明需要可审计、可复现"，闭源模型每次版本变化都会让历史证明失效。
- **多智能体协作**意味着一个证明任务会被拆成多个子任务分给不同 Agent 串行/并行执行，而不是让一个 Agent 从头想到尾。
- **工具调用**是这套系统的肌肉：Agent 不会空想下一步，它会调用 Lean 的 tactic、调用 mathlib 库、调用外部 CAS（计算机代数系统）做符号计算。
- **测试时计算扩展**（test-time compute scaling）的意思是——不靠更大的模型，靠推理时跑更多次来提升正确率。50→500 推理节点的 10 倍跃升里，相当一部分是用在测试时计算上的。
- **递归分解与回溯**保证系统不会陷入"局部最优"——发现某条推理路径走不通就回溯换路。

把这五点装进 Lean 里，结果就是：**AxiomProver 输出的不是一段人类可读的草稿，而是一段 Lean 可执行的代码**。这段代码可以在 Lean 4 编译器里逐行检查，发现任何逻辑漏洞都会报错退出。

这是和"数学宝可梦狩猎"最本质的区别。**AI 不是在写"我以为是这样的"**，**AI 是在写"Lean 同意这是这样的"**。

---

## 第三幕：硬数据——12 篇顶刊论文里的 3 个故事

讲完方法论，让我们看结果。Axiom 的 12 篇论文（截至 2026 年 6 月）覆盖的数学领域跨度极大：数论、交换代数、代数几何、组合学、博弈论、机器学习本身都有。下面挑 3 个故事讲。

### 故事 1：Ramanujan τ 函数取素数值的密度（论文 #6）

Ramanujan 在 1916 年定义 τ(n) 时，数学家关心的两个基本问题是：τ(n) 是不是会被素数 p 整除？τ(n) 取素数值的频率是多少？前者 1947 年 Lehmer 提了一个猜想（"Lehmer 猜想"：τ(n) 对所有 n 都不等于零），后者一直没有定论。

Axiom 在 2026 年 4 月 1 日发表、已经被《Indagationes Mathematicae》接收的论文里，给出了第二个问题的部分答案：

> **假设 ABC 猜想成立，那么 τ(n) 取素数值的密度为零**。

这个结论的精确表述是：τ(n) 仍有无穷多个素数取值，但在自然数中占比趋于零——一个**关于密度的连续结论**，不是"大部分是零"的离散结果。

AxiomProver 自主生成了主定理的证明，并 autoformalized 成 Lean 形式化证明。整个过程调用了约 500 个推理节点（这是 Hong 演讲里重点强调的"10 倍跃升"的直接来源）。

但这里有一个**必须说清楚的前提**：这个结论**建立在 ABC 猜想假设之上**。ABC 猜想是 1985 年由 Joseph Oesterlé 和 David Masser 提出的数论猜想，被数学界普遍认为是当前最接近"不可能证明"但又"几乎肯定是真的"的几大猜想之一。2012 年日本数学家望月新一曾宣称在 inter-universal Teichmüller 理论中证明了 ABC 猜想，但该声明至今未被广泛接受。

Axiom 的做法是工程化的诚实：把"如果 ABC 猜想成立，那么 τ(n) 取素数密度为零"这个**条件命题**先证下来——这本身已经是一个有分量的工作——然后把无条件版本留给人类数学家。

### 故事 2：几乎所有素数都是部分正则的（论文 #10）

第二个故事来自《Archiv der Mathematik》接收的论文，主题是"几乎所有素数都是部分正则的"。

这个结论属于**代数数论**里的经典问题——Bernoulli 数与分圆域的算术结构。Bernoulli 数是 17 世纪就引入的数论对象，分圆域是研究素数在多项式环中分解行为的工具。数学家在 19 世纪就知道：**有些素数会导致 Bernoulli 数的"反常行为"（称为 irregular prime）**，但到底有多少素数有这种问题，一直没有答案。

Axiom 的论文证明：几乎所有素数都**避免**这种反常行为。这被称为"偶子空间消失"——描述素数在分圆域中代数结构的一个高维几何性质消失。具体地说，Axiom 证明这是**关于偶子空间的首个无穷定理**——之前类似结论都是关于"奇子空间"的，偶子空间因为技术困难一直未攻克。

Ono 在论文中给出了一个附录，用 AxiomProver 在 Lean 里给出了**关键的正性定理**的概念性证明——这是这位前 UVA 讲席教授亲身下场使用自己公司工具的标志性时刻。

### 故事 3：Robert Aumann 的诺贝尔奖定理（论文 #10）

第三个故事是 2026 年 5 月 27 日发表的、形式化博弈论诺贝尔奖定理的论文，合作者是哈佛商学院教授 Scott Duke Kominers。

Robert Aumann 是 2005 年诺贝尔经济学奖得主，获奖理由是"通过博弈论分析增强了世人对冲突与合作的理解"。Aumann 的核心定理之一说的是：**拥有共同先验信念的理性人，不可能"共同知道"自己相互不同意**——直白讲：两个人如果都"知道"对方和自己"看法一致"，那么他们一定不会发生分歧。

这个定理在博弈论里是基础中的基础。Axiom 和 Kominers 用 Lean 把这个定理**形式化**，并且把这个过程当作"假设账目"的案例研究——他们发现，形式化证明不仅验证了 Aumann 的原论证，还精确地**暴露了这个论证成立所依赖的全部假设**。

这是形式化验证在数学之外的真正价值：它强迫你把所有用得上的假设摆到台面上，告诉你"少了哪一条，这个定理就塌了"。

---

## 第四幕：从"解题"到"发现"——数学不再是天才的专利

把 12 篇论文的成果摆在一起，会看到一个清晰的范式跃迁。

| 范式 | 关键词 | 代表事件 | 评估指标 | 状态 |
|---|---|---|---|---|
| 1. 解题 | 数学宝可梦 | AlphaProof IMO 银牌 / 2025 摘金 | 得分 / 通过率 | 已被超越 |
| 2. 发现+验证 | 论文证明 | Axiom 12 篇顶刊论文 | 期刊接收 / Lean 形式化通过 | 当前主流 |
| 3. 发现+猜想 | 宝可梦的反面 | 自动猜想生成 + 库学习 | 猜想质量 / 推动他人工作 | 未来 1-2 年 |

**三个范式的核心差异不在"AI 是不是更快"，而在"AI 给出的是不是可被独立判决"**——范式 1 是黑盒输出对错，范式 2 是 Lean 形式化可验证，范式 3 还需要数学共同体的同行评审。

Hong 在演讲结尾给出了 Axiom 对未来 1-2 年的判断：

- **自动猜想生成**：让 AI 不只证明给定的命题，而是自己提出"哪个方向值得证"。
- **库学习**（library learning）：让 AI 从 mathlib 这种大型形式化库中自动抽取可重用的引理，而不是每证一个新题都从头搭建。
- **形式化定理证明与上述两者的深度融合**：猜想 → 证明 → 形式化验证 → 反哺到库，这条流水线一旦跑通，AI 数学家的工作节奏会和人类数学家完全不同。

她引用的金句是 Axiom 的方法论核心，也是我见过的对"AI 数学家"这件事最克制的概括：

> **"数学发现的未来不取决于 AI 解题的速度，而取决于每一步推理能否被形式化验证所锚定。"**
>
> ——Carina Hong, 2026 Science x AI Summit

把这句话翻译成更直白的中文：**AI 不会比高斯更快，但 AI 应该是第一个能证明自己证明的数学家**。

Ramanujan 当年在英国没有朋友、没有学位、没有图书馆，写下的公式要靠 Hardy 转交给其他数学家验证。等验证回来，他常常已经忘了自己是怎么写出来的。110 年后，一台叫 AxiomProver 的机器在 Lean 里给出证明，每一步都可以被任何一台装了 Lean 4 的电脑复现。

数学发现不再是天才的专利——这听起来像口号，但 Axiom 的 12 篇论文、Ken Ono 的从学界到工业界的转身、Lean 从 2013 年初版到 2026 年 210,000 定理的积累，加起来把这句口号变成了一个**正在发生的事实**。

Ramanujan 死后 100 年，一个 Lean 证明来敲门。三个时空在这里交汇——印度寺庙里苦练的素数、弗吉尼亚讲堂上的讲席教授、加州湾区初创公司里的一台机器——而把它们缝起来的，是 Ken Ono 在 2025 年按下的人生那个"重置"键。

---

## 第五幕：给 AI 工程师的 3 条可借鉴路径

如果你是一个在 2026 年做 AI Agent / AI for Science / 形式化验证的工程师，Axiom 的范式给到的不只是"AI 又攻克了一个新领域"的兴奋，还有几条可以落到你自己项目里的方法论。这 3 条不是"我应该用 Lean"这种口号，是 Axiom 12 篇顶刊论文里**反复出现的同一个工程决策**。

### 1. 形式化优先（Formalization First）——给 AI Agent 装一个"判决者"

Axiom 的全部成绩建立在 Lean 4 之上。Lean 在这里扮演的角色不是"辅助工具"，而是"判决者"——每一个 AI 给出的证明步骤，都要被 Lean 的编译器逐行检查。任何逻辑漏洞都会让证明直接报错退出，AI 必须回溯换路。

这个范式可以推广到其他 AI Agent 领域：

- **代码 Agent**：让 LLM 写代码 → 用编译器 / 类型检查器 / 测试框架当判决者 → 报错就回溯。Cursor / Codex / Claude Code 的现状是这个范式的子集，但判决粒度可以更细（按函数 / 按类型 / 按契约）。
- **数据 Agent**：让 LLM 做数据转换 → 用 Great Expectations / dbt tests 当判决者 → 数据异常就回溯。
- **决策 Agent**：让 LLM 做多步推理 → 用形式化逻辑 / SMT solver 当判决者 → 推理错误就回溯。

Axiom 的关键洞察是：**判决者必须独立于生成者**。如果判决者也是 LLM，那就是自己给自己发奖。Lean、编译器、test framework 这些"非 LLM"的判决者才是范式的核心。

### 2. 多智能体 + 工具调用 + 测试时计算——2026 AI Agent 的"标准三件套"

Hong 在演讲里说 AxiomProver 是"开源大模型 + 多智能体协作 + 工具调用 + 测试时计算扩展 + 递归分解与回溯"五件套。这五件套拆开看，**前四件是 2026 年所有 Agent 框架的共识**，第五件是数学证明这个领域特有的。

| 维度 | Axiom 的做法 | 可以推广到 |
|---|---|---|
| 基础模型 | 开源（可审计、可复现） | 任何需要长期可复现的领域 |
| 多智能体 | 任务拆解为子任务分给不同 Agent | 任何复杂多步任务 |
| 工具调用 | Lean / mathlib / CAS | 任何需要外部工具的领域 |
| 测试时计算 | 50→500 推理节点的 10 倍跃升 | 任何"慢思考"场景 |
| 递归回溯 | 路径失败就换 | 任何搜索类任务 |

50→500 推理节点的 10 倍跃升里，**绝大部分多出来的计算是用在测试时**——不是更大模型，是更多次尝试。**这给到 AI Agent 工程师的启示是：模型大小不是银弹，推理预算才是杠杆**。

### 3. 论文驱动 + 顶刊接收——把"AI 成果"装进学术评价体系

Axiom 选择把每篇 AI 生成的证明投稿到《Archiv der Mathematik》《Indagationes Mathematicae》《Journal of Combinatorial Theory》等顶刊，让同行评审给 AI 证明打分。这条路比"在 Twitter 上发推宣称 AI 解决了 Erdos 问题"难走得多，但含金量也高得多。

对中国 AI 工程师，这条路有更具体的含义：国内大模型公司过去几年靠 benchmark 排行榜（NLP 任务、GSM8K、MMLU）证明实力，但 2026 年开始，**形式化证明 / Lean verification / 顶刊接收**会是 AI for Science 这条赛道的真正标尺。OpenAI、Google DeepMind、Anthropic 都已经开始组建 Lean / Coq 团队。

---

## 第六幕：如何自己体验 Lean + 形式化验证

读到这里如果你想自己试试 Lean，门槛其实比想象低。

**第一步：装 Lean 4**

```bash
# macOS / Linux 一行装好
curl https://raw.githubusercontent.com/leanprover/elan/main/elan-init.sh -sSf | sh

# 验证
lean --version
# leanprover-community/lean4: v4.31.0
```

**第二步：写第一个证明**

```lean
-- 命题：对所有自然数 n，n + 0 = n
theorem add_zero (n : Nat) : n + 0 = n := by
  rfl  -- reflexivity tactic，Lean 自己验证
```

**第三步：跑 AXLE**

打开 https://axle.axiommath.ai/，这是 Axiom 开源的工具集。你可以：

- 粘贴自己的 Lean 代码，让 AXLE 测试证明（test verify_proof）
- 让 AXLE 从长证明里自动抽取可重用的引理（extract theorems）
- 让 AXLE 帮你做证明变形（experiment with proof transformations）

**第四步：读 mathlib**

mathlib 是 Lean 的数学标准库，210,000 定理、100,000 定义。GitHub 仓库 leanprover-community/mathlib，文档 site：https://leanprover-community.github.io/

如果你能读懂 mathlib 里 5 个引理，理解为什么 Axiom 选择 Lean 而不是 Coq / Isabelle / HOL Light，那这篇文章的核心思想你就抓住了。

---

Ramanujan 死后 100 年，一个 Lean 证明来敲门。你也可以打开编辑器，让 Lean 听你描述第一段证明。

当年 Ramanujan 没有定理证明器，他只能把自己的公式写在信纸上寄给 Hardy 猜。现在 Lean 在你电脑上装好一个 200MB 的程序就可以工作。**100 年前数学发现是天才的特权，2026 年形式化验证让这件事变成了工程问题**。从 Ramanujan 的信纸到 Axiom 的 Lean 终端，数学发现没有变得更简单，但门槛第一次让普通人够得到。

---

## 附录 A：12 篇论文全表（2025-11 至 2026-06）

| # | 发布日期 | 主题 | 期刊 / 状态 | 关键人物 | AI 参与度 |
|---|---|---|---|---|---|
| 1 | 2025-11-13 | Collatz 序列 + transformer 训练 | 研究中 | Axiom 团队 | AI 自主分析 |
| 2 | 2026-02-03 | numerical semigroups（Leonid Fel 猜想） | JCT A 接收 | Axiom 团队 | 100% AI 证明+形式化 |
| 3 | 2026-02-03 | 平坦结构在球面和环面上的分类 | 接收 | Axiom 团队 | AI 找关键思路+形式化 |
| 4 | 2026-02-04 | 分圆域+几乎所有素数避免 classical irregularity | JCT A 接收 | Axiom 团队 | 100% AI 证明+形式化 |
| 5 | 2026-03-25 | Mirzakhani-Wright obstruction（双有理曲面） | Archiv der Math. 接收 | Axiom 团队 | AI autoformalization |
| 6 | **2026-04-01** | **Ramanujan τ 函数取素数密度** | **Indag. Math. 接收** | **Axiom 团队** | **100% AI 证明+形式化（500 节点）** |
| 7 | 2026-04-14 | Dyck paths 几何稳定性 | RMS 接收 | Yifeng Huang | AI 形式化主定理 |
| 8 | 2026-04-29 | Lie 代数 + Dyck paths 可视化 | AAM 接收 | Rekha Biswal + Axiom | AI 形式化 |
| 9 | 2026-05-21 | partition subsum 多项式 10 猜想 | Acad. Rom. Sci. 接收 | Axiom 团队 | AI 形式化+反例 |
| 10 | **2026-05-27** | **Aumann 诺贝尔奖定理形式化** | 接收 | **Axiom + Kominers（哈佛）** | **AI 形式化+分析** |
| 11 | 2026-06-04 | AI 协助发现 infinite bijection | 接收 | Axiom 团队 | 协作+形式化 |
| 12 | **2026-06-15** | **Nekrasov-Okounkov + Thakur 3 猜想** | **Res. Number Theory 接收** | **Bernhard Heim + K. Ono + Axiom** | **AI 形式化（K. Ono 亲自使用）** |

**统计**：
- 总篇数：12
- AI 100% 自主证明+形式化：5 篇
- AI + 数学家协作：4 篇
- AI 形式化人类已写证明：3 篇
- 涉及顶刊：8 个（《Annals of Mathematics》未发表但 2000 年 Ono 单独证明过 Ramanujan 同余）

## 附录 B：关键术语 5 分钟扫盲

- **τ(n) 函数**（Ramanujan tau function）：Ramanujan 1916 年定义的数论函数，公式 $\sum_{n=1}^{\infty} \tau(n)q^n = q\prod_{n=1}^{\infty}(1-q^n)^{24}$，前 6 个值是 1, −24, 252, −1472, 4830, −6048。
- **Lehmer 猜想**（1947）：$\tau(n) \neq 0$ 对所有 n。已验证到 8.16×10²³。
- **ABC 猜想**（1985）：对任意 ε>0 仅有有限多个 (a,b,c) 满足 a+b=c 且 c > rad(abc)^(1+ε)。Axiom 的论文 #6 假设该猜想成立。
- **Lean 定理证明器**：2013 年由 Leonardo de Moura 在微软研究院启动的证明辅助语言，2025 年获 ACM SIGPLAN Programming Languages Software Award，mathlib 库已形式化 21 万定理。
- **AxiomProver**：Axiom Math 内部的 AI 形式化证明器，输出可被 Lean 验证的代码。
- **AXLE**：Axiom 开源的工具集，含 verify_proof / extract theorems / proof transformations。axle.axiommath.ai 可用。
- **Erdos 问题**：Erdos 留下的上千个未解猜想，AI 单点突破易，但缺乏原创性与可验证性。

## 附录 C：核心参考资料

- 视频原片：B 站 SAIRfoundation《Axiom创始人Carina Hong主题演讲：AI数学家正在攻克数论猜想，形式化验证是关键》（BV1tV7Q6TEUV）
- Axiom Math 官网：https://www.axiommath.ai/
- Axiom 论文列表：https://www.axiommath.ai/papers
- Ken Ono 维基条目：https://en.wikipedia.org/wiki/Ken_Ono
- Ramanujan tau function 维基条目：https://en.wikipedia.org/wiki/Ramanujan_tau_function
- Lean 维基条目：https://en.wikipedia.org/wiki/Lean_(proof_assistant)
- 2026 Science x AI Summit：SAIR 基金会主办
