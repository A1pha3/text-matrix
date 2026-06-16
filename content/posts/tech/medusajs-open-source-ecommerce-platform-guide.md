+++
date = '2026-05-17T20:25:00+08:00'
draft = false
title = 'MedusaJS：开源 Headless 商务平台'
slug = 'medusajs-open-source-ecommerce-platform-guide'
description = 'MedusaJS 是一个基于 Node.js/TypeScript 的开源 Headless 商务平台，提供灵活的电商后端架构，支持插件扩展、个性化定制与多场景部署。'
categories = ['技术笔记']
tags = ['开源', '电商', 'Node.js', 'TypeScript']
+++

## MedusaJS 解决的是什么

选电商后端框架时，大多数团队真正纠结的不是"能不能跑起来"，而是"以后改不动了怎么办"。SaaS 平台把后台逻辑锁在订阅费里，自研又需要从头搭一套商品、订单、支付、物流系统。

[MedusaJS](https://github.com/medusajs/medusa)（简称 Medusa）走的是第三条路：把电商后端做成一组可替换的模块，用插件而不是配置文件来扩展功能。它是基于 **Node.js + TypeScript** 的开源 **Headless 商务平台**，后端只暴露 REST API，前端你可以用 React、Next.js、Vue 或任何框架。

下面这张图概括了 Medusa 的三层拆法和它提供的核心模块：

```
┌──────────────────────────────────────────────────────────────┐
│                    前端（任意框架）                            │
│       React  /  Next.js  /  Vue  /  小程序  /  Flutter       │
└──────────────────────────┬───────────────────────────────────┘
                           │  REST API
┌──────────────────────────▼───────────────────────────────────┐
│                   Medusa Server                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Products │ │  Orders  │ │ Payments │ │  Shipping    │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │  Carts   │ │ Regions  │ │  Auth    │  │  Event Bus   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘   │
│                                                              │
│  插件系统（依赖注入 + 生命周期钩子）                            │
│  Workflows 工作流引擎（v1.14+）                                │
└──────────────────────────┬───────────────────────────────────┘
                           │  TypeORM / Knex 抽象层
┌──────────────────────────▼───────────────────────────────────┐
│          PostgreSQL  /  MySQL  /  SQLite                     │
│          Redis（事件队列 + 缓存）                              │
└──────────────────────────────────────────────────────────────┘
```

下面会先讲架构和关键机制，再给一个完整任务流案例，然后展开安装、插件开发、定制部署的具体做法。已经在评估 Medusa 的话，可以直接跳到最后的「采用决策」。

---

## 一次下单请求穿过系统

在展开模块细节之前，先看一个具体任务在 Medusa 里怎么流转。假设一个用户从浏览商品到支付完成：

```
用户浏览商品
  → Store API GET /store/products（可带 ?expand=variants 预加载变体）
  → 返回商品列表，含变体价格、库存状态

用户加入购物车
  → Store API POST /store/carts（region_id + variant_id + quantity）
  → 服务端计算运费、税费，返回 cart 对象含 totals

用户发起结算
  → Store API POST /store/carts/:id/payment-sessions
  → 支付插件（Stripe 等）创建 payment session，返回 client_secret

用户在前端完成支付（Stripe Elements / 第三方 SDK）
  → 前端 Stripe SDK 完成 3D Secure 等流程
  → Medusa 通过 webhook 收到支付授权结果

Medusa 自动完成
  → 购物车 → 订单（cart.completeOrder）
  → 事件总线触发 order.placed
  → 订阅者执行：扣库存、发邮件、同步 ERP、通知物流
```

这个流程里，Medusa 负责的几件事是明确的：商品数据、购物车状态机、订单生命周期、支付 session 管理、以及通过事件总线把"发生了什么"通知给所有关心的插件。它不负责的也同样明确：前端 UI、支付 SDK 集成细节、邮件模板、物流追踪页面——这些都在你的控制范围里。

---

## 架构怎么拆的

### 三层 API 设计

Medusa 把 API 拆成三个独立路由组，各自服务不同客户端，权限边界清晰：

| API 层 | 路由前缀 | 服务对象 | 典型操作 |
|--------|---------|---------|---------|
| **Store** | `/store` | 消费者（C 端） | 浏览商品、管理购物车、下单、查订单 |
| **Admin** | `/admin` | 商家（后台） | 商品 CRUD、订单处理、用户管理、报表 |
| **Auth** | `/auth` | 认证 | 登录、注册、Token 刷新、密码重置 |

Store 和 Admin 各自独立鉴权：Store 用 customer token，Admin 用 JWT + API Key。分开部署时，你可以把 Admin API 放在内网、Store API 暴露公网，中间不用额外加一层网关做权限隔离。

### 数据库抽象层

Medusa 在 ORM 层做了封装，一套代码可以跑在 PostgreSQL、MySQL 或 SQLite 上。生产环境推荐 PostgreSQL，开发调试可以用 SQLite 省掉数据库安装步骤。

```javascript
// medusa-config.js
module.exports = {
  projectConfig: {
    redis_url: "redis://localhost:6379",
    database_type: "postgres",  // postgres | mysql | sqlite
    database_url: "postgres://localhost:5432/medusa",
    database_extra: {
      ssl: { enabled: false }
    }
  }
}
```

Redis 承担两件事：事件队列的消息中转（默认用 Redis 做 event bus 后端）和可选的缓存层。如果不用缓存插件，Redis 最低配置也可以跑，但 event bus 依赖它。

---

## 核心模块

### 商品（Products）

Medusa 的商品模型围绕"变体"展开。一个 Product 可以有多个 Option（如尺寸、颜色），每个 Option 组合出一个 Variant，每个 Variant 独立管理价格和库存。这和 Shopify 的模型一致，熟悉 Shopify 数据结构的开发者迁移成本很低。

```typescript
// 通过 Admin API 创建商品（实际调用在服务端）
const product = await medusa.createProduct({
  title: "Ultimate T-Shirt",
  description: "Premium cotton t-shirt",
  variants: [
    {
      title: "Large / Black",
      prices: [{ currency_code: "usd", amount: 2999 }],
      inventory_quantity: 100,
      options: { Size: "Large", Color: "Black" }
    },
    {
      title: "Medium / White",
      prices: [{ currency_code: "usd", amount: 2999 }],
      inventory_quantity: 50,
      options: { Size: "Medium", Color: "White" }
    }
  ],
  options: [
    { title: "Size", values: ["Small", "Medium", "Large"] },
    { title: "Color", values: ["Black", "White", "Navy"] }
  ],
  tags: ["clothing", "summer", "sale"],
  collections: ["summer-collection-id"]
})
```

商品模块还覆盖：多仓库库存、图片画廊（通过 file plugin 对接 S3/MinIO）、自定义 metadata 字段、以及通过 Relations 做相关商品推荐。

### 购物车（Cart）

购物车是 Medusa 里状态最复杂的一个模块——它需要联查 Region（区域定价）、Shipping Option（可选配送方式）、Payment Session（支付会话）和 Discount（优惠规则）。Medusa 把这套逻辑封装在 CartService 里，前端只需要调用 REST API。

```typescript
// 创建购物车
const cart = await fetch("http://localhost:9000/store/carts", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    region_id: "reg_xxx",
    items: [{ variant_id: "variant_xxx", quantity: 2 }]
  })
}).then(r => r.json())

// 追加商品到已有购物车
await fetch(`http://localhost:9000/store/carts/${cart.id}/line-items`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ variant_id: "variant_yyy", quantity: 1 })
})
```

购物车在生成订单后不会自动删除——这个设计让你可以基于同一购物车做多次支付尝试，或者让用户回到未完成的购物车。

### 订单（Orders）

订单状态机是 Medusa 最值得细看的设计之一。它不是简单的"已支付 / 未支付"二元状态，而是把支付授权和实际扣款拆成两步：

```
pending → authorized → captured → fulfilled → shipped → delivered
                ↓（支付失败或取消授权）
             canceled
```

这个拆分的实际意义是：你可以在用户下单时只做预授权（冻结额度），等仓库确认有货再真正扣款。如果发货前取消，取消授权即可，省掉退款手续费。

订单还支持：部分退款、订单编辑（发货前修改商品或地址）、退货（Return）和换货（Swap）。

### 支付（Payments）

支付通过插件接入，Medusa 本身不处理任何支付逻辑，只管理 Payment Session 的生命周期。原生支持的支付网关：

| 网关 | 覆盖地区 | 说明 |
|------|---------|------|
| Stripe | 全球 | 信用卡、Klarna、Afterpay、支付宝等 |
| Mollie | 欧洲 | iDEAL、SEPA、信用卡 |
| Paystack | 非洲 | 移动支付、银行转账 |
| Manual | 测试/开发 | 模拟支付流程，不调用真实网关 |

```javascript
// medusa-config.js 中配置 Stripe
module.exports = {
  plugins: [
    {
      resolve: "@medusajs/medusa-payment-stripe",
      options: {
        api_key: "sk_test_xxx",
        webhook_secret: "whsec_xxx",
        payment_methods: ["card", "klarna", "afterpay_clearpay"]
      }
    }
  ]
}
```

### 物流（Shipping）

配送选项按 Region 配置，每个 Region 可以有多个 Shipping Option，各自绑定不同的 Provider（默认手动计算、或对接 DHL/FedEx 等第三方插件）。配送费用可以根据购物车小计设置阶梯规则。

```typescript
const shippingOption = await medusa.createShippingOptions({
  region_id: "reg_xxx",
  provider_id: "default_shipping",
  name: "Express Shipping",
  amount: 1999,
  requirements: [
    { type: "min_subtotal", value: 0 },
    { type: "max_subtotal", value: 50000 }
  ]
})
```

---

## 安装与快速上手

### 环境要求

- **Node.js** ≥ 18.0
- **PostgreSQL** 14+（开发环境可用 SQLite 替代）
- **Redis** 6+（事件队列和缓存）

### 方式一：脚手架创建（推荐）

```bash
npx create-medusa-app@latest my-medusa-store

# 交互式选择：
# ? Choose a starter template
#   ❯ Next.js Starter（官方推荐）
#     Nuxt.js Storefront
#     Gatsby Storefront
#     Medusa UI（管理后台）
#     None（仅后端）
```

脚本会自动完成：克隆并启动 Medusa Server、配置数据库连接、运行迁移、初始化种子数据、启动可选的前端商店。

### 方式二：手动安装

```bash
mkdir my-medusa-store && cd my-medusa-store
npm install @medusajs/cli -g
medusa init --no-db

cat > medusa-config.js << 'EOF'
module.exports = {
  projectConfig: {
    redis_url: "redis://localhost:6379",
    database_type: "postgres",
    database_url: "postgres://localhost:5432/medusa",
    database_extra: { ssl: { enabled: false } },
    port: 9000
  },
  plugins: []
}
EOF

npm install pg
medusa develop
# 服务运行在 http://localhost:9000
# 管理后台：http://localhost:9000/app
```

### 启动后验证

```bash
curl http://localhost:9000/health
# {"status":"ok","version":"1.x.x","type":"medusa"}

curl http://localhost:9000/store/products
```

---

## 插件系统：替换任意模块

Medusa 的插件是"模块替换"，不是"功能开关"。支付、物流、文件存储、缓存、事件总线——这些全部通过插件注入，Medusa 核心只提供接口契约和生命周期钩子。

### 插件怎么写

每个插件是一个独立 npm 包，暴露 `register`、`load`、`dispose` 三个生命周期函数：

```typescript
// medusa-plugin-example/index.ts
import { Medusa, EventBusService } from "@medusajs/medusa"

export default {
  register: async function({ container, configFile }: {
    container: Medusa,
    configFile: Record<string, any>
  }) {
    container.register({
      myCustomService: new MyCustomService()
    })
  },

  load: async function({ container }) {
    const myService = container.resolve<MyCustomService>("myCustomService")
    const eventBus = container.resolve<EventBusService>("eventBusService")
    eventBus.subscribe("order.placed", async (data) => {
      await myService.onOrderPlaced(data)
    })
  },

  dispose: async ({ container }) => {
    // 取消订阅、关闭连接
  }
}
```

`register` 阶段往 IoC 容器注册服务，`load` 阶段订阅事件或启动后台任务，`dispose` 阶段做清理。加载顺序由 `load` 的优先级字段控制（数字越小越先加载）。

### 常用官方插件

```bash
npm install @medusajs/medusa-payment-stripe       # Stripe 支付
npm install @medusajs/medusa-payment-woocommerce  # WooCommerce 数据导入
npm install @medusajs/medusa-fulfillment-manual   # 手动配送
npm install @medusajs/medusa-fulfillment-shippo   # Shippo 物流
npm install @medusajs/medusa-file-s3              # AWS S3 文件存储
npm install @medusajs/medusa-file-minio           # MinIO 兼容 S3
npm install @medusajs/medusa-cache-redis          # Redis 缓存
npm install @medusajs/medusa-eventbus-redis       # Redis 事件总线
```

### 完整插件配置示例

```javascript
// medusa-config.js
module.exports = {
  projectConfig: {
    redis_url: "redis://localhost:6379",
    database_type: "postgres",
    database_url: "postgres://localhost:5432/medusa",
    database_extra: { ssl: { enabled: false } },
    port: 9000
  },
  plugins: [
    {
      resolve: "@medusajs/medusa-file-s3",
      options: {
        bucket: "my-medusa-bucket",
        region: "ap-northeast-1",
        access_key_id: "AKIAxxx",
        secret_access_key: "xxx"
      }
    },
    {
      resolve: "@medusajs/medusa-payment-stripe",
      options: {
        api_key: "sk_test_xxx",
        webhook_secret: "whsec_xxx"
      }
    },
    {
      resolve: "@medusajs/medusa-cache-redis",
      options: {
        redis_url: "redis://localhost:6379",
        ttl: 30
      }
    },
    {
      resolve: "./src/plugins/my-custom-plugin"
    }
  ]
}
```

### 发布自定义插件

```bash
mkdir -p plugins/my-medusa-plugin/src
cd plugins/my-medusa-plugin
npm init -y
npm install @medusajs/medusa

cat > src/index.ts << 'EOF'
import { Medusa } from "@medusajs/medusa"

class MyNotifierService {
  async sendOrderConfirmation(order) {
    console.log(`Order ${order.id} confirmed!`)
  }
}

export default {
  register: async ({ container }) => {
    container.register({
      myNotifierService: new MyNotifierService()
    })
  }
}
EOF

npm link
cd ../../my-medusa-store
npm link my-medusa-plugin
```

---

## 二次开发：Service 层与事件总线

Medusa 的业务逻辑封装在 Service 中。扩展的方式不是改源码，而是继承 Service 并重写方法——你的自定义 Service 通过 loader 注册后，会替换掉默认实现。

### 继承并扩展 ProductService

```typescript
// src/services/MyProductService.ts
import { ProductService, EventBusService } from "@medusajs/medusa"

class MyProductService extends ProductService {
  private eventBus_: EventBusService

  constructor({ productRepository, eventBusService, ...otherDeps }) {
    super({ productRepository, ...otherDeps })
    this.eventBus_ = eventBusService
  }

  async getFeaturedProducts(limit = 10) {
    return this.productRepository.find({
      where: { tags: { value: "featured" } },
      take: limit,
      order: { created_at: "DESC" }
    })
  }

  async retrieve(productId, config?) {
    const product = await super.retrieve(productId, config)
    product["my_custom_field"] = await this.computeCustomField(productId)
    return product
  }
}

export default MyProductService
```

### 注册自定义 Service

```typescript
// src/loaders/custom.ts
import { getContainer } from "@medusajs/medusa"
import MyProductService from "../services/MyProductService"

export default async function customLoader({ container }) {
  container.register({
    myProductService: MyProductService
  })
}
```

### 自定义 API 路由

```typescript
// src/api/routes/custom/get-featured-products.ts
import { Router } from "express"
import { getEmptyResponseBody } from "@medusajs/medusa"

const router = Router()

export const featuredProducts = (container) =>
  router.get("/store/featured-products", async (req, res) => {
    const productService = container.resolve("myProductService")
    const products = await productService.getFeaturedProducts(20)
    res.json({ products })
  })

// src/api/routes/custom/index.ts
import { featuredProducts } from "./get-featured-products"

const customRoutes = (config) => [featuredProducts]

export default customRoutes
```

### 事件总线（Event Bus）

事件总线是 Medusa 里实现异步解耦的关键机制。订单创建、支付完成、商品更新等操作都会发出事件，插件和自定义 Service 通过订阅这些事件来响应——发邮件、同步 ERP、写入分析数据库，这些都不阻塞主流程。

```typescript
class OrderProcessorService {
  constructor({ eventBusService }) {
    this.eventBus_ = eventBusService
  }

  async registerSubscribers() {
    this.eventBus_.subscribe("order.placed", async (data) => {
      await this.processNewOrder(data)
    })

    this.eventBus_.subscribe("order.shipment_created", async (data) => {
      await this.sendShipmentNotification(data)
    })

    this.eventBus_.subscribe("product.updated", async (data) => {
      await this.syncToExternalPlatform(data)
    })
  }

  private async processNewOrder(data) {
    console.log("Processing order:", data.id)
  }
}
```

### Workflows 工作流引擎（v1.14+）

事件总线适合"通知"类的异步任务，但遇到需要编排多步骤、带条件判断和补偿逻辑的流程时，Medusa 提供了 Workflows。它把多个步骤串成一个有向图，支持步骤间的数据传递和失败回滚。

```typescript
// src/workflows/create-product-workflow.ts
import {
  createWorkflow,
  WorkflowEvent,
  MedusaError
} from "@medusajs/medusa"

const createProductWorkflow = createWorkflow(
  "create-product-with-notification",
  function (input: { title: string; price: number }) {
    const product = createProductsStep([{
      title: input.title,
      variants: [{ title: "Default", prices: [{ amount: input.price, currency_code: "usd" }] }]
    }])

    const validated = transform({ product }, (input) => {
      if (!input.product.id) {
        throw new MedusaError(MedusaError.Types.INVALID_DATA, "Product creation failed")
      }
      return input.product
    })

    sendNotificationStep({
      to: "admin@example.com",
      subject: `New Product: ${input.title}`,
      body: "A new product has been created."
    })

    return validated
  }
)

export default createProductWorkflow
```

事件总线和 Workflows 的边界是这样的：一条规则是"通知别人"，用事件总线；一条规则是"多步骤任务本身需要可观测、可重试、可补偿"，用 Workflows。

---

## 部署方案

### Docker 部署

```yaml
# docker-compose.yml
version: "3.8"
services:
  medusa:
    build: .
    ports:
      - "9000:9000"
    environment:
      DATABASE_URL: postgres://postgres:postgres@db:5432/medusa
      REDIS_URL: redis://redis:6379
      NODE_ENV: production
    depends_on:
      - db
      - redis
    volumes:
      - ./medusa-config.js:/app/medusa-config.js

  db:
    image: postgres:14-alpine
    environment:
      POSTGRES_DB: medusa
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

```bash
docker-compose up -d
docker-compose logs -f medusa
```

### PM2 进程管理（VPS 部署）

```bash
npm install -g pm2

cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: "medusa-server",
    script: "node",
    args: ["--inspect", "./node_modules/@medusajs/medusa/dist/index.js"],
    cwd: "/opt/medusa",
    env: {
      NODE_ENV: "production",
      DATABASE_URL: "postgres://postgres:secret@localhost:5432/medusa",
      REDIS_URL: "redis://localhost:6379",
      PORT: 9000
    },
    instances: 2,
    exec_mode: "cluster"
  }]
}
EOF

pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### 云平台

| 平台 | 推荐配置 | 特点 |
|------|---------|------|
| **Railway** | PostgreSQL + Medusa | 最简部署，按量付费 |
| **Render** | 共享 PostgreSQL + Web Service | 免费 tier 可用 |
| **AWS ECS** | ECS Fargate + RDS + ElastiCache | 企业级高可用 |
| **GCP Cloud Run** | Cloud Run + Cloud SQL + Memorystore | 无服务器容器 |

Railway 部署示例：

```bash
npm install -g @railway/cli
railway login
railway init
railway add postgres
railway variable set DATABASE_URL=$(railway env postgres -q)
railway variable set REDIS_URL=$(railway env redis -q)
railway up
```

### Nginx 反向代理

```nginx
# /etc/nginx/sites-available/medusa
upstream medusa_backend {
    server 127.0.0.1:9000;
    keepalive 64;
}

server {
    listen 443 ssl http2;
    server_name api.mystore.com;

    ssl_certificate /etc/letsencrypt/live/api.mystore.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.mystore.com/privkey.pem;

    location / {
        proxy_pass http://medusa_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /ws {
        proxy_pass http://medusa_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 性能优化与安全加固

### 数据库索引

```sql
CREATE INDEX idx_product_tags ON product_tags (value);
CREATE INDEX idx_product_handle ON product (handle);
CREATE INDEX idx_order_display_id ON order (display_id);

-- 游标分页（大数据量场景）
SELECT * FROM order WHERE id > last_seen_id ORDER BY id LIMIT 20;

-- OFFSET 分页（深度分页性能差，不推荐）
SELECT * FROM order ORDER BY id OFFSET 100000 LIMIT 20;
```

### Redis 缓存策略

```javascript
// medusa-config.js
{
  resolve: "@medusajs/medusa-cache-redis",
  options: {
    redis_url: "redis://localhost:6379",
    ttl: 60,
    scopes: {
      "productService": 300,  // 商品缓存 5 分钟
      "cartService": 0        // 购物车不缓存（实时性要求高）
    }
  }
}
```

### API 响应优化

```typescript
// 用 fields 减少返回字段，避免 N+1 查询
const products = await medusa.products.list({
  limit: 20,
  fields: "id,title,thumbnail,variants.calculated_price"
})

// 用 expand 预加载关联数据
const orders = await medusa.orders.list({
  expand: "items,variants,shipping_methods"
})
```

### 安全配置

```javascript
// CORS 白名单（medusa-config.js）
module.exports = {
  projectConfig: {
    cors_domains: [
      "https://admin.mystore.com",
      "https://store.mystore.com"
    ]
  }
}
```

限流建议通过 Nginx 或 API 网关实现，不在 Medusa 层做：

```nginx
# limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
# limit_req zone=api burst=20 nodelay;
```

---

## 与同类项目对比

| 特性 | MedusaJS | Saleor | Sylius |
|------|----------|--------|--------|
| 语言 | TypeScript/Node.js | Python/Django | PHP/Symfony |
| 数据库 | PostgreSQL | PostgreSQL | PostgreSQL/MySQL |
| API 风格 | REST | GraphQL | REST + GraphQL |
| 插件生态 | 丰富 | 一般 | 较成熟 |
| 部署复杂度 | 中等 | 中等 | 较高 |
| 管理后台 | React Admin（官方） | 三方方案 | Symfony Admin |
| 开源协议 | MIT | BSD | MIT |
| GitHub Stars | ~25k+ | ~20k+ | ~8k+ |

选择 Medusa 还是 Saleor，主要看团队技术栈。Node.js 团队选 Medusa 几乎没有学习成本，Python 团队选 Saleor 同理。Sylius 的插件生态更成熟，但 PHP 生态的招聘和迭代速度在一些场景下是劣势。

---

## 采用决策与学习路径

### 什么时候选 Medusa

- 你需要一个电商后端，但前端必须完全自主（自定义 UI、多端同步）。
- 团队技术栈是 Node.js/TypeScript，不想引入额外的语言和运维负担。
- 业务模型不是标准 B2C——比如 B2B 批发、多租户市场、订阅制电商——这些需要深度定制订单和商品逻辑。
- 你不希望被 SaaS 平台的订阅费和 API 限流捆住。

### 什么时候不急着选 Medusa

- 只需要一个简单的商品展示 + 下单页面，不需要复杂的订单和物流管理——这种情况下用 Shopify 或 WooCommerce 更快上线。
- 团队没有 Node.js 经验，短期内也不想投入学习成本。
- 业务需要开箱即用的多语言、多币种前台——Medusa 这些能力需要自己搭建或找插件。

### 推荐的学习顺序

```
第 1 步：跑起来
  → create-medusa-app，走一遍商品浏览到下单的完整流程

第 2 步：理解数据模型
  → 读懂 Product / Variant / Cart / Order / Region 之间的关系

第 3 步：熟悉 API 层
  → 用 Postman 把 Store API 和 Admin API 的主要端点过一遍

第 4 步：拆一个插件
  → 先读 medusa-payment-stripe 的源码，再写一个自定义插件

第 5 步：定制 Service 和路由
  → 继承一个 Service，挂一个自定义 API 端点

第 6 步：掌握事件总线和 Workflows
  → 区分"通知型"和"编排型"异步任务，各自用对工具

第 7 步：生产部署
  → Docker + Nginx + SSL + 监控，跑通完整部署链路
```

---

## 参考资源

- **官方文档**：https://docs.medusajs.com
- **GitHub 仓库**：https://github.com/medusajs/medusa
- **官方插件市场**：https://medusajs.com/plugins
- **Discord 社区**：https://discord.gg/medusajs
- **Next.js Storefront 模板**：https://github.com/medusajs/nextjs-starter-medusa

---

*基于 MedusaJS v1.x 版本编写，v2.x（开发中）的部分特性可能有变化，建议参考官方文档获取最新信息。*