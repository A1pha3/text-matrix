---
title: "Immich：高性能自托管照片和视频管理解决方案完全指南"
date: "2026-04-06T21:30:00+08:00"
slug: "immich-self-hosted-photo-video-management-guide"
github_repo: "immich-app/immich"
description: "全面介绍接近 9.9 万 Stars 的 Immich 自托管照片和视频管理方案，涵盖 Docker 部署、多端架构、人脸识别、CLIP 搜索、OIDC、API 集成等核心功能，以及开发指南和常见问题解决方案。"
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
| GitHub Stars | 约 9.9 万 |
| License | AGPLv3 |
| 发布节奏 | 每周发版，社区驱动 |

项目无公司实体、无 VC 投资，完全由社区维护。当前版本线为 v3（官方 Docker 镜像 tag 为 `v3`），具体版本号迭代很快，部署前以 [GitHub Releases](https://github.com/immich-app/immich/releases) 为准，不要在文档里写死某个旧版本号。

### 1.3 技术栈

前后端分离 + 多端客户端，核心服务用 Node.js / NestJS，媒体处理与向量检索依赖 PostgreSQL 扩展，智能功能用独立机器学习容器承载。

### 1.4 与竞品对比

| 特性 | Immich | Google Photos | iCloud Photos |
|------|--------|---------------|---------------|
| 自托管 | 数据在自己服务器 | 云端 | 云端 |
| 隐私 | 本地存储，可控 | 依赖云厂商 | 依赖云厂商 |
| 人脸识别 | 本地推理 | 云 | 云 |
| 自动备份 | 移动端可配 | 有 | 有 |
| 多用户 | 内置管理员/用户体系 | 家庭共享 | 家庭共享 |
| RAW / Live Photo | 支持 | 受限/需付费 | 支持 |
| 开源 | AGPLv3 | 否 | 否 |

---

## 2. 核心功能详解

### 2.1 照片和视频管理

Web 端支持拖拽、批量上传，移动端则侧重自动备份。上传后的媒体通过时间线、相册、地图、人物等多个入口浏览，大图库靠虚拟滚动保证流畅。

移动端备份是可以配置的策略，而不是简单的"全量同步"：

| 配置项 | 说明 |
|------|------|
| 参与备份的相册 | 可只选相机胶卷，排除截图、缓存目录 |
| 仅 WiFi 上传 | 避免消耗移动流量 |
| 备份质量 | 可选择压缩或保留原始文件 |
| 后台持续同步 | 打开 App 或触发时自动补传 |

### 2.2 重复照片检测

Immich 通过文件大小、校验和、EXIF 元数据以及由 CLIP 生成的感知向量综合判断重复，避免同一张照片被重复入库。

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

归档时会抽取 EXIF 元数据（相机型号、光圈、快门、ISO、拍摄时间），并保留 GPS 坐标。Web 端提供地图视图，可按地理位置浏览全部照片。如果有大量历史照片没有坐标，可以通过写入 XMP sidecar 或修正元数据的方式补齐。

### 2.5 搜索功能

| 搜索类型 | 实现方式 |
|----------|---------|
| 元数据搜索 | 按相机、时间、地点、型号筛选 |
| 语义搜索 | CLIP 图像向量 + 文本向量相似度匹配 |
| 人脸搜索 | 人脸聚类后的身份属性 |
| 文字识别 | OCR 抽取照片中的文字供检索 |

语义搜索示例：搜索"海边日落的照片"，系统理解语义后返回匹配结果，不需要靠手动打标签。

### 2.6 人脸识别和聚类

```text
1. SCRFD 检测图像中的人脸边界框
2. INSIGHTFACE（ArcFace）提取每张人脸的特征向量
3. 对特征向量做聚类，把同一人的照片归到一组
4. 手动为人物命名，支持合并/拆分聚类
```

人脸识别的结果只在本地局域网内推理，照片与人脸数据不出服务器。

---

## 3. 系统架构

### 3.1 整体架构

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  Mobile      │   Web        │    CLI       │  其他客户端   │
│  Flutter     │  SvelteKit   │   npm 包     │   OpenAPI    │
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
│PostgreSQL│   │  Redis   │   │ machine-learning │
│ vectorchord│  │ 任务队列  │   │  ONNX 推理        │
└─────────┘   └──────────┘   └──────────────────┘
```

### 3.2 核心模块

| 模块 | 技术栈 | 职责 |
|------|--------|------|
| server | NestJS + TypeScript | API、后台任务、媒体处理 |
| web | SvelteKit + TypeScript + Tailwind CSS | Web 管理界面 |
| mobile | Flutter + Dart | iOS / Android 客户端 |
| machine-learning | Python（ONNX Runtime） | 人脸识别、CLIP、OCR |
| cli | npm 包 | 命令行批量上传等操作 |
| open-api | OpenAPI 3.0 | 客户端代码自动生成依据 |

### 3.3 数据存储

核心数据分两类存：

- **关系数据**：账户、相册关系、媒体元数据、任务状态，存 PostgreSQL。
- **向量数据**：CLIP 图像向量和人脸特征向量，利用 PostgreSQL 的向量扩展（早期用 pgvecto.rs，现多采用社区维护的 vectorchord 镜像）做相似度检索。
- **媒体文件**：原图、视频、缩略图、转码产物按配置落在 `UPLOAD_LOCATION` 指向的目录。

### 3.4 为什么用 Redis

缩略图生成、视频转码、智能搜索这类耗时任务放在后台执行，由 Redis 作为任务队列衔接。server 把任务投递到队列，worker 消费执行，这样 API 请求不会因为长耗时的媒体处理而阻塞。

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

官方 compose 定义的服务大致如下（以发布版为准）：

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
      - model-cache:/cache          # 模型加载缓存
    env_file: .env
    restart: always

  redis:
    image: valkey/valkey:9          # 兼作缓存的键值数据库
    restart: always

  database:
    container_name: immich_postgres
    image: ghcr.io/immich-app/postgres:14-vectorchord... # 带向量扩展的 PG
    env_file: .env
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

注意命令是 V2 的 `docker compose`，不是已废弃的 `docker-compose`。升级也是两步：先改 `.env` 里的 `IMMICH_VERSION`（或用 `latest` 镜像重新拉取），再 `docker compose pull && docker compose up -d`。

### 4.3 关键环境变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `UPLOAD_LOCATION` | 媒体文件存储目录 | `./library` |
| `DB_DATA_LOCATION` | 数据库数据目录 | `./postgres` |
| `DB_PASSWORD` | PostgreSQL 连接密码 | 随机字符串 |
| `IMMICH_VERSION` | 固定版本或为 `release` | `release` |
| `TZ` | 时区 | `Etc/UTC` |

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

官方给出的最低配置为 2 核 CPU + 6 GB 内存，推荐 4 核 + 8 GB。机器学习推理、缩略图生成、视频转码都会额外吃 CPU 与内存。首次对一个大图库做智能索引，会持续数小时甚至更久，这是 CPU 推理的正常现象，不等于启动失败。图库超过 5 万张建议起步 16 GB 内存。机器上若另有 NVIDIA GPU，可以为 machine-learning 容器追加 `-cuda` 镜像 tag 加速推理。

### 4.6 数据备份策略

Immich 官方并不建议把它当媒体唯一存储，重要资料应按 3-2-1 原则（3 份副本、2 种介质、1 份异地）保留在多个位置。备份要覆盖三类数据：

```bash
# 1. 导出数据库（关系数据与元数据）
docker compose exec database pg_dump -U <DB_USERNAME> \
  postgres > backup_$(date +%Y%m%d).sql

# 2. 同步媒体文件目录
rsync -av --delete ./library/ /path/to/backup-drive/library/

# 3. 保存配置文件
cp .env /path/to/backup-drive/
```

数据库备份和媒体目录备份解决的是不同故障场景，缺一不可：只有媒体文件没有数据库，元数据、相册关系、人脸聚类都会丢失；只有数据库没有媒体，则没有可展示的原图。

---

## 5. 移动端使用

### 5.1 iOS / Android 应用

| 功能 | 说明 |
|------|------|
| 自动备份 | 打开 App 或按策略后台同步 |
| 选择性相册 | 只参与备份指定的本地相册 |
| 仅 WiFi 上传 | 可在设置中配置 |
| 电池优化跳过 | 低电量自动暂停备份 |
| RAW / Live Photo | 按原始格式备份 |
| 后台数据集缓存 | 离线浏览已同步内容 |

移动端主要是备份入口和轻量浏览入口，重度的整理、用户管理、系统配置放在 Web 端完成。

### 5.2 相册同步的取舍

默认不会把设备上所有图片都传上来。进入 App 后需要逐相册勾选参与备份的范围，避开截图、缓存和其他没有长期保存价值的目录，这能显著减少存储占用和备份流量。

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
- **合作伙伴**：与指定账号双向自动分享新上传的媒体。

### 6.3 OIDC / SSO

Immich 支持以 **OIDC** 方式接入身份提供商，前端先把浏览器重定向到 IdP，完成认证后再回到 Immich 建立会话并映射用户。常见可对接的提供商包括 Google、Microsoft Entra ID、Keycloak、Authentik、Zitadel、Dex 等；企业场景可经支持 SAML 的 IdP（如 Entra ID）间接实现单点登录。配置项集中在管理后台的外部认证设置里，需要填写签发者地址、客户端 ID 和密钥。

接口上它是通用 OIDC，而不是对某一家厂商的单独适配，因此具体支持范围取决于 IdP 是否符合 OIDC 协议。

### 6.4 API 与集成

```bash
# 在 设置 → API Keys 创建一个 API Key，然后：
curl -H "x-api-key: YOUR_API_KEY" \
     https://photos.example.com/api/assets
```

所有客户端都通过 OpenAPI 接口与服务器通信，第三方便可以走同一套规范写批量导入、自动打标签或对接工作流。底层备份可以结合 Immich CLI（npm 包）做脚本化上传。

---

## 7. 机器学习模块

### 7.1 ONNX 统一推理

machine-learning 容器里的所有模型都是 ONNX 格式，由 ONNX Runtime 加载执行。请求进来后按文本或图像负载选择对应模型，模型被加载后缓存在内存里复用，多个请求放到线程池并行处理，避免阻塞异步事件循环。硬件加速通过给镜像追加 tag 启用：

| 加速器 | tag 后缀 |
|------|---------|
| CPU（默认） | 无 |
| NVIDIA GPU | `-cuda` |
| AMD GPU | `-rocm` |
| Intel 核显 | `-openvino` |
| ARM / Rockchip NPU | `-armnn`、`-rknn` |

### 7.2 人脸识别

检测用 SCRFD，特征是 ArcFace 风格的人脸模型（INSIGHTFACE 系列）在 ONNX 下运行。人脸聚类由 server 侧的后台任务完成，负责把同一人的照片归并，支持后续手动命名、合并、拆分。

### 7.3 CLIP 语义搜索

```text
1. 用 OpenCLIP（如 ViT-B-32、ViT-L-14）把每张图编码成向量
2. 搜索时把查询文本编码成同空间向量
3. 计算文本向量与全部图像向量的余弦相似度
4. 取相似度最高的结果返回
```

支持多语言查询的话可以切换到多语言 CLIP 变体。向量存在 PostgreSQL 的向量列里，用 ANN 索引加速近邻检索。首次全量索引用 CPU 跑需要较长时间，之后新上传的照片在后台增量索引。

### 7.4 OCR

图片里的可读文字会被抽取出向量和文本，用于文字搜索，也让"截图内容可检索"成为可能。OCR 同样在 ONNX/视觉管线中处理，需注意不是所有旧版模型镜像都带 OCR 能力。

---

## 8. 开发指南

### 8.1 本地开发环境

```bash
# 1. 克隆仓库
git clone https://github.com/immich-app/immich.git
cd immich

# 2. 安装依赖（工作区用 pnpm）
corepack enable
pnpm install

# 3. 拉起基础设施（数据库、Redis 等）
docker compose -f docker-compose.dev.yml up -d

# 4. 运行 Web 前端热更新
pnpm dev web

# 5. 运行移动端
cd mobile && flutter run
```

### 8.2 项目结构

```
immich/
├── server/            # NestJS 后端
│   ├── src/
│   │   ├── controllers/  # API 路由（HTTP 端点）
│   │   ├── services/     # 业务逻辑
│   │   ├── repositories/ # 技术实现（数据访问）
│   │   └── ...
├── web/               # SvelteKit Web UI
├── mobile/            # Flutter 移动端
├── machine-learning/  # Python ONNX 推理服务
├── cli/               # npm 命令行工具
└── open-api/          # OpenAPI 规范
```

server 后端大致遵循六边形（Hexagonal）架构：核心业务逻辑在 `services`，而具体的技术实现（数据库、Redis、文件系统）隔离在 `repositories`，视图通过 DTO 与外部交换，既方便测试也方便替换实现。

### 8.3 代码规范

```bash
# TypeScript / Node.js
pnpm lint        # ESLint
pnpm format      # Prettier
pnpm test        # 单元测试

# Flutter / Dart
flutter analyze
flutter format
flutter test

# Python
ruff check .
ruff format .
pytest
```

---

## 9. 常见问题

### 9.1 数据库起不来，报 pgvecto_rs 库加载失败

多半是用了标准 `postgres:14` 镜像，却没有向量扩展。模型选型要跟着官方 compose 走，使用带 vectorchord / pgvecto.rs 的镜像，不能换成普通 postgres。换回正确镜像后删除旧的数据库卷再启动。

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

智能功能依赖后台任务，先到 **管理 → 作业** 里看智能索引作业是否在跑、是否阻塞，再检查 machine-learning 容器状态与日志：

```bash
docker compose logs immich-machine-learning
```

首次对大批照片建索引在 CPU 上要跑很久，耐心等待增量完成即可，不要据此误判为故障。

### 9.4 内存占用高

machine-learning 在做推理和模型缓存时会吃内存。手头机器紧张时，可以给容器设内存上限：

```yaml
services:
  immich-machine-learning:
    mem_limit: 4g
```

同时按 4.5 的基线评估当前图库规模是否超出硬件能力。

### 9.5 升级后界面报错或任务异常

Immich 每周发版，跨版本升级偶有 schema 变化。先确认 `.env` 里的 `IMMICH_VERSION` 与你实际拉取的镜像一致，再 `docker compose pull && up -d`；仍异常时到 GitHub Issues 或 Discord 社区按版本号检索是否已知问题。

---

## 自测清单

- 能说出 Immich 与 Google Photos 在数据载体上的本质差异。
- 能用 Docker Compose 部署并通过 2283 端口访问，说出 server 与 machine-learning 的分工。
- 知道为什么用 PostgreSQL 而非 SQLite：向量检索、多用户、并发写入、任务状态都需要一个可靠的数据库，SQLite 不适合这类并发负载。
- 能解释人脸识别四步流程各自的作用，以及 CLIP 语义搜索如何把文本与图像统一到同一向量空间。
- 能列出备份时必须覆盖的三类数据，以及每类对应什么故障场景。
- 能判断一个问题该查 server 日志还是 machine-learning 日志。

---

## 进阶路径

**已经部署，想进一步用好：**

- **性能调优**：图库超 100 GB 后关注智能索引重建频率与 ML 内存；有 NVIDIA GPU 时给 machine-learning 容器追加 `-cuda` tag。
- **备份完善**：把 3-2-1 原则落到实际，数据库用 `pg_dump`，媒体文件用 `rsync`，再把副本推到异地存储。
- **多用户规划**：给家人用提前设计管理员、普通用户、外部分享三种权限的边界。
- **外部集成**：用 API Key 写批量导入、自动归档脚本，或把 Immich 接进既有自动化工作流。

**想参与项目：**

- 仓库地址：https://github.com/immich-app/immich
- 后端 NestJS + SvelteKit + Flutter 任一熟悉即可，从 `good first issue` 入手。
- 机器学习侧是 Python + ONNX，熟悉人脸识别或 CLIP 模型可以参与模型选型与推理优化。

---

## 10. 总结

Immich 用一个社区维护的开源项目，覆盖了从移动端自动备份到 Web 浏览、人脸聚类、语义搜索、相册分享的完整链路。数据落在自己服务器上，代码可审计，没有隐藏追踪。

它的代价也很明确：**一切需要你自己运维**。媒体与数据库备份、升级窗口、硬件容量、故障排查，都不再有云厂商替你兜底。它适合愿意投入一点的个人用户、家庭和小团队；如果你要的是"零维护的备份"，Google Photos 这类服务仍是最省心的选择。

**官方资源：**

- 官网：https://immich.app
- 文档：https://docs.immich.app
- 安装要求：https://docs.immich.app/install/requirements/
- 演示：https://demo.immich.app
- GitHub：https://github.com/immich-app/immich
- Releases：https://github.com/immich-app/immich/releases