+++
date = '2026-05-28T00:00:01+08:00'
draft = false
title = 'Openstock Open Source Stock Market Platform'
+++

title: "OpenStock：一个开源股票工作台，怎么把查询、自选股和邮件摘要串起来"
date: "2026-05-27T09:25:00+08:00"
slug: "openstock-open-source-stock-market-platform"
description: "OpenStock 的关键不在图表，而在于把外部行情、用户状态和异步通知接成一套能长期使用的股票工作台。"
draft: false
categories: ["技术笔记"]
tags: ["开源", "股票", "Next.js", "MongoDB", "Inngest", "自托管"]
---

<!-- markdownlint-disable-file MD003 MD041 -->

OpenStock 的看点，不在于又做了一层股票图表，而在于它把现成的行情源、嵌入式图表、账户体系、自选股、邮件工作流和 Docker 自部署接成了一套能长期使用的个人股票工作台。顺着公开 README 和仓库结构往下看，它更像一个“教程型 stock app 继续产品化”的样本，而不是要正面挑战专业交易终端的金融基础设施项目。

如果你只想先下判断，先记住 4 句：

- 底层行情与图表主要交给 Finnhub 和 TradingView，OpenStock 自己重点做的是用户状态、产品流程和异步通知。
- AI 不是系统主路径，它更多放在欢迎邮件、周摘要和提醒检测这类异步边缘环节。
- 项目完成度已经超过“能查一只股票”的演示页，因为登录、自选股列表、个性化引导（onboarding）、邮件触达和自部署都已经接上。
- 如果你要把它当底座，最该看的不是首页样式，而是数据入口、用户模型、工作流和许可证边界。

读这篇文章时，最好一直带着 3 个问题往下看：

- OpenStock 到底哪些能力是自己实现的，哪些只是把第三方服务接得更顺？
- Inngest、邮件和 LLM 在这套系统里是“加分项”，还是已经变成主路径依赖？
- 它什么时候适合当开源产品模板，什么时候又不该被误判成专业市场终端？

## 它更像产品化工作台，不像专业终端替代品

截至 2026 年 5 月 27 日，OpenStock 的 GitHub 公共页显示约 12.3k Stars、1.6k Forks，许可证为 AGPL-3.0，最近一次公开提交距今约 3 周。这个热度说明它已经不是刚发布的玩具项目，但热度本身并不能替你做产品判断。

README 顶部把 OpenStock 描述成 expensive market platforms 的开源替代品。这个说法很抓人，但真正落到工程判断时，最好把宣传语和已公开实现分开看。继续往源码里走，会看到两个很重要的事实。第一，alerts 不只是 marketing 文案：`database/models/alert.model.ts`、`lib/actions/alert.actions.ts`、`app/(root)/watchlist/page.tsx` 和 `lib/inngest/functions.ts` 已经接出了一条“创建价格提醒、5 分钟轮询价格、命中后标记触发”的基础链路。第二，README 仍然写着按 watchlist 的每日新闻摘要，但当前 `app/api/inngest/route.ts`、`lib/inngest/functions.ts` 和 `API_DOCS.md` 暴露出来的实现，已经是每周一上午 9 点抓取通用市场新闻并通过 Kit 广播的 `weekly-news-summary`。也就是说，这个项目确实在做主动触达，但 README 和当前源码在摘要节奏、个性化范围和告警成熟度上已经不完全同步。

README 里还有一个很重要的线索：项目专门感谢了 Adrian Hajdin 的 stock market app tutorial。这个信息不该被当成“只是教程改皮肤”，恰恰相反，它解释了 OpenStock 最值得看的地方不在 dashboard 的视觉层，而在于它怎样把教程里常见的股票展示面，继续推进成一个能注册、能保存、能发信、能部署、能长期回访的产品。

## 系统地图：先看清 3 条主线

| 主线 | 负责什么 | 关键依赖 | OpenStock 自己补上的部分 |
| ------ | ------ | ------ | ------ |
| 数据与展示 | 搜索股票、查看个股详情、市场概览、图表与热力图 | Finnhub、TradingView、可选 Adanos 情绪卡 | 把查询入口、详情页和界面结构组织成能用的产品页面 |
| 账户与个性化 | 登录、会话保护、自选股、用户偏好 | Better Auth、MongoDB、Next.js 中间件（middleware） | 把匿名只读面板改造成有长期用户状态的工作台 |
| 自动化与通知 | 欢迎邮件、价格提醒、周摘要、用户召回、定时任务 | Inngest、Nodemailer、Kit、可选 Gemini / MiniMax / Siray | 让产品不只会展示页面，还能异步欢迎、检测和周期触达 |

先把这张表记住，后面读细节时就不容易把第三方数据能力、OpenStock 的产品包装，以及 AI 工作流混成一团。

## 别把它误读成“自建行情系统”

这类项目最容易写偏的地方，就是把“接入得很完整”误写成“基础设施是自己造的”。OpenStock 的边界其实很清楚：

| 能力 | 公开资料能确认的实现方式 | 应该怎么理解 |
| ------ | ------ | ------ |
| 股票搜索、公司资料、市场新闻 | Finnhub API | 这是项目的数据入口，不是自建证券数据管线 |
| 图表、热力图、报价、时间线 | TradingView 嵌入式组件（widgets） | 页面观感完整，不等于项目自带一套图表引擎 |
| 情绪洞察 | 可选 Adanos 情绪卡 | 是补充信号，不是主数据源 |
| 登录、会话、受保护路由 | Better Auth + MongoDB + 中间件（middleware） | 这是 OpenStock 真正做深的产品层能力之一 |
| watchlist 与用户画像 | MongoDB 持久化 + 业务规则 | 决定它能不能从 demo 变成长期工作台 |
| 欢迎邮件、周摘要、价格提醒、用户召回 | Inngest + Nodemailer + Kit + 可选 LLM Provider | 这是自动化层，不是页面主链路 |

这个边界一旦看清，项目的真实价值就会更容易判断。OpenStock 并没有去重做行情抓取、证券主数据清洗、低延迟分发或自研图表内核，它把开发预算花在了更接近“产品能不能长期被使用”的那几步上。

## 主线一：数据面看起来像终端，骨子里还是工作台

OpenStock 的数据层并不神秘。Finnhub 负责股票搜索、公司资料和市场新闻，TradingView 负责最显眼的图表和市场概览，Adanos 则作为可选情绪补充。这样的组合很现实：先用成熟供应商补齐查询和可视化，再把精力放到真正能区分产品层完成度的部分。

这也是为什么你打开它的个股详情页，会觉得“像个完整的股票产品”，但仔细读 README，又会发现项目自己承担的主要不是行情基础设施，而是页面组织、信息拼装和用户上下文。对独立开发者或小团队来说，这种取舍并不保守，反而更务实。做一套证券数据基础设施是另一场战争，做一套让用户愿意反复回来用的工作台，又是另一场战争。

约束也必须说清。Finnhub 免费层通常伴随延迟数据和配额限制，所以“real-time prices”这类表述离不开具体套餐和部署配置。你可以用它做个人工作台、学习项目或轻量产品原型，但如果目标是低延迟专业终端、深度盘口或交易级行情分发，那已经走到了 OpenStock 当前公开实现之外。

## 主线二：真正把它从 demo 拉成产品的，是账户和用户状态

很多开源股票项目停在“首页能搜股票、能看卡片”的阶段。OpenStock 往前多走了一步，关键不在视觉，而在状态。

这部分并不只是 README 里的口头承诺。`app/(auth)/sign-up/page.tsx` 的注册表单真的收了 `country`、`investmentGoals`、`riskTolerance` 和 `preferredIndustry`；`lib/actions/auth.actions.ts` 在创建账号后，会把这些字段连同 `email`、`name` 一起作为 `app/user.created` 事件发给 Inngest；`middleware/index.ts` 的 `matcher` 明确把 `sign-in`、`sign-up`、`forgot-password`、`reset-password`、`assets` 和 Next 内部资源排除在保护之外，其余主体页面走受保护路由。单看每一项都不复杂，合在一起，性质就变了。它不再是一个匿名访客随便打开看看就走的页面，而是一个会记住“你是谁、你偏好什么、后续该把什么信息推给你”的应用。

watchlist 也不是一层纯前端状态。`database/models/watchlist.model.ts` 用 `WatchlistSchema.index({ userId: 1, symbol: 1 }, { unique: true })` 硬性防止同一用户重复加入同一 symbol；`app/(root)/watchlist/page.tsx` 则把 `getUserWatchlist`、`getUserAlerts` 和 `getNews` 并行拉起，再把 `AlertsPanel` 和 `NewsGrid` 拼到同一页。这样一来，个性化 onboarding、长期用户状态、自选股和提醒面板就在页面层、动作层和数据层闭合了第一圈。

## 主线三：Inngest、邮件和 AI 没有喧宾夺主

OpenStock 接了 Inngest，也接了 LLM Provider，但源码里真正值得看的，是这条异步平面已经不止一封欢迎邮件。

当前 `app/api/inngest/route.ts` 注册了 4 个函数：`sendSignUpEmail`、`sendWeeklyNewsSummary`、`checkStockAlerts` 和 `checkInactiveUsers`。其中 `sendSignUpEmail` 由 `app/user.created` 触发，`lib/inngest/functions.ts` 会把注册阶段收集到的国家、投资目标、风险偏好和偏好行业拼成 `userProfile`，再喂给 `PERSONALIZED_WELCOME_EMAIL_PROMPT`，最后通过 `sendWelcomeEmail` 发欢迎邮件。这条链路已经把 onboarding 和 AI 个性化真正接上了。

但新闻摘要这条线，已经和 README 的描述出现了偏移。当前代码里的 `sendWeeklyNewsSummary` 用的是 `0 9 * * 1`，也就是每周一上午 9 点；它抓的是通用市场新闻的最新 10 条，不是按每个用户 watchlist 做逐人摘要；投递也不是逐封 Nodemailer，而是通过 Kit 做广播。换句话说，源码里的这条链路更像“周报型市场广播”，而不是“按 watchlist 定制的日报”。

alerts 这一层也比 README 暗示得更具体，但还没有完全闭环。`checkStockAlerts` 每 5 分钟跑一次，拉活跃提醒、抓最新价格、按 `ABOVE` / `BELOW` 条件判断是否命中，命中后会把 alert 标记成 `triggered: true` 和 `active: false`。不过函数体里的注释也写得很直白：当前公开实现把“检测和状态迁移”做实了，真正的提醒投递路径还没有完全补满。再加上 `checkInactiveUsers` 这条每日 10 点的召回任务，OpenStock 的自动化层已经不只是“有 AI”这么简单，而是正在朝完整的后台工作流系统长。

从工程角度看，这样分层有两个直接好处。第一，行情查询、登录、watchlist 持久化这些基础动作不需要依赖模型响应才能成立，系统主路径更稳。第二，AI 能力、邮件模板、广播和 cron 任务都能沿着 Inngest 这条异步平面演进，页面本身不必承担太多慢调用和失败恢复逻辑。更直白一点说：在 OpenStock 里，AI 现在负责“把已有信息组织得更像产品”，而不是“替代整个产品本身”。这就是它该在的位置。

## 一条真实用户路径：从注册到触发提醒

静态地看模块，容易觉得它们只是几个功能点。把它们放回源码里已经存在的路径，项目的产品意味就出来了。

1. 用户在 `app/(auth)/sign-up/page.tsx` 提交注册表单，同时填入国家、投资目标、风险偏好和偏好行业。
2. `lib/actions/auth.actions.ts` 创建账号后，立刻发送 `app/user.created` 事件，把这些字段交给 Inngest。
3. `sendSignUpEmail` 根据这组用户画像调用模型生成欢迎内容，再通过 `sendWelcomeEmail` 发出个性化欢迎邮件。
4. 用户把股票加入 watchlist；`database/models/watchlist.model.ts` 的联合唯一索引保证不会把同一 symbol 重复塞进同一用户列表。
5. 用户在 watchlist 页面创建 `ABOVE` 或 `BELOW` 价格提醒；`app/(root)/watchlist/page.tsx` 同时把自选股、提醒和新闻拉进同一工作台。
6. `checkStockAlerts` 每 5 分钟抓一次最新价格，命中阈值后把该提醒标记为已触发并停用。

这条链路说明 OpenStock 的核心不是把金融信息塞进几张页面，而是把“注册画像、长期状态、提醒检测、异步触达”接成一个真正可运行的闭环。需要额外记住的是：周摘要也确实存在，但当前公开实现更接近一条面向订阅者的市场周报广播，而不是逐用户的 watchlist 日报。

## 读源码时，先顺着这几处入口看

如果你要继续开发，不建议一上来就扎进某个 UI 组件。先看产品骨架会快得多。

| 入口 | 你会看到什么 | 为什么先看 |
| ------ | ------ | ------ |
| `app/` | 注册页、watchlist、个股详情页、API docs、Inngest 路由 | 页面流转、功能入口和对外叙事都从这里开始 |
| `middleware/` | 受保护路由的 `matcher` | 判断哪些页面必须登录、哪些是公共入口 |
| `database/` | Mongoose 连接、watchlist 和 alert 模型 | 看清哪些状态会长期保存 |
| `lib/actions/` | auth、watchlist、alert、finnhub、user 相关动作 | 这是业务边界最集中的位置 |
| `lib/inngest/` | `sign-up-email`、`weekly-news-summary`、`check-stock-alerts`、`check-inactive-users` | 这里最能看出 README 和当前实现的差异 |
| `lib/nodemailer/`、`lib/kit` 与 `app/api/inngest/route.ts` | 欢迎邮件、周摘要广播和工作流注册 | 方便把投递通道一口气读通 |

如果你只读一小时，先把这 6 个入口过一遍，比从组件目录漫游高效得多。

## 体验它和改它，是两条不同的路

OpenStock 既能当产品体验，也能当源码样本来看，但这两条路径不要混在一起。

### 只想体验，或者先把它跑起来

线上 Demo 在 [openstock-ods.vercel.app](https://openstock-ods.vercel.app/)。当前公开入口默认就是登录页，所以它更适合感受成品形态，不适合替代源码阅读。

README 里给出的最短自托管路径是 Docker：

```bash
git clone https://github.com/Open-Dev-Society/OpenStock.git
cd OpenStock
docker compose up -d mongodb && docker compose up -d --build
```

Docker 模式下，MongoDB 连接串不是本机 `localhost`，而是容器网络里的服务名：

```env
MONGODB_URI=mongodb://root:example@mongodb:27017/openstock?authSource=admin
BETTER_AUTH_SECRET=your_better_auth_secret
BETTER_AUTH_URL=http://localhost:3000
NEXT_PUBLIC_FINNHUB_API_KEY=your_finnhub_key
FINNHUB_BASE_URL=https://finnhub.io/api/v1
```

如果你还想把欢迎邮件、周摘要和其他 Inngest 任务也一并跑起来，就要继续补齐 `NODEMAILER_EMAIL`、`NODEMAILER_PASSWORD`，以及在 Vercel 场景下的 `INNGEST_SIGNING_KEY`。这几个变量决定了项目能不能从“页面能打开”走到“工作流真的会跑”。

### 想读源码、继续开发，或者改成自己的产品

如果你的目标是二次开发，就别停在 Docker 这一步，直接切到本地开发模式：

```bash
npm install
npm run test:db
npm run dev
npx inngest-cli@latest dev
```

`pnpm` 也可用，但不管你选哪个包管理器，真正值得尽快跑通的是数据库检查、Next.js 开发服务和 Inngest 本地工作流。只有这三段都起来了，你才能判断 OpenStock 的核心体验到底是页面优先，还是工作流优先。

## 这套项目里，有 4 个工程取舍特别值得学

### 1. 先借成熟服务，把产品面做完整

Finnhub 和 TradingView 让项目绕开了最重的行情与图表基础设施。对资源有限的团队来说，这不是偷懒，而是把时间花在更有区分度的地方。

### 2. 用户状态先于花哨功能

watchlist、onboarding、受保护路由和持久化模型，决定的是用户第二次回来时系统还记不记得他。很多 demo 没有第二次使用价值，问题就出在这里。

### 3. 异步工作流直接接在用户路径上

欢迎邮件、周摘要、价格提醒和用户召回都不是“展示技术栈存在感”的附加品，它们直接关系到留存和回访。Inngest 在这里接的是产品动作，不只是后台任务。

### 4. AI 放在增强层，而不是主路径

OpenStock 目前公开出来的 AI 用法集中在欢迎邮件、摘要生成和 Provider 抽象。这个位置很克制，也很对。页面能不能用，不该由模型是否可用来决定。

## 二次开发前，先把这些现实约束看清楚

1. Finnhub 免费层的延迟和配额限制，决定了它更适合个人工作台和原型，而不是专业终端级实时系统。
2. TradingView widget 带来的是成熟图表体验，不是项目自带的可完全掌控图表内核；你未来想深改交互时，会碰到第三方边界。
3. README 与当前源码已经有轻微漂移，最明显的是“按 watchlist 的每日摘要”在代码里已经表现成“通用市场新闻的每周广播”；写文章或做二开方案时不能只看 README。
4. OpenStock 是 AGPL-3.0。只要你修改后继续以网络服务形式部署，就要认真处理源码开放义务，不能等上线前再想起这件事。
5. 邮件、Inngest 和 AI Provider 这几段一旦接进生产环境，运维问题就不只是“应用能启动”这么简单，还包括签名、Kit/SMTP 凭证、任务失败恢复，以及提醒“检测到了”之后到底怎么把消息可靠送出去。

## 如果你准备把它改成自己的产品，优先动这 4 处

1. 先重看数据入口。顺着 `lib/actions/` 把搜索、公司资料、新闻获取这条线读通，再决定是否继续用 Finnhub，还是做多源聚合。
2. 再升级通知链路。`lib/inngest/`、`lib/nodemailer/` 和 `lib/kit` 决定了产品能不能从“用户自己打开看”变成“系统按条件主动推送”。如果你想做逐用户日报、真正发得出去的价格提醒、行业观察或组合周报，这一层会比首页 UI 更早变成瓶颈。
3. 然后扩展用户模型。当前项目更偏 watchlist 和偏好驱动的工作台；如果你要做组合、持仓、收益归因、提醒规则，就必须把 `database/` 里的模型再往前推一层。
4. 最后再谈终端化改造。等数据入口、通知策略和用户模型都清楚了，再去改首页布局、图表主题、热力图样式，才不容易把时间浪费在表面层。

## 适合谁，不适合谁

OpenStock 适合下面几类人：

- 你想搭一套可自托管的个人股票工作台，而不是把所有数据和界面都交给封闭平台。
- 你想研究一个由 Next.js 15、React 19、Better Auth、MongoDB、Inngest 和第三方金融数据服务拼起来的完整 Web 产品。
- 你准备在现有基础上继续加自己的信号源、邮件模板、筛选逻辑、观察列表或轻量策略面板。

它不太适合下面这些场景：

- 你需要专业终端级的低延迟行情、深度盘口和明确的商业数据授权。
- 你要做高频、自动交易执行或券商级别的订单流系统。
- 你需要严格的金融合规审计、券商集成和生产级 SLA。

README 也写得很直白：它不是 brokerage，市场数据可能因为供应商规则和部署配置而延迟，页面内容也不是投资建议。把这条边界记住，后面对项目的期待会更稳。

## 最后该把它当成什么

如果把 OpenStock 当成“开源版 Bloomberg”去看，你大概率会失望；如果把它当成一套把股票搜索、自选股、用户画像、价格提醒、周摘要、邮件触达和部署链路接起来的产品样板，它就立刻变得很有价值。

这套项目最值得学的，不是某个图表组件有多炫，而是它怎样把外部数据服务、用户状态和异步通知接成一个能长期使用的 Web 产品。先看账号、数据、通知怎么连起来，再看 AI 被放在哪，你会更容易判断它适不适合做自己下一版产品的底座。

如果你准备继续往下拆，下一步最稳的顺序仍然是：先读 [GitHub README](https://github.com/Open-Dev-Society/OpenStock)，再跑一遍 Docker 或本地开发环境，最后沿着 `app/`、`middleware/`、`database/`、`lib/actions/`、`lib/inngest/` 这几条线把代码读通。到了这一步，OpenStock 对你来说就不再只是一个“看起来不错的开源项目”，而是一套能不能接到你自己产品上的清晰判断。
