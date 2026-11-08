---
title: "Comma：一个不靠对话记住你的 AI，需要把三件事写进类型系统"
date: "2026-11-08T11:53:00+08:00"
slug: "afk-surf-comma-sessionless-agent-formal-verification"
github_repo: "AFK-surf/Comma"
source_key: "gh:AFK-surf/Comma"
description: "Comma 把「会话是无状态的、任务是持久执行状态」这句话落到了运行时：每个 Agent 是 Erlang VM 上的独立进程，副作用动作先记账再执行，Elixir/OTP 负责故障恢复，Lean 4 负责被机器检查的不变量，TLA+ 负责分布式协议的模型检查。这篇文章拆它的三条主线，并说明它离可用的个人 Agent 还差多远。"
draft: false
categories: ["技术笔记"]
tags: ["Elixir", "Lean 4", "TLA+", "形式化验证", "Agent 架构", "分布式系统"]
---

## 先说判断

大多数「个人 AI 助手」项目在解决一个其实不难的问题：怎么让模型记得昨天聊过什么。Comma 的作者们选了相反的路——他们认为「记住」根本不是重点，重点是**当一次执行被中断、崩溃、重启之后，系统怎么知道这件事到底做完没有**。

这个转向决定了整个项目的形状：

- 仓库里有 11,756 个文件。
- 后端是 Elixir/OTP umbrella，`systems/apps/` 下 34 个应用。
- 关键不变量用 Lean 4 写死并机器检查，分布式协议用 TLA+ 做模型检查。
- Agent 的隔离靠 eBPF 程序（spinfoam）而不是容器。

2026 年 9 月 30 日第一次提交，10 月 27 日最后一次 push，仓库里 8 次提交有 6 次标题是 `Sync Comma source`——这不是一个社区项目的样子，是一个团队把自己的代码同步到公开仓库的镜像。

所以这篇东西的价值不在「介绍一个 536 star 的新项目」，而在它把「长跑型 Agent 系统」这件事最难的部分摊开给你看：**幂等、围栏、状态权威、未知态**。

这四个词在大多数 Agent 框架文档里根本不出现，因为它们的失败模式要在跑了几千次、崩了几百次之后才会显形。Comma 选择在最贵的层（形式化验证）上先把它们钉住。

下面先给系统地图，然后拆三条主线：执行模型、幂等围栏、验证边界。最后说它离「能用的个人 Agent」还差什么。

## 系统地图

Comma 的部署形态是一个 Docker Compose 单机栈，跑 6 个服务：

```text
                    浏览器 / Mac App / 移动端
                              │
              ┌───────────────┴────────────────┐
              │                                │
        Comma Web :8080              Comma Admin :8082
        （用户界面 + Assistant Chat）      （管理面）
              │                                │
              └───────────────┬────────────────┘
                              │
                    Comma Product API :8081
                              │
                    ┌─────────┴─────────┐
                    │  Salix（Agent 运行时）│
                    │  Elixir/OTP umbrella │
                    └─────────┬─────────┘
                              │
        ┌──────────┬──────────┼──────────┬───────────┐
     Postgres    Redis      MinIO     ClickHouse   Mailpit
    （权威状态） （协调）  （对象）  （可观测）  （本地信箱）
                              │
                    Salix Mac 客户端（Salix）
                    连接你的 Mac：读文件、改文件、
                    跑命令、把手上的活交给 Codex / Claude Code
```

叠加在运行时之上的是三层验证，它们不是「测试」，是三种不同强度的保证：

| 层 | 工具 | 保证什么 | 不保证什么 |
|---|---|---|---|
| 内核不变量 | Lean 4（`systems/native/verified_kernel/`） | Session 状态机、幂等重试、工具授权（IFC）的规则被机器检查 | 外部调用是否真的成功、任务是否达成目标 |
| 分布式协议 | TLA+（`tla/`，≤5000 行预算） | 冲突提交、陈旧 owner 写入、丢输入、重复授权这类并发故障不会静默发生 | 整个系统的 exactly-once；不覆盖客户端代码 |
| 实现回归 | Elixir / Vitest / Rust 测试 | 具体代码路径的行为 | 任何未被建模的边界 |

注意第三行的位置：TLA+ 只覆盖核心服务端，客户端代码没有模型。README 里那句「形式化验证不证明模型的判断力或任务成功，它验证的是运行时在出故障时仍然遵守自己的规则」，是整个项目最诚实的一句话。

## 主线一：Task 是唯一权威的执行状态，Chat 只是界面

Comma 的核心设计决策写在 `docs/architecture/PRODUCT_MODEL.md` 里，一句话：**对话只是界面，任务才是持久的执行状态**。

这句话拆开看，意味着几件事同时成立：

- **Conversation 是消息事实的边界**，有 `user_chat` 和 `agent_task` 两种 kind。`agent_task` 类型的 Conversation 就是一个 Task。
- **Task 生命周期只有一份权威**，就是 Conversation 的 `status` 字段。Gate progress 是执行细节，不是第二套状态机。这条约束消灭了「进度显示和真实状态对不上」这一整类 bug——很多 agent 框架的看板就是靠两套状态并存才出问题的。
- **Router 是协调者，Worker 是执行者**。Router 在一个范围内有 0..1 个（chat-ready 时必须是 1），Worker 是 0..N 个。用户跟 Router 说话，Router 通过 `im_api.internal.task.create` 派发 Task，Worker 负责具体干活并把结果作为普通消息发回来。
- **人工验收是独立动作**，不是「系统说完成了就算完成」。自动化跑完停在 `ready_for_review`，必须由人审阅，并且经过版本校验才能进 `completed`。一个状态是 `completed` 不代表人接受了它。

这里有个容易被忽略但很聪明的设计：Router 派发 Task 时用 `content` 字段承载全部自足信息，同时传入一个 `loop` 参数。

**Loop Task 不新增任何实体**——它就是一个 Task，只是额外显示一个 Background Loop，节奏、限额、运行次数、状态全在 Loop 行上，Task 自己没有 `loop` 值。Router 不会为每次运行创建一个新 Task，也不会用 `schedule` 机制。

Loop 的运行计数逻辑值得单独说。每次唤醒是一次 `agent.notify`，owner 把它作为私有 `agent_input` 消息追加到 Task 里，去重键是 `loop:<id>:<dedup_key>`。所以「同一次运行被投递两次」在数据层面就折叠成一次，不会重复触发。而 Task 的状态和 Loop 的状态是两回事：

| Task 状态 | 对 Loop 的影响 |
|---|---|
| `active` / `escalated` | 无。Loop 按自己的状态跑或等。 |
| `ready_for_review` | **拒绝**—— Loop 还没结束就不许进入待审。一次报告是一次运行，不是工作的终点。 |
| `completed` / `cancelled` / `failed` | 发布状态时结束 Loop，原因就是该状态。 |
| `archived` | Loop 以 `cancelled` 结束。恢复 Task 不会让它重跑。 |

这张表解决的是一个真实的坑：一个「每天早上 9 点生成日报」的 Loop Task，如果某天早上跑完就立刻进 `ready_for_review`，用户审阅完点完成，Loop 就被连带结束了——后面几天的定时任务静默消失。Comma 明确拒绝这种转移。

### 一个任务如何流过系统

拿「看 PR #12 的新评论，处理每一条，合并后停掉」这个真实场景走一遍：

1. **用户对 Router 说这句话**。Router 识别出这是「重复 + 持续观察」型工作，不是一次性问答，于是准备创建 Loop Task。它不调 `schedule.create`，也不调 `loop.build`——后者是 Worker 的活。
2. **Router 组装 request**。不同类型的参数有严格的归属规则：

   - 节奏放 `loop.cadence`。这里是 `events`，标签如「PR #12 新评论」，限 1..32 字符。
   - 工作内容、条件、涉及的人全放 `content`。
   - 停止条件放 `until`，限 500 字节。
   - `max_runs` 只在用户明确说了次数时才填。
   - `ends_at` 只在明确说了日期时才填。

   **Router 不许自己发明一个限制。** 用户没给时区，Router 也不填，服务端用请求方设备或来源的时区；两个都没有就拒绝创建。Router 会先问一次，给出「每天 09:00」这样的具体建议，答案回来之前什么都不建。
3. **Router 调 `task.create`**，同时传 `agent_id`、自足的 `content` 和 `loop`。服务端先写 Loop 为 `pending`，**再**建 Task 和命令——顺序是刻意的，避免出现「Task 存在但 Loop 不存在」的中间态。
4. **Worker 接命令后建 Loop**。它用 `loop.sdk` / `loop.build` / `loop.create` 提交程序，Loop 变 `active`。Loop Task 必须跑在 Salix 里——station 或 Group Cloud VM 上的 Session 没有 Salix 工具，Loop 会永远停在 `pending`。
5. **每次运行**。定时程序调 `loop.next_run` 拿下一次；事件程序等自己的事件。运行被记在 Loop 行的 `run_count` 和 `last_run_at` 上，同一来源只算一次。
6. **停止**。几种情况会终结 Loop：达到 `max_runs` 的那次运行计数后结束；首次唤醒时、`loop.next_run` 时、或加载时已过 `ends_at`；剩下的由 Reconciler 每分钟扫一遍收尾——**没有专门的 deadline 定时器**。

   之后 Worker 报告停止条件成立，Router 才把 Task 置为 `completed`。如果 Loop 是自己停的（`exited` / `failed` / `budget` / `quota` / `undeliverable`），Task 状态不变，由 Worker 在 Task 里说明原因。

整个流程里值得玩味的是第 3 步和第 6 步的边界：**Loop 可以自己结束，但 Task 的完成必须由 Router 依据 Worker 的报告来做**。系统不允许「机器觉得做完了」。

## 主线二：围栏与幂等——把「不确定」当一等公民

这是 Comma 与其它 agent 框架差距最大的地方，也是它花最多工程成本的地方。

### 从「重试」到「不重复产生副作用」

Agent 系统的经典事故链是这样的：模型调了个有副作用的工具（发邮件、改文件、提交代码），请求发出去了，网络断了，agent 不知道成没成，于是重试——副作用发生两次。

Comma 的处理方式是把它拆成「准备」和「承诺」两阶段。`durable_fence/4` 通过快照 CAS（compare-and-swap）把状态持久化下去。文档里写得很直白：**冲突时 fail closed，绝不把计划套到另一个 owner 的状态上去重放**。

几个具体的不变式：

- **Provider 的输出在围栏成功之前一直被闸住**。模型说了什么、准备做什么，只有在「这件事已经被持久化了」这个事实成立之后，才允许变成真实效果。
- **写入确认不等于业务完成**。队列 ACK 只确认了「材料化了」，它不解除任何业务义务或回复义务。这条区分很关键——很多系统在这里偷懒，把「消息收到了」当成「事情做完了」。
- **工具永不重复执行**。重启规划会拿持久化的能力请求去对 Session 的执行记录。存下来的结果保留，查找重试有界。
- **歧义不等于失败**。有歧义的 CAS 会把实际读回的字节和保留的上传字节做比较。四次结算尝试后才做四次只读尝试；用尽之后返回 `commit_indeterminate`，**且不给重放权**——系统在这种状态下宁可停住，也不猜。
最后这一条是整个设计的道德底线：**不确定时停下，而不是赌一把**。

### 一个具体的失败场景

假设 agent 正在改一个文件，工具调用的意图已经通过围栏持久化了，但响应没回来就崩了。重启之后：

- 重启规划发现这条工具调用的执行记录状态不明。
- 它不会重跑工具（工具永不重复执行）。
- 它会把这个 Session 的状态从存储重新加载（`load`），因为「启动、未保留的写入、结果未知的路径」都走重新加载。
- 如果发现这次工具调用确实产生过副作用，恢复计划会告诉后续逻辑「这一步已经发生过了」。

对比一下 `flush_id` 的注释——**它是诊断用的，不是持久化成功的证明**。这个区分在事故复盘时价值极大：你不会因为看到一个 flush id 就相信写入成功了。

### 并发写入的仲裁

两个 owner 同时改同一个 Session 会怎样？答案是 CAS 冲突时**丢弃驻留版本**（discard the resident revision），重新读存储再决定。文档提到还有一次「歧义 CAS 比较原始读回字节」的路径——网络响应本身被篡改或截断时，能发现上传内容和实际存储的不一致。

这是分布式系统里少见的严谨：大多数实现只做「CAS 失败就重试」，Comma 额外处理了「我以为写成功了，其实写的是别的东西」。

## 主线三：验证边界——哪些保证是真的，哪些明确不是

Comma 的验证体系有明确的自我限制，这一点比它的证明本身更有信息量。

### Lean 内核管什么

`systems/native/verified_kernel/` 里的 Lean 4 代码是唯一的 Session 实现。宿主拿的是一个不透明句柄（`SalixAgent.InternalSession`），**不能改它的字段**；只有 `load` / `persist` / `open` / `export` 四个点能让状态以数据形式进出。

分工划得很清楚：

| Lean 所有 | 宿主所有 |
|---|---|
| 表示、压缩决策、结算、重启规划、等待超时、激活重试截止 | 定时器投递、进程观察、外部权威、持久化提交、图像读取、凭据、网络 I/O |
| provider 请求投影、附件来源、Anthropic Messages / OpenAI Chat / Responses 的编码解析、SSE 状态、重试决策 | 站点代理的聊天翻译、媒体 API |

文档里有一段专门说明「哪些不保证」，值得原样记住其精神：

> 这些定理不主张 provider 调用的回滚、不主张外部效果的 exactly-once、不主张调度进展、不主张用户任务达成。

以及关于证明边界的一句：「领域从空的现代存储开始。遗留和导入的初始状态需要另一个证明。所有者把证明边界划在 Lean。外部代码是被假设的，不是被建模的。」——包括 Elixir 和 Erlang、标准库、C、BEAM 和 FFI、编解码器、存储。

**Lean 只证明纯定义的终止性。这不证明任何执行时长的上界，不证明外部调用的终止性，也不证明 Actor 的重试会有进展。** 大部分查询没有被证明。一个不透明句柄本身也不构成语义边界。

### TLA+ 管什么

`tla/` 目录有明确的 5,000 行物理行数硬预算（注释和空行都算），并且明确禁止「把模型移出仓库来绕过预算」。保留四个套件：

| 套件 | 防的是什么系统级故障 | 边界 |
|---|---|---|
| Salix | 冲突的持久化提交；陈旧 owner 写入；重复或已确认但未持久化的输入；归档丢失；外部运行时接受/身份混淆 | 每对象 CAS + 有界故障；不是全系统 exactly-once |
| Mesh 信任 | 已撤销成员身份复活；未授权的路由/结果重放；密钥确认前配对 | 抽象密码学 + 注册表 CAS；条件收敛，不是密码学证明 |
| Billing | 未支付/重复发放；ACK 早于日志提交；陈旧订阅事件覆盖 | SQL 事务/行锁假设 + 当前 provider 读；无投递活性 |
| 签名密钥轮换 | 新签名密钥在合规验证器缓存能容纳它之前被使用 | 常规轮换 + 有界缓存年龄；无紧急轮换/操作员进展保证 |

文档里有一句很克制的话：**「这些是有选择的、有界的检查，不是 Comma 的组合证明。」** 而且明确区分了 safety 和 liveness——「不要从 safety 推断 liveness」。

「Deliberately not modeled」一节同样诚实：客户端代码没有 TLA+ 模型；功能/UI 生命周期、呈现、本地排序、单个集成、搜索索引、调度精化、Workflow/Triage reducer、配置子步骤、迁移协议都没有专门模型。「缺少模型不构成这些行为已被证明的声明，也不授权移除产品需要的运行时校验、测试或恢复。」

### 工具授权：IFC

信息流控制（Information Flow Control）是 Lean 模型负责的另一块。规则可以概括成两句：

- **工具请求需要同一权威下已消费的命令**。数据、转发的文本、不可信的网页都不构成授权。未知权威不是许可。
- **来源准入区分四种情形**：普通流转、原位使用、回执、指令。普通流转要求 `readersSubset(destination, source) = yes`；非流转准入需要策略里声明的可读、未封装来源事实。

一个显式的空来源列表就是空。模型不追踪自己积累的知识作为隐式标签集。租户、目的地、成员身份、来源和请求事实在各自的宿主边界解析。

还有一条针对 Task 的细节值得留意：内部 Task 报告要为 Task 的**人类读者**解析投放位置，不只是指派的 agent。存储的投放事实和已认证的入口投放优先于 provider 回退。

Slack Task 读者事实缺失时，每个连接每次解析最多读 20 个具名用户。结果按安装世代作用域缓存 1 分钟，用 4,096 个节点本地槽位。过期条目不授权转移，provider 失败、禁用的安装和超限的读者都保持「未知」。

**这不给了 agent 作者的 Task 消息任何通用命令权。** Task 所有权只授予列出的效果，IFC 仍然检查来源和目的地。

## 本地运行与部署边界

自托管的门槛按 README 说得很清楚：Docker Engine + Compose v2.24 以上，构建时要下载 Lean、Elixir、Go、Node 的公开工具链，需要一个模型 provider 账号。

```sh
cp .env.example .env
# 设 COMMA_OWNER_EMAIL（这个账号获得 Admin 权限）
docker compose up -d --build
```

起来之后是这几个入口：

| 接口 | 默认地址 |
|---|---|
| Comma Web | http://localhost:8080 |
| Comma Admin | http://localhost:8082 |
| Comma Product API | http://localhost:8081 |
| Salix dashboard | http://localhost:4000/dash |
| 本地信箱（Mailpit） | http://localhost:8025 |

登录码在 Mailpit 里读——这在本地开发时很方便，**但也是一条安全边界**：本地信箱只能绑 loopback，任何能读到它的人都能拿到你的登录码。公网部署必须换真实 SMTP。

默认所有端口只绑 loopback。对外暴露时有三处硬约束：Web、Admin 和 Product API 必须在同一个可注册域名下用**不同的 origin**；要配真实 SMTP；本地信箱仅限 loopback。Group 云电脑需要 Cloudflare 配置；会议和 Agent VMM 主机需要本仓库不含的运行时。

升级和备份的规矩也很硬：**升级前停栈**，五个命名卷（`config`、`postgres`、`objects`、`clickhouse`、`redis`）要一起备份。`config` 卷存加密密钥和认证密钥，不要删它、不要重新生成它的密钥。`docker compose down` 保留数据，除非加 `-v`。

### Salix 那一侧

Salix 是连你 Mac 的本地代理。它的设计要点在 `docs/agent-runtime.md` 里：LLM、压缩、工具、运行时和 Connector 都需要有界通道、owner 身份、截止时间、取消和过期结果栅栏，**它们不能阻塞核心控制或无限期阻塞另一个租户**。

超时数字给得很具体：模型请求 600 秒（含重试），Router 轮次请求 300 秒，流在 120 秒内没有首个 SSE 事件、或事件之间间隔 30 秒就失败（`: keep-alive` 注释不算事件）。

Salix 也接外部 agent——Codex、Claude Code、Pi、Kimi 都能作为应用调用或注册成 Worker 与 Sub-agent。项目自己的定位是「Keep your existing tools and workflows. Comma orchestrates and automates them.」

## 采用建议与边界

**该用什么、什么时候不必用**：

- **如果你在写长跑型 agent**（每天自动跑、盯 PR、盯价格、写日报），Comma 的 Loop Task 模型值得抄。哪怕你不写 Elixir，那套「Task 是唯一权威状态」「Loop 结束 ≠ Task 完成」「Router 不许自己发明限额」的规则可以直接套进任何 agent 编排层。
- **如果你关心的是「agent 会不会把事情做两遍」**，围栏那一节的模型值得读。尤其值得看的是「歧义时返回 `commit_indeterminate` 且不给重放权」这个选择——很多框架在这一点上默默选了「重试」，然后在生产环境制造重复副作用。
- **如果你只是想要一个能用的个人助理**，Comma 现在太重了。536 stars、AGPL-3.0、8 次提交里 6 次是源码同步、正式发布时间距今不到两个月——它是一个正在施工的架构宣言，不是可以拿来用的产品。
- **如果你在评估自托管成本**，算一下：单机栈要跑 Postgres + Redis + MinIO + ClickHouse + Mailpit 五个服务，构建期要下载四套工具链。为了省一个订阅费而背这个栈，未必划算。

**AGPL-3.0 这条要说清楚**。仓库用的是 GNU Affero General Public License v3。如果你要把 Comma 改造成闭源 SaaS，或者把它作为网络服务提供给别人用，AGPL 的网络条款会要求你公开你的修改版本。这不是技术细节，是决定产品形态的前提——在评估阶段就该看清楚，而不是等到写完代码才发现。

**它明确不做的事**（README 自己列的）：不上传你的应用到云端（分析在本机跑，agent 会拿到工具结果，但模型 provider 有自己的数据政策）；不提供工具许可、密钥或激活权利；用户必须自己合法取得 IDA Pro / Hopper / JEB 的商用许可。

## 常见问题与排查

**Q：Task 显示 `ready_for_review` 但 Loop 还在跑？**
A：这是设计。服务端在 Loop 未结束时拒绝进入 `ready_for_review`——「一次报告是一次运行，不是工作的终点」。如果你看到 Task 停在待审而 Loop 仍 active，那是 Loop 还没结束，不是状态错乱。

**Q：Loop Task 一直停在 `pending`？**
A：Loop Task 必须在 Salix 内运行。station 或 Group Cloud VM 上的 Session 没有 Salix 工具，它们的 Loop 会永远停在 `pending`。另外 Loop 是由 Task 的 Worker 通过 `loop.build` / `loop.create` 建的，Router 自己不会建。

**Q：崩溃重启后某个动作会不会被重复执行？**
A：工具不会重复执行。重启规划会拿持久化的能力请求对 Session 执行记录，已存下的结果保留。如果某次写入结果未知，系统返回 `commit_indeterminate` 而不是重放——这时需要人工看一眼，不是自动重试。

**Q：`flush_id` 有值，能确认写入成功了吗？**
A：不能。它是诊断用的，不是持久化成功的证明。

**Q：升级会丢数据吗？**
A：不会，但必须先停栈，并把五个命名卷一起备份。`docker compose down` 保留数据；不要加 `-v`，除非你确实想删掉这个实例。`config` 卷尤其不能动——它在持有加密密钥。

**Q：TLA+ 跑不起来？**
A：需要 Java 11+。macOS 上用 Homebrew 装的 OpenJDK，把它的 `bin` 放进 `PATH`。CI 里有 `Systems TLA+ Model Checks` 这个 workflow。

## 小结

Comma 真正有意思的地方不是它有 536 个 star，也不是它把自己叫作「the best free & open source super agent」（这是仓库 description 里的原话）。有意思的是它对「一个 agent 系统在凌晨三点崩了以后如何知道自己该干什么」这个问题的回答方式：**用类型系统写死不变量，用模型检查穷举并发故障，用不透明句柄阻止宿主偷改状态，用「不确定就停」代替「不确定就重试」。**

这套做法有明确的代价——11,756 个文件、四层工具链、一套 Lean 4 内核。也有明确的收益：它的运行时规则在故障下仍然成立，而这恰恰是长跑型 agent 最难做到的部分。

如果你是从 2026 年 9 月底开始关注这个方向的，那么现在（2026 年 11 月初）它更像一份写给未来的设计文档加一份可运行原型。读它、抄它的模型判断，别急着抄它的部署栈。

---

## 术语表与版本追溯

| 术语 | 含义 |
|---|---|
| Task | 一个 `agent_task` 类型的 Conversation，代表一件独立且可持久的工作；生命周期状态只有 Conversation `status` 一份权威 |
| Router | 工作范围内唯一的当前协调 Agent（0..1，chat-ready 时为 1），负责派发 Task 而非执行 |
| Worker | 执行具体任务的 Agent（0..N），一个 Worker 可处理多个独立 Task |
| Gate / Progress | Gate 定义阶段，Progress 是 Gate 的一次具体 activation；Progress 不是第二套 Task 状态 |
| Background Loop | Agent 拥有的 eBPF 程序（跑在 spinfoam 上），记录节奏、限额、运行次数与 checkpoint；一个 Task 至多一个 Loop |
| Loop Task | 带 Background Loop 的 Task；不新增实体，只额外显示一个 Loop |
| Salix | Agent 运行时（Elixir/OTP umbrella），也是连接用户 Mac 的本地代理 |
| Comma | 产品侧（Web / Admin / Product API），持有用户、Workspace 与订阅关系 |
| Workspace | Comma 的授权范围，同时也是 Agent 工作范围 |
| IFC | 信息流控制（Information Flow Control），由 Lean 系统模型负责的工具授权机制 |
| 围栏（durable fence） | 通过快照 CAS 持久化执行意图的机制；冲突时 fail closed，不重放 |
| CAS | compare-and-swap，基于保留修订号的并发写入仲裁 |
| 宿主（host） | 运行 Lean 内核的 Elixir/Erlang 侧；只持有不透明句柄，不能修改 Session 字段 |
| spinfoam | 承载 Background Loop eBPF 程序的执行层 |

**版本追溯**：本文基于 `AFK-surf/Comma` 仓库 main 分支在 **2026-11-08** 的状态。核对时的仓库事实为：536 stars / 45 forks / 7 个 open issues，AGPL-3.0 许可，主语言 Elixir，仓库创建于 2026-09-30，最后一次 push 为 2026-10-27，8 次提交中 6 次标题为 `Sync Comma source`，git 作者 3 位。

上游变动频繁（10-27 仍在 push），文中所有协议细节、限额数值与超时参数都以上述时间点的仓库原文为准。若要复现本文的核对过程，读 `docs/architecture/PRODUCT_MODEL.md`（产品语义入口）、`docs/architecture/DOMAIN_CONCEPTS.md`（概念清单）、`docs/verification.md`（验证边界）、`docs/agent-runtime.md`（运行时契约）、`tla/README.md`（模型边界）五份文件即可覆盖全文论断的来源。

---

**数据来源**：[AFK-surf/Comma 仓库](https://github.com/AFK-surf/Comma) · [comma.surf](https://comma.surf) · [README.md](https://github.com/AFK-surf/Comma/blob/main/README.md) · [PRODUCT_MODEL.md](https://github.com/AFK-surf/Comma/blob/main/docs/architecture/PRODUCT_MODEL.md) · [DOMAIN_CONCEPTS.md](https://github.com/AFK-surf/Comma/blob/main/docs/architecture/DOMAIN_CONCEPTS.md) · [verification.md](https://github.com/AFK-surf/Comma/blob/main/docs/verification.md) · [agent-runtime.md](https://github.com/AFK-surf/Comma/blob/main/docs/agent-runtime.md) · [tla/README.md](https://github.com/AFK-surf/Comma/blob/main/tla/README.md) · [docs/salix/](https://github.com/AFK-surf/Comma/tree/main/docs/salix)
