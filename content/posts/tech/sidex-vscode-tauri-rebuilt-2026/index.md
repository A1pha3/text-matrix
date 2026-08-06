---
title: "SideX：把 VSCode 拆了再用 Tauri 拼回去，然后瘦了 96%"
slug: sidex-vscode-tauri-rebuilt-2026
date: 2026-08-06T23:44:00+08:00
draft: false
tags: ["vscode", "tauri", "electron", "rust", "ide", "open-source", "review"]
categories: ["tech"]
description: "4 个月大、2652 stars 的 VSCode Tauri 重写版：从 Electron main process 到 Tauri Rust backend 的逐层映射、Rust 接管 fs/pty/git/search/sqlite 的工程哲学、以及它 0.1.3 早期版本的真实边界。"
keywords: ["sidex", "vscode", "tauri", "electron", "rust", "monaco", "xterm.js", "portable-pty", "open-vsx"]
github_repo: "Sidenai/sidex"
---

# SideX：把 VSCode 拆了再用 Tauri 拼回去，然后瘦了 96%

> "VSCode's workbench, without Electron."

如果让我给 2026 年开源 IDE 圈挑一个"最有胆"的标题，上面这行就是。

SideX 是一个 4 个月大、2652 stars、224 forks 的开源项目。它的作者做了一件听起来很疯狂、做完之后又觉得"为什么没人早点做"的事：**把 VSCode 的 TypeScript workbench 整个 port 出来，然后把 Electron 那一层拆掉，换成 Tauri + Rust**。

官方给的两个数字对比图是这样的：SideX **16.4 MB** vs Visual Studio Code **797.8 MB**。

你看到的不是 4 倍、不是 10 倍——是 **48 倍**。Electron 那层打包的 Chromium，单独占了 VSCode 几乎所有内存。SideX 把那一层砍掉，改用系统原生的 webview：macOS 上是 WKWebView（和 Safari 共享），Windows 上是 WebView2，Linux 上是 WebKitGTK。

读完 README、完整的 `ARCHITECTURE.md`、`package.json`、`src-tauri/Cargo.toml` 之后，我的判断是：**SideX 不是"又一个 Tauri Demo"**。它是把 Tauri 当作"VSCode 工程问题"的解药来开的方子。能不能治本，还得看几件事。

## 一、让人好奇的三个事实

在我继续之前，先摆三个让你盯屏幕看的数字：

- **2652 stars、4 个月大、224 forks**。一个 IDE 重写项目 4 个月拿到这个量级，**靠的不是"AI 写代码"，是"VSCode 这五个字母"**——VSCode 源码是 MIT 协议的（Code-OSS），任何人都可以合法 fork、改名、改壳。SideX 做的是把壳换成 Tauri。
- **2026-08-06 还在更新**（13 小时前最后一次）。版本号 **0.1.3**——是早期发布，但节奏对。
- **TypeScript 31 MB + Rust 3.4 MB**。这两个数字加在一起告诉你：**前端不是"借鉴"，是"直接 port"**（TypeScript 31 MB 不是几行代码的工作量，是整个 VSCode workbench）；**Rust 不是"装个壳"，是"接管所有 Node.js native module"**（fs/pty/git/file-watching/search-indexing/sqlite/process-management 全在 Rust 里）。

第三个数字最关键。一个 IDE 之所以"卡顿、占内存、启动慢"，90% 不是 TypeScript 写的 editor 慢，是 Electron 的 Chromium 在吃 CPU。SideX 用 Tauri 把 Chromium 干掉，VSCode 那个被诟病多年的内存问题**理论上**就消失了。

但"理论上"三个字，是我后面要花篇幅讲的事情。

## 二、它不只是一次"换壳"

我读完 README 之前，以为 SideX 是"VSCode 加 Tauri 启动器"那种浅层包装。读完不是。

`ARCHITECTURE.md` 里给了一张非常清醒的映射表，我把它重排一下：

### 2.1 进程模型的逐层对应

```
VSCode (Electron)                    SideX (Tauri)
─────────────────                    ─────────────
Electron Main Process        →       Tauri Rust Backend
  ├─ BrowserWindow           →       WebviewWindow
  ├─ ipcMain                 →       Tauri Commands + Events
  ├─ Menu/Dialog/Shell       →       Tauri Plugins
  └─ UtilityProcess          →       Rust async tasks / sidecars

Renderer Process             →       Tauri Webview (frontend TS)
  ├─ Workbench               →       Workbench (same TS)
  ├─ Monaco Editor           →       Monaco Editor (same)
  └─ Extension Host API      →       Extension Host API (ported)

Shared Process               →       Rust service layer
Extension Host               →       Sidecar process (in progress)
```

注意 "in progress" 这两个字——它出现在 `Extension Host`。这是 SideX 整个 0.1.3 版本**还没解决的最大一块**。我后面会讲。

### 2.2 Electron API 替换表（官方版本）

| Electron API | Tauri Replacement | Status |
|---|---|---|
| `BrowserWindow` | `WebviewWindow` | ✅ Ported |
| `ipcMain/ipcRenderer` | `invoke()` / `emit()` / `listen()` | ✅ Ported |
| `Menu/MenuItem` | `tauri::menu::Menu` | ✅ Ported |
| `dialog.*` | `@tauri-apps/plugin-dialog` | ✅ Ported |
| `clipboard` | `@tauri-apps/plugin-clipboard-manager` | ✅ Ported |
| `shell.openExternal` | `@tauri-apps/plugin-opener` | ✅ Ported |
| `Notification` | `@tauri-apps/plugin-notification` | ✅ Ported |
| `safeStorage` | Rust keyring crate | ⚠️ Partial |
| `protocol.*` | Tauri custom protocol | ✅ Ported |

**只有 1 个 Partial**——`safeStorage`（用于 token/密钥安全存储）。这是工程优先级，不是技术做不到。

### 2.3 VSCode 的 Layering 被完整保留

```
┌─────────────────────────────────────────────┐
│  code/        → Application entry (Tauri)   │
├─────────────────────────────────────────────┤
│  workbench/   → IDE shell                   │
│    ├── Feature contributions (contrib/)     │
│    ├── Services (services/)                 │
│    ├── Visual Parts (browser/parts/)        │
│    ├── Extension host API (api/)            │
│    └── Layout engine (browser/layout.ts)    │
├─────────────────────────────────────────────┤
│  editor/      → Monaco text editor core     │
├─────────────────────────────────────────────┤
│  platform/    → Platform services (DI)      │
├─────────────────────────────────────────────┤
│  base/        → Foundation utilities        │
└─────────────────────────────────────────────┘
```

**关键洞察**：VSCode 之所以能 port，不是 Tauri 多强，是 VSCode 自己的代码组织**早就准备好了**。`workbench/` → `editor/` → `platform/` → `base/` 这四层是 VSCode 十几年来迭代沉淀的分层，每一层职责清晰、依赖单向。SideX 把这个分层**完全保留**，只是把"承载这一切的运行时"从 Electron 换成了 Tauri。

这就是 README 里那句"**Follows VSCode's patterns — familiar if you've read the VSCode source**"的底气。你给 SideX 提 PR 时，VSCode 老兵上手零成本。

## 三、技术栈的"克制"

`package.json` 里 dependencies 一共 19 个（不算 devDependencies），我数了一下，挑几个有说法的：

| 包 | 作用 | 为什么是它 |
|---|---|---|
| `@tauri-apps/api ^2` | Tauri 2 官方 JS SDK | 不是 v1，是 v2（IPC + Window API 重写） |
| `monaco-editor ^0.52.2` | VSCode 用的同一个编辑器 | 不是 CodeMirror，不是 Ace |
| `@xterm/xterm ^5.5.0` + 8 个 addon | 终端 | 同一个 xterm.js，但启用 WebGL 渲染 + canvas/clipboard/fit/image/search/unicode11 等 addon |
| `vscode-textmate ^9.3.2` + `vscode-oniguruma ^2.0.1` | 语法高亮 + Oniguruma 正则 | 不是 Monaco 自带，是 VSCode 抽出来的独立包 |
| `@vscode/tree-sitter-wasm ^0.3.0` | Tree-sitter WASM（语法树） | 为未来高级语义分析留口 |
| `tas-client ^0.3.2` | VSCode Telemetry | 继承自 VSCode 的遥测管道 |
| `@microsoft/1ds-core-js` + `@microsoft/1ds-post-js` | VSCode 用的 1DS 遥测后端 | 一并继承 |

**一个被忽略的细节**：SideX 把 VSCode 用的 **1DS 遥测**（1st-party Data Science，Microsoft 内部的诊断遥测 SDK）也继承了。这意味着：
- 它不打算做"零遥测纯净版"
- 但 1DS 是开源的（`@microsoft/1ds-core-js`），不会偷偷上传数据
- 这是个"忠于原版"的取舍

`src-tauri/Cargo.toml` 那一侧也克制：

```toml
tauri = { version = "2.10.3", features = [
  "protocol-asset",
  "tray-icon",
  "devtools",
] }
tauri-plugin-log = "2"
tauri-plugin-dialog = "2"
tauri-plugin-shell = "2"

notify = { version = "7", features = ["macos_fsevent"] }   # 文件监听
portable-pty = "0.8"                                       # 跨平台 PTY
rusqlite = { version = "0.31", features = ["bundled"] }    # SQLite（embedded）
tokio = { version = "1", features = ["full"] }             # 异步运行时
hostname = "0.4"                                           # 主机名
```

**没看到**：
- 没看到 `serde_yaml` / `toml` 这种配置文件处理——说明配置走 Tauri 自带的 config
- 没看到 `reqwest` / `hyper`——HTTP 由 Tauri 内部处理或前端 fetch
- 没看到 `regex` crate 在 `dependencies`——搜索用的 `regex` 走 `dashmap + rayon + regex` 在 ARCHITECTURE.md 提到（在某个独立 crate 或 dev-dep）

**一个值得说一下的细节**：`notify` crate 启用了 `macos_fsevent` feature。FSEvents 是 macOS 内核级文件监听 API，比 Linux 的 inotify 更省电、比 Windows 的 ReadDirectoryChangesW 更原生。**SideX 在 macOS 上做文件监听是直接走内核的**，这跟 VSCode 在 Electron 里的 Node.js `fs.watch` 形成对比——后者在 macOS 上有 [known issues](https://github.com/nodejs/node-v0.x-archive/issues/4803) 而 FSEvents 没有。

## 四、Rust 接管了哪些"本来是 Node.js native module"的东西

VSCode 的"重"，大头不在 TypeScript workbench，在 Node.js native module 这一层。VSCode 为了实现 file watching / search indexing / git integration / terminal PTY / SQLite，**在 Electron 进程里跑了一堆 C++ addon**。

SideX 把这一层完全搬到 Rust。我把 `src-tauri/src/commands/` 目录下能确认的几块列一下（README 没列全，但 ARCHITECTURE.md 提了）：

| VSCode 里跑的东西 | SideX 用什么 | Rust crate |
|---|---|---|
| `fs.watch` + chokidar | 内核级文件监听 | `notify` (FSEvents on macOS) |
| `node-pty` | PTY | `portable-pty` |
| `vscode-sqlite` / `better-sqlite3` | 配置 + 文档 + autosave + undo/redo | `rusqlite` (bundled) |
| Git operations | `simple-git` / `git` CLI | Rust command + `git` subprocess |
| Full-text search | `minimatch` + custom index | `dashmap` + `rayon` + `regex`（并行搜索索引） |
| File watching IPC | `fs.watch` IPC bridge | `notify` events 走 Tauri event bus |

`portable-pty` 是 SideX 整个项目里最值钱的依赖之一。VSCode 在 Electron 里跑终端需要 `node-pty`，但 `node-pty` 在 Windows 上用的是 [ConPTY](https://learn.microsoft.com/en-us/windows/console/closepseudoconsole)，macOS 上用的是 posix_openpt，Linux 上也是 posix_openpt——三者行为差异巨大。`portable-pty` 把这三个抽象成同一个 Rust API，**SideX 的终端在三大平台上跑同一份 Rust 代码**。

`dashmap` + `rayon` 做搜索索引这个组合也很精致：
- `dashmap`：并发 HashMap，多线程读写无锁
- `rayon`：数据并行（parallel iterator）
- `regex`：正则匹配

搜索索引更新时多 worker 并行建索引，查询时多线程并发查——这就是 README 写的 "Rust-backed search index"。

## 五、96% 缩水的来源

SideX 的 16.4 MB vs VSCode 的 797.8 MB，**48 倍差距**是怎么来的？我拉了 README 和一些公开数据推算了一下：

**VSCode 797.8 MB 大致构成**（估算）：
- Chromium runtime + V8：~400 MB
- Node.js + npm deps：~150 MB
- VSCode 自己的 TS 代码 + bundled resources：~250 MB

**SideX 16.4 MB 大致构成**：
- Rust 后端 binary：~3-5 MB（编译后，upx 压缩后更小）
- TypeScript workbench：~5-8 MB（同样的 VSCode 代码，但没 Electron 包袱）
- 原生 webview：**0 MB**（用系统的 WKWebView / WebView2 / WebKitGTK）

**关键节省 = 不打包 Chromium**。Electron 的全部问题几乎都是这一个：自带 Chromium，每个应用一份。Tauri 的核心价值就是"用系统的 webview"。一个普通 macOS 用户打开 Safari 时 WKWebView 已经在内存里了；再开 SideX，它和 Safari 共享进程资源。

但作者也写了非常清醒的限制：

> "**RAM savings are most tested on macOS, WKWebView is shared with Safari.** On Windows the picture is more nuanced — WebView2 memory can look higher depending on how it's measured, and it's an active area in the Tauri ecosystem."

—— 这是工程诚实。Windows 上 WebView2 内存不一定比 Chromium 小（取决于测量方式、Edge 是否在跑、是否启用共享进程），他们没把 Windows 的数字画成对比图。

> "The target is **under 200 MB at idle** on macOS. We'll publish real benchmarks once the app is stable enough for them to be meaningful."

—— **目标 200 MB**（VSCode idle 一般 600-800 MB）。他们没有拿"16.4 MB"当稳态值——那个是磁盘大小，不是内存。**这个区分非常重要**。很多 Tauri 营销稿把磁盘大小和内存大小混着说，SideX 区分得很清楚。

## 六、Extension Host 是最大那块空白

我前面提过 "Extension Host - Sidecar process (in progress)"——这是 SideX 0.1.3 整个版本里**最大的"未完成"**。

为什么这块这么重要？因为 VSCode 的 extension 生态（marketplace + Open VSX）是它最值钱的资产。一个 IDE 没了 extension，就是个编辑器；有了 extension，才是 IDE。

SideX 当前的状态是：

| 能力 | 状态 |
|---|---|
| Open VSX 扩展安装 | ✅ |
| Extension Host 进程 | ⏳ Sidecar process (in progress) |
| Debugger / Debug Adapter Protocol | ⏳ 进行中 |

`README` 的 "What's Working - Solid" 列表里**没列** extension host，`ARCHITECTURE.md` 里 extension host 那行是 "Sidecar process (in progress)"。

**这是什么意思**？它意味着：

1. **你能装扩展**（从 Open VSX registry 下载）
2. **但扩展可能跑不起来**（因为 extension host 还没实现到能 host 一个完整的 VSCode extension process）
3. **或者部分扩展能跑**（那些不依赖 extension host 完整 API 的，比如 theme/icon）

对于一个 VSCode 重写项目来说，**extension host 的成熟度决定了它的"实际可用度"**。这也是为什么版本号还在 0.1.3——0.1.x 不是"勉强能用"，是"架构到位、生态在路上"。

作者说"This was released early to get outside contributors involved"——这是一个非常聪明的策略：先把 Tauri 重写 + Monaco + 文件管理 + 终端 + Git + themes 这些"基础设施"做掉，剩下 extension host 和 debugger 是"全 VSCode 都知道怎么做"的部分，开放给社区贡献。

## 七、安装和构建的真实门槛

如果有人想本地跑起来，README 给的命令是这样的：

```bash
git clone https://github.com/Sidenai/sidex.git
cd sidex
npm install
npm run tauri dev
```

听起来很顺。但有几个真实门槛 README 没大声说：

1. **`NODE_OPTIONS="--max-old-space-size=12288"`** —— 12 GB 堆内存才能 build。Vite 在打包整个 VSCode workbench 时内存峰值极高，普通开发者机器 16 GB 内存会被 swap 打爆。
2. **"First build takes 5–10 minutes (Rust compile time)"** —— Rust 首次编译 + 链接 + tauri-build features 激活。后续 cargo build 增量会快很多。
3. **"Pre-built binaries are not distributed yet"** —— 没有 release 下载，你必须从源码 build。如果你是 Windows 用户，还需要 PowerShell 跑特定的环境变量设置。
4. **`rustup toolchain`** —— `Cargo.toml` 写了 `rust-version = "1.91.0"`，比 stable Rust 1.82 高——意味着需要 nightly 或指定 toolchain。

**这些不是 bug，是诚实**。一个 IDE 项目 4 个月大、2652 stars，作者没时间做 release pipeline + Windows installer + code signing + auto-update——这些事情 VSCode 做了十年。SideX 还在"先把核心跑起来"的阶段。

## 八、它不解决的问题

诚实地说几个 SideX **没做也不打算做**的事：

1. **不做 IntelliSense 的 language server**。Monaco 自带 basic IntelliSense，但完整的 VSCode IntelliSense 走 LSP（Language Server Protocol）——LSP server 通常是 Node.js / Go / Rust 写的二进制，sidecar 起来后通过 JSON-RPC 通信。SideX 现在应该能跑 LSP（因为 stdin/stdout IPC 在 Tauri 里是 OK 的），但 README 没强调 LSP 的状态。
2. **不做 remote development**。VSCode 的 remote SSH / remote containers / WSL 是大功能。SideX 没提。
3. **不做 settings sync**。VSCode 的 Settings Sync 让你的配置在多设备同步，SideX 没提。
4. **不做 workspace trust**。这是 VSCode 的代码执行安全模型，SideX 0.1.3 没提。
5. **不做完整的 Microsoft 认证**。`@microsoft/1ds-*` 遥测 SDK 仍在，但 `safeStorage` Partial——token 持久化未完成意味着某些需要安全存储的功能会受限。

**它的"边界"很清楚**：做一个**能编辑代码、能跑终端、能 git commit、能装一部分扩展**的轻量 IDE，不做"VSCode 替身"。

这是好的工程边界。**试图做 VSCode 替身的开源项目全部死了**（Code-OSS 之外的任何一个 fork 都很难维持全部能力），做"轻量 VSCode-like 编辑器"的反而活得久（VSCodium、Code - OSS、VSCodium）。

## 九、给我的启发

我读完这个项目，三个最大收获：

**第一，"Tauri 不是 Electron 杀手"**——Tauri 杀手锏是"不打包 webview"，这恰好解决了 VSCode 这种"重 TypeScript、轻 native"的场景。**但 Tauri 不是所有 Electron 应用的解药**——比如 Discord、Slack、Notion 这种重交互、富媒体的应用，用系统 webview 反而会因为 webview 版本碎片化（macOS 旧版 Safari vs Windows 新版 Edge）导致兼容问题。**SideX 的成功不能泛化到 Electron 生态**。

**第二，"port VSCode" 是合法的开源策略**——VSCode 源码是 MIT（Code-OSS），任何人都可以 fork、改名、换壳。SideX 不是"抄"，是"在 MIT 协议下 port"。这种"基于另一个开源项目的二次开发"在开源生态里非常健康——只要 attribution 清楚（SideX README 最后写了"MIT — SideX is a port of Visual Studio Code (Code - OSS)"），就是合规且贡献丰富的。

**第三，"0.1.x 是真实边界，不是营销"**——SideX 0.1.3 不藏 extension host 没做完的事实，不藏 Windows 内存数字"more nuanced"，不藏 12 GB build memory。**这种诚实本身就是项目的护城河**——吸引来的贡献者是来解决真实问题的人，不是来"凑热闹等 1.0"的人。

---

最后一句话。

SideX 把 VSCode 拆了，然后用 Tauri + Rust 拼回去。**96% 的瘦身不来自 TypeScript 优化（TypeScript 本来就不重），来自砍掉打包的 Chromium**。这种"换载具不换货物"的工程哲学值得所有在 Electron 痛苦里的团队想一想：**你们的应用值得 797.8 MB 吗？还是 16.4 MB 就够了？**

如果答案是后者——Tauri + Rust + system webview 这条路 SideX 已经走通了，剩下的是 extension host 和 debugger 的工程量。

> 项目仓库：[Sidenai/sidex](https://github.com/Sidenai/sidex)
> 架构文档：[ARCHITECTURE.md](https://github.com/Sidenai/sidex/blob/main/ARCHITECTURE.md)
> Discord：[SideX Community](https://discord.gg/8CUCnEAC4J)
> 作者：Siden Technologies Inc（@ImRazshy / kendall@siden.ai）