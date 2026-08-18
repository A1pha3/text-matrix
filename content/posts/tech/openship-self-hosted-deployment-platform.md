---
title: "Openship：自托管应用部署平台，内置 CI/CD 与全栈后端"
date: 2026-08-19T03:26:14+08:00
slug: "openship-self-hosted-deployment-platform"
github_repo: "oblien/openship"
source_key: "gh:oblien/openship"
description: "Openship 是一个开源、可自托管的部署平台，内置 CI/CD。指向一个仓库，它自动构建、发布、路由并完成 TLS 终结，同时管理数据库、域名、SSL、CDN、邮件与备份，支持桌面应用、Web 仪表盘与 CLI 三种入口。"
draft: false
categories: ["技术笔记"]
tags: ["部署", "DevOps", "自托管", "CI/CD", "开源"]
---

# Openship：自托管应用部署平台，内置 CI/CD 与全栈后端

部署个人项目时，最烦的不是"把代码跑起来"，而是围绕它的一整圈附属设施：数据库要装、域名要配、HTTPS 要申请证书、邮件要搭、备份要计划。Openship 把这些全部收进一个自托管平台——你指向一个仓库，它负责构建、发布、路由、TLS 终结，以及背后的数据库、CDN 和邮件。

## 一分钟总览

Openship 是 oblien 开源的自托管部署平台（Apache 2.0，TypeScript 编写），内置 CI/CD。核心流程是一条从源码到上线的管道：

```
源码（GitHub 仓库 / 本地文件夹 / 预构建产物）
   → 检测（识别栈、包管理器、构建/启动命令、端口）
   → 构建（Docker 镜像或裸发布）
   → 运行（容器或受监督的宿主进程）
   → 路由 + 安全（反向代理 + Let's Encrypt TLS）
   → 上线（GitHub webhook 触发 push-to-deploy）
```

启动方式有三种：**桌面应用**（适合单人）、**自托管服务器**（`openship up`，适合团队与 push-to-deploy）、**Openship Cloud**（托管版，零运维）。

## 一个关键决策：Openship 自己怎么跑

项目 README 把第一决策点讲得很清楚——**你如何运行 Openship 控制平面**，其余都相同：

| 场景 | 运行方式 | 应用跑在哪 |
|------|---------|-----------|
| 单人、单机、不想运维 | **桌面应用** | 通过 SSH 连接的服务器，或 Openship Cloud |
| 团队、要 push-to-deploy、要自托管 | **自托管服务器**（`openship up`） | 本机（Compose 模式）或外部服务器/Cloud（bare 模式） |
| 不想运行任何东西 | **Openship Cloud** | 托管沙箱，零设置 |

桌面应用的控制平面只在应用打开时运行在本地，什么都不常驻、不对外暴露。只有当你需要 push-to-deploy（CI/CD）、团队访问或在这台机器上托管应用时，才需要一个常开的服务器。

## 上手：两种典型路径

### 单人：桌面应用

下载对应平台的安装包（macOS Apple Silicon/Intel、Windows、Linux），打开后通过 SSH 连接一台服务器或 Openship Cloud 就能部署。无需登录、无需终端、无公开面。

### 团队 / 常开：自托管服务器

```sh
curl -fsSL https://get.openship.io | sh     # 安装（或 npm i -g openship，需要 Node 22+）
openship                                     # 引导式初始化：创建管理员、绑定域名、注册为开机服务
```

`openship up` 会自动选择运行形态：

- **Linux 带 Docker → Compose 模式**（默认）：拉起完整栈——Postgres、Redis、API、仪表盘和容器化的 OpenResty edge（:80/:443），能在同一台机器上托管你的应用，自动域名 + Let's Encrypt TLS。
- **其他环境 → bare 模式**：单一轻量进程 + 内嵌数据库，常开控制平面，把应用部署到服务器（SSH）或 Cloud。

然后部署一个项目：

```sh
cd your-project
openship init            # 关联目录到项目
openship deploy
```

## 怎么工作的：五步管道

1. **检测**。读取 `package.json`、框架配置、lockfile，以及可选的 `docker-compose.yml` / `openship.json`，识别栈、包管理器、构建/启动命令和端口。零配置文件即可工作；`openship.json` 用于覆盖自动猜测。
2. **构建**。在目标服务器或本地编排器上构建成 Docker 镜像或裸发布，配置被冻结进快照，重部署和回滚会精确重跑当时发布的内容。
3. **运行**。容器（只在 loopback 发布，绝不开公网端口）或受监督的宿主进程。
4. **路由 + 安全**。OpenResty edge 为你的域名写反向代理 vhost，签发 Let's Encrypt 证书（HTTP-01）。因为路由和 TLS 在应用起来之后才做，DNS 或证书抖动只会显示为"需要处理"，不会让部署失败或把应用搞挂。
5. **Push-to-deploy**。GitHub webhook 在每次 push 到跟踪分支时重跑管道——monorepo 里只重建实际被改动的服务。

**数据库、域名、SSL、CDN、邮件、备份**都在同一处管理。push-to-deploy 和公网域名需要一个常开服务器或 Cloud——桌面/loopback 实例没有公网端点接收 webhook。

## 三种界面 + 两种自动化入口

同一个后端有三种驱动方式：**桌面应用**（完整 GUI、实时日志）、**Web 仪表盘**（浏览器中同一 UI，适合团队）、**CLI**（可脚本化、CI 友好，也是安装和管理自托管实例的方式）。

自动化方面还有 **MCP 端点**（给 AI Agent）和 **REST API**。MCP 只暴露选择进入的路由，每次调用重查权限，凭证/令牌路由永远不会变成工具。

## 内置能力一览

| 能力 | 说明 |
|------|------|
| 内置 CI/CD | push-to-deploy、预览环境、staging/prod 流程、回滚 |
| 任意技术栈 | Node、Python、Go、Rust、PHP、Ruby、Java、.NET、Docker、monorepo |
| 全栈后端 | Postgres、MySQL、MongoDB、Redis、workers、WebSockets、存储 |
| 域名与 SSL | 自动 Let's Encrypt、通配符、无限域名、自动续期 |
| CDN | 边缘缓存、HTTP/3、Brotli 压缩、即时清理 |
| 邮件服务器 | 内置 SMTP + DKIM/SPF/DMARC，无需 Mailgun 或 SES |
| 备份 | 定时、数据库 + 卷、一键恢复、随时导出 |
| 实时监控 | 实时构建日志、容器指标、按地区与状态码的访问分布 |
| 扩展 | 云端自动扩缩容，自托管多节点就绪 |
| 可移植 | 标准 Docker 容器，可自由迁移 |

## 适用边界

- **适合**：想自托管应用但不想被 K8s 复杂度淹没的个人开发者；想要开箱即用 CI/CD + 全栈后端的团队；对云厂商锁定有顾虑、想用标准 Docker 容器自由迁移的人。
- **不适合**：如果你已经有稳定的 CI/CD + 托管平台，且不需要自托管，Openship 的迁移成本可能不值；beta 边缘功能的稳定性需要自己评估。
- **注意**：`api` 容器挂载宿主 Docker socket 来构建和运行宿主容器——README 明确提醒"它通过 socket 拥有宿主权限，只应在可信主机上运行"。Compose 模式仅限 Linux（host 网络）。

## 小结论

Openship 的价值主张是**把部署从"一堆独立服务拼起来"变成"一个平台搞定"**——从源码到 HTTPS 域名再到数据库和邮件，都是同一套界面和同一条管道。对自托管爱好者来说，它提供了一条介于"裸机手动配 Nginx + Certbot"和"上 K8s"之间的中间路线，且核心代码开源、可审计。如果你想要一个自己能完全掌控的部署平台，值得给它一台服务器试试。
