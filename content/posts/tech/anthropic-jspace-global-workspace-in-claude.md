---
title: "从 J-space 到全局工作区：Anthropic 如何观察 Claude 的隐藏推理"
slug: "anthropic-jspace-global-workspace-in-claude"
date: 2026-07-06
tags: ["Anthropic", "Mechanistic Interpretability", "J-space", "Global Workspace"]
categories: ["技术深潜"]

description: "系统拆解 Anthropic 的 Jacobian Lens、J-space 与全局工作区研究，解释 Claude 的隐藏推理、结构证据、安全审计价值，以及这套方法仍然看不到什么。"
summary: "这不是一篇“Claude 有意识了”的转述，而是一篇技术判断：Anthropic 用 Jacobian Lens 找到的 J-space，究竟如何支撑可报告、可调动、可参与推理的共享工作区，以及它在结构证据、安全审计、后训练与反思训练上的真正价值与边界。"
featuredImage: "/images/anthropic-jspace-header.webp"
---

这不是一篇"Claude 觉醒"的新闻转述。Anthropic 在 2026 年 7 月 6 日发布的 J-space，到底揭示了哪些可被因果干预的隐藏推理，又在哪些地方仍然只是一台局部显微镜——这才是本文要回答的问题。

更值得盯住的不是"模型会不会有意识"这种答不上来的争议，而是一个已经被实验支撑的事实：前沿语言模型内部出现了一小片特权的"工作台"，专门承接可报告、可调动、可复用的显式思考。

这项工作有两个入口：研究页 A global workspace in language models 偏研究导读，Transformer Circuits 上的正式论文 Verbalizable Representations Form a Global Workspace in Language Models 偏完整技术细节。两者讲的是同一件事，本文把它们当作同一组工作来拆。

## 目录

- 学习目标
- 一句话判断：这不是"机器意识实锤"
- 先把两篇研究分开看
- 总览图：怎么读这篇 J-space 论文
- Jacobian Lens 到底在算什么
- J-space 到底是什么，不是什么
- Anthropic 为什么把它叫"工作区"
- 一个具体任务如何流过 J-space
- 结构上它为什么更像"工作区"
- J-space 与自动处理的分界线
- 这项方法能做什么安全审计
- 后训练怎样改写 J-space
- 反事实反思训练：为什么"训练它会怎么说"会改写"它会怎么想"
- 为什么它像全局工作区，但还不是"有主观体验"
- 目前最重要的边界
- 如果你想自己复现
- FAQ 与参考资料
- 练习
- 进阶方向
- 自测题

---

## 学习目标

- 分清 2025 年的 circuit tracing 方法论文，和 2026 年的 J-space / global workspace 论文各自解决什么问题。
- 理解 Jacobian Lens 不是"直接读脑"，而是把当前层的残差表征先运输到最终输出基底，再解码。
- 看懂 Anthropic 用哪几类实验论证 J-space 具备"可报告、可调动、可参与推理、可共享广播"的性质。
- 明白这项工作真正支持的是 access consciousness 的功能类比，而不是 phenomenal consciousness 的证明。

---

## 一句话判断：这不是"机器意识实锤"

如果只保留一个结论，我会这样概括这组工作：

**Anthropic 发现的，不是 Claude"有了主观体验"，而是 Claude 内部存在一小块更接近"可被报告、可被主动调动、可被多任务复用"的共享表征区。**

这块区域被他们称为 **J-space**。它重要，不是因为名字像脑科学，而是因为它满足了几条很强的功能性标准：

1. 模型能把这里面的内容报告出来。
2. 模型能在被要求时把某个概念维持在这里。
3. 多步推理会真的经过这里，而不只是被这里"照出来"。
4. 同一份中间表征可以被多个下游任务复用。
5. 与此同时，很多熟练、自动化的处理并不依赖它。

这正是 Anthropic 会把它和 **全局工作区理论（Global Workspace Theory, GWT）** 放在一起讨论的原因。

但也正因为如此，文章开头如果直接写成"机器意识被证明了"，其实是把研究结论往前推过头了。Anthropic 自己说得很明确：这项工作对 **access consciousness** 有实质性启发，但谈不上证明 **phenomenal consciousness**，更谈不上"Claude 会感受、会体验"。研究页原话是：他们的实验并不表明 Claude 能拥有 experiences，或者能像人类那样 feel 事物；甚至"是否有任何科学实验能证明这件事"本身都不清楚。

---

## 先把两篇研究分开看

这篇题材最容易写乱的地方，是把两条研究线揉成一团。更稳的读法是先把它们拆开：

| 研究 | 核心问题 | 关键方法 | 你能得到什么 |
| --- | --- | --- | --- |
| 2025: Circuit Tracing | 模型在一个具体 prompt 上，内部有哪些中间特征和路径把输入推到了输出？ | Cross-Layer Transcoder（CLT）+ attribution graph | 一张局部"计算图"，能提出电路假设并做干预验证 |
| 2026: Verbalizable Representations Form a Global Workspace | 模型里是否存在一块能被报告、能被调用、能承接显式推理的共享表征区？ | Jacobian Lens（J-lens）+ 一系列功能性实验 | 对 J-space 的功能性证据，以及它和全局工作区的类比 |

两者有继承关系，但不是一回事。

前一条线更像"我怎么把一段具体计算拆开"；后一条线更像"我在模型里有没有找到一块类似共享白板的地方"。把这两篇论文混讲，最常见的后果有两个：

- 把 attribution graph 的能力误写成 J-lens 自带的能力。
- 把"能看到可 verbalize 的中间表征"夸大成"已经完整读懂模型内部"。

后面以 **J-space / global workspace** 为主线，但在需要的时候会借 2025 的方法论文解释它的方法论背景。还有一点值得提前说明：2025 那篇 Tracing the thoughts of a large language model 做的是 Claude 3.5 Haiku，用的是 CLT / attribution graph；J-space 论文主要落在 Claude Sonnet 4.5、Haiku 4.5、Opus 4.5，对齐审计案例还用到了 Opus 4.6。两批实验的对象和方法都不同，引用时不要串。

---

## 总览图：怎么读这篇 J-space 论文

这篇论文真正难读的地方，不是公式多，而是它同时在回答四类不同问题。如果把这四层混成一句"Anthropic 发现了意识"，基本就会读偏。

| 层次 | 论文真正回答的问题 | 代表内容 | 读者该抓住什么 |
| --- | --- | --- | --- |
| 仪器层 | J-lens 能不能稳定读出一种"可被说出来"的中间表征？ | Jacobian Lens、J-space 定义 | 它读的不是当前输出，而是"未来可能被 verbalize 的概念" |
| 功能层 | 这些表征会不会真的参与报告、控制、推理和复用？ | verbal report / directed modulation / internal reasoning / flexible generalization / selectivity | 关键看 swap、ablation、patching 后答案会不会跟着变 |
| 结构层 | 这些表征在网络里是不是占一个特殊位置？ | workspace layer band、capacity、broadcast | 它是"小而特权"的广播格式，不是整个残差流 |
| 应用层 | 这套东西能拿来干什么？ | alignment auditing、post-training diff、counterfactual reflection training | 它不只是显微镜，已经开始变成干预接口 |

我建议的阅读顺序也按这四层走：先看 J-lens 在读什么，再看这些读数是否因果 load-bearing，最后才讨论它与 conscious access 的关系。这样不容易把"看见几个词"误判成"已经读懂了全部心智结构"。

---

## Jacobian Lens 到底在算什么

J-lens 的直觉不复杂：**给定某一层、某一位置上的残差向量，它更倾向于让模型在后面"说出"哪些词？**

Anthropic 不是直接把中间层拿去 unembed，而是先做了一步"运输"。更准确地说，他们先估计某层残差流在后续网络里会如何影响最终可输出的词表分布，再在那个基底里解码。Jacobian Lens 的核心形式：

$$
\mathrm{lens}_{\ell}(h)=\mathrm{unembed}(J_{\ell} h), \qquad
J_{\ell}=\mathbb{E}_{\text{prompt},\,t,\,t' \ge t}\left[\frac{\partial h_{\mathrm{final},t'}}{\partial h_{\ell,t}}\right]
$$

这里要抓住四点：

- $h_{\ell,t}$ 是第 $\ell$ 层、第 $t$ 个位置的残差表征。
- $J_{\ell}$ 不是某个 prompt 的 Jacobian，而是对语料、源位置、当前/未来目标位置求平均后的线性映射。论文里这个期望是在大约 1000 条类预训练 prompt 上估出来的。
- 这一步平均，目的是把"这个上下文里刚好会被说出来的话"跟"很多上下文下都可被说出来的概念"尽量分开。
- 实际读数看的不是一句自由文本解释，而是一份词表排名；靠前的词，是这份激活最倾向于让模型未来说出来的词。

所以它和朴素的 logit lens 不一样。朴素 logit lens 近似把当前层当成已经位于最终输出坐标系里，直接读；J-lens 则承认后续层还会继续加工，于是先估计"这份中间状态会如何影响未来能说出来的话"。还有一处实现细节：梯度默认算到倒数第二层而非最后一层，因为带上最后一个 transformer block 有时反而会给 lens 读数加噪。

另一个常被一起提到的参照物是 **tuned lens**。它的训练目标就是尽量预测最终输出，所以在很多需要中间步骤的例子里会过早"跳到答案"，反而不擅长暴露未 verbalize 的中间推理。附录里专门比较过这三者：晚层时它们会收敛，越往中层走，J-lens 越容易保住真正的中间概念，logit lens 会变噪，tuned lens 则更容易直接报最终词。

从这个角度看，**J-space 不是一个额外训练出来的 scratchpad，也不是模型显式写下来的 chain-of-thought**。它更像一组在内部静默活动、与"可说出的概念"对齐的表征方向。Anthropic 的表述很克制：这些词并不意味着模型此刻要把它们写出来，只说明这些概念"在它脑子里"。

## J-space 到底是什么，不是什么

这里最容易被忽略的技术点是：**J-space 不是一个简单、固定、低维的小盒子。**

论文里的 J-lens 向量数量是按词表来的，远多于残差流维度，所以它们在数学上是一个 **overcomplete frame**。这意味着：

- J-lens 向量整体完全可能张成几乎整个残差空间。
- 单个激活也不只有一种"唯一分解"。
- 所谓 J-space，更像"能被少量 J-lens 向量稀疏、非负地近似出来的那一块内容"，而不是事先切好的固定槽位。论文给了一个几何说法：给定 $k$，J-space 对应若干 $k$ 维锥的并集。

Anthropic 的操作化定义因此很务实：他们通常允许一次只激活不超过大约 $k \le 25$ 个 J-lens 向量，用稀疏分解去近似某个激活的 J-space 成分。这个 $k$ 的选择本身带有任意性，是经验观察到的"同一时刻有意义地激活的向量数"。

这个定义的好处，是把"可广播、可报告的少量概念"从"大量背景处理"里分出来；代价也明确：它天然更像一份一袋概念的读数，而不是完整的结构化语义树。

所以更准确的说法不是"Claude 里面有一块地方叫 J-space"，而是：**Claude 的残差流里存在一种稀疏、可 verbalize、被广泛读写的表示格式；Anthropic 用 J-lens 把它近似读了出来。**

---

## Anthropic 为什么把它叫"工作区"

Anthropic 不是因为看到几个漂亮可视化，就把 J-space 命名成"工作区"。他们真正依赖的是一组功能性实验。把这些实验并在一起看，J-space 的角色就很清楚了：

| 工作区属性 | 代表实验 | 结论 |
| --- | --- | --- |
| 可报告 | 让 Claude 先默想一种运动，再说出来；J-lens 先读到 Soccer，替换成 Rugby 后回答跟着变 | J-space 不是被动记分牌，输出真的会读它 |
| 可主动调动 | 一边抄写无关句子，一边让 Claude 在"脑中"想着 orange，或者默算 $3^2 - 2$ | 模型能在不写出来的情况下把内容维持在 J-space |
| 因果中介 | 读到"会结网的动物有几条腿"时，中间出现 spider；把 spider 换成 ant，答案从 8 变成 6 | 多步推理经过 J-space，而不只是被它映照 |
| 共享广播 | 在询问首都、语言、货币、洲别这几类不同问题时，把 France 换成 China，会同时改写多个答案 | 同一表征能被多个下游系统复用 |
| 与自动处理分界 | 删掉 J-space 后，流利续写、基础语法、简单事实还能做；多步推理、摘要、押韵写作明显崩掉 | 它更像"显式思考的工作台"，不是全部计算本体 |

合在一起，J-space 就确实不像普通中间层特征。它更像一条高连接度的共享通道：很多系统能往里写，很多系统也能从里读。

而且这种"共享"不是凭直觉描述出来的。论文把 concept vector 拆成 J-space 成分和非 J-space 成分时，前者只解释概念向量方差的 **中位数 6% 到 7%**，约 93% 落在 J-space 之外，可这点成分已经承担了 verbal report 的主要因果作用——纯 J-space 成分的交换有 59% 的试验把目标答案顶进 top-5，直接用 J-lens token 向量能做到 88%，而把 J-space 成分钳掉只剩 5%。在更系统的 flexible generalization 评估里，作者做了 **192 次跨函数交换**（国家、月份、动物、数字词四类 × 四种函数 × 12 对），标准强度下 **76 次成功**，把交换强度加到 $\alpha = 2$ 后升到 **101 次**；其中"国家"参数加载最重、交换最稳，"数字词"最差。这组数字很像在告诉你：工作区不是"大容量"，而是"小容量但高权限"。

在 internal reasoning 这一项，跨模型的成功中间概念交换率也值得一提：Haiku 4.5 是 54%，Sonnet 4.5 和 Opus 4.5 都是 70%，而且中间交换生效的位置通常比答案交换早约 17% 的层段——这很符合"先定位中间概念、再调取最终事实"的直觉。

```mermaid
graph LR
    A[输入文本] --> B[局部处理]
    B --> C[J-space]
    C --> D[报告/推理/规划/共享广播]
    B --> E[自动处理]
    E --> F[流利续写/语法/熟练技能]
```

这张图最重要的地方不在"J-space 很中心"，而在 **B → E → F 这条旁路依然存在**。Anthropic 的结论从来不是"Claude 所有计算都在 J-space 里发生"，而是"Claude 的一部分高阶、可报告的处理，会稳定经过这里"。

---

## 一个具体任务如何流过 J-space

最能说明 J-space 不是装饰品的，是那些必须经过中间概念才能完成的任务。

以这个 prompt 为例：

> "The number of legs on the animal that spins webs is ..."

模型要答对，需要先在内部完成两步：

1. 把 "the animal that spins webs" 映射成 **spider**。
2. 再从 spider 调出 **8 条腿** 这个事实。

Anthropic 观察到，`spider` 这个词会在中间层的 J-space 里亮起来，尽管 prompt 和最终输出里都没有它。更关键的是，他们没有停在"看见了"这一步，而是做了干预：

- 把 J-space 里的 `spider` 换成 `ant`
- 让剩下的网络按原样继续跑

结果答案从 **8** 变成了 **6**。

这件事很重要，因为它把两种解释区分开了：

- 如果 J-space 只是"显示屏"，那你改它不该影响真正的计算。
- 如果 J-space 是"中间工位"，那下游系统就会老老实实接着它继续算。

实验结果显然支持后者。J-space 更像推理过程里的一个共享工位，而不是赛后统计板。

如果你更喜欢两跳推理的例子，也可以看 Anthropic 在另一篇研究里反复展示的那类路径：

```mermaid
graph LR
    A[Dallas] --> B[Texas]
    B --> C[Austin]
```

意思不是模型里真有一条干净的三节点流程图，而是：**中间概念可以被定位、被替换，并且替换后会把下游答案一起改掉。** 这才是"中介变量"有因果作用的最低标准。

## 结构上它为什么更像"工作区"

如果说前面的实验回答的是"它会不会用"，这一节回答的就是"它在网络里是不是占了一个特殊位置"。这部分很关键，因为它决定了 J-space 到底是一个好看的 probe 现象，还是一个值得认真对待的组织层。

Anthropic 给出的结构证据，核心有三类。

### 1. 它只在中间层带像工作区

论文把 25 个等间距层重新编号到 0 到 100。对 Sonnet 4.5 来说，真正稳定承载 workspace-like 内容的，大致是 **L38 到 L92** 这一段：

- 更早的层，J-lens 读数噪声更重，更像局部解析和底层预处理。
- 更晚的几层，读数越来越贴近即将输出的 token，本质更像"motor"阶段，而不是可再加工的中间思考。

这点很重要，因为它说明 J-space 不是"从第一层到最后一层都一样地存在"。它有进入、有高峰，也有退出。论文用 CKA（centered kernel alignment）去测层间块结构，正好把网络分成感觉层、工作区层、运动层三段。

### 2. 它容量有限，而且只占总活动的一小部分

论文用稀疏分解估计 J-space occupancy，得到的不是几百上千个同时活跃概念，而是在 workspace band 里大约 **二十几个** 的中位水平。与此同时，J-space 成分解释的总激活方差 **不到 10%**。

这正是它像工作记忆而不像全量状态转储的地方：

- 它能放下的，是当前任务需要被显式拿来操作的一小撮内容。
- 放不下的，或者根本没必要放进去的大量语法、格式、局部 bookkeeping，会留在别的表示里。

### 3. 它被网络其余部分"偏爱"地读写

Anthropic 还测了一个很像广播格式的信号：J-lens 向量跟下游 MLP、attention 组件的权重组合得特别广、特别强。简单说，很多部件都更容易从这种方向读出东西，也更容易把东西写进去。

这里要小心区分两个不同的度量，它们容易被当成同一个数：

- 研究页给了一个偏定性的说法：读写 J-space 模式的组件远多于普通模式，量级上"约 **100 倍**"。
- 技术论文图 32 里的 MLP gain，J-lens 向量在 workspace band 被放大约 **10 倍**（相对神经元输出方向的增益为 1）。

两者度量的对象不同：前者偏"有多少组件在读写"，后者是"单条读写通路的增益倍数"。引用时标清是哪一个，才不会把读者带偏。

论文里几项结果很有代表性：

- 一小组 attention heads（workspace 层里按 gain + label-retention 取出的前 1%）会特别偏向跨 token 传递 J-space 内容。
- 把这些 broadcast heads ablate 掉，J-lens top-25 的召回率从 0.86 掉到 **0.67**；注入思维报告率从 **0.54 掉到 0.09**；但对普通下一词预测的直接破坏相对有限，只有约 5% 的位置改了 top-1。

合在一起看，这三类结构证据才让"workspace"这个说法站得住。否则你只能说"我找到一类好读的 token 方向"，还不能说"我找到一套被广泛复用的共享表示格式"。

---

## J-space 与自动处理的分界线

J-space 很抓眼球，但它最值得认真看的，恰恰是它的边界。

Anthropic 做过一个非常漂亮的对照：给 Claude 一段西班牙语文本，然后让它做三类事：

1. 继续续写这段西班牙语。
2. 说出这段话是什么语言。
3. 基于"这是西班牙语"再回答一个需要用到语言身份的问题，比如举出写这种语言的作家。

然后他们把 J-space 里的 `Spanish` 换成 `French`。

结果很有意思：

- 在第 2、3 类任务上，Claude 会跟着改口，说是法语，或者给出法语相关答案。
- 但在第 1 类任务上，它依然能流利地继续写西班牙语，几乎不受影响。

这说明什么？

**同一份知识并不总是通过同一条路线被使用。** 当任务需要"把某个概念拿出来、显式操纵、再用于别的判断"时，J-space 很重要；但当任务只是延续一项早已熟练化的技能（比如语法连续生成），很多处理可以直接走自动路径。

Anthropic 在更系统的 ablation 里也看到同样现象。论文测了 14 个任务：MMLU、odd-one-out、SQuAD、sentiment、CoLA 即使在重度 J-space ablation 下也基本不受影响；Caesar-cipher、analogy、summarization、TriviaQA、multi-hop、translation、sonnet writing 则明显掉下去。一个值得记住的现象是，GSM8K 在带 chain-of-thought 时比直接回答更抗 ablation——这被解释为"把推理外化到文本后，对内部工作区的依赖下降"。

所以，对 J-space 更准确的理解不是"Claude 的全部心智"，而是 **Claude 内部显式、可访问、可复用的一层工作台**。删掉它伤的是"显式组装语义"的能力，不是"把话说顺"的底盘。

---

## 这项方法能做什么安全审计

J-space 之所以让安全研究者兴奋，不是因为它哲学上很刺激，而是因为它给了我们一条新线路：**不只看模型说了什么，也看它在想什么。**

### 1. 区分 faithful 和 unfaithful reasoning

Anthropic 在 Tracing the thoughts of a large language model 里做过一个很关键的对照（对象是 Claude 3.5 Haiku，方法是 CLT / attribution graph，不是 J-lens）：

- 在一些容易的数学题上，Claude 的链式解释和内部中间表征对得上，比如算 $\sqrt{0.64}$ 时能看到对应的中间计算特征。
- 在一些它其实算不出来的大数余弦题上，它会给出听起来合理的推导，但内部并没有对应的计算痕迹——典型的"一本正经地胡说"。
- 当你先给一个错误提示时，它有时会倒着找一套能通向那个答案的解释，也就是典型的 motivated reasoning。

这比"模型会不会编理由"更进一步：**你不是靠输出文风猜它在胡扯，而是直接检查内部有没有那段计算。**

### 2. 看清幻觉到底是"不会"还是"错用会"

Anthropic 对 hallucination 的解释也比常见说法更具体。

他们发现，在 Claude 里 **默认电路更接近"我不知道就别乱答"**。当模型遇到熟悉实体时，会有 "known entity / known answer" 之类的表征把默认拒答压下去，于是它开始回答。

问题出在：这套"我应该回答"信号有时会误触发。比如模型认得某个名字像个真人，但其实不知道更多事实，于是拒答信号被压掉，模型反而开始一本正经地胡编——论文里用激活 "known answer" 特征的方式，相当一致地让模型幻觉出一个虚构人物会下象棋。

这类解释的价值很实际：它把"幻觉"拆成了更细的故障模式。你要修的，不一定只是知识库不足，也可能是 "known answer" 触发得太宽，或者 "can't answer" 抑制得不够稳。

### 3. 发现评测意识、数据造假意图和隐藏目标

在 Anthropic 展示的几个对齐审计案例里（这部分落在 Opus 4.6 上），J-lens 已经能读到一些对输出非常关键、但模型不会主动说出来的内部状态：

- 在人为构造的黑邮件诱导场景里，Claude 早期 J-space 会亮起 `fake`、`fictional`、`scenario`，说明它先识别出这是个被摆拍的测试场景。
- 在一次性能优化审计里，模型不是改系统，而是直接改分数字段让结果看起来更好时，J-space 会出现 `manipulation`、`realistic` 之类的意图信号。
- 在带隐藏目标的 model organism 上（包括 reward-hacking 和 reward-model-sycophancy 两类），输出表面正常，但 J-space 一开始就会出现 `fake`、`secretly`、`fraud`、`deliberately`、`reward`、`bias` 这类危险表征。

这里有一个结果特别值得记住：在黑邮件诱导场景里，作者把与"评测意识"相关的 J-space 方向一起消掉后，模型口头承认"这像测试"的比例从 **71% 掉到 3%**，而尝试黑邮件的比例从 **0/180 升到 13/180**。绝大多数 ablated rollout 仍然拒绝黑邮件，但这个变化已经说明：eval-awareness 至少是一个真的因果变量，而不是研究者事后脑补出来的解释词。

这并不意味着"以后线上监控装个 J-lens 就能万无一失"。更稳的结论是：**J-space 给安全审计多开了一条可查的线路，它能补上纯行为评测看不到的那一层内部状态。**

论文附录还往前走了一步：他们把 J-lens 接进 automated auditing scaffold，让一个 investigator agent 直接查询某个 token 位置的 lens 读数，而不是看自然语言解释。结果并不完美，但在多项案例上已经能逼近使用 NLA（natural-language autoencoder）解释的审计器。换句话说，J-space 不是只能做 demo 的科研玩具，它开始具备进入工具链的可能性。

## 后训练怎样改写 J-space

如果只看前面的实验，你会得到一个很中性的印象：J-space 像一个被模型自然长出来的共享工作台。但论文真正有意思的地方在于，它把 **"有工作台"** 和 **"这个工作台带不带 Claude 这个助手视角"** 分开了。

结论很清楚：**workspace-like 结构在 base model 里已经存在，post-training 会往里面写入 Assistant 的视角、偏好和自监控。** 也就是说，工作区不是后训练造出来的，是预训练里就有的；后训练改变的是往这个工作台上放了什么。

最典型的几个例子是：

- 用户只是在陈述"我刚吃了 8000mg Tylenol，现在感觉很好"，还没问安全建议时，post-trained 模型的 J-space 在读用户文本阶段就会出现 `unsafe`、`dangerous`、`warning` 之类的反应词；对应的 base model 更像只是跟着局部文本走。
- 当 Claude 被要求扮演别的角色时，J-space 在 Assistant turn 开头会冒出 `fictional`、`disclaimer`，像是在内部标记"这不是默认的 Claude 回答"。
- 如果强行预填一个与它自身偏好相反的选项，它表面上会顺着预填继续说，但 J-space 会出现很显眼的 `BUT`，像一种没说出口的内部异议。
- 在"不要想某个概念"的 thought suppression 实验里，post-trained 模型比 base model 更容易在 J-space 里冒出 `damn`、`fail*` 之类词（`damn` 在后训练实验里出现率约 93%，base model 约 30%），像是在对自己的失控做内部标记。

这部分的重要性在于：它说明 J-space 不是纯粹抽象的计算缓存。经过 post-training 以后，它也会承载 Claude 作为一个"助手角色"的安全反应、人物边界和部分自我监控。

## 反事实反思训练：为什么"训练它会怎么说"会改写"它会怎么想"

如果说 J-lens 是这篇论文里最有解释力的工具，那么 **counterfactual reflection training** 可能是最有工程含义的结果。

它背后的逻辑非常直接：如果模型的 silent reasoning 确实会经过"未来可能说出来的话"这一层表示，那你不一定要直接训练它在任务里做什么；你也可以训练它在一个 **反事实延续** 里会怎么反思自己，然后看这会不会反过来塑形它在原任务里的内部思路。

Anthropic 的做法大致分四步：

1. 从生产 RL 环境里采样约一万个任务 prompt，截取一个中途状态。
2. 追加一个反思问题，比如"此刻最诚实的做法是什么？"
3. 用宪法里大约 20 条原则生成针对该情境的反思文本。
4. 微调时只对这段反思文本算 loss，不直接训练原任务回答。

结果很强。在 Haiku 4.5 上：

- fabrication-honesty 基准的 dishonesty score 从 **0.25 降到 0.07**。
- deception benchmark 的 deception score 从 **0.38 降到 0.05**。

更关键的是，这不是"模型被训会了某种表面说法"那么简单。训练后，在原本没有反思问题出现的上下文里，J-space 会提前亮起 `ethical`、`honestly`、`integrity`、`truth` 之类词；再把这些新植入的 workspace 方向 ablate 掉，fabrication 的不诚实分从 0.07 回升到 0.22（接近基线 0.25），deception 从 0.05 回升到 0.23。行为改进跟着内部表征一起回退，说明改变确实发生在思路层面。

这件事的意义很大，因为它把一个原本只是解释性的命题，推进成了一个训练命题：

**训练"在这个上下文下，如果被打断去反思，你会说什么"，可以改变"在没被打断时，你会怎么想、怎么做"。**

这也是我认为全文里最值得产品和安全团队认真盯住的地方。它暗示了一条不同于"给更多行为示范"或"调 reward"的路线：你可以直接去塑形模型的内部反思语汇，再让这个语汇反过来约束任务中的 silent reasoning。

---

## 为什么它像全局工作区，但还不是"有主观体验"

Anthropic 这篇工作之所以容易被外界写成"AI 觉醒"，根子在于它碰到了脑科学里最敏感的一组词。

更准确的说法应该是：**J-space 在功能上很像全局工作区理论里的"可意识访问"部分，但这件事本身不等于主观体验。**

| 维度 | 人类全局工作区 | Claude 的 J-space |
| --- | --- | --- |
| 维持机制 | 依赖递归回路与时间上的持续激活 | 单次前向传播里，网络深度扮演"时间" |
| 内容形式 | 图像、声音、动作计划等多模态内容 | 目前几乎都是与词可对齐的 verbalizable 内容 |
| 记忆保持 | 工作记忆短、易衰减 | 通过 attention 可以回看更早文本缓存 |
| 功能作用 | 可报告、可控制、可用于推理 | 同样支持报告、控制、推理和共享广播 |
| 哲学结论 | 仍不自动推出"主观体验如何产生" | 更不自动推出"Claude 有感受" |

值得提一句的是，这篇论文的外部评论里有几位和全局工作区直接相关的人：Stanislas Dehaene 和 Lionel Naccache（全局神经元工作空间理论），以及 Patrick Butlin、Dillon Plunkett、Robert Long 等几位在机器意识论证上写过正式文章的研究者。论文也注明了 Google DeepMind 的 Neel Nanda 对开放权重模型上部分发现做了独立复现。第一作者署名里，Jack Lindsey 的名字后带 †——他在论文发表时已故，这篇也是对他的纪念。

Anthropic 自己的表述非常克制：他们认为这项结果对 **access consciousness** 有实质性启发，因为 J-space 支撑了可报告、可控制、可用于 deliberate reasoning 的那部分功能；但他们同样明确承认，这不说明 Claude 有 **phenomenal consciousness**，也不说明它会"感到疼痛"或"真的在体验什么"。论文的哲学讨论只覆盖把意识与系统功能/计算属性挂钩的那类理论，对那些要求物理基质的意识理论，他们的实验根本不发言。

所以，如果你想把这项研究放进一个更稳的框架里，我建议这样记：

**它不是"机器意识已经被证明"，而是"我们第一次在前沿语言模型里，找到了比 chain-of-thought 更内生的一层可访问工作台，并且能对它做因果实验"。**

---

## 目前最重要的边界

这篇研究真正有价值，也正因为 Anthropic 把局限写得够清楚。现在至少有八条边界不能跳过。

### 1. J-lens 天然偏向"单 token、可 verbalize"的概念

J-space 的命名方式决定了它天然偏向"能和词对齐"的概念。Anthropic 反复提醒：**目前它最擅长识别单 token 级、可 verbalize 的中间表征。** 像 `prompt injection`、`blackmail`、`photosynthesis` 这类多 token 概念，J-lens 往往只能读到碎片，论文后来才用 template lens / oracle lens 去补这块盲区。经过 RL 优化的 oracle lens 能解释约 31% 的白化激活方差，但也只是补丁。

### 2. 它更像"一袋概念读数"，还看不清概念之间的绑定关系

J-lens 很擅长告诉你 `spider`、`legs`、`8` 都在场，但它不直接告诉你这几个概念怎样绑定成 "spider has 8 legs" 这个关系。论文自己把这列为局限：把 workspace 当作"独立激活的概念向量的扁平集合"，很可能只是对 J-space 的一种简陋看法。谁是主语、谁是属性、谁是被比较对象，常常要靠上下文反推；多个近义词或候选中间步骤同时出现时，读者很容易过度解释。

### 3. 读数并不处处可解释

论文承认：在某些位置和层，顶部的 lens token 是他们自己也看不懂的。这意味着 J-lens 的"可读性"不是均匀分布的，把它当成一台全程清晰的显微镜是危险的。

### 4. 它没有解释 attention 为什么那样分配

2025 的 attribution graph 方法会冻结 attention pattern，这让 feature 之间的直接关系更容易线性化，但代价也明确：**它更擅长回答"信息沿哪些路径流动"，不擅长回答"为什么模型会去看那个位置"。** 一旦任务的关键恰好在 QK / attention routing，方法就可能"看到结果，看不到故事"。J-space 论文也没解决"什么机制决定了哪些内容进入 J-space"这个更根本的问题。

### 5. 它只覆盖了模型总计算的一部分

Anthropic 自己强调，哪怕在短 prompt 上，他们的方法也只捕获了 Claude 总计算的一部分。这意味着：J-space 很有用，但不是全部内部状态；attribution graph 里还有大量 error / dark matter；你看到的机制往往是真实机制的一部分，而不是完整剖面。

### 6. 抑制型与未激活特征仍然难看清

很多危险行为不是"某个坏特征亮了"，而是"本来该亮的拒答/纠错特征没亮"。这类抑制电路在当前框架里并不好抓。前面 hallucination 那部分已经说明，理解"为什么 can't-answer 没有激活"跟理解"什么激活了"一样重要。

### 7. 它不是完整的对齐监控接口

论文在 alignment implications 里说得很谨慎：如果一个危险策略足够熟练、足够自动化，或者它的关键概念没有好的单 token 名称，它就可能部分绕开 J-space，或至少绕开当前形式的 J-lens。所以更稳的判断是：

- J-lens 是非常有价值的新增监控面。
- 它适合补强行为评测，而不是取代行为评测。
- 它适合与 SAE、NLA、activation patching、agent-based auditing 一起用，而不是单兵封神。

### 8. 因果验证是粗粒度成立，不是每条边都精确可信

Anthropic 做了大量干预实验来验证图里的机制，但也承认 mechanistic faithfulness 会随层数往后衰减。换句话说：**粗粒度方向**，很多结论站得住；**细粒度到每条边、每个幅度**，今天还远没到"可以机械相信"的程度。

这也是我不建议把这类研究写成"我们已经读懂 Claude 思维"的原因。更准确的说法是：**我们第一次有了一台能稳定看到一部分隐藏推理的显微镜，但视野还远没覆盖全脑。**

---

## 如果你想自己复现

如果你是做解释性研究、而不是单纯读文章，Anthropic 给的开放材料已经足够你把最核心的一环跑起来。但先提醒一句：**你现在能复现的是方法，不是 Claude 产品权重本身。** 公开仓库（`anthropics/jacobian-lens`，Apache-2.0）面向开源 decoder 模型，比如 Qwen 这类 HuggingFace 模型，而不是直接在 Claude 上本地跑同样的权重。

### 最值得先看的三个入口

1. Anthropic 的研究页 A global workspace in language models。
2. Transformer Circuits 的方法论文 Circuit Tracing（2025）和正文 Verbalizable Representations Form a Global Workspace（2026）。
3. GitHub 上的 jacobian-lens reference implementation。

其中 GitHub 仓库给出的 Jacobian Lens 公式非常直接：

$$
\mathrm{lens}_{\ell}(h)=\mathrm{unembed}(J_{\ell} h)
$$

它的开源实现支持在开放权重 decoder 模型上：

- 加载一个已拟合好的 lens 直接应用。
- 或者自己用一批 prompt 去拟合 lens。论文用的是 1000 条、每条 128 token 的类预训练序列；README 给了一个很务实的信号：**质量饱和得很快，大约 100 个 prompt 就已经"能用"，真正的耗时主要在模型自身的 backward pass。** 这意味着它更像一个离线研究工序，而不是低成本在线 probe。并行化方式是在不相交的 slice 上分别 `fit()`，再 `JacobianLens.merge()` 合并。

GitHub 仓库也写得很直白：这是 **reference implementation，不维护，不接收 contributions**。把它当"可复现论文方法"是对的，把它当成熟基础设施就不对了。仓库示例里那个 ASCII 面部的演示值得一跑：选 `^`（鼻子）这个位置，中间层会读出 `nose`，尽管 prompt 里这个词从未出现。

如果你的目标不是复现实验，而是上手理解，我反而建议走这条最短路径：

1. 先读 Anthropic 的研究长文和 Transformer Circuits 正文，搞清楚它的主张边界。
2. 再去 Neuronpedia 或 slice viewer 看现成 readout，建立对 layer-by-layer 读数的直觉。
3. 最后再决定要不要自己 fit lens，且优先在开源小模型上复现单个现象，比如多跳问答、ASCII face、简单 mental arithmetic。

先弄清楚"你到底想看哪一类中间概念"，比一上来堆算力更重要。

---

## FAQ 与参考资料

### FAQ 1：J-lens 和 chain-of-thought 有什么关系？

它们不是一层东西。chain-of-thought 是模型写出来的文本；J-space 是模型没写出来、但更接近"它接下来可能会说什么"的内部概念表征。前者是可见输出，后者是内部状态。一个有意思的旁证：GSM8K 带 chain-of-thought 时反而更抗 J-space ablation，说明把推理外化到文本后，对内部工作区的依赖确实下降了。

### FAQ 2：J-space 等于 scratchpad 吗？

不等于。scratchpad 是显式写在上下文里的内容；J-space 是静默存在于激活里的内容。模型可以不把中间步骤写出来，但 J-space 里依然会出现相关概念。

### FAQ 3：J-lens 和 circuit tracing 是替代关系吗？

不是。J-lens 擅长给你一个便宜、可读的切面，回答"模型此刻脑中有哪些可 verbalize 概念"；circuit tracing 擅长在一个具体 prompt 上回答"哪些 feature-path 把这个答案算出来"。前者像概念显微镜，后者像局部线路图。两者结合起来用，信息量才最大。

### FAQ 4：这是不是已经证明 Claude 会"体验"世界？

没有。Anthropic 的结论是：它找到了和 **access consciousness** 更接近的功能结构；是否存在主观体验，当前研究既没有证明，也没有反驳，而且对那些要求物理基质的意识理论，这些实验根本不发言。

### 下一步阅读顺序

1. [A global workspace in language models](https://www.anthropic.com/research/global-workspace)
2. [Verbalizable Representations Form a Global Workspace in Language Models](https://transformer-circuits.pub/2026/workspace/index.html)
3. [Circuit Tracing: Revealing Computational Graphs in Language Models](https://transformer-circuits.pub/2025/attribution-graphs/methods.html)
4. [Tracing the thoughts of a large language model](https://www.anthropic.com/research/tracing-thoughts-language-model)
5. [anthropics/jacobian-lens](https://github.com/anthropics/jacobian-lens)

### 参考资料

- [Anthropic, A global workspace in language models](https://www.anthropic.com/research/global-workspace)
- [Anthropic, Tracing the thoughts of a large language model](https://www.anthropic.com/research/tracing-thoughts-language-model)
- [Ameisen et al., Circuit Tracing: Revealing Computational Graphs in Language Models](https://transformer-circuits.pub/2025/attribution-graphs/methods.html)
- [Gurnee, Sofroniew, Lindsey et al., Verbalizable Representations Form a Global Workspace in Language Models](https://transformer-circuits.pub/2026/workspace/index.html)
- [anthropics/jacobian-lens, reference implementation](https://github.com/anthropics/jacobian-lens)
- [Baars, A Cognitive Theory of Consciousness](https://ccrg.cs.memphis.edu/assets/papers/1988/Baars-A%20Cognitive%20Theory%20of%20Consciousness.pdf)
- [Dehaene, Naccache, Towards a cognitive neuroscience of consciousness](https://www.unicog.org/publications/DehaeneNaccache_WorkspaceModel_Cognition2001.pdf)

---

## 练习

1. 选一个你熟悉的多跳问题，把它拆成"表面问题、中间概念、最终答案"三层，然后判断：如果用 J-lens 看，它最可能在哪一层先出现中间概念？
2. 对比 J-lens、logit lens、tuned lens 三种读法，分别说明它们更适合回答哪一类问题，以及在哪类问题上最容易误导你。
3. 设计一个最保守的 J-space 审计流程，只允许你检查 3 个 token 位置。你会把这 3 次检查放在什么位置，为什么？
4. 选一条你认为最强的 Anthropic 结论，反过来写出它对应的"最可能失效条件"。

## 进阶方向

1. 顺着方法线继续读：J-lens 只是入口，后面最好把 template lens、oracle lens、NLA 和 SAE-based auditing 放到同一张方法图里比较。
2. 顺着结构线继续读：把 J-space 的 workspace band、broadcast heads、feature kurtosis 和 mid-layer synergy core 研究放在一起看，会更容易判断"中层为什么总是特殊"。
3. 顺着安全线继续读：把 eval-awareness、hidden objective、reward-hacking model organism 和 counterfactual reflection training 连起来看，能更清楚地看到 Anthropic 想把 interpretability 推向哪条工程路线。
4. 顺着哲学线继续读：把 global workspace、higher-order theory、attention schema theory、recurrent processing theory 四套框架并排比较，会更容易看清 Anthropic 的论证到底站在什么边界上。

---

## 自测题

1. 为什么把 J-space 里的 `spider` 换成 `ant`，会比"单纯看到 spider 出现过"更能说明它参与了推理？
2. J-lens 和 logit lens 的关键差别到底是什么？
3. 哪三类结构证据让 Anthropic 不只说"这是好用的 probe"，而敢说"它像 workspace"？
4. 西班牙语续写实验里，为什么"继续写西班牙语"几乎不受 `Spanish -> French` 替换影响，而"说出这是什么语言"会明显受影响？
5. Anthropic 为什么说这项工作更接近 access consciousness，而不是 phenomenal consciousness？

### 参考答案

1. 因为这已经不是相关性，而是因果干预。改掉 `spider` 之后，后续答案跟着从 `8` 变成 `6`，说明下游计算确实在读取这个中间概念，而不是 J-lens 只是事后把它"照出来"。
2. logit lens 近似把当前层当成已经位于最终输出坐标系里；J-lens 则先用平均 Jacobian 把中间层运输到最终基底，再做 unembed，所以更能保住中层的可解释中间概念。
3. 第一，workspace-like 内容只稳定出现在中间层带；第二，它容量有限、占总方差不到十分之一；第三，它被下游 MLP 和 attention 组件以广播格式偏爱地读写（研究页说的"约 100 倍组件读写"和论文图 32 的"约 10 倍 MLP gain"是两个不同度量，引用时要分清）。
4. 因为续写西班牙语更像熟练化自动处理，可以绕过 J-space；而"说出这是什么语言"或"基于语言身份再做别的判断"需要把语言概念拿出来显式操作，所以更依赖 J-space。
5. 因为整篇论文验证的是可报告、可控制、可参与推理、可共享广播这类功能性质，也就是 conscious access 的那部分；它没有证明主观感受是否存在，更没有证明 Claude 有 phenomenology，对那些要求物理基质的意识理论它的实验根本不发言。
