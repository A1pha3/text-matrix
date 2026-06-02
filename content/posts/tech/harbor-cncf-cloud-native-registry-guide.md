---
title: "Harbor：CNCF 云原生容器注册表的技术指南"
date: "2026-04-09T12:40:00+08:00"
slug: "harbor-cncf-cloud-native-registry-guide"
description: "Harbor 是由 CNCF 托管的开源云原生容器注册表，提供容器镜像和 Helm Chart 存储、签名、扫描、复制、权限管理等功能。本文深入解析 Harbor 的架构设计、核心组件、高可用部署、安全机制以及与 Kubernetes 的集成。"
draft: false
categories: ["技术笔记"]
tags: ["Harbor", "容器注册表", "CNCF", "Docker Registry", "Kubernetes", "云原生", "镜像签名", "漏洞扫描"]
---

# Harbor：CNCF 云原生容器注册表的技术指南

## §1 这篇文章会帮你做什么

Harbor 真正解决的不是「存镜像」—— Docker Hub 和云厂商的 ECR / ACR 都能存镜像。Harbor 解决的是：当你的组织需要自建一套镜像仓库，同时还要合规、要权限隔离、要跨数据中心同步、要镜像签名和漏洞扫描这条完整链路时，怎么把这些需求组装成一套可运维的系统。

这篇文章会从三个角度展开：

1. 结构层面：Harbor 的组件拆了什么、每层存储怎么配合，让你知道出问题时该看哪个容器日志。
2. 流转层面：一次镜像推送在 Harbor 里经历了什么——认证、存储、扫描、签名、复制，每一步的触发条件和失败后果。
3. 决策层面：什么场景下该用 Harbor 而不是云厂商的托管注册表，部署时副本数、存储选型、灾备策略怎么定。

默认读者已经用过 `docker push` / `docker pull`，但对自建注册表的技术选型还不确定。

**目录**

- [§2 项目背景与生态定位](#§2-项目背景与生态定位)
- [§3 核心功能详解](#§3-核心功能详解)
- [§4 系统架构深度解析](#§4-系统架构深度解析)
- [§5 一次镜像推送的完整流转](#§5-一次镜像推送的完整流转)
- [§6 安装与配置](#§6-安装与配置)
- [§7 运维管理](#§7-运维管理)
- [§8 安全加固](#§8-安全加固)
- [§9 最佳实践](#§9-最佳实践)
- [§10 怎么选、怎么上线](#§10-怎么选怎么上线)

## §2 项目背景与生态定位

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

**托管方**：CNCF（Cloud Native Computing Foundation，云原生计算基金会）

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
| 开源 | Apache-2.0 | 闭源 | 闭源 | 部分 |
| 本地部署 | 完全自控 | SaaS | 云服务 | 可私有 |
| Helm 支持 | 原生 | 有限 | 支持 | 支持 |
| 漏洞扫描 | 免费 | 付费 | 支持 | 支持 |
| 多租户 | 项目级 | 不支持 | 支持 | 支持 |
| 复制同步 | 策略驱动 | 不支持 | 跨账户 | 支持 |

## §3 核心功能详解

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
| CNAB | Cloud Native Application Bundle | 多容器应用分发 |

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

权限继承关系：

| 角色 | 拉取 | 推送 | 删除 | 管理成员 | 管理策略 |
|------|------|------|------|----------|---------|
| guest | 可以 | 不可以 | 不可以 | 不可以 | 不可以 |
| developer | 可以 | 可以 | 不可以 | 不可以 | 不可以 |
| maintainer | 可以 | 可以 | 可以 | 不可以 | 不可以 |
| projectAdmin | 可以 | 可以 | 可以 | 可以 | 可以 |
| sysAdmin | 可以 | 可以 | 可以 | 可以 | 可以 |

### 3.4 基于策略的复制

Harbor 的复制功能支持多种同步场景：

#### 3.4.1 复制模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| 拉取模式 | Harbor 从远程注册表拉取 | 中心-边缘架构 |
| 推送模式 | 本地 Harbor 推送到远程 | 灾备复制 |
| 双向模式 | 双向同步 | 多数据中心 |

#### 3.4.2 复制过滤器

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

Harbor 集成 Trivy 作为漏洞扫描器：

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

```yaml
# 示例：阻止严重漏洞镜像部署
pre条件：
- CVE 严重级别 ≥ Critical
- CVE 高危数量 > 0

执行动作：
- 阻止镜像拉取
- 发送 Webhook 通知
- 记录审计日志
```

### 3.6 内容签名与 Notary

Harbor 通过 Docker Notary 实现镜像签名：

#### 3.6.1 信任模型

```
┌─────────────────────────────────────────────────────────────┐
│                  Docker Content Trust 模型                  │
├─────────────────────────────────────────────────────────────┤
│  Root Key（根密钥）                                        │
│  └── Repository Key（仓库密钥）                            │
│       └── Tag Key（标签密钥）                               │
│            └── 镜像 Manifest                               │
└─────────────────────────────────────────────────────────────┘
```

#### 3.6.2 签名验证流程

1. **签名阶段**：
   - 开发者使用私钥对镜像 tag 进行签名
   - 签名信息随镜像一起存储在 Harbor 中

2. **验证阶段**：
   - Docker Client 请求 Harbor 时携带公钥
   - Harbor 返回签名信息
   - Docker Client 验证签名完整性

3. **部署策略**：
   - 可配置为「仅允许已签名镜像」
   - K8s Admission Controller 可集成验证

## §4 系统架构深度解析

### 4.1 整体架构

Harbor 采用微服务架构，核心组件如下：

```
┌─────────────────────────────────────────────────────────────────┐
│                         Harbor 架构                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Portal    │  │    API     │  │  Registry   │            │
│  │  (前端 UI)  │  │  (Go/Chi)  │  │  (Docker)   │            │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘            │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          │                                      │
│         ┌────────────────┴────────────────┐                    │
│         │            Core Services         │                    │
│         │  ┌────────┐ ┌────────┐ ┌──────┐  │                    │
│         │  │ Job    │ │  SC    │ │  GC   │  │                    │
│         │  │ Service│ │ Service│ │Service│  │                    │
│         │  └────────┘ └────────┘ └──────┘  │                    │
│         └────────────────┬────────────────┘                    │
│                          │                                      │
│         ┌────────────────┼────────────────┐                    │
│         │          Data Layer              │                    │
│         │  ┌─────────┐ ┌─────────────┐     │                    │
│         │  │PostgreSQL│ │ Redis      │     │                    │
│         │  │(元数据)  │ │(缓存/会话) │     │                    │
│         │  └─────────┘ └─────────────┘    │                    │
│         │  ┌─────────────┐                 │                    │
│         │  │  Storage    │                 │                    │
│         │  │(S3/GCS/Azure)│                │                    │
│         │  └─────────────┘                 │                    │
│         └──────────────────────────────────┘                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 核心组件职责

| 组件 | 技术栈 | 职责 |
|------|--------|------|
| Portal | Angular/TypeScript | Web 管理界面 |
| API | Go/Chi 框架 | RESTful API 服务 |
| Registry | Go/Docker Distribution | 镜像存储分发 |
| Job Service | Go | 异步任务（复制/扫描） |
| SC Service | Go | 签名服务（Notary） |
| GC Service | Go | 垃圾回收 |
| PostgreSQL | DB | 元数据存储 |
| Redis | Cache | 会话/缓存 |

## §5 一次镜像推送的完整流转

下面以「开发者推送一个带签名的镜像到 Harbor，并要求漏洞扫描」为例，把前面讲的组件串起来。

### 5.1 初始化状态

- Harbor 已部署，hostname 为 `harbor.example.com`
- 项目 `myproject` 已创建，配置了漏洞扫描策略：Critical 级别阻止部署
- 开发者本地已配置 Docker Content Trust

### 5.2 推送流程

**Step 1：认证**

```bash
docker login harbor.example.com
```

Docker Client 向 Harbor API 发送认证请求。API 检查凭据（本地数据库或 LDAP/OIDC），生成 JWT Token 返回。后续所有操作都携带此 Token。

**Step 2：推送镜像**

```bash
docker tag myapp:v1.2.3 harbor.example.com/myproject/myapp:v1.2.3
docker push harbor.example.com/myproject/myapp:v1.2.3
```

Registry 组件接收推送请求。镜像 Layer 按块写入存储后端（S3 / GCS / 本地文件系统）。每层写入完成后，Registry 向 PostgreSQL 写入一条 blob 记录。

**Step 3：触发扫描**

镜像 Manifest 写入成功后，Registry 通过内部事件通知 Job Service。Job Service 创建一个扫描任务，交给 Trivy 适配器。Trivy 逐层解压镜像、对比 CVE 数据库，生成漏洞报告写回 PostgreSQL。

如果扫描结果中有 Critical 级别漏洞，Harbor 会在该镜像上标记「不可部署」，并拒绝后续拉取请求（前提是项目已开启阻止策略）。

**Step 4：签名**

如果开发者启用了 Docker Content Trust：

```bash
export DOCKER_CONTENT_TRUST=1
docker push harbor.example.com/myproject/myapp:v1.2.3
```

SC Service（签名服务）接收 Notary 请求，将签名元数据存入 Notary 数据库。此后，任何拉取该镜像的客户端如果也开启了 Content Trust，Docker 会自动验证签名链。

**Step 5：复制（可选）**

如果项目配置了复制策略（例如推送到灾备站点），Job Service 在镜像推送成功后触发复制任务，将镜像同步到目标注册表。复制任务的状态和进度记录在 PostgreSQL 中，可通过 API 或 Portal 查看。

### 5.3 拉取流程

```bash
docker pull harbor.example.com/myproject/myapp:v1.2.3
```

1. Docker Client 携带 Token 向 Harbor API 发起拉取请求。
2. API 验证 Token，检查用户对 `myproject` 的权限（至少需要 guest）。
3. API 检查该镜像是否被阻止部署（扫描策略结果）。
4. 通过后，返回 Registry 的 blob 下载地址。
5. Docker Client 从 Registry 拉取各 Layer。

### 5.4 这个案例说明了什么

- Harbor 的认证、存储、扫描、签名、复制是**五条独立链路**，共享 PostgreSQL 和 Redis 作为状态存储，但各自由不同组件执行。
- 任何一步失败不会影响已完成的步骤——镜像推送成功后，即使扫描失败，镜像仍然可拉取（除非开启阻止策略）。
- 排查问题时，先确认是哪个组件卡住了：认证看 API 日志，存储看 Registry 日志，扫描看 Trivy 日志，复制看 Job Service 日志。

## §6 安装与配置

### 6.1 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|---------|
| CPU | 2 核 | 4 核以上 |
| 内存 | 4 GB | 8 GB 以上 |
| 磁盘 | 40 GB | 100 GB 以上 |
| Docker | 20.10.10-ce 以上 | 最新稳定版 |
| docker-compose | 1.18.0 以上 | 最新稳定版 |
| PostgreSQL | 13 以上 | 15 以上 |
| Redis | 6 以上 | 7 以上 |

### 6.2 Docker Compose 部署

#### 6.2.1 下载安装包

```bash
# 下载最新稳定版
wget https://github.com/goharbor/harbor/releases/download/v2.15.0/harbor-offline-installer-v2.15.0.tgz

# 解压
tar -xzf harbor-offline-installer-v2.15.0.tgz
cd harbor
```

#### 6.2.2 配置 harbor.yml

```yaml
# harbor.yml 关键配置

# 基本信息
hostname: harbor.example.com
http:
  port: 80
https:
  port: 443
  certificate: /path/to/cert.pem
  private_key: /path/to/key.pem

# 数据库配置
database:
  password: your_db_password
  max_idle_conns: 50
  max_open_conns: 100

# Redis 配置
redis:
  host: redis
  port: 6379
  password: your_redis_password
  database: 1

# 存储配置
storage:
  provider: s3
  s3:
    region: us-west-1
    bucket: harbor-registry
    access_key: your_access_key
    secret_key: your_secret_key

# 管理员密码
harbor_admin_password: YourAdminPassword123

# 禁止用户注册（仅允许 LDAP/OIDC）
harbor_ca_root: /path/to/ca.crt
```

#### 6.2.3 启动 Harbor

```bash
# 首次安装 - 加载镜像并启动
sudo ./install.sh

# 已有配置重新启动
docker-compose down
docker-compose up -d

# 查看状态
docker-compose ps
```

### 6.3 Kubernetes Helm 部署

#### 6.3.1 添加 Harbor Helm 仓库

```bash
# 添加 Helm 仓库
helm repo add harbor https://helm.goharbor.io
helm repo update

# 查看版本
helm search repo harbor
```

#### 6.3.2 Helm 配置 values.yaml

```yaml
# values.yaml 关键配置

expose:
  type: ingress
  tls:
    enabled: true
    certSource: auto
  ingress:
    className: nginx
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
    hosts:
      core: harbor.example.com
      notary: notary.harbor.example.com

persistence:
  resourcePolicy: keep
  persistentVolumeClaim:
    registry:
      storageClass: "gp3"
      size: 100Gi
    chartmuseum:
      storageClass: "gp3"
      size: 20Gi

database:
  internal:
    persistence:
      storageClass: "gp3"
      size: 10Gi

redis:
  internal:
    persistence:
      storageClass: "gp3"
      size: 2Gi

metrics:
  enabled: true
  serviceMonitor:
    enabled: true

notary:
  enabled: true

trivy:
  enabled: true
  # 漏洞扫描器配置
  resources:
    requests:
      cpu: 200m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 2Gi
```

#### 6.3.3 部署命令

```bash
# 创建命名空间
kubectl create namespace harbor

# 安装 Harbor
helm install harbor harbor/harbor \
  -n harbor \
  -f values.yaml \
  --timeout 10m

# 验证安装
kubectl get pods -n harbor
kubectl get ingress -n harbor
```

### 6.4 高可用部署

#### 6.4.1 多副本架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Harbor 高可用架构                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Harbor #1  │    │  Harbor #2  │    │  Harbor #3  │    │
│  │  (Primary)  │◄──►│ (Replica)   │◄──►│ (Replica)   │    │
│  └──────┬─────┘    └──────┬─────┘    └──────┬─────┘    │
│         │                 │                 │              │
│         └────────────────┼─────────────────┘              │
│                          │                                │
│         ┌────────────────┴────────────────┐                │
│         │         共享存储 (S3/GCS)        │                │
│         └────────────────┬────────────────┘                │
│                          │                                │
│         ┌────────────────┴────────────────┐                │
│         │         共享数据库 (PG 集群)     │                │
│         └────────────────┬────────────────┘                │
│                          │                                │
│         ┌────────────────┴────────────────┐                │
│         │           共享 Redis 集群        │                │
│         └────────────────┬────────────────┘                │
│                          │                                │
│  LB (Nginx/HAProxy) ─────┴─────────────────              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### 6.4.2 推荐配置

| 组件 | 开发环境 | 生产环境 |
|------|----------|---------|
| Harbor 实例 | 1 | 3 以上 |
| PostgreSQL | 主从 | 主从 + Failover |
| Redis | 单机 | 3 节点集群 |
| 存储 | 本地 NFS | S3/GCS 多副本 |
| 负载均衡 | - | L4/L7 |

## §7 运维管理

### 7.1 用户管理

#### 7.1.1 创建用户

```bash
# 通过 API 创建用户
curl -X POST "https://harbor.example.com/api/v2.0/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "username": "developer1",
    "email": "developer1@example.com",
    "password": "YourPassword123!",
    "realname": "Developer One"
  }'
```

#### 7.1.2 LDAP 集成

```yaml
# harbor.yml LDAP 配置
ldap:
  url: ldap://ldap.example.com:389
  search_dn: cn=admin,dc=example,dc=com
  search_password: ldap_admin_password
  base_dn: dc=example,dc=com
  filter: "(objectClass=person)"
  uid: uid
  scope: 2
  timeout: 5

# LDAP 组同步
ldap_group:
  base_dn: dc=example,dc=com
  filter: (objectClass=groupOfNames)
  name: cn
  gid: cn
```

### 7.2 垃圾回收

#### 7.2.1 GC 策略配置

```bash
# 通过 API 触发 GC
curl -X POST "https://harbor.example.com/api/v2.0/system/gc/schedule" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -d '{
    "schedule": {
      "type": "weekly",
      "weekday": 0,
      "offtime": 2
    },
    "delete_untagged": true,
    " gc_history": true
  }'
```

#### 7.2.2 GC 执行策略

| 策略 | 说明 |
|------|------|
| 清理无引用 Blob | 不被任何 Manifest 引用的 Layer |
| 清理悬空 Manifest | 无 tag 的 Manifest |
| 清理已删除镜像 | 被标记删除但未回收的镜像 |

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

```yaml
# 配置日志保留周期
log:
  level: info
  local:
    rotate_count: 50      # 保留文件数
    rotate_size: 200M     # 单文件大小
  access_log:
    rotate_count: 100
    rotate_size: 50M
```

### 7.4 故障排查

#### 7.4.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|---------|
| 镜像推送失败 500 | Registry 磁盘满 | 清理存储或扩容 |
| 扫描任务堆积 | Trivy 资源不足 | 增加 Trivy 资源 |
| 复制任务卡住 | 网络不通 | 检查端点配置 |
| 用户无法登录 | LDAP 超时 | 检查 LDAP 配置 |

#### 7.4.2 日志查看

```bash
# 查看 API 日志
docker logs harbor-core --tail 100 -f

# 查看 Registry 日志
docker logs harbor-registry --tail 100 -f

# 查看 Job Service 日志
docker logs harbor-jobservice --tail 100 -f

# 查看 Trivy 扫描日志
docker logs harbor-trivy-adapter --tail 100 -f
```

## §8 安全加固

### 8.1 网络安全

```yaml
# 网络隔离配置
network:
  # 限制 Harbor 只能内部访问
  internal:
    enabled: true
    # 仅允许以下 IP 访问
    allowed_external_ips:
      - 10.0.0.0/8
      - 172.16.0.0/12
```

### 8.2 证书管理

#### 8.2.1 自签名证书

```bash
# 生成自签名 CA
openssl req -x509 -newkey rsa:4096 \
  -keyout ca.key -out ca.crt \
  -days 365 -nodes \
  -subj "/CN=Harbor CA"

# 为 Harbor 生成证书
openssl req -newkey rsa:4096 \
  -keyout harbor.key -out harbor.csr \
  -subj "/CN=harbor.example.com"

# 使用 CA 签名
openssl x509 -req -in harbor.csr \
  -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out harbor.crt \
  -days 365
```

#### 8.2.2 Let's Encrypt 自动证书

```yaml
# cert-manager 配置
cert-manager.io/cluster-issuer: letsencrypt-prod

# Harbor Ingress 注解
annotations:
  cert-manager.io/cluster-issuer: letsencrypt-prod
  nginx.ingress.kubernetes.io/ssl-redirect: "true"
```

### 8.3 CVE 防护

#### 8.3.1 自动阻断策略

```yaml
# 配置阻止严重漏洞镜像
replication:
  policy:
    - name: block-critical-cve
      trigger:
        type: event_based
      filters:
        - type: cve
          value: "CVE-2024-*"
          severity: critical
      actions:
        - type: stop
          message: "Critical CVE detected"
```

#### 8.3.2 安全加固清单

| 加固项 | 操作 |
|--------|------|
| TLS 加密 | 强制 HTTPS，禁用 HTTP |
| 密码策略 | 最小长度、复杂度、过期 |
| 会话超时 | 短会话 + 自动登出 |
| API 密钥 | 定期轮换 |
| 审计日志 | 开启并定期审查 |
| 漏洞扫描 | 强制扫描 + 自动更新 CVE 库 |

## §9 最佳实践

### 9.1 镜像管理

```bash
# 1. 使用标准命名规范
# 项目/镜像名:tag
docker tag myapp:1.0.0 harbor.example.com/myproject/myapp:1.0.0

# 2. 镜像打标签策略
# latest 标签仅用于测试
docker push harbor.example.com/myproject/myapp:latest
# 生产使用具体版本
docker push harbor.example.com/myproject/myapp:v1.2.3

# 3. 定期清理过期镜像
# 设置保留策略：只保留最近 10 个版本
harbor gc --keep-last-n 10
```

### 9.2 权限管理

```
推荐：项目级权限控制
├── 项目 A：团队 A 成员（developer）
├── 项目 B：团队 B 成员（developer）
└── 项目 C：所有开发（guest）

避免：使用系统管理员账户日常操作
```

### 9.3 灾备方案

```yaml
# 主 Harbor 配置
harbor:
  replication:
    enabled: true
    # 复制到灾备站点
    destinations:
      dr-site:
        url: https://harbor-dr.example.com
        credential:
          access_key: ${DR_ACCESS_KEY}
          access_secret: ${DR_ACCESS_SECRET}
        # 触发条件
        trigger:
          type: manual
          # 或定时
          schedule: "0 2 * * *"  # 每天凌晨 2 点

# 灾备 Harbor 配置
harbor:
  # 开启只读模式（主站点恢复前）
  readonly: true
```

## §10 怎么选、怎么上线

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

```
阶段 1：单实例验证
├── Docker Compose 部署，本地存储
├── 配置 HTTPS + 自签名证书
├── 创建 1-2 个项目，验证推送/拉取
└── 周期：1-2 天

阶段 2：接入组织
├── 对接 LDAP/OIDC，统一认证
├── 按团队创建项目，分配 RBAC 角色
├── 开启 Trivy 扫描，配置阻止策略
└── 周期：1 周

阶段 3：生产化
├── 迁移到 Helm 部署，共享存储（S3）
├── 至少 3 副本，PostgreSQL 主从 + Redis 集群
├── 配置灾备复制策略
├── 接入 Prometheus 监控
└── 周期：1-2 周
```

### 10.3 上线后关注什么

- **磁盘**：镜像 Layer 只增不减，GC 不是自动执行的。每周检查一次存储使用量，定期触发 GC。
- **CVE 数据库**：Trivy 的 CVE 库需要定期更新，否则新漏洞扫不出来。Harbor 默认每天更新一次。
- **复制任务积压**：如果灾备站点网络不稳定，复制任务会堆积。Job Service 的队列长度是需要监控的关键指标。
- **证书过期**：自签名证书和 Let's Encrypt 证书都有有效期。证书过期会导致所有 `docker pull` / `docker push` 失败，且报错信息不直观。

### 10.4 官方资源

- 官网：[goharbor.io](https://goharbor.io)
- GitHub：[github.com/goharbor/harbor](https://github.com/goharbor/harbor)
- 文档：[goharbor.io/docs](https://goharbor.io/docs)
- 在线 Demo：[demo.goharbor.io](https://demo.goharbor.io)
- Slack：#harbor、#harbor-dev

---

文档版本：v1.1 | 写作日期：2026-04-09 | 更新日期：2026-06-02