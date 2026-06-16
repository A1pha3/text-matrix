---
title: "Dify：开源 Agentic Workflow 开发平台从入门到精通指南"
date: "2026-05-02T10:12:21+08:00"
slug: "dify-agentic-workflow-development-platform-guide"
description: "Dify 是一款开源的 LLM 应用开发平台，集成 AI 工作流、RAG 管道、Agent、模型管理等功能，支持从原型到生产的完整流程。本文深入分析其核心原理、系统架构，提供详细的安装配置指南与实战演示，助你掌握这一生产级 Agentic Workflow 开发平台。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "LLM", "Agent", "Agentic Workflow", "RAG", "工作流", "Dify", "Python"]
---

很多团队在 Prompt 调优阶段做得不错，但一把 LLM 接入真实业务流，问题就来了：日志怎么查？多模型怎么切换？RAG 管道怎么管？生产流量怎么限？这些不是换个 Prompt 就能解决的——它们需要一套把模型调用、流程编排、数据管理和可观测性统一起来的平台。

[Dify](https://github.com/langgenius/dify) 正是在这个方向上深耕的开源项目（139k+ Stars），是 Agentic Workflow 领域最活跃的开源项目之一。它把 AI 工作流、RAG 管道、Agent、模型管理和 LLMOps 整合到一个可视化界面里，让开发者可以从原型一路迭代到生产级应用。

这篇文章讲 Dify 的核心原理、系统架构、安装部署、典型场景实战和二次开发路径。读完能跑通完整示例，也能在生产环境里用起来。

## 1. 原理分析

### 1.1 什么是 Agentic Workflow

传统 LLM 应用的核心模式是**单轮问答**：用户给一段 Prompt，模型返回一个答案。这种模式在简单场景下足够用，但面对复杂业务流程时会产生两个问题：一是任务无法在单次调用中完成，需要拆解为多步骤；二是决策需要根据执行结果动态调整。

Agentic Workflow（智能体工作流）就是对这两个问题的系统化回答。它将 AI 任务的执行单元从「一次调用」扩展为「多步循环」，每个步骤可以由 LLM 本身、其他 AI 模型或传统代码共同完成，步骤之间通过状态传递形成有向图结构。

拿「分析竞品报告」这个任务来说。传统方式的 Prompt 大概长这样：

```
请分析以下竞品信息，输出优劣势分析报告。
```

用 Agentic Workflow 的思路来实现，这个任务会被分解为：

1. **信息提取**（LLM）：从原始文本中提取竞品名称、关键指标
2. **并行查询**（Tool）：针对每个竞品查询最新市场数据
3. **综合分析**（LLM）：将提取信息与查询结果合并，生成结构化报告
4. **质量校验**（LLM）：检查报告逻辑完整性，决定是否需要补充查询

这四个步骤构成一个有向无环图（DAG）：每个节点可以独立替换，也可以并行执行，失败时只重跑受影响的分支。Dify Workflow 的核心抽象就是这张图。

### 1.2 Dify 的核心设计理念

Dify 在设计上有三个值得注意的决策。

**抽象层次的一致性。** Dify 把聊天助手、Agent、工作流、RAG 应用都统一到「应用（Application）」这个概念下，区别只在于执行模型和流程编排方式。开发者在同一个界面里就能完成从简单对话机器人到复杂多步骤工作流的全部开发，不用在多个工具之间切换。

**提示词即资产。** Prompt、上下文和对话历史在 Dify 里是第一等公民。每次对话、每个工作流节点都有版本记录，可以随时回滚和对比。这个设计对应 LLMOps 的一条经验：模型能力的差异根子在 Prompt 工程，而 Prompt 工程需要版本管理。

**BaaS 优先。** 所有功能都配有 REST API 和 Webhook，天然嵌入已有业务系统。平台本身是 Backend-as-a-Service，前端通过 API 调用所有能力，不需要直接依赖 Dify 的前端界面。

### 1.3 Dify 与其他开发方式的对比

Dify 不是万能工具，有些场景用直接调 API 或 LangChain 更合适。理解它的适用边界，选型时不容易踩坑。

| 维度 | 直接调用 API | LangChain / LangGraph | Dify |
|------|------------|----------------------|------|
| 上手难度 | 低 | 高 | 中 |
| 快速原型 | ✅ 极快 | ❌ 大量胶水代码 | ✅ 拖拽即可 |
| Workflow 编排 | ❌ 需自建 | ✅ 灵活 | ✅ 可视化 + 代码 |
| 生产可观测性 | ❌ 自建 | 部分 | ✅ 内置 |
| 多租户/权限 | ❌ 自建 | ❌ 自建 | ✅ 开箱即用 |
| 定制化上限 | ✅ 最高 | ✅ 最高 | 中（受限于平台能力） |

如果你的团队需要快速验证 AI 概念并尽快进入生产，Dify 是一条投入产出比很高的路径。如果追求极致定制化或已有成熟的基础设施，LangChain/LangGraph 仍然是更灵活的底层框架。两者不是互斥的——Dify 的自定义工具（Tools）机制可以接入 LangChain Chain，形成互补。

## 2. 架构分析

### 2.1 整体架构

Dify 采用微服务架构，所有组件通过 Docker 容器化部署。从功能层次上，可以划分为四层：

```
┌─────────────────────────────────────────────────────────┐
│                    Web UI (React)                       │
│              提示词 IDE / 工作流画布 / 日志              │
├─────────────────────────────────────────────────────────┤
│                      API Server                         │
│          (Flask + Nginx + Gunicorn)                     │
│     应用管理 / 鉴权 / 租户隔离 / API 路由 / 事件分发     │
├─────────────┬──────────────┬───────────────────────────┤
│  Worker     │  Plugin      │  Sandbox                  │
│  (Celery)   │  Engine      │  (代码执行隔离)            │
│  异步任务   │  扩展机制    │  用户自定义代码安全执行     │
├─────────────┴──────────────┴───────────────────────────┤
│                PostgreSQL        Redis                  │
│              (元数据/应用配置)   (缓存/消息队列)         │
├─────────────────────────────────────────────────────────┤
│           支持 100+ 模型提供商（OpenAI / Anthropic /     │
│           本地模型 / Azure / Gemini 等）                 │
└─────────────────────────────────────────────────────────┘
```

**Web UI** 层是 React 单页应用，负责用户交互、工作流可视化编排、提示词调试、日志查看等前端能力。

**API Server** 层是 Dify 的核心，用 Python/Flask 实现，通过 Gunicorn + Nginx 做生产部署。几乎所有用户可见的功能——应用的创建、版本管理、API 调用、日志读取——都经过这一层。API Server 还负责租户隔离、访问控制（基于 RBAC）和审计日志。

**Worker** 层基于 Celery 实现异步任务系统。LLM 推理调用、日志写入、数据导出等耗时操作以异步任务方式执行，通过 Redis 做消息队列。Worker 支持水平扩展，可以根据负载情况增加节点。

**Sandbox** 是一个隔离执行环境，用于安全运行用户上传的自定义 Python 代码片段和部分工具逻辑，防止恶意代码影响主机系统。Dify v1.0+ 版本对 Sandbox 做了显著强化，安全性更高。

**数据库层** 使用 PostgreSQL 存储应用元数据、用户配置、对话历史和日志。Redis 承担缓存、Session 存储和 Celery 消息队列的角色。

### 2.2 核心数据模型

搞懂 Dify 的数据模型，才能理解它的扩展边界。核心实体有以下几类：

**Tenant（租户）** 是 Dify 的顶级隔离单位。每个租户拥有独立的用户体系、应用配置、积分制度和用量统计。多租户设计意味着 Dify 可以直接用于 SaaS 化运营。

**App（应用）** 是 Dify 的核心工作单元，分为四种类型：

- **chatApp**：对话类应用，支持多轮对话和上下文记忆
- **completionApp**：补全类应用，适用于一次性生成任务
- **workflowApp**：工作流应用，基于有向图编排的复杂任务
- **agentApp**：Agent 应用，基于 ReAct 或 Function Calling 的智能体

**Conversation（会话）** 关联一个 App 和一个终端用户，记录完整的多轮对话历史。每个 Message 属于一个 Conversation，支持人工标注和反馈。

**Workflow（工作流）** 是 Dify v1.0+ 引入的核心能力。它由多个 **Node（节点）** 和 **Edge（边）** 组成，Node 代表一个处理单元（如 LLM 调用、条件分支、数据转换），Edge 代表数据流向。工作流支持条件分支、并行执行、循环等复杂控制流，比传统的线性 Prompt 链强大得多。

**Dataset（知识库）** 是 Dify 的 RAG 能力载体。每个 Dataset 包含多个 Document（文档），文档经过切片（Chunking）处理后存入向量数据库（默认是 pgvector，PostgreSQL 的向量扩展）。Dify 支持从 PDF、PPT、Word、Markdown 等格式直接导入文档。

### 2.3 推理调用链路

当用户发起一次 LLM 调用时，Dify 的处理链路如下：

```
用户请求 → API Server（鉴权+路由）
         → 检查缓存（Redis）
         → 构造 Prompt（含上下文+变量替换）
         → 调用模型提供商 API（OpenAI兼容格式）
         ← 接收模型响应
         → 流式/非流式返回
         → 记录日志（PostgreSQL + S3/本地）
         → 触发 Webhook（如果配置了）
```

Dify 对模型调用做了两层抽象：底层是 **Model Runtime**，对接各提供商的具体 API 实现；上层是 **Model Config**，保存每个租户的配置（API Key、base URL、模型参数等）。这种设计让切换模型提供商对上层应用透明，也支持在同一应用内做 A/B 模型对比。

## 3. 安装配置

### 3.1 环境要求

Dify 对硬件的要求因规模和功能而异。对于单机体验和功能验证，推荐配置：

| 资源 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核以上 |
| 内存 | 4 GiB | 8 GiB 以上 |
| 磁盘 | 20 GiB | 50 GiB 以上（视文档量） |
| Docker | 20.x + Compose V2 | 最新稳定版 |

如果需要跑较大的开源模型（如 Llama3 70B），内存建议 16 GiB 以上，或者使用 Ollama 等本地推理服务通过 OpenAI-compatible API 接入 Dify。

### 3.2 Docker Compose 快速部署

Docker Compose 是最推荐的安装方式，一条命令即可启动完整服务。

```bash
# 克隆仓库
git clone https://github.com/langgenius/dify.git
cd dify/docker

# 复制环境变量配置
cp .env.example .env

# 启动所有服务
docker compose up -d
```

启动完成后，打开浏览器访问 `http://localhost/install`，按照引导完成管理员账号创建和基础配置。整个过程不超过五分钟。

`.env` 文件中需要关注几个关键配置项：

```bash
# 服务基础配置
SECRET_KEY=your-secret-key-here          # 建议使用随机字符串
CONSOLE_WEB_URL=http://localhost          # 前端地址
CONSOLE_API_URL=http://localhost/api       # 后端API地址

# 数据库（默认使用 Docker Compose 内置 PostgreSQL）
DB_USERNAME=dify
DB_PASSWORD=dify
DB_HOST=postgres
DB_PORT=5432
DB_DATABASE=dify

# Redis（默认使用 Docker Compose 内置 Redis）
REDIS_HOST=redis
REDIS_PORT=6379

# 模型提供商配置（按需填写）
# OpenAI
OPENAI_API_KEY=sk-xxxx
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=xxxx
# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxxx
```

如果你需要连接本地模型服务（如 Ollama），在 Dify 的「模型供应商」页面添加「OpenAI-Compatible 接口」，填入 Ollama 的地址（通常是 `http://localhost:11434/v1`）和模型名称即可。

### 3.3 常用生产环境配置

**反向代理配置（Nginx）**

生产环境中，建议用 Nginx 做反向代理，同时处理 SSL 终止和请求限流：

```nginx
server {
    listen 443 ssl;
    server_name dify.your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 流式响应需要关闭缓冲
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding on;
    }

    location /api {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://localhost:80;
    }
}
```

**外部 PostgreSQL**

如果数据量较大，可以将 PostgreSQL 迁移到独立数据库服务器：

```bash
# .env 中修改数据库连接
DB_HOST=your-postgres-host.internal
DB_PORT=5432
DB_DATABASE=dify
DB_USERNAME=dify_prod
DB_PASSWORD=strong-password-here
```

**外部 S3 兼容存储**

Dify 的日志和上传文件默认存储在本地 Docker 卷中，生产环境建议切换到 S3 兼容存储（如 MinIO、阿里云 OSS、AWS S3）：

```bash
S3_ENDPOINT=https://your-bucket.s3.region.amazonaws.com
S3_BUCKET_NAME=dify-logs
S3_ACCESS_KEY=AKIAxxx
S3_SECRET_KEY=xxx
S3_REGION=us-east-1
```

### 3.4 常见安装问题排查

**端口冲突**

Docker Compose 默认占用端口 `80`（Nginx）、`5432`（PostgreSQL）、`6379`（Redis）、`3000`（前端）。如果这些端口已被占用，修改 `docker-compose.yaml` 中的端口映射或停掉冲突服务。

**模型调用返回 400/401 错误**

先确认 API Key 正确，然后在 Dify 的「模型供应商」页面点击对应供应商卡片的「检查连接」按钮。Dify 会发送一个探测请求来验证配置是否生效。如果使用代理，确保代理支持 `POST` 方法和流式响应格式。

**向量检索结果不准确**

检查知识库的切片策略。Dify 默认按固定长度切片，容易在句子中间断开，导致语义不完整。可以在知识库设置中将切片策略调整为「语义分块」，或手动调整切片大小和重叠参数。

## 4. 实战演示

### 4.1 场景一：构建一个基于知识库的问答机器人

这是 Dify 最典型的使用场景——将产品文档上传到知识库，用户提问时自动检索相关片段并生成答案。

**Step 1：创建知识库**

1. 在左侧菜单选择「知识库」，点击「创建知识库」
2. 上传文档（支持 PDF、Word、PPT、Markdown、TXT）
3. 选择切片策略：Dify 提供「自动」和「手动」两种模式。自动模式下系统自动识别文档结构并切片；手动模式允许你自定义切片大小和重叠
4. 点击「索引并处理」，等待文档处理完成（大型文档可能需要几分钟）

**Step 2：创建应用**

1. 选择「创建应用」→「聊天助手」
2. 在「提示词编排」页面，启用「RAG」能力，并将刚才创建的知识库关联进来

```
你是一个专业的技术支持助手。当用户提问时，先从知识库中检索相关信息，
然后结合检索结果给出准确、专业的回答。如果知识库中没有相关信息，
请明确告知用户，并提供一般性的建议。
```

3. 调整模型参数（温度、Top-P、最大 token 数），保存

**Step 3：测试与发布**

在右侧对话窗口输入问题，观察知识库检索结果和最终答案的生成质量。如果检索到的片段不相关，可以回到知识库调整切片策略或重新上传格式更规范的文档。

确认效果后，点击「发布」，获得 API 地址和调用示例。

```python
import requests

response = requests.post(
    "https://your-dify-instance/v1/chat-messages",
    headers={
        "Authorization": "Bearer-app-YOUR_API_KEY",
        "Content-Type": "application/json"
    },
    json={
        "query": "你们产品的退款政策是什么？",
        "user": "user-123",
        "response_mode": "streaming"
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode("utf-8"))
```

### 4.2 场景二：构建多步骤 Agent 工作流

下面实现一个「竞品分析助手」：用户输入竞品名称后，Agent 自动完成提取竞品信息 → 并行搜索最新动态 → 整理分析报告。

**Step 1：创建工作流应用**

选择「创建应用」→「工作流」，进入可视化编排画布。

**Step 2：编排工作流节点**

```
[开始] → [LLM: 提取竞品名称和关键指标]
       → [工具: 谷歌搜索 × 3（并行）]
       → [LLM: 综合信息生成报告]
       → [结束]
```

Dify 的工作流画布支持拖拽节点、连线、设置条件分支。具体操作：

- **LLM 节点**：在节点设置中选择模型，编写 Prompt，定义输入变量（从前序节点传递过来）
- **工具节点**：Dify 提供 50+ 内置工具（Google 搜索、DALL·E、Stable Diffusion、WolframAlpha 等），也可以添加自定义 HTTP 工具来调用任意外部 API
- **条件分支**：如果搜索结果为空，跳转到「补充搜索」分支；否则进入报告生成分支

**Step 3：配置变量传递**

工作流节点之间的数据传递通过变量实现。第一个 LLM 节点的输出 `company_name` 成为第二个工具节点的输入；多个搜索工具的输出汇聚到一个数组变量 `search_results` 中，供最后的报告生成节点使用。

**Step 4：运行测试**

点击「试运行」按钮，输入一个竞品名称，观察每个节点的执行状态和输出。流式日志会实时显示工作流各节点的执行进度，便于定位问题。

### 4.3 场景三：LLMOps——基于生产数据进行 Prompt 优化

Dify 把生产环境的用户对话完整记录下来，这为持续的 Prompt 优化提供了数据基础。

**查看日志与分析**

在「日志」页面，可以查看每一条对话的完整记录：用户输入 → 完整 Prompt → 模型输出 → Token 消耗 → 响应时间。

对于需要改进的对话，可以点击「标注」按钮，添加人工反馈（「回答不准确」「信息过时」「格式不规范」），这些标注数据可以导出用于 fine-tuning 或作为评估集。

**批量测试 Prompt 变体**

Dify 支持在「日志」页面对同一条用户输入，用不同的 Prompt 版本做 A/B 对比测试。如果你的团队在探索更好的 Prompt 表达方式，这个功能可以让你用真实用户 query 来快速验证效果差异。

## 5. 开发扩展

### 5.1 自定义工具开发

Dify 的工具系统基于 [MCP（Model Context Protocol）](https://modelcontextprotocol.io/) 构建，支持通过 HTTP 请求调用任意外部 API。开发一个自定义工具只需要几步：

**Step 1：定义工具元信息**

在「工具」→「自定义工具」中新建工具，填写基本信息（名称、描述、图标）。

**Step 2：编写接口定义**

```json
{
  "schema": {
    "name": "get_weather",
    "description": "查询指定城市的当前天气",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {
          "type": "string",
          "description": "城市名称，如北京、上海"
        },
        "unit": {
          "type": "string",
          "enum": ["celsius", "fahrenheit"],
          "default": "celsius"
        }
      },
      "required": ["city"]
    }
  }
}
```

**Step 3：配置调用逻辑**

填写目标 API 的地址、认证方式（API Key / Bearer Token / 无认证），以及请求体的构造方式。Dify 支持将用户输入的对话参数自动映射到 API 请求参数中。

**Step 4：测试与发布**

在工具配置页面填写测试参数，验证 API 调用结果。确认正常后，该工具即可在工作流和 Agent 中使用。

### 5.2 API 集成与二次开发

Dify 提供完整的 REST API，所有在 UI 上能完成的操作都可以通过 API 实现。API 遵循 OpenAI 的接口规范，与现有 LLM 应用生态高度兼容。

**应用管理 API**

```bash
# 创建应用
curl -X POST "https://your-dify-instance/v1/apps" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "竞品分析助手",
    "description": "自动完成竞品信息收集与分析报告生成",
    "app_type": "agent",
    "icon": "🤖"
  }'

# 获取应用详情
curl "https://your-dify-instance/v1/apps/{app_id}" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**消息发送 API**

```python
import openai

client = openai.OpenAI(
    api_key="YOUR_DIFY_API_KEY",
    base_url="https://your-dify-instance/v1"
)

response = client.chat.completions.create(
    model="draft-app",
    messages=[
        {"role": "user", "content": "帮我分析下智谱 AI 的最新动态"}
    ],
    stream=True,
    user="user-id-123"
)

for chunk in response:
    print(chunk.choices[0].delta.content, end="", flush=True)
```

Dify 的 API 在设计上大量保留了 OpenAI SDK 的接口约定，因此主流的 LLM 调用代码只需要修改 base URL 和 API Key 即可无缝迁移到 Dify。

### 5.3 插件机制

Dify v1.0+ 引入了插件（Plugin）系统，允许开发者以插件形式扩展平台能力，而不需要修改 Dify 核心代码。官方提供了几个插件示例，包括：

- **SAML SSO**：对接企业身份提供商（Okta、Azure AD 等）
- **自定义模型**：接入 Dify 官方未直接支持的模型服务
- **Webhook 增强**：在特定事件（应用创建/用户注册/超用量）触发自定义业务逻辑

插件开发文档位于 Dify 官方文档的「扩展开发」章节，涉及 Python 打包、权限声明和生命周期钩子等标准插件机制。

## 6. 总结与进阶路线

Dify 做的事情很明确：把 LLM 应用从原型到生产这条路上最重复的工程工作——模型切换、流程编排、日志追踪、租户管理——封装成开箱即用的平台能力。对多数团队来说，基于 Dify 起步比从零搭建基础设施更务实，省下的时间可以花在真正拉开差距的地方：Prompt 设计和业务流程设计。

**继续深入的路径：**

1. **官方文档**：docs.dify.ai 覆盖从快速入门到高级配置的每一个细节
2. **GitHub Discussions**：社区活跃，遇到问题基本能找到前人的解决方案
3. **工作流设计模式**：DAG 编排、条件分支、循环处理等高级工作流特性，是用好 Dify 的关键
4. **RAG 深入**：向量检索质量直接决定问答效果，建议系统学习 Embedding 模型选择、分块策略、混合检索
5. **贡献社区**：Dify 的插件生态还处于早期，现在是参与贡献自定义工具和插件的好时机

Dify 的开源协议基于 Apache 2.0，额外增加了一些条件（主要限制商用时请勿直接用 Dify 品牌做产品化），具体请参考 [LICENSE](https://github.com/langgenius/dify/blob/main/LICENSE) 文件。对于希望将 Dify 能力集成到商业产品中的团队，也可以联系官方了解企业版授权。