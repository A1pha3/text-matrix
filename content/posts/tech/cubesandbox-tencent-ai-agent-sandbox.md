---
title: "CubeSandbox 拆解：60ms 冷启动不是把开机做快了，而是把启动、隔离和出网拆成三条链路"
date: "2026-04-23T07:58:00+08:00"
lastmod: "2026-09-19T00:00:00+08:00"
slug: "cubesandbox-tencent-ai-agent-sandbox"
github_repo: "TencentCloud/CubeSandbox"
source_key: "gh:TencentCloud/CubeSandbox"
description: "按 v0.7.1 的仓库与代码拆解腾讯开源的 AI Agent 沙箱 CubeSandbox：模板快照与 XFS reflink 如何省掉开机开销、逃逸面从共享内核换到 VMM 边界之后剩什么、CubeVS 三个 TC 程序与双 Map 会话跟踪的真实处理顺序、CubeEgress 的 L7 裁决、裸金属实测数据的口径边界，以及部署硬前置与三类对得上日志的故障。"
draft: false
categories: ["技术笔记"]
tags: ["沙箱", "AI Agent", "eBPF", "Rust", "KVM"]
author: text-matrix
---

Agent（智能体）要执行大模型现写的代码，这件事本身没有安全的做法：共享内核的容器有逃逸面，独立内核的虚拟机启动太慢、单实例太贵。CubeSandbox 的处理方式不是在这两端找一个折中点，而是把"启动有多快、隔离有多强、出网管多细"拆成三条互不牵制的链路，各自往下压。

拆开看，三条链路各有落点：启动靠模板快照恢复加 Copy-on-Write（写时复制）克隆，绕开整个引导过程；隔离靠 KVM MicroVM（轻量虚拟机）给每个沙箱一颗独立内核，VMM（虚拟机监视器）侧再用 seccomp 收窄系统调用面；出网靠 eBPF 在内核态做完 L3/L4 裁决，再把需要看内容的流量交给一个宿主上的 L7 代理。

这份拆解对着 v0.7.1 的仓库做：架构与网络文档、`CubeNet` 下的 BPF 源码与 Go 控制面、一键安装与排障文档、裸金属性能报告。核对日期 2026-09-19，仓库最后一次提交是 2026-09-18。文中每个数字都标了测法和出处；文档与代码、文档与文档对不上的几处单独写出来，不替项目方打圆场。

## 先分清三条主线

仓库根目录有 26 个一级目录，去掉 `docs/`、`deploy/`、`examples/`、`sdk/`、`tests/` 这类支撑目录，剩下十四个组件本体。第一次读容易把它们当成一条从 API（应用程序接口）到 VM 的直线，其实是三组：

| 主线 | 组件 | 语言 / 载体 | 职责 |
| --- | --- | --- | --- |
| 控制面 | CubeAPI | Rust（Axum） | 兼容 E2B 的 REST 网关，把 SDK 调用翻成内部 gRPC |
| 控制面 | CubeMaster | Go | 集群编排调度，选节点、下发请求；本身无状态 |
| 控制面 | CubeOps | Go | 节点纳管、隔离/解除隔离（v0.7 从 CubeMaster 拆出，HTTP 端口 `3010`） |
| 控制面 | CubeTemplateCenter | Go | 模板构建与回收（v0.7.1 拆为独立服务，产物落 S3/MinIO） |
| 启动链路 | Cubelet | Go | 节点本地生命周期调度，内置 network runtime |
| 启动链路 | CubeShim | Rust | containerd Shim v2 实现，二进制名 `containerd-shim-cube-rs` |
| 启动链路 | CubeHypervisor | Rust（RustVMM + KVM） | MicroVM 的 vCPU、内存、virtio 设备与快照恢复 |
| 启动链路 | CubeCoW | Rust | `FICLONE` ioctl 之上的 O(1) 卷快照与克隆 |
| 出网链路 | CubeVS | eBPF + Go | 内核态 NAT、会话跟踪、L3/L4 策略、DNS 学习 |
| 出网链路 | CubeEgress | OpenResty + Lua | L7 透明代理：域名过滤、凭证注入、审计 |
| 出网链路 | CubeProxy | OpenResty + Lua | 入站反向代理，把外部请求路由回沙箱端口 |

三个容易记错的点：

- **CubeProxy 不是 Rust。** 架构文档与 README 的组件表只写"反向代理"，但 `CubeProxy/lua/` 下是 15 个 Lua 文件（连测试共 20 个）加一份 nginx 配置模板，整个目录没有一行 Rust。写 Rust 的是 CubeAPI。
- **控制面之间没有 etcd。** Redis 是沙箱元数据、生命周期事件流、CubeProxy 路由表和自动暂停协调所需分布式锁的存放处；MySQL 收持久化状态。两者的分工在 `CubeMaster/pkg/templatecenter/job_pull_progress.go` 的注释里写得很直白：高频回调进 Redis 作为 live snapshot，MySQL 只留 durable terminal snapshot。任何 CubeAPI / CubeMaster 实例都能处理任何请求，这是"无状态控制面"这句话的具体含义。
- **节点管理不在 CubeMaster 里。** v0.7.0 把节点管理拆成 CubeOps，配套 `cubeopscli`；v0.7.1 又把模板构建拆成 CubeTemplateCenter，目的是让 CubeMaster 可以多副本。

## 一次 `Sandbox.create()` 走过的路

抽象机制放在一次调用里最好读。客户端用 E2B SDK 发 `POST /sandboxes`，之后发生的事：

1. CubeAPI 收下请求，转成 gRPC 交给 CubeMaster。
2. CubeMaster 按资源可用性选出目标节点，把 `RunCubeSandbox` 发给那台机器上的 Cubelet。
3. Cubelet 用 CubeCoW 从模板克隆 rootfs 与内存卷——一次 `FICLONE`，只登记元数据，不搬字节。
4. Cubelet 通过 containerd 的 Shim v2 接口让 CubeShim `Create` + `Start`。
5. CubeShim 调 CubeHypervisor：`launch_vmm()` → `create_vm()` → `restore_vm()`。最后一步是从模板的内存快照恢复，不是引导内核。
6. VM 起来后，Cubelet 的 network runtime 执行 `AddTAPDevice()` 写入沙箱元数据与策略，再 `AttachFilter()` 在这块 TAP 上挂 `from_cube`。
7. 生命周期事件发布到 Redis，CubeAPI 返回 `201 { sandbox_id, ... }`。

第 3 步和第 5 步贡献了绝大部分启动收益，第 6 步说明网络不在这条关键路径上——TAP 池在沙箱创建之前就已预建好。

## 60ms 是从哪几处省下来的

一次 MicroVM 交付的时间只会花在四处：引导内核、初始化语言运行时、准备文件系统、建立网络。逐项对应的处理是：

| 开销来源 | 处理方式 | 关键参数 |
| --- | --- | --- |
| 引导内核、初始化运行时 | 模板阶段已经完整跑过一遍启动，冻结成内存快照，创建时直接 `restore_vm()` | 探针端口与路径 |
| 准备文件系统 | 模板 rootfs 只读，沙箱可写层用 XFS reflink 克隆，不拷数据 | `--writable-layer-size` |
| 建立网络 | Cubelet 预建 TAP 池，创建时从池里取一块挂过滤器 | `tap_init_num`（默认 500） |

内存那一头是同一套机制的另一面：CoW 让 2 GiB 规格的沙箱在空载时并不预占 2 GiB，页要等到第一次写入才分配。README 给这条口径加了限定——基于 ≤ 32 GB 规格沙箱实测，更大规格下开销会略有上升，但幅度极小。

### 探针决定快照落在哪一刻

模板不是 Dockerfile 的产物，而是"一个跑到某个时刻的 VM 的影子"。所以真正要理解的是那个"某个时刻"怎么定。

CubeSandbox 拉取 OCI 镜像后，用它在临时 MicroVM 里正常启动，然后持续 `GET http://<sandbox>:<probe-port><probe-path>`，**直到返回 HTTP 2xx 才冻结文件系统和内存**。因此创建模板必须给三样东西：

```bash
--expose-port 49983 --probe 49983 --probe-path /health
```

`49983` 是 `envd` 的端口。`envd` 是预装在基础镜像里的后台服务，SDK 的"执行命令""读写文件""打开终端"最终都打到它身上；它的 `/health` 在能接请求时返回 204。上面这行配置的含义是：等 `envd` 活了再落快照。

探针选得早有代价（应用还在初始化就被写进快照），选晚了模板构建直接超时。平台还有一层随之而来的就绪语义：**由该模板创建的运行中沙箱，被探测的那个端口在 `create` 返回时就可用**，`resume` 和自动恢复起来也一样，客户端不用再等或者重试。两个例外要记住——只 `--expose-port` 而没被探测的端口不在这个保证内；被探测端口上的服务自己崩了也不在。

完整的一条建模板命令，用的是官方预置的代码解释器镜像：

```bash
cubemastercli tpl create-from-image \
  --image cube-sandbox-cn.tencentcloudcr.com/cube-sandbox/sandbox-code:latest \
  --writable-layer-size 1G \
  --expose-port 49999 \
  --expose-port 49983 \
  --probe 49999

cubemastercli tpl watch --job-id <job_id>
```

镜像仓库分国内（`cube-sandbox-cn`）和境外（`cube-sandbox-int`）两个前缀，目前只有 `sandbox-code:latest` 发布成 Multi-Arch 镜像，同时覆盖 x86_64 与 aarch64。等状态变 `READY`，记下 `template_id`。`cubemastercli` 走 CubeMaster 的 HTTP API（默认端口 `8089`），另两个常用子命令是 `tpl ls` 和 `tpl info <template-id>`（后者能看到模板在各节点上的副本状态）。

模板做出来之后还有两个运维动作，区别值得记：`tpl merge` 把留在 CubeMaster 本地盘上的历史 artifact 迁入托管存储（对应 `/cube/template/migrate`），`tpl redo` 让指定节点重新分发或重建。先 merge 后 redo，前者收敛存储、后者覆盖节点。

## 隔离这条线：把逃逸面从内核换成 VMM

共享内核的方案之所以在"跑别人写的代码"这件事上一直不踏实，是因为容器和宿主机之间只有一层命名空间与 cgroup 的软边界。Dirty COW、Dirty Pipe 这类内核本地提权，或者 runc 的权限问题，一旦命中，同一台机器上的所有容器就都在影响范围内。CubeSandbox 的解法直接：每个沙箱一颗独立的 Linux 内核，跑在自己的 KVM MicroVM 里。架构文档里那句"不存在共享内核的逃逸面"就是这个意思。

README 那张对比表把三方的差异摆得很清楚：Docker 是低隔离（共享内核 Namespaces）、200 ms 启动、内存低；传统 VM 是高隔离但秒级启动、内存高；CubeSandbox 走独立内核加 eBPF 网络隔离，启动一栏写"毫秒级（< 60ms）"，内存一栏写"极限裁剪（< 5MB）"。后一句的口径要等到读实测报告才看得清，这里先记住它是"自身额外开销"。

但"独立内核"不等于没有攻击面，只是把它换了位置：guest 到 host 的路径现在要经过 virtio 设备、vsock 和 VMM 本身。CubeHypervisor 因此做了 seccomp 加固，把可用的系统调用收窄成白名单。架构文档把安全设计列成六层，各自拦的是不同的事：

| 层 | 拦什么 | 由谁做 |
| --- | --- | --- |
| 硬件隔离 | 靠共享内核软边界挡住的逃逸 | CubeHypervisor + KVM |
| 网络隔离 | 沙箱访问内网或其他沙箱 | CubeVS 默认拒绝私有与链路本地段 |
| 出网控制 | 沙箱访问任意外部地址 | CubeEgress 域名白名单 |
| 凭据保险库 | 密钥进入沙箱或模型上下文 | CubeEgress 改写请求头注入 |
| Seccomp | VMM 可用的系统调用 | CubeHypervisor 白名单 |
| 鉴权 | 谁能调 API | CubeAPI 可插拔鉴权回调 |

六层里有三层要运维自己打开。凭证注入得先配规则；网络加固见官方指南；最要紧的是最后一层——Cube API Server 默认不启用鉴权，所有请求直接放通，要接自己的服务得显式给一个 `--auth-callback-url`（或 `AUTH_CALLBACK_URL`），回调返回 200 才放行，其他状态码一律 401。这解释了本地部署为什么可以随便填 `E2B_API_KEY`。

这套隔离有两个边界需要说清（下面两句是我的推论，不是项目方的表述）。一是它保护的是宿主机和别的沙箱，不保护 guest 内部：代码一旦进入自己的 MicroVM，里头的文件、进程和网络对它完全透明。二是隔离强度最终取决于宿主内核、KVM 和 VMM 三者都没有可被利用的缺陷，seccomp 是在缩小这个面，不是取消它。

## CubeVS：三个 TC 程序、一张会话表、两类策略

CubeVS 是这套东西里最有读相的子系统——它用三个挂在 TC（流量控制钩子）上的 eBPF 程序替掉了 Linux Bridge、OVS 和 iptables NAT（网络地址转换）的整套软件交换栈。挂载点分别是：

| 程序 | 源文件 | 挂载点 | 方向 | 做什么 |
| --- | --- | --- | --- | --- |
| `from_cube` | `mvmtap.bpf.c` | 每块 TAP 的 TC ingress | 沙箱 → 宿主机 | 策略检查、DNS 拦截、SNAT、会话创建、ARP 代理 |
| `from_world` | `nodenic.bpf.c` | 宿主机网卡的 TC ingress | 外部 → 宿主机 | 会话反向 NAT、端口映射、DNS 响应学习 |
| `from_envoy` | `localgw.bpf.c` | `cube-dev` 的 TC egress | 宿主机 → 沙箱 | L7 代理回包与宿主机探测的 DNAT |

一个早期版本的差异值得单独提：v0.1.0 到 v0.2.2 的网络文档里有第四个程序 `filter_from_cube`，用 XDP 挂在 `cube-dev` 上做入站早拒；v0.3.0 的文档开始不再提到它。当前 master 的 `CubeNet/src` 与 `CubeNet/cubevs` 下 grep 不到 `xdp`（只有生成的 `vmlinux.h` 里还带着内核枚举），数据面文件就是上表这三个，另有 `dns_learn_test.bpf.c`、`tcp_state_test.bpf.c` 之类测试程序。照旧文档去找那个 XDP 过滤器会落空。

### 程序之间靠固定的 Map 共享状态

`CubeNet/src/map.h` 里一共 16 个 Map 定义，13 个按名固定到 `/sys/fs/bpf/`，剩下 3 个（`dns_query_scratch`、`dns_query_state`、`dns_response_state`）是 PERCPU 暂存，配合 `dns_tail_calls` 这个 PROG_ARRAY 完成 DNS 报文的分片尾调用解析。文档把固定的那些按功能归成六组：

| 分组 | Map | 内容 |
| --- | --- | --- |
| 设备注册表 | `mvmip_to_ifindex`、`ifindex_to_mvmmeta` | 沙箱 IP ↔ TAP ifindex ↔ 元数据 |
| NAT 会话 | `egress_sessions`、`ingress_sessions` | 双向五元组 |
| SNAT 池 | `snat_iplist` | SNAT IP 与各自的源端口水位线 |
| 端口映射 | `remote_port_mapping`、`local_port_mapping` | 宿主端口 ↔（TAP ifindex，沙箱监听端口） |
| L3/L4 策略 | `allow_out_v3`、`deny_out` | 每沙箱的 CIDR 允许 / 拒绝表 |
| 域名策略 | `dns_allow_v2`、`dns_query_track` | 每沙箱域名规则与待响应查询 |

三个策略 Map 都是 Hash-of-Maps，内层 LPM Trie 就地声明，所以改一个沙箱的规则不会碰别人的表。表格里没列的还有一个 `direct_neigh`：一张 LRU Hash，存最近一次 `bpf_fib_lookup()` 的结果（MAC 加 `valid_until`、`fib_ok`、最后使用时间）。数据面只负责写这些字段，并且解析不出邻居时也照样转发（退回网关 MAC）；GC、学习触发和 keepalive 的调度全在用户态扫描器里，陈旧窗口的上限是一个 `CACHE_TTL`。

这里有个必须留神的地方：`network.md` 通篇写 `allow_out_v2`，数据面用的却是 `allow_out_v3`。`cubevs/migration.go` 的注释交代了全过程——启动时做一次单向迁移，把旧表内容展开成新格式，两张 legacy 表都复制成功之后才解除旧 pin，中途失败就留着旧 pin 等下次重启重试；当前的数据面和用户态只读 `allow_out_v3` 与 `dns_allow_v2`。注意别只凭"`bpftool` 里还能看到 `allow_out_v2`"就断定迁移失败：解除旧 pin 是 best-effort 的，成功之后也可能留一根下来，下次重启会幂等地再迁一遍。

有一类损失倒是可以从日志里直接读出来：v3 的 LPM key 是 `/48`，只能表达精确的 (IP, 端口) 对，表达不了"子网 + 端口"这种组合。所以带 `L7_REQUIRED` 标记且前缀短于 /32 的旧规则会被丢弃并留下一行 `dropping unsupported L7 subnet rule`，提示改成 /32 主机条目或域名规则。代码里给的理由是，硬搬过去会把它悄悄收窄成网络地址，那比丢条目更糟。

### 出站报文的实际顺序

沙箱发出的每个包，源地址固定是 `169.254.68.6`，`from_cube` 按这个次序处理：

1. 目标是网关 `169.254.68.5` → 重定向到 `cube-dev`，交给宿主机协议栈。
2. 评估 L3/L4 策略（下节）。被打上"需要 L7 检查"标记的目标，走 `cube-dev` 转给 CubeEgress，不再进直接 NAT 路径。
3. DNS 查询被拦下来提取域名，供域名策略在响应回来时学习 IP。
4. 创建或更新会话，同时写 `egress_sessions` 与 `ingress_sessions`。
5. 执行 SNAT，把源改写成 SNAT 池里的地址和动态端口，同步更新 L3、L4 校验和。
6. 重定向到宿主机网卡。

入站方向由 `from_world` 分两种情况：会话命中就在 `ingress_sessions` 里重建沙箱侧五元组做反向 DNAT；没命中就查 `remote_port_mapping`，按静态映射把目标改到沙箱监听端口。第三条路是 `from_envoy`，处理宿主机自己发往沙箱的流量，两种来源的源地址处理方式不同：CubeEgress 的回包保留真实远端地址（靠 `IP_TRANSPARENT`），沙箱因此以为响应是远端直接发来的；宿主机的就绪/存活探测则把源地址改写成 `169.254.68.5`，让沙箱以为是网关发来的。

### 会话表与超时：为什么 ESTABLISHED 只留 3 小时

TCP 状态跟踪直接照内核的 `enum tcp_conntrack` 取值。Go 侧 `cubevs/reaper.go` 从 `tcpCTNone` 排到 `tcpCTSynSent2` 共 10 个实际状态，外加 `Invalid`、`Ignored` 两个哨兵。超时表也在同一个文件里：

| 状态 | 回收阈值 | 内核 nf_conntrack 的默认值 |
| --- | --- | --- |
| SYN_SENT / SYN_RECV / SYN_SENT2 | 1 分钟 | 2 分钟 |
| ESTABLISHED | 3 小时 | 5 天 |
| FIN_WAIT / TIME_WAIT | 2 分钟 | — |
| CLOSE_WAIT | 1 分钟 | — |
| LAST_ACK | 30 秒 | — |
| CLOSE | 10 秒 | — |
| UDP UNREPLIED / REPLIED | 30 秒 / 180 秒 | — |
| ICMP | 30 秒 | — |

值得停下来看的是 ESTABLISHED 这一行：3 小时只有内核默认值（5 天）的四十分之一。这不是偷工，而是场景决定的——沙箱随时可被暂停或销毁，一条挂着 5 天的会话映射意味着 SNAT 端口和会话表槽位被长期占住。代价是空闲超过 3 小时的长连接会在数据面失去反向 NAT 条目，需要靠 `timeout` / 自动暂停这类生命周期语义来管，不能指望连接跟踪替它兜底。

会话表容量 `maxSessions = 1048576`，回收器是每 5 秒扫一遍 `egress_sessions` 的后台 goroutine，占用率过 80% 告警。会话非正常终止（比如 ESTABLISHED 没等到 FIN 就超时）会记一条告警。`active_close` 标志用来区分关闭由哪一侧发起，TIME_WAIT 的处置跟着变。

回收器只做 Go 侧的清理，NAT 池的紧张靠另一条路缓解：SNAT 最多用 4 个 IP，`index = jhash(sandbox_ip) % 4` 按沙箱确定性地选，保证同一沙箱的所有连接走同一个源地址（外部防火墙规则和日志因此好处理）；端口从 30000 起单调递增分配，条目受 BPF 自旋锁保护；撞上 `ingress_sessions` 已有条目就递增重试，重试次数有上限，超限则丢这个包。

宿主机的端口空间被切成三段，避免子系统互相抢：`10000-19999` 是宿主机临时端口，`20000-29999` 给 CubeProxy 访问沙箱用（Cubelet 分配映射端口时只用这一段），`30000-65535` 留给沙箱出站的 SNAT 源端口。

### allow、deny、默认放行，以及 8192 这条线

出站策略优先级是 **允许 > 拒绝 > 默认放行**：先查 `allow_out_v3`，命中即放（条目带 `L7_REQUIRED` 标记的话，随后的 80/443 还会被送进 CubeEgress）；再查 `deny_out`，命中就拒，TCP 尽量回 RST、非 TCP 直接 drop；都不命中就放行。因此可以先下一条 `0.0.0.0/0` 全拒，再用 allow 开白名单。

`allow_internet_access=False`（默认 `True`）走的就是这条路——后端替你装一条 `0.0.0.0/0` 的 deny-all。

不管策略怎么配，这五个段永远在 `deny_out` 里：`10.0.0.0/8`、`127.0.0.0/8`、`169.254.0.0/16`、`172.16.0.0/12`、`192.168.0.0/16`，防止沙箱探测宿主机内网和其他沙箱。

规则数量有硬上限，超限时错误从 Cubelet 经 CubeMaster、CubeAPI 逐层回给调用方：`allow_out` 与 `deny_out` 各 8192 条唯一 key，域名规则 1024 条。报错长这样：

```text
network.allow_out_v2 exceeds maximum entries: got 8193, max 8192
```

域名规则解决的是"对端 IP 是动态的"这类目标，比如 CDN（内容分发网络）和云服务的 API。规则按沙箱存在 `dns_allow_v2` 里，key 是反转后的小写域名，支持精确（`qq.com`）和通配（`*.qq.com`，不含顶级域本身）。生效过程是一次学习：`from_cube` 从查询里取出域名并命中规则，就把查询 id 与源端口记进 `dns_query_track`；响应回来时 `from_world` 匹配上，抽出 A 记录，按 DNS TTL 作为过期时间写进该沙箱的 allow 表。因为学出来的条目落在同一张表里，L3/L4 快路径不需要为它们分叉。

没配域名规则时这条链路完全不启动：沙箱元数据里的 `dns_policy_flags` 是总闸门，未置位则 DNS 报文走普通 UDP NAT，不解析、不写跟踪表、不查域名表。

### 两个 `169.254.68.x` 和一类常见误配

沙箱 guest 里看到的地址是固定的：`mvm_inner_ip = "169.254.68.6"`、`mvm_gw_dest_ip = "169.254.68.5"`（Cubelet 配置项，不是编译期常量）。所有沙箱都用同一个地址并不冲突——每块 TAP 是点对点链路，链路本地地址只在链路内有意义。也正因为链路上没有真实主机应答 ARP，`from_cube` 兼职 ARP 代理：收到"谁是 169.254.68.5"就现场构造一份回复，把发送方 MAC 填成 `cube-dev` 的网关 MAC 沿同一块 TAP 送回去。

另一套地址在宿主机侧：TAP 池默认占用 `192.168.0.0/18`，`cube-dev` 拿到 `192.168.0.1`，TAP 名字形如 `z192.168.0.x`。这两套分属不同层面，但第二套会咬人——排障文档里就有一例完整的：

```toml
[plugins."io.cubelet.internal.v1.network"]
    eth_name = "eth0"
    tap_init_num = 500
    cidr = "192.168.0.0/18"
```

## 出网的另一半交给 CubeEgress

CubeVS 只看 IP 和端口，看不到 URL。要看内容的部分交给 CubeEgress：每台宿主机上一个 host-network 容器，OpenResty 加 Lua，在面向沙箱的地址上开两个 TPROXY 监听——8080 收 HTTP、8443 收 HTTPS。

哪些流量进哪个监听，由规则声明的 port/scheme 映射决定，而不是绑死目的端口。链路是这样接起来的：

1. `from_cube` 按 allow 表里的 (host, port) → scheme 映射，在出方向 SYN 上打 `skb->mark`；
2. iptables 的 `mangle/PREROUTING` 按 mark 做 TPROXY，把包转到 `192.168.0.1:8080` 或 `:8443`；
3. `ssl_certificate_by_lua` 按客户端 SNI 现场签一张 leaf 证书；
4. `access_by_lua` 匹配 L7 规则，放行 / 拒绝 / 注入；
5. `proxy_pass` 到原始目的 IP（依赖 `IP_TRANSPARENT` 保留）。

第 3 步能被沙箱接受，是因为 CubeEgress 的根 CA 在模板构建时就烘进了 rootfs 的系统 CA。工作负载的 TLS 客户端因此看不见这次中间人检查，代理可以合法读写请求和响应。这也说明架构文档里"无 iptables 规则"那句话有边界：NAT 和策略路径确实不装规则，但把流量交给 L7 代理需要一条 mangle TPROXY 规则来转向。

三类能力都由创建沙箱时那一份规则列表驱动：域名过滤按 SNI / Host / 方法 / scheme / 路径；凭证注入在转发前追加固定 header（典型是 `Authorization: Bearer …`），密钥不进沙箱，模型上下文里也拿不到；每一次决策——放行、拒绝、注入、TLS 握手结果——都落到本机按主机划分的 JSONL 审计日志。上游 `proxy_read_timeout` / `proxy_send_timeout` 是 2 小时，`proxy_connect_timeout` 保持 10 秒。

## 数字怎么读

先回答"测的是什么"。官方裸金属报告（2026-06-01，`docs/zh/blog/posts/2026-06-01-cubesandbox-perf-benchmark.md`）的机型是腾讯云 BMI5，2 Socket × 24 Core × 2 Thread 共 96 逻辑核、375 GiB 内存，沙箱规格 2 vCPU / 2 GiB，压测工具 `examples/cube-bench`，每轮先 warm-up 丢掉首轮结果。指标里 `wall` 是整批端到端耗时，`per` 是 wall 除以批次数。

**创建延迟与并发（基于模板新建沙箱）：**

| 并发 | 请求数 | avg | min | p95 | max | 单沙箱均摊 `per` | 吞吐 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 20 | 47.8 ms | 43.5 ms | 57.4 ms | 60.4 ms | 55.8 ms | 17.9 个/s |
| 10 | 200 | 88.7 ms | 45.8 ms | 116.9 ms | 119.1 ms | 9.9 ms | 101.4 个/s |
| 20 | 300 | 98.1 ms | 47.7 ms | 175.8 ms | 232.6 ms | 5.5 ms | 180.9 个/s |
| 50 | 500 | 276.1 ms | 60.6 ms | 508.4 ms | 681.3 ms | 6.8 ms | 147.6 个/s |

这张表要这样读：单条延迟随并发加深而变差（50 并发 p95 已经到 508 ms），但均摊到每个沙箱的时间从 55.8 ms 掉到 5.5 ms——因为创建过程大量是并行的编排工作，不是串行的算力开销。报告给的结论是这台机器上 20 并发是吞吐甜点，50 并发反而回落到 147.6 个/s。

同一份 README 里另有一组数字："单并发下为 60ms，50 并发场景下平均 67ms（P95 90ms，P99 137ms）"。这句注解和上表对不上，50 并发的均值差了一个量级，而且它从 v0.1.0 的 README 起就在那儿，也没标机型与日期——不是"新版本变快了"能解释的。两处口径无法从公开材料里对齐（unresolved），引用时要说清自己用的是哪一份，以及能不能给出机型。顺带一提，旧文档里另一个滞后数字是 Map 数量：v0.1.0 到 v0.3.0 都写"九个"，而现在 `map.h` 里是 16 个定义。

**内存与密度：** 从空机开始分批 `create-only` 起沙箱，用 `(当前 used − 基线 used) ÷ VM 数` 算均摊：

| 存活沙箱数 | 系统可用内存 | 单 VM 均摊 |
| --- | --- | --- |
| 0（基线） | 359.5 GiB | — |
| 100 | 357.4 GiB | 约 21.5 MB |
| 300 | 352.5 GiB | 约 23.8 MB |
| 500 | 347.3 GiB | 约 25.0 MB |
| 1000 | 334.3 GiB | 约 25.7 MB |

这里必须区分两个"内存开销"。README 的"< 5 MB"是 CubeSandbox 自身在 ≤ 32 GB 规格下的额外开销口径；上表的 25 MB 是宿主机实际内存水位的变化，包含 guest 已写入的页。两者不矛盾，但也回答不了同一个问题。

从这张表**不能**推出：单机就能塞几千个 2 GiB 沙箱。报告自己给的估算是——每个沙箱真把 2 GiB 写满时 `375 GiB ÷ (2 GiB + 25 MB) ≈ 185 个`；只有在空载或轻载、页按需分配没被触发时，密度才由 25 MB 量级的开销主导，"数千实例"是那个场景。另外还有一个非内存的天花板：TAP 池目标数 `tap_init_num` 默认 500，要压到 1000 得先改配置再重启 `cube-sandbox-cubelet.service`。

报告在这一点上加了醒目提醒：每批创建前用 `free -h` 确认余量，边起边看，不要一次起太多——内存耗尽会触发 OOM Killer，轻则杀进程，重则损坏环境。

## 部署：五条路径和四个硬前置

部署入口在五个月里拓宽了不少。v0.1.0（2026-04-20）的快速开始只认一种机器：已启用 KVM 的 x86_64 裸金属；PVM 和 dev-env 都是 v0.2.0 才出现的入口，Terraform 与 ARM64 在 v0.5.0，K8s 在 v0.6.0（标 preview），跨节点暂停恢复在 v0.7.0（也是 preview）。现在按手里有什么机器选：

| 手上的机器 | 走哪条 | 要点 |
| --- | --- | --- |
| 普通云服务器（没有 `/dev/kvm`） | PVM | 装 PVM 宿主机内核 + `kvm_pvm` 模块，再一键安装 |
| 物理机 / 裸金属，已开 KVM | 裸金属一键 | x86_64 直接跑脚本；ARM64 暂时要手动下包 |
| 已有 K8s 集群 | K8s | 文档标 preview |
| 只有本地开发机（WSL 2 / Linux） | dev-env | 一次性 OpenCloudOS 9 虚机，README 上标着"不推荐 — 性能差" |
| 生产集群 | Terraform | 腾讯云一键，`deploy/one-click/terraform/tencentcloud/` |

PVM（Pagetable-based Virtual Machine，基于页表的虚拟机）值得多说一句，因为它解释了"普通云服务器也能跑"这件事。它是建在 KVM 之上的页表方案虚拟化框架，对宿主 hypervisor 完全透明：不要求宿主向 guest 暴露 VT-x / AMD-V，而是在 guest 内核层用影子页表完成特权级切换与内存虚拟化。约束是 PVM 宿主机内核只有 x86_64 的包，ARM64 不支持——那种机器要用原生提供 KVM 的物理机或裸金属。

KVM、root 权限、外网连通这三项属于常规要求。下面四条最容易漏，缺一个就装不上：

1. **glibc ≥ 2.31。** 二进制基于 Ubuntu 20.04 构建，老系统上直接跑不起来。
2. **`/data/cubelet` 必须是 XFS。** CubeCoW 的 O(1) 快照靠 reflink，ext4 上没有。Ubuntu / Debian / WSL 默认都是 ext4，需要单独挂载（issue #311 有逐步指引）。推荐发行版是 OpenCloudOS 9 和 TencentOS 4，默认就是 XFS。
3. **`/data/cubelet` 上至少 50 GB 可用空间。** 要多做几个模板或自定义镜像，200 GB 起。
4. **Docker 在跑。** MySQL、Redis、CubeProxy、CoreDNS 都走 Docker Compose。

宿主机安装（国内源）：

```bash
curl -sL https://cnb.cool/CubeSandbox/CubeSandbox/-/git/raw/master/deploy/one-click/online-install.sh | MIRROR=cn bash
```

PVM 环境多带一个 `CUBE_PVM_ENABLE=1`。脚本默认在下载大发布包前先做环境前置检测，跳过的方式是 `ONE_CLICK_SKIP_PRECHECK=1` 或 `--skip-precheck`——但真正执行部署的 `install.sh` 仍会跑一遍强制检测，绕不过去。

装完之后端口就固定了：E2B 兼容 REST API 在 `3000`，Web 控制台在 `12088`。CubeMaster、内置 network runtime 的 Cubelet、CubeShim 以宿主机进程运行，MySQL 和 Redis 走 Docker Compose。TLS 和域名路由由 CubeProxy 负责，分别是 mkcert 签发的证书和 CoreDNS 的 `cube.app`。

多机集群和"再跑一遍安装脚本"不是一回事。控制节点跑全家桶（含 CubeOps 与内置 MinIO）；新增计算节点要把同一份发布包拷过去，用 `install-compute.sh` 并以 `.env` 声明角色：

```bash
ONE_CLICK_DEPLOY_ROLE=compute
CUBE_SANDBOX_NODE_IP=<当前节点IP>
ONE_CLICK_CONTROL_PLANE_IP=<控制节点IP>
```

计算节点向控制面的 CubeOps 注册（`3010`），用内置 MinIO 时还要通 `9000`。计算节点要求物理机或裸金属，不接受嵌套虚拟化。

从源码构建不需要 `--recursive`：仓库里的 `.gitmodules` 是个 0 字节空文件，没有子模块。构建入口也不是 `make build`——Makefile 里没有这个 target，只有 `all`、`builder-image`、`cubemaster`、`cubelet` 这些。正确的一条是：

```bash
cp deploy/one-click/build.env.example deploy/one-click/build.env
./deploy/one-click/build-release-bundle-builder.sh
```

产物在 `deploy/one-click/dist/cube-sandbox-one-click-<commit>.tar.gz`，版本号取当前 commit ID。构建前还得准备 guest 内核：从 `kernel-release-*` Release 下载 `vmlinux` 放进 `deploy/one-click/assets/kernel-artifacts/`，或自行编译后用 `ONE_CLICK_CUBE_KERNEL_VMLINUX` 指定路径。装完用 `./smoke.sh` 验一下 `cube-api` 的 `/health`。

## 接入已有 E2B 代码要改什么

四个环境变量把 SDK 的请求从 E2B 云改到本地：

```bash
export E2B_API_URL="http://127.0.0.1:3000"
export E2B_API_KEY="e2b_000000"          # SDK 只校验非空，本地填任意串
export CUBE_TEMPLATE_ID="<你的模板ID>"
export SSL_CERT_FILE="/root/.local/share/mkcert/rootCA.pem"
```

业务代码不用动：

```python
import os
from e2b_code_interpreter import Sandbox

with Sandbox.create(template=os.environ["CUBE_TEMPLATE_ID"]) as sandbox:
    result = sandbox.run_code("print('Hello from Cube Sandbox, safely isolated!')")
    print(result)
```

想用到 CubeSandbox 独有的能力，就换成官方 `cubesandbox` SDK（PyPI，≥ 0.2.0），它向下兼容 e2b 的接口形态：

```python
from cubesandbox import Sandbox, NEVER_TIMEOUT

sandbox = Sandbox.create(template=..., timeout=60, on_timeout="pause")
snap = sandbox.create_snapshot()
copies = sandbox.clone(n=4)          # 从运行中的沙箱派生 4 个独立副本
sandbox.rollback(snap.id)            # 原地回到快照状态，沙箱 ID 不变
```

这里有个语义差异容易踩：`timeout` 的单位是**秒**，而 e2b 的 `timeoutMs` 是毫秒。不传 `timeout` 时用服务端默认值，服务端没配或配成 ≤ 0 就是永不超时；`NEVER_TIMEOUT` 是 `-1`，`0` 表示空闲后首次扫描即回收。`on_timeout` 取 `"kill"`（默认）或 `"pause"`——暂停后的沙箱把 VM 内存落成快照，不占 CPU 和内存，`connect()` 或者有请求打进来时再恢复回去。

沙箱状态是五个：`running`、`pausing`、`paused`、`resuming`、`terminated`。`terminated` 不可恢复。

## 三个对得上日志的故障

各组件日志在 `/data/log/<Module>/`，按天或按 `-req.log` 命名，**不进 `journalctl`**；Cubelet 默认级别是 `warn`，复现问题时常要临时开 debug。沙箱内 init 进程的输出被 CubeShim 写进 Cubelet 的私有挂载命名空间，得用 `cubecli logs` 读；guest kernel 通过 `console=hvc0` 打印的启动信息也走同一条 `cube-shim-req.log`，不用额外工具。

**一、创建模板卡在 `CREATING_TEMPLATE` 超时。** 现象是 `cubemastercli` 报 `context deadline exceeded`，`cube-bench` 侧则是一批 `HTTP 500` 带错误码 `130595`。去 Cubelet 日志里搜关键字：

```bash
rg 'PortBindingFailed|probe \[|Create fail|sandboxIP' /data/log/Cubelet/Cubelet-req.log
```

看到 `The initialization timeout or detecting 192.168.1.40 port failed` 这类行，基本就是 TAP 池网段和宿主机局域网撞了：`ip route` 里同时存在 `192.168.0.0/18 dev cube-dev` 和 `192.168.1.0/24 dev enp56s0f0`，而 /24 比 /18 更精确，于是访问沙箱地址的探测包走了物理网卡，探不到真正的沙箱。解法是把 `cidr` 改到不冲突的段（例子里改成 `172.31.64.0/18`），删掉旧的 `cube-dev` 和 `z*` TAP 再重启。

**二、装完跑不起来，或者模板永远做不出来。** 两类原因占大多数：glibc 低于 2.31 导致二进制直接失败；`/data/cubelet` 是 ext4，CubeCoW 的 reflink 落不了地。安装脚本的前置检测就是拦这两种情况的，别急着绕过。第三类是探针：镜像里没有固定端口上的 HTTP 服务，或者探针路径不返回 2xx，模板构建会一路等到超时。

**三、压到高并发后单条创建延迟突然拉长。** 先确认这不是故障。50 并发下 p95 到 500 ms 级别是那份报告里的正常形态。真撞上瓶颈时按三块天花板依次排：会话表（1,048,576 条，过 80% 会有回收器告警）、TAP 池数量 `tap_init_num`（默认 500，改完必须重启 Cubelet 才生效）、内存（轻载下每沙箱 20 多 MB，业务真写内存时要按规格算）。

## 什么时候不必上 CubeSandbox

它换掉的不是"安全"这一层，而是"既要强隔离又要点开就走"这一层。所以判断可以简单粗暴：

- **要跑模型现写的、内容不可信的代码，并且并发高**：值得上。独立内核加默认拒绝内网段，加上 L7 的域名白名单和凭证注入，这套组合是容器方案给不了的。
- **代码来源可信、只是要环境隔离**：Docker 或者一次 `venv` 就够了，多引一套 KVM 依赖不划算。
- **需要 GPU 隔离**：目前只能等。GPU 透传在 README 的 Roadmap 上，还没落。
- **只有普通云服务器，又不想换内核**：PVM 要装专用宿主机内核并重启。不想动内核的话，dev-env 那条路能看不能跑，官方自己标了不推荐。
- **要做 E2B 的完全替代**：先看 Roadmap 上"补齐 E2B API 剩余差距"这一条的状态。快照、克隆、回滚这些是 CubeSandbox 特有，e2b SDK 里没有对应接口，切过去意味着代码要按 `cubesandbox` 写。

采用的顺序建议反过来走：先用一台裸金属或 PVM 机器装单机，跑通官方 `sandbox-code` 模板，确认 `create` 和 `run_code` 通畅；再把现有 E2B 调用改成环境变量指向本地，看有没有触发上面那批语义差异；然后配 `allow_internet_access=False` 加白名单，让 CubeEgress 先只跑审计不拦流量；最后再谈多节点和 K8s。生产暴露到不可信网络之前，两件事必须先做完：按 `docs/zh/guide/network-hardening.md` 做加固，以及把 `AUTH_CALLBACK_URL` 接到自己的鉴权服务上。

## 常见问题

**Q：`< 60 ms` 和 `< 5 MB` 能同时成立吗？**
各自成立，但别拿它们做乘法。60 ms 是裸金属单并发的创建延迟，README 自己那句注解里 50 并发的均值已经是 67 ms（另一份报告的 50 并发高出一个量级）；5 MB 是 CubeSandbox 自身在 ≤ 32 GB 规格下的额外开销，不等于一个沙箱在 `free -h` 里占用的量——后者实测在 25 MB 量级。算延迟用前者，算密度用后者。

**Q：CubeVS 完全不碰 iptables 吗？**
NAT、会话、策略这三件事在 eBPF 里做，不产生 iptables 规则。但只要用到 L7 出网检查，就需要一条 mangle/PREROUTING 的 TPROXY 规则把打了 mark 的包转向 CubeEgress。

**Q：为什么沙箱里 `ip addr` 看到的地址全都一样？**
`169.254.68.6` 是 guest 内的链路本地地址，每块 TAP 是点对点链路，不存在跨沙箱冲突。宿主机侧用来区分沙箱的是 TAP ifindex 和 `192.168.0.0/18` 那套地址。

**Q：暂停的沙箱还占资源吗？**
不占 CPU 和内存，VM 内存已经落成快照；但快照要存进存储层，配了 S3/MinIO 后端时可能落到对象存储。跨节点暂停恢复在 v0.7.0 里是 preview。

**Q：同一台机器上两个沙箱能互相看到吗？**
不能。各自的 TAP、各自的策略表、各自的会话，没有共享网桥或交换机；再加上 `169.254.0.0/16` 这类段永远在拒绝列表里。

## 六个自测题

1. 一次 `Sandbox.create()` 里，哪两步决定了启动耗时？为什么 TAP 的预建不算在这条关键路径上？
2. `from_cube` 处理一个出站包要走完哪几步？哪一步决定这个包交给 CubeEgress 还是直接 SNAT 出去？
3. 换成 MicroVM 之后，攻击面从"共享内核"挪到了哪里？CubeHypervisor 为此做了什么？
4. ESTABLISHED 会话只保留 3 小时，比内核默认值小得多。这个选择换来什么、丢掉什么？该由哪个机制补上？
5. 模板探针选得太早会出现什么现象？为什么"被探测端口在 `create` 返回时即可用"这句话不包括第二个端口？
6. 单机密度同时受三块天花板约束，分别是哪三块？改 `tap_init_num` 之后还要做什么才生效？

## 下一步读什么

- 想搞清楚数据面到底怎么写的：`CubeNet/src/mvmtap.bpf.c` 里的 `from_cube`，以及 `CubeNet/src/tcp.h` 那张状态推进表。
- 想知道超时值和回收节奏：`CubeNet/cubevs/reaper.go`，一张 `tcpTimeouts` 表加上每 5 秒一轮的扫描，比文档直白。
- 想理解快照为什么是 O(1)：`cubecow/` 和架构文档的存储层一节，`FICLONE` 的边界条件都在那里。
- 想接 L7 策略：`docs/zh/guide/security-proxy.md`，规则形状和审计日志字段以它为准。
- 想复现性能数字：`docs/zh/blog/posts/2026-06-01-cubesandbox-perf-benchmark.md` 每节都附完整命令，`examples/cube-bench` 的 `-c/-n/-m` 三个参数就够驱动。
- 踩坑先看：`docs/zh/guide/troubleshooting/`，排障条目要求中英双语同时提交，因此内容相对新。

## 参考资料

以下链接在 2026-09-19 逐条访问确认可达（HTTP 200）。

- CubeSandbox 仓库、README 与组件表：<https://github.com/TencentCloud/CubeSandbox>
- 架构概览（控制面 / 数据面划分、请求生命周期、支撑设施）：<https://github.com/TencentCloud/CubeSandbox/blob/master/docs/zh/architecture/overview.md>
- CubeVS 网络模型（挂载点、Map 分组、会话跟踪、SNAT、域名策略、端口段）：<https://github.com/TencentCloud/CubeSandbox/blob/master/docs/zh/architecture/network.md>
- 源码：`CubeNet/src/map.h`、`CubeNet/src/mvmtap.bpf.c`、`CubeNet/src/cubevs.h`、`CubeNet/cubevs/reaper.go`、`Cubelet/config/config.toml`（commit `d1a7bb3`，2026-09-18）
- 快速开始与裸金属部署（硬前置、安装命令、组件清单）：<https://github.com/TencentCloud/CubeSandbox/blob/master/docs/zh/guide/quickstart.md>
- 模板概览（探针语义、`envd`、镜像与模板的关系）：<https://github.com/TencentCloud/CubeSandbox/blob/master/docs/zh/guide/templates.md>
- 安全代理 CubeEgress（TPROXY 链路、SNI 签发、审计）：<https://github.com/TencentCloud/CubeSandbox/blob/master/docs/zh/guide/security-proxy.md>
- 核心操作性能基准报告（裸金属实测数据）：<https://github.com/TencentCloud/CubeSandbox/blob/master/docs/zh/blog/posts/2026-06-01-cubesandbox-perf-benchmark.md>
- 沙箱网段与局域网冲突导致创建超时（排障条目原文）：<https://github.com/TencentCloud/CubeSandbox/blob/master/docs/zh/guide/troubleshooting/local-network-cidr-conflict.md>
- Ubuntu / WSL 上挂载 XFS 的指引：<https://github.com/TencentCloud/CubeSandbox/issues/311>
- `cubesandbox` Python SDK（PyPI）：<https://pypi.org/project/cubesandbox/>
- 发布记录与 CHANGELOG（v0.1.0 于 2026-04-20 首发，v0.7.1 于 2026-09-11 发布）：<https://github.com/TencentCloud/CubeSandbox/releases>
- CubeHypervisor 的上游谱系：Cloud Hypervisor <https://github.com/cloud-hypervisor/cloud-hypervisor>，具体出处是仓库 `LICENSE` 里的第三方声明段（列出 kata-containers 与 cloud-hypervisor 的版权行）
- CNCF Landscape 条目（`ai-native-infra / workload-runtime`）：<https://landscape.cncf.io/?landscape=observability-and-analysis&group=ai-native&item=ai-native-infra--workload-runtime--cubesandbox>

核对方式记一句：组件语言和 Map 名称以源码为准，性能数字标注机型与并发度，版本差异用 tag 拉同一份文档前后对比确认。这个仓库五个月里的演进速度比它的文档快，凡是读到的架构断言，都值得再确认一次它在当前 tag 下还成立。
