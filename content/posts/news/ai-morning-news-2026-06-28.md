---
title: "AI新闻早报 2026-06-28"
date: 2026-06-28T07:24:20+08:00
slug: ai-morning-news-2026-06-28
description: "2026年6月28日 AI 新闻早报，精选过去 24 小时内 OpenAI 发布 GPT-5.6 三档模型、DeepSeek 开源 DSpark 推理加速框架、亚洲 AI 初创推 Mythos 类模型对抗出口禁令、微软年度 AI 职场报告等核心动态。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "GPT-5.6", "DeepSeek", "开源框架", "AI职场"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 🚀 产品发布

### OpenAI 一口气端出 GPT-5.6 三档模型，旗舰版对标 Claude Mythos 5
来源: 36kr
原文: [原文](https://www.36kr.com/p/3870740141135108)
摘要: OpenAI 在 6 月 27 日推出 GPT-5.6 有限预览版，三款型号分工明确：旗舰 Sol（太阳）主打复杂推理与代码，输入 5 美元/百万 token、输出 30 美元，与 GPT-5.5 标准版同价；Terra（地球）面向日常工作、价格约为 Sol 的一半；Luna（月亮）则走轻量高速路线，价格只有 Sol 的五分之一。基准测试显示 Sol 在 Terminal-Bench 2.1 编程任务上以 ultra 模式比 Claude Fable 5 高 7.6 个百分点，在网络安全 ExploitBench 上仅用约三分之一输出 token 即可逼近 Mythos Preview 的水平。受美国政府审查影响，目前仅向少数受信任合作伙伴开放。

## 🛠️ 开源工具

### DeepSeek 开源 DSpark 推测解码框架，单用户生成速度最高提升 85%
来源: 36kr
原文: [原文](https://www.36kr.com/p/3871187114448133)
摘要: DeepSeek 在 6 月 27 日开源推测解码框架 DSpark 与配套训练框架 DeepSpec，并发布 DeepSeek-V4-Pro-DSpark 与 DeepSeek-V4-Flash-DSpark 两个推理加速版本。该工作由创始人梁文锋署名、联合北京大学完成，对应论文同步公开。技术核心是半自回归生成与置信度调度验证：用轻量草稿模型并行生成候选 token，再由目标模型批量校验，对极可能被驳回的尾部 token 提前剪枝。在与生产基线 MTP-1 对比中，DSpark 在保持整体吞吐不变的前提下，把单用户生成速度提升 60%-85%，并避免了高并发下的吞吐率大幅滑坡。

### BrowserBC：把人类一次网页操作蒸馏成所有 Agent 都能复用的技能卡
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/06/439393.html)
摘要: Einsa AI 旗下 Navers Lab 开源 BrowserBC，提出录制→转写 Skill→交付执行的三步范式。用户只需在浏览器里完成一次任务，模型会把全过程（含页面观察、操作、反馈与终态）转写成一份讲清"该做什么、怎么算做完"的自然语言技能卡，再交给任意一个更小的模型在真实页面上自主落地。文章指出，技能来源与执行者可以彻底分离，这一思路把 Agent 从"每次从零摸索"推进到"做一次复用很多次"。

## 🔬 技术进展

### 杭州团队 VLX 把 CVPR 2026 多模态热点搬进端侧
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/06/439236.html)
摘要: Om AI 在 CVPR 2026 落幕后第三天连发 VLX 三款模型：VLX-Flow 做实时流式感知，让视频像水流一样持续喂入；VLX-Seek 负责精准定位，从"看见"走向"看清"；VLX-Go 衔接行动决策。该团队去年凭 VLM-R1（全球首个将 DeepSeek R1 强化学习范式引入 VLM 的开源项目）斩获 6000+ GitHub Star，本次原生端侧设计让 VLX 能跑进手机、无人机与机器人，正面回应 CVPR 2026 现场 VLM 论文占比从 4.9% 翻倍到 10.6% 的趋势。

## 💡 开发实践

### Karpathy 流出的 CLAUDE.md 让 Claude "不再和你对着干"
来源: 36kr
原文: [原文](https://www.36kr.com/p/3870932227724547)
摘要: 36kr 6 月 27 日披露的一份据称为 Andrej Karpathy 本人使用的 CLAUDE.md 文件已在开发者社区流传。该文件定位为"不是建议，是规则"——把大模型写代码时反复犯的几类错误写死成工程纪律：写之前先读现有代码、禁止用未读的代码下结论、失败时绝不留半成品、删除死代码优先于注释保留、严格遵循既有 API 路由模式。文件全文链接已随报道公开，对使用 Claude Code 等 AI 编程助手的开发者具有直接参考价值。

## 📊 行业报告

### 微软年度 AI 职场报告：员工准备好了，组织还没跟上
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/06/439032.html)
摘要: 微软《2026 Work Trend Index》覆盖全球 10 个市场、20000 名 AI 用户及数万亿条匿名化 Microsoft 365 生产力信号，提出"转型悖论"：58% 的 AI 用户表示已能产出一年前无法完成的任务，该比例在中国高达 72%；但只有 26% 的员工认为领导层对 AI 的认知与自己一致。报告量化指出，驱动 AI 价值的因素中组织环境占 67%、个人心态行为仅占 32%，前者是后者的整整两倍，将瓶颈指向企业流程与考核框架，而非模型能力本身。

## 🌏 全球动态

### 亚洲 AI 初创连发 Mythos 类模型，趁 Anthropic 出口禁令窗口抢市场
来源: TechCrunch（HackerNews 转载）
原文: [原文](https://techcrunch.com/2026/06/27/asian-ai-startups-launch-mythos-like-models-as-anthropics-export-ban-drags-on/)
摘要: TechCrunch 6 月 27 日报道，在 Anthropic Mythos 5 与 Fable 5 因美国出口禁令被全球下架后，亚洲厂商加速推出对标产品：中国网络安全公司 360 推出 Tulongfeng，声称可与 Mythos 正面对抗；东京初创 Sakana AI 同期发布 Fugu（取自日语"河豚"），定位前沿大模型。文章指出，禁令的真空期正在被本地玩家迅速填充，区域 AI 主权议题从政策讨论转入实际产品落地阶段。

### 第一批"一人公司"长什么样：人指挥一群 Agent
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/06/439237.html)
摘要: 量子位走访多位 One Person Company（OPC）创业者，记录他们如何把"一个人加一群 Agent"做成可持续生意。代表案例超级峰一个人维护 MotiClaw，两周发布 20 多个公开版本、累计 40-50 个小版本，遇到用户现场报错就当场改版。报道勾勒出 AI 时代最常见的小型组织形态：人站在最上层指挥多个 Agent，分别承担开发、内容与运营，自己负责提问、分配与验收，工作流与传统单人创业有本质差异。

---

🦞 每日08:00自动更新

**数据来源**：36kr、量子位、TechCrunch（HackerNews 转载）