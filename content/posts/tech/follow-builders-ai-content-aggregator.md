---
title: "Follow Builders：追踪 AI 顶尖建造者的信息聚合神器"
date: "2026-03-29T21:51:00+08:00"
slug: "follow-builders-ai-content-aggregator"
description: "深入解读 Follow Builders 项目，一个 AI 驱动的信息聚合工具，追踪 AI 领域顶尖研究员、创始人、产品经理和工程师的最新动态，整理成易于消化的摘要推送。"
draft: false
categories: ["技术笔记"]
tags: ["AI资讯", "信息聚合", "OpenClaw", "SKILL", "Twitter"]
---

# Follow Builders：追踪 AI 顶尖建造者的信息聚合神器

> 一文读懂 AI 时代的信息筛选之道——追踪建造者，而非网红

**学习目标**

学完本文后，你将掌握：
- 理解 Follow Builders 的核心设计理念与产品定位
- 掌握安装、配置和使用 Follow Builders 的完整流程
- 了解默认信息源（播客、X 建造者、官方博客）的完整列表
- 学会自定义摘要风格和推送偏好
- 理解其去中心化隐私保护设计

---

## 一、项目概述

### 1.1 是什么

[Follow Builders](https://github.com/zarazhangrui/follow-builders) 是一个 **AI 驱动的信息聚合工具**。它的核心功能是追踪 AI 领域最顶尖的建造者——研究员、创始人、产品经理和工程师——并将他们的最新动态整理成易于消化的摘要推送给你。

### 1.2 项目信息

| 项目 | 内容 |
|------|------|
| Stars | 1.7k（1730） |
| Forks | 140 |
| 许可证 | MIT |
| 最新更新 | 2026-03-25 |

### 1.3 核心理念

> **追踪那些真正在做产品、有独立见解的人，而非只会搬运信息的网红。**

在信息爆炸的时代，我们每天都被海量内容淹没。Follow Builders 选择了一条不同的路：**只追踪真正在一线建造的人**。他们分享的是第一手经验、独立思考和深度洞察，而非二手转发和标题党。

### 1.4 与其他资讯工具的区别

| 维度 | 传统资讯工具 | Follow Builders |
|------|--------------|----------------|
| 筛选标准 | 热度/算法推荐 | 建造者质量 |
| 内容来源 | 随机/爬虫 | 精选建造者第一手内容 |
| 摘要方式 | 机器生成（质量差） | AI 根据偏好定制 |
| 信息源 | 需要自己维护 | 中心化统一更新 |
| API Key | 多个平台需要多个 Key | 无需任何 API Key |

---

## 二、核心功能详解

### 2.1 你会得到什么

每日或每周推送到你常用的通讯工具（Telegram、Discord、WhatsApp 等），包含：

| 内容类型 | 说明 |
|---------|------|
| 播客摘要 | 5 个顶级 AI 播客新节目的精华摘要 |
| X/Twitter 观点 | 25 位精选 AI 建造者的关键观点和洞察 |
| 官方博客 | AI 公司官方博客的完整文章（Anthropic Engineering、Claude Blog） |
| 原始链接 | 所有原始内容的链接，方便深入阅读 |
| 多语言支持 | 英文、中文或双语版本 |

### 2.2 推送方式

| 方式 | 说明 |
|------|------|
| Telegram | 即时推送，适合高信息密度用户 |
| Discord | 适合社区内分享和讨论 |
| WhatsApp | 私密性强，适合个人使用 |
| 直接聊天 | 直接在 AI Agent 对话中显示 |

### 2.3 推送频率

- **每日推送**：适合需要紧跟行业动态的用户
- **每周推送**：适合希望系统化学习、不被信息焦虑的用户

---

## 三、默认信息源

### 3.1 播客来源（5个）

| 播客名称 | 说明 |
|---------|------|
| [Latent Space](https://www.youtube.com/@LatentSpacePod) | AI 技术深度播客，专注 LLM 和 AI 系统 |
| [Training Data](https://www.youtube.com/playlist?list=PLOhHNjZItNnMm5tdW61JpnyxeYH5NDDx8) | ML 训练相关技术讨论 |
| [No Priors](https://www.youtube.com/@NoPriorsPodcast) | AI 创业和投资视角 |
| [Unsupervised Learning](https://www.youtube.com/@RedpointAI) | AI 和技术深度分析 |
| [Data Driven NYC](https://www.youtube.com/@DataDrivenNYC) | 数据驱动文化和创业 |

### 3.2 X/Twitter AI 建造者（25位）

| 类别 | 建造者列表 |
|------|-----------|
| LLM 大牛 | Andrej Karpathy、Sam Altman、Amanda Askell |
| AI 工程师 | Swyx、Josh Woodward、Guillermo Rauch、Alex Albert |
| 产品/创始人 | Garry Tan、Aaron Levie、Peter Yang、Nikunj Kothari |
| 投资人大佬 | Matt Turck、Aditya Agarwal |
| Google/AI Lab | Kevin Weil、Google Labs |
| Others | Cat Wu、Thariq、Amjad Masad、Ryo Lu、Dan Shipper、Peter Steinberger、Zara Zhang、Claude |

### 3.3 官方博客（2个）

| 博客 | 说明 |
|------|------|
| [Anthropic Engineering](https://www.anthropic.com/engineering) | Anthropic 团队的技术深度文章 |
| [Claude Blog](https://claude.com/blog) | Claude 的产品公告与更新 |

---

## 四、快速开始

### 4.1 前置要求

| 要求 | 说明 |
|------|------|
| AI Agent | OpenClaw、Claude Code 或类似工具 |
| 网络连接 | 用于获取中心化 feed |

**仅此而已。不需要任何 API Key。**

### 4.2 安装步骤

#### OpenClaw 安装

```bash
# 从 ClawhHub 安装（即将上线）
clawhub install follow-builders

# 或手动安装
git clone https://github.com/zarazhangrui/follow-builders.git ~/skills/follow-builders
cd ~/skills/follow-builders/scripts && npm install
```

#### Claude Code 安装

```bash
git clone https://github.com/zarazhangrui/follow-builders.git ~/.claude/skills/follow-builders
cd ~/.claude/skills/follow-builders/scripts && npm install
```

### 4.3 初始化配置

1. 在你的 AI Agent 中输入 `"set up follow builders"` 或执行 `/follow-builders`
2. Agent 会以对话方式引导你完成设置——**不需要手动编辑任何配置文件**

Agent 会询问你：
- 推送频率（每日或每周）和时间
- 语言偏好（英文、中文或双语）
- 推送方式（Telegram、邮件或直接在聊天中显示）

**设置完成后，你的第一期摘要会立即推送。**

---

## 五、自定义配置

### 5.1 通过对话修改偏好

直接告诉你的 Agent：

| 示例指令 | 说明 |
|---------|------|
| "改成每周一早上推送" | 修改推送频率和时间 |
| "语言换成中文" | 修改语言偏好 |
| "把摘要写得更简短一些" | 修改摘要详细程度 |
| "显示我当前的设置" | 查看当前配置 |

### 5.2 自定义摘要风格

Skill 使用纯文本 prompt 文件来控制内容的摘要方式。你可以通过两种方式自定义：

#### 通过对话（推荐）

直接告诉你的 Agent——
- "摘要写得更简练一些"
- "多关注可操作的洞察"
- "用更轻松的语气"

Agent 会自动帮你更新 prompt。

#### 直接编辑（高级用户）

编辑 `prompts/` 文件夹中的文件：

| 文件 | 说明 |
|------|------|
| `summarize-podcast.md` | 播客节目的摘要方式 |
| `summarize-tweets.md` | X/Twitter 帖子的摘要方式 |
| `summarize-blogs.md` | 博客文章的摘要方式 |
| `digest-intro.md` | 整体摘要的格式和语气 |
| `translate.md` | 英文内容翻译为中文的方式 |

这些都是**纯文本指令，不是代码**。修改后下次推送即生效。

---

## 六、工作原理

### 6.1 架构流程

```
┌─────────────────┐
│   中心化 Feed   │  每日更新
│  (博客/油管/X)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HTTP 请求获取   │  一次请求
│   (无需 API)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    AI Agent     │  按偏好混编
│  (本地处理)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    推送渠道     │  Telegram/Discord/
│   (你自己选择)   │  WhatsApp/直接聊天
└─────────────────┘
```

### 6.2 技术细节

| 环节 | 技术实现 |
|------|---------|
| 博客抓取 | 网页抓取 |
| YouTube 字幕 | Supadata |
| X/Twitter 帖子 | 官方 API |
| Feed 更新 | 中心化服务每日抓取 |
| 摘要生成 | 本地 AI Agent |

---

## 七、隐私保护

Follow Builders 在隐私保护方面设计出色：

| 保护措施 | 说明 |
|---------|------|
| 无 API Key 外发 | 不发送任何 API Key——所有内容由中心化服务获取 |
| 本地存储 | Telegram/邮件等 Key 仅存储在本地 ~/.follow-builders/.env |
| 只读公开内容 | Skill 只读取公开内容（公开博客、YouTube 视频、X 帖子） |
| 配置本地保存 | 你的配置、偏好和阅读记录都保留在自己设备上 |

---

## 八、与 OpenClaw SKILL 生态

### 8.1 SKILL 文件结构

```
follow-builders/
├── .github/           # GitHub Actions CI/CD
├── config/            # 配置文件
├── examples/          # 示例输出
├── prompts/           # 摘要风格配置（可自定义）
├── scripts/           # 安装脚本
├── SKILL.md          # SKILL 定义文件
└── README.zh-CN.md   # 中文说明
```

### 8.2 如何集成到 OpenClaw

Follow Builders 本身就是一个 **OpenClaw SKILL**。安装后，它会：

1. **监听设置命令**：响应 `"set up follow builders"` 或 `/follow-builders`
2. **引导配置**：通过对话方式收集用户偏好
3. **生成摘要**：调用 AI 能力根据 prompt 模板生成摘要
4. **执行推送**：根据用户选择的渠道推送内容

---

## 九、使用场景

### 9.1 典型使用场景

| 场景 | 使用方式 |
|------|---------|
| 晨间学习 | 每天早上收到一份 AI 资讯摘要，30 分钟了解行业动态 |
| 周末深度 | 每周一收到一份深度摘要，系统化学习 |
| 项目调研 | 追踪特定建造者，获取第一手技术洞察 |
| 行业洞察 | 关注创始人视角，了解 AI 创业趋势 |

### 9.2 与其他工具的协同

| 工具 | 协同方式 |
|------|---------|
| Hacker News | HN 提供技术讨论，Follow Builders 提供建造者洞察 |
| Twitter/X | 互补——HN 是社区讨论，FB 是精选建造者视角 |
| AI 新闻早报 | 互补——早报是媒体视角，FB 是建造者第一手视角 |

---

## 十、常见问题

### Q: 为什么不需要 API Key？

**A**: 所有内容（博客文章 + YouTube 字幕 + X/Twitter 帖子）由**中心化服务统一抓取**。你的 Agent 只需要一次 HTTP 请求获取 feed，不需要对接各个平台的 API。

### Q: 如何添加更多的信息源？

**A**: 目前信息源由中心化统一管理和更新，你无需操作即可获得最新的信息源。如需自定义，可以编辑 `prompts/` 中的配置文件来调整摘要风格。

### Q: 支持哪些 AI Agent？

**A**: 目前支持 OpenClaw 和 Claude Code。其他 Agent 可以参考 SKILL.md 的格式进行适配。

### Q: 推送频率可以自定义吗？

**A**: 可以。通过对话告诉 Agent 你想要的频率和时间，例如"每周三晚上推送"。

### Q: 如何确保内容质量？

**A**: Follow Builders 通过**人工精选建造者名单**来保证质量。25 位 X 建造者和 5 个播客都是 AI 领域真正有影响力的一线人员，而非随机抓取的网红。

---

## 十一、总结

Follow Builders 提供了一种**AI 时代的信息筛选新范式**：

| 核心价值 | 说明 |
|---------|------|
| 质量优先 | 追踪建造者，而非搬运网红 |
| 中心化抓取 | 中心化抓取，本地 AI 处理 |
| 隐私友好 | 无需暴露 API Key，内容本地处理 |
| 高度可定制 | 通过对话或编辑 prompt 文件自定义 |

**适合用户：**
- AI 研究者和工程师
- AI 创业者和技术管理者
- 对 AI 行业有深度学习需求的用户
- 希望获取第一手行业洞察的投资者

**不适合用户：**
- 需要实时新闻的用户（FB 是精选+摘要，非实时）
- 喜欢刷信息的用户（设计理念是少而精）

---

## 十二、资源链接

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/zarazhangrui/follow-builders |
| 英文 README | https://github.com/zarazhangrui/follow-builders/blob/main/README.md |
| 中文 README | https://github.com/zarazhangrui/follow-builders/blob/main/README.zh-CN.md |
| SKILL.md | 项目内 SKILL.md 文件 |
| 示例摘要 | examples/sample-digest.md |

**附：精选建造者完整名单（25位 X 账号）**

Andrej Karpathy、Swyx、Josh Woodward、Kevin Weil、Peter Yang、Nan Yu、Madhu Guru、Amanda Askell、Cat Wu、Thariq、Google Labs、Amjad Masad、Guillermo Rauch、Alex Albert、Aaron Levie、Ryo Lu、Garry Tan、Matt Turck、Zara Zhang、Nikunj Kothari、Peter Steinberger、Dan Shipper、Aditya Agarwal、Sam Altman、Claude
