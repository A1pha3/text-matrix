---
title: "DataWeave/easy-vibe：一个「会说话就能做 App」的 Vibe Coding 2026 教程完全指南"
date: "2026-05-10T16:55:00+08:00"
slug: "datawhale-easy-vibe-vibe-coding-course-guide"
description: "DataWeave/easy-vibe 是一个面向零基础的 Vibe Coding 2026 开源教程，通过「先做出来，再理解原理」的沉浸式交互学习路径，让普通人也能用 AI 构建产品。本文全面解析其学习路径、内容体系、多语言支持，以及与 OpenClaw 等 AI Coding Agent 的协同方式。"
draft: false
categories: ["技术笔记"]
tags: ["Vibe Coding", "AI Coding", "DataWeave", "AI Agent", "无门槛编程", "教程指南"]
---

# DataWeave/easy-vibe：一个「会说话就能做 App」的 Vibe Coding 2026 教程完全指南

> 项目地址：[dataweavechina/easy-vibe](https://github.com/dataweavechina/easy-vibe)
>
>  Stars: 8,652⭐ | License: CC BY-NC-SA 4.0 | 官网：[dataweavechina.github.io/easy-vibe](https://dataweavechina.github.io/easy-vibe/welcome.html)

---

## 先体验：If You Can Talk, You Can Build

**想要一个记账本？说出来。**
**需要一个带微信登录的预约系统？说出来。**
**想要一个带评论的博客？说出来。**

在 AI 时代，编程的起点不再是写代码——而是**描述你想要什么**。

DataWeave/easy-vibe（以下简称 easy-vibe） 是一个零基础友好的人工智能编程学习项目，由 DataWeave（数据小炒）开源维护。核心理念一句话：**If you can talk, you can build.** 只要你会说话，你就能做应用。

项目于 2026 年 1 月正式发布，短短几个月斩获 8,652 颗 Star，课程内容已覆盖 Stage 1（入门）、Stage 2（前端+后端+部署）、Stage 3（AI Coding 高级工作流）和附录知识库，并支持 **10 种语言**：简体中文、繁体中文、英语、日语、韩语、西班牙语、法语、德语、阿拉伯语、越南语。

---

## 核心学习路径：从零到发布的四个 Stage

### Stage 1：先做出来，再理解原理

**适合人群**：完全零基础、产品经理、创业者、在校学生

这是整个课程的起点，核心方法论：**Build First, Understand Later**——先跑起来，再补课。

| 阶段 | 核心内容 |
|:---|:---|
| [Learning Map](https://dataweavechina.github.io/easy-vibe/en/stage-1/learning-map/) | 完整的成长路线图和学习节奏建议 |
| [AI Capabilities Through Games](https://dataweavechina.github.io/easy-vibe/en/stage-1/ai-capabilities-through-games/) | 通过游戏例子（如贪吃蛇）感受 AI 编程是什么体验 |
| [Introduction to AI IDE](https://dataweavechina.github.io/easy-vibe/en/stage-1/introduction-to-ai-ide/) | 了解主流 AI IDE（Cursor、Copilot、Windsurf 等）的工作原理和使用方法 |
| [Find Great Ideas](https://dataweavechina.github.io/easy-vibe/en/stage-1/finding-great-idea/) | 如何发现、筛选和验证值得做的产品创意 |
| [Build Product Prototypes](https://dataweavechina.github.io/easy-vibe/en/stage-1/building-prototype/) | 从需求到单页原型，再到完整产品原型 |
| [Integrate AI Capabilities](https://dataweavechina.github.io/easy-vibe/en/stage-1/integrating-ai-capabilities/) | 集成 AI 能力：文本生成、图片生成、视频生成 |
| [Complete Project Practice](https://dataweavechina.github.io/easy-vibe/en/stage-1/complete-project-practice/) | 完整走一遍：模拟真实场景→收集用户反馈→迭代优化 |

#### 附录：产品思维和用户验证（3大核心框架）

Stage 1 的附录知识库新增了产品思维和需求验证内容，帮助学习者在动手之前做正确的事：

- [Where to Find Ideas](https://dataweavechina.github.io/easy-vibe/en/stage-1/appendix-idea-sources/) — **3 个最佳创意来源**，帮助你持续找到值得做的小产品
- [Double Diamond](https://dataweavechina.github.io/easy-vibe/en/stage-1/appendix-double-diamond/) — **做正确的事，再正确地做事**：从发散→聚焦→发散→交付的完整设计思维框架
- [Jobs to Be Done (JTBD)](https://dataweavechina.github.io/easy-vibe/en/stage-1/appendix-jobs-to-be-done/) — **理解用户真正想完成的任务**，而不是他们表面说的功能
- [The Mom Test](https://dataweavechina.github.io/easy-vibe/en/stage-1/appendix-mom-test/) — **用对问题验证真实需求**，避免自嗨式产品开发

这些框架填补了「只会问 AI」和「能做出好产品」之间的鸿沟。很多人在 AI 时代依然做不出好产品，问题不在于不会写代码——而是不知道该做什么。

---

### Stage 2：从原型到全栈上线

**适合人群**：初级开发者、独立开发者、indie hackers

Stage 2 教你把 Stage 1 的原型变成真实可用的产品。

#### 前端路径

| 章节 | 内容亮点 |
|:---|:---|
| [Lovart & Nanobanana 资产生成](https://dataweavechina.github.io/easy-vibe/en/stage-2/lovart/) | 用 AI 生成设计资产，构建意图识别绘图 Agent |
| [Figma & MasterGo 工作流](https://dataweavechina.github.io/easy-vibe/en/stage-2/frontend/figma-mastergo/) | 设计稿到代码的完整流程 |
| [AI 生成 UI：LLM + Skills](https://dataweavechina.github.io/easy-vibe/en/stage-2/frontend/llm-skills/) | 让 AI 生成更美观、更有一致性的界面 |
| [Design to Code](https://dataweavechina.github.io/easy-vibe/en/stage-2/frontend/design-to-code/) | 设计稿还原为可运行的浏览器代码 |
| [Modern Component Library](https://dataweavechina.github.io/easy-vibe/en/stage-2/frontend/modern-component-library/) | 用现代组件库快速搭建专业级 UI |

#### 后端路径

| 章节 | 内容亮点 |
|:---|:---|
| [Git & GitHub 协作流](https://dataweavechina.github.io/easy-vibe/en/stage-2/backend/git-workflow/) | 版本控制和多人大规模协作 |
| [Supabase 数据库](https://dataweavechina.github.io/easy-vibe/en/stage-2/backend/database-supabase/) | 现代 BaaS 平台，关系型数据库速通 |
| [API 设计与 AI 辅助开发](https://dataweavechina.github.io/easy-vibe/en/stage-2/backend/ai-interface-code/) | 用 AI 辅助 API 设计和文档撰写 |
| [Zeabur 一键部署](https://dataweavechina.github.io/easy-vibe/en/stage-2/backend/zeabur-deployment/) | 前后端一键上线 |
| [Stripe 支付集成](https://dataweavechina.github.io/easy-vibe/en/stage-2/backend/stripe-payment/) | **实战重点**：完整接入 Stripe 支付体系，支持多产品计费体系 |
| [WeChat Mini Program 后端](https://dataweavechina.github.io/easy-vibe/en/stage-2/backend/wechat-backend/) | 微信小程序后端集成 |

#### 实战项目：AI 文案生成网站（SaaS 全栈）

Stage 2 的集大成之作——**[Your First SaaS Full-Stack App](https://dataweavechina.github.io/easy-vibe/en/stage-2/assignments/fullstack-app/)**，完整覆盖：

- 用户登录与鉴权
- AI 文案生成核心流程
- Stripe 订阅计费
- 管理后台

整个项目走完，你就拥有了一个**可演示、可收费的真实 SaaS 产品原型**。

---

### Stage 3：AI Coding 高级工作流

**适合人群**：中高级开发者、AI 工程感兴趣者

Stage 3 是课程的高级内容，围绕 **Claude Code** 展开，涵盖当前最前沿的 AI Coding 工作流。

#### Claude Code 核心技能

| 章节 | 核心内容 |
|:---|:---|
| [Claude Code 基础](https://dataweavechina.github.io/easy-vibe/en/stage-3/core-skills/basics/) | 安装、配置、核心命令和使用范式 |
| [MCP (Model Context Protocol)](https://dataweavechina.github.io/easy-vibe/en/stage-3/core-skills/mcp/) | 连接 GitHub、数据库、外部 API，将 Claude Code 接入真实工具链 |
| [Skills 系统](https://dataweavechina.github.io/easy-vibe/en/stage-3/core-skills/skills/) | 将专业知识封装成可复用的技能，在多个项目中反复调用 |
| [Agent Teams](https://dataweavechina.github.io/easy-vibe/en/stage-3/core-skills/agent-teams/) | 多 Agent 协作，模拟真实团队分工——规划者、执行者、审查者各司其职 |
| [Long-Running Tasks](https://dataweavechina.github.io/easy-vige/en/stage-3/core-skills/long-running-tasks/) | 设计可靠的长时间任务，保证 AI 不中途跑偏 |
| [Spec Coding](https://dataweavechina.github.io/easy-vige/en/stage-3/core-skills/spec-coding/) | 从「随口 prompting」升级到「规范驱动开发」——先写规格说明书，让 AI 按规格执行，减少返工和幻觉。 |
| [Claude Agent SDK](https://dataweavechina.github.io/easy-vibe/en/stage-3/core-skills/claude-agent-sdk/) | 将 Claude Code 能力集成到自己的工具和平台中 |
| [Mobile Development](https://dataweavechina.github.io/easy-vibe/en/stage-3/core-skills/mobile-development/) | 用 Claude Code 做移动端开发（iOS/Android）|
| [Cross-Platform Projects](https://dataweavechina.github.io/easy-vibe/en/stage-3/cross-platform/) | 跨平台项目实战 |

---

### 附录知识库：80+ 知识点，随用随查

easy-vibe 的附录知识库覆盖 9 大知识领域，目前已有 **80+ 交互式知识点**，涉及：
- 计算机基础知识
- 前端语言基础（HTML/CSS/JS
- 后端语言基础（Node.js/Python/Go
- AI 基础 (LLM / Diffusion Model / RAG) 原理可视化
- 工程实践（Git、终端、API 等）

---

## 与 OpenClaw 的协同：🦞 + easy-vibe = 真正的 Vibe Coding

easy-vibe 在 2026 年 3 月 2 日正式支持 OpenClaw。项目中内置了 `llms.txt`，让 AI Coding Agent（包括 OpenClaw、Claude Code、Cursor、Trae 等）能够**快速理解项目结构，直接定位到最合适的学习内容**。

这意味着什么？

**OpenClaw 是你的 AI Coding Agent，easy-vibe 是你的教科书。**

两者结合：一个帮你干活，一个教你学习。
- 当你遇到具体任务 → OpenClaw 直接帮你搞定
- 当你想系统提升 → easy-vibe 带你从零到高级

> 🦞 想系统学习 OpenClaw？DataWeave 配套推出了 [hello-claw](https://github.com/dataweavechina/hello-claw)——专门为 OpenClaw 设计的上手教程。

---

## 多语言支持：10 种语言，全球覆盖

easy-vibe 是真正为全球学习者设计的产品。

| 语言 | 访问路径 |
|:---|:---|
| 🇺🇸 English | `easy-vibe/en/` |
| 🇨🇳 简体中文 | `easy-vibe/zh-CN/` |
| 🇹🇼 繁體中文 | `easy-vibe/zh-TW/` |
| 🇯🇵 日本語 | `easy-vibe/ja/` |
| 🇰🇷 한국어 | `easy-vibe/ko/` |
| 🇪🇸 Español | `easy-vibe/es/` |
| 🇫🇷 Français | `easy-vibe/fr/` |
| 🇩🇪 Deutsch | `easy-vibe/de/` |
| 🇸🇦 العربية | `easy-vibe/ar/` |
| 🇻🇳 Tiếng Việt | `easy-vibe/vi/` |

简体中文内容覆盖最完整，英文内容也基本同步更新。

---

## Vibe Stories：真实用户，真实故事

easy-vibe 还有一个感人的板块——**Vibe Stories**。

真实用户分享：
- 🌱 一位乡村小学教师用 AI 做出了教学管理工具
- 🎓 一个大学生用 AI 做出了毕业设计作品
- 💻 一位高中信息技术老师用 AI 辅助编程课教学
- 🚛 一位卡车司机用 AI 做出了物流调度小工具

---

## 如何开始

### 如果你是零基础

**Step 1** → 打开 [AI Capabilities Through Games](https://dataweavechina.github.io/easy-vibe/en/stage-1/ai-capabilities-through-games/)，感受一下 AI 编程是什么体验（大约 30 分钟）。

**Step 2** → 跟着 [Learning Map](https://dataweavechina.github.io/easy-vibe/en/stage-1/learning-map/) 走完 Stage 1（约 1-2 周）。

**Step 3** → 根据兴趣选 Stage 2 或 Stage 3。

### 如果你已经有基础

直接跳到 [Stage 2](https://dataweavechina.github.io/easy-vibe/en/stage-2/) 或 [Stage 3](https://dataweavechina.github.io/easy-vibe/en/stage-3/)，哪里不懂查哪里。

---

## 项目特色总结

| 特色 | 说明 |
|:---|:---|
| 🎮 先做再学 | Build First, Understand Later，打破「学了很多但做不出来」的困境 |
| 🎨 沉浸式交互 | GIF 动画 + 模拟鼠标 + 可交互 Demo，学习过程不枯燥 |
| 🌍 10 种语言 | 覆盖全球主要语言，零门槛上手 |
| 🦞 OpenClaw 友好 | llms.txt 加持，AI Agent 能直接读懂项目结构 |
| 📦 实战导向 | Stage 2 有完整 SaaS 项目，Stage 3 有跨平台项目实战 |
| 📚 知识库 | 9 大领域、80+ 知识点，随用随查 |
| 💡 产品思维优先 | 先教你想清楚做什么，再教你怎么实现 |

---

## 总结

easy-vibe 的核心价值：**打破编程学习的两个壁垒——不知道该做什么，以及不知道怎么做好。** 课程把产品思维（Appendix 部分）和工程实践融合在一起，先帮你搞清楚需求和用户，再帮你用 AI 把产品做出来、部署上线、接上支付。

**链接资源：**
- 🦞 OpenClaw + easy-vibe 组合，让 AI Coding 从「能用」到「用好」