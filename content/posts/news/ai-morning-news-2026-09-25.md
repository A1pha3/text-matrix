---
title: "AI新闻早报 2026-09-25"
date: 2026-09-25T06:30:00+08:00
slug: ai-morning-news-2026-09-25
description: "2026年9月25日 AI 新闻早报，精选过去 24 小时内 Gemini 3.8 Live Avatar、Claude 发现新酶系统、DeepSeek PCIe 推理优化、米奥兰特小元AI 等产品与研究动态。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "Gemini", "Claude", "具身智能", "开源工具"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 🚀 产品发布

### Google DeepMind 发布 Gemini 3.8 Live with Live Avatar
来源: Google DeepMind
原文: [原文](https://deepmind.google/blog/introducing-gemini-38-live-with-live-avatar/)
摘要: Gemini 3.8 Live 新增 Live Avatar，为实时语音对话带来近实时可视形象，表情随对话自适应，支持 97 种语言。企业可从单张高质量参考图生成保留品牌形象与角色特征的定制动画头像（目前仅限企业白名单），所有音视频输出均嵌入 SynthID 水印以保证 AI 生成内容可检测。

### 米奥兰特全球首发 AI 出海经营智能体"小元AI"
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/496961.html)
摘要: 9 月 23 日全球数字贸易博览会上，米奥兰特发布面向中国外贸企业的 AI 出海经营智能体"出海精灵·小元AI"，依托 30 余年出海服务经验、千万级全球买家数据与百万级真实询盘，覆盖市场洞察、买家分析、客户盘点、内容营销、展会策划五大任务。背景是字节"豆包工作"、阿里"千问办公"、腾讯 WorkBuddy 接连整合入场，AI 办公赛道进入集团军作战阶段。

## 🔬 技术进展

## 📰 行业动态

### Meta Muse 登顶北美 App Store，Meta 股价单日暴涨 11%
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/496647.html)
摘要: Meta 超级智能实验室的个人 AI 智能体 Muse 上线 13 天登顶北美 App Store，增速超过 2022 年末的 ChatGPT，Meta 股价周一暴涨 11% 创近一年最大单日涨幅。用户实测中 Muse 可自主拨打客服电话砍价：与 Xfinity 客服三方连线砍网费月省 85.3 美元并锁定 5 年，帮健身房用户 15 分钟砍掉车险 1156 美元，通话记录全程透明可查。

### 蔚来发布多模式世界-动作联合模型 MM-Future
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/496834.html)
摘要: 任少卿时隔十年以通讯作者身份回归论文署名，第一机构为 NIO。MM-Future 一次生成多组"配对场景-动作假设"，让轨迹与对应未来场景共同演化再择优执行，解决了级联式方案单向传递、联合式方案单结果输出的空白，使自动驾驶"走一步想十步"。论文核心设计围绕多样性来源（Gaussian Mixture Noise）、多假设计算成本与候选筛选三道门槛展开。

### 诺因发布通用具身智能 GLOW 技术报告：机器人"一教就会"
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/496816.html)
摘要: 9 月 24 日诺因（Knowin）发布 GLOW 生成式学习架构技术报告，将人类一次完整演示、环境状态与执行历史放在同一链路中理解，实现跨物体、跨环境、跨任务复用：换壶浇水、换盒收纳、复现心形擦桌轨迹、多杯多步调酒均已验证。报告发布正值 GPT-6 Astra 引发具身智能路线之争，行业共识正转向"自回归架构收敛、竞争核心在数据与学习方式"。

### DeepSeek PCIe 推理优化：软件调优吞吐提升近 7 倍
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/496925.html)
摘要: 是石科技自研 Meta-Infer 推理引擎针对无高速卡间互联的 PCIe 显卡，通过内核补齐、通信重构、并行调优等纯软件手段释放被适配问题锁住的硬件性能：DeepSeek-V4.1-Flash 在 8 张 PCIe 显卡上输入吞吐从社区基线 1932 tok/s 提升至 5850 tok/s，1.5 台 6000D 即可跑赢 1 台 B300，同一思路已在 GLM5.3 等模型复现。

## 🧪 研究探索

### Anthropic Project Swap：让 Agent 替人交易的微型市场实验
来源: Anthropic
原文: [原文](https://www.anthropic.com/research/project-swap)
摘要: 六个办公室的员工带一本书入场，与 Claude 聊五分钟阅读偏好后派 Agent 上交易场谈判换书。仅凭短对话，Agent 的书目排序与其主人匹配度达 61%；交易环节表现良好，失败主要源于 Agent 掌握的偏好信息不足而非谈判能力。团队随后更换模型与指令重跑数十次交易场，系统性测量 Agent 经济的行为边界。

## 🛠️ 开源工具

### LiquidAI 开源 LFM2.5-VL-DSpark：视觉语言模型投机解码加速
来源: HuggingFace
原文: [原文](https://huggingface.co/blog/LiquidAI/lfm2-5-vl-dspark)
摘要: LiquidAI 为 3B 视觉语言模型 LFM2.5-VL-3B 发布实验性 DSpark 投机解码草稿模型，仅增加 280M 参数（+8.9% 显存）即换来端侧最高 3.13 倍、H100 上 2.66 倍的解码加速，端到端增益最高 2.62 倍，输出质量不变，并配套 llama.cpp、MLX-VLM、SGLang 首日集成支持。

### Whiteboard（YC W26）：人与 Agent 共用画布的开源设计 IDE
来源: Hacker News
原文: [原文](https://github.com/devdotfast/whiteboard)
摘要: YC W26 团队开源桌面应用 Whiteboard，接入 Claude Code、Codex 等编码 Agent，并给 Agent 提供 SDK 在应用内画布上绘制架构图、解释改动。项目推荐配合 GPT-6 Sol 与 Claude Opus 5.5 使用，当前提供 macOS 与 Fedora 版本，登陆 Hacker News 首页引发讨论。

---

🦞 每日08:00自动更新

**数据来源**：量子位、Google DeepMind、Anthropic、HuggingFace、Hacker News
