---
title: "chrome-devtools-mcp：把 Chrome DevTools 完整能力切给 Coding Agent"
date: "2026-07-09T02:55:00+08:00"
slug: "chrome-devtools-mcp-ai-agent-browser-debug-mcp"
github_repo: "ChromeDevTools/chrome-devtools-mcp"
source_key: "gh:ChromeDevTools/chrome-devtools-mcp"
description: "chrome-devtools-mcp 是 Chrome DevTools 团队官方出的 MCP server 与 CLI，把 Performance、Network、Memory、PWA 等真实 DevTools 能力暴露给 Claude/Cursor/Copilot 等 Coding Agent。本文拆解 58 个工具（11 组，部分分组需开参数）、性能 trace 流程、一个修性能问题的任务流案例，以及它与 Playwright MCP 的选型取舍。"
draft: false
categories: ["技术笔记"]
tags: ["MCP", "Chrome DevTools", "AI Agent"]
---

# chrome-devtools-mcp：把 Chrome DevTools 完整能力切给 Coding Agent

## 它到底解决什么问题

chrome-devtools-mcp（仓库 `ChromeDevTools/chrome-devtools-mcp`）要接近一个目标：让 Coding Agent 像一个熟练的前端工程师一样使用 Chrome DevTools。它把 DevTools 的能力拆成多个工具组，按 MCP 协议暴露给 Claude Code、Cursor、Copilot 等客户端。以 2026-09 发布的 v1.9.0 为口径，官方工具参考列出 58 个工具，分属 11 组——除了点击、填表、导航这些基础动作，还覆盖性能 trace、堆快照 diff、Lighthouse 审计、扩展管理，以及 Progressive Web Apps（PWA）的安装与启动。默认配置只激活其中 30 个，其余要靠启动参数逐组打开；这个数字也会随版本演进，要用精确清单，以官方 tool-reference 为准。它自己也是拿 Puppeteer 当自动化基座（动作自带等待、结果可靠），和"拿 Puppeteer 给 Agent 写一层薄 wrapper"的真正差别在于：性能 trace、堆快照这些 DevTools 高级能力，MCP 协议一次绑定就能调用，不用自己维护一份 trace 解析脚本。

如果只是想"让 Agent 点按钮、填表单、抓截图"，可以选轻量方案；如果要"让 Agent 看 performance trace、对比 heap snapshot、抓 source-mapped 错误"，chrome-devtools-mcp 是当下最完整的官方路径。

## 系统这么分：三层 + 工具分组

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
│  │   2 tools  │  │   9 tools  │  │  13 tools  │  │   5 tools  │ │
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

上面的分组合计 54 个工具，图中尚未画出最后一组 **Progressive Web Apps（4 个）**：`get_os_app_state`、`install_pwa`、`launch_pwa`、`uninstall_pwa`。加上这组，当前总数是 58。

但图里的数字是各组的完整规模，不等于开箱可用数。默认激活的只有输入自动化（不含 `click_at`）、导航、仿真、性能、网络、调试（不含 screencast）这六组，加上内存组的 `take_heapsnapshot`，合计 30 个。其余的开关分别是：内存组另外 12 个工具要加 `--memoryDebugging`；扩展组要加 `--categoryExtensions`；第三方与 WebMCP 分别对应 `--categoryExperimentalThirdParty`、`--categoryExperimentalWebmcp`；PWA 组要加 `--categoryPwa`；`click_at` 要 `--experimentalVision`；screencast 要 `--experimentalScreencast`（还要求机器上装了 ffmpeg）。其中扩展组和 PWA 组目前只支持 pipe 连接，`--browser-url`、`--autoConnect` 这类连接方式带不动它们。

另一个方向是收窄：`--slim` 把整个服务端收成 3 个工具——`navigate`、`evaluate`、`screenshot`，适合只需要基础浏览任务的场景。图中的 CLI 是服务端的另一种形态，用法见"接入方式"一节末尾。

## 为什么不是又一个浏览器自动化 wrapper

市面上能给 Agent 操作浏览器的方案不少，但多数只解决"自动化点击"。chrome-devtools-mcp 的差异化集中在三处：

1. **官方团队出品，底座是 Puppeteer**：服务端由 Chrome DevTools 团队维护，自动化层用 Puppeteer 驱动 Chrome，动作自带等待；Performance、Memory、Lighthouse、扩展管理这些 DevTools 高级能力都直接暴露。
2. **MCP 协议一次绑定**：`npx -y chrome-devtools-mcp@latest` 一行就把默认分组的工具注册到 MCP client，需要更多能力再加启动参数，不用自己逐个封装。
3. **保持 DevTools 的可观测性**：性能 trace、堆快照、网络请求详情这些"看起来 Agent 用不上"的信息，对调试真实应用极其关键。

它的关键限制在 README 里写得很清楚：**官方只支持 Google Chrome 与 Chrome for Testing，其他 Chromium 派生浏览器"may work"但不被保证**；官方承诺的修复与支持范围也只覆盖最新的 Extended Stable 版本。这意味着项目是绑在 Chrome 上的，不要把它当成"通用浏览器协议"。

## 工具分组与典型调用

官方文档按工具用途分好了组，这里再按"什么场景该动哪一组"筛一遍，方便直接挑：

### 1. 输入自动化（10 tools）

点、拖、填表单、悬停、按键、处理浏览器弹窗、上传、点击指定坐标——这些是"动浏览器"的基本动作。`fill_form`、`click_at`、`upload_file` 比单纯的 `click` 更贴合现代 web 表单的复杂性。`fill_form` 一次调用填完整张表单，官方明确建议优先用它代替多次 `fill`。两个细节容易踩坑：`click_at` 按坐标点击，要开 `--experimentalVision`，而且通常得配一个能看截图给坐标的 computer-use 模型；`upload_file` 的文件路径必须是浏览器实例那一侧的本地路径，不是 MCP 客户端侧——浏览器跑在容器或远程机器上时路径会失效。

### 2. 导航与多页管理（6 tools）

`navigate_page`、`new_page`、`list_pages`、`select_page`、`close_page`、`wait_for` 是多 tab 调试的核心。Agent 在"打开 A 页面、登录、切到 B 页面、操作 C"这种任务上需要明确的"页"对象，模型才能精准选择。`new_page` 还支持 `isolatedContext` 参数：同名上下文共享 cookie 和存储，不同上下文完全隔离，做多账号并行测试时不用反复清登录态。注意 `wait_for` 等的是指定文本出现在页面上，不是"等网络空闲"——语义是文本断言，不是加载完成信号。

### 3. 仿真与多设备（2 tools）

`emulate` 能模拟 CPU 节流、网络限速（Slow 3G 到 Fast 4G）、深浅色模式、UA、地理位置、自定义请求头和 viewport；`resize_page` 调整窗口尺寸。典型用法是让性能 trace 在弱网、低端设备的条件下复现真实体验，或者对比不同 viewport 下的布局表现。

### 4. 性能分析（3 tools）

这是 chrome-devtools-mcp 最"上强度"的工具组：

- `performance_start_trace`：启动 Chrome 内置的 trace recorder，官方定位就是排查前端性能问题和 Core Web Vitals（LCP、INP、CLS）。支持 `reload`（开始录制后自动重载页面）和 `autoStop`（录完自动停止），原始 trace 可以存成文件。
- `performance_stop_trace`：停掉录制，需要时把原始 trace 落盘。
- `performance_analyze_insight`：trace 结果里会给出 Insight 集合的概要，这个工具对其中某个具体 Insight 深挖细节——传 `insightName`（比如 `LCPBreakdown`、`DocumentLatency`）和对应的 `insightSetId`。

下面是性能 trace 的典型调用序列：

```
navigate_page（先把页面导航到目标 URL）
  → performance_start_trace（reload/autoStop 按需开启）
    → 跑业务场景或等自动停止
      → performance_analyze_insight（对可疑 Insight 逐个深挖）
```

这跟过去 Puppeteer + trace 手工分析的差异是：**Agent 能直接调用底层的 Insights API**，不再要维护一份手工 trace 解析脚本。

#### 性能分析任务流示例：一个 LCP 问题从定位到修复

举一个实际工作流，展示如何用这套工具链完成一次完整调试：

1. **导航到位**：用 `navigate_page` 把页面带到目标 URL。官方参数说明要求：打算用 `reload` 或 `autoStop` 时，必须先导航再启动 trace
2. **启动 trace**：调 `performance_start_trace`，开 `reload: true` 和 `autoStop: true`，页面自动重载并录制到加载稳定
3. **读概要**：录制结果直接带出 Insight 集合——LCP 拆解、长任务、渲染阻塞这些条目一目了然
4. **深挖可疑项**：对 LCP 相关的 Insight 调 `performance_analyze_insight`（`insightName` 传 `LCPBreakdown`），拿到 LCP 各阶段的耗时分解和涉及的具体资源
5. **Agent 动手改代码**：根据诊断结果处理——比如压缩主图资源、调整加载优先级、加懒加载
6. **重新验证**：重跑一遍 trace，对比 LCP 数值的变化

整个过程中，开发者只需要说一句"帮我看看为什么 LCP 这么慢"，从录制到拿到结论全由 Agent 操作，不需要手动点 DevTools 面板、复制粘贴 trace、再对着结果读一遍。

### 5. 网络（2 tools）

`list_network_requests` 列出上次导航以来的请求，支持分页、按资源类型过滤，还能带上最近 3 次导航的保留请求；`get_network_request` 拿单个请求的详情——请求头（含 `Cookie`）和响应头（含 `Set-Cookie`）都在。配合调试组的 source-mapped console 错误，"接口 500 + 控制台具体报错"一抓一个准。

### 6. 调试（9 tools）

- `evaluate_script`：在浏览器上下文跑任意 JS，返回值必须是 JSON 可序列化的。
- `list_console_messages` / `get_console_message`：拿 console 日志，堆栈自带 source map 还原。
- `take_snapshot` / `take_screenshot`：前者是基于无障碍树（a11y tree）的文本快照，给页面元素标上 uid——Agent 定位元素全靠它，官方明确建议优先用快照；后者是视觉截图，适合人眼复核或配合视觉模型。
- `get_css_styles`：查某个元素的匹配规则、内联样式、继承样式和层叠信息，用来解释"这条 CSS 为什么生效、被谁覆盖"。
- `lighthouse_audit`：跑 Lighthouse 审计，覆盖可访问性、SEO、最佳实践和 agentic browsing——注意它**不含性能**，性能问题走上面那组 trace 工具。支持 desktop/mobile 设备模拟和 navigation/snapshot 两种模式。
- `screencast_start` / `screencast_stop`：把页面录成视频（.webm/.mp4），需要开 `--experimentalScreencast` 且机器上装有 ffmpeg。

### 7. 内存（13 tools）

这一组是 chrome-devtools-mcp 最独特的地方。`take_heapsnapshot` 默认可用；其余 12 个要加 `--memoryDebugging` 才会出现：`compare_heapsnapshots`（两份快照 diff）、`get_heapsnapshot_retaining_paths`（追溯"某个对象为什么没被 GC"）、`get_heapsnapshot_dominators`（谁在撑住这个节点）、`get_heapsnapshot_edges`（引用关系）、`query_heapsnapshot_objects`（按类名、大小等条件查询对象），以及 `close_heapsnapshot`、`get_heapsnapshot_class_nodes`、`get_heapsnapshot_details`、`get_heapsnapshot_duplicate_strings`、`get_heapsnapshot_object_details`、`get_heapsnapshot_retainers`、`get_heapsnapshot_summary`。直接对两份堆快照做 diff、顺藤摸瓜找 retaining path，这套能力极少出现在通用 MCP server 里——排查大型 SPA 的内存泄漏时，比人肉在 DevTools 里点要可靠得多。

### 8. 扩展 / 第三方 / WebMCP（共 9 tools）

扩展组（`install_extension`、`list_extensions`、`reload_extension`、`trigger_extension_action`、`uninstall_extension`）让 Agent 可以管理浏览器里的扩展。注意 `install_extension` 装的是本地 unpacked 扩展目录，不是从 Chrome 商店安装——典型场景是开发自己的扩展：改完代码让 Agent `reload_extension` 再自动验证行为。整组默认关闭，要加 `--categoryExtensions`，而且这个开关目前只在 pipe 连接下可用（`--browser-url`、`--autoConnect` 带不动它）。

在扩展之外，还有两组与浏览器内部协议相关的工具，同样默认关闭：

- 第三方工具（2 个）：`execute_3p_developer_tool` / `list_3p_developer_tools`，开关是 `--categoryExperimentalThirdParty`——调用被测页面自己暴露的调试工具。
- WebMCP（浏览器内 MCP，2 个）：`execute_webmcp_tool` / `list_webmcp_tools`，开关是 `--categoryExperimentalWebmcp`。这条值得关注：当一个网页本身实现了 WebMCP，Agent 可以直接调用页面暴露的工具，不必走 DOM。

### 9. 渐进式 Web 应用（4 tools）

`install_pwa` / `launch_pwa` / `uninstall_pwa` / `get_os_app_state` 覆盖 PWA 的安装、启动、卸载与 OS 集成状态查询（角标数、注册的文件处理器）。整组要加 `--categoryPwa`，同样只支持 pipe 连接。有一个和直觉不同的点：`install_pwa` 走 PWA CDP 域直接安装，**没有用户手势、也不模拟安装提示对话框**，默认装成 browser 显示模式；要独立窗口体验得显式传 `displayMode: "standalone"`。所以它的价值不是"验收安装弹窗"，而是让 Agent 能端到端验证一个 Web App 以系统应用形态（独立窗口、桌面图标）装好、启动、跑起来的完整链路——比如"装上后独立窗口能不能正常打开、离线缓存是否生效"这类验收。

## 隐私与遥测：哪些数据被发走了

README 在 Disclaimers 和 Usage statistics 两节写下几个容易被忽略的点：

- **usage statistics 默认开**：Google 会收集工具调用成功率、延迟、环境信息。关掉用 `--no-usage-statistics`，或设置环境变量 `CHROME_DEVTOOLS_MCP_NO_USAGE_STATISTICS`。
- **CI 环境会自动关**：`CI` 环境变量存在时自动停用统计。
- **Performance 工具可能调用 CrUX API**：把 trace 里的 URL 发给 CrUX 换回真实用户体验（field）数据，与实验室数据对照。能用 `--no-performance-crux` 关掉。
- **Update check 默认开**：定期查 npm registry 通知有新版，可用 `CHROME_DEVTOOLS_MCP_NO_UPDATE_CHECKS=1` 关闭。

在 CI、个人开发机、涉及敏感数据的场景里，建议把这三项默认开启的数据行为都关一遍再跑。另外还有两个收紧面的选项：`--redactNetworkHeaders` 在把网络详情返回给客户端前脱敏部分敏感请求头；`--blockedUrlPattern` / `--allowedUrlPattern`（后者需 Chrome 149+）能直接限制浏览器可访问的域名范围。

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

- Claude Code：`claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest`；或装成插件（MCP + Skills 一起装）`/plugin marketplace add ChromeDevTools/chrome-devtools-mcp`，再 `/plugin install chrome-devtools-mcp@chrome-devtools-plugins`
- VS Code / Copilot：推荐以插件方式安装（把 MCP server 和 skills 一起打包，装完就能用）；也可以手动加，macOS/Linux 命令是 `code --add-mcp '{"name":"io.github.ChromeDevTools/chrome-devtools-mcp","command":"npx","args":["-y","chrome-devtools-mcp"],"env":{}}'`
- Codex：`codex mcp add chrome-devtools -- npx chrome-devtools-mcp@latest`
- Cursor、Gemini CLI、JetBrains 等：在各自 MCP 配置里填同一段最小配置即可，核心字段一致，官方 README 有逐家说明

> **注意**：MCP server 会把当前 Chrome 实例里的内容暴露给 MCP 客户端，客户端能读取、调试、修改浏览器里的任何数据。不要在调试时把不想让客户端看到的敏感或个人信息留在页面里。

如果不想跑 MCP、只想在终端里直接操作浏览器，可以用包自带的实验性 CLI：全局装一次 `npm i -g chrome-devtools-mcp`，就有 `chrome-devtools` 命令，`status` 检查是否装好，`navigate_page`、`take_screenshot`、`lighthouse_audit` 等直接在终端跑，`stop` 退出后台守护进程。两点提醒：CLI 默认开放无限制的文件系统访问，用 `--workspace` 把文件工具圈在指定目录里；需要额外 flag 的工具（比如 `--categoryExtensions` 那组）在 CLI 里用不了，`wait_for`、`fill_form` 这类少数命令也未纳入。

## 关键设计取舍

读完代码与 README 后几个工程启示：

- **stdio 走 MCP，连接方式可选**：默认由 `npx` 拉起 MCP server，通过标准输入/输出和客户端通信。要接一个已经在跑的 Chrome，有两条路：一是 `--browser-url=http://127.0.0.1:9222` 连远程调试端口（适合沙箱环境、IDE 内置浏览器这类场景，但开了调试端口后本机任何应用都能连上这个浏览器，调试期间别开敏感网站）；二是 Chrome 144+ 的 `--autoConnect`，在 `chrome://inspect/#remote-debugging` 里开启远程调试后，server 自动连上当前浏览器并弹窗请求授权——适合"手动测试和 Agent 测试共享同一个浏览器状态"的日常场景。这种解耦让工具在不同编辑器之间复用。
- **默认持久 profile，隔离靠 `--isolated`**：默认用专用目录（`~/.cache/chrome-devtools-mcp/chrome-profile`）持久保存浏览器数据，登录态天然跨会话保留，代价是同一时间只能有一个浏览器实例占用它；加 `--isolated` 则改用临时目录，浏览器关闭即清理，适合多个 server 实例并行各跑各的。想换位置用 `--userDataDir` 指定。CLI 这边默认策略相反：headless 和 isolated 都默认开启，除非显式传了 `--userDataDir`。
- **Experimental CLI**：内置 CLI 通过 Unix socket（macOS/Linux）或命名管道（Windows）连一个后台 `chrome-devtools-mcp` daemon，同一个后台实例被多次命令复用，页面、cookie 这些状态得以保留；`start`、`stop`、`status` 手动控制生命周期。

### 跟 Playwright MCP 怎么选

这是最常问到的边界问题，一句话就能说清：

- **要自动化 UI 测试** → 选 Playwright MCP，它就是干这个的，跨浏览器、元素定位、断言都做完整
- **要 Agent 自己做前端调试** → 选 chrome-devtools-mcp，它能把 DevTools 里的性能、内存、网络诊断直接给 Agent

Playwright 适合"你写脚本，机器跑断言"；chrome-devtools-mcp 适合"Coding Agent 自己动手读诊断、改代码，再验证"。路径目标不一样，不要混着用。

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

## 值不值得接入

chrome-devtools-mcp 的真正价值，是把 DevTools 里最吃人力的几类活——跑性能 trace、排查内存泄漏、做 Lighthouse 审计——打包成 agent 能直接调用的工具。前端调试的工作重心随之从"人盯着 DevTools 面板"移到"Agent 动手、人复核结果"。如果你的 Coding Agent 确实需要一套真实可用的浏览器调试能力，这是目前最稳的官方路径。

## 参考链接

- 仓库：<https://github.com/ChromeDevTools/chrome-devtools-mcp>
- 工具参考（完整工具清单，分组与数量随版本更新）：<https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/tool-reference.md>
- 配置参数总表（全量启动参数与默认值）：<https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/configuration.md>
- 高级用法（并发会话、连接已有 Chrome、Android 调试）：<https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/advanced-usage.md>
- CLI 说明：<https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/cli.md>
- npm 包：`chrome-devtools-mcp`
- 协议：Model Context Protocol（MCP，默认 stdio）
- 仅支持：Google Chrome / Chrome for Testing
- License：Apache-2.0
- 数据收集说明：Google Privacy Policy《[Privacy](https://policies.google.com/privacy)》
