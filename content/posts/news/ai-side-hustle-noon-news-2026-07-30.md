---
title: "AI副业午报 2026-07-30"
date: 2026-07-30T12:00:00+08:00
slug: ai-side-hustle-noon-news-2026-07-30
description: "2026年7月30日 AI 副业午报，精选过去 24 小时内西安移山科技 AI 应用工程师招聘、深圳 AI 美企全栈岗、程序员副业睡后收入讨论、AgentMicro 开源 Codex 菜单栏工具、用 AI 重做用户反馈挂件 side project、跨 Agent 管理 skill 讨论、Agent/Harness 岗位转型、本月 AI 花费盘点、LLM Honeypot 工具、AI 头部创业公司研究发表锐减、HuggingFace Agent 入侵事件技术复盘等真实公开案例。"
draft: false
categories: ["行业快讯"]
tags: ["AI副业", "招聘", "Agent", "独立开发", "AI工具"]
hiddenFromHomePage: true
---

🦞 每日11:00自动更新

---

## 🏢 AI 核心岗位招聘

### [西安/全职] 移山科技招 2 位 AI 应用工程师：必须用 AI，Token 不限量，不限技术栈

来源: V2EX 酷工作
发布者: Elatlas
原文: [原文](https://www.v2ex.com/t/1231065)
摘要: 西安移山科技（GEO 产品方向）扩招两位 AI 应用工程师。核心岗位为 AI 应用核心工程师（GEO 方向），12-20K；以及 AI 应用工程师（成长型），8-12K。工作地点在碑林区永宁门地铁站，全职现场办公。业务核心是 GEO（生成引擎优化）——让品牌在 DeepSeek、豆包、Kimi 等模型的回答中被提到、引用和推荐。技术栈涉及多模型调用、非结构化数据清洗、RAG 与知识图谱、自动化评估等。团队强调"必须用 AI，Token 不限量"，是传统 SEO 向 AI 时代 GEO 转型的典型岗位机会。

### 深圳南山 AI 美企招 infra/后端全栈工程师，28-35K

来源: V2EX 酷工作
发布者: kuls
原文: [原文](https://www.v2ex.com/t/1231044)
摘要: 深圳 AI 美企招聘平台基础设施全栈工程师，薪资 28-35K，简历直达 team lead。核心职责包括平台化基础设施架构设计、后端微服务开发（用户/鉴权、credits/计费、支付风控、模型集成等），要求精通 Node.js + TypeScript + Next.js（App Router），有云原生部署经验（GCP/AWS/Azure）。岗位强调高并发生成场景下的稳定性保障（限流、熔断、降级），是"AI 产品商业化阶段"的基础设施核心岗位，适合有平台化思维和微服务实战经验的全栈开发者。

## 💼 程序员副业 / 职业转型

### 程序员副业讨论：聊聊大家的睡后收入怎么实现

来源: V2EX 问与答
发布者: JiFengs
原文: [原文](https://www.v2ex.com/t/1231056)
摘要: 楼主发起"程序员副业和睡后收入"话题讨论，已有 9 条回复、404 次浏览。帖子面向程序员群体征集真实副业案例，讨论方向覆盖工具类 SaaS、内容创作、独立产品、投资等路径。这类讨论通常能沉淀出大量真实变现经验，是了解国内程序员群体"主业之外第二收入"现状的窗口，对评估 AI 时代副业方向有参考价值。

### 从 Java 后端转 Agent/Harness 开发，实际工作内容和能力要求是什么？

来源: V2EX 职场话题
发布者: casperZhao
原文: [原文](https://www.v2ex.com/t/1231022)
摘要: 楼主正在学习 Agent 原理，计划从 Java 后端转向 Agent/Harness 开发，向社区请教日常实际工作内容、需要具备的技术能力和非技术素质。帖子已有 612 次浏览，是当下"传统后端工程师向 AI Agent 方向转型"的典型提问，评论区的经验分享对评估 Agent 岗位真实门槛有直接参考价值。

## 🚀 独立开发者 / 开源项目

### 开源分享：AgentMicro — 把并行 Codex 任务放进 macOS 菜单栏

来源: V2EX 分享创造
发布者: fizzy798
原文: [原文](https://www.v2ex.com/t/1231055)
摘要: 开发者 fizzy798 发布 AgentMicro V1，一款 macOS 菜单栏应用（Swift 6 + macOS 14+），用于监控并行 Codex 任务状态。核心设计理念是"只做观察与跳转，不做任务管理器"，五种固定状态（空闲、未读、思考、需处理、错误），菜单栏六格图标同步前六个任务并轻微呼吸。完全本地、只读，不上传任务内容，不需要 Full Disk Access。对同时使用多个 AI Coding Agent 的独立开发者是实用工具，也是"小切口解决具体痛点"的独立开发范例。

### 用 AI 重做一遍：一个收集用户反馈的网页挂件 side project

来源: V2EX 分享创造
发布者: paicha
原文: [原文](https://www.v2ex.com/t/1231049)
摘要: 开发者 paicha 发布团队首个 side project「Make This Better」（makethisbetter.dev），一套收集和处理用户反馈的 Agent 工作流，包含 Widget、CLI、MCP、Skill。用户在网页提交反馈后，AI 进行需求分析，本地 coding agent 接手处理，全程不碰数据和代码。前端 Widget 开源，支持 BYOK（自带 Key）和个人免费使用。项目已帮助团队处理大量用户反馈并发现新需求，是"用 AI 重做传统需求"的典型独立项目案例。

### 在 AI Coding 时候跨多 Agent，如何管理 Skill？

来源: V2EX 问与答
发布者: kuhung
原文: [原文](https://www.v2ex.com/t/1231026)
摘要: 楼主提出"跨 Claude、Codex、Cursor 管理 Skill 的痛点"：在不同 Agent 间生成的 skill 复用时需要手动迁移，目前缺少统一管理方案。帖子征集社区对 Skill 管理工具和心得的推荐，反映了 AI Coding 生态中"Agent 间资产互通"这一新兴需求，对独立开发者和 AI 工具方向有启发意义。

## 🌐 全球 AI 动态

### AI 头部创业公司几乎不再发表研究论文

来源: Hacker News / Science.org
发布者: YeGoblynQueenne
原文: [原文](https://www.science.org/content/article/ai-s-top-startups-are-barely-publishing-their-research)
摘要: Science 杂志发文分析指出，AI 头部创业公司（如 OpenAI、Anthropic 等）的研究论文发表数量急剧下降，与开源社区的期望形成鲜明对比。HN 上获得 519 points 和 266 条评论，引发关于"AI 研究封闭化趋势"和"商业利益与学术开放之间矛盾"的广泛讨论。对关注 AI 行业走向独立开发者，理解行业开放生态变化有参考意义。

### HuggingFace 复盘：2026年7月前沿实验室 Agent 入侵事件技术时间线

来源: Hacker News / HuggingFace Blog
发布者: artninja1988
原文: [原文](https://huggingface.co/blog/agent-intrusion-technical-timeline)
摘要: HuggingFace 发布技术博客，详细复盘 2026 年 7 月发生的"前沿实验室 Agent 入侵事件"完整时间线。文章从技术角度还原了 Agent 系统被入侵的各个环节，包括漏洞利用路径、数据泄露范围和安全改进措施。HN 上获得 411 points 和 224 条评论，是 AI Agent 安全领域的标志性事件复盘，对从事 Agent 开发和安全研究的团队有重要参考价值。

### LLM Honeypot：检测大语言模型生成的"蜜罐"工具

来源: Hacker News
发布者: 8thom
原文: [原文](https://llm2human.pages.dev/)
摘要: LLM Honeypot 是一款用于检测文本是否由大语言模型生成的在线工具，以复古网页风格呈现。HN 上获得 300 points 和 88 条评论，讨论涵盖了 AI 内容检测的技术可行性、误判率问题和实际应用场景。对关注 AI 内容审核、反作弊和 Prompt 工程的开发者具备参考价值。

## 💡 AI 使用成本 / 社区讨论

### 这个月你们都花了多少钱给 AI？

来源: V2EX 人工智能
发布者: wuxinling
原文: [原文](https://www.v2ex.com/t/1231037)
摘要: 月底 AI 花费盘点帖，楼主分享自己在 DeepSeek 上花了 15 元，认为产出对得起工资。帖子已有 16 条回复、555 次浏览，讨论覆盖了不同 AI 工具的使用成本（ChatGPT Plus、Claude Pro、Cursor、API 调用等）和性价比评估。对评估"AI 工具个人订阅 ROI"和"企业 AI 成本管理"有一手参考价值，也是观察国内开发者 AI 使用习惯的窗口。

---

🦞 每日11:00自动更新

**数据来源**：V2EX（酷工作、问与答、分享创造、职场话题、人工智能节点）、Hacker News

**⚠️ 链接核查清单（仅列正文实际引用链接）：**
- ✅ https://www.v2ex.com/t/1231065 - 西安移山科技 AI 应用工程师招聘
- ✅ https://www.v2ex.com/t/1231044 - 深圳南山 AI 美企全栈工程师招聘
- ✅ https://www.v2ex.com/t/1231056 - 程序员副业睡后收入讨论
- ✅ https://www.v2ex.com/t/1231022 - Java 后端转 Agent/Harness 开发讨论
- ✅ https://www.v2ex.com/t/1231055 - AgentMicro 开源 Codex 菜单栏工具
- ✅ https://www.v2ex.com/t/1231049 - 用 AI 重做用户反馈挂件 side project
- ✅ https://www.v2ex.com/t/1231026 - 跨 Agent 管理 Skill 讨论
- ✅ https://www.science.org/content/article/ai-s-top-startups-are-barely-publishing-their-research - AI 创业公司研究发表减少
- ✅ https://huggingface.co/blog/agent-intrusion-technical-timeline - HuggingFace Agent 入侵事件复盘
- ✅ https://llm2human.pages.dev/ - LLM Honeypot 工具
- ✅ https://www.v2ex.com/t/1231037 - 这个月 AI 花费盘点
