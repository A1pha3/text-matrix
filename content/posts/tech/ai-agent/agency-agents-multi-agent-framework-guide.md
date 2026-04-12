---
title: "Agency Agents：轻量级多智能体工作流框架完全指南"
slug: "agency-agents-multi-agent-framework-guide"
aliases:
  - /posts/tech/agency-agents-multi-agent-framework-guide/
date: 2026-04-01T01:25:00+08:00
categories: ["技术笔记"]
tags: ["Agency Agents", "多智能体", "Multi-Agent", "Claude API", "TypeScript", "工作流", "记忆管理", "AI Agent", "工具集成"]
description: "深度解析 Agency Agents 框架：基于 Claude API 的轻量级多智能体工作流框架，支持高级记忆管理、推理能力、工具使用和流式响应，TypeScript 编写，MIT 许可证。"
---

# Agency Agents：轻量级多智能体工作流框架完全指南

> 预计阅读时间：30分钟 | 难度：⭐⭐⭐

---

## §2 项目概述

### 2.1 什么是 Agency Agents？

**Agency Agents**（[GitHub 仓库](https://github.com/msitarzewski/agency-agents)）是一个**轻量级框架**，用于构建具有高级记忆、推理和工具使用的多智能体工作流，基于 Claude API 构建。

**官方描述**：

> A lightweight framework for building multi-agent workflows with advanced memory, reasoning, and tool use. Built on top of Claude's API.

**官网**：无官方独立网站

**GitHub**：https://github.com/msitarzewski/agency-agents

### 2.2 核心数据

| 指标 | 数值 |
|------|------|
| **Stars** | 2.4k (2,384) |
| **Forks** | 204 |
| **Watchers** | 14 |
| **提交数** | 97 |
| **分支** | 2 |
| **Tags** | 1 |
| **Releases** | 1 (v1.0.0) |
| **贡献者** | 2 |
| **许可证** | MIT |

### 2.3 语言分布

| 语言 | 占比 |
|------|------|
| **TypeScript** | 94.7% |
| **Shell** | 3.0% |
| **JavaScript** | 1.7% |
| **其他** | 0.6% |

### 2.4 发展历程

| 日期 | 事件 |
|------|------|
| **2026.03.30** | v1.0.0 发布 (首次 Release) |
| **2026.03.30** | 最新 commit: feat(evaluation): Add evaluation for multi-turn conversations (#48) |

### 2.5 与其他框架的区别

| 特性 | Agency Agents | AutoGen | CrewAI | LangGraph |
|------|---------------|---------|--------|-----------|
| **复杂度** | 轻量 | 中等 | 中等 | 较高 |
| **基于 Claude** | 原生 | 部分 | 部分 | 否 |
| **TypeScript** | 原生 | 否 | 否 | 否 |
| **记忆管理** | 内置 | 需扩展 | 需扩展 | 需扩展 |
| **学习曲线** | 平缓 | 中等 | 中等 | 较陡 |

---

## §3 核心功能详解

### 3.1 多智能体工作流

**核心理念**：定义具有角色、目标和行为的智能体，构建协作工作流。

#### 3.1.1 智能体定义

```typescript
import { Agency, Agent } from 'agency-agents';

const researcher = new Agent({
  name: 'Researcher',
  goal: 'Find and summarize information about a given topic',
  model: 'claude-3-5-sonnet-20241022',
  backstory: 'You are an expert researcher with years of experience in finding and synthesizing information.'
});

const writer = new Agent({
  name: 'Writer',
  goal: 'Create clear, engaging content based on research',
  model: 'claude-3-5-sonnet-20241022',
  backstory: 'You are a professional writer who transforms complex information into accessible content.'
});
```

#### 3.1.2 工作流编排

```typescript
// 创建 Agency
const agency = new Agency();

// 添加多个智能体
agency.addAgent(researcher);
agency.addAgent(writer);

// 定义工作流
agency.createWorkflow({
  name: 'Research and Write',
  agents: [researcher, writer],
  tasks: [
    {
      agent: researcher,
      task: 'Research the latest developments in AI'
    },
    {
      agent: writer,
      task: 'Write a blog post about the research'
    }
  ]
});

// 执行工作流
const result = await agency.run('Write a blog post about AI');
```

### 3.2 高级记忆管理

**内置的记忆系统**，追踪对话历史和上下文。

#### 3.2.1 记忆类型

| 类型 | 说明 |
|------|------|
| **Short-term Memory** | 当前对话的上下文 |
| **Long-term Memory** | 持久化的知识和经验 |
| **Working Memory** | 当前任务的中间状态 |

#### 3.2.2 记忆配置

```typescript
const agent = new Agent({
  name: 'Assistant',
  goal: 'Help users with their tasks',
  model: 'claude-3-5-sonnet-20241022',
  memory: {
    type: 'hybrid', // 'short' | 'long' | 'hybrid'
    maxTokens: 100000,
    summaryThreshold: 0.8
  }
});
```

### 3.3 工具使用

**扩展智能体能力**，集成自定义工具。

#### 3.3.1 内置工具

| 工具 | 说明 |
|------|------|
| **WebSearch** | 网络搜索 |
| **Calculator** | 数学计算 |
| **CodeInterpreter** | 代码执行 |
| **FileReader** | 文件读取 |

#### 3.3.2 自定义工具

```typescript
import { Tool } from 'agency-agents';

const weatherTool = new Tool({
  name: 'get_weather',
  description: 'Get weather information for a location',
  parameters: {
    location: {
      type: 'string',
      required: true,
      description: 'The city name'
    }
  },
  handler: async ({ location }) => {
    // 调用天气 API
    const weather = await fetchWeatherAPI(location);
    return weather;
  }
});

// 添加工具到智能体
agent.addTool(weatherTool);
```

### 3.4 推理能力

**内置推理引擎**，处理复杂任务。

#### 3.4.1 推理模式

```typescript
const agent = new Agent({
  name: 'Problem Solver',
  goal: 'Solve complex problems step by step',
  model: 'claude-3-5-sonnet-20241022',
  reasoning: {
    type: 'chain_of_thought', // 'chain_of_thought' | 'tree_of_thought'
    maxDepth: 5,
    confidenceThreshold: 0.9
  }
});
```

### 3.5 流式响应

**实时流式输出**，提供即时反馈。

```typescript
const stream = agency.run('Write a story', { streaming: true });

for await (const chunk of stream) {
  console.log(chunk); // 实时输出
}
```

### 3.6 持久化

**保存和加载智能体状态**。

```typescript
// 保存状态
await agent.saveState('agent-state.json');

// 加载状态
await agent.loadState('agent-state.json');

// 跨会话持久化
const persistentAgency = new Agency({
  storage: {
    type: 'file', // 'file' | 'database' | 'cloud'
    path: './agency-state'
  }
});
```

---

## §4 技术架构

### 4.1 核心模块

| 模块 | 说明 |
|------|------|
| **Agency** | 主协调器，管理多个智能体和工作流 |
| **Agent** | 智能体单元，封装 LLM 调用和工具 |
| **Memory** | 记忆系统，管理上下文和历史 |
| **Tool** | 工具系统，扩展智能体能力 |
| **Reasoning** | 推理引擎，处理复杂任务 |
| **Workflow** | 工作流编排器 |

### 4.2 架构图

```
用户输入
    ↓
Agency (协调器)
    ↓
┌─────────────────────────────────────┐
│  Workflow (工作流编排)              │
│                                     │
│  ┌─────────┐    ┌─────────┐        │
│  │ Agent 1 │ →  │ Agent 2 │ → ...│
│  └─────────┘    └─────────┘        │
│      ↓              ↓               │
│  ┌─────────┐    ┌─────────┐        │
│  │ Memory  │    │  Tools  │        │
│  └─────────┘    └─────────┘        │
└─────────────────────────────────────┘
    ↓
LLM (Claude API)
    ↓
流式输出
```

### 4.3 数据流

```
用户请求
    ↓
请求解析与任务分解
    ↓
智能体选择与调度
    ↓
┌──────────────────────────────────────┐
│ 并发/顺序执行                         │
│                                      │
│ Agent.execute()                      │
│   ↓                                 │
│ Memory.loadContext()                │
│   ↓                                 │
│ Reasoning.process()                 │
│   ↓                                 │
│ Tool.execute()                      │
│   ↓                                 │
│ LLM.call()                           │
│   ↓                                 │
│ Memory.saveContext()                │
└──────────────────────────────────────┘
    ↓
结果聚合与输出
    ↓
流式响应
```

---

## §5 快速开始

### 5.1 安装

```bash
npm install agency-agents
# 或
yarn add agency-agents
# 或
pnpm add agency-agents
```

### 5.2 环境配置

```bash
# 设置 Claude API 密钥
export ANTHROPIC_API_KEY='your-api-key'
```

### 5.3 首个示例

```typescript
import { Agency, Agent } from 'agency-agents';

async function main() {
  // 创建智能体
  const assistant = new Agent({
    name: 'Assistant',
    goal: 'Help users with their questions',
    model: 'claude-3-5-sonnet-20241022'
  });

  // 创建 Agency
  const agency = new Agency();
  agency.addAgent(assistant);

  // 运行
  const response = await agency.run('What is the capital of France?');
  console.log(response);
}

main();
```

### 5.4 TypeScript 配置

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "esModuleInterop": true
  }
}
```

---

## §6 使用指南

### 6.1 基本用法

#### 6.1.1 单智能体

```typescript
import { Agent } from 'agency-agents';

const agent = new Agent({
  name: 'ChatBot',
  goal: 'Conversational AI assistant',
  model: 'claude-3-5-sonnet-20241022'
});

const response = await agent.run('Hello!');
console.log(response);
```

#### 6.1.2 多智能体协作

```typescript
const researcher = new Agent({
  name: 'Researcher',
  goal: 'Find accurate information',
  model: 'claude-3-5-sonnet-20241022'
});

const editor = new Agent({
  name: 'Editor',
  goal: 'Polish and refine content',
  model: 'claude-3-5-sonnet-20241022'
});

const agency = new Agency();
agency.addAgent(researcher);
agency.addAgent(editor);

// 研究员找信息，编辑润色
const result = await agency.run(
  'Find information about climate change and write a summary'
);
```

### 6.2 工具集成

#### 6.2.1 使用内置工具

```typescript
import { Agency, Agent, Tools } from 'agency-agents';

const agent = new Agent({
  name: 'Assistant',
  goal: 'Help with various tasks',
  model: 'claude-3-5-sonnet-20241022',
  tools: [Tools.webSearch, Tools.calculator]
});

const result = await agent.run(
  'What is 15% of 200 and search for latest AI news?'
);
```

#### 6.2.2 自定义工具

```typescript
import { Tool } from 'agency-agents';

const searchTool = new Tool({
  name: 'search_code',
  description: 'Search for code snippets',
  parameters: {
    query: { type: 'string', required: true },
    language: { type: 'string', required: false }
  },
  handler: async ({ query, language }) => {
    // 实现搜索逻辑
    const results = await searchCodeAPI(query, language);
    return results;
  }
});

const agent = new Agent({
  name: 'Developer Assistant',
  goal: 'Help with coding tasks',
  model: 'claude-3-5-sonnet-20241022',
  tools: [searchTool]
});
```

### 6.3 记忆管理

#### 6.3.1 短期记忆

```typescript
const agent = new Agent({
  name: 'Assistant',
  goal: 'Remember and use context',
  model: 'claude-3-5-sonnet-20241022',
  memory: {
    type: 'short',
    maxTokens: 50000
  }
});

// 对话历史被自动维护
await agent.run('My name is John');
const response = await agent.run('What is my name?');
// response 将包含 "John"
```

#### 6.3.2 长期记忆

```typescript
const agent = new Agent({
  name: 'Assistant',
  goal: 'Learn from interactions',
  model: 'claude-3-5-sonnet-20241022',
  memory: {
    type: 'long',
    storagePath: './memory-store',
    embeddingModel: 'text-embedding-3-small'
  }
});
```

### 6.4 流式响应

```typescript
const stream = await agency.run(
  'Write a long story about space exploration',
  { streaming: true }
);

for await (const chunk of stream) {
  process.stdout.write(chunk);
}
```

### 6.5 工作流

#### 6.5.1 定义工作流

```typescript
agency.createWorkflow({
  name: 'Content Pipeline',
  agents: [researcher, writer, editor],
  tasks: [
    {
      agent: researcher,
      task: 'Research the topic thoroughly',
      outputKey: 'research'
    },
    {
      agent: writer,
      task: 'Write initial draft using research: {research}',
      outputKey: 'draft',
      dependsOn: ['research']
    },
    {
      agent: editor,
      task: 'Edit and polish the draft: {draft}',
      outputKey: 'final',
      dependsOn: ['draft']
    }
  ]
});

const result = await agency.runWorkflow('Content Pipeline', {
  topic: 'Artificial Intelligence'
});
```

---

## §7 高级配置

### 7.1 模型配置

```typescript
const agent = new Agent({
  name: 'Assistant',
  goal: 'Help with tasks',
  model: 'claude-3-5-sonnet-20241022',
  modelConfig: {
    temperature: 0.7,
    maxTokens: 4096,
    topP: 0.9,
    stopSequences: ['END']
  }
});
```

### 7.2 并发控制

```typescript
const agency = new Agency({
  maxConcurrency: 3, // 最大并发智能体数
  timeout: 60000     // 超时时间（毫秒）
});
```

### 7.3 错误处理

```typescript
const agency = new Agency({
  errorHandling: {
    maxRetries: 3,
    retryDelay: 1000,
    onError: (error) => {
      console.error('Agency error:', error);
    }
  }
});
```

---

## §8 开发扩展

### 8.1 自定义智能体类型

```typescript
import { Agent, AgentConfig } from 'agency-agents';

class SpecializedAgent extends Agent {
  constructor(config: AgentConfig) {
    super(config);
    this.specializedBehavior();
  }

  private specializedBehavior() {
    // 自定义行为
  }

  async execute(task: string): Promise<string> {
    // 自定义执行逻辑
    return super.execute(task);
  }
}
```

### 8.2 自定义工具开发

```typescript
import { Tool, ToolResult } from 'agency-agents';

export class DatabaseTool extends Tool {
  constructor() {
    super({
      name: 'query_database',
      description: 'Execute SQL queries',
      parameters: {
        sql: { type: 'string', required: true }
      }
    });
  }

  async handler({ sql }: { sql: string }): Promise<ToolResult> {
    try {
      const results = await executeSQL(sql);
      return {
        success: true,
        data: results
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }
}
```

### 8.3 记忆存储扩展

```typescript
import { MemoryStore } from 'agency-agents';

class CustomMemoryStore extends MemoryStore {
  async save(key: string, value: any): Promise<void> {
    // 自定义存储逻辑
  }

  async load(key: string): Promise<any> {
    // 自定义加载逻辑
  }

  async delete(key: string): Promise<void> {
    // 自定义删除逻辑
  }
}
```

---

## §9 最佳实践

### 9.1 智能体设计

| 实践 | 说明 |
|------|------|
| **单一职责** | 每个智能体专注于特定任务 |
| **清晰目标** | 为每个智能体定义明确的目标 |
| **适当背景** | 提供丰富的 backstory 增加上下文 |
| **工具精简** | 只添加必要的工具 |

### 9.2 性能优化

| 实践 | 说明 |
|------|------|
| **记忆管理** | 合理设置 maxTokens 避免浪费 |
| **并发控制** | 根据 API 限制调整并发数 |
| **缓存** | 对频繁使用的上下文进行缓存 |
| **批处理** | 批量处理相似任务 |

### 9.3 安全实践

| 实践 | 说明 |
|------|------|
| **API 密钥** | 使用环境变量存储密钥 |
| **工具权限** | 限制工具的敏感操作 |
| **输入验证** | 验证用户输入防止注入 |
| **审计日志** | 记录所有操作 |

---

## §10 应用场景

### 10.1 自动化写作

```typescript
const researcher = new Agent({
  name: 'Researcher',
  goal: 'Gather accurate information',
  tools: [Tools.webSearch]
});

const writer = new Agent({
  name: 'Writer',
  goal: 'Create engaging content'
});

const agency = new Agency();
agency.addAgents([researcher, writer]);

// 自动化写作工作流
const article = await agency.run(
  'Write an article about the latest AI trends'
);
```

### 10.2 代码审查

```typescript
const reviewer = new Agent({
  name: 'Code Reviewer',
  goal: 'Review code for bugs and improvements',
  model: 'claude-3-5-sonnet-20241022'
});

const agency = new Agency();
const result = await agency.run(
  `Review this code:\n${codeSnippet}`
);
```

### 10.3 客户服务

```typescript
const assistant = new Agent({
  name: 'Customer Support',
  goal: 'Help customers with their inquiries',
  memory: { type: 'long' }
});

const agency = new Agency();
agency.addAgent(assistant);
```

---

## §11 常见问题

### Q1: Agency Agents 和 LangChain Agents 有什么区别？

Agency Agents 是轻量级 TypeScript 框架，原生支持 Claude API，学习曲线平缓。LangChain Agents 是更通用的框架，支持多种 LLM，但配置更复杂。

### Q2: 支持哪些 LLM？

目前主要针对 Claude API 优化。支持 claude-3-5-sonnet、claude-3-opus 等模型。

### Q3: 如何处理 API 限流？

使用 `maxConcurrency` 控制并发数，设置 `timeout` 处理超时，配置 `errorHandling` 进行重试。

### Q4: 如何持久化记忆？

使用 `memory.type: 'long'` 配置长期记忆，设置 `storagePath` 指定存储路径。

### Q5: 如何调试多智能体工作流？

启用 `debug: true` 获取详细日志，使用 `workflow.visualize()` 可视化工作流执行过程。

---

## §12 总结

### 12.1 核心优势

| 优势 | 说明 |
|------|------|
| **轻量级** | 简单的 API，易于上手 |
| **TypeScript 原生** | 完整的类型支持 |
| **Claude 优先** | 针对 Claude API 深度优化 |
| **内置记忆** | 无需额外配置记忆系统 |
| **流式响应** | 实时输出体验 |
| **可扩展** | 支持自定义智能体和工具 |

### 12.2 适用场景

| 场景 | 说明 |
|------|------|
| **快速原型** | 快速构建多智能体原型 |
| **简单工作流** | 1-5 个智能体的中等复杂度任务 |
| **Claude 优先** | 深度使用 Claude 能力 |
| **TypeScript 项目** | 前端/Node.js 项目集成 |

### 12.3 项目信息

| 项目 | 信息 |
|------|------|
| **Stars** | 2.4k |
| **Forks** | 204 |
| **许可证** | MIT |
| **语言** | TypeScript 94.7% |
| **最新版本** | v1.0.0 |
| **最新更新** | Mar 30, 2026 |

### 12.4 相关链接

| 资源 | 链接 |
|------|------|
| **GitHub** | https://github.com/msitarzewski/agency-agents |
| **npm** | https://www.npmjs.com/package/agency-agents |