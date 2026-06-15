---
title: "AI新闻早报 2026-06-06"
date: 2026-06-06T07:36:00+08:00
slug: ai-morning-news-2026-06-06
description: "2026年6月6日 AI 新闻早报，汇总 24 小时内 Anthropic Mythos 泄密、DeepSeek 登顶 Ramp、互联网 Bot 流量反超人类等关键变化。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "Anthropic", "DeepSeek", "模型发布", "华为云"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 🔬 技术进展

### 智源&清华合作成果登上 Science：脑科学多模态基础模型 Brainμ 支撑"记忆-睡眠"调控研究
来源：量子位
原文：[原文](https://www.qbitai.com/2026/06/431033.html)
摘要: 2026 年 6 月 4 日，北京智源人工智能研究院与清华大学联合团队论文《Memory Reactivation Underlies Experience-Dependent Adaptive Regulation of Sleep》在国际期刊《科学》发表，由智源悟界·Brainμ 模型团队负责人雷博与清华生命学院钟毅共同通讯。研究首次表明睡眠中的记忆重激活可反向调控睡眠动态；智源自研的脑科学多模态基础模型 Brainμ0 提供 EEG、双光子钙成像与 Neuropixels 多模态神经信号的对齐表征与解码，辅助完成"伴随记忆重激活的睡眠"（MRS）与"非伴随"（Non-MRS）的识别和因果推断。

### Google 开源 Gemma 4 QAT 量化感知训练权重，针对移动与笔记本端设备优化
来源：Google（Hacker News）
原文：[原文](https://blog.google/innovation-and-ai/technology/developers-tools/quantization-aware-training-gemma-4/)
摘要：Google DeepMind 发布 Gemma 4 家族的 QAT（Quantization-Aware Training）检查点，覆盖 Q4_0 与一种新的量化格式，模拟量化过程训练以最小化压缩后的质量损失，目标是把 Gemma 4 直接跑在普通消费级 GPU 与边缘设备上。QAT 版本延续此前的 E4B、12B 与 26B MoE 等多个尺寸，并配合多 token 预测（MTP）以进一步加速推理。Google DeepMind 的产品负责人 Olivier Lacombe 与技术成员 Omar Sanseviero 在博客中将其定位为 Gemma 4 发布两个月后的"端侧可用版本"。

### 阶跃星辰 Step 3.7 Flash 登顶 AA 榜，输出速度 416 tokens/s、单任务成本约为 Claude Opus 4.6 的 1/9
来源：量子位
原文：[原文](https://www.qbitai.com/2026/06/429294.html)
摘要：阶跃星辰发布 Step 3.7 Flash，同时在 OpenRouter Trending 冲至全球第二，在 Artificial Analysis（AA）榜速度、性价比、端到端三项排名第一，HuggingFace 开源后下载量持续走高。官方实测显示其输出速度最高 416 tokens/s，单任务成本压到 Claude Opus 4.6 的约 1/9，但编程能力达到 Claude 约 97%。报道把这次发布定位为"效率优先"——在 Agent 工作链路下，推理延迟与 Token 成本正取代单点榜单分数成为新的赛点。

## 🚀 产品发布

### 华为云发布 Agentic AI 系列新品，提出 Agentic Infra 新范式
来源：量子位
原文：[原文](https://www.qbitai.com/2026/06/431027.html)
摘要: 2026 年 6 月 5 日华为云 INSPIRE 创想者大会上，华为云正式提出"Agentic Infra"新范式，并一次性发布四大基础设施新品：AICS 灵衢智算集群支持 10 万卡级规模、总算力 200 EFLOPS、Token 生成时延 10 毫秒以内；AMS Agentic 记忆存储基于 NPU 直通 CMS 打造 PB 级上下文记忆；CCE Volcano Next 引擎通过"训推共池+碎片整合"将通智混合算力利用率提升 30%；AgentSphere 提供极速弹性与 100 毫秒级沙箱启动。同步推出新一代 ModelArts Next 平台，集成 RL 强化学习、机密推理、模型路由与模型矩阵四大能力，模型调度精准率超 95%、调用成本平均下降 20%，并公测企业级智能体平台"智果 AgentArts"，开源版本 openJiuwen 同源度超 90%。

## 📰 行业动态

### Anthropic 内部 Mythos（Oceanus）红队测试遭内鬼倒卖 API，紧急停用并推迟发布
来源: 36 氪
原文：[原文](https://www.36kr.com/p/3840185187010824)
摘要: 36 氪 6 月 5 日报道，Anthropic 内部代号 Oceanus 的新一代大模型 Mythos 即将上线，在红队测试开放数小时内，被红队成员偷偷打包并转售给某国 API 代购服务商，相关凭据在 Claude Console 短暂露出"claude-oceanus-v1-p"检查点。事件爆出后 Anthropic 立即全面叫停红队测试并停用模型，预计下一批红队人员规模将更小、限制更严。同时泄露的参数显示模型吞吐量约 52 Token/s、单日使用成本达 80 美元；多家硅谷内线及爆料博主称 Mythos 大概率在 6 月 16 日正式发布。

### Cloudflare Radar：全球 HTML 网页请求中 Bot 流量首次反超人类，美国达 71.5%
来源: 36 氪
原文：[原文](https://www.36kr.com/p/3839937467419143)
摘要：Cloudflare Radar 最新数据显示，全球 HTML 网页请求中 Bot 机器人流量占比已达 57.5%、人类流量降至 42.5%，互联网有史以来首次出现机器请求多于人类请求的局面；美国市场这一数字更高达 71.5%。Cloudflare CEO Matthew Prince 在 X 上承认这一拐点比自己在 SXSW 预测的 2027 年底要早很多。文章指出 Bot 流量性质已经发生转变——从早期为系统服务的爬虫/监控，演变为代表用户意图行动的 AI Agent，预示着"互联网默认服务对象正在从人变成机器人"。

### Anthropic 发文呼吁全球 AI 实验室考虑放缓前沿开发，列举"递归式自我改进"风险
来源: 36 氪
原文：[原文](https://www.36kr.com/p/3839972948855045)
摘要：Anthropic 内部研究所负责人与政策主管在 6 月 4 日博客中披露模型能力提升数据，公开表示"如果世界能拥有放缓或暂时暂停前沿 AI 开发的选项，将是一件好事"，并提出"AI 系统在无人工干预下自我提升"已临近，需要全球协议与核查机制。文中同时提及 Anthropic 估值已接近 1 万亿美元并已秘密提交 S-1 草案启动 IPO。文章也引述 David Sacks、沃顿商学院教授 Ethan Mollick 等的不同声音——前者认为这是"监管俘获议程"，后者认为文章中"自我反思、营销和真诚判断"成分都有。

### 美国企业 SaaS 平台 Ramp 报告：DeepSeek 登顶"软件趋势榜"第一，成为增速最快软件之一
来源: 36 氪
原文：[原文](https://www.36kr.com/p/3840188780513792)
摘要: 36 氪独家引用美国企业支出管理平台 Ramp 最新报告：DeepSeek 首次登上 Ramp"软件趋势榜单"首位，该榜单追踪企业向某软件供应商的首次采购情况。Ramp Economics Lab 首席经济学家 Ara Kharazian 表示，这是美国企业"寻找 OpenAI、Anthropic 低成本替代方案"的最明显信号。Ramp 目前服务约 7 万家企业客户，较年初的 5 万家增长 40%，新增客户中相当一部分来自扩张中的 AI 初创企业。报道同时指出，DeepSeek 2025 年初 R1 期间美国企业采用率曾冲至 0.3% 后回落至 0.1%，此番再度升温被归因于"美国 AI 太贵"——有 AI 顾问透露一家企业未对 Claude 许可设上限，单月烧掉 5 亿美元，Uber 前四个月即耗尽全年 Token 预算。

---

🦞 每日08:00自动更新

**数据来源**：量子位、Google DeepMind（via Hacker News）、36 氪
