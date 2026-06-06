+++
date = '2026-05-26T23:00:00+08:00'
draft = false
title = 'OpenStock：不只是免费行情看板，更是一套可自部署的股市数据中台'
slug = 'open-stock-free-market-platform-guide'
description = 'OpenStock 用 Next.js 15 + MongoDB + Inngest + Gemini 搭了一套完整的股市数据平台，集认证、AI 邮件自动化、多源舆情分析和 Docker 部署于一体。'
categories = ['技术笔记']
tags = ['金融', '开源', 'AI', 'Next.js']
+++

## 目录

- [OpenStock 解决什么，不解决什么](#openstock-解决什么不解决什么)
- [系统地图：从用户注册到每日新闻推送](#系统地图从用户注册到每日新闻推送)
- [技术栈拆解](#技术栈拆解)
- [认证与用户系统](#认证与用户系统)
- [数据管线：多源行情与舆情聚合](#数据管线多源行情与舆情聚合)
- [AI 自动化：Inngest 工作流引擎](#ai-自动化inngest-工作流引擎)
- [部署指南](#部署指南)
- [适用边界与决策建议](#适用边界与决策建议)
- [常见问题](#常见问题)
- [结语](#结语)

---

## OpenStock 解决什么，不解决什么

[OpenStock](https://github.com/Open-Dev-Society/OpenStock) 常被拿来和 TradingView、Yahoo Finance 对比——它确实提供了类似的行情看板和图表，但把它定位成「免费版 TradingView」就低估了它的实际能力。

OpenStock 真正做的，是**把行情数据、用户认证、个性化监控、AI 邮件推送、多源舆情聚合整合成一套可自部署的平台**。它不是替换你的交易终端，而是替换你散落在 5 个页面上的数据聚合链路。

具体来说，它解决的是：

- 一个地方看行情、图表、新闻、舆情，不用在不同产品之间切来切去
- 自选股列表和价格提醒需要持久化，不能每次打开浏览器都重新输入
- 每天想收到一封基于自选股定制的市场摘要邮件，而不是通用的新闻推送
- 数据源要可控——知道数据从哪来、延迟多长、免费额度够不够

它不解决的是：

- 实时交易下单（OpenStock 不是券商，不接交易 API）
- 深度基本面分析（PE/PB/ROE 等财务指标不在当前版本范围内）
- 毫秒级行情（Finnhub 免费层延迟 15 分钟，付费层可到实时）

---

## 系统地图：从用户注册到每日新闻推送

在拆模块之前，先看一条完整的用户路径，理解各组件之间的关系：

```
用户注册
  → Better Auth 创建账号，写入 MongoDB
  → Inngest 触发 user.created 事件
  → Gemini 生成个性化欢迎邮件，Nodemailer 发送

日常使用
  → 用户登录，通过搜索栏（Command+K）查找股票
  → Finnhub API 返回股票代码、公司信息
  → 用户将股票加入自选股列表（MongoDB 持久化）
  → 详情页加载 TradingView 图表 + Adanos 舆情卡片

每日推送
  → Inngest Cron 每天 12:00 UTC 触发
  → 遍历每个用户的自选股列表
  → 聚合 Finnhub 新闻 + 行情数据
  → 通过 Nodemailer 发送个性化摘要邮件
```

这条路径里，Inngest 是连接 AI 和用户的桥梁——没有它，AI 生成的欢迎邮件和每日新闻摘要就只是一段没人跑的代码。

---

## 技术栈拆解

OpenStock 的技术选型，每一层都有明确的取舍理由，而不是「用最新框架」的堆砌。

### 前端

| 选型 | 角色 | 为什么选它 |
|---|---|---|
| Next.js 15 (App Router) | 全栈框架 | SSR 对 SEO 友好；App Router 的 Server Actions 让数据获取逻辑留在服务端 |
| React 19 | UI 层 | 最新稳定版，Concurrent 特性对复杂图表渲染有帮助 |
| Tailwind CSS v4 | 样式 | v4 使用 CSS-first 配置，不再需要 tailwind.config.js |
| shadcn/ui + Radix UI | 组件库 | 可复制源码的组件，不依赖 npm 包，定制自由度高 |
| cmdk | 命令面板 | Command+K 快速搜索股票，体验对标 Linear/Raycast |

### 后端与数据

| 选型 | 角色 | 为什么选它 |
|---|---|---|
| Better Auth | 认证 | 比 NextAuth v5 更轻量，MongoDB adapter 开箱即用 |
| MongoDB + Mongoose | 存储 | 用户数据、自选股列表、配置偏好，Schema 灵活 |
| Finnhub | 行情数据 | 免费层覆盖股票搜索、公司信息、市场新闻，够用 |
| TradingView | 图表 | 嵌入式 Widget，K 线图、热力图、市场概览一行 iframe 搞定 |
| Adanos | 舆情分析 | 聚合 Reddit、X.com、新闻、Polymarket 的情绪数据 |

### 自动化与 AI

| 选型 | 角色 | 为什么选它 |
|---|---|---|
| Inngest | 工作流引擎 | 事件驱动 + Cron 定时，比手动写 Cron Job 更可靠，带重试和可观测性 |
| Gemini | AI 内容生成 | 生成个性化欢迎邮件；可通过 `AI_PROVIDER` 切换 MiniMax/Siray |
| Nodemailer | 邮件发送 | 通过 Gmail SMTP 发送，生产环境建议换专用 SMTP 服务 |

---

## 认证与用户系统

OpenStock 的认证设计比大多数「登录即用」的看板工具更完善。它用 Better Auth 做邮箱密码认证，通过 Next.js middleware 保护路由——`sign-in` 和 `sign-up` 页面公开，其余所有页面需要登录后才能访问。

用户注册时，系统收集的不只是邮箱和密码，还包括：

- 所在国家（影响市场数据默认展示）
- 投资目标（长期持有 / 短线交易 / 分红收益）
- 风险承受能力（保守 / 稳健 / 激进）
- 偏好行业（科技 / 金融 / 医疗 / 能源等）

这些数据不是摆设——注册完成后，Inngest 触发 `user.created` 事件，Gemini 根据用户的投资偏好生成一封个性化的欢迎邮件。一个倾向于长期持有科技股的投资者和一个偏好分红收益的保守型投资者，收到的欢迎邮件内容完全不同。

---

## 数据管线：多源行情与舆情聚合

### Finnhub：行情数据主力

Finnhub 是 OpenStock 的行情数据主力源，覆盖：

- 股票搜索（symbol lookup）——支撑 Command+K 搜索和自选股添加
- 公司信息（company profile）——股票详情页的公司概览
- 市场新闻（market news）——每日新闻摘要的素材来源

Finnhub 免费层限制：每分钟 60 次 API 调用，行情数据延迟约 15 分钟。对于个人投资者的日常查看来说够用，但如果你需要实时行情，需要升级到付费层（$99/月起）。

### TradingView：图表与市场概览

OpenStock 不自己画 K 线图——它嵌入 TradingView Widget。这种方式有几个好处：

1. 图表交互（缩放、拖拽、切换时间周期）由 TradingView 处理，开发量几乎为零
2. 热力图（Heatmap）和市场概览（Market Overview）同样是 Widget 嵌入
3. 不需要维护行情数据的 WebSocket 连接

代价是自定义程度受限——你不能在图表上叠加自己的指标或标注，图表的样式和交互也受 TradingView 的约束。

### Adanos：舆情情绪聚合

这是 OpenStock 区别于其他行情看板的一个亮点。Adanos 提供的不是传统的新闻标题列表，而是**结构化的情绪快照**——按来源（Reddit、X.com、新闻、Polymarket）分别给出正面/负面/中性的情绪占比。

对于 A 股投资者来说，Polymarket 的数据可能不太相关；但对于跟踪美股事件驱动的投资者，Adanos 的情绪数据能提供比新闻标题更直观的信号——Reddit 上的散户情绪和 Polymarket 的预测市场定价，往往是新闻媒体之前的价格发现来源。

---

## AI 自动化：Inngest 工作流引擎

OpenStock 的自动化层跑在 Inngest 上，而不是传统的 `node-cron` 或 GitHub Actions。这个选择在工程上值得拆开看。

### 为什么是 Inngest

自建 Cron Job 的常见问题：任务失败后没有重试、执行日志散落在服务器日志里、多个任务之间的依赖关系需要手动管理。Inngest 解决了这三件事：

- **事件驱动**：用户注册触发 `user.created` 事件 → 自动执行欢迎邮件工作流
- **Cron 定时**：`0 12 * * *` 每天中午触发新闻摘要生成
- **内置重试**：工作流失败自动重试，带指数退避
- **可观测性**：Inngest Dashboard 可以看到每次工作流执行的输入、输出和耗时

### 两个核心工作流

**1. 欢迎邮件工作流**

```mermaid
flowchart LR
    A[用户注册] --> B[user.created 事件]
    B --> C[读取用户偏好]
    C --> D[Gemini 生成个性化欢迎内容]
    D --> E[Nodemailer 发送邮件]
```

注册时收集的投资目标、风险偏好、偏好行业，全部作为 Prompt 输入传给 Gemini。生成的邮件内容不是模板填空，而是真正的个性化文本——这就是为什么系统需要 Gemini 而不是简单的字符串替换。

**2. 每日新闻摘要工作流**

```mermaid
flowchart LR
    A[Cron 12:00 UTC] --> B[遍历所有用户]
    B --> C[读取用户自选股列表]
    C --> D[Finnhub 获取新闻+行情]
    D --> E[组装摘要邮件]
    E --> F[Nodemailer 发送]
```

每个用户收到的摘要邮件基于自己的自选股列表生成，不是群发同一封。这个设计在用户量小的时候没问题，但如果用户量增长到几千人，每封邮件独立拉取 Finnhub 数据会触发 API 速率限制——这是目前未解决但可以预见的扩展瓶颈。

---

## 部署指南

### 环境准备

- Node.js 20+
- MongoDB（本地 Docker 或 MongoDB Atlas）
- Finnhub API Key（[免费注册](https://finnhub.io/)）
- Gmail 账号（用于邮件发送）
- Gemini API Key（可选，用于 AI 欢迎邮件）

### 方式一：Docker Compose（推荐）

```bash
git clone https://github.com/Open-Dev-Society/OpenStock.git
cd OpenStock

# 创建 .env 文件（参考下方环境变量）
cp .env.example .env

# 启动 MongoDB + 应用
docker compose up -d mongodb && docker compose up -d --build
```

访问 `http://localhost:3000`。

### 方式二：本地开发

```bash
git clone https://github.com/Open-Dev-Society/OpenStock.git
cd OpenStock
pnpm install

# 验证数据库连接
pnpm test:db

# 启动 Next.js 开发服务器（Turbopack）
pnpm dev

# 另开终端，启动 Inngest 本地开发服务
npx inngest-cli@latest dev
```

### 关键环境变量

```env
# 数据库（Docker Compose）
MONGODB_URI=mongodb://root:example@mongodb:27017/openstock?authSource=admin

# 数据库（MongoDB Atlas）
# MONGODB_URI=mongodb+srv://<user>:<pass>@<cluster>/<db>?retryWrites=true&w=majority

# 认证
BETTER_AUTH_SECRET=至少32位随机字符串
BETTER_AUTH_URL=http://localhost:3000

# 行情数据
NEXT_PUBLIC_FINNHUB_API_KEY=your_finnhub_key

# AI 邮件（可选）
GEMINI_API_KEY=your_gemini_api_key

# 邮件发送
NODEMAILER_EMAIL=youraddress@gmail.com
NODEMAILER_PASSWORD=your_gmail_app_password
```

Gmail 的 `NODEMAILER_PASSWORD` 需要使用 App Password（应用专用密码），不能直接用登录密码。在 Google 账号设置中开启两步验证后，搜索「App Passwords」即可生成。

---

## 适用边界与决策建议

### 适合的场景

- **个人投资者需要一个统一的行情看板**：一个页面覆盖搜索、图表、自选股、新闻摘要，不用在不同产品之间切换。
- **想自部署、完全掌控数据链路**：AGPL-3.0 许可证允许自部署，甚至可以修改源码。但注意 AGPL-3.0 要求修改后的代码也必须开源。
- **学习 Next.js 15 + MongoDB + Inngest 的实战项目**：代码结构清晰，覆盖认证、数据库、工作流引擎、AI 集成、邮件发送等常见后端场景。

### 不适合的场景

- **需要实时交易下单**：OpenStock 不是券商，不接交易 API。
- **需要深度基本面分析**：Finhub 的免费数据不包含 PE/PB/ROE 等财务指标，需要额外付费或换数据源。
- **需要实时行情（秒级）**：Finnhub 免费层延迟 15 分钟。付费层可到实时，但成本不低。

### 扩展建议

如果你已经跑起来了，以下是几个扩展方向：

1. **换数据源**：Finnhub 免费层数据有限，可以考虑接 Yahoo Finance（`yfinance` Python 库的 Node.js 等价实现）或 Alpha Vantage。
2. **加 AI 分析**：在每日新闻摘要工作流中，把 Finnhub 新闻 + Adanos 舆情数据一起传给 Gemini，生成一段 AI 写的市场分析，而不是纯新闻列表。
3. **自建舆情**：Adanos 是第三方服务，如果担心数据隐私，可以自己接 Reddit API + X API + NewsAPI，在 Inngest 工作流中做聚合。

---

## 常见问题

**Q: 部署后搜索不到股票**

检查 `NEXT_PUBLIC_FINNHUB_API_KEY` 是否正确配置。Finnhub 的免费 Key 需要在 [finnhub.io](https://finnhub.io/) 注册获取。另外，Finnhub 的搜索 API 只支持美股代码（如 AAPL、TSLA），不支持 A 股代码。

**Q: 邮件发不出去**

两步排查：1) 确认 `NODEMAILER_PASSWORD` 使用的是 Gmail App Password 而非登录密码；2) 确认 Gmail 账号已开启两步验证。如果还是不行，检查 Gmail 账号是否触发了「不安全应用」的安全警告。

**Q: 图表加载不出来**

TradingView Widget 的图片域名 `i.ibb.co` 需要加入 `next.config.ts` 的 `images.remotePatterns` 白名单。项目已默认配置，如果你修改了 `next.config.ts`，确认这一条还在。

**Q: 本地开发时 Inngest 工作流不执行**

确认已经运行了 `npx inngest-cli@latest dev`。Inngest 的本地开发需要启动一个独立的 Dev Server，它负责监听事件并触发工作流。如果只启动了 `pnpm dev`，Inngest 工作流不会执行。

**Q: 可以部署到 Vercel 吗**

可以，但需要注意：1) 需要配置 `INNGEST_SIGNING_KEY`（从 Inngest Dashboard 获取）；2) `NEXT_PUBLIC_FINNHUB_API_KEY` 在 Vercel 上需要配置为环境变量；3) MongoDB 需要是公网可访问的（如 MongoDB Atlas）。

---

## 结语

OpenStock 的工程设计值得关注的点不在于「它用了 Next.js 15」，而在于它把认证、数据、自动化、AI 四层串联成了一个完整的用户路径——从注册的那一刻起，系统就开始根据你的投资偏好生成个性化内容，而不是等你手动配置。

如果你在找一个能自部署、数据源可控、带 AI 邮件推送的股市数据平台，OpenStock 是当前开源生态里最接近「开箱即用」的选择。

项目地址：[github.com/Open-Dev-Society/OpenStock](https://github.com/Open-Dev-Society/OpenStock)

---

*本文不构成任何投资建议。OpenStock 不是券商，不提供交易服务。市场数据可能因提供商规则而延迟，请以实际交易平台数据为准。*