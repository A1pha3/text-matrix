---
title: "Datawhale Agent Skills完全指南：吴恩达课程深度解读"
slug: "datawhale-agent-skills-with-anthropic-guide"
description: "深入解读Datawhale基于吴恩达DeepLearning.AI课程打造的中文Agent Skills学习资料，掌握Skills的核心概念、架构对比和实战技能。"
date: "2026-04-10T21:15:00+08:00"
categories: ["技术笔记"]
tags: ["AI", "Agent", "Skills", "Claude", "MCP", "吴恩达", "Datawhale", "Agentic AI"]
---

# Datawhale Agent Skills完全指南：吴恩达课程深度解读

## §1 学习目标

通过本文，您将掌握：

1. **理解Skills的本质**：什么是Agent Skills，为什么需要Skills，Skills的核心特点
2. **掌握Skills的架构**：YAML前置元数据、Markdown正文、渐进式披露机制
3. **理解Skills vs 其他组件**：Skills vs Tools、Skills vs MCP、Skills vs Subagents的对比和协作
4. **学会创建自定义Skills**：以Excel Skill为案例，掌握创建完整Skill的流程
5. **理解Agent生态系统**：Prompts、Skills、Subagents、MCP如何协同工作

---

## §2 项目概述

### 2.1 什么是Agent Skills？

**Agent Skills** 是一种轻量、开放的格式，用于扩展AI Agent的能力。它是一个组织良好的文件夹，包含：

- **指令（Instructions）**：定义Skill的行为和用途
- **脚本（Scripts）**：可执行的代码文件
- **资产与资源（Assets and Resources）**：参考文档、模板等

### 2.2 吴恩达 × Anthropic 合作课程

本项目是Datawhale对吴恩达老师在DeepLearning.AI平台推出的 **agent-skills-with-anthropic** 系列课程的完整中文学习资料。

| 项目 | 信息 |
|------|------|
| **课程来源** | DeepLearning.AI × Anthropic |
| **主讲讲师** | Elie Schoppik |
| **官方仓库** | [sc-agent-skills-files](https://github.com/https-deeplearning-ai/sc-agent-skills-files) |
| **视频课程** | [DeepLearning.AI Short Courses](https://www.deeplearning.ai/short-courses/agent-skills-with-anthropic/) |
| **中文整理** | Datawhale |
| **Stars** | 494 |
| **Forks** | 64 |

### 2.3 项目特点

- **完整中文翻译**：降低学习门槛，让中文用户无障碍学习
- **系统知识点梳理**：帮助理解核心概念，而非碎片化信息
- **详细代码示例**：提供可运行的实践代码
- **开源协作模式**：社区共同完善中文学习生态

---

## §3 Skills的核心特点

### 3.1 三大核心特点

**1. 开放标准（Open Standard）**
> Skills现在是一个开放标准，采用标准化格式，可与任何兼容的智能体产品配合使用。

**2. 一次构建，多处部署（Build Once, Deploy Everywhere）**
> 你可以构建一次技能，然后在多个智能体产品中部署使用。

**3. 渐进式披露（Progressive Disclosure）**
> 技能的名称和描述始终存在于智能体的上下文窗口中，但只有当用户请求与技能描述匹配时，才会加载其余指令。

### 3.2 Skills的三大用武之地

| 领域 | 示例 |
|------|------|
| **领域专业知识** | 品牌规范与模板、法务审核流程、数据分析方法论 |
| **可重复的工作流程** | 每周营销活动复盘、客户电话准备流程、季度业务复盘 |
| **新能力** | 制作演示文稿、生成Excel/PDF报告、搭建MCP服务器 |

### 3.3 没有Skills会怎样？

如果每次都要重新描述指令和需求，而不是使用Skills：

- 每次都要重新描述指令与需求
- 每次都要重新打包参考资料与支持文件
- 难以保证流程或产出始终一致

---

## §4 Skills的架构深度解析

### 4.1 渐进式披露机制

Skills采用 **YAML + Markdown + 元数据** 的三层架构：

```
┌─────────────────────────────────────┐
│  YAML Frontmatter（元数据）            │  ← 始终加载
│  - name: skill-name                 │
│  - description: 技能描述            │
├─────────────────────────────────────┤
│  Markdown正文（指令）                  │  ← 触发时加载
│  - 输入格式                          │
│  - 处理流程                          │
│  - 输出格式                          │
├─────────────────────────────────────┤
│  Resources（资源）                    │  ← 按需加载
│  - scripts/（脚本）                  │
│  - references/（参考资料）            │
└─────────────────────────────────────┘
```

### 4.2 Excel Skill目录结构示例

以"分析营销活动"为例，Skill目录结构如下：

```
analyzing-marketing-campaign/
├── SKILL.md                    # 主说明文档
└── references/
    └── budget_relocation_rules.md  # 参考规则和模板
```

### 4.3 SKILL.md格式详解

SKILL.md通常包含YAML Frontmatter和Markdown正文：

```yaml
---
name: analyzing-marketing-campaign
description: 分析多渠道数字营销数据，计算转化漏斗、效率指标，并给出预算调整建议。
inputs:
  - file: Excel/CSV，包含Date, Campaign_Name, Channel, Impressions, Clicks, Conversions, Spend, Revenue, Orders等字段
outputs:
  - Markdown/Excel表格，含各项指标与建议
---

## 任务流程

1. 读取Excel/CSV数据
2. 计算各渠道CTR（点击率）、CVR（转化率）
3. 计算ROAS（广告回报率）、CPA（获客成本）、净利润等效率指标
4. 输出对比表格，生成分析解读与预算建议

## 公式示例

- CTR% = Clicks / Impressions * 100
- CVR% = Conversions / Clicks * 100
- ROAS = Revenue / Spend
- CPA = Spend / Conversions
- Net Profit = Revenue - (Spend + 其它成本)
```

### 4.4 常见Excel自动化任务

| 任务类型 | 示例 |
|---------|------|
| 数据汇总与统计 | 如销售总额、最大单笔交易 |
| 条件格式化 | 如根据状态标记行颜色 |
| 多表合并 | 如客户与订单表按ID合并 |
| 批量文件生成 | 如根据模板自动生成邀请函、产品文档 |
| 数据过滤、排序与导出 | 按条件筛选数据并导出 |

---

## §5 Skills vs 其他组件对比

### 5.1 生态系统全景图

```
┌────────────────────────────────────────────────────────────┐
│                    AI Agent（智能体）                        │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Skills（技能）= 可重复的工作流                       │   │
│  │  - 专业知识和指令                                   │   │
│  │  - 定义处理数据的标准方法论                         │   │
│  └──────────────────────────────────────────────────┘   │
│                         ↑                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │ MCP Servers（模型上下文协议）                        │   │
│  │  - 提供外部数据和工具                              │   │
│  │  - 按需加载                                       │   │
│  └──────────────────────────────────────────────────┘   │
│                         ↑                                │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Tools（工具）                                     │   │
│  │  - 底层能力：文件系统、代码执行、Bash              │   │
│  │  - 每次都加载                                     │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────-───┘
                            ↓
          ┌─────────────────────────────────────┐
          │  Subagents（子代理）                 │
          │  - 隔离上下文                       │
          │  - 可访问Skills                      │
          │  - 并行执行                          │
          └─────────────────────────────────────┘
```

### 5.2 Skills vs MCP

| 对比维度 | MCP | Skills |
|---------|-----|--------|
| **核心功能** | 连接智能体与外部系统和数据 | 定义可重复的工作流 |
| **数据来源** | 外部数据库等 | 利用MCP提供的工具和数据 |
| **使用场景** | 获取模型不知道的外部数据 | 教智能体如何处理这些数据 |

**比喻理解**：
- **MCP** 就像带来所有底层工具和资源的**连接器**
- **Skills** 就像使用这些工具构建特定工作流的**可重复流程**

### 5.3 Skills vs Tools

| 对比维度 | Tools（工具） | Skills（技能） |
|---------|--------------|----------------|
| **功能** | 提供访问文件系统的方式 | 扩展智能体的能力，提供专业知识和指令 |
| **性质** | 提供底层能力来生成、读取技能 | 引入需要执行的额外文件和脚本 |
| **使用方式** | 支持文件编辑、执行代码、加载技能 | 创建可预测的工作流 |
| **加载方式** | 始终存在于上下文窗口 | 渐进式加载，只在需要时加载 |

**比喻理解**：
- **Tools** = 锤子、锯子和钉子（提供底层能力）
- **Skills** = 如何建造书架（定义工作流程）

### 5.4 Skills vs Subagents

| 对比维度 | Subagents（子代理） | Skills（技能） |
|---------|-------------------|----------------|
| **核心特性** | 隔离上下文 | 提供专业知识和指令 |
| **使用场景** | 并行化执行，在独立线程和上下文中运行 | 以可预测、可重复、可移植的方式消费所有信息 |
| **权限** | 限制工具使用权限 | 每个子代理可以访问特定的技能 |

### 5.5 完整组件对比表

| 组件 | 定义 | 特点 |
|------|------|------|
| **Prompts（提示词）** | 与模型通信的最原子单位 | 基础但不易扩展 |
| **Skills（技能）** | 通过代码和资源打包提示词和对话 | 可预测、可重复、可移植 |
| **Subagents（子代理）** | 被委派任务的独立智能体 | 可复用技能，隔离上下文 |
| **MCP** | 定义子代理使用的工具 | 按需加载必要数据 |

---

## §6 综合案例：客户洞察分析器

### 6.1 架构详解

这是一个典型的多层AI Agent系统：

**Agent层（大脑与指挥中心）**
- LLM作为推理引擎，能够理解复杂指令、进行多步思考和决策规划
- 配备代码执行环境，支持动态调用工具和执行脚本
- 主要职责：接收高层任务目标，将其拆解为可执行的子任务，协调下方两个子分析器并行工作

**Subagents层（执行手臂）**
- **Interview Analyzer**：处理非结构化的客户访谈记录，运用自然语言理解技术提取关键观点、情感倾向和深层需求
- **Survey Analyzer**：针对结构化的问卷数据进行统计分析、模式识别和趋势归纳
- 两个工具相互独立又可并行运行

**Skills层（能力基础设施）**
- Filesystem作为技能容器，封装了多个可复用的Skill模块
- 指导文档作为元指令（Meta-prompt），定义了系统处理数据的标准方法论
- 实现了"知识即配置"的理念

**MCP层（外部连接）**
- 三个MCP服务器：MCP server 1、MCP server 3、Google Drive MCP
- Agent能够以统一的方式调用不同服务商的API

### 6.2 工作流程

```
主智能体（配备工具）
    ↓
通过MCP服务器获取工具
    ↓
分派子代理分析客户
    ↓
并行分析客户访谈和调查
    ↓
使用Skills进行可预测的分析
```

### 6.3 各组件作用

| 组件 | 作用 |
|------|------|
| **MCP** | 外部引入数据 |
| **子代理** | 并行化执行，在独立线程和上下文中运行 |
| **Skills** | 以可预测、可重复、可移植的方式消费所有信息 |

---

## §7 创建自定义Skills实战

### 7.1 Skill文件夹完整结构

以Excel Skill为例：

```
excel-skill/
├── SKILL.md                    # 说明技能用途、输入输出、流程
├── scripts/
│   ├── process_data.py         # 数据处理脚本
│   └── recalc.py               # 公式重算脚本
└── references/
    ├── example_input.xlsx       # 输入样例
    ├── output_template.xlsx     # 输出模板
    └── rules.md                 # 规则文档
```

### 7.2 技术路线选择

| 工具 | 适用场景 |
|------|---------|
| **pandas** | 批量数据处理、分析、导出 |
| **openpyxl** | 复杂格式、公式、Excel特性操作 |

### 7.3 工作流程

1. **选择工具**：根据需求选择pandas或openpyxl
2. **创建/加载文件**：新建或读取工作簿
3. **数据处理**：增删改查、公式、格式化
4. **保存文件**：写回Excel
5. **公式重算**：如涉及公式，需用recalc.py脚本进行重算（openpyxl仅写入公式字符串，不计算结果）
6. **错误校验与修复**：Skill应返回JSON报告所有错误类型和位置，便于二次修正

### 7.4 最佳实践

1. **明确输入输出标准**：示例文件放在references目录
2. **异常处理**：所有脚本应有异常处理与错误报告能力，便于Agent自动修复
3. **模块化实现**：复杂逻辑建议分模块实现，主流程在SKILL.md中清晰描述
4. **公式分离**：Excel公式相关操作建议分离脚本处理，避免直接在openpyxl中计算
5. **输出中间结果**：尽量输出中间结果与最终数据，便于人工或Agent二次校验

---

## §8 课程章节速览

| 章节 | 内容 | 核心要点 |
|------|------|---------|
| **1. Introduction** | 课程介绍 | Skills定义、三大特点、组合使用 |
| **2. Why Use Skills I** | Skills的意义 | 三大用武之地、渐进式披露、Excel Skill案例 |
| **3. Why Use Skills II** | 从Agent角度思考 | Agent与Skills的关系、协作模式 |
| **4. Skills vs Tools/MCP/Subagents** | 组件对比 | 生态系统全景、各组件协作 |
| **5. Exploring Pre-Built Skills** | 预设Skills探索 | 官方Skills使用 |
| **6. Creating Custom Skills** | 自定义Skills | 创建流程、最佳实践 |
| **7. Skills with Claude API** | API使用 | 在Claude API中使用Skills |
| **8. Skills with Claude Code** | Claude Code使用 | 在Claude Code中使用Skills |
| **9. Skills with Agent SDK** | SDK使用 | 在Claude Agent SDK中使用Skills |
| **10. Conclusion** | 总结 | 回顾与展望 |

---

## §9 总结

### 9.1 Skills的核心价值

**Skills为AI Agent提供了专业化、标准化、可复用的能力扩展载体，极大提升了自动化办公与复杂数据处理的效率。**

通过SKILL.md元数据、脚本与参考文件的组合，实现了从数据读取、处理、输出到结果校验的自动化全流程。

### 9.2 未来展望

随着Skill生态的丰富，AI Agent将能像积木一样组合各种能力，满足更多元的业务需求。Skills的开放标准使得一次构建、多处部署成为可能，这将是AI Agent生态发展的重要方向。

### 9.3 学习路径建议

1. **入门**：先学习Introduction和Why Use Skills，理解Skills的核心概念
2. **进阶**：深入研究Skills vs Tools/MCP/Subagents的对比，理解生态系统
3. **实践**：通过Creating Custom Skills章节学习创建自己的Skill
4. **扩展**：探索Pre-Built Skills，了解官方Skill的使用方法

---

## 附录：快速参考

### YAML Frontmatter字段

| 字段 | 必填 | 说明 |
|------|-----|------|
| `name` | 是 | Skill名称，唯一标识 |
| `description` | 是 | Skill描述，用于匹配用户请求 |
| `inputs` | 否 | 输入格式要求 |
| `outputs` | 否 | 输出格式说明 |

### Skills加载方式

| 类型 | 加载时机 | 说明 |
|------|---------|------|
| **Metadata** | 始终加载 | name、description |
| **Instructions** | 触发时加载 | Markdown正文内容 |
| **Resources** | 按需加载 | scripts/、references/ |

---

*🦞 本文由钳岳星君基于 [Datawhale/agent-skills-with-anthropic](https://github.com/datawhalechina/agent-skills-with-anthropic) 项目撰写，原始课程来自 DeepLearning.AI × Anthropic。*
