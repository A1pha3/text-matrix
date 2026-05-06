---
title: "Vercel Open Agents：2.4K Stars的云端Agent部署模板——Web/Workflow/Sandbox三层架构、GitHub集成、Session共享"
date: "2026-04-16T02:00:00+08:00"
slug: "vercel-open-agents-cloud-agent-template"
description: "Vercel Open Agents是2.4K Stars的开源模板，用于在Vercel上构建和运行云端Agent。三层架构（Web/Agent Workflow/Sandbox），支持GitHub集成、自动commit/PR、Session共享。"
draft: false
categories: ["技术笔记"]
tags: ["Vercel", "Agent", "TypeScript", "云端", "GitHub集成"]
---

# Vercel Open Agents：2.4K Stars的云端Agent部署模板——Web/Workflow/Sandbox三层架构、GitHub集成、Session共享

> **目标读者**：后端开发者、AI应用架构师、对云端Agent部署感兴趣的工程师
> **预计阅读时间**：40-55分钟
> **前置知识**：TypeScript/Next.js 基础、了解 Agent 基本概念
> **难度定位**：⭐⭐⭐⭐ 专家设计

---

## §1 学习目标

完成本篇文章后，你将能够：

1. **理解 Open Agents 的三层架构**：Web / Agent Workflow / Sandbox VM
2. **掌握关键设计决策**：为何 Agent 不运行在 Sandbox 内
3. **部署自己的 Open Agents 实例**：从 Fork 到完整运行
4. **理解 GitHub 集成**：如何实现 repo 访问、commit 和 PR
5. **使用 Session 共享和声音输入**：增强用户体验
6. **根据需求定制**：fork 后如何修改和适配

---

## §2 项目概览

### 2.1 基本信息

| 属性 | 值 |
|------|------|
| **Stars** | 2,433 ⭐ |
| **组织** | Vercel Labs |
| **语言** | TypeScript |
| **许可证** | MIT |
| **官网** | https://open-agents.dev |
| **创建时间** | 2025-12-26 |

### 2.2 核心特性

| 特性 | 说明 |
|------|------|
| **三层架构** | Web → Agent Workflow → Sandbox VM |
| **持久化执行** | Workflow SDK 支持的持久化运行 |
| **沙箱隔离** | Vercel Sandboxes 基于快照恢复 |
| **GitHub 集成** | repo 访问、branch 管理、commit、PR |
| **Session 共享** | 只读链接分享对话 |
| **语音输入** | ElevenLabs 转录（可选） |

### 2.3 架构概览

```
┌─────────────────────────────────────────────────────┐
│                      Web Layer                      │
│            (Next.js App: Auth, Sessions, Chat UI)   │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│                 Agent Workflow Layer                 │
│        (Durable Workflow: Agent Runtime + Tools)     │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│                    Sandbox Layer                     │
│   (Vercel Sandbox VM: Filesystem, Shell, Git, Dev)  │
└─────────────────────────────────────────────────────┘
```

---

## §3 核心设计决策：Agent 不在 Sandbox 内

### 3.1 这是最重要的设计决策

Open Agents 的核心理念：

> **Agent does not run inside the VM. It runs outside the sandbox and interacts with it through tools.**

```
Agent (outside) ←── tools ───→ Sandbox VM (inside)
```

### 3.2 为什么这样设计

| 优势 | 说明 |
|------|------|
| **生命周期解耦** | Agent 执行不绑定单个请求周期 |
| **沙箱独立休眠** | Sandbox 可以休眠和恢复，不影响 Agent |
| **技术选型灵活** | Model/Provider 和 Sandbox 实现可以独立演进 |
| **保持 VM 纯净** | VM 保持为纯执行环境，不成为控制平面 |

### 3.3 传统方案的问题

```
传统方案：Agent 在 VM 内部
┌─────────────────────────────────────┐
│ VM: Agent + Runtime + Filesystem    │
│   ↑                                  │
│   └── 请求生命周期绑定               │
│   └── VM 不可独立休眠               │
│   └── Agent 和 VM 耦合               │
└─────────────────────────────────────┘
```

### 3.4 Open Agents 的方案

```
Open Agents 方案：Agent 在 VM 外部
┌─────────────────────────────────────┐
│ Agent Runtime (outside Sandbox)     │
│   ├── 文件读写工具                   │
│   ├── Shell 执行工具                 │
│   ├── Git 操作工具                   │
│   └── 搜索工具                       │
└─────────────────────────────────────┘
            ↓ tools
┌─────────────────────────────────────┐
│ Sandbox VM (pure execution)          │
│   ├── Filesystem                     │
│   ├── Shell                          │
│   └── Ports: 3000, 5173, 4321, 8000  │
└─────────────────────────────────────┘
```

---

## §4 三层架构详解

### 4.1 Web Layer

基于 Next.js，负责：

| 功能 | 说明 |
|------|------|
| **Auth** | Vercel OAuth 登录 |
| **Sessions** | 聊天会话管理 |
| **Chat UI** | 流式响应界面 |
| **Streaming** | Agent 响应的流式传输 |

### 4.2 Agent Workflow Layer

基于 Vercel Durable Objects，实现：

| 功能 | 说明 |
|------|------|
| **持久化执行** | Agent 可以跨多个请求持续运行 |
| **工具调用** | file/search/shell/task/skill/web 工具 |
| **流式处理** | 支持流式输出到 Web |
| **取消功能** | 可以取消正在运行的 Agent |

### 4.3 Sandbox Layer

Vercel Sandbox 是执行环境：

| 属性 | 说明 |
|------|------|
| **隔离** | 快照隔离的 VM |
| **文件系统** | 完整的文件系统访问 |
| **Shell** | bash/zsh 命令执行 |
| **Git** | git 操作支持 |
| **Dev Servers** | 暴露端口 3000/5173/4321/8000 |
| **休眠** | 空闲后自动休眠 |

---

## §5 当前功能详解

### 5.1 Chat-Driven Coding Agent

核心 Agent 能力：

| 工具 | 功能 |
|------|------|
| **file** | 读写和编辑文件 |
| **search** | 代码搜索 |
| **shell** | 执行 Shell 命令 |
| **task** | 任务拆解和执行 |
| **skill** | 调用预定义技能 |
| **web** | 网页访问和信息获取 |

### 5.2 Durable Multi-Step Execution

```typescript
// Agent 运行在 Durable Workflow 中
import { WorkflowClient } from '@vercel/workflow';

const client = new WorkflowClient();

async function runAgent(userMessage: string) {
  // 启动持久化 Workflow
  const run = client.run('agent-workflow', {
    args: [userMessage],
    signal: new AbortController().signal  // 支持取消
  });

  // 流式获取响应
  for await (const event of run.stream()) {
    if (event.type === 'text') {
      // 流式显示
      display(event.text);
    }
  }

  return run.output;
}
```

**特性**：
- Agent 可以跨多个持久化步骤继续执行
- 活跃的运行可以通过重新连接流恢复
- Workflow SDK 提供可靠的持久化保证

### 5.3 GitHub 集成

支持完整的 GitHub 工作流：

| 功能 | 说明 |
|------|------|
| **Repo 访问** | 连接 GitHub，访问 public/private repos |
| **Branch 管理** | 创建和切换分支 |
| **Auto-commit** | 成功后自动提交（可选） |
| **Auto-push** | 自动推送到远程（可选） |
| **PR 创建** | 自动创建 Pull Request（可选） |

**配置需要**：

```env
NEXT_PUBLIC_GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_APP_ID=
GITHUB_APP_PRIVATE_KEY=
NEXT_PUBLIC_GITHUB_APP_SLUG=
GITHUB_WEBHOOK_SECRET=
```

### 5.4 Session 共享

通过只读链接分享对话：

```
用户 A 完成任务后生成分享链接
    ↓
分享给用户 B（只读权限）
    ↓
用户 B 可以查看完整对话记录
    ↓
但不能继续对话
```

### 5.5 语音输入（可选）

使用 ElevenLabs 转录：

```env
ELEVENLABS_API_KEY=xxx
```

启用后，用户可以通过语音输入代替打字。

---

## §6 环境变量详解

### 6.1 最小运行时

仅需两个变量即可启动应用：

```env
POSTGRES_URL=       # PostgreSQL 数据库连接
JWE_SECRET=         # JWT Web Encryption secret
```

### 6.2 登录所需

需要完整的 OAuth 登录：

```env
ENCRYPTION_KEY=                        # 密钥
NEXT_PUBLIC_VERCEL_APP_CLIENT_ID=     # Vercel OAuth App ID
VERCEL_APP_CLIENT_SECRET=             # Vercel OAuth App Secret
```

### 6.3 GitHub 集成所需

完整 GitHub 功能：

```env
NEXT_PUBLIC_GITHUB_CLIENT_ID=         # GitHub App Client ID
GITHUB_CLIENT_SECRET=                 # GitHub App Client Secret
GITHUB_APP_ID=                        # GitHub App ID
GITHUB_APP_PRIVATE_KEY=               # GitHub App 私钥
NEXT_PUBLIC_GITHUB_APP_SLUG=         # GitHub App slug
GITHUB_WEBHOOK_SECRET=                # Webhook 密钥
```

### 6.4 可选变量

```env
REDIS_URL=              # Skills 元数据缓存
KV_URL=                 # Upstash KV
VERCEL_PROJECT_PRODUCTION_URL=         # 生产环境 URL
NEXT_PUBLIC_VERCEL_PROJECT_PRODUCTION_URL=
VERCEL_SANDBOX_BASE_SNAPSHOT_ID=        # 沙箱基础快照
ELEVENLABS_API_KEY=     # 语音转录
```

---

## §7 部署指南

### 7.1 推荐部署路径

**在 Vercel 上一键部署**：

1. Fork 本仓库
2. 创建 PostgreSQL 数据库（推荐 Neon）
3. 生成必要的密钥
4. 导入到 Vercel
5. 配置环境变量
6. 部署

### 7.2 部署步骤详解

**Step 1: Fork 仓库**

```bash
# 在 GitHub 上 fork
# https://github.com/vercel-labs/open-agents
```

**Step 2: 创建数据库**

推荐使用 Neon：

```bash
# 在 https://neon.tech 创建数据库
# 复制 POSTGRES_URL
```

**Step 3: 生成密钥**

```bash
# 生成 JWE_SECRET
openssl rand -base64 32 | tr '+/' '-_' | tr -d '=\n'
# 输出类似: ZkqM8dL2Xw7Yr5K3Hs6Nm4Bv9T1Qj7P

# 生成 ENCRYPTION_KEY
openssl rand -hex 32
# 输出类似: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

**Step 4: 导入到 Vercel**

```bash
# 在 https://vercel.com 导入
```

**Step 5: 配置环境变量**

在 Vercel 项目设置中添加：

```env
POSTGRES_URL=postgresql://user:pass@host/db
JWE_SECRET=your_jwe_secret
ENCRYPTION_KEY=your_encryption_key
NEXT_PUBLIC_VERCEL_APP_CLIENT_ID=your_client_id
VERCEL_APP_CLIENT_SECRET=your_secret
```

**Step 6: 创建 Vercel OAuth App**

回调 URL：
```
https://YOUR_DOMAIN/api/auth/vercel/callback
```

本地开发：
```
http://localhost:3000/api/auth/vercel/callback
```

**Step 7: 配置 GitHub App（可选）**

GitHub App 设置：

- Homepage URL: `https://YOUR_DOMAIN`
- Callback URL: `https://YOUR_DOMAIN/api/github/app/callback`
- Setup URL: `https://YOUR_DOMAIN/api/github/app/callback`

需要启用：**"Request user authorization (OAuth) during installation"**

### 7.3 本地开发

```bash
# 1. 安装依赖
bun install

# 2. 创建环境文件
cp apps/web/.env.example apps/web/.env

# 3. 填写必要值
# POSTGRES_URL, JWE_SECRET, ENCRYPTION_KEY 等

# 4. 启动
bun run web
```

---

## §8 仓库结构解析

### 8.1 目录结构

```
open-agents/
├── apps/
│   └── web/                    # Next.js 应用
│       ├── src/
│       │   ├── app/           # Next.js App Router
│       │   ├── components/    # React 组件
│       │   ├── lib/          # 工具函数
│       │   └── styles/       # 样式
│       ├── .env.example      # 环境变量模板
│       └── package.json
├── packages/
│   ├── agent/                # Agent 实现
│   │   ├── src/
│   │   │   ├── tools/        # 工具定义
│   │   │   ├── subagents/    # 子代理
│   │   │   └── skills/       # 技能
│   │   └── package.json
│   ├── sandbox/              # Sandbox 抽象
│   │   └── src/
│   │       └── vercel.ts     # Vercel Sandbox 集成
│   └── shared/               # 共享工具
│       └── src/
├── README.md
└── package.json
```

### 8.2 Agent 包详解

`packages/agent` 包含：

| 模块 | 说明 |
|------|------|
| `tools/` | file/search/shell/task/skill/web 工具 |
| `subagents/` | 子代理实现 |
| `skills/` | 可复用的技能定义 |

### 8.3 Sandbox 包详解

`packages/sandbox` 包含：

| 模块 | 说明 |
|------|------|
| `vercel.ts` | Vercel Sandbox 集成 |
| `snapshot.ts` | 快照管理 |
| `ports.ts` | 端口暴露管理 |

---

## §9 工具详解

### 9.1 File Tools

```typescript
// 文件读取
const content = await tools.file.read({
  path: 'src/app.js',
  encoding: 'utf-8'
});

// 文件写入
await tools.file.write({
  path: 'src/new-file.js',
  content: 'console.log("hello");'
});

// 文件编辑
await tools.file.edit({
  path: 'src/app.js',
  find: 'old code',
  replace: 'new code'
});
```

### 9.2 Shell Tools

```typescript
// 执行 Shell 命令
const result = await tools.shell.execute({
  command: 'npm install',
  cwd: '/app',
  timeout: 30000
});
```

### 9.3 Search Tools

```typescript
// 代码搜索
const results = await tools.search.code({
  query: 'function authenticate',
  path: 'src/',
  filePattern: '*.ts'
});
```

### 9.4 Web Tools

```typescript
// 网页访问
const content = await tools.web.fetch({
  url: 'https://github.com/vercel/vercel',
  selectors: '.repo-title'
});
```

---

## §10 与其他方案对比

### 10.1 vs Claude Code (Host)

| 维度 | Open Agents | Claude Code Host |
|------|-------------|------------------|
| 架构 | 云端原生 + 多 VM 分层 | Anthropic 官方托管的云端 CLI |
| 模型 | 灵活选择（支持多种 LLM） | 绑定 Claude |
| 部署 | Vercel 一键部署 | 无需部署，直接使用 CLI |
| 费用 | 按 Vercel 计费 | Anthropic 官方按 Token 计费 |
| 定制性 | 可 fork 修改源码 | 依赖官方更新 |

**注**：Claude Code Host 是 Anthropic 官方托管的云端服务，用户无需自建服务器，直接通过 `claude code` CLI 连接使用，按 Token 计费。

### 10.2 vs GenericAgent

| 维度 | Open Agents | GenericAgent |
|------|-------------|---------------|
| 架构 | 云端 + 分层 | 本地 + 分层 |
| 复杂度 | 高（完整系统） | 低（~3K 行） |
| 定制性 | 需要 fork 修改 | 直接修改源码 |
| 适用场景 | 团队协作 | 个人助手 |

---

## §11 定制指南

### 11.1 修改 Agent 行为

在 `packages/agent/src/` 中修改：

```typescript
// 修改工具
packages/agent/src/tools/

// 修改子代理
packages/agent/src/subagents/

// 修改技能
packages/agent/src/skills/
```

### 11.2 修改 Web UI

在 `apps/web/src/` 中修改：

```typescript
// 修改聊天界面
apps/web/src/components/ChatUI/

// 修改认证逻辑
apps/web/src/lib/auth/
```

### 11.3 修改 Sandbox 配置

在 `packages/sandbox/src/` 中修改：

```typescript
// 修改端口配置
packages/sandbox/src/ports.ts

// 修改快照策略
packages/sandbox/src/snapshot.ts
```

---

## §12 常见问题 FAQ

**Q1: 需要多少费用？**

A：主要是 Vercel 费用：
- Postgres（Neon）：免费层足够起步
- Vercel Sandbox：按使用计费
- 可选 Redis（Upstash）：免费层足够

**Q2: 支持哪些模型？**

A：支持 OpenAI-compatible API，可以配置：
- GPT-4 / GPT-3.5
- Claude（通过 Anthropic API）
- 本地模型（通过兼容接口）

**Q3: 如何添加新工具？**

A：在 `packages/agent/src/tools/` 添加新工具定义：

```typescript
// packages/agent/src/tools/my-tool.ts
export const myTool = {
  name: 'my_tool',
  description: 'My custom tool',
  execute: async (args) => { /* ... */ }
};
```

**Q4: Sandbox 休眠后如何恢复？**

A：Sandbox 在空闲后自动休眠，重新请求时会自动恢复，Agent 从上一个检查点继续。

**Q5: 如何实现高可用？**

A：Vercel 的 Durable Objects 提供高可用保证。多个实例可以同时运行，流量自动负载均衡。

---

## §13 相关资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/vercel-labs/open-agents |
| 官网 | https://open-agents.dev |
| Vercel 部署 | https://vercel.com/new/clone?project-name=open-agents |

---

**🦞 作者：钳岳星君 | 来源：GitHub vercel-labs/open-agents**