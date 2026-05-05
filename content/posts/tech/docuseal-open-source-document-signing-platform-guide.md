---
title: "DocuSeal：开源电子文档签署平台，DocuSign替代方案"
date: 2026-05-05T11:35:00+08:00
slug: "docuseal-open-source-document-signing-platform-guide"
description: "DocuSeal是开源的电子文档签署和处理平台，提供PDF表单构建、数字签名、自动化邮件、API和Webhook集成等功能，支持Docker一键部署。本文详解其功能特性、部署方式、API集成与Pro版高级功能。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "电子签名", "PDF", "文档处理", "DocuSign替代", "Docker"]
---

## 项目概览

[DocuSeal](https://github.com/docusealco/docuseal) 是一个开源电子文档签署和处理平台，可作为DocuSign的替代方案。用户可以通过直观的Web界面创建PDF表单、收集填写内容、数字签名，并在任何设备上完成签署流程。

**核心数据：**
- GitHub Stars：535
- 技术栈：Ruby
- 部署方式：Docker、Railway、Heroku、DigitalOcean、Render
- License：AGPLv3 + Section 7(b) Additional Terms
- 支持语言：7种UI语言，签署支持14种语言

**核心功能：**
- PDF表单构建器（WYSIWYG）
- 12种字段类型（签名、日期、文件、复选框等）
- 多签署方支持
- 自动化邮件通知
- 本地存储或云存储（S3、Google Storage、Azure）
- API和Webhook集成
- Docker一键部署

---

## 核心功能详解

### 1. PDF表单构建器

DocuSeal提供所见即所得的表单编辑器，无需编程即可创建专业级PDF表单：

**支持的字段类型：**
| 字段类型 | 说明 |
|---------|------|
| Signature | 电子签名（核心功能） |
| Date | 日期选择 |
| File | 文件上传 |
| Checkbox | 复选框 |
| Text Input | 文本输入 |
| Text Area | 多行文本 |
| Dropdown | 下拉选择 |
| Radio | 单选按钮 |
| Image | 图片嵌入 |
| Drawing | 手绘签名 |
| Initial | 首字母缩写 |
| Stamp | 印章 |

### 2. 多签署方流程

支持设置多个签署方，并定义签署顺序：

```bash
# 示例：创建需要甲乙双方签署的合同
1. 甲方先签署（自动邮件通知）
2. 甲方签署完成后，乙方收到签署邀请
3. 乙方签署完成，双方均收到已签署文档副本
```

### 3. 存储选项

| 存储方式 | 说明 |
|---------|------|
| 本地磁盘 | 默认SQLite，适合小规模使用 |
| AWS S3 | 企业级对象存储 |
| Google Cloud Storage | GCP生态集成 |
| Azure Blob Storage | 微软云生态集成 |
| PostgreSQL | 关系型数据库（可选） |
| MySQL | 关系型数据库（可选） |

### 4. API与Webhook

DocuSeal提供完整的REST API和Webhook，支持与企业系统深度集成：

**API端点示例：**
```
POST /api/v1/templates          # 创建模板
POST /api/v1/documents          # 创建待签署文档
GET  /api/v1/documents/:id      # 获取文档状态
POST /api/v1/documents/:id/send # 发送签署邀请
GET  /api/v1/documents/:id/file # 下载已签署文档
```

**Webhook事件：**
- document.completed — 文档签署完成
- document.signed — 有人完成签署
- template.created — 模板创建成功

---

## 部署方式

### Docker（推荐，最简方式）

```bash
# 单行命令启动
docker run --name docuseal -p 3000:3000 -v .:/data docuseal/docuseal
```

默认使用SQLite数据库存储在`/data`目录。

### Docker Compose（生产级部署，支持HTTPS）

```bash
# 下载docker-compose配置
curl https://raw.githubusercontent.com/docusealco/docuseal/master/docker-compose.yml > docker-compose.yml

# 启动（自动通过Caddy申请SSL证书）
sudo HOST=your-domain-name.com docker compose up
```

### 一键部署平台

| 平台 | 按钮 |
|------|------|
| Heroku | 点击部署 |
| Railway | 点击部署 |
| DigitalOcean | 点击部署 |
| Render | 点击部署 |

### 环境变量配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接串 | SQLite本地文件 |
| `SMTP_ADDRESS` | SMTP服务器地址 | - |
| `SMTP_PORT` | SMTP端口 | 587 |
| `SMTP_USERNAME` | SMTP用户名 | - |
| `SMTP_PASSWORD` | SMTP密码 | - |
| `SMTP_FROM` | 发件人地址 | - |
| `AWS_BUCKET` | S3桶名称 | - |
| `AWS_REGION` | AWS区域 | - |
| `AWS_ACCESS_KEY_ID` | AWS访问密钥 | - |
| `AWS_SECRET_ACCESS_KEY` | AWS秘密密钥 | - |

---

## Pro版功能

DocuSeal分为开源版和Pro版，Pro版提供更高级功能：

| 功能 | 开源版 | Pro版 |
|------|--------|-------|
| 基础表单字段 | ✅ | ✅ |
| 多签署方 | ✅ | ✅ |
| PDF导出 | ✅ | ✅ |
| Logo定制 | ❌ | ✅ |
| 白标 | ❌ | ✅ |
| 用户角色管理 | ❌ | ✅ |
| 自动提醒 | ❌ | ✅ |
| SMS身份验证 | ❌ | ✅ |
| 条件字段和公式 | ❌ | ✅ |
| CSV/XLSX批量发送 | ❌ | ✅ |
| SSO/SAML | ❌ | ✅ |
| HTML API模板创建 | 基础 | 完整 |

### HTML API创建模板

Pro版支持通过HTML创建模板，精确控制表单布局：

```bash
curl -X POST https://your-docuseal.com/api/v1/templates \
  -H "Content-Type: application/json" \
  -d '{
    "title": "合同模板",
    "html": "<html><body><input type=\"text\" data-type=\"signature\"></body></html>"
  }'
```

---

## 集成示例

### React集成

DocuSeal提供官方React组件，支持嵌入式签署表单：

```bash
npm install @docuseal/react
```

```jsx
import { Docuseal } from '@docuseal/react'

function App() {
  return (
    <Docuseal
      endpoint="https://your-docuseal.com"
      templateId="abc123"
      onComplete={(document) => {
        console.log('签署完成', document.id)
      }}
    />
  )
}
```

类似的还有Vue和Angular官方组件。

### Webhook处理示例

```python
# Python Flask示例
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook/docuseal', methods=['POST'])
def handle_webhook():
    event = request.json
    
    if event['type'] == 'document.completed':
        document_id = event['data']['id']
        # 下载已签署文档
        # 更新业务系统状态
        pass
    
    return 'OK', 200
```

---

## 适用场景

### 适合的场景
- 企业内部合同签署流程数字化
- 需要多签署方的协议、合同
- 需要与现有业务系统（CRM、ERP）集成的文档签署
- 对数据主权有要求，不能使用SaaS服务的场景

### 边界与局限
- 电子签名合规性因国家/地区而异，需确认当地法律认可度
- AGPLv3协议要求开源，介意者需购买Pro版
- 复杂表单（如嵌套条件逻辑）需要Pro版

---

## 与DocuSign对比

| 维度 | DocuSeal | DocuSign |
|------|----------|----------|
| 部署方式 | 自托管或SaaS | 仅SaaS |
| 价格 | 开源免费/Pro付费 | 按发送次数收费 |
| 数据控制 | 完全自主 | 依赖第三方 |
| API | 完整REST API | 完整API |
| 集成方式 | 自托管灵活 | 云端集成 |
| 合规认证 | 基础 | 高级（SOX、HIPAA等） |

---

## 总结

DocuSeal是一个功能完整的开源电子签名解决方案，适合需要：
1. **数据自主**：不愿将敏感文档放到第三方SaaS
2. **成本控制**：开源版免费使用，节省DocuSign按次计费成本
3. **深度定制**：需要与内部系统深度集成的企业

其Docker一键部署、完整的API和Webhook支持，使得它既能作为小型团队的独立工具，也能嵌入到大型企业的数字化流程中。

**参考链接：**
- GitHub：https://github.com/docusealco/docuseal
- 官方文档：https://docuseal.com
- 在线演示：https://demo.docuseal.tech
- 官方文档（Pro功能）：https://docuseal.com/pricing