---
title: "Langfuse：把 LLM 调用变成可查询、可评分、可回放的对象"
date: "2026-04-23T14:00:00+08:00"
slug: "langfuse-llm-engineering-platform-architecture"
github_repo: "langfuse/langfuse"
description: "Langfuse 是 MIT 许可的开源 LLM 工程平台。本文解析其双容器架构（Web + Worker）、存储层（PostgreSQL + ClickHouse + Redis + S3）、追踪数据模型、摄取流水线及与主流框架的对接，梳理 v3 到 v4 的架构演进，并给出按规模选型的建议。"
draft: false
categories: ["技术笔记"]
tags: ["Langfuse", "ClickHouse", "PostgreSQL", "OpenTelemetry", "LangChain"]
---

# Langfuse：把 LLM 调用变成可查询、可评分、可回放的对象

Langfuse 解决的不是「怎么更顺滑地调模型」，而是把一次 LLM 调用的输入、输出、成本、延迟和错误记录成结构化对象，让它在调试、评估和迭代阶段都能被查询。它把观测（tracing）、评估（evaluation）和 Prompt 管理放进同一套数据模型，这是它和普通日志平台的分界点。

读完你能判断三件事：Langfuse 的写入链路为什么拆成 Web 和 Worker 两段；观测数据为什么丢进 ClickHouse 而不是留在 PostgreSQL；以及你的团队在什么规模下值得接入它。

## 一、它解决的具体问题

LLM 应用和普通后端服务的差异集中在不确定性：输出不固定、调用链路是多步 Agent 嵌套出来的、Prompt 经常改。对应到工程上，Langfuse 覆盖四个场景：

- **观测**：一次调用的模型名、输入输出、token 数、延迟、错误，能不能一眼定位到出错的那一步。
- **评估**：上线前后同一批问题答得如何，能不能量化对比。
- **管理**：Prompt 有没有版本、能不能回滚、团队怎么共用。
- **调试**：一段含工具的 Agent 对话，哪一步结果不对。

四件事的共同前提是先把调用数据规整起来，这就是 Langfuse 的建模目标。

## 二、系统地图：两条执行线，存储层

Langfuse 的架构容易把几条并行机制混在一起看。拆开看其实是「两条执行线」加「存储层」：

```
           ┌──────────────────────────────────────────────┐
           │            Langfuse 部署                       │
           │                                                │
  SDK/API ─▶│  Web（Next.js）     Worker（Express）          │
            │  鉴权/校验/入队 ◀──── 消费队列/写库/执行评估     │
           └──────┬───────────────┬───────────┬───────────┘
                  │队列/缓存       │           │
           ┌──────▼──────┐ ┌──────▼──────┐ ┌──▼──────────────┐
           │  Redis/      │ │ ClickHouse   │ │ S3 / Blob      │
           │  Valkey      │ │ (OLAP 观测)   │ │ (原始事件/多媒体)│
           │  (队列+缓存)  │ │              │ │                │
           └─────────────┘ └─────────────┘ └─────────────────┘
                       PostgreSQL（OLTP 事务）
```

**两条执行线**分别是：

- **Web（Next.js）**：提供 UI 和里外全部 API。应用上报的事件在这里完成鉴权和结构校验，随后写入队列即返回，不在请求线程里做重活。
- **Worker（Express）**：独立进程，专门异步消费队列，执行「写库、跑评估、导出、Prompt 补全」这类后台任务。

**存储层的四个组件**各管一段数据：

| 存储 | 角色 | 存放内容 |
|------|------|---------|
| PostgreSQL | OLTP 事务库 | 用户、组织、项目、API Key、Prompt、数据集、评估配置 |
| ClickHouse | OLAP 分析库 | Trace、Observation、Score 及其聚合查询 |
| Redis / Valkey | 队列 + 缓存 | BullMQ 事件队列；缓存 API Key 与 Prompt |
| S3 / Blob | 对象存储 | 原始摄取事件、多模态附件、大文件导出 |

两条执行线靠 Redis 队列解耦，这是 Langfuse 能扛吞吐的基础。它最初跑在 Vercel 和 Supabase 上，v1、v2 全部数据都在 PostgreSQL，能撑到每分钟数万事件；等头部用户把数据库 IOPS 打满、仪表盘聚合查询变慢之后，才在 2024 年 12 月的 v3 把追踪数据迁到 ClickHouse。2026 年 1 月，ClickHouse 公司收购了 Langfuse；2026 年 3 月，团队公开了 v4 的新数据模型——把观测数据收敛进一张宽表、基本不可变的 ClickHouse 表，消除读路径上的 join 与去重。v4 先在 Cloud 上验证，2026 年 6 月随 v4.0.0 正式发布并开放自托管迁移；v3 的维护期延续到 2027 年 1 月底。

## 三、数据模型：Trace 之下是 Observation

Langfuse 的追踪模型遵循 OpenTelemetry 语义约定，再叠一层面向 LLM 的抽象。

```
Trace（一次请求的顶级容器）
├── metadata / session / user
└── Observation 节点
    ├── Generation（一次 LLM 调用：模型、提示、补全、用量、延迟）
    ├── Span（一段有时间跨度的操作，可嵌套，如 RAG 检索）
    └── Event（一个瞬时事件）
```

差别在 Observation 的粒度：Generation 对应真实的模型往返，Span 是中间步骤，Event 是时间点标记。多步 Agent 的完整轨迹，就是靠这种嵌套结构还原出来的。

**双库分工**：PostgreSQL 只存事务元数据（项目、Key、Prompt、数据集），Observation 的具体内容落在 ClickHouse。这套产品把观测数据放进列式库而不是行式库，是因为 agent 工作负载同时在写量、跟踪深度、分析读三个方向上压存储：单条 trace 可能嵌上千个 operation，行又重（输入输出常是几 MB 大字符串），而查询多是「按项目加时间的高基数组聚合」。列式存储只在投影被过滤到的列上做 IO，多 MB 的输入输出载荷留在磁盘，直到查询真正需要它。

v3 到 v4 的演进把这一思路推到极致：v4 不再维护独立的 traces / observations 两张表，而是把所有观测行写进同一张宽表，并把 user、session、metadata 这类原本挂在 trace 上的属性复制到每一行。代价是写放大，换来的是读路径彻底免 join——任何一条查询都是单表扫描，这也是 ClickHouse 最擅长的形态。

## 四、一次用户消息如何穿过系统

把抽象机制合起来看，最简单的路径是一次普通 LLM 调用的上报：

1. 应用侧用 SDK 或封装好的一次调用，拼成一个完整的 Trace 事件。
2. 事件发到 `POST /api/public/ingestion`，Web 容器做鉴权和结构校验。
3. Web 把原始事件落到 S3，再把 S3 引用推入 Redis / BullMQ 队列，立刻返回成功；应用主线程不被阻塞。
4. Worker 从队列取出引用、读取 S3 原始事件，写 ClickHouse（观测数据）与 PostgreSQL（必要的元数据），供回放和重算。
5. 在 UI 里，同一批事件按 Trace 聚合展示，仪表盘跑的是 ClickHouse 上的聚合查询。

关键点在第 3 步：响应与写入分离。上传方拿到 200 只代表「已收下并排队」，不代表「已落库」，真正写库发生在 Worker。这份解耦让 SDK 侧可以批量合并再上报，短生命周期应用在退出前需要显式 flush。

## 五、与框架的对接方式

Langfuse 提供了两种接入风格：改 import 的零侵入封装，或显式回调。下面三组是文档里最常见、也确实能跑的写法。

**OpenAI SDK（Python 透明替换）**——只换 import，配置走环境变量：

```python
# pip install langfuse
# 环境变量：LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_HOST
# LANGFUSE_HOST 默认 https://cloud.langfuse.com，美国区为 us.cloud.langfuse.com
from langfuse.openai import openai

completion = openai.chat.completions.create(
    name="chat-demo",
    model="gpt-4o",
    messages=[{"role": "user", "content": "写一段关于 Langfuse 的介绍"}],
)
```

**LangChain（回调注入）**——不动链路的搭建逻辑：

```python
from langfuse.callback import CallbackHandler
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

langfuse_handler = CallbackHandler()   # 可选 user_id / metadata 参数

model = ChatOpenAI(model="gpt-4o")
prompt = ChatPromptTemplate.from_template("解释一下 {topic}")
chain = prompt | model

chain.invoke(
    {"topic": "Langfuse 的架构"},
    config={"callbacks": [langfuse_handler]},
)
```

**OpenAI SDK（JS/TS 封装）**——TypeScript 这边基于 OpenTelemetry，需要初始化 LangfuseSpanProcessor：

```typescript
import OpenAI from "openai";
import { observeOpenAI } from "@langfuse/openai";

const openai = observeOpenAI(new OpenAI());

const res = await openai.chat.completions.create({
  model: "gpt-4o",
  messages: [{ role: "user", content: "Langfuse 是什么？" }],
});
```

除了这三类，官方还维护 `@langfuse/otel` 与 OpenTelemetry 协议（OTLP）对接，非 JS/TS 语言可直接上报 OTel span。

**Prompt 管理**——服务端存版本，客户端缓存读取：

```python
from langfuse import Langfuse

langfuse = Langfuse()
# 创建并立即启用一个版本的 Prompt
langfuse.create_prompt(
    name="travel_consultant",
    prompt=template,
    is_active=True,
)
# 读取生产版本，客户端可配置缓存 TTL
p = langfuse.get_prompt("travel_consultant", cache_ttl_seconds=300)
system_message = SystemMessagePromptTemplate.from_template(p.prompt)
```

Prompt 每次修改生成新的不可变版本，历史版本可回滚；服务端用 Redis 缓存，SDK 侧维护本地缓存，两者叠加让迭代不引入额外一次数据库往返。

## 六、摄取与查询怎么扛量

把吞吐放在队列后面，是 Langfuse 的关键设计：

- **写入**：Web 只负责鉴权和入队，Worker 批量消费后写 ClickHouse。ClickHouse 本就适合高吞吐批量插入，配合队列天然契合。
- **查询**：追踪表按「项目 + 时间」排序、按月分区、对高频过滤列建跳数索引，任何查询都带项目和时间过滤，便于剪裁分区。
- **API 契约**：observations / metrics 接口要求时间过滤并用 token 分页。这不是随手加的规矩，而是为了让查询顺着 ClickHouse 的存储剪裁设计，而不是逆着它扫全表。

这是个容易被忽略的取舍：ClickHouse 快，但「无界时间查询」这类对行存很自然的请求在列存上是反模式。

到 v4 这一步更彻底：摄取端废弃了按事件类型的 batch 端点（traces / generations / spans），统一走 OpenTelemetry 协议；读取端只剩 Observations / Metrics v2 这一类按存储剪裁的接口。也就是说，「顺着存储结构设计 API」从建议变成了强制。

## 七、评估：把「效果」变成可执行对象

评估的难点在主观判断，Langfuse 把它拆成几条可配置的通道：

- **LLM-as-a-Judge**：由 Worker 代为调用外部强模型，对固定样本打分，适合自动化回归。
- **用户反馈**：App 内的点赞 / 差评按钮，采集真实体验。
- **人工标注**：标注员对特定 case 打分，适合争议样本。
- **代码评估（Code Evaluator）**：自定义评分脚本，经 CodeEvalDispatcher 派发到独立的 Lambda 运行器执行，避免堵住 Worker。

各通道最终落入统一的 Score 对象，和 Trace、Dataset 挂在一起，评估结果可在仪表盘里与具体 trace 关联回看。

## 八、部署与资源规模

三种部署跑的是同一套代码和 schema，可在任何时候切换：OSS 自托管、企业自托管、Langfuse Cloud。

**本地起一套（Docker Compose）**：

```bash
git clone https://github.com/langfuse/langfuse.git
cd langfuse
cp .env.dev.example .env
docker compose up
```

访问 `http://localhost:3000`。Compose 会一并带起 PostgreSQL、ClickHouse、Redis。

**生产（Kubernetes + Helm）**：

```bash
helm repo add langfuse https://langfuse.github.io/helm-charts
helm repo update
helm install langfuse langfuse/langfuse \
    --set database.url="postgresql://user:pass@pg:5432/langfuse" \
    --set clickhouse.url="clickhouse://clickhouse:9000" \
    --set redis.url="redis://redis:6379"
```

选型时注意三点：一是 ClickHouse 是按磁盘和内存规划的资源大头，观测数据量大时磁盘会花钱；二是若要回放原始事件或存放图片、音频等多模态附件，得配对象存储（S3 或类 S3）；三是整套产品依赖 PostgreSQL + ClickHouse + Redis 三个组件，最少是三件事要拉起来，比单库方案部署成本高一点。

## 九、开源边界与企业版

Langfuse 核心代码是 MIT 许可、无用量上限，云端和自托管跑的是同一套代码与 schema。这是「开源与商业化并存」的典型做法：

- **OSS 自托管**：包含全部产品功能，无 license key，任意扩展、商用。
- **企业版 / Enterprise Edition（EE）**：代码位于独立 `/ee` 目录，以源码形式随仓库分发，但需要 license key 才能运行。影响的是内建：SCIM 身份供应、审计日志、数据保留策略等安全与合规增强。

值得带一句：所谓「企业多租户隔离」如果被描述成「每个组织独享一套数据库 Schema」，是不准确的。Langfuse 的三套部署共用同一 schema，组织间按访问控制隔离数据，企业协议的溢价主要落在安全与合规增强上。

## 十、按规模选型：谁先上、谁可以等

结合观测负担和回报，接入顺序大致是：

1. **已经开始用 LLM 做产品、并在为「某步结果不对」而排查的人**——先用 Langfuse Cloud 免费档，花半小时把 tracing 接上，能立刻看到调用链。这一步几乎零成本。
2. **需要对 Prompt 做版本化或跑自动化评估的团队**——接 Langfuse 的 Prompt Management 与 Evaluation，把「改 Prompt」从口头变成可回滚对象。
3. **有合规、数据主权或大规模用量需求的团队**——再考虑自托管（Docker Compose 起步，按需迁 Helm / Terraform），并按数据量提前规划 ClickHouse 磁盘与对象存储。

可以用「是否需要回头看一次历史调用」当作判断信号：如果只是偶尔查日志，别急着上整套基建；如果每天都要复盘 Agent 的分支、改 Prompt 要对比前后效果，那么当一个可查询、可评分、可回放的调用对象，就值得。

最后补一条时间线：v3 的安全补丁只维护到 2027 年 1 月底。现在才决定接入的团队，直接以 v4 起步（Python SDK v4 / JS SDK v5），没必要在 v3 上重复建设；存量自托管用户把迁移排上日程，升级指南给了两条路——后台自动回填历史数据，或保留双写直到数据保留期自然滚动过去。

## 参考链接

- **GitHub**：https://github.com/langfuse/langfuse
- **官方文档**：https://langfuse.com/docs
- **架构总览（Handbook）**：https://langfuse.com/handbook/product-engineering/architecture
- **ClickHouse 实践（v3 迁移与存储设计）**：https://langfuse.com/resources/engineering/clickhouse-at-agent-scale
- **Self-Hosting 指南**：https://langfuse.com/self-hosting
- **OpenAI 集成（Python）**：https://langfuse.com/docs/openai
- **Observability 入门**：https://langfuse.com/docs/observability/get-started
- **v4 新数据模型（技术深度解析）**：https://langfuse.com/blog/2026-03-10-simplify-langfuse-for-scale
- **v3 到 v4 迁移指南（自托管）**：https://langfuse.com/self-hosting/upgrade/upgrade-guides/upgrade-v3-to-v4
- **ClickHouse 收购公告**：https://langfuse.com/blog/joining-clickhouse