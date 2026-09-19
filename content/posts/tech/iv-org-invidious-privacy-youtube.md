---
title: "Invidious：去广告、可自托管的 YouTube 前端"
date: 2026-08-02T02:59:48+08:00
slug: "iv-org-invidious-privacy-youtube"
github_repo: "iv-org/invidious"
source_key: "gh:iv-org/invidious"
description: "Invidious（iv-org/invidious）是 AGPL-3.0 许可的 YouTube 替代前端，用 Crystal 编写，不使用官方 API，无广告、无追踪、订阅独立于 Google。本文梳理它七年与 YouTube 对抗的脉络、一次播放请求的完整流转、生产环境的自托管步骤，以及它与 FreeTube、Piped 的真实关系。"
draft: false
categories: ["技术笔记"]
tags: ["隐私", "YouTube", "自托管", "AGPL", "Crystal"]
---

[Invidious](https://github.com/iv-org/invidious) 是用 Crystal 写成的 YouTube 替代前端，AGPL-3.0 许可，约 24.5k stars（2026 年 9 月）。它不抓视频、不破解 DRM，自己渲染页面和播放器，把广告、追踪和推荐算法挡在外面。理解它的关键在于一点：这不是一个"装完就完事"的工具，而是一场从 2018 年持续至今的对抗性工程——YouTube 每收紧一次接口，项目就要找到新的绕行办法。2023 年 6 月 YouTube 发出限期七天的律师函，开发者选择无视，项目活了下来，但"能正常播放"从此需要持续投入来维持。

## 它是什么，不是什么

Invidious 的 README 写明它 "Does not use official YouTube APIs"。它解析的是 YouTube 网站的内部接口，把返回的视频流和元数据装进自己的页面。这带来几个直接推论：

- 页面上没有 YouTube 的脚本和播放器，广告层、追踪像素、推荐算法都进不来；
- 视频流最终仍来自 YouTube 的服务器，地理限制和版权屏蔽原样保留；
- 因为绕开了官方条款，实例 IP 会被 YouTube 周期性封锁，稳定性是运维问题而不是部署问题。

订阅、观看历史这些数据存在你自己的实例（或你选择的公共实例）里，与 Google 账号无关。README 把这条特性写作 "Subscriptions independent from Google"，并支持从 YouTube（经 Google Takeout 导出的 CSV）、NewPipe 和 FreeTube 导入订阅。

## 七年对抗的脉络

- **2018 年 8 月**：Omar Roth 创建项目，从一开始就用 Crystal 编写。
- **2020 年**：Roth 宣布退出并关闭主实例 invidio.us，社区组织 iv-org 接管开发，项目没有停。
- **2023 年 6 月**：YouTube 向项目发出要求七天内下线的律师函。开发者公开拒绝，理由是 Invidious 不使用官方 API、只是抓取网站，随后继续开发。
- **律师函之后**：对抗常态化。官方文档专门写了 IPv6 地址轮换来规避 YouTube 对实例 IP 的封锁；生产部署配置里也新增了 invidious-companion 服务，与主程序一同运行，详细文档放在 [invidious-companion 的 GitHub wiki](https://github.com/iv-org/invidious-companion/wiki)。

这四段脉络解释了 Invidious 与普通自托管应用最大的不同：普通应用部署完就稳定了，Invidious 部署完，战争才刚开始。

## 核心能力

以下特性均来自 README：

| 能力 | 说明 |
|------|------|
| 无广告、无追踪 | 页面不加载任何 YouTube 脚本 |
| 不依赖 JavaScript | 关闭 JS 也能浏览和观看 |
| 音频模式 | 只拉音频流，移动端支持后台播放，省流量也省电 |
| 订阅独立于 Google | 订阅列表存在实例数据库中，可随时导出或删除 |
| 通知 | 已订阅频道有新视频时推送 |
| Reddit 评论 | 评论区可切换为 Reddit 来源 |
| 明暗主题、自定义主页、多语言 | 翻译由 Weblate 社区维护 |

画质方面，Invidious 提供 DASH 自适应流与传统 itag 分段两种形态。官方 FAQ 提醒：YouTube 经常对 hd720、medium、small 这几档发送损坏的视频数据，遇到花屏先刷新几次或切换到 DASH，这是 YouTube 侧的问题，不是实例坏了。

## 一次播放请求的完整流转

把抽象架构落到一个动作上：你在自托管实例上点开一个视频，发生了什么。

1. 浏览器向你的实例请求视频页，页面和播放器由 Invidious 渲染，期间没有任何请求发往 YouTube 的前端。
2. Invidious 后端向 YouTube 的内部接口发起抓取，拿回视频元数据、可用格式（DASH 与 itag 分段）和字幕。
3. 播放器加载视频流。默认情况下流直接从 YouTube 服务器到你本地；如果你的 IP 容易被 YouTube 盯上，可以在 URL 加 `&local=1`（或在偏好里开启 Proxy videos），让流量经实例中转，代价是实例带宽。
4. 评论区加载，来源可以是 YouTube 或 Reddit。

每一步都有已知的失败模式，排查顺序也固定：

- **视频完全无法加载**：音乐视频最常见，多半是 YouTube 屏蔽了视频流，开启代理（`local=1`）通常能解决。
- **画质档位花屏**：hd720/medium/small 的已知问题，刷新 5-7 次或切 DASH。
- **字幕失效**：热门公共实例的常见病，源于 Google 对字幕 URL 的限速，换冷门实例或自托管。
- **整个实例时好时坏**：实例 IP 被 YouTube 封了，管理员需要配置 IPv6 轮换。

## 自托管：按生产文档来

先说一个坑：仓库根目录那份 docker-compose.yml 开头就标注了 "made for development purposes"——它从本地源码构建镜像，直接拿去跑，等于自己编译了一遍。生产部署按官方安装文档走：

1. 克隆仓库（安装文档要求挂载 `config/sql` 目录和数据库初始化脚本到 PostgreSQL 容器）；
2. 用 `pwgen 16 1` 生成两个密钥：HMAC_KEY 和 invidious_companion_key，文档特别强调两者不要复用同一个值；
3. 编辑 docker-compose.yml，填入密钥，镜像固定为 `quay.io/invidious/invidious:latest`（Invidious 的镜像只发布在 Quay）、`quay.io/invidious/invidious-companion:latest` 和 `postgres:14` 三个服务；
4. `docker compose up -d` 启动，健康检查打的是 `/api/v1/stats`。

compose 默认把端口绑在 `127.0.0.1:3000`，即只允许本机访问——这是给反向代理准备的默认值。想直接访问就把映射改成 `3000:3000`。启动后浏览器打开 `http://localhost:3000`，就是一个干净的 YouTube。

两点限制提前知道：官方不提供 .deb/.rpm 包，只有 Docker 和源码编译两条路；反向代理部署时需要正确设置 `https_only`、`domain`、`external_port` 三项配置，用 IP 直连时 `domain` 留空，否则登录和偏好保存会莫名失效（cookie 作用域问题，FAQ 里排障频率最高的一条）。

不想自己运维的话，社区实例列表在 [instances.invidious.io](https://instances.invidious.io/)。个人轻度使用通常够用，但对稳定性敏感的用法（比如给第三方客户端当后端）还是自托管。

## API 与生态位

实例自带一套公开的 REST API，base path 是 `/api/v1/`，常用的几个端点：

```bash
# 视频详情：格式列表、字幕、推荐视频
curl https://<your-instance>/api/v1/videos/<video-id>

# 搜索
curl "https://<your-instance>/api/v1/search?q=...&type=video"

# 实例状态（也是部署的健康检查端点）
curl https://<your-instance>/api/v1/stats
```

此外还有 comments、captions、trending、playlists 等端点；订阅类端点归入认证接口，需要登录凭据。完整文档在 [docs.invidious.io](https://docs.invidious.io/) 的 API 章节。

官方文档维护着一个[使用 Invidious 的应用列表](https://docs.invidious.io/applications/)，几个代表性项目：

- **FreeTube**：Electron 桌面客户端。注意，它的默认数据源是自带的提取器（Local API），Invidious 只是两个可选后端之一——网上大量教程说"FreeTube 默认走 Invidious"，这是过时信息。
- **Yattee**：iOS、iPadOS、macOS、Apple TV 上的原生播放器，支持把 Invidious 实例当后端，内置 SponsorBlock。
- **Materialious**：Material Design 风格的现代化界面；**Playlet** 跑在 Roku 电视上；**WatchTube** 跑在 Apple Watch 上，甚至还有 Apple II 客户端 IInvidious。
- **UntrackMe**：Android 上把 YouTube 链接重写为 Invidious 链接。

**Piped 容易被误放进这个列表，但它不在官方名单里。** Piped 是另一个独立的 YouTube 替代前端（约 10.3k stars），数据抓取用的是 NewPipeExtractor，与 Invidious 的 API 没有依赖关系。两者是平行的技术路线，解决同一个问题。如果你看到"某客户端基于 Piped API"和"基于 Invidious API"的讨论，那是两套不同的后端。

## 适用边界与采用建议

**适合**：在意观看历史被 Google 收走的人；想把 YouTube 当纯视频源、不被首页推荐绑架的人；给家庭或小团队搭一个统一视频入口；做第三方客户端时找一条稳定的数据管道。

**不适合**：依赖直播打赏、Super Chat、频道会员这些变现链路的创作者场景；想借它绕开地区版权限制（做不到，流还是 YouTube 的）；把公共实例当生产 SaaS 依赖——2023 年以来的对抗强度决定了公共实例的可用性随时波动。

采用顺序上，建议先拿公共实例用一周，确认这类使用方式适合自己；然后自托管一个只给自己用的实例，把浏览器默认入口切过去；移动端配上 Yattee 或 FreeTube 指向你的实例。三步走完，YouTube 生态里属于 Google 的部分就只剩视频流本身了。

这个项目真正的价值不在"无广告"这个功能点——广告拦截插件也能做到——而在它验证了另一种可能：观看行为可以不经过推荐算法、不留下追踪数据。代价同样清楚：这是一场军备竞赛，YouTube 不会罢手，项目的每一次"能用"都是维护者刚刚赢下的一局。
