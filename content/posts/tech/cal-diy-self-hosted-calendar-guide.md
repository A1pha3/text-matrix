---
title: "Cal.diy：开源社区版 Cal.com 完整自托管调度平台指南"
date: 2026-05-17T20:10:00+08:00
slug: "cal-diy-self-hosted-calendar-guide"
description: "Cal.diy 是 Cal.com 的开源社区分支，移除所有企业功能后完全 MIT 授权。本文解析其架构设计、本地开发环境搭建、Docker 部署流程及与 Cal.com 的核心差异，帮助个人开发者和小型团队快速部署私有调度系统。"
draft: false
categories: ["技术笔记"]
tags: ["Cal.diy", "Cal.com", "开源日历", "自托管", "Next.js", "tRPC", "Docker部署", "调度系统"]
---

## 项目概览

Cal.diy（calcom/cal.diy）是 Cal.com 的**开源社区维护分支**，定位为完全自托管的调度（scheduling）基础设施。该项目从 Cal.com 主代码库中移除了所有企业级功能，以 MIT License 重新发布，面向需要私有部署但不想受制于 Cal.com 商业模式的个人开发者和小型团队。

截至 2026 年 5 月，Cal.diy 在 GitHub 拥有 **43,003 Stars** 和 **13,351 Forks**，主要语言为 TypeScript，使用 Next.js + tRPC + Prisma 技术栈，支持 Docker 一键部署。

### 与 Cal.com 的核心区别

| 维度 | Cal.diy | Cal.com |
|------|---------|--------|
| 许可协议 | MIT（100% 开源） | Open Core（社区版免费，企业版付费） |
| 企业功能 | 无（Teams、Organizations、SSO/SAML 等已移除） | 完整保留 |
| 许可证密钥 | 不需要 | 需要（Enterprise 计划） |
| 托管版本 | 无，全部自托管 | 有（cal.com 官方托管） |
| 维护方 | 社区 | Cal.com 官方团队 |

Cal.diy 官方明确声明：**不适用于商业生产环境**，建议用于个人自用和非关键任务的私有部署。

---

## 技术架构

Cal.diy 的技术栈是现代全栈 Web 应用的典型组合：

### 核心框架

- **Next.js**：React 全栈框架，提供 SSR/SSG 混合能力，处理页面渲染与 API 路由
- **tRPC**：类型安全的 API 层，前后端共享 TypeScript 类型定义，消除 REST/GraphQL 的类型摩擦
- **Prisma**：ORM 工具，对接 PostgreSQL 数据库，提供类型安全的数据库查询
- **Tailwind CSS**：原子化 CSS 框架，负责全部样式实现

### 基础设施依赖

- **PostgreSQL（≥13）**：唯一支持的数据库，用于存储用户、事件、团队等业务数据
- **Daily.co**：视频会议集成层，提供内置的 video call 能力（Cal.diy 的事件类型支持"视频会议"集成）
- **NextAuth.js**：身份认证，支撑用户注册、登录、会话管理

### 关键设计决策

Cal.diy 采用** monorepo + 微前端**架构，项目结构位于 `packages/` 目录下，核心包包括：

- `@calcom/prisma` — 数据库 schema 与 Prisma client
- `@calcom/web` — 主 Web 应用（Next.js）
- `@calcom/ui` — 共享 UI 组件库

此外，大量集成（Google Calendar、Microsoft 365、Zoom、HubSpot 等）以独立 App Store 条目存在，可按需启用。

---

## 本地开发环境快速上手

### 前置依赖

- Node.js ≥ 18.x（推荐使用 nvm 管理版本）
- PostgreSQL ≥ 13.x
- Yarn（项目推荐）

### 标准安装流程

**Step 1：克隆代码库**

```bash
git clone https://github.com/calcom/cal.diy.git
cd cal.diy
```

**Step 2：安装依赖**

```bash
yarn
```

**Step 3：配置环境变量**

```bash
cp .env.example .env
```

需要手动生成两个关键密钥：

```bash
# 认证 Cookie 加密密钥
openssl rand -base64 32
# 数据库加密密钥（32 字节，AES256）
openssl rand -base64 24
```

将生成的密钥填入 `.env` 文件的 `NEXTAUTH_SECRET` 和 `CALENDSO_ENCRYPTION_KEY` 字段。

> Windows 用户注意事项：需要将 `packages/prisma/.env` 软链接替换为真实文件拷贝，以避免 Prisma 解析错误：
> ```bash
> rm packages/prisma/.env && cp .env packages/prisma/.env
> ```

**Step 4：数据库初始化**

开发环境使用 Prisma migrate：

```bash
yarn workspace @calcom/prisma db-migrate
```

**Step 5：启动开发服务器**

```bash
yarn dev
```

访问 [http://localhost:3000](http://localhost:3000)，首次访问会触发初始化向导，引导创建第一个用户账号。

### 一键启动方案（Docker）

如果本地已安装 Docker 和 Docker Compose，可以使用项目提供的 `yarn dx` 命令一键启动包含测试数据库的完整开发环境：

```bash
yarn dx
```

该命令会通过 Docker Compose 启动一个本地 PostgreSQL 实例，并预置多个测试账号：

| 邮箱 | 密码 | 角色 |
|------|------|------|
| `free@example.com` | `free` | Free 用户 |
| `pro@example.com` | `pro` | Pro 用户 |
| `admin@example.com` | `ADMINadmin2022!` | 管理员 |

---

## Docker 部署详解

生产环境推荐使用 Docker Compose 部署 Cal.diy，以下是完整的部署流程。

### 基础部署（docker compose up）

```bash
# 克隆代码库（含子模块）
git clone --recursive https://github.com/calcom/cal.diy.git
cd cal.diy

# 生成生产密钥
openssl rand -base64 32   # → NEXTAUTH_SECRET
openssl rand -base64 24   # → CALENDSO_ENCRYPTION_KEY

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入上述密钥和 DATABASE_URL

# 启动完整栈（数据库 + Web + Prisma Studio）
docker compose up -d
```

服务启动后：
- Web 应用：[http://localhost:3000](http://localhost:3000)
- Prisma Studio 数据库管理：[http://localhost:5555](http://localhost:5555)

首次访问同样会进入初始化向导，可直接跳过日历连接步骤（后续从 Settings > Integrations 补配）。

### 按需启动变体

Docker Compose 配置支持多种启动模式，通过不同的服务组合实现灵活部署：

```bash
# 仅启动 Web 应用（需已有外部数据库）
docker compose up -d calcom

# 启动 Web + Prisma Studio（连接远程数据库）
docker compose up -d calcom studio

# 完整栈（数据库 + Web + Prisma Studio）
docker compose up -d
```

### ARM 用户注意

使用 ARM 架构服务器（如 Apple Silicon Mac 或 ARM 服务器）时，pull 镜像需使用 `-arm` 后缀标签：

```bash
docker pull calcom/cal.diy:v5.6.19-arm
```

### 从源码构建 Docker 镜像

若需要自行构建镜像（非直接使用预编译镜像）：

```bash
# 1. 配置 .env
cp .env.example .env
# 编辑 .env 中的 DATABASE_URL 等配置

# 2. 启动临时本地数据库（构建过程需要可用数据库）
docker compose up -d database

# 3. 执行构建（需网络 bridge）
DOCKER_BUILDKIT=0 docker compose build calcom

# 4. 启动
docker compose up -d
```

### 关键环境变量

**运行时变量**（必须提供）：

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL 连接串 | `postgresql://user:pass@host:5432/cal` |
| `NEXTAUTH_SECRET` | Cookie 加密密钥 | `openssl rand -base64 32` 生成 |
| `CALENDSO_ENCRYPTION_KEY` | 数据加密密钥（32 字节） | `openssl rand -base64 24` 生成 |
| `NEXT_PUBLIC_WEBAPP_URL` | 站点基础 URL | `https://schedule.example.com` |

**可选变量**：

| 变量 | 说明 |
|------|------|
| `NEXT_PUBLIC_VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY` | Web Push 通知（需 web-push 生成） |
| `CALCOM_TELEMETRY_DISABLED=1` | 禁用匿名使用数据收集 |
| `NODE_TLS_REJECT_UNAUTHORIZED=0` | SSL 边缘终止（仅在负载均衡处理 HTTPS 时使用） |

### 更新部署

```bash
docker compose down
docker compose pull
docker compose up -d
```

每次更新后会自动执行数据库迁移（通过 `db-deploy`）。

---

## 其他部署平台

除了 Docker Manual 部署，Cal.diy 官方还支持以下一键部署平台：

- **Railway** — 点击 README 中的 "Deploy on Railway" 按钮，附带[详细博客教程](https://blog.railway.app/p/calendso)
- **Northflank** — 提供[部署指南](https://northflank.com/guides/deploy-calcom-with-northflank)
- **Vercel** — 需要 Vercel Pro Plan（免费计划 serverless function 数量限制不足）
- **Render** — 通过 Docker 镜像部署
- **Elestio** — 一键部署托管服务

---

## 集成生态

Cal.diy 保留了 Cal.com 的 App Store 体系，支持多种第三方服务集成，每个集成需要各自 OAuth 凭证配置。主要集成包括：

**日历 / 视频会议**
- Google Calendar / Outlook Calendar（日历双向同步）
- Zoom、Microsoft Teams、GoToMeeting、VideoCam 等视频工具
- Daily.co（内置）

**CRM 与生产力**
- HubSpot、ZohoCRM、Pipedrive（HTTPS://cal.com/sales）
- Notion（文档嵌入）

**日历生态**
- Calendly（迁移工具）
- 数十种其他主流 SaaS 工具

配置集成需要将对应的 Client ID / Secret 填入 `.env` 文件，详细步骤见项目 README。

---

## 适用场景与边界

### 适合的场景

- 个人或小团队自建调度系统，数据完全私有
- 在私有网络/防火墙内运行，不希望依赖外部服务
- 有 Docker 部署经验，需要快速搭建内部预约平台
- 开发者基于 Cal.diy 做二次开发或定制

### 边界与局限

- **不是生产级商业调度解决方案**：官方明确不建议用于商业生产环境，缺乏 SLA 支持和高级企业功能（SSO、审计日志、团队管理等）
- **没有托管版本**：所有实例必须自行维护服务器，包括安全更新、数据库备份、SSL 证书续期
- **企业功能缺失**：Teams、Organizations、Workflows（自动化）、Insights（分析）等 Cal.com 企业版功能已全部移除，且不会以开源形式提供
- **视频集成依赖外部服务**：视频会议能力依赖 Daily.co 或其他第三方视频 API，需自行注册账号并配置

---

## 常见问题

### 数据库迁移失败

某些版本在创建用户时若 `metadata` 字段为空可能导致报错。解决方式：使用空 JSON 对象 `{}` 作为值，同时 id 字段留空让自增长处理。

### CLIENT_FETCH_ERROR（认证错误）

当 Docker 容器内无法解析本地开发机器的域名时会出现。例如 `testing.localhost:3000` 在容器内无法解析。解决方法是在 `.env` 中明确设置 `NEXTAUTH_URL` 指向容器自身地址：

```
NEXTAUTH_URL=http://localhost:3000/api/auth
```

### 内存不足

Node.js 默认内存限制可能不足以支撑大型 monorepo 项目的开发构建。建议在 shell 配置中添加：

```bash
export NODE_OPTIONS="--max-old-space-size=16384"
```

### E2E 测试浏览器未安装

如果 `yarn test-e2e` 报 Chromium 可执行文件不存在，执行：

```bash
npx playwright install
```

---

## 总结

Cal.diy 提供了一条**零成本、完全私有**的调度系统搭建路径。43K Stars 的社区规模意味着它在 GitHub 拥有足够的可见度和活跃维护，但使用前必须理解它与 Cal.com 商业版本之间的本质差异——它跟 Cal.com 免费版不同——是**完整 MIT 授权的独立开源项目**，专为自托管场景设计。

如果你有 Docker 部署经验且需要私有调度基础设施，Cal.diy 是目前开源社区中门槛最低、文档最完整的选项之一。如果你需要商业级 SLA、SSO 或托管服务，直接选择 [Cal.com](https://cal.com) 的付费计划是更合适的路径。

---

**延伸资源**

- GitHub 仓库：https://github.com/calcom/cal.diy
- 官方讨论区：https://github.com/calcom/cal.diy/discussions
- Docker 镜像：https://hub.docker.com/r/calcom/cal.diy
- Cal.com 官网：https://cal.com