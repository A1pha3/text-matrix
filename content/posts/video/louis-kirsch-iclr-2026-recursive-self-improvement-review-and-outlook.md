---
title: "逃逸速度：Louis Kirsch 在 ICLR 2026 怎么讲递归自我改进的拐点"
date: 2026-07-13T21:30:00+08:00
slug: louis-kirsch-iclr-2026-recursive-self-improvement-review-and-outlook
description: "ICLR 2026 RSI Workshop 首场受邀报告精读。据 43 页幻灯片原件重建：Louis Kirsch 没有宣称逃逸速度已经到来，他真正讲的是三件事——怎么把人类移出 AI 研究的外层循环、用哪几类机制保证自我改进不是自欺、以及拐点之前还剩哪些硬骨头。本文删除了此前流传但并不在幻灯片里的'5 判据'叙事，补上了 Darwin/Huxley-Gödel Machine 与 Inherent 的'集体递归自我改进'展望。"
draft: false
categories: ["视频精读"]
tags: ["ICLR2026", "RecursiveSelfImprovement", "LouisKirsch", "Schmidhuber", "GödelMachine", "DarwinGödelMachine", "FME", "Inherent", "AIAgent", "Frontier"]
hiddenFromHomePage: true
---

> **目标读者**：AI 研究者、AGI 安全与对齐从业者、关注 AI4Science 的工程师与产品经理
> **这篇文章的判断**：Kirsch 这场报告的分量不在某个新算法，而在于把"递归自我改进"从一句吓人的口号，拆成三个能分头讨论的工程问题——把人移出外层循环、保证每次改动是真改进、以及拐点之前那堆没解决的开放难题。
> **难度**：⭐⭐⭐⭐ | **来源**：B站 @至高机器智能 转 Louis Kirsch @ ICLR 2026 RSI Workshop 首场受邀报告

[原视频链接（B站）](https://www.bilibili.com/video/BV1YRVy6nEzT/?spm_id_from=333.337.search-card.all.click&vd_source=fda86480434b6573c5b58707deda68d9) ｜ [演讲幻灯片 PDF（43 页）](https://louiskirsch.com/assets/louis_at_the_recursive_workshop_ICLR_2026.pdf) ｜ [SlidesLive 录像](https://slideslive.com/39063672?t=1425) ｜ [RSI 2026 Workshop 主页](https://recursive-workshop.github.io/) ｜ 时长 27:57 ｜ 现场 2026-04-26

---

## 视频信息卡

| 项目 | 内容 |
| ------ | ------ |
| 标题（B站转载） | 【Frontier】递归式自我提升：回顾和展望 \| ICLR 2026 \| Louis Kirsch |
| 演讲原始标题 | *Escape Velocity: The inflection point for Recursive Self-Improvement* |
| 场合 | ICLR 2026 RSI Workshop 首场受邀报告（Invited Talk 1，2026-04-26，里约热内卢 101-D 厅） |
| 演讲者 | Louis Kirsch —— IDSIA 博士（导师 Schmidhuber）；前 Google DeepMind「AI Scientist」团队创建者与负责人；现 Inherent 联合创始人兼 Chief Superintelligence Officer |
| 幻灯片 | 43 页，作者个人站公开 PDF（本文逐页核对） |
| 录像 | SlidesLive（含现场 Q&A） |
| B站 UP 主 | 至高机器智能 |
| 时长 | 27:57 |
| B站发布 | 2026-06-03 |
| 播放量 | 1271 |
| 点赞 / 投币 / 收藏 | 57 / 23 / 138 |
| 链接 | [bilibili.com/video/BV1YRVy6nEzT](https://www.bilibili.com/video/BV1YRVy6nEzT/) |

> **前置说明（写作依据，以及一处必须先讲的更正）**：ICLR 2026 的 RSI Workshop 自称"可能是全球第一个专门聚焦 RSI 的研讨会"，Kirsch 讲的是当天第一场受邀报告。本文依据其个人站公开的 43 页幻灯片原件（已逐页核对文本）、Workshop 官网、Kirsch 个人站与相关 arXiv 论文写成，**未拿到逐字字幕**，所有口头引用都是据幻灯片的综合转述。
>
> 有一点得先摆在前面：此前网络上（也包括本站更早的版本）流传过一套"RSI 五判据"——可修改范围、可信评估、可持续增长、资源有界、状态可读写，并说它出自这场演讲。**把 43 页幻灯片逐页核对之后，这五条一条都不在里面**，属于对演讲的误读。本文已据真实幻灯片重建框架。演讲里确实有一张"如何保证改进"的清单，但它讲的是另一回事（见第四节）。

## 目录

- [视频信息卡](#视频信息卡)
- [目录](#目录)
- [一、这场演讲到底在讲什么](#一这场演讲到底在讲什么)
- [二、从元学习到 agentic scientist：Kirsch 站在哪条脉络上](#二从元学习到-agentic-scientistkirsch-站在哪条脉络上)
- [三、RSI：把人类移出外层循环](#三rsi把人类移出外层循环)
- [四、真正的清单：怎么保证"自我改进"不是在自欺](#四真正的清单怎么保证自我改进不是在自欺)
- [五、FME：Kirsch 自己的赌注](#五fmekirsch-自己的赌注)
- [六、逃逸速度：一个还没跨过的拐点](#六逃逸速度一个还没跨过的拐点)
- [七、Lessons Learned：三条来自实战的教训](#七lessons-learned三条来自实战的教训)
- [八、Open Problems：拐点之前的硬骨头](#八open-problems拐点之前的硬骨头)
- [九、Kirsch 要把这条路带去哪：Inherent 与"集体递归自我改进"](#九kirsch-要把这条路带去哪inherent-与集体递归自我改进)
- [十、常见误读：这场演讲没有在说什么](#十常见误读这场演讲没有在说什么)
- [十一、给不同读者的落地建议](#十一给不同读者的落地建议)
- [十二、自测：你读懂真实框架了吗](#十二自测你读懂真实框架了吗)
- [十三、论文与资源地图](#十三论文与资源地图)
- [写作笔记（给后续读者）](#写作笔记给后续读者)

---

## 一、这场演讲到底在讲什么

Kirsch 开场先抛了一张 Schmidhuber 的老图：如果把人类历史上的重大里程碑排在时间轴上，它们大致落在一条指数曲线上，外推下去，收敛点落在 2040 年前后——Schmidhuber 半开玩笑地把那个收敛点记作 Ω，也就是超级智能。这张图不是论证，是一个坐标：它把整场演讲要谈的东西，钉在"通往 Ω 的最后一段路由什么驱动"这个问题上。

Kirsch 给的答案是两台咬合在一起的引擎：**AI 做 AI 研究**（自动化科研），和 **递归自我改进**（一个系统研究自己，产出一个更强的自己，再让更强的那个继续研究自己）。前者决定进步能不能被自动化，后者决定这种自动化能不能自我加速。剩下 20 多分钟，他就在这两台引擎上做三件事：先说清楚 RSI 怎么"把人移出外层循环"，再摆出一张"怎么保证自我改进是真的"的清单，最后交待哪些教训已经学到、哪些问题还悬着。

有一句话得替他强调，因为最容易被断章取义：**他没有说逃逸速度已经发生**。幻灯片里的原话恰恰相反——当前的 RSI 系统"过早地停止改进，仍然需要人类介入"。他所谓的逃逸速度，是那个"人类不再需要亲自推动进步"的拐点；他的判断是我们正在逼近它，不是已经越过它。整场报告的张力就在这里：技术栈在快速就位，可临界点还没到，中间缺的东西恰恰是最难的。

下面这张表把演讲的真实脉络和本文各节对上，方便你对照着看：

| 演讲脉络（据幻灯片） | 本文对应 |
| ------ | ------ |
| Ω 收敛 + 两台引擎：自动化科研 × 递归自我改进 | 第一节 |
| 从元学习到 agentic scientist 的路线 | 第二节 |
| RSI 定义：把人移出外层循环 | 第三节 |
| "如何保证改进"的五类机制 | 第四节 |
| FME：Kirsch 自己的机制 | 第五节 |
| 逃逸速度：还没跨过的拐点 + 怎么度量 | 第六节 |
| Lessons Learned：三条实战教训 | 第七节 |
| Open Problems：奖励、好奇心、可证明性 | 第八节 |
| 落到 Inherent 的"集体 RSI" | 第九节 |

---

## 二、从元学习到 agentic scientist：Kirsch 站在哪条脉络上

要听懂这场报告，先得知道 Kirsch 是从哪条路走上来的——这条路解释了他为什么把 RSI 讲成一个可以拆解的工程问题，而不是一句预言。

思想源头在 Schmidhuber 学派。RSI 这个念头本身可以追到 I. J. Good 1965 年的"智能爆炸"猜想，而把"系统改写自己"做成研究纲领的是 Schmidhuber：从 1987 年的自指学习硕士论文，到 2003 年提出 Gödel Machine（arXiv cs/0309048，后续还有 2007、2009 的修订版，Kirsch 在幻灯片里引的是后面这几版），再到用人工好奇心让系统自己造任务。有一个流传很广的坑顺手澄清：1987 那篇是硕士论文，是概念前驱，和 2003 年的 Gödel Machine 差着 16 年，不是同一样东西，中文二手资料经常把它们并成"1987 年 Gödel Machine"。

Kirsch 自己的工作是这条脉络往前的延伸，而且一路在把"元"这个前缀往上叠。他早期做元学习（meta-learning）：给定一批相似任务，学出一个能快速适应新任务的学习算法。接着往通用走——**MetaGenRL**（Kirsch et al. 2019）直接用神经网络去学一个能跨环境泛化的强化学习损失函数；**VSML**（2020）和 **GPICL**（2022）让网络在上下文里"就地"学习，甚至重新发现了反向传播。这些工作的共同母题，是把原本由人手工设计的那一层（损失函数、学习规则）交给系统自己去发现。演讲里那张"搜索空间"的幻灯片说的就是这件事：不同的 RSI 路线，区别只在于**把什么当成"可以被改的部分"**——是 RNN / Transformer 的权重，是一个 RL 损失函数，还是一个大模型加上它的"脚手架"（harness：提示词、代码、工具，乃至架构）。

到了 2023 年之后，这条线跟大模型合流，长成了"agentic scientist"。Kirsch 在幻灯片里点了一串名字：ML Agent Bench、MLE-Bench、OPRO、PromptBreeder，以及 GPTSwarm（Zhuge 2024）、ADAS（Hu et al. 2024）、Sakana 的 AI Scientist（Lu et al. 2024）、MLGym（Nathani et al. 2025）。共同点是让 LLM 智能体去跑"提假设—写代码—做实验—自审"的科研循环。值得留意的是这里的第一手视角：Kirsch 在 DeepMind **亲手创建并带过一个 AI Scientist 团队**，2025 年又全职去做 RSI 创业。所以他这张地图不是旁观者画的，是一个下过场的人画的——这也是为什么他后半程谈"教训"和"开放问题"时，比谈定义时更值得听。

> **一处顺带的更正**：网上不少解读说 Kirsch"反复引用 FunSearch 和 AlphaEvolve"。这两个是 RSI 邻域里很重要的系统，但**它们不在这 43 页幻灯片里**；他现场举的例子是上面那串（STOP、Darwin Gödel Machine、GPTSwarm、ADAS、Sakana AI Scientist、MLGym、EvoTune）。AlphaEvolve 出现在 Workshop 的参考文献列表里，不是他的演讲内容。

---

## 三、RSI：把人类移出外层循环

Kirsch 给 RSI 的定义很短：一个系统对自己做研究，产出一个更强的自己（幻灯片原话是 "a system that does research on itself to create an even better version of itself"）。关键在"更强"怎么理解。他画了一道梯子：最底下是人类手写更新规则，往上一层是元学习（meta-learning，系统学怎么更新自己），再往上是元-元学习（系统学"怎么学会更新自己"）……每往上爬一层，就从外层循环里拿掉一点人类的参与。RSI 就是把这道梯子推到底——用他幻灯片上的话说，目标是"最小化对人类工程的依赖"，一个 RSI 系统"能无界地改进自己的能力，且在需要时无需人类介入"。

这里有个容易被略过、却恰恰是整场报告最锋利的切割：**改进"表现"和改进"改进能力"是两回事**。一个模型微调完在某个 benchmark 上分数高了，这不算 RSI——除非它改完之后，做下一轮自我改进的能力也跟着变强了。普通 fine-tuning 停在前者，RSI 要的是后者。这个区别听着抽象，但 2025 年有两个系统把它做成了能测量的东西，正好当注脚：

- **Darwin Gödel Machine（DGM，Zhang et al. 2025，arXiv 2505.22954）**：它反复改写自己的代码，按论文的说法，这个过程"同时也在改进它改写自己代码库的能力"。它维护一个智能体存档，采样一个、用基础模型变异出一个"有意思的新版本"、再用编程 benchmark 实测，好的留下。这套开放式进化把 SWE-bench 从 20.0% 推到 50.0%、Polyglot 从 14.2% 推到 30.7%，全程带沙箱和人类监督。它对应的正是下一节那张"如何保证改进"清单里的"进化"一档。
- **Huxley-Gödel Machine（HGM，arXiv 2510.21614，Zhuge、Schmidhuber 等 KAUST 团队）**：它把这道切割顶到更精细的地方。作者发现了一个叫 **Metaproductivity-Performance Mismatch（元生产力—表现错配）** 的现象——一个智能体当下的 benchmark 分数，并不能预测它后代的自我改进潜力。于是他们不再用"当前分数"决定保留谁，而是用一个受赫胥黎"演化支（clade）"概念启发的指标 CMP：把一个智能体所有后代的表现聚合起来，当作它"自我改进潜力"的信号。用更少的 CPU 小时，HGM 在 SWE-bench 上追平了人类手工打造的顶尖编程智能体。

把这两个放一起看，就明白 Kirsch 为什么死抠"改进改进能力"这件事：如果你用错了信号（拿当前分数当潜力），你会在自我改进的树上一路选错枝，越走越窄。RSI 难就难在，你得优化一个你还测不准的东西。

（不用记住上面所有名字。记住一句就够——RSI 的门槛不是"变强"，是"变得更能变强"。）

---

## 四、真正的清单：怎么保证"自我改进"不是在自欺

如果这场报告里有一张最该被截图的幻灯片，是这张——标题叫 **Guaranteeing improvement**（如何保证改进），出处标着 Kirsch 博士论文《Automating AI Research》第 7 章。它回答的是一个具体到冒汗的问题：一个系统在改自己，你凭什么相信每次改动真的是改进，而不是它在自欺欺人？Kirsch 把已有的答案归成五类，每一类都是一种"用什么代价换什么保证"的赌注：

| 机制 | 代表系统 | 怎么保证"这次改动是改进" | 代价 / 边界 |
| ------ | ------ | ------ | ------ |
| 不做保证 | STOP（Self-Taught Optimizer，Zelikman et al. 2023） | 不设护栏，直接让模型改自己的脚手架 | 可能改坏，且没有回退 |
| 形式化证明 | Gödel Machine（Schmidhuber 2003，及后续修订） | 改动前先证明它会严格改进目标函数，证明通过才动手 | 现实里"证明大多数改动有益"几乎做不到 |
| 回滚有害改动 | Success Story Algorithm（Schmidhuber 1997） | 允许先改，但一旦后续表现变差就回退到历史检查点 | 需要一个可靠的"表现是否变差"判据 |
| 元编排 / 进化 | Darwin Gödel Machine（Zhang et al. 2025） | 维护智能体存档，采样—变异—用 benchmark 实测，留下好的 | 吃 benchmark 的可信度；探索开销大 |
| 按 fitness 分配算力 | Fitness Monotonic Execution（Kirsch & Schmidhuber 2022） | 给测得更好的解更多算力，让改进在期望意义上单调 | reward 从哪来仍是开放问题（见第八节） |

这张表比它看上去更有用。五行从上往下，其实是同一根轴上的滑块：**越往上越严格、越往下越实用**。Gödel Machine 给你数学级别的保证，代价是它在现实里几乎跑不起来；STOP 什么都不保证，换来的是立刻能用。中间那三档——回滚、进化、按 fitness 分配算力——才是 2025 年真正在跑的东西，因为它们放弃了"每一步都可证明"，改成"允许犯错，但留一套机制把错的收回来"。

所以，面对一个号称会自我改进的系统，别问它"聪不聪明"，问它这一条：**你落在这五行的哪一行？** 停在"不做保证"那档的系统，跟一个会不小心把自己改崩、还没有 Ctrl+Z 的脚本没有本质区别。这张表，而不是那套并不存在的"五判据"，才是这场演讲真正留下的清单。

---

## 五、FME：Kirsch 自己的赌注

上面那张表的最后一行——按 fitness 分配算力——是 Kirsch 自己押的方向，全名叫 **Fitness Monotonic Execution（FME，适应度单调执行）**，出自他和 Schmidhuber 2022 年那篇 [Eliminating Meta Optimization Through Self-Referential Meta Learning](https://arxiv.org/abs/2212.14392)（arXiv 2212.14392），博士论文第 7 章有完整版。他用了三页幻灯片专门讲它，值得单独拆开。

FME 想拆掉的是"外层元优化器"这个部件。传统做法里总有一个固定的外层优化器规定"元参数该怎么改"，这个外层越强、成本越高，而且它本身没法被系统改进。FME 的思路是把它整个去掉：让系统沿时间展开，候选解在每一层——行为、学习、元学习、元-元学习——都自己修改自己，没有任何固定流程规定改法。那靠什么保证不越改越差？靠一条概率性的保留规则——**测得越好的解，分到越多算力去繁衍下一代**。因为算力按 fitness 分配，好的解在期望意义上被保留得更多，改进就单调了。

他给的实验是一个"会切换的老虎机（swapping bandit）"任务，结论有三条，最后一条最关键：自我修改能收敛出对当前任务有效的策略；更重要的是，这些修改会**调整未来的修改方式**，因此打得过固定的爬山法；而当你把 reward 直接喂给系统当输入，它就开始"学会怎么学"。这正好把第三节那句话落了地——不是变强，是变得更能变强。

但 FME 有一道它自己迈不过去的坎，Kirsch 在演讲里也坦率地把它单拎出来问了：**这个 fitness / reward 到底从哪来？**（幻灯片原话：What is the reward, e.g. in FME? Where does this come from?）FME 解决的是"拿到 fitness 之后怎么保留"这一层，它默认 fitness 是给定的。可在真正开放的自我改进里，没人从外面递给你一个可信的分数——系统得自己生成评价自己的标准。这道坎，正是下面"开放问题"那一节的引信。

---

## 六、逃逸速度：一个还没跨过的拐点

演讲的正式标题就是"逃逸速度"，Kirsch 用这个物理隐喻收束整场。对应关系不复杂：

- 引力 ≈ 人类驱动研究的那层阻力——读论文的速度、设计实验的带宽、验证一个想法的成本；
- 火箭速度 ≈ "AI 改 AI"这个反馈环的转速；
- 逃逸速度 ≈ 反馈环快到能自我维持的那个临界点，过了它，进步不再需要人类亲自去推。

再强调一遍那个最容易被漏掉的限定词：Kirsch 说的是**还没到**。他的原话是当前 RSI 系统"过早地停止改进，仍然需要人类介入"；逃逸速度是"人类不再被需要来交付进步"的那个拐点。他的判断是方向性的——我们在逼近，不是已经越过。他也没给时间表，但明确表示不认为这是"几十年后"的事。

那怎么知道拐点到没到？Kirsch 没给"顶会接收率超过某个百分比"这类具体阈值——网上流传的那几个数字并不在幻灯片里。他给的是一套更诚实、也更难的度量思路（幻灯片 "How to measure RSI?"）：

- **白盒 vs 黑盒**。如果只盯系统内部结构（白盒），麻烦在于——原则上连一个 RNN 都能被论证成"可以无界自我改进"，因为它结构上是图灵完备的。所以他反问：是不是该更"苦涩教训（bitter lesson）"一点，只看行为、从外部去找 RSI 涌现的**信号**（黑盒）？
- **改进的阶数**。他把能力提升分成几阶：零阶是当前表现 / 已掌握的知识；一阶是"创新的过程"本身；二阶是"改进创新过程的过程"，也就是元学习；三阶再往上叠。逃逸速度的问题，本质上是问：**高阶那几项能不能长期保持为正**，而不是某个单点 benchmark 好不好看。

这套度量观是整场报告的暗线：RSI 之所以难判断，是因为你要测的不是"它现在多强"，而是"它变强的能力有没有在变强"，而后者恰恰最难有一把便宜、可信、又骗不过去的尺子。

---

## 七、Lessons Learned：三条来自实战的教训

报告中段有一节干脆就叫 "Lessons Learned"，是 Kirsch 从自己下场做 AI Scientist 的经历里拧出来的三条，比前面的定义更接地气。

**一，基座模型的分量压倒一切（Base models matter a lot）。** 底座模型的能力，很大程度上决定了整个自我改进循环的天花板。换句话说，你没法靠外面那层脚手架，把一个弱底座"救"成强系统。

**二，光有 agent 脚手架不够（Agent harnesses are not enough）。** 这一条他连着放了三页幻灯片来敲。把提示词、工具、代码这套 harness（脚手架）堆得再精巧，本身也变不出 RSI。**但是**——他补了个重要转折——harness 可以被当成一个"改进算子"来用，让它去改进别的东西，例子是 EvoTune（Surina et al. 2025）。区别在于：harness 不是终点，是一件可以拿来改进系统的工具。

**三，真正的方向是"脚手架—模型协同演化"（Harness-Model Co-evolution）。** 别把两者中任何一个冻住单独优化，而是让 harness 和底座模型一起进化。（他还挂了一篇相关博客，Addy Osmani 谈 "agent harness engineering"。）

三条合起来，其实是在纠正一个 2025 年很流行的错觉：以为把 agent 的提示词和工具链调得够花哨，就能逼近自我改进。Kirsch 的经验是反的——底座决定上限，脚手架只有在"和底座一起被改进"时才真正进入 RSI 的循环。

---

## 八、Open Problems：拐点之前的硬骨头

报告的最后三分之一叫 "Open Problems"，也是最实在的一段——没有一条是"未来展望"式的漂亮话，全是当前没人能完整回答的硬问题。挑五个说。

**1. 怎么度量 RSI。** 第六节已经铺过：白盒会把问题变得没意义（结构上什么都能自我改进），所以得往黑盒的"行为信号"走，还得区分改进的阶数。度量不解决，"拐点到没到"就永远是口水仗。

**2. 人机协同，以及它带来的安全问题。** 这里 Kirsch 的立场值得单独讲，因为它和外界给他贴的标签相反。他不是说"把人留在系统外面当审批员"，而是主张**把人重新塞回循环里**——一个人与智能体**协同演化**的联合 RSI 系统。他画了三张图：现在是人类驱动 AI 研究；一种可能是 AI 系统自己转；而他认为**该去的方向**是人和智能体绑成一个共演化的 RSI 系统。安全含义顺着这个走：人类是 RSI 系统的一部分、持续监控与主动的信息共享、以及用自动化去做安全研究本身。安全不在系统外面加锁，而在系统内部留人。

**3. reward 从哪来。** 就是 FME 留下的那道坎：自我改进要有一个 fitness / reward，可这个信号本身谁来给？系统越自主、越没有外部裁判，这个问题越尖锐。Inherent 后来把它凝成了一句创业级的问法（见下一节）。

**4. 自生成任务与人工好奇心。** 一个通用 RSI 系统不能只会解别人给的题，得自己造题。Kirsch 把这条接回 Schmidhuber 的老本行——**人工好奇心（Artificial Curiosity）**：最早的做法（1990/1991，也是 GAN 的雏形之一）是让策略的内在奖励等于模型的预测误差，哪里预测不准就往哪里探。但它在随机环境里会翻车，就是著名的"噪声电视（noisy TV）"问题——面对纯随机的画面，预测永远不准，系统会被无意义的噪声勾住。改良方向是把目标换成**信息增益 / 学习进展（learning progress）**：不奖励"预测不准"，奖励"预测在变准"。（顺带一提，Schmidhuber 的 PowerPlay（2011）也属于这条线——不断给自己出"当前刚好还解不了"的新题；本文把它当背景，它并不在这次幻灯片里。）

> **一处必须做的更正**：本站早期版本说 Kirsch 提议"对抗式度量：让两个 AI 互相出题打分"，并自标存疑。核对幻灯片后，这段没有依据；他真正讲的是上面这套"人工好奇心 / 信息增益"，本文据此改写。

**5. 能不能直接为 RSI 优化，以及可证明性。** 现在的自我改进里，"改进算子"往往是**隐式涌现**的——靠归纳偏置，或者环境里一些先验说不清的东西——而不是被直接优化出来的。能不能显式地拿 RSI 当目标去优化？Kirsch 说他有些别的想法，但"结论还没定"，而且直接优化容易过拟合。这条最终又指回 Schmidhuber 2007 年的 Gödel Machine：可证明的递归自我改进，仍然是这条路的理论北极星。

---

## 九、Kirsch 要把这条路带去哪：Inherent 与"集体递归自我改进"

演讲里那个署名 "Co-Founder @ Stealth Startup"，到 2026 年 5 月已经揭了盖——这家公司叫 **Inherent**（inherentlabs.ai），Kirsch 是联合创始人，头衔是 Chief Superintelligence Officer；共同创始人还有 Tantum Collins、Edward Hughes、Kaloyan Aleksiev。它注册成一家**公益公司（Public Benefit Corporation）**，用意是让"对社会有益的研究"在与利润冲突时也能被优先。知道这家公司在赌什么，就能看懂这场演讲真正的落点。

Inherent 押的是一个更大号的 RSI——**集体递归自我改进（Recursive Collective Self-Improvement）**。他们不把 RSI 放在单个智能体身上，而是放在**整个实验室**上。灵感来自文化进化：在他们看来，人类文化演化本身就是 RSI 的原型——"一个能改进自己改进能力的系统"。一个先进 AI 系统的诞生，牵涉研究讨论、资源分配、硬件、训练数据、学习算法一整张网；AI 可以在每个维度上加速这张网，而这些加速只有在一个"从头就围着递归回路设计"的组织里才会复利。

这正好接上演讲里"人机协同"那一节——自我改进的单位是一个人机组织，不是一个孤零零的模型。更耐人寻味的是，他们把第八节那道最难的坎，直接刻进了公司的开创性问题：

> "How can we craft rigorous benchmarks for a system that controls its own reward?"（对一个自己掌控奖励的系统，我们要怎么设计严格的 benchmark？）

这句话和 FME 的"reward 从哪来"是同一道题。区别在于，在演讲里它是一个待解的开放问题，在 Inherent 那里成了立身之本的赌注。这也是"回顾和展望"里"展望"两个字真正的落点：Kirsch 不是在预测别人会怎样，他把自己接下来几年押在了"组织层的集体 RSI，且要在系统自控奖励的前提下守住可信评估"上。

---

## 十、常见误读：这场演讲没有在说什么

这场报告被转述得很多，几处走样也传得很广。对着幻灯片逐条校一遍：

- **误读一：它宣布逃逸速度已经发生。** 恰好相反。Kirsch 的论点是当前 RSI"过早停止改进、仍需人类介入"，拐点在前方，不在身后。
- **误读二：演讲给了一套"RSI 五判据"（可修改范围 / 可信评估 / 可持续增长 / 资源有界 / 状态可读写）。** 43 页幻灯片里没有这五条。演讲里真正的那张清单是第四节的"如何保证改进"（不做保证 / 形式化证明 / 回滚 / 进化 / 按 fitness 分配算力），讲的是另一回事。
- **误读三：Kirsch 反复引用 FunSearch 和 AlphaEvolve。** 这两个不在他的幻灯片里；他举的例子是 STOP、Darwin Gödel Machine、GPTSwarm、ADAS、Sakana AI Scientist、MLGym、EvoTune。AlphaEvolve 只出现在 Workshop 的参考文献列表里。
- **误读四：他给了 benchmark 阈值（比如顶会接收率超过 30%）。** 没有。他刻意不给单点阈值，度量思路是白盒 vs 黑盒加上"改进的阶数"。
- **误读五：Gödel Machine 到底是 2003 还是 2007？** 都对。最早的 arXiv 版本是 2003（cs/0309048），之后有 2007、2009 的修订版，Kirsch 幻灯片里引的是后面几版。

---

## 十一、给不同读者的落地建议

**做 AI Agent 工程的**：把第四节那张"如何保证改进"的表当 checklist 用。现在大多数 agent 框架其实停在最上面那档——"不做保证"：能自己改提示词和工具，但改坏了没有回退。往 RSI 挪一步，先补上"回滚有害改动"（Success Story Algorithm 的思路，留检查点），再接一个可信的 benchmark 闭环（Darwin / Huxley-Gödel Machine 的做法）。别一上来就追"让 agent 改自己权重"，那是更靠后的事。

**做 AI 安全 / 对齐的**：先纠正一个直觉。Kirsch 的安全立场不是"人在系统外把关"，而是"人是 RSI 系统里共演化的一部分"。落到工程上，两个点最该盯：一是 reward 的来源（FME 那道坎），二是自生成任务的好奇心目标会不会退化——盯着"噪声电视"问题，别让系统被纯随机的信号勾住。

**做 AI4Science 的**：Kirsch 自己（Inherent）押的是"组织层的集体 RSI"。对你更实际的判断点是：**你的领域有没有便宜又可信的验证**。代码、数学、形式化证明这类有 ground truth 的地方，改进环能闭上；湿实验、临床、社会科学这类验证又贵又慢的地方，卡住 RSI 的往往不是模型，是"reward 从哪来"。

**不太适合谁**：想要 SOTA 数字或纯 RL 数学推导的人。这是一场综述加纲领性质的报告，不展开公式，也不报 benchmark 成绩——它给的是一张地图，不是一张成绩单。

---

## 十二、自测：你读懂真实框架了吗

读完不妨用这几个问题回扣一下，答案都散在正文里：

1. Kirsch 的"逃逸速度"论点，是"已经发生"还是"还没跨过"？为什么这个限定词值得较真？（第一、六节）
2. 第四节那张"如何保证改进"的表，五档各自用什么代价换什么保证？今天大多数 agent 落在哪一档？（第四节）
3. 为什么"benchmark 分数变高"不等于"自我改进能力变强"？用 Metaproductivity-Performance Mismatch 解释一下。（第三节）
4. FME 解决了自我改进的哪一层，又明确没解决哪一层？（第五节）
5. Kirsch 讲的安全，为什么是"把人放进 RSI 系统"，而不是"人在系统外把关"？（第八节）

第 2、3 两题若能一口气答上来，这场演讲的骨架你就抓住了；剩下的都是枝叶。

---

## 十三、论文与资源地图

按"读完能把 Kirsch 的思想脉络复现出来"的优先级排：

| 优先级 | 资源 | 作者 | 链接 | 与演讲的关联 |
| ------ | ------ | ------ | ------ | ------ |
| ★★★ | 演讲幻灯片 PDF（43 页） | Kirsch | [louiskirsch.com/…ICLR_2026.pdf](https://louiskirsch.com/assets/louis_at_the_recursive_workshop_ICLR_2026.pdf) | 本文一手依据 |
| ★★★ | SlidesLive 现场录像（含 Q&A） | Kirsch | [slideslive.com/39063672](https://slideslive.com/39063672?t=1425) | 口头论证的原声 |
| ★★★ | PhD 论文《Automating AI Research》 | Kirsch | [phd_thesis…pdf](https://louiskirsch.com/assets/phd_thesis_automating_ai_research_louis_kirsch.pdf) | 第 7 章＝"保证改进"清单与 FME 完整版 |
| ★★★ | Self-Referential Meta Learning（含 FME） | Kirsch & Schmidhuber | [arXiv 2212.14392](https://arxiv.org/abs/2212.14392) | FME 的一手出处 |
| ★★ | Darwin Gödel Machine | Zhang, Hu, Lu, Lange, Clune | [arXiv 2505.22954](https://arxiv.org/abs/2505.22954) | "进化"一档；改代码同时改"改代码的能力" |
| ★★ | Huxley-Gödel Machine（HGM） | Wang, Piękos, …, Zhuge, Schmidhuber | [arXiv 2510.21614](https://arxiv.org/abs/2510.21614) | Metaproductivity-Performance 错配；CMP 指标 |
| ★★ | Gödel Machine | Schmidhuber | [arXiv cs/0309048](https://arxiv.org/abs/cs/0309048) | "形式化证明"一档；可证明 RSI 的理论原型 |
| ★★ | GPTSwarm: Language Agents as Optimizable Graphs | **Zhuge**（一作）, …, Kirsch, …, Schmidhuber | [arXiv 2402.16823](https://arxiv.org/abs/2402.16823) | agentic scientist 的可优化计算图（ICML 2024） |
| ★ | STOP: Self-Taught Optimizer | Zelikman et al. | [arXiv 2310.02304](https://arxiv.org/abs/2310.02304) | "不做保证"一档的代表 |
| ★ | The AI Scientist | Sakana AI（Lu et al.） | [arXiv 2408.06292](https://arxiv.org/abs/2408.06292) | 幻灯片点名的 agentic scientist |
| ★ | Agent-as-a-Judge | Zhuge et al. | [arXiv 2410.10934](https://arxiv.org/abs/2410.10934) | "用 AI 评 AI"，扣"reward 从哪来" |
| — | Inherent 宣言《Living within the Experiment》 | Collins, Hughes, Kirsch, Aleksiev | [inherentlabs.ai](https://inherentlabs.ai/) | "集体 RSI"的展望出处 |
| — | Schmidhuber 元学习 / 自指学习索引页 | Schmidhuber | [idsia.ch/~juergen/metalearning.html](https://people.idsia.ch/~juergen/metalearning.html) | 好奇心、Gödel Machine 等一手索引 |

读的顺序建议：**幻灯片 PDF → PhD 论文第 7 章 → FME 论文 → Darwin / Huxley-Gödel Machine → Gödel Machine 原论文**。前三篇是 Kirsch 自己的骨架，后两组一个补"进化派"实证、一个补"证明派"理论。

---

## 写作笔记（给后续读者）

- **信息来源**：Kirsch 个人站公开的 43 页幻灯片原件（已用 pypdf 逐页提取核对）＋ [SlidesLive 录像页](https://slideslive.com/39063672?t=1425) ＋ Workshop 官网 ＋ Kirsch 个人站与相关 arXiv 论文。**未拿到逐字字幕**，所有口头引用为据幻灯片的综合转述。
- **这一版（v5）做的最重要一件事，是拆掉上一版自己搭错的台子**：
  - 上一版把演讲核心说成"RSI 五判据"（可修改范围 / 可信评估 / 可持续增长 / 资源有界 / 状态可读写）。逐页核对 43 页幻灯片后确认，**这五条不在演讲里**，属于虚构框架，已整体删除。
  - 演讲里真正的那张清单是"如何保证改进"的五类机制（不做保证 / 形式化证明 / 回滚有害改动 / 进化 / 按 fitness 分配算力），据此重建了第四节，并把 FME 放回它本来的位置——五类机制中的一类（第五节）。
  - 删除了"Kirsch 反复引用 FunSearch / AlphaEvolve"的说法（幻灯片无此内容），换成幻灯片实际点名的系统。
  - 删除了"顶会接收率 >30%"等三个"可观测信号"（幻灯片未给任何阈值），换成演讲真实的度量思路（白盒 / 黑盒＋改进的阶数）。
  - 把"对抗式度量"改成演讲实际讲的"人工好奇心 / 信息增益"（含噪声电视问题）。
- **顺带落实的事实**：演讲＝ICLR 2026 RSI Workshop 首场受邀报告（2026-04-26，里约）；此前标注"存疑"的"Kirsch 转创业时间"已确认——2025 年 12 月共同创立 **Inherent**，2026 年 5 月揭盖。补入 Darwin Gödel Machine、Huxley-Gödel Machine 两项 2025 年的一手实证。
- **保留的既有更正**：FME 论文编号 **2212.14392**（不是 2212.14311）；1987 是 Schmidhuber 硕士论文（概念前驱），Gödel Machine 是 2003；GPTSwarm 一作是 Mingchen Zhuge，Kirsch 为合作者。
- **与同仓库 [emergent-garden RSI 文章]({{< relref "emergent-garden-recursive-self-improvement-fractalsearch.md" >}}) 的关系**：两篇是互补视角。本篇是 Schmidhuber 学派、从"怎么保证自我改进为真"切入；那篇是 Karpathy 学派、用 fractalsearch 实测"真跑一个 RSI 循环会撞到什么边界"。一篇讲机制，一篇讲边界，对照着读最省事。

— 钳岳星君 2026-07-13（v5：据 43 页幻灯片原件重建框架 / 删除虚构的"5 判据"叙事 / 还原"保证改进"五机制与 FME / 补 Darwin & Huxley-Gödel Machine 与 Inherent 展望 / 更正好奇心与信号段）
