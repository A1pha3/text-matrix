---
title: "Chrome DevTools MCP：让 AI 编程代理操控 Chrome 的官方方案"
date: "2026-05-21T20:16:13+08:00"
slug: "chrome-devtools-mcp-ai-coding-agent-chrome"
description: "Chrome DevTools MCP 通过 Model Context Protocol 把 Chrome DevTools 协议暴露给 AI 编程代理，让 Claude Code、Codex 等可以直接操控 Chrome 浏览器。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Chrome", "MCP", "Claude Code", "浏览器自动化"]
---

# Chrome DevTools MCP：让 AI 编程代理操控 Chrome 的官方方案

[![GitHub stars](https://img.shields.io/github/stars/ChromeDevTools/chrome-devtools-mcp?style=flat)](https://github.com/ChromeDevTools/chrome-devtools-mcp/stargazers)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

**让 AI 编程代理（Claude Code、Codex 等）通过 Chrome DevTools 协议直接操控 Chrome 浏览器。**

## 背景：为什么 AI 代理需要浏览器控制能力

当前主流的 AI 编程代理（Claude Code、Codex、Cursor Agent 等）都能读写文件、搜索代码库、执行 Shell 命令，但在**浏览器操控**方面能力有限。现实中大量任务需要浏览器参与：

- **Web 抓取**：需要登录的页面、JS 渲染的内容
- **UI 测试**：端到端测试（E2E testing）
- **自动化任务**：填表、点击、登录、截图
- **性能分析**：基于真实用户数据的性能诊断

虽然有 Puppeteer、Playwright 等工具，但它们需要单独集成，不在 AI 代理的原生能力范围内。

**Chrome DevTools MCP** 通过 Model Context Protocol（MCP）把 Chrome DevTools 协议直接暴露给 AI 代理，让代理可以像人类开发者一样操控 Chrome。

---

## 什么是 MCP（Model Context Protocol）

MCP 是 Anthropic 在 2024 年末推出的开放协议，旨在让 AI 模型与外部工具（文件系统、浏览器、数据库等）标准化对接。

```
AI 模型 ←→ MCP 协议 ←→ MCP Server ←→ Chrome DevTools
```

MCP 的核心优势：
- **统一接口**：不同工具（浏览器、数据库、文件系统）通过同一个协议接入
- **安全隔离**：工具调用经过协议层，不直接暴露敏感数据
- **实时反馈**：工具执行结果实时返回给模型

---

## Chrome DevTools MCP 核心能力

### 1. 浏览器导航与交互

```json
// MCP 工具调用示例
{
  "name": "navigate",
  "parameters": {
    "url": "https://github.com"
  }
}
```

代理可以：
- 打开任意 URL
- 点击元素（按钮、链接、表单）
- 填写输入框
- 提交表单
- 滚动页面

### 2. 网络抓包与请求拦截

```json
{
  "name": "start_network_tracking"
}
```

代理可以：
- 监听所有网络请求
- 查看请求/响应详情（Headers、Body、Timing）
- 修改请求/响应（注入 JS、修改 Cookie）
- 模拟慢速网络测试

这对 AI 代理理解 Web 应用的网络行为极其有用。

### 3. JavaScript 执行

```json
{
  "name": "evaluate",
  "parameters": {
    "expression": "document.querySelectorAll('.repo-title')"
  }
}
```

在页面上下文中执行任意 JavaScript，直接读取 DOM 结构、提取数据。

### 4. 截图与屏幕录制

```json
{
  "name": "screenshot",
  "parameters": {
    "fullPage": true
  }
}
```

- 全页面截图
- 指定元素截图
- 屏幕录制（用于记录代理操作过程）

### 5. 控制台日志捕获

```json
{
  "name": "get_console_messages",
  "parameters": {}
}
```

捕获页面 Console 输出，用于调试和理解 Web 应用行为。

### 6. 性能分析

```json
{
  "name": "start_performance_tracing"
}
```

- 捕获 Performance Trace
- 分析页面加载性能
- 获取真实用户数据（CrUX）

---

## 工作原理

### 架构

```
AI Agent (Claude Code / Codex)
         ↓ MCP Client
    MCP Server (chrome-devtools-mcp)
         ↓ Chrome DevTools Protocol (CDP)
    Chrome (with remote debugging enabled)
```

### Chrome DevTools Protocol (CDP)

Chrome 内置了 CDP（Chrome DevTools Protocol），这是 Chrome DevTools 背后的协议。通过 CDP，可以：

- 检查和控制 Chrome 的每一个页面
- 拦截网络请求
- 注入 JavaScript
- 获取性能数据

**Chrome DevTools MCP** 的本质是一个 **CDP → MCP 的桥接器**，把 CDP 的能力以 MCP 工具的形式暴露给 AI 代理。

### 连接方式

Chrome 启动时开启远程调试端口：

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Linux
google-chrome --remote-debugging-port=9222

# Windows
chrome.exe --remote-debugging-port=9222
```

然后 MCP Server 通过 WebSocket 连接到这个端口：

```
ws://localhost:9222/devtools/page/<target-id>
```

---

## 安装与配置

### 前提条件

- Node.js LTS
- Chrome 当前稳定版
- npm

### 快速安装

**方式一：直接运行**

```bash
npx -y chrome-devtools-mcp@latest
```

**方式二：在 Claude Code 中配置**

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

**方式三：在 Cursor Agent 中配置**

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest"]
    }
  }
}
```

### 启动 Chrome（开启远程调试）

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# 或者启动已存在的 Chrome 实例
open -a "Google Chrome" --args --remote-debugging-port=9222
```

### 验证

启动后，MCP Server 默认监听 `http://localhost:9222`。可以用以下命令验证：

```bash
curl http://localhost:9222/json
```

返回当前打开的所有标签页列表。

---

## MCP 工具列表

### 会话与导航

| 工具 | 说明 |
|------|------|
| `sessions_list` | 列出所有打开的浏览器会话 |
| `navigate` | 导航到指定 URL |
| `reload` | 刷新当前页面 |
| `go_back` | 后退 |
| `go_forward` | 前进 |

### 内容采集

| 工具 | 说明 |
|------|------|
| `screenshot` | 截图（支持全页面） |
| `screenrecord_start` | 开始屏幕录制 |
| `screenrecord_stop` | 停止屏幕录制并返回视频 |
| `evaluate` | 在页面中执行 JS 表达式 |
| `get_document` | 获取完整 DOM 树 |
| `get_computed_styles` | 获取元素的计算样式 |

### 网络

| 工具 | 说明 |
|------|------|
| `start_network_tracking` | 开始网络请求追踪 |
| `stop_network_tracking` | 停止网络追踪并返回结果 |
| `get_network_logs` | 获取捕获的网络日志 |

### 控制台

| 工具 | 说明 |
|------|------|
| `get_console_messages` | 获取 Console 日志 |
| `console_log` | 向 Console 写入日志 |

### 性能

| 工具 | 说明 |
|------|------|
| `start_performance_tracing` | 开始性能追踪 |
| `stop_performance_tracing` | 停止性能追踪并返回 Trace |
| `get_performance_metrics` | 获取性能指标 |

### 输入交互

| 工具 | 说明 |
|------|------|
| `click` | 点击元素 |
| `double_click` | 双击元素 |
| `hover` | 悬停元素 |
| `type_text` | 输入文本 |
| `select_option` | 选择下拉选项 |
| `check` | 勾选复选框 |
| `press_key` | 按键盘按键 |

---

## 实际应用场景

### 场景 1：AI 代理帮你填表

```bash
# 让 Claude Code 帮你填写一个网页表单
# 提示词：打开 https://example.com/form，然后填写姓名为张三，邮箱为 zhangsan@example.com，然后提交
```

### 场景 2：自动化 Web 抓取

Claude Code 可以配合 MCP 抓取需要 JS 渲染的页面：

1. 导航到目标页面
2. 执行 JS 提取数据
3. 截图记录抓取结果

### 场景 3：E2E 测试

```bash
# 让代理帮你做端到端测试
# 提示词：打开购物网站，添加一件商品到购物车，然后结算，截图确认订单成功
```

### 场景 4：性能问题诊断

```bash
# 让代理帮你分析页面性能
# 提示词：打开 https://yoursite.com，用 Performance API 抓取 10 秒 Trace，然后告诉我 Largest Contentful Paint 时间
```

---

## 数据收集与隐私

### 隐私政策

- **CrUX 数据**：性能工具可能向 Google CrUX API 发送请求，获取真实用户体验数据（可选，可通过 `--no-performance-crux` 禁用）
- **使用统计**：默认开启，可通过 `--no-usage-statistics` 禁用
- **更新检查**：默认开启，可通过环境变量 `CHROME_DEVTOOLS_MCP_NO_UPDATE_CHECKS` 禁用

### 禁用数据收集

```bash
# 禁用所有可选的数据收集
npx -y chrome-devtools-mcp@latest \
  --no-usage-statistics \
  --no-performance-crux \
  --no-update-checks
```

或者设置环境变量：

```bash
export CHROME_DEVTOOLS_MCP_NO_USAGE_STATISTICS=1
export CHROME_DEVTOOLS_MCP_NO_UPDATE_CHECKS=1
export CI=1
```

---

## 与 Playwright/Puppeteer 的对比

| 特性 | Chrome DevTools MCP | Playwright | Puppeteer |
|------|---------------------|------------|-----------|
| **接入方式** | MCP 协议 | 代码库 | 代码库 |
| **AI 代理原生支持** | ✅ 是 | ❌ 否 | ❌ 否 |
| **协议类型** | WebSocket | HTTP/CDP | HTTP/CDP |
| **主要用途** | AI Agent 工具 | 自动化测试 | 自动化测试 |
| **学习曲线** | 低（MCP 工具调用） | 中 | 中 |
| **语言** | TypeScript | 多语言 | Node.js |
| **社区** | 活跃（Anthropic 官方） | 非常活跃 | 活跃 |

---

## 结论

Chrome DevTools MCP 是第一个真正把 Chrome 控制能力引入 AI 编程代理生态的官方工具。它让 AI 代理可以像人类开发者一样操控浏览器、采集数据、执行自动化任务、诊断性能问题。

如果你正在使用 Claude Code、Codex 或其他 MCP 兼容的 AI 代理，这个工具值得关注。

---

**GitHub 地址**：[https://github.com/ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp)
