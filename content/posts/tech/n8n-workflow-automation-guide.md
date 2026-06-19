---
title: "n8n：开源工作流自动化平台指南"
date: "2026-04-06T22:16:00+08:00"
slug: "n8n-workflow-automation-guide"
description: "n8n 的真正差异化不是 400+ 集成，而是代码可扩展、自托管、AI LangChain 原生三者结合。本文从系统地图、任务流案例、与 Zapier/Make 的工程取舍、自托管部署、企业级功能到采用顺序，给出一份工程视角的落地指南。"
draft: false
categories: ["技术笔记"]
tags: ["n8n", "工作流自动化", "AI Agent", "LangChain", "低代码", "开源"]
---

## n8n 在企业场景里靠什么站住脚

把 n8n 放到 Zapier、Make（原 Integromat）旁边比较时，"400+ 集成"这个数字并不构成护城河——Zapier 的应用数量更多，Make 的可视化编排更顺。n8n 在企业场景里能站住脚，靠的是三件事同时具备：能写代码扩展、能自托管、AI LangChain 原生集成。

这三者的组合指向一个具体的采购决策：当工作流需要处理客户数据、内部知识库或受合规约束的凭证时，Zapier 和 Make 的云端模型会让数据必须经过第三方 SaaS，而 n8n 自托管可以把数据流限制在企业网络内；工作流逻辑复杂到无代码表达式无法表达时，n8n 的 Code 节点允许直接写 JavaScript 或 Python，并安装 npm 包；而工作流的核心是 LLM 调用而非传统 API 编排时，n8n 内置的 LangChain 节点把 Agent、Tool、Memory、Vector Store 做成了一等公民，而不是通过 HTTP Request 节点拼装。

代价是运维投入：n8n 自托管意味着要自己管 Docker、PostgreSQL、Redis、备份和升级。Sustainable Use License 也不是纯 OSS——它允许内部和商业使用，但禁止把 n8n 本身打包成 SaaS 转售，这与 MIT/Apache 的许可范围有明确差异，采购前需要法务确认。

本文按"先看系统地图，再走一次完整任务流，最后给采用顺序"的方式展开，适合正在评估工作流平台的工程师和架构师。读完之后，你应该能判断 n8n 是否适合你的场景，知道从哪里起步，以及哪些场景不该用它。

---

## n8n 的系统地图

n8n 的核心可以拆成五层，理解这五层的边界比记住 400+ 集成更重要：

```text
┌─────────────────────────────────────────────────────────┐
│  触发器层  Webhook / Schedule / Email / Manual / Form   │
│           / 第三方应用事件（GitHub、Slack、Shopify…）   │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  节点层    集成节点（OpenAI、PostgreSQL、Slack…）        │
│           Code 节点（JS / Python + npm 包）              │
│           AI 节点（LangChain Agent / Tool / Memory）     │
│           逻辑节点（IF / Switch / Merge / Loop）         │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  凭证层    独立于节点存储，加密保存                      │
│           支持 OAuth2、API Key、Basic Auth、JWT 等       │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  执行引擎  编排节点顺序、传递 item 数组、错误重试        │
│           支持子工作流、并发控制、超时                   │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  持久化层  工作流定义、执行历史、凭证密文                │
│           SQLite（默认）/ PostgreSQL / MySQL             │
└─────────────────────────────────────────────────────────┘
```

几个边界容易踩坑，单独拎出来说：

**凭证独立于节点存储**。一个 Slack 凭证可以被任意多个 Slack 节点引用，轮换 Token 时只改一处。这和直接在节点里写 API Key 的做法相比，安全性高一个量级——后者在节点配置里到处散落密钥，轮换一次得改几十处。

**Code 节点补的是集成节点的空白**。集成节点处理"调用某个 API 的标准姿势"，Code 节点处理"集成节点覆盖不到的转换逻辑"。能用集成节点就别写 Code，因为集成节点的字段映射、分页、重试已经处理好，自己写 Code 等于把这些都重造一遍。

**AI 节点和普通节点走的是同一套执行引擎**。LangChain Agent 节点是一个会多次回调工具节点的特殊节点，它的执行历史、错误处理、数据流转和普通节点一致，因此可以用同一套调试和监控手段管理 AI 工作流。

**触发器决定工作流的执行模型**。Webhook 触发器是同步的，调用方等待结果；Schedule 触发器是异步批处理；第三方应用事件触发器（如 GitHub Webhook、Slack Event）依赖 n8n 实例的公网可达性。选错触发器类型是新手最常见的坑。

---

## 与 Zapier、Make 的工程取舍

把三个平台放在一起时，差异不在功能数量，而在数据流向和扩展模型：

| 维度 | n8n | Zapier | Make |
|------|-----|--------|------|
| 部署模型 | 自托管或 n8n Cloud | 仅云端 | 仅云端 |
| 数据流向 | 可限制在企业网络内 | 必须经过 Zapier 云 | 必须经过 Make 云 |
| 代码扩展 | Code 节点支持 JS/Python + npm | 仅表达式 | 有限的表达式和模块 |
| AI 集成 | LangChain 节点原生 | 通过 OpenAI 应用 | 通过 HTTP 和模块组合 |
| 计费模型 | 自托管免费 / Cloud 按执行 | 按任务数 | 按操作数 |
| 凭证管理 | 独立加密存储 | 平台托管 | 平台托管 |
| 运维成本 | 自托管需投入 | 零运维 | 零运维 |

Zapier 和 Make 的零运维对小团队是实打实的好处——如果工作流只有十几条、数据不敏感、预算允许按量付费，云端方案的上线速度远快于自托管。n8n 的优势在另一端：工作流数量上百、数据受合规约束、需要写复杂转换逻辑、需要把 LLM 编排进流程——这些场景下自托管的控制权和代码扩展能力才真正产生价值。

计费模型也值得拆开看。Zapier 按任务数收费，Make 按操作数收费，两者都会在工作流规模放大时出现成本不可控。n8n 自托管的成本是固定的服务器费用，但需要把运维人力算进去。一个常见的误判是只看 SaaS 的标价，忽略自托管的隐性人力成本。

---

## 快速上手：从 npx 到 Docker

n8n 的安装方式按"测试 → 单机生产 → 集群"递进，选哪种取决于用途而非偏好。

### 测试用途：npx 一行启动

```bash
# 需要 Node.js
npx n8n
```

适合本地试一下编辑器和节点配置，数据存在 `~/.n8n`，不要用于生产。

### 单机生产：Docker

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

`-it --rm` 适合临时跑，生产环境改成 `-d` 并配合 `restart: unless-stopped`。`n8n_data` 卷里存着工作流定义、执行历史和加密凭证，丢了不可恢复，必须备份。

### 单机生产：Docker Compose

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

`N8N_SECURE_COOKIE=false` 只适合本地调试，生产环境必须配合 HTTPS 改成 `true`。

### 从源码构建

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

只有需要改 n8n 本身或调试自定义节点时才走这条路。日常使用没必要从源码构建。

---

## 工作流的核心抽象

### 节点（Node）

节点是工作流的最小执行单元。每个节点接收一个 item 数组，处理后输出一个 item 数组。item 是 n8n 的数据载体，结构是 `{ json: {...}, binary?: {...} }`。理解 item 数组这个模型很关键——它决定了节点之间如何传递数据，也决定了批量处理时的行为。

n8n 选择 item 数组而不是单个对象，是因为工作流自动化的典型场景就是批量处理：一次 Webhook 可能带 10 条订单，一次数据库查询可能返回 100 行。如果节点只处理单个对象，用户就得自己在每个节点里写循环逻辑。item 数组让批量语义成为默认行为，节点内部不用写 for 循环。

一个常见误区是把节点当成函数。节点更接近 map 操作：如果输入是 10 个 item，节点会对每个 item 执行一次，输出 10 个 item。Code 节点里写 `return [transformed]` 只会输出 1 个 item，要保留批量语义应该写 `return items.map(...)`。

### 触发器（Trigger）

触发器决定工作流何时启动。几类触发器的执行语义不同：

- **Webhook**：同步，调用方等待 n8n 返回。适合做 API 代理或即时响应。
- **Schedule**：异步，按 cron 表达式触发。适合批处理。
- **Email**：异步，IMAP 轮询新邮件。适合邮件驱动的流程。
- **Manual**：只在编辑器里手动点击执行。用于调试。
- **Form**：n8n 自带的表单页面提交触发。适合内部工具。
- **第三方应用事件**：依赖 Webhook URL 公网可达，配置时要把 `WEBHOOK_URL` 设对。

`WEBHOOK_URL` 配错是第三方触发器不工作的最常见原因。n8n 在向 GitHub、Slack 等平台注册 Webhook 时会用这个值，如果设成 `localhost`，平台回调时根本到不了你的实例。

### 凭证（Credential）

凭证独立于节点存储，加密保存在数据库里。这种解耦设计有几个好处：同一个凭证可以被多个节点复用（一个 Slack Token 能被几十个 Slack 节点引用），轮换凭证时只改一处，凭证的加密和权限管理可以单独做，不和具体节点的配置混在一起。

加密密钥由 `N8N_ENCRYPTION_KEY` 控制，默认自动生成并存在 `~/.n8n/config`。生产环境必须显式设置这个环境变量，否则密钥丢失后所有凭证不可解密。

凭证支持 OAuth2、API Key、Basic Auth、JWT 等常见类型。OAuth2 凭证会自动处理 Token 刷新，不需要在节点里手动管理过期。

---

## 一次 AI Agent 工作流的完整路径

分层图是静态的，下面用一个 AI 客服工作流把节点、触发器、凭证、执行引擎串起来，看看一次任务如何流过 n8n。

### 场景

客户在网站提交问题，n8n 接收后用 LLM 判断是否需要人工，需要则创建工单并通知 Slack，不需要则直接回复。

### 工作流结构

```text
[Webhook 触发]
    │  接收 POST /ask，body 含 question 和 user_id
    ▼
[LangChain Agent 节点]
    │  系统提示词：判断问题类型，决定调用哪些工具
    │  绑定工具：知识库检索、工单查询、工单创建
    ▼
[工具节点分支]
    ├── [Vector Store 检索]
    │     从 Pinecone 检索相关文档片段
    ├── [PostgreSQL 工单查询]
    │     查询该用户最近的工单状态
    └── [PostgreSQL 工单创建]
          当 Agent 判断需要人工时调用
    ▼
[LangChain Agent 节点（继续）]
    │  汇总工具返回结果，生成最终回复
    ▼
[IF 节点]
    │  判断回复中是否包含 "需要人工" 标记
    ├── 是 → [Slack 通知] → [Webhook Response 返回工单号]
    └── 否 → [Webhook Response 返回回复]
```

### 一次执行的内部流转

1. **Webhook 触发器**收到 HTTP 请求，把 `question` 和 `user_id` 包成 item 传给下游。
2. **LangChain Agent 节点**接收 item，把 `question` 作为用户消息发给 LLM。LLM 根据 system prompt 决定调用工具。
3. 假设 LLM 决定先检索知识库：Agent 节点暂停，调用 **Vector Store 检索**节点，传入查询词。检索节点返回 top-3 文档片段给 Agent。
4. Agent 把片段塞进上下文，再次调用 LLM。LLM 判断信息不足，决定再查工单历史。Agent 调用 **PostgreSQL 工单查询**节点。
5. 工单查询节点用预存的 PostgreSQL 凭证连接数据库，执行参数化查询，返回该用户最近 3 条工单。
6. Agent 把所有上下文交给 LLM 生成最终回复。回复里包含 "需要人工：是" 标记。
7. **IF 节点**解析回复，走 "是" 分支。
8. **Slack 通知**节点用 Slack 凭证发消息到 `#support` 频道，附带问题、用户 ID、Agent 的分析。
9. **Webhook Response** 节点返回工单号给调用方。
10. 整个执行过程被写入执行历史，包含每个节点的输入输出、耗时、状态。

### 从这个案例能看到的几件事

**Agent 节点会多次回调工具节点**。Agent 节点在内部循环：调用工具 → 拿到结果 → 再问 LLM → 决定是否继续调用。执行历史里会看到工具节点被多次执行，这是正常行为，不是重试。

凭证在多个节点间共享是这个工作流的关键设计。PostgreSQL 凭证被工单查询和工单创建两个节点引用，Slack 凭证被通知节点引用。轮换数据库密码时只改一处，所有引用该凭证的节点自动生效。

**错误处理需要显式设计**。如果 Vector Store 检索失败，Agent 会拿到错误信息继续推理，可能产生幻觉。生产环境应该在工具节点里加 try-catch，返回结构化错误给 Agent，而不是让 LLM 自己猜。

还有一点容易忽略：Webhook 触发器有超时限制。LLM 调用 + 工具调用可能超过 30 秒，HTTP 客户端会超时。长任务应该改成异步——Webhook 立即返回 "处理中"，后台工作流完成后通过另一个 Webhook 或 Slack 通知。

---

## 400+ 集成背后的工程取舍

n8n 的集成不是单一形态，理解三种集成方式的差异比数集成数量重要：

**原生集成节点**：n8n 官方维护的节点，如 OpenAI、Slack、PostgreSQL、GitHub。字段映射、分页、错误处理已经处理好，能用就用。

**HTTP Request 节点**：通用 HTTP 客户端，可以调用任何 REST API。适合原生节点没覆盖的服务，或需要精细控制请求的场景。配合 `Define OAuth2 API` 凭证类型，可以给任意 API 加 OAuth2 支持。

**自定义节点**：用 TypeScript 写的节点包，发布到 npm。适合内部系统或高频使用的第三方服务。开发成本高于前两者，但复用性最好。

### OpenAI 集成示例

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

实际配置时优先用 n8n 编辑器的可视化字段，JSON 形态主要用于版本管理和模板导出。`temperature` 和 `maxTokens` 的取值要根据场景调，客服场景建议 `temperature` 设 0.3 以下以减少随机性。

### Slack 集成示例

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

`{{ $now }}` 是 n8n 的表达式语法，运行时求值。表达式可以引用上游节点的输出，比如 `{{ $json["workflow_name"] }}`。

### 数据库集成示例

```javascript
// PostgreSQL 查询节点
{
  "operation": "execute",
  "query": "SELECT * FROM users WHERE created_at > $1",
  "values": ["{{ $json.since }}"]
}
```

参数化查询是硬性要求。直接拼字符串会导致 SQL 注入，n8n 的 PostgreSQL 节点支持 `$1`、`$2` 占位符，配合 `values` 数组传参。

### 集成分类速查

| 分类 | 代表集成 |
|------|---------|
| AI & ML | OpenAI、Anthropic Claude、LangChain、Hugging Face |
| 通信 | Slack、Discord、Teams、Email |
| 云服务 | AWS、Google Cloud、Azure |
| 数据库 | PostgreSQL、MySQL、MongoDB、Redis |
| CRM | Salesforce、HubSpot |
| 电商 | Shopify、WooCommerce、Stripe |
| 社交 | Twitter/X、LinkedIn、Instagram |
| 开发 | GitHub、GitLab、Jira |

这个表只用于快速定位。具体某个服务是否支持某个操作，查 [n8n 集成中心](https://n8n.io/integrations) 比记表格靠谱。

---

## 自托管部署的真实考量

### 为什么自托管对企业重要

自托管把数据流限制在企业控制的边界内。Zapier 和 Make 的工作流执行时，数据会经过它们的云端服务器——这对个人或小团队无伤大雅，但对处理客户 PII、内部财务数据、医疗记录的企业，可能直接违反 GDPR、HIPAA 或行业合规要求。n8n 自托管后，数据流可以完全在内网完成，只有需要调用外部 API 时才出境。

第二个价值是凭证控制。云端方案下，所有 API Key、OAuth Token 都存在 SaaS 平台侧，平台被攻破意味着所有凭证泄露。自托管把凭证存在企业自己的加密存储里，攻击面收窄到企业自己的基础设施。

第三个价值是成本可控。SaaS 按执行或操作收费，工作流规模放大后成本会非线性增长。自托管的成本是固定的服务器和运维人力，规模越大单位成本越低。

但运维投入省不掉：备份、升级、监控、安全补丁都要自己做。如果团队没有专职运维，自托管的隐性成本可能超过 SaaS 的显性成本。

### Docker 部署

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

`WEBHOOK_URL` 必须设成外部可访问的地址，否则第三方 Webhook 注册会失败。

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

企业内网通常需要走代理才能访问外部 API。注意 n8n 调用 OpenAI、Slack 等 SaaS 时会走这个代理，但调用内网服务时不应该走——需要配合 `NO_PROXY` 环境变量排除内网域名。

### 关键环境变量

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

`N8N_ENCRYPTION_KEY` 在生产环境必须显式设置并妥善保管。丢失后所有凭证不可解密，等于工作流全部失效。`EXECUTIONS_DATA_SAVE_ON_SUCCESS` 在高频工作流下建议改成 `none` 或自定义 prune，否则执行历史会无限增长撑爆数据库。

### 数据持久化

```bash
# 创建命名卷
docker volume create n8n_data

# 查看卷位置
docker volume inspect n8n_data
```

默认用 SQLite，数据存在 `n8n_data` 卷里。生产环境建议改用 PostgreSQL，性能和并发能力都更好。切换数据库时执行历史不会自动迁移，需要导出工作流定义后在新数据库重新导入。

### HTTPS 配置

生产环境必须 HTTPS。用 Traefik 做反向代理和自动证书：

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

`N8N_SECURE_COOKIE` 在 HTTPS 下必须设回 `true`，否则 Cookie 可能在中间节点被截获。

---

## 企业级功能：什么时候需要

n8n 的企业级功能按需开启，单团队用不上就别开。

### 权限管理

| 角色 | 权限 |
|------|------|
| Owner | 完全控制 |
| Admin | 管理用户和工作流 |
| Member | 编辑自己的工作流 |
| Editor | 仅编辑 |
| Viewer | 仅查看 |

角色系统在多团队共用一个 n8n 实例时才有价值。单团队使用时全员 Admin 反而更顺手，权限分层带来的管理成本可能超过收益。

**项目隔离**：按项目分组工作流，独立权限控制，跨项目模板共享。适合多业务线共用平台的中大型组织。

### SSO 配置

支持 SAML 2.0、OIDC（OpenID Connect）、LDAP/Active Directory。企业已有身份提供商时强制走 SSO，避免本地账号泄露后横向移动。

**OIDC 配置示例**（通过环境变量注入，具体变量名以 n8n 当前版本文档为准）：

```yaml
# 环境变量（生产环境通过密钥管理服务注入，不要写进 docker-compose.yml）
N8N_SSO_ENABLED=true
N8N_SSO_PROVIDER=oidc
N8N_SSO_CLIENT_ID=your-client-id
N8N_SSO_CLIENT_SECRET=your-client-secret
N8N_SSO_ISSUER_URL=https://your-idp.com
```

`N8N_SSO_CLIENT_SECRET` 必须通过环境变量或密钥管理服务注入，不要写进 docker-compose.yml 提交到 Git。SSO 相关环境变量名在不同 n8n 版本间有调整，部署前以 [n8n 官方环境变量文档](https://docs.n8n.io/hosting/configuration/environment-variables/) 为准。

### 空中隔离部署

n8n 支持 Air-Gapped 环境部署：无需互联网连接，完全离线运行，企业内部数据安全。代价是无法用 n8n Cloud 的模板同步、无法自动更新节点定义。适合金融、军工、能源等强隔离行业。

### 审计日志

用户操作记录、工作流执行历史、敏感操作告警。审计日志建议导出到外部 SIEM（如 ELK、Splunk），n8n 自身的日志存储不适合长期合规留存。

---

## 自定义节点开发：何时该写、何时不该写

写自定义节点之前先问三个问题：

1. HTTP Request 节点能不能解决？能就别写。
2. 是不是高频复用的内部系统？是才值得写。
3. 团队有没有维护 npm 包的能力？没有就先用 HTTP Request 顶着。

自定义节点的好处是把内部系统的 API 调用标准化，让非开发同事也能在编辑器里拖拽使用。如果只是某个工作流用一次，HTTP Request 节点更合适。

### 创建自定义节点

```bash
# 使用 n8n 节点开发工具
npx n8n-node-dev

# 选择基础模板
? Select a template for your new node
  ❯ Empty Node
    CredentialType
    Template
```

### 节点结构

```text
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

凭证和节点分开存放是有意设计：一个凭证类型可以被多个节点复用，比如内部 API 网关的 Token 可能被十几个内部服务节点共用。

### 节点代码示例

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

`execute` 方法里的 `for` 循环是 n8n 节点的标准模式：对每个输入 item 执行一次操作，保持批量语义。如果只处理第一个 item，会丢失批量数据。

### 发布节点

```bash
# 构建
pnpm build

# 登录 npm
npm login

# 发布到 npm
npm publish --access public
```

发布前在 `package.json` 里加 `n8n` 字段声明节点入口，否则 n8n 识别不到。内部节点可以发到私有 npm registry，不必公开。

---

## 实战场景与适用边界

### AI 客服机器人

```text
[Webhook 触发] 
  → [LangChain Agent] 
    → [Tool: Slack] 
    → [Tool: 数据库查询]
```

适合：知识库相对稳定、问题类型可枚举的客服场景。

不适合：需要多轮深度对话、需要情感判断的高敏感场景——这类场景用专门的对话框架（如 Rasa）更合适，n8n 做后端编排。

### 数据同步管道

```text
[Schedule 触发]
  → [PostgreSQL 查询]
  → [数据转换]
  → [Elasticsearch 索引]
  → [发送 Slack 通知]
```

适合：定时全量或增量同步、ETL 轻量场景。

不适合：实时 CDC（变更数据捕获）、超大规模数据（千万级以上）——前者用 Debezium + Kafka，后者用 Spark 或 Flink。

### 社交媒体管理

```text
[RSS 触发]
  → [内容提取]
  → [AI 生成摘要]
  → [多平台发布]
    → Twitter
    → LinkedIn
    → Facebook
```

适合：内容运营团队的发布自动化。

不适合：需要严格审核流程的场景——AI 生成内容直接发布有合规风险，应该加人工审核节点。

### 电商订单处理

```text
[Shopify 新订单]
  → [验证库存]
  → [创建发货单]
  → [发送邮件通知]
  → [更新 CRM]
```

适合：中小电商的订单流转自动化。

不适合：高频交易、强一致性要求的场景——n8n 的工作流不是事务性的，中间节点失败不会自动回滚上游操作，需要显式设计补偿逻辑。

---

## 排查与运维

### 调试工作流

1. 用 Manual 触发器逐步测试，不要直接用 Webhook 触发器调试。
2. 在每个节点后加 Code 节点打印 `JSON.stringify($input.all(), null, 2)`，看实际数据结构。
3. 用编辑器的 "Preview" 模式查看每个节点的输入输出，比看执行日志直观。
4. 执行历史里点开失败节点，看错误堆栈和当时的输入数据——大多数错误是数据结构不匹配，不是节点本身的问题。

### 处理大文件

- 用流式处理（Streaming），不要把整个文件读进内存。
- 配置节点超时时间（在节点设置的 `Timeout` 字段里），避免长任务卡死执行引擎。
- 用 "Chunk" 或 "Loop" 节点分批处理，每批控制在几百条。

### 错误处理与重试

n8n 的错误处理有三种模式：

- **节点级重试**：在节点设置里开启 retry，配置间隔和次数。适合网络抖动类错误。
- **错误触发器**：用 `Error Trigger` 节点捕获工作流错误，转发到告警工作流。适合集中监控。
- **Try-Catch 模式**：用 `Execute Workflow` 节点调用子工作流，子工作流失败时走补偿逻辑。适合需要事务性的场景。

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

### 高可用部署

单机 n8n 挂了工作流就停了。生产环境建议多副本 + Redis + PostgreSQL：

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

多副本模式下，`EXECUTIONS_MODE` 要设成 `queue`，Webhook 触发器由 Redis 队列分发到不同副本执行。注意：定时触发器在多副本下会去重，但 Webhook 触发器需要外部负载均衡保证幂等。

### 升级

```bash
# Docker 方式
docker pull docker.n8n.io/n8nio/n8n:latest
docker stop n8n
docker rm n8n
# 重新启动（数据保持）
```

升级前必须备份 `n8n_data` 卷和数据库。n8n 的大版本升级（如 1.x → 2.x）可能有不兼容变更，先在测试环境验证。生产环境建议锁定版本号，不要用 `latest` 标签。

### 监控

监控三个指标就够了：

- **执行成功率**：低于 95% 说明工作流有稳定性问题。n8n 自身的执行历史 API（`/api/v1/executions`）可以拉到每次执行的状态，配合 Prometheus 暴露成功率指标。
- **执行耗时 P95**：突然变长通常是上游 API 变慢或数据库索引缺失。关注 P95 而非平均值，长尾任务会拖垮整体体验。
- **队列积压**：多副本模式下，Redis 队列长度持续增长说明副本数不够。用 `redis-cli LLEN <queue_name>` 监控。

告警建议接 PagerDuty 或飞书机器人，不要只靠邮件——工作流故障往往在非工作时间发生，邮件告警的响应速度不够。

---

## 采用顺序与决策建议

### 谁该先用 n8n

**适合先上的团队**：

- 有运维能力的中大型企业，工作流涉及敏感数据，需要自托管满足合规。
- AI 应用团队，需要把 LLM 编排进业务流程，且不想从零搭 Agent 框架。
- 内部工具团队，需要快速搭建跨系统数据流转，且逻辑复杂到无代码表达式不够用。

**可以等等的团队**：

- 工作流只有几条、数据不敏感的小团队——Zapier 或 Make 上线更快，零运维。
- 需要严格事务一致性的场景——n8n 的工作流不是事务性的，金融交易类场景不合适。
- 需要超低延迟的场景——n8n 的执行引擎有调度开销，毫秒级响应用代码直接写更快。

### 落地顺序

1. **先跑通一个非关键工作流**。选一个数据不敏感、失败可接受的工作流（如每日报告推送），用 Docker 单机部署验证。这一步验证的是 Docker 部署、`WEBHOOK_URL` 配置、凭证加密存储是否正常工作。
2. **再迁移一个 AI 工作流**。把一个现有的 LLM 调用脚本改造成 n8n 工作流，体验 LangChain 节点的编排能力。重点看 Code 节点的 npm 包安装、LangChain Agent 节点的工具回调机制、以及 Webhook 触发器的超时限制。
3. **然后做凭证和权限治理**。把散落在各处的 API Key 收敛到 n8n 凭证系统，按团队划分项目。这一步验证的是凭证的 OAuth2 Token 刷新、项目隔离的权限模型、以及 `N8N_ENCRYPTION_KEY` 的备份策略。
4. **最后做高可用和监控**。工作流数量上 50 条、有核心业务依赖后，再上多副本和监控。盯三个指标：执行成功率、P95 耗时、队列积压，分别对应工作流稳定性、长尾任务和 Redis 队列健康度。

### 不要做的事

- 不要把 n8n 当数据库用。工作流定义和执行历史不是业务数据，该存业务库的还是要存业务库。
- 不要在 Code 节点里写复杂业务逻辑。Code 节点适合数据转换，复杂逻辑应该抽成独立服务，n8n 通过 HTTP Request 调用。
- 不要忽略执行历史的增长。生产环境必须配置 prune 策略，否则磁盘会爆。
- 不要用 `latest` 标签跑生产。版本漂移会导致工作流行为突然变化。

### Sustainable Use License 的边界

n8n 的许可证是 Sustainable Use License，属于 fair-code 范畴，不是 OSI 认可的开源许可证。具体边界：

- ✅ 内部使用：企业内部跑工作流，无限制。
- ✅ 商业使用：把 n8n 集成进自己的产品提供给客户，可以。
- ❌ 转售 n8n 本身：把 n8n 改个名字作为 SaaS 卖给别人，不行。
- ❌ 移除许可证限制：去除 fair-code 限制后重新分发，不行。

采购前让法务确认这个许可证是否符合公司政策。部分企业对非 OSI 开源许可证有统一禁令，需要提前沟通。

### 官方资源

- GitHub：https://github.com/n8n-io/n8n
- 文档：https://docs.n8n.io
- 集成中心：https://n8n.io/integrations
- 模板库：https://n8n.io/workflows
- 社区论坛：https://community.n8n.io
- AI 指南：https://docs.n8n.io/advanced-ai/
