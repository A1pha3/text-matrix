---
title: "withastro/flue：Astro 团队的 Agent Harness 框架"
date: "2026-06-06T09:50:00+08:00"
slug: "withastro-flue-agent-harness-framework"
aliases:
  - "/posts/tech/withastro-flue-agent-harness-framework/"
description: "withastro/flue 是 Astro 团队推出的 TypeScript Agent Harness 框架，重点不在模型调用，而在 session、sandbox、skills、持久化和跨运行时部署。"
draft: false
categories: ["技术笔记"]
tags: ["Flue", "Agent Harness", "Astro", "TypeScript", "Cloudflare"]
---

# withastro/flue：Astro 团队的 Agent Harness 框架

Flue 做的事情比"再封装一次大模型调用"更多。它更像把 Claude Code、Codex、OpenCode 这类交互式 Agent 的工作方式，搬到可部署的 TypeScript 后端里：agent 有会话、文件系统、skills、sandbox，也能跑在 Node.js、Cloudflare Workers 或 CI runner 上。

如果只需要 `generateText()`、`streamText()`，Vercel AI SDK 已经够用。Flue 处理的是后半段：多步 agent 怎么拿工具、保留上下文、恢复执行，并部署到不同运行时。

本文基于 [withastro/flue](https://github.com/withastro/flue) 仓库、官方文档和 v0.10.1 时代的 API 整理。写作时 `@flue/runtime` 已到 `0.11.0`（2026-06-10），部署前要看 CHANGELOG。

## 核心判断

Flue 是 TypeScript 优先的 Agent Harness 框架。它把 agent 执行时需要的环境装进一个 harness：

- `createAgent()` 描述模型、指令、工具、skills 和 sandbox。
- `init()` 创建 harness，让 agent 进入执行环境。
- `harness.session()` 管理会话历史和持久化。
- build target 把同一份代码构建到 Node.js、Cloudflare Workers 或 CI。

官方 README 称它为 “Agent Harness Framework”。Flue 的重点不在 prompt，而在上下文、工具、文件系统、持久化和部署包装。

## 系统地图

Flue 的核心抽象是四层：

```text
Agent   -> 模型、指令、tools、skills、sandbox
Harness -> init() 后得到的运行 handle
Session -> 会话历史、持久化、同一 id 的上下文
Task    -> prompt 调用、子 agent、skill 激活
```

一次请求大致是：route 做鉴权，runtime 找到 agent module，`init(agent)` 创建 harness，`harness.session()` 打开或复用 session，最后由 `session.prompt()` 调用模型、工具和 sandbox。

URL 里的 `<id>` 是 agent instance 的稳定标识。同一个 `<id>` 续接 session，换一个 `<id>` 就是新对话。

## 基本信息

Flue 由 Astro 团队维护，主语言是 TypeScript，License 是 Apache-2.0，运行目标包括 Node.js、Cloudflare Workers、GitHub Actions 和 GitLab CI/CD。项目仍是 Experimental。

## 和同类项目的边界

问题是“怎么调模型”，先看 Vercel AI SDK；问题是“agent 怎么带工具、续会话、跑在后端并可恢复”，Flue 才进入讨论。跟 LangGraph 相比，它更偏 TypeScript / Cloudflare；跟 Mastra 相比，它更强调 sandbox、Markdown skills 和部署 target；跟 Claude Code / Codex / OpenCode 相比，它把 CLI DX 抽成 headless runtime。

## 关键机制

### Sandbox：默认轻，必要时换真容器

Flue 默认用 [just-bash](https://github.com/vercel-labs/just-bash) 做 virtual sandbox，适合文件读写、简单命令和受控工具执行。它启动快，不需要给每个 agent 拉容器。边界也明确：`git clone`、`npm install`、复杂构建、网络隔离、系统依赖安装，都不适合只靠 just-bash。需要真实 Linux 环境时，应切到 Daytona、Cloudflare Sandbox、E2B。

最容易混的是 session 和 sandbox。Session 持久化决定对话历史、run history 能不能跨请求保留；sandbox 持久化决定文件、依赖、构建产物能不能留在执行环境里。Cloudflare Durable Objects 可以保留 session，但不代表 virtual sandbox 的临时文件会自动保留。

### Skills 是 Markdown

Flue 的 skills 可以直接从 Markdown 导入。Skill 是一份 agent 能直接读懂的操作说明，不是 TypeScript callback。它支持静态导入和运行时发现；静态导入会在打包时校验 `SKILL.md`，运行时可通过 `session.skill('name')` 调用 workspace skills。构建阶段会拒绝 `.env*`、`.ssh/`、`.aws/` 等敏感文件进入 skill 包。

### Durable execution 和 persistence

v0.10.0 后，Flue 把一次输入看成 submission，而非普通 HTTP 请求。Direct HTTP、SSE、WebSocket、local CLI、`dispatch()` 共享一套 SQL-backed 生命周期。agent turn 断线、重启或失败时，系统可以尽量从已记录的进度恢复。

Node.js 默认用内存存储。要持久化，可以放 `db.ts` 接 SQLite 或 PostgreSQL。Cloudflare target 默认走 Durable Objects + SQLite，不需要也不允许 `db.ts`。同一项目同时支持 Node 和 Cloudflare 时，要提前处理这个差异。

### `prompt()` 和 `dispatch()`

`session.prompt()` 适合同步请求：调用方等 agent 给出结果，再返回。

`dispatch()` 更像事件投递：webhook、队列消息、聊天事件进来后，应用先返回 receipt，让 agent 后台处理。典型场景是 webhook 必须几秒内返回 200，但 agent 处理要几分钟。

### Provider、MCP 和可观测性

企业场景经常需要私有 API gateway 或 OpenAI 兼容代理。Flue 可以在应用入口统一配置 provider，让所有 harness/session 走同一套模型端点配置。

MCP 也能接，但还偏底层：`connectMcpServer()` 默认用 streamable HTTP；legacy SSE 要显式传 transport；不会自动检测 transport，不会 spawn stdio server，也不处理 OAuth。

可观测性方面，Flue 有 `observe()` 钩子，也提供 `@flue/opentelemetry`。生产环境至少应记录 run start/end、错误、模型调用、工具调用和 submission receipt，否则 agent 出问题时很难排查。

## 最小使用方式

一个 workflow 的骨架基本是：创建 agent，`init(agent)` 得到 harness，`harness.session()` 打开会话，最后 `session.prompt(payload.prompt)` 执行。结构化输出可加 Valibot schema；CI 操作真实仓库可用 `local()` sandbox，但它会接触 host filesystem，不适合多租户。

源目录优先级：`.flue/` > `src/` > 项目根。第一个匹配目录生效，不会合并。

## 适合什么，不适合什么

适合先试 Flue 的场景：TypeScript 团队想把 agent 做成后端服务；需要在 Cloudflare Workers 上跑 agent 并保存会话；同一份 agent 逻辑要跑在本地、CI 和生产环境；任务需要 tools、skills、文件系统、session 这些执行环境能力。

不建议急着迁移的场景：Python 体系已经围绕 LangGraph 建好；只是做聊天 UI，后端只需要模型流式输出；生产系统要求稳定 API；任务强依赖真容器，但团队还没准备好 Daytona / E2B / Cloudflare Sandbox 的成本和运维。

Flue 的价值不在“功能最多”，而在把 TypeScript、sandbox、Markdown skills、Cloudflare 部署和 durable execution 放到同一条路径上。只命中其中一两项时，未必值得引入。

## 风险和采用顺序

主要风险：API 仍可能变化；v0.10+ 有 breaking changes；just-bash 不能替代真实容器；文档分散；MCP 的 transport、OAuth、stdio server 要自己处理；Cloudflare Durable Object 和 SQLite classes 迁移有手工配置。

稳妥的试用路径：先用 Node.js target 跑最小 workflow；再把文件操作放进 virtual sandbox；需要长会话时加 `db.ts` 或切 Cloudflare 验证 Durable Objects；有 webhook/队列再引入 `dispatch()`；just-bash 不够时才接真实容器；最后补 observability。

这个顺序能把三条线拆开：agent 行为、session 持久化、sandbox 环境。三者都跑通后，再谈迁移已有系统会稳很多。

最后更新：2026-06-10

说明：本文保留 v0.10.1 取证时的主要 API 形态，并补充 2026-06-10 npm 包版本已到 `0.11.0` 的事实。
