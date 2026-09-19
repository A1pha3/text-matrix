---
title: "Immich：高性能自托管照片和视频管理解决方案完全指南"
date: "2026-04-06T21:30:00+08:00"
slug: "immich-self-hosted-photo-video-management-guide"
github_repo: "immich-app/immich"
source_key: "gh:immich-app/immich"
description: "全面介绍约 11.4 万 Stars（2026 年 9 月）的 Immich 自托管照片和视频管理方案，涵盖 Docker 部署、多端架构、人脸识别、CLIP 搜索、OIDC、API 集成等核心功能，以及开发指南和常见问题解决方案。"
draft: false
categories: ["技术笔记"]
tags: ["自托管", "Flutter", "NestJS"]
---

## 学习目标

读完本文你能回答下面几类问题：

- Immich 定位是什么，和 Google Photos、iCloud Photos 相比差异在哪里
- 它的技术栈由哪几个模块组成，各自承担什么职责
- 用 Docker Compose 部署一个可用实例需要哪些服务和参数
- 人脸识别、CLIP 语义搜索背后大致是什么原理，依赖哪些模型
- 部署后如何做备份、如何升级、踩到常见坑时按什么顺序排查
- 作为开发者想参与，项目结构长什么样、如何跑本地开发环境

---

## 1. 项目概述

### 1.1 是什么

Immich 是一个自托管的照片和视频管理方案，定位是 Google Photos 的开源替代。媒体文件存在你自己控制的服务器上，不走任何云服务商，数据归属完全由你决定。

它覆盖从移动端自动备份到 Web 浏览、人脸聚类、语义搜索、相册分享的完整链路，可运行在个人 NAS、VPS 或云主机上。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | 约 11.4 万（2026 年 9 月） |
| License | AGPLv3 |
| 发布节奏 | 高频发版，几乎每周都有新版本 |

项目由开源社区驱动维护。当前版本线为 v3（`.env` 里 `IMMICH_VERSION=v3`），具体版本号迭代很快，部署前以 [GitHub Releases](https://github.com/immich-app/immich/releases) 为准，不要写死某个旧版本号。

### 1.3 技术栈

前后端分离 + 多端客户端，核心服务用 Node.js / NestJS，媒体处理与向量检索依赖 PostgreSQL 扩展，智能功能由独立的机器学习容器承载。

### 1.4 与云相册对比

| 维度 | Immich | Google Photos / iCloud Photos |
|------|--------|-------------------------------|
| 数据位置 | 自己的服务器，文件与数据库都能自持备份 | 云厂商 |
| 人脸 / 语义搜索 | 本地模型推理，照片与向量不出机器 | 云端处理 |
| 多用户 | 自建用户体系、共享相册、外链分享 | 家庭共享方案 |
| 费用 | 软件免费，代价是自担硬件、带宽与运维 | 订阅或免费额度 |
| 开源 | AGPLv3，代码可审计 | 闭源 |

---

## 2. 核心功能详解

### 2.1 照片和视频管理

Web 端支持拖拽、批量上传，移动端侧重自动备份。上传后的媒体通过时间线、相册、地图、人物等多个入口浏览，大图库靠虚拟滚动保证流畅。

移动端备份默认只在 WiFi 下进行，打开 App 时和后台周期性补传，服务器按文件内容的校验和跳过已存在的文件。可配置项见第 5 节。

### 2.2 重复照片检测

上传环节按内容校验和精确去重，同一个文件不会被重复入库。已经入库的近似重复，由一个默认开启的机器学习作业找出来：在工具页的重复项面板里人工挑选保留哪张，"全部去重"建议会优先保留元数据更多、体积更大的那张；只保留一张时，相册、收藏、评分、标签等元数据会合并过去。

### 2.3 RAW 格式支持

| 格式 | 支持情况 |
|------|---------|
| Canon CR2 / CR3 | 支持 |
| Nikon NEF | 支持 |
| Sony ARW | 支持 |
| Adobe DNG | 支持 |
| Apple ProRAW | 支持 |
| Samsung RAW | 支持 |

### 2.4 元数据和地理信息

归档时会抽取 EXIF 元数据（相机型号、光圈、快门、ISO、拍摄时间），并保留 GPS 坐标。Web 端提供地图视图，可按地理位置浏览全部照片。大量历史照片没有坐标的话，可以通过 XMP sidecar 或修正元数据的方式补齐。

### 2.5 搜索功能

| 搜索类型 | 实现方式 |
|----------|---------|
| 元数据搜索 | 按相机、时间、地点、文件名、标签筛选 |
| 语义搜索 | CLIP 图像向量 + 文本向量相似度匹配 |
| 人脸搜索 | 人脸聚类后的身份属性 |
| 文字识别 | OCR 抽取照片中的文字供检索，截图内容可搜 |

语义搜索的例子：搜"海边日落"，匹配的是图像向量与文本向量的相似度，不需要手动打标签。

### 2.6 人脸识别和聚类

```text
1. InsightFace 模型检测图像中的人脸边界框
2. 同系列模型提取每张人脸的特征向量
3. 对特征向量做聚类，把同一人的照片归到一组
4. 手动为人物命名，支持合并/拆分聚类
```

检测与特征提取用的是 InsightFace 项目的 ONNX 模型（可选 antelopev2、buffalo_l 等，这类模型包内部是 SCRFD 检测加 ArcFace 识别的组合）。所有推理都发生在你自己的服务器上，照片与人脸向量不出机器。

---

## 3. 系统架构

### 3.1 整体架构

```text
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Mobile      │   Web        │    CLI       │  其他客户端   │
│  Flutter     │  SvelteKit   │  @immich/cli │   OpenAPI    │
└──────┬───────┴──────┬───────┴──────┬───────┴──────────────┘
       │             │              │
       └─────────────┴──────────────┘
                  REST API
                        ▼
┌─────────────────────────────────────────────┐
│              immich-server                   │
│  NestJS + Express + Kysely（六边形架构）      │
│  · 处理 REST API 请求                        │
│  · 后台任务：缩略图生成、元数据抽取、          │
│    视频转码、智能搜索、人脸识别、sidecar 等   │
└──────────────────┬────────────────────────────┘
                   │
   ┌───────────────┼───────────────┐
   ▼               ▼               ▼
┌─────────┐   ┌──────────┐   ┌──────────────────┐
│PostgreSQL│   │  Valkey  │   │ machine-learning │
│vectorchord│  │ 任务队列  │   │   ONNX 推理       │
└─────────┘   └──────────┘   └──────────────────┘
```

### 3.2 核心模块

| 模块 | 技术栈 | 职责 |
|------|--------|------|
| server | NestJS + TypeScript | API、后台任务、媒体处理 |
| web | SvelteKit + TypeScript + Tailwind CSS | Web 管理界面 |
| mobile | Flutter + Dart | iOS / Android 客户端 |
| machine-learning | Python（ONNX Runtime） | 人脸识别、CLIP、OCR |
| cli | npm 包 `@immich/cli` | 命令行批量上传等操作 |
| open-api | OpenAPI 3.0 | 客户端代码自动生成依据 |

### 3.3 数据存储

核心数据分两类存：

- **关系数据**：账户、相册关系、媒体元数据、任务状态，存 PostgreSQL。
- **向量数据**：CLIP 图像向量和人脸特征向量，靠 PostgreSQL 的向量扩展做相似度检索——早期用 pgvecto.rs，现在官方镜像内置 VectorChord。
- **媒体文件**：原图、视频、缩略图、转码产物按配置落在 `UPLOAD_LOCATION` 指向的目录。

### 3.4 为什么需要 Valkey

缩略图生成、视频转码、智能搜索这类耗时任务放在后台执行，由 Valkey（Redis 协议兼容的键值数据库）充当任务队列：server 把任务投递进去，后台任务消费执行，API 请求不会因为长耗时的媒体处理而阻塞。

---

## 4. 部署指南

### 4.1 Docker Compose 部署（推荐）

不要手工抄写 compose 内容，直接从最新 Release 拉取，避免本地用错版本：

```bash
mkdir ./immich-app && cd ./immich-app
wget -O docker-compose.yml \
  https://github.com/immich-app/immich/releases/latest/download/docker-compose.yml
wget -O .env \
  https://github.com/immich-app/immich/releases/latest/download/example.env
```

官方 compose 定义四个服务，结构大致如下。注意：官方文件里还带镜像 digest 固定和健康检查，且随版本演进，请以你下载的发布版为准，不要手抄本文片段：

```yaml
name: immich
services:
  immich-server:
    container_name: immich_server
    image: ghcr.io/immich-app/immich-server:${IMMICH_VERSION:-release}
    volumes:
      - ${UPLOAD_LOCATION}:/data   # 媒体文件存储位置
      - /etc/localtime:/etc/localtime:ro
    env_file: .env
    ports:
      - "2283:2283"
    depends_on:
      - redis
      - database
    restart: always

  immich-machine-learning:
    container_name: immich_machine_learning
    image: ghcr.io/immich-app/immich-machine-learning:${IMMICH_VERSION:-release}
    volumes:
      - model-cache:/cache         # 模型加载缓存
    env_file: .env
    restart: always

  redis:
    container_name: immich_redis
    image: valkey/valkey:9         # 兼作缓存的键值数据库
    restart: always

  database:
    container_name: immich_postgres
    image: ghcr.io/immich-app/postgres:14-vectorchord0.4.3-pgvectors0.2.0
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_USER: ${DB_USERNAME}
      POSTGRES_DB: ${DB_DATABASE_NAME}
      POSTGRES_INITDB_ARGS: '--data-checksums'
    volumes:
      - ${DB_DATA_LOCATION}:/var/lib/postgresql/data
    restart: always

volumes:
  model-cache:
```

### 4.2 启动与更新

```bash
# 进入部署目录启动
docker compose up -d

# 查看状态与日志
docker compose ps
docker compose logs -f
```

注意命令是 V2 的 `docker compose`，不是已废弃的 `docker-compose`。升级也是两步：按需改 `.env` 里的 `IMMICH_VERSION`，再 `docker compose pull && docker compose up -d`。跨大版本升级前先读一遍 Release Notes，确认有没有需要手工处理的变化。

### 4.3 关键环境变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `UPLOAD_LOCATION` | 媒体文件存储目录 | `./library` |
| `DB_DATA_LOCATION` | 数据库数据目录 | `./postgres` |
| `DB_PASSWORD` | PostgreSQL 连接密码 | 官方建议只用 `A-Za-z0-9` 字符 |
| `DB_USERNAME` / `DB_DATABASE_NAME` | 数据库用户与库名 | `postgres` / `immich` |
| `IMMICH_VERSION` | 固定版本线 | `v3` |
| `TZ` | 时区 | `Etc/UTC` |

两个硬性限制：数据库目录不能放在 NFS/SMB 网络挂载上；数据库所在文件系统不能是 NTFS 或 exFAT。

### 4.4 反向代理配置

以下配置把 443 端口的 HTTPS 流量代理到本机的 2283 端口，同时开启 WebSocket 支持：

```nginx
server {
    listen 443 ssl;
    server_name photos.example.com;

    ssl_certificate     /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:2283;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 大视频/RAW 上传需要
        client_max_body_size 0;

        # WebSocket：实时通知与任务进度推送
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

`client_max_body_size 0` 表示不限制上传体积，避免大图库上传被 Nginx 拒绝。

### 4.5 硬件基线

官方要求最低 2 核 CPU + 6 GB 内存，推荐 4 核 + 8 GB。Postgres 本身至少要占 2 GB 内存，用 Docker 资源限额时别算漏。只有 4 GB 内存的机器也能跑，但需要在设置里关闭机器学习功能。存储按原文件的 10%–20% 预留缩略图和转码视频的空间。

机器学习推理、缩略图生成、视频转码都吃 CPU。首次对一个大图库跑智能搜索作业，会连续执行几个小时甚至更久，这是 CPU 推理的正常现象，不等于启动失败。机器上若有 NVIDIA GPU（算力 5.2 以上），可以给 machine-learning 容器换 `-cuda` 镜像加速。

### 4.6 数据备份策略

官方明确提醒：Immich 不替你管理文件系统备份，也绝不会扫描 library 目录来反推数据。数据库里存着全部文件路径和元数据，丢了数据库，相册关系、人脸聚类、人物命名全部归零；只留数据库没有媒体文件，则没有可显示的原图。所以两类都要备，顺序是先库后文件（或者干脆先停掉 immich-server）：

```bash
# 1. 导出数据库（官方命令，默认用户/库名为 postgres/immich）
docker exec -t immich_postgres pg_dump --clean --if-exists \
  --dbname=immich --username=postgres | gzip > dump_$(date +%Y%m%d).sql.gz

# 2. 同步媒体目录（原图在 library，上传缓存与头像在 upload、profile）
rsync -av --delete ./library/ /path/to/backup-drive/library/

# 3. 保留配置
cp .env docker-compose.yml /path/to/backup-drive/
```

恢复推荐走 Web 端的 管理 → 维护（Administration → Maintenance），界面会先建一个回滚点再重置数据库。整体上按 3-2-1 原则（3 份副本、2 种介质、1 份异地）保留副本。

---

## 5. 移动端使用

### 5.1 iOS / Android 应用

| 功能 | 说明 |
|------|------|
| 自动备份 | 打开或恢复 App 时上传，另按周期在后台补传 |
| 选择性相册 | 勾选参与备份的本地相册，iOS 上可双击排除重叠相册 |
| 仅 WiFi 上传 | 默认开启，可在备份设置中改为移动网络 |
| 相册同步 | 服务器自动建同名相册镜像设备相册，单向同步 |
| 释放空间 | 清除已备份的本地文件，可设置保留收藏、相册等 |
| 平台限制 | Android 可设仅充电时后台同步，严格电池优化会杀后台任务；iOS 需开启 Background App Refresh |

移动端是备份入口和轻量浏览入口，重度的整理、用户管理、系统配置放在 Web 端完成。

### 5.2 相册同步的取舍

默认不会把设备上所有图片都传上来。进入 App 后需要逐相册勾选参与备份的范围，避开截图、缓存和其他没有长期保存价值的目录，能省下不少存储和流量。

---

## 6. 用户与分享

### 6.1 多用户与权限

| 角色 | 权限 |
|------|------|
| 管理员 | 用户管理、系统设置、清理后台任务 |
| 用户 | 创建和共享相册、搜索、下载 |
| 外部分享 | 通过链接范围受限地访问特定相册或资产 |

### 6.2 相册与分享

- **个人相册**：仅自己可见。
- **共享相册**：邀请站内其他用户协作添加照片。
- **外部分享**：生成公开链接，收件人无需账号即可查看。
- **合作伙伴**：添加对方为合作伙伴后，自动分享彼此新上传的媒体。

### 6.3 OIDC / SSO

Immich 通过标准 OIDC（OpenID Connect）接入外部身份提供商：浏览器先被重定向到 IdP 登录，认证完成后带着令牌回到 Immich 建立会话。配置集中在管理后台的 OAuth 设置，必填三项是 Issuer 地址、Client ID 和 Client Secret，令牌签名算法默认 RS256，scope 默认 `openid email profile`。官方文档给出的适配示例包括 Authentik、Authelia、Okta、Google、Keycloak，任何符合 OIDC 的 IdP 原则上都能接。

要注意的是 Immich 只支持 OIDC，没有原生 SAML。企业里 IdP 只出 SAML 的话，需要换用或前置一个支持 OIDC 的 IdP。

### 6.4 API 与集成

```bash
# 在 设置 → API Keys 创建一个 API Key，然后：
curl -H "x-api-key: YOUR_API_KEY" \
     https://photos.example.com/api/assets
```

所有客户端都通过同一套 OpenAPI 接口与服务器通信，第三方照样走这套规范写批量导入、自动打标签或对接工作流。底层批量备份可以结合官方 CLI（npm 包 `@immich/cli`）做脚本化上传。

---

## 7. 机器学习模块

### 7.1 ONNX 统一推理

machine-learning 容器里的模型都是 ONNX 格式，由 ONNX Runtime 加载执行，模型加载后常驻缓存复用。硬件加速通过换镜像 tag 启用：

| 加速器 | tag 后缀 |
|------|---------|
| CPU（默认） | 无 |
| NVIDIA GPU | `-cuda` |
| AMD GPU | `-rocm` |
| Intel 核显 | `-openvino` |
| ARM | `-armnn` |
| Rockchip NPU | `-rknn` |

### 7.2 人脸识别

检测与特征提取用 InsightFace 系列模型（管理后台可选 antelopev2、buffalo_l 等）。人脸聚类由 server 侧的后台任务完成，把同一人的照片归并，之后可以手动命名、合并、拆分。

### 7.3 CLIP 语义搜索

```text
1. 用 CLIP 模型把每张图编码成向量
2. 搜索时把查询文本编码成同空间向量
3. 计算文本向量与全部图像向量的余弦相似度
4. 取相似度最高的结果返回
```

默认模型为速度优化，管理后台可以换成 ViT-B-32、ViT-L-14 等档位；主要用中文等非英语搜索的建议选 nllb 系列多语言模型，混合语言场景可选 xlm、siglip2 系列。向量存在 PostgreSQL 的向量列里，靠向量扩展的 ANN 索引加速近邻检索。首次全量索引用 CPU 跑需要较长时间，之后新上传的照片在后台增量索引。

### 7.4 OCR

图片里的可读文字会被抽取出来供检索，"截图内容可搜"就是靠它。对已入库的照片，重跑一次智能搜索作业即可补齐 OCR 结果。

---

## 8. 开发指南

### 8.1 本地开发环境

开发环境用 mise 管理工具链（Node、pnpm 等版本由仓库配置锁定）：

```bash
# 1. 克隆仓库
git clone https://github.com/immich-app/immich.git
cd immich

# 2. 安装 mise 后初始化工具链
mise trust && mise install

# 3. 准备开发环境变量
cp docker/example.env docker/.env   # 按需修改 UPLOAD_LOCATION

# 4. 安装 JS 依赖
mise x -- pnpm i

# 5. 一条命令拉起全部服务（server、web、ML、数据库、Redis），带热更新
mise dev
# 浏览器打开 http://localhost:3000
```

移动端单独跑：

```bash
mise //mobile:install
cd mobile && flutter run
```

### 8.2 项目结构

```text
immich/
├── server/            # NestJS 后端（六边形架构）
├── web/               # SvelteKit Web UI
├── mobile/            # Flutter 移动端
├── machine-learning/  # Python ONNX 推理服务
├── cli/               # @immich/cli 命令行工具
├── open-api/          # OpenAPI 规范与生成的客户端
├── e2e/               # 端到端测试
└── docker/            # compose 文件与镜像构建配置
```

server 后端遵循六边形（Hexagonal）架构：核心业务逻辑与具体技术实现（数据库、文件系统）隔离在两层，视图通过 DTO 与外部交换，既方便测试也方便替换实现。

### 8.3 代码规范与常用任务

```bash
# 查看仓库定义的全部任务
mise tasks ls --all

# 常用任务示例
mise //server:lint
mise //web:start        # 单独跑 Web，可连远程后端
mise //mobile:install
```

机器学习侧的 Python 依赖用 uv 管理：

```bash
cd machine-learning
uv sync
```

---

## 9. 常见问题

### 9.1 数据库起不来，报向量扩展加载失败

多半是用了标准 `postgres` 镜像，里面没有 Immich 依赖的向量扩展。database 服务必须用官方 compose 里的 `ghcr.io/immich-app/postgres` 镜像（内置 VectorChord / pgvectors 扩展），不能换成普通 postgres，也不要自行改 tag 跳大版本。同时确认数据库目录没有落在 NTFS/exFAT 文件系统或 NFS/SMB 网络挂载上。

从 pgvecto.rs 时代的旧库迁移上来的数据，先按官方文档导出数据库再动数据卷，不要直接删卷重来。

### 9.2 上传失败

按存储权限 → 磁盘空间 → 容器日志的顺序排查：

```bash
# 存储目录权限
ls -la ./library

# 磁盘剩余空间
df -h

# 容器日志中的错误
docker compose logs immich-server | grep -i error
```

如果走了反向代理，还要确认 Nginx 的 `client_max_body_size` 是否放开了大文件上传。

### 9.3 人脸识别 / 语义搜索没有结果

智能功能依赖后台任务，先到管理后台的作业页看智能搜索作业是否在跑、是否阻塞，再检查 machine-learning 容器状态与日志：

```bash
docker compose logs immich-machine-learning
```

首次对大批照片建索引在 CPU 上要跑很久，等它增量完成即可，不要据此误判为故障。

### 9.4 内存占用高

machine-learning 在做推理和模型缓存时会吃内存。机器紧张时，可以给容器设内存上限：

```yaml
services:
  immich-machine-learning:
    mem_limit: 4g
```

同时按 4.5 的基线评估当前图库规模是否超出硬件能力。

### 9.5 升级后界面报错或任务异常

Immich 发版频繁，跨版本升级偶有 schema 变化。先确认 `.env` 里的 `IMMICH_VERSION` 与实际拉取的镜像一致，再 `docker compose pull && up -d`；仍异常时到 GitHub Issues 或 Discord 社区按版本号检索是否已知问题。

---

## 10. 自测清单

- 能说出 Immich 与 Google Photos 在数据载体上的本质差异。
- 能用 Docker Compose 部署并通过 2283 端口访问，说出 server 与 machine-learning 的分工。
- 知道为什么必须用带向量扩展的 PostgreSQL：语义搜索、人脸向量、多用户并发写入、任务状态都压在数据库上，普通 postgres 镜像或 SQLite 承担不了。
- 能解释人脸识别四步流程各自的作用，以及 CLIP 语义搜索如何把文本与图像统一到同一向量空间。
- 能列出备份时必须覆盖的内容（数据库、媒体目录、配置文件），以及每类对应什么故障场景。
- 能判断一个问题该查 server 日志还是 machine-learning 日志。

---

## 11. 进阶路径

**已经部署，想进一步用好：**

- **性能调优**：图库变大后关注智能搜索作业耗时与 ML 内存占用；有 NVIDIA GPU（算力 5.2+）时给 machine-learning 容器换 `-cuda` 镜像。
- **备份完善**：把 3-2-1 原则落到实际，数据库用 `pg_dump`，媒体文件用 `rsync`，再把副本推到异地存储。
- **多用户规划**：给家人用之前，先想清楚管理员、普通用户、外部分享三种权限的边界。
- **外部集成**：用 API Key 写批量导入、自动归档脚本，或把 Immich 接进既有自动化工作流。

**想参与项目：**

- 仓库地址：https://github.com/immich-app/immich
- 后端 NestJS、前端 SvelteKit、移动端 Flutter 任一熟悉即可，从 `good first issue` 入手。
- 机器学习侧是 Python + ONNX，熟悉人脸识别或 CLIP 模型可以参与模型选型与推理优化。

---

## 12. 总结

Immich 把 Google Photos 的核心体验搬到了自己的服务器上：移动端自动备份、时间线浏览、人脸聚类、语义搜索、相册与外链分享，代码开源可审计，所有推理都在本地完成。

代价同样清楚：一切运维归你。备份、升级、容量规划、故障排查，都不再有云厂商兜底，官方文档甚至专门提醒不要把它当媒体文件的唯一存储。它适合愿意花时间养服务的个人、家庭和小团队；如果只想要"存完就忘"，付费云服务仍然是更省心的选择。

**官方资源：**

- 官网：https://immich.app
- 文档：https://docs.immich.app
- 安装要求：https://docs.immich.app/install/requirements/
- 演示：https://demo.immich.app
- GitHub：https://github.com/immich-app/immich
- Releases：https://github.com/immich-app/immich/releases
