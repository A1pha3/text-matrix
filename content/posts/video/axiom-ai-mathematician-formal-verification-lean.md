---
title: "100 年前 Ramanujan 写下素数的秘密，今天一台机器在 Lean 里证明它"
date: "2026-06-18T00:30:00+08:00"
lastmod: "2026-09-07T12:00:00+08:00"
slug: "axiom-ai-mathematician-formal-verification-lean"
source_key: "bv:BV1tV7Q6TEUV"
description: "【视频精读】从 1916 年 Ramanujan 在剑桥定义 tau 函数，到 2026 年 AxiomProver 在 Lean 里完成形式化证明。本文基于 SAIR 演讲切片第七期（BV1tV7Q6TEUV），逐项核实 Carina Hong 演讲的核心事实：7 篇论文、3 项期刊接收、50 到 500 个推理节点，以及 tau 函数、部分正则素数、k-微分奇偶三个能对回 arXiv 的故事。"
tags: ["视频精读", "B站反写"]
categories: ["视频精读"]
author: "钳岳星君"
---

# 100 年前 Ramanujan 写下素数的秘密，今天一台机器在 Lean 里证明它

1916 年，到剑桥不过两年的 Srinivasa Ramanujan 发表了论文《On certain arithmetical functions》，里面定义了一个系数函数，后来被数学家称为 **τ(n)**——取值在 1、−24、252、−1472、4830 之间跳跃的奇怪数列。它身上挂着一串难题：1917 年 Mordell 证出前两个性质，第三个性质（|τ(n)| 的上界）要等到 1974 年 Deligne 才解决，而 τ(n) 到底以多大频率取到素数值，直到 2026 年都没有像样的答案。

110 年后，加州帕罗奥图，一家叫 **Axiom Math** 的公司用他们的 **AxiomProver** 给出了目前最硬的一个回答：**假设 ABC 猜想成立，τ(n) 的绝对值取到素数的那些素数，在全体素数中的密度为零**。证明的主引擎由系统从自然语言命题出发自动生成，并在 Lean 定理证明器里完成形式化——按公司创始人 Carina Hong 在演讲里的说法，整个过程动用了约 500 个推理节点，是半年前解决 Erdos 问题时（约 50 个）的 10 倍。

这家公司的科学核心，是 2025 年离开弗吉尼亚大学讲席教授席位加入的 Ken Ono——当代最懂 Ramanujan 的数学家之一，传记电影《The Man Who Knew Infinity》的数学顾问兼联合制片人。

2026 年 6 月上旬，Hong 在 SAIR 基金会主办的 2026 Science x AI Summit 上发表主题演讲；切片视频于 6 月 6 日由 B 站 UP 主 SAIRfoundation 发布（15 分钟，第七期）。成绩单没有"AI 颠覆数学"的口号：**自 2026 年 2 月起，Axiom 已发布 7 篇数学研究论文，其中 5 篇涉及形式化定理证明，3 项成果已被《Mathematische Nachrichten》《Indagationes Mathematicae》《Archiv der Mathematik》接收**。

本文沿着 Hong 的演讲、Axiom 的论文（能对回 arXiv 的部分逐篇核对）、Ken Ono 的学术轨迹、Ramanujan 的原始问题四条线展开：它做到了什么、怎么做到的、和真正的数学研究差在哪里、又把"数学发现"这件事推到了什么位置。

---

## 总览：AI 数学家 2026 路线图

下表把"AI 做数学"从 1917 年到 2026 年 6 月的关键节点串成一条时间线，可作为全文目录。

| 年份 | 关键事件 | 谁做的 | 性质 |
|---|---|---|---|
| 1917 | Mordell 证明 τ 函数的乘法性质等前两个性质 | Louis Mordell | 解析证明 |
| 1974 | Deligne 证明 Ramanujan 猜想（|τ(n)| 的界） | Pierre Deligne | Weil 猜想推论 |
| 2013 | Lean 首次发布 | Leonardo de Moura（微软研究院） | 形式化工具 |
| 2024-07 | AlphaProof 与 AlphaGeometry 拿 IMO 银牌 | Google DeepMind | 解题 |
| 2025 | Lean 获 ACM SIGPLAN 软件奖 | Lean 的四位开发者 | 工具里程碑 |
| 2025 | Ken Ono 离开 UVA 加入 Axiom | Ken Ono | 数学家进工业界 |
| 2025-11 | 演讲时间线的起点：Collatz 序列 + transformer | 作者归属见附录 A | AI 与数学交叉 |
| 2025-12 | 解决一个 Erdos 问题（约 50 个推理节点） | AxiomProver | 演讲口径 |
| 2026-02 | 论文密集上线：k-微分奇偶（02-03）、几乎所有素数部分正则（02-04） | Axiom 团队 | AI 证明+形式化 |
| **2026-03-31** | **τ 函数论文提交 arXiv（约 500 个推理节点）** | **24 位作者，含 Ken Ono** | **AI 证明+形式化** |
| 2026-06 上旬 | Carina Hong 在 SAIR Summit 演讲（切片 06-06 发布） | Carina Hong | 方法论定调 |
| 2026-06-15 | Lean v4.31.0 发布 | Lean FRO | 工具版本 |
| 2026-06 | Nekrasov–Okounkov 论文被 Research in Number Theory 接收 | Heim、Neuhauser | Ono 附录由 AxiomProver 生成 |

演讲提到的成绩是 2 月以来的 7 篇论文、5 篇涉及形式化；官网论文页在演讲前后共挂出 12 篇，其中能在 arXiv 上独立核实的关键论文，见附录 A 的逐篇清单。

---

## 第一幕：AlphaProof 之后，AI 真的会做数学吗？

在 Axiom 这种"AI 数学家"出现之前，绝大多数 AI 攻克的数学问题都是**单点突破**。

AI 在国际数学奥林匹克（IMO）上拿奖，遵循的是"考前刷题 → 考试对线 → 出分"的范式。这条范式的问题不在"AI 解不出 IMO 题"，而在"解出 IMO 题不等于会做数学研究"——IMO 是 100 米短跑，数学研究是马拉松加铁人三项，规则完全不同。

2024 年 7 月，Google DeepMind 的 AlphaProof 与 AlphaGeometry 组合在 IMO 拿到银牌水平，这是 AI 第一次在数学竞赛里逼近金牌。到 2025 年，推理模型与形式化方法双双摘金，"AI 攻克数学"成了科技媒体的头条。

但 Hong 在演讲里泼了冷水。她举的例子是 Erdos 问题：这批问题曾因"AI 找到十个未解答案"的新闻引发热议，可细究之下，所谓"找到"大多是文献检索，而不是原创证明。她把这种模式称为**"数学宝可梦狩猎"**——找到一只，登上一张卡，丢掉，再找下一只。

这种"狩猎"式成果的问题在于：AI 在检索已有文献，不是在生成新的证明思想；而且这类单点突破难以系统评估，你没法回答"这台机器到底会不会做研究"。

Hong 给出的分界线是**"形式化验证"**：未来衡量 AI 能不能做数学的标准，不是"它解出了多少题"，而是"它能不能给出可被机器端到端验证的证明"。这是 Axiom 把整家公司押在 Lean 上的原因。

---

## 第二幕：Axiom 的路径——把 Lean 当成共同作者

Axiom Math 2025 年成立，总部在加州帕罗奥图。官网 axiommath.ai 上挂着一句克制的口号："The Starting Point for Reasoning"。Ken Ono 是公司的科学核心，CEO Carina Hong 负责商业和工程。

先说 Ono 这个人。他 1968 年生于费城，父亲 Takashi Ono 是二战后从日本移居美国的数学家。他高中辍学，没拿高中文凭就进了芝加哥大学，1989 年本科毕业，1993 年在 UCLA 拿到博士学位。此后辗转普林斯顿高等研究院、宾州州立大学、威斯康星、埃默里，2019 年起任弗吉尼亚大学 Thomas Jefferson 数学教授。他 1999 年一年内拿下 NSF CAREER、Sloan、Packard 三个早期职业奖项，2000 年获克林顿总统颁发的 PECASE，2003 年拿 Guggenheim Fellowship；担任过美国数学会副主席（2018-2021）、美国科学促进会数学分会主席（2020-2023）。

他的研究轨迹和 Ramanujan 缠绕得很深：2000 年在《数学年刊》的论文把 partition 函数的 Ramanujan 同余推广到所有大于 3 的素数模——"挂在数学家遗稿里的猜想"被系统性激活的经典操作；与 Duncan、Griffin 合作证明 umbral moonshine 猜想（论文 2015 年发表）；2019 年与 Griffin、Rolen、Zagier 在《PNAS》发表关于黎曼猜想的论文，证明了 Jensen–Pólya 判据的大部分情形。他还是《The Man Who Knew Infinity》的数学顾问兼联合制片人——就是 Jeremy Irons 演 Hardy、Dev Patel 演 Ramanujan 的那部。

2025 年，他离开 UVA，加入这家成立不久的公司，头衔是 Founding Mathematician。一个在 UVA 给本科生讲了一辈子课的讲席教授，转身去一家初创公司做 AI 数学——这种转型在数学界并不多见。

Axiom 给 Ono 提供的工具，一是内部的 AI 证明器 **AxiomProver**，二是开源工具集 **AXLE**（Axiom Lean Engine）——axle.axiommath.ai 上挂着 Console，可以校验证明（check）、抽取定理声明（extract_theorems）、批量分析证明状态（extract_proof_states），2026 年 8 月的 v1.7.0 版本还加上了供 MCP server 调用的机器可读文档接口。

Axiom 的技术路线，按演讲的概括是："基于开源语言模型，结合多智能体协作、工具调用、测试时计算扩展以及递归分解与回溯"。

拆开是五件事：

- **基础是开源语言模型**。演讲没有展开选型理由；从结果看，可复现性对数学场景确实是硬要求——你要让第三方能重跑你的证明流程。
- **多智能体协作**，一个证明任务拆成多个子任务，分给不同 Agent 串行或并行执行，而不是让一个 Agent 从头想到尾。
- **工具调用**是这套系统的肌肉：Agent 不空想下一步，它调用 Lean 的 tactic、调用 mathlib 库、必要时调用外部计算机代数系统做符号计算。
- **测试时计算扩展**——不靠更大的模型，靠推理时跑更多次来提升正确率。50 到 500 个推理节点的跃升具体怎么在测试时分配，演讲没有拆账，但"推理预算上量"这个方向是明确的。
- **递归分解与回溯**保证系统不陷入局部最优：某条推理路径走不通就退回来换路。

这五件事装进 Lean，结果是：**AxiomProver 输出的不是一段人类可读的草稿，而是一段 Lean 可执行的代码**。这段代码可以在 Lean 编译器里逐行检查，任何逻辑漏洞都会报错退出。

这是和"数学宝可梦狩猎"的区别：AI 不是在写"我以为是这样的"，而是在写"Lean 同意这是这样的"。

---

## 第三幕：硬数据——三个能对回 arXiv 的故事

Axiom 的论文覆盖数论、交换代数、代数几何、组合学等领域。以下三个故事，每一篇我都对回了 arXiv 原文，参与深度各不相同。

### 故事 1：Ramanujan τ 函数与素数（arXiv 2603.29970）

Ramanujan 在 1916 年定义 τ(n) 时，数学家关心的基本问题有两个：τ(n) 会不会等于零？τ(n) 取素数值的频率是多少？前者是 1947 年 Lehmer 提出的猜想——τ(n) 对所有 n 都不为零，至今既没被证明也没被推翻；后者更难，连"τ 的绝对值会不会无穷多次取到素数"都只是民间猜想（folklore conjecture）。

已知进展有一条线：2023 年 Boyuan Xiong 证明，τ 取到素数值的那些素数，在全体素数中的密度不超过 2/11。

Axiom 的论文（2026 年 3 月 31 日提交 arXiv，24 位作者里有 Ken Ono）把这条例往上压了一大截：

> **假设 ABC 猜想成立，那么 #{ℓ ≤ X：ℓ 为素数且存在 n 使 |τ(n)| = ℓ} = O(X^(13/22))，即 τ 函数"错过"了密度为 1 的素数子集**——素数值在素数中占比趋于零。

要读准这个结论：它是关于**素数集的密度**，说"几乎没有素数 ℓ 能作为 |τ(n)| 出现"；至于"无穷多个素数值是否存在"，论文反而给了一个启发式论证，预测 S(X) 的量级约为 X^(1/11)/(log X)²——这个量会缓缓长到无穷，但速度慢到几乎测不到。"无穷多"是猜想，密度为零（在 ABC 之下）才是证明。

论文摘要最后一句写得很直白：主引擎由 AxiomProver 从自然语言陈述的命题出发，在 Lean/Mathlib 中自动生成并形式化。这篇已被《Indagationes Mathematicae》接收——arXiv v3 版本的修订说明是"回应两位审稿人的意见"，能看出它走完了正规的评审流程。

ABC 猜想是 1985 年由 Joseph Oesterlé 和 David Masser 提出的数论猜想，普遍被认为是"几乎肯定为真但极难证明"的那类问题。2012 年望月新一曾宣称在 inter-universal Teichmüller 理论中证明了它，该声明至今未被数学界广泛接受。Axiom 的做法是工程化的诚实：把"如果 ABC 成立，那么密度为零"这个**条件命题**先证下来——这本身已经是有分量的工作——然后把无条件版本留给人类数学家。

### 故事 2：几乎所有素数都是部分正则的（arXiv 2602.05090）

第二篇（2026 年 2 月 4 日提交 arXiv，21 位作者，Ono 同样在列）已被《Archiv der Mathematik》接收，主题是"几乎所有素数都是部分正则的"。

背景是 19 世纪就有的老问题。Bernoulli 数早在 18 世纪初就进入了数学；到 1850 年代，Kummer 在研究费马大定理时发现，有些素数会整除某些 Bernoulli 数的分子，这类"反常素数"（irregular primes）会破坏代数结构的规整性。用现代语言说：对奇素数 p，看 p 次分圆域 Q(ζ_p)（添加 p 次单位根得到的数域），它的类群刻画了素数理想分解的偏离程度——p"正则"与否，就看类群的某些特征空间是否消失。

Axiom 这篇论文给出了一个部分正则的定量定义（特征标范围随 p 增长的条件），然后证明：**密度为 1 的素数都满足这个部分正则性**。借助 Leopoldt 反射定理，它还推出一个部分 Vandiver 定理——对密度为 1 的素数，类群的偶特征空间全部消失。演讲把后者概括为"首个关于偶子空间的无穷定理"。

论文摘要明确写道：证明"几乎所有素数部分正则"的定理已在 Lean/Mathlib 中完全形式化，由 AxiomProver 从自然语言陈述的猜想自动生成。三篇故事里，这一篇的 AI 参与最深——连主定理本身都是机器给出的。

### 故事 3：k-微分自旋奇偶：从条件结果到无条件证明（arXiv 2602.03722）

第三个故事（2026 年 2 月 3 日提交 arXiv）作者里有 Dawei Chen、Evan Chen、Kenny Lau、Ken Ono、Jujian Zhang。论文完全确定了 genus 0 和 genus 1 黎曼面上、带指定零点与极点阶的 k-微分（k-differentials）的自旋奇偶性——这是模空间与平坦结构研究里的基础问题。

有意思的是证明的来路。这个结果先前已经有人得到过，但是**带条件的**：第一作者与 Quentin Gendron 此前在假设一个数论猜想（Conjecture A.10）成立的前提下证出。这一次，团队把那个猜想用 Jacobi 符号重新表述，把证明归约到一个组合恒等式上；摘要原话是："证明由 AxiomProver 获得，系统在 Lean/Mathlib 中形式化了该组合恒等式的证明。"

这篇的价值点在另一个方向：AI 把别人"条件成立才行"的结果做成了无条件定理，并且让证明里最机械、最容易出错的那一环（组合恒等式）接受了机器验证。三篇放在一起看，AxiomProver 的参与深度是一个光谱——从"形式化一个关键引理"，到"自动生成并形式化整条主定理"。

---

## 第四幕：从"解题"到"发现"

三个故事的参与深度不同，但指向同一个范式变化。

| 范式 | 关键词 | 代表事件 | 评估指标 | 状态 |
|---|---|---|---|---|
| 1. 解题 | 数学宝可梦 | AlphaProof IMO 银牌（2024）/ 推理模型摘金（2025） | 得分 / 通过率 | 演讲称为已被超越 |
| 2. 发现+验证 | 论文证明 | Axiom 被期刊接收的论文 | 期刊接收 / Lean 形式化通过 | 当前主线 |
| 3. 发现+猜想 | 猜想生成 | 自动猜想生成 + 库学习 | 猜想质量 / 推动他人工作 | 路线图上的下一步 |

**三个范式的分野在于"AI 给出的是否可被独立判决"**——范式 1 是黑盒输出对错，范式 2 是 Lean 形式化可验证，范式 3 还需要数学共同体的同行评审。

Hong 在演讲结尾给出的路线图有三步：

- **自动猜想生成**：让 AI 不只证明给定的命题，而是自己提出"哪个方向值得证"。
- **库学习**（library learning）：让 AI 从 mathlib 这种大型形式化库中自动抽取可重用的引理，而不是每证一个新题都从头搭建。
- **形式化定理证明与上述两者深度融合**：猜想 → 证明 → 形式化验证 → 反哺到库。这条流水线一旦跑通，AI 数学家的工作节奏会和人类数学家完全不同。

切片视频的结语把这层意思收得很紧：

> **"数学发现的未来不取决于 AI 解题的速度，而取决于每一步推理能否被形式化验证所锚定。"**
>
> ——SAIR 演讲切片视频文案

把这句话落回个体：AI 不会比高斯更快，但它可能是第一个能自证"我的证明成立"的数学家——因为那个证明交给了 Lean，而 Lean 不接受口头担保。

Ramanujan 没有定理证明器。他 1913 年从马德拉斯把写满公式的信寄给剑桥的 Hardy，靠对方判断对错；两年后他自己到了剑桥，和 Hardy 面对面工作，但他的很多公式直到今天还在被证明。2026 年，AxiomProver 在 Lean 里给出证明，每一步都可以被任何一台装了 Lean 的电脑复现。

演讲和视频文案都以同一句话收尾：**数学发现不再是天才的专利**，它正在变成一个可扩展、可验证的协作过程。

---

## 读这份成绩单，先分清三对概念

第一对，**"接收"和"发表"**。附录 A 里的状态大多是"接收"（accepted）——通过了同行评审、排队等见刊，和正式刊出之间还有一段距离；而这批论文清单本身来自 Axiom 自己的论文页（axiommath.ai/papers），由公司披露。

第二对，**"AI 证明"和"AI 发现"**。演讲口径是 7 篇论文里 5 篇涉及形式化定理证明，但各篇的参与深度差别很大：有的是 AxiomProver 自动生成并形式化主定理，有的只是形式化一个组合恒等式（见第三幕）。Axiom 展示的是"AI 把定理证出来"，不是"AI 提出新问题"——后者还挂在路线图上。

第三对，**条件结论和结论**。最重磅的 τ 素数密度论文，前提是"ABC 猜想成立"；而 ABC 猜想本身还没有无条件证明。Axiom 证下的是条件命题，把无条件版本留给人类数学家——这是它诚实的地方，也最容易在传播中被省略。

---

## 第五幕：给 AI 工程师的 3 条可借鉴路径

对 2026 年做 AI Agent / AI for Science / 形式化验证的工程师，Axiom 的范式里有几条能落到自己项目里的方法论。这 3 条不是"我应该用 Lean"这种口号，是从论文里反复出现的同一个工程决策里提炼出来的。

### 1. 形式化优先（Formalization First）——给 AI Agent 装一个"判决者"

Axiom 的全部成绩建立在 Lean 之上。Lean 在这里不是"辅助工具"，而是"判决者"——每一个证明步骤都要被编译器逐行检查，任何逻辑漏洞都会让证明报错退出，AI 必须回溯换路。

这个范式可以推广到其他 Agent 领域：

- **代码 Agent**：让 LLM 写代码 → 用编译器 / 类型检查器 / 测试框架当判决者 → 报错就回溯。Cursor / Codex / Claude Code 的现状是这个范式的子集，但判决粒度可以更细（按函数 / 按类型 / 按契约）。
- **数据 Agent**：让 LLM 做数据转换 → 用 Great Expectations / dbt tests 当判决者 → 数据异常就回溯。
- **决策 Agent**：让 LLM 做多步推理 → 用形式化逻辑 / SMT solver 当判决者 → 推理错误就回溯。

Axiom 的核心判断是：**判决者必须独立于生成者**。如果判决者也是 LLM，等于自己给自己发奖。Lean、编译器、test framework 这些"非 LLM"的判决者才是这套方法的关键。

### 2. 多智能体 + 工具调用 + 测试时计算——2026 AI Agent 的"标配三件套"

Hong 概括的五件事里，前四件（开源模型、多智能体、工具调用、测试时计算）到 2026 年已是多数 Agent 框架的标配，第五件（递归分解与回溯）在数学证明这种深搜索场景里才显得特别重。

| 维度 | Axiom 的做法 | 可以推广到 |
|---|---|---|
| 基础模型 | 开源 | 任何需要长期可复现的领域 |
| 多智能体 | 任务拆解为子任务分给不同 Agent | 任何复杂多步任务 |
| 工具调用 | Lean / mathlib / 计算机代数系统 | 任何需要外部工具的领域 |
| 测试时计算 | 50→500 个推理节点的 10 倍跃升 | 任何"慢思考"场景 |
| 递归回溯 | 路径失败就换 | 任何搜索类任务 |

推理节点从 50 到 500 的跃升，是 2025 年 12 月到 2026 年 3 月之间发生的。演讲没有公布节点怎么分配，但结论方向对工程师有用：**模型大小不是唯一杠杆，推理预算是**。

### 3. 论文驱动 + 期刊接收——把"AI 成果"装进学术评价体系

Axiom 选择把 AI 生成的证明投稿到正经学术期刊，让同行评审给 AI 证明打分。这条路比"在社交媒体上宣布 AI 解决了某问题"难走得多，含金量也高得多——arXiv 上能对回的这几篇，摘要里都保留着"referee reports""see the Appendix"这类经过评审流程的痕迹。

对中国 AI 工程师，这条路有更具体的含义：过去几年大家靠 benchmark 排行榜（GSM8K、MMLU）证明实力，但在 AI for Science 这条赛道，**形式化验证 + 期刊评审**正在成为更硬的标尺。DeepMind 的 AlphaProof 走的也是 Lean 形式化路线——判决者的选择正在收敛。

---

## 第六幕：如何自己体验 Lean + 形式化验证

想自己试试 Lean，门槛比想象低。

**第一步：装 Lean**

```bash
# macOS / Linux 一行装好（elan 是 Lean 的工具链管理器）
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh

# 验证（stable 版本会持续更新，2026-09-07 快照为 v4.33.1）
lean --version
# Lean (version 4.33.1, arm64-apple-darwin, commit ..., Release)
```

**第二步：写第一个证明**

```lean
-- 命题：对所有自然数 n，n + 0 = n
example (n : Nat) : n + 0 = n := by
  rfl  -- reflexivity，Lean 自己验证
```

**第三步：跑 AXLE**

打开 https://axle.axiommath.ai/ ，这是 Axiom 开源的 Axiom Lean Engine。你可以：

- 用 Console 校验自己的 Lean 证明（check）
- 从长证明里抽取定理声明（extract_theorems）
- 批量分析证明状态（extract_proof_states，v1.6.0 起提供）

AXLE 的 GitHub 和 Docs 入口都在页面上，v1.7.0 起 MCP server 可以直接拉机器可读的工具文档。

**第四步：读 mathlib**

mathlib 是 Lean 的数学标准库——截至 2025 年 5 月已形式化超过 210,000 个定理和 100,000 个定义，2026 年拿下 Demailly 开放科学奖。GitHub 仓库 leanprover-community/mathlib4，文档站 https://leanprover-community.github.io/ 。

如果你能读懂 mathlib 里 5 个引理，理解为什么 Axiom 选择 Lean 而不是 Coq / Isabelle / HOL Light，那这篇文章想说的你就理解了。

---

Ramanujan 没有定理证明器，他的公式要靠 Hardy 和后辈数学家一个一个验。现在，Lean 装进你的电脑就能工作。**100 年前数学发现是天才的特权，2026 年形式化验证让这件事至少变成了一个工程问题**。从马德拉斯寄出的信纸到 Axiom 的 Lean 终端，数学发现没有变得更简单，但验证它的门槛第一次让普通人够得到。

---

## 谁该去看原片，谁读这篇就够

想听 Carina Hong 的原话、核对 50→500 推理节点的细节、看 AxiomProver 演示的，去 B 站搜 BV1tV7Q6TEUV（SAIRfoundation，2026-06-06 发布，15 分钟切片，播放量 6212——2026-09-07 快照）。文稿只能转述判断，演示的冲击力留在视频里。

只要结论和路线图的——Axiom 做了什么、三条可借鉴方法、怎么上手 Lean——读这篇就够，不必为几条结论专门去翻视频。

想动手的，直接跳到第六幕和附录 A：把 Lean 装起来跑第一个证明，再把三篇 arXiv 论文的摘要读一遍，比看任何讲解都直观。

---

## 附录 A：论文清单与核实口径（截至 2026-09-07）

演讲口径的成绩单是：2026 年 2 月起发布 7 篇论文、5 篇涉及形式化、3 项被期刊接收。官网论文页在演讲前后共挂出 12 篇（该页面由前端脚本渲染，历史快照未能存档清单内容）。以下 6 篇已对回 arXiv 独立核实：

| 论文 | arXiv | 提交日期 | 核实要点 |
|---|---|---|---|
| ABC implies that Ramanujan's tau function misses almost all primes | [2603.29970](https://arxiv.org/abs/2603.29970) | 2026-03-31 | 24 位作者含 Ken Ono；假设 ABC 下 S(X)=O(X^(13/22))；主引擎由 AxiomProver 自动生成并形式化；《Indagationes Mathematicae》接收（视频口径） |
| Almost all primes are partially regular | [2602.05090](https://arxiv.org/abs/2602.05090) | 2026-02-04 | 21 位作者含 Ken Ono；密度为 1 的素数部分正则 + 部分 Vandiver 定理；主定理在 Lean/Mathlib 完全形式化；《Archiv der Mathematik》接收（视频口径） |
| Parity of k-differentials in genus zero and one | [2602.03722](https://arxiv.org/abs/2602.03722) | 2026-02-03 | 作者含 Dawei Chen、Evan Chen、Ken Ono；证明由 AxiomProver 获得，组合恒等式在 Lean/Mathlib 形式化 |
| Transformers know more than they can tell — Learning the Collatz sequence | [2511.10811](https://arxiv.org/abs/2511.10811) | 2025-11-13 | 与演讲时间线起点（Collatz + transformer）日期与主题吻合；但 arXiv 署名为 François Charton 与 Ashvni Narayanan，与 Axiom 的关系未获确认 |
| A quadratic form generalization of rational dinv | [2604.13238](https://arxiv.org/abs/2604.13238) | 2026-04-14 | Yifeng Huang 参与；与演讲时间线中"2026-04-14 Dyck paths"条目吻合 |
| Chebyshev quotients, Demazure multiplicities, and Dyck-path models | [2604.25246](https://arxiv.org/abs/2604.25246) | 2026-04-28 | Rekha Biswal 参与；与演讲时间线中"2026-04-29 Lie 代数 + Dyck paths"条目吻合 |

其余条目（numerical semigroups、Mirzakhani–Wright 障碍、partition 多项式猜想、Aumann 定理形式化、无穷双射等）截至 2026-09-07 未能独立核实，以官网论文页为准。另据官网当前版本：**Nekrasov–Okounkov 多项式主导零点**论文已被 Research in Number Theory 接收（作者 Bernhard Heim、Markus Neuhauser，K. Ono 的附录证明由 AxiomProver 在 Lean 中生成并验证）；官网论文页在 2026 年 6 月下旬至 8 月已更新为新一批论文（含 Rogers–Ramanujan 恒等式的形式化 q-级数等），旧清单已不在页面上。

## 附录 B：关键术语 5 分钟扫盲

- **τ(n) 函数**（Ramanujan tau function）：Ramanujan 1916 年定义的数论函数，$\sum_{n=1}^{\infty} \tau(n)q^n = q\prod_{n=1}^{\infty}(1-q^n)^{24}$，前 6 个值是 1, −24, 252, −1472, 4830, −6048。
- **Lehmer 猜想**（1947）：$\tau(n) \neq 0$ 对所有 n 成立。至今既未被证明也未被推翻。
- **ABC 猜想**（1985）：对任意 ε>0，仅有有限多个互素正整数组 (a,b,c) 满足 a+b=c 且 c > rad(abc)^(1+ε)。τ 函数密度论文假设该猜想成立。
- **Lean 定理证明器**：2013 年由 Leonardo de Moura 在微软研究院启动的证明助手；2025 年获 ACM SIGPLAN 软件奖（授奖词：对数学、硬件与软件验证及 AI 的重大影响）；2026 年 mathlib 获 Demailly 开放科学奖。当前 stable 版本 v4.33.1（2026-08-21）。
- **mathlib**：Lean 4 的数学标准库，截至 2025 年 5 月包含超过 210,000 个定理与 100,000 个定义。
- **AxiomProver**：Axiom 的 AI 证明器，从自然语言陈述的命题出发自动生成证明并在 Lean/Mathlib 中形式化（论文摘要原话支撑）。
- **AXLE**（Axiom Lean Engine）：Axiom 开源的 Lean 证明环境与工具集，Console 在 axle.axiommath.ai。
- **部分正则**（partially regular）：arXiv 2602.05090 定义的素数性质——分圆域 Q(ζ_p) 类群在给定特征标范围内的特征空间消失，等价于 p 在该范围内不整除 Bernoulli 数 B_2k 的分子。
- **Erdos 问题**：Paul Erdos（约 1500 篇论文）留下的大量公开问题。演讲批评的对象不是问题本身，而是"AI 用文献检索冒充原创证明"的汇报方式。

## 附录 C：核心参考资料

- 视频原片：B 站 SAIRfoundation《Axiom 创始人 Carina Hong 主题演讲：AI 数学家正在攻克数论猜想，形式化验证是关键》（BV1tV7Q6TEUV，2026-06-06 发布，902 秒，2026 Science x AI Summit 系列切片第七期）
- Axiom Math 官网：https://www.axiommath.ai/
- Axiom 论文列表：https://www.axiommath.ai/papers
- AXLE（Axiom Lean Engine）：https://axle.axiommath.ai/
- τ 函数论文：https://arxiv.org/abs/2603.29970
- 部分正则素数论文：https://arxiv.org/abs/2602.05090
- k-微分奇偶论文：https://arxiv.org/abs/2602.03722
- Ken Ono 维基条目：https://en.wikipedia.org/wiki/Ken_Ono
- Ramanujan tau function 维基条目：https://en.wikipedia.org/wiki/Ramanujan_tau_function
- Lean 维基条目：https://en.wikipedia.org/wiki/Lean_(proof_assistant)
- 2026 Science x AI Summit：SAIR 基金会主办
