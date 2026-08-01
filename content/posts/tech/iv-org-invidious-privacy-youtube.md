---
title: "Invidious：去广告、可自托管的 YouTube 前端"
date: 2026-08-02T02:59:48+08:00
slug: "iv-org-invidious-privacy-youtube"
description: "Invidious（iv-org/invidious）是 AGPL-3.0 许可的 YouTube 替代前端，无广告、无追踪、无推荐算法，可自托管；同时提供 API、订阅、音频模式与多语言界面，是隐私优先观看 YouTube 的事实标准。"
draft: false
categories: ["技术笔记"]
tags: ["隐私", "YouTube", "自托管", "AGPL", "RSS"]
---

## 一句话判断

`iv-org/invidious` 是 YouTube 的**前端替代实现**——不抓视频、不破解 DRM，只通过 YouTube 公开接口把视频页面、订阅、搜索、字幕、音频流重新渲染成无广告、无追踪、无推荐算法的版本。任何人都可以自托管一个实例，整个项目采用 AGPL-3.0。

## 为什么需要 Invidious

YouTube 在过去几年陆续加上了：

- 多层广告（前置/中插/可跳片尾）
- 强制登录才能看部分视频
- 基于观看历史的激进推荐
- 与 Google 账号绑定的追踪

Invidious 提供一个**完全可逆的观看体验**：登录可选、无广告、无追踪、推荐可关、可纯音频、可导出 RSS。

## 核心能力

| 能力 | 描述 |
|------|------|
| 无广告播放 | 通过 embed URL 渲染，绕过 YouTube 广告层 |
| 无追踪 | 不加载 Google Analytics/YouTube Pixel；默认不记录 IP |
| 可关推荐 | 主页 / 侧栏推荐可一键关 |
| 订阅 | 用户系统可选（本地 cookie 或完整账号）；订阅源可导出 RSS |
| 音频模式 | 直接拉音频流，省带宽省电池 |
| API | `/api/v1/...` 公开端点，便于第三方客户端 |
| 多语言界面 | 翻译覆盖主要语言 |
| 多种播放器 | dash、itag、传统 mp4 三种回退 |

## 自托管 vs 公共实例

仓库 README 强烈鼓励自托管，并提供 Docker、Crystal 源码 build、systemd unit 等多种部署路径。公共实例由社区维护，需要警惕运维稳定性，但通常足够个人使用。

最小化自托管：

```bash
# Docker 方式（仓库提供 docker-compose.yml）
docker compose up -d
```

启动后访问 `http://localhost:3000`，即可获得一个干净的 YouTube 前端。

## API 形态

```bash
# 获取视频信息
curl https://<your-instance>/api/v1/videos/<video-id>

# 搜索
curl "https://<your-instance>/api/v1/search?q=...&type=video"

# 订阅导出（RSS）
https://<your-instance>/feed/subscriptions
```

这套 API 也成了 FreeTube、Yattee、Piped 等第三方 YouTube 客户端的事实上游。

## 适用边界与不适用边界

**适用**：

- 关心隐私、不愿让 YouTube 拿到完整观看历史的人
- 想要把 YouTube 当成单纯"视频源"，不被首页推荐绑架的人
- 想要为家庭/小团队部署一个稳定可控的视频入口
- 想做第三方客户端（Invidious API 是最稳定的开源 YouTube 数据源）

**不适用**：

- 强依赖 YouTube 直播打赏/Super Chat（Invidious 不支持打赏链路）
- 期待它解决地区版权问题（视频流最终仍来自 YouTube，地理限制不变）
- 大型团队把 Invidious 当成生产环境的 SaaS（运维成本需要自己承担）

## 与 Piped、FreeTube 的关系

- **Piped**：另一个 YouTube 替代前端，更强调联邦化（多实例 + ActivityPub 风格关注）。Invidious 偏自托管单体，Piped 偏联邦。
- **FreeTube**：基于 Electron 的桌面客户端，**后端默认就是 Invidious 实例**——这意味着 Invidious 的稳定程度直接影响所有 FreeTube 用户。

过去一年 Invidious 经历了多轮大版本重构（项目从 Ruby 重写到 Crystal），目前在性能与稳定性上比早期版本提升明显。