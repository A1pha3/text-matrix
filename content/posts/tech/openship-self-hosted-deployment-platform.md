---
title: "Openship：自托管应用部署平台，内置 CI/CD 与全栈后端"
date: 2026-08-19T03:26:14+08:00
slug: "openship-self-hosted-deployment-platform"

github_repo: "oblien/openship"
source_key: "gh:oblien/openship"
description: "Openship 是一个开源、可自托管的部署平台，内置 CI/CD。指向一个仓库，它自动构建、发布、路由并完成 TLS 终结，同时管理数据库、域名、SSL、CDN、邮件与备份，支持桌面应用、Web 仪表盘与 CLI 三种入口。"
categories: ["技术笔记"]
tags: ["部署", "DevOps", "自托管", "CI/CD", "开源"]
---

# Openship：自托管应用部署平台，内置 CI/CD（持续集成/持续部署）与全栈后端

部署个人项目时，最烦的不是"把代码跑起来"，而是围绕它的一整圈附属设施：数据库要装、域名要配、HTTPS 要申请证书、邮件要搭、备份要计划。Openship 把这些全部收进一个自托管平台——你指向一个仓库，它负责构建、发布、路由、TLS（传输层安全协议）终结，以及背后的数据库、CDN（内容分发网络）和邮件。

本文的目标是讲清三件事：Openship 的控制平面有几种跑法、从源码到上线的管道如何工作、它适合谁又不适合谁。读完你应能判断：自己的项目该用桌面应用、自托管服务器还是 Openship Cloud。

> 仓库数据（GitHub 应用程序接口（API），2026-08-19 核实）：`oblien/openship`，11,045 stars / 944 forks，主语言 TypeScript，Apache-2.0 协议，2026 年 3 月创建，至今保持每日级更新。

## 一分钟总览

Openship 是 oblien 开源的自托管部署平台，内置 CI/CD（持续集成/持续部署）。核心流程是一条从源码到上线的管道：

```text
源码（GitHub 仓库 / 本地文件夹 / 预构建产物）
   → 检测（识别栈、包管理器、构建/启动命令、端口）
   → 构建（Docker 镜像或裸发布）
   → 运行（容器或受监督的宿主进程）
   → 路由 + 安全（反向代理 + Let's Encrypt TLS）
   → 上线（GitHub webhook 触发 push-to-deploy）
```

启动方式有三种：**桌面应用**（适合单人）、**自托管服务器**（`openship up`，适合团队与 push-to-deploy（推送即部署））、**Openship Cloud**（托管版，零运维）。

## 目录

- [一个关键决策：Openship 自己怎么跑](#一个关键决策openship-自己怎么跑)
- [上手：两种典型路径](#上手两种典型路径)
- [怎么工作的：五步管道](#怎么工作的五步管道)
- [三种界面与两种自动化入口](#三种界面与两种自动化入口)
- [内置能力一览](#内置能力一览)
- [适用边界](#适用边界)
- [动手练习](#动手练习)
- [常见问题](#常见问题)
- [进阶与下一步](#进阶与下一步)
- [参考文献](#参考文献)

## 一个关键决策：Openship 自己怎么跑

项目 README 把第一决策点讲得很清楚——**你如何运行 Openship 控制平面**，其余都相同：

| 场景 | 运行方式 | 应用跑在哪 |
|------|---------|-----------|
| 单人、单机、不想运维 | **桌面应用** | 通过 SSH（安全外壳协议）连接的服务器，或 Openship Cloud |
| 团队、要 push-to-deploy、要自托管 | **自托管服务器**（`openship up`） | 本机（Compose 模式）或外部服务器/Cloud（bare 模式） |
| 不想运行任何东西 | **Openship Cloud** | 托管沙箱，零设置 |

桌面应用的控制平面只在应用打开时运行在本地，什么都不常驻、不对外暴露。只有当你需要 push-to-deploy、团队访问或在这台机器上托管应用时，才需要一个常开的服务器——这些场景都需要一个公网可达、长期在线的端点。

## 上手：两种典型路径

### 单人：桌面应用

下载对应平台的安装包（macOS Apple Silicon/Intel、Windows、Linux AppImage），打开后连接一台服务器（SSH）或 Openship Cloud 就能部署。无需登录、无需终端、无公开面。已经装了 CLI（命令行工具）的话，`openship install` 可以直接拉取并启动桌面应用，下载链接永远指向最新版本。

注意桌面应用本身不在你的笔记本上托管公网应用——它是控制平面，应用跑在你连接的服务器或 Cloud 上。

### 团队 / 常开：自托管服务器

```sh
curl -fsSL https://get.openship.io | sh     # 安装（或 npm i -g openship，需要 Node 22+）
openship                                     # 引导式初始化：创建管理员、绑定域名、注册为开机服务
```

安装脚本在系统 Node（节点，JavaScript 运行时）低于 22 时会自带一个 Node 运行时；走包管理器安装则使用你已有的 Node。初始化向导随时可以重跑，用来管理已有实例。

CI 或无头服务器上可以跳过向导，直接驱动 `openship up`：

```sh
openship up                                            # 安装并注册为后台服务（开机自启 + 自动重启）
openship up --public-url https://openship.example.com  # 同时把仪表盘挂到你的域名（边缘路由 + TLS 自动处理）
```

`openship up` 会自动选择运行形态：

- **Linux 带 Docker → Compose 模式**（默认，可用 `--compose` 强制）：拉起完整栈——Postgres、Redis、API、仪表盘和容器化的 OpenResty edge（:80/:443），能在同一台机器上托管你的应用，自动域名 + Let's Encrypt TLS。
- **其他环境 → bare 模式**（可用 `--bare` 强制）：单一轻量进程 + 内嵌数据库，常开控制平面，把应用部署到外部服务器（SSH）或 Cloud，类似桌面应用但长期在线且要求登录。

自托管实例**始终要求登录**（用初始化时创建的管理员）。日常管理命令：`openship open` 打开仪表盘、`openship stop` 停止、`openship update` 升级、`openship up --foreground` 前台运行。

然后部署一个项目：

```sh
cd your-project
openship init            # 关联目录到项目
openship deploy
```

## 怎么工作的：五步管道

1. **检测**。读取 `package.json`、框架配置、lockfile，以及可选的 `docker-compose.yml` / `openship.json`，识别栈、包管理器、构建/启动命令和端口。零配置文件即可工作；`openship.json` 是权威覆盖层——自动检测先跑，文件里出现的字段（如 `buildCommand`、`startCommand`、`port`、`env`、`domains`）逐项覆盖检测结果，未出现的字段保留检测值。
2. **构建**。在目标服务器或本地编排器上构建成 Docker 镜像或裸发布，配置被冻结进快照，重部署和回滚会精确重跑当时发布的内容。
3. **运行**。容器只在 loopback 发布，绝不开公网端口；或作为受监督的宿主进程运行。
4. **路由 + 安全**。OpenResty edge 为你的域名写反向代理 vhost，签发 Let's Encrypt 证书（HTTP-01 验证）。为什么路由和 TLS 放在应用起来之后才做？因为这样 DNS（域名系统）或证书抖动只会显示为"需要处理"，不会让部署失败或把应用搞挂——基础设施问题与发布流程解耦。
5. **Push-to-deploy**。GitHub Webhook（HTTP 回调通知）在每次推送（push）到跟踪分支时重跑管道——monorepo（单仓库）里只重建实际被改动的服务。

**数据库、域名、SSL、CDN、邮件、备份**都在同一处管理。push-to-deploy 和公网域名需要一个常开服务器或 Cloud——桌面/loopback 实例没有公网端点接收 webhook。

## 三种界面与两种自动化入口

同一个后端有三种驱动方式：

| 界面 | 特点 | 适合 |
|------|------|------|
| **桌面应用** | 完整 GUI（图形用户界面）、实时日志、一键操作 | 单人 |
| **Web 仪表盘** | 浏览器中同一套 UI | 团队 |
| **CLI** | 可脚本化、CI 友好，也是安装和管理自托管实例的方式 | 自动化 |

自动化方面还有 **MCP（模型上下文协议）端点**（给 AI Agent（智能体）用）和 **REST API**。REST 全称表述性状态转移。MCP 只暴露选择进入（opt-in）的路由，每次调用重查权限，凭证/令牌路由永远不会变成工具。

## 内置能力一览

| 能力 | 说明 |
|------|------|
| 内置 CI/CD | push-to-deploy、预览环境、staging/prod 流程、回滚 |
| 任意技术栈 | Node、Python、Go、Rust、PHP、Ruby、Java、.NET、Docker、monorepo |
| 全栈后端 | Postgres、MySQL、MongoDB、Redis、workers、WebSockets、存储 |
| 域名与 SSL | 自动 Let's Encrypt、通配符、无限域名、自动续期 |
| CDN | 边缘缓存、HTTP/3、Brotli 压缩、即时清理 |
| 邮件服务器 | 内置 SMTP（简单邮件传输协议）+ DKIM/SPF/DMARC，无需 Mailgun 或 SES |
| 备份 | 定时、数据库 + 卷、一键恢复、随时导出 |
| 实时监控 | 实时构建日志、容器指标、按地区与状态码的访问分布 |
| 扩展 | 云端自动扩缩容，自托管多节点就绪 |
| 可移植 | 标准 Docker 容器，可自由迁移 |
| Docker Compose | 现有 compose 文件原样部署 |

监控的实现成本很低：每个访客请求只增加约 1.4 µs 的内存计数操作，且**每个请求零数据库写入**（统计按天聚合落库，来源见 docs/monitoring.md）。

部署目的地不挑：Openship Cloud、任意 VPS（Hetzner、DigitalOcean、Linode、OVH 等）、专用服务器（裸金属、托管机房、家庭实验室）、多服务器混布——界面完全一致。

## 适用边界

- **适合**：想自托管应用但不想被 K8s 复杂度淹没的个人开发者；想要开箱即用 CI/CD + 全栈后端的团队；对云厂商锁定有顾虑、想用标准 Docker 容器自由迁移的人。
- **不适合**：如果你已经有稳定的 CI/CD + 托管平台，且不需要自托管，Openship 的迁移成本可能不值。
- **注意安全面**：`api` 容器挂载宿主 Docker socket（套接字）来构建和运行宿主容器——README 明确提醒"它通过 socket 拥有宿主权限，只应在可信主机上运行"。Compose 模式仅限 Linux（host 网络）。
- **成熟度**：项目自述核心已生产可用，自托管免费、无计费；多节点集群、负载均衡 UI、私有网络、可视化 CI/CD 管道仍在路线图上，尝鲜前自行评估。

## 动手练习

1. **五分钟体验检测逻辑**：随便找一个带 `package.json` 的项目跑 `openship init && openship deploy`，观察它自动识别出的栈、构建命令和端口，再写一个 `openship.json` 覆盖其中一项（示例：`{"buildCommand": "npm run build:prod", "port": 3000}`），对比检测差异。
2. **验证回滚语义**：部署 v1 后改一行代码重新部署，再执行回滚——确认回滚重放的是快照里冻结的内容，而不是当前目录。
3. **观察故障降级**：故意把域名的 DNS 解析停掉再部署，确认部署本身成功、仪表盘把证书签发标为"需要处理"，体会"路由/TLS 后置"的设计。

## 常见问题

**桌面应用能直接托管公网网站吗？**
不能。桌面应用只是本地控制平面，应用要部署到你 SSH 连接的服务器或 Openship Cloud 上才有公网入口。

**自托管一定要 Docker 吗？**
不一定。Linux 有 Docker 时默认走 Compose 模式并在本机托管应用；macOS、Windows 或无 Docker 的 Linux 自动降级为 bare 模式，应用部署到外部服务器或 Cloud。

**不用 CLI，纯 Docker Compose 能自托管吗？**
可以。仓库 `docker/docker-compose.yml` 直接拉取 `ghcr.io/oblien/*` 发布镜像（postgres + redis + api + dashboard（仪表盘）+ edge），无需构建工具；仅支持 Linux（host 网络）。注意宿主操作（:80/:443 接管、邮件引擎等）需要容器到宿主的 SSH 通道，这条路径默认不配置，部署本身不受影响。

**升级会不会动到我的数据？**
`openship update` 只处理 CLI 安装的栈；手写的 Compose 部署应通过 `.env` 固定 `OPENSHIP_VERSION` 后手动拉取（pull）并重启：`pull && up -d`。不要对非 CLI 安装的实例跑 `openship up`，它会"收养"该实例。

**部署失败从哪里排查？**
先看仪表盘的实时构建日志（检测、构建、运行每一步都有输出）；DNS/证书类问题不会导致部署失败，会以"需要处理"状态单独呈现；宿主操作类错误参考官方文档的 Troubleshooting 章节。

## 进阶与下一步

- **Shell 补全**：`openship completion <bash|zsh|fish>` 生成静态补全文件，或在 shell 配置里 source 动态补全，后者始终跟随当前安装版本。
- **尝鲜未发布构建**：`curl -fsSL https://get.openship.io/dev | sh` 安装独立的 `openship-dev` 命令（自带隔离目录 `~/.openship-dev` 与开机服务），不影响生产实例；需要 Bun + git，仅限开发验证。
- **路线图上值得关注的**：多节点集群、负载均衡 UI、私有网络、高级监控与可视化 CI/CD 管道。

## 小结论

Openship 的价值主张是**把部署从"一堆独立服务拼起来"变成"一个平台搞定"**——从源码到 HTTPS 域名再到数据库和邮件，都是同一套界面和同一条管道。对自托管爱好者来说，它提供了一条介于"裸机手动配 Nginx + Certbot"和"上 K8s"之间的中间路线，且核心代码开源、可审计。如果你想要一个自己能完全掌控的部署平台，值得给它一台服务器试试。

## 参考文献

- Openship 仓库与 README：[github.com/oblien/openship](https://github.com/oblien/openship)
- 官方文档与 CLI 参考：[openship.io/docs](https://openship.io/docs)
- 监控设计说明：仓库内 `docs/monitoring.md`
- npm 包：[npmjs.com/package/openship](https://www.npmjs.com/package/openship)
