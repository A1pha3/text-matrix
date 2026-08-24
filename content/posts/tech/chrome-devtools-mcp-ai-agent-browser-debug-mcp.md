---
title: "chrome-devtools-mcp：把 Chrome DevTools 完整能力切给 Coding Agent"
date: "2026-07-09T02:55:00+08:00"
slug: "chrome-devtools-mcp-ai-agent-browser-debug-mcp"
github_repo: "ChromeDevTools/chrome-devtools-mcp"
description: "chrome-devtools-mcp 是 Chrome DevTools 团队官方出的 MCP server 与 CLI，把 Performance、Network、Memory、Debug 等真实 DevTools 能力暴露给 Claude/Cursor/Copilot 等 Coding Agent。本文拆解 53 个工具分组、性能 trace 流程、与 Puppeteer 直连方案的取舍。"
draft: false
categories: ["技术笔记"]
tags: ["MCP", "Chrome DevTools", "AI Agent"]
---

# chrome-devtools-mcp：把 Chrome DevTools 完整能力切给 Coding Agent

## 一句话核心判断

chrome-devtools-mcp（仓库 `ChromeDevTools/chrome-devtools-mcp`）做的事情可以一句话总结：让 Coding Agent 像一个熟练的前端工程师一样使用 Chrome DevTools。它把 DevTools 的能力拆成多个工具组，按 MCP 协议暴露给 Claude Code、Cursor、Copilot 等客户端，工具总数达到 53 个。和"用 Puppeteer 给 Agent 写一层薄薄 wrapper"最大的差别在于——性能 trace、堆快照分析、Lighthouse 审计这些 DevTools 的高级能力，MCP 协议一次绑定就能调用。

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
│  │   2 tools  │  │   8 tools  │  │  13 tools  │  │   5 tools  │ │
│  ├────────────┤  ├────────────┤  ┌────────────┐                │
│  │ Third-party│  │  WebMCP    │  │   CLI      │  ── 作为服务    │
│  │   2 tools  │  │   2 tools  │  │  （实验性） │  端的另一种形态 │
│  └────────────┘  └────────────┘  └────────────┘                │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Chrome DevTools Protocol（CDP）
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Chrome（Stable / Extended Stable / Chrome for Testing）          │
└─────────────────────────────────────────────────────────────────┘
```

这里的 `--slim`、`--headless` 是 MCP server 的启动参数，不是 CLI 的形态区分。slim 模式裁剪掉大部分工具、只留基础浏览能力；headless 让 Chrome 无头运行。项目另外提供一个实验性的独立 CLI（`chrome-devtools` 命令），用于不依赖 MCP 客户端、直接在终端操作浏览器（详见下文"CLI 直连"一节）。

## 核心判断：为什么不是又一个"浏览器自动化 wrapper"

市面上能给 Agent 操作浏览器的方案不少，但多数只解决"自动化点击"。chrome-devtools-mcp 的差异化集中在三处：

1. **官方背书的协议栈**：服务端通过 Chrome DevTools Protocol 跟 Chrome 通信，所有高级功能（Performance、Memory、Lighthouse、Extension）都暴露出来。
2. **MCP 协议一次绑定全部工具**：`npx -y chrome-devtools-mcp@latest` 一行就能把上述 53 个工具同时注册到 MCP client。
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

### 7. 内存（13 tools）

这一组是 chrome-devtools-mcp 最独特的地方。`take_heapsnapshot`、`get_heapsnapshot_class_nodes`、`compare_heapsnapshots`、`get_heapsnapshot_retaining_paths` 这类工具极少出现在通用 MCP server 里——它允许你**直接对两份堆快照做 diff**，还能追溯"某个对象为什么没法被 GC"的 retaining path。排查大型 SPA 的内存泄漏时，这比人肉在 DevTools 里点要可靠得多。

### 8. 扩展 / 第三方 / WebMCP（共 9 tools）

`install_extension`、`list_extensions`、`reload_extension`、`trigger_extension_action`、`uninstall_extension` 让 Agent 可以管理已安装的扩展（典型场景：测试某个生产扩展是否被 update 修复了 bug）。

在扩展之外，还有两组与浏览器内部协议相关的工具：

- 第三方工具（2 个）：`execute_3p_developer_tool` / `list_3p_developer_tools`
- WebMCP（浏览器内 MCP，2 个）：`execute_webmcp_tool` / `list_webmcp_tools`——这条值得关注：当一个网页本身实现了 WebMCP，Agent 可以直接调用页面暴露的工具，不必走 DOM。

## 隐私与遥测：哪些数据被发走了

README 在 Disclaimers 和 Usage statistics 两节写下几个容易被忽略的点：

- **usage statistics 默认开**：Google 会收集工具调用成功率、延迟、环境信息。关掉用 `--no-usage-statistics`，或设置环境变量 `CHROME_DEVTOOLS_MCP_NO_USAGE_STATISTICS`。
- **CI 环境会自动关**：`CI` 环境变量存在时自动停用统计。
- **Performance 工具可能调用 CrUX API**：用于拿真实用户数据做对比，能用 `--no-performance-crux` 关掉。
- **Update check 默认开**：定期查 npm registry 通知有新版，可用 `CHROME_DEVTOOLS_MCP_NO_UPDATE_CHECKS=1` 关闭。

在 CI、个人开发机、涉及敏感数据的场景里，建议把这三项默认开启的数据行为都关一遍再跑。

## 接入方式

前置要求：Node.js 的 LTS 版本（`node -v` 验证）、npm、当前稳定版或更新版本的 Chrome。注意 MCP server 会在客户端第一次调用需要浏览器的工具时才自动拉起 Chrome，连接上去本身不会启动浏览器。

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

装完后可以用官方给的"第一句话"验证是否打通——让客户端对 `https://developers.chrome.com` 跑一次性能检查，如果客户端打开浏览器并录下 performance trace，说明链路正常。

各客户端对应的安装路径：

- Claude Code：`claude mcp add chrome-devtools -- npx chrome-devtools-mcp@latest`；或装成插件（MCP + Skills 一起装）`/plugin marketplace add ChromeDevTools/chrome-devtools-mcp`，再 `/plugin install chrome-devtools-mcp@chrome-devtools-plugins`
- VS Code / Copilot：推荐以插件方式安装（把 MCP server 和 skills 一起打包，装完就能用）；也可以手动加，macOS/Linux 命令是 `code --add-mcp '{"name":"io.github.ChromeDevTools/chrome-devtools-mcp","command":"npx","args":["-y","chrome-devtools-mcp"],"env":{}}'`
- Codex：`codex mcp add chrome-devtools -- npx chrome-devtools-mcp@latest`
- Cursor、Gemini CLI、JetBrains 等：在各自 MCP 配置里填同一段最小配置即可，核心字段一致，官方 README 有逐家说明

> **注意**：MCP server 会把当前 Chrome 实例里的内容暴露给 MCP 客户端，客户端能读取、调试、修改浏览器里的任何数据。不要在调试时把不想让客户端看到的敏感或个人信息留在页面里。

如果不想跑 MCP、只想在终端里直接操作浏览器，可以用包自带的实验性 CLI：全局装一次 `npm i -g chrome-devtools-mcp`，就有 `chrome-devtools` 命令，`status` 检查是否装好，`navigate_page`、`take_screenshot`、`lighthouse_audit` 等直接在终端跑，`stop` 退出后台守护进程。

## 关键设计取舍

读完代码与 README 后几个工程启示：

- **官方选择 stdio 走 MCP，连接方式可指定**：默认由 `npx` 拉起 MCP server，通过标准输入/输出和客户端通信；也可以传 `--browser-url=http://127.0.0.1:9222` 让 server 连到已经跑在远程调试端口的 Chrome（比如 IDE 内置浏览器或独立的 Chrome 实例）。这种解耦让工具在不同编辑器之间复用。
- **隔离与持久化的取舍**：默认会以独立 profile 启动一个隔离的浏览器实例；需要接真实登录态或跑场景复用时，用 user-data-dir 参数（CLI 里写作 `--userDataDir`）指定一个用户数据目录，登录态能跨会话保留。headless（无头）模式在 CLI 里默认开启。
- **Experimental CLI**：内置 CLI 通过 Unix socket（macOS/Linux）或命名管道（Windows）连一个后台 `chrome-devtools-mcp` daemon，同一个后台实例被多次命令复用，页面、cookie 这些状态得以保留；`start`、`stop`、`status` 手动控制生命周期。

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

## 最后说几句

chrome-devtools-mcp 的价值不在"多一个能点按钮的 Agent"，而在把 DevTools 里最吃人力的几类工作——性能 trace、内存泄漏排查、Lighthouse 审计——一并变成 agent 可调用的工具。它把前端调试这件事从"必须人来"推到"Agent 直接动手"。如果工程上确实要给 Coding Agent 装一套真实可用的浏览器调试能力，这是目前最稳的官方路径。

## 参考链接

- 仓库：<https://github.com/ChromeDevTools/chrome-devtools-mcp>
- 工具参考（完整 53 个工具说明）：<https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/tool-reference.md>
- CLI 说明：<https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/cli.md>
- npm 包：`chrome-devtools-mcp`
- 协议：Model Context Protocol（MCP，默认 stdio）
- 仅支持：Google Chrome / Chrome for Testing
- License：Apache-2.0
- 数据收集说明：Google Privacy Policy《[Privacy](https://policies.google.com/privacy)》
