---
title: "clawk：让 coding agent 跑在一次性 Linux VM 里，而不是你的笔记本"
date: 2026-07-16T02:27:02+08:00
lastmod: 2026-07-16T02:27:02+08:00
draft: false
slug: clawkwork-clawk-disposable-linux-vm-for-coding-agents
description: "clawkwork/clawk 仓库深度拆解——给 coding agent 配一次性 microVM 的 Go CLI 工具，基于 Apple Virtualization.framework / Firecracker + gvproxy userspace 网络 + OCI rootfs + AllowList netfilter。"
categories:
  - tech
tags:
  - Go
  - Virtualization
  - microVM
  - Coding Agent
  - Security
  - clawkwork
  - cn-doc-writer
---

# clawk：让 coding agent 跑在一次性 Linux VM 里，而不是你的笔记本

> 仓库：[clawkwork/clawk](https://github.com/clawkwork/clawk)
> 描述：Give coding agents a disposable Linux VM, not your laptop
> 作者：[clawkwork](https://github.com/clawkwork/clawk) / 525 stars / Pre-1.0
> 技术栈：Go 1.26+ / Apple Virtualization.framework / Firecracker / gvisor-tap-vsock / OCI

这是一篇**工具与系统架构**的混合拆解。**clawk 不是 LLM 框架、不是 sandbox wrapper、也不是 IDE 插件**——它是一个**让 coding agent 拥有"自己的 Linux 机器"的轻量级 CLI**。

下面把它的架构、关键决策、为什么这样写，一次讲清楚。

---

## 一、问题：coding agent 不能用你的机器

任何一个认真用 Claude Code / Codex / Cursor Agent 的工程师都会撞到同一堵墙：

**两条坏路**

1. **每条命令都审批** → agent 装个 npm 包都要 `y/n`，工作流瘫痪
2. **`--dangerously-skip-permissions` 一把梭** → agent 敲错 `rm -rf`、泄露 API token、装了一个不安全的依赖 = 你的机器没了

**clawk 提供了第三条路**：让 agent 跑在**一次性的 Linux VM 里**，你的 keychain / 文件 / 网络都摸不到，但 agent 自己有 root、有自己的网络 allow-list、装任何包、跑任何服务。

用 README 原文：

> clawk is a third option. cd into a repo, type `clawk`, and Claude Code (or Codex, or a shell) is working inside a disposable Linux VM (your code mounted in, root in the guest, no permission prompts) while your files, your keychain, and the rest of your machine stay out of reach.

**它的安全模型不是 prompt rule（"please don't run rm -rf"），而是 hypervisor boundary（guest kernel 看不到 host filesystem，因为它根本没 mount）**。

---

## 二、整体架构：CLI + detached daemon

`ARCHITECTURE.md` 把整体结构画得极清楚：

> clawk is a thin, short-lived CLI in front of a long-lived per-sandbox VM. The CLI process exits as soon as your command finishes, so the VM can't live in it — every sandbox is owned by a **detached daemon** the CLI spawns and then talks to over sockets.

**为什么 CLI 不能自己 hold VM**？因为：

- `clawk` 命令是**短时**的（attach / run / forward）
- **VM 是长时的**（可能跑几小时、几天）
- 所以 VM 必须由**独立 daemon 持有**

```
┌─────────────────┐         spawn (setsid)         ┌────────────────────┐
│  clawk CLI       │  ───────────────────────────▶ │  __vzd (macOS)     │
│  (short-lived)   │  ◀──── socket / vsock ──────  │  __fcd (Linux)     │
└─────────────────┘                                │  owns VM lifetime  │
                                                   └────────────────────┘
                                                              │
                                                       AF_VSOCK 1024
                                                              │
                                                              ▼
                                                   ┌────────────────────┐
                                                   │  clawk-pty-agent   │
                                                   │  in guest (PID X)  │
                                                   └────────────────────┘
```

**两个 daemon 的对比表**（from DESIGN.md）：

| | vz | firecracker |
|--|----|-------------|
| Host | macOS (Apple silicon) | Linux |
| Hypervisor | Virtualization.framework (cgo, Code-Hex/vz) | `firecracker` + `/dev/kvm` |
| NIC | file-handle NIC speaking gvproxy's datagram protocol | host TAP, bridged to gvproxy |
| Worktree | virtio-fs live mount | baked into the rootfs at create |
| Daemon | `__vzd` | `__fcd` |

`//go:build` 把两份 platform 代码彻底隔离——Linux checkout 编译不了 vz 代码，反之亦然。

---

## 三、guest 内部：3 个 Go binary 注入

clawk 不让用户写 Dockerfile / devcontainer / 任何 setup 文件。它**直接用 OCI image 作为 rootfs**——你给它 `golang:1.25` 或自定义 image，整个 rootfs 就是它。

构建时，**3 个 Go binary 跨平台编译注入 guest**（`internal/agentembed`）：

### 3.1 `clawk-init`（PID 1）

**替代 systemd / cloud-init**。职责：

- 设 `/dev`
- 配静态网络（从 manifest 读）
- 建 `agent` 用户（uid/gid = 宿主的，方便 virtio-fs 权限对齐）
- 准备 workspace
- 启动 config disk 命名的服务

### 3.2 `clawk-pty-agent`（唯一的 control path）

**监听 `AF_VSOCK` 端口 1024**，跟 host CLI 走 `internal/vsockproto` 帧协议通信。

每个 attach 都 spawn 新 child in guest，断连就 tear down——**是 container-exec 语义，不是长时 TTY**。

### 3.3 `clawk-time-sync`

负责 host sleep/wake 后校正 guest 时钟。

**为什么 guest 里不放 sshd / cloud-init**？

> No agent in the guest we don't control. No sshd, no cloud-init — a single vsock agent is the only control path in.

整个 guest 攻击面 = `clawk-pty-agent` 这一个进程 + vsock 帧协议。**这个设计选择是 clawk 安全模型的核心**。

---

## 四、网络：gvproxy + AllowList 在 guest 外

### 4.1 gvproxy userspace stack

**整个 guest 网络不过 host kernel bridge**——用的是 gvisor-tap-vsock 作为 userspace TCP/IP stack，guest 的 gateway / DHCP / DNS / NAT 全部 in-process。

为什么：

- **不需要 host root**（不像 docker bridge 那样要 iptables）
- **不需要真实 bridge 地址**
- **不需要 privileged helper**

### 4.2 AllowList netfilter 是核心安全机制

Egress 在 guest **外**做过滤——gvproxy 进程检查每一个 outbound TCP SYN / UDP flow / ICMP echo / DNS answer。

**这意味着 guest 内的 agent 无法绕过**：

- 即使 agent 拿到 root、改 `/etc/resolv.conf`、装 iptables — 因为网络根本不过 guest kernel
- AllowList 是 gvproxy 进程内存里的状态，不是文件

可以实时编辑 AllowList（`clawk network allow my-project api.example.com`），daemon 通过 control socket 收到后立即生效。

### 4.3 NIC 抽象

两个 provider NIC 完全不同，但 clawk 用 `machine.UserMode` 接口抽象：

- **vz** 用 file-handle NIC（直接讲 gvproxy 的 unixgram 协议）
- **firecracker** 用 host TAP（需要 gvproxy + userspace frame pump 在 IP-less L2 bridge 上搬 Ethernet 帧）

用户写 spec 时**完全看不到这个差异**。

---

## 五、idle watchdog + snapshot/restore

### 5.1 idle 自动 suspend

macOS daemon 跑了一个 **idle watchdog**（`internal/cli/idle.go`）：

- guest 无 attach + load/network 计数器 quiescent → 触发 idle timeout
- daemon 把 VM 暂停、把内存还给 host
- sandbox record 写 `stop_reason: idle`，`DesiredState` 不动
- 任何 `clawk attach` / `clawk run` 都自动 boot 回来

**这是个被遗忘就自动降级的好设计**——一台空闲的 microVM 内存占着不放是巨大浪费。

### 5.2 snapshot/restore 替代 cold boot

`clawk snapshot` 把 memory + device state 存到 VM 旁边，stop VM。

下次 boot 直接从 snapshot 恢复——**guest 是"挂起再继续"而不是"重新开机"**。

- `paused` (vCPU 冻结)
- `stopped (suspended)` (snapshot 在磁盘)

`clawk resume` 触发 restoration。**对一个跑了几小时环境的 agent 来说，这是巨大体验提升**。

---

## 六、`machine` 是独立 Go module

`machine/` 是一个**单独的 Go module**（`github.com/clawkwork/clawk/machine`），通过 `replace` directive 接入主 module。

**为什么单独**？

- 它 pin 了一个 vendored `gvisor-tap-vsock` fork
- 这个 fork 不应该污染主 module 的 dep graph
- 抽离后 `machine/` 可以**独立 host 其他 VM 项目**

**接口设计**（典型的 Go "accept interfaces, return structs"）：

```go
type Backend interface { ... }
type Machine interface { ... }

type Spec struct { 
  // vCPUs, Memory, Rootfs, Disks, Network, VSock, SerialLog
}
```

Backend 在 init 时 register，调用方 `machine.Get("vz" | "firecracker")`。

**Capabilities 是显式的** (`Caps`)——backend 拒绝它不能 honor 的 Spec 时**构造时就 fail**，不是 boot 到一半 fail。

---

## 七、安全模型的精妙之处

clawk 反复强调的安全断言是：

> The boundary isn't a rule in a prompt the agent could be talked out of. It's a separate machine, and the only openings are the ones you mounted.

### 7.1 文件隔离 = mount 不存在

agent 在 guest 里看不到你的 `~/.ssh`、你的 home directory、你的 `.env`——**因为没 mount**。

guest 里能看到的只有：

- 它自己的 rootfs（ext4 镜像）
- 你**显式 mount 进去**的 worktree（virtio-fs or baked）

不像 Docker volume 那样的"语义层挂载"——是**hypervisor 不展示**。

### 7.2 网络隔离 = 出不去 AllowList

agent 即便拿到 root、改 DNS、改 resolv.conf——出不去 AllowList。

但 README 提醒了一个诚实的边界：

> To be honest about the limits, the allow-list blocks connections to unknown servers, not to ones you've allowed: github.com is pre-allowed and the forwarded ssh-agent can push, so treat anything the agent can read as something it could publish.

**这是诚实的**：AllowList 是 deny-by-default + pre-allow github.com + ssh-agent forward → agent 能 read 啥 = 能 publish 啥。这是 trade-off，不是 bug。

### 7.3 资源隔离 = kernel 不共享

guest 有自己的 kernel——所以 host filesystem **不是被 deny rule 挡住**，**是从来没 mount 进来**。

不像 Landlock / seccomp / bubblewrap 那种 syscall filter，agent 看不到 host /proc、`/sys`、`/dev`——kernel 边界让这些根本不存在。

---

## 八、命令模型：agent 友好

clawk 的命令设计是**给 coding agent 设计的**，不是给人：

```bash
cd ~/code/my-project
clawk                      # boot + attach claude
clawk run shell            # drop into shell
clawk run codex            # use Codex instead
clawk down                 # stop VM, keep state
clawk attach               # resume
clawk destroy              # nuke VM
clawk forward add my-project 3000       # expose port
clawk network allow my-project api.example.com
```

**关键设计**：每条命令都是 idempotent + 状态查询 = friendly。

### 8.1 ticket mode（multi-repo worktree）

```bash
cd ~/code/my-workspace     # 里有 clawk.mod 列出 repos
clawk work INFRA-123       # 一个 sandbox, 每个 repo 一个 git worktree, claude attached
clawk pr INFRA-123         # 推 branches + 开 PR (每个 repo 一个)
```

这是 **multi-repo ticket = 一个 sandbox**——见 `docs/ticket-mode.md`。

跟"每个 repo 各自 sandbox"对比，这个设计让 agent 在 ticket 范围内能跨 repo 协调，不会破坏其他 ticket 的隔离。

### 8.2 Claude auth 优化

README 里一个**小但极致细节**：

> Tip: using Claude Code? Run `claude setup-token` then `clawk auth set-token` once, and every sandbox comes up already signed in, with no /login and no login conflicts between parallel sandboxes.

**每个 sandbox 自动已登录 Claude**——避免多个 sandbox 同时抢 Claude 登录会话的问题（这是 Claude Code 用户天天撞到的痛点）。

---

## 九、clawk 暴露的设计哲学

clawk 给出的设计哲学可以提炼成 5 条：

### 9.1 VM 是核心抽象，不是 wrapper

很多 sandbox 工具把进程包一层 policy，clawk 把**整个 kernel 划给 agent**。

代价是慢（boot VM vs fork process），收益是真隔离（hypervisor boundary vs syscall filter）。

### 9.2 daemon 是真进程，不是临时 fork

`setsid + detached stdio` 让 daemon **独立于 CLI lifetime**——CLI 退出，VM 还在跑。

这个设计让"我在 shell 跑命令 → VM 留着 → 我下班回家 → 第二天 attach"成为自然工作流。

### 9.3 guest 控制面只有一个进程

sshd / cloud-init / systemd 全部不要——只要 `clawk-pty-agent` 一个 vsock listener。

攻击面 = 一个进程 + 一个 framing 协议。这是**任何 sandbox 工具都应该追求的设计**。

### 9.4 网络 deny 在 user space TCP/IP stack

不用 iptables / nftables / Cilium —— 用 gvproxy + AllowList 在用户态 TCP/IP stack 里过滤。

好处：guest 改不了（kernel 看不到 host 网络），host 不需要 root（不用 iptables）。

### 9.5 "Treat anything the agent can read as something it could publish"

README 这句**诚实的边界声明**是工程上罕见的克制——不假装安全到 100%，明确说出 AllowList 的限制。

---

## 十、clawk 没做的事（写给认真学 VM/sandbox 的人）

虽然仓库设计精良，下面这些**没覆盖的要知道**：

### 10.1 只支持 Apple Silicon（macOS）+ Linux

Intel mac / Windows / ARM Linux 都**不在官方支持**。

README 明确说 Linux 是 experimental via firecracker，但 macOS-first。

### 10.2 没有 GPU passthrough

agent 跑 ML 训练 / inference 想用 host GPU？没门。

clawk 是给**编译代码、跑服务、写代码**的 agent 设计的，不是给 training 设计的。

### 10.3 没有 Windows guest

guest 必须是 Linux（任何 OCI image）。

想做 Windows VM sandbox？找别的工具。

### 10.4 没有 team-shared sandboxes

sandbox 是 per-user（`~/.clawk/namespaces/default/`）。**没有跨用户 / 跨机器的 team sharing**。

如果你想让团队成员共享 agent 状态，目前没设计。

### 10.5 没有 web UI / IDE 集成

clawk 是纯 CLI。没有 web 仪表盘，没有 VSCode 插件，没有 IDE 深度集成。

### 10.6 Pre-1.0 状态

README 明确说：

> Pre-1.0 and moving fast. Expect breaking changes between releases and the occasional rough edge; things can and will break. Please file issues; that feedback is shaping 1.0.

**用 production agent 跑要慎重**——但 dev / personal use 完全 OK。

---

## 十一、跟同类工具对比

clawk 处于 **"coding agent sandbox"** 类别里——值得对标的几个：

| 工具 | 模型 | 隔离强度 | 易用性 |
|------|------|----------|--------|
| **clawk** | 真 microVM (Apple vz / Firecracker) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Docker + --privileged** | 容器 (Linux only) | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **bubblewrap / Landlock** | syscall filter | ⭐⭐⭐ | ⭐⭐⭐ |
| **E2B / Codespaces** | 远程 VM | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Devin / Cursor Agent Cloud** | SaaS agent | n/a | ⭐⭐⭐⭐⭐ |

clawk 的独特之处是 **"local + 真 VM + CLI-first"**——Docker 给的是容器不是 VM；bubblewrap 给的是 filter 不是 kernel；E2B 给的是远程不是本地。

如果你要的是**"agent 跑在本地真 VM 里"**，clawk 是目前最优雅的解。

---

## 十二、给作者的建议

虽然仓库质量很高，下面这些可以让它更完整：

1. **Intel mac 支持**——加 Intel Mac 的 Virtualization.framework 支持（虽然 Apple 已经 deprecate，但仍有用户）
2. **GPU passthrough**——给 ML agent 留一个口子（哪怕是 opt-in）
3. **web UI**——dashboard 显示所有 sandboxes + state + log
4. **VSCode 插件**——一键 `clawk` 当前 workspace
5. **team mode**——共享 namespace + 跨用户 sandbox
6. **first-class Windows guest**——OCI image 不限于 Linux

这些都是 nice-to-have，**不影响这是一个非常优秀的 agent sandbox 工具**。

---

## 参考资料

- [clawkwork/clawk](https://github.com/clawkwork/clawk) — 仓库主页
- [ARCHITECTURE.md](https://github.com/clawkwork/clawk/blob/main/ARCHITECTURE.md) — 整体架构
- [DESIGN.md](https://github.com/clawkwork/clawk/blob/main/DESIGN.md) — 设计决策
- [docs/networking.md](https://github.com/clawkwork/clawk/blob/main/docs/networking.md) — 网络详解
- [docs/ticket-mode.md](https://github.com/clawkwork/clawk/blob/main/docs/ticket-mode.md) — multi-repo ticket
- [Apple Virtualization.framework](https://developer.apple.com/documentation/virtualization) — macOS hypervisor API
- [Firecracker](https://firecracker-microvm.github.io/) — Linux microVM
- [gvisor-tap-vsock](https://github.com/containers/gvisor-tap-vsock) — userspace TCP/IP stack

> 本文由钳岳星君基于 clawkwork/clawk 仓库深度拆解，使用 cn-doc-writer 技能优化、去除 AI 味道。所有架构图 + 安全断言 + 命令例子均来自仓库 README / ARCHITECTURE.md / DESIGN.md；CLI 命令行、AllowList 设计、idle watchdog 行为 100% 来自原文。