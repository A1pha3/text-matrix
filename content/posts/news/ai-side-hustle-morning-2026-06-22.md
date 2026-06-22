---
title: "AI副业早报 2026-06-22"
date: 2026-06-22T08:21:00+08:00
slug: ai-side-hustle-morning-2026-06-22
description: "2026年6月22日 AI 副业早报，覆盖过去 24 小时 V2EX 招聘与办公自动化小单、AI 副业安全警示，以及 Reddit SideProject/LocalLLaMA 的 AI 健身教练、本地 MCP 网关等独立项目。"
draft: false
categories: ["行业快讯"]
tags: ["AI副业", "V2EX", "Reddit", "独立开发"]
hiddenFromHomePage: true
---

🦞 每日09:00自动更新

---

## 💼 招聘/项目

### [远程兼职] 招 Chatwoot 二开 / AI 客服方向高级全栈或技术负责人
来源: V2EX
发布者: ${encodeURIComponent(memberUsername)}
原文: [原文](https://www.v2ex.com/t/1221698)
摘要: 团队在做面向海外跨境业务的 AI 客服与客户转化系统，方向是 Chatwoot 二开 + AI Agent + RAG 知识库 + 多语言实时翻译 + 人工接管。已有 Chatwoot 企业版源码环境、本地测试环境和 PostgreSQL/Redis 基础环境，目前寻找有经验的高级全栈或 Chatwoot 二开工程师，第一阶段主要是共同梳理方向和 MVP 范围，适合熟悉开源客服系统且愿意以兼职/顾问方式参与 AI 项目落地的人。

### [远程] Native 招聘 devops、golang、rust（AI 工具栈报销福利）
来源: V2EX
发布者: ${encodeURIComponent(memberUsername)}
原文: [原文](https://www.v2ex.com/t/1221763)
摘要: 新加坡主体公司 native.org 招聘 devops、golang、rust 工程师，满一年可申请 transfer 到新加坡并由公司办理 EP 或报销移民费用。除了标准 5 天工作制外，明确把"全额报销 Claude Code Max、Cursor Pro 等顶级 AI 编程助手"列为福利，意味着岗位工作流直接嵌入 AI 辅助编程，适合想借机把 AI 工具栈用到极致并长期派驻海外的工程师。

## 💰 赚钱机会

### 想验证一个 99 元办公自动化小单：Excel/PPT/脚本类需求有人需要吗？
来源: V2EX
发布者: ${encodeURIComponent(memberUsername)}
原文: [原文](https://www.v2ex.com/t/1221792)
摘要: 作者提出一个面向个人和中小团队的"99 元起办公自动化小单"试水：服务范围覆盖 Excel/CSV 数据清洗与透视、PPT/Word 排版、网页样式和 JS 脚本、批量文件处理等 1-2 小时可交付的需求，并主动划定不接违法违规、刷量、密码证件医疗等高敏数据的边界。这条帖子本质上是在公开招募第一批"小单验证客户"，对想用 AI + 脚本做副业但不知道如何起步的工程师来说是可参考的定价和边界模板。

### 问一个私密但又迫切的问题：进入 AI 时代后，大家用 AI 做的项目都实实在在挣到钱了吗？
来源: V2EX
发布者: ${encodeURIComponent(memberUsername)}
原文: [原文](https://www.v2ex.com/t/1221724)
摘要: 帖子直接抛出现阶段副业圈最真实的问题——到底有多少 AI 项目真正挣到钱，并邀请大家晒一晒自己做的项目和收入。正文虽然简短，但讨论氛围鼓励"晒项目和数字"，是评估当前 AI 副业变现真实状况的高密度信息源。回复里有相当比例的实操者晒单，比单纯看新闻更能反映"个人做 AI 项目能不能养活自己"。

## ⚠️ 风险提示

### 应聘 AI Agent 岗位前请保护好自己的代码
来源: V2EX
发布者: ${encodeURIComponent(memberUsername)}
原文: [原文](https://www.v2ex.com/t/1221808)
摘要: 作者认为当前 AI Agent 处在爆发期又恰逢企业降本增效，部分公司会以"面试/收集简历"为名套取多个候选人的项目方案，再用 Vibe Coding 拼装成产品，违法成本极低。帖子建议项目里含较多 Issue、PR、Commit、部署指南、本地开发指南和 Release 的独立开发者考虑闭源、仅提供演示地址，并为项目添加 Apache/AGPL 等开源协议以增加法律威慑。这条对所有正在把 AI 项目作为求职敲门砖或副业作品的开发者都是必读警示。

## 🚀 AI项目

### I made a simple iOS lifting app where an AI coach knows every exercise, set, and rep you've ever logged
来源: Reddit r/SideProject
发布者: YardOk3457
原文: [原文](https://www.reddit.com/r/SideProject/comments/1uc4ep0/)
摘要: 作者做了一款 iOS 力量训练 App，AI 教练会记住你每一次训练的动作、组数和次数，并据此给出建议，而不是简单地复读 ChatGPT 式鼓励。原帖在 Selftext 里强调它"知道什么对你的训练最好"，目标是把 AI 当成有上下文记忆的真正教练，而不是聊天机器人；对想用 AI 切入健身垂类的独立开发者是有参考价值的产品差异化样本。

### I built a local-first MCP gateway so my agents load 3 tools instead of hundreds (open source)
来源: Reddit r/LocalLLaMA
发布者: kydude
原文: [原文](https://www.reddit.com/r/LocalLLaMA/comments/1uc52eh/)
摘要: 开发者构建了一个本地优先（local-first）的 MCP 网关，让 Agent 一次只加载约 3 个工具而不是数百个，意图是用网关层解决 MCP 生态里"工具爆炸"导致的上下文浪费和选择困难。开源定位意味着普通工程师可以把它直接接进 Claude/Cursor 等客户端，对想给 AI Agent 做中间件副业或在本地 LLM 工作流里卖工具路由服务的开发者是一种明确的差异化方向。

### I built a local AI translator with streaming output (open source)
来源: Reddit r/LocalLLaMA
发布者: HolaTomita
原文: [原文](https://www.reddit.com/r/LocalLLaMA/comments/1uc4s9x/)
摘要: 作者基于本地模型实现了一款支持流式输出的开源 AI 翻译工具，主打"本地、隐私、流式"三件套，把翻译延迟降到可逐句接收的程度。对面向跨境业务或隐私敏感场景的副业项目来说，这种"本地 + 实时"的组合是付费订阅或 API 转售的天然切入点，比直接用云端翻译服务有更清晰的卖点。

## 🛠️ 工具推荐

### I built a tool that connects Google Trends and Reddit sentiment to stocks
来源: Reddit r/SideProject
发布者: reupped
原文: [原文](https://www.reddit.com/r/SideProject/comments/1uc3293/)
摘要: 开发者把 Google Trends 关键词热度与 Reddit 帖子情绪合并成对个股的辅助信号，并把这个工作做成了一个独立工具。原帖主动征集改进方向，对想要切入"散户投研副业"或"另类数据 SaaS"的工程师有借鉴意义——它示范了如何把免费公开数据二次加工成可量化信号，避免直接和彭博/万得竞争。

### Looking for feedback on my browser-based video creation tool
来源: Reddit r/SideProject
发布者: Sarntinel
原文: [原文](https://www.reddit.com/r/SideProject/comments/1uc56an/)
摘要: 作者在做一款浏览器内运行的视频创作工具，目标用户是希望快速剪辑和分享但不想装桌面软件的内容创作者。Selftext 重点在征求反馈而非硬卖，是典型"先验证再变现"的独立开发节奏，适合正在评估"工具型副业 vs 内容型副业"的开发者参照其冷启动做法。

### Built a vibed out habit & task tracker
来源: Reddit r/SideProject
发布者: SouthDetective1117
原文: [原文](https://www.reddit.com/r/SideProject/comments/1uc2xhx/)
摘要: 作者用 vibe coding 的方式快速搭了一款习惯与任务追踪工具，重点是验证"用 AI 写小工具到底能做到什么程度"。对想用 AI 做个人 productivity 副业、又不想从零设计 UI 的开发者是一条低门槛路径，可以直接 fork 思路做差异化收费版本。

---

🦞 每日09:00自动更新

**数据来源**：V2EX 酷工作、Reddit r/SideProject、Reddit r/LocalLLaMA

**⚠️ 链接核查清单（已逐条验证，仅列正文实际引用链接）：**
- ✅ https://www.v2ex.com/t/1221698 - Chatwoot 二开 / AI 客服兼职正文与标题一致
- ✅ https://www.v2ex.com/t/1221763 - Native devops/golang/rust 招聘含 AI 工具栈福利
- ✅ https://www.v2ex.com/t/1221792 - 99 元办公自动化小单正文与标题一致
- ✅ https://www.v2ex.com/t/1221724 - AI 时代项目挣钱讨论正文与标题一致
- ✅ https://www.v2ex.com/t/1221808 - AI Agent 岗位前保护代码正文与标题一致
- ✅ https://www.reddit.com/r/SideProject/comments/1uc4ep0/ - iOS lifting app with AI coach（23:24 UTC）
- ✅ https://www.reddit.com/r/LocalLLaMA/comments/1uc52eh/ - Local-first MCP gateway（23:54 UTC）
- ✅ https://www.reddit.com/r/LocalLLaMA/comments/1uc4s9x/ - Local AI translator streaming（23:41 UTC）
- ✅ https://www.reddit.com/r/SideProject/comments/1uc3293/ - Google Trends + Reddit sentiment stocks（22:23 UTC）
- ✅ https://www.reddit.com/r/SideProject/comments/1uc56an/ - Browser-based video creation tool（23:59 UTC）
- ✅ https://www.reddit.com/r/SideProject/comments/1uc2xhx/ - Vibed out habit & task tracker（22:17 UTC）
