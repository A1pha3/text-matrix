---
title: "AiToEarn 源码解读：把'一段想法'变成'十几个平台的自动内容流水线'"
date: 2026-06-04T16:53:00+08:00
lastmod: "2026-09-24T10:00:00+08:00"
slug: aitoearn-ai-content-marketing-agent-guide
github_repo: "yikart/AiToEarn"
source_key: "gh:yikart/AiToEarn"
description: "yikart/AiToEarn 源码级解析：从一段中文创意到 14 平台自动发布+商单撮合的端到端架构。覆盖 MCP 双端点 35 个工具、OpenClaw 插件、Monetize/Publish/Engage/Create 四 Agent 拆解、Docker 自部署。"
draft: false
categories: ["技术笔记"]
tags: ["MCP", "OpenClaw", "AI Agent"]
hiddenFromHomePage: true
---

## 目录

- [先给判断](#先给判断)
- [学习目标](#学习目标)
- [系统总览：四 Agent 产品层，三个子项目代码层](#系统总览四-agent-产品层三个子项目代码层)
- [任务流：一条 MCP 工具链走完创作到发布](#任务流一条-mcp-工具链走完创作到发布)
- [MCP 接入：云端端点，不是本地包](#mcp-接入云端端点不是本地包)
- [常见问题](#常见问题)
- [采用建议与适用边界](#采用建议与适用边界)
- [自测与进阶路径](#自测与进阶路径)
- [参考来源与口径说明](#参考来源与口径说明)
- [链接与版本](#链接与版本)

---

## 先给判断

AiToEarn 把 **AI 内容生成、平台分发、商单变现** 三件事做在同一个仓库里，并以官网直接用、OpenClaw（龙虾）插件、Claude/Cursor 等 MCP 客户端、Docker 自部署、源码开发五种方式开放。它的定位介于"AI 写作工具"和"Buffer/Hootsuite 多平台定时发布器"之间——前者只管生成不管分发，后者只管分发不管生成，AiToEarn 把两端连同变现层一起打包。

**核心场景**：当一个 Agent（比如 Claude Code）写完一段产品介绍，它可以调 AiToEarn 的 MCP 工具生成多平台草稿，再创建发布流，让这段介绍以各自账号的状态出现在抖音、小红书、哔哩哔哩、视频号、YouTube、TikTok 等平台上；互动和结算环节也能在同一套体系里跑完。

版本口径：本文主体以 2026-05-21 发布的 v2.4.0 为基线；仓库迭代很快，MCP 工具清单、支持渠道数等标注了"2026-09-24 读数"的内容以当天 main 分支为准。仓库当前 26370 stars、4275 forks（2026-09-24 读数），MIT 协议，README 有中英日三语版本。

---

## 学习目标

读完本文，你应该能够：

1. **理解 AiToEarn 的定位**：说清它和"AI 写作工具""多平台发布器"的差异，以及它把哪三件事做在同一个仓库里。
2. **对应产品与代码**：把 README 里 Monetize / Publish / Engage / Create 四个 Agent 映射到仓库真实的三个子项目和后端服务模块上。
3. **解释 MCP 接入方式**：说清 AiToEarn 的 MCP 是云端端点而非本地包，以及 Claude Code / Cursor 接入后能调用哪些工具。
4. **评估适用场景**：面对"多平台运营团队""单平台品牌号""有接单需求的创作者"三类读者，能分别给出"先用/可以等等"的判断理由。
5. **独立跑通最小闭环**：用官方 SaaS 或 Docker 自部署，实际走一遍"输入创意 → 生成草稿 → 多平台发布"。

---

## 系统总览：四 Agent 产品层，三个子项目代码层

README 把能力切成四块：**Monetize / Publish / Engage / Create**。这是产品语言。代码层的真实结构是一个 monorepo，顶层 `project/` 目录下有三个子项目：

| 子项目 | 技术栈 | 职责 |
| --- | --- | --- |
| `project/aitoearn-backend` | Nx + pnpm（NestJS） | 两个应用：`aitoearn-server` 是对外 API 与 MCP 服务，`aitoearn-ai` 是草稿生成等 AI 能力服务 |
| `project/aitoearn-web` | Next.js + pnpm | Web 前端与官网 |
| `project/aitoearn-electron` | Electron | 桌面客户端 |

后端内部还有一层值得看的划分。`aitoearn-server` 的 `src/core/` 下是 api-key、assets、channels、content、publish-record、short-link、unified-mcp、user 八个模块——围绕"渠道账号、内容、发布记录"组织；`aitoearn-ai` 的 `src/core/` 下是 agent、ai、ai-availability、draft-generation、internal 五个模块——围绕"生成什么、用什么模型生成"组织。两个服务通过内部客户端调用互通，`draft-generation` 收到请求后返回任务 ID，生成过程异步完成。

四个 Agent 与代码的对应关系大致是：

| Agent | README 能力 | 代码侧落点 |
| --- | --- | --- |
| Create | 调用视频/图片模型生成内容，支持批量 | `aitoearn-ai` 的 `draft-generation` 与 `agent` 模块 |
| Publish | 一键分发到全球 10+ 平台，日历排期 | `aitoearn-server` 的 `channels`、`publish-record` 模块 |
| Engage | 浏览器插件自动点赞/收藏/关注，AI 回复评论 | `aitoearn-server` 的 engagement 相关接口 + 独立分发的浏览器插件 |
| Monetize | 创作者接商家推广任务，按 CPS/CPE/CPM 结算 | 主要在 SaaS 侧运营，开源仓库内没有独立的撮合服务模块 |

Monetize 这一行值得多说一句：README 给出的结算模式有三种——按成交额（CPS）、按互动量（CPE）、按播放量（CPM），结算以结果为导向。但在开源代码里找不到对应的撮合引擎模块，商单匹配与结算主要发生在官方 SaaS 侧。想要自建撮合能力的团队，不能假设这部分逻辑随开源仓库交付。

支持渠道方面，v2.4.0 的 README 列了 13 个：抖音、小红书（Rednote）、快手、哔哩哔哩、视频号、TikTok、YouTube、Facebook、Instagram、Threads、Twitter（X）、Pinterest、LinkedIn；2026-09-24 读数的 main 分支已加入微信公众号，共 14 个。

---

## 任务流：一条 MCP 工具链走完创作到发布

这一节用一个真实可跑的链路把系统串起来。链路上的每个工具都来自 `aitoearn-server` 源码里注册的 MCP 工具定义，不是示意。

### 第 1 步：生成草稿

创作者在 Claude Code 里说："用 AiToEarn 给我生成一条视频草稿，主题是新版本发布，重点讲对个人创作者的成本下降。"Agent 调用 `createVideoDraft` 工具。源码里的行为是：请求透传给 `aitoearn-ai` 的草稿生成服务，**立即返回任务 ID**，生成异步进行——工具描述原话是 "Returns task IDs, use getDraftTaskStatus to check progress"。

生成期间用 `getDraftTaskStatus` 轮询，状态机只有三态：generating、success、failed。成功后返回完整草稿内容。图文内容走对称的 `createImageTextDraft`。

v2.4.0 起草稿生成支持多模型选择：README 的版本动态明确写着"草稿生成新增支持 HappyHorse 1.0 和 Seedance 2.0，增强视频/图文草稿批量生成、多模型选择、参考图片/视频、目标平台限制与文案提示词"。README 在 Create 能力介绍里提到的模型还包括 Grok、Veo、Seedance（视频）与 Nano Banana（图片）。

### 第 2 步：创建发布流

草稿就绪后，`createChannelPublishFlow` 用 v2 版渠道输入格式创建一次发布流。发布前可以先用 `listChannelPlatforms` 看当前账号可用的平台，B 站和 YouTube 还有专门的分类查询工具（`listBilibiliChannelPlatformCategories`、`listYoutubeChannelPlatformCategories`），用于给内容挂分区。

发布时机有两种：`publishChannelTaskNow` 立即发，或 `updateChannelPublishAt` 改成定时——README 里"像排日程一样统一规划所有平台的内容发布时间"的日历排期，落到工具层就是这个接口。发完之后 `listChannelPublishRecords` 按 flowId、taskId 或 recordId 三种粒度查发布记录。

### 第 3 步：互动与数据回流

发布后进入长跑模式。`listChannelEngagementComments` 拉取评论，`submitChannelEngagementComment` 提交回复，`callChannelEngagementFunction` 执行点赞、收藏这类互动动作——这些是 Engage Agent 在工具层的真实形态，浏览器插件负责在各平台页面上落地执行。数据侧有 `getChannelAccountAnalytics`（账号维度）和 `getChannelWorkAnalytics`（作品维度）两个查询工具。

### 第 4 步：接商单（可选）

创作者在 SaaS 侧开启接单后，可以承接商家下发的推广任务，按 CPS/CPE/CPM 之一结算。2026-04-20 起，OpenClaw（龙虾）用户可以在龙虾里直接接收并执行这些变现任务——README 的演示场景是"在 OpenClaw 中执行 AiToEarn 赚钱任务"。这条链路的撮合逻辑在官方服务端，开源仓库里看不到。

---

## MCP 接入：云端端点，不是本地包

2026-03-26 的 v2.1 版本，AiToEarn 上线了 MCP 协议支持（同一次更新还上线了内容交易市场和 OpenClaw 支持）。MCP 是 Anthropic 2024 年底提出的工具调用协议，让 AI 工具能像调用函数一样调用外部服务。

这里有一个容易踩的认知坑：AiToEarn 的 MCP server **不是**一个 `npx` 启动的本地包，而是官方托管的云端端点。所有配置只需要两样东西——端点 URL 和 API Key 请求头：

| 配置项 | 值 |
| --- | --- |
| MCP 地址 | `https://aitoearn.ai/api/unified/mcp`（国际版）或 `https://aitoearn.cn/api/unified/mcp`（中国版） |
| 认证 Header | `x-api-key: 你的API-Key` |
| SSE 长连接 | 把路径里的 `mcp` 换成 `sse` |

Claude Desktop 的配置示例（README 原版）：

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

API Key 在 aitoearn.ai 或 aitoearn.cn 注册后，从"设置 → API Key"里创建。**中国版 Key 只能搭配 `aitoearn.cn` 的地址，国际版 Key 只能搭配 `aitoearn.ai` 的地址**，环境与 Key 不匹配会返回 401。自部署用户把域名换成自己的地址即可。

工具清单（2026-09-24 读数，main 分支）：统一端点 `unified` 下挂 13 个工具，覆盖草稿生成（createVideoDraft、createImageTextDraft、getDraftTaskStatus）与内容管理（createDraft、listDrafts、deleteDraft、listMedia 等）；另有独立的 `channels` 端点挂 22 个工具，覆盖发布流、互动与数据分析。合计 35 个。上一节的任务流就是按这批工具的真实定义写的。

OpenClaw 是另一条接入路径：在服务器终端运行 `npx -y @aitoearn/openclaw-plugin-cli` 安装插件，选择环境并填入对应 Key 之后，OpenClaw 里就能直接接收并执行 AiToEarn 的赚钱任务。它与 MCP 的分工是——MCP 让你的 Agent 主动调用 AiToEarn 的能力，OpenClaw 插件让 AiToEarn 的任务找到你的 Agent。

自部署只要三条命令：

```bash
git clone https://github.com/yikart/AiToEarn.git
cd AiToEarn
docker compose up -d
```

启动后打开 `http://localhost:8080`。compose 文件编排了 10 个服务：mongodb（含副本集初始化）、redis、rustfs（本地 S3 兼容对象存储）、aitoearn-ai、aitoearn-server、aitoearn-web、nginx，外加三个一次性初始化任务；数据库不需要手动装。

---

## 常见问题

**Q1：内容会被平台判定为 AI 生成吗？**

各平台对 AI 内容的政策不同，AiToEarn 的发布链路产出的是草稿，发布前可以人工二次编辑。如果你的平台对 AI 内容有严格限制，把人工 review 作为固定步骤加进流程，比事后补救可靠。

**Q2：中国版和国际版有什么区别？**

两个独立环境：中国版 aitoearn.cn，国际版 aitoearn.ai。账号、API Key、MCP 地址都不互通，Key 配错环境直接 401。功能面基本一致，选哪个取决于你的目标平台和账号体系在哪边。

**Q3：商用有什么限制？**

仓库用 MIT 协议，允许商用，没有附加条款。需要注意的反而是运营层面：商单撮合与结算跑在官方 SaaS 侧，自部署拿到的是内容生成与分发能力，不含撮合网络。

**Q4：HappyHorse 1.0 和 Seedance 2.0 是什么？**

v2.4.0 新增的两个草稿生成可选模型，出处是 README 的版本动态原文，README 没有给出它们与其他模型的对比数据。想评估效果，最直接的办法是在草稿生成时分别指定模型跑同一段提示词对比。

**Q5：自部署版和 SaaS 版差在哪？**

自部署包含完整的生成、发布、互动接口和 Web 界面，数据留在自己服务器；内容交易市场、商单撮合这些需要多方参与的能力在官方 SaaS 侧。另外自部署要自己在配置管理里处理各发布平台的 OAuth 授权，或者配置 Relay 借用官方凭据（详见 README 的 Docker 部署一节）。

---

## 采用建议与适用边界

### 谁该先用

- **多平台内容运营团队**：已经在 5 个以上平台手动维护账号，每周重复"改写-排版-发布"流程，AiToEarn 的草稿批量生成加日历排期能把这部分工时压下来。
- **AI Agent 开发者**：需要在 Agent 工作流里嵌入"发布到社交平台"能力。MCP 端点现成，35 个工具覆盖从生成到数据查询的完整链路，接入成本接近零。
- **有接单需求的创作者**：官方 SaaS 的撮合层和 OpenClaw 的变现任务通道是现成的赚钱入口，CPS/CPE/CPM 按结果结算。

### 谁可以等等

- **单平台运营者**：只做小红书或只做 YouTube，平台官方后台更可控，多平台分发的价值发挥不出来。
- **对内容原创性要求极高的品牌**：批量生成的草稿即使人工 review，仍需要为品牌调性付出额外校对成本。
- **数据合规敏感的团队**：用 SaaS 意味着内容与账号数据经过官方服务；自部署可以缓解，但撮合类能力又必须回到 SaaS。两头都要的场景需要先做合规评估。

### 接入顺序建议

1. 先在官网注册，用 SaaS 跑通"创作 → 发布"最小闭环，验证内容质量是否达标
2. 再配 MCP 端点，把发布能力嵌进现有 Agent 工作流
3. 有变现诉求再评估商单撮合，这一步涉及资金流，条款看清楚再开
4. 需要数据私有再自部署，从 `docker compose up -d` 三条命令起步

---

## 自测与进阶路径

### 自测问题

1. 如果一个创作者只想运营小红书一个平台，他应该用 AiToEarn 还是直接用小红书官方后台？为什么？
2. MCP 接入和 OpenClaw 插件的分工差异是什么？什么场景下必须用后者？
3. Monetize 在产品语言里是"第四个 Agent"，在开源代码里它的真实形态是什么？
4. `createVideoDraft` 返回任务 ID 而不是直接返回草稿，这个设计对 Agent 侧的调用流程意味着什么？

### 进阶路径

- **源码层面**：从 `project/aitoearn-backend/apps/aitoearn-server/src/core/unified-mcp/` 入手，看 MCP 工具如何注册与透传；再看 `apps/aitoearn-ai/src/core/draft-generation/` 理解异步生成
- **协议层面**：读 Anthropic 官方 MCP 规范（modelcontextprotocol.io），对比 AiToEarn 的 `libs/nest-mcp` 封装
- **部署层面**：从 `docker-compose.yml` 入手，理清 10 个服务的依赖关系与 rustfs 对象存储的角色
- **业务层面**：注册账号实际跑通"创作 → 发布 → 接单 → 结算"完整链路

---

## 参考来源与口径说明

1. **主要信源**：yikart/AiToEarn 仓库 v2.4.0 tag（74e884f，2026-05-21）与 main 分支源码、README（中/英/日）、`DOCKER_DEPLOYMENT_CN.md`、`AGENTS.md`，GitHub API 仓库元数据。核实日期 2026-09-24。
2. **版本口径**：主体描述以 v2.4.0 为基线；MCP 工具数（35）、支持渠道数（14）、compose 服务数为 main 分支 2026-09-24 读数，与 v2.4.0 时点存在差异处已注明（v2.4.0 支持 13 渠道）。v2.5.0（2026-06-24）起 Relay 配置从 compose 文件移到配置管理界面，并新增开放平台（docs.aitoearn.cn）。
3. **数字来源**：stars/forks 为 2026-09-24 GitHub API 读数；四 Agent 能力描述、结算模式、平台清单、5 种使用方式均转述 README 原文；MCP 工具清单逐一取自源码中注册的工具定义。本文不含未经复测的性能与耗时数字。
4. **边界**：浏览器插件本体不在开源仓库内（仓库只有插件指南素材），分发渠道以官方文档为准；商单撮合与结算的服务端实现不开源，文中仅描述产品层行为。

---

## 链接与版本

- **GitHub 仓库**：https://github.com/yikart/AiToEarn
- **官网**：https://www.aitoearn.ai/（国际版）、https://aitoearn.cn/（中国版）
- **开放平台文档**：https://docs.aitoearn.cn/
- **英文 README**：https://github.com/yikart/AiToEarn/blob/main/README_EN.md
- **日文 README**：https://github.com/yikart/AiToEarn/blob/main/README_JA.md
- **TrendShift**：https://trendshift.io/repositories/20785
- **基线版本**：v2.4.0（2026-05-21）；最新 release v2.5.0（2026-06-24）
- **开源协议**：MIT
- **主要语言**：TypeScript
- **仓库读数**：26370 stars / 4275 forks（2026-09-24）

---

**延伸阅读**：AiToEarn 的 MCP 接入方式与站内另一篇同类项目解读可以对照着看——{{< relref "ai-agent/xiaohongshu-mcp-xiaohongshu-model-context-protocol-guide.md" >}}（小红书 MCP，同样走"AI 工具直连社交平台"的路线）；想深入 MCP 协议本身，见 {{< relref "ai-agent/anthropic-claude-api-mcp.md" >}}。
