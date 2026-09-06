---
title: "Linear Sync Engine 反向工程：2562 颗星背后的协作引擎如何实现"
date: "2026-09-06T15:50:00+08:00"
draft: false
slug: reverse-linear-sync-engine-deep-dive
github_repo: wzhudev/reverse-linear-sync-engine
source_key: gh:wzhudev/reverse-linear-sync-engine
description: "wzhudev 用 96KB 的 uglified（被代码混淆器压缩过的）注释版代码 + 5 章 7 节还原了 Linear 客户端 Sync Engine，被 Linear CTO Tuomas Artman 称为「比内部文档还好」。本文对照仓库 5 章 + SUMMARY + imgs 截图，把 LSE 拆到第一性原理：为什么 Linear 不选 CRDT（Conflict-Free Replicated Data Type 无冲突复制数据类型）、七种 property type 如何组成模型层、本地「只更内存不写库」的 SSOT（Single Source of Truth 单一事实源）哲学，以及它和经典 OT（Operational Transformation 操作变换算法）的差异。"
categories: ["技术笔记"]
tags: ["Linear Sync Engine", "反向工程", "MobX", "IndexedDB", "WebSocket", "OT", "CRDT", "lastSyncId", "Object Pool", "Delta Packet", "Transaction Queue", "Schema Hash", "MobX observable", "Operational Transformation", "Local-First", "Wenzhao Hu", "Tuomas Artman"]
author: 钳岳
---

# Linear Sync Engine 反向工程：2562 颗星背后的协作引擎如何实现

**核心判断**：Linear Sync Engine（LSE）难的地方不是「让多人同时改一个 Issue」。它把「ORM（Object-Relational Mapping，对象关系映射）写法的开发体验」「部分索引 + SyncGroup 权限」「中心化总序 + last-writer-wins 冲突解决」这三件原本冲突的事，缝合成一个可以让前端开发者写 `issue.title = "New Title"; issue.save();` 就能拿到离线、撤销、权限、广播四件套。它选 OT-like 而不是 CRDT，不是因为 OT 更简单——Linear 的产品形态（issue tracker，强权限边界，中心化 workspace）天然拒绝「去中心化偏序」。

## 为什么这个仓库值得拆

`wzhudev/reverse-linear-sync-engine` 在 GitHub 上的姿态只有一句话：「A reverse engineering of Linear's sync engine. Endorsed by Linear CTO」。2562 stars / 138 forks（GitHub API 拉取于 2026-09-06 16:05 GMT+8），无 LICENSE（仅文章正文 CC-BY 4.0，README 末尾声明），2025-06-02 最后一次 push。`code/` 目录只有 `html.js` 与 `Root.js` 两个文件——这不是个代码项目，是个**对生产代码的考古报告**：作者 Wenzhao Hu 把 Linear 客户端的 uglified（被代码混淆器压缩过的）bundle（前端打包产物）加了几千行注释还原出来，并对照 Tuomas Artman 三次公开演讲、一次 Local First Conf talk 与一次播客，把每一处混淆命名映射回原始语义。

更值得注意的是它获得了 CTO 亲自站台：

> "This is a pretty awesome (and correct) write-up of our sync engine."  
> "...probably the best documentation that exists - internally or externally."  
> -- Tuomas Artman (Co-founder and CTO of Linear)

HN 评论：「documentation that is correct and more complete than what Linear publishes internally」。CTO 亲自盖章「比内部文档还好」的反向工程——这种评价在商业产品里几乎不可能出现。把它和仓库里 96 KB 的 README + 13 KB 的 SUMMARY + 一张完整 Excalidraw 架构图摆在一起，差别一眼就看出来：

- **普通的源码解读**：按行讲一遍 API
- **这份反向工程**：把生产代码当化石，按 5 章（模型 / 引导加载 / 事务 / 增量包 / 其他）+ 结论 + 附录，逐层剥出 LSE 的架构哲学

下面把 LSE 拆到能自己解释每一行注释为什么这么写的程度。

## 总览：LSE 的五个关键概念

LSE 的所有机制都围绕五个概念展开，理解这五个概念就能读懂后面所有的代码：

**Model（模型）**——LSE 把 `Issue`、`Team`、`Organization`、`Comment` 当作有 property 和 reference 的类。每个模型带 metadata（元数据，决定它如何被加载、被引用、被索引）。模型可以从本地 IndexedDB 加载，也可以从服务器拉取；进入内存后统一进入一个叫 Object Pool 的大 map，靠 UUID 检索。模型支持**懒 hydrate（hydrate 意为「填充」/「注水」，指把数据库里的扁平数据变成有引用、有监听能力的对象图）**——只在访问某个字段时才去加载那个字段。

**Transaction（事务）**——对模型的所有操作（增删改归档）都被打包成事务，发送到服务器，**只在服务端执行**，然后以 delta packet（增量包）的形式广播给所有客户端。事务是**可逆的**：失败时客户端能回滚；离线时事务先缓存进 IndexedDB，连上自动重发。每个事务带一个**单调递增的 sync id**，保证全库操作的总序。

**Delta Packet（增量包）**——服务器把事务产生的最终状态打包成 sync action（同步动作）的序列，广播给所有连接中的客户端——包括发起事务的那个客户端。每个 sync action 也带 sync id。本地数据库**只在收到 delta packet 确认后才写入**——这是 LSE 和「乐观写本地」最关键的差异。

**Object Pool（对象池）**——一个由 `modelLookup` 实现的 map，把模型 UUID 映射到内存对象实例。提供 O(1) 的检索能力，且保证同一 UUID 的对象只有一份。

**Hydration（注水）**——把 IndexedDB 里扁平的 JSON 行变回有 MobX observable（响应式监听）能力、有引用关系、有 computed（计算属性）的对象图的过程。LSE 支持**懒 hydrate**：不一次性把所有属性读进内存。

五个概念之间的关系可以用一句话总结：**Model 是形状，Transaction 是动词，Delta Packet 是回声，Object Pool 是舞台，Hydration 是开机**。

## 第一性原理：为什么 Linear 不选 CRDT

仓库作者在 README 开篇就把这个问题抛出来了：OT 和 CRDT 是两大主流协作引擎技术，但 Linear 都不完全用，而是走出了第三条路——OT-like 的中心化总序。理解这条选择要先理解 OT 和 CRDT 的真实代价。

**OT 的代价**：OT 是一套 server-centric（服务端主导）的算法，要求服务端保留所有未确认的操作历史，用于在并发冲突时做 transformation（变换）。它的优势是能精确保留用户意图，冲突处理结果可解释。但代价是**服务端状态爆炸**——Linear 的服务端不仅要存文档数据，还要存「每一笔未完成的操作」，这对 issue tracker 这种「每条记录都是结构化字段而不是自由文本」的产品形态来说太重。Wenzhao 在 README 里直接写：「OT is widely adopted but notorious for its complexity. This complexity stems from the need to account for diverse data models and operation sets across different applications」。

**CRDT 的代价**：CRDT 看起来更友好——它把数据结构内置成可合并的（如文本、列表、map、计数器），开发者不用关心 transformation。但有两个工程问题：

1. **Metadata overhead（元数据开销）**：CRDT 的每个字符、每个节点都带唯一 ID 和版本向量，数据量远大于原始数据。Linear 的 issue 列表要展示几千条记录，每条都带完整 CRDT 历史是不可接受的。
2. **权限控制困难**：CRDT 是为去中心化系统设计的，但 Linear 的 workspace / team / role 权限边界是中心化的。CRDT 难以表达「你能看到这些 issue 但不能看到那些 comment」这种**部分同步**场景。

作者本人的偏好也是 CRDT——「I am personally an advocate of CRDTs」——但他承认：**Linear 的产品形态让 CRDT 的优势变成了劣势**。

LSE 的解法是「**OT-like 但只对 Update 冲突做 last-writer-wins（LWW，后写入者覆盖先写入者）**」：

- **中心化总序**：服务器分配全局单调递增的 sync id，所有事务按这个总序执行。这部分像 OT。
- **不保留操作历史**：服务器只广播最终模型状态（delta packet），不广播 transformation 步骤。这部分像 CRDT 的「只关心合并结果」。
- **冲突解决简化**：对 `UpdateTransaction` 用 LWW——后到的 sync action 直接覆盖在客户端等待的事务的 `original` 值，让本地事务被 rebase（基线重定）到这个新值之上。删除/归档的 LWW 通过 sync id 比较直接判定（后到的 sync id 大 → 赢）。
- **服务端副作用**：服务器在执行事务时可以生成 history（`IssueHistory`）、发送通知、写 activity log——这些副作用通过 delta packet 的额外 sync action 广播给所有客户端。

LSE 把这种 hybrid（混合）形态叫做「linearized OT with delta-based broadcast」。它不是教科书里的 OT，也不是教科书里的 CRDT，是为 issue tracker 量身剪裁的产物。架构选型从来不是「选最好」，而是「选最不坏」。

## 模型层：七种 property type 如何拼出整个领域

LSE 的模型层是整个引擎的语法基础。所有 property 通过 TypeScript decorator（TypeScript 装饰器，即 `@Decorator` 这种语法糖，在编译时会被转成函数调用）注册到 `ModelRegistry`，并带 metadata。

七种 property type 各司其职：

1. **`property`** —— 模型「拥有」的字段，写入 IndexedDB。例：`Issue.title`、`Issue.priority`。
2. **`ephemeralProperty`** —— 类似 property 但不入库，只在内存中存在。例：`User.lastUserInteraction`。
3. **`reference`** —— 指向另一个模型，**只存 ID**（不是对象）。可被 lazy-loaded（懒加载，第一次访问时才去查对象）。例：`Team.subscription`。
4. **`referenceModel`** —— 当 `reference` 被注册时，自动生成的镜像字段，提供 getter/setter 通过 ID 拿到对象。**不入库**。例：`Issue.assignee`（背后实际读 `Issue.assigneeId`）。
5. **`referenceCollection`** —— 类似 reference，但存的是 ID 数组。例：`Team.templates`。
6. **`backReference`** —— reference 的反向。**关键差异**：backReference 被引用方「拥有」——被引用方（B）删除时，反向引用（A）也一起删除。例：`Issue.favorite`。
7. **`referenceArray`** —— 多对多关系。例：`Project.members`。

七种类型的关键是**「存储」和「访问」彻底分开**。`assigneeId` 是持久化的字段（标量），`assignee` 是基于 `assigneeId` 加 getter/setter 的视图（对象）。这种分离带来三个好处：

- **序列化简单**：传输只需要 ID，不需要序列化对象引用（避免循环引用问题）。
- **Lazy 加载天然支持**：访问 `issue.assignee` 时如果内存里没有 User 对象，自动通过 ID 去 Object Pool 找或发起网络请求。
- **删除传播可控**：只有 `backReference` 会在被引用方删除时被一起删，`reference` 不会——这个语义差异在分布式同步里至关重要。

`ModelRegistry` 维护几个关键的 lookup（查找表）：

- `modelLookup` — 模型名到构造函数的映射
- `modelPropertyLookup` — 模型属性 metadata
- `modelReferencedPropertyLookup` — 模型引用 metadata
- `__schemaHash` — 所有模型 + 所有属性 metadata 的 hash，**用于检测 IndexedDB 是否需要迁移**

`__schemaHash` 这个设计很关键——它意味着**模型 schema（模式，即数据形状的定义）变了，自动触发迁移**，不需要写迁移代码。这和传统 ORM 里的 migration（数据库迁移）工具（Django ORM、Sequelize）一样，但触发点是自动的。

Observable（响应式监听）的实现通过 `Object.defineProperty` 重写 getter/setter——这是 MobX 的标准玩法。`M1` 函数（被混淆的 observabilityHelper 原始名）做三件事：

1. 在 `__mobx` 对象上创建一个 MobX box（响应式容器）
2. 重写 getter/setter 走 box 的 get/set
3. setter 触发 `propertyChanged` → `markPropertyChanged`，**记录字段名 + 旧值 + 新值**

第三步是「事务生成」的基础——所有这些「字段被改了」的信号在 `model.save()` 时被收集起来，组装成 `UpdateTransaction`。

## 引导加载：Full Bootstrap 的七步曲

引导加载（Bootstrap）的目标是把 LSE 从「空进程」变成「可用的协作客户端」。README 里给出了一张完整的引导加载流程图，但读图容易忽略细节。下面用伪代码把七步拆开：

```ts
// 第 1 步：StoreManager 为每个模型创建 ObjectStore
//   loadStrategy = partial → PartialStore
//   其他策略 → FullStore
//   每个 store 计算自己模型的 hash 作为表名
//   partial 策略额外建一个 <hash>_partial 索引库
//
// 第 2 步：Database 连接 IndexedDB
//   linear_databases 库存「workspace 元信息」
//   linear_<hash> 库存具体 workspace 的数据
//   如果库不存在 → 创建；如果 schemaHash 不匹配 → 迁移
//
// 第 3 步：判断 bootstrap 类型
//   stores 全空 / lastSyncId 未定义 / 模型过期 → full bootstrap
//   否则 → local bootstrap（用 IndexedDB 已有数据 + 拉增量）
//   部分场景 → partial bootstrap
//
// 第 4 步：执行对应 bootstrap
//   full → 调 GraphQLClient.restModelsJsonStreamGen 拉数据
//   请求 URL: /sync/bootstrap?type=full&onlyModels=...
//
// 第 5 步：写回 IndexedDB
//   把流式 JSON 行写入对应 ObjectStore
//   更新 _meta 表的元数据（lastSyncId, subscribedSyncGroups, ...）
//
// 第 6 步：内存 hydrate + 激活 observable
//   loadStrategy = instant 的模型立刻 hydrate 进 Object Pool
//   调用 updateFromData 填充字段
//   调 makeObservable 激活响应式
//
// 第 7 步：建立 WebSocket
//   监听 SyncMessage channel
//   收到 handshake callback 后对比 lastSyncId
//   如果缺失 → 请求补发 delta packet
```

第 4 步的全量引导加载请求和响应值得单独看一眼。请求 URL 是：

```
https://client-api.linear.app/sync/bootstrap?type=full&onlyModels=WorkflowState,IssueDraft,Initiative,ProjectMilestone,...,Webhook,WorkflowCronJobDefinition
```

`onlyModels` 是 `loadStrategy` 为 `instant` 或 `lazy` 的模型名，逗号分隔。响应是 NDJSON（Newline-Delimited JSON，每行一个 JSON 对象的流式格式），每行一个模型实例，**最后一行是 `_metadata_`**，包含服务端返回的 `lastSyncId`、`subscribedSyncGroups`、`returnedModelsCount` 等关键字段。

第 6 步里的 hydrate 关键点：**构造对象时不传数据**，先 `new Issue()`，再调 `updateFromData()` 填字段。这是为 lazy hydrate 留口子——后续访问字段时可以单独 hydrate。

第 7 步的 handshake callback 是「客户端是不是落后于服务器」的判定点：

```json
{
  "userSyncGroups": { "all": [...], "optimized": [...] },
  "lastSyncId": 3529152751,
  "lastSequentialSyncId": 3529152751,
  "databaseVersion": 1179
}
```

**注意：lastSyncId 是全库的，不是 workspace 的**。作者在 README 里专门强调：「even if a single transaction happens in your workspace, the `lastSyncId` often increments significantly, indicating that it is tracking changes across all workspaces in the system」。这意味着 sync id 的水位很高，冲突窗口反而更小。

## 懒加载：partial index + SyncGroup 两把钥匙

LSE 的懒加载不是简单的「按需网络请求」——它有两把钥匙配合：**partial index** 和 **SyncGroup**。

**Partial Index** 解决的问题是：「拿到一个外键 ID 但不知道另一端的具体数据时，用什么字段去查询？」例：拿到 `User.id` 想查该 User 名下所有 `Issue`，查询参数是什么？

LSE 的解法是在 `Issue` 模型上声明 `assigneeId` 是 indexed reference，对应在 `User` 上生成 `assignedIssues` 这个 `LazyReferenceCollection`，构造时指定：

```ts
this.assignedIssues = new LazyReferenceCollection(
  Issue, this, "assigneeId",
  undefined,
  { canSkipNetworkHydration: () => this.canSkipNetworkHydration(Issue) }
);
```

`PartialIndexHelper` 进一步把这种关系做成「嵌套三层」的 partial index——比如 `Comment` 可以通过 `Issue.cycleId-<id>` 反查，即「属于该 cycle 的所有 issue 的所有 comment」。这种笛卡尔积式索引（partial index × dependencies）让懒加载可以批量发出请求。

实际 hydrate `LazyReferenceCollection` 的逻辑分三步：

1. 调 `getCoveringPartialIndexValues` 拿到所有候选查询参数。
2. 调 `SyncedStore.hydrateModels` → `SyncClient.hydrateModelsByIndexedKey` → `Database.getModelDataByIndexedKey`。
3. 先查本地 IndexedDB。如果 `coveringPartialIndexValues` 缺失，或本地 partial index store 里没记录，**或** `canSkipNetworkHydration` 返回 false——才发网络请求。

**SyncGroup** 是另一把钥匙。它解决的是「权限边界」：所有 workspace 共享同一个 `lastSyncId` 计数器，但某个客户端只能看到自己有权限的 issue / comment。`subscribedSyncGroups` 数组存的就是「你的 user ID + 你所属的 team ID + 预定义角色 ID」。当一个 `Team` 有很多 `Issue` 时，LSE 不会用 `assigneeId` 拉，而是用 `customNetworkHydration` 定义查询参数为 `syncGroup: this.id`：

```ts
this.issues = new LazyReferenceCollection(Issue, this, "teamId", undefined, {
  customNetworkHydration: () => [
    { modelClass: Issue, syncGroup: this.id },
    { modelClass: Attachment, syncGroup: this.id },
  ],
});
```

请求 URL 会变成：

```
/sync/bootstrap?type=partial&noSyncPackets=true&useCFCaching=true&noCache=true&firstSyncId=3577987809&syncGroups=aa788b7b-9b76-4caa-a439-36ca3b3d6820&onlyModels=Issue,Attachment
```

`SyncGroup` 是 LSE 能在 issue tracker 这种「强权限边界」场景下保持「每个客户端只加载自己有权看到的数据」的关键——这是 CRDT 几乎做不到的事。

## 事务队列：四个数组 + 一个 updateLock

事务从生成到执行经过四个数组：

1. **`createdTransactions`** —— 刚被 `model.save()` 创建。
2. **`queuedTransactions`** —— 已从 `createdTransactions` 提交（commit）过来，等执行；**同时写入 `__transactions` 表做缓存**（断网/崩溃可恢复）。
3. **`executingTransactions`** —— 已发到服务器，等响应。
4. **`persistedTransactionsEnqueue`** —— bootstrap 时从 IndexedDB 恢复出来的事务，远程更新确认后被移到 `queuedTransactions`。

额外的 `completedButUnsyncedTransactions` 队列记录「事务已经被服务端确认（拿到 lastSyncId），但还没收到对应 delta packet」的事务——这是 delta rebasing（增量重定基线）的关键。

四个数组的流转有几个关键判断：

- **批量化**：同一个 event loop（事件循环，JavaScript 单线程模型中处理异步回调的机制）里创建的事务共享同一个 `batchIndex`（批序号），被合并到一次 GraphQL mutation 里发出。
- **批量上限**：`queuedTransactions` 太多时不移到 `executingTransactions`，避免服务端压力。
- **大小上限**：累积的 GraphQL mutation 大小超过阈值就停发，避免单次请求过大。
- **执行序列化**：所有 delta packet 处理在 `updateLock.runExclusive` 回调里，确保**前一个 delta 处理完才处理下一个**，避免乱序。

**LSE 在这一步做了一件和大多数客户端数据库相反的事：服务端响应后，本地 IndexedDB 仍然不写**。原文：

> "LSE has **not** modified model tables (e.g., the `Issue` table) in IndexedDB. This is because, in Linear, the local database is a subset of the server database (the SSOT), and it cannot contain changes that have not been approved by the server."

这意味着：**即使服务端返回 lastSyncId，本地数据库依然要等对应的 delta packet 到达后才写入**。换句话说，服务端的 mutation response 是「服务器承认了你的请求」，但「最终落库」要等 delta packet 携带的 sync action。这种「双层确认」让客户端永远不可能和服务端数据分叉——这是 LSE 一致性保证的基石。

## Delta Packet：八种 sync action 与两轮循环

服务器处理完 mutation 后，**广播** delta packet 给所有客户端（包括发起者）。每个 delta packet 含一组 sync action，每个 sync action 带一个 sync id。sync action 有 8 种 type：

| Type | 含义 |
| --- | --- |
| `I` | Insertion（插入） |
| `U` | Update（更新） |
| `A` | Archiving（归档） |
| `D` | Deletion（删除） |
| `C` | Covering（覆盖索引） |
| `G` | 改 sync group（加） |
| `S` | 改 sync group（删？区别于 G 不太清楚） |
| `V` | Unarchiving（取消归档） |

收到 delta packet 后 `SyncClient.applyDelta` 做 7 件事：

1. 判定用户加入/离开 sync group，加入则触发部分 bootstrap 拉数据。
2. 加载特定 action 的依赖（用 `DependentsLoader.supportedPacket` 筛选）。
3. 把新 sync group 的数据写进本地数据库。
4. **第一轮循环**：遍历 sync actions，让 TransactionQueue.modelUpserted 取消那些「UUID 已经出现在 delta 里」的 CreationTransaction。
5. **第二轮循环**：再遍历一次，更新内存模型。对 I/V/U/C 类型执行 rebase——把所有 UpdateTransaction 的 `original` 值更新到 delta 携带的最新值，让本地变更被「基线重定」到新值之上。
6. 更新 lastSyncId，更新 firstSyncId（sync group 变化时）。
7. 调 `syncWaitQueue.progressQueue(this.lastSyncId)`，把所有等这个 lastSyncId 的事务标记完成。

两轮循环的分工：第一轮做「取消无效 + 准备模型」，第二轮做「执行 + rebase」。一个具体的 rebase 例子：

> 你的同事把 assignee 改成 Alice，你同时把它改成 Bob。服务端按时间序先收到 Alice 的更新，存的是 Bob（因为你后到）。在你客户端：你创建了把 assignee 改成 Bob 的 UpdateTransaction；事务发出后、收到响应前，收到了 Alice 的 delta packet。这时 LSE 触发 rebase——把 UpdateTransaction 的 `original` 从「你创建时的 assignee 值」更新成 Alice，然后内存模型重置回 Bob。

**这一步很像经典 OT 的 transformation——但服务端不参与 transform**。客户端自己做 rebase，服务端只发最终状态。这是 LSE 与经典 OT 的第三大差异。

## 三组对比：LSE 和经典 OT、CRDT、通用本地优先数据库的本质差异

把 LSE 和常见的对比对象放一起，三组差异最关键：

### LSE vs 经典 OT

| 维度 | 经典 OT | LSE |
| --- | --- | --- |
| 操作存储 | 服务端保留所有未确认操作历史 | 不保留，只广播最终状态 |
| 冲突解决 | 服务端 transformation | 客户端 rebase（LWW） |
| 服务端角色 | transformation + 权限校验 + 执行 | 同上 + 副作用（history / activity） |
| 广播范围 | 仅给发起者 ack | 广播所有相关客户端全量属性 |

LSE 是「OT 思想 + CRDT 风格的最终广播」。代价是损失了 OT 的「保留用户意图」优势——但 issue tracker 场景下这种损失不重要。

### LSE vs CRDT

| 维度 | CRDT | LSE |
| --- | --- | --- |
| 数据顺序 | 偏序（不需要中心） | 总序（sync id 全局递增） |
| Metadata 开销 | 每个节点带 ID + 版本向量 | 只有 sync id |
| 权限边界 | 难表达 | SyncGroup 天然支持 |
| 离线合并 | 数学上保证 | 依赖 LWW，部分场景不保证 |

LSE 用「总序」换「偏序」的代价是必须依赖服务端——但换来的是「权限边界可以精确表达」「数据结构不会被 metadata 膨胀」。

### LSE vs 其他本地优先数据库（ElectricSQL、ZeroSync 等）

仓库作者在 README 里专门提了这两个项目。区别在于 LSE 是**应用层自己实现**的 OT-like 引擎，不是通用数据库层。它为 Linear 的「issue tracker 形态」做了 80 个模型的 metadata 精雕细琢；通用方案则要面对「所有应用形态」的长尾问题。

## 反向工程的工程哲学：CTO 为何站台

把仓库的价值和「普通源码解读」做对比，最能看出 Wenzhao 做对了什么：

1. **照搬 uglified bundle 加注释**——但用三遍演讲 + 一次播客 + 一次 Local First Conf talk 做交叉验证，对每一个混淆命名都给出「可能的原始名」。
2. **画出 17 张架构图 + 1 张 Excalidraw 全景图**——把代码逻辑变成视觉流程，让读者能在 5 分钟内建立 mental model（心智模型）。
3. **5 章 + 结论 + 附录**的章节结构**——「先讲 what 再讲 how」**：每章先给流程图，再展开代码细节。SUMMARY.md 提供 10 分钟快读版。
4. **保留「不确定」**——明确标注「I may inevitably fall victim to the curse of knowledge」「I'm not affiliated with Linear」，邀请读者提 issue 修正。这种**学术诚实**让文档的可信度大增。
5. **写给「想造一个」的人**——附录「Actions and Computed Values」专门讲 MobX 的 Action / Computed decorator 在 LSE 里怎么用，瞄准的不是「看懂 Linear」，而是「拿这个仓库当模板造一个新引擎」。

CTO 站台的真实原因不是「文档写得漂亮」，而是**这份反向工程的精度已经达到了内部文档级别**——这对 Linear 来说是一次零成本的「外部开发者教育」。Wenzhao 用 2562 颗星给 Linear 做了最好的招聘广告和开源布道。

## 可借鉴之处：哪些设计值得抄

如果想造一个类似的协作引擎，下面五个设计是值得借鉴的：

1. **Schema hash 自动迁移**——`__schemaHash` 把「模型变了 = 触发迁移」这个流程自动化，省掉所有手动写 migration 的成本。
2. **五种 loadStrategy**（instant / lazy / partial / explicitlyRequested / local）——把「加载时机」变成模型层的第一公民元数据，应用层不用关心。
3. **「本地只更新内存」的双层确认**——服务端响应 ≠ 数据落库，落库要等 delta packet。这是一致性保证，不是 optimistic write（乐观写入）。
4. **SyncGroup 作为权限边界**——用 ID 数组而不是 ACL（Access Control List，访问控制列表）描述权限，让增量同步可以精确过滤。
5. **事务级 undo/redo**——所有操作都是事务，每个事务都有 `undoTransaction` 方法返回 redo transaction。撤销/重做直接走事务队列，自动获得冲突解决、离线缓存、广播能力。

## 局限与未覆盖之处

Wenzhao 在结论里诚实地列了「本文未涉及的议题」：

- **其他事务类型**：`CreationTransaction`、`DeletionTransaction`、`ArchivalTransaction` 的具体实现，特别是 `onDelete` / `onArchive` metadata 如何影响事务生成。
- **其他 bootstrap 类型**：partial bootstrap 和 local bootstrap 的差异和触发条件。
- **Decorative 的内部演进**：Linear 团队在 README 写作过程中仍在改 `_mobx` 容器、subscribedSyncGroups → userSyncGroups 等字段命名，作者标注了但未重写。

这些「未覆盖」恰好是仓库的下一步方向——读完 README + SUMMARY 之后直接看 `code/` 注释代码，**对作者没讲到的事用 issue 提问**，是最有效的深度路径。

## 来源与延伸阅读

**本文主要事实来源**：

- 仓库 README.md（96 KB，5 章 + 结论 + 附录）
- 仓库 SUMMARY.md（13 KB，10 分钟快读版）
- `code/html.js` + `code/Root.js`（加注释的 uglified Linear 客户端代码）
- `imgs/` 目录 17 张架构截图
- `reverse-lse.excalidraw` 全景架构图
- GitHub API metadata（2562 stars / 138 forks，2026-09-06 16:05 GMT+8 拉取）

**延伸阅读**：

- Tuomas Artman 的 [两次公开演讲](https://www.youtube.com/watch?v=WxK11RsLqp4&t=2175s) 和 [Local First Conf 演讲](https://www.youtube.com/watch?v=VLgmjzERT08)——LSE 设计的第一手解释。
- [Scaling the Linear Sync Engine](https://linear.app/blog/scaling-the-linear-sync-engine)——Linear 工程博客的官方资料。
- [devtools.fm Episode 61](https://www.devtools.fm/episode/61)——对 Tuomas 的访谈。
- Wenzhao Hu 的 [OT 详细解读](https://wzhu.dev/posts/ot)——理解 OT 算法本身。
- [ElectricSQL](https://electric-sql.com/) / [ZeroSync](https://zerosync.dev/)——通用本地优先同步方案，与 LSE 的「应用层定制」形成对比。
- [Local-first software 论文](https://www.inkandswitch.com/local-first/)——本地优先理念的源头。

**License 说明**：原文仓库 LICENSE 字段为空，仅 README 正文 CC-BY 4.0（Wenzhao Hu, © 2025）。本文为原创解读，引用了原 README 的事实陈述与少量术语。

---

© 2026 钳岳 · 本解读为独立分析，所有架构描述基于仓库公开材料与 Linear CTO 公开演讲，未涉及 Linear 私有信息。
