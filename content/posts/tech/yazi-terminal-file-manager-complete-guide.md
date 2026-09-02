---
title: "Yazi：极快的终端文件管理器"
date: "2026-04-11T14:20:52+08:00"
slug: yazi-terminal-file-manager-complete-guide
github_repo: "sxyazi/yazi"
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
3. [内置图片预览的工程难点](#内置图片预览的工程难点)
4. [插件系统为什么选 Lua](#插件系统为什么选-lua)
5. [任务流案例](#任务流案例)
6. [自测题](#自测题)
7. [练习](#练习)
8. [进阶路径](#进阶路径)
9. [资料口径说明](#资料口径说明)

终端文件管理器赛道并不缺选手，ranger、lf、nnn 各有拥趸。Yazi 用 Rust 重写一遍，如果只比启动速度和帧率，很难构成切换理由——lf 的 goroutine 模型已经够快，nnn 在低资源环境下更轻。

Yazi 值得拆开看的地方在于它把三件通常各走各路的工程目标压进了同一个二进制：全异步 I/O、内置图片预览、Lua 插件系统。这三件事在工程上本来互相争资源——异步 I/O 要的是线程不被挂起，图片预览要抢 CPU 和解码管线，插件系统则要求一个稳定的 API 边界和沙箱。ranger 想预览图片要靠 w3m、Überzug 这类外部进程，lf 也得借助 chafa 或 Überzug++；Yazi 直接在 Rust 里解码 PNG/JPEG/GIF/WebP，再通过 kitty、Sixel、iTerm2 等 10 余种终端协议把像素写回终端。终端支持就开箱预览，不必再装一堆辅助工具。

本文按四条主线展开：异步 I/O 为什么对文件管理器是硬需求、内置图片预览的工程难点在哪、插件系统为什么选 Lua 而不是 WASM 或 Python，最后用一个完整的浏览-预览-复制任务流把这几条主线串起来，并给出采用顺序。

## 项目位置

| 指标 | 数值 |
|------|------|
| Stars | 41.9k |
| Forks | 1000 |
| 语言 | Rust 94.5%, Lua 4.6% |
| 最新版本 | v26.9.1 (2026-09-01) |
| 许可证 | MIT |
| 仓库 | sxyazi/yazi |

Yazi 目前处于 Public Beta，可以作为日常主力工具使用。Rust 占 94.5%，Lua 占 4.6%——这个比例对应 Yazi 的设计选择：核心引擎用 Rust 写死，扩展面留给 Lua。下面先看为什么这个分工不是随手定的。

## 异步 I/O 为什么对文件管理器关键

文件管理器的工作负载有两个特征：I/O 密集（读目录、读文件、复制、移动），且 I/O 之间天然可并行（同时浏览两个目录、后台复制的同时继续浏览）。同步 I/O 在这里会直接变成 UI 卡顿——打开一个有几千个文件的目录，主线程要等 readdir 返回，期间按键无响应。

Yazi 基于 Tokio 运行时把所有 I/O 操作做成异步，CPU 任务分散到多个线程：

```rust
// 示意代码：Yazi 的 I/O 全部走 tokio::fs，不直接调用阻塞的 std::fs
pub struct IoWorker {
    pool: ThreadPool,
    rx: Receiver<IoRequest>,
}

impl IoWorker {
    pub async fn read_file(&self, path: PathBuf) -> Result<Vec<u8>> {
        tokio::fs::read(&path).await
    }

    pub async fn list_dir(&self, path: PathBuf) -> Result<Vec<DirEntry>> {
        tokio::fs::read_dir(&path)
            .await?
            .entries()
            .collect()
            .await
    }
}
```

`IoWorker` 把文件读取和目录列表都走 `tokio::fs`，而不是 `std::fs`——后者会阻塞 Tokio 运行时，等于把整个 UI 卡住。走 `tokio::fs` 的副作用是所有 I/O 调用都要写成 `.await`，代码可读性略降；好处是 UI 线程永远不会因为某个文件操作被挂起。

异步带来的实际差别体现在三个场景：

- 大目录浏览：进入一个有上万个文件的目录，UI 不会冻结，可以先看到部分条目，剩余条目在后台流入。
- 后台复制：复制几个 GB 的文件时，仍然能用 `h/j/k/l` 继续浏览其他目录，复制进度在状态栏实时更新。
- 并发预览：滚动到下一个文件时，前一个文件的预览任务可以被取消或降级，新文件的预览优先处理。

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

`yazi-adapter` 单独拎出来值得注意——它把"终端图片协议适配"做成独立模块。这是 Yazi 能同时支持 10 余种协议又不让协议细节渗透进核心逻辑的关键。新增一个终端协议时，改动只落在 `yazi-adapter` 里，`yazi-core` 不用动。

### 任务调度

异步 I/O 只解决了"操作不阻塞运行时"这一层。文件管理器还要回答另一个问题：当多个 I/O 任务同时排队时，先做哪个。Yazi 的任务调度器维护一个优先级队列：

```rust
// 示意代码：调度器按优先级排队任务，支持取消
pub struct Scheduler {
    tasks: PriorityQueue<Task>,
    worker_pool: Vec<Worker>,
}

impl Scheduler {
    // 高优先级任务（如 UI 更新）优先处理
    pub fn schedule(&mut self, task: Task) {
        self.tasks.push(task.priority, task);
    }

    // 任务取消支持
    pub fn cancel(&mut self, task_id: u64) {
        self.tasks.remove_if(|t| t.id == task_id);
    }
}
```

调度优先级大致是：UI 任务 > 文件操作 > 后台任务。这个顺序的逻辑是——UI 卡顿用户立刻能感知，文件操作慢一点用户可以等状态栏更新，后台任务（如预加载缩略图）最不紧急。任务取消是另一条容易被忽略的链路：快速滚动文件列表时，前一个文件的预览任务如果不取消，会堆积成大量无用的 I/O，反而拖慢当前可见文件的预览。

## 内置图片预览难在哪里

终端原本不是为图片设计的。字符终端只认字符网格，图片要显示出来，必须借助终端提供的扩展协议。问题在于：协议不止一种，而且互不兼容。

这种碎片化有历史原因。早期终端只处理文本，图片显示能力是各家终端模拟器后来各自扩展的——kitty 用 unicode placeholders，iTerm2 用 inline images，foot 和 Windows Terminal 用 Sixel，X11 终端要靠 Überzug++ 在窗口上叠图层。没有一个协议成为事实标准，终端文件管理器如果想"开箱即用"，就得把这些协议都适配一遍。

Yazi 内置支持 10 余种协议：

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
| Rio (≥0.3.9) | Kitty unicode placeholders | 内置 |
| Black Box | Sixel | 内置 |
| Bobcat | Inline images | 内置 |
| X11 / Wayland | 窗口系统协议 | 需 Überzug++ |
| 不支持任何协议 | ASCII art (Chafa) | 需安装 |

适配只是第一步。图片在终端里显示还要解决解码和缩放——一张 4000×3000 的 JPEG 不能原样塞进 80×24 的终端窗口，得先解码、缩放到终端字符尺寸、再按协议编码发出去。Yazi 直接在 Rust 里做这件事：

```rust
// 示意代码：按格式分发解码，配合 LRU 缓存
pub struct ImageDecoder {
    cache: LruCache<PathBuf, CachedImage>,
}

impl ImageDecoder {
    pub fn decode(&mut self, path: &Path) -> Result<CachedImage> {
        let data = self.read_file(path)?;
        let format = self.detect_format(&data)?;

        match format {
            Format::Png => self.decode_png(&data),
            Format::Jpeg => self.decode_jpeg(&data),
            Format::Gif => self.decode_gif(&data)?,
            // 其他格式走通用解码路径
        }
    }
}
```

解码不依赖外部工具，但格式覆盖有边界：PNG、JPEG、GIF、WebP 等常见位图格式由 Yazi 内置解码；其余格式走外部工具——SVG 用 `resvg`，HEIC、JPEG XL 和字体用 ImageMagick（`magick`），视频缩略图用 `ffmpeg`，PDF 用 `poppler`（`pdftoppm`），压缩包用 7-Zip。这些工具不装只是对应格式预览不可用，不影响文件管理本身。Yazi 还内置代码高亮，配合预加载机制，滚动到下一个文件时提前把缩略图备好。图片缓存默认落在系统缓存目录，滚动回同一个文件时直接命中，不必重复解码；`[preview]` 段提供 `max_width`、`max_height`、`image_filter`、`image_quality` 等选项控制预览尺寸与缩放质量。

把图片预览做进核心，意味着 Yazi 必须自己维护一整套解码和协议适配代码，二进制体积和代码复杂度都比"调外部工具"高出一截。换回来的是用户侧的配置成本接近零——不必再为图片预览装一堆辅助工具。原本散落在用户侧的协议适配工作被收进了工具本身。这是 Yazi 和 ranger、lf 在工程取向上的一个明确分野：后两者把协议适配留给用户和外部工具，Yazi 把它收进 Rust 核心。

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

本地文件的并发问题靠异步 I/O 解决了，远程文件也要纳入同一个界面。Yazi 的虚拟文件系统（VFS）做的是这件事——不同来源的文件在内部都用统一的 URL 表示，再按 scheme 分发到对应的实现：

| URL scheme | 来源 | 说明 |
|------------|------|------|
| `local://` | 本地文件系统 | 默认来源 |
| `sftp://` | 远程服务器 | 内置 SFTP 支持，服务器需在 `vfs.toml` 里注册 |
| `trash://` | 回收站 | 已删除文件的浏览与恢复 |

```rust
// 示意代码：VFS 按 URL scheme 分发到对应实现
pub enum UrlScheme {
    Local,
    Sftp,
    Trash,
}

impl UrlScheme {
    pub fn parse(url: &Url) -> UrlScheme {
        match url.scheme() {
            "local" => UrlScheme::Local,
            "sftp"  => UrlScheme::Sftp,
            "trash" => UrlScheme::Trash,
            _       => UrlScheme::Local,
        }
    }
}
```

这套抽象的价值：处理 `sftp://` 远程文件时，目录浏览、选中、复制这些操作与本地完全一致，界面不用区分来源。SFTP 服务器在 `vfs.toml` 里注册：

```toml
# ~/.config/yazi/vfs.toml
[sftp.my-server]
host = "1.2.3.4"
user = "root"
port = 22
```

注册后 `yazi sftp://my-server` 就能直接以远程目录为工作目录启动，认证走 SSH agent 或 `key_file`/`password` 选项。回收站由内置的 trash 插件实现——`d` 删除的文件进入 `trash://`，`g t` 跳到回收站查看，在回收站里按 `O` 选择 trash 开启器即可恢复选中的文件，也可以直接清空回收站。Yazi 还支持自定义搜索引擎，把搜索结果当作可浏览的虚拟来源。

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

## 一次完整的任务流：浏览 + 预览 + 复制

把前面几条主线串起来。假设场景：在一个有 5000 张图片的目录里，浏览、预览、把选中的几张复制到另一个目录。

1. 用户按下 `j` 移动到下一个文件。Yazi 把"光标下移"作为 UI 任务立即执行，状态栏同步更新。
2. 光标停在 `photo_1234.jpg` 上。Yazi 触发预览任务：先查 LRU 缓存，未命中则交给 `ImageDecoder` 解码。解码是 CPU 任务，丢到线程池；解码完成后缩放到终端尺寸，按当前终端协议（如 kitty）编码发送。
3. 用户继续按 `j` 快速下移。前一个文件的预览任务如果还在队列里，调度器取消它；新文件的预览任务以高优先级插入。这避免了快速滚动时堆积无用 I/O。
4. 用户按 `Space` 选中当前文件，继续浏览选中另外两张。选中状态在 UI 层维护，不触发 I/O。
5. 用户按 `y` 把选中的文件标记为已 yank（复制），再切到目标目录。yank 状态保存在进程内，同样不触发 I/O。
6. 在目标目录按 `p` 发起粘贴。调度器把粘贴任务以"文件操作"优先级插入队列，三个文件的复制并发执行，进度在状态栏实时更新。
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
| `Tab` | 显示悬停文件的详细信息 |
| `w` | 打开任务管理器 |
| `q` / `Ctrl+c` | 退出 / 关闭当前标签页 |
| `~` 或 `F1` | 打开帮助 |

注意 `Ctrl+c` 在 Yazi 里是关闭当前标签页，不是中断、也不是复制——复制是 `y`。这和 shell 习惯冲突，初次使用容易误触，可以把关闭标签页的按键在 `keymap.toml` 里重映射。

### 高级用法

```bash
# 在当前目录启动，退出时切换到浏览的目录
yazi --cwd .

# 通过 shell 函数实现"退出后跟随目录"
function yy() {
    local tmp="$(mktemp -t "yazi-cwd.XXXXXX")" cwd
    yazi "$@" --cwd-file "$tmp"
    if cwd="$(command cat -- "$tmp")" && [ -n "$cwd" ] && [ "$cwd" != "$PWD" ]; then
        builtin cd -- "$cwd"
    fi
    rm -f -- "$tmp"
}

# 查看版本和构建信息
yazi --version
```

`--cwd-file` 是 Yazi 推荐的"退出后跟随目录"机制：把退出时的目录写入指定文件，shell 函数读取后 `cd` 过去。这是终端文件管理器的常见痛点——直接运行 `yazi` 退出后，shell 不会跟着切换目录。

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

- 官方插件仓库：yazi-rs/plugins（20 余个）
- 主题（flavor）仓库：yazi-rs/flavors
- 插件列表：https://yazi-rs.github.io/docs/plugins

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
| 图片不显示 | 确认终端在协议支持列表里；用 `YAZI_LOG=debug` 启动，查日志里的协议握手失败记录 |
| 预览加载慢 | 安装对应格式的外部工具（ffmpeg/poppler/7-Zip/ImageMagick 等），调大 `[preview]` 缓存 |
| 快捷键冲突 | 检查 `keymap.toml` 中的映射 |
| 插件报错 | 看 `~/.local/state/yazi/yazi.log` 中的插件错误输出 |

图片不显示是最常见的问题。排查顺序：先确认终端是否在支持列表里（见前面的协议表），再确认该格式是否需要外部工具（如 SVG 要 resvg），最后用 `YAZI_LOG=debug` 启动看协议握手失败日志。

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

A: 支持。Windows Terminal (≥v1.22.10352) 可使用 Sixel 协议图片预览。Warp 终端在 macOS/Linux 体验最佳。

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
| 文档 | https://yazi-rs.github.io/docs/ |
| 插件列表 | https://yazi-rs.github.io/plugins |
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
   Yazi 直接在 Rust 里解码 PNG/JPEG/GIF/WebP，再通过 kitty、Sixel、iTerm2 等终端协议把像素写回终端。
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
- 创建 `~/.config/yazi/plugins/` 目录
- 编写一个简单的 Lua 插件
- 在 `yazi.toml` 中加载插件

### 练习 3：研究异步 I/O 实现

阅读 Yazi 源代码中 `yazi-core/src/io.rs` 的部分，理解其异步 I/O 实现。尝试：
- 找到 `IoWorker` 结构体
- 理解 `tokio::fs` 的使用
- 解释为什么不使用 `std::fs`

---

## 进阶路径

1. **深入研究异步 I/O**：理解 Tokio 运行时、async/await 模式、线程池配置
2. **研究终端图片协议**：理解 kitty、Sixel、iTerm2 等协议的工作原理
3. **编写复杂 Lua 插件**：为 Yazi 添加自定义功能（如 Git 集成、Docker 集成）
4. **贡献 Yazi 核心**：提交 PR 修复 bug 或添加新功能
5. **研究 Rust TUI 开发**：理解 Ratatui 等 TUI 框架的设计

---

## 资料口径说明

1. **信息来源与时效性**：本文基于 sxyazi/yazi 仓库的 README、官方文档（配置、插件、CLI、DDS、安装）和 GitHub 仓库数据（采集时间 2026-09-02）。项目处于 Public Beta，具体细节可能已更新。
2. **技术细节验证**：异步 I/O 实现、图片预览机制等技术细节来自官方文档和源代码，但未在实际环境中完整验证。
3. **判断与建议的边界**：本文对 Yazi 适用场景与局限性的判断基于公开信息，实际体验可能因个人需求而异。
4. **未覆盖的内容**：本文未深入讨论 Yazi 的完整配置选项、性能基准测试、与其他文件管理器的详细对比等。
5. **术语使用说明**：本文保留 Yazi、Tokio、Lua、Rust 等专有名词，首次出现时附上中文释义。
6. **更新记录**：本文撰写于 2026-04-11，2026-09-02 依据官方文档修正了配置段名（`[mgr]`/`[preview]`）、插件命令（`ya pkg`）、调试方式（`YAZI_LOG`）、VFS scheme（`sftp://`）与回收站恢复方式等过时信息。

---

_本文基于 Yazi v26.9.1_
