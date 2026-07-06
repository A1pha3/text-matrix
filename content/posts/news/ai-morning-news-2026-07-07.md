---
title: "AI新闻早报 2026-07-07"
date: 2026-07-07T07:14:49+08:00
slug: ai-morning-news-2026-07-07
description: "2026年7月7日 AI 新闻早报，覆盖 7 月 6 日 ICML 2026 公布 10 篇获奖论文含清华阿里 dLLM 杰出论文、腾讯混元 3 正式版总参 295B 激活 21B、字节 Seedance 进入好莱坞长片工作流、大厂集中整合 AI 入口告别赛马、Karpathy 解读 Agent 性能差距在 Harness 而非模型、Meta 推出 Meta Compute 卖 GPU 算力、Martin Alderson 论 GLM 5.2 引发 AI 利润率塌缩。"
draft: false
categories: ["行业快讯"]
tags: ["ICML", "腾讯混元", "Seedance", "Agent Harness", "Meta Compute", "GLM"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 🚀 产品发布

### 腾讯混元 3 正式版发布：搜索追平 GPT-5.5，幻觉率减半
来源: 36氪（字母AI）
原文: [原文](https://www.36kr.com/p/3884027229420160)
摘要: 姚顺雨加入腾讯后首个重量级产品 Hy3 正式版落地。模型总参 295B、单次激活 21B、外加 3.8B MTP 层，80 层 GQA 分组注意力，64 头中 8 个 KV 头，隐藏层维度 4096，中间层 13312，专家系统 192 选 top-8，上下文 256K、词表 120832，精度 BF16。架构沿用 Hy3 preview 不变，官方把提升归功于"后训练数据质量与多样性提升"和"RL 算力规模扩大"，有效参数量约为 GLM 5.2 的一半。文中称 Hy3 正式版搜索能力追平 GPT-5.5、幻觉率减半。

### 字节 Seedance 进入好莱坞长片工作流
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/07/443665.html)
摘要: 据《洛杉矶时报》报道，字节 Seedance 2.0 正在进入洛杉矶 AI 创作者圈、独立电影项目与好莱坞周边工作流。Higgisfield AI 出品的 95 分钟长片《Hell Grind》主要用 Seedance 2.0 制作，15 人团队两周完成；Kavan Cardoza 创作的 AI 奇幻剧集《骸骨编年史》同样基于 Seedance，月更一集、单集均观看量 300 万、Cardoza 在 YouTube 累计粉丝 50 万。回顾今年 2 月，Seedance 2.0 因一段布拉德·皮特与汤姆·克鲁斯天台打斗视频在海外爆火，被 MPA 点名批评可能侵权；4 个月后，好莱坞从最初抵触转向接受，工具被用于概念短片、镜头风格测试、pitch 素材与长片制作。

## 🏆 学术里程碑

### ICML 2026 公布 10 篇获奖论文：黄高团队获杰出论文，A3C 获时间检验奖
来源: 36氪（机器之心）
原文: [原文](https://www.36kr.com/p/3883880502046980)
摘要: ICML 2026 第四十三届会议 7 月 6 日至 11 日在韩国首尔举行，今年共收到 247 份 workshop 提案、44 项入选。奖项含 2 篇杰出论文、1 篇杰出立场论文、5 篇杰出论文荣誉提名、1 篇立场论文荣誉提名、1 篇时间检验奖。清华黄高团队参与、阿里清华合作的《The Flexibility Trap: Rethinking the Value of Arbitrary Order in Diffusion Language Models》获杰出论文，论文提出 JustGRPO 方法，放弃 dLLM 任意顺序生成、强制从左到右配合 GRPO 训练，GSM8K 上准确率达 89.1% 并保留并行解码能力；A3C 算法获得时间检验奖；麻省理工 / 耶鲁的《High-accuracy sampling for diffusion models and log-concave distributions》拿下第二篇杰出论文；慕尼黑大学的立场论文《The Alignment Community is Unintentionally Building a Censor's Toolkit》获得杰出立场论文。

## 🧠 Agent 工程

### Karpathy 解读 Agent 性能差距在 Harness 而非模型
来源: 36氪（AI前线）
原文: [原文](https://www.36kr.com/p/3884083529658374)
摘要: 文中援引 Anthropic 预训练研究员 Andrej Karpathy 在播客《AGI is still a decade away》中的观点："今天 AI 行业最大的误区，是大家都在逼 Agent 尽快干活，却没有先把底层模型和系统机制理解吃透。"Hugging Face 工程师 Joel Niklaus 的实验《Don't Train the Model, Evolve the Harness》佐证了这一判断：在冻结 DeepSeek-V4-Pro 权重、不做任何微调的前提下，仅替换 5 种 Agent Harness，pooled score 在 3.5% 到 80.1% 之间剧烈波动（差距 76 分）；经过约 22 轮代码自动迭代优化后，在 100 个 held-out test 任务上从 63.4% 提升到 80.1%，追平 Claude Sonnet 4.6，运行成本仅为原来的 1/7；同一 Harness 迁移到 DeepSeek-V4-Flash 仍能提升 14.4 分，证明 Harness 比 prompt 调优更易沉淀和跨模型迁移。

## 📰 行业整合

### 大厂 AI 步入"大一统"：告别赛马试错期，入口归一、能力聚合
来源: 36氪（商业新研社）
原文: [原文](https://www.36kr.com/p/3884034614950534)
摘要: 文章观察"百模大战"野蛮生长周期落幕，最近半个月大厂在 AI 业务上呈现统一动作：微信启动原生 AI 助手"小微"灰度测试，支付宝上线"阿宝"，两大国民级超级应用以整合方式推动 AI 落地；字节豆包开启付费功能、做市场分层与 C 端资源集中化运营；百度整合文心全产品线打造一站式 AI 服务门户；阿里收拢 QoderWork、悟空、MuleRun 分散 AI 工具，准备推出统一生产力 AI 平台。能力上"小微"已支持语音或文字调整微信设置、发消息、打电话、调生活小程序；"阿宝"覆盖居家、交通、优惠采购、政务、钱包、陪伴等场景。

## 💰 算力经济学

### Meta 推出 Meta Compute，卖 GPU 算力转向 Neocloud
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/07/443606.html)
摘要: 据彭博社与 SemiAnalysis 报道，Meta 正考虑推出 Meta Compute，把庞大 AI 基建开放给外部客户。今年前 6 个月 Meta 已签下超过 5GW 的云和托管数据中心容量，建设中的两个最大数据中心园区合计代表 2.5GW 容量，自 2024 年初以来累计交易接近 10GW。Meta 内部 AI 团队（亚历山大王的 MSL）继续用算力训练 Muse Spark 与下一代模型 Watermelon；同时可能与 Anthropic 进行最终谈判获得 Claude 私有实例访问权，复制 Amazon Bedrock、Microsoft Foundry、Google Vertex 模式做模型服务平台。Meta 2026 年资本开支指引 1250–1450 亿美元，一季度 198.4 亿美元已落地；消息公布后 Meta 股价大涨近 9%，而 CoreWeave、Nebius 等 Neocloud 厂商遭遇抛售。

## 💹 模型经济学

### GLM 5.2 与即将到来的 AI 利润率塌缩
来源: Hacker News（Martin Alderson 博客）
原文: [原文](https://martinalderson.com/posts/the-upcoming-ai-margin-collapse-part-1-glm-5-2/)
摘要: Martin Alderson 7 月 6 日发布的两部分系列首篇指出，"真正的 DeepSeek 时刻"已经到来。DeepSeek R1 训练成本据报道低于 600 万美元，曾让市场恐慌性抛售 Nvidia；作者认为这是误读——训练是固定资本支出，"完成即结束"；真正的边际成本集中在推理上，且 API 标价远高于真实成本。当 GLM 5.2 这类新一代开源模型进一步压缩单位推理成本，Anthropic、OpenAI 收取的 $25/MTok 定价将无法维持，AI 行业将进入利润率塌缩阶段。文章预告第二部分将在后续发布。

---

🦞 每日08:00自动更新

**数据来源**：36氪（字母AI、AI前线、机器之心、商业新研社）、量子位、Hacker News（Martin Alderson 博客）
