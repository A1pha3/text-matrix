---
title: "Chatwoot：开源全渠道客服平台，Intercom/Zendesk 的自托管替代"
date: 2026-08-01T02:54:21+08:00
lastmod: 2026-09-14T12:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Chatwoot", "客服", "全渠道", "开源", "Ruby", "Rails", "自托管"]
description: "Chatwoot 是 36.8k Stars 的开源客服平台，将网站实时聊天、邮件、WhatsApp、Telegram、Facebook、Instagram 等渠道统一到一个收件箱，内置 Captain AI agent、分配策略和自助知识库。本文核实其许可证结构、技术栈与官方部署流程，并给出采用建议。"
slug: chatwoot-chatwoot-omnichannel-support-guide
github_repo: "chatwoot/chatwoot"
source_key: "gh:chatwoot/chatwoot"

---

## 一句话判断

找 Intercom 或 Zendesk 的开源替代，Chatwoot 是目前最成熟的选项之一：36.8k Stars、2019 年立项并持续迭代至 v4.17.1、渠道覆盖面对齐商业产品，核心代码 MIT 许可、可自托管。选型前要算清三笔账：自托管的运维投入、AI 功能的付费边界、语音通话这类新功能成熟度。

## 它在解决什么问题

客服团队的日常麻烦是渠道割裂：客户散落在网站、邮件、WhatsApp、社交媒体，每个渠道一个后台，上下文互不相通。Chatwoot 把这些渠道聚合成一个收件箱，让一个团队在同一个界面里协作处理所有对话。它不是"网站聊天挂件加个机器人"——那类产品只覆盖单渠道场景；它对标的是 Intercom、Zendesk、Salesforce Service Cloud 这一档的全渠道客服台。

把系统拆成三层主线，分别对应三类决策：

| 层 | 解决什么 | 关键组件 |
| --- | --- | --- |
| 对话层 | 渠道聚合、团队协作、分配 | 全渠道收件箱、Assignment Policies、帮助中心 |
| 自动化层 | 让机器先接、人接复杂的 | Captain（AI agent）、Agent Bots、自动化规则 |
| 开放层 | 数据自主、可扩展 | 自托管、MIT 核心、API 与集成 |

带着这三层往下看，比逐个过功能清单有效。

## 一次对话怎么流过系统

以网站访客发消息为例，走一遍完整链路：

1. 访客在网站 widget 发出消息，请求打到 Rails API，消息写入 PostgreSQL；
2. Sidekiq 从 Redis 队列接走后台任务：发 webhook、推送邮件通知、执行自动化规则；
3. 客服端（Vue 3 单页应用）通过 ActionCable 的 WebSocket 长连接收到新对话推送，不需要刷新页面；
4. 新对话按分配策略路由。v4.12 起的 Assignment Policies 支持 round-robin（轮流）与 balanced（按负载）两种分配方式，可给每个客服设容量上限，新账号默认启用这套 v2 分配；
5. 如果启用了 Captain，它先读帮助中心与 FAQ 生成应答；解决不了就转人工，或在回复框给出草稿让客服一键采用；
6. 客服回复经队列发出，对话结束后可触发 CSAT（客户满意度）调查，数据进报表。

这条链路里，实时性靠 ActionCable，异步靠 Sidekiq，状态在 PostgreSQL——全程是 Rails 生产力栈的原生组合，没有引入额外的消息队列中间件。对运维的含义是：会养 Rails 应用，就会养 Chatwoot。

## Captain：AI 部分的边界在哪

Chatwoot 的 AI 有三条路径，能力与获取方式各不相同：

- **Captain**：官方 AI agent，2025 年 4 月底正式发布，随付费 Cloud 计划提供，含每月免费应答额度（Startups 100 条、Business 300 条、Enterprise 500 条）。能力分四块：AI Assistant 自动应答（从帮助中心、FAQ 和历史对话中学习）；Copilot 辅助人工（起草、改进、翻译回复，支持用自然语言查询客户历史）；Smart FAQs 找知识盲区（把高频未覆盖问题整理成待审文章草稿）；Memories 跨对话记忆上下文。v4.6.0 起支持给 Captain 上传 PDF 文档。
- **Agent Bots**：通过 webhook 接自己搭的机器人，模型和提示词都由你控制。
- **Chatwoot CLI**：命令行入口，面向开发与自动化场景。

注意一个容易误判的点：官方自托管文档没有为 Captain 提供专门的配置章节，"内置 AI agent"的完整开箱体验目前绑定付费 Cloud 计划。自托管团队要 AI，现实路径是用 Agent Bots 接自己的模型。

## 渠道覆盖

README 列出的渠道：网站实时聊天、邮件、SMS；WhatsApp、Telegram、Line；Facebook、Instagram、Twitter（X）；TikTok（2026 年 2 月上线，付费计划）。

语音通话值得单独说：2026 年 6 月起进入 beta，支持 Twilio 传统电话和 WhatsApp Calling，客服在浏览器里接听、界面带客户上下文；自托管从 v4.15.0 起对付费计划开放；8 月又补上了通话仪表盘（按条件筛选、录音回放）。一年前的资料还会说"Chatwoot 电话渠道弱，要自己接 Twilio"，这条已经过时——但通话毕竟是 2026 年的新功能，选它承担呼叫中心级负载还太早。

## 协作、分配与报表

- **团队协作**：私信与 @提及（讨论不进入客户可见的回复）、标签、快捷回复模板、自定义视图、营业时间与自动回复
- **分配**：Assignment Policies 的 round-robin / balanced 两种策略加容量上限
- **知识库**：内置帮助中心，发布文章和 FAQ 供客户自助查询，减少重复咨询
- **报表**：对话、客服、收件箱、标签、团队多个维度，含实时视图、CSAT 和可下载报表
- **安全与效率**：MFA 多因素认证（v4.6.0 起）、按发送者/收件箱/时间过滤的高级搜索（2026 年 2 月）
- **集成**：Slack（直接在 Slack 里处理对话）、Dialogflow（接自建机器人）、Shopify（查看订单）、Linear（创建工单）、Google Translate（实时翻译）

## 技术栈

按 GitHub 语言统计（字节数）与前端依赖清单核实：

| 组件 | 选型 | 版本/占比 |
| --- | --- | --- |
| 后端 | Ruby on Rails | Ruby 约占代码 52% |
| 前端 | Vue 3 + Vite | Vue 约 27%，JavaScript 约 23%，vue-router 4 |
| 状态管理 | Pinia 与 Vuex 并存 | 历史迁移的中间态，二开两套都会碰到 |
| 实时通信 | ActionCable（WebSocket） | 前端依赖 `@rails/actioncable` |
| 数据库 | PostgreSQL | — |
| 队列与缓存 | Redis + Sidekiq | — |

选型逻辑是典型的 Rails 生产力路线：实时、队列、后台任务全部在 Rails/Redis 生态内解决。这意味着自托管的技术门槛不在组件数量，而在你是否熟悉 Rails 应用的常规运维。

## 自托管部署：官方流程

官方生产部署用 Docker Compose（要求 Docker ≥ 20.10.10、Compose ≥ v2.14.1），一个 compose 文件里跑四个角色：Rails Web、Sidekiq worker、PostgreSQL、Redis。

```bash
# 1. 拉取官方模板（develop 分支）
wget -O .env https://raw.githubusercontent.com/chatwoot/chatwoot/develop/.env.example
wget -O docker-compose.yaml https://raw.githubusercontent.com/chatwoot/chatwoot/develop/docker-compose.production.yaml

# 2. 编辑 .env：设置 FRONTEND_URL、SECRET_KEY_BASE（rake secret 生成）、
#    POSTGRES_PASSWORD、REDIS_PASSWORD 等

# 3. 初始化数据库（首次安装用这个命令，此时不要用 db:migrate）
docker compose run --rm rails bundle exec rails db:chatwoot_prepare

# 4. 启动
docker compose up -d

# 5. 验证
curl -I localhost:3000/api
```

三个最容易踩的坑：

- **`db:chatwoot_prepare` 在每次升级镜像后都要重跑**；跨多个版本的旧实例要按官方指引逐级升级，不能一步跳到最新。
- **compose 容器只绑 localhost**，对外需要 nginx 反代，且配置有硬性要求：`underscores_in_headers on`（Chatwoot 的请求头带下划线，nginx 默认丢弃这类头）、WebSocket upgrade 头、`proxy_buffering off`、`client_max_body_size 0`，SSL 用 certbot 签发。
- **`SECRET_KEY_BASE` 与数据库密码同等对待**：丢失即全部会话失效。

不想自己养机器的话，README 提供 Heroku 一键部署，DigitalOcean Marketplace 有 1-Click Kubernetes。

## 许可证：open-core，别只看标签

这个项目的许可证有个容易误读的地方：GitHub 的 license 检测显示 "Other"，但 LICENSE 文件的主体是标准 MIT Expat 文本，自定义的部分只有一条——`enterprise/` 目录被排除在外，按单独的商业许可授权，第三方依赖则保留各自的原许可。

也就是说：核心代码是真 MIT，可以自由商用、修改、再分发；只有在你需要 enterprise 目录里的企业版功能时，才进入商业授权范围。判断——别信 GitHub 那个 "Other" 标签——直接看 `LICENSE` 文件正文。

## 适用边界

**适合**：

- 想把客服从 SaaS 订阅费和外部数据依赖里拿回来的中小团队
- 渠道分散（网站 + WhatsApp + 社媒）、需要一个统一收件箱的团队
- 具备 Rails/PostgreSQL/Redis 运维能力，或愿意用受管服务跑 compose 的团队
- 想用 AI 但坚持自控模型与数据的团队（Agent Bots 路线）

**要三思**：

- 没有运维人手的小团队：自托管省下的是订阅费，换来的是运维时间，此时 Cloud 或 Heroku 一键部署更划算
- 把 AI 自动化当核心依赖的团队：Captain 的开箱体验绑定付费 Cloud 计划，自托管要自己接模型
- 需要开箱即用企业级分析与 SLA 的团队：那部分在 enterprise 目录里，按商业许可销售
- 呼叫中心级语音需求的团队：通话功能 2026 年 6 月才进 beta，成熟度不及经营多年的传统电话客服产品

采用顺序建议：先用 Cloud 免费档或本地 compose 跑通网站渠道，验证收件箱体验是否匹配团队流程；再逐个接入 WhatsApp、邮件等渠道（每个渠道的 API 申请成本不同，留出等待期）；最后才上 Captain 或 Agent Bots。反过来先铺 AI 再补渠道，是这类平台选型里最常见的返工路径。

## 相关链接

- 仓库：[github.com/chatwoot/chatwoot](https://github.com/chatwoot/chatwoot)
- 官网：[chatwoot.com](https://www.chatwoot.com)
- 开发者文档（自托管与 API）：[developers.chatwoot.com](https://developers.chatwoot.com)
- 产品文档：[chatwoot.com/help-center](https://www.chatwoot.com/help-center)
- Docker 镜像：[hub.docker.com/r/chatwoot/chatwoot](https://hub.docker.com/r/chatwoot/chatwoot)
- Discord：[discord.gg/cJXdrwS](https://discord.gg/cJXdrwS)
- 翻译贡献：[chatwoot.crowdin.com/chatwoot](https://chatwoot.crowdin.com/chatwoot)

---

*仓库数据（Stars、Forks、版本、许可证）与部署流程核实于 2026-09-14，来源为 GitHub API、官方部署文档与官方 changelog。*
