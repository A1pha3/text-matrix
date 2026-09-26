---
title: "Pake：配置在编译期定死的网页打包机，运行期只剩一个 WebView 壳"
date: "2026-04-07T17:15:00+08:00"
lastmod: "2026-09-21T00:00:00+08:00"
slug: pake-turn-any-webpage-into-desktop-app
github_repo: "tw93/Pake"
source_key: "gh:tw93/Pake"
description: "对照 tw93/Pake 的 main 分支、npm pake-cli@3.17.1 与 V3.17.0 的 64 个发布产物拆解 Pake：一条命令背后命令行工具如何生成 .pake 配置并经 include_str! 编译进二进制，release profile 与系统 WebView 如何决定 3.4-13.4 MB 的包体，capabilities 与 entitlements 划出的真实权限边界，以及 GPL-3.0 加产物例外对采用的影响。"
categories: ["技术笔记"]
tags: ["Tauri", "Rust", "桌面应用", "跨平台"]
draft: false
---

> **目标读者**：想把某个网站或本地前端产物变成常驻桌面应用的个人开发者，以及在 Pake、Tauri、Electron、Neutralino 之间做选型的工程师。
> **核心问题**：一条命令行工具（CLI）指令 `pake <url> --name X` 到底做了什么，为什么产物能只有几 MB，以及这个「小」用掉了哪些能力。
> **事实边界**：本文核对的是 `tw93/Pake` 的 `main` 分支提交 `d9e3201`（2026-09-20）、npm `pake-cli@3.17.1`（2026-09-20T13:41 发布）、GitHub Release `V3.17.0`（2026-09-20）的 64 个产物文件，以及 2026-09-21 通过 GitHub 与 npm 的应用程序接口（API）读到的数据。机制描述一律指到仓库内的具体文件；体积用的是 release 产物的实际字节数；内存与启动速度不给数字，官方只给了定性描述。

## 一句话判断

Pake 的 Rust 侧是一个不读外部配置的壳：目标网址、窗口尺寸、注入的 CSS 与 JS、图标、User-Agent（用户代理串）、托盘开关，全部在构建期写进二进制。运行期它只做三件事——把系统 WebView 撑起来、按固定顺序注入初始化脚本、把网页侧的调用转成原生动作。

这个取舍决定了它的三个特征：产物只有几 MB，因为没有任何浏览器内核被打进去；改一个窗口宽度要重新打包，因为配置是编译期常量；网页运行时能拿到的原生能力被 `capabilities` 一份清单钉死，因为壳的行为在建窗时就定完了。

如果需求只是一个网址、一个桌面身份、一个 Dock 图标，这条路径的维护成本接近于零。反过来，要装 Chrome 扩展、用 history 路由打包本地单页应用（SPA）、在应用里跑 Node.js 原生模块，或者依赖 Google 那类会拒绝嵌入式 WebView 的登录，Pake 帮不上忙——官方给的建议也是换浏览器或官方客户端。

## 项目坐标（2026-09-21 核对）

| 字段 | 值 |
|------|------|
| 仓库 | [tw93/Pake](https://github.com/tw93/Pake)，默认分支 `main`，建仓 2022-10-14，最近推送 2026-09-20 |
| Stars / Forks | 61,549 / 12,687（GitHub API 当日读数） |
| 贡献者 / Release 数 | 84 / 53 |
| 作者 | Tw93（`package.json` 的 `author` 与 `Cargo.toml` 的 `authors` 都是这个名字） |
| 最新版本 | GitHub Release 为 `V3.17.0`「Harbor」（2026-09-20），`main` 的 HEAD 已把版本提到 3.17.1，npm `pake-cli` latest 也就是 3.17.1 |
| License | GPL-3.0-or-later，另附 `LICENSE-EXCEPTION`（Pake Output Exception），见后文「许可证」一节 |
| npm 侧 | `pake-cli` 自 2022-11-13 起发布 175 个版本，latest 解包 14,689,922 字节，上一周下载 1,864 次 |
| 运行时要求 | CLI 需要 Node.js ≥20.9.0（`package.json` 的 `engines`，README 建议 22）；Rust ≥1.85.0（`Cargo.toml` 的 `rust-version`），仓库自带 `rust-toolchain.toml` 钉在 1.95.0 |
| 依赖内核 | Tauri 2.10.2 + tauri-build 2.5.5，8 个官方插件，渲染交给系统 WebView |

GitHub API 给出的语言字节数是 Rust 129,283、Dockerfile 2,844、TypeScript 381。别拿它算代码占比：`.gitattributes` 把 `bin/**`、`src-tauri/src/inject/**`、`docs/**`、`tests/**` 全标成了 `linguist-vendored`，CLI 的 TypeScript 与近 3,400 行注入脚本都不参与统计。真实的构成是「TypeScript CLI + Rust 壳 + 一批 JS/CSS 注入代码」三块，语言条只让你看见第二块。

## 系统地图：两条互不相干的线

读者最容易搞混的一点是：Pake 的 CLI 和 Pake 的应用几乎不共享运行时代码。前者是一次性构建工具，后者是编译产物。分清这两条线，后面所有细节都能归位。

```text
构建期（TypeScript CLI，跑一次就退出）
  参数与配置文件合并  bin/helpers/cli-program.ts + bin/helpers/config-file.ts
        ↓
  配置模板拼装        bin/helpers/tauriConfig.ts → bin/helpers/merge.ts
        ↓  写入 src-tauri/.pake/{pake.json,tauri.conf.json,tauri.<平台>.conf.json}
  注入代码合并        bin/utils/combine.ts → 覆写 src-tauri/src/inject/custom.js
  图标与权限          sharp 转 icns/ico/png；--camera/--microphone 生成 entitlements.plist
        ↓
  调 tauri build --features cli-build  （在临时工作区内，Cargo 缓存目录复用）
        ↓
运行期（Rust 壳，编译产物里已经没有 CLI）
  util.rs 用 include_str! 读到的 .pake/pake.json 是编译期常量
        ↓
  app/window.rs 建窗 → 按固定顺序注入 inject/*.js
        ↓
  app/{menu,setup,invoke,navigation,auth}.rs 提供菜单、托盘、全局快捷键、下载、缩放、认证

```

`.pake/` 这个目录是关键。`src-tauri/src/util.rs:9-22` 里，同一对配置有两条读取分支：

```rust
#[cfg(feature = "cli-build")]
let pake_config: PakeConfig = serde_json::from_str(include_str!("../.pake/pake.json"))
    .expect("Failed to parse pake config");

#[cfg(not(feature = "cli-build"))]
let pake_config: PakeConfig =
    serde_json::from_str(include_str!("../pake.json")).expect("Failed to parse pake config");
```

带 `cli-build` feature（CLI 会自动加上）就编入 `.pake/` 下生成的那份，也就是你打包的那个网站；不带则编入仓库自带的 `pake.json`，那是 `pnpm run dev` 时打开 `https://weekly.tw93.fun/en` 的默认壳。`include_str!` 意味着字符串被写死进可执行文件，因此：

- 应用没有「外部配置」这个概念，改任何参数都要重新 `pake` 一遍。
- 装到磁盘上的就是一个自包含的应用包，没有首启初始化、没有配置文件要用户维护。
- `bin/builders/BaseBuilder.ts:507` 的 `getBuildFeatures()` 说明了一件事：`macos-proxy` 只在宿主 Darwin 主版本 ≥23（macOS 14 及以后）时才加上，因为 Tauri 的 macOS 代理 API 有系统版本门槛，旧系统上构建出的包不带这条能力。

## 一条命令如何流过系统

拿一个真实需求走一遍：给内部看板打包一个应用，窗口 1400×900，注入一份去广告样式，macOS 隐藏标题栏。

```bash
pake https://kanban.internal.example.com \
  --name "Kanban" \
  --width 1400 --height 900 \
  --hide-title-bar \
  --inject ./tools/adblock.css,./tools/hotkey.js \
  --json
```

第一步是参数收敛。`--json` 会把日志全部推到 stderr，stdout 只留一个 JSON 对象，同时关掉交互式提问——这是给脚本和 agent 用的机器可读契约（`llms.txt` 里逐条写明，退出码 0 成功、2 输入非法、3 构建失败、4 环境或缺依赖、1 其他）。数值类参数在解析阶段就被拦住：`--zoom` 要求 50-200 的整数，`--width`/`--height` 走同一个校验器，URL 参数同时接受 http(s) 链接和本地路径。

第二步写配置。`bin/helpers/tauriConfig.ts` 从 npm 安装目录里读 `src-tauri/pake.json`、`tauri.conf.json` 和当前平台的 `tauri.<os>.conf.json`，`bin/helpers/merge.ts` 把命令行参数逐个落进这份合并结果，写到 `src-tauri/.pake/`。注意它读的是 **npm 包里的那份**：`package.json` 的 `files` 字段包含 `src-tauri`，所以 `pake-cli` 这个 14.7 MB 的包里装着整个 Rust 壳，构建过程既不用克隆仓库，也不用你自己准备 Tauri 模板——要联网下载的只有 crates.io 与 npm 上的依赖。

第三步处理注入文件。`bin/utils/combine.ts` 把 `--inject` 的每个文件包成一段 `DOMContentLoaded` 监听再拼接，覆写 `src-tauri/src/inject/custom.js`；不传 `--inject` 时把这个文件写成空。这里有两个能立刻咬到人的边界：注入的 CSS 走 `window.__PAKE_INJECT_STYLE__`（由 `inject/styles.js` 提供，用 `adoptedStyleSheets` 装，样式里含 `@import` 时退回插 `<style>` 标签）；而注入代码的运行时机是 `DOMContentLoaded`，也就是页面自己的脚本已经跑过了。指望注入脚本抢在站点逻辑之前改行为，会失败。

第四步建工作区并构建。`bin/utils/build-workspace.ts` 先在系统临时目录下 `mkdtemp('pake-build-')` 开一份工作区，只拷 `package.json`、锁文件、`rust-toolchain.*` 和 `src-tauri/`，而 `src-tauri/` 里的 `target`、`.pake`、`gen` 三个子目录被过滤掉——缓存与上一次生成的配置不属于模板；`node_modules` 用软链接过去。生成的配置与图标都写进这份副本，构建完连副本一起删掉，全局安装的 npm 包不会被写脏。编译缓存则是另一回事：`CARGO_TARGET_DIR` 按安装包所在目录解析成 `src-tauri/target` 并跨多次构建复用，同时在那把 `.pake-build.lock` 上排队，最多等 15 分钟。这就是「第一次很慢、后面快」的机制原因，也是并发打包会互相等待的原因；官方对 GitHub Actions 的时长预期同样是首次 10-15 分钟建立缓存、后续约 5 分钟、缓存 400-600 MB。

第五步交付产物。`--targets` 决定格式：macOS 是 `dmg`（设了 `PAKE_CREATE_APP=1` 则出 `.app`，`--install` 会顺手拷进 `/Applications` 并删掉本地那份），Windows 是 `msi`，Linux 可选 `deb,appimage,rpm,zst`。`--keep-binary` 在安装包旁边留一份裸二进制，`--iterative-build` 走快速模式只出应用本体、跳过 `dmg`/`deb`/`msi` 封装，用于反复调试。产物路径与字节数会回写进 `--json` 的 `outputs[]`。

## 3.4 MB 与 150 MB 之间：这些数字该读几层

官方对体积的说法是「安装包相比 Electron 应用小近 20 倍，通常小于 10M」。把它换算成倍数需要一层分母，而分母取什么很关键。

对照基线取 Electron 的最新稳定版 `v44.4.3`（2026-09-18 发布），它的运行时装包是：darwin-arm64 124.1 MB、win32-x64 150.9 MB、linux-x64 117.3 MB。这是每个 Electron 应用都必须带走的 Chromium 加 Node.js 运行时，跟你的业务代码无关。再看 Pake `V3.17.0` 产物里 ChatGPT 这个应用的实测体积：

| 格式 | 字节数换算 | 对同平台 Electron 运行时 |
|------|------|------|
| `ChatGPT.dmg` | 9.42 MB | 13 倍 |
| `ChatGPT_x64.msi` | 3.54 MB | 43 倍 |
| `ChatGPT_x86_64.deb` | 4.55 MB | 26 倍 |
| `ChatGPT_x86_64.AppImage` | 75.96 MB | 1.5 倍 |

同一次 CI、同一个站点，只差打包格式。整个 release 的 64 个产物合起来看：16 个应用的 `dmg` 落在 8.03-13.43 MB，`msi` 在 3.41-3.82 MB，`deb` 在 4.31-5.27 MB，`AppImage` 清一色 75.8-76.5 MB。

于是「约 5MB」这句话要说清三件事。它测的是磁盘上的安装包，不是运行时内存；它对 `dmg`/`msi`/`deb` 成立，对 `AppImage` 不成立——后者要把 WebKitGTK 及其 GTK 依赖一起塞进单文件，为的是在没有包管理的发行版上也能跑起来，代价就是回到几十 MB。至于是 13 倍还是 43 倍，取决于拿哪个平台、哪种格式去比；官方那句「小近 20 倍」没有指明用哪种格式作比，按上表自己换算更稳。

小体积来自三处叠加，都能在代码里指认：

1. **不打浏览器内核**。渲染走系统 WebView：macOS 的 WKWebView、Windows 的 WebView2、Linux 的 WebKitGTK。`Cargo.toml` 里 macOS 只依赖 `objc2-web-kit` 的 `WKUserContentController`/`WKWebViewConfiguration` 两项 feature，Linux 依赖 `webkit2gtk =2.0.2`（`v2_38`），Windows 依赖 `webview2-com 0.38`——都是绑定时库，不是内嵌。
2. **release profile 压到底**。`src-tauri/Cargo.toml` 的 `[profile.release]` 写了 `panic = "abort"`、`codegen-units = 1`、`lto = "thin"`、`opt-level = "z"`、`strip = true`。`opt-level="z"` 是尺寸优先而非速度优先，`strip` 去掉符号表。
3. **配置内联而非资源打包**。没有外置配置目录、没有前端 bundle，`tauri.conf.json` 里 `frontendDist` 指向的 `dist/` 只放了 CLI 自己的 `cli.js`。

第二处也解释了为什么不要拿 Pake 的「快」当真：README 里那句「比传统 JS 框架更快，内存占用更少」没有附测量数据，而 `opt-level="z"` 换的是体积不是速度。`docs/faq_CN.md` 反倒把另一头写明了：应用会拉起 `WebKitWebProcess`（Linux）或 WebContent 进程（macOS）吃掉几百 MB，这部分由引擎和页面决定，「Pake 在 WebView 之上几乎不增加额外开销，所以没有能显著降低它的 Pake 侧设置」。小的是磁盘，不是内存——这是用系统 WebView 换体积时必须接受的账。

## 运行期：脚本按固定顺序进场

壳启动后真正的活集中在 `src-tauri/src/app/window.rs:553-585`。初始化脚本分两类作用域：`initialization_script_for_all_frames` 进所有 frame，`initialization_script` 只进主 frame，顺序有硬约束。下表 12 行里有 10 行是无条件注入的，另外两行按开关与平台决定是否进场。

| 脚本 | 行数量级 | 作用域 | 为什么在这个位置 |
|------|------|------|------|
| `window.pakeConfig = {...}` | 生成 | 全 frame | 后面每个脚本都读它，必须最先落 |
| `link_policy.js` | 90 | 全 frame | 决定链接留在应用内还是交系统浏览器 |
| `auth.js` | 80 | 全 frame | HTTP Basic 认证拦截 |
| `frame_links.js` | 67 | 全 frame | 注释写明 WebKit 下子 frame 拿不到主页面那套注入 |
| `styles.js` | 100 | 主 frame | 提供 `window.__PAKE_INJECT_STYLE__` |
| `find.js` | 725 | 主 frame | 仅 `--enable-find` 时注入，注释的理由是省掉每次页面加载解析 700 行 |
| `toast.js` | 22 | 主 frame | 要在 Rust 调 `show_toast()` 之前注册 `window.pakeToast` |
| `fullscreen.js` | 234 | 主 frame | Windows 上跳过——WebView2 的原生全屏 API 已经驱动窗口全屏 |
| `event.js` | 1,487 | 主 frame | 快捷键、缩放、复制链接、拖拽、下载等主体逻辑 |
| `style.js` | 540 | 主 frame | 内置的站点样式修正 |
| `theme_refresh.js` | 59 | 主 frame | 深浅色切换后刷新 |
| `custom.js` | 0（默认） | 主 frame | `--inject` 的合并结果写在这里，编进二进制 |

`event.js` 单文件 1,487 行，是注入脚本里最厚的一块，README 那张快捷键表里的行为主要由它实现：`⌘[`/`]` 与 `Ctrl+←`/`→` 前后退、`⌘↑`/`↓` 滚到顶底、`⌘r` 刷新、`⌘w` 隐藏窗口而非退出、`⌘±/0` 缩放、`⌘L` 复制当前网址、`⌘⇧H` 回首页、`⌘⇧⌫` 清缓存重启、`⌃⌘F` 或 `F11` 切原生全屏，以及双击标题栏切全屏。想关掉这套透传，参数是 `--disabled-web-shortcuts`。

缩放有两处容易撞的边界：`--zoom` 只接受 50-200 的整数（3.17 系列专门加了拒绝小数的校验），页面侧 `event.js` 读 `window.pakeConfig.zoom` 调 `setZoom()`；`app/invoke.rs` 里也暴露了 `set_zoom` 命令给网页用。Rust 侧可调的其余命令还有 `webview_navigate`（原生导航，用于注入的快捷键在 Linux/Windows 上触发 `Ctrl+R`、`[`、`]`）、`download_file`、`send_notification`、`clear_dock_badge` / `increment_dock_badge` / `set_dock_badge` 一组 Dock 角标，以及 `update_theme_mode`。

## 身份、状态与「同站多开」

Pake 给每个打包应用一个 bundle identifier：`bin/utils/info.ts` 里取 `md5(url + "::" + name)` 的前 6 位，拼成 `com.pake.a<hash>`。因此同一个站点用两个名字打包，系统会当成两个独立应用装了两次——官方文档给的例子是「Gmail Work」和「Gmail Personal」各存一套登录态。把 `name` 纳入哈希是 V3.10.1 起的行为，更早的标识只由 url 决定，同一站点在那之前打出的两个包会落到同一个标识上。要固定标识可以传隐藏参数 `--identifier com.example.gmail.work`。

真正跟「同站多开」易混的是另外两个开关，官方文档专门把三者拆开：

| 参数 | 语义 | 典型场景 |
|------|------|------|
| `--identifier` / 换 `--name` | 造出多个彼此独立的安装身份 | 两个账号的同一站点 |
| `--multi-instance` | 允许同一个已打包应用起多个进程 | 需要并排开两个窗口 |
| `--multi-window` | 单进程内多窗口，重复启动即新开窗口 | 一个应用里多标签页；macOS 上 `Cmd+N` 的窗口会自动进原生标签页组 |

状态保持来自 `tauri-plugin-window-state` 加 `app/window.rs` 的 `save_last_url` / `util.rs` 的 `read_last_url`：关闭窗口或退出时记住主窗口完整网址，下次启动恢复；没有记录时打开打包网址。回退条件写得很具体——只有 scheme 是 `http`/`https` 的才认，`--incognito` 和本地 HTML 应用不保存不恢复。数据目录是 `config_dir()` 下按包名建的那层（`util.rs:26-48`），Cookie 就活在系统 WebView 的存储里。

`--incognito` 存在的理由值得单独说一句：微信网页版检测到 WebView 会写标记 Cookie，导致后续持续被拦，官方给的解法就是强制隐身，代价每次都要重新扫码。这类「站点识别出你不是标准浏览器」的问题，在 Pake 上不是一次性的 bug，而是引擎归属暴露出来的常态，后文边界一节还会遇到。

## 权限边界：一份清单和一次 ad-hoc 签名

Pake 上面没有额外一层沙箱，真实的权限边界是一份 Tauri capability。`src-tauri/capabilities/default.json` 声明该 capability 作用于 label 为 `pake` 的 webview，`remote.urls` 写成 `["https://*.*"]`——也就是说，只要是你打包进去的那个远程站点，就被视为可信来源，可以拿到清单里列的权限：`shell:allow-open`、一组窗口操作（主题、拖拽、最大化、全屏、最小化、关闭、`allow-set-resizable`）、`core:webview:allow-internal-toggle-devtools`、通知相关的注册与发送，以及 `core:path:default`。加上 `tauri.conf.json` 里 `app.withGlobalTauri: true`，网页侧脚本能直接拿到 `window.__TAURI__`。

这带来两个方向相反的判断。一方面 `advanced-usage_CN.md` 的「容器通信」是可行的：网页里 `window.__TAURI__.core.invoke("handle_scroll", {...})`，Rust 侧加一个 `#[tauri::command]` 就能收——但改 Rust 意味着重新编译，它属于定制开发而不是配置项。另一方面，把不可信站点打包成桌面应用，等于把上面这组原生调用交给那个站点。Pake 的 CSP 是 `null`（`tauri.conf.json` 里 `security.csp`），`headers` 是空对象，它不做任何内容过滤。想收紧，实际能操作的是别打包来路不明的页面、需要时用 `--safe-domain` 与 `--force-internal-navigation` 把跳转留在应用内、用 `--internal-url-regex` 指定内网域。

macOS 侧还有两道。`tauri.macos.conf.json` 写了 `hardenedRuntime: true`、`signingIdentity: "-"` 和 `entitlements`、`infoPlist` 两个入口，而仓库里的 `src-tauri/entitlements.plist` 是一个空 `<dict>`。签名身份是 `-` 即 ad-hoc，没有走开发者证书，所以从浏览器下载的 `dmg` 首次打开会被 Gatekeeper 拦一下：要么用户自己放行（右键打开，或去掉隔离属性），要么你有 Apple 开发者证书去做签名加公证。摄像头与麦克风默认不申请，`--camera` / `--microphone` 会让 `generateMacEntitlements()` 往 `entitlements.plist` 里写 `com.apple.security.device.camera` 与 `com.apple.security.device.audio-input`，首次使用时系统才弹窗。视频站点要单独传这两个开关，没有传就是构建完也拿不到权限。

`--ignore-certificate-errors` 是另一个要明白代价才用的开关：它给 Windows 的 WebView2 浏览器参数追加上同名项（Linux 分支同理），用于内网自签证书的场景，代价是那台机器上这个应用不再对证书错误报警。Pake 在 Windows 上默认还带了 `--disable-features=msWebOOUI,msPdfOOUI,msSmartScreenProtection` 与 `--disable-blink-features=AutomationControlled`，前者关掉 WebView2 的 OOUI 浮层与 SmartScreen 拦截，后者关掉 Blink 的自动化特征位。这些都是浏览器参数层面的行为调整，与安全边界的收紧无关。

## 许可证：产物归你，源码归 GPL

Pake 用 GPL 而不是 MIT 发布：`package.json` 与 `Cargo.toml` 都写 `GPL-3.0-or-later`，GitHub API 的 license 字段是 GPL-3.0。真正影响采用决策的是仓库根目录那份 `LICENSE-EXCEPTION`。

它是一段 GPLv3 第 7 条下的额外许可：用 Pake（或用标准构建流程产出的 Pake）生成的目标应用，其中被打进去的那部分 Pake 不会导致整个产物落到 GPLv3 之下，你可以按自己选定的许可条款分发它，包括闭源。例外不适用于 Pake 本身，也不适用于超出「标准构建的配置与打包」之外改动过 Pake 源码的作品——那仍然完整地受 GPLv3 约束。README 的中文表述更直白：打包生成的应用所有权完全归你；想派生（fork）一个自己的 Pake 产品，请换名字并注明来源。

对采用方这意味着：内部工具、分发的商业桌面客户端，产物许可不受污染；改 `src-tauri` 的 Rust 代码或 `inject/*.js` 再对外发布，就要按 GPL 提供源码。`--inject` 传外部 CSS/JS 文件属于「标准构建流程的配置」这一侧，因为它只是被合并进 `custom.js` 的内容。

## 许可证之外，什么时候不该用 Pake

| 情况 | 为什么 | 更合适的做法 |
|------|------|------|
| 本地前端产物用 history 路由的 SPA | 官方边界：本地打包开箱只支持 hash 路由，history 模式暂不支持 | 打包时改 hash 路由，或回到 Tauri 自己配前端 |
| 依赖 Google 等第三方 OAuth 弹窗 | 提供方会拒绝嵌入式 WebView 中的授权；`--new-window`、`--multi-window` 只能改善弹窗流程，官方原话是「不能绕过认证提供方的策略限制」 | 换官方桌面客户端或浏览器 |
| 站点前置 Cloudflare / 人机验证 | Linux 的 WebKitGTK 尤其容易被判为非标准浏览器并无限循环，官方明确「加了自定义 `--user-agent` 也无效，Pake 侧没有可靠绕过手段」 | 别打包这个站点 |
| 需要 Chrome 扩展、Node.js 原生模块、复杂系统集成 | 系统 WebView 没有扩展 API，Pake 也没有 Node.js 运行时 | Electron 或直接 Tauri |
| 要在没有系统 WebKit 的环境稳定一致渲染 | 三平台三引擎（WKWebView / WebView2 / WebKitGTK），渲染差异由宿主版本决定 | Electron，锁 Chromium 版本 |
| 需要运行时改配置、远程下发参数 | 配置编译期内联，改任何一项都要重新打包 | Tauri 自己起外部进程或读外部配置 |

Linux 上还有两条与引擎、合成器版本绑定的现实问题，都在官方 FAQ 里。一是 Ubuntu 24.04 / GNOME 下窗口按钮刚启动时点不动，代码里的处理是等 30ms 让窗口管理器处理完 `MapWindow` 再抢焦点（`lib.rs` 的注释点名 issue #1122）。二是纯 Wayland 合成器（FAQ 点名 niri）上 AppImage 能打开，但按钮点不动、键盘进不去 webview。后者在 3.17 系列里做成了启动期判定：`apply_linux_webkit_runtime_flags()` 读桌面标识、`NIRI_SOCKET`、`WAYLAND_DISPLAY` 与 WebKit 版本，按需自己 `set_var` 打开 `WEBKIT_DISABLE_DMABUF_RENDERER`、`WEBKIT_DISABLE_COMPOSITING_MODE`、`WEBKIT_DMABUF_RENDERER_FORCE_SHM` 中的相应几项，判定范围收窄到 Wayland，用户可以用 `PAKE_LINUX_WEBKIT_SAFE_MODE` 强制开启或整体关闭。这类按环境开关渲染路径的处置属于打补丁级别，选 Linux 桌面化时要把这层不确定性算进去。

## 使用路径与真实参数

按投入产出排：

**先确认这个站点值不值得打包。** [Releases](https://github.com/tw93/Pake/releases) 里有 16 个现成应用，清单维护在 `default_app_list.json`：WeChat、DeepSeek、Grok、Gemini、Excalidraw、Notion、ProgramMusic、Twitter、YouTube、ChatGPT、Flomo、Qwerty、LiZhi、XiaoHongShu、YouTubeMusic、WeRead。每个应用出四种格式的包，一次发版共 64 个产物。微信那条自带 `incognito: true` 与 1000×720，正是前文那个 Cookie 标记问题的处置。发版时 `release.yml` 用 `jq` 把这份列表展开成构建矩阵，逐个调 `single-app.yaml`；你要打包的站点在这 16 个之外，才轮到自己构建。

**装 CLI，跑最小示例。**

```bash
pnpm install -g pake-cli          # 或 npm install -g pake-cli

pake https://github.com --name GitHub                    # 图标自动抓 favicon
pake ./dist --name MyTool                                # 本地静态目录，根目录要有索引页 index.html
pake https://chatgpt.com --name ChatGPT --microphone     # 要语音输入就得显式给权限
```

窗口默认 1200×780，`--width/--height/--min-width/--min-height/--fullscreen/--maximize/--always-on-top/--title/--zoom` 是这一类。缺 `--name` 时行为分两种：交互终端下 `bin/options/` 里的选项处理会用从 URL 推出的默认名向你确认一次，而 `--json`、`CI` 与 `GITHUB_ACTIONS` 任一成立时不提问，直接采用推导结果。`--hide-title-bar` 只作用于 macOS，Windows 和 Linux 上会被忽略，对应参数是 `--hide-window-decorations`（出一个带顶部拖拽区的无边框窗口）。`--hide-on-close` 默认 macOS 为 true、其他平台 false。

**没有本地环境就用 Actions 或 Docker。** 在线构建的路径是 fork 仓库、在 Actions 里运行 `Build App With Pake CLI` 这个 `workflow_dispatch`，表单字段与 CLI 参数同名（`platform` 是 `macos-latest`/`windows-latest`/`ubuntu-24.04` 三选，`targets` 默认 `deb`，Linux 侧可选 `deb,appimage,rpm,zst`），产物在 Artifacts 里下载。这个工作流的权限只有 `contents: read`，它不写任何东西回仓库。仓库里另有一个复合 action（`action.yml`，输入 `url`/`name`/`icon`/`width`/`height`/`output-dir`/`debug`，输出 `package-path`）供别人在自己的 workflow 里 `uses`，时长预期与前文一致。Docker 走 `ghcr.io/tw93/pake`，构建 AppImage 需要 `--device /dev/fuse` 和 `--security-opt apparmor=unconfined`。

**要改行为再进定制开发。** 环境要求 Rust ≥1.85、Node.js ≥22（旧一点 ≥20 也可能可用），`pnpm i && pnpm run dev` 起的是自带那份 `pake.json` 指向的站点，右键可开调试模式——注意 DevTools 那个 `⌘⌥I` 菜单项在 `app/menu.rs:174` 用 `cfg!(debug_assertions)` 控制可见，正式包点不出来，要调试就自己 `--debug` 打一个。改样式动 `src-tauri/src/inject/style.js`，改交互动 `event.js`，跑 `pnpm test`（先 build CLI，再 Vitest，再做真实构建与发布流程冒烟，`--no-build` 可跳过后两步）。

**给脚本或智能体（agent）用。** 除了 `--json`，还有 `--config app.json` 走声明式配置，字段名是 camelCase 化的命令行选项加一个 `url`，字段模式（JSON Schema）在 `schema/pake.schema.json`；显式命令行参数优先于配置文件字段，未知字段直接失败；配置里相对路径的 `url` 按进程工作目录解析，而不是按配置文件所在目录。Linux 多目标构建有个坑：`ok: true` 时 `outputs[]` 可能少于请求的格式数，失败的那部分落在 `warnings` 里，判定要看 `outputs[].format`。国内网络下 `PAKE_USE_CN_MIRROR=1` 可显式切镜像源，默认走官方 npm 与 Rust 源。

## 排查：六类常见失败

按现象分。构建期的问题集中在环境、依赖与编译缓存，运行期的集中在引擎与站点策略。

**第一次构建极慢，或卡在拉依赖。** 首次要装系统依赖并冷编译 Cargo，`prepare()` 会先提示一次。Windows 上官方给的预期是 10-15 分钟。判据是第二次是否明显变快——若每次都慢，检查 `CARGO_TARGET_DIR` 是否被指向临时盘，以及 `src-tauri/target` 有没有被清理脚本带走。并发打包时它会排队等编译缓存，最长 15 分钟；如果报 `A previous Pake process left a compilation cache lock`，说明上一次构建没留下活进程却漏了锁文件，按提示删掉 `src-tauri/target/.pake-build.lock` 再试。国内网络显式设 `PAKE_USE_CN_MIRROR=1`。

**报 Rust 版本错，提示 `feature 'edition2024' is required`。** `Cargo.toml` 要求 ≥1.85，依赖链里有 crate 用了 2024 edition。`rustup update stable` 后确认 `rustc` 版本，CLI 缺 Rust 时会问你要不要自动装，装失败或超时再手动装。

**Linux 构建报找不到 appindicator 库。** 缺的是 `libayatana-appindicator3-dev` 一类的开发包，Ubuntu 24.04 上最常见。

**AppImage 启动即崩，报找不到 `WebKitNetworkProcess`。** 这是 Tauri 打包器的上游限制（tauri-apps/tauri#5292），只有你在非 Debian 系发行版上本地打 AppImage 时才会撞到：Tauri 会把 WebKit 辅助进程的绝对路径改写成相对形式，并按 Debian 的库布局（`/usr/lib/<三元组>/webkit2gtk-4.1`）复制它们，而 Arch 的路径里没有那个三元组目录，改写后的路径在 bundle 内不存在。官方给的三条处置分别是：Arch 上改用 `--targets zst` 出 pacman 包、在基于 Debian 的 `ghcr.io/tw93/pake` 镜像里打 AppImage、或 `--appimage-extract` 后补一条软链接再跑 `AppRun`。

**打不开、登录卡住、验证死循环。** 先分清是弹窗被拦还是引擎被识别。前者试 `--new-window`（允许站点开新窗口，用于两段式授权）与 `--safe-domain`（把单点登录（SSO）回调域留在应用内）；后者按 FAQ 的定性处理——验证服务在识别浏览器引擎，不是 Pake 的 bug，换浏览器或官方客户端。微信网页版被标记后用 `--incognito`。

**界面被改了但重启没生效。** 改的是 `--inject` 的文件、`style.js`、`event.js` 或任何窗口参数，都需要重新打包，因为配置和脚本都编在二进制里。反复验证时用 `--iterative-build` 只出 `.app`，省掉 dmg/安装包环节。macOS 上装了同名旧版本没更新，先核对 bundle identifier：只改 `--name` 会造出新身份而不是覆盖旧应用。

## 五个自测题

**1. 为什么 `dmg` 只有 8-13 MB，`AppImage` 却接近 76 MB？**

<details>
<summary>参考答案</summary>

`dmg`/`msi`/`deb` 依赖系统已有的 WebView 与图形栈，包里主要是那个按 `opt-level="z"` 编译、`strip` 过符号的 Rust 壳。AppImage 要单文件可运行，就得把 WebKitGTK 及其 GTK、libsoup 等运行时一起打进去，76 MB 基本是这些系统库。所以「小近 20 倍」这个量级只对前三种格式成立，拿同平台 Electron 运行时装包作分母是 13 到 43 倍，AppImage 只有约 1.5 倍。
</details>

**2. 改了 `--width` 为什么应用没变化？**

<details>
<summary>参考答案</summary>

窗口尺寸写进 `pake.json` 的 `windows[0].width`，而 Rust 侧是 `include_str!("../.pake/pake.json")` 在编译期内联，运行时不存在读配置这一步。重新执行 `pake` 打包才有变化；开发验证可以 `--iterative-build` 只出 `.app`。
</details>

**3. `--inject` 的 CSS 为什么有时抢不过站点自己的样式？**

<details>
<summary>参考答案</summary>

两条独立原因。时机上，`combine.ts` 把注入文件包在 `DOMContentLoaded` 监听里，页面脚本先跑完；装载方式上，`styles.js` 优先用 `adoptedStyleSheets`，但检测到 `@import` 时改走插 `<style>` 标签（因为 `replaceSync` 会静默丢掉 import 规则），后者在层叠里的位置与前者不同。要强制生效就在注入样式里加 `!important` 或用 `@layer` 明确层级。
</details>

**4. 同一站点要两个独立登录态，用 `--multi-instance` 行不行？**

<details>
<summary>参考答案</summary>

不行。`--multi-instance` 允许多进程，但它们共用同一身份与同一份 WebView 数据目录，登录态互相覆盖。正确做法是换 `--name`（identifier 由 `url + "::" + name` 哈希而来）或显式 `--identifier`，让系统装成两个应用。
</details>

**5. 团队想把打包好的应用直接分发给客户，发布前必须处理哪两件事？**

<details>
<summary>参考答案</summary>

一是 macOS 的 ad-hoc 签名：`signingIdentity` 为 `-`，用户会看到 Gatekeeper 拦截，要么自建证书做 Developer ID 签名加公证，要么明确告知需要右键打开。二是许可与品牌：Pake 是 GPL-3.0-or-later，产物靠 `LICENSE-EXCEPTION` 获得自有许可的自由，但只要你改过 `src-tauri` 的 Rust 源码再分发就得开放那部分源码，并且按 README 要求换掉产品名、注明来源。
</details>

## 下一步读哪份代码

按目的选，不按顺序：

- 想看构建期一条参数怎么落地：`bin/helpers/cli-program.ts`（52 个选项的定义与校验，其中 32 个 `hideHelp`，`--help` 只是常用那一档）→ `bin/helpers/merge.ts`（合并与写 `.pake/`、生成 entitlements）→ `bin/builders/BaseBuilder.ts`（`copyBuildArtifacts`、`--install`）。
- 想知道产物为什么小：`src-tauri/Cargo.toml` 的 `[profile.release]` 与 `src-tauri/src/util.rs` 的 `include_str!` 两处，一共不到 40 行。
- 想理解网页侧行为：`src-tauri/src/inject/event.js` 加 `window.rs:553-585` 的注入顺序注释，注释本身是最好的一份设计说明。
- 想确认权限面：`src-tauri/capabilities/default.json` 与 `src-tauri/tauri.macos.conf.json`。
- 想给 agent 接进来：`llms.txt`（退出码、JSON 结构、错误码、配置优先级）配 `schema/pake.schema.json`。
- 参数手册与故障库：`docs/cli-usage_CN.md`（720 行，逐条带示例与默认值）和 `docs/faq_CN.md`（594 行，按平台与现象分类）。

Pake 可以看成「把 Tauri 的某一个具体用法固化成 CLI」，一旦你需要外部配置、多窗口编排或自定义 Rust 命令，就该直接下到 Tauri 那一层。[SideX：把 VSCode 拆了再用 Tauri 拼回去]({{< relref "sidex-vscode-tauri-rebuilt-2026.md" >}}) 是那条路上走到很远处之后长出来的样子，两篇对照着读能看出「打包一个网页」与「用 Tauri 重写一个应用」的分界在哪里。

## 参考

- 仓库与机制：[tw93/Pake](https://github.com/tw93/Pake) `main@d9e3201`（2026-09-20），`README_CN.md`、`docs/advanced-usage_CN.md`、`docs/cli-usage_CN.md`、`docs/faq_CN.md`、`llms.txt`
- 许可：[`LICENSE`](https://github.com/tw93/Pake/blob/main/LICENSE)（GPL-3.0-or-later）与 [`LICENSE-EXCEPTION`](https://github.com/tw93/Pake/blob/main/LICENSE-EXCEPTION)
- 版本与统计：GitHub API 于 2026-09-21 读取（stars 61,549、forks 12,687、contributors 84、releases 53、created 2022-10-14）；Release `V3.17.0` 的 64 个产物字节数；Electron `v44.4.3` 运行时装包体积
- npm 元数据：`pake-cli@3.17.1` 的 `engines`、`files`、`unpackedSize` 与上一周下载量（2026-09-13 至 09-19）
