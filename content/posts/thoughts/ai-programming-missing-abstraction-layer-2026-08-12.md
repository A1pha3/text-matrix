---
title: "AI 编程缺失的抽象层：siddontang 那篇元视角文章真正在讲什么"
date: 2026-08-12T21:50:00+08:00
draft: false
tags: ["AI Agent", "技术写作", "抽象层", "软件工程", "Engineering", "Programming"]
categories: ["技术笔记"]
description: "siddontang《AI 编程缺失的抽象层》不是又一篇'AI 抢工作'焦虑文——它把'AI Coding 是什么'放到计算机抽象升级史里看，给出三组判断：编程关系从人→Lang→Computer 变成人→Intent→Agent→Lang→Computer；新基本功 = Spec + Decomposition + Verification + Context Engineering；'AI 时代的 C 语言'可能是一组新抽象 Intent+Spec+Context+Tools+Memory+Policy+Runtime+Eval。这篇文章拆的是 siddontang 论点的内在结构、为什么这个结构现在才被看清，以及它对 Junior Engineer 训练梯子的具体含义。"
slug: "ai-programming-missing-abstraction-layer"
band: "essay"
gates: ["事实性", "去AI味", "观点依据"]
---

## 这篇文章在回答什么

siddontang 那篇《AI 编程缺失的抽象层》很容易被读成另一种"AI 抢工作"焦虑文。但它不是。它把"AI Coding 是什么"这个新问题，放进计算机抽象升级史里看了一遍，然后得出一个判断：今天的不安不是因为 AI 变强了，而是因为**能力已经跃迁，新的抽象层还没稳定下来**。

把它和别的"AI 编程"文章分开的，是它那三组判断：

1. 编程关系正在从 `人 → Programming Language → Computer` 变成 `人 → Intent → Agent → Programming Language → Computer`。代码依然存在，但逐渐从"被操作的对象"变成"被生成的产物"。
2. AI 时代的基本功可能正在重新定义——不再是"亲手实现底层"，而是 **Specification / Decomposition / Verification / Context Engineering** 四个新能力。
3. 今天可能正处在 "AI Programming 的 Assembly Era"——Prompt、Memory、Tool、MCP、Sub-agent、Harness 这些概念，最终大部分会被更高层的 Runtime / Framework / Protocol 吃掉。最终稳定下来的，可能是一组新抽象：`Intent + Specification + Context + Tools + Memory + Policy + Runtime + Eval`。

下面不打算复述他的结论，而是拆开三样东西：他论点的**内在结构**，即为什么把"AI 编程"放进抽象升级史、这个类比为什么现在才被看清；他论证里**几个被低估的判据**，比如"AI 时代的 C 语言还没出现"不是抱怨而是诊断、Junior Engineer 真正的危险不是失业而是训练梯子断了；以及把他的清单**落到今天的工程现实里**，说明 Spec / Decomposition / Verification / Context Engineering 对应什么，为什么它们不只是"AI 时代新话术"。

## 一、把"AI 编程"放进抽象升级史，问题就变了

siddontang 论证的第一步是历史定位。机器码之上出现汇编，汇编之上出现 C，高级语言之上出现 Framework，服务器之上出现 VM / Cloud / Container / Serverless——每一次抽象升级，都有人担心"基本功是不是没了"。但基本功没有消失，只是换了位置。你不需要每天写汇编，但遇到性能问题要理解 CPU 和内存；你不需要自己实现数据库，但遇到一致性问题要理解事务和复制。

真正重要的不是"是否亲手实现底层"，而是**当抽象失效时，你能不能穿透它，理解下面发生了什么**。

这段不是在讲历史。它把"AI Coding 是什么"这个问题，从"AI 是不是比程序员强"拉回到"这是又一次抽象升级吗"。问法一变，讨论的层次就变了。前者把人引向"AI 会不会替代我"（焦虑问题），后者把人引向"这次抽象升级有哪些特殊性"（工程问题）。

siddontang 给出的特殊性是两个字：**速度**。

过去的抽象升级都花了至少一代人。汇编到 C 花了 20 年，C 到 Java 又花了一代，云到 Serverless 又一代。AI 编程不一样——能力这一代（LLM 能独立完成几千行代码的修改）已经进来了，但新抽象层还没形成。**模型可以生成几千行代码，可我们还没解决如何精确表达意图、如何管理长期 Context、如何定义权限边界、如何 Debug 非确定性系统，也还没有针对 Agent 的测试、Eval 和 Observability**。

"能力下一代，方法论没跟上"——这是他最核心的判据。它不悲观也不乐观，只描述一个具体的现状：模型能做的事和工作流能接住的事之间，gap 巨大。

## 二、编程关系变了：从"操纵代码"到"操纵智能系统"

siddontang 的第二组判断是编程关系的结构性变化。过去更像 `人 → Programming Language → Computer`，未来越来越可能变成 `人 → Intent → Agent → Programming Language → Computer`。

| 关系节点 | 过去 | 现在 / 未来 |
|---|---|---|
| 人操作的对象 | 代码 | 一个能生成 / 修改 / 运行 / 测试代码的智能系统 |
| 代码的位置 | the interface we operate | the artifact the system generates |
| 核心问题 | How do I write this code? | How do I make the system reliably produce the right software? |

最后一句尤其重要——**"这其实已经不是同一种工程学"**。

"写代码"和"让系统可靠地产出正确的软件"，听起来是同一件事的两种说法，拆开差别巨大：

- 前者假定程序员是**作者**——他直接控制每个字符、每行、每个函数。
- 后者假定程序员是**指挥**——他通过 Intent + Context + Tools 表达目标，让 Agent 决定具体怎么实现。

作者关心局部正确性（这个函数对不对、这个边界条件是否覆盖），指挥关心系统可靠性（Agent 在长程任务里会不会跑偏、Context 撑爆了会怎样、Test 怎么覆盖非确定性行为）。**两种关心对应两套工程实践、两套训练路径、两套评估标准**。

放在今天的公司里看：多数时候，"写代码"和"让系统可靠地产出软件"是同一个人做的，但**两件事背后的能力栈并不相同**。前者是程序员的老基本功（语法、数据结构、算法、设计模式），后者是 Agent 时代的新基本功（Spec、Decomposition、Verification、Context Engineering）。这是 siddontang 文章里隐含、但没有展开的一条线，下一节起会逐一落到具体能力上。

## 三、今天最大的麻烦："AI 时代的 C 语言"还没出现

先看历史坐标系：

| 时代 | 稳定的概念体系 |
|---|---|
| Unix | Process、File、Pipe |
| 数据库 | Table、Transaction、SQL |
| Cloud | VM、Object Storage、Function |
| Kubernetes | Pod、Service、Deployment |
| **AI（现在）** | **Prompt、Context、Memory、Tool、Skill、MCP、Sandbox、Workflow、Sub-agent、Harness、Agent SDK** |

这张表的两边有质的不同。前四行的概念体系都已经"稳定下来"——围绕它们形成了课程、工具、最佳实践和工程训练体系。AI 这一行不是——这是一堆候选词，**到底哪些会成为未来真正稳定的一等抽象，现在没人知道**。

siddontang 把这个 gap 写成一个具体的问题：

> 什么叫一个 Agent？它是一个长期运行的 Process？一个按需启动的 Runtime？一个 Workflow？一个有 Memory 和 Tools 的 LLM？还是一个拥有 Identity、Memory、Files、Tools、Runtime 的新型计算实体？

四个候选定义，每一个对应不同的工程实践：
- **Process** → 关注生命周期、信号、并发原语
- **Runtime** → 关注启动开销、隔离、资源回收
- **Workflow** → 关注编排、状态机、回滚
- **新型计算实体** → 关注身份、记忆、工具权限、Eval

这四种定义不是非此即彼——它们都在被不同的人用。但正因为都在用，**今天整个行业还在跑马圈地**。这意味着一个新项目的架构决策不再只是"用 React 还是 Vue"，而是"我们到底在用哪一种 Agent 定义"。

siddontang 没说哪一种会赢，但他说了一句比"选哪种"更值钱的话：

> 最终定义这些抽象的人，很可能也会定义未来十年甚至二十年的软件工程。

这句话把"Coding Agent 竞争"重新定义成"下一代计算机抽象定义权竞争"。它解释了为什么今天所有大厂都在卷 Agent / Harness / Agent SDK / MCP——这些不是"产品线"，是**抽象定义权**。

## 四、Junior Engineer 真正的问题：旧训练梯子断了

第四节是 siddontang 文章里最"焦虑"的一节，但它的判据不是"AI 太强了所以初级岗位没了"，而是**AI 自动化掉的，恰恰是过去用来训练初级工程师的工作**。

> 过去的软件行业存在一套非常成熟的隐性学徒制。新人先写简单功能、修 Bug、做测试，再逐渐维护模块、处理线上问题、理解数据库和分布式系统，最后形成系统设计能力。这些工作表面上是在创造产出，实际上也在训练工程直觉。写很多 CRUD 的价值，不只是 CRUD 本身。在这个过程中，一个新人会逐渐理解边界条件、错误处理、接口设计、测试、线上环境，以及为什么一个看起来正确的改动也可能造成事故。

这段把"训练任务"和"产出任务"分开看，是 siddontang 论证里另一个结构性观察。**修 Bug 的价值不在 Bug 被修了，在修 Bug 的人学到了边界条件**。**写 CRUD 的价值不在 CRUD 写完了，在写 CRUD 的人理解了接口设计**。

AI 替代的是"产出任务"——修一个 Bug、写一个 CRUD、补一个测试。但 AI 替代不了"训练任务"——那个新人从修 Bug 过程里学到的边界条件直觉。AI 替他修了，他学不到。

这才是 Junior Engineer 真正的问题：**如果他们不再通过这些工作积累经验，新的训练机制是什么？** 不是"Junior Engineer 还有没有工作"——能这么问的人，默认了"工作"等于"训练"——而是"如果 AI 把训练任务自动化了，下一代工程师的工程直觉从哪里来"。

siddontang 给出的结论是一个悖论：

> AI 降低了生产代码的门槛，却可能提高了成为优秀工程师的门槛。

这句话把"AI 替代程序员"的焦虑，从 job loss 问题转化成了 capability formation 问题。问题一变，应对也变了——前者让人焦虑"怎么保住工作"，后者让人思考"怎么重建训练机制"。

## 五、新基本功：四个能力，不是一个新话术

siddontang 把"AI 时代的工程师基本功"拆成四个。

### 5.1 Specification

过去最大的困难是"我知道要什么，但不知道怎么写出来"。未来更大的困难是：**你到底知不知道自己要什么**。

这个判据很反直觉——Spec 的难度不在描述，在**精确知道自己要什么**。"怎么写"和"要什么"的相对成本变了。CRUD 时代，"怎么写"贵，所以工程师的价值在"写出来"；AI Coding 时代，"怎么写"几乎免费，价值反倒在"想清楚"。siddontang 用一句话钉死这个翻转："某种意义上，Spec 可能正在成为新的代码。"

### 5.2 Decomposition

过去程序员主要把需求拆成函数和模块。未来还需要决定：什么交给人、什么交给 Agent、什么可以并行、什么必须 deterministic、哪里设置 checkpoint、哪里必须人工审核。

**过去我们设计代码的 control flow。未来可能更多是在设计 intelligence 的 control flow**。

这把这个能力从"代码结构问题"升级成"人机协作架构问题"。代码的 control flow 关心"哪些步骤必须串行、哪些可以并行、谁先谁后"；intelligence 的 control flow 关心"哪些决策权必须留在人手里、哪些可以委托给 Agent、Agent 出错时怎么回退、哪些步骤必须 verify 才能放行下一步"。两者工程难度完全不同：代码 control flow 有完整的图论和静态分析工具支撑；intelligence control flow 没有，因为 Agent 的非确定性让"等价变换"和"形式化验证"都失效了。

### 5.3 Verification

AI 最大的问题不是不会生成，而是**会高速生成"看起来正确"的东西**。因此软件工程的瓶颈很可能从 "How to generate" 转向 "How to verify"。测试、Invariant、Eval、Failure Injection、Security Boundary——这些能力反而会越来越重要。

Verification 不是新东西——单元测试、集成测试、形式化验证都是。但它在 AI 时代的角色变了。过去它是"做完东西之后验一下"，是 quality assurance；未来它是"在生成的每一步卡住错误输出"，是 **execution substrate**。这个转换的关键在于：从"事后检查"到"实时过滤"。前者只在软件交付边界发生，后者必须在 Agent 运行的每一步发生——因为 Agent 不会主动 stop 自己，Verification 必须是它工作流里内嵌的一环。

### 5.4 Context Engineering

真正决定 Agent 表现的，不只是 Prompt，而是它在某个时刻到底看到了什么、记住了什么、拥有哪些工具和权限。所以未来可能出现一种新工程能力：**为智能系统设计正确的 Context**。

它是四个基本功里最容易被低估的一个，因为它和 Prompt 看起来很像。但两者处理的是不同尺度的问题：Prompt 处理"这一次对话我应该告诉 Agent 什么"，Context 处理"Agent 在整个生命周期里能接触到的信息 / 工具 / 权限的总和"。类比过来——Prompt 是一句话，Context 是一个系统。设计 Prompt 是在做语句优化，设计 Context 是在做**信息架构**：哪些信息常驻、哪些临时载入、哪些 Agent 可读、哪些可改、哪些工具在什么条件下可用、什么时候 Context 应该被压缩 / 遗忘 / 持久化。

这四件事合起来，siddontang 的论证里有一张隐藏的图：

| 基本功 | 解决的问题 | 对应的工程能力 |
|---|---|---|
| Specification | "我们要做什么" | 把模糊目标变成可验证描述 |
| Decomposition | "我们怎么一起做" | 编排人 / Agent / 工具的工作流 |
| Verification | "我们怎么知道做对了" | 在执行流中卡住错误 |
| Context Engineering | "我们让 Agent 看到什么" | 设计信息 / 工具 / 权限的供给 |

四条横线、四个维度。它们一起定义的，是"指挥 Agent"的能力栈——和过去"写代码"的能力栈并列，但完全不同。

## 六、"汇编时代"是一个坐标，不是一个贬义词

siddontang 把今天定位为 "AI Programming 的 Assembly Era"——Prompt、Memory、Agent Loop、Tool、MCP、Sub-agent、Harness 这些概念很重要，但其中相当一部分未来会被更高层的 Runtime / Framework / Protocol 吃掉。

"汇编时代"这个隐喻做三件事：

1. **承认今天的具体工作有价值**——没有人否认汇编程序员当年的工作重要，他们建立的计算基础设施是后来所有高级语言的基础。
2. **指出今天的概念大部分会被替代**——大多数 2026 年写的 Prompt 技巧、MCP 协议、Harness 设计，会在 2030 年的某个 Framework 里变成无需显式书写的底层。
3. **回答"那今天该学什么"**——学那个会稳定下来的新抽象层。siddontang 的候选答案是 `Intent + Specification + Context + Tools + Memory + Policy + Runtime + Eval`。

这串词不是一份"工具清单"，是一组**抽象单元的候选集**——每一条都可能成为未来 10-20 年软件工程的基本构件。它也是 siddontang 论证里最难的部分：前面几节都在做历史定位，这一节是**预判**。预判总会被现实打脸，但好的预判会告诉你**该往哪些方向验证**。

这串词的价值不在哪一条最终胜出，而在它把"AI 时代需要什么工程抽象"这个问题问清楚了。问题问对了，答案会被迭代出来；问题没问对，迭代再久也是错的。

## 七、为什么是现在——"抽象层真空"这个窗口

siddontang 文章最容易被忽略的是"为什么是现在"。为什么抽象升级这件事在 2026 年突然变得紧迫？他的论证里有一个隐藏的时间结构：

- 2020 年前后，AI 编程主要是补全（Copilot 类）——抽象层没变，只是工具变聪明了。
- 2023-2024 年，LLM 能力进入能独立完成小段任务的阶段——抽象层开始变（Prompt 出现），但还不足以撼动整个编程关系。
- 2025-2026 年，Agent 范式成熟——LLM 能在长程任务里调用工具、维持 Context、跑测试，编程关系结构性地变了。

**抽象升级不是均匀发生的**——它有快慢两段。慢段是"工具变聪明但抽象不变"（过去十年），快段是"抽象本身被重写"（最近一两年）。siddontang 的论证力量在于：他不是在"AI 编程"这个笼统题目上做判断，而是在"快段已经到来、慢段还没结束"这个具体时间窗上做判断。

这也是为什么"AI 时代的 C 语言还没出现"不是抱怨而是诊断——它说的是：**我们正处在抽象真空期（abstraction vacuum），能力已经跃迁，但新的概念体系还没稳定下来**。这个窗口期会有多久，没人知道。但它给"今天该往哪里学"提供了一个具体的时间约束：学那些可能成为未来一等抽象的候选概念，而不是"今天看起来很热门的具体工具"。

## 八、落回工程现实——今天能做什么

siddontang 的论断是元视角——它讲"AI 编程的结构"，不是"今天怎么用 AI 编程"。但元视角的价值要落回工程现实，否则就是漂亮的废话。把他的判断翻译成今天可做的事：

| 判据 | 对今天的工程含义 |
|---|---|
| 代码从 interface 变成 artifact | 写"被 Agent 读"的代码比写"被程序员读"的更优先——命名、接口、注释、目录结构都在 Agent 视野里 |
| 编程关系从人→Lang→Computer 变成人→Intent→Agent→Lang→Computer | Intent 和 Spec 是新瓶颈，Type system、Property-based test、Eval harness 的投入应该加码 |
| 抽象真空期 | 别在某个 Agent 框架上押重注，但要在"怎么指挥 Agent"上积累能力 |
| Junior 训练梯子断了 | 在团队里主动设计 Agent 时代的"训练任务"——让 Junior 负责 Spec、Verification、Context 设计，不要把他们从这些任务里挤出去 |
| 四个新基本功 | 自己学 + 带团队学：写 Spec、设计人机 Decomposition、设计 Verification 流、设计 Context 的能力 |

最后一条最值得展开。**"带团队学"不是新话术**——它对应的是具体的训练路径设计：

- **Spec 训练**：让 Junior 写"完整描述一个功能"的文档——不是 acceptance criteria 清单，而是 narrative + invariants + failure modes——交给 Senior review。review 的不是写得对不对，是想得清不清。
- **Decomposition 训练**：让 Junior 拆"这个任务谁做、谁 review、Agent 在哪一步插入"。这是 design review 的新版本。
- **Verification 训练**：让 Junior 写"Agent 生成的代码怎么 test"。Test 是新基本功，verification 流是新 design。
- **Context Engineering 训练**：让 Junior 维护"Agent 知道什么"的 context——CLAUDE.md、project rule、tool registry、permission matrix。

这些不是"AI 时代新话术"——它们是具体的工程任务，能在团队里直接执行。

## 九、一章小结

siddontang 那篇文章真正在讲的不是"AI 编程的现状"，是**"AI 编程处在哪一段历史"**。他给出三个判据：

1. **结构判据**——编程关系从 `人 → Lang → Computer` 变成 `人 → Intent → Agent → Lang → Computer`，代码从 interface 变成 artifact。
2. **方法论判据**——能力下一代，方法论没跟上，新基本功（Spec / Decomposition / Verification / Context Engineering）正在重新定义。
3. **历史坐标判据**——我们处在 "AI Programming 的 Assembly Era"，最终稳定的可能是 `Intent + Spec + Context + Tools + Memory + Policy + Runtime + Eval` 一组新抽象。

这三个判据连起来，他给的不是一份"AI 时代程序员生存指南"，而是一个**判断时间窗的工具**：慢段已经过去、快段正在发生、真空期还看不到头。在这个窗口里，最值得投入的不是某个具体工具，而是**那几个可能成为未来一等抽象的候选能力**。

换成更短的话：今天学的是未来不会被替代的部分，**未来不被替代的部分 = 抽象层升级需要的工程能力**。

## 三个常被问错的问题

> **为什么不说"AI 不会替代程序员"或"AI 会替代程序员"？** 因为这个问题问错了。它把"AI 编程"看成"AI vs 程序员"的零和博弈。siddontang 的论证把它换成"抽象升级 vs 训练梯子"——前者关心"编程关系怎么变"，后者关心"下一代工程师怎么成长"。两个问题都重要，但答案完全不同：**前者的答案在工程实践里（怎么指挥 Agent、怎么写 Spec、怎么设计 Context），后者的答案在教育体系里（怎么设计新的训练梯子）**。混在一起讨论的人会一直焦虑，分开讨论的人会各自找到具体的应对路径。
>
> **为什么 siddontang 不给"AI 时代的 C 语言"一个明确候选，而是列一串抽象？** 因为他很诚实地承认"没人知道"。那一串词（Intent / Specification / Context / Tools / Memory / Policy / Runtime / Eval）是候选集，不是答案。它的价值不在"选哪个"，在"问题问对了"。**问题问对 = 抽象层真空期里最稀缺的事**——它告诉我们该往哪几个方向投入验证精力。
>
> **为什么"四大新基本功"不是"AI 时代新话术"？** 因为它们每一个都对应具体的工程任务，能在团队里直接执行。Spec 训练 → 写完整功能描述文档并 review；Decomposition 训练 → 拆"谁做 / 谁 review / Agent 在哪一步"；Verification 训练 → 设计 Agent 生成代码的 test 流；Context Engineering 训练 → 维护 CLAUDE.md、project rule、tool registry、permission matrix。这些不是 buzzword，是**可以排进 sprint 的训练任务**。