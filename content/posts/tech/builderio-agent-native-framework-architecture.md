---
title: "BuilderIO/agent-native 拆解：一个让 Agent 和 UI 共享状态的开放框架"
date: "2026-06-19T21:04:05+08:00"
slug: "builderio-agent-native-framework-architecture"
description: "BuilderIO 发布的 agent-native 框架把 GUI 与 Agent 视为同等公民，用一条 defineAction 把 UI、HTTP、MCP、A2A、CLI 五种调用入口打通。本文从核心抽象、三种产品形态、协议栈、决策边界四个角度做原理拆解。"
draft: false
categories: ["技术笔记"]
tags: ["Agent", "MCP", "A2A", "CRDT", "全栈框架"]
---

## 核心判断

agent-native 不是一个"聊天 + 工具调用"的 chatbot 框架，而是 Builder.io 用来把自家 SaaS 改造成"Agent + UI 双形态"产品的底座。它最关键的设计是**让一个 Action 同时被 6 种入口消费**：UI 点击、Agent 对话、HTTP API、MCP Server、A2A 调用、CLI 命令。

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

这段代码不是普通的 server action——它声明的是一个**协议无关的工作单元**，由框架根据上下文决定执行路径。这意味着一个产品改一处 Action，UI 按钮、Agent 工具、外部 MCP Client、A2A 远端 agent 都能用上。

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

框架默认**自带一组协议适配**而不是每个 feature 单独接入：

- **A2A**（Agent-to-Agent）：Agent 之间相互发现并跨应用调用
- **MCP** + **MCP Apps** + **远程 MCP OAuth** + **MCP Client**
- **AG-UI**、**OpenAI**、**Claude Agent SDK**、**Vercel AI SDK** 聊天 runtime
- **HTTP / CLI** Action 调用、**原生 chat widget**、**deep link**

这种"协议伴随框架"的设计避免了 AI 产品最常见的痛点：先做 chat，再补 MCP，再补 A2A，每个新协议都改一遍核心层。

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

## 写给读者的判断

agent-native 在 2026 年这个时间点切中的痛点很准：**真正阻碍 Agent 落地的不是模型能力，而是 UI 与 Agent 的状态脱节**。它用 CRDT 共享状态 + `defineAction` 协议无关层 + 协议伴随框架三招，把"Agent 协作应用"的工程量压到了模板级别。

如果你的产品天然有"用户与 Agent 同时在操作同一份数据"的属性，这个框架值得认真评估；如果只是做一个"能聊天的内部工具"，它的复杂度远超必要。
