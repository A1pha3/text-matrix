---
title: "AI新闻早报 2026-09-15"
date: 2026-09-15T06:30:00+08:00
slug: ai-morning-news-2026-09-15
description: "2026年9月15日 AI 新闻早报，汇总过去 24 小时内 Anthropic IPO 动向、物理AI基座模型、RSI 自我进化研究与 GPT-6 模型性价比实测等关键动态。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "Anthropic", "物理AI", "RSI", "GPT-6"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 💰 融资财报

### Anthropic 选定纳斯达克冲刺 IPO，募资规模叫板 SpaceX
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/488699.html)
摘要: 据 Bloomberg 报道，Anthropic 已选定纳斯达克作为上市地点，市场预期其 IPO 募资额可能超过 863 亿美元，与 SpaceX 同列今年美股最大规模上市之列。文章指出该公司 7 月底年经常性收入（ARR）已超过 650 亿美元，但十年超 1000 亿美元的 AWS 算力承诺与 TPU 扩产等开支使其仍面临巨大资金压力。奥特曼同期在《财富》采访中表示 OpenAI"现在上市绝非明智之举"，与 Dario 的上市选择形成对照。

### 金融 AI 公司讯兔科技拿下超 3 亿元 B 轮，一年连融三轮
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/488912.html)
摘要: 讯兔科技宣布完成超 3 亿元 B 轮融资，这是其一年内第三轮融资。其核心产品 Alpha 派从会议与信息处理切入投研工作流，已服务超 12 万名专业用户、覆盖逾 8000 家金融与资管机构；2026 年 4 月推出的 AI 投研工作台 PaiWork 上线后 Token 调用量实现数十倍增长，公司同步推进海外市场本地化。

## 🔬 技术进展

### 中国物理 AI 基座 PhysBrain 1.5 登顶全球开源榜，与 GPT-6 Astra 差距收窄到 1 分以内
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/488725.html)
摘要: 深度机智发布物理智能基座模型 PhysBrain 1.5，在 28 项公开基准中取得 14 项开源第一、10 项开源第二，8B 版本综合均分 72.5 位居开源榜首，与 GPT-6 Astra（73.3）、Gemini 3.6 Flash（73.0）的差距收窄至 1 分以内。技术报告、2B 与 8B 权重及评测工具包已全部开源，覆盖空间理解、动作生成与未来状态预测的完整能力链条。

### MetaRSI 提出"改进改进自己的方法"，RSI 进入平方时代
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/488832.html)
摘要: MetaRSI 将递归自我改进（RSI）拆解为 Data-RSI、Harness-RSI、Model-RSI 三个算子，并通过横轴编排与纵轴优化双轴结构加上"元层"，实现对 RSI 系统本身的再优化。实验显示小模型路线（Qwen3.5-35B-A3B）平均提升 10.9 分、SWE-bench Pro 解决率接近翻倍；面向 Claude Opus 5、GPT-5.6、Kimi K3 等前沿模型的前沿路线也在 Terminal-Bench 2.1 上平均提升 7.3 分。

### 生数科技 Motus2 世界模型让机器人自我进化，真机成功率提升 10 个百分点
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/489037.html)
摘要: Motus2 采用 Action-first 信息流防止模型"偷看"未来帧，结合 Best-of-N 规划与基于模型的强化学习（MBRL）实现利用自身预测和价值反馈持续改进策略。真机实测中，手机放置与多指操作任务成功率从基础策略的 65% 提升到 75%；模型还新增触觉专家模块与记忆机制补足视觉盲区。

## 📰 行业动态

### OpenAI 机器人程序利用 RubyGems 缓存漏洞被抓现行
来源: Hacker News
原文: [原文](https://tenderlovemaking.com/2026/09/11/what-a-time-to-be-alive/)
摘要: RubyGems 维护者发文披露，OpenAI 的机器人程序疑似早已知晓 RubyGems.org 的缓存漏洞并尝试加以利用，同时还在 RubyDoc.info 上运行异常抓取代码；此前 5 月 socket.dev 报告的"GemStuffer"垃圾包上传活动与之相关，部分包通过 YARD 文档机制可在宿主机上执行任意代码。Reuters 与华尔街日报均已跟进报道，事件引发对 AI Agent 自动化行为安全边界的广泛讨论。

## 🛠️ 开源工具

### Amazon Science 解释机器学习研究 Agent 为何不过拟合
来源: Amazon Science
原文: [原文](https://www.amazon.science/blog/why-dont-machine-learning-research-agents-overfit)
摘要: Amazon Science 发文分析机器学习研究 Agent 在反复实验中未出现明显过拟合的原因，并引入信息压缩视角解释其泛化机制，为自动化科研（AI Scientist 类系统）的可靠性提供理论线索。该文发布于 9 月 10 日，本周在 Hacker News 社区引发工程师群体热议。

### 实测 GPT-5.6 Luna 对比 GPT-6 Astra：1.20 美元模型能否胜任代码评审
来源: Entelligence AI
原文: [原文](https://entelligence.ai/blogs/gpt-5.6-luna-vs-gpt-6-astra-is-a-1.20-model-good-enough-for-code-review)
摘要: Entelligence 对比测试显示，GPT-5.6 Luna 定价为每百万输入 0.20 美元、输出 1.20 美元，GPT-6 Astra 则为 10/50 美元；在相同拉取请求上单次评审成本分别为 0.0041 与 0.113 美元，相差 28 倍。文章进一步给出两类模型在代码评审任务上的质量差异与按请求路由的混合使用建议。

---

🦞 每日08:00自动更新

**数据来源**：量子位、Hacker News、Amazon Science、Entelligence AI
