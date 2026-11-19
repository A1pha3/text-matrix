---
title: "Sure：一个花了 100 万美元做出来、然后被市场判死刑的个人财务应用，现在以社区 fork 的形式活着"
date: "2026-11-20T01:27:19+08:00"
slug: "we-promise-sure-maybe-finance-community-fork"
description: "Sure 是已停运的 Maybe Finance 的社区 fork，一个 Rails 个人财务应用，同时向浏览器、桌面、移动端、API 与 LLM agent 提供入口。本文梳理它的商业失败史、社区接管的边界、AGPLv3 与商标约束，以及 MCP 接入时「agent 能读你全家账本」的权限设计。"
draft: false
categories: ["技术笔记"]
tags: ["Rails", "个人财务", "开源", "AGPL", "MCP"]
github_repo: "we-promise/sure"
source_key: "gh:we-promise/sure"
---

## 核心判断

Sure 的技术栈（Ruby on Rails + PostgreSQL + Redis）并不稀奇，架构也没什么可圈可点的地方。真正让它值得写一篇的，是它的**来历**，以及这个来历带来的两条硬约束。

来历是这样的：Maybe Finance 团队在 2021–2022 年花了近 100 万美元（员工、承包商、数据供应商、基础设施）做了一个功能完整的个人财务与财富管理应用，甚至包含「Ask an Advisor」—— 订阅内直接连一位真实的 CFP/CFA 持证人。商业上没跑通，2023 年中停止开发，随后开源，目标是让用户免费自托管。托管版也短暂上线过，作为 B2C 生意同样不可持续。现在它是一个社区维护的 fork。

这意味着两件事：

**第一，它是一个「商业失败后被社区接管」的样本。** 这类项目在开源世界不少见，但少有像它这样把失败过程原样写在 README 里的。

**第二，「Maybe」是 Maybe Finance Inc. 的注册商标，不允许在 fork 里使用。** 这直接导致项目改名 Sure，并要求所有 fork 保留原始 AGPLv3 许可、明确声明与 Maybe Finance **无关联也未获背书**。

顺带一提，一个容易被忽略的技术决策：**Sure 把 MCP（Model Context Protocol）端点做成了正式的一等客户端入口。** 这意味着 Claude Desktop、GPT agent 或任何本地 agent 可以直接查询你的家庭财务数据 —— 这件事在个人财务领域相当激进，后面会详细说它的权限设计。

截至 2026 年 11 月 20 日，这个仓库有 16652 stars、1470 forks，Ruby 为主，AGPL-3.0 许可，2025 年 7 月创建，11 月 19 日仍在更新。

## 商业失败史：README 里的诚实叙事

README 把失败过程写得很完整，值得原文引用式地梳理：

1. **2021–2022**：团队构建功能完整的个人财务与财富管理应用，含 Ask an Advisor（订阅内连真实 CFP/CFA）。
2. **2023 年中**：商业跑不通，停止开发。
3. **开源**：花掉近 100 万美元之后开源，目标是让用户免费自托管，最终上线一个小额收费的托管版。
4. **托管版短暂上线**：作为可持续的 B2C 生意，同样没跑通。
5. **现在**：社区维护的 fork，目标是让代码库活着，看它能走向哪里。

这段叙事的信息量在于它区分了两种失败：**「产品做不好」和「商业模式不成立」**。Maybe 的失败是后者 —— 功能做到了「Ask an Advisor」这个程度，产品能力不是瓶颈。

这对做技术选型的人是个提醒：**一个代码质量很好的项目仍然可能因为商业模式而消失**。而社区 fork 之所以能存在，正是因为代码在商业失败之前已经开源了。

## 架构：以 Rails 服务端为中心

`docs/clients.md` 开门第一句就把架构说清楚了：

> Sure 以一个 Rails 服务端为中心。每个客户端都连接到这个服务端，使用相同的账户、用户、认证规则和财务数据。

`app/` 目录是标准 Rails 分层：

```
app/
├── assets · channels · components · constraints
├── controllers · helpers · javascript
├── jobs · mailers · middleware · models
├── policies · services · validators
└── views · data_migrations
```

注意 `policies`（Pundit 风格的授权策略）和 `constraints`（数据库约束）都是独立目录 —— **授权逻辑和数据完整性约束被显式从控制器里抽出来了**。对一个要暴露给第三方客户端和 AI agent 的应用，这是必要的结构。

服务端依赖：PostgreSQL（>9.3，推荐最新稳定版）、Redis（>5.4）、`.ruby-version` 指定的 Ruby 版本。

## 客户端矩阵

| 客户端 | 适合谁 | 状态 | 入口 |
|---|---|---|---|
| Web 应用 | 完整日常使用、管理、自托管访问 | **主客户端** | 跑 Rails 应用访问服务器 URL；本地开发用 `bin/dev` 开 `http://localhost:3000` |
| macOS 桌面应用 | 想在原生 Mac 窗口里用 | Web 应用的原生外壳 | Tauri 2 壳，见 `desktop/README.md` |
| 移动应用 | iOS/Android 的基础访问 | Flutter 伴生应用 | 目前聚焦登录和账户余额 |
| LLM agent 与助手 | 需要结构化访问财务数据的 agent 运行时 | MCP 端点 | 见 `docs/hosting/mcp.md` |
| 自定义 API 客户端 | 脚本、服务、导入实验、面板 | HTTP API | OpenAPI 规范 `docs/api/openapi.yaml` |

桌面应用的设计值得一读：**Tauri 2 壳渲染完整的 Sure Web 应用**。首次启动时问服务器 URL、检查健康端点，然后加载正常的登录流程。它和浏览器**用同一个服务端、同一套认证、同一套 MFA 和权限**。README 说得很清楚：「当有人想要桌面应用体验但不需要一套独立的桌面数据模型时用它。」

移动应用是 Flutter 伴生应用，通过 API 连接，目前**只做核心流程**（认证、查看余额）。功能集不够时用 Web。

### 一条重要的架构约定

文档最后有一条对所有客户端开发者都适用的规则：

> 原生客户端应该用 `GET /api/v1/cash_flow` 读取**服务端计算的月度汇总和每日支出对比**，而不是从交易流水里自己重建 Sure 的报表规则。

这是分布式系统的经典陷阱：**报表规则不能有两个实现**。一旦客户端自己算一遍，两边的口径迟早会漂移。这个约定把「哪些计算属于服务端」写清楚了。

## MCP 接入：把 agent 接到你的账本上

这是 Sure 最激进也最值得讨论的设计。

Sure 暴露一个 MCP 端点，让 Claude.ai、Claude Desktop、GPT agent 或自定义 AI 客户端**直接查询并操作**你的财务数据。文档给的理由很实在：

> 与其把财务数据复制粘贴进聊天窗口，不如让你的 AI 助手通过安全的 API 直接查询 Sure 的数据。

三个使用场景：让外部助手分析你的 Sure 数据；希望 LLM 提供商与 Sure 分离；构建需要财务工具的自定义 AI agent。

### 两种认证模式

**模式一：OAuth 2.0 / 动态客户端注册（推荐）**

Sure 暴露三个标准端点：

- `/.well-known/oauth-protected-resource`
- `/.well-known/oauth-authorization-server`
- `POST /register`（动态客户端注册）

兼容的 MCP 客户端可以注册一个公共 OAuth 客户端、把用户重定向回 Sure 登录、拿到带 `read_write` scope 的 bearer token。

**模式二：静态 bearer token（环境变量）**

适合自定义 agent、脚本，以及想把 MCP 固定到某个特定用户的部署：

| 变量 | 说明 | 示例 |
|---|---|---|
| `MCP_API_TOKEN` | 认证用 bearer token | `your-secret-token-here` |
| `MCP_USER_EMAIL` | 助手可访问的那个 Sure 用户的邮箱 | `user@example.com` |

生成 token：

```bash
openssl rand -base64 32
```

### 权限设计的真实边界

这里必须把话说透。文档自己写了：

> 因为这给了助手对那个用户**家庭数据**的读权限，请把 MCP token 当作生产环境机密，只连接你信任的助手和提供方。

而且 `MCP_USER_EMAIL` 必须匹配一个已存在的 Sure 用户邮箱 —— **助手能访问该用户的全部财务数据**。

这是一个很重的授权授予。特别注意 `read_write` 这个 scope —— **它不是只读的**。所以：

- 给第三方 agent 发一个 token，等于把某个家庭账户的读写权交出去；
- 静态 token 模式没有过期机制，泄漏了只能手动轮换；
- OAuth 模式虽然可以撤销，但 `read_write` 的粒度依然偏粗。

如果你要用这个功能，**最小化原则在这里格外重要**：只接你自己控制的 agent，token 走环境变量不进版本库，定期轮换。

### API 认证

自定义 API 客户端有两种认证方式：

- 用户生成的 `X-Api-Key` 请求头
- Doorkeeper 授权服务器的 OAuth2 bearer token（给注册的应用客户端）

原生客户端可以用 `PATCH /api/v1/insights/:id/acknowledge` 确认一条主动推送的洞察，这需要 `read_write` 凭据和预览功能访问权，成功返回 `204 No Content`。

## 自托管

### Docker

`docs/hosting/docker.md` 是自托管的入口。Sure 可以用 Docker 自托管。

### 本地开发

```sh
cd sure
cp .env.local.example .env.local
bin/setup
bin/dev

# 可选：加载演示数据
rake demo_data:default
```

访问 `http://localhost:3000`。加载了演示数据的话，登录凭据是 `user@example.com` / `Password1!`。

环境变量示例文件有三份：`.env.example`、`.env.local.example`、`.env.test.example`。

### 一键部署

Render 的一键部署按钮指向 `sure-render-templates` 仓库的 `branches/<branch-name>/render.yaml`（Render 要求按钮目标分支根目录有 `render.yaml`）。三个变体：

| 变体 | 部署内容 | `latest` / `stable` |
|---|---|---|
| **Sure - No AI** | Sure web、Sidekiq worker、Render Postgres、Render Key Value。**AI token 故意留空** | 两个分支都有 |
| **Sure - Simple AI** | 上面这套 + OpenAI 支持的 AI 设置、pgvector-ready 的 Postgres、Sidekiq、Render Key Value。Render 会提示填 OpenAI token | 两个分支都有 |
| **Sure - External AI** | 上面 + 外部助手设置 + **AlphaClaw**（管理 Render 上的 OpenClaw gateway） | 两个分支都有 |

这个三档划分很实用：**「No AI」这一档让人能先把账本跑起来，再决定要不要接 AI**。对个人财务软件来说，这个默认顺序是对的。

除了 Render，还有 PikaPods 和 Hostim 的一键部署。

## 性能是公开讨论的

Sure 建了一个**公开的性能看板**（Skylight），展示 demo 站上问题请求的端点和堆栈追踪，直接挂在 README 里：

> https://www.skylight.io/app/applications/s6PEZSKwcklL/recent/6h/endpoints

README 的态度很直接：「任何有助于改善性能的贡献都非常受欢迎。」

这在开源项目里不常见 —— **把「哪里慢」摆在首页，而不是等用户报障**。数据密集的财务应用，慢查询是核心体验问题。

## 许可与商标：硬约束

这一节对 fork 者最重要。

- **许可**：Sure 和 Maybe 都是 **AGPLv3**。AGPL 的关键条款是：**通过网络提供服务也必须开源**。你基于它改的东西，只要通过网络提供，就要开放源码。
- **商标**：「Maybe」是 Maybe Finance, Inc. 的商标，**不允许**在 fork 的仓库里使用。**「Sure」不是** —— 它指的是这个社区 fork。
- **归属要求**：你可以在 AGPLv3 下自由 fork，但请在 README 里明确声明你的 fork 基于 Maybe Finance、**与 Maybe Finance 无关联也未获其背书**，并保留原始 AGPLv3 许可。

## 边界

**功能上，移动端和桌面端都不是完整替代。** 桌面端是 Web 壳，移动端只做登录和余额。需要完整功能就用 Web。

**AI 集成是可选的，且三档部署的 AI 能力不同。** 「No AI」档根本不带 AI。

**性能问题是被承认的、公开的、未完全解决的。** 看板就是证据。

**社区 fork 的维护是分时的。** 它「活着」，但没有 Maybe 团队的工程投入。README 邀请你加入 Discord。

**「Ask an Advisor」那类功能不在了。** 那是原 Maybe 的商业能力，社区 fork 不提供。

## 采用顺序

1. **先 Docker 自托管跑起来**，用 `rake demo_data:default` 的演示数据看看它到底做什么，别先读代码。
2. **用 Web 端走一遍核心流程**（连接 provider、导入交易、看报表）。原生客户端只在你确实需要手机/桌面访问时才上。
3. **再看 MCP**。如果你确实要让 agent 查账，按 `docs/hosting/mcp.md` 配 OAuth（优先）或静态 token（次选），并把 token 当生产机密 —— 它是 `read_write` 权限，绑到整个家庭数据。
4. **要改代码的话，先读 `docs/llm-guides/` 和 `docs/providers/`** —— 仓库专门为 LLM 辅助开发准备了指引。
5. **fork 的话，先处理商标**。README 里要求的两句话必须写进你的 README。

## 排查：按现象定位

| 现象 | 先查这里 |
|---|---|
| 部署后起不来 | 先看 `docs/hosting/docker.md`；本地开发确认 PostgreSQL >9.3、Redis >5.4 和 `.ruby-version` |
| 桌面 app 连不上服务器 | 首次启动要填服务器 URL 并检查健康端点；确认服务端可达 |
| MCP 认证失败 | OAuth 模式检查 `/.well-known/*` 端点；静态 token 模式检查 `MCP_API_TOKEN` 和 `MCP_USER_EMAIL` 两个变量**都**设了 |
| agent 读不到数据 | `MCP_USER_EMAIL` 必须匹配一个已存在的 Sure 用户邮箱；确认该用户有数据 |
| 报表数字和 Web 端对不上 | 原生客户端不该自己从交易重建报表规则，改用 `GET /api/v1/cash_flow` |
| 页面卡顿 | 看公开性能看板：<https://www.skylight.io/app/applications/s6PEZSKwcklL/recent/6h/endpoints> |
| `rake demo_data:default` 没数据 | 演示数据登录是 `user@example.com` / `Password1!` |
| 想用 AI 但不想配 key | 用「Sure - No AI」那档 Render 部署，AI token 故意留空 |
| fork 后能用吗 | AGPLv3 可以，但「Maybe」是注册商标不能用，且 README 必须声明无关联未背书 |

## 参考

- 仓库：<https://github.com/we-promise/sure>
- 站点：<https://sure.am>
- 原项目最终版本说明：<https://github.com/maybe-finance/maybe/releases/tag/v0.6.0>
- 客户端指南：仓库内 `docs/clients.md`
- MCP 服务端文档：仓库内 `docs/hosting/mcp.md`
- Docker 自托管：仓库内 `docs/hosting/docker.md`
- OpenAPI 规范：仓库内 `docs/api/openapi.yaml`
- Discord：<https://discord.gg/36ZGBsxYEK>
