---
title: "Page Agent：阿里巴巴开源的网页内置 GUI Agent"
date: "2026-04-06T21:20:00+08:00"
slug: "page-agent-alibaba-gui-agent-guide"
description: "全面介绍阿里巴巴开源的 Page Agent 网页内置 GUI Agent，涵盖集成方式、文本化 DOM 操作、MCP Server、Chrome 扩展和与 browser-use 的差异化定位。"
draft: false
categories: ["技术笔记"]
tags: ["Page Agent", "GUI Agent", "阿里巴巴", "浏览器自动化", "MCP", "Web"]
---

## 学习目标

通过本文，你将全面掌握以下核心能力：

- 深入理解 Page Agent 的项目定位、技术架构和设计理念
- 掌握在网页中集成 Page Agent 的两种方式（CDN 一行代码 + NPM）
- 学会使用文本化 DOM 操作进行自然语言浏览器控制
- 理解 MCP Server 的架构和外部控制能力
- 掌握 Chrome 扩展实现多页面 Agent 的方法
- 理解与 browser-use 的差异化定位

---

## 1. 项目概述

### 1.1 是什么

Page Agent 是阿里巴巴开源的**网页内置 GUI Agent**，核心理念是：**The GUI Agent Living in Your Webpage**——让网页拥有自己的 AI Agent，通过自然语言控制网页界面。

它让你只需一行 JavaScript 代码，就能在任何网页中注入 AI 助手，用户可以用自然语言完成点击、填写表单等操作。

### 1.2 核心定位

| 特性 | 说明 |
|------|------|
| **客户端增强** | 不需要浏览器扩展、Python 或无头浏览器 |
| **纯前端实现** | 一切发生在你的网页中 |
| **文本化 DOM** | 不需要截图、不需要多模态 LLM |
| **自带 LLM** | 支持接入各种大语言模型 |

### 1.3 与 browser-use 的关系

Page Agent 的 DOM 处理组件和提示词**源自 browser-use**，但定位不同：

| 项目 | 定位 | 实现方式 |
|------|------|---------|
| **Page Agent** | 客户端网页增强 | 纯前端 JavaScript，文本化 DOM |
| **browser-use** | 服务端自动化 | Python + 无头浏览器，截图+视觉 |

> Page Agent is designed for **client-side web enhancement**, not server-side automation.

### 1.4 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **15.5k** |
| GitHub Forks | **1.2k** |
| 最新版本 | **v1.7.1** |
| 贡献者 | **24** |
| 提交数 | **857** |
| License | **MIT** |

---

## 2. 核心特性详解

### 2.1 极简集成

**不需要后端重写**，只需一行代码：

```html
<script src="https://cdn.jsdelivr.net/npm/page-agent@1.7.1/dist/iife/page-agent.demo.js" crossorigin="true"></script>
```

### 2.2 文本化 DOM 操作

| 特性 | 说明 |
|------|------|
| **DOM 解析** | 将网页 DOM 结构化文本描述 |
| **元素定位** | 通过文本描述找到可交互元素 |
| **动作执行** | 自然语言转换为 DOM 操作 |
| **结果反馈** | 返回操作结果和页面状态 |

### 2.3 多 LLM 支持

```javascript
import { PageAgent } from 'page-agent';

const agent = new PageAgent({
  model: 'qwen3.5-plus',
  baseURL: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  apiKey: 'YOUR_API_KEY',
  language: 'en-US',
});

await agent.execute('Click the login button');
```

### 2.4 Chrome 扩展

可选的 Chrome 扩展支持**多页面任务**：

- 跨浏览器标签页协作
- 统一的任务分发
- 共享的浏览器上下文

### 2.5 MCP Server (Beta)

允许外部 Agent 客户端控制你的浏览器：

```javascript
// MCP Server 让外部 Agent 能够：
// - 控制本地浏览器
// - 执行跨页面任务
// - 共享浏览器状态
```

---

## 3. 快速上手

### 3.1 CDN 一行代码（最快）

```html
<!DOCTYPE html>
<html>
<head>
  <title>My Page with AI Agent</title>
</head>
<body>
  <!-- 你的网页内容 -->
  <button id="login">Login</button>
  
  <!-- 引入 Page Agent -->
  <script 
    src="https://cdn.jsdelivr.net/npm/page-agent@1.7.1/dist/iife/page-agent.demo.js" 
    crossorigin="true">
  </script>
</body>
</html>
```

> ⚠️ 注意：此 Demo CDN 使用免费的测试 LLM API，仅供技术评估使用。

**国内镜像**：

```html
<script src="https://registry.npmmirror.com/page-agent/1.7.1/files/dist/iife/page-agent.demo.js"></script>
```

### 3.2 NPM 安装（生产环境）

```bash
npm install page-agent
```

```javascript
import { PageAgent } from 'page-agent';

const agent = new PageAgent({
  // 使用阿里云 DashScope
  model: 'qwen3.5-plus',
  baseURL: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  apiKey: process.env.DASHSCOPE_API_KEY,
  
  // 设置语言
  language: 'en-US',
});

// 执行自然语言命令
await agent.execute('Fill in the username with john@example.com');
await agent.execute('Click the submit button');
```

### 3.3 支持的模型

| 提供商 | 模型 | 说明 |
|--------|------|------|
| **DashScope** | qwen3.5-plus, qwen-plus | 阿里云通义千问 |
| **OpenAI** | gpt-4o, gpt-4o-mini | OpenAI GPT 系列 |
| **Anthropic** | claude-sonnet-4, claude-opus | Claude 系列 |
| **Google** | gemini-pro | Gemini 系列 |
| **本地模型** | 支持 Ollama | 本地部署 |

---

## 4. 使用场景

### 4.1 SaaS AI Copilot

为你的产品快速添加 AI Copilot，无需后端重写：

```javascript
// 在你的 SaaS 产品中集成
const agent = new PageAgent({
  model: 'qwen3.5-plus',
  baseURL: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  apiKey: 'YOUR_API_KEY',
});

// 用户可以说："帮我填写这份订单"
await agent.execute('填写订单：客户名=张三，数量=100');
```

### 4.2 智能表单填写

将 20 次点击的工作流变成一句话：

```javascript
// ERP/CRM/管理系统的福音
await agent.execute(`
  表单填写任务：
  - 客户名称：阿里巴巴
  - 联系人：张三
  - 联系电话：13800138000
  - 订单金额：100000
  - 提交订单
`);
```

### 4.3 无障碍访问

让任何网页都能通过自然语言操控：

```javascript
// 支持语音命令
await agent.execute('找到设置按钮并点击');
await agent.execute('阅读当前页面的主要内容');
await agent.execute('滚动到页面底部');
```

### 4.4 多页面 Agent

通过 Chrome 扩展实现跨标签页协作：

- Tab 1: 打开产品列表
- Tab 2: 打开产品详情
- Tab 3: 填写购买表单

### 4.5 MCP 集成

让外部 Agent 控制你的浏览器：

```bash
# 启动 MCP Server
npx page-agent mcp-server

# 外部 Agent 可以发送命令
mcp-server.execute('在淘宝搜索 iPhone');
```

---

## 5. 技术架构深度解析

### 5.1 整体架构

```
┌─────────────────────────────────────┐
│         Page Agent                    │
├─────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐ │
│  │   Agent    │  │   Chrome    │ │
│  │   Core     │  │  Extension │ │
│  └──────┬──────┘  └──────┬──────┘ │
│         │                │         │
│  ┌──────▼──────┐  ┌──────▼──────┐ │
│  │    DOM      │  │ MCP Server │ │
│  │  Processor │  │  (Beta)   │ │
│  └──────┬──────┘  └───────────┘ │
│         │                          │
│  ┌──────▼──────┐                 │
│  │    LLM      │                 │
│  │  Adapter    │                 │
│  └─────────────┘                 │
└─────────────────────────────────────┘
```

### 5.2 DOM 处理器

DOM 处理器将网页结构转换为文本描述：

```javascript
// 输入：网页 DOM
// 输出：结构化文本描述
{
  "clickable_elements": [
    { "id": "btn-login", "text": "登录", "type": "button" },
    { "id": "input-name", "type": "text" },
    { "id": "input-email", "type": "email" },
  ],
  "page_title": "用户登录",
  "url": "https://example.com/login"
}
```

### 5.3 LLM 适配器

支持多种 LLM 提供商：

```typescript
// 适配器接口
interface LLMAdapter {
  chat(messages: Message[]): Promise<string>;
  stream(messages: Message[]): AsyncGenerator<string>;
}

// 支持的适配器
- DashScopeAdapter (阿里云)
- OpenAIAdapter
- AnthropicAdapter
- GoogleAdapter
- OllamaAdapter (本地)
```

---

## 6. MCP Server 详解

### 6.1 什么是 MCP

MCP (Model Context Protocol) 是一种让外部 Agent 能够控制本地浏览器的协议。

### 6.2 启动 MCP Server

```bash
# 全局安装
npm install -g page-agent

# 启动 Server
npx page-agent mcp-server
```

### 6.3 连接外部 Agent

```javascript
// MCP Server 配置
{
  "server": {
    "type": "stdio",
    "command": "npx",
    "args": ["page-agent", "mcp-server"]
  },
  "client": {
    "name": "my-agent",
    "version": "1.0.0"
  }
}
```

### 6.4 MCP 命令示例

```python
# Python Agent 客户端示例
from page_agent_mcp import PageAgentClient

client = PageAgentClient()

# 让 Agent 控制浏览器
await client.execute("打开淘宝首页")
await client.execute("搜索 iPhone 15")
await client.execute("点击第一个商品")
```

---

## 7. Chrome 扩展

### 7.1 安装

1. 访问 Chrome 扩展商店（待发布）
2. 点击"添加到 Chrome"
3. 授权需要的权限

### 7.2 多页面协作

```javascript
// 扩展支持多标签页协调
await browser.tabs.execute({
  // 在所有打开的标签页中搜索
  script: 'pageAgent.execute("找到所有商品链接")',
  match: { url: /taobao\.com\/item\/.*/ }
});
```

### 7.3 跨页面上下文共享

```javascript
// 页面1：获取商品信息
const productInfo = await pageAgent.execute('提取当前商品名称和价格');

// 页面2：填写订单
await pageAgent.execute(`填写订单：${productInfo}`);
```

---

## 8. 实践建议

### 8.1 集成建议

| 场景 | 推荐方式 |
|------|---------|
| **快速演示** | CDN 一行代码 |
| **生产环境** | NPM 安装 + API Key |
| **多页面任务** | Chrome 扩展 |
| **外部 Agent** | MCP Server |

### 8.2 安全考虑

```javascript
// 生产环境务必配置 API Key
const agent = new PageAgent({
  model: 'qwen3.5-plus',
  baseURL: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
  apiKey: process.env.DASHSCOPE_API_KEY, // 放在环境变量中
});

// 不要在前端暴露明文 API Key
```

### 8.3 错误处理

```javascript
try {
  await agent.execute('点击登录按钮');
} catch (error) {
  if (error.code === 'ELEMENT_NOT_FOUND') {
    // 元素未找到，尝试替代方案
    await agent.execute('点击页面上的第一个按钮');
  } else if (error.code === 'LLM_ERROR') {
    // LLM 调用失败
    console.error('AI 服务暂时不可用');
  }
}
```

### 8.4 性能优化

```javascript
// 避免频繁的 DOM 查询
const context = await agent.getPageContext({
  includeHidden: false,
  maxElements: 50,
});

// 批量操作比单个操作更高效
await agent.execute(`
  1. 点击用户名输入框
  2. 输入 "admin"
  3. 点击密码输入框
  4. 输入 "123456"
  5. 点击登录按钮
`);
```

---

## 9. 总结

Page Agent 是前端 AI Agent 领域的一个创新解决方案：

**为什么选择 Page Agent：**

| 优势 | 说明 |
|------|------|
| **零后端重写** | 只需前端集成，不改变现有架构 |
| **文本化 DOM** | 不需要截图，不需要多模态 LLM |
| **轻量快速** | 纯前端实现，加载即用 |
| **MCP 支持** | 可与外部 Agent 集成 |
| **阿里背书** | 阿里巴巴开源，品质保证 |

**不适用的场景：**

- 需要深度浏览器控制的自动化任务（使用 browser-use）
- 纯后端的网页抓取（使用 Playwright/Puppeteer）
- 需要截图和视觉理解的复杂任务（使用 GPT-4V）

---

**附录：相关资源**

- GitHub：https://github.com/alibaba/page-agent
- 官方文档：https://alibaba.github.io/page-agent/
- 在线 Demo：https://alibaba.github.io/page-agent/
- NPM：https://www.npmjs.com/package/page-agent
- MCP Server：https://alibaba.github.io/page-agent/docs/features/mcp-server
- Chrome 扩展：https://alibaba.github.io/page-agent/docs/features/chrome-extension