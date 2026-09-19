---
title: "chrome-devtools-mcp 完全指南：让 AI 编程助手掌控 Chrome DevTools"
date: "2026-04-18T11:35:00+08:00"
slug: "chrome-devtools-mcp-ai-coding-agents-guide"
github_repo: "ChromeDevTools/chrome-devtools-mcp"
source_key: "gh:ChromeDevTools/chrome-devtools-mcp"
aliases:
  - "/posts/tech/chrome-devtools-mcp/"
  - "/posts/tech/chrome-devtools-mcp-ai-browser-control/"
  - "/posts/tech/chrome-devtools-mcp-ai-coding-agent-chrome/"
  - "/posts/tech/chrome-devtools-mcp-ai-coding-agents/"
description: "ChromeDevTools/chrome-devtools-mcp 解读：pageId 与 uid 两级寻址如何让智能体稳定操作浏览器，57 项工具盘点与默认可见集开关、CLI 行为边界、隐私脱敏与报错对照。"
draft: false
lastmod: "2026-09-19T00:00:00+08:00"
categories: ["技术笔记"]
topics: ["coding-agent"]
tags: ["MCP", "Chrome DevTools", "Puppeteer", "AI Agent", "浏览器自动化", "Claude"]
---

`chrome-devtools-mcp` 的价值不在"给大模型加了一层协议壳"。它做的是把 Chrome DevTools 的调试能力改写成智能体用得上的两级寻址：pageId 定位标签页，uid 定位元素，而 uid 来自可访问性树快照，不是 CSS 选择器。

先说它不是什么东西。它不是又一个 headless 浏览器，不是没有主张的 Puppeteer（Node.js 浏览器驱动库）封装，也不是测试框架。它是 Google Chrome 团队维护的一个 Model Context Protocol（模型上下文协议）服务端，服务对象是 Antigravity、Claude、Cursor、Copilot 这类编码智能体，让它们能控制并检查一个实时运行的 Chrome。它按 MCP 这套开放标准暴露应用程序接口，不绑定某一家模型。仓库现在的名字是 "Chrome DevTools for agents"，npm 包仍叫 `chrome-devtools-mcp`。

判断它值不值得接进工作流，看三件事：两级寻址解决了什么老问题，57 项工具里有多少真用得上，以及它把哪些数据交给了谁。

## 各取所需

- 只想把服务跑起来：看「部署与接入」和「环境要求」两节。
- 想知道它跟 Puppeteer 脚本的差别在哪：读完「三层技术栈」和「pageId 与 uid」这两节就够了。
- 在评估能力边界：「工具全家福」给出按能力分组的清单，「隐私边界」列出默认往外发的数据。
- 习惯在命令行里操作浏览器：「CLI 模式」（命令行工具模式）说明守护进程行为，以及哪些工具在那里没有对应子命令。
- 关心词元开销：看「性能实践」。
- 起不来、连不上、跑一半报错：看「排障」。

## 三层技术栈

这条链路里有四个名字容易被混为一谈，先把职责钉死。

```text
┌─────────────────────────────────────────────────┐
│        AI Coding Agent (Claude/Copilot)         │
│              ↑ MCP 协议 (JSON-RPC)              │
├─────────────────────────────────────────────────┤
│         MCP Server (chrome-devtools-mcp)        │
│  ┌─────────────────────────────────────────┐    │
│  │  工具层：navigate_page / screenshot /…  │    │
│  ├─────────────────────────────────────────┤    │
│  │   DevTools Frontend（性能/Insight）      │    │
│  ├─────────────────────────────────────────┤    │
│  │       Puppeteer（Chrome 进程管理）       │    │
│  └─────────────────────────────────────────┘    │
├─────────────────────────────────────────────────┤
│              Chrome Browser (独立进程)           │
│           通过 CDP WebSocket 接收命令             │
└─────────────────────────────────────────────────┘
```

图里的 DevTools Frontend 指 Chrome DevTools 的前端界面代码。四层各自负责什么：

- **CDP（Chrome DevTools Protocol）**：Chrome 自带的调试协议，走 WebSocket 连接。能力覆盖导航、网络、控制台与性能追踪。本文说"协议"时若无特别说明，指的是它。
- **Puppeteer**：负责启动与关闭 Chrome、维护连接、等 DOM 稳定。它是 CDP 之上的高级封装。
- **DevTools Frontend**：`chrome-devtools-mcp` 复用它录制 trace，并从 trace 里提取性能洞察。这是它比自研采集脚本便宜的地方——分析逻辑与 DevTools 面板同源。
- **Model Context Protocol**：智能体与外部工具之间的 JSON-RPC 通道。服务端声明一组工具的名称、参数模式（schema）与返回格式，智能体读完描述自行决定调用哪一项，路由不靠人工。

MCP 的一次工具调用长这样：

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "navigate_page",
    "arguments": {
      "pageId": 1,
      "url": "https://example.com",
      "type": "url"
    }
  },
  "id": 1
}
```

结论：这个项目真正的工程量在 Puppeteer 之上那层——把调试能力切成地址稳定、返回可读的函数。浏览器控制本身它一行没重造。

## pageId 与 uid：把选择器问题换成快照问题

与传统 Puppeteer 脚本相比，差别集中在两处寻址设计上。

**pageId 定位标签页。** 除 `list_pages` 外，几乎所有工具都要求传一个数字 pageId。多标签场景下，"作用在哪个页面"必须是显式参数，而不是"当前激活的那个"这种运行时状态。工作流因此固定为先 `new_page` 或 `list_pages` 拿到 id，再往下传。这层路由默认开启（`--pageIdRouting`），多个会话共用一个服务端实例时靠它把调用分发到各自的标签页；`--no-page-id-routing` 会退回"只路由到当前选中页"的老行为。

**uid 定位元素。** 交互类工具（`click`、`fill`、`hover`、`drag`、`upload_file`）不吃 CSS 选择器。先调 `take_snapshot` 拿到页面的可访问性树文本快照，快照给每个元素分配一个 uid，交互时传这个 uid。

为什么绕这一圈？选择器是脆弱断言。模型猜 `#main > div:nth-child(3) > button` 一旦 DOM 改动就点错，而且它看不到页面，只能基于上一次返回的文本推断。快照给的是当前页面实际存在、且系统认得的元素句柄。代价写在流程里：交互前必须多一次快照调用，页面重绘后旧 uid 作废，得重新取。官方同时建议"能快照就别截图"——快照是文本，占的词元（token）少，截图贵。

还有一条一致的设计取向：重的产物默认落盘再给路径。`take_screenshot`、`performance_start_trace`、`evaluate_script`、`get_network_request` 都有 `filePath` 一类的参数，不给就把内容内联返回。仓库的设计原则文档把这条叫 "Reference over Value"，配套的还有"返回语义摘要而非五万行 JSON"。

## 工具全家福

v1.9.0 版共 57 项，按能力分 11 组。下表是分组与数量，逐项签名以官方 [tool-reference](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/tool-reference.md) 为准；main 分支已把调试组扩到 9 项（新增 `get_css_styles`，返回某个元素的匹配规则、内联样式与层叠信息，用来判断某条属性为什么生效、为什么被覆盖），清单总数随之变成 58。

| 能力组 | 数量 | 成员 |
|--------|------|------|
| 输入自动化 | 10 | `click` / `drag` / `fill` / `fill_form` / `handle_dialog` / `hover` / `press_key` / `type_text` / `upload_file` / `click_at` |
| 导航自动化 | 6 | `list_pages` / `new_page` / `navigate_page` / `select_page` / `close_page` / `wait_for` |
| 模拟 | 2 | `emulate` / `resize_page` |
| 性能 | 3 | `performance_start_trace` / `performance_stop_trace` / `performance_analyze_insight` |
| 网络 | 2 | `list_network_requests` / `get_network_request` |
| 调试 | 8 | `take_snapshot` / `take_screenshot` / `evaluate_script` / `list_console_messages` / `get_console_message` / `lighthouse_audit` / `screencast_start` / `screencast_stop` |
| 内存 | 13 | 堆快照的拍摄、比较与查询一族，见下文 |
| 扩展 | 5 | `install_extension` / `list_extensions` / `reload_extension` / `uninstall_extension` / `trigger_extension_action` |
| 渐进式 Web 应用（PWA） | 4 | `get_os_app_state` / `install_pwa` / `launch_pwa` / `uninstall_pwa` |
| 第三方工具 | 2 | `list_3p_developer_tools` / `execute_3p_developer_tool` |
| WebMCP | 2 | `list_webmcp_tools` / `execute_webmcp_tool` |

数量是清单上限，不是默认可见集。真正的默认集比 57 小得多：内存那 13 项要 `--memoryDebugging`（别名 `--experimentalMemory`）；扩展、PWA、第三方三组分别要 `--categoryExtensions`、`--categoryPwa`、`--categoryExperimentalThirdParty`；`screencast_*` 要 `--experimentalScreencast`，且录制依赖 ffmpeg 在 MCP 服务端的 PATH 里；`click_at` 要 `--experimentalVision`。这些开关默认全是 false。扩展与 PWA 两组还要求管道连接：用 `--browserUrl`、`--wsEndpoint` 或 `--autoConnect` 连一个已在运行的 Chrome 时拿不到它们，官方说明这一限制要到 Chrome 149 才解除。

按上表算：默认暴露的是输入 10 + 导航 6 + 模拟 2 + 性能 3 + 网络 2 + 调试 7 = 30 项；打开 `--memoryDebugging` 到 43，再打开扩展与 PWA 两组到 52。别按 57 项预估智能体每次要读多少工具描述，那直接反映在接入后的首轮词元开销上。客户端里能列出的工具清单才是准数，这 30 项是按上表默认值推出来的。

输入组里值得单独说的：

- `fill_form` 一次填多个表单控件（输入框、下拉、复选与单选）。官方描述里用了 ALWAYS prefer，理由是比逐个 `fill`/`click` 更快、更稳、占的对话轮次更少。
- `handle_dialog` 处理 `alert`/`confirm`/`prompt` 三类浏览器对话框（分别是告警、确认与提示词输入）。`action` 取 accept 或 dismiss，输入框里要填的文本走 `promptText`。
- `type_text` 与 `press_key` 是键盘路径，适用于 `fill` 填不进去的场景，比如快捷键和特殊组合键（`Control+Shift+R`）。
- `click_at` 按坐标点击，需要 `--experimentalVision=true` 启动。
- `upload_file` 的文件路径相对浏览器所在主机解析，不在 MCP 客户端那一侧——浏览器跑在远端时这是最常见的坑。

导航组里 `wait_for` 等的是页面上出现指定文本（传一组候选，任一命中即返回），不是"等 3 秒"。`new_page` 的 `isolatedContext` 决定新页面进哪个浏览器上下文：同名共享 cookie 与存储，不同名完全隔离。`close_page` 关不掉最后一个页面。

## 两条值得单看的链路

**Source Map 还原。** 线上跑的是压缩代码，控制台报错的行列号指向打包产物，对排障几乎无用。`list_console_messages` 带 `includeStackTraces` 参数，能取到栈信息；打包产物配了 `.map` 文件时，报错位置会映射回 TypeScript 源码。`--sourceMaps` 开关控制该能力，默认开。

智能体拿到"哪个组件的哪一行"之后，才有机会直接改对；只拿堆栈摘要，多半只能在猜测里挑一个。这条链路的准确度取决于 Source Map 是否可达，私有源未上传时它也无法还原。

**性能洞察与真实用户数据。** `performance_start_trace` 录 Core Web Vitals（LCP、INP、CLS）相关的 trace，可配 `reload` 与 `autoStop`；随后 `performance_analyze_insight` 按 `insightSetId` 与 `insightName` 钻取某一条，例如 `DocumentLatency` 或 `LCPBreakdown`。

性能工具会把被分析页面的 URL 发给 Google 的 CrUX（Chrome UX Report）接口，换回真实用户体验数据，与刚录的实验室数据并排展示。CrUX 汇总的是真实 Chrome 用户贡献的性能数据，你平时拿不到同口径的线上数字，这份对照才值钱；否则用 `--no-performance-crux` 关掉。

`lighthouse_audit` 不给性能分。官方描述写明它覆盖可访问性、SEO（搜索引擎优化）、最佳实践与 agentic browsing 四项，性能审计要跑 `performance_start_trace`。把它当 Lighthouse 全能入口的人会拿不到期望的报表。

## 串一遍：让智能体查一处表单提交后的 500

把机制放回一次真实工作里。假设前端改了登录页，提交后偶发失败，你让智能体去复现并定位。

```text
1. new_page(url="https://staging.example.com/login")   → 返回 pageId=1
2. take_snapshot(pageId=1)                             → 用户名框 uid=3、密码框 uid=7、按钮 uid=9
3. fill_form(pageId=1, elements=[{uid:3,value:"..."}, {uid:7,value:"..."}])
4. click(pageId=1, uid=9)                              → 提交
5. wait_for(pageId=1, text=["Server Error"])           → 确认失败分支
6. list_network_requests(pageId=1, resourceTypes=["Fetch","XHR"])
   → 定位到 POST /api/login 状态 500
7. get_network_request(pageId=1, reqid=42, responseFilePath="./login-500.network-response")
8. list_console_messages(pageId=1, includeStackTraces=true)
   → 栈指回 src/auth/LoginForm.tsx:88
```

第 7 步把响应体写成文件而不是塞回对话，第 8 步靠 Source Map 把位置还原到源码。整条链上没有任何一处需要人来猜选择器或者手点浏览器——但前提是你给了它 staging 地址，并且这个环境允许被真实登录。

同一套动作写成 Puppeteer 脚本也能跑，差别在于：脚本要预先知道页面结构，改一版 DOM 就得回去改代码；这里的第 2 步是运行时现取的，页面变了 uid 跟着变。反过来，脚本的执行成本确定，而智能体每一步都要经过一次模型调用，链越长越贵，也越容易在中途跑偏。

## 环境要求

| 依赖 | 要求 | 说明 |
|------|------|------|
| Node.js（JavaScript 运行时） | LTS（长期支持版） | 官方要求 |
| Chrome | 当前稳定版或更新 | 官方只保证 Google Chrome 与 Chrome for Testing；其他 Chromium 内核浏览器可能遇到意外行为 |
| npm | 随 Node.js 自带 | 安装与 `npx` 启动用 |

## 部署与接入

最省事的接入方式是在支持 Model Context Protocol 的客户端配置里加一段：

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

`@latest` 让客户端每次都用最新版，这是官方写法。只需要基础页面操作的话，加 `--slim` 换成精简工具集——只有导航、求值、截图三项，`--headless` 让浏览器不带界面：

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

各客户端的官方安装命令：

- Claude Code（MCP 方式）：`claude mcp add chrome-devtools --scope user npx chrome-devtools-mcp@latest`
- Claude Code（插件方式，工具加技能一起装）：`/plugin marketplace add ChromeDevTools/chrome-devtools-mcp`，再 `/plugin install chrome-devtools-mcp@chrome-devtools-plugins`
- Codex：`codex mcp add chrome-devtools -- npx chrome-devtools-mcp@latest`
- Copilot / VS Code：命令面板执行 `Chat: Install Plugin From Source`，填仓库名 `ChromeDevTools/chrome-devtools-mcp`
- Cursor：`Settings → MCP → New MCP Server`，贴上面的 JSON
- Gemini CLI：`gemini mcp add -s user chrome-devtools npx chrome-devtools-mcp@latest`

装完重启客户端。第一次调用给个固定示例，别用"随便打开个网页"这种开放式提示词（prompt）：

```text
Check the performance of https://developers.chrome.com
```

这是官方文档里的验收示例。通过标准也明确：浏览器被拉起，跑完一次性能 trace，返回一段洞察摘要而不是原始数据。看不到这些就说明还没接通。服务端不会在连接建立时启动浏览器，要等智能体真的调用需要浏览器的工具才拉起——连上不等于浏览器已开。

### CLI 模式

同一个包附带一个实验性命令行工具（CLI），不开 MCP 也能操作浏览器：

```sh
npm i chrome-devtools-mcp@latest -g
chrome-devtools status          # 看守护进程在不在线

chrome-devtools new_page "https://example.com"
chrome-devtools navigate_page 1 --url "https://web.dev"
chrome-devtools take_screenshot 1 --filePath shot.png

chrome-devtools click 1 "element-uid-123"
chrome-devtools fill 1 "input-uid-456" "search query"

chrome-devtools lighthouse_audit 1 --mode snapshot
chrome-devtools list_pages --output-format=json

chrome-devtools stop
```

CLI 是客户端，后台跑着一个 `chrome-devtools-mcp` 守护进程，Linux/macOS 用 Unix socket（套接字），Windows 用命名管道。首次调用自动拉起，之后复用同一实例，页面和 cookie 都留着。`start` 的默认值与 MCP 服务端不同：headless 默认开，`--isolated` 默认开（除非你给了 `--userDataDir`）。

两条限制记牢：

- CLI 只暴露无需额外参数即可调用的工具，`--categoryExtensions` 相关的扩展类工具因此不在 CLI 里。
- `wait_for` 与 `fill_form` 被排除在 CLI 生成之外，用不了。别照抄 MCP 的调用顺序写脚本：用 shell 的 `sleep` 顶替等待，只是把稳定的流程换成随机失败的流程。

CLI 默认放开整个文件系统访问，`chrome-devtools start --workspace=/path/to/project` 可以把文件类工具限制在指定目录，需要时可重复传该参数。让智能体生成脚本时，这行参数值得默认加上。

## 隐私边界

官方把前两条写进了免责声明，三条机制要分开看：内容暴露、数据外发、主动收口。

第一条关于内容暴露。这个 MCP 服务端会把浏览器实例里的内容开放给客户端检查、调试乃至修改。别在这个受控浏览器里登录你不想让智能体看见的账号——它的 cookie、localStorage、已打开的页面全都是可读的。默认情况下用户数据目录（Chrome 的缓存目录）落在 `$HOME/.cache/chrome-devtools-mcp/chrome-profile`，也就是说登录态会留在磁盘上。要一次性会话就用 `--isolated`（临时目录，关浏览器即删）。

第二条关于外发数据。CrUX 查询发的是页面 URL，用 `--no-performance-crux` 关；使用统计由 Google 收集（工具调用成功率、延迟、环境信息），用 `--no-usage-statistics` 关，设置 `CI` 或 `CHROME_DEVTOOLS_MCP_NO_USAGE_STATISTICS` 环境变量也会关。两者互不相干：关掉 Chrome 浏览器的指标不等于关掉本工具的，反之亦然。还有一项更新检查默认开启，`CHROME_DEVTOOLS_MCP_NO_UPDATE_CHECKS` 关掉。

```jsonc
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--no-usage-statistics"]
    }
  }
}
```

第三条是主动收口。前面两个开关只是少发数据，下面这三个能限制智能体能看到什么，且默认全关：

- `--redactNetworkHeaders`：置 true 后，被认为是敏感的请求头在返回客户端前先脱敏。默认 false，即 `Cookie` 与 `Authorization`（授权）头原样回给智能体。
- `--blockedUrlPattern` / `--allowedUrlPattern`：按 URL Pattern 规范限制浏览器可访问的地址，连导航与子资源一起拦，命中禁用地址的标签页在连接时静默分离。allow 一侧需要 Chrome 149 以上。
- `--javascriptEvaluation=false`：关掉页内 JS 执行，同时停用 `evaluate_script`、slim 的 `evaluate` 与 `navigate_page` 的 `initScript`，并禁止 `javascript:`、`data:`、`vbscript:` 这类 URL。

三者共同回答一个问题：智能体读到的东西，能不能被限制在它该读的范围内。答案是可以，但要你自己开。

## 性能实践

实践中省词元、省轮次的几条：

1. 多字段表单一次 `fill_form`，别拆成串行 `fill`。
2. 复用浏览器实例，别每条命令都重开；需要干净会话用 `isolatedContext` 开新上下文。
3. trace 只录关心的区间，在关键代码段前后 start/stop；用 `filePath` 流式落盘，别把整个生命周期塞回对话。
4. 只需要读数据的 `evaluate_script` 调用传 `waitForStableDom=false`，默认值会等 DOM 安定，白等一轮。
5. 重的返回值（截图、trace、响应体）一律走 `filePath`。截图想省得更彻底，用 `--screenshotFormat` 把默认格式定为 JPEG 或 WebP，再用 `--screenshotMaxWidth` 压尺寸——官方说明图片词元随像素数增长，不只随字节数。
6. 用不到的能力组直接踢出清单：`--categoryEmulation`、`--categoryPerformance`、`--categoryNetwork` 默认 true，设成 false 即从工具列表里移除。少了 20 项工具描述，比事后压缩返回值便宜。

## 排障

卡住时先按错误字符串定位，官方排障文档给出的对应关系如下：

| 报错 | 原因与处置 |
|------|-----------|
| `Target closed` | 浏览器没能起来。先关掉已在跑的 Chrome 实例，确认装的是最新稳定版 |
| `Error [ERR_MODULE_NOT_FOUND]: Cannot find module ...` | Node.js 版本不受支持，或 npx 缓存损坏。清缓存后重装 |
| 容器 / CI 里 Chrome 立即退出 | Chrome 不能以 root 运行。镜像里建一个非特权用户，用 `USER` 切过去 |
| 客户端开了沙箱（macOS Seatbelt、Linux 容器）起不来 Chrome | 该工具自己也要创建沙箱。关掉对这个服务端的沙箱，或改用 `--browser-url` 连一个沙箱外手动启动的 Chrome |
| `--autoConnect` 下 `ProtocolError: Network.enable timed out` | 服务端没能与那个 Chrome 握手。需要 Chrome 144 以上且已在运行，在 `chrome://inspect/#remote-debugging` 里开启远程调试并在弹窗中放行，且没有别的进程占着同一调试端口 |
| `Element uid "x" not found on page N` / `Element with uid "x" was detached or no longer exists on the page. Please take a new snapshot with take_snapshot.` | 旧快照作废。后者已经把补救动作写进错误文本，正是设计原则里的 "Self-Healing Errors" |

卡住时的通用顺序：

- `chrome-devtools status` 看守护进程状态，连接失败或挂起先 `chrome-devtools stop` 再重试。
- 要详细日志：`DEBUG=* chrome-devtools list_pages`；MCP 配置里也可以用 `NODE_DEBUG` 环境变量。
- 找不到浏览器：用 `--executablePath`（简写 `-e`）指定 Chrome 可执行文件路径。
- 装完不生效：先确认 Node.js 是 LTS、Chrome 不低于当前稳定版。
- 第二个服务端实例起不来或连不上：默认的 user data directory 同一时刻只允许一个浏览器占用。多套独立会话要么各自 `--isolated`（临时目录，用完即删），要么各给一个 `--userDataDir`。

标签数量也要留意：官方说明 Chrome 149 及以前，未加载或已冻结的标签会引发连接问题，而这个工具会把所有标签强制加载。挂着几百个标签的浏览器实例不建议接进来。

## 常见疑问

**为什么交互工具不认 CSS 选择器？** 设计使然，见上文快照一节。先 `take_snapshot` 再 `click`。

**几乎每个工具都要 pageId，是不是多余？** 多余与否取决于一个服务端实例被几个会话共用。默认它按 pageId 显式路由；关掉路由参数才退回"只作用于当前选中页"。会话越多，显式寻址越省事。

**会往 Google 发数据吗？** 两个独立机制：CrUX 查询与使用统计，各有开关。见「隐私边界」。

**能同时开多个浏览器实例吗？** 一个服务端只管一个浏览器；它的设计取向是在这一个实例里用 `isolatedContext` 做多套互不可见的会话。真要并行多浏览器，就起多个服务端进程，并各自处理 user data directory 冲突。

**`fill_form` 为什么在 CLI 里找不到？** CLI 不生成需要复合参数的工具，`fill_form` 与 `wait_for` 都在排除之列。

**Lighthouse 报告里没有性能分？** 正常。`lighthouse_audit` 明确不含性能项，性能要另跑 trace。

## 什么时候不必用它

- 只做本地渲染、把浏览器当渲染器的批处理任务，直接用 Puppeteer 脚本更省事，不必绕 MCP 与快照两层。
- 要接 CI 做回归测试的，Playwright（浏览器自动化软件开发包）一系的测试 runner 更合适：断言、并行、轨迹回放都是现成的。本项目的 Lighthouse 与 trace 能力对测试流水线是补充，不是替代。
- 智能体只需要"打开页面、取个标题"这类轻操作，`--slim` 的三项工具就够，不必载入全量清单。
- 页面上有敏感凭据、或目标站点明确不接受自动化访问时，别接。

反过来，值得接的场景也很具体：需要智能体读网络请求与控制台报错来改前端代码；需要性能 trace 与洞察而不想自己写采集脚本；需要复用本机已登录的浏览器会话；需要让智能体加载并触发浏览器扩展。

## 五道题自测

1. 智能体拿到 `Element uid ... not found on page` 这类错误，你第一步调哪个工具、为什么？
2. 关掉 Chrome 浏览器的使用统计，能否同时关掉本工具的上报？为什么？
3. 一次 `fill_form` 和四次 `fill`，除了轮次还有什么差别？
4. `lighthouse_audit` 拿不到性能分，接下来调哪个工具？
5. CLI 里为什么没有 `wait_for`，你打算怎么补这个语义？

答案在上文对应小节里。第 2 题的关键词是两个开关互相独立，第 5 题的关键词是复合参数不参与 CLI 生成。

## 下一步

接通之后，有三件事值得立刻动手试，各自会撞上上面讲过的一个机制：

1. 把「部署与接入」那条验收提示词真跑一遍，看返回的洞察摘要里有几条 `performance_analyze_insight` 可以继续钻。
2. 连做两次 `take_snapshot`，中间用 `evaluate_script` 往页面里插一个按钮，观察第二次的 uid 怎么变。
3. 用 `--memoryDebugging` 起一个开了堆快照工具的服务端，录两次快照，再让智能体自己解释哪里在漏。

## 维护与复现

- 本文事实来自仓库 `chrome-devtools-mcp`，快照为 main 分支 2026-09-18 提交、npm 已发布的 v1.9.0（2026-09-08）。工具组数量与参数以官方文档为准。
- 逐项签名看 [tool-reference](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/tool-reference.md)，精简模式看 [slim-tool-reference](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/slim-tool-reference.md)，启动参数看 [configuration](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/configuration.md)。
- 上游更新后最容易失效的是四处：调试组的数量与成员、各开关的默认值、CLI 排除工具清单、`lighthouse_audit` 的覆盖范围。
- 改动时四处标题都要对得上：「各取所需」的条目、「工具全家福」的分组表、「排障」里的错误字符串、本节标题本身。按标题关键词搜，别按行号。

| 参考资源 | 链接 |
|------|------|
| 仓库 | https://github.com/ChromeDevTools/chrome-devtools-mcp |
| npm 包 | https://www.npmjs.com/package/chrome-devtools-mcp |
| CLI 文档 | https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/cli.md |
| 客户端配置指南 | https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/client-configurations.md |
| 排障指南 | https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/troubleshooting.md |
| 设计原则 | https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/design-principles.md |
| MCP 规范 | https://modelcontextprotocol.io |
| Puppeteer 文档 | https://pptr.dev |
| Chrome DevTools Protocol | https://chromedevtools.github.io/devtools-protocol/ |
