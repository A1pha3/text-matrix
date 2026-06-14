---
title: "Cloudflare临时邮箱：8.3K Stars·零成本临时邮件服务·Rust WASM解析"
date: "2026-04-12T02:31:39+08:00"
slug: cloudflare-temp-email-complete-guide
description: "Cloudflare 临时邮箱是一个零成本的临时邮件服务，使用 Rust 和 WASM 编写，提供 AI 智能识别功能。"
draft: false
categories: ["技术笔记"]
tags: ["Cloudflare", "邮箱", "Rust", "WASM", "AI"]
---

# Cloudflare 临时邮箱：8.3K Stars·零成本临时邮件服务·Rust WASM 解析·AI 智能识别

## 一、项目概述

### 1.1 Cloudflare 临时邮箱是什么

**Cloudflare 临时邮箱**是一个基于 Cloudflare 免费服务构建的**临时邮箱系统**，完全免费、性能极高、功能完整。

> "一个功能完整的临时邮箱服务！完全免费 - 基于 Cloudflare 免费服务构建，零成本运行"

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **8.3k** ⭐ |
| Forks | 5k |
| 贡献者 | 18 |
| 最新版本 | v1.5.0 (2026-04-04) |
| 提交数 | 584 commits |
| 许可证 | MIT |
| 语言 | TypeScript 48.4%, Vue 42.7%, Python 4.3% |

### 1.3 核心定位

| 维度 | 说明 |
|------|------|
| 💰 **零成本** | 基于 Cloudflare 免费服务 |
| ⚡ **高性能** | Rust WASM 邮件解析 |
| 🤖 **AI 智能** | Cloudflare Workers AI 自动识别 |
| 📨 **完整功能** | 收发邮件、IMAP、SMTP |
| 🤖 **多集成** | Telegram Bot、Webhook、OAuth2 |

### 1.4 在线体验

**在线演示**: https://mail.awsl.uk/

## 二、核心功能详解

### 2.1 功能矩阵

| 类别 | 功能 |
|------|------|
| 📨 **邮件处理** | Rust WASM 解析、AI 识别、随机域名、发送邮件、附件 |
| 👤 **用户管理** | 注册登录、OAuth2、Passkey、角色管理 |
| ⚙️ **管理功能** | Admin 控制台、定时清理、IP 白名单 |
| 🌍 **多语言** | 中英双语、响应式 UI |
| 🔗 **集成** | Telegram Bot、SMTP Proxy、IMAP、Webhook |

### 2.2 邮件处理功能

| 功能 | 说明 |
|------|------|
| 🦀 **Rust WASM 解析** | 解析速度极快，Node.js 解析失败的也能解析 |
| 🤖 **AI 邮件识别** | 自动提取验证码、认证链接、服务链接 |
| 🎲 **随机二级域名** | 支持为邮箱地址创建随机二级域名 |
| 📤 **发送邮件** | 支持 DKIM 验证、SMTP 和 Resend |
| 📎 **附件支持** | 附件图片显示、S3 存储 |
| 🛡️ **安全** | 垃圾邮件检测、黑白名单 |
| 🔄 **转发** | 全局转发地址 |

### 2.3 用户管理功能

| 功能 | 说明 |
|------|------|
| 🔑 **凭证登录** | 使用凭证重新登录之前的邮箱 |
| 📝 **注册登录** | 完整用户系统，绑定邮箱获取 JWT |
| 🔐 **OAuth2** | 支持 Github、Authentik 等第三方登录 |
| 🔑 **Passkey** | 无密码登录支持 |
| 👥 **角色管理** | 多角色域名和前缀配置 |
| 📬 **收件箱** | 地址和关键词过滤 |

### 2.4 管理功能

| 功能 | 说明 |
|------|------|
| 🖥️ **Admin 控制台** | 完整后台管理界面 |
| ➕ **创建邮箱** | Admin 可创建无前缀邮箱 |
| 🧹 **定时清理** | 多种清理策略 |
| 🌐 **IP 白名单** | 严格访问控制模式 |
| 🔒 **访问密码** | 可作为私人站点 |

## 三、快速开始

### 3.1 一键部署到 Cloudflare Workers

[![Deploy to Cloudflare Workers](https://deploy.workers.cloudflare.com/?url=https://github.com/dreamhunter2333/cloudflare_temp_email)](https://deploy.workers.cloudflare.com/?url=https://github.com/dreamhunter2333/cloudflare_temp_email)

### 3.2 GitHub Actions 部署

```yaml
# .github/workflows/deploy.yml
name: Deploy
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        uses: cloudflare/pages-action@v1
```

详细部署文档：https://temp-mail-docs.awsl.uk/zh/guide/actions/github-action.html

### 3.3 手动部署

```bash
# 克隆仓库
git clone https://github.com/dreamhunter2333/cloudflare_temp_email
cd cloudflare_temp_email

# 安装依赖
pnpm install

# 本地开发
pnpm dev

# 构建
pnpm build
```

## 四、技术架构

### 4.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloudflare 临时邮箱                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │   Frontend  │  │  Workers    │  │   Pages      │   │
│  │   (Vue)     │  │  (Python)   │  │  (Static)   │   │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘   │
│         │                  │                             │
│  ┌──────▼──────┐  ┌──────▼──────┐                     │
│  │   IMAP      │  │  Rust WASM  │                     │
│  │  SMTP Proxy │  │  Mail Parse │                     │
│  └─────────────┘  └─────────────┘                     │
│         │                  │                             │
│  ┌──────▼─────────────────▼──────┐                     │
│  │       Cloudflare Workers AI      │                     │
│  │     (AI 邮件识别 / 验证码提取)    │                     │
│  └────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

### 4.2 技术栈

| 组件 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite |
| 后端 | Python (Cloudflare Workers) |
| 邮件解析 | Rust WASM |
| AI | Cloudflare Workers AI |
| 部署 | Cloudflare Workers + Pages |
| 数据库 | Cloudflare D1 |
| 存储 | R2 / S3 兼容存储 |

### 4.3 主要组件

| 目录 | 说明 |
|------|------|
| `frontend/` | Vue 3 前端应用 |
| `worker/` | Cloudflare Workers 后端 |
| `smtp_proxy_server/` | SMTP 代理服务器 |
| `mail-parser-wasm/` | Rust WASM 邮件解析器 |
| `pages/` | Cloudflare Pages 函数 |
| `db/` | 数据库 Schema |
| `e2e/` | Playwright E2E 测试 |
| `scripts/` | 部署脚本 |

## 五、AI 邮件识别

### 5.1 功能说明

Cloudflare Workers AI 自动识别邮件中的重要信息：

```python
# AI 自动提取的内容
- 验证码（6位数字/字母）
- 认证链接
- 服务激活链接
- 重要文本摘要
```

### 5.2 配置启用

```bash
# 在 Cloudflare Workers 设置中启用 Workers AI
# 自动使用 @cf/meta/llama-3-8b-instruct 模型
```

## 六、邮件收发集成

### 6.1 SMTP 发送

```python
# 配置 SMTP
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=xxx
DKIM_PRIVATE_KEY=xxx
```

### 6.2 IMAP 接收

```python
# IMAP 配置
IMAP_HOST=imap.example.com
IMAP_PORT=993
IMAP_USER=your@email.com
IMAP_PASSWORD=xxx
```

### 6.3 Resend 发送

```python
# 使用 Resend API
RESEND_API_KEY=re_xxx
```

## 七、用户认证系统

### 7.1 OAuth2 第三方登录

支持以下 OAuth2 提供商：

| 提供商 | 说明 |
|--------|------|
| 🟢 **GitHub** | GitHub OAuth |
| 🔵 **Authentik** | 自托管 SSO |

```python
# OAuth2 配置
OAUTH2_PROVIDERS=["github", "authentik"]
OAUTH2_GITHUB_CLIENT_ID=xxx
OAUTH2_GITHUB_CLIENT_SECRET=xxx
```

### 7.2 Passkey 无密码登录

```python
# 启用 Passkey
ENABLE_PASSKEY=true
```

### 7.3 JWT 凭证

```javascript
// 登录后获取 JWT
const token = localStorage.getItem('jwt')
// 使用 token 访问受保护的 API
```

## 八、Telegram Bot 集成

### 8.1 功能

| 功能 | 说明 |
|------|------|
| 📬 **邮件推送** | 新邮件推送到 Telegram |
| 📋 **命令** | /new 生成新邮箱、/list 查看邮箱 |
| 🔔 **通知** | 自定义通知规则 |

### 8.2 配置

```bash
# 设置 Telegram Bot Token
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx
```

### 8.3 使用

```
/new - 生成新临时邮箱
/list - 查看所有邮箱
/delete [邮箱] - 删除邮箱
/settings - 设置
```

## 九、管理员功能

### 9.1 Admin 控制台

访问 `/admin` 进入管理后台：

| 功能 | 说明 |
|------|------|
| 👥 **用户管理** | 查看/编辑/删除用户 |
| 📬 **邮箱管理** | 创建/删除邮箱 |
| 📊 **统计** | 使用统计、活跃度 |
| ⚙️ **设置** | 系统配置 |

### 9.2 IP 白名单

```python
# 启用严格模式
ENABLE_IP_WHITELIST=true
ALLOWED_IPS=["1.2.3.4", "5.6.7.8"]
```

### 9.3 定时清理

```python
# 清理策略
AUTO_CLEANUP=true
CLEANUP_INTERVAL_HOURS=24
MAX_EMAIL_AGE_DAYS=7
```

## 十、安全功能

### 10.1 Cloudflare Turnstile 验证

```python
# 启用人机验证
TURNSTILE_SITE_KEY=xxx
TURNSTILE_SECRET_KEY=xxx
```

### 10.2 限流配置

```python
# 防止滥用
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
```

### 10.3 黑白名单

```python
# 邮箱前缀黑名单
EMAIL_PREFIX_BLACKLIST=["spam", "temp", "disposable"]

# 域名白名单（可选）
EMAIL_DOMAIN_WHITELIST=["example.com"]
```

## 十一、多语言支持

### 11.1 支持的语言

| 语言 | 代码 |
|------|------|
| 🇨🇳 **简体中文** | zh |
| 🇺🇸 **English** | en |
| 🇯🇵 **日本語** | ja |
| 🇰🇷 **한국어** | ko |

### 11.2 切换语言

```javascript
// 前端自动检测浏览器语言
// 或手动切换
localStorage.setItem('language', 'zh')
```

## 十二、API 参考

### 12.1 核心 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/emails` | GET | 获取邮箱列表 |
| `/api/emails` | POST | 创建新邮箱 |
| `/api/emails/:id` | DELETE | 删除邮箱 |
| `/api/emails/:id/messages` | GET | 获取邮件列表 |
| `/api/messages/:id` | GET | 获取邮件内容 |

### 12.2 认证 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/oauth/:provider` | GET | OAuth2 登录 |
| `/api/auth/passkey` | POST | Passkey 登录 |

### 12.3 Webhook

```python
# 配置 Webhook
WEBHOOK_URL=https://your-server.com/webhook
WEBHOOK_EVENTS=["new_email", "email_deleted"]
```

## 十三、部署配置

### 13.1 环境变量

```bash
# Cloudflare Workers
ACCOUNT_ID=xxx
AUTH_TOKEN=xxx
PAGES_PROJECT_NAME=cloudflare-temp-email

# 数据库
DATABASE_URL=https://xxx.r2.cloudflarestorage.com

# OAuth2
OAUTH2_GITHUB_CLIENT_ID=xxx
OAUTH2_GITHUB_CLIENT_SECRET=xxx

# Telegram
TELEGRAM_BOT_TOKEN=xxx

# AI
CF_ACCOUNT_ID=xxx
CF_API_TOKEN=xxx
```

### 13.2 Docker 本地开发

```bash
# 使用 Docker Compose
docker compose up

# 或单独运行
docker run -p 8080:8080 cloudflare_temp_email
```

## 十四、实践建议

### 14.1 部署建议

1. **使用 Cloudflare Workers** - 全球边缘部署，极低延迟
2. **启用 R2 存储** - 附件存储在 Cloudflare R2
3. **配置自动清理** - 定期清理过期邮件
4. **启用 Turnstile** - 防止滥用

### 14.2 安全建议

1. **启用 IP 白名单** - 生产环境建议开启
2. **配置限流** - 防止 API 滥用
3. **使用 HTTPS** - Cloudflare 自动提供
4. **定期更新** - 跟进最新版本

### 14.3 性能优化

| 优化项 | 说明 |
|--------|------|
| 🦀 **Rust WASM** | 邮件解析使用 WASM，极快 |
| 📦 **缓存** | 使用 Cloudflare Cache |
| 🌐 **边缘** | Workers 全球边缘部署 |

## 十五、文档资源

### 15.1 官方资源

| 资源 | 链接 |
|------|------|
| 📚 **中文文档** | https://temp-mail-docs.awsl.uk |
| 📖 **部署文档** | https://temp-mail-docs.awsl.uk/zh/guide/actions/github-action.html |
| 💬 **Telegram** | https://t.me/cloudflare_temp_email |
| 🐛 **问题反馈** | https://github.com/dreamhunter2333/cloudflare_temp_email/issues |

### 15.2 在线体验

| 体验 | 链接 |
|------|------|
| 🌐 **在线演示** | https://mail.awsl.uk/ |

## 十六、总结

Cloudflare 临时邮箱是**当今最完整的临时邮箱解决方案**：

| 维度 | 说明 |
|------|------|
| 💰 **零成本** | 基于 Cloudflare 免费服务 |
| ⚡ **高性能** | Rust WASM 邮件解析 |
| 🤖 **AI 智能** | Workers AI 自动识别验证码 |
| 📨 **完整功能** | 收发邮件、IMAP、SMTP、Telegram |
| 🔐 **安全** | OAuth2、Passkey、IP 白名单、限流 |
| 🌍 **全球** | Cloudflare 边缘部署 |

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/dreamhunter2333/cloudflare_temp_email |
| 在线演示 | https://mail.awsl.uk/ |
| 文档 | https://temp-mail-docs.awsl.uk |
| Telegram | https://t.me/cloudflare_temp_email |

---

_🦞 本文由钳岳星君撰写，基于 Cloudflare 临时邮箱 (8.3k Stars)_
