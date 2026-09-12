---
title: "Harbor：CNCF 云原生容器注册表的技术指南"
date: "2026-04-09T12:40:00+08:00"
slug: "harbor-cncf-cloud-native-registry-guide"
github_repo: "goharbor/harbor"
source_key: "gh:goharbor/harbor"
description: "Harbor 是由 CNCF 托管的开源云原生容器注册表，提供容器镜像和 Helm Chart 存储、签名、扫描、复制、权限管理等功能。本文深入解析 Harbor 的架构设计、核心组件、高可用部署、安全机制以及与 Kubernetes 的集成。"
draft: false
categories: ["技术笔记"]
tags: ["Kubernetes"]
---

# Harbor：CNCF 云原生容器注册表的技术指南

Harbor 真正解决的不是「存镜像」——Docker Hub 和云厂商的 ECR / ACR 都能存镜像。Harbor 解决的是：当你的组织需要自建一套镜像仓库，同时还要合规、要权限隔离、要跨数据中心同步、要镜像签名和漏洞扫描这条完整链路时，怎么把这些需求组装成一套可运维的系统。

本文从三个角度展开：

1. 结构层面：Harbor 的组件拆了什么、每层存储怎么配合，让你知道出问题时该看哪个容器日志。
2. 流转层面：一次镜像推送在 Harbor 里经历了什么——认证、存储、扫描、签名、复制，每一步的触发条件和失败后果。
3. 决策层面：什么场景下该用 Harbor 而不是云厂商的托管注册表，部署时副本数、存储选型、灾备策略怎么定。

默认读者已经用过 `docker push` / `docker pull`，但对自建注册表的技术选型还不确定。

## 学习目标

读完本文后，你应能：

- 说清 Harbor 解决的五个问题（分发效率、安全合规、权限控制、多格式支持、审计追溯）以及它和 Docker Hub / ECR / ACR 的边界划在哪里。
- 跟着一次镜像推送走完认证、存储、扫描、签名、复制五条独立链路，定位每条链路失败时该看哪个组件日志。
- 在 Harbor 和云厂商托管注册表之间做选型时，能列出自建与托管在合规、多数据中心、RBAC、运维成本四个维度上的真实差异。
- 判断自己的场景该用代理缓存还是复制策略，以及推送模式和拉取模式分别对应什么网络拓扑。

**目录**

- [2. 项目背景与生态定位](#2-项目背景与生态定位)
- [3. 核心功能详解](#3-核心功能详解)
- [4. 系统架构深度解析](#4-系统架构深度解析)
- [5. 一次镜像推送的完整流转](#5-一次镜像推送的完整流转)
- [6. 安装与配置](#6-安装与配置)
- [7. 运维管理](#7-运维管理)
- [8. 安全加固](#8-安全加固)
- [9. 最佳实践](#9-最佳实践)
- [10. 怎么选、怎么上线](#10-怎么选怎么上线)
- [11. 常见问题](#11-常见问题)

## 2. 项目背景与生态定位

### 2.1 云原生场景下注册表要解决什么

在云原生环境中，容器镜像的存储与管理需要同时面对五个问题：

| 问题 | 具体表现 | Harbor 的做法 |
|------|----------|---------------|
| 分发效率 | 跨集群、多环境镜像传输慢 | 近源存储、复制策略 |
| 安全合规 | 镜像漏洞、签名伪造 | 漏洞扫描、内容签名 |
| 权限控制 | 不同团队、项目需要隔离 | RBAC + 项目级权限 |
| 多格式支持 | Docker 镜像 + Helm Chart | OCI 标准兼容 |
| 审计追溯 | 谁在什么时间做了什么 | 完整操作日志 |

### 2.2 Harbor 的定位

**Harbor 是什么？**

> Harbor is an open source trusted cloud native registry project that stores, signs, and scans content.

**官方定义**：Harbor 是一个开源的可信云原生注册表项目，用于存储、签名和扫描容器镜像及 Helm Chart。

**托管方**：CNCF（Cloud Native Computing Foundation，云原生计算基金会）。

Harbor 的四个关键能力：

```
┌─────────────────────────────────────────────────────────────┐
│                      Harbor 关键能力                        │
├─────────────────────────────────────────────────────────────┤
│  OCI 兼容：Docker Image + Helm Chart + OCI Artifact         │
│  安全可信：内容签名 + 漏洞扫描 + 权限控制                   │
│  高可用：多主复制 + 故障转移 + 水平扩展                     │
│  易集成：RESTful API + Webhook + Kubernetes Operator        │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 竞品对比

| 维度 | Harbor | Docker Hub | AWS ECR | 阿里云 ACR |
|------|--------|-----------|---------|-----------|
| 开源 | Apache-2.0 | 闭源 | 闭源 | 闭源 |
| 本地部署 | 完全自控 | SaaS | 云服务 | 云服务 |
| Helm 支持 | 原生 | 有限 | 支持 | 支持 |
| 漏洞扫描 | 免费 | 付费 | 支持 | 支持 |
| 多租户 | 项目级 | 不支持 | 支持 | 支持 |
| 复制同步 | 策略驱动 | 不支持 | 跨账户 | 支持 |

## 3. 核心功能

### 3.1 功能全景图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Harbor 功能矩阵                          │
├────────────────┬────────────────┬────────────────┬───────────────┤
│   存储分发      │     安全      │     管理      │    集成     │
├────────────────┼────────────────┼────────────────┼───────────────┤
│ 容器镜像存储    │ 漏洞扫描      │ 多项目管理    │ Kubernetes   │
│ Helm Chart     │ 内容签名      │ RBAC 权限     │ Helm/OCI     │
│ OCI Artifact   │ Notary 信任   │ LDAP/AD 集成  │ RESTful API  │
│ 代理缓存       │ 镜像删除 GC   │ 审计日志      │ Webhook      │
│ 多注册表复制   │ OIDC 单点登录 │ 用户组管理    │ Harbor API   │
└────────────────┴────────────────┴────────────────┴───────────────┘
```

### 3.2 云原生注册表

Harbor 作为云原生注册表，支持以下产物类型：

| 类型 | 说明 | 典型用途 |
|------|------|----------|
| Docker 镜像 | OCI Image Manifest 格式 | 容器化应用分发 |
| Helm Chart | Kubernetes 包管理 | 应用模板分发 |
| OCI Artifact | 通用 OCI 产物 | 任意二进制分发 |

支持的 Helm 版本：Helm 2 / Helm 3，兼容 Chartmuseum。

### 3.3 基于角色的访问控制（RBAC）

Harbor 采用项目级权限模型：

```
┌─────────────────────────────────────────────────────────────┐
│                    Harbor 权限模型                          │
├─────────────────────────────────────────────────────────────┤
│  系统级：                                                  │
│  ├── sysAdmin（系统管理员）：管理所有项目、用户、系统配置   │
│  └── anonymous（匿名用户）：只读公共项目                   │
│                                                             │
│  项目级：                                                   │
│  ├── projectAdmin（项目管理员）：管理项目成员、策略         │
│  ├── developer（开发者）：推送/拉取镜像                    │
│  ├── guest（访客）：仅拉取公共/授权镜像                    │
│  └── maintainer（维护者）：高级开发者权限                   │
└─────────────────────────────────────────────────────────────┘
```

各角色的实际操作权限：

| 角色 | 拉取 | 推送 | 删除 | 管理成员 | 管理策略 |
|------|------|------|------|----------|---------|
| guest | 可以 | 不可以 | 不可以 | 不可以 | 不可以 |
| developer | 可以 | 可以 | 不可以 | 不可以 | 不可以 |
| maintainer | 可以 | 可以 | 可以 | 不可以 | 不可以 |
| projectAdmin | 可以 | 可以 | 可以 | 可以 | 可以 |
| sysAdmin | 可以 | 可以 | 可以 | 可以 | 可以 |

### 3.4 基于策略的复制

Harbor 的复制功能支持多种同步场景。

#### 3.4.1 复制模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| Push 模式 | 本地 Harbor 推送到远程 | 灾备复制、主节点分发 |
| Pull 模式 | Harbor 从远程注册表拉取 | 中心-边缘去中心化解耦 |

Push 与 Pull 在端点语义上相反，实际由复制策略中的方向决定。多数据中心通常会为两个站点各配置一条方向相反的策略，形成双向同步。

#### 3.4.2 复制过滤器

复制策略通过仓库名与标签匹配来筛选同步对象：

```
复制策略配置：
├── 仓库过滤器
│   ├── 仓库名称模式：匹配哪些仓库（如：project/*）
│   └── 排除模式：排除哪些仓库（如：project/internal）
├── 标签过滤器
│   ├── 标签模式：匹配哪些标签（如：release-*）
│   └── 排除模式：排除哪些标签（如：latest）
```

#### 3.4.3 复制触发器

| 触发方式 | 说明 |
|----------|------|
| 手动 | 管理员手动触发 |
| 定时 | Cron 表达式定时同步 |
| 事件驱动 | 镜像推送时自动触发 |

### 3.5 漏洞扫描

Harbor 集成 Trivy 作为漏洞扫描器。

#### 3.5.1 扫描流程

```
镜像推送 → 触发扫描 → 提取 Layer → 对比 CVE 数据库 → 生成报告
                              ↓
                      严重程度分级
                              ↓
                    高危 → 阻止部署策略
                    中危 → 警告
                    低危 → 允许
```

#### 3.5.2 CVE 严重级别

| 级别 | 阈值配置 | 默认动作 |
|------|----------|----------|
| Critical（严重） | ≥ 9.0 | 阻止部署 |
| High（高危） | ≥ 7.0 | 警告 |
| Medium（中危） | ≥ 4.0 | 允许 |
| Low（低危） | < 4.0 | 允许 |

#### 3.5.3 阻止策略配置

在项目设置里开启「自动扫描」并配置阻止级别：

```
项目 → Configuration → Security
├── 自动扫描新镜像：开启
├── 阻止级别（Block on CVE）：Critical / High 任选
└── 否满足条件：仅拦截未通过门槛的镜像拉取与复制
```

CVE 评分取 CVSS v3 基准分，来自 Trivy 拉取的漏洞数据库。

### 3.6 内容签名与 Notary

Harbor 通过 Docker Notary 实现镜像签名。签名由 Notary 签名服务（Notary Server + Notary Signer）维护，与镜像内容分开存储。

#### 3.6.1 信任模型

```
推镜像时：
  开发者本地持有 root / targets 私钥
  → 对镜像 tag 的摘要生成签名
  → 签名连同信任链上传到 Notary Server

拉镜像时：
  docker 开启 DCT（Docker Content Trust）
  → 从 Notary Server 拉取信任元数据
  → 比对签名与镜像摘要是否匹配
```

#### 3.6.2 签名验证流程

1. **签名阶段**：开发者使用私钥对镜像 tag 进行签名，签名信息随信任链一起存储到 Notary。
2. **验证阶段**：Docker Client 请求镜像时向 Notary 获取信任元数据，验证签名的完整性。
3. **部署策略**：可配置为「仅允许已签名镜像」，Kubernetes 用 Admission Controller 结合 Notary 验证后放行。

## 4. 系统架构

### 4.1 整体架构

Harbor 由一组独立的 Go 服务组成，控制面与数据面分离：

```
                 ┌─────────────┐
                 │    Portal    │  Angular 单页管理 UI
                 └──────┬──────┘
                        │
                 ┌──────┴──────┐
                 │    核心服务   │  Harbor Core（API + 调度 + 配置）
                 └──────┬──────┘
        ┌───────────────┼────────────────┐
        │               │                │
┌───────┴───────┐ ┌─────┴──────┐ ┌──────┴────────┐
│  Registry(distribution) │ │ Job Service │ │ Notary Server/Signer │
└───────┬───────┘ └─────┬──────┘ └───────────────┘
        │               │
        │ (对象存储)      │（调度扫描/复制/GC 任务）
┌───────┴───────────────┴───────┐
│        PostgreSQL（元数据）     │
│        Redis（会话/缓存）       │
│        S3 / GCS / OSS / 本地    │（镜像 Blob）
└───────────────────────────────┘
```

### 4.2 核心组件职责

| 组件 | 技术栈 | 职责 |
|------|--------|------|
| Portal | Angular/TypeScript | Web 管理界面 |
| Harbor Core | Go | RESTful API、认证、项目与策略管理 |
| Registry | Go/Docker Distribution | 镜像存储分发 |
| Job Service | Go | 异步任务（复制、扫描、GC） |
| Notary Server/Signer | Go/Notary | 签名服务，维护信任元数据 |
| Trivy Adapter | Go | 调用 Trivy 做漏洞扫描 |
| PostgreSQL | DB | 元数据、审计日志、任务状态 |
| Redis | Cache | 会话与缓存 |

## 5. 一次镜像推送的完整流转

以「开发者推送一个带签名的镜像到 Harbor，并要求漏洞扫描」为例，把前面讲的组件串起来。

### 5.1 初始化状态

- Harbor 已部署，hostname 为 `registry.example.com`。
- 项目 `myproject` 已创建，配置了漏洞扫描策略：Critical 级别阻止部署。
- 开发者本地已配置 Docker Content Trust。

### 5.2 推送流程

**Step 1：认证**

```bash
docker login registry.example.com
```

Docker Client 向 Harbor 发送认证请求。Harbor Core 校验凭据（本地数据库或 LDAP/OIDC），生成 JWT Token 返回。后续所有操作都携带此 Token。

**Step 2：推送镜像**

```bash
docker push registry.example.com/myproject/myapp:1.0.0
```

Registry 组件接收推送请求。镜像 Layer 按块写入存储后端（S3 / GCS / OSS / 本地文件系统）。每层写入完成后，Registry 向 PostgreSQL 写入一条 blob 记录和 Image Manifest。

**Step 3：触发扫描**

镜像 Manifest 写入成功后，Harbor Core 创建扫描任务交给 Job Service，Job Service 调用 Trivy Adapter。Trivy 解压镜像各层、对比 CVE 数据库，生成漏洞报告写回 PostgreSQL。

如果扫描结果中有 Critical 级别漏洞，Harbor 会在该镜像上标记「不可部署」，并拒绝后续拉取请求（前提是项目已开启阻止策略）。

**Step 4：签名**

如果开发者启用了 Docker Content Trust：

```bash
export DOCKER_CONTENT_TRUST=1
docker push registry.example.com/myproject/myapp:1.0.0
```

Notary Signer 生成签名与信任元数据，存入 Notary 的数据库。此后，任何拉取该镜像的客户端如果也开启了 DCT，Docker 会自动从 Notary 获取信任链验证签名。

**Step 5：复制（可选）**

如果项目配置了复制策略（例如推送到灾备站点），Job Service 在镜像推送成功后触发复制任务，将镜像同步到目标注册表。复制任务的状态和进度记录在 PostgreSQL 中，可通过 API 或 Portal 查看。

### 5.3 拉取流程

1. `docker pull registry.example.com/myproject/myapp:1.0.0`：Docker Client 携带 Token 向 Harbor Core 发起拉取请求。
2. Harbor Core 验证 Token，检查用户对 `myproject` 的权限（至少需要 guest）。
3. Harbor Core 检查该镜像是否被阻止部署（扫描策略结果）。
4. 通过后，返回 Registry 的 blob 下载地址。
5. Docker Client 从 Registry 拉取各 Layer。

### 5.4 五条独立链路，一个共享状态

上面这次推送把 Harbor 的五条链路都走了一遍。每条链路都由不同组件执行，但共享 PostgreSQL 和 Redis 里的状态：

- 认证失败 → Core 返回 401，后续全部中断。
- 存储完成但扫描失败 → 镜像仍可拉取（除非项目开了阻止策略），漏洞报告缺失。
- 签名失败 → 镜像可用，但开启 DCT 的客户端会拒绝拉取。
- 复制失败 → 不影响本地，灾备站点缺这个镜像，Job Service 日志里能看到 pending 任务堆积。

排查时直接对号入座：认证、配置、策略看 Core 日志，存储转发看 Registry 日志，扫描看 Trivy Adapter 日志，复制和 GC 看 Job Service 日志。

## 6. 安装与配置

### 6.1 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|---------|
| CPU | 2 核 | 4 核以上 |
| 内存 | 4 GB | 8 GB 以上 |
| 磁盘 | 40 GB | 100 GB 以上 |
| Docker | 17.06+（在线安装） | 20.10+ |
| docker-compose | 1.18.0 以上 | 最新稳定版 |
| PostgreSQL | 内置容器 | 外部 13+ |
| Redis | 内置容器 | 外部 6+ |

Harbor 的离线安装包自带 PostgreSQL、Redis 容器，便于单节点起步；生产环境建议使用外部高可用数据库。

### 6.2 Docker Compose 部署

#### 6.2.1 下载安装包

到 GitHub Releases 下载离线安装包（以下为示例版本号，请以最新 Release 为准）：

```bash
wget https://github.com/goharbor/harbor/releases/download/v2.11.1/harbor-offline-installer-v2.11.1.tgz
tar xzvf harbor-offline-installer-v2.11.1.tgz
cd harbor
```

#### 6.2.2 配置 harbor.yml

编辑在 harbor 目录解压出的 `harbor.yml`：

```yaml
hostname: registry.example.com

http:
  port: 80

https:
  port: 443
  certificate: /your/certificate/path
  private_key: /your/private/key/path

harbor_admin_password: YourStrongAdminPassword

database:
  password: root123
  max_idle_conns: 100

data_volume: /data
```

`hostname` 必须是客户端访问 Harbor 的地址；`https.certificate` 指向证书，否则需要先执行 `prepare --with-notary` 生成自签名。

#### 6.2.3 启动 Harbor

```bash
sudo ./install.sh --with-trivy --with-notary
```

`--with-trivy` 启用漏洞扫描，`--with-notary` 启用镜像签名，`--with-chartmuseum` 启用 Helm Chart 支持（新版默认内置 OCI 仓库时可不加）。安装完成后访问 `https://registry.example.com`，用 `admin` 与 harbor.yml 里的密码登录。

### 6.3 Kubernetes Helm 部署

#### 6.3.1 添加 Harbor Helm 仓库

```bash
helm repo add harbor https://helm.goharbor.io
helm repo update
```

#### 6.3.2 Helm 配置 values.yaml

```yaml
externalURL: https://registry.example.com
harborAdminPassword: YourStrongAdminPassword
expose:
  type: ingress
  tls:
    enabled: true
persistence:
  enabled: true
  persistentVolumeClaim:
    registry:
      storageClass: standard
    database:
      storageClass: standard
core:
  replicas: 3
registery:
  replicas: 3
jobservice:
  replicas: 2
```

#### 6.3.3 部署命令

```bash
helm install my-harbor harbor/harbor -n harbor --create-namespace -f values.yaml
```

### 6.4 高可用部署

#### 6.4.1 多副本架构

生产环境让所有无状态组件多副本，把状态外置到可横向扩展的服务：

```
                  ┌───── LB / Ingress（L4/L7）─────┐
                  │                                │
        Core ×N            Registry ×N            Job Service ×N
           │                    │                     │
           └──────────┬─────────┴─────────┬───────────┘
                      │                   │
                PostgreSQL（主从 + Failover）    S3 / GCS（多区域副本）
                      │
                Redis（3 节点哨兵/集群）
```

核心要点：Core、Registry、Job Service 都是无状态，可通过多副本扩展；PostgreSQL、Redis、对象存储是状态所在，必须做高可用。

#### 6.4.2 推荐配置

| 组件 | 开发环境 | 生产环境 |
|------|----------|---------|
| Harbor 实例 | 1 | 3 以上 |
| PostgreSQL | 主从 | 主从 + Failover |
| Redis | 单机 | 3 节点哨兵/集群 |
| 存储 | 本地 NFS | S3/GCS 多副本 |
| 负载均衡 | - | L4/L7 |

## 7. 运维管理

### 7.1 用户管理

#### 7.1.1 创建用户与项目

登录 Portal 后，在 `Administration → Users` 创建用户，再到 `Projects → New Project` 创建项目并添加成员、分配角色。新建用户默认不属于任何项目，需要在项目成员列表里显式添加。

#### 7.1.2 LDAP 集成

在 `Administration → Configuration → Authentication` 选择 LDAP，配置：

- URL：`ldap://ldap.example.com:389`（或 `ldaps://`）
- Base DN：`dc=example,dc=com`
- User DN 与管理员 DN

LDAP 会把账号映射为本地用户，组可同步为项目角色，避免逐个维护。

### 7.2 垃圾回收

#### 7.2.1 GC 策略配置

在 Portal 的 `Administration → Garbage Collection` 创建 GC 任务，选择清理范围，可设置 Cron 定时触发。

#### 7.2.2 GC 执行策略

| 策略 | 说明 |
|------|------|
| 清理无引用 Blob | 不被任何 Manifest 引用的 Layer |
| 清理悬空 Manifest | 无 tag 的 Manifest |
| 清理已删除镜像 | 被标记删除但未回收的镜像 |

GC 是两阶段过程：先在 PostgreSQL 把 blob 标记为 `deleted`，再由 Registry 异步执行实际文件删除，二者不是原子操作。

### 7.3 审计日志

#### 7.3.1 可审计事件

| 事件类型 | 说明 |
|----------|------|
| 项目操作 | 创建、删除、修改项目配置 |
| 镜像操作 | 推送、拉取、删除镜像 |
| 用户操作 | 登录、登出、用户管理 |
| 策略操作 | 创建、修改、删除复制策略 |
| 扫描操作 | 触发扫描、查看报告 |

#### 7.3.2 日志保留

审计日志写入 PostgreSQL 的 auditlog 表，可按用户名、资源、操作时间过滤。日志保留时长建议根据合规要求配置，超期后可清理并归档，避免表无限增长。

### 7.4 故障排查

#### 7.4.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|---------|
| 镜像推送失败 500 | Registry 磁盘满 | 清理存储或扩容 |
| 扫描任务堆积 | Trivy 资源不足 | 增加 Trivy Adapter 资源 |
| 复制任务卡住 | 网络不通 | 检查端点配置 |
| 用户无法登录 | LDAP 超时 | 检查 LDAP 配置 |

#### 7.4.2 日志查看

Harbor 每个组件都是独立容器，直接看对应容器日志：

```bash
# Core / Registry / Job Service 各自的日志
docker logs harbor-core
docker logs harbor-registry
docker logs harbor-jobservice
docker logs harbor-trivy-adapter
```

配合 `--follow`、`grep 关键词` 定位具体任务。

## 8. 安全加固

### 8.1 网络安全

强制 HTTPS，禁用 HTTP 明文端口；用防火墙或安全组限制 80/443 只对必要网段开放；Portal 与 API 放到内网或 VPN 后面，不直接暴露公网。

### 8.2 证书管理

#### 8.2.1 自签名证书

生成后用 `prepare` 生成配置文件时引用：

```bash
openssl req -newkey rsa:4096 -nodes -sha256 \
  -keyout server.key -x509 -days 365 \
  -out server.crt -subj "/CN=registry.example.com"
```

将生成的 `server.crt` / `server.key` 路径填入 harbor.yml 的 `https.certificate` 与 `https.private_key`。客户端需把该证书加入信任链，否则 `docker login` 会报证书不受信任。

#### 8.2.2 Let's Encrypt 自动证书

用 certbot 签发现成证书后替换：

```bash
certbot certonly --standalone -d registry.example.com
sudo cp /etc/letsencrypt/live/registry.example.com/fullchain.pem server.crt
sudo cp /etc/letsencrypt/live/registry.example.com/privkey.pem server.key
```

再修改 harbor.yml 证书路径并重启相关容器。也可用 Kubernetes 的 cert-manager 在 Ingress 层自动签发与续期。

### 8.3 CVE 防护

#### 8.3.1 自动阻断策略

在项目配置里开启「按 CVE 级别阻止」后，含 Critical / High 漏洞的镜像会被标记为不可部署，拉取返回 403，从源头阻断带病镜像进入集群。

#### 8.3.2 安全加固清单

| 加固项 | 操作 |
|--------|------|
| TLS 加密 | 强制 HTTPS，禁用 HTTP |
| 密码策略 | 最小长度、复杂度、过期 |
| 会话超时 | 短会话 + 自动登出 |
| API 密钥 | 定期轮换 |
| 审计日志 | 开启并定期审查 |
| 漏洞扫描 | 强制扫描 + 自动更新 CVE 库 |

## 9. 最佳实践

### 9.1 镜像管理

用不可变 tag（如镜像摘要或构建号）代替 `latest`；在 CI 推送镜像后就触发扫描，把漏洞问题拦截在发布前；对多个环境（dev / staging / prod）用独立项目隔离。

### 9.2 权限管理

按最小权限原则给角色：只有负责人能在项目里推送或管理，普通成员默认 guest 只读。项目超过 10 个后接入 LDAP / OIDC，用组同步替代逐成员维护。

### 9.3 灾备方案

用复制策略把主站镜像同步到灾备站点，方向取决于网络出口。主站push到灾备，或灾备从主站 pull，二选一即可，避免双向同时写造成冲突。定期触发复制并检查 Job Service 是否有 pending 堆积。

## 10. 怎么选、怎么上线

### 10.1 什么时候选 Harbor

Harbor 不是「比云厂商注册表更好」的选项，而是适合以下场景：

- 镜像需要留在自有基础设施内（合规要求、数据主权）。
- 多集群、多数据中心之间需要策略驱动的镜像同步。
- 需要免费的漏洞扫描和内容签名，而云厂商这些功能在付费 tier。
- 团队需要项目级 RBAC 隔离，而不是单一 Namespace 的权限模型。

**不推荐 Harbor 的场景**：

- 你只有 1-2 个集群，团队规模小，镜像量不大——云厂商的托管注册表（ECR、ACR、GCR）运维成本更低。
- 你的组织还没有专人维护基础设施——Harbor 的高可用部署需要维护 PostgreSQL、Redis、存储三层，不是装完就能忘的。

### 10.2 上线顺序建议

先单节点跑通，再加安全与高可用，逐步铺开：

1. 单节点部署，验证 push / pull、项目与 RBAC。
2. 接入 LDAP / OIDC，统一账号来源。
3. 开启 TLS、扫描与内容签名。
4. 配置复制与 GC 定时任务。
5. 外部化 PostgreSQL / Redis，做多副本 + 存储迁移到对象存储。

每步先在 staging 验证，再切生产流量。

### 10.3 上线后关注什么

- **磁盘**：镜像 Layer 只增不减，GC 不是自动执行的。每周检查一次存储使用量，定期触发 GC。
- **CVE 数据库**：Trivy 的 CVE 库需要定期更新，否则新漏洞扫不出来。Trivy Adapter 默认每 12 小时拉取一次新数据库。
- **复制任务积压**：如果灾备站点网络不稳定，复制任务会堆积。Job Service 的队列长度是需要监控的关键指标。
- **证书过期**：自签名证书和 Let's Encrypt 证书都有有效期。证书过期会导致所有拉取与复制失败，且报错信息不直观。

### 10.4 官方资源

- 官网：https://goharbor.io
- GitHub：https://github.com/goharbor/harbor
- 文档：https://goharbor.io/docs/
- 在线 Demo：https://demo.goharbor.io
- Slack：#harbor、#harbor-dev

## 11. 常见问题

**Q1：Trivy 扫不出刚公开的 CVE，是 Harbor 的问题吗？**

不是。Trivy Adapter 默认每 12 小时从 GitHub 拉取一次 CVE 数据库。今天公开的高危漏洞，Harbor 要到下一次数据库更新才会扫到。遇到紧急 CVE 可以等待下次更新，或临时更新 Trivy 数据库容器：重启 `harbor-trivy-adapter` 触发重新拉取。

**Q2：docker push 成功但 docker pull 报 403 forbidden，从哪开始查？**

按这个顺序排查三层权限：

1. 用户角色：打开 Portal → 项目 → 成员列表，确认用户至少有 guest 角色。新建用户默认不属于任何项目，需要手动添加。
2. 阻止策略：Portal → 项目 → 策略，看镜像是否被扫描阻止策略标记。如果有 Critical CVE 且项目开了自动阻止，拉取会直接返回 403。
3. Content Trust：如果客户端开启了 Docker Content Trust，未签名或签名不匹配的镜像也会被拒绝，但报错信息通常不是 403。用 `docker trust inspect <image>` 确认签名状态。

**Q3：GC 跑完磁盘空间没释放，为什么？**

Harbor 的 GC 分两步：先在 PostgreSQL 里把 blob 标记为 `deleted`，再由 Registry 异步执行实际文件删除。这两个步骤不是原子操作。如果刚跑完 GC 就看磁盘，可能 Registry 还没删完。另外 S3 / GCS 存储的删除本身有最终一致性延迟。排查方法：去 Job Service 日志 grep 该任务 ID，看任务状态是否已是 `completed`。

**Q4：复制任务一直 pending，通常是什么原因？**

两种最常见的情况：

1. 目标注册表不可达：先从 Harbor 所在节点用 `openssl s_client -connect <目标地址>:443` 或 `curl -kv https://<目标地址>`测试连通性和证书。证书过期或自签名证书未加入信任链是最常见的根因。
2. Job Service worker 池被占满：去 Job Service 日志看是否有大量 `running` 状态的任务堆积。可以考虑增加 Job Service 的并发数（默认 10）。

**Q5：代理缓存和复制有什么区别？什么时候该用哪个？**

代理缓存的逻辑是「有人第一次拉的时候，Harbor 从上游缓存一份到本地」，适合加速 Docker Hub 等公共镜像的拉取速度。配置简单，不需要预先指定要缓存哪些镜像。

复制是「按策略主动同步指定镜像到目标站」，适合多数据中心灾备和镜像分发。需要明确指定仓库和 tag 匹配规则。

快速判断：只是想加速 `docker pull` 公共镜像 → 代理缓存。需要跨机房灾备或合规同步 → 复制。

## 12. 自测：你对 Harbor 理解了多少

以下 4 道题覆盖了 Harbor 的链路协作、权限模型、依赖关系和灾备决策。建议读完文章后独立回答，再对照文中对应章节验证。

**1. 链路判断**

Harbor 一次镜像推送会经过认证、存储、扫描、签名、复制五条链路。如果扫描链路因为 Trivy 容器 OOM 导致失败，其他四条链路会受影响吗？已经推送成功的镜像还能不能拉取？

<details>
<summary>参考答案（点击展开）</summary>

不会受影响。五条链路由不同组件独立执行，共享 PostgreSQL 和 Redis 里的状态但不共享执行流程。镜像推送成功后，即使扫描失败，镜像仍然可拉取，除非项目开启了阻止策略（阻止策略会拒绝后续拉取请求）。参见 5.4。

</details>

**2. 权限设计**

你的团队有 3 个业务线（订单组、支付组、用户组），每个组需要自己的镜像仓库且组员只能推送自己的镜像，但所有组都能拉取公共基础镜像（如 `base/nginx`）。你会怎么设计 Harbor 的项目结构和角色分配？

<details>
<summary>参考答案（点击展开）</summary>

- 创建 4 个项目：`order`、`payment`、`user`、`base`。
- 订单组成员在 `order` 项目里分配 developer 角色，在 `base` 项目里分配 guest 角色。
- 支付组和用户组同理：各自项目给 developer，`base` 项目给 guest。
- 如果项目数超过 10 个，考虑对接 LDAP 组实现自动化角色同步，避免手动维护。参见 3.3 和 7.1.2。

</details>

**3. 依赖关系**

Harbor 依赖 PostgreSQL 存元数据、Redis 存会话和缓存、S3 存镜像文件。如果 PostgreSQL 挂了，哪些操作会直接失败？docker pull 之前已经缓存过的镜像还能成功吗？

<details>
<summary>参考答案（点击展开）</summary>

PostgreSQL 挂了以后，所有需要查元数据的操作都会失败：docker login（校验凭据）、docker push（写 blob 记录和 manifest）、Portal 登录、RBAC 校验。docker pull 能走多远取决于具体的拉取场景：如果客户端已有认证 Token 且 Redis 中 session 未过期，Registry 可以直接从 S3 返回 blob 数据；但新的认证请求和 manifest 查询都需要查 PostgreSQL，会失败。参见 4.1 架构图里数据层（Data Layer）的三层依赖。

</details>

**4. 灾备决策**

你的 Harbor 部署在自建机房，需要在云上部署一个灾备实例。你会选择推送模式还是拉取模式？给出两个关键理由。

<details>
<summary>参考答案（点击展开）</summary>

两种模式都可以，选择取决于网络拓扑：

- **Push 模式**（自建 → 云）：自建机房的 Harbor 主动把镜像推送到云端。适合自建机房有稳定的出网线路、云端只作为被动灾备接收方的场景。优点是复制策略集中管理在主站。
- **Pull 模式**（云 → 自建）：云上 Harbor 主动从自建机房拉取。适合自建机房没有固定公网 IP、需要通过 VPN 或专线让云端主动发起连接的场景。

关键判断因素：谁有稳定可达的网络出口、防火墙规则放行哪个方向的连接。参见 3.4 和 9.3。

</details>

---

## 练习

### 练习 1：在本地虚拟机部署一套单节点 Harbor

1. 准备一台 4 核 8GB 的虚拟机（Ubuntu 20.04+）。
2. 按照第 6 章步骤，用 Docker Compose 完成 Harbor 安装。
3. 创建一个项目 `myproject`，配置一个开发者用户。
4. 从本地 `docker push` 一个测试镜像到 Harbor，再 `docker pull` 验证。

### 练习 2：配置跨数据中心的镜像复制

假设你在上海和北京两个机房各有一套 Harbor，完成：

1. 在上海 Harbor 上配置复制策略：Push 模式，目标为北京 Harbor。
2. 推送一个镜像到上海，观察复制任务状态。
3. 模拟北京机房网络中断，观察 Job Service 队列变化。
4. 恢复网络后，验证镜像是否自动同步。

### 练习 3：用 Harbor API 自动化镜像清理

写一个简单的 Python 脚本，完成：

1. 调用 Harbor API 列出所有项目下超过 30 天未拉取的镜像。
2. 生成清理计划（保留最近 3 个 tag）。
3. 输出为 CSV 报告，包含：项目名、仓库名、tag、上次拉取时间。

---

## 进阶路径

### 入门（第一次接触容器注册表）

- 理解 Docker 镜像的基本结构（Layer、Manifest、Tag）。
- 完成练习 1，在本地跑通一套单节点 Harbor。
- 阅读 Harbor 官方文档的 Quick Install 部分。

### 进阶（在生产环境运维 Harbor）

- 掌握 Harbor 高可用架构（第 6.4 节）：多副本 + 外部 PostgreSQL/Redis。
- 深入理解镜像安全链路：漏洞扫描（Trivy）+ 内容签名（Notary）+ 阻止策略。
- 参与一次 Harbor 版本升级，理解数据迁移和回滚步骤。

### 专业（为组织设计镜像管理战略）

- 对比 Harbor 与云厂商托管注册表（ECR、ACR、GCR）的总拥有成本（TCO）。
- 设计多区域镜像分发架构：就近推送 + 中心同步 + 边缘缓存。
- 深入理解 OCI 标准：不止 Docker 镜像，还能分发 Helm Chart、SBOM、扫描报告。

---

文档版本：v1.1 | 写作日期：2026-04-09 | 更新日期：2026-06-02