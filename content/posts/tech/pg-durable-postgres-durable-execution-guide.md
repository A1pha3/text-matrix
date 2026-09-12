+++
github_repo = "microsoft/pg_durable"
source_key = "gh:microsoft/pg_durable"
date = '2026-06-07T23:03:00+08:00'
lastmod = '2026-09-06T12:00:00+08:00'
draft = false
title = 'pg_durable 解析：把 durable execution 直接搬进 PostgreSQL，Microsoft 给后端工程师的零基础设施工作流'
slug = 'pg-durable-postgres-durable-execution-guide'
description = '微软开源的 PostgreSQL 扩展 pg_durable，把 durable execution 模式从 Temporal / Airflow / Step Functions 收回到 SQL 内：顺序、并行、循环、审批全用 ~> & |=> 这类操作符表达，状态和检查点落在数据库自己的表里。本文对照官方 README 与 User Guide 梳理原理、DSL、监控与生产注意事项。'
categories = ['技术笔记']
tags = ['PostgreSQL', '数据库', '工作流', 'Microsoft']
+++

# pg_durable 解析：把 durable execution 直接搬进 PostgreSQL，Microsoft 给后端工程师的零基础设施工作流

> **目标读者**：负责后台数据流水线、AI 嵌入管道、运维 runbook 的后端 / 数据工程师和 DBA
> **核心问题**：能不能不引入 Temporal、Airflow、Step Functions、pg_cron+worker，就在 PostgreSQL 内部跑出可恢复、可检查点、可并行 fan-out 的长跑工作流？
> **难度**：⭐⭐⭐（中级，需要熟悉 PostgreSQL 扩展和 SQL 函数）
> **预计阅读时间**：40 分钟

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

durable execution（持久化执行）作为一种行业模式，就是为了把以上五处合并到一个 runtime 内部：每步执行前先落盘意图，执行后落盘结果，崩溃后按日志重放，已完成的步骤不重跑。Temporal、AWS Step Functions、Airflow、DBOS 都属于这个流派，区别只在 runtime 放在哪里。

### 1.2 pg_durable 的答案：runtime 就是 PostgreSQL 本身

`microsoft/pg_durable` 的设计目标是：**让 durable execution 直接在 PostgreSQL 内部跑**。它是一个用 pgrx 框架构建的 PG 扩展，内部托管了微软的 duroxide 编排运行时和 duroxide-pg 状态提供者——README 的原话是 "everything runs inside the PostgreSQL server, no external services"。工作流的图定义、实例状态、检查点、重试进度，全部落在数据库自己的表里，随业务数据一起备份、一起受同一套权限和审计模型管束。

需要先校准预期的是项目状态：**截至 2026 年 9 月，pg_durable 仍处于 Preview 阶段**（README 原话 "This project is currently in preview"），仅支持 PostgreSQL 17 和 18，Docker 镜像只有 linux/amd64。GitHub 上约 2.8k stars。它和微软的云服务 Azure HorizonDB 一起出场，README 邀请用户 "Try pg_durable now in Azure HorizonDB"——云上开箱即用，自托管则要自己装扩展。

它在这个光谱里的位置可以压成一句：**「业务逻辑大部分本来就在 SQL 里」的团队，可以用一个扩展换掉 cron + 状态表 + 一组 worker 的整套胶水。**

---

## 二、原理：durable execution 的 SQL 化

### 2.1 用 SQL 操作符画工作流图

pg_durable 把一个工作流建模成 **SQL 步骤组成的图**。步骤就是普通的 SQL 字符串，操作符负责把它们连起来：

| 操作符 | 名称 | 作用 | 官方示例 |
|---|---|---|---|
| `~>` | 顺序 | 左边跑完跑右边 | `'SELECT 1' ~> 'SELECT 2'` |
| `\|=>` | 命名绑定 | 把左边结果存为变量 | `'SELECT 1' \|=> 'myvar'` |
| `&` | 并行 join | 同时跑，等全部完成 | `'SELECT 1' & 'SELECT 2'` |
| `\|` | 并行 race | 同时跑，先完成者胜 | `fast_query \| slow_query` |
| `?>` / `!>` | 条件分支 | 真 / 假各走一支 | `cond ?> then_branch !> else_branch` |
| `@>` | 永久循环 | 前缀修饰，无限重复 | `@> body` |

配套还有一组 `df.*` 函数补足操作符表达不了的动作：`df.join()` / `df.join3()`（并行）、`df.race()`（竞速）、`df.if(cond, then, else)`（分支）、`df.loop(body, cond)`（条件循环）、`df.sleep(seconds)`（延时）、`df.wait_for_schedule(cron)`（cron 触发）、`df.wait_for_signal(name)`（等外部信号）、`df.http(url, method, body, headers, timeout)`（出站 HTTP）。

有两个设计细节直接影响怎么写代码。

**图在内存里构建，`df.start()` 才落库。** 拼接表达式只是生成一个 JSON 图结构：

```sql
-- 这一句只返回图的 JSON 表示，不碰数据库
SELECT 'SELECT 1' ~> 'SELECT 2';

-- 只有 df.start() 把图写进数据库并开始执行
SELECT df.start('SELECT 1' ~> 'SELECT 2');
```

`df.start()` 返回一个 8 字符的十六进制实例 ID（如 `a1b2c3d4`），后续的 `df.status(id)`、`df.result(id)`、`df.cancel(id)` 都用它。

**启动默认跟随调用者的事务。** `df.start()` 参与 caller 的当前事务——事务回滚，工作流就像没发生过一样。要让它穿越回滚（典型场景：业务写入失败回滚，但审计日志的记录任务必须留下），加 `transaction_mode => 'new'`，启动动作会在独立连接上提交。官方文档对它设了明确的边界：每次 `'new'` 启动要占一个额外后端连接，集群级别的并发上限由 `pg_durable.max_new_transaction_starts`（默认 2）控制，所以官方提醒不要放在行触发器这类高扇出调用点上。

### 2.2 状态在哪：df.* 用户可见层 + duroxide.* 运行时

pg_durable 落地的数据分两层：

- `df.instances` — workflow 实例的状态、label、提交者（`submitted_by`）
- `df.nodes` — 图中每个节点的定义、状态和结果
- `df.vars` — durable 变量（跨步骤、跨实例的键值存储），带 `owner` 列做按用户隔离；官方提醒不要在这里存明文密钥
- `duroxide.*` schema — 运行时内部状态（实例历史、工作队列），由扩展的后台 worker 拥有，用户一般不直接读

普通用户对 `df.instances` / `df.nodes` 拿到的是 `SELECT` + `INSERT` 加列级 `UPDATE`（只能改 `status` / `updated_at`，用于取消），行级安全（RLS）保证每个用户只能看到和管理自己提交的实例。

容错语义照抄 durable execution 的标准定义，USER_GUIDE 原话：

- 已完成的节点不会重跑
- 进行中的节点从最近的 checkpoint 恢复
- 未开始的节点等服务器重启后执行

对运维的直接含义是：**不需要额外的 Redis，也不需要额外的 Temporal 集群。一次 PG 备份 = 整个 workflow 状态 + 业务数据。**

### 2.3 和「pg_cron + workers + 状态表」传统方案的对比

| 维度 | pg_cron + workers | Airflow / Temporal | pg_durable |
|---|---|---|---|
| 状态存储 | 业务 DB + 队列 | 独立 runtime DB | PostgreSQL `df.*` / `duroxide.*` 表 |
| 检查点 | 自建 status 列 | runtime 内部 | 每个节点一次，随 PG 事务落盘 |
| 失败恢复 | 重新拼装 | 重新触发 DAG | 从 checkpoint 自动续跑 |
| 并行 fan-out | 自己写 worker | DAG 配置 | `&` / `df.join()` / `df.join3()` |
| 定时 | pg_cron 表达式 | scheduler 组件 | `df.wait_for_schedule()` + `@>` 循环 |
| 可见性 | 多张表 join | runtime UI | `df.list_instances()` 等直接 SQL 查询 |
| 基础设施 | Redis/队列 + worker | 额外 K8s 集群 | 仅一个 PG 扩展 + 后台 worker |
| 备份模型 | 双份（业务 + runtime） | 三份（业务 + runtime + 队列） | 一份（业务即 runtime） |

后端团队拿到的是：**少一套基础设施、少一份数据一致性风险、少一个权限体系要打通。** 代价同样清楚：workflow 的表达力被限制在「SQL 步骤 + 官方给出的几种控制流」之内，README 的原话是 "The model is intentionally SQL-shaped"——这是有意的设计选择，不是缺陷陈述。

---

## 三、任务流案例：一条真实的 embedding 管道

README 的 Quick Example 很贴近 AI 工程的日常——批量给未处理文档算 embedding 并标记，全文如下：

```sql
SELECT df.start(
    'SELECT id FROM documents WHERE processed = false LIMIT 100' |=> 'batch'
    ~> 'UPDATE documents SET processed = true WHERE id IN (SELECT id FROM $batch.*)'
);
```

逐段拆开：

- `'SELECT id FROM documents WHERE processed = false LIMIT 100' |=> 'batch'`：第一步查出一批待处理文档的 id，`|=>` 把这个多行结果集绑定成变量 `batch`
- `~> 'UPDATE ... FROM $batch.*'`：第二步用 `$batch.*` 行集展开语法，把上一步的多行结果原地展开成 `(VALUES (1,'Alice'), (2,'Bob')) AS batch(id, name)` 形态的内联子查询，直接 `IN` 进去
- 整条链在任何一步崩溃，恢复时**只重做未完成的节点**

变量引用有一套完整的规则，官方给出的语义表值得记一下：

| 写法 | 上一步无行 | 值为 NULL |
|---|---|---|
| `$name` / `$name.col` | 整个实例**失败** | 实例**失败** |
| `$name?` / `$name.col?` | 替换为 NULL | 替换为 NULL |

也就是说，默认情况下「引用一个空结果」是硬错误而不是静默 NULL——想宽容处理必须显式写 `?`。访问具体列用点号：`$user.id`。这条规则决定了你的管道在数据异常时是「快速失败」还是「带着 NULL 继续跑」。

再往上叠真实生产里常见的三种结构，代码全部来自官方 User Guide。

**出站 HTTP，拿响应字段写库：**

```sql
SELECT df.start(
    df.http('https://api.example.com/users/123', 'GET') |=> 'user'
    ~> 'INSERT INTO users_cache (data) VALUES (($user.body)::jsonb)',
    'fetch-user'
);
```

`df.http()` 的返回值是个 JSON 信封：`status`、`body`、`headers`、`ok`、`duration_ms`，用 `$user.body` 这样的点号直接取。文本响应原样存放；二进制（图片、PDF）自动 base64 编码并标记 `"encoding": "base64"`。失败语义也有明确划分：4xx 会作为正常结果返回给工作流自己处理，5xx、超时和网络错误才算活动失败、进入重试。

**人工审批：等外部信号再继续。** 官方把它列为 signals 的头号用途（human-in-the-loop）：

```sql
SELECT df.start(
    'SELECT id, total FROM orders WHERE id = 1' |=> 'order'
    ~> df.wait_for_signal('approval', 86400) |=> 'sig'  -- 24h 超时
    ~> df.if(
        'SELECT NOT ($sig::jsonb->>''timed_out'')::boolean
            AND ($sig::jsonb->''data''->>''approved'')::boolean',
        'UPDATE orders SET status = ''approved'' WHERE id = $order.id',
        'UPDATE orders SET status = ''rejected'' WHERE id = $order.id'
    ),
    'order-approval'
);

-- 审批人在任何外部系统里发出信号，工作流随即恢复
SELECT df.signal('a1b2c3d4', 'approval', '{"approved": true, "approver": "jane@acme.com"}');
```

`df.wait_for_signal()` 会把实例挂起，直到 `df.signal()` 送来数据或超时。信号结果带 `timed_out` 标记，超时不算失败，由工作流自己决定走哪支。多方会签用 `df.join3()` 把三个 `wait_for_signal` 并起来，等全部到位。

**cron 定时：`wait_for_schedule` 配合永久循环。**

```sql
-- 每天凌晨归档已完成订单
SELECT df.start(
    @> (
        df.wait_for_schedule('0 0 * * *')
        ~> 'UPDATE playground.orders SET status = ''archived''
            WHERE status = ''completed''
            AND processed_at < now() - interval ''7 days'''
    ),
    'daily-order-archive'
);
```

`@>` 让函数永久循环，每轮迭代通过 continue-as-new 以全新状态重启，耐久性不受影响。要停掉它，`df.cancel('实例ID')` 或先按 label 查 ID：`SELECT instance_id FROM df.list_instances() WHERE label = 'daily-order-archive'`。

一条流程串下来：**查询待办 → 命名绑定 → SQL 步骤消费结果 → 出站调 API → 挂起等审批 → 定时收尾**，全部发生在数据库内部，没有任何一个环节需要引入外部 runtime。

---

## 四、适用与不适用：什么时候该上 pg_durable

README 自己列了「适合我」的画像：

- 后端 / 数据工程师：希望 workflow 和它操作的数据**物理上放在一起**
- DBA / SRE：自动化 runbook，**必须能跨重启存活 + SQL 可审计**
- 数据 / AI pipeline 团队：向量嵌入管道、摄取管道（stage→去重→转换→发布）、fan-out 聚合、外部 API 工作流

README 也明确列了「不适合」的边界：

- 任务已经是一个 `INSERT ... SELECT` 或一句普通 SQL
- 你要的是亚毫秒级同步请求处理（pg_durable 是**后台执行**）
- 环境不允许装扩展或起 background worker
- workflow 主要活在 PostgreSQL 之外，横跨大量异构系统
- 业务逻辑是任意应用代码，映射不到 SQL 步骤 / 分支 / 循环 / HTTP

实际工程判断建议：

- **替换 pg_cron + 一张 status 表 + 几个 Python worker** → 直接上 pg_durable，收益最大
- **替换 Temporal / Airflow** → 评估：你的 DAG 是不是绝大部分都在 SQL 内部完成？是 → 值得试；否 → 保留外部 runtime
- **AI 嵌入管道 / 数据 ingest / 月度对账** → README 点名的目标场景

还有一个结构性限制要先知道：**后台 worker 只服务一个数据库**（由 `pg_durable.database` GUC 指定，默认 `postgres`）。想让多个数据库各有各的 workflow，目前的办法是在各自的数据库里装扩展并分别配置 worker。

---

## 五、横向对比：pg_durable vs DBOS vs Temporal vs Airflow

| 维度 | pg_durable | DBOS | Temporal | Airflow |
|---|---|---|---|---|
| 形态 | PG 扩展 | PG + Python/TS SDK | 独立 Go runtime | 独立 Python runtime |
| 语言 | SQL | Python / TypeScript | 多语言 SDK | Python |
| 学习曲线 | 低（SQL） | 中（SDK + 装饰器） | 中高（worker 模型） | 中（DAG 配置） |
| 部署 | PG 装上就完事 | PG + 调度器 | 集群 + DB | 集群 + executor |
| 检查点粒度 | 节点 | step | event | task |
| 跨工作流事务 | PG 事务直接覆盖 | PG 事务 | saga 模式 | XCom + 人工拼装 |
| 适用规模 | 单 PG 实例 | 中小 | 大 | 大 |
| 生态成熟度 | 新（截至 2026-09 仍为 Preview） | 较新 | 老牌 | 老牌 |

一句话：**「业务逻辑大部分在 SQL 里」且「不想再养一套 workflow 集群」的团队，pg_durable 是目前表达成本最低的选择；前提是你能接受 Preview 阶段的 API 变动风险。**

---

## 六、和 Azure HorizonDB 的关系

pg_durable 和微软的 **Azure HorizonDB**（内置 pg_durable 的 PostgreSQL 云服务）一起出场。README 给出的分工是：

- Azure 用户：在 HorizonDB 里直接可用，不用操心扩展安装和后台 worker 配置
- 自托管用户：在 PostgreSQL 17 / 18 上自行安装（Debian 包、Docker 镜像、PGXN 或源码编译四条路）

自托管安装完成后的启用是固定三步：把 `pg_durable` 加进 `shared_preload_libraries`，重启 PostgreSQL，然后 `CREATE EXTENSION pg_durable;`。第三步之后后台 worker 会异步初始化引擎 schema（通常几秒），期间 `df.*` 函数会返回「background worker not yet initialized」的提示，稍等重试即可。给应用角色授权用一句 `SELECT df.grant_usage('app_role');`。

---

## 七、生产落地的真实清单

pg_durable 把编排复杂度收进了数据库，但有几类约束是文档明确写出的，上生产前应该逐条过。

**1. 连接预算要先算。** 后台 worker 维护三类连接池，外加每个调用 `df.start()` 的后端会话各占一条：

| 连接类别 | 用途 | GUC | 默认 |
|---|---|---|---|
| Management pool | 生命周期检查、图加载、状态更新 | `pg_durable.max_management_connections` | 6 |
| Duroxide pool | 编排状态、LISTEN/NOTIFY 派发 | `pg_durable.max_duroxide_connections` | 10 |
| User-execution | 每个 SQL 节点的执行连接，以提交者身份认证 | `pg_durable.max_user_connections` | 10 |
| New-start loopback | `transaction_mode => 'new'` 的额外启动会话 | `pg_durable.max_new_transaction_starts` | 2 |

总预算公式：`Total = 三类池 + max_new_transaction_starts + 活跃后端会话数`。默认配置下 5 个已连接用户就是 `6 + 10 + 10 + 2 + 5 = 33` 条连接，务必确认 `max_connections` 装得下。这些 GUC 都是 postmaster 级，改完要重启。另外 `pg_durable.worker_role`（默认 `postgres`）必须是超级用户。

**2. 过载时是排队，不是立刻失败。** 用户执行连接池占满后，后续 SQL 节点会排队等槽位；等待超过 `pg_durable.execution_acquire_timeout`（默认 30 秒）才报 `connection limit reached` 并把工作流置为 `failed`，已拿到槽位的兄弟节点继续跑。容量规划要按这条超时链路来，而不是假设高并发时请求会被立即拒绝。

**3. 权限模型：以提交者身份执行。** worker 直接以 `submitted_by`（调用 `df.start()` 时的 `current_user`）身份建立连接执行 SQL，没有 `SET ROLE` 中间层。两个推论：

- 提交角色必须有 `LOGIN` 属性，`SET ROLE` 切到 NOLOGIN 组角色后再提交会被拒绝
- 在 `SECURITY DEFINER` 函数里调用 `df.start()`，捕获的是**函数所有者**的身份——官方专门警告了这个提权路径：不要把不可信 SQL 从 SECURITY DEFINER 上下文传给 `df.start()`

一个已声明的例外：`df.http()` 目前以**后台 worker 的权限**出站，没有按用户隔离的 URL 白名单，多租户场景要自己把关。

**4. 运维动作各有讲究。** `DROP EXTENSION pg_durable` 必须 `CASCADE`（worker 建的表不完全归扩展所有）；drop 后 worker 每 5 秒轮询一次，关闭运行时约需 10 秒，重建要等 15–20 秒。角色被 drop 会让其未完成的实例直接转 `failed`。Docker 镜像官方声明仅用于评估学习，不要上生产；镜像以超级用户运行且 HTTP 出口默认放行 Azure 域名。

**5. 一个最常见的坑：`df.start()` 返回了 ID，实例却永远不动。** 官方 Troubleshooting 列出的头号原因是 `pg_durable` 没进 `shared_preload_libraries`——扩展装了、函数能用、图也落库了，但后台 worker 根本没在跑。先用 `SHOW shared_preload_libraries;` 确认，补上配置并重启后，日志里应出现 `pg_durable: duroxide runtime started`。反过来的组合同样要警惕：配了 `shared_preload_libraries` 却没执行 `CREATE EXTENSION`，worker 会一直空转等待。

**6. 监控不用接外部系统。** 实例列表用 `df.list_instances()`（支持按 status / label 过滤和游标分页），单个实例详情 `df.instance_info(id)`、执行历史 `df.instance_executions(id, n)`、逐节点状态 `df.instance_nodes(id)`，图结构预览 `df.explain(id)`。卡住的 workflow 长什么样、卡在哪一步，SQL 一查便知。

**7. 升级两件事。** PG 大版本只支持 17/18，升级前先在测试集群验证 `df.*` / `duroxide.*` 数据兼容性；扩展升级后要重跑 `df.grant_usage()`——`GRANT EXECUTE` 只对授权时已存在的函数生效，新加的 `df.*` 函数不会自动带权限。

---

## 八、总结：给后端工程师的决策清单

- ✅ **强推荐**：你的 workflow 主体在 SQL 内，且现状是 pg_cron + 几张状态表 + 一组 worker
- ✅ **推荐**：你要做 AI 嵌入管道 / 月度对账 / 数据 ingest pipeline
- ✅ **值得评估**：你已经在 Azure 上用 PG，且不愿意引入 Temporal 这种大 runtime
- ⚠️ **谨慎**：workflow 跨大量外部 SaaS 编排、每一步都需要复杂应用代码，或你无法接受 Preview 期的 API 变动
- ❌ **不推荐**：你要的是同步请求级别的 saga，或业务逻辑基本不在 SQL 里

起步路径很直接：拉一个 Docker 镜像在本地库里跑通 Quick Example，再把一条真实的 cron + 状态表流程搬过去对比维护成本。

**GitHub**: [microsoft/pg_durable](https://github.com/microsoft/pg_durable)
**许可**: PostgreSQL License（开源，免费商用）
**支持版本**: PostgreSQL 17 / 18
**状态**: Preview（截至 2026-09）

---

*2026-06-07 · GitHub Trending 收录 · 文本矩阵「技术笔记」专栏*
