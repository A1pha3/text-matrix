---
title: "BuilderIO/agent-native 拆解：一个让 Agent 和 UI 共享状态的开放框架"
date: "2026-06-19T21:04:05+08:00"
slug: "builderio-agent-native-framework-architecture"
description: "BuilderIO 发布的 agent-native 框架把 GUI 与 Agent 视为同等公民，用一条 defineAction 把 UI、HTTP、MCP、A2A、CLI、Agent Tool Call 六种调用入口打通。本文从核心抽象、三种产品形态、协议栈、决策边界四个角度做原理拆解。"
draft: false
categories: ["技术笔记"]
tags: ["Agent", "MCP", "A2A", "CRDT", "全栈框架"]
---
 
## 快速信息卡

| 项目 | 信息 |
|------|------|
| **Stars** | 2,504+ |
| **Forks** | 244+ |
| **许可证** | 未指定 |
| **语言** | TypeScript |
| **仓库** | [BuilderIO/agent-native](https://github.com/BuilderIO/agent-native) |

agent-native 是 Builder.io 用来把自家 SaaS 改造成"Agent + UI 双形态"产品的底座。

## 学习目标
 
读完本文后你应当能够：

1. 说清 `defineAction` 为什么能让一个工作单元被 6 种入口消费，以及框架在运行时如何选择执行路径
2. 区分 Headless / Rich chat / Whole app 三种产品形态的边界与升级路径
3. 列出框架默认携带的协议适配清单，并解释"协议随框架一起更新"对工程维护成本的影响
4. 判断自己的产品是否适合引入 agent-native，并给出可量化的取舍依据

## 目录

- [核心判断](#核心判断)
- [系统地图](#系统地图)
- [三种产品形态](#三种产品形态)
- [协议栈（关键差异化）](#协议栈关键差异化)
- [协作与状态层](#协作与状态层)
- [模板与脚手架](#模板与脚手架)
- [visual-plan 与 visual-recap](#visual-plan-与-visual-recap)
- [适用边界](#适用边界)
- [任务流案例](#任务流案例)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [常见问题](#常见问题)
- [写给读者的判断](#写给读者的判断)

## 核心判断

agent-native 是 Builder.io 用来把自家 SaaS 改造成"Agent + UI 双形态"产品的底座。它最关键的设计是**让一个 Action 同时被 6 种入口消费**：UI 点击、Agent 对话、HTTP API、MCP Server、A2A 调用、CLI 命令。

```ts
export default defineAction({
  schema: z.object({
    emailId: z.string(),
    body: z.string(),
  }),
  run: async ({ emailId, body }) => {
    await db.insert(replies).values({ emailId, body });
  },
});
```

这段代码声明的是一个**与调用协议解耦的工作单元**：开发者只定义 schema 和 `run`，由框架根据上下文（请求来自 UI、HTTP、MCP 还是 A2A）决定执行路径。一个产品改一处 Action，UI 按钮、Agent 工具、外部 MCP Client、A2A 远端 agent 都能用上。这也是它和传统 server action 的本质差异——server action 绑定单一调用方，`defineAction` 绑定的是契约本身。

## 系统地图

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent-Native Runtime                      │
│                                                              │
│   defineAction ─┬─> UI (实时同步、CRDT)                       │
│                 ├─> HTTP API                                  │
│                 ├─> MCP Server                                │
│                 ├─> A2A                                       │
│                 ├─> CLI                                       │
│                 └─> Agent Tool Call                           │
│                                                              │
│   共享：SQL 状态 + 身份 + Skills + Memory + Jobs + Observability │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        任意 SQL 数据库           任意 Nitro 兼容 Host
       （Drizzle 支持的）      （Cloudflare / Vercel / Node）
```

## 三种产品形态

agent-native 把"Agent 包装程度"切成 3 档，同一套底层 primitive 可以根据业务选择深度：

| 形态 | 适用场景 | 关键 primitive |
| --- | --- | --- |
| **Headless** | 把 Agent 当成 API/MCP/A2A 服务对外提供，UI 是后加的 | `defineAction`、auth、skills、memory、jobs |
| **Rich chat** | 独立或嵌入的 chat 界面，原生表格、图表、审批流 | 共享 chat runtime + BYO runtime adapter + action-declared native renderers |
| **Whole app** | 完整 SaaS，Agent 居于中央但能"挪到侧边栏"，与 App 状态实时同步 | SQL state、actions、context awareness、live sync |

README 给出的"决策指南"建议先用 Headless 验证业务流程，再升到 Rich chat，最后才考虑 Whole app。

## 协议栈（关键差异化）

框架默认**自带一组协议适配**，而不是让每个 feature 单独接入：

- **A2A**（Agent-to-Agent）：Agent 之间相互发现并跨应用调用
- **MCP** + **MCP Apps** + **远程 MCP OAuth** + **MCP Client**
- **AG-UI**、**OpenAI**、**Claude Agent SDK**、**Vercel AI SDK** 聊天 runtime
- **HTTP / CLI** Action 调用、**原生 chat widget**、**deep link**

把协议适配放进框架核心层，带来的工程收益是：当 MCP 规范更新或 A2A 新增能力时，升级一个依赖即可让所有 Action 同步获得新协议版本，避免了"先做 chat，再补 MCP，再补 A2A，每个新协议都改一遍核心层"的常见维护路径。代价是团队需要接受框架对协议实现深度的判断，无法自行替换底层 client。

## 协作与状态层

- **CRDT 合并 + live presence**：人和 Agent 同时编辑同一份文档，光标 / 选区 / 谁在看哪一页都同步
- **Per-user workspace**：每个用户一份 SQL 后端的 Skills、Memory、Instructions、Sub-agents、MCP Servers 配置
- **Reusable integrations**：在 Dispatch 里"一次接入，授权给多个 app 共享凭证"，避免每个 Agent 重复 OAuth

## 模板与脚手架

框架提供 6 个完整可 clone 的 SaaS 模板（Calendar / Content / Plans / Slides / Analytics / Clips），全部是**真 SaaS**而不是"半成品 demo"：

```bash
npx @agent-native/core@latest create my-platform
cd my-platform
pnpm install
pnpm dev
```

支持 monorepo 多 app（共享 auth、A2A 自动跨应用调用），也支持 `--standalone` 模式做单 app。

## 一个杀手锏：`/visual-plan` / `/visual-recap`

```bash
npx @agent-native/core@latest skills add visual-plan
```

为 Claude Code / Codex / Cursor / GitHub Copilot / VS Code 等 coding agent 装两个 slash command：

- `/visual-plan`：写代码前生成可视化的实现规划（架构图、UI 线框、文件级 map、可批注）
- `/visual-recap`：PR 提交后生成高层次的视觉复盘（schema、API、文件 before/after、review 链接）

等于把"计划 → 实现 → 复盘"三段切到可视化层，减少 coding agent 写代码前的盲区。

## 适用边界

- ✅ **适合**：
  - 想做"Agent + GUI"双形态产品的团队（CRM、邮件、日历、文档等结构化领域）
  - 已经在维护 SaaS，想给现有 UI 加 Agent 入口并保持状态同步
  - 需要多协议暴露（A2A + MCP + HTTP）的中后台产品
- ❌ **不适合**：
  - 纯单页 LLM Chatbot 玩具（太重，用 Dify / Vercel AI SDK 即可）
  - 不需要实时多人 / Agent 协作的离线工具
  - 想完全控制前端框架（agent-native 强绑 CRDT + Drizzle + Nitro，迁移成本高）
- ⚠️ **关注点**：
  - "Agent 修改自己的 app" 是一个大胆的能力（README 强调"apps improve themselves"），生产环境必须配合审计与审批流
  - `defineAction` 的 schema 用 Zod，团队需要接受 Zod 作为运行时契约
  - 协议适配器覆盖度虽广，但每种协议的实现深度需要看 `agent-native.com/docs` 实际文档，本文以 README 为准

---

## 任务流案例

### 案例：用日历应用创建会议（UI + Agent 双入口）

假设你有一个日历 SaaS，用 agent-native 构建了"创建会议"这个 Action：

```ts
export default defineAction({
  schema: z.object({
    title: z.string(),
    startTime: z.string(),
    attendees: z.array(z.string()),
  }),
  run: async ({ title, startTime, attendees }) => {
    await db.insert(events).values({ title, startTime, attendees });
  },
});
```

**场景 1：用户通过 UI 创建会议**

1. 用户在日历 UI 点击"创建会议"按钮
2. UI 调用 `defineAction` 生成的客户端方法
3. 框架通过 CRDT 实时同步状态到其他在线用户
4. 数据库写入会议记录

**场景 2：用户通过 Agent 对话创建会议**

1. 用户在 chat 界面输入："帮我创建一个明天下午3点的团队会议"
2. Agent 识别意图，调用"创建会议"工具（由 `defineAction` 自动生成）
3. Agent 填充参数：`title: "团队会议"`, `startTime: "2026-06-27T15:00"`, `attendees: ["alice@example.com", "bob@example.com"]`
4. 框架执行 `run` 方法，写入数据库
5. UI 实时更新，显示新会议

**场景 3：外部系统通过 MCP 创建会议**

1. 用户的邮件客户端（支持 MCP）检测到会议邀请
2. 邮件客户端调用 agent-native 暴露的 MCP Server 的"创建会议"工具
3. 框架执行 `run` 方法，写入数据库
4. 用户的日历 UI 实时更新

这个案例展示了 `defineAction` 的核心价值：**一个 Action 定义，六种调用方式，共享状态同步**。

---

## 自测题

### 基础概念

**问题 1**：`defineAction` 与传统 server action 的本质差异是什么？

<details>
<summary>参考答案</summary>

传统 server action 绑定单一调用方（通常是 UI），而 `defineAction` 绑定的是契约本身。一个 `defineAction` 定义的工作单元可以被 6 种入口消费：UI 点击、Agent 对话、HTTP API、MCP Server、A2A 调用、CLI 命令。

</details>

**问题 2**：agent-native 的三种产品形态是什么？它们的升级路径如何？

<details>
<summary>参考答案</summary>

三种产品形态：
1. **Headless**：把 Agent 当成 API/MCP/A2A 服务对外提供，UI 是后加的
2. **Rich chat**：独立或嵌入的 chat 界面，原生表格、图表、审批流
3. **Whole app**：完整 SaaS，Agent 居于中央但能"挪到侧边栏"，与 App 状态实时同步

升级路径：README 建议先用 Headless 验证业务流程，再升到 Rich chat，最后才考虑 Whole app。

</details>

### 实践操作

**问题 3**：你正在评估是否引入 agent-native 到你的 SaaS 产品，应该考虑哪些因素？

<details>
<summary>参考答案</summary>

需要考虑：
1. **产品形态**：是否需要"Agent + GUI"双形态？如果只需要单页 LLM Chatbot，用 Dify 或 Vercel AI SDK 更合适
2. **实时协作需求**：是否需要人和 Agent 同时编辑同一份数据？如果需要，agent-native 的 CRDT 共享状态是核心优势
3. **协议暴露需求**：是否需要多协议暴露（A2A + MCP + HTTP）？如果需要，框架自带的协议适配是优势
4. **前端框架绑定**：是否能接受 CRDT + Drizzle + Nitro 绑定？如果团队想完全控制前端框架，迁移成本高
5. **协议实现深度**：框架的协议适配是否足够深？需要看 `agent-native.com/docs` 实际文档

</details>

**问题 4**：agent-native 的协议栈包含哪些协议？把协议适配放进框架核心层有什么优缺点？

<details>
<summary>参考答案</summary>

协议栈包含：
- A2A（Agent-to-Agent）
- MCP + MCP Apps + 远程 MCP OAuth + MCP Client
- AG-UI、OpenAI、Claude Agent SDK、Vercel AI SDK 聊天 runtime
- HTTP / CLI Action 调用、原生 chat widget、deep link

优点：
- 当 MCP 规范更新或 A2A 新增能力时，升级一个依赖即可让所有 Action 同步获得新协议版本
- 避免了"先做 chat，再补 MCP，再补 A2A，每个新协议都改一遍核心层"的常见维护路径

缺点：
- 团队需要接受框架对协议实现深度的判断，无法自行替换底层 client

</details>

**问题 5**：你正在设计一个需要 Agent 协作的 SaaS 产品，agent-native 的哪些特性最有价值？

<details>
<summary>参考答案</summary>

最有价值的特性：
1. **CRDT 合并 + live presence**：人和 Agent 同时编辑同一份文档，光标 / 选区 / 谁在看哪一页都同步
2. **Per-user workspace**：每个用户一份 SQL 后端的 Skills、Memory、Instructions、Sub-agents、MCP Servers 配置
3. **Reusable integrations**：在 Dispatch 里"一次接入，授权给多个 app 共享凭证"，避免每个 Agent 重复 OAuth
4. **`defineAction`**：一个 Action 定义，六种调用方式，共享状态同步

</details>

---

## 进阶路径

### 1. 深入理解 agent-native 架构

- 阅读 [agent-native 文档](https://agent-native.com/docs)
- 理解 `defineAction` 的运行时选择逻辑：框架如何根据上下文（请求来自 UI、HTTP、MCP 还是 A2A）决定执行路径
- 深入研究 CRDT 共享状态：如何实现的？性能如何？冲突解决策略是什么？
- 对比其他框架：Vercel AI SDK、Claude Agent SDK、LangChain 的 Agent 协作方案

### 2. 从模板入手实践

- 运行 `npx @agent-native/core@latest create my-platform` 创建一个模板项目
- 选择与你业务最接近的模板（Calendar / Content / Plans / Slides / Analytics / Clips）
- 理解模板的代码结构：如何定义 Action、如何处理认证、如何配置 MCP Server
- 修改模板，添加自己的 Action

### 3. 集成到现有 SaaS 产品

- 评估现有产品的状态管理层：是否能迁移到 CRDT + Drizzle？
- 选择第一个集成点：通常是一个简单的 Action（如"创建会议"）
- 逐步实现：先实现 UI 入口，再实现 Agent 入口，最后暴露 MCP Server
- 测试实时同步：多个用户同时编辑，人 + Agent 同时操作

### 4. 贡献到 agent-native 项目

- 从 [GitHub 仓库](https://github.com/BuilderIO/agent-native) 克隆代码
- 阅读贡献指南（如果有）
- 从简单 issue 开始：修复文档错误、添加单元测试、优化错误处理
- 理解代码结构：核心框架、协议适配器、模板、文档

### 5. 探索高级功能

- **A2A 跨应用调用**：配置多个 app 的 A2A 调用
- **MCP Server 开发**：为自己的服务提供 MCP 接口
- **自定义 chat runtime**：集成到自己的 chat UI
- **性能优化**：当 Action 数量增多、并发调用增加时，如何优化性能？

---

## 常见问题

### agent-native 与 Vercel AI SDK 有什么区别？

Vercel AI SDK 主要关注 chat runtime 和 LLM 调用，而 agent-native 关注的是"Agent 与 UI 共享状态"。如果你只需要一个 chat interface，用 Vercel AI SDK 更合适；如果你需要人和 Agent 同时操作同一份数据，agent-native 的 CRDT 共享状态是核心优势。

### agent-native 的学习曲线如何？

agent-native 的概念较多（`defineAction`、CRDT、协议适配等），学习曲线中等。建议先从模板入手，理解一个完整的 Action 如何被多种入口调用，然后逐步深入框架核心。

### 生产环境使用 agent-native 需要注意什么？

需要注意：
1. **审计与审批流**：README 强调"apps improve themselves"，生产环境必须配合审计与审批流
2. **Zod schema 管理**：`defineAction` 的 schema 用 Zod，团队需要接受 Zod 作为运行时契约
3. **协议实现深度**：框架的协议适配是否足够深？需要看实际文档
4. **性能监控**：需要监控 Action 执行时间、并发量、错误率

### agent-native 的许可证是什么？

仓库未指定许可证。在生产环境使用前，需要联系 Builder.io 团队确认许可证条款。

### 如何获取 agent-native 的技术支持？

- 阅读 [agent-native 文档](https://agent-native.com/docs)
- 在 [GitHub 仓库](https://github.com/BuilderIO/agent-native) 提交 issue
- 加入 Builder.io 社区（如果有）

---

## 写给读者的判断

agent-native 在 2026 年这个时间点切中的痛点很准：**真正阻碍 Agent 落地的不是模型能力，而是 UI 与 Agent 的状态脱节**。它用 CRDT 共享状态 + `defineAction` 协议无关层 + 协议伴随框架三招，把"Agent 协作应用"的工程量压到了模板级别。

如果你的产品天然有"用户与 Agent 同时在操作同一份数据"的属性，这个框架值得认真评估；如果只是做一个"能聊天的内部工具"，它的复杂度远超必要。
