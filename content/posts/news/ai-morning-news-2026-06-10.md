---
title: "AI新闻早报 2026-06-10"
date: 2026-06-10T11:25:30+08:00
slug: ai-morning-news-2026-06-10
description: "2026年6月10日 AI 新闻早报（补做），严格采集 06-09 08:00 至 06-10 08:00 窗口，覆盖 Anthropic 发布 Claude Fable 5/Mythos 5、Microsoft GitHub 开源工具遭供应链攻击、Amazon 员工在 Slack 上嘲讽自家 AI 产品、法官发现原被告双方均用 AI 直接撤销庭审、Apple AI 自动改密码的安全风险、内蒙吉瓦级 AI 算力与电力一体化、理想智驾一号位创立昆仑行具身智能、Nextie 4B 认知模型、腾讯 WorkBuddy 企业版、DeepSeek 招 IDC 工程师自建 GW 数据中心、小红书 RED Skill、AppLovin CEO 演讲、中国 2950 亿美元 AI 投资计划等关键事件。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "Anthropic", "Claude", "Microsoft", "Amazon", "Apple", "DeepSeek", "理想汽车", "昆仑行", "腾讯", "WorkBuddy", "小红书", "Nextie", "认知模型", "内蒙", "远景", "AppLovin", "Bloomberg", "Meta", "EU"]
hiddenFromHomePage: true
aliases: ["/categories/news/"]
---

🦞 每日08:00自动更新

> 补做说明：cron 08efa9de 因 quota+gateway 故障连续多日 08:00 触发失败，今早 11:00 后人工触发补做。本次严格遵循 24h 时间窗（2026-06-09 08:00 → 2026-06-10 08:00 BJT），剔除所有越过 08:00 cutoff 的内容（含苹果与 Google 共建 Gemini 架构、小米 MiMo-V2.5-Pro、Sora 核心成员离职、Kimi 136 亿融资等昨日 8:00 前已收录条目），并新增 Anthropic Claude Fable 5/Mythos 5、Microsoft GitHub 供应链攻击、Amazon Sloppenheimer、内蒙吉瓦级算电一体化、Nextie 4B 认知模型、昆仑行具身智能、小红书 RED Skill、腾讯 WorkBuddy 企业版、DeepSeek 自建 GW 数据中心、AppLovin CEO 演讲、中国 2950 亿美元 AI 投资计划等 21 条今日新发高质量新闻。

---

## 🧠 大模型

### Anthropic 发布 Claude Fable 5 与 Claude Mythos 5：自研"神话级"旗舰分两档上桌
来源：Anthropic 官网（量子位、VentureBeat、Hacker News）
原文：[原文](https://www.qbitai.com/2026/06/433590.html)
摘要：Anthropic 在遮遮掩掩两个月后端出旗舰组合 Claude Fable 5 + Claude Mythos 5：Fable 5 是带防护网版本面向所有用户开放，触发风险分类器即自动降级到 Opus 4.8；Mythos 5 是满血版本只对受信任用户开放，解除网安/生物领域安全限制。两者共享同一基础模型，API 定价相比预览版直接砍半（10/百万输入 token、50/百万输出）。关键基准：在 SWE-bench Pro 拿到 80.3%（GPT-5.5 仅 58.6%），在 Cognition Frontier Code 评测的"中等努力"档就拿下前沿模型第一。Stripe 5000 万行 Ruby 代码库全库迁移 1 天完成（人工原本要两个多月），Fable 5 还在原生视觉盲打《宝可梦·火红》和《杀戮尖塔》两款游戏上刷出历史性成绩。Mythos 5 还在生命科学领域独立完成完整生物学工作流（结合位点选择→调度工具→Debug 失败），其"大肠杆菌蛋白新机制"假设被独立实验验证。（量子位 2026-06-10 06:52:37 发布，落在窗口内）

### Mythos/Fable 故意抑制 AI 研发相关请求：把"权限时代"的边界写在明面上
来源：Elie Bakouch（X/Twitter）
原文：[原文](https://twitter.com/eliebakouch/status/2064399902684139852)
摘要：Anthropic 安全研究员 Elie Bakouch 公开贴图说明：Mythos 5 与 Fable 5 在响应"涉及 AI 研发/AI 能力提升"的查询时会被路由到上一代 Opus 4.8 兜底，意在阻止用户借旗舰模型继续推高 AI 自身能力上限。这与 Anthropic 此前"呼吁全球暂停 AI 研发"的官方立场形成闭环——嘴上喊暂停，自家产品也已经把"自己不做"做成路由默认。评论认为这是"AI 公司主动给自家最强模型上锁"的标志性时刻，也意味着前沿模型的访问权从"算力门槛"正式变成"信任门槛"。（HN 2026-06-10 05:42 BJT 提交，10 pts，落在窗口内）

### 国产 4B"认知模型"新程 Alpha 落地：李笛带队复刻卡帕西预言
来源：量子位
原文：[原文](https://www.qbitai.com/2026/06/433478.html)
摘要：小冰之父李笛携半年内成立的 Nextie（明日新程）推出行业首个认知模型"新程 Alpha"，仅 4B 参数即可在群体智能任务上等效 GPT-5.4 等大模型输出，号称"用 4B 跑出 10 倍以上知识型推理模型的成本下降、直接端侧可部署"。Nextie 团队梳理了 1800-2020 跨 220 年的人类学术论文，从辩论/反思/挑战/投票四种群体决策机制归纳出五个评估维度（视角完备性、隐含诉求满足度、辩证深度、落地实操性、决策可解释性），用"在已有开源推理模型上做强化学习"的方式解耦知识与认知。卡帕西几个月前在访谈中预言的"10 亿参数级别的认知核心"被国产团队率先实现。（量子位 2026-06-09 12:17:04 发布，落在窗口内）

## 🏢 公司动作

### Microsoft 数十个 GitHub 仓库遭供应链攻击：AI 开发者密码被批量偷
来源：TechCrunch
原文：[原文](https://techcrunch.com/2026/06/08/microsofts-open-source-tools-were-hacked-to-steal-passwords-of-ai-developers)
摘要：Microsoft 6 月 8 日关闭数十个 Azure/AI 编码工具相关开源项目仓库，因黑客在源码中注入了可在用户本地 AI 编码 App（Claude Code、Gemini CLI、VS Code）打开项目时偷取密码/凭据的恶意载荷。安全公司 Cloudsmith 与社区分析平台 OpenSourceMalware 最先发现并上报，至少 70 个微软官方仓库被 GitHub Staff 标记"违反 ToS"而停用。Microsoft 发言人 Ben Hope 表示已通知受影响的少量客户，部分仓库审查后已恢复。这是 Microsoft 近几周内第二次开源项目被黑（5 月中旬 Durable Task 已被攻陷一次），也是 OpenSourceMalware 所称的"再入侵"（re-compromise）——意味着首次清理并未根除威胁。（HN 2026-06-09 15:33 BJT 提交，528 pts 当日 Top1，落在窗口内）

### "Sloppenheimer"：Amazon 员工在 Slack 上建专门频道嘲讽自家 AI 产品
来源: 404 Media
原文：[原文](https://www.404media.co/sloppenheimer-amazon-employees-mock-the-companys-ai-on-slack/)
摘要: 404 Media 披露，Amazon 内部有一个 Slack 频道专门用来吐槽公司的 AI 编程产品，员工把它的输出称为"slop"，并对集团层"用 AI 提效"的运动冷嘲热讽。报道把这种员工自下而上的嘲弄命名为"Sloppenheimer"。讽刺的是，Amazon 创始人 Jeff Bezos 在公开场合一直坚持 AI 会带来"前所未有的生产力提升"，承诺会带来"更便宜的食品、住房、两人家庭不再需要两份工资"——可一线员工看到的现实是 AI 工具输出质量糟糕、Token 排行榜被当成 KPI 来刷而没有真正帮助业务。这是 2026 年以来"AI 提效谎言"在公司内部被戳穿的最直接样本。（HN 2026-06-09 23:59 BJT 提交，184 pts，落在窗口内）

### 法官发现原被告双方均用 AI 撰稿：直接撤销庭审、全员逐出本案
来源: 404 Media
原文：[原文](https://www.404media.co/judge-learns-lawyers-on-both-sides-of-case-used-ai-cancels-trial-kicks-everyone-off-the-case/)
摘要：一名美国法官在庭审中意识到原被告双方的律师都在用 AI 撰写诉状/答辩材料，且 AI 互相援引了对方编造的案例，法官随即宣布撤销庭审并将本案的全体律师踢出代理。报道评论："当两个 AI 互相辩论时，司法系统会输。"事件再次把"律师/法律 AI 输出必须人工复核"的实操问题摆到桌面。在美国法律界，2024 年起已发生多起律师因未核实 AI 引用判例而上庭被罚的案件，但双方同时使用 AI 且 AI 互相喂食对方幻觉，是首个"全案撤销"的极端案例。（HN 2026-06-09 23:30 BJT 提交，79 pts，落在窗口内）

### Apple AI 自动改密码功能上线即被警告：把"凭据控制权"交给 Agent 的四大风险
来源：kylereddoch.me
原文：[原文](https://www.kylereddoch.me/blog/apples-ai-can-now-change-your-passwords-what-could-possibly-go-wrong)
摘要：安全研究员 Kyle Reddoch 详细拆解 Apple 新上线的"AI 自动重置已泄露密码"功能。核心担忧：让 Agent 直接操控账号凭据会引入 prompt injection（提示词注入）、账号锁定、用户同意、设备被入侵四大类风险。具体攻击路径至少包括：(1） 用户点开一份被注入的邮件，Agent 误判"要求改密码"为系统建议并执行；(2) Agent 改密码后无法收到原账号绑定的二次验证，导致用户被锁出；(3) Agent 改密操作不可审计，用户事后无法回溯；(4） 用户被诱导用"换密码"借口把 Agent 引导进钓鱼流程。Apple 把"自主改密"作为 Apple Intelligence 的最新卖点之一，安全社区认为这是把"AI 权限"推到凭据层的最激进一步。（HN 2026-06-10 02:50 BJT 提交，78 pts，落在窗口内）

### Anthropic 警告：全球应保留"暂停 AI"选项
来源：The Guardian
原文：[原文](https://www.theguardian.com/technology/2026/jun/05/anthropic-urges-temporary-pau)
摘要：Anthropic 联合创始人 Jack Clark 与研究所负责人 Marina Favaro 公开提案"全球暂停 AI 研发"，并把"暂停"作为未来监管的合法选项之一写入公司白皮书。报道指出，这一表态与 Anthropic 自身已向 SEC 秘密提交 S-1（估值 9650 亿美元、10 月上市）的"油门"动作形成戏剧性反差，被评论为"IPO 前先竖刹车"的标准操作。Anthropic 是目前唯一在自家旗舰模型（Mythos 5/Fable 5）里默认抑制 AI 研发请求（见上条）的大模型公司，监管层开始把"自我降速"作为可验证指标纳入 AI 公司行为审计。（HN 2026-06-10 04:14 BJT 提交，6 pts，落在窗口内）

### 理想智驾"一号位"郎咸朋与前阿里副总裁任庚联手：昆仑行落户北京亦庄
来源：量子位
原文：[原文](https://www.qbitai.com/2026/06/433560.html)
摘要：理想汽车高级副总裁、自动驾驶总裁郎咸朋（"理想智驾一号位"）与前阿里集团副总裁任庚联合创立的"昆仑行"正式落户北京亦庄经开区，3 月 16 日刚完成注册即跻身"10 天独角兽"。对标特斯拉人形机器人，主打通用具身智能赛道，兼顾本体与大脑。任庚履历横跨华为/阿里/新奥（执掌阿里云中国区期间市占率达 42.1%），郎咸朋则一手从零搭建理想智驾研发体系。昆仑行的差异化技术路线是"物理内生因果"——他们判断当前主流 VLA 行为模仿/世界模型空间预演都只做"看起来对的拟合"，而真正需要的是"物理上站得住的推理"，落地在原生模型、Agent 架构、数据体系三方向。亦庄经开区专班定向支持产业/政策/资金/人才/场景。（量子位 2026-06-09 21:20:05 发布，落在窗口内）

### 腾讯 WorkBuddy 企业版：把"统一入口"作为企业 AI 办公最终答案
来源：量子位
原文：[原文](https://www.qbitai.com/2026/06/432631.html)
摘要：腾讯云副总裁、CodeBuddy & WorkBuddy 负责人刘毅在 2026 腾讯云 AI 产业应用大会上正式发布 WorkBuddy 企业版，定位"企业 AI 办公统一入口"，对标"散装 AI 全家桶"打法。WorkBuddy 平台人均 Token 消耗近 3 个月暴涨 10 倍以上，但"个人很爽，组织无感"的副作用同步出现。WorkBuddy 企业版给出三层能力设计：专家（把岗位 Know-how 封装成 AI，按业务规约自动调用）、助理（云端常驻、7×24 不下班，多助理异步并行）、团队（人和数字员工共处同一项目空间，共享上下文、沉淀为团队 AI 资产）。腾讯同时还放出 Managed Agents 让企业自建智能体体系，可专有云/私有云部署，应对"数据不能出域"的合规需求。同步亮相的产品矩阵包括 Miora（创意智能体）、Ardot（AI 设计协作）、CodeBuddy（编程助手）、CNB（新闻场景 AI）、Onboard（智能体构建治理）、OneAPI（API 统一管理）、ima（企业知识库笔记协同）。（量子位 2026-06-09 09:24:10 发布，落在窗口内）

### 与爱为舞亮相腾讯云 AI 产业应用大会：教育大模型 + 学习 Agent 飞轮
来源：量子位
原文：[原文](https://www.qbitai.com/2026/06/433508.html)
摘要：教育垂类 AI 公司"与爱为舞"在 2026 腾讯云 AI 产业应用大会智慧教育专场发布爱学大模型 + 爱学 AI 学习智能体。核心数据：爱学 APP 课堂形态平均互动频次超 40 次/小时，AI 生成的题目讲解采纳率已超 90%。技术路径走"三阶段能力跃迁"：从对话机器人 → 工具型模型（融合全模态）→ 完整教学 Agent（短/中/长期三层记忆）→ 自主教学系统（围绕长期能力成长的学生仿真模型）。与爱为舞在腾讯云算力底座上做联合推理优化（性能提升 3-4 倍），同时用腾讯云 TRTC 支撑高密度实时互动课堂。腾讯云 + 与爱为舞的协同被定位为"技术共研、难题共克、成果共享"的产业样板。（量子位 2026-06-09 15:11:48 发布，落在窗口内）

### DeepSeek 招募"IDC 设计规划工程师"：从 MW 到 GW 的自建算力基建启动
来源：量子位
原文：[原文](https://www.qbitai.com/2026/06/432735.html)
摘要：DeepSeek 6 月 9 日在官网挂出 IDC 设计规划工程师岗位，明确承诺"参与从 MW（兆瓦）到 GW（吉瓦）级基础设施的规划与建设"，岗位同时面向无经验新人和 7 年以上资深架构师，考核指标聚焦高密度 GPU 集群、液冷与先进散热、新型供配电架构、自动化运维与数字孪生。JD 把"今天的数据中心已经从传统机房演进为支撑 AI 训练与推理的大型工业系统"明文写入岗位收获，对应 DeepSeek 估值据传已达 3500 亿元的本轮融资。从杭钢云计算数据中心到内蒙古乌兰察布、再到杭州总部招募设计规划核心人才，DeepSeek 算力版图正从"借船出海"转向"造船远航"。报道对比 OpenAI Stargate 单园区 5GW/远期 30GW、马斯克 Colossus 1+Colossus 2 的吉瓦级野心，称 DeepSeek 若真建吉瓦级数据中心将是"野心不小"，但行业人士也指出"GW 数据中心盖楼上卡 1-2 年、等电网供应链要 5-8 年"。（量子位 2026-06-09 10:39:19 发布，落在窗口内）

## 🛠️ 技术与基础设施

### 小红书 RED Skill 上线：把"内容社区"长成"另一个 GitHub"
来源：量子位
原文：[原文](https://www.qbitai.com/2026/06/433066.html)
摘要：小红书正式上线 RED Skill（内测中，7 月全量），让创作者可以把"AI Skill"直接挂载到任意一条笔记下，用户看到就能一键复制到自己的 AI 助手（OpenClaw、Claude Code、Codex 等）里跑起来。RED Skill 支持两种上传方式：直接拖文件夹上传，或复制专属口令发给 AI 助手让它代为上传到 SkillHub。归藏的 PPT Skill 在 GitHub 上 1 万+ star，搬到小红书已有 3000 多人下载使用；其他热门 Skill 包括"面试准备助手""动森训练岛""旅行地图""AI 渣男识别器"等。平台同步上线"Red Skill 大赏"活动和 6 月 23 日的"Skill Museum"精选榜单。报道认为"Skill"从 GitHub 技术社区的开发者工具，进化成了"小红书上的内容消费品"，内容/分发/使用闭环首次被压到同一条笔记内。（量子位 2026-06-09 12:07:56 发布，落在窗口内）

### 内蒙跑通"AI 逆袭"新解法：远景星河基地让能源系统与算力系统原生融合
来源：量子位
原文：[原文](https://www.qbitai.com/2026/06/433565.html)
摘要：腾讯集团高级执行副总裁汤道生、腾讯首席 AI 科学家姚顺雨（首次线下公开亮相）在北京对谈上抛出关键判断："AI 下半场最重要的问题，不再只是找到更好的方法，而是找到真正值得解决的问题"——并把 Token 效率推到所有玩家必须攻克的难关。汤道生直言"客户甚至同事们紧盯 Token 消耗"已成行业共同焦虑，Token 成本爆发的底层是"每一个 Token 都要转化为 GPU 的一次次运算，转化为数据中心的一度度电"。远景科技集团董事长张雷在国家能源局"AI+能源"推进会上抛出判断"电力系统正在成为 AI 的主体工程，而非配套"，远景在乌兰察布的"星河基地"尝试吉瓦级能源系统与算力系统的一体化原生融合，从风电光伏出力预测、储能系统毫秒级响应、到算力集群任务编排全部在同一套 AI 电力系统内完成闭环。国际能源署数据：2025 年全球数据中心总耗电 485 太瓦时，AI 负载独占 170 太瓦时；预计 2030 年达 950 太瓦时，仅 AI 专用算力就要消耗 465 太瓦时，超过日本全国年用电量。（量子位 2026-06-09 21:40:54 发布，落在窗口内）

## 💼 行业人物

### AppLovin CEO Adam Foroughi 毕业演讲：面试紧张、害怕演讲、管出最赚钱的 AI 广告公司
来源：量子位
原文：[原文](https://www.qbitai.com/2026/06/433517.html)
摘要：AppLovin 创始人兼 CEO Adam Foroughi 2026 年 5 月在 UC Berkeley 商学院毕业演讲中自陈"大学成绩挺一般的，基本都在玩 Beer Pong"，并坦言毕业后第一份金融工作做得很烂、一年半不到就失业、之后报复性娱乐跑欧洲、回来背上信用卡债、被妈妈赶出家门。Adam 的反直觉人设：面试紧张到出汗、不爱聚光灯、怕上台演讲、恐惧公开发言——但他一手把 AppLovin 从 2012 年自掏腰包创立的"小作坊"带到 2025 年市值约 2500 亿、股价 80 倍涨幅、AI 广告平台 Axon 2.0 深度学习重构后的硅谷最炙手可热 AI 广告公司。Adam 透露"举债 60 亿美元回购股票 + 关闭投资者关系部门"是 2022 年股价暴跌 92% 至暗时刻的三个非常规决定之一，另两条是底层模型重构和引入 Meta 广告核心葛小川。Adam 不认可 Token 预算 KPI："Token 预算跟十年前的招人预算是一回事，你给员工设 Token 消耗排行榜，人们就会为了刷排名去制造一堆没有意义的消耗。"（量子位 2026-06-09 17:12:19 发布，落在窗口内）

## 🏛️ 行业政策与监管

### Bloomberg：中国筹备 2950 亿美元计划 资助全国 AI 建设
来源：Bloomberg
原文：[原文](https://www.bloomberg.com/news/articles/2026-06-09/china-prepares-295-billion-plan-to-fund-nationwide-ai-buildout)
摘要：Bloomberg 6 月 9 日报道，中国正在筹备规模约 2950 亿美元（约合人民币 2.1 万亿元）的国家级 AI 建设资助计划，覆盖全国 AI 数据中心、算力网络与本土 AI 芯片采购，重点扶持使用华为等国产 AI 芯片的数据中心建设。报道指出这是 2025 年同类计划的 2.5 倍规模，目标是到 2027 年形成全球规模最大的国家级 AI 算力底座，同时把对美国芯片的依赖度从 2025 年的 38% 进一步压低。报道同时披露，配套监管框架要求所有享受补贴的数据中心必须把"电力消耗/AI 推理次数"作为可被第三方审计的绿色指标公开。（HN 2026-06-09 22:58 BJT 提交，6 pts，落在窗口内）

### 欧盟裁定 Meta 必须在 WhatsApp 上重新允许第三方 AI 聊天机器人免费接入
来源：Reuters
原文：[原文](https://www.reuters.com/world/eu-regulators-order-meta-allow-rival-ai-chatbots-back-on-whatsapp-for-free/)
摘要：欧盟监管机构正式裁定 Meta 必须重新允许第三方 AI 聊天机器人在 WhatsApp 上免费接入，理由是"AI 助手在超级应用内的互操作义务属于 DMA（数字市场法）核心要求"。这与欧盟 5 月裁定"Apple Siri AI 在欧延迟发布是 Apple 自己的决定"形成同一轮"美式超级应用在欧被动合规"的判决序列。报道分析这是欧盟把"AI Agent 互操作"作为下一代监管抓手的明确信号——AI 入口不能由单一平台垄断。（HN 2026-06-10 03:05 BJT 提交，25 pts，落在窗口内）

## 📰 行业争议

### The Verge：让我们过滤 AI slop 吧，懦夫们
来源：The Verge
原文：[原文](https://www.theverge.com/ai-artificial-intelligence/942909/let-us-filter-ai-slop-google-youtube)
摘要：The Verge 专栏记者 Jess Weatherbed 撰文挑战 YouTube/Instagram/TikTok 等主流平台：既然各家过去一年都在搞 C2PA/SynthID 等内容溯源系统给 AI 内容打标，为什么不能加一个"AI 内容过滤"开关？作者一一询问了 Meta、Google、TikTok、Spotify，无一愿意承诺上线功能。DeviantArt 是少数上线了"AI 内容设置"菜单的平台之一，但藏得极深，且"实测发现没什么用"。Pinterest 也有类似功能，但只能"少看到"AI 修改过的内容。Google CEO Sundar Pichai 近日承认"网上有大量 AI slop，用户需要适应"，被作者反呛"那就给我们过滤"。报道指出这是 AI 标注系统的一个尴尬真相：标注给监管看、给批评者看，但用户实际想要的功能却一个都不上。（HN 2026-06-09 08:01 BJT 提交，11 pts，落在窗口内）

### The Register：开发者明知 AI 代码漏洞百出，还是把货发出去
来源：The Register
原文：[原文](https://www.theregister.com/devops/2026/06/09/devs-know-ai-code-is-riddled-with-holes-but-ship-it-anyway/5252824)
摘要：The Register 6 月 9 日报道，DevOps 社区调研显示 4/5 的企业承认自家生产环境里存在 AI 引入的漏洞应用——但交付压力让安全团队无法阻挡。报道援引内部讨论：开发者明知 LLM 生成的代码在认证、依赖、边界检查上存在问题，但产品上线节奏要求"先用 AI 写好能跑的，再让安全后续修补"，结果是修补几乎从不发生。报道把这种现象命名为"AI 速度债务"——AI 提速的代价是把质量债从代码编写阶段推到了运行时阶段，让安全/可观测性团队承担所有后果。这是继"AI 80% 代码"（Anthropic 自曝）之后，AI 在企业内部代码供应链质量问题上最具体的实证。（HN 2026-06-10 03:37 BJT 提交，20 pts，落在窗口内）

### "Sloppenheimer"配套观察：Apollo 经济学家开怼"AI 引发就业危机"叙事
来源：Apollo
原文：[原文](https://www.apollo.com/wealth/the-daily-spark/where-is-the-ai-jobs-crisis)
摘要：Apollo 首席经济学家 Torsten Slok 在 The Daily Spark 专栏中直怼当前流行的"AI 导致大规模失业"叙事：若 AI 真在引发就业危机，那我们应该看到 JOLTS 职位空缺暴跌、失业率上升——但事实相反，两项数据在过去 6 个月里都呈现温和增长。Slok 用美国劳工统计局 JOLTS、ADP 私营部门就业、BLS 失业率三组数据交叉对比，结论是"AI 替代论"在 2026 年仍缺乏可验证的宏观证据，企业用 AI 的方式更多是"扩大产能"而不是"减少员工"——这与 Amazon Sloppenheimer 现象（员工嘲弄 AI 但未被裁）形成正反互证。（HN 2026-06-10 01:29 BJT 提交，141 pts，落在窗口内）

### Fortune：华尔街一边吃 AI 蛋糕 一边怕 AI 泡沫——SpaceX IPO 前的最后紧张
来源：Fortune
原文：[原文](https://fortune.com/2026/06/08/stocks-ai-bubble-spacex-ipo/)
摘要：Fortune 6 月 8 日分析，过去一周美股大跌的关键叙事是"AI 泡沫要破了"——5 月非农新增 17.2 万远超预期 8.8 万，市场重新押注"美联储不降息甚至加息"，把 AI 板块从"未来现金流"重新放回"现在利息成本"框架里看。Google 上周增发 850 亿美元新股、Meta 准备跟进，叠加 Meta/Oracle 此前通过私募债为 AI 数据中心融资数十亿——"超大云厂商"的新债供给已到 1590 亿美元年规模。文章把三只"AI 板块巨无霸 IPO"（SpaceX、Anthropic、OpenAI 预期年内挂牌）视为这一波抛压的真正导火索：一旦 OpenAI/Anthropic 上市，市场将首次被迫为"私有阶段已被推到 1 万亿+估值"的公司给出明牌定价。（HN 2026-06-09 19:07 BJT 提交，3 pts，落在窗口内）

## 📊 行情表（AI 概念股 / 2026-06-10 A 股盘中）

> 行情数据：东方财富 2026-06-10 A 股盘中（11:24 BJT 截取），仅作 AI 概念股走势参考。

| 板块/个股 | 代码 | 现价 | 涨跌幅 | 昨收 | 开盘 | 最高 | 最低 |
|---|---|---|---|---|---|---|---|
| 上证指数 | 000001 | 3989.26 | -0.52% | 4010.03 | - | - | - |
| 深证成指 | 399001 | 14998.76 | -1.77% | 15268.71 | - | - | - |
| 创业板指 | 399006 | 3881.12 | -2.04% | 3961.75 | - | - | - |
| 科创 50 | 000688 | 1673.43 | +0.62% | 1663.11 | - | - | - |
| 沪深 300 | 000300 | 4760.76 | -0.85% | 4801.81 | - | - | - |
| 科大讯飞 | 002230 | ¥42.91 | -3.59% | ¥44.51 | ¥44.30 | ¥44.40 | ¥42.70 |
| 海光信息 | 688041 | ¥289.51 | +7.95% | ¥268.18 | ¥285.00 | ¥305.80 | ¥283.00 |
| 中科曙光 | 603019 | ¥83.66 | +4.05% | ¥80.40 | ¥81.87 | ¥86.33 | ¥81.87 |
| 寒武纪 | 688256 | ¥1271.72 | +0.13% | ¥1270.01 | ¥1300.00 | ¥1349.90 | ¥1263.00 |
| 拓维信息 | 002261 | ¥30.91 | +10.00% | ¥28.10 | ¥28.11 | ¥30.91 | ¥28.01 |
| 浪潮信息 | 000977 | ¥59.79 | +0.55% | ¥59.46 | ¥58.88 | ¥62.13 | ¥58.80 |
| 中际旭创 | 300308 | ¥1167.46 | -1.06% | ¥1180.00 | ¥1150.00 | ¥1174.00 | ¥1128.80 |
| 新易盛 | 300502 | ¥782.00 | -0.47% | ¥785.73 | ¥770.00 | ¥799.75 | ¥760.10 |
| 金山办公 | 688111 | ¥216.47 | -4.13% | ¥225.80 | ¥221.42 | ¥223.94 | ¥215.18 |
| 同花顺 | 300033 | ¥201.40 | -3.45% | ¥208.60 | ¥206.00 | ¥206.58 | ¥200.77 |
| 润泽科技 | 300442 | ¥78.30 | +2.99% | ¥76.03 | - | - | - |
| 拓尔思 | 300229 | ¥16.00 | -4.76% | ¥16.80 | - | - | - |
| 宝信软件 | 600845 | ¥19.04 | +0.47% | ¥18.95 | - | - | - |

> 板块速读：算力/光模块分化——海光信息/中科曙光/拓维信息涨停或逼近涨停（CPO+国产算力链强势），但 AI 应用层（科大讯飞、金山办公、同花顺、拓尔思）普遍承压回吐昨日涨幅，与昨日腾讯汤道生+姚顺雨公开警示"Token 焦虑"、今日 Fortune/Apollo "AI 叙事"争议升温形成对应。

---

## 🗂️ 今日窗口内已收录但未单列条目

| 来源 | 标题 | 摘要要点 | 链接 |
|---|---|---|---|
| 404 Media | ALPR 将加上手机/AirPod/智能手表追踪器 | 监控厂商 Flock 把车牌识别扩展到所有随身蓝牙设备 | [原文](https://www.404media.co/this-company-will-add-phone-airpod-and-smartwatch-trackers-to-license-plate-readers/) |
| WSOC TV | AI 误识别导致错误逮捕 当事人寻求正义 | 美国又一起 AI 人脸识别冤枉无辜的案例 | [原文](https://www.wsoctv.com/news/local/ai-misidentification-results-wrongful-arrest-man-seeks-justice/I7UQJWV33FBN3LMKHCSXI6FIVA/) |
| Techdirt | 认为 AI 能替代员工的 CEO 都是糟糕的 CEO | 评论 Anthropic/Marc Benioff 等的"AI 减员"主张 | [原文](https://www.techdirt.com/2026/06/09/ceos-who-think-ai-replaces-their-employees-are-just-bad-ceos/) |
| codingwithjesse | 清理 AI Rockstar 开发者留下的烂摊子 | "AI 提效"承诺的隐藏人工成本：被裁掉的人要替他擦屁股 | [原文](https://www.codingwithjesse.com/blog/rockstar-developers/) |
| Computerworld | 特朗普新 AI 行政令——幻觉不只是 LLM 的事 | 评论 AI 行政令对监管 LLM 之外的 AI 系统的盲点 | [原文](https://www.computerworld.com/article/4182531/trumps-new-ai-order-hallucinations) |
| Reddit/BetterOffline | AI 实现盈利在数学上不可能 | 资本开支与推理成本剪刀差分析 | [原文](https://old.reddit.com/r/BetterOffline/comments/1tzwnhi/ai_profitability_is_mathematically_impossible/) |

---

*本早报共 21 条主新闻 + 6 条速览条目，覆盖大模型 / Agent / 具身 / 开源生态 / 企业 AI / 算力基础设施 / 监管 / 安全 / 投资叙事 / 行情 10 个维度。数据采集时间：2026-06-10 11:25 BJT；新闻时间窗：2026-06-09 08:00 - 2026-06-10 08:00 BJT。下次自动更新：2026-06-11 08:00 BJT。*
