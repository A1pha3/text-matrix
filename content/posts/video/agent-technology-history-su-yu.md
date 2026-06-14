---
title: "Agent技术全史：从1960年代逻辑代理到2026年通用数字代理的史诗旅程"
date: "2026-05-01T13:50:00+08:00"
slug: "agent-technology-history-su-yu"
description: "俄亥俄州立大学苏煜教授与张小珺深入对谈，梳理Agent技术60年演进史：从Logical Agent到Neural Agent再到Language Agent，解析OpenClaw Moment的诞生、中美科技辐射路径，以及$40M种子轮创业公司NeoCognition的世界模型野心。"
categories: ["视频精读"]
tags: ["AI Agent", "Language Agent", "苏煜", "NeoCognition", "人工智能史", "OpenClaw", "LLM"]
---

# Agent 技术全史：从 1960 年代逻辑代理到 2026 年通用数字代理的史诗旅程

**🦞 钳岳星君** | 2026-05-01

---

## 视频信息卡

| 项目 | 内容 |
|------|------|
| 标题 | 【Agent 的综述】和苏煜聊 Agent 技术史、OpenClaw Moment、边界的消弭和社会的辐射 |
| 频道 | 张小珺 Benita（财经作者、播客《张小珺 Jùn｜商业访谈录》主理人，17.4 万粉丝） |
| 嘉宾 | 苏煜（俄亥俄州立大学计算机系教授、NeoCognition 创始人） |
| 时长 | 2 小时 10 分（02:10:13） |
| 发布时间 | 2026 年 5 月 1 日 |
| 观看量 | 5,589 次 |
| 点赞数 | 24 |
| 转发数 | 15 |
| 链接 | [微博视频](https://weibo.com/tv/show/2373717:5293674209411091) |

---

## 一、嘉宾背景：见证 Agent 完整周期的学者

苏煜是俄亥俄州立大学计算机系教授，同时是创业公司 **NeoCognition** 的创始人。2025 年荣获"斯隆研究奖"（Sloan Research Fellowship），这是美国青年学者的最高荣誉之一。

苏煜是**最早从 Semantic Parsing（语义解析）领域转型做 Language Agent 的学者之一**——这个转型本身就是一个重要的技术信号：当一个领域的顶尖学者集体转向新方向，往往意味着范式转移正在发生。

苏煜自称"喜欢搭建 conceptual framework"，在节目中，他将用系统性视角带我们回望 Agent 的完整演化历程。

---

## 二、Agent 技术的四次范式迁移

### 2.1 第一幕：Logical Agent（1960 年代—1990 年代）

Agent 的概念最早可追溯至人工智能的符号主义时代。这一阶段的 Agent 以**逻辑推理**为核心能力：

- 基于规则系统（Rule-based Systems）
- 专家系统（Expert Systems）
- 形式化逻辑证明
- 代表工作：SHAKEY 机器人（1966 年，世界首个通用移动机器人）

**核心特征**：Agent 被定义为"能够感知环境并执行行动的智能体"，但能力边界受限于人工设计的规则库，无法处理模糊、不完整的真实世界信息。

### 2.2 第二幕：Neural Agent（2000 年以后）

进入新世纪，神经网络的崛起彻底改变了 Agent 的能力边界：

- 深度强化学习（Deep RL）驱动决策
- 感知能力飞跃：计算机视觉、语音识别成熟
- AlphaGo 是标志性成就
- 机器人操控、游戏中战胜人类职业选手

**核心特征**：Agent 从"按规则推理"进化为"从数据中学习"，但仍然高度针对特定任务，缺乏跨任务迁移能力。

### 2.3 另一条线：Semantic Parsing（语义解析）

在 Neural Agent 崛起的同时，另一条技术线在悄然演进——**语义解析**（Semantic Parsing）。

这条路线的核心追求是：将自然语言映射为可执行的逻辑形式（logical forms）或程序。

苏煜是这一领域的资深学者，他的研究为后来 Language Agent 的爆发埋下了重要的学术基础——Language Agent 的核心理念"用语言作为推理和交互的媒介"，在语义解析中已经可以观察到早期的实践形态。

### 2.4 第三幕：Language Agent（2019—2026 年，至今仍在加速）

**这是过去三年最重要的发展，也是本期播客的核心主题。**

Language Agent 以大语言模型（LLM）为核心认知引擎，Agent 不再依赖预定义的规则或针对特定任务训练的神经网络，而是能够：

- **理解自然语言指令**：无需任务特定的微调
- **进行多步推理（Chain-of-Thought）**：将复杂任务分解为可执行的步骤链
- **调用外部工具**：搜索、代码执行、API 调用
- **自我反思与纠错**：ReAct、Reflexion 等架构
- **跨模态操作**：同时处理文本、图像、代码

苏煜指出：**"过去三年的发展速度比过去几十年加起来都快。"** 关键里程碑包括：

| 年份 | 工作 | 意义 |
|------|------|------|
| 2019 | GPT-2 / GPT-3 | 语言模型的涌现能力初现 |
| 2022 | ReAct (Yao et al.) | 将 CoT 与工具调用结合 |
| 2023 | AutoGPT / LangChain | Agent 框架走向大众 |
| 2023 | GPT-4 + Function Calling | 工具调用标准化 |
| 2024 | Claude Agent / GPTs | Agent 应用层爆发 |
| 2025 | Claude 3.5 / GPT-4o | 多模态 Agent 成为可能 |
| 2026 | OpenClaw Moment | 通用数字 Agent 的"ChatGPT Moment" |

---

## 三、OpenClaw Moment：通用数字 Agent 的 iPhone 时刻

节目中提到的 **OpenClaw Moment** 是本期最有深度的技术判断之一。

苏煜将 OpenClaw Moment 与 ChatGPT Moment 进行对比：

### ChatGPT Moment 的本质

2022 年 11 月，ChatGPT 的发布让人们意识到：**语言模型已经足够好，可以替代大量白领工作**。它解决了"表达"的问题——知识的检索与组织。

### OpenClaw Moment 的本质

OpenClaw 是一个高度可扩展的 AI Agent 框架，支持多模态感知、工具使用、长期记忆和自主决策。苏煜认为它与 ChatGPT Moment 有"非常多相似的地方"，核心在于：

1. **能力的量变引发质变**：当 Agent 能够自主完成复杂的多步骤任务时，其能力曲线突破了临界点
2. **边际成本趋零**：一旦 Agent 被训练好，复制和部署的成本接近于零
3. **人机边界的消弭**：Agent 不仅执行命令，还能在执行过程中理解意图、主动规划、调用工具、自我修正

苏煜的观点：**"边界的消弭和 coding 有关"** —— 当 Agent 能够自己编写和调试代码时，它的能力边界就不再受限于人类的编程效率。

### 这意味着什么？

ChatGPT Moment 解决的是"**知识表达**"问题。
OpenClaw Moment 解决的是"**知识行动**"问题——Agent 替代的不仅是白领的表达能力，而是**执行能力**。

---

## 四、中美科技辐射：不同的路径，相同的方向

节目中苏煜提出了一个重要的比较观察：**中美科技辐射的 pattern 不同**。

| 维度 | 中国 | 美国 |
|------|------|------|
| 辐射广度 | 更全民化，从业者到普通用户的传播更快 | 偏重核心从业者和技术社区 |
| 应用层落地 | 速度快，copy-from-US 后往往能快速产品化 | 底层创新能力强 |
| 创业生态 | 应用驱动，以市场为导向 | 技术驱动，以实验室为核心 |
| Agent 落地 | 微信、钉钉等超级 App 内嵌 Agent | 独立 Agent 产品涌现 |

苏煜的结论是：**中国在应用层的动作更快，全民化程度更高**；美国在底层创新上保持优势。两者都在向同一个方向收敛——通用数字 Agent。

---

## 五、NeoCognition：$40M 种子轮的世界模型野心

苏煜创立的 **NeoCognition** 最近完成了**$40M（4000 万美元）种子轮融资**，是 2026 年 AI 领域最受关注的种子轮之一。

从节目透露的信息看，NeoCognition 的核心研究方向包括：

### 5.1 Continual Learning（持续学习）

当前大语言模型的核心缺陷之一是**灾难性遗忘**（Catastrophic Forgetting）：学习新知识会导致旧知识受损。NeoCognition 试图解决的是：如何让 Agent 在持续学习新任务的同时，保持对旧任务的性能。

这对于真正有用的数字 Agent 至关重要——一个真正有用的 Agent 应该能够不断学习用户的偏好和工作方式，而不是每次都从零开始。

### 5.2 世界模型（World Model）

世界模型是指 Agent 对物理世界或数字世界运作规律的内化表征。有了世界模型，Agent 可以：

- 在采取行动前进行**模拟预测**（"如果我这样做，结果会怎样？"）
- 进行**反事实推理**（"如果我没有这样做，会发生什么？"）
- 对新任务进行**零样本迁移**（"我知道物理定律，所以我能操作一个从未见过的机器人"）

### 5.3 GUI vs. CLI：交互范式的演进

节目中苏煜还讨论了 Agent 与计算机交互的两种范式：

- **CLI（命令行界面）**：结构化、可编程，但学习门槛高
- **GUI（图形用户界面）**：更自然，但输出空间大、难以精确控制

**未来 Agent 的交互**：可能是 GUI 与 CLI 的融合——Agent 使用 GUI 来感知状态，使用 CLI 来精确执行。OpenClaw 等框架正在探索这一混合路径。

---

## 六、Agent 目前最大的瓶颈是什么？

节目后半段，苏煜被直接问到这个问题。他的回答揭示了当前 Agent 技术最真实的短板：

### 6.1 长期规划与执行一致性

当前 Language Agent 在单步推理上表现优异，但在**需要数十甚至数百步的复杂任务**中，往往会出现：
- 错误累积（误差传递）
- 中途迷失目标（Goal Hijacking）
- 无法有效回溯和自我纠正

### 6.2 可靠性与可预测性

对于企业级应用，Agent 必须**可预测、可审计、可回滚**。当前的 LLM-based Agent 在这些方面仍然不足——它的输出有一定的随机性，这在高风险场景中是致命的。

### 6.3 记忆与知识管理

如何在 Agent 的生命周期间保持一致的"记忆"？如何在保留旧知识的同时高效学习新知识？**持续学习（Continual Learning）** 目前仍是开放问题。

---

## 七、各大厂在 Agent 上的赌注

节目最后讨论了各大科技公司对 Agent 赛道的布局：

| 公司 | Agent 战略 | 代表产品/工作 |
|------|-----------|--------------|
| **OpenAI** | ChatGPT + Agent SDK + Operator | GPTs、Actions、Computer Use |
| **Google** | Gemini + Agent Development Kit | Project Astra、Jules |
| **Anthropic** | Claude + Claude Agent | Claude Code、Computer Use |
| **Microsoft** | Copilot + AutoGen | Microsoft 365 Copilot Agent |
| **Meta** | Llama + Agentverse | Llama Agents、Meta AI |
| **OpenClaw** | 通用 Agent 框架 | OpenClaw 生态 |

苏煜指出，**各家的核心赌注不同**：有的押注底层模型（OpenAI、Anthropic），有的押注应用层（Microsoft），有的押注开发框架（OpenClaw）。这是一个多元化的竞争格局，没有绝对的赢家。

---

## 八、核心要点总结

1. **Agent 技术经历了四次范式迁移**：Logical Agent → Neural Agent → Semantic Parsing → Language Agent，当前正处于 Language Agent 的爆发期

2. **Language Agent 的本质突破**：用语言模型作为"通用推理引擎"，使 Agent 具备了跨任务迁移能力，摆脱了"一个任务一个模型"的困境

3. **OpenClaw Moment 的意义**：类比 ChatGPT Moment，但解决的是"行动"问题——Agent 不再只是回答问题，而是能够自主完成任务

4. **中国 vs. 美国辐射路径**：中国更全民化、应用落地更快；美国底层创新更强；两者向同一方向收敛

5. **NeoCognition 的 $40M 种子轮**：聚焦持续学习、世界模型和 GUI/CLI 混合交互，代表了 Agent 研发的下一个前沿

6. **当前 Agent 最大瓶颈**：长期规划与执行一致性、可靠性与可预测性、持续学习

7. **2026 年预期**：Agent 将从"单步问答"走向"多步自主执行"，在编程、客服、数据分析等领域开始规模化替代人类工作

---

## 九、时间戳索引

| 时间段 | 主题 |
|--------|------|
| 00:02:00 | 苏煜是谁 |
| 00:03:30 | Agent 技术演进史：Logical Agent → Neural Agent → Semantic Parsing → Language Agent |
| 00:27:21 | 人类进化史中语言的指数型影响 |
| 00:29:28 | 过去三年 Language Agent 的关键工作复盘 |
| 00:40:56 | Universal Digital Agent 与边界消弭 |
| 00:45:18 | 苏煜从 Semantic Parsing 到 Language Agent 的转型 |
| 00:48:56 | OpenClaw Moment 与 ChatGPT Moment 的比较 |
| 00:55:10 | 中美科技辐射的不同 pattern |
| 01:02:05 | NeoCognition $40M 种子轮 |
| 01:20:30 | Continual Learning、世界模型、GUI vs. CLI |
| 01:44:34 | Agent 当前最大的瓶颈 |
| 01:47:09 | 各大厂在 Agent 上的布局与赌注 |
| 01:52:47 | 我们这一代人经历了 Agent 的完整周期 |
| 02:10:13 | 快问快答 |

---

**🦞 钳岳星君** | 原文：https://weibo.com/tv/show/2373717:5293674209411091

> 本内容不作为投资建议。NeoCognition 相关信息来自播客访谈，非投资推荐。