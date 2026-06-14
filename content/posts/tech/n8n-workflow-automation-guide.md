---
title: "n8n：开源工作流自动化平台指南"
date: "2026-04-06T22:16:00+08:00"
slug: "n8n-workflow-automation-guide"
description: "介绍 183k Stars 的 n8n 工作流自动化平台，涵盖 400+ 集成、AI LangChain 原生支持、Docker 部署、企业级 SSO、权限管理、自定义节点开发，以及实战案例和建议做法。"
draft: false
categories: ["技术笔记"]
tags: ["n8n", "工作流自动化", "AI Agent", "LangChain", "低代码", "开源"]
---

## 这篇文章覆盖什么

- n8n 的项目定位、核心概念和设计理念
- 安装、部署和基本使用方法
- 可视化编辑器和工作流节点
- AI 与 LangChain 原生集成，构建 AI Agent 工作流
- 400+ 集成的使用场景和配置方法
- 自托管和企业级功能
- 自定义节点开发和扩展 n8n

---

## 1. 项目概述

### 1.1 是什么

**n8n** 是一个**工作流自动化平台**，为技术团队提供代码的灵活性与无代码的速度。

核心理念：用代码扩展能力，用无代码提升效率。

n8n 发音为 "n-eight-n"，源自 "nodemation"（Node.js + automation）。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **183k** |
| GitHub Forks | **56.5k** |
| Watchers | **1.1k** |
| Releases | **571 个** |
| 最新版本 | **v2.14.2** (2026-03-26) |
| License | **Sustainable Use License** (fair-code) |
| 语言 | **TypeScript 91.3%**，Vue 7.4% |

### 1.3 为什么选择 n8n

| 特性 | 说明 |
|------|------|
| **代码灵活性** | 可写 JavaScript/Python，添加 npm 包 |
| **AI 原生** | 基于 LangChain 构建 AI Agent 工作流 |
| **400+ 集成** | 主流服务和应用无缝连接 |
| **自托管** | 完全控制数据和部署 |
| **企业就绪** | SSO、细粒度权限、空中隔离部署 |
| **活跃社区** | 900+ 模板，快速上手 |

### 1.4 n8n vs 其他自动化平台

| 平台 | n8n | Zapier | Make |
|------|------|--------|------|
| **代码扩展** | ✅ JS/Python | ❌ | ⚠️ 有限 |
| **自托管** | ✅ 完全开源 | ❌ | ❌ |
| **AI 集成** | ✅ LangChain 原生 | ⚠️ 有限 | ⚠️ 有限 |
| **价格** | 免费/企业付费 | 按执行收费 | 按操作收费 |
| **数据控制** | 完全自控 | 云端 | 云端 |

---

## 2. 快速开始

### 2.1 安装方式

**方式一：npx 快速启动（推荐用于测试）**

```bash
# 需要 Node.js
npx n8n
```

**方式二：Docker 部署（生产推荐）**

```bash
# 创建持久化卷
docker volume create n8n_data

# 启动容器
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n

# 访问编辑器
# http://localhost:5678
```

**方式三：Docker Compose（生产推荐）**

```yaml
version: '3'
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
    environment:
      - N8N_SECURE_COOKIE=false
    restart: unless-stopped
volumes:
  n8n_data:
```

**方式四：手动安装**

```bash
# 克隆仓库
git clone https://github.com/n8n-io/n8n.git
cd n8n

# 安装依赖
pnpm install

# 构建
pnpm build

# 启动
pnpm start
```

### 2.2 基本概念

**节点（Node）**：工作流中的基本单元，每个节点执行一个操作

**工作流（Workflow）**：连接多个节点形成完整业务流程

**触发器（Trigger）**：工作流的起始节点，决定何时执行

### 2.3 第一个工作流

创建一个简单的 "收到邮件 → 保存到 Google Sheets" 工作流：

```
[Webhook 触发] → [Gmail 读取] → [Google Sheets 写入]
```

---

## 3. 核心功能详解

### 3.1 可视化编辑器

n8n 提供直观的可视化编辑器：

| 功能 | 说明 |
|------|------|
| **拖拽节点** | 从节点面板拖拽到画布 |
| **连接节点** | 拖拽连接点创建数据流 |
| **配置面板** | 点击节点配置参数 |
| **数据预览** | 执行后查看每个节点输出 |
| **错误追踪** | 快速定位失败节点 |

### 3.2 代码能力

**内置代码节点**：

```javascript
// JavaScript 代码节点
const timestamp = new Date().toISOString();
const data = $input.first().json;

// 转换数据
const transformed = {
  id: data.id,
  name: data.name.toUpperCase(),
  processedAt: timestamp,
  // 添加自定义逻辑
  category: data.value > 100 ? 'high' : 'low'
};

return [{ json: transformed }];
```

**Python 代码节点**：

```python
import json
from datetime import datetime

timestamp = datetime.now().isoformat()
data = $input.first().json

transformed = {
    "id": data["id"],
    "name": data["name"].upper(),
    "processedAt": timestamp,
    "category": "high" if data["value"] > 100 else "low"
}

return [{"json": transformed}]
```

### 3.3 AI 与 LangChain 集成

n8n 是 **AI-Native 平台**，内置 LangChain 支持：

**构建 AI Agent 工作流**：

```
[LangChain Agent] → [Tool: Wikipedia] → [Tool: Calculator] → [输出]
```

**聊天机器人工作流**：

```
[Webhook] → [LangChain Agent] → [Slack/Discord 发送]
```

**RAG (检索增强生成) 工作流**：

```
[文档上传] → [向量化] → [向量数据库] → [LLM 查询]
```

### 3.4 触发器类型

| 触发器 | 说明 |
|--------|------|
| **Webhook** | HTTP 请求触发 |
| **Schedule** | 定时执行（cron） |
| **Email** | 收到邮件触发 |
| **Node** | 其他节点触发 |
| **Manual** | 手动执行 |
| **Form** | 表单提交触发 |

---

## 4. 400+ 集成

### 4.1 常用集成分类

| 分类 | 代表集成 |
|------|---------|
| **AI & ML** | OpenAI、Anthropic Claude、LangChain、Hugging Face |
| **通信** | Slack、Discord、Teams、Email |
| **云服务** | AWS、Google Cloud、Azure |
| **数据库** | PostgreSQL、MySQL、MongoDB、Redis |
| **CRM** | Salesforce、HubSpot |
| **电商** | Shopify、WooCommerce、Stripe |
| **社交** | Twitter/X、LinkedIn、Instagram |
| **开发** | GitHub、GitLab、Jira |

### 4.2 OpenAI 集成示例

```javascript
// OpenAI ChatGPT 节点配置
{
  "resource": "chat",
  "operation": "complete",
  "model": "gpt-4",
  "messages": [
    {
      "role": "user",
      "content": "解释这段代码的功能"
    }
  ],
  "temperature": 0.7,
  "maxTokens": 500
}
```

### 4.3 Slack 集成示例

```javascript
// Slack 发送消息节点配置
{
  "resource": "message",
  "operation": "post",
  "channel": "#general",
  "text": "工作流执行完成！\n状态：成功\n时间：{{ $now }}",
  "username": "n8n Bot"
}
```

### 4.4 数据库集成示例

```javascript
// PostgreSQL 查询节点
{
  "operation": "execute",
  "query": "SELECT * FROM users WHERE created_at > $1",
  "values": ["{{ $json.since }}"]
}
```

---

## 5. 自托管与部署

### 5.1 Docker 部署

**基础部署**：

```bash
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  -e N8N_HOST=your-domain.com \
  -e N8N_PROTOCOL=https \
  -e WEBHOOK_URL=https://your-domain.com/ \
  docker.n8n.io/n8nio/n8n
```

**使用代理**：

```bash
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  -e HTTP_PROXY=http://proxy:8080 \
  -e HTTPS_PROXY=http://proxy:8080 \
  docker.n8n.io/n8nio/n8n
```

### 5.2 环境变量配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `N8N_HOST` | 主机名 | localhost |
| `N8N_PORT` | 端口 | 5678 |
| `N8N_PROTOCOL` | 协议 | http |
| `WEBHOOK_URL` | Webhook 基础 URL | - |
| `N8N_BASIC_AUTH_ACTIVE` | 启用 Basic Auth | false |
| `N8N_BASIC_AUTH_USER` | Basic Auth 用户名 | - |
| `N8N_BASIC_AUTH_PASSWORD` | Basic Auth 密码 | - |
| `N8N_ENCRYPTION_KEY` | 加密密钥 | 自动生成 |
| `EXECUTIONS_DATA_SAVE_ON_ERROR` | 错误时保存数据 | all |
| `EXECUTIONS_DATA_SAVE_ON_SUCCESS` | 成功时保存数据 | all |

### 5.3 数据持久化

```bash
# 创建命名卷
docker volume create n8n_data

# 查看卷位置
docker volume inspect n8n_data
```

### 5.4 HTTPS 配置

**使用 Traefik**：

```yaml
# docker-compose.yml
services:
  traefik:
    image: traefik:v2.10
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./traefik.yml:/traefik.yml
      - ./certs:/certs

  n8n:
    image: docker.n8n.io/n8nio/n8n
    environment:
      - N8N_HOST=n8n.example.com
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://n8n.example.com/
    labels:
      - traefik.enable=true
      - traefik.http.routers.n8n.rule=Host(`n8n.example.com`)
      - traefik.http.routers.n8n.tls.certresolver=letsencrypt
```

---

## 6. 企业级功能

### 6.1 权限管理

**角色系统**：

| 角色 | 权限 |
|------|------|
| Owner | 完全控制 |
| Admin | 管理用户和工作流 |
| Member | 编辑自己的工作流 |
| Editor | 仅编辑 |
| Viewer | 仅查看 |

**项目隔离**：

- 按项目分组工作流
- 独立权限控制
- 跨项目模板共享

### 6.2 SSO 配置

**支持的身份提供商**：

- SAML 2.0
- OIDC (OpenID Connect)
- LDAP/Active Directory

**OIDC 配置示例**：

```yaml
# 环境变量
N8N_SSO_ENABLED=true
N8N_SSO_PROVIDER=oidc
N8N_SSO_CLIENT_ID=your-client-id
N8N_SSO_CLIENT_SECRET=your-client-secret
N8N_SSO_ISSUER_URL=https://your-idp.com
```

### 6.3 空中隔离部署

n8n 支持 Air-Gapped 环境部署：

- 无需互联网连接
- 完全离线运行
- 企业内部数据安全

### 6.4 审计日志

- 用户操作记录
- 工作流执行历史
- 敏感操作告警

---

## 7. 自定义节点开发

### 7.1 创建自定义节点

```bash
# 使用 n8n 节点开发工具
npx n8n-node-dev

# 选择基础模板
? Select a template for your new node
  ❯ Empty Node
    CredentialType
    Template
```

### 7.2 节点结构

```
my-custom-node/
├── src
│   └── nodes
│       └── MyCustomNode
│           ├── MyCustomNode.node.ts
│           └── MyCustomNode.trigger.ts
├── credentials
│   └── MyCustomApi.credentials.ts
├── package.json
└── README.md
```

### 7.3 节点代码示例

```typescript
import { INodeType, INodeTypeDescription } from 'n8n-workflow';

export class MyCustomNode implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'My Custom Node',
    name: 'myCustomNode',
    icon: 'fa:rocket',
    group: ['transform'],
    version: 1,
    description: 'A custom node I built',
    defaults: {
      name: 'My Custom Node',
    },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      {
        displayName: 'API Key',
        name: 'apiKey',
        type: 'string',
        default: '',
      },
      {
        displayName: 'Operation',
        name: 'operation',
        type: 'options',
        options: [
          { name: 'Get', value: 'get' },
          { name: 'Post', value: 'post' },
        ],
        default: 'get',
      },
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    const items = this.getInputData();
    const returnData: INodeExecutionData[] = [];

    for (let i = 0; i < items.length; i++) {
      const apiKey = this.getNodeParameter('apiKey', i) as string;
      const operation = this.getNodeParameter('operation', i) as string;

      // 执行操作
      const result = { operation, timestamp: new Date().toISOString() };
      returnData.push({ json: result });
    }

    return [returnData];
  }
}
```

### 7.4 发布节点

```bash
# 构建
pnpm build

# 登录 npm
npm login

# 发布到 npm
npm publish --access public
```

---

## 8. 实战案例

### 8.1 AI 客服机器人

```
[Webhook 触发] 
  → [LangChain Agent] 
    → [Tool: Slack] 
    → [Tool: 数据库查询]
```

功能：
- 自动回复客户咨询
- 知识库检索
- 工单创建

### 8.2 数据同步管道

```
[Schedule 触发]
  → [PostgreSQL 查询]
  → [数据转换]
  → [Elasticsearch 索引]
  → [发送 Slack 通知]
```

功能：
- 定时同步数据
- 数据清洗转换
- 全量/增量同步

### 8.3 社交媒体管理

```
[RSS 触发]
  → [内容提取]
  → [AI 生成摘要]
  → [多平台发布]
    → Twitter
    → LinkedIn
    → Facebook
```

功能：
- 定时获取资讯
- AI 辅助创作
- 一键多平台发布

### 8.4 电商订单处理

```
[Shopify 新订单]
  → [验证库存]
  → [创建发货单]
  → [发送邮件通知]
  → [更新 CRM]
```

---

## 9. 实践建议

### 9.1 工作流设计

| 实践 | 说明 |
|------|------|
| **模块化** | 拆分为子工作流复用 |
| **错误处理** | 添加错误捕获和重试 |
| **日志记录** | 使用 Code 节点记录关键步骤 |
| **数据验证** | 使用 IF 节点验证数据 |

### 9.2 性能优化

```javascript
// 批量处理示例
const items = $input.all();

return items.map(item => ({
  json: {
    ...item.json,
    processed: true,
    batchId: Math.random().toString(36).substr(2, 9)
  }
}));
```

### 9.3 安全实践

- **凭据管理**：使用 n8n 凭据存储，不硬编码
- **环境变量**：敏感配置使用环境变量
- **最小权限**：数据库用户使用最小权限
- **定期备份**：备份 n8n_data 卷

### 9.4 监控告警

```javascript
// 错误告警工作流
const error = $json.error;
const workflowName = $workflow.name;

if (error) {
  return [{
    json: {
      alert: 'Workflow Failed',
      workflow: workflowName,
      error: error.message,
      time: new Date().toISOString()
    }
  }];
}
```

---

## 10. 常见问题

### 10.1 如何调试工作流？

1. 使用 "Manual" 触发器逐步测试
2. 在每个节点后添加 Code 节点打印数据
3. 使用 "Preview" 模式查看节点输出
4. 查看执行历史中的错误信息

### 10.2 如何处理大文件？

- 使用流式处理（Streaming）
- 配置 `EXECUTIONS_DATA_TIMEOUT` 超时时间
- 使用 "Chunk" 节点分批处理

### 10.3 如何实现高可用？

```yaml
# docker-compose.yml for HA
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n
    deploy:
      replicas: 3
    depends_on:
      - redis
      - postgres
  redis:
    image: redis:7-alpine
  postgres:
    image: postgres:15
```

### 10.4 如何升级 n8n？

```bash
# Docker 方式
docker pull docker.n8n.io/n8nio/n8n:latest
docker stop n8n
docker rm n8n
# 重新启动（数据保持）
```

---

## 11. 总结

**n8n** 是技术团队工作流自动化的**首选开源方案**：

| 优势 | 说明 |
|------|------|
| **代码+无代码** | 兼顾灵活性与效率 |
| **AI 原生** | LangChain 深度集成 |
| **400+ 集成** | 覆盖主流服务 |
| **完全自控** | 自托管，数据不出局 |
| **开源透明** | 源代码完全可见 |
| **活跃社区** | 900+ 模板，快速上手 |

**适用场景**：

- 企业内部流程自动化
- AI Agent 工作流构建
- 数据同步和 ETL
- 客服和沟通自动化
- 社交媒体管理
- 电商订单处理

**官方资源**：

- GitHub：https://github.com/n8n-io/n8n
- 文档：https://docs.n8n.io
- 集成中心：https://n8n.io/integrations
- 模板库：https://n8n.io/workflows
- 社区论坛：https://community.n8n.io
- AI 指南：https://docs.n8n.io/advanced-ai/