---
title: "Invidious：不依赖官方 API 的 YouTube 替代前端，如何在反爬时代活下来"
date: "2026-04-30T10:10:59+08:00"
lastmod: "2026-09-26T10:00:00+08:00"
slug: "invidious-open-source-youtube-alternative"
github_repo: "iv-org/invidious"
source_key: "gh:iv-org/invidious"
description: "Invidious 是用 Crystal 编写的开源 YouTube 替代前端，不使用官方 API，靠自研解析层获取数据。2024 年 YouTube 反爬封锁后，它把视频流拆给 TypeScript 写的 companion 进程，公共实例从数十个缩到 4 个，官方立场转向自托管。本文拆解它的双进程架构、缓存设计与真实部署成本。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "YouTube", "隐私保护", "自托管"]
---

Invidious 常被介绍成"无广告的 YouTube 前端"，这个说法低估了它的工程难度，也掩盖了它 2024 年之后的真实处境。它做的是一件更难的事：完全不用 Google 官方 API，直接解析 YouTube 的页面和内部接口来获取数据。2024 年 6 月 YouTube 上线"请登录以确认你不是机器人"的验证（[issue #4734](https://github.com/iv-org/invidious/issues/4734)）之后，这条路线的维护成本陡增——官方公共实例列表从几十个缩到 4 个，项目把视频流加载拆给了新的伴生进程 Invidious Companion，官方文档现在明确建议：能自托管，就别用公共实例。

看懂这些变化，比记住"它没有广告"重要得多。本文基于 2026-09-26 的仓库数据（master 分支 `c882300`）和官方文档，拆解它的架构、部署成本和适用边界。

---

## 项目速览

| 项目 | 信息 |
|------|------|
| 仓库 | [iv-org/invidious](https://github.com/iv-org/invidious) |
| Stars / Forks | 24,788 / 2,775（GitHub API，2026-09-26） |
| 语言 | Crystal（`crystal: ">= 1.14.1, < 2.0.0"`，见 shard.yml） |
| 许可证 | AGPL-3.0-only |
| Web 框架 | Kemal ~> 1.6.0 |
| 数据库 | PostgreSQL（强制，配置只接受 `postgres://` URI） |
| 最新 Release | v2.20260804.1（2026-08-05） |
| 官方文档 | https://docs.invidious.io |
| 创建时间 | 2018-02（项目已持续维护 8 年） |

用户能感知的功能：无需 Google 账号看视频、订阅频道、管理播放列表；页面无广告、无追踪；除播放器外不需要 JavaScript；内置简体中文在内的 63 种语言（locales/ 目录 63 个文件）；还支持纯音频模式（移动端可后台播放）、Reddit 评论聚合、订阅频道通知和自定义主页。

---

## 系统地图：一个主进程，一个伴生进程

2024 年之后部署 Invidious，跑的不只是一个程序。当前架构分两层：

| | Invidious 主程序 | Invidious Companion |
|------|------|------|
| 语言 | Crystal | TypeScript（基于 youtube.js） |
| 职责 | 页面渲染、搜索、订阅、评论、API、数据库 | 从 YouTube 服务器加载视频流 |
| 仓库 | iv-org/invidious | [iv-org/invidious-companion](https://github.com/iv-org/invidious-companion)（2024-09 创建） |
| 通信 | Invidious 把视频流请求代理给 companion；`invidious_companion_key`（16 字符）做认证 | 可横向部署多个，Invidious 每次取视频数据时随机挑一个 |

Companion 替代了此前的两个组件：`inv-sig-helper` 和 `youtube-trusted-session-generator`。官方安装文档把这次迁移标注为 "MIGRATION NEEDED (NEW)"——旧的签名辅助方案已经走不通，视频流交给专门进程处理后，主程序的解析层和流加载层解耦，companion 可以独立扩容。这套设计是应对 YouTube 反爬的直接产物：对抗逻辑变化最快的部分被隔离到一个小进程里，坏了先换它。

主程序内部还有 8 个后台任务（`src/invidious/jobs/`）：刷新频道与订阅 feed、拉取热门视频、投递通知、清理过期数据、刷新统计信息等。订阅更新不依赖登录 Google 账号，靠的就是这几个定时任务的持续轮询。

---

## 主要特点

### 无追踪、无广告、尽量无 JavaScript

Invidious 页面默认不需要 JavaScript 即可加载，播放等必须用到 JS 的功能也全部在本地执行，不向第三方上报用户行为。订阅数据存在实例数据库里，与 Google 账号无关。

### 数据导入导出

按官方 README 的口径，导入导出能力分三档，迁移前值得核对清楚：

- **导入订阅**：支持 YouTube（Google Takeout 导出）、NewPipe、FreeTube
- **导入观看历史**：只支持 YouTube 和 NewPipe
- **导出订阅**：可导出为 NewPipe 和 FreeTube 兼容格式

从 NewPipe 或 FreeTube 迁移过来，订阅关系可以无损搬走；但 FreeTube 的观看历史目前导不进来。

### RSS 订阅

每个频道都有 RSS feed，地址格式为 `https://<实例域名>/feed/channel/<channel_id>`。配合 RSS 阅读器可以完全不打开网页就追踪频道更新。Invidious 自己的订阅系统底层也是靠 feed 拉取实现的（`subscribe_to_feeds_job.cr`）。

### 内置 JSON API

Invidious 提供公开的 JSON API（文档：https://docs.invidious.io/api/ ），无需申请 API Key 即可获取视频信息、搜索结果、评论等数据。这个 API 的价值超出"给极客玩"：官方文档的 [Applications 页面](https://docs.invidious.io/applications/)列出一长串第三方客户端直接以它为后端——桌面端的 FreeTube、Apple 全平台的 Yattee、Roku 电视上的 Playlet、Apple Watch 上的 WatchTube、Kodi 插件等都依赖它。对开发者来说，这是不碰官方配额就能取 YouTube 数据的少数途径之一。

---

## 技术架构

### 为什么用 Crystal？

Crystal 语法接近 Ruby，但编译为原生二进制，没有虚拟机的运行时开销，类型在编译期检查。对一个要扛大量 HTTP 并发、又要频繁处理文本解析（视频页面、protobuf、字幕）的服务来说，这个组合兼顾了开发效率和性能。仓库 shard.yml 声明的主要依赖也印证了分工：

- **kemal**：轻量级 Web 框架，处理路由和 HTTP
- **pg**（crystal-pg）：PostgreSQL 驱动
- **protodec**：iv-org 自研的 protobuf 解析库，处理 YouTube 内部数据格式
- **sqlite3**：只在导入 NewPipe/FreeTube 备份时解析临时文件用（下文详述）
- **athena-negotiation**：HTTP 内容协商
- **http_proxy**：代理支持

### 目录结构

```text
src/invidious/
├── channels/          # 频道页与频道数据
├── comments/          # 评论解析（含 Reddit 评论）
├── database/          # 数据库访问层与迁移脚本
├── frontend/          # 前端工具（模板辅助函数）
├── helpers/           # i18n、日志等辅助函数
├── http_server/       # HTTP 服务器设置
├── jobs/              # 8 个后台定时任务
├── routes/            # 路由：watch、channels、feeds、search、
│                      #   login、playlists、preferences、api/ 等
├── search/            # 搜索查询解析
├── user/              # 用户数据与导入导出
├── videos/            # 视频数据结构与解析器
├── views/             # ECR HTML 模板（22 个页面模板 + 组件）
└── yt_backend/        # YouTube 数据解析核心（约 2,600 行）
```

`yt_backend/` 是整个项目最关键的部分：`extractors.cr`（1,218 行）负责从 YouTube 响应中提取视频元数据、字幕、评论结构，`youtube_api.cr`（711 行）封装对 YouTube 内部接口的调用，`connection_pool.cr` 管理到 YouTube 的连接池，`url_sanitizer.cr` 做流地址规范化。YouTube 每次改版都可能破坏这些解析逻辑——翻一下提交历史，"fix: xxx after YouTube change" 类型的提交反复出现，这是这条技术路线的固定维护成本。

### 数据库：只有 PostgreSQL，别被 shard 里的 sqlite3 误导

一个常见的误读是"Invidious 可以在 PostgreSQL 和 SQLite 之间按规模选择"。事实是：**主数据库只有 PostgreSQL**。配置文件 `config.example.yml` 中 `database_url` 只接受 `postgres://` URI；数据库访问层（`database/base.cr`）require 的是 `pg`。shard.yml 里确实有 sqlite3 依赖，但它在源码中只有一处用途：导入 NewPipe/FreeTube 备份文件时，用 `DB.open("sqlite3://" + tempfile.path)` 读取用户上传的临时 SQLite 文件（`user/imports.cr:306`）。它是解析工具，不是存储后端。

PostgreSQL 里的核心表包括 channels、channel_videos、videos、users、playlists、session_ids、nonces、annotations 等（`database/base.cr` 的完整性检查清单）。视频数据以 JSON 形式缓存在 videos 表，缓存策略在 `videos.cr` 的 `get_video` 里写得很清楚：

- 命中缓存且更新时间在 **10 分钟内**，直接返回（注释说明：YouTube 响应里的过期参数是 6 小时，Invidious 保守取 10 分钟）
- 超过 10 分钟、视频已首播、或缓存条目的 `SCHEMA_VERSION` 与当前代码不一致，就重新抓取并更新
- `SCHEMA_VERSION`（当前为 3）专门防止滚动升级时，新版代码读到旧版结构的缓存 JSON
- 带 `region` 参数的请求不写缓存，避免地区差异污染通用缓存

这套设计说明了一件事：Invidious 的数据库首先是**解析结果的缓存层**，其次才是用户数据存储。

### Companion：反爬时代的架构应对

YouTube 的反爬核心是 BotGuard 等客户端验证机制。2024 年 6 月起，大量 IP 收到"请登录以确认你不是机器人"的拦截（issue #4734），所有第三方 YouTube 客户端都受影响，Invidious 的公共实例首当其冲。项目先后用过 `youtube-trusted-session-generator` 生成可信会话、`inv-sig-helper` 处理签名，最终把这部分整体迁移为独立的 Invidious Companion 进程（该仓库创建于 2024 年 9 月），官方安装文档将迁移标注为必做项。

部署层面有几个值得注意的细节（来自 config.example.yml 注释）：

- `invidious_companion` 支持配置多个 URL，Invidious 每次要取视频数据时随机选一个，选中结果会随视频元数据缓存一段时间，缓存过期后重新挑选
- 简单部署下，Invidious 默认代理 companion 的流量；进阶场景可以让用户请求直达 companion，由反向代理分流
- 通信密钥 `invidious_companion_key` 必须是 16 字符随机字符串

这个设计的思路很务实：把"最容易被 YouTube 打击、需要频繁更换策略"的部分隔离出来，主程序保持稳定，companion 快速迭代甚至横向扩容。

### 无 API 依赖的代价

不使用官方 API 换来隐私和免账号访问，代价则由维护者承担：

1. **解析层永远在追赶**：YouTube 改版即失效。最近的 v2.20260804.0（2026-08）的主要工作仍是修复评论渲染——视频描述里的链接和时间戳、社区帖子的评论等。
2. **内容可达性受限**：需要登录或特殊授权的内容无法获取，字幕在热门公共实例上常因 Google 的 URL 限流而失效（官方 FAQ 明确提到）。
3. **持续的对抗压力**：YouTube 持续封锁第三方解析，项目需要不断调整会话与签名策略（companion 的存在本身就是证据）。

---

## 一次视频播放请求的完整路径

把上面的机制串起来，看一次 `GET /watch?v=xxx` 在系统里的流转：

1. **路由层**：`routes/watch.cr` 接到请求，校验视频 ID 格式，处理播放列表、region、续播等查询参数
2. **缓存判定**：调用 `get_video`，先查 PostgreSQL 的 videos 表。命中且 10 分钟内更新过 → 直接进入渲染；否则走抓取
3. **数据抓取**：`fetch_video` 经 `yt_backend/youtube_api.cr` 请求 YouTube 内部接口，`extractors.cr` 解析响应为视频对象，写回数据库。若 YouTube 拒绝请求，错误向上冒泡，用户看到 404/500 模板
4. **页面渲染**：视频对象连同用户订阅、通知状态一起交给 ECR 模板，输出无 JS 也可用的 HTML
5. **视频流加载**：浏览器随后请求视频流地址，这部分由 Invidious 代理转发给 Invidious Companion 处理——companion 负责与 YouTube 服务器完成流会话，用户侧拿到的是经过实例代理的流

一次普通的播放，穿过两个进程、一个缓存层和一整套解析器。理解了这条路径，就理解了为什么实例需要 PostgreSQL、需要 companion、需要足够的带宽——官方文档给公共实例的建议配置是 4GB 内存、2 vCPU、200 Mbps 带宽和 20TB 月流量起。

---

## 安装与快速开始

### 普通用户：公共实例还有，但选择很少

官方实例列表已迁至 [docs.invidious.io/instances](https://docs.invidious.io/instances/)（旧域名 instances.invidious.io 会重定向过去）。截至 2026-09，列表上只有 4 个 clearnet 实例（另有 Tor、I2P、Yggdrasil 入口），且官方给出两条硬性警告：

> 不在此列表上的公共实例一律视为不可信，使用风险自负。
> 如果可以，请在家自托管 Invidious，而不是使用公共实例。

热门公共实例普遍过载，字幕失效、限流是常态。多数实例无需注册即可观看，注册账号（保存订阅和偏好）视实例策略而定。给普通用户的现实建议是：偶尔看看，挑列表上的实例直接用；重度使用，参考下一节自建。

### 自托管：Docker Compose（官方推荐路径）

官方文档的 Docker 流程（https://docs.invidious.io/installation/ ）与很多旧教程不同，注意四点：

1. 镜像只发布在 [Quay](https://quay.io/repository/invidious/invidious)（`quay.io/invidious/invidious:latest`），不提供官方 Docker Hub 镜像——官方理由是 Quay 本身是开源软件
2. 需要生成两个密钥：Invidious 的 `HMAC_KEY` 和 companion 的 `invidious_companion_key`（各 16 字符，文档用 `pwgen 16 1` 生成）
3. 生产用的 docker-compose.yml 在安装文档里，需要挂载仓库的 `init-invidious-db.sh` 和 `config/sql/` 到 postgres 容器；仓库根目录自带的 docker-compose.yml 明确标注仅供开发
4. compose 里包含 invidious、invidious-db（postgres:14）两个服务，companion 按文档需单独配置或使用官方完整示例

官方给出的最低硬件参考：磁盘 20GB、空闲内存 2GB（定期重启前提下）；公共实例建议 60GB 磁盘、4GB 内存。

### 从源码构建

```bash
# 安装 Crystal（shard.yml 要求 >= 1.14.1, < 2.0.0）
curl -fsSL https://crystal-lang.org/install.sh | sudo bash

# 克隆并安装依赖
git clone https://github.com/iv-org/invidious.git
cd invidious
shards install

# 编译（编译期需要约 2.5GB 空闲内存，不足可用 swap）
crystal build --release src/invidious.cr -o invidious

# 初始化数据库 schema 并运行
# （数据库连接在 config/config.yml 中配置，仅支持 PostgreSQL）
./invidious
```

数据库 schema 由 `config/sql/` 中的迁移脚本初始化，运行时 `check_tables: true` 可自动补齐缺失的表和列。

---

## 适用边界

**适合自建或使用的人群：**

1. **隐私敏感的重度用户**：观看历史、订阅完全脱离 Google 账号，自托管后数据只在自己手里
2. **低配置设备用户**：无 JS 页面在老旧设备上远比 youtube.com 轻快；纯音频模式适合移动端听视频
3. **开发者**：免 Key 的 JSON API，或为 FreeTube、Yattee 这类客户端自建后端
4. **想摆脱算法推荐的人**：没有推荐流，只有搜索、订阅和趋势列表——对一些人来说是功能，对另一些人来说是缺陷

**不适合的场景：**

1. **需要登录才能看的内容**：会员专属、私享视频无法获取
2. **指望替代 YouTube 推荐算法**：它不提供推荐
3. **不想维护服务的人自建**：YouTube 反爬是持续性对抗，实例需要定期升级——官方列表甚至规定"落后最新版本超过一个月的实例将从列表移除"。装完就忘的玩法在这个项目上不成立

---

## 结语：一条难走但走得通的路

Invidious 证明了一件事：在 YouTube 全面收紧反爬的背景下，不依赖官方 API 的第三方前端依然可以存活，但代价是持续工程投入——解析层反复修补、视频流拆给独立进程、公共实例大批退场。它 2024 年后的演进——companion 架构、自托管导向——目标只有一个：在封锁下继续可用。

如果你决定上，推荐的顺序是：先用官方列表上的公共实例验证需求是否真实存在；确认后按官方安装文档用 Docker Compose 自建，配好 companion 和密钥；把频道订阅迁移进来（从 YouTube Takeout 或 NewPipe 导入）；最后视情况把 FreeTube、Yattee 等客户端接到自己的实例上。纯粹想省事、又没有隐私硬需求的用户，公共实例加一个浏览器重定向扩展就够了——但要知道，2026 年的"省事版 Invidious"体验上限，比封锁前低了不少。

---

## 参考链接

- 官方仓库：https://github.com/iv-org/invidious
- 官方文档：https://docs.invidious.io
- 安装指南（含生产用 docker-compose.yml）：https://docs.invidious.io/installation/
- 公共实例列表：https://docs.invidious.io/instances/
- API 文档：https://docs.invidious.io/api/
- Invidious Companion：https://github.com/iv-org/invidious-companion
- 第三方客户端与应用列表：https://docs.invidious.io/applications/
- 反爬封锁原始 issue：https://github.com/iv-org/invidious/issues/4734
- 官方主页：https://invidious.io
