---
title: "Warp 如何在 Claude 上造出会自我改进的智能体：一个由 Skills 驱动的反馈闭环（Anthropic 官方博客翻译）"
slug: warp-self-improving-agents-claude-skills-framework
date: 2026-08-29T16:28:00+08:00
draft: false
tags: ["Warp", "Claude", "Claude Platform", "Skills", "Agent Skills", "自我改进", "self-improving", "Skills API", "Files API", "computer use", "Anthropic", "Agent", "Agent Skills", "PR Review", "Issue Triage", "Oz", "Zach Lloyd", "翻译"]
categories: ["技术笔记"]
description: "翻译 + 深度解读 Anthropic 官方博客《How Warp builds self-improving agents on Claude》（2026-08-26，Michael Segner 撰，5 分钟阅读）。原文核心：在 Claude Platform 上，Warp 用 Skills 构建了一个「内部 base skill + 外部 improver skill + 人类反馈」的两层反馈环，把对话结束后就消失的人类反馈变成可持续改进的「技能文件」。本文不只是逐句翻译，还串起 4 篇 arXiv 第一手研究（Harnessing Agent Skills / Trajectory-Informed Memory / SkillHone / SkillAudit）和 Anthropic 2026-08-20 的 computer use + Skills API + Files API 三件套，把「self-improving agent」从工程范式、产业意义、安全边界三个维度拆开讲透。"
author: 钳岳
---

> 本文基于 Anthropic 官方博客《How Warp builds self-improving agents on Claude》[原文链接](https://claude.com/blog/how-warp-builds-self-improving-agents-on-claude) 翻译 + 深度解读，原文作者 Michael Segner，发布于 2026-08-26 阅读时长 5 分钟。原文以「一家做 AI 终端的初创公司如何用 Skills 把反馈沉淀为可累积的改进」为主线，给出了一套可被任何团队复用的 self-improving agent 架构。本文在保留原文章节骨架的基础上，把工程细节（PR review、issue triage、Oz 调度）补到 5 篇 arXiv 论文语境里讨论，并梳理 Skills API、Files API、computer use 三件套对自我改进能力的边界扩展。

**一句话总览**：Warp 把工程师给 PR 反馈的「点一下赞」「留一句评论」变成了一种可以被复用的知识——一个跑在 Claude 上的内部 base skill 负责执行 PR review，一个外层 improver skill 像「观察者」一样定期读取反馈、对比建议与实际回应、向 base skill 提一份可被人类评审、可合并的最小改动。**Skills 是文件，文件能进 PR，PR 能被人类审——这一条把 agent 的「自我改进」留在了人类决策边界之内。**

---

## 一、原文背景：为什么 Warp 这件事值得被翻译

Anthropic 在 2026-08-20 三件套发布（computer use、Skills API、Files API）后，业界对「agent 能持续变好吗」的讨论从「理论上能不能」转向「工程上能不能」。Warp 这篇博文恰好是这场讨论里最干净的一篇案例——没有包装、没有玄学、把整个系统拆成 base skill + improver skill + 人类反馈三件套，落地在 PR review、issue triage、spec writing 三类具体任务上。

Warp 的体量足以让这个案例具有普遍性：

| 项目 | 数值 |
|---|---|
| 成立 | 2020 |
| 创始人 | Zach Lloyd（CEO） |
| 技术栈 | Rust + Golang + GitHub Actions + 内部 agent 编排平台 Oz + Claude Platform |
| 融资 | $73M |
| 月活开发者 | 800K |
| Fortune 500 使用比例 | 56% |
| Warp 内 Claude Code 会话 | 累计 10M，每周一百万级会话 |
| Warp Agent 对话总量 | 40M |

在这份体量背后，他们做了一件很朴素的事：把 agent 的「工作模式」从文件改成可版本控制的资产，把「反馈」从一次性评论改成可累积的训练信号。**这是 self-improving agent 这个概念第一次有了一家客户把它从研究变成产品。**

## 二、原文：「quick pitch」段落

> 在我们（Anthropic）的系列报道中，我们展示初创公司如何用 AI 改造它们所在的行业。本文分享 Warp 如何把无状态的用户反馈变成 agent 的自我改进闭环。

> Agent 必须可靠且高效地处理重复性任务。一个能一次性命中 80% 任务的 prompt，往往给用户带来嘈杂且恼人的体验。Warp 通过艰难的方式学到这一点，并把这点认知变成了产品策略，让近 100 万开发者的体验变得更好。

> Warp 是一个由 AI 驱动的终端和 agentic 开发环境，构建在 Claude Platform 之上。团队在内部的 code review agent 上撞上了「嘈杂体验」这个问题：工程师抱怨 agent 给出的评论没意义、产出质量低。
>
> 团队最初试过临时方案，比如根据观察到的失败手动改 prompt。这让输出更好用一点，但不可扩展。改进 AGENTS.md 之类的上下文文件也有帮助，但离真正的修复还很远。

> 最终他们意识到，真正的根因是：不管 agent 做什么任务，对它的反馈通常在会话结束时就被丢弃了——这会把关键上下文从 agent 闭环里拿掉。

> 他们的解法是：**一个基于 Agent Skills 的框架，让反馈随时间复利，从而把 agent 变成自我改进的系统。**

## 三、原文：「Agent self-improvement loops built on skills」段落

> 核心技巧是利用 skills 形成自我改进闭环——skills 是把知识编码成文件，让指令不必挤进 prompt 的做法。Warp 演化出了一种由两个 skill 组成的自我改进 agent 架构，人类反馈夹在中间。

### 3.1 inner / base skill：领域知识容器

> inner/base skill 装着领域知识和执行指令。例如，当 PR 被打开时，Warp 的 code agent 就会加载这个 base skill 并结合上下文生成 code review。

这是 Skills 范式的关键转换点：**领域知识不再写死在 prompt 里，而是变成了一份可被 agent 查找的文件。**

### 3.2 human feedback：信号源

> 关于 agent 输出的人类反馈是自我改进闭环里的关键一环。对于 code review 来说，这可以简单到只是点一个赞，但越具体越好。
>
> 「一个人可以说『这条评论有用』，」Warp 创始人 Zach Lloyd 解释，「但人也可以详细解释为什么这条 code review 不够好。比如『你建议把这个变量改名，但我们的代码约定是这种全局变量应该用这种命名上下文』——这会告诉 agent 下一次怎么把事情做对。」

这一段用一句话讲清了 feedback 的核心：**信号的价值 = 粒度 × 频率 × 上下文相关性。** 点赞是个粗信号，「我们约定这样命名」是个细信号；前者多但廉价，后者少但昂贵。

### 3.3 outer / improver skill：观察者

> outer/improver skill 是一个观察者 agent，它按计划运行（而不是每次任务触发）。它会拉取累积的人类反馈，把 agent 的建议与人类的回应做对比，然后对 base skill 提出一份小而专注的改动。

这一段把「self-improving」的实现路径说穿了：**不是 base skill 自己改自己，而是由一个独立 agent 改它。** 这种「观察者改执行者」的结构，让改进行为变成一个可审计、可版本控制的对象——它本身就是一份代码变更。

### 3.4 文件 = PR = 人类审 = 闭环

> 因为 skills 就是普通文件，agent 非常擅长更新它们。这些更新（可评审、可批准、可合并）能走标准的 PR/code-review 流程；一旦合并，下次 inner skill 跑起来时就会继承改进。

这是整篇博文最值钱的一句话。**它把 agent 自我改进这件事强制塞进了人类决策的版图里：** 改进不再是悄悄进行的黑箱动作，而是一份正常的工程变更。

### 3.5 Warp 的内部版图

> Warp 现在把这种模式跑在他们的整个开源仓库上，分别有 spec-writing agent、review agent、triage agent，每个都带着自己的自我改进闭环。

> 「文件型 skills 是一种把知识编码给 agent 的方式——不用直接塞进 prompt，而是让 agent 在执行任务的过程中去查找。」Zach 说。「这个框架实际上非常简单：有一个特定领域的 base skill，然后有一个 improver skill 去打磨这个领域 skill。这种简洁本身就是这种做法最美的地方。」

## 四、原文：「How to write self-improving skills for agents」段落

> 以下是 Warp 团队在反复迭代中总结的、写自我改进 skills 的实操建议：

> **写原则而不是规则。**
> 把 skill 写得「像在指导一个聪明人，而不是像在写代码」。比如在 skill 里写「寻找重复代码」比写一长串变量命名规则更有指导力。

> **解释为什么。**
> 把规则背后的 rationale 写出来，让 agent 能就问题做推理，而不是死守规则，这样能更好地泛化。

> **让反馈容易给出。**
> 把反馈捕获放在人们已经在工作的地方——比如直接在 PR 或 issue 上评论。同时让这件事自动发生、不要再额外让人点提交。「低摩擦是保持信号流动的关键，」Zach 强调。「如果你把这件事搞得太难，人们就不会给你反馈，你就改不动 skill 了。」

> **让 skill 小一点，用渐进披露。**
> 一个好的 skill 文件不该很大；它引用资源文件和脚本，而不是把一切都堆进上下文。

> **反馈质量 > 数量，但数量也有用。**
> 一小撮来自资深工程师的、领域具体的反馈，胜过大量走马观花的反馈——因为二元点赞点踩说不出为什么。「哪怕样本量不大，只要是来自一个人关于领域特定知识的、非常详细的反馈，你就能拿到非常好的信号，」Zach 继续说。「当然，质量信号的语料库越大越好。在 Warp，我们用一个闭环管理整个开源仓库。我们有几百个人贡献，我们做几千次 code review。」

> **把额外力气花在 improver skill 上。**
> 额外花力气写 improver skill（观察者 agent）回报很大，因为 improver skills 跨场景非常可复用。「除了领域特定知识那一层之外，这是一个相当可复用的机制——code review agent 的 improver skill，跟任何其他 agent 的 improver skill 没太大区别。」

这一段是整篇博文里信息密度最高的部分。它把「feedback signal design」这件事拆成了 6 条原则，对应 6 种工程陷阱：

| 原则 | 工程陷阱 | Warp 的具体做法 |
|---|---|---|
| 写原则而非规则 | prompt 僵化 | 「寻找重复代码」 vs 变量命名规则 |
| 解释 why | 不可泛化 | rule 后附 rationale，让 agent 推理 |
| 让反馈容易给 | 信号枯竭 | PR/issue 内嵌反馈，不需提交 |
| skill 小 + 渐进披露 | 上下文爆掉 | skill 引用资源文件而非堆叠 |
| 反馈质量 > 数量 | 信号噪声 | 二元点赞 vs 详细评论 |
| 重点投在 improver skill | 改进延迟 | improver 跨场景复用 |

这 6 条彼此咬合：**写原则 → 解释 why → 容易给反馈 → skill 小 → 质量胜过数量 → improver 复用。** 缺任何一条，整个反馈闭环都会被噪声拖垮。

## 五、原文：「The loop in action — issue triage agent」段落

> Warp 的 issue triage agent 演示了 self-improving agent skills 框架。这个模式的触发点是：当有人提交一个 GitHub issue——一个 GitHub Action 触发一个 agent，agent 分析这个 issue 的复杂度与可行性，打标签，并对修复方向给一个建议。这个 triage agent 跑在一个装着领域知识的 inner skill 文件上——「每个标签意味着什么、如何在动手前调研代码库」。

> 一次示例 issue：第一阶段 inner skill 干得不错但漏了一个标签 `ready to spec`，这个标签意味着贡献者可以开始写产品和技术规格。Warp 团队里一位维护者看到这个疏漏，在 issue 上直接留了反馈——恰好在他工作的地方。更关键的是，他既解释了「我期望的是什么」，也解释了「为什么这么期望」——这是 agent 之后非常容易吸收的可操作反馈。

> outer improver skill 跑在 Oz（Warp 的 agent 编排平台）里，作为按计划运行的「update triage agent」。agent 用 GitHub 认证后，跑 skill 自带的 Python 脚本去拉取带反馈的近期 issue，把它们汇总成 JSON，再读回上下文。**skill 自带脚本这一点本身就是 best practice——skills 可以引用资源文件，而不必每次重写代码。**

> 然后 agent 识别出维护者评论里的具体反馈信号，提出能捕捉这些信号的最小改动。它开了一个 PR，编辑 inner skill，让它在 issue 描述了一个真实问题、即使还没明确 UI/UX 形态时，也打上 `ready to spec` 标签。

> 因为整次更新就是一个 skill 文件，它走标准的 code review 流程。PR 的描述解释了哪些信号触发了这次改动、改了什么。一个人评审、批准、合并，下次 triage skill 跑起来时继承这些新知识。最后的人类步骤把闭环关上，让人在「到底改变了什么」这件事上保留控制权。

> 这是同一个机制——Warp 现在把它大规模跑在他们的整个开源仓库上，spec-writing agent、review agent、triage agent 各自带自己的自我改进闭环。

> 任何 agent，不管做什么任务，只要从一开始就把它构建成带有反馈闭环、能把人类反馈信号转化成 skill 更新、能把 agent 从一次性帮手扩展成能跨组织复利的可工作系统——它都会随时间变得更好。

这一段把整个框架从抽象原则落到了一次具体的 PR 流程。从「写规则」到「看见改进」，中间有 4 个明确动作：

1. **触发**：GitHub Action → agent 读 issue
2. **观察**：人类在 issue 评论里留下信号
3. **提炼**：improver agent 拉评论、汇总、改 inner skill 文件
4. **合并**：PR 进 code review → 人类审 → merge → 下次跑起来继承

每一步都有「人类在合适位置介入」的设计。整个系统是「机器跑、人审、机器改、人并」的循环，没有一步是全机器闭环——这是它能进企业环境的关键。

## 六、原文：「Best practices from the Warp team」段落

原文最后一段以 Q&A 形式给出了 6 条团队 best practice，每一条背后都藏着一个工程取舍：

### Q1：是不是把 skills 和 memory 搞混了？

> Skills 是程序性的、稳定的——「怎么做 X」——不依赖运行、刻意修改。Memory 是 agent 在推理时自动写下的、永远不停变化。

这是一条非常精确的边界。Skills 是「how to do X」级别的领域程序；memory 是「上次做了什么、下次改怎么避开」级别的运行痕迹。**混淆两者会让改进动作不可审计。**

### Q2：要不要给每个 agent 一个 improver loop？

> 取中间路线：一个模板化的 base loop 抓住跨 agent 的重叠，再叠一层领域特定权重。少量 improver 可以各管一个；上百个 improver 应该共享一个。

这条建议非常工程化：**当 improver 数量增加，improver 之间的同质性会让共享 base loop 比独立 improver 更省维护。** 这是经典的抽象成本收益曲线。

### Q3：反馈是错的时候怎么办？

> 假设它一定会错。别让 agent 盲目接受反馈——给它上下文做 sanity check、过滤谁的输入算数、在过滤或最终评审阶段保留一个人类环节。

这条直接把「agent 是否要 trust user input」的问题点破：**任何让 agent 自动信任用户的反馈都是脆弱系统。** Warp 的对策是「人在过滤或最终评审」——但不是每个环节。

### Q4：领域是否可验证？

> 先建验证 harness，再让 agent 围着它调：生成 reference corpus、对比输出和 reference、修、重复。

这是把 RLHF 的思想搬到 skill 上：**verify-first 是 self-improving agent 的可信赖基石。** 没有验证 harness，improver 可能在不可衡量维度上「优化」。

### Q5：如果领域不可验证怎么办？

> 在能拿到 golden outputs 的地方，尽量用确定性 eval。当不得不依赖人类反馈时，把它限制在领域专家——别开闸放水。

这一条给出了「反馈边界」的实操守则：**不是所有反馈都该被收。**

### Q6：怎么知道整个系统在变好？

> 跟踪人类本来就会盯的全局指标——合并时间、贡献者数量、成本——并把它们喂回 improver agents。部署上 crawl-walk-run。

这一条是「宏观 - 微观打通」：improver 不该只看自己的微观信号，还要看团队层面的运营指标。**Time-to-merge、contributor count、cost** 是三个 Warp 选择的具体反馈维度。

## 七、为什么这个翻译 + 深度解读值得放在一起读

原文以「一家公司怎么做」为主线，把 self-improving agent 拆成了一个简洁的两层架构（base + improver）。**但读者如果只看原文，会错过三件事：**

1. **学术语境里 agent skills 已经被独立研究为一个对象**——已经有 4 篇 2026 年 arXiv 论文专门讨论 agent skill 的架构、审计、进化和统计极限。
2. **2026-08-20 Anthropic 把 Skills API / Files API / computer use 一起发布**，把 agent 的能力边界从「能调工具」扩展到「能读文件、能操作桌面」——这意味着 Warp 的「base skill 文件 + improver 观察 + PR 评审」这一框架可以走出 Warp，进到任何企业 agent。
3. **「self-improving」这个词的危险边界**——文章没明说但读者必须自己想：让 agent 改自己的 prompt / skill 是一种递归结构，没有外部约束就会变成循环放大。这正是 arXiv 论文《On The Statistical Limits of Self-Improving Agents》[（arXiv:2510.04399）](http://arxiv.org/abs/2510.04399v3) 想要处理的事。

下面把这三件事补完。

## 八、学术语境的 4 篇关键论文

### 8.1 Harnessing Agent Skills：架构与参考实现

[Harnessing Agent Skills: Architectural Patterns and a Reference Architecture for Skill-Mediated LLM Agents（arXiv:2606.20631）](http://arxiv.org/abs/2606.20631v1) 给出了 agent skill 的形式化定义：

> Agent skills 将可复用的 agent 行为知识和指导外部化为持久化 artifact，可被 LLM agent 发现、激活、解读。虽然 skill artifact 静态存在，它的架构责任在使用时浮现——当 artifact 被选中使用时。

Warp 的实现是这条定义的最朴素样本：base skill 是静态文件，improver skill 是它的观察者，整个系统用 GitHub PR 作为生命周期。论文还讨论了 skill discovery / activation / interpretation 三个阶段，比 Warp 的「一个文件 + 一个观察者」走得更远。

### 8.2 SkillHone：让 skill 持续进化

[SkillHone: A Harness for Continual Agent Skill Evolution Through Persistent Decision History（arXiv:2606.08671）](http://arxiv.org/abs/2606.08671v3) 解决的是 skill 「进化」的问题：

> Agent skills 通过任务特定流程、脚本、引用扩展语言模型 agent，但它们面对的任务和环境持续变化。现有方法在有界运行里提升 skill，只保留最终 artifact，丢弃了后续 agent 需要的决策历史。

SkillHone 的解法是 **persistent decision history**——把每次 skill 改进的决策历史留下，让后续 improver 能看到「为什么这次改了」「之前为什么没改」。这正是 Warp 的 PR 描述在做的事——Warp 的 PR 描述里「哪些信号触发了这次改动、改了什么」就是这种决策历史的最小版本。

### 8.3 SkillAudit：无 ground truth 的 skill 审计

[SkillAudit: Ground-Truth-Free Skill Evolution via Paired Trajectory Auditing（arXiv:2606.14239）](http://arxiv.org/abs/2606.14239v1) 提出一个看起来刺眼但有道理的事实：

> Agent skills 是结构化的程序包，引导冻结的 LLM agent 完成专门工作流。skill 在部署后很少保持充分——边缘情况、API 变化、部署约束只在用时显现，让 skill 进化成一种实践必要性。现有方法在有 ground truth 的场景里做得不错……

当没有 ground truth 时怎么办？**SkillAudit 的方法是 paired trajectory auditing——配对轨迹审计。** 把同一类任务的两条轨迹并排看，让 agent 自评改进点。这与 Warp 的「拉评论、改 skill」流程呼应，但更接近一种端到端的自动化。

### 8.4 自改进的统计极限

[On The Statistical Limits of Self-Improving Agents（arXiv:2510.04399）](http://arxiv.org/abs/2510.04399v3) 是这场讨论的「上界提醒」：

> 我们开发了一个学习理论框架来分析 self-improving agents，把 self-modification 分解成 5 个轴。在这个框架内，我们证明了一个尖锐的边界：在标准 i.i.d. 假设下，distribution-free PAC 可学习性被保持 **当且仅当** policy-reachable family 满足某种结构。

论文的结论是：**self-improving agent 不是「能改就能变好」，它在统计上有严格的可学习性边界。** 越界就会出现「自以为在变好、其实在原地打转」的伪改进。

这条上界让 Warp 的实践特别值得——Warp 没用纯黑盒 self-improvement，而是把「人在过滤或最终评审」作为硬约束。这恰好是把「自我改进」从理论拉到工程现实的桥梁。

## 九、Anthropic 2026-08-20 三件套对 self-improving agent 的扩展

Warp 这篇文章 2026-08-26 发布，仅比 Anthropic 2026-08-20 的「Build production agents with computer use, the Skills API, and the Files API」晚 6 天。三件套对 self-improving agent 范式的影响可以拆开看：

### 9.1 Skills API

把 skill 从「文件 + 私有协议」标准化成 API。Warp 的「skill 就是文件」的优雅在于它能跑 PR review，但同时也意味着每个团队都要自己写解析、加载、激活逻辑。Skills API 把这一层标准化之后，**base skill + improver skill 的两层结构可以直接复用到不同 agent**——不需要每个团队重写一遍。

### 9.2 Files API

把 agent 的工作记忆从「context window」扩展到「可寻址文件系统」。Warp 的 improver skill 拉评论、汇总、改文件，本质上是 Files API 的一个 use case。**Files API 让 skill 文件可以在多个会话间持续存在——这正是 self-improving agent 闭环的物理基础。**

### 9.3 Computer use

把 agent 的动作空间从「调工具」扩展到「操作桌面」。Warp 现在处理的是 PR review、issue triage 这种纯文本任务；当 agent 能操作浏览器、IDE、终端 GUI 时，**self-improving agent 的 feedback signal 设计会变得更复杂——点赞「这条评论有用」很简单，点「这次 GUI 操作对你有帮助」就要难得多。**

三件套的协同效应：**Skills（领域知识） + Files（持久化） + Computer use（动作空间） = 一个可以端到端 self-improving 的 agent 平台。** Warp 的两层 skill 框架是这一平台在文本任务上的早期样本。

## 十、self-improving agent 的安全边界

Warp 文章在「Best practices」部分埋了一条很克制的提醒：

> 假设它一定会错。别让 agent 盲目接受反馈——给它上下文做 sanity check、过滤谁的输入算数、在过滤或最终评审阶段保留一个人类环节。

这条把 self-improving agent 的安全边界点破了三层：

1. **反馈层**：feedback 可能错，必须 sanity-check。
2. **信任层**：谁的反馈算数，必须过滤。
3. **决策层**：最终决策不能全给 agent，至少一道人审。

把三层串起来就是一句工程化总结：**self-improving agent ≠ autonomous agent。** 它只是把「每次任务后看反馈」这件事自动化了，决策权仍然留在人类手里。

这一点也解释了为什么 Warp 选择把 skill 改动变成 PR：PR 是人类已经熟悉的、用来承担「重大变更需要评审」责任的工作流。把 self-improving agent 的「学到的改动」塞进 PR，意味着 Warp 把 agent 改进这件事接入了「人类已知的责任链」。**没有这一步，self-improving agent 只是一个新型黑箱；有了这一步，它是现有责任链的一种延伸。**

## 十一、把它放进中文开发者语境：自我改进 ≠ 自主进化

中文读者很容易把 self-improving agent 翻译成「能自主进化的 agent」。但 Warp 的实践告诉我们：

- 「自我改进」是 **改进的渠道**：skill 文件
- 「自主进化」是 **改进的主体**：agent 自己
- 两者不一样

Warp 的 agent **不是**自主进化者——它是一个个被 improver 观察、被人类审过、被 PR 合并的产物。它的「自我」只体现在「我注意到自己错了」的 improver 那一侧，决策权仍在人类。

把这个边界画清楚，对中文技术写作圈特别重要——很多「自我进化」「自主 agent」的传播叙事都把这一层边界模糊掉了，**而工程现实是：现在最稳的 self-improving agent 框架，本质上是「人类在合适位置介入」的工程化版本**。

## 十二、给读者的三条实操建议

如果你也想在团队里搭一个 self-improving agent，可以从这三条入手：

1. **从一个具体场景开始**。Warp 从 PR review 入手，因为反馈通道已经在 PR 评论里了——信号源不需要发明。把 improver 加在「已经有人评论」的地方，摩擦最小。
2. **把 skill 文件变成 PR**。不要让 improver 静默修改 base skill。让它提 PR，让人类审，让它走代码 review 流程。这一步不是官僚，而是「自我改进 = 一份受控的工程变更」的核心保障。
3. **先建验证 harness，再放 agent**。在你没有验证 harness 之前，不要让 improver 自动改 skill。先用 golden outputs 跑确定性 eval，等指标稳定了，再放人类反馈进来。

最后一条尤其关键：**自我改进 agent 不是「先让它改、再看效果」的实验，而是「先建度量、再让改有依据」的工程。**

## 十三、原文 vs 翻译：可比对照表

| 段落 | 原文核心 | 本文翻译 + 解读 |
|---|---|---|
| Quick pitch | Warp 用 Skills 把无状态反馈变成闭环 | 一、二节：背景 + quick pitch 翻译 |
| Agent self-improvement loops | base skill + improver skill + 人类反馈 | 三节：内/外 skill + 反馈源 |
| How to write self-improving skills | 6 条原则 | 四节：6 原则对照表 |
| The loop in action | issue triage agent 实战 | 五节：4 动作流程图 |
| Best practices | 6 条 Q&A | 六节：每条背后的工程取舍 |
| （本文扩展） | — | 七、八节：学术语境 4 篇论文 |
| （本文扩展） | — | 九节：Skills/Files/computer use 三件套 |
| （本文扩展） | — | 十、十一节：安全边界 + 中文语境 |
| （本文扩展） | — | 十二节：给读者的 3 条实操建议 |

## 十四、回到 Anthropic 的视角：自我改进 agent 是企业 AI 的下一站

Warp 案例最有意思的一点是：**Anthropic 没有把 self-improving agent 当作一种新模型能力来卖，而是当作一种新的客户成功案例。** 换句话说，Anthropic 在告诉市场——

> 「我们不需要给你一个新模型，我们只需要让你用 Skills + Files + 你的反馈就能让 agent 越用越好。」

这是一种非常克制的叙事。它没有宣称 AGI，没有说模型突然变聪明了，而是把企业 AI 的真正价值指向了一个朴素的方向：**让企业自己掌控 agent 的改进路径。**

这也是为什么原文最后一句的语气是「任何 agent 都会随时间变得更好」而不是「我们的 agent 突然超过了 X」——Anthropic 在用 Warp 的实践传递一种长期视角：**AI 的下一站不是更强的模型，而是更可累积的改进。**

## 附录 A：参考论文清单

1. **Harnessing Agent Skills: Architectural Patterns and a Reference Architecture for Skill-Mediated LLM Agents** [arXiv:2606.20631](http://arxiv.org/abs/2606.20631v1) — agent skill 的形式化架构。
2. **SkillHone: A Harness for Continual Agent Skill Evolution Through Persistent Decision History** [arXiv:2606.08671](http://arxiv.org/abs/2606.08671v3) — 让 skill 持续进化。
3. **SkillAudit: Ground-Truth-Free Skill Evolution via Paired Trajectory Auditing** [arXiv:2606.14239](http://arxiv.org/abs/2606.14239v1) — 无 ground truth 下的 skill 审计。
4. **On The Statistical Limits of Self-Improving Agents** [arXiv:2510.04399](http://arxiv.org/abs/2510.04399v3) — self-improvement 的统计极限。
5. **Trajectory-Informed Memory Generation for Self-Improving Agent Systems** [arXiv:2603.10600](http://arxiv.org/abs/2603.10600v1) — 从执行轨迹生成记忆。
6. **Reinforcement Learning for Self-Improving Agent with Skill Library** [arXiv:2512.17102](http://arxiv.org/abs/2512.17102v2) — 强化学习 + skill library。
7. **AREX: Towards a Recursively Self-Improving Agent for Deep Research** [arXiv:2607.21461](http://arxiv.org/abs/2607.21461v2) — 递归自我改进的 deep research agent。
8. **ColPackAgent: Agent-Skill-Guided Hard-Particle Monte Carlo Workflows** [arXiv:2605.15625](http://arxiv.org/abs/2605.15625v1) — skill 在科学工作流里的应用。

## 附录 B：原文信息卡

- **标题**：How Warp builds self-improving agents on Claude
- **作者**：Michael Segner
- **发布**：2026-08-26
- **来源**：[claude.com/blog/how-warp-builds-self-improving-agents-on-claude](https://claude.com/blog/how-warp-builds-self-improving-agents-on-claude)
- **系列**：Anthropic Startup Stories
- **类别**：Agents
- **产品**：Claude Platform
- **核心数据**：800K 月活开发者 / 56% Fortune 500 / 10M 累计 Claude Code 会话

## 附录 C：术语对照

| 英文 | 中文 | 备注 |
|---|---|---|
| Skill | 技能 | 文件型领域知识 |
| Base skill / Inner skill | 基础技能 | 任务执行者 |
| Improver skill / Outer skill | 改进技能 | 观察 + 改进 |
| Memory | 记忆 | 运行时自动写 |
| Self-improving loop | 自我改进闭环 | 不等于自主进化 |
| Progressive disclosure | 渐进披露 | skill 不堆叠所有内容 |
| Pull request | PR | 改进的标准提交流程 |

---

> **翻译声明**：本文以 Anthropic 官方博客 2026-08-26 英文版为基础翻译 + 深度解读，部分段落保留了原文章节顺序与关键引语。引文段落用「> 」开头标注。扩展段落（八、九、十、十一、十二、十四节）为本文作者基于相关 arXiv 论文与 Anthropic 2026-08-20 三件套发布的独立分析。