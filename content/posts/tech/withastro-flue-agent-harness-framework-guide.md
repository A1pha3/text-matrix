---
title: "withastro/flue：Astro 团队出品的 Agent Harness 框架，把 Claude Code 变成可编程的 headless runtime"
date: "2026-06-06T09:50:00+08:00"
slug: "withastro-flue-agent-harness-framework"
aliases:
  - "/posts/tech/withastro-flue-agent-harness-framework/"
description: "withastro/flue 是 Astro 团队 2026 年新出的 TypeScript Agent 框架，自带 agent harness + just-bash 虚拟沙箱，runtime-agnostic 部署到 Node.js/Cloudflare/GitHub Actions，由 @flue/runtime + @flue/cli + Hono 路由组成，把 Claude Code 的 DX 搬到 headless 可编程形态。"
draft: false
categories: ["技术笔记"]
tags: ["Flue", "Agent Harness", "Astro", "TypeScript", "Cloudflare"]
---

# withastro/flue：Astro 团队出品的 Agent Harness 框架，把 Claude Code 变成可编程的 headless runtime

> **目标读者**：在 Node.js / Cloudflare Workers / GitHub Actions 上构建 AI Agent 后端服务的工程师；想把 Claude Code 那种"很爽的 DX"搬到 headless 可编程环境的人
> **核心问题**：如何用一个 **runtime-agnostic** 的 TypeScript 框架写 Agent，让同一个代码能跑在 Node.js、Cloudflare Workers、CI runner 上，并自带沙箱、session、skills、hooks？
> **难度**：⭐⭐⭐⭐（框架层概念：agents/harnesses/sessions/tasks 四层模型）
> **来源**：GitHub [withastro/flue](https://github.com/withastro/flue)，4,533 ★ / Apache-2.0 / 2026-06-06

---

## 一、核心判断

[withastro/flue](https://github.com/withastro/flue) 不是又一个 LLM SDK，它做了一件更"框架层"的事：**把 Claude Code / Codex / OpenCode 这种交互式 Agent 工具的 DX 抽象出来，搬到 headless 可编程环境**。

项目方原话：

> "Flue isn't another AI SDK. It's a proper runtime-agnostic framework — think Astro or Next.js, but for agents."

**这意味着**：

1. **不是 SDK**——AI SDK 关心的是"调一次 LLM 返回结果"，Flue 关心的是"一个 Agent 怎么部署、怎么跑、怎么和外部系统集成"
2. **runtime-agnostic**——同一份代码在 Node.js、Cloudflare Workers、CI runner 上都能跑
3. **像 Astro/Next.js 一样分层**——文件约定、build 流程、deploy 目标都由框架管，开发者专注业务逻辑

**与同类项目的关系**：

| 项目 | 范围 | Flue 的差异 |
|------|------|-------------|
| Vercel AI SDK | LLM 调用 + 流式输出 | Flue 是更上层的"Agent runtime + 部署框架" |
| LangGraph | Agent 编排（Python） | Flue 是 TypeScript 优先、runtime-agnostic |
| Mastra | TypeScript Agent framework | Flue 内置 virtual sandbox、MCP、消息驱动 agents |
| Claude Code / Codex / OpenCode | 交互式 CLI Agent | Flue 把这些工具的 DX 抽到 headless |

---

## 二、关键数据

| 指标 | 数值 |
|------|------|
| Stars | 4,533 |
| Forks | 241 |
| License | Apache-2.0 |
| 主语言 | TypeScript |
| 创建时间 | 2026-02-07 |
| 最近推送 | 2026-06-05（持续活跃） |
| 状态 | **Experimental** — APIs may change |
| 维护方 | [withastro](https://github.com/withastro)（Astro 团队） |
| 部署目标 | Node.js、Cloudflare Workers、GitHub Actions、GitLab CI/CD |

> ⚠️ 仓库顶部明确标注 **Experimental**——v0.0.x 在 v0.0 分支，主分支是正在迭代的"下一版"。

---

## 三、四层核心模型

Flue 最重要的概念分层：

```
Agent
  └── Harness（一个或多个）
        └── Session（默认或多个）
              └── Tasks / Prompts / Skills
```

### 3.1 Agent

Agent 是 `agents/<name>.ts` 里的源文件，是 Flue 应用的入口。它定义：

- 默认模型（`anthropic/claude-sonnet-4-6`）
- 默认 sandbox
- 默认 cwd
- subagent profiles

### 3.2 Harness

`init(createdAgent)` 创建一个 **Harness**——一个**已经配置好的、可以直接用的 handle**。Harness 持有：

- 模型默认值
- 工具集合
- sandbox
- 文件系统
- 多个 session

**同一个 workflow 可以用多个 isolated harness scope**（传 `{ name }` 参数）。

### 3.3 Session

`harness.session()` 打开默认 session。Session 持有：

- 消息历史
- 对话 metadata
- 持久化层（Cloudflare 用 Durable Objects，Node 默认内存）

**关键设计**：**URL `<id>` 是 Agent instance 的稳定标识**。同一个 `<id>` 多次访问会复用 session（"会话续接"），换 `<id>` 开新对话。

```
POST /agents/<agent-name>/<id>    ← 同 <id> 续接
POST /agents/<agent-name>/other   ← 新对话
```

### 3.4 Tasks

`session.task()` 跑**一次性子 agent**——共享 sandbox 和文件系统，但有独立消息历史，并从 cwd 重新发现 `AGENTS.md` + `.agents/skills/`。

```ts
const research = await session.task('Research the auth flow.', {
  cwd: '/workspace/project',
  agent: 'researcher',  // 用 defineAgentProfile 定义的 subagent
});
```

**这个设计让 Agent 内部能并行调度 subagent 做研究/探索**——主 agent 不阻塞。

---

## 四、核心特性拆解

### 4.1 内置 Virtual Sandbox（just-bash）

Flue 默认用 [just-bash](https://github.com/vercel-labs/just-bash)（Vercel Labs 出品）做 virtual sandbox——一个**轻量级的 Linux 兼容 Bash runtime**。

**为什么默认用 virtual sandbox 而不是真容器**：

- **快**——没有冷启动
- **便宜**——不需要为每个 agent 拉起一个容器
- **可扩展**——高流量场景跑得动
- **足够**——大部分 Agent 任务只是文件操作 + 命令执行

如果需要真 Linux 环境（git clone、npm install、跑 dev server），用 **Daytona connector** 切换到容器 sandbox。

### 4.2 Skills 导入为 Markdown

```ts
import review from '../skills/review/SKILL.md' with { type: 'skill' };

const agent = createAgent(() => ({
  model: 'anthropic/claude-sonnet-4-6',
  skills: [review],
}));
```

**关键点**：

- **运行时发现**——`session.skill('name')` 激活 workspace 里的 `AGENTS.md` 风格的 skills
- **静态导入**——打包期就校验 `SKILL.md` 合规性，并打包支持文件
- **安全**——`.env*`、`.ssh/`、`.aws/` 等敏感文件**拒绝 build**

**这意味着 Agent 的"业务逻辑"主要活在 Markdown**——skills 写规则、context 写约束、`AGENTS.md` 写指令。

### 4.3 Connectors（沙箱/服务集成）

Connector 不是 npm 包，是**写在 https://flueframework.com/cli/connectors/ 的 Markdown 安装说明**。让 AI coding agent 帮你装：

```bash
flue add                                            # 列出可用 connector
flue add daytona | claude                           # 装 Daytona + 配 adapter
flue add https://e2b.dev --category sandbox | claude  # 自定义 sandbox
```

**这种设计很妙**：Flue 不绑定特定 sandbox 提供商，加新 sandbox 不需要 PR Flue 主仓库。

### 4.4 Observability（可观测性）

内置 observability 钩子：

- **官方 OpenTelemetry adapter** — `@flue/opentelemetry`
- **Braintrust tracing example** — `examples/braintrust`
- **Sentry error reporting example** — `examples/sentry`

```ts
import { observe } from '@flue/runtime';
// or use the Braintrust / Sentry adapters
```

### 4.5 部署目标

```bash
flue build --target node          # Node.js 服务器（单 bundled .mjs）
flue build --target cloudflare    # Cloudflare Workers + Durable Objects
```

- **Node.js**：单 .mjs 文件直接 `node dist/server.mjs`
- **Cloudflare**：通过官方 Vite/workerd 集成，配合 `wrangler deploy`

**同一个 workflow 同时支持两种部署**——这正是"runtime-agnostic"的体现。

---

## 五、代码示例解析

### 5.1 Quickstart：翻译 Agent

```ts
// .flue/workflows/hello-world.ts
import { createAgent, type FlueContext, type WorkflowRouteHandler } from '@flue/runtime';
import * as v from 'valibot';

export const route: WorkflowRouteHandler = async (_c, next) => next();

const translator = createAgent(() => ({ model: 'anthropic/claude-sonnet-4-6' }));

export async function run({ init, payload }: FlueContext) {
  const harness = await init(translator);
  const session = await harness.session();
  const { data } = await session.prompt(
    `Translate this to ${payload.language}: "${payload.text}"`,
    {
      result: v.object({
        translation: v.string(),
        confidence: v.picklist(['low', 'medium', 'high']),
      }),
    },
  );
  return data;
}
```

**关注点**：

- `result: v.object({...})`——**typed, schema-validated data back from your agent**
- `route` 是 Hono middleware——**public HTTP exposure**
- `createAgent` 只配置模型（用 default sandbox + 默认 cwd）

### 5.2 Support Agent（Cloudflare 部署）

```ts
const support = createAgent(() => ({ model: 'openrouter/moonshotai/kimi-k2.6' }));

export async function run({ init, payload }: FlueContext) {
  const harness = await init(support);
  const session = await harness.session();
  await session.fs.mkdir('/workspace/articles', { recursive: true });
  await session.fs.writeFile('/workspace/articles/reset-password.md', '# Reset password...');
  return await session.prompt(`You are a support agent. ${payload.message}`);
}
```

**Cloudflare 自动持久化 session 状态**——几天/几周后客户回来，还能接着上次的对话。

### 5.3 CI Issue Triage

```ts
import { local } from '@flue/runtime/node';
const agent = createAgent(() => ({
  sandbox: local({ env: { GH_TOKEN: process.env.GH_TOKEN } }),
  model: 'anthropic/claude-opus-4-7',
}));

const { data } = await session.skill('triage', {
  args: { issueNumber: payload.issueNumber },
  result: v.object({
    severity: v.picklist(['low', 'medium', 'high', 'critical']),
    reproducible: v.boolean(),
    summary: v.string(),
    fix_applied: v.boolean(),
  }),
});
```

**`local()` sandbox**——Agent 直接用 host filesystem + shell。**适合 CI runner**（`gh`、`git`、`npm` 已在 PATH，runner 本身就是隔离边界）。

### 5.4 Coding Agent（真实容器）

```ts
import { daytona } from '../connectors/daytona';
const client = new Daytona({ apiKey: env.DAYTONA_API_KEY });
const sandbox = await client.create();
const setupAgent = createAgent(() => ({ sandbox: daytona(sandbox), model: 'openai/gpt-5.5' }));
// 先 clone repo、npm install...
// 然后再开第二个 harness 在 /workspace/project 里跑
```

**两个 harness 共享同一个 sandbox**——一个负责环境准备（setup），一个负责项目内工作（project）。

---

## 六、Provider Settings（自定义端点）

企业常用私有 API gateway、自托管 OpenAI 兼容端点：

```ts
// .flue/app.ts
import { configureProvider } from '@flue/runtime';
import { flue } from '@flue/runtime/routing';

export default {
  fetch(req, env, ctx) {
    configureProvider('anthropic', {
      baseUrl: env.ANTHROPIC_BASE_URL,
      headers: { 'X-Custom-Auth': env.GATEWAY_KEY },
      apiKey: 'dummy',  // proxy 用自己的 auth
    });
    return flue().fetch(req, env, ctx);
  },
};
```

**这个设计给企业留出了入口**——所有 harness/session 都走统一 provider 配置，audit logging、traffic routing、self-hosted 模型都好用。

---

## 七、与同类框架对比

| 框架 | 运行时 | Sandbox | Skills | 跨部署 | 状态 |
|------|--------|---------|--------|--------|------|
| **Flue** | Node.js / Cloudflare | just-bash (default) / Daytona (real) | Markdown 导入 + workspace 发现 | ✅ | Experimental |
| LangGraph | Python | 自定义 | LangGraph tools | 多（自部署） | GA |
| Mastra | Node.js | 自定义 | TS function tools | 部分 | Beta |
| Vercel AI SDK | Node.js / Edge | — | — | ✅ | GA |
| Inngest AgentKit | Node.js | — | 函数 | 部分 | Beta |

**Flue 的独特定位**：

1. **TypeScript + Cloudflare Workers 一等公民**——边缘部署 Agent
2. **just-bash virtual sandbox by default**——成本极低
3. **skills = Markdown 导入**——把"业务逻辑"放 Markdown
4. **runtime-agnostic**——同一个 workflow 跑 Node / Cloudflare / CI

---

## 八、适用边界

### 8.1 适合

- **TypeScript 团队**构建生产级 Agent 后端
- **Cloudflare Workers** 上跑 Agent（持久化 + 边缘部署）
- **CI/CD 集成**——自动 triage、自动 code review、自动文档生成
- **多 deployment target 场景**——开发用 Node.js、生产用 Cloudflare

### 8.2 不适合

- **Python 团队**——LangGraph 仍是更好的选择
- **纯前端聊天 UI**——Flue 是 backend runtime，前端用别的
- **预算紧张且需要真容器的场景**——just-bash 不够时，Daytona / E2B 是付费的
- **已经在用 LangGraph 且不想迁移**——迁移成本可能不值

---

## 九、风险与未知

| 风险 | 说明 |
|------|------|
| **Experimental** | 仓库顶部明确标了，APIs may change |
| **生态较新** | withastro 团队是前端起家，Agent 生态还在铺 |
| **just-bash 能力有限** | virtual sandbox 跑不动 git clone / npm install 这种重活 |
| **文档分散** | 主文档在 flueframework.com，仓库 README 是 reference |
| **MCP 局限** | `connectMcpServer()` 不自动检测 transport、不 spawn stdio server、不处理 OAuth——enterprise 集成需要自己包一层 |

---

## 十、为什么值得关注

1. **Astro 团队出品**——前端框架功底扎实，Flue 的 DX 设计有"Next.js for agents"的味道
2. **runtime-agnostic 是真做**——不只是口号，Node.js / Cloudflare / CI 都能跑同一份代码
3. **just-bash virtual sandbox**——成本模型完全不同（不必为每个 agent 拉容器）
4. **Skills = Markdown**——把"Agent 业务逻辑"放 Markdown 是未来方向

**最大不确定性**：

- 状态是 **Experimental**——生产用要慎重
- withastro 是前端团队，Agent 生态的深度还得观察

---

## 十一、快速开始

```bash
# 安装 CLI
npm install -g @flue/cli

# 新建项目
flue create my-agent
cd my-agent
npm install

# 开发
flue dev --target node          # Node.js
flue dev --target cloudflare    # Cloudflare

# 部署
flue build --target node
flue build --target cloudflare
```

更详细的 workflow 模板见 [flueframework.com/docs](https://flueframework.com/docs/)。

---

## 十二、相关项目

- [withastro/astro](https://github.com/withastro/astro) — Flue 兄弟项目，Web 框架
- [vercel-labs/just-bash](https://github.com/vercel-labs/just-bash) — Flue 默认 virtual sandbox
- [daytonaio/daytona](https://github.com/daytonaio/daytona) — Flue connector 之一
- [nicobailon/mcporter](https://github.com/nicobailon/mcporter) — MCP 桥接（Agent Reach 也用）
- [Mastra](https://github.com/mastra-ai/mastra) — TypeScript Agent framework 对比参考
- [LangGraph](https://github.com/langchain-ai/langgraph) — Python 端同类项目

---

> **最后更新**：2026-06-06
> **许可证**：Apache-2.0
> **仓库**：[withastro/flue](https://github.com/withastro/flue)
> **文档**：[flueframework.com](https://flueframework.com/)
