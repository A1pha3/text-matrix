---
title: "Chatwoot：开源全渠道客服平台，Intercom 与 Zendesk 的自部署替代"
date: "2026-06-12T15:11:15+08:00"
slug: "chatwoot-open-source-customer-support-platform-guide"
description: "Chatwoot 是面向中小团队的开源全渠道客服平台，统一管理网站在线聊天、邮件及 Facebook/Instagram/WhatsApp 等多渠道对话。本文从项目定位、技术栈、架构概览、Captain AI 能力与部署路径五个角度，帮你判断它是否能替代 Intercom、Zendesk 这类 SaaS 客服系统。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "Rails", "Vue", "全渠道客服", "AI Agent"]
---

## 学习目标

读完本文后，你应能：

- 说清 Chatwoot 把"多渠道对话归一化"做到什么程度，以及它和 Twenty、Odoo 这类相邻项目的边界在哪里。
- 对照 Rails + Sidekiq + PostgreSQL + Redis 这套后端组合，判断自部署时哪个组件会成为瓶颈，并知道 pgvector 在 Captain AI Agent 里扮演什么角色。
- 跟着一次"客户从网站 Widget 发消息到坐席回复"的完整链路，定位路由、实时分发、报表聚合分别落在哪段代码、哪个进程。
- 在 Heroku、DigitalOcean Kubernetes、自建 Docker Compose 三条部署路径里做出取舍，并知道落地前必须自检的合规、凭证、本地化三件事。

## 目录

- [一句话判断](#一句话判断)
- [项目位置](#项目位置)
- [系统地图](#系统地图)
- [一次会话从客户敲第一行字到坐席回复](#一次会话从客户敲第一行字到坐席回复)
- [Captain：值得单独看的 AI Agent](#captain值得单独看的-ai-agent)
- [部署与落地](#部署与落地)
- [谁该用、谁可以等](#谁该用谁可以等)
- [边界与未覆盖](#边界与未覆盖)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [FAQ](#faq)

## 一句话判断

Chatwoot 把分散在十几种渠道里的客户对话统一收进一个可自托管的工单系统，同时把 AI 助手、Help Center、报表、自动化打包在一起。它不是 Intercom 的功能克隆，但已经覆盖 80% 的中型团队实际会用到的客服场景，剩下的 20% 需要靠 enterprise 版或自研补齐。

## 项目位置

[chatwoot/chatwoot](https://github.com/chatwoot/chatwoot) 是 GitHub 上规模最大的开源客服平台之一：33.5k+ Stars、7.9k+ Forks、6,279 次 commit。官方把它定位为 Intercom、Zendesk、Salesforce Service Cloud 的开源替代，覆盖三类典型用户：

- 想从 Intercom/Zendesk 迁出、按坐席付费压不住成本的中小 SaaS 团队；
- 数据合规要求客户对话必须留在自己服务器上的金融、医疗、政企客户；
- 想把客服系统嵌进现有 Rails/Vue 技术栈、避免引入新一套封闭平台的工程团队。

与同类项目对比时，区别比较明显：Twenty 主打 CRM（销售线索与商机），Odoo 把客服当 ERP 的一小块；Chatwoot 是专门的对话中心，模型围绕"会话（Conversation）"这一核心对象展开，不掺杂销售管道、库存、订单等概念。

## 系统地图

仓库 `develop` 分支（约 6,279 次 commit）已经把整套系统拆得比较清楚。结合 README、`Gemfile`、`Procfile` 和官方 `docker-compose.production.yaml`，可画出一张总览图：

```text
┌─────────────────────────────────────────────────────────────┐
│                    Frontend  (Vue 3 + Vite + Tailwind)      │
│  - Agent Dashboard (收件箱/会话/联系人/报表)                  │
│  - Help Center Portal (公开帮助中心)                         │
│  - Captain UI (AI Agent 配置与回放)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST + WebSocket (Rails 默认)
┌──────────────────────────▼──────────────────────────────────┐
│              Backend  (Ruby on Rails 7.1 + Sidekiq)         │
│  - app/controllers          : REST API                       │
│  - app/jobs                 : 异步任务 (Sidekiq)             │
│  - app/mailers              : 邮件入站/出站                   │
│  - app/models/services      : 业务编排                        │
│  - app/javascript           : 前端代码（含 widget）          │
│  - lib/                     : 渠道连接器与集成                │
└─────┬───────────┬──────────────────┬────────────────────────┘
      │           │                  │
┌─────▼─────┐ ┌───▼─────────┐  ┌─────▼──────────┐
│ PostgreSQL│ │   Redis     │  │   文件存储      │
│ (主数据,  │ │ (Sidekiq +  │  │ (storage_data  │
│  pgvector)│ │  实时分发)  │  │  volume)       │
└───────────┘ └─────────────┘  └────────────────┘

外部渠道(由 lib/ 下的适配器实现):
  Website Widget ─ Live Chat
  Email (IMAP/SMTP) ─ Email Channel
  WhatsApp Business API, Facebook, Instagram,
  Twitter/X, Telegram, Line, SMS
```

读这张图要注意四件事：

1. **后端是 Rails 7.1 单体**。`Gemfile` 写明 `gem 'rails', '~> 7.1'`，`Procfile` 把 `web`、`worker`、`release` 三个进程拆开跑：web 是 `rails server`，worker 是 `bundle exec sidekiq -C config/sidekiq.yml`。这意味着核心能力都跑在同一个 Rails 应用里，异步任务用 Sidekiq + Redis，发布前的 `db:chatwoot_prepare` 由 release 阶段执行。
2. **PostgreSQL 还带 pgvector**。`docker-compose.production.yaml` 用的镜像是 `pgvector/pgvector:pg16`——这不是巧合，pgvector 正是 Captain AI Agent 做检索增强生成（RAG，Retrieval-Augmented Generation）的存储后端。
3. **前端是独立 SPA**。`vite.config.ts`、`package.json`、`pnpm-lock.yaml`、`tailwind.config.js`、`postcss.config.js` 都在仓库根目录——Vue 3 + Vite + Tailwind。`Procfile.dev` 同时拉 Rails 后端和 Vite 前端，是开发时的并行启动方式。
4. **渠道适配被压到 `lib/` 之下**。每个渠道（WhatsApp、Line、Facebook、Email）独立成文件，统一走 `Channel` 抽象层。这就是"全渠道"的工程含义——不是写十套代码，而是写一份抽象 + 若干适配器。

## 一次会话从客户敲第一行字到坐席回复

光看结构容易把 Chatwoot 当成普通的工票系统。它真正的差异在"消息归一化"——把不同来源、不同协议的消息塞进同一张 `messages` 表。下面以"客户从网站点击在线聊天"为例，看一次会话在系统里的实际流转（具体类名是按 Rails 约定做的示意，对应代码以仓库实际为准）：

1. 客户在网站打开 Widget。Widget 是仓库内 `app/javascript/widget/` 的独立打包产物，前端建立 WebSocket 长连接后从后端拿到匿名身份。
2. 客户发出第一条消息。前端把消息 POST 到 REST API，后端在负责会话创建的服务对象里建出 `Conversation` 与第一条 `Message`。
3. **路由与自动分配**。`Assignment` 逻辑按 inbox 策略（轮询、负载最低、标签匹配）选一个坐席；`reporting_event` 写入一张事件表，供后续报表聚合。
4. **坐席收到通知**。Rails 广播到该会话的实时通道，所有订阅该会话的浏览器/移动端会立刻收到事件，UI 上无需刷新就把消息卡片 push 出来。
5. **坐席回复**。回复时如果启用了 Captain（AI Agent），Capilot 服务会先在文本框里给出草稿；坐席可以接受、改写、或直接关闭。专门负责自动回复的 worker 任务则把草稿直接自动发出去（适用于"咨询营业时间""退订邮件"这类高频问答）。
6. **多渠道合并**。如果同一客户随后从 WhatsApp 又发来消息，WhatsApp 渠道的 incoming-message 服务会按 `contact_id` 把消息合进已有的 `Conversation` 上，而不是新开一张工单。这就是"客户看到的是一次完整对话"与"系统看到的是一条会话记录"的对应。
7. **报表与导出**。报表模块异步聚合当天的 `reporting_event`，供 Agent Reports、Inbox Reports、CSAT Reports 拉取。

理解这条链路后，部署和调优就清楚多了：PostgreSQL 撑会话数，Redis 撑异步任务与实时分发；任何一个环节被打满，瓶颈都落在那一个组件上。

## Captain：值得单独看的 AI Agent

Captain 是 Chatwoot 自家的 AI Agent，和"在回答框上方加个 Copilot 按钮"不同。README 把它的能力列为四块：

- **自动回复**：基于知识库（Help Center 文章 + 上传文档）做检索增强生成，把常见问题直接答完。
- **建议回复**：在坐席输入时给出三条候选草稿，并标注依据文章 ID，方便坐席快速改写。
- **意图分类**：给新进来的会话打标签、转给对应 Team，充当分流器。
- **工作总结**：对话结束自动生成摘要，发到 Slack 或写回 `Conversation#summary` 字段。

工程上 Captain 是"挂件式"接入：默认的 Copilot 行为不需要外部 LLM，关键路径是一组 service object，外部 LLM 通过 `llm` 配置项接入。这套设计的代价是——如果你想换模型、改 embedding 或加自托管的 vLLM/TGI，需要改的就是这层 service，而不是 UI。这一点对企业客户比较友好。

但要注意一点：README 公开列出的功能并不等于企业级能力。Captain 的稳定性、计费、长上下文表现受所选 LLM 影响；自部署时如果不上 enterprise 版，部分高级功能（如 SSO、审计日志、SLA 管理）会受限。

## 部署与落地

README 列了三条主要部署路径：

- **Heroku 一键部署**。仓库根目录有 `app.json`，按钮直接调用。优点是 5 分钟拉起，缺点是 Heroku 免费层已废弃，规模化后账单会迅速超过 SaaS 客服。
- **DigitalOcean 1-Click Kubernetes**。仓库里 `deployment/` 目录有对应 manifests，思路是 Rails + Sidekiq + PostgreSQL + Redis 拆成 K8s Deployment。
- **自建 Docker Compose**。`docker-compose.yaml`（开发）和 `docker-compose.production.yaml`（生产）覆盖了 90% 自部署场景，标准四件套：Rails + Sidekiq + pgvector/PostgreSQL 16 + Redis。

落地前需要自检的三件事：

1. **依赖外部渠道的凭证**。WhatsApp Business API、Facebook Page、Line Official Account 都需要在对应平台注册开发者账号，拿到的 token 写进 `InstallationConfig` 表；自部署时这一步绕不开。
2. **合规与留存**。GDPR 场景下要打开 Data Retention 规则和 PII 脱敏；PCI 场景则需要关闭卡片号自动识别功能。这些配置大多在后台 Settings 即可改。
3. **本地化与多语言**。UI 翻译走 [translate.chatwoot.com](https://translate.chatwoot.com) 的 Crowdin 工作流，要本地化 UI 先到那里提权。

## 谁该用、谁可以等

适合先用 Chatwoot 的场景：

- 中小 SaaS、电商、在线教育团队，需要"一个收件箱管所有渠道"，预算敏感；
- 已有 Rails/Vue 技术栈的工程团队，希望二开成本低；
- 客户对话数据需留在自己 VPC 内的金融、医疗、政企；
- 想在 1-3 个月内迁出 Intercom/Zendesk 的团队。

可以再等等的场景：

- 需要完整 SSO + 审计 + SLA + 大型知识库的企业功能，建议直接评估 enterprise 报价，对比 Zendesk 的总成本；
- 团队体量在 5 人以下、客户对话量日均 < 100 条，用免费版 Intercom 或 Crisp 更划算，Chatwoot 的运维成本远高于 SaaS；
- 已经在用 Salesforce Service Cloud 且深度耦合，迁移 ROI 不高。

## 边界与未覆盖

- 这篇文章没有展开 `app/javascript/` 的前端模块切分、Sidekiq 队列配置、ActionCable 的连接回收策略——这些属于源码层细节，需要结合自己的二次开发需求再读。
- 没有涉及 Captain 在 pgvector 上的具体索引策略、embedding 模型选型与重排逻辑，这部分企业落地时需要单独做一次 PoC。
- 没有跑 benchmark。README 没给出"每秒能处理多少条会话"这种数据，自部署规模评估只能结合自己的压测；不要直接套用其它 Rails 应用的通用经验。

Chatwoot 是一份"成熟但不完美"的开源答案：核心场景够用、扩展接口清晰、迁移路径明确，剩下的工程取舍在你这一侧。

## 自测题

下面 5 道题用来检验你是否真的把上面的架构和落地路径串起来了。先自己答，再点开参考答案对照。

### 1. 为什么 Chatwoot 在 `docker-compose.production.yaml` 里用的是 `pgvector/pgvector:pg16` 而不是普通的 `postgres:16`？

<details>
<summary>参考答案</summary>

`pgvector` 镜像在原生 PostgreSQL 之上加了 vector 类型与 ANN 索引扩展。Captain AI Agent 做检索增强生成（RAG）时，要把 Help Center 文章和上传文档的 embedding 存进数据库，再按相似度检索。换成普通 `postgres:16` 镜像，Captain 的向量检索路径会直接报错或退化到不可用。这是"AI 能力已经下沉到存储层"的信号，部署时不能按传统 Rails 应用的依赖来理解。
</details>

### 2. 客户先在网站 Widget 发了一条消息，半小时后又从 WhatsApp 发来一条。系统会新开一张工单还是合进原会话？依据是什么？

<details>
<summary>参考答案</summary>

会合进原会话。WhatsApp 渠道的 incoming-message 服务按 `contact_id` 把新消息挂到已有的 `Conversation` 上，而不是新开一张。前提是两条渠道都关联到同一个 `Contact`——这通常靠邮箱或手机号匹配。如果客户在两个渠道用了完全不同的身份信息，系统就无法自动合并，需要坐席手工 merge contact。
</details>

### 3. Sidekiq 在这套架构里承担了哪些异步任务？如果 Redis 挂了 5 分钟，哪些功能会先坏？

<details>
<summary>参考答案</summary>

Sidekiq 主要承担：消息归一化后的入库、报表 `reporting_event` 异步聚合、Captain 的草稿生成与自动回复 worker、邮件入站出站、跨渠道 webhook 重试。Redis 挂掉后，实时分发（ActionCable 也会用 Redis 做 pubsub）和异步任务会同时停摆——坐席 UI 不再实时收到新消息，自动回复不再触发，报表聚合堆积。但已落库的会话不会丢，PostgreSQL 仍是唯一真源；Redis 恢复后积压任务会按队列重放。
</details>

### 4. 一个 5 人小团队日均 80 条对话，要不要上 Chatwoot 自部署？给出判断依据。

<details>
<summary>参考答案</summary>

不建议。这个量级用免费版 Intercom 或 Crisp 更划算。自部署 Chatwoot 的运维成本（Rails + Sidekiq + PostgreSQL + Redis + pgvector + 渠道凭证维护 + 升级跟进）远高于 SaaS 月费。Chatwoot 的甜区是"按坐席付费已经压不住成本"的中型团队——通常坐席数 20+ 或对话量日均 500+ 才能看到明显 ROI。5 人团队更应该把工程时间花在产品本身。
</details>

### 5. Captain 的"挂件式"接入设计对换模型这件事意味着什么？如果要换 vLLM 自托管，改动会落在哪一层？

<details>
<summary>参考答案</summary>

意味着换模型不需要动 UI 或前端，改动集中在 Captain 的 service object 层和 `llm` 配置项。具体说，要改的是负责构造 prompt、调用 LLM API、解析返回的那组 service 对象——把对 OpenAI/Anthropic 的 HTTP 调用换成对 vLLM 自托管端点的调用，并调整 embedding 模型以匹配 pgvector 里已有的向量维度。如果原 embedding 维度和新模型不一致，还需要重算全量文档的 embedding 并重建索引，这是落地时最容易低估的工作量。
</details>

## 进阶路径

把上面这些读完，只是把 Chatwoot 当作"可用的开源客服"看清楚了。要把它真正用顺、改顺，建议按下面这条顺序继续走：

### 1. 源码阅读顺序

1. **先读 `app/models/`**：`Conversation`、`Message`、`Contact`、`Inbox` 这四个核心模型是整套系统的语义骨架。看完它们的关系，再读其它表都是"挂在哪个外键上"。
2. **再读 `lib/` 下的渠道适配器**：挑 WhatsApp 和 Email 两个对比看，理解 `Channel::Api` 抽象怎么把不同协议的消息归一到 `Message` 表。
3. **接着读 `app/jobs/` 与 Sidekiq 队列配置**：搞清 `reporting_event`、`webhooks`、Captain 相关 worker 各自跑在哪个队列，便于后续按队列做隔离与限流。
4. **最后读 `app/services/`**：会话路由、自动分配、Captain 调用入口都在这里，是二开改动最频繁的一层。

### 2. Captain PoC 步骤

如果团队打算用 Captain 替代部分一线坐席，建议先做一次小范围 PoC，而不是直接全量上线：

1. 选一个高频 FAQ 主题（如"营业时间""退订邮件""物流查询"），把对应 Help Center 文章写齐。
2. 在一个低峰 inbox 上打开 Captain 自动回复，其它 inbox 保持人工。
3. 跑两周后看三个指标：自动回复解决率、坐席改写率、CSAT 评分变化。
4. 如果 CSAT 没掉、解决率 > 30%，再扩到第二个主题；如果 CSAT 掉了 5 分以上，先回到知识库质量而不是调模型。

### 3. 自部署压测

README 没给吞吐数据，自部署前必须自己压。最小压测脚本可以这么写：

- 用 `k6` 或 `locust` 模拟 200 个并发客户从 Widget 发消息；
- 监控 PostgreSQL 的 `pg_stat_activity`、Redis 的 `INFO clients`、Sidekiq Web UI 的队列堆积；
- 重点看 `messages` 表的写入延迟和 ActionCable 的广播延迟——这两个先涨起来，就是瓶颈所在。

### 4. 升级与迁移

Chatwoot 的 `develop` 分支活跃，minor 版本之间会有 schema 迁移。升级前先看 `db/migrate/` 里新增的迁移文件，在 staging 跑一次 `db:chatwoot_prepare`，确认回滚路径再上生产。从 Intercom/Zendesk 迁移时，官方提供了 CSV 导入工具，但历史会话的 `contact_id` 映射需要自己写脚本对齐。

## FAQ

### Q1：自部署后，Captain 的 LLM 调用是走 Chatwoot 的云服务还是我自己配的 endpoint？

A：默认走 Chatwoot 官方的 LLM 服务（需要 enterprise 版授权），但企业版可以配置成走自托管的 vLLM/TGI 或第三方 API。具体配置项在 `InstallationConfig` 表的 `llm` 相关 key 里。如果你用的是社区版（非 enterprise），Captain 的高级功能会受限，建议先确认 license 再决定 PoC 范围。

### Q2：WhatsApp Business API 接入一直报 401，怎么排查？

A：按这个顺序查：

1. Meta Business 后台的 WhatsApp Business Account 是否已通过验证，Phone Number ID 是否正确。
2. `InstallationConfig` 里 `whatsapp_app_id`、`whatsapp_app_secret`、`whatsapp_phone_number_id` 是否都填了，且没有多余空格。
3. Webhook 校验 token 是否和 Meta 后台配置的一致。
4. 如果是刚申请的号码，24 小时内只能发模板消息，不能发自由文本——这是 Meta 的限制，不是 Chatwoot 的 bug。

### Q3：Sidekiq 队列堆积越来越长，坐席 UI 收新消息有延迟，怎么定位？

A：先看 Sidekiq Web UI（默认 `/sidekiq`）的队列分布。常见原因有三个：

1. **Captain worker 慢**：LLM 调用超时堆积，把 default 队列堵住。解法是把 Captain 相关 worker 拆到独立队列，并在 `config/sidekiq.yml` 里给它单独的并发数。
2. **报表聚合任务跑全表**：`reporting_event` 在大表上跑聚合时锁住写入。解法是给 `reporting_event` 加按天分区，或把聚合任务挪到只读副本。
3. **Redis 内存打满**：`INFO memory` 看 `used_memory` 是否接近 `maxmemory`。打满后 Sidekiq 会拒绝新任务，需要扩容或调短任务保留时间。

### Q4：从 Intercom 迁移，历史会话能完整迁过来吗？

A：不能完整迁。Intercom 的导出 API 只提供最近 90 天的会话，且不包含附件原文件。Chatwoot 官方的 CSV 导入工具能把文本会话迁过来，但 `contact_id` 需要自己写映射脚本对齐。建议迁移策略是：历史会话留在 Intercom 只读访问 6 个月，新会话从切换日起在 Chatwoot 走，避免一次性迁移的脏数据风险。

### Q5：pgvector 的索引该用 IVFFlat 还是 HNSW？

A：取决于数据规模和召回精度要求。Chatwoot 默认不强制选哪种，自部署时需要自己定。经验值：

- 文档量 < 10 万条：HNSW，召回精度高，构建慢但查询快。
- 文档量 10 万 - 100 万条：HNSW 仍可用，注意 `ef_construction` 调到 200 以上。
- 文档量 > 100 万条：需要做 A/B，IVFFlat 在大表上构建更快，但召回精度需要调 `lists` 和 `probes` 参数。

无论选哪种，embedding 模型一旦换，索引必须重建——这是 Captain PoC 里最容易踩的坑。
