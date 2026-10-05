+++
github_repo = "medusajs/medusa"
source_key = "gh:medusajs/medusa"
date = '2026-05-17T20:25:00+08:00'
draft = false
title = 'MedusaJS：开源 Headless 商务平台'
slug = 'medusajs-open-source-ecommerce-platform-guide'
description = 'Medusa 是基于 Node.js/TypeScript 的开源商务平台：17 个核心商务模块加一套定制框架，模块隔离架构，工作流编排，适合 B2B、多渠道市场等需要深度定制的电商场景。'
categories = ['技术笔记']
tags = ['开源', 'Node.js', 'TypeScript']
+++

## MedusaJS 解决的是什么

选电商后端时，大多数团队真正纠结的不是"能不能跑起来"，而是"以后改不动了怎么办"。SaaS 平台把后台逻辑锁在订阅费里，自研又得从零搭商品、订单、支付、物流。

[Medusa](https://github.com/medusajs/medusa) 走第三条路：核心商务逻辑全部开源，同时把平台本身做成一个可定制的框架。官方的定位是 "Building blocks for digital commerce"——B2B 批发、DTC 品牌店、多商户市场、经销平台、门店 POS 都能在这套积木上搭。

截至 2026 年 10 月，这个项目的基本盘：

- **GitHub 36.5k stars、5.3k forks**，当前版本 v2.21，2024 年底从 v1 完成重写并发布 v2。
- **开源协议是 open-core**：核心功能 MIT，仓库中标注为 Enterprise Edition 的部分（RBAC 权限体系等）需要与 MedusaJS, Inc. 签商业协议。
- **Discord 社区 14,000+ 人**，核心团队在 GitHub Discussions 跟进 issue 和路线图。
- 官方专门维护了一套 [agent skills](https://github.com/medusajs/medusa-agent-skills)，可以直接在 Claude Code 等编码智能体里装插件，让 AI 按 Medusa 的规范写定制功能。

技术形态：**Node.js + TypeScript** 的后端服务，外加一个内置的 Vite 管理后台。后端暴露 REST API，前端随意——官方提供 Next.js Starter，用 Vue、小程序或任何框架也行。数据库只支持 PostgreSQL，开发环境也得装。

一个容易误判的点：Medusa 不是"电商建站工具"。装完它你得到的是一个带完整商务模块的后端和一个后台界面，商店本身（前台页面）要自己开发。如果你的需求是"今天就要开店卖货"，Shopify 更合适；如果你的需求是"业务模型特殊，要长期改后端逻辑"，Medusa 才是对手的场景。

下面这张图概括 Medusa 应用的三层结构和周边：

```
┌──────────────────────────────────────────────────────────────┐
│                     前端（任意框架）                           │
│      Next.js Starter  /  自研 SPA  /  小程序  /  POS 终端     │
└──────────────────────────┬───────────────────────────────────┘
                           │  REST API（Store / Admin / Auth）
┌──────────────────────────▼───────────────────────────────────┐
│                      Medusa 应用（HTTP 层）                    │
│   自定义 API routes · 中间件 · 文件校验（Zod）· CORS/认证      │
├──────────────────────────────────────────────────────────────┤
│                    Workflows 工作流引擎                        │
│   多步骤编排 · 补偿回滚 · 重试 · 长事务 · 执行历史持久化        │
├──────────────────────────────────────────────────────────────┤
│                  模块层（每个模块独立隔离）                     │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐ │
│  │ Product│ │  Cart  │ │ Order  │ │Payment │ │ Inventory  │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────────┘ │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐ │
│  │Pricing │ │ Region │ │   Tax  │ │  Auth  │ │ Fulfillment│ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────────┘ │
│  模块间通过 Module Links + Query 关联，不直接引用内部实现       │
├──────────────────────────────────────────────────────────────┤
│  基础设施模块：Event Bus / Cache / File / Notification /       │
│  Locking / Workflow Engine（本地实现或 Redis、S3、SendGrid）   │
└──────────────────────────┬───────────────────────────────────┘
                           │  MikroORM
                 ┌─────────▼──────────┐
                 │    PostgreSQL      │
                 └────────────────────┘
```

先看一笔订单怎么穿过这套系统，再拆架构和扩展方式。正在做选型的话，可以直接跳到「与同类项目对比」和「采用决策」。

---

## 一次下单请求穿过系统

以一个标准 B2C 结算为例，客户端调用和 Medusa 内部的分工：

```
浏览商品
  → GET /store/products?q=shirt&fields=id,title,*variants
  → 请求头带 x-publishable-api-key，绑定到某个 Sales Channel
  → 返回商品与变体，价格按 Region/Currency 上下文计算

创建购物车
  → POST /store/carts（region_id 指定区域）
  → POST /store/carts/:id/line-items（variant_id + quantity）
  → POST /store/carts/:id/shipping-methods（选配送方式）
  → 每一步返回的 cart 对象都带小计、税费、运费等 totals

发起支付
  → POST /store/payment-collections（创建支付集合）
  → POST /store/payment-collections/:id/payment-sessions
    （provider_id 指定 Stripe 等支付提供商）
  → 前端用 Stripe Elements 持 client_secret 完成 3D Secure

完成订单
  → POST /store/carts/:id/complete
  → completeCartWorkflow 依次执行：校验 → 授权支付 → 购物车转订单
  → 校验失败或支付失败时工作流中断，已有步骤按补偿函数回滚

后续异步动作
  → Stripe 通过 POST /hooks/payment/stripe 推送支付状态
  → 事件总线发出 order.placed
  → src/subscribers 里的订阅者各自执行：发确认邮件、同步 ERP、通知物流
```

这里能看出 Medusa 的边界。它负责：商品与定价数据、购物车与订单状态、支付会话生命周期、工作流编排、事件分发。它不负责：前台 UI、邮件模板文案、物流商的具体对接——这些通过订阅者和自定义工作流接到你自己的系统上。

---

## 架构怎么拆的

### HTTP 层、工作流层、模块层

Medusa v2 把一个应用拆成三层，改动频率从高到低：

- **HTTP 层**是 `src/api` 下的路由文件。每个 `route.ts` 导出 `GET`/`POST` 等函数，接收 `MedusaRequest`、返回 `MedusaResponse`，请求体校验直接用 Zod。中间件在 `src/api/middlewares.ts` 里统一挂。
- **工作流层**是 `src/workflows` 下的编排代码。多步骤、需要重试或补偿的逻辑都写在这里，HTTP 层、订阅者、定时任务都通过它来执行业务，而不是直接调服务方法。
- **模块层**是业务能力的最小单元。官方 17 个核心商务模块（商品、购物车、订单、支付、库存、履约、区域、税率、促销、定价、客户、认证等）开箱即用；你自己的业务逻辑放在 `src/modules` 下，每个模块有独立的数据模型和服务。

三条层间规则值得记住：HTTP 层调用工作流而不直接改数据库；工作流的每个步骤有独立的重试和补偿；模块之间互相隔离——你拿不到另一个模块的内部实现，只能通过它的公开服务方法，跨模块的数据关联用 Module Links 声明。

模块隔离是 v2 重写后最重要的变化。v1 时代你可以继承 `ProductService` 覆盖任意方法，代价是核心代码和你的补丁搅在一起，升级极痛苦。v2 干脆禁止这样做：核心模块只暴露公开 API，扩展点收敛为工作流钩子、订阅者和 Module Links。升级不再靠人肉 diff，官方提供 codemod 工具自动迁移大部分破坏性改动。

### 配置文件

整个应用的配置集中在一个 `medusa-config.ts`：

```typescript
// apps/backend/medusa-config.ts
import { defineConfig } from "@medusajs/framework/utils"

module.exports = defineConfig({
  projectConfig: {
    databaseUrl: process.env.DATABASE_URL,
    http: {
      storeCors: "http://localhost:8000",
      adminCors: "http://localhost:5173",
      authCors: "http://localhost:8000",
      jwtSecret: process.env.JWT_SECRET || "supersecret",
      cookieSecret: process.env.COOKIE_SECRET || "supersecret",
      jwtExpiresIn: "1d",
    },
    redisUrl: process.env.REDIS_URL,
    workerMode: process.env.WORKER_MODE || "shared",
  },
  admin: {
    backendUrl: process.env.MEDUSA_BACKEND_URL,
    storefrontUrl: process.env.MEDUSA_STOREFRONT_URL,
  },
  modules: [
    {
      resolve: "@medusajs/medusa/payment",
      options: {
        providers: [
          {
            resolve: "@medusajs/medusa/payment-stripe",
            id: "stripe",
            options: {
              apiKey: process.env.STRIPE_API_KEY,
            },
          },
        ],
      },
    },
  ],
})
```

几个字段的行为值得单独说：

- `workerMode` 决定进程形态，`shared`（默认，请求和后台任务同进程）、`server`（只处理 API 请求）、`worker`（只处理订阅者、定时任务等后台任务）。生产环境建议拆成 server 和 worker 两个实例，部署一节细说。
- `redisUrl` 在 v2 里不再是必需品。开发环境不需要 Redis：事件总线、缓存、工作流引擎都有本地内存实现。Redis 只在三处生产场景用得上——多实例间共享 session、Redis 事件总线、Redis 工作流引擎。
- CORS 在 `http` 下分 `storeCors`、`adminCors`、`authCors` 三组配置，比 v1 的两个开关多了认证域。
- 管理后台默认挂在 `/app` 路径（`/admin`、`/store`、`/auth` 是 API 保留路径），不用单独部署，构建产物跟后端一起走。

### 认证与密钥

认证走独立的 Auth 模块，路由前缀 `/auth`，官方提供四种认证方式：邮箱密码（emailpass）、GitHub、Google、OIDC。同一套认证服务同时服务后台用户和顾客，路径里的角色段区分两者，比如 `/auth/user/emailpass` 是后台登录，`/auth/customer/emailpass` 是顾客登录，签发的是有效期一天（默认值）的 JWT。

API 密钥分两种：`pk_` 前缀的 Publishable Key 给前台用，每次 Store API 请求放在 `x-publishable-api-key` 头里，作用是把请求绑定到某个 Sales Channel；`sk_` 前缀的 Secret Key 给服务端集成用，可以调 Admin API。

---

## 核心模块

### 商品与定价（Product + Pricing）

商品模型围绕 Option 和 Variant 展开：一个商品声明 Size、Color 等选项，每个选项组合生成一个变体，变体持有自己的 SKU、尺寸重量和库存关联。用惯 Shopify 商品结构的团队对这个模型不陌生。

价格不在商品上，而在 Pricing 模块里。价格可以挂规则——按区域、按币种、按客户组出不同价格——同一件商品对不同市场展示不同价是配置出来的，不是复制商品做出来的。另一个和 v1 不同的细节：金额按主单位存储（10 美元存 `10`），不再存最小货币单位（`1000`），省掉一层换算。

```typescript
// 前端取数：fields 里用 * 展开关联
const { products } = await sdk.store.product.list({
  q: "shirt",
  limit: 20,
  fields: "id,title,*variants,*variants.calculated_price",
})
```

`*` 前缀展开关联是 v2 查询语法的关键，v1 的 `expand=` 参数已废弃。

### 购物车（Cart）

购物车模块管的是"这一单现在值多少钱"：每次改动都重新计算小计、折扣、税费、运费，返回完整的 totals。区域（Region）决定币种和可用的配送方式，促销（Promotion）模块的礼券和折扣码也挂在购物车上。

一个实用细节：所有购物车——包括没走到下单那一步的——都完整存在数据库里，弃单召回、催付这类功能直接查表就行，不需要自己另建存储。

### 订单（Order）

订单模块是全渠道的订单管理：创建、履行、部分发货、部分退款、退货换货、订单编辑都有对应的 API 和工作流。v2 为此提供了详细的变更记录（order version 机制），每次编辑生成新版本，审计时能看到一单的完整演进。

事件在订单生命周期里持续发出，`order.placed`、`order.canceled`、`order.fulfillment_created` 等，事件清单官方有单独的参考页。订阅者在 `src/subscribers` 里声明自己关心的事件：

```typescript
// src/subscribers/order-placed.ts
import { SubscriberArgs, SubscriberConfig } from "@medusajs/framework"

export default async function orderPlacedHandler({
  event,
  container,
}: SubscriberArgs<{ id: string }>) {
  const orderId = event.data.id
  const logger = container.resolve("logger")
  logger.info(`订单 ${orderId} 已创建，开始同步 ERP`)
}

export const config: SubscriberConfig = {
  event: "order.placed",
}
```

订阅者在 worker 进程里异步执行，失败不影响下单主流程；生产环境换上 Redis 事件总线后，多个实例可以分摊事件处理。

### 支付（Payment）

支付模块把"支付"抽象成三段：Payment Collection（一次结算的支付集合）→ Payment Session（向某个支付提供商发起的会话）→ Payment（授权后的支付记录）。授权和扣款天然分离，预授权、发货后扣款这类流程是模型内建的，不用绕。

官方维护的支付提供商只有一个——Stripe：

```typescript
// medusa-config.ts 的 modules 里注册
{
  resolve: "@medusajs/medusa/payment",
  options: {
    providers: [
      {
        resolve: "@medusajs/medusa/payment-stripe",
        id: "stripe",
        options: {
          apiKey: process.env.STRIPE_API_KEY,
          webhookSecret: process.env.STRIPE_WEBHOOK_SECRET,
        },
      },
    ],
  },
}
```

支付状态回调用统一入口 `/hooks/payment/[provider]`，Stripe 的 webhook 配到这个地址即可。另有内置的 `pp_system` 占位提供商，行为类似货到付款，开发调试时有用。

需要支付宝、微信支付或 Mollie、Paystack 的话，官方渠道没有现成模块，两条路：到 [integrations 页](https://medusajs.com/integrations/)找第三方维护的集成，或者自己写——自定义支付提供商继承 `AbstractPaymentProvider` 实现若干方法即可，支付宝和微信支付在国内确实都有社区实现，选型时要自己评估维护状态。

### 库存与履约（Inventory + Fulfillment + Stock Location）

库存按地点（Stock Location）管理，支持多仓库和预留（Reservation）：下单先冻结预留，履约确认后再落账。这套结构对多仓发货、门店库存共享的场景是现成的。

履约同样是提供商制：内置手动履约，接快递 100、Shippo 之类的服务则写一个 fulfillment provider 对接 API。

### 区域与渠道（Region + Sales Channel + Tax）

Region 绑定币种和国家，决定价格和运费的适用范围；Sales Channel 是渠道隔离的边界——一个品牌官网、一个 App、一个亚马逊店可以各建一个渠道，Publishable Key 绑定渠道后，前台天然只看到自己的商品；Tax 模块支持按区域粒度配置税率规则。

---

## 安装与快速上手

环境要求：Node.js ≥ 22.15（LTS 版本），PostgreSQL 装好并运行。Redis 开发环境不需要。

```bash
npx create-medusa-app@latest my-medusa-store
```

脚手架会问两个问题：数据库连接（默认会在本地 Postgres 创建名为 `medusa-my-medusa-store` 的库）、是否安装 Next.js Starter Storefront。装完后是 pnpm monorepo 结构：

```
my-medusa-store/
├── apps/
│   ├── backend/          # Medusa 应用 + 管理后台
│   │   ├── src/
│   │   │   ├── api/          # 自定义 API 路由
│   │   │   ├── modules/      # 自定义模块
│   │   │   ├── workflows/    # 自定义工作流
│   │   │   ├── subscribers/  # 事件订阅者
│   │   │   ├── jobs/         # 定时任务
│   │   │   ├── links/        # 模块关联定义
│   │   │   ├── admin/        # 管理后台扩展
│   │   │   └── scripts/      # CLI 脚本
│   │   └── medusa-config.ts
│   └── storefront/       # Next.js Starter（可选）
└── package.json
```

启动开发服务：

```bash
cd my-medusa-store/apps/backend
npm run dev
```

- 后端和管理后台：`http://localhost:9000`、`http://localhost:9000/app`
- Next.js 前台：`http://localhost:8000`
- 健康检查：`GET /health` 返回 `OK`

安装过程结束时会自动打开管理后台让你创建管理员；之后也可以用 CLI 建：

```bash
npx medusa user -e admin@medusajs.com -p supersecret
```

### 用 AI 智能体开发

官方维护的 [medusa-agent-skills](https://github.com/medusajs/medusa-agent-skills) 值得一试。Claude Code 里装插件市场后，AI 能按 Medusa 规范直接实现"顾客给商品写评价、管理员在后台审核"这类完整功能，生成的代码结构（模块、工作流、路由、后台扩展）和文档教程一致。初学者也可以用 `learn-medusa` 技能，让 AI 带着做一个 brands 功能来学概念。文档站同时提供 `llms.txt` 索引，方便任何智能体检索。

---

## 二次开发：v2 的扩展模型

v1 时代扩展 Medusa 的主流写法是继承核心 Service 覆盖方法。v2 把这条路封了，换成了五个正交的扩展点。理解它们的分工，是上手 Medusa 定制的关键。

### 自定义模块：装自己的业务逻辑

以一个品牌（Brand）模块为例，三个文件：

```typescript
// src/modules/brand/models/brand.ts
import { model } from "@medusajs/framework/utils"

export const Brand = model.define("brand", {
  id: model.id().primaryKey(),
  name: model.string(),
})
```

```typescript
// src/modules/brand/service.ts
import { MedusaService } from "@medusajs/framework/utils"
import { Brand } from "./models/brand"

class BrandModuleService extends MedusaService({
  Brand,
}) {}

export default BrandModuleService
```

```typescript
// src/modules/brand/index.ts
import { Module } from "@medusajs/framework/utils"
import BrandModuleService from "./service"

export const BRAND_MODULE = "brand"

export default Module(BRAND_MODULE, {
  service: BrandModuleService,
})
```

继承 `MedusaService` 工厂后，`createBrands`、`listBrands`、`deleteBrands` 等数据操作方法自动生成。迁移用两条命令走完：`npx medusa db:generate brand` 按模块生成迁移文件，`npx medusa db:migrate` 执行。数据模型是声明式的（Data Model Language），属性、关系、索引、校验约束都写在这里，类型自动推导。

### Module Links：跨模块关联数据

品牌和商品分属两个模块，互相隔离，怎么建立"这个商品属于那个品牌"的关联？在 `src/links` 里声明一条 link：

```typescript
// src/links/brand-product.ts
import { defineLink } from "@medusajs/framework/utils"
import BrandModule from "../modules/brand"
import ProductModule from "@medusajs/product"

export default defineLink(
  BrandModule.linkable.brand,
  ProductModule.linkable.product
)
```

声明之后，查询时用 `Query.graph` 一次取回商品和它挂的品牌，底层是数据库 join。想给品牌补一个 logo 字段，不需要改核心商品表——再加一个自定义模块，用 link 关联过去。这套机制取代了 v1 的"给核心实体加字段"，核心表从此不被改动。

### Workflows：编排与补偿

工作流是 v2 的一等公民，订单完成、商品创建等所有核心流程本身就是工作流。自定义工作流的写法：

```typescript
// src/workflows/create-brand.ts
import {
  createStep,
  createWorkflow,
  WorkflowResponse,
  StepResponse,
} from "@medusajs/framework/workflows-sdk"
import { BRAND_MODULE } from "../modules/brand"
import BrandModuleService from "../modules/brand/service"

type CreateBrandInput = { name: string }

export const createBrandStep = createStep(
  "create-brand-step",
  async (input: CreateBrandInput, { container }) => {
    const brandModuleService: BrandModuleService =
      container.resolve(BRAND_MODULE)
    const brand = await brandModuleService.createBrands(input)
    // 第二个参数传回补偿所需的数据
    return new StepResponse(brand, brand.id)
  },
  async (brandId, { container }) => {
    // 补偿函数：后续步骤失败时回滚本步骤
    if (!brandId) return
    const brandModuleService: BrandModuleService =
      container.resolve(BRAND_MODULE)
    await brandModuleService.deleteBrands(brandId)
  }
)

export const createBrandWorkflow = createWorkflow(
  "create-brand",
  (input: CreateBrandInput) => {
    const brand = createBrandStep(input)
    return new WorkflowResponse(brand)
  }
)
```

每个步骤带一个补偿函数，工作流引擎记录每步的执行状态（invoke/compensate），失败时沿已完成的步骤逆序回滚。步骤还可以配置自动重试和超时；跨多天的长流程（比如超时未支付自动关单）用长事务工作流实现，状态由工作流引擎模块持久化，生产环境换 Redis 引擎保证多实例下的正确性。

step 函数体内有一条硬约束：不能访问 step 外部的变量，只能通过入参里的 `container` 取依赖——这是为了保证步骤可以被独立重放。

### 扩展核心流程：Workflow Hooks

不改核心代码怎么在"创建商品"后追加自己的逻辑？核心工作流都预留了钩子。比如给下单流程加自定义校验：

```typescript
// src/workflows/hooks/validate-cart.ts
import { completeCartWorkflow } from "@medusajs/medusa/core-flows"

completeCartWorkflow.hooks.validate(
  async ({ input, cart }, { container }) => {
    // 返回前抛错即中断下单，例如黑名单校验、风控检查
    if (cart.email.endsWith("@blocked.com")) {
      throw new Error("下单被风控拦截")
    }
  }
)
```

`completeCartWorkflow` 还有 `orderCreated` 钩子在订单落库后执行。取代 v1 的 Service 继承，这套钩子是官方钦定的核心流程扩展点。

### 自定义 API 路由

```typescript
// src/api/store/brands/route.ts
import { MedusaRequest, MedusaResponse } from "@medusajs/framework/http"
import { createBrandWorkflow } from "../../workflows/create-brand"

export async function POST(req: MedusaRequest, res: MedusaResponse) {
  const { result: brand } = await createBrandWorkflow(req.scope).run({
    input: req.body as { name: string },
  })
  res.json({ brand })
}
```

路由函数里能拿到 `req.scope`（依赖注入容器），从中解析模块服务或工作流。需要鉴权的路由在 `src/api/middlewares.ts` 统一挂中间件：

```typescript
// src/api/middlewares.ts
import { defineMiddlewares, authenticate } from "@medusajs/framework/http"

export default defineMiddlewares({
  routes: [
    {
      matcher: "/store/brands*",
      methods: ["POST", "PUT", "DELETE"],
      // 只允许后台用户（支持 session、bearer、api-key 三种凭证）
      middlewares: [authenticate("user", ["session", "bearer", "api-key"])],
    },
  ],
})
```

### 管理后台扩展

管理后台是 React 应用，用 Widget 和 UI Route 两种方式扩展。Widget 声明注入位置，比如在商品详情页下方加一块品牌面板：

```tsx
// src/admin/widgets/product-brand.tsx
import { defineWidgetConfig } from "@medusajs/admin-sdk"
import { Container, Heading, Text } from "@medusajs/ui"

const ProductBrandWidget = () => {
  return (
    <Container className="divide-y p-0">
      <Heading level="h2">品牌信息</Heading>
      <Text>这里展示商品关联的品牌</Text>
    </Container>
  )
}

export const config = defineWidgetConfig({
  zone: "product.details.after",
})

export default ProductBrandWidget
```

`zone` 决定注入点（官方维护了一张注入位置参考表），后台代码热更新，改完刷新浏览器即可看到。完整的管理页面（自定义路由页）也是类似写法。

### 打包复用：插件

以上所有定制——模块、工作流、路由、订阅者、后台扩展——可以打成一个 npm 包（插件，v2.3.0 引入），在别的项目里加进 `medusa-config.ts` 的 `plugins` 数组就能用。官方仓库里的 draft-order（补录订单）、loyalty（积分）就是这种形态，其中 loyalty 属于 Enterprise Edition 需商业授权。单项目的业务逻辑没必要抽插件，跨项目复用或想开源分享时再打包。

---

## 部署方案

### 进程形态：server 与 worker 分离

v2 生产部署的关键词是 worker mode。后台任务（订阅者、定时任务、长事务工作流）可能很重，和 API 请求挤在一个进程里会互相拖累。官方建议部署两个实例，跑同一份构建产物，靠环境变量区分角色：

```bash
# server 实例：只处理 API 请求
WORKER_MODE=server npx medusa start

# worker 实例：只处理后台任务
WORKER_MODE=worker npx medusa start
```

两个实例连同一个 PostgreSQL；用 Redis 事件总线时，后台任务由 worker 实例统一消费。

构建用 `npx medusa build`，产物在 `.medusa/server`，自带 `medusa start` 入口。健康检查 `GET /health` 返回 `OK`，负载均衡器探活用这个。

### 平台与托管

| 平台 | 适用场景 | 说明 |
|------|---------|------|
| **Medusa Cloud** | 官方托管 | 零配置部署、自动扩缩、GitHub 集成，商业产品 |
| **Railway / Render** | 中小项目 | 官方有分步指南，PostgreSQL 用平台托管服务 |
| **DigitalOcean / CloudPanel** | VPS 自管 | 官方指南覆盖 |
| **AWS ECS** | 企业级 | Fargate + RDS + ElastiCache 组合 |
| **Vercel / Cloudflare** | 仅前台 | Next.js Storefront 部署到边缘，后端仍需自托管 |

Docker 部署官方也有专门指南（Compose 编排 backend、storefront、PostgreSQL、Redis 四个服务）。反向代理、限流这些通用环节，在 Nginx 或云负载均衡层做即可，Medusa 本身不内置。

---

## 与同类项目对比

三个常被放在一起比较的开源电商后端（数据截至 2026 年 10 月，stars 来自 GitHub API）：

| 特性 | Medusa | Saleor | Sylius |
|------|--------|--------|--------|
| 语言 | TypeScript / Node.js | Python / Django | PHP / Symfony |
| 数据库 | PostgreSQL | PostgreSQL | PostgreSQL / MySQL |
| API 风格 | REST | GraphQL | REST + GraphQL（API Platform） |
| 定制框架 | 模块 + 工作流 + 钩子 | App/插件 | Symfony Bundle 插件 |
| 管理后台 | 内置（Vite + React） | Dashboard 项目 | Symfony 后台 |
| 开源协议 | open-core（核心 MIT，企业版商业授权） | BSD-3-Clause | MIT |
| GitHub Stars | ~36.5k | ~23.4k | ~8.5k |

三者定位的重叠在"headless 电商 API"，差别在技术栈和定制哲学：

- **技术栈是第一决策项**。Node/TS 团队选 Medusa，前后端同语言同类型系统；Python 团队选 Saleor；PHP 团队选 Sylius。跨栈选型省不了学习成本。
- **API 范式影响前端工作方式**。Saleor 是 GraphQL-first，前端查询自由度高；Medusa 是 REST 加上 `fields` 展开，配合官方 JS SDK 用起来接近 RPC；Sylius 的 API Platform 两者都给。
- **定制深度上 Medusa 的框架化更彻底**。工作流补偿、模块隔离、声明式链接这些是应用框架的设计，用 Medusa 更像在"一个商务领域的前辈框架上开发"，而 Saleor/Sylius 更像"扩展一个成型的电商产品"。代价是 Medusa 要求你接受它的框架约定，只想改几个模板的团队会觉得重。
- **商业化模式**。Medusa 核心开源、RBAC 等企业功能收费；Saleor 核心同样开源但生态对齐其商业版；Sylius 整体 MIT，商业支持走服务。

---

## 采用决策与学习路径

### 适合选 Medusa 的情况

- 业务模型不是标准 B2C：B2B 批发价、多商户分账、订阅制、定制商品，这些要改订单和定价逻辑的场景正是框架的用武之地。
- 多渠道销售，需要 Sales Channel + Publishable Key 做渠道隔离，或者多仓库存共享。
- 团队是 Node.js/TypeScript 栈，希望前后端共享语言和工具链，还想要 AI 编码助手直接生成合规范的定制代码。
- 不能接受 SaaS 的订阅费、API 限流和数据出境，需要完整的数据控制权。

### 不急着选的情况

- 只是标准卖货，无深度定制需求——Shopify 或 WooCommerce 上线快得多，运维成本也低。
- 团队没有 Node.js 经验且短期不打算补——框架收益吃不到，只剩学习成本。
- 需要开箱即用的完整前台（多语言主题、模板市场）——Medusa 官方只有一个 Next.js Starter，前台基本要自己做。
- 现有系统是 v1 且深度定制过——v2 的扩展模型是重写级别的变化，迁移要按官方 v1→v2 指南重估工作量，不是升个版本号。

### 推荐的学习顺序

```
第 1 步：跑起来
  → create-medusa-app 建项目，走一遍前台浏览到下单的完整链路

第 2 步：建立架构直觉
  → 读官方 Architecture 章节和 From v1 to v2 概念页
  → 重点理解模块隔离：为什么不能继承核心 Service 了

第 3 步：跟着 Brands 教程做一遍
  → 自定义模块 → 数据模型 → 工作流 → API 路由 → 后台 Widget
  → 这条线走完，v2 五类扩展点就都摸过了

第 4 步：吃透工作流
  → 补偿函数、when-then 条件、并行步骤、重试、长事务
  → 这是和"写普通 CRUD"拉开差距的地方

第 5 步：接入支付与邮件
  → Stripe 模块配置 webhook，Notification 模块发订单确认邮件

第 6 步：生产部署
  → server/worker 分离，Redis 事件总线与工作流引擎，/health 探活
```

---

## 参考资源

- **官方文档**：https://docs.medusajs.com （learn 系列章节 + API 参考，附 [llms.txt](https://docs.medusajs.com/llms.txt)）
- **GitHub 仓库**：https://github.com/medusajs/medusa
- **从 v1 迁移**：https://docs.medusajs.com/learn/introduction/from-v1-to-v2
- **官方集成目录**：https://medusajs.com/integrations/
- **AI 智能体技能**：https://github.com/medusajs/medusa-agent-skills
- **Next.js Storefront**：https://github.com/medusajs/nextjs-starter-medusa
- **Discord 社区**：https://discord.gg/medusajs

---

*基于 Medusa v2.21（2026 年 10 月）编写。Medusa 迭代较快，配置项以官方文档为准；仍在 v1 的项目请参考官方迁移指南。*
