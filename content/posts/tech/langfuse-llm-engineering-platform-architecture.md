---
title: "Langfuse：25K Stars 开源 LLM 工程平台，架构设计与集成实践解析"
date: "2026-04-23T14:00:00+08:00"
slug: "langfuse-llm-engineering-platform-architecture"
description: "YC W23 孵化的 25K+ Stars 开源 LLM 工程平台。本文解析：Monorepo 架构、PostgreSQL+ClickHouse 双数据库、OpenTelemetry 追踪模型、事件摄取流水线及主流框架集成。"
draft: false
categories: ["技术笔记"]
tags: ["Langfuse", "LLMOps", "LLM Observability", "OpenTelemetry", "ClickHouse", "PostgreSQL", "LangChain", "Traces", "Evals"]
---

# Langfuse：25K Stars 开源 LLM 工程平台，架构设计与集成实践解析

## 一、为什么需要 Langfuse？

LLM 应用开发与传统软件有本质区别：AI 输出的不确定性、多步骤 Agent 的复杂调用链路、海量 Prompt 版本迭代需求，以及"效果到底好不好"这个难以量化的问题。

Langfuse 解决的是 LLM 工程中四个具体问题：

- **观测（Observability）**：LLM 调用长什么样？Token 消耗多少？延迟多长？哪一步出错了？
- **评估（Evaluation）**：上线前后的效果对比如何量化？用户反馈如何自动化收集？
- **管理（Management）**：Prompt 如何版本控制？跨团队如何共享？
- **调试（Debugging）**：一次复杂的 Agent 对话，如何定位是哪一步出了问题？

Langfuse 最初于 2023 年 5 月开源，获得 Y Combinator W23 孵化，GitHub  Stars 已突破 **25,757**，成为 LLM 工程化领域最活跃的开源项目之一。

> 📌 **数据卡片**：Langfuse 是目前 GitHub 上 Stars 最多的开源 LLM 观测平台，超越 Phoenix（Amlabs）、Weave（Weights & Biases）等竞品。

## 二、整体架构：TypeScript Monorepo

### 2.1 Monorepo 结构

Langfuse 采用 **pnpm Workspace** 构建 Monorepo，核心目录结构如下：

```
langfuse/
├── web/                    # Next.js 14 前端应用
│   └── src/
│       ├── app/            # Next.js App Router
│       ├── features/        # 按功能模块划分的 Feature 目录
│       ├── server/          # 服务端 API 逻辑
│       └── workers/         # 后台任务处理器
├── packages/
│   └── shared/             # 核心共享包（后端逻辑、数据访问）
│       └── src/
│           ├── server/     # 核心服务端逻辑
│           │   ├── ingestion/     # 事件摄取
│           │   ├── llm/          # LLM 调用处理
│           │   ├── otel/         # OpenTelemetry 处理
│           │   ├── datasets/     # 数据集管理
│           │   └── ...
│           ├── clickhouse/ # ClickHouse 迁移脚本
│           ├── prisma/     # Prisma Schema（PostgreSQL）
│           └── encryption/  # 加密工具
├── worker/                 # 独立 Worker 进程（后台任务）
├── ee/                     # 企业版功能
└── fern/                   # API 文档 OpenAPI 规范
```

**关键设计决策**：Langfuse 没有将前后端分离为独立 Repo，而是将所有代码放在一个 Monorepo 中，通过 pnpm Workspace 实现包共享。这带来两个好处：

1. **类型安全**：前后端共享 `@langfuse/shared` 包，API 的 TypeScript 类型在编译时就能发现不匹配
2. **开发体验**：一次 `pnpm install` 即可配置好完整开发环境

### 2.2 技术栈全景

| 层次 | 技术选型 |
|------|---------|
| 前端框架 | Next.js 14（App Router）+ React |
| UI 组件 | MUI（Material UI） + 自定义组件 |
| 状态管理 | TanStack Query（服务器状态）+ Zustand（客户端状态） |
| 后端框架 | Next.js API Routes + tRPC（类型安全 API） |
| ORM | Prisma（PostgreSQL） |
| 分析数据库 | ClickHouse（trace/observation/score 存储） |
| 消息队列 | Redis + BullMQ |
| 追踪标准 | OpenTelemetry（OTLP） |
| 认证 | NextAuth.js |
| 部署 | Docker Compose / Kubernetes Helm |

## 三、核心数据模型：Trace → Span → Observation

Langfuse 的观测模型遵循 **OpenTelemetry 语义约定**，并在其上构建了更适合 LLM 场景的抽象。

### 3.1 三层数据模型

```
Trace
├── metadata（元数据）
├── session（会话）
├── user（用户）
└── Observations
    ├── Generation（LLM 调用）
    │   ├── model
    │   ├── prompt
    │   ├── completion
    │   ├── inputTokens / outputTokens
    │   ├── latency
    │   └── usage
    ├── Span（一个操作区间）
    │   ├── startTime / endTime
    │   ├── input / output
    │   └── nested Observations
    └── Event（时间点事件）
```

**Trace** 是一次完整请求的顶级容器，比如用户的一次 Agent 对话。**Observation** 是 Trace 中的具体操作节点——Generation 对应 LLM 调用，Span 对应一个有时间跨度的操作（如 RAG 检索），Event 对应一个瞬时事件。

这种层级结构让 Langfuse 能完美还原一个复杂 Agent 的完整执行轨迹。

### 3.2 Prisma Schema：PostgreSQL 中的实体关系

Langfuse 使用 **Prisma ORM** 管理 PostgreSQL 中的核心实体，主要模型包括：

```prisma
model Project {
  id          String   @id @default(cuid())
  orgId       String
  name        String
  retentionDays Int?   // 数据保留天数配置
  hasTraces   Boolean @default(false)

  // 关联
  apiKeys     ApiKey[]
  datasets    Dataset[]
  Prompts     Prompt[]
  Models      Model[]
  EvalTemplates EvalTemplate[]
  scoreConfig ScoreConfig[]
}

model ApiKey {
  id        String   @id @default(cuid())
  projectId String
  key       String   @unique  // 加密存储
  name      String
  expiresAt DateTime?
  project   Project  @relation(fields: [projectId], references: [id])
}

model Prompt {
  id        String   @id @default(cuid())
  projectId String
  name      String   // 如 "customer-support-v2"
  version   Int
  isActive  Boolean
  prompt    String   // 支持模板变量 {{variable}}
  config    Json     // 模型配置（temperature, max_tokens 等）
  project   Project  @relation(...)
}
```

### 3.3 ClickHouse：海量 Trace 的存储引擎

PostgreSQL 存储**元数据**（Project、ApiKey、Prompt 版本等结构化配置），而所有 **Trace、Observation、Score 的具体内容** 均存入 ClickHouse。

这是因为 LLM 应用会产生海量的调用数据：

- 一个中等规模的 AI 产品每天可产生 **数百万条 traces**
- 每条 trace 包含多层的嵌套 spans、完整的 prompt/completion 内容
- 需要做聚合分析（按模型、按时间、按用户的用量统计）

ClickHouse 的列式存储和向量化查询让这类分析查询在秒级完成。Langfuse 的 ClickHouse Schema 包括：

```sql
-- traces 表：存储完整调用链
CREATE TABLE traces (
    id          String,
    project_id  String,
    timestamp   DateTime,
    name        String,
    user_id     String,
    metadata    Map(String, String),
    -- ... 其他字段
) ENGINE = MergeTree()
ORDER BY (project_id, timestamp);

-- observations 表：嵌套的操作节点
CREATE TABLE observations (
    trace_id    String,
    project_id  String,
    type        Enum('GENERATION', 'SPAN', 'EVENT'),
    -- LLM 相关字段
    model       String,
    prompt      String,
    completion  String,
    usage        Map(String, Int64),
    -- ...
) ENGINE = MergeTree();
```

Langfuse 在 `packages/shared/clickhouse/migrations/` 中维护了完整的 ClickHouse 迁移脚本，这也意味着用户可以在自托管时灵活调整 Schema。

## 四、SDK 与集成：应用如何对接 Langfuse

### 4.1 Python SDK

```python
from langfuse import Langfuse

langfuse = Langfuse()

# 追踪一次 LLM 调用
trace = langfuse.trace(name="customer-support")

response = model.chat(
    messages=[{"role": "user", "content": "我想退换货"}]
)

trace.generation(
    name="gpt-4-generation",
    model="gpt-4",
    messages=[...],
    input_tokens=...,
    output_tokens=...,
    # Langfuse 自动计算延迟、成本
)

trace.log(
    name="retrieval",
    span={
        "query": "退货政策",
        "results": [...],
    }
)
```

### 4.2 LangChain 集成

LangChain 提供了原生 Langfuse Callback Handler，无需修改业务代码即可完成插桩：

```python
from langfuse.callback import CallbackHandler
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

langfuse_handler = CallbackHandler(
    user_id="user-123",
    metadata={"session": "support-ticket-456"}
)

llm = ChatOpenAI()
chain = RetrievalQA(llm=llm, retriever=retriever)

# 通过 callback 参数注入 Langfuse
result = chain.invoke(
    "退货政策是什么？",
    config={"callbacks": [langfuse_handler]}
)
```

### 4.3 OpenAI SDK 集成

Langfuse 提供 OpenAI SDK 的**透明替换**，只需修改 import：

```python
# 之前
from openai import OpenAI
client = OpenAI(api_key="...")

# 之后：替换为 Langfuse 的 OpenAI 兼容客户端
from langfuse.openai import OpenAI
client = OpenAI(
    api_key="sk-langfuse-...",
    base_url="https://cloud.langfuse.com/api/public/v1"
)
```

所有 `client.chat.completions.create(...)` 调用自动被 Langfuse 拦截和记录，零代码侵入。

### 4.4 LlamaIndex 集成

```python
from langfuse.callback import CallbackHandler
from llama_index.core import Settings
from llama_index.core.query_engine import RetrieverQueryEngine

Settings.callback_manager.add_handler(CallbackHandler())

query_engine = RetrieverQueryEngine.from_args(...)
response = query_engine.query("退货政策")
# Langfuse 自动记录 RAG retrieval + synthesis 两个阶段
```

## 五、摄取流水线（Ingestion Pipeline）

### 5.1 高并发摄取设计

Langfuse 的摄取 API 需要处理极高的写入吞吐（一个中大型应用可能每秒数百至数千次 LLM 调用）。其设计考虑了以下目标：

- **低延迟**：应用发起的 LLM 调用不应被 Langfuse 显著阻塞
- **高吞吐**：支持每秒百万级事件摄取
- **容错性**：网络抖动或 Langfuse 服务暂时不可用时不应影响主应用

### 5.2 摄取流水线源码解析

Langfuse 的摄取逻辑位于 `packages/shared/src/server/ingestion/`，核心流程：

```
1. 接收事件批次（/api/public/ingestion）
   ↓
2. processEventBatch.ts — 批量解析 + 格式校验
   ↓
3. 采样决策（sampling.ts）— 按配置决定是否采样
   ↓
4. validateAndInflateScore.ts — 评分校验与补全
   ↓
5. ClickHouse 写入（异步，不阻塞响应）
   ↓
6. 返回 200 OK（应用无需等待 ClickHouse 完成）
```

**采样机制**是摄取流水线的关键优化。当流量极大时，存储每一条调用会产生高昂的 ClickHouse 成本。Langfuse 支持基于规则和基于成本的采样策略：

```typescript
// sampling.ts 中的采样逻辑
export function shouldSample(event: TracerEvent, config: SamplingConfig): boolean {
    // 策略1：强制采样（重要用户/生产错误）
    if (config.always.sample === true) return true;

    // 策略2：概率采样（如 10% 流量）
    if (Math.random() < config.sample.rate) return true;

    // 策略3：成本感知采样（低价值调用优先丢弃）
    const estimatedCost = event.usage.totalTokens * config.costPerToken;
    if (estimatedCost < config.sample.minCostThreshold) return false;

    return true;
}
```

### 5.3 异步写入与响应分离

Langfuse 摄取 API 的响应流程：

```typescript
// 摄取 API 伪代码
async function ingestEvents(events: Event[]) {
    // Step 1: 同步验证 + 鉴权（< 5ms）
    await validateApiKey(events[0].publicKey);

    // Step 2: 异步写入 ClickHouse（不阻塞响应）
    ingestQueue.add(() => writeToClickHouse(events));

    // Step 3: 立即返回成功
    return { status: "success", ingested: events.length };
}
```

应用侧的平均摄取延迟 < **10ms**，完全不会对 LLM 调用的主流程产生影响。

## 六、Prompt 管理层：版本控制与热更新

### 6.1 Prompt 版本管理

Langfuse 的 Prompt 管理解决了工程中的核心痛点：**Prompt 也是代码，需要版本控制**。

```typescript
// 从 Langfuse 读取当前活跃版本的 Prompt
const prompt = await langfuse.prompt.get("customer-support-v2");

// Prompt 内容支持模板变量
// "请根据用户 {{user_name}} 的订单 {{order_id}} 回答：{{question}}"

const rendered = prompt.render({
    user_name: "张三",
    order_id: "ORD-2024-001",
    question: "我的快递到哪了？"
});
```

每个 Prompt 有版本号，每次修改会创建新版本（不可变）。历史版本可随时回滚。

### 6.2 服务端缓存：零延迟迭代

Langfuse 在服务端实现了**强缓存策略**，确保 Prompt 迭代不引入额外延迟：

1. **服务端缓存**：Prompt 读取后缓存在 Redis 中，TTL 内无需访问数据库
2. **客户端缓存**：SDK 侧维护本地 Prompt 缓存，基于 hash 检测变化

```typescript
// packages/shared/src/server/prompts/cache.ts
export const PROMPT_CACHE_TTL = 60_000; // 1 分钟

export async function getPrompt(projectId: string, name: string) {
    const cacheKey = `prompt:${projectId}:${name}`;

    const cached = await redis.get(cacheKey);
    if (cached) return JSON.parse(cached);

    const prompt = await db.prompt.findUnique({...});
    await redis.setex(cacheKey, PROMPT_CACHE_TTL, JSON.stringify(prompt));

    return prompt;
}
```

## 七、评估体系：LLM-as-a-Judge

### 7.1 评估模型的多层设计

Langfuse 的评估体系支持多种评分方式：

| 评估类型 | 描述 | 适用场景 |
|---------|------|---------|
| **LLM-as-a-Judge** | 用强模型（如 GPT-4）评估弱模型输出 | 快速自动化评分 |
| **用户反馈收集** | 应用内 👍/👎 按钮 | 真实用户体验数据 |
| **人工标注** | 标注员对特定 case 打分 | 高价值/争议 case |
| **自定义评分函数** | 通过 SDK 编写评分逻辑 | 精确的业务指标 |

### 7.2 Dataset 与 EvalTemplate

Langfuse 的数据集（Dataset）和评估模板（EvalTemplate）支持将测试集管理与评估流水线结合：

```typescript
// 定义评估模板
const template = await langfuse.evalTemplate.create({
    name: "回答质量评估",
    prompt: `你是一个严格的评审员。评估以下回答对问题的帮助程度（1-5分）。
问题：{{question}}
回答：{{answer}}
评分理由：`
});

// 创建数据集（测试用例）
await langfuse.datasetItem.create({
    datasetName: "退货问题集",
    input: { question: "我的订单什么时候发货？" },
    expectedOutput: "应在 24 小时内发货"
});

// 运行评估
const run = await langfuse.eval.run({
    template: "回答质量评估",
    dataset: "退货问题集",
    model: "gpt-4"
});
```

## 八、自托管部署：从 Docker 到 Kubernetes

### 8.1 Docker Compose 单机部署（5 分钟启动）

```bash
git clone https://github.com/langfuse/langfuse.git
cd langfuse

# 复制环境变量配置
cp .env.dev.example .env

# 启动全部服务（PostgreSQL + ClickHouse + Redis + Langfuse）
docker compose up
```

访问 `http://localhost:3000`，即可使用 Langfuse Web UI。

### 8.2 生产级 Kubernetes 部署

Langfuse 提供 Helm Chart，支持 AWS、Azure、GCP 三大云平台的生产部署：

```bash
# 添加 Helm Repo
helm repo add langfuse https://langfuse.github.io/helm-charts
helm repo update

# 部署到 Kubernetes
helm install langfuse langfuse/langfuse \
    --set database.url="postgresql://user:pass@pg:5432/langfuse" \
    --set clickhouse.url="clickhouse://clickhouse:9000" \
    --set redis.url="redis://redis:6379"
```

Helm Chart 默认配置了：
- HPA（Horizontal Pod Autoscaler）自动扩缩容
- PodDisruptionBudget 保证高可用
- 持久化存储（PVC）配置
- TLS 入口配置

### 8.3 环境变量关键配置

```bash
# 数据库
DATABASE_URL=postgresql://langfuse:password@localhost:5432/langfuse
DIRECT_URL=postgresql://langfuse:password@localhost:5432/langfuse_direct

# ClickHouse
CLICKHOUSE_URL=http://localhost:8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=password

# Redis
REDIS_URL=redis://localhost:6379

# Auth
NEXTAUTH_SECRET=your-secret-key
NEXTAUTH_URL=http://localhost:3000

# Langfuse Cloud（可选，用于 License 管理）
LANGFUSE_CLOUD_LICENSE_KEY=...
```

## 九、企业版：多租户隔离与高级功能

Langfuse 的企业版（`ee/` 目录）提供了大规模部署所需的功能：

### 9.1 多租户隔离

企业版支持**完全数据隔离**的多租户架构：

- 每个组织的数据库 Schema 隔离（而非仅逻辑隔离）
- 基于属性的访问控制（ABAC）替代简单的 RBAC
- SOC 2 Type II 合规支持

### 9.2 数据脱敏与合规

在事件摄取阶段，企业版支持**PII 数据自动脱敏**：

```typescript
// packages/shared/src/server/ee/ingestionMasking/
export function maskPII(event: TraceEvent): TraceEvent {
    return {
        ...event,
        metadata: maskFields(event.metadata, ["email", "phone", "ssn"]),
        user_id: hashUserId(event.user_id)  // 不可逆哈希
    };
}
```

### 9.3 私有部署 License 管理

企业版通过 `eeLICENSE_CHECK` 机制验证部署的合法性，确保在无 Internet 连接的环境中也能完成授权校验。

## 十、架构亮点总结

Langfuse 的架构设计在以下几个方面值得学习：

### ✅ 双数据库架构

PostgreSQL（结构化元数据）+ ClickHouse（海量分析数据）的组合，是 LLM 应用观测平台的常见实践。Prisma 管理 PostgreSQL 提供了类型安全的实体操作，ClickHouse 的列式存储让聚合查询极快。

### ✅ 异步非阻塞摄取

应用发起的 LLM 调用不应被观测平台拖慢。Langfuse 通过异步队列 + 快速响应的设计，实现了 < 10ms 的摄取延迟，对主流程零影响。

### ✅ OpenTelemetry 原生支持

Langfuse 的追踪模型与 OpenTelemetry 语义完全兼容，：
- 可以用标准 OTLP 协议将数据导出到其他观测平台（如 Grafana Tempo）
- 可以用 OpenTelemetry SDK 的跨语言支持对接非 JS/TS 应用

### ✅ 框架集成深度

不仅支持 LangChain、LlamaIndex，还支持 DSPy、Instructor、AutoGen 等新兴框架，形成了完整的 LLM 工程工具链生态。

### ✅ Prompt 即代码

将 Prompt 的版本管理、模板变量、热更新与 Git 工作流结合，是 LLM 应用工程化的关键一步。

## 参考链接

- **GitHub**：https://github.com/langfuse/langfuse
- **官方文档**：https://langfuse.com/docs
- **在线 Demo**：https://langfuse.com/demo
- **Langfuse Cloud**：https://cloud.langfuse.com
- **Self-Hosting 指南**：https://langfuse.com/docs/deployment/self-host
- **GitHub Stars**：25,757 ⭐（持续增长中）

🦞 钳岳星君
