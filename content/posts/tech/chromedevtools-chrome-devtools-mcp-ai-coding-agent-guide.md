---
title: "chrome-devtools-mcp：把 Chrome DevTools 装进 AI 编码代理"
date: "2026-07-02T21:08:42+08:00"
lastmod: "2026-09-30T10:30:00+08:00"
draft: false
categories: ["技术笔记"]
tags: ["MCP", "Chrome DevTools", "AI Agent", "Puppeteer", "性能分析"]
description: "chrome-devtools-mcp 把 Chrome DevTools 能力通过 MCP 暴露给 AI 编程代理，以语义摘要替代 trace JSON。本文拆解工具分层、连接模式与安全边界。"
author: text-matrix
slug: chromedevtools-chrome-devtools-mcp-ai-coding-agent-guide

---

# chrome-devtools-mcp：把 Chrome DevTools 装进 AI 编码代理

`ChromeDevTools/chrome-devtools-mcp` 是 Chrome DevTools 官方团队维护的 MCP（Model Context Protocol）服务器，让 Claude、Cursor、Copilot、Antigravity、Codex、Gemini CLI 这类编码代理直接驱动一个真实的 Chrome 实例——自动化、调试、性能分析都能做，而不只是拿到截图和 console log。截至 2026-09-30，仓库 52,746 Stars，最新版 v1.10.1（2026-09-23）；从 5 月 18 日 v1.0.0 算起，四个月发了 14 个版本。

它跟 Puppeteer / Playwright 的差异不在"能不能自动化浏览器"，在返回值的形态。Puppeteer 把原始数据交给调用方，chrome-devtools-mcp 先把数据消化成代理能直接用的结论：

- **拿 LCP / CLS / FCP 数字**，而不是 50k 行 trace JSON
- **拿"DOM 节点 + 无障碍树 + 关键属性"快照**，而不是整页 HTML
- **拿"网络请求 + 关键 headers + 状态码"**，而不是原始 HAR
- **拿"heap 增长分类 + dominator 链"**，而不是 .heapsnapshot 文件本身

重型资产（截图、trace、视频）一律返回文件路径或 URI，不回流原始字节。代理的上下文窗口因此只装结论，不装原始数据——这条贯穿整个仓库的设计取舍，是它与 Puppeteer 的本质差异。

## 学习目标

读完本文，你应该能够：

- 根据调试场景在"内置 Chrome 实例"与"连接现有 Chrome"两条启动路径之间做选择，并知道什么时候必须用后者。
- 用 slim 模式与类别开关（`--category*`）控制 59 个工具对上下文窗口的占用。
- 跟着任务流案例，用 `performance_*` 工具完成一次 LCP 劣化的端到端诊断。
- 判断哪些场景适合采用、哪些场景（高敏数据、纯后端）应该避开，以及上线前该打开哪些安全开关。

## 目录

- [系统地图：59 个工具按能力切片](#系统地图：59-个工具按能力切片)
- [双模式启动：内置 Chrome 还是连接现有 Chrome](#双模式启动：内置-chrome-还是连接现有-chrome)
  - [路径 A：内置 Chrome 实例（默认）](#路径-a：内置-chrome-实例（默认）)
  - [路径 B：连接现有 Chrome（sandboxed / 共享登录态）](#路径-b：连接现有-chrome（sandboxed-共享登录态）)
- [任务流案例：性能问题的端到端诊断](#任务流案例：性能问题的端到端诊断)
- [设计原则（来自 `docs/design-principles.md`）](#设计原则（来自-docsdesign-principlesmd）)
- [安全边界与隐私开关](#安全边界与隐私开关)
- [版本节奏：四个月 14 个版本](#版本节奏：四个月-14-个版本)
- [skills 与 Agent Plugins：从工具到技能包](#skills-与-agent-plugins：从工具到技能包)
- [适用边界与采用顺序](#适用边界与采用顺序)
  - [适合采用](#适合采用)
  - [不适合采用](#不适合采用)
  - [推荐的接入顺序](#推荐的接入顺序)
- [仓库元信息](#仓库元信息)

## 系统地图：59 个工具按能力切片

v1.10.x 的 tool-reference 注册了 59 个工具，分 11 个类别。默认只激活其中约 30 个——Memory 的 13 个重分析工具、Extensions / Third-party / WebMCP / PWA 四个类别、坐标点击和 screencast 都靠 flag 按需打开：

| 类别 | 工具数 | 默认激活 | 说明与代表工具 |
|---|---:|---:|---|
| **Input automation** | 10 | 9 | `click` / `fill` / `fill_form` / `drag` / `press_key` / `type_text` / `upload_file` / `hover` / `handle_dialog`；`click_at` 坐标点击需 `--experimentalVision`（配视觉模型） |
| **Navigation automation** | 6 | 6 | `navigate_page` / `new_page` / `list_pages` / `close_page` / `select_page` / `wait_for` |
| **Emulation** | 2 | 2 | `emulate`（设备、CPU 节流、网络条件）/ `resize_page` |
| **Performance** | 3 | 3 | `performance_start_trace` / `performance_stop_trace` / `performance_analyze_insight` |
| **Network** | 2 | 2 | `list_network_requests` / `get_network_request` |
| **Debugging** | 9 | 7 | `evaluate_script` / `take_snapshot`（DOM + 无障碍树）/ `take_screenshot` / `list_console_messages`（v1.8.0 起可带源映射堆栈）/ `get_console_message` / `get_css_styles`（v1.10.0 新增）/ `lighthouse_audit`；`screencast_start/stop` 需 `--experimentalScreencast` + ffmpeg |
| **Memory** | 14 | 1 | `take_heapsnapshot` 默认可用；其余 13 个（快照对比、dominator 链、retainer 路径、重复字符串、对象级下钻等）需 `--memoryDebugging` |
| **Extensions** | 5 | 0 | 安装/重载/卸载扩展，需 `--categoryExtensions`，仅支持 pipe 连接 |
| **Third-party** | 2 | 0 | 页面自暴露的 developer tool，需 `--categoryExperimentalThirdParty` |
| **WebMCP** | 2 | 0 | 需 `--categoryExperimentalWebmcp`，要求 Chrome 150+ 并加 `--enable-features=WebMCP` |
| **Progressive Web Apps** | 4 | 0 | v1.8.0 新增：`install_pwa` / `launch_pwa` / `uninstall_pwa` / `get_os_app_state`，需 `--categoryPwa`，仅支持 pipe 连接 |

slim 模式只保留三个工具，名字也做了简化：`navigate` / `evaluate` / `screenshot`（对应完整模式的 `navigate_page` / `evaluate_script` / `take_screenshot`）。它适合"打开页面看一眼"的轻量场景，也适合用来先验证 MCP 配置和权限链路，避免一次性把几十条工具描述塞进上下文窗口。

类别开关可以直接控制这批工具的去留：

```bash
npx -y chrome-devtools-mcp@latest \
  --memoryDebugging \
  --categoryExtensions=true
```

Input、Navigation、Emulation、Performance、Network、Debugging、Memory（基础部分）默认全开；Extensions、Third-party、WebMCP、PWA 四个类别默认关闭。每个类别的工具描述都会进上下文窗口，按需打开比全开更省 token。

## 双模式启动：内置 Chrome 还是连接现有 Chrome

跟 Puppeteer 不同，chrome-devtools-mcp 把"启动浏览器"这件事做成了两条互斥路径：

### 路径 A：内置 Chrome 实例（默认）

第一次调用需要浏览器的工具时，服务器会自动启动一个 Chrome stable 通道实例，使用专用 user-data-dir（位于 `$HOME/.cache/chrome-devtools-mcp/chrome-profile`，非 stable 通道会追加通道后缀）。

默认 user-data-dir **不会在每次运行后清理**，跨实例共享。如果想完全隔离：

```bash
npx -y chrome-devtools-mcp@latest --isolated
```

`--isolated` 会创建一个临时 user-data-dir，浏览器关闭后自动清理。

### 路径 B：连接现有 Chrome（sandboxed / 共享登录态）

某些场景默认启动不适用：

- 想在手工测试和代理驱动测试之间保留同一个应用状态（同一窗口、同一登录态、同一表单数据）
- 代理需要登录，但 WebDriver 控制下的 Chrome 被某些账号风控拒绝
- LLM 跑在沙箱里，但想让浏览器跑在沙箱外（让用户能看到真实渲染）

这种情况下要先启动带远程调试端口的 Chrome，再用 `--browser-url` 或 `--ws-endpoint` 连过去：

```bash
# 先开 Chrome（macOS）
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-profile-stable

# 再启动 MCP server
npx -y chrome-devtools-mcp@latest --browser-url=http://127.0.0.1:9222
```

WebSocket 连接还可以带自定义头：`--ws-endpoint` 配合 `--ws-headers`（例如传 `Authorization`），WebSocket 地址可从 `http://127.0.0.1:9222/json/version` 的 `webSocketDebuggerUrl` 字段拿到。

Chrome 144+ 还提供了 `--autoConnect` 模式：通过 `chrome://inspect/#remote-debugging` 启用远程调试，配置 `--autoConnect` 后 MCP server 会自动定位当前用户配置的 default profile 并发起连接，弹出对话框让用户授权。这条路径省去了手动开 Chrome 的步骤，但需要用户在场。

注意 Chrome 要求"启用远程调试端口必须使用非默认 user-data-dir"——这是 Chrome 内置的安全约束（[官方说明](https://developer.chrome.com/blog/remote-debugging-port)），不是 MCP server 加的。共享常规浏览 profile 给调试会话是危险的（任何本机进程都能连 9222 操控浏览器），所以文档示例都用 `--user-data-dir=/tmp/...` 隔离。

## 任务流案例：性能问题的端到端诊断

下面是 chrome-devtools-mcp 配合 Claude Code 的典型工作流——一次 LCP（最大内容绘制时间）突然劣化后的诊断全过程：

1. **触发**。用户在 Claude Code 输入：

```text
我们的产品页 LCP 最近从 1.8s 退化到 4.2s，看看是不是新加的 hero 图影响的。
```

2. **代理发现 + 启动**。Claude Code 通过 MCP 拿到 chrome-devtools-mcp 的工具列表（默认约 30 个），第一次调用需要浏览器的工具时，MCP server 自动启动 Chrome stable 实例。v1.8.0 起 `--pageIdRouting` 默认开启，每个 page-scoped 工具都要传 `pageId`——多个代理会话同时操作不同页面时互不干扰。

3. **trace 采集**。代理先 `navigate_page` 打开产品页，再调 `performance_start_trace`（`reload=true`，重新加载页面开始记录），加载完成后 `performance_stop_trace`。trace 数据保存为本地文件（默认 `.json.gz` 压缩，可用 `filePath` 参数指定路径）——**不是原始 JSON 内联返回**，这是 chrome-devtools-mcp 的关键设计选择，见下文。

4. **关键洞察抽取**。代理调用 `performance_analyze_insight`（传入 trace 结果里的 `insightSetId` 和洞察名，如 `LCPBreakdown`），MCP server 调用 DevTools frontend 的 trace 分析能力，返回结构化结论。返回形态示意：

```json
{
  "insights": [
    {"name": "LCP", "value": "4.12s", "element": "img.hero-banner"},
    {"name": "Render-blocking resources", "value": "1 stylesheet, 142ms"},
    {"name": "Largest network payload", "value": "img.hero-banner (2.4MB, no srcset)"}
  ]
}
```

5. **真实用户数据交叉验证**（CrUX 集成）。默认配置下，性能工具会把 trace URL 发到 Google CrUX（Chrome User Experience Report）API 取真实用户数据，让"实验室测量"与"真实用户体验"对齐。如果不想上传 URL，加 `--no-performance-crux`：

```bash
npx -y chrome-devtools-mcp@latest --no-performance-crux
```

6. **生成修复建议**。代理根据结构化洞察生成建议："hero 图 2.4MB 没 srcset，LCP 4.12s 主要在图片加载；加响应式 srcset + AVIF，预计 LCP 回到 1.8s 附近。"

整条链路里代理**从来没有看到 trace 的 50k 行 JSON**——MCP server 把它解析成 LCP / 阻塞资源 / 最大 payload 等概念。v1.10.0 又给大 trace 加了分块解析（chunked trace buffer parser），大页面的长 trace 也不会撑爆返回。这是 chrome-devtools-mcp 跟 Playwright + 人工看 trace 的根本差异。

## 设计原则（来自 `docs/design-principles.md`）

仓库的官方设计原则共 7 条，每条都对架构选择有直接影响：

| 原则 | 工程含义 |
|---|---|
| **Agent-Agnostic API** | 用 MCP 标准协议，不绑特定 LLM。Claude、Cursor、Copilot、Codex、Gemini CLI 都能消费同一套工具 |
| **Token-Optimized** | 返回语义摘要。`"LCP was 3.2s"` 比 50k 行 JSON 好。大块数据写文件 |
| **Small, Deterministic Blocks** | 给代理组合式小工具（Click、Screenshot），而不是一个"做正确的事"的大按钮 |
| **Self-Healing Errors** | 错误信息自带上下文和可能的修复建议——代理能基于错误自己排错 |
| **Human-Agent Collaboration** | 输出既要让机器读（结构化）又要让人读（摘要） |
| **Progressive Complexity** | 工具默认是简单的高阶动作，高级参数供进阶用户展开 |
| **Reference over Value** | 重型资产返回路径或 URI，绝不返回原始流 |

第 2 条（Token-Optimized）和第 7 条（Reference over Value）合起来构成了"截图缩放"的设计：截图默认 PNG，JPEG/WebP 体积小 3-5 倍（`--screenshotFormat` 可改默认格式，`--screenshotQuality` 控制压缩质量）；`--screenshotMaxWidth` / `--screenshotMaxHeight` 在源头降采样。这两个选项的注释直白写了 "Reduces context size in AI conversations"——图片 token 随像素尺寸走，而不是随编码后字节走，所以降采样比换格式更省上下文。

## 安全边界与隐私开关

README 第一段 Disclaimer 把边界写得很清楚：

> `chrome-devtools-mcp` exposes content of the browser instance to the MCP clients allowing them to inspect, debug, and modify any data in the browser or DevTools. Avoid sharing sensitive or personal information that you don't want to share with MCP clients.

也就是说 **MCP server 看到的所有浏览器内容都暴露给代理**。这条不是 bug，是设计——但使用前需要明确边界。

围绕这条边界，仓库提供了一组默认开或默认关的开关：

**使用统计，默认开启。** Google 收集工具调用成功率、延迟、环境信息，按 Google Privacy Policy 处理，且独立于 Chrome 浏览器自身的统计设置。`--no-usage-statistics` 关闭；设 `CHROME_DEVTOOLS_MCP_NO_USAGE_STATISTICS` 或 `CI` 环境变量也会自动关闭：

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--no-usage-statistics"]
    }
  }
}
```

**版本更新检查，默认开启。** 服务器定期查 npm registry，发现新版本会打日志；设 `CHROME_DEVTOOLS_MCP_NO_UPDATE_CHECKS` 关闭。

**CrUX 上传，默认开启。** 见上文任务流案例，`--no-performance-crux` 关闭。

**JavaScript 执行，默认开启。** `--no-javascript-evaluation` 会停用 `evaluate_script` 和 slim 模式的 `evaluate`、关闭 `navigate_page` 的 `initScript` 参数、禁止 `javascript:` / `data:` / `vbscript:` 导航——给不信任页面脚本的场景用。

**网络访问限制，默认不限制。** `--blockedUrlPattern` 屏蔽指定 URL 模式，`--allowedUrlPattern` 只放行指定模式（后者要求 Chrome 149+）。两者都用 URLPattern 语法；带正则捕获组的模式会被直接拒绝，因为重定向和子资源上无法可靠执行。

**文件写入范围。** MCP 客户端未协商 roots 能力时，文件写入工具默认限制在操作系统临时目录；`--filesystemRoot`（别名 `--workspace`）可追加允许目录，`--allowUnrestrictedPaths` 解除限制（只给完全信任的本地客户端用）。

**网络头脱敏。** `--redactNetworkHeaders` 在返回给客户端前脱敏部分敏感网络头（如 Cookie）。

浏览器支持面：只官方支持 Google Chrome 和 Chrome for Testing——其他 Chromium 内核浏览器（Edge / Brave / Arc）**可能工作但不保证**。官方承诺为最新版 Extended Stable Chrome 提供修复和支持。

## 版本节奏：四个月 14 个版本

CHANGELOG 显示这是一个节奏非常快的项目。v1.2.0 / v1.3.0 / v1.4.0（6 月）依次加入内存调试工具开关、heapsnapshot dominator 分析、skills 文件夹；此后半年继续高频迭代：

- **v1.5.0（2026-07-03）**：heap snapshot 对比工具、重复字符串统计
- **v1.6.0（2026-07-14）**：Lighthouse 升到 13.4.0，快照聚合支持过滤
- **v1.7.0（2026-08-10）**：heap snapshot 对象级详情（`get_heapsnapshot_object_details`）、按 native context 分组过滤
- **v1.8.0（2026-08-25）**：PWA 自动化 4 工具、`query_heapsnapshot_objects` 条件查询、`list_console_messages` 可带源映射堆栈、**pageId 必填**（`--pageIdRouting` 默认开，为多代理并发会话铺路）
- **v1.9.0（2026-09-08）**：Agent Plugins 1.0 包、cookie-debugging 技能、`--no-javascript-evaluation` 覆盖面扩到导航和 initScript、screencast 可调帧率
- **v1.10.0（2026-09-23）**：`get_css_styles` CSS 检查工具、`--config` JSON 配置文件、大 trace 分块解析
- **v1.10.1（2026-09-23）**：构建修复

两条主线值得注意。一是**内存分析持续加码**：v1.5 到 v1.8 连续四个版本都在堆 heap snapshot 工具——对比、对象级下钻、重复字符串、按执行上下文分组、条件查询。传统开发者用 DevTools 自己看 .heapsnapshot，不会主动要 dominator 链；代理需要这套结构化结论才能做"AI 内存分析"。二是**安全开关成体系**：JS 执行开关、网络白名单、文件系统限制、网络头脱敏——每一条都对应"把浏览器交给代理"这个动作新增的风险面。

## skills 与 Agent Plugins：从工具到技能包

v1.4.0 开始，这个仓库不再只发 MCP server。`skills/` 目录现在带 7 个技能：`chrome-devtools`（总入口）、`chrome-devtools-cli`（不走 MCP 的命令行用法）、`debug-optimize-lcp`、`memory-leak-debugging`、`cookie-debugging`、`a11y-debugging`、`troubleshooting`。编码代理装了技能之后，遇到对应任务（比如查内存泄漏）会自己翻对应的 playbook，而不是每次都靠工具描述现猜调用序列。

v1.9.0 的 Agent Plugins 1.0 把这套东西打成了可一键安装的插件包。README 还专门给"想把浏览器子代理集成进自家产品"的团队指了路：Gemini CLI 的 browser agent 就是官方参考实现。

## 适用边界与采用顺序

chrome-devtools-mcp 是"前端调试 AI 化"的事实标准入口之一，但用之前需要分清边界：

### 适合采用

- 前端 bug 排查需要"看真实浏览器行为"而不是看代码
- 性能优化（LCP / CLS / INP）需要持续测量与回归保护
- 自动化 e2e 测试想要 LLM 驱动而不是手写脚本
- 调试"只在生产环境、特定用户、特定设备下出现"的诡异问题
- 内存泄漏调查（`--memoryDebugging` 启用后，13 个分析工具可用）
- PWA 的安装/启动/状态自动化（`--categoryPwa`）

### 不适合采用

- 后端 / Node 服务 / API 调试——用对应语言的 debugger，不要经过浏览器
- 单纯截图任务（Playwright / Puppeteer 已够，chrome-devtools-mcp 是更重的选项）
- 不信任代理看到浏览器内容的高敏场景（任何登录态、任何表单数据都会暴露给代理）
- 没有 Chrome stable 通道的环境

### 推荐的接入顺序

1. **先用 slim 模式**。`npx -y chrome-devtools-mcp@latest --slim --headless` 只暴露 3 个工具，验证 MCP 配置和权限链路。
2. **再开 input automation + navigation**。这是 90% LLM 自动化任务的最小集合。
3. **按需开启 performance / network / memory**。每个类别的工具描述都会进上下文窗口，按需打开比"全开"更省 token。
4. **生产环境慎用 autoConnect**。`--autoConnect` 需要用户在现场授权（弹窗），适合本地开发，不适合 CI/CD；CI 用 `--browser-url` 显式连接更稳。
5. **不信任的页面上线前加限制**。`--no-javascript-evaluation` + `--allowedUrlPattern` + `--filesystemRoot` 三件套，把代理能碰的范围收窄。

## 仓库元信息

| 字段 | 值 |
|---|---|
| 仓库 | `ChromeDevTools/chrome-devtools-mcp` |
| 主页 | developer.chrome.com/docs/devtools/agents |
| 主语言 | TypeScript |
| Stars | 52,746（2026-09-30 核实） |
| 协议 | Apache 2.0 |
| 最新版 | v1.10.1（2026-09-23） |
| 工具规模 | 注册 59 个 / 11 类别，默认激活约 30 个（slim 模式 3 个） |
| 必需环境 | Node.js LTS（npm engines：20.19+ / 22.12+ / 23+）+ Chrome stable 或 Chrome for Testing |
| 包名 | `chrome-devtools-mcp`（npm 公开） |

如果只是想"让代理能截图并执行 JS"，slim 模式 5 分钟可用。如果要做"AI 驱动的端到端浏览器调试"，chrome-devtools-mcp 是当前 MCP 生态里**唯一一个把 DevTools 完整语义能力封装成代理工具**的项目——加上官方团队的迭代速度（四个月 14 个版本）和 Gemini CLI 已经把它做成内置 browser subagent 这两个信号，它暂时没有直接对手。

## 自测题

1. chrome-devtools-mcp 与 Puppeteer / Playwright 的本质区别在哪？
2. slim 模式默认保留哪三个工具？它解决了什么工程问题？
3. 路径 A（内置 Chrome）与路径 B（连接现有 Chrome）分别在什么场景下更合适？
4. 任务流案例里 `performance_analyze_insight` 返回的是 trace JSON 吗？它实际给代理的是什么？
5. v1.8.0 把 pageId 变成必填参数，解决的是什么问题？
6. CrUX 集成默认是开启还是关闭？不想把 URL 发给 Google 该加什么参数？
7. 使用统计默认开启，有哪几种关闭方式？

### 参考答案

1. 不是"又一个浏览器自动化工具"，而是把 DevTools 能力做**语义化封装**：给 LCP/CLS/FCP 数字、给 DOM 快照 + 无障碍树、给网络请求摘要，而不是 50k 行 trace JSON、整页 HTML 或原始 HAR。这让 LLM 上下文窗口用得起来。
2. `navigate` / `evaluate` / `screenshot`。59 个工具的描述全塞进上下文会很贵，slim 适合"打开页面看一眼"的轻量场景，先验证配置和权限链路。
3. 路径 A 让服务器自动起一个 Chrome stable 实例，最简单；路径 B 是连一个你手动启动、带 `--remote-debugging-port` 的 Chrome，适合要保留登录态/应用状态、要绕过 WebDriver 风控、或让浏览器跑在沙箱外的场景。`--autoConnect` 介于两者之间，但需要用户在场授权。
4. 不是 JSON。trace 文件保存为本地路径（重型资产返回路径而非原始字节），`performance_analyze_insight` 再调用 DevTools 前端的 trace 分析能力，返回"LCP 4.12s / 阻塞资源 / 最大 payload"这类结构化结论。
5. 多代理并发会话。`--pageIdRouting` 默认开启后，page-scoped 工具都按 pageId 路由到具体页面，多个代理同时操作不同页面互不干扰。
6. 默认开启（会把 trace URL 发到 Google CrUX API 取真实用户数据）。加 `--no-performance-crux` 即可关闭上传。
7. 三种：`--no-usage-statistics` 命令行参数、环境变量 `CHROME_DEVTOOLS_MCP_NO_USAGE_STATISTICS`、或设 `CI` 环境变量（CI 下自动关闭）。

## 练习

1. 用 `npx -y chrome-devtools-mcp@latest --slim --headless` 起一个 MCP server，在 Claude Code / Cursor 里验证它能列出三个工具并完成一次截图。
2. 打开任意一个网页，用 `evaluate_script` 在页面上下文里取出某个 DOM 节点的 `textContent` 或某个全局变量的值。
3. 复现任务流案例：对某个慢页面依次跑 `navigate_page` → `performance_start_trace`（`reload=true`）→ `performance_stop_trace` → `performance_analyze_insight`，对比"有 srcset"和"无 srcset"两种 hero 图下的 LCP。
4. 手动启动带 `--remote-debugging-port=9222` 的 Chrome（先登录一个站点），再用 `--browser-url=http://127.0.0.1:9222` 连接过去，确认代理能操作你已经登录的页面。
5. 加 `--memoryDebugging` 启动，对一个已知会泄漏内存的页面依次 `take_heapsnapshot` → 操作 → `compare_heapsnapshots`，看 dominator 链指向哪类对象。

## 进阶路径

- 读 `docs/design-principles.md` 七条原则，重点看 Token-Optimized 与 Reference over Value 如何共同决定"截图降采样、trace 返回路径"这些取舍。
- 翻 `docs/configuration.md` 的完整参数表，理解每个默认值背后的取舍；`docs/advanced-usage.md` 覆盖并发会话、持久 user-data-dir、Android 设备调试。
- 翻 `src/tools/` 下的工具注册代码，理解每个工具如何把 DevTools 协议调用收束成一个语义化返回。
- 写一个 Third-party 类别的自定义 developer tool（`list_3p_developer_tools` / `execute_3p_developer_tool`），把你们内部平台的能力暴露给代理。
- 把 CrUX API 与你们自己的 RUM 数据对齐，让代理的"修复建议"同时参考真实用户指标和实验室测量。

## 常见问题 FAQ

**Q：只能用在 Google Chrome 上吗？Edge / Brave / Arc 行不行？**
官方只支持 Google Chrome 和 Chrome for Testing。其它 Chromium 内核浏览器"可能工作但不保证"——因为它们未必实现完整的 DevTools 远程调试协议细节。生产环境别赌这个。

**Q：代理会看到我的登录态和表单数据吗？**
会。MCP server 看到的所有浏览器内容都暴露给代理，这是设计使然（README 第一段 Disclaimer 写明了）。高敏场景要么用隔离的 `--isolated` profile，要么加 `--redactNetworkHeaders` / `--no-javascript-evaluation` 收窄暴露面，要么干脆不接这类页面。

**Q：`--autoConnect` 为什么不适合 CI？**
因为它需要用户在 `chrome://inspect` 弹窗里手动授权，依赖"人在现场"。CI 里没有人点确认，链路会卡住。CI 用路径 B 的 `--browser-url` 显式连接更稳。

**Q：trace / 截图这些文件存哪了，怎么清理？**
默认 user-data-dir 跨实例共享、不会自动清理（路径在 `$HOME/.cache/chrome-devtools-mcp/`）。要彻底隔离就在启动时加 `--isolated`，浏览器关闭后临时目录自动删除。

**Q：几十个工具把上下文撑爆了怎么办？**
默认只激活约 30 个，已经过滤掉大头（Memory 的 13 个重分析工具、Extensions / PWA / WebMCP / Third-party 四个类别默认全关）。还不够就用类别开关继续关：`--categoryInput=false`、`--categoryEmulation=false` 等；或者直接用 slim 模式只留 3 个。

**Q：工具报错了有没有自带排错指引？**
有。设计原则里的 Self-Healing Errors 要求错误信息自带上下文和可能的修复建议，代理能基于错误自己重试或换路径，不需要你从零读堆栈。
