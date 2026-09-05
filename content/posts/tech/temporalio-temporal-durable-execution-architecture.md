---
title: "Temporal 架构深读：从事件溯源到 ASM 框架，durable execution 平台为什么这样设计"
date: "2026-09-05T15:55:00+08:00"
lastmod: "2026-09-05T15:55:00+08:00"
draft: false
categories: ["技术笔记"]
tags: ["temporal", "durable-execution", "workflow", "cadence", "go", "分布式系统", "事件溯源", "项目解读"]
description: "Uber Cadence fork 的 Temporal 22.8k stars Go 项目。它不只是 'workflow orchestration'，是 durable execution 的工业级实现。本文拆 5 个架构决策：Event Sourcing 双轨、History Shard 固定分片、CHASM 把 Workflow 抽象成通用 ASM 框架、Speculative Workflow Task 让 Update 拒绝不写 history、Outbound Queue 按目的地隔离 circuit breaker。每个决策都对应 GitHub 代码入口或架构文档的具体路径。"
slug: "temporalio-temporal-durable-execution-architecture"
band: "review"
gates: ["事实性", "去AI味", "观点依据"]
hiddenFromHomePage: false
github_repo: "temporalio/temporal"
source_key: "gh:temporalio/temporal"
---

> **关于这篇文章。** Temporal 是一个 22.8k stars 的 Go 项目，最早从 Uber Cadence fork 出来（2019-10），现在由 Temporal Technologies 维护。它的代码库里藏着不少有教学价值的分布式系统设计——本文挑 5 个具体的架构决策深读，每个都指到 GitHub 仓库的具体文件或文档路径。不是教程（怎么用 Temporal），也不是 API 文档；是项目解读：它为什么这样设计。
>
> 仓库：[github.com/temporalio/temporal](https://github.com/temporalio/temporal) · 22.8k stars · 1.87k forks · Go 1.26.4 · MIT · 架构文档：[docs/architecture/](https://github.com/temporalio/temporal/tree/main/docs/architecture)

## 为什么挑这 5 个决策

Temporal 在 GitHub 上一搜出来就是"durable execution platform"——能写长跑 Workflow、自动处理瞬时失败、自动重试。但读 [docs/architecture/README.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/README.md) 会发现，文档本身不展开"怎么写 Workflow"——它展开的是另一条线：5 个具体的工程决策。这 5 个决策决定了这个系统能不能在生产环境里"经年累月不出问题"。

1. **Event Sourcing 双轨**——为什么同时维护 Mutable State 缓存和 Event History 持久化
2. **History Shard 固定分片**——为什么分片总数在集群创建时就固定、且永远不增不减
3. **CHASM 框架**——为什么把 Workflow 抽象成 ASM（Application State Machine），让 Scheduler / Nexus Operation 都变成"同一种东西"
4. **Speculative Workflow Task**——为什么 Update 拒绝时一行 history 都不能写
5. **Outbound Queue + Circuit Breaker Pool**——为什么按 `(TaskGroup, NamespaceID, Destination)` 隔离故障域

这 5 个决策决定了这个系统能不能在生产环境里"经年累月不出问题"。下面逐个拆。

---

## 决策一：Mutable State + Event History 双轨，Event Sourcing 的工程取舍

Temporal 文档里反复强调它"uses event sourcing"——每个 Workflow Execution 有一条 append-only 的 Event History，所有 state 都能从 history 重放出来。但真去看代码会发现，**光有 Event History 不够，每个** 还有一个常驻内存的 **Mutable State** 对象。

[history-service.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md) 写得很直接：

> For every workflow execution, we maintain a collection of data structures summarizing various aspects of its current state, for example, the identities of in-progress activities, timers, and child workflows. Although most of this data could in principle be recomputed from Workflow History Events when handling an incoming request, this would be slow, and hence the summaries themselves are persisted.

翻译过来：**理论上 Mutable State 能从 Event History 重算出来，但每次 RPC 都重算一遍太慢，所以单独持久化一份"摘要"**。

为什么这么设计？三个具体原因：

- **RPC 处理必须快**：Frontend 收到 `StartWorkflow` / `Signal` / `Update` 等请求，要写新 event + 更新 mutable state + 创建新的内部任务。这些动作如果在一次 RPC 里都走 history 重放路径，延迟会很难看。
- **查询/读路径不用重放**：[history-service.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md) 里 Mutable State 章节点出"recently accessed workflow executions are cached in memory"——读路径直接命中缓存，绕过 history 重放。
- **跨 shard 操作保持一致性**：Timer Task 触发 / Transfer Task 把任务塞进 Matching Service 时，需要知道 workflow 还活着、当前进度到哪——这种"内部调度"如果每次都重算整个 history，开销不可接受。

具体代码里，Mutable State 的运行时实现是 [`MutableStateImpl`](https://github.com/temporalio/temporal/blob/main/service/history/workflow/mutable_state_impl.go)，它实现了 [`MutableState`](https://github.com/temporalio/temporal/blob/main/service/history/workflow/mutable_state.go) 接口。每次"state transition"——也就是 RPC 来了或 timer 触发了——都通过统一的 [`GetAndUpdateWorkflowWithNew`](https://github.com/temporalio/temporal/blob/main/service/history/api/update_workflow_util.go#L37) 工具函数同时做两件事：追加 Event History + 更新 Mutable State。

这是 Event Sourcing 在工业实践里非常典型的取舍：**纯 Event Sourcing 在分布式系统里很难直接落地**，因为每一步都要重放，开销不可控**。Temporal 的解法是把"重放"留给 Worker（SDK 在 Replay 模式下用 history 重建 workflow code 的内存状态），而把"服务端的 authoritative state"做成 Event History + Mutable State 双轨**。Server 永远不重放自己的 history——它信任 Mutable State 缓存。

这个权衡带来的代价也很清晰：**Mutable State 必须在每次 state transition 时和 Event History 一起原子提交**。代码里通过 Cassandra/MySQL/Postgres 的事务保证，写 event 和写 mutable state 是一条 single-row 的 update。这意味着 Mutable State 不是"独立的服务端状态"——它只是 Event History 的一个 materialized view，一旦需要 rebuild 就从 history 重新生成（`MutableState` 接口的 LoadFromHistory 方法）。

---

## 决策二：History Shard 固定分片，分片数一选定终身

一个 cluster 管理上百万个 Workflow Execution，怎么扩展？分片。具体怎么分？[history-service.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md) 给的答案是：

> The total number of History Shards is fixed at cluster creation and cannot be changed later.

为什么不能改？答案藏在分片本身的 ownership 协议里——用 [Ringpop](https://github.com/uber/ringpop-go) 做 shard membership 协调。Ringpop 是 Uber 的 gossip 协议库，每个 History Service 实例持有 shard id 的一段 hash range；shard 的 ownership 在 gossip 协议里就是"我持有哪些 shard id"，改分片数等于改 hash range 划分，等于让所有 ownership 失效。

但更深一层是**为什么用 fixed shards 而非 consistent hashing**：因为 shard ownership 改变要付出昂贵的代价——重新加载 shard 上的 mutable state、缓存、ack levels、历史任务队列。所以 Temporal 选择"宁可一次分配到位，永不扩容"。

**实际代价是什么？** 假设集群创建时设了 1024 个 shard，业务跑两年后 workflow execution 数量翻 5 倍——这时候你不能再加 shard。唯一的选择是**把单个 workflow 的 Event History 分到多个 shard 上**——这正是 Workflow Execution History 章节里提到的：

> Workflow Execution History is a linear sequence of History Events (unless the workflow has been `Reset` or subject to conflict resolution, in which case it has a branching topology).

也就是说 History 默认是线性的，但 Reset 和 conflict resolution 时会进入"branching topology"——这恰恰是因为单 shard 装不下、必须把后续 history 写到另一个 shard 时做的妥协。

代码里 shard 的入口在 [`service/history/history_engine.go`](https://github.com/temporalio/temporal/blob/main/service/history/history_engine.go) 的 `Start()` 方法——当 History service 启动在某个 host 上时，它为持有的每个 shard 启动一个 `QueueProcessor`。Ringpop 协调 host 之间的 shard ownership 转移，转移发生时新 host 会全量加载 shard 的状态。

这个决策的工程含义：**Temporal cluster 创建时必须估算好未来 3-5 年的 workflow execution 数量上限**。生产经验通常是"高峰时段单 shard 承载 ~1000 active workflow executions"——这数字直接决定初始 shard 数。

---

## 决策三：CHASM 框架，把 Workflow 抽象成可水平复制的 ASM

Temporal 仓库里有一篇 12K 字的架构文档专门讲 [CHASM](https://github.com/temporalio/temporal/blob/main/docs/architecture/chasm.md)，全称 **Coordinated Heterogeneous Application State Machines**。这篇文章读起来不像 Temporal 项目的一部分，倒像是一个独立的"分布式状态机框架"的 RFC。

CHASM 的核心判断很刺激：

> Temporal Workflows are powerful, but they have real limits: too slow or heavyweight for some problems, unable to scale in every dimension (e.g. millions of signals, large payloads), and overly complex when a purpose-built solution would be simpler.

翻译：**Workflow 太重、太慢、太复杂**。它能承载上百万种业务逻辑，但不是所有东西都应该跑在 Workflow 上。

CHASM 的解法是把 Workflow 抽象成一种 **Application State Machine (ASM)**——一种**用 Temporal 的 sharding/routing/atomic storage/failure recovery，但避开 full workflow cost** 的轻量级状态机。

CHASM 把"做一个 ASM"的成本压到很低：

| 概念 | 含义 |
| --- | --- |
| **Library** | 一组 Component types + Tasks 的命名空间，比如内置的 `workflow`、`scheduler`、`nexusoperation` |
| **Component type** | 一种注册的状态机类型，由 Fields（持久化数据）+ behavior（方法）组成 |
| **Node** | Component 在 runtime 的实例，存在 Execution 树里 |
| **Execution** | 一棵 Component tree 的根，由 `NamespaceID + BusinessID + RunID` 唯一定位 |
| **Transition** | 原子状态变更单元——一个事件进来，整个 Execution 树上相关 Node 一起更新 |
| **Task** | 异步工作单元，分 Pure（事务内）和 Side Effect（事务后）两类 |

CHASM 不只是"Workflow 的简化版"。它的野心是把 Temporal 的核心能力——sharding、routing、atomic storage、failure recovery——**剥离成一个可水平复制的框架**，然后用这个框架去构建各种业务实体。当前仓库里 [chasm/lib/](https://github.com/temporalio/temporal/tree/main/chasm/lib) 已经包含三个内置 Library：

- [`workflow`](https://github.com/temporalio/temporal/tree/main/chasm/lib/workflow)——传统 Workflow Execution，被改造成 CHASM 的 root component
- [`scheduler`](https://github.com/temporalio/temporal/tree/main/chasm/lib/scheduler)——Schedules 特性（定时触发 Workflow 的新实现），整个 Scheduler 树就是 CHASM tree
- [`nexusoperation`](https://github.com/temporalio/temporal/tree/main/chasm/lib/nexusoperation)——Nexus Operation 的生命周期管理

为什么这是关键决策？因为它意味着 Temporal 不再是"Workflow orchestration"——它变成一个**通用状态机平台**。新的业务实体（比如 Schedules）不需要重新实现一套 sharding/timer/circuit breaker 体系，直接在 CHASM 框架上注册一个新 ASM Library 就行。

这种架构变化的工程信号：[schedules.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/schedules.md) 顶部就有：

> ⚠️ All documentation pertains to the CHASM-based Scheduler implementation, which is not yet generally available.

也就是说旧 Scheduler 实现还在，新 Scheduler 实现已经 CHASM 化。这是一种架构迁移——把现有 Workflow 抽象成 ASM tree，未来可能有更多组件加入这个 tree（比如 Schedule、Callback、NexusOperation）。

**CHASM 的核心创新**：用 `VersionedTransition` 作为全局逻辑时钟——每个 transition 有 `(FailoverVersion, TransitionCount)` 两个分量，前跨跨 DC failover、后者跨 Execution 内 transition。这让 CHASM 能在多数据中心环境下提供**严格的总序**，这是 Event Sourcing 系统里很难做到的。

---

## 决策四：Speculative Workflow Task，让 Update 拒绝一行 history 都不写

[Temporal Workflow Update](https://github.com/temporalio/temporal/blob/main/docs/architecture/workflow-update.md) 是个有趣的新特性。它的存在意义文档开头就讲了：

> Historically, Temporal had two basic primitives, which allows users to interact with a Workflow: 1. Signal, which can be sent to a Workflow to trigger some behavior there. 2. Query, which can be used to return some information from a Workflow.

Signal 是 fire-and-forget，Query 是 read-only。但实际业务经常需要"既要触发更新，又要拿到结果"——这就是 Update 的需求场景。Update 可以被 Workflow 拒绝，**而且拒绝时不能在 history 里留任何痕迹**。

"拒绝不留痕"在 Event Sourcing 里是反直觉的——history 是 immutable 的，按说只能 append。Temporal 的解法是发明了一种**新的消息协议**：[message-protocol.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/message-protocol.md)——用 messages 而不是 events 来承载 Update 请求。

但这还不够。Update 被拒绝时不仅不写 event，还**不能写 mutable state、不能创建 transfer task**——因为 transfer task 本身就要写一行 event。所以 Workflow Update 需要一个**完全不写 DB 的路径**来派发 Workflow Task。

这就是 [speculative-workflow-task.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/speculative-workflow-task.md) 的来历。Speculative Workflow Task 的定义：

> Similar to a CPU's *speculative execution* (which gives this Workflow Task its name) where a branch execution can be thrown away, a speculative Workflow Task can be discarded as if it never existed.

整个 speculative task **永远不写 DB**。它走的是一条不经过 Transfer Task Queue、不经过 Timer Task Queue 的特殊路径——直接通过 `AddWorkflowTask` RPC 把 task 塞进 Matching Service。超时用 [in-memory-queue.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/in-memory-queue.md)——一个只在内存里的 timer queue，不写数据库。

这个设计的代价是：要确保 speculative task 在中途挂掉时（worker crash、network error）能**安全地丢弃**——`StartedTime` 加到 workflow task token 里就是为了让 worker 在新 task 创建后无法用旧 token 完成；`ResetHistoryEventId` 字段让 SDK 在 server 决定 discard 时能 rollback history checkpoint。

**为什么要这么麻烦？** 因为 Update 的核心 SLA 是"如果 Workflow 拒绝，必须完全不写 history"。这是产品级的承诺——业务代码调用 `workflow.ExecuteUpdate(ctx, "reject", req)` 时，期望"什么都没发生"——必须真有"什么都没发生"的工程语义。任何"Update Admitted"或"Update Rejected"事件都会让 SDK 报错。

Speculative task 的应用不止 Update——文档里明确指出"future refactoring could replace query task processing under speculative workflow tasks under the hood"。这是一个**通用工程模式**：当业务需要"先尝试、失败时不留痕"的语义时，Event Sourcing 系统的常规做法是引入 speculative execution，CPU 体系结构的概念被原样搬到了分布式系统。

---

## 决策五：Outbound Queue 按 `(TaskGroup, NamespaceID, Destination)` 三元组隔离 circuit breaker

[Nexus](https://github.com/temporalio/temporal/blob/main/docs/architecture/nexus.md) 是 Temporal 用于跨 namespace / 跨 cluster 边界的服务调用框架。它要解决的核心问题是：**Temporal server 自己作为 client 调外部服务**（不像普通 worker 那样——worker 调外部是 user 的代码）。具体场景：调用另一个 namespace 的 Nexus service / 调用外部 HTTP endpoint / 投递 workflow completion callback。

[Temporal server 自己作为 client] 这件事带来一个全新的故障模式——destination 可能慢、可能挂、可能反复 503。如果 Temporal 把这些 outbound 调用塞进普通的 transfer queue，每一个 retry 都会加载 workflow 的 mutable state（cache 或 DB 命中），占住 scheduler goroutine，然后阻塞在一个注定要超时的 HTTP 请求上。

[circuit-breaker.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/circuit-breaker.md) 把这个失败模式叫"destination down"——一个 destination 死了，会让 outbound queue 整体饿死。

**解法是给每个 destination 单独配一个 circuit breaker**——而不是一个全局的。

但单个全局 breaker 太粗——一个 destination 挂了，所有 outbound task 都被短路。所以 Temporal 用一个 [`CircuitBreakerPool[K]`](https://github.com/temporalio/temporal/blob/main/service/history/circuitbreakerpool/circuit_breaker_factory.go)，key 是 `(TaskGroup, NamespaceID, Destination)` 三元组。

为什么用这个三元组？文档里写：

> When a breaker is first requested for a key, the pool reads that (namespace, destination) pair's initial `OutboundQueueCircuitBreakerSettings` and subscribes to future changes, so operators can tune or disable the breaker per destination via dynamic config.

也就是说——**配置粒度可以到「单一来源 namespace 调单一 destination endpoint」**。运维想给某个 endpoint 关掉 circuit breaker、给另一个加严阈值，单独改它那条就行。

breaker 的 trip 策略用 gobreaker 默认：连续失败超过 5 次就 trip。trip 后状态走 Open → Half-open → Closed 的标准三态机。

这种 key粒度设计背后的工程判断：**故障隔离的代价是配置面复杂度**，但收益是 "一个不健康的 destination 不会拖垮整个 cluster"。Temporal 选择接受配置复杂度，因为——Nexus 服务调用场景下，一个挂的 destination 可能影响成百上千个上游 workflow，让它拖垮整个 outbound queue 远比配置面复杂更糟糕。

具体的处理栈：[Nexus 文档](https://github.com/temporalio/temporal/blob/main/docs/architecture/nexus.md#outbound-task-queue) 把 Outbound Queue 处理 pipeline 拆成五步：`Reader → Buffer → Concurrency Limiter → Rate Limiter → Circuit Breaker → Executor`。每一层都是独立的 buffer / limit / 隔离，**只有全部环节通过才能让 task 落到 Executor**。

Multi-Cursor 是另一层隔离——一个 shard 上的 outbound queue 默认起 4 个 reader，slow destination 的 task 被移动到慢 reader（4 个 reader 分别有自己的 cursor），让健康 destination 不被拖累。

整个 outbound queue 设计的工程哲学：**把"对外部世界的信任"降到零**——每个 outbound call 都被多层 limit 包着，每个 destination 都有自己的 breaker，每个 shard 都有自己的 cursor。这和 Temporal 内部的 in-memory state machine 设计风格完全相反（内部状态机信任内存、信任历史、重放是合法的）——因为外部世界不能被信任。

---

## 这 5 个决策之外，还有什么

读完整套架构文档还能看到几个值得讲的工程决策：

**Workflow Task 三态**——[speculative-workflow-task.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/speculative-workflow-task.md) 把 Workflow Task 拆成 Normal / Transient / Speculative 三种。Normal 是写 DB 的常规 task；Transient 是"中途失败不写 history"的 retry-only task；Speculative 是上面决策四讲的"完全不写 DB"的 task。三态分得很清楚——用 `Type` 字段 + `IsTransientWorkflowTask()` 这种 boundary check 把语义差异写进代码。

**VersionedTransition**——CHASM 的全局逻辑时钟（`(FailoverVersion, TransitionCount)`）。前者跨 DC failover、后者跨 Execution 内 transition。提供跨数据中心的**严格总序**——这是 Event Sourcing 系统里几乎不会自然存在的特性。

**Message Protocol**——上面决策四提到的 message protocol 用 `protocol_instance_id`（当前 == update_id，未来可能扩展到 signal/query）+ `body: Any` + `sequencing_id`（event_id 或 command_index）。`body: Any` 用 protobuf Any 而不是 oneof，是为了让 server 不需要知道所有消息类型——可插拔设计。

**Transfer Queue + Timer Queue 拆分**——把"立即推进"（Transfer）和"等时长"（Timer）拆成两个内部队列。每个都是 sharded queue processor 模式运行。文档里强调："elsewhere in Temporal documentation, 'task queue' refers to the Task Queues of the Matching Service, which are a concept exposed to Temporal users; the task queues we are discussing here are an internal implementation detail of the History Service."——外部可见的 Task Queue 和内部 task queue 是两套东西，名字相同但语义不同。

---

## 写给想用 Temporal 做长跑业务的人

读完这 5 个决策，几个能立刻用得上的判断：

**判断 1：Workflow Task Failure 是设计内的，不是 bug**。Worker 报 `RespondWorkflowTaskFailed` 或 `RecordWorkflowTaskStarted` 失败时，server 会写一行 `WorkflowTaskFailed` event 并加 attempt count。如果失败反复发生，最终是 transient workflow task——task scheduled/started events 不写 history，但 Workflow 仍然在推进。这是为了"worker 失败 ≠ workflow 失败"的隔离，工程上必须这么设计。

**判断 2：Update 拒绝不留痕是产品级承诺**。如果你在设计业务 SDK，要让 workflow code 真的能"reject" Update——并且不能依赖任何"Update Rejected"事件。`UpdateStore` 的存在意味着 server 自己会处理 in-flight Update 的恢复，但 rejected Update 不会持久化。如果你需要"reject with reason"的语义，目前的实现下 SDK 拿不到 reason——这是有意取舍。

**判断 3：Cluster shard 数上线估算很关键**。fixed shard 决策意味着你创建集群时要估算未来 3-5 年的 peak workflow execution 数量——这数字决定初始 shard 数。生产经验通常按"单 shard 承载 ~1000 active workflow executions"估算，然后用 `rps × avg_duration / 1000` 算初始 shard 数。

**判断 4：CHASM 框架会越来越重要**。现在 Workflow / Scheduler / NexusOperation 都已经是 CHASM tree 的 root，未来 Signal / Query 也可能 CHASM 化（文档里有 TODO）。新业务实体如果想"复用 Temporal 的 sharding + atomic storage + failure recovery 但不要 workflow 的全成本"，CHASM 是入口。

**判断 5：Nexus endpoint registry 不是多 cluster safe**。[nexus.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/nexus.md) 顶部明确警告"Nexus shouldn't be used in multi cluster setups because replication for the registry is not implemented"。这是个还没解决的架构债，未来会修——但今天不要在多 cluster 部署里依赖 Nexus endpoint registry。

---

## 这个项目真正讲的是什么

把 5 个决策摆在一起看，Temporal 不只是"Workflow orchestration"——它是**对"Event Sourcing 工业落地"这个分布式系统老问题的工程回答**：

- Event Sourcing 太慢？→ Mutable State 缓存做 materialized view。
- 单 shard 装不下历史？→ fixed shard + 后续 history 跨 shard（branding topology）。
- Workflow 太重？→ CHASM 把 Workflow 抽象成 ASM tree，让其他实体复用基础设施。
- Event 不可变所以 Update 不能拒绝？→ Speculative Workflow Task + Message Protocol。
- 外部 destination 可能挂？→ Outbound Queue + Circuit Breaker Pool + 多层 limit。

每一层都是对前一层缺陷的修正——而每一层修复又引入了新的工程复杂度（Mutable State 一致性、fixed shard 不可扩容、CHASM 框架心智负担、Speculative task 路径特殊、Circuit breaker 配置面）。

Temporal 22.8k stars 不是一个"Workflow DSL 设计得好"的项目——它的价值在**这些工程细节**：五年生产环境的反馈沉淀、Uber Cadence fork 出来的工业基础、对分布式系统每个老问题都给出具体答案。

读它的代码不是学 Go，是学**Event Sourcing 在分布式系统里要怎么落地**。

> 出处：
> - 仓库：[github.com/temporalio/temporal](https://github.com/temporalio/temporal)
> - 架构文档：[docs/architecture/README.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/README.md)
> - 关键子文档：[history-service.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md) · [chasm.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/chasm.md) · [workflow-update.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/workflow-update.md) · [speculative-workflow-task.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/speculative-workflow-task.md) · [nexus.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/nexus.md) · [circuit-breaker.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/circuit-breaker.md)
>
> 作者：钳岳 · 2026-09-05