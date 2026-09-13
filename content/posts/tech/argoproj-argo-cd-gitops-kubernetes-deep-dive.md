---
title: "Argo CD 深度拆解：GitOps 控制器的同步、漂移修复与多租户边界"
date: 2026-07-14T03:13:50+08:00
slug: "argoproj-argo-cd-gitops-kubernetes-deep-dive"
github_repo: "argoproj/argo-cd"
source_key: "gh:argoproj/argo-cd"
description: "Argo CD 是 Kubernetes 上的声明式 GitOps 持续交付工具，核心由 API Server、Repository Server、Application Controller 三大组件协同。本文拆解其同步机制、漂移修复、Helm/Kustomize/plain 三类任务流，以及多租户边界。"
draft: false
categories: ["技术笔记"]
tags: ["Kubernetes"]
---

# Argo CD 深度拆解：GitOps 控制器的同步、漂移修复与多租户边界

## 核心判断

很多人把 Argo CD 当成"会 watch Git 的 kubectl"。这个理解漏掉了要害：Argo CD 把"集群当前的实时状态"（live state）和"Git 上声明的目标状态"（target state）做成两份可以随时对比的事实，再以 Kubernetes 控制器的形式持续把前者收敛到后者。`kubectl apply` 只执行一次，Argo CD 管的是执行之后的一生。

仓库地址是 [github.com/argoproj/argo-cd](https://github.com/argoproj/argo-cd)，Apache-2.0 协议，Star 约 2.4 万、Fork 约 7.8 千（2026 年 9 月 GitHub API 数据）。Argo 项目 2022 年 12 月从 CNCF 毕业，并通过了 CII Best Practices 检查；当前稳定版 v3.5.x（v3.5.2 发布于 2026 年 8 月）的容器镜像用 cosign 签名，附带满足 SLSA Level 3 的 provenance，可按官方文档用 `cosign verify` 和 `slsa-verifier` 验证。工程量级上，它就是装进集群的一套"GitOps 控制器 + 一组 CRD + 一个 UI + 一个 CLI"。

先给三条判断，全文围绕它们展开：

- **判断 1：Argo CD 是 Kubernetes 控制器，不是 CI 流水线**。它自己以 Deployment 或 StatefulSet 的形式跑在集群里，受 Kubernetes 调度。数据面只有一条路：从 Git 拉取（pull 模型）。Git webhook 只是"有新提交"的信号铃，不传任何清单数据。这决定了它的部署形态、灾备思路和权限设计。
- **判断 2：Application 不是一组 manifest，而是一个 CRD**。Application 是 Argo CD 自定义的 Kubernetes 资源，`spec` 里写的是"我要的最终态"：从哪个仓库哪个目录读、写到哪个集群哪个命名空间、按什么策略同步。manifest 清单只是渲染中间产物，控制器真正盯的是这份 spec 与集群实际状态之间的差。
- **判断 3：sync 是一次幂等操作，Reconcile 才是核心循环**。Sync 是被触发的一次"对齐"；Reconcile 是控制器对每个 Application 周期性执行的循环——对比 live 与 target、刷新 sync status、按策略清理。分清这两个词，self-heal、prune、drift detection 才不会搅在一起。

---

## 系统地图

Argo CD 在集群内部署成 3 个核心组件 + 1 组 CRD + N 个集群凭证。

### 三组件：API Server / Repository Server / Application Controller

| 组件 | 角色 | 关键职责 | 通信方式 |
|------|------|----------|----------|
| **API Server** (`argocd-server`) | 控制平面入口 | 暴露 gRPC/REST API，终端用户、CI、UI 都经它操作 Application；负责认证鉴权；接收 Git webhook 并转发为刷新信号 | gRPC / REST，对外暴露 |
| **Repository Server** (`argocd-repo-server`) | manifest 渲染器 | 拉取并缓存 Git 仓库，调用 Helm/Kustomize/Jsonnet/目录解析等工具，把 Application 引用的 source 渲染成 Kubernetes 对象清单 | 集群内部 gRPC |
| **Application Controller** (`argocd-application-controller`) | reconcile 引擎 | 周期性对比"期望态"（来自 repo-server）与"实时态"（来自 kube-apiserver），计算 diff，刷新 Sync/Health 状态，按策略触发 sync | informer watch + 内部 gRPC |

三个组件默认装在 `argocd` 命名空间，共享 `argocd-cm`、`argocd-secret` 等配置对象。分工上有一条硬边界：Application Controller 从不直接 `git clone`，所有渲染都委托给 Repository Server，自己只保留"对比 → 标记 → 触发 sync"这条主线。

### 三类对象：Application / AppProject / ApplicationSet

Argo CD 注册的核心 CRD 有三个：

- **Application**：最小交付单位。`spec` 写明 source（仓库 URL + revision + path）、destination（目标集群 + 命名空间）、同步策略、忽略差异规则等。控制器周期比对 spec 与目标集群，结果分两轨写进 `status`：sync 状态（Synced / OutOfSync，在 `status.sync.status`）和健康状态（Healthy / Degraded / Suspended 等，在 `status.health.status`）。
- **AppProject**：项目级隔离面。限定可引用的源仓库白名单、可部署的目标集群与命名空间白名单、cluster-scoped 资源白名单，可配 SyncWindow 和 RBAC policy。Application 必须挂在某个 AppProject 下，越界请求会被拒收并记录 condition。
- **ApplicationSet**：扇出器。从 Git 目录、Cluster 列表、Pull Request/Merge Request、SCM Provider 等生成器（generator）取输入，按模板批量生成 Application。同一份 chart 要铺 12 个环境，写一个 ApplicationSet 而不是 12 份 YAML。

ApplicationSet 自己不部署任何东西：它把数据源拆成 N 份模板参数，产出 N 个 Application CR，然后交给标准同步流程。

### 多集群：单 controller 联邦，凭证用 Secret

Argo CD 装在"中心集群"，管理一组"外部集群"（含自身的 in-cluster）。每个外部集群在中心集群里只是一个 Secret，存 bearer token + API server 地址或 kubeconfig。Application 的 destination 字段按名字引用这些集群。

所有 reconcile 都发生在中心集群，外部集群只需要暴露标准 kube-apiserver。代价是：中心集群宕机，drift detection 一起停。这是 pull 模型的固有属性，做灾备方案时必须考虑。

### 异步流水线：一次 reconcile 的关键链路

1. API Server 接收 Application 的创建/更新，或收到 Git webhook 事件；
2. Application Controller 通过 informer 感知 Application CR 变化，进入工作队列；
3. Controller 按 source 字段向 Repository Server 请求最终 Kubernetes 对象清单；
4. Controller 清单中的每个对象，经 informer 从目标集群 kube-apiserver 取真实对象，做 diff；
5. 结合 diff 与同步策略决定是否触发 sync，把结果写回 `Application.status`；
6. sync 时通过 Kubernetes API 写目标集群（走 client-go 的 patch 语义，不是调用 kubectl）。

全链路用 watch/list 而不是轮询（controller 端走 informer，repo-server 端用 `git ls-remote` + 内部缓存），所以不会产生"高频 cron 拉 Git"的开销。

## 边界拆分：source 与 destination、渲染工具、隔离面

### 边界 1：读哪里 vs 写哪里

| 概念 | 字段 | 含义 |
|------|------|------|
| Source | `spec.source.repoURL` + `spec.source.targetRevision` + `spec.source.path` | 从哪个仓库的哪个分支/commit 的哪个目录读 |
| Destination | `spec.destination.server` + `spec.destination.namespace` | 渲染结果写到哪个集群的哪个命名空间 |
| 观测结果 | `status.sync.status` / `status.health.status` | 只读的状态轨，不参与 manifest 决策 |

`source` 是"读哪里"，`destination` 是"写哪里"。仓库不是唯一的 source 形态：Helm chart（含 OCI 引用）和插件输出同样作为 source；destination 支持本地集群与已注册的外部集群。

### 边界 2：manifest 渲染工具

| 工具 | 何时启用 | 如何被调起 |
|------|----------|--------------------|
| **目录（plain YAML）** | 目录下是普通 K8s YAML | repo-server 直接解析并拆分文档 |
| **Helm** | 目录含 `Chart.yaml` | 用内置 Helm v3 渲染，values 可写在 `spec.source.helm` |
| **Kustomize** | 目录含 `kustomization.yaml` | 用内置 kustomize 二进制渲染（可用 sidecar 挂多版本） |
| **Jsonnet** | 目录含 `.jsonnet` | 用 jsonnet 渲染 |
| **插件（CMP）** | 配置了 config management plugin | 由 repo-server 的 sidecar 插件容器经 Unix socket 处理 |

检测逻辑在 repo-server：`spec.source` 里显式写了 `helm:` / `kustomize:` / `plugin:` 等配置节时直接按显式类型走；没写则按目录标记文件自动发现。注意一个细节：同一目录里 `Chart.yaml` 和 `kustomization.yaml` 并存时，自动检测的结果偏向 Kustomize——想让行为可预期，就显式声明类型。一个 Git 仓库混用多种工具没问题，但结构复杂的 monorepo 要留意嵌套目录被误检的副作用。

### 边界 3：三种隔离面

| 隔离面 | 靠什么 | 控制字段 |
|--------|------|----------|
| 集群隔离 | destination | `spec.destination.server` 引用哪个集群 Secret |
| 命名空间隔离 | destination + AppProject | `spec.destination.namespace` + AppProject 的 `destination` 白名单 |
| 用户操作隔离 | AppProject RBAC | AppProject 内嵌 `roles`/`policies`，用户绑定 role 后只能操作本项目内的 Application |

四类约束叠起来才是完整的多租户：源仓库靠 `sourceRepos` 白名单，目标环境靠 destination 白名单，资源种类靠 cluster/namespace 资源白名单，人的操作靠 RBAC policy。后面"多租户边界"一节逐个展开。

## 关键机制：同步、漂移修复、孤儿资源清理

把 sync、Reconcile、drift detection、prune 四件事拆开看。

### sync：一次幂等操作

sync 把 target state 应用一次到目标集群。实现在 Application Controller 的 `appcontroller` 包，底层不是"把整个 YAML apply 上去"，而是先算出期望对象清单，再逐对象写入 kube-apiserver。写入语义取决于是否开启 Server-Side Apply：

- 默认（未开 SSA）：走 kubectl 式 three-way merge。Argo CD 给每个对象维护 `kubectl.kubernetes.io/last-applied-configuration` 注解，据此算 diff 后做 strategic merge patch；CRD 这类没有 scheme 的类型退化为 JSON merge patch。语义与 `kubectl apply` 一致，能正确删除"上一次 apply 之后从声明里消失的字段"。
- 开启 SSA（`syncOptions: [ServerSideApply=true]`）：改用 Kubernetes 原生 Server-Side Apply，字段所有权（field manager）和冲突检测交给 API server，客户端不再依赖 last-applied 注解。

这条区别在混用工具时最要命：默认模式下，如果对象被 kubectl 或其他 CD 以不完整注解改过，last-applied 会失真；SSA 把合并逻辑移进 API server，冲突时给出明确报错，是多租户共享集群下更稳的选择。

sync 的开关都写在 Application CR 里：

- `syncPolicy.automated`：开启后 drift 一经发现即自动 sync，这是 self-heal 的来源；
- `syncPolicy.automated.prune`：是否删除"目标态里没有、集群里却有"的对象（孤儿资源）；
- `syncPolicy.automated.selfHeal`：是否追回集群侧的本地改动；
- `syncPolicy.automated.allowEmpty`：源目录被清空时是否允许同步成空；
- `syncOptions` 里的 `PrunePropagationPolicy`：决定删除的传播方式（foreground / background / orphan）。

sync 是幂等的：同一份源同步两次，结果一样。所以外部工具（kubectl、Helm、Terraform）改了集群也不要紧——Argo CD 检测到 drift，再 sync 一次就拉回 Git 声明的状态。

### Reconcile 与 drift detection

Application Controller 对每个 Application 跑一个 reconcile loop：

1. 按 source hash 查缓存，未命中则让 repo-server 重新渲染；
2. 拿渲染结果与目标集群的实际对象做 diff；
3. 把结果写进 status；若 `automated` 与 `selfHeal` 都开着且发现 drift，就触发 sync。

`selfHeal` 是漂移修复的开关。打开后，任何集群侧改动（手工 kubectl、别的工具、节点上的意外变更）都会在下一个 reconcile 周期被追回——Git 永远赢。关掉则只标 OutOfSync，等人工处理。

轮询节奏由两个参数控制：`--app-resync` 默认 120 秒、`--app-resync-jitter` 默认再加最多 60 秒抖动（可用 `argocd-cm` 的 `timeout.reconciliation` 覆盖）。也就是说，没有 webhook 的最坏情况下，一个变更最多约 3 分钟被发现。`--self-heal-timeout-seconds` 默认 0，不额外设阈值；自愈失败后按指数退避重试（初始 2 秒、上限 300 秒、冷却 330 秒后重置），避免和应用故障互相踩踏。配好 Git webhook 后，commit 一落地就能触发刷新，不必等整轮轮询。

### Prune：孤儿资源清理

Prune 在 sync 阶段顺带删除"Git 里已经没有、集群里还留着"的对象。三种典型场景：

- 应用换 chart：旧 chart 有个 ConfigMap，新 chart 删掉了它；开 prune 后这个 ConfigMap 被自动清掉；
- 手工改动被追回：有人 `kubectl edit` 改了 Deployment，下一次 reconcile 标 OutOfSync，selfHeal 把它拉回 Git 声明的样子；
- 跨 Application 共享对象：两个 Application 都要创建同名 ConfigMap 时，开 prune 很容易互相误删——共享对象应放进独立 Application，或对该对象关 prune。

"删除目标态之外的对象"这个语义是 Argo CD 补上的，Kubernetes 原生 apply 没有。它换来的代价是误删面变大：任何不在 Git 声明里、但确实被别的系统管理的对象（比如某个 controller 自动生成的资源）都可能被 prune 掉。所以官方建议的顺序永远是：先关 prune 跑稳 drift detection，再分环境放开。

### SyncWindow：变更节奏护栏

SyncWindow 限制"什么时间段允许 sync"，不是调频率。常见用法：生产环境只允许 22:00–06:00 自动 sync，其余时间的变更留在 OutOfSync 状态，等窗口打开或人工放行。窗口可以按 AppProject 或 Application 匹配，也能配 deny 窗口硬停。

## 一次真实任务穿过系统

### 场景设定

一个 SaaS 团队有两个对象：

- Application `web`：repo `git@github.com/acme/web.git`，path `deploy/prod`，Helm 渲染，部署到 production 集群的 `web` 命名空间；
- AppProject `web-team`：限定项目内 Application 只能引用 `github.com/acme/*`，只能部署到 production 集群的 `web` 和 `staging-web` 命名空间。

### 步骤 1：开发者合并 PR

开发者改了 `deploy/prod/values.yaml`，PR 合入 main。GitHub 通过 webhook 通知 Argo CD API Server（payload URL 配的是 `/api/webhook` 端点）。API Server 核对事件与哪些 Application 相关，给它们打上 `argocd.argoproj.io/refresh` 注解——这是一次刷新请求，不携带任何清单数据。

### 步骤 2：Application Controller 触发 Reconcile

Controller 感知到 refresh 注解后立刻处理这个 Application，不等 120 秒的周期。它拿着 source 定义去问 Repository Server："渲染 `git@github.com/acme/web.git@main` 在 `deploy/prod` 下的最终对象清单。"

### 步骤 3：Repository Server 渲染 manifest

repo-server 内部：

1. 用 Application 配置的 Git 凭证（Secret 里的 SSH key 或 HTTPS token）执行 `git ls-remote`，把 `main` 解析成具体 commit；
2. 检出该 commit 到缓存目录，识别渲染工具：`deploy/prod/Chart.yaml` 存在 → 调 Helm v3，把 values 和模板渲染成 Kubernetes 对象清单；
3. 渲染结果按 revision 等要素缓存，同一 commit 下次直接复用。

如果目录里同时有 `kustomization.yaml`，自动检测会偏向 Kustomize；想精确控制，在 `spec.source` 里显式写 `kustomize:` 或 `helm:` 配置节，跳过自动检测。

### 步骤 4：Application Controller 做 diff

拿到期望对象清单（假设是 6 个 Deployment + 6 个 Service + 1 个 ConfigMap + 1 个 Ingress）后，Controller 经 informer 从 production 集群取实际对象，逐个 diff。结论例如：只有 Deployment `web` 的 image 从 `v1.4.2` 变成 `v1.5.0`，其余全部对齐——Application 被标 OutOfSync。

### 步骤 5：sync 写入集群

`automated=true` 且 `selfHeal=true` 时，Controller 直接发起 sync：

- 按前述默认 three-way merge 或 SSA 语义，把新 Deployment patch 进 production 集群；pod 模板变了，Kubernetes 新建 ReplicaSet 并逐批替换 Pod；
- 声明里带 sync hook 的对象按序执行——`argocd.argoproj.io/hook: PreSync` 的 Job 会先跑（数据库迁移常这么挂），然后是 `Sync`，最后 `PostSync`；
- 本例 prune 清单为空，跳过删除。

sync 完成后 `status.sync.status` 变成 `Synced`；等 Pod 真正 ready，`status.health.status` 才变成 `Healthy`。健康判定由内置的 health check（Lua 脚本，按 kind 注册，可自定义扩展）完成：对 Deployment 检查副本的就绪情况，不逐个读 Pod。

**这里有一层默认看不见的机制**：Argo CD 凭什么知道"这个 Deployment 属于哪个 Application"？靠给托管对象打跟踪标记。资源跟踪方法由 `application.resourceTrackingMethod` 配置，默认 `annotation`——在对象上写 `argocd.argoproj.io/tracking-id` 注解（内容形如 `web:apps/Deployment:default/web`，即应用名:组/类型:命名空间/名字）；可选值还有 `label`（只用 `app.kubernetes.io/instance` 标签）和 `annotation+label`（注解跟踪、标签仅供其他工具识别）。跟踪标记决定三件事：健康推断时收集哪些对象、diff 时怎么对齐、prune 时哪些算"本应用该管的"。所以两个 Application 声明同一批对象时，归属判定会打架，健康状态和 prune 都会互相污染——这是前文"共享对象要单独放"的根本原因。

### 步骤 6：失败回滚

sync 之后健康掉到 Degraded，wave/hook 的顺序不会自动倒带。Argo CD 的"回滚"是把应用 sync 到历史里的上一个可用 revision：`argocd app rollback` 本质就是一次指向历史版本的特殊 sync。历史长度由 Application 的 `spec.revisionHistoryLimit` 控制，默认 10。另外有个前提：开启 auto-sync 的应用不允许 rollback，得先关掉自动同步。

## 多租户边界：AppProject + RBAC + 资源白名单

### 1. 源仓库白名单

`AppProject.spec.sourceRepos` 支持 URL 字面量和 glob（如 `https://github.com/acme/*`）。项目内 Application 的 `spec.source.repoURL` 不在白名单里就被拒收，请求记入 condition，不会部署。这条堵住了"工程师随手把生产应用指向任意仓库"的口子。

### 2. 集群 + 命名空间白名单

`spec.destinations` 列出项目允许的"集群 + 命名空间"组合，是把开发环境和生产环境分开的关键约束。cluster-scoped 资源（CRD、ClusterRole 等）另有 `clusterResourceWhitelist`：自定义 AppProject 默认白名单为空，即默认禁止创建任何 cluster-scoped 资源；需要放行时逐条加白。内置的 `default` project 恰好相反，默认全放开——多租户场景第一条守则就是别用 default project 装业务应用。

### 3. AppProject 内嵌 RBAC Policy

每个 AppProject 可定义 `policies`，格式是 RBAC 风格的六元组 `p, 主体, 动作, 资源, 对象, 效果`，对象字段用 `项目名/应用名`：

```yaml
policies:
  - p, proj:web-team:dev, applications, get, web-team/*, allow
  - p, proj:web-team:dev, applications, sync, web-team/guestbook-dev, deny
```

policy 在 argocd-server 鉴权时读取，能做到"张三只能看本项目的应用、不能对某个指定应用执行 sync"。对中型平台团队，这层直接省掉一个自建审批系统。

### 4. 全局 RBAC 与 SSO

项目级 policy 之外，`argocd-rbac-cm` ConfigMap 定义全局的角色到用户/组的映射；身份源接 OIDC / SAML / LDAP 时可走内置 dex（`argocd-dex-server`），已有的 OIDC provider 也可以直连、不经 dex。两层配置都记录在官方 RBAC 文档里。

### 这层边界不卡什么

AppProject 不是 namespace。分属不同 AppProject 的 Application 仍跑在同一个 controller 进程里，共享同一份 repo-server 缓存——某个项目里的应用反复触发渲染，拖慢的是所有人的 repo-server。cluster-scoped 资源默认是禁的，但只要某个项目加了白名单，它创建的 CRD、ClusterRole 影响的就是整个集群。多租户评估时，这两条要一起看。

## 采用建议

### 推荐采用顺序

1. **从 standalone 单集群开始**：在 dev/staging 起一个 Argo CD，托管一两个无状态服务；
2. **用 Application 替代脚本**：把 `helm install` 改写成 Application CR，第一周保留手动 sync；
3. **加 AppProject 隔离**：每个团队一个项目，先配 source 白名单，再配 destination 白名单；业务应用搬出 default project；
4. **再开 selfHeal**：开 `automated` + `selfHeal`，但 prune 保持关闭，让 drift detection 先稳定跑一周；
5. **开 prune**：先在 staging 验证无误删，再带到生产；
6. **接 ApplicationSet**：模板相同的多环境从一份 ApplicationSet 扇出；
7. **接 SyncWindow 与 Resource Hook**：生产 sync 限制到夜间；用 PreSync Job 做数据库迁移；
8. **观测与告警**：接 Notifications（Slack / Alertmanager），drift 或 sync 失败实时通知。

### 不适合 Argo CD 的场景

- **没有 Kubernetes 集群**：纯静态文件发 S3/OSS 之类，Argo CD 帮不上；
- **超大单实例规模**：单个 controller 实例的吞吐有上限，集群规模上去要走 sharding 多副本；Dynamic Cluster Distribution（v2.9 起，Alpha、默认关闭）支持副本增减时自动重分布，但生产启用前要评估成熟度；
- **集群无法出网拉代码**：pull 模型要求能从集群内访问 Git；
- **一次性批处理**：那是 Argo Workflows 的地盘，Argo CD 管的是持续运行的部署对象。

## 常见翻车现场

### 翻车 1：永远 OutOfSync，diff 看不出差别

- **症状**：status 显示 OutOfSync，点开 diff 却找不到有意义的差别。
- **原因**：对象带 status 子字段（CRD 常见）、自动生成的时间戳或注入的 hash 注解，这些"非 spec 差异"被算进了对比。
- **修法**：用 `ignoreDifferences` 精确排除。比如忽略 Deployment 的 `spec.replicas`（配合 HPA 是标准做法）：

```yaml
ignoreDifferences:
  - group: apps
    kind: Deployment
    jsonPointers:
      - /spec/replicas
```

### 翻车 2：prune 失败，报 Forbidden

- **症状**：sync 日志里出现 `Error from server (Forbidden): ... cannot delete resource`，但管理员手动删没问题。
- **原因**：Argo CD 在目标集群用的 ServiceAccount 缺 delete 权限——配置目标集群凭证时给的 role 太窄。
- **修法**：检查目标集群的 ClusterRole，确认包含 `delete` / `list` / `patch` 等动词；临时规避可在 Application 上调整 syncOptions 跳过 prune。

### 翻车 3：Helm values 里的 secret 渲染成空

- **症状**：模板里引用 `{{ .Values.db.password }}`，sync 后 Pod 起不来，环境变量是空的。
- **原因**：这个值在集群里才存在（或由外部系统管理），Git 里的 values 根本没有它——Argo CD 只做声明式渲染，不会帮你从别处取 secret。把真实密码写进 values 又会让它进 Git，两头都不对。
- **修法**：把 secret 从 Helm values 里拆出去，交给专门机制管理：External Secrets Operator、Sealed Secrets，或 argocd-vault-plugin 这类插件，在部署阶段把值注入集群，Git 里只留引用。

### 翻车 4：ApplicationSet 重渲染风暴

- **症状**：模板一改，几百个派生 Application 同时 OutOfSync、同时 reconcile，controller CPU 打满。
- **原因**：ApplicationSet 一次生成所有 Application，同步没有内建节流。
- **修法**：用 Progressive Syncs 分批推进（v3.3 起 Beta，需通过 flag 或 ConfigMap 显式开启，通过 `strategy` 配置 RollingSync，前一批恢复 Healthy 才放下一批）；或者按环境拆成多个 ApplicationSet，缩小一次性扇出的爆炸范围。

### 翻车 5：selfHeal 追回人工 debug 改动

- **症状**：排障时 `kubectl edit` 改了 Deployment 的参数，第二天被 Argo CD 自动改回去。
- **原因**：selfHeal 开启后，Git 永远赢，任何集群侧改动都是"漂移"。
- **修法**：排障期间把该应用的 `syncPolicy.automated` 暂时关掉，或临时加一条 `ignoreDifferences`；更干净的做法是在不纳入 Argo CD 管理的独立 namespace 里复现问题。

## 常见问题

**Argo CD 自己宕机会怎么样？**

sync 流水线停，已部署的 workload 不受影响——这正是 pull 模型的隔离性。恢复要提前规划：HA manifests 起多副本并把 Redis 切 HA 模式，controller 分片多副本分担集群，再配灾备。

**Argo CD 跟 Flux 怎么选？**

两者都是 CNCF 毕业项目。Argo CD 是多组件 + UI + Application CRD 驱动，多团队多租户友好；Flux 是 controller + 单进程形态，与 Kustomize 生态贴合更深。按团队对 UI、CRD-first 还是 controller-first 的偏好选，两条路线都有大规模生产背书。

**跟 Argo Rollouts / Argo Workflows 是什么关系？**

同属 argoproj。Argo CD 管 sync 与 reconcile，Argo Rollouts 做渐进式交付（canary / blue-green），Argo Workflows 做 DAG / 批处理。Application 的 sync hook 可以衔接 Rollouts 和 Workflows。

**Argo CD 与 Helm 的边界在哪里？**

Helm 是模板与打包工具，Argo CD 是控制器 + 渲染调度器。Argo CD 可以把 Helm chart 作为 source 渲染，但 GitOps 的合规要求——审计、漂移修复、权限——由 Argo CD 这一层负责。Helm release 的状态记录在集群 Secret 里，而 Argo CD 的真相在 Git，两者不要混用同一批对象。

## 项目资源

- 仓库：[github.com/argoproj/argo-cd](https://github.com/argoproj/argo-cd)
- 官方文档：[argo-cd.readthedocs.io](https://argo-cd.readthedocs.io/)
- Live Demo：[https://cd.apps.argoproj.io/](https://cd.apps.argoproj.io/)
- 架构总览：[Architectural Overview](https://argo-cd.readthedocs.io/en/stable/operator-manual/architecture/)
- 核心概念：[Core Concepts](https://argo-cd.readthedocs.io/en/stable/core_concepts/)
- 签名验证：[Verification of Argo CD Artifacts](https://argo-cd.readthedocs.io/en/stable/operator-manual/signed-release-assets/)
- 项目主页：[https://argoproj.github.io/](https://argoproj.github.io/)
- Slack：[join argoproj workspace](https://argoproj.github.io/community/join-slack)
