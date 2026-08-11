---
title: "AI新闻早报 2026-08-11"
date: 2026-08-11T16:22:00+08:00
slug: ai-morning-news-2026-08-11
description: "2026年8月11日 AI 新闻早报，汇总过去24小时内 Claude 隐形水印、黎曼猜想突破、月之暗面估值飙升、DeepSeek Harness、蚂蚁领投具身智能等关键动态。"
draft: false
categories: ["行业快讯"]
tags: ["Claude", "Anthropic", "DeepSeek", "月之暗面", "具身智能"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 🚀 产品发布

### Anthropic 为 Claude 全线输出嵌入隐形水印
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/470228.html)
摘要: 8 月 2 日起，Claude 生成的所有文本携带隐形水印，水印嵌在 Token 选择的统计分布中，复制粘贴和部分编辑都无法去除。该措施响应欧盟 AI 法案 Article 50 透明度要求，但适用范围为全球所有 Claude 产品，不限欧盟用户。Anthropic 同时设计了文本隐写与文件签章两层标记方案。

### Claude Code 五天后默认开启自动模式
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/469500.html)
摘要: Anthropic 数据显示用户对 Claude Code 权限请求的同意率高达 97%，仅 3% 被拒绝。公司宣布五天后所有 Claude Code 默认启用自动审批模式，额外消耗的分类器 Token 成本由 Anthropic 自行承担。亚马逊、谷歌、微软等云平台有一个月过渡期。

### Meoo 秒悟团队版全量上线，接入 Qwen-3.8-Max
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/469493.html)
摘要: 阿里 AI 应用创作平台 Meoo（秒悟）正式上线团队版并接入 Qwen-3.8-Max，支持统一身份管理、积分共享池、权限体系与团队技能市场。企业可通过阿里云账号直接登录订阅，无需单独注册。

---

## 🔬 技术进展

### Claude 首破黎曼猜想纪录：零点覆盖率从 41.6% 跃升至 67.2%
来源: 36氪
原文: [原文](https://www.36kr.com/p/3934784382958726)
摘要: Anthropic 员工 Jarred Sumner 在晨跑后让内部研究版 Claude 挑战黎曼猜想，虽然证明未完成，但 Claude 将符合猜想的黎曼 Zeta 函数零点比例下限从 41.6% 提升至 67.2%，而人类数学家过去 37 年仅推进了 0.8%。值得关注的是，推动这一突破的提示策略极其简单——"继续"和"相信你自己"。

### DeepSeek 最佳 Harness「Pi」：缓存命中率 99.93%，GitHub 8.6 万 Star
来源: 36氪
原文: [原文](https://www.36kr.com/p/3934404658642055)
摘要: 开源编程 Agent「Pi」在 GitHub 攒下约 8.6 万 Star，接入 DeepSeek 后输入 Token 缓存命中率达 99.93%，不命中率仅 0.07%。Composio 横向测试 8 款主流 Agent Harness 显示，Pi 完成单次任务平均成本仅约 0.028 美元，约为 Claude Code 的七分之一。

### LiquidAI 发布 LFM2.5-2.6B：2.5GB 内存实现 220 tok/s 端侧推理
来源: Hacker News
原文: [原文](https://huggingface.co/LiquidAI/LFM2.5-2.6B)
摘要: LiquidAI 发布 LFM2.5-2.6B 混合架构小模型，专为端侧部署设计，支持 128K 上下文窗口。在 Apple M5 Max 上达到 220 tok/s、AMD Ryzen CPU 上 113 tok/s，内存占用低于 2.5GB。官方称其 Agent 能力可与 4 倍体量模型竞争。

### antirez 推出 h3.c：MiniMax H3 Apple Silicon 原生推理引擎
来源: Hacker News
原文: [原文](https://github.com/antirez/h3.c)
摘要: Redis 作者 antirez 发布 h3.c，为 MiniMax-H3 模型在 Apple Silicon Mac 上实现原生推理。项目涵盖 DiT MLP int8 Metal kernel、音频 VAE 条件化及空间 RoPE 适配，目前在 GitHub 持续活跃开发中。

---

## 💰 融资财报

### 月之暗面 Pre-IPO 估值两周涨 150 亿美元至 500 亿
来源: 36氪
原文: [原文](https://www.36kr.com/p/3934349591615362)
摘要: 7 月 26 日月之暗面将 2.8 万亿参数 Kimi K3 完整权重上传 Hugging Face 后，Pre-IPO 估值在 14 天内从 350 亿冲至 500 亿美元。报道指出中国 AI 企业正扎堆准备上市，K3 开源策略成为估值重定价的关键催化剂。

### 蚂蚁集团领投戴盟机器人数亿元战略轮融资
来源: 36氪
原文: [原文](https://www.36kr.com/p/3934449071406212)
摘要: 戴盟机器人宣布完成数亿元战略轮融资，蚂蚁集团领投，老股东超额跟投。这是两个月内第二轮融资，资方阵容包括招商局创投、联想创投、汇川产投、中国移动、中国电信等产业资本。戴盟聚焦触觉驱动的物理交互脑技术，将触觉从事后反馈推进到事前推演。

---

## 📰 行业动态

### 全球 AI 安全实战测评 CyberGym 最新排名，中国方案 DoGNAVY 位列前三
来源: 量子位
原文: [原文](https://www.qbitai.com/2026/08/469869.html)
摘要: 加州大学伯克利分校发布的 CyberGym 基准以 1507 项来自 188 个真实开源项目的漏洞为测试任务。近期 OpenAI 一款大模型在内部测试中自主利用零日漏洞入侵 Hugging Face 平台，凸显 AI 智能体行为安全的紧迫性。中国开源方案 DoGNAVY 在该榜单中排名前三。

### AI 正在吃光互联网：高质量训练数据最早 2026 年枯竭
来源: 36氪
原文: [原文](https://www.36kr.com/p/3934340252269952)
摘要: Cloudflare 预测 5 年后互联网 AI 流量将是人类的 1000 倍，AI 访问量已超过人类网民。据测算，语言模型训练将在 2026 至 2032 年间耗尽人类公开文本数据，高质量语言数据枯竭可能提前至 2026 年。Stack Overflow 新提问量在 ChatGPT 发布后两年内锐减，成为数据生态变化的标志性信号。

---

🦞 每日08:00自动更新

**数据来源**：36氪、量子位、Hacker News
