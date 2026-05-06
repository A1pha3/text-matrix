---
title: "Anthropic Financial Services：Claude金融行业智能体与技能库"
date: "2026-05-06T20:05:34+08:00"
slug: "anthropics-claude-financial-services-guide"
description: "Anthropic官方金融服务业Claude智能体库，涵盖投行、行研、私募等场景，提供Pitch Agent、DCF建模等插件，支持Cowork和Managed Agents两种部署方式。"
draft: false
categories: ["技术笔记"]
tags: ["Claude", "AI Agent", "金融", "Anthropic", "投资银行"]
---

Anthropic Financial Services 是 Anthropic 官方发布的**金融服务业垂直领域 Claude 智能体和工作流技能库**。它将金融行业常见的工作流（投行Pitch、 Equity Research、私募、财富管理等）封装为可安装的智能体插件，分析师可以直接在 Claude Cowork 中使用，也可以通过 Claude Managed Agents API 自行部署。

> ⚠️ **重要声明**：本仓库中的任何内容均不构成投资、法律、税务或会计建议。这些智能体生成的仅是分析师工作产品（模型、备忘录、研究笔记、对账表），用于辅助专业人士审阅，不构成投资推荐或交易执行指令。所有输出都需要人工复核。

## 核心定位

Anthropic Financial Services 解决的是**金融行业 AI 落地最后一公里**的问题。传统的通用 AI 助手无法理解投行、行研等垂直领域的专业术语、工作流程和输出规范。Anthropic 通过与金融机构合作，将专业工作流封装为开箱即用的智能体，降低了 AI 在金融行业的落地门槛。

## 智能体矩阵

### 覆盖与咨询类

| 智能体 | 功能 |
|--------|------|
| **Pitch Agent** | 承销Pitch全程：从可比公司分析（comps）、先例交易（precedents）到 LBO 建模，输出品牌化 Pitch Deck |
| **Meeting Prep Agent** | 客户会议前简报包，自动整理相关背景材料和数据 |

### 研究与建模类

| 智能体 | 功能 |
|--------|------|
| **Market Researcher** | 行业或主题研究，输出行业概览、竞争格局、可比公司列表和 ideas 短名单 |
| **Earnings Reviewer** | 分析财报和电话会，触发模型更新，生成财报点评草稿 |
| **Model Builder** | 构建 DCF、LBO、三张报表联动模型、可比公司分析——直接在 Excel 中运行 |

### 基金行政与财务运营类

| 智能体 | 功能 |
|--------|------|
| **Valuation Reviewer** | 消化 GP 数据包，运行估值模板，准备 LP 报告 |
| **GL Reconciler** | 自动发现总账不平项，追溯根本原因，分流给对应人员审批 |
| **Month-End Closer** | 计提、滚动-forward、差异分析，自动生成结账备忘录 |
| **Statement Auditor** | 审计 LP 报表，在分发前发现错误 |

### 运营与合规类

| 智能体 | 功能 |
|--------|------|
| **KYC Screener** | 解析开户文件，触发规则引擎，标注合规缺口 |

## 垂直插件体系

除了完整智能体，Anthropic Financial Services 还提供了按金融行业垂直分类的**技能包（Skills Bundle）**：

- **Investment Banking**：投行专属技能集
- **Equity Research**：Equity Research 专属技能集
- **Skills**：各垂直领域共享的通用金融分析技能

这些技能包可以独立安装，与其他智能体组合使用，灵活性更高。

## 部署方式

Anthropic Financial Services 支持两种部署路径：

### 方式一：Claude Cowork 插件安装

在 Claude Cowork 中（Settings → Plugins → Add plugin），输入仓库地址：

```
https://github.com/anthropics/claude-for-financial-services
```

然后从市场列表中选择想要安装的智能体和垂直技能包。

### 方式二：Claude Code 安装

```bash
# 添加市场
claude plugin marketplace add anthropics/claude-for-financial-services

# 安装核心技能和连接器
claude plugin install financial-analysis@claude-for-financial-services

# 安装指定智能体
claude plugin install pitch-agent@claude-for-financial-services
claude plugin install gl-reconciler@claude-for-financial-services
claude plugin install market-researcher@claude-for-financial-services

# 安装垂直技能包
claude plugin install investment-banking@claude-for-financial-services
claude plugin install equity-research@claude-for-financial-services
```

安装后，智能体出现在 Cowork 的调度界面，技能会自动触发，斜杠命令（如 `/comps`、`/dcf`、`/earnings`、`/ic-memo`）可直接使用。

### 方式三：Claude Managed Agents API 部署

通过 `/v1/agents` 接口自行部署，每个智能体模板都提供了 `agent.yaml`、子智能体配置和安全说明：

```bash
export ANTHROPIC_API_KEY=sk-ant-...
scripts/deploy-managed-agent.sh gl-reconciler
```

详细的事件循环参考：[`scripts/orchestrate.py`](./scripts/orchestrate.py)，展示了如何通过自建编排层处理 `handoff_request` 事件在子智能体之间路由。

## 仓库结构

```
plugins/
  agent-plugins/        # 独立智能体插件（每个插件自包含）
  vertical-plugins/      # 按金融垂直领域分类的技能包 + MCP 连接器
  partner-built/         # 合作伙伴（LSEG、S&P Global 等）编写的插件
managed-agent-cookbooks/ # Claude Managed Agent 模板（每个智能体一个目录）
claude-for-msft-365-install/  # Microsoft 365 插件管理工具
scripts/                 # 部署和编排脚本
```

## 技术架构

| 组件 | 说明 |
|------|------|
| **智能体（Agent）** | 自包含插件，包含系统提示词和所需技能，Cowork 和 Managed Agent 包装器共用同一目录 |
| **技能（Skills）** | 领域专业知识、规范和步骤方法，编写一次，在各智能体间同步 |
| **斜杠命令（Commands）** | 显式触发的斜杠操作（`/comps`、`/earnings` 等） |
| **连接器（Connectors）** | MCP 服务器，将 Claude 连接到数据源（终端、研究平台、文档库） |
| **Managed Agent 包装器** | `agent.yaml` + 子智能体配置 + 引导示例 |

## 与传统金融工具的集成

Anthropic Financial Services 通过 MCP 协议与外部数据源连接：

- **Financial Data Platforms**：Bloomberg、Refinitiv 等（通过合作伙伴连接器）
- **Document Management**：内部文档库、研究报告存储
- **Excel/Python**：直接操作财务模型

## 使用边界

| 适合的场景 | 不适合的场景 |
|-----------|-------------|
| 投行分析师撰写 Pitch Deck 初稿 | 生成具有约束力的投资建议 |
| 研究员快速整理财报要点 | 替代人工尽职调查 |
| 财务人员做期末结账对账 | 执行涉及监管合规的关键审批 |
| 市场研究员整理行业概览 | 替代监管机构审批流程 |

所有输出都需要经过**有资质专业人士的复核**，系统不会生成具有约束力的交易指令或监管文件。

## 总结

Anthropic Financial Services 是 AI 在金融行业垂直落地的标杆项目。它不是简单地把 LLM API 包装成聊天机器人，而是深入理解金融工作流（从 Comps 到 LBO、从 Earnings Review 到 GL Reconciliation），将行业专业知识封装为可安装、可组合的智能体插件。对金融从业者来说，这是目前最接近"AI 分析师助手"的开源解决方案。

- **GitHub**：https://github.com/anthropics/financial-services
- **Cowork 插件市场**：直接在 Claude Cowork 中搜索 "Anthropic Financial Services"
