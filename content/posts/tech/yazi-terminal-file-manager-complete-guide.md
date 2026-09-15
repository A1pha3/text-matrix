---
title: "Yazi：极快的终端文件管理器"
date: "2026-04-11T14:20:52+08:00"
slug: yazi-terminal-file-manager-complete-guide
github_repo: "sxyazi/yazi"
source_key: "gh:sxyazi/yazi"
description: "Yazi 把异步 I/O、内置图片预览和 Lua 插件三者结合，让终端文件管理器第一次做到不依赖外部工具就能预览图片。本文拆解它的架构取舍与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "终端", "TUI", "Lua"]
---

# Yazi：异步 I/O、内置图片预览与 Lua 插件同处一个终端

## 学习目标

阅读本文后，你应该能够：

1. **理解 Yazi 的架构设计**：解释为什么 Yazi 把异步 I/O、内置图片预览、Lua 插件系统三者结合
2. **掌握异步 I/O 的价值**：描述异步 I/O 对文件管理器的关键作用，以及 Yazi 如何基于 Tokio 实现
3. **了解图片预览机制**：解释 Yazi 如何直接在 Rust 里解码图片并通过终端协议显示
4. **理解插件系统选择**：解释为什么 Yazi 选择 Lua 而不是 WASM 或 Python
5. **评估适用性**：根据 Yazi 的特性判断它是否适合你的工作场景

## 目录

1. [项目位置](#项目位置)
2. [异步 I/O 为什么对文件管理器关键](#异步-io-为什么对文件管理器关键)
3. [内置图片预览难在哪里](#内置图片预览难在哪里)
4. [为什么插件系统选 Lua](#为什么插件系统选-lua)
5. [虚拟文件系统与多实例协作](#虚拟文件系统与多实例协作)
6. [一次完整的任务流：浏览、预览与复制](#一次完整的任务流浏览预览与复制)
7. [自测题](#自测题)
8. [练习](#练习)
9. [进阶路径](#进阶路径)
10. [资料口径说明](#资料口径说明)

终端文件管理器赛道并不缺选手，ranger、lf、nnn 各有拥趸。Yazi 用 Rust 重写一遍，如果只比启动速度和帧率，很难构成切换理由——lf 的 goroutine 模型已经够快，nnn 在低资源环境下更轻。

Yazi 值得拆开看的地方在于它把三件通常各走各路的工程目标压进了同一个二进制：全异步 I/O、内置图片预览、Lua 插件系统。这三件事在工程上本来互相争资源——异步 I/O 要的是线程不被挂起，图片预览要抢 CPU 和解码管线，插件系统则要求一个稳定的 API 边界和沙箱。ranger 想预览图片要靠 w3m、Überzug 这类外部进程，lf 也得借助 chafa 或 Überzug++；Yazi 直接在 Rust 里解码图片，再适配 kitty、iTerm2、Sixel 等 10 余种终端，把像素写回终端。终端支持就开箱预览，不必再装一堆辅助工具。

本文按四条主线展开：异步 I/O 为什么对文件管理器是硬需求、内置图片预览的工程难点在哪、插件系统为什么选 Lua 而不是 WASM 或 Python，最后用一个完整的浏览-预览-复制任务流把这几条主线串起来，并给出采用顺序。

## 项目位置

| 指标 | 数值 |
|------|------|
| Stars | 42.2k |
| Forks | 1017 |
| 语言 | Rust 94.0%, Lua 5.0% |
| 最新版本 | v26.9.1 (2026-09-01) |
| 许可证 | MIT |
| 仓库 | sxyazi/yazi |

Yazi 目前处于 Public Beta，可以作为日常主力工具使用。Rust 占 94.0%，Lua 占 5.0%——这个比例对应 Yazi 的设计选择：核心引擎用 Rust 写死，扩展面留给 Lua。下面先看为什么这个分工不是随手定的。

## 异步 I/O 为什么对文件管理器关键

文件管理器的工作负载有两个特征：I/O 密集（读目录、读文件、复制、移动），且 I/O 之间天然可并行（同时浏览两个目录、后台复制的同时继续浏览）。同步 I/O 在这里会直接变成 UI 卡顿——打开一个有几千个文件的目录，主线程要等 readdir 返回，期间按键无响应。

Yazi 基于 Tokio 运行时，文件系统操作统一走异步引擎（底层是 `tokio::fs`），不直接调用会阻塞运行时的同步 `std::fs`。走异步的代价是所有 I/O 调用都要写成 `.await`，代码可读性略降；好处是 UI 线程永远不会因为某个文件操作被挂起。

异步带来的实际差别体现在三个场景：

- 大目录浏览：进入一个有上万个文件的目录，UI 不会冻结，可以先看到部分条目，剩余条目在后台流入。
- 后台复制：复制几个 GB 的文件时，仍然能用 `h/j/k/l` 继续浏览其他目录，复制进度在状态栏实时更新。
- 并发预览：滚动到下一个文件时，预览立即转向新文件，未完成的旧取图作废，不阻塞界面。

ranger 的同步模型在第一个场景就会暴露问题——Python 的 GIL 加上同步 I/O，大目录加载期间界面完全无响应。lf 用 Go 写，并发能力比 ranger 强，但图片预览仍然依赖外部进程。

### 模块划分

Yazi 采用 monorepo 结构，核心模块按职责切分：

| 模块 | 职责 |
|------|------|
| yazi-core | 核心逻辑、文件操作、任务调度 |
| yazi-adapter | 终端适配器（图片协议） |
| yazi-fm | 文件管理器主程序 |
| yazi-cli | `ya` 命令行接口 |
| yazi-config | 配置管理 |
| yazi-plugin | 插件系统 |
| yazi-scheduler | 任务调度器 |
| yazi-fs | 文件系统操作 |
| yazi-vfs | 虚拟文件系统（URL scheme 抽象） |
| yazi-sftp | SFTP 远程文件访问 |
| yazi-dds | 数据分发服务（跨实例通信） |
| yazi-proxy | 代理/Pub-Sub |
| yazi-shared | 共享类型和工具 |

`yazi-adapter` 单独拎出来值得注意——它把"终端图片适配"做成独立模块。这是 Yazi 能同时适配 10 余种终端又不让协议细节渗透进核心逻辑的关键。新增一种终端时，改动只落在 `yazi-adapter` 里，`yazi-core` 不用动。

### 任务调度

异步 I/O 只解决了"操作不阻塞运行时"这一层。文件管理器还要回答另一个问题：当多个 I/O 任务同时排队时，先做哪个。Yazi 的调度器（`yazi-scheduler`）没有把所有任务塞进一条全局队列，而是按类型拆成五条通道，每条通道各自维护一个优先级队列和独立的 worker 池：

```rust
// yazi-scheduler/src/worker.rs：五类任务各自一条优先级通道
let (file_tx, file_rx) = async_priority_channel::unbounded();
let (plugin_tx, plugin_rx) = async_priority_channel::unbounded();
let (fetch_tx, fetch_rx) = async_priority_channel::unbounded();
let (preload_tx, preload_rx) = async_priority_channel::unbounded();
let (size_tx, size_rx) = async_priority_channel::unbounded();
```

文件操作（复制、移动、删除）、插件调用、元数据获取、预加载、目录体积计算各走各的通道，互不挤占——预加载缩略图再多，也不会占掉复制文件的 worker。每个通道的并发数可以在 `yazi.toml` 的 `[tasks]` 段调整（`file_workers`、`preload_workers` 等），优先级则由入队时指定，同类任务里高优先级先出队。任务可以在任务管理器（`w` 打开）里手动取消：快速滚动文件列表时，作废的预加载任务留在队列里只会浪费 I/O，及时取消才不会拖慢当前可见文件的预览。

## 内置图片预览难在哪里

终端原本不是为图片设计的。字符终端只认字符网格，图片要显示出来，必须借助终端提供的扩展协议。问题在于：协议不止一种，而且互不兼容。

这种碎片化有历史原因。早期终端只处理文本，图片显示能力是各家终端模拟器后来各自扩展的——kitty 用 unicode placeholders，iTerm2 用 inline images，foot 和 Windows Terminal 用 Sixel，X11 终端要靠 Überzug++ 在窗口上叠图层。没有一个协议成为事实标准，终端文件管理器如果想"开箱即用"，就得把这些协议都适配一遍。

Yazi 内置适配以下终端：

| 终端 | 协议 | 支持状态 |
|------|------|----------|
| kitty (≥0.28.0) | Kitty unicode placeholders | 内置 |
| iTerm2 | Inline images | 内置 |
| WezTerm | Inline images | 内置 |
| Konsole | Kitty old protocol | 内置 |
| foot | Sixel | 内置 |
| Ghostty | Kitty unicode placeholders | 内置 |
| Windows Terminal (≥v1.22.10352) | Sixel | 内置 |
| st（带 Sixel patch） | Sixel | 内置 |
| Warp（仅 macOS/Linux） | Inline images | 内置 |
| Tabby | Inline images | 内置 |
| VSCode | Inline images | 内置 |
| Rio | Kitty unicode placeholders | ❌ 已知缺陷：图片渲染尺寸不正确 |
| Black Box | Sixel | 内置 |
| Bobcat | Inline images | 内置 |
| X11 / Wayland | 窗口系统协议 | 需 Überzug++（Wayland 仅 Hyprland、Sway、Niri、Wayfire） |
| 不支持任何协议 | ASCII art（Unicode block） | 需 Chafa ≥ 1.16.0 |

Yazi 启动时依据 `$TERM`、`$TERM_PROGRAM`、`$XDG_SESSION_TYPE` 自动匹配适配方式，按上表从上到下取第一个可用的；运行 `ya env` 可以查看当前实际命中的适配器（`Kgp`、`KgpOld`、`Iip`、`Sixel`、`X11`、`Wayland`、`Chafa`）。

适配只是第一步。图片在终端里显示还要解决解码和缩放——一张 4000×3000 的 JPEG 不能原样塞进 80×24 的终端窗口，得先解码、缩放到终端字符尺寸、再按协议编码发出去。

Yazi 把这条流水线做成了内置预览插件：图片文件的预览由预设的 `image.lua` 驱动，它调用 `ya.image_show()` / `ya.image_precache()` 两个 API，真正的解码和缩放在 Rust 侧完成（基于 image 库），然后按当前终端的适配方式输出。解码不依赖外部工具，内置支持的格式覆盖 PNG、JPEG、GIF、WebP、BMP、TIFF、ICO 等常见位图；其余格式走外部工具——SVG 用 `resvg`，HEIC、JPEG XL 和字体用 ImageMagick（`magick`），视频缩略图用 `ffmpeg`，PDF 用 `poppler`（`pdftoppm`），压缩包用 7-Zip。这些工具不装只是对应格式预览不可用，不影响文件管理本身。Yazi 还内置代码高亮，配合预加载机制，滚动到下一个文件时提前把缩略图备好。图片缓存默认落在系统缓存目录（重启自动清理），滚动回同一个文件时直接命中，不必重复解码；`[preview]` 段提供 `max_width`、`max_height`、`image_filter`、`image_quality` 等选项控制预览尺寸与缩放质量。

把图片预览做进核心，意味着 Yazi 必须自己维护一整套解码和协议适配代码，二进制体积和代码复杂度都比"调外部工具"高出一截。换回来的是协议适配从用户的终端环境收进了工具本身。这是 Yazi 和 ranger、lf 在工程取向上的一个明确分野：后两者把协议适配留给用户和外部工具，Yazi 把它收进 Rust 核心。

## 为什么插件系统选 Lua

Yazi 的插件用 Lua 5.5 编写。这个选择背后有几层考量。

WASM 听起来更现代，但 WASM 运行时嵌入 Rust 的成本不低，且 WASM 模块需要工具链编译，对插件作者门槛高——写一个插件要先装 Rust 工具链、配 wasm-pack、编译成 `.wasm` 文件再放进插件目录。Python 嵌入成本更高，还要带一个解释器运行时，且 Python 的 GIL 会和 Yazi 的异步模型冲突。Lua 的优势在于：解释器小（几百 KB）、嵌入 Rust 的绑定成熟（mlua）、插件作者不需要编译步骤，写完 `.lua` 文件直接生效。插件作者改一行配置就能看到效果，这种短反馈环对早期生态积累比运行时性能更重要——愿意写插件的人多了，生态才能起来。

插件目录结构如下——每个插件是一个以 `.yazi` 结尾的目录，放在配置目录的 `plugins/` 下，入口文件是 `main.lua`：

```text
~/.config/yazi/
├── init.lua                # 初始化脚本（同步上下文，可调用插件的 setup）
├── yazi.toml               # 主配置
├── keymap.toml             # 按键映射
├── plugins/
│   ├── my-plugin.yazi/     # 功能插件
│   │   ├── main.lua        # 插件入口
│   │   ├── README.md
│   │   └── LICENSE
│   └── bar.yazi/
│       ├── main.lua
│       ├── README.md
│       └── LICENSE
└── flavors/                # 主题（flavor）目录
```

插件按用途分两类：**功能插件**（绑定到按键，按下即执行一段逻辑）和**内置能力扩展**——在 `yazi.toml` 的 `[plugin]` 段里注册自定义的预览器（previewer）、预加载器（preloader）、spotter、fetcher，让某个 MIME 类型的文件走你的插件逻辑：

| 类型 | 说明 |
|------|------|
| 功能插件 | 绑定 `plugin <name>` 到按键，执行自定义动作 |
| previewer | 自定义某类文件的预览渲染（实现 `peek`/`seek`） |
| preloader | 自定义文件的预加载逻辑（实现 `preload`） |
| spotter | 自定义"文件信息"面板内容 |
| fetcher | 自定义文件的元数据获取（如 MIME 类型、大小） |

一个最小功能插件长这样——插件只返回一张带 `entry` 的 Lua 表，Yazi 以异步上下文调用它：

```lua
-- ~/.config/yazi/plugins/my-plugin.yazi/main.lua
local get_hovered = ya.sync(function()
  -- cx 只能在同步块（sync block）中访问
  local h = cx.active.current.hovered
  return h and tostring(h.url) or nil
end)

return {
  entry = function()
    local url = get_hovered()  -- 当前悬停的文件
    if url then
      ya.dbg(url)  -- 写入 ~/.local/state/yazi/yazi.log
    end
  end,
}
```

`cx` 是 Yazi 暴露给插件的全局上下文，`cx.active.current.hovered` 表示当前面板中悬停的文件。插件默认运行在异步上下文（async context），与主线程并发、不阻塞 UI，但异步线程拿不到 `cx` 里的数据，需要通过 `ya.sync()` 开一个同步块去读取；`ya.dbg()` 把调试信息写进日志。插件不需要编译，改完 `main.lua` 重启 Yazi 即生效。

插件本身不注册按键；按键到插件的绑定写在 `keymap.toml` 里：

```toml
# ~/.config/yazi/keymap.toml
[mgr]
prepend_keymap = [
  { on = "gx", run = "plugin my-plugin", desc = "运行我的插件" },
]
```

如果插件需要用户传参（比如绑定一个独立的预览器），`yazi.toml` 的 `[plugin]` 段负责注册。以自定义预览器为例，插件返回实现 `peek`/`seek` 方法的表，`peek` 负责在预览区绘制，`seek` 处理上下滚动；预加载器则实现 `preload`，返回 `(complete, err)` 表明任务是否完成，未完成会被自动重试。

插件也可以从 `init.lua` 接收配置——`init.lua` 是同步上下文，常用于初始化：

```lua
-- ~/.config/yazi/init.lua
require("my-plugin"):setup { key = "value" }
```

```lua
-- ~/.config/yazi/plugins/my-plugin.yazi/main.lua
return {
  setup = function(state, opts)
    state.key = opts.key  -- 保存用户配置到插件状态
  end,
}
```

Lua 的代价是性能不如原生 Rust，且沙箱能力比 WASM 弱——插件能调用的 API 由 Yazi 显式暴露，但 Lua 本身能访问的内存和系统资源不像 WASM 那样有硬边界。Yazi 的取舍是：插件做轻量扩展（按键动作、预览逻辑、UI 定制），重活（图片解码、大文件复制）留在 Rust 核心。

## 虚拟文件系统与多实例协作

本地文件的并发问题靠异步 I/O 解决了，远程文件也要纳入同一个界面。Yazi 的虚拟文件系统（VFS）做的是这件事——不同来源的文件在内部都用统一的 URL 表示，再按 scheme 分发到对应的引擎。scheme 在源码里就是一个三值枚举：

```rust
// yazi-shared/src/auth/scheme.rs
pub enum Scheme {
    Regular,
    Sftp,
    Custom(KebabCasedKey),
}
```

`Regular` 是本地文件系统，`Sftp` 是内置的 SFTP 引擎，`Custom` 则开放给 Lua 写的 VFS 引擎——任何符合 kebab-case 命名的 scheme 都可以在 `vfs.toml` 里注册，由插件提供目录读取、元数据等操作（官方插件仓库的 `vfs-demo.yazi` 是最小示例），内置的回收站视图 `trash:///` 就是用这套机制实现的。

这套抽象的价值：处理 `sftp://` 远程文件时，目录浏览、选中、复制这些操作与本地完全一致，界面不用区分来源。SFTP 服务器在 `vfs.toml` 里注册：

```toml
# ~/.config/yazi/vfs.toml
[sftp.my-server]
host = "1.2.3.4"
user = "root"
port = 22
```

注册后 `yazi sftp://my-server` 就能直接以远程目录为工作目录启动。认证默认走 SSH agent（`$SSH_AUTH_SOCK` 指定的套接字），也可以在 `vfs.toml` 里改用 `key_file`（配 `key_passphrase`）或 `password`，或用 `identity_agent` 指定其他 agent 套接字。回收站由内置的 trash 插件实现——`d` 删除的文件进入 `trash://`，`g t` 跳到回收站查看，在回收站里按 `O` 选择 trash 开启器即可恢复选中的文件，也可以直接清空回收站。

多实例协作走另一条路——DDS（Data Distribution Service）。它采用客户端-服务器架构但不需要额外进程，实例之间通过 Lua 的发布-订阅模型通信，同时支持状态持久化：以 `@` 开头的消息会持久化存储，新实例启动时自动恢复，向同一 kind 发送 `nil` 则取消持久化。

```text
┌──────────────────────────────────────┐
│            Yazi 实例 A                │
│   ┌─────────┐      ┌──────────────┐ │
│   │  DDS    │◄────►│  Lua 插件    │ │
│   │ pub/sub │      └──────────────┘ │
│   └────┬────┘                      │
└────────┼─────────────────────────────┘
         │ 实例间直接通信（无额外进程）
┌────────▼─────────────────────────────┐
│            Yazi 实例 B                │
│   ┌─────────┐      ┌──────────────┐ │
│   │  DDS    │◄────►│  Lua 插件    │ │
│   │ pub/sub │      └──────────────┘ │
│   └─────────┘                      │
└──────────────────────────────────────┘
```

DDS 有两条对外通道。**消息通道**用 `ya pub` 向当前实例（`$YAZI_ID` 标识）发消息、`ya pub-to` 向指定实例发消息，消息体支持字符串、列表和 JSON 三种格式；**动作通道**用 `ya emit` / `ya emit-to` 把按键动作直接发给实例执行：

```bash
# 在当前 Yazi 子 shell 中，请求当前实例解压两个压缩包
ya pub extract --list "/root/a.zip" "/root/b.7z"

# 向指定实例发一条自定义消息
ya pub-to "$YAZI_ID" my-event --str "Hello world!"

# 让另一个实例切换到 /tmp 目录
ya emit-to <receiver> cd /tmp
```

典型用途是跨实例同步：外部脚本把文件列表推给正在运行的 Yazi，或者让两个实例共享同一份状态。

## 一次完整的任务流：浏览、预览与复制

把前面几条主线串起来。假设场景：在一个有 5000 张图片的目录里，浏览、预览、把选中的几张复制到另一个目录。

1. 用户按下 `j` 移动到下一个文件。Yazi 把"光标下移"作为 UI 任务立即执行，状态栏同步更新。
2. 光标停在 `photo_1234.jpg` 上。Yazi 触发预览：先查图片缓存，命中就直接显示；未命中则由 preload 任务在 Rust 侧解码、缩放并写入缓存，再按当前终端的适配方式（如 kitty）把像素发到终端。
3. 用户继续按 `j` 快速下移。预览由 peek 逻辑驱动，每次光标移动都以新文件为目标重新取缓存、重新渲染，旧一次未完成的取图自然作废；已入队的预加载任务也可以在任务管理器里取消。这避免了快速滚动时堆积无用 I/O。
4. 用户按 `Space` 选中当前文件，继续浏览选中另外两张。选中状态在 UI 层维护，不触发 I/O。
5. 用户按 `y` 把选中的文件标记为已 yank（复制），再切到目标目录。yank 状态保存在进程内，同样不触发 I/O。
6. 在目标目录按 `p` 发起粘贴。调度器把粘贴任务插入 file 通道，三个文件的复制并发执行，进度在状态栏实时更新。
7. 复制期间用户继续浏览，UI 不卡顿——复制走异步 I/O，UI 走主线程，互不阻塞。
8. 复制完成，状态栏提示。

这八步里，异步 I/O 保证 UI 不被挂起，任务调度决定哪个 I/O 先跑、哪个被取消，图片预览负责解码和协议适配，DDS 把跨实例/跨标签页的状态同步起来。任何一条退回同步模型，体验都会塌——UI 卡、预览慢、或者复制阻塞浏览，至少踩中一条。

## 与 ranger/lf 的工程取舍

把 Yazi 放回赛道看会更清楚。

| 维度 | ranger | lf | Yazi |
|------|--------|-----|------|
| 语言 | Python | Go | Rust |
| I/O 模型 | 同步 | 并发（goroutine） | 异步（Tokio） |
| 图片预览 | 外部工具（w3m、Überzug） | 外部工具（chafa、Überzug++） | 内置 |
| 插件语言 | Python | Shell | Lua |
| 插件生态 | 成熟，Python 生态可用 | 较少 | 20 余个官方插件，仍在早期 |
| 配置 | Python 脚本 | Shell 风格 | TOML + Lua |

ranger 的优势是 Python 生态——任何能写 Python 的人都能扩展它，且十年积累的插件数量多。劣势是同步 I/O 和 GIL，大目录和图片预览体验差。

lf 用 Go，并发能力强，二进制单文件部署方便。但图片预览仍然依赖外部工具，且 Shell 风格的配置对复杂逻辑表达力有限。

Yazi 的取舍可以拆成三句：Rust 换的是性能和内存安全，内置图片预览换的是用户侧零配置，Lua 换的是插件门槛和扩展能力之间的平衡。代价同样具体——Rust 学习曲线陡，插件生态比 ranger 小，Lua 沙箱不如 WASM 严格。

ranger、lf、Yazi 三者并非互相替代。已经在 ranger 上有一套 Python 插件工作流、且不依赖图片预览的人，没有强理由切换。日常需要预览图片、在大目录里频繁切换、且终端支持 kitty 或 Sixel 的用户，Yazi 的体验差异是可感知的。

## 安装与基础配置

```bash
# macOS（Homebrew，连同常用可选依赖；ffmpeg-full/imagemagick-full 提供完整格式支持）
brew install yazi ffmpeg-full sevenzip jq poppler fd ripgrep fzf zoxide resvg imagemagick-full font-symbols-only-nerd-font
brew link ffmpeg-full imagemagick-full -f --overwrite

# Debian/Ubuntu（官方 APT 仓库，稳定版）
curl -fsSL https://yazi-rs.github.io/builds/yazi-keyring.gpg | sudo tee /usr/share/keyrings/yazi-keyring.gpg >/dev/null
echo 'deb [signed-by=/usr/share/keyrings/yazi-keyring.gpg] https://yazi-rs.github.io/builds/ stable main' | sudo tee /etc/apt/sources.list.d/yazi.list >/dev/null
sudo apt update && sudo apt install yazi

# Rust 源码编译（crates.io 上通过 yazi-build 统一安装）
cargo install --force yazi-build
```

基础配置走 TOML，不是 Lua——Lua 只用于插件。主配置文件是 `~/.config/yazi/yazi.toml`，配置段对应不同职责，核心段是 `[mgr]`（文件列表）和 `[preview]`（预览）：

```toml
# ~/.config/yazi/yazi.toml
[mgr]
show_hidden = true
sort_by = "mtime"          # 按修改时间排序
sort_dir_first = true      # 目录优先
sort_sensitive = false     # 不区分大小写

[preview]
max_width = 1000           # 图片预览最大宽度
max_height = 1000          # 图片预览最大高度
image_filter = "lanczos3"  # 缩放滤镜，质量最高但最慢

[open]
prepend_rules = [
  { url = "*.json", use = "edit" },
]

[tasks]
file_workers = 8           # 并发的文件操作数
```

主题不写在 `yazi.toml`，而是独立的 `theme.toml`，通过 `[flavor]` 段引用已安装的主题包（flavor）：

```toml
# ~/.config/yazi/theme.toml
[flavor]
dark  = "catppuccin-mocha"  # 深色模式使用的 flavor
light = "catppuccin-latte"  # 浅色模式使用的 flavor
```

配置目录结构：

```text
~/.config/yazi/
├── yazi.toml        # 主配置
├── keymap.toml      # 按键映射
├── theme.toml       # 主题：通过 [flavor] 引用已装的主题包
├── init.lua         # 初始化脚本（同步上下文，可调用插件的 setup）
├── package.toml     # 插件/主题依赖锁定（ya pkg 自动维护）
├── plugins/         # 插件目录
│   └── *.yazi/      #   每个插件一个目录
│       ├── main.lua #   插件入口
│       ├── README.md
│       └── LICENSE
└── flavors/         # 主题（flavor）目录
    └── *.yazi/
        ├── flavor.toml   # 主题配色
        └── tmtheme.xml   # 代码高亮配色
```

### 快捷键速查

Yazi 默认 Vim 风格，下表摘取最常用的映射（完整列表见官方 `keymap-default.toml`）：

| 快捷键 | 功能 |
|--------|------|
| `h/j/k/l` | 返回父目录 / 下移 / 上移 / 进入目录 |
| `H` / `L` | 目录历史后退 / 前进 |
| `gg` / `G` | 跳转到顶部 / 底部 |
| `Space` | 选中 / 取消选中当前文件 |
| `v` / `V` | 进入可视模式（选中 / 反选） |
| `Ctrl+a` | 全选 |
| `y` | 复制（yank）选中文件 |
| `x` | 剪切（yank --cut） |
| `p` / `P` | 粘贴 / 覆盖粘贴 |
| `Y` / `X` | 取消 yank |
| `d` / `D` | 移入回收站 / 永久删除 |
| `a` | 创建文件或目录 |
| `r` | 重命名 |
| `o` / `Enter` | 打开选中文件 |
| `cc` | 复制文件路径到剪贴板 |
| `s` / `S` | 按文件名搜索（fd）/ 按内容搜索（rg） |
| `/` | 在当前目录查找文件 |
| `z` / `Z` | 通过 fzf 跳转 / 通过 zoxide 跳转 |
| `tt` | 新建标签页 |
| `[` / `]` | 切换上一个 / 下一个标签页 |
| `Tab` | 打开悬停文件的 spot 信息面板 |
| `w` | 打开任务管理器 |
| `q` / `Ctrl+c` | 退出 / 关闭当前标签页 |
| `~` 或 `F1` | 打开帮助 |

注意 `Ctrl+c` 在 Yazi 里是关闭当前标签页（最后一个标签页时退出整个程序），不是中断、也不是复制——复制是 `y`。这和 shell 习惯冲突，初次使用容易误触，可以把关闭标签页的按键在 `keymap.toml` 里重映射。

### 高级用法

```bash
# 以指定目录为启动位置（位置参数，可同时给多个条目）
yazi /tmp

# 查看版本
yazi --version
```

Yazi 自己改不了 shell 的工作目录——终端文件管理器的常见痛点就是直接运行 `yazi` 退出后，shell 不会跟着切换。官方的解法是 `--cwd-file` 参数：退出时把最后浏览的目录写入指定文件，再由一个 shell 包装函数读取并 `cd` 过去。官方文档给出的 Bash/Zsh 版本：

```bash
# 官方推荐的包装函数：用 y 代替 yazi 启动，退出后 shell 跟随目录
function y() {
    local tmp cwd; tmp="$(mktemp -t "yazi-cwd.XXXXXX")"
    command yazi "$@" --cwd-file="$tmp"
    IFS= read -r -d '' cwd < "$tmp"
    [ "$cwd" != "$PWD" ] && [ -d "$cwd" ] && builtin cd -- "$cwd" || builtin true
    command rm -f -- "$tmp"
}
```

配合这个函数，按 `q` 退出会把目录写入 cwd-file（默认行为），shell 随即切换过去；不想让 shell 跟随时用 `Q` 退出，它会跳过 cwd-file 输出。

## 插件分发

Yazi 自带包管理器 `ya`，用于安装插件和主题（flavor）：

```bash
# 安装插件（从官方插件仓库装 git.yazi）
ya pkg add yazi-rs/plugins:git

# 安装主题（flavor）
ya pkg add yazi-rs/flavors:catppuccin

# 更新所有已安装的包
ya pkg upgrade

# 列出已安装的包
ya pkg list

# 在新机器上按 package.toml 的锁定版本批量安装
ya pkg install
```

`ya pkg add` 会自动从 GitHub 克隆对应仓库、把包复制到 `plugins/` 或 `flavors/` 目录，并把锁定版本（commit 与 hash）写进 `package.toml`——这样换机器后一条 `ya pkg install` 就能恢复完全相同的环境。

社区资源：

- 官方插件仓库：https://github.com/yazi-rs/plugins（20 余个）
- 主题（flavor）仓库：https://github.com/yazi-rs/flavors
- 插件开发文档：https://yazi-rs.github.io/docs/plugins/overview

## 性能调优与排查

### 性能优化

Yazi 的预览缓存默认落在系统缓存目录、自动启用，无需手动开关；值得调的配置集中在 `[preview]` 和 `[tasks]` 两段：

```toml
# yazi.toml 性能相关配置
[preview]
# 把预览缓存改成持久化目录（默认系统缓存目录，重启即清）
cache_dir = "/path/to/cache"
image_quality = 80        # 预缓存图片质量（50-90），越大越清晰也越耗 CPU
image_filter = "lanczos3" # 缩放滤镜：nearest < triangle < catmull-rom < lanczos3

[tasks]
file_workers = 8          # 并发的文件操作数，可按机器核数调整
preload_workers = 4       # 并发的预加载任务数
image_alloc = 0           # 单张图片解码的内存上限（字节），0 表示不限制
```

预览缓存对图片密集目录效果明显——重复浏览同一目录时，缩略图直接从缓存取，跳过解码。`image_alloc` 限制单张图片解码的内存占用，浏览超大图时防内存暴涨。另外，`fd`、`rg`、`fzf`、`zoxide` 这类外部工具增强的是搜索和跳转能力（`s` 键用 fd 按文件名搜索、`S` 键用 rg 按内容搜索），不是替代目录读取——目录读取本身走内置异步实现。

### 调试

```bash
# 启用调试日志（不设置则不记录任何日志）
YAZI_LOG=debug yazi

# 调试构建下可叠加堆栈回溯
YAZI_LOG=debug RUST_BACKTRACE=1 ./target/debug/yazi

# 查看日志
tail -f ~/.local/state/yazi/yazi.log
```

`YAZI_LOG` 的取值从高到低为 `debug`、`info`、`warn`、`error`，日志写到 `~/.local/state/yazi/yazi.log`（Unix-like）。插件调试用 `ya.dbg()` / `ya.err()` 输出到同一文件。

### 常见问题排查

| 问题 | 解决方案 |
|------|----------|
| 图片不显示 | 确认终端在协议支持列表里；用 `ya env` 查看实际命中的适配器，再用 `YAZI_LOG=debug` 启动查握手失败记录 |
| 预览加载慢 | 确认已安装对应格式的外部工具（ffmpeg/poppler/7-Zip/ImageMagick 等）；缩小 `max_width`/`max_height` 或调低 `image_quality` 减少解码开销 |
| 快捷键冲突 | 检查 `keymap.toml` 中的映射 |
| 插件报错 | 看 `~/.local/state/yazi/yazi.log` 中的插件错误输出 |

图片不显示是最常见的问题。排查顺序：先用 `ya env` 确认适配器命中情况（输出里的 `Drivers.matches` 字段直接给出当前协议），再确认该格式是否需要外部工具（如 SVG 要 resvg），最后用 `YAZI_LOG=debug` 启动看协议握手失败日志。

## 适用边界与采用顺序

Yazi 并非在所有场景下都值得切换。

**适合切换的场景**：

- 日常在终端里管理文件，且终端支持 kitty、Sixel 或 iTerm2 协议。
- 经常需要预览图片、PDF、视频缩略图，不想为每种格式装外部工具。
- 经常处理大目录（上千文件），对 UI 响应敏感。
- 愿意用 Lua 写少量插件定制工作流。

**不必急着切换的场景**：

- 已经在 ranger 上有成熟的 Python 插件工作流，且不依赖图片预览。
- 终端不支持任何图片协议，且不能换终端（如某些服务器场景）。
- 只用 `ls` + `cd` 偶尔看文件，文件管理不是日常工作流。

**采用顺序建议**：

1. 先在支持的终端里跑起来，确认图片预览开箱可用。这一步验证的是你的终端是否在协议支持列表里。图片协议由 Yazi 自动探测匹配，不需要手动配置。如果图片不显示，回到前面的协议表排查，不要急着往下走。
2. 把常用快捷键映射到自己的习惯（`keymap.toml`）。Yazi 默认 Vim 风格，但复制剪切用的是 `y`/`x`、`Ctrl+c` 关闭标签页，从 shell 或 ranger 习惯迁移过来的用户可能要先适应这几个键位。
3. 从官方插件仓库装 1-2 个高频插件（如 `git.yazi`）。这一步验证的是插件系统是否正常工作，以及 `ya pkg add` 命令能否拉取远程插件。
4. 只在前三步都顺畅后，再考虑写自定义插件。写插件前先读官方插件的 `main.lua`，了解 Yazi 暴露的 API 边界——Lua 插件能做的是按键动作、预览逻辑、UI 定制，重活（图片解码、大文件复制）由 Rust 核心处理。

## 常见问题

**Q: Yazi 和 ranger/lf 有什么区别？**

A: Yazi 用 Rust 编写，原生支持异步 I/O，内置图片预览（无需配置），插件系统基于 Lua。ranger 用 Python、lf 用 Go 编写，更轻量但图片预览依赖外部工具。

**Q: 支持 Windows 吗？**

A: 支持。Windows 上可以用 WinGet（`winget install sxyazi.yazi`）或 Scoop 安装，Windows Terminal (≥v1.22.10352) 下可使用 Sixel 协议图片预览。

**Q: 如何自定义快捷键？**

A: 按键映射统一写在 `keymap.toml` 里。用 `prepend_keymap` / `append_keymap` 在默认键位之上叠加自定义映射，而不是覆盖全部默认键位：

```toml
# ~/.config/yazi/keymap.toml
[mgr]
prepend_keymap = [
  { on = "gx", run = "plugin my-plugin", desc = "运行我的插件" },
]
```

按键到插件的绑定也走这里（`run = "plugin <name>"`），插件本身不注册按键。

**Q: 插件开发需要学 Rust 吗？**

A: 不需要。Yazi 插件用 Lua 编写。Rust 只用于核心引擎和性能敏感的内置功能。

**Q: 如何报告 Bug？**

A: https://github.com/sxyazi/yazi/issues

## 相关资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/sxyazi/yazi |
| 文档 | https://yazi-rs.github.io/docs/quick-start |
| 插件仓库 | https://github.com/yazi-rs/plugins |
| 主题（flavor）列表 | https://github.com/yazi-rs/flavors |
| Discord (英文) | https://discord.gg/qfADduSdJu |
| Telegram (中文) | https://t.me/yazi_rs |

性能分析文章值得读一遍：

> 为什么 Yazi 这么快？
> https://yazi-rs.github.io/blog/why-is-yazi-fast
>
> 深入解析 Yazi 的异步架构、任务调度和预加载机制。

贡献流程：

```bash
# Fork 后克隆
git clone https://github.com/YOUR_NAME/yazi.git
cd yazi

# 开发
cargo run

# 测试
cargo test

# 提交 PR
git checkout -b feat/your-feature
```

---

## 自测题

1. **Yazi 与其他终端文件管理器（如 ranger、lf）的核心区别是什么？**
   <details>
   <summary>查看答案</summary>
   Yazi 把异步 I/O、内置图片预览、Lua 插件系统三者结合在同一个二进制中，而不依赖外部工具。
   </details>

2. **为什么 Yazi 选择异步 I/O？**
   <details>
   <summary>查看答案</summary>
   文件管理器的工作负载是 I/O 密集型的，异步 I/O 可以避免 UI 卡顿，支持大目录浏览、后台复制、并发预览等场景。
   </details>

3. **Yazi 如何预览图片？**
   <details>
   <summary>查看答案</summary>
   预览由内置的 image.lua 插件驱动，解码和缩放在 Rust 侧完成（基于 image 库），再按当前终端的适配方式（kitty、Sixel、iTerm2 等）把像素写回终端。
   </details>

4. **为什么 Yazi 的插件系统选择 Lua 而不是 WASM 或 Python？**
   <details>
   <summary>查看答案</summary>
   Lua 轻量、无需编译即可生效，且与 Yazi 的异步模型配合好，适合作为插件语言。WASM 需要工具链编译、门槛高；Python 嵌入成本高，且 GIL 与异步模型冲突。
   </details>

5. **如何贡献 Yazi 项目？**
   <details>
   <summary>查看答案</summary>
   Fork 仓库，克隆到本地，修改代码，运行 `cargo run` 测试，运行 `cargo test` 确保测试通过，然后提交 PR。
   </details>

---

## 练习

### 练习 1：安装并试用 Yazi

按照官方文档安装 Yazi，然后试用基本功能。尝试：
- 浏览目录
- 预览图片
- 复制/移动文件
- 自定义配色方案

### 练习 2：配置 Lua 插件

编写一个简单的 Lua 插件，定制 Yazi 的行为。尝试：
- 创建 `~/.config/yazi/plugins/my-plugin.yazi/main.lua`，返回一个带 `entry` 的表
- 在 `keymap.toml` 里用 `plugin my-plugin` 绑定按键
- 如果做的是预览器，改在 `yazi.toml` 的 `[plugin]` 段按 MIME 类型注册

### 练习 3：研究任务调度实现

阅读 Yazi 源码中 `yazi-scheduler/src/worker.rs`，理解其任务调度实现。尝试：
- 找到 file、plugin、fetch、preload、size 五条任务通道
- 理解每类任务为什么用独立的优先级通道和 worker 池
- 对照 `yazi.toml` 的 `[tasks]` 段，解释 `file_workers`、`preload_workers` 分别控制哪条通道的并发数

---

## 进阶路径

1. **深入研究异步 I/O**：理解 Tokio 运行时、async/await 模式、线程池配置
2. **研究终端图片协议**：理解 kitty、Sixel、iTerm2 等协议的工作原理
3. **编写复杂 Lua 插件**：为 Yazi 添加自定义功能（如 Git 集成、Docker 集成）
4. **贡献 Yazi 核心**：提交 PR 修复 bug 或添加新功能
5. **研究 Rust TUI 开发**：理解 Ratatui 等 TUI 框架的设计

---

## 资料口径说明

1. **信息来源与时效性**：本文基于 sxyazi/yazi 仓库的 README、官方文档（安装、图片预览、配置、插件、VFS、DDS、CLI、快速上手）和 GitHub 仓库数据（采集时间 2026-09-15，stars 42.2k、最新版本 v26.9.1）。项目处于 Public Beta，具体细节可能已更新。
2. **技术细节验证**：任务调度通道（`yazi-scheduler/src/worker.rs`）、scheme 枚举（`yazi-shared/src/auth/scheme.rs`）、图片预览插件（`yazi-plugin/preset/plugins/image.lua`）、回收站恢复（`trash.lua` 与默认 opener 配置）等行为均对照 v26.9.1 源码核实；未在实际环境中完整运行验证。
3. **判断与建议的边界**：本文对 Yazi 适用场景与局限性的判断基于公开信息，实际体验可能因个人需求而异。
4. **未覆盖的内容**：本文未深入讨论 Yazi 的完整配置选项、性能基准测试、与其他文件管理器的详细对比等。
5. **术语使用说明**：本文保留 Yazi、Tokio、Lua、Rust 等专有名词，首次出现时附上中文释义。
6. **更新记录**：本文撰写于 2026-04-11；2026-09-02 依据官方文档修正了配置段名（`[mgr]`/`[preview]`）、插件命令（`ya pkg`）、调试方式（`YAZI_LOG`）、VFS scheme（`sftp://`）与回收站恢复方式等过时信息；2026-09-15 对照 v26.9.1 文档与源码修正了 Rio 终端支持状态（官方标注图片渲染尺寸缺陷）、`yazi --cwd` 不存在的 CLI 参数、调度器与图片解码的真实实现，并更新仓库数据。

---

_本文基于 Yazi v26.9.1_
