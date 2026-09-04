---
title: "AI 新闻早报（2026-09-05）"
date: 2026-09-05T06:40:00+08:00
slug: ai-morning-news-2026-09-05
description: "英伟达 129 亿美元收购 Hugging Face，Stripe 约 75 亿美元买下 OpenRouter；Anthropic 发布费马大定理首个完整机器可验证证明；DeepMind 推出 WeatherNext 3 气象模型。"
draft: false
categories: ["行业快讯"]
tags: ["英伟达", "Hugging Face", "OpenRouter", "Claude", "世界模型"]
hiddenFromHomePage: true
---

## 💰 融资并购

### 英伟达 129.3 亿美元收购 Hugging Face，创其史上最大整体收购

黄仁勋在英伟达官方博客宣布，已与 Hugging Face 签署最终收购协议，交易总额 129.303 亿美元，为英伟达史上最大整体收购（上一纪录是 2020 年 69 亿美元收购 Mellanox）。戏剧性在于：2025 年底 Hugging Face 曾拒绝英伟达 5 亿美元入股以保持平台中立，如今整体出售。CEO Clément Delangue 解释称开源 AI 到达拐点，扩张至 1 亿开发者需要更多算力与基建。开源社区担忧：芯片巨头接管全球最大开源 AI 分发入口后，"算力中立"如何保障。[原文](https://www.36kr.com/p/3968940073595144)

### Stripe 约 75 亿美元收购模型路由平台 OpenRouter

Stripe 收购 AI 创业公司 OpenRouter，成交价约 75 亿美元，距其上轮 13 亿美元估值仅三个月，翻五倍多。该公司 82 人，不训练任何模型，只做统一 API 聚合：接入 80 多家供应商、400 多个模型，服务约 1000 万开发者，日 token 调用超 10 万亿。其商业模式是充值手续费而非模型加价，模型厂越卷，"替用户选模型"越稀缺。[原文](https://www.36kr.com/p/3968960676294920)

## 🔬 技术进展

### Anthropic 发布费马大定理首个完整机器可验证证明

Anthropic 于 9 月 4 日公布费马大定理（Fermat's Last Theorem）的首个完整计算机检验证明：Claude 在 11 天内高度自主地用 Lean 语言写出该证明。1995 年 Wiles 的原始证明长达 129 页，验证耗时数月；形式化后可由计算机自动检验，同期开源代码库也已放出。这被视为 AI 辅助研究数学的标志性进展。[原文](https://www.anthropic.com/research/formalizing-fermats-last-theorem)

### DeepMind 推出 WeatherNext 3：迄今最先进的全球气象 AI 模型

Google DeepMind 发布 WeatherNext 3，称其为目前最先进、最准确的全球天气 AI 模型，延续了其在气旋预报等方向上的突破路线，进一步压缩传统数值预报与 AI 预报的差距。[原文](https://deepmind.google/blog/introducing-weathernext-3-our-most-advanced-and-accurate-global-weather-ai-model/)

### 星尘智能发布 SmoothRL：异步推理下的在线强化学习框架

星尘智能（Astribot）基座模型团队发布可异步执行的在线强化学习框架 SmoothRL，解决机器人异步部署中"模型计划"与"实际执行"动作不对齐导致 RL 学错账的问题，并首次在真实高动态投掷任务中验证——任务要求连续加速、精确释放、不能停顿。[原文](https://www.qbitai.com/2026/09/484437.html)

### 李飞飞 World Labs 发 Atlas，国内影溯同路线模型已开源半年

9 月 2 日李飞飞创办的 World Labs 发布全球首个多模态世界模型 Atlas，将文字、图像、视频与 3D 信息放进统一空间上下文。量子位指出，国内团队影溯今年 3 月已开源类似能力的 InSpatio-World，且其 InSpatio-Curious 以 66.11 分位列 WorldArena 2.0 榜首。世界模型正从"生成合理视频"走向"围绕持续时空状态生成多视角观测"。[原文](https://www.qbitai.com/2026/09/484163.html)

### 九问社区 ScienceDiscovery 用树搜索实现科研代码自迭代

openJiuwen 社区的 ScienceDiscovery 把科研代码的试错交给树搜索：每版产物是树节点，选择、改写、沙箱评分、记账循环推进，全程无人干预。在 38 道半无穷区间振荡积分上，2 小时 236 个版本将得分从 -3.40 推到 -0.0007，产出的 247 行通用求解器在未参与打分的题目上同样有效；高斯超几何函数求值任务也超过 scipy 数十年基线。[原文](https://www.qbitai.com/2026/09/484293.html)

## 💼 商业应用

### 千问办公上线首月用户破 3000 万，企业用户占比过半

阿里企业级 Agent 产品千问办公上线满月：用户超 3000 万，企业用户占比过半，一个月完成 120 个版本迭代并推出国际版。其开源上下文设施 MyContext 数周获超 3000 Star；配合 Qwen3.8-Flash 专属版模型，单任务生成速度提升约 100%、Token 消耗平均减少 75%。长安汽车、汇付天下、老乡鸡等企业已接入。[原文](https://www.qbitai.com/2026/09/484155.html)

## 📰 行业动态

### 德银报告：美国 AI 资本豪赌押上美元命运

德意志银行 9 月 3 日报告指出，美国企业今年 AI 资本开支预计约 8000 亿美元，AI 风险投资募资超 4000 亿美元，最大两家 AI 实验室合计融资近 2170 亿美元、估值均逼近 1 万亿；超大规模科技企业投资级债券融资约为 2020-2024 年均的十倍。德银警告美元正从避险锚蜕变为高风险 AI 押注，商业模式一旦证伪资本将快速出逃。[原文](https://www.36kr.com/p/3968887667077384)

### 纽约市公立学校对 AI"急刹车"：8 年级以下全面禁用一年

纽约市长宣布自 2026-2027 学年起，全市幼儿园至 8 年级约 60 万名学生（占公校人数三分之二）课堂全面禁用生成式 AI 一年，约 40 款含 AI 功能的教育 App 将被删除或调整；高中生改为素养教育加有限试点。这是美国规模最大、限制最严的学生 AI 使用政策之一。[原文](https://www.36kr.com/p/3968940471857664)

---

## 数据来源

- 量子位
- 36氪 AI 频道
- [Anthropic Research](https://www.anthropic.com/research)
- [Google DeepMind Blog](https://deepmind.google/blog/)
