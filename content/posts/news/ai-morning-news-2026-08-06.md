---
title: "AI新闻早报 2026-08-06"
date: 2026-08-06T06:26:00+08:00
slug: ai-morning-news-2026-08-06
description: "2026年8月6日 AI 新闻早报，Sand.ai 开源千亿 MoE 视频生成模型，微软叫停 Tokenmaxxing，OpenAI 挖来黑客祖师爷，Ilya 首个模型被曝本月上线，Google DeepMind 管理层重大重组。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "模型开源", "行业动态", "视频生成", "网络安全"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 🚀 产品发布

### Sand.ai 开源千亿 MoE 视频生成模型 MAGI-2-preview
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/466847.html)
摘要: Sand.ai 发布并开源 MAGI-2-preview，总参数 114B、单次前向激活仅约 6B。模型采用单流 MoE 架构，支持 10 秒 1080P 视频生成，单次推理成本约 5 毛钱，仅为行业主流模型的十分之一。在 AA 视频生成榜单排名第六，是首个将视频 MoE 从理论落到千亿参数开源模型的产品。

### Meta 发布 Muse Code 和 Muse Spark 1.2
来源: Meta AI Research
原文: [原文](https://research.meta.ai/blog/introducing-muse-code-and-muse-spark-1-2)
摘要: Meta 正式发布 Muse Code（beta）终端编码 Agent 和 Muse Spark 1.2 模型。Muse Code 支持跨大型仓库的复杂软件工程任务，引入异步后台 Agent 持久化机制，减少重复信息收集。其运行时使用本地事件日志实现崩溃后精确恢复，可承担长时间运行任务而不被失败打断。

### 清华等提出全球首个连续时间具身世界模型 ODEWorld
来源: 36氪
原文: [原文](https://www.36kr.com/p/3926559299418502)
摘要: 清华大学团队提出 ODEWorld，是全球首个连续时间具身世界模型，支持任意帧率自由生成。该模型将连续时间建模引入具身智能领域，在模拟环境交互和物理世界建模方面取得突破，可广泛应用于机器人仿真和虚拟环境生成。

## 🔬 技术进展

### 微软叫停 Tokenmaxxing：内部设 AI Token 预算，默认用 GPT-5.6
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/466739.html)
摘要: 微软执行副总裁 Jay Parikh 发布内部邮件，从 2026 年 7 月起为各业务部门设置 AI Token 预算目标，并将 GPT-5.6 设为内部默认模型。员工可查看个人 Token 支出，部分工程师每月花费数百至数千美元。此前硅谷刮起的 Tokenmaxxing 风潮被微软正式叫停，纳德拉表示"生产率提升的边际收益必须匹配 Token 的边际成本"。

### 初创公司用 AI Agent 10 小时搭建类 CUDA 软件
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/466553.html)
摘要: 初创公司 Infinity 开发 AI 研究 Agent Ignition，为芯片厂商 d-Matrix 搭建了一套类 CUDA 底层软件，仅耗时 10 小时。Ignition 可自动生成 GPU Kernel、运行测试、发现错误并修改代码，形成完整闭环。该公司已获 1500 万美元融资，估值达 1 亿美元。分析认为，推理侧市场正在成为 CUDA 生态的新突破口。

### Prime Intellect 发布自改进 RLM Agent "Prime Agent"
来源: Hacker News
原文: [原文](https://www.primeintellect.ai/blog/prime-agent)
摘要: Prime Intellect 发布 Prime Agent，一个基于递归语言模型的自改进编码 Agent。其核心创新包括将子 Agent 委托视为函数调用、持久化 REPL 上下文管理，以及让 Agent 自主 CRUD 自己的 Prompt、Skills 和记忆。该设计突破了传统固定工具调用的限制，使 Agent 能在长时间运行中持续自我优化。

## 📰 行业动态

### OpenAI 挖来黑客祖师爷 Halvar Flake 负责网络安全
来源: 36氪
原文: [原文](https://www.36kr.com/p/3926558877333639)
摘要: 安全领域传奇人物 Halvar Flake 正式宣布下周入职 OpenAI，负责网络安全方向。OpenAI 多位联合创始人和核心研究员第一时间表示欢迎。Halvar 被业界称为黑客圈"祖师爷"级人物，这次加入是 OpenAI 在安全领域的重要布局。

### Ilya Sutskever 的 SSI 首个模型被曝本月上线
来源: 36氪
原文: [原文](https://www.36kr.com/p/3926559181961600)
摘要: 顶级投资人 Gavin Baker 透露，Ilya Sutskever 创立的 Safe Superintelligence（SSI）将于本月发布首个模型。Baker 是 NVIDIA 首位大型机构投资人，被黄仁勋亲自认证，其消息被业内视为可靠信息。若属实，SSI 将成为 AI 模型领域的重要新玩家。

### Google DeepMind 管理层重大重组：Demis 转任 Chair，Jeff Dean 离职
来源: Google Blog
原文: [原文](https://blog.google/company-news/inside-google/message-ceo/next-chapter-ai-momentum/)
摘要: Google 与 Alphabet CEO Sundar Pichai 宣布 DeepMind 重大管理层重组：联合创始人 Demis Hassabis 从 CEO 转任董事会主席，传奇工程师 Jeff Dean 正式离职，Sanjay Ghemawat 也一同离开。Google 通过官方博客宣布公司进入 AI 发展的新阶段，此次调整在业界引发广泛讨论。

---

🦞 每日08:00自动更新

**数据来源**：量子位、36氪、Meta AI Research、Prime Intellect、Hacker News