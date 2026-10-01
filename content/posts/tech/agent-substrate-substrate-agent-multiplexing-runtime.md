---
title: "Agent Substrate：把百万级 AI Agent 装进 8 个 Pod 的「演员-工人」多路复用运行时"
date: "2026-10-02T03:23:27+08:00"
lastmod: "2026-10-02T03:23:27+08:00"
draft: false
slug: "agent-substrate-substrate-agent-multiplexing-runtime"
github_repo: "agent-substrate/substrate"
source_key: "gh:agent-substrate/substrate"
description: "Agent Substrate 是一个 secure-by-default 的 Agent 执行运行时，把大量「常驻 Agent」当作可暂停/恢复的演员（Actor）多路复用到少量工人（Worker）上，靠全状态快照实现亚秒级激活与 30 倍超卖，让运行一百万个沙箱的密度比标准容器运行时高一个数量级。"
categories: ["技术笔记"]
tags: ["AI Agent", "Kubernetes", "云原生", "Go"]
---

## 本文导读

读完本文你将能够：

- 说清 Agent Substrate 要解决的问题：为什么「按峰值常驻」跑 Agent 是资源浪费，以及「actor/worker 多路复用」如何把它变成「按活跃度复用」
- 理解一次 suspend/resume「 teleport」的完整链路：谁触发、谁快照、快照存哪、流量怎么路由回去
- 对照 gVisor / microVM 两种沙箱形态，判断自己的 Agent 负载该接哪一层
- 用 kind 十分钟跑通 Counter Demo，亲手验证「暂停的 actor 记得自己的计数器」

## 它解决的是一个「空闲率」问题

先看一个反直觉的数字：官方演示里，一个 8 个物理 Pod 的小集群，同时「住」着约 250 个有状态 Agent。这不是把 Agent 塞得更挤，而是承认一个事实——**Agent 大部分时间在闲着**。

一个典型的编码 Agent：接收任务 → 调 LLM → 执行工具 → 等待用户/上游 → 再调 LLM。其中真正占用 CPU/内存的窗口可能只有百分之几，但它却像一个常驻 Web 服务一样占着完整的容器：文件系统、内存里的会话状态、网络连接，全都要在。如果你要跑一百万个这样的 Agent，按峰值配置常驻，成本会先杀死你。

Agent Substrate（Go 编写，Apache-2.0，背靠 Google 的 Agent Executor / kagent 生态）给出的方案是把 Kubernetes 里两个早已存在但从未为 Agent 组合过的能力拼起来：

1. **CRIU 式的全状态快照**（通过 gVisor 的 `runsc` checkpoint/restore，或 cloud-hypervisor microVM）
2. **Actor 模型的按需激活**

于是架构变成两层映射：**大量 Actor（逻辑上的 Agent 实例）映射到少量 Worker（真实跑着的 Pod）**。Actor 没有流量时被挂起（suspend）成快照，流量来了再在任意一个空闲 Worker 上恢复（resume）。README 里的术语叫 **Actor Teleport**——演员可以随时"传送"到任何一个有空位的舞台上。

## 核心抽象：Actor、Worker 和它们之间的调度契约

理解这套系统只需要记住五个概念：

| 概念 | 是什么 | 类比 |
|------|--------|------|
| **Actor** | 逻辑 Agent 实例，有自己的状态（内存 + 文件系统）和身份 | 一个"会话" |
| **Worker** | 物理上真实运行的沙箱 Pod（gVisor 或 microVM） | 一个"舞台" |
| **ActorTemplate** | Actor 的镜像/规格模板 | Deployment 的 PodTemplate |
| **WorkerPool** | Worker 的池子，可配 HPA 自动伸缩 | NodePool |
| **Atespace** | 命名空间（项目对 namespace 的叫法） | K8s namespace |

关键设计决策有三个，值得逐个展开：

### 1. 低观点（low-opinion）系统：它不是 Agent SDK

README 明确划界：Substrate **不是**构建 Agent 的 SDK，而是运行 Agent 的系统。它管理的是标准 OCI 容器（gVisor 在内核层面拦截），所以框架无关——ADK、LangChain、Claude Code、CodeX 都能跑；MCP Server 也能作为一个 Actor 部署进来当"耐用工具"。这意味着你不需要重写 Agent 逻辑，只需要给它一个 ActorTemplate。

### 2. 安全默认（secure-by-default）

每个 Worker 都跑在 gVisor（用户态内核拦截）或 microVM 里，网络走零信任模型——Actor 之间的流量不因同集群而可信，出口流量有显式的 Egress 协议管控，甚至支持配置 MITM 拦截做出口策略（header 注入等）。这对"Agent 会执行不可信代码"的场景是刚需：**Agent 的沙箱本身就是产品的一部分**。

### 3. 基于 Kubernetes，但自己管调度

Worker 的生命周期（Pod、DaemonSet、自动伸缩）交给 Kubernetes，但 **Actor 到 Worker 的分配是 Substrate 自己的控制面做的**——因为 K8s 调度器不懂"毫秒级激活延迟"这件事。官方数据是 sub-500ms 的 resume、每秒 500+ 次 suspend/resume 激活，密度比标准容器运行时高 10 倍。这个"双层调度"的取舍很经典：基础设施复用 K8s 生态，Agent 特有的低延迟调度自己写。

## 一次 Teleport 的完整链路

把 demo 里的流程拆开看，suspend/resume 不是"把容器停了"这么简单：

1. **挂起**：控制面（`ate-api-server`）决定把某个 Actor 从 Worker 上撤下。节点上的 `atelet` DaemonSet 指挥 Worker 内部的 `ateom-gvisor` 执行 `runsc` checkpoint——把整个进程树的状态连同内存、打开的文件描述符打成快照，持久化到对象存储。
2. **腾位**：原 Worker 立刻可以承载别的 Actor。资源是按"活跃 actor 数"流动的，不是按"登记 actor 数"静态划分。
3. **恢复**：流量到达时，`atenet`（Envoy 路由层）发现目标 Actor 没有活跃 Worker，触发 resume——任意一个有空位的 Worker 从快照 restore，恢复内存里的变量和文件系统里的中间产物。
4. **路由**：`atenet` 把请求转发到新 Worker，调用方完全无感。

对 Agent 的意义：**会话状态（volatile RAM）和文件系统状态在 hibernation 周期之间完整保留**。一个 Claude Code 实例被挂起三天再唤醒，它的工作目录、shell 历史、甚至内存里缓存的内容都还在。这就是官方说的 30 倍以上超卖（oversubscription）敢做的底气——挂起不是杀死重建，是真正的冻结。

## 两条沙箱路线：gVisor vs microVM

Substrate 把沙箱技术做成了可插拔，目前两条主线：

| | gVisor 路线 | microVM 路线 |
|---|---|---|
| 实现 | `ateom-gvisor`，runsc checkpoint/restore | `ateom-microvm`，cloud-hypervisor 虚机 |
| 隔离 | 用户态内核拦截（系统调用级） | 硬件虚拟化 |
| 快照 | CRIU 式进程级快照，轻量 | 整 VM 快照，更重但隔离更强 |
| 适合 | 普通 Agent / 工具执行 | 强隔离需求（跑完全不可信代码） |

两者共享同一套生命周期 API，这对平台团队很关键：先用 gVisor 跑密度，遇到需要强隔离的租户切 microVM，上层编排不用改。

## 十分钟跑通 Counter Demo（kind 本地版）

最快的体感方式是官方 Counter Demo——一个有状态 Go HTTP 计数器，演示"挂起后状态不丢"：

```bash
# 前置：Go + kubectl + docker，其余依赖（kind 等）由 Go 自动管理
git clone https://github.com/agent-substrate/substrate.git
cd substrate

# 1. 建 kind 集群 + 本地 registry
hack/create-kind-cluster.sh

# 2. 装 ate 系统（控制面）+ PostgreSQL + rustfs（快照存储）
hack/install-ate-kind.sh --deploy-ate-system

# 3. 装 counter demo + kubectl 插件
hack/install-ate-kind.sh --deploy-demo-counter
go install ./cmd/kubectl-ate

# 4. 创建一个 counter actor
kubectl ate create actor my-counter-1 -a ate-demo-counter --template counter

# 5. 端口转发网络路由层
kubectl port-forward -n ate-system svc/atenet-router 8000:80
```

另开一个终端，计数：

```bash
curl -X POST \
   -H "ate-target-actor: ate-demo-counter/my-counter-1" \
   -i http://localhost:8000/
```

多打几次，然后把 actor 挂起（`kubectl ate` 提供 suspend），再 resume，重新 curl——计数器从挂起前的值继续走。这个"记得自己数到几"的小实验，就是全状态快照最直观的证明。

一个容易踩的坑：**Worker 只调度到带 `ate.dev/substrate-version` 标签的节点**（版本化容量管理）。后来加进集群的节点要先手动打标签才会有 Worker：

```bash
kubectl label node <node> ate.dev/substrate-version=<build version>
```

## 生产化视角：什么团队现在就该关注它

诚实地说，这是 pre-1.0 项目，API 还会变，README 也直言短期可能顾不上合并不合核心目标的贡献。但它背后站着 Google 的 Agent Executor（分布式 Agent 运行时，官方博客明确说构建在 Substrate 上）和 CNCF 沙箱项目 kagent（用 Substrate 跑沙箱化有状态 Agent 负载），生态位非常清晰。

三类团队值得关注：

1. **Agent 平台团队**：如果你们内部要跑成百上千个常驻编码/自动化 Agent，"按活跃度复用"的密度收益是直接的算力账。
2. **RL 训练基础设施**：README 特别点名 RL 场景——agentic、inference、training 混部时，Agent 沙箱的快速起停直接影响 rollout 吞吐。
3. **MCP 托管服务**：把 MCP Server 当 Actor 部署，天然获得沙箱隔离 + 按需激活 + 状态持久化，比常驻容器便宜得多。

对照检查你的场景是否匹配：Agent 是否**有状态**（无状态的 serverless 已经够用）？是否**空闲率高**（一直忙的负载复用收益小）？是否需要**毫秒级恢复**（能接受冷启动的用普通 Job 即可）？三个都是 yes，Substrate 就是为你这类负载设计的。

## 写在最后

Agent 基础设施这两年的主旋律是"更聪明的编排"，Substrate 选的是另一条更底层也更朴素的路：**Agent 是一种新的负载形态，它需要一种新的运行时**。Actor 模型 + 全状态快照 + K8s 生态，三个都是旧零件，拼出来的却是"百万 Agent 常驻"这个此前不可能的密度。它未必是最终形态，但"按活跃度复用有状态 Agent"这个思路，大概率会成为下一代 Agent 平台的标配。

项目信息：[agent-substrate/substrate](https://github.com/agent-substrate/substrate)（Go · Apache-2.0 · 4k+ stars），每周四有社区会议，CNCF Slack 有 #substrate-users 频道。文档里的 [Architecture](https://github.com/agent-substrate/substrate/blob/main/docs/architecture.md) 和 [Threat Model](https://github.com/agent-substrate/substrate/blob/main/docs/threat-model.md) 值得精读。
