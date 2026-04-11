+++
date = '2026-04-11T14:20:52+08:00'
draft = false
title = 'Yazi：⚡ 级快的终端文件管理器'
+++

# Yazi：⚡ 级快的终端文件管理器

## 📖 一、项目概述

### 1.1 Yazi 是什么

**Yazi**（谐音"鸭子"）是一款用 Rust 编写的极速终端文件管理器，基于**非阻塞异步 I/O**构建，它的目标是为用户提供一个高效、用户友好，可高度定制的文件管理体验。

作为一款 Public Beta 产品，Yazi 已经可以作为日常主力工具使用。其核心设计理念是**"快如闪电，稳如磐石"**——所有 I/O 操作均为异步执行，CPU 任务分散到多个线程，最大限度利用系统资源。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | 36.2k ⭐ |
| Forks | 803 |
| 贡献者 | 167 |
| 语言 | Rust 94.2%, Lua 4.8% |
| 最新版本 | v26.1.22 (2026-01-22) |
| 许可证 | MIT |
| 仓库 | sxyazi/yazi |

### 1.3 为什么选择 Yazi

传统的终端文件管理器（如 ranger、lf）要么基于同步 I/O，要么依赖外部工具处理图片预览。Yazi 通过以下特性实现了差异化：

- **原生异步架构**：所有文件操作不阻塞主线程
- **内置图片预览**：支持 10+ 种终端图片协议，无需额外配置
- **并发插件系统**：用 Lua 编写插件，门槛低且功能强大
- **虚拟文件系统**：支持远程文件管理，自定义搜索引擎
- **现代化用户界面**：Vim 风格快捷键、多标签页、鼠标支持

---

## 🏗️ 二、技术架构深度解析

### 2.1 异步架构设计

Yazi 的核心是基于 **Tokio** 运行时构建的全异步架构：

```rust
// yazi-core/src/io.rs (概念代码)
pub struct IoWorker {
    pool: ThreadPool,
    rx: Receiver<IoRequest>,
}

impl IoWorker {
    pub async fn read_file(&self, path: PathBuf) -> Result<Vec<u8>> {
        // 异步文件读取，不阻塞其他操作
        tokio::fs::read(&path).await
    }
    
    pub async fn list_dir(&self, path: PathBuf) -> Result<Vec<DirEntry>> {
        // 异步目录列表
        tokio::fs::read_dir(&path)
            .await?
            .entries()
            .collect()
            .await
    }
}
```

**异步设计优势**：
- UI 永远流畅，即使处理大量文件
- 后台任务（如大文件复制）不阻塞前台操作
- 天然支持并发文件操作

### 2.2 模块化架构

Yazi 采用 **monorepo** 结构，核心模块包括：

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

### 2.3 任务调度系统

Yazi 的任务调度是其高性能的关键：

```rust
// yazi-scheduler/src/lib.rs (概念代码)
pub struct Scheduler {
    tasks: PriorityQueue<Task>,
    worker_pool: Vec<Worker>,
}

impl Scheduler {
    // 优先级调度：高优先级任务（如 UI 更新）优先处理
    pub fn schedule(&mut self, task: Task) {
        self.tasks.push(task.priority, task);
    }
    
    // 任务取消支持
    pub fn cancel(&mut self, task_id: u64) {
        self.tasks.remove_if(|t| t.id == task_id);
    }
}
```

**调度特性**：
- 优先级队列：UI 任务 > 文件操作 > 后台任务
- 实时进度更新
- 任务取消支持
- 内部任务优先级分配

---

## 🖼️ 三、图片预览系统

### 3.1 多协议支持

Yazi 内置支持 10+ 种终端图片协议：

| 终端 | 协议 | 支持状态 |
|------|------|----------|
| kitty (≥0.28.0) | Kitty unicode placeholders | ✅ 内置 |
| iTerm2 | Inline images | ✅ 内置 |
| WezTerm | Inline images | ✅ 内置 |
| Konsole | Kitty old protocol | ✅ 内置 |
| foot | Sixel | ✅ 内置 |
| Ghostty | Kitty unicode placeholders | ✅ 内置 |
| Windows Terminal (≥v1.22) | Sixel | ✅ 内置 |
| Warp | Inline images | ✅ 内置 |
| VSCode | Inline images | ✅ 内置 |
| X11/Wayland + 终端 | 需 Überzug++ | ☑️ 需安装 |
| 不支持终端 | ASCII art (Chafa) | ☑️ 需安装 |

### 3.2 内置图片解码

Yazi 直接在 Rust 中处理图片，无需依赖外部工具：

```rust
// yazi-core/src/image.rs (概念代码)
pub struct ImageDecoder {
    cache: LruCache<PathBuf, CachedImage>,
}

impl ImageDecoder {
    // 预处理图片，加速加载
    pub fn decode(&mut self, path: &Path) -> Result<CachedImage> {
        let data = self.read_file(path)?;
        let format = self.detect_format(&data)?;
        
        match format {
            Format::Png => self.decode_png(&data),
            Format::Jpeg => self.decode_jpeg(&data),
            Format::Gif => self.decode_gif(&data)?,
            // ... 更多格式
        }
    }
}
```

**内置支持格式**：PNG、JPEG、GIF、WebP、SVG，BMP、ICO 等

---

## 🔌 四、插件系统

### 4.1 Lua 插件架构

Yazi 使用 **Lua 5.5** 作为插件语言：

```
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

### 4.2 插件类型

| 类型 | 说明 | 示例 |
|------|------|------|
| UI 插件 | 重写大部分 UI | 自定义布局、主题 |
| 功能插件 | 添加新功能 | 文件压缩、哈希计算 |
| 预览器 | 自定义文件预览 | Markdown 渲染、PDF 预览 |
| 预加载器 | 加速文件加载 | 图片预解码 |
| 获取器 | 获取远程文件 | 云存储集成 |

### 4.3 插件示例

```lua
-- my-plugin/init.lua
local M = {}

function M.name()
    return "我的插件"
end

function M.setup()
    -- 注册快捷键
    require("yazi").map("yy", "复制文件路径")
end

function M.copy_path()
    local cwd = require("yazi").cwd()
    local selected = require("yazi").selected()
    -- 复制选中文件的绝对路径
    vim.fn.setreg("+", cwd .. "/" .. selected)
end

return M
```

---

## ☁️ 五、虚拟文件系统

### 5.1 VFS 架构

Yazi 的虚拟文件系统（VFS）允许挂载远程资源和自定义来源：

```rust
// yazi-vfs/src/lib.rs (概念代码)
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

### 5.2 内置虚拟文件系统

| FS 类型 | 用途 |
|---------|------|
| Local | 本地文件系统 |
| SFTP | 远程服务器 |
| Archive | ZIP/TAR/GZ 内容浏览 |
| Search | 搜索结果虚拟目录 |
| Trash | 回收站 |

---

## 📡 六、数据分发服务

### 6.1 Pub/Sub 架构

Yazi 采用客户端-服务端架构，无需额外进程：

```
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

**用途**：
- 跨实例通信（打开文件同步）
- 状态持久化
- 多 Yazi 实例协作

---

## 📦 七、包管理器

### 7.1 一键安装插件/主题

```bash
# 安装插件
yazi --install https://github.com/yazi-rs/plugins/blob/main/readme.yazi

# 安装主题
yazi --install https://github.com/yazi-rs/themes/blob/main/gruvbox.yazi

# 更新所有
yazi --update

# 锁定版本
yazi --pin <plugin-name>=<version>
```

### 7.2 社区资源

- **官方插件仓库**：yazi-rs/plugins（60+ 插件）
- **主题仓库**：yazi-rs/themes（20+ 主题）
- **插件列表**：https://yazi-rs.github.io/docs/plugins

---

## 🚀 八、快速上手

### 8.1 安装

```bash
# macOS
brew install yazi

# Linux (二进制)
curl -fsSL https://github.com/sxyazi/yazi/releases/latest/download/yazi-x86_64-linux-musl.tar.gz
tar -xzf yazi-x86_64-linux-musl.tar.gz
sudo mv yazi /usr/local/bin/

# Rust 源码编译
cargo install yazi-bundle
ya --install yazi
```

### 8.2 基础配置

```lua
-- ~/.config/yazi/init.lua (Yazi initial.lua)
local yazi = require("yazi")

yazi.setup({
    -- 文件管理器配置
    manager = {
        show_hidden = true,           -- 显示隐藏文件
        sort_by = "name",          -- 按名称排序
        case_sensitive = false,       -- 大小写不敏感
    },
    
    -- 预览器配置
    previewer = {
        image_protocol = "kitty",   -- 使用 kitty 协议
        cache_dir = "~/.cache/yazi",
    },
    
    -- 主题
    theme = "gruvbox",
})
```

### 8.3 快捷键速查

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

### 8.4 高级用法

```bash
# 打开文件时自动预览
yazi --preview

# 使用内置 git 集成
yazi --cwd .

# 远程文件管理
yazi sftp://user@host:/path/to/dir

# 查看文件校验和
yazi --checksum
```

---

## 🔧 九、配置与定制

### 9.1 目录结构

```
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

### 9.2 完整配置示例

```toml
[manager]
show_hidden = true
sort_by = "mtime"          # 按修改时间排序
sort_dir_first = true        # 目录优先
case_sensitive = false

[previewer]
image_protocol = "kitty"
cache_dir = "~/.cache/yazi/previewer"
 hep = true

[plugin]
install_dir = "~/.config/yazi/plugins"

[theme]
active = "catppuccin-mocha"

[input]
escape_timeout = 200
```

---

## 💡 十，最佳实践

### 10.1 性能优化

1. **使用 faster 文件系统**
   ```lua
   -- 使用 fd 加速目录列表
   yazi config set manager.preloaders[1] = "fd"
   ```

2. **图片预览缓存**
   ```lua
   -- 启用预览缓存
   yazi config set previewer.cache_enabled = true
   ```

3. **按需加载插件**
   ```lua
   -- 只在需要时加载插件
   require("heavy-plugin"):load_on_demand()
   ```

### 10.2 开发调试

```bash
# 启用调试模式
RUST_LOG=yazi_debug yazi

# 检查配置
yazi --debug-config

# 查看日志
tail -f ~/.local/state/yazi/yazi.log
```

### 10.3 常见问题解决

| 问题 | 解决方案 |
|------|----------|
| 图片不显示 | 确认终端支持图片协议，尝试 `image_protocol = "sixel"` |
| 预览加载慢 | 安装 `fd`、`bat`、`glow` 等外部工具 |
| 快捷键冲突 | 检查 `init.lua` 中的映射 |
| 插件报错 | 查看 `yazi --debug` 输出 |

---

## 📚 十一、相关资源

### 11.1 官方资源

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/sxyazi/yazi |
| 文档 | https://yazi-rs.github.io/docs/ |
| 插件列表 | https://yazi-rs.github.io/plugins |
| 主题列表 | https://yazi-rs.github.io/themes |
| Discord (英文) | https://discord.gg/qfADduSdJu |
| Telegram (中文) | https://t.me/yazi_rs |

### 11.2 性能分析文章

> **为什么 Yazi 这么快？**
> https://yazi-rs.github.io/blog/why-is-yazi-fast
> 
> 深入解析 Yazi 的异步架构、任务调度和预加载机制。

### 11.3 贡献指南

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

## ❓ 十二、常见问题

**Q: Yazi 和 ranger/lf 有什么区别？**

A: Yazi 用 Rust 编写，原生支持异步 I/O，内置图片预览（无需配置），插件系统基于 Lua（比 VimScript 更易学）。ranger 和 lf 用 Python/C/Go 编写，更轻量但图片预览依赖外部工具。

**Q: 支持 Windows 吗？**

A: 支持！Windows Terminal (≥v1.22) 可使用 Sixel 协议图片预览。Warp 终端在 macOS/Linux 体验最佳。

**Q: 如何自定义快捷键？**

A: 在 `init.lua` 中使用 `require("yazi").map()`：

```lua
local yazi = require("yazi")

-- 将 "yy" 映射为复制路径
yazi.map("yy", function()
    local path = yazi.selected()
    yazi.execute("cp", {"-r", path, "."})
end)
```

**Q: 插件开发需要学 Rust 吗？**

A: 不需要！Yazi 插件用 **Lua** 编写。只要会写脚本就能开发插件。

**Q: 如何报告 Bug？**

A: https://github.com/sxyazi/yazi/issues

---

## 🎯 总结

Yazi 是一款**现代化、高性能、可扩展**的终端文件管理器，它的核势：

| 优势 | 说明 |
|------|------|
| ⚡ 极速响应 | 全异步架构 + Rust 性能 |
| 🖼️ 开箱即用 | 内置图片预览，无需配置 |
| 🔌 插件丰富 | 60+ 官方插件，Lua 开发简单 |
| 💻 跨平台 | macOS/Linux/Windows 全支持 |
| ⌨️ Vim 风格 | 高效键盘操作 |

无论你是日常用户还是开发者，Yazi 都能显著提升终端文件管理效率。立即尝试，你会发现：一旦使用 Yazi，就再也回不去了！

---

**🚀 立即体验：**

```bash
# 一行命令安装（macOS）
brew install yazi

# 或下载二进制
curl -fsSL https://github.com/sxyazi/yazi/releases/latest/download/yazi-x86_64-apple-darwin.tar.gz
tar -xzf yazi-x86_64-apple-darwin.tar.gz
./yazi
```

---

_🦞 本文由钳岳星君撰写，基于 Yazi v26.1.22_
