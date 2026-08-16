---
title: "Cloudflare Computer：给 AI Agent 一台跑在 Durable Object 上的虚拟计算机"
date: 2026-08-12T03:23:25+08:00
slug: "cloudflare-computer"
github_repo: "cloudflare/computer"
source_key: "gh:cloudflare/computer"
description: "Cloudflare Computer 是一个运行在 Durable Object 内的虚拟文件系统，通过 FUSE 挂载、Worker 隔离沙箱和 JavaScript 动态 Worker 三种后端，为 AI Agent 提供可持久化的文件操作与代码执行环境。本文拆解其架构分层、同步协议与性能边界。"
draft: false
categories: ["技术笔记"]
tags: ["Cloudflare", "Durable Objects", "FUSE", "AI Agent", "虚拟文件系统"]
---

## 核心判断

Cloudflare Computer 解决的问题是：AI Agent 需要一个能持久化文件、执行代码、且不依赖外部服务器的"工作环境"。它的做法是把整个文件系统状态放进一个 Durable Object（DO）的 SQLite 存储里，再通过三种可插拔的后端把这个虚拟文件系统暴露给不同的执行环境。这不是又一个沙箱方案，而是把"文件系统即状态机"这一设计推到了 Cloudflare 边缘网络上。

截至本文写作时，项目处于 PREVIEW 阶段——API 不稳定，设计仍在迭代，不适合生产使用。但架构思路值得拆解。

## 系统地图

整个系统分三层：

| 层 | 组件 | 职责 |
|---|---|---|
| **状态层** | Durable Object + SQLite | 文件系统的唯一权威状态（authoritative state），所有写入最终落到这里 |
| **协议层** | capnweb RPC | 连接 DO 与沙箱内守护进程 `computerd` 的双向同步通道 |
| **执行层** | 三种后端 | Container（FUSE 挂载）、Isolate Shell（just-bash）、Isolate JavaScript（Dynamic Worker） |

数据流的方向是：调用方通过 `workspace.runtime.exec(source, { backend })` 发起执行请求 → 选定的后端接管 → Container 后端通过 `computerd` 把 SQLite 中的虚拟文件系统以 FUSE 形式挂载到沙箱容器里 → 沙箱内的操作通过 capnweb RPC 同步回 DO。

关键点在于：文件系统状态只有一份，住在 DO 的 SQLite 里。沙箱看到的是这份数据的投影，不是副本。

## 三种后端

### Container 后端

最重量级的后端。工作方式：

1. 在 Cloudflare Container（标准 Linux 沙箱）内启动 `computerd` 守护进程
2. `computerd` 通过 FUSE 把 DO 侧的虚拟文件系统挂载为 `/workspace`
3. 沙箱内获得完整的 Linux 用户态——真实二进制、真实网络
4. 写操作通过 capnweb RPC 同步回 DO

这意味着 Agent 可以在一个真实容器里运行 `git`、`pandoc`、`npm install` 等完整工具链，而文件状态由边缘 DO 持久化。

### Isolate Shell 后端

轻量级方案。在 Dynamic Worker 中运行 [just-bash](https://github.com/vercel-labs/just-bash)（一个用 JavaScript 实现的 bash 解释器），通过 Workers RPC 直接访问 DO 侧的 Workspace。没有容器、没有 FUSE、没有第二个存储——shell 操作直接映射到 DO 的 SQLite 文件系统上。

适合不需要完整 Linux 环境、只需要基本 shell 脚本能力的场景。

### Isolate JavaScript 后端

在 Dynamic Worker 中执行 ECMAScript 模块。支持结构化输入输出、持久化相对导入、配置化的库依赖、Workspace 支撑的 `node:fs/promises`，以及受信任的 `ws:git` 和 `ws:artifacts` 模块。

与 Isolate Shell 的区别是：后者跑 bash 命令，前者跑 JS 模块。两者共享同一个"无容器、无 FUSE"的轻量模型。

## 同步协议：文件系统如何保持一致

Container 后端的核心复杂度在于 FUSE 挂载与 DO 之间的双向同步。设计文档描述了一套基于 capnweb 的 RPC 协议：

- **FUSE 挂载默认启用**。`computerd` 检测 `/dev/fuse` 是否可用：在 Cloudflare Containers 上可用（内核 FUSE），在 `wrangler dev` 本地开发时不可用（降级为用户态 shim）。
- **写入的同步路径**：沙箱内的写操作 → FUSE 驱动标记为 dirty → 下一次 `exec()` 调用的 post-exec pull 把变更拉回 DO。也可以通过 `workspace.push()` / `workspace.pull()` 显式触发同步。
- **chunk 级去重**：写入时按 512 KiB 分块，每块做内容寻址（content-addressed）存入 blob store。DO 只需同步发生变化的 chunk，相同内容自动去重。

这个设计在 metadata 密集型操作上有优势（内存 inode store 比真磁盘快），但在大文件顺序 I/O 上有明显代价。

## 性能边界

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

所以不能从这些数字推出"computerd 整体比 ext4 慢"或"不适合跑重负载"。它适合的是以 metadata 操作为主、单文件小的场景（git 状态、模块解析、增量构建）；不适合的是单文件上百 MiB 的场景（视频、大模型权重、数据库 dump）。做取舍前，先想清楚自己工作负载里大文件顺序 I/O 占多少。

## 仓库结构

```
packages/
├── dofs/                    # @cloudflare/dofs — DO SQLite 虚拟文件系统 + 同步协议
├── rpc/                     # @cloudflare/computer-rpc — capnweb 线路类型 + 服务端/客户端
├── computerd/               # @cloudflare/computerd — 沙箱内 FUSE 挂载 + HTTP/WS RPC 守护进程
├── computer/                # @cloudflare/computer — 顶层包，DO 消费入口
└── computer-computerd-linux-x64/  # 预编译 Docker 镜像（非 npm 包）
```

`docs/` 目录包含 19 篇设计规范文档，从虚拟文件系统 schema 到同步协议、运行时接口、Git 集成、Assets 和 Artifacts 接口——这套文档是 forward-looking 的，描述的是目标形态而非当前代码实现的全部。

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

## 适用边界

**适合尝试**：

- AI Agent 需要持久化文件状态，且希望文件系统操作在边缘网络上完成
- 需要 Agent 在真实 Linux 环境中运行完整工具链（git、编译器、CLI 工具）
- 探索"文件系统即 Agent 工作目录"的编程范式

**当前限制**：

- PREVIEW 阶段，API 不稳定，设计可能变化
- 大文件 I/O 性能差距明显（对视频/大模型文件操作不友好）
- 需要在 Cloudflare 生态内使用（Durable Objects、Containers、Workers）
- 不接受非协作方的 unsolicited PR

## 采用建议

PREVIEW 阶段决定了它不适合现在就当场架生产链路，但架构思路值得先跟上：

- **想验证的团队**：用 `examples/tutorial` 跑通一次"挂载 → 执行 → 同步回 DO"的完整路径，重点看两个问题：你的工作负载是大文件还是 metadata 密集；换主/重启后文件状态是否真的不丢。这两个答案决定它和你业务合不合。
- **想在生产落地的团队**：等 API 稳定、版本出正式 release 再评估，同时盯住大文件 I/O 的优化方向——content-addressed chunk 的去重收益是否值得为顺序读写买单，是它能否从实验走向实用的关键。
- **仅做技术跟踪的团队**：把它当作 Cloudflare 在"Agent 原生文件系统"上的探路实验，与同类"给 Agent 一个工作目录"的方案放在一起观察，不必急着投入。

## 与同类方案的差异

这个项目与"给 Agent 一个 Docker"类方案的区别在于：状态不在容器里，而在 Durable Object 里。容器只是执行环境，可随时销毁重建，文件状态不丢。与"给 Agent 一个远程文件系统"类方案的区别在于：文件系统是 SQLite 中的虚拟实现，不是 NFS 或 SSHFS——这意味着可以做 chunk 级去重、内容寻址、与 DO 的强一致性。

这个定位目前没有直接竞品，更接近 Cloudflare 在 Workers 平台上探索"Agent 原生文件系统"的一次架构实验。

## 版本与仓库信息

- **仓库**：[cloudflare/computer](https://github.com/cloudflare/computer)
- **Stars**：7,567（截至 2026-08-11）
- **主要语言**：TypeScript
- **许可证**：MIT
- **最新版本**：@cloudflare/computer@0.2.0（2026-08-11）
- **活跃度**：数小时内有多条提交，处于活跃开发状态
