---
title: "Anthropic Knowledge Work Plugins 官方指南：让 Claude 成为你的专业助手"
date: 2026-05-27T03:05:00+08:00
tags: ["Claude", "Anthropic", "Cowork", "插件", "AI助手", "知识工作"]
categories: ["AI工具"]
description: "深入解析 Anthropic 官方开源的 11 款知识工作插件，如何将 Claude 打造成团队专属的专业助手，涵盖生产力、销售、客服、产品管理等多个领域。"
---

# Anthropic Knowledge Work Plugins 官方指南：让 Claude 成为你的专业助手

## 简介

[Anthropic Knowledge Work Plugins](https://github.com/anthropics/knowledge-work-plugins) 是 Anthropic 官方开源的插件仓库，专为知识工作者设计，旨在将 Claude 打造成各行各业的专业助理。这些插件最初为 [Claude Cowork](https://claude.com/product/cowork) 构建，同时兼容 [Claude Code](https://claude.com/product/claude-code)。

截至目前，该项目已获得 **16,536** Star，是 Claude 生态中最受欢迎的插件集合之一。

## 为什么需要插件？

Cowork 让你设定目标，Claude 完成专业工作。插件让你更进一步：告诉 Claude 你喜欢如何工作、需要从哪些工具和数据中拉取、如何处理关键工作流程，以及暴露哪些斜杠命令——让你的团队获得更好、更一致的结果。

每个插件将特定工作所需的技能、连接器、斜杠命令和子代理打包在一起。开箱即用，它们为该角色中的任何人提供强大的起点。真正的力量来自于为你的公司定制它们——你的工具、你的术语、你的流程——让 Claude 工作起来就像为你的团队量身打造的一样。

## 插件市场：11 款官方插件一览

| 插件 | 功能 | 支持的连接器 |
|------|------|-------------|
| **[productivity](./productivity)** | 管理任务、日历、日常工作流和个人上下文 | Slack, Notion, Asana, Linear, Jira, Monday, ClickUp, Microsoft 365 |
| **[sales](./sales)** | 研究潜在客户、准备电话、审查管道、起草外联和构建竞争卡 | Slack, HubSpot, Close, Clay, ZoomInfo, Notion, Jira, Fireflies, Microsoft 365 |
| **[customer-support](./customer-support)** | 分流工单、起草回复、封装升级、研究客户上下文 | Slack, Intercom, HubSpot, Guru, Jira, Notion, Microsoft 365 |
| **[product-management](./product-management)** | 撰写规范、规划路线图、综合用户研究 | Slack, Linear, Asana, Monday, ClickUp, Jira, Notion, Figma, Amplitude, Pendo, Intercom, Fireflies |
| **[marketing](./marketing)** | 起草内容、计划活动、执行品牌声音 | Slack, Canva, Figma, HubSpot, Amplitude, Notion, Ahrefs, SimilarWeb, Klaviyo |
| **[legal](./legal)** | 审查合同、分流 NDA、评估风险、起草模板回复 | Slack, Box, Egnyte, Jira, Microsoft 365 |
| **[finance](./finance)** | 准备日记账分录、对账账户、生成财务报表 | Snowflake, Databricks, BigQuery, Slack, Microsoft 365 |
| **[data](./data)** | 查询、可视化和解释数据集——编写 SQL、运行统计分析 | Snowflake, Databricks, BigQuery, Definite, Hex, Amplitude, Jira |
| **[enterprise-search](./enterprise-search)** | 跨邮件、聊天、文档和 wiki 搜索任何内容 | Slack, Notion, Guru, Jira, Asana, Microsoft 365 |
| **[bio-research](./bio-research)** | 连接临床前研究工具和数据库 | PubMed, BioRender, bioRxiv, ClinicalTrials.gov, ChEMBL, Synapse, Wiley, Owkin, Open Targets, Benchling |
| **[cowork-plugin-management](./cowork-plugin-management)** | 创建或自定义插件 | — |

## 安装指南

### Claude Cowork

直接从 [claude.com/plugins](https://claude.com/plugins/) 安装插件。

### Claude Code

```bash
# 添加市场
claude plugin marketplace add anthropics/knowledge-work-plugins

# 安装特定插件
claude plugin install sales@knowledge-work-plugins
```

安装后，插件会自动激活。技能在相关时会触发，斜杠命令在会话中可用（如 `/sales:call-prep`、`/data:write-query`）。

## 插件工作原理

每个插件遵循相同结构：

```
plugin-name/
├── .claude-plugin/plugin.json   # 清单文件
├── .mcp.json                    # 工具连接
├── commands/                    # 显式调用的斜杠命令
└── skills/                      # Claude 自动调用的领域知识
```

- **Skills** 编码 Claude 需要提供有用帮助的领域专业知识、最佳实践和逐步工作流程。Claude 在相关时自动调用它们。
- **Commands** 是你显式触发的操作（如 `/finance:reconciliation`、`/product-management:write-spec`）。
- **Connectors** 通过 [MCP 服务器](https://modelcontextprotocol.io/) 将 Claude 连接到你的角色所依赖的外部工具。

每个组件都是基于文件的——Markdown 和 JSON，无需代码、无基础设施、无构建步骤。

## 深度定制

这些插件是通用的起点。当为你公司实际工作方式定制时，它们会变得更有用：

- **交换连接器** — 编辑 `.mcp.json` 指向你的特定工具栈
- **添加公司上下文** — 将你的术语、组织结构和流程放入技能文件中，让 Claude 理解你的世界
- **调整工作流程** — 修改技能指令以匹配你的团队实际做事方式
- **构建新插件** — 使用 `cowork-plugin-management` 插件或遵循上述结构

## 技术栈与扩展性

所有插件使用纯文件格式，通过 MCP（Model Context Protocol）协议连接外部工具。这意味着：

1. **无需编写代码** — 只需编辑 Markdown 和 JSON
2. **完全可扩展** — 任何实现了 MCP 的工具都可以接入
3. **版本控制友好** — 所有配置都是文本文件，可以像代码一样管理

## 适用场景

- **企业团队** — 需要统一 AI 助手的专业能力
- **销售团队** — 需要自动化的客户研究和外联
- **产品团队** — 需要规范的需求管理和路线图规划
- **数据团队** — 需要快速 SQL 查询和数据分析
- **客服团队** — 需要智能工单分类和响应

## 总结

Anthropic 的知识工作插件代表了 AI 助手发展的新方向——不是通用工具，而是专业化的、可定制的领域专家。通过开源这些插件，Anthropic 让任何组织都能快速拥有一个量身定制的 AI 团队成员，大幅提升知识工作效率。

**GitHub**: [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)
**Star**: 16,536 | **Fork**: 1,943