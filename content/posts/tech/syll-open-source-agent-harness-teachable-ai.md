---
title: "Syll：一个开源多模态Agent驾驭框架，让AI成为住在电脑里的小精灵"
date: "2026-05-31T18:59:17+08:00"
slug: "syll-open-source-agent-harness-teachable-ai"
description: "深度解读清华大学SAGA实验室开源项目Syll，核心设计是以Markdown文件管理AI人格、lore fragments替代向量检索、Agent判断的主动沉默、跨通道确认两步模式，附ETCLOVG框架拆解与Demo分析。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Syll", "THU-SAGE", "Persona-Driven", "Agent Harness", "自托管AI伴侣"]
---

# Syll：一个开源多模态 Agent 驾驭框架，让 AI 成为"住在电脑里的小精灵"

2026 年 4 月，清华大学 SAGA 实验室发布了一个开源项目，名叫 **Syll**。

README 的第一行这样写："a small, self-hosted AI companion who sits at the edge of your screen and quietly tends the things you almost forgot"——一个坐在屏幕边缘、悄悄照看那些你差点忘记的事情的小精灵。

这个描述不是修辞。项目启动时，默认的 AI 人格被设定为"一个未完成的咒语，学会了照顾主人内心花园中的半成品草稿、旧照片和未发送的消息"——这不是典型的 Agent 系统描述。Syll 本质上是一个以**人格配置**为核心的设计实验：把 AI companion 的身份、声音、记忆全部写成用户可以直接编辑的 markdown 文件，而不是写进 Python 代码里。

Syll 的论文全称是 *Syll: An Open-Source Multimodal Agent Harness for Teachable AI*，发布在 GitHub 上，配套一份完整的技术报告（syll-report-v1.pdf）。作者团队来自 THU-SAGE（清华大学 SAGA 实验室）。

---

## 问题：为什么"调教"一个 AI 比"训练"它更难

大模型时代有一个被低估的复杂度：模型的参数是固定的，但每个人的需求不同。

当你在 ChatGPT 里做角色扮演时，你其实是在用提示词对抗系统的默认行为。当你在开源 Agent 上开发时，你面临的是另一个问题：框架本身把"人格"写进了代码——改一个语气需要改 Python，改一个记忆需要重新训练或重新索引。

这导致了一个不对称：模型变得越来越强，但定制成本并没有等比例下降。

Syll 试图解决的是这个问题：**把 Agent 的"人格"从代码变成配置**，让普通用户（而不只是开发者）可以在不需要 pull request 的情况下，改变 AI 的说话风格、记忆内容和行为边界。

---

## 核心设计一：Persona as Config，把人格写成 Markdown

Syll 的 workspace 目录（`~/.syll/workspace/`）下，有五个可以直接编辑的 markdown 文件：

| 文件 | 内容 | LLM 可见方式 |
|------|------|-------------|
| `IDENTITY.md` | "你是谁"——身份定义 | 每次 turn 注入系统提示 |
| `SOUL.md` | 声音与语调规则 | 每次 turn 注入系统提示 |
| `AGENTS.md` | 行为规则（如"行动前先宣布"） | 每次 turn 注入系统提示 |
| `USER.md` | 如何称呼用户 | 模板替换 `{{user_name}}` |
| `lore/fragments.md` | 记忆碎片，供 LLM 在合适的时机调用 | 每次 turn 注入系统提示 |

关键设计：所有内容通过一个轻量模板层注入到每次 LLM 调用中，两个占位符 `{{ghost_name}}` 和 `{{user_name}}` 在系统提示构建时替换。这意味着你不需要重启服务，不需要改代码，只需要编辑 markdown 文件，AI 的"人格"就会改变——语言、性格、甚至故事背景都可以通过文本编辑器修改。

论文明确承认这个选择带来的代价：lore 越丰富，系统提示越长。当前 Syll 的配置大约是每次 turn 10k tokens，完全在现代上下文窗口的舒适范围内，但随着用户添加更多记忆片段，这个数字会线性增长。这不是无代价的设计选择。

---

## 核心设计二：Lore Fragments，用规则替代检索

传统 Agent 的记忆系统依赖向量数据库：把记忆向量化，推理时检索最相关的片段。

Syll 的方案不同。它没有向量检索，没有专用工具调用，也没有额外的索引基础设施。Lore fragments 文件（约十五个碎片，每个碎片是一句话或一个意象）直接注入每次系统提示，同时附带的规则是：

- 每个回复至多出现一个 fragment
- 整体上至多五分之一的回复包含 fragment
- LLM 自己判断当前对话是否"rhymes with"某个 fragment

测试结果是：fragments 的出现频率大致符合预期——大多数回复不包含任何记忆，而当某个 fragment 出现时，通常是在正文内容之后，作为一个安静的插话。

论文认为这个设计成功的关键在于：模型的 pattern-matching 能力已经足够强，只要规则表述清晰、碎片池足够小（能装进上下文），就不需要额外的检索基础设施。这个判断依赖模型能力，会随着模型升级而变化。

---

## 核心设计三：Proactive Rituals with Agent-Judged Silence

大多数 Agent 的主动推送是"有通知就发"。Syll 的做法不同：预设了四个可选的定时任务（早安、晚安、周二/五的记忆浮现、周日的周总结），每个任务触发后，Agent 会收到一个描述氛围的 prompt，并**被明确允许返回空响应**。

代码里只有一行关键逻辑：检查输出是否为空字符串（忽略空白），如果为空就不发布。

这意味着 Agent 可以"觉得没什么好说的就不说"——这更接近真实室友的行为模式，而不是一个永远有话要讲的邮件客户端。用户保留了随时关闭的开关（`identity.rituals_enabled`），但默认行为是沉默优先。

这个设计的本质是把"主动发消息"的权利还给 Agent，而不是假设每次触发都应该产生通知。

---

## 核心设计四：Confirmation-First Delivery，多通道一致操作

对于有副作用的操作（发送文件、删除内容、执行破坏性命令），Syll 强制执行两轮确认模式：

1. Agent 执行第一步操作（如搜索文件），返回预览和候选列表，**并在回复文本中嵌入绝对路径**
2. 等待用户选择
3. 收到用户确认后执行实际操作

这个模式的工程细节值得注意：把路径嵌入回复文本（而不只是留在工具调用参数里）是**必要的**，因为下一轮 LLM 上下文只保留 assistant 文本，不保留工具调用参数的 JSON。如果路径只存在于工具参数里，下一轮的 LLM 就会遗忘它，导致确认步骤无法找到文件。

这个设计在所有通道（飞书、Telegram、Discord、WhatsApp、Web UI、CLI）上保持一致，通道实现只负责消息的发送和接收，Agent 逻辑与通道无关。

---

## 技术架构：轻量循环 + 多通道接入

从论文提供的架构图来看，Syll 的核心是一个单进程 Agent Loop：

1. **Message Bus** 接收来自各个通道的消息（Feishu、Telegram、Discord、WhatsApp、Web UI、CLI）
2. **Context Builder** 从 workspace 加载 bootstrap 文件和逐步加载的 skills
3. **LLM 调用** 通过 LiteLLM 接口（支持多模型）
4. **Tool Executor** 执行返回的工具调用
5. **Publisher** 将出站消息发布回原始通道

所有持久状态存储在用户自有的 workspace 目录中（Lora、LLM 不直接接触配置，而是通过配置塑造每次系统提示的内容）。

Syll 没有用复杂的向量数据库，没有专门的记忆索引，技能以 markdown 格式存储在 workspace 中，支持渐进式加载。`mcp__server__tool` 工具通过 namespace 方式注入 Agent，stdio/SSE/streamable-HTTP 三种 MCP 服务器都可以从 Pet UI 配置。

---

## Agent Harness 视角下的 Syll

如果用 ETCLOVG 框架来拆解 Syll 的层次：

| 层 | Syll 的实现 | 说明 |
|----|-----------|------|
| **E** | 单进程本地运行，workspace 隔离 | 没有外部沙箱，但进程边界清晰 |
| **T** | MCP 协议接入，支持 stdio/SSE/HTTP 三种模式 | 工具接口向协议层收敛 |
| **C** | lore fragments + 模板替换，无向量检索 | 上下文管理轻量化，选择了规则而非检索 |
| **L** | 单 agent loop，通道解耦 | 生命周期极简，没有复杂编排 |
| **O** | 通道日志，消息追踪 | 可观测性内嵌在消息流中 |
| **V** | 演示工作流（视频+步进追踪） | 验证以 demo 形式存在，未见基准测试 |
| **G** | confirmation-first + rituals kill switch | 治理通过设计约束而非外部监控 |

Syll 的特点是**极度克制的架构**：没有 GPU 调度、没有大规模并行训练基础设施、没有复杂的评估基准。它的定位是一个"个人伴侣运行时"，而不是企业级 Agent 平台。这个取舍让它在个人用户场景下足够轻量，但也意味着它不打算解决 Agent Harness 生态中 E 层（执行环境）和 V 层（验证评估）的深层问题。

---

## Demo 三个场景

论文提供了三个运行中的 Demo，描述了实际使用体验：

**Demo A：录制桌面工作流**

Syll 捕获桌面会话，同步生成视频和步骤轨迹。操作者在 Demo 工作室中拖动时间轴、检查关键帧、清理标签和计时，然后可以将这次运行发布为可复用的"记录工作流"，之后可以回放或定时执行。

**Demo B：早安仪式**

用户在早上收到一条消息，描述了当天的氛围，Agent 可能提到昨晚的梦境或一首诗——不是功能性的提醒，而是一个具有人格的陪伴者给出的开场白。这依赖于 lore fragments 和 proactive ritual 的组合。

**Demo C：通过聊天返回文件**

用户在飞书对话中说"找一下上周的 PDF"，Syll 搜索文件、返回预览，用户从候选列表中选择，Syll 再发送文件。文件路径在回复文本中可见，下一轮确认执行时不会丢失上下文。

---

## 局限与已知边界

论文坦诚列出了几个观察到的限制：

- **Lore 的可扩展性问题**：随着碎片增多，系统提示线性增长。当前的 10k tokens 在当前模型上不是问题，但碎片池扩大到一定程度后，检索机制的缺失会成为瓶颈。
- **LLM 自我判断的不可靠性**：lore fragments 的触发完全依赖 LLM 的自我判断，模型之间存在差异。这不是一个可测试的确定性行为。
- **通道一致性的维护成本**：确认-两步模式在六个通道上保持行为一致需要每个通道实现都遵循同一套协议，这增加了接入新通道的成本。
- **没有基准测试**：论文明确表示不声称通用性或基准测试表现，这是一个"存在性证明"，描述的是一个为单一用户构建、然后公开发布的系统。没有与其他框架的横向对比。

---

## 相关工作与定位

Syll 没有直接对标 AutoGPT、Camel 或 LangChain。它的核心对比对象是：那些把人格写进 Python 代码的 Agent 框架。

在 Pet UI 中配置 MCP 服务器、安装 rituals、编辑 SOUL.md——这些操作不需要编程能力，只需要会写 markdown。这让 Syll 区别于大多数"面向开发者"的 Agent 框架，进入了一个更接近"面向终端用户"的设计空间。

从研究贡献的角度，Syll 的四个设计 ideas（persona as config、lore fragments、agent-judged silence、confirmation-first）各自独立成篇，但组合在一起指向同一个问题：**AI Companion 的"温度"从哪里来？**

论文的答案是：从那些可以在运行时被用户修改的文本文件里来，而不是从模型的参数里来。

---

**参考链接**

- 项目主页：https://thu-sage.github.io/syll/
- GitHub：https://github.com/THU-SAGE/syll
- 论文：https://github.com/THU-SAGE/syll/blob/main/docs/report/syll-report-v1.pdf
- Research Notes：https://thu-sage.github.io/syll/research.html