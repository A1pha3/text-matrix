---
title: "Ghost CMS：专业开源发布平台完全指南"
date: 2026-05-17
draft: false
author: "钳岳星君 🦞"
tags: ["Node.js", "开源"]
categories : ["技术笔记"]
slug: ghostcms-open-source-publishing-platform-guide
github_repo: "TryGhost/Ghost"
source_key: "gh:TryGhost/Ghost"
description: "深入解析 Ghost CMS 的架构设计、主要功能、安装配置、自定义开发、API 使用和部署方案，与主流替代方案全面对比。"
keywords:
  - Ghost CMS
  - Ghost 开源
  - Node.js CMS
  - Headless CMS
  - 专业博客
cover: ""
---

## 前言

Ghost 是一个专为专业创作者设计的开源发布平台，由 John O'Nolan 与 Hannah Wolfe 于 2013 年联合创办，最初通过一场成功的 Kickstarter 众筹启动。John 曾是 WordPress 的早期核心贡献者，他做 Ghost 的出发点正是对 WordPress 日益臃肿的不满。与 WordPress 的全能型定位不同，Ghost 从一开始就走"小而美"路线——只做好一件事：把高质量内容的创作、订阅与发布体验做到极致。

下面从架构、功能、安装、主题、API 到部署逐层拆解。

## 什么是 Ghost？

Ghost 是一个**开源的、专业级的发布平台**，基于 Node.js 构建，主要特点：

- **卡片式编辑器** — 沉浸式无干扰写作，支持富媒体卡片
- **结构化内容管理** — 原生支持会员（Members）和订阅（Subscriptions）功能
- **原生 SEO** — 内置 SEO 优化，无需额外插件
- **轻量高性能** — 面向发布场景优化的快速加载
- **RESTful + Content API** — 完整的 API 接口，支持 Headless 模式
- **主题系统** — 基于 Handlebars 模板引擎的 Themes API
- **会员变现** — 内置免费/付费会员体系，支持 Stripe 集成

Ghost 官方提供托管服务（ghost.org），同时代码完全开源，可自行部署。

**官网：** https://ghost.org  
**GitHub：** https://github.com/TryGhost/Ghost  
**最新稳定版：** v6.65.0（2026 年 9 月发布）  
**技术栈：** Node.js v22 + MySQL（生产环境；开发环境可用 SQLite）

## 技术架构

### 技术栈一览

| 层次 | 技术选型 |
|------|---------|
| 运行时 | Node.js v22 |
| 数据库 | MySQL 8（生产）/ SQLite3（开发） |
| 缓存层 | 默认进程内 MemoryCache，可切换 Redis 适配器 |
| 前端渲染 | Handlebars 主题 |
| 管理后台 | Ghost Admin（Ember.js 应用，部分界面正逐步迁移到 React） |
| API | RESTful Content API + Admin API |
| 认证 | Admin API 采用签名 JWT / 会话认证 |
| 文件存储 | 本地文件为默认；内置 S3 兼容适配器（S3/MinIO/R2 等），支持自定义 adapter |
| 邮件 | Nodemailer（支持 SendGrid、Mailgun、Amazon SES 等） |

### 架构设计哲学

Ghost 采用了典型的**三层架构**：

```text
┌─────────────────────────────────────────┐
│            Presentation Layer            │
│  (Handlebars Themes / Admin UI / API)   │
├─────────────────────────────────────────┤
│            Business Logic               │
│  (Ghost Core: Posts, Members, Settings)│
├─────────────────────────────────────────┤
│              Data Layer                │
│       (MySQL / SQLite + Cache)         │
└─────────────────────────────────────────┘
```

这套架构的四条设计取向贯穿全文：

1. **内容与表现分离** — Content API 使 Ghost 可作为纯 Headless CMS 使用
2. **解耦架构** — Core API、Admin 客户端、前端主题三部分彼此独立，便于定制
3. **缓存友好** — Content API 响应可完整缓存，高频读取也能保持高性能
4. **可扩展存储** — 存储层抽象，内置 S3 兼容适配器之外也支持自定义 storage adapter

### 数据库设计概览

Ghost 使用 Bookshelf.js ORM，默认连接 MySQL，主要表结构：

- `posts` — 文章主表（title, slug, html, status, published_at 等）
- `posts_meta` — 文章元数据（og_image, meta_description 等）
- `members` — 会员表
- `members_login_events` — 登录事件
- `posts_authors` — 多作者关联
- `tags` / `posts_tags` — 标签系统
- `settings` — 系统设置（KV 存储）

把一次真实发布串起来看：作者在编辑器里点下发布，`posts.status` 写为 `published` 并落库；`post.published` 事件随即触发两件事——渲染管道把内容喂给 Handlebars 主题生成页面，同时向配置过的 Webhook 地址发出签名 POST；如果配置了 Newsletter，邮件任务也会入队。此后任何 Headless 前端用 Content API Key 请求 `/ghost/api/content/posts/`，就能拿到这篇带 `html`、`tags`、`authors` 的结构化 JSON。一条数据流贯穿了编辑器、数据库、主题渲染和 API 四层，这正是下一节逐个展开的内容。

## 主要功能详解

### 1. Ghost 编辑器

Ghost 的编辑器基于开源的 [Koenig](https://github.com/TryGhost/Koenig) 编辑器构建，采用**卡片式（Card）结构**，正文由一组可拖拽排序的卡片组成。支持：

- 富媒体卡片（图片、图集、代码、视频、音频、嵌入、折叠块等）
- 行内 Markdown 快捷输入与格式化快捷键
- 团队成员协作：通过邀请成员并分配角色（作者 / 编辑 / 管理员）管理内容

### 2. 会员与订阅体系

Ghost 内置了完整的会员管理系统，无需第三方插件：

- **免费会员** — 可订阅 Newsletter
- **付费订阅** — Stripe 集成，支持按月/按年计费
- **会员 tiers（等级）** — 可创建多个订阅等级
- **Portal** — 嵌入式的注册/登录弹窗组件

### 3. 结构化内容（Collections）

Collections 是通过 `content/settings/routes.yaml` 定义的站点内容分区（可在后台 Settings → Labs 上传生效），决定一篇文章的 URL 结构和所用模板：

```yaml
routes:

collections:
  /blog/:
    permalink: /blog/{slug}/
    template: index
  /podcast/:
    permalink: /podcast/{slug}/
    template: podcast
```

三条规则值得记住：每篇文章只能属于一个 collection（按 `filter` 归类，常用 `primary_tag`）；各 collection 的 `filter` 必须彼此唯一，否则会出现渲染和分页问题；URL 前缀、永久链接格式（`{slug}`、`{year}` 等）和模板都可以按集合单独指定。

### 4. 内置 SEO

Ghost 自动处理：

- 自动生成 `sitemap.xml`
- 自动生成 `robots.txt`
- Open Graph 和 Twitter Card 元标签
- JSON-LD 结构化数据（Article schema）
- Canonical URL 管理

## 安装部署

### 环境要求

| 依赖 | 版本要求 | 说明 |
|------|---------|---------|
| Node.js | 22.x | Ghost 6 移除了 Node 18/20 支持（本地开发装 SQLite3 还需要 Python 3） |
| 数据库 | MySQL 8.0 | 生产环境唯一官方支持的数据库；开发可用 SQLite |
| Ghost CLI | 最新版 | `npm install -g ghost-cli` 安装 |

> 注意：Ghost 6 官方支持口径是 Node.js 22 LTS（当前版本的 engines 字段亦声明兼容 Node 24）；生产环境仅支持 MySQL 8，PostgreSQL 已不再官方支持。另外 Ghost 6 移除了 API 的 `?limit=all`，单页最多返回 100 条数据，超出部分必须翻页获取。

### 方式一：本地快速安装（开发环境）

使用 Ghost 官方 CLI，一行命令安装：

```bash
# 安装 Ghost CLI
npm install -g ghost-cli

# 创建项目目录并进入
mkdir my-ghost-blog && cd my-ghost-blog

# 本地安装（使用 SQLite，适用于开发测试）
ghost install local

# 启动
ghost start
```

访问 http://localhost:2368 即可看到博客，Admin 面板在 http://localhost:2368/ghost

### 方式二：生产环境完整安装（Ubuntu 22.04）

#### 1. 安装基础依赖

```bash
# 系统更新
sudo apt update && sudo apt upgrade -y

# 安装 Nginx
sudo apt install nginx -y

# 安装 MySQL
sudo apt install mysql-server -y
sudo mysql_secure_installation

# （可选）安装 Redis：仅在启用 Redis 缓存时使用
sudo apt install redis-server -y

# 安装 Node.js 22.x
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install nodejs -y

# 安装 Ghost CLI
sudo npm install -g ghost-cli
```

#### 2. 配置 MySQL 数据库

```bash
sudo mysql
```

```sql
CREATE DATABASE ghost_prod;
CREATE USER 'ghostuser'@'localhost' IDENTIFIED BY 'your_strong_password';
GRANT ALL PRIVILEGES ON ghost_prod.* TO 'ghostuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 3. 创建专用用户

```bash
sudo adduser --system --group ghost
sudo chown -R ghost:ghost /var/www/ghost
```

#### 4. 安装 Ghost

```bash
sudo -u ghost -H bash
cd /var/www/ghost
ghost install
```

安装向导会自动检测并配置：
- Nginx 与 SSL（可自动申请 Let's Encrypt 证书）
- MySQL 连接信息
- systemd 服务守护
- SSL 与 HTTP→HTTPS 重定向

#### 5. 常用 CLI 命令

```bash
ghost start          # 启动 Ghost
ghost stop           # 停止 Ghost
ghost restart        # 重启 Ghost
ghost ls             # 列出实例及运行状态
ghost update         # 更新 Ghost（出问题可 ghost update --rollback）
ghost config         # 显示当前配置
ghost log            # 查看日志
ghost check-update   # 检查是否有可用更新
```

### 方式三：Docker 部署

```yaml
# docker-compose.yml
services:
  ghost:
    image: ghost:6
    container_name: ghost-blog
    restart: unless-stopped
    ports:
      - "2368:2368"
    environment:
      url: https://yourblog.com
      database__client: mysql
      database__connection__host: db
      database__connection__user: ghost
      database__connection__password: ghost_password
      database__connection__database: ghost
    volumes:
      - ./content:/var/lib/ghost/content
    depends_on:
      - db

  db:
    image: mysql:8
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: ghost
      MYSQL_USER: ghost
      MYSQL_PASSWORD: ghost_password
    volumes:
      - ./mysql:/var/lib/mysql

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - ghost
```

```bash
docker-compose up -d
```

### 方式四：使用 Cloudflare Tunnel（无公网 IP 本地部署）

```bash
# 安装 cloudflared
brew install cloudflare/cloudflare/cloudflared  # macOS
# 或
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared && sudo mv cloudflared /usr/local/bin/

# 创建隧道
cloudflared tunnel create ghost-tunnel

# 配置 DNS（自动完成）
cloudflared tunnel route dns ghost-tunnel yourblog.com

# 运行隧道
cloudflared tunnel run --token <your-tunnel-token>
```

配合 Nginx 反向代理，Nginx 配置参考：

```nginx
server {
    listen 80;
    server_name yourblog.com;

    location / {
        proxy_pass http://127.0.0.1:2368;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 配置深度解析

### config.production.json

Ghost 的配置文件（`config.*.json`）控制所有运行参数：

```json
{
  "url": "https://yourblog.com",
  "server": {
    "port": 2368,
    "host": "127.0.0.1"
  },
  "database": {
    "client": "mysql",
    "connection": {
      "host": "localhost",
      "port": 3306,
      "user": "ghostuser",
      "password": "your_password",
      "database": "ghost_prod"
    }
  },
  "mail": {
    "transport": "SMTP",
    "options": {
      "service": "SendGrid",
      "auth": {
        "user": "apikey",
        "pass": "your_sendgrid_api_key"
      }
    }
  },
  "storage": {
    "active": "S3Storage",
    "S3Storage": {
      "bucket": "your-bucket-name",
      "region": "ap-northeast-1",
      "accessKeyId": "your_access_key",
      "secretAccessKey": "your_secret_key",
      "cdnUrl": "https://cdn.yourblog.com",
      "staticFileURLPrefix": "content/images",
      "multipartUploadThresholdBytes": 52428800,
      "multipartChunkSizeBytes": 10485760
    }
  },
  "members": {
    "stripe": {
      "secretKey": "sk_live_xxx",
      "webhookSecret": "whsec_xxx"
    }
  },
  "privacy": {
    "useTinfoil": true
  }
}
```

### 关键配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `url` | 博客公开 URL（结尾不带 `/`） | http://localhost:2368 |
| `server.port` | 监听端口 | 2368 |
| `database.client` | 数据库客户端 | mysql |
| `adapters.cache` | 缓存适配器（默认 MemoryCache，可切 Redis 并按 feature 设置 TTL） | MemoryCache |
| `mail.transport` | 邮件发送方式 | Direct |
| `storage.active` | 文件存储适配器（内置 `local` 与 `S3Storage`） | local |
| `members.stripe` | Stripe 密钥与 Webhook 配置 | - |
| `privacy.useTinfoil` | 开启隐私模式，关闭 Gravatar 等外部请求 | false |

### 环境变量覆盖

除 JSON 配置文件外，Ghost 也支持环境变量覆盖：

```bash
export url="https://yourblog.com"
export database__connection__host="prod-db-host"
export database__connection__password="super_secret"
export mail__from="noreply@yourblog.com"
```

## 主题开发

### 主题结构

```text
my-theme/
├── package.json            # 主题元数据
├── README.md
├── LICENSE
├── assets/
│   ├── css/
│   │   └── screen.css     # 主样式文件
│   ├── js/
│   │   └── script.js       # 主脚本文件
│   └── images/
│       └── logo.png
├── partials/               # 模板片段
│   ├── header.hbs
│   ├── footer.hbs
│   ├── post-card.hbs
│   └── members/           # 会员相关片段
│       ├── signin.hbs
│       └── signup.hbs
├── default.hbs             # 默认布局（主模板）
├── index.hbs               # 首页模板
├── post.hbs                # 单篇文章模板
├── page.hbs                # 页面模板
├── tag.hbs                 # 标签归档模板
├── author.hbs              # 作者归档模板
└── 404.hbs                 # 404 页面
```

### package.json 示例

```json
{
  "name": "my-custom-theme",
  "version": "1.0.0",
  "description": "A custom Ghost theme",
  "demo": "https://demo.ghost.io",
  "screenshots": {
    "desktop": "assets/screenshot-desktop.png"
  },
  "author": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "engines": {
    "ghost": ">=5.0.0",
    "node": ">=22.12.0"
  },
  "keywords": [
    "ghost",
    "theme"
  ]
}
```

### Handlebars 模板基础

#### 全局对象（Global Context）

| 对象 | 说明 |
|------|------|
| `{{title}}` | 当前页面标题 |
| `{{content}}` | 当前页面正文 |
| `{{url}}` | 当前页面 URL |
| `{{@site}}` | 站点全局配置 |
| `{{@member}}` | 当前登录会员信息 |
| `{{#if @member}}` | 判断会员是否登录 |

#### 主要 Helper

```handlebars
{{!-- 循环输出文章列表 --}}
{{#foreach posts}}
  <article>
    <h2><a href="{{url}}">{{title}}</a></h2>
    <p>{{excerpt words="30"}}</p>
    <img src="{{feature_image}}" alt="{{title}}">
    <time datetime="{{published_at}}">{{date format="YYYY年MM月DD日"}}</time>
    {{#if @member.paid}}
      <span class="badge">付费会员专属</span>
    {{/if}}
  </article>
{{/foreach}}

{{!-- 条件判断 --}}
{{#if @site.members_enabled}}
  <a href="#/portal/signup">订阅更新</a>
{{/if}}

{{!-- 分页 --}}
{{pagination}}
```

#### 复用模板片段（Partials）

Ghost 主题使用的是内置 Helper 集合，主题本身不能注册自定义 Handlebars Helper。需要复用一段模板时，把它放进 `partials/` 目录，再用 `{{> "partial-name"}}` 引入：

```handlebars
{{!-- partials/post-card.hbs --}}
<article class="post-card">
  <h2><a href="{{url}}">{{title}}</a></h2>
  <p>{{excerpt}}</p>
</article>

{{!-- 在任意模板中复用 --}}
{{#foreach posts}}
  {{> "post-card"}}
{{/foreach}}
```

更复杂的输出逻辑可以用 `{{#get}}` 取数据，配合 `{{#match}}`、`{{#has}}` 等内置 Helper 组合实现，参照官方 Helper 文档即可覆盖绝大多数场景。

### 主题兼容性检查（GScan）

Ghost 提供 [GScan](https://docs.ghost.org/themes/gscan) 工具在线或本地校验主题与当前版本的兼容性，包括 Helper 用法、模板缺失、权限问题等。在上传主题前先跑一次 GScan，可以提前发现升级或定制时的问题。

```bash
# 安装 GScan
npm install gscan -g

# 校验主题目录
gscan /path/to/my-theme
```

> 说明：早期的 AMP（Accelerated Mobile Pages）功能在 Ghost 6.0 中已彻底移除，主题不再需要 `amp.hbs` 模板。

## Content API 与 Admin API

Ghost 提供两套 API：

| API | 端点 | 用途 | 认证 |
|-----|------|------|------|
| Content API | `/ghost/api/content/` | 公开交付已发布内容（只读） | Content API Key |
| Admin API | `/ghost/api/admin/` | 管理内容与数据（读写） | 签名 JWT / 会话 / 用户认证 |

### Content API

#### 获取文章列表

```bash
curl "https://yourblog.com/ghost/api/content/posts/?key=your_public_api_key"
```

响应示例：

```json
{
  "posts": [
    {
      "id": "65a1b2c3d4e5f6a7b8c9d0e1",
      "uuid": "65a1b2c3-d4e5-f6a7-b8c9-d0e1f2a3b4c5",
      "title": "Hello World",
      "slug": "hello-world",
      "html": "<p>这是文章内容...</p>",
      "custom_excerpt": "文章摘要",
      "feature_image": "https://yourblog.com/content/images/2024/hello.jpg",
      "featured": false,
      "status": "published",
      "published_at": "2024-01-15T08:00:00.000Z",
      "updated_at": "2024-01-15T10:30:00.000Z",
      "url": "https://yourblog.com/hello-world/",
      "tags": [
        { "name": "技术", "slug": "tech" }
      ],
      "authors": [
        { "name": "John Doe", "slug": "john" }
      ]
    }
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "limit": 10,
      "pages": 5,
      "total": 42,
      "next": 2,
      "prev": null
    }
  }
}
```

#### 查询参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `key` | Public API Key（必需） | `key=xxx` |
| `page` | 页码 | `page=2` |
| `limit` | 每页数量（max 100） | `limit=20` |
| `order` | 排序 | `order=published_at desc` |
| `filter` | 过滤条件 | `filter=tag:tech+author:john` |
| `fields` | 指定返回字段 | `fields=title,slug,url` |
| `include` | 关联数据 | `include=tags,authors` |

#### 按标签过滤

```bash
curl "https://yourblog.com/ghost/api/content/posts/?key=xxx&filter=tag:tech"
```

#### 按作者过滤

```bash
curl "https://yourblog.com/ghost/api/content/posts/?key=xxx&filter=author:john"
```

### Admin API

Admin API 用于管理内容与数据。对于第三方集成，官方推荐使用 **Admin API Key** 认证：先在 Admin → Settings → Integrations 中创建自定义 Integration，获得一对 `id:secret` 形式的 API Key，再据此生成短期签名的 JWT。

由于 API Key 属于机密，只能用于安全的服务端环境，不可在浏览器等不可信环境使用。

#### 生成签名 JWT

```bash
# 用 openssl 手搓一个 HS256 JWT
# 假设 API Key 为：5fdc1e0e5f2f1ab:8a9bcdef0123456789abcdef01234567
# （id 在前半，secret 为十六进制编码的 HMAC 密钥）
ID="5fdc1e0e5f2f1ab"
SECRET_HEX="8a9bcdef0123456789abcdef01234567"
NOW=$(date +%s)
EXP=$(($NOW + 300))   # 有效期最长 5 分钟

HEADER=$(printf '{"alg":"HS256","kid":"%s","typ":"JWT"}' "$ID" | openssl base64 -A | tr '+/' '-_' | tr -d '=')
PAYLOAD=$(printf '{"aud":"/admin/","exp":%s,"iat":%s}' "$EXP" "$NOW" | openssl base64 -A | tr '+/' '-_' | tr -d '=')
SIGNING_INPUT="$HEADER.$PAYLOAD"
SECRET=$(printf '%s' "$SECRET_HEX" | xxd -r -p | openssl base64 -A)
SIG=$(printf '%s' "$SIGNING_INPUT" | openssl dgst -sha256 -mac HMAC -macopt hexkey:"$SECRET_HEX" -binary | openssl base64 -A | tr '+/' '-_' | tr -d '=')

TOKEN="$SIGNING_INPUT.$SIG"
echo "$TOKEN"
```

#### 调用 Admin API

```bash
curl -X POST "https://yourblog.com/ghost/api/admin/posts/" \
  -H "Authorization: Ghost $TOKEN" \
  -H "Accept-Version: v6.0" \
  -H "Content-Type: application/json" \
  -d '{
    "posts": [{
      "title": "My New Article",
      "html": "<p>Article content here...</p>",
      "status": "draft"
    }]
  }'
```

#### 更新文章

```bash
curl -X PUT "https://yourblog.com/ghost/api/admin/posts/article-id/" \
  -H "Authorization: Ghost $TOKEN" \
  -H "Accept-Version: v6.0" \
  -H "Content-Type: application/json" \
  -d '{
    "posts": [{
      "status": "published",
      "published_at": "2024-01-15T08:00:00.000Z",
      "updated_at": "2024-01-15T09:00:00.000Z"
    }]
  }'
```

更新请求建议带上读取时返回的 `updated_at`，Ghost 用它检测并发修改冲突。

#### 获取会员列表

```bash
curl "https://yourblog.com/ghost/api/admin/members/?limit=100" \
  -H "Authorization: Ghost $TOKEN" \
  -H "Accept-Version: v6.0"
```

## 自定义开发

### 官方 SDK

Ghost 提供 JavaScript SDK（`@tryghost/content-api` 和 `@tryghost/admin-api`）：

```bash
npm install @tryghost/content-api @tryghost/admin-api
```

#### 使用 Content API SDK

```javascript
const GhostContentAPI = require('@tryghost/content-api');

// 初始化
const api = new GhostContentAPI({
  url: 'https://yourblog.com',
  key: 'your_public_api_key',
  version: 'v6.0'
});

// 获取文章
async function getPosts() {
  const posts = await api.posts.browse({
    limit: 10,
    fields: ['title', 'slug', 'excerpt', 'published_at']
  });
  console.log(posts);
  return posts;
}

// 获取单篇文章
async function getPost(slug) {
  const post = await api.posts.read({
    slug: slug
  }, {
    fields: ['title', 'html', 'og_image']
  });
  return post;
}

// 获取标签
async function getTags() {
  const tags = await api.tags.browse({ limit: 20 });
  return tags;
}

getPosts().catch(console.error);
```

#### 使用 Admin API SDK

```javascript
const GhostAdminAPI = require('@tryghost/admin-api');

const api = new GhostAdminAPI({
  url: 'https://yourblog.com',
  key: 'your_integration_api_key', // 完整格式：id:secret
  version: 'v6.0',                 // 客户端会自动用该 Key 生成签名 JWT
});

// 创建文章
async function createPost() {
  const post = await api.posts.add({
    title: 'My New Post via SDK',
    html: '<p>Content goes here...</p>',
    status: 'draft',
    tags: ['tech', 'nodejs']
  });
  console.log('Created post:', post.id);
  return post;
}

// 发布文章
async function publishPost(postId) {
  const post = await api.posts.edit({
    id: postId,
    status: 'published'
  });
  return post;
}

// 获取会员
async function getMembers() {
  const members = await api.members.browse({
    limit: 100,
    fields: ['id', 'email', 'name', 'subscriptions']
  });
  return members;
}

createPost().catch(console.error);
```

### Webhooks（Webhook 触发器）

Ghost 支持 Webhook，可在特定事件触发时向外部系统发送 HTTP POST 请求。

**配置路径：** Admin → Settings → Webhooks

#### 创建 Webhook

```bash
# Ghost Admin 中配置：
# Event: post.published
# Target URL: https://your-app.com/webhooks/ghost
# Secret: your_webhook_secret
```

#### 验证 Webhook 签名

配置了 Secret 的 Webhook，请求头 `X-Ghost-Signature` 的格式为 `sha256=<签名十六进制值>, t=<Unix 时间戳>`，签名内容是**原始请求体拼接时间戳**。验证时必须用未经框架解析的原始 body 计算 HMAC：

```javascript
const crypto = require('crypto');

function verifyWebhookSignature(rawBody, headers) {
  const signature = headers['x-ghost-signature'];
  const secret = 'your_webhook_secret';

  if (!signature) return false;

  // header 形如 "sha256=abc123..., t=1715982456"
  const [shaPart, tPart] = signature.split(', ');
  const receivedHash = shaPart.replace('sha256=', '');
  const timestamp = tPart.replace('t=', '');

  const expectedHash = crypto
    .createHmac('sha256', secret)
    .update(`${rawBody}${timestamp}`)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(receivedHash),
    Buffer.from(expectedHash)
  );
}
```

在 Express 中可通过 `express.json({ verify: (req, res, buf) => { req.rawBody = buf; } })` 保留原始请求体再传入验证函数。

## 与主流替代方案对比

| 特性 | Ghost | WordPress | Strapi | Decap CMS（原 Netlify CMS） |
|------|-------|-----------|--------|---------------------------|
| **定位** | 发布平台 | 全能型 CMS | Headless CMS | Git-based CMS |
| **数据库** | MySQL(生产)/SQLite | MySQL | PostgreSQL/MySQL/MariaDB/SQLite | Git (Markdown) |
| **运行时** | Node.js | PHP | Node.js | 浏览器端应用，无独立运行时 |
| **会员/变现** | ✅ 内置 | 需插件 | 需插件 | ❌ |
| **原生 SEO** | ✅ | 需插件（Yoast） | 需配置 | 取决于所用静态生成器 |
| **REST API** | ✅ | ✅ 内置 REST API | ✅ REST + GraphQL | 经 Git 平台 API 读写 |
| **Headless 模式** | ✅ | △ 可作 Headless 用 | ✅ 原生 | ✅ 本身即无前端 |
| **学习曲线** | 低 | 中等 | 中等 | 低 |
| **开源许可** | MIT | GPL v2 | MIT | MIT |
| **官方托管** | ✅ Ghost(Pro) | ✅ WordPress.com | ✅ Strapi Cloud | ❌ |
| **生态插件** | 中等 | 极丰富 | 丰富 | 较少 |
| **适合场景** | 专业博客/出版物 | 企业站/电商 | API-first 应用 | 已有静态站点的编辑界面 |

> 注：Strapi 自 v4 起不再支持 MongoDB；Decap CMS 是 Netlify CMS 于 2023 年 2 月更名后的社区版本。

### 选择建议

**选 Ghost 当：**
- 专注于高质量内容创作
- 需要内置会员/订阅变现功能
- 想避免 WordPress 的维护负担
- 需要专业的 SEO 开箱即用体验

**选 WordPress 当：**
- 需要电商功能（WooCommerce）
- 需要高度定制化（插件生态极丰富）
- 已有 WordPress 使用经验

**选 Strapi 当：**
- 需要纯 Headless CMS
- 团队有 React/Next.js 前端能力
- 需要 GraphQL API

**选 Hugo/静态站点当：**
- 内容变更不频繁
- 追求极致性能和安全
- 预算极为有限（仅需静态托管）

## 运维与安全

### 日常维护

```bash
# 更新 Ghost
ghost update

# 查看日志
ghost log               # 查看运行日志（位于 content/logs/）

# 数据库备份
mysqldump -u ghostuser -p ghost_prod > backup_$(date +%Y%m%d).sql

# 同时备份 content 目录（图片、主题等）
tar -czf content_$(date +%Y%m%d).tar.gz /var/www/ghost/content

# 检查配置
ghost config
```

### 安全加固

#### 1. 修改默认端口

```json
{
  "server": {
    "port": 4368
  }
}
```

#### 2. 启用隐私模式

```json
{
  "privacy": {
    "useTinfoil": true
  }
}
```

#### 3. 限制 API 请求频率

配合 Nginx 实现 rate limiting：

```nginx
# /etc/nginx/nginx.conf
http {
    limit_req_zone $binary_remote_addr zone=ghost_api:10m rate=10r/s;

    server {
        location /ghost/api/ {
            limit_req zone=ghost_api burst=20 nodelay;
        }
    }
}
```

#### 4. 定期更新

```bash
# 检查可用更新
ghost check-update

# 执行更新；若新版本异常，回滚到上一个版本
ghost update
ghost update --rollback

# 自动更新脚本（crontab）
# 0 3 * * 0 /usr/local/bin/ghost update >> /var/log/ghost-update.log 2>&1
```

## 常见问题

### Q1: Ghost 和 WordPress 哪个更好？

取决于需求。Ghost 专注于内容发布，WordPress 是全能选手。如果你的主要目标是**写好文章并变现**，Ghost 更适合。如果需要电商、多类型内容、多人协作，WordPress 更成熟。

### Q2: Ghost 支持多语言吗？

分两层看。主题界面文字可以通过 i18n 翻译文件（`locales/` 下的 JSON）配合 `{{t}}` Helper 输出多语言，官方文档有完整说明。但**文章内容本身**没有内置的多语言管理，一篇文章只有一个语言版本；需要内容级多语言的站点，通常用两个独立站点（如 `/en/` 子域）或借助第三方方案。

### Q3: 可以导入 WordPress 内容到 Ghost 吗？

可以。官方提供了 [WordPress 迁移指南](https://docs.ghost.org/migration/wordpress/)，一般流程是从 WordPress 导出 XML（WXR）文件，再通过 Ghost Admin（Settings → Labs）导入。文章、页面、标签和作者会随迁移工具转换。

### Q4: Ghost 支持静态生成吗？

Ghost 本身是动态 Node.js 服务器，不内置静态导出。但它的 Content API 让它可以充当 Headless CMS，用 Next.js、Gatsby、Eleventy、Hexo 等静态生成器或任意前端框架渲染，官方维护了[各技术栈的接入指南](https://docs.ghost.org/jamstack/)。

### Q5: 如何自定义 Admin 管理面板？

Ghost Admin 是独立的前端应用（Ember.js 构建，部分界面正迁移到 React），官方不提供 Admin 界面级的插件机制。想扩展后台能力，正确路径是通过 Admin API 做外部集成——Ghost Admin 自己也是这套 API 的客户端，API 能做的事与后台一致。

## 总结

Ghost 的定位可以用一句话说清：把"写、发、订阅、变现"装进一个维护负担很小的 Node.js 应用。它不追求 WordPress 那种什么都能做的生态，也不像纯 Headless CMS 那样把前端完全交给你——换来的是一条从写作到收费的完整闭环。

如果要给采用顺序：个人博客或独立出版物，Ghost 可以直接上，会员变现是它相对一切免费方案的最大筹码；需要电商、论坛或复杂企业站，留在 WordPress；做 API-first 的多端产品，选 Strapi，Ghost 只当内容源；已经在用 Hugo、Eleventy 等静态站点，接 Content API 即可，不必迁移。

*本文基于 Ghost 6.x 版本编写，部分 API 或功能可能随版本迭代发生变化，建议参考 [官方文档](https://ghost.org/docs/) 获取最新信息。*