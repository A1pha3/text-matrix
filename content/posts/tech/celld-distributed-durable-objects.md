---
title: "celld：自托管、分布式 Durable Objects——没有控制平面也没有共识"
date: 2026-08-15T03:24:06+08:00
slug: "celld-distributed-durable-objects"
github_repo: "denoland/celld"
source_key: "gh:denoland/celld"
description: "celld 是 Deno 团队开源的分布式 Durable Objects 守护进程，让 Cloudflare Workers 与 Durable Objects 跑在你自己的机器上。每个对象即一个 SQLite 数据库，节点只通过一个你拥有的 bucket 协调，无控制平面、无共识协议。"
draft: false
categories: ["技术笔记"]
tags: ["Deno", "Durable Objects", "分布式系统", "SQLite", "Rust"]
---

# celld：自托管、分布式 Durable Objects——没有控制平面也没有共识

**核心判断**：celld 最反直觉的地方在于它的架构取舍——一个分布式对象运行时，却不需要控制平面、成员协议、故障检测或共识服务。它把"对象所有权"这个分布式系统里最难的问题，用"对象存储上的 compare-and-swap"这样一个原子操作解决掉了。代价是每对象一个 SQLite 数据库、按对象分片，换来的是极低的 blast-radius 和近乎为零的空闲成本。

## 为什么值得看

celld 是 Deno 团队开源的守护进程，让你在自己的机器上运行 Cloudflare Workers 和 Durable Objects。每个对象就是它自己的 SQLite 数据库。对象按名字寻址，并复制到你拥有的 bucket（兼容 S3 或 Google Cloud Storage）里。节点之间只通过这个 bucket 协调——没有控制平面，没有共识。

因为它把每个对象做成独立的小数据库，应用天然按对象分片（shard by construction）：共享数据库的争用和故障爆炸半径（blast-radius）被设计掉，而不是靠管理去规避。一个没有任何节点持有的 cell 处于非活动状态，非活动 cell 的成本几乎为零。

当前约 3.5k star（Rust 实现，Apache-2.0，主页 celld.dev）。

## 系统地图

```
每个 celld 节点内嵌 V8，执行 Wrangler bundles
      │
      ▼
┌─────────────────────────────────────────┐
│ 共享 bucket（S3 兼容 / GCS）             │
│  部署包 / cell 状态 / 小型所有权记录     │
└─────────────────────────────────────────┘
      │  compare-and-swap（对象存储 CAS）
      ▼
同一时刻恰好一个节点拥有一个 cell（无需成员协议/共识）
      │
      ▼
celld 持续把每个 cell 的 SQLite 数据库复制到 bucket
      │  cell 迁移 / 非活动 cell 激活时，新 owner 恢复数据库并续跑
      ▼
bucket 是持久真相源，节点可替换
```

## 关键机制

### 对象即数据库

每个对象对应一个 SQLite 数据库。应用的数据天然按对象隔离，一个对象崩溃不会波及其他对象。这是"按构造分片"的来源——不需要一个集中式数据库再去做分区。

### 用对象存储 CAS 替代共识

"一个 cell 只能有一个 owner"这个保证，靠 bucket 上的 compare-and-swap 完成。对象存储的原子比较-交换保证了同一时刻只有一个节点能抢到某 cell 的所有权，于是不需要成员协议、故障检测器或共识服务。这大幅简化了系统的运维心智。

### bucket 是唯一真相源

celld 持续把每个 cell 的 SQLite 数据库复制到 bucket。当 cell 迁移，或非活动 cell 被激活时，新 owner 从 bucket 恢复数据库并续跑。节点是可替换的——任何节点都能从 bucket 把对象"捡起来"继续跑。bucket 就是持久真相源（source of truth）。

这个复制走的是"备份 + 恢复"的思路：owner 负责把活跃 cell 的数据库状态推到 bucket，节点崩溃或 cell 换主后，新 owner 从 bucket 重建数据库。因为状态在一边只写、在另一边只读，两侧不会在同一时刻写同一份数据，这绕开了共享文件系统最麻烦的并发一致性问题——celld 不需要解决"两个节点同时写一个文件"的冲突，因为冲突场景在设计上就不存在。

## 一个任务如何流过系统

把"所有权 + 真相源"这两个机制拼起来，看一次 cell 从创建到换主的过程：

1. 客户端调用 `celld deploy`，把 Workers 包上传到 bucket。
2. 某个空闲节点执行 CAS，抢到 cell 的所有权，在本地建一个空 SQLite 库开始执行。
3. 运行期间，owner 把数据库快照定时推回 bucket。此时 bucket 里已有部署包和最新的 cell 状态。
4. 这台节点下线，或负载均衡把请求引到另一台节点。新节点对同一个 cell 发起 CAS，旧的 owner 因心跳丢失自动让位。
5. 新 owner 从 bucket 拉取最新快照，在本地重建 SQLite 库，接着旧 owner 的进度继续跑。

关键在最后一步：新 owner 恢复的不是"冷启动"，而是旧 owner 上一次落盘的状态。只要快照足够新，换主对上层几乎是透明的。这也是为什么 bucket 被称为真相源——节点只是一次性的执行工位，数据从来不在节点上独存。

## 快速上手

安装：

```bash
curl -fsSL https://celld.dev/install.sh | sh
```

部署到 S3 兼容 bucket，然后启动 celld 指向同一个 bucket：

```bash
celld deploy . \
  --bucket s3://my-cells-bucket

celld \
  --bucket s3://my-cells-bucket \
  --listen 0.0.0.0:8080 \
  --internal-listen 10.0.0.12:8081 \
  --advertise 10.0.0.12:8081
```

用 `--endpoint` 指定其它 S3 兼容服务，`--region` 指定区域。celld 使用标准的 AWS 凭证链。

容器方式（Linux x86-64 / ARM64 镜像）：

```bash
docker run --rm ghcr.io/denoland/celld --version
```

持久化运行时本地状态并传入 AWS 凭证环境：

```bash
docker volume create celld-state
docker run --rm --network host \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
  -e CELLD_WATCH=/var/lib/celld/state \
  -v celld-state:/var/lib/celld \
  ghcr.io/denoland/celld \
  --bucket s3://my-cells-bucket \
  --endpoint https://ACCOUNT.r2.cloudflarestorage.com \
  --region auto \
  --listen 0.0.0.0:8080 \
  --internal-listen 10.0.0.12:8081 \
  --advertise node-a.internal:8081
```

对外暴露 8080 给负载均衡器，8081 保持在私有网络内。

## 适用边界

- **适合**：想自托管 Durable Objects / Workers、需要按对象分片隔离、愿意接受"对象即数据库"模型的应用。
- **边界**：当前版本节奏较快（刚发布 v0.2.x），属于早期项目；生产环境需自行评估稳定性。
- **依赖**：`celld deploy` 需要 `esbuild` 在 PATH 上；纯资源型项目不需要。

## 采用建议

这套取舍并不适合所有人，先分清自己属于哪类使用者：

- **可以先上**：正在做原型、想验证"边缘对象 + 按对象分片"是否适合自己的团队。bucket 是真相源意味着哪天不想要了，停掉节点、数据还在 bucket 里，退出的代价低。
- **应该等**：对可用性有严格 SLA、需要事故后审计、或依赖成熟故障切换语义的生产服务。v0.2.x 的稳定性要靠自己验证，CAS 抢主的竞态细节也需要在实践中观察。
- **值得对比**：如果你已经深度绑定某个云厂商的 Durable Objects，celld 的价值不在替代，而在"同一个对象模型能否跑在自有的 bucket 之上"——这是它在生态里最独特的位置。

## 进一步阅读

- 官网与文档：<https://celld.dev>
- 文档：<https://celld.dev/docs>
