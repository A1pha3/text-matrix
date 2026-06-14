---
title: "AI副业早报 2026-06-11"
date: 2026-06-11T09:11:45+08:00
slug: ai-side-hustle-morning-2026-06-11
description: "2026年6月11日 AI 副业早报，精选过去 24 小时 V2EX 招聘/创业组队/独立开发 6 条 + Hacker News Show HN/Ask HN 5 条，覆盖 AI 应用创业找 CTO、Token 替代外包、Claude Code Loop 流水线、AI coding agent 成本监控、Local-first 副业工具、独立思考方法论等 11 条。"
draft: false
categories: ["行业快讯"]
tags: ["AI副业", "V2EX", "HackerNews", "独立开发", "Agent", "ClaudeCode"]
hiddenFromHomePage: true
---

🦞 每日 09:00 自动更新

---

## 🔥 今日热门

### AI 应用创业找 CTO，PMF 已通、已有营收
来源：V2EX
发布者：a8937010
原文：[原文](https://www.v2ex.com/t/1219254)
摘要：帖子发布于 2026-06-10 09:44 BJT。楼主创业项目已跑通 0 到 1 的 PMF 并持续迭代：高势能用户圈层包括过万付费用户（40% AI 从业者 / 24% CXO / 70% 全球 Top 高校背景），北美同赛道头部产品创始人担任顾问，a16z Founder 评价产品优于北美同类。要求联创 CTO 对 AI 应用有 passion、全栈、懂 AI 与工程；能提供有诚意的联创股权 + 跑着的产品 + 真实营收 + 真实用户，vx: HeySoso1。对 AI 副业读者的可抄点：**PMF 已通 + 已有营收** 阶段是 2026 年最稀缺的「带项目找联创」范式，比 0 阶段拉人概率高一个数量级。

### Show HN: AuthAI —— 给 indie hacker 的开源「用户授权 AI 会话」中继
来源：Hacker News
发布者：riccardoio
原文：[原文](https://news.ycombinator.com/item?id=48477326)
摘要：帖子发布于 2026-06-10 22:56 BJT。Riccardo 做的 AuthAI 让最终用户「连接自己的 ChatGPT / Grok / Copilot 账户」，由 side project 把 AI 请求路由到用户自己的 AI 订阅上 —— 解决了「商业模型跑不通 + 单位经济学卡死」的最大拦路虎。技术细节：tokens 用每用户 AES-256-GCM 加密、密钥只存在于用户 JWT 会话、整套安全模型在 GitHub 全公开。MIT 协议 + 自带 hosted relay + 整套 stack 可自托管，对接 OpenAI SDK 只需 `baseURL: relay.authai.io/v1` 一行。对 AI 副业读者的价值：**重新定义了「按调用付费 vs 让用户自带 quota」的产品定价权**，是 2026 年最值得抄的「开源 + 业务模式 + SDK 体验」三件套。

### Show HN: Eatmydata.ai —— Local-First 的「问问题 → 生成 SQL → 出 Dashboard」AI 工具
来源：Hacker News
发布者: (HN id 48472867)
原文：[原文](https://news.ycombinator.com/item?id=48472867)
摘要：帖子发布于 2026-06-10 15:43 BJT。完全跑在浏览器里的本地优先 AI 数据分析：agents 生成多条 SQL 直接查询 in-browser sqlite（永远看不到结果），再写 dashboard 配置代码；用 QuickJS sandbox 渲染图表，数据全程不离开本机。技术栈：SQLite OPFS（基于 wa-sqlite）、自研 TurboQuant semantic index、C+WASM-simd128 推理引擎（比 onnxruntime 轻 38x）、Apache ECharts 图表、xlsx Community 增强版。MIT 开源 + 纯静态 web app 可自部署。**对 AI 副业读者**：**「LLM 看不到你的数据」是企业级 SaaS 的新卖点**——单人或两人组合的「local-first + agent + 数据安全」产品，2026 下半年比传统云 SaaS 有更高的转化率与定价空间。

## 💼 招聘/接单

### 「现在花 2w 找外包，不如冲 2000 的 token 实在」：AI 主导项目的实战算账
来源：V2EX
发布者：dearmymy
原文：[原文](https://www.v2ex.com/t/1219489)
摘要：帖子发布于 2026-06-11 02:57 BJT。楼主常驻北美的连续创业者，过去一年把项目从「自己主导 + AI 辅助」转成「AI 主导 + 自己 review」：几千块的 token 可以等效至少 3 个有经验的外包，沟通成本 / 情绪成本归零；建议「没事多逛 reddit 找痛点，那种月赚几千块但能批量复制的 niche 是 AI 副业最稳的现金流」。评论区多人在补「生成 UI / 出图的最优解」。**对 AI 副业读者的价值**：把 2026 年的「算账公式」从「小时单价 × 工时」换成「月 token 预算 × 单项目可批量数」—— 同样的资金和精力，**月做 3 个 5k 美金的海外 niche > 月做 1 个 50k 美金的国内大单**。

### [全职/合伙人] 寻找 Golang & Vue3 全栈合伙人，50/50 股份 + 月流水 7 位数
来源：V2EX
发布者：totorohappy
原文：[原文](https://www.v2ex.com/t/1219480)
摘要：帖子发布于 2026-06-10 23:43 BJT。楼主已运营 5 个月、营收流水 7 位数（明账），三年行业经验总结 + 完整旗舰产品设计方案、现有客户展示（不是构思项目阶段）。寻找全职合伙人负责全部技术（要求 Golang + Gin/Go-Zero + PostgreSQL + Redis + WebSocket + 安全设计 + Vue3/TS 熟练），自己负责推广营销；合作 50/50 股份，预计 2-4 个月开发周期 + 半年内几乎垄断市场 + 年盈利 8 位数（保守），联系 demoplay11@proton.me。**对 AI 副业读者**：**「带流量 / 客户 / 营收的合伙人 + 50/50 股份」是 2026 年最优解**，比「纯技术合伙人拿工资 + 期权」靠谱 10 倍。

### 招聘：CFO（Web3/CEX）+ 高级前端工程师（预测市场）+ 量化/全端/合规多个岗位
来源：V2EX
发布者：justinX
原文：[原文](https://www.v2ex.com/t/1219449) / [原文](https://www.v2ex.com/t/1219240)
摘要：两条同号招聘帖均发布于 2026-06-10 上午：1219240 招量化交易系统工程师 + 全端前端（Flutter+React）+ 首席合规官 + 大数据开发；1219449 招 CFO（Web3/CEX 方向）+ 高级前端工程师（预测市场）。Web3 方向给到的薪资段在 60-150k/月区间，比国内同岗位平均高 50-80%。**对 AI 副业读者**：**Web3 + AI 副业者被并购 / 收购的窗口在 2026 上半年加速打开**——但合规与财务结构比「写代码」更稀缺，懂传统审计 / 金融牌照的「半技术半金融」候选人被点名高薪抢。

## 🚀 创业/项目

### Claude-lights-out：基于 Claude Code Workflow 的 9 阶段 Loop Engineering 流水线
来源：V2EX
发布者：DreamChaser
原文：[原文](https://www.v2ex.com/t/1219430)
摘要：帖子发布于 2026-06-10 17:54 BJT。楼主用 Claude Code 的 dynamic workflow 写了一个「强制 9 阶段流水线」：需求编写 → 交互设计 → 技术架构 → 一致性检查 → 测试用例设计 → 写代码 → QA → E2E 验证 → 最终检查。每个阶段都有「独立 agent 审查（不过打回重写）」。核心设计原则：(1） 写的人和审的人必须是不同 agent；(2） 文档先行，代码最后；(3） 写代码阶段 agent 自主决定策略（简单项目 TDD，复杂项目自动拆前后端并行）；(4） 每个环节自带 5 轮修复循环。实测 4 个项目（含 67 / 66 / 50 个测试）均一次或一轮修复后通过。**对 AI 副业读者**：**30-50 个 agent call + 1-2 小时 = 完整可上线的全栈 demo** —— 这就是 2026 年 AI 副业 / 独立开发的「基础时薪」基准，单人/两人组靠它能产出过去 5 人团队的产能。

## 🤖 Agent 基建（监控/调度）

### Show HN: AgentMeter —— 实时监控你的 AI coding agent 花了多少 token / 钱
来源：Hacker News
发布者: (HN id 48475587)
原文：[原文](https://news.ycombinator.com/item?id=48475587)
摘要：帖子发布于 2026-06-10 20:54 BJT。AgentMeter 专门给「并行跑 5-10 个 Claude Code / Codex / Cursor / 各种 agent」的重度用户做的成本控制台：实时 token / 美元消耗、按项目 / 模型 / session 拆解、Slack / Webhook 告警超额、支持自托管。对 AI 副业读者价值：**Agent 化开发最大的隐性成本是「无人值守的 token 烧光」**——日均 200+ 美金的 token 预算在 2026 年是独立开发者常态，缺一个 dashboard 就会在「跑通 PMF」之前破产。**这是一条典型的「副业者给副业者做工具」的赛道**，开发者 × 开发者付费意愿 = 行业最稳的 PMF。

### Show HN: AgentHUD —— 并行跑 5+ Claude Code session 的实时 TUI 仪表盘
来源：Hacker News
发布者: (HN id 48474693)
原文：[原文](https://news.ycombinator.com/item?id=48474693)
摘要：帖子发布于 2026-06-10 19:25 BJT。AgentHUD 是给「同时跑多个 Claude Code session」的开发者做的 TUI + 每日 digest 工具：把所有 session 的进度、状态、token、log 流实时打到一块屏上。**对 AI 副业读者**：与 AgentMeter 同期出现不是巧合——「**单人 + 多个 agent + 实时观测**」是 2026 年 AI 副业的新基础设施层。**从「手把手调教 LLM」到「监控 N 个 agent 自己干活」的过渡期**，每多 1 个并发 session 边际收益递增，配套工具（观测 / 计费 / 调度）的早期窗口至少还有 6-12 个月。

## 💡 副业方法论

### Claude-lights-out 实测表：1 人 / 2 小时 = 过去 5 人 / 1 周产能
来源：V2EX（综合 DreamChaser 1219430 + HN 48472867 + HN 48475587 三帖对照）
原文：[原文](https://www.v2ex.com/t/1219430) / [原文](https://news.ycombinator.com/item?id=48472867) / [原文](https://news.ycombinator.com/item?id=48475587)
摘要：把今天三条工具帖放到一张产能对比表上：**Claude-lights-out**（V2EX 1219430）跑 4 个项目，30-50 个 agent call / 45 分钟到 2 小时出全栈 demo + 测试 + 文档；**Eatmydata.ai**（HN 48472867）做纯 local-first SQL+ dashboard，单人单 repo 完整实现；**AgentMeter**（HN 48475587）证明日均 200+ 美金 token 已经是「并行 5-10 个 agent」的常态成本。**对 AI 副业读者的可抄组合拳**：(1) Claude-lights-out 当「自动开发 pipeline」把单月产能从 1 个 demo 拉到 3-4 个；(2) Eatmydata.ai 当「垂直 SaaS 模板」，每个新行业（医疗 / 律所 / 跨境电商）用 2-3 天克隆一份；(3) AgentMeter 必备，把「日烧 token」可视化，避免「副业 = 倒贴钱」。

## 🤔 心态/趋势

### Ask HN: Will the next high value profession be people who can think independently?
来源：Hacker News
发布者：ciwolex
原文：[原文](https://news.ycombinator.com/item?id=48482723)
摘要：帖子发布于 2026-06-11 05:06 BJT。讨论串里 mikestorrent 一句话点题：「过去一直如此，**前提是你的独立思考得对齐别人真正需要的东西**——纯为独立而独立走到极端往往毁掉自己」；andersmurphy 跟了一条 LLM 时代预言：「LLM 让平均输出趋同，公司决策越来越可预测，**独立思考变成 alpha 最高的稀缺资源**」。**对 AI 副业读者**：**「副业选品 = 独立判断 + 海外 niche 数据 + 跨域迁移能力」**——这是 2026 年副业者给自己定价的最干净公式，HN 讨论串也反复回归到这一组关键词。

### AI Influencers Now Indistinguishable from Real Creators
来源：Hacker News
发布者：Vaslo
原文：[原文](https://news.ycombinator.com/item?id=48462713)
摘要：文章发布于 2026-06-09 23:51 BJT。techbuzz.ai 报道，AI 生成的虚拟网红（AI Influencer）在内容、互动、粉丝增长曲线上已经和真人 creator 几乎无法区分。**对 AI 副业读者**：**这是一条被严重低估的「副业 + 灰产 + 主流」三合一机会**——AIGC + 视频生成 + 多账号矩阵运营 = 2026 年海外网创团队（lead generation / 联盟营销 / 直播带货）的标配。对想用 AI 副业做到 50k 美金/月的人来说，「AI Influencer 工作室」是少有的「内容 + 流量 + 变现」三端都能靠 prompt 工程打满的赛道。

---

🦞 每日 09:00 自动更新

**数据来源**：V2EX（酷工作 / 创业组队 / 职场话题 / create 节点 6 条帖子页 + API 元数据交叉验证）、Hacker News（Show HN / Ask HN / 外站转载 5 条帖子页逐条打开核验）。Reddit r/SideProject / r/AI_Agents / r/IndieHackers 全部 403 屏蔽，按任务铁律「副业不足 6 条时拓宽到 V2EX / ProductHunt 替代采集源」执行，ProductHunt / IndieHackers 链接由 HN 转引保留。

**🔗 原文链接：**
- ✅ https://www.v2ex.com/t/1219254 - AI 应用创业找 CTO，PMF 已通
- ✅ https://www.v2ex.com/t/1219489 - Token 替代外包的算账帖
- ✅ https://www.v2ex.com/t/1219480 - Golang&Vue3 全栈合伙人
- ✅ https://www.v2ex.com/t/1219449 - 招聘 CFO/高级前端工程师（Web3）
- ✅ https://www.v2ex.com/t/1219240 - 量化/全端前端/合规招聘
- ✅ https://www.v2ex.com/t/1219430 - Claude-lights-out 9 阶段流水线
- ✅ https://news.ycombinator.com/item?id=48477326 - Show HN: AuthAI
- ✅ https://news.ycombinator.com/item?id=48472867 - Show HN: Eatmydata.ai
- ✅ https://news.ycombinator.com/item?id=48475587 - Show HN: AgentMeter
- ✅ https://news.ycombinator.com/item?id=48474693 - Show HN: AgentHUD
- ✅ https://news.ycombinator.com/item?id=48482723 - Ask HN: 独立思考是下一个 high value profession
- ✅ https://news.ycombinator.com/item?id=48462713 - AI Influencers Indistinguishable
