+++
date = '2026-05-26T23:00:00+08:00'
draft = false
title = 'Twenty：Salesforce 的开源替代'
slug = 'twenty-open-source-crm-ai-alternative-guide'
description = 'Twenty 是一个开源的 AI 优先 CRM 系统，TypeScript 全栈开发，PostgreSQL 存储，支持自定义对象和工作流自动化，是 Salesforce 的替代方案。'
categories = ['技术笔记']
tags = ['开源', 'AI', 'TypeScript', 'CRM']
+++

# Twenty：Salesforce 的开源替代

Twenty 把 CRM 当代码发布。对象、字段、视图写在 TypeScript 文件里，用 `npx twenty app:publish --private` 推到工作区；Salesforce 那套在 UI 里点击创建自定义对象、再通过 Metadata API 导出 XML 的路径，在这里被换成了 `defineObject` 函数和版本控制。截至 2026 年 5 月，仓库到达 v2.8.0，12,313 次提交，73 个 release，技术栈从早期的 GraphQL Yoga + TypeORM 收敛到 NestJS + BullMQ + PostgreSQL + Redis 的组合。

这篇文章要回答的问题是：把 CRM 的数据模型、视图、工作流全部放进代码版本控制，这条路在 2026 年走通了吗，哪些团队该上，哪些团队该等。

## 开源 CRM 的市场分层

Salesforce 的锁定问题主要在数据模型层。业务一旦跑在自定义对象、APEX 触发器、Flow 自动化上，迁移成本随业务复杂度指数级增长。按席位定价（Enterprise 版列表价 $165/用户/月，Unlimited 版 $330/用户/月）在团队扩张时也会变成固定成本压力。开源 CRM 选项一直存在，但定位分散：

| 项目 | 定位 | 技术栈 | 适合谁 |
| --- | --- | --- | --- |
| Odoo | ERP 套件，CRM 是其中一个模块 | Python + PostgreSQL | 需要进销存、财务、库存一体化的团队 |
| ERPNext | ERP 套件，CRM 是其中一个模块 | Python + MariaDB | 同上，偏好 Frappe 框架的团队 |
| SuiteCRM | SugarCRM 社区版分支 | PHP + MySQL | 从 SugarCRM 迁移的存量用户 |
| Twenty | 纯 CRM，代码优先 | TypeScript + NestJS + React | 把 CRM 当产品代码来管理的工程团队 |

Twenty 的差异点在最后一行。它不做 ERP，不做进销存，只做 CRM，但把 CRM 的对象模型、视图、工作流全部放进代码版本控制。Odoo 和 ERPNext 的 CRM 模块可以通过 Python 代码扩展，但对象定义本身仍然在数据库里，靠模块安装时写入；Twenty 把对象定义放在 TypeScript 文件里，跟业务代码一起 review、一起发布。

## 架构总览

```text
┌─────────────────────────────────────────────────────────────┐
│                  Twenty Monorepo (Nx)                        │
├─────────────────────────┬───────────────────────────────────┤
│    twenty-front         │         twenty-server             │
│    React 18             │         NestJS                    │
│    Jotai (状态管理)      │         BullMQ (任务队列)          │
│    Linaria (CSS-in-JS)  │         GraphQL API (/graphql)    │
│    Lingui (i18n)        │         REST API (/rest)          │
│    Vite (构建)           │         Worker (后台任务)          │
├─────────────────────────┴───────────────────────────────────┤
│    PostgreSQL 16          │        Redis (缓存 + 队列)       │
└─────────────────────────────────────────────────────────────┘
```

后端用 NestJS 框架，BullMQ 处理异步任务（邮件发送、工作流触发、AI 调用），PostgreSQL 16 存储业务数据，Redis 做缓存和任务队列。前端从早期的 Styled-components 迁移到 Linaria（零运行时 CSS-in-JS），状态管理用 Jotai，国际化用 Lingui。整个仓库用 Nx 管理为 monorepo，`twenty-front`、`twenty-server`、`twenty-eslint-rules`、`twenty-website` 等包共享同一个 TypeScript 配置。

开发环境要求 Node v24.5.0 和 yarn v4，`npm` 和 `pnpm` 不支持。本地启动需要 PostgreSQL 和 Redis 两个外部依赖，可以通过 `make -C packages/twenty-docker postgres-on-docker` 和 `redis-on-docker` 快速拉起。服务端口分配：前端 `http://localhost:3001`，后端 `http://localhost:3000`，GraphQL API 在 `/graphql`，REST API 在 `/rest`。

## 自定义对象：代码优先 vs 元数据导出

Twenty 的自定义对象通过 `twenty-sdk/define` 包里的 `defineObject` 函数定义，跟 Salesforce 的 Custom Object 在概念上对应，但实现路径不同。Salesforce 的流程是在 Setup UI 里点击创建对象和字段，系统写入数据库和 Metadata API，需要版本控制时再用 Salesforce DX 或 Gearset 导出 XML。Twenty 的流程是直接写 TypeScript 文件，对象定义本身就是代码。

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

这段代码定义了一个 `Deal` 对象，包含三个字段：文本类型的 `name`、货币类型的 `amount`、日期类型的 `closeDate`。`FieldType` 枚举覆盖了 TEXT、CURRENCY、DATE_TIME、NUMBER、SELECT、MULTI_SELECT、LINK、RICH_TEXT 等类型，跟 Salesforce 的 Field Types 基本对齐。差异在版本控制：这个文件可以进 Git，可以 review，可以在 CI 里跑类型检查；Salesforce 的自定义对象要达到同样的效果，需要额外部署 Salesforce DX 项目结构和 metadata 解析流程。

## 一次完整的发布流程

把一个自定义对象从代码推到工作区，完整路径如下：

```bash
# 1. 用 CLI 脚手架创建 app 项目
npx create-twenty-app my-app

# 2. 在项目里定义对象、字段、视图（TypeScript 文件）
#    编辑 src/objects/deal.ts，写入上面的 defineObject 代码

# 3. 发布到工作区（--private 表示只发布到当前工作区）
npx twenty app:publish --private
```

`app:publish` 执行时，CLI 会把 TypeScript 定义编译成 GraphQL mutation，调用 Twenty server 的 `/graphql` 端点，在工作区的 metadata 表里创建对象记录，同时在 PostgreSQL 的业务表里建对应的物理表。前端订阅 GraphQL schema 变更，自动渲染新对象的列表视图、详情视图、创建表单。整个过程不需要手动写 SQL，也不需要在 UI 里点击。

跟 Salesforce 的 Metadata API 部署对比：Salesforce DX 的 `sf project deploy start` 也会把 XML 定义推到 org，但部署失败时的回滚依赖 Changeset 或 Git 历史，对象之间的依赖关系（lookup field、record type）需要手动管理顺序。Twenty 的 `app:publish` 在 server 端处理依赖顺序，因为对象定义是 TypeScript 代码，类型系统在编译阶段就能发现字段引用错误。

## 工作流自动化与 AI 能力

Twenty 的构建块有四个：objects（对象）、views（视图）、workflows（工作流）、agents（代理）。前三个对应 Salesforce 的 Custom Object、Page Layout、Flow；agents 是 Twenty 在 2026 年加进来的层，对应 AI 驱动的自动化任务。

工作流部分目前支持基于事件触发的自动化：对象记录创建、更新、字段变更时触发动作（发邮件、调 webhook、更新关联记录）。跟 Salesforce Flow 相比，Twenty 的工作流还在早期，缺少 Flow Builder 那种可视化拖拽编排器，复杂分支逻辑需要写代码而不是配置。

AI 能力分几块。仓库根目录有 `.mcp.json` 文件，说明 Twenty 集成了 MCP（Model Context Protocol），AI agent 可以通过 MCP server 读取 CRM 数据。提交历史里有 "Fix AI chat re-renders" 的记录，前端有内建的 AI 对话界面。agents 构建块允许在工作流里调用 AI 模型处理自然语言任务，比如自动给 lead 打分、从邮件提取联系信息填充字段。这些能力跟 Salesforce Einstein 的定位类似，但 Twenty 的 AI 调用是代码可控的——agent 的 prompt、模型选择、触发条件都写在 app 代码里，而不是 Einstein 那种黑盒打分。

## 跟 Odoo 和 ERPNext 的定位差异

Odoo 和 ERPNext 是 ERP 套件，CRM 是其中一个模块，跟进销存、财务、库存、HR 共享同一套对象模型。如果业务需要从 lead 到 invoice 到 inventory 的全链路，Odoo 和 ERPNext 的覆盖面更广。Twenty 只做 CRM，不做 ERP，但 CRM 部分的深度和代码可控性比 Odoo 的 CRM 模块高。

具体差异：Odoo 的自定义字段通过 Python 代码或 UI 添加，字段定义存在 `ir.model.fields` 表里，版本控制需要额外的模块打包流程。Twenty 的字段定义是 TypeScript 代码，天然在 Git 里。Odoo 的工作流用 XML 文件定义，Twenty 用 TypeScript。Odoo 的 AI 能力依赖第三方模块（如 OCA 的 AI 模块），Twenty 内建了 MCP 集成和 agents 构建块。

选型判断：如果团队需要 CRM + 进销存 + 财务一体化，选 Odoo 或 ERPNext；如果仅用 CRM 且有工程团队维护代码，Twenty 的代码优先路径更直接。

## 部署方式

Twenty 提供三种部署路径：

```bash
# 路径 1：Cloud（最快，无需管理基础设施）
# 注册 twenty.com，1 分钟内拉起工作区

# 路径 2：Docker Compose 自托管
git clone https://github.com/twentyhq/twenty.git
cd twenty
docker-compose up

# 路径 3：本地开发
git clone https://github.com/twentyhq/twenty.git
cd twenty
cp ./packages/twenty-front/.env.example ./packages/twenty-front/.env
cp ./packages/twenty-server/.env.example ./packages/twenty-server/.env
yarn
npx nx database:reset twenty-server
npx nx start
```

Docker Compose 部署会拉起 PostgreSQL、Redis、server、worker、front 五个容器，适合自托管场景。本地开发需要手动安装 PostgreSQL 16 和 Redis，通过 `npx nx start` 同时启动 server、worker、front 三个进程。多工作区模式（multi-workspace）通过 `IS_MULTIWORKSPACE_ENABLED=true` 环境变量开启，支持子域名隔离。

许可证方面，Twenty 在 2024 年 10 月的提交里加入了 SSO 支持（OIDC 和 SAML），企业版功能（SSO、审计日志、高级权限）走商业许可，核心 CRM 功能走开源许可。自托管时需要确认哪些功能在开源许可范围内。

## 采用建议

先判断团队类型再决定是否采用。

工程团队主导的 SaaS 或 B2B 初创公司，CRM 数据模型跟产品强相关，需要频繁调整对象和字段，且团队有 TypeScript 经验——Twenty 的代码优先路径能省掉 Salesforce 的许可证成本和 Metadata API 部署复杂度。从 `npx create-twenty-app` 开始，先定义核心对象（Company、Person、Deal），跑通 lead 到 deal 的基本流程，再逐步加工作流和 agents。

非工程团队主导的销售组织，依赖 UI 配置和拖拽式工作流编辑器，对代码 review 流程不熟悉——Twenty 目前的工作流能力还在早期，缺少可视化编排器，这类团队用 Salesforce 或 HubSpot 的成熟 UI 更直接。可以等 Twenty 的工作流编辑器和 UI 配置能力更完整后再评估。

从 Odoo 或 ERPNext 迁移的团队，如果只用 CRM 模块且不依赖 ERP 链路，Twenty 是更聚焦的替代；如果 CRM 跟进销存、财务有数据关联，迁移成本会高于留在 Odoo 生态内。

边界判断：Twenty 目前不适合需要复杂权限矩阵（field-level security、record-level sharing rules）的大型组织。Salesforce 在这一层有成熟的 Role Hierarchy、Sharing Rules、Field-Level Security 体系，Twenty 的权限模型还在迭代。等 v3.x 的权限层稳定后再评估企业级场景。

GitHub: https://github.com/twentyhq/twenty
