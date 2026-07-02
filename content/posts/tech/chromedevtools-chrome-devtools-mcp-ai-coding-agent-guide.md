---
title: "chrome-devtools-mcp：把 Chrome DevTools 装进 AI 编码代理"
date: "2026-07-02T21:08:42+08:00"
lastmod: "2026-07-02T21:08:42+08:00"
draft: false
categories: ["技术笔记"]
tags: ["MCP", "Chrome DevTools", "AI Agent", "Puppeteer", "性能分析"]
description: "chrome-devtools-mcp 把 Chrome DevTools 能力通过 MCP 暴露给 AI 编程代理，以语义摘要替代 trace JSON。本文拆解工具分层与连接模式。"
weight: 1
author: text-matrix
---

# chrome-devtools-mcp：把 Chrome DevTools 装进 AI 编码代理

`ChromeDevTools/chrome-devtools-mcp` 是 Chrome DevTools 官方团队在 2026 年主推的项目（截至 2026-07-02 达 44,941 Star，单日新增 92）。它的定位非常精确：把 DevTools 完整能力通过 Model Context Protocol（MCP）暴露给 Claude、Cursor、Copilot、Antigravity、Codex、Gemini CLI 这类编码代理，让代理拥有真正的"可观察、可操作"浏览器——不再只是给出截图和 console log，而是能驱动真实 Chrome 实例去做自动化、调试、性能分析。

往深看，它的核心价值不在于"又一个浏览器自动化工具"（这一直是 Puppeteer / Playwright 的领地），而在于**DevTools 能力的语义化封装**：

- **拿 LCP / CLS / FCP 数字**而不是 50k 行 trace JSON
- **拿"DOM 节点 + 无障碍树 + 关键属性"快照**而不是整页 HTML
- **拿"网络请求 + 关键 headers + 状态码"**而不是原始 HAR
- **拿"heap 增长分类 + dominator 链"**而不是 .heapsnapshot 文件本身

这条"语义化 → 压缩 → 适合 LLM 上下文窗口"的设计哲学贯穿整个仓库，是它跟 Puppeteer 的本质差异。

## 系统地图：51+ 工具按能力切片

仓库当前默认暴露 51 个工具（含 1 个 slim 套餐），按能力分组：

| 类别 | 工具数 | 代表工具 |
|---|---:|---|
| **Input automation** | 10 | `click` / `drag` / `fill` / `fill_form` / `press_key` / `type_text` / `upload_file` / `click_at`（坐标点击，需视觉模型） / `hover` / `handle_dialog` |
| **Navigation automation** | 6 | `navigate_page` / `new_page` / `list_pages` / `close_page` / `select_page` / `wait_for` |
| **Emulation** | 2 | `emulate`（设备、CPU 节流、网络条件）/ `resize_page` |
| **Performance** | 3 | `performance_start_trace` / `performance_stop_trace` / `performance_analyze_insight` |
| **Network** | 2 | `list_network_requests` / `get_network_request` |
| **Debugging** | 8 | `evaluate_script` / `take_snapshot`（DOM + 无障碍树）/ `take_screenshot` / `list_console_messages` / `get_console_message` / `lighthouse_audit` / `screencast_start` / `screencast_stop` |
| **Memory** | 11 | `take_heapsnapshot` / `close_heapsnapshot` / `compare_heapsnapshots_summary` / `compare_heapsnapshots_class_nodes` / `get_heapsnapshot_summary` / `get_heapsnapshot_class_nodes` / `get_heapsnapshot_details` / `get_heapsnapshot_dominators` / `get_heapsnapshot_edges` / `get_heapsnapshot_retainers` / `get_heapsnapshot_retaining_paths` |
| **Extensions** | 5 | `install_extension` / `list_extensions` / `reload_extension` / `trigger_extension_action` / `uninstall_extension` |
| **Third-party** | 2 | `list_3p_developer_tools` / `execute_3p_developer_tool` |
| **WebMCP** | 2 | `list_webmcp_tools` / `execute_webmcp_tool`（需 Chrome 149+） |

`slim` 模式只保留三个：`navigate_page` + `evaluate_script` + `take_screenshot`，适合"我只要打开页面看一眼"的轻量场景，避免一次性把 51 个工具描述塞进上下文窗口。

类别间有清晰的开关：

```bash
npx -y chrome-devtools-mcp@latest \
  --categoryEmulation=false \
  --categoryPerformance=true \
  --categoryNetwork=true \
  --categoryExtensions=true \
  --memoryDebugging
```

`--categoryEmulation`、`--categoryPerformance`、`--categoryNetwork` 默认为 `true`；`--categoryExtensions` 和 `--memoryDebugging` 默认关闭——这两个类别工具描述加起来相当长，工程上做了"按需加载"的折中。

## 双模式启动：内置 Chrome 还是连接现有 Chrome

跟 Puppeteer 不同，chrome-devtools-mcp 把"启动浏览器"这件事做成了两条互斥路径：

### 路径 A：内置 Chrome 实例（默认）

第一次调用需要浏览器的工具时，服务器会自动启动一个 Chrome stable 通道实例，使用专用 user-data-dir：

- Linux / macOS: `$HOME/.cache/chrome-devtools-mcp/chrome-profile-$CHANNEL`
- Windows: `%HOMEPATH%/.cache/chrome-devtools-mcp/chrome-profile-$CHANNEL`

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

Chrome 144+ 还提供了 `--autoConnect` 模式：通过 `chrome://inspect/#remote-debugging` 启用远程调试，配置 `--autoConnect` 后 MCP server 会自动定位当前用户配置的 default profile 并发起连接，弹出对话框让用户授权。这条路径省去了手动开 Chrome 的步骤，但需要用户在场。

注意 Chrome 要求"启用远程调试端口必须使用非默认 user-data-dir"——这是 Chrome 内置的安全约束，不是 MCP server 加的。共享常规浏览 profile 给调试会话是危险的（任何本机进程都能连 9222 操控浏览器），所以 MCP server 强制 `--user-data-dir=/tmp/...` 隔离。

## 任务流案例：性能问题的端到端诊断

下面是 chrome-devtools-mcp 配合 Claude Code 的典型工作流——一次 LCP（最大内容绘制时间）突然劣化后的诊断全过程：

1. **触发**。用户在 Claude Code 输入：

```text
我们的产品页 LCP 最近从 1.8s 退化到 4.2s，看看是不是新加的 hero 图影响的。
```

2. **代理发现 + 启动**。Claude Code 通过 MCP 拿到 `chrome-devtools-mcp` 的 51 个工具，第一次调用 `navigate_page` 时 MCP server 自动启动 Chrome stable 实例。

3. **trace 采集**。代理依次调用 `performance_start_trace` → `navigate_page` 打开产品页 → 等待关键渲染 → `performance_stop_trace`。trace 文件被保存为本地路径（**不是原始 JSON 内联返回**——这是 chrome-devtools-mcp 的关键设计选择，见下文）。

4. **关键洞察抽取**。代理调用 `performance_analyze_insight`，MCP server 调用 DevTools frontend 的 trace 分析能力，返回结构化结论：

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

整条链路里代理**从来没有看到 trace 的 50k 行 JSON**——MCP server 把它解析成 LCP / 阻塞资源 / 最大 payload 等概念。这是 chrome-devtools-mcp 跟 Playwright + 人工看 trace 的根本差异。

## 设计原则（来自 `docs/design-principles.md`）

仓库的官方设计原则共 7 条，每条都对架构选择有直接影响：

| 原则 | 工程含义 |
|---|---|
| **Agent-Agnostic API** | 用 MCP 标准协议，不绑特定 LLM。Claude、Cursor、Copilot、Codex、Gemini CLI 都能消费同一套工具 |
| **Token-Optimized** | 返回语义摘要。`"LCP was 3.2s"` 比 50k 行 JSON 好。重型资产（截图、trace、视频）返回文件路径，不返回原始字节 |
| **Small, Deterministic Blocks** | 给代理组合式小工具（Click、Screenshot），而不是一个"做正确的事"的大按钮 |
| **Self-Healing Errors** | 错误信息自带上下文和可能的修复建议——代理能基于错误自己排错 |
| **Human-Agent Collaboration** | 输出既要让机器读（结构化）又要让人读（摘要） |
| **Progressive Complexity** | 工具默认是简单的高阶动作，高级参数供进阶用户展开 |
| **Reference over Value** | 重型资产返回路径或 URI，绝不返回原始流 |

第 2 条（Token-Optimized）和第 7 条（Reference over Value）合起来构成了"截图缩放"的设计：截图默认是 PNG，但 JPEG/WebP 体积小 3-5 倍；`--screenshotMaxWidth` / `--screenshotMaxHeight` 在源头做降采样。这两个选项的注释直白写了"Reduces context size in AI conversations"——是为 LLM 上下文窗口做的工程取舍。

## 隐私与统计：使用数据默认开启

README 第一段 Disclaimer 把边界写得很清楚：

> `chrome-devtools-mcp` exposes content of the browser instance to the MCP clients allowing them to inspect, debug, and modify any data in the browser or DevTools. Avoid sharing sensitive or personal information that you don't want to share with MCP clients.

也就是说 **MCP server 看到的所有浏览器内容都暴露给代理**。这条不是 bug，是设计——但使用前需要明确边界。

另一个默认开启的边界是**使用统计**：

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

默认收集"工具调用成功率、延迟、环境信息"，按 Google Privacy Policy 处理。`--no-usage-statistics` 关闭，或设 `CHROME_DEVTOOLS_MCP_NO_USAGE_STATISTICS` / `CI` 环境变量也会自动关闭。

只支持 Google Chrome 和 Chrome for Testing——其他 Chromium 内核浏览器（Edge / Brave / Arc）**可能工作但不保证**。

## 版本节奏：从 2026-05 到 2026-06 的密集发布

CHANGELOG 显示这是一个节奏非常快的项目，2026-05-27 到 2026-06-23 之间连发了 1.1.1 / 1.2.0 / 1.3.0 / 1.4.0：

- **v1.2.0（2026-06-08）**：启用内存调试工具（`--memoryDebugging`）、allowed/blockedUrlPattern、`close_heapsnapshot`、实验性 TOON 结构化输出
- **v1.3.0（2026-06-18）**：新增 `get_heapsnapshot_dominators` / retaining paths / edges，截图 CLI 加尺寸限制，list_pages 加 title
- **v1.4.0（2026-06-23）**：发布 skills 文件夹，让 Claude Code 既能拿 MCP server 也能拿配套技能（之前只能装 MCP）

一个明显趋势是**"工具集从开发者向代理迁移"**：v1.2 的内存调试工具、v1.3 的 dominator / retaining paths 都是给代理做"AI 内存分析"用的——传统开发者用 Chrome DevTools 自己看 .heapsnapshot 文本，不会主动要 dominator 链；代理需要。

## 适用边界与采用顺序

chrome-devtools-mcp 是"前端调试 AI 化"的事实标准入口之一，但用之前需要分清边界：

### 适合采用

- 前端 bug 排查需要"看真实浏览器行为"而不是看代码
- 性能优化（LCP / CLS / INP）需要持续测量与回归保护
- 自动化 e2e 测试想要 LLM 驱动而不是手写脚本
- 调试"只在生产环境、特定用户、特定设备下出现"的诡异问题
- 内存泄漏调查（--memoryDebugging 启用后）

### 不适合采用

- 后端 / Node 服务 / API 调试——用对应语言的 debugger，不要经过浏览器
- 单纯截图任务（Playwright / Puppeteer 已够，chrome-devtools-mcp 是更重的选项）
- 不信任代理看到浏览器内容的高敏场景（任何登录态、任何表单数据都会暴露给代理）
- 没有 Chrome stable 通道的环境

### 推荐的接入顺序

1. **先用 slim 模式**。`npx -y chrome-devtools-mcp@latest --slim --headless` 只暴露 3 个工具，验证 MCP 配置和权限链路。
2. **再开 input automation + navigation**。这是 90% LLM 自动化任务的最小集合。
3. **按需开启 performance / network / memory**。每个类别的工具描述都会进上下文窗口，按需打开比"全开"更省 token。
4. **生产环境慎用 autoConnect**。`--autoConnect` 需要用户在现场授权（弹窗），适合本地开发不适合 CI/CD。

## 仓库元信息

| 字段 | 值 |
|---|---|
| 仓库 | `ChromeDevTools/chrome-devtools-mcp` |
| 主语言 | TypeScript |
| Stars | 44,941（2026-07-02，单日 +92） |
| 协议 | Apache 2.0（仓库内） |
| 最新版 | v1.4.0（2026-06-23） |
| 默认工具数 | 51（含 slim 模式 3 个） |
| 必需环境 | Node.js LTS + Chrome stable 或 Chrome for Testing |
| 包名 | `chrome-devtools-mcp`（npm 公开） |

如果只是想"让代理能截图并执行 JS"，slim 模式 + Claude Code 的 plugin 安装是 5 分钟可用的最小路径。如果要做"AI 驱动的端到端浏览器调试"，chrome-devtools-mcp 是当前 MCP 生态里**唯一一个把 DevTools 完整语义能力封装成代理工具**的项目——这一点它暂时没有直接对手。