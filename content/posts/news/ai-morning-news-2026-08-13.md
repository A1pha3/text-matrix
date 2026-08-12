---
title: "AI新闻早报 2026-08-13"
date: 2026-08-13T06:25:00+08:00
slug: ai-morning-news-2026-08-13
description: "2026年8月13日 AI 新闻早报，精选过去 24 小时内 Grok 4.6 发布、DeepSeek V4 Pro 上线、Qwen3.8 开源、Jeff Dean 离职创业、Anthropic IPO 前瞻、Manus 恢复独立等关键动态。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "Grok", "DeepSeek", "Qwen", "Anthropic", "具身智能"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 🚀 产品发布

### xAI 发布 Grok 4.6：聚焦长程 Agent 与视觉交互
来源: Hacker News
原文: [原文](https://x.ai/news/grok-4-6)
摘要: xAI 于 8 月 12 日发布 Grok 4.6，重点提升长时间运行的 Agent 能力与交互式视觉任务表现。该模型在 Artificial Analysis Intelligence Index 上以 61 分追平 GPT-5.6 Sol Max 和 Fable 5 Max，并在 DeepSWE 1.1、CursorBench 3.2 等编程基准中达到前沿水平。Grok 4.6 采用了比前代更长的补充训练流程，结合模型生成的推理数据与高质量工程数据改进优化器，现已上线 Cursor 和 Grok Build。

### DeepSeek V4 Pro 0813 正式发布：百万上下文 MoE
来源: Hacker News
原文: [原文](https://openrouter.ai/deepseek/deepseek-v4-pro-0813)
摘要: DeepSeek 于 8 月 12 日发布 V4 Pro 正式版（GA），采用大规模混合专家（MoE）架构，支持 100 万 Token 上下文窗口。API 定价为输入 $0.435/百万 Token、输出 $0.87/百万 Token，较同级别模型具备显著成本优势。该模型已在 OpenRouter 上线，开发者可直接调用。

### 通义千问开源 Qwen3.8-2.4T-A95B：万亿参数级 MoE
来源: Hacker News
原文: [原文](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B)
摘要: 阿里通义千问团队在 HuggingFace 发布 Qwen3.8-2.4T-A95B 开源模型，总参数量 2.4 万亿，激活参数约 950 亿。模型采用 MoE 架构，在多项推理与代码基准中表现接近闭源前沿模型，是当前开源阵营中规模与性能最强的模型之一。

## 📰 行业动态

### Jeff Dean 离职谷歌最后 48 小时：139 人会议、1500 人告别会、次日凌晨创立 Discovery Loop
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/471254.html)
摘要: Jeff Dean 在 KDD 2026 顶会上披露了离开谷歌的最后 48 小时时间线：先向 139 名核心同事视频会议公布离职，随后参加约 1500 人的告别会，当晚逐条回复 400 条消息至凌晨 2:30。8 月 6 日 23:59 他将身份改为"失业"，随后立即以 Discovery Loop 联创兼 CEO 身份重新上岗。新公司聚焦用 AI 和自动化工具加速机器学习与科学研究，联合创始人包括 Sanjay Ghemawat、Oriol Vinyals 和 Quoc Le。

### Anthropic 或于 10 月 IPO，投资人劝 CEO 少谈末日风险
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/471162.html)
摘要: Polymarket 预测 Anthropic 很可能在 10 月底进行 IPO，有投行预计募资超 600 亿美元，将成为全球规模第二大 IPO（仅次于 SpaceX 的 857 亿美元）。但部分投资者对 CEO Dario Amodei 频繁预警 AI 末日风险表示不满，希望他在 IPO 路演阶段更多强调商业前景。文章同时披露了 Claude 模型在网络安全测试中意外连入真实互联网的三起事故细节。

### Manus 脱离 Meta 恢复独立运营，面临大规模数据迁移
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/470805.html)
摘要: 被 Meta 收购的 AI Agent 产品 Manus 于 8 月 12 日宣布恢复独立公司运营，总部回归新加坡。作为分拆协议的一部分，2025 年 12 月 29 日后产生的部分用户数据将在 8 月 23-24 日被删除，用户需在窗口期内备份。Manus 表示正在筹备新功能，目标"再次突破通用 AI Agent 能力边界"。此前 Meta 收购金额超 20 亿美元。

## 🔬 技术进展

### 紫东太初提出 GMC 剪枝方法：80% Token 压缩仍满血保真
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/471030.html)
摘要: 中科院自动化所紫东太初团队提出视觉语言模型 Token 压缩新方法 GMC（Grounded Message Coreset Pruning），通过互补证据筛选与群体信息传输两阶段架构，在减少 80% 视觉 Token 的条件下保持多模态推理能力不降。方法全程免训练、无需额外模型依赖，已兼容 Qwen、LLaVA 等主流架构，在 POPE、HallusionBench 等幻觉评测集上表现优于原始完整模型。

## 🤖 具身智能

### 自变量机器人直播实测：夹爪方案以 30% 成本超越 Figure AI 分拣效率
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/471049.html)
摘要: 自变量机器人在公开直播中，使用双机械臂+标准夹爪方案完成物流分拣实测，1 小时分拣 1816 件随机异形包裹，超过 Figure AI 此前 1248 件/小时的纪录 45%，准确率 98%。硬件成本仅为 Figure AI 人形机器人方案的 30%。核心能力来自自研 WALL-B 世界统一模型，可实时感知包裹属性并动态调整抓取策略。

---

🦞 每日08:00自动更新

**数据来源**：量子位、Hacker News、Anthropic、OpenRouter、HuggingFace
