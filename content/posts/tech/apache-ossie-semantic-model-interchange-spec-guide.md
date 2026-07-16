---
title: "apache/ossie 拆解：Apache 孵化中的语义模型互操作规范，如何让 KPI 在 BI / AI agent / dbt 之间不再各说各话"
date: 2026-07-17T02:58:00+08:00
lastmod: 2026-07-17T02:58:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Apache", "Ossie", "Semantic Model", "dbt", "BI"]
description: "Apache Ossie（前身 Open Semantic Interchange）是 Apache 孵化中的厂商中立语义模型互操作规范，0.2.0.dev0 草案阶段。它定义 JSON/YAML 双格式 schema，配套 dbt / GoodData / Polaris / Salesforce 多向 converter，用单一事实源解决同一个 KPI 在不同 BI 工具里口径不同的行业老问题。"
weight: 1
slug: "apache-ossie-semantic-model-interchange-spec-guide"
author: text-matrix
---

## 一句话判断

**Apache Ossie（[apache/ossie](https://github.com/apache/ossie)，前身 Open Semantic Interchange / OSI）是 Apache 软件基金会孵化中的厂商中立语义模型互操作规范**——它的目标是用一份 JSON/YAML 双格式的 schema，让”营收”、”DAU”、”留存率”这类业务指标在 dbt、GoodData、Snowflake、Salesforce、Tableau、PowerBI、AI agent 之间有**唯一可读可写的事实源**，从而根除”同一个 KPI 在每个 BI 工具里被定义一遍、每个月都在人工对账”的行业痛点。843 stars、Apache-2.0、Python 实现 reference converters，当前 spec 版本 `0.2.0.dev0`（draft，0.2.0 之前 schema 可能变化），前 6 个月由社区贡献者推进。

如果你的团队正在为”业务口径在 5 个工具里 5 种定义”或”AI agent 拿不到正确 KPI 定义”这两件事头疼，这篇文章值得读完。

---

## 系统地图

```
┌──────────────────────────────────────────────────────────────────────┐
│                       Apache Ossie 仓库                                │
│                                                                          │
│  ┌─────────────────────┐    ┌────────────────────────────────────┐    │
│  │  core-spec/         │    │  converters/                       │    │
│  │  ─────────────────── │    │  ────────────────────────────────  │    │
│  │  spec.md            │    │  dbt  ↔  Ossie                     │    │
│  │  spec.yaml          │    │  GoodData  ↔  Ossie                 │    │
│  │  osi-schema.json    │    │  Polaris  ↔  Ossie                  │    │
│  │  expression_        │    │  Salesforce  ↔  Ossie              │    │
│  │    language.md      │    │                                      │    │
│  └──────────┬──────────┘    └────────────────┬───────────────────┘    │
│             │                                │                         │
│             │   ┌────────────────────────┐   │                         │
│             │   │  examples/             │   │                         │
│             │   │  ───────────────────── │   │                         │
│             │   │  TPC-DS 完整示例       │   │                         │
│             │   │  sales_analytics       │   │                         │
│             │   │  orders / customers    │   │                         │
│             │   └────────────┬───────────┘   │                         │
│             │                │               │                         │
│             ▼                ▼               ▼                         │
│            ┌──────────────────────────────────────┐                    │
│            │  validation/                          │                    │
│            │  ────────────────────────────────     │                    │
│            │  jsonschema 校验器                   │                    │
│            │  cli 校验                             │                    │
│            └────────────────┬─────────────────────┘                    │
│                             │                                          │
│                             ▼                                          │
│            ┌──────────────────────────────┐                            │
│            │  docs/                       │                            │
│            │  ─────────────────────────── │                            │
│            │  ROADMAP.md                  │                            │
│            │  CONTRIBUTING.md             │                            │
│            │  working groups 文档         │                            │
│            └──────────────────────────────┘                            │
└──────────────────────────────────────────────────────────────────────┘
                          ▼
        ┌─────────────────────────────────────┐
        │  下游消费者                          │
        │  ────────────────────────────────  │
        │  BI 工具（Tableau / Looker / ...） │
        │  dbt / SQL engine                  │
        │  AI agent（LangChain / LlamaIndex） │
        │  数据目录（Atlan / DataHub / ...）  │
        └─────────────────────────────────────┘
```

这张图最重要的一条路径：**spec.md / spec.yaml / osi-schema.json 三份同源文件 + 多向 converters + validation**。spec 是契约，converters 是桥，validation 是守门人，examples 是模板。这种”规范本身小、converters 大”的形态与 Apache Avro / Protobuf 的设计哲学一致。

---

## 边界与角色划分

Ossie 的设计边界可以用 5 条不变项概括：

| 维度 | 不变项 | 含义 |
|------|--------|------|
| 输出格式 | JSON + YAML 双格式 | spec.md 同时落到 `.yaml` 与 `.json` schema；任一工具都能解析 |
| 版本节奏 | 0.2.0.dev0（草案） | 0.2.0 之前 schema 可能 breaking change |
| 方言覆盖 | 7 个 SQL/expression dialect | ANSI_SQL / SNOWFLAKE / MDX / TABLEAU / DATABRICKS / MAQL / BIGQUERY |
| 扩展机制 | `custom_extensions` 字段 | 任何 vendor 可以在不破坏 schema 的前提下加自有字段 |
| AI 维度 | `ai_context` 一级字段 | 每层（semantic_model / dataset / field / metric）都支持挂 AI 上下文 |

不变项之外，**它明确不做的事**：

- ❌ **不**定义 query execution。spec 只描述”营收 = sum(orders.amount)”，不规定”用什么引擎跑这个 sum”。
- ❌ **不**做身份 / 行级权限。访问控制留给下游 BI / catalog 工具。
- ❌ **不**要求厂商支持全部字段。所有字段除 `name` / `source` 外都是 optional，但越核心的字段跨厂商一致性越好。
- ❌ **不**替代 dbt / LookML / Cube.js。它是这些工具之间的”互操作语言”，不是它们其中之一的竞争者。
- ❌ **不**锁定 license。所有内容 Apache-2.0，任何人都可以 fork、自部署、做私有扩展。

这 5 条”不做”恰好决定了它的设计取舍——下面拆开看。

---

## 关键机制：Spec 结构与 ai_context

### 1. 顶层结构

Ossie 的 spec 顶层是一个 `semantic_model` 数组：

```yaml
semantic_model:
  - name: sales_analytics
    description: Sales and customer analytics model
    ai_context:
      instructions: ”Use this model for sales analysis and customer insights”
    datasets: [...]
    relationships: [...]
    metrics: [...]
    custom_extensions:
      - vendor_name: DBT
        data: '{”project_name”: ”tpcds_analytics”, ”models_path”: ”models/semantic”}'
```

每一层都遵守同一个原则：**核心 schema 字段最小化 + custom_extensions 留给 vendor + ai_context 留给 AI**。这三条是 Ossie 与传统语义层工具（dbt semantic models、LookML、Cube.js semantic layer）最大的设计差异。

### 2. ai_context：把 AI 当一等公民

spec 里最值得注意的设计是 `ai_context` 字段出现在 4 个层级：

| 层级 | ai_context 作用 |
|---|---|
| `semantic_model` | 整模型指令（”这个模型用于销售分析”） |
| `dataset` | 实体级上下文（同义词、常用业务术语） |
| `field` | 列级上下文（”customer_id 也叫 buyer_id”） |
| `metric` | 指标级上下文（”revenue 是 gross 不是 net”） |

**为什么这件事关键**：在 2026 年的真实工作流里，AI agent 是 semantic layer 的新消费者——LangChain、LlamaIndex、CrewAI 之类的 agent 框架会读 dbt manifest、LookML、Cube semantic API 来理解”业务里有这些字段、它们的语义是什么”。但传统 spec 没有为 agent 优化字段描述。Ossie 把 `ai_context` 设成一级字段，本质上是承认：**语义模型的未来消费者不只是 SQL 引擎，更是 LLM agent**。

### 3. Dialect 枚举覆盖 7 种 SQL/expression 方言

```yaml
# expression_language.md 中的 Dialects 枚举
- ANSI_SQL       # 标准 SQL
- SNOWFLAKE      # Snowflake SQL
- MDX            # 多维表达式（SSAS / PowerBI 等）
- TABLEAU        # Tableau 计算字段语法
- DATABRICKS     # Databricks SQL
- MAQL           # GoodData 的 MAQL
- BIGQUERY       # Google BigQuery（GoogleSQL）
```

**为什么这件事关键**：跨 BI 工具搬运 metric 时，最头疼的就是”同一个 sum，在 Tableau 里是 `SUM([Amount])`，在 Snowflake 里是 `SUM(amount)`，在 BigQuery 里是 `SUM(amount)`（同名但 window function 行为略不同）”。Ossie 用一份 `dialect` 枚举让每个 metric 显式声明自己的 dialect，下游 converter 按方言翻译——这是它在 schema 层最具体的设计杠杆。

### 4. custom_extensions：让厂商既能扩展又不破坏 schema

```yaml
metrics:
  - name: revenue
    description: Total recognized revenue
    type: simple
    type_params:
      measure: recognized_revenue
    custom_extensions:
      - vendor_name: DBT
        data: '{”materialized”: ”incremental”, ”cluster_by”: [”order_date”]}'
      - vendor_name: GOODDATA
        data: '{”maql_fragment”: ”SELECT SUM(recognized_revenue)”}'
```

**关键设计**：`custom_extensions` 是一个数组，每条 entry 自带 `vendor_name` + `data`（任意 JSON）。这让 dbt / GoodData / Polaris / Salesforce 各自能挂自己的 metadata 而不影响其它 reader。**这个字段是 Ossie 能否真正”厂商中立”的工程保证**——没有它，每个 vendor 都会提 patch 改 core schema，最终分叉。

### 5. Converters：双向翻译，不是单向导入

`converters/` 目录下每个 vendor 一个目录：

```
converters/
├── dbt/          # dbt  ↔  Ossie
├── gooddata/     # GoodData  ↔  Ossie
├── polaris/      # Polaris  ↔  Ossie
└── salesforce/   # Salesforce  ↔  Ossie
```

**为什么双向很关键**：如果只是 dbt → Ossie，那 Ossie 就是 dbt 的 export 格式；事实是很多团队已经在 GoodData / Tableau / Salesforce 里写好 metric 定义了，他们想做”反向迁移”或”对账”——双向 converter 让 Ossie 成为 pivot，而不是某一方的附庸。

---

## 任务流案例：用 Ossie 对齐三个工具里的 revenue 定义

把上面的零件拼起来跑一次完整 flow：

**Step 1：在 dbt 里定义 revenue**

```yaml
# dbt model: revenue.sql
{{ config(materialized='incremental', cluster_by=['order_date']) }}
SELECT
  order_id,
  order_date,
  customer_id,
  amount AS recognized_revenue,
  refund_amount
FROM orders
WHERE status = 'recognized'
```

**Step 2：跑 dbt → Ossie converter**

```bash
python -m converters.dbt.cli \
  --dbt-project ./my_dbt_project \
  --out ossie.yaml
```

converter 输出：

```yaml
semantic_model:
  - name: revenue_model
    datasets:
      - name: orders
        source: analytics.orders
        primary_key: [order_id]
        fields:
          - name: recognized_revenue
            type: measure
            ai_context:
              synonyms: [”net_revenue”, ”booked_revenue”]
    metrics:
      - name: revenue
        type: simple
        type_params:
          measure: recognized_revenue
        ai_context:
          instructions: ”Recognized revenue only, excludes refunds”
        custom_extensions:
          - vendor_name: DBT
            data: '{”materialized”: ”incremental”}'
```

**Step 3：GoodData 同步**

GoodData 管理员在 GoodData UI 里手工维护的 `revenue` metric 与 dbt 这边的口径不同（”用 gross_revenue 字段”）。跑 GoodData → Ossie converter，输出另一份 yaml；用 `diff` 工具对比，发现：

```diff
- measure: recognized_revenue  (dbt)
+ measure: gross_revenue        (GoodData)
```

**Step 4：选定一边，sync 回去**

业务口径讨论后，决定用 `recognized_revenue`（因为含 refund 调整更准）。把 dbt 这边的 Ossie yaml 喂给 GoodData → Ossie converter 的反向 sync：

```bash
python -m converters.gooddata.cli sync \
  --in ossie.yaml \
  --target gooddata_project_id
```

GoodData 里的 metric 定义被改写为 `recognized_revenue`。

**Step 5：让 AI agent 也能用**

AI agent 在接到”上个月营收多少”的提问时：

1. 读 `ossie.yaml`（已注册到企业 metadata store）。
2. 找到 `metric: revenue`，读 `ai_context.instructions`。
3. 用 `metric.type_params.measure` 生成 SQL → `SELECT SUM(recognized_revenue) FROM analytics.orders WHERE ...`。
4. 返回答案。

**这是 Ossie 的关键卖点**：在不改 dbt / GoodData 任一工具的前提下，用同一份 ossie.yaml 统一两边口径 + 让 AI agent 也能消费。

---

## 与同类项目的横向对照

| 维度 | Apache Ossie | dbt semantic models | LookML | Cube.js semantic layer | OpenLineage |
|---|---|---|---|---|---|
| 角色 | 互操作规范 | 单工具模型层 | 单工具模型层 | 自托管语义 API | 数据血缘规范 |
| 厂商中立 | ✅ 7 方言 | ❌ dbt 专属 | ❌ Looker 专属 | ❌ Cube 专属 | ✅ 厂商中立 |
| AI 字段 | ✅ `ai_context` 一级 | ❌ 注释式 | ❌ 注释式 | ❌ 无 | ❌ 无 |
| 双向转换 | ✅ 多对多 | 单向 | 单向 | 单向 | 单向 |
| 治理位置 | 仓库 + 社区 | dbt 项目 | LookML repo | 自部署服务 | Marquez 等 |
| License | Apache-2.0 | Apache-2.0 | 私有 | Apache-2.0 | Apache-2.0 |
| 状态 | 0.2.0.dev0 草案 | GA | GA | GA | GA |

这张表想表达一件事：**Ossie 不是要替代 dbt / LookML / Cube**，而是要在这些工具之上提供一层”跨工具的语义层互操作语言”。这跟 OpenLineage 在数据血缘领域的角色非常像——OpenLineage 也不替代 dbt / Airflow，但让 dbt 和 Airflow 的血缘能互相消费。

---

## 适用边界

**推荐使用**：

- 团队同时使用 2+ 个 BI / 语义层工具，且需要确保 KPI 一致性
- 正在做 AI agent for analytics（让 agent 准确理解”营收是什么”）
- 想从 dbt / LookML / Cube 迁移到另一个工具，需要一份 pivot
- 在做企业级 data catalog（Atlan / DataHub / Unity Catalog），需要为 AI 消费提供结构化语义层

**不推荐使用**：

- 团队只用 1 个 BI 工具 → 直接用那个工具的 native semantic model 更省事
- 0.2.0 GA 还没出，需要 production stability → 暂时观望，或锁定 `0.2.0.dev0` 的某次 commit
- 只关心 query performance → Ossie 是 spec，不解决 query engine 问题
- 不想参与上游治理 → Ossie 在 Apache 孵化中，重大决策需要进社区讨论

---

## 决策建议

按组织阶段选：

1. **只用 1 个 BI 工具** → 用 dbt / LookML / Cube.js native model；Ossie 等 GA。
2. **用 2 个工具且口径已开始打架** → 评估 Ossie 作为 pilot 项目，从一个 dataset 开始双向 sync。
3. **正在做 AI agent for analytics** → Ossie 的 `ai_context` 字段是当前公开规范里最值得参考的设计，可以 fork 这部分设计。
4. **企业 data catalog 选型** → 优先选支持 Ossie import 的（Atlan、DataHub 已经在跟）。
5. **想参与 Apache 项目** → Ossie 现在处于孵化阶段，贡献窗口开放，converters/ 下的 vendor 覆盖还不全，是贡献 converter 的好时机。

---

## 阅读路径

按需读：

- **只想理解问题**：本文 + spec.md 头部 ”Goals” 段
- **想理解 schema**：core-spec/spec.md（按章节读 Datasets → Relationships → Fields → Metrics）
- **想理解 ai_context**：core-spec/spec.md 中所有 `ai_context` 出现的位置（顶层、dataset、field、metric 四层）
- **想理解 dialect 体系**：core-spec/expression_language.md
- **想跑一个 converter**：converters/dbt/ 或 converters/gooddata/ 下的 README
- **想参与社区**：docs/ROADMAP.md + GitHub Discussions + Slack

---

## 边界声明

本文基于 [apache/ossie](https://github.com/apache/ossie) 仓库 README（2026-07-17 抓取）+ `core-spec/spec.md` 前 200 行 + `core-spec/expression_language.md` 目录列表 + GitHub API 拉取的仓库元数据。

**重要事实**：

- 当前版本 `0.2.0.dev0`（DRAFT）—— spec 在 0.2.0 正式发布前可能 breaking change。
- README 明确写 ”in development, schema may change before 0.2.0 is released”。
- 仓库处于 Apache 孵化阶段（”incubating”），毕业到 TLP 之前由 mentor pod 监督，社区治理结构按 Apache 流程演进。
- `converters/` 下的 vendor 覆盖（dbt / GoodData / Polaris / Salesforce）尚不完整；具体覆盖矩阵请查仓库当时状态。
- `custom_extensions` 的 vendor 注册目前是约定俗成（”用 vendor_name 标识"），还没有中心化 registry；正式治理可能在 0.2.0 之后成型。

如果你的生产系统强依赖 Ossie schema，请固定到具体 commit 或等待 0.2.0 GA。
