---
title: "AI新闻早报 2026-08-14"
date: 2026-08-14T06:25:00+08:00
slug: ai-morning-news-2026-08-14
description: "2026年8月14日 AI 新闻早报，汇总过去 24 小时内 DeepSeek Harness 发布、Gemini 3.7 Flash 上线、Grok 4.6 反超、Cerebras 加速 GPT-5.6 Sol 等关键动态。"
draft: false
categories: ["行业快讯"]
tags: ["DeepSeek", "Gemini", "Grok", "Cerebras", "AI模型"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 🚀 产品发布

### DeepSeek Harness 开发者预览版发布，开源 Agent 框架亮相
来源: 量子位 / Hacker News
原文: [原文](https://deepseek.com/harness/en/)
摘要: DeepSeek 发布 Harness 开发者预览版，定位为开源 Agent 框架，将模型、工具、技能、会话、沙箱、存储等能力全部插件化，支持开发者自由组合与替换。框架基于 Rust 编写单体核心，已内置 100 多个官方插件，并预留 Plugin Store。源码同步开源至 GitHub，可通过 `npx @deepseek-ai/dsh web` 快速启动。在 Hacker News 上获 517 点热度、231 条讨论。

### Google 发布 Gemini 3.7 Flash：面向编码与 Agent 的最强工作模型
来源: Google DeepMind / Hacker News
原文: [原文](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-3-7-flash/)
摘要: Google 推出 Gemini 3.7 Flash，距 3.6 Flash 发布仅三周，定位为"最智能的工作模型"，重点提升软件工程、知识工作和 Web 开发能力。 introductory 价格为原 3.6 Flash 每百万 token 成本的一半。在 Hacker News 上获 506 点热度、308 条讨论，开发者社区关注度极高。

### Grok 4.6 发布：跑分反超 GPT-5.6 Sol 和 Fable 5 Max
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/472067.html)
摘要: xAI 发布 Grok 4.6，在 GDPVal-AA v2 基准测试中拿到全场最高分 1753，反超 GPT-5.6 Sol 和 Fable 5 Max。定价为每百万 token 输入 2 美元、输出 6 美元，显著低于竞品。新模型已接入 Grok Build、Cursor、Grok Bot 和 API，Cursor 首周提供双倍用量。

### Mistral 发布 OCR 4.1：支持段落级边界框提取
来源: Hacker News / Mistral
原文: [原文](https://docs.mistral.ai/models/ocr-4-1)
摘要: Mistral 推出 OCR 4.1 服务，新增原生段落级边界框提取、结构化块标签和块级置信度分数功能，进一步强化 Document AI 技术栈。定价为每 1000 页 3.5 欧元。在 Hacker News 上获 213 点热度。

---

## 🔬 技术进展

### Cerebras 联合 OpenAI 推出 GPT-5.6 Sol Ultrafast 模式
来源: Cerebras / Hacker News
原文: [原文](https://www.cerebras.ai/blog/accelerating-gpt-5-6-sol-ultrafast-with-openai)
摘要: Cerebras 与 OpenAI 合作推出 Ultrafast 模式，为 GPT-5.6 Sol 提供每秒最高 750 token 的输出速度，比 Fable 5 快 11 倍、比 Opus 4.8 Fast 模式快 5 倍，且不牺牲质量。该服务首先在 OpenAI API 上线，初期面向部分客户开放。在 Hacker News 上获 332 点热度。

### Claude 突破 668 阶哈达玛矩阵，AI 持续清空数学待解列表
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/472016.html)
摘要: Anthropic 研究员、数学家 Levent Alpöge 与两名人类合作者借助 Claude，成功找到 668 阶哈达玛矩阵的解决方案。此前 Anthropic 团队还用 Fable 5 推翻了雅可比猜想。AI 在数学研究中的角色正从辅助工具变为核心生产力。

### Ilya 创办的 SSI 首个模型曝光：基于 TTT 的推理引擎
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/471701.html)
摘要: 前 OpenAI 首席科学家 Ilya 创办的 SSI（Safe Superintelligence）曝光首个模型方向：探索基于 TTT（Test-Time Training，测试时训练）的小型推理引擎。SSI 成立两年多以来几乎不发布产品和模型，此次曝光显示其正在持续学习方向展开研究。

---

## 💰 融资财报

### Acrab 完成 1.3 亿美元 B 轮融资，端侧 AI 芯片累计融资超 4.8 亿美元
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/472059.html)
摘要: 总部位于新加坡的 AI 计算基础设施公司 Acrab 完成 1.3 亿美元 B 轮融资，Vertex Growth 等机构参与。公司成立不到三年，首颗 AI 芯片已进入量产阶段，累计融资超 4.8 亿美元。新资金将用于扩大产能、拓展技术生态和研发下一代 AI 计算平台。

---

## 🛠️ 开源工具

### Bullet (YC S26)：主打速度的编码 Agent，SWE-bench 达 95.8%
来源: Hacker News
原文: [原文](https://www.codewithbullet.com)
摘要: YC S26 孵化的 Bullet 定位为更快的编码 Agent，在 SWE-bench Verified 上以单次尝试解决 479/500（95.8%）问题，平均耗时 119 秒，比 mini-SWE-agent + Fable/Sol 快 35%-67%。核心优化包括模型路由、定向代码搜索、激进上下文管理和并行化独立任务。在 Hacker News Launch专区获 71 点热度。

---

🦞 每日08:00自动更新

**数据来源**：量子位、Google DeepMind、Cerebras、Mistral、Hacker News
