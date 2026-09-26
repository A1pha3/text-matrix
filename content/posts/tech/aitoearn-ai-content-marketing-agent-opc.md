---
title: "AiToEarn：OPC 的 AI 全平台内容营销智能体"
date: 2026-05-14T12:05:00+08:00
lastmod: 2026-09-24T12:00:00+08:00
slug: "aitoearn-ai-content-marketing-agent-opc"
github_repo: "yikart/AiToEarn"
source_key: "gh:yikart/AiToEarn"
description: "AiToEarn 是一款面向 OPC（一人公司）的 AI 内容营销工具，通过 AI Agent 自动化实现内容创作、多平台分发、互动运营和变现结算。本文解析其四大核心 Agent 能力（Monetize/Publish/Engage/Create）、API 接入方式和变现模式。"
categories: ["技术笔记"]
tags: ["AI Agent", "抖音", "小红书", "TypeScript"]
---

## 快速信息卡

| 指标 | 数值 |
|------|------|
| Stars | 26,391+ |
| Forks | 4,282+ |
| 许可证 | MIT |
| 语言 | TypeScript |
| 最新版本 | v2.5.0（2026-06-24） |
| 官网 | https://aitoearn.ai / https://aitoearn.cn |
| 仓库 | [yikart/AiToEarn](https://github.com/yikart/AiToEarn) |

## 学习目标

读完本文，你应该能够：

1. **理解 AiToEarn 的核心定位**：明白它如何把 AI Agent 能力接进内容营销的四个环节
2. **掌握四大核心能力**：Monetize / Publish / Engage / Create 各自解决什么问题
3. **选择接入方式**：网站、OpenClaw 插件、MCP 协议、Docker、源码，哪种适合你
4. **评估适用性**：判断你的场景是否适合用 AiToEarn，以及用哪部分能力
5. **避开常见坑**：多平台分发时的内容适配、结算模式选择、账号风险管理

## 目录

1. [项目概览](#项目概览)
2. [核心定位](#核心定位)
3. [四大核心 Agent](#四大核心-agent)
   - [Monetize —— 内容赚钱](#monetize--内容赚钱)
   - [Publish —— 多平台分发](#publish--多平台分发)
   - [Engage —— 自动化互动运营](#engage--自动化互动运营)
   - [Create —— AI 内容创作](#create--ai-内容创作)
4. [接入方式](#接入方式)
5. [技术架构](#技术架构)
6. [版本历史](#版本历史)
7. [适用场景](#适用场景)
8. [常见问题与故障排查](#常见问题与故障排查)
9. [自测题](#自测题)
10. [进阶路径](#进阶路径)
11. [总结](#总结)

---

## 项目概览

[yikart/AiToEarn](https://github.com/yikart/AiToEarn) 是一个面向内容创作者和 OPC（一人公司）的 AI 全平台内容营销智能体，2025 年 2 月开源，当前已获得 **26,391+ 颗 Stars** 和 4,282+ 个 Forks，采用 MIT 许可证，主要语言为 TypeScript。

官网：https://aitoearn.ai（国际版）/ https://aitoearn.cn（中国版）

## 核心定位

AiToEarn 的 slogan 是「**Monetize · Publish · Engage · Create**」，按官方的说法，它通过 AI Agent 自动化，帮助 OPC（一人公司）、创作者、品牌与企业在全球主流平台上构建、分发并变现内容。目标用户是：

- 想一个人运营多个平台矩阵的创作者
- 需要降低内容生产成本的 SMB
- 希望将社媒运营自动化的品牌方

## 四大核心 Agent

### Monetize —— 内容赚钱

官方把「帮助每一位创作者赚钱」列为最核心的目标。创作者在平台的内容交易市场承接商家的推广任务，所有结算以结果为导向，共三种结算模式：

| 结算模式 | 全称 | 含义 |
|---------|------|------|
| **CPS** | Cost Per Sale | 按成交额结算 |
| **CPE** | Cost Per Engagement | 按互动量结算 |
| **CPM** | Cost Per Mille | 按播放量结算 |

「按效果付费」降低了商家的投放风险，也给创作者一条更清晰的变现路径。

### Publish —— 多平台分发

一键将内容分发到全球 14 个主流平台：

**国内**：抖音、快手、B 站、小红书、视频号、微信公众号  
**海外**：TikTok、YouTube、Facebook、Instagram、Threads、X（Twitter）、Pinterest、LinkedIn

支持日历排期，像排日程一样统一规划所有平台的发布时间，不用逐个平台手动操作。

### Engage —— 自动化互动运营

通过 AiToEarn 浏览器插件，在上述所有平台上实现自动化互动：

- **自动化操作**：自动点赞、收藏、关注，批量高效运营
- **AI 智能回复**：调用大模型为每条评论生成针对性回复
- **评论挖掘**：识别「求链接」「怎么购买」等高转化信号，快速响应
- **品牌监测**：实时追踪关于品牌的讨论，主动参与热点话题

### Create —— AI 内容创作

用 Agent 方式重构内容制作流程：告诉 Agent 你的需求，它自动完成从创意到成品的全部工作。

- **视频**：自动调用视频生成模型（Grok、Veo、Seedance 等）、视频翻译模块和剪辑模块，一站式出片；v2.4 起草稿生成还支持 HappyHorse 1.0 与 Seedance 2.0
- **图文**：调用 Nano Banana 等图片模型生成图文（2025 年 11 月起含 Nano Banana Pro）
- **批量生成**：批量下发创作任务，并行产出多条内容，适合矩阵账号运营和大规模分发

## 接入方式

官方提供 5 种使用方式。注意：**方式二、三、四都需要先获取 API Key**，且只需获取一次、所有方式通用——在官网注册登录后，进入「设置 → API Key」创建即可。

### 方式一：直接使用（网站）

🌍 国际版：https://aitoearn.ai  
🇨🇳 中国版：https://aitoearn.cn

### 方式二：OpenClaw（龙虾）插件

[OpenClaw](https://github.com/openclaw/openclaw) 是一个开源个人 AI 助理，社区俗称「龙虾」。AiToEarn 为它提供了官方插件，安装后可以在 OpenClaw 中直接接收并执行 AiToEarn 的赚钱任务。

在运行 OpenClaw 的服务器终端执行：

```bash
npx -y @aitoearn/openclaw-plugin-cli
```

首次运行会让你选择环境（中国版/国际版）并输入对应的 API Key。环境与 Key 必须匹配——用 aitoearn.cn 的 Key 配国际版环境会直接返回 401。

### 方式三：MCP 协议（Claude / Cursor 等）

AiToEarn 支持标准 MCP 协议，可在任何兼容 MCP 的 AI 助手中使用。认证通过 HTTP Header `x-api-key` 传递：

| 环境 | MCP 地址 | SSE 地址 |
|------|---------|---------|
| 中国版 | `https://aitoearn.cn/api/unified/mcp` | `https://aitoearn.cn/api/unified/sse` |
| 国际版 | `https://aitoearn.ai/api/unified/mcp` | `https://aitoearn.ai/api/unified/sse` |

以 Claude Desktop 为例，在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "aitoearn": {
      "type": "http",
      "url": "https://aitoearn.ai/api/unified/mcp",
      "headers": {
        "x-api-key": "你的API-Key"
      }
    }
  }
}
```

Cursor 在 MCP 设置里填同样的地址和 Header 即可。自部署用户把 `aitoearn.ai` 换成自己的部署地址（如 `localhost:8080`）。

### 方式四：Docker 私有化部署

3 条命令起一套完整服务，无需手动安装数据库：

```bash
git clone https://github.com/yikart/AiToEarn.git
cd AiToEarn
docker compose up -d
```

启动后访问 http://localhost:8080，首次启动会自动创建管理员账号并登录。官方要求 Docker 20.10+ 和 Docker Compose 2.0+，建议 4GB 内存、20GB 磁盘空间。

**配置 Relay（强烈推荐）**：发布内容需要登录各社交平台的账号，而这些平台的 OAuth 授权要求开发者凭据。自部署若不配 Relay，就得去十几个平台逐一申请开发者账号；配上 Relay，则借用官方 aitoearn.ai 的凭据完成授权，一个 API Key 覆盖所有平台。v2.5 起 Relay 在网页的「配置管理」界面里配置，拆成两路：Server Relay 用于发布平台授权，AI Relay 用于调用平台提供的 AI 模型。完整部署指引见仓库内的 `DOCKER_DEPLOYMENT_CN.md`。

### 方式五：源码开发

仓库是 monorepo，`project/` 目录下三个子项目：

- **aitoearn-backend**：NestJS 后端，含主后端 `aitoearn-server` 与 AI 服务 `aitoearn-ai` 两个应用，pnpm + nx 管理
- **aitoearn-web**：Next.js 前端
- **aitoearn-electron**：Electron 桌面客户端

本地开发时用 Docker 跑 MongoDB/Redis 即可，具体步骤见 README 的「源码开发」一节。

## 技术架构

整体分层比较直接：NestJS 后端负责业务与 AI 调度，Next.js Web 前端和 Electron 桌面客户端两个入口，数据层是 MongoDB 加 Redis，对象存储用 S3 兼容的 RustFS，Docker 部署时由 Nginx 做 8080 统一入口。

对外能力有三条通道：网站直接用；MCP 协议接入 AI 助手；开放平台 API（2026 年 6 月随 v2.5 上线，文档在 docs.aitoearn.cn），一套 API 覆盖内容生成、模型调用、账号授权、素材上传和多平台发布，以 `X-Api-Key` 鉴权。互动运营则由浏览器插件在各平台上执行。

与各平台的对接统一走 OAuth 授权：官方托管版和配置了 Relay 的自部署版共用官方凭据。发布链路按「读取平台元数据 → 账号授权 → 拉取平台发布选项 → 上传素材 → 创建发布 Flow → 查询发布记录」推进。AI 生成侧由 aitoearn-ai 服务统一调度视频、图片模型，自部署用户也可以在配置管理里直接填 OpenAI、Gemini、Anthropic 自己的 Key 和地址。

## 版本历史

- **v2.5（2026-06-23）**：Relay 拆分为 Server Relay 与 AI Relay，迁移到配置管理界面；新增开放平台（docs.aitoearn.cn）
- **v2.4（2026-05-21）**：草稿生成支持 HappyHorse 1.0 与 Seedance 2.0，增强视频/图文批量生成、多模型选择、参考图片/视频；全新界面，增强 X 探索与互动
- **2026-04-20**：OpenClaw 新增赚钱支持，可在龙虾中直接接收并执行内容变现任务
- **v2.1（2026-03-26）**：内容交易市场上线；新增 OpenClaw 支持与 MCP 协议支持
- **v1.8（2026-02-07）**：线下商户推广解决方案（餐厅、零售、民宿等），把线下推广活动转化为可执行的线上传播任务
- **v1.4.3（2025-12-15）**：「All In Agent」——加入自动内容生成、发布与操作 AiToEarn 的超级 AI Agent
- **v1.4.0（2025-11-28）**：应用内自动更新；创作界面新增缩写、扩写、图片生成、视频生成、标签生成，支持 Nano Banana Pro
- **v1.3.2（2025-11-12）**：首个开源且可完全使用的版本
- **v1.0.18（2025-09-16）**：首个出海版本，新增 Facebook、Instagram、Threads、X、YouTube、TikTok、Pinterest
- **v0.1.1（2025-02-26）**：首个开源版本，初步实现小红书、抖音、快手、视频号一键发布

从这条时间线能看到产品的重心迁移：先做一键发布工具，再往 Agent 自动化走，v2.1 上线内容交易市场后开始向生态平台扩展。

## 适用场景

- **个人创作者**：一个人管多个平台，靠 Agent 提升效率
- **品牌方**：统一管理多平台内容投放，监控互动数据
- **MCN 机构**：批量运营矩阵账号，提升内容产出量
- **线下商户**：通过内容营销获取到店流量（v1.8 起有专门方案）

---

## 常见问题与故障排查

### Q1：AiToEarn 会违反平台规则吗？

**A**：这取决于具体平台的内容政策和自动化程度。抖音、小红书等平台对自动化操作有严格限制，建议：

- 先手动测试少量内容，观察账号状态
- 不要短时间内大量发布相同或相似内容
- 使用「人工审核 + Agent 辅助」模式，而不是完全自动化

### Q2：MCP 协议接入需要编程基础吗？

**A**：需要基本的 API 调用能力。如果你用的是 Claude Desktop 或 Cursor，只需要在配置文件中添加 MCP 地址和 API Key，不需要写代码。但要做深度集成，还是需要了解 MCP 协议的基本结构。

### Q3：CPS / CPE / CPM 哪种结算模式更适合新手？

**A**：建议从 CPE 或 CPM 开始：

- **CPE（按互动量结算）**：门槛低，只要内容有互动就能赚钱，适合测试内容质量
- **CPM（按播放量结算）**：适合已经有稳定流量的账号
- **CPS（按成交额结算）**：需要更强的转化能力，建议有经验后再尝试

### Q4：多平台分发时，内容需要针对每个平台调整吗？

**A**：需要。虽然 AiToEarn 支持一键分发，但不同平台的：

- **内容规范不同**：各平台对视频时长、画幅、文件大小的限制不一样，竖屏为主的短视频平台和横屏为主的 B 站，对同一素材的适配要求完全不同
- **推荐机制不同**：各平台的分发逻辑不同，同一内容在不同平台的反馈可能差异很大
- **用户预期不同**：B 站用户接受长视频，抖音用户偏好快节奏

建议先用 Agent 生成「适配后的内容」，而不是直接一模一样地发到所有平台。

### Q5：OpenClaw 插件和 MCP 协议有什么区别？

**A**：先澄清一个容易混淆的点：OpenClaw 不是浏览器插件，而是一个开源个人 AI 助理，自己跑在服务器或电脑上；AiToEarn 的 OpenClaw 插件装在这个助理里，让它直接接收并执行赚钱任务。做互动运营的浏览器插件是另一个东西，别混淆。

| 对比项 | OpenClaw 插件 | MCP 协议 |
|--------|--------------|----------|
| **宿主** | OpenClaw 个人 AI 助理 | 任何 MCP 兼容的 AI 助手（Claude Desktop、Cursor 等） |
| **安装方式** | 在服务器终端跑 `npx` 命令 | 在 AI 助手配置里填地址和 API Key |
| **适用场景** | 想让助理自动接收并执行变现任务 | 想在自己的工作流里按需调用 |
| **灵活性** | 任务由 AiToEarn 下发 | 高，可自定义调用具体工具 |

---

## 自测题

### 问题 1：AiToEarn 的四大核心 Agent 中，哪个负责「按效果结算」？

A. Publish  
B. Monetize  
C. Engage  
D. Create  

<details>
<summary>查看答案</summary>
<b>答案：B</b><br>
Monetize 对应内容交易市场，支持 CPS / CPE / CPM 三种结算模式，核心是按效果付费。
</details>

### 问题 2：如果你想在 Claude Desktop 中使用 AiToEarn，应该选哪种接入方式？

A. 网站直接使用  
B. OpenClaw 插件  
C. MCP 协议  
D. Docker 私有化部署  

<details>
<summary>查看答案</summary>
<b>答案：C</b><br>
MCP 协议是标准协议，Claude Desktop 兼容 MCP，只需要在配置中添加 AiToEarn 的 MCP 地址和 API Key。
</details>

### 问题 3：多平台分发时，为什么不能把所有平台的内容弄得一模一样？

<details>
<summary>查看答案</summary>
<b>答案要点</b>：<br>
1. 各平台内容规范不同（时长、比例、格式）<br>
2. 推荐机制不同，同一内容的反馈差异可能很大<br>
3. 用户预期不同（B 站接受长视频，抖音偏好快节奏）<br>
4. 一模一样的内容可能被平台判定为「搬运」或「垃圾内容」
</details>

### 问题 4：如果你的账号被平台限流了，应该从哪些方面排查？

<details>
<summary>查看答案</summary>
<b>答案要点</b>：<br>
1. 检查是否短时间内发布大量内容<br>
2. 检查内容是否过于相似（被判定为搬运）<br>
3. 检查是否有违规词（政治、色情、暴力、导流）<br>
4. 检查互动是否异常（突然大量点赞/评论，可能是刷量）<br>
5. 查看平台站内信，看是否有违规通知
</details>

### 问题 5：为什么说 AiToEarn 适合 OPC（一人公司），但不一定适合大团队？

<details>
<summary>查看答案</summary>
<b>答案要点</b>：<br>
<strong>适合 OPC 的原因</strong>：<br>
1. 一个人运营多个平台，靠 Agent 提升效率<br>
2. 不需要招运营团队，降低成本<br>
3. 快速测试内容方向，灵活调整<br>

<strong>不一定适合大团队的原因</strong>：<br>
1. 大团队通常有固定的内容审核流程，完全自动化可能跳过审核<br>
2. 品牌方对内容质量和安全有更高要求，需要人工把控<br>
3. 多平台分发需要统一的品牌调性，Agent 生成的内容可能不一致
</details>

---

## 进阶路径

### 阶段 1：快速体验（1-2 天）

- [ ] 注册 AiToEarn 账号（国际版或中国版）
- [ ] 手动发布一篇内容到 1-2 个平台，熟悉流程
- [ ] 查看内容交易市场的任务列表，了解变现模式

### 阶段 2：Agent 辅助（1 周）

- [ ] 安装浏览器插件，体验自动化互动
- [ ] 用 Create Agent 生成 5-10 条内容，测试质量
- [ ] 用 Publish Agent 分发到 3-5 个平台，观察数据
- [ ] 有 OpenClaw 环境的话，装插件试一次赚钱任务的接收与执行

### 阶段 3：MCP 集成（2-4 周）

- [ ] 获取 API Key
- [ ] 在 Claude Desktop / Cursor 中配置 MCP 协议
- [ ] 用 AI 助手调用 AiToEarn 的 MCP 工具，实现工作流集成

### 阶段 4：深度定制（1-3 个月）

- [ ] 阅读源码，理解 Agent 的实现逻辑
- [ ] 基于 AiToEarn 做二次开发（如自定义内容模板、接入私有平台）
- [ ] 用 Docker 私有化部署，数据完全自主

### 进阶资源

- [AiToEarn 开放平台文档](https://docs.aitoearn.cn)（API 接入、模型调用、发布链路）
- [AiToEarn 国际版文档](https://docs.aitoearn.ai/en/home)
- [MCP 协议规范](https://modelcontextprotocol.io)
- 仓库内部署文档：`DOCKER_DEPLOYMENT_CN.md`

---

## 总结

AiToEarn 把内容营销的四个环节（创作、分发、互动、变现）各自做成独立的 Agent，你可以只用一个环节，也可以串起来跑完整流程。

值得注意的三个点：

1. **多平台分发不等于内容复制**：各平台的推荐机制和用户预期不同，用 Publish Agent 时要针对每个平台调整内容格式和时长
2. **结算模式影响内容策略**：CPS 要求内容有强转化能力，CPM 要求内容有高播放量，选结算模式时要先想清楚内容定位
3. **自动化程度要循序渐进**：先从手动发布开始，观察账号状态，再逐步引入 Agent 辅助，避免被平台判定为搬运或刷量

如果你已经有稳定的内容生产能力，但苦于多平台分发的执行成本，AiToEarn 的 Publish + Engage 能直接减少重复劳动。如果你是新手，建议先从内容交易市场的 CPE 任务开始，用平台的流量测试内容质量，再决定是否深度投入。

仓库：https://github.com/yikart/AiToEarn  
官网：https://aitoearn.ai

---

## 参考来源与口径说明

- Stars 26,391、Forks 4,282、MIT、TypeScript、创建时间：GitHub API，2026-09-24 复核
- 五种接入方式、API Key 获取步骤、MCP/SSE 地址与 `x-api-key` 认证、OpenClaw 插件安装与 401 提示、Docker 部署命令、Relay 机制、版本时间线：仓库 README 与 `DOCKER_DEPLOYMENT_CN.md`（main 分支 2026-09 快照）
- 服务架构（Nginx :8080、Next.js :3000、NestJS :3002/:3010、MongoDB、Redis、RustFS）与部署前置要求：`DOCKER_DEPLOYMENT_CN.md`
- 开放平台能力与发布链路六步：docs.aitoearn.cn，2026-09-24 访问
- OpenClaw 定位（开源个人 AI 助理）：openclaw/openclaw 仓库
- 平台渠道：README 渠道列表实际列出 14 个平台，官方口径写「全球 10+ 主流平台」，正文按 14 个逐一列出
- README「源码开发」一节仍写克隆 `AttAiToEarn`，该地址已 301 重定向回主仓库；Electron 代码现位于主仓库 `project/aitoearn-electron`
