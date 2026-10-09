---
title: "AI新闻早报 2026-10-10"
date: 2026-10-10T06:28:33+08:00
slug: ai-morning-news-2026-10-10
description: "2026年10月10日 AI 新闻早报，精选过去 24 小时内模型研究、具身智能、企业级开源与海外融资动态，含清华具身模型登顶 RoboDojo、字节 Seed 揭示 DeepSeek 波动原因等。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "具身智能", "代码智能体", "融资"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 🔬 技术进展

### 字节Seed团队揭示DeepSeek表现"时强时弱"之谜：Token位置周期性影响准确率
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/10/502364.html)
摘要: 字节Seed研究人员发现，同一道题在输入前多塞几个无关Token，DeepSeek-V4 的答案就会反复横跳，且以 4 个 Token 为周期性变化。在 128K 长上下文检索测试中，同一条信息仅因位置不同，检索准确率差距最高达 40.2 个百分点。研究将根因指向 DeepSeek-V4 采用的分块KV Cache压缩技术——这项为省内存优化的设计，反而让模型对信息站位异常敏感。

### 清华具身公司星动纪元VPP2登顶RoboDojo，超越GPT-6-Astra与英伟达GR00T
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/10/502125.html)
摘要: 星动纪元自研的世界动作模型 VPP2 在 RoboDojo 仿真榜单以综合平均成功率 32.26%、综合得分 39.26 双指标登顶全球第一，在泛化、精细操作、记忆三个维度也均列榜首。该成绩未使用额外数据、未依赖 Agent RSI 等增强手段，技术路线核心是将视频预测与动作学习分阶段解耦训练。

### Google诊断AI研究首登《柳叶刀》主刊：AMIE鉴别诊断与医生吻合度达90%
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/10/502359.html)
摘要: Google 与贝斯以色列女执事医疗中心（BIDMC）在真实门诊场景中对 98 名患者开展研究：患者就诊前使用研究级诊断AI聊天机器人 AMIE，医生全程监控，无任何对话因安全问题被中断。75% 的场景下 AI 摘要帮助医生提前接诊准备，超过半数案例中 AI 输出改变了诊疗思路，鉴别诊断与最终确诊吻合度达 90%。

### UCSD系因果智能公司Aether AI发布CRIS-0：机器人0.2秒急停、秒级重规划
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/10/502411.html)
摘要: 因果智能企业 Aether AI 的机器人系统 CRIS-0 在官方 Demo 中展示了对突发扰动的实时推理能力：关闭微波炉门时遇人手介入可在 0.2 秒内悬停，咖啡制备测试中遭遇人为移位与光照突变，平均 2 秒内识别因果变量改变并完成重规划，10 次随机扰动中 9 次有效恢复。其路线核心是让机器人从"看到什么"走向"理解为什么发生"。

## 🚀 产品发布

### TRAE正式合并Code与Work，统一AI开发工具形态
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/10/502426.html)
摘要: TRAE 将面向程序员的 Code 与面向通用办公的 Work 两条产品线正式合并，统一为单一产品形态。此举意在打通代码与工作流场景的边界，让同一智能体同时覆盖开发与日常任务。

### openJiuwen发布并开源企业级AgentOS，多智能体协同+自演进底座
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/10/502106.html)
摘要: 由华为2012实验室、华为云等多团队联合高校与企业构建的开源AI Agent平台 openJiuwen 发布企业级 AgentOS，将多智能体协同、自演进、算力亲和与企业级安全能力融入统一底座。其通过蜂群协同与工作流编排支持任务拆解和并行执行，依托执行轨迹与记忆机制沉淀可复用经验，并在华为全联接大会2026上推出基于该系统的开源Agent加速平台一体机方案。

### 联想天禧TianxiCode获SWE-bench-Live全球第一，通过官方Verified认证
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/10/502422.html)
摘要: 联想天禧AI自研的代码智能体框架 TianxiCode 配合 DeepSeek-v4.1-Flash，在国际软件工程评测 SWE-bench-Live（Lite分榜）以 71% 的问题解决率登顶全球第一，并通过官方对运行轨迹的严格审查获得 Verified 认证。该框架聚焦代码生成与工程开发，未来将应用于联想 AI 硬件产品。

## 💰 融资财报

### TypeSafe AI完成8.7亿美元融资，估值达75亿美元
来源: TypeSafe AI
原文: [原文](https://typesafe.ai/blog/series-ai)
摘要: 机器原生智能基础设施公司 TypeSafe AI 宣布由 Andreessen Horowitz 领投、Sequoia 与 DCVC 参投的大额融资，融资额 8.7 亿美元，投后估值 75 亿美元。官方称三分之一的财富500强企业已在使用其首个 System One 模型 Jev，生产环境累计为客户节省数百万美元成本。

## 📰 行业动态

### Cloudflare收购Deno，Ryan Dahl团队整体加入
来源: Deno
原文: [原文](https://deno.com/blog/cloudflare)
摘要: Deno 官方宣布加入 Cloudflare，创始人 Ryan Dahl 及团队将整体并入。官方称这一组合把 Deno 的运行时技术积累与 Cloudflare 的全球边缘网络结合，继续推进简化服务器软件构建的目标，Deno Deploy 与 JSR 等产品路线将照常演进。对 Web 开发生态而言，这是 Runtime 竞争格局的一次重要整合。

### Ai2开源实践：如何为GPU集群构建"高影响力"调度器
来源: Hugging Face
原文: [原文](https://huggingface.co/blog/allenai/impactful-scheduling)
摘要: Ai2 基础设施团队分享其 GPU 集群调度器设计，提出可用性、占用率、影响力、利用率四层指标金字塔，重点解决"过度提交"导致的资源挤占问题。文章给出公平共享、预算约束的调度契约设计与仿真结果，为研究机构的算力治理提供了可复用的工程参考。

---

🦞 每日08:00自动更新

**数据来源**：量子位、TypeSafe AI、Deno、Hugging Face
