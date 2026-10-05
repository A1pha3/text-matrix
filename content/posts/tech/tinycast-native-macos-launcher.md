---
title: "Tinycast：一个不到 100 MB 内存的全原生 macOS 启动器"
date: 2026-09-18T03:40:00+08:00
lastmod: 2026-10-01T00:00:00+08:00
slug: "tinycast-native-macos-launcher"
github_repo: "abue-ammar/tinycast"
source_key: "gh:abue-ammar/tinycast"
description: "Tinycast 用 Swift 6 与 SwiftUI/AppKit 写成，零第三方依赖、无遥测、内存低于 100 MB，还能用系统自带的 JavaScriptCore 直接运行 Raycast 扩展并渲染为原生界面。本文拆解它的兼容实现、工程约束与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["macOS", "Swift", "启动器", "开源软件", "效率工具"]
---

## 核心判断

macOS 启动器这个品类长期被两极占据：一极是 Raycast 这样的重量级选手，功能全面但随扩展生态持续膨胀；另一极是系统自带的 Spotlight，轻，但定制能力有限。Tinycast 走的是第三条路：**用 Swift 6 + SwiftUI/AppKit 写一个全原生的启动器，零第三方依赖、无遥测、内存预算写死在 100 MB 以内，同时用系统自带的 JavaScriptCore 直接运行已有的 Raycast 扩展，把扩展的 React 界面渲染成原生 SwiftUI**。

这个组合的卖点不是"更快"或"功能更多"，而是承接资产：你已经装了、配好了一批 Raycast 扩展，Tinycast 让这些投入换一个更小的宿主继续生效。项目 2026 年 6 月 29 日创建，截至 2026 年 10 月 1 日约 7,800 stars、400 forks，三个月发了 105 个 release——stable 渠道最新是 v0.11.3，beta 渠道基本保持日更。由一位主要作者主导，外部贡献经严格的流程 gate 进来。

## 系统地图

Tinycast 的功能面已经超出"启动器"的传统盘面。按实现方式分四块看，比按功能清单看更清楚：

| 板块 | 覆盖内容 | 实现要点 |
|---|---|---|
| 启动与检索 | 应用启动、模糊搜索、每应用热键、文件搜索、词典查询、Emoji | 文件搜索走 Spotlight、只搜你指定的文件夹，自己不建索引；词典读系统词典 |
| 效率命令 | 剪贴板历史、计算器（含实时汇率与加密货币）、Quicklinks、Snippets、自定义命令、Apple Shortcuts、窗口管理（34 种 Rectangle 风格操作）、系统操作、应用卸载 | 全部本地执行；剪贴板 OCR 在独立 helper 进程完成 |
| 日历与笔记 | 下一个会议显示在空面板和菜单栏、一键入会或自动入会、Markdown 笔记浮动编辑器 | 接系统 CalendarStore；笔记是纯 Markdown 文件，TextKit 2 边写边渲染 |
| AI 与扩展 | AI 聊天、选中文本快捷操作、Raycast 扩展运行时、MCP 工具调用 | 全部默认关闭；API key 与 OAuth token 只存登录钥匙串 |

最后一块是它和所有同类工具拉开差距的地方，下面单独展开。

## Raycast 扩展兼容：不是"类似"，是真的跑

很多启动器宣传"兼容 Raycast"，指的是提供相似的 API 让开发者重写。Tinycast 的路子完全不同：**它运行的就是 Raycast 自己构建出来的产物**。一个 Raycast 扩展命令是 esbuild 打包好的单个 CommonJS 文件，只是把 `react`、`@raycast/api` 和 Node 内置模块声明为外部依赖——Tinycast 恰好补上这三样，然后跑这个 bundle，把它产出的 React 树渲染成原生界面。没有 Electron，没有浏览器，没有 Node.js。

拆开看有三层：

- **JavaScriptCore 做引擎**。JSC 随 macOS 自带，嵌入零二进制体积；文档对比过 QuickJS 方案，要多背约 1 MB 还搭一套构建系统，被否了。裸 `JSContext` 缺 `console`、`fetch`、`URL`、流、WebSocket 这些 Web/Node 设施，由一个约 200 KB 的生成运行时（`RaycastRuntime.generated.js`，内含 React 19 + react-reconciler + `@raycast/api` shim + Node polyfill）在构建期生成并提交进仓库——所以编译 Tinycast 本身不需要 Node。
- **Swift 宿主供能力**。扩展调用剪贴板、存储、toast、网络、exec 时，经桥接由 Swift 侧服务：`fetch` 走 URLSession，`fs`/`child_process`/`crypto`/`zlib` 各有原生实现，WebSocket 用 `URLSessionWebSocketTask`，连 `.local` 域名解析都由系统 mDNSResponder 代答，不引入任何多播权限。
- **界面归 SwiftUI**。扩展声明的 List、Grid、Form、Detail、ActionPanel 逐一对到原生控件；`__slot` 约定让"元素作为 props 传入"的 React 模式能序列化成结构树，函数 props 变成可派发的句柄。

兼容度有实测数字：作者用一台开发机上真实安装的 37 个扩展测过，**32 个扩展、147 个 view 命令中的 114 个能正常启动渲染**（OAuth 支持是测量之后落地的，3 个 OAuth 扩展未计入，文档注明引用前应重测）。不支持的部分也列得明白：依赖 Raycast PKCE 代理的登录、`AI`/`BrowserExtension`/`WindowManagement` 这三个 API、`net`/`tls` 裸 socket、流式 HTTP——这些场景调用时会抛出带原因的错误，而不是静默失败。

安全模型跟着来：扩展支持默认关闭，开启时明确确认一次，因为"开启就是同意运行第三方代码"；前台命令独占一个 `JSContext`，退出即整个丢弃（文档测得热启动约 7 ms），正在运行的命令持有 JS 引擎，是整个应用唯一的常驻内存开销。

扩展从哪来？三条路：**从 Raycast 导入**——直接复制本地已构建的 bundle，不编译、不需要 Node 和网络，同时扫描 `~/.config/raycast` 和 Raycast Beta 的 `raycast-x` 两个目录；**搜注册表**——Raycast Store 官方前端接口加任意 GitHub 仓库布局，从源码安装时直接调 `ray build` 并跳过生命周期脚本；**指定本地文件夹**——适合自己刚 `ray build` 完的扩展。配置迁移读 Raycast 的 `.rayconfig` 导出文件（RAYCFG3 容器，AES-256-GCM 加 scrypt 派生密钥），quicklinks 合并进库而非替换，`{Query}` 占位符自动改写成 Tinycast 的 `{argument}`。

## AI 与 MCP：自带路由，也接你已有的账号

AI 部分比"填 API key"丰富。模型选择器上有三类路由：**已安装的 AI 工具**——Codex、Claude、Grok、OpenCode、Cursor 各自独立开关（默认全关），走的是你机器上已有的登录态；**Apple Intelligence**——可用时作为默认路由；**API 连接**——自带 key 的 OpenAI 兼容端点，key 只存登录钥匙串，远程端点强制 HTTPS（仅 loopback 豁免）。每个对话锁定自己的模型，面板内的 Quick AI 和独立 AI Chat 窗口共享一份历史，⌘J 随时交接。

工具调用走 MCP：把远程 HTTPS 端点或本机命令注册为 MCP 服务器，工具按命名空间暴露给模型。API 路由下 Tinycast 自己当 MCP 客户端；Codex/Claude 路由下由它们的 CLI 当客户端，Tinycast 负责供服务器。信任模型是三档——首次调用弹三方对话框，Always Allow 永久放行、Allow This Chat 仅限当前会话、Don't Allow 单次拒绝，Esc 永远不会持久化决定。每轮工具调用次数有上限（默认 25，可调到 10/50/100/不限），防止模型只调工具不回答。

这些能力全部默认关闭，关闭是彻底的：不建历史数据库、不起任何进程、不给模型暴露任何工具名，且 AI/MCP 开关和服务器列表都被排除在设置备份之外——备份文件永远不会替你打开一个能执行代码的功能。

## 为什么能小：预算写进纪律

Tinycast 的小一半靠选型，一半靠纪律。架构文档写得很清楚，每个成熟子系统收敛到同一个四层结构：

| 层 | 职责 | 约束 |
|---|---|---|
| Model（PURE） | 决策：排序、匹配、计算、解析 | 只用 Foundation，禁 import AppKit/SwiftUI，时钟网络文件系统全是注入参数 |
| Service（EFFECT） | 平台 I/O：每个 `AXUIElement` 调用、CGEventTap、网络请求都在这层 | 每功能一个文件夹 |
| Observable State | 39 个 `@MainActor @Observable` 状态类型 | 不用 ObservableObject/@Published |
| View | SwiftUI 界面与协调器 | 声明式、薄、不持策略 |

这套分层不是靠自觉：测试 harness 直接编译交付源码而非副本，Model 层一旦 import 了 AppKit，harness 立刻编译失败。整个应用跑在 Swift 6 语言模式，数据竞争是编译错误；全库只有一个 actor，重活和 I/O 推给 `Task.detached`。

内存上最讲究的一处是剪贴板 OCR：它是唯一会离开主进程的功能。识别文本时，每个剪贴板项起一个独立的 `ClipboardTextHelper` 进程跑完即回收——Vision 和 PDFKit 的内存分配落在一个会退出的进程里，主进程始终干净。

纪律侧，贡献指南把 Non-negotiables 列在最前：内存低于 100 MB、零泄漏（面板关闭后回基线）、视觉改动必须附同窗口同操作的 before/after 视频、每个 PR 必须填 idle 和 peak 内存实测数字。没有 CI，全靠本地跑测试脚本和 lint。想加功能先开 issue 拿到 approved 标签才能动代码，不关联 approved issue 的 PR 打开即自动关闭——README 直说"功能集是刻意封闭的，别的启动器有不是加功能的理由"。

## 一个 Raycast 用户的迁移路径

把上面的机制串成一次真实迁移：

1. `brew install --cask tinycast` 装好，在 Settings → General 录一个全局热键呼出面板——到这一步它已经是一个可用的启动器加剪贴板工具。
2. 在 Raycast 里导出设置得到 `.rayconfig`，到 Tinycast 的 Backup 页选文件、输入 Raycast 给的导出密码（密码可在 Raycast 的设置里查看）。热键、剪贴板历史、quicklinks、snippets 各归各位，quicklinks 是并入不覆盖。
3. Settings → Extensions 打开扩展支持（确认一次），选 Import from Raycast。面板会扫描本机两个 Raycast 数据目录里已构建的 bundle，直接复制安装——这一步没有编译，几秒钟完事。之后在 Raycast 里新装的扩展，重开这个页面会提示"Raycast 有而 Tinycast 没有"。
4. 按热键，输入扩展关键词，回车。bundle 在 JavaScriptCore 里跑起来，React 树序列化成 JSON 过桥，SwiftUI 画出原生行——模糊过滤用的是启动器自己的匹配器，键盘导航和其他面板行为一致。
5. 需要状态类扩展常驻的（比如显示咖啡因状态的 Coffee），给单个命令开 background refresh，它按声明的间隔在后台无界面重跑，把副标题刷进启动器搜索行。

走完这条路的判断点在第 3、4 步之间：你常用的扩展在不在那 114/147 里，一试便知。

## 安装

通过 Homebrew 安装。先信任这个第三方 tap（Homebrew 对第三方源的新信任机制），再装对应机型：

```sh
brew trust --tap abue-ammar/tinycast
brew tap abue-ammar/tinycast
brew install --cask tinycast           # Apple silicon，macOS 26+
brew install --cask tinycast-universal # Intel，macOS 26
```

想跟日更 beta，装 `tinycast@beta`——独立 bundle ID，`Tinycast Beta.app` 与稳定版并存，设置和权限各自独立。Homebrew 每次安装和更新会自动清除隔离标记；从 Releases 页直接下 DMG 的话，应用是自签名的，手动清一次：

```sh
xattr -dr com.apple.quarantine "/Applications/Tinycast.app"
```

首次使用在 Settings → General 录全局快捷键；粘贴和关键词展开需要辅助功能权限，系统在首次用到时提示。剪贴板的关键词展开功能默认关闭，按键匹配完全在本地完成，不存储不上报。

主线要求 macOS 26（Tahoe），门槛相当激进。还在 macOS 15 Sequoia 上的用户有单独的 `tinycast-sequoia` cask，由发布工作流自动跟进，但对应的是 0.9.x 分支，功能集落后主线。

## 适用边界

- **macOS 26+**：老系统用户只能用功能落后的 Sequoia 分支。
- **扩展兼容有明确缺口**：依赖 Raycast PKCE 代理登录、需要 `AI`/`BrowserExtension`/`WindowManagement` API、要裸 TCP socket 或流式 HTTP 的扩展跑不了。官方维护着一份不支持清单，且给出原因。
- **AGPL-3.0**：个人使用无感，想基于它做商业分发的人需要认真对待传染条款；贡献者还要签一份贡献者许可与反馈协议。
- **一人主导、流程从严**：外部贡献存在但都要过 approved issue 和内存实测的 gate；没有 CI 意味着质量靠作者本人的发布纪律背书。指望它快速长出长尾功能的人会失望——封闭功能集是明文政策。

## 采用建议

在意内存占用、不喜欢 Electron、又已经积累了一批 Raycast 扩展的用户，现在就值得装——迁移成本接近零，最坏情况退回 Raycast，扩展原封未动。用扩展不多、只要启动器加剪贴板的用户，Tinycast 的功能面也覆盖得住，且比 Raycast 常驻轻得多。依赖上面列的缺口能力（尤其 Raycast AI 和需要裸 socket 的扩展）、或系统停在 Sequoia 的用户，观察即可；每月看一眼 release 列表，兼容面还在快速扩张。
