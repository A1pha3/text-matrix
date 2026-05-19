---
title: "MedusaJS：开源 Headless 商务平台从入门到精通指南"
date: 2026-05-17T20:25:00+08:00
slug: medusajs-open-source-ecommerce-platform-guide
description: "MedusaJS 是一个基于 Node.js/TypeScript 的开源 Headless 商务平台，提供灵活的电商后端架构，支持插件扩展、个性化定制与多场景部署。本文从核心概念、架构设计、功能特性、安装配置、插件系统、二次开发到生产部署，提供全方位技术文档。"
 keywords: ["MedusaJS", "Headless Commerce", "开源电商", "Node.js电商", "电商平台", "Medusa插件", "Medusa部署"]
 topics: ["电商", "Node.js", "TypeScript", "开源", "商务平台"]
 image: "https://medusa2hxh.files.brave系数.com/blog/2022-04-1-banner.jpg"
 author: "钳岳星君 🦞"
 draft: false
---

## 什么是 MedusaJS？

**MedusaJS**（官方仓库 [medusajs/medusa](https://github.com/medusajs/medusa)）是一个开源的 **Headless 商务平台**，基于 **Node.js + TypeScript** 构建，旨在为开发者提供灵活、可扩展的电商后端解决方案。与传统电商平台（如 Shopify、Magento）不同，Medusa 采用**前后端分离**架构——后端仅暴露 **REST API**，前端完全由开发者自主选择，可对接 Web、移动端、SaaS、小程序等各种前端。

> "Medusa 把电商后端变成了开发者手中的构建材料，而非一个黑盒产品。"

### 核心定位

| 维度 | 传统电商平台 | MedusaJS |
|------|------------|----------|
| 前端控制 | 受限，需使用平台主题 | 完全自主，任意前端框架 |
| 定制化 | 受插件市场限制 | 全源码开放，任意修改 |
| 商业模式 | 订阅制 | 开源免费（商业友好） |
| 部署方式 | SaaS 托管 | 自托管，完全自主 |

---

## 架构解析：Headless Commerce

Medusa 的核心架构理念是 **Headless Commerce**（无头商务），将"商务逻辑"从"展示层"中解耦出来。

### 三层架构模型

```
┌─────────────────────────────────────────────────────┐
│                  前端（Storefront）                  │
│    React Storefront  /  Next.js  /  任意前端框架     │
└──────────────────────┬──────────────────────────────┘
                       │  REST API / GraphQL
┌──────────────────────▼──────────────────────────────┐
│               Medusa Server（后端）                  │
│   Products  Orders  Payments  Carts  Shipping...    │
│              Event Bus (内部消息队列)                 │
└──────────────────────┬──────────────────────────────┘
                       │  数据库抽象层（TypeORM / Knex）
┌──────────────────────▼──────────────────────────────┐
│                  数据库层                            │
│         PostgreSQL  /  MySQL  /  SQLite             │
└─────────────────────────────────────────────────────┘
```

### API 分层设计

Medusa 将 API 明确划分为三个独立层级，每个层级服务不同客户端：

1. **Store API**（`/store`）：面向消费者——商品浏览、购物车、下单
2. **Admin API**（`/admin`）：面向商家——商品管理、订单处理、用户管理
3. **Auth API**（`/auth`）：面向认证——登录、注册、Token 管理

这种分层设计使得权限控制和 API 版本管理更加清晰，也便于对接不同的客户端应用。

### 数据库抽象层

Medusa 在数据库层做了良好的抽象：

```sql
-- Medusa 使用 TypeORM，支持多种数据库
-- 配置文件：medusa-config.js

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

---

## 核心功能特性

### 1. 商品管理（Products）

Medusa 的商品模型支持**多属性变体**、**多标签**、**多分类**，灵活满足各类电商场景。

```typescript
// 创建商品示例
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

**支持的功能：**
- 商品多属性变体（尺寸 + 颜色 + 材质等组合）
- 图片画廊与 metadata 自定义
- 分类（Collections）与标签（Tags）
- 库存管理（含多仓库支持）
- 商品Relations（相关商品推荐）

### 2. 购物车（Cart）

```typescript
// 前端添加商品到购物车
const cart = await fetch("http://localhost:9000/store/carts", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    region_id: "reg_xxx",
    items: [{
      variant_id: "variant_xxx",
      quantity: 2
    }]
  })
}).then(r => r.json())

// 更新购物车项
await fetch(`http://localhost:9000/store/carts/${cart.id}/line-items`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    variant_id: "variant_yyy",
    quantity: 1
  })
})
```

### 3. 订单系统（Orders）

```typescript
// 完成下单（从购物车创建订单）
const order = await medusa.createOrder(cart)

// 订单状态流转
// pending → authorized → captured → fulfilled → shipped → delivered
//                          ↓ (若支付失败)
//                         canceled
```

**订单流程支持：**
- 支付前授权（Authorization）
- 支付捕获（Capture）
- 部分退款 / 全额退款
- 订单编辑（编辑已创建但未发货的订单）
- 退货处理（Return）

### 4. 支付系统（Payments）

Medusa 原生集成了 **Stripe**、**Mollie**、**Paystack** 等主流支付网关：

```typescript
// 配置 Stripe 支付插件
// medusa-config.js
module.exports = {
  plugins: [
    {
      resolve: "@medusajs/medusa-payment-stripe",
      options: {
        api_key: "sk_test_xxx",
        webhook_secret: "whsec_xxx",
        // 配置要启用的支付方式
        payment_methods: ["card", "klarna", "afterpay_clearpay"]
      }
    }
  ]
}
```

**支持的支付方式：**

| 支付网关 | 支持地区 | 特点 |
|---------|---------|------|
| Stripe | 全球 | 信用卡、Klarna、Afterpay 等 |
| Mollie | 欧洲为主 | iDEAL、SEPA、信用卡 |
| Paystack | 非洲 | 移动支付、银行转账 |
| Manual | 测试用 | 模拟支付流程 |

### 5. 物流配送（Shipping）

```typescript
// 创建配送选项
const shippingOption = await medusa.createShippingOptions({
  region_id: "reg_xxx",
  provider_id: "default_shipping", // 或集成 DHL/FedEx 等插件
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
- **PostgreSQL** 14+（开发可用 SQLite）
- **Redis** 6+（用于事件队列和缓存）

### 方式一：快速创建项目（推荐）

```bash
# 使用官方脚手架创建项目
npx create-medusa-app@latest my-medusa-store

# 交互式选择：
# ? Choose a starter template
#   ❯ Next.js Starter (官方推荐)
#     Nuxt.js Storefront
#     Gatsby Storefront
#     Medusa UI (管理后台)
#     None (仅后端)
```

该脚本会自动：
1. 克隆并启动 Medusa Server
2. 配置 PostgreSQL 数据库连接
3. 运行数据库迁移
4. 种子数据初始化
5. 启动可选的前端商店

### 方式二：手动安装

```bash
# 1. 初始化项目
mkdir my-medusa-store && cd my-medusa-store

# 2. 安装 Medusa CLI
npm install @medusajs/cli -g

# 3. 初始化后端
medusa init --no-db

# 4. 配置文件
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

# 5. 安装数据库驱动
npm install pg

# 6. 启动服务
medusa develop
# 服务运行在 http://localhost:9000
# 管理后台： http://localhost:9000/app
```

### 启动后验证

```bash
# 健康检查
curl http://localhost:9000/health

# 应返回：
# {"status":"ok","version":"1.x.x","type":"medusa"}

# 获取商品列表
curl http://localhost:9000/store/products

# 获取已配置的 API Key
curl http://localhost:9000/admin/api-keys
```

---

## 插件系统：Medusa 的灵魂

Medusa 的插件系统是其最大亮点之一——**几乎所有功能都是插件**，开发者可以自由替换或扩展任意模块。

### 插件工作原理

Medusa 采用 **依赖注入 + 生命周期钩子** 的插件架构：

```typescript
// 每个插件都是一个独立的 Node.js 包
// 结构：src/index.ts → 暴露插件主体

// medusa-plugin-example/index.ts
import {
  Medusa,
  Middleware,
  EventBusService
} from "@medusajs/medusa"

export default {
  register: async function({ container, configFile }: {
    container: Medusa,
    configFile: Record<string, any>
  }) {
    // 在容器中注册自定义服务
    container.register({
      myCustomService: new MyCustomService()
    })
  },

  // 插件加载顺序（数字越小越先加载）
  load: async function({ container }) {
    const myService = container.resolve<MyCustomService>("myCustomService")

    // 监听事件
    const eventBus = container.resolve<EventBusService>("eventBusService")
    eventBus.subscribe("order.placed", async (data) => {
      await myService.onOrderPlaced(data)
    })
  },

  // 插件卸载时的清理逻辑
  dispose: async ({ container }) => {
    // 取消事件订阅、关闭连接等
  }
}
```

### 常用官方插件

```bash
# 安装常用插件
npm install @medusajs/medusa-payment-stripe      # Stripe 支付
npm install @medusajs/medusa-payment-woocommerce # WooCommerce 导入
npm install @medusajs/medusa-fulfillment-manuel  # 手动物流
npm install @medusajs/medusa-fulfillment-shippo  # Shippo 物流
npm install @medusajs/medusa-file-s3              # AWS S3 文件存储
npm install @medusajs/medusa-file-minio          # MinIO 兼容 S3
npm install @medusajs/medusa-cache-redis         # Redis 缓存层
npm install @medusajs/medusa-eventbus-redis     # Redis 事件总线
npm install @medusajs/medusa-link-Whitels        # Shopify 链接
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
    // 文件存储（S3 兼容）
    {
      resolve: "@medusajs/medusa-file-s3",
      options: {
        bucket: "my-medusa-bucket",
        region: "ap-northeast-1",
        access_key_id: "AKIAxxx",
        secret_access_key: "xxx"
      }
    },
    // Stripe 支付
    {
      resolve: "@medusajs/medusa-payment-stripe",
      options: {
        api_key: "sk_test_xxx",
        webhook_secret: "whsec_xxx"
      }
    },
    // Redis 缓存
    {
      resolve: "@medusajs/medusa-cache-redis",
      options: {
        redis_url: "redis://localhost:6379",
        ttl: 30 // 缓存 TTL（秒）
      }
    },
    // 自定义插件（本地路径）
    {
      resolve: "./src/plugins/my-custom-plugin"
    }
  ]
}
```

### 发布自定义插件

```bash
# 在 plugins 目录创建插件
mkdir -p plugins/my-medusa-plugin/src
cd plugins/my-medusa-plugin

# 初始化包
npm init -y

# 添加 Medusa 类型依赖
npm install @medusajs/medusa

# 创建插件源码
cat > src/index.ts << 'EOF'
import { Medusa } from "@medusajs/medusa"

class MyNotifierService {
  async sendOrderConfirmation(order) {
    console.log(`Order ${order.id} confirmed!`)
    // 集成邮件 / 短信 / Slack 等通知渠道
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

# 链接到主项目
npm link
cd ../../my-medusa-store
npm link my-medusa-plugin
```

---

## 二次开发与个性化定制

### 自定义 Service（服务层）

Medusa 的业务逻辑封装在 **Service** 中，推荐通过继承和重写来定制行为：

```typescript
// src/services/MyProductService.ts
import {
  ProductService,
  EventBusService
} from "@medusajs/medusa"

class MyProductService extends ProductService {
  private eventBus_: EventBusService

  constructor({
    productRepository,
    eventBusService,
    ...otherDeps
  }) {
    super({ productRepository, ...otherDeps })
    this.eventBus_ = eventBusService
  }

  // 添加自定义方法
  async getFeaturedProducts(limit = 10) {
    return this.productRepository.find({
      where: { tags: { value: "featured" } },
      take: limit,
      order: { created_at: "DESC" }
    })
  }

  // 重写原有方法（保留原有逻辑 + 扩展）
  async retrieve(productId, config?) {
    const product = await super.retrieve(productId, config)

    // 添加自定义字段或逻辑
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

    res.json({
      products
    })
  })

// src/api/routes/custom/index.ts
import { featuredProducts } from "./get-featured-products"

const customRoutes = (config) => [featuredProducts]

export default customRoutes
```

### 订阅事件总线（Event Bus）

Medusa 内置事件总线，支持异步处理耗时代理：

```typescript
// 在插件或 service 中订阅事件
class OrderProcessorService {
  constructor({ eventBusService }) {
    this.eventBus_ = eventBusService
  }

  async registerSubscribers() {
    // 订单创建时触发
    this.eventBus_.subscribe("order.placed", async (data) => {
      await this.processNewOrder(data)
    })

    // 订单发货时触发
    this.eventBus_.subscribe("order.shipment_created", async (data) => {
      await this.sendShipmentNotification(data)
    })

    // 产品更新时触发
    this.eventBus_.subscribe("product.updated", async (data) => {
      await this.syncToExternalPlatform(data)
    })
  }

  private async processNewOrder(data) {
    // 执行业务逻辑（发邮件、同步 ERP、更新分析等）
    console.log("Processing order:", data.id)
  }
}
```

### 工作流引擎（Workflows）

Medusa v1.14+ 引入了 **Workflows**（工作流引擎），用于编排复杂的异步业务逻辑：

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
    // Step 1: 创建产品
    const product = createProductsStep([{
      title: input.title,
      variants: [{ title: "Default", prices: [{ amount: input.price, currency_code: "usd" }] }]
    }])

    // Step 2: 验证产品（条件判断）
    const validated = transform({ product }, (input) => {
      if (!input.product.id) {
        throw new MedusaError(MedusaError.Types.INVALID_DATA, "Product creation failed")
      }
      return input.product
    })

    // Step 3: 发送通知（异步，不阻塞主流程）
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

---

## 部署方案

### 方案一：Docker 部署（推荐生产环境）

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
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f medusa
```

### 方案二：PM2 进程管理（VPS 部署）

```bash
# 1. 安装 PM2
npm install -g pm2

# 2. 创建启动配置
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

# 3. 启动
pm2 start ecosystem.config.js

# 4. 配置开机自启
pm2 save
pm2 startup
```

### 方案三：云平台部署

| 云平台 | 推荐配置 | 特点 |
|-------|---------|------|
| **Railway** | PostgreSQL + Medusa | 最简部署，按量付费 |
| **Render** | 共享 PostgreSQL + Web Service | 免费 tier 可用 |
| **AWS ECS** | ECS Fargate + RDS + ElastiCache | 企业级高可用 |
| **GCP Cloud Run** | Cloud Run + Cloud SQL + Memorystore | 无服务器容器 |

**Railway 部署示例：**

```bash
# 1. 安装 Railway CLI
npm install -g @railway/cli

# 2. 登录
railway login

# 3. 初始化项目
railway init

# 4. 添加 PostgreSQL 插件
railway add postgres

# 5. 设置环境变量
railway variable set DATABASE_URL=$(railway env postgres -q)
railway variable set REDIS_URL=$(railway env redis -q)

# 6. 部署
railway up
```

### 生产环境 Nginx 反向代理配置

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

    # API 请求代理
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

        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket 支持（用于管理后台热重载等）
    location /ws {
        proxy_pass http://medusa_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 最佳实践与性能优化

### 1. 数据库优化

```sql
-- 为高频查询字段添加索引
CREATE INDEX idx_product_tags ON product_tags (value);
CREATE INDEX idx_product_handle ON product (handle);
CREATE INDEX idx_order_display_id ON order (display_id);

-- 分页查询优化（使用游标分页替代 OFFSET）
-- 游标分页：
SELECT * FROM order WHERE id > last_seen_id ORDER BY id LIMIT 20;

-- OFFSET 分页（大数据量时不推荐）
SELECT * FROM order ORDER BY id OFFSET 100000 LIMIT 20;
```

### 2. Redis 缓存策略

```javascript
// medusa-config.js 中配置 Redis 缓存
{
  resolve: "@medusajs/medusa-cache-redis",
  options: {
    redis_url: "redis://localhost:6379",
    ttl: 60,      // 默认缓存 TTL（秒）
    scopes: {
      "productService": 300,  // 商品缓存 5 分钟
      "cartService": 0       // 购物车不缓存（实时性要求高）
    }
  }
}
```

### 3. API 响应优化

```typescript
// 避免 N+1 查询问题，使用Medusa的select/inlude参数
const products = await medusa.products.list({
  limit: 20,
  // 只获取需要的字段，减少数据传输
  fields: "id,title,thumbnail,variants.calculated_price"
})

// 使用 expand 参数预加载关联数据
const orders = await medusa.orders.list({
  expand: "items,variants,shipping_methods"
})
```

### 4. 安全加固

```javascript
// CORS 配置（medusa-config.js）
module.exports = {
  projectConfig: {
    cors_s横向: [
      "https://admin.mystore.com",
      "https://store.mystore.com"
    ]
  }
}

// Rate Limiting（通过 Nginx 或 API 网关实现）
// Nginx 配置：
// limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
// limit_req zone=api burst=20 nodelay;
```

---

## 与竞品对比

| 特性 | MedusaJS | Saleor | Sylius |
|------|----------|--------|--------|
| 语言 | TypeScript/Node.js | Python/Django | PHP/Symfony |
| 数据库 | PostgreSQL | PostgreSQL | PostgreSQL/MySQL |
| API 风格 | REST | GraphQL | REST + GraphQL |
| 插件生态 | ⭐⭐⭐⭐ 丰富 | ⭐⭐⭐ 一般 | ⭐⭐⭐ 较成熟 |
| 部署复杂度 | 中等 | 中等 | 较高 |
| 管理后台 | React Admin（官方） | 三方方案 | Symfony Admin |
| 开源协议 | MIT | BSD | MIT |
| GitHub Stars | ~25k+ | ~20k+ | ~8k+ |

---

## 总结与学习路径

**MedusaJS 是目前开源电商领域最具开发者友好度的选择之一。** 其核心优势在于：

1. **真正的 Headless**：后端 API 驱动，前端完全自主
2. **插件化架构**：灵活替换任意功能模块
3. **TypeScript 原生**：类型安全，开发体验优秀
4. **活跃社区**：GitHub 25k+ Stars，插件生态持续增长
5. **商业友好**：MIT 协议，生产可用

### 推荐学习路径

```
第1步：快速上手
  → 运行 create-medusa-app，体验完整电商流程

第2步：理解数据模型
  → 研读 Medusa 官方文档的数据模型章节
  → 理解 Product / Variant / Cart / Order / Region 的关系

第3步：掌握 API 层
  → 熟悉 Store API 和 Admin API 的调用方式
  → 通过 Postman 或 Insomnia 测试 API

第4步：深入插件系统
  → 阅读官方插件源码（如 medusa-payment-stripe）
  → 编写第一个自定义插件

第5步：进阶定制
  → 学习 Service 层定制和自定义路由
  → 掌握 Event Bus 和 Workflows

第6步：生产部署
  → 使用 Docker 或 PM2 部署到生产环境
  → 配置 Nginx、SSL 和监控告警
```

---

## 参考资源

- **官方文档**：https://docs.medusajs.com
- **GitHub 仓库**：https://github.com/medusajs/medusa
- **官方插件市场**：https://medusajs.com/plugins
- **Discord 社区**：https://discord.gg/medusajs
- **Medusa Storefront 模板**：https://github.com/medusajs/nextjs-starter-medusa

---

*本文基于 MedusaJS v1.x 版本编写，部分特性在 v2.x（开发中）中可能有变化，建议参考官方文档获取最新信息。*