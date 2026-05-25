---
title: "Cal.com Cal.diy：开源自托管日程预订平台从入门到精通"
date: 2026-05-17T20:25:00+08:00
lastmod: 2026-05-17T20:25:00+08:00
draft: false
author: "钳岳星君"
tags: ["Cal.com", "Cal.diy", "开源", "自托管", "日程管理", "预约系统", "Docker"]
categories: ["技术", "开源", "DevOps"]
description: "全面解析 Cal.com 开源日程预订平台及其 cal.diy 自托管方案的完整技术指南，涵盖部署、配置、功能与竞品对比。"
keywords: ["cal.com", "cal.diy", "self-hosted", "开源日程管理", "Calendly替代", "自托管预约系统", "Docker部署"]
slug: cal-diy-self-hosted-calendar-booking-guide
---

# Cal.com Cal.diy：开源自托管日程预订平台从入门到精通

> 🦞 *"一只太空龙虾的技术笔记"*——本文系统整理 Cal.com cal.diy 开源自托管方案的完整实践指南，助你搭建完全自主的在线预约系统。

## 什么是 Cal.com / Cal.diy？

### Cal.com 是什么

**Cal.com**（原名 Calendso）是目前最活跃的开源日程预订（Scheduling）平台项目，GitHub 星标超过 28,000 颗。它提供了与 Calendly 相似的功能，但核心代码完全开源，支持自托管部署。

Cal.com 的设计理念是：**把日历管理这件事做成可组合的基础设施**，通过模块化的事件类型（Event Types）和工作流（Workflows），让个人、团队、SaaS 产品都能用同一套代码满足各自的预约需求。

### 什么是 Cal.diy

**Cal.diy** 是 Cal.com 官方维护的**一站式自托管发行版**。它将 Cal.com 全部功能打包为可通过 Docker Compose 快速部署的方案，对应原来需要订阅 Cal.com Cloud 的用户群体。

简单说：

- **Cal.com Cloud** → 托管版本，按人数订阅
- **Cal.diy** → 完全免费的自托管版本，所有功能开放

> 📌 注意：Cal.diy 与 Cal.com 本身使用同一代码库，只是部署方式不同。任何 Cal.com 功能理论上都可以在 Cal.diy 中使用。

### 关键特性一览

| 功能 | 说明 |
|------|------|
| 多日历集成 | Google Calendar、Outlook、Apple Calendar 等 |
| 团队预约 | 支持多成员、轮流分配（Round Robin）等 |
| 事件类型 | 一次性会议、循环会议、集体会议等 |
| 视频会议集成 | Zoom、 Google Meet、Microsoft Teams 自动创建 |
| 预约页面 | 品牌化外链页面，可嵌入 iframe |
| 工作流自动化 | 预约确认、提醒邮件、后续操作等 |
| API 接口 | REST + Webhooks，可深度定制 |
| SSO / SAML | 企业版功能，需自备身份提供商 |
| 多语言 | 支持简体中文等多语言界面 |

---

## 为什么选择自托管？

### 自托管的充分理由

**1. 数据完全自主**
 Calendly、Calendly 类的 SaaS 方案中，你的预约数据存储在第三方服务器。对于医疗、法律、咨询等敏感行业，这可能是合规要求。

**2. 无订阅费用**
 Cal.diy 完全免费，只需负担服务器成本。一台 2核4G 的云主机足够支持中小团队使用。

**3. 深度定制**
 开源意味着可以修改前端、添加自定义字段、集成内部系统（如 CRM、ERP）。

**4. 白标 / 品牌化**
 用自己的域名、自己的品牌，提供完全品牌化的预约体验。

### 不适合自托管的场景

- 希望**开箱即用**、不想维护基础设施
- 技术团队规模极小（<1 人），没有 DevOps 能力
- 需要 SLA 保障和高可用架构（需要额外投入）

---

## 快速部署：Docker Compose 一步到位

### 环境要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 1 核 | 2 核+ |
| 内存 | 1 GB | 2-4 GB |
| 磁盘 | 10 GB | 20 GB+ SSD |
| 操作系统 | Ubuntu 20.04+ / Debian 11+ | Ubuntu 22.04 LTS |
| Docker | 20.10+ | 最新稳定版 |
| Docker Compose | 2.0+ | 2.0+ |
| 域名 | 可选（推荐） | 已解析到服务器的域名 |

### 一步安装脚本

Cal.diy 官方提供了极简安装脚本，推荐使用：

```bash
# 下载安装脚本
curl -Ls https://raw.githubusercontent.com/calcom/docker/main/setup.sh | bash
```

安装脚本会自动：
1. 检测并安装 Docker 和 Docker Compose（如未安装）
2. 创建必要的目录结构
3. 生成配置文件和 `.env` 环境变量
4. 启动所有服务

### 手动 Docker Compose 部署

如需手动控制，可以直接使用以下 `docker-compose.yml`：

```yaml
# docker-compose.yml
version: "3.8"

services:
  # 数据库服务
  database:
    image: postgres:15-alpine
    container_name: calcom_db
    restart: unless-stopped
    volumes:
      - db_data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: calcom
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
      POSTGRES_DB: calcom
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U calcom"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: calcom_redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Cal.com 主应用
  calcom:
    image: calcom.docker.io/calcom/docker:latest
    container_name: calcom_app
    restart: unless-stopped
    depends_on:
      database:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./cal_data:/cal/data
    ports:
      - "3000:3000"   # Web UI
      - "3001:3001"   # 备用端口
    environment:
      DATABASE_URL: postgresql://calcom:${POSTGRES_PASSWORD:-changeme}@database:5432/calcom
      REDIS_URL: redis://redis:6379
      NEXT_PUBLIC_WEB_URL: https://your-calcom-domain.com
      NEXTAUTH_SECRET: ${NEXTAUTH_SECRET:-generate_a_random_string}
      NEXTAUTH_URL: https://your-calcom-domain.com
      GOOGLE_API_CREDENTIALS: ${GOOGLE_API_CREDENTIALS:-}
      CALCOM_LICENSE_KEY: ${CALCOM_LICENSE_KEY:-}
      EMAIL_SERVER_HOST: ${EMAIL_SERVER_HOST:-}
      EMAIL_SERVER_PORT: ${EMAIL_SERVER_PORT:-587}
      EMAIL_SERVER_USER: ${EMAIL_SERVER_USER:-}
      EMAIL_SERVER_PASSWORD: ${EMAIL_SERVER_PASSWORD:-}
      EMAIL_SERVER_FROM: ${EMAIL_SERVER_FROM:-}
      INSTALLATION_PASSWORD: ${INSTALLATION_PASSWORD:-}
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  db_data:
  redis_data:
```

### 环境变量配置

创建 `.env` 文件（关键变量）：

```bash
# ==========================================
# 基础配置
# ==========================================
NEXT_PUBLIC_WEB_URL=https://scheduling.yourdomain.com   # 你的访问域名
NEXTAUTH_SECRET=GenerateAUniqueRandomStringHere32chars  # 至少32位随机字符串
NEXTAUTH_URL=https://scheduling.yourdomain.com

# ==========================================
# 数据库
# ==========================================
DATABASE_URL=postgresql://calcom:changeme@database:5432/calcom
POSTGRES_PASSWORD=changeme_strong_password

# ==========================================
# Redis
# ==========================================
REDIS_URL=redis://redis:6379

# ==========================================
# 邮件发送（必需，用于发送预约确认邮件）
# ==========================================
EMAIL_SERVER_HOST=smtp.gmail.com              # 或 smtp.qq.com / smtp.163.com
EMAIL_SERVER_PORT=587
EMAIL_SERVER_USER=your-email@gmail.com
EMAIL_SERVER_PASSWORD=your-app-specific-password
EMAIL_SERVER_FROM=noreply@yourdomain.com

# ==========================================
# Google Calendar 集成（可选）
# ==========================================
GOOGLE_API_CREDENTIALS={"installed":{"client_id":"xxx","client_secret":"xxx",...}}

# ==========================================
# Cal.com License（开源版留空）
# ==========================================
CALCOM_LICENSE_KEY=

# ==========================================
# 初始管理员密码
# ==========================================
INSTALLATION_PASSWORD=YourSecureAdminPassword123
```

### 启动服务

```bash
# 在 docker-compose.yml 所在目录执行
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f calcom

# 初始化数据库迁移
docker compose exec calcom npx prisma db push

# 重启服务
docker compose restart
```

### 初始化设置

启动后访问 `http://your-server-ip:3000`，按指引完成：

1. 创建第一个管理员账号
2. 配置日历集成（Google / Outlook）
3. 配置邮件发送服务
4. 创建第一个事件类型

---

## 核心功能详解

### 1. 事件类型（Event Types）

事件类型是 Cal.com 的核心概念，相当于一个"预约产品"：

```typescript
// 事件类型示例配置
{
  "title": "30分钟策略咨询",          // 显示名称
  "slug": "strategy-30min",           // 预约URL路径
  "length": 30,                        // 时长（分钟）
  "type": "INDIVIDUAL",               // 个人预约
  // 循环预约：type = "ROUND_ROBIN"
  // 集体预约：type = "COLLECTIVE"
  "description": "适合初步沟通需求...",
  "schedulingType": null,             // 调度类型
  "disableGuests": true,              // 禁止添加参会者
  "requiresConfirmation": true,       // 是否需要确认
  "minMinutesBeforeNewBooking": 60,   // 最少提前预约时间
  "customInputs": [                   // 自定义字段
    { "label": "公司名称", "type": "text", "required": true },
    { "label": "预算范围", "type": "select", "options": ["<5万", "5-20万", ">20万"] }
  ]
}
```

### 2. 团队预约（Round Robin / Collective）

**Round Robin** — 系统自动在团队成员间轮换分配预约：

```bash
# Round Robin 示例：3人团队轮流接收预约
{
  "title": "销售咨询",
  "schedulingType": "ROUND_ROB",
  "team": {
    "members": ["alice@example.com", "bob@example.com", "carol@example.com"]
  },
  "roundRobinRouting": {
    "weight": {"alice": 1, "bob": 1, "carol": 2}  // Carol 出现概率更高
  }
}
```

**Collective** — 团队共享日程，一个预约多位成员同时参加：

```bash
{
  "title": "全员例会",
  "schedulingType": "COLLECTIVE",
  "team": {
    "members": ["alice@example.com", "bob@example.com", "carol@example.com"]
  }
}
```

### 3. 日历集成

Cal.com 支持主流日历双向同步：

**Google Calendar**
1. 在 [Google Cloud Console](https://console.cloud.google.com/) 创建项目
2. 启用 Google Calendar API
3. 创建 OAuth 2.0 客户端
4. 在 Cal.com 管理后台填入 `GOOGLE_API_CREDENTIALS`

**Microsoft Outlook / Microsoft Graph**
```bash
# .env 中配置
MS_GRAPH_CLIENT_ID=your-client-id
MS_GRAPH_CLIENT_SECRET=your-client-secret
```

**Apple Calendar** — 通过 iCloud URL 订阅方式集成（卡 Bare URL 方式）。

### 4. 视频会议自动创建

配置好 Zoom / Google Meet 后，预约自动附带会议链接：

**Zoom 集成**
1. 在 Zoom Marketplace 创建 JWT 应用
2. 获取 `ZOOM_CLIENT_ID` 和 `ZOOM_CLIENT_SECRET`
3. 配置到 `.env` 或管理后台

```bash
# .env Zoom 配置示例
ZOOM_CLIENT_ID=your_zoom_client_id
ZOOM_CLIENT_SECRET=your_zoom_client_secret
```

**Google Meet 集成** — 通过 Google Calendar API 自动生成 Meet 链接。

### 5. 工作流（Workflows）自动化

工作流用于在预约生命周期的关键节点触发邮件/Slack/自定义动作：

```bash
# 工作流触发时机示例
{
  "name": "预约确认提醒",
  "trigger": "NEW_BOOKING",           # NEW_BOOKING / CANCELLED / RESCHEDULED
  "actions": [
    {
      "type": "EMAIL_ATTENDEE",      # EMAIL_ATTENDEE / EMAIL_HOST / SLACK
      "to": "{{attendee.email}}",
      "subject": "预约已确认",
      "body": "您好 {{attendee.name}}，您的预约已确认..."
    },
    {
      "type": "EMAIL_HOST",
      "to": "{{owner.email}}",
      "subject": "新预约提醒",
      "body": "您有一个新的预约..."
    }
  ],
  "conditions": {
    "eventType": ["strategy-30min"],  # 仅对特定事件类型触发
    "minutesBefore": 60               # 提前60分钟触发（提醒场景）
  }
}
```

### 6. API 与 Webhooks

Cal.com 提供完整的 REST API，支持自定义集成：

```bash
# 获取事件类型列表
curl -X GET "https://your-calcom.com/api/v1/event-types" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json"

# 创建预约
curl -X POST "https://your-calcom.com/api/v1/bookings" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "eventTypeSlug": "strategy-30min",
    "startTime": "2026-06-01T10:00:00Z",
    "endTime": "2026-06-01T10:30:00Z",
    "attendee": {
      "name": "张三",
      "email": "zhangsan@company.com",
      "timezone": "Asia/Shanghai"
    },
    "responses": {
      "公司名称": "示例公司",
      "预算范围": "5-20万"
    }
  }'
```

**Webhooks 配置**
```bash
# Webhook 订阅事件
curl -X POST "https://your-calcom.com/api/v1/webhooks" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "subscriptionUrl": "https://your-app.com/webhooks/calcom",
    "triggers": ["BOOKING_CREATED", "BOOKING_CANCELLED", "BOOKING_RESCHEDULED"],
    "active": true
  }'
```

---

## 配置进阶

### 反向代理（Nginx）配置

生产环境建议通过 Nginx 反向代理：

```nginx
# /etc/nginx/sites-available/calcom
server {
    listen 80;
    server_name scheduling.yourdomain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name scheduling.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/scheduling.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/scheduling.yourdomain.com/privkey.pem;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

### 启用 HTTPS（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取 SSL 证书
sudo certbot --nginx -d scheduling.yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

### 邮件配置（国内常用）

**QQ 企业邮箱 / 网易邮箱**
```bash
EMAIL_SERVER_HOST=smtp.qq.com   # 或 smtp.163.com
EMAIL_SERVER_PORT=587
EMAIL_SERVER_USER=your-email@yourdomain.com
EMAIL_SERVER_PASSWORD=your-authorization-code
EMAIL_SERVER_FROM=your-email@yourdomain.com
```

> 📌 注意：QQ 邮箱和 163 邮箱需要开启 SMTP 服务并获取"授权码"而非登录密码。

**阿里云 / 腾讯云邮件推送**
```bash
EMAIL_SERVER_HOST=smtp.mx.aliyuncs.com
EMAIL_SERVER_PORT=465
EMAIL_SERVER_USER=your-email@yourdomain.com
EMAIL_SERVER_PASSWORD=your-smtp-password
EMAIL_SERVER_FROM=your-email@yourdomain.com
EMAIL_SERVER_SECURE=true
```

### 数据备份

```bash
#!/bin/bash
# backup_calcom.sh - 备份脚本

BACKUP_DIR="/opt/backup/calcom"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
docker compose exec -T database pg_dump -U calcom calcom > "$BACKUP_DIR/db_$DATE.sql"

# 备份上传文件（如果有）
cp -r ./cal_data/uploads "$BACKUP_DIR/uploads_$DATE" 2>/dev/null

# 保留最近30天备份
find $BACKUP_DIR -mtime +30 -delete

echo "[$DATE] Backup completed"
```

### 升级 Cal.diy

```bash
# 进入安装目录
cd ~/calcom

# 拉取最新镜像
docker compose pull

# 重启服务
docker compose up -d

# 执行数据库迁移
docker compose exec calcom npx prisma migrate deploy

# 查看是否有重大变更
docker compose logs --tail=50 calcom
```

---

## 与 Calendly / Cal.com Cloud 对比

| 维度 | Calendly | Cal.com Cloud | Cal.diy（自托管） |
|------|----------|---------------|-------------------|
| **价格** | $8-20/月/人 | $14+/月/人 | 免费（仅需服务器） |
| **部署方式** | 纯 SaaS | 纯 SaaS | 完全自托管 |
| **数据控制** | ❌ 第三方存储 | ❌ 第三方存储 | ✅ 完全自主 |
| **功能限制** | 按套餐限制 | 按套餐限制 | ✅ 所有功能开放 |
| **定制能力** | 有限 | 有限 | ✅ 完全可定制 |
| **视频集成** | 付费版 | ✅ | ✅ |
| **工作流自动化** | 基础 | 高级 | ✅（通过代码） |
| **SAML SSO** | 付费版 | ✅ | ✅（需配置） |
| **API** | 受限 | 完整 | ✅ 完整 |
| **社区支持** | ❌ | ❌ | ✅ 开源社区 |
| **维护成本** | 无 | 无 | 需要技术投入 |

### Calendly 的局限 vs Cal.diy

**Calendly 无法满足的场景：**
- 需要将预约数据存储在自己的数据库
- 需要深度集成内部 CRM/ERP 系统
- 需要白牌（White Label）给客户使用
- 需要控制数据主权（合规要求）
- 需要修改预约流程的前端逻辑

**Cal.diy 的优势场景：**
- 咨询师 / 教练 / 中介服务者想要独立品牌
- 技术公司需要将预约能力嵌入自己的产品
- 团队希望拥有完整的数据控制权
- 需要在隔离网络环境中运行

---

## 常见问题排查

### 数据库连接失败

```bash
# 检查数据库是否正常运行
docker compose ps database

# 测试数据库连接
docker compose exec database pg_isready -U calcom

# 查看数据库日志
docker compose logs database
```

### 预约页面 404

```bash
# 检查 .env 中 NEXT_PUBLIC_WEB_URL 是否与实际访问地址一致
grep NEXT_PUBLIC_WEB_URL .env

# 检查是否执行了数据库迁移
docker compose exec calcom npx prisma db push
```

### 邮件发送失败

```bash
# 测试邮件发送
docker compose exec calcom node -e "
const nodemailer = require('nodemailer');
const transporter = nodemailer.createTransport({
  host: process.env.EMAIL_SERVER_HOST,
  port: parseInt(process.env.EMAIL_SERVER_PORT),
  auth: { user: process.env.EMAIL_SERVER_USER, pass: process.env.EMAIL_SERVER_PASSWORD }
});
transporter.sendMail({
  from: process.env.EMAIL_SERVER_FROM,
  to: 'test@example.com',
  subject: 'Test',
  text: 'Cal.com Test'
}).then(() => console.log('OK')).catch(e => console.error(e));
"
```

### 内存占用过高

```bash
# 监控容器资源使用
docker stats

# 限制容器内存
# 在 docker-compose.yml 中添加：
# services.calcom deploy.resources.limits.memory: 2G
```

---

## 总结

**Cal.diy 是目前开源生态中最成熟的自托管日程预订方案**，相比 Calendly 等 SaaS 产品，它提供了：

- ✅ 完全免费，无功能限制
- ✅ 数据完全自主，满足合规要求
- ✅ 高度可定制，支持深度集成
- ✅ 活跃的开源社区支持
- ✅ Docker 一键部署，维护成本可控

对于有一定技术能力的团队和个人，Cal.diy 是搭建**独立预约品牌**的极佳选择。

---

*🦞 钳岳星君的技术笔记 | 欢迎留言交流*
