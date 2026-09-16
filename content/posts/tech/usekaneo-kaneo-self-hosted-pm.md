---
title: "Kaneo 拆解：功能做减法、接口做加法的自托管项目管理"
date: 2026-08-02T02:59:48+08:00
slug: "usekaneo-kaneo-self-hosted-pm"
github_repo: "usekaneo/kaneo"
source_key: "gh:usekaneo/kaneo"
description: "usekaneo/kaneo 用 MIT 许可把自托管项目管理压进单个容器：Hono + Drizzle + PostgreSQL + React 19 的 TypeScript 全栈，功能克制，但 MCP、webhook、OAuth/OIDC 接口齐全。本文基于 2026-09-12 的仓库与文档数据，拆解其架构、任务流转路径、部署方式与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["项目管理", "自托管", "看板", "开源", "Hono", "React", "MCP"]
---

# Kaneo 拆解：功能做减法、接口做加法的自托管项目管理

自托管项目管理工具长年困在两个极端：要么像 Plane、OpenProject 那样把功能做全，代价是多容器架构和可观的运维负担；要么像 Focalboard 那样轻巧，官方仓库如今却挂着“不再维护”的警告。`usekaneo/kaneo`（下称 Kaneo）走的是中间路线：功能只保留任务协作的最小集，交付形态压成单个 Docker 容器，然后把 MCP（Model Context Protocol，模型上下文协议）、webhook、OAuth/OIDC（OpenID Connect）这些对外接口做齐。

截至 2026 年 9 月 12 日（GitHub API），Kaneo 有 9,056 Stars、775 Forks，主语言 TypeScript，MIT 许可。仓库创建于 2024 年 12 月 31 日，数据基准日前一天仍有推送，不到两年积累近万 Star。

## 一、它赌的是什么

README 的自述开门见山：

> The problem with most tools isn't that they lack features, it's that they have **too many**.

转述过来：每一条多余的通知、按钮和工作流，都在把团队从“做产品”上拉开；最好的工具是隐形的。这个哲学落到工程上是两句话——功能层做减法，工作流、字段、通知都往回收；接口层做加法，MCP、出站 webhook、SSO、S3 附件一个不缺。这是 Kaneo 与“又一个 Trello 替代品”的分野。

系统全景如下，后面各节的展开都对应表里的某一层：

| 层 | 选择 | 说明 |
|------|------|------|
| 交付形态 | `ghcr.io/usekaneo/kaneo` 单容器 | Web 与 API 同在 5173 端口对外；也可拆成独立的 api / web 镜像 |
| API | Hono + @hono/zod-openapi | Zod schema 直接生成 OpenAPI 文档 |
| 数据 | PostgreSQL + Drizzle ORM | 唯一的强依赖存储 |
| 认证 | better-auth | 邮箱验证码或密码登录，GitHub / Google / Discord / 自定义 OIDC SSO |
| 实时 | WebSocket | 单实例走进程内广播，多实例加 Redis Pub/Sub |
| 前端 | React 19 + Vite + TanStack Router / Query + TipTap 3 + dnd-kit | 依赖里带上了 React Compiler 的 Babel 插件 |
| 扩展 | MCP 端点 `/api/mcp`、出站 webhook、GitHub App / Gitea | AI 客户端和外部系统可以直接操作任务 |

## 二、仓库地图：一个 pnpm monorepo

代码用 pnpm workspaces 加 Turborepo 组织。`apps/` 下是四个应用：

- `api`：Hono 后端。源码按领域切目录：task、project、column、comment、activity、label、custom-field、task-relation、time-entry、search、notification、scheduler、storage、oauth、mcp，外加 github、gitea、slack、telegram、mattermost、discord 和通用 webhook 等集成目录；
- `web`：React 前端；
- `docs` 与 `site`：文档站和官网，kaneo.app 就跑在仓库内这两个应用上。

`packages/` 下是六个共享包：libs、mcp（stdio 版 MCP 服务器）、permissions、email、planka-import（从 PLANKA 迁移的 CLI）、typescript-config。

后端依赖里有几个值得留意的信号：`better-auth` 负责认证与会话，文档站 API 参考里那组组织、团队、角色管理端点与它的 organization 模块对应；`drizzle-orm` 加 `pg` 落数据库；`ioredis` 对接可选的 Redis；`@aws-sdk/client-s3` 对接 S3 兼容存储（MinIO、AWS S3、Cloudflare R2）；`octokit` 支撑 GitHub 集成；`croner` 跑定时任务。前端是 React 19 一套：TanStack Router 管路由，TanStack Query 管服务端状态，TipTap 3 做任务描述编辑器，dnd-kit 做看板拖拽，状态层用 zustand。

## 三、一个任务穿过系统的完整路径

以“把『修复登录超时』从进行中拖到待验收”为例：

1. 成员 A 在看板拖动卡片，dnd-kit 负责拖拽手势与位置计算，卡片随手势到位；
2. 变更经 TanStack Query 的 mutation（变更提交）发往 API：Hono 用 Zod 校验请求体，Drizzle 写入 PostgreSQL，同时记一条 activity（活动记录）；
3. API 通过 WebSocket 把变更广播出去。单实例时进程内直接分发；多实例部署时 WebSocket 会话不共享，需要配 Redis 做 Pub/Sub（支持单机、Sentinel、Cluster 三种模式）；
4. 成员 B 的浏览器里，同一块看板上的卡片同步移动；
5. 成员 B 若订阅了通知，投递渠道按个人偏好走：邮件、ntfy、Gotify 或自定义 webhook，按工作区与项目两级过滤；
6. 项目若连了 GitHub 仓库，GitHub App 通过 webhook 接收仓库活动；出站 webhook 也可以把这次任务活动推给 Slack、Discord、Telegram 或任意 HTTP 端点，支持可选签名；
7. 这套操作也可以不开浏览器：每个 Kaneo 实例自带 HTTP MCP 端点 `/api/mcp`，Claude、Cursor 等 MCP 客户端经 OAuth 2.1（PKCE 加明确的授权确认页）接入后，能创建、移动、指派任务，查询活动记录；偏好 stdio 的客户端用官方 npm 包 `@kaneo/mcp`，走设备授权流程，凭据存在 `~/.config/kaneo-mcp/credentials.json`。

第七步在同类自托管工具里还不多见：任务管理交给 AI 客户端代操作，权限收敛在用户自己的 OAuth 授权里。MCP 文档也写明了边界——时间条目只有增、改、查，没有删除，因为底层 API 就没有删除端点。

## 四、部署：三条路径，同一个容器

官方给出三条部署路径，按介入深度排序。

**drim 一键安装**（README 首推）：

```bash
curl -fsSL https://assets.kaneo.app/install.sh | sh
drim setup
```

drim 是 Kaneo 官方的部署 CLI，自动处理 HTTPS、数据库初始化和全部服务配置。

**Docker Compose 手动部署**。仓库根目录的 `compose.yml` 只有两个服务：

```yaml
services:
  postgres:
    image: postgres:16-alpine
    env_file:
      - .env
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U kaneo -d kaneo"]
      interval: 10s
      timeout: 5s
      retries: 5

  kaneo:
    image: ghcr.io/usekaneo/kaneo:latest
    ports:
      - "5173:5173"
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://127.0.0.1:5173/api/health"]
      interval: 30s
      timeout: 5s
      start_period: 60s
      retries: 3

#  Optional for HA Setup
#  redis:
#    image: valkey/valkey
#    ports:
#      - "6379:6379"

volumes:
  postgres_data:
```

配置步骤：从 `.env.sample` 复制出 `.env`，确认 `KANEO_CLIENT_URL=http://localhost:5173`，设置 `POSTGRES_PASSWORD` 和 `AUTH_SECRET`（用 `openssl rand -hex 32` 生成），然后 `docker compose up -d`，访问 5173 端口。

三个容易踩的坑，都出自官方文档：

- `KANEO_API_URL` 留空即可，它默认从 `KANEO_CLIENT_URL` 派生（`<client>/api`）。手动设成 `localhost` 会弄坏浏览器端的 API 调用，README 特意标注了这一点；
- `AUTH_SECRET` 不设也能启动，但每次重启都会随机生成，所有登录会话随之失效；
- 任务描述和评论里的私有图片、附件依赖 S3 兼容对象存储（MinIO、AWS S3 或 Cloudflare R2），不配置就没有私有上传。

**托管平台**：Coolify 用仓库内置的 `compose.coolify.yml`，Railway 有官方模板，Kubernetes 走仓库内的 Helm chart（`charts/kaneo`）。

升级与备份不需要专门工具。compose.yml 引的就是 `:latest` 标签，拉新镜像重启即完成升级，容器自带 `/api/health` 健康检查，`docker compose ps` 回到 healthy 就算切换完成；有状态数据全部落在 PostgreSQL，备份与迁移等价于数据库的 dump 与 restore。

关于邮件还有一个行为要知道：配置了 SMTP 之后，登录默认走邮箱验证码；想改回邮箱加密码的登录方式，需要显式设置 `DISABLE_EMAIL_OTP_SIGN_IN=true`。

## 五、减法减掉了什么

**有的**（依据文档站功能指南与源码目录）：

- workspace、project、task 三层结构。任务带状态列、指派人、截止日期、标签、评论、活动记录、自定义字段和任务关联；backlog（待办池）用于进入执行前的规划；
- 工作流可配置：自定义列加自动化规则；
- 看板与列表两种视图，任务支持批量更新；
- 时间条目：能记、能改、能查，不能删；
- 通知：站内偏好之外，支持邮件、ntfy、Gotify、自定义 webhook；
- 集成：GitHub App（仓库连接与 webhook）、Gitea（issues、PR、webhook）、Slack / Telegram / Discord 通知、带签名的出站 webhook；
- SSO：GitHub、Google、Discord、自定义 OIDC；
- PLANKA 迁移：`@kaneo/planka-import` CLI，覆盖列表、卡片、标签、指派人、清单和评论；
- 界面多语言（i18next）。

**没有或弱的**（依据同样可查）：

- 没有甘特图、资源排程、预算与计费——文档站的功能指南清单里没有这些页面；
- 权限模型到组织、团队、角色为止，没有字段级权限矩阵；
- 没有原生移动端，Web 是唯一界面。

咨询公司常要的“时间追踪加计费”，前一半 Kaneo 现在有（时间条目），后一半没有。

## 六、放在同类里看

| 项目 | 定位 | 交付形态 | 规模与现状 |
|------|------|----------|-----------|
| Kaneo | 克制的任务协作最小集 | 单容器 TypeScript 全栈 | 9.1K Stars，2026-09-11 仍有推送 |
| Plane | 全功能 Jira 替代 | 多容器：React + Django + Hocuspocus | 59.3K Stars，活跃 |
| OpenProject | 企业级 PM：甘特图、成员与成本 | Ruby on Rails，社区版加商业版 | 老牌项目 |
| Focalboard | 看板 | 桌面应用 / Mattermost 插件 | 官方仓库声明不再维护 |

选型含义：要功能面，Plane 是自托管同类里最全的，代价是多容器运维；要企业流程，甘特图和成本核算本来就是 OpenProject 的主场；要一个“装完就忘、数据在自己服务器上”的任务看板，Kaneo 是当前最省心的形态之一；Focalboard 不该再进新的选型清单。

## 七、采用建议

适合先上：

- 3–30 人、想要 Linear 手感但要求数据自持的工程团队。单实例即单租户，没有多租户复杂度要操心；
- 已经在用 Compose 或 Kubernetes 的团队：前者一个 `compose.yml` 加三个环境变量，后者有 Helm chart；
- PLANKA 的存量用户：官方迁移 CLI 能把看板整体搬过来。

建议再等等：

- 依赖甘特图、资源排程、预算功能的团队，Kaneo 没做这些；
- 需要字段级权限矩阵或完整审计链的受监管组织，权限模型到组织与角色为止；
- 移动端是硬需求的团队，只有 Web。

起步路径：个人或小团队从 drim 开始，几分钟出结果；对部署形态有要求的用 Compose 或 Helm 自己管；已有 PLANKA 的先跑 `@kaneo/planka-import`。

回到开头的赌注：Kaneo 的价值不在“又一个开源 Trello”，而在把自托管 PM 的门槛项——部署、认证、集成、AI 接口——做成默认项，功能面则刻意停在任务协作的最小集。赌注能否兑现，要看团队涨到 30 人以上时，“够用的最小集”是否依然够用；就目前的迭代速度和接口完成度看，2026 年的自托管 PM 选型，值得先把它放进对比清单再下结论。

## 数据来源

- 仓库元数据（Stars、Forks、语言、许可、创建与推送时间）：GitHub API，2026-09-12；
- 部署与环境变量：仓库 `README.md`、`compose.yml`、`.env.sample`（main 分支，2026-09-12）；
- 技术栈：`apps/api/package.json`、`apps/web/package.json`（main 分支）；
- 功能与集成：[kaneo.app 文档站](https://kaneo.app/docs/core)及其 `llms.txt` 索引、MCP 集成页；
- 对比数据：makeplane/plane（GitHub API，2026-09-12）；mattermost/focalboard 仓库 README 的维护状态声明。

> 本文数据基准为 2026-09-12。仓库迭代较快，部署细节与环境变量以官方文档为准。
