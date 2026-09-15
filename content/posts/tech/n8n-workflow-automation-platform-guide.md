---
title: "n8n 深度解读：可自托管的工作流自动化与 AI Agent 平台"
date: "2026-05-02T10:12:00+08:00"
lastmod: 2026-09-13T09:30:00+08:00
slug: n8n-workflow-automation-platform-guide
github_repo: "n8n-io/n8n"
source_key: "gh:n8n-io/n8n"
summary: "n8n 是一款采用 fair-code 模式发布的工作流自动化平台，官方提供 500+ 集成节点与原生 AI Agent 能力。涵盖执行模型、架构设计、Docker 与 npm 部署、可视化编辑器实战、自定义节点开发与生产环境落地建议。"
description: "n8n 的执行模型、节点架构、凭证加密、queue 模式扩展，以及 Docker/npm 安装配置、可视化编辑器实战、社区节点开发与生产环境部署建议。"
draft: false
categories: ["技术笔记"]
tags: ["n8n", "工作流自动化", "TypeScript", "AI Agent", "无代码", "LangChain", "Docker"]
---

> **目标读者**：希望搭建自动化工作流、或将 n8n 作为 AI Agent 执行引擎的后端工程师与全栈开发者。
> **核心问题**：n8n 与 Zapier/Make 有何本质差异？为什么它适合自托管？它如何执行一条工作流？自定义节点怎么写？
> **事实边界**：本文基于 n8n 官方文档与 GitHub 仓库（n8n 2.x，写作时最新版本为 2.39）整理；代码示例基于自托管开源版本，企业版特有功能单独标注。

n8n 真正解决的问题不是"没有代码能不能做自动化"——Zapier 已经回答过这个问题——而是"自动化的数据和控制权能不能留在自己手里"。工作流定义、执行历史、凭证全部存本地数据库，代码可以随时插进节点图里，这是它与 SaaS 自动化平台的分界线。

## 阅读导航

- 只想快速跑起来：直接看 §4 安装配置
- 想理解执行模型：先看 §3 核心概念与执行模型
- 想了解完整架构：看 §5 架构分析
- 想动手写个工作流：看 §6 实战演示
- 想写自己的节点：看 §7 开发扩展

## §1 学习目标

完成本文后，你可以：

- 理解 n8n 的节点图执行模型与数据流机制
- 掌握 Docker 与 npm 两种安装方式的差异与适用场景
- 使用可视化编辑器构建包含条件分支、AI 调用和数据转换的工作流
- 将 n8n 自托管部署到生产环境，配置反向代理、HTTPS 与外部数据库
- 理解 n8n 的 Credential 机制与 queue 模式扩展方案
- 基于 n8n-workflow 类型包编写并安装社区节点

## §2 为什么是 n8n

在 n8n 出现之前，工作流自动化领域被 Zapier 和 Make（原 Integromat）主导。这两个平台都是 SaaS 模式——你的工作流跑在他们的云上，数据经过他们的服务器。如果你的场景有下面任何一条约束，SaaS 方案就开始变得别扭：

- **数据不能出内网**：金融数据、医疗记录、用户隐私不经过第三方服务器
- **自定义逻辑多**：平台自带的条件/循环不够用，需要写 JavaScript 或 Python
- **成本可控**：SaaS 按任务数计费，任务量大时自托管反而划算
- **要改平台本身**：需要修改自动化工具的行为，而不是迁就它

n8n 填补的正是这个位置。它与传统 SaaS 平台的关键差异：

| 维度 | Zapier / Make | n8n |
|---|---|---|
| 部署方式 | 仅云端 | 云端服务或自托管（支持气隙部署） |
| 代码能力 | 受限的 Code 步骤 | Code 节点运行 JavaScript/Python |
| 应用集成 | Zapier 官网宣称 9,000+ | 官方 500+，社区节点可继续扩展 |
| 许可证 | 专有 | Sustainable Use License（fair-code） |
| AI 能力 | 有限 | 内置 AI Agent 节点，基于 LangChain |
| 扩展方式 | 官方维护 | 可自建社区节点（npm 包） |

许可证值得单独说明。n8n 采用 Sustainable Use License，不属于 OSI 认证开源，官方将其归类为 fair-code：源码公开，**内部业务使用完全免费**，包括商用公司的内部自动化；但**不得将 n8n 本身收费分发或包装成竞品服务**，使用源码中以 `.ee` 标记的企业版功能（SSO、RBAC、环境等）需要购买 Enterprise License。多数"自托管自动化"场景落在免费范围内，部署前确认自己的用法不越界即可。

## §3 核心概念与执行模型

### 3.1 节点、连接与工作流

n8n 的数据模型只有三个概念：

**节点（Node）** 是基本计算单元。每个节点做一件事：读取数据、转换数据、发送数据或执行动作。官方维护的节点集中在仓库的 `packages/nodes-base` 目录，覆盖 HTTP 请求、数据库操作、消息推送、文件处理、AI 模型调用等场景；社区节点则以独立 npm 包的形式补充长尾应用。

**连接（Connection）** 是节点之间的有向数据通道。数据从上游节点的输出端口流向下游节点的输入端口，构成有向图。一个节点可以有多个输入和输出端口，支持多路汇聚与分发（IF 分支、Merge 合并）。

**工作流（Workflow）** 是节点与连接构成的完整自动化逻辑单元。每个工作流由一个触发器节点（Trigger）起步，当特定事件发生时触发整条链的执行。

### 3.2 触发方式：拉与推

触发器决定工作流何时启动，n8n 支持两类：

**轮询触发**：节点按固定间隔主动拉取数据，例如 Schedule Trigger 按 cron 规则定时触发（它的工作方式与 Unix cron 工具类似）。

**事件触发**：节点等待外部事件被动接收数据，例如 Webhook 节点等待 HTTP 请求到达，RabbitMQ 节点等待队列消息。

无论数据来自轮询还是事件，进入工作流之后都经过同一套转换、路由和输出节点，两条路径在节点图层面没有区别。

有一个 n8n 2.0 之后的实操细节容易踩坑：触发型工作流必须**保存并发布（Publish）**才会生效。2.0 用发布/取消发布（Publish/Unpublish）取代了原来的激活/停用开关，改动只有在发布后才上线，避免把调试中的版本误部署到生产。

### 3.3 数据流：JSON 主体加二进制附件

n8n 内部用 JSON 表示结构化数据。每个节点接收一组条目（item，每个 item 是一个 JSON 对象），处理后再输出新的条目。条目除了 `json` 主数据外，还可以挂一个 `binary` 对象存放二进制引用——文件、图片、音频走这条通道。

这样的组合允许节点自由拼接：HTTP 节点拉取一份文件，HTML 节点提取内容，Code 节点清洗数据，数据库节点写回 PostgreSQL。结构化数据与二进制数据可以在同一条工作流里交替转换。

### 3.4 一次执行的完整过程

一条工作流被触发后，执行引擎做的事情可以概括为：

1. 把工作流的节点和连接实例化为可执行对象
2. 从触发节点开始，沿连接逐个执行下游节点；多条分支按工作流的执行顺序设置依次处理
3. 上游节点的输出自动作为下游节点的输入，每个节点的执行结果记入执行历史
4. 节点失败时，按节点配置决定重试，按工作流配置决定停止还是继续

n8n 运行在 Node.js 上，I/O 密集型任务（网络请求、数据库查询）天然能并发处理。如果工作流设置了 "Save execution progress"，每个节点的执行数据会单独保存，出错后可以从停止的节点恢复执行——代价是执行延迟增加，官方文档对此有明确提示。

### 3.5 AI 能力：LangChain 集成

n8n 在 2023 年引入了基于 LangChain 的原生 AI 节点，此后持续加码，官网现在的定位就是"AI agents and workflows"。可在编辑器里直接组合：

- **AI Agent 节点**：能调用工具的 Agent。自 n8n 1.82 起统一以 Tools Agent 方式运行（需要模型支持工具调用），v1 版本的旧 Agent 类型计划在 3.0 移除
- **Chain 节点**：问答、摘要等链式调用
- **Memory 子节点**：为会话维护上下文，支持多轮对话
- **Embedding 与 Vector Store 节点**：文本向量化与向量检索，用于 RAG 场景

AI 节点是节点图中的普通节点：Agent 的输出可以继续连接数据库、邮件、IM 节点，一条工作流里也可以放多个 Agent。

## §4 安装配置

n8n 支持两种自托管安装方式，外加官方云服务。生产环境以 Docker 为准。

### 4.1 Docker 安装（推荐）

**本地快速试用**：

```bash
# 创建持久化存储卷
docker volume create n8n_data

# 启动 n8n
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  docker.n8n.io/n8nio/n8n
```

访问 `http://localhost:5678` 即可打开可视化编辑器。

**带 PostgreSQL 的生产部署**：

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
  -e N8N_ENCRYPTION_KEY=your-long-random-secret \
  -v n8n_data:/home/node/.n8n \
  --restart unless-stopped \
  docker.n8n.io/n8nio/n8n
```

`N8N_ENCRYPTION_KEY` 用于加密数据库中的凭证，首次启动时 n8n 会自动生成一个随机密钥写入 `~/.n8n/config`。自托管多实例或使用 queue 模式时必须显式设置，并保证所有实例（worker、webhook 处理器）使用同一把密钥——丢了这把钥匙，数据库里的凭证将无法解密。

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

### 4.2 npm 安装

适合开发者本地快速体验，或没有 Docker 环境的机器。注意两点：当前 n8n 要求 Node.js 版本在 20.19 至 24.x 之间；官方已宣布 npm 安装方式自 n8n 3.0 起弃用，新项目优先用 Docker。

不想安装可以直接用 npx 试用：

```bash
npx n8n
```

或全局安装：

```bash
npm install -g n8n

# 启动
n8n
# 或指定端口
n8n --port 5679
```

带外部数据库时，通过环境变量传入配置：

```bash
export DB_TYPE=postgresdb
export DB_POSTGRESDB_HOST=localhost
export DB_POSTGRESDB_PORT=5432
export DB_POSTGRESDB_DATABASE=n8n
export DB_POSTGRESDB_USER=n8n
export DB_POSTGRESDB_PASSWORD=secret
export N8N_ENCRYPTION_KEY=your-long-random-secret
export WEBHOOK_URL=https://n8n.your-domain.com
n8n
```

### 4.3 环境变量速查表

| 变量 | 说明 | 示例 / 默认值 |
|---|---|---|
| `N8N_HOST` | n8n 运行的主机名 | `localhost` |
| `N8N_PORT` | HTTP 端口 | `5678` |
| `N8N_PROTOCOL` | 协议类型 | `http` / `https` |
| `WEBHOOK_URL` | Webhook 对外基础 URL | `https://n8n.example.com` |
| `DB_TYPE` | 数据库类型 | `sqlite`（默认）/ `postgresdb` |
| `DB_POSTGRESDB_HOST` | PostgreSQL 主机 | `10.0.1.5` |
| `DB_POSTGRESDB_PORT` | PostgreSQL 端口 | `5432` |
| `DB_POSTGRESDB_DATABASE` | 数据库名 | `n8n` |
| `DB_POSTGRESDB_USER` | 数据库用户 | `n8n` |
| `DB_POSTGRESDB_PASSWORD` | 数据库密码 | `***` |
| `N8N_ENCRYPTION_KEY` | 凭证加密密钥 | 首次启动自动生成 |
| `GENERIC_TIMEZONE` | 实例时区 | `Asia/Shanghai` |
| `EXECUTIONS_MODE` | 执行模式 | `regular`（默认）/ `queue` |
| `EXECUTIONS_DATA_PRUNE` | 自动清理历史执行数据 | `true`（默认） |
| `EXECUTIONS_DATA_MAX_AGE` | 执行数据保留时长（小时） | `336`（14 天） |
| `EXECUTIONS_DATA_PRUNE_MAX_COUNT` | 最多保留的执行条数 | `10000` |
| `N8N_LOG_LEVEL` | 日志级别 | `info` / `debug` |

时区值得多说一句：`GENERIC_TIMEZONE` 决定 Schedule Trigger 的定时基准，默认时区是 `America/New_York`。中文用户部署后第一件事通常就是把它改成 `Asia/Shanghai`，否则定时任务会按纽约时间跑。工作流级别也可以单独设置时区，优先级高于实例设置。

### 4.4 反向代理配置（Nginx）

生产环境通常用 Nginx 反向代理并提供 HTTPS：

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

        # 编辑器与服务端之间的实时推送连接
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时配置
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

同时记得把 `N8N_HOST`、`N8N_PROTOCOL=https` 和 `WEBHOOK_URL` 指向对外域名，Webhook 回调地址才能拼对。

### 4.5 SQLite 还是 PostgreSQL

默认数据库是嵌入式 SQLite，个人使用和中小团队够用。出现以下情况时切换到 PostgreSQL：

- **多实例部署**：多实例必须共享状态（见 §5.5，queue 模式强制要求 PostgreSQL）
- **数据量大**：工作流和执行记录持续累积后，SQLite 的写并发受单写锁限制
- **备份要求高**：PostgreSQL 的备份与恢复机制更成熟

## §5 架构分析

### 5.1 整体架构

n8n 采用前后端分离的单体架构：

```
┌─────────────────────────────────────────┐
│            n8n Editor (前端)             │
│  Vue 3 + Pinia 可视化编辑器              │
│  实时推送（执行状态更新）                 │
└──────────────┬──────────────────────────┘
               │ REST API / 推送连接
┌──────────────┴──────────────────────────┐
│           n8n Server (后端)              │
│  Node.js + Express                      │
│  Workflow Engine                        │
│  Node Loader（节点注册与加载）           │
│  Credential Manager（凭证管理）         │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───┴──────┐      ┌──────┴───────┐
│ SQLite / │      │ Executions   │
│ Postgres │      │ Queue (Redis)│
└──────────┘      └──────────────┘
```

**Editor UI** 是一个 Vue 3 单页应用（状态管理用 Pinia），负责画布、节点配置面板、执行日志展示，通过 REST API 与后端通信。

**Server** 是核心服务，承担：工作流的存储与版本管理、节点的注册与动态加载、执行引擎调度、凭证的加密存取、Webhook 的接收与分发。

### 5.2 节点架构

节点是 n8n 的扩展单元。官方的几百个节点都住在 `packages/nodes-base` 这一个包里，每个节点一个目录；社区节点则是独立的 npm 包，安装后由 n8n 动态加载。两者遵循同一套接口规范：

```typescript
// 节点接口的关键部分（摘自 n8n-workflow 包）
interface INodeType {
  description: INodeTypeDescription;

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]>;
}
```

`description` 声明节点的名称、图标、输入输出口和属性表——前端根据它渲染配置面板；`execute` 是节点被调用时执行的函数，返回二维数组：外层对应输出口，内层是该口输出的条目。

节点按功能分三类：

- **Trigger Nodes**：没有输入口，作为工作流起点（Webhook、Schedule、Email 等触发器）
- **Regular Nodes**：有输入输出口，承接并转发数据（HTTP Request、Edit Fields/Set 等）
- **Cluster Nodes**：AI 相关节点，由根节点（如 AI Agent）和子节点（Chat Model、Memory、Tool）组成，见 §6.3

### 5.3 Credential 机制

Credential 是 n8n 安全模型的核心。需要认证的节点（数据库连接、API 密钥）不直接接触明文密钥，而是引用一个 Credential 对象：

1. **加密存储**：凭证数据在写入数据库前用 `N8N_ENCRYPTION_KEY` 做 AES-256 对称加密（数据走 CBC，新版的密钥信封走 GCM），密钥本身不进数据库
2. **按需解密**：工作流执行时引擎解密凭证，只交给声明引用它的节点
3. **与工作流分离**：一个凭证可被多个工作流共享，凭证的生命周期独立管理
4. **权限分层**：凭证可以属于创建者个人，也可以共享给项目/团队

### 5.4 执行引擎的取舍

引擎的边界由几条设计决定：

- **图遍历，不解释节点**：引擎只负责沿连接调度和传递数据，节点内部逻辑对引擎透明
- **Node.js 异步 I/O**：自动化工作流大多在等网络和数据库，异步模型正好匹配
- **执行历史落库**：每次执行的输入输出可以完整保存，配合 "Save execution progress" 还能从出错节点恢复；生产环境要搭配 §4.3 的 prune 配置控制体量
- **错误分层**：节点级重试（§6.4）与工作流级 Error Workflow 各管一层，互不替代

### 5.5 水平扩展：queue 模式

普通模式（`EXECUTIONS_MODE=regular`）只支持单个主实例。要水平扩展，n8n 的官方答案是 queue 模式：

```
                    ┌─────────────┐
   Clients ──────▶  │Load Balancer│
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌────────┐   ┌────────┐   ┌────────┐
         │  n8n   │   │ Worker │   │ Worker │
         │  main  │   │   1    │   │   2    │
         └────┬───┘   └────┬───┘   └────┬───┘
              │            │            │
              └─────┬──────┴────────────┘
                    │
         ┌──────────┼───────────┐
         ▼          ▼           ▼
    ┌────────┐ ┌────────┐ ┌──────────┐
    │Postgres│ │ Redis  │ │ Webhook  │
    │  (DB)  │ │ (Queue)│ │Processor │
    └────────┘ └────────┘ └──────────┘
```

流程是：main 实例处理定时器和 Webhook 调用，生成执行任务但不执行，把执行 ID 推进 Redis 队列；空闲的 worker 从队列取任务，用 ID 从数据库读出工作流定义并执行，完成后把结果写回数据库、通知 Redis，Redis 再通知 main。扩容就是加 worker。

三个部署注意点：

- **数据库共享**：所有实例必须使用同一个 PostgreSQL（queue 模式不支持 SQLite）和同一把 `N8N_ENCRYPTION_KEY`，worker 才能解密凭证
- **二进制数据**：queue 模式不支持本地文件系统存储二进制数据，需要持久化时接 S3 外部存储
- **社区节点**：queue 模式下无法用界面安装社区节点，要在每个实例上手动安装（见 §7.1）

## §6 实战演示

### 6.1 工作流设计：从需求到节点图

用一个具体场景串起整条链路：**每天上午 9 点抓取 GitHub Trending 的 Python 区页面，汇总为 Markdown 报告，邮件发给团队**。

节点图设计：

1. **Schedule Trigger**：每天 9:00 触发
2. **HTTP Request**：GET `https://github.com/trending/python`
3. **HTML**：从页面提取项目名称、描述、Star 数
4. **Code**：过滤 Star 数并格式化为 Markdown 表格
5. **Send Email**：把报告发到团队邮箱

### 6.2 在编辑器里搭出来

启动 n8n 后访问 `http://localhost:5678`，按以下步骤操作。

**Step 1：新建工作流**

点击画布上的 "+" 创建工作流。

**Step 2：添加 Schedule Trigger**

搜索 "Schedule Trigger" 节点（前身是 Cron 节点），触发间隔选 Days，触发时间设为 9:00。定时任务依赖时区——实例没配 `GENERIC_TIMEZONE` 的话，在工作流设置里单独指定。

注意：触发型工作流要**发布**之后才会按计划运行，光保存不够。

**Step 3：添加 HTTP Request 节点**

```
Method: GET
URL: https://github.com/trending/python
Response Format: String
```

Response Format 必须选 String——GitHub 返回的是 HTML，默认的 JSON 解析会直接报错。响应内容会出现在下游节点的 `$json.data` 字段。

**Step 4：用 HTML 节点提取内容**

HTML 节点（n8n 0.213 起取代旧的 HTML Extract 节点）选 "Extract HTML content" 操作：

```
Source Data: JSON
JSON Property: data
Extraction Values:
  - CSS 选择器: article h2 a        → 字段 name
  - CSS 选择器: article p           → 字段 description
  - CSS 选择器: article .d-inline-block float-sm-right → 字段 stars
```

CSS 选择器依赖 GitHub 当时的页面结构，页面改版后需要同步调整。要更复杂的解析逻辑，可以在 Code 节点里用 cheerio 处理——自托管实例需要先放行外部模块（`NODE_FUNCTION_ALLOW_EXTERNAL=cheerio`），n8n Cloud 不允许导入外部 npm 包。

**Step 5：Code 节点格式化报告**

添加 Code 节点，语言 JavaScript，运行模式 "Run Once for All Items"。这段代码只用内置能力，不需要任何外部依赖：

```javascript
const items = $input.all().map(item => item.json);

const repos = items
  .map(({ name, description, stars }) => ({
    name: (name || '').trim(),
    description: (description || '').trim(),
    stars: parseInt((stars || '0').replace(/[,\s]/g, ''), 10),
  }))
  .filter(r => r.name && r.stars >= 500)
  .sort((a, b) => b.stars - a.stars);

const lines = [
  '## GitHub Python Trending（Star ≥ 500）', '',
  '| 项目 | 描述 | Stars |',
  '| --- | --- | --- |',
];
for (const r of repos) {
  lines.push(`| [${r.name}](https://github.com/${r.name}) | ${r.description} | ${r.stars} |`);
}

return [{ json: { report: lines.join('\n') } }];
```

**Step 6：Send Email 发送报告**

添加 Send Email 节点（SMTP），先创建 SMTP 凭证，然后：

```
From: n8n@your-team.com
To: team@your-team.com
Subject: GitHub Python Trending Report - {{ $today.toFormat('yyyy-MM-dd') }}
Body: {{ $json.report }}
```

最终节点图：

```
[Schedule Trigger] ──▶ [HTTP Request] ──▶ [HTML: Extract] ──▶ [Code: Format] ──▶ [Send Email]
```

点击 "Execute Workflow" 手动跑一遍，在右侧执行面板检查每个节点的输入输出，确认无误后发布。

### 6.3 AI Agent 工作流

n8n 的 AI 节点采用"根节点 + 子节点"的 Cluster Node 结构：AI Agent 是根节点，模型、记忆、工具都是连接到它的子节点。Agent 根据系统提示词决定调用哪个工具，工具的输出回到 Agent 继续推理。

一个"Slack 技术支持助手"的节点图：

```
[Slack Trigger]
       │
       ▼
[AI Agent] ── [Anthropic Chat Model]   （子节点：模型）
       ├── [Simple Memory]              （子节点：会话上下文）
       ├── [HTTP Request Tool]          （子节点：工具：知识库检索）
       └── [Call n8n Workflow Tool]     （子节点：工具：通知值班人员）
       │
       ▼
[Slack: Send Reply]
```

配置要点：

- **AI Agent 节点**里写 System Message，约定角色与行为边界：

```
你是一个技术支持助手。用户提问时，先用知识库检索工具查相关文档；
查不到再直接回答。遇到投诉或紧急问题，调用通知工具上报值班人员。
```

- **Chat Model 子节点**选 Anthropic Chat Model（或 OpenAI 等其他供应商节点），填入 API 凭证并选择模型。Agent 需要支持工具调用的模型
- **工具子节点**用 n8n 现成的 Tool 节点包装：HTTP Request Tool 指向内部知识库检索 API；Call n8n Workflow Tool 把"通知值班"封装成一个可复用的子工作流。工具的名称和描述会传给模型，描述写得越具体，Agent 选工具越准
- **Memory 子节点**按会话 key 存上下文，多轮对话靠它

工具不是在代码里定义的 tools 数组——初学 n8n AI 节点时最常犯的错误就是把 LangChain 的代码习惯带进来。在 n8n 里，加工具等于往 Agent 上连一个 Tool 子节点。

### 6.4 错误处理与重试

**节点级重试**：在节点的 Settings 标签开启 "Retry On Fail"，配置 Max Tries（尝试次数）和 Wait Between Tries（重试间隔，毫秒）。适合网络抖动、限流这类瞬时故障：

```
Retry On Fail: true
Max Tries: 3
Wait Between Tries: 5000
```

**工作流级错误处理**：建一个独立的错误处理工作流（内含 Error Trigger 节点），然后在业务工作流的设置里把它指定为 Error Workflow。业务工作流失败时自动触发：

```
[Error Trigger] ──▶ [Slack: 告警通知] ──▶ [写错误日志到数据库]
```

**条件路由**：用 IF 节点按表达式分流：

```
表达式: {{ $json.error?.code === 'RATE_LIMIT' }}
├── true:  [Wait 60s] ──▶ [重试原请求]
└── false: [Send Email 通知]
```

三层各管一段：瞬时故障交给重试，系统性失败交给 Error Workflow，业务分支交给 IF。

## §7 开发扩展

### 7.1 社区节点：安装与开发

**安装别人的节点**（自托管实例支持三种方式）：

1. **界面安装**：Settings → Community Nodes → Install a community node，输入 npm 包名即可，适合单机日常使用
2. **手动安装**：queue 模式或不方便用界面时，进入 n8n 容器或服务器，在 `~/.n8n/nodes` 目录里 `npm install <包名>`，重启 n8n 生效
3. **环境变量批量管理**（n8n 2.21+）：设 `N8N_COMMUNITY_PACKAGES_MANAGED_BY_ENV=true` 并用 `N8N_COMMUNITY_PACKAGES` 列出固定包集合，n8n 每次启动对齐清单，适合流水线统一部署。注意启用后界面安装页会变成只读

社区节点从 npm 安装，仅自托管实例可用；n8n Cloud 只能用官方验证过的社区节点。

**开发自己的节点**：从官方模板 [n8n-nodes-starter](https://github.com/n8n-io/n8n-nodes-starter) 起步，它预置了构建工具链和示例：

```
my-n8n-nodes/
├── package.json              # keywords 必须含 n8n-community-node-package
├── nodes/
│   └── GithubIssues/
│       ├── GithubIssues.node.ts     # 节点主文件
│       └── github.svg               # 节点图标
└── credentials/
    └── GithubIssuesApi.credentials.ts   # 凭证定义
```

节点主文件实现 `INodeType` 接口。一个查 GitHub 仓库统计的例子：

```typescript
import {
  IExecuteFunctions,
  INodeExecutionData,
  INodeType,
  INodeTypeDescription,
} from 'n8n-workflow';

export class GithubIssues implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'GitHub 仓库统计',
    name: 'githubIssues',
    group: ['input'],
    version: 1,
    description: '获取仓库的 Star、Fork 等统计数据',
    defaults: { name: 'GitHub 仓库统计' },
    inputs: ['main'],
    outputs: ['main'],
    credentials: [
      {
        name: 'githubApi',
        required: true,
      },
    ],
    properties: [
      {
        displayName: '仓库路径',
        name: 'repo',
        type: 'string',
        required: true,
        default: 'n8n-io/n8n',
        description: '格式：owner/repo',
      },
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    const items = this.getInputData();
    const returnData: INodeExecutionData[] = [];

    for (let i = 0; i < items.length; i++) {
      const repo = this.getNodeParameter('repo', i) as string;
      const credentials = await this.getCredentials('githubApi');

      const response = await this.helpers.httpRequest({
        method: 'GET',
        url: `https://api.github.com/repos/${repo}`,
        headers: {
          Authorization: `Bearer ${credentials.apiKey as string}`,
          Accept: 'application/vnd.github.v3+json',
        },
      });

      returnData.push({
        json: {
          name: response.full_name,
          stars: response.stargazers_count,
          forks: response.forks_count,
          openIssues: response.open_issues_count,
          url: response.html_url,
        },
      });
    }

    return [returnData];
  }
}
```

凭证定义类实现 `ICredentialType`，字段同样声明式：

```typescript
import { ICredentialType, INodeProperties } from 'n8n-workflow';

export class GithubIssuesApi implements ICredentialType {
  name = 'githubApi';
  displayName = 'GitHub API';
  documentationUrl = 'https://docs.github.com/en/authentication';
  properties: INodeProperties[] = [
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

开发与发布流程：

```bash
npm install          # 安装依赖
npm run dev          # 本地调试（启动开发实例并热加载节点）
npm run build        # 构建
npm publish          # 发布到 npm，之后就能按社区节点安装
```

调试技巧：`N8N_LOG_LEVEL=debug` 提升服务日志级别；节点的 `execute` 里可以 `console.log` 中间变量；`this.helpers.httpRequestWithAuthentication` 能自动附加凭证，不用手工拼认证头。

### 7.2 工作流的版本管理

工作流可以导出为 JSON（编辑器菜单 Download），也能从文件或 URL 导入。把 JSON 存进 Git，配合 CLI 或 API 导入，就能把工作流纳入 "基础设施即代码" 的管理——环境之间迁移、回滚、评审都有据可查。

### 7.3 生产环境实践

**监控**：n8n 内置 Prometheus 指标端点，设 `N8N_METRICS=true` 开启 `/metrics`（默认关闭，不要对公网暴露），配合官方 Grafana 看板可以看执行量、队列深度等指标。

**数据清理**：执行历史默认自动清理——超过 336 小时（14 天）或总数超过 10000 条的部分会被定期删除（`EXECUTIONS_DATA_PRUNE=true` 默认开启）。数据量大的实例可以调小 `EXECUTIONS_DATA_MAX_AGE`，或在工作流设置里只保存出错的执行。

**安全加固**：

- `N8N_ENCRYPTION_KEY` 用足够长的随机字符串，安全保管；丢了它等于丢了数据库里所有凭证
- 数据库（PostgreSQL）不暴露公网，走内网或 VPN
- 全站 HTTPS，关闭 HTTP 回退
- 凭证定期轮换；n8n 2.0 起默认禁用了 ExecuteCommand 和 LocalFileTrigger 这类高危节点，以及 Code 节点内的环境变量访问，非必要不要放开

**性能**：

- 并发量大时切 queue 模式，按负载增减 worker
- HTTP Request 节点设置合理的超时，避免慢接口拖住整个工作流
- 大批量数据处理拆分为分页处理，或用子工作流分批调度

## §8 进阶学习路径

- **RAG 工作流**：用 Vector Store 节点（Qdrant、Postgres 向量库等）接 Embedding 模型，搭私有知识库问答
- **多 Agent 协作**：AI Agent 节点可以串联或并联组合，配合 human-in-the-loop 审批节点做人机协同
- **源码阅读**：`packages/nodes-base` 里每个官方节点都是活教材，HTTP Request、Code 两个高频节点的实现值得通读
- **执行顺序深入**：多分支工作流的执行顺序（v0/v1 语义差异）官方文档有专文，处理复杂分支前建议先读

## 参考资源

- [n8n 官方文档](https://docs.n8n.io)
- [n8n GitHub 仓库](https://github.com/n8n-io/n8n)
- [n8n 社区工作流模板](https://n8n.io/workflows)
- [n8n AI 能力文档](https://docs.n8n.io/advanced-ai/)
- [n8n 社区论坛](https://community.n8n.io)
