---
title: "Twenty：开源CRM的完整技术指南与最佳实践"
date: 2026-03-29T16:14:00+08:00
slug: "twenty-open-source-crm-guide"
aliases:
  - /posts/tech/twenty-open-source-crm-guide/
description: "Twenty 是 42.6k Stars 的开源 CRM 平台，Salesforce 的现代替代品。本文全面介绍其功能架构、技术栈、权限系统、工作流、API 集成和最佳实践。"
draft: false
categories: ["技术笔记"]
tags: ["CRM", "开源", "TypeScript", "NestJS", "GraphQL"]
---

# Twenty：开源CRM的完整技术指南与最佳实践

## 一、项目概览

**Twenty** 是一个现代化的开源 CRM（客户关系管理）平台，旨在成为 Salesforce 的开源替代品，作为开源 CRM 领域的后起之秀，Twenty 凭借其现代化的技术栈、清晰的架构设计和完善的功能生态，正在吸引越来越多的开发者和企业的关注。

该项目在 GitHub 上获得了 **42.6k Stars** 和 **5.6k Forks**，拥有 **604 位贡献者**，证明了其在开源社区的强大影响力。

### 1.1 为什么需要 Twenty

Twenty 的诞生源于三个核心洞察：

**1. CRMs 价格高昂且存在供应商锁定**

传统 CRM 巨头如 Salesforce、HubSpot 等不仅价格昂贵（Salesforce Enterprise 版每用户每月 $150 起），而且一旦数据被锁定，迁移成本极高。Twenty 提供了完全开源、自托管的解决方案，数据完全由企业自己掌控。

**2. 用户体验需要革新**

许多传统 CRM 的界面停留在十年前，已经无法满足现代用户对简洁、直观、高效的期望。Twenty 借鉴了 Notion、Airtable、Linear 等现代工具的 UX 设计理念，打造了一个清新、现代的界面。

**3. 开放源代码与社区协作**

Twenty 的开发者相信开源的力量。目前已有数百名开发者参与到 Twenty 的建设中来，随着插件系统的完善，一个完整的生态系统将会在此基础上蓬勃发展。

### 1.2 技术统计

| 指标 | 数值 |
|------|------|
| **Stars** | 42.6k |
| **Forks** | 5.6k |
| **贡献者** | 604 位 |
| **Commits** | 11,073 次 |
| **最新版本** | v1.19.0 (2026-03-23) |
| **技术栈** | TypeScript 80.1% + MDX 19.0% |
| **许可证** | GPL |

## 二、核心功能详解

### 2.1 多维度数据视图

Twenty 提供了丰富的数据展示方式，满足不同工作场景的需求：

**表格视图（Table View）**

表格视图是处理大量数据的最佳方式。用户可以：
- 调整列的顺序和宽度
- 隐藏/显示特定列
- 冻结首列方便滚动时始终可见
- 支持千行级别的数据流畅滚动

**看板视图（Kanban View）**

看板视图非常适合销售流程管理：
- 按销售阶段分组（如：潜在客户 → 初次联系 → 方案提交 → 成交）
- 拖拽卡片即可更新状态
- 支持按负责人、创建时间等维度排序
- 可视化销售漏斗

**分组视图（Group By）**

灵活的分组功能让数据分析更便捷：
- 按任何字段进行分组（如按城市、按行业、按负责人）
- 支持多级分组嵌套
- 自动计算每组的汇总数据

**筛选与排序**

强大的筛选功能：
- 支持 AND/OR 逻辑组合
- 预设常用筛选条件保存为视图
- 支持跨对象联合筛选
- 实时预览筛选结果

### 2.2 自定义对象与字段系统

Twenty 的核心优势之一是其灵活的数据建模能力。

**标准对象**

开箱即用的对象包括：

| 对象 | 说明 | 核心字段 |
|------|------|----------|
| **Company** | 公司/客户组织 | 名称，行业、规模、地址 |
| **Contact** | 联系人 | 姓名、邮箱、电话、职位、公司关联 |
| **Deal** | 交易/机会 | 金额、阶段、预期成交日期、关联联系人 |
| **Task** | 任务 | 标题、截止日期、优先级、状态 |
| **Event** | 日历事件 | 时间、地点、参与者 |
| **Note** | 备注 | 内容、关联对象 |

**自定义字段类型**

Twenty 支持丰富的字段类型：

| 字段类型 | 适用场景 | 示例 |
|----------|----------|------|
| **文本（Text）** | 短文本/长文本 | 产品描述、备注 |
| **数字（Number）** | 整数或浮点数 | 交易金额、人口数量 |
| **货币（Currency）** | 带货币单位的金额 | 预算、报价 |
| **日期/日期时间** | 时间记录 | 生日、会议时间 |
| **关系（Relation）** | 关联其他对象 | 联系人所属公司 |
| **枚举（Select）** | 单选下拉 | 状态、类型 |
| **多选（Multi-select）** | 多选下拉 | 标签、技能 |
| **布尔（Boolean）** | 是/否开关 | 是否VIP、是否已审核 |
| **电话（Phone）** | 电话号码 | 办公电话、mobile |
| **邮箱（Email）** | 电子邮件地址 | 工作邮箱、个人邮箱 |
| **URL** | 网页链接 | 公司官网、社交媒体 |
| **文件（File）** | 附件上传 | 合同扫描件、产品手册 |

**关系字段与数据联动**

关系字段是 Twenty 数据建模的精髓：

```
Contact（联系人）
    │
    ├── company: Relation → Company（所属公司）
    ├── deals: Relation[] → Deal[]（参与的交易）
    ├── tasks: Relation[] → Task[]（待办任务）
    └── notes: Relation[] → Note[]（相关备注）
```

通过关系字段，可以实现：
- 点击联系人自动显示其所属公司的所有信息
- 查看交易时列出所有相关的联系人
- 在公司视图下查看所有关联任务和备注

### 2.3 权限管理系统

Twenty 实现了细粒度的基于角色的访问控制（RBAC，Role-Based Access Control）。

**权限层级架构**

```
Workspace（工作空间）
    │
    └── 角色（Role）
            │
            ├── 数据权限（Data Permissions）
            │       ├── 对象级：可读/可写/不可见
            │       └── 字段级：可读/可写/不可见
            │
            └── 功能权限（Feature Permissions）
                    ├── API 访问
                    ├── 导入/导出
                    └── 管理功能
```

**内置角色**

| 角色 | 说明 | 典型用户 |
|------|------|----------|
| **Admin** | 完全控制 | 系统管理员 |
| **Editor** | 可编辑所有数据 | 销售经理、运营人员 |
| **Viewer** | 只读访问 | 财务人员、外部门诊 |
| **Custom** | 自定义角色 | 根据企业需求创建 |

### 2.4 工作流自动化

Twenty 的工作流引擎支持基于触发器和动作的自动化流程。

**触发器类型（Triggers）**

| 触发器 | 说明 | 条件示例 |
|--------|------|----------|
| **record.created** | 记录创建时 | 新线索创建 |
| **record.updated** | 记录更新时 | 交易阶段变更 |
| **record.deleted** | 记录删除时 | 联系人被删除 |
| **field.value_changed** | 字段值变更 | 任务优先级变为"高" |
| **date.reached** | 指定日期到达 | 会议开始前1小时 |
| **api.called** | API 被调用 | 收到 webhook |

**动作类型（Actions）**

| 动作 | 说明 |
|------|------|
| **update_record** | 更新记录字段 |
| **create_record** | 创建新记录 |
| **delete_record** | 删除记录 |
| **send_email** | 发送邮件 |
| **send_notification** | 发送站内通知 |
| **http_request** | 发送 HTTP 请求 |
| **webhook** | 触发 webhook |
| **assign_to** | 变更负责人 |

### 2.5 电子邮件与日历集成

Twenty 原生支持与电子邮件和日历系统的集成。

**邮件集成**

- **发送追踪**：记录每封邮件的发送、打开、点击情况
- **邮件模板**：预设邮件模板，支持变量替换
- **批量发送**：支持向多个联系人发送个性化邮件
- **Gmail/Outlook 同步**：双向同步邮件往来

**日历集成**

- **事件同步**：与 Google Calendar、Outlook Calendar 双向同步
- **会议安排**：直接在 Twenty 中安排会议并发送邀请
- **忙碌检测**：查看联系人的日历空闲情况
- **会议回顾**：自动生成会议纪要并关联到相关记录

## 三、技术架构深度解析

### 3.1 Monorepo 架构

Twenty 采用 **Nx Monorepo** 架构，将所有功能模块组织在一个代码仓库中。

**Monorepo 的优势**

1. **代码共享**：所有包共享类型定义和工具函数
2. **统一构建**：一次安装、一次构建、一次测试
3. **增量构建**：Nx 的affected 命令只会构建受影响的包
4. **依赖管理**：统一的依赖版本，避免版本冲突
5. **跨项目重构**：修改共享代码时自动更新所有依赖方

**包结构详解**

| 包名 | 说明 | 依赖关系 |
|------|------|----------|
| **twenty-front** | React 前端应用 | twenty-ui, twenty-sdk |
| **twenty-server** | NestJS 后端服务 | twenty-shared |
| **twenty-ui** | React UI 组件库 | twenty-shared |
| **twenty-sdk** | SDK 用于前端与后端通信 | twenty-shared |
| **twenty-client-sdk** | 客户端 SDK | twenty-sdk |
| **twenty-shared** | 共享工具和类型 | - |
| **twenty-utils** | 通用工具函数 | - |
| **twenty-cli** | 命令行工具 | twenty-server, twenty-shared |
| **twenty-docker** | Docker 部署配置 | - |
| **twenty-docs** | 项目文档 | - |
| **twenty-emails** | 邮件模板 | - |
| **twenty-zapier** | Zapier 集成 | twenty-sdk |
| **create-twenty-app** | 项目脚手架 | - |
| **twenty-e2e-testing** | E2E 测试框架 | twenty-front, twenty-server |

### 3.2 前端架构

**技术栈**

- **React 18**：核心 UI 框架
- **Jotai**：轻量级状态管理，基于原子化设计
- **Linaria**：CSS-in-JS 方案，零运行时开销
- **Apollo Client**：GraphQL 客户端（正在迁移到 v4）
- **Lingui**：国际化方案

**状态管理（Jotai）**

Twenty 使用 Jotai 进行状态管理，其原子化设计非常适合 CRM 的复杂表单场景：

```typescript
// 定义原子状态
const currentCompanyState = atom<Company | null>(null);
const companyContactsState = atom<Contact[]>([]);
const isLoadingState = atom<boolean>(false);

// 派生状态
const companyWithContactsState = atom((get) => {
  const company = get(currentCompanyState);
  const contacts = get(companyContactsState);
  return company ? { ...company, contacts } : null;
});

// 表单专用原子
const companyFormState = atomFamily((companyId: string) =>
  atom<CompanyFormData>({ /* 默认值 */ })
);
```

**组件架构**

Twenty 的组件采用原子设计（Atomic Design）：

```
atoms/          # 基础原子组件
  ├── Button
  ├── Input
  ├── Select
  └── Badge

molecules/      # 分子组件
  ├── FormField
  ├── DataTableCell
  └── FilterPill

organisms/     # 有机组件
  ├── CompanyForm
  ├── ContactList
  └── DealBoard

templates/      # 页面模板
  ├── CompanyDetailTemplate
  └── SettingsTemplate
```

### 3.3 后端架构

**技术栈**

- **NestJS**：渐进式 Node.js 框架
- **Prisma**：Node.js ORM
- **PostgreSQL**：主数据库
- **Redis**：缓存和消息队列
- **BullMQ**：基于 Redis 的任务队列
- **GraphQL**：API 层（主推）/ REST（兼容）

**模块化设计**

```
twenty-server/
├── src/
│   ├── core/
│   │   ├── company/         # 公司模块
│   │   │   ├── company.entity.ts
│   │   │   ├── company.service.ts
│   │   │   ├── company.resolver.ts  # GraphQL
│   │   │   └── company.controller.ts # REST
│   │   │
│   │   ├── contact/        # 联系人模块
│   │   ├── deal/           # 交易模块
│   │   └── ...
│   │
│   ├── workspace/          # 工作空间模块
│   │   ├── workspace.entity.ts
│   │   ├── workspace.service.ts
│   │   └── workspace.resolver.ts
│   │
│   ├── auth/               # 认证授权
│   │   ├── jwt.strategy.ts
│   │   ├── gql-auth.guard.ts
│   │   └── rbac.decorator.ts
│   │
│   └── queue/              # 任务队列
│       ├── email.queue.ts
│       └── webhook.queue.ts
```

**GraphQL API 设计**

Twenty 主要使用 GraphQL 作为 API 协议，提供了灵活的数据查询能力。

**查询示例：获取公司列表**

```graphql
query GetCompanies($first: Int!, $after: String) {
  companies(first: $first, after: $after) {
    edges {
      node {
        id
        name
        domain
        industry
        employees
        createdAt
        contacts {
          edges {
            node {
              id
              name
              email
            }
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

**变更示例：创建公司**

```graphql
mutation CreateCompany($input: CreateCompanyInput!) {
  createCompany(input: $input) {
    id
    name
    domain
    industry
  }
}
```

### 3.4 数据库设计

**核心表结构**

```
┌─────────────────┐       ┌─────────────────┐
│    Company      │       │     Contact     │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │◄──────│ companyId (FK) │
│ name            │       │ id (PK)         │
│ domain          │       │ name            │
│ industry        │       │ email           │
│ employees       │       │ phone           │
│ createdAt       │       │ jobTitle        │
│ workspaceId(FK)│       │ createdAt       │
└─────────────────┘       └─────────────────┘
        │
        │ 1:N
        ▼
┌─────────────────┐       ┌─────────────────┐
│      Deal      │       │     Task        │
├─────────────────┤       ├─────────────────┤
│ id (PK)        │       │ id (PK)         │
│ companyId (FK) │       │ dealId (FK)     │
│ contactId (FK) │       │ title           │
│ name            │       │ dueDate         │
│ amount          │       │ status          │
│ stage           │       │ priority        │
│ probability     │       │ assigneeId (FK) │
│ expectedCloseAt│       │ createdAt       │
└─────────────────┘       └─────────────────┘
```

### 3.5 认证与授权

Twenty 支持多种认证方式：

**JWT 认证**

```typescript
// JWT Payload 结构
interface JWTPayload {
  sub: string;           // 用户 ID
  workspaceId: string;   // 工作空间 ID
  role: Role;            // 用户角色
  type: 'access' | 'refresh';
}

// 生成 Access Token
const accessToken = jwt.sign(
  {
    sub: user.id,
    workspaceId: workspace.id,
    role: user.role,
    type: 'access',
  },
  process.env.JWT_SECRET,
  { expiresIn: '15m' }
);

// 生成 Refresh Token
const refreshToken = jwt.sign(
  { sub: user.id, type: 'refresh' },
  process.env.JWT_REFRESH_SECRET,
  { expiresIn: '7d' }
);
```

**SSO 支持**

Twenty 支持 OIDC 和 SAML 协议实现企业单点登录：

```yaml
# twenty-server 环境配置
AUTH_SSO_ENABLED: true
AUTH_SSO_PROVIDER: "oidc"  # 或 "saml"
AUTH_SSO_CLIENT_ID: "${OIDC_CLIENT_ID}"
AUTH_SSO_CLIENT_SECRET: "${OIDC_CLIENT_SECRET}"
AUTH_SSO_ISSUER: "https://your-idp.example.com"
AUTH_SSO_CALLBACK_URL: "https://your-twenty.com/auth/callback"
```

## 四、快速开始

### 4.1 本地开发环境

**前置要求**

| 组件 | 版本要求 | 说明 |
|------|----------|------|
| Node.js | 24+ | 建议使用 nvm 管理 |
| PostgreSQL | 14+ | 数据库 |
| Redis | 6+ | 缓存和队列 |
| Git | 最新版 | 版本控制 |
| Docker | 20+ | 仅部署时需要 |

**克隆与安装**

```bash
# 克隆仓库（使用 shallow clone 加快速度）
git clone --depth 1 https://github.com/twentyhq/twenty.git
cd twenty

# 使用 nvm 切换 Node 版本
nvm use

# 安装依赖
yarn install
```

**环境配置**

```bash
# 复制环境变量模板
cp twenty-server/.env.example twenty-server/.env
cp twenty-front/.env.example twenty-front/.env

# 编辑服务器环境变量
vim twenty-server/.env

# 关键配置项：
# - POSTGRES_HOST=localhost
# - POSTGRES_USER=postgres
# - POSTGRES_PASSWORD=your_password
# - POSTGRES_DB=twenty
# - REDIS_HOST=localhost
# - FRONTEND_URL=http://localhost:3000
```

**启动开发服务器**

```bash
# 方式1：使用 Docker 启动数据库和 Redis
docker-compose up -d postgres redis

# 方式2：本地已有 PostgreSQL 和 Redis，直接启动
# 初始化数据库
yarn database:init

# 启动开发服务器
yarn dev
```

访问 http://localhost:3000 即可看到 Twenty 应用。

### 4.2 Docker 部署

**使用 Docker Compose 一键部署**

```bash
# 克隆仓库
git clone https://github.com/twentyhq/twenty.git
cd twenty

# 复制并编辑环境变量
cp twenty-docker/.env.example twenty-docker/.env
vim twenty-docker/.env

# 启动所有服务
cd twenty-docker
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f twenty-server
```

### 4.3 云部署选项

**Railway 部署**

Railway 提供了最简单的云端部署方式：

```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录
railway login

# 初始化项目
railway init

# 添加 PostgreSQL
railway add

# 部署
railway up
```

**Render 部署**

Render 支持一键部署：

1. Fork Twenty 仓库
2. 在 Render 创建新的 Web Service
3. 连接 GitHub 仓库
4. 设置构建命令：`yarn build`
5. 设置启动命令：`yarn start`
6. 添加 PostgreSQL 和 Redis 插件

## 五、API 与集成开发

### 5.1 GraphQL API 使用

**安装 Apollo Client**

```bash
npm install @apollo/client graphql
```

**配置客户端**

```typescript
// apollo-client.ts
import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client';

const httpLink = createHttpLink({
  uri: 'http://localhost:3001/graphql',
  headers: {
    Authorization: `Bearer ${getAccessToken()}`,
  },
});

export const apolloClient = new ApolloClient({
  link: httpLink,
  cache: new InMemoryCache(),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
    },
  },
});
```

### 5.2 Webhook 开发

**Webhook 配置**

```typescript
// 创建 Webhook
const webhook = await api.webhooks.create({
  name: 'My CRM Webhook',
  url: 'https://my-app.example.com/webhook',
  events: [
    'company.created',
    'company.updated',
    'deal.stage_changed',
    'contact.created',
  ],
  secret: 'my-webhook-secret',
});
```

**处理 Webhook 事件**

```typescript
// webhook-handler.ts
import crypto from 'crypto';

function verifySignature(payload: string, signature: string, secret: string): boolean {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}

app.post('/webhook', (req, res) => {
  const signature = req.headers['x-twenty-signature'] as string;
  const isValid = verifySignature(
    JSON.stringify(req.body),
    signature,
    process.env.WEBHOOK_SECRET
  );

  if (!isValid) {
    return res.status(401).send('Invalid signature');
  }

  const { event, data } = req.body;

  switch (event) {
    case 'company.created':
      handleNewCompany(data);
      break;
    case 'deal.stage_changed':
      handleDealStageChange(data);
      break;
  }

  res.status(200).send('OK');
});
```

### 5.3 SDK 使用

**安装 SDK**

```bash
npm install twenty-sdk
```

**SDK 客户端初始化**

```typescript
import { TwentyClient } from 'twenty-sdk';

const client = new TwentyClient({
  baseUrl: 'https://your-twenty-instance.com',
  apiKey: 'your-api-key',
});
```

**使用 SDK 操作数据**

```typescript
// 创建公司
const company = await client.companies.create({
  name: 'Acme Corp',
  domain: 'acme.com',
  industry: 'Technology',
});

// 创建联系人并关联公司
const contact = await client.contacts.create({
  name: 'John Doe',
  email: 'john@acme.com',
  companyId: company.id,
  jobTitle: 'CTO',
});

// 创建交易
const deal = await client.deals.create({
  name: 'Enterprise License',
  amount: 50000,
  stage: 'proposal',
  companyId: company.id,
  contactId: contact.id,
  expectedCloseDate: '2026-06-30',
});

// 查询数据
const companies = await client.companies.findMany({
  filter: { industry: { equals: 'Technology' } },
  orderBy: { createdAt: 'desc' },
  limit: 20,
});
```

## 六，最佳实践

### 6.1 数据建模最佳实践

**1. 从业务需求出发设计对象**

在创建自定义对象前，先回答以下问题：
- 这个实体是什么？（如：项目、产品、服务合同）
- 它与现有对象是什么关系？（公司-联系人-交易已经很成熟）
- 需要跟踪哪些属性？
- 有哪些工作流需要触发？

**2. 避免过度设计**

CRM 的数据模型应该随着业务发展逐步演进。初期可以：
- 使用标准对象和字段
- 用标签（tags）代替复杂的分类
- 用备注（notes）记录非结构化信息

**3. 合理使用关系字段**

推荐的关联结构：

```
Company (1) ─── (N) Contact (1) ─── (N) Deal (N)
                    │
                    └── (N) Task
```

### 6.2 权限配置最佳实践

**1. 遵循最小权限原则**

每个角色只应获得完成其工作所需的最小权限：

```typescript
// 销售代表角色 - 数据权限
const salesRepPermissions = {
  company: {
    read: 'own',     // 只能看自己的客户
    write: 'own',    // 只能编辑自己的客户
    delete: 'none', // 禁止删除
  },
  contact: {
    read: 'own',
    write: 'own',
    delete: 'none',
  },
  deal: {
    read: 'all',     // 需要看所有人的交易便于协作
    write: 'own',   // 只能编辑自己的交易
    delete: 'none',  // 禁止删除
  },
};
```

**2. 定期审计权限设置**

建议每季度进行一次权限审计，确保配置与业务需求匹配。

### 6.3 工作流设计最佳实践

**1. 保持工作流简单**

- 每个工作流完成单一任务
- 使用清晰的工作流名称
- 添加注释说明业务逻辑

**2. 避免无限循环**

```typescript
// ❌ 错误：可能导致状态更新触发自身
{
  trigger: { type: 'record.updated', field: 'status' },
  actions: [
    { type: 'update_record', field: 'lastUpdated', value: 'now' }
  ]
}

// ✅ 正确：使用条件防止循环
{
  trigger: { type: 'record.updated', field: 'status' },
  conditions: [
    { field: 'status', operator: 'equals', value: 'closed' }
  ],
  actions: [
    { type: 'send_notification', message: '交易已成交！' }
  ]
}
```

## 七、与其他 CRM 的对比

### 7.1 功能对比

| 功能 | Twenty | Salesforce | HubSpot | Pipedrive |
|------|--------|-----------|---------|------------|
| **开源** | ✅ GPL | ❌ 闭源 | ❌ 闭源 | ❌ 闭源 |
| **自托管** | ✅ 完全支持 | ❌ 仅 SaaS | 部分支持 | ❌ 仅 SaaS |
| **自定义对象** | ✅ | ✅ | ❌ | ❌ |
| **GraphQL API** | ✅ | ❌ | ❌ | ❌ |
| **工作流自动化** | ✅ | ✅ | ✅ | ✅ |
| **权限系统** | ✅ 细粒度 RBAC | ✅ | 基础 | 基础 |
| **多语言** | ✅ | ✅ | ✅ | ✅ |
| **UI 设计** | 现代简洁 | 复杂 | 中等 | 现代 |
| **价格** | 免费开源 | $150+/用户/月 | $50+/用户/月 | $12+/用户/月 |

### 7.2 技术架构对比

| 维度 | Twenty | Salesforce | HubSpot |
|------|--------|-----------|---------|
| **前端框架** | React + Jotai | Lightning Web Components | React |
| **后端框架** | NestJS | 自有 Java 框架 | Node.js |
| **数据库** | PostgreSQL | Oracle +自家数据库 | PostgreSQL |
| **API 协议** | GraphQL + REST | REST | REST + GraphQL（部分） |
| **部署方式** | 自托管/Kubernetes | 仅 SaaS | SaaS/自托管 |
| **扩展机制** | 插件系统（开发中） | AppExchange | Apps Marketplace |

## 八、常见问题

### 8.1 部署相关

**Q: Docker 部署时数据库连接失败？**

A: 检查以下几点：
1. PostgreSQL 容器是否正常运行：`docker-compose ps postgres`
2. 环境变量中的 `POSTGRES_HOST` 是否正确（如果是 docker-compose 网络内，应该是服务名 `postgres`）
3. 数据库是否创建：`docker-compose exec postgres psql -U postgres -l`
4. 防火墙是否允许容器间通信

**Q: 如何升级 Twenty 到新版本？**

A: 使用 Docker Compose 升级：

```bash
cd twenty-docker
docker-compose pull
docker-compose down
docker-compose up -d
```

### 8.2 开发相关

**Q: 如何调试 GraphQL API？**

A: Twenty 服务器内置了 GraphQL Playground：
1. 访问 `http://localhost:3001/graphql`
2. 登录后即可使用 Playground
3. 右下角可以查看当前用户的 token

**Q: 如何添加新的 API 端点？**

A: 在 twenty-server 中创建新的模块：

```bash
# 1. 创建模块目录
mkdir -p src/core/my-custom-module

# 2. 创建文件
touch src/core/my-custom-module/my-custom-module.entity.ts
touch src/core/my-custom-module/my-custom-module.service.ts
touch src/core/my-custom-module/my-custom-module.resolver.ts

# 3. 在 core.module.ts 中注册
@Module({
  imports: [
    MyCustomModuleModule,
  ],
  ...
})
export class CoreModule {}
```

### 8.3 数据相关

**Q: 如何迁移现有数据到 Twenty？**

A: 提供两种方式：

**方式1：CSV 导入**

```bash
# 导出 CSV 模板
yarn workspace twenty-server database:export-template --entity Company

# 填充数据后导入
yarn workspace twenty-server database:import --entity Company --file ./companies.csv
```

**方式2：API 批量写入**

```typescript
import { TwentyClient } from 'twenty-sdk';

const client = new TwentyClient({
  baseUrl: 'https://your-twenty.com',
  apiKey: 'your-api-key',
});

// 批量导入函数
async function importContacts(contacts: ContactData[]) {
  const batchSize = 50;
  for (let i = 0; i < contacts.length; i += batchSize) {
    const batch = contacts.slice(i, i + batchSize);
    await Promise.all(
      batch.map(contact => client.contacts.create(contact))
    );
    console.log(`Imported ${Math.min(i + batchSize, contacts.length)}/${contacts.length}`);
  }
}
```

## 九、总结

Twenty 代表了开源 CRM 的新势力：

- ✅ **完全开源**：代码透明，无供应商锁定，采用 GPL 许可证
- ✅ **功能完整**：覆盖 CRM 核心需求（公司、联系人、交易、任务、日历），并持续快速迭代
- ✅ **技术现代**：TypeScript 全栈，架构清晰，React + NestJS + PostgreSQL
- ✅ **社区活跃**：42.6k Stars，大量开发者参与贡献，604 位贡献者
- ✅ **可自托管**：数据完全自主掌控，支持 Docker 和 Kubernetes 部署
- ✅ **API 优先**：GraphQL + REST API，SDK 完善，易于集成
- ✅ **插件生态**：正在开发插件系统，未来将支持扩展

**适用人群**：

- ✅ 开发者和技术团队：喜欢自托管、控制数据的团队
- ✅ 中小企业：预算有限，无法承担 Salesforce 费用的
- ✅ 重视开源的团队：希望参与贡献源码
- ✅ 需要深度定制的企业：标准 CRM 无法满足需求的

无论你是独立开发者、中小企业还是大型组织，Twenty 都值得一试。

---

**相关资源：**

- 🌐 官网：https://twenty.com
- 📚 文档：https://docs.twenty.com
- 💬 Discord：https://discord.gg/cx5n4Jzs57
- 🐙 GitHub：https://github.com/twentyhq/twenty
- 🗺️ 路线图：https://github.com/orgs/twentyhq/projects/1
- 🎨 Figma：https://www.figma.com/file/xt8O9mFeLl46C5InWwoMrN/Twenty
