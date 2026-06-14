---
title: "AI副业早报 2026-06-13"
date: 2026-06-13T08:40:00+08:00
slug: ai-side-hustle-morning-2026-06-13
description: "2026年6月13日 AI 副业早报：过去 24h 内 V2EX 独立 FDE 在大阪做制造业 AI 落地项目、硅谷公司招 AI Infra 工程师、东八区远程、生物医药招 AI 应用工程师 35-70 万、AI 陪伴产品招远程岗位、ChatVault 上 Chrome Web Store、Hermes 开源 AI Agent 击败付费工具、llmjob LLM 选 GPU 工具、寻找 Go&Vue3 合伙人 50/50、用 AI 写中医自诊网站等共 9 条。"
draft: false
categories: ["行业快讯"]
tags: ["AI副业", "V2EX", "Reddit", "FDE", "远程工作", "AI招聘", "开源Agent", "独立开发"]
hiddenFromHomePage: true
aliases: ["/categories/news/"]
---

🦞 每日 08:00 自动更新

---

## 🔥 今日热门

### 独立 FDE 在大阪做制造业 AI 落地：3 层方案（LLM 转写老师傅 + RAG + 视觉检测）
来源：V2EX
发布者：zengdan2024
原文：[原文](https://www.v2ex.com/t/1220072)
摘要：帖子发布于 2026-06-13 00:45 BJT（约 8 小时前）。楼主 zengdan2024 分享在大阪关西一家精密零部件中型制造厂（400 人、年营收几十亿日元）做独立 FDE 顾问的真实过程。客户原本只想做「AI 替代老师傅目视质检」，楼主到现场后发现质检的真正难点不是「缺陷检测」而是「老师傅根据 20 年经验做的根因诊断」。最终方案分 3 层：底层用 LLM 把老师傅一边检查一边说的 60 小时录音转写为可检索的隐性知识库；中间层搭 RAG，给新质检员推荐类似案例；上层才是 AI 视觉分类模型，输出「疑似 XX 缺陷 + 置信度 + 参考案例」而非「合格 / 不合格」。**对 AI 副业读者的范本价值**：(1) FDE 路径真实可行——独立顾问 + 制造业 + AI 落地的「三角组合」在日本中型企业有真实需求；(2） 难点不在模型，而在「替客户重新定义需求」，需要文化适配（日本客户要用「肯定-包装-替代」三段式沟通）；(3) 「LLM 转写老法师经验 + RAG 检索 + 视觉检测」是这个细分可复用的 3 层架构。

### ChatVault v0.6.0 发布：local-first AI 对话导出器，已上 Chrome Web Store
来源：Reddit r/SideProject
发布者：SkyAfraid3158
原文：[原文](https://www.reddit.com/r/SideProject/comments/1u4c6s1/title_shipped_chatvault_a_localfirst_exporter_for)
摘要：帖子发布于 2026-06-13 00:18 BJT（约 8 小时前）。ChatVault v0.6.0 由独立开发者 johnivanov04 推出，是一个 100% 客户端运行、零后端、零托管成本的 AI 对话导出器（React + TS + Vite + Tailwind，JSZip 在浏览器内解析 ChatGPT/Claude/Gemini 的 data-export ZIP，Vercel 静态托管月费 $0）。配套 MV3 浏览器扩展已通过 Chrome Web Store 审核，支持一键抓取附件二进制（MAIN-world content script 拦截 fetch + XHR）。差异化点：附件导出（竞品都不支持）、不限免费 PDF（多数 cap 3 / 天）、多 provider、无登录、无埋点。**对 AI 副业/独立开发者**：(1) 「纯 client-side + 零后端 + Vercel $0 托管 + 浏览器扩展」是被反复验证的极低门槛单人副业公式；(2） 抓取附件二进制是技术差异化（其他人不愿意啃 MV3 + MAIN-world 这层坑），证明「硬骨头 + 工具缺口」是独立开发定价权的来源；(3） 开源（GitHub johnivanov04/ChatVault）+ Chrome Web Store 上架 + 评论区 AMA，是 2026 年「软件出海」最轻的样板。

### Hermes：开源 AI Agent 三个月处理 15.8T tokens，OpenRouter 编程/生产力/CLI 三榜 #1
来源：Reddit r/SideProject
发布者：Exact_Pen_8973
原文：[原文](https://www.reddit.com/r/SideProject/comments/1u4c1n9/hermes_the_free_opensource_ai_agent_beating_paid)
摘要：帖子发布于 2026-06-13 00:11 BJT（约 8 小时前）。Hermes 是来自 Nous Research 的开源 AI agent，3 个月内累计处理 15.8 万亿 tokens，并在 OpenRouter 编程/生产力/CLI 三个类别登顶 #1（超过了付费工具）。对单人副业的关键卖点：内置 40+ 工具无需在多个 App 之间来回切；`/goal` 命令让用户只给目标，agent 自己挑模型 + 工具；带工作流记忆。Tradeoff：软件免费但要接 Claude/GPT 付费模型才达到最佳效果，权限放得开意味着安全责任在自己。**对 AI 副业读者**：(1) 「开源 agent + 自接付费模型」是一个被验证的「0 起步 + 边际成本可控」的副业底座——做上层应用不必从 0 写 agent；(2) OpenRouter #1 位置本身就是自然流量入口，单人开发者不用买量也能获客；(3) `/goal` 这种「目标驱动」交互是 2026 副业小工具最被低估的范式。

## 💼 招聘 / 远程机会

### AI 陪伴团队招远程全职：全栈 / 文本训练 / 视频训练 / 数据 / 产品经理（美主体）
来源：V2EX
原文：[原文](https://www.v2ex.com/t/1219661)
摘要：帖子发布于 2026-06-12 19:53 BJT（约 13 小时前）。美国主体的 AI 陪伴团队（情感陪伴、NSFW 伴侣、AI 游戏平台）招 5 个远程全职岗位，结算灵活，可项目制 / 顾问制合作：高级全栈（Java + Vue 3/TS，要求 1 年以上 Claude Code / Cursor 实战）；文本大模型训练专家（基于开源 LLM 做 NSFW 叙事微调，要求有 Hugging Face 模型作品）；视频训练专家（开源视频生成模型做仿真人 / 动漫微调）；AI 数据工程师（NSFW 语料 + 多模态数据集 + 标注平台）；AI 产品经理（陪伴 + 创作者工具链）。同时招推广增长经理、品类运营经理（男女向 / 多语种）。**对 AI 副业读者**：(1) 「美主体 + 远程 + 结算灵活」是 2026 副业最稳定的跨境合同结构之一；(2) Hugging Face 模型作品 / 标注平台搭建经验是当下高溢价副业技能；(3） 同一团队同时开全职 + 项目制 + 顾问制 3 种合作形态，给「想试水但不想全职」的人留了接单窗口。

### 硅谷公司招 AI Infra 工程师（东八区远程 + 客户维护奖金，按 opc 算）
来源：V2EX
原文：[原文](https://www.v2ex.com/t/1219748)
摘要：帖子发布于 2026-06-12 21:44 BJT（约 11 小时前）。硅谷 Quotaflow（admin@quotaflow.ai）业务扩展招东八区工程师，要求：擅长沟通 + 快速学习 + 企业级高可用系统构建 + 维护。**核心硬要求是重度使用 Codex 或 Claude Code 做快速定位 / 重构**——本质上招的是「agentic engineer」。薪资结构 = 底薪 + 客户维护奖金（客户维护越多奖金越多），按 opc（one-person company）模式理解。**对 AI 副业读者**：(1) 「AI 编程重度用户」已从加分项变成 2026 年海外招工的硬门槛，纯 prompt 能力不够，要会 agent 重构 + 系统设计；(2） 硅谷 SaaS 团队用「底薪 + 客户奖金 + 远程」的结构给「一人多客户」型副业 / 半独立留了合法化通道——比纯 freelance 收入更稳；(3） 投 admin@quotaflow.ai 时如果简历里直接写明「Codex / Claude Code 重构案例 + 高可用服务」比写「会用 ChatGPT」过简历概率高一个量级。

### BioAI 公司招 AI 应用工程师（LLM + Agent），上海 35-70 万/年
来源：V2EX
原文：[原文](https://www.v2ex.com/t/1219617)
摘要：帖子发布于 2026-06-12 22:17 BJT（约 10 小时前）。上海生物医药细分领域 AI 应用公司（联创多为外资背景，已交付给国内外 top 生物医药企业的 AI 数字人 + AI Agent 订单）招 AI 应用工程师，薪资 35-70 万/年。岗位职责：基于 LLM 的 AI 产品研发 / AI Agent 工作流（任务规划、工具调用、知识检索）/ RAG + 企业知识库 + 向量检索 / AI 后端 API + 全栈。投递邮箱 joy_ss@foxmail.com。**对 AI 副业读者**：(1) 「垂直行业（生物医药 / 金融 / 制造）+ AI 应用」是 2026 年招工量最大的「传统行业 + LLM 落地」交叉岗位——从自由职业接单到拿正式 offer 的转化路径最短；(2) 「RAG + Agent + 向量库」是当下副业市场最通用的「3 件套」技能栈，学会后能接 5+ 行业；(3） 外资文化团队通常对接单、远程、灵活结算更开放，可作为副业 → 长期合同的入口。

## 🚀 工具 / 平台

### llmjob.com：开源「选 LLM / 选 GPU」匹配工具，VRAM 一眼能跑哪些模型
来源：Reddit r/LocalLLaMA
发布者：super3
原文：[原文](https://www.reddit.com/r/LocalLLaMA/comments/1u47kmx/built_a_tool_that_tells_you_exactly_which_llms)
摘要：帖子发布于 2026-06-12 21:03 BJT（约 12 小时前）。r/LocalLLaMA 用户 super3 自建 llmjob.com/rankings.html，输入 GPU 信息就能看到哪些开源 LLM 实际能跑，按质量 + 上下文长度排序，解决「VRAM 够不够、上下文够不够」两个最常被问的问题。**对 AI 副业读者**：(1） 端侧 AI 副业（本地部署代理 / 私人 RAG / 本地图像生成）最常被新手卡在「我这块显卡能跑啥」——这种小工具的搜索流量在 Reddit / X / 公众号长尾都很大；(2） 单 HTML 静态页 + 真实数据 + 简洁交互的「边角工具」是 2026 年最容易被 AI 编程重度用户复制并商业化的形态（加 SEO + 联盟链接到 GPU 云厂商就能直接收钱）；(3) 「超级细分 + 真实痛点 + 静态站」是个人副业最容易跑通冷启动的 3 件套。

## 💰 赚钱 / 合伙机会

### [全职 / 合伙人] 项目寻找 Go&Vue3 全栈合伙人：50/50 股份 + 已有 5 个月 7 位数营收
来源：V2EX
发布者：aicodingsh
原文：[原文](https://www.v2ex.com/t/1219480)
摘要：帖子发布于 2026-06-12 22:26 BJT（约 10 小时前）。aicodingsh 自营 SaaS 项目（产品弱、急需技术合伙人重构），验证过市场和盈利（5 个月非正式推广 7 位数营收），提供 50/50 股份、3 年行业经验总结、完整旗舰产品设计方案。硬性技术栈：Golang（Gin / Go-Zero）+ PostgreSQL + Redis + WebSocket + REST + JWT + 权限/防爬 + Docker + Linux + Nginx + CI/CD；前端 Vue3 + TS + Vite + WebSocket + Pinia + Element Plus；要求「熟练使用 AI 减少开发周期」。**加分项**：SaaS / 私有化部署 / IM / 低代码 / 可视化编辑器 / Tauri 经验。**对 AI 副业读者**：(1) 「产品 + 营销 + 已有营收 + 寻找技术合伙人」是 2026 副业圈最稀缺的「被动 offer」——技术合伙人不必自己找方向；(2） 帖子明确写「对实践论 / 矛盾论有较深理解」是加分项，说明团队文化偏「产品主义 + 工程哲学派」，匹配前需要价值观对齐；(3） 接这种 50/50 合伙前要重点 verify 营收流水 + 老客户名单 + 现有产品 Demo 完整度（5 个月 7 位数是相对可靠的验证数据），验证不到位风险远大于全职打工。

### 用 AI 写了个中医自诊网站，纯爱发电「求喷」
来源：V2EX
原文：[原文](https://www.v2ex.com/t/1219848)
摘要：帖子发布于 2026-06-13 08:37 BJT（约 9 分钟前）。楼主「失眠几年看西医只会开安眠药」转而自学中医后，独立开发了中医自诊网站 xuanhu.cn，主打「不争中西医孰优孰劣，谁有效用谁」的个人副业项目。**对 AI 副业读者**：(1) 「个人健康痛点 + 自学领域知识 + AI 工具做产品 + 自建站」是 2026 副业最被反复验证的「小而美」公式——产品不需要融资、用户不需要推广、SEO 自然流量即可；(2) 「求喷」式的开放交流是 V2EX / X / 少数派等社区获取早期用户反馈最快的方式，比小范围私域传播好 5–10 倍；(3） 纯爱发电起步但保留升级路径（v1 个人工具 → v2 订阅服务 → v3 行业 API）是单兵副业最稳的 3 阶段路径。

---

## 📚 学习 / 取舍

### 「一个人写了大半年 Android App」式独立开发范式：付费买断 + 多平台 + 零订阅
来源：V2EX
发布者：putilaoha（Meows 半年连载 #5）
原文：[原文](https://www.v2ex.com/t/1219146)
摘要: 6-09 09:54 BJT 发布的 Meows 半年连载帖讨论范式（24h 外但有持续讨论价值）。Meows（p/putilaoha 做的 SSH 服务器监控 App，填 IP 就能用、服务器端零安装），半年连载新增 Docker 容器管理（启动/停止/重启/实时日志，全程走 SSH 协议不破零安装原则）+ 历史曲线钻取进程详情 + 终端文字渲染重写。商业模式：付费买断 $4.99，无订阅无广告无埋点；已上架 Google Play 11 个地区（日本/美国/新加坡/韩国/香港/台湾/英国/加拿大/澳门/马来西亚/冰岛），Android 14+，中英日韩 4 语言。**对 AI 副业读者**：(1） 评论区多人求 iOS 版，「一个人做小工具 + 多平台买断 + 零订阅」是被反复验证的独立开发范式；(2） 谷歌 Play 出海被「12 人测试者」卡住的真实痛点也暴露出来——出海类副业读者可关注规避策略；(3） 把 SSH 这类「工程师基础工具」做精做透是 AI 副业里被低估的细分（Copilot 帮写代码后，配套 SSH / 监控 / 部署工具需求反而增长）。

## 📊 关键平台动态

| 工具 / 平台 | 动态 | 副业相关性 |
| --- | --- | --- |
| ChatVault (v0.6.0) | 上 Chrome Web Store + GitHub 开源 + 纯 client-side | 单人副业「零后端 + 浏览器扩展」模板 |
| Hermes Agent (Nous Research) | OpenRouter 编程 / 生产力 / CLI 三榜 #1 | 0 起步副业的 agent 底座，自接付费模型 |
| llmjob.com | 静态 HTML 选 LLM / 选 GPU 工具 | 端侧 AI 副业入口工具，SEO 长尾流量大 |
| 小红书 RED Skill | 6-09 已开放内测，预计 7 月全量 | 2026 最大新分发渠道（AI 副业新蓝海） |
| V2EX 招聘 / 项目区 | 24h 内 10+ AI / 远程 / 创业帖更新 | 国内 AI 副业最高密度社区入口 |

---

🦞 每日 08:00 自动更新

**数据来源**：V2EX（jobs / 创业区）、Reddit r/SideProject、Reddit r/LocalLLaMA

**🔗 原文链接：**
- ✅ https://www.v2ex.com/t/1220072 - 独立 FDE 大阪制造业 AI 落地（zengdan2024，2026-06-13 00:45 BJT）
- ✅ https://www.reddit.com/r/SideProject/comments/1u4c6s1/title_shipped_chatvault_a_localfirst_exporter_for - ChatVault v0.6.0（SkyAfraid3158，2026-06-13 00:18 BJT）
- ✅ https://www.reddit.com/r/SideProject/comments/1u4c1n9/hermes_the_free_opensource_ai_agent_beating_paid - Hermes（Exact_Pen_8973，2026-06-13 00:11 BJT）
- ✅ https://www.v2ex.com/t/1219661 - AI 陪伴产品远程岗位（2026-06-12 19:53 BJT）
- ✅ https://www.v2ex.com/t/1219748 - 硅谷 AI Infra 工程师（2026-06-12 21:44 BJT）
- ✅ https://www.v2ex.com/t/1219617 - BioAI AI 应用工程师（2026-06-12 22:17 BJT）
- ✅ https://www.reddit.com/r/LocalLLaMA/comments/1u47kmx/built_a_tool_that_tells_you_exactly_which_llms - llmjob（super3，2026-06-12 21:03 BJT）
- ✅ https://www.v2ex.com/t/1219480 - 寻找 Go&Vue3 合伙人（aicodingsh，2026-06-12 22:26 BJT）
- ✅ https://www.v2ex.com/t/1219848 - AI 写中医自诊网站（2026-06-13 08:37 BJT）
