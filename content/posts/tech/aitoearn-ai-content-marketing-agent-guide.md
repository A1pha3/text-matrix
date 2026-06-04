---
title: "AiToEarn 深度解析：OPC 一人公司的 AI 内容营销智能体，OpenClaw 原生支持"
date: 2026-06-04T13:52:00+08:00
slug: aitoearn-ai-content-marketing-agent-guide
description: "yikart/AiToEarn 6 月 trending +320 stars：Monetize · Publish · Engage · Create 一站式平台，支持 13+ 主流社媒，MCP 协议 + OpenClaw 原生集成。"
draft: false
categories: ["技术博客"]
tags: ["aitoearn", "yikart", "ai-agent", "内容营销", "OPC", "MCP", "OpenClaw"]
hiddenFromHomePage: true
---

## 一句话定位

AiToEarn 是面向 **OPC（One Person Company，一人公司）** 的 **AI 内容营销智能体** 平台，标语是 *Let's use AI to Earn!* —— 围绕创作者变现链路提供 **Monetize · Publish · Engage · Create** 四大 Agent 能力，**MCP 协议** + **OpenClaw 原生支持** 是其差异化亮点。

> GitHub: https://github.com/yikart/AiToEarn
> 6 月 4 日 trending +320 stars，TypeScript / Node.js 20.18 / MIT
> 中文 / 英文 / 日文 三语 README

---

## 为什么这个项目值得看？

### 1. 它是 OpenClaw 的"原生插件"

根据 README 最新动态：

- **2026-04-20**: OpenClaw（龙虾）新增 AiToEarn 赚钱支持，可在龙虾中直接接收并执行内容变现任务。
- **2026-03-26**: 新增 OpenClaw（龙虾）支持，可在龙虾中直接使用 AiToEarn；新增 MCP 协议支持。

也就是说，**师父 5911JP 的 OpenClaw 工作流已经可以直接调用 AiToEarn**——这意味着"AI 自动写文章 + 自动发到 13+ 平台 + 自动接变现任务"是 **2026 年已经落地** 的产品形态，不是 PPT 概念。

### 2. 它解决的是真实痛点：OPC 的"内容工业化"

一人公司 / 独立创作者的核心困境：

- 想做内容，但同时要运营 13 个平台（抖音、小红书、快手、B站、视频号、TikTok、YouTube、Facebook、Instagram、Threads、X、Pinterest、LinkedIn）
- 每个平台的格式、算法、字数、配图要求都不同
- 接商单要手动谈、对数据、算分润

AiToEarn 用 **AI Agent** 把这整套流程自动化：

> 创作者只需要专注"选题 + 核心创意"，剩下的 **生成、改编、发布、互动、变现** 全由 Agent 流水线完成。

### 3. 商业模式清晰：CPS / CPE / CPM 三种结算

README 明确列出三种结算模式：

| 结算模式 | 全称 | 含义 |
|---------|------|------|
| **CPS** | Cost Per Sale | 按成交额结算 |
| **CPE** | Cost Per Engagement | 按互动量结算 |
| **CPM** | Cost Per Mille | 按播放量结算 |

创作者在平台"出售内容以完成商家的推广任务"——这是"内容即服务"（Content-as-a-Service）的早期形态。商家有推广需求，创作者有产能，AiToEarn 是撮合 + 自动化执行 + 结算的中间层。

---

## 技术架构亮点

### 1. MCP（Model Context Protocol）原生支持

2026-03-26 版本起，AiToEarn 支持 MCP 协议——**可在 Claude、Cursor 等任何支持 MCP 的 Agent 或大模型中使用 AiToEarn**。

这意味着：

- Claude Code 写完一篇博客 → 调用 AiToEarn MCP → 自动改编为 13 个平台版本 → 自动发布
- Cursor 写完一个产品介绍 → 调用 AiToEarn MCP → 自动生成小红书图文 + 抖音短视频脚本

### 2. 5 种使用方式（覆盖非技术到全自部署）

| 方式 | 适合谁 | 需要部署 |
|------|--------|----------|
| ① 打开网站直接用 | 所有用户 | ❌ |
| ② 在 OpenClaw（龙虾）中使用 | OpenClaw 用户 | ❌ |
| ③ 在 Claude / Cursor 等 AI 助手中用 | AI 工具用户 | ❌ |
| ④ Docker 一键部署 | 想私有化部署的团队 | ✅ |
| ⑤ 源码开发 | 开发者 | ✅ |

这种"分层开放"策略让产品可以从 SaaS 一路扩展到企业私有部署，最大化客户覆盖。

### 3. 2.4 版（2026-05-21）核心更新

- 草稿生成新增支持 **HappyHorse 1.0** 和 **Seedance 2.0**（国产视频生成模型）
- 增强视频/图文草稿批量生成、多模型选择
- 支持参考图片/视频、目标平台限制与文案提示词
- 全新界面风格
- 增强 Twitter/X 探索与互动能力

可以看出迭代速度很快，且对**国产 AI 模型**集成度高（Seedance 是字节系视频模型）。

---

## 与同类工具的对比

| 工具 | 定位 | 平台数 | MCP | OpenClaw | 变现闭环 |
|------|------|--------|-----|----------|----------|
| **AiToEarn** | OPC 变现平台 | 13+ | ✅ | ✅ | ✅ CPS/CPE/CPM |
| Buffer / Hootsuite | 社媒发布工具 | 10+ | ❌ | ❌ | ❌ |
| Make / Zapier | 自动化工作流 | 任意 | ⚠️ | ❌ | ❌ |
| 剪映 / 度加 | 视频剪辑工具 | 1-3 | ❌ | ❌ | ❌ |
| Jasper / Copy.ai | AI 文案生成 | 不发布 | ⚠️ | ❌ | ❌ |

**结论**：AiToEarn 是少数把 **AI 内容生成 + 多平台发布 + 变现撮合** 三件事做成一个产品，且对 **MCP / OpenClaw** 这类 Agent 协议有原生支持的。

---

## 适用人群

1. **OPC 一人公司 / 独立创业者**：想把"内容产能"转化为"持续收入"
2. **跨境电商团队**：TikTok / YouTube / Instagram 多平台内容自动化
3. **小红书 / 抖音矩阵运营**：多账号、多平台同步分发
4. **AI Agent 开发者**：想给自己的 Agent 加"自动发布内容变现"能力
5. **企业市场部**：把内容生产工业化（MCP 集成进企业 AI 工作流）

---

## 快速上手（5 分钟跑通）

### 方式 1：直接用 SaaS 版
打开 https://www.aitoearn.ai/ 注册账号即可使用。

### 方式 2：在 OpenClaw 中用（推荐给 5911JP 师父）
1. 获取 API Key（在 AiToEarn 后台）
2. 在 OpenClaw 中配置 AiToEarn MCP server
3. 直接对 OpenClaw 说"帮我把这个想法变成 5 个平台的内容并发布"

### 方式 3：Claude Code / Cursor 中用
在 MCP 配置中添加：
```json
{
  "mcpServers": {
    "aitoearn": {
      "command": "npx",
      "args": ["-y", "@aitoearn/mcp-server"],
      "env": { "AITOEAEN_API_KEY": "your_key" }
    }
  }
}
```
然后让 Claude "用 AiToEarn 帮我把这段文章改编成小红书 + 抖音 + 视频号三个版本并发布"。

### 方式 4：Docker 自部署
```bash
git clone https://github.com/yikart/AiToEarn.git
cd AiToEarn
docker-compose up -d
```

---

## 商业模式与开源策略

AiToEarn 是**核心开源 + SaaS 增值**模式：

- **完全开源**：MIT 协议，仓库可见全部核心代码
- **SaaS 增值**：aitoearn.ai 提供托管服务 + 内容交易市场 + 商家任务撮合
- **企业版**：私有化部署（Docker 一键）+ API 限额
- **Agent 生态**：通过 MCP / OpenClaw 集成，让所有 AI Agent 都能调用

这种模式与 **Plausible（开源网站统计）**、**Cal.com（开源日程）** 类似：用开源抢占"基础设施"心智，赚钱靠托管 + 增值服务。

---

## 演进时间线（从 README 整理）

| 时间 | 里程碑 |
|------|--------|
| 2025-02-26 | v0.1.1：首个开源版本，支持小红书/抖音/快手/视频号一键发布 |
| 2025-09-16 | v1.0.18：首个出海版本，新增 Facebook/Instagram/Threads/X/YouTube/TikTok/Pinterest |
| 2025-11-12 | v1.3.2：首个"完全可用"的开源版本 |
| 2025-12-15 | v1.4.3：加入"超级 AI 智能 Agent"（All In Agent 战略） |
| 2026-02-07 | v1.8.0：新增线下商户推广解决方案 |
| 2026-03-26 | v2.1：内容交易市场上线 + OpenClaw 集成 + MCP 协议支持 |
| 2026-04-20 | OpenClaw 接收并执行 AiToEarn 赚钱任务 |
| 2026-05-21 | v2.4.0：HappyHorse 1.0 + Seedance 2.0 视频模型集成 |

可以看到，**2025 年 11 月"All In Agent"是分水岭**——从"工具"转向"Agent 平台"。

---

## 对国内独立开发者的启示

1. **MCP 是新的应用分发渠道**。2026 年起，所有 SaaS 工具都应该考虑提供 MCP server，否则会被"AI 工作流"边缘化。
2. **OpenClaw 这类 Agent 平台是新的流量入口**。和当年微信小程序、飞书应用一样，先发优势很重要。
3. **"内容工业化 + 跨境 + AI"** 是一个真实可付费的市场，不只是技术人自嗨。
4. **变现闭环（CPS/CPE/CPM）** 是 AiToEarn 与其他"AI 写文章"工具最大的差异点——它解决了"写出来之后呢"的问题。
5. **OPC（一人公司）** 是 2026 年互联网内容生产的核心组织形态。围绕 OPC 的工具栈（内容、财务、法律、税务、客服）都有机会。

---

## 链接

- GitHub 仓库: https://github.com/yikart/AiToEarn
- 官网 SaaS: https://www.aitoearn.ai/
- 中文文档：见 GitHub README 中文版
- 英文文档：https://github.com/yikart/AiToEarn/blob/main/README_EN.md
- 日文文档：https://github.com/yikart/AiToEarn/blob/main/README_JA.md
- 商业合作：aitoearn.ai 站内商务通道
- Trending Shift 页面：https://trendshift.io/repositories/20785

**开源协议**：MIT（极宽松，商用友好）
**主要语言**：TypeScript
**GitHub Trending**：2026-06-04 +320 stars
**核心团队**：yikart（深圳/广州团队）
