---
title: "AI新闻早报 2026-06-11"
date: 2026-06-11T07:20:00+08:00
slug: ai-morning-news-2026-06-11
description: "2026年6月11日 AI 新闻早报，严格采集 06-10 08:00 至 06-11 08:00 窗口，覆盖国家队下场做 AI 虚拟细胞（百曜科技融资）、小鹏机器人核心产品一号位施晓鑫离职、抖音征召 AI 视频英才、Anthropic 推出 Mythos 级 30 天数据保留政策、网络安全研究者不满 Fable 模型护栏、Dario Amodei 谈 AI 指数增长与政治制度脱节、Google 开源扩散语言模型 DiffusionGemma、Apache Burr 进入 Apache 孵化器等关键事件。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "Anthropic", "DarioAmodei", "Google", "DiffusionGemma", "Apache", "Burr", "36kr", "量子位", "抖音", "虚拟细胞", "百曜科技", "小鹏", "机器人", "Mythos", "Fable"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 💰 融资财报

### 国家队下场做 AI 虚拟细胞：「百曜科技」完成数千万元新一轮融资
来源: 36 氪
原文：[原文](https://www.36kr.com/p/3835460873385348)
摘要：AI 虚拟细胞（AIVC）平台公司「百曜科技」已完成数千万元新一轮融资，由国家级国有资本运营平台中国国新旗下的国新创投基金领投，道彤资本、云启资本跟投，老股东峰瑞资本和百度风投追加投资。资金将用于新一代虚拟细胞算法模型迭代、独家数据收集平台建设与产业化加速。「国家队」首度进入 AI for Science 虚拟细胞赛道，标志国资对生命科学大模型路径的认可，与英伟达 BioNeMo、海外 EvolutionaryScale 路线形成对照。

## 🏢 公司动作

### 小鹏机器人核心产品一号位施晓鑫 6 月初主动离职
来源: 36 氪
原文：[原文](https://www.36kr.com/p/3839560961116417)
摘要：职场 Bonus 独家获悉，小鹏机器人产品规划高级总监施晓鑫于 6 月初正式离职。施晓鑫是小鹏人形机器人 Iron 与 PX 系列的产品一号位，主导从概念到工业场景落地的产品路线规划。事件发生在小鹏刚刚发布 Iron 二代并启动工厂实训的窗口期，对一家正全力推进具身智能量产的车企而言，核心产品负责人离场意味着 PX3 / Iron3 节奏需快速完成接班。

### 抖音征召天下「AI 视频英才」：创作者端开启 AI 红利兑现通道
来源：量子位
原文：[原文](https://www.qbitai.com/2026/06/433832.html)
摘要：抖音正式启动面向创作者的「AI 视频英才」扶持计划，将流量、变现工具与 AIGC 创作能力打包下放。文章认为对绝大多数内容创作者来说，这可能是离 AI 红利最近的一次入口。计划重点是降低创作者使用 AI 视频工具的门槛，并把平台流量机制与 AIGC 内容打通，对国内视频生成模型厂商与 MCN 是一次需求侧集中释放。

## 🛡️ 行业政策

### Anthropic 公布 Mythos 级模型 30 天数据保留与安全审查政策
来源：Anthropic 官方
原文：[原文](https://support.claude.com/en/articles/15425996-data-retention-practices-for-mythos-class-models)
摘要：Anthropic 官方支持文档显示，为「负责任地部署 Mythos 级模型」，Mythos-class 模型将实施 30 天的数据保留与人工审查机制，提交至 Mythos 模型的 prompt 与其生成内容均纳入审计范围。Fable 作为 Mythos 的对外受限版本同步沿用该政策。Anthropic 表示这是其 RSP（Responsible Scaling Policy）框架的延续，但对客户侧意味着 Mythos/Fable 的调用日志和提示词会在更长周期内可被调取，企业与开发者需要重新评估合规与数据治理流程。

### Dario Amodei 长文《Policy on the AI Exponential》：呼吁政治体制追上 AI 速度
来源：Dario Amodei 个人博客
原文：[原文](https://darioamodei.com/post/policy-on-the-ai-exponential)
摘要：Anthropic CEO Dario Amodei 发布政策长文，核心论点是 AI 能力正以指数速度前进，但政治制度是「霍比特人级」节奏（以年为单位决策），AI 风险与监管窗口将以月为单位关闭。文章用《指环王》树须（Treebeard）的寓言开篇，呼吁建立专门、能持续学习、足够快的 AI 监管机构，并主张让 AI 能力评估结果「本身也可被 AI 实时审计」。这是 Mythos/Fable 争议之后，Anthropic 管理层首次系统阐述「监管为什么必须追上 AI」的整套框架。

## 🐛 开发者实战

### Claude Desktop 每次启动都拉起 1.8 GB Hyper-V 虚拟机：仅聊天也会触发
来源：GitHub Issue (anthropics/claude-code #29045)
原文：[原文](https://github.com/anthropics/claude-code/issues/29045)
摘要：用户在 anthropics/claude-code 仓库提交 Issue #29045 报告：Claude Desktop 每次启动都会在 Windows 上拉起一个约 1.8 GB 的 Hyper-V 虚拟机进程，即便用户只打算进行纯文本对话、不调用任何代码执行或沙箱功能。该 Issue 在 Hacker News 提交后获得 314 分（提交时 6 小时前），成为当日工程社区对 Claude Desktop 资源开销的最大集中吐槽点。事件反映出 Anthropic 在「默认沙箱 + 跨平台一致」设计与桌面端资源占用之间的取舍冲突，也与 Mythos/Fable 同期「安全收紧」主旋律形成对照。

## ⚠️ 安全与争议

### 网络安全研究者公开不满：Fable 模型护栏让合法研究「无法进行」
来源：TechCrunch
原文：[原文](https://techcrunch.com/2026/06/10/cybersecurity-researchers-arent-happy-about-the-guardrails-on-anthropics-fable/)
摘要：TechCrunch 报道，多位白帽安全研究者公开表达不满：Anthropic 周二发布的 Fable 模型虽然定位为 Mythos 的「公开受限版」，但其默认护栏同样拒绝大多数合法安全研究场景，例如漏洞复现、攻防演练 PoC 生成。研究者在 X 与 HN 上集中吐槽「Fable 把 80% 的研究价值封在拒答里」。事件与 Dario Amodei 当日发布的「AI 指数增长」长文形成正反两面：一边在政策层面呼吁监管速度，一边在产品层面把护栏继续收紧。

## 🛠️ 技术进展

### Google 开源扩散语言模型 DiffusionGemma：26B MoE、4× 文本生成加速
来源：Google 官方博客
原文：[原文](https://blog.google/innovation-and-ai/technology/developers-tools/diffusion-gemma-faster-text-generation/)
摘要：Google 发布实验性开源模型 DiffusionGemma（Apache 2.0），26B 参数的 MoE 架构，首次把「文本扩散」范式带进大模型主流：放弃自回归逐 token 顺序生成，改用并行去噪方式输出文本。官方在专用 GPU 上测得最高 4× 推理加速，并打开本地交互式工作流的新空间。模型当前定位「实验性」，但代表 Google 在扩散语言模型赛道正式下注，与 Inception Labs、Meta LLaDA 的扩散 LLM 路线同台竞争。

### Apache Burr 进入 Apache 孵化器：纯 Python 构建可靠 AI Agent
来源：Apache 软件基金会
原文：[原文](https://burr.apache.org/)
摘要：Apache Burr（Incubating）由 Apache 软件基金会孵化，定位「让任何人都能构建可靠的 AI 应用」，从简单聊天机器人到多智能体系统均可基于其可组合接口开发，纯 Python 实现、无黑盒魔法。文档展示了状态机式的 Agent 设计、决策可观测性与人类在环回退机制，正好回应了过去一年企业部署 AI Agent 普遍遇到的「跑得起来、跑得稳、跑得可控」难题。Burr 进入孵化器意味着 Apache 生态对 Agent 框架的标准制定已经起步。

---

🦞 每日08:00自动更新

**数据来源**：36 氪、量子位、Anthropic 官方支持文档、Dario Amodei 博客、TechCrunch、Google 官方博客、Apache 软件基金会
