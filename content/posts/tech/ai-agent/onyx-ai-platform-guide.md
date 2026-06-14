---
title: "Onyx 中文指南：自托管 AI 对话平台的入门到精通"
date: "2026-03-28T13:30:00+08:00"
slug: "onyx-ai-platform-guide"
aliases:
  - /posts/tech/onyx-ai-platform-guide/
description: "Onyx 是一个功能丰富的自托管 AI 对话平台，支持任意 LLM、RAG、知识图谱、MCP 集成和代码执行。本文从原理到实践全面讲解。"
draft: false
categories: ["技术笔记"]
tags: ["Onyx", "RAG", "AI Agent", "MCP", "自托管"]
---

# Onyx 中文指南：自托管 AI 对话平台的入门到精通

> 预计阅读时间：35 分钟 | 难度：⭐⭐⭐⭐

---

> **目标读者**：对 AI 对话平台有兴趣的开发者与团队
> **前置知识**：Docker 基础、Python 基础、对 LLM 有基本认知
> **预计阅读时间**：45 分钟
> **项目地址**：https://github.com/onyx-dot-app/onyx
> **最新版本**：v3.0.5（2026 年 3 月 25 日）

---

## 章节导航

| 小节 | 主题 | 难度 |
|------|------|------|
| §1 | 学习目标 | ⭐ |
| §2 | 原理分析：为什么需要 Onyx 这样的平台 | ⭐⭐ |
| §3 | 架构分析：前端 / 后端 / 数据流 | ⭐⭐⭐ |
| §4 | 核心功能详解 | ⭐⭐⭐ |
| §5 | 安装与部署（Docker / Kubernetes） | ⭐⭐ |
| §6 | 使用指南：从快速开始到高级配置 | ⭐⭐⭐ |
| §7 | 开发扩展：自定义 Agent 与 MCP 集成 | ⭐⭐⭐⭐ |
| §8 | 推荐做法 | ⭐⭐⭐⭐ |
| §9 | 常见问题（FAQ） | ⭐⭐ |

---

## §1 学习目标

完成本文后，可以：

- [ ] 理解 Onyx 的核心定位与适用场景
- [ ] 读懂 Onyx 的整体架构设计
- [ ] 掌握 Docker 与 Kubernetes 两种部署方式
- [ ] 独立完成 Onyx 的安装、配置与首次运行
- [ ] 理解 RAG 混合搜索与知识图谱的工作原理
- [ ] 配置 Web Search、Connectors 与数据源连接
- [ ] 构建自定义 Agent 并集成 MCP 工具
- [ ] 运用推荐做法保障生产环境的稳定性与安全

---

## §2 原理分析：为什么需要 Onyx 这样的平台

### 2.1 从「能用」到「好用」的距离

大语言模型（LLM）在 2022 年底的爆发，让无数团队开始尝试将 AI 能力集成到自己的产品或工作流中。直接调用 API 是最简单的方式——但在真实场景中，光靠 API 远远不够：

- **数据隔离**：企业内部的文档、技术方案、会议记录往往涉及机密，无法上传到第三方 API
- **知识时效**：通用 LLM 的知识有截止日期，而企业内部信息每天都在更新
- **工具联动**：AI 需要能够查邮件、操作数据库、搜索内网、调用内部 API——这远超出纯对话的范畴
- **多模型切换**：不同场景需要不同的模型（有的任务用 GPT-4 性价比更高，有的用 Claude，有的用开源模型）

于是，如何让 AI 真正「接入」真实世界，成了下一个核心问题。**Onyx 就是这个问题的答案之一**——一个可以自托管、功能完备、扩展性强的 AI 对话与智能体平台。

### 2.2 Onyx 解决了什么问题

| 问题 | 现状（无 Onyx） | 使用 Onyx 后 |
|------|----------------|--------------|
| 数据隐私 | 文档必须上传第三方 API，存在泄露风险 | 完全本地部署，数据不出内网 |
| 知识检索 | AI「遗忘」企业内部信息 | RAG 混合搜索，实时检索企业知识库 |
| 工具调用 | 每个工具都要单独开发集成 | MCP 协议统一接入，40+ 官方连接器开箱即用 |
| 多模型管理 | 混用多个平台，配置混乱 | 一个界面管理所有 LLM 连接 |
| 协作与权限 | 对话无法共享，权限难以控制 | 内置团队协作、RBAC 权限与用量分析 |

### 2.3 定位

Onyx 的官方定位是：

> **A feature-rich, self-hostable Chat UI that works with any LLM.**

这句话有几个关键词需要逐一拆解：

- **Feature-rich（功能丰富）**：不止是聊天界面，还包括 Agent、RAG、Search、Actions、MCP 等完整生态
- **Self-hostable（可自托管）**：支持 Docker、Kubernetes 等部署方式，完全私有化
- **Works with any LLM（兼容任意 LLM）**：OpenAI、Anthropic、本地开源模型都可以接入

### 2.4 竞品对比

在同类自托管 AI 平台中，Onyx 的差异化优势非常明显：

| 特性 | Onyx | LangFlow | Dify | Flowise |
|------|------|----------|------|---------|
| 部署复杂度 | ⭐⭐ 中等 | ⭐⭐⭐ 较高 | ⭐ 简单 | ⭐ 简单 |
| RAG 能力 | ⭐⭐⭐⭐⭐ 混合搜索+知识图谱 | ⭐⭐⭐ 基础 RAG | ⭐⭐⭐ 基础 RAG | ⭐⭐ 基础 |
| MCP 支持 | ✅ 原生支持 | ❌ 不支持 | ❌ 部分支持 | ❌ 不支持 |
| 企业级功能（SSO/RBAC） | ✅ 完整 | ❌ 不支持 | ⚠️ 部分 | ❌ 不支持 |
| 代码解释器 | ✅ 支持 | ❌ 不支持 | ❌ 不支持 | ❌ 不支持 |
| 开源协议 | MIT | MIT | Apache 2.0 | Apache 2.0 |

---

## §3 架构分析：前端 / 后端 / 数据流

### 3.1 技术栈概览

Onyx 采用了多语言混合技术栈，这是由其丰富的功能模块决定的：

| 语言 | 占比 | 主要用途 |
|------|------|----------|
| Python | 63.3% | 核心后端逻辑、RAG 处理、Agent 引擎 |
| TypeScript | 31.2% | 前端界面（Next.js）、API 客户端 |
| Go | 1.6% | 高性能工具、数据处理管道 |

### 3.2 整体架构图

```mermaid
graph TD
    subgraph Client["客户端层"]
        WebUI["Web UI (Next.js/TypeScript)"]
        API_Client["API Client SDK"]
    end

    subgraph Gateway["网关层"]
        Nginx["Nginx / 反向代理"]
        Auth["认证服务 (SSO/RBAC)"]
    end

    subgraph Backend["后端服务 (Python)"]
        Agent_Engine["Agent 引擎"]
        RAG_Pipeline["RAG 处理流水线"]
        Search_Service["搜索服务"]
        Action_Executor["动作执行器"]
        Code_Interpreter["代码解释器"]
        MCP_Server["MCP 服务器"]
    end

    subgraph Data["数据层"]
        Vector_DB["向量数据库<br/>(Milvus/Pinecone/Qdrant)"]
        KG["知识图谱数据库"]
        Postgres[(PostgreSQL)]
        Redis[(Redis 缓存)]
        S3["对象存储 (S3/MinIO)"]
    end

    subgraph External["外部服务"]
        LLM["LLM 提供商<br/>(OpenAI/Anthropic/本地)"]
        Search_API["搜索引擎 API<br/>(Google PSE/Exa/Serper)"]
        Crawler["爬虫服务<br/>(Firecrawl/自研)"]
    end

    WebUI --> Nginx
    API_Client --> Nginx
    Nginx --> Auth
    Auth --> Agent_Engine
    Agent_Engine --> RAG_Pipeline
    Agent_Engine --> Action_Executor
    Agent_Engine --> Code_Interpreter
    Agent_Engine --> Search_Service
    RAG_Pipeline --> Vector_DB
    RAG_Pipeline --> KG
    Agent_Engine --> MCP_Server
    Search_Service --> Search_API
    Search_Service --> Crawler
    Agent_Engine --> LLM
    Action_Executor --> External
    Postgres --> Redis
    Postgres --> S3
```texttext
用户: "帮我分析过去一周的销售数据，并画一张趋势图"

┌─────────────────────────────────────────────────────────────┐
│ 1. 认证鉴权                                                │
│    Nginx → Auth Service → JWT Token 验证                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. 请求路由                                                │
│    Web UI → Agent Engine → 解析用户意图                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. 工具规划                                                 │
│    Agent 判断需要：                                        │
│    ① 数据库查询（Connector）                               │
│    ② 代码执行（Code Interpreter）                          │
│    ③ 图表渲染（Code Interpreter）                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. 并行执行                                                 │
│    ┌──────────────┐  ┌──────────────┐                     │
│    │ Connector    │  │ MCP Tool     │                     │
│    │ 查询销售数据  │  │ 调用内部 API │                     │
│    └──────────────┘  └──────────────┘                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. RAG 增强（如需）                                         │
│    向量检索 + 关键词检索 → 混合打分 → 上下文注入           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. LLM 推理                                                 │
│    将工具返回结果 + RAG 上下文 + 对话历史 → LLM → 回答    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. 后处理                                                   │
│    Code Interpreter 执行 Python → 生成图表 → 返回给用户    │
└─────────────────────────────────────────────────────────────┘
                            ↓
用户 ← 最终回答（含图表）
```textbash
# 在 Onyx 配置文件中设置
WEB_SEARCH_PROVIDER=google_pse
GOOGLE_PSE_API_KEY=your_api_key
GOOGLE_PSE_ENGINE_ID=your_engine_id
```textpython
# 伪代码：混合搜索融合逻辑
def hybrid_search(query, top_k=10, alpha=0.7):
    # alpha 控制向量检索权重（1-alpha 控制 BM25 权重）
    vector_results = vector_search(query, top_k=top_k * 2)
    bm25_results = bm25_search(query, top_k=top_k * 2)

    # Reciprocal Rank Fusion（RRF）融合
    fused_results = rrf_fusion(vector_results, bm25_results, alpha=alpha)
    return fused_results[:top_k]
```text
Score(d) = Σ 1 / (k + rank_i(d))

其中：
- d = 文档
- k = 平滑因子（通常为 60）
- rank_i(d) = 该文档在第 i 个检索结果列表中的排名
```textbash
# 环境变量配置
CONNECTOR_POSTGRES_ENABLED=true
CONNECTOR_POSTGRES_HOST=localhost
CONNECTOR_POSTGRES_PORT=5432
CONNECTOR_POSTGRES_DB=mydb
CONNECTOR_POSTGRES_USER=onyx_user
CONNECTOR_POSTGRES_PASSWORD=secure_password
```textyaml
# Action 定义示例
name: "查询销售数据"
description: "从 PostgreSQL 查询指定时间范围的销售记录"
connector: "postgresql"
operation: "execute_query"
params:
  sql: "{{ temporal_query }}"
  timeout: 30s
output:
  type: "table"
  format: "json"
```texttypescript
// MCP Server 配置示例
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/data"],
      "description": "访问 /data 目录下的文件"
    },
    "brave-search": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-brave-search", "YOUR_API_KEY"],
      "description": "网络搜索能力"
    }
  }
}
```text
用户：分析 sales_data.csv 并绘制月度趋势图

Onyx 内部：
1. 读取 /uploads/sales_data.csv
2. 执行 Python 脚本：
   ```python
   import pandas as pd
   import matplotlib.pyplot as plt

   df = pd.read_csv('/uploads/sales_data.csv')
   monthly = df.groupby(df['date'].dt.to_period('M'))['amount'].sum()
   monthly.plot(kind='bar')
   plt.savefig('/tmp/monthly_sales.png')
   ```text

### 4.8 Image Generation（图像生成）

Onyx 集成了主流图像生成模型（支持 DALL-E、Stable Diffusion 等），可以在对话中直接根据提示词生成图像：

```bash
# 配置图像生成
IMAGE_GENERATION_PROVIDER=openai  # 或 stable-diffusion, anthropic
IMAGE_GENERATION_API_KEY=your_api_key
```textbash
curl -fsSL https://onyx.app/install_onyx.sh | bash
```textbash
git clone https://github.com/onyx-dot-app/onyx.git
cd onyx
```textbash
# 复制配置文件
cp .env.example .env

# 编辑配置文件
vim .env
```textbash
# ===== 基础配置 =====
POSTGRES_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password

# ===== LLM 配置（至少选一个）=====
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# ===== 向量数据库 =====
VECTOR_DB_TYPE=qdrant  # 可选：milvus, pinecone, qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# ===== Web 搜索（可选）=====
WEB_SEARCH_PROVIDER=google_pse
GOOGLE_PSE_API_KEY=your_key
GOOGLE_PSE_ENGINE_ID=your_engine_id

# ===== 文件存储 =====
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=onyx
```textbash
# 启动所有服务（后台运行）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f onyx-backend
```textbash
# 添加 Helm 仓库
helm repo add onyx https://charts.onyx.app
helm repo update

# 安装 Onyx
helm install onyx onyx/onyx \
  --namespace onyx \
  --create-namespace \
  --values values.yaml
```textyaml
# values.yaml
replicaCount: 3

image:
  repository: onyx/onyx
  tag: "v3.0.5"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8080

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: onyx.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: onyx-tls
      hosts:
        - onyx.example.com

resources:
  requests:
    cpu: 500m
    memory: 2Gi
  limits:
    cpu: 2000m
    memory: 8Gi

persistence:
  enabled: true
  storageClass: "gp3"
  size: 50Gi

postgresql:
  enabled: true
  auth:
    password: "your_secure_password"
  primary:
    persistence:
      size: 20Gi

redis:
  enabled: true
  auth:
    password: "your_redis_password"

config:
  openaiApiKey: "sk-..."
  anthropicApiKey: "sk-ant-..."
  vectorDbType: "qdrant"
  s3Endpoint: "http://minio:9000"
  s3AccessKey: "minioadmin"
  s3SecretKey: "minioadmin"
```texthcl
# main.tf
module "onyx" {
  source  = "onyx-dot-app/onyx/aws"
  version = "1.0.0"

  cluster_name = "onyx-eks"
  region       = "us-west-2"

  # EKS 配置
  eks_node_instance_type = "m6i.xlarge"
  eks_desired_capacity   = 3
  eks_min_size           = 2
  eks_max_size           = 10

  # Onyx 配置
  onyx_domain      = "onyx.example.com"
  onyx_ssl_enabled = true

  # 外部 LLM（不推荐在 Terraform 中硬编码密钥，建议使用 Secrets Manager）
}
```text
首次使用向导
├── 1. 创建管理员账户
├── 2. 配置 LLM 提供商（至少一个）
│     ├── OpenAI（最简单，推荐新手）
│     ├── Anthropic（效果最好）
│     ├── Azure OpenAI（企业内网）
│     └── 本地模型（Ollama/vLLM）
├── 3. 配置向量数据库
├── 4. 配置文件存储（S3/MinIO）
├── 5. 测试连接
└── 6. 开始使用
```textbash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_DEFAULT_MODEL=gpt-4o
```textbash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_DEFAULT_MODEL=claude-sonnet-4-20250514
```textbash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3.3:latest
```textbash
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-06-01
```textmarkdown
   你是一个专业的技术支持助手，名为「技术支持助手」。

   你的职责：
   - 回答用户关于产品功能、技术规格的问题
   - 提供故障排除步骤
   - 指导用户进行配置和操作

   回答原则：
   - 简洁清晰，直接给出答案
   - 如需更多信息，先明确告知用户缺少什么
   - 如果不确定，坦诚说明，不要编造答案
   ```textpython
# /onyx/backend/onyx/actions/weather.py
from onyx.actions.base import Action, ActionConfig, ActionResult
from typing import Optional
import httpx

class WeatherAction(Action):
    """查询指定城市的天气信息"""

    name = "weather_query"
    description = "获取指定城市的当前天气和预报"

    config = ActionConfig(
        parameters={
            "city": {
                "type": "string",
                "description": "城市名称（中文或英文）",
                "required": True,
            },
            "days": {
                "type": "integer",
                "description": "预报天数（1-7）",
                "required": False,
                "default": 3,
            }
        },
        timeout=10,
        retry=2,
    )

    async def execute(self, city: str, days: int = 3) -> ActionResult:
        api_key = self.get_secret("WEATHER_API_KEY")
        url = f"https://api.weather.com/v3/wx/conditions/current"

        params = {
            "city": city,
            "days": days,
            "apikey": api_key,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=self.config.timeout)
            data = response.json()

        return ActionResult(
            success=True,
            data={
                "city": city,
                "current": data.get("current"),
                "forecast": data.get("forecast")[:days],
            },
            message=f"已获取 {city} 的天气信息",
        )
```textpython
# /onyx/backend/onyx/actions/__init__.py
from onyx.actions.weather import WeatherAction

ACTION_REGISTRY = {
    "weather_query": WeatherAction,
    # ... 其他 actions
}
```textbash
npm install -g @modelcontextprotocol/server-brave-search
```textjson
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-brave-search", "YOUR_BRAVE_API_KEY"],
      "description": "网络搜索，支持实时新闻和信息检索"
    },
    "filesystem": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/data/onyx-files"],
      "description": "访问 Onyx 文件存储目录"
    },
    "slack": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-slack"],
      "description": "Slack 消息发送和频道读取"
    }
  }
}
```text
请搜索「Onyx AI 最新版本」并告诉我结果
```textpython
# /onyx/backend/onyx/connectors/custom_jira.py
from onyx.connectors.base import Connector, Document, Credentials

class CustomJiraConnector(Connector):
    """Jira Issue 连接器"""

    name = "
    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.jira_url = credentials.get("jira_url")
        self.api_token = credentials.get("api_token")
        self.email = credentials.get("email")

    async def load_documents(self, query: str | None = None) -> list[Document]:
        """从 Jira 加载 Issues 作为文档"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.jira_url}/rest/api/3/search",
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Accept": "application/json",
                },
                params={
                    "jql": query or "project = MYPROJECT ORDER BY updated DESC",
                    "maxResults": 50,
                },
            )
            data = response.json()

        documents = []
        for issue in data.get("issues", []):
            doc = Document(
                id=issue["id"],
                title=issue["fields"]["summary"],
                content=issue["fields"]["description"]
                + f"\nStatus: {issue['fields']['status']['name']}",
                metadata={
                    "type": "jira_issue",
                    "key": issue["key"],
                    "status": issue["fields"]["status"]["name"],
                },
            )
            documents.append(doc)

        return documents

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.jira_url}/rest/api/3/myself",
                    headers={"Authorization": f"Bearer {self.api_token}"},
                )
                return r.status_code == 200
        except Exception:
            return False
```textpython
from onyx.connectors.custom_jira import CustomJiraConnector

CONNECTOR_REGISTRY = {
    # ... 官方 connectors
    "custom_jira": CustomJiraConnector,
}
```textyaml
# Webhook 配置示例
webhooks:
  - name: "notification_to_slack"
    trigger: "agent_response"
    url: "https://hooks.slack.com/services/xxx"
    events:
      - on_response_complete
      - on_error
    headers:
      Content-Type: "application/json"
    body_template: |
      {
        "text": "Onyx Agent 响应完成",
        "attachment": {
          "title": "{{ agent_name }}",
          "text": "{{ response_summary }}"
        }
      }
```textmermaid
graph TD
    User1["用户 A"] --> LB["负载均衡器"]
    User2["用户 B"] --> LB
    User3["用户 C"] --> LB

    LB --> Nginx1["Nginx x2"]
    LB --> Nginx2

    Nginx1 --> Onyx1["Onyx Backend x3"]
    Nginx2 --> Onyx2["（副本）"]
    Nginx1 --> Onyx3["（副本）"]

    Onyx1 --> Postgres[(PostgreSQL<br/>主从复制)]
    Onyx2 --> Postgres
    Onyx3 --> Postgres

    Onyx1 --> Redis[(Redis Cluster)]
    Onyx2 --> Redis
    Onyx3 --> Redis

    Onyx1 --> VectorDB[(向量数据库<br/>集群模式)]
    Onyx2 --> VectorDB
    Onyx3 --> VectorDB

    Postgres -.-> Backup["备份存储 S3"]
    VectorDB -.-> Backup
```textmarkdown
# ❌ 模糊不清
你是一个 AI，帮助用户完成任务。

# ✅ 角色 + 职责 + 约束
你是「技术支持助手」，专门回答用户关于 [产品名] 的技术问题。
- 只回答产品功能、配置和故障排除相关问题
- 如果问题超出产品范围，明确告知「这个问题我无法回答」
- 需要重启服务时，先告知用户影响范围，再给出步骤
```textmarkdown
回答时遵循以下格式：
1. 直接回答问题（1-2 句话）
2. 如需详细说明，用编号列表
3. 涉及操作步骤时，每步单独一行
4. 结尾附上「需要进一步帮助请说『继续』」
```textmarkdown
当用户询问产品功能时，优先从知识库中检索相关信息。
检索不到时，基于你的知识回答，但明确告知「此信息来自通用知识，未在官方文档中确认」。
```textpython
# 在 Onyx 配置中启用 PII 过滤
PII_FILTER_ENABLED=true
PII_FILTER_STRENGTH=high  # high / medium / low

# 过滤类型
PII_TYPES=email,phone,id_card,credit_card,bank_account
```textbash
# Docker Compose 升级
docker-compose pull
docker-compose up -d
# 查看版本
docker-compose exec onyx-backend onyx --version

# Kubernetes Helm 升级
helm upgrade onyx onyx/onyx --version 3.0.6

# 重要：升级前请阅读 Release Notes，确认是否有破坏性变更
```textyaml
# 模型路由配置示例
model_routing:
  - condition: "intent == 'quick_question'"
    model: "gpt-4o-mini"
    temperature: 0.3
  - condition: "intent == 'deep_analysis'"
    model: "claude-opus-4"
    temperature: 0.7
  - condition: "intent == 'code_generation'"
    model: "gpt-4o"
    temperature: 0.2
```

### Q9：遇到问题如何获取帮助？

**A**：按以下优先级获取帮助：

1. **官方文档**：[https://docs.onyx.app](https://docs.onyx.app) — 最权威的资料来源
2. **GitHub Issues**：[https://github.com/onyx-dot-app/onyx/issues](https://github.com/onyx-dot-app/onyx/issues) — 查是否已有解决方案
3. **GitHub Discussions**：[https://github.com/onyx-dot-app/onyx/discussions](https://github.com/onyx-dot-app/onyx/discussions) — 社区讨论
4. **Discord 社区**：[https://discord.gg/onyx](https://discord.gg/onyx) — 实时交流
5. **企业支持**：如果是企业版用户，联系你的专属支持工程师

### Q10：Onyx 能完全离线部署吗？

**A**：可以。Onyx 支持完全气隙（Air-Gapped）部署：

1. 下载所有 Docker 镜像和 Helm Chart
2. 配置 `OFFLINE_MODE=true`
3. 使用本地模型（Ollama/vLLM 导入 GGUF 文件）
4. 配置内网 S3 替代（MinIO）
5. 使用内网 PostgreSQL 和 Redis

---

## 扩展阅读

| 资源 | 链接 | 说明 |
|------|------|------|
| 官方文档 | [https://docs.onyx.app](https://docs.onyx.app) | 最权威的安装、配置、API 文档 |
| GitHub 仓库 | [https://github.com/onyx-dot-app/onyx](https://github.com/onyx-dot-app/onyx) | 源码、Issue、PR |
| Release Notes | [GitHub Releases](https://github.com/onyx-dot-app/onyx/releases) | 各版本变更说明 |
| MCP 协议文档 | [https://modelcontextprotocol.io](https://modelcontextprotocol.io) | MCP 官方规范 |
| RAG 技术详解 | [Onyx Blog](https://blog.onyx.app) | RAG 原理与推荐做法文章 |
| 视频教程 | [YouTube: Onyx](https://youtube.com/@onyx) | 官方安装和使用教程 |

---

**文档元信息**

难度：⭐⭐⭐⭐⭐ | 类型：入门到精通 | 更新日期：2026-03-28 | 预计阅读时间：45 分钟
