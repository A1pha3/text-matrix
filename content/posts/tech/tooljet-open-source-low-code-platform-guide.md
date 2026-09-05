---
title: "ToolJet：开源低代码平台，60+ 组件与 80+ 数据源拼装内部工具"
date: 2026-08-17T03:24:00+08:00
slug: "tooljet-open-source-low-code-platform-guide"
github_repo: "ToolJet/ToolJet"
source_key: "gh:ToolJet/ToolJet"
description: "ToolJet 是一个开源的低代码平台，社区版提供可视化拖拽构建器、内置数据库和 80+ 数据源连接器，企业版叠加 AI 生成与 Agent 编排。本文拆解其 Server / Client 架构、代理式数据流与上手路径。"
draft: false
categories: ["技术笔记"]
tags: ["低代码", "内部工具", "开源", "JavaScript"]
---

内部工具开发是个尴尬的领域：需求琐碎但真实，认真写一套前后端太重，用 Excel 凑合又撑不住权限和协作。ToolJet 在这个位置做了多年积累——一个 AGPL v3 开源的低代码平台，主语言 JavaScript/TypeScript（仓库约 40k stars、5.4k forks），2026 年仍在以几乎每天一个版本的节奏发版（LTS 与 beta 双线并行，例如 v3.20.214-lts 与 v3.21.61-beta 前后脚落地）。

读完后你会知道：它内部由哪几个服务组成、数据怎么流、什么场景适合它、什么场景不该选它，以及从零起一个实例要几步。

## 核心判断

ToolJet 的工程重点不在"画 UI"，而在**数据连接与执行**。它的设计是：数据库凭据只存在服务端，查询由服务端代跑，浏览器只拿到结果。这个"代理式"结构决定了它能不能进你的生产环境，也是它与 Excel 类工具的本质区别。

社区版（CE）已经覆盖完整的可视化构建能力；AI 生成界面、AI 辅助查询、Agent 编排属于 ToolJet AI（企业版）的付费范畴。评估它时，CE 和 AI 版要分开看。

## 系统地图

ToolJet 是 JavaScript/TypeScript monorepo。自托管时是一组服务，以官方架构文档和仓库 `.agents/context` 架构地图为准：

```
浏览器：ToolJet Client（React）
  │  拖拽建 UI / 绑定查询 / 触发事件
  │  REST / WebSocket
  ▼
ToolJet Server（NestJS / Node.js API）
  │  认证授权（JWT + CASL 权限）/ 持久化应用定义
  │  代跑查询 / 加密存凭据 / 定时与后台任务
  │  邮件服务（SMTP / Sendgrid / Mailgun）负责邀请与密码重置
  ▼
PostgreSQL（主数据库：应用定义、用户、加密凭据）
  ▲
  │  PostgREST：把 ToolJet Database 暴露成 REST API
ToolJet Database（内置数据库，独立的第二个 PostgreSQL 连接）
  ▼
Redis + BullMQ：队列与后台任务调度（Workflow 用）
Worker 进程：消费队列执行工作流
```

- **ToolJet Client**：React 应用，负责可视化编辑、数据绑定、渲染与事件触发。
- **ToolJet Server**：NestJS / Node.js API 服务，管认证、应用定义持久化、查询执行和数据源凭据的加密存储。
- **PostgreSQL**：主数据库，存应用定义、用户和加密后的数据源凭据。
- **ToolJet Database**：内置的"零配置"数据库，走独立 PostgreSQL 连接，通过 PostgREST 暴露成 REST API；PostgREST 只与 Server 通信，不对外暴露。
- **Redis + BullMQ**：任务队列，支撑 Workflow 编排、定时任务与多实例协同（多 Pod / 多 Worker 部署时必需）。
- **邮件服务**：SMTP 或 Sendgrid / Mailgun 等，用于发送邀请与密码重置。

数据流和构建流是两条主线：数据从浏览器到 Server 再到数据源；构建则是拖组件、绑数据、设权限、发布。

## 关键机制

### 机制 1：查询在服务端执行，凭据不出浏览器

建一个查询时，数据源凭据存在服务端。运行时浏览器只把"执行哪个查询、带什么参数"发给 Server，由 Server 连库取数，结果再回传。数据库账号和密钥不会出现在前端代码里，这就是 README 说的 proxy-only data flow。它同时解决两个问题：前端拿不到凭据，凭据在存储时用 AES-256-GCM 加密。

### 机制 2：ToolJet Database 是"独立 PostgreSQL + PostgREST"

内置数据库不需要先接一个外部 Postgres。它使用独立的 PostgreSQL 连接（默认库名 `tooljet_db`），之上再挂一层 PostgREST 把表暴露成 REST API；表、字段、关系在 UI 里点出来就能建，天然支持 CRUD。PostgREST 只和 ToolJet Server 通信，不对外网开放。对"只想快速存点数据、不想维护独立数据库"的场景，这一步省掉了最大的入门成本。

### 机制 3：组件与查询靠绑定连接

表格、表单、图表这类组件本身不装数据，靠绑定表达式把某个查询的结果喂进来，再配好事件（比如按钮点击 → 跑查询 → 刷新表格）。复杂逻辑可以用内嵌 JavaScript 或 Python 片段补上。理解"组件—查询—事件"三个要素，就能拆掉 ToolJet 里绝大多数应用。

### 机制 4：Workflow 是独立于页面的编排层

除了页面里的即时事件，ToolJet 还有一个 Workflow 模块：用可视化节点编辑器把多步业务过程串起来，支持分支、循环、条件执行，可被用户动作、定时器或 API 调用触发。数据源连接器在页面查询和 Workflow 里通用，编排出来的流程也可以嵌入应用里。

## 社区版能力清单

- **可视化构建器**：60+ 响应式组件，表格、图表、表单、列表、进度条等；多页面应用与多人实时编辑是内置能力。
- **数据层**：ToolJet Database、80+ 数据源连接器（数据库、REST / GraphQL API、云存储、SaaS）、Code Anywhere 可跑 JS / Python。
- **工作流**：Workflow 可视化编排（触发、分支、循环、定时）。
- **协作与安全**：行内评论、@提及、细粒度访问控制；AES-256-GCM 加密、代理式数据流、SSO。
- **扩展**：用 [ToolJet CLI](https://www.npmjs.com/package/@tooljet/cli) 写自己的插件和连接器。

## 快速上手

最快的本地体验是一条 Docker 命令：

```bash
docker run \
  --name tooljet \
  --restart unless-stopped \
  -p 80:80 \
  --platform linux/amd64 \
  -v tooljet_data:/var/lib/postgresql/13/main \
  tooljet/try:ee-lts-latest
```

生产部署建议走 Docker Compose，用官方生成的 compose 文件，并选 LTS 版本线。README 明确说明 LTS 线只收稳定性修复、安全补丁和性能增强，适合生产；`latest` 更适合尝鲜。自托管时要注意几个环境变量：

- `TOOLJET_HOST`：访问地址（`http://IP` 或 `https://域名`），必须以 `http://` / `https://` 开头。
- 密钥类变量（`LOCKBOX_MASTER_KEY` 用 `openssl rand -hex 32` 生成、`SECRET_KEY_BASE` 用 `openssl rand -hex 64` 生成、数据库密码）：官方脚本 `internal.sh` 会帮你生成。
- 要用 ToolJet AI 功能，需要在网络里放行 `https://api-gateway.tooljet.ai` 和 `https://python-server.tooljet.ai`。

不想自托管就直接用 ToolJet Cloud 托管版。

## 任务流案例：搭一个订单查询后台

假设要给运营同事搭一个"查订单"的小工具：

1. 建一个数据源，连已有的 PostgreSQL（或直接用 ToolJet Database 建表）。
2. 拖一个 Table 组件，把绑定指向查询 `get_orders`。
3. 加一个输入框，事件设为"输入订单号 → 带参重跑查询"。
4. 按角色设权限（运营只读，管理员可改），发布。

一次点击背后的流程是：浏览器把"执行 `get_orders` 并带参数"发给 Server → Server 用存好的凭据连库取数 → 结果回传 → Table 刷新。整个过程中运营同事看不到数据库账号，也碰不到别的表。

## 企业版加什么

ToolJet AI 在 CE 之上叠加的能力里，值得关注的几条：

- **AI App Generation**：自然语言描述直接生成应用初稿。
- **AI Query Builder / AI Debugging**：辅助生成查询、一键定位问题。
- **Agent Builder**：构建自动化工作流的智能体。
- **企业治理**：SOC 2 / GDPR 合规准备、审计日志、RBAC、多环境（dev / stage / prod）、GitSync 与 CI/CD 集成、白标与嵌入。

## 测什么、不能推出什么

"60+ 组件、80+ 数据源"衡量的是**连接器与组件的覆盖广度**。它说明大多数内部工具的高频需求有现成件可拼，不能推出"任何需求都能在平台内表达干净"。低代码平台的表达力有上限：超过某个复杂度阈值（复杂状态机、特殊渲染、深度定制交互），维护成本会反超传统开发。组件数量也不代表性能——大表要靠分页和虚拟滚动支撑，表格组件需要你显式配置分页，而不是把所有行一次渲染出来。

## 常见问题

**自托管需要多少运维？** 需要一台能跑 Docker 的机器和一点基础：设置环境变量、备份 PostgreSQL、跟踪版本升级。没有 DevOps 经验的团队，用 Cloud 版更省事。

**数据安全怎么保证？** 凭据只在服务端，前端拿不到；存储用 AES-256-GCM 加密；部署层支持 SSO。但自托管时数据库备份、TLS、服务器加固仍是你自己的责任。

**AGPL v3 对我意味着什么？** 如果你基于 ToolJet 二次开发并向外部提供网络服务，需要开源衍生代码。内部自用通常不受影响，但商业集成前要评估许可证兼容性。

**升级选 LTS 还是 latest？** 生产选 LTS，尝鲜用 latest。

## 适用边界与采用顺序

适合：需要快速交付内部工具、管理后台、仪表盘、审批流的团队；已有数据库和 SaaS 资产、想在其上快速搭一层操作界面的场景。

不适合：面向外部用户的 C 端产品（性能和定制自由度不够）；深度定制业务系统；需要复杂离线流程或重前端交互的应用。

如果要试，建议按这个顺序：先用一条 Docker 命令起本地实例 → 用你们最高频的一两个场景（比如订单查询、审批流）各搭一个最小应用 → 验证权限、数据源、性能能不能接受 → 再决定自托管（Compose + LTS）还是 Cloud。

## 进阶路径

- 把官方[快速入门](https://docs.tooljet.com/docs/)里的示例应用（时间追踪、CMS、AWS S3 Browser）逐个搭一遍，理解组件—查询—事件三要素。
- 用 [ToolJet CLI](https://www.npmjs.com/package/@tooljet/cli) 写一个自己的数据源连接器，摸清平台扩展边界。
- 读[架构文档](https://docs.tooljet.com/docs/contributing-guide/setup/architecture/)和 docker-compose 文件，弄清 Server / Client / PostgREST / Redis 各自的职责，自托管排障会顺利很多。

- 仓库：https://github.com/ToolJet/ToolJet
- 文档：https://docs.tooljet.com
