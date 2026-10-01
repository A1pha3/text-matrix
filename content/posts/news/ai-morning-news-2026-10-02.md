---
title: "AI新闻早报 2026-10-02"
date: 2026-10-02T06:30:00+08:00
slug: ai-morning-news-2026-10-02
description: "2026年10月2日 AI 新闻早报，汇总过去 24 小时内 Gemini 4 发布、何恺明团队 ARC 新研究、OpenAI DevDay、Cloudflare 开源决策模型等关键动态。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "Gemini", "开源模型", "决策模型"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 🚀 产品发布

### 谷歌突然发布 Gemini 4：RSI 加持，同步推出安全智能体 Argon
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/10/499663.html)
摘要: 谷歌正式发布 Gemini 4，主打递归自我改进（RSI）能力，定价约为 Astra 的一半；同场推出安全智能体 Argon，可自主发现并修补 20 多种语言的关键软件漏洞，在 Wiz 黑箱渗透测试中实现了无源代码的实时攻击面分析。Argon 首批接入谷歌 Fairwind 计划，仅面向审核通过的网络安全防御方开放。报道同时引述彭博消息，部分谷歌内部员工对 Gemini 4 的实际编程表现存疑，谷歌回应称相关说法并不准确。

### OpenAI DevDay 2026：GPT-6.1 Sol、Pro 500 套餐与 ChatGPT Space
来源: Ben's Bites
原文: [原文](https://www.bensbites.com/p/openai-devday-2026)
摘要: OpenAI 在 DevDay 上发布 GPT-6.1 Sol，评价为相较 GPT-6 Sol 的实质性升级；同时推出 Pro 500 套餐，将各档用量统一折算为基础套餐的 5x/10x/25x 倍率，并正式上线 Sign in with ChatGPT，允许第三方应用调用用户的 ChatGPT 用量。面向协作场景的 ChatGPT Space 提供类 Notion 文档工作区，可分享给智能体与团队；GPT-6 Astra 的 Ultrafast 模式可提速 8 倍，但消耗 6 倍用量。

### Cloudflare 开源决策模型 Clef，并推出 RL 微调平台
来源: Cloudflare Blog
原文: [原文](https://blog.cloudflare.com/clef-decision-models/)
摘要: Cloudflare 发布自研决策模型 Clef 与 Clef-flash，托管于 Workers AI，在 Jev Decision Index 评测中暂列第一，且与 Jev API 完全兼容。决策模型以低成本、快速、一致的方式输出带概率的结构化决策结果，填补了非确定性 LLM 与传统分类器之间的空白。两款模型以 Apache 2.0 许可在 HuggingFace 开源，配套的强化学习微调产品允许客户针对自身场景调优，Cloudflare 威胁情报团队已在内测中使用。

## 🔬 技术进展

### 何恺明团队新作：ImageNet 预训练打通 ARC 视觉路线的 scaling 瓶颈
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/10/499812.html)
摘要: MIT CSAIL 何恺明组的 NAT-ARC 直接复用 ImageNet 上 MAE 预训练的 encoder 权重初始化视觉编码器，再在 ARC 训练集上离线训练并对每题做测试时 LoRA 微调。集成三个不同预训练策略的模型后以约 2B 总参数取得 ARC-1 上 70.2% 的 pass@2 成绩，接近用 8B 语言模型的专用系统 The ARChitects（71.6%）。论文还发现 ImageNet 预训练使 scaling 曲线转正——未预训练时模型越大反而越差，预训练后三个尺度一路向上。

### Ai2 发布 Olmo-core 3：面向大型 MoE 的开源可扩展训练基础设施
来源: HuggingFace
原文: [原文](https://huggingface.co/blog/allenai/olmocore3)
摘要: Allen AI 开源 Olmo-core 3，专为大型混合专家（MoE）模型设计的训练框架。基准测试中，专家池从 8 扩到 128、每 token 激活专家数保持 4 个，总参数从 4.6B 增至 47B 的同时训练吞吐下降不到 5%，该基础设施已在超过一万亿总参数规模上完成基准验证。框架将训练栈从全分片数据并行（FSDP）转向针对 MoE 路由通信优化的新系统，目标是为学术研究者和中小实验室提供可负担的大模型训练路径。

## 💼 商业应用

### 巴克莱银行扩大与 Anthropic 合作，规模化部署 Claude
来源: Anthropic
原文: [原文](https://www.anthropic.com/news/barclays-scales-claude)
摘要: 巴克莱宣布扩大与 Anthropic 的战略合作，在企业级安全与治理框架内集成 Claude，覆盖客户服务、软件工程与网络安全等场景。其内部 Colleague Knowledge Assistant 自 2025 年上线以来已有超过 1.6 万名员工使用，累计处理逾百万次检索，支撑面向 2000 万英国零售客户的服务的提速。巴克莱联席首席运营官 Craig Bright 表示，AI 正成为嵌入开发、测试与安全运营的智能体能力。

---

🦞 每日08:00自动更新

**数据来源**：量子位、Ben's Bites、Cloudflare Blog、HuggingFace、Anthropic
