---
title: "listmonk：从入门到精通的自托管邮件通讯平台完全指南"
date: 2026-05-17
draft: false
tags: ["邮件", "自托管", "Newsletter", "邮件列表", "SMTP", "Go"]
categories: ["技术指南"]
description: "全面介绍 listmonk——一款用 Go 编写的开源自托管邮件 Newsletter 和邮件列表管理平台，涵盖安装配置、SMTP 对接、运营管理和 API 开发。"
slug: listmonk-self-hosted-email-newsletter-platform-guide
---

## 什么是 listmonk？

[listmonk](https://github.com/knadh/listmonk)（[listmonk.org](https://listmonk.org)）是由印度开发者 [knadh](https://github.com/knadh) 用 Go 语言编写的**自托管邮件 Newsletter 和邮件列表管理平台**。它将 Newsletter 编辑、订阅者管理、投递追踪和数据分析全部整合在一个轻量、优雅的 Web 管理后台中，无需依赖任何第三方邮件服务即可独立运行。

作为 Mailchimp、ConvertKit 等商业平台的开放替代方案，listmonk 的核心理念是：**你的数据、你的服务器、你的规则**。

> **项目地址：** https://github.com/knadh/listmonk  
> ** LICENSE：** AGPLv3  
> **技术栈：** Go + PostgreSQL + Vue.js（管理后台）

---

## 核心功能一览

### 📬 Newsletter 管理
- **多列表管理**：按主题、受众群体创建多个独立邮件列表
- **订阅者管理**：支持手动添加、CSV 批量导入、API 动态注册
- **双向订阅确认（Double Opt-in）**：有效防止垃圾邮件投诉
- **取消订阅（Unsubscribe）**：内置一键退订链接，完全符合 CAN-SPAM 和 GDPR
- **订阅偏好中心**：让用户自行管理偏好的邮件类别

### ✉️ Campaign（邮件活动）运营
- **富文本编辑器**：基于 HTML 模板的可视化编辑
- **草稿和定时发送**：支持草稿保存、按计划时间自动投递
- **A/B 主题行测试**：对比不同标题的打开率
- **批量发送与节流（Throttling）**：控制发送速率以适配 SMTP 服务商限制
- **TX（事务邮件）模式**：支持发送密码重置、订单确认等触发式邮件

### 📊 数据分析与追踪
- **打开率（Open Rate）** 和 **点击率（Click Rate）** 追踪
- **退回率（Bounce Rate）** 监控（硬退回/软退回区分）
- **退订率**统计
- **按订阅者维度查看**投递详情
- **导出 CSV 报表**

### 🔌 REST API 与二次开发
- 完整的 REST API，支持与第三方 CMS、CRM、自动化工具深度集成
- Webhook 钩子，支持投递事件回调通知
- 支持与 Matomo、PostHog 等分析平台联动

---

## 架构设计解析

```
┌─────────────────────────────────────────────────┐
│                   用户 / 管理员                   │
│                     浏览器                        │
└──────────────────────┬──────────────────────────┘
                       │ HTTP
┌──────────────────────┴──────────────────────────┐
│              listmonk Web Server                  │
│               (:9000 管理后台)                     │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │  Vue.js  │  │  Go API  │  │  SMTP Relay  │    │
│  │  Frontend│  │  Core    │  │  (发送邮件)   │    │
│  └──────────┘  └──────────┘  └──────────────┘    │
└──────────────────────┬──────────────────────────┘
                       │
         ┌─────────────┴─────────────┐
         │      PostgreSQL 数据库     │
         │  (订阅者 / 模板 / Campaign) │
         └───────────────────────────┘
```

**关键设计哲学：**
- **单二进制部署**：编译好的 Go 程序无外部依赖，直接运行
- **数据库存储一切**：PostgreSQL 承载所有状态，包括邮件内容和投递日志
- **SMTP 中继负责投递**：程序本身不直接连接 MTA，而是将邮件提交给外部 SMTP 服务商
- **追踪像素（Tracking Pixel）**：邮件中嵌入 1×1 透明图片，通过图片请求计数统计打开率

---

## 安装部署（Docker Compose）

### 前置要求

| 依赖 | 最低版本 | 建议 |
|------|---------|------|
| Docker | 20.10+ | 最新稳定版 |
| Docker Compose | 2.0+ | v2.x |
| PostgreSQL | 13+ | 16 |
| 内存 | 512 MB | 2 GB+ |
| SMTP 服务 | 任意 | SendGrid / AWS SES / Mailgun / 自建 Postfix |

### Step 1：创建目录结构

```bash
mkdir -p ~/listmonk/{data,conf}
cd ~/listmonk
```

### Step 2：编写 docker-compose.yml

```yaml
version: "3.8"

services:
  listmonk:
    image: listmonk/listmonk:latest
    container_name: listmonk
    restart: always
    ports:
      - "9000:9000"          # 管理后台
    volumes:
      - ./data:/listmonk/data
      - ./conf:/listmonk/conf
    environment:
      - LISTMONK_DATABASE_HOST=postgres
      - LISTMONK_DATABASE_PORT=5432
      - LISTMONK_DATABASE_USER=listmonk
      - LISTMONK_DATABASE_PASSWORD=change_me_strong_password
      - LISTMONK_DATABASE_NAME=listmonk
      - LISTMONK_DATABASE_SSL_MODE=disable
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    image: postgres:16-alpine
    container_name: listmonk-postgres
    restart: always
    environment:
      - POSTGRES_USER=listmonk
      - POSTGRES_PASSWORD=change_me_strong_password
      - POSTGRES_DB=listmonk
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U listmonk"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Step 3：初始化配置

```bash
# 生成默认配置文件
docker run --rm \
  -v $(pwd)/conf:/listmonk/conf \
  listmonk/listmonk:latest \
  ./listmonk --init --config /listmonk/conf/config.toml

# 查看配置文件
cat conf/config.toml
```

生成的 `config.toml` 关键配置项：

```toml
[app]
# 管理员账号
admin_username = "listmonk"
admin_password = "listmonk"        # ⚠️ 首次登录后务必修改
# 服务地址
host = "0.0.0.0"
port = 9000
upload_dir = "/listmonk/data/uploads"
encryption_key = ""                # 留空则自动生成，启动后自动持久化

[database]
host = "postgres"
port = 5432
user = "listmonk"
password = "change_me_strong_password"
database = "listmonk"
ssl_mode = "disable"
max_conns = 5
max_idle_conns = 2

[smtp]
# SMTP 中继地址
host = "localhost"
port = 587
user = ""
password = ""
skip_tls_verify = false
# 发送速率限制（每小时）
throttle_per_hour = 0             # 0 = 无限制
# TLS 模式
tls = "opportunistic"             # opportunistic | mandatory | none
```

### Step 4：启动服务

```bash
docker compose up -d

# 查看日志确认启动成功
docker compose logs -f listmonk
```

### Step 5：访问管理后台

打开浏览器访问 **http://your-server-ip:9000**，使用默认账号登录后：

1. 进入 **Settings → Profile**，修改管理员密码
2. 进入 **Settings → SMTP**，配置邮件发送服务商
3. 进入 **Lists**，创建第一个订阅者列表

---

## SMTP 配置详解

SMTP 是 listmonk 的"生命线"——所有发出的邮件都经过它中转。以下是几种主流配置方案。

### 方案一：使用 SendGrid（推荐，免费额度充足）

```toml
[smtp]
host = "smtp.sendgrid.net"
port = 587
user = "apikey"                    # SendGrid 要求 user 为 "apikey"
password = "SG.xxxxxxxxxxxxxxxx"   # 你的 SendGrid API Key
tls = "opportunistic"
```

> **SendGrid 免费额度：** 每月 100 封事务邮件 + 2,500 封营销邮件，对于中小型 Newsletter 完全够用。

### 方案二：使用 AWS SES（性价比最高）

```toml
[smtp]
host = "email-smtp.us-east-1.amazonaws.com"  # 替换为你的区域端点
port = 587
user = "AKIAXXXXXXXXXXXXXXXX"     # AWS SES SMTP 用户名
password = "xxxxxxxxxxxxxxxxxxxx" # SMTP 密码（在 AWS SES 控制台生成）
tls = "opportunistic"
```

> **AWS SES 优势：** 发送成本极低（$0.10/1000 封），需要提前在 SES 控制台申请生产访问权限。

### 方案三：自建 Postfix SMTP 服务器

```toml
[smtp]
host = "mail.yourdomain.com"
port = 587
user = "your-smtp-username"
password = "your-smtp-password"
tls = "opportunistic"
```

**Postfix 配置要点（确保通过反垃圾检查）：**

```bash
# /etc/postfix/main.cf 关键配置
myhostname = mail.yourdomain.com
mydomain = yourdomain.com
smtp_tls_security_level = may
smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt
```

### SMTP 配置自检清单

| 检查项 | 说明 |
|--------|------|
| ✅ SPF 记录 | 添加 SMTP 服务器 IP 到你的 DNS TXT 记录 |
| ✅ DKIM 签名 | 在 SMTP 服务商处配置 DKIM 公钥并添加到 DNS |
| ✅ DMARC 策略 | 添加 `_dmarc.yourdomain.com` TXT 记录 |
| ✅ 专用发件域 | 使用 `newsletter@yourdomain.com` 而非 Gmail/QQ 等公共邮箱 |
| ✅ 预热（Warm-up） | 新 SMTP 账号初期降低发送量，逐步增加以建立发件信誉 |

---

## 订阅者管理与列表运营

### 创建列表

进入 **Lists → New List**，配置：

- **Name**：列表名称（如 "AI 周刊订阅者"）
- **Description**：列表描述
- **Double Opt-in**：是否需要订阅确认邮件
- **GDPR compliant**：是否符合 GDPR 要求（显示隐私政策链接）

### 订阅者数据字段

listmonk 支持为订阅者添加**自定义字段（Custom Attributes）**：

| 内置字段 | 类型 | 说明 |
|---------|------|------|
| email | string | 邮箱（必填） |
| name | string | 姓名 |
| status | enum | subscribed / unsubscribed / blocked / bounced |
| created_at | timestamp | 订阅时间 |
| optout_token | string | 退订凭证 |

### 批量导入订阅者（CSV）

```csv
email,name,company,subscribed_at
alice@example.com,Alice Wang,ByteDance,2025-01-15
bob@example.com,Bob Chen,AI Labs,2025-02-20
```

在管理后台 **Lists → Import** 上传 CSV 文件并映射字段即可。

### API 注册订阅者

```bash
# 注册新订阅者到指定列表
curl -X POST http://localhost:9000/api/subscribers \
  -H "Content-Type: application/json" \
  -u "listmonk:listmonk" \
  -d '{
    "email": "new_user@example.com",
    "name": "New User",
    "list_ids": [1],
    "status": "enabled"
  }'
```

---

## 模板系统与邮件编辑

listmonk 使用 **HTML 模板引擎** 来渲染邮件内容，支持在模板中嵌入动态变量。

### 模板语法

```html
<!-- 基础变量 -->
{{ .Subscriber.Name }}          <!-- 订阅者姓名 -->
{{ .Subscriber.Email }}         <!-- 订阅者邮箱 -->
{{ .Campaign.Subject }}         <!-- 邮件主题 -->
{{ .CampaignURL }}              <!-- Web 阅读版本的链接 -->

<!-- 退订链接（必须包含，符合 CAN-SPAM / GDPR） -->
<a href="{{ .UnsubscribeURL }}">退订此邮件</a>

<!-- 阅读网页版链接 -->
<a href="{{ .ViewInBrowserURL }}">在浏览器中查看</a>

<!-- 条件渲染 -->
{{ if gt (len .Subscriber.Name) 0 }}
  您好，{{ .Subscriber.Name }}！
{{ else }}
  您好，读者！
{{ end }}
```

### 内置模板变量速查

| 变量 | 说明 |
|------|------|
| `{{ .Subscriber.UUID }}` | 订阅者唯一标识 |
| `{{ .Campaign.UUID }}` | Campaign 唯一标识 |
| `{{ .CampaignURL }}` | 当前 Campaign 的 Web 版本地址 |
| `{{ .UnsubscribeURL }}` | 退订链接 |
| `{{ .ViewInBrowserURL }}` | 浏览器阅读链接 |
| `{{ .SubscriberAttributes.field_name }}` | 自定义字段 |
| `{{ .Date.Format "2006-01-02" }}` | 日期格式化 |

### 完整 HTML 邮件模板示例

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ .Campaign.Subject }}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 0; background: #f5f5f5; }
    .container { max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 32px; text-align: center; }
    .header h1 { color: #ffffff; margin: 0; font-size: 24px; font-weight: 600; }
    .content { padding: 32px; color: #333333; line-height: 1.8; font-size: 15px; }
    .content h2 { color: #222222; font-size: 20px; margin-top: 0; }
    .content p { margin: 16px 0; }
    .btn { display: inline-block; padding: 12px 24px; background: #667eea; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: 600; }
    .footer { padding: 24px 32px; background: #f8f9fa; font-size: 12px; color: #888888; text-align: center; border-top: 1px solid #eeeeee; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{{ .Campaign.Subject }}</h1>
    </div>
    <div class="content">
      {{ if gt (len .Subscriber.Name) 0 }}
      <p>你好，<strong>{{ .Subscriber.Name }}</strong>！</p>
      {{ else }}
      <p>你好，读者！</p>
      {{ end }}

      <!-- 邮件正文占位符 -->
      {{ .HTMLBody }}

      <div style="margin-top: 32px; text-align: center;">
        <a href="{{ .CampaignURL }}" class="btn">在浏览器中阅读完整内容 →</a>
      </div>
    </div>
    <div class="footer">
      <p>你收到这封邮件是因为订阅了我们的Newsletter。<br>
      <a href="{{ .UnsubscribeURL }}" style="color: #888888;">点击此处退订</a></p>
      <p>&copy; {{ .Date.Format "2006" }} Your Company. All rights reserved.</p>
    </div>
  </div>
  <!-- 追踪像素（勿删） -->
  <img src="{{ .TrackOpenURL }}" width="1" height="1" alt="" style="display:none;" />
</body>
</html>
```

---

## Campaign（邮件活动）的完整生命周期

### Step 1：创建 Campaign

1. 进入 **Campaigns → New Campaign**
2. 选择目标**列表（List）**
3. 填写邮件主题（Subject）和邮件预览标题（From Name）
4. 选择发送**频率**：立即 / 定时 / 草稿

### Step 2：编辑邮件内容

在富文本编辑器中编写正文，或直接粘贴 HTML。可以使用模板变量做个性化处理。

### Step 3：配置发送选项

| 选项 | 说明 |
|------|------|
| **Send immediately** | 立即发送 |
| **Schedule for later** | 定时发送（指定 UTC 时间） |
| **Save as draft** | 保存为草稿 |
| **Throttling** | 设置每小时最大发送量（如 500/小时） |
| **Track opens** | 追踪打开率（嵌入追踪像素） |
| **Track clicks** | 追踪点击率（将链接转换为重定向追踪链接） |

### Step 4：发送与监控

Campaign 发送后，在 **Campaigns → 查看详情** 中可实时看到：

- 📤 **已发送**：成功投递数量
- ✅ **已送达**：无退回的邮件
- 📬 **已打开**：追踪像素被加载的数量
- 🖱️ **已点击**：链接被点击的数量
- ❌ **已退回**：硬退回/软退回详情
- 🚫 **已退订**：主动退订数量

---

## REST API 深度使用

listmonk 提供完整的 REST API，默认认证方式为 HTTP Basic Auth（使用管理员账号）。

### 基础调用格式

```bash
BASE_URL="http://localhost:9000/api"
AUTH="listmonk:listmonk"   # 修改为你的管理员密码
```

### 订阅者管理 API

```bash
# 获取所有订阅者（第1页，每页50条）
curl -s "${BASE_URL}/subscribers?page=1&per_page=50" -u "${AUTH}"

# 按列表筛选订阅者
curl -s "${BASE_URL}/subscribers?list_id=1&status=subscribed" -u "${AUTH}"

# 获取单个订阅者详情
curl -s "${BASE_URL}/subscribers/<uuid>" -u "${AUTH}"

# 注册新订阅者
curl -X POST "${BASE_URL}/subscribers" \
  -H "Content-Type: application/json" \
  -u "${AUTH}" \
  -d '{
    "email": "user@example.com",
    "name": "张三",
    "list_ids": [1],
    "status": "enabled",
    "attributes": {
      "company": "某科技公司",
      "plan": "pro"
    }
  }'

# 批量导入订阅者
curl -X POST "${BASE_URL}/subscribers/import" \
  -u "${AUTH}" \
  -F "format=csv" \
  -F "overwrite=true" \
  -F "file=@/path/to/subscribers.csv"

# 手动触发订阅者状态变更
curl -X PUT "${BASE_URL}/subscribers/<uuid>/status" \
  -H "Content-Type: application/json" \
  -u "${AUTH}" \
  -d '{"status": "unsubscribed"}'
```

### 列表（List）API

```bash
# 创建列表
curl -X POST "${BASE_URL}/lists" \
  -H "Content-Type: application/json" \
  -u "${AUTH}" \
  -d '{
    "name": "AI 爱好者",
    "description": "关注 AI 和机器学习动态的读者群",
    "optin": "double",          # double = 双重确认
    "GDPR": true
  }'

# 获取列表及统计信息
curl -s "${BASE_URL}/lists?with_stats=true" -u "${AUTH}"

# 更新列表
curl -X PUT "${BASE_URL}/lists/<list_id>" \
  -H "Content-Type: application/json" \
  -u "${AUTH}" \
  -d '{"name": "AI 与 ML 爱好者", "description": "更新后的描述"}'

# 删除列表（需先清空订阅者）
curl -X DELETE "${BASE_URL}/lists/<list_id>" -u "${AUTH}"
```

### Campaign API

```bash
# 获取所有 Campaign
curl -s "${BASE_URL}/campaigns?page=1&per_page=20" -u "${AUTH}"

# 创建 Campaign（草稿）
curl -X POST "${BASE_URL}/campaigns" \
  -H "Content-Type: application/json" \
  -u "${AUTH}" \
  -d '{
    "name": "第 12 期周报",
    "subject": "【AI 周报】第 12 期：大模型最新进展",
    "list_ids": [1],
    "content_type": "html",
    "body": "<h1>第 12 期 AI 周报</h1><p>本期内容：...</p>",
    "send_at": null,
    "status": "draft"
  }'

# 发布 Campaign（立即发送）
curl -X POST "${BASE_URL}/campaigns/<campaign_id>/send" \
  -u "${AUTH}"

# 定时发送 Campaign
curl -X POST "${BASE_URL}/campaigns/<campaign_id>/send" \
  -H "Content-Type: application/json" \
  -u "${AUTH}" \
  -d '{"schedule_at": "2026-06-01T09:00:00Z"}'

# 获取 Campaign 统计
curl -s "${BASE_URL}/campaigns/<campaign_id>/stats" -u "${AUTH}"
```

### 模板 API

```bash
# 获取所有模板
curl -s "${BASE_URL}/templates" -u "${AUTH}"

# 创建模板
curl -X POST "${BASE_URL}/templates" \
  -H "Content-Type: application/json" \
  -u "${AUTH}" \
  -d '{
    "name": "简洁周报模板",
    "body": "<!DOCTYPE html>...</html>",
    "data": {}
  }'
```

### 发送事务邮件（TX Mode）

listmonk 支持发送**非营销性质**的事务邮件（如密码重置、订单通知），不走常规 Campaign 流程。

```bash
# 发送单封事务邮件
curl -X POST "${BASE_URL}/tx" \
  -H "Content-Type: application/json" \
  -u "${AUTH}" \
  -d '{
    "to": ["user@example.com"],
    "subject": "您的密码重置链接",
    "body": "<p>请点击以下链接重置密码：<a href=\"https://example.com/reset?token=xxx\">重置链接</a></p>",
    "content_type": "html"
  }'
```

### API 认证与安全建议

**默认配置下使用 HTTP Basic Auth**，生产环境中建议通过反向代理添加 HTTPS + API Key 认证层：

```nginx
# Nginx 反向代理配置（添加 API Key 认证）
server {
    listen 443 ssl;
    server_name listmonk.yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;

    location /api/ {
        # 要求携带指定的 API Key 头
        if ($http_x_api_key != "your-secret-api-key") {
            return 403;
        }
        proxy_pass http://127.0.0.1:9000;
    }
}
```

---

## 高级运营策略

### 📈 提升邮件送达率（Delivery Rate）

1. **预热 SMTP 账号**：新账号前 2 周发送量控制在 50~200 封/天，逐周递增
2. **维护订阅者质量**：定期清理软退回（连续 3 次软退回自动移入黑名单）
3. **内容质量控制**：避免触发垃圾邮件关键词，HTML 邮件文本比例保持合理
4. **listmonk 配置节流**：

```toml
[smtp]
throttle_per_hour = 500   # 每小时最多发送 500 封
```

### 🧪 A/B 测试实现

listmonk 原生支持 A/B 测试。在创建 Campaign 时：

1. 设置**多个主题行变体**（如 3 个不同标题）
2. 系统自动按比例拆分受众，发送不同版本
3. 根据打开率/点击率自动选择最优版本发送给剩余订阅者

### 📅 自动化触发邮件

结合 API 和外部触发源（网站、CRM、自动化工具），可以实现：

- **欢迎邮件**：新订阅者注册后自动发送欢迎邮件
- **遗忘提醒**：订阅后 X 天未打开邮件，自动发送提醒
- **周期性 Newsletter**：配合 cron job 或 n8n 自动化工作流定时创建 Campaign

```bash
# 配合 n8n 自动化：每周末自动发送周报
# n8n workflow 伪代码：
# 1. 触发器：每个周日 10:00
# 2. 生成周报内容（调用 AI API）
# 3. 调用 listmonk API 创建 Campaign（草稿）
# 4. 调用 listmonk API 发送 Campaign
```

### 📊 与外部分析平台集成

通过 Webhook 将投递事件发送到 Matomo、PostHog 或自建分析平台：

```toml
[webhooks]
# 投递事件回调
urls = [
  "https://your-analytics.com/webhook?event={{ .Event }}&email={{ .Subscriber.Email }}"
]
```

---

## 运维与监控

### 数据备份

```bash
# 备份 PostgreSQL 数据
docker compose exec postgres pg_dump -U listmonk listmonk > backup_$(date +%Y%m%d).sql

# 定时备份脚本（crontab）
# 每天凌晨 3 点备份
0 3 * * * docker compose -f /path/to/listmonk/docker-compose.yml exec -T postgres pg_dump -U listmonk listmonk > /backups/listmonk_$(date +\%Y\%m\%d).sql
```

### 更新 listmonk

```bash
# 拉取最新镜像
docker compose pull

# 重启服务
docker compose up -d

# 查看更新日志
docker run --rm listmonk/listmonk:latest --version
```

### 性能调优

```toml
[database]
max_conns = 10          # 提高并发连接数
max_idle_conns = 5       # 保持 5 个空闲连接

[app]
# 并行发送 worker 数量
max_workers = 10
# 每个 worker 批次大小
batch_size = 100
```

### 日志查看

```bash
# 实时查看 listmonk 日志
docker compose logs -f listmonk

# 查看错误日志
docker compose logs -f --tail=100 listmonk | grep -i error

# PostgreSQL 连接状态
docker compose exec postgres psql -U listmonk -c "SELECT count(*), state FROM pg_stat_activity WHERE datname='listmonk' GROUP BY state;"
```

---

## 常见问题排查（FAQ）

### Q1：邮件发送后大量退回
- **原因：** SMTP 服务商信誉不足，或订阅者邮箱已失效
- **解决：** 使用专用发件域名、预热 SMTP、清理长期不活跃订阅者

### Q2：追踪像素不工作（打开率为 0）
- **原因：** 邮件客户端默认阻止图片加载，或 SMTP 服务商过滤了 1×1 追踪图
- **解决：** 检查 SMTP 服务商政策，部分 ESP（如 Gmail）不允许追踪像素

### Q3：管理员账号无法登录
```bash
# 重置管理员密码
docker compose exec listmonk ./listmonk --reset-admin-password --password "NewStrongPass123" --config /listmonk/conf/config.toml
```

### Q4：Docker 启动后 502 Bad Gateway
- **原因：** PostgreSQL 未就绪（`depends_on` 仅检查容器启动，不检查数据库就绪）
- **解决：** 确保 `docker-compose.yml` 中 PostgreSQL 配置了 `condition: service_healthy`

### Q5：Campaign 发送卡住不动
```bash
# 检查是否有未完成的 Campaign
docker compose exec listmonk ./listmonk --config /listmonk/conf/config.toml --migrate 2>&1 | head -50

# 重启队列
docker compose restart listmonk
```

---

## 总结与生态定位

listmonk 是一款**专注于 Newsletter 和邮件列表运营**的精品开源工具，它的优势在于：

| 优势 | 说明 |
|------|------|
| 🖥️ **单容器部署** | 无需复杂的微服务架构，一个 Docker Compose 就跑起来 |
| 💰 **零成本** | 只需一个 SMTP 服务，自托管无需按订阅者数付费 |
| 📊 **自带分析** | 打开率、点击率、退订率一目了然，无需接入外部分析工具 |
| 🔓 **数据自主** | 所有数据存在自己的 PostgreSQL，不依赖第三方平台 |
| 🚀 **API 优先** | 完整的 REST API，可与任何 CMS/CRM/自动化工具集成 |
| ⚡ **性能优秀** | Go 编写，单机可支撑数万订阅者的 Newsletter 发送 |

**适用场景：**
- ✅ 独立博主/创作者的定期 Newsletter
- ✅ 开源项目的版本更新通知
- ✅ 中小型 SaaS 的用户通知和营销邮件
- ✅ 社区/论坛的周期性邮件摘要
- ❌ 不适合：每天百万级发送量（应选择 Amazon SES + 自建投递系统）

**不适用场景：**
- ❌ 需要原生 iOS/Android 管理 App
- ❌ 需要内置 A/B 测试平台级功能（listmonk 的 A/B 测试仅支持主题行）
- ❌ 需要与 Shopify、WordPress 等平台原生深度集成（需 API 桥接）

---

> **写在最后：** listmonk 是那种"装完就觉得值了"的开源项目。它的管理后台体验远超同类自托管方案，数据完全自主可控。对于希望摆脱商业平台限制、掌控自己邮件数据的人来说，listmonk 是目前最好的选择之一。

---

*本文基于 listmonk v3.x 版本编写，参考 [GitHub 官方仓库](https://github.com/knadh/listmonk) 和 [官方文档](https://listmonk.org/docs/)。如有疏漏，欢迎指正。*
