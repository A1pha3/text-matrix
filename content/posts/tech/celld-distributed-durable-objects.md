---
title: "celld：自托管、分布式 Durable Objects——没有控制平面也没有共识"
date: 2026-08-15T03:24:06+08:00
lastmod: 2026-09-28
slug: "celld-distributed-durable-objects"
github_repo: "denoland/celld"
source_key: "gh:denoland/celld"
description: "celld 是 Deno Land 开源的分布式 Durable Objects 守护进程，把 Cloudflare 的 Workers 平台搬到自己的机器上：对象所有权靠 bucket 上的条件写仲裁，写确认靠 follower fsync（RPO=0），bucket 只是慢一级的持久层。本文按 v0.6.0 拆解它的所有权、复制与恢复机制，并给出部署、运维与采用判断。"
draft: false
categories: ["技术笔记"]
tags: ["Deno", "Durable Objects", "分布式系统", "SQLite", "Rust"]
---

# celld：自托管、分布式 Durable Objects——没有控制平面也没有共识

**核心判断**：celld 最反直觉的地方在于它的架构取舍——一个分布式对象运行时，却不需要控制平面、成员协议、故障检测或共识服务。它把"对象所有权"这个分布式系统里最难的问题，交给对象存储上的条件写：bucket 只接受一个竞争者，同一时刻就只有一个节点拥有一个 cell。写入侧同样没有走"共享存储"的老路，而是 owner 把每个写推给一两个 follower 节点，fsync 落盘即向客户端确认，bucket 上传随后补上。代价是每对象一个 SQLite 数据库、升级常要停掉整个集群；换来的是极低的故障爆炸半径、接近为零的空闲成本，以及确认过的写不丢（RPO=0）。

## 为什么值得看

celld 是 Deno Land 开源的守护进程（Rust 实现，Apache-2.0），把 Cloudflare 的 Workers 平台搬到你自己的机器上。它跑的不只是 Workers 和 Durable Objects：KV、Queues、D1、R2、Workflows、Cron Triggers、静态资产各是一种绑定，其中 KV namespace、队列、D1 库、Workflow 本身就是一个 cell，享受和 Durable Objects 相同的租约、复制和故障切换（README "What runs on celld"，2026-09-28 取）。

每个 cell 是一个有名字的服务，带着自己的 SQLite 数据库，长期状态存进你拥有的 bucket——S3 兼容存储、Google Cloud Storage 或 Azure Blob 都行。节点之间靠签名的 peer HTTP 通信，bucket 只在需要仲裁所有权时出场，所以不需要控制平面，也不需要共识服务。

因为它把每个对象做成独立的小数据库，应用天然按对象分片（shard by construction）：共享数据库的争用和故障爆炸半径（blast-radius）被设计掉，而不是靠管理去规避。没有任何节点持有的 cell 处于非活动状态，成本几乎为零。

项目节奏很快：2026 年 8 月 5 日发 v0.1.0，9 月 26 日发 v0.6.0，七周六个 minor 版本，官方文档明说 v0.6.0 是 beta。当前约 4.8k star（2026-09-28 取）。

## 系统地图

```text
celld 节点 ×N（每台机器一个进程，内嵌 V8，执行 Wrangler 产物）
      │
      │  peer HTTP（签名，内网 8081）：请求路由 + 复制日志传输
      ▼
写确认（RPO=0）：owner 把每个写发给 1–2 个 follower，
follower fsync 落盘即持久，bucket 上传随后完成
      │
      ▼
┌───────────────────────────────────────────┐
│ 共享 bucket（S3 兼容 / GCS / Azure Blob）    │
│  部署包 / cell 状态（LTX）/ 所有权记录 / lease │
└───────────────────────────────────────────┘
      │  条件写仲裁所有权：同一时刻恰好一个 owner
      ▼
节点宕机 → lease 过期自我 fence → 新节点 CAS 接管，
按 epoch 链从 bucket 与 follower 磁盘重建数据库
```

共享同一个 bucket 的一组节点就是一个 fleet。bucket 是唯一把节点绑在一起的东西：部署包、cell 状态（LTX 格式，一种为 SQLite 设计的复制日志）、所有权记录全在里面，节点坏了换一台就能接上。

## 关键机制

### 对象即数据库

每个 cell 对应一个 SQLite 数据库，应用的数据天然按对象隔离，一个对象崩溃不会波及其他对象。这是"按构造分片"的来源——不需要一个集中式数据库再去做分区。

成本模型也站得住。v0.2.0 起驻留 cell 共享 isolate 池，官方测量单个驻留 cell 约 471 KB（v0.1.0 是 3.4 MB），单机线性测到 2,500 个驻留 cell 约 1.2 GB。每个 isolate 另有 128 MB 的 V8 堆上限，与 Cloudflare 上 Durable Objects 的限制一致；按这个默认值，一个 cell 大约能挂 5 万个可休眠 WebSocket 客户端，堆给到 512 MB 能撑到约 10 万。

### 用条件写替代共识

"一个 cell 只能有一个 owner"这个保证，靠 bucket 上的所有权记录完成：没有记录时用条件创建抢，有记录时用比较-交换（CAS）抢，bucket 只接受一个竞争者，两个节点就抢不到同一个 cell。

光抢到还不够，还得防住失权节点继续乱写。celld 的做法是给每次激活一个递增的 fencing epoch，复制数据全部写进 `cells/<cell>/ltx/e<epoch>/` 这样的前缀。丢掉所有权的节点就算还在写，也只写进被取代的旧前缀，恢复时只会选中当前血脉。

节点自身也有一条自我了断的规则：每个节点在 bucket 里持有 lease（默认 10 秒，过 1/3 续一次），续不上就等已发布的过期时间一到自我 fence——停掉所有活跃 cell，未完成的请求全部失败，日志打 `SELF-FENCE:` 前缀、退出码 3。fence 是终态，只有重启才能回队。所以 celld 必须跑在会重启进程的 supervisor 下面（systemd、Docker restart 策略、Kubernetes 都行），否则一台 fence 掉的节点就白丢了。

### 写入确认：RPO=0 的两条证明路径

celld 承诺"确认过的写不会丢"，做法是在确认之前先拿到持久性证明，证明有两条路：

- **fleet proof**（默认，`CELLD_DURABILITY=fleet`）：owner 把每个提交的 SQLite 写捕获成 LTX 复制格式，发给一两个 follower 节点，所有 follower fsync 落盘，写就算持久。bucket 上传随后补上（write-behind）。三个以上节点的 fleet 持有三份已确认的写，丢一个 follower 不用退回 bucket。
- **bucket proof**：单节点没有 follower 可发，每个写都要等对象存储一个往返才确认，慢得多。

两条路的可靠性并不对等——bucket proof 之后 celld 还会复查一次所有权记录，确认自己仍是当前 epoch 的 owner 才向客户端确认；分区中的节点就算本地提交成功，也会在这次复查里被拦下。fleet proof 不需要这次复查，因为接管会先封存旧节点的日志会话（后述）。

输出门（output gate）把这条规则罩到所有出口：HTTP 响应、流式响应的每个 chunk、出站 WebSocket 帧、Queue 投递、R2 变更，都要等它们可能暴露的写拿到证明才放行。客户端拿不到一个"崩溃后会消失"的值。

性能差异是实打实的。官方给的单写参考：region-local 的 bucket 约 90 ms；一个负载中的实验集群对非本地区域的 bucket 测到约 600 ms，第二个节点开始承接写之后降到约 25 ms。v0.3.0 引入这套 write-behind 日志时给的数据是写延迟降 10 倍、Class A S3 操作少 100 倍。结论很简单：在乎写延迟就跑两个以上节点，加节点零配置——节点通过 bucket 找到彼此。

### 换主：bucket 是真相源，恢复有门卫

节点只是可替换的执行工位。接管（takeover）不是简单地把数据库文件拉回来：新 owner 激活时先查旧 owner 的节点日志记录——记录还开着，说明旧会话可能有已确认但尚未落到 bucket 的写，必须先跑恢复（封存旧会话、从 follower 收齐尾部、补传 bucket），然后才按 epoch 链重建 SQLite 数据库继续跑。大 cell 还有按页恢复：先把请求跑起来，数据库页在首次触碰时才从 bucket 读，后台再补齐（小于 `CELLD_LTX_PAGED_MIN_MB` 的照旧整库下载）。

这套"确认过的写不丢、没确认的不算数"的边界是明确的：接管精确钉住恢复点，被 fence 的旧 owner 之后的写进不了当前血脉，cell 的历史不会分叉。

## 一个 cell 的一生

把上面四个机制串起来，看一个 cell 从创建到换主的完整过程：

1. `celld deploy . --bucket s3://my-cells-bucket` 把 esbuild 打包好的 Worker 直接写成 bucket 里的部署对象。没有账号服务或加入服务，fleet 里每个节点都从 bucket 读最新部署。
2. 首个请求落到某个节点，它对 cell 的所有权记录做条件创建或 CAS，抢到即成为 owner，epoch 推进，本地建 SQLite 库开跑。
3. 运行期间每次提交都被捕获为 LTX 段：owner 发给 follower，follower fsync 后响应对外放行，bucket 上传在后台完成。此时 bucket 里已有部署包和不断增长的 cell 状态。
4. 这台节点宕机。lease 无人续租，过期时间一到它自我 fence（若进程还活着）；其他节点把它的 lease 读成死，对同一个 cell 的所有权记录发起 CAS。
5. 新 owner 赢得 CAS，先封存旧会话、收齐 follower 磁盘上的日志尾部，再按 epoch 链重建数据库，从旧 owner 已确认的进度继续。客户端视角，凡是拿到过响应的写都还在。

## 快速上手

零依赖跑起来只要一条命令，本地开发不需要 Docker 也不需要云 bucket：

```bash
celld dev
```

`celld dev` 起一个带本地对象存储的节点，Worker 监听 `http://127.0.0.1:9876`，状态存 `.celld/dev`，改代码自动重建，`--clean` 清空重来。

正式安装：

```bash
curl -fsSL https://celld.dev/install.sh | sh
```

安装器提供 Linux x86-64、Linux ARM64 和 Apple Silicon 的二进制（可用 `gh attestation verify` 验证来源），不支持 Windows。`celld deploy` 需要 `esbuild` 在 PATH 上；纯静态资产项目不需要。

部署到 bucket，然后启动 celld 指向同一个 bucket：

```bash
celld deploy . \
  --bucket s3://my-cells-bucket

celld \
  --bucket s3://my-cells-bucket \
  --listen 0.0.0.0:8080 \
  --internal-listen 10.0.0.12:8081 \
  --advertise 10.0.0.12:8081
```

8080 对外交给负载均衡器，8081 是内部 listener（peer 流量和运维 API），必须留在私有网络或 WireGuard/Tailscale 这类加密 overlay 里。`--endpoint` 指定其它 S3 兼容服务，`--region` 指定区域；`gs://` 前缀选 Google Cloud Storage，`az://` 选 Azure Blob。celld 使用标准的 AWS 凭证链。第二个节点用同样的命令指向同一个 bucket 即可，无需额外配置。

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

无论哪种方式，都要把进程交给会重启的 supervisor——自我 fence 后进程会退出，没有重启策略的部署在故障后会一直缺一台节点。

## 运维与排查

排查入口是 `celld diagnose`：枚举每个节点的 lease 并对存活 peer 做签名直探，区分过期记录、不安全的 advertise 地址、不可达 peer 和协议不兼容；同时向 bucket 发四个条件写做存储自检（两个必须失败，否则这个 bucket 根本无法 fencing，celld 会直接报错退出）。每个节点启动时也会跑同样的存储测试，无法禁用。

```bash
celld diagnose --bucket s3://my-cells-bucket
celld cell list --bucket s3://my-cells-bucket
```

数据面也有对应命令：`celld d1` 跑 SQL 和迁移，`celld kv` 读写 KV（bulk 命令兼容 Wrangler 导出格式），`celld r2` 直读 bucket 上的对象（不需要节点在跑），`celld queue` 查看、暂停、恢复队列投递。

资源上的主要旋钮：`CELLD_MAX_RESIDENT_CELLS` 限制单节点驻留 cell 数；`CELLD_MAX_RSS_MB` 控制内存压力（默认在可用内存 80% 时开始逐出最久未用的空闲 cell，95% 有硬上限兜底）；`CELLD_IDLE_EVICT_S` 决定空闲 cell 多久休眠。负载均衡每 5 秒采一次全 fleet 样本，最重的节点每次最多交出 32 个休眠 cell 给最闲的 peer（驻留 cell 要等空闲逐出后才移动），`CELLD_PLACEMENT_WEIGHT` 调节点权重，`CELLD_REBALANCE_INTERVAL_MS=0` 关闭均衡。`/state` 路由报告各节点的内存与 cell 明细。

## 适用边界

- **适合**：想自托管 Workers 平台、需要按对象分片隔离、愿意接受"对象即数据库"模型的应用。
- **成熟度**：官方文档明说 v0.6.0 是 beta；一个 fleet 只跑一个应用，没有多租户调度和托管 ingress。
- **网络**：celld 不终止 TLS，公开流量在入口代理上终结；peer 流量是明文 HTTP，靠 fleet HMAC 认证、不加密，保密性由内网或 overlay 负责。bucket 凭证等同于 fleet 管理员权限，只给一个 fleet 用。
- **存储选型**：已验证的 bucket 是 Amazon S3、Cloudflare R2、Tigris、Google Cloud Storage、Azure Blob。Backblaze B2、Hetzner、DigitalOcean Spaces 不支持所需的条件写，celld 在这些存储上不正确；MinIO 社区版通过测试但未获生产认证。
- **客户端语义**：出站 Durable Object WebSocket 会让 cell 保持驻留，cell 迁移时连接断开，应用要自己保存连接意图并重连。
- **升级**：跨版本常要求先停整个 fleet（v0.5.0 相对 v0.4.1、v0.6.0 在 fleet 持久模式下相对 v0.5.1 都如此），滚动更新只在部分相邻版本间可用。

## 采用建议

这套取舍并不适合所有人，先分清自己属于哪类使用者：

- **现在就能玩**：`celld dev` 十分钟能验证"边缘对象 + 按对象分片"是否合手。bucket 是真相源意味着退出代价低——停掉节点，数据还在 bucket 里，而且是 LTX 格式（Litestream v0.5.16 可直接读），没有私有格式锁定。
- **生产要等**：对可用性有严格 SLA、需要成熟故障切换语义的服务。beta 状态、停队升级、恢复路径的边角（follower 日志尾部缺失会阻塞恢复）都需要自己验证。官方也在 limitations 页列出了运行限制，公开部署前值得逐条过。
- **值得对比**：已经深度绑定 Cloudflare 网络的团队不必迁移——celld 明确把需要 Cloudflare 网络、GPU 或浏览器集群的场景划出范围。它的独特位置是"同一个 Workers 对象模型，跑在你拥有的 bucket 之上"，数据主权和自托管合规是它真正的卖点。

## 进一步阅读

- 官网与文档：<https://celld.dev> ・ <https://celld.dev/docs>
- 完整协议与保证：<https://github.com/denoland/celld/blob/main/docs/guarantees.md>
- 运行限制：<https://github.com/denoland/celld/blob/main/docs/limitations.md>
- Cloudflare 兼容性清单：<https://github.com/denoland/celld/blob/main/docs/cloudflare-compat.md>
