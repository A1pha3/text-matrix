---
title: "OpenStock：开源股市数据追踪平台，12k星的新选择"
date: 2026-05-27T09:25:00+08:00
slug: "openstock-open-source-stock-market-platform"
description: "OpenStock是由Open Dev Society打造的开源股市追踪平台，基于Next.js 15 + shadcn/ui + MongoDB构建，接入Finnhub实时行情和TradingView图表，支持自部署、个性化提醒和公司基本面数据，旨在成为昂贵付费平台的开源替代方案。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "股市", "Next.js", "TypeScript", "Finnhub", "自托管"]
---

## 项目概览

**OpenStock** 是由 Open Dev Society 社区开发的开源股市追踪平台，目标是为普通用户提供一款永久免费的数据追踪工具，替代彭博终端这类价格高昂的闭源方案。

### 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | 12,132（今日趋势榜） |
| Fork 数 | 1,627 |
| 主要语言 | TypeScript |
| 许可证 | AGPL-3.0 |
| 技术栈 | Next.js 15 / shadcn/ui / MongoDB / Finnhub |
| 官网 | [openstock-ods.vercel.app](https://openstock-ods.vercel.app) |

### 定位一句话

> 构建透明、开源、永远免费的股市数据平台，让信息不再被付费墙隔离。

---

## 核心能力

### 实时行情追踪

OpenStock 接入 **Finnhub API**，提供全球主要交易所的股票、指数行情数据。用户可自定义关注列表，实时盯盘。

### TradingView 图表集成

行情页面直接嵌入 **TradingView** 交互式图表，支持技术指标叠加，界面体验接近专业交易终端。

### 个性化提醒

支持价格提醒、涨跌幅提醒等触发条件，通过邮件发送通知。数据基于 Finnhub 规则会有延迟。

### 公司基本面数据

每个标的均提供公司简介、财务数据等基础信息，方便基本面分析。

### 开源自部署

代码完全开源，支持 Docker 一键部署，自建数据服务，不依赖平台方的服务端。

---

## 技术架构

### 技术栈一览

| 层级 | 技术选型 |
|------|---------|
| 前端框架 | Next.js 15 (App Router) + React 19 |
| UI 组件 | shadcn/ui + Radix UI + Tailwind CSS v4 |
| 类型安全 | TypeScript |
| 数据库 | MongoDB + Mongoose ODM |
| 认证 | Better Auth（邮箱/密码）+ MongoDB adapter |
| 实时数据 | Finnhub API |
| 图表 | TradingView embeddable widgets |
| 后端任务 | Inngest（事件驱动 + cron + AI 推理） |
| 邮件通知 | Nodemailer（Gmail transport） |

### 项目结构

```
OpenStock/
├── app/               # Next.js App Router
├── components/       # shadcn/ui 组件
├── lib/              # 工具函数
├── models/           # MongoDB Mongoose 模型
├── scripts/          # 工具脚本
├── public/           # 静态资源
└── README.md
```

### 数据流向

1. 用户在前端添加股票关注
2. 数据存入 MongoDB（自部署场景）或调用 Finnhub API
3. Inngest cron 定时任务拉取最新行情
4. 触发条件满足时，通过 Nodemailer 发送邮件提醒

---

## 快速开始

### Docker 部署（推荐）

```bash
git clone https://github.com/Open-Dev-Society/OpenStock.git
cd OpenStock
docker compose up -d
```

### 环境变量

```bash
# .env.local
MONGODB_URI=mongodb://localhost:27017/openstock
FINNHUB_API_KEY=your_finnhub_api_key
BETTER_AUTH_SECRET=your_secret
# Nodemailer (可选，启用邮件提醒)
SMTP_USER=your@gmail.com
SMTP_PASS=your_app_password
```

### Finnhub API

Finnhub 提供免费层，每日请求限额内足够个人用户使用。注册地址：[finnhub.com](https://finnhub.com)

---

## 适用边界

### 适合人群

- 想自托管个人股票追踪工具的技术用户
- 需要免费股市数据的独立开发者
- 学习 Next.js 15 全栈项目实战的学习者

### 不适合场景

- 替代专业交易终端（数据延迟，无 L2 盘口）
- 高频交易（实时性不足）
- 需要保证数据100%准确性的投资决策

### 注意事项

> ⚠️ 项目属于社区开发非券商。行情数据存在延迟，不构成投资建议。用户需自行承担使用风险。

---

## 为什么值得关注

OpenStock 的核心价值不在于技术突破，而在于**开源替代**的理念。传统股市数据平台年费动辄数万，而 OpenStock 提供了一个可自部署、可审计、可定制的免费方案。

对于 AI + 金融科技的结合点来说，Inngest 已内置对 Gemini AI 推理的接入能力，未来可扩展 AI 驱动的选股/分析逻辑。

---

## 竞争对比

| 平台 | 费用 | 自托管 | 开源 | 技术栈 |
|------|------|--------|------|--------|
| Bloomberg Terminal | 年费数万元 | ❌ | ❌ | 闭源 |
| TradingView | 免费层有限制 | ❌ | ❌ | 闭源SaaS |
| **OpenStock** | **免费（含限制）** | **✅** | **✅** | Next.js+TypeScript |

---

## 阅读路径

1. 先体验 [在线 demo](https://openstock-ods.vercel.app)
2. 阅读 [GitHub README](https://github.com/Open-Dev-Society/OpenStock) 了解架构
3. 参考 `docker-compose.yml` 完成自部署
4. 按需扩展 Inngest AI 推理流程

> 本项目属于非AI项目的纯金融工具，本次写入为趋势覆盖。OpenStock 的 AGPL-3.0 协议要求网络部署时必须开源。