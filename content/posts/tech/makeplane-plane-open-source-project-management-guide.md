---
title: "Plane 架构拆解：开源项目管理平台的 React + Django + Hocuspocus 分层实现"
date: "2026-06-18T15:08:00+08:00"
slug: "makeplane-plane-open-source-project-management-guide"
description: "makeplane/plane 是开源项目管理平台，定位为 Jira / Linear / Monday / ClickUp 的开源替代。本文基于仓库源码拆解其 React + Django + Hocuspocus 分层架构、God Mode 自托管治理与 Monorepo 工程体系。"
categories: ["技术笔记"]
tags: ["React", "Django", "PostgreSQL"]

github_repo: "makeplane/plane"
source_key: "gh:makeplane/plane"
---

# Plane 架构拆解：开源项目管理平台的 React + Django + Hocuspocus 分层实现

`makeplane/plane` 要做的事不新鲜：在 Jira、Linear、Monday、ClickUp 已经教育过市场的项目管理领域，做一个完全开源、可自托管的替代品。截至 2026 年 8 月，仓库有 56,093 Stars、5,349 Forks、789 个 open issues（数据来源见文末参考文献），采用 AGPL-3.0 许可证，提交持续活跃。它把 issues、cycles、modules、views、pages、analytics 六大模块打磨到了接近商业竞品的成熟度，同时提供 Plane Cloud 与 Self-Host（自托管）两种形态。

本文基于 GitHub 仓库源码与官方文档，拆解 Plane 的应用分层、API（应用程序接口）后端选型、实时协作服务与基础设施，并讨论自托管方案适合谁、不适合谁。

## 目录

- [一、定位：开源 + 自托管，而不是"另一个 Linear"](#一定位开源--自托管而不是另一个-linear)
- [二、仓库结构：六个应用加一组共享包](#二仓库结构六个应用加一组共享包)
- [三、前端：React + Vite + TipTap 编辑器](#三前端react--vite--tiptap-编辑器)
- [四、API 后端：Django + DRF 的稳健选型](#四api-后端django--drf-的稳健选型)
- [五、实时服务：Hocuspocus 与 Yjs 协同](#五实时服务hocuspocus-与-yjs-协同)
- [六、基础设施：Docker Compose 一眼看完](#六基础设施docker-compose-一眼看完)
- [七、God Mode：实例管理员入口](#七god-mode实例管理员入口)

- [八、功能矩阵：六大模块](#八功能矩阵六大模块)
- [九、工程体系：Turborepo + pnpm workspaces](#九工程体系turborepo--pnpm-workspaces)
- [十、动手练习：本地跑一个 Plane](#十动手练习本地跑一个-plane)
- [十一、适用边界](#十一适用边界)
- [十二、常见问题（FAQ）与排查](#十二常见问题faq与排查)
- [十三、进阶方向](#十三进阶方向)
- [参考文献与事实来源](#参考文献与事实来源)

这篇文章的阅读目标，是让你能回答四个问题：Plane 的每层服务用什么技术、为什么实时层选了 Hocuspocus、God Mode 能管什么、自托管需要准备哪些基础设施。

## 一、定位：开源 + 自托管，而不是"另一个 Linear"

Plane 的 README 开篇这样定义自己：

> Meet Plane, an open-source project management tool to track issues, run ~sprints~ cycles, and manage product roadmaps without the chaos of managing the tool itself.

关键词是 open-source 和 "managing the tool itself"。不少团队已经厌倦了为工具本身付出管理成本——账号体系、订阅计费、第三方集成，每一项都要人维护。Plane 想把工具的所有权交回用户。

它的产品边界也比"开源"两个字更宽：

- 功能上吸收 Jira 式的企业能力（cycles、modules、roadmap、analytics），交互上靠近 Linear 的现代体验（键盘流、issue 引用）
- 部署上提供 Plane Cloud 与 Self-Host 两条路线，自托管覆盖 Docker Compose 与 Kubernetes
- 许可证选择 AGPL-3.0：内部自由使用与修改没有问题；对外提供修改后的网络服务时，需要按 AGPL 条款开放源码

一句话：Plane 追求的是"功能接近 Jira / Linear，部署完全开放"，而不是"更轻量"或"更便宜"。

## 二、仓库结构：六个应用加一组共享包

打开仓库根目录，应用与包的边界一目了然：

```bash
plane/
├── apps/          # web、admin、space、api、live、proxy 六个应用
├── packages/      # editor、ui、hooks、types、i18n 等共享包
├── deployments/   # aio、cli、kubernetes、swarm 部署资产
└── docker-compose.yml
```

对应到运行时，可以按四层理解：

| 层 | 载体 | 职责 |
| --- | --- | --- |
| 前端 | `apps/web` | 核心 UI：看板、cycle 视图、Pages |
| 管理 | `apps/admin`、`apps/space` | God Mode 实例管理、对外 issue 发布 |
| API | `apps/api` | Django + DRF 业务逻辑与数据持久化 |
| 实时 | `apps/live` | Hocuspocus WebSocket 协同服务 |

底座是 PostgreSQL、Valkey（Redis 兼容分支）、RabbitMQ、MinIO 四个有状态组件，部署形态见第六节。

## 三、前端：React + Vite + TipTap 编辑器

`apps/web` 的技术栈是 React + Vite + React Router + TypeScript。React Router（前端路由器）负责应用内导航。重点在共享包体系：

- **`packages/editor`**：基于 TipTap 的富文本编辑器，依赖里能看到 `@tiptap/extension-collaboration`——协同编辑能力直接建在编辑器层
- **`packages/ui`**：组件库，按钮、输入框、弹窗、看板组件都在这里
- **`packages/types`**：跨应用共享的 TypeScript 类型
- **`packages/hooks`**：共享的自定义 React hooks
- **`packages/i18n`**：国际化文案

共享包让接口类型在前后端之间保持同步：schema（模式，即数据结构定义）变了，编译期就能发现前后端不一致。代价是构建复杂度上升，Plane 选择了代码质量优先。

Pages 模块承载长文本协作：文本格式、图片、超链接，README 还提到可以把笔记内容转换成 actionable item（可执行条目），并带 AI 辅助能力。

## 四、API 后端：Django + DRF 的稳健选型

`apps/api` 没有跟风 Go 或 Rust，选了 Django + Django REST（表述性状态转移）Framework，即 DRF。锁定版本能看出工程取向：`requirements/base.txt` 里是 Django 5.2.15、djangorestframework 3.17.1，另有 django-redis、django-filter、django-storages、Celery 相关包。

这个选型换来三样东西：

- ORM（对象关系映射）、admin、auth、migrations 开箱即用，PostgreSQL 的数据模型变更走 Django migrations
- DRF 的 ViewSet、Serializer、Router 把接口定义标准化
- Celery 承接异步任务，`docker-compose.yml` 里的 worker 与 beat-worker 两个服务就是它的运行载体，消息队列用 RabbitMQ

后端主体是单体结构，不是 microservices（微服务）拆分。对自托管场景这很关键：用户部署的是一个 Django 项目加若干 worker，而不是一堆要编排的服务。业务模型——issues、cycles、modules、projects、workspaces——的复杂度远高于吞吐压力，开发效率优先是合理取舍。

## 五、实时服务：Hocuspocus 与 Yjs 协同

`apps/live` 值得单独说，因为它的实现和很多人猜测的不一样：不是 NestJS，而是 Hocuspocus——Yjs 文档协同的 WebSocket 服务端。`apps/live` 的 package.json 自我描述是 "A realtime collaborative server powers Plane's rich text editor"，依赖以 `@hocuspocus/server` 为核心，配合 Express 与 `@hocuspocus/extension-redis`、`@hocuspocus/extension-database` 两个扩展。

这套组合的分工很清晰：

- Yjs 负责富文本的冲突合并，多人同时编辑同一个 Page 时不需要中心裁决
- Hocuspocus 负责 WebSocket 连接、文档加载与数据库持久化
- Redis 扩展让多个 live 实例之间同步编辑状态，具备横向扩展空间

它与前端 `packages/editor` 的 collaboration 扩展正好对接：编辑器产生 Yjs 更新，live 服务广播并落库。"主后端负责增删改查、独立服务负责长连接协同"是近年常见的拆法，Plane 的特色在于它没有自研协同协议，而是直接押注 Yjs 生态。

## 六、基础设施：Docker Compose 一眼看完

自托管最关键的问题是"要维护多少东西"。仓库根目录的 `docker-compose.yml` 定义了 13 个服务：除 web、admin、space、api、worker、beat-worker、migrator、live 和反向代理 proxy 这九个无状态服务外，还有四个有状态组件：

```yaml
plane-db: { image: postgres:15.7-alpine }                # 主存储
plane-redis: { image: valkey/valkey:7.2.11-alpine }      # 缓存与实时状态
plane-mq: { image: rabbitmq:3.13.6-management-alpine }   # Celery 消息队列
plane-minio: { image: minio/minio }                      # 文件上传对象存储
```

要点有三个：主存储是 PostgreSQL；缓存与实时状态用 Valkey——Redis 的开源兼容分支，接口一致；文件上传走 MinIO，生产环境也可以按官方文档换成 S3 等外部对象存储。

官方部署方式有三种：

| 方式 | 适用场景 |
| --- | --- |
| Docker Compose | 配置最少，适合中小团队快速起步 |
| Kubernetes（Helm） | 生产级，强调高可用与自动扩缩 |
| 托管服务（Zenith） | 不想自己运维的折中选项 |

## 七、God Mode：实例管理员入口

God Mode 是自托管场景下的管理员界面，对应 `apps/admin` 应用，路由路径是 `/god-mode`。实例管理员在这里治理整个 Plane 实例：

- **General**：实例名称、遥测开关
- **Email**：SMTP 配置，官方文档建议部署后第一件事就配好它，否则邀请邮件发不出去
- **Authentication（身份认证）**：SSO（单点登录）与 OAuth 登录方式，支持 Google、GitHub、GitLab 等
- **Workspaces**：查看全部工作区、创建工作区、限制创建权限
- **User management**：用户增删、邀请其他实例管理员

官方文档也明确了一点：Cloud 版暂时没有对等的 God Mode（"Not now, but soon enough"）。也就是说，实例级治理目前是自托管用户的专属能力。

## 八、功能矩阵：六大模块

Plane 的功能划分与主流工具高度对齐，README 的表述如下：

| 模块 | 能力 | 可类比的对象 |
| --- | --- | --- |
| Work Items（issues） | 富文本描述、文件上传、子属性、issue 互相引用 | Jira issue / Linear issue |
| Cycles | 限时迭代，带 burn-down 图 | Jira Sprint |
| Modules | 把复杂项目拆成可管理的大块 | Jira Epic |
| Views | 自定义过滤器，可保存与分享 | Linear view |
| Pages | 富文本笔记，支持 AI 能力，可转 actionable item | Notion page |
| Analytics | 全量数据的实时趋势与洞察 | Jira 报表 |

它没有发明新概念，而是把被验证过的概念用开源方式重新实现一遍。对用惯了 Jira 或 Linear 的团队，迁移的理解成本很低。

## 九、工程体系：Turborepo + pnpm workspaces

仓库顶层是 `turbo.json` + `pnpm-workspace.yaml`，packageManager 锁定 pnpm 11。workspace 成员是 `apps/*` 与 `packages/*`，其中 `apps/api`（Python）和反向代理应用 `apps/proxy` 被排除在 JS（JavaScript）工作区之外。

两个工程细节：

- **catalog 统一版本**：React、Vite、TipTap 等依赖在 `pnpm-workspace.yaml` 的 catalog 里声明一次，所有包引用同一个版本，避免漂移
- **跨应用原子改动**：给 issue 加一个字段，前端组件、Django model、`packages/types` 三处可以在同一个 PR（拉取请求）里改完并提交

Turborepo 负责构建编排与缓存。这套组合是近年 JS monorepo（单仓库）的主流答案，Plane 的规模正好是它的舒适区。

## 十、动手练习：本地跑一个 Plane

这一节给出三个由浅入深的示例，全部基于仓库自带资产。

**练习 1：用 Docker Compose 起一个本地实例。** 克隆仓库后执行：

```bash
docker compose -f docker-compose-local.yml up
```

CONTRIBUTING.md 给出的流程是：先在 `http://localhost:3001/god-mode/` 注册为实例管理员，再用同一账号登录 `http://localhost:3000`。官方提醒本地全套容器对内存要求不低，8 GB 内存的机器可能构建失败。

**练习 2：对照源码验证本文的三个断言。** 打开 `apps/live/package.json` 确认实时服务的框架；读 `apps/api/requirements/base.txt` 确认 Django 与 DRF 版本；看 `docker-compose.yml` 数一数有状态组件。

**练习 3：自测。** 不查资料回答：(1) Plane 六个应用分别叫什么？(2) 协同编辑由哪个服务、哪个协议支撑？(3) God Mode 能配置哪几类设置？答不上来的回到对应章节。

## 十一、适用边界

**适合采用**：

- 团队规模数十到数百人，需要 Jira / Linear 级能力但要求数据自持
- 数据合规严格（金融、医疗、政府），所有数据必须留在自己的服务器
- 已有 Docker / Kubernetes 运维能力
- 希望深度定制；AGPL-3.0 允许内部修改使用

**谨慎采用**：

- 没有 DevOps 能力的小团队：自托管意味着维护 PostgreSQL、Valkey、RabbitMQ、MinIO、反向代理与 SMTP 一整条链
- 追求"五分钟上线"：直接用 Plane Cloud 更省心

**不适用**：

- 只需要轻量待办：Todoist、TickTick 这类工具更合适
- 法务不接受 AGPL-3.0：对外提供修改后的服务需要开源，这条不是每个企业都能过审

## 十二、常见问题（FAQ）与排查

**Q1：AGPL-3.0 能商用吗？**
内部使用、修改、分发都没有问题。触发点是"把修改后的版本作为网络服务对外提供"，此时需要按 AGPL 开放源码。纯内部部署不受这条约束。具体法务判断请以许可证原文为准。

**Q2：Cloud 版会有 God Mode 吗？**
官方文档的说法是暂时没有、在路线图上（"Not now, but soon enough"）。目前实例级治理是自托管专属。

**Q3：实时服务不是 NestJS 吗？**
不少架构文章仍把它写成 NestJS。实际以源码为准：当前仓库的 `apps/live` 由 Hocuspocus + Express 实现，依赖里没有任何 NestJS 相关包；自 v1.0.0 起的发布版本均可验证这一点。

**Q4：为什么 compose 里是 Valkey 而不是 Redis？**
Valkey 是 Redis 的开源兼容分支，命令与协议兼容，`django-redis`、`@hocuspocus/extension-redis` 均可直接对接。生产环境也可换成托管 Redis。

**常见部署错误与排查方向**：

| 现象 | 可能原因 | 排查动作 |
| --- | --- | --- |
| 收不到邀请邮件、密码重置失败 | SMTP 未配置或配置错误 | 官方文档明确建议部署后先配 SMTP；在 God Mode 的 Email 页检查 |
| 本地 compose 构建失败、容器内存崩溃 | 机器资源不足 | CONTRIBUTING.md 提示 8 GB 内存可能不够，换更大内存或 Codespaces |
| 普通用户看到 "instance not set up" 界面 | 实例初始化未完成 | 回到 `/god-mode` 完成 secure instance set-up |

## 十三、进阶方向

想继续深挖，下一步可以沿三条线走：

- **协同编辑**：读 Yjs 与 Hocuspocus 文档，理解 CRDT（无冲突复制数据类型）如何合并富文本，再看 `apps/live` 的 extension 目录
- **后端 API**：从 `apps/api/plane` 的 Django app 结构入手，追一条 issue 创建请求的完整链路（REST 视图 → serializer → model）
- **生产部署**：跟随官方 self-hosting 文档走一遍 Kubernetes 部署，重点看外部 PostgreSQL、外部存储的接法

## 参考文献与事实来源

一手来源（本文源码断言与数据的核对基准）：

- [makeplane/plane GitHub 仓库](https://github.com/makeplane/plane)：浅克隆 `--depth 1` 逐条核对
- [Plane README](https://github.com/makeplane/plane#readme)：产品定位、README 引文、功能列表、部署方式表
- [Plane CONTRIBUTING](https://github.com/makeplane/plane/blob/main/CONTRIBUTING.md)：本地开发流程与内存要求
- [Plane 自托管文档](https://developers.plane.so/self-hosting/overview)：部署方式与外部服务接入
- [Instance admin and God mode](https://developers.plane.so/self-hosting/govern/instance-admin)：God Mode 功能范围与 FAQ
- GitHub API 仓库数据（stars、open issues、forks）：查询于 2026 年 8 月 19 日

延伸阅读：

- [Hocuspocus](https://tiptap.dev/docs/hocuspocus)：TipTap 官方的 Yjs WebSocket 后端文档
- [Django REST Framework](https://www.django-rest-framework.org/)：API 层框架
- [Turborepo](https://turborepo.com/)：monorepo 构建编排工具
