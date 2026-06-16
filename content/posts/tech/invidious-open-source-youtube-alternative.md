---
title: "Invidious：无需 Google 账号的开源 YouTube 替代前端"
date: "2026-04-30T10:10:59+08:00"
slug: "invidious-open-source-youtube-alternative"
description: "Invidious 是一个用 Crystal 语言编写的开源 YouTube 替代前端，通过直接解析 YouTube 页面获取数据而不依赖 Google API，实现了无追踪、无广告的观看体验，支持 RSS 订阅、多语言界面和 JSON API。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "YouTube", "隐私保护", "Crystal", "Web"]
---

说起在浏览器里看 YouTube 视频，大多数人的第一反应是打开 youtube.com，登录 Google 账号，接受所有 cookie，然后忍受贴片广告和推荐算法。如果不想被 Google 追踪，又不想装浏览器插件，有什么开源方案？

Invidious（https://github.com/iv-org/invidious）就是其中之一。这是一个用 Crystal 语言编写的 YouTube 替代前端，核心理念是：**不依赖 Google 官方 API，不追踪用户数据，不展示广告**。用户无需 Google 账号即可观看视频、订阅频道、管理播放列表。

---

## 项目概览

| 项目 | 信息 |
|------|------|
| 仓库 | iv-org/invidious |
| 语言 | Crystal（crystal: >= 1.10.0, < 2.0.0） |
| 许可证 | AGPL-3.0-only |
| 框架 | Kemal |
| 数据库 | PostgreSQL + SQLite |
| 最新 Release | v2.20260207.0 |
| 最新提交 | afea61bb8f1aa74f107f82cb69b999a235c5858f（2026-04-28） |
| 官方文档 | https://docs.invidious.io |

Invidious 是一个完整的、去 Google 化的视频平台前端，远不止"去掉广告的 YouTube"。用户可以搜索内容、浏览频道、查看趋势视频、管理订阅导入/导出——全程无需与 Google 服务交互。

---

## 主要特点

### 无追踪、无广告、无 JavaScript

Invidious 页面默认不需要 JavaScript 即可加载。对于确实需要 JavaScript 的功能（如视频播放），也完全在本地执行，不会上传用户行为数据到任何第三方服务器。官方维护了一个公共实例列表（https://instances.invidious.io），用户可以自由选择信任的节点。

### 多主题与国际化

内置 Light/Dark 主题切换，支持数十种语言界面（locales/ 目录下有 60+ 语言文件）。对于中文用户，直接在设置中选择简体中文即可。

### 数据导入导出

Invidious 支持从以下来源导入订阅和播放记录：
- YouTube（需要导出数据）
- NewPipe
- FreeTube

导出格式同样兼容 NewPipe 和 FreeTube，方便在不同工具之间迁移。对于已经使用这些工具的用户来说，切换成本几乎为零。

### RSS 订阅

每个频道都提供 RSS feed，地址格式为 `https://instance.invidious.io/feed/channel/{channel_id}`。用户可以直接在 RSS 阅读器里追踪更新，无需打开浏览器。

### 内置 Developer API

Invidious 提供了公开的 JSON API，允许开发者获取视频信息、搜索结果、评论等数据，无需申请 API Key。文档地址：https://docs.invidious.io/api/

---

## 技术架构

### 为什么用 Crystal？

Crystal 是一门编译型语言，语法接近 Ruby，但编译产物是原生二进制文件，性能和内存效率都很高。对于一个需要处理大量 HTTP 请求和并发连接的视频平台来说，Crystal 的类型安全和低运行时开销是有吸引力的选择。

从 shard.yml 中可以看到主要依赖：
- **kemal**: 轻量级 Crystal Web 框架
- **crystal-pg**: PostgreSQL 驱动
- **crystal-sqlite3**: SQLite 驱动
- **protodec**: protobuf 解析工具（用于处理 YouTube 内部数据格式）

### 目录结构

```
src/invidious/
├── channels/          # 频道相关逻辑
├── comments/          # 评论解析
├── database/         # 数据库操作
├── helpers/          # 辅助函数（i18n、日志、工具函数）
├── http_server/       # HTTP 服务器相关
├── jobs/             # 后台任务（订阅更新等）
├── routes/            # 路由处理
│   ├── api/          # API 路由
│   ├── watch.cr      # 视频播放页
│   ├── channels.cr    # 频道页
│   ├── feeds.cr      # RSS feed
│   └── ...
├── videos/           # 视频数据处理
├── views/            # HTML 模板
├── yt_backend/       # YouTube 数据解析核心
│   ├── extractors.cr # 页面解析提取器
│   ├── youtube_api.cr # YouTube API 调用封装
│   └── url_sanitizer.cr # URL 规范化
└── user/             # 用户管理
```

`yt_backend/` 是整个项目最关键的部分。由于不依赖 YouTube 官方 API，Invidious 需要自己解析 YouTube 页面和响应数据。这包括提取视频元数据、解析 DASH manifest（如果可用）、获取字幕、解析评论结构等。YouTube 每次改版都可能影响这些解析逻辑，这也是 Invidious 维护工作量最大的地方之一。

### 数据库设计

Invidious 使用两层数据库策略：
- **PostgreSQL**：存储用户数据、订阅关系、播放列表
- **SQLite**：存储视频缓存、观看历史等本地数据

这种设计让实例管理员可以根据规模选择轻量（SQLite）或高并发（PostgreSQL）方案。

### 无 API 依赖的代价

YouTube 官方提供了稳定的公开 API，但 Invidious 选择了一条更难的路：不使用任何 Google 官方服务，代价如下：

1. **维护成本高**：YouTube 每次改版都可能破坏解析逻辑，需要快速响应
2. **功能受限**：部分需要登录才能获取的内容（如地区限制视频的完整描述）无法获取
3. **版权风险**：YouTube 一直在试图封禁第三方解析行为

作为交换，用户获得了真正的隐私保护和无需账号的访问体验。近期 v2.20260207.0 版本的主要工作之一就是修复 livestream 导航和 playlist 解析，正是因为 YouTube 近期对这部分做了改动。

---

## 安装与快速开始

### 方式一：使用公共实例（推荐普通用户）

无需安装，直接访问 https://instances.invidious.io 选择一个公共实例即可。大多数实例无需注册即可观看视频，部分实例支持创建账号以保存订阅和偏好设置。

### 方式二：Docker 部署（推荐自建用户）

```bash
# 克隆仓库
git clone https://github.com/iv-org/invidious.git
cd invidious

# 复制并编辑配置
cp config/config.example.yml config/config.yml
# 编辑 config/config.yml，填写数据库配置等必要项

# 使用 Docker Compose 启动
docker-compose up -d
```

### 方式三：从源码构建

```bash
# 安装 Crystal（需要 >= 1.10.0）
curl -fsSL https://crystal-lang.org/install.sh | sudo bash

# 安装依赖
shards install

# 编译
crystal build --release src/invidious.cr -o invidious

# 运行
./invidious
```

默认配置下 Invidious 使用 SQLite，如果需要更高性能，可以在 config/config.yml 中切换为 PostgreSQL（也可以直接使用 docker-compose.yml 中预设的 PostgreSQL）。

---

## 适用场景

### 适合使用 Invidious 的场景

1. **隐私敏感用户**：不想被 Google 追踪观看历史、订阅行为
2. **低配置设备**：Invidious 页面比 YouTube 官方更轻量，在老旧设备上加载更快
3. **开发者**：需要批量获取 YouTube 数据但不想申请官方 API
4. **网络受限环境**：部分地区访问 YouTube 不稳定，通过 Invidious 实例可能更顺畅

### 不适合的场景

1. **需要登录才能观看的内容**：如会员专属视频、私享内容
2. **需要完整 YouTube 算法推荐**：Invidious 没有推荐算法，只有搜索和订阅
3. **部分受地区限制的视频**：Invidious 同样受这些限制

---

## 总结

Invidious 用 Crystal 语言实现了一个功能完整的 YouTube 替代前端，在不依赖 Google 服务的情况下提供了还算完整的观看体验——这在"去大公司化"方向上是一个可跑通的实践。

如果你对隐私有要求，或者只是想找一个更轻量的方式看 YouTube 视频，公共 Invidious 实例已经足够好用。如果你是开发者，想研究如何解析 YouTube 数据，或者想自建私有实例，那么这个仓库的源码值得一看。

官方文档（https://docs.invidious.io）提供了更详细的部署和开发指南，包括 Kubernetes 部署配置、Docker 进阶用法、API 文档等，建议有需要的读者直接查阅原文。

---

## 参考链接

- 官方仓库：https://github.com/iv-org/invidious
- 官方文档：https://docs.invidious.io
- 官方实例列表：https://instances.invidious.io
- 官方主页：https://invidious.io
- 隐私浏览器重定向扩展（配合 Invidious 使用）：https://github.com/SimonBrazell/privacy-redirect
