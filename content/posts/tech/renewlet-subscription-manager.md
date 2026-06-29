---
title: "Renewlet：一站式自托管订阅管理工具，把所有 SaaS 续费管起来"
date: "2026-05-17T11:59:04+08:00"
slug: "renewlet-self-hosted-subscription-manager"
description: "Renewlet 是一个开源自托管订阅管理工具，支持同时管理 SaaS、AI 工具、云服务和开发工具的订阅信息、续费提醒和支出统计，前端用 React 19，后端用 Go + PocketBase，单容器一键部署。"
draft: false
categories: ["技术笔记"]
tags: ["订阅管理", "自托管", "Docker", "PocketBase", "Go", "React", "SaaS"]
---

## 学习目标

通过本文，你将掌握以下核心能力：

- 理解 Renewlet 的技术架构和 Design Choices（Go + PocketBase + React 19）
- 掌握一键 Docker 部署的完整流程
- 学会配置多种通知渠道（Telegram、企业微信、Webhook 等）
- 理解内置调度器与外部调度器的取舍
- 能够判断 Renewlet 是否适合你的场景

## 目录

1. [项目概览](#项目概览)
2. [技术架构](#技术架构)
3. [核心功能](#核心功能)
4. [快速部署](#快速部署)
5. [常用运维命令](#常用运维命令)
6. [适用场景与边界](#适用场景与边界)
7. [自测题](#自测题)
8. [练习](#练习)
9. [进阶路径](#进阶路径)

---

## 项目概览

**Renewlet**（[zhiyingzzhou/renewlet](https://github.com/zhiyingzzhou/renewlet)）是一个自托管的订阅管理工具，用一个界面把个人或团队用到的 SaaS、AI 工具、云服务和开发工具统一管起来：谁在什么时候扣费、每月花多少钱、哪些服务快到期、通知要发到哪里。

核心特点：

- 全平台覆盖：SaaS、AI 工具、云服务、开发工具均可录入
- 多币种换算：自动按汇率折算月度成本
- 多种通知渠道：Telegram、Notifyx、Webhook、企业微信机器人、SMTP 邮件、Bark
- 单容器部署：一个 Docker 镜像同时跑前端、后端 API 和 PocketBase Admin
- 中英文界面

## 技术架构

当前代码库采用前后端分离结构：

| 包 | 技术栈 | 职责 |
|---|---|---|
| `packages/client` | Vite + React 19 | 单页应用界面、主题、多语言 |
| `packages/server` | Go + PocketBase | 业务 API、数据模型、认证、文件存储 |

Docker 部署时，Go binary 以外部进程形式运行 PocketBase，提供 PocketBase 原生 API 和 Admin UI。SQLite 数据库保存在宿主机的 `data/` 目录或 Docker volume 中。

### 技术选型思路

用 Go + PocketBase 而非直接用某个成熟框架，有几个实际好处：PocketBase 内置了 Admin UI 和认证体系，省去了管理面板的开发量；Go 作为 Runtime，内存占用低，单容器 128MiB GOMEMLIMIT 就够跑起来；SQLite 作为存储引擎，备份和迁移都是单文件，不需要额外部署数据库服务。

React 19 选型也比较务实——如果你需要在前端快速出产品原型，React 19 + Vite 的组合足够成熟，生态丰富，不需要为了"新"而引入额外风险。

## 核心功能

### 订阅记录管理

每条订阅可记录以下字段：

- 名称、Logo（自动拉取服务图标）
- 价格与币种（支持多币种，自动换算）
- 扣费周期：月付、季付、年付等
- 续费日期与续费状态
- 付款方式（信用卡、PayPal 等）
- 分类与标签
- 服务地址、备注

### 续费提醒

按用户设置的时区和提前提醒天数，自动在指定时间生成通知。发送历史会被记录，失败的任务支持手动重试。

### 多币种支持

可选择 Frankfurter 或 FloatRates 作为汇率来源。远端汇率服务不可用时，会回退到本地缓存的备用汇率，避免换算中断。

### 支出统计

仪表盘会自动把不同周期的费用折算成月度成本，展示：

- 总预算与已使用额度
- 各分类支出占比
- 各付款方式占比
- 已停用订阅节省了多少

### 续费日历

按月展示所有订阅的续费事件和预计支出，适合在月初做预算规划时一眼扫过本月续费情况。

## 快速部署

### 前提条件

- 一台有 Docker 和 Docker Compose v2 的服务器（或树莓派）
- 域名（非必需，直接 IP:Port 访问也行）

### 一键部署

```bash
mkdir -p renewlet && cd renewlet
curl -fsSL https://raw.githubusercontent.com/zhiyingzzhou/renewlet/main/deploy/docker-deploy.sh | bash
docker compose up -d
```

脚本会自动：

- 下载 `docker-compose.yml` 和 `.env` 模板
- 生成随机的 `PB_ENCRYPTION_KEY` 和 `CRON_SECRET`
- 创建 `data/` 目录用于持久化 SQLite

部署完成后，访问 `http://<服务器IP>:3000/setup` 创建第一个管理员账号。这个账号同时也是 PocketBase Admin UI 的初始账号。

### 配置通知渠道

在应用内配置各通知渠道的凭据，支持：Telegram Bot、Notifyx、Webhook、企业微信机器人、SMTP 邮件、Bark（iOS 推送）。

### 定时通知调度

应用内置了一个通知调度器，按 `NOTIFICATION_SCHEDULER_CRON`（默认每分钟）检查所有用户的提醒设置，到期自动发送。

如果用 Vercel Cron、GitHub Actions 或宿主机的 crontab 做外部调度，可以关闭内置调度器：

```env
NOTIFICATION_SCHEDULER_ENABLED="false"
CRON_SECRET="CHANGE_ME_TO_A_RANDOM_SECRET"
```

外部调用方式：

```bash
curl -H "Authorization: Bearer $CRON_SECRET" "https://YOUR_DOMAIN/api/cron/notifications"
```

调试时加 `dryRun=1` 只跑逻辑不实际发通知，`force=1` 可强制触发。

## 常用运维命令

```bash
# 查看状态
docker compose ps

# 查看日志
docker compose logs -f

# 升级到最新版本
tar -czf renewlet-backup-$(date +%F).tgz .env docker-compose.yml data
docker compose pull && docker compose up -d
```

## 适用场景与边界

**适合的场景：**

- 个人同时订阅了大量 SaaS 工具，续费日期不透明
- 小团队需要统一管理成员的工具订阅和预算
- 家庭实验室想追踪各项云服务开支
- 技术团队想把订阅管理放在内网，不依赖第三方

**不适合的场景：**

- 需要多用户权限隔离和审计日志的企业管理场景（当前架构是单容器单数据库，无细粒度 RBAC）
- 需要自动从信用卡账单抓取订阅的服务（目前是纯手动录入）

## 自测题

1. **Renewlet 的技术栈是什么？为什么选择这个组合？**
   <details>
   <summary>查看答案</summary>
   答案：前端用 React 19（Vite），后端用 Go + PocketBase。选择理由：PocketBase 内置 Admin UI 和认证体系，省去管理面板开发量；Go 内存占用低，单容器 128MiB 够跑；React 19 + Vite 生态成熟。
   </details>

2. **Renewlet 的通知调度有哪两种模式？**
   <details>
   <summary>查看答案</summary>
   答案：内置调度器（默认每分钟检查）和外部调度器（Vercel Cron、GitHub Actions、crontab）。可以在 `.env` 中设置 `NOTIFICATION_SCHEDULER_ENABLED="false"` 关闭内置调度器。
   </details>

3. **如果想在外部系统中触发通知检查，应该调用哪个接口？**
   <details>
   <summary>查看答案</summary>
   答案：`curl -H "Authorization: Bearer $CRON_SECRET" "https://YOUR_DOMAIN/api/cron/notifications"`。可以加 `dryRun=1` 只跑逻辑不实际发通知，加 `force=1` 强制触发。
   </details>

4. **Renewlet 适合多用户权限隔离的企业场景吗？**
   <details>
   <summary>查看答案</summary>
   答案：不适合。当前架构是单容器单数据库，无细粒度 RBAC（基于角色的访问控制）。
   </details>

5. **部署完成后，第一次访问应该打开哪个 URL？**
   <details>
   <summary>查看答案</summary>
   答案：`http://<服务器IP>:3000/setup`，用于创建第一个管理员账号（同时也是 PocketBase Admin UI 的初始账号）。
   </details>

---

## 练习

1. **在自己的服务器或本地 Docker 环境部署 Renewlet**，完成初始化配置，并添加 3 条订阅记录（选择你实际在用的 SaaS 工具）。
2. **配置一个通知渠道**（推荐用 Telegram Bot 或 Bark），设置一个订阅的提前提醒（比如提前 3 天），验证通知是否能正常到达。
3. **尝试用外部 crontab 触发通知检查**：在宿主机上添加一条 crontab 记录，每天固定时间调用 `/api/cron/notifications` 接口，并观察日志输出。

---

## 进阶路径

1. **深入 PocketBase**：阅读 PocketBase 文档，理解其数据模型、认证体系和 Admin UI 的定制方式。
2. **定制通知模板**：修改后端代码，支持更丰富的通知内容（比如附上订阅详情链接、月度成本图表等）。
3. **集成账单抓取**：研究如何通过信用卡账单 API 或邮件解析自动抓取订阅记录，减少手动录入。
4. **多用户场景**：如果确实需要团队多人使用，可以基于 PocketBase 的多租户能力做二次开发，或等待官方支持。
5. **备份与迁移**：研究 PocketBase 的备份机制，确保 `data/` 目录定期备份到远程存储。

---

## 资料口径说明

1. **信息来源**：本文基于 Renewlet 仓库的 README、部署脚本和源码结构编写，所有技术细节均来自官方文档和可验证的代码示例。
2. **版本时效性**：Renewlet 处于活跃开发阶段，具体配置项、环境变量和 API 接口可能随版本变化，请以仓库最新代码为准。
3. **部署前提**：本文的部署步骤假设读者有基本的 Docker 和 Linux 命令行使用经验，生产环境请额外考虑 HTTPS、备份、监控等运维需求。
4. **通知渠道可用性**：Telegram Bot、企业微信机器人等外部服务需要自行申请凭据，本文不涉及第三方服务的申请流程。
5. **适用性判断**：本文给出的「适用场景与边界」基于技术架构分析，实际选型请结合团队规模、预算、合规要求综合判断。
6. **示例与事实边界**：本文中的命令示例来自官方部署脚本，实际执行时请先阅读脚本内容，理解每一步的行为后再执行。

---

## 总结

Renewlet 把"订阅管理"这个看似简单、实际上很碎片化的事情做成了自托管方案。技术选型务实——Go + PocketBase + React，单容器部署，没有引入多余的东西。不想每个月被意外扣费、想搞清楚钱花在哪里的个人开发者和小型团队，可以试试。

**链接汇总：**

- GitHub：[zhiyingzzhou/renewlet](https://github.com/zhiyingzzhou/renewlet)
- 部署脚本：[deploy/docker-deploy.sh](https://github.com/zhiyingzzhou/renewlet/blob/main/deploy/docker-deploy.sh)