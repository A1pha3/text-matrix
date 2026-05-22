---
title: "Mirage：AI Agent 统一虚拟文件系统，让智能体用 Bash 操作一切后端"
date: "2026-05-22T11:10:00+08:00"
slug: "mirage-unified-virtual-filesystem-ai-agents"
description: "Mirage 是一个为 AI Agent 设计的统一虚拟文件系统（VFS），将 S3、Google Drive、Slack、Github、Gmail、MongoDB 等各种后端服务以文件系统语义挂载到同一个目录树下，让 AI 智能体通过熟悉的 bash 命令操作一切数据源，无需学习每个服务的专属 SDK。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Agent", "TypeScript", "Python", "VFS", "Agent工具"]
---

## Mirage 是什么

Mirage（[strukto-ai/mirage](https://github.com/strukto-ai/mirage)）是一个**统一虚拟文件系统（Unified Virtual Filesystem for AI Agents）**，其核心理念是：

> 各种后端服务（S3、Slack、Github、Gmail、Redis 等）以目录树的形式挂载到同一个根目录，AI 智能体通过熟悉的 bash 命令（cat、grep、ls、cp 等）来操作一切数据源。

| 基础信息 | |
|---|---|
| 仓库 | [strukto-ai/mirage](https://github.com/strukto-ai/mirage) |
| Stars | 约 2,500+（2026-05-22） |
| 主要语言 | TypeScript + Python |
| 许可证 | 详见 GitHub LICENSE |
| 官网 | [strukto.ai/mirage](https://www.strukto.ai/mirage) |
| 文档 | [docs.mirage.strukto.ai](https://docs.mirage.strukto.ai) |

## 核心问题：为什么需要统一虚拟文件系统

当前 AI 智能体需要对接大量外部服务：S3 存文件、Slack 沟通、GitHub 管代码、Gmail 收邮件。每种服务都有独立的 SDK 和 API，AI 需要分别学习才能使用。

Mirage 的思路是：**用统一语义掩盖复杂性**。一个熟悉 bash 的 LLM，不需要学习任何新词汇，就能操作所有已挂载的后端。

## 系统架构

```
┌─────────────────────────────────────────────┐
│     AI Agent / Application                  │
│  (OpenAI Agents / Vercel AI SDK / LangChain)│
└────────────────┬────────────────────────────┘
                 │
          Mirage Bash & VFS
                 │
          Dispatcher & Cache
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
  S3/R2      Slack/GitHub   GDrive
  (Storage)   (APIs)        (Docs)
```

**两层缓存机制**：
- **Index Cache**：目录列表和元数据缓存，减少 API 调用
- **File Cache**：文件内容缓存，避免重复下载

支持 RAM（默认，512MB）或 Redis（可跨进程共享）作为缓存后端。

## 支持的数据源

Python 和 TypeScript SDK 支持以下资源类型（部分）：

| 资源 | 说明 |
|---|---|
| RAM | 内存文件系统 |
| Disk | 本地磁盘 |
| Redis | 缓存与键值存储 |
| S3 / R2 / OCI / Supabase / GCS | 对象存储 |
| Gmail / GDrive / GDocs / GSheets / GSlides | Google 全家桶 |
| GitHub / Linear / Notion / Trello | 开发与协作工具 |
| Slack / Discord / Telegram / Email | 通信平台 |
| MongoDB | 数据库 |
| SSH | 远程服务器 |

所有资源挂载在同一目录树下，可相互pipe和组合。

## 快速上手

### Python 安装

```bash
uv add mirage-ai
```

### TypeScript 安装

```bash
npm install @struktoai/mirage-node      # Node.js 服务器和 CLI
npm install @struktoai/mirage-browser   # 浏览器 / Edge 运行时
npm install @struktoai/mirage-core      # 运行时无关的核心库
```

### 基本用法（Python）

```python
from mirage import Workspace
from mirage.resource.ram import RAMResource
from mirage.resource.s3 import S3Config, S3Resource
from mirage.resource.slack import SlackConfig, SlackResource

ws = Workspace({
    '/data':   RAMResource(),
    '/s3':     S3Resource(S3Config(bucket='my-bucket')),
    '/slack':  SlackResource(SlackConfig()),
})

# 文件操作跨后端：S3 → 本地
await ws.execute("cp /s3/report.csv /data/report.csv")

# 在 Slack 数据里搜索
await ws.execute("grep alert /slack/general/*.json | wc -l")

# 快照整个工作空间
ws.snapshot("demo.tar")
```

### 基本用法（TypeScript）

```ts
const ws = new Workspace({
  '/data':   new RAMResource(),
  '/s3':     new S3Resource({ bucket: 'my-bucket' }),
  '/slack':  new SlackResource({}),
  '/github': new GitHubResource({}),
})

await ws.execute('grep alert /slack/general/*.json | wc -l')
await ws.execute('cat /github/mirage/README.md')
await ws.execute('cp /s3/report.csv /data/local.csv')
```

## 与主流 Agent 框架集成

Mirage 支持无缝接入主流 Agent 应用框架：

### OpenAI Agents SDK（Python）

```python
from agents import Runner
from agents.sandbox import SandboxAgent, SandboxRunConfig
from mirage.agents.openai_agents import MirageSandboxClient

client = MirageSandboxClient(ws)
agent = SandboxAgent(
    name="Mirage Sandbox Agent",
    model="gpt-5.4-nano",
    instructions=ws.file_prompt,
)

result = await Runner.run(
    agent,
    "Summarize /s3/data/report.parquet into /report.txt.",
    run_config=RunConfig(sandbox=SandboxRunConfig(client=client)),
)
```

### Vercel AI SDK（TypeScript）

```ts
import { generateText } from 'ai'
import { openai } from '@ai-sdk/openai'
import { mirageTools } from '@struktoai/mirage-agents/vercel'

const { text } = await generateText({
  model: openai('gpt-5.4-nano'),
  system: buildSystemPrompt({ mountInfo: { '/': 'In-memory filesystem' } }),
  prompt: "Use readFile to read /docs/paper.pdf, then describe what's in it.",
  tools: mirageTools(ws),
})
```

还支持 LangChain、Pydantic AI、CAMEL、OpenHands、Mastra 等框架。

## 自定义命令扩展

可以为特定后端和文件类型注册专属命令：

```ts
// 注册跨所有挂载点可用的命令
ws.command('summarize', ...)

// 针对特定资源的特定文件类型覆盖默认行为
// 例如：在 /s3 上对 Parquet 文件执行 cat 时，自动渲染为 JSON
ws.command('cat', { resource: 's3', filetype: 'parquet' }, ...)
```

## 适用场景

- **多后端数据聚合 Agent**：需要从 S3、Slack、Github 同时拉取数据的智能体
- **编码 Agent**：如 Claude Code、Codex，通过 bash 访问一切挂载资源
- **数据分析 Agent**：跨数据源进行 grep、wc、jq 等 Unix 工具操作
- **知识管理 Agent**：打通 GDocs、GSheets、Gmail 的信息流

## 局限与注意事项

- FUSE 模式挂载依赖 macOS/Linux 平台支持
- Python ≥ 3.12、Node.js ≥ 20
- 目前处于积极开发阶段，API 可能发生变化
- 企业使用前请评估具体后端连接器的稳定性

## 总结

Mirage 的核心价值在于**将 AI Agent 与后端服务的交互方式统一到最熟悉的文件系统语义**。对于 AI 开发者而言，这意味着不再需要为每个服务编写独立的工具封装层；对于 LLM 而言，这意味着可以复用它最擅长的 bash 技能来操作一切数据。

项目同时提供 Python 和 TypeScript 双语言 SDK，并深度集成 OpenAI Agents SDK、Vercel AI SDK、LangChain 等主流框架，是当前 Agent 工具层值得关注的基础设施项目。