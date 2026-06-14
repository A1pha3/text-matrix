---
title: "chrome-devtools-mcp 完全指南：让 AI 编程助手掌控 Chrome DevTools"
date: "2026-04-18T11:35:00+08:00"
slug: "chrome-devtools-mcp-ai-coding-agents-guide"
aliases:
  - "/posts/tech/chrome-devtools-mcp/"
  - "/posts/tech/chrome-devtools-mcp-ai-browser-control/"
  - "/posts/tech/chrome-devtools-mcp-ai-coding-agent-chrome/"
  - "/posts/tech/chrome-devtools-mcp-ai-coding-agents/"
description: "全面解析 ChromeDevTools/chrome-devtools-mcp 项目：MCP 协议如何桥接 AI 编码助手与 Chrome DevTools，puppeteer 底层原理、架构设计、所有工具函数详解、开发扩展方法与最佳实践。"
draft: false
categories: ["技术笔记"]
tags: ["MCP", "Chrome DevTools", "Puppeteer", "AI Agent", "浏览器自动化", "Claude"]
---

> **目标读者**：希望将 AI 编码助手（Claude、Cursor、Copilot、Copilot）深度接入浏览器能力的前端工程师、全栈工程师与 AI Agent 开发者。
> **核心问题**：`chrome-devtools-mcp` 通过 MCP 协议赋予 AI Agent 操作 Chrome DevTools 的能力——具体是怎么做到的？底层依赖是什么？有哪些能力边界？又该如何扩展？
> **事实边界**：本文基于 `ChromeDevTools/chrome-devtools-mcp` 公开仓库信息整理，涵盖 README 功能列表、工具函数签名及 npm 包元数据。

---

## 阅读导航

- 只想快速安装跑起来 → 直接看 `§5 使用说明`
- 想理解 MCP 协议如何与 Puppeteer 衔接 → 重点看 `§2 原理分析`
- 想了解全部能力边界 → 重点看 `§4 功能详解`
- 想定制自己的 DevTools MCP 服务 → 重点看 `§6 开发扩展`
- 遇到常见问题 → 直接查 `§8 FAQ`

---

## §1 学习目标

完成本文后，你应该能够：

1. **理解原理**：说清楚 MCP 协议是什么、`chrome-devtools-mcp` 如何通过 Puppeteer 控制 Chrome，以及 CDP（Chrome DevTools Protocol）在这一链路中的角色。
2. **掌握全貌**：列举出 `chrome-devtools-mcp` 提供的所有工具函数，知道每个函数的输入输出语义。
3. **正确安装**：在 Node.js v20.19+ 环境下成功安装、启动并验证 `chrome-devtools-mcp`。
4. **集成使用**：将 MCP server 配置到 Claude Desktop（或其他 MCP 客户端），并完成一次完整的浏览器自动化任务（截图、抓控制台日志、监听网络请求）。
5. **安全扩展**：理解该项目的权限边界，知道如何在开发分支上添加自定义工具函数，以及如何安全地控制 AI 的浏览器操作权限。
6. **规避陷阱**：了解常见安装失败原因、连接问题和安全注意事项。

---

## §2 原理分析

### 2.1 三层技术栈总览

`chrome-devtools-mcp` 并不是凭空发明了一套浏览器控制协议，而是站在三条成熟技术的肩上：

```
┌─────────────────────────────────────────────────┐
│         AI Coding Agent (Claude/Copilot)        │
│              ↑ MCP 协议 (JSON-RPC)              │
├─────────────────────────────────────────────────┤
│         MCP Server (chrome-devtools-mcp)        │
│  ┌─────────────────────────────────────────┐    │
│  │  工具函数层：navigate / screenshot / ... │    │
│  ├─────────────────────────────────────────┤    │
│  │  Puppeteer Core (Chrome 进程管理)        │    │
│  ├─────────────────────────────────────────┤    │
│  │  CDP (Chrome DevTools Protocol) 通信      │    │
│  └─────────────────────────────────────────┘    │
├─────────────────────────────────────────────────┤
│              Chrome Browser (独立进程)           │
│         通过 CDP WebSocket 接收命令               │
└─────────────────────────────────────────────────┘
```

- **CDP（Chrome DevTools Protocol）**：Chrome 内置的调试协议，通过 WebSocket 与 Chrome 通信，支持导航、网络拦截、控制台监听、性能追踪等能力。Puppeteer 本质上是对 CDP 的高级封装。
- **Puppeteer**：Google 维护的 Node.js 库，通过 CDP 控制无头（headless）或有头 Chrome 实例。它负责进程的启动/关闭、WebSocket 连接管理、自动等待 DOM 稳定等。
- **MCP（Model Context Protocol）**：Anthropic 提出的开放协议，用于在 AI Agent 与外部工具之间建立标准化的 JSON-RPC 通信通道。MCP Server 暴露一组"工具函数"，AI Agent 通过自然语言调用这些函数。

### 2.2 MCP 协议的工作机制

MCP 基于 JSON-RPC 2.0 规范，消息格式如下：

```json
// AI Agent 请求工具调用
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "navigate",
    "arguments": { "url": "https://example.com" }
  },
  "id": 1
}

// MCP Server 响应
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      { "type": "text", "text": "Navigated to https://example.com" }
    ]
  },
  "id": 1
}
```

MCP 的核心设计哲学是**工具即函数**：每个工具函数有明确的名称、参数 schema 和返回值格式。AI Agent 通过理解工具描述（tool description）自主决定调用哪个工具——不需要人工介入路由逻辑。

### 2.3 Puppeteer 如何桥接到 CDP

当你调用 `browser.newPage()` 时，Puppeteer 实际执行了以下操作：

1. **启动 Chrome**：Puppeteer 通过 `chrome-launcher` 启动一个 Chrome 进程，传入 `--remote-debugging-port=9222` 参数。
2. **建立 WebSocket**：Puppeteer 连接 Chrome 的 CDP WebSocket 端点（`ws://localhost:9222/devtools/page/<id>`），向该 WebSocket 发送 JSON 编码的 CDP 命令。
3. **命令封装**：`page.goto(url)` 对应的 CDP 命令是 `Page.navigate`，`page.screenshot()` 对应 `Page.captureScreenshot`。

`chrome-devtools-mcp` 的工具函数层，正是对 Puppeteer API 的再一次封装——将每个 Puppeteer 调用打包为一个 MCP 工具。

### 2.4 关键设计决策：自动等待机制

Puppeteer 区别于 raw CDP 的一个核心特性是**自动等待**（Auto-Waiting）。例如，`page.click(selector)` 不会立即发送点击命令，而是：

```
等待策略：
1. 等待 selector 对应的元素出现在 DOM 中
2. 等待元素可见（visibility: visible）
3. 等待元素可点击（无其他元素遮挡）
4. 触发 click
```

这对于 AI Agent 尤为重要——AI 不会写显式的 `sleep`，自动等待机制使 AI 的"自然语言动作"能够可靠地在页面上落地。

---

## §3 架构分析

### 3.1 项目结构

```
chrome-devtools-mcp/
├── src/
│   ├── index.ts              # MCP server 入口
│   ├── tools/                # 工具函数目录
│   │   ├── browser.ts        # 浏览器生命周期管理
│   │   ├── navigation.ts     # 导航相关
│   │   ├── screenshot.ts      # 截图
│   │   ├── console.ts         # 控制台监听
│   │   ├── network.ts         # 网络拦截
│   │   └── performance.ts     # 性能追踪
│   └── types.ts              # 共享类型定义
├── package.json
└── README.md
```

从架构上看，这是一个典型的**插件化工具函数注册**模式：

```
MCP Server
  ↓ 注册
tools/ 目录下的所有工具函数
  ↓ 调用
PuppeteerBrowser 实例（单例或按需创建）
  ↓ 执行
CDP → Chrome Browser
```

### 3.2 工具注册机制

每个工具函数通过 MCP 的 `setRequestHandler` 注册，典型模式如下：

```typescript
// 伪代码示例（基于 MCP SDK 惯用写法）
server.setRequestHandler("tools/call", async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case "navigate":
      return await handleNavigate(args.url);
    case "screenshot":
      return await handleScreenshot(args.fullPage);
    // ...
  }
});
```

这种模式的优势在于：新增工具只需要在 `tools/` 目录下新增文件，在 `index.ts` 中注册 case 分支即可，不需要改动 MCP 框架层。

### 3.3 浏览器生命周期管理

`chrome-devtools-mcp` 对浏览器的管理遵循**单例 + 按需启动**策略：

- **首次调用时启动**：当第一个工具函数需要浏览器时，Puppeteer 才启动 Chrome 进程。
- **空闲后关闭**：一段时间无操作后（可配置），Puppeteer 自动关闭 Chrome 进程，避免资源泄漏。
- **多标签支持**：通过 `browser.newPage()` 创建新标签页，每个标签页有独立的 CDP session。

另一篇旧稿补上了一个很实用的工程细节：如果多个 subagent 要并行盯不同标签页，`--experimentalPageIdRouting` 基本是必开的。打开后，工具响应会带回 `pageId`，后续调用可以显式路由到同一标签页；再配合 `--isolated` 给不同 MCP server 分配独立的 user-data-dir，多会话同时跑页面分析时就不容易互相踩状态。这部分不影响单人单页的基础用法，但对真正把它接进 agent 编排系统的团队很关键。

### 3.4 与其他方案的架构对比

| 维度 | chrome-devtools-mcp | Playwright (SDK) | agent-browser (CLI) |
|------|---------------------|-------------------|---------------------|
| **控制层** | MCP Server | Native SDK | CLI 进程 |
| **浏览器控制** | Puppeteer → CDP | Playwright 自己的 CDP wrapper | 独立二进制 |
| **AI 集成方式** | 工具函数注册到 MCP | 需要手写 SDK 调用 | 自然语言 CLI 对话 |
| **协议标准** | MCP（开放） | 无（各语言 SDK） | 无 |
| **适用场景** | AI Agent 深度集成 | 传统自动化测试 | Agent 快速交互 |

---

## §4 功能详解

### 4.1 工具函数一览

`chrome-devtools-mcp` 提供以下工具函数（基于 npm 包元数据与 README 功能列表）：

#### 浏览器管理

| 函数名 | 功能 | 关键参数 |
|--------|------|----------|
| `launch_browser` | 启动 Chrome 浏览器实例 | `headless`, `args`（启动参数） |
| `close_browser` | 关闭当前浏览器实例 | — |
| `new_page` | 创建新标签页 | — |
| `close_page` | 关闭指定标签页 | `page_id` |

#### 页面导航与交互

| 函数名 | 功能 | 关键参数 |
|--------|------|----------|
| `navigate` | 打开指定 URL | `url`, `wait_until`（加载策略） |
| `reload` | 刷新当前页面 | `wait_until` |
| `go_back` | 后退 | — |
| `go_forward` | 前进 | — |
| `evaluate` | 在页面上下文执行 JavaScript | `script`（JS 代码字符串） |
| `click` | 点击指定选择器元素 | `selector`, `button`（左/中/右） |
| `type` | 向输入框输入文本 | `selector`, `text` |
| `hover` | 鼠标悬停 | `selector` |
| `scroll` | 滚动页面 | `selector`（可选，滚动到元素） |

#### 截图与媒体

| 函数名 | 功能 | 关键参数 |
|--------|------|----------|
| `screenshot` | 页面截图 | `full_page`（是否截全页），返回 base64 编码图片 |
| `get_element_screenshot` | 截取指定元素的图片 | `selector` |

#### 网络监听

| 函数名 | 功能 | 关键参数 |
|--------|------|----------|
| `set_network_interception` | 开启网络请求拦截 | `patterns`（URL 过滤规则） |
| `get_requests` | 获取捕获的网络请求列表 | — |
| `get_response_body` | 获取指定请求的响应体 | `request_id` |
| `clear_requests` | 清空已捕获的请求列表 | — |

#### 控制台

| 函数名 | 功能 | 关键参数 |
|--------|------|----------|
| `enable_console` | 开启控制台消息监听 | — |
| `get_console_messages` | 获取捕获的控制台消息 | `level`（log/warn/error） |
| `console_messages_with_source_maps` | 获取含 Source Map 还原后的控制台消息 | — |

#### 性能分析

| 函数名 | 功能 | 关键参数 |
|--------|------|----------|
| `start_performance_trace` | 启动 Chrome Performance Trace | `trace_file_path` |
| `stop_performance_trace` | 停止追踪并输出 trace 文件 | — |

### 4.2 控制台与 Source Map 还原

这是 `chrome-devtools-mcp` 的亮点功能之一。生产环境的网页通常经过压缩、合并和混淆，控制台日志中的报错位置会被 Source Map 还原为原始源码位置。

```
Source Map 还原链路：
1. 控制台消息 → 原始文件 + 行号（来自 CDP）
2. 查询 .map 文件（如果可访问）
3. 还原为框架/库的原始源码位置
```

这意味着 AI Agent 可以在处理线上报错时，直接看到原始 TypeScript/React 源码位置，而不是压缩后的行号——大幅提升 AI 辅助调试的准确度。

### 4.3 网络拦截与 API Mock

通过 `set_network_interception`，AI Agent 可以：

- 捕获特定 URL 模式的请求和响应
- 查看 POST 请求体和响应体的详细内容
- 在 Agent 层面实现"读接口、验逻辑"的工作流，而不需要额外的抓包工具

### 4.4 Performance Trace 的价值

Chrome 的 Performance Trace 是 Chrome DevTools 中最强大的 profiling 工具。`chrome-devtools-mcp` 将其暴露为工具函数，AI Agent 可以在代码变更前后各做一次 trace，对比主线程耗时分布，客观量化性能差异。

---

## §5 使用说明

### 5.1 环境要求

| 依赖 | 最低版本 | 说明 |
|------|----------|------|
| Node.js | v20.19.0 | 必须支持 ES Module |
| Chrome 浏览器 | 最新稳定版 | 支持有头（headed）和无头（headless）模式 |
| npm / pnpm / yarn | 最新稳定版 | 用于安装依赖 |

### 5.2 安装步骤

**全局安装（CLI 使用）：**

```bash
npm install -g chrome-devtools-mcp
```

**项目本地安装（作为 MCP server 使用）：**

```bash
npm install chrome-devtools-mcp
# 或
pnpm add chrome-devtools-mcp
```

**验证安装：**

```bash
npx chrome-devtools-mcp --help
```

### 5.3 CLI 模式（不通过 MCP）

如果你的场景不需要 MCP 协议，可以直接通过 CLI 操作：

```bash
# 截图
npx chrome-devtools-mcp screenshot https://example.com --full-page -o example.png

# 导航并执行脚本
npx chrome-devtools-mcp evaluate "document.title" --url https://example.com

# 启动带自定义参数的 Chrome
npx chrome-devtools-mcp launch --headless false --args "--window-size=1920,1080"
```

### 5.4 MCP Server 模式（AI Agent 集成）

#### 5.4.1 配置为 MCP Server

在 MCP 配置文件中添加（路径因客户端而异）：

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["chrome-devtools-mcp"],
      "env": {}
    }
  }
}
```

#### 5.4.2 Claude Desktop 配置示例

macOS：`~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp"]
    }
  }
}
```

Linux：`~/.config/Claude/claude_desktop_config.json`

Windows：`%APPDATA%/Claude/claude_desktop_config.json`

修改配置后，重启 Claude Desktop 使配置生效。

#### 5.4.3 在对话中使用

配置成功后，你可以直接用自然语言驱动浏览器：

```
用户：帮我截一张 github.com 首页的图

AI Agent 调用工具：screenshot(url="https://github.com")
→ 返回 base64 编码的 PNG 图片

用户：这个页面加载时有哪些网络请求发了出去？

AI Agent 调用工具：
1. set_network_interception(patterns=["*"])
2. navigate(url="https://github.com")
3. get_requests()
→ 返回请求列表（URL、方法、状态码、耗时）

用户：控制台有什么报错吗？

AI Agent 调用工具：
1. enable_console()
2. navigate(url="https://github.com")
3. get_console_messages(level="error")
→ 返回错误级别消息列表，含 Source Map 还原后的位置
```

### 5.5 有头 vs 无头模式

```typescript
// 无头模式（默认，适合服务器/CI 环境）
npx chrome-devtools-mcp launch --headless

// 有头模式（可以看到浏览器窗口，便于调试）
npx chrome-devtools-mcp launch --headless false

// 有头模式 + 指定窗口大小
npx chrome-devtools-mcp launch --headless false --args "--window-size=1440,900"
```

---

## §6 开发扩展

### 6.1 扩展思路

`chrome-devtools-mcp` 的工具函数层设计得相当薄，扩展新工具的成本很低。常见的扩展方向包括：

1. **新增工具函数**：针对特定业务场景（如登录、表单填写、PDF 导出）封装新工具。
2. **自定义 CDP 调用**：访问 Puppeteer 尚未封装但 CDP 支持的底层能力。
3. **多浏览器支持**：除了 Chrome，扩展对 Firefox（WebDriver Bidi）或 Edge 的支持。

### 6.2 添加自定义工具函数示例

以下示例展示如何在 `chrome-devtools-mcp` 源码中添加一个新的 `export_pdf` 工具函数：

**Step 1：安装源码依赖**

```bash
git clone https://github.com/ChromeDevTools/chrome-devtools-mcp.git
cd chrome-devtools-mcp
npm install
```

**Step 2：在 `src/tools/` 下新增文件**

```typescript
// src/tools/pdf.ts
import { MCPTool } from "../types";

export const exportPdfTool: MCPTool = {
  name: "export_pdf",
  description: "将当前页面导出为 PDF 文件",
  inputSchema: {
    type: "object",
    properties: {
      path: {
        type: "string",
        description: "PDF 文件保存路径（绝对路径）",
      },
      printBackground: {
        type: "boolean",
        description: "是否打印背景颜色和图片",
        default: false,
      },
    },
    required: ["path"],
  },
  handler: async (args, context) => {
    const page = context.getCurrentPage();
    await page.pdf({
      path: args.path,
      printBackground: args.printBackground ?? false,
    });
    return {
      content: [{ type: "text", text: `PDF 已保存至 ${args.path}` }],
    };
  },
};
```

**Step 3：在 `src/index.ts` 中注册**

```typescript
import { exportPdfTool } from "./tools/pdf";

// 在工具注册区域添加
server.setRequestHandler("tools/call", async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    // ... 其他工具
    case "export_pdf":
      return await exportPdfTool.handler(args, context);
  }
});
```

**Step 4：构建并测试**

```bash
npm run build
npx chrome-devtools-mcp export_pdf --url https://example.com --path ./output.pdf
```

### 6.3 Puppeteer 未封装的 CDP 能力

Puppeteer 只封装了 CDP 的部分能力，CDP 本身有更多能力未暴露。以下列举一些可以通过扩展访问的 CDP 域：

| CDP 域 | 能力 | 场景 |
|--------|------|------|
| `DOMStorage` | 读写 LocalStorage / SessionStorage | 注入测试数据 |
| `ApplicationCache` | 查看应用缓存状态 | 调试 PWA |
| `CacheStorage` | 检查 Service Worker 缓存 | 缓存调试 |
| `ServiceWorker` | 列出/删除 Service Worker | SW 调试 |
| `Performance` | 获取原始性能指标 | 精细化性能分析 |
| `Memory` | 获取 JS 堆快照 | 内存泄漏排查 |

访问这些 CDP 域的底层方式：

```typescript
// 通过 Puppeteer 的 cdpSession 访问底层 CDP
const cdpSession = await page.createCDPSession();
await cdpSession.send("DOMStorage.enable");
const storage = await cdpSession.send("DOMStorage.getDOMStorageItems", {
  storageId: { securityOrigin: page.url(), isLocalStorage: true },
});
```

### 6.4 发布自定义分支

如果你希望在组织内部维护一个定制版：

```bash
# 在 forked 仓库中维护
git checkout -b feature/export-pdf
git add .
git commit -m "feat: add export_pdf tool"
git push origin feature/export-pdf
```

然后在 MCP 配置中指向你的分支：

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "github:your-org/chrome-devtools-mcp#feature/export-pdf"]
    }
  }
}
```

---

## §7 实践建议

### 7.1 安全实践

**⚠️ AI Agent + 浏览器 = 需要审慎的权限控制**

AI Agent 接收自然语言指令，这意味着恶意指令（如"访问 `file:///etc/passwd`"）可能被意外执行。以下是安全配置建议：

1. **网络隔离**：通过 `--args "--host-rules=MAP example.com 127.0.0.1"` 限制 AI 可访问的域名。
2. **禁止自动化下载**：默认配置下 Puppeteer 会自动下载文件，设置 `--args "--download-restrictions=3"` 禁止之。
3. **容器化运行**：在 Docker 容器中运行 Chrome，配合 seccomp 配置文件收紧系统调用。
4. **操作审计**：通过 `set_network_interception` 和 `enable_console` 记录 AI 所有浏览器操作，供人工审查。

```bash
# 推荐的安全启动参数（生产环境）
google-chrome \
  --headless \
  --no-sandbox \
  --disable-dev-shm-usage \
  --disable-gpu \
  --host-rules="MAP *.internal.corp 127.0.0.1" \
  --download-restrictions=3
```

### 7.2 性能实践

1. **复用浏览器实例**：不要在每次工具调用时都启动/关闭 Chrome，启动一次后保持运行。
2. **有头 vs 无头按需切换**：开发调试用有头模式，CI/生产环境用无头模式。
3. **限制截图分辨率**：全页截图在高分辨率显示器上可能产生数十 MB 的图片，设置合理的 `viewport`：

   ```typescript
   await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
   ```

4. **批量网络请求时使用拦截**：开启拦截后批量触发页面操作，最后统一 `get_requests()` 获取全部请求，避免逐个请求实时监听带来的开销。

### 7.3 AI Agent 集成实践建议

1. **工具描述要具体**：在给 AI 描述工具时，明确说明每个参数的含义和取值范围，否则 AI 可能在工具选择上犯错。
2. **错误处理**：当 `navigate` 超时或页面崩溃时，MCP server 应返回结构化错误，AI 才能写出有针对性的错误恢复逻辑。
3. **幂等性设计**：工具函数应尽量幂等（同样的输入重复调用结果一致），便于 AI 验证操作是否成功。
4. **组合使用示例**：为 AI 提供常见工作流的示例 prompt（Few-shot），帮助 AI 学习工具组合：

   ```
   示例：验证页面加载性能
   1. start_performance_trace()
   2. navigate(url="https://example.com")
   3. wait_for_network_idle()  # 如果有的话
   4. stop_performance_trace()
   ```

### 7.4 调试实践

**调试 MCP 通信**：启用 MCP 的 debug 日志级别：

```bash
DEBUG=mcp* npx chrome-devtools-mcp
```

**调试 Puppeteer**：使用 Puppeteer 的 `dumpio` 选项查看浏览器进程的原始 IO：

```typescript
const browser = await puppeteer.launch({
  dumpio: true,  // 将浏览器 stdout/stderr 导入 Node.js 进程
  headless: false,
});
```

**检查 Chrome 是否正常启动**：

```bash
# 手动检查 CDP 端口
curl http://localhost:9222/json
# 应返回 Chrome DevTools Protocol 的可用端点列表
```

---

## §8 FAQ

### Q1: 安装时报 `Error: Cannot find Chrome browser`，如何解决？

**原因**：系统未找到 Chrome 可执行文件路径。

**解决方案**：

```bash
# 方法1：手动指定 Chrome 路径
export PUPPETEER_EXECUTABLE_PATH=/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome

# 方法2：在 Docker 环境中安装无头 Chrome
apt-get install -y chromium-browser

# 方法3：让 Puppeteer 自动下载 Chromium
npx puppeteer browsers install chrome
```

### Q2: MCP Server 启动后 AI Agent 无法调用工具，如何排查？

排查路径：

```
1. 确认 MCP Server 进程在运行
   ps aux | grep chrome-devtools-mcp

2. 确认 MCP 配置文件格式正确（JSON 语法）
   cat ~/.config/Claude/claude_desktop_config.json | python -m json.tool

3. 确认 Node.js 版本 >= 20.19.0
   node --version

4. 用 MCP inspector 独立测试 server
   npx @modelcontextprotocol/inspector npx chrome-devtools-mcp
```

### Q3: 截图返回的是空图片或黑屏，是什么原因？

**可能原因**：

1. 页面尚未完全加载（JavaScript 渲染的内容未执行完毕）
2. 使用了 headless=new 模式（新无头模式的渲染机制不同）
3. 页面使用了 WebGL，黑头模式下的渲染有限制

**解决方案**：

```typescript
// 方案1：显式等待页面完全加载
await page.goto(url, { waitUntil: "networkidle0" });

// 方案2：增加截图前的等待
await page.waitForTimeout(2000);
await page.screenshot();

// 方案3：使用有头模式截图（headless: false）
```

### Q4: `get_console_messages` 返回空列表，但页面明显有控制台输出？

**原因**：`enable_console` 必须在页面导航**之前**调用，否则会漏掉页面加载阶段的早期日志。

**正确顺序**：

```typescript
// 1. 先开启监听（此时页面还未导航）
await page.evaluate(() => {
  // Puppeteer 的 console 监听器需要在页面创建时就注册
});
await page.goto(url);  // 2. 再导航
const messages = await page.evaluate(() => window.__consoleMessages);  // 3. 最后获取
```

### Q5: MCP 和直接使用 Puppeteer SDK 相比，优势在哪里？

| 对比维度 | 直接使用 Puppeteer | chrome-devtools-mcp |
|----------|-------------------|---------------------|
| **集成成本** | 高（需要手写调用代码） | 低（只需配置 JSON） |
| **AI 自主性** | 弱（需要人类路由工具调用） | 强（AI 直接通过 MCP 协议调用） |
| **工具发现** | 手动文档查阅 | AI 通过 tool description 自主发现 |
| **多 Agent 共享** | 需要额外服务层 | MCP 原生支持多客户端 |

### Q6: 可以同时控制多个浏览器实例吗？

技术上可以，但 `chrome-devtools-mcp` 默认配置是单浏览器实例。多实例需要修改源码，在 `BrowserManager` 中管理多个 `PuppeteerBrowser` 实例，并为每个实例分配独立的 CDP 端口：

```typescript
// 伪代码：多浏览器管理
const browsers = new Map<string, Browser>();
browsers.set("browser-1", await puppeteer.launch({ port: 9222 }));
browsers.set("browser-2", await puppeteer.launch({ port: 9223 }));
```

### Q7: `evaluate` 函数执行恶意脚本怎么办？

**建议的安全措施**：

1. **沙箱化 Chrome**：启动时加 `--no-sandbox --disable-setuid-sandbox`（容器环境必需，但也缩小了攻击面）。
2. **禁用 JavaScript**（特定场景）：`--disable-javascript` 可以防止 AI 通过 JS 执行恶意操作。
3. **内容安全策略（CSP）**：对于不受信的页面，启用严格的 CSP 限制脚本执行。
4. **限制文件访问**：`--restrict-filespaces` 可限制浏览器访问本地文件系统。

### Q8: 如何让 AI 只在特定域名下操作？

在 MCP 工具函数层做域名校验：

```typescript
// 在 evaluate / navigate 等工具中添加域名白名单检查
const ALLOWED_HOSTS = ["github.com", "example.com"];
const urlObj = new URL(args.url);

if (!ALLOWED_HOSTS.includes(urlObj.hostname)) {
  throw new Error(`域名 ${urlObj.hostname} 不在白名单中`);
}
```

### Q9: Performance Trace 文件很大，如何处理？

Chrome Performance Trace（`.chrometrace` 格式）可能从几十 MB 到数 GB。可以：

1. **限制 Trace 时长**：`start_performance_trace` 后，在合理时间内调用 `stop_performance_trace`，避免无限增长。
2. **只追踪关键阶段**：在可疑代码段前后启动/停止 Trace，而不是追踪整个页面生命周期。
3. **使用流式写入**：`traceFile` 参数使用流式写入器，避免内存溢出。

---

## 附录

### A. 相关资源

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/ChromeDevTools/chrome-devtools-mcp |
| npm 包 | https://www.npmjs.com/package/chrome-devtools-mcp |
| MCP 协议规范 | https://modelcontextprotocol.io |
| Puppeteer 文档 | https://pptr.dev |
| Chrome DevTools Protocol | https://chromedevtools.github.io/devtools-protocol/ |

### B. 参考项目对比

| 项目 | 协议层 | 底层引擎 | AI 友好度 | 维护状态 |
|------|--------|----------|-----------|----------|
| chrome-devtools-mcp | MCP | Puppeteer | ⭐⭐⭐⭐⭐ | 活跃 |
| playwright (传统) | 无 | Playwright own | ⭐⭐ | 活跃 |
| puppeteer (直接) | 无 | Puppeteer | ⭐⭐ | 活跃 |
| agent-browser | CLI | 独立 binary | ⭐⭐⭐ | 活跃 |

---

*本文档由 钳岳星君 🦞 整理，基于 chrome-devtools-mcp 公开信息编写。如有疏漏，欢迎指正。*
