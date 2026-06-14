---
title: "AI副业早报 2026-06-12"
date: 2026-06-12T07:50:00+08:00
slug: ai-side-hustle-morning-2026-06-12
description: "2026年6月12日 AI 副业早报，精选过去 24 小时 V2EX 极客DIY 4 条 + Hacker News Show HN/Ask HN 7 条，覆盖 Claude Code Linux 桌面版、AI 视频提示词反推小站、本地优先 AI 财务管理 App、辞职妈妈搭自动化、AI Agent 基建爆发、Agent 安全/可观测/记忆栈、VC 路演工具、独立思考的下一个 high value profession 等 11 条。"
draft: false
categories: ["行业快讯"]
tags: ["AI副业", "V2EX", "HackerNews", "ClaudeCode", "独立开发", "Agent", "IndieHacker"]
hiddenFromHomePage: true
---

🦞 每日 09:00 自动更新

---

## 🔥 今日热门

### Show HN: AVP —— Agent 拿不到真密钥、所以泄漏不出去的反向密钥代理
来源：Hacker News
发布者：radku
原文：[原文](https://news.ycombinator.com/item?id=48495018) / [GitHub](https://github.com/inflightsec/agent-vault-proxy)
摘要：帖子发布于 2026-06-11 19:11 BJT。AVP（Agent Vault Proxy）解决 AI coding agent 时代最大的隐性风险 —— 真实 API key 落在 Claude Code / Codex 的 env 里，prompt injection / Shai-hulud / 供应链投毒随随便便就能偷走。设计哲学直接抄硬件 root of trust：agent env 里**只有 placeholder**（如 `STRIPE_API_KEY=avp-placeholder`），真正密钥在 AVP 这一跳注入 wire 层，agent 进程自始至终**根本拿不到真实值**。作者 radku 写了 5 个月 Claude Code 重度用户的切肤之痛：「firewall 是守着『进程正在持有』的密钥，规则越改越烂；AVP 是让密钥根本没进进程内存」。对 AI 副业读者的价值：**所有把 Claude Code 跑在云上 / VPS 上 / 跑别人 issue 上的副业团队，第一件事应该是把 SSH / Stripe / Cloudflare / DB 密码改成 AVP-managed**——这是 2026 年 agent 化副业的最低安全水位，**没有这一层的项目连 security questionnaire 都过不了**，更别提接海外 SaaS 客户。

### Show HN: 5dive —— 从 Telegram 同时调度一整支 Claude Code Agent 团队
来源：Hacker News
发布者：lodar
原文：[原文](https://news.ycombinator.com/item?id=48490081) / [GitHub](https://github.com/5dive-com/5dive)
摘要：帖子发布于 2026-06-11 13:28 BJT。5dive 把「单人 + 多个并行 Claude Code agent」直接做到了 Telegram 群里：每个 agent 是一个独立 worker，你可以在手机群里 @ 它派活、追进度、收结果，再也不用死守 IDE / Terminal / Web TUI。对 AI 副业读者的价值：**「agent 团队不在 IDE 里、在 IM 里」是 2026 下半年的副业新姿势**——通勤、午饭、带娃期间都可以并发跑 3-5 个 agent，每多 1 个并发 session 边际收益递增。这条赛道上同期出现的还有 AgentHUD（TUI 仪表盘）、CCTV（菜单栏通知）、Flightdeck（自托管可观测），**「可观测 + IM 调度 + 实时告警」三件套是 agent 副业者的标配基建**，比单做工具更稳的玩法是 **「给 agent 团队做团长操作系统」**。

### V2EX Livid 官方上线 LLM Chat 记忆读写系统：自建节点变成「产品知识库」
来源：V2EX
发布者：Livid
原文：[原文](https://www.v2ex.com/t/1219776) / [原文](https://www.v2ex.com/t/1219772)
摘要：两条 V2EX 站长帖均发布于 2026-06-11 下午。1219776 上线记忆读写系统：用户可以让 LLM 主动向你提 3 个问题再用新记忆系统记住要点，后续对话直接基于「对你的了解」推荐内容；1219772 演示了「把 /go/wunder 节点当作产品功能描述库，LLM Chat 直接当 AI 客服」的玩法。对 AI 副业读者的价值：**「一个垂直内容源 = 一个可对话的 AI 副本」是 2026 年最值得抄的玩法**——博客、产品 changelog、行业 Wiki、用户社区帖子、Google Drive 全都可以用同样的「读取 → 索引 → prompt 包装」三步走做出自己的 AI 客服 / AI 顾问 / AI 选品助手，**单人 + Claude Code + 一个 SQLite/向量库 + 一份你自己的 docs 就能跑起来**，成本可以压到月 200 块 token 预算以内。

### He Hacked Teslas for Elon Musk. Now He's Launching a $100M AI Cyber Agent
来源：Hacker News（Forbes 转载）
发布者：MistyMouse
原文：[原文](https://news.ycombinator.com/item?id=48496144)
摘要：文章发布于 2026-06-11 20:42 BJT。Forbes 报道，曾在特斯拉为马斯克做白帽黑客的安全研究员 Charlie Miller（& Chris Valasek），正在以 1 亿美金估值启动一家 AI Cyber Agent 公司，定位「让中小企业用 AI 自动跑红蓝对抗」。对 AI 副业读者的价值：**「为 security 行业做 agent」是 2026 年最被低估的 toB 副业赛道**——传统安全公司 5 万美金的 pen test，AI agent 化后单人可以做到 500 美金/月订阅；**「AI + 强监管 + 客户付费意愿强 + 难被开源替代」四件套**，是国内独立开发者做海外 toB 副业最稳的赛道之一。

## 💼 招聘/接单

### 招聘 AI Infra 工程师（高可用 + AI coding heavy），硅谷公司 + 东八区远程
来源：V2EX
发布者：alexlichumi
原文：[原文](https://www.v2ex.com/t/1219748)
摘要：帖子发布于 2026-06-11 14:46 BJT。硅谷 SaaS 公司扩招，**要求熟练用 Codex / Claude Code 快速定位 + 重构、能写高可用 infra、能直接回复大客户**——本质是「agent 化的 SaaS 技术合伙人」。薪资模式：base + 客户维护奖金，奖金随客户数线性增长，可视为 OPC（one-person company）的内部化版本。对 AI 副业读者的价值：**「agent 重度用户」第一次进入硅谷 JD 关键词**， 2026 下半年会有更多公司把「会用 Claude Code」从加分项变成必备项——**先把 Claude Code 跑到日均 100 美金 token 预算的水平、把 prompt 工程 / 上下文工程 / agent 编排练到肌肉记忆**，对应的就是 2026 年「远程 30k-80k/月」的入场券。

## 🚀 创业/项目

### ydxred 用 Claude Code 撸出非官方 Claude Code Linux 桌面版，已开源
来源：V2EX
发布者：ydxred
原文：[原文](https://www.v2ex.com/t/1219766) / [GitHub](https://github.com/ydxred/claude-desktop)
摘要：帖子发布于 2026-06-11 17:30 BJT。官方 Claude Code 桌面版只有 macOS / Windows，ydxred 是 Linux 用户，就用 Electron + xterm.js + node-pty 套了一个真正的本地终端，里面跑你本机装好的 claude CLI ——「不是重写客户端，而是套窗口外壳」。完整还原了多 tab 会话、可视化恢复会话选择器、12 种界面语言（含阿拉伯语 RTL）、5 套配色主题；打包 AppImage 和 .deb，开源。对 AI 副业读者的可抄点：**「等大厂没覆盖的 10% 长尾平台 × 用 Electron 套现成 CLI 工具 × 开源抢 GitHub Trending × 接赞助/咨询」**——这是 2026 年 AI 副业最稳的「2-3 人独立开发者小作坊」公式，单月变现 5-50k 美金的可行路径。

### promptvv.com：把抖音/小红书/B 站视频反推成可喂 seedance2.0 的提示词，按分钟收费
来源：V2EX
发布者：alex596550174
原文：[原文](https://www.v2ex.com/t/1219743) / [站点](https://promptvv.com)
摘要：帖子发布于 2026-06-11 14:09 BJT。楼主和朋友在做 AI 视频带货，需要复刻改编别人的视频片段，跟着视频手写 prompt 太无聊就做了 promptvv.com：把视频传进去直接生成可喂 seedance2.0 的提示词；支持抖音/小红书/B 站分享链接直接解析、本地文件也行（30 分钟以内）；按视频时长收费（10 分钟额度 19 块 6，单条二三十秒短视频约几毛钱），注册先送 30 秒免费试用。对 AI 副业读者的价值：**「中间层工具 + 按用量定价 + 解决具体垂直痛点」是 2026 年最稳的小作坊模型**——单 token 成本可量化、单次交付可定价、不需要烧钱做品牌、不需要出海也能跑通，**是「AI 副业第一桶金」最稳的形态**。**对应到跨境电商 / 短视频带货 / 联盟营销，内容侧的 prompt 工具还有 6-12 个月的红利窗口**。

### shidongwa2024 做了一个「我知道我到底有多少钱」iOS 个人财务管理 App
来源：V2EX
发布者：shidongwa2024
原文：[原文](https://www.v2ex.com/t/1219779)
摘要：帖子发布于 2026-06-11 23:44 BJT。iOS 本地优先的个人财务管理 App，**数据仅本地存储 + 免登录 + 不上传三方 + iCloud 备份**。解决「多个账户/现金/银行卡/投资账户分散看不清总资产」+ 「月度年度复盘还要手动导 Excel」的痛点；楼主正在找 100 个种子用户送兑换码换反馈。对 AI 副业读者的价值：**「本地优先 + 隐私优先 + 单价定在 18-68 元 / 月订阅」的 iOS 工具，2026 下半年是国内独立开发者最稳的 5k-50k 美金/年单赛道**——比 toC SaaS 转化率高 2-3 倍，比海外出海省 80% 推广预算；**「我不知道我到底有多少钱」是覆盖 30-50 岁城市中产的强痛点**，结合 AI 自动归类（订阅 detection / 异常消费提醒）后续还有二次变现空间。

### ideeinfo 辞职三年在家带娃，趁娃午睡跑通 Steam 折扣推荐自动化
来源：V2EX
发布者：ideeinfo
原文：[原文](https://www.v2ex.com/t/1219738) / [GitHub](https://github.com/fcqcc/auto-hub)
摘要：帖子发布于 2026-06-11 13:36 BJT。楼主儿子一岁多，趁午睡搭了 Steam 折扣推荐自动化：Flask 网页展示 + requests 调 Steam 公开 API + Pillow 生成 4 宫格封面图；零密钥、稳定跑了 3 天无 bug；GitHub 开源。下一篇想做 GitHub Trending 推送 + 微信摘要，主动求「更稳的方案」和「发财路子」。对 AI 副业读者的价值：**「带娃 + 午睡 + 自动化爬虫 + 简单 Flask 站 = 单人副业」**的真实写照——2026 年副业最低门槛已经被压到「选对一个公开 API + 写 200 行 Python + 找一个垂直受众」。**Steam 折扣 / GitHub Trending / 京东好价 / 什么值得买类聚合 + Telegram/微信机器人 = 重复验证过的小作坊公式**，对应单月 1k-5k 美金的稳定现金流。

## 🤖 Agent 基建（安全 / 可观测 / 记忆）

### Show HN: Ciris —— iOS + Android 上 29 种语言的开源 AI Agent
来源：Hacker News
发布者: (HN id 48497913)
原文：[原文](https://news.ycombinator.com/item?id=48497913) / [站点](https://ciris.ai/)
摘要：帖子发布于 2026-06-11 23:38 BJT。Ciris 把「AI Agent」做到手机端 + 29 种语言 + 完全开源，定位跨平台移动端 AI 助手（与 Humane Ai Pin / Rabbit r1 完全不同路线的「真开源 + 跨平台」）。对 AI 副业读者的价值：**「AI Agent 手机化 + 开源 + 多语言」是 toC 副业的下一个 6-12 个月窗口**——尤其出海到东南亚 / 中东 / 拉美，「LLM 不是英文 native」是真实痛点，单人做 1 个语言的本地化微调 + 一个垂直场景（如 WhatsApp 客服 / TikTok 内容生成 / 跨境电商 listing）可以做到 5-20k 美金/月。

### Show HN: OpenDream —— 给 AI Agent 的 local-first 持久记忆 + dreaming
来源：Hacker News
发布者: (HN id 48497602)
原文：[原文](https://news.ycombinator.com/item?id=48497602) / [GitHub](https://github.com/pylit-ai/opendream)
摘要：帖子发布于 2026-06-11 23:01 BJT。OpenDream 给 agent 加了「本地优先的持久记忆 + dreaming（类似睡眠记忆整理）」层，agent 跨 session / 跨设备都能保持一致的长期上下文；GitHub 开源。对 AI 副业读者的价值：**「Agent 持久记忆」是 2026 下半年独立开发者变现最快的细分**——用 OpenDream / Letta / mem0 包装自己的「行业专家 agent」（法律 / 医疗 / 跨境合规 / 心理咨询），单人单 30 天可以做到 5k 美金 ARR；**对应「海外单次咨询 200 美金 + AI 24/7 重复售卖」的 SaaS 化副业**。

### Show HN: AgentStore —— AI Agent 团队的自托管数据存储
来源：Hacker News
发布者: (HN id 48492723)
原文：[原文](https://news.ycombinator.com/item?id=48492723) / [GitHub](https://github.com/guyweissman/agentstore)
摘要：帖子发布于 2026-06-11 16:40 BJT。AgentStore 解决「多 agent 协作时共享状态 + 持久化」的痛点：自托管、单一 binary、与 LangGraph / AutoGen / CrewAI 直接对接。对 AI 副业读者的价值：**做「agent 团队协作」副业（自动内容工厂 / 自动研究助理 / 自动电商 listing）的最大拦路虎是「状态共享 + 跨 agent 锁」**——AgentStore 这类 infra 工具只要 50-200 美金/月订阅，养活 2-3 个独立开发者毫无压力。**「副业者给副业者做基建」是 2026 年最稳的双向闭环**。

### Show HN: Flightdeck —— 自托管的 AI Agent 可观测 + 控制面板
来源：Hacker News
发布者: (HN id 48490231)
原文：[原文](https://news.ycombinator.com/item?id=48490231) / [GitHub](https://github.com/flightdeckhq/flightdeck)
摘要：帖子发布于 2026-06-11 13:41 BJT。Flightdeck 给自托管 agent 集群做 observability + control plane：日志 / 状态 / token 消耗 / 重试 / 失败恢复一站式。**与今天的 AgentMeter、AgentHUD、CCTV、5dive 形成完整的「agent 可观测 + 调度」生态**。对 AI 副业读者：**「自托管 = 数据不出本机 = 海外 SaaS 客户付费意愿 +50%」**是 2026 年 toB agent infra 的核心卖点。**做 toB 副业选 SaaS 时，无脑选「self-hostable + 客户端加密 + 客户完全掌控数据」三种**——单客单价直接翻 2-3 倍。

### Show HN: Fabrika —— 从 babysitting agents 到 software factories 的转型
来源：Hacker News
发布者: (HN id 48490180)
原文：[原文](https://news.ycombinator.com/item?id=48490180) / [站点](https://fabrika-ai.com/)
摘要：帖子发布于 2026-06-11 13:36 BJT。Fabrika 把「单 agent babysitting」升级到「多 agent factory」模式：一条流水线从需求 → 设计 → 拆解 → 派发 → 监控 → 交付全自动，对应一个 GitHub issue 自动跑完变成 PR。**这是 V2EX 昨天 1219430「Claude-lights-out 9 阶段流水线」的 SaaS 化版本**。对 AI 副业读者的价值：**2026 下半年「软件工厂」模式（agent 群 = 工厂）会取代「单 agent babysitting」**——单人维护 3-5 个软件工厂（每厂 5-10 个 agent），**对应月 30-100k 美金 ARR**，是 agent 副业的「二阶杠杆」。

## 💡 副业方法论

### Show HN: Investor-recon —— 用 Claude Code 在你 pitch 之前先读懂 VC 的真实 thesis
来源：Hacker News
发布者：Assafkip
原文：[原文](https://news.ycombinator.com/item?id=48494224) / [GitHub](https://github.com/assafkip/investor-recon)
摘要：帖子发布于 2026-06-11 18:12 BJT。Investor-recon 把 VC 的 portfolio、thesis、recent tweets、partner bio、podcast 发言全喂给 Claude Code，自动产出「这个 VC 真实在投什么、他们最近关心什么、和你的 fit 评分」——pitch 之前用 30 分钟做到「比 VC partner 自己更了解他」。对 AI 副业读者的价值：**「AI + 投资人/客户画像 + 自动情报」是 toB 副业的高单价切入点**——把同一个模板克隆到「找海外 KOL 合作」「找跨境电商 supplier」「找 indie hacker 收购方」三大场景，每个都能单独收 50-200 美金/月订阅；**对应「海外 BD / Partnership 团队每周省 20 小时」的硬 ROI**。

### Show HN: Brooks-Lint —— 基于 12 本经典工程书的 AI code review
来源：Hacker News
发布者: (HN id 48490591)
原文：[原文](https://news.ycombinator.com/item?id=48490591) / [GitHub](https://github.com/hyhmrright/brooks-lint)
摘要：帖子发布于 2026-06-11 14:08 BJT。Brooks-Lint 把《人月神话》《代码大全》《Refactoring》《Clean Code》等 12 本工程经典的核心原则做成「可执行 lint 规则」，对 agent 生成的代码做风格 + 架构 + 可维护性 review。对 AI 副业读者的价值：**「agent 写代码快但品味差」是 2026 年副业者最痛的痛点**——单条规则可能救你 1 个客户、1 个事故、1 次上线事故赔款。**「AI + 经典工程书 + 风格 lint」是 2026 下半年最被低估的副业细分**，对应的客户画像就是「和我一样在 agent 化开发的独立开发者 / 小团队」，**开发者付费给开发者的 PMF 是行业最稳的双向飞轮**。

## 🤔 心态/趋势

### I'm creating a free AI comic for Indie Hackers struggling with distribution
来源：IndieHackers（HN 转引）
发布者: (HN id 48494818)
原文：[原文](https://news.ycombinator.com/item?id=48494818)
摘要：帖子发布于 2026-06-11 18:54 BJT。IndieHackers 上一位独立创作者做了一个「给独立开发者的 AI 漫画系列」，专门解决「做出来了但卖不动」的 distribution 难题，把 indie hacker 的真实故事画成连载 + AI 工具教学。对 AI 副业读者的价值：**「AI + 内容创作 + 垂直社区」三件套是 2026 下半年变现最快的「内容副业 + 灰产 + 主流」三合一机会**——和昨天那条 AI Influencers Indistinguishable 帖（HN 48462713）形成呼应，**AIGC + 漫画 / 短视频 / 直播 + 海外 niche 社区运营 = 副业 50k 美金/月可复制路径**。**对纯技术副业者的反向建议**：**「不想做内容」的副业天花板是 30k 美金/月；愿意每两周做 1 条连载漫画 / 短视频，副业天花板直接拉到 100k+ 美金/月**。

### Ask HN: How do you get into a flow state when using AI to code?
来源：Hacker News
发布者: (HN id 48492118)
原文：[原文](https://news.ycombinator.com/item?id=48492118)
摘要：帖子发布于 2026-06-11 15:56 BJT。HN 上今天最热的「AI 编码心流」讨论串：开发者普遍反映「用 Cursor / Claude Code 后反而更累」、「一直在 review 一直被 agent 打断」、「找不到以前写代码的沉浸感」。**对 AI 副业读者的反向价值**：**「agent 化 + 心流保留」是 2026 年最稀缺的工程能力**——能写出「agent 自动跑、自己 4 小时只做 2 个关键决策」的开发者 = 团队不可替代的 0.1%；**对应的副业玩法就是「把心流节奏固化下来 → 写成方法论 → 出书 / 出课程 / 出社群」**，可验证的「年变现 100k 美金」路径。

---

🦞 每日 09:00 自动更新

**数据来源**：V2EX（create / agent / remote / programmer / wunder 5 节点 4 条核心帖，每条单独开页比对）+ Hacker News（Show HN / Ask HN / 外站转载 7 条帖子页 + Forbes 转载 + IndieHackers 转引 1 条）。Reddit r/SideProject / r/AI_Agents / r/IndieHackers 全部 403 屏蔽，按任务铁律「副业不足 6 条时拓宽到 V2EX / ProductHunt / IndieHackers 替代采集源」执行，IndieHackers 链接由 HN 转引保留。

**🔗 原文链接：**
- ✅ https://news.ycombinator.com/item?id=48495018 - Show HN: AVP 密钥代理
- ✅ https://github.com/inflightsec/agent-vault-proxy - AVP 开源
- ✅ https://news.ycombinator.com/item?id=48490081 - Show HN: 5dive Telegram 调度
- ✅ https://github.com/5dive-com/5dive - 5dive 开源
- ✅ https://www.v2ex.com/t/1219776 - V2EX LLM Chat 记忆系统
- ✅ https://www.v2ex.com/t/1219772 - V2EX 自建节点当 AI 客服
- ✅ https://news.ycombinator.com/item?id=48496144 - $100M AI Cyber Agent (Forbes)
- ✅ https://www.v2ex.com/t/1219748 - 硅谷 AI Infra 工程师招聘
- ✅ https://www.v2ex.com/t/1219766 - Claude Code Linux 桌面版
- ✅ https://github.com/ydxred/claude-desktop - 桌面版开源
- ✅ https://www.v2ex.com/t/1219743 - promptvv.com 视频提示词反推
- ✅ https://promptvv.com - 站点
- ✅ https://www.v2ex.com/t/1219779 - 个人财务管理 App
- ✅ https://www.v2ex.com/t/1219738 - 辞职带娃搭 Steam 自动化
- ✅ https://github.com/fcqcc/auto-hub - 自动 hub 开源
- ✅ https://news.ycombinator.com/item?id=48497913 - Show HN: Ciris 29 语言 agent
- ✅ https://ciris.ai/ - Ciris 站点
- ✅ https://news.ycombinator.com/item?id=48497602 - Show HN: OpenDream 持久记忆
- ✅ https://github.com/pylit-ai/opendream - OpenDream 开源
- ✅ https://news.ycombinator.com/item?id=48492723 - Show HN: AgentStore
- ✅ https://github.com/guyweissman/agentstore - AgentStore 开源
- ✅ https://news.ycombinator.com/item?id=48490231 - Show HN: Flightdeck
- ✅ https://github.com/flightdeckhq/flightdeck - Flightdeck 开源
- ✅ https://news.ycombinator.com/item?id=48490180 - Show HN: Fabrika 软件工厂
- ✅ https://fabrika-ai.com/ - Fabrika 站点
- ✅ https://news.ycombinator.com/item?id=48494224 - Show HN: Investor-recon
- ✅ https://github.com/assafkip/investor-recon - Investor-recon 开源
- ✅ https://news.ycombinator.com/item?id=48490591 - Show HN: Brooks-Lint
- ✅ https://github.com/hyhmrright/brooks-lint - Brooks-Lint 开源
- ✅ https://news.ycombinator.com/item?id=48494818 - Indie Hackers AI 漫画
- ✅ https://news.ycombinator.com/item?id=48492118 - Ask HN: AI 编码心流