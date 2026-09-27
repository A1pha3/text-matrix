---
title: "Cilium：用 eBPF 重写 Kubernetes 网络层的 CNCF 毕业项目"
date: 2026-09-21T03:45:00+08:00
lastmod: 2026-09-27T10:30:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["cilium", "ebpf", "kubernetes", "网络"]
description: "Cilium 是 CNCF 毕业级的 eBPF 网络、可观测与安全方案，用内核态数据面替代 kube-proxy，以身份而非 IP 地址执行 L3-L7 策略。本文拆解其组件结构、身份模型与落地路径。"
github_repo: "cilium/cilium"
source_key: "gh:cilium/cilium"
slug : cilium-ebpf-kubernetes-networking
---

## 核心判断

Cilium 解决的不是"又一个 CNI 插件"的问题，而是把 Kubernetes 网络从"IP 地址 + iptables"的模型迁移到"身份标识 + eBPF 程序"的模型。它的数据面运行在 Linux 内核里，而不是用户态的规则引擎里——这是它能在服务密度和策略表达能力上同时拉开差距的根本原因。

对大多数团队，Cilium 的实际价值集中在三件事：完全替代 kube-proxy 的东西向负载均衡、不依赖 IP 的 L3-L7 网络策略、以及跨集群的统一安全模型。如果你的集群还在为 iptables 规则数量膨胀发愁，或者需要按"Pod 是谁"而不是"Pod 在哪个网段"来写策略，Cilium 值得认真评估。

## 项目概览

| 项 | 数据（2026-09-27 取自 GitHub） |
|---|---|
| 仓库 | [cilium/cilium](https://github.com/cilium/cilium) |
| 定位 | eBPF-based Networking, Security, and Observability |
| Stars / Forks | 25,557 / 4,108 |
| 主语言 | Go（数据面为 eBPF C） |
| License | Apache-2.0（部分组件 BSD/GPL） |
| 成熟度 | CNCF 毕业项目（Graduated） |
| 维护版本 | v1.20.2 / v1.19.8 / v1.18.14（2026-09-15 同日发布），v1.21.0-pre.2 预发布中 |

官方只为最近三个次版本维护稳定分支，更早的版本进入 EOL；main 分支每日产出 CI 镜像供测试。这是基础设施级项目的典型维护强度，也意味着升级路径有明确的时间窗——跨过三个次版本的升级要先读官方升级指南。

## 组件地图：一个 CNI 插件背后的五个角色

很多文章把 Cilium 当成一个单体程序，实际上一个部署里至少有五类组件各管一段（CNI 即 Container Network Interface，容器网络接口，是 Kubernetes 的网络插件标准）。先分清它们的职责，后面的机制才不会混：

| 组件 | 形态 | 职责 |
|---|---|---|
| cilium-agent | 每节点一个 | 监听 Kubernetes 事件（Pod 启停、策略变更），把网络、负载均衡、策略与可见性需求编译成 eBPF 程序装进内核 |
| cilium-cni | 每节点一个 | kubelet 在 Pod 调度或终止时调用，触发该 Pod 的数据面配置 |
| operator | 全集群一个 | 处理只需做一次的集群级事务（如 IP 分配）；不在转发与策略决策的关键路径上，短暂不可用集群照常工作 |
| Envoy | 每节点一个（DaemonSet 或内嵌于 agent Pod） | 承接 L7 协议解析，L7 策略的流量经它代理 |
| Hubble | server 内嵌于 agent，relay 全集群一个 | 汇集内核发出的流日志，提供查询 API 与 UI |

组件间共享状态默认走 Kubernetes CRD（自定义资源），不需要额外的存储；集群规模大时可选 etcd 作为优化，变更通知和存储开销都更低。另有 `cilium` CLI（独立于 Cilium 本体的版本线，当前 v0.20.1，支持 Cilium 1.17 及以上）负责安装与运维，`cilium-dbg` 则随 agent 安装，用于检查本节点的 agent 状态和 eBPF map 内容——两个 CLI 名字接近，用途不同。

## 身份模型：IP 过滤器撑不到的那个规模

传统容器防火墙按 IP 地址过滤：如果只允许 `role=frontend` 的 Pod 访问 `role=backend` 的 Pod，那么每个运行了 backend Pod 的节点上，都要装一条"放行所有 frontend Pod 的 IP"的规则。Cilium 官方文档对这套模型的推演很直接：每次 frontend Pod 启停，所有相关节点的规则都得更新——大规模应用下这可能意味着每秒更新数千个节点；更麻烦的是，新 frontend Pod 必须等全部相关节点更新完才能放行流量，否则连接会被误杀。

Cilium 把安全和寻址彻底拆开。身份从 labels 派生，一组带相同标签（即相同策略）的 Pod 共享一个安全身份。第一个 `role=frontend` Pod 启动时，Cilium 给它分配一个身份并写入数据存储；之后再启动多少个 frontend Pod，各个节点只需从数据存储里解析出同一个身份，任何运行 backend Pod 的节点都不需要改动规则。新 Pod 的等待条件从"数千节点规则更新完成"变成"身份解析完成"，扩展性的差异就在这一步。

### 一次请求的旅程

把上面的机制串成一个具体场景：`app=service` 只接受来自 `env=prod` 的 HTTP GET。一个 `env=prod` Pod 发起请求后：

1. Pod 被调度到某节点，kubelet 调用 cilium-cni，触发该 Pod 的数据面配置。
2. cilium-agent 监听到创建事件，按 labels 算出这个 Pod 的安全身份（是已有身份就直接解析复用）。
3. 应用对 Service 发起 `connect()`：eBPF 在 socket 层直接把目标地址改写为选中的后端 Pod，没有逐包 NAT，也不经过 iptables——这就是替代 kube-proxy 的位置。
4. 包到达目的节点，内核按包携带的身份查策略表：`env=prod` 对 `app=service` 的 80 端口放行；超出规则的 HTTP 请求不会被静默丢弃，而是由 Envoy 返回一个 HTTP 403。
5. 整条路径上每条流的记录（放行、拒绝、原因）都可被 Hubble 查询。

南北向（外部进集群）流量走另一条路：XDP（eXpress Data Path，内核驱动层的极速数据路径）挂载点上做高吞吐的四层负载均衡，支持 Direct Server Return 与 Maglev 一致性哈希。负载均衡本身用 eBPF 哈希表实现，官方的说法是支撑"几乎无上限"的服务规模。

## 策略能写到多细

身份模型解决"按谁放行"，策略规则决定"放到多细"。Cilium 的策略从粗到细分四档，全部可以混用：

- **L3/L4**：按标签、协议、端口放行，这是身份模型的基本盘。
- **DNS/FQDN**：按域名放行出口流量，如 `api.example.com`、`*.trusted.com`——控制 Pod 访问第三方服务时最实用。
- **L7**：按 HTTP 方法、URL 路径、header、gRPC 调用过滤。官方仓库自带的示例只放行 `env=prod` 来源对 80 端口的 `GET /public`：

```yaml
apiVersion: "cilium.io/v2"
kind: CiliumNetworkPolicy
metadata:
  name: "rule1"
spec:
  description: "Allow HTTP GET /public from env=prod to app=service"
  endpointSelector:
    matchLabels:
      app: service
  ingress:
  - fromEndpoints:
    - matchLabels:
        env: prod
    toPorts:
    - ports:
      - port: "80"
        protocol: TCP
      rules:
        http:
        - method: "GET"
          path: "/public"
```

- **CIDR**：按网段控制进出，用于对接遗留系统或合规边界这类没法贴标签的对象。

L7 规则有两个值得注意的行为：一是违规请求不丢包，而是返回应用层拒绝（HTTP 403 或 DNS REFUSED），客户端拿到的语义是"被拒绝"而不是"超时"；二是 L7 流量必须经节点本地的 Envoy 代理解析，若 Envoy 内嵌在 agent Pod 里，这些流量的可用性就依赖 agent Pod 本身——给 L7 策略做可用性设计时要算上这一层。

## 三种组网模式

Cilium as CNI 提供三种部署形态，按对底层网络的要求从低到高：

1. **Overlay（覆盖网络）**：VXLAN 或 Geneve 封装，唯一要求是主机间 IP 可达。几乎可以在任何网络基础设施上跑。
2. **原生路由（native routing）**：直接使用 Linux 主机路由表，要求网络能路由容器 IP。适合与云路由器、路由守护进程或 IPv6 原生基础设施集成。
3. **自动化路由学习**：在 L2 同域场景用邻居发现、跨 L3 场景用 BGP 自动完成路由宣告。

不确定时从 overlay 开始，等遇到性能或与底层网络集成的明确需求再切原生路由——两种模式的切换不影响策略语义，代价主要在运维侧。

## 跨集群与流量加密

**ClusterMesh** 解决多集群互通：跨集群的工作负载像访问本地服务一样互相发现，后端可以跨集群自动故障转移，日志、认证、数据库这类共享服务也能统一暴露给多个环境。关键在安全语义不打折——策略身份跨集群统一，"允许 A 访问 B"在四个集群里是一条规则，不是四条。

传输加密不依赖 Istio 这类外部网格，Cilium 内置 IPsec、WireGuard 和 ztunnel 三种透明加密选项。入口管理上，Cilium 是 Kubernetes Gateway API 兼容的数据面，ingress、流量切分、路由行为都能用 Kubernetes 原生 CRD 声明。

## Hubble：内核态决策变得可查

eBPF 数据面有个天然的运维难题：决策发生在内核里，出问题时要回答"这条流为什么被断了"。Hubble 就是这个问题的答案：

- **server** 内嵌在每个节点的 agent 里，直接从 eBPF 拿流事件，开销低；通过 gRPC 对外提供流查询和 Prometheus 指标。
- **relay**（hubble-relay）连接全集群所有 server，提供一个聚合视图；`hubble` CLI 和 hubble-ui 都从它读数据，UI 画出的是服务依赖与连通性地图。
- **drop reasons** 是排障时最有用的部分：一条流被丢弃时能查到具体原因——策略违规、端口不对、还是 DNS 解析失败，不用再靠 tcpdump 猜。

运维侧另有现成的 Prometheus、Grafana 集成，指标和告警不必自建。

## 快速上手

最快验证路径是 Kind 集群（命令来自 [官方入门文档](https://docs.cilium.io)的标准流程）：

```bash
# 安装 cilium CLI 后
cilium install --version 1.20.2   # 部署 Cilium 到集群
cilium status                      # 检查组件健康
cilium connectivity test           # 跑内置连通性测试套件
```

`cilium connectivity test` 值得单独说明：它是一套开箱即用的端到端验证（官方文档示例跑出 69/69 通过），部署真实的探测负载覆盖连通性与策略场景，比手工 curl 探测可靠得多，建议在任何环境变更后跑一遍。

镜像分发覆盖 AMD64 和 AArch64；从 v1.13.0 起所有镜像附带 SPDX 格式的软件物料清单（SBOM），供应链审计友好。

## 适用边界

- **内核版本要求**：容器镜像方式运行要求 Linux 内核 5.10 以上（RHEL 8.10 的 4.18 内核也支持）。Cilium 会探测内核可用特性并自动启用，老内核上部分高级特性静默降级——评估前先确认目标节点的内核版本，别等装完再发现特性缺失。
- **L7 策略的架构代价**：所有 L7 流量过 Envoy，策略的深度是用一跳用户态代理换来的。纯 L3/L4 场景不经过 Envoy，没有这笔开销。
- **学习曲线**：排障需要同时理解 Kubernetes 网络和 eBPF。`cilium status` 加 Hubble 的 drop reasons 能覆盖大部分日常，真正深入时会牵扯到 BPF 程序与 map，`cilium-dbg` 是那时候的工具。
- **不是万能加速器**：收益在大服务规模、复杂策略场景最明显；小规模集群切 Cilium 更多是为策略表达能力和可观测性，而非纯性能。

## 结语

落地顺序建议从最便宜的收益开始：第一步做 kube-proxy 替代和身份策略，这两项不改变应用任何行为，收益立刻可见；第二步开 Hubble，可观测性价值独立于其他特性；L7 策略、传输加密、ClusterMesh 按需跟上；服务网格类特性放在最后——多数团队走到第二步就已经解决当初评估 Cilium 的问题了。

反向的判断同样成立：节点内核普遍低于 5.10、或者集群规模小到策略用 iptables NetworkPolicy 就写得下，那么 Cilium 引入的运维复杂度大于收益，不值得跟进。
