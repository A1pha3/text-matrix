---
title: "Sim Studio AI 完全指南：从零构建 AI Agent 工作流"
date: "2026-05-02T15:06:00+08:00"
slug: "simstudioai-sim-ai-agent-guide"
description: "Sim 是开源的 AI Agent 构建与编排平台，支持可视化工作流设计、Copilot 辅助、多模型集成和知识库检索。本文深入解析其架构设计、本地部署流程、核心功能实操及二次开发路径。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Agent", "Sim", "工作流编排", "Next.js", "RAG", "自动化", "Bun"]
---

# Sim Studio AI 完全指南：从零构建 AI Agent 工作流

## 学习目标

在阅读完本文后，你应该能够：

1. **理解 Sim 的核心定位**：掌握 Sim 作为"AI 劳动力的中央智能层"的设计理念，以及它与其他 AI Agent 框架的区别
2. **掌握系统架构**：理解 Turborepo 单体仓库结构、Next.js 主应用与 Bun + Socket.IO 实时协作服务的职责切分、包边界的严格约束
3. **配置与部署**：能够通过 Docker Compose、npx 一键启动或手动完整搭建三种方式部署 Sim，并正确配置环境变量与数据库
4. **构建第一个工作流**：能够在可视化画布上设计 Agent 链路，使用 Copilot 辅助生成节点，配置知识库（RAG）实现检索增强
5. **二次开发**：掌握添加新集成的完整流程（Tools → Block → Icon → Trigger），理解代码规范与质量门禁

## 目录

1. [学习目标](#学习目标)
2. [什么是 Sim？](#1-什么是-sim)
3. [系统架构解析](#2-系统架构解析)
4. [核心概念：Block、Tool、Trigger](#3-核心概念blocktooltrigger)
5. [安装与配置](#4-安装与配置)
6. [实战演示：构建一个 AI Agent 工作流](#5-实战演示构建一个-ai-agent-工作流)
7. [代码执行安全机制](#6-代码执行安全机制)
8. [二次开发指南](#7-二次开发指南)
9. [部署与运维](#8-部署与运维)
10. [常见问题与故障排查](#9-常见问题与故障排查)
11. [自测题](#自测题)
12. [练习](#练习)
13. [进阶路径](#进阶路径)
14. [资料口径说明](#资料口径说明)
15. [总结与进阶路径](#总结与进阶路径)

---

## 1. 什么是 Sim？

Sim 是 simstudioai 组织开源的 AI Agent 构建、部署与编排平台，定位为**AI 劳动力的中央智能层（central intelligence layer）**。其核心理念是将 AI Agent 的构建过程从代码层面下沉到可视化操作，让团队可以设计、运行和管理多 Agent 协作的工作流。

### 1.1 核心能力矩阵

| 能力维度 | 具体功能 |
|---|---|
| **工作流编排** | 可视化画布（ReactFlow）设计 Agent 链路，支持循环（Loop）、并行（Parallel）、条件分支等控制结构 |
| **多模型集成** | 支持 OpenAI、Anthropic、DeepSeek、Azure OpenAI/AI Foundry、Gemini、本地 Ollama、vLLM 等 |
| **工具生态** | 内置 1000+ 集成工具，支持自定义工具注册 |
| **知识库 / RAG** | 上传文档至向量数据库，Agent 运行时可基于私有知识作答 |
| **Copilot 辅助** | AI 驱动的自然语言节点生成、错误修复和迭代优化 |
| **实时协作** | Socket.IO 驱动的多人画布编辑 |
| **触发器** | 支持 Webhook、定时任务等触发方式 |
| **安全执行** | 代码隔离执行（E2B 远程沙箱 + isolated-vm 本地沙箱） |
| **自托管** | Docker Compose 一键部署，支持本地模型（Ollama/vLLM） |

### 1.2 技术标签与定位

从 GitHub Topic 可以看出其技术栈与目标场景：

```
agentic-workflow, ai-agents, anthropic, deepseek, gemini, low-code,
nextjs, no-code, openai, rag, react, typescript, automation, chatbot
```

Sim 并不是一个低代码玩具——它的架构设计、代码组织和技术选型都指向生产级使用场景。GitHub 已有 28k+ stars、3.5k+ forks，在开源社区有实际认可度。

---

## 2. 系统架构解析

理解 Sim 的架构是正确使用和二次开发的前提。

### 2.1 整体架构

Sim 采用 **Turborepo 单体仓库（monorepo）** 结构，主要分为两个应用和若干共享包：

```
simstudioai/sim/
├── apps/
│   ├── sim/                    # Next.js 主应用（UI + API + Workflow Editor）
│   │   ├── app/                # Next.js App Router（页面与 API 路由）
│   │   ├── blocks/             # Block 定义与注册表（可视化节点类型）
│   │   ├── components/         # 共享 UI 组件（emcn/、ui/）
│   │   ├── executor/           # 工作流执行引擎
│   │   ├── hooks/              # 共享 React Hooks（queries/、selectors/）
│   │   ├── lib/                # 通用工具函数
│   │   ├── providers/          # LLM Provider 集成
│   │   ├── stores/             # Zustand 全局状态管理
│   │   ├── tools/              # 工具定义与注册表
│   │   └── triggers/           # 触发器定义与注册表
│   └── realtime/               # Bun + Socket.IO 实时协作服务器
│       └── src/                # auth, config, database, handlers,
│                               # middleware, rooms, routes,
│                               # internal/webhook-cleanup.ts
│
└── packages/
    ├── audit/                  # 审计日志（recordAudit / AuditAction / AuditResourceType）
    ├── auth/                   # Better Auth 共享验证器（@sim/auth/verify）
    ├── db/                     # Drizzle ORM Schema + 客户端
    ├── logger/                 # 结构化日志（createLogger）
    ├── realtime-protocol/      # Socket 操作常量 + Zod Schema
    ├── security/               # 安全工具（safeCompare）
    ├── tsconfig/               # 共享 TypeScript 配置预设
    ├── utils/                  # 通用工具（generateId / generateShortId）
    ├── workflow-authz/         # 工作流权限验证（authorizeWorkflowByWorkspacePermission）
    ├── workflow-persistence/   # 工作流持久化（raw load/save + subflow helpers）
    └── workflow-types/         # 纯类型定义（BlockState / Loop / Parallel / ...）
```

### 2.2 两个服务如何协作

**Next.js 应用（port 3000）** 负责：页面渲染、API 路由、工作流编辑画布（ReactFlow）、Agent 执行引擎。

**Realtime 服务（port 3002）** 负责：多用户实时协作的 WebSocket 通道（Socket.IO），让多个开发者在同一画布上同步编辑。

两者共享同一个 PostgreSQL 数据库（通过 `@sim/db`），共享 `BETTER_AUTH_SECRET`，实现跨服务的会话一致性——这是 Better Auth 的"Shared Database Session"模式。

### 2.3 包边界的严格约束

架构设计中有两条铁律：

1. **单向依赖**：`apps/*` 可以依赖 `packages/*`，但 `packages/*` 绝对不能依赖 `apps/*`。
2. **realtime 服务隔离**：`apps/realtime` 有意不引入 Next.js、React、Block/Tool 注册表、Provider SDK 和执行器。CI 通过 `scripts/check-monorepo-boundaries.ts` 和 `scripts/check-realtime-prune-graph.ts` 强制校验这条约束。

这两条设计确保了代码的模块化边界清晰，realtime 服务不会因为前端依赖的膨胀而变得臃肿。

### 2.4 数据流概述

一个典型的工作流执行路径：

```
用户触发（Webhook / 手动运行 / 定时）
  → API Route (Next.js App Router)
    → Copilot（可选：AI 辅助生成节点）
      → Workflow Executor
        → LLM Provider（从 providers/ 选择）
          → Tools（从注册表执行外部 API 集成）
            → Knowledge Base（向量检索增强）
  → 结果写入数据库（通过 @sim/db）
  → WebSocket 推送状态变更（apps/realtime）
  → 后台任务（Trigger.dev 处理异步步骤）
```

---

## 3. 核心概念：Block、Tool、Trigger

理解这三个实体的关系是掌握 Sim 的关键。

### 3.1 Block（块）

Block 是可视化画布上的节点，代表工作流中的一个逻辑单元。每个 Block 定义了：

- **Inputs / Outputs**：输入输出端口，定义了与其他 Block 的连接关系
- **工具绑定**：Block 可以调用多个 Tool（工具），配置参数映射
- **渲染模式**：`basic`（简单参数填写）、`advanced`（完整配置）、`both`（两种模式并存）、`trigger`（触发器专用）
- **条件显示**：`condition` 字段控制某些参数在特定条件下才显示

Block 存于 `apps/sim/blocks/blocks/` 目录，每个 Block 对应一种服务或功能（如 Slack 发送消息、Gmail 读取、HTTP 请求等）。

### 3.2 Tool（工具）

Tool 是具体的 API 集成单元，存于 `apps/sim/tools/` 目录，结构如下：

```
tools/{service}/
├── index.ts      # 统一导出
├── types.ts      # 参数与响应的 TypeScript 类型
└── {action}.ts   # 具体操作实现（如 sendMessage.ts）
```

Tool 的核心结构如下（参考 AGENTS.md 中的规范）：

```typescript
export const serviceTool: ToolConfig<Params, Response> = {
  id: 'service_action',
  name: 'Service Action',
  description: '...',
  version: '1.0.0',
  oauth: { required: true, provider: 'service' },
  params: { /* JSON Schema 定义参数 */ },
  request: { url: '/api/tools/service/action', method: 'POST', ... },
  transformResponse: async (response) => { /* 数据转换 */ },
  outputs: { /* 输出结构定义 */ },
}
```

工具注册在 `tools/registry.ts` 中。Block 通过 `tools.access` 字段声明它需要哪些工具，`tools.config.tool` 在序列化阶段运行（变量尚未解析），`tools.config.params` 在执行阶段运行（变量已解析）。

### 3.3 Trigger（触发器）

Trigger 定义工作流何时被启动，例如：

- **Webhook**：外部系统通过 HTTP POST 触发
- **定时任务**：CRON 表达式驱动
- **事件驱动**：如邮箱收到新邮件

Trigger 存于 `apps/sim/triggers/` 目录，通过 `triggers/registry.ts` 注册。

### 3.4 三者关系图

```
Trigger（启动条件）→ Block（逻辑节点）→ Tool（具体操作）→ 结果
                  ↗                  ↗
              画布节点           API 调用
```

一个完整的集成需要：Tools（API 集成）→ Block（画布节点）→ Icon（UI 图标）→ (optional) Trigger（触发器）。文档中提供了详细的[添加集成检查清单](https://github.com/simstudioai/sim/blob/main/AGENTS.md)。

---

## 4. 安装与配置

### 4.1 快速云端使用

直接访问 **[sim.ai](https://sim.ai)**，注册后即可使用云端托管版本，无需任何安装。

### 4.2 NPM 一键启动（Docker）

前提条件：本地已安装并运行 Docker。

```bash
npx simstudio
# 默认访问 http://localhost:3000
# 可用 -p/--port 指定端口：npx simstudio -p 8080
# 可用 --no-pull 跳过拉取最新镜像
```

### 4.3 Docker Compose 生产部署

克隆仓库后使用生产配置：

```bash
git clone https://github.com/simstudioai/sim.git && cd sim
docker compose -f docker-compose.prod.yml up -d
# 访问 http://localhost:3000
```

生产配置包含三个服务：
- **simstudio**：主应用（内存限制 8GB）
- **realtime**：实时协作服务（内存限制 1GB）
- **db**：PostgreSQL + pgvector（向量数据库）

### 4.4 本地模型支持（Ollama / vLLM）

使用 Ollama 接入本地大模型：

```bash
docker compose -f docker-compose.ollama.yml --profile setup up -d
```

环境变量配置：

```bash
OLLAMA_URL=http://localhost:11434        # Ollama 服务地址
VLLM_BASE_URL=http://localhost:8000    # vLLM 服务地址（OpenAI 兼容）
VLLM_API_KEY=                           # 若 vLLM 需要认证
FIREWORKS_API_KEY=                      # Fireworks AI（可选）
```

### 4.5 手动完整搭建（开发模式）

适用于需要修改源码或深度定制的场景。

#### 依赖要求

| 依赖 | 版本要求 |
|---|---|
| Bun | 最新稳定版 |
| Node.js | v20+ |
| PostgreSQL | 12+ |
| pgvector | 必须安装（用于向量检索） |

#### 步骤 1：克隆并安装

```bash
git clone https://github.com/simstudioai/sim.git
cd sim
bun install
bun run prepare  # 设置 Git pre-commit hooks
```

#### 步骤 2：配置 PostgreSQL + pgvector

```bash
docker run --name simstudio-db \
  -e POSTGRES_PASSWORD=your_password \
  -e POSTGRES_DB=simstudio \
  -p 5432:5432 \
  -d pgvector/pgvector:pg17
```

或参考 [pgvector 官方安装指南](https://github.com/pgvector/pgvector#installation)。

#### 步骤 3：环境变量配置

```bash
cp apps/sim/.env.example apps/sim/.env

# 生成三个安全密钥（用于加密敏感信息）
perl -i -pe "s/your_encryption_key/$(openssl rand -hex 32)/" apps/sim/.env
perl -i -pe "s/your_internal_api_secret/$(openssl rand -hex 32)/" apps/sim/.env
perl -i -pe "s/your_api_encryption_key/$(openssl rand -hex 32)/" apps/sim/.env

# 设置数据库连接字符串
cp packages/db/.env.example packages/db/.env
# 编辑 packages/db/.env：DATABASE_URL="postgresql://postgres:your_password@localhost:5432/simstudio"
# 编辑 apps/sim/.env：DATABASE_URL="postgresql://postgres:your_password@localhost:5432/simstudio"
```

关键环境变量说明：

```bash
# 认证（必填）
BETTER_AUTH_SECRET=your_secret_key          # 使用 openssl rand -hex 32 生成
BETTER_AUTH_URL=http://localhost:3000

# 安全（必填）
ENCRYPTION_KEY=your_encryption_key           # 环境变量加密
INTERNAL_API_SECRET=your_internal_api_secret # 内部 API 路由加密
API_ENCRYPTION_KEY=your_api_encryption_key    # API 密钥加密

# 自托管 Copilot（可选）
# 访问 https://sim.ai → Settings → Copilot 生成 API Key
COPILOT_API_KEY=your_copilot_api_key

# 本地模型（可选）
OLLAMA_URL=http://localhost:11434
VLLM_BASE_URL=http://localhost:8000
VLLM_API_KEY=
```

#### 步骤 4：运行数据库迁移

```bash
cd packages/db && bun run db:migrate
```

#### 步骤 5：启动开发服务器

```bash
bun run dev:full  # 同时启动 Next.js 和 realtime Socket 服务器

# 或分别启动：
bun run dev       # Next.js 主应用（port 3000）
cd apps/sim && bun run dev:sockets  # realtime 服务（port 3002）
```

---

## 5. 实战演示：构建一个 AI Agent 工作流

### 5.1 创建第一个工作流

1. 访问 `http://localhost:3000`，创建工作区（Workspace）
2. 点击 **New Workflow**，进入可视化画布
3. 从左侧工具栏拖拽节点到画布上

### 5.2 核心节点类型

| 节点类型 | 用途 |
|---|---|
| **Agent** | 选择 LLM 模型，配置系统提示词（System Prompt） |
| **Tool** | 调用外部 API（邮件、Slack、数据库查询等） |
| **Knowledge** | 连接向量数据库，实现 RAG 检索 |
| **Condition** | if/else 条件分支 |
| **Loop** | 循环处理列表数据 |
| **Parallel** | 并行执行多个分支 |
| **Code** | 执行自定义代码（隔离沙箱） |
| **Webhook** | 发送 HTTP 请求 |

### 5.3 使用 Copilot 生成节点

在画布右侧打开 Copilot 面板，用自然语言描述需求：

```
"帮我创建一个 Agent，它能从知识库中检索相关信息并总结回答"
```

Copilot 会自动生成对应节点结构，并放置在画布上。

### 5.4 配置知识库（RAG）

1. 在 **Knowledge** 节点中上传文档（支持 PDF、Markdown、TXT 等格式）
2. 文档经过 embedding 后存入 pgvector 向量数据库
3. Agent 运行时，RAG 管线会自动检索与用户问题最相关的文档片段，注入到上下文中

### 5.5 运行与调试

- 点击画布右上角的 **Run** 按钮执行工作流
- 右侧面板显示实时执行日志：节点输入/输出、token 消耗、延迟
- 每个节点支持单步执行（Step-by-step debug）

---

## 6. 代码执行安全机制

Sim 处理两类代码执行场景：

### 6.1 远程沙箱（E2B）

用于需要网络访问或较长执行时间的代码。通过 E2B 平台在隔离容器中运行：

```typescript
// 远程执行，由 E2B 沙箱托管
const result = await e2b.execute({ code: '...', timeout: 60000 })
```

### 6.2 本地隔离（isolated-vm）

用于短时执行且不需要网络的代码。使用 V8 引擎的 native 隔离：

```typescript
// 本地执行，V8 隔离环境
import { isolate } from 'isolated-vm'
const result = await isolate.run('...')
```

两种机制确保用户定义的代码不会影响宿主服务器安全。

---

## 7. 二次开发指南

### 7.1 添加新集成：Tools → Block → Icon → Trigger

参考 AGENTS.md 中的完整流程，以下是关键步骤：

#### 第一步：创建 Tool

```bash
# 目录结构
apps/sim/tools/yourservice/
├── index.ts      # barrel export
├── types.ts      # Params / Response TypeScript 类型
└── sendMessage.ts  # 具体工具实现
```

#### 第二步：注册 Tool

在 `apps/sim/tools/registry.ts` 中添加（按字母顺序排列）。

#### 第三步：创建 Block

```bash
apps/sim/blocks/blocks/yourservice.ts
```

Block 配置示例：

```typescript
export const YourServiceBlock: BlockConfig = {
  type: 'yourservice',
  name: 'Your Service',
  description: '描述信息',
  category: 'tools',
  bgColor: '#hexcolor',
  icon: YourServiceIcon,
  subBlocks: [
    {
      id: 'operation', title: 'Operation',
      type: 'dropdown',
      options: [{ label: 'Send', value: 'send' }],
      required: true,
    },
    {
      id: 'message', title: 'Message',
      type: 'short-input',
      placeholder: 'Enter message...',
      required: true,
      dependsOn: ['operation'],
      condition: { field: 'operation', value: 'send' },
    },
  ],
  tools: {
    access: ['yourservice_send'],
    config: {
      tool: (p) => `yourservice_${p.operation}`,
      params: (p) => ({ /* 类型转换 */ }),
    },
  },
  inputs: { /* 输入端口 */ },
  outputs: { /* 输出端口 */ },
}
```

#### 第四步：添加 Icon

在 `apps/sim/components/icons.tsx` 中新增 SVG 图标组件。

#### 第五步：注册 Block

在 `apps/sim/blocks/registry.ts` 中注册（按字母顺序）。

### 7.2 包边界与导入规范

- **绝对导入优先**：使用 `@/` 别名，不使用相对路径
- **导入顺序**：React 核心 → 外部库 → `@/components/emcn` → `@/lib/utils` → `@/stores` → 特性模块 → CSS
- **类型导入**：`import type { X }` 明确声明仅导入类型

```typescript
// ✓ 正确
import { useWorkflowStore } from '@/stores/workflows/store'
import type { WorkflowConfig } from '@/types/workflow'

// ✗ 错误
import { useWorkflowStore } from '../../../stores/workflows/store'
```

### 7.3 状态管理约定

**全局状态** → Zustand（通过 `devtools` 中间件），**服务端数据** → TanStack Query（通过 React Query hooks），**组件本地状态** → useState。

TanStack Query 的 Query Key Factory 规范示例：

```typescript
export const workflowKeys = {
  all: ['workflow'] as const,
  lists: () => [...workflowKeys.all, 'list'] as const,
  list: (workspaceId?: string) => [...workflowKeys.lists(), workspaceId ?? ''] as const,
  details: () => [...workflowKeys.all, 'detail'] as const,
  detail: (id?: string) => [...workflowKeys.details(), id ?? ''] as const,
}
```

所有 `queryFn` 必须传递 `signal`（请求取消），所有 query 必须显式声明 `staleTime`。

### 7.4 代码规范与质量门禁

- **日志**：统一使用 `createLogger`（`@sim/logger`），禁止 `console.log`
- **ID 生成**：使用 `generateId()`（UUID v4）或 `generateShortId()`（紧凑格式），禁止使用 `crypto.randomUUID()`、`nanoid`、`uuid` 等
- **无 any**：使用 `unknown` + 类型守卫替代 `any`
- **测试**：使用 Vitest，测试文件命名 `feature.ts` → `feature.test.ts`

---

## 8. 部署与运维

### 8.1 生产环境部署（Docker Compose）

```bash
# 设置环境变量
export POSTGRES_PASSWORD=your_secure_password
export BETTER_AUTH_SECRET=$(openssl rand -hex 32)
export ENCRYPTION_KEY=$(openssl rand -hex 32)
export INTERNAL_API_SECRET=$(openssl rand -hex 32)

# 启动
docker compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker compose -f docker-compose.prod.yml ps

# 健康检查（主应用）
curl -fsS http://localhost:3000
# 健康检查（实时服务）
curl -fsS http://localhost:3002/health
```

### 8.2 内存需求

| 服务 | 最低内存 |
|---|---|
| simstudio（Next.js） | 8GB |
| realtime（Socket.IO） | 1GB |
| PostgreSQL + pgvector | 2GB+ |
| **总计** | **12GB+** |

### 8.3 GitOps 管理（自托管）

自托管实例支持通过 Admin API 进行工作流批量导入/导出：

```bash
curl -H "x-admin-key: your_admin_key" \
  https://your-instance/api/v1/admin/workspaces
```

需要设置 `ADMIN_API_KEY` 环境变量。

---

## 9. 常见问题与故障排查

### 端口冲突

如果 3000、3002 或 5432 端口已被占用：

```bash
# 检查占用进程
lsof -i :3000
lsof -i :3002
lsof -i :5432

# 或在启动时指定备用端口
npx simstudio -p 8080
```

### 数据库连接失败

```bash
# 验证 pgvector 是否正常
docker exec -it <container_id> psql -U postgres -d simstudio -c "SELECT 1;"

# 检查迁移是否运行
docker compose -f docker-compose.prod.yml ps migrations
```

### 本地模型（Ollama）无法连接

```bash
# 确认 Ollama 服务运行
curl http://localhost:11434

# 确认模型已下载
ollama list

# 若未安装模型
ollama pull llama3.2
```

### Copilot 在自托管实例上无法使用

自托管实例默认不包含 Sim 的云端 Copilot 服务。需在 [sim.ai](https://sim.ai) → Settings → Copilot 页面生成 API Key，然后在 `apps/sim/.env` 中设置：

```bash
COPILOT_API_KEY=sk_copilot_xxxx
```

---

## 自测题

以下问题用于检验你对 Sim 平台的理解程度：

1. **Sim 的核心定位是什么？它与低代码玩具的区别在哪里？**
   <details>
   <summary>点击查看答案</summary>
   Sim 定位为"AI 劳动力的中央智能层"，核心是可视化编排 AI Agent 工作流。它与低代码玩具的区别在于：架构设计、代码组织和技术选型都指向生产级使用场景；支持 E2B + isolated-vm 双层代码执行隔离；有完善的 AGENTS.md、类型安全的工具注册系统、清晰的新集成添加流程。
   </details>

2. **Sim 的架构中，Next.js 主应用与 Realtime 服务如何协作？**
   <details>
   <summary>点击查看答案</summary>
   Next.js 应用（port 3000）负责页面渲染、API 路由、工作流编辑画布、Agent 执行引擎。Realtime 服务（port 3002）负责多用户实时协作的 WebSocket 通道。两者共享同一个 PostgreSQL 数据库，共享 `BETTER_AUTH_SECRET`，实现跨服务的会话一致性。
   </details>

3. **Block、Tool、Trigger 三者的关系是什么？**
   <details>
   <summary>点击查看答案</summary>
   Trigger 定义工作流何时被启动（Webhook / 定时任务 / 事件驱动）。Block 是可视化画布上的节点，代表工作流中的一个逻辑单元，可以调用多个 Tool。Tool 是具体的 API 集成单元。完整集成需要：Tools（API 集成）→ Block（画布节点）→ Icon（UI 图标）→ (optional) Trigger（触发器）。
   </details>

4. **Sim 的代码执行安全机制是什么？**
   <details>
   <summary>点击查看答案</summary>
   Sim 处理两类代码执行场景：远程沙箱（E2B）——用于需要网络访问或较长执行时间的代码，通过 E2B 平台在隔离容器中运行；本地隔离（isolated-vm）——用于短时执行且不需要网络的代码，使用 V8 引擎的 native 隔离。两种机制确保用户定义的代码不会影响宿主服务器安全。
   </details>

5. **如何在 Sim 中添加一个新的集成（Tool + Block）？**
   <details>
   <summary>点击查看答案</summary>
   第一步：创建 Tool（在 `apps/sim/tools/yourservice/` 下创建 `index.ts`、`types.ts`、`action.ts`）。第二步：注册 Tool（在 `apps/sim/tools/registry.ts` 中添加）。第三步：创建 Block（在 `apps/sim/blocks/blocks/yourservice.ts`）。第四步：添加 Icon（在 `apps/sim/components/icons.tsx` 中新增 SVG 图标组件）。第五步：注册 Block（在 `apps/sim/blocks/registry.ts` 中注册）。
   </details>

## 练习

以下练习帮助你实践使用 Sim 平台：

### 练习 1：使用 Docker Compose 部署 Sim

**任务**：使用 Docker Compose 在生产环境中部署 Sim，并正确配置环境变量与数据库。

**步骤**：
1. 克隆仓库：`git clone https://github.com/simstudioai/sim.git && cd sim`
2. 设置环境变量：`export POSTGRES_PASSWORD=your_secure_password` 等
3. 启动：`docker compose -f docker-compose.prod.yml up -d`
4. 验证服务状态：`docker compose -f docker-compose.prod.yml ps`
5. 健康检查：访问 `http://localhost:3000` 和 `http://localhost:3002/health`

**参考答案**：部署成功后，应该能访问 Sim 的主界面（port 3000）。如果遇到数据库迁移问题，需要手动运行 `cd packages/db && bun run db:migrate`。

### 练习 2：构建一个简单的 AI Agent 工作流

**任务**：在 Sim 的可视化画布上构建一个简单的工作流：接收 Webhook → 调用 LLM 生成回复 → 发送邮件。

**步骤**：
1. 访问 `http://localhost:3000`，创建工作区（Workspace）
2. 点击 **New Workflow**，进入可视化画布
3. 从左侧工具栏拖拽节点：Webhook Trigger → Agent Block → Email Tool Block
4. 配置 Agent Block：选择 LLM 模型，配置系统提示词
5. 配置 Email Tool Block：配置 SMTP 设置
6. 运行与调试：点击 **Run** 按钮，查看执行日志

**参考答案**：构建成功后，向 Webhook 发送一个 HTTP POST 请求，应该能触发工作流执行，并最终发送邮件。右侧面板的执行日志会显示每个节点的输入/输出、token 消耗、延迟。

### 练习 3：添加一个新的集成（Tool + Block）

**任务**：为 Sim 添加一个新的集成——例如，集成一个自定义的 REST API 服务。

**步骤**：
1. 创建 Tool：在 `apps/sim/tools/customapi/` 下创建 `index.ts`、`types.ts`、`callEndpoint.ts`
2. 注册 Tool：在 `apps/sim/tools/registry.ts` 中添加
3. 创建 Block：在 `apps/sim/blocks/blocks/customapi.ts`
4. 添加 Icon：在 `apps/sim/components/icons.tsx` 中新增 SVG 图标组件
5. 注册 Block：在 `apps/sim/blocks/registry.ts` 中注册
6. 测试：重启开发服务器，在画布上应该能看到新的 Block

**参考答案**：添加成功后，在画布上拖拽新的 Block，配置参数，运行工作流，应该能成功调用自定义 REST API 服务。

## 进阶路径

如果你希望更深入地使用或定制 Sim 平台，可以按照以下路径进行：

1. **先用云端版本熟悉基本概念**：访问 [sim.ai](https://sim.ai) 注册，使用云端托管版本熟悉工作流设计的基本概念
2. **使用 `npx simstudio` 完成本地 Docker 部署**：理解数据流和架构，验证不同 LLM Provider 的集成方式
3. **阅读 AGENTS.md**：深入理解 Sim 的架构设计、代码规范、新集成添加流程
4. **尝试添加一个新的集成**：从简单的 REST API 开始，逐步过渡到复杂的 OAuth 集成
5. **研究 `@sim/workflow-executor` 和 `apps/sim/executor/` 的执行管线源码**：理解工作流是如何被调度、执行、错误处理
6. **探索 `@sim/db` 的 Drizzle Schema**：理解数据模型设计，如何扩展数据模型以支持自定义需求
7. **参与社区**：加入 Sim 的 Discord 或 GitHub Discussions，与其他开发者交流使用经验，贡献代码或文档

## 资料口径说明

本文档基于以下来源和假设：

1. **信息来源**：本文主要基于 Sim 的 GitHub 仓库（https://github.com/simstudioai/sim）的 README、AGENTS.md、架构文档和配置文档。所有数字（28k+ stars、3.5k+ forks）来自仓库公开信息，截至本文写作时。
2. **技术栈时效性**：文章描述了 Sim 的技术栈（Next.js、Bun、Socket.IO、PostgreSQL + pgvector 等），但这些技术栈的版本会随项目更新而变化。请以仓库最新版本为准。
3. **部署方式**：文章描述了多种部署方式（Docker Compose、npx 一键启动、手动完整搭建），但不同环境下的具体配置可能有所不同。生产环境部署前，建议参考官方文档并进行充分测试。
4. **本地模型支持**：文章提及使用 Ollama 或 vLLM 接入本地大模型，但具体兼容性、性能表现需要用户自行验证。
5. **代码执行安全**：文章说明了 E2B 和 isolated-vm 两种安全机制，但这些机制的有效性依赖于正确的配置和使用方式。在生产环境中，建议进行安全审计。
6. **局限性**：本文未深入评估 Sim 在大规模、高并发场景下的性能表现、资源消耗、以及与其他 AI Agent 框架的详细对比。这些评估需要结合实际使用经验和基准测试。

---

Sim 的设计目标并非做一个"又一个 AI Agent 框架"，而是一个**端到端的 AI Workforce 编排平台**。从它的架构可以看出几个值得留意的工程决策：

- **清晰的服务边界**：Next.js 主应用和 realtime 服务通过明确的包边界隔离，避免了单体应用的复杂度膨胀
- **可视化优先**：ReactFlow 驱动的画布让非工程师也能理解和修改工作流
- **安全第一**：E2B + isolated-vm 的双层代码执行隔离，让开放用户自定义代码成为可能而不引入安全风险
- **开发者友好**：完善的 AGENTS.md、类型安全的工具注册系统、清晰的新集成添加流程

**进阶学习路径建议**：

1. 先用云端版本 [sim.ai](https://sim.ai) 熟悉工作流设计的基本概念
2. 使用 `npx simstudio` 完成本地 Docker 部署，理解数据流和架构
3. 阅读 AGENTS.md，尝试添加一个新的集成（Tool + Block）
4. 研究 `@sim/workflow-executor` 和 `apps/sim/executor/` 的执行管线源码
5. 探索 `@sim/db` 的 Drizzle Schema，理解数据模型设计

官方文档：[https://docs.sim.ai](https://docs.sim.ai)