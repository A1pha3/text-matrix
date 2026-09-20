---
title: "Cilium：用 eBPF 重写 Kubernetes 网络层的 CNCF 毕业项目"
date: 2026-09-21T03:45:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["cilium", "ebpf", "kubernetes", "网络"]
description: "Cilium 是 CNCF 毕业级的 eBPF 网络、可观测与安全方案，用内核态数据面替代 kube-proxy，以身份而非 IP 地址执行 L3-L7 策略。本文拆解其架构判断与上手路径。"
github_repo: "cilium/cilium"
source_key: "gh:cilium/cilium"
slug : cilium-ebpf-kubernetes-networking
---

## 核心判断

Cilium 解决的不是"又一个 CNI 插件"的问题，而是把 Kubernetes 网络从"IP 地址 + iptables"的模型迁移到"身份标识 + eBPF 程序"的模型。它的数据面运行在 Linux 内核里，而不是用户态的规则引擎里——这是它能在服务密度和策略表达能力上同时拉开差距的根本原因。

对大多数团队，Cilium 的实际价值集中在三件事：完全替代 kube-proxy 的东西向负载均衡、不依赖 IP 的 L3-L7 网络策略、以及跨集群的统一安全模型。如果你的集群还在为 iptables 规则数量膨胀发愁，或者需要按"Pod 是谁"而不是"Pod 在哪个网段"来写策略，Cilium 值得认真评估。

## 项目概览

| 项 | 数据（2026-09-20 取自 GitHub） |
|---|---|
| 仓库 | [cilium/cilium](https://github.com/cilium/cilium) |
| 定位 | eBPF-based Networking, Security, and Observability |
| Stars / Forks | 25,381 / 4,085 |
| 主语言 | Go（数据面为 eBPF C） |
| License | Apache-2.0（部分组件 BSD/GPL） |
| 成熟度 | CNCF 毕业项目（Graduated） |
| 维护版本 | v1.20.2 / v1.19.8 / v1.18.14（2026-09-15 同日发布），v1.21.0-pre.2 预发布中 |

三个稳定版本分支并行维护、补丁节奏整齐，加上 main 分支每日 CI 镜像，这是基础设施级项目的典型维护强度。

## 系统地图：eBPF 数据面在哪些位置挂钩

理解 Cilium 的最短路径是看 eBPF 程序挂在内核的哪些集成点上。README 明确列出的挂载点包括网络 I/O、应用套接字（socket）和 tracepoint：

- **网络 I/O 路径（TC/XDP）**：容器流量的转发、NAT、负载均衡在这里完成。东西向负载均衡直接在 socket 层改写 `connect()` 调用，避免了逐包 NAT 的开销——这也是它"完全替代 kube-proxy"的底气所在。
- **XDP 路径**：面向高吞吐的南北向负载均衡，支持 Direct Server Return（DSR）与 Maglev 一致性哈希。
- **身份模型**：Cilium 的网络策略基于安全身份（identity）而非 IP 地址。身份与网络寻址解耦后，Pod 重建、IP 变化不再导致策略失效，策略可以精确到 L7 协议（如"只允许访问某 API 的 GET 路径"）。

## 三种组网模式

Cilium as CNI 提供三种部署形态，按对底层网络的要求从低到高：

1. **Overlay（覆盖网络）**：VXLAN 或 Geneve 封装，唯一要求是主机间 IP 可达。几乎可以在任何网络基础设施上跑。
2. **原生路由（native routing）**：直接使用 Linux 主机路由表，要求网络能路由容器 IP。适合与云路由器、路由守护进程或 IPv6 原生基础设施集成。
3. **自动化路由学习**：在 L2 同域场景用邻居发现、跨 L3 场景用 BGP 自动完成路由宣告。

选型经验：不确定时从 overlay 开始，等遇到性能或与底层网络集成的明确需求再切原生路由。

## 跨集群：Cluster Mesh

多集群场景下，Cilium 的 Cluster Mesh 让跨集群的工作负载像访问本地服务一样互相发现与连接——支持后端跨集群自动故障转移，也能把日志、认证、数据库这类共享服务统一暴露给多个环境。对混合云和多云团队，这是比单点网络加速更实际的价值点。

## 快速上手

最快验证路径是 Kind 集群（以下命令来自 Cilium 官方 CLI 的标准用法，详见 [docs.cilium.io](https://docs.cilium.io)）：

```bash
# 安装 cilium CLI 后
cilium install --version 1.20.2   # 部署 Cilium 到集群
cilium status                      # 检查组件健康
cilium connectivity test           # 跑内置连通性测试套件
```

`cilium connectivity test` 值得单独说明：它是一套开箱即用的端到端验证，覆盖东西向、南北向和策略场景，比手工 curl 探测可靠得多，建议在任何环境变更后跑一遍。

镜像分发覆盖 AMD64 和 AArch64；从 v1.13.0 起所有镜像附带 SPDX 格式的软件物料清单（SBOM），供应链审计友好。

## 适用边界

- **内核版本要求**：eBPF 特性依赖较新的 Linux 内核，老内核（或某些托管环境的受限内核）可能无法启用全部功能，评估前先确认目标节点内核版本。
- **学习曲线**：排障需要同时理解 Kubernetes 网络和 eBPF，`cilium` CLI 的 `status`/`health` 子命令能覆盖大部分日常，但深度问题会牵扯到 bpf 程序本身。
- **不是万能加速器**：Cilium 带来的收益在大服务规模、复杂策略场景最明显；小规模集群切 Cilium 更多是为策略表达能力和可观测性（Hubble），而非纯性能。

## 结语

Cilium 是"新内核技术重写基础设施层"这条路线最成功的范本之一：eBPF 提供机制，Cilium 把机制收敛成可运维的产品。如果你的下一步是服务网格，它的 sidecar-free 模式（与 Envoy 集成）也预留了演进空间——先从替代 kube-proxy 和身份策略做起，是最平滑的落地顺序。
