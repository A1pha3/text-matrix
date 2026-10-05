---
title: "BookOrbit：一个自托管阅读平台的进度同步是怎么做成的"
date: 2026-08-27T03:45:00+08:00
lastmod: 2026-09-28T00:00:00+08:00
slug: "bookorbit-self-hosted-reading-three-way-sync"
github_repo: "bookorbit/bookorbit"
source_key: "gh:bookorbit/bookorbit"
description: "BookOrbit 是 AGPLv3 的自托管电子书/有声书/漫画平台，靠模拟 Kobo 官方同步服务器打通网页阅读器、Kobo、KOReader 的双向进度和高亮同步，v3.0 起加入官方 iPhone/Apple Watch 应用。本文拆解其同步架构与上手路径。"
draft: false
categories: ["技术笔记"]
tags: ["自托管", "电子书", "Kobo", "KOReader", "iPhone", "Docker"]
---

> **先给判断**：自托管书库这件事，Calibre 系工具已经做了十几年，BookOrbit 真正的差异点只有一个——**跨设备续读**。网页阅读器、Kobo 墨水屏、KOReader、官方 iPhone 应用之间的阅读进度和高亮双向流动，换设备不用人工对齐。其余能力（多库、元数据抓取、OPDS、多用户）是这一代自托管项目的标配，唯有把四个阅读面接进同一个进度轴是它做到位的护城河。评估它值不值得装，就看你的阅读是否横跨其中两个以上。

## 1. 项目是什么

BookOrbit 是一个自托管的书库与阅读平台，覆盖电子书（EPUB / KEPUB / MOBI / AZW3 / AZW / FB2）、PDF、漫画（CBZ / CBR / CB7）和有声书（M4B / MP3 / M4A / OPUS / OGG / FLAC），全部内置网页阅读器，无需插件。

技术栈是 NestJS（Fastify 驱动）+ Vue 3 + PostgreSQL，数据库镜像用 pgvector（外部自备数据库时要求 uuid-ossp、pg_trgm、vector 三个扩展可用），Docker 单 compose 部署，AGPLv3 协议。2026 年 5 月 9 日创建，9 月下旬仍在高频发版：v3.0.0（9 月 21 日，官方 iOS 应用）到 v3.1.0（9 月 25 日）只隔了四天。4,804 stars（2026-09-28 GitHub API 读数），有 live demo 可以在安装前直接试。

## 2. 系统地图：三层能力一张表

| 层 | 能力 | 备注 |
|----|------|------|
| 阅读与同步 | 四面同步（BookOrbit + Kobo + KOReader + iPhone/Apple Watch）、网页阅读器、标注聚合、EPUB 3 跟读、自带 TTS | 核心差异点，见下两节 |
| 库管理 | 多库隔离、扫描规则、14 家元数据源、封面单独抓取、智能集合（Smart Scopes：规则保存的动态过滤器） | 元数据：Google Books / Open Library / Amazon / Goodreads / Kobo / Hardcover / Audible / Audnexus / Libro.fm / iTunes，加 ComicVine（漫画）、RanobeDB（轻小说）、Aladin（韩文）、Lubimyczytać（波兰文）；封面另走 iTunes / DuckDuckGo / AudiobookCovers |
| 平台与分发 | 多用户 + OIDC SSO（Authentik / Keycloak / Authelia）、OPDS、邮件 Send-to-Kindle、Book Dock 落盘自动导入、求书系统（Prowlarr + SABnzbd）、Hardcover / Readwise / StoryGraph 外部同步、Crowdin 多语言 | NAS 场景考虑了 PUID/PGID；另有第三方 Zenith 托管，不想碰 Docker 可以直接买 |

外围还有阅读统计（热力图、连续天数、年度目标、五类 50+ 成就，以及按真实会话历史生成阅读风格画像的 Reading DNA）和官方迁移向导——它清楚自己的用户从哪里来，这件事第 6 节展开。

## 3. 跨设备同步：为什么难、它怎么解

跨设备同步进度的难点不在"传个百分比"，而在**三件事**：

**一是两端同时读，进度合并谁说了算。** 官方文档在 Three-Way Progress 一节给出的口径是：防止旧设备状态覆盖较新的状态，同步按变更增量分页下发。更细粒度的冲突规则文档没有展开——这是诚实的地方，也是潜在用户需要知道边界的地方：它保证"不会拿旧状态盖新状态"，没有承诺一套可配置的合并策略。

**二是标注格式异构。** 网页阅读器、KOReader、Kobo 的高亮数据结构各不相同。BookOrbit 把三方标注汇入一个可检索的中枢，按颜色、样式、来源过滤，可导出 Markdown / CSV / JSON。Kobo 侧还有个格式陷阱：精确到句子的同步依赖 KEPUB 的 KoboSpan 定位，普通 EPUB 只能做到百分比级。服务端用 kepubify 缓存生成 `.kepub.epub`，转换失败回退原 EPUB——想在 Kobo 上句子级续读，书就得是 EPUB（服务端自动转 KEPUB），MOBI 之类享受不到这层精度。

**三是 Kobo 是半封闭设备，没有"填服务器地址"的设置项。** BookOrbit 的解法是把自己伪装成 Kobo 官方同步服务器：配对设备后，服务端生成一个含设备令牌的私有 URL，用户 USB 连上 Kobo，手工编辑 `.kobo/Kobo/Kobo eReader.conf`，把 `[OneStoreServices]` 段的 `api_endpoint` 指到这个 URL。之后 Kobo 把同步请求发给 BookOrbit，它处理不了的请求（商店类）再转发回 Kobo 官方服务。设备令牌就是身份凭据，文档提醒要当密码保管，泄露后吊销设备重新配对。同步哪些书由集合驱动：集合打开 "Sync to Kobo" 开关才下发，且主文件必须是 EPUB。

KOReader 这端简单得多——它本就是开源软件，装插件即可，而且插件不只是同步：还是设备上的目录浏览器，在 KOReader 里直接搜索、下载书库的书、管理状态和评分，不用离开设备。安装五步：网页端 **Settings > KOReader** 创建凭据并 **Download Plugin** → 解压 zip → 拷进 `koreader/plugins/` → 重启 KOReader 打开一本书 → **Tools > BookOrbit Sync** 连接。插件 zip 里预配置了服务器地址和凭据，设备上零手动输入。

外部服务也是双向的：Hardcover 的阅读历史可以**回拉**（pull back），用来补全 BookOrbit 里的空白条目；状态、进度、评分按可配置的触发器推送出去；Readwise 收高亮和笔记，StoryGraph 收状态和进度。

v3.0.0 把这条进度轴又延长了两端：iPhone / Apple Watch 官方应用（App Store 上架，要求服务端 v3.0.0+、iOS 26+，Watch 功能需 watchOS 26+）。离线优先，有声书可以单独下到 Watch 上，跑步时手机留家里，回来再对账进度。更值得注意的是**朗读进度同步**：有声书、电子书、网页阅读器、Kobo、KOReader 可以停在同一个位置——按书在详情页开关，时长对不上的书会明说不可用。

## 4. Read-along 与 TTS：听读合一的两条路

v3.0.0 还带了两条"书自己读给你听"的路子，面向的场景不同：

**Read-along 走文件本身。** 带 EPUB 3 media overlays 的书（比如 Storyteller 工具产出的），阅读器直接播放书内嵌的真实朗读音频，正在读的句子高亮，音频流自 EPUB 文件本身，合上书下次从精确的句子恢复。不需要服务器做任何语音合成——朗读是作者预录在文件里的。

**TTS 走服务器合成。** 管理员在设置里接任何 OpenAI 兼容的语音合成服务——比如本地跑一个 Kokoro 容器（官方 compose 提供了 `--profile tts` 的可选服务，内网 `http://kokoro:8880/v1`，不暴露端口）——测试连接、列出声音、筛选哪些开放给读者、排序兜底；官方 iPhone 应用也支持把书读出来。

一条路吃制作者的录音，一条路吃自己的算力，没有把两者搅在一起讲成"AI 朗读"——这个区分做得干净。

## 5. 五分钟部署与最常见的坑

官方快速开始只需三步：

```bash
mkdir bookorbit && cd bookorbit
mkdir -p books data/app data/postgres
curl -fsSLo .env https://raw.githubusercontent.com/bookorbit/bookorbit/main/.env.example
curl -fsSLo docker-compose.yml https://raw.githubusercontent.com/bookorbit/bookorbit/main/docker-compose.yml
```

编辑 `.env` 填五个必填项：`APP_URL`（浏览器里访问的地址）、`BOOKS_HOST_PATH`（书文件所在目录）、`POSTGRES_PASSWORD`（`openssl rand -hex 24`）、`JWT_SECRET`（`openssl rand -hex 32`）、`SETUP_BOOTSTRAP_TOKEN`（一次性安装向导令牌，`openssl rand -hex 16`）。

然后 `docker compose up -d`，浏览器打开 `http://<ip>:3000` 用 bootstrap token 走完安装向导。

**最常见的坑**（README 原话）：在 NAS 或任何书目录属主不是 UID 1000 的机器上，把 `PUID` / `PGID` 设成实际属主的 uid/gid（用 `id -u` / `id -g` 查）——改错这个是首次扫描权限错误的最常见原因。Kobo 同步还要过反代这一关：文档专门给了 Nginx 的 `X-Forwarded-*` 转发头和大请求头缓冲配置，挂在 Cloudflare Access 这类认证代理后面的要给若干路径开豁免。

compose 文件本身有两处值得留意。安全上是认真做的：应用容器 `read_only: true`、`cap_drop: ALL` 后按需加回五个文件属主能力、`no-new-privileges`，PostgreSQL 有健康检查做启动依赖。可扩展性上有明确边界：`NODE_MAX_OLD_SPACE_SIZE` 注释写了 25 万册以上要调堆；敏感配置全部支持 `_FILE` 挂载文件注入；已有的外部 PostgreSQL 只要把三个扩展备齐就能接。

## 6. 迁移与替代品对照

官方迁移向导覆盖四个来源：Booklore、Grimmory、Audiobookshelf、Calibre-Web Automated（各自标了已测试版本）。迁移是叠加模式：先把书扫描进 BookOrbit，再按 ISBN → ASIN → 文件哈希 → 路径映射 → 标题+作者 的顺序匹配补数据，跑之前可以先 dry run。注意标注（高亮）只有 Booklore 和 Grimmory 能带过来，Audiobookshelf 和 Calibre-Web Automated 都不迁移标注——听书进度和书签能迁，划线迁不过去。

**选它，如果**：你的阅读横跨 Kobo / KOReader / 网页 / iPhone 中两个以上，进度和高亮不想手动对齐；家里有 NAS 或常驻服务器；在意数据主权（书库、进度、标注全在自控基础设施上）。

**不用勉强，如果**：只用一个阅读面——Calibre-Web 系（纯网页）或 Kobo 原生 + Dropbox 更轻；有声书是唯一需求——Audiobookshelf 更专注（BookOrbit 反而给 Audiobookshelf 用户写了迁移指南）；已在用 Booklore 或 Grimmory 且依赖它们的标注库——先看第 6 节开头那段再决定。

**风险项**：项目 2026 年 5 月才创建，五个月 4.8k stars，版本节奏极快（v2.8 到 v3.1 用了四周），升级前看一眼 release notes；AGPLv3 意味着若你基于它做托管服务向外提供，衍生代码须开源。

## 7. 结论

BookOrbit 没有重新发明书库管理，它把赌注押在"多设备阅读者的进度同步"这个具体而真实的痛点上，并且一路做深：三端双向扩到四面，标注聚合，外部服务回拉，连有声书和电子书的朗读位置都拉到了同一条轴上。Docker 部署路径干净，live demo 先试后装，迁移向导覆盖四个存量系统。如果你是跨设备重度阅读者，这可能是目前自托管阵营里把"续读"这件事做得最省心的一份。

> 仓库：<https://github.com/bookorbit/bookorbit>（4.8k stars，TypeScript，AGPLv3，文档站 <https://bookorbit.app>）

---

## 参考来源与口径说明

- 版本锚点：v3.1.0（2026-09-25 发布）；stars 4,804、forks 316 为 2026-09-28 GitHub API 读数。
- 功能与格式清单核对自仓库 README（main 分支，2026-09-28）；技术栈核对自 `server/package.json`（@nestjs/platform-fastify、pg、drizzle-orm）与 `client/package.json`（Vue 3.5）；部署细节核对自 `.env.example` 与 `docker-compose.yml`（kokoro TTS 为 `--profile tts` 可选服务，PostgreSQL 镜像 pgvector/pgvector:pg18）。
- Kobo 同步原理、KEPUB/KoboSpan 边界、反代配置、合并策略口径核对自文档站 bookorbit.app/kobo/；迁移向导的范围与限制核对自 bookorbit.app/migration/。
- iOS 应用要求（服务端 v3.0.0+、iOS 26+、watchOS 26+）核对自 README 与 App Store 条目。
