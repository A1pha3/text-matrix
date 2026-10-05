---
title: "Cal.diy：开源社区版 Cal.com 完整自托管调度平台指南"
date: 2026-05-17T20:10:00+08:00
lastmod: 2026-09-28T11:30:00+08:00
slug: "cal-diy-self-hosted-calendar-guide"
github_repo: "calcom/cal.diy"
source_key: "gh:calcom/cal.diy"
description: "Cal.diy 是 Cal.com 剥离全部企业代码后的 MIT 社区版。本文对照 2026-09-28 的仓库现状与 README，梳理它与 Cal.com 的差别、monorepo 结构、本地开发与 Docker 部署全流程、经核实的集成清单与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["自托管", "Next.js"]
---

## 学习目标

读完本文应能：

1. 说清 Cal.diy 与 Cal.com 在许可协议、企业功能、托管方式、维护方四个维度上的差别，以及官方对商业用途的明确建议
2. 描述 Cal.diy 的技术栈与 Turborepo monorepo 结构，知道 `db-migrate`、`dx` 这些命令分别定义在哪个包里
3. 用手动流程或 `yarn dx` 一键搭起本地开发环境，拿到五个预置测试账号
4. 用 Docker Compose 完成一次面向自用的完整部署，知道五个服务各自的职责和三种启动变体
5. 遇到 metadata 报错、CLIENT_FETCH_ERROR、VAPID 缺钥、内存不足这些高频问题时，知道去哪里改

---

## 目录

- [学习目标](#学习目标)
- [先说结论](#先说结论)
- [数据与版本口径](#数据与版本口径)
- [与 Cal.com 的区别](#与-calcom-的区别)
- [技术栈与仓库结构](#技术栈与仓库结构)
- [本地开发环境](#本地开发环境)
- [Docker 部署](#docker-部署)
- [托管平台一键部署](#托管平台一键部署)
- [集成生态](#集成生态)
- [适用边界](#适用边界)
- [常见问题排查](#常见问题排查)
- [自测题](#自测题)
- [参考](#参考)

---

## 先说结论

Cal.diy 是 Cal.com 官方组织维护的社区版：同一套调度系统的代码，剥掉全部企业功能后按 MIT 发布。README 的自我定义是一句话——"a fork of Cal.com with all enterprise/commercial code removed"，社区驱动的完全开源调度平台。

它的账很清楚。得到的是 100% MIT：没有 Open Core 切分，不需要许可证密钥，开箱即用。放弃的是 Teams、Organizations、Insights、Workflows、SSO/SAML 这些企业功能——README 写明它们已从代码中移除——以及任何官方托管：没有托管版，服务器、安全更新、数据库备份、证书续期全部自理。

还有一条立场写在 README 最顶部：WARNING 节的原话是"strictly recommended for personal, non-production use"（严格建议用于个人的、非生产的场景）；TIP 节则指路——要商业和企业级的调度基础设施，请用 Cal.com，官方托管或申请 on-prem 企业接入。

所以这篇文章回答三件事：它跟 Cal.com 到底差在哪；从本地开发到 Docker 部署的完整路径怎么走；哪些坑 README 之外没人告诉你。

## 数据与版本口径

截至 2026-09-28 的 GitHub API 快照：48,709 stars、15,232 forks、1,439 个 open issue，主语言 TypeScript。仓库创建于 2021-03-22——比 Cal.diy 这个名字老得多，项目前身叫 Calendso，旧名还留在默认数据库名（`calendso`）、Railway 教程链接（`blog.railway.app/p/calendso`）和 `.env.example` 里引用的旧仓库 issue 链接中。最近一次推送是 2026-09-26，维护活跃。

最新 release 是 v6.2.0，发布于 2026-03-01，此前是一条密集的 v6.1.x 补丁线。README 的 Docker 小节拿 `v5.6.19-arm` 举 ARM 镜像的例子，那只是写法示例，实际拉镜像时把 `{version}` 换成你要的 tag 即可。

本文的命令与结论全部对 2026-09-28 的 main 分支、README 和 `docker-compose.yml` 核对过。stars/forks 是瞬时值，别当精确数用。

## 与 Cal.com 的区别

| 维度 | Cal.diy | Cal.com |
|------|---------|--------|
| 许可协议 | MIT，无 Open Core 切分 | Open Core（社区版免费，企业功能付费） |
| 企业功能 | Teams、Organizations、Insights、Workflows、SSO/SAML 等已移除 | 完整保留 |
| 许可证密钥 | 不需要 | 企业功能需要 |
| 托管版本 | 无，只能自托管 | 官方托管，另有 on-prem 企业接入 |
| 维护方 | 社区 | Cal.com 官方团队 |

两点补充。其一，两边代码是两条线：README 的 Contributing 一节写明"Contributions to this repo do not flow to Cal.com's production platform"——对 Cal.diy 的贡献不会回流到 Cal.com 生产平台。其二，README 用加粗字重申过定位：Cal.diy 是 self-hosted 项目，没有 hosted/managed 版本，你跑在自己的基础设施上。

## 技术栈与仓库结构

README 列出的 Built With 六项：Next.js、tRPC、React、Tailwind CSS、Prisma、Daily.co。运行前提：Node.js ≥ 18、PostgreSQL ≥ 13、Yarn（推荐）。Yarn 版本被 `package.json` 钉死——`engines` 要求 `yarn >= 4.12.0`，`packageManager` 字段固定 `yarn@4.12.0`，脚本经由 Turborepo 分发（`yarn dx`、`yarn build` 实际都是 `turbo run` 代理）。

仓库是标准的 monorepo，`apps/` 放应用，`packages/` 放共享包：

| 路径 | 内容 |
|------|------|
| `apps/web` | 主应用（`@calcom/web`），Next.js，默认端口 3000 |
| `apps/api` | API v2，带独立 Dockerfile（Docker 部署里的 `calcom-api` 服务构建自它） |
| `apps/docs` | 文档站 |
| `packages/prisma` | 数据库 schema 与迁移脚本（`@calcom/prisma`） |
| `packages/app-store` | 全部第三方集成的实现，一个集成一个目录 |
| `packages/` 其余 | `trpc`、`ui`、`features`、`lib`、`emails`、`embeds`、`kysely`、`platform` 等 18 个共享包 |

一条更正常出现在旧资料里：主应用在 `apps/web`，不在 `packages/` 下；这套架构是 Turborepo + Yarn Workspaces 的 monorepo，没有微前端。认证用 NextAuth（对应 `NEXTAUTH_SECRET`、`NEXTAUTH_URL` 两个变量）；数据库只支持 PostgreSQL。

## 本地开发环境

### 前置依赖

- Node.js ≥ 18（README 要求；仓库建议用 nvm 对齐版本）
- PostgreSQL ≥ 13（手动安装路径才需要，`yarn dx` 会用 Docker 起一个）
- Yarn 4（`corepack` 可直接启用 4.12.0）
- `yarn dx` 路径另需 Docker 和 Docker Compose

Windows 用户在克隆这一步就要注意：README 要求在管理员权限的 Git Bash 里执行 `git clone -c core.symlinks=true https://github.com/calcom/cal.diy.git`，否则仓库里的软链接处理不了。

### 手动安装

```bash
git clone https://github.com/calcom/cal.diy.git
cd cal.diy
yarn
cp .env.example .env
```

`.env` 里有两个密钥必须自己生成：

```bash
# 认证 Cookie 加密密钥 → NEXTAUTH_SECRET
openssl rand -base64 32
# 凭证加密密钥（AES-256 要求 32 字节）→ CALENDSO_ENCRYPTION_KEY
openssl rand -base64 24
```

`.env.example` 默认的 `DATABASE_URL` 指向 `localhost:5450`——那是 `yarn dx` 用 Docker 起的本地库端口。走手动路径就把它改成你自己的 PostgreSQL 连接串，然后跑迁移：

```bash
# 开发环境
yarn workspace @calcom/prisma db-migrate
# 生产语义（只应用已有迁移，不新建）
yarn workspace @calcom/prisma db-deploy
```

启动开发服务器：

```bash
yarn dev
```

打开 [http://localhost:3000](http://localhost:3000) 即可。

Windows 还有一处：`packages/prisma/.env` 是个软链接，PowerShell 原生环境处理不了，Prisma 会报 `unexpected character / in variable name`。README 给的解法是把它换成真实拷贝：

```bash
rm packages/prisma/.env && cp .env packages/prisma/.env
```

### 第一个用户

开发环境没有初始化向导，README 给了两种建用户的方式。

方式一，手工建。运行 `yarn db-studio` 打开 Prisma Studio，在 `User` 模型里新增记录：填 `email`、`username`、`password`（要先过 BCrypt 加密再填），`metadata` 字段必须填空 JSON 对象 `{}`，保存。注意新建用户默认是 TRIAL 计划，想改默认值去 `packages/prisma/schema.prisma`。

方式二，灌种子数据：

```bash
cd packages/prisma
yarn db-seed
```

### yarn dx 一键启动

根目录的 `yarn dx` 实际是 `turbo run dx`，真正干活的是 `packages/prisma` 里的 `db-setup` 脚本链：用 Docker Compose 起一个 PostgreSQL 18 实例（映射到 5450 端口，避免和本机已有实例冲突），执行迁移，再灌种子用户；随后 `apps/web` 的 `yarn dev` 启动主应用。

README 给出的预置账号是五个：

| 邮箱 | 密码 | 角色 |
|------|------|------|
| `free@example.com` | `free` | Free 用户 |
| `pro@example.com` | `pro` | Pro 用户 |
| `trial@example.com` | `trial` | 试用用户 |
| `admin@example.com` | `ADMINadmin2022!` | 管理员 |
| `onboarding@example.com` | `onboarding` | 未完成引导的用户 |

凭据同时会打印在控制台。想看全部种子用户的细节，跑 `yarn db-studio` 后访问 [http://localhost:5555](http://localhost:5555)。开发期要收发邮件（E2E 测试设了 `E2E_TEST_MAILHOG_ENABLED=1` 时必须），按 README 起一个 MailHog 容器：

```bash
docker pull mailhog/mailhog
docker run -d -p 8025:8025 -p 1025:1025 mailhog/mailhog
```

### 两个开发期实用配置

大仓库构建容易撞 Node 默认内存上限，README 的建议是：

```bash
export NODE_OPTIONS="--max-old-space-size=16384"
```

数值按自己内存改。要调 tRPC 查询和变更的日志级别，在 `.env` 里设 `NEXT_PUBLIC_LOGGER_LEVEL`，取值 0–6 对应 silly 到 fatal，设 N 则记录 N 及以上级别。不想装本地环境，README 也提供了 Gitpod 一键入口，浏览器里直接得到配好的工作区。

## Docker 部署

### compose 里的五个服务

`docker-compose.yml` 定义了五个服务，比"数据库 + Web + Studio"的老描述多了两个：

| 服务 | 镜像/构建 | 端口 | 说明 |
|------|-----------|------|------|
| `database` | postgres 官方镜像 | 不对外 | 示例凭据 `unicorn_user` / `magical_password`，默认库 `calendso` |
| `redis` | `redis:latest` | 6379（`REDIS_PORT` 可改） | `calcom-api` 的依赖 |
| `calcom` | `calcom.docker.scarf.sh/calcom/cal.diy` | 3000 | Web 主应用，只依赖 `database` |
| `calcom-api` | 由 `apps/api/v2/Dockerfile` 构建 | 80（`API_PORT` 可改） | API v2 |
| `studio` | 同 `calcom` 镜像 | 5555 | Prisma Studio，compose 注释建议生产环境删掉这个服务 |

镜像入口有两个：compose 默认拉取 `calcom.docker.scarf.sh/calcom/cal.diy`（Scarf 提供的分发统计入口），Docker Hub 上的同名镜像页面是 `calcom/cal.diy`。

### 标准部署流程

```bash
# 克隆（含子模块）
git clone --recursive https://github.com/calcom/cal.diy.git
cd cal.diy

# 配置环境变量
cp .env.example .env
# 生成两个密钥（同本地开发一节）
openssl rand -base64 32   # → NEXTAUTH_SECRET
openssl rand -base64 24   # → CALENDSO_ENCRYPTION_KEY

# 启动完整栈
docker compose up -d
```

README 特别警告：生产环境沿用 `.env` 里的 `secret` 占位符是安全风险，两个密钥必须换掉。Web 起在 [http://localhost:3000](http://localhost:3000)，首次访问会出现初始化向导，定义第一个用户。向导里的"Connect your Calendar"一步可以跳过——直接访问 `<WEBAPP_URL>/event-types` 进面板，日历以后从 Settings > Integrations 补配。

如果浏览器推送报 `Error: No key set vapidDetails.publicKey`，是 Web Push 的 VAPID 密钥没配，生成后填入 `.env`：

```bash
npx web-push generate-vapid-keys
# → NEXT_PUBLIC_VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY
```

有一处 README 没写透的坑。`calcom` 服务的 `DATABASE_URL` 由 `${POSTGRES_USER}`、`${POSTGRES_PASSWORD}`、`${DATABASE_HOST}`、`${POSTGRES_DB}` 四个变量插值而来，而 compose 的 `environment` 节优先于 `env_file`——光改 `.env` 里的 `DATABASE_URL` 对 `calcom` 容器不生效。这四个变量 `.env.example` 里没有预置，用内置数据库时往 `.env` 补上这一组（与 `database` 服务的默认值对齐）：

```env
POSTGRES_USER=unicorn_user
POSTGRES_PASSWORD=magical_password
POSTGRES_DB=calendso
DATABASE_HOST=database
```

换了自己的数据库就填自己的值。不补的话，这几个变量插值为空串，容器拿到的是一条连不上的连接串。

### 三种启动变体

```bash
# 完整栈（README 表述：本地数据库 + Web + Prisma Studio）
docker compose up -d

# Web + Studio，连远程数据库（DATABASE_URL 指向已有库）
docker compose up -d calcom studio

# 只起 Web
docker compose up -d calcom
```

调试时把 `-d` 去掉即可前台运行看日志。

### ARM 用户

ARM 架构（Apple Silicon、ARM 服务器）拉镜像用 `{version}-arm` 后缀，README 的示例写法：

```bash
docker pull calcom/cal.diy:v5.6.19-arm
```

`v5.6.19` 只是 README 里的示例版本号，按需替换。

### 从源码构建

构建期就要求有一个可用的数据库（README 的说法是"应用配置要求"）：要么 `.env` 里配好远程库，要么先起一个本地库再构建：

```bash
docker compose up -d database
DOCKER_BUILDKIT=0 docker compose build calcom
docker compose up -d
```

`DOCKER_BUILDKIT=0` 是必须的——BuildKit 下构建期用不了网络 bridge 连数据库，README 注明这个要求未来会移除。

### 环境变量清单

运行时变量（README 的 Important Run-time variables 表）：

| 变量 | 说明 | 必填 | 默认 |
|------|------|------|------|
| `DATABASE_URL` | 数据库连接串；用连接池时指向池 | 是 | `postgresql://unicorn_user:magical_password@database:5432/calendso` |
| `NEXT_PUBLIC_WEBAPP_URL` | 站点基础 URL；与构建值不一致时容器启动会先做一轮静态文件替换，稍慢 | 否 | `http://localhost:3000` |
| `NEXTAUTH_URL` | 认证服务地址 | 否 | `{NEXT_PUBLIC_WEBAPP_URL}/api/auth` |
| `NEXTAUTH_SECRET` | Cookie 加密密钥，须与构建时一致 | 是 | `secret` |
| `CALENDSO_ENCRYPTION_KEY` | 凭证加密密钥（AES-256 要求 32 字节），须与构建时一致 | 是 | `secret` |

自建镜像时的构建时变量（README 的 Build-time variables 表）：

| 变量 | 说明 | 必填 | 默认 |
|------|------|------|------|
| `DATABASE_URL` | 构建期就要能连上 | 是 | 同上 |
| `MAX_OLD_SPACE_SIZE` | Node 构建内存上限（MB） | 是 | 4096 |
| `NEXTAUTH_SECRET` | 烧进构建产物，运行时必须一致 | 是 | `secret` |
| `CALENDSO_ENCRYPTION_KEY` | 同上 | 是 | `secret` |
| `NEXT_PUBLIC_WEBAPP_URL` | 注入静态文件 | 否 | `http://localhost:3000` |
| `NEXT_PUBLIC_WEBSITE_TERMS_URL` / `NEXT_PUBLIC_WEBSITE_PRIVACY_POLICY_URL` | 条款与隐私政策链接 | 否 | 空 |
| `CALCOM_TELEMETRY_DISABLED` | 设 `1` 关闭匿名使用数据收集 | 否 | 空 |

### 更新与自动迁移

```bash
docker compose down
docker compose pull
# 按需更新 .env
docker compose up -d
```

不需要手动跑数据库迁移。容器入口脚本 `scripts/start.sh` 每次启动都做五件事：等数据库就绪、执行 `prisma migrate deploy`、重跑 App Store 种子数据、把构建时烧进静态文件的 `WEBAPP_URL` 占位符替换成运行时值（这就是上面说"启动稍慢"的原因）、最后 `yarn start`。升级只管换镜像。

### 两个安全相关开关

Web 应用放在处理 SSL 的负载均衡后面时，需要设 `NODE_TLS_REJECT_UNAUTHORIZED=0`，否则请求会被拒。README 原话的告诫是：只在你知道自己在做什么、并且信任前面的负载均衡时才这么做。

内容安全策略默认关闭，设 `CSP_POLICY="non-strict"` 可启用——除 `style-src` 允许 `unsafe-inline` 外遵循 Strict CSP。目前的覆盖范围：登录页全量启用，其余 SSR 页以 report-only 模式运行，SSG 页不支持。

## 托管平台一键部署

不想自己管 Docker 的话，README 给了五个入口：

- **Railway** — 一键部署模板，Railway 团队还有一篇详细的[博客教程](https://blog.railway.app/p/calendso)
- **Northflank** — 官方[部署指南](https://northflank.com/guides/deploy-calcom-with-northflank)
- **Vercel** — 需要 Pro 计划，免费计划的 serverless 函数数量不够用
- **Render** — 部署按钮指向 `calcom/docker` 仓库的模板
- **Elestio** — 托管一键部署

## 集成生态

机制先讲清楚：每个集成的实现都放在 `packages/app-store` 下自成目录；启用一个集成，要拿对应平台的 OAuth 凭证填进 `.env`（README 逐个写了申请步骤），然后刷新 App Store：

```bash
cd packages/prisma
yarn seed-app-store
```

README 手把手讲解了十一个集成的凭证申请：Google Calendar（`GOOGLE_API_CREDENTIALS`，整段 JSON）、Microsoft Graph、Zoom、Daily.co（`DAILY_API_KEY`，买了 Scale 计划再加 `DAILY_SCALE_PLAN=true` 启用录制等能力）、Basecamp 3、HubSpot、Webex、ZohoCRM、Zoho Calendar、Zoho Bigin、Pipedrive。

数量远不止这些。把 `packages/app-store` 目录数一遍（2026-09-28），共 154 个条目，其中应用目录过百，按类挑代表性的：

- **日历**：Google、Outlook（`office365calendar`）、CalDAV、Exchange 2013/2016、ICS 订阅、Apple、飞书（`feishucalendar` / `larkcalendar`）、Zoho
- **视频**：Daily.co（内置默认）、Zoom、Teams（`office365video`）、Google Meet、Jitsi、Whereby、Webex、Mirotalk、Element Call、Nextcloud Talk
- **CRM**：HubSpot、Salesforce、Pipedrive、Zoho CRM、Zoho Bigin、Close.com、Attio
- **支付**：Stripe、PayPal、BTCPay Server、HitPay
- **自动化**：Zapier、Make、n8n、Pipedream
- **分析**：Plausible、PostHog、Fathom、GA4、Matomo、Umami

另有一个可选项：Unkey 限流（`UNKEY_ROOT_KEY`），README 注明不配置也不影响自托管运行。

一处在旧资料里常见的错误要指出：GoToMeeting、VideoCam、Notion、Calendly 这些条目已不在当前的 `packages/app-store` 目录里，别再照着旧清单申请凭证。

## 适用边界

适合的场景：

- 个人自用、非关键业务的私有预约页——这是 README 明示的定位
- 数据必须完全留在自己服务器或内网里
- 想在 MIT 代码上做二次开发，或想研究 Cal.com 系调度系统的实现

不适合的场景：

- 商业与生产用途。README 的 TIP 明确让商业需求去找 Cal.com（托管或 on-prem 企业接入），WARNING 则把 Cal.diy 限定在 personal、non-production
- 依赖 SSO/SAML、Teams、Organizations、Insights、Workflows 的组织——这些代码已从仓库移除
- 想要"零运维"的团队。没有官方托管，安全更新、备份、证书续期都归你

还有一点容易忽略：对 Cal.diy 仓库的贡献不会回流到 Cal.com 生产平台（README Contributing 一节原话），选哪条线就是哪条线。

## 常见问题排查

**创建用户报 `Invalid 'prisma.user.create()'`** — 某些版本在 `metadata` 字段为空时会报错。README 的解法：`metadata` 填空 JSON 对象 `{}`；`id` 是自增的，留空即可。

**Docker 日志报 `CLIENT_FETCH_ERROR`** — 容器内的 DNS 和你的开发机不一定一致，默认认证回调拿 `WEBAPP_URL` 当基底地址解析失败（日志里常见 `getaddrinfo ENOTFOUND testing.localhost`）。在 `.env` 里明确指定：

```env
NEXTAUTH_URL=http://localhost:3000/api/auth
```

**构建或开发时内存不足** — Node 默认堆上限撑不住这个 monorepo，按上文设 `NODE_OPTIONS="--max-old-space-size=16384"`（自建镜像则调构建时变量 `MAX_OLD_SPACE_SIZE`）。

**`yarn test-e2e` 报 Chromium 可执行文件不存在** — Playwright 的浏览器没装，执行：

```bash
npx playwright install
```

**PowerShell 下迁移报 `Environment variable not found: DATABASE_DIRECT_URL`** — Turbo 没能把根目录 `.env` 的变量注入。README 的绕法是进 `packages/prisma` 直接跑：

```powershell
cd packages/prisma
$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/postgres"; $env:DATABASE_DIRECT_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/postgres"
npx prisma db push
cd ../..
```

**Docker 全栈起不来、Web 连不上数据库** — 先查上文"标准部署流程"里的 compose 插值四变量（`POSTGRES_USER` 等）是否已补进 `.env`。

## 自测题

### 题 1：与 Cal.com 的取舍

Cal.diy 与 Cal.com 在许可、企业功能、托管、维护方四个维度上各有什么差别？什么情况必须选 Cal.com？

<details>
<summary>参考答案</summary>

Cal.diy 是 100% MIT、无 Open Core 切分、无需许可证密钥、无托管版、社区维护；Cal.com 是 Open Core、企业功能完整、有官方托管和 on-prem 企业接入、官方团队维护。需要 SSO/SAML、Teams、Organizations、Insights、Workflows 或商业级支持时，只能选 Cal.com——这些能力已从 Cal.diy 代码中移除。
</details>

### 题 2：技术栈与结构

Cal.diy 的主应用代码在仓库哪个目录？Next.js + tRPC + Prisma 各自解决什么问题？

<details>
<summary>参考答案</summary>

主应用在 `apps/web`（`@calcom/web`），不在 `packages/` 下；整体是 Turborepo + Yarn Workspaces 的 monorepo。Next.js 承担页面渲染与 API 路由；tRPC 让前后端共享 TypeScript 类型，省掉接口层的类型对账；Prisma 提供类型安全的数据库访问，schema 集中在 `packages/prisma`。
</details>

### 题 3：部署流程

从克隆到第一个预约，Docker 部署有哪几步？哪一处最容易出问题？

<details>
<summary>参考答案</summary>

克隆（`--recursive`）→ 生成并填入 `NEXTAUTH_SECRET` 与 `CALENDSO_ENCRYPTION_KEY` → 补 compose 插值所需的 `POSTGRES_USER` 等四个变量 → `docker compose up -d` → 首次访问初始化向导建第一个用户 → 按需配集成。最容易出问题的是环境变量：两个密钥沿用占位符是安全风险；compose 四变量不补，Web 容器拿到的连接串是空的。
</details>

### 题 4：适用边界

列出至少三个不该用 Cal.diy 的场景。

<details>
<summary>参考答案</summary>

需要商业级保障的生产环境（README 限定 personal、non-production）；依赖 SSO/SAML、Teams、Organizations、Insights、Workflows 的组织（已移除）；没有服务器运维能力又不想自己管备份、证书、安全更新的团队（无官方托管）。
</details>

### 题 5：故障排查

Docker 部署后日志报 `CLIENT_FETCH_ERROR`，怎么定位？

<details>
<summary>参考答案</summary>

这是认证回路的基底地址解析失败：容器内的 DNS 与开发机不一致，`WEBAPP_URL` 解析不到（日志可见 `getaddrinfo ENOTFOUND`）。在 `.env` 里显式设置 `NEXTAUTH_URL=http://localhost:3000/api/auth`，让后端回环到自身。
</details>

## 参考

- 仓库：<https://github.com/calcom/cal.diy>（2026-09-28 观测：48,709 stars、15,232 forks、1,439 open issues，TypeScript，MIT）
- 最新 release：v6.2.0，2026-03-01 发布
- README：安装流程、`yarn dx` 账号表、Docker 变量表、集成凭证步骤与排错条目的出处
- `docker-compose.yml` 与 `scripts/start.sh`：五个服务构成与"启动即迁移"机制的出处
- `packages/app-store/` 目录：集成清单的出处（154 个条目，2026-09-28）
- `packages/prisma/package.json`：`db-migrate`、`db-deploy`、`db-seed`、`dx` 等脚本的定义
- Docker 镜像：<https://hub.docker.com/r/calcom/cal.diy>
- Cal.com（商业版）：<https://cal.com>
