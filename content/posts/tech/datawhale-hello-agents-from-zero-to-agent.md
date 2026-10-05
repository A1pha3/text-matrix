---
title: "Datawhale hello-agents 解读：16 章从零构建智能体的开源教程"
date: "2026-05-09T03:20:00+08:00"
lastmod: "2026-10-03T10:30:00+08:00"
slug: "datawhale-hello-agents-from-zero-to-agent"
github_repo: "datawhalechina/hello-agents"
source_key: "gh:datawhalechina/hello-agents"
description: "hello-agents（《从零开始构建智能体》）是 Datawhale 出品的开源智能体教程，16 章主线从 ReAct、Reflection 等经典范式讲到 MCP/A2A 协议、GRPO 训练与多智能体实战，另附 13 篇 Extra-Chapter。本文梳理其结构、关键知识点与学习路径。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Datawhale", "ReAct", "MCP", "多智能体"]
---

## 学习目标

读完本文后，你应该能够：

- 说清 hello-agents 与 Dify、Coze 这类低代码平台的分界，判断它教的是哪一派智能体
- 描述 ReAct 的「思考—行动—观察」循环与 Reflection 的「执行—反思—优化」循环如何运作
- 区分 MCP、A2A、ANP 三种通信协议各自解决的问题
- 解释 GRPO 用组内相对奖励替代价值模型的思路，以及它与 PPO 的差别
- 按教程的真实架构描述智能旅行助手的分层设计
- 判断这套教程是否匹配自己的背景，并规划出合适的学习顺序

## 目录

- [项目概览](#项目概览)
- [教程结构：五部分学习路径](#教程结构五部分学习路径)
- [范式详解：ReAct 与 Reflection](#范式详解react-与-reflection)
- [通信协议：MCP、A2A 与 ANP](#通信协议mcpa2a-与-anp)
- [Agentic RL：从 SFT 到 GRPO](#agentic-rl从-sft-到-grpo)
- [综合案例：智能旅行助手](#综合案例智能旅行助手)
- [学习建议](#学习建议)
- [自测问题](#自测问题)
- [练习](#练习)
- [常见问题 (FAQ)](#常见问题-faq)
- [进阶路径](#进阶路径)
- [总结](#总结)

## 项目概览

hello-agents（[GitHub 仓库](https://github.com/datawhalechina/hello-agents)）是 Datawhale 社区出品的系统性智能体学习教程，正式名称是《从零开始构建智能体》，由陈思州牵头写作，多位 Datawhale 成员与外部工程师参与章节贡献，浙江师范大学杭州人工智能研究院教授朱信忠担任指导专家。教程以中文编写，完全免费。截至 2026 年 10 月，仓库有约 8.2 万 Star、1 万 Fork——README 的致谢里还保留着「助力 7W Star」的里程碑记录。

教程开篇对行业做了一个分野：2024 年是「百模大战」元年，2025 年则开启了「Agent 元年」，技术焦点从训练更大的基础模型转向构建更聪明的智能体应用。在这个判断之下，教程明确站队「AI 原生 Agent」——真正以 AI 驱动的智能体；而 Dify、Coze、n8n 这类平台做的是流程驱动的软件开发，LLM 只是数据处理的后端，不在教程的核心范围内。这个立场贯穿全书：先讲原理和范式，再动手写代码，最后自己搭框架。

**项目数据**（2026-10-03 经 GitHub API 核实）：

- Stars：81,545；Forks：10,136
- 主语言：Python
- 许可证：CC BY-NC-SA 4.0（署名—非商业性使用—相同方式共享）。注意「非商业性使用」限制：教程内容不能拿去做商业培训或付费课程
- 章节规模：16 章主线 + 13 篇 Extra-Chapter（社区加餐）
- 在线阅读：[国际版](https://datawhalechina.github.io/hello-agents/) / [国内加速版](https://hello-agents.datawhale.cc)
- PDF 下载：[GitHub Releases](https://github.com/datawhalechina/hello-agents/releases/latest/) / [国内地址](https://www.datawhale.cn/learn/summary/239)。为防盗版贩卖，官方 PDF 内置了不影响阅读的 Datawhale 水印
- 配套自研框架：[HelloAgents](https://github.com/jjyaoao/helloagents)，已发布 V1.0.0，基于 OpenAI 原生 API

---

## 教程结构：五部分学习路径

### 第一部分：智能体与语言模型基础（第一章至第三章）

**第一章：初识智能体** 给出智能体的定义、类型、范式与应用场景，并以一个最小的智能旅行助手演示 `Thought-Action-Observation` 循环的基本原理——这个例子会在第十三章长成一个完整项目。

**第二章：智能体发展史** 从符号主义讲到 LLM 驱动的智能体，梳理各阶段的突破与局限。了解这段历史的价值在于分清哪些问题是新问题、哪些是老问题换了外壳。

**第三章：大语言模型基础** 覆盖 Transformer 架构、提示工程、主流 LLM 及其局限。LLM 是智能体的「大脑」，但大脑本身不会行动——调用工具、维护状态、根据反馈调整，这些是智能体框架要补的部分。

### 第二部分：构建你的大语言模型智能体（第四章至第七章）

**第四章：智能体经典范式构建** 是全书分量最重的一章，不依赖任何框架，从零实现三种经典范式：ReAct、Plan-and-Solve、Reflection。后文的框架应用、协议集成、训练实战都建立在这章的代码之上。

**第五章：基于低代码平台的智能体搭建** 介绍 Coze、Dify、n8n 等平台的使用。教程对这类平台的定性很明确：快速原型验证的工具，本质是流程驱动的软件开发。

**第六章：框架开发实践** 覆盖 AutoGen、AgentScope、LangGraph 等主流框架。这些框架把第四章的经典范式封装成高级抽象——先理解范式，再用框架，才知道每个参数在做什么。

**第七章：构建你的 Agent 框架** 基于 OpenAI 原生 API 从零构建自己的智能体框架。这门课的产出就是 HelloAgents 框架的学习版，后续章节的协议、训练、评估都往这个框架里加功能。

### 第三部分：高级知识扩展（第八章至第十二章）

**第八章：记忆与检索** 讲记忆系统设计：短期的上下文窗口、长期的知识存储，以及 RAG（检索增强生成）在其中的角色。

**第九章：上下文工程** 探讨持续交互中如何维持情境理解——不只是写好 prompt，还包括组织对话历史、在长程任务中保持焦点。

**第十章：智能体通信协议** 解析三种协议：MCP（Model Context Protocol）管智能体与工具的通信，A2A（Agent-to-Agent Protocol）管智能体之间的点对点协作，ANP（Agent Network Protocol）面向大规模智能体网络的服务发现。实践部分把它们接入了 HelloAgents 框架。

**第十一章：Agentic RL** 从 SFT（监督微调）讲到 GRPO（Group Relative Policy Optimization，群组相对策略优化），配套完整的训练代码。这是让智能体从环境反馈中持续改进的训练侧技术。

**第十二章：智能体性能评估** 介绍评估指标、基准测试与评估框架。评估是迭代的起点——没有度量，改进无从谈起。

### 第四部分：综合案例进阶（第十三章至第十五章）

**第十三章：智能旅行助手** 把第一章的演示扩展为前后端分离的完整 Web 应用，实战 MCP 协议与多智能体协作。这是全书工程量最大的案例。

**第十四章：自动化深度研究智能体** 复现与解析 DeepResearch Agent，让 AI 自动完成信息检索、分析与综合。

**第十五章：构建赛博小镇** 用 Agent 模拟社会动态的虚拟小镇：每个居民是一个 Agent，有自己的目标、记忆和社会关系，用于观察多 Agent 交互的行为。

### 第五部分：毕业设计及未来展望（第十六章）

要求读者构建一个完整的多智能体应用，综合运用全书知识。仓库另有「共创毕业设计」板块，收录社区学员的毕设项目，可以当参考答案看。

### 13 篇 Extra-Chapter：容易错过加餐

主线之外，社区以 Extra-Chapter 的形式贡献了 13 篇加餐，其中几篇的实用价值不亚于正章：

- **面试与求职**：Extra01 汇总 Agent 岗位面试题及参考答案
- **环境配置**：Extra07 给出 Python 3.10+ 环境的完整搭建步骤
- **技术对比**：Extra05 解读 Agent Skills 与 MCP 的差异；Extra02 补充上下文工程
- **场景实战**：Extra06 GUI Agent 科普与实战、Extra11 Web Agent 原理与反爬实战、Extra03 Dify 保姆级教程
- **经验沉淀**：Extra08 如何写出好的 Skill、Extra09 Agent 应用开发踩坑、Extra10 Agent 自进化的四类闭环
- **训练实战**：Extra12 把旅行助手 Demo 后训练成能用的 Planner——想跑通第十一章内容的读者建议搭配这篇

---

## 范式详解：ReAct 与 Reflection

### ReAct 的工作原理

ReAct（Reasoning + Acting）由 Shunyu Yao 等人在 2022 年提出。它出现的背景是两条路都走不通：纯「思考」的方法（如思维链）能做复杂推理但无法与外部世界交互，容易产生事实幻觉；纯「行动」的方法能执行动作，但缺乏规划和纠错能力。ReAct 把两者拧在一起，形成固定的输出轨迹：

```text
Thought（思考）→ Action（行动）→ Observation（观察）→ Thought → ...
```

以航班查询为例：

1. **Thought**：用户要查下周上海到东京的机票，这需要调用外部 API，先确认日期
2. **Action**：向用户追问「哪天出发？」，或直接调用航班查询工具
3. **Observation**：工具返回 3 个候选航班
4. **Thought**：信息已足够，整理关键信息给出最终答案

这个循环的关键在于格式规约：模型被强制按 `Thought`/`Action` 结构化输出，代码才能精确解析每一步的意图，把行动交给工具、把观察写回上下文。智能体不断重复这个循环，直到模型在 `Thought` 中判断任务完成。

### Reflection 的自我改进机制

ReAct 和 Plan-and-Solve 生成初稿后工作就结束了，初稿有错也只能靠外部反馈（工具报错、Observation）来纠。Reflection 给智能体加了一个内部纠错回路，教程把它概括为三步循环：

```text
执行（Execution）→ 反思（Reflection）→ 优化（Refinement）
```

1. **执行**：用 ReAct 等已有方法完成任务，产出「初稿」
2. **反思**：调用一个独立的（或带特殊提示词的）LLM 实例扮演「评审员」，从事实性错误、逻辑漏洞、效率问题、遗漏信息四个维度审视初稿，输出结构化的反馈
3. **优化**：把初稿和反馈一起交给 LLM，生成修订稿

循环重复进行，直到评审员不再发现新问题，或达到预设的迭代上限。这一思路的代表性研究是 Shinn 等人 2023 年的 Reflexion 框架。

教程在实战部分特意强调了实现细节：迭代的前提是记住之前的尝试，所以 Reflection 必须搭配一个「短期记忆」模块，存储每一轮「执行—反思」的完整轨迹。这个设计也预告了第八章的记忆系统。

---

## 通信协议：MCP、A2A 与 ANP

教程第十章用一句分工概括三种协议：MCP 解决「如何访问工具」，A2A 解决「如何与其他智能体对话」，ANP 解决「如何在大规模网络中发现和连接智能体」。

### MCP（Model Context Protocol）

MCP 由 Anthropic 主导，定义智能体与外部工具、数据源之间的标准化接口。教程给了一个具体场景：用户在 Claude Desktop 里问「我桌面上有哪些文档」，Claude Desktop 作为 **Host（宿主层）** 接收提问并管理对话；Host 内置的 **Client（客户端层）** 负责与 MCP Server 建立连接、收发请求；**Server（服务器层）** 执行实际的文件扫描并返回结果。分工之后，应用开发者只需要写 MCP Server，不用关心 Host 和 Client 的实现。

工作流程分四步：Client 连接 Server 后先调用 `list_tools()` 拿到工具清单（名称、功能说明、参数定义），把清单转成 LLM 能理解的格式注入系统提示词；LLM 决定用哪个工具后，Client 通过 MCP Server 执行并取回结果。通信基于 JSON-RPC，一个 Server 可以挂载多个 Tool。

### A2A（Agent to Agent）

A2A 协议由 Google 团队提出，关注智能体之间的点对点协作。它的设计哲学是「对等通信」：每个智能体既是服务提供者也是服务消费者，可以主动发起请求，也可以响应别人的请求。这种对等设计避免了中心化协调器的瓶颈——多个 Agent 协作时，不需要一个常驻的中枢来转发所有消息。

### ANP（Agent Network Protocol）

ANP 目前还是概念性的协议框架，由开源社区维护，生态尚未成熟。它的设计哲学是「去中心化服务发现」：在成百上千个智能体的网络里，通过服务注册、发现和路由机制，让智能体动态找到需要的服务，而不必预先配置所有连接。教程在 HelloAgents 中只做了概念模拟，官方另有 [AgentConnect](https://github.com/agent-network-protocol/AgentConnect) 实现。

选型逻辑也简单：接工具用 MCP，多智能体协作用 A2A，构建大规模智能体生态才考虑 ANP。

---

## Agentic RL：从 SFT 到 GRPO

教程第十一章回答一个训练侧的问题：SFT（监督微调）之后的模型只是学会了「模仿」训练数据里的推理过程，并没有真正学会「思考」。要强化推理策略，需要强化学习让模型通过试错来超越训练数据的质量。

路线是从 PPO 说起的。PPO 是强化学习里最经典的算法之一，但用在 LLM 训练上有三个痛点：需要训练 Value Model（价值模型），增加复杂度和显存占用；要同时维护 Policy、Reference、Value、Reward 四个模型，工程实现复杂；训练不稳定，容易出现奖励崩塌或策略退化。

**GRPO（Group Relative Policy Optimization，群组相对策略优化）** 是专门为 LLM 设计的 PPO 简化变体，核心改动是去掉 Value Model，用组内相对奖励代替绝对奖励：对每个提示采样一组响应，拿组内平均奖励作基线，用「单条奖励减去组内平均」代替优势函数，再叠加 KL 散度惩罚防止策略偏离参考模型太远。这样训练流程只需要 Policy Model 和 Reference Model，更简单、更稳定、显存占用更低。

教程的实战部分给出了完整 pipeline：先在 GSM8K 数学题数据集上做 SFT 让模型学会推理格式，再用 GRPO 优化策略提升准确率。奖励函数的设计也展开讲了——准确率奖励、长度惩罚、步骤奖励各有分工。有一个诚实的提醒：教程演示只用了 0.7% 的训练样本跑一轮，准确率低是正常现象，想复现效果要给足数据和轮次。

---

## 综合案例：智能旅行助手

智能旅行助手是教程中最完整的实战案例，也是第一章那个最小演示的工程化版本。它包含五个功能：智能行程规划、地图可视化、预算计算、行程编辑（增删景点后实时更新地图和预算）、导出 PDF 或图片。

系统采用前后端分离架构，分四层：

```text
用户（浏览器）
    ↓
前端层：Vue3 + TypeScript（表单输入、地图可视化、结果展示）
    ↓
后端层：FastAPI（API 路由、数据验证、业务逻辑）
    ↓
智能体层：HelloAgents（4 个专职 Agent）
    ↓
外部服务：高德地图 API（经 MCP 协议接入）
```

4 个 Agent 分别负责景点搜索、天气查询、酒店推荐、行程规划。数据流转是串行的：用户在前端填写表单，后端验证后调用智能体系统，系统依次调用四个 Agent，每个 Agent 通过 MCP 协议调用高德地图 API，结果整合后返回前端渲染。

案例里的工程细节值得细读。数据模型用 Pydantic 定义，从位置坐标、景点、酒店到单日行程逐层组合；天气字段做了特殊处理——高德地图返回的温度格式不规范，需要自定义验证器兜底。这些正是「把演示变成能用的应用」要付的成本，也是教程想传达的：多智能体系统的难点不在范式本身，而在数据建模、异常处理和系统集成。

---

## 学习建议

### 适合人群与前置条件

README 对读者的定义很清楚：有一定编程基础的 AI 开发者、软件工程师、在校学生和自学者。前置条件两条——基本的 Python 编程能力，对大语言模型有概念性了解（知道怎么通过 API 调用一个 LLM）。教程的重点是应用与构建，不需要深厚的算法或模型训练背景。环境方面按 Extra07 的指引准备 Python 3.10+ 即可。

### 学习路径建议

1. 第一至三章快速过一遍，重点放在第一章的循环演示——它是全书案例的种子
2. 第四章放慢，亲手实现 ReAct、Plan-and-Solve、Reflection 三种范式。这章的代码是后续所有章节的地基
3. 第八至十二章按需取用：做应用优先第十章（协议），做训练优先第十一章
4. 从三个综合案例中选一个完整做一遍，旅行助手工程量最大、收获也最完整
5. 最后用第十六章毕业设计收尾，检验学习成果

教程在 `code` 文件夹提供了全部配套代码。作者的建议同样适用于这篇导读的读者：务必亲手运行、调试甚至修改每一份代码，只读不跑等于没学。

---

## 自测问题

完成阅读后，尝试回答以下问题以检验理解：

1. **ReAct 范式中「思考」与「行动」是如何交替的？用一个具体例子说明完整循环。**

   <details>
   <summary>参考答案</summary>
   模型按 Thought → Action → Observation 的固定轨迹输出：思考分析当前状态并决定下一步，行动调用工具或与用户交互，观察把执行结果写回上下文，如此循环直到模型在 Thought 中判断任务完成。以航班查询为例：Thought 判断需要调用 API → Action 调用航班查询工具 → Observation 返回 3 个航班 → Thought 判断信息已足够 → 输出最终答案。
   </details>

2. **Reflection 范式的三步循环是什么？「评审员」从哪些维度评估初稿？为什么实现时必须搭配记忆模块？**

   <details>
   <summary>参考答案</summary>
   三步循环是执行 → 反思 → 优化。评审员从事实性错误、逻辑漏洞、效率问题、遗漏信息四个维度评估初稿，输出结构化反馈。迭代的前提是记住之前的尝试和反馈，所以需要短期记忆模块存储每轮「执行—反思」的完整轨迹，否则优化无从下手。
   </details>

3. **MCP、A2A、ANP 分别解决什么问题？为什么需要三种协议而不是一种？**

   <details>
   <summary>参考答案</summary>
   MCP 定义智能体与工具、数据源的接口，解决「如何访问工具」；A2A 定义智能体之间的点对点通信，解决「如何与其他智能体对话」；ANP 面向大规模网络的服务注册、发现与路由，解决「如何在大规模网络中发现和连接智能体」。三者作用在通信的不同环节——工具接入、水平协作、网络发现，场景不同，所以是互补而非替代关系。
   </details>

4. **GRPO 相比 PPO 做了什么简化？「组内相对奖励」体现在哪里？**

   <details>
   <summary>参考答案</summary>
   GRPO 去掉了 Value Model：对每个提示采样一组响应，以组内平均奖励为基线，用「单条奖励减去组内平均」代替需要价值网络估计的优势函数，并叠加 KL 散度惩罚约束策略偏离。模型从四个减到两个（Policy + Reference），训练更稳定、显存占用更低。「组内相对」指的是奖励不与绝对标准比较，而是与同组响应的平均水平比较。
   </details>

5. **智能旅行助手案例中，四个 Agent 是如何组织的？为什么说这个案例的难点不在范式本身？**

   <details>
   <summary>参考答案</summary>
   景点搜索、天气查询、酒店推荐、行程规划四个 Agent 挂在 HelloAgents 智能体层，由系统依次调用，各自通过 MCP 协议调用高德地图 API。难点在于工程集成：前后端分离架构、Pydantic 数据模型逐层组合、高德返回的非规范温度字段需要自定义验证器兜底——把范式演示变成可用应用，成本都花在这些地方。
   </details>

---

## 练习

### 练习 1：实现一个最小化的 ReAct Agent

**任务**：从零开始实现一个最简单的 ReAct Agent，不依赖任何框架（LangChain、AutoGen 等）——这正是教程第四章的起手式。

**要求**：
1. 使用 OpenAI API（或兼容的 LLM API）
2. 实现 ReAct 循环：Thought → Action → Observation → ...
3. 定义至少 2 个工具（如：计算器、天气查询）
4. 用明确的格式标记推理和行动的边界（如：`Thought:`、`Action:`、`Observation:`）
5. 处理至少 3 轮交替

**参考伪代码**：

```text
while not finished:
    prompt = system_prompt + history + current_observation
    response = llm.generate(prompt)

    if "Action:" in response:
        action = parse_action(response)
        observation = execute_tool(action)
        history.append(observation)
    elif "Final Answer:" in response:
        break
```

**检验标准**：
- Agent 能正确交替进行推理和行动
- 工具调用结果能被正确解析和利用
- Agent 能在获得足够信息后终止循环并给出最终答案

**扩展思考**：如何防止 Agent 陷入无限循环？如何限制最大推理步数？

### 练习 2：设计一个多 Agent 协作系统

**场景**：你要设计一个「智能会议助手」，帮助用户提高会议效率。

**功能需求**：
- 会前：自动生成议程、提醒参会者、准备背景资料
- 会中：实时记录要点、自动生成行动项
- 会后：生成会议纪要、跟踪行动项执行进度

**任务**：设计一个多 Agent 协作系统来实现上述功能。

**要求**：
1. 绘制系统架构图（参考本文智能旅行助手的分层画法）
2. 定义每个 Agent 的职责
3. 定义 Agent 之间的协作流程（消息传递、任务分配）
4. 定义需要哪些 MCP Server（如：日历 API、邮件 API、文档 API）
5. 考虑异常情况（如：参会者迟到、议程临时变更）

**输出**：一份系统设计方案（Markdown 格式），包含架构图（用 Mermaid 或 ASCII art）、Agent 职责表、协作流程图、MCP Server 列表。

**深入问题**：
- 协调者 Agent 应该如何设计？它需要维护什么状态？
- 如果某个子 Agent 失败（如：邮件 API 调用失败），系统应该如何处理？
- 如何让 Agent 之间的协作可追溯、可调试？

### 练习 3：分析一个真实 Agent 系统的失败案例

**任务**：在 GitHub、Reddit 或技术博客中找到一个真实 Agent 系统失败的案例（如：Agent 陷入循环、产生幻觉、调用错误工具等），进行深度分析。Extra09 收录的踩坑经验是现成的素材库。

**分析框架**：
1. **失败现象描述**
   - 这个 Agent 系统应该做什么？
   - 实际发生了什么？
   - 失败的具体表现是什么？（无限循环、错误输出、崩溃？）

2. **根因分析**
   - 是 Prompt 设计问题、工具定义问题、还是框架实现问题？
   - 如果用 ReAct/Reflection 范式分析，问题出在哪个环节？
   - 是否有上下文长度限制、工具返回格式变化等隐蔽因素？

3. **改进方案设计**
   - 如何修复这个问题？
   - 需要修改 Prompt、工具定义、还是增加 Reflection 机制？
   - 如何防止类似问题再次发生？（增加单元测试、加入监控报警？）

4. **经验教训总结**
   - 从这个失败案例中学到了什么？
   - 这些经验如何应用到你自己的 Agent 系统设计中？

**输出**：一份 1000-1500 字的案例分析报告，包含以上四个部分的详细内容，并附上原始案例的链接。

---

## 常见问题 (FAQ)

### Q1: hello-agents 适合完全没有 AI 基础的初学者吗？

不太适合。教程假设读者有基本的 Python 编程能力，知道如何通过 API 调用一个 LLM。零基础读者可以先看 Datawhale 的另一门课 [easy-vibe](https://github.com/datawhalechina/easy-vibe)（vibe coding 入门，约 2 万 Star），再回来学 hello-agents。

### Q2: 需要读完全部 16 章才能开始构建自己的 Agent 吗？

不需要。读完第一部分和第四章（三种经典范式）就可以动手，然后直接跳到综合案例（第十三至十五章）实践，遇到不懂的概念再回头查对应章节。第十章（协议）和第十一章（训练）可以按需插入。

### Q3: 教程中的代码可以直接运行吗？需要什么环境？

可以。`code` 文件夹提供了全部配套代码。环境要求：Python 3.10+（Extra07 有完整的环境配置指引）、一个 OpenAI API Key 或兼容的 LLM API、部分章节的额外依赖（如 LangChain、AutoGen）。建议在虚拟环境中安装依赖，避免版本冲突。

### Q4: Dify/Coze 等低代码平台已经能搭建 Agent 了，为什么还要学框架开发？

教程对这个问题的回答很直接：低代码平台做的是流程驱动的软件开发，LLM 充当数据处理后端，你通过拖拽组件定义流程——这是第五章的范围。而理解范式、手写框架之后，你才能构建真正自主决策的 AI 原生 Agent，才能看懂 LangGraph 这类框架的每个抽象在做什么。「用轮子」和「造轮子」的能力，教程希望读者兼得。

### Q5: 学完 hello-agents 后，下一步应该学什么？

三个方向：深入某个主流框架（LangGraph、AutoGen）的源码，理解工程实现细节；走训练路线，Extra12 的旅行助手后训练实战是现成的进阶案例，作者团队也在筹备续作《从零开始训练智能体》；或者结合业务场景，把自己的多 Agent 应用做到生产环境。2026 年 5 月 Datawhale 还发布了配套的 [Agent-Learning-Hub](https://github.com/datawhalechina/Agent-Learning-Hub)，汇总了最新的学习路线。

---

## 进阶路径

**方向一：框架源码深入**
- HelloAgents 已发布 V1.0.0，从自己亲手写过学习版的人去读它，每一步都不陌生
- 再选 LangGraph 或 AutoGen 之一对照阅读，看工业级框架如何实现相同的范式
- 尝试为框架贡献代码（修复 bug、添加新功能）

**方向二：Agentic RL 实战**
- 沿第十一章的 GSM8K pipeline 换一个任务域（如代码生成），重新设计奖励函数
- 用 Extra12 的旅行助手后训练实战，把 Demo 打磨成能用的 Planner
- 理解 GRPO 之外的其他路线（如 DPO），对比适用场景

**方向三：生产级 Agent 系统**
- 学习部署：并发、容错、监控、日志
- 理解安全性：prompt injection 防御、数据泄露防范
- 建立评估体系：延迟、成本、准确率的量化与回归

**方向四：更多 Agent 形态**
- 教程主线聚焦文本 Agent，Extra06（GUI Agent）和 Extra11（Web Agent）是现成的多模态延伸
- 动手做一个能操作浏览器或桌面应用的 Agent，体会感知与行动的对接

---

## 总结

hello-agents 值得推荐的几个理由：

1. 知识成体系：从原理、范式、框架到协议、训练、评估，一条线走完单 Agent 到多 Agent 的完整路径，不是零散的工具介绍
2. 每章配套可运行代码，理论之后立即动手验证；自研框架 HelloAgents 贯穿全书，学完即拥有一个可控的智能体运行时
3. 13 篇 Extra-Chapter 补齐了面试、环境配置、踩坑经验这些主线放不下的实用内容
4. 中文编写，Datawhale 社区维护，CC BY-NC-SA 4.0 许可，遇到问题可以在 GitHub 提 Issue

如果你要从理论到实践系统地学 AI Agent 开发，hello-agents 是目前中文社区覆盖面最广的教程之一——从手写 ReAct 到 GRPO 训练，再到 Vue3 + FastAPI 的完整应用，这个跨度在同类教程里并不多见。它对「AI 原生 Agent」与「流程驱动开发」的区分，尤其适合正从 Dify/Coze 这类平台转向框架开发的读者。

**延伸阅读**：

- GitHub 仓库：https://github.com/datawhalechina/hello-agents
- 在线阅读（国际版）：https://datawhalechina.github.io/hello-agents/
- 在线阅读（国内加速）：https://hello-agents.datawhale.cc
- PDF 下载：https://github.com/datawhalechina/hello-agents/releases/latest/ （国内：https://www.datawhale.cn/learn/summary/239）
- 自研框架 HelloAgents：https://github.com/jjyaoao/helloagents
- 智能体学习路线：https://github.com/datawhalechina/Agent-Learning-Hub
- Datawhale 官网：https://datawhale.cn/
