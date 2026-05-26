---
title: "Jellyfin 完全指南：开源媒体服务器的终极选择"
date: 2026-05-27T03:05:00+08:00
tags: ["Jellyfin", "媒体服务器", "开源", "Plex替代", "家庭影院", "NAS"]
categories: ["开源项目"]
description: "Jellyfin 是 Emby 3.5.2 的开源分支，完全免费的媒体系统。本文详解其功能、技术架构、安装配置和高级用法。"
---

# Jellyfin 完全指南：开源媒体服务器的终极选择

## 简介

[Jellyfin](https://github.com/jellyfin/jellyfin) 是完全开源的媒体系统，是 Emby 和 Plex 的免费替代方案。项目已获得 **52,326** Star，是开源媒体服务器领域的绝对领导者。

官网：[jellyfin.org](https://jellyfin.org)

## 什么是 Jellyfin？

Jellyfin 让你掌控管理和流媒体传输媒体的全过程。它源自 Emby 3.5.2 版本，并移植到 .NET 平台以实现完整的跨平台支持。

**核心理念**：无字符串、无高级许可、无隐藏议程——只有一个想要构建更好东西的团队。

## 核心功能

### 1. 媒体管理
- 自动扫描和整理媒体库
- 支持电影、电视剧、音乐、书籍等
- 自动获取元数据（海报、简介、演员等）
- 收藏和标签管理

### 2. 多平台客户端
- Web 界面（任何浏览器）
- Android / Android TV
- iOS / tvOS
- Roku、Samsung、LG 等智能 TV
- Kodi 集成

### 3. 直播电视 (Live TV)
- 支持 DVR 功能
- 集成 TV tuner 设备
- EPG 电子节目指南

### 4. 用户和权限管理
- 多用户支持
- 基于库或媒体的家庭限制
- 观看历史和进度同步

### 5. 转码和流媒体
- 硬件加速转码（Intel QuickSync、NVIDIA、AMD）
- 按需转码适配不同客户端
- 字幕转译和嵌入

## 技术架构

### 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | C# / .NET 10 |
| 数据库 | SQLite / PostgreSQL（可选） |
| Web 前端 | React（独立仓库） |
| 媒体处理 | ffmpeg |
| 协议 | DLNA, UPnP, HTTP(S) |

### 项目结构

```
jellyfin/
├── Jellyfin.Server/          # 主服务器项目
├── Jellyfin.Api/             # API 层
├── Jellyfin.Data/            # 数据访问
├── Jellyfin.Plugins/         # 插件系统
├── MediaBrowser.Controller/   # 核心媒体控制器
└── ffmpeg/                   # 绑定的 ffmpeg 版本
```

### API

Jellyfin 提供完整的 REST API，可通过 `http://localhost:8096/api-docs/swagger/` 访问 Swagger 文档。

## 安装指南

### 方式一：Docker（推荐）

```bash
docker run -d \
  --name jellyfin \
  --privileged \
  -p 8096:8096 \
  -p 8920:8920 \
  -v /path/to/config:/config \
  -v /path/to/cache:/cache \
  -v /path/to/media:/media \
  --device /dev/dri:/dev/dri \
  jellyfin/jellyfin
```

### 方式二：直接从源码构建

```bash
# 1. 克隆仓库
git clone https://github.com/jellyfin/jellyfin.git
cd jellyfin

# 2. 安装依赖
# - .NET 10 SDK
# - ffmpeg

# 3. 构建
dotnet build

# 4. 运行
dotnet run --project Jellyfin.Server --webdir /path/to/jellyfin-web/dist
```

### 方式三：二进制安装

从 [jellyfin.org/downloads](https://jellyfin.org/downloads) 下载对应平台的安装包。

## 配置推荐

### 硬件加速转码

**Intel QuickSync (Linux)**:
```bash
docker run -d \
  --device /dev/dri:/dev/dri \
  jellyfin/jellyfin
```

**NVIDIA GPU**:
```bash
docker run -d \
  --runtime nvidia \
  -e NVIDIA_VISIBLE_DEVICES=0 \
  jellyfin/jellyfin
```

### 媒体库配置

建议的目录结构：
```
/media
├── movies
├── tv
├── music
└── books
```

每个媒体类型单独配置一个库，Jellyfin 会自动刮削元数据。

### 用户权限

- 创建家庭成员账户
- 限制儿童账户的访问内容
- 启用观看时间限制

## 插件生态

Jellyfin 支持插件扩展，主要插件类型：

- **Metadata providers** — 扩展元数据源
- **Playback** — 新播放后端
- **Notifications** — 通知渠道（Email、Push、Webhook）
- **Analytics** — 使用统计

## 性能优化

### 1. 硬件加速

确保系统有支持的 GPU：
- Intel QuickSync (6th+ CPU)
- NVIDIA GPU (GTX 900+)
- AMD GPU (Ryzen APU 或 Radeon)

### 2. 资源分配

Docker 部署建议：
- 内存：4GB+（取决于库大小）
- CPU：4核+（转码时）
- 网络：千兆局域网

### 3. 数据库优化

小规模部署（<10000项）用 SQLite 即可，大型库推荐 PostgreSQL：

```bash
# 环境变量
JELLYFIN_DATABASE_TYPE=postgres
DATABASE_CONNECTION_STRING="Host=postgres;Database=jellyfin;User=foo;Password=bar"
```

## 与 Emby / Plex 对比

| 特性 | Jellyfin | Emby | Plex |
|------|----------|------|------|
| 费用 | 完全免费 | 免费+高级版 | 免费+高级版 |
| 开源 | ✅ | ❌ | ❌ |
| 平台 | 全平台 | 全平台 | 全平台 |
| 硬件转码 | ✅ | ✅ | ✅ |
| 直播电视 | ✅ | 高级功能 | ✅ |
| 插件支持 | ✅ | ✅ | ❌ |
| 社区规模 | 大 | 中 | 大 |

## 常见问题

**Q: Jellyfin 和 Emby 哪个好？**
A: 如果需要免费开源，选 Jellyfin。Emby 有更好的默认 UI 和更多高级功能（但需付费）。

**Q: 如何处理字幕？**
A: Jellyfin 自动下载嵌入字幕，也支持 srt/ssa 外部字幕文件。

**Q: 能同时服务多个用户吗？**
A: 可以，Jellyfin 设计为多用户并发访问，局域网环境下通常支持 5-10 人同时播放。

## 总结

Jellyfin 是目前最成熟的免费开源媒体服务器，拥有活跃的社区、完善的文档和跨平台支持。无论你是家庭用户还是小型企业，它都能提供专业级的媒体管理和流媒体服务。

**GitHub**: [jellyfin/jellyfin](https://github.com/jellyfin/jellyfin)
**Star**: 52,326 | **Fork**: 4,868
**官网**: [jellyfin.org](https://jellyfin.org)