---
title: "AI新闻早报 2026-07-06"
date: 2026-07-06T07:26:21+08:00
slug: ai-morning-news-2026-07-06
description: "2026年7月6日 AI 新闻早报，覆盖 7 月 5 日 Codex 与 ChatGPT 整合、Cloudflare 默认屏蔽 AI 爬虫、汽车 Tier1 涌入人形机器人、海外开发者报告 GPT-5.5 Codex 推理聚簇异常与 Anthropic 新模型工具调用稳定性下降。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "模型评测", "Cloudflare", "具身智能", "Codex"]
hiddenFromHomePage: true
---

🦞 每日08:00自动更新

---

## 🚀 产品发布

### OpenAI Codex 与 ChatGPT 合并，周活突破 500 万
来源: 36氪（机器之心）
原文: [原文](https://www.36kr.com/p/3882258709180678)
摘要: Codex 桌面应用团队负责人 Andrew Ambrosino 在访谈中披露，Codex 周活用户自 1 月起增长超过 5 倍，规模已达 500 万，其中知识工作者的采用速度是开发者的 3 倍以上；2 月上线的桌面 App 是关键转折点。他同时解释了 Codex 与 ChatGPT 合并的原因：当实现变得便宜，"品味"和策展成为组织最贵的部分，未来 Codex 将更多围绕工作流而非纯写代码迭代。

## 🛡️ 行业监管

### Cloudflare 默认屏蔽混合用途 AI 爬虫，9 月 15 日生效
来源: 36氪（极客公园）
原文: [原文](https://www.36kr.com/p/3882226982842376)
摘要: Cloudflare 宣布自 9 月 15 日起，所有使用其服务的网站默认屏蔽混合用途 AI 爬虫，广告页面上的训练爬虫和 Agent 爬虫都无法访问，除非站长手动开启。这一变化背景是互联网 bot 流量已超过人类流量。同时，Cloudflare 把 AI 爬虫拆成 Search / Agent / Training 三类独立管理，并升级 "Pay Per Use" 模式，从按爬取次数收费转向按内容真正被用于回答时收费，合作伙伴包括 Ceramic.ai 与 You.com。

## 🔬 技术进展

### 模型评测从"知识考试"转向"岗位考核"
来源: 36氪（奇点湃）
原文: [原文](https://www.36kr.com/p/3882467938040710)
摘要: 文章观察第一代 AI 公司的竞争标准正从 MMLU、HumanEval 等 Benchmark 向 SWE Bench、BrowserComp、Terminal Bench、OSWorld 等"任务完成"指标迁移。当模型能力逐渐趋同，企业采购更关心能否修 Bug、完成网页操作、调用内部系统。文中以 MiniMax M3 为例，分析 AI 公司收入单位正在从 Token 转向 Workflow，并指出这是行业层面从 Intelligence 商业化到 Task Completion 商业化的拐点。

### GPT-5.5 Codex 用户报告推理 token 固定聚簇在 516/1034/1552
来源: Hacker News（OpenAI Codex issue）
原文: [原文](https://github.com/openai/codex/issues/30364)
摘要: 用户 vguptaa45 在 OpenAI Codex 仓库提交 issue，统计了 Feb-Jun 2026 的 token_count 元数据，发现 GPT-5.5 响应异常聚集在 reasoning_output_tokens=516，并在 1034 与 1552 出现次级峰值，与复杂任务上 Codex 表现下降的时间段高度重合。同一用户之前在 #29353 中给出单点复现：跑分恰好停在 516 时返回错误答案。结论是这与"受限推理预算"行为高度一致，作者未直接断言截断，但建议模型侧复盘推理 token 的阈值设计。

## 🐛 模型稳定性

### Anthropic 新模型工具调用错误率上升，旧模型反而更稳
来源: Hacker News（Armin Ronacher 博客）
原文: [原文](https://lucumr.pocoo.org/2026/7/4/better-models-worse-tools/)
摘要: Flask 作者 Armin Ronacher 在博客中实测，Opus 4.8 与 Sonnet 5 等较新 Anthropic 模型在调用 Pi 编辑工具时，会向 `edits[]` 数组追加 schema 中不存在的键（type / id / kind / requireUnique 等），导致 Pi 拒绝调用并要求重试。Haiku 等小模型和旧版本都没有这个问题。Ronacher 认为这是模型在没有 grammar-aware constrained decoding 时凭"学到的约定"生成 JSON 出现的退化，工具调用稳定性需要重新作为一等公民评估。

## 🤖 具身智能

### 汽车零部件 Tier1 集体涌入人形机器人赛道
来源: 36氪（汽车公社）
原文: [原文](https://www.36kr.com/p/3882021170589699)
摘要: 摩根士丹利预测 2050 年全球人形机器人保有量将达 10 亿台、市场规模 7.5 万亿美元。德国舍弗勒已与 Neura、Hexagon Robotics 合作并入股英国 Humanoid，计划 5-6 年内自有工厂部署千台人形机器人；大陆集团子公司欧摩威为 Mobileye 收购的 Mentee Robotics 生产整机，成为首家切入人形机器人代工的国际 Tier1；博世也在今年初与 Neura Robotics 合作。三花智控等中国 Tier1 把汽车热管理与机电执行器经验复制到旋转执行器、灵巧手等机器人部件。

## 🔒 安全与运维

### Claude Code Enterprise ZDR 工作区被报告出现 session/cache 泄漏
来源: Hacker News（Anthropic Claude Code issue）
原文: [原文](https://github.com/anthropics/claude-code/issues/74066)
摘要: 用户 milesrichardson-edb 在企业 Zero Data Retention 工作区提交 bug：Claude Code 在某次会话中突然开始询问 Minecraft 神庙的砖块类型，并自信地在总结里说自己在搭建 Minecraft 神庙。提交者怀疑是同事账号或 consumer plan 的缓存污染到了企业会话，并把所有"早期污染"作为工作上下文继续使用。issue 引发大量共鸣并已被官方标为 Open。

---

🦞 每日08:00自动更新

**数据来源**：36氪、Hacker News（Armin Ronacher 博客、OpenAI Codex issue、Anthropic Claude Code issue）
