---
title: "Cloudflare Computer：给 AI Agent 一台跑在 Durable Object 上的虚拟计算机"
date: 2026-08-12T03:23:25+08:00
slug: "cloudflare-computer"
github_repo: "cloudflare/computer"
source_key: "gh:cloudflare/computer"
description: "Cloudflare Computer 是一个运行在 Durable Object 内的虚拟文件系统，通过 FUSE 挂载、Worker 隔离沙箱和 JavaScript 动态 Worker 三种后端，为 AI Agent 提供可持久化的文件操作与代码执行环境。本文拆解其架构分层、同步协议、安全模型与性能边界，并追踪 PREVIEW 两个月的版本演进。"
draft: false
categories: ["技术笔记"]
tags: ["Cloudflare", "Durable Objects", "FUSE", "AI Agent", "虚拟文件系统"]
---

## 核心判断

Cloudflare Computer 解决的问题是：AI Agent 需要一个能持久化文件、执行代码、且不依赖外部服务器的"工作环境"。它的做法是把整个文件系统状态放进一个 Durable Object（DO）的 SQLite 存储里，再通过三种可插拔的后端把这个虚拟文件系统暴露给不同的执行环境。容器可以随时销毁重建，文件状态不丢——这是它与"给 Agent 一个 Docker"类方案的分界线。

截至 2026 年 10 月初，项目仍处于 PREVIEW 阶段——API 不稳定，官方明言不适合生产。但发表后两个月里它从 0.2.0 走到 0.4.0，五次升级补上了传输层鉴权、环境变量白名单、容器调度模型重构，演进方向清晰：把 Agent 工作环境当作正经的基础设施问题来做，而不是一次概念验证。架构思路值得拆解。

## 系统地图

整个系统分三层：

| 层 | 组件 | 职责 |
|---|---|---|
| **状态层** | Durable Object + SQLite | 文件系统的唯一权威状态（authoritative state），所有写入最终落到这里 |
| **协议层** | capnweb RPC | 连接 DO 与沙箱内守护进程 `computerd` 的双向同步通道 |
| **执行层** | 三种后端 | Container（FUSE 挂载）、Isolate Shell（just-bash）、Isolate JavaScript（Dynamic Worker） |

数据流的方向是：调用方通过 `workspace.runtime.exec(source, { backend })` 发起执行请求 → 选定的后端接管 → Container 后端通过 `computerd` 把 SQLite 中的虚拟文件系统以 FUSE 形式挂载到沙箱容器里 → 沙箱内的操作通过 capnweb RPC 同步回 DO。

关键点在于：文件系统状态只有一份，住在 DO 的 SQLite 里。沙箱看到的是这份数据的投影，不是副本。Workspace 也可以完全不挂执行后端——只要文件系统本身，`withWorkspace` 混入一个 DO 类就够。

## 三种后端

### Container 后端

最重量级的后端。工作方式：

1. 在 Cloudflare Container（标准 Linux 沙箱）内启动 `computerd` 守护进程
2. `computerd` 通过 FUSE 把 DO 侧的虚拟文件系统挂载为 `/workspace`
3. 沙箱内获得完整的 Linux 用户态——真实二进制、真实网络
4. 写操作通过 capnweb RPC 同步回 DO

Agent 因此可以在一个真实容器里运行 `git`、`pandoc`、`npm install` 等完整工具链，而文件状态由边缘 DO 持久化。

0.4.0 把这一类后端拆成了两个：`ContainerBackend`（默认）配合由 Durable Object 自己调度的容器（`scheduling_policy: "durable_object"`），每次启动可指定镜像、实例规格、entrypoint 和快照选项；`LegacyContainerBackend` 则沿用旧的平台调度模型，由 wrangler 配置的 `containers` 块决定镜像与规格。两者的连接流程相同：启动容器 → 把容器出站流量拦截回 DO 的 Worker Fetcher → `HEAD /health` 探活 → `/connect` 升级为 WebSocket 跑 capnweb 会话。

### Isolate Shell 后端

轻量级方案。在 Dynamic Worker 中运行 [just-bash](https://github.com/vercel-labs/just-bash)（一个用 JavaScript 实现的 bash 解释器），通过 Workers RPC 直接访问 DO 侧的 Workspace。没有容器、没有 FUSE、没有第二个存储——shell 操作直接映射到 DO 的 SQLite 文件系统上。

shell 按"功能组"打包：常驻核心之外，`curl`、`python`、`sqlite`、`jq`、`yq` 等各自是一个可选导入组，没导入的命令不会进 bundle，打包器会把它摇掉。适合不需要完整 Linux 环境、只要基本 shell 能力的场景。

### Isolate JavaScript 后端

在 Dynamic Worker 中执行 ECMAScript 模块。支持结构化输入输出、持久化相对导入、配置化的库依赖、Workspace 支撑的 `node:fs/promises`，以及受信任的 `ws:git` 和 `ws:artifacts` 模块。

与 Isolate Shell 的区别是：后者跑 bash 命令，前者跑 JS 模块。两者共享同一个"无容器、无 FUSE"的轻量模型。

## 同步协议：文件系统如何保持一致

Container 后端的核心复杂度在于 FUSE 挂载与 DO 之间的双向同步。设计文档描述了一套基于 capnweb 的 RPC 协议：

- **FUSE 挂载默认启用**。`computerd` 的 `FUSE_MOUNT=auto` 模式探测 `/dev/fuse`（Linux）或 macFUSE（macOS）：在 Cloudflare Containers 上内核 FUSE 可用；探测失败则透明降级为用户态 shim——把 VFS 子树物化到宿主文件系统并保持同步，用于大多数 CI 和没有 FUSE 的本地环境。
- **写入的同步路径**：沙箱内的写操作 → FUSE 驱动标记为 dirty → 下一次 `exec()` 调用的 post-exec pull 把变更拉回 DO。也可以通过 `workspace.push()` / `workspace.pull()` 显式触发同步。一次 pull 中途失败也不需要人工干预：同步水位标（watermark）持久保存进度，下一次 `pull()` 从断点继续。
- **chunk 级去重**：写入时按 512 KiB 分块，每块做内容寻址（content-addressed）存入 blob store。DO 只同步发生变化的 chunk，相同内容自动去重。

这个设计在 metadata 密集型操作上有优势（内存 inode store 比真磁盘快），但在大文件顺序 I/O 上有明显代价——代价的具体数字见下一节，其中一部分并不体现在官方表格里。

## 安全模型：0.3.0 补上的一课

PREVIEW 期头一个月，容器与 DO 之间的 HTTP 通道不设鉴权。0.3.0（9 月 11 日）改变了这一点，改动本身值得细读：

- **传输层鉴权**：宿主在启动容器时生成密钥，经 `RPC_CLIENT_SECRET` 环境变量传入；容器的 HTTP 面从此拒绝未携带该密钥的请求（`/health` 探活保持开放），容器回拨宿主时也要带同一密钥。宿主在建立会话前会先验证容器确实拒绝匿名请求——验证不过就直接 fail 掉连接，还在跑旧镜像的部署必须回收重建。
- **环境变量白名单**：容器里执行的命令不再继承容器的全部环境，只拿到 `PATH`、`HOME`、`TMPDIR`、时区与 locale 一类基础变量，外加 `COMPUTER_VAR_` 前缀的自定义变量（传入时剥掉前缀）。Agent 生成的命令看不到容器的其余环境变量。
- **启动规格固化**：每次启动记录 `{ env, enableInternet }` 规格，发现存活容器的规格与记录不符就重启它——在活跃容器上没法改环境变量和网络开关，索性不允许"带病续用"。从外部另起容器也一样：没有记录，不被信任，重启处理。

这套机制说明作者对威胁模型的认知在跟进：执行环境由模型生成的命令驱动，通道上跑的东西不能默认可信。

## 性能边界：表格里的数字，和表格外的成本

项目提供了一组基于 `fs-bench` 的基准测试数据，测试环境为 Cloudflare Containers standard-2 实例（1 vCPU / 6 GiB RAM / 12 GB disk）。

**computerd 超过磁盘基线的场景**（即更快）：

| 操作 | computerd | ext4 磁盘 | 比率 |
|---|---:|---:|---:|
| stat 1000 文件 | 1972 ms | 2659 ms | 0.91x |
| rm 1000 文件 | 828 ms | 1282 ms | 0.66x |
| mkdir 10×10×10 树 | 1598 ms | 3035 ms | 0.74x |
| find 树遍历 | 1814 ms | 4404 ms | 0.72x |
| git init + commit 100 文件 | 459 ms | 635 ms | 0.72x |
| npm init + 小安装 | 599 ms | 631 ms | 0.95x |

这些场景覆盖了 `git status`、模块解析、增量构建等日常工作的大头——metadata 操作走内存 inode store，天然比磁盘快。

**computerd 落后的场景**：

| 操作 | computerd | ext4 磁盘 | 比率 |
|---|---:|---:|---:|
| 写 64 MiB | 231 ms | 17 ms | 16.9x |
| 读 64 MiB | 438 ms | 26 ms | 39.7x |
| copy 64 MiB | 1037 ms | 40 ms | 40.5x |

大文件顺序 I/O 慢的原因是每个 512 KiB chunk 都要计算内容寻址哈希存入 blob store。这是同步去重的设计代价。

完整的 `npm install`（854 包 / 36675 文件）：computerd 124.7 秒，ext4 磁盘 63.9 秒，tmpfs 34.3 秒。大约比磁盘慢 2 倍。

这几组数字要分着看。慢的并不是"计算机跑得慢"，而是**大文件顺序读写**这一条窄路径：写 64 MiB 慢 16.9x、读慢 39.7x、copy 慢 40.5x，共同指向同一个根因——每 512 KiB 一算的内容寻址哈希。它换来的是跨沙箱复用时的去重收益，代价落在单文件的顺序搬运上。反过来，metadata 密集操作（stat、rm、mkdir 树、git init）反而更快，因为内存 inode store 跳过了磁盘寻址。

但官方文档在同一页性能数字上方加了一个重要警示：**表格测的是挂载，不是回传**。`npm install` 的 124.7 秒在命令返回时就停表了，之后把 36,675 个文件搬进 Durable Object 的时间完全没有计入——而对依赖树来说，回传才是更大的成本。issue #179 记录了一个真实案例：安装 120 秒超时，随后花了约 3 分钟才把部分 `node_modules` 拉回 DO，下一条命令又因存储超时失败，且 Workspace 没能从中恢复。给自己的工作负载做容量估算时，这部分要自己加上，或者干脆让依赖树留在容器本地磁盘。

留在本地正是 `MOUNT_IGNORE` 的用途：匹配的路径直接由容器磁盘服务，不进 VFS、不进存储、不进同步协议。不过它省的是回传字节，不是 FUSE 往返——字节仍要从内核拷进守护进程。文档算过这笔账：passthrough 模式可以连这一跳也省掉，但 computerd 经 `fuse-native` 绑定的是 libfuse 2.9，passthrough 需要 libfuse 3.17 的 API，所以本地路径的 `npm install` 实测仍会贴着表格里 computerd 那一列，而不是 ext4 那一列。

另一个常被忽略的维度是存储位置。`computerd` 的 SQLite 存储默认驻留内存，设 `COMPUTERD_DB` 指向路径即落到容器磁盘。对比数据显示：读几乎不受影响（2000 个文件的 stat 在 2 MiB 缓存对 3.8 MiB 数据库的极端配置下仍是 0.99x），写则明显变慢——创建 2000 个文件，内存 181 ms，磁盘 659 ms。这解释了 README 里的那句限制："容器侧文件系统驻留内存，按 agent 规模的工作目录设计，别拿来装整个 monorepo。"

所以不能从这些数字推出"computerd 整体比 ext4 慢"或"不适合跑重负载"。它适合的是以 metadata 操作为主、单文件小的场景（git 状态、模块解析、增量构建）；不适合的是单文件上百 MiB 或文件数上万的依赖树——视频、大模型权重、装完还要持久化的 `node_modules`。做取舍前，先想清楚自己工作负载里大文件顺序 I/O 和回传各占多少。

## 一个具体的请求流

以 `examples/tutorial` 为例——这是一个 step-by-step 的构建教程：

1. Worker 接收到 HTTP 请求，调用 `workspace.runtime.exec("pandoc recipe.md -o recipe.pdf", { backend: "container" })`
2. Container 后端在 Cloudflare Container 中启动 `computerd`
3. `computerd` 通过 FUSE 把 DO 侧 SQLite 中的虚拟文件系统挂载为 `/workspace`
4. 前序步骤写入的 `recipe.md` 已经在 FUSE 视图中可见
5. `pandoc` 读取 `/workspace/recipe.md`，生成 `/workspace/recipe.pdf`
6. `computerd` 通过 post-exec pull 把新文件 `recipe.pdf` 的 chunk 同步回 DO
7. Worker 通过 `workspace.fs.readFile("/workspace/recipe.pdf")` 读取结果

整个过程中，文件系统状态始终以 DO 的 SQLite 为唯一权威来源。

## 两个月、五次升级：PREVIEW 期的演进轨迹

版本历史本身是这个项目最有信息量的部分——它披露了作者认为什么问题必须先解决（0.2.0 是本文初稿时的最新版，列在这里作基线）：

| 版本 | 日期 | 主要内容 |
|---|---|---|
| 0.2.0 | 2026-08-11 | 出口流量（egress）配置统一；分页目录列表；`read` 工具支持图片与数据格式；worker-shell 命令改为可选导入以缩减 bundle |
| 0.2.1 | 2026-08-17 | 同步 pull 峰值内存修复——应用文件条目时直接链接对端已暂存的 chunk，不再读回拼接成整文件缓冲（原先要在 isolate 里同时握住约两倍文件大小的内存）；`container-shell` 在 `computerd` 重启后安全重连，进程级执行句柄在容器被替换后返回 `EEXEC_LOST` |
| 0.3.0 | 2026-09-11 | 传输层 bearer token 鉴权；命令环境变量白名单；启动规格固化与不匹配重启（见上文安全模型一节） |
| 0.3.1–0.3.2 | 09-18 / 10-01 | `fs.rename`；`find`/`grep` 支持 `exclude`；符号链接文件面文档化；git diff 按命名路径加速 |
| 0.4.0 | 2026-10-02 | 容器后端按调度模型拆分为 `ContainerBackend`/`LegacyContainerBackend`；`ContainerBackend.ignore` 本地路径；pi 与 TanStack AI 工具集；`ws:git` 默认全量历史克隆 |

两个月的线索连起来读：先修正确性（内存、重连），再补安全（鉴权、白名单），然后才动架构（调度模型拆分）。这也是判断一个 PREVIEW 项目靠不靠谱的实用信号——它的问题是按优先级解的，不是按热度解的。

## 生态方向：MCP 与 RLM 两个示例

`examples/` 目录从文章初稿时的 9 个扩到了 15 个，其中两个指向这个项目真正的野心。

**examples/mcp** 把整个 Computer 包成一个 MCP 服务器，对客户端只暴露一个 Code Mode `code` 工具——背后是一个持久 Workspace、一个快速 Worker shell 和一个完整 Linux 容器。Agent 不拿到一堆细粒度的文件工具，而是拿到"写 JS 来操作工作目录"这一个口子。端点默认 fail-closed，必须配 `MCP_TOKEN` 才能访问。

**examples/rlm** 演示如何用 Computer 构建递归语言模型（RLM），口号是"模型管语义，代码管总量"：长语料放在 Workspace 里而不是塞进父模型的 prompt，模型生成一段 JavaScript 模块去读语料分区、给每个分区发起有界的模型调用、再用普通代码校验和归约结果。示例任务把 2,433 个句子按正式/非正式分类，RLM 把语料切成 22 个分区跑模型，最后用 JS 精确累加标签数。这就是"文件系统即 Agent 工作目录"的完整形态——文件不只是持久化状态，还是代码的输入输出和模型调度的缓冲区。

## 适用边界

**适合尝试**：

- AI Agent 需要持久化文件状态，且希望文件系统操作在边缘网络上完成
- 需要 Agent 在真实 Linux 环境中运行完整工具链（git、编译器、CLI 工具）
- 探索"文件系统即 Agent 工作目录"的编程范式，MCP 与 RLM 两个示例是现成的起点

**当前限制**：

- PREVIEW 阶段，API 不稳定，设计可能变化
- 单个 Workspace 约 10 GB 上限（与 DO 共享存储）；容器侧文件系统驻留内存，按 agent 规模设计，不适合 monorepo
- 大文件 I/O 性能差距明显，依赖树回传成本未计入基准表格（对视频、大模型文件、装完要持久化的 `node_modules` 都不友好）
- 需要在 Cloudflare 生态内使用（Durable Objects、Containers、Workers）
- 不接受非协作方的 unsolicited PR——补丁请走 issue 或 discussion，未经邀请的 PR 可能被直接关闭

## 采用建议

PREVIEW 阶段决定了它不适合现在就当场架生产链路，但架构思路值得先跟上：

- **想验证的团队**：用 `examples/tutorial` 跑通一次"挂载 → 执行 → 同步回 DO"的完整路径，重点看两个问题：你的工作负载是大文件还是 metadata 密集；换主/重启后文件状态是否真的不丢。再用 `examples/mcp` 试着把工作目录接到你现有的 Agent 上。这两个答案决定它和你业务合不合。
- **想在生产落地的团队**：等 API 稳定、版本出正式 release 再评估。盯三件事：大文件 I/O 与回传成本的优化方向（`MOUNT_IGNORE` 是当前答案的一半）；0.3.0 引入的鉴权机制会不会再收紧；issue #179 一类的存储超时有没有结构性修复。
- **仅做技术跟踪的团队**：把它当作 Cloudflare 在"Agent 原生文件系统"上的探路实验。同门还有 cloudflare/sandbox-sdk（跑边缘沙箱代码环境），一个卖"有状态的文件系统"，一个卖"开箱即用的沙箱执行"，对照着看能更快看清 Cloudflare 对 Agent 基础设施的切分思路。

## 与同类方案的差异

这个项目与"给 Agent 一个 Docker"类方案的区别在于：状态不在容器里，而在 Durable Object 里。容器只是执行环境，可随时销毁重建，文件状态不丢。与"给 Agent 一个远程文件系统"类方案的区别在于：文件系统是 SQLite 中的虚拟实现，不是 NFS 或 SSHFS——这意味着可以做 chunk 级去重、内容寻址、与 DO 的强一致性。

在 Cloudflare 自家版图内，它与 sandbox-sdk 也不是重复建设：sandbox-sdk 提供沙箱化的代码执行环境，Computer 提供以文件系统为权威状态的执行面——后者的性能文档甚至把完整安装 cloudflare/sandbox-sdk（854 包）当作最重的负载测试用例。这个"把文件系统做成状态机、把执行环境做成投影"的定位，目前仍然是这个仓库独有的实验。

## 版本与仓库信息

- **仓库**：[cloudflare/computer](https://github.com/cloudflare/computer)
- **Stars**：9,445（截至 2026-10-03；本文初稿时为 7,567）
- **主要语言**：TypeScript
- **许可证**：MIT
- **最新版本**：@cloudflare/computer@0.4.0（2026-10-02）
- **活跃度**：近三个月保持每周多个提交，处于活跃开发状态
