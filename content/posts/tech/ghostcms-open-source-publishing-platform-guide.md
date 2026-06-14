---
title: "Ghost CMS：从入门到精通的专业开源 publishing 平台完全指南"
date: 2026-05-17
draft: false
author: "钳岳星君 🦞"
tags:
  - Ghost
  - CMS
  - Node.js
  - 开源
  - 博客平台
  - Headless CMS
categories:
  - 技术
slug: ghostcms-open-source-publishing-platform-guide
description: "深入解析 Ghost CMS 的架构设计、核心功能、安装配置、自定义开发、API 使用和部署方案，与主流替代方案全面对比。"
keywords:
  - Ghost CMS
  - Ghost 开源
  - Node.js CMS
  - Headless CMS
  - 专业博客
cover: ""
---

## 前言

Ghost 是一个专为专业内容创作者设计的开源 publishing 平台，由 Hugo 框架的作者 John O'Nolan 于 2013 年发起。与 WordPress 的全能型定位不同，Ghost 从一开始就走"小而美"路线——只做好一件事：让高质量内容的创作和发布体验做到极致。

本文全面解析 Ghost 的架构设计、核心功能、安装配置、自定义开发、API 使用和部署方案。

---

## 什么是 Ghost？

Ghost 是一个**开源的、专业级的 publishing 平台**，基于 Node.js 构建，核心特点：

- **Markdown 编辑器** — 沉浸式无干扰写作，支持富媒体嵌入
- **结构化内容管理** — 原生支持会员（Members）和订阅（Subscriptions）功能
- **原生 SEO** — 内置 SEO 优化，无需额外插件
- **轻量高性能** — 默认页面加载时间 < 1 秒
- **RESTful + Content API** — 完整的 API 接口，支持 Headless 模式
- **主题系统** — 基于 Handlebars 模板引擎的 Themes API
- **会员变现** — 内置免费/付费会员体系，支持 Stripe 集成

Ghost 官方提供托管服务（ghost.org），同时代码完全开源，可自行部署。

**官网：** https://ghost.org  
**GitHub：** https://github.com/TryGhost/Ghost  
**最新稳定版：** 5.x（截至 2026 年）  
**技术栈：** Node.js (≥18) + MySQL/PostgreSQL + Redis

---

## 核心技术架构

### 技术栈一览

| 层次 | 技术选型 |
|------|---------|
| 运行时 | Node.js ≥ 18 |
| 数据库 | MySQL 8.0+ 或 PostgreSQL 12+ |
| 缓存层 | Redis 6+ |
| 前端渲染 | Handlebars + Ember.js (admin) |
| 公共前端 | Ghost Handlebars 主题 |
| API | RESTful Content API + Admin API |
| 认证 | JWT (JSON Web Tokens) |
| 文件存储 | 本地文件 / S3 / Google Cloud Storage / Azure |
| 邮件 | Nodemailer (支持 SendGrid、Mailgun 等) |

### 架构设计哲学

Ghost 采用了典型的**三层架构**：

```
┌─────────────────────────────────────────┐
│            Presentation Layer            │
│  (Handlebars Themes / Admin UI / API)   │
├─────────────────────────────────────────┤
│            Business Logic               │
│  (Ghost Core: Posts, Members, Settings)│
├─────────────────────────────────────────┤
│              Data Layer                │
│     (MySQL/PostgreSQL + Redis Cache)    │
└─────────────────────────────────────────┘
```

**关键设计原则：**

1. **内容与表现分离** — Content API 使 Ghost 可作为纯 Headless CMS 使用
2. **缓存优先** — Redis 缓存层确保高频读取的高性能
3. **版本化内容** — 所有内容变更均有版本历史
4. **可扩展存储** — 存储层抽象，支持任意 S3 兼容存储后端

### 数据库设计概览

Ghost 使用 Bookshelf.js ORM，默认连接 MySQL，主要表结构：

- `posts` — 文章主表（title, slug, html, mobiledoc, status, published_at 等）
- `posts_meta` — 文章元数据（og_image, meta_description 等）
- `members` — 会员表
- `members_login_events` — 登录事件
- `posts_authors` — 多作者关联
- `tags` / `posts_tags` — 标签系统
- `settings` — 系统设置（KV 存储）

---

## 核心功能详解

### 1. Markdown 编辑器

Ghost 的编辑器基于 **Mobiledoc** 格式构建，支持：

- 实时预览（Split view / Full screen）
- 富媒体嵌入（图片、视频、音频、代码块、卡片）
- 可自定义的 Markdown 快捷键
- 协作编辑（通过团队邀请）

```handlebars
{{!-- 示例：Ghost 主题中的文章卡片 --}}
{{#foreach posts}}
<article class="post-card">
  <h2><a href="{{url}}">{{title}}</a></h2>
  <p>{{excerpt}}</p>
  <time>{{date format="YYYY-MM-DD"}}</time>
</article>
{{/foreach}}
```

### 2. 会员与订阅体系

Ghost 内置了完整的会员管理系统，无需第三方插件：

- **免费会员** — 可订阅 Newsletter
- **付费订阅** — Stripe 集成，支持按月/按年计费
- **会员 tiers（等级）** — 可创建多个订阅等级
- **Portal** — 嵌入式的注册/登录弹窗组件

### 3. 结构化内容（Collections）

Ghost 5.x 引入了 Collections 功能，允许创建不同类型的内容集合：

- `/blog/` — 博客文章
- `/newsletter/` — 邮件期刊
- `/podcast/` — 播客节目

每个 Collection 可独立配置 SEO、订阅设置和内容模板。

### 4. 内置 SEO

Ghost 自动处理：

- 自动生成 `sitemap.xml`
- 自动生成 `robots.txt`
- Open Graph 和 Twitter Card 元标签
- JSON-LD 结构化数据（Article schema）
- Canonical URL 管理

---

## 安装部署

### 环境要求

| 依赖 | 最低版本 | 推荐版本 |
|------|---------|---------|
| Node.js | 18.x | 20.x LTS |
| npm | 9.x | 10.x |
| MySQL | 8.0 | 8.0 |
| Redis | 6.x | 7.x |

### 方式一：本地快速安装（LiteSpeed）

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

### 方式二：生产环境完整安装（Ubuntu 20.04）

#### 1. 安装基础依赖

```bash
# 系统更新
sudo apt update && sudo apt upgrade -y

# 安装 Nginx
sudo apt install nginx -y

# 安装 MySQL
sudo apt install mysql-server -y
sudo mysql_secure_installation

# 安装 Redis
sudo apt install redis-server -y

# 安装 Node.js 20.x
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
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
- Nginx SSL 证书（Let's Encrypt）
- MySQL 连接信息
- Redis 连接信息
- systemd 服务守护
- SSL 强制重定向

#### 5. 常用 CLI 命令

```bash
ghost start          # 启动 Ghost
ghost stop           # 停止 Ghost
ghost restart        # 重启 Ghost
ghost status         # 查看运行状态
ghost update         # 更新 Ghost
ghost config run     # 查看当前配置
ghost logs           # 查看日志
```

### 方式三：Docker 部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  ghost:
    image: ghost:5
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
      cache__connection__host: cache
    volumes:
      - ./content:/var/lib/ghost/content
    depends_on:
      - db
      - cache

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

  cache:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - ./redis:/data

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

---

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
  "cache": {
    "redis": {
      "host": "127.0.0.1",
      "port": 6379,
      "password": ""
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
    "active": "s3",
    "s3": {
      "accessKeyId": "your_access_key",
      "secretAccessKey": "your_secret_key",
      "region": "ap-northeast-1",
      "bucket": "your-bucket-name"
    }
  },
  "members": {
    "stripe": {
      "apiKey": "sk_live_xxx",
      "productId": "prod_xxx",
      " plans": ["monthly", "yearly"]
    }
  },
  "privacy": {
    "useTinfoilHat": true,
    "forceContentPublic": false
  }
}
```

### 关键配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `url` | 博客公开 URL（结尾不带 `/`） | http://localhost:2368 |
| `server.port` | 监听端口 | 2368 |
| `database.client` | 数据库客户端 | mysql |
| `cache.redis` | Redis 缓存配置 | 内置内存缓存 |
| `mail.transport` | 邮件发送方式 | Direct |
| `storage.active` | 文件存储方式 | local |
| `members.stripe` | Stripe 支付配置 | - |
| `privacy.useTinfoilHat` | 是否开启隐私模式 | false |

### 环境变量覆盖

除 JSON 配置文件外，Ghost 也支持环境变量覆盖：

```bash
export url="https://yourblog.com"
export database__connection__host="prod-db-host"
export database__connection__password="super_secret"
export mail__from="noreply@yourblog.com"
```

---

## 主题开发

### 主题结构

```
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
    "ghost-api": "v5"
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

#### 核心 Helper

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

#### 自定义 Helper

Ghost 支持注册自定义 Handlebars Helper。创建一个 `/src/server/helpers/my-helper.js`：

```javascript
// src/server/helpers/my-helper.js
module.exports = function myHelper(htmlString, options) {
  // 自定义helper逻辑
  return htmlString.toUpperCase();
};

// 或使用 async helper（用于API调用）
module.exports = async function asyncHelper(options) {
  const result = await someAsyncOperation();
  return result;
};
```

在 `ghost/core/server/index.js` 或主题的 `helpers/` 目录中注册。

### AMP 支持

Ghost 内置 AMP（Accelerated Mobile Pages）支持。只需在主题中创建 `amp.hbs` 模板：

```handlebars
{{!< amp}}
<article class="post">
  <h1>{{post.title}}</h1>
  <p>{{post.excerpt}}</p>
  <time>{{post.published_at}}</time>
</article>
```

访问 `https://yourblog.com/article-slug/amp/` 即可获取 AMP 版本。

---

## Content API 与 Admin API

Ghost 提供两套 API：

| API | 端点 | 用途 | 认证 |
|-----|------|------|------|
| Content API | `/blog/api/content/` | 公开内容（博客、标签等） | 无 |
| Admin API | `/blog/ghost/api/admin/` | 管理功能（创建文章、管理会员等） | JWT / API Key |

### Content API

#### 获取文章列表

```bash
curl "https://yourblog.com/blog/api/content/posts/?key=your_public_api_key"
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
curl "https://yourblog.com/blog/api/content/posts/?key=xxx&filter=tag:tech"
```

#### 按作者过滤

```bash
curl "https://yourblog.com/blog/api/content/posts/?key=xxx&filter=author:john"
```

### Admin API

Admin API 用于后台管理操作，需要 JWT 认证。

#### 获取 Access Token

```bash
curl -X POST https://yourblog.com/blog/ghost/api/admin/authentication/password/" \
  -H "Content-Type: application/json" \
  -d '{"username": "your@email.com", "password": "your_password"}'
```

响应：

```json
{
  "errors": [],
  "data": {
    "accessToken": "xxx",
    "refreshToken": "xxx",
    "expires": 3600
  }
}
```

#### 创建文章

```bash
curl -X POST "https://yourblog.com/blog/ghost/api/admin/posts/" \
  -H "Authorization: Ghost xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "posts": [{
      "title": "My New Article",
      "html": "<p>Article content here...</p>",
      "status": "draft",
      "tags": ["tech"],
      "authors": ["author-id"]
    }]
  }'
```

#### 更新文章

```bash
curl -X PUT "https://yourblog.com/blog/ghost/api/admin/posts/article-id/" \
  -H "Authorization: Ghost xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "posts": [{
      "status": "published",
      "published_at": "2024-01-15T08:00:00.000Z"
    }]
  }'
```

#### 获取会员列表

```bash
curl "https://yourblog.com/blog/ghost/api/admin/members/?limit=100" \
  -H "Authorization: Ghost xxx"
```

### 自定义 Integration

在 Ghost Admin → Settings → Integrations 中创建自定义 Integration，获取 API Key：

```bash
curl "https://yourblog.com/blog/ghost/api/admin/posts/" \
  -H "Authorization: Ghost your-integration-api-key"
```

---

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
  version: 'v5'
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
  key: 'your_admin_api_key',
  version: 'v5'
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

```javascript
const crypto = require('crypto');

function verifyWebhookSignature(req) {
  const signature = req.headers['x-ghost-signature'];
  const secret = 'your_webhook_secret';
  
  if (!signature) return false;
  
  const [algo, hash] = signature.split('=');
  const expectedHash = crypto
    .createHmac(algo, secret)
    .update(JSON.stringify(req.body))
    .digest('hex');
  
  return crypto.timingSafeEqual(
    Buffer.from(hash),
    Buffer.from(expectedHash)
  );
}
```

---

## 与主流替代方案对比

| 特性 | Ghost | WordPress | Strapi | Netlify CMS |
|------|-------|-----------|--------|-------------|
| **定位** | Publishing 平台 | 全能型 CMS | Headless CMS | Git-based CMS |
| **数据库** | MySQL/PostgreSQL | MySQL | MongoDB/PostgreSQL | Git (Markdown) |
| **Node.js** | ✅ 原生 | ❌ (PHP) | ✅ 原生 | ✅ (静态构建) |
| **会员/变现** | ✅ 内置 | 需插件 | 需插件 | ❌ |
| **原生 SEO** | ✅ | 需插件(Yoast) | 需配置 | ✅ |
| **REST API** | ✅ | REST API 插件 | ✅ GraphQL+REST | ✅ |
| **Headless 模式** | ✅ | ❌ 需插件 | ✅ 原生 | ✅ |
| **学习曲线** | 低 | 中等 | 中等 | 低 |
| **开源许可** | MIT | GPL v2 | MIT | MIT |
| **官方托管** | ✅ | ❌ | ❌ | ❌ |
| **生态插件** | 中等 | 极丰富 | 丰富 | 较少 |
| **适合场景** | 专业博客/出版物 | 企业站/电商 | API-first 应用 | 技术文档 |

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

---

## 运维与安全

### 日常维护

```bash
# 更新 Ghost
ghost update

# 查看日志
ghost logs --server     # 查看服务器日志
ghost logs --error      # 仅查看错误

# 数据库备份
mysqldump -u ghostuser -p ghost_prod > backup_$(date +%Y%m%d).sql

# 清理缓存
redis-cli FLUSHALL

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
    "useTinfoilHat": true,
    "forceContentPublic": false
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
        location /blog/ghost/api/ {
            limit_req zone=ghost_api burst=20 nodelay;
        }
    }
}
```

#### 4. 定期更新

```bash
# 检查可用更新
npm check -g ghost-cli
ghost update --info

# 自动更新脚本（crontab）
# 0 3 * * 0 /usr/local/bin/ghost update >> /var/log/ghost-update.log 2>&1
```

---

## 常见问题

### Q1: Ghost 和 WordPress 哪个更好？

取决于需求。Ghost 专注于内容发布，WordPress 是全能选手。如果你的主要目标是**写好文章并变现**，Ghost 更适合。如果需要电商、多类型内容、多人协作，WordPress 更成熟。

### Q2: Ghost 支持多语言吗？

官方主题可通过 i18n 文件实现多语言。也有社区多语言插件如 `ghost-i18n`。

### Q3: 可以导入 WordPress 内容到 Ghost 吗？

可以。使用官方迁移工具 [Ghost WordPress Plugin](https://github.com/TryGhost/WordPressPlugin)，或通过 Ghost Admin 手动导入 XML 文件。

### Q4: Ghost 支持静态生成吗？

Ghost 本身是动态服务器，但可以配合 [Static Site Generator](https://github.com/TryGhost/Ghost/tree/main/contentThemes#static-site-generation) 工具将内容导出为静态文件。

### Q5: 如何自定义 Admin 管理面板？

Ghost Admin 使用 Ember.js 构建，定制需要修改 `@tryghost/ember-admin` 包（高级用法，不推荐在生产环境直接修改）。

---

## 总结

Ghost 是一个设计理念清晰、技术选型务实、专注于内容发布的开源 CMS。对比 WordPress 的臃肿，它更轻量；对比纯静态站点，它更动态；对比新兴 Headless CMS，它有完整的发布工作流和内置变现能力。

**核心优势总结：**
- 🚀 专为内容创作优化的高性能平台
- 💰 开箱即用的会员订阅变现体系
- 🔍 原生 SEO 支持，无需额外配置
- 📡 完整的 Content API + Admin API
- 🎨 简洁的 Handlebars 主题系统
- 🛡️ MIT 开源许可，可完全自托管

如果你正在寻找一个**专业、高效、变现友好**的内容发布平台，Ghost 值得优先考虑。

---

*本文基于 Ghost 5.x 版本编写，部分 API 或功能可能随版本迭代发生变化，建议参考 [官方文档](https://ghost.org/docs/) 获取最新信息。*