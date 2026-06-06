+++
date = '2026-05-28T01:00:36+08:00'
draft = false
title = 'OpenStock：开源股票工作台'
slug = 'openstock-open-source-stock-market-platform'
description = 'OpenStock 把 Finnhub、TradingView、Better Auth、MongoDB 和 Inngest 织成一套能长期使用的开源股票工作台，本文分析它的技术栈、已闭环能力和扩展方向。'
categories = ['技术笔记']
tags = ['金融', '开源', 'Next.js', 'MongoDB']
+++

# OpenStock：开源股票工作台

OpenStock 很容易被看错。有人把它当成“开源版 Bloomberg”，也有人把它当成股票教程换了套更漂亮的 UI。把 README、API 文档和当前主干源码对着读一遍，会发现这两种看法都不准。它真正做成的，是在不自建行情基础设施的前提下，把行情接入、用户状态、异步通知和自部署链路缝成一套能长期使用的股票工作台。

让它真正像产品的，是注册之后那条状态链：系统记住用户偏好，把 watchlist 和 alerts 存下来，再把欢迎邮件、市场周报和后台任务挂到同一条异步平面上。对一个开源 Web 产品来说，这比"首页能搜股票"更接近真实产品。

## 先把问题摆在前面

- OpenStock 自己实现了什么，又把什么明确交给了 Finnhub、TradingView、Kit 和 AI Provider。
- 当前已经闭环的能力有哪些，哪些功能还停在“检测到了”或“广播得出去”的阶段。
- 它更适合被当成个人股票工作台、开源产品模板，还是专业市场终端的替代品。
- 如果你准备 fork 它，最先应该读哪些入口，先补哪几块能力。

先把判断压成 5 句。

## 5 句判断

- OpenStock 没有自建证券数据管线。股票搜索、公司资料和市场新闻主要来自 Finnhub，图表、热力图和市场概览主要来自 TradingView。
- 它最扎实的部分不是图表层，而是状态层。Better Auth、MongoDB、受保护路由、watchlist 的联合唯一索引和 onboarding 字段，把 demo 拉成了能留住用户的工作台。
- Inngest 不是装饰。欢迎邮件、每周新闻广播、5 分钟轮询的价格提醒检测和每日召回任务，都已经挂在事件或 cron 上。
- AI 不在同步主路径上。登录、搜索、watchlist 和行情展示都不依赖模型；模型主要用在欢迎邮件和新闻摘要这类异步增强环节，而且公开文档已经给出多 Provider fallback 的思路。
- README 的营销表述比当前实现更激进。最明显的例子是 README 仍写着 `Daily news summary emails` 且强调 `using user watchlists`，而当前代码已经落成“每周一上午 9 点抓通用市场新闻并通过 Kit 广播”；价格提醒的检测与状态迁移也已完成，但 `lib/inngest/functions.ts` 的注释直接说明送达链路仍待补齐。

## 系统地图：先把 3 条主线拆开

```mermaid
flowchart LR
	User[用户] --> UI[Next.js 15 / React 19 页面]
	UI -->|登录与受保护路由| Auth[Better Auth + Middleware]
	Auth --> DB[(MongoDB)]
	UI -->|股票搜索、新闻、报价| Finnhub[Finnhub]
	UI -->|图表、热力图、市场视图| TV[TradingView Widgets]
	UI -->|注册事件、后台任务| Inngest[Inngest]
	Inngest -->|欢迎邮件、周报、提醒检测、召回| Workflows[异步工作流]
	Workflows -->|生成内容| AI[Gemini / MiniMax / Siray]
	Workflows -->|广播| Kit[Kit]
	Workflows -->|事务邮件| Mail[Nodemailer]
	Workflows -->|新闻与报价| Finnhub
	DB -->|用户、watchlist、alerts| Workflows
```

图里最关键的分界线只有一条：查询和状态是同步主路径，邮件、摘要、提醒检测和召回是异步平面。这个分界线的好处很直接。哪怕模型暂时不可用，用户依然能注册、登录、搜索股票、看图表、维护 watchlist。AI 失败时，坏掉的是欢迎邮件文案或摘要生成，不是整个产品。

| 主线 | 负责什么 | 关键依赖 | 当前判断 |
| ------ | ------ | ------ | ------ |
| 数据与展示 | 股票搜索、公司资料、市场新闻、图表、热力图 | Finnhub、TradingView、可选 Adanos | 页面完整，但不是自建行情基础设施 |
| 状态与个性化 | 登录、受保护路由、onboarding、自选股、提醒持久化 | Better Auth、MongoDB、Next.js middleware | 这是项目最成熟、也最像产品的部分 |
| 自动化与触达 | 欢迎邮件、市场周报、价格提醒检测、沉睡用户召回 | Inngest、Kit、Nodemailer、可选 AI Provider | 已有可用链路，但不同工作流成熟度差异明显 |

看到这里，大概就能判断它的分量了。它不是在跟专业终端拼数据深度，而是在把外部行情源、用户状态和异步任务装进一条能长期维护的产品骨架里。

## 它不是自建行情系统，这反而是对的

这类项目最容易写偏的地方，是把“接得很完整”误写成“底层都是自己做的”。OpenStock 的边界其实很清楚。

| 能力 | 公开资料能确认的实现方式 | 该怎么理解 |
| ------ | ------ | ------ |
| 股票搜索、公司资料、市场新闻 | Finnhub API | 这是数据入口，不是自建证券数据服务 |
| 个股图表、热力图、报价与市场视图 | TradingView widgets | 体验完整，不等于项目自带图表引擎 |
| 情绪洞察 | 可选 Adanos 情绪卡 | 是补充信号，不是主数据源 |
| 价格提醒判断 | 自己的规则逻辑 + Finnhub quote | 有业务层判断，但不是交易级告警系统 |
| 登录、watchlist、用户状态 | Better Auth + MongoDB + 业务模型 | 这是 OpenStock 自己真正做深的产品层 |

这种取舍很务实。做一套证券数据基础设施，是另一场战争；先借成熟数据和图表服务，把精力花在用户状态、后台任务和长期留存上，才是小团队更可能守住的路线。

Adanos 也不只是 README 里的一个环境变量。`app/(root)/stocks/[symbol]/page.tsx` 会在个股详情页并行拉 `getStockSentimentInsights(symbol)`，再把结果交给 `StockSentimentCard`。这说明项目确实给“情绪洞察”留了产品入口，只是它被放在辅助判断的位置，而不是整个系统的数据主干。

当然，代价也要说清。Finnhub 免费层会有延迟和配额限制，TradingView widget 让图表来得很快，但深改交互时会碰到第三方边界。你可以用它做个人工作台、学习项目或轻量 SaaS 原型；如果目标是低延迟专业终端、深度盘口、自动交易执行或明确的数据授权体系，当前公开实现离那个层级还很远。

## 把它从教程拉成产品的，是状态层，不是首页

看源码时，最能说明项目成色的不是 dashboard，而是用户状态从哪里来、怎么被保存、又怎么进入后续工作流。

注册页 `app/(auth)/sign-up/page.tsx` 不是只收邮箱和密码。它还收 `country`、`investmentGoals`、`riskTolerance` 和 `preferredIndustry`。`lib/actions/auth.actions.ts` 在 Better Auth 完成注册后，会把这些字段和 `email`、`name` 一起发成 `app/user.created` 事件。这个动作很关键，因为它把“注册成功”立刻变成了“后续异步任务可用的用户画像”。

状态层还有 3 个不显眼、但很说明问题的细节。

1. `middleware/index.ts` 默认保护了大多数页面，只把 `sign-in`、`sign-up`、`forgot-password`、`reset-password`、静态资源和 Next 内部资源排除在外。这个边界说明它不是匿名访客随便逛一圈就结束的只读站点。
2. `database/models/watchlist.model.ts` 为 `{ userId, symbol }` 建了联合唯一索引。也就是说，watchlist 不是一层前端临时状态，而是认真考虑过重复写入和长期持久化的产品数据。
3. `signInWithEmail` 会更新 `lastActiveAt`。这一步不显眼，但给后面的召回任务留下了可用信号。

把这几处连起来看，就能明白 OpenStock 的产品逻辑。它关注的不是“某只股票的详情页能不能展示”，而是“这个用户下次回来时，系统还记不记得他是谁、关心什么、最近有没有回来过”。

## 自动化层要对着源码看

这里不是在挑刺，而是在回答一个很实际的问题：不读源码的话，你能不能直接把它当成自己的产品底座。答案取决于每条工作流到底走到哪一步了。

| 工作流 | 触发方式 | 当前公开实现 | 工程判断 |
| ------ | ------ | ------ | ------ |
| 个性化欢迎邮件 | `app/user.created` 事件 | `sendSignUpEmail` 用注册画像组装 prompt，调用带 fallback 的 AI Provider，最后通过 Nodemailer 发信 | 这条链路已经闭环，是当前最完整的 AI 场景 |
| 市场新闻摘要 | `app/send.weekly.news` 事件或 `0 9 * * 1` cron | `sendWeeklyNewsSummary` 抓取通用市场新闻前 10 条，总结后通过 Kit 广播 | 真有周报，但范围已经从 README 的 `using user watchlists` 表述，收缩成通用市场新闻广播 |
| 价格提醒 | `*/5 * * * *` cron | 抓活跃提醒、按 `ABOVE` / `BELOW` 判断、命中后把 alert 标记为 `triggered: true` 与 `active: false` | 检测和状态迁移真实存在，但送达链路还没有完全补上 |
| 沉睡用户召回 | `0 10 * * *` cron | 能按 `lastActiveAt` / `lastReengagementSentAt` 找到 30 天以上沉默用户，但代码注释也承认 Kit 的一对一发送路径还不顺，多数用户仍偏向 mock / log 路径 | 有产品意图，但还不是可直接拿去上线的成品 |

如果只读 README，你很容易把这部分想成“提醒、日报、召回都已经是成熟能力”。源码给出的答案更细一些：欢迎邮件是真的闭环，市场周报是真的能发，价格提醒已经能检测命中，但提醒送达和用户召回仍然带着明显的在建痕迹。这不是靠文案猜出来的，`sendWeeklyNewsSummary` 的 cron 和 `checkStockAlerts`、`checkInactiveUsers` 里的注释都把边界写得很直白。

还有一处容易漏看：watchlist 个性化新闻并没有从产品里消失，只是留在了应用内页面，而不是现在的邮件摘要链路里。`app/(root)/watchlist/page.tsx` 会先拉一版通用新闻，再在 watchlist 有 symbol 时改用 `getNews(watchlistSymbols)`；`lib/actions/finnhub.actions.ts` 也确实会按 symbol 去抓 `company-news`，再用 round-robin 的方式挑出最多 6 条相关新闻。也就是说，“using user watchlists” 现在更多体现在站内阅读体验，而不是邮件周报。

Kit 的角色也该单独看。`lib/kit.ts` 把 `sendBroadcast` 明确写成 newsletter / summary 广播接口，并直接提醒它不是天然的 1 对 1 SMTP 替代。这一点解释了为什么周报广播能成立，而沉睡用户召回和单用户触达会显得更别扭。

对二开来说，API_DOCS 往往比 README 更有参考价值。API 文档已经把 `weekly-news-summary` 写成每周一上午 9 点的广播周报，也明确了 `check-stock-alerts` 和 `check-inactive-users` 的 cron 语义。这比 marketing 口号更有用。

## 一条真实任务流：从注册到提醒命中

静态地看模块，容易误以为 OpenStock 只是把几个功能拼在了一起。把它放回一次真实用户路径里，系统的形状会清楚得多。

1. 用户在注册页提交邮箱、密码和 4 个偏好字段。
2. Better Auth 完成注册后，`lib/actions/auth.actions.ts` 立刻发送 `app/user.created` 事件。
3. `sendSignUpEmail` 把国家、投资目标、风险偏好和偏好行业组装进 prompt；如果模型调用失败，会退回一段普通欢迎文案，而不是直接让链路报错。
4. 用户把股票加入 watchlist；联合唯一索引保证同一用户不会重复添加同一 symbol。
5. 用户创建 `ABOVE` 或 `BELOW` 价格提醒；`database/models/alert.model.ts` 还给提醒加了默认 90 天过期时间。
6. `check-stock-alerts` 每 5 分钟抓一次活跃提醒和最新报价，命中阈值后把提醒标记成已触发并停用。
7. 如果你想把“主动提醒”当成产品卖点，最后一步还不能省。当前公开实现已经完成检测与状态迁移，但真正稳定的通知送达，还需要你自己把最后一公里补起来。

这条路径很说明问题。OpenStock 不是把金融信息摆进页面，而是在尝试把用户画像、持久化状态、后台检测和异步触达串成一条能持续运行的产品链。链路已经成形，只是不同节点的成熟度并不一样。

## 体验、自托管、二开，是 3 条不同的路

很多开源产品文章喜欢把“在线体验”“Docker 跑起来”和“继续开发”写成同一段。这会让读者误判自己真正需要什么。OpenStock 更适合拆开来看。

### 只想体验产品

在线 Demo 在 [openstock-ods.vercel.app](https://openstock-ods.vercel.app/)。当前公开入口默认就是登录流程，所以它更适合感受完成度，而不是替代源码阅读。你能比较快看到认证、命令面板、股票搜索和整体视觉风格，但看不出工作流到底挂了哪些任务。

### 想把它先跑起来

README 给出的最短路径仍然是 Docker：

```bash
git clone https://github.com/Open-Dev-Society/OpenStock.git
cd OpenStock
docker compose up -d mongodb && docker compose up -d --build
```

Docker 模式下，MongoDB 连接串要写容器网络里的 `mongodb` 服务名，而不是本机 `localhost`：

```env
MONGODB_URI=mongodb://root:example@mongodb:27017/openstock?authSource=admin
BETTER_AUTH_SECRET=your_better_auth_secret
BETTER_AUTH_URL=http://localhost:3000
NEXT_PUBLIC_FINNHUB_API_KEY=your_finnhub_key
FINNHUB_BASE_URL=https://finnhub.io/api/v1
```

如果你只想确认页面能打开，到这里通常够了。可一旦你希望欢迎邮件、周报或 Inngest 任务也一起工作，还要继续补齐 `NODEMAILER_EMAIL`、`NODEMAILER_PASSWORD`、`INNGEST_SIGNING_KEY`，以及 AI Provider 相关变量。否则你看到的只会是“页面能访问”，而不是“产品链路真的跑起来”。

### 想把它当底座继续开发

这时就别停在 Docker 这一步了，直接切到本地开发路径：

```bash
npm install
npm run test:db
npm run dev
npx inngest-cli@latest dev
```

这里最容易漏的是最后一行。只开 Next.js 不开 Inngest，本地页面照样能访问，但欢迎邮件、周报、提醒检测和召回任务都会像“没实现”一样安静。很多人第一次跑这类项目时，会在这里误判功能状态。如果页面能用、邮件却没到，第一步先确认 `npx inngest-cli@latest dev` 是否真的已经跑起来。

## 真要 fork，先从这些入口读

如果你只有 1 小时，不要先钻 UI 组件。OpenStock 的判断力更多藏在工作流、模型和边界文件里。

| 入口 | 先看什么 | 为什么从这里开始 |
| ------ | ------ | ------ |
| [app/api/inngest/route.ts](https://github.com/Open-Dev-Society/OpenStock/blob/main/app/api/inngest/route.ts) | 注册了哪些 Inngest 函数 | 最快看清系统到底把哪些事交给后台 |
| [lib/inngest/functions.ts](https://github.com/Open-Dev-Society/OpenStock/blob/main/lib/inngest/functions.ts) | cron、邮件、价格提醒、召回任务的真实状态 | README 与当前实现的差异基本都在这里暴露 |
| [lib/actions/auth.actions.ts](https://github.com/Open-Dev-Society/OpenStock/blob/main/lib/actions/auth.actions.ts) | 注册事件、登录后的 `lastActiveAt` 更新 | 看用户状态如何进入后续工作流 |
| [database/models/watchlist.model.ts](https://github.com/Open-Dev-Society/OpenStock/blob/main/database/models/watchlist.model.ts) | 联合唯一索引 | 看 watchlist 是不是认真持久化的数据 |
| [database/models/alert.model.ts](https://github.com/Open-Dev-Society/OpenStock/blob/main/database/models/alert.model.ts) | 提醒条件、过期时间、触发字段 | 看提醒规则目前能支撑到什么程度 |
| [app/(auth)/sign-up/page.tsx](https://github.com/Open-Dev-Society/OpenStock/blob/main/app/%28auth%29/sign-up/page.tsx) | onboarding 收集了哪些偏好 | 看“个性化”是不是停在 README 里 |
| [middleware/index.ts](https://github.com/Open-Dev-Society/OpenStock/blob/main/middleware/index.ts) | 受保护路由的范围 | 看它更像公开站点还是登录后工作台 |

先看产品骨架，再看页面细节。这样很多“这个项目到底成熟到哪一步”的问题，不用跑完整站也能判断出来。

## 最值得抄回自己项目的 5 个取舍

### 1. 先借成熟服务，把范围守住

Finnhub 和 TradingView 让项目绕开了最重的数据与图表基础设施。OpenStock 并没有因此显得“轻”，反而更像一个知道自己预算和边界的产品。对个人开发者和小团队来说，这通常比从零造行情系统更现实。

### 2. 让注册就产出长期可用的用户画像

很多项目的 onboarding 只是视觉装饰。OpenStock 把国家、投资目标、风险偏好和偏好行业直接接进 `app/user.created` 事件，使这些字段马上可用于欢迎邮件和后续个性化。这一步做早了，后面的工作流才有东西可用。

### 3. 把后台任务接在真实用户路径上

欢迎邮件、周报、提醒检测和召回都不是“展示自己用了 Inngest”的装饰。它们直接服务留存和回访，这是项目比教程更像产品的地方。

### 4. AI 放在增强层，而不是放进同步主路径

欢迎邮件和新闻摘要可以受益于 LLM，但搜索、登录、watchlist 和图表不能靠模型兜底。OpenStock 的当前分层基本守住了这条线，而且 API 文档已经明确强调模型路由与 fallback。这个位置摆得对，系统才不容易因为 AI 抖动把基础体验一起拖垮。

更重要的是，这个 fallback 不是写在 README 里的抽象承诺。`lib/ai-provider.ts` 当前默认以 Gemini 为主，失败后优先切到 MiniMax；若存在 Siray 的 key，也会把 Siray 纳入回退路径。对欢迎邮件和新闻摘要这类异步任务来说，这种设计比“只绑一个模型”更接近可运行系统。

### 5. 把许可证和部署约束当成架构的一部分

OpenStock 用的是 AGPL-3.0。只要你改了之后继续以网络服务形式部署，就要认真处理源码开放义务。再加上 SMTP、Kit、Inngest Signing Key 和第三方数据源条款，这不是“上线前再补文档”的问题，而是产品路线早期就该算进去的成本。

## 常见误判

### 它能不能替代 TradingView、Bloomberg 或专业终端

不能。它更像“开源股票工作台”，不是“专业终端替代品”。如果你要低延迟行情、深度盘口、订单执行、合规审计和明确的数据授权，当前公开实现远远不够。

### 价格提醒现在是不是已经能稳定发出去

还不能这么说。源码已经做到了定时检测、阈值判断和状态更新，但提醒送达的最后一公里还没完全补齐。把“检测到命中”写成“完整通知系统”会高估当前完成度。

### AI 是不是系统不可或缺的一层

不是。模型主要用在欢迎邮件和新闻摘要。哪怕 AI Provider 挂掉，登录、搜索、股票详情和 watchlist 这些基础能力仍然能继续工作。

### 它能不能直接拿来做自己的 SaaS

如果你的目标是个人投资工作台、轻量观察列表、邮件周报或开源产品模板，可以。如果你想承诺强实时、复杂告警策略、生产级运营后台或金融合规能力，当前实现还只是起点。

## 真要二开，顺序最好这样排

1. 先重新审视数据入口，决定是否继续单押 Finnhub，还是改成多源聚合。
2. 再补通知链路，把“检测到了”真正变成“稳定送达了”，否则 alerts 很难成为可靠卖点。
3. 然后扩展用户模型，把 watchlist 和基础偏好推进到组合、持仓、收益归因或更细的提醒规则。
4. 最后再谈首页布局、主题切换和图表样式。表层视觉改得再快，也替代不了数据和工作流的底层判断。

这个顺序的好处很现实。先把会影响产品可信度的链路补齐，再处理看得见的界面，返工最少。

## 相关资料

- [OpenStock GitHub 仓库](https://github.com/Open-Dev-Society/OpenStock)
- [项目 README](https://github.com/Open-Dev-Society/OpenStock/blob/main/README.md)
- [API 与架构文档](https://github.com/Open-Dev-Society/OpenStock/blob/main/API_DOCS.md)
- [在线 Demo](https://openstock-ods.vercel.app/)
- [Adrian Hajdin 的原始教程背景](https://www.youtube.com/watch?v=gu4pafNCXng)

## 最后该怎么判断 OpenStock

如果你把 OpenStock 当成“开源版 Bloomberg”来看，大概率会失望；如果你把它当成一套把股票搜索、自选股、用户画像、价格提醒、市场周报和部署链路接起来的产品样板，它就很有研究价值。

它最值得学的，不是某个图表组件有多炫，而是这些东西怎么被编排到一起：外部数据服务负责行情与图表，Better Auth 和 MongoDB 负责长期状态，Inngest 负责把欢迎邮件、提醒检测和周报这类慢任务从同步页面里拆出去。继续往里拆，会发现 OpenStock 留下的不是“功能很多”，而是“骨架已经立住了”。

对独立开发者和轻量产品团队来说，这个骨架已经足够值得 fork；对想做专业终端的人，它更像一份边界清楚的参考答案，而不是终局方案。
