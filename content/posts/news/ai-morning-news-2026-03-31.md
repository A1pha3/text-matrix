---
title: "AI新闻早报：2026年3月31日"
date: "2026-03-31T08:00:00+08:00"
slug: ai-morning-news-2026-03-31
description: "AI新闻早报——每日08:00自动更新。今日要点：阿里千问上线Qwen3.6系列全模态模型、美团开源LongCat-AudioDiT、GitHub遭遇投毒攻击、Mistral AI融资8.3亿美元。"
draft: false
categories: ["行业快讯"]
tags: ["AI", "Qwen", "Claude", "Kimi", "Mistral", "GitHub", "开源", "大模型"]
hiddenFromHomePage: true
---

# AI新闻早报：2026年3月31日

采集时间：2026-03-31 08:47 | 来源：36kr + 量子位 + 橘鸦AI早报 + Reddit | ⚠️ 本期内容经过严格核实

---

## 🤖 模型发布（5条）

### 1. 阿里千问上线 Qwen3.6 Plus Preview

阿里千问在 OpenRouter 上线 Qwen3.6 Plus Preview 模型，支持百万上下文，在 Agentic coding、前端开发及复杂问题解决上表现优异。[原文](https://openrouter.ai/qwen/qwen3.6-plus-preview)

### 2. 阿里千问发布 Qwen3.5-Omni 全模态系列

阿里千问发布 Qwen3.5-Omni 系列，包含 Plus、Flash、Light 三种尺寸。原生支持文本/图片/音频/音视频理解，支持 113 种语音交互，单轮可处理 3 小时音频或 1 小时 720P 音视频。[原文](https://qwen.ai/blog?id=qwen3.5-omni)

### 3. 美团龙猫开源 LongCat-AudioDiT

美团龙猫团队发布 TTS 模型 LongCat-AudioDiT，提供 1B 和 3.5B 两种规格。直接在波形潜空间运行，支持高保真中英双语音频生成。在 Seed 基准测试中实现 SOTA 零样本语音克隆性能。[原文](https://github.com/meituan-longcat/LongCat-AudioDiT)

### 4. 爱诗科技发布 PixVerse V6

爱诗科技发布全新视频模型 PixVerse V6，几十秒内生成 1080P 电影级视频，实现复杂特效与镜头叙事。支持 2-15 人团队协作、共享积分池、角色权限管理。[原文](https://x.com/PixVerse_/status/2038711108119281671)

### 5. 微软发布 Harrier-OSS-v1 多语言嵌入模型

微软发布 Harrier-OSS-v1 多语言文本嵌入模型系列，包含 270M、0.6B、27B 三种规格。采用 Decoder-only 架构，支持 32k 上下文窗口，可广泛应用于检索、聚类、语义相似度计算等任务。[原文](https://huggingface.co/microsoft/harrier-oss-v1-27b)

---

## 💻 开发生态（6条）

### 6. Kimi 会员计费体系调整为统一额度

月之暗面将 Kimi 会员各功能独立计次调整为基于实际 token 消耗的统一额度跨功能共享机制，覆盖 Agent、编程、图片生成等全部会员权益。现有会员权益自动等价迁移。[原文](https://www.kimi.com/membership-credits)

### 7. Claude Code 上线 Computer Use

Claude Code 面向 macOS 平台 Pro 和 Max 用户推出 Computer Use 研究预览版，允许通过 CLI 控制屏幕、点击界面完成端到端 GUI 测试。同时全面支持 GitHub Enterprise Server。[原文](https://code.claude.com/docs/en/computer-use)

### 8. Claude Code 高阶功能开发者分享

Claude Code 开发者 Boris Cherny 分享一系列高阶冷门功能：loop 和 schedule 命令实现长达一周的任务自动化；batch 命令结合 git worktrees 将大规模代码迁移分发给成百上千个并行 Agent 处理；--bare 参数实现最高 10 倍 SDK 启动加速。[原文](https://x.com/bcherny/status/2038454336355999749)

### 9. OpenAI 发布 Codex 插件

OpenAI 为 Claude Code 打造插件 codex-plugin-cc，允许在 Claude Code 中调用 Codex 进行代码审查或任务接管。提供标准审查、对抗性审查和任务移交三大核心功能。[原文](https://github.com/openai/codex-plugin-cc)

### 10. Hermes Agent 新增 Multi Agent Profiles

Nous Research 推出 Hermes Agent 重大更新：Multi Agent Profiles。允许在同一机器运行多个完全隔离的 Agent，各自拥有独立配置、API 密钥及记忆。执行 hermes update 即可获取。[原文](https://hermes-agent.nousresearch.com/docs/user-guide/profiles/)

### 11. 企业微信开源 wecom-cli

企业微信开源命令行工具 wecom-cli，支持 AI Agent 直接通过终端操作企业微信核心业务。覆盖通讯录、会议、消息、日程、文档等 7 大业务品类，预置 12 个开箱即用 Agent Skills。[原文](https://github.com/WecomTeam/wecom-cli)

---

## 🚀 产品应用（2条）

### 12. 智谱 Z.ai Chat 支持一键接入飞书和微信

智谱 Z.ai Chat 更新，Agent 模式支持用户免费一键接入飞书和微信的 ClawBot。海外用户还支持接入其他聊天工具。[原文](https://chat.z.ai)

### 13. Microsoft 365 Copilot 引入 Critique 多模型能力

Microsoft 365 Copilot 研究 Agent 引入 Critique 和 Council 两项多模型能力。Critique 通过分离生成与评估环节，结合 Anthropic 和 OpenAI 不同模型形成反馈循环优化报告。在 DRACO 基准测试中，集成 Critique 的 Researcher 比 Perplexity Deep Research 高出约 13.88%。[原文](https://techcommunity.microsoft.com/blog/microsoft365copilotblog/introducing-multi-model-intelligence-in-researcher/4506011)

---

## ⚠️ 行业动态（2条）

### 14. GitHub 遭遇投毒攻击

2026年3月29-30日，GitHub 遭遇有组织大规模垃圾信息投毒攻击。攻击者在 WSL、isce-framework/isce2 等数百个知名开源项目中创建超过 20 万个赌博与成人内容垃圾 Issue，攻击速率高达每秒 20 条。WSL 项目 Issue 编号从 #14575 激增至 #40028。[原文](https://github.com/microsoft/WSL/issues/40028)

### 15. Mistral AI 融资 8.3 亿美元

法国 AI 实验室 Mistral AI 完成 8.3 亿美元首次债务融资，用于在巴黎南部建设 44 兆瓦数据中心，部署 13800 块 Nvidia GB300 GPU。预计 2026 年 Q2 末投入运营。[原文](https://www.reuters.com/business/finance/frances-mistral-raises-830-million-debt-ai-data-centre-build-up-2026-03-30/)

---

## 📰 来源

- [36kr AI](https://www.36kr.com/information/AI/)
- [量子位](https://www.qbitai.com/)
- [橘鸦AI早报](https://mp.weixin.qq.com/s/-A-NRQ4sTdUvddioGpVslg)
- [Reddit r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/)
- [Reddit r/MachineLearning](https://www.reddit.com/r/MachineLearning/)

🦞 每日08:00自动更新
