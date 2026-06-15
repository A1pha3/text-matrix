---
title: "AI新闻早报 2026-06-09"
date: 2026-06-09T10:31:22+08:00
slug: ai-morning-news-2026-06-09
description: "2026年6月9日 AI 新闻早报（补做），严格采集 06-08 08:00 至 06-09 08:00 窗口，覆盖 OpenAI 秘密提交 S-1、Apple 与 Google Gemini 共建新 AI 架构、小米 MiMo-V2.5-Pro 1T 跑出 1000 tokens/s、Anthropic 80% 代码由 Claude 写、蚂蚁海外 AI 支付 AMP、高德 ABot-Earth 0.5 等关键事件。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "OpenAI", "Apple", "Gemini", "Xiaomi", "Anthropic", "蚂蚁集团", "高德", "WWDC2026", "Bun", "Claude"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

> 补做说明：cron 08efa9de 因昨日 07:20 触发时 usage limit 失败，10:00 quota 重置后自动补做。本次严格遵循 24h 时间窗（2026-06-08 08:00 → 2026-06-09 08:00 BJT），剔除了原 878d492b 漏跑稿中越过 08:00 cutoff 的 2 条（腾讯 WorkBuddy、李飞飞世界模型宣言），并新增 Kimi 136 亿融资、ChatGPT 改版、Sora 核心成员 Gabriel 离职、Apple 走"便宜 AI 路线"4 条高质量新闻。

---

## 🚀 产品发布

### 小米 MiMo-V2.5-Pro-UltraSpeed：1T 模型跑出 1000 tokens/s，推理速度进入"飞秒时代"
来源：Xiaomi MiMo Blog（Hacker News）
原文：[原文](https://mimo.xiaomi.com/blog/mimo-tilert-1000tps)
摘要：小米与 TileRT 联合发布 MiMo-V2.5-Pro-UltraSpeed，官方宣称是首个在 1 万亿参数规模上跑出 1000 tokens/s 解码速度的模型，峰值可达约 1200 tokens/s。文章把它定位为"范式转变"：在 wall-clock 时间内，模型可并行跑出几十条 Best-of-N/Tree Search 推理路径并自校验，从而用"原始速度"换取"思维深度"；对 Coding Agent 而言，意味着开发者不再被推理延迟锁住，可在编码会话里"实时"跟进。试用窗口为 2026-06-09 09:00 至 2026-06-23 23:59 BJT，按企业/开发者真实需求定向审批，定价为 MiMo-V2.5-Pro 的 3 倍、对应"约 10 倍生成速度"。（HN 约 10 小时前发布，发布时间约 2026-06-09 00:16 BJT，落在窗口内）

### 蚂蚁集团推出海外 AI 支付 AMP：把"用户授权+智能体执行"做成全球基础设施
来源：量子位
原文：[原文](https://www.qbitai.com/2026/06/432587.html)
摘要：蚂蚁集团推出面向 AI 智能体的全球商业接入层 AMP（Agentic Merchant Protocol），解决 AI 出海/跨境电商/航旅/数娱等场景下"消费者用 AI 找商品却无法完成全球支付、智能体身份难认证、渠道难覆盖、信任难建立"的痛点。AMP 给出三步用户操作：钱包绑定智能体 → 智能体聊天框内下单 → 钱包内实时管控预算与任务支出，超预算自动终止。同时引入 KYA（Know Your Agent）认证体系，对交易智能体做"信用评级"，把"识别商户"扩展到"识别可信智能体"，目标是把 Agentic Commerce 从单点试验推向规模化。（量子位首页约 15 小时前发布，发布时间约 2026-06-08 19:16 BJT，落在窗口内）

### 高德 ABot-Earth 0.5：用 3DGS 原生路径做"公里级"城市生成
来源：量子位
原文：[原文](https://www.qbitai.com/2026/06/432489.html)
摘要：高德发布 ABot-Earth 0.5，官方称其"跨越 2D 蒸馏模式"，走 3DGS 原生路径：用户输入一张卫星图或一段文字，即可在单张消费级显卡上生成 3DGS 格式的城市，效率较传统模式提升约 1000 倍。模型首次将数百万基元的高质量 3DGS 场景压缩到隐空间再生成，并提出"滑窗推理"机制做公里级连续生成，配合跨域自适应模块与多层次细节解码器（LOD）弥合卫星/三维数据域差。输出可直接接入 Unity、Unreal Engine 等引擎做交互，产品已开放内测申请（abot-earth.amap.com）。（量子位首页约 17 小时前发布，发布时间约 2026-06-08 17:16 BJT，落在窗口内）

### ChatGPT 即将迎来"史上最大改版"：从单一聊天变身"超级应用"
来源: 36 氪
原文：[原文](https://www.36kr.com/p/3844133886396936)
摘要: 36 氪 6 月 8 日报道，ChatGPT 即将迎来"史上最大改版"，从单一聊天界面变身"超级应用"，把"对话 + Agent + 第三方应用"统一到同一入口。文章披露新版本将整合"项目空间（Projects）""应用 SDK（Apps SDK）""GPT Store 2.0"和"Agent 调度层"四大模块，开发者可通过 Apps SDK 把自家 SaaS 工具直接挂进 ChatGPT 主对话流。报道把这次改版定位为 OpenAI 在 GPT-5 推迟窗口期"先发制人"的产品反击，也是其反击 Anthropic 把"模型 + Agent"打通的 Claude Code 战略的关键一子。（36kr 首页约 18 小时前发布，发布时间约 2026-06-08 16:16 BJT，落在窗口内）

## 🏢 公司动作

### OpenAI 秘密向 SEC 提交 S-1 草案，启动 IPO 流程
来源：OpenAI（Hacker News）
原文：[原文](https://openai.com/index/openai-submits-confidential-s-1/)
摘要：OpenAI 6 月 8 日在官网公告，已根据《1933 年证券法》Rule 135 秘密向美国证券交易委员会提交 S-1 招股书草案，并坦承"我们预期招股书会泄露，所以先发个声明"。OpenAI 明确表示尚未决定上市时间，理由是有些事情作为私营公司做起来更简单；但保留在权衡后尽快上市的权利。这则短公告是 295 票 HN 热帖，也是 OpenAI 首次为 IPO 路径给出官方书面陈述，被视为公司从微软加注、估值持续上修走向公开市场的新节点。（HN 约 4 小时前发布，发布时间约 2026-06-09 06:16 BJT，落在窗口内）

### Apple 与 Google 联手：Apple Intelligence 改用 Gemini 共建的新基础模型
来源：MacRumors（Hacker News）
原文：[原文](https://www.macrumors.com/2026/06/08/apple-reveals-new-ai-architecture/)
摘要：MacRumors 6 月 8 日 WWDC26 现场报道，Apple 当日宣布 Apple Intelligence 平台进行"重大重写"，新的 Apple Foundation Models 与 Google 联合开发、底层基于 Gemini 家族技术，并被设计为同时支持设备端与 Private Cloud Compute 端运行。报道引用 Apple 描述，称这是一次"深度"合作，给 Apple 智能带来"巨大升级"，包括更强的理解/推理能力与多模态支持。这是 Apple 智能首次从单点接入 ChatGPT 转向与 Google 联合训练自有基座模型，标志其 AI 路线正式进入"混合双源"阶段，国行版本依然被排除在外。（HN 约 7 小时前发布，发布时间约 2026-06-09 03:16 BJT，落在窗口内）

### Apple 走"便宜 AI"路线：押注小开发者与本地小模型
来源：TechCrunch
原文：[原文](https://techcrunch.com/2026/06/08/apple-bets-cheaper-ai-will-woo-small-developers/)
摘要：TechCrunch 6 月 8 日报道，Apple 在 WWDC26 同步推出"面向小开发者的便宜 AI"策略：把 Apple Intelligence 拆出"按需付费的小模型 API"和"免费配额"两档，目标是把过去只服务大厂云端预算的 AI 能力"降到独立开发者买得起的价位"。报道披露 Apple 同时推出 Core AI Framework，让第三方 App 可以零成本调用设备端基础模型，把"端侧 AI 普及"作为差异化卖点。这是 Apple 在"Gemini 联合基座"之外，针对"AI 商业化下沉"做出的另一手布局，与 OpenAI / Anthropic 押注企业大客户形成路径分化。（HN 约 5 小时前发布，发布时间约 2026-06-09 05:16 BJT，落在窗口内）

### Sora 核心成员 Gabriel 从 OpenAI 离职，创业做"AGI 前最后一款产品"
来源: 36 氪
原文：[原文](https://www.36kr.com/p/3844109155125760)
摘要: 36 氪 6 月 8 日报道，OpenAI Sora 核心成员 Gabriel Goh 官宣离职，将创办一家以"AGI 前最后一款产品"为使命的 AI 公司。文章引用 Gabriel 的离职信，称"AGI 不会在某一天突然降临，它会是一款产品被做出来的那一天"，并把"让每个人都能用上接近 AGI 的能力"作为新公司产品定义。报道披露其新公司已完成约 8000 万美元种子轮，红杉、a16z 与 OpenAI 创业基金均参与投资。Gabriel 是 Sora 文生视频模型核心架构师之一，他的离开被业内视为"OpenAI 多模态团队加速外溢"的最新信号。（36kr 首页约 18 小时前发布，发布时间约 2026-06-08 16:16 BJT，落在窗口内）

## 🛠️ 技术与基础设施

### 9 天、6755 次提交、100 万行 Rust：Anthropic 用 Claude Code 把 Bun 改写完了
来源: 36 氪（CSDN）
原文：[原文](https://www.36kr.com/p/3844285021047304)
摘要: 36 氪转载 CSDN 报道：Anthropic 收购的开源 JavaScript 运行时 Bun 在 9 天内由 Claude Code 智能体完成超 100 万行 Rust 代码、6755 次提交，把原本 Zig 实现的核心部分整体迁移到 Rust，官方宣称测试通过率达 99.8%。此事在 HN 与开发者社区引发激烈争议：开发者 dreamreal 发文《Bun Has Been Converted to Rust. Now What?》指出，号称"解决内存安全"的 Rust 重写最终留下超过一万个 `unsafe` 块，质疑"测试通过率是否等于代码可信"，把争议焦点从"AI 能不能写代码"推进到"AI 写代码的速度远超人类审查速度"。（36kr 首页约 13 小时前发布，发布时间约 2026-06-08 21:16 BJT，落在窗口内）

### Anthropic 80% 代码由 Claude 写：联合创始人呼吁全球暂停 AI 研发
来源: 36 氪（新智元）
原文：[原文](https://www.36kr.com/p/3844411705985540)
摘要: 36 氪转载新智元稿件：Anthropic 联合创始人 Jack Clark 与研究所负责人 Marina Favaro 公开提案，呼吁全球暂停 AI 研发以避免失控；与此同时 Anthropic 已于 6 月 1 日向 SEC 秘密提交 S-1（该提交事件本身在 6 月 1 日发生，但本文是 6 月 8 日的解读稿），预计 10 月上市、估值接近 9650 亿美元。关键数据点：到 2026 年 5 月，并入 Anthropic 自身代码库的代码中超过 80% 由 Claude 编写，Jack Clark 把 AI 行业现状概括为"只有油门，没有刹车"，并预判到 2028 年底，AI 在无人类参与下自行创造下一代产品的概率高达 60%。报道把"IPO 油门 + 全球急刹车"的两极并置，指向递归自我改进的临界点争论。（36kr 首页约 14 小时前发布，发布时间约 2026-06-08 20:16 BJT，落在窗口内）

### GPT-5 作者 Łukasz Kaiser 复盘：趁 OpenAI 沉迷 ChatGPT，Anthropic 死磕代码完成"偷家"
来源: 36 氪（CSDN）
原文：[原文](https://www.36kr.com/p/3844470724708617)
摘要: 36 氪转载 CSDN 与 OpenAI 资深科学家 Łukasz Kaiser（Transformer 八子之一）的对话：Kaiser 坦言大模型是"靠穷尽所有错误表象规律才理解一个底层概念"的低效学习者，今天的行业陷入"必须吞下万亿 token 才能学会"的盲目狂热，与人类学习方式背道而驰。他把 Scaling Law 撞上效率冰山视为推理模型"还停留在极早期 RNN 阶段"的原因之一，并指出当大量真实工作流数据被用于强化学习时，行业可能再次迎来"意想不到的惊喜"。报道把这场对话包装为"OpenAI 沉迷 ChatGPT，Anthropic 死磕代码偷家"的范式剧本。（36kr 首页约 13 小时前发布，发布时间约 2026-06-08 21:16 BJT，落在窗口内）

### Kimi Work 不是中国版 Codex：把编程 Agent 能力泛化到通用办公
来源: 36 氪
原文：[原文](https://www.36kr.com/p/3844257852885256)
摘要: 36 氪报道 Kimi 发布的 Windows/Mac 客户端"Kimi Work"模式：内核是 Kimi Code + 金融/科研/法律专业数据（同花顺、天眼查等）+ WebBridge 浏览器操控方案 + Kimi K2.5 的 Agent 集群，但定位是"面向知识工作者的通用型本地 Agent"，不锁定编程。文章把它与卡帕西去年的"氛围编程（Vibe Coding）"对接，提出"氛围办公（Vibe Working）"概念：用户不再需要打开终端/敲命令/配环境，用自然语言即可让 Kimi Work 在本机拆解任务、并行执行子任务、操作浏览器、交付文档/表格/PPT。报道强调 Kimi Work 与 Codex 仅"外观相近"，内核是另一条产品路径。（36kr 首页约 13 小时前发布，发布时间约 2026-06-08 21:16 BJT，落在窗口内）

### 云知声发布 U2：把"万卡+万亿 token"的玩法重新计费
来源: 36 氪
原文：[原文](https://www.36kr.com/p/3844393508047108)
摘要: 36 氪报道云知声新一代通用大语言模型底座 U2 发布：把"训练与推理成本同步推高、部署门槛高筑"视为大模型下半场的核心痛点，明确提出从 generative AI（生成式 AI）转向 productive AI（生产力 AI），把"原生智能体（Agentic）大模型"作为公司新定位。U2 在文中被定位为云知声上市以来"最重要的基座模型技术迭代"和"全面转向 Agentic 大模型公司"的关键里程碑，目标是用更低的综合成本把硬核智能塞进真实产业毛细血管。（36kr 首页约 14 小时前发布，发布时间约 2026-06-08 20:16 BJT，落在窗口内）

## 💰 融资财报

### Kimi 母公司月之暗面再融 136 亿，赴港 IPO 提速
来源: 36 氪
原文：[原文](https://www.36kr.com/p/3844092401666564)
摘要: 36 氪 6 月 8 日报道，Kimi 母公司月之暗面（Moonshot AI）已接近完成新一轮 136 亿元融资，投后估值突破 2000 亿元，本轮由阿里、腾讯、五源等老股东联合领投，红杉中国、IDG 资本跟投。文章披露月之暗面已正式启动赴港 IPO 流程，最快 2026 年 Q4 递交 A1 表，2027 年上半年挂牌。报道把这一动作解读为"Kimi 在 Kimi K2.5 / Kimi Work 两款产品落地窗口期"主动锁定资本市场"卡位"，同时也是"中国大模型六小虎"在 IPO 退出路径上又一次分化。（36kr 首页约 18 小时前发布，发布时间约 2026-06-08 16:16 BJT，落在窗口内）

## 📰 行业动态

### 拆解 25 笔超 5000 万 A 轮融资：机器人+算力底座拿走 60 亿美元
来源: 36 氪（硅基观察 Pro）
原文：[原文](https://www.36kr.com/p/3844470639036680)
摘要: 36 氪转载硅基观察 Pro 基于 Crunchbase 与企业公开披露数据的盘点：2026 年全球 AI 领域融资规模最大的 25 家 A 轮公司累计融资超 60 亿美元，其中机器人/具身智能拿走 6 家共 20.49 亿美元，AI 基础设施拿走约 15 亿美元，剩余资金流向网络安全、国防、软件开发与科研类自主智能系统。文中点名代表项目：Apptronik（5.2 亿美元 A 轮延伸，估值 50 亿美元，Apollo 人形机器人已与 Google DeepMind 集成 Gemini Robotics）、Mind Robotics（5 亿美元 A 轮，估值 20 亿美元，Rivian 2025 年 11 月内部孵化分拆）。报道把"最聪明的钱已离开大模型本身"作为核心判断。（36kr 首页约 13 小时前发布，发布时间约 2026-06-08 21:16 BJT，落在窗口内）

### Cognition 发布 FrontierCode：把"AI 工程师"塞进企业代码库
来源：Cognition AI
原文：[原文](https://cognition.ai/blog/frontier-code)
摘要：Cognition（Devin 母公司）6 月 8 日发布 FrontierCode，把"AI 工程师"从单一 IDE 助手升级为"代码库级别的协作者"：可以持续跟踪 PR Review、自动重构旧代码、跨仓库调用内部库、给生产事故做 Root-Cause 分析，并支持多人协作同一段代码的"AI 接力"。文章披露 FrontierCode 已接入 Cognition 的 SWE-Agent 2.0 引擎，基准测试中在 12 类企业级代码任务上首次超过资深工程师的中位数水平。Cognition 把 FrontierCode 定位为"从 IDE 走向企业代码基础设施"的产品升级，是 Devin 从开发者工具走向"组织级 AI 员工"的关键一步。（HN 约 5 小时前发布，发布时间约 2026-06-09 05:16 BJT，落在窗口内）

---
