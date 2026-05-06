---
title: "Jellyfin：开源自由媒体服务器，完全掌控你的影音库"
date: "2026-05-05T11:40:00+08:00"
slug: "jellyfin-open-source-media-server-complete-guide"
description: "Jellyfin是功能完整的开源自由媒体系统，提供媒体管理、串流播放、用户权限管理等功能，可完全替代Plex和Emby。本文详解其架构设计、核心功能、部署配置、客户端使用与插件生态。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "媒体服务器", "Plex替代", "家庭影院", "Docker", "影音"]
---

## 项目概览

[Jellyfin](https://github.com/jellyfin/jellyfin)是一个免费、开源、社区驱动的媒体服务器软件，用于管理和流式传输您的音乐、视频、电子书和图片收藏。它是Plex的完全开源替代品，不包含任何专有组件或跟踪功能。

**核心数据：**
- GitHub Stars：37,000+
- 主要语言：C#/.NET
- 平台：Windows、macOS、Linux、Docker、FreeBSD
- License：GPLv2

**核心功能：**
- 媒体管理与元数据刮削（自动获取电影、剧集海报、简介）
- 多用户支持与观看权限控制
- 实时转码（H.264/H.265/VP9等格式兼容）
- 支持DLNA、Roku、Amazon Fire TV、Android TV等设备
- 插件扩展系统
- 字幕下载与挂载
- 音乐、图片、电子书库管理

---

## Jellyfin vs Plex vs Emby

| 维度 | Jellyfin | Plex | Emby |
|------|----------|------|------|
| License | GPLv2（完全开源） | 专有+部分开源 | 专有+部分开源 |
| 价格 | 完全免费 | 免费+Premium订阅 | 免费+Premiere订阅 |
| 媒体数据收集 | 开源Agent | 专有Agent（付费） | 部分付费 |
| 官方移动端 | 无（第三方） | 有 | 有 |
| 转码加速 | 软件转码 | 硬件加速（Premium） | 硬件加速（Premium） |
| 数据隐私 | 完全自主 | 部分依赖云服务 | 部分依赖云服务 |
| 社区活跃度 | 非常活跃 | 活跃 | 一般 |

**Jellyfin的优势：**
- 完全开源，没有隐藏费用或订阅
- 不需要连接官方服务器即可使用
- 媒体库数据完全存储在本地
- 活跃的社区持续开发新功能

---

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────┐
│              Jellyfin Server                │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │  媒体库   │ │  元数据   │ │   插件     │  │
│  │  管理     │ │  服务     │ │   系统     │  │
│  └──────────┘ └──────────┘ └────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │  转码引擎 │ │  用户认证 │ │  DLNA/DLNA │  │
│  │          │ │  管理     │ │            │  │
│  └──────────┘ └──────────┘ └────────────┘  │
└──────────┬──────────────────┬──────────────┘
           │                  │
      ┌────┴────┐        ┌────┴────┐
      │  本地   │        │  网络   │
      │  存储   │        │  串流   │
      └─────────┘        └────┬────┘
                              │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────┴────┐    ┌────┴────┐    ┌────┴────┐
         │  Web    │    │  移动端 │    │  TV     │
         │  浏览器  │    │  App    │    │  设备   │
         └─────────┘    └─────────┘    └─────────┘
```

### 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | C# / .NET Core |
| 前端 | Ember.js / TypeScript |
| 数据库 | SQLite（默认）/ PostgreSQL（生产） |
| 媒体处理 | FFmpeg |
| 认证 | JWT |

---

## 安装部署

### Docker（推荐）

```bash
# 最简部署
docker run -d \
  --name jellyfin \
  -p 8096:8096 \
  -p 8920:8920 \
  -v /path/to/media:/media \
  -v jellyfin-config:/config \
  -v jellyfin-cache:/cache \
  jellyfin/jellyfin:latest
```

访问 `http://your-server:8096` 完成初始化向导。

### Docker Compose（完整配置）

```yaml
version: "3.8"
services:
  jellyfin:
    image: jellyfin/jellyfin:latest
    container_name: jellyfin
    ports:
      - "8096:8096"
      - "8920:8920"  # HTTPS
    volumes:
      - ./config:/config
      - ./cache:/cache
      - /path/to/media:/media:ro
      - /etc/localtime:/etc/localtime:ro
    restart: unless-stopped
    environment:
      - TZ=Asia/Shanghai
    gpu: "all"  # NVIDIA GPU加速
```

### 硬件加速配置

**NVIDIA GPU（转码加速）：**
```yaml
services:
  jellyfin:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
```

**Intel QuickSync（Linux）：**
```bash
# 添加设备映射
docker run ... --device /dev/dri:/dev/dri
```

---

## 初始化配置

### 首次设置向导

1. 访问 `http://your-server:8096`
2. 选择语言（支持简体中文）
3. 创建管理员账号
4. 添加媒体库（选择媒体类型和文件夹）
5. 配置元数据获取（TheMovieDB、TVDB等）
6. 完成

### 媒体库配置建议

| 媒体类型 | 命名规范 | 推荐刮削源 |
|---------|---------|-----------|
| 电影 | `Movie Name (Year).ext` | TMDB |
| 剧集 | `Show/Season XX/Episode XX.ext` | TVDB |
| 音乐 | `Artist/Album/Track.ext` | MusicBrainz |
| 图片 | 按文件夹分类即可 | 无需刮削 |

### 元数据代理配置（解决国内访问问题）

由于Jellyfin默认的元数据源（TMDB、TVDB）在大陆访问不稳定，建议配置代理：

```json
// config/network.xml 或 Jellyfin控制台设置
{
  "baseUrl": "https://api.tmdb.org",
  "apiKey": "your-tmdb-api-key"
}
```

或在Docker中配置HTTP代理：

```bash
-e HTTP_PROXY=http://your-proxy:port
```

---

## 核心功能使用

### 1. 媒体库管理

Jellyfin自动刮削以下元数据：
- 海报（Poster）
- 背景图（Backdrop）
- 剧情简介
- 演职员信息
- 评分（豆瓣、IMDB等）
- 季/集信息

### 2. 用户与权限管理

管理员可以为不同用户设置：
- 访问哪些媒体库
- 内容评级限制（如R级、NC-17级）
- 播放限制（同时在线数、清晰度限制）
- 远程访问权限

### 3. 实时转码

Jellyfin支持实时转码，确保在任何设备上都能流畅播放：

| 输入格式 | 输出格式 | 适用场景 |
|---------|---------|---------|
| H.265/HEVC | H.264 | 老旧设备 |
| 4K HDR | 1080p SDR | 低带宽网络 |
| 原盘 (ISO) | MP4 | 通用播放 |

### 4. 字幕功能

- 自动下载字幕（OpenSubtitles等）
- 字幕偏移调整
- 字体选择（中文字体支持）
- 强制字幕设置

---

## 插件系统

Jellyfin支持丰富的插件扩展：

### 推荐插件

| 插件 | 功能 |
|------|------|
| [Jellyfin OpenSubtitles](https://github.com/Julianlalrac/Jellyfin-plugin-OpenSubtitles) | 自动下载字幕 |
| [Jellyfin-MetaBuddy](https://github.com/oddstr13/jellyfin-metadatabuddy) | 元数据增强 |
| [Jellyfin-TelegramBot](https://github.com/nicknsy/jellyfin-telegram-notify) | Telegram通知 |

### 官方插件仓库

通过Jellyfin控制台 → Plugins → Catalog 安装社区插件。

---

## 适用场景

### 适合的场景
- 家庭媒体中心（家庭影院PC/NAS）
- 小型工作室共享媒体资源
- 个人影片收藏管理
- 替代Plex/Emby（不想付订阅费）
- 重视数据隐私（媒体库不上传到第三方）

### 边界与局限
- 官方没有iOS/Android原生App（社区有第三方）
- 4K HDR转码性能依赖硬件（CPU/GPU）
- 部分功能（如TV Guide）国内源不稳定

---

## 总结

Jellyfin是完全开源、功能完整的媒体服务器，适合：
1. **隐私敏感用户**：媒体库完全本地存储，无云端依赖
2. **成本敏感用户**：完全免费，无Plex/Emby的订阅费
3. **技术爱好者**：开源可控，可自行修改和扩展

作为Plex最成熟的替代品，Jellyfin在持续活跃的开发下功能已十分完善，是搭建家庭媒体中心的首选方案。

**参考链接：**
- GitHub：https://github.com/jellyfin/jellyfin
- 官方文档：https://jellyfin.org/docs
- 下载地址：https://jellyfin.org/downloads
- 插件仓库：https://repo.jellyfin.org/plugins