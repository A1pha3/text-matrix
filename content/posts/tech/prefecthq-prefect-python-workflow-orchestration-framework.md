---
title: "Prefect 实战：把 Python 脚本升级为可观测的工作流"
date: 2026-07-13T03:01:47+08:00
categories: ["技术笔记"]
tags: ["Python", "工作流编排", "数据管道", "Prefect", "可观测性"]
description: "Prefect 是 Python 工作流编排框架,装饰器风格让脚本零改造升级为带调度、缓存、重试与可观测性的生产工作流,自托管 Server 与 Cloud 双轨,Apache 2.0。"
slug: prefecthq-prefect-python-workflow-orchestration-framework
---
# Prefect 实战：把 Python 脚本升级为可观测的工作流

> 仓库：`PrefectHQ/prefect`（[GitHub](https://github.com/PrefectHQ/prefect)），截至 2026-07-13 公开数据 23 090 stars、2 386 forks，主语言 Python，协议 Apache 2.0。仓库首次提交 2018-06-29，最近一次 push 在 2026-07-12，仍然活跃。

## 一、Prefect 是什么、解决什么问题

Prefect 是 Python 写的数据管道编排框架。它的核心承诺是：**用几个装饰器把一段普通的 Python 脚本升级为生产级工作流**，自带调度、缓存、重试、事件触发、参数化与运行时可观测性。

它解决的是数据团队最常见的一个困境：本地跑得好好的 ETL 脚本，搬到生产就崩——要么某一步超时、要么下游 API 短暂故障、要么不知道昨晚跑没跑、跑到哪一步。传统的解法是引入 Airflow，但 Airflow 的 DAG 定义是另一套语言、另一套心智模型，对小团队或快速迭代的脚本来说太重。Prefect 的路径不同：保持代码是 Python，编排能力是装饰器，让本地和生产的语义一致。

按官方 README 与社区文档，Prefect 的典型使用场景包括：

- 周期性数据同步（DB → 数仓、API → DB）
- 机器学习训练与推理流水线
- 多步 ETL 任务，带依赖、缓存与失败回退
- 事件驱动的响应式自动化（webhook、文件到达、消息总线事件触发）
- 团队协作的工程化数据产品

## 二、安装与最简上手

Prefect 要求 Python 3.10+。安装只有一行：

```bash
pip install -U prefect
# 或者
uv add prefect
```

官方 README 给出的最简示例是一个"获取 GitHub stars"的脚本，足够把 Prefect 的核心 API 都展示一遍：

```python
from prefect import flow, task
import httpx


@task(log_prints=True)
def get_stars(repo: str):
    url = f"https://api.github.com/repos/{repo}"
    count = httpx.get(url).json()["stargazers_count"]
    print(f"{repo} has {count} stars!")


@flow(name="GitHub Stars")
def github_stars(repos: list[str]):
    for repo in repos:
        get_stars(repo)


# run the flow!
if __name__ == "__main__":
    github_stars(["PrefectHQ/prefect"])
```

几个关键点：

1. `@task` 装饰器把普通函数变成"Prefect 任务"，自带重试、日志、缓存、tags 等配置项，`log_prints=True` 把函数内的 `print` 接入 Prefect 日志系统。
2. `@flow` 装饰器把函数变成"Prefect 流"，是任务的容器。流可以嵌套（流里调用流）、可以参数化、可以单独部署。
3. 直接 `python script.py` 时，流按普通 Python 执行，但每次任务运行都会被 Prefect 引擎追踪，本地无需启动任何服务即可获得完整的运行历史（写到本地 SQLite 或配置的 backend）。

启动 Prefect Server 看 UI：

```bash
prefect server start
```

默认监听 `http://localhost:4200`。能看到每次 run 的状态、参数、日志、缓存命中、失败堆栈。

把它变成周期性部署，只改最后一行：

```python
if __name__ == "__main__":
    github_stars.serve(
        name="first-deployment",
        cron="* * * * *",
        parameters={"repos": ["PrefectHQ/prefect"]},
    )
```

`serve()` 会启动一个常驻进程，按 cron 表达式调度流。也可以通过 UI 或 CLI 手动触发，或者订阅事件触发（webhook、自动化事件）。

## 三、核心概念全景

Prefect 的概念体系相对克制，主要由这几个对象组成：

### 3.1 Task（任务）

最小执行单元，是被 `@task` 装饰的 Python 函数。任务可以独立配置：

- `retries`：失败重试次数（默认 0）
- `retry_delay_seconds`：重试间隔
- `timeout_seconds`：单次执行超时
- `cache_key_in` / `cache_expiration`：输入驱动的缓存（同一输入只跑一次）
- `log_prints`：把 print 接入 Prefect 日志
- `tags`：用于过滤与路由
- `task_run_name`：动态 run 名
- `persist_result`：把返回值落盘，便于跨任务恢复

任务可以在本地函数上声明，也可以在外层用 `.submit()` 提交给 task runner 并发执行。

### 3.2 Flow（流）

容器，是被 `@flow` 装饰的 Python 函数。流本身也有：

- `name`、`description`、`version`
- `retries`、`timeout_seconds`
- `log_prints`
- `task_runner`：默认是 `ThreadPoolTaskRunner`，可以换成 `DaskTaskRunner`、`RayTaskRunner` 等
- `result_storage`、`result_serializer`：如何把返回值持久化
- `on_completion` / `on_failure` 钩子

流的返回值会被 Prefect 自动持久化为"flow run result"，下游工作流可以用 `load_flow_from_result()` 之类 API 加载。

### 3.3 Deployment（部署）

流要在生产跑，必须变成 deployment。`flow.serve()` 是最直接的方式，更复杂的场景下用 `flow.deploy()` 把镜像、worker pool、调度都写进声明式描述。Prefect 3 的 deployment 模型有几种：

- **Process deployment**：在本地或 worker 机器上以子进程方式跑
- **Docker deployment**：把流打包进镜像，在容器中跑
- **Kubernetes deployment**：在 K8s 上跑，配合 worker pool
- **Serverless deployment**：AWS ECS、Azure Container Instances、GCP Cloud Run 等托管运行时

每个 deployment 都有 schedule（cron 或 interval）、work pool（运行时环境）、parameters、tags、concurrency limit、global concurrency limit 等。

### 3.4 Work Pool（工作池）与 Worker（工作者）

Work pool 是"流跑在哪里的抽象"：一台机器、一个 K8s 集群、一组 Lambda。Worker 是实际去 poll work pool 的进程，拉取待执行的流运行、起环境、跑流、回报结果。

这种解耦的好处是：开发者只关心代码与声明式部署，运行时拓扑由 infra 团队在 work pool 层配置。

### 3.5 Schedule（调度）

部署自带 schedule。常用类型：

- `CronSchedule`：标准 5 字段 cron，带时区
- `IntervalSchedule`：固定间隔（每 15 分钟、每 2 小时）
- `RRuleSchedule`：复杂重复规则
- 也可以完全无 schedule，靠事件或外部触发

### 3.6 Flow Run（流运行）

一次具体的执行，包含：

- 状态（pending / scheduled / running / completed / failed / crashed / cancelled / paused）
- 任务运行列表（每个 task 的状态、参数、结果、缓存键、重试次数）
- 开始/结束时间、耗时
- 输入参数
- 日志（结构化）

UI 上可以查看每次 flow run 的完整轨迹。

### 3.7 State 与 Result（状态与结果）

Prefect 用一套语义化状态机描述每次执行的进程。配合 `result_storage`（本地文件系统 / S3 / GCS / Azure Blob 等）可以持久化任务与流的返回值，供后续 run 引用或跨进程恢复。

## 四、Prefect 的两大运行模式

### 4.1 自托管：Prefect Server

`prefect server start` 会启动一个本地 Prefect Server（包含 Orion 后端 API + Postgres + UI）。它把每次 flow run 的状态、参数、日志、结果都存入 Postgres，并提供完整的 UI。

生产部署通常用 `prefect server database upgrade` 初始化 schema，再把 server 跑在独立机器或 K8s。同一份代码在 server 模式下与在 Prefect Cloud 上的 API 兼容，迁移只需修改 `PREFECT_API_URL` 环境变量。

### 4.2 托管：Prefect Cloud

Prefect Cloud 是官方托管版，提供：

- 多用户工作区与 RBAC
- 审计日志与团队治理
- 跨工作区审计与 SSO
- Work pool、自动化、事件订阅的托管界面
- 自动扩容的 worker 接入

按 README 介绍，Prefect Cloud 每月处理超过 2 亿个数据任务，客户包括 Progressive Insurance、Cash App 等。

代码侧 API 完全一致，切换方式：

```bash
prefect cloud login
# 或
prefect config set PREFECT_API_URL=https://api.prefect.cloud/api/accounts/<ACCOUNT_ID>/workspaces/<WORKSPACE_ID>
```

### 4.3 轻量客户端：prefect-client

如果应用不需要发起 flow run，只消费 Prefect Cloud 或远端 Server 的元数据、读运行结果、订阅事件，可以用更轻的 `prefect-client` 包，避免引入完整 `prefect` SDK 的依赖。它适合嵌入 Lambda、Cloud Run Jobs、临时容器等短生命周期运行环境。

## 五、关键能力拆解

### 5.1 重试与超时

`@task(retries=3, retry_delay_seconds=[10, 30, 60])` 就能声明一串指数退避的重试。`@flow(retries=2)` 则让整个流在最后任务失败后整体重跑。重试状态可以在 UI 上一目了然。

### 5.2 缓存

缓存是 Prefect 的核心卖点之一。两种粒度：

- **输入驱动的缓存**：`@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(hours=1))`。同一输入在一小时内只跑一次，结果直接复用。
- **外部文件驱动的缓存**：通过 `cache_key_fn` 自定义，把缓存键和外部文件、S3 对象等绑定。

这对"重新跑昨天的 ETL 只想刷新最新一段"这类场景特别有用：上游未变，跳过；下游变了，重跑。

### 5.3 并发

流默认用 `ThreadPoolTaskRunner`。提交任务时用 `get_stars.submit("PrefectHQ/prefect")` 而不是 `get_stars("PrefectHQ/prefect")`，就可以并发：

```python
@flow(task_runner=ThreadPoolTaskRunner(max_workers=4))
def github_stars(repos: list[str]):
    futures = [get_stars.submit(repo) for repo in repos]
    return [f.result() for f in futures]
```

切到 `DaskTaskRunner` 或 `RayTaskRunner` 即得到跨机器的分布式并发。

### 5.4 子流与映射

流可以嵌套流；任务可以 `submit` 出去并发；流也可以用 `.map()` 把一组参数映射成多个并行子任务。这是 Prefect 处理 fan-out / fan-in 的标准范式。

### 5.5 参数化

流签名本身就是参数契约。`@flow def fetch(repo: str, since: datetime)` 部署时通过 `parameters={"repo": "...", "since": "..."}` 注入，UI 上也能临时改参数触发。

### 5.6 事件驱动自动化

Prefect 3 引入了 Automation：监听事件（新 flow run 完成、失败、自定义事件、webhook），触发动作（跑另一个流、发 Slack、调 webhook、暂停 work pool）。这让响应式数据管道成为可能：上游 DAG 完成 → 自动跑下游模型评估；Sentry 报警 → 触发数据修复。

事件源可以是 Prefect 内部事件，也可以是外部 webhook、PostgreSQL CDC、S3 event、Kafka 等（通过对应集成）。

### 5.7 结果持久化与跨进程恢复

`@task(persist_result=True, result_storage=S3(bucket="..."))` 让任务返回值写入 S3。如果 worker 进程崩溃，下一次重试可以直接拿到上次的中间结果，而不需要从头跑整个流。这对长任务至关重要。

### 5.8 可观测性

每次 flow run 在 UI 上有：

- 时间线视图（任务开始、结束、重试）
- 完整日志（带 traceback）
- 输入输出（参数与返回值）
- 缓存命中与跳过
- tags 与关联的 work pool、deployment

CLI 上 `prefect flow-run ls`、`prefect flow-run logs <id>`、`prefect task-run ls` 等命令能脚本化查看。

## 六、与 Airflow / Dagster 的取舍

把 Prefect 放进数据编排工具谱系里看，它的定位清晰：

- **相对 Airflow**：Prefect 代码即 Python，airflow 要写 DAG 描述文件；Prefect 重试、缓存是声明式的，airflow 经常要写自定义 operator；Prefect 的 UI 围绕"flow run"组织，airflow 围绕"DAG run + task instance"。代价是：airflow 在大数据批处理生态（Sensors、Providers、连接器）上历史更长、迁移路径更成熟；Prefect 适合 Python-first 的小到中型团队。
- **相对 Dagster**：Dagster 的资产（asset）模型是核心抽象，强调"数据应该是什么样子"，定义 schema 与 lineage；Prefect 更强调"任务流"，按调度与触发驱动。Dagster 的资产/观测/ lineage 体验更适合数据资产导向的团队；Prefect 的代码风格对应用开发者更友好。
- **相对 Temporal / Step Functions**：后者更偏微服务编排，前者更偏数据/批处理。

团队选择哪种框架，关键不是工具本身的优劣，而是"代码组织方式"是否与团队习惯一致。

## 七、生态与扩展

README 列出的生态资源：

- **官方文档**：[docs.prefect.io](https://docs.prefect.io)，覆盖安装、概念、API、部署、Cloud 接入。
- **Slack 社区**：25 000+ 实践者，链接在 README。
- **Dev Log**：[dev-log.prefect.io](https://dev-log.prefect.io/)，团队公开发的产品演进博客。
- **集成仓库**：通过 `prefect-aws`、`prefect-gcp`、`prefect-azure`、`prefect-k8s`、`prefect-sqlalchemy`、`prefect-dbt` 等官方集成，把 S3、BigQuery、Databricks、K8s 等资源封装成可重用的任务与运行时。
- **Newsletter**：订阅后能收到 Prefect 团队的产品与最佳实践更新。
- **YouTube 频道**：包含教程、案例、版本更新解读。

## 八、典型工作流范式

下面给出几个典型的工作流模式，方便建立直观认识。

### 8.1 周期 ETL + 缓存

```python
@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(hours=6))
def extract(table: str, since: datetime): ...


@task(retries=3, retry_delay_seconds=[10, 30, 60])
def transform(rows: list[dict]) -> pd.DataFrame: ...


@task
def load(df: pd.DataFrame, dest: str) -> int: ...


@flow(name="etl-pipeline")
def etl(table: str, dest: str):
    rows = extract(table, datetime.utcnow() - timedelta(days=1))
    df = transform(rows)
    return load(df, dest)
```

部署到 K8s work pool，每天 02:00 跑一次。上游 `extract` 因为 `cache_key_fn` 在 6 小时内重复输入不重跑；`transform` 失败时按指数退避重试。

### 8.2 事件驱动自动修复

```python
from prefect import flow
from prefect.events import listen_event

@listen_event(event="sentry.alert.critical", filters={"project": "data-pipeline"})
def on_critical(event):
    # 触发修复流
    auto_remediate.submit(event.resource.id)


@flow
def auto_remediate(alert_id: str):
    ...
```

UI 上配置一条 Automation："Sentry 严重告警 → 调用 `auto_remediate` 流"，把响应链路写在 Python 里而不是 YAML/UI。

### 8.3 长任务 checkpoint

```python
@task(persist_result=True, result_storage=S3(bucket="prefect-results"))
def train_step(state, step_idx):
    ...
    return new_state


@flow(retries=2)
def train():
    state = init()
    for i in range(100):
        state = train_step(state, i)
```

worker 崩溃后，重试能从最近一次成功的 `train_step` 继续，而不是从头来。

## 九、读懂 Prefect 的源码路径

如果想从代码层面理解 Prefect，建议按这个顺序读：

1. `src/prefect/flows.py` 与 `src/prefect/tasks.py`：核心装饰器与状态机。
2. `src/prefect/engine.py`：流的执行引擎，理解为什么 task 会被追踪。
3. `src/prefect/orion/schemas/`（3.x 之后改名为 `server/schemas/`）：运行、部署、状态、参数等的 Pydantic 模型。
4. `src/prefect/results.py`：结果持久化机制。
5. `src/prefect/cli/`：CLI 命令实现，对照 `--help` 看结构。
6. `src/integrations/prefect-aws/` 等：集成包，理解第三方资源怎么被封装。

## 十、采用建议与边界

Prefect 适合的团队：

- Python-first 数据/工程团队，已有 Python 资产但缺编排层
- 工作流主要是 Python 函数，调度与重试是主要诉求
- 想要"先本地能跑、再上生产"的统一体验
- 需要事件驱动能力但不想自己搭消息总线

不适合：

- 需要完整 SQL 血缘或 schema 管理的资产治理场景——Dagster 的资产模型更直接
- 多语言混合（Java/Go/Rust）任务编排——Temporal 或 Argo Workflows 更合适
- 已有 Airflow 投资且无迁移必要——Airflow 仍然是大数据批处理的成熟方案

上手建议：

1. 把现有脚本加 `@flow` 与 `@task`，本地跑通，确认 Prefect 自动追踪与日志正常。
2. 启动 `prefect server start`，在 UI 上观察默认行为。
3. 把流改成 `.serve(cron="...")`，跑一次真正的部署。
4. 把数据库 backend 换成 Postgres，启动 worker，把 work pool 配到生产环境。
5. 用 Automation 把外部事件接进来，从"定时跑"升级到"响应式"。

## 十一、小结

Prefect 把"工作流编排"从一种独立范式降维成了 Python 装饰器。它没有发明新的执行模型，而是把现有 Python 函数加上调度、缓存、重试、事件、可观测性这些生产必需的能力。对数据团队来说，这意味着可以把大量日常脚本先用 Prefect 包装起来，再视复杂度逐步引入 work pool、Automation、跨 worker 调度，而不必从零搭一套 Airflow 或 Dagster。

如果团队已经在 Python 中写了大量 ETL、训练、特征工程脚本，Prefect 值得从最小工作流开始试；如果工作流核心是数据资产治理而非任务流，可以再看 Dagster；如果团队需要长期、多语言、微服务级别的编排，Temporal 更对位。