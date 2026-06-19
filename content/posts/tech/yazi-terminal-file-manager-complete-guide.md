---
title: "Yazi：极快的终端文件管理器"
date: "2026-04-11T14:20:52+08:00"
slug: yazi-terminal-file-manager-complete-guide
description: "Yazi 把异步 I/O、内置图片预览和 Lua 插件三者结合，让终端文件管理器第一次做到不依赖外部工具就能预览图片。本文拆解它的架构取舍与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "终端", "文件管理", "TUI", "Go"]
---

# Yazi：异步 I/O、内置图片预览与 Lua 插件同处一个终端

终端文件管理器赛道并不缺选手，ranger、lf、nnn 各有拥趸。Yazi 用 Rust 重写一遍，如果只比启动速度和帧率，很难构成切换理由——lf 的 goroutine 模型已经够快，nnn 在低资源环境下更轻。

Yazi 值得拆开看的地方在于它把三件通常各走各路的工程目标压进了同一个二进制：全异步 I/O、内置图片预览、Lua 插件系统。这三件事在工程上本来互相争资源——异步 I/O 要的是线程不被挂起，图片预览要抢 CPU 和解码管线，插件系统则要求一个稳定的 API 边界和沙箱。ranger 想预览图片要靠 w3m、Überzug 这类外部进程，lf 也得借助 chafa 或 Überzug++；Yazi 直接在 Rust 里解码 PNG/JPEG/GIF/WebP，再通过 kitty、Sixel、iTerm2 等 10 余种终端协议把像素写回终端。终端支持就开箱预览，不必再装一堆辅助工具。

本文按四条主线展开：异步 I/O 为什么对文件管理器是硬需求、内置图片预览的工程难点在哪、插件系统为什么选 Lua 而不是 WASM 或 Python，最后用一个完整的浏览-预览-复制任务流把这几条主线串起来，并给出采用顺序。

## 项目位置

| 指标 | 数值 |
|------|------|
| Stars | 36.2k |
| Forks | 803 |
| 贡献者 | 167 |
| 语言 | Rust 94.2%, Lua 4.8% |
| 最新版本 | v26.1.22 (2026-01-22) |
| 许可证 | MIT |
| 仓库 | sxyazi/yazi |

Yazi 目前处于 Public Beta，可以作为日常主力工具使用。Rust 占 94.2%，Lua 占 4.8%——这个比例对应 Yazi 的设计选择：核心引擎用 Rust 写死，扩展面留给 Lua。下面先看为什么这个分工不是随手定的。

## 异步 I/O 为什么对文件管理器关键

文件管理器的工作负载有两个特征：I/O 密集（读目录、读文件、复制、移动），且 I/O 之间天然可并行（同时浏览两个目录、后台复制的同时继续浏览）。同步 I/O 在这里会直接变成 UI 卡顿——打开一个有几千个文件的目录，主线程要等 readdir 返回，期间按键无响应。

Yazi 基于 Tokio 运行时把所有 I/O 操作做成异步，CPU 任务分散到多个线程：

```rust
// yazi-core/src/io.rs (按源码结构整理，省略错误处理与字段细节)
pub struct IoWorker {
    pool: ThreadPool,
    rx: Receiver<IoRequest>,
}

impl IoWorker {
    pub async fn read_file(&self, path: PathBuf) -> Result<Vec<u8>> {
        // 走 tokio::fs 而非 std::fs，避免阻塞 Tokio 运行时
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
| yazi-fm | 文件管理器核心 |
| yazi-cli | 命令行接口 |
| yazi-config | 配置管理 |
| yazi-plugin | 插件系统 |
| yazi-scheduler | 任务调度器 |
| yazi-vfs | 虚拟文件系统 |
| yazi-proxy | 代理/Pub-Sub |
| yazi-shared | 共享类型和工具 |

`yazi-adapter` 单独拎出来值得注意——它把"终端图片协议适配"做成独立模块。这是 Yazi 能同时支持 10 余种协议又不让协议细节渗透进核心逻辑的关键。新增一个终端协议时，改动只落在 `yazi-adapter` 里，`yazi-core` 不用动。

### 任务调度

异步 I/O 只解决了"操作不阻塞运行时"这一层。文件管理器还要回答另一个问题：当多个 I/O 任务同时排队时，先做哪个。Yazi 的任务调度器维护一个优先级队列：

```rust
// yazi-scheduler/src/lib.rs (按源码结构整理，省略错误处理与字段细节)
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
| Windows Terminal (≥v1.22) | Sixel | 内置 |
| Warp | Inline images | 内置 |
| VSCode | Inline images | 内置 |
| X11/Wayland + 终端 | 需 Überzug++ | 需安装 |
| 不支持终端 | ASCII art (Chafa) | 需安装 |

适配只是第一步。图片在终端里显示还要解决解码和缩放——一张 4000×3000 的 JPEG 不能原样塞进 80×24 的终端窗口，得先解码、缩放到终端字符尺寸、再按协议编码发出去。Yazi 直接在 Rust 里做这件事：

```rust
// yazi-core/src/image.rs (按源码结构整理，省略错误处理与字段细节)
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

内置支持格式：PNG、JPEG、GIF、WebP、SVG、BMP、ICO 等。LRU 缓存的作用是——同一个文件来回滚动时不必重复解码，缓存命中直接取缩略图。缓存大小可在 `yazi.toml` 里调，图片密集目录下适当调大能减少重复解码，代价是内存占用上升；在内存受限的机器上反过来调小，让缓存更频繁地淘汰，换回更稳的内存峰值。

把图片预览做进核心，意味着 Yazi 必须自己维护一整套解码和协议适配代码，二进制体积和代码复杂度都比"调外部工具"高出一截。换回来的是用户侧的配置成本接近零——不必再为图片预览装一堆辅助工具。原本散落在用户侧的协议适配工作被收进了工具本身。这是 Yazi 和 ranger、lf 在工程取向上的一个明确分野：后两者把协议适配留给用户和外部工具，Yazi 把它收进 Rust 核心。

## 为什么插件系统选 Lua

Yazi 的插件用 Lua 5.5 编写。这个选择背后有几层考量。

WASM 听起来更现代，但 WASM 运行时嵌入 Rust 的成本不低，且 WASM 模块需要工具链编译，对插件作者门槛高——写一个插件要先装 Rust 工具链、配 wasm-pack、编译成 `.wasm` 文件再放进插件目录。Python 嵌入成本更高，还要带一个解释器运行时，且 Python 的 GIL 会和 Yazi 的异步模型冲突。Lua 的优势在于：解释器小（几百 KB）、嵌入 Rust 的绑定成熟（mlua）、插件作者不需要编译步骤，写完 `.lua` 文件直接生效。插件作者改一行配置就能看到效果，这种短反馈环对早期生态积累比运行时性能更重要——愿意写插件的人多了，生态才能起来。

插件目录结构如下：

```text
~/.config/yazi/plugins/
├── my-theme.yazi/          # 主题插件
│   ├── init.lua            # 插件入口
│   ├── theme.lua          # 主题定义
│   └── README.md
├── my-plugin.yazi/         # 功能插件
│   ├── init.lua
│   ├── actions.lua        # 自定义动作
│   └── README.md
└── my-previewer.yazi/     # 预览器插件
    ├── init.lua
    ├── previewer.lua      # 文件预览逻辑
    └── README.md
```

插件按用途分五类：

| 类型 | 说明 | 示例 |
|------|------|------|
| UI 插件 | 重写大部分 UI | 自定义布局、主题 |
| 功能插件 | 添加新功能 | 文件压缩、哈希计算 |
| 预览器 | 自定义文件预览 | Markdown 渲染、PDF 预览 |
| 预加载器 | 加速文件加载 | 图片预解码 |
| 获取器 | 获取远程文件 | 云存储集成 |

一个最小插件长这样：

```lua
-- my-plugin.yazi/init.lua
local M = {}

function M.name()
    return "我的插件"
end

function M.setup()
    -- 通过 Yazi 暴露的 API 注册快捷键
    ya.map("yy", "复制文件路径")
end

function M.copy_path()
    local cwd = ya.cwd()
    local selected = ya.selected()
    -- 把选中文件的绝对路径写入系统剪贴板
    ya.clipboard_set(cwd .. "/" .. selected)
end

return M
```

Lua 的代价是性能不如原生 Rust，且沙箱能力比 WASM 弱——插件能调用的 API 由 Yazi 显式暴露，但 Lua 本身能访问的内存和系统资源不像 WASM 那样有硬边界。Yazi 的取舍是：插件做轻量扩展（快捷键映射、预览逻辑、UI 定制），重活（图片解码、大文件复制）留在 Rust 核心。

## 虚拟文件系统与多实例协作

本地文件的并发问题靠异步 I/O 解决了，远程文件也要纳入同一个界面。虚拟文件系统（VFS）做的是这件事——把不同来源的文件统一成同一套目录操作接口：

```rust
// yazi-vfs/src/lib.rs (按源码结构整理，省略错误处理与字段细节)
pub trait FileSystem {
    fn read_dir(&self, path: &Path) -> Vec<DirEntry>;
    fn read_file(&self, path: &Path) -> Vec<u8>;
    fn write_file(&mut self, path: &Path, data: &[u8]) -> Result<()>;
}

// 内置实现
pub struct LocalFs;
pub struct SftpFs { /* SSH 连接 */ }
pub struct SearchFs { /* 搜索结果 */ }
pub struct ArchiveFs { /* 压缩包内容 */ }
```

内置 VFS 类型：

| FS 类型 | 用途 |
|---------|------|
| Local | 本地文件系统 |
| SFTP | 远程服务器 |
| Archive | ZIP/TAR/GZ 内容浏览 |
| Search | 搜索结果虚拟目录 |
| Trash | 回收站 |

Archive Fs 值得单独提一句——浏览一个 ZIP 包不必先解压，直接当目录打开。这在处理下载的源码包时省一步。

多实例协作走另一条路。Yazi 实例之间通过 Pub/Sub 通信，底层是 Unix Socket 或 TCP：

```text
┌─────────────────────────────────────┐
│           Yazi 实例 A                │
│  ┌─────────┐    ┌──────────────┐  │
│  │  Pub/   │◄──►│   Lua 脚本   │  │
│  │  Sub    │    └──────────────┘  │
│  └────┬────┘                      │
└───────┼─────────────────────────────┘
        │  Unix Socket / TCP
┌───────▼─────────────────────────────┐
│           Yazi 实例 B                │
│  ┌─────────┐    ┌──────────────┐  │
│  │  Pub/   │◄──►│   插件/UI    │  │
│  │  Sub    │    └──────────────┘  │
│  └─────────┘                      │
└─────────────────────────────────────┘
```

这套机制不需要额外进程，实例之间直接对话。典型用途是跨实例同步打开的文件，或者把一个实例的状态推给另一个实例。

## 一次完整的任务流：浏览 + 预览 + 复制

把前面几条主线串起来。假设场景：在一个有 5000 张图片的目录里，浏览、预览、把选中的几张复制到另一个目录。

1. 用户按下 `j` 移动到下一个文件。Yazi 把"光标下移"作为 UI 任务立即执行，状态栏同步更新。
2. 光标停在 `photo_1234.jpg` 上。Yazi 触发预览任务：先查 LRU 缓存，未命中则交给 `ImageDecoder` 解码。解码是 CPU 任务，丢到线程池；解码完成后缩放到终端尺寸，按当前终端协议（如 kitty）编码发送。
3. 用户继续按 `j` 快速下移。前一个文件的预览任务如果还在队列里，调度器取消它；新文件的预览任务以高优先级插入。这避免了快速滚动时堆积无用 I/O。
4. 用户按 `Space` 选中当前文件，继续浏览选中另外两张。选中状态在 UI 层维护，不触发 I/O。
5. 用户按 `Ctrl+c`（Yazi 的复制快捷键，不是中断）把选中文件加入复制队列，目标目录是当前另一个标签页的路径。
6. 调度器把复制任务以"文件操作"优先级插入队列。三个文件的复制并发执行，进度在状态栏实时更新。
7. 复制期间用户继续浏览，UI 不卡顿——复制走异步 I/O，UI 走主线程，互不阻塞。
8. 复制完成，状态栏提示。

这八步里，异步 I/O 保证 UI 不被挂起，任务调度决定哪个 I/O 先跑、哪个被取消，图片预览负责解码和协议适配，Pub/Sub 把跨标签页的状态同步起来。任何一条退回同步模型，体验都会塌——UI 卡、预览慢、或者复制阻塞浏览，至少踩中一条。

## 与 ranger/lf 的工程取舍

把 Yazi 放回赛道看会更清楚。

| 维度 | ranger | lf | Yazi |
|------|--------|-----|------|
| 语言 | Python | Go | Rust |
| I/O 模型 | 同步 | 并发（goroutine） | 异步（Tokio） |
| 图片预览 | 外部工具（w3m、Überzug） | 外部工具（chafa、Überzug++） | 内置 |
| 插件语言 | Python | Shell | Lua |
| 插件生态 | 成熟，Python 生态可用 | 较少 | 60+ 官方插件，仍在早期 |
| 配置 | Python 脚本 | Shell 风格 | TOML + Lua |

ranger 的优势是 Python 生态——任何能写 Python 的人都能扩展它，且十年积累的插件数量多。劣势是同步 I/O 和 GIL，大目录和图片预览体验差。

lf 用 Go，并发能力强，二进制单文件部署方便。但图片预览仍然依赖外部工具，且 Shell 风格的配置对复杂逻辑表达力有限。

Yazi 的取舍可以拆成三句：Rust 换的是性能和内存安全，内置图片预览换的是用户侧零配置，Lua 换的是插件门槛和扩展能力之间的平衡。代价同样具体——Rust 学习曲线陡，插件生态比 ranger 小，Lua 沙箱不如 WASM 严格。

ranger、lf、Yazi 三者并非互相替代。已经在 ranger 上有一套 Python 插件工作流、且不依赖图片预览的人，没有强理由切换。日常需要预览图片、在大目录里频繁切换、且终端支持 kitty 或 Sixel 的用户，Yazi 的体验差异是可感知的。

## 安装与基础配置

```bash
# macOS
brew install yazi

# Linux (二进制)
curl -fsSL https://github.com/sxyazi/yazi/releases/latest/download/yazi-x86_64-linux-musl.tar.gz
tar -xzf yazi-x86_64-linux-musl.tar.gz
sudo mv yazi /usr/local/bin/

# Rust 源码编译
cargo install yazi-bundle
ya --install
```

基础配置走 TOML，不是 Lua——Lua 只用于插件。主配置文件是 `~/.config/yazi/yazi.toml`：

```toml
[manager]
show_hidden = true
sort_by = "mtime"          # 按修改时间排序
sort_dir_first = true        # 目录优先
case_sensitive = false

[previewer]
image_protocol = "kitty"
cache_dir = "~/.cache/yazi/previewer"

[plugin]
install_dir = "~/.config/yazi/plugins"

[theme]
active = "catppuccin-mocha"

[input]
escape_timeout = 200
```

配置目录结构：

```text
~/.config/yazi/
├── init.lua              # 初始化配置
├── init.yml             # YAML 配置（可选）
├── theme/                # 主题目录
│   └── my-theme.lua
├── plugins/              # 插件目录
│   ├── readme.yazi
│   └── image-preview.yazi
└── yazi.toml           # 全局设置
```

### 快捷键速查

Yazi 默认 Vim 风格：

| 快捷键 | 功能 |
|--------|------|
| `h/j/k/l` | 上下左右导航 |
| `H/L` | 上/下跳转到父目录 |
| `gg` | 跳转到顶部 |
| `G` | 跳转到底部 |
| `Space` | 选中文件 |
| `Ctrl+c` | 复制文件 |
| `dd` | 剪切文件 |
| `p` | 粘贴文件 |
| `d` | 删除文件 |
| `r` | 重命名 |
| `yy` | 复制路径 |
| `Enter` | 进入目录/打开文件 |
| `Tab` | 多选模式 |
| `Ctrl+f` | 搜索文件 |
| `/` | 全局搜索 |

注意 `Ctrl+c` 在 Yazi 里是复制，不是中断——这和 shell 习惯冲突，初次使用容易误触。如果想改回中断语义，可以在 `keymap.toml` 里重映射。

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

Yazi 自带包管理器 `ya`，用于安装插件和主题：

```bash
# 安装插件（ya package install）
ya package install yazi-rs/plugins:readme

# 安装主题
ya package install yazi-rs/themes:gruvbox

# 更新所有已安装的包
ya package upgrade

# 列出已安装的包
ya package list
```

社区资源：

- 官方插件仓库：yazi-rs/plugins（60+ 插件）
- 主题仓库：yazi-rs/themes（20+ 主题）
- 插件列表：https://yazi-rs.github.io/docs/plugins

## 性能调优与排查

### 性能优化

Yazi 的性能调优主要通过 `yazi.toml` 配置和外部工具配合：

```toml
# yazi.toml 性能相关配置
[manager]
# 使用 fd 替代默认的 readdir，大目录下速度更快
# 需要先安装 fd: brew install fd / apt install fd-find
# Yazi 会自动检测 fd 是否在 PATH 中

[previewer]
# 启用预览缓存，重复浏览同一目录时跳过解码
cache_enabled = true
```

预览缓存对图片密集目录效果明显——重复浏览同一目录时，缩略图直接从缓存取，跳过解码。`fd` 比 `std::fs::read_dir` 快的原因是 `fd` 用了并行 readdir，在大目录里差距拉得开。

### 调试

```bash
# 启用调试日志
RUST_LOG=yazi=debug yazi

# 检查配置加载情况
yazi --debug

# 查看日志（日志路径可能因平台而异）
tail -f ~/.local/state/yazi/yazi.log
```

### 常见问题排查

| 问题 | 解决方案 |
|------|----------|
| 图片不显示 | 确认终端支持图片协议，尝试 `image_protocol = "sixel"` |
| 预览加载慢 | 安装 `fd`、`bat`、`glow` 等外部工具 |
| 快捷键冲突 | 检查 `keymap.toml` 中的映射 |
| 插件报错 | 查看 `yazi --debug` 输出 |

图片不显示是最常见的问题。排查顺序：先确认终端是否在支持列表里（见前面的协议表），再确认 `image_protocol` 配置和终端匹配，最后看 `yazi --debug` 是否有协议握手失败日志。

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

1. 先在支持的终端里跑起来，确认图片预览开箱可用。这一步验证的是你的终端是否在协议支持列表里，以及 `image_protocol` 配置是否匹配。如果图片不显示，回到前面的协议表排查，不要急着往下走。
2. 把常用快捷键映射到自己的习惯（`keymap.toml`）。Yazi 默认 Vim 风格，但从 ranger 或 lf 迁移过来的用户可能需要调整 `Ctrl+c` 复制、`dd` 剪切等和 shell 习惯冲突的键位。
3. 从官方插件仓库装 1-2 个高频插件（如 `readme.yazi` 预览）。这一步验证的是插件系统是否正常工作，以及 `ya package install` 命令能否拉取远程插件。
4. 只在前三步都顺畅后，再考虑写自定义插件。写插件前先读官方插件的 `init.lua`，了解 Yazi 暴露的 API 边界——Lua 插件能做的是快捷键映射、预览逻辑、UI 定制，重活（图片解码、大文件复制）由 Rust 核心处理。

## 常见问题

**Q: Yazi 和 ranger/lf 有什么区别？**

A: Yazi 用 Rust 编写，原生支持异步 I/O，内置图片预览（无需配置），插件系统基于 Lua（比 VimScript 更易学）。ranger 和 lf 用 Python/C/Go 编写，更轻量但图片预览依赖外部工具。

**Q: 支持 Windows 吗？**

A: 支持。Windows Terminal (≥v1.22) 可使用 Sixel 协议图片预览。Warp 终端在 macOS/Linux 体验最佳。

**Q: 如何自定义快捷键？**

A: 在 `keymap.toml` 中重映射，或在插件里通过 `ya.map()` 注册：

```lua
-- my-plugin.yazi/init.lua
local M = {}

function M.setup()
    -- 将 "yy" 映射为复制路径
    ya.map("yy", function()
        local path = ya.selected()
        ya.clipboard_set(path)
    end)
end

return M
```

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
| 主题列表 | https://yazi-rs.github.io/themes |
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

_本文基于 Yazi v26.1.22_
