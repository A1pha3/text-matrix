---
title: "Jellyfin：不把媒体库交给云端的自建方案"
date: "2026-05-05T11:40:00+08:00"
slug: "jellyfin-open-source-media-server-complete-guide"
description: "Jellyfin 真正解决的问题不是「播放视频」，而是让媒体库的存储、索引、转码和权限控制完全留在你自己手里。本文从架构、部署、转码到客户端选择，给出可落地的搭建路线。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "媒体服务器", "Plex替代", "家庭影院", "Docker", "影音"]
---

## 这篇文章解决什么问题

你有一堆电影、剧集和音乐文件，想在任何设备上随时观看，但不想把媒体库索引和播放记录交给 Plex 或 Emby 的云端服务。Jellyfin 是目前唯一一个功能完整、社区活跃、且从头到尾不依赖外部服务器的开源方案。

读完这篇文章，你可以：

- 在 NAS 或 Linux 服务器上把 Jellyfin 跑起来，并配置硬件转码
- 理解 Jellyfin 的模块划分——媒体库扫描、元数据刮削、实时转码和用户认证各自干了什么
- 知道什么时候该用 Jellyfin，什么时候不如直接用 SMB + VLC

---

## 先把系统地图画出来

Jellyfin 不是一个单体应用，而是几套独立子系统在同一个进程里协作。用一张图把它们的边界划清楚，后面再逐个展开。

```
┌──────────────────────────────────────────────────┐
│                  Jellyfin Server                  │
│                                                   │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ 媒体库扫描 │  │ 元数据刮削 │  │  插件系统      │  │
│  │ (文件监控) │  │ (TMDB等)  │  │  (字幕/通知等) │  │
│  └────┬─────┘  └────┬─────┘  └───────────────┘  │
│       │             │                             │
│  ┌────┴─────────────┴──────┐  ┌───────────────┐  │
│  │      SQLite / PostgreSQL │  │  用户认证 (JWT) │  │
│  └──────────────────────────┘  └───────────────┘  │
│                                                   │
│  ┌──────────────────────────────────────────────┐ │
│  │           FFmpeg 转码引擎                     │ │
│  │  H.265→H.264 / 4K→1080p / 硬解 (VAAPI/QSV)  │ │
│  └──────────────────┬───────────────────────────┘ │
└─────────────────────┼─────────────────────────────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
     ┌────┴────┐ ┌────┴────┐ ┌────┴────┐
     │ Web 端  │ │ 移动端  │ │ TV 端   │
     │ (自带)  │ │ (第三方) │ │ (Android│
     │         │ │         │ │  TV等)  │
     └─────────┘ └─────────┘ └─────────┘
```

三条主线的职责边界：

1. **媒体库扫描 + 元数据刮削**：负责把你的文件系统变成可浏览的影音库。它扫描文件夹、识别文件名、从 TMDB / TVDB 拉海报和简介，写入本地数据库。
2. **FFmpeg 转码引擎**：负责在播放时把源文件实时转成客户端能解码的格式。这是 Jellyfin 最吃 CPU / GPU 的部分。
3. **用户认证与权限**：决定谁能看到哪些库、能以什么清晰度播放。认证完全本地，不经过任何外部服务。

---

## 一次播放请求如何穿过整个系统

把抽象结构串起来看一个具体例子：你在手机上用 4G 网络点播一部 4K HDR 电影。

1. 手机 App 向 Jellyfin Server 发起播放请求，携带 JWT token。
2. 认证模块校验 token 有效，并且你的账号有权访问这部电影所在的媒体库。
3. 转码引擎检查源文件格式（假设是 HEVC 10bit HDR），对比客户端能力（手机 App 在 4G 下只能接受 1080p SDR），决定启动转码。
4. FFmpeg 开始读取源文件，用 GPU 做硬件解码 + 缩放 + 色调映射，输出 H.264 1080p SDR 流。
5. 转码后的流以 HLS 分片形式推给手机 App，App 边下边播。

整个过程，Jellyfin 没有向任何外部服务器发过请求——认证是本地的、转码是本地的、媒体文件也是本地的。这就是它和 Plex / Emby 最根本的区别。

---

## 和 Plex、Emby 的边界在哪

| 维度 | Jellyfin | Plex | Emby |
|------|----------|------|------|
| 许可证 | GPLv2（完全开源） | 专有 + 部分开源 | 专有 + 部分开源 |
| 价格 | 完全免费 | 免费 + Premium 订阅 | 免费 + Premiere 订阅 |
| 认证依赖 | 本地，无外部服务 | 需 Plex 账号（部分功能） | 需 Emby Connect（可选） |
| 元数据刮削 | 开源 Agent，直连 TMDB 等 | 专有 Agent（付费） | 部分付费 |
| 硬件转码 | 免费（依赖硬件驱动） | Premium 订阅 | Premiere 订阅 |
| 官方移动端 | 无（社区第三方 App） | 有 | 有 |
| 数据隐私 | 完全自主 | 部分依赖云服务 | 部分依赖云服务 |

一句话：如果你不想为硬件转码付费、也不想媒体库的任何元数据离开你的服务器，选 Jellyfin。如果你更看重官方移动端 App 的开箱体验，Plex 或 Emby 更省事。

---

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 后端 | C# / .NET Core | 跨平台，性能足够 |
| 前端 | Ember.js / TypeScript | 自带 Web UI |
| 数据库 | SQLite（默认）/ PostgreSQL | 生产环境建议切 PostgreSQL |
| 媒体处理 | FFmpeg | 所有转码和封装都走 FFmpeg |
| 认证 | JWT | 无状态 token，不依赖外部服务 |

---

## 安装部署

### Docker（最快上手）

```bash
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

### Docker Compose（生产环境推荐）

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
    devices:
      - /dev/dri:/dev/dri  # Intel QuickSync / VAAPI 硬件加速
```

### 硬件加速配置

转码是 Jellyfin 对硬件要求最高的环节。没有硬件加速时，一颗 4 核 CPU 大概能同时转 1-2 路 1080p，4K 基本跑不动。

**NVIDIA GPU：**

```yaml
services:
  jellyfin:
    image: jellyfin/jellyfin:latest
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=compute,video,utility
```

**Intel QuickSync（推荐，功耗低，核显够用）：**

```bash
docker run -d \
  --name jellyfin \
  --device /dev/dri:/dev/dri \
  ...
```

配置完成后，进 Jellyfin 控制台 → 播放 → 硬件加速，选 VAAPI（Intel）或 NVENC（NVIDIA），勾选需要加速的编码格式。

---

## 初始化配置

### 首次设置

1. 访问 `http://your-server:8096`
2. 选择语言（支持简体中文）
3. 创建管理员账号
4. 添加媒体库——选类型（电影/剧集/音乐）和对应文件夹
5. 配置元数据刮削源（TMDB、TVDB 等）
6. 完成

### 媒体文件命名规范

Jellyfin 靠文件名识别媒体，命名不规范会导致刮削失败或识别错误。

| 媒体类型 | 推荐命名 | 刮削源 |
|---------|---------|--------|
| 电影 | `Movie Name (Year).ext` | TMDB |
| 剧集 | `Show/Season 01/Episode 01.ext` | TVDB |
| 音乐 | `Artist/Album/01 Track.ext` | MusicBrainz |
| 图片 | 按文件夹分组即可 | 无需刮削 |

### 国内网络环境下的元数据问题

Jellyfin 默认从 TMDB 和 TVDB 拉取海报、简介和评分，这些服务在国内访问不稳定。两种解决方式：

1. **配置 HTTP 代理**（推荐）：在 Docker 环境变量里加 `HTTP_PROXY=http://your-proxy:port`。
2. **申请自有 API Key**：在 TMDB 官网申请 API Key，填入 Jellyfin 控制台 → 媒体库 → 元数据管理器设置，绕过公共 Key 的速率限制。

---

## 核心功能

### 媒体库管理

添加媒体库后，Jellyfin 会自动扫描文件并刮削元数据：海报、背景图、剧情简介、演职员信息、评分（IMDB / 豆瓣等）、季/集信息。刮削结果写入本地 SQLite 或 PostgreSQL，不依赖云端缓存。

### 用户与权限

管理员可以为每个用户单独设置：

- 可访问的媒体库（比如不给小孩看大人的电影库）
- 内容分级限制（按 MPAA 或自定义分级）
- 同时播放数上限和最高清晰度限制
- 是否允许从外网访问

这套权限系统完全在本地运行，不需要像 Plex 那样把用户列表同步到云端。

### 实时转码矩阵

转码策略由两个因素决定：源文件格式和客户端能力。下面这张表覆盖了最常见的场景。

| 源文件 | 目标设备 | 转码动作 | 硬件需求 |
|--------|---------|---------|---------|
| 4K HDR (HEVC) | 手机 4G | 4K→1080p, HDR→SDR, HEVC→H.264 | 需要 GPU |
| 1080p H.264 | 浏览器 | 直接串流，不转码 | 无 |
| 原盘 ISO/BDMV | 电视 | 封装→MP4 | 低 |
| HEVC 10bit | 老旧电视 | HEVC→H.264, 10bit→8bit | 需要 GPU |

关键认知：**能不转码就不转码**。转码是不得已的手段——当客户端不支持源格式或带宽不够时才触发。如果你的媒体文件已经是 H.264 1080p，大部分设备都能直接播放，Jellyfin 几乎不消耗 CPU。

### 字幕

Jellyfin 通过插件支持自动下载字幕（OpenSubtitles 等），也支持手动上传。中文用户需要注意字体配置——默认字体可能不包含中文字形，导致字幕渲染为方块。在控制台 → 播放 → 字幕设置里指定一个中文字体路径即可。

---

## 插件生态

Jellyfin 的功能边界由插件定义。以下三个是使用频率最高的：

| 插件 | 解决的问题 |
|------|-----------|
| [OpenSubtitles](https://github.com/Julianlalrac/Jellyfin-plugin-OpenSubtitles) | 播放时自动匹配和下载字幕 |
| [MetaBuddy](https://github.com/oddstr13/jellyfin-metadatabuddy) | 批量修复元数据缺失或错误 |
| [Telegram Bot](https://github.com/nicknsy/jellyfin-telegram-notify) | 新内容入库时通过 Telegram 推送通知 |

插件通过 Jellyfin 控制台 → 插件 → 目录 安装，无需手动下载文件。

---

## 什么时候用 Jellyfin，什么时候不用

### 建议直接上 Jellyfin 的情况

- 有一台 NAS 或 24 小时开机的 Linux 服务器，媒体文件已经整理好了。
- 不想为硬件转码付订阅费（Plex Pass 和 Emby Premiere 都把这功能锁在付费墙后面）。
- 看重隐私——媒体库索引、播放记录、用户列表全部留在本地。
- 愿意花一点时间配置，换取完全的控制权。

### 建议先等等，或者选其他方案的情况

- 家里主力设备是 iPhone / iPad，且需要官方 App Store 里的原生客户端。Jellyfin 的 iOS 客户端是社区维护的（Swiftfin），功能不如 Plex 官方 App 完善。
- 需要开箱即用、不想折腾 Docker 和硬件转码配置。Plex 的安装体验和自动配置明显更友好。
- 依赖 TV Guide（电子节目单）功能做直播录制——国内源基本不可用。
- 4K HDR 转码需求大，但服务器没有 GPU 或核显。纯 CPU 转 4K 基本不可用，这种情况下即使用 Plex 也一样需要 GPU，但 Plex 的自动降级策略更成熟。

### 推荐搭建顺序

1. 先用 Docker 跑起来，不配置硬件加速，验证媒体库刮削和 Web 端播放正常。
2. 确认文件命名规范、元数据刮削成功率达标后，再接入 GPU 硬件加速。
3. 配置外网访问（推荐反向代理 + HTTPS，不要直接暴露 8096 端口）。
4. 最后按需安装字幕插件和通知插件。

---

## 参考链接

- GitHub：[github.com/jellyfin/jellyfin](https://github.com/jellyfin/jellyfin)
- 官方文档：[jellyfin.org/docs](https://jellyfin.org/docs)
- 下载：[jellyfin.org/downloads](https://jellyfin.org/downloads)
- 插件仓库：[repo.jellyfin.org/plugins](https://repo.jellyfin.org/plugins)
- 第三方 iOS 客户端 Swiftfin：[apps.apple.com](https://apps.apple.com/app/swiftfin/id1604098728)