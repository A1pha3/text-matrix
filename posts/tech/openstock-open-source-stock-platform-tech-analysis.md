---
title: "OpenStock：从入门到精通，开源股票数据平台的全方位技术解析"
date: 2026-05-27T15:05:00+08:00
draft: false
author: "钳岳星君"
tags: ["OpenStock", "开源", "股票", "金融数据", "Next.js", "Inngest", "MongoDB", "Better Auth", "Finnhub", "TradingView", "Docker"]
categories: ["技术笔记", "金融科技"]
description: "OpenStock 是 GitHub 获星 12k+ 的开源股票数据平台，AGPL-3.0 许可，Next.js 15 + TypeScript + Inngest + MongoDB 技术栈。本文从项目架构、核心模块、数据流、安全设计、部署实践到二次开发，提供从入门到精通的完整技术指南。"
---

# OpenStock：从入门到精通，开源股票数据平台的全方位技术解析

## 前言

在金融数据领域，彭博终端每年数千美元的订阅费用让个人开发者和散户投资者望而却步。**OpenStock**（Open-Dev-Society/OpenStock）正是为打破这一壁垒而生——一个完全开源、免费使用的股票数据平台。

截至 2026 年 5 月，该项目已收获 **12,311 ⭐ Star**、**1,639 Fork**，是 GitHub Trending 上的热门项目。其核心理念写在项目宣言中：

> _"We live in a world where knowledge is hidden behind paywalls… We believe there's a better way."_

本文基于项目源码（`main` 分支）进行深度技术解析，覆盖架构设计、核心模块、数据流、安全机制、部署实践及二次开发路径。

---

## 一、项目概览

### 1.1 基本信息

| 属性 | 值 |
|------|-----|
| **仓库** | [Open-Dev-Society/OpenStock](https://github.com/Open-Dev-Society/OpenStock) |
| **语言** | TypeScript (~93.4%), CSS (~6%), JavaScript (~0.6%) |
| **许可** | AGPL-3.0 |
| **Stars** | 12,311 ⭐ |
| **Fork** | 1,639 |
| **主站** | [openstock-ods.vercel.app](https://openstock-ods.vercel.app) |
| **组织** | Open Dev Society |

### 1.2 核心价值主张

OpenStock 的定位是**昂贵专有市场平台的开源替代方案**，提供以下能力：

- 实时股价追踪
- 个性化价格预警
- 详细公司数据洞察
- TradingView 级别图表
- AI 个性化邮件摘要

> ⚠️ **重要声明**：项目明确标注 OpenStock 为社区构建产品，**非券商**，市场数据因供应商规则和配置可能存在延迟，**不构成任何投资建议**。

---

## 二、技术栈全景

### 2.1 技术选型哲学

```
Next.js 15 (App Router)  ── 前端/全栈框架
      ↓
TypeScript                ── 类型安全
      ↓
Tailwind CSS v4          ── 样式（via @tailwindcss/postcss）
      ↓
shadcn/ui + Radix UI     ── UI 组件库
      ↓
Better Auth               ── 认证层（MongoDB 适配器）
MongoDB + Mongoose         ── 数据持久化
Inngest                   ── 事件驱动自动化 / Cron / AI 推理
Nodemailer                ── 邮件发送（Gmail Transport）
Finnhub API               ── 股票数据源
TradingView Widgets      ── K 线图 / 热力图 / 行情
```

### 2.2 依赖详解

**生产依赖（核心）：**

```json
{
  "next": "15.5.7",
  "react": "19.1.0",
  "better-auth": "^1.3.25",
  "inngest": "^3.47.0",
  "mongodb": "^6.20.0",
  "mongoose": "^8.19.0",
  "nodemailer": "^7.0.6",
  "cmdk": "^1.1.1",
  "react-hook-form": "^7.63.0",
  "date-fns": "^4.1.0",
  "@vercel/analytics": "^1.6.1"
}
```

**开发依赖亮点：**

```json
{
  "@tailwindcss/postcss": "^4",
  "tailwindcss": "^4",
  "vitest": "^4.1.0",
  "eslint": "^9"
}
```

---

## 三、架构设计

### 3.1 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (Client)                     │
│   Next.js 15 (App Router) + shadcn/ui + Tailwind CSS    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────────┐
│                    Vercel (Hosting)                      │
│   Next.js API Routes  │  Middleware (Route Protection)   │
│   Better Auth         │  Inngest Webhook Handler         │
└──────┬───────────────┬───────────────┬───────────────────┘
       │               │               │
┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼────────┐
│  MongoDB    │ │  Finnhub    │ │  Inngest      │
│  Atlas      │ │  API        │ │  Cloud        │
│  (持久化)    │ │  (实时数据)  │ │  (定时/事件)   │
└─────────────┘ └─────────────┘ └───────────────┘
                           │
              ┌────────────▼────────────┐
              │  Gemini / MiniMax / Siray │
              │  (AI 内容生成)            │
              └─────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │  Gmail (Nodemailer)      │
              │  Kit (邮件列表管理)        │
              └─────────────────────────┘
```

### 3.2 目录结构

```
OpenStock/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # 认证路由组
│   │   ├── sign-in/
│   │   ├── sign-up/
│   │   ├── forgot-password/
│   │   └── reset-password/
│   ├── (root)/                   # 受保护路由组
│   │   ├── page.tsx              # 首页/市场概览
│   │   ├── stocks/[symbol]/     # 个股详情页
│   │   ├── watchlist/            # 自选股管理
│   │   └── ...
│   └── api/
│       └── inngest/route.ts      # Inngest webhook 端点
├── components/
│   ├── ui/                       # shadcn/ui 基础组件
│   ├── forms/                    # 表单字段组件
│   ├── stocks/                   # 股票相关组件
│   ├── watchlist/                # 自选股组件
│   ├── Header.tsx
│   ├── SearchCommand.tsx         # Cmd+K 全局搜索
│   └── TradingViewWidget.tsx
├── database/
│   ├── mongoose.ts               # MongoDB 连接管理
│   └── models/
│       ├── watchlist.model.ts
│       └── alert.model.ts
├── hooks/
│   ├── useDebounce.ts
│   └── useTradingViewWidget.tsx
├── lib/
│   ├── actions/                  # Server Actions
│   │   ├── auth.actions.ts
│   │   ├── finnhub.actions.ts
│   │   ├── watchlist.actions.ts
│   │   ├── alert.actions.ts
│   │   └── user.actions.ts
│   ├── ai-provider.ts            # 多提供商 AI 抽象
│   ├── better-auth/auth.ts
│   ├── inngest/
│   │   ├── client.ts
│   │   ├── functions.ts          # 定时任务/事件处理器
│   │   └── prompts.ts            # AI Prompt 模板
│   ├── kit.ts                    # Kit (ConvertKit) API
│   └── nodemailer/
│       ├── index.ts
│       └── templates.ts
├── middleware/
│   └── index.ts                  # Next.js 中间件（路由保护）
├── scripts/                      # 工具脚本
│   ├── test-db.mjs
│   ├── migrate-users-to-kit.mjs
│   └── ...
└── __tests__/                    # Vitest 测试
```

---

## 四、核心模块深度解析

### 4.1 认证系统 — Better Auth

OpenStock 使用 **Better Auth** 替代 NextAuth.js，配合 MongoDB 适配器实现完整的邮箱/密码认证：

```typescript
// lib/better-auth/auth.ts
// Better Auth 配置核心片段
export const auth = betterAuth({
  database: mongoAdapter(mongoose.connection),
  emailAndPassword: {
    enabled: true,
  },
  session: {
    expiresIn: 60 * 60 * 24 * 7,  // 7 天
  },
});
```

**中间件保护逻辑：**

```typescript
// middleware/index.ts
import { getSessionCookie } from "better-auth/cookies";

export async function middleware(request: NextRequest) {
    const sessionCookie = getSessionCookie(request);
    if (!sessionCookie) {
        return NextResponse.redirect(new URL('/sign-in', request.url));
    }
    return NextResponse.next();
}

export const config = {
    matcher: [
        '/((?!api|_next/static|_next/image|favicon.ico|sign-in|sign-up|forgot-password|reset-password|assets).*)',
    ],
};
```

所有受保护页面（`app/(root)/`）通过中间件统一拦截，未登录用户强制跳转登录页。公开路由（`sign-in`、`sign-up` 等）排除在匹配规则之外。

### 4.2 数据层 — MongoDB + Mongoose

**数据模型设计：**

```typescript
// database/models/watchlist.model.ts
export interface WatchlistItem extends Document {
    userId: string;
    symbol: string;       // 大写，自动 trim
    company: string;
    addedAt: Date;
}

// 每个用户每只股票唯一，防止重复添加
WatchlistSchema.index({ userId: 1, symbol: 1 }, { unique: true });


// database/models/alert.model.ts
export interface IAlert extends Document {
    userId: string;
    symbol: string;
    targetPrice: number;
    condition: 'ABOVE' | 'BELOW';
    active: boolean;
    triggered: boolean;
    expiresAt: Date;
    createdAt: Date;
}

// 预警默认 90 天过期
expiresAt: {
    type: Date,
    default: () => new Date(Date.now() + 90 * 24 * 60 * 60 * 1000),
}
```

**连接管理（`database/mongoose.ts`）：**

```typescript
import mongoose from 'mongoose';

const MONGODB_URI = process.env.MONGODB_URI!;

export async function connectDB() {
    if (mongoose.connection.readyState >= 1) return;
    await mongoose.connect(MONGODB_URI);
}
```

### 4.3 事件驱动 — Inngest

Inngest 是 OpenStock 自动化能力的核心，支撑四大后台任务：

| 函数 ID | 类型 | 触发 | 功能 |
|---------|------|------|------|
| `sign-up-email` | 事件驱动 | `app/user.created` | AI 个性化欢迎邮件 |
| `weekly-news-summary` | Cron | `0 9 * * 1` (每周一 9AM) | 市场新闻摘要广播 |
| `check-stock-alerts` | Cron | `*/5 * * * *` (每 5 分钟) | 价格预警实时监控 |
| `check-inactive-users` | Cron | `0 10 * * *` (每天 10AM) | 唤醒沉睡用户 |

```typescript
// lib/inngest/functions.ts
export const inngest = new Inngest({ id: "openstock" });

export const signUpEmail = inngest.createFunction(
    { id: "sign-up-email", name: "Sign-up Email" },
    { event: "app/user.created" },
    async ({ event, step }) => {
        const userProfile = event.data;
        // Step 1: 调用 AI 生成个性化内容
        const intro = await step.run("generate-intro", async () => {
            return await callAIProviderWithFallback(
                buildWelcomePrompt(userProfile)
            );
        });
        // Step 2: 发送邮件
        await step.run("send-email", async () => {
            await sendWelcomeEmail(event.data.email, intro);
        });
    }
);
```

### 4.4 多提供商 AI 抽象

```typescript
// lib/ai-provider.ts
// 支持三种 AI 提供商自动切换
export type AIProviderName = "gemini" | "minimax" | "siray";

// 默认 Gemini，失败时自动切换 MiniMax / Siray
export async function callAIProviderWithFallback(
    prompt: string
): Promise<string> {
    const primary = (process.env.AI_PROVIDER as AIProviderName) || "gemini";
    const fallback = getFallbackProviderName(primary);

    try {
        return await callAIProvider(prompt, primary);
    } catch (primaryError) {
        console.error(`⚠️ ${primary} failed, switching to ${fallback}`);
        return await callAIProvider(prompt, fallback);
    }
}
```

这种设计确保 AI 功能**永不宕机**——任何一个提供商出现问题，流量自动切换到备用提供商，用户感知为零。

### 4.5 Finnhub 数据集成

```typescript
// lib/actions/finnhub.actions.ts
'use server';

// Finnhub API 调用封装，支持 Next.js React Cache
export async function searchStocks(query: string) {
    const url = `${FINNHUB_BASE_URL}/search?q=${encodeURIComponent(query)}&token=${NEXT_PUBLIC_FINNHUB_API_KEY}`;
    return fetchJSON<FinnhubSearchResult>(url);
}

export async function getStockQuote(symbol: string) {
    const url = `${FINNHUB_BASE_URL}/quote?symbol=${symbol}&token=${NEXT_PUBLIC_FINNHUB_API_KEY}`;
    return fetchJSON<FinnhubQuote>(url, 60); // 缓存 60 秒
}
```

### 4.6 全局搜索 — Cmd+K 命令面板

```typescript
// components/SearchCommand.tsx
// 基于 cmdk 库构建的即时搜索面板
// - 空闲时展示热门股票
// - 搜索时 Debounce 调用 Finnhub
// - 支持键盘导航
```

---

## 五、部署实践

### 5.1 Docker Compose 一键部署

```bash
# docker-compose.yml 结构
services:
  mongodb:
    image: mongo:7
    container_name: mongodb
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: example
    ports:
      - "27017:27017"
    volumes:
      - mongo-data:/data/db

  openstock:
    build: .
    ports:
      - "3000:3000"
    depends_on:
      mongodb:
        condition: service_healthy
    environment:
      - NODE_ENV=production

volumes:
  mongo-data:
```

```bash
# 启动
docker compose up -d mongodb
docker compose up -d --build
# 访问 http://localhost:3000
```

### 5.2 环境变量配置

```env
# .env 示例（本地开发）
NODE_ENV=development
MONGODB_URI=mongodb://root:example@mongodb:27017/openstock?authSource=admin

BETTER_AUTH_SECRET=your_better_auth_secret_min_32_chars
BETTER_AUTH_URL=http://localhost:3000

NEXT_PUBLIC_FINNHUB_API_KEY=your_finnhub_key
FINNHUB_BASE_URL=https://finnhub.io/api/v1

GEMINI_API_KEY=your_gemini_api_key
# AI_PROVIDER=gemini  # 可选: gemini | minimax | siray

NODEMAILER_EMAIL=youraddress@gmail.com
NODEMAILER_PASSWORD=your_gmail_app_password

INNGEST_SIGNING_KEY=your_inngest_signing_key
```

### 5.3 本地开发

```bash
# 克隆
git clone https://github.com/Open-Dev-Society/OpenStock.git
cd OpenStock

# 安装依赖
pnpm install

# 配置 .env
cp .env.example .env

# 验证数据库连接
pnpm test:db

# 启动 Next.js (Turbopack)
pnpm dev

# 单独启动 Inngest 开发服务器（支持本地 Cron/事件）
npx inngest-cli@latest dev
```

---

## 六、安全设计

### 6.1 认证安全

- **Better Auth** 负责密码哈希、会话管理、CSRF 保护
- 会话 Cookie HttpOnly + Secure，生产环境强制 HTTPS
- 路由中间件统一守卫，无遗漏

### 6.2 数据安全

- MongoDB 索引唯一性约束（用户 + 股票符号组合）
- 预警默认 90 天过期，避免过期数据残留
- 环境变量隔离密钥，不进入版本控制

### 6.3 第三方 API 安全

- Finnhub API Key 仅在服务端使用（`NEXT_PUBLIC_` 前缀用于客户端 Widget）
- AI API Key 多层回退设计，避免单点故障导致密钥暴露

### 6.4 AGPL-3.0 许可义务

> 若修改、分发或部署本项目（含作为 Web 服务部署），**必须**以相同许可证开源源代码并署名原作者。

---

## 七、二次开发指南

### 7.1 新增数据源

在 `lib/actions/finnhub.actions.ts` 中添加新的 Server Action：

```typescript
// 添加新的 Finnhub 端点
export async function getStockNews(symbol: string) {
    const url = `${FINNHUB_BASE_URL}/news?category=general&token=${FINNHUB_API_KEY}`;
    return fetchJSON(url);
}
```

### 7.2 新增 Inngest 定时任务

```typescript
// lib/inngest/functions.ts
export const myNewCron = inngest.createFunction(
    { id: "my-new-cron", name: "My New Cron" },
    { cron: "0 8 * * *" },  // 每天 8AM
    async ({ step }) => {
        const data = await step.run("fetch-data", async () => {
            // 你的业务逻辑
        });
        return data;
    }
);
```

### 7.3 添加新的 AI 提供商

```typescript
// lib/ai-provider.ts
// 在 getProviderConfig() 的 switch 中添加新 case
case "openai": {
    return {
        name: "openai",
        apiKey: process.env.OPENAI_API_KEY || "",
        baseUrl: "https://api.openai.com/v1",
        model: "gpt-4o",
    };
}
```

### 7.4 测试

```bash
# 运行所有测试
pnpm test

# 监听模式
pnpm test:watch

# 覆盖的测试文件
__tests__/
├── adanos.actions.test.ts
├── ai-provider.integration.test.ts
├── ai-provider.test.ts
├── reset-password-email.test.ts
└── utils.test.ts
```

---

## 八、与同类项目对比

| 维度 | OpenStock | Bloomberg Terminal | Yahoo Finance API |
|------|-----------|-------------------|-------------------|
| **成本** | 免费开源 | ~$25k/年 | 免费（限速）|
| **数据源** | Finnhub | 自有数据 | Yahoo |
| **图表** | TradingView Widget | 自研 | 基础图表 |
| **预警** | ✅ | ✅ | ❌ |
| **自托管** | ✅ | ❌ | ❌ |
| **AI 个性化** | ✅ Gemini/MiniMax | ❌ | ❌ |
| **许可** | AGPL-3.0 | 专有 | 专有 |

---

## 九、总结与展望

OpenStock 展示了如何用现代化的 Web 技术栈构建一个功能完整的金融数据平台：

- **Next.js 15 App Router** 提供了优秀的全栈开发体验
- **Inngest** 完美解决了定时任务和事件驱动的工程复杂度
- **多提供商 AI 抽象** 确保了生成式功能的稳定性
- **AGPL-3.0** 真正兑现了"开放数据属于所有人"的承诺

无论你是想学习金融数据平台架构、研究 Inngest 事件驱动设计，还是基于 OpenStock 构建自己的投资工具链，这个项目都值得深入研究。

---

## 参考资源

- **GitHub**: https://github.com/Open-Dev-Society/OpenStock
- **在线演示**: https://openstock-ods.vercel.app
- **API 文档**: https://openstock-ods.vercel.app/api-docs
- **Finnhub API**: https://finnhub.io
- **Better Auth**: https://www.better-auth.com
- **Inngest**: https://www.inngest.com
- **Open Dev Society**: https://github.com/open-dev-society
