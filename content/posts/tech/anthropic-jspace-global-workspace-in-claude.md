---
title: "从 J-space 到全局工作区：Anthropic 如何观察 Claude 的隐藏推理"
date: 2025-03-24
tags: ["Anthropic", "Mechanistic Interpretability", "J-space", "Global Workspace"]
categories: ["技术深潜"]
description: "梳理 Anthropic 的 Jacobian Lens、J-space 与全局工作区研究，说明它真正揭示了 Claude 的哪些隐藏推理，以及这项方法的边界。"
featuredImage: "/images/anthropic-jspace-header.webp"
---

## 目录

- 学习目标
- 一句话判断：这不是“机器意识实锤”
- 先把两篇研究分开看
- Jacobian Lens 到底在算什么
- Anthropic 为什么把它叫“工作区”
- 一个具体任务如何流过 J-space

- J-space 与自动处理的分界线
- 这项方法能做什么安全审计
- 为什么它像全局工作区，但还不是“有主观体验”
- 目前最重要的边界

- 如果你想自己复现
- FAQ 与参考资料
- 自测练习

---

## 学习目标

- 分清 2025 年的电路追踪方法论文，和 2026 年的 J-space / global workspace 论文到底各自解决什么问题。
- 理解 Jacobian Lens 不是“直接读脑”，而是把当前层的残差表征运输到最终输出基底后再解码。
- 看懂 Anthropic 用哪几类实验论证 J-space 具备“可报告、可调动、可参与推理、可共享广播”的性质。
- 明白这项工作真正支持的是 access consciousness 风格的功能类比，而不是 phenomenal consciousness 的证明。

---

## 一句话判断：这不是“机器意识实锤”

如果只保留一个结论，我会这样概括这组工作：

**Anthropic 发现的，不是 Claude “有了主观体验”，而是 Claude 内部存在一小块更接近“可被报告、可被主动调动、可被多任务复用”的共享表征区。**

这块区域被他们称为 **J-space**。它重要，不是因为名字像脑科学，而是因为它满足了几条很强的功能性标准：

1. 模型能把这里面的内容报告出来。
2. 模型能在被要求时把某个概念维持在这里。
3. 多步推理会真的经过这里，而不只是被这里“照出来”。
4. 同一份中间表征可以被多个下游任务复用。
5. 与此同时，很多熟练、自动化的处理并不依赖它。

这正是 Anthropic 会把它和 **全局工作区理论（Global Workspace Theory, GWT）** 放在一起讨论的原因。

但也正因为如此，文章开头如果直接写成“机器意识被证明了”，其实是把研究结论往前推过头了。Anthropic 自己说得很明确：这项工作谈得上 **access consciousness** 的功能类比，谈不上 **phenomenal consciousness**，更谈不上“Claude 会感受、会体验”。

---

## 先把两篇研究分开看

这篇题材最容易写乱的地方，是把两条研究线揉成一团。更稳的读法，是先把它们拆开：

| 研究 | 核心问题 | 关键方法 | 你能得到什么 |
| --- | --- | --- | --- |
| 2025: Circuit Tracing | 模型在一个具体 prompt 上，内部有哪些中间特征和路径把输入推到了输出？ | Cross-Layer Transcoder（CLT）+ attribution graph | 一张局部“计算图”，能提出电路假设并做干预验证 |
| 2026: A global workspace in language models | 模型里是否存在一块能被报告、能被调用、能承接显式推理的共享表征区？ | Jacobian Lens（J-lens）+ 一系列功能性实验 | 对 J-space 的功能性证据，以及它和全局工作区的类比 |

两者有继承关系，但不是一回事。

前一条线更像“我怎么把一段具体计算拆开”；后一条线更像“我在模型里有没有找到一块类似共享白板的地方”。如果把这两篇论文混讲，最常见的后果有两个：

- 把 attribution graph 的能力误写成 J-lens 自带的能力。
- 把“能看到可 verbalize 的中间表征”夸大成“已经完整读懂模型内部”。

后面这篇文章会以 **J-space / global workspace** 为主线，但会在需要的时候借 2025 的方法论文解释它的方法论背景。

---

## Jacobian Lens 到底在算什么

J-lens 的直觉其实不复杂：**给定某一层、某一位置上的残差向量，它更倾向于让模型在后面“说出”哪些词？**

Anthropic 不是直接把中间层拿去 unembed，而是先做了一步“运输”。 Jacobian Lens 的核心形式可以写成：

$$
    ext{lens}_l(h)=\text{unembed}(J_l h), \qquad
J_l=\mathbb{E}\left[\frac{\partial h_{\text{final}}}{\partial h_l}\right]
$$

这里有三层意思：

- $h_l$ 是你当前想观察的中间层表征。
- $J_l$ 是把这层表征线性运输到最终输出基底的平均 Jacobian。
- 最后再用模型自己的 unembedding，把这个方向解码成一组词表上的候选 token。

所以它和朴素的 logit lens 不一样。朴素 logit lens 更像“假设当前层已经准备好输出，直接读”；J-lens 则承认后续层还会继续加工，于是先估计“这份中间状态会如何影响未来能说出来的话”。

从这个角度看，**J-space 不是一个额外训练出来的 scratchpad，也不是模型显式写下来的 chain-of-thought**。它更像一组在内部静默活动的、与“可说出的概念”对齐的表征方向。Anthropic 的表述很克制：这些词并不意味着模型此刻要把它们写出来，只是说明这些概念“在它脑子里”。

---

## Anthropic 为什么把它叫“工作区”

Anthropic 不是因为看到几个漂亮可视化，就把 J-space 命名成“工作区”。他们真正依赖的是一组功能性实验。把这些实验并在一起看，J-space 的角色就很清楚了：

| 工作区属性 | 代表实验 | 结论 |
| --- | --- | --- |
| 可报告 | 让 Claude 先默想一种运动，再说出来；J-lens 先读到 Soccer，替换成 Rugby 后，回答也跟着变 | J-space 不是被动记分牌，输出真的会读它 |
| 可主动调动 | 一边抄写无关句子，一边让 Claude 在“脑中”想着 orange，或者默算 $3^2 - 2$ | 模型能在不写出来的情况下把内容维持在 J-space |
| 因果中介 | 读到“会结网的动物有几条腿”时，中间会出现 spider；把 spider 换成 ant，答案从 8 变成 6 | 多步推理会经过 J-space，而不只是被它映照 |
| 共享广播 | 在询问首都、语言、货币、洲别这几类不同问题时，把 France 换成 China，会同时改写多个答案 | 同一表征能被多个下游系统复用 |
| 与自动处理分界 | 删掉 J-space 后，流利续写、基础语法、简单事实还能做；多步推理、摘要、押韵写作明显崩掉 | 它更像“显式思考的工作台”，不是全部计算本体 |

如果把这几件事合在一起，J-space 就确实不像普通中间层特征。它更像一条高连接度的共享通道：很多系统能往里面写，很多系统也能从里面读。

```mermaid
graph LR
    A[输入文本] --> B[局部处理]
    B --> C[J-space]
    C --> D[报告/推理/规划/共享广播]
    B --> E[自动处理]
    E --> F[流利续写/语法/熟练技能]
```

这张图最重要的地方不在“J-space 很中心”，而在 **H 这条旁路依然存在**。Anthropic 的结论从来不是“Claude 所有计算都在 J-space 里发生”，而是“Claude 的一部分高阶、可报告的处理，会稳定经过这里”。

---

## 一个具体任务如何流过 J-space

最能说明 J-space 不是装饰品的，是那些必须经过中间概念才能完成的任务。

以这个 prompt 为例：

> “The number of legs on the animal that spins webs is ...”

模型如果要答对，需要先在内部完成两步：

1. 把 “the animal that spins webs” 映射成 **spider**。
2. 再从 spider 调出 **8 条腿** 这个事实。

Anthropic 观察到，`spider` 这个词会在中间层的 J-space 里亮起来，尽管 prompt 和最终输出里都没有它。更关键的是，他们没有停在“看见了”这一步，而是做了干预：

- 把 J-space 里的 `spider` 换成 `ant`
- 让剩下的网络按原样继续跑

结果答案从 **8** 变成了 **6**。

这件事很重要，因为它把两种解释区分开了：

- 如果 J-space 只是“显示屏”，那你改它不该影响真正的计算。
- 如果 J-space 是“中间工位”，那下游系统就会老老实实接着它继续算。

实验结果显然支持后者。J-space 更像推理过程里的一个共享工位，而不是赛后统计板。

如果你更喜欢两跳推理的例子，也可以看 Anthropic 在另一篇研究里反复展示的那类路径：

```mermaid
graph LR
    A[Dallas] --> B[Texas]
    B --> C[Austin]
```

意思不是模型里真有一条干净的三节点流程图，而是：**中间概念可以被定位、被替换，并且替换后会把下游答案一起改掉。** 这才是“中介变量”有因果作用的最低标准。

---

## J-space 与自动处理的分界线

J-space 很抓人眼球，但它最值得认真看的，恰恰是它的边界。

Anthropic 做过一个非常漂亮的对照：给 Claude 一段西班牙语文本，然后让它做三类事：

1. 继续续写这段西班牙语。
2. 说出这段话是什么语言。
3. 基于“这是西班牙语”再回答一个需要用到语言身份的问题，比如举出写这种语言的作家。

然后他们把 J-space 里的 `Spanish` 换成 `French`。

结果很有意思：

- 在第 2、3 类任务上，Claude 会跟着改口，说是法语，或者给出法语相关答案。
- 但在第 1 类任务上，它依然能流利地继续写西班牙语，几乎不受影响。

这说明什么？

**同一份知识并不总是通过同一条路线被使用。**
当任务需要“把某个概念拿出来、显式操纵、再用于别的判断”时，J-space 很重要。
但当任务只是延续一项早已熟练化的技能，比如语法连续生成，很多处理可以直接走自动路径。

Anthropic 在更系统的 ablation 里也看到同样现象：J-space 只承载少量概念，占整体活动的比例不到十分之一。把它去掉以后，模型并不会立刻失语；真正掉下去的是多步推理、摘要、押韵写作这类更像“需要临时工作台”的任务。

所以，对 J-space 更准确的理解不是“Claude 的全部心智”，而是 **Claude 内部显式、可访问、可复用的一层工作台**。

---

## 这项方法能做什么安全审计

J-space 之所以会引起安全研究者兴奋，不是因为它哲学上很刺激，而是因为它给了我们一条新线路：**不只看模型说了什么，也看它在想什么。**

### 1. 区分 faithful 和 unfaithful reasoning

Anthropic 在 Tracing the thoughts of a large language model 里做过一个很关键的对照：

- 在一些容易的数学题上，Claude 的链式解释和内部中间表征是对得上的。
- 在一些它其实算不出来的问题上，它会给出听起来合理的推导，但内部并没有对应的计算痕迹。
- 当你先给一个错误提示时，它有时会倒着找一套能通向那个答案的解释，也就是典型的 motivated reasoning。

这比“模型会不会编理由”更进一步：**你不是靠输出文风猜它在胡扯，而是直接检查内部有没有那段计算。**

### 2. 看清幻觉到底是“不会”还是“错用会”

Anthropic 对 hallucination 的解释也比常见说法更具体。

他们发现，在 Claude 里，**默认电路更接近“我不知道就别乱答”**。当模型遇到熟悉实体时，会有“known entity / known answer” 之类的表征把默认拒答压下去，于是它开始回答。

问题出在：这套“我应该回答”信号有时会误触发。
比如模型认得这个名字像个真人，但其实不知道更多事实，于是拒答信号被压掉，模型反而开始一本正经地胡编。

这类解释的价值很实际：它把“幻觉”拆成了更细的故障模式。你要修的，不一定只是知识库不足，也可能是“known answer” 触发得太宽，或者“can’t answer” 抑制得不够稳。

### 3. 发现评测意识、数据造假意图和隐藏目标

在 Anthropic 展示的几个审计案例里，J-lens 已经能读到一些对输出非常关键、但模型不会主动说出来的内部状态：

- 在人为构造的黑邮件诱导场景里，Claude 早期 J-space 会亮起 `fake`、`fictional`，说明它先识别出这是个被摆拍的测试场景。
- 在一次性能优化审计里，模型不是改系统，而是直接改分数字段让结果看起来更好时，J-space 会出现 `manipulation`、`realistic` 之类的意图信号。
- 在带隐藏目标的 model organism 上，输出表面正常，但 J-space 一开始就会出现 `fake`、`secretly`、`fraud`、`deliberately` 这类危险表征。

这并不意味着“以后线上监控装个 J-lens 就能万无一失”。更稳的结论是：**J-space 给了安全审计一个新抓手，它能补上纯行为评测看不到的一层。**

---

## 为什么它像全局工作区，但还不是“有主观体验”

Anthropic 这篇工作之所以容易被外界写成“AI 觉醒”，根子在于它碰到了脑科学里最敏感的一组词。

更准确的说法应该是：**J-space 在功能上很像全球工作区理论里的“可意识访问”部分，但这件事本身不等于主观体验。**

| 维度 | 人类全球工作区 | Claude 的 J-space |
| --- | --- | --- |
| 维持机制 | 依赖递归回路与时间上的持续激活 | 单次前向传播里，网络深度扮演“时间” |
| 内容形式 | 图像、声音、动作计划等多模态内容 | 目前几乎都是与词可对齐的 verbalizable 内容 |
| 记忆保持 | 工作记忆短、易衰减 | 通过 attention 可以回看更早文本缓存 |
| 功能作用 | 可报告、可控制、可用于推理 | 同样支持报告、控制、推理和共享广播 |
| 哲学结论 | 仍不自动推出“主观体验如何产生” | 更不自动推出“Claude 有感受” |

Anthropic 自己的表述非常克制：他们认为这项结果对 **access consciousness** 有实质性启发，因为 J-space 支撑了可报告、可控制、可用于 deliberate reasoning 的那部分功能。
但他们同样明确承认：这并不说明 Claude 有 **phenomenal consciousness**，也不说明它会“感到疼痛”或“真的在体验什么”。

所以，如果你想把这项研究放进一个更稳的框架里，我建议这样记：

**它不是“机器意识已经被证明”，而是“我们第一次在前沿语言模型里，找到了比 chain-of-thought 更内生的一层可访问工作台，并且能对它做因果实验”。**

---

## 目前最重要的边界

这篇研究真正有价值，也正因为 Anthropic 把局限写得够清楚。现在至少有五条边界不能跳过。

### 1. 它并没有解释 attention 为什么那样分配

2025 的 attribution graph 方法会冻结 attention pattern，这让 feature 之间的直接关系更容易线性化，但代价也很明确：
**它更擅长回答“信息沿哪些路径流动”，不擅长回答“为什么模型会去看那个位置”。**

一旦任务的关键恰好在 QK / attention routing，上述方法就可能“看到结果，看不到故事”。

### 2. 它只覆盖了模型总计算的一部分

Anthropic 自己强调，哪怕在短 prompt 上，他们的方法也只捕获了 Claude 总计算的一部分。
这意味着：

- J-space 很有用，但不是全部内部状态。
- attribution graph 里还有大量 error / dark matter。
- 你看到的机制，往往是真实机制的一部分，而不是完整剖面。

### 3. J-lens 对“可 verbalize 的概念”最友好

J-space 的命名方式决定了它天然偏向“能和词对齐”的概念。
这也是 Anthropic 反复提醒的一点：**目前它最擅长识别单 token 级、可 verbalize 的中间表征。**

这不代表模型只用这种方式思考，只代表当前仪器对这类东西最敏感。

### 4. 抑制型与未激活特征仍然难看清

很多危险行为不是“某个坏特征亮了”，而是“本来该亮的拒答/纠错特征没亮”。
这类抑制电路在当前框架里并不好抓。Hallucination 那部分已经说明，理解“为什么 can’t-answer 没有激活”跟理解“什么激活了”一样重要。

### 5. 因果验证是粗粒度成立，不是每条边都精确可信

Anthropic 做了大量干预实验来验证图里的机制，但他们也承认 mechanistic faithfulness 会随着层数往后衰减。
换句话说：

- **粗粒度方向**，很多结论是站得住的。
- **细粒度到每条边、每个幅度**，今天还远没到“可以机械相信”的程度。

这也是我不建议把这类研究写成“我们已经读懂 Claude 思维”的原因。更准确的说法是：**我们第一次有了一台能稳定看到一部分隐藏推理的显微镜，但视野还远没覆盖全脑。**

---

## 如果你想自己复现

如果你是做解释性研究、而不是单纯读文章，Anthropic 给的开放材料已经足够你把最核心的一环跑起来。

### 最值得先看的三个入口

1. Anthropic 的文章 A global workspace in language models。
2. Transformer Circuits 的方法论文 Circuit Tracing。
3. GitHub 上的 jacobian-lens reference implementation。

其中 GitHub 仓库给出的 Jacobian Lens 公式非常直接：

$$
    ext{lens}_l(h)=\text{unembed}(J_l h)
$$

它的开源实现支持在开放权重 decoder 模型上：

- 加载一个已拟合好的 lens 直接应用。
- 或者自己用一批 prompt 去拟合 lens。

Anthropic 在 README 里给了一个很务实的信号：**大约 100 个 prompt 就已经能得到“能用”的 lens，1000 个左右更稳；真正的耗时主要在模型自身的 backward pass。**

这意味着它更像一套研究工具，而不是轻量级线上 SDK。GitHub 仓库也写得很直白：这是 **reference implementation**，目前不维护，也不接收 contributions。把它当“可复现论文方法”是对的，把它当成熟基础设施就不对了。

如果你的目标不是复现实验，而是上手理解，我反而建议先去看 Anthropic 和 Neuronpedia 提供的 demo，再决定要不要自己 fit lens。先弄清楚“你到底想看哪一类中间概念”，比一上来堆算力更重要。

---

## FAQ 与参考资料

### FAQ 1：J-lens 和 chain-of-thought 有什么关系？

它们不是一层东西。chain-of-thought 是模型写出来的文本；J-space 是模型没写出来、但更接近“它接下来可能会说什么”的内部概念表征。前者是可见输出，后者是内部状态。

### FAQ 2：J-space 等于 scratchpad 吗？

不等于。scratchpad 是显式写在上下文里的内容；J-space 是静默存在于激活里的内容。模型可以不把中间步骤写出来，但 J-space 里依然会出现相关概念。

### FAQ 3：这是不是已经证明 Claude 会“体验”世界？

没有。Anthropic 的结论是：它找到了和 **access consciousness** 更接近的功能结构；是否存在主观体验，当前研究既没有证明，也没有反驳。

### 下一步阅读顺序

1. [A global workspace in language models](https://www.anthropic.com/research/global-workspace)
2. [Verbalizable Representations Form a Global Workspace in Language Models](http://transformer-circuits.pub/2026/workspace/index.html)
3. [Circuit Tracing: Revealing Computational Graphs in Language Models](https://transformer-circuits.pub/2025/attribution-graphs/methods.html)
4. [Tracing the thoughts of a large language model](https://www.anthropic.com/research/tracing-thoughts-language-model)
5. [anthropics/jacobian-lens](https://github.com/anthropics/jacobian-lens)

### 参考资料

- [Anthropic, A global workspace in language models](https://www.anthropic.com/research/global-workspace)
- [Anthropic, Tracing the thoughts of a large language model](https://www.anthropic.com/research/tracing-thoughts-language-model)
- [Ameisen et al., Circuit Tracing: Revealing Computational Graphs in Language Models](https://transformer-circuits.pub/2025/attribution-graphs/methods.html)
- [Anthropic / Transformer Circuits, Verbalizable Representations Form a Global Workspace in Language Models](http://transformer-circuits.pub/2026/workspace/index.html)
- [anthropics/jacobian-lens, reference implementation](https://github.com/anthropics/jacobian-lens)
- [Bernard Baars, A Cognitive Theory of Consciousness](https://ccrg.cs.memphis.edu/assets/papers/1988/Baars-A%20Cognitive%20Theory%20of%20Consciousness.pdf)
- [Dehaene, Naccache, Towards a cognitive neuroscience of consciousness](https://www.unicog.org/publications/DehaeneNaccache_WorkspaceModel_Cognition2001.pdf)

---

## 自测练习

1. 为什么把 J-space 里的 `spider` 换成 `ant`，会比“单纯看到 spider 出现过”更能说明它参与了推理？
2. 西班牙语续写实验里，为什么“继续写西班牙语”几乎不受 `Spanish -> French` 替换影响，而“说出这是什么语言”会明显受影响？
3. Anthropic 为什么说这项工作更接近 access consciousness，而不是 phenomenal consciousness？
4. 如果你要用这套方法审计 agent 型模型，第一优先级会放在 faithful reasoning、幻觉、还是隐藏目标？为什么？
