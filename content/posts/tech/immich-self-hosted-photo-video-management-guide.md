---
title: "Immich：高性能自托管照片和视频管理解决方案完全指南"
date: 2026-04-06T21:30:00+08:00
slug: "immich-self-hosted-photo-video-management-guide"
description: "全面介绍 96.6k Stars 的 Immich 自托管照片和视频管理方案，涵盖 Docker 部署、多端架构、人脸识别、CLIP 搜索、API 集成等核心功能，以及开发指南和常见问题解决方案。"
draft: false
categories: ["技术笔记"]
tags: ["Immich", "自托管", "照片管理", "Flutter", "NestJS"]
---

## 学习目标

通过本文，你将全面掌握以下核心能力：

- 深入理解 Immich 的项目定位、技术架构和设计理念
- 掌握 Immich 的核心功能（照片/视频备份、人脸识别、CLIP 搜索等）
- 学会部署 Immich（Docker、docker-compose）
- 理解 Immich 的多端架构（Web、iOS、Android）
- 掌握 Immich 的 API 和第三方集成
- 理解 Immich 的机器学习模块（人脸识别、物体检测）
- 学会开发 Immich 插件和自定义部署

---

## 1. 项目概述

### 1.1 是什么

Immich 是一个**高性能自托管的照片和视频管理解决方案**，是 Google Photos 的开源替代品。

它允许你在自己的服务器上部署完整的照片/视频备份和管理系统，**无需依赖任何云服务**，完全掌控你的数据。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **96.6k** |
| GitHub Forks | **5.3k** |
| 贡献者 | **1,993** |
| 最新版本 | **v2.6.3**（2026-03-27） |
| License | **AGPLv3** |

### 1.3 技术栈

| 组件 | 语言 | 占比 |
|------|------|------|
| **服务端** | TypeScript (NestJS) | 46.8% |
| **移动端** | Dart (Flutter) | 34.6% |
| **Web UI** | Svelte (SvelteKit) | 12.2% |
| **Android** | Kotlin | 2.0% |
| **iOS** | Swift | 1.8% |
| **机器学习** | Python | 1.4% |

### 1.4 与竞品对比

| 特性 | Immich | Google Photos | iCloud Photos |
|------|--------|---------------|---------------|
| **自托管** | ✅ 完全掌控 | ❌ | ❌ |
| **隐私保护** | ✅ 本地存储 | ❌ | ❌ |
| **人脸识别** | ✅ 本地 | ✅ | ✅ |
| **自动备份** | ✅ | ✅ | ✅ |
| **多用户** | ✅ | ❌（家庭共享） | ✅ |
| **RAW 格式** | ✅ | ✅ | ✅ |
| **开源** | ✅ | ❌ | ❌ |

---

## 2. 核心功能详解

### 2.1 照片和视频管理

**上传和查看**

```bash
# Web 端功能
- 支持拖拽上传
- 支持批量上传
- 支持大文件（视频/RAW）
- 支持虚拟滚动（流畅浏览大量照片）
```

**自动备份（移动端）**

| 平台 | 功能 |
|------|------|
| **iOS/Android** | 打开 App 时自动后台备份 |
| **后台备份** | 持续同步新照片 |
| **选择性备份** | 只备份指定相册 |

### 2.2 重复照片检测

```python
# Immich 使用多种策略检测重复
- 文件大小比对
- EXIF 元数据比对
- 感知哈希（Perceptual Hash）
- 内容比对（AI 辅助）
```

### 2.3 RAW 格式支持

| 格式 | 支持情况 |
|------|---------|
| **Canon CR2/CR3** | ✅ |
| **Nikon NEF** | ✅ |
| **Sony ARW** | ✅ |
| **Adobe DNG** | ✅ |
| **Apple ProRAW** | ✅ |
| **Samsung RAW** | ✅ |

### 2.4 元数据和地理信息

```bash
# EXIF 信息展示
- 相机型号
- 拍摄参数（光圈/快门/ISO）
- GPS 坐标
- 拍摄时间

# 地图视图
- 全球照片分布图
- 按地理位置浏览
- 地理位置纠错
```

### 2.5 搜索功能

| 搜索类型 | 技术实现 |
|----------|---------|
| **元数据搜索** | 相机型号、时间、地点 |
| **物体识别** | CLIP 多模态模型 |
| **人脸搜索** | 人脸识别 + 聚类 |
| **文字描述** | AI 生成描述 |

```bash
# CLIP 搜索示例
搜索："海边日落的照片"
结果：AI 理解图像内容，返回匹配结果
```

### 2.6 人脸识别和聚类

```python
# 人脸识别流程
1. 检测人脸边界框
2. 提取人脸特征向量（FaceNet）
3. 聚类分析（同一人的照片归组）
4. 支持手动合并/分割人物
5. 人物名称标注
```

---

## 3. 系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────┐
│              客户端层                   │
├──────────┬──────────┬──────────┬──────────┤
│   Web    │   iOS    │  Android │    CLI   │
│ (Svelte)│ (Flutter)│ (Flutter)│ (Node.js)│
└────┬────┴────┬────┴────┬────┴────────┘
     │         │         │
     └─────────┴─────────┘
              │ REST API
              ▼
┌─────────────────────────────────────┐
│           API 网关层                   │
│         (TypeScript/NestJS)          │
│  - 认证鉴权                         │
│  - 请求路由                         │
│  - 限流保护                         │
└────────────────┬────────────────────┘
                   │
     ┌────────────┼────────────┐
     ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────────┐
│  存储层  │ │  数据库层 │ │  ML 引擎层  │
│ (S3/NAS)│ │ (Postgre)│ │ (PyTorch)  │
└─────────┘ └─────────┘ └─────────────┘
```

### 3.2 核心模块

| 模块 | 技术栈 | 功能 |
|------|--------|------|
| **server** | NestJS + TypeScript | API 服务、数据处理 |
| **web** | SvelteKit + TypeScript | Web 管理界面 |
| **mobile** | Flutter + Dart | iOS/Android 应用 |
| **machine-learning** | Python + PyTorch | 人脸识别、物体检测 |
| **cli** | Node.js + TypeScript | 命令行工具 |
| **open-api** | OpenAPI 3.0 | 公共 API 规范 |

### 3.3 数据库设计

```sql
-- 核心表结构（简化）
assets          -- 媒体资产（照片/视频）
users           -- 用户
albums          -- 相册
faces           -- 人脸数据
smart_searches   -- AI 搜索索引
```

### 3.4 存储策略

```yaml
# 支持的存储后端
storage:
  - 本地文件系统
  - S3 兼容存储（AWS S3, MinIO, Backblaze）
  - NAS 挂载（SMB/NFS）
  - 外部存储路径

# 用户自定义存储结构
user_storage:
  by_date: "/photos/{year}/{month}/{day}"
  by_album: "/albums/{album_name}"
```

---

## 4. 部署指南

### 4.1 Docker Compose 部署（推荐）

```yaml
# docker-compose.yml
version: '3.8'

services:
  immich-server:
    image: immich-app/immich-server:release
    container_name: immich_server
    ports:
      - "2283:3000"
    volumes:
      - ./upload:/usr/src/app/upload
      - /etc/localtime:/etc/localtime:ro
    environment:
      - DB_HOSTNAME=immich_postgres
      - REDIS_HOSTNAME=immich_redis
    depends_on:
      - immich_postgres
      - immich_redis

  immich_machine_learning:
    image: immich-app/immich-machine-learning:release
    container_name: immich_ml

  immich_redis:
    image: redis:14
    container_name: immich_redis

  immich_postgres:
    image: tensorchord/pgvecto-rs:pg14-v0.2.0
    container_name: immich_postgres

  immich_typesense:
    image: typesense/typesense:26.0
    container_name: immich_typesense
```

### 4.2 启动命令

```bash
# 创建容器网络
docker network create immich_network

# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 4.3 环境变量配置

| 变量 | 说明 | 默认值 |
|------|------|---------|
| `DB_HOSTNAME` | 数据库主机 | localhost |
| `REDIS_HOSTNAME` | Redis 主机 | localhost |
| `UPLOAD_LOCATION` | 上传文件路径 | ./upload |
| `PUBLIC_LOGIN_PAGE_MESSAGE` | 登录页提示 | - |
| `IMMICH_MACHINE_LEARNING_URL` | ML 服务地址 | http://immich_machine_learning:3000 |

### 4.4 反向代理配置

```nginx
# Nginx 反向代理配置
server {
    listen 443 ssl;
    server_name your-immich-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:2283;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        # 文件上传大小限制
        client_max_body_size 100M;
        
        # WebSocket 支持（实时通知）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 4.5 数据备份策略

⚠️ **重要提示**：遵循 3-2-1 备份原则

```
3-2-1 备份原则：
- 3 份数据副本
- 2 种不同存储介质
- 1 份异地存储
```

```bash
# 备份脚本示例
#!/bin/bash
# 备份 Immich 数据

# 1. 导出数据库
docker exec immich_postgres pg_dump -U postgres > backup_$(date +%Y%m%d).sql

# 2. 备份上传文件
rsync -avz ./upload/ /path/to/backup-drive/

# 3. 备份配置文件
cp .env /path/to/backup-drive/
```

---

## 5. 移动端使用

### 5.1 iOS/Android 应用

| 功能 | iOS | Android |
|------|-----|---------|
| **自动备份** | ✅ | ✅ |
| **后台备份** | ✅ | ✅ |
| **选择性相册** | ✅ | ✅ |
| **电池优化跳过** | ✅ | ✅ |
| **RAW 备份** | ✅ | ✅ |
| **LivePhoto** | ✅ | ✅ |
| **离线模式** | ✅ | ❌ |

### 5.2 应用设置

```dart
// Flutter 应用配置选项
AppSettings:
  - 自动备份：开启/关闭
  - 备份仅 WiFi：开启/关闭
  - 备份质量：高/中/低/原始
  - 电池优化：允许后台运行
  - 通知：备份完成/失败通知
```

---

## 6. 高级功能

### 6.1 多用户和权限管理

| 角色 | 权限 |
|------|------|
| **管理员** | 用户管理、存储配额、系统设置 |
| **用户** | 创建相册、分享、标签 |
| **只读** | 浏览、下载 |
| **访客** | 受限分享内容 |

### 6.2 相册和分享

```bash
# 相册类型
- 个人相册：仅自己可见
- 共享相册：邀请他人协作
- 外部分享：生成公开链接
- 合作伙伴：双向自动分享
```

### 6.3 OAuth 和 SSO

```yaml
# 支持的 OAuth 提供商
oauth:
  - Google
  - Facebook
  - LinkedIn
  - GitHub
  - SAML 2.0  # 企业 SSO
```

### 6.4 API 访问

```bash
# 获取 API Key
# 设置 → API Keys → 创建新 Key

# 使用 API
curl -H "x-api-key: YOUR_API_KEY" \
     https://your-immich.com/api/assets
```

---

## 7. 机器学习模块

### 7.1 架构

```
┌────────────────────────────────────┐
│      Immich ML Engine (Python)      │
├──────────────┬─────────────────────┤
│  人脸识别    │   物体检测          │
│ (FaceNet)   │   (YOLO/TensorFlow) │
├──────────────┼─────────────────────┤
│  CLIP 搜索  │   场景识别          │
│ (OpenCLIP)  │   (MobileNet)       │
└──────────────┴─────────────────────┘
```

### 7.2 人脸识别流程

```python
# 人脸识别伪代码
def recognize_faces(image):
    # 1. 检测人脸
    boxes = face_detector(image)
    
    # 2. 提取特征
    embeddings = face_encoder(image, boxes)
    
    # 3. 与已知人脸比对
    for embedding in embeddings:
        matches = find_similar(embedding, known_faces)
        
    return clusters
```

### 7.3 CLIP 多模态搜索

```python
# CLIP 搜索原理
def clip_search(query_text, image_db):
    # 1. 将文本编码为向量
    query_embedding = clip.encode_text(query_text)
    
    # 2. 与所有图像向量比对
    results = []
    for image in image_db:
        similarity = cosine_similarity(
            query_embedding, 
            image.embedding
        )
        results.append((image, similarity))
    
    # 3. 返回最相似的图像
    return sorted(results, key=lambda x: x[1], reverse=True)
```

---

## 8. 开发指南

### 8.1 本地开发环境

```bash
# 1. 克隆仓库
git clone https://github.com/immich-app/immich.git
cd immich

# 2. 安装依赖（使用 pnpm）
corepack enable
pnpm install

# 3. 启动开发服务
docker-compose -f docker-compose.dev.yml up -d

# 4. 运行 Web 开发服务器
pnpm dev web

# 5. 运行移动端
cd mobile && flutter run
```

### 8.2 项目结构

```
immich/
├── server/           # NestJS 后端服务
│   ├── src/
│   │   ├── api/     # API 路由
│   │   ├── domain/   # 业务逻辑
│   │   ├── entities/# 数据库实体
│   │   └── immich.controller.ts
│   └── test/
├── web/              # SvelteKit Web UI
│   ├── src/
│   │   ├── lib/     # 组件库
│   │   ├── routes/   # 页面路由
│   │   └── stores/  # 状态管理
│   └── static/
├── mobile/           # Flutter 移动端
│   ├── lib/
│   │   ├── app/     # 主应用
│   │   ├── services/ # 服务层
│   │   └── widgets/ # UI 组件
│   └── test/
├── machine-learning/  # Python ML 引擎
│   ├── model/
│   ├── face/
│   └── clip/
├── cli/              # Node.js 命令行
└── open-api/         # OpenAPI 规范
```

### 8.3 代码规范

```bash
# TypeScript/Node.js
pnpm lint          # ESLint 检查
pnpm format        # Prettier 格式化
pnpm test          # 运行测试

# Flutter/Dart
flutter analyze    # Dart 分析
flutter format     # 格式化
flutter test       # 运行测试

# Python
ruff check .        # Lint 检查
ruff format .       # 格式化
pytest              # 运行测试
```

---

## 9. 常见问题

### 9.1 上传失败

```bash
# 检查存储权限
ls -la ./upload
chmod 755 ./upload

# 检查磁盘空间
df -h

# 检查 Docker 日志
docker-compose logs immich_server | grep -i error
```

### 9.2 人脸识别不工作

```python
# 重启 ML 容器
docker-compose restart immich_machine_learning

# 检查 ML 模型是否正确加载
docker exec immich_machine_learning python -c "import torch; print(torch.cuda.is_available())"
```

### 9.3 内存占用高

```yaml
# 限制 Docker 内存
services:
  immich_server:
    mem_limit: 4g
    mem_reservation: 2g
```

---

## 10. 总结

Immich 是一个功能完备的**自托管照片和视频管理解决方案**：

**为什么选择 Immich：**

| 优势 | 说明 |
|------|------|
| **完全隐私** | 数据存储在自己的服务器 |
| **开源透明** | 代码可审计，无隐藏追踪 |
| **功能丰富** | 人脸识别、CLIP 搜索、RAW 支持 |
| **多平台支持** | Web、iOS、Android、CLI |
| **社区活跃** | 1993+ 贡献者，持续更新 |
| **部署简单** | Docker 一键部署 |

**适用场景：**

- 个人照片/视频备份（替代 Google Photos）
- 家庭共享相册
- 小型企业媒体资产管
- 摄影师作品管理
- 私有云盘

**官方资源：**

- 官网：https://immich.app
- 文档：https://docs.immich.app
- 演示：https://demo.immich.app
- Discord：https://discord.immich.app
- GitHub：https://github.com/immich-app/immich