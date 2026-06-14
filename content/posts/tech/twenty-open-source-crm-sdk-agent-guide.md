---
title: "Twenty：开源CRM的「代码优先」实践，用SDK定义Object、工作流和Agent"
date: "2026-05-29T09:06:54+08:00"
slug: "twenty-open-source-crm-sdk-agent-guide"
description: "Twenty是一款开源CRM，以「代码优先」为核心设计理念——Object定义、工作流配置和AI Agent全部可通过TypeScript代码管理，像发布代码一样发布CRM变更。本文覆盖其核心能力、App开发模式和快速上手路径。"
draft: false
categories: ["技术笔记"]
tags: ["CRM", "开源", "TypeScript", "AI Agent", "NestJS", "PostgreSQL"]
---

# Twenty：开源 CRM 的「代码优先」实践

Twenty 给自己的定位很直接：**The #1 Open-Source CRM**，同时也是 Salesforce 的开源替代方案。但它的野心不止于此——它真正想做的是把 CRM 变成工程团队可以「编写、发布和版本化管理」的普通代码。

这不是一个典型的「配置型 CRM」向技术人员妥协的产物，而是一个从一开始就按照开发者工作流设计的 CRM 平台。

## 核心判断

Twenty 的核心差异在于：它的所有配置（Object 定义、字段、视图、工作流、AI Agent）都可以通过 TypeScript 代码描述，并通过 CLI 发布到工作区。这意味着 CRM 的变更可以走 Git，可以做 Code Review，可以回滚——这是传统 SaaS CRM 做不到的事。

## 系统地图

Twenty 的技术栈：

| 层级 | 技术选型 |
|------|---------|
| 语言 | TypeScript |
| 后端框架 | NestJS + BullMQ |
| 数据库 | PostgreSQL |
| 缓存 | Redis |
| 前端 | React + Jotai + Linaria + Lingui |
| 构建工具 | Nx |

CRM 核心能力模块：

- **Objects**：可自定义的实体对象（类似 Salesforce 的 Custom Object）
- **Views**：数据的多视图展示和布局管理
- **Workflows**：工作流自动化
- **AI Agents**：内置 AI Agent 能力，支持在 CRM 内执行智能任务

## 快速上手

### 安装方式一：Cloud（最快）

访问 [twenty.com](https://twenty.com)，注册后一键创建工作区，无需管理基础设施，始终保持最新版本。

### 安装方式二：本地 CLI

```bash
npx create-twenty-app my-app
```

这个命令会脚手架一个完整的 Twenty 项目，包含 Object 定义、字段配置和视图模板。

### 定义一个 Object

```ts
import { defineObject, FieldType } from 'twenty-sdk/define';

export default defineObject({
  nameSingular: 'deal',
  namePlural: 'deals',
  labelSingular: 'Deal',
  labelPlural: 'Deals',
  fields: [
    { name: 'name', label: 'Name', type: FieldType.TEXT },
    { name: 'amount', label: 'Amount', type: FieldType.CURRENCY },
    { name: 'closeDate', label: 'Close Date', type: FieldType.DATE_TIME },
  ],
});
```

Object 可以定义任意自定义字段，字段类型覆盖 TEXT、CURRENCY、DATE_TIME 等常见类型。

### 发布 Object

```bash
npx twenty app:publish --private
```

这条命令将代码中定义的 Object 发布到指定工作区。与传统 CRM 的「点击保存」相比，这里的「发布」是命令行操作，可以写入 CI/CD 流水线。

## App 开发模式：CRM 的二次开发方式

Twenty 在 v2 版本引入了「Apps」概念，允许开发者以代码形式扩展 CRM：

- **Objects**：以代码描述的数据模型
- **Views**：布局和展示配置
- **Agents**：AI Agent 的定义
- **Logic Functions**：业务逻辑函数

每个 App 都可以独立发布，版本化管理，适合技术团队自主维护 CRM 能力而不依赖供应商。

## AI Agent 能力

Twenty 内置 AI Agent，支持在 CRM 上下文中执行任务。具体能力包括：

- 基于 CRM 数据的智能问答
- 工作流自动化建议
- 任务创建和分配

官方文档中的截图展示了「AI agents and chats」界面，但详细的 Agent API 文档和可配置边界仍需参考 [官方文档](https://docs.twenty.com/user-guide/ai/overview)。

## 适用边界

**值得考虑 Twenty 的场景：**
- 技术团队需要自主管理 CRM 行为，不接受 SaaS 平台的「配置锁定」
- 希望 CRM 变更走 Git 工作流，做 Code Review 和版本化
- 需要在 CRM 内构建 AI 驱动的工作流

**不适合或需要谨慎的场景：**
- 非技术团队主导 CRM 配置和使用的组织
- 需要强 vendor lock-in 支持的敏感业务场景
- 还在评估 CRM 基本功能的阶段（ Twenty 的功能丰富度尚在追赶 Salesforce 的过程中）

## 技术债务提示

Twenty 是一个相对较新的项目，GitHub 页面显示仍在活跃维护中。self-hosting 方式为 Docker Compose，适合有容器化运维能力的团队。

## 阅读路径

- [Twenty官网](https://twenty.com)
- [官方文档](https://docs.twenty.com)
- [App开发指南](https://docs.twenty.com/developers/extend/apps/getting-started)
- [本地开发指南](https://docs.twenty.com/developers/contribute/capabilities/local-setup)
- [GitHub仓库](https://github.com/twentyhq/twenty)