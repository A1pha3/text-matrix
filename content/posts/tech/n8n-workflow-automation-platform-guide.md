---
title: "n8n 工作流自动化平台：从入门到精通完全指南"
date: "2026-05-02T10:12:00+08:00"
lastmod: 2026-05-02T10:12:00+08:00
slug: n8n-workflow-automation-platform-guide
summary: "n8n 是一款基于 fair-code 模式开源的工作流自动化平台，支持 400 + 集成与原生 AI 能力。本文系统讲解其核心概念、执行引擎、架构设计、本地部署配置、Docker 与 npm 安装方式、可视化编辑器使用、实战工作流示例及自定义节点开发路径。"
description: "本文系统讲解 n8n 的工作原理、节点架构、执行引擎、AI 原生能力，以及 Docker/npm 安装配置、可视化编辑器实战、自定义节点开发与生产环境最佳实践。"
draft: false
categories: ["技术笔记"]
tags: ["n8n", "工作流自动化", "TypeScript", "AI Agent", "无代码", "LangChain", "Docker"]
---

> **目标读者**：希望搭建自动化工作流、或将 n8n 作为 AI Agent 执行引擎的后端工程师与全栈开发者。
> **核心问题**：n8n 与 Zapier/Make/Integromat 有何本质差异？为什么它适合自托管？它的执行模型到底是怎么工作的？自定义节点怎么写？
> **事实边界**：本文基于 n8n 官方 GitHub 仓库（v1.x）与公开文档整理；代码示例基于 n8n 开源版本，企业版特有功能单独标注。

## 阅读导航

- 只想快速跑起来：直接看 `§4 安装配置`
- 想理解执行模型：先看 `§3 核心概念与执行模型`
- 想了解完整架构：看 `§5 架构分析`
- 想动手写个工作流：看 `§6 实战演示`
- 想写自己的节点：看 `§7 开发扩展`

## §1 学习目标

完成本文后，你应该能够：

- 理解 n8n 的节点图执行模型与数据流机制
- 掌握 Docker 与 npm 两种安装方式的差异与适用场景
- 使用可视化编辑器构建包含条件分支、循环、AI 调用和数据转换的工作流
- 将 n8n 自托管部署到生产环境并配置反向代理、HTTPS 与外部数据库
- 理解 n8n 的 Credential 机制与安全模型
- 基于 n8n SDK 编写并发布自定义节点

## §2 为什么是 n8n

在 n8n 出现之前，工作流自动化领域被 Zapier 和 Make（Integromat）主导。这两个平台都是 SaaS 模式——你的工作流跑在他们的云上，数据经过他们的服务器。如果你的场景需要：

- **数据完全自主**：金融数据、医疗记录、用户隐私不能交给第三方
- **自定义逻辑**：平台自带的条件/循环不够用，需要写 Python/JavaScript
- **成本控制**：集成数量按月收费贵，自托管反而划算
- **深度定制**：需要修改自动化平台本身的行为

n8n 正好填补了这个空白。它的核心差异在于：

| 维度 | Zapier/Make | n8n |
|---|---|---|
| 部署方式 | 仅云端 | 自托管 + 云端 |
| 代码能力 | 受限的 Code 步骤 | 原生 JavaScript/Python |
| 集成数量 | 5000+（按月付费） | 400+（开源免费） |
| 许可证 | 专有 | fair-code（源码可见，可自用） |
| AI 能力 | 有限 | LangChain 原生集成 |
| 扩展方式 | 官方维护 | 可自建节点 |

n8n 采用 fair-code 许可模式——源码可见、可自托管运行，但商业用途需要购买许可证。这意味着你可以完全掌控自己的数据和工作流，同时项目有可持续的商业模式支撑。

## §3 核心概念与执行模型

### 3.1 节点、连接与工作流三元素

n8n 的数据模型极其简洁，核心只有三个概念：

**节点（Node）** 是 n8n 的基本计算单元。每个节点做一件事：读取数据、转换数据、发送数据或执行动作。n8n 提供了 400+ 官方节点，覆盖 HTTP 请求、数据库操作、消息推送、文件处理、AI 模型调用等场景。

**连接（Connection）** 是节点之间的有向数据通道。数据从上游节点的输出端口流向下游节点的输入端口，形成有向无环图（DAG）。n8n 允许一个节点有多个输入/输出端口，支持多输入汇聚和多输出分发。

**工作流（Workflow）** 是节点与连接构成的完整自动化逻辑单元。每个工作流有一个触发器节点（Trigger Node）作为起点，当特定事件发生时触发整条链的执行。

### 3.2 执行模型：推拉结合

n8n 的执行模型比较特殊，它不是简单的"触发-执行"线性流，而是支持两种数据获取模式：

**Polling Trigger（轮询触发）**：节点按固定时间间隔主动拉取数据。例如 Cron 节点按 cron 表达式定时触发，IMAP 节点每 N 分钟检查一次邮件。轮询模式的特点是"拉"——节点主动发起请求获取新数据。

**Event Trigger（事件触发）**：节点等待外部事件被动接收数据。例如 Webhook 节点等待 HTTP 请求传入，RabbitMQ 节点等待消息到达队列。事件模式的特点是"推"——外部系统主动将数据推入。

这两种模式通过节点的输入/输出端口统一抽象为同一条数据流水线。无论数据来自轮询还是事件触发，都经过相同的转换、路由和输出节点。

### 3.3 数据流与二进制数据处理

n8n 内部使用 JSON 作为统一的数据表示格式。每个节点接收一个 JSON 对象（或对象数组），经过处理后输出新的 JSON 对象。节点的输入输出通过 `Connection` 对象传递，包含两个主要数据槽：

- **JSON Data**：结构化数据，以键值对或数组形式存在
- **Binary Data**：二进制数据（文件、图片、音频等），以 `binary` 对象引用

这种设计允许节点自由组合——例如 HTTP 节点拉取一个 CSV 文件，Binary 节点将其解析为 JSON，Transform 节点做数据清洗，Database 节点写入 PostgreSQL。整个链路中二进制和 JSON 数据可以交替转换。

### 3.4 执行引擎的内部调度

当一个工作流被触发时，n8n 的执行引擎会做以下几件事：

1. **构建执行图**：将工作流的节点和连接转换为内部可执行的 DAG 结构
2. **拓扑排序**：按照依赖关系确定节点的执行顺序
3. **异步调度**：从触发节点开始，按拓扑序异步执行各节点
4. **数据传递**：上游节点的输出自动作为下游节点的输入
5. **错误处理**：节点执行失败时，根据工作流配置选择停止、重试或继续执行
6. **输出汇总**：执行完成后收集各节点的输出，生成执行日志

n8n 使用 Node.js 原生的异步调度机制，因此对 I/O 密集型任务（网络请求、数据库查询）有很好的并发处理能力。

### 3.5 AI 原生能力：LangChain 集成

n8n 在 v0.200+ 版本后引入了原生 AI 支持，基于 LangChain 构建。这意味着你可以直接在可视化编辑器里组合：

- **AI Agent 节点**：创建能够调用工具的 AI Agent，支持 OpenAI GPT、Anthropic Claude 等模型
- **Chain 节点**：构建 Chain-of-Thought、RetrievalQA 等链式推理流程
- **Memory 节点**：在对话中维护上下文状态，实现多轮对话
- **Embedding 节点**：将文本向量化，用于 RAG（检索增强生成）场景

AI 能力与 n8n 的节点图模型天然契合：你可以在工作流中插入 AI 节点处理自然语言输入，然后将其输出连接到数据库或消息推送节点，构建完整的 AI 应用。

## §4 安装配置

n8n 支持三种安装方式，各有适用场景：

### 4.1 Docker 安装（推荐）

Docker 是生产环境部署的首选方式，也是最省事的本地试用方式。

**快速启动**：

```bash
# 创建持久化存储卷
docker volume create n8n_data

# 启动 n8n（前台运行）
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n
```

访问 `http://localhost:5678` 即可打开可视化编辑器。

**带 PostgreSQL 数据库的生产部署**：

```bash
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -e N8N_PROTOCOL=https \
  -e WEBHOOK_URL=https://your-domain.com \
  -e DB_TYPE=postgresdb \
  -e DB_POSTGRESDB_HOST=10.0.1.5 \
  -e DB_POSTGRESDB_PORT=5432 \
  -e DB_POSTGRESDB_DATABASE=n8n \
  -e DB_POSTGRESDB_USER=n8n_user \
  -e DB_POSTGRESDB_PASSWORD=n8n_secret \
  -e N8N_ENCRYPTION_KEY=your-32-char-secret-key \
  -v n8n_data:/home/node/.n8n \
  --restart unless-stopped \
  docker.n8n.io/n8nio/n8n
```

**docker-compose 生产部署**：

```yaml
version: '3'
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=https://n8n.your-domain.com
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=n8n
      - DB_POSTGRESDB_PASSWORD=${DB_PASSWORD}
      - N8N_ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - EXECUTIONS_MODE=regular
      - GENERIC_TIMEZONE=Asia/Shanghai
    volumes:
      - n8n_data:/home/node/.n8n
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_DB=n8n
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U n8n"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  n8n_data:
  postgres_data:
```

### 4.2 npm 全局安装

适合开发者本地调试，或在没有 Docker 环境的服务器上快速部署。

**前置条件**：Node.js v18+（建议 v20 LTS）

```bash
# 全局安装
npm install -g n8n

# 启动
n8n
# 或者指定端口
n8n --port 5679
```

**带数据库的配置**：

```bash
export DB_TYPE=postgresdb
export DB_POSTGRESDB_HOST=localhost
export DB_POSTGRESDB_PORT=5432
export DB_POSTGRESDB_DATABASE=n8n
export DB_POSTGRESDB_USER=n8n
export DB_POSTGRESDB_PASSWORD=secret
export N8N_ENCRYPTION_KEY=32-char-encryption-key-here
export WEBHOOK_URL=https://n8n.your-domain.com
n8n
```

### 4.3 环境变量速查表

| 变量 | 说明 | 示例 |
|---|---|---|
| `N8N_PROTOCOL` | 协议类型 | `http` / `https` |
| `WEBHOOK_URL` | Webhook 基础 URL | `https://n8n.example.com` |
| `DB_TYPE` | 数据库类型 | `sqlite` / `postgresdb` |
| `DB_POSTGRESDB_HOST` | PostgreSQL 主机 | `10.0.1.5` |
| `DB_POSTGRESDB_PORT` | PostgreSQL 端口 | `5432` |
| `DB_POSTGRESDB_DATABASE` | 数据库名 | `n8n` |
| `DB_POSTGRESDB_USER` | 数据库用户 | `n8n` |
| `DB_POSTGRESDB_PASSWORD` | 数据库密码 | `***` |
| `N8N_ENCRYPTION_KEY` | 加密密钥（32字符） | `xxx` |
| `GENERIC_TIMEZONE` | 时区 | `Asia/Shanghai` |
| `EXECUTIONS_MODE` | 执行模式 | `regular` / `queue` |
| `N8N_HIRING_IN_ASIA` | 允许亚洲节点 | `true` |
| `N8N_LOG_LEVEL` | 日志级别 | `info` / `debug` |

### 4.4 反向代理配置（Nginx）

生产环境通常需要 Nginx 反向代理并提供 HTTPS：

```nginx
upstream n8n {
    server 127.0.0.1:5678;
}

server {
    listen 443 ssl http2;
    server_name n8n.your-domain.com;

    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://n8n;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持（n8n 编辑器实时通信）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时配置
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Webhook 路径（可选，用于区分处理）
    location /webhook/ {
        proxy_pass http://n8n;
        proxy_read_timeout 300s;
    }
}
```

### 4.5 SQLite vs PostgreSQL

默认情况下 n8n 使用嵌入式 SQLite，适合个人使用和中小团队。但有以下限制时应当切换到 PostgreSQL：

- **高可用部署**：多实例运行需要共享状态
- **大型工作流库**：SQLite 在数千个工作流时性能下降
- **需要备份一致性**：PostgreSQL 的备份机制更成熟
- **并发写入**：SQLite 写并发受限于单写锁

## §5 架构分析

### 5.1 整体架构

n8n 采用典型的前后分离架构：

```
┌─────────────────────────────────────────┐
│            n8n Editor (前端)              │
│  React + Vue-based 可视化编辑器          │
│  WebSocket 实时通信                      │
└──────────────┬──────────────────────────┘
               │ REST API / WebSocket
┌──────────────┴──────────────────────────┐
│           n8n Server (后端)              │
│  Node.js + Express                      │
│  Workflow Engine                       │
│  Node Loader                           │
│  Credential Manager                    │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───┴──────┐      ┌──────┴──────┐
│ SQLite /  │      │ Executions  │
│ Postgres │      │ Queue (Redis)│
└──────────┘      └─────────────┘
```

**Editor UI**：基于 Vue.js 构建的可视化编辑器，提供节点拖拽、连接绘制、配置面板、执行日志查看等功能。通过 REST API 与后端通信，并通过 WebSocket 实时推送执行状态。

**Server**：基于 Node.js + Express 构建的核心服务，负责：
- 工作流的创建、存储和版本管理
- 节点的注册与动态加载
- 执行引擎的调度
- Credential（凭证）的加密存储与分发
- Webhook 接收与分发

### 5.2 节点架构

n8n 的节点体系是其最大特色。每个节点是一个独立的 NPM 包，符合统一的接口规范：

```typescript
// 节点接口核心定义（简化版）
interface INode {
  // 节点类型标识（命名空间/节点名）
  type: string;

  // 节点显示名称
  displayName: string;

  // 节点属性定义（用于前端渲染配置面板）
  properties: INodeProperties[];

  // 节点执行逻辑
  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[]>;
}
```

n8n 的节点按功能可分为几大类：

- **Trigger Nodes**：无输入端口，作为工作流起点（Webhook Trigger、Cron Trigger、Email Trigger 等）
- **Regular Nodes**：有输入和输出端口，承接并转发数据（Transform、HTTP Request 等）
- **AI Nodes**：基于 LangChain 的 AI 相关节点（AI Agent、Chain、Memory 等）

官方维护的 400+ 节点位于 `packages/nodes-base`，每个节点是一个独立目录，包含 TypeScript 源码和测试文件。

### 5.3 Credential 机制

Credential 是 n8n 安全模型的核心。每个需要认证的节点（数据库、API 密钥等）使用 Credential 对象存储敏感信息。Credential 的关键设计：

1. **加密存储**：Credential 在存入数据库前使用 `N8N_ENCRYPTION_KEY` AES-256-GCM 加密
2. **按需分发**：工作流执行时，引擎解密 Credential 并仅传递给需要它的节点，执行后立即清除内存副本
3. **独立权限**：Credential 与工作流分离，同一个 Credential 可以被多个工作流共享，但需要分别授权
4. **用户绑定**：Personal Credential 只能被创建者使用，Share Credential 可在团队内共享

### 5.4 执行引擎的设计哲学

n8n 的执行引擎是理解其能力边界的关键。它的设计哲学是"图优先、节点独立"：

- **图优先**：工作流是一个有向无环图，引擎的任务是正确遍历这张图
- **节点独立**：每个节点自己负责读取输入、执行逻辑、产生输出，引擎不介入节点内部逻辑
- **异步非阻塞**：Node.js 的异步 I/O 模型天然适合 I/O 密集型的自动化工作流
- **可恢复**：启用 SQLite/PostgreSQL 作为执行历史存储时，引擎支持从中间节点恢复执行（需要工作流开启 "Save Execution Progress"）

### 5.5 高可用与多实例部署

在生产环境中，n8n 支持多实例部署以实现高可用：

```
                    ┌─────────────┐
   Clients ──────▶  │ Load Balancer│
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌────────┐   ┌────────┐   ┌────────┐
         │  n8n   │   │  n8n   │   │  n8n   │
         │ Node 1 │   │ Node 2 │   │ Node 3 │
         └────┬───┘   └────┬───┘   └────┬───┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────┴──────┐
                    │ PostgreSQL  │
                    └─────────────┘
```

当使用 PostgreSQL 作为数据库时，多个 n8n 实例可以共享同一份工作流定义和 Credential，实现水平扩展。但需要注意：

- **Webhook 负载均衡**：Webhook 通过 HTTP 请求触发，天然支持无状态分发
- **执行锁**：并发执行同一工作流时，PostgreSQL 行锁防止数据竞争
- **Redis Queue 模式**：启用 `EXECUTIONS_MODE=queue` 时，执行任务进入 Redis 队列，多个 Worker 实例竞争获取任务，实现真正的分布式执行

## §6 实战演示

### 6.1 工作流设计：从需求到节点图

我们用一个具体场景串联整个流程：**每日自动抓取 GitHub Trending 页面，将 Python 项目汇总为 Markdown 报告，发送邮件给团队**。

工作流设计思路：

1. **Cron Trigger**：每天上午 9:00 触发（`0 9 * * *`）
2. **HTTP Request**：GET GitHub Trending 页面（`https://github.com/trending/python`）
3. **HTML Extract**：从页面中提取项目名称、Star 数、描述
4. **Transform**：过滤出 Star 数 > 500 的项目，格式化为 Markdown 表格
5. **Email Send**：将报告发送到团队邮箱

### 6.2 可视化编辑器使用

启动 n8n 后访问 `http://localhost:5678`，按以下步骤操作：

**Step 1：创建工作流**

点击左侧 "+" 新建工作流，自动进入空白编辑器。

**Step 2：添加触发节点**

在节点列表中搜索 "Schedule Trigger"（在 v1.x 中已更名为 "Schedule Trigger"），拖入画布。配置 cron 表达式：

```
Expression: 0 9 * * *
```

这表示每天 9:00 触发。

**Step 3：添加 HTTP Request 节点**

添加 "HTTP Request" 节点，配置：

```
Method: GET
URL: https://github.com/trending/python
```

**Step 4：HTML 提取数据**

n8n 的 HTML Extract 节点使用 CSS 选择器提取页面内容。对于 GitHub Trending 页面，我们可以：

1. 设置 "Property Output" 为 "JSON"
2. 添加提取规则：

| CSS 选择器 | 字段名 | 数据类型 |
|---|---|---|
| `article h2 a` | `name` | String |
| `.Link--muted` | `description` | String |
| `.d-inline-block span` | `stars` | Number |

实际使用中，GitHub 页面结构复杂，建议使用 "HTTP Request" 获取原始 HTML 后，再用 "Code" 节点（JavaScript）配合 `cheerio` 库解析：

```javascript
// Code 节点（Run Once for All Items）
const cheerio = require('cheerio');
const items = [];

for (const item of $input.all()) {
  const html = item.json.body;
  const $ = cheerio.load(html);

  $('article').each((_, el) => {
    const name = $(el).find('h2 a').text().trim().replace(/\s+/g, '/');
    const desc = $(el).find('p').text().trim();
    const stars = parseInt($(el).find('.d-inline-block span').text().trim().replace(/,/g, ''), 10) || 0;

    if (stars >= 500) {
      items.push({
        name,
        description: desc,
        stars
      });
    }
  });
}

return items.map(item => ({ json: item }));
```

**Step 5：格式化 Markdown 表格**

添加 "Code" 节点，将数组转换为 Markdown 表格：

```javascript
// Code 节点（Run Once for All Items）
const items = $input.all().map(item => item.json);
items.sort((a, b) => b.stars - a.stars);

const lines = ['## GitHub Python Trending（Star ≥ 500）', '', '| 项目 | 描述 | Stars |', '| --- | --- | --- |'];
for (const item of items) {
  lines.push(`| [${item.name}](https://github.com/${item.name}) | ${item.description} | ${item.stars} |`);
}

return [{ json: { report: lines.join('\n') } }];
```

**Step 6：发送邮件**

添加 "Email Send" 节点，配置 SMTP 凭证后设置：

```
From: n8n@your-team.com
To: team@your-team.com
Subject: GitHub Python Trending Report - {{ $today }}
Body: {{ $json.report }}
```

**最终节点图**：

```
[Schedule Trigger] ──▶ [HTTP Request] ──▶ [Code: Parse HTML] ──▶ [Code: Format MD] ──▶ [Email Send]
```

### 6.3 AI Agent 工作流示例

n8n 的 AI 能力是这个平台的亮点之一。我们构建一个 "Slack 消息 → AI 分析 → 回复" 的 Agent 工作流：

**工作流设计**：

1. **Slack Trigger**：监听频道消息
2. **AI Agent**：调用 Claude/GPT 分析消息意图
3. **Condition**：判断意图类型（问题/请求/闲聊）
4. **AI Agent / Function Call**：执行对应动作（查数据库/发通知/回复）

**AI Agent 节点配置**：

```
Model: anthropic
Model Name: claude-3-5-sonnet-latest
System Message: |
  你是一个技术支持助手。当用户提问时，先判断是否需要查询知识库。
  如果需要查询，使用知识库搜索工具。
  如果是闲聊，直接回答。
  如果是投诉或紧急问题，立即标记并通知值班人员。
Tools:
  - Wikipedia Search
  - Calculator
```

**Function Calling 实现**：

在 "Code" 节点中注册工具：

```javascript
// AI Agent 的 Tool 定义
const tools = [
  {
    name: 'search_knowledge_base',
    description: '在内部知识库中搜索相关文档',
    parameters: {
      type: 'object',
      properties: {
        query: { type: 'string', description: '搜索关键词' }
      },
      required: ['query']
    }
  },
  {
    name: 'notify_oncall',
    description: '通知值班人员处理紧急问题',
    parameters: {
      type: 'object',
      properties: {
        message: { type: 'string' },
        severity: { type: 'string', enum: ['normal', 'urgent', 'critical'] }
      },
      required: ['message', 'severity']
    }
  }
];
```

### 6.4 错误处理与重试机制

n8n 提供了多层次错误处理机制：

**节点级重试**：在节点配置中开启 "Retry On Fail"，设置重试次数和间隔：

```
Retry On Fail: true
Max Retries: 3
Retry Interval: 5 seconds
```

**工作流级错误处理**：使用 "Error Trigger" 节点捕获整个工作流的异常：

```
[Main Workflow]
     │
     ▼
[Error Trigger] ──▶ [Notify Error via Slack] ──▶ [Log to Database]
```

**条件路由**：使用 "IF" 节点配合表达式做分支：

```
Expression: {{ JSON.parse($json.error).code === 'RATE_LIMIT' }}
├── True:  [Wait 60s] ──▶ [Retry Original]
└── False: [Notify via Email]
```

## §7 开发扩展

### 7.1 自定义节点开发

n8n 支持通过创建自定义节点扩展平台功能。自定义节点本质上是一个符合接口规范的 NPM 包。

**项目结构**：

```
my-custom-nodes/
├── package.json
├── tsconfig.json
├── nodes/
│   └── MyCustomNode/
│       ├── MyCustomNode.node.ts       # 节点主文件
│       └── MyCustomNode Trigger/
│           └── MyCustomNodeTrigger.node.ts  # 触发器节点
└── credentials/
    └── MyCustomApi/
        └── MyCustomApi.credentials.ts  # 凭证定义
```

**节点文件示例**（使用 n8n 的 TypeScript 类型系统）：

```typescript
import {
  IExecuteFunctions,
  INodeExecutionData,
  INodeType,
  INodeTypeDescription,
} from 'n8n-workflow';

export class GitHubRepoStats implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'GitHub 仓库统计',
    name: 'githubRepoStats',
    group: ['input'],
    version: 1,
    subtitle: '获取仓库统计数据',
    defaults: { name: 'GitHub 仓库统计' },
    inputs: ['main'],
    outputs: ['main'],
    properties: [
      {
        displayName: '仓库路径',
        name: 'repo',
        type: 'string',
        required: true,
        default: 'owner/repo',
        description: '格式：owner/repo，如 n8n-io/n8n',
      },
      {
        displayName: 'API Token',
        name: 'apiToken',
        type: 'string',
        typeOptions: { password: true },
        required: true,
        default: '',
        description: 'GitHub Personal Access Token',
      },
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    const items = this.getInputData();
    const returnData: INodeExecutionData[] = [];

    for (let i = 0; i < items.length; i++) {
      const repo = this.getNodeParameter('repo', i) as string;
      const apiToken = this.getNodeParameter('apiToken', i) as string;

      const response = await this.helpers.httpRequest({
        method: 'GET',
        url: `https://api.github.com/repos/${repo}`,
        headers: {
          Authorization: `Bearer ${apiToken}`,
          Accept: 'application/vnd.github.v3+json',
          'X-GitHub-Api-Version': '2022-11-28',
        },
      });

      returnData.push({
        json: {
          name: response.full_name,
          stars: response.stargazers_count,
          forks: response.forks_count,
          openIssues: response.open_issues_count,
          language: response.language,
          description: response.description,
          createdAt: response.created_at,
          updatedAt: response.updated_at,
          url: response.html_url,
        },
      });
    }

    return this.prepareOutputData(returnData);
  }
}
```

**凭证文件示例**：

```typescript
import {
  ICredentialType,
  INodePropertyTypes,
  INodePropertyOption,
} from 'n8n-workflow';

export class GitHubApi implements ICredentialType {
  name = 'githubApi';
  displayName = 'GitHub API';
  documentationUrl = 'https://docs.github.com/en/authentication';
  properties = [
    {
      displayName: 'Personal Access Token',
      name: 'apiKey',
      type: 'string',
      typeOptions: { password: true },
      default: '',
    },
  ];
}
```

**package.json**：

```json
{
  "name": "n8n-nodes-github-stats",
  "version": "1.0.0",
  "description": "GitHub 仓库统计节点",
  "keywords": ["n8n-nodes"],
  "license": "MIT",
  "n8n": {
    "nodes": ["dist/nodes/MyCustomNode/MyCustomNode.node.js"]
  },
  "dependencies": {
    "n8n-core": "^1.0.0"
  }
}
```

### 7.2 节点本地加载与调试

创建自定义节点后，需要在 n8n 中注册和加载：

**方式一：节点加载目录（开发调试用）**

在 n8n 配置文件中指定自定义节点目录：

```bash
# 启动 n8n 并指定节点目录
n8n --customNodesDir /path/to/my-custom-nodes/dist/nodes
```

**方式二：安装为全局 NPM 包**

```bash
cd /path/to/my-custom-nodes
npm link
cd ~/path/to/project
npm link n8n-nodes-github-stats
n8n
```

**调试技巧**：

1. 使用 `console.log` 输出中间变量，查看 n8n 服务日志
2. 开启 DEBUG 模式：`N8N_LOG_LEVEL=debug n8n`
3. 在 "Code" 节点中使用 `$json` 和 `$input` 打印数据结构
4. 使用 `this.helpers.httpRequestWithAuthentication` 简化认证请求

### 7.3 工作流模板与复用

n8n 支持将工作流导出为 JSON 模板，便于团队复用和分发：

**导出模板**：在编辑器中点击 "Workflow Settings" → "Export Template"

**导入模板**：点击 "Import from JSON" 按钮加载

**版本管理**：建议将工作流 JSON 文件存入 Git 管理，配合 CI/CD 实现工作流的 "基础设施即代码" 管理。

### 7.4 生产环境最佳实践

**监控与告警**：

- 配置 Prometheus + Grafana 监控 n8n 指标
- 监控工作流执行成功率、执行时长、错误率
- 关键工作流失败时发送 Slack/PagerDuty 告警

**备份策略**：

- PostgreSQL 定期全量 + 增量备份
- n8n 配置目录（`~/.n8n`）纳入备份范围
- 测试备份恢复流程

**安全加固**：

- `N8N_ENCRYPTION_KEY` 使用 32 位随机字符串，不低于 20 字符
- 外部数据库（PostgreSQL）禁止公网访问，使用内网或 VPN 连接
- API 端点启用 HTTPS，关闭 HTTP 回退
- Credential 定期轮换，GitHub Token 等设置过期时间

**性能调优**：

- 大量并发执行时启用 Redis Queue 模式（`EXECUTIONS_MODE=queue`）
- HTTP Request 节点配置合理的超时时间（建议 30s）
- 避免工作流中长时间运行的同步循环，改为异步分片
- 定期清理执行历史（SQLite `execution_entity` 表膨胀）

## §8 进阶学习路径

完成本文后，可以继续探索以下方向：

- **AI 应用深化**：结合向量数据库（如 Pinecone、Qdrant）构建 RAG 工作流，实现私有知识库问答
- **事件驱动架构**：使用 n8n 作为 GitHub Actions、AWS EventBridge 的处理层，实现云事件路由
- **多租户 SaaS**：基于 n8n 企业版构建面向客户的自动化服务平台
- **节点源码研究**：阅读 `packages/nodes-base` 源码，学习官方节点的实现模式
- **LangChain 集成进阶**：使用 LangChain 的 Tool、Agent、Memory 组件构建复杂 AI Agent

## 参考资源

- [n8n 官方文档](https://docs.n8n.io)
- [n8n GitHub 仓库](https://github.com/n8n-io/n8n)
- [n8n 社区工作流模板](https://n8n.io/workflows)
- [n8n AI & LangChain 指南](https://docs.n8n.io/advanced-ai/)
- [n8n 社区论坛](https://community.n8n.io)
