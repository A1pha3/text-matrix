---
title: "CubeSandbox：腾讯开源的极速、高并发、安全沙箱服务——专为 AI Agent 打造"
date: "2026-04-23T07:58:00+08:00"
slug: "cubesandbox-tencent-ai-agent-sandbox"
description: "CubeSandbox 是腾讯开源的基于 RustVMM 与 KVM 的 AI Agent 安全沙箱服务，冷启动低于 60ms、内存开销低于 5MB、内核级硬件隔离，并兼容 E2B SDK。本文从架构、原理、使用、扩展四个维度对其作全方位深入剖析。"
draft: false
categories: ["技术笔记"]
tags: ["沙箱", "AI-Agent", "KVM", "Rust", "eBPF", "腾讯云"]
---

# CubeSandbox：腾讯开源的极速、高并发、安全沙箱服务——专为 AI Agent 打造

## 学习目标

- 理解 CubeSandbox 的核心定位、适用场景及其与 Docker 容器、传统 VM 的本质差异
- 掌握 CubeSandbox 的整体架构设计与各核心组件的职责划分
- 理解基于 eBPF 的 CubeVS 网络虚拟化层的工作原理（SNAT/DNAT、会话跟踪、网络策略）
- 熟悉模板（Template）的生命周期管理（Init → Boot & Snapshot → Deploy）
- 能够在本地环境（WSL 2 或裸金属）完成 CubeSandbox 的安装与第一个 Agent 代码运行
- 了解从源码构建和多机集群部署的扩展路径

<!-- truncate -->

## 一、为什么需要 CubeSandbox？

在 AI Agent 的实际应用中，Agent 往往需要**执行大模型生成的未知代码**——这带来了一个根本性的安全问题：如何在不影响性能的前提下，实现**强隔离**，让恶意或错误的代码无法影响宿主机和其他沙箱实例？

传统的隔离方案各有缺陷：

| 方案 | 隔离级别 | 启动速度 | 内存开销 | 密度 |
|------|----------|----------|----------|------|
| Docker 容器 | 低（共享内核 Namespace） | 快（200ms） | 低 | 高 |
| 传统 VM | 高（独立内核） | 慢（秒级） | 高 | 低 |
| **CubeSandbox** | **极高（独立内核 + eBPF）** | **极速（< 60ms）** | **极低（< 5MB）** | **极高（单机数千实例）** |

Docker 容器的问题在于共享内核——容器逃逸漏洞（如 runc CVE、Dirty COW）本质上无法根除。传统 VM 虽然安全，但启动慢、内存大、成本高，难以支撑 AI Agent 场景下的高并发快速执行需求。

**CubeSandbox 正是为解决这一矛盾而生**：在 60ms 内创建一个具备完整服务能力的硬件隔离沙箱，同时保持小于 5MB 的单机实例内存开销，从而在一台普通服务器上跑起数千个相互隔离的 Agent 环境。

> **关键洞察**：CubeSandbox 之所以能做到"极速启动"，核心并非"加快开机"，而是基于**资源池化预置 + 快照克隆**——沙箱模板预先以 MicroVM 形式冷启动并打下内存快照，后续每次创建沙箱实例时直接从快照热启动，跳过完整的 OS 引导过程。

---

## 二、整体架构

### 2.1 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                         AI Agent / SDK                          │
│                    (E2B SDK — Python / JS 等)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API（兼容 E2B）
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                        CubeAPI  (Rust)                          │
│              高并发 REST API 网关，兼容 E2B 协议                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                ↓                         ↓
┌─────────────────────────┐   ┌─────────────────────────┐
│   CubeProxy (Rust)      │   │   CubeMaster (Go)       │
│  TLS 终端 + 反向代理     │   │   集群编排调度器         │
│  路由到对应沙箱实例       │   │   资源调度 + 集群状态     │
└────────────┬────────────┘   └────────────┬────────────┘
             │                              │
             │                   ┌───────────┴───────────┐
             │                   ↓                       ↓
             │         ┌─────────────────┐   ┌─────────────────┐
             │         │   Cubelet (Go)  │   │   Cubelet (Go)  │
             │         │   Node 1         │   │   Node N         │
             │         │  管理本节点所有   │   │  管理本节点所有  │
             │         │  沙箱生命周期     │   │  沙箱生命周期    │
             │         └────────┬─────────┘   └────────┬─────────┘
             │                  │                       │
             │        ┌─────────┴──────────┐            │
             │        ↓                    ↓            │
             │  ┌────────────┐   ┌────────────────────┐ │
             │  │ CubeVS (eBPF)│   │ CubeHypervisor (RustVMM) │
             │  │ 网络虚拟化层 │   │ + CubeShim (容器运行时集成) │
             │  │ 内核态网络   │   │ KVM MicroVM 管理        │
             │  │ 隔离+策略   │   └────────────────────┘ │
             │  └────────────┘              │           │
             │                               ↓           │
             │                      ┌────────────────┐   │
             │                      │  MicroVM 沙箱   │   │
             │                      │  (独立内核)      │   │
             │                      └────────────────┘   │
             │                                         │
└────────────┼─────────────────────────────────────────┘
             ↓
    ┌────────────────┐
    │  宿主机网卡 eth0 │
    │  (from_world    │
    │   eBPF TC)      │
    └────────────────┘
```

### 2.2 核心组件职责

| 组件 | 语言 | 职责 |
|------|------|------|
| **CubeAPI** | Rust | 兼容 E2B 的 REST API 网关，接收 SDK 请求；只需替换 URL 环境变量即可从 E2B 无缝切换 |
| **CubeMaster** | Go | 集群编排调度器，接收 API 请求并分发到对应 Cubelet，维护资源调度与集群状态 |
| **CubeProxy** | Rust | 反向代理，兼容 E2B 协议，通过解析 Host 头中 `<port>-<sandbox_id>.<domain>` 格式将请求路由到正确沙箱；提供 mkcert TLS 和 CoreDNS 域名路由（`cube.app`）|
| **Cubelet** | Go | 计算节点本地调度组件，管理单节点所有沙箱实例的完整生命周期 |
| **CubeVS** | eBPF + Go | 基于 eBPF 内核态转发的虚拟交换机，提供网络隔离与细粒度出站流量过滤 |
| **CubeHypervisor** | Rust（基于 Cloud Hypervisor） | KVM MicroVM 管理器，负责创建和管理轻量级虚拟机 |
| **CubeShim** | Rust | 实现 containerd Shim v2 API，将沙箱集成到容器运行时生态 |

---

## 三、CubeVS 网络模型：内核态 eBPF 实现的沙箱网络隔离

这是 CubeSandbox 最有技术深度的子系统。CubeVS（Cube Virtual Switch）是专为沙箱场景设计的网络虚拟化层，由**三个 eBPF 程序**、**九个 BPF Map**和一个 **Go 控制面**组成。

> **为什么用 eBPF 而不是传统的 iptables/brctl？** 传统方案在每个报文上都会引入额外开销，且随租户数量增长而加剧。eBPF 程序挂载在内核数据路径关键位置，数据面逻辑完全在内核态执行，无需用户态上下文切换，CPU 开销极低。

### 3.1 三个 BPF 程序

| 程序 | 源文件 | 挂载点 | 方向 | 职责 |
|------|--------|--------|------|------|
| `from_cube` | `mvmtap.bpf.c` | 各 TAP 设备的 TC ingress | 沙箱 → 宿主机 | SNAT、策略检查、会话创建、ARP 代理 |
| `from_world` | `nodenic.bpf.c` | 宿主机网卡 (eth0) 的 TC ingress | 外部 → 宿主机 | 反向 NAT、端口映射代理 |
| `from_envoy` | `localgw.bpf.c` | cube-dev 的 TC egress | Overlay → 沙箱 | 将 Overlay 流量 DNAT 到沙箱 IP 并重定向至 TAP |

额外还有一个轻量程序 `filter_from_cube`，通过 **XDP** 挂载在 cube-dev 上，作为早期拒绝过滤器，在报文进入 TC 层之前丢弃未经请求的入站 TCP/UDP 报文。

### 3.2 出站流量：沙箱到外部网络

当沙箱进程发起到互联网的连接时，报文路径如下：

```
沙箱 (169.254.68.6:src_port)
  → TAP 设备
    → TC ingress: from_cube (eBPF)
      → 执行 SNAT + 网络策略 + 会话创建
        → 宿主机网卡 (eth0)
          → 外部网络
```

`from_cube` 对每个出站报文依次执行：

1. **网络策略评估**：根据目标 IP 在沙箱的 LPM Trie（`allow_out` / `deny_out` Map）中决定放行或丢弃
2. **NAT 会话创建**：将沙箱内部 IP（`169.254.68.6`）和端口替换为 SNAT 池中的 IP 及动态分配端口，同时更新 IP 和 L4 校验和
3. **重定向**：将改写后的报文发送到宿主机网卡

沙箱的内部 IP 固定为 `169.254.68.6`，网关为 `169.254.68.5`。由于网关地址在 TAP 设备的点对点链路内没有真实主机响应 ARP，CubeVS 内置了 ARP 代理——`from_cube` 拦截 ARP 请求并以 cube-dev 的 MAC 地址构造 ARP 回复，使沙箱网络栈能正常工作。

### 3.3 入站流量：外部网络到沙箱

外部回复报文（或端口映射的入站连接）到达宿主机网卡后：

```
外部网络
  → 宿主机网卡 (eth0)
    → TC ingress: from_world (eBPF)
      → 查找 ingress_sessions 反向查找表
        → 执行反向 DNAT（目标地址改写回沙箱内部）
          → TAP 设备
            → 沙箱
```

`from_world` 处理两种场景：

- **基于会话的反向 NAT**：过滤器在 `ingress_sessions` 中查找报文五元组，若匹配则重建沙箱侧原始坐标并执行反向 DNAT
- **端口映射代理**：若会话未匹配，则根据目标端口查找 `remote_port_mapping`，直接将目标 DNAT 到沙箱监听端口

### 3.4 有状态的连接跟踪

CubeVS 维护双 Map 会话跟踪：

- **`egress_sessions`**（主会话表）：Key 为沙箱侧五元组（沙箱 IP、目标 IP、沙箱端口、目标端口、协议），Value 包含 SNAT IP 和端口、TAP ifindex、时间戳、TCP 状态
- **`ingress_sessions`**（反向查找表）：Key 为外部侧五元组，Value 仅存储足以重建 `egress_sessions` Key 的信息

TCP 实现了完整的 11 种状态机（SYN_SENT、SYN_RECV、ESTABLISHED、FIN_WAIT、CLOSE_WAIT 等），精确控制不同状态的超时时间——例如 `ESTABLISHED` 可存活 3 小时，而 `SYN_SENT` 应在 1 分钟后被回收。

### 3.5 逐沙箱网络策略

每个沙箱拥有独立的 `allow_out`（允许列表）和 `deny_out`（拒绝列表）LPM Trie，评估顺序为：**允许 → 拒绝 → 默认放行**。

始终被阻止的 CIDR 段（无论策略如何配置）：

- `10.0.0.0/8`、`127.0.0.0/8`、`169.254.0.0/16`、`172.16.0.0/12`、`192.168.0.0/16`

这些在 `AddTAPDevice()` 期间被添加到 `deny_out`，且无法被允许规则覆盖，防止沙箱探测宿主机的内部网络。

---

## 四、模板生命周期：如何实现 60ms 极速冷启动？

Template（模板）是 CubeSandbox 创建实例的基础镜像和配置快照，其生命周期分为三步：

### 4.1 Init（初始化构建）

基于基础镜像（如 Ubuntu）和 Dockerfile，使用 Buildkit 等构建引擎打包出满足沙箱运行需求的 rootfs 文件系统。这一步产出标准的 OCI 镜像格式。

### 4.2 Boot & Snapshot（冷启动与快照）

将初始化的 rootfs 放入 MicroVM 中冷启动。等待系统和语言环境（如 Python、Node.js）完全加载后，对此时的**内存和状态打下快照（Snapshot）**。

> **核心原理**：快照克隆技术使得后续创建沙箱实例时，无需重新经历完整的 OS 引导和语言环境初始化，直接从快照恢复——这就是 60ms 冷启动的技术根源。

### 4.3 Deploy（注册与发布）

将打包好的 rootfs 和 Snapshot 文件注册到系统中，成为一个可用的 Template。此后即可通过该 Template 实现沙箱的**热启动（Hot Start）**。

### 4.4 使用示例

通过 CLI 从预构建镜像制作模板：

```bash
cubemastercli tpl create-from-image \
  --image ccr.ccs.tencentyun.com/ags-image/sandbox-code:latest \
  --writable-layer-size 1G \
  --expose-port 49999 \
  --expose-port 49983 \
  --probe 49999

# 监控构建进度
cubemastercli tpl watch --job-id <job_id>
```

等待模板状态变为 `READY` 后，记录输出的 `template_id` 供 SDK 使用。

---

## 五、快速开始：四步跑起第一个 Agent 沙箱

### 5.1 前置环境

CubeSandbox 需要一台开启了 KVM 的 x86_64 Linux 环境，以下任一均可：

- **Windows WSL 2**（Windows 11 22H2+，BIOS / WSL 开启嵌套虚拟化）：管理员 PowerShell 执行 `wsl --install`
- **Linux 物理机或裸金属服务器**
- **开启了嵌套虚拟化的 Linux 虚拟机**（VMware 中为虚拟机 CPU 启用 Intel VT-x/EPT）

宿主机需要安装 QEMU 和 Docker 并能正常访问互联网。

### 5.2 第一步：准备开发虚机（可选）

如果没有裸金属服务器，可以通过 dev-env 在 WSL / Linux 上启动一台一次性 OpenCloudOS 9 虚机：

```bash
git clone https://github.com/tencentcloud/CubeSandbox.git
# 国内用户：
# git clone https://cnb.cool/CubeSandbox/CubeSandbox.git

cd CubeSandbox/dev-env
./prepare_image.sh   # 仅首次：下载并初始化运行环境
./run_vm.sh          # 启动虚机，保持此终端不关

# 新开终端，进入虚机
cd CubeSandbox/dev-env && ./login.sh
```

### 5.3 第二步：安装 Cube Sandbox

在虚机内（或裸金属服务器上）执行：

```bash
# 国内用户
curl -sL https://cnb.cool/CubeSandbox/CubeSandbox/-/git/raw/master/deploy/one-click/online-install.sh | MIRROR=cn bash

# 海外用户
curl -sL https://github.com/tencentcloud/CubeSandbox/raw/master/deploy/one-click/online-install.sh | bash
```

安装组件：
- E2B 兼容 REST API 监听在 `3000` 端口
- CubeMaster、Cubelet、network-agent、CubeShim 作为宿主机进程运行
- MySQL 和 Redis 通过 Docker Compose 管理
- CubeProxy 提供 mkcert TLS 和 CoreDNS 域名路由

### 5.4 第三步：制作模板

```bash
cubemastercli tpl create-from-image \
  --image ccr.ccs.tencentyun.com/ags-image/sandbox-code:latest \
  --writable-layer-size 1G \
  --expose-port 49999 \
  --expose-port 49983 \
  --probe 49999

cubemastercli tpl watch --job-id <job_id>
# 等待模板状态变为 READY，记录 template_id
```

### 5.5 第四步：运行 Agent 代码

安装 Python SDK 并运行环境变量：

```bash
pip install e2b-code-interpreter

export E2B_API_URL="http://127.0.0.1:3000"
export E2B_API_KEY="dummy"
export CUBE_TEMPLATE_ID="<你的模板ID>"
export SSL_CERT_FILE="$(mkcert -CAROOT)/rootCA.pem"
```

运行代码——**直接使用 E2B SDK，CubeSandbox 在底层无缝接管所有请求**：

```python
import os
from e2b_code_interpreter import Sandbox  # 只需导入！无需修改任何业务代码

with Sandbox.create(template=os.environ["CUBE_TEMPLATE_ID"]) as sandbox:
    result = sandbox.run_code("""
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(0, 2 * np.pi, 100)
y = np.sin(x)

plt.figure(figsize=(10, 4))
plt.plot(x, y)
plt.title('Sin Wave from CubeSandbox')
plt.savefig('/tmp/sin_wave.png')
print('Plot saved successfully!')
result = {'plot_path': '/tmp/sin_wave.png'}
""")
    print(result)
```

---

## 六、多机集群部署

当单节点容量不足时，CubeSandbox 支持多机集群水平扩展。新增节点只需运行同样的安装脚本，CubeMaster 会自动发现并纳入新节点，完成负载调度：

```bash
# 在新节点上执行相同的安装命令
curl -sL https://cnb.cool/CubeSandbox/CubeSandbox/-/git/raw/master/deploy/one-click/online-install.sh | MIRROR=cn bash
```

CubeMaster 通过 etcd 或内置状态存储维护集群视图，自动将 API 请求分发到有可用资源的 Cubelet。

---

## 七、从源码构建

如需自定义组件、使用特定 commit 或参与开发贡献，可以从源码构建发布包：

```bash
# 克隆仓库（含子模块）
git clone --recursive https://github.com/tencentcloud/CubeSandbox.git

# 进入源码目录
cd CubeSandbox

# 编译（需要 Rust、Go 等工具链）
make build

# 或使用本地构建部署脚本
./deploy/one-click/local-build.sh
```

详细说明请参阅 `docs/guide/self-build-deploy.md`。

---

## 八、总结

CubeSandbox 解决了 AI Agent 代码执行场景中**安全与性能的矛盾**：

- **硬件级隔离**：每个 Agent 运行在独立的 MicroVM 中，拥有自己的 Guest OS 内核，彻底消除容器逃逸风险
- **极速冷启动**：基于快照克隆技术，平均冷启动时间 < 60ms，P99 < 150ms
- **极高部署密度**：单实例内存开销 < 5MB，单机可运行数千个沙箱实例
- **零成本迁移**：兼容 E2B SDK，只需替换  PROTECTED_49  环境变量即可从 E2B 切换到 CubeSandbox
- **内核态网络**：CubeVS 基于 eBPF 实现网络隔离，所有数据面逻辑在内核态执行，无用户态开销

---

## 进阶路径

- **深入 CubeVS**：阅读  PROTECTED_50  中流量路径与会话跟踪的完整实现
- **Template 定制**：学习如何制作自定义镜像和模板，满足特定语言或工具链需求
- **集群运维**：掌握多节点调度策略、资源配额管理和监控告警配置
- **参与贡献**：阅读  PROTECTED_51 ，了解如何参与开源社区贡献

---

> **参考链接**：
> - 官方文档：https://docs.cubesandbox.ai/
> - GitHub 仓库：https://github.com/TencentCloud/CubeSandbox
> - Discord 社区：https://discord.gg/kkapzDXShb

🦞 钳岳星君 · 每日自动更新
