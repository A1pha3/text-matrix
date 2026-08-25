---
title: "AI新闻早报 2026-08-26"
date: 2026-08-26T06:40:42+08:00
slug: ai-morning-news-2026-08-26
description: "2026年8月26日 AI 新闻早报，精选过去 24 小时内模型、芯片、融资与具身智能领域的重要动态。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "具身智能", "大模型", "芯片"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 💰 融资财报

### Anthropic 启动 500 万美元研究资助，聚焦 AI 对用户福祉的影响
来源: Anthropic
原文: [原文](https://www.anthropic.com/news/wellbeing-research-grants)
摘要: Anthropic 宣布推出 500 万美元资助计划，为研究 AI 如何影响用户福祉的独立项目提供资金、模型访问与技术支持，受助者需以开源形式发布成果。官方表示，业界在衡量 AI 对话中用户情感支持等福祉影响方面仍缺乏统一标准，这一项目意在补齐评估能力。

### 未来不远机器人半年三轮融资共 10 亿元，字节跳动入股
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/479132.html)
摘要: 报道披露，字节跳动已入股家用通用机器人公司未来不远最新一轮融资，叠加汇川产投、国方创投等近 10 家机构，该公司半年内累计融资 10 亿元。这家全球首个实现家庭商业化落地的通用机器人公司已覆盖研发、数据迭代、量产与销售全链路，据称产品已进入数百个家庭。

## 🚀 产品发布

### 开源国产 8B 生图模型 SenseNova U1.5 Lite 正式版发布
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/479192.html)
摘要: 量子位测评显示，商汤 SenseNova U1.5 Lite 时隔三周从预览走向正式版，主打"更完整、更准确、更稳定"。实测中它可组织长文本、多层级结构、插画与版式关系的复杂信息图，也能在多张参考图之间区分内容与设计逻辑，局部编辑后保持原视觉风格，被评价为已接近可直接使用的封面级产出。

### Ilya Sutskever 的 SSI 首个模型疑本周发布
来源: 36氪
原文: [原文](https://www.36kr.com/p/3954832606510208)
摘要: a16z 合伙人 Martin Casado 预告"刚获得今年最重要模型的访问权限"后，多方线索指向 Ilya Sutskever 创立的 Safe Superintelligence（SSI）。报道称 SSI 可能在持续学习等方向取得突破，首个模型或以测试时训练为核心、直接对标预训练范式，黄仁勋据称已斥资约 50 亿美元押注该公司。

### IBM 开源 Granite 4.2 系列模型，最高 30B 参数支持 512K 上下文
来源: Hugging Face
原文: [原文](https://huggingface.co/blog/ibm-granite/granite-4-2)
摘要: IBM 通过 Hugging Face 发布 Granite 4.2 系列，提供 3B、8B、30B 三个稠密版本，基于约 15 万亿 token 的五阶段训练，支持 512K 长上下文与原生工具调用。SFT 数据以软件工程为主（约占 69%），并采用 GPT-OSS-120B 与 Gemma 4 作为质量裁判过滤样本。

## 🔬 技术进展

### OpenAI 自研推理芯片 Jalapeño 亮相，官方基准超越英伟达芯片
来源: SemiAnalysis
原文: [原文](https://newsletter.semianalysis.com/p/openai-jalapeno-better-than-nvidia)
摘要: SemiAnalysis 报道，OpenAI 在 Hot Chips 上公开了与博通合作自研的推理芯片 Jalapeño，从组建团队到流片仅约 16 个月。受邀实测显示，其在多款开源模型上的推理表现超过团队测试过的英伟达、AMD 与谷歌芯片，据称依靠软硬件协同设计实现，而非对单一规格的过度定制。

### 原力灵机 DM0.5 登顶 RoboDojo，具身大模型全开源
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/478791.html)
摘要: 原力灵机发布的开源具身基座模型 DM0.5 在由港大、伯克利、清华等机构联合推出的 RoboDojo 评测中登顶。它原生支持最长 60 秒的动作记忆，可跨语言理解人类示教视频，并在 0.1-1 毫米尺度的微型积木拼装等精细操作上超过人手抖动极限。

### 研究提出量化感知修复（QAH）：4-bit 压缩模型反超全精度原版
来源: Hugging Face
原文: [原文](https://huggingface.co/blog/MultiverseComputingCAI/quantization-aware-healing)
摘要: 多所机构联合发表的论文提出 Quantization-Aware Healing（QAH），针对结构压缩后再量化的模型设计专门修复流程。将该方法应用于 120B 参数模型压缩至 60B 并量化为 MXFP4 后，模型在 9 项基准中的 7 项超过了原 bfloat16 全精度版本，实现了更小、更省算力且更准确的"反向关系"。

## 🤖 具身智能

### 范式联合优必选等十余家具身厂商，PhanthyMotus 从开源走向共建
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/479314.html)
摘要: 范式宣布 PhanthyMotus 具身生态共建计划进入新阶段，优必选、北京人形机器人创新中心、星动纪元等十余家头部本体厂商共同见证。社区成立两个月已汇聚宇树、智元、大疆、云深处等厂商开发者，累计贡献超 60 万行代码、完成 15+ 主流本体适配，目标 2026 年底前完成 50+ 本体适配。

### AI4S 进入"项目时代"：紫东太初把 AI 从做 Task 推向做 Project
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/479096.html)
摘要: 量子位报道称 AI for Science 正从工具级转向系统级，紫东太初提出让 AI 承接完整科研项目而非单一科研任务。报道指出，过去 AI 多作为任务智能体在科研人员明确目标后完成独立 Task，新的范式要求 AI 具备项目规划、多环节衔接与结果验证能力，这被视为 AI4S 能力的一次范式切换。

### Ben's Bites：移动端 Agent 正在成为新焦点
来源: Ben's Bites
原文: [原文](https://www.bensbites.com/p/agents-on-your-mobile)
摘要: 订阅量超 17 万的 AI 产品通讯 Ben's Bites 本周围绕"移动端 Agent"发起讨论，话题聚焦用户希望在桌面还是手机使用 Agent，以及移动场景下 Agent 的能力边界。报道整理了近期移动端 Agent 的产品进展与使用体验，反映工程师社区对端侧智能体落地的关注正在升温。

---

🦞 每日08:00自动更新

**数据来源**：Anthropic、量子位、36氪、Hugging Face、SemiAnalysis、Ben's Bites
