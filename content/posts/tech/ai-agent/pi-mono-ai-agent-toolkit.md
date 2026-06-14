---
title: "Pi Monorepo：开源 AI Agent 工具包专家级技术文档"
date: "2026-03-30T13:03:00+08:00"
slug: pi-mono-ai-agent-toolkit
aliases:
  - /posts/tech/pi-mono-ai-agent-toolkit/
categories: ["技术笔记"]
tags: ["AI Agent", "LLM", "Monorepo", "TypeScript", "vLLM"]
description: "Pi Monorepo 是开源 AI Agent 工具包，本文档从入门到精通涵盖原理分析、架构设计、七大核心包详解、使用说明和开发扩展。"
---

# Pi Monorepo：开源 AI Agent 工具包专家级技术文档

> 预计阅读时间：35分钟 | 难度：⭐⭐⭐⭐

---

> **目标读者**：想要掌握 Pi Monorepo 的开发者、AI 应用工程师和技术决策者

---

## 1. 学习目标

完成本文档后，你将掌握：

- ✅ 理解 Pi Monorepo 作为 AI Agent 工具包的核心定位与适用场景
- ✅ 掌握 Pi 的七大核心包架构与模块职责
- ✅ 能够独立完成本地开发环境搭建和包管理
- ✅ 学会使用 Unified LLM API 进行多模型切换
- ✅ 掌握 Agent Runtime 的工具调用与状态管理机制
- ✅ 了解 Pi 与 LangChain、AutoGPT 等竞品的核心差异

---

## 2. 原理分析

### 2.1 什么是 Pi Monorepo？

**Pi Monorepo** 是一个开源的 **AI Agent 工具包**，由 badlogic 开发维护。它提供了构建 AI Agent 和管理 LLM 部署所需的全部核心组件。

> 💡 **类比理解**：把 Pi 想象成一个「AI Agent 的乐高积木」——每个包都是一块精心设计的积木，你可以根据需要组合使用，也可以单独使用某一块。从底层的统一 LLM API，到上层的 Terminal UI，层层解耦，灵活组合。

### 2.2 Pi 的核心定位

| 维度 | Pi Monorepo | LangChain | AutoGPT | CrewAI |
|------|-------------|-----------|----------|---------|
| **架构** | Monorepo | 单体 | 单体 | 单体 |
| **核心场景** | 全栈 Agent 工具包 | LLM 应用框架 | 自主 Agent | 多 Agent 协作 |
| **LLM 支持** | 统一 API，多provider | 多 provider | 多 model | 多 model |
| **Agent Runtime** | ✅ 原生支持 | ✅ 支持 | ✅ 原生 | ✅ 支持 |
| **TUI 界面** | ✅ 原生 | ❌ | ❌ | ❌ |
| **Web UI** | ✅ 原生 | ❌ | ❌ | ❌ |
| **Slack Bot** | ✅ 原生 | ❌ | ❌ | ❌ |
| **vLLM 部署** | ✅ 原生 | ❌ | ❌ | ❌ |
| **许可证** | MIT | MIT | MIT | MIT |

### 2.3 为什么选择 Pi？

**Pi 解决的核心问题**：

1. **多模型切换难题**：开发者常常需要在不同 LLM Provider 之间切换，Pi 提供统一的 API 接口，代码无需大改即可切换模型
2. **Agent 开发门槛高**：Pi 提供了开箱即用的 Agent Runtime，无需从零实现工具调用和状态管理
3. **部署复杂**：Pi 提供了 vLLM Pods CLI，一键部署 GPU 集群上的 LLM 服务
4. **界面开发工作量大**：Pi 同时提供 TUI 和 Web UI 组件库，快速构建 AI 交互界面

**Pi 的设计原则**：

> "Tools for building AI agents and managing LLM deployments" — 专注于 AI Agent 构建和 LLM 部署的工具集

Pi 坚持模块化设计，每个包都可以独立使用，也可以组合使用。代码完全开源，MIT 许可证，无商业限制。

### 2.4 Pi 的技术边界

| 能力 | Pi 支持 | Pi 不支持 |
|------|---------|-----------|
| 多 LLM Provider | ✅ OpenAI/Anthropic/Google 等统一封装 | 自定义 provider 需实现接口 |
| Agent Runtime | ✅ 工具调用/状态管理/记忆 | 无内置知识库（需集成） |
| TUI 界面 | ✅ 差分渲染 Terminal UI | 无内置编辑器 |
| Web UI | ✅ AI Chat 组件库 | 完整 SaaS 平台 |
| Slack 集成 | ✅ Slack Bot 消息转发 | Slack OAuth 二次开发 |
| vLLM 部署 | ✅ GPU Pods 管理 | 自动扩缩容 |
| 本地模型 | ✅ Ollama 集成 | 自行托管模型训练 |

---

## 3. 架构分析

### 3.1 整体架构

Pi Monorepo 采用经典的 **分层架构**：

```mermaid
graph TD
    subgraph User["用户层"]
        UserCLI[CLI 用户]
        UserSlack[Slack 用户]
        UserWeb[Web 用户]
    end

    subgraph Interface["接口层"]
        CodingAgent[pi-coding-agent<br/>交互式编码 Agent CLI]
        SlackBot[pi-mom<br/>Slack Bot]
        WebUI[pi-web-ui<br/>Web UI 组件]
        TUI[pi-tui<br/>Terminal UI]
    end

    subgraph Runtime["运行时层"]
        AgentCore[pi-agent-core<br/>Agent 核心运行时]
        ToolCalling[工具调用系统]
        StateManagement[状态管理]
        Memory[记忆系统]
    end

    subgraph API["API 层"]
        UnifiedAPI[pi-ai<br/>统一 LLM API]
        OpenAIProvider[OpenAI Provider]
        AnthropicProvider[Anthropic Provider]
        GoogleProvider[Google Provider]
        OllamaProvider[Ollama Provider]
    end

    subgraph Infra["基础设施层"]
        PodsCLI[pi-pods<br/>vLLM Pods 管理]
        vLLM[vLLM 集群]
        GPU[GPU Pods]
    end

    UserCLI --> CodingAgent
    UserSlack --> SlackBot
    UserWeb --> WebUI

    CodingAgent --> AgentCore
    SlackBot --> AgentCore
    TUI --> AgentCore
    WebUI --> AgentCore

    AgentCore --> UnifiedAPI
    AgentCore --> ToolCalling
    AgentCore --> StateManagement
    AgentCore --> Memory

    UnifiedAPI --> OpenAIProvider
    UnifiedAPI --> AnthropicProvider
    UnifiedAPI --> GoogleProvider
    UnifiedAPI --> OllamaProvider

    PodsCLI --> vLLM
    vLLM --> GPU
```

### 3.2 七大核心包详解

| 包名 | 职责 | 独立使用 | 依赖关系 |
|------|------|---------|---------|
| **pi-ai** | 统一 LLM API | ✅ | 无 |
| **pi-agent-core** | Agent 运行时核心 | ✅ | pi-ai |
| **pi-coding-agent** | 交互式编码 Agent CLI | ❌ | pi-agent-core + pi-tui |
| **pi-mom** | Slack Bot | ❌ | pi-agent-core |
| **pi-tui** | Terminal UI 库 | ✅ | 无 |
| **pi-web-ui** | Web UI 组件 | ✅ | 无 |
| **pi-pods** | vLLM Pods 管理 CLI | ✅ | 无 |

### 3.3 核心技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| **语言** | TypeScript 95.9% | 类型安全，IDE 支持完善 |
| **运行时** | Node.js / Bun | 支持最新 ES 模块 |
| **包管理** | npm workspaces | Monorepo 原生支持 |
| **类型检查** | TypeScript strict mode | 全面类型覆盖 |
| **代码质量** | Biome | Lint + Format + Type check |
| **测试** | Vitest | 快速单元测试 |

### 3.4 目录结构

```
pi-mono/
├── .github/              # GitHub Actions CI/CD
├── .husky/               # Git hooks
├── .pi/                  # Pi 配置文件
│   └── coding-agent/     # Agent 相关配置
├── packages/             # 核心包源码
│   ├── ai/               # Unified LLM API
│   │   └── src/
│   │       ├── providers/    # 各 Provider 实现
│   │       ├── api.ts        # 统一接口
│   │       └── types.ts      # 类型定义
│   ├── agent/            # Agent Runtime
│   │   └── src/
│   │       ├── agent.ts      # Agent 核心
│   │       ├── tools/        # 工具系统
│   │       ├── memory/       # 记忆系统
│   │       └── state.ts      # 状态管理
│   ├── coding-agent/     # 编码 Agent CLI
│   ├── mom/              # Slack Bot
│   ├── tui/              # Terminal UI
│   ├── web-ui/           # Web UI 组件
│   └── pods/             # vLLM Pods CLI
├── scripts/               # 开发脚本
├── docs/                  # 项目文档
├── AGENTS.md             # Agent 开发规范
├── CONTRIBUTING.md       # 贡献指南
├── biome.json            # Biome 配置
├── package.json          # Workspace 根配置
└── tsconfig.base.json   # TypeScript 基础配置
```

### 3.5 Unified LLM API 架构

Pi 的统一 LLM API 是整个工具包的核心：

```mermaid
sequenceDiagram
    participant User as 用户代码
    participant API as pi-ai
    participant Provider as Provider
    participant LLM as OpenAI/Anthropic/Google

    User->>API: chat({ model: "gpt-4", messages })
    API->>API: selectProvider("gpt-4")
    API->>Provider: generate()
    Provider->>LLM: HTTP Request
    LLM-->>Provider: Response
    Provider-->>API: Standardized Response
    API-->>User: { content, usage, model }

    Note over User,LLM: 同理支持 claude-3, gemini-pro 等
```

**Provider 映射表**：

| 模型 | Provider | 状态 |
|------|----------|------|
| GPT-4 / GPT-3.5 | OpenAI | ✅ 稳定 |
| Claude 3 / 2 | Anthropic | ✅ 稳定 |
| Gemini Pro / Flash | Google | ✅ 稳定 |
| Llama / Mistral | Ollama | ✅ 稳定 |
| 本地模型 | Ollama | ✅ 稳定 |
| vLLM 部署模型 | Custom | ✅ 稳定 |

---

## 4. 功能详解

### 4.1 pi-ai：统一 LLM API

**pi-ai** 是 Pi 的核心，提供了统一的 LLM 调用接口：

```typescript
import { createLLM } from '@mariozechner/pi-ai';

// 创建 OpenAI 模型
const openai = createLLM({
  provider: 'openai',
  model: 'gpt-4',
  apiKey: process.env.OPENAI_API_KEY
});

// 创建 Anthropic 模型
const anthropic = createLLM({
  provider: 'anthropic',
  model: 'claude-3-opus-20240229',
  apiKey: process.env.ANTHROPIC_API_KEY
});

// 创建 Ollama 本地模型
const ollama = createLLM({
  provider: 'ollama',
  model: 'llama2',
  baseUrl: 'http://localhost:11434'
});

// 统一调用接口
const response = await openai.chat({
  messages: [
    { role: 'system', content: 'You are a helpful assistant.' },
    { role: 'user', content: 'Hello!' }
  ]
});

console.log(response.content);  // 模型输出
console.log(response.usage);  // Token 使用量
```

### 4.2 pi-agent-core：Agent 运行时

**pi-agent-core** 提供了 Agent 的核心运行时：

```typescript
import { Agent } from '@mariozechner/pi-agent-core';
import { createLLM } from '@mariozechner/pi-ai';
import { ReadFileTool, WriteFileTool, BashTool } from '@mariozechner/pi-agent-core/tools';

// 创建 LLM
const llm = createLLM({ provider: 'openai', model: 'gpt-4' });

// 创建 Agent
const agent = new Agent({
  llm,
  tools: [
    new ReadFileTool(),
    new WriteFileTool(),
    new BashTool()
  ],
  systemPrompt: '你是一个专业的程序员助手。'
});

// 运行对话
const response = await agent.run({
  messages: [
    { role: 'user', content: '帮我创建一个 Hello World 的 Python 文件。' }
  ]
});

console.log(response.content);
```

**内置工具系统**：

| 工具 | 说明 | 示例 |
|------|------|------|
| **ReadFileTool** | 读取文件 | `readFile({ path: './src/main.py' })` |
| **WriteFileTool** | 写入文件 | `writeFile({ path, content })` |
| **BashTool** | 执行命令 | `bash({ command: 'npm install' })` |
| **WebSearchTool** | 网页搜索 | `search({ query: '最新 AI 新闻' })` |
| **GitTool** | Git 操作 | `git({ action: 'commit', message: 'fix bug' })` |

### 4.3 pi-coding-agent：交互式编码 Agent CLI

**pi-coding-agent** 是 Pi 提供的交互式编码 Agent：

```bash
# 安装
npm install -g @mariozechner/pi-coding-agent

# 运行（从源码）
./pi-test.sh

# 或直接运行编译后的 CLI
pi
```

**主要功能**：

- 交互式 Terminal UI，实时显示 Agent 思考过程
- 多轮对话支持，Agent 记住上下文
- 内置代码编辑工具（读取/写入/执行命令）
- Git 集成，自动 commit
- 会话历史保存

### 4.4 pi-mom：Slack Bot

**pi-mom** 是 Slack Bot，将 Coding Agent 集成到 Slack：

```bash
# 安装
npm install -g @mariozechner/pi-mom

# 配置环境变量
export SLACK_BOT_TOKEN=xoxb-xxx
export SLACK_SIGNING_SECRET=xxx
export PI_CODING_AGENT_URL=http://localhost:3000

# 运行
pi-mom
```

**使用方式**：

1. 在 Slack 中 @pi-mom 调用 Agent
2. Agent 自动处理请求并回复
3. 支持代码片段高亮

### 4.5 pi-tui：Terminal UI 库

**pi-tui** 提供了差分渲染的 Terminal UI 组件：

```typescript
import { render, Box, Text } from '@mariozechner/pi-tui';

// 简单示例
render((
  <Box width={80} height={24}>
    <Text color="green">Hello, Pi!</Text>
  </Box>
));
```

**核心特性**：

- 声明式组件 API
- 差分渲染（只更新变化的 DOM）
- 键盘事件处理
- ANSI 颜色支持
- 自动检测 Terminal 尺寸

### 4.6 pi-web-ui：Web UI 组件

**pi-web-ui** 提供了 AI Chat 的 Web 组件：

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="pi-web-ui.css">
</head>
<body>
  <ai-chat id="my-chat"></ai-chat>
  <script type="module">
    import 'pi-web-ui';
    
    const chat = document.getElementById('my-chat');
    chat.config = {
      apiEndpoint: 'http://localhost:3000/chat',
      theme: 'dark'
    };
  </script>
</body>
</html>
```

### 4.7 pi-pods：vLLM Pods 管理

**pi-pods** 是管理 GPU Pods 上 vLLM 部署的 CLI：

```bash
# 安装
npm install -g @mariozechner/pi-pods

# 初始化集群
pi-pods init --cluster my-cluster --gpu-type A100

# 部署模型
pi-pods deploy --model llama2 --replicas 2

# 扩缩容
pi-pods scale --model llama2 --replicas 4

# 查看状态
pi-pods status

# 删除部署
pi-pods delete --model llama2
```

---

## 5. 使用说明

### 5.1 环境准备

**前置要求**：

| 依赖 | 版本要求 | 说明 |
|------|---------|------|
| Node.js | ≥18.x | 推荐 LTS 版本 |
| npm | ≥9.x | 或使用 Bun |
| Git | 任意版本 | 代码版本控制 |
| Ollama | ≥0.1.x | 本地模型（可选） |

### 5.2 快速开始

**方式一：从源码运行（推荐）**：

```bash
# 1. 克隆代码仓库
git clone https://github.com/badlogic/pi-mono.git
cd pi-mono

# 2. 安装所有依赖
npm install

# 3. 构建所有包
npm run build

# 4. 类型检查、格式化和 Lint
npm run check

# 5. 运行测试
./test.sh

# 6. 运行 Coding Agent（交互模式）
./pi-test.sh
```

**方式二：使用已发布的 npm 包**：

```bash
# 安装核心包
npm install @mariozechner/pi-ai
npm install @mariozechner/pi-agent-core
npm install @mariozechner/pi-tui
```

**方式三：使用 Docker**：

```bash
# 克隆代码仓库
git clone https://github.com/badlogic/pi-mono.git
cd pi-mono

# 运行测试环境
docker compose -f docker-compose.dev.yml up
```

### 5.3 配置文件

Pi 在项目根目录使用 `.pi/` 目录存储配置：

```
.pi/
└── coding-agent/
    ├── config.json      # Agent 配置
    ├── prompts/         # 自定义提示词
    └── memory/          # 记忆存储
```

**config.json 示例**：

```json
{
  "model": "gpt-4",
  "temperature": 0.7,
  "maxTokens": 4096,
  "tools": [
    "readFile",
    "writeFile", 
    "bash",
    "git"
  ],
  "systemPrompt": "你是一个专业的程序员助手。"
}
```

### 5.4 开发工作流

```bash
# 1. 创建新分支
git checkout -b feature/my-feature

# 2. 开发代码...

# 3. 运行检查
npm run check

# 4. 运行测试
./test.sh

# 5. 提交（自动触发 Lint）
git add .
git commit -m "feat: add new feature"

# 6. 推送并创建 PR
git push origin feature/my-feature
```

### 5.5 环境变量配置

```bash
# .env 文件
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
GOOGLE_API_KEY=xxx

# Ollama（本地模型）
OLLAMA_BASE_URL=http://localhost:11434

# Slack Bot
SLACK_BOT_TOKEN=xoxb-xxx
SLACK_SIGNING_SECRET=xxx

# vLLM 集群
VLLM_API_BASE=http://gpu-pod:8000
```

---

## 6. 开发扩展

### 6.1 自定义 Provider

扩展 Pi 支持新的 LLM Provider：

```typescript
// packages/ai/src/providers/my-provider.ts
import { createProvider, type ProviderConfig } from '../types';

export const myProvider = createProvider({
  name: 'my-provider',
  
  async generate(config: ProviderConfig) {
    // 1. 构建请求
    const response = await fetch('https://api.my-provider.com/v1/chat', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${config.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: config.model,
        messages: config.messages,
        max_tokens: config.maxTokens,
        temperature: config.temperature
      })
    });
    
    // 2. 解析响应
    const data = await response.json();
    
    // 3. 返回标准化格式
    return {
      content: data.choices[0].message.content,
      usage: {
        inputTokens: data.usage.prompt_tokens,
        outputTokens: data.usage.completion_tokens,
        totalTokens: data.usage.total_tokens
      },
      model: data.model,
      raw: data  // 保留原始响应供调试
    };
  }
});
```

### 6.2 自定义工具

扩展 Agent 的工具集：

```typescript
// packages/agent/src/tools/database-tool.ts
import { Tool, type ToolResult } from '../types';

export class DatabaseTool extends Tool {
  name = 'database_query';
  description = 'Execute a SQL query on the database';
  
  async execute(params: { sql: string }): Promise<ToolResult> {
    try {
      // 执行 SQL
      const result = await db.query(params.sql);
      
      return {
        success: true,
        output: JSON.stringify(result.rows),
        metadata: {
          rowCount: result.rowCount
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}

// 在 Agent 中注册
const agent = new Agent({
  llm,
  tools: [
    new DatabaseTool(),  // 新增自定义工具
    new ReadFileTool(),
    new WriteFileTool()
  ]
});
```

### 6.3 自定义记忆系统

实现持久化记忆：

```typescript
import { Memory, type MemoryEntry } from '@mariozechner/pi-agent-core';

class PostgresMemory extends Memory {
  async add(entry: MemoryEntry): Promise<void> {
    await db.query({
      text: 'INSERT INTO memories (content, embedding, metadata) VALUES ($1, $2, $3)',
      values: [entry.content, entry.embedding, entry.metadata]
    });
  }
  
  async search(query: string, limit: number = 10): Promise<MemoryEntry[]> {
    // 向量搜索
    const result = await db.query({
      text: `
        SELECT * FROM memories 
        ORDER BY embedding <=> $1
        LIMIT $2
      `,
      values: [generateEmbedding(query), limit]
    });
    
    return result.rows;
  }
}

// 使用自定义记忆
const agent = new Agent({
  llm,
  memory: new PostgresMemory()
});
```

### 6.4 Webhook 集成

Pi Agent 支持 Webhook 通知：

```typescript
const agent = new Agent({
  llm,
  webhook: {
    url: 'https://your-server.com/webhook',
    events: ['agent.start', 'agent.end', 'tool.call', 'error'],
    headers: {
      'Authorization': 'Bearer xxx'
    }
  }
});
```

---

## 7. 最佳实践

### 7.1 生产环境部署

**使用 PM2 管理进程**：

```bash
# 安装 PM2
npm install -g pm2

# 启动 Coding Agent
pm2 start ./packages/coding-agent/dist/index.js \
  --name pi-coding-agent \
  --env NODE_ENV=production

# 保存进程列表
pm2 save

# 设置开机自启
pm2 startup
```

**使用 Nginx 反向代理**：

```nginx
server {
    listen 443 ssl;
    server_name pi.your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }
}
```

### 7.2 安全配置

```bash
# .env.production
NODE_ENV=production

# API Keys 使用密钥管理服务
# 不要写在代码中！
OPENAI_API_KEY=${OPENAI_API_KEY}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

# 限制 Agent 权限
AGENT_MAX_BUDGET=1000      # 最大 Token 预算
AGENT_TIMEOUT=300000       # 超时 5 分钟
AGENT_ALLOWED_COMMANDS=git,node,npm  # 允许的命令白名单
```

**安全检查清单**：

- [ ] API Keys 存储在环境变量或密钥管理服务
- [ ] Agent 执行命令使用白名单机制
- [ ] 限制 Token 预算防止异常消耗
- [ ] 设置请求超时防止无限等待
- [ ] 生产环境使用 HTTPS
- [ ] 定期轮换 API Keys

### 7.3 性能优化

| 优化项 | 建议 | 实现方式 |
|--------|------|----------|
| **缓存 LLM 响应** | 启用响应缓存 | `pi-ai` 内置缓存 |
| **并发请求限制** | 限制并发数 | `RateLimiter` 中间件 |
| **连接池复用** | 复用 HTTP 连接 | Agent SDK 配置 |
| **本地模型加速** | 使用 Ollama | Ollama 部署本地模型 |

---

## 8. 常见问题

### Q1: Pi 和 LangChain 如何选择？

| 场景 | 推荐 | 原因 |
|------|------|------|
| 快速构建 Agent 原型 | **Pi** | 开箱即用，CLI 友好 |
| 复杂 LLM 应用 | **LangChain** | 链式调用丰富 |
| 需要 TUI/Web UI | **Pi** | 内置 UI 组件 |
| 企业级知识库集成 | **LangChain** | 文档加载器完善 |
| 多 Agent 协作 | **两者皆可** | Pi 支持，A LangChain 更成熟 |

### Q2: 如何添加新的 LLM Provider？

参见「6.1 自定义 Provider」章节。需要实现 `createProvider` 接口，返回标准化响应格式。

### Q3: Pi 支持流式输出吗？

✅ 支持。在调用 `chat()` 时传入 `stream: true` 即可获得流式响应：

```typescript
const stream = await openai.chat({
  messages: [{ role: 'user', content: '讲个故事' }],
  stream: true
});

for await (const chunk of stream) {
  process.stdout.write(chunk.content);
}
```

### Q4: 如何调试 Agent 的思考过程？

Pi 提供了详细的调试日志：

```bash
# 开启调试日志
DEBUG=pi-* ./pi-test.sh

# 查看特定模块
DEBUG=pi-agent ./pi-test.sh
```

### Q5: Pi 支持多语言吗？

Pi 的 Core 和 API 层语言无关。TUI/Web UI 默认英文，但支持自定义界面文本：

```typescript
const tui = new TUI({
  locale: 'zh-CN',
  translations: {
    'zh-CN': {
      welcome: '欢迎使用 Pi',
      thinking: '思考中...',
      error: '错误'
    }
  }
});
```

---

## 9. 总结

### 核心要点

1. **Pi = 模块化 AI Agent 工具包**：七大核心包，层层解耦，可独立使用
2. **统一 LLM API**：一行代码切换 OpenAI/Anthropic/Google/Ollama
3. **开箱即用的 Agent Runtime**：工具调用、状态管理、记忆系统全内置
4. **丰富的界面组件**：TUI + Web UI + Slack Bot
5. **vLLM 部署支持**：GPU Pods 管理 CLI

### 资源链接

| 资源 | 链接 |
|------|------|
| **GitHub 仓库** | https://github.com/badlogic/pi-mono |
| **官方文档** | https://pi.dev |
| **Discord 社区** | https://discord.com/invite/3cU7Bz4UPx |
| **问题反馈** | https://github.com/badlogic/pi-mono/issues |
| **npm 包** | https://www.npmjs.com/~mariozechner |

---

*文档信息：Pi Monorepo v0.64.0 | 更新日期：2026-03-30 | 难度：⭐⭐⭐⭐*
