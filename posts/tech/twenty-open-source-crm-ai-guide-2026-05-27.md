---
title: "Twenty CRM 完全指南：AI 原生的开源 Salesforce 替代方案"
date: 2026-05-27T03:05:00+08:00
tags: ["CRM", "开源", "TypeScript", "React", "AI", "NestJS", "PostgreSQL"]
categories: ["企业软件"]
description: "Twenty 是开源 CRM 领域的领导者，号称 AI 时代的 Salesforce 替代品。本文深入解析其架构、功能、CLI 工具和自定义能力。"
---

# Twenty CRM 完全指南：AI 原生的开源 Salesforce 替代方案

## 简介

[Twenty](https://github.com/twentyhq/twenty) 是排名第 1 的开源 CRM，已获得 **46,743** Star。它旨在给技术团队提供构建定制化 CRM 的基础模块，像管理代码一样管理 CRM 版本。

官网：[twenty.com](https://twenty.com)
文档：[docs.twenty.com](https://docs.twenty.com)

## 核心价值主张

> Twenty gives technical teams the building blocks for a custom CRM that meets complex business needs and quickly adapts as the business evolves.

Twenty 是你构建、部署、版本控制得像其他代码库一样的 CRM。

## 快速开始

### 云端（最快）

访问 [twenty.com](https://twenty.com) 注册，1 分钟内启动工作空间。

### 使用 CLI 构建应用

```bash
# 创建一个新应用
npx create-twenty-app my-app

# 进入目录
cd my-app
```

### 定义对象和字段

```typescript
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

### 发布到工作空间

```bash
npx twenty app:publish --private
```

## 功能一览

### CRM 核心功能

- **对象管理** — 自定义 CRM 对象（公司、联系人、交易等）
- **视图和仪表盘** — 灵活的数据展示和可视化
- **工作流** — 自动化业务流程
- **AI Agents** — 内置 AI 助手处理 CRM 相关任务

### 技术特性

| 特性 | 说明 |
|------|------|
| 版本控制 | 所有对象定义可以像代码一样 Git 管理 |
| GraphQL API | 完整的 GraphQL 接口供外部集成 |
| 多工作空间 | 支持隔离的团队/组织工作空间 |
| 实时协作 | 团队成员实时看到数据变化 |

## 技术栈

| 层级 | 技术 |
|------|------|
| 语言 | TypeScript |
| 后端 | NestJS + BullMQ |
| 数据库 | PostgreSQL |
| 缓存 | Redis |
| 前端 | React + Jotai + Linaria |
| 国际化 | Lingui |
| 构建 | Nx (monorepo) |

## 项目结构

```
packages/
├── twenty-front/          # React 前端
├── twenty-server/          # NestJS 后端
├── twenty-website/         # 官网
├── twenty-sdk/             # SDK (defineObject, CLI)
└── twenty-workers/         # 后台任务 workers
```

## 自托管部署

### Docker Compose（推荐生产部署）

参考 [官方 Docker Compose 文档](https://docs.twenty.com/developers/self-host/capabilities/docker-compose)。

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/twentyhq/twenty.git
cd twenty

# 安装依赖并启动
# 参考 docs.twenty.com/developers/contribute/capabilities/local-setup
```

## 为什么选择 Twenty？

### 对比 Salesforce

| 维度 | Twenty | Salesforce |
|------|--------|------------|
| 费用 | 免费开源 | 昂贵订阅 |
| 可定制性 | 代码级定制 | 受限定制 |
| 版本控制 | ✅ | ❌ |
| 数据控制 | 完全自有 | 厂商锁定 |
| AI 集成 | 原生 AI Agents | 需付费升级 |

### 对比其他开源 CRM

| CRM | 优势 | 劣势 |
|------|------|------|
| Twenty | TypeScript-first、AI 原生 | 较新 |
| ERPNext | 功能完整、ERP 集成 | Python/Frappe |
| Odoo | 企业级、功能全 | 复杂、贵 |

## AI Agents 功能

Twenty 内置 AI Agents，可以：

- 自动填充 CRM 记录
- 生成销售报告和洞察
- 自动化日常 CRM 任务
- 智能搜索和推荐

## 扩展性

### 通过 App 发布自定义逻辑

```bash
npx twenty app:publish --private
npx twenty app:publish --public  # 公开分享
```

### GraphQL API

完整的 GraphQL API 支持外部系统集成，文档：`http://localhost:3000/api-docs`

## 社区和生态

- **Discord** — [官方 Discord](https://discord.gg/cx5n4Jzs57)
- **Roadmap** — [GitHub Projects](https://github.com/orgs/twentyhq/projects/1)
- **Figma** — [设计稿](https://www.figma.com/file/xt8O9mFeLl46C5InWwoMrN/Twenty)

## 总结

Twenty 代表了新一代开源 CRM 的方向——不是功能堆砌，而是给技术团队提供可编程的构建块。通过将 CRM 对象定义为代码，它让技术团队可以用 Git 管理 CRM 版本，用熟悉的工具部署和迭代。

**GitHub**: [twentyhq/twenty](https://github.com/twentyhq/twenty)
**Star**: 46,743 | **Fork**: 6,637
**官网**: [twenty.com](https://twenty.com)