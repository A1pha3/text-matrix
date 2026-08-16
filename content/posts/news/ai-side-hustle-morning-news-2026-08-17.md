---
title: "AI副业早报 2026-08-17"
date: 2026-08-17T07:12:50+08:00
slug: ai-side-hustle-morning-news-2026-08-17
description: "2026年8月17日 AI 副业早报，精选过去 24 小时内 DeepSeek Harness 生态的开源插件与编排引擎、Agent 目录站、Amazon AI 生图工具、Codex 浏览器插件平替与原生 macOS 视频客户端等可落地的独立开发机会。"
draft: false
categories: ["行业快讯"]
tags: ["AI副业", "独立开发", "V2EX", "DeepSeek", "Agent"]
hiddenFromHomePage: true
---

🦞 每日07:15自动更新

---

## 🔥 今日热门

### 独立开发者给 DeepSeek Harness 写了插件 DAG 编排引擎：可视化拖拽解决 preset YAML 难维护问题
来源: V2EX
发布者: darrenlopez
原文: [原文](https://www.v2ex.com/t/1234808)
摘要: 开发者注意到 DeepSeek Harness（dsh）上线几天内 GitHub 几万的星，催生插件市场、Awesome 列表、桌面壳，但所有工具都停在"帮你找插件"，真正组装 Agent 仍要手写 YAML preset（声明模型、工具、skill、事件钩子）。他为此做了一个可视化编排扩展：从节点库拖出积木、连线表达依赖、填参数即可保存为 preset。连线即显式依赖，未连线的部分交给 Cordis 依赖注入自动装配，连成环时直接报错回退；任何发布 Cordis service 的插件会自动包进隔离 realm，避免 preset 被拒。对想做"给开源 Agent 框架做编辑器"或"为 DSL/Harness 生态配套可视化工具"的副业开发者，这条路径示范了"用户痛点是配置难、而你交付的不是 AI 而是编辑器"的非典型 AI 副业切入点。

### AgentStackMap：按"你能用 Agent 干的活"重新分类，解决主流 Agent 目录只收 GitHub 或只收付费产品的偏差
来源: V2EX
发布者: chatbase
原文: [原文](https://www.v2ex.com/t/1234805)
摘要: AgentStackMap 把 Agent 产品按"助理 / 编程 / 设计 / 研究 / 自动化 / 业务"六类组织，每条卡片标注是否开源、是否有免费计划，搜名字或从手头任务入口点进即可直达官网。它明确点出现有 Agent 目录的两个偏差——只收 GitHub 仓库会漏掉 Cursor、Harvey、Sierra，只收付费产品又像广告。对想做"AI 工具导购站 / 评测站 / 流量站"但又不想做 Notion 二手目录的副业团队，这条产品示范了"任务为锚的目录结构"如何与传统 feature 列表差异化，后续作者计划出技术栈全景图，可作为流量入口的延伸方向。

### 中学生实验仿真平台 harnessLab：用 deep agents 重写 AI 模块，求社区试用与远程岗位
来源: V2EX
发布者: michelleGoGo
原文: [原文](https://www.v2ex.com/t/1234789)
摘要: 开发者将去年 vibe coding 项目的 AI 模块用 deep agents 重构，新增多租户隔离与会话历史持久化，提供 20 credits / 天的免费额度（harnesslab.onrender.com）。帖内同时公布其独立开发远程模式已结束，希望寻找远程或线下的 AI 全栈 / Agent 应用开发岗位，并附 GitHub（ladycui）。对其他独立开发者而言，这条帖子的价值在于它示范了一种"把项目开放试用 + 求职"两件事在 V2EX 一并完成的打法——项目本身既是作品集，又能拿到真实用户反馈，是兼顾求职与持续运营的低成本路径。

---

## 🛠️ AI 工具与副业机会

### Amazon Listing AI 生图工具：可先审方案再出图，面向跨境电商副业场景
来源: V2EX
发布者: h2mxxy
原文: [原文](https://www.v2ex.com/t/1234814)
摘要: 开发者做了一款面向 Amazon Listing 的 AI 生图工具，特色是"先审方案再出图"——卖家或服务商可在生成前先选风格 / 构图 / 文案方案，确认后再批量出图，省去反复调整的迭代成本。原文未列出技术栈，但从目标用户（Amazon 卖家、独立站运营）和工作流（多步审稿）判断，是典型的"垂直电商 × AI 提效"组合。对面向跨境电商做工具型副业、熟悉 Amazon Listing 规范但不想碰底层模型的开发者，这是一条"小而专、可收费、可复购"的方向。

### open-web-bridge：Codex 浏览器插件平替，能在 OpenCode 等 harness 中无缝接入
来源: V2EX
发布者: woniu9527
原文: [原文](https://www.v2ex.com/t/1234823)
摘要: open-web-bridge 是一个为 opencode 这类 harness 补上浏览器能力的 CLI 工具，能力对齐 Codex 自带的 Chrome 插件，且多了几样官方不能做、playwright 类方案做不好的事——尤其是不丢登录态、风控更轻。开发者明确对比了 playwright、cloakbrowser、camoufox 等反检测路线，指出真实浏览器里装一个野生插件在"保持登录态 + 弱风控"上仍是当前最优解。对做 Agent harness 周边配套、做 opencode 生态插件市场的副业开发者，这是一个清晰的"补缺型"工具切入点。

### 原生 macOS 视频客户端 OKVideoMac：作者首次开源分享 Native-first + Android Bridge 实现
来源: V2EX
发布者: linyao2010
原文: [原文](https://www.v2ex.com/t/1234829)
摘要: OKVideoMac 0.3.41（Build 64）是一款 macOS 原生视频客户端，作者今天首次开源（GitHub: yaolin-dev/OKVideoMac，提供 arm64 DMG 下载）。项目亮点是 Native-first + Android Bridge 实现路径——即把 macOS 原生端作为核心体验层，再以 Android Bridge 形式复用移动端能力。这条帖子的副业参考价值在"如何低成本起步一款 macOS 工具"——开发者没有选择 Electron，而是直接做原生，意味着上手门槛更高但用户口碑更好；对拥有 macOS / iOS 开发能力的副业者，原生客户端仍是变现稳定性最高的形态之一。

### 独立开发「图片转 AI 绘画 Prompt」工具，欢迎体验
来源: V2EX
发布者: weijiejason119
原文: [原文](https://www.v2ex.com/t/1234790)
摘要: 一款把图片反向解析成 AI 绘画 Prompt 的小工具，独立开发者公开求体验。功能定位介于"逆向 prompt 工程"与"普通图像识别工具"之间，目标用户是 Midjourney / Stable Diffusion / ComfyUI 等创作链路的从业者。对副业者来说，这是一条典型的"小工具冷启动 + V2EX 求反馈 + 后续可接 Midjourney API / Prompt 模板订阅"的低风险路径。

---

## 🚀 副业生态周边

### 鲸鱼娘皮肤上榜 Awesome DeepSeek Harness：DSH 插件生态两天内催生 100+ 项目
来源: V2EX
发布者: fendouai_com
原文: [原文](https://www.v2ex.com/t/1234796)
摘要: DeepSeek Harness 上线几天后，社区已经形成完整的生态飞轮：dsh-deep-whale 鲸鱼娘皮肤、DSH Web UI 大型插件与皮肤集合、Awesome DeepSeek Harness 排行榜，附 trending 排序。作者原意是整理编程和文档向的工具，结果意外发现皮肤系列（fendouai/awesome-deepseek-harness）。对所有正在做开源 AI 工具框架的副业者，这条信息是一份"项目冷启动后生态如何自然外溢"的样本——插件市场、Awesome 列表、皮肤主题、排行站都是自发涌现的二次机会。

---

🦞 每日07:15自动更新

**数据来源**：V2EX 创意（?tab=creative）

**⚠️ 链接核查清单（已逐条验证，仅列正文实际引用链接）：**
- ✅ https://www.v2ex.com/t/1234808 - DeepSeek Harness DAG 编排引擎
- ✅ https://www.v2ex.com/t/1234805 - AgentStackMap Agent 目录
- ✅ https://www.v2ex.com/t/1234789 - harnessLab 中学生实验仿真
- ✅ https://www.v2ex.com/t/1234814 - Amazon Listing AI 生图工具
- ✅ https://www.v2ex.com/t/1234823 - open-web-bridge 浏览器插件平替
- ✅ https://www.v2ex.com/t/1234829 - OKVideoMac 原生 macOS 视频客户端
- ✅ https://www.v2ex.com/t/1234790 - 图片转 AI 绘画 Prompt 工具
- ✅ https://www.v2ex.com/t/1234796 - Awesome DeepSeek Harness 生态