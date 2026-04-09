---
title: "Harbor：CNCF云原生容器注册表的完整技术指南"
date: 2026-04-09T12:40:00+08:00
slug: "harbor-cncf-cloud-native-registry-guide"
description: "Harbor是由CNCF托管的开源云原生容器注册表，提供容器镜像和Helm Chart存储、签名、扫描、复制、权限管理等功能。本文深入解析Harbor的架构设计、核心组件、高可用部署、安全机制以及与Kubernetes的集成。"
draft: false
categories: ["技术笔记"]
tags: ["Harbor", "容器注册表", "CNCF", "Docker Registry", "Kubernetes", "云原生", "镜像签名", "漏洞扫描"]
---

# Harbor： CNC F云原生容器注册表的完整技术指南

## §1 学习目标

通过本文，你将掌握：

- Harbor在云原生生态系统中的定位与核心价值
- Harbor的完整架构设计与核心组件
- 容器镜像的存储、签名、扫描全流程
- 基于策略的复制机制与多注册表同步
- RBAC权限管理与OIDC单点登录
- Kubernetes环境下的Helm Chart管理
- 高可用部署架构与性能优化
- 安全加固与漏洞防护措施
- 运维管理与故障排查

## §2 项目背景与生态定位

### 2.1 云原生存储的需求

在云原生时代，容器镜像的存储与管理面临五大挑战：

| 挑战 | 具体表现 | Harbor解决方案 |
|------|----------|---------------|
| **分发效率** | 跨集群/多环境镜像传输慢 | 近源存储、复制策略 |
| **安全合规** | 镜像漏洞、签名伪造 | 漏洞扫描、内容签名 |
| **权限控制** | 不同团队/项目访问隔离 | RBAC + 项目级权限 |
| **多格式支持** | Docker镜像 + Helm Chart | OCI标准兼容 |
| **审计追溯** | 谁在什么时间做了什么 | 完整操作日志 |

### 2.2 Harbor的定位

**Harbor是什么？**

> Harbor is an open source trusted cloud native registry project that stores, signs, and scans content.

**官方定义**：Harbor是一个开源的可信云原生注册表项目，用于存储、签名和扫描容器镜像及Helm Chart。

**托管方**：CNCF（Cloud Native Computing Foundation，云原生计算基金会）

**核心价值主张**：

```
┌─────────────────────────────────────────────────────────────┐
│                      Harbor 核心价值                       │
├─────────────────────────────────────────────────────────────┤
│  ✅ OCI兼容：Docker Image + Helm Chart + OCI Artifact      │
│  ✅ 安全可信：内容签名 + 漏洞扫描 + 权限控制               │
│  ✅ 高可用：多主复制 + 故障转移 + 水平扩展               │
│  ✅ 易集成：RESTful API + Webhook + Kubernetes Operator   │
└─────────────────────────────────────────────────────────┘
```

### 2.3 竞品对比

| 维度 | Harbor | Docker Hub | AWS ECR |阿里云ACR |
|------|--------|-----------|---------|-----------|
| **开源** | ✅ Apache-2.0 | ❌ 闭源 | ❌ 闭源 | ⚠️ 部分 |
| **本地部署** | ✅ 完全自控 | ❌ SaaS | ❌ 云服务 | ✅ 可私有 |
| **Helm支持** | ✅ 原生 | ⚠️ 有限 | ✅ | ✅ |
| **漏洞扫描** | ✅ 免费 | ⚠️ 付费 | ✅ | ✅ |
| **多租户** | ✅ 项目级 | ❌ | ✅ | ✅ |
| **复制同步** | ✅ 策略驱动 | ❌ | ⚠️ 跨账户 | ✅ |

## §3 核心功能详解

### 3.1 功能全景图

```
┌─────────────────────────────────────────────────────────────────┐
│                         Harbor 功能矩阵                          │
├────────────────┬────────────────┬────────────────┬───────────────┤
│   存储分发      │     安全      │     管理      │    集成     │
├────────────────┼────────────────┼────────────────┼───────────────┤
│ 容器镜像存储    │ 漏洞扫描      │ 多项目管理    │ Kubernetes   │
│ Helm Chart     │ 内容签名      │ RBAC权限      │ Helm/OCI    │
│ OCI Artifact   │ Notary信任    │ LDAP/AD集成   │ RESTful API  │
│ 代理缓存       │ 图像删除GC   │ 审计日志      │ Webhook     │
│ 多注册表复制   │ OIDC单点登录  │ 用户组管理    │ Harbor API   │
└────────────────┴────────────────┴────────────────┴───────────────┘
```

### 3.2 云原生注册表

Harbor作为云原生注册表，核心支持以下产物类型：

| 类型 | 说明 | 典型用途 |
|------|------|----------|
| **Docker镜像** | OCI Image Manifest格式 | 容器化应用分发 |
| **Helm Chart** | Kubernetes包管理 | 应用模板分发 |
| **OCI Artifact** | 通用OCI产物 | 任意二进制分发 |
| **CNAB** | Cloud Native Application Bundle | 多容器应用分发 |

**支持的Helm版本**：
- Helm 2 / Helm 3
- Chartmuseum兼容

### 3.3 基于角色的访问控制（RBAC）

Harbor采用项目级权限模型：

```
┌─────────────────────────────────────────────────────────────┐
│                    Harbor 权限模型                          │
├─────────────────────────────────────────────────────────────┤
│  系统级：                                                  │
│  ├── sysAdmin（系统管理员）：管理所有项目、用户、系统配置   │
│  └── anonymous（匿名用户）：只读公共项目                      │
│                                                              │
│  项目级：                                                   │
│  ├── projectAdmin（项目管理员）：管理项目成员、策略          │
│  ├── developer（开发者）：推送/拉取镜像                       │
│  ├── guest（访客）：仅拉取公共/授权镜像                     │
│  └── maintainer（维护者）：高级开发者权限                   │
└─────────────────────────────────────────────────────────────┘
```

**权限继承关系**：

| 角色 | 拉取 | 推送 | 删除 | 管理成员 | 管理策略 |
|------|------|------|------|----------|---------|
| guest | ✅ | ❌ | ❌ | ❌ | ❌ |
| developer | ✅ | ✅ | ❌ | ❌ | ❌ |
| maintainer | ✅ | ✅ | ✅ | ❌ | ❌ |
| projectAdmin | ✅ | ✅ | ✅ | ✅ | ✅ |
| sysAdmin | ✅ | ✅ | ✅ | ✅ | ✅ |

### 3.4 基于策略的复制

Harbor的复制功能支持多种同步场景：

#### 3.4.1 复制模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| **拉取模式** | Harbor从远程注册表拉取 | 中心-边缘架构 |
| **推送模式** | 本地Harbor推送到远程 | 灾备复制 |
| **双向模式** | 双向同步 | 多数据中心 |

#### 3.4.2 复制过滤器

```
复制策略配置：
├── 仓库过滤器
│   ├── 仓库名称模式：匹配哪些仓库（如：project/*）
│   └── 排除模式：排除哪些仓库（如：project/internal）
├── 标签过滤器
│   ├── 标签模式：匹配哪些标签（如：release-*）
│   └── 排除模式：排除哪些标签（如：latest）
└── 标签过滤器
    ├── 标签模式：匹配哪些标签（如：release-*）
    └── 排除模式：排除哪些标签（如：latest）
```

#### 3.4.3 复制触发器

| 触发方式 | 说明 |
|----------|------|
| **手动** | 管理员手动触发 |
| **定时** | Cron表达式定时同步 |
| **事件驱动** | 镜像推送时自动触发 |

### 3.5 漏洞扫描

Harbor集成开源漏洞扫描器Trivy：

#### 3.5.1 扫描流程

```
镜像推送 → 触发扫描 → 提取Layer → 对比CVE数据库 → 生成报告
                              ↓
                      严重程度分级
                              ↓
                    高危 → 阻止部署策略
                    中危 → 警告
                    低危 → 允许
```

#### 3.5.2 CVE严重级别

| 级别 | 阈值配置 | 默认动作 |
|------|----------|----------|
| **Critical（严重）** | ≥9.0 | 阻止部署 |
| **High（高危）** | ≥7.0 | 警告 |
| **Medium（中危）** | ≥4.0 | 允许 |
| **Low（低危）** | <4.0 | 允许 |

#### 3.5.3 阻止策略配置

```yaml
# 示例：阻止严重漏洞镜像部署
pre条件：
- CVE严重级别 ≥ Critical
- CVE高危数量 > 0

执行动作：
- 阻止镜像拉取
- 发送Webhook通知
- 记录审计日志
```

### 3.6 内容签名与Notary

Harbor通过Docker Notary实现镜像签名：

#### 3.6.1 信任模型

```
┌─────────────────────────────────────────────────────────────┐
│                  Docker Content Trust 模型                  │
├─────────────────────────────────────────────────────────────┤
│  Root Key（根密钥）                                       │
│  └── Repository Key（仓库密钥）                           │
│       └── Tag Key（标签密钥）                              │
│            └── 镜像Manifest                               │
└─────────────────────────────────────────────────────────┘
```

#### 3.6.2 签名验证流程

1. **签名阶段**：
   - 开发者使用私钥对镜像tag进行签名
   - 签名信息随镜像一起存储在Harbor中

2. **验证阶段**：
   - Docker Client请求Harbor时携带公钥
   - Harbor返回签名信息
   - Docker Client验证签名完整性

3. **部署策略**：
   - 可配置为"仅允许已签名镜像"
   - K8s Admission Controller可集成验证

## §4 系统架构深度解析

### 4.1 整体架构

Harbor采用微服务架构，主要组件包括：

```
┌─────────────────────────────────────────────────────────────────┐
│                         Harbor 架构                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Portal    │  │    API     │  │  Registry   │          │
│  │  (前端UI)   │  │  (Go/Chi) │  │  (Docker)  │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         │                │                │                    │
│         └────────────────┼────────────────┘                    │
│                          │                                     │
│         ┌────────────────┴────────────────┐                   │
│         │              Core Services         │                   │
│         │  ┌────────┐ ┌────────┐ ┌──────┐  │                   │
│         │  │ Job    │ │  SC    │ │  GC   │  │                   │
│         │  │ Service│ │ Service│ │Service│  │                   │
│         │  └────────┘ └────────┘ └──────┘  │                   │
│         └────────────────┬────────────────┘                   │
│                          │                                     │
│         ┌────────────────┼────────────────┐                   │
│         │        Data Layer                │                   │
│         │  ┌─────────┐ ┌─────────────┐   │                   │
│         │  │ PostgreSQL│ │ Redis      │   │                   │
│         │  │(元数据)  │ │(缓存/会话) │   │                   │
│         │  └─────────┘ └─────────────┘   │                   │
│         │  ┌─────────────┐              │                   │
│         │  │  Storage    │              │                   │
│         │  │(S3/GCS/Azure)│             │                   │
│         │  └─────────────┘              │                   │
│         └────────────────────────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 核心组件详解

| 组件 | 技术栈 | 职责 |
|------|--------|------|
| **Portal** | Angular/TypeScript | Web管理界面 |
| **API** | Go/Chi框架 | RESTful API服务 |
| **Registry** | Go/Docker Distribution | 镜像存储分发 |
| **Job Service** | Go | 异步任务（复制/扫描） |
| **SC Service** | Go | 签名服务（Notary） |
| **GC Service** | Go | 垃圾回收 |
| **PostgreSQL** | DB | 元数据存储 |
| **Redis** | Cache | 会话/缓存 |

### 4.3 数据流

```
用户请求流程：

1. 认证流程
   Docker Client → Harbor API → LDAP/OIDC验证 → JWT Token

2. 镜像推送
   Docker Client → Registry → Storage (S3/GCS)
                        ↓
                   Job Service（触发扫描）
                        ↓
                   PostgreSQL（记录元数据）

3. 镜像拉取
   Docker Client → Harbor API（验证Token）
                        ↓
                   Registry → Storage
```

## §5 安装与配置

### 5.1 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|---------|
| **CPU** | 2核 | 4核+ |
| **内存** | 4GB | 8GB+ |
| **磁盘** | 40GB | 100GB+ |
| **Docker** | 20.10.10-ce+ | 最新稳定版 |
| **docker-compose** | 1.18.0+ | 最新稳定版 |
| **PostgreSQL** | 13+ | 15+ |
| **Redis** | 6+ | 7+ |

### 5.2 Docker Compose部署

#### 5.2.1 下载安装包

```bash
# 下载最新稳定版
wget https://github.com/goharbor/harbor/releases/download/v2.15.0/harbor-offline-installer-v2.15.0.tgz

# 解压
tar -xzf harbor-offline-installer-v2.15.0.tgz
cd harbor
```

#### 5.2.2 配置harbor.yml

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

# Redis配置
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

# 禁止用户注册（仅允许LDAP/OIDC）
harbor_ca_root: /path/to/ca.crt
```

#### 5.2.3 启动Harbor

```bash
# 首次安装 - 加载镜像并启动
sudo ./install.sh

# 已有配置重新启动
docker-compose down
docker-compose up -d

# 查看状态
docker-compose ps
```

### 5.3 Kubernetes Helm部署

#### 5.3.1 添加Harbor Helm仓库

```bash
# 添加Helm仓库
helm repo add harbor https://helm.goharbor.io
helm repo update

# 查看版本
helm search repo harbor
```

#### 5.3.2 Helm配置values.yaml

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
  #漏洞扫描器配置
  resources:
    requests:
      cpu: 200m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 2Gi
```

#### 5.3.3 部署命令

```bash
# 创建命名空间
kubectl create namespace harbor

# 安装Harbor
helm install harbor harbor/harbor \
  -n harbor \
  -f values.yaml \
  --timeout 10m

# 验证安装
kubectl get pods -n harbor
kubectl get ingress -n harbor
```

### 5.4 高可用部署

#### 5.4.1 多副本架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Harbor 高可用架构                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │  Harbor #1 │    │  Harbor #2 │    │  Harbor #3 │    │
│  │  (Primary) │◄──►│ (Replica) │◄──►│ (Replica) │    │
│  └──────┬─────┘    └──────┬─────┘    └──────┬─────┘    │
│         │                 │                 │              │
│         └────────────────┼─────────────────┘              │
│                          │                               │
│         ┌────────────────┴────────────────┐                │
│         │         共享存储 (S3/GCS)        │                │
│         └────────────────┬────────────────┘                │
│                          │                               │
│         ┌────────────────┴────────────────┐                │
│         │         共享数据库 (PG集群)     │                │
│         └────────────────┬────────────────┘                │
│                          │                               │
│         ┌────────────────┴────────────────┐                │
│         │           共享Redis集群         │                │
│         └────────────────┬────────────────┘                │
│                          │                               │
│  LB (Nginx/HAProxy) ─────┴─────────────────              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### 5.4.2 推荐配置

| 组件 | 开发环境 | 生产环境 |
|------|----------|---------|
| Harbor实例 | 1 | 3+ |
| PostgreSQL | 主从 | 主从+Failover |
| Redis | 单机 | 3节点集群 |
| 存储 | 本地NFS | S3/GCS多副本 |
| 负载均衡 | - | L4/L7 |

## §6 运维管理

### 6.1 用户管理

#### 6.1.1 创建用户

```bash
# 通过API创建用户
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

#### 6.1.2 LDAP集成

```yaml
# harbor.yml LDAP配置
ldap:
  url: ldap://ldap.example.com:389
  search_dn: cn=admin,dc=example,dc=com
  search_password: ldap_admin_password
  base_dn: dc=example,dc=com
  filter: "(objectClass=person)"
  uid: uid
  scope: 2
  timeout: 5

# LDAP组同步
ldap_group:
  base_dn: dc=example,dc=com
  filter: (objectClass=groupOfNames)
  name: cn
  gid: cn
```

### 6.2 垃圾回收

#### 6.2.1 GC策略配置

```bash
# 通过API触发GC
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

#### 6.2.2 GC执行策略

| 策略 | 说明 |
|------|------|
| **清理无引用Blob** | 不被任何Manifest引用的Layer |
| **清理悬空Manifest** | 无tag的Manifest |
| **清理已删除镜像** | 被标记删除但未回收的镜像 |

### 6.3 审计日志

#### 6.3.1 可审计事件

| 事件类型 | 说明 |
|----------|------|
| **项目操作** | 创建、删除、修改项目配置 |
| **镜像操作** | 推送、拉取、删除镜像 |
| **用户操作** | 登录、登出、用户管理 |
| **策略操作** | 创建、修改、删除复制策略 |
| **扫描操作** | 触发扫描、查看报告 |

#### 6.3.2 日志保留

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

### 6.4 故障排查

#### 6.4.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|---------|
| 镜像推送失败500 | Registry磁盘满 | 清理存储或扩容 |
| 扫描任务堆积 | Trivy资源不足 | 增加Trivy资源 |
| 复制任务卡住 | 网络不通 | 检查端点配置 |
| 用户无法登录 | LDAP超时 | 检查LDAP配置 |

#### 6.4.2 日志查看

```bash
# 查看API日志
docker logs harbor-core --tail 100 -f

# 查看Registry日志
docker logs harbor-registry --tail 100 -f

# 查看Job Service日志
docker logs harbor-jobservice --tail 100 -f

# 查看Trivy扫描日志
docker logs harbor-trivy-adapter --tail 100 -f
```

## §7 安全加固

### 7.1 网络安全

```yaml
# 网络隔离配置
network:
  # 限制Harbor只能内部访问
  internal:
    enabled: true
    # 仅允许以下IP访问
    allowed_exernal_ips:
      - 10.0.0.0/8
      - 172.16.0.0/12
```

### 7.2 证书管理

#### 7.2.1 自签名证书

```bash
# 生成自签名CA
openssl req -x509 -newkey rsa:4096 \
  -keyout ca.key -out ca.crt \
  -days 365 -nodes \
  -subj "/CN=Harbor CA"

# 为Harbor生成证书
openssl req -newkey rsa:4096 \
  -keyout harbor.key -out harbor.csr \
  -subj "/CN=harbor.example.com"

# 使用CA签名
openssl x509 -req -in harbor.csr \
  -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out harbor.crt \
  -days 365
```

#### 7.2.2 Let's Encrypt自动证书

```yaml
# cert-manager配置
cert-manager.io/cluster-issuer: letsencrypt-prod

# Harbor Ingress注解
annotations:
  cert-manager.io/cluster-issuer: letsencrypt-prod
  nginx.ingress.kubernetes.io/ssl-redirect: "true"
```

### 7.3 CVE防护

#### 7.3.1 自动阻断策略

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

#### 7.3.2 安全加固清单

| 加固项 | 操作 |
|--------|------|
| **TLS加密** | 强制HTTPS，禁用HTTP |
| **密码策略** | 最小长度、复杂度、过期 |
| **会话超时** | 短会话+自动登出 |
| **API密钥** | 定期轮换 |
| **审计日志** | 开启并定期审查 |
| **漏洞扫描** | 强制扫描+自动更新CVE库 |

## §8 最佳实践

### 8.1 镜像管理最佳实践

```bash
# 1. 使用标准命名规范
# 项目/镜像名:tag
docker tag myapp:1.0.0 harbor.example.com/myproject/myapp:1.0.0

# 2. 镜像打标签策略
# latest标签仅用于测试
docker push harbor.example.com/myproject/myapp:latest
# 生产使用具体版本
docker push harbor.example.com/myproject/myapp:v1.2.3

# 3. 定期清理过期镜像
# 设置保留策略：只保留最近10个版本
harbor gc --keep-last-n 10
```

### 8.2 权限管理最佳实践

```
✅ 推荐：项目级权限控制
├── 项目A：团队A成员（developer）
├── 项目B：团队B成员（developer）
└── 项目C：所有开发（guest）

❌ 避免：使用系统管理员账户日常操作
```

### 8.3 灾备方案

```yaml
# 主Harbor配置
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
          schedule: "0 2 * * *"  # 每天凌晨2点

#灾备Harbor配置
harbor:
  # 开启只读模式（主站点恢复前）
  readonly: true
```

## §9 总结

Harbor作为CNCF的旗舰级云原生容器注册表，提供了：

- ✅ **全面的OCI标准支持**：Docker镜像、Helm Chart、任意OCI产物
- ✅ **企业级安全**：漏洞扫描、内容签名、RBAC、OIDC
- ✅ **灵活的复制机制**：策略驱动、多注册表同步、故障转移
- ✅ **成熟的运维体系**：高可用部署、垃圾回收、审计日志
- ✅ **深度Kubernetes集成**：Helm Chart、Operator、CSI存储

**官方资源**：

- 官网：goharbor.io
- GitHub：github.com/goharbor/harbor
- 文档：goharbor.io/docs
- 在线Demo：demo.goharbor.io
- Slack：#harbor, #harbor-dev

---

🦞 文档版本：v1.0 | 写作日期：2026-04-09
