---
title: "DocuSeal：开源电子文档签署平台，DocuSign 替代方案"
date: "2026-05-05T11:35:00+08:00"
slug: "docuseal-open-source-document-signing-platform-guide"
description: "DocuSeal 是开源的电子文档签署和处理平台，提供 PDF 表单构建、数字签名、自动化邮件、API 和 Webhook 集成等功能，支持 Docker 一键部署。本文详解其功能特性、部署方式、API 集成与 Pro 版高级功能。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "电子签名", "PDF", "文档处理", "DocuSign 替代", "Docker"]
---

# DocuSeal：开源电子文档签署平台，DocuSign 替代方案

> **目标读者**：需要电子签名功能的企业、开发者、自托管爱好者
> **核心问题**：如何在不依赖商业 SaaS 的前提下，实现专业级电子文档签署？
> **预计时间**：约 20 分钟
> **前置知识**：了解 Docker 基础、REST API、SMTP 配置

---

## §1 学习目标

完成本文档后，你将能够：

- [ ] 理解 DocuSeal 的核心定位与解决的问题
- [ ] 掌握 DocuSeal 的 12 种核心字段类型'
- [ ] 熟练使用 Docker、Railway、Heroku 等平台部署 DocuSeal
- [ ] 配置 SMTP、云存储和 REST API'
- [ ] 基于 DocuSeal API 和 Webhook 实现自动化文档签署流程'
- [ ] 判断何时需要升级到 Pro 版'

---

## §2 文章主线#

- [DocuSeal 是什么，解决了什么问题？](#§3-项目概览)
- [12 种核心功能如何覆盖完整签署流程？](#§4-核心功能详解)
- [如何选择最适合的部署方式？](#§5-部署方式)
- [API 和 Webhook 如何与企业系统集成？](#§6-api-与-webhook-集成)
- [开源版和 Pro 版的区别在哪里？](#§7-pro-版功能)
- [DocuSeal 与 DocuSign 应该如何选择？](#§8-与-docusign-对比)

---

## §3 项目概览#

### 3.1 什么是 DocuSeal？

[DocuSeal](https://github.com/docusealco/docuseal) 是一个**开源电子文档签署和处理平台**，可作为 DocuSign 的替代方案。用户可以通过直观的 Web 界面创建 PDF 表单、收集填写内容、数字签名，并在任何设备上完成签署流程。

**官方描述**：

> The #1 Open Source DocuSign Alternative. Create, send, and sign PDF documents online. Self-host or use our cloud.

### 3.2 核心数据#

| 指标 | 数值 |
|------|------|
| **Stars** | **535** |
| **Forks** | 89 |
| **Watchers** | 12 |
| **贡献者** | 15 人 |
| **最新版本** | v1.2.3 (2026-05-01) |
| **许可证** | AGPLv3 + Section 7(b) Additional Terms |
| **语言** | Ruby 94.2%, HTML 3.1%, JavaScript 2.7% |

### 3.3 核心功能#

- **PDF 表单构建器**（WYSIWYG）
- **12 种字段类型**（签名、日期、文件、复选框等）
- **多签署方支持**
- **自动化邮件通知**
- **本地存储或云存储**（S3、Google Storage、Azure）
- **API 和 Webhook 集成**
- **Docker 一键部署**

---

## §4 核心功能详解#

### 4.1 PDF 表单构建器#

DocuSeal 提供所见即所得的表单编辑器，无需编程即可创建专业级 PDF 表单：

**支持的字段类型：**

| 字段类型 | 说明 |
|---------|------|
| **Signature** | 电子签名（核心功能） |
| **Date** | 日期选择 |
| **File** | 文件上传 |
| **Checkbox** | 复选框 |
| **Text Input** | 文本输入 |
| **Text Area** | 多行文本 |
| **Dropdown** | 下拉选择 |
| **Radio** | 单选按钮 |
| **Image** | 图片嵌入 |
| **Drawing** | 手绘签名 |
| **Initial** | 首字母缩写 |
| **Stamp** | 印章 |

### 4.2 多签署方流程#

支持设置多个签署方，并定义签署顺序：

```bash
# 示例：创建需要甲乙双方签署的合同
1. 甲方先签署（自动邮件通知）
2. 甲方签署完成后，乙方收到签署邀请'
3. 乙方签署完成，双方均收到已签署文档副本'
```

### 4.3 存储选项#

| 存储方式 | 说明 |
|---------|------|
| **本地磁盘** | 默认 SQLite，适合小规模使用 |
| **AWS S3** | 企业级对象存储 |
| **Google Cloud Storage** | GCP 生态集成 |
| **Azure Blob Storage** | 微软云生态集成 |
| **PostgreSQL** | 关系型数据库（可选） |
| **MySQL** | 关系型数据库（可选） |

### 4.4 API 与 Webhook#

DocuSeal 提供完整的 REST API 和 Webhook，支持与企业系统深度集成：

**API 端点示例：**

```bash
POST /api/v1/templates          # 创建模板'
POST /api/v1/documents          # 创建待签署文档'
GET  /api/v1/documents/:id      # 获取文档状态'
POST /api/v1/documents/:id/send # 发送签署邀请'
GET  /api/v1/documents/:id/file # 下载已签署文档'
```

**Webhook 事件：**

- `document.completed` — 文档签署完成'
- `document.signed` — 有人完成签署'
- `template.created` — 模板创建成功'

---

## §5 部署方式#

### 5.1 Docker（推荐，最简方式）#

```bash
# 单行命令启动'
docker run --name docuseal -p 3000:3000 -v $(pwd)/data:/data docuseal/docuseal
```

默认使用 SQLite 数据库存储在 `/data` 目录。

### 5.2 Docker Compose（生产级部署，支持 HTTPS）#

```bash
# 下载 docker-compose 配置'
curl https://raw.githubusercontent.com/docusealco/docuseal/master/docker-compose.yml > docker-compose.yml

# 启动（自动通过 Caddy 申请 SSL 证书）'
sudo HOST=your-domain-name.com docker-compose up
```

### 5.3 一键部署平台#

| 平台 | 按钮 |
|------|------|
| **Heroku** | [点击部署](https://heroku.com/deploy?template=https://github.com/docusealco/docuseal) |
| **Railway** | [点击部署](https://railway.app/new/template?template=https://github.com/docusealco/docuseal/raw/master/railway.json) |
| **DigitalOcean** | [点击部署](https://cloud.digitalocean.com/apps/new) |
| **Render** | [点击部署](https://render.com/deploy?repo=https://github.com/docusealco/docuseal) |

### 5.4 环境变量配置#

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接串 | SQLite 本地文件 |
| `SMTP_ADDRESS` | SMTP 服务器地址 | - |
| `SMTP_PORT` | SMTP 端口 | 587 |
| `SMTP_USERNAME` | SMTP 用户名 | - |
| `SMTP_PASSWORD` | SMTP 密码 | - |
| `SMTP_FROM` | 发件人地址 | - |
| `AWS_BUCKET` | S3 桶名称 | - |
| `AWS_REGION` | AWS 区域 | - |
| `AWS_ACCESS_KEY_ID` | AWS 访问密钥 | - |
| `AWS_SECRET_ACCESS_KEY` | AWS 秘密密钥 | - |

---

## §6 API 与 Webhook 集成#

### 6.1 REST API 使用示例#

**创建模板：**

```bash
curl -X POST https://your-docuseal.com/api/v1/templates \
  -H "Content-Type: application/json" \
  -d '{
    "title": "服务合同模板",
    "fields": [
      {"name": "client_name", "type": "text", "required": true},
      {"name": "signature", "type": "signature", "required": true}
    ]
  }'
```

**创建待签署文档：**

```bash
curl -X POST https://your-docuseal.com/api/v1/documents \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "abc123",
    "send_email": true,
    "recipients": [
      {"name": "张三", "email": "zhangsan@example.com"}
    ]
  }'
```

### 6.2 Webhook 处理示例#

```python
# Python Flask 示例'
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook/docuseal', methods=['POST'])
def handle_webhook():
    event = request.json
    
    if event['type'] == 'document.completed':
        document_id = event['data']['id']
        # 下载已签署文档'
        # 更新业务系统状态'
        pass
    
    return 'OK', 200
```

---

## §7 Pro 版功能#

DocuSeal 分为**开源版**和 **Pro 版**，Pro 版提供更高级功能：

| 功能 | 开源版 | Pro 版 |
|------|--------|-------|
| **基础表单字段** | ✅ | ✅ |
| **多签署方** | ✅ | ✅ |
| **PDF 导出** | ✅ | ✅ |
| **Logo 定制** | ❌ | ✅ |
| **白标** | ❌ | ✅ |
| **用户角色管理** | ❌ | ✅ |
| **自动提醒** | ❌ | ✅ |
| **SMS 身份验证** | ❌ | ✅ |
| **条件字段和公式** | ❌ | ✅ |
| **CSV/XLSX 批量发送** | ❌ | ✅ |
| **SSO/SAML** | ❌ | ✅ |
| **HTML API 模板创建** | 基础 | 完整 |

### 7.1 HTML API 创建模板#

Pro 版支持通过 HTML 创建模板，精确控制表单布局：

```bash
curl -X POST https://your-docuseal.com/api/v1/templates \
  -H "Content-Type: application/json" \
  -d '{
    "title": "合同模板",
    "html": "<html><body><input type=\"text\" data-type=\"signature\"></body></html>"
  }'
```

---

## §8 与 DocuSign 对比#

| 维度 | DocuSeal | DocuSign |
|------|----------|----------|
| **部署方式** | 自托管或 SaaS | 仅 SaaS |
| **价格** | 开源免费 / Pro 付费 | 按发送次数收费 |
| **数据控制** | 完全自主 | 依赖第三方 |
| **API** | 完整 REST API | 完整 API |
| **集成方式** | 自托管灵活 | 云端集成 |
| **合规认证** | 基础 | 高级（SOC2、HIPAA 等） |

---

## §9 适用场景#

### 9.1 适合的场景#

- 企业内部合同签署流程数字化'
- 需要多签署方的协议、合同'
- 需要与现有业务系统（CRM、ERP）集成的文档签署'
- 对数据主权有要求，不能使用 SaaS 服务的场景'

### 9.2 边界与局限#

- 电子签名合规性因国家/地区而异，需确认当地法律认可度'
- AGPLv3 协议要求开源，介意者需购买 Pro 版'
- 复杂表单（如嵌套条件逻辑）需要 Pro 版'
- 企业级合规认证（SOC2、HIPAA）需要 Pro 版或自建'

---

## §10 常见问题排查#

### 问题 1：Docker 容器无法启动#

**原因**：可能是端口冲突或数据目录权限问题'

**解决方法**：

```bash
# 1. 检查端口占用'
lsof -i :3000

# 2. 检查数据目录权限'
ls -la $(pwd)/data

# 3. 查看容器日志'
docker logs docuseal

# 4. 重新创建容器'
docker rm -f docuseal
docker run --name docuseal -p 3000:3000 -v $(pwd)/data:/data docuseal/docuseal
```

### 问题 2：邮件通知未发送#

**原因**：SMTP 配置错误或邮件被标记为垃圾邮件'

**解决方法**：

```bash
# 1. 检查 SMTP 配置'
echo $SMTP_ADDRESS
echo $SMTP_PORT

# 2. 测试 SMTP 连接'
telnet $SMTP_ADDRESS $SMTP_PORT

# 3. 查看 DocuSeal 日志'
docker logs docuseal | grep -i "mail\|smtp"

# 4. 检查垃圾邮件文件夹'
```

### 问题 3：API 调用返回 401 未授权#

**原因**：API 密钥未配置或已过期'

**解决方法**：

```bash
# 1. 在 DocuSeal 管理界面生成 API 密钥'
# 2. 在请求头中添加 Authorization'
curl -H "Authorization: Bearer YOUR_API_KEY" ...

# 3. 检查 API 密钥权限范围'
```

### 问题 4：Webhook 未接收到事件#

**原因**：Webhook URL 不可公网访问，或签名验证失败'

**解决方法**：

```bash
# 1. 使用 ngrok 等工具暴露本地服务'
ngrok http 3000

# 2. 在 DocuSeal 管理界面配置 Webhook URL'
# 3. 验证 Webhook 签名'
# 4. 查看 Webhook 交付日志'
```

### 问题 5：SSL 证书申请失败（Docker Compose 部署）#

**原因**：域名未正确解析到服务器 IP，或 80/443 端口被防火墙阻止'

**解决方法**：

```bash
# 1. 检查域名解析'
dig your-domain-name.com

# 2. 检查端口开放'
nc -zv your-domain-name.com 80
nc -zv your-domain-name.com 443

# 3. 查看 Caddy 日志'
docker logs docuseal | grep -i "caddy\|ssl\|certificate"

# 4. 临时使用 HTTP（仅测试）'
sudo HOST=your-domain-name.com docker-compose up
```

---

## §11 实践建议#

### 11.1 优化部署#

**建议 1：根据规模选择存储**

| 规模 | 推荐存储 |
|------|----------|
| **< 100 份/月** | 本地 SQLite |
| **100-1000 份/月** | PostgreSQ L或 MySQL |
| **> 1000 份/月** | PostgreSQ L + AWS S3 |

**建议 2：配置自动备份**

```bash
# 每天凌晨 2 点备份 SQLite 数据库'
0 2 * * * cp /data/docuseal.sqlite /backup/docuseal-$(date +\%Y\%m\%d).sqlite
```

**建议 3：使用 Nginx 反向代理提升性能**

```nginx
# /etc/nginx/sites-available/docuseal
server {
    listen 80;
    server_name your-domain-name.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 11.2 团队协作#

**共享配置**：

```bash
# 将配置文件提交到版本控制'
cp config/storage.yml ~/projects/dotfiles/docuseal-storage.yml
cd ~/projects/dotfiles
git add docuseal-storage.yml
git commit -m "Add DocuSeal storage config"
git push
```

**团队配置规范**：

1. 统一使用相同的存储后端（S3 或 PostgreSQL）'
2. 统一 SMTP 配置'
3. 统一 API 密钥权限范围'
4. 在 README 中记录配置方法'

### 11.3 安全优化#

**降低风险**：

```bash
# 1. 启用 HTTPS（Docker Compose 自动处理）'
# 2. 配置防火墙规则（仅允许必要端口）'
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# 3. 定期更新 DocuSeal 版本'
docker pull docuseal/docuseal:latest
docker-compose up -d

# 4. 配置 API 密钥轮换策略'
```

---

## §12 自测问题#

可以先用 5 个问题检验自己是否已经吃透 DocuSeal：

1. **DocuSeal 的核心优势是什么？与 DocuSign 的主要区别在哪里？**
2. **如何配置 Docker Compose 部署并自动申请 SSL 证书？**
3. **DocuSeal API 支持哪些主要操作？如何与业务系统集成？**
4. **开源版和 Pro 版的主要区别是什么？什么场景需要升级？**
5. **如何配置 Webhook 实现签署完成后的自动化操作？**

**参考答案**：

1. DocuSeal 的核心优势是**数据自主**（自托管）、**成本可控**（开源免费）、**灵活集成**（完整 REST API）；与 DocuSign 的主要区别是部署方式（自托管 vs. SaaS）。
2. 下载官方 `docker-compose.yml`，设置 `HOST=your-domain.com`，运行 `docker-compose up`，Caddy 会自动申请 Let's Encrypt SSL 证书。
3. 主要操作：创建模板、创建文档、发送签署邀请、获取文档状态、下载已签署文档；通过 REST API 和 Webhook 与 CRM、ERP 等业务系统集成。
4. Pro 版提供 Logo 定制、白标、用户角色管理、自动提醒、SMS 身份验证、条件字段和公式、SSO/SAML 等高级功能；需要企业级品牌定制、复杂表单、合规认证时需要升级。
5. 在 DocuSeal 管理界面配置 Webhook URL，DocuSeal 会在文档签署完成后向该 URL 发送 POST 请求；服务端需要验证签名、处理事件、更新业务系统状态。

---

## §13 进阶路径#

### 13.1 基础阶段（第 1-2 周）#

- [ ] 安装 DocuSeal 并熟悉基本操作'
- [ ] 创建第一个 PDF 表单模板'
- [ ] 配置 SMTP 并实现首次签署流程'
- [ ] 掌握 Docker 基础操作'

### 13.2 进阶阶段（第 3-4 周）#

- [ ] 配置 AWS S3 或 Google Cloud Storage 云存储'
- [ ] 集成 DocuSeal REST API 到业务系统'
- [ ] 配置 Webhook 实现自动化工作流'
- [ ] 排查常见问题和性能优化'

### 13.3 高级阶段（第 5-8 周）#

- [ ] 从源码构建 DocuSeal'
- [ ] 贡献代码到上游（提交 PR）'
- [ ] 开发自定义字段类型或集成插件'
- [ ] 在企业中推广 DocuSeal 最佳实践'

### 13.4 相关资源#

| 资源 | 链接 |
|------|------|
| **GitHub 仓库** | https://github.com/docusealco/docuseal |
| **官方网站** | https://docuseal.com |
| **在线演示** | https://demo.docuseal.tech |
| **官方文档**（Pro 功能） | https://docuseal.com/pricing |
| **Docker Hub** | https://hub.docker.com/r/docuseal/docuseal |

---

## §14 总结速查#

### 核心要点#

1. **DocuSeal 是开源电子签名解决方案**，可作为 DocuSign 替代方案'
2. **支持 12 种字段类型**，覆盖完整签署流程'
3. **Docker 一键部署**，支持自托管或云平台'
4. **完整 REST API 和 Webhook**，支持与企业系统集成'
5. **开源版免费使用**，Pro 版提供高级功能（白标、SSO、条件字段等）'

### 快速命令#

| 命令 | 用途 |
|------|------|
| `docker run docuseal/docuseal` | Docker 启动 DocuSeal |
| `docker-compose up` | Docker Compose 启动（生产级）|
| `curl /api/v1/templates` | 创建模板（API）|
| `curl /api/v1/documents` | 创建待签署文档（API）|

---

**文档信息**

难度：⭐⭐ | 类型：完全指南 | 更新日期：2026-05-05 | 预计阅读时间：20 分钟'
