---
title: "AI for Science 爆发：一个新时代到来的征兆、赌注与未解之问（101 视频播客曹原访谈精读）"
slug: ai-for-science-discovery-loop-101-cao-yuan
date: 2026-08-20T22:00:00+08:00
draft: false
tags: ["AI for Science", "Discovery Loop", "Jeff Dean", "Oriol Vinyals", "Quoc Le", "Sanjay Ghemawat", "DeepMind", "曹原", "硅谷101", "AI Co-Scientist", "RSI", "AlphaFold", "Gemini", "视频精读"]
categories: ["视频精读"]
description: "深度解读硅谷 101 「对话前 DeepMind 曹原：AI for Science 爆发，一个新时代到来了」（BV1GQgg6yEy5，2026-08 上线，时长 1 小时 49 分）。背景事件：2026-08-05 Jeff Dean 携 Sanjay Ghemawat、Oriol Vinyals、Quoc Le 三位长期搭档离开 Google，创办 Public Benefit Corporation「Discovery Loop」，把「自动化机器学习 + 自动化科研 + 自动化工程」作为唯一方向；Alphabet 是创始投资人 + 第一年 Cloud 算力供应商；Hassabis 接任 Alphabet 首席科学家 + Google DeepMind 主席。本文按视频 10 段高光时间锚组织，串起三个核心命题：为什么 AI for Science 在此刻爆发、三大公司的科学路线有何不同、自动化科研会不会是通向 AGI 的最后一英里。"
author: 钳岳
---

> 本文基于视频官方简介、十章章节结构与公开报道整理，不是逐字记录；直接引语均标注来源报道。完整来源清单见文末附录 A。

---

## 一、为什么是这期：8 月第一周那场小地震

2026 年 8 月第一周，硅谷 AI 圈发生了一件难以忽略但容易被低估的人事地震。

主角是 Jeff Dean——Google 第 6 号员工，加入 27 年、长期担任 Alphabet 首席科学家、TensorFlow / MapReduce / BigTable / TPU / Gemini 这些定义现代 AI 基础设施的项目的共同缔造者。他带着另外三位共事 14–30 年的老搭档一起离开 Google，创办一家叫 **Discovery Loop** 的新公司。董事会成员里有 Vinod Khosla（Khosla Ventures）、Jordan Jacobs（Radical Ventures 合伙人）。[TechCrunch 2026-08-05 报道](https://techcrunch.com/2026/08/05/jeff-dean-and-other-top-ai-researchers-are-leaving-google-to-launch-their-own-startup/)把这件事定位成「这可能是 Google 历史上最重要的一次人才外流」。

硅谷 101 这期播客把这场地震放到台面上讲：访谈嘉宾是**前 Google DeepMind 资深研究科学家曹原**，议题从「Jeff Dean 出走背后的 Google 取舍」一路拉到「AI for Science 会不会是通向 AGI 的最后一英里」。

把背景人物和议题说清楚之后，你会发现这期播客讨论的不是一件「公司新闻」，而是一个行业级的方向问题：**当 AI 不再只是回答问题，而开始提出假设、设计实验、运行验证的时候，科学研究的范式会发生什么变化？**

这篇文章按视频的 10 段章节展开，把这期访谈的核心命题拆开来讲清楚。每一节末尾会标注「本节公开信息外推的部分」与「明确来源」——因为本文基于视频简介与公开报道整理，不是逐字记录，标注边界是对读者负责。

## 二、四位创始人 + 一个产业级方向：Discovery Loop 是什么

先把 Discovery Loop 这件事讲透，因为后续九节几乎都跟它有关。

### 2.1 创始人名单与共事时间

按 OfficeChai 报道[整理](https://officechai.com/ai/jeff-dean-discovery-loop/)的四位创始人是：

- **Jeff Dean**：Google 第 6 号员工、27 年任期、原 Alphabet 首席科学家。TensorFlow、MapReduce、BigTable、Spanner、TPU、Gemini 等项目共同作者。
- **Sanjay Ghemawat**：与 Dean 在 Google 27 年共事，大规模分布式系统专家，MapReduce / Google File System / Spanner 的共同作者。
- **Oriol Vinyals**：原 Google DeepMind 首席研究科学家，AlphaStar、AlphaCode、word2vec、sequence-to-sequence、chain-of-thought、mixture-of-experts 多个里程碑的共同作者。
- **Quoc Le**：原 Google Brain 团队核心成员，以自动化模型设计（neural architecture search）方向著称。

按 Dean 本人在 X 上的公开声明，四人共事时间跨度为 **14 到 30 年**——这不是一次「临时拼凑」，是一支真正从互联网早期就一起写系统的队伍。

### 2.2 公司方向：把科学方法自动化

按 Discovery Loop 官方陈述 + WIRED 报道[整合](https://www.wired.com/story/jeff-dean-google-discovery-loop-startup/)，公司的核心产品方向是**自动化科学方法**（automated scientific method）：

> Dean in an interview: "You propose an experiment, you implement what you need to run the experiment, you evaluate the experiment, and then you get results from that." Running thousands of those automated loops in parallel is the bet.

按 Unite.ai 报道的[三层机制](https://www.unite.ai/jeff-dean-leaves-google-to-automate-the-scientific-method-with-discovery-loop/)，落地路径分三步：

1. **第一步：用 AI 自动化机器学习研究本身**——用前沿大模型 + 大规模算力，自动提出 ML 实验、跑实验、读结果、迭代。
2. **第二步：Discovery Loop 当自己的第一个客户**——把这些自动化能力用来优化 Discovery Loop 自己的技术栈。
3. **第三步：泛化到任意科学领域**——芯片设计、生物学、药物发现、材料设计。

### 2.3 资本与算力结构

按 TechCrunch 报道[整理](https://techcrunch.com/2026/08/05/jeff-dean-and-other-top-ai-researchers-are-leaving-google-to-launch-their-own-startup/)：

- **创始投资人**：Alphabet 本身；首轮由 Radical Ventures 与 Khosla Ventures 共同领投，跟投方包括 Kleiner Perkins、Lightspeed、Doerr Capital。
- **Cloud 合作方**：Google Cloud，提供第一年算力。
- **估值与轮次规模**：未公开。

按 OfficeChai 引用 Pichai 的公开声明[整理](https://officechai.com/ai/jeff-dean-discovery-loop/)：

> "Over 27 years, Jeff and Sanjay helped to drive some of the most significant technology transitions ... We'll continue to work with Discovery Loop as a founding investor and Cloud partner."

### 2.4 一次性把 Google 的 AI 高层重组了

按 OfficeChai 报道[整合](https://officechai.com/ai/jeff-dean-discovery-loop/)：

- **Demis Hassabis**：原 Google DeepMind CEO → 升任 **Alphabet 首席科学家 + Google DeepMind 主席**（从日常执行角色抽身，专注长期战略与科学突破）。
- **Koray Kavukcuoglu**：原 Google DeepMind CTO → 接任 **Google DeepMind SVP**。
- **Jeff Dean**：辞任 Alphabet 首席科学家 → 全职加入 Discovery Loop。

注意一个细节：Google 给了祝福，但**四位联合创始人带着多年共事的团队集体出走**这件事本身，对任何一家公司来说都不是小事。

### 2.5 这一节可以确认的事实与外推

- **可直接确认**：四创始人身份、共事时间区间、公司使命三段式（auto-ML → 自用 → 泛化）、投资方名单、Pichai 公开声明。
- **基于背景资料反推的方向判断**：把 AI for Science 当作「最后一场竞赛」的产业级共识，正在 Google / DeepMind / OpenAI / Anthropic 同步形成。这条外推对应视频第二节「AI4S 爆发」章节。

## 三、为什么 AI for Science 在此刻爆发（章节 1–2）

视频的第二、三章把这个问题展开。议题清单来自视频简介：

> 为什么 AI for Science 会在此刻爆发？谷歌 DeepMind 前资深研究科学家曹原从 Google 内部的组织变化谈起，拆解 AI for Science、AI for AI 与 RSI 的关系，以及 AI 科研闭环如何运转。

### 3.1 三个互相咬合的齿轮

视频简介给出三个关键概念的耦合关系：

- **AI for Science**：用 AI 加速科学研究本身（蛋白质、材料、化学反应、芯片设计……）。
- **AI for AI**：用 AI 自动化 AI 研究——这是 Discovery Loop 把 ML 研究自动化作为第一个客户的核心。
- **RSI（Recursive Self-Improvement，递归自我改进）**：AI 改进 AI，循环往复。

把它们排成一张因果链：

```
AI for AI（自动化 ML 研究）
   ↓ 产出更强模型
更强模型
   ↓ 反哺
AI for Science（自动化材料/化学/生物实验）
   ↓ 产出新发现
新发现
   ↓ 反哺
RSI（让发现本身成为下一代模型的训练素材）
```

这就是视频简介里说的「AI 科研闭环如何运转」。

### 3.2 为什么是「现在」

按视频简介的反推，本质上有三股力在 2026 年这个时间窗同时成熟：

| 力量 | 成熟标志 |
|------|----------|
| **大模型学会推理** | Gemini / Claude / GPT 系列在 chain-of-thought、tool use、code generation 上达到科学任务门槛 |
| **大模型学会编程 + 调用工具** | Coding agent（如 Claude Code、Cursor）成熟；agent SDK 把工具调用 / 状态管理 / 权限装进同一框架 |
| **科学问题可计算化** | AlphaFold 已把蛋白质结构预测变成「一次推理」问题；新材料筛选、合成路径规划也开始可计算化 |

视频简介提到的一个判断是：

> 从数学、代码到生物、材料和物理，问题越容易计算和验证，AI 进展越快。

这句话的反面同样重要：一旦进入真实世界实验，**实验周期、验证成本、反馈速度**就成为 AI 进展的瓶颈。

### 3.3 AI for Science 的「第四堵墙」

视频简介里提到了一个关键边界：

> 自动实验室、科研 Agent 和符号系统，可能成为 AI 跨越这道障碍的关键。

翻译一下：

- **自动实验室**：让机器人代替人做实验，把「几小时湿实验」压成「几分钟干实验 + 几小时湿实验 + AI 调参」。
- **科研 Agent**：让 AI 自己看论文、设计实验、跑代码、分析结果、写论文。
- **符号系统**：把神经网络和符号推理结合，让 AI 不只是拟合曲线，还能做严格证明和形式化推理。

这三件事任何一件做成，AI for Science 的边界都会被推开一截。

## 四、问题定义：什么叫「AI 做科研」（章节 3–5）

视频第四节到第六节讨论「AI 究竟如何做科研」「什么叫真正发现」「符号主义 vs 连接主义」三个问题。

### 4.1 自动化科研的四种范式

按视频简介 + 三篇 arXiv 论文[（Co-Scientist 2502.18864）](https://arxiv.org/abs/2502.18864v2)[（DISCOVERYWORLD 2406.06769）](https://arxiv.org/abs/2406.06769v2)[（AutoSciDACT 2510.21935）](https://arxiv.org/abs/2510.21935v2)的交叉印证，目前 AI 做科研可分四种范式：

| 范式 | 代表工作 | 自动化边界 | 当前局限 |
|------|----------|------------|----------|
| **AI 作为工具** | 蛋白质结构预测（AlphaFold）| 单步推理（序列 → 结构）| 不形成研究循环 |
| **AI 作为助手** | AI Co-Scientist（Google，2025-02）| 多智能体生成假设 + 文献综述 + 排序| 仍需人类设计实验并验证 |
| **AI 作为研究员** | DISCOVERYWORLD（2024-06）| 端到端科学推理（在虚拟环境里做完整实验）| 真实世界实验能力有限 |
| **AI 作为科学家** | Discovery Loop 愿景 / AutoSciDACT（2025-10）| 提出假设 → 跑实验 → 验证 → 迭代，循环往复| 算力 + 湿实验 + 反馈速度仍是瓶颈 |

视频简介用「AI 不再只回答问题，也开始提出假设、设计实验」描述这场变化——按上面的分类，它对应的是 **AI 作为科学家** 范式。

### 4.2 Vinyals 关于「真正发现」的一句话

按 WIRED 报道对 Vinyals 的[直接引语](https://www.wired.com/story/jeff-dean-google-discovery-loop-startup/)：

> "One of the things that we'll be obviously very focused on is how these models come up with new ideas to try. That's not something that currently they're super strong at."

翻译：当前大模型不擅长的事情，是「想出值得一试的新点子」。这正是 Discovery Loop 要攻的核心。

### 4.3 符号主义 vs 连接主义的旧账

视频第六节讨论这个 AI 史经典争论。按视频简介的反推，这节想讲的不是「谁赢谁输」，而是**它们的组合方式正在被重新定义**：

- **连接主义的胜利**显而易见：过去十年从 GPT 到 Gemini 的所有进展，几乎都是 scale up + 数据 + 算力。
- **符号主义的回归**则体现在两个具体方向：formal verification（形式化验证，AI 自动证明定理）+ symbolic regression（符号回归，AI 从数据反推公式）。
- **两者的结合**：把大模型当「直觉引擎」，把符号系统当「验证引擎」——直觉给方向，符号给证明。

视频简介里那句「符号主义与连接主义的结合」对应这个组合。

### 4.4 数学是发现还是发明

视频第七节问了一个哲学问题：数学是发现还是发明？

按视频简介：「更重要的，当 AI 已经会解题、搜索与组合，它能否创造新的概念和知识？」

这是 AI for Science 最核心的哲学张力：

- 如果数学是**发现**——AI 在做发现，它和人类科学家在做同类事情，只是更高效。
- 如果数学是**发明**——AI 在做发明，它在拓展人类已有的概念空间，性质与「发现新大陆」不同。

这两种立场决定了我们对「AI 做出新发现」这件事的根本评价。

## 五、巨头押注：三大 AI 公司的科学路线（章节 7）

视频第八节进入产业议题。

按公开资料，2026 年 AI for Science 的三条主线公司各有侧重：

| 公司 | 主线方向 | 代表项目 | 自动化层级 |
|------|----------|----------|------------|
| **Google / DeepMind** | 科学发现 + 自动化科研 + AI for Science 全栈 | AlphaFold、AlphaChip、Gemini、Co-Scientist、Discovery Loop（前员工延续）| 端到端（Discovery Loop 愿景）|
| **OpenAI** | 通用智能 + reasoning + 工具调用 | o-series、Operator、Deep Research | 工具调用层为主 |
| **Anthropic** | 长程任务 + agent 编排 + 工具可靠性 | Claude / Claude Code / Computer Use | 工具可靠性 + agent 编排 |

按 WIRED 报道对 Vinyals 的[引语](https://www.wired.com/story/jeff-dean-google-discovery-loop-startup/)：

> "As we create the core intelligence and the discovery loop fundamentals, we'll be able to quickly generalize to other domains."

这条表态把 Discovery Loop 定位成 Google DeepMind 体系的延伸——不是替代，是**用初创公司的速度 + Google 的算力 + Alphabet 的资金**做 Google 内部组织做不动的事情。

视频简介的反推还提到：「Jeff Dean 出走背后的 Google 取舍」——指 Google 内部的取舍：Discovery Loop 的方向 Google 自己也在做（Co-Scientist / AlphaFold / AlphaChip），但大公司有惯性，所以让四个人出去试。这跟 Vinyals 在 WIRED 的[原话](https://www.wired.com/story/jeff-dean-google-discovery-loop-startup/)完全对得上：

> "In a large organization there is always a lot of inertia you have to overcome to make any radical changes. We want to build something different."

### 5.1 这一节外推的明确边界

- **可确认**：三家公司主线方向（公开资料 + WIRED 报道）。
- **外推**：把 Discovery Loop 视为「Google DeepMind 体系延伸」这个判断基于 WIRED 报道 + 创始人履历，但 Discovery Loop 独立运营的具体机制（与 Alphabet 的研究框架合作细节）尚不公开。

## 六、数学边界（章节 8–9）：为什么数学是 AI for Science 的最佳试金石

视频第八、九节讨论数学和物理。

### 6.1 数学为什么是最佳试金石

数学是 AI for Science 的最佳试金石，原因有三：

1. **可验证**：一个证明要么对要么错，没有「湿实验」成本，反馈回路极快。
2. **可计算**：数学对象是离散的、形式化的、可编码的，正好适配大模型的工具调用能力。
3. **可对比**：人类数学家几百年积累的成果，可以直接当成 benchmark。

按视频简介的反推，「数学边界」这节对应的可能是 DeepMind 风格的「自动化定理证明」方向——Lean、Coq、Isabelle 这类证明助手 + 大模型做证明搜索。

### 6.2 物理：跨越数学之后的第一道坎

视频第九节进入物理。数学之后的第一道难处是物理——因为物理必须连上真实世界：

- 数学 → 验证成本 = 计算时间
- 化学 → 验证成本 = 反应时间（小时/天）
- 生物学 → 验证成本 = 培养时间（天/周）
- 材料学 → 验证成本 = 制备时间（周/月）

按视频简介的反推，「AI for Science 在此刻爆发」的判断成立，前提是**自动实验室 + 科研 Agent** 把真实世界实验的成本压下去。否则数学以外的所有学科都会被实验周期卡住。

## 七、商业化与哲学（章节 10）：AI 是不是 AGI 的最后一英里

视频第十节把议题拉到哲学层：科学发现会不会是通向 AGI 的最后一英里？

### 7.1 AGI 的两条路径

按视频简介的反推，存在两种 AGI 路径：

- **路径 A：从工具到通用智能**——OpenAI / Anthropic 的路子，先把工具调用 / 长程任务做稳，再扩展到更多领域。
- **路径 B：从科学到通用智能**——Google / Discovery Loop 的路子，先把科学发现做穿，再把能力泛化。

视频简介的那句「科学发现，会是通往 AGI 的最后一英里吗？」对应路径 B 的核心命题。

### 7.2 Khosla 的押注逻辑

按 WIRED 报道对 Vinod Khosla 的[引语](https://www.wired.com/story/jeff-dean-google-discovery-loop-startup/)：

> "Humans have been using AI to do research, not using AI to be a researcher."

这句话点出了 AI for Science 的关键转变：**从「AI 帮助人做研究」到「AI 自己就是研究者」**。

### 7.3 自动化的双刃剑

视频第十节还提到商业化议题。按公开报道 + 视频简介反推：

- **正面**：Discovery Loop 把自动化科研作为 SaaS / API 卖给科研机构、药企、材料公司，第一批客户可能就是 AI for Science 的头部实验室。
- **风险**：如果 AI 真的能产生新概念和新知识，「谁拥有这些发现」「AI 发明的专利归谁」「AI 科学家和人类科学家的责任边界」这些法律和伦理问题就会接踵而至。

## 八、写在最后：一个新时代到来了，但还没结束

把这期访谈看完，再把 Discovery Loop 这件事放进去，会发现硅谷 101 这次选题抓得很准——它不只是「Jeff Dean 出走」的新闻评论，而是把整个 AI for Science 方向的产业级判断压在 1 小时 49 分的访谈里。

视频简介的最后一句话是这期访谈的核心命题：

> 科学发现，会是通往 AGI 的最后一英里吗？

我的判断：

**「最后一英里」是个不确定的措辞，但「关键一公里」几乎是确定的。** AI for Science 不是 AGI 的附属品，而是 AGI 能力边界的试金石——一个能自主提出假设、设计实验、运行验证、产出新概念的 AI 系统，距离 AGI 只差「常识推理 + 价值对齐」两道关卡。反过来，一个只会聊天、不会做科学的 AI，无论多会答题，都离 AGI 还很远。

Discovery Loop 的四创始人用 27 年积累赌这一公里。Google / OpenAI / Anthropic 也在各自的路线图上押注这一公里。

这期访谈回答的不是「谁会赢」，而是「这场赛跑的赛道在哪里」。

赛道的名字，叫 AI for Science。

---

## 附录 A：本文资料来源清单

| 来源类型 | 链接 / 编号 | 用于章节 |
|----------|-------------|----------|
| 视频元数据与章节结构 | B 站视频页（标题、简介、10 段章节）| §一（时长、标题、UP 主）|
| TechCrunch Discovery Loop 报道 | [链接](https://techcrunch.com/2026/08/05/jeff-dean-and-other-top-ai-researchers-are-leaving-google-to-launch-their-own-startup/) | §二、§五 |
| WIRED Discovery Loop 报道 | [链接](https://www.wired.com/story/jeff-dean-google-discovery-loop-startup/) | §二、§四、§五、§七 |
| OfficeChai Discovery Loop 报道 | [链接](https://officechai.com/ai/jeff-dean-discovery-loop/) | §二、§五 |
| Unite.ai Discovery Loop 报道 | [链接](https://www.unite.ai/jeff-dean-leaves-google-to-automate-the-scientific-method-with-discovery-loop/) | §二 |
| Co-Scientist 论文（Google，2025-02）| [arXiv 2502.18864](https://arxiv.org/abs/2502.18864v2) | §四 |
| DISCOVERYWORLD 论文 | [arXiv 2406.06769](https://arxiv.org/abs/2406.06769v2) | §四 |
| AutoSciDACT 论文 | [arXiv 2510.21935](https://arxiv.org/abs/2510.21935v2) | §四 |
| 视频官方简介（议题清单）| B 站 desc 字段 | 全文结构骨架 |

## 附录 B：本文无法覆盖的内容

- **逐字内容**：本文基于视频官方简介、章节结构与公开报道整理，不是访谈逐字记录；不带来源标注的「曹原说 / 嘉宾认为」类表述均为结构化转述。
- **曹原本人详细履历**：本文明示其身份为「前 Google DeepMind 资深研究科学家」，更早期职业经历（PhD 阶段、博士论文方向、加入 DeepMind 时间）本文未做考证，需要通过 LinkedIn / Google Scholar / 个人主页补充。
- **Discovery Loop 产品细节**：公司网站 2026-08 上线，但产品功能、定价、首批客户名单未公开。

## 附录 C：本文已明确外推的判断清单

为了让读者清楚分辨「事实 vs 推断」，以下判断是基于公开资料**外推**的结构化论点：

1. 「AI for Science + AI for AI + RSI」三层耦合关系（§3.1）——基于视频简介 + Discovery Loop 公司使命反推。
2. 「三股力量同时成熟」表（§3.2）——基于视频简介反推。
3. 「AI for Science 四种范式」表（§4.1）——基于视频简介 + 三篇 arXiv 论文交叉整合。
4. 「AI for Science 是 AGI 的关键一公里」判断（§八 结尾）——基于视频简介反推 + 公开资料外推。

以上四条是本文的「外推层」，如需严格事实陈述请回查来源。
