+++
date = '2026-06-07T23:03:00+08:00'
draft = false
title = 'pg_durable 深度解析：把 durable execution 直接搬进 PostgreSQL，Microsoft 给后端工程师的零基础设施工作流'
slug = 'pg-durable-postgres-durable-execution-guide'
description = '微软开源的 PostgreSQL 扩展 pg_durable，把 durable execution 模式从 Temporal / Airflow / Step Functions 收回到 SQL 内：长跑、容错、检查点、并行 fan-out 全部用 df.start(~> 和 |=> 表达，零基础设施，深度对比传统方案。'
categories = ['技术笔记']
tags = ['PostgreSQL', 'pg_durable', 'durable execution', '数据库', '工作流', 'Azure HorizonDB', 'Microsoft']
+++

# pg_durable 深度解析：把 durable execution 直接搬进 PostgreSQL，Microsoft 给后端工程师的零基础设施工作流

> **目标读者**：负责后台数据流水线、AI 嵌入管道、运维 runbook 的后端 / 数据工程师和 DBA
> **核心问题**：能不能不引入 Temporal、Airflow、Step Functions、pg_cron+worker，就在 PostgreSQL 内部跑出可恢复、可检查点、并行 fan-out 的长跑工作流？
> **难度**：⭐⭐⭐（中级，需要熟悉 PostgreSQL 扩展和 SQL 函数）
> **预计阅读时间**：35 分钟

---

## 一、为什么 pg_durable 会出现在 GitHub Trending

### 1.1 后端的老问题：长跑任务 = 状态机 + 队列 + worker + cron

任何一个跑过数据管道、AI 嵌入批处理、月度对账的团队，几乎都拼过同一种「胶水架构」：

- 一张 `jobs` 表记录「开始时间 / 状态 / 重试次数」
- 一个 `pg_cron` 表达式每分钟唤醒一次轮询
- 一组 worker（Python、Go、Node）在外面消费
- 一个队列（Redis / RabbitMQ / SQS）做削峰
- 几张 status 表跟踪部分完成 / 失败 / 重放
- 一组 dashboard 显示「卡住的任务」「卡住多久」
- 出问题时的复盘：哪些 step 重跑了？哪些没？能不能幂等？

这套架构的代价是：**业务逻辑被切碎到 SQL、worker、队列、调度器、状态表五处**，故障时需要人脑重新拼装。

durable execution（持久化执行）作为一种「行业默认模式」，就是为了把以上五处合并到一个 runtime 内部。Temporal、AWS Step Functions、Airflow、DBOS 都属于这个流派。

### 1.2 pg_durable 的差异化：把所有 runtime 塞回 PostgreSQL

`microsoft/pg_durable` 的设计目标是：**让 durable execution 直接在 PostgreSQL 内部跑**，作为一个 PG 扩展，状态、checkpoint、调度、可见性全在 `df.*` 表里。配合微软同期的 Azure HorizonDB（cloud PostgreSQL 服务）一起发布，已经预装在生产环境里。

GitHub Trending 把它推上来，本质上是因为：后端工程师已经被「Temporal 自托管」「Airflow 升级」折磨太久了，突然看到一个「零基础设施、纯 SQL、原生 PG 扩展」的方案，情绪被点燃。

---

## 二、原理分析：durable execution 的 SQL 化

### 2.1 核心思想：每一步都 checkpoint

pg_durable 把一个工作流建模成 **SQL 步骤的有向图**：

- 用 `df.start('workflow_id', $step)` 启动一个 durable function
- 步骤之间的连接用 `~>`（顺序）和 `|=>`（并行 fan-out）表达
- 每一个 step 完成后，结果写进 PG 表，下次启动从 checkpoint 恢复
- 整个 workflow 的状态可以在 `df.instances` / `df.steps` 表里直接 SQL 查询

这就是为什么 README 把它概括为：**「Function state persists to PostgreSQL. Survives crashes, restarts, and failovers.」**

### 2.2 状态在哪：df.* 系统表

pg_durable 把 durable execution 的全部运行时数据落地在 PostgreSQL 自己的表里，权限模型、备份模型、审计模型和业务数据一致：

- `df.instances` — workflow 实例的状态、启动时间、结束时间
- `df.steps` — 每一步的输入 / 输出 / 状态 / checkpoint
- `df.journal` — 事件流（可选，用于审计）
- 调度、并行执行、HTTP 出站调用，都有对应的内置 step 类型

后果：**你不再需要额外的 Redis 也不需要额外的 Temporal 集群**。一次 PG 备份 = 整个 workflow 状态 + 业务数据一起被备份。

### 2.3 和「pg_cron + workers + 状态表」传统方案的对比

| 维度 | pg_cron + workers | Airflow / Temporal | pg_durable |
|---|---|---|---|
| 状态存储 | 业务 DB + 队列 | 独立 runtime DB | PostgreSQL `df.*` 表 |
| 检查点 | 自建 status 列 | runtime 内部 | 每 step 一次，PG 事务级 |
| 失败恢复 | 重新拼装 | 重新触发 DAG | 从 checkpoint 自动续跑 |
| 并行 fan-out | 自己写 worker | DAG 配置 | `~>` / `\|=>` 表达式 |
| 可见性 | 多张表 join | runtime UI | 直接 SQL `df.instances` |
| 基础设施 | Redis/队列 + worker | 额外 K8s 集群 | 仅一个 PG 扩展 |
| 备份模型 | 双份（业务 + runtime） | 三份（业务 + runtime + 队列） | 一份（业务即 runtime） |

后端团队的核心收益：**少一套基础设施、少一份数据一致性风险、少一个权限体系要打通。**

---

## 三、Quick Example：把"批量处理文档 + 调 embedding API + 写回 pgvector"装进一个 workflow

README 提供的官方例子很贴近真实 AI 工程：

```sql
-- 1. durable function：把 100 条未处理文档跑成 embedding
SELECT df.start(
    'SELECT id FROM documents WHERE processed = false LIMIT 100' |=> 'batch'
    ~> 'UPDATE documents SET processed = true WHERE id = ANY($batch)'
    ~> df.http('https://api.openai.com/v1/embeddings', $batch)
    ~> 'INSERT INTO documents_embedding SELECT * FROM embeddings_tmp'
);
```

解读：

- `|=> 'batch'`：把第一步结果存为变量 `batch`
- `~> 'UPDATE ...'`：本地 SQL 步骤，事务级 checkpoint
- `~> df.http(...)`：出站 HTTP 调用，失败会按 retry policy 重试
- `~> 'INSERT ...'`：再把结果写回业务表
- 整条链 crash anywhere，恢复时 **只重做未完成的 step**

这是 README 的简化版。生产里通常会再叠加：

- `df.parallel(...)` 把 100 条文档切成 N 路并发
- `df.wait_for_approval('oncall_team')` 让某些 step 暂停等待人审批
- `df.schedule('every day at 03:00')` 做周期触发

---

## 四、适用与不适用：什么时候该上 pg_durable

README 自己列了「适合我」的画像：

- 后端 / 数据工程师：希望 workflow 和它操作的数据**物理上放在一起**
- DBA / SRE：自动化 runbook，**必须能跨重启存活 + SQL 可审计**
- 数据 / AI pipeline 团队：每行 / 每文档 / 每批都需要 durable execution

README 也明确列了「不适合」的边界：

- 任务已经是一个 `INSERT ... SELECT` 或一句普通 SQL
- 你要的是亚毫秒级同步请求处理（pg_durable 是**后台执行**）
- 环境不允许装扩展或起 background worker
- workflow 跨很多非 PG 异构系统
- 业务逻辑本质上是任意代码、不容易映射到 SQL step / 分支 / 循环 / HTTP

实际工程判断建议：

- **替换 pg_cron + 一张 status 表 + 几个 Python worker** → 直接上 pg_durable，收益最大
- **替换 Temporal / Airflow** → 评估：你的 DAG 是不是 90% 都在 SQL 内部完成的？是 → 强烈推荐；否 → 保留外部 runtime
- **AI 嵌入管道 / 数据 ingest / 月度对账** → 这是 pg_durable 的「教科书场景」

---

## 五、横向对比：pg_durable vs DBOS vs Temporal vs Airflow

| 维度 | pg_durable | DBOS | Temporal | Airflow |
|---|---|---|---|---|
| 形态 | PG 扩展 | PG + Python SDK | 独立 Go runtime | 独立 Python runtime |
| 语言 | SQL | Python / TypeScript | 多语言 SDK | Python |
| 学习曲线 | 低（SQL） | 中（SDK + 装饰器） | 中高（worker 模型） | 中（DAG 配置） |
| 部署 | PG 装上就完事 | PG + 调度器 | 集群 + DB | 集群 + executor |
| 检查点粒度 | step | step | event | task |
| 跨工作流事务 | PG 事务直接覆盖 | PG 事务 | saga 模式 | XCom + 人工拼装 |
| 适用规模 | 单 PG 实例即可 | 中小 | 大 | 大 |
| 生态成熟度 | 新（2026 GA） | 较新 | 老牌 | 老牌 |

一句话：**「业务逻辑 80% 都在 SQL 里」且「不想再养一套 workflow 集群」的团队，pg_durable 是目前最朴素的选择。**

---

## 六、和 Azure HorizonDB 的关系

pg_durable 不是孤立发布的——它和微软的 **Azure HorizonDB**（一个为性能调优、内置 pg_durable 的 PostgreSQL 云服务）一起出场。意味着：

- Azure 用户：直接在 HorizonDB 里 `CREATE EXTENSION pg_durable;` 就能用
- 自托管用户：在 PostgreSQL 17 / 18 上装扩展也可以
- README 明确支持 PG 17 和 18 两个版本

**附带价值**：在 Azure 上跑的话，pg_durable 的运维监控、SLA、和业务表共池是默认打通的状态。

---

## 七、生产落地的几个关键提醒

虽然 pg_durale 把复杂度藏进了 PG 内部，但生产上还是要小心：

1. **不要把 step 粒度做太细**：每一步都是一次 PG 事务，事务太密会拖慢整体吞吐
2. **长时间无 checkpoint 的 step**：用 `df.parallel` 拆分或显式调 `df.checkpoint()`
3. **HTTP 出站**：注意 timeout 和 retry 预算，建议在 SQL 步骤外面包一层限流
4. **backpressure**：业务表被写爆时，durable function 不会自动背压，需要业务侧做信号量
5. **审计**：把 `df.journal` 接到 ELK / Datadog / OpenTelemetry，长期可观测性靠这个
6. **升级路径**：PG 大版本升级时，先在测试集群验证 `df.*` 表的数据兼容性

---

## 八、总结：给后端工程师的决策清单

- ✅ **强推荐**：你的 workflow 主体在 SQL 内，且现状是 pg_cron + 几张状态表 + 一组 worker
- ✅ **推荐**：你要做 AI 嵌入管道 / 月度对账 / 数据 ingest pipeline
- ✅ **值得评估**：你已经在 Azure 上用 PG，且不愿意引入 Temporal 这种大 runtime
- ⚠️ **谨慎**：你的 workflow 跨很多外部 SaaS 编排、且每一步都需要复杂代码逻辑
- ❌ **不推荐**：你要的是「同步请求级别的 saga」，或业务逻辑基本不在 SQL 里

**GitHub**: [microsoft/pg_durable](https://github.com/microsoft/pg_durable)
**官网**: [microsoft.github.io/pg_durable](https://microsoft.github.io/pg_durable/)
**许可**: PostgreSQL License（开源，免费商用）
**支持版本**: PostgreSQL 17 / 18

---

*2026-06-07 · GitHub Trending 收录 · 文本矩阵「技术笔记」专栏*
