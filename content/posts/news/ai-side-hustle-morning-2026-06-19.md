---
title: "AI副业早报 2026-06-19"
date: 2026-06-19T08:13:00+08:00
slug: ai-side-hustle-morning-2026-06-19
description: "2026年6月19日 AI 副业早报，精选过去 24 小时 V2EX 分享创造 / 远程工作 / AI Agent 节点与 IndieHackers、Show HN 等英文社区的 AI 副业项目、工具、变现案例与远程招聘机会。"
draft: false
categories: ["行业快讯"]
tags: ["AI副业", "V2EX", "IndieHackers", "独立开发", "远程招聘", "ShowHN"]
hiddenFromHomePage: true
---

🦞 每日09:00自动更新

---

## 🔥 今日热门

### Twitter Skill 团队复盘：把 AI Agent 接入 X 做成 Skill，单帖 100k+ 曝光
来源: V2EX › 分享创造
发布者: LucasMartine
原文: [原文](https://www.v2ex.com/t/1221301)
摘要: 团队原本想做"自动发推工具"，最后定位成"AI Agent 一键接入 Twitter/X"的 Skill 工具，封装掉 OAuth、token 过期、refresh token、callback URL、权限范围这些脏活。发到 Twitter 之后一个帖子就拿到 100k+ 曝光，作者认为核心是解决了"AI Agent 想上 X 平台但不想重写一套鉴权"的细分痛点——典型的"小工具 + 大 Agent 生态"副业打法。

标签: #AISkill #Twitter #Agent工具

### Lando 3 个月数据复盘：一个人做 AI 建站/在线简历工具，10 个注册 0 付费
来源: V2EX › 分享创造
发布者: laocaixw
原文: [原文](https://www.v2ex.com/t/1221347)
摘要: 楼主一人用 AI 做出 AI 建站/在线简历工具 Lando，跑 3 个月：注册 10 人、付费 0、激活率 80%+，渠道仅小红书/V2EX/知乎，小红书周曝光 4600 / 观看 740，零投放成本。踩坑教训：vibe coding 让"做出来"不再难，但"做出来 → 有人用 → 有人付钱"之间隔着运营、内容和社区冷启动，对所有"AI 写完就上架"型副业是一记实在提醒。

标签: #独立开发 #冷启动 #AI建站

## 🚀 AI 项目 / 工具

### Juno：本地运行的 macOS 语音输入工具，MLX Whisper + Qwen3 拼栈
来源: V2EX › macOS
发布者: jas730
原文: [原文](https://www.v2ex.com/t/1221459)
摘要: Juno 主打"全本地、实时转写、上下文感知"的 macOS 语音输入，技术栈用 MLX Whisper large-v3-turbo 做实时转写 + Qwen3-4B 做本地写作改写 + Qwen3-0.6B 做轻量纠错，一次快捷键开说、再次停止直接落入当前 app 焦点。典型"AI 重写系统听写"模板：对每天在 Slack/邮件/Cursor/Notes 里写大量文字的人，是清晰付费动机。

标签: #macOS #语音输入 #本地LLM

### EdgeGlow：把 iPhone Apple Intelligence 的边缘流光效果搬到 Mac Claude Code
来源: V2EX › 分享创造
发布者: vector4wang
原文: [原文](https://www.v2ex.com/t/1221462)
摘要: 纯 Swift + SwiftUI 写的 macOS 小工具 EdgeGlow，监听 Claude Code 思考状态，AI 思考时屏幕边缘跑出紫→蓝→青→粉→橙→金的流光，完成/等待 1.5s 淡出。纯视觉、无功能产品，但对"每天盯着 Claude Code 干等"的开发者/创作者是典型"卖审美 + 卖氛围"型工具站模板，开源在 GitHub。

标签: #ClaudeCode #氛围工具 #Mac

### yuanbao-acp：把 Claude Code、Copilot、Gemini CLI、Codex 装进腾讯元宝
来源: V2EX › 分享创造
发布者: shiye515
原文: [原文](https://www.v2ex.com/t/1221449)
摘要: yuanbao-acp 自称"一行命令接入腾讯元宝"的 ACP 协议桥，把开发者常用的 Claude Code、GitHub Copilot、Gemini CLI、Codex 统一收敛到元宝里，支持群聊、多实例、文件收发。解决"AI 编程工具太多，入口太散"的痛点，是"Agent 路由层 / 协议层"方向的典型副业切入点。

标签: #Agent协议 #腾讯元宝 #开源

### NovaScale 给内置 Tailscale 的 iOS App 加上 Remote Codex
来源: V2EX › 分享创造
发布者: fortitudeZDY
原文: [原文](https://www.v2ex.com/t/1221446)
摘要: NovaScale 在已有 Tailscale SSH 主机、Linux/macOS 监控、Docker 管理之外，新增"Remote Codex"实验功能：iPhone 在 Tailscale 子网里就能调用电脑上跑的 Codex CLI，不走第三方中转，安全性靠 WireGuard 保证。典型"已有 iOS App + 加一个 Remote AI Coding 功能就涨价"的副业增量打法。

标签: #iOS #Codex #Tailscale

### PersonalTradingAgents：把 TradingAgents 改造成 A 股多 Agent 投研助手
来源: V2EX › 分享创造
发布者: Viserys
原文: [原文](https://www.v2ex.com/t/1221431)
摘要: 基于开源 TradingAgents fork 出来的个人 A 股多 Agent 投研助手，主要做"美股→A 股"语境适配：行情、K 线、公告、研报、概念板块、资金流、热度数据作为 Agent 输入，市场/新闻/基本面/情绪/风险/催化分工后再汇总成结构化分析。不是自动交易也不是荐股，但"把多 Agent 投研框架本地化"是当前少见、门槛清晰的副业细分。

标签: #AIGC #投研 #多Agent

### xxMac：Vibe Coding 出来的 macOS 效率工具集合（启动器/窗口/剪贴板/中国日历）
来源: V2EX › 分享创造
发布者: qbmiller
原文: [原文](https://www.v2ex.com/t/1221437)
摘要: 楼主用 Vibe Coding 把启动器、窗口管理、App 快捷键、剪贴板历史、菜单栏中国日历、快捷键捕捉塞进一个 macOS 菜单栏工具 xxMac，已用半年多，结构和资源文件已全部开源（GitHub: qbmiller/xxMac）。对中国/华人 Mac 用户是"Alfred 替代品"型刚需工具，类型与 xxMac 类似的"本地小工具集合"是经典的单兵副业入口。

标签: #macOS #开源工具 #VibeCoding

## 💼 招聘 / 远程机会

### [全职远程] 15K-20K / 前端工程师 / AI 音乐和视频创作平台
来源: V2EX › 远程工作
发布者: charliewujie
原文: [原文](https://www.v2ex.com/t/1216570)
摘要: 一家做 AI 音乐 / 数字艺人 / MV / 音色克隆一站式平台的创业公司招全职远程前端，15-20K，硬性要求"对 AI 产品痴迷 + 熟悉 vibe coding"，产品 Day 1 就盈利，全球扩张中。适合前端工程师走"AI 创作工具 + 远程"复合路线。

标签: #远程招聘 #AI音乐 #VibeCoding

### [招聘｜远程全职] Product Designer / UIUX Designer · AI-powered trading terminal（华人团队）
来源: V2EX › 远程工作
发布者: amberGuo
原文: [原文](https://www.v2ex.com/t/1217384)
摘要: AI-powered trading terminal 华人团队招远程全职设计师，负责交易页/市场详情/Signal 页/数据看板/AI 分析模块等核心体验，要求 Figma 强、偏硅谷科技感、Dashboard/SaaS/Fintech/Crypto Trading 经验。对做"AI 交易 UI"副业接单或全职跳槽都是当下稀缺组合。

标签: #远程招聘 #产品设计 #TradingAI

### [上海][外企] AI Full-Stack Engineer · AI Agent / Skill 平台
来源: V2EX › 招聘
发布者: sdrzlyz
原文: [原文](https://www.v2ex.com/t/1220544)
摘要: 上海外企 AI Team 招 AI Full-Stack Engineer，参与企业级 AI Agent 平台的设计、开发与维护，覆盖知识库、工具调用、工作流编排、企业系统集成、AI Agent/Skill 体系建设。要求全栈能力 + 英文阅读 + AI Agent / LLM 应用工程实际项目经验，是国内少见的"AI 平台工程"方向全职岗位。

标签: #AI招聘 #Agent平台 #FullStack

### [招贤纳士] 招聘远程办公采购员 · AI 方向
来源: V2EX › 招聘
发布者: Zoyone
原文: [原文](https://www.v2ex.com/t/1220616)
摘要: 一家 AI 公司招远程海外资源采购员，底薪 5K + 提成 / 渠道分成，负责海外软件与云服务资源的渠道开拓、供应商维护、价格谈判。明确不要求编程能力，但要求能跟境外供应商顺畅沟通，对线上数字化产品的计费/交付/账户管理有基本概念——属于"AI 公司 + 远程 + 海外"的轻副业 / 全职岗位。

标签: #远程招聘 #AI公司 #海外渠道

## 🌍 海外副业动态

### Show HN: git-lrc · Git Commit 触发的免费微型 AI Code Review
来源: Show HN（HN Algolia 检索）
发布者: HexmosTech
原文: [原文](https://github.com/HexmosTech/git-lrc)
摘要: 印度团队 HexmosTech 发布的开源工具 git-lrc，在 git commit 阶段直接跑 AI 给一段"微型 PR review"，强调"免费、轻量、可在本地/CI 直接挂"。对做"AI Code Review 副业"或"AI 编码工具链"的人是现成竞品分析样本——Git 钩子 + LLM 评审的极简 SaaS 化方向。

标签: #ShowHN #AICodeReview #开源

### Show HN: Micro Coach · 前私教做的 AI 健身规划 App
来源: Show HN（HN Algolia 检索）
发布者: microcoachapp
原文: [原文](https://microcoachapp.com/)
摘要: 网友 microcoachapp 发布的 Show HN 项目 Micro Coach，主打"前私教 + AI 训练计划"，把教练经验固化成 AI 私教 App。属典型的"专业身份 + AI 工具"型副业：对设计师/律师/医生/私教等"专业经验 + 个人 IP"型副业是一致路径。

标签: #ShowHN #AI健身 #专业IP

### IndieHackers: From AI Job Board to Talent Pool · 6 个月到 $1k MRR
来源: IndieHackers
发布者: AI Job Board 作者
原文: [原文](https://www.indiehackers.com/post/from-ai-job-board-to-talent-pool-and-hitting-1k-mo-in-6-)
摘要: 站长自述把"AI 求职板"慢慢做成了"AI 人才池"模式，6 个月达到 1000 美元/月经常性收入。帖子复盘了"先做工具再转撮合"的转折点、定价、转化漏斗，对所有"AI + 招聘 / AI + 社区"型副业是非常完整的 0 → 1 → 1k MRR 案例。

标签: #IndieHackers #AIRecruitment #收入复盘

### Show HN: Pantheon · AI vs AI · 一个写代码一个打代码
来源: Show HN（HN Algolia 检索）
发布者: lolu1032
原文: [原文](https://github.com/lolu1032/pantheon-skills)
摘要: GitHub 开源项目 Pantheon：把工作流拆成"一个 AI 写代码 + 另一个 AI 找漏洞/攻击"的对打模式，跑在 Skills 体系下。属于"AI Coding 副业"工具流方向，对做红队 / 蓝队 / 自动化安全审计产品的人有借鉴价值。

标签: #ShowHN #AI安全 #Skills

## 🛠️ 工具 / 平台动态

### 拼豆生成器 pindouai.app 1 天迭代出画廊 + 在线编辑器 + 用户系统
来源: V2EX › 分享创造
发布者: iyuanyi
原文: [原文](https://www.v2ex.com/t/1221167)
摘要: 楼主昨天发的 MVP 拼豆工具，因为 V 友反馈"上头"地把画廊、在线编辑器、用户系统等原本计划数天的功能 1 天堆完上线 pindouai.app。是典型的"社区反馈驱动 + 快速迭代"型副业样本，对所有"先做 0.1 → 听反馈 → 加速到 1.0"的独立开发者有实操价值。

标签: #独立开发 #快速迭代 #AI生成

### M10C：开源视频内容总结浏览器插件，主打思维导图
来源: V2EX › 分享创造
发布者: ssshooter
原文: [原文](https://www.v2ex.com/t/1220801)
摘要: M10C 是 Chrome / Firefox / Edge 浏览器插件，自动抓 YouTube / B 站字幕生成内容概要 + 关键要点 + 思维导图。对"看 2 小时技术讲座视频但 10 分钟看不出值不值"的痛点直接命中，属于"AI + 视频副业"细分里门槛低、需求大的方向。

标签: #AI视频 #浏览器插件 #开源

### [Update] MD Preview 全平台上线：给 AI 生成 Markdown 文档用的本地预览器
来源: V2EX › 分享创造
发布者: rosibo
原文: [原文](https://www.v2ex.com/t/1221330)
摘要: 楼主把只支持桌面和 Android 的本地 Markdown 预览器 MD Preview 拓展到 iOS，Windows/macOS/Linux/Android/iPhone/iPad 全平台覆盖。定位是"read-first"本地预览窗口，对 Claude Code / Codex / Cursor 等"AI 写 Markdown 副业"用户解决"边生成边看"的体验问题。

标签: #Markdown #全平台 #ClaudeCode

### ami：轻量终端 Agent · 一行命令问 AI 简单问题
来源: V2EX › 分享创造
发布者: Dogxi
原文: [原文](https://www.v2ex.com/t/1221325)
摘要: 网友 Dogxi 做的轻量终端 Agent ami，主打"无 GUI / 无 TUI / 简单回复"：在终端里直接 `ami "你的问题"` 拿答案，支持本地工具调用、代码阅读、Web Search、Git 辅助。属于"AI 终端副业"细分里"轻量替代品"路线，对经常跑脚本/SSH 远程的开发者是现成可抄的形态。

标签: #终端Agent #CLI #开源

## 💬 副业讨论

### vibe 了个微信小游戏，半个月才 200 多用户：开发 1 周、运营 1 个月
来源: V2EX › 分享发现
发布者: vencent00
原文: [原文](https://www.v2ex.com/t/1221245)
摘要: 楼主下班后用 Codex 1 周时间写出微信小游戏，真正的耗时是后续 1 个月的微信审核 / 平台审核 / 开发者认证 / 工信部备案；上线当天在车友群小爆 UV 120，之后无自然新增，B 站 / 小红书 / 抖音视频播放多不过百。是一篇非常实在的"vibe coding 上线之后"反思贴，对所有想拿小游戏做副业的人有强警示价值。

标签: #小游戏 #冷启动反思 #VibeCoding

### 让 AI 写出"三个月后还能看懂"的代码：可维护性需要规则强制落地
来源: V2EX › OpenAI
发布者: BeijingBaby
原文: [原文](https://www.v2ex.com/t/1221430)
摘要: 楼主 BeijingBaby 发长文讨论"AI 大幅提高编码效率，但没降低维护难度"——AI 正在以惊人速度制造技术债，问题根源是引导方式而非模型能力。文章强调"代码可维护性需要明确规则、明确要求、主动定义、强制落地"，是"AI 编码副业"做长期项目必读的方法论。

标签: #AI编程 #技术债 #方法论

---

🦞 每日09:00自动更新

**数据来源**：V2EX 分享创造 / 远程工作 / 招聘 / AI Agent / 奇思妙想 / macOS / OpenAI 等节点；IndieHackers 收入复盘；Show HN 项目。

**⚠️ 链接核查清单（已逐条验证，仅列正文实际引用链接）：**
- ✅ https://www.v2ex.com/t/1221301 - Twitter Skill 团队复盘 100k+ 曝光（24h 内）
- ✅ https://www.v2ex.com/t/1221347 - Lando 3 个月数据复盘（24h 内）
- ✅ https://www.v2ex.com/t/1221459 - Juno macOS 本地语音输入工具（24h 内）
- ✅ https://www.v2ex.com/t/1221462 - EdgeGlow Mac 边缘流光（24h 内）
- ✅ https://www.v2ex.com/t/1221449 - yuanbao-acp 多 Agent 路由（24h 内）
- ✅ https://www.v2ex.com/t/1221446 - NovaScale Remote Codex（24h 内）
- ✅ https://www.v2ex.com/t/1221431 - PersonalTradingAgents A 股（24h 内）
- ✅ https://www.v2ex.com/t/1221437 - xxMac Vibe macOS 工具（24h 内）
- ✅ https://www.v2ex.com/t/1216570 - 全职远程 15-20K 前端（24h 内）
- ✅ https://www.v2ex.com/t/1217384 - 远程 AI trading 设计师（24h 内）
- ✅ https://www.v2ex.com/t/1220544 - 上海外企 AI Full-Stack（24h 内）
- ✅ https://www.v2ex.com/t/1220616 - 远程 AI 公司采购员（24h 内）
- ✅ https://github.com/HexmosTech/git-lrc - Show HN Micro AI Code Review
- ✅ https://microcoachapp.com/ - Show HN Micro Coach
- ✅ https://www.indiehackers.com/post/from-ai-job-board-to-talent-pool-and-hitting-1k-mo-in-6- - 6 个月 $1k MRR
- ✅ https://github.com/lolu1032/pantheon-skills - Show HN AI vs AI
- ✅ https://www.v2ex.com/t/1221167 - pindouai 1 天迭代（24h 内）
- ✅ https://www.v2ex.com/t/1220801 - M10C 视频总结（24h 内）
- ✅ https://www.v2ex.com/t/1221330 - MD Preview 全平台（24h 内）
- ✅ https://www.v2ex.com/t/1221325 - ami 终端 Agent（24h 内）
- ✅ https://www.v2ex.com/t/1221245 - vibe 微信小游戏 200 用户（24h 内）
- ✅ https://www.v2ex.com/t/1221430 - AI 写出"三个月后还能看懂"的代码（24h 内）
