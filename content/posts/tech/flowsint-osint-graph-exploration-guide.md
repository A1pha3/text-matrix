---
title: "Flowsint：开源 OSINT 图探索工具完全指南"
slug: "flowsint-osint-graph-exploration-guide"
date: 2026-03-31T21:21:00+08:00
categories: ["技术笔记"]
tags: ["Flowsint", "OSINT", "开源情报", "图数据库", "Neo4j", "Enricher", "网络安全", "威胁情报", "侦察工具", "数据丰富"]
description: "深度解析 Flowsint (2.9k Stars)：开源 OSINT 图探索工具，30+ Enricher 覆盖域名/IP/社交媒体/加密货币等，模块化架构（flowsint-core/types/enrichers/api/app），Docker 一键部署，适合网络安全研究和威胁情报收集。"
---

# Flowsint：开源 OSINT 图探索工具完全指南

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 Flowsint 的核心定位与设计理念
- ✅ 掌握 Flowsint 的模块化架构设计
- ✅ 熟练部署 Flowsint（Docker / 开发环境）
- ✅ 理解 Enricher 系统的 30+ 数据源
- ✅ 使用 Flowsint 进行 OSINT 调查
- ✅ 扩展 Flowsint（添加新类型、新 Enricher）
- ✅ 遵守伦理规范，确保合法使用

---

## §2 项目概述

### 2.1 什么是 Flowsint？

**Flowsint**（[GitHub 仓库](https://github.com/reconurge/flowsint)）是一个开源的 **OSINT（图源情报）图探索工具**，专注于侦察和开源情报收集。它允许用户通过可视化图形界面探索实体之间的关系，并使用自动化 Enricher（数据丰富器）进行深度调查。

**官方描述**：

> Flowsint is an open-source OSINT graph exploration tool designed for ethical investigation, transparency, and verification.

**核心定位**：为网络安全研究人员、记者、执法机构和组织提供合法的威胁情报和数字风险分析工具。

### 2.2 核心数据

| 指标 | 数值 |
|------|------|
| **Stars** | 2,911 (2.9k) |
| **Forks** | 372 |
| **Watchers** | 27 |
| **贡献者** | 6 人 |
| **提交数** | 759 |
| **发布版本** | 10 个 |
| **最新版本** | v1.2.7 (2026-03-15) |
| **分支数** | 5 |
| **许可证** | Apache-2.0 |

### 2.3 技术栈

| 类别 | 技术 | 占比 |
|------|------|------|
| **前端** | TypeScript | 53.7% |
| **后端** | Python | 43.8% |
| **样式** | CSS | 1.2% |
| **脚本** | JavaScript | 0.6% |
| **配置** | Makefile | 0.3% |
| **图查询** | Cypher | 0.2% |

### 2.4 核心特性

| 特性 | 说明 |
|------|------|
| **图可视化** | 探索实体关系的可视化图形界面 |
| **30+ Enricher** | 自动化数据丰富器，覆盖 10+ 数据类型 |
| **隐私优先** | 所有数据存储在本地，不上传云端 |
| **模块化架构** | 高度解耦的微服务设计 |
| **高性能** | 即使处理数千节点也不卡顿 |
| **快速部署** | Docker 一键部署 |

### 2.5 适用场景

| 场景 | 描述 |
|------|------|
| **网络安全研究** | 威胁情报收集与分析 |
| **记者调查** | 深度调查报道的事实核查 |
| **执法取证** | 欺诈调查与数字取证 |
| **企业安全** | 内部威胁情报与数字风险分析 |
| **漏洞赏金** | 目标侦察与信息收集 |

---

## §3 系统架构

### 3.1 模块架构总览

Flowsint 采用**高度模块化**的微服务架构，将项目拆分为 5 个独立模块：

```
flowsint-app (前端)
      ↓
flowsint-api (API 服务)
      ↓
flowsint-core (核心引擎)
      ↓
flowsint-enrichers (数据丰富器)
      ↓
flowsint-types (类型定义)
```

### 3.2 核心模块详解

#### 3.2.1 flowsint-core（核心模块）

**职责**：提供所有其他模块使用的核心工具和基类

**包含内容**：
- 数据库连接（PostgreSQL, Neo4j）
- 认证与授权
- 日志与事件处理
- 配置管理
- Enricher 和工具的基类
- 工具函数

#### 3.2.2 flowsint-types（类型模块）

**职责**：定义所有数据类型的 Pydantic 模型

**包含类型**：
- **网络类**：Domain, IP, ASN, CIDR
- **人物类**：Individual, Organization, Email, Phone
- **网络资源**：Website, Social profiles, Credentials
- **加密货币**：Crypto wallets, Transactions, NFTs
- **其他**：更多类型...

#### 3.2.3 flowsint-enrichers（丰富器模块）

**职责**：处理数据的 Enricher 模块和扫描逻辑

**包含 Enricher**：
- Domain enrichers（子域名、WHOIS、解析）
- IP enrichers（地理定位、ASN 查询）
- 社交媒体 enrichers（Maigret, Sherlock）
- 邮箱 enrichers（泄露检查、Gravatar）
- 加密货币 enrichers（交易、NFT）
- 以及更多...

#### 3.2.4 flowsint-api（API 模块）

**职责**：FastAPI 服务器，提供 REST API 端点

**包含内容**：
- REST API 端点
- 认证与用户管理
- 图数据库集成
- 实时事件流

#### 3.2.5 flowsint-app（前端模块）

**职责**：现代化的前端应用

**包含内容**：
- 现代化、用户友好的界面
- 高性能图形渲染（数千节点不卡顿）

### 3.3 架构优势

| 优势 | 说明 |
|------|------|
| **高内聚低耦合** | 每个模块职责单一 |
| **独立开发** | 团队可并行开发不同模块 |
| **独立测试** | 每个模块有独立的测试套件 |
| **独立部署** | 可根据需要选择部署哪些模块 |
| **易于扩展** | 新类型和 Enricher 可独立添加 |

---

## §4 Enricher 系统详解

### 4.1 概述

Flowsint 的 **Enricher 系统**是其核心能力，通过自动化数据丰富器将原始数据转换为可操作的威胁情报。

### 4.2 Domain Enrichers（域名丰富器）

| Enricher | 描述 |
|----------|------|
| **Reverse DNS Resolution** | 查找指向某 IP 的所有域名 |
| **DNS Resolution** | 将域名解析为 IP 地址 |
| **Subdomain Discovery** | 枚举子域名 |
| **WHOIS Lookup** | 获取域名注册信息 |
| **Domain to Website** | 将域名转换为网站实体 |
| **Domain to Root Domain** | 提取根域名 |
| **Domain to ASN** | 查找域名关联的 ASN |
| **Domain History** | 获取历史域名数据 |

### 4.3 IP Enrichers（IP 丰富器）

| Enricher | 描述 |
|----------|------|
| **IP Information** | 获取地理定位和网络详情 |
| **IP to ASN** | 查找 IP 地址的 ASN |

### 4.4 ASN Enrichers（ASN 丰富器）

| Enricher | 描述 |
|----------|------|
| **ASN to CIDRs** | 获取 ASN 关联的 IP 范围 |

### 4.5 CIDR Enrichers（CIDR 丰富器）

| Enricher | 描述 |
|----------|------|
| **CIDR to IPs** | 枚举 IP 范围内的所有 IP |

### 4.6 Social Media Enrichers（社交媒体丰富器）

| Enricher | 描述 |
|----------|------|
| **Maigret** | 在多个社交平台搜索用户名 |

### 4.7 Organization Enrichers（组织丰富器）

| Enricher | 描述 |
|----------|------|
| **Organization to ASN** | 查找组织拥有的 ASN |
| **Organization Information** | 获取公司详细信息 |
| **Organization to Domains** | 查找组织拥有的域名 |

### 4.8 Cryptocurrency Enrichers（加密货币丰富器）

| Enricher | 描述 |
|----------|------|
| **Wallet to Transactions** | 获取交易历史 |
| **Wallet to NFTs** | 查找钱包拥有的 NFT |

### 4.9 Website Enrichers（网站丰富器）

| Enricher | 描述 |
|----------|------|
| **Website Crawler** | 爬取并映射网站结构 |
| **Website to Links** | 提取所有链接 |
| **Website to Domain** | 从 URL 提取域名 |
| **Website to Webtrackers** | 识别追踪脚本 |
| **Website to Text** | 提取文本内容 |

### 4.10 Email Enrichers（邮箱丰富器）

| Enricher | 描述 |
|----------|------|
| **Email to Gravatar** | 查找 Gravatar 头像 |
| **Email to Breaches** | 在数据泄露数据库中检查 |
| **Email to Domains** | 查找关联域名 |

### 4.11 Phone Enrichers（电话丰富器）

| Enricher | 描述 |
|----------|------|
| **Phone to Breaches** | 在数据泄露中检查电话号码 |

### 4.12 Individual Enrichers（个人丰富器）

| Enricher | 描述 |
|----------|------|
| **Individual to Organization** | 查找组织隶属关系 |
| **Individual to Domains** | 查找个人关联的域名 |

### 4.13 Integration Enrichers（集成丰富器）

| Enricher | 描述 |
|----------|------|
| **N8n Connector** | 连接到 N8n 工作流 |

---

## §5 安装与部署

### 5.1 前置要求

| 要求 | 说明 |
|------|------|
| **Docker** | 容器化部署 |
| **Make** | 构建工具 |

### 5.2 生产环境部署（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/reconurge/flowsint.git
cd flowsint

# 2. 进入项目目录
cd flowsint

# 3. 运行安装命令
make prod
```

部署完成后，访问 **http://localhost:5173/register** 注册账号。

**✅ 重要提示**：OSINT 调查需要高度隐私保护。所有数据都存储在你的机器上，不会上传到云端。

### 5.3 开发环境部署

```bash
# 1. 克隆仓库
git clone https://github.com/reconurge/flowsint.git
cd flowsint

# 2. 进入项目目录
cd flowsint

# 3. 安装依赖
make dev
```

开发环境访问：**http://localhost:5173**

### 5.4 Docker Compose 配置

Flowsint 使用 Docker Compose 管理多容器部署：

| 文件 | 用途 |
|------|------|
| **docker-compose.yml** | 默认配置 |
| **docker-compose.dev.yml** | 开发环境 |
| **docker-compose.prod.yml** | 生产环境 |

---

## §6 使用指南

### 6.1 注册与认证

1. 访问 **http://localhost:5173/register**
2. 创建账号（无默认凭证）
3. 登录系统

### 6.2 创建调查

1. 点击 "New Investigation"
2. 输入调查名称和描述
3. 开始添加实体

### 6.3 添加实体

Flowsint 支持多种实体类型：

| 类型 | 示例 |
|------|------|
| **Domain** | example.com |
| **IP** | 192.168.1.1 |
| **ASN** | AS15169 |
| **CIDR** | 192.168.0.0/24 |
| **Email** | user@example.com |
| **Phone** | +1234567890 |
| **Organization** | Google Inc. |
| **Individual** | John Doe |
| **Website** | https://example.com |

### 6.4 运行 Enricher

1. 选择一个实体
2. 点击 "Enrich" 按钮
3. 选择要运行的 Enricher
4. 查看结果

### 6.5 图探索

- **拖拽**：移动节点
- **缩放**：查看不同粒度
- **点击**：查看实体详情
- **连接线**：查看关系

---

## §7 开发扩展

### 7.1 开发工作流

#### 7.1.1 添加新类型

新类型添加到 **flowsint-types** 模块：

```bash
# 1. 进入类型模块
cd flowsint-types

# 2. 在 Pydantic 模型中定义新类型
from pydantic import BaseModel

class NewEntityType(BaseModel):
    field1: str
    field2: int
```

#### 7.1.2 添加新 Enricher

新 Enricher 添加到 **flowsint-enrichers** 模块：

```bash
# 1. 进入 Enricher 模块
cd flowsint-enrichers

# 2. 创建 Enricher 类
from flowsint_core.base import BaseEnricher

class NewEnricher(BaseEnricher):
    name = "new_enricher"
    entity_types = ["Domain", "IP"]

    async def enrich(self, entity):
        # 实现 Enricher 逻辑
        pass
```

#### 7.1.3 添加新 API 端点

新 API 端点添加到 **flowsint-api** 模块：

```bash
# 1. 进入 API 模块
cd flowsint-api

# 2. 定义新路由
from fastapi import APIRouter

router = APIRouter()

@router.get("/new-endpoint")
async def new_endpoint():
    return {"message": "Hello"}
```

#### 7.1.4 添加新工具函数

新工具函数添加到 **flowsint-core** 模块：

```bash
# 1. 进入核心模块
cd flowsint-core

# 2. 实现工具函数
def new_utility(param: str) -> str:
    return param.upper()
```

### 7.2 测试

每个模块有独立的测试套件：

```bash
# 测试核心模块
cd flowsint-core
poetry run pytest

# 测试类型模块
cd ../flowsint-types
poetry run pytest

# 测试 Enricher 模块
cd ../flowsint-enrichers
poetry run pytest

# 测试 API 模块
cd ../flowsint-api
poetry run pytest
```

### 7.3 贡献指南

| 要求 | 说明 |
|------|------|
| **模块化结构** | 遵循现有模块结构 |
| **Poetry 管理** | 使用 Poetry 进行依赖管理 |
| **测试覆盖** | 为新功能编写测试 |
| **文档更新** | 必要时更新文档 |

---

## §8 伦理与法律说明

### 8.1 设计初衷

Flowsint 是为以下场景创建的：

| 适用场景 | 说明 |
|----------|------|
| **网络安全研究人员** | 威胁情报收集 |
| **记者** | 调查报道的事实核查 |
| **执法人员** | 欺诈调查与取证 |
| **组织安全团队** | 内部威胁情报 |

### 8.2 禁止用途

⚠️ **Flowsint 严格禁止以下用途**：

| 禁止用途 | 说明 |
|----------|------|
| **未经授权的入侵** | 禁止非法入侵系统 |
| ** surveillance** | 禁止未经授权的监视 |
| **人肉搜索** | 禁止侵犯隐私 |
| **doxxing** | 禁止公开他人隐私信息 |
| **政治操纵** | 禁止虚假信息和舆论操纵 |
| **隐私侵犯** | 禁止违反隐私法规 |

### 8.3 伦理原则

使用 Flowsint 前，请阅读 **ETHICS.md** 了解详细的伦理使用指南。

任何滥用行为都违反项目伦理原则，会被追究法律责任。

---

## §9 项目结构

### 9.1 目录结构

```
flowsint/
├── .github/workflows/     # GitHub Actions
├── .husky/              # Git hooks
├── flowsint-api/         # FastAPI 服务器
├── flowsint-app/         # 前端应用
├── flowsint-core/        # 核心模块
├── flowsint-enrichers/   # Enricher 模块
├── flowsint-types/       # 类型定义
├── neo4j-migrations/      # Neo4j 迁移
├── scripts/              # 脚本
├── docker-compose.yml     # Docker 配置
├── Makefile             # 构建工具
└── pyproject.toml       # Python 配置
```

### 9.2 配置文件

| 文件 | 用途 |
|------|------|
| **.env.example** | 环境变量示例 |
| **poetry.toml** | Poetry 配置 |
| **commitlint.config.js** | 提交规范 |
| **.versionrc.json** | 版本控制配置 |

---

## §10 总结

### 10.1 核心优势

| 优势 | 说明 |
|------|------|
| **开源免费** | Apache-2.0 许可证 |
| **隐私优先** | 数据全部本地存储 |
| **30+ Enricher** | 覆盖 10+ 数据类型 |
| **图可视化** | 直观探索实体关系 |
| **模块化** | 易于扩展和维护 |
| **高性能** | 数千节点不卡顿 |
| **快速部署** | Docker 一键部署 |

### 10.2 适用对象

| 对象 | 使用场景 |
|------|----------|
| **安全研究人员** | 威胁情报收集 |
| **OSINT 调查员** | 信息收集与验证 |
| **记者** | 调查报道 |
| **执法机构** | 数字取证 |
| **企业安全** | 风险分析 |

### 10.3 项目信息

| 项目 | 信息 |
|------|------|
| **Stars** | 2.9k |
| **Forks** | 372 |
| **版本** | v1.2.7 |
| **许可证** | Apache-2.0 |

### 10.4 相关链接

| 资源 | 链接 |
|------|------|
| **GitHub** | https://github.com/reconurge/flowsint |
| **官网** | https://flowsint.io |
| **Buy Me a Coffee** | https://www.buymeacoffee.com/dextmorgn |
| **Ko-fi** | https://ko-fi.com/P5O1W3GPJ |

---

## §11 附录：术语表

| 术语 | 说明 |
|------|------|
| **OSINT** | Open Source Intelligence，开源情报 |
| **Enricher** | 数据丰富器，自动收集实体相关信息 |
| **Graph** | 图数据库，存储实体和关系 |
| **Neo4j** | 流行的图数据库 |
| **ASN** | Autonomous System Number，自治系统号 |
| **CIDR** | Classless Inter-Domain Routing，无类别域间路由 |
| **WHOIS** | 域名注册信息查询协议 |
| **Maigret** | 社交媒体用户名搜索工具 |

---

*文档版本 1.0 | 撰写日期：2026-03-31 | 基于 flowsint v1.2.7 (2.9k Stars) | 请遵守 ETHICS.md 伦理规范*