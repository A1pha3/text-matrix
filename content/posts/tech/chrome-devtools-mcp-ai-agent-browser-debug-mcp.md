---
title: "chrome-devtools-mcp：把 Chrome DevTools 完整能力切给 Coding Agent"
date: "2026-07-09T02:55:00+08:00"
slug: "chrome-devtools-mcp-ai-agent-browser-debug-mcp"
description: "chrome-devtools-mcp 是 Chrome DevTools 团队官方出的 MCP server，把 Performance、Network、Memory、Debug 等真实 DevTools 能力暴露给 Claude/Cursor/Copilot 等 Coding Agent。本文拆解 26+ 工具分组、性能 trace 流程、与 Puppeteer 直连方案的取舍。"
draft: false
categories: ["技术笔记"]
tags: ["MCP", "Chrome DevTools", "Chrome", "调试自动化", "AI Agent"]
---

# chrome-devtools-mcp：把 Chrome DevTools 完整能力切给 Coding Agent

## 一句话核心判断

chrome-devtools-mcp（仓库 `ChromeDevTools/chrome-devtools-mcp`）做的事可以一句话总结：让 Coding Agent 像一个熟练的前端工程师一样使用 Chrome DevTools。它把 DevTools 的 26+ 工具拆成"输入自动化 / 导航 / 仿真 / 性能 / 网络 / 调试 / 内存 / 扩展"等组，按 MCP 协议暴露给 Claude Code、Cursor、Copilot 等客户端。和"用 Puppeteer 给 Agent 写一层薄薄 wrapper"最大的差别是——性能 trace、堆快照分析、Lighthouse 审计这些 DevTools 的"高级货"，MCP 协议一次绑定就能调用。

如果只是想"让 Agent 点按钮、填表单、抓截图"，可以选轻量方案；如果要"让 Agent 看 performance trace、对比 heap snapshot、抓 source-mapped 错误"，chrome-devtools-mcp 是当下最完整的官方路径。

## 系统地图：三层 + 工具分组

整个项目按"协议层 / 服务端 / 客户端"三层落地，下面只画到 MCP server 这一层（客户端由各家 Agent 实现，不属于该项目本身）：

```
┌─────────────────────────────────────────────────────────────────┐
│  Client 层：Claude Code / Cursor / Copilot / Codex / Antigravity │
│  （各家 MCP client 不在仓库内）                                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ MCP（JSON-RPC over stdio / streamable HTTP）
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  chrome-devtools-mcp server（TypeScript，Node.js LTS）           │
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐ │
│  │ Input auto │  │ Navigation │  │ Emulation  │  │ Performance│ │
│  │   10 tools │  │   6 tools  │  │   2 tools  │  │   3 tools  │ │
│  ├────────────┤  ├────────────┤  ├────────────┤  ├────────────┤ │
│  │ Network    │  │ Debugging  │  │  Memory    │  │ Extensions │ │
│  │   2 tools  │  │   8 tools  │  │  11 tools  │  │   5 tools  │ │
│  ├────────────┤  ├────────────┤  ┌────────────┐                │
│  │ Third-party│  │  WebMCP    │  │   CLI      │   —— 双形态    │
│  │   2 tools  │  │   2 tools  │  │  slim/full │                │
│  └────────────┘  └────────────┘  └────────────┘                │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Chrome DevTools Protocol（CDP）
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Chrome（Stable / Extended Stable / Chrome for Testing）          │
└─────────────────────────────────────────────────────────────────┘
```

CLI 形态（`--slim`、`--headless`）让"不想跑全套 MCP server"的用户直接以子进程方式调用，运维路径短很多。

## 核心判断：为什么不是又一个"浏览器自动化 wrapper"

市面上能给 Agent 操作浏览器的方案不少，但多数只解决"自动化点击"。chrome-devtools-mcp 的差异化集中在三处：

1. **官方背书的协议栈**：服务端通过 Chrome DevTools Protocol 跟 Chrome 通信，所有高级功能（Performance、Memory、Lighthouse、Extension）都暴露出来。
2. **MCP 协议一次绑定全部工具**：`npx -y chrome-devtools-mcp@latest` 一行就能把上述 26+ 个工具同时注册到 MCP client。
3. **保持 DevTools 的可观测性**：性能 trace、堆快照、网络请求详情这些"看起来 Agent 用不上"的信息，对调试真实应用极其关键。

它的关键限制在 README 里写得很清楚：**官方只支持 Google Chrome 与 Chrome for Testing，其他 Chromium 派生浏览器"may work"但不被保证**。这意味着项目是绑在 Chrome 上的，不要把它当成"通用浏览器协议"。

## 工具分组与典型调用

把 README 里"工具自动生成段"按目的重新分类，便于按场景选工具：

### 1. 输入自动化（10 tools）

点、拖、填表单、悬停、按键、上传、点击指定坐标——这些是"动浏览器"的基本动作。`fill_form`、`click_at`、`upload_file` 比单纯的 `click` 更贴合现代 web 表单的复杂性。

### 2. 导航与多页管理（6 tools）

`navigate_page`、`new_page`、`list_pages`、`select_page`、`close_page`、`wait_for` 是多 tab 调试的核心。Agent 在"打开 A 页面、登录、切到 B 页面、操作 C"这种任务上需要明确的"页"对象，模型才能精准选择。

### 3. 仿真与多设备（2 tools）

`emulate`、`resize_page` 主要配合 Lighthouse 跑移动端性能、对比不同 viewport。

### 4. 性能分析（3 tools）

这是 chrome-devtools-mcp 最"上强度"的工具组：

- `performance_start_trace`：启动 Chrome 内置的 trace recorder。
- `performance_stop_trace`：停掉 trace 并落盘。
- `performance_analyze_insight`：把 trace 交给 DevTools 处理，自动给出 Insights（关键耗时、卡顿点、长任务）。

下面是性能 trace 的典型调用序列：

```
performance_start_trace  → 跑业务场景
  → performance_stop_trace
    → performance_analyze_insight（自动汇总瓶颈）
```

这跟过去 Puppeteer + trace 手工分析的差异是：**Agent 能直接调用底层的 Insights API**，不再要维护一份手工 trace 解析脚本。

### 5. 网络（2 tools）

`list_network_requests`、`get_network_request` 提供每个请求的 method/url/status/latency。配合 Debug 工具组的 source-mapped console 错误，"接口 500 + 控制台具体报错"一抓一个准。

### 6. 调试（8 tools）

- `evaluate_script`：在浏览器上下文跑任意 JS。
- `list_console_messages` / `get_console_message`：拿 console 日志，自动做 source map 还原。
- `take_screenshot` / `take_snapshot`：DOM 快照 + 视觉截图（前者适合 Agent 看结构，后者适合人眼复核）。
- `lighthouse_audit`：一次性跑性能/可访问性/SEO 审计并拿到结构化结果。
- `screencast_start` / `screencast_stop`：流式把页面截屏用于"观察 Agent 行为回放"。

### 7. 内存（11 tools）

`take_heapsnapshot`、`get_heapsnapshot_class_nodes`、`compare_heapsnapshots` 这样的工具非常罕见出现在通用 MCP server 里——它让你**直接对两份堆快照做 diff**，这是排查内存泄漏最锋利的工具。`get_heapsnapshot_retaining_paths` 可以告诉你"某个对象为什么没法被 GC"，对于大型 SPA 应用价值极高。

### 8. 扩展与第三方（7 tools）

`install_extension`、`list_extensions`、`reload_extension`、`trigger_extension_action` 让 Agent 可以管理已安装的扩展（典型场景：测试某个生产扩展是否被 update 修复 bug）。

Third-party + WebMCP 工具组覆盖两类"浏览器内部协议"：

- 第三方工具：`execute_3p_developer_tool`
- WebMCP（浏览器内 MCP）：`execute_webmcp_tool` / `list_webmcp_tools`——这条是值得关注的：当一个网页本身实现了 WebMCP，Agent 可以直接调用页面暴露的工具，不必走 DOM。

## 隐私与遥测：哪些数据被发走了

README 在 Disclaimers / Usage statistics 段写了几个常见被忽视的关键点：

- **默认开 usage statistics**：Google 会收集工具调用成功率、延迟、环境信息。要关掉用 `--no-usage-statistics` 或设置环境变量 `CHROME_DEVTOOLS_MCP_NO_USAGE_STATISTICS`。
- **CI 环境会自动关**：`CI` 环境变量存在时自动停用统计。
- **Performance 工具可能调用 CrUX API**：拿真实用户数据做对比，能用 `--no-performance-crux` 关。
- **Update check 默认开**：定期查 npm registry 通知有新版，能 `CHROME_DEVTOOLS_MCP_NO_UPDATE_CHECKS=1` 关掉。

对这些遥测不放心的话，强烈建议在 CI、个人开发机、涉及敏感数据的场景里把三种默认开启的统计都关一遍。

## 接入方式

最小可用配置（任意 MCP 客户端都能用）：

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

如果只需要"基本浏览"功能，用 slim 模式：

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--slim", "--headless"]
    }
  }
}
```

各客户端对应的安装路径：

- Claude Code：`claude mcp add chrome-devtools -- npx chrome-devtools-mcp@latest` 或 `/plugin marketplace add ChromeDevTools/chrome-devtools-mcp`
- VS Code：`code --add-mcp '{"name":"io.github.ChromeDevTools/chrome-devtools-mcp","command":"npx","args":["-y","chrome-devtools-mcp"],"env":{}}'`
- Cursor / Copilot / Codex：配置文档各自说明，核心字段一致

## 关键设计取舍

读完代码与 README 后几个工程启示：

- **MCP over stdio + WebSocket 双传输**：兼容 MCP client（stdio）和 IDE 内置 Chrome（WebSocket 自定义 header）。这种"双传输"对工具在不同编辑器之间的复用非常关键。
- **Concurrent sessions**：MCP server 可以在同一 Chrome 实例上跑多个独立调试 session，互不干扰——这给多 Agent 并行调试铺平了路。
- **User data directory 显式可控**：agent 可以在 `--user-data-dir` 注入指定配置，意味着能"接管理用户的真实登录态"或"用全新临时 profile 跑测试"。
- **Android 调试支持**：通过 `chrome://inspect` 暴露的远程调试端口进行 Android 设备调试——这是文档里的进阶用法，CI 跑端到端时非常有用。

## 适用边界

**适合**：

- Coding Agent 想做"修完代码立刻验证 UI/性能"——这是首选
- 给前端团队搭"自动化页面巡检、性能监控代理"——开箱即用
- 跑性能/可访问性审计（Lighthouse）+ 长任务跟踪
- 用 heap snapshot diff 排查内存泄漏

**不太适合**：

- 纯后端 / API-only 场景——直接打 HTTP 更快
- 跨浏览器兼容性测试——只支持 Chrome
- 想完全脱离 Chrome 生态的项目——项目的所有能力都绑在 Chrome DevTools 上

## 一句话总结

chrome-devtools-mcp 把"前端调试"这件事从"必须人来"提到"Agent 直接用"，核心价值是 DevTools 的高级能力（Performance / Memory / Lighthouse / Extension）一次绑定全部注册。如果工程上有给 Coding Agent 装真实调试能力的需求，这是当前最稳的官方路径。

## 参考链接

- 仓库：<https://github.com/ChromeDevTools/chrome-devtools-mcp>
- npm 包：`chrome-devtools-mcp`
- 协议：Model Context Protocol（MCP，stdio / streamable HTTP）
- 仅支持：Google Chrome / Chrome for Testing
- License：Apache-2.0（README 顶部约定）
