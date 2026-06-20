---
title: "Follow Builders：追踪 AI 建造者的信息聚合工具"
date: "2026-03-29T21:51:00+08:00"
slug: "follow-builders-ai-content-aggregator"
description: "深入解读 Follow Builders 项目，一个 AI 驱动的信息聚合工具，追踪 AI 领域顶尖研究员、创始人、产品经理和工程师的最新动态，整理成易于消化的摘要推送。"
draft: false
categories: ["技术笔记"]
tags: ["AI 资讯", "信息聚合", "OpenClaw", "SKILL", "Twitter"]
---

# Follow Builders：追踪 AI 建造者的信息聚合工具

Follow Builders 是一个 OpenClaw SKILL 形式的信息聚合工具，订阅 AI 领域一线研究员、创始人、产品经理和工程师的公开内容（X 帖子、播客、官方博客），由本地 AI Agent 按用户偏好生成摘要，推送到 Telegram、Discord、WhatsApp 或聊天对话中。项目地址：https://github.com/zarazhangrui/follow-builders

## 目录

- [为什么需要这个工具](#为什么需要这个工具)
- [学习目标](#学习目标)
- [项目概览](#项目概览)
- [你会得到什么](#你会得到什么)
- [默认信息源](#默认信息源)
- [快速开始](#快速开始)
- [自定义配置](#自定义配置)
- [工作原理](#工作原理)
- [端到端案例](#端到端案例)
- [隐私保护](#隐私保护)
- [错误排查](#错误排查)
- [常见问题](#常见问题)
- [采用顺序与决策建议](#采用顺序与决策建议)
- [资源链接](#资源链接)

## 为什么需要这个工具

AI 领域的信息源有两个特征：数量爆炸，质量参差。技术博客、播客、X 帖子、论文解读每天产生数百条更新，但其中大部分是二手转发和标题党。直接订阅所有源头会陷入信息过载，靠算法推荐又会把时间花在热度高但价值低的内容上。

Follow Builders 的做法是固定订阅 25 位一线建造者和 5 个顶级播客，由中心化服务统一抓取公开内容，再由本地 AI Agent 按用户偏好生成摘要。两个直接收益：信息源质量由人工筛选保证，摘要风格可定制而不被推荐算法带偏。

## 学习目标

读完本文后，你能够：

- 说出 Follow Builders 与传统 RSS 阅读器、算法资讯工具在选源和处理方式上的差异
- 完成 OpenClaw 或 Claude Code 下的安装与初始化配置
- 通过对话指令调整推送频率、语言和摘要风格
- 解释中心化抓取与本地处理分离带来的隐私优势
- 识别并处理常见的安装与推送失败问题

## 项目概览

| 项目 | 内容 |
|------|------|
| Stars | 1.7k（1730） |
| Forks | 140 |
| 许可证 | MIT |
| 最新更新 | 2026-03-25 |

Follow Builders 与传统资讯工具的差异体现在选源标准和处理方式上。传统工具按热度或算法推荐筛选内容，来源随机，摘要由通用模型生成，质量参差；Follow Builders 按建造者质量选源，固定追踪一线人员，摘要由本地 Agent 按用户偏好定制。信息源由中心化服务统一更新，用户无需自己维护 feed 列表。

## 你会得到什么

每日或每周推送到你常用的通讯工具，内容包括：

- **播客摘要**：5 个 AI 顶级播客新节目的精华摘要
- **X/Twitter 观点**：25 位 AI 建造者的关键帖子和洞察
- **官方博客**：Anthropic Engineering、Claude Blog 的完整文章
- **原始链接**：所有内容的原始链接，方便深入阅读
- **多语言支持**：英文、中文或双语版本

推送渠道支持 Telegram、Discord、WhatsApp 和直接在 AI Agent 对话中显示。推送频率分为每日和每周两档：每日适合紧跟行业动态，每周适合系统化学习、降低信息焦虑。

## 默认信息源

### 播客来源（5 个）

| 播客名称 | 说明 |
|---------|------|
| [Latent Space](https://www.youtube.com/@LatentSpacePod) | AI 技术深度播客，专注 LLM 和 AI 系统 |
| [Training Data](https://www.youtube.com/playlist?list=PLOhHNjZItNnMm5tdW61JpnyxeYH5NDDx8) | ML 训练相关技术讨论 |
| [No Priors](https://www.youtube.com/@NoPriorsPodcast) | AI 创业和投资视角 |
| [Unsupervised Learning](https://www.youtube.com/@RedpointAI) | AI 和技术深度分析 |
| [Data Driven NYC](https://www.youtube.com/@DataDrivenNYC) | 数据驱动文化和创业 |

### X/Twitter AI 建造者（25 位）

名单按角色分组，包含个人账号和少量组织账号（如 Google Labs、Claude 官方账号）：

| 类别 | 建造者 |
|------|--------|
| LLM 大牛 | Andrej Karpathy、Sam Altman、Amanda Askell |
| AI 工程师 | Swyx、Josh Woodward、Guillermo Rauch、Alex Albert |
| 产品/创始人 | Garry Tan、Aaron Levie、Peter Yang、Nikunj Kothari |
| 投资人 | Matt Turck、Aditya Agarwal |
| Google/AI Lab | Kevin Weil、Google Labs |
| 其他 | Cat Wu、Thariq、Amjad Masad、Ryo Lu、Dan Shipper、Peter Steinberger、Zara Zhang、Claude |

> 注：名单中的 "Claude" 指 Claude 官方 X 账号，"Google Labs" 指组织账号，二者用于追踪官方动态而非个人观点。

### 官方博客（2 个）

- [Anthropic Engineering](https://www.anthropic.com/engineering)：Anthropic 团队的技术深度文章
- [Claude Blog](https://claude.com/blog)：Claude 的产品公告与更新

## 快速开始

### 前置要求

- 已安装 OpenClaw 或 Claude Code（或其他兼容 SKILL 格式的 AI Agent）
- 网络可访问中心化 feed 服务

### 安装步骤

OpenClaw 安装：

```bash
# 从 ClawhHub 安装（即将上线）
clawhub install follow-builders

# 或手动安装
git clone https://github.com/zarazhangrui/follow-builders.git ~/skills/follow-builders
cd ~/skills/follow-builders/scripts && npm install
```

Claude Code 安装：

```bash
git clone https://github.com/zarazhangrui/follow-builders.git ~/.claude/skills/follow-builders
cd ~/.claude/skills/follow-builders/scripts && npm install
```

### 初始化配置

1. 在 AI Agent 中输入 `"set up follow builders"` 或执行 `/follow-builders`
2. Agent 以对话方式引导你完成设置，无需手动编辑配置文件

Agent 会询问三项偏好：推送频率（每日或每周）和时间、语言偏好（英文、中文或双语）、推送方式（Telegram、邮件或直接在聊天中显示）。设置完成后，第一期摘要会立即推送。

## 自定义配置

### 通过对话修改偏好

直接告诉 Agent 即可，例如：

- "改成每周一早上推送"
- "语言换成中文"
- "把摘要写得更简短一些"
- "显示我当前的设置"

### 自定义摘要风格

摘要方式由 `prompts/` 目录下的纯文本 prompt 文件控制，不是代码。两种修改方式：

**通过对话（推荐）**：直接告诉 Agent "摘要写得更简练一些"、"多关注可操作的洞察"、"用更轻松的语气"，Agent 会自动更新 prompt。

**直接编辑（高级用户）**：修改 `prompts/` 下的文件：

| 文件 | 控制内容 |
|------|---------|
| `summarize-podcast.md` | 播客节目的摘要方式 |
| `summarize-tweets.md` | X/Twitter 帖子的摘要方式 |
| `summarize-blogs.md` | 博客文章的摘要方式 |
| `digest-intro.md` | 整体摘要的格式和语气 |
| `translate.md` | 英文内容翻译为中文的方式 |

修改后下次推送即生效。

## 工作原理

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

各环节的技术实现：

- **博客抓取**：网页抓取，由中心化服务完成
- **YouTube 字幕**：通过 Supadata 获取
- **X/Twitter 帖子**：中心化服务通过官方 API 抓取，用户侧无需 X API Key
- **Feed 更新**：中心化服务每日抓取并打包
- **摘要生成**：本地 AI Agent 按 prompt 模板处理

> 关于 "无需 API Key" 的澄清：用户侧无需 X/Twitter、YouTube 等平台的 API Key，因为抓取由中心化服务统一完成。用户只需配置推送渠道的凭证（如 Telegram Bot Token），这些凭证仅保存在本地。

## 端到端案例

以一个完整的每日推送流程为例，展示任务如何流过系统：

1. **早上 08:00**：中心化服务抓取过去 24 小时内 25 位建造者的新帖子、5 个播客的新节目、2 个官方博客的新文章
2. **08:05**：抓取结果打包成 feed，发布到中心化端点
3. **08:10**：你的本地 AI Agent 按计划发起一次 HTTP 请求，拉取当日 feed
4. **08:11**：Agent 按 `prompts/summarize-tweets.md` 处理 X 帖子，按 `summarize-podcast.md` 处理播客字幕，按 `summarize-blogs.md` 处理博客
5. **08:13**：Agent 按 `digest-intro.md` 组装整体摘要，按 `translate.md` 将英文部分翻译为中文（如已配置双语）
6. **08:14**：Agent 通过 Telegram Bot Token 将摘要推送到你配置的聊天
7. **08:15**：你在 Telegram 收到一份包含播客精华、建造者观点、博客链接的中文摘要

整个过程只需配置一次，之后每天自动执行。

## 隐私保护

Follow Builders 的隐私设计基于一个原则：用户侧不外发任何平台 API Key，所有内容获取由中心化服务完成。

具体措施：

- **无 API Key 外发**：不发送任何 API Key 到中心化服务，所有内容由中心化服务自行获取
- **本地存储**：Telegram Bot Token、邮件配置等仅存储在本地 `~/.follow-builders/.env`
- **只读公开内容**：Skill 只读取公开博客、YouTube 视频、X 帖子
- **配置本地保存**：偏好和阅读记录保留在自己设备上

## 错误排查

| 错误现象 | 可能原因 | 处理方式 |
|---------|---------|---------|
| 安装后 `/follow-builders` 无响应 | SKILL 未被 Agent 识别 | 检查克隆路径是否正确，重启 Agent |
| `npm install` 失败 | 网络或 Node 版本问题 | 确认 Node 版本 ≥ 18，使用代理重试 |
| 推送未到达 | Telegram Bot Token 错误或网络问题 | 在 Agent 中执行 "显示我当前的设置" 核对配置 |
| 摘要内容为空 | 中心化 feed 当日无更新 | 等待下一周期，或检查网络连接 |
| 摘要质量下降 | prompt 文件被误改 | 用 `git diff prompts/` 查看改动，`git checkout` 恢复 |
| 双语翻译缺失 | `translate.md` 配置异常 | 检查语言偏好设置，确认 prompt 文件存在 |

## 常见问题

### Q: 为什么不需要 API Key？

所有内容（博客文章、YouTube 字幕、X/Twitter 帖子）由中心化服务统一抓取。你的 Agent 只需一次 HTTP 请求获取 feed，不需要对接各个平台的 API。用户侧只需配置推送渠道的凭证（如 Telegram Bot Token）。

### Q: 如何添加更多的信息源？

信息源由中心化统一管理和更新，用户无需操作即可获得最新信息源。如需调整摘要风格，可编辑 `prompts/` 中的配置文件。

### Q: 支持哪些 AI Agent？

目前支持 OpenClaw 和 Claude Code。其他 Agent 可参考 SKILL.md 的格式进行适配。

### Q: 推送频率可以自定义吗？

可以。通过对话告诉 Agent 你想要的频率和时间，例如 "每周三晚上推送"。

### Q: 如何确保内容质量？

Follow Builders 通过人工精选建造者名单保证质量。25 位 X 建造者和 5 个播客都是 AI 领域有影响力的一线人员或组织，而非随机抓取的网红账号。

## 采用顺序与决策建议

如果你打算接入 Follow Builders，建议按以下顺序：

1. **先评估信息源名单**：查看 25 位建造者和 5 个播客是否覆盖你关心的领域，若重叠度低则收益有限
2. **在 OpenClaw 或 Claude Code 中安装**：按快速开始步骤完成克隆和依赖安装
3. **先用每日推送试跑一周**：评估摘要质量和信息密度，确认是否符合你的阅读习惯
4. **调整摘要风格**：通过对话指令调整详细程度和语气，找到最适合自己的格式
5. **切换到每周推送（可选）**：如果每日信息量过大，切换到每周以降低信息焦虑
6. **定期回看名单更新**：中心化服务会更新信息源，关注仓库 commit 了解变化

## 资源链接

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/zarazhangrui/follow-builders |
| 英文 README | https://github.com/zarazhangrui/follow-builders/blob/main/README.md |
| 中文 README | https://github.com/zarazhangrui/follow-builders/blob/main/README.zh-CN.md |
| SKILL.md | 项目内 SKILL.md 文件 |
| 示例摘要 | examples/sample-digest.md |

**附：精选建造者完整名单（25 位 X 账号）**

Andrej Karpathy、Swyx、Josh Woodward、Kevin Weil、Peter Yang、Nan Yu、Madhu Guru、Amanda Askell、Cat Wu、Thariq、Google Labs、Amjad Masad、Guillermo Rauch、Alex Albert、Aaron Levie、Ryo Lu、Garry Tan、Matt Turck、Zara Zhang、Nikunj Kothari、Peter Steinberger、Dan Shipper、Aditya Agarwal、Sam Altman、Claude
