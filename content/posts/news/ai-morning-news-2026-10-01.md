---
title: "AI新闻早报 2026-10-01"
date: 2026-10-01T06:31:16+08:00
slug: ai-morning-news-2026-10-01
description: "2026年10月1日 AI 新闻早报，汇总过去 24 小时内 Gemini 4 Argon 发布、DeepSeek 开源昇腾组件与 DSec 基础设施披露、Manus 2.0 回归、GPT-6 控制机器人等关键动态。"
draft: false
categories: ["行业快讯"]
tags: ["Gemini 4", "DeepSeek", "AI Agent", "机器人", "开源生态"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 🚀 产品发布

### Google DeepMind 发布前沿模型 Gemini 4 Argon
来源: Google DeepMind
原文: [原文](https://deepmind.google/blog/gemini-4-argon-our-next-era-of-frontier-intelligence/)
摘要: DeepMind 于 10 月 1 日凌晨正式官宣 Gemini 4 Argon，定位为面向真实世界编程（real-world coding）、企业知识工作与网络防御的前沿模型，将陆续推送给用户。官方口径将其称为"下一代前沿智能"的开端，博客明确了三大主攻方向而非泛用宣传。

### Manus 2.0 回归：给 Agent 配手机号、钱包，还能拉群协作
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/499592.html)
摘要: 9 月 1 日宣布恢复独立运营的 Manus 发布回归后首个大版本 Manus 2.0，带来新 Agent 底座与创作工作台 Manus Studio（支持剪视频、做游戏，人可随时接手），并推出个人 Agent 应用 Cue——为 Agent 配备邮箱、电话号码、钱包和电脑，多个助手可拉群协作办事。国内市场产品正在筹备。发布时点恰在老东家 Meta 的个人 Agent Muse 登顶美区 App Store 免费榜 10 天后，收购方与被收购方在 Agent 赛道正面相遇。

## 🔬 技术进展

### DeepSeek 知乎独家长文，首次公开 V4 训练"大本营" DSec
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/499308.html)
摘要: DeepSeek 在知乎发布技术长文，首次系统阐释支撑 DeepSeek-V4 全部训练、评测与数据预处理的沙盒基础设施 DSec（DeepSeek Elastic Compute）。技术报告已公开至 arXiv，由 DeepSeek 联合清华大学发布，作者超过 130 人，梁文锋在列。DSec 的核心命题是让 Agent 大模型在真实环境里反复试错——读代码、改文件、装依赖、跑测试。

### GPT-6 Astra 接上宇树 G1，斯坦福 HomeBody 让机器人收拾厨房
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/499493.html)
摘要: 斯坦福团队项目 HomeBody 中，宇树 G1 先自主探索陌生厨房，再按语言指令归拢物品、丢纸盒，甚至凭记忆找到不在视野内的药并递给人。核心思路是让 GPT 把机器人技能当工具调用；团队表示部署到新厨房无需额外采集训练数据或训练专用动作策略，泛化能力显著。大模型控制机器人的任务范围从桌面抓放扩展到了整屋移动操作。

### Noam Brown 访谈：万 Agent 解千禧年难题，多智能体只是开胃菜
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/499654.html)
摘要: o1 核心作者 Noam Brown 在 Dwarkesh Patel 播客中谈及此前 OpenAI 用 1 万个 Agent、耗时 88 小时、输出 1300 亿 token 解出千禧年数学难题的工作，并称该突破中 10000 个 Agent 最多只占 10% 的功劳。他将多智能体定义为"推理时计算从串行到并行的扩展"，并展望了递归自我改进（RSI）、超级对齐等下一步方向。

## 🛠️ 开源生态

### DeepSeek 正式开源昇腾基础组件，共建国产 AI 芯片软件生态
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/499263.html)
摘要: 9 月 30 日 DeepSeek 开源面向华为昇腾算力的基础设施组件，包括 DeepGEMM、FlashMLA、TileKernel、DeepSelect 等高性能算子库与 DeepEP 分布式通信库，与此前 GPU 平台开源组件一一对应。华为提供了联合定义的昇腾超节点 SuperPoD Flex 和 UBL128 组网方案，支持 128 卡 3.2Tbps 单层交换 Scale-up 与 256K 卡两层 Scale-out 网络。

## 📰 行业动态

### Anthropic 报告"警告" GLM-5.3，实测数据反成智谱广告
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/499597.html)
摘要: Anthropic 发布关于智谱 GLM-5.3 的安全报告，指其具备较强的漏洞发现与攻击程序编写能力且防滥用限制易被绕过。但报告引用的实测数据引发反向解读：ExploitBench 测试中 GLM-5.3 成功 50 次对比 Claude Mythos Preview 的 56 次，且 NIST 下属 CAISI 评估称 GLM-5.3 是"迄今网络能力最强的开源权重模型，距美国前沿约 4 个月"。核心议题是 Mythos 级能力正在流向开源模型。

### 36 家机器人公司已敲钟：赚钱能力差距巨大，商业化不再玩花架子
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/09/499280.html)
摘要: 宇树登陆科创板、梅卡曼德与优地机器人港交所挂牌后，本末科技、欢创科技 9 月底相继上市，量子位 ROBO 梳理出至少 36 家已上市机器人相关公司。财务差距悬殊：有人形机器人收入占比过半者，也有新业务占比仅万分之几者；有年赚近 3 亿元者，也有收入 20 亿元仍未盈利者。投行消息称监管正在调整部分人形机器人企业的上市节奏，审视标准趋严。

### 个人 AI 助理竞速：Meta、Manus、OpenAI 已下场，字节急追
来源: 36氪
原文: [原文](https://www.36kr.com/p/4005287845173121)
摘要: 36氪梳理个人 AI 助理赛道的竞速格局：Meta、Manus、OpenAI 已先后下场推出产品，字节跳动正在急追，行业将个人 AI 助理视为"下一个超级入口"的争夺焦点。

---

🦞 每日08:00自动更新

**数据来源**：量子位、Google DeepMind、36氪
