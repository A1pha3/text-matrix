---
title: "Temporal 架构深读：从事件溯源到 ASM 框架，durable execution 平台为什么这样设计"
date: "2026-09-05T15:55:00+08:00"
lastmod: "2026-09-15T10:30:00+08:00"
draft: false
categories: ["技术笔记"]
tags: ["temporal", "durable-execution", "workflow", "cadence", "go", "分布式系统", "事件溯源", "项目解读"]
description: "Uber Cadence fork 的 Temporal，23k stars 的 Go 项目。它不只是 'workflow orchestration'，是 durable execution 的工业级实现。本文拆 5 个架构决策：Event Sourcing 双轨、History Shard 固定分片、CHASM 把 Workflow 抽象成通用 ASM 框架、Speculative Workflow Task 让 Update 拒绝不写 history、Outbound Queue 按目的地隔离 circuit breaker。每个决策都对应 GitHub 代码入口或架构文档的具体路径。"
slug: "temporalio-temporal-durable-execution-architecture"
band: "review"
gates: ["事实性", "去AI味", "观点依据"]
hiddenFromHomePage: false
github_repo: "temporalio/temporal"
source_key: "gh:temporalio/temporal"
---

> **关于这篇文章。** Temporal 是一个 23k stars 的 Go 项目，最早从 Uber Cadence fork 出来（2019-10），现在由 Temporal Technologies 维护。它的代码库里藏着不少有教学价值的分布式系统设计——本文挑 5 个具体的架构决策深读，每个都指到 GitHub 仓库的具体文件或文档路径。不是教程（怎么用 Temporal），也不是 API 文档；是项目解读：它为什么这样设计。
>
> 仓库：[github.com/temporalio/temporal](https://github.com/temporalio/temporal) · 23k stars · 1.9k forks · go.mod 声明 go 1.27.0 · MIT · 架构文档：[docs/architecture/](https://github.com/temporalio/temporal/tree/main/docs/architecture)

## 为什么挑这 5 个决策

Temporal 在 GitHub 上一搜出来就是"durable execution platform"——能写长跑 Workflow、自动处理瞬时失败、自动重试。但读 [docs/architecture/README.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/README.md) 会发现，文档本身不展开"怎么写 Workflow"——它展开的是另一条线：5 个具体的工程决策。这 5 个决策决定了这个系统能不能在生产环境里"经年累月不出问题"。

1. **Event Sourcing 双轨**——为什么同时维护 Mutable State 缓存和 Event History 持久化
2. **History Shard 固定分片**——为什么分片总数在集群创建时就固定、且永远不增不减
3. **CHASM 框架**——为什么把 Workflow 抽象成 ASM（Application State Machine），让 Scheduler / Nexus Operation 都变成"同一种东西"
4. **Speculative Workflow Task**——为什么 Update 拒绝时一行 history 都不能写
5. **Outbound Queue + Circuit Breaker Pool**——为什么按 `(TaskGroup, NamespaceID, Destination)` 隔离故障域

下表把这 5 个决策、它们各自要回答的问题、以及对应的架构文档先摆在一起，往下读时可直接对照：

| 决策 | 要回答的问题 | 对应文档 |
| --- | --- | --- |
| Event Sourcing 双轨 | 服务端读路径为什么不能靠重放 | `history-service.md` |
| History Shard 固定分片 | 为什么分片数一选定终身 | `history-service.md` |
| CHASM 框架 | Workflow 太重时，其他业务实体怎么办 | `chasm.md` |
| Speculative Workflow Task | 被拒绝的 Update 如何在 history 上不留痕 | `speculative-workflow-task.md`、`workflow-update.md` |
| Outbound Queue 隔离 | 一个不健康的 destination 如何不拖垮全局 | `nexus.md`、`circuit-breaker.md` |

下面逐个拆。

---

## 决策一：Mutable State + Event History 双轨，Event Sourcing 的工程取舍

Temporal 文档里反复强调它"uses event sourcing"——每个 Workflow Execution 有一条 append-only 的 Event History，所有 state 都能从 history 重放出来。但真去看代码和文档会发现，**光有 Event History 不够——每个 execution 还有一个单独持久化的 Mutable State**。

[history-service.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md) 写得很直接：

> For every workflow execution, we maintain a collection of data structures summarizing various aspects of its current state, for example, the identities of in-progress activities, timers, and child workflows. Although most of this data could in principle be recomputed from Workflow History Events when handling an incoming request, this would be slow, and hence the summaries themselves are persisted.

也就是说：理论上 Mutable State 能从 Event History 重算出来，但每次 RPC 都重算一遍太慢，所以单独持久化一份"摘要"。

为什么这么设计？三个具体原因：

- **RPC 处理必须快**：Frontend 收到 `StartWorkflow` / `Signal` / `Update` 等请求，要写新 event + 更新 mutable state + 创建新的内部任务。这些动作如果在一次 RPC 里都走 history 重放路径，延迟会很难看。
- **查询/读路径不用重放**：[history-service.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md) 里 Mutable State 章节点出"recently accessed workflow executions are cached in memory"——读路径直接命中缓存，绕过 history 重放。
- **跨 shard 操作保持一致性**：Timer Task 触发 / Transfer Task 把任务塞进 Matching Service 时，需要知道 workflow 还活着、当前进度到哪——这种"内部调度"如果每次都重算整个 history，开销不可接受。

具体代码里，Mutable State 的运行时实现是 [`MutableStateImpl`](https://github.com/temporalio/temporal/blob/main/service/history/workflow/mutable_state_impl.go)，它实现了 [`MutableState`](https://github.com/temporalio/temporal/blob/main/service/history/workflow/mutable_state.go) 接口。每次"state transition"——也就是 RPC 来了或 timer 触发了——都通过统一的 [`GetAndUpdateWorkflowWithNew`](https://github.com/temporalio/temporal/blob/main/service/history/api/update_workflow_util.go#L14) 工具函数同时做两件事：追加 Event History + 更新 Mutable State。

这是 Event Sourcing 在工业实践里非常典型的取舍：**纯 Event Sourcing 在服务端读路径上很难直接落地，因为每一步都要重放，开销不可控。Temporal 的解法是把"重放"留给 Worker（SDK 在 Replay 模式下用 history 重建 workflow code 的内存状态），而把"服务端的 authoritative state"做成 Event History + Mutable State 双轨**。Server 永远不重放自己的 history——它信任 Mutable State 缓存。

这个权衡带来的代价也很清晰：**Mutable State 必须在每次 state transition 时和 Event History 一起原子提交**。这一点靠存储层事务保证。另外，Mutable State 本身因为 Cassandra 的行大小限制而以单行存储（文档原话是 "persisted in a single row, similar to its layout in the in-memory cache"）。这意味着 Mutable State 不是"独立的服务端状态"——它只是 Event History 的一个物化视图，理论上随时可以从 history 重建。

---

## 决策二：History Shard 固定分片，分片数一选定终身

一个 cluster 管理上百万个 Workflow Execution，怎么扩展？分片。具体怎么分？[history-service.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md) 给的答案是：

> The total number of History Shards is fixed at cluster creation and cannot be changed later.

文档只陈述了这条规则，没有解释原因。顺着实现往下读，能看出一些门道：shard 归属由 [Ringpop](https://github.com/uber/ringpop-go) 协调——每个 History Service 实例通过 gossip 维护成员关系，用一致性哈希环决定"我持有哪些 shard id"。shard id 到存储记录的映射、到 in-memory 状态的映射都以 shard id 为键；shard 数固定，这个映射才稳定。扩容的正确姿势是**加 host、让环重新划分 shard 的 ownership**，而不是加 shard。

我的读法是：ownership 转移本身就不便宜——新 host 要重新加载 shard 上的 mutable state 缓存、任务队列的推进状态。如果 shard 数还能变，等于每次变更都要同时处理两层重新映射。Temporal 选择"宁可一次分配到位"。

**实际代价是什么？** 假设集群创建时设了 1024 个 shard，业务跑两年后 workflow execution 数量翻 5 倍——这时候你不能再加 shard。负载增长只能靠更多 host 分担这 1024 个 shard 的 ownership，单个 shard 管的 execution 数量则会一直涨。按文档定义，"owning" 一个 shard 意味着负责该 shard 里**每个 execution 的完整生命周期**——同步处理它的请求、异步推进它的定时器和任务分发。这个责任粒度定死了，后面的所有伸缩都只能在它之上做。

顺带澄清一个容易误读的地方。同一份文档里还有一句：

> Workflow Execution History is a linear sequence of History Events (unless the workflow has been `Reset` or subject to conflict resolution, in which case it has a branching topology).

History 默认线性，Reset 和 conflict resolution 时出现"branching topology"——这是版本管理语义（Reset 产生新分支、failover 冲突产生分叉），**与 shard 无关**。一条 history 不会因为太长就被拆到别的 shard；shard 按 execution 的 key 哈希分配，一个 execution 的 history 始终归一个 shard 管。

代码里 shard 的入口在 [`service/history/history_engine.go`](https://github.com/temporalio/temporal/blob/main/service/history/history_engine.go)：每个 shard 对应一个 `historyEngineImpl`，其 `Start()` 拉起该 shard 内部的多个 queue processor（transfer、timer 等每种内部队列各一个）和 replication processor。注释里还写明了一点：ShardController 会顺序调用本 host 所有 shard 的 start，所以 start 必须立即返回、组件全部懒加载。ownership 转移发生时，新 host 全量加载 shard 的状态。

这个决策的工程含义：**Temporal cluster 创建时必须把规模预算一次做对**。shard 数一旦定死，后续扩容只能加 host 分担 ownership；对增长快的业务，初始 shard 数要按未来的峰值规模估，而不是按当下。

---

## 决策三：CHASM 框架，把 Workflow 抽象成可水平复制的 ASM

Temporal 仓库里有一篇 1600 多词的架构文档专门讲 [CHASM](https://github.com/temporalio/temporal/blob/main/docs/architecture/chasm.md)，全称 **Coordinated Heterogeneous Application State Machines**。这篇文章读起来不像 Temporal 项目的一部分，倒像是一个独立的"分布式状态机框架"的 RFC。

CHASM 起点的判断相当坦率：

> Temporal Workflows are powerful, but they have real limits: too slow or heavyweight for some problems, unable to scale in every dimension (e.g. millions of signals, large payloads), and overly complex when a purpose-built solution would be simpler.

也就是承认：**Workflow 太重、太慢、太复杂**。它能承载海量业务逻辑，但不是所有东西都应该跑在 Workflow 上。

CHASM 的解法是把 Workflow 抽象成一种 **Application State Machine (ASM)**——一种**用 Temporal 的 sharding/routing/atomic storage/failure recovery，但避开 full workflow cost** 的轻量级状态机。

CHASM 把"做一个 ASM"的成本压到很低：

| 概念 | 含义 |
| --- | --- |
| **Library** | 把 components、tasks、service handlers 归组到一个命名空间下，比如内置的 `workflow`、`scheduler` |
| **Component type** | 一种注册的状态机类型，由 Fields（持久化数据）+ behavior（方法）组成 |
| **Node** | Execution 的状态载体——存储归 Node 管，行为归 Component 管，根节点及其后代构成 CHASM Tree |
| **Execution** | 一个 ASM 的运行时实例，由 `NamespaceID + BusinessID + RunID` 组成的 ExecutionKey 唯一定位 |
| **Transition** | 原子状态变更单元——一次 transition 作用于整个 Execution，所有写入要么全部提交要么全部回滚 |
| **Task** | 异步工作单元，分 Pure（事务内执行）和 Side Effect（事务提交后异步执行）两类 |

CHASM 不只是"Workflow 的简化版"。它的野心是把 Temporal 的核心能力——sharding、routing、atomic storage、failure recovery——**剥离成一个可水平复制的框架**，然后用这个框架去构建各种业务实体。当前仓库里 [chasm/lib/](https://github.com/temporalio/temporal/tree/main/chasm/lib) 已经有五个内置 Library：

- [`workflow`](https://github.com/temporalio/temporal/tree/main/chasm/lib/workflow)——传统 Workflow Execution，被改造成 CHASM 的 root component
- [`scheduler`](https://github.com/temporalio/temporal/tree/main/chasm/lib/scheduler)——Schedules 特性的新实现，整个 Scheduler 树就是 CHASM tree
- [`nexusoperation`](https://github.com/temporalio/temporal/tree/main/chasm/lib/nexusoperation)——Nexus Operation 的生命周期管理
- [`activity`](https://github.com/temporalio/temporal/tree/main/chasm/lib/activity)、[`callback`](https://github.com/temporalio/temporal/tree/main/chasm/lib/callback)——后加入的两个实体

这层变化的份量在于 Temporal 的定位从"Workflow orchestration"移到了**通用状态机平台**。新的业务实体不需要重新实现一套 sharding/timer 体系，直接在 CHASM 框架上注册一个新 ASM Library 就行。从三个 library 到五个，这个清单还在变长。

这种架构变化的工程信号：[schedules.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/schedules.md) 顶部就有：

> ⚠️ All documentation pertains to the CHASM-based Scheduler implementation, which is not yet generally available.

也就是说旧 Scheduler 实现还在，CHASM 化的新 Scheduler 尚未 GA——迁移在推进，但还没走完。

**CHASM 的核心创新**：用 `VersionedTransition` 作为全局逻辑时钟——每个 transition 有 `(FailoverVersion, TransitionCount)` 两个分量，前者跨 DC failover 递增，后者在 Execution 内随每次状态更新递增。CHASM 用它给出所有状态变更的全序，跨数据中心也一样成立——这是 Event Sourcing 系统里很难自然拥有的性质。

---

## 决策四：Speculative Workflow Task，让 Update 拒绝一行 history 都不写

[Temporal Workflow Update](https://github.com/temporalio/temporal/blob/main/docs/architecture/workflow-update.md) 是个有趣的新特性。它的存在意义文档开头就讲了：

> Historically, Temporal had two basic primitives, which allows users to interact with a Workflow: 1. Signal, which can be sent to a Workflow to trigger some behavior there. 2. Query, which can be used to return some information from a Workflow.

Signal 是 fire-and-forget，Query 是 read-only。但实际业务经常需要"既要触发更新，又要拿到结果"——这就是 Update 的需求场景。Update 可以被 Workflow 拒绝，**而且拒绝时不能在 history 里留任何痕迹**。

"拒绝不留痕"在 Event Sourcing 里是反直觉的——history 是 immutable 的，按说只能 append。Temporal 的解法是发明了一种**新的消息协议**：[message-protocol.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/message-protocol.md)——用 messages 而不是 events 来承载 Update 请求。

但这还不够。Update 要做到文档所说的 zero writes——不仅不写 event，连 transfer task 都不能创建，因为创建 transfer task 本身就要写一次 DB。所以 Workflow Update 需要一条**完全不落库的路径**来派发 Workflow Task。

这就是 [speculative-workflow-task.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/speculative-workflow-task.md) 的来历。Speculative Workflow Task 的定义：

> Similar to a CPU's *speculative execution* (which gives this Workflow Task its name) where a branch execution can be thrown away, a speculative Workflow Task can be discarded as if it never existed.

整个 speculative task **永远不写 DB**。它走的是一条不经过 Transfer Task Queue、不经过 Timer Task Queue 的特殊路径——直接通过 `AddWorkflowTask` RPC 把 task 塞进 Matching Service。超时用 [in-memory-queue.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/in-memory-queue.md)——一个只在内存里的 timer queue，不写数据库。

这个设计的代价是：要确保 speculative task 在中途挂掉时（worker crash、network error）能**安全地丢弃**——`StartedTime` 加到 workflow task token 里就是为了让 worker 在新 task 创建后无法用旧 token 完成；`ResetHistoryEventId` 字段让 SDK 在 server 决定 discard 时能 rollback history checkpoint。

**为什么要这么麻烦？** 因为 Update 的核心承诺是"拒绝不留痕"。workflow-update.md 里有一句很直白的描述：

> There is no 'Update Rejected' event: when an Update is rejected, it just disappears.

被拒绝的 Update 无处存储、无法去重，同一个请求甚至可能被重复投递给 worker；之后再去 poll 这个 Update 的结果，得到的也只是一次 NotFound。这是产品级的语义承诺——调用方期望"什么都没发生"，系统就必须真的做到"什么都没发生"，哪怕代价是给 task 派发专门修一条不落库的通路。

Speculative task 的应用不止 Update——workflow task 处理代码里留有一条 TODO 注记，说 Query 的处理未来也可能改用 speculative Workflow Task 实现。这是一个**通用工程模式**：当业务需要"先尝试、失败时不留痕"的语义时，Event Sourcing 系统的常规做法是引入 speculative execution——CPU 体系结构的概念被原样搬到了分布式系统。

---

## 决策五：Outbound Queue 按 `(TaskGroup, NamespaceID, Destination)` 三元组隔离 circuit breaker

[Nexus](https://github.com/temporalio/temporal/blob/main/docs/architecture/nexus.md) 是 Temporal 用于跨 namespace / 跨 cluster 边界的服务调用框架。它要解决的核心问题是：**Temporal server 自己作为 client 调外部服务**（不像普通 worker 那样——worker 调外部是 user 的代码）。具体场景：调用另一个 namespace 的 Nexus service / 调用外部 HTTP endpoint / 投递 workflow completion callback。

**Temporal server 自己作为 client** 这件事带来一个全新的故障模式——destination 可能慢、可能挂、可能反复 503。如果 Temporal 把这些 outbound 调用塞进普通的 transfer queue，每一个 retry 都会加载 workflow 的 mutable state（cache 或 DB 命中），占住 goroutine，然后阻塞在一个注定要超时的 HTTP 请求上。

[circuit-breaker.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/circuit-breaker.md) 开篇就点破这个失败模式：一个不健康的 destination 会把队列容量吃光，健康 destination 需要的配额被它抢走——对死掉的 destination 反复重试代价极高，因为它每次都要走完上面那整条路径。

最粗的解法是给整个 outbound queue 配一个全局 circuit breaker，但那样一个 destination 挂了，所有 outbound task 都被短路。Temporal 的解法是按 destination 隔离：用一个 [`CircuitBreakerPool[K]`](https://github.com/temporalio/temporal/blob/main/service/history/circuitbreakerpool/circuit_breaker_factory.go)，key 是 `(TaskGroup, NamespaceID, Destination)` 三元组。注意 Destination 不是 URL，而是 Nexus endpoint 的名字——同一个 endpoint 背后怎么换地址，熔断状态都跟着名字走。

为什么用这个三元组？文档里写：

> When a breaker is first requested for a key, the pool reads that (namespace, destination) pair's initial `OutboundQueueCircuitBreakerSettings` and subscribes to future changes, so operators can tune or disable the breaker per destination via dynamic config.

也就是说——**配置粒度可以到「单一来源 namespace 调单一 destination endpoint」**。运维想给某个 endpoint 关掉 circuit breaker、给另一个加严阈值，单独改它那条就行。

breaker 的 trip 策略用 gobreaker 默认：连续失败超过 5 次就 trip。trip 后状态走 Open → Half-open → Closed 的标准三态机。

这种 key 粒度设计背后的工程判断：**故障隔离的代价是配置面复杂度**，但收益是"一个不健康的 destination 不会拖垮整个 cluster"。Temporal 选择接受配置复杂度，因为 Nexus 服务调用场景下，一个挂掉的 destination 可能牵连大量上游 workflow，让它拖垮整个 outbound queue，远比配置面复杂更糟。

具体的处理栈：[Nexus 文档](https://github.com/temporalio/temporal/blob/main/docs/architecture/nexus.md#outbound-task-queue) 里，Outbound Queue 的 reader 先从队列读出 task，再按**源 namespace + 目的地**分组送进各自的 scheduler，每个组内部依次经过 `Buffer → Concurrency Limiter → Rate Limiter → Circuit Breaker`，最后落到 Executor。每一层都是独立的限流和隔离，**只有全部环节通过才能让 task 被真正执行**。

Multi-Cursor 是另一层隔离——一个 shard 上的 outbound queue 默认起 4 个 reader（各自有自己的 cursor，可用动态配置 `history.outboundQueueMaxReaderCount` 调整），slow destination 的 task 被移交给较慢的 reader 消费，让健康 destination 不被拖累。

把这套 outbound queue 的设计和 Temporal 内部状态机的风格放在一起看很有意思：内部信任内存、信任 history，重放是合法操作；对外则把信任降到零——每个 outbound call 被多层 limit 包着，每个 destination 有自己的 breaker，每个 shard 有自己的 cursor。区别只有一个：外部世界不能被信任。

---

## 一个 outbound 调用怎么穿过这套系统

把上面几张抽象叠成一次真实调用看：某个 workflow 要调另一个 namespace 的 Nexus service，而那个 destination 恰好开始 503。

1. History Service 需要推进这次 outbound 调用，把任务写进当前 shard 的 Outbound Queue。
2. Multi-Cursor 的 reader（默认 4 个，可调 `history.outboundQueueMaxReaderCount`）取出任务，按 `(TaskGroup, NamespaceID, Destination)` 分到对应分组。
3. 任务在分组里依次过 `Buffer → Concurrency Limiter → Rate Limiter → Circuit Breaker`。destination 已经连续失败超过 5 次，breaker trip 进入 Open，任务在到达 Executor 之前就被挡下，不会真的发起一次注定超时的 HTTP 请求。
4. Open 期间，后续发往这个 destination 的任务都会在 Executor 前被拦截；被拖慢的 reader 单独消费这批任务，健康 destination 的任务照常走其他组、其他 reader。

直观的效果是：失败被挡在边界上，而不是滚进每个 retry 去重走"追加 event + 更新 mutable state"的完整路径。这就是决策五那份工程判断落到真实路径上的样子。

---

## 这 5 个决策之外，还有什么

读完整套架构文档还能看到几个值得讲的工程决策：

**Workflow Task 三态**——[speculative-workflow-task.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/speculative-workflow-task.md) 把 Workflow Task 拆成 Normal / Transient / Speculative 三种。Normal 失败时写 failure event 并加 attempt count；重试改用 Transient，它的 scheduled/started events 不写 history，直到某次真正完成才一并补写；Speculative 是上面决策四讲的"完全不写 DB"的 task。有个耐人寻味的细节：数据结构里其实有 `Type` 字段，但 `WORKFLOW_TASK_TYPE_TRANSIENT` 值目前没被使用——代码实际用 `ms.IsTransientWorkflowTask()` 检查 attempt count 是否大于 1 来判断，文档里以 TODO 的形式承认了这一点。

**Message Protocol**——上面决策四提到的 message protocol 用 `protocol_instance_id`（当前 == update_id，未来可能扩展到 signal/query）+ `body: Any` + `sequencing_id`（event_id 或 command_index）。`body: Any` 用 protobuf Any 而不是 oneof，是为了让 server 不需要知道所有消息类型——可插拔设计。

**Transfer Queue + Timer Queue 拆分**——把"立即推进"（Transfer）和"等时长"（Timer）拆成两个内部队列，分别用 immediate queue 和 scheduled queue 两种变体处理。文档里特意提醒："It's important to understand that elsewhere in Temporal documentation, 'task queue' refers to the Task Queues of the Matching Service, which are a concept exposed to Temporal users; the task queues we are discussing here are an internal implementation detail of the History Service."——外部可见的 Task Queue 和内部 task queue 是两套东西，名字相同但语义不同。

---

## 写给想用 Temporal 做长跑业务的人

读完这 5 个决策，几个能立刻用得上的判断：

**判断 1：Workflow Task Failure 是设计内的，不是 bug**。Worker 报 `RespondWorkflowTaskFailed` 时，server 会写一条 failure event 并把 mutable state 里的 attempt count 加一；下一次重试改用 Transient task，它的 scheduled/started events 不进 history——反复失败也不会堆出一串失败事件，直到某次真正完成才补写。这套机制的目的就是"worker 失败 ≠ workflow 失败"，读 history 时看到的事件序列比实际的重试次数干净得多。

**判断 2：Update 拒绝不留痕是产品级承诺**。集成 SDK 或设计上层系统时要记住：没有 "Update Rejected" 事件，被拒绝的 Update 无处存储、无法去重，可能被重复投递给 worker；事后 poll 它只会得到 NotFound。服务端会通过 `UpdateStore` 恢复 in-flight 的 Update（文档称之为 Update Resurrection），但"拒绝"这条路从设计上就不留下任何可查询的痕迹。如果你的业务依赖"拒绝原因可追溯"，当前语义下得自己在客户端记录。

**判断 3：Cluster shard 数的初始估算很关键**。fixed shard 决策意味着你创建集群时要按未来的峰值规模做预算——shard 数之后不能增减，扩容只能加 host 分担 ownership。这笔账没有公开的通用公式，但方向是明确的：shard 数定小了，单 shard 的责任范围随业务增长越滚越大，最后只能重建集群。

**判断 4：CHASM 框架会越来越重要**。chasm/lib 下已经有 workflow、scheduler、nexusoperation、activity、callback 五个 library，清单还在变长。新业务实体如果想"复用 Temporal 的 sharding + atomic storage + failure recovery 但不要 workflow 的全成本"，CHASM 是入口。

**判断 5：Nexus endpoint registry 不是多 cluster safe**。[nexus.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/nexus.md) 顶部明确警告"Nexus shouldn't be used in multi cluster setups because replication for the registry is not implemented"。这是个还没解决的架构债，未来会修——但今天不要在多 cluster 部署里依赖 Nexus endpoint registry。

---

## 这个项目真正讲的是什么

把 5 个决策摆在一起看，Temporal 不只是"Workflow orchestration"——它是**对"Event Sourcing 工业落地"这个分布式系统老问题的工程回答**：

- Event Sourcing 太慢？→ Mutable State 缓存做物化视图。
- shard 责任粒度怎么定？→ 创建时一次定死，扩容靠加 host 分担 ownership。
- Workflow 太重？→ CHASM 把 Workflow 抽象成 ASM tree，让其他实体复用基础设施。
- Event 不可变所以 Update 不能拒绝？→ Speculative Workflow Task + Message Protocol。
- 外部 destination 可能挂？→ Outbound Queue + Circuit Breaker Pool + 多层 limit。

每一层都是对前一层缺陷的修正——而每一层修复又引入了新的工程复杂度（Mutable State 一致性、fixed shard 不可扩容、CHASM 框架心智负担、Speculative task 路径特殊、Circuit breaker 配置面）。

Temporal 的 23k stars 不是一个"Workflow DSL 设计得好"就能解释的——它的价值在**这些工程细节**：多年生产环境的反馈沉淀、Uber Cadence fork 出来的工业基础、对分布式系统每个老问题都给出具体答案。

读它的代码不是学 Go，是学**Event Sourcing 在分布式系统里要怎么落地**。

> 出处：
> - 仓库：[github.com/temporalio/temporal](https://github.com/temporalio/temporal)
> - 架构文档：[docs/architecture/README.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/README.md)
> - 关键子文档：[history-service.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md) · [chasm.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/chasm.md) · [workflow-update.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/workflow-update.md) · [speculative-workflow-task.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/speculative-workflow-task.md) · [nexus.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/nexus.md) · [circuit-breaker.md](https://github.com/temporalio/temporal/blob/main/docs/architecture/circuit-breaker.md)
>
> 作者：钳岳 · 2026-09-05