---
title: "AI副业早报 2026-06-23"
date: 2026-06-23T08:31:53+08:00
slug: ai-side-hustle-morning-2026-06-23
description: "2026年6月23日 AI 副业早报，覆盖 V2EX 招聘：web3/AI+DEX/Quant 远程全职、TAPON AI Agent Team 回归北京线下、宁波物流 SaaS AI 全栈；以及 Reddit 独立开发：parry AI 反击助手、Voice AI Agent 房产获客、本地 Agent 编排库、Modly v0.4.0 嵌入 Ollama。"
draft: false
categories: ["行业快讯"]
tags: ["AI副业", "V2EX", "Reddit", "独立开发", "AI招聘"]
hiddenFromHomePage: true
---

🦞 每日09:00自动更新

---

## 💼 招聘/项目

### web3/AI+DEX/Quant 招聘：AI 测试开发 / 量化交易系统 / Flutter+React / CCO/CFO（远程全职）
来源: V2EX
发布者: justinX
原文: [原文](https://www.v2ex.com/t/1222056)
摘要: 加密交易所/DEX 团队一次放出 6 个岗位，亮点在「资深 AI 测试开发工程师（web3）」要求用 AI Agent 或 LLM 辅助做智能用例生成、缺陷预测、自愈脚本等，是直接面向 AI 落地的测试岗。运营经理要会预测市场用户增长，量化交易系统工程师 5-8 年后端背景负责低延迟撮合，并提供新加坡/香港 EP 通道；前端、CCO/CFO、数据开发同步招。原文给出的 Base64 邮箱和多个飞书招聘链接，对有加密背景 + AI 测试/后端经验的工程师是一次性投多个对口岗位的高密度机会。

### 远程 7 个月后回归线下：TAPON AI Agent 团队招 UI/后端/产品（北京）
来源: V2EX
发布者: heyao114
原文: [原文](https://www.v2ex.com/t/1222053)
摘要: 作者所在团队已经远程 7 个月且刚结束一个月旅行，6 月完成核心功能发布、种子用户内测超出预期，现要扩 AI Agent Team 并回到北京线下办公。团队方向是「个性化 AI Agent」：base 记忆、用户偏好、人格化回答，目前在招 4 年以上 UI 设计师、Agent/AI 工作流后端开发以及产品经理，奖金慷慨、不卷加班/不写日报。原文贴出完整岗位 JD 和「创新/Nice/高效」三条团队文化，对想进独立 AI Agent 创业团队又接受一线城市线下节奏的人是一个明确窗口。

### [宁波][全栈] 鑫淼国际物流招 AI 方向全栈工程师
来源: V2EX
发布者: codermz
原文: [原文](https://www.v2ex.com/t/1221885)
摘要: 帮宁波鑫淼国际物流发的招聘，方向是把 AI 真正落到物流 SaaS 业务里，岗位要求熟悉 OpenAI/DeepSeek 大模型应用、有 Prompt/Agent/AI 工作流开发经验，能独立完成方案设计与落地。技术栈是 Node.js / Express / Prisma / MySQL / JavaScript，工作地宁波东部新城可协商，薪资 15K-25K/月、优秀者可谈。对刚入门 AI 应用层、想找一份"AI+传统行业"全栈岗位练手并接触 Prompt 和 Agent 落地的工程师是一个相对友好且门槛清晰的机会。

## 💰 赚钱机会

### I built parry, an AI reply assistant that helps you "counter" any message
来源: Reddit r/SideProject
发布者: u/uhh_nomaly
原文: [原文](https://www.reddit.com/r/SideProject/comments/1ud11ya/)
摘要: 作者把过去在 ChatGPT/Claude 里手动"喂对方消息让 LLM 帮我回"的流程做成了一个独立 iOS App：选 Tone 就拿回 4 条候选回复，可一键换 Tone、重新生成、上传截图或照片让 AI 判断是「要回的内容」还是「只是背景」，还内置语音听写。Selftext 直接讨论"多 Tone 候选+快速重生成"相对复制粘贴到 ChatGPT 是不是真值这个钱，并明确因为每条都跑 Claude API、连免费档都在亏 token。对想做 AI 工具型副业的人来说，这是一个"明确说出自己定价逻辑"和"承认自己仍在验证"的真实样本。

### I built a Voice AI Agent that instantly calls your leads from Paid Ads
来源: Reddit r/SideProject
发布者: u/Clear_Performer_556
原文: [原文](https://www.reddit.com/r/SideProject/comments/1ud0qm8/)
摘要: 作者把 Voice AI Agent 接到付费投流表单后面：线索一留资 60 秒内 AI 就打电话，按自然对话问"人在哪、什么时候看房、是买还是租"，通过筛选再把意向客户写进 CRM，让销售只追高意向线索。原帖定位是房地产垂类，但工作流完全可以拆出来给医美、教育、本地服务等同样"线索贵、需要 60 秒响应"的行业复用。对正在评估「AI + 实时电话 + CRM 串联」是否值得做副业/小工作室的独立开发者，是一个完整的端到端 demo。

## 🚀 AI项目

### Most agent tools make every agent identical — so I built one where each agent stays independent
来源: Reddit r/LocalLLaMA
发布者: u/facu_75
原文: [原文](https://www.reddit.com/r/LocalLLaMA/comments/1ucuy0q/)
摘要: 作者认为主流 Agent 框架为了"易 spawn"都把 agent 做成同质化线程、固定配置，而自己正在写的 orchestration 库坚持"每个 agent 独立进程、独立 workspace、独立 harness/toolchain/secrets"，代价是声明舰队更繁琐，所以他把"声明 + 驱动"这两件事单独抽出来用 agents.yaml + .agents 目录结构解决。这是一个面向 Agent 工具链/中间件副业的开源方向，开发者想差异化可以从"agent 个性化 + 配置可声明"切入，而不是再造一个"又一个 spawn 工具"。

## 🛠️ 工具推荐

### Released v0.4.0 — you can now use Ollama inside Modly
来源: Reddit r/LocalLLaMA
发布者: u/Lightnig125
原文: [原文](https://www.reddit.com/r/LocalLLaMA/comments/1ucqgau/)
摘要: Modly 是一个开源桌面端本地 AI 3D 生成应用，v0.4.0 的核心更新是把 Ollama 嵌入到 Modly 内部的 Chat Mode，让本地模型直接在 3D 生成工作流里"理解当前 Modly 工程"并引导用户走完生成步骤。作者把路线图讲得很清楚：先做能听懂项目上下文的本地 agent，后面再扩展为能改工作流的副驾。对想用开源+本地 AI 切入"创意工具副驾"细分赛道的开发者，这个 3D 垂类的 Chat Mode 是一个能直接 fork 思路、改成视频/音频/平面设计副驾的现成模板。

## 🤖 Agent 工具

### I built a durable runtime for AI agents that don't lose state after restarts
来源: Reddit r/SideProject
发布者: u/r2werks
原文: [原文](https://www.reddit.com/r/SideProject/comments/1uczf6w/)
摘要: 作者观察到一个普遍痛点：Agent 演示时很顺、生产环境却各种掉链子——宿主机重启后文件丢失、浏览器状态没了、长任务跑到一半被 kill、agent 重复劳动。正在做的 Jettson 给每个 Agent 一个持久化 Linux workspace（文件系统 + 浏览器 + shell + HTTP + 内存 + 可恢复执行），并主动在帖子里问"做 agent 的人现在是怎么处理持久化/恢复的"。原文底下的评论已经出现 "SQLite for checkpoints" 的标准答案，对想以"Agent 持久化 runtime"做副业/小项目的开发者，这是一条明确的需求信号 + 真实工程讨论。

---

🦞 每日09:00自动更新

**数据来源**：V2EX 酷工作、Reddit r/SideProject、Reddit r/LocalLLaMA

**⚠️ 链接核查清单（已逐条验证，仅列正文实际引用链接）：**
- ✅ https://www.v2ex.com/t/1222056 - web3/AI+DEX/Quant 招聘正文与标题一致
- ✅ https://www.v2ex.com/t/1222053 - TAPON AI Agent Team 招 UI/后端/产品正文与标题一致
- ✅ https://www.v2ex.com/t/1221885 - 宁波鑫淼国际物流 AI 全栈正文与标题一致
- ✅ https://www.reddit.com/r/SideProject/comments/1ud11ya/ - parry AI reply assistant 标题/正文/作者一致
- ✅ https://www.reddit.com/r/SideProject/comments/1ud0qm8/ - Voice AI Agent for paid leads 标题/正文/作者一致
- ✅ https://www.reddit.com/r/LocalLLaMA/comments/1ucuy0q/ - Independent agent orchestration 标题/正文/作者一致
- ✅ https://www.reddit.com/r/LocalLLaMA/comments/1ucqgau/ - Modly v0.4.0 + Ollama 标题/正文/作者一致
- ✅ https://www.reddit.com/r/SideProject/comments/1uczf6w/ - Jettson durable AI agent runtime 标题/正文/作者一致
