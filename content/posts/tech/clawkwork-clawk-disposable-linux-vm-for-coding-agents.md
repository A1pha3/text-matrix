---
title: "clawk 拆解：把 coding agent 放进一次性 VM 之后，问题变成内存怎么还、流量怎么拦"
date: 2026-07-16T02:27:02+08:00
lastmod: "2026-09-21T00:00:00+08:00"
draft: false
slug: clawkwork-clawk-disposable-linux-vm-for-coding-agents
github_repo: "clawkwork/clawk"
source_key: "gh:clawkwork/clawk"
description: "对照 clawkwork/clawk 的 main 分支（a67d04f，v0.4.0）读这套 coding agent 沙箱：短命 CLI 与常驻 daemon 的分工、气球加准入控制加 idle 停机的三层内存机制、gvproxy 用户态协议栈里的 139 条出网白名单与交互式闸口、vsock 单入口控制面、9p 共享工具链缓存从加装到撤回的全过程，以及 vz 与 firecracker 两个 provider 今天各自的缺口。"
categories: ["技术笔记"]
tags: ["Go", "Coding Agent", "AI Agent", "开源"]
---

> **读者**：已经用过 `--dangerously-skip-permissions`、正在判断"要不要把 agent 挪出本机"的工程师；以及想看清一台给智能体用的 microVM 在资源与网络上具体怎么做取舍的人。
>
> **读法**：先给一句判断，再按"进程模型 → 内存 → 网络 → 控制面"四条主线拆开，每条都指出它防的是哪一种真实故障；ticket 流转与 9p 撤回两节把这些机制串起来，文末留了复核命令。
>
> **核对基线与边界**：内容对齐 `clawkwork/clawk` 的 `main` 分支提交 `a67d04f`（2026-08-12，v0.4.0 的发布提交是次日 2026-08-13），核对时间 2026-09-21。本文没有实跑 clawk——本机没有 Go 1.26 工具链，也没有安装它或起过 VM。所有结论来自仓库源码与仓库自带文档，关键处标了 `文件:行号`；启动耗时、内存占用这类必须执行才能定案的数字，文中一处也不给。

## 一句话判断

clawk 想解决的问题不新：agent 要么每条命令都问你一次，要么你干脆关掉审批，而关掉审批的第一天可能就是它 `rm -rf` 的那天。它给出的答案也不新：给 agent 一台一次性 Linux 虚拟机。

新的是随之而来的三问：这台 VM 的内存怎么在多个沙箱之间还给宿主；出网流量拦在哪一层，才让 guest 里的 root 改不动；一条 VM 的生命周期该由哪个进程负责。三问在仓库里都有带出处的答案，而"把宿主的依赖缓存共享进来"这件附带的事，还留下了一次完整的加装与撤回。

它关于提示词的安全话术只有一句，抄自 README：

> The boundary isn't a rule in a prompt the agent could be talked out of. It's a separate machine, and the only openings are the ones you mounted.

## 项目坐标

| 项 | 值（2026-09-21 核对） |
|:---|:---|
| 仓库 | [clawkwork/clawk](https://github.com/clawkwork/clawk)，`main`，`a67d04f` |
| 定位 | 给编码智能体一次性 Linux microVM 的 Go 命令行工具（CLI），macOS 优先，Linux 标为实验性 |
| 许可 | Apache-2.0；`NOTICE` 列出两个被复制改造的第三方组件：`clawkwork/gvisor-tap-vsock` 分支（Apache-2.0）与 hcsshim 的 ext4 写入器（MIT） |
| 发布 | 仓库建在 2026-07-06，v0.1.0 次日发布；v0.2.0 在 07-13，v0.3.0 在 08-05，v0.4.0 在 08-13 |
| 活跃度 | `main` 最后一次提交 2026-08-12，距核对日 40 天；1,012 stars、39 forks；贡献者 1 人（`celrenheit`，33 次提交）；2 个未关闭 issue、2 个未关闭 PR |
| 规模 | `git ls-files` 355 个文件；`machine/` 是独立 Go module，靠 `replace` 接进来 |
| 语言与下限 | Go 1.26（`go.mod:3`）；发行二进制自带 guest 侧程序，用户机不需要 Go |

一个只发布到 v0.4.0、由一个人推进、一个多月没动的仓库，值不值得单独写一篇。值得的理由只有一条：它内部有几处决策把"踩过的那次故障"直接写进了注释，这类材料在别处读不到。同类的本地 microVM 与容器方案，站内已有 [apple/container](/posts/tech/apple-container-macos-lightweight-vm-containers/) 与 [microsandbox](/posts/tech/microsandbox-local-microvm-runtime/) 两篇，但都没有把这三问放到一起处理。

## 目录

- [一句话判断](#一句话判断)
- [项目坐标](#项目坐标)
- [系统地图：五块职责各自归谁](#系统地图五块职责各自归谁)
- [为什么 CLI 不持有 VM](#为什么-cli-不持有-vm)
- [内存：气球、准入与 idle 停机](#内存气球准入与-idle-停机)
- [网络：过滤点在 guest 之下](#网络过滤点在-guest-之下)
- [进 guest 的路只有一条](#进-guest-的路只有一条)
- [一次 ticket 的完整流转](#一次-ticket-的完整流转)
- [加装又撤回：9p 共享工具链缓存](#加装又撤回9p-共享工具链缓存)
- [两个 provider 的分岔](#两个-provider-的分岔)
- [版本边界：哪项能力从哪个版本起](#版本边界哪项能力从哪个版本起)
- [该不该用，从哪儿开始用](#该不该用从哪儿开始用)
- [五道自测题](#五道自测题)
- [出错时先看哪几处](#出错时先看哪几处)
- [下一步读什么](#下一步读什么)
- [参考与复核命令](#参考与复核命令)

## 系统地图：五块职责各自归谁

看这套东西最容易混成一条线的是"CLI、虚拟机、网络、guest 里的进程"。它其实是五块，边界划得很硬。地图背后是 `DESIGN.md:15-24` 列出的四条设计目标约束：要真操作系统、强隔离、便宜的生命周期；镜像由项目自带；网络策略得抗篡改；guest 里不留任何 clawk 控制不了的常驻进程。

| 块 | 在哪跑 | 负责什么 | 位置 |
|:---|:---|:---|:---|
| `clawk` CLI | 宿主，短命 | 解析命令、把配置快照成沙箱记录、跟 daemon 要结果，然后退出 | `internal/cli`，一个 verb 一个文件 |
| `__vzd` / `__fcd` | 宿主，常驻 | 持有 VM 整个生命周期，跑用户态网络栈，macOS 上还兼 agent 代理、ssh-agent 代理、反向转发代理 | `internal/cli/vzd.go`、`fcd.go`，共用 `daemon.go` |
| `machine` | 库，不是进程 | 声明式 `Spec` 进、`Machine` 出；OCI 镜像转 ext4、reflink 克隆、两个 hypervisor 的适配 | `machine/`，独立 module |
| guest 三件套 | 虚拟机里 | `clawk-init`（PID 1）、`clawk-pty-agent`（唯一入口）、`clawk-time-sync` | `internal/agentembed`，宿主交叉编译后注入 rootfs |
| 出网闸 | daemon 进程内 | 网关、DHCP、DNS、网络地址转换（NAT）与 allowlist 判定 | 打了补丁的 gvproxy 加 `internal/netfilter` |

`ARCHITECTURE.md:109-125` 的包映射表是这份地图的原始版本。两条 `//go:build` 规则把平台代码隔得很干净：Linux 检出编译不了 vz 那半，反之也一样（`ARCHITECTURE.md:137`）。所以"运行时才发现平台不支持"这条路径不存在，`internal/cli/providers_darwin.go` 与 `providers_linux.go` 在参数校验阶段就分岔了。

把五块按进程与端口的关系画成一棵树，是这样：

```text
clawk CLI                       host, short-lived, exits with your command
└─ setsid ─> __vzd | __fcd      host daemon, owns the VM for its whole life
   ├─ machine.Get("vz"|"firecracker")
   │   └─ guest VM             disposable Linux, boots an OCI image as rootfs
   │      ├─ clawk-init                 PID 1, no systemd / cloud-init
   │      ├─ clawk-pty-agent            AF_VSOCK 1024, the only way in
   │      ├─ clawk-time-sync            AF_VSOCK 1025
   │      └─ /home/agent/workspace      virtio-fs live mount (vz only)
   ├─ gvproxy + AllowList      in-process userspace stack, the egress gate
   ├─ agent.sock               bridges the CLI to guest port 1024 (vz)
   ├─ ssh-agent proxy          AF_VSOCK 1026, keys never enter the guest
   ├─ balloon controller       reads the 56-byte report pushed on 1027
   └─ idle watchdog            stops the VM after 30 min idle (vz only)
```

## 为什么 CLI 不持有 VM

`clawk` 的一次调用是秒级的：attach 完、命令跑完，进程就没了。一台要跑几小时甚至几天的 VM 不能活在这种进程里。所以 `provider.Start` 做的第一件事是 `setsid` 拉起一个脱离控制终端的 daemon，等 guest 里的 agent 回话才返回（`DESIGN.md:29-32`）。VM 的命此后就握在这个 daemon 手上：`clawk down` 靠 pidfile 给它发信号，而 `clawk list`、`clawk status` 这类读命令压根不碰它，只读 `~/.clawk` 下的记录。

`DESIGN.md:240-242` 给了为什么不写成"CLI 后台起个 goroutine"的两条理由：VM 必须活得比一次 `Ctrl+C` 长；而短命 CLI 要能连回来，那些 broker 套接字（socket）总得有个进程持有。

这条分工顺带解释了安装形态。README 说装完不需要额外宿主工具：没有 Docker、没有 qemu、不需要 sudo。卸载时也没有 launchd 作业要清——那些 per-sandbox 守护进程就是普通进程，跟着自己的 VM 一起走（`README.md:146-149`）。

## 内存：气球、准入与 idle 停机

一台 Mac 上同时开五六个沙箱，最先出事的是内存。clawk 在这里堆了三层，每层防的是不同时间尺度的问题。

**气球**处理"平时别占着"。默认值是 `baseline 1024 MiB / ceiling 4096 MiB / 4 vCPU`（`internal/cli/resources.go:17-19`），两者的差就是气球的行程：guest 报告有内存压力就放气，闲下来就充气收回基线。`memory` 单独写则视为固定大小、不留突发余量，这是为了保留加气球之前那条指令的老语义（`resources.go:44-46`）。

问题在于 Apple 的 virtio-balloon 不协商统计队列（`VIRTIO_BALLOON_F_STATS_VQ` 没谈成，`machine/vz/memreport.go:40-42`），宿主拿不到 guest 内部的 MemAvailable。clawk 的做法是自己造一个上报通道：guest agent 通过 vsock 端口 1027 推一个定长快照，七个 big-endian `uint64` 共 56 字节，依次是 `MemTotal`、`MemAvailable`、内存 PSI 的 `some avg10`（×100）、`load1`（×100）、收发字节数、`SwapTotal`、`SwapFree`。长度是分档加上去的（24 → 40 → 56），新旧彼此仍读得懂（`machine/vz/memreport.go:22-31`）；老 agent 不报活动字段时，控制器降级回只看会话信号。控制器每 5 秒轮询一次（`machine/vz/pressure_darwin.go:103`），20 秒没有新报告就当作过期（`pressure_darwin.go:121`）。PSI 要内核带 `psi=1` 启动，取不到时控制器只靠 available/total 比值决策。

**准入控制**管的是另一件事：别让宿主炸掉。`internal/cli/admission.go:13-21` 的注释把原因写在第一句：guest 内存事实上不可分页，所以分给运行中 VM 的内存加上宿主自己的需求一旦超过物理内存，内核就会去 fault 一个杀不掉的进程，launchd 收到的是 SIGBUS。气球是事后反应，突发面前来不及。于是启动时按最坏情形算：所有运行中的沙箱同时冲到自己的 ceiling，加上新这一个，还要给宿主留下 `max(物理内存 / 4, 3 GiB)` 的余量（`admission.go:26-46`）。算不过来就当场拒绝，它能做的只有不启动。

第三层是 idle 停机，管的是你忘了的那台 VM。`internal/cli/idle.go` 的判定是三条信号合取：agent 代理上没有桥接中的会话、guest load1 低于 0.25、两次采样之间收发字节增量低于 32 KiB。任一条不满足就不算空闲，所以"detach 之后继续跑的那次构建"和"有人正在浏览转发出来的 dev server"都会让 VM 活着。采样拿不到时按活跃处理——正在开机的 guest 还没起 agent，停一台看不见的机器是最坏反应（`idle.go:16-18`）。

阈值写死在 `idle.go:27-45`：每 1 分钟一次采样（所以实际停放时间最多比配置超时晚一个 tick），默认超时 30 分钟（`resources.go:138-144`），可按沙箱改成 `idle_timeout 2h` 或 `off`，最小 1 分钟。

这里有两个坑要记：停机的语义是 `stop` 而不是 `pause`，`clawk list` 里显示 `stopped (idle)`，任何 attach 或 run 都会重新开机，行为等价于 `down` 加 `up`，于是 `on up` 钩子会重跑，必须写成幂等；端口转发也随停机消失。而 firecracker 侧的 daemon 观测不到客户端会话，所以 idle 停机目前只有 macOS 有（`docs/commands.md:122-123`）。

v0.4.0 加的 swap 是这套内存机制的第四块，而它的原因是气球。宿主压力下 clawk 会按 guest 需求收回 RAM（WARN 收到 ceiling 的 3/4、CRITICAL 收到 1/2，下限 512 MiB，`machine/vz/balloon.go:29-52`）。guest 里冷的匿名页没地方去，就直接卡在回收路径上，最坏情况喂给自己的 OOM killer。一次几秒的停顿不只是慢：agent 进程不再读套接字，连接空下来，而不到一分钟就回收 NAT 映射的链路（手机热点、酒店网络正是这类）会就此断掉一轮流式响应。加 swap 是把停顿换成翻页（`CHANGELOG.md:73-99`、`internal/sandbox/swapdisk.go:18-22`）。

实现里有两处细节对得上前面的判断。swap 走自己那块稀疏 virtio-blk 设备而不是 rootfs 上的 swapfile，因为 `swapon(2)` 拒绝带洞文件，写成文件就会按整块大小实打实吃掉宿主磁盘；默认 2 GiB 是上限而非分配，从不换出的沙箱只为它付几百字节的目录项（`internal/sandbox/swapdisk.go:26-33`）。`clawk-init` 自己按 `linux/swap.h` 的 version-1 布局写盘头，magic `SWAPSPACE2` 落在 `[pagesize-10, pagesize)`。不外调 `mkswap(8)` 的理由与它直接改 `/etc/passwd` 建用户同源：rootfs 是任意 OCI 镜像，没人保证里面有 util-linux（`internal/agentembed/init_main.go.in:352-356`）。

气球控制器则要学会看换出量。冷页换出会抬高 `MemAvailable` 又压低 PSI，两个信号同时把这个 guest 读成"很宽松"，不去干预就会把正在干活的 guest 永远停在基线上。所以 `swapTrend` 只在换出量增长时压制回收，静默累计 24 次报告（约两分钟）后放开（`machine/vz/balloon.go:96-167`）；占用会锁存，槽位只在对应页被换回来时释放，光看水位等于永久免死。还有一个不利的对称性：`swapon` 请求了 `SWAP_FLAG_DISCARD`，但两个后端的 virtio-blk 都不宣告 discard 支持，内核于是丢掉这个标志。换出的页在沙箱销毁前不会还回宿主，所以那个数字要按高水位读；也正因为如此，设备稀疏不等于可以随便调大（`internal/sandbox/swapdisk.go:32-37`）。

## 网络：过滤点在 guest 之下

"agent 有 root、能改 `/etc/resolv.conf`、能装 iptables"是这类工具所有网络策略的共同失效点。clawk 的解法是把过滤放在 guest 内核之外。整台 VM 的三层（网关、DHCP、DNS、NAT）都是 daemon 进程里的 gVisor 用户态协议栈，出向连接在拨号之前先查 allowlist。补丁打在那个 gvisor-tap-vsock 分支上（`go.mod:5-7` 用 `replace` 指过去），挂钩点是四条：出向 TCP SYN、UDP 流、ICMP echo，以及 DNS 应答（`ARCHITECTURE.md:51-57`）。除了这几类，其它 IP 协议根本不转发（`SECURITY.md:11-14`）。

内置白名单 `DefaultAllowedDomains`（`internal/config/types.go:230-379`）有 139 条不重复域名，30 条是 `*.` 前缀的通配。五类分布是：AI 服务 16 条，包管理器 53 条，代码托管与镜像仓库 20 条，云基础设施 34 条，发行版源 16 条。这份清单也划出了它防什么、不防什么：`github.com` 与 `*.github.com` 都在里面。

规则语义有三条，都跟直觉不一样：

`allow` 只按目的地判，覆盖所有协议和端口，所以写 `example.com` 而不是 `https://example.com:443`；`block` 拒绝一个域名及其全部子域，压过任何 allow 且不提示；删规则只有一个动词 `clawk network remove`，allow 被删回到"默认拒绝并询问"，block 被删回到不再自动拒绝（`docs/networking.md:16-20`）。

判定不靠静态 IP 表。allowlist 里挂着三张运行时集合：`resolved` 由周期 DNS 查询白名单模式得到，每个 IP 记着是哪个名字证明的；`observed` 装的是 guest 自己经 gvproxy 解析出来的 IP；`granted` 是人在闸口上放行得到的 IP。通配匹配实际靠第二张表工作；第一张定期重建，所以内容分发网络（CDN）换 IP 不会打断（`internal/netfilter/acl.go:25-40`）。

被拒的记录按"guest 刚解析过的那个主机名"归因，`clawk network denials` 于是读起来像一份 agent 想去哪里的日志。这份账本按目的地聚合、最新优先、最多 256 个主机（超了淘汰最旧的），每份 `--json` 输出都带一个 `schema`（模式）字段，同一模式版本内只加字段、不删不改名（`docs/commands.md:36-44`）。

闸口（`internal/netfilter/gate.go`）是这份 deny-by-default 上唯一的可协商处：

- 只有当至少有一个决策方订阅时才生效。没有 UI 挂着，`Decide` 立刻返回拒绝，行为与加这个功能之前完全一致——是运行 UI 这件事打开了交互模式（`gate.go:21-25`）。
- 同一目的地 IP 的多个连接合并成一个提示，并发挂起上限 16，超过就 fail-closed，不排队等人。
- 30 秒没答案算拒绝。
- 文件里写下的 `deny` 永远走不到闸口：它算护栏，不算一次询问（`acl.go:50-53`）。

终端侧的决策方是 `clawk network watch`，六个键：单次放行、本会话放行、永久放行并写进策略、`1` 键一小时内全通、拒绝、把整个域名连同子域永久拉黑。帮助文本提到 macOS 菜单栏应用提供同样的原生弹窗控制；那个应用不在这个仓库里，`clawkwork` 组织下也只有 4 个仓库（clawk、gvproxy 分支、homebrew-tap、p9）。菜单栏这条按"代码与注释声称存在"记录，本文未独立核实。

命名策略叠在白名单下面。`network ( use default oisd corp-egress )` 按低到前列链；`policy <name> ( … )` 块可以带 `source "<url>"` 拉外部黑名单，hosts、EasyList、uBlock 三种格式都吃，`@@` 例外行转成 allow，超过 `refresh` 就重取。没有 `use` 行等于 `use default`，即那份 139 条内置清单；显式写了却不带 `default`，就是彻底放弃内置白名单。

转发是双向的，两条路完全不同。出向 `clawk forward add` 是 gvproxy 在宿主 loopback 上的绑定，VM 启动时定死，改配置要重开。入向 `clawk forward add-reverse` 做不到这样：guest 进程拨 `127.0.0.1` 只会到 guest 自己的 loopback，那儿没有任何路由通向宿主。所以端口由 guest agent 自己绑，每个连接经 vsock 隧道回 daemon，daemon 先拿这个端口号去比对沙箱配置里的集合，再去拨宿主服务；集合的变更由 daemon 推下去，因此能作用在跑着的 guest 上。入向这条路 vz-only，出向的 `forward add` 两边都有；firecracker 的 vsock 是单向的（`ARCHITECTURE.md:66-75`）。

`docs/networking.md` 里唯一标着 Recipe 的小节，讲的是 Claude Code 的 JetBrains / VS Code 插件。做法是把宿主的 `~/.claude/ide` 只读共享进去，再反向转发锁文件名里的那个端口。沙箱里的 `claude` 于是能像在本机一样连上集成开发环境（IDE）。端口随编辑器窗口变，而反向转发是热生效的，重跑一次 `add-reverse` 就够（`docs/networking.md:134-159`）。串口 `clawk serial add` 复用了同一形状，差别只在宿主侧开的是真 tty 而不是套接字；把宿主打开与 guest 打开绑在一起还有个副作用——开串口会拉 DTR，而板子的复位脉冲正是上传时序等的那一下。

README 里关于失效边界最直白的一句是：

> the allow-list blocks connections to *unknown* servers, not to ones you've allowed: github.com is pre-allowed and the forwarded ssh-agent can push, so treat anything the agent can read as something it could publish.

翻成中文：被放行的目的地照样能推送，转发的 ssh-agent 确实能签名，而 `github.com` 本来就在内置清单里。所以 agent 读得到的东西，等于它发得出去的东西。

## 进 guest 的路只有一条

DESIGN 的措辞是 `No agent in the guest we don't control.`（`DESIGN.md:23`）。落到实现里是：没有 sshd、没有 cloud-init、没有 systemd，PID 1 是 `clawk-init`，控制面只有 `clawk-pty-agent` 一个监听者。固定端口表集中在两处注释里（`internal/revfwd/revfwd.go:45-46`、`internal/sandbox/shares.go:305-310`），常量各自可查：

| 端口 | 用途 | 定案位置 |
|:---|:---|:---|
| 1024 | pty-agent，唯一的进入路径 | `internal/sandbox/firecracker_linux.go:61` |
| 1025 | time-sync，宿主睡眠唤醒后校时 | `internal/cli/timesync_sender_darwin.go:45` |
| 1026 | ssh-agent 转发，密钥不进 VM | `internal/cli/sshagent_proxy_darwin.go:24` |
| 1027 | mem-report，气球与 idle 看门狗的输入 | `machine/vz/memreport.go:20` |
| 1028 | 反向转发 | `internal/revfwd/revfwd.go:47` |
| 1100 起 | 9p 缓存服务，每份一个端口 | `internal/sandbox/shares.go:310` |

端口选在 1100 起是给未来留余量，注释里点名了不能撞的五个固定值。

attach 的语义是 container-exec：每次连接在 guest 里起一个新子进程，断开就拆掉，不是一根长活的 TTY。敢这么做是因为 agent 的恢复不靠进程，靠盘上状态。vz 侧还有个中间层：`Machine.VSock()` 是 daemon 里那个活 VM 句柄上的方法，短命 CLI 拨不到，所以 daemon 额外开一个宿主 Unix socket（`agent.sock`）桥到 guest 的 1024；firecracker 侧则直接跑它的 hybrid-vsock `CONNECT <port>` 握手（`DESIGN.md:99-108`）。

凭据这块分两种处理。ssh-agent 是**转发**，签名留在宿主；Claude 的 OAuth 令牌和 `files ( … )` 里的秘密是**推进去**的，属于用户明确选择。

环境变量的处理更严：`env ( … )` 里声明的名字进沙箱记录，值不落盘——它只在创建/up 时从宿主 shell 读，写进 guest 的 `/etc/profile.d/99-clawk-env.sh`（`internal/config/types.go:629-637`）。v0.4.0 修了一个方向很危险的细节：声明的 `env` 必须无条件压过 clawk 自己的同名变量，解析失败也照样压。在那之前，一个指向第三方网关的沙箱会拿到 clawk 的 Anthropic 令牌，当作授权头 `Authorization` 发出去（`CHANGELOG.md:178-198`）。MCP 服务器同理：凭据值不进 `clawk.mod`、不进渲染给 guest 的配置，只在 attach 时进 runner 的进程环境。URL 里内嵌凭据的写法直接拒绝（`docs/mcp.md:62`）。

## 一次 ticket 的完整流转

一个跨三个仓库的工单 `INFRA-123`，从进门到收工是这样的（路径按 `docs/ticket-mode.md` 与 `docs/commands.md`）：

1. `cd ~/code/my-workspace && clawk work INFRA-123`。CLI 读那个带 `includes ( … )` 的 `clawk.mod` 块，形状大致是下面这个示例（取自 README，去掉了 `mcp` 与 `agent` 两块）：

   ```text
   sandbox my-project (
       vm (
           cpu    4
           memory 8GiB
           image  golang:1.25
       )
       network ( allow api.example.com )
       forwards ( 3000 )
       env ( DATABASE_URL )
       on create ( "go mod download" )
   )
   ```

   读它是创建时的一次性动作：模板被快照进沙箱记录，之后再改这个文件不影响已经存在的沙箱。
2. 每个仓库在 `~/.clawk/namespaces/default/worktrees/INFRA-123/` 下开一个 worktree，分支同名 `INFRA-123`；沙箱记录写入 `DesiredState`；`provider.Start` 拉起 `__vzd`，daemon 建 rootfs（同一镜像的话是一次 reflink 克隆）、起 gvproxy 与三个代理、开机、等 1024 回话。
3. claude 经 `agent.sock` → vsock 1024 进去，在同一个 VM 里的三个 worktree 上工作。它登录的用户是 `agent`，root 靠 `clawk-init` 写下的 `/etc/sudoers.d/90-clawk` 那行 NOPASSWD 兑现；装包、起服务、跑测试都不问你，因为边界已经在机器外面。
4. 你 `Ctrl+C` 退出 attach：guest 里那个子进程被拆掉，VM 继续跑。回来时在任何目录 `clawk attach INFRA-123` 都行——attach 不创建、不重读模板，只恢复。
5. 三小时后你去吃饭，没 detach 也没活动：若这台沙箱分开写了 `memory` 与 `memory_max`，气球先把它压回基线（本文示例只写了 `memory`，那是固定大小，没有气球行程）；满 30 分钟合取条件后 daemon 记 `stop_reason: idle` 并停机，端口转发一起消失。你回来 `clawk attach`，它按 `down` 加 `up` 的语义重启，`on up` 重跑。
6. 代码改完 `clawk pr INFRA-123`：推分支、每个仓库开一个互相链接的 PR，需要 `gh`。重跑安全——已存在的 PR 会被找到并复用，相对 base 没有改动的仓库跳过，PR 描述留空。`clawk status` 里那列 PR 状态是从 `gh` 现读的，落在磁盘记录上的 `Status` 只是个 60 秒缓存（`internal/pr/status.go:1-6`）。
7. 某个仓库合并了还要接着改：`clawk worktree add INFRA-123 some-repo` 会给出 `INFRA-123-2` 而不是撞车，`worktree rebase` 把它变基到刚合并的默认分支上，各仓库进度互不牵连。
8. 收工 `clawk destroy INFRA-123`：删 VM、worktree 和网络规则；有脏或未推送的 worktree 会先警告，`-f` 才强推。会话历史与记忆留在宿主上。

历史能留住靠的是另一个包。`internal/sessions` 把一个项目的 Claude Code 会话记录当成 git 仓库来管：`~/.clawk/history/<projectID>.git` 是裸库，`main` 是累积的规范历史；每个沙箱从自己的分支 `vm/<sandbox>` 检出到那个已经被挂成 `~/.claude` 的宿主目录；开机时把 `main` 折进沙箱分支，所以同一项目的新沙箱在 resume 选择器里看得见之前的对话，关机时反向合回 `main`。被跟踪的只有对话与 per-project memory，密钥与宿主种进去的配置由 `Prepare` 写下的 `.gitignore` 排除在外。这一条也是 vz-only（`internal/sessions/sessions.go:1-24`）。

## 加装又撤回：9p 共享工具链缓存

v0.2.0 换成自写的 9p 服务端，v0.3.0 又整段撤掉，两次的理由都留在注释里。

v0.1 时代，Go module 缓存和 Cargo registry 从宿主目录挂进每台 VM，走 Apple 的 virtio-fs。这条路在多个沙箱并行时会打死宿主。Virtualization.framework 为 guest 摸过的每个 inode 缓存一个打开的宿主文件描述符，而且释放不可靠（`internal/ninep/ninep.go:6-16` 写明 Apple 的 `FB13640480` 到 2026 年仍未修）。`find ./vendor` 或者一次跨共享模块缓存的 `go build ./...`，就能把 `com.apple.Virtualization.VirtualMachine` 的 fd 数顶过系统级 `kern.maxfiles`。接下来那次 mmap 页入拿到 ENFILE，变 SIGBUS；如果死的是 1 号进程 launchd，整机以 "initproc exited" panic 重启。

v0.2.0 的解法是换协议不换思路：自己写一个 9p2000.L 服务端当普通宿主进程。它只为 guest 当前真正打开、还没 clunk 的 fid 持有描述符，于是文件描述符用量跟着活跃程度走，而不是跟着文件总数走。guest 侧内核为此带 `CONFIG_NET_9P_FD`，走 vsock 而不是 virtio-fs。跨沙箱的写回去重顺带保住了（`internal/ninep/ninep.go:17-22`）。

v0.3.0 把它撤了，原因不在性能。Go 的模块缓存和 Cargo 的 registry 依赖文件锁、只读与原子重命名语义，而 9p-over-vsock 满足不了这些语义。表现是校验和不匹配的模块失败、`EACCES`、卡住的锁、写了一半的缓存条目。结论是"每台 VM 重新下载一套依赖，比调试一个坏掉的缓存便宜"（`internal/sandbox/shares.go:312-325`、`CHANGELOG.md:315-323`）。

这次回退有三处可读的后遗症，都留在代码里。第一处，默认根盘从 8 GiB 提到 32 GiB，因为缓存改落到 rootfs 上，8 GiB 会写到一半就满。第二处，`ToolchainCachesEnabled` 这个常量现在是 `false`，而四份缓存挂载 spec 保持编译、保持被测试，注释写明"9p 传输硬化后挂回来"。第三处，32 GiB 也不是免费的。ext4 的 inode 表按上限的 1/64 预先写出来，所以一个构建好的 rootfs 实打实占约 512 MiB 宿主磁盘，而不是 128 MiB。这笔开销按"镜像加大小"的缓存项各付一次，每台 VM 的盘再从它 reflink。

顺带一句：`clawk image gc` 用来清那些被升级淘汰掉的旧盘，v0.3.0 之后第一次 `up` 会因为缓存键变了而重建 rootfs（大镜像是几分钟量级的一次性开销）。

## 两个 provider 的分岔

`vz`（macOS，默认）和 `firecracker`（Linux，实验性）共享同一套 OCI rootfs、同一个 vsock agent、同一份出网白名单。两者的差异不在性能，在能力集合。对照 `ARCHITECTURE.md:127-139` 与 `docs/commands.md:148-163`：

| | vz | firecracker |
|:---|:---|:---|
| hypervisor | Virtualization.framework（cgo，Code-Hex/vz） | `firecracker` 加 `/dev/kvm`，实测跟的是 v1.12 |
| worktree | virtio-fs 实时挂载，宿主编辑立刻可见 | 自己在用户态造一块 ext4 盘，挂到 `/workspace`，宿主编辑不传导 |
| 网络设备 | 无（fd NIC 直连 gvproxy） | 一个网桥加两张 TAP，默认放在每沙箱自己的非特权 user/netns 里 |
| 会话可观测 | 能 | 不能，所以 idle 停机只在 macOS 生效 |
| ssh-agent 转发 | 有 | 无 |
| 反向转发 | 有 | 无，vsock 单向，CLI 会明说而不是静默不做 |
| 分阶段钩子、宿主推文件 | 有 | 无 |
| 会话历史进 git | 有 | 未接，需要先补一次 copy-out |

Linux 侧的权限模型另有一层设计：造网桥和 TAP 要 `CAP_NET_ADMIN`，clawk 不用 sudo 拿到它——在你自己拥有的命名空间里你就是自己网络=root。所以允许非特权用户命名空间的宿主上，起一台沙箱全程零特权操作，宿主上也不出现任何 clawk 网卡。被禁时退回 bridge 模式，用 `sudo ip` 建设备，每台沙箱最多提示一次、绝不在后台 daemon 里提示；Ubuntu 24.04 之后常见，因为 AppArmor 默认禁非特权 userns，一条 `sysctl` 可解（`docs/commands.md:190-221`）。`CLAWK_NET_MODE=rootless` 能让它在这种机器上直接失败而不偷偷退回 sudo。

## 版本边界：哪项能力从哪个版本起

浅克隆（`git clone --depth 1`）只看得到今天，而 clawk 五个星期里改过好几件用户可见的事。按 `CHANGELOG.md` 排一遍，方便对号入座：

| 版本 | 发布日 | 与本文相关的变化 |
|:---|:---|:---|
| v0.1.0 | 2026-07-07 | 首个公开版：两种进入方式、默认全自主、用户态出网闸、OCI 转 ext4、气球、宿主侧状态活过 VM；`pause` / `snapshot` / `resume` 三档停机与"快照失配就退回冷启动"也在这版 |
| v0.2.0 | 2026-07-13 | 默认 guest 内核换成自带 9p-over-vsock 的 clawk 内核；工具链缓存改走 9p |
| v0.3.0 | 2026-08-05 | 反向转发；Linux rootless；发行二进制不再需要 Go；默认盘 8 → 32 GiB；撤回 9p 缓存共享；firecracker 的 worktree 改独立盘；恢复快照前不再重刷 rootfs |
| v0.4.0 | 2026-08-13 | swap 设备；串口；`mcp ( … )`；pi runner 与 opencode 接通；每个 runner 各自一份宿主状态目录；宿主级默认值文件 |

三条最容易踩的边界：反向转发与串口要 v0.3.0 / v0.4.0 之后；`~/.config/clawk/clawk.mod` 只在 v0.4.0 之后存在；v0.3.0 之前只有 `~/.claude` 挂在宿主上，codex 的会话与登录状态会被一次普通 `down`/`up` 冲掉，而不是只有 `destroy` 才丢。

## 该不该用，从哪儿开始用

先给结论：如果你要的是"agent 在我这台机器上别乱来"，clawk 现在的形态（macOS、单用户、个人项目）已经可用；团队共用、审计级出网控制、需要 GPU 的负载，这三样它都给不了。

一条成本递增的顺序：

1. 拿一个不重要的仓库，用 `clawk run shell` 进去当普通 Linux 用一天。这一步不碰任何凭据，只验证你自己的工具链能不能在"任意 OCI 镜像当 rootfs"这个前提下工作。
2. 换 `clawk run claude`，但先不收紧网络：用 `clawk network denials` 看一周它到底想去哪儿，再决定白名单。这一步是整套设计里唯一需要你主动读日志的地方，而它给出的信息比任何策略预设都准。
3. 需要 `git push` 时再确认 ssh-agent 转发；需要 MCP 时用 `mcp ( … )` 声明，接受"只能静态凭据、URL 内嵌凭据会被拒"这个约束。
4. `clawk snapshot` 与 idle 停机一起用，把"开着一堆沙箱"变成"堆着不占内存"。注意 snapshot 的恢复是一次性的：`suspend/` 目录被下一次启动消费掉，`clawk down` 会把它连同快照一起丢掉（`DESIGN.md:171-176`）。
5. 多仓 ticket 真出现时再上 `clawk work`，因为它引入 worktree 生命周期，心智负担明显高一档。

不适合的四种情况，都能指到具体缺口：需要 GPU（整个仓库没有任何 GPU 直通相关代码或文档）；需要 Windows guest 或 Intel Mac（FAQ 直接写 No，macOS 要 14+ 且 Apple silicon）；要在 Linux 上用反向转发、ssh-agent 或分阶段钩子（v0.4.0 仍未接通）；以及把"agent 读到的都可能被发出去"当不可接受风险的人。github.com 在内置白名单里，转发的 ssh-agent 能推，所以白名单拦的是往未知地址外传，拦不住数据外流本身。

还有两个和成熟度有关的事实要摆明。仓库自己写着 Pre-1.0、版本之间会有破坏性变更（`README.md:62-65`）；CI 跑两个模块的 build / vet / test 和跨平台编译，但两个 job 都不起真 VM。端到端启动测试挡在 `TEST_GUEST_BOOT` 后面，还需要 `/dev/kvm`（`.github/workflows/ci.yml:5-7`）。也就是说"这条路径在真机器上还行不通"目前主要靠作者本机跑。

## 五道自测题

1. 为什么 allowlist 放在 guest 外面才算防篡改？guest 里改成 DNS 或加 iptables 为什么无效？
2. 一台 VM 因为 idle 停机被重启，`on up` 钩子会发生什么？为什么文档要求它幂等？
3. 默认根盘为什么从 8 GiB 提到 32 GiB？这 32 GiB 里哪一部分是宿主上真实存在的字节？
4. `clawk forward add` 和 `add-reverse` 谁的配置能热生效，为什么方向不同会导致这个差别？
5. 气球控制器为什么要看换出量（swap）的变化趋势，而不是直接看 `MemAvailable`？

## 出错时先看哪几处

四类现象各有各的排查入口，仓库里都留了现成的检查点。最常见的是前两类：起不来，和网络不通。

起不来：Linux 上先跑 `clawk doctor`，它查三件事：`firecracker` 在不在 `PATH`、`/dev/kvm` 是否可读写（缺的是 `kvm` 组）、`nsenter` 在不在（缺了不致命，会退回 bridge 模式并说明）。`/dev/kvm` 那类失败 firecracker 只回一句 `Permission denied (os error 13)`，`clawk up` 当前版本会把 `usermod -aG kvm` 这条修法直接打出来。Go 工具链不在检查项里：发行二进制自带 guest 侧那三个程序，`clawk doctor` 会显式说"不需要"。

网络不通：先看 `clawk status` 的 `Blocked` 行或 `clawk network denials`，它是按主机名记的；allow 一条只按目的地、覆盖全协议全端口，所以别写带 scheme 和端口的形式；黑名单型策略若拉取失败会显式报错而不是静默放行。

东西"丢了"：先分清丢在哪一层。VM 盘每次 vz 启动都从镜像重新克隆，只有宿主上那份状态目录 `state/<沙箱名>/` 里的几个 runner 家目录会活过 `destroy`；`clawk snapshot` 的内存回到挂起点，`clawk down` 会把快照一起丢；配置不匹配（改了 shares 或内存）时恢复会退回冷启动。`on create` 失败会留下 `CreatePending`，下一次 `up` 从头重跑整个阶段。

慢或莫名重启：`clawk list` 里的 `stopped (idle)` 表示是停放而不是崩溃；要常驻服务的沙箱写 `idle_timeout off`。镜像用可变 tag 时，每次重建 rootfs 都会重新解析引用，上游一动，你的 rootfs 下一次启动就跟着变了。要可复现就钉 digest，或者用本地 `docker save` 包。排障材料用 `clawk debug dump`（日志加状态），逃生口是 `clawk debug vshell`。

## 下一步读什么

每一层机制都有一份比本文更可靠的原始材料。

- 进程模型与包边界：`ARCHITECTURE.md` 全文不到 140 行，从 `How a command flows` 那节读起，它把 CLI、daemon、guest 三件套的启动顺序一次讲完。
- 内存三层：先读 `internal/cli/admission.go:13-21` 的注释（为什么必须预防），再读 `machine/vz/memreport.go:34-58`（宿主为什么需要一条自建的上报通道），最后看 `machine/vz/balloon.go` 里 `swapTrend` 的注释。
- 网络闸口：`internal/netfilter/gate.go:14-30` 是全部交互语义的出处，配 `docs/networking.md` 的动词表读；`internal/netfilter/acl.go:25-40` 说明通配为什么能工作。
- 撤回史：`internal/sandbox/shares.go:312-325` 与 `internal/ninep/ninep.go:6-22` 两段注释，加上 `CHANGELOG.md` 的 v0.2.0 与 v0.3.0 两节，构成完整的一条决策链。

再往外走一步可以对照站内 [apple/container 拆解](/posts/tech/apple-container-macos-lightweight-vm-containers/)。clawk 在没有自己发布的内核时退回 Kata 官方静态内核，而 `machine/kernel/kernel.go:12-14` 注明那正是 Apple 的 `container machine` 所引导的同一个内核；`DESIGN.md:231-232` 又说它试过基于 apple-container 的 provider 再放弃。两篇对着读，能看出"站在 Apple 的虚拟化栈上"的两条不同落点。

## 参考与复核命令

- 仓库与文档：[clawkwork/clawk](https://github.com/clawkwork/clawk)（`main`，Apache-2.0）—— [README](https://github.com/clawkwork/clawk/blob/main/README.md)、[ARCHITECTURE.md](https://github.com/clawkwork/clawk/blob/main/ARCHITECTURE.md)、[DESIGN.md](https://github.com/clawkwork/clawk/blob/main/DESIGN.md)、[SECURITY.md](https://github.com/clawkwork/clawk/blob/main/SECURITY.md)、[CHANGELOG.md](https://github.com/clawkwork/clawk/blob/main/CHANGELOG.md)
- 分册文档：[commands](https://github.com/clawkwork/clawk/blob/main/docs/commands.md)、[networking](https://github.com/clawkwork/clawk/blob/main/docs/networking.md)、[ticket-mode](https://github.com/clawkwork/clawk/blob/main/docs/ticket-mode.md)、[images](https://github.com/clawkwork/clawk/blob/main/docs/images.md)、[configuration](https://github.com/clawkwork/clawk/blob/main/docs/configuration.md)、[mcp](https://github.com/clawkwork/clawk/blob/main/docs/mcp.md)、[linux-quickstart](https://github.com/clawkwork/clawk/blob/main/docs/linux-quickstart.md)
- 上游与被改造的依赖：[containers/gvisor-tap-vsock](https://github.com/containers/gvisor-tap-vsock)（clawk 用自己的分支并打补丁）、[Microsoft/hcsshim](https://github.com/microsoft/hcsshim) 的 ext4 写入器、[Kata Containers](https://github.com/kata-containers/kata-containers)（默认 guest 内核的配置来源）、[Firecracker](https://firecracker-microvm.github.io/)
- 站内对照：[apple/container 拆解](/posts/tech/apple-container-macos-lightweight-vm-containers/)、[microsandbox 拆解](/posts/tech/microsandbox-local-microvm-runtime/)、[Microsoft MxC 沙箱执行](/posts/tech/microsoft-mxc-sandboxed-code-execution-guide/)，分别代表 macOS 原生容器、本地 microVM 运行时与策略驱动的进程级沙箱三条路线。clawk 的 README 在 "Compared to" 一节点名对标的是容器与 devcontainer、操作系统级 agent 沙箱（举的是 Anthropic 的 sandbox-runtime）、通用 VM 管理器（举的是 Lima）以及云端沙箱四类

下面几条命令能对本文最硬的那些断言重跑一遍，前两条只需要 `gh` 认证，后面的需要先 `git clone`：

```bash
# 发布节奏与仓库现状（本文写的是 2026-09-21 的快照）
gh api repos/clawkwork/clawk --jq '{st:.stargazers_count,pushed:.pushed_at,lic:.license.spdx_id}'
gh api repos/clawkwork/clawk/releases --jq '.[]|{tag:.tag_name,pub:.published_at}'
gh api 'search/issues?q=repo:clawkwork/clawk+type:issue+state:open' --jq .total_count

git clone https://github.com/clawkwork/clawk && cd clawk
git ls-files | wc -l                                    # 355：跟踪文件数
python3 - <<'EOF'                                       # 内置白名单条数：139
import re; t = open('internal/config/types.go').read()
b = re.search(r'var DefaultAllowedDomains = \[\]string\{(.*?)\n\}', t, re.S).group(1)
e = re.findall(r'"([^"]+)"', '\n'.join(re.sub(r'//.*$', '', l) for l in b.split('\n')))
print(len(e), len(set(e)), sum(x.startswith('*') for x in e))
EOF
grep -n "1024 pty-agent" internal/revfwd/revfwd.go        # 那张端口表在注释里
grep -rn "fcAgentPort = 1024\|timeSyncPort = 1025\|SSHAgentVSockPort uint32 = 1026\|agentMemPort uint32 = 1027\|VSockPort uint32 = 1028\|NinepBasePort uint32 = 1100" \
  internal/sandbox/firecracker_linux.go internal/cli/timesync_sender_darwin.go \
  internal/cli/sshagent_proxy_darwin.go machine/vz/memreport.go internal/revfwd/revfwd.go internal/sandbox/shares.go
grep -n "ToolchainCachesEnabled" internal/sandbox/shares.go | head -3   # 现在是 false
grep -n "defaultSandboxMemory\|defaultIdleTimeout" internal/cli/resources.go | head
```

维护说明：核对基线是 `main` 的 `a67d04f`（2026-08-12），GitHub 显示的最近推送是 2026-08-13。版本发布停在 v0.4.0，此外还有一个 guest 内核发布物。重看本文时优先复查五处。`DefaultAllowedDomains` 的条数与分类在 `internal/config/types.go`；firecracker 的能力缺口看 `docs/commands.md` 的 provider 表格；`ToolchainCachesEnabled` 一旦被翻回 `true`，"加装又撤回"一节要改写；idle 停机的阈值与"仅 vz"那句要同时看 `internal/cli/resources.go` 和 `docs/commands.md`；剩下的是 star 数、贡献者数、未关闭 issue 数这三组快照值。星标与提交数只作时间戳使用，不当论据。
