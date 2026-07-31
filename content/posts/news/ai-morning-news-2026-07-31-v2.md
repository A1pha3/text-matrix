---
title: "AI新闻早报 2026-07-31（RSS 多源提炼版）"
date: 2026-07-31T08:32:00+08:00
slug: ai-morning-news-2026-07-31-v2
description: "2026年7月31日 AI 新闻早报（RSS 多源提炼版），精选 GPT-5.6 递归自进化、MirrorCode 周级编程基准、Claude Code 之父 Harness 反思、AlphaFold 团队解散、翁荔重返 OpenAI、李飞飞 R2S2R、无问芯穹 PDD、ChatGPT 突破 10 亿用户等关键动态。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "OpenAI", "Anthropic", "DeepMind", "RSI", "Agent", "机器人"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## OpenAI 披露 GPT-5.6 递归自进化：生产成本降 20%
来源: 量子位、Import AI
原文: [原文](https://www.qbitai.com/2026/07/463297.html)
摘要: OpenAI 最新技术报告披露，GPT-5.6 已被投入真实生产环境执行递归自优化（RSI）：分析线上流量并调整请求路由、通过 Codex 改写底层 Triton/Gluon Kernel、为推测解码系统设计并测试 draft model、自动搜索 batching 与 KV Cache 的最优组合。实施后端到端服务成本降低 20%，Token 生成效率提升 15% 以上，作者名单含 Triton 之父 Philippe Tillet。Import AI 已连续多期追踪该方向（从「AI systems are about to start building themselves」到「paths to ASI」），这是主流厂商首次系统性公开生产级 RSI 实践，目前仍保留 human-in-the-loop。

## MirrorCode 基准发布：AI 独立完成人类数周的编程任务
来源: Import AI（Epoch × METR）
原文: [原文](https://importai.substack.com/p/import-ai-466-the-bitter-lesson-for)
摘要: Epoch 与 METR 发布长程编程基准 MirrorCode，要求模型仅凭 CLI 访问、在不读源码和不上网的前提下完整重实现一个软件。Opus 4.7 花费 14 小时、251 美元推理成本，完成了一个 METR/Epoch 估计人类需 2-17 周的任务。一年前的主流模型只能解决约 30% 的较简单样本（如日历工具），如今已能重实现 Apple 的 pkl（6.1 万行配置语言）等项目。最难的样本 AI 仍无法解决，作者认为这在当下「是件好事（good）」。

## Claude Code 之父：Harness 保质期只有半年，呼吁「解缰绳」
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/07/463433.html)
摘要: Claude Code 作者 Boris Cherny 在 YC 访谈中建议：每六个月删掉 Claude.md、skills 和 hooks，逐行重新加回以测试每行的真实影响（消融实验）。7 月 24 日 Anthropic 已将 Claude Code 的 system prompt 删除超过 80%，harness 几乎只剩安全、权限与静态分析。Boris 将模型比作「有自己性格的活体生物」，主张产品迭代「少预判、多测试」，并让模型承担更难、更长时间独立任务。这与 Import AI 同期讨论的 robotics「bitter lesson」相互呼应。

## DeepMind 解散 AlphaFold 团队，诺奖得主投奔 Anthropic
来源: 量子位（金融时报）
原文: [原文](https://www.qbitai.com/2026/07/463123.html)
摘要: 据《金融时报》，打造 AlphaFold 并诞生诺贝尔化学奖得主的 DeepMind 明星团队已不再作为独立团队存在。AlphaFold 2 负责人、诺奖得主 John Jumper 离开工作近 9 年的 DeepMind 转投 Anthropic，核心成员 Jonas Adler 与 Alexander Pritzel 同行。初期署名 AlphaFold 论文的 DeepMind 员工中近四分之一已离开，且多人流向同一竞争对手 Anthropic。其余成员转入 Gemini、AI 编程、核聚变，或 Alphabet 旗下 Isomorphic Labs 从事药物研发。

## 翁荔重返 OpenAI，领导「自进化」研究团队
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/07/462947.html)
摘要: 因健康原因刚从 Thinking Machines Lab 离职的翁荔，已重返 OpenAI，领导高优先级的「自进化」（RSI）团队，目标是让模型训练并改进自身的后继模型——她本月初刚发布过 RSI 深度博客。至此 Thinking Machines Lab 六位联合创始人中已有三人（翁荔、Barret Zoph、Luke Metz）回归 OpenAI，公司仅剩 CEO Mira Murati 与首席科学家 John Schulman。

## 李飞飞 World Labs 发布 R2S2R：世界模型训练真实机器人
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/07/463217.html)
摘要: World Labs 借收购机器人公司 SceniX 之力，发布 Real-to-sim-to-real（R2S2R）引擎，首次打通真实→仿真→真实闭环。Real-to-Sim 将真实机器人、传感器与交互过程搬进虚拟环境，Sim-to-Real 把训练好的策略迁移回真实机器人。李飞飞称基于此训练的策略即使完全不用真实世界数据，也能连续自主运行 1 小时无需人工干预，填补了其世界模型三分法（渲染器/仿真器/规划器）中「仿真器」这块关键拼图。

## 无问芯穹 PDD：PD 分离延迟降 51.5%、成本降 37.5%
来源: 量子位（WAIC 2026）
原文: [原文](https://www.qbitai.com/2026/07/463012.html)
摘要: 无问芯穹公布跨集群异构推理架构 PDD，将传统 Prefill-Decode 两级分离扩展为 P-RLD-MD 三级，以广域网以太网串联各地已建成的同构数据中心，让「偏科」的硬件只做擅长的题。实测首 Token 延迟降低 51.5%，单 Token 成本降低 37.5%，突破了以太网环境下 KV Cache 跨集群传输的延迟瓶颈。技术报告已在 GitHub 开源。

## ChatGPT 周活跃用户突破 10 亿
来源: Ben's Bites
原文: [原文](https://www.bensbites.com/p/1-billion-chatgpt-users)
摘要: ChatGPT 周活跃用户正式突破 10 亿，成为全球用户规模最大的消费级 AI 应用。AI 产品首次跻身「十亿用户俱乐部」，与 Google Search、YouTube、微信等比肩。同期 OpenAI 推出 GPT-5.6 桌面应用与托管站点功能，继续扩张产品边界，标志着消费级 AI 渗透已进入主流阶段。

---

🦞 每日08:00自动更新

**数据来源**：量子位、Import AI、Ben's Bites（RSS 多源订阅）
