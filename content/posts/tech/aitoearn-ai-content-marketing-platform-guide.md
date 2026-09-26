---
title: "AiToEarn：一人公司 AI 内容营销自动化平台"
date: "2026-05-14T10:53:00+08:00"
lastmod: "2026-09-25T11:30:00+08:00"
slug: "aitoearn-ai-content-marketing-platform-guide"
github_repo: "yikart/AiToEarn"
source_key: "gh:yikart/AiToEarn"
description: "AiToEarn 把 AI 创作、多平台分发、评论互动和商单结算放进同一条内容流水线。本文对照官网、README、部署文档与后端源码，拆清四块能力的真实边界、Claude Agent SDK 构成的 Agent 内核、35 个对外 MCP 工具覆盖到哪一步，以及 Docker 自部署在 v2.5.0 之后的配置方式。"
draft: false
categories: ["技术笔记"]
tags: ["MCP", "OpenClaw", "内容营销", "Docker", "AI Agent"]
toc: true
---

## 快速信息卡

| 项目 | 内容 |
| ---- | ---- |
| 热度 | Stars 26,407、Forks 4,286（2026-09-25 取自 GitHub 仓库数据） |
| 最新版本 | v2.5.0（2026-06-24 发布），仓库最近一次推送 2026-09-18 |
| 许可证 | MIT |
| 主要语言 | TypeScript，约占代码量 84% |
| 产品入口 | https://aitoearn.ai （国际版）/ https://aitoearn.cn （中国版） |
| 仓库 | [yikart/AiToEarn](https://github.com/yikart/AiToEarn) |

## 先给判断

AiToEarn 值得看的地方，不在于它能发小红书和 TikTok，而在于它把创作、分发、互动、结算这四件事接成了同一条链。发内容只是入口，链路的后半段——谁在评论区问了价格、这条内容按什么规则结钱——才是它和排期工具分开的地方。

这个定位决定了它的重量。做矩阵账号、跨平台分发，或者想把 AI 助手挂到发布链路上的人，会觉得它比拼装四五个单点工具省事；一个月发三条内容的人，它会明显偏重。

README 给它的定义是"OPC（一人公司）的 AI 内容营销智能体"，面向一人公司、创作者、品牌和企业，用 AI Agent 自动化把内容在全球主流平台上构建、分发并变现。

## 四块能力各自补的是哪一段

README 把能力分成 Monetize、Publish、Engage、Create 四块。放进实际工作流里对照，边界会清楚很多：

| 环节 | 补的是哪一段 | 公开列出的能力 | 前提与限制 |
| ---- | ---- | ---- | ---- |
| Create | 内容从哪来 | 告诉 Agent 需求后生成视频或图文草稿；视频链路调用 Grok、Veo、Seedance 等模型以及视频翻译、剪辑模块；图文调用 Nano Banana；支持批量下发任务并行生成 | 可选项取决于你接了哪些模型服务商，或是否走 AI Relay |
| Publish | 内容怎么发出去 | 分发到 14 个平台：抖音、小红书、快手、哔哩哔哩、视频号、公众号、TikTok、YouTube、Facebook、Instagram、Threads、X、Pinterest、LinkedIn；日历排期统一管理各平台发布时间 | 每个平台要先完成账号授权 |
| Engage | 发出去之后谁盯评论 | 自动点赞、收藏、关注；为每条评论生成 AI 回复；识别"求链接""怎么购买"这类高转化信号；品牌监测 | README 明确写这部分通过浏览器插件在各平台上完成，不是纯服务端能力 |
| Monetize | 内容怎么换钱 | 内容交易市场接任务；CPS（Cost Per Sale，按成交额）、CPE（Cost Per Engagement，按互动量）、CPM（Cost Per Mille，按播放量）三种结算 | 依附前三步跑通，结算口径由任务方给出 |

Engage 这一行的信息量比表面看起来大。多数同类工具把这一步写成"AI 自动回复评论"，AiToEarn 的 README 说得更具体：自动化互动通过浏览器插件完成。也就是说它走的是"接管人在平台上的操作"这条路，而不是平台开放接口。差别落在两处——插件依赖账号登录态和页面结构，平台一改版、登录态一过期，这一步就先坏；接口路径则受平台配额和审核约束，稳定性来自接口本身。两条路的失败方式不同，这会影响你怎么排运维预期。

## 为什么它比排期工具重

排期工具的起点通常是"内容已经写好"。AiToEarn 的起点在更前面，终点在更后面，于是它必须接手三件排期工具不必处理的事：内容本身的生产、发布后的评论互动、以及和广告主之间的结算。

结果是入口收敛了，复杂性没有消失，只是集中到了认证、配置和调度这几处。你越往深用，越会碰到账号授权、平台规则、API Key（应用程序接口密钥）的环境匹配、自部署配置这些问题。它省的是"在五六个工具之间来回切换"，换进来的是"一套需要认真配的系统"。

## 代码里的 Agent 是什么

README 说了四块能力，没说这四块靠什么跑。打开 `project/aitoearn-backend`，内核是一组可以直接指认的部件。

`apps/aitoearn-ai/src/core/agent/services/agent-runtime.service.ts` 从 `@anthropic-ai/claude-agent-sdk` 引入 `query` 与 `createSdkMcpServer`：`query()` 负责发起一次 Agent 会话，进程启动交给自定义的 `spawn` 钩子，日志里把退出事件写成 "Claude Code process exited"。每个生成任务有自己的工作目录 `<cwd>/.claude-session/tasks/<taskId>`，会话状态按任务隔离。

`core/agent/skill-init.service.ts` 在模块初始化时，把 13 个技能目录复制到 `.claude-session/.claude/skills`：

```text
generating-images      generating-videos     editing-videos
editing-images         transferring-video-styles
generating-drama-recaps composing-videos     translating-videos
removing-subtitles     analyzing-videos
managing-content       crawling-social-media extracting-thumbnails
```

每个目录里是一份 `SKILL.md`，写的是这个能力怎么用、用哪个模型、什么情况该换路径。以 `generating-videos` 为例，它声明用 Grok 做文生视频和图生视频，正文给了一张选择表：单次生成上限 15 秒，超过 15 秒的内容拆成多段生成，再加载 `editing-videos` 把片段接起来。

工具侧是 9 个进程内 MCP server 文件（`core/agent/mcp/`），封装媒体上传下载、字幕、图片编辑、视频剪辑、风格迁移、剧集回顾等能力，其中 `mcp/volcengine/` 一组对接火山引擎。

模型来源由 `core/agent/claude-code-router/` 处理：它 `spawn` 一个 `@musistudio/claude-code-router` 的 CLI（命令行工具）子进程，把后端地址、密钥和模型列表写成一份路由配置，按 `default`、`background`、`think` 三档分别指定模型，`transformer` 一项写成 Anthropic。部署文档让你在「AI → 模型服务商」里自行填写 OpenAI、Gemini、Anthropic 等服务商的密钥与接口地址，指的就是这一层。

把这几块拼起来，Create 环节的实现路径并不神秘：**Claude Agent SDK（软件开发工具包）驱动下的 Claude Code 充当推理与调度内核，SKILL.md 提供领域做法，MCP 工具提供动手能力的入口**。这也能解释一类容易被当成"模型不稳"的现象——生成质量与 Claude Code 的行为绑得比较紧，换模型服务商实际换的是内核背后的推理端，skills 和工具面并不跟着变。

## 一条任务跑完整个系统

假设你在做一个出海 SaaS（软件即服务）产品，今天刚发了新版本。要做的不是"写一条更新公告"，而是今晚把这次更新同步到小红书、TikTok、YouTube Shorts 和 LinkedIn，并在评论区接住问价格的人。

1. Create：把版本信息、卖点、目标受众交给 Agent，拿到的是各平台可以继续改写的多条草稿。批量下发时，任务交给 `draft-generation` 的 consumer 承接，状态可以回查。
2. Publish：同一批素材进不同平台时，标题长度、标签、内容结构和发布时间跟着平台特性走，日历排期统一看。
3. Engage：发出后盯评论，AI 针对每条生成回复，"求链接""怎么购买"这类信号被挑出来优先处理。
4. Monetize：如果这条内容接的是平台任务，结算按任务方指定的那一种——CPS、CPE 或 CPM。

顺序反不了。Monetize 依附于前三步：没有发布就没有互动，没有互动数据就没有按互动量结算的依据。

## 五条接入路径，选哪条

README 列出 5 条使用方式，从纯网页体验到源码贡献铺成一条全光谱。

| 路径 | 适合谁 | 需要准备 | 要不要部署 |
| ---- | ---- | ---- | ---- |
| 打开网站直接用 | 所有用户 | 一个账号 | 不需要 |
| 在龙虾 OpenClaw 中用 | 已在用 OpenClaw 的人 | API Key | 不需要 |
| 在 Claude / Cursor 等 AI 助手中用 | 已经习惯在 AI 助手里干活的人 | API Key + 一段 MCP 配置 | 不需要 |
| Docker 一键部署 | 想私有化部署的团队 | 一台服务器、Docker 20.10+、Docker Compose 2.0+ | 需要服务器 |
| 源码开发 | 开发者与贡献者 | Node.js、pnpm | 需要开发环境 |

不想逐条看，按这个顺序挑：

1. 日常在 Claude 或 Cursor 里写内容，先走 MCP，它最适合把"写完即发布"接成一条工作流。
2. 已经在用 OpenClaw，直接装插件，你会最快碰到变现和任务能力。
3. 只是想判断产品方向，先用 Web，这样最容易看清自己缺的是创作、分发、互动还是变现那一段。
4. 对数据归属和运行环境有控制要求，再看 Docker。它解决的是服务跑在哪里，不会替你解决平台授权。
5. 想改产品本身、提 PR，最后才看源码。那已经不是"怎么用"，而是"怎么参与"。

一个容易混淆的点：**自部署和贡献开发是两条不同的路**。前者把产品搬到自己服务器上跑起来，后者改产品代码。普通使用者走前者就够了，不需要一开头去读启动流程。

## 前提：Key 和端点必须在同一侧

这是 README、部署文档和仓库内的 AGENTS.md 都反复写到的约束，也是最容易踩的坑。

中国版和国际版各自独立：

1. 中国版入口 [aitoearn.cn](https://aitoearn.cn/)，国际版入口 [aitoearn.ai](https://aitoearn.ai/)。
2. Key 在登录后的左侧菜单「设置」→「API Key」里创建，三种接入方式共用同一个 Key，只需获取一次。
3. Key 来自哪个环境，就必须连回哪个环境。不匹配的结果是 `401`。

环境和 Key 不匹配时，症状看起来像"功能坏了"或"插件没装上"，实际是认证没过去。后面 MCP、OpenClaw、Relay 三节都会撞回这条。

## MCP 这条路径能走到哪一步

MCP（Model Context Protocol，模型上下文协议）配置只需要两个信息：MCP 地址和认证 Header。README 按环境列了一张端点表：

| 环境 | MCP 地址 | SSE 地址 |
| ---- | ---- | ---- |
| 中国版 | `https://aitoearn.cn/api/unified/mcp` | `https://aitoearn.cn/api/unified/sse` |
| 国际版 | `https://aitoearn.ai/api/unified/mcp` | `https://aitoearn.ai/api/unified/sse` |

Claude Desktop 的示例配置写进 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "aitoearn": {
      "type": "http",
      "url": "https://aitoearn.ai/api/unified/mcp",
      "headers": {
        "x-api-key": "你的 API Key"
      }
    }
  }
}
```

Cursor 或其他支持 MCP 的工具，把上表的地址和 `x-api-key: 你的 API Key` 填进设置即可；长连接场景走 SSE（Server-Sent Events）那一列。自部署用户把域名换成自己的地址，README 给的例子是 `localhost:8080`。

这条路径到底给了助手多大的操作面，README 没有写，`aitoearn-server` 的源码里有准确答案。`core/unified-mcp/unified-mcp.module.ts` 以 `apiPrefix: 'unified'` 注册 MCP，并引入了三组工具控制器，`@Tool` 装饰器总数 35 个：

| 控制器 | 工具数 | 覆盖动作 |
| ---- | ---- | ---- |
| `draft-generation.mcp.controller.ts` | 3 | `createVideoDraft`、`createImageTextDraft`、`getDraftTaskStatus` |
| `content.mcp.controller.ts` | 10 | 草稿与素材的分组、创建、列表、详情、删除 |
| `channels/mcp/channels.mcp.controller.ts` | 22 | 发布流创建、立即发布、取消、改排期、平台与类目查询、作品归属校验、账号与作品数据分析、评论列表与提交 |

三条结论从这份清单里直接读得出来：

- 发布这一环是真能远程触发的。`createChannelPublishFlow`、`publishChannelTaskNow`、`cancelChannelPublishTask`、`updateChannelPublishAt` 都在，所以"让 AI 助手把写完的内容直接发出去"不是宣传语。
- 数据能回读。`getChannelAccountAnalytics`、`getChannelWorkAnalytics`、`listChannelEngagementComments` 让助手可以取账号与作品数据、拉评论区列表，于是"发完之后接着管"在同一会话里就有可能。
- **35 个工具里没有任何一个属于 Monetize**。没有接单、没有任务撮合、没有结算与提现相关工具。想在 Claude 里说一句就领到一个推广任务，目前这条路径不通；变现能力落在 Web 界面和 OpenClaw 插件那两条路上。这条判断的范围是服务端源码里的 35 个 `@Tool`，OpenClaw 插件由 npm 单独分发、工具面不在本仓库内，不在结论覆盖范围内。

所以更准确的说法是：MCP 把 AiToEarn 从"一个要单独登录的站点"变成了"助手可以调用的生产、发布、互动与数据接口"，但商业侧那半套没有一起开放出来。

## OpenClaw 这条路最短

已经在用 OpenClaw（龙虾）的人，一条命令装完：

```bash
npx -y @aitoearn/openclaw-plugin-cli
```

首次运行会让你选环境并填入 API Key。命令本身没有难度，真正决定后续体验的是上一节的环境匹配——选错环境，之后的现象看起来像插件坏了，本质上只是认证失败。

装完就能在 OpenClaw 里直接接收并执行 AiToEarn 的赚钱任务。前面说过 MCP 面上没有变现工具，想让别人替你把内容和钱这两头接起来，这条是入口最浅的一条。

## Docker 自部署：你起的是一整套栈

三条命令启动：

```bash
git clone https://github.com/yikart/AiToEarn.git
cd AiToEarn
docker compose up -d
```

启动后访问 `http://localhost:8080`。首次启动会自动创建管理员账号并完成登录，不需要手动注册。

"一键"背后是这些容器：

| 服务 | 角色 | 端口 |
| ---- | ---- | ---- |
| `aitoearn-nginx` | 反向代理，统一入口 | 宿主 8080、9000 |
| `aitoearn-web` | Next.js 前端 | 内部 3000 |
| `aitoearn-server` | NestJS 主后端 API | 内部 3002 |
| `aitoearn-ai` | NestJS AI 服务 | 内部 3010 |
| `mongodb` | 数据库，单节点副本集 `rs0` | 宿主 27017 |
| `redis` | 缓存与队列 | 宿主 6379 |
| `rustfs` | S3 兼容对象存储 | 宿主 9001 控制台，API 9000 经 nginx |
| `aitoearn-init` 等三个 init 容器 | 一次性初始化：管理员登录令牌、副本集初始化、存储桶 | — |

部署文档「前置要求」一节写的是：Docker 20.10+、Docker Compose 2.0+、系统内存建议 4GB 以上、磁盘空间建议 20GB 以上。

仓库自带的 `docker-compose.yml` 里有三处设置，公网部署前需要先过一眼：

1. 端口映射把 8080、9000、9001、27017、6379 全部暴露到了宿主机，其中两个是数据库和缓存。
2. 默认凭证是明文弱值：MongoDB 是 `admin` / `password`，Redis 的 requirepass 也是 `password`，RustFS 的 access key 与 secret key 都是 `rustfsadmin`，JWT 密钥是 `change-this-jwt-secret`。
3. 自动登录默认开启：`aitoearn-init` 生成的管理员登录令牌会写进共享卷，由 `aitoearn-web` 启动时读取。

这三条叠起来的含义很直接——照仓库原样部署到一台有公网 IP 的机器上，等于把一个带默认密码的数据库和一个可自动取得管理员登录态的站点摆在了公网上。要公网跑，先改端口映射与这几个默认值，或者把整栈收到内网、放到自己的反向代理后面。

后端和 AI 服务的运行参数不在 compose 的环境变量里。`aitoearn-ai` 与 `aitoearn-server` 读取挂载为可写卷的 `config.yaml`（分别位于 `project/aitoearn-backend/apps/aitoearn-ai/config/` 和 `apps/aitoearn-server/config/`），改动通过配置管理界面完成。三个应用镜像都设了 `pull_policy: always`，每次 `docker compose up` 都会去拉最新镜像，这在生产上是个需要留意的行为。

### Relay：自部署绕不开的一环

发内容需要登录社交账号，而抖音、小红书、TikTok 这些平台的 OAuth 登录要求开发者凭据。不配 Relay，你得自己去十几个平台逐一申请开发者账号、拿 client_id 和 secret；配了 Relay，就是借用官方的凭据完成授权握手。

v2.5.0 改了这件事的做法。按 release 说明，Relay 配置从 `docker-compose.yml` 的运行时环境变量迁到了 Web 的配置管理界面，并拆成两类：

1. **Server → Relay 中转**：内容发布与社交平台 OAuth 授权使用。
2. **AI → Relay 中转**：使用平台提供的 AI 模型，同一版还加入了 Video Relay 与 Relay Media。

模型这一侧也可以不走 Relay：OpenAI、Gemini、Anthropic 等服务商，在 **AI → 模型服务商** 里直接填 API Key 和接口地址。

中国版 Key 搭配 `https://aitoearn.cn/api`，国际版 Key 搭配 `https://aitoearn.ai/api`，仍然遵循环境匹配那条前提。保存后点「保存并重启」，让对应服务重新加载配置。如果你手上是 v2.5.0 之前的部署文档或第三方教程，看到让你直接往 compose 里写 Relay 环境变量的步骤，可以先确认版本再照做。

Relay 解决的是"不申请开发者账号也能完成授权"。它的代价是授权链路经过官方服务。README 和部署文档都没有把"完全脱离官方 Relay、独立跑通全部平台授权"写成一条快速路径；真要那么做，就得逐个平台走开放接口和自己的凭据，那是另一件工作量更大的事。

## 源码开发要面对的真实结构

`project/` 下的三个目录由主仓库直接跟踪，不是 submodule，克隆下来就是完整代码。

| 目录 | 形态 | 上手命令 |
| ---- | ---- | ---- |
| `project/aitoearn-backend` | Nx + pnpm 工作区，含 `aitoearn-ai` 与 `aitoearn-server` 两个应用 | `pnpm install`，复制 `config.yaml` 为 `local.config.yaml`，再 `pnpm nx serve aitoearn-ai` 与 `pnpm nx serve aitoearn-server` 分两个终端起 |
| `project/aitoearn-web` | Next.js + pnpm | `pnpm install`、`pnpm run dev` |
| `project/aitoearn-electron` | Electron + Vite + TypeScript，包名 `aiToEarn`、版本 0.8.0，没有单独的 README | `npm run dev:mac` 或 `npm run dev` 起开发，`npm run build` 打包，`npm run test` 走 vitest |

桌面端的脚本里藏着一个跨平台陷阱：`dev` 的内容是 `chcp 65001 && vite`，`chcp` 是 Windows 切换控制台编码的命令，在 macOS 或 Linux 上会直接失败；跨平台跑要用 `dev:mac`。`rebuild` 是 `electron-rebuild -f -w better-sqlite3`，编译原生模块还需要 node-gyp 和本地 Python。

仓库根目录的 AGENTS.md 写明：backend 与 web 使用 pnpm，根目录没有统一的 package，不要在根目录随手执行 install 或 build。后端改动优先在 `project/aitoearn-backend` 用 `pnpm nx ...` 验证，并遵循该目录下的 CLAUDE.md。

Node 版本在三个地方给了三个要求，这是本地开发前先要理清的一件事：

| 出处 | 要求 |
| ---- | ---- |
| README 徽章 | Node.js 20.18.x |
| `project/aitoearn-backend/.nvmrc` | `24` |
| `project/aitoearn-electron/package.json` 的 `engines` | `20.x.x` |

哪个都不算权威说明，实际开发时按所在子项目的锁定版本走更稳——`.nvmrc` 是仓库自己开发后端时用的版本，`engines` 是桌面端的运行环境约束，README 徽章则更像是面向整体的一条笼统提示。

还有一处容易走错：README 的「启动 Electron 桌面项目」一节给的是另一个仓库 [yikart/AttAiToEarn](https://github.com/yikart/AttAiToEarn)，而主仓库 `project/aitoearn-electron` 里也有一份 Electron 代码。两处并存，动手前先确认你要改的是哪一个。

想评估产品能力的人，这一节可以整体跳过。"本地能不能跑起来"和"值不值得用"是两个问题，前者的答案对后者没有约束力。

## 版本演进的三个转折

以下日期取自 GitHub releases 页面，变化点取自 README 的「最新动态」与对应 release 说明：

| 版本 | 发布 | 重点变化 |
| ---- | ---- | ---- |
| v0.1.1 | 2025-02-26 | 首个开源版本，小红书、抖音、快手、视频号视频一键发布 |
| v1.0.18 | 2025-09-16 | 首个出海版本，新增 Facebook、Instagram、Threads、Twitter、YouTube、TikTok、Pinterest |
| v1.3.2 | 2025-11-13 | README 称之为"首个开源且可完全使用的版本" |
| v1.4.0 | 2025-11-28 | 应用内自动更新；创作界面加入缩写、扩写、图片与视频生成、标签生成，支持 Nano Banana Pro |
| v1.4.3 | 2025-12-15 | "All In Agent" 起点，加入能自动内容生成与发布的 Agent |
| v1.8.0 | 2026-02-10 | 线下商户推广方案，覆盖餐厅、零售店、民宿、美容美发、健身房 |
| v2.1.0 | 2026-03-28 | 内容交易市场上线；接入 OpenClaw；加入 MCP 协议支持 |
| v2.4.0 | 2026-05-21 | 草稿生成接入 HappyHorse 1.0 与 Seedance 2.0，强化视频/图文批量生成、多模型选择、参考图片与视频、目标平台限制与文案提示词；界面改版，Twitter/X 探索与互动能力增强 |
| v2.5.0 | 2026-06-24 | Relay 配置迁入配置管理界面并拆为 Server Relay 与 AI Relay；运行时配置改为挂载 `config.yaml`；新增[开放平台文档](https://docs.aitoearn.cn/) |

这条时间线上有三个节点起了转折作用。

v1.4.3 是分界点。在此之前它是一个多平台发布工具，从这一版开始，内容的生成和发布交给 Agent 调度。

v2.1.0 同时开了两个方向：面向交易的内容交易市场，以及面向 Agent 生态的 OpenClaw 与 MCP。产品重心从"帮你发"移向"帮你赚"，就发生在这一版。

v2.5.0 看着最不起眼，对自部署的人却最实在：Relay 配置从文件搬进了界面，发布平台授权和 AI 模型这两条中转第一次分开成两个开关。这类改动不会出现在演示视频里，却直接决定你要改几个地方、重启几次服务。

HappyHorse 1.0 和 Seedance 2.0 都是 v2.4.0 接进草稿生成的模型。README 只写了两者用于草稿生成并增强视频/图文批量能力，没有区分哪一位负责图文、哪一位负责视频。要用哪个模型产出什么，以模型方文档和草稿生成界面的可选项为准。

## 它适合谁，也不适合谁

一人公司和独立创作者最容易感到省事——一个人同时管创作、分发、互动和结算时，集中入口比多工具拼装划算。做矩阵账号的小团队是另一类，多平台协同和排期的价值要在这里才兑现，单平台工具接不住跨平台调度。想把 AI 助手接进发布链路的团队，MCP 面上的发布、素材和数据工具已经齐了，不必从零搭。手上已经有推广任务要结算的人，则会直接用起 Monetize 那一层。

不划算的情形也很具体。只运营单一平台、发文频率很低，这套工具链会显得偏重，普通排期工具就够用。只想找个 AI 文案生成器，后面那半条链路对你不存在，单点写作工具更轻。完全不想碰授权、配置和环境问题，那么一旦深入，工程细节不可避免，纯 SaaS 交付更合适。需要在助手侧完成变现动作，MCP 面上没有任务与结算工具，这部分只能回到 Web 或 OpenClaw。

## 卡住时先看这几处

文档和源码里能确认的错误现象不多，最常见的是两类：环境不匹配返回 `401`，以及 Docker 栈里有容器起不来。下面这张表按现象给出排查顺序。

| 现象 | 先查 |
| ---- | ---- |
| 接入返回 `401` | Key 来自哪个环境、端点是否同一环境、Key 是否完整复制；Docker 部署再看 Server Relay 与 AI Relay 的地址是否成对 |
| 助手看不到 AiToEarn 的工具 | 配置用的是 `type: http` 还是 SSE、Header 名是否为 `x-api-key`、自部署是否把域名换成了自己的地址 |
| `docker compose up` 后有服务起不来 | Docker 与 Compose 版本、内存和磁盘是否达到建议值，再用 `docker compose ps` 看哪个容器不是 healthy |
| 发布卡在授权这一步 | 该平台是否需要开发者凭据、Server Relay 是否已配置并重启、账号登录态是否已过期 |
| 自动互动没有发生 | 浏览器插件是否安装、是否登录了同一个账号、平台页面结构是否改版 |
| 生成结果与预期偏差大 | 先确认走的是哪个模型服务商和 `default` / `think` 分档，再检查 skills 层面的提示词约束 |

## 三个问题，检验你有没有抓准边界

可以用下面三问自测。答得上来，说明这条链路的分段和限制已经清楚：

1. **四块能力的先后关系是什么，为什么 Monetize 排在最后？** 因为它依附前三步——没有发布就没有互动，没有互动数据，按互动量结算就无从谈起。
2. **一个已经在用 Cursor 写内容的独立开发者，该走哪条路径，能走到哪一步？** 走 MCP。可生成草稿、可发布与改排期、可读数据与评论，但不能在助手里接变现任务，那部分要回 Web 或装 OpenClaw 插件。
3. **自部署后所有平台授权都失败，第一个排查点在哪？** 先看 Relay 是否配置（v2.5.0 之后在配置管理界面的 Server → Relay 中转），再看 Key 与 Relay 地址是否同侧。

## 下一步读什么

按你选择的接入路径，读的顺序不一样：

- 判断产品方向：README 的「快速使用 AiToEarn（5 种方式）」和「如何获取 API Key」两节，加一遍 Web 体验。
- 走 MCP：README 第 ③ 节给端点与配置，[开放平台文档](https://docs.aitoearn.cn/) 看接口细节，需要工具清单时读 `apps/aitoearn-server/src/core/unified-mcp/unified-mcp.module.ts` 引入的三个控制器。
- 走 Docker：[DOCKER_DEPLOYMENT_CN.md](https://github.com/yikart/AiToEarn/blob/main/DOCKER_DEPLOYMENT_CN.md) 覆盖生产配置、AI 服务、OAuth 和存储，再对照 `docker-compose.yml` 检查端口与默认凭证。
- 改代码：先读 [CONTRIBUTING.md](https://github.com/yikart/AiToEarn/blob/main/CONTRIBUTING.md)，再读根目录与 `project/aitoearn-backend/AGENTS.md`，这两份文件写了包管理器边界和验证命令。
- 看产品边界：README 的三语版本（`README.md` / `README_EN.md` / `README_JA.md`）由同一套规则同步维护，能力描述会同时落到三份，英文版可用来交叉核对表述。

遇到功能问题，README 建议优先走 [GitHub Issues](https://github.com/yikart/AiToEarn/issues) 反馈。

## 资料口径说明

本文的判断基于以下来源，核查时间为 2026-09-25：

1. **仓库文档**：README（含英日双语版本）、`DOCKER_DEPLOYMENT_CN.md`、`CONTRIBUTING.md`、根目录与后端的 `AGENTS.md`
2. **后端源码**：`project/aitoearn-backend/apps/aitoearn-ai/src/core/agent/`（运行时、skills、MCP 工具、claude-code-router）、`apps/aitoearn-server/src/core/unified-mcp/`、`core/content/`、`core/channels/mcp/`，以及 `docker-compose.yml`
3. **GitHub API 与 releases**：Stars / Forks / 语言占比 / 最近推送时间，v0.1.1 至 v2.5.0 共 28 个 release 的发布时间
4. **在线端点连通性**：`aitoearn.ai` 与 `docs.aitoearn.cn` 访问返回 200

判断的边界：

- 未实际运行 AiToEarn，也未部署过这一整套容器。功能可用性与平台授权成功率取决于账号状态、平台策略和模型服务商配额，本文不作承诺。
- 源码结论（Agent 内核、35 个 MCP 工具、Relay 配置方式）取自 main 分支当前状态，v2.5.0 之后仓库仍在持续提交，这部分描述可能随后续版本失效。
- Stars、Forks 和语言占比是某一天的快照，会随时间变化。
- README 的「最新动态」日期与 GitHub release 的发布时间存在一到三天出入（如 v1.3.2 记为 2025-11-12、release 页面为 2025-11-13，v1.8.0 记为 2026-02-07、release 页面为 2026-02-10），本文表格统一采用 release 页面时间。

## 参考链接

- 官网（国际版）：[aitoearn.ai](https://aitoearn.ai/)
- 官网（中国版）：[aitoearn.cn](https://aitoearn.cn/)
- GitHub：[yikart/AiToEarn](https://github.com/yikart/AiToEarn)
- 开放平台文档：[docs.aitoearn.cn](https://docs.aitoearn.cn/)
- Docker 部署指南：[DOCKER_DEPLOYMENT_CN.md](https://github.com/yikart/AiToEarn/blob/main/DOCKER_DEPLOYMENT_CN.md)
- 最新版本：[v2.5.0](https://github.com/yikart/AiToEarn/releases/tag/v2.5.0)
- 相关项目：[claude-code-router](https://github.com/musistudio/claude-code-router)
