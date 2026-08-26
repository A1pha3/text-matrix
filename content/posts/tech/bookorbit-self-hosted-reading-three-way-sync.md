---
title: "BookOrbit：一个自托管阅读平台的三端进度同步是怎么做成的"
date: 2026-08-27T03:45:00+08:00
slug: "bookorbit-self-hosted-reading-three-way-sync"
github_repo: "bookorbit/bookorbit"
source_key: "gh:bookorbit/bookorbit"
description: "BookOrbit 是 AGPLv3 的自托管电子书/有声书/漫画平台，核心卖点是网页阅读器、Kobo 设备与 KOReader 之间的双向进度和高亮同步，外加 14 家元数据源与 Docker 五分钟部署。本文拆解其同步架构与上手路径。"
draft: false
categories: ["技术笔记"]
tags: ["自托管", "电子书", "Kobo", "KOReader", "Docker"]
---

> **先给判断**：自托管书库这件事，Calibre 系工具已经做了十几年，BookOrbit 真正的差异点只有一个——**三端同步**。网页阅读器、Kobo 墨水屏、KOReader 之间的阅读进度和高亮双向流动，换设备续读不用人工对齐。其余能力（多库、元数据抓取、OPDS、多用户）是这一代自托管项目的标配，唯有三端同步是它做到位的护城河。评估它值不值得装，就看你的阅读是否横跨"手机/网页 + Kobo + KOReader"三个面。

## 1. 项目是什么

BookOrbit 是一个自托管的书库与阅读平台，覆盖电子书（EPUB / KEPUB / MOBI / AZW3 / AZW / FB2）、PDF、漫画（CBZ / CBR / CB7）和有声书（M4B / MP3 / M4A / OPUS / OGG / FLAC），全部内置网页阅读器，无需插件。

技术栈是 NestJS + Vue + PostgreSQL，Docker 单 compose 部署，AGPLv3 协议。2026 年 5 月初创建，8 月下旬仍在活跃提交，3.2k stars，有 live demo 可以在安装前直接试。

## 2. 系统地图：三层能力一张表

| 层 | 能力 | 备注 |
|----|------|------|
| 阅读与同步 | 三端同步（BookOrbit + Kobo + KOReader）、网页阅读器、标注高亮聚合 | 核心差异点，见下节 |
| 库管理 | 多库隔离、扫描规则、14 家元数据源、封面单独抓取、智能集合 | Google Books / Open Library / Amazon / Goodreads / Kobo / Hardcover / Audible / ComicVine 等 |
| 平台与分发 | 多用户 + OIDC SSO（Authentik / Keycloak / Authelia）、OPDS、Send-to-Kindle、Book Dock 落盘自动导入、Hardcover / Readwise / StoryGraph 外部同步 | NAS 场景考虑了 PUID/PGID |

外围还有阅读统计（热力图、连续天数、年度目标、50+ 成就）和从 Audiobookshelf、Calibre-Web Automated 迁移的专用指南——后者说明它清楚自己的用户从哪里来。

## 3. 三端同步：为什么难、它怎么解

跨设备同步进度的难点不在"传个百分比"，而在**三件事**：

1. **两端同时读**——进度合并策略谁赢？BookOrbit 的做法是进度、高亮（含删除）双向流动，合并细节官方文档有专门章节（文档站 bookorbit.app 覆盖 Kobo 同步专题）。
2. **标注格式异构**——网页阅读器、KOReader、Kobo 的高亮数据结构各不相同。BookOrbit 把三方标注汇入一个可检索的中枢，按颜色、样式、来源过滤，可导出 Markdown / CSV / JSON。
3. **Kobo 是半封闭设备**——KOReader 是开源软件，插件好办；Kobo 同步则依赖服务端配置级集成（官方文档站有专门章节），KOReader 则有专门的设备端插件。

KOReader 插件值得一说：不只是同步，还是设备上的目录浏览器——在 KOReader 里直接搜索、下载书库的书、管理状态和评分，不用离开设备。安装流程被压到五步：服务端下载插件 zip → 解压 → 拷进 `koreader/plugins/` → 重启 → 连接。插件预配置了服务器地址和凭据，设备上零手动输入。

另一个实用细节：Hardcover 的阅读历史可以**回拉**（pull back）来补全 BookOrbit 里的空白条目——同步是双向的，不是单纯外推。

## 4. 五分钟部署与最常见的坑

官方快速开始只需三步：

```bash
mkdir bookorbit && cd bookorbit
mkdir -p books data/app data/postgres
curl -fsSLo .env https://raw.githubusercontent.com/bookorbit/bookorbit/main/.env.example
curl -fsSLo docker-compose.yml https://raw.githubusercontent.com/bookorbit/bookorbit/main/docker-compose.yml
```

编辑 `.env` 填四个必填项：`APP_URL`（浏览器里访问的地址）、`BOOKS_HOST_PATH`（书文件所在目录）、`POSTGRES_PASSWORD`（`openssl rand -hex 24`）、`JWT_SECRET`（`openssl rand -hex 32`）、`SETUP_BOOTSTRAP_TOKEN`（一次性安装向导令牌，`openssl rand -hex 16`）。

然后 `docker compose up -d`，浏览器打开 `http://<ip>:3000` 用 bootstrap token 走完安装向导。

**最常见的坑**（README 明确点名）：在 NAS 或任何书目录属主不是 UID 1000 的机器上，必须把 `PUID` / `PGID` 设成实际属主的 uid/gid（用 `id -u` / `id -g` 查）。不改的话首次扫描几乎必然报权限错误。反代、外部数据库、完整环境变量参考见官方安装文档。

## 5. 适用边界与替代品对照

**选它，如果**：你的阅读横跨 Kobo / KOReader / 网页三端，进度和高亮不想手动对齐；家里有 NAS 或常驻服务器；在意数据主权（书库、进度、标注全在自控基础设施上）。

**不用勉强，如果**：只用一个阅读面——Calibre-Web 系（纯网页）或 Kobo 原生 + Dropbox 更轻；有声书是唯一需求——Audiobookshelf 更专注（BookOrbit 反而给 Audiobookshelf 用户写了迁移指南）；企业级多租户场景——它是单实例自托管定位。

**风险项**：项目 2026 年 5 月才创建，三个月 3.2k stars 增长很快，但处于快速迭代期，升级前看一眼 release notes；AGPLv3 意味着若你基于它做托管服务向外提供，衍生代码须开源。

## 6. 结论

BookOrbit 没有重新发明书库管理，它把赌注押在"多设备阅读者的进度同步"这个具体而真实的痛点上，并且做完整了：三端双向、标注聚合、外部服务回拉。Docker 部署路径干净，live demo 先试后装，迁移指南覆盖两大存量用户群。如果你是跨设备重度阅读者，这可能是目前自托管阵营里把"续读"这件事做得最省心的一份。

> 仓库：<https://github.com/bookorbit/bookorbit>（3.2k stars，TypeScript，AGPLv3，文档站 <https://bookorbit.app>）
