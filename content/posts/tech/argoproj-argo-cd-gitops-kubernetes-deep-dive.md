---
title: "Argo CD 深度拆解：GitOps 控制器的同步、漂移修复与多租户边界"
date: 2026-07-14T03:13:50+08:00
slug: "argoproj-argo-cd-gitops-kubernetes-deep-dive"
description: "Argo CD 是 Kubernetes 上的声明式 GitOps 持续交付工具，核心由 API Server、Repository Server、Application Controller 三大组件协同。本文按系统地图、同步机制、漂移修复、Helm/Kustomize/plain 三类任务流，逐层拆解它的 GitOps 控制器模型与多租户边界。"
draft: false
categories: ["技术笔记"]
tags: ["GitOps", "Argo CD", "Kubernetes", "持续交付", "声明式"]
---

# Argo CD 深度拆解：GitOps 控制器的同步、漂移修复与多租户边界

> **目标读者**：负责 Kubernetes 应用交付的 SRE / 平台工程师，已经用过 kubectl 和 Helm，希望在选型或落地 Argo CD 之前把它的工作机制看穿
> **预计阅读时间**：25-30 分钟
> **前置知识**：了解 Git、Kubernetes 对象模型（Deployment / Service / CRD）、Helm 或 Kustomize 的基本用法
> **适用版本**：Argo CD master 分支（README 与官方文档 https://argo-cd.readthedocs.io/ 最新稳定版）

读完这篇，你应该能在不打开 dashboard 的情况下回答这几个问题：

- Argo CD 的"持续交付"和传统 CI/CD 流水线到底差在哪里？为什么它把 Git 当成 source of truth？
- 一个 Application 从 Git 仓库里被渲染、对比、修复到集群，到底经过哪几个组件？
- 漂移（drift）是怎么检测的，怎么自动修、什么时候该人工介入？
- Helm、Kustomize、纯 YAML 三种任务源在 `repo-server` 里的渲染路径有什么不同？
- AppProject + RBAC + 命名空间白名单这套多租户边界到底卡住了什么、放过了什么？

阅读建议：第一遍按"核心判断 → 系统地图 → 一次任务穿过系统 → 同步/漂移机制 → 多租户边界"读，先把骨架看明白；第二遍按需跳到具体机制深入。

---

## 核心判断

很多人把 Argo CD 当成"会 watch Git 的 kubectl"。这是把它低估了的看法。Argo CD 的核心价值不是把 `kubectl apply` 自动化，而是把"集群的实时状态"和"Git 上声明的目标状态"做成两份独立可对比的事实（live state vs target state），并以 Kubernetes 控制器的形式持续把前者收敛到后者。

仓库地址是 [github.com/argoproj/argo-cd](https://github.com/argoproj/argo-cd)，Apache-2.0 协议，目前 master 分支的最新提交时间是 2026-07-13，仓库累计 Star 数 2.37w、Forks 约 7.6k（README 与 GitHub API 实时数据）。CNCF 毕业项目，OpenSSF Scorecard 和 CII Best Practices 都打了卡；发布版带 SLSA 3 等级的供应链元数据。从工程量级看，它本身就是个安装到集群里的"GitOps 控制器 + 一组 CRD + 一个 UI + 一组 CLI"。把它当作 Kubernetes 原生对象管理 Git 仓库这件事，理解全篇文章就足够了。

读完 Argo CD 项目自己的 README，加上官方 Architectural Overview 与 Core Concepts 两份文档之后，可以归纳出三条核心判断：

- **判断 1：Argo CD 是 Kubernetes 的控制器，不是 CI 流水线**。它跑在集群里，和 Deployment/ReplicaSet 一样由 `kube-scheduler` 调度、由 `controller-manager` 守护；它和外部世界唯一的协议是 Git（pull 模型），而不是 webhook（push 模型）。这条直接决定了它的部署模型、灾备模型和权限模型。
- **判断 2：Application 不是一组 manifest，而是一个 CRD**。Application 是 Argo CD 自己定义的 Kubernetes Custom Resource，里面写的是"我想要的最终态"。Argo CD 只关心这份期望的最终态，并把它和集群里真实的对象逐个对比。manifest 只是 Application 的一部分字段。
- **判断 3：sync 是一次幂等操作，Reconcile 才是核心循环**。Sync 是用户或控制器主动触发的一次"对齐"动作；Reconcile 是控制器对每个 Application 周期性跑的那段 reconcile loop（对照 live vs target、修正 sync status、清理孤儿资源）。理解这两件事的区别，drift detection、self-heal、prune 这些功能才好分清顺序。

第一条判断点出架构立足点：pull 模型，控制循环跑在集群内部。第二条指明核心对象：Application CRD 是 gitops workload 的基本单位。第三条点出核心动作：sync 是写一次，reconcile 是持续读并收敛。

## 目录

- [目录](#目录)
- [核心判断](#核心判断)
- [系统地图](#系统地图)
- [边界拆分：三种 Git 引用、三种渲染工具、三种隔离面](#边界拆分：三种-git-引用、三种渲染工具、三种隔离面)
- [关键机制：同步、漂移修复、孤儿资源清理](#关键机制：同步、漂移修复、孤儿资源清理)
- [一次真实任务穿过系统](#一次真实任务穿过系统)
- [多租户边界：AppProject + RBAC + 命名空间白名单](#多租户边界：appproject--rbac--命名空间白名单)
- [采用建议](#采用建议)
- [常见翻车现场](#常见翻车现场)
- [常见问题](#常见问题)
- [总结](#总结)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [项目资源](#项目资源)

---

## 系统地图

Argo CD 在集群内部署成 3 个核心组件 + 1 组 CRD + N 个集群凭证。先把这张地图摆出来，后面所有的同步、对比、修复动作都不会脱离它。

### 三组件：API Server / Repository Server / Application Controller

官方 Architectural Overview 把 Argo CD 拆成 3 个互不重叠的组件，对应 deployment 在 namespace 里都能看到：

| 组件 | 角色 | 关键职责 | 通信协议 |
|------|------|----------|----------|
| **API Server** (`argocd-server`) | 控制平面入口 | 暴露 gRPC/REST API；终端用户、CI 系统、UI 都通过它操作 Application；认证鉴权；Git Webhook 事件的转发器 | gRPC / REST，对外暴露 |
| **Repository Server** (`argocd-repo-server`) | manifest 渲染器 | 拉取 Git 仓库、缓存、调用 Helm/Kustomize/Jsonnet/Plain 等工具把 Application 引用的 source 渲染成最终 Kubernetes 对象 | 内部 gRPC，对 controller 提供 |
| **Application Controller** (`argocd-application-controller`) | reconcile 引擎 | 周期性地把"期望态"（来自 repo-server）和"实时态"（来自 kube-apiserver）做 diff，标 Sync/Health 状态，并按策略触发 sync | kube-informer + 内部 gRPC |

三组件都跑在 Argo CD 自己的 namespace 里（默认 `argocd`），由 Deployment/ReplicaSet 拉起，各自有 ConfigMap 和 Secret。Application Controller 是 reconcile 的核心，但它自己并不直接 git clone，所有 manifest 渲染都委托给 Repository Server，自己保留"对比 → 标记 → 触发 sync"这条主线。

### 三类对象：Application / AppProject / ApplicationSet

Argo CD 安装后会在集群里注册一组 CRD（这是 Argo CD 自己拥有的 schema），核心是这 3 个：

- **Application**：最小的"想交付到哪个集群"的单位。spec 里写明 source（Git repo URL + revision + path）、destination（目标集群名 + 命名空间）、sync policy、ignore differences 规则等。status 里实时同步 sync status 与 health。Argo CD 周期性地比对 spec 与目标集群状态，把差异算到 OutOfSync / Healthy / Degraded / Suspended。
- **AppProject**：项目级别的"业务隔离面"。一个 AppProject 内有 source 仓库白名单、destination 集群白名单 + 命名空间白名单、cluster resource 白名单、可签发的 SyncWindow、可调的 RBAC policy 列表。Application 必须挂在 AppProject 下，越界就拒收。
- **ApplicationSet**：Application 的 generator（生成器）。用来从 Git 目录、Cluster list、PR/MR、ScmProvider 等输入"扇出"出大量 Application。同一份 helm chart 在 12 个环境部署，靠 ApplicationSet + 模板而不是写 12 个 YAML。

ApplicationSet 不直接部署东西，它是把 Git/Cluster/Scm 数据源拆成 N 份模板参数，每份产出一个 Application CR，让 Argo CD 控制器接手。Argo CD 控制器再走标准同步流程。

### 多集群：单 controller 联邦，凭证用 Secret

Argo CD 部署在"中心集群"，但可以管理一组"外部集群"（包括它自己所在的那一个，名为 in-cluster）。每个外部集群在 Argo CD 那边只是一个 Secret：里面存 kubeconfig 或者 bearer token + API server URL。Application 的 destination 字段写的就是这些集群的名字。

这种"单 controller 联邦多个集群"模型意味着：所有 reconcile 都在中心集群的 Argo CD 里发生；外部集群不需要装 Argo CD，只暴露标准 kube-apiserver 即可。代价就是中心集群宕机时所有 drift detection 跟着停——这是任何 controller model 的固有弱点，README 没有特意强调，但运维时必须考虑。

### 异步流水线：API Server → Controller → Repo Server → kube-apiserver

把三组件和三类对象排到时间轴上，一次 reconcile 的关键链路是：

1. API Server 接收用户的 Application 创建/更新、或者收到 Git webhook 事件；
2. Application Controller 看见 Application CR 变更后，把它丢进工作队列；
3. Controller 用 Application 的 source 字段请求 Repository Server，请求给出最终的 K8s object 列表（即 manifest）；
4. Controller 用 manifest 里的 namespace + name 列表，从目的地 kube-apiserver 拉真实对象，做 diff；
5. Controller 根据 diff + sync policy，决定是否触发 sync，把状态写回 Application.status；
6. Sync 时 Controller 通过 Kubernetes API 写目标集群（不是 kubectl apply，而是走 client-go 的 patch 逻辑）。

每一步都用了 Kubernetes 的 watch/list 而不是轮询（Controller 端走 informer，repo-server 端走 git ls-remote + 内部缓存），所以 Argo CD 不会出现"高频 cron 拉 Git"的成本。

## 边界拆分：三种 Git 引用、三种渲染工具、三种隔离面

第一次读 Argo CD 文档最容易混的地方是字段同名不同物。表里给出最关键的 3 组边界。

### 边界 1：Git 引用 vs 集群路径

| 概念 | 字段 | 含义 |
|------|------|------|
| Source | `spec.source.repoURL` + `spec.source.targetRevision` + `spec.source.path` | 在哪个 Git 仓库的哪个 commit/branch 的哪个目录 |
| Destination | `spec.destination.server` + `spec.destination.namespace` | 渲染后的对象要送到哪个集群的哪个 namespace |
| Sync status | `status.conditions[]` | sync / 健康 / suspended 状态码，不参与 manifest 决策 |

`source` 是"读哪里"，`destination` 是"写哪里"。仓库只是 source 之一，OCI（Helm OCI）和 Plugin 也算 source；destination 也支持本地集群、外接集群等多种形态。

### 边界 2：三种 manifest 渲染工具

| 工具 | 何时启用 | 如何被 Argo CD 调起 |
|------|----------|--------------------|
| **Plain (Directory)** | repo 根目录直接就是 K8s YAML | repo-server 直接遍历，校验 K8s schema |
| **Helm** | source.path 指向含 `Chart.yaml` 的目录 | 通过 Helm v2/v3 CLI / Helm libs 渲染，可填 `helm.values` |
| **Kustomize** | source.path 指向含 `kustomization.yaml` 的目录 | 通过 kubectl 内嵌或独立 kustomize binary 调用 |
| **Jsonnet** | source.path 是 .jsonnet 文件 | 通过 jsonnet 命令行渲染 |
| **Plugin** | sidecar / config management plugin | repo-server 启动时通过 ConfigMap 声明 `<name>.yaml` |

Argo CD 的 Application 不强制渲染工具，渲染由 repo-server 根据目录内容自动嗅探（详见 user-guide 里的 directory tool detection）。这种"按 source.path 自动发现"的策略让一个 Git 仓库可以混用多种工具，但对 retention 很复杂的 monorepo 来说要小心嵌套副作用。

### 边界 3：三种隔离面

| 隔离面 | 对象 | 控制字段 |
|--------|------|----------|
| **Kubernetes 集群隔离** | destination | `spec.destination.server` 选哪个集群的 Secret |
| **命名空间隔离** | destination + AppProject | `spec.destination.namespace` + AppProject 的 `clusterResourceWhitelist` / `namespaceResourceWhitelist` |
| **逻辑项目隔离** | AppProject + RBAC | AppProject 内嵌 `roles` / `policies`；用户绑定到一个 role 后只能在自己 AppProject 内的 Application 上 sync/render |

把三层都看清之后，"为什么 Argo CD 适合多团队多环境"这个问题就有一个具体答案：datasource 隔离靠 Git 仓库 + repo URL；集群隔离靠 destination；命名空间隔离靠 AppProject 白名单；用户隔离靠 AppProject 内 RBAC + Policy。

## 关键机制：同步、漂移修复、孤儿资源清理

Argo CD 的卖点是"自动修复漂移"，但具体什么时候自动修、什么时候手工介入是新手最常踩的坑。下面把 sync、Reconcile、drift detection、prune 这 4 件事拆开看。

### sync：一次幂等操作

sync 是单次操作：把"target state"应用一次到目标集群。Argo CD 选用 `kubectl apply --prune` 的升级版——它会先算出 desired object list，再走 server-side apply 或 strategic merge patch 到 kube-apiserver，而不是直接 apply 整个 yaml。核心代码在 Application Controller 的 `appcontroller` 包里。

sync 的几个关键开关，都写在 Application CR 里：

- `syncPolicy.automated` 开了之后，drift 被发现就会自动 sync。这是 self-heal 的来源。
- `syncPolicy.automated.prune` 决定要不要清理"目标态里没有、集群里却有"的对象（即孤儿资源）。
- `syncPolicy.automated.allowEmpty` 决定清空目录是否合法。
- `syncOptions[].PrunePropagationPolicy` 决定依赖对象的删除顺序（foreground / background / orphan）。

sync 是幂等的——同一份源推到集群两次，最终结果一样；这意味着可以从 Argo CD 之外的工具（kubectl / Helm / terraform）做变更，Argo CD 检测到 drift 再 sync 一次就能拉回来。

### Reconcile 与 drift detection

Application Controller 在每个 application 上跑一个 reconcile loop：

1. 用 source hash 查 cache 命中，否则触发 repo-server 重新渲染；
2. 拿渲染结果对象，和目标集群的对应对象做 server-side diff；
3. 把 diff 写到 status 里；如果 `automated` 开启且 `selfHeal` 为真，则触发 sync。

`selfHeal` 是 drift 修复的核心开关。打开它之后，任何外部方式（人手 kubectl / 别套 CD 工具 / 节点漂移）造成的偏差，都会在下一个 reconcile 周期被 Argo CD 追回。关掉它的话，Argo CD 只标记 OutOfSync 等用户主动 sync。

Reconcile 周期可在 controller 的 `--sync`（默认 3s）和 `--status` flag（默认 5s）调整，但 Argo CD 也支持 Webhook 推送，Git 端 commit 后几分钟内就能触发 reconcile。

### Prune：孤儿资源

Prune 是 sync 阶段同步处理"集群里多余的对象"。三种典型场景：

- 应用换 chart：旧 chart 里有个 ConfigMap，新 chart 里删了；开 prune 之后这条 ConfigMap 会被自动清掉。
- 团队手工改了 cluster 里某个 deployment（手 kubectl edit）；下次 reconcile 时 OpenSync + sync 会把它追回 Git（selfHeal）。
- 跨 application 共享对象：例如两个 Application 都创建 ConfigMap `foo`，开 prune + 多 Application 容易互相踩，建议把共享对象放到独立 Application 或者关 prune。

`--auto-prune` 等开关在原 kubernetes 工具里没有，Argo CD 把这一层语义补上。代价是开 prune 容易误删——>比如 CronJob `successfulJobsHistoryLimit` 之类的对象和另一个工具管理，prune 会删掉它。

### Sync Window：变更节奏护栏

SyncWindow 不是控制同步频率，而是限制哪些时间窗口内允许 sync。常见用法是只在 22:00 到 06:00 允许生产环境自动 sync，剩下的时间 drift 都会留在 OutOfSync 状态等人工看。这条对生产稳定性比 self-heal 更重要。

## 一次真实任务穿过系统

下面是一个"用户提交 PR → main 触发同步 → 集群自动更新"的真实案例，把上一节的所有边界串起来。

### 应用场景

一家 SaaS 团队有两个 Application：

- Application `web`：repo 是 `git@github.com/acme/web.git`，path = `deploy/prod`，工具 = Helm，destination 是 production 集群、`web` namespace；
- AppProject `web-team`：只允许 `web` 这个 Application 引用 `github.com/acme/*` 仓库，只允许部署到 production 集群的 `web` 和 `staging-web` namespace。

### 步骤 1：开发者 push PR → main 合并

开发者改了 `deploy/prod/values.yaml`，PR 合入 main。GitHub 通过 webhook 通知 Argo CD API Server（argocd-server 的 `argocd-server --enable-gzip` 选项之外，webhook 接收器默认监听 `/api/webhook`）。Argo CD 把这次 commit 信息插入 Application 的 `spec.source.targetRevision` 候选，并在 Application Controller 里记一个 hint。

### 步骤 2：Application Controller 触发 Reconcile

Controller 看到 hint 后立刻 reconcile（不等 3 分钟 reconcile 周期）。它拿着 Application 的 source hash 去问 Repository Server："请帮我渲染 `git@github.com/acme/web.git@main` 在 `deploy/prod` 路径下的最终对象列表。"

### 步骤 3：Repository Server 渲染 manifest

repo-server 内部：

1. 用 ApplicationSpec 里指定的 git creds（从 Secret 拿 ssh key / https token）走 `git ls-remote + git archive`，不真正 clone，减少 IO；
2. 把 path 目录喂给工具检测：`deploy/prod/Chart.yaml` 存在 → 调 Helm v3，把 Helm Values + 模板渲染成 K8s object list；
3. 把渲染结果按文件 hash 缓存，下次同 commit 命中。

如果 path 下同时存在 `kustomization.yaml`，用户可在 `spec.source.kustomize` 里强制走 kustomize；要混用工具，就在 Chart.yaml 内部再嵌入 Kustomize 钩子。

### 步骤 4：Application Controller 做 diff

拿到 desired object list（可能是 6 个 Deployment + 6 个 Service + 1 个 ConfigMap + 1 个 Ingress）后，Controller 走 informer 向 production 集群的 kube-apiserver 拉对应的 live object。然后按 name 做 server-side diff，计算出 OutOfSync 集合：比如只有 Deployment `web-7c8f9b` 的 image 从 `v1.4.2` 变成 `v1.5.0`，其余对象对齐。

### 步骤 5：sync 写入集群

`automated=true` + `selfHeal=true` 时，Controller 直接发起 sync：

- 走 server-side apply 把新 Deployment 写入 production 集群；selector 标签变化时由 Kubernetes 创建新 ReplicaSet、逐 pod 滚动；
- Spec 里有 sync hook（pre-sync/sync/post-sync）的对象按顺序执行（例如 Job）；
- Prune 阶段跳过，因为没变更清单删除项。

`status.sync.status` 在 controller 写完 Deployments 之后被改成 `Synced`，`status.health.status` 在 Pod ready 之后被改成 `Healthy`。Application Controller 自己不直接读 Pod，它写一个 Synthetic ReplicaSet（`app.kubernetes.io/instance=app-name` label tracking），通过 tracker 找到所有派生对象。

### 步骤 6：失败回滚

如果 sync 后 controller 探测到 health Degraded 且未自愈，sync 后追加的 wave/phase 顺序不会自动回退。Argo CD 的"回滚"实际上是 sync 到上一个 Known Good Revision，这在 controller 的 `--revision-history-limit` 上限之内都能做。CLI 的 `argocd app rollback` 就是一个特殊形态的 sync。

## 多租户边界：AppProject + RBAC + 命名空间白名单

Argo CD 真正替代"CI/CD 流水线"那一段，靠的不是 sync 速度，而是权限和审计。下面 4 类边界是最常被绕过的。

### 1. AppProject 的源仓库白名单

`AppProject.spec.sourceRepos` 只能写 git URL 字面匹配或前缀匹配（如 `https://github.com/acme/*`），Application 的 `spec.source.repoURL` 不在白名单里就会被 controller 拒收，写进 status 但不部署。这避免某个工程师随手配置仓库从任意地址拉代码。

### 2. AppProject 的集群 + 命名空间白名单

`spec.destinations` 可以列"哪些集群 + 哪些命名空间"。这是把"开发环境"和"生产环境"从同一 Argo CD 中分离的关键开关。每个 AppProject 也可单独禁用 cluster-scoped 资源（ClusterRole、CustomResourceDefinition 等），进一步缩小爆破半径。

### 3. AppProject 内嵌的 RBAC Policy

每个 AppProject 可以定义 `policies`，policy 是 RBAC 风格的 `<action, resource, object>` 元组，例如：

```yaml
policies:
  - p, proj:web-team:dev, applications, get, web/*, allow
  - p, proj:web-team:dev, applications, sync, web/*, deny
```

policy 在 argocd-server 鉴权时被读取。它可以做到"张三只能在 staging 环境的 web 应用上 sync，不能看别的应用"。这条对中型平台团队很关键——直接省掉自建审批系统。

### 4. 集群级角色 Config

除了 AppProject 内嵌 policy，argocd-server 还支持全局角色（role/cluster role）。本地的 `argocd-rbac-cm` ConfigMap 写角色到用户的映射，外接 OIDC / SAML / LDAP / SSO 时由 dex 接驳（`argocd-dex-server` 组件）。这两层都按官方 README 和操作手册配。

### 这层边界不卡什么

值得警觉的是：AppProject 不是 namespace。多个 Application 即使分属不同 AppProject，依然跑在同一个 controller 进程里、共享同一个 repo-server 缓存、共享同一个 informer quota。一个 AppProject 内的 Application 配置错误（比如 tight loop 装 Helm chart 每秒 reconcile）会拉低整组性能。

另外，AppProject 不能阻止 Application 在 dest cluster 上 create 任意 cluster-scoped 资源，除非你显式把 `clusterResourceWhitelist` 关掉。一旦开了 cluster-scoped 准入，Argo CD 在多租户场景下需要慎重评估。

## 采用建议

下面这套顺序是按"大多数中型平台团队从 0 到 1 落地 Argo CD"的踩坑经验排的，仅供参考。

### 推荐采用顺序

1. **从 standalone 单集群开始**：先在 dev/staging 集群起一个 Argo CD，托管 1-2 个不含状态的 microservice。CLI 用 `kubectl apply -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml`，namespace 默认 `argocd`。
2. **引入 Application 而不是 Bash**：把 helm install 改成 Argo CD 的 Application CR。第一周保留手动 sync，先熟悉 diff 行为。
3. **加 AppProject 隔离**：每个业务团队一个 AppProject，先开 source repo 白名单，再开 cluster/namespace 白名单。RBAC policy 这一层先不上，避免误伤。
4. **再加 selfHeal**：开 automated + selfHeal，但关 prune。先让 drift detection 与被动修复稳定一周。
5. **开 prune**：先在 staging 开，验证无误删，再带到生产。
6. **接 ApplicationSet**：模板相同的多环境（dev/staging/prod）从一份 ApplicationSet 扇出，避免写 N 份 Application。
7. **接 SyncWindow 与 Resource Hook**：把生产 sync 限制到夜间；用 pre-sync Job 做 migration、schema 升级等。
8. **观测与告警**：开 Notification（Slack / Alertmanager）、SSE / Metrics，drift 发生或 sync 失败实时通知到值班。

### 不适合 Argo CD 的场景

- **纯静态文件发布到 S3/OSS**：没有 K8s 集群就上不了 Argo CD；用 Spinnaker 或 Argo Events 这种 push 模型更合适。
- **超大规模（>10k Application 单 controller）**：单个 controller 的 informer 是有上限的，要走 HA + sharding（v2.4 起支持 Dynamic Cluster Distribution）。
- **不希望任何远端拉代码**：Argo CD 默认 pull 模型，必须能从集群内拉 Git；如果网络隔离严重要走 Argo CD 的"Secrets as Code + UI-only"等额外方案或换 push 模型。
- **一次性 Job 流水线**：Argo Workflows 才覆盖这个领域，Argo CD 适合的是"持续运行的 deployable object"。

### 决策清单

> 接 Argo CD 之前先回答这 5 条

- 团队 GitOps 文化是否成立？拒绝直接 `kubectl apply` 改 prod？
- 多集群 / 多 namespace 数量级是否超过人手维护？
- 现有的 Helm chart / Kustomize 模板是否规范，secret 走 SealedSecrets / External Secrets？
- 是否能接受 center-cluster 当 downtime 时整组 reconciliation 跟着停？
- 是否已经有非 cluster-level 的 CI 系统兜底？Argo CD 只解决 CD 这一段。

## 常见翻车现场

把团队落地过程中踩过坑的地方列成清单——遇到类似症状时先查这里。

### 翻车 1：sync 永远 OutOfSync，diff 不收敛

- **症状**：status 显示 OutOfSync，但点开 diff 看不出差别。
- **原因**：对象有 status 字段（CRD 常见）、时间戳、annotation 自带 hash 等"非 spec 差异"被算入 diff。
- **修法**：写 `ignoreDifferences` 规则指明哪些 json path 差异忽略，注意更新 reference doc 中说明的 schema。

### 翻车 2：开 prune 后日志大量 Object was not deleted

- **症状**：prune 操作出现 `Error from server (Forbidden): User cannot delete resource`，但手动删没问题。
- **原因**：Argo CD 的 service account 在目的地集群缺 delete 权限。
- **修法**：检查目的地集群的 ClusterRole，确保 SA 包含 `delete` / `list` / `patch` 等；或在 Application 上加 `syncOptions` 跳过 prune。

### 翻车 3：Helm chart 渲染后 secret 字段值丢

- **症状**：Helm template 里有 `{{ .Values.db.password }}`，sync 后 secret 字段是空。
- **原因**：Argo CD 的 Helm 调用对外层 secret 注入靠 `spec.source.helm.valueFiles` + 显式 `spec.source.helm.parameters`；外面 secret 走 External Secrets Operator 注入，不能用 `--set` 方式传。
- **修法**：把 secret 拆出去管理，或者用 Helm 的 `--set-string` 在 Argo CD 端注入前先 dry-run 验证。

### 翻车 4：ApplicationSet 重渲染风暴

- **症状**：template 改动后，几百个派生 Application 全部同时进入 OutOfSync → Reconcile 风暴，controller CPU 飙满。
- **原因**：reconcile 是控制器频率触发，没有内建节流。
- **修法**：ApplicationSet 用 progressive sync 或 `applicationsync` 内的 spread 配置，或者通过 promotion generator 控制节奏。

### 翻车 5：selfHeal 反过来追回人工 debug 改动

- **症状**：debug 时改了 cluster 的 Deployment 跑通测试，第二天被 Argo CD 自动 sync 回去。
- **原因**：selfHeal 开启后等于"Git 永远赢"。
- **修法**：debug 时把应用 syncPolicy 改成 manual；或者用 `ignoreDifferences` 临时挂一条；或者改用一个独立 namespace 不进 AppProject。

## 常见问题

**Q：Argo CD 自己宕机会怎么样？**
A：sync 流水线停。已部署的 workload 不受影响（controller 跟 etcd 不同 round）。从单一集群多 controller HA（Dynamic Cluster Distribution，v2.4+）和跨集群的灾备都要提前规划。

**Q：能不靠 Git 仓库把对象导入 Argo CD 吗？**
A：可以。Application 有一个 source type 叫 `Plain` / `Directory` + `Local` 路径，或用 ApplicationSet + cluster generator。但生产用例下不走 Git 等于放弃 audit trail。

**Q：Argo CD 跟 Flux 怎么选？**
A：Argo CD 是 pull + 多组件，UI 友好，多团队多租户优势明显；Flux 是 controller + 单进程，Kustomize 生态深，CI hook 集成更好。两者都毕业自 CNCF，按团队对 UI、CRD-first 还是 controller-first 的偏好选择。

**Q：跟 Argo Rollouts / Argo Workflows 是什么关系？**
A：同属 argoproj 家族。Argo CD 管 sync 与 reconcile，Argo Rollouts 做渐进式交付（canary / blue-green），Argo Workflows 做 DAG / 批处理。Argo CD Application 的 sync hook 可以调 Rollouts / Workflows，做"迁移 Job + 渐进式切流"。

**Q：如何避免某个用户上手就 sync 生产？**
A：AppProject 内嵌 policy 限定可 sync 应用；外接 dex/SSO 接 OIDC 角色映射；argocd-server 暴露的 UI 也受 RBAC 控制。

**Q：Argo CD 与 Helm 的边界在哪里？**
A：Helm 是 templating + package 工具；Argo CD 是 controller + 多 source 渲染器 + Application CRD。Argo CD 可以渲染 Helm chart，但所有合规/GitOps 行为都由 Argo CD 这一侧负责。

## 总结

Argo CD 的核心价值在 README 的"Why Argo CD"两条 philosophy 里写得很直白——"application definitions, configurations, and environments should be declarative and version controlled"和"application deployment and lifecycle management should be automated, auditable, and easy to understand"。

把全文整理成三句话：

- **架构上**：三个组件（API Server、Repository Server、Application Controller）+ 三类对象（Application、AppProject、ApplicationSet）+ 拉模型 reconcile。理解这一面，整套术语都能落到具体代码包。
- **机制上**：sync 是单次幂等操作，Reconcile 是持续对比 cycle。Drift detection 来自 live vs target diff，selfHeal 把 diff 自动化，prune 把孤儿资源回收。把这三件事独立看，sync 调优才有抓手。
- **管理上**：AppProject + RBAC + 命名空间白名单构成多租户三层边界，但单 controller 是有上限的——多数团队从单集群单 controller 起步，再扩到 HA + 多集群。

它不是万能轮；想让 Argo CD 跑出价值，先把"Git 唯一 source of truth"这一文化跑通，再讨论具体 CRD。否则 selfHeal 会变成自我矛盾：昨晚救场的人，今早被它追回来。

## 自测题

1. 描述 Application / AppProject / ApplicationSet 三个 CRD 的关系，并解释哪个是 reconcile 的核心对象。
2. sync 和 Reconcile 的区别是什么？为什么 drift detection 发生在 Reconcile 而不是 sync？
3. 假设你把一个应用从 Helm 切到 Kustomize，需要修改 Application 哪些字段？Repository Server 渲染流程有何不同？
4. AppProject 的 `sourceRepos` 白名单和 destination 白名单分别防的是哪一类攻击或误操作？
5. 列出至少 3 个会让 selfHeal 带来负面效果的场景，并给出每种场景下的对策。

## 进阶路径

- **Argo Rollouts**：把 sync 这一段从"全量"换成"渐进式"，配合 Argo CD 的 sync hook 触发 rollout。
- **Argo Workflows**：在 pre-sync/post-sync 阶段跑任意 DAG 逻辑，常见用法是做 schema 迁移、数据回填。
- **ApplicationSet Generators**：从 Git Directory 到 PR Generator，把 Git 仓库里的目录结构直接映射到 ApplicationSet 模板。
- **Plugin 体系**：sidecar config management plugin 让 Argo CD 渲染它不原生支持的工具，比如 custom DSL、sealed secret 加密。
- **HA / Disaster Recovery**：Dynamic Cluster Distribution、Redis HA、External Secrets，把单点 controller 的可靠性推到企业级。
- **GitOps Set / kustomize-controller 等**：CNCF 同领域兄弟项目，理解它们和 Argo CD 的取舍面能帮你找最合适的方案。

## 项目资源

- 仓库：[github.com/argoproj/argo-cd](https://github.com/argoproj/argo-cd)
- 官方文档：[argo-cd.readthedocs.io](https://argo-cd.readthedocs.io/)
- Live Demo：[https://cd.apps.argoproj.io/](https://cd.apps.argoproj.io/)
- 架构总览：[Architectural Overview](https://argo-cd.readthedocs.io/en/stable/operator-manual/architecture/)
- 核心概念：[Core Concepts](https://argo-cd.readthedocs.io/en/stable/core_concepts/)
- 项目主页：[https://argoproj.github.io/](https://argoproj.github.io/)
- Slack：[join argoproj workspace](https://argoproj.github.io/community/join-slack)
