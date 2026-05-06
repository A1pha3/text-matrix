---
title: "Open-Antigravity：将Antigravity转为OpenAI/Anthropic兼容API"
slug: "open-antigravity-openai-anthropic-api-proxy-guide"
date: "2026-04-08T13:00:00+08:00"
lastmod: 2026-04-08T13:00:00+08:00
categories: ["技术笔记"]
tags: ["API代理", "TypeScript", "OpenAI兼容", "Anthropic兼容", "Antigravity", "gRPC-Web"]
description: "Open-Antigravity 是一个 TypeScript 编写的 API 代理工具，将 Antigravity 桌面应用暴露为 OpenAI 和 Anthropic 兼容的 API 服务。只需 base_url + key，即可让 Claude Code、Cursor、Continue、Python SDK 等任何兼容客户端调用 Antigravity。"
draft: false
---

# Open-Antigravity：将Antigravity转为OpenAI/Anthropic兼容API

## 1. 学习目标

通过本文你将掌握：

- 理解 Open-Antigravity 的设计理念和核心价值
- 熟练安装和配置 Open-Antigravity
- 使用 OpenAI 和 Anthropic 格式调用 API
- 集成到 Claude Code、Cursor、Continue 等客户端
- 理解底层架构和通信机制
- 掌握高级用法（workspace 选择、对话复用）

## 2. 项目概述

### 2.1 什么是 Open-Antigravity

Open-Antigravity 是一个开源的 API 代理工具：

> **"将 Antigravity 暴露为 OpenAI 和 Anthropic 兼容的 API 服务"**

**一句话解释**：通过 `base_url + key`，让任何兼容 OpenAI/Anthropic API 的客户端都能调用 Antigravity。

**核心价值**：

| 痛点 | 解决方案 |
|------|---------|
| Antigravity 没有标准 API | 转换为 OpenAI/Anthropic 兼容格式 |
| 只能通过桌面应用使用 | 任何 HTTP 客户端都能调用 |
| 生态封闭 | 无缝接入 Claude Code、Cursor 等工具 |

### 2.2 支持的客户端

Open-Antigravity 可让以下客户端使用 Antigravity：

| 客户端类型 | 示例工具 |
|-----------|---------|
| AI 编程工具 | Claude Code、Cursor、Continue、VS Code AI |
| Python SDK | OpenAI Python SDK、Anthropic Python SDK |
| 命令行工具 | cURL、HTTPie |
| 其他工具 | 任何支持 OpenAI/Anthropic API 的应用 |

### 2.3 技术栈

```
├── TypeScript 100%
├── tsx（开发/运行）
├── 零运行时依赖：纯 Node.js
│   ├── http 模块
│   ├── https 模块
│   └── crypto 模块
├── gRPC-Web（与 Antigravity 通信）
└── MIT License
```

## 3. 系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    客户端层                              │
│  Claude Code / Cursor / Continue / Python SDK / cURL    │
└─────────────────────────────────────────────────────────┘
                           │
                           │ HTTP (REST)
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Open-Antigravity (端口 4000)               │
│                                                         │
│  routes/openai.ts     →  /v1/chat/completions          │
│  routes/anthropic.ts  →  /v1/messages                  │
│  converter.ts        →  格式转换                        │
│  bridge/             →  与 Antigravity 通信            │
│    ├── discovery.ts  →  发现 language_server           │
│    ├── statedb.ts    →  读取 API key (SQLite)         │
│    └── grpc.ts       →  gRPC-Web 通信                 │
└─────────────────────────────────────────────────────────┘
                           │
                           │ gRPC-Web (HTTPS, 127.0.0.1)
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Antigravity language_server                 │
│              (本地运行的桌面应用)                       │
└─────────────────────────────────────────────────────────┘
```

### 3.2 核心组件

**routes/openai.ts** — OpenAI 兼容接口：

```typescript
// 处理 OpenAI 格式的请求
POST /v1/chat/completions
{
  "model": "claude-sonnet-4-20250514",
  "messages": [{"role": "user", "content": "Hello!"}]
}
```

**routes/anthropic.ts** — Anthropic 兼容接口：

```typescript
// 处理 Anthropic 格式的请求
POST /v1/messages
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 1024,
  "messages": [{"role": "user", "content": "Hello!"}]
}
```

**converter.ts** — 格式转换：

```typescript
// OpenAI → Antigravity 格式
function toAntigravityRequest(openaiReq: OpenAIRequest): AntigravityRequest {
  return {
    workspace: openaiReq.workspace,
    model: modelMapper(openaiReq.model),
    messages: convertMessages(openaiReq.messages)
  }
}
```

**bridge/discovery.ts** — 服务发现：

```typescript
// 使用 ps + lsof 发现本地运行的 Antigravity
async function discoverLanguageServer(): Promise<string> {
  const pid = await findProcess('Antigravity')
  const port = await findPort(pid)
  return `http://127.0.0.1:${port}`
}
```

### 3.3 通信流程

**请求流程**：

```
1. 客户端发送 HTTP 请求到 :4000
   ↓
2. Open-Antigravity 解析请求格式（OpenAI 或 Anthropic）
   ↓
3. 转换为 Antigravity 内部格式
   ↓
4. 通过 gRPC-Web 转发给 Antigravity language_server
   ↓
5. Antigravity 处理请求，返回结果
   ↓
6. Open-Antigravity 转换响应格式
   ↓
7. 返回给客户端
```

## 4. 安装与配置

### 4.1 环境要求

- Node.js 18+
- Antigravity 桌面应用（已安装并运行）
- 至少打开一个 workspace

### 4.2 安装步骤

**前提条件**：

确保 Antigravity 桌面应用已经在运行，并且已经打开至少一个 workspace。

**安装 Open-Antigravity**：

```bash
# 克隆仓库
git clone https://github.com/jackwener/open-antigravity.git
cd open-antigravity

# 安装依赖
npm install

# 启动服务
npm run dev
```

**验证安装**：

```bash
# 健康检查
curl http://localhost:4000/health

# 查看可用模型
curl http://localhost:4000/v1/models
```

### 4.3 配置

**环境变量**：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | 4000 | 服务端口 |
| `HOST` | 0.0.0.0 | 监听地址 |

**创建 .env 文件**：

```bash
# .env
PORT=4000
HOST=0.0.0.0
```

## 5. 使用指南

### 5.1 OpenAI 格式

**基础调用**：

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer any-key" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

**流式输出**：

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer any-key" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "stream": true,
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### 5.2 Anthropic 格式

**基础调用**：

```bash
curl http://localhost:4000/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: any-key" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### 5.3 Python SDK

**OpenAI Python SDK**：

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000/v1",
    api_key="any"
)

resp = client.chat.completions.create(
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(resp.choices[0].message.content)
```

**Anthropic Python SDK**：

```python
import anthropic

client = anthropic.Anthropic(
    base_url="http://localhost:4000",
    api_key="any"
)

msg = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello!"}]
)

print(msg.content[0].text)
```

## 6. 高级用法

### 6.1 指定 Workspace

通过 `x-workspace` Header 指定使用的 workspace：

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "x-workspace: file:///Users/you/project" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "messages": [{"role": "user", "content": "Which project am I in?"}]
  }'
```

**说明**：
- 不传 `x-workspace` 则使用第一个可用的 workspace
- 传入 `file:///` 开头的路径指定具体项目目录

### 6.2 复用对话

通过 `x-conversation-id` Header 复用已有对话：

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "x-conversation-id: conv_xxx123" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "messages": [{"role": "user", "content": "Continue from where we left off"}]
  }'
```

**使用场景**：
- 在多个请求间保持上下文连续性
- 避免每次请求都创建新对话

### 6.3 集成到 Claude Code

在 Claude Code 中配置 Open-Antigravity 作为 API 提供商：

```bash
# 设置环境变量
export ANTHROPIC_API_BASE="http://localhost:4000"
export ANTHROPIC_API_KEY="any"

# 或在项目根目录创建 .env
echo 'ANTHROPIC_API_BASE=http://localhost:4000' >> .env
echo 'ANTHROPIC_API_KEY=any' >> .env

# 启动 Claude Code
claude
```

### 6.4 集成到 Cursor

在 Cursor 设置中配置自定义 API：

```json
{
  "api": {
    "openai": {
      "baseURL": "http://localhost:4000/v1",
      "apiKey": "any"
    }
  }
}
```

## 7. 可用模型

### 7.1 模型映射表

| 外部名称 | Antigravity 内部 ID | 显示名称 |
|---------|---------------------|---------|
| `gemini-3.1-pro` | MODEL_PLACEHOLDER_M37 | Gemini 3.1 Pro (High) |
| `gemini-3.1-pro-low` | MODEL_PLACEHOLDER_M36 | Gemini 3.1 Pro (Low) |
| `gemini-3-flash` | MODEL_PLACEHOLDER_M47 | Gemini 3 Flash |
| `claude-sonnet-4-20250514` | MODEL_PLACEHOLDER_M35 | Claude Sonnet 4.6 (Thinking) |
| `claude-opus-4-20250514` | MODEL_PLACEHOLDER_M26 | Claude Opus 4.6 (Thinking) |
| `gpt-oss-120b` | MODEL_OPENAI_GPT_OSS_120B_MEDIUM | GPT-OSS 120B |

**注意**：也可以直接使用内部 ID（如 `MODEL_PLACEHOLDER_M35`）。

## 8. API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/chat/completions` | OpenAI Chat Completions |
| POST | `/v1/messages` | Anthropic Messages |
| GET | `/v1/models` | 可用模型列表 |
| GET | `/health` | 健康检查 |

## 9. 技术原理

### 9.1 为什么需要 API 代理

Antigravity 原本只支持桌面应用交互，缺乏标准 API：

```
传统方式：
用户 → Antigravity 桌面应用 →（用户操作）

问题：
- 无法编程调用
- 无法集成到其他工具
- 无法自动化
```

Open-Antigravity 的解决方案：

```
用户 → Open-Antigravity → Antigravity language_server
      (HTTP)          (gRPC-Web)
```

### 9.2 gRPC-Web 通信机制

Open-Antigravity 使用 gRPC-Web 与 Antigravity 通信：

```typescript
// bridge/grpc.ts
import { grpc } from 'bandage'

// 创建 gRPC-Web 客户端
const client = grpc.createClient({
  service: 'antigravity.LanguageServer',
  host: 'https://127.0.0.1:8080'  // Antigravity 本地端口
})

// 发送请求
const response = await client.invoke('Generate', {
  workspace: '/path/to/workspace',
  prompt: 'Hello!'
})
```

### 9.3 服务发现机制

bridge/discovery.ts 使用系统工具发现 Antigravity：

```typescript
// 使用 ps 查找进程
const pid = await findProcess('Antigravity')

// 使用 lsof 查找端口
const port = await findPort(pid)

// 组合地址
const address = `https://127.0.0.1:${port}`
```

## 10. 最佳实践

### 10.1 开发环境配置

```bash
# 启动开发模式（热重载）
npm run dev

# 后台运行
nohup npm run dev > open-antigravity.log 2>&1 &

# 查看日志
tail -f open-antigravity.log
```

### 10.2 生产环境配置

```bash
# 使用 PM2 管理进程
npm install -g pm2
pm2 start npm --name "open-antigravity" -- run dev

# 开机自启
pm2 save
pm2 startup
```

### 10.3 安全考虑

| 风险 | 缓解措施 |
|------|---------|
| 本地服务暴露 | 默认只监听 127.0.0.1 |
| API Key 验证 | 任何 key 都可以（本地服务） |
| HTTPS 支持 | gRPC-Web 使用 HTTPS 连接到 Antigravity |

**重要**：服务默认只监听本地（127.0.0.1），不会暴露到外网。

## 11. 常见问题

**Q: 服务启动失败，提示端口被占用？**

```bash
# 查找占用端口的进程
lsof -i :4000

# 杀掉占用进程或修改端口
PORT=4001 npm run dev
```

**Q: 返回 "workspace not found"？**

```bash
# 确保 Antigravity 桌面应用正在运行
# 确保已经打开至少一个 workspace
# 使用 x-workspace 指定具体路径
```

**Q: 如何查看调试日志？**

```bash
# 启动时显示详细日志
DEBUG=* npm run dev

# 或者查看控制台输出
```

**Q: 支持流式输出吗？**

A: 支持。在请求中添加 `"stream": true` 即可。

**Q: 可以同时使用多个客户端吗？**

A: 可以。Open-Antigravity 支持并发请求，每个请求相互独立。

## 12. 与类似项目对比

| 项目 | 定位 | 协议 | 特点 |
|------|------|------|------|
| Open-Antigravity | Antigravity → OpenAI/Anthropic | HTTP + gRPC-Web | 零依赖 |
| @openai/agents-sdk | OpenAI 官方 | HTTP | 云端 |
| Anthropic SDK | Anthropic 官方 | HTTP | 云端 |

**Open-Antigravity 优势**：
- 零运行时依赖（纯 Node.js）
- 本地服务，不需要云端
- 支持 Antigravity 独有功能

## 13. 总结

Open-Antigravity 是一个桥梁工具，连接了 Antigravity 桌面应用和标准 API 生态：

| 特性 | 说明 |
|------|------|
| 协议转换 | OpenAI ↔ Anthropic ↔ Antigravity |
| 零依赖 | 纯 Node.js 标准库 |
| 本地优先 | 不需要云端服务 |
| 生态兼容 | Claude Code、Cursor、SDK 等 |

**适用场景**：
- 想要编程调用 Antigravity
- 想要在 Claude Code 等工具中使用 Antigravity
- 想要自动化 Antigravity 工作流

**不适用场景**：
- 没有安装 Antigravity 桌面应用
- 需要云端部署（当前版本只支持本地）

---

*🦞 每日08:00自动更新*
