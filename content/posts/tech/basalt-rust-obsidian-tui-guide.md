---
title: "Basalt：用Rust在终端里管理Obsidian笔记，1.2k星的ratatui实战"
date: "2026-05-11T22:50:00+08:00"
slug: "basalt-rust-obsidian-tui-notes"
description: "深度解析erikjuhani/basalt：用Rust和ratatui构建的Obsidian笔记TUI工具，三窗格布局（Explorer+Editor+Outline），WYSIWYG Markdown渲染，支持Vim模式和TOML配置。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "TUI", "Obsidian", "ratatui", "Markdown", "终端", "笔记工具"]
hiddenFromHomePage: true
---

> "Basalt 不是 Obsidian 的替代品，它提供极简主义终端界面和 WYSIWYG Markdown 体验。"——README 开篇声明

---

一句话定位

[Basalt](https://github.com/erikjuhani/basalt) 是一个用 **Rust** 构建的 **Obsidian 笔记终端管理器**。它不是一个全功能的笔记软件，而是专注做好一件事：在终端里以三窗格布局（Explorer + Note Editor + Outline）浏览和管理 Obsidian 保险库。

当前 GitHub ⭐ **1.2k**，Rust 实现，MIT 许可证。

---

核心架构：ratatui 驱动的三窗格 TUI

技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| TUI 框架 | [ratatui](https://github.com/ratatui-org/ratatui) | Rust 最流行的 TUI 库，继承自 tui-rs |
| Markdown 解析 | [pulldown-cmark](https://github.com/pulldown-cmark/pulldown-cmark) | CommonMark + GFM 兼容解析器 |
| 跨平台 | 原生实现 | Windows / macOS / Linux |
| 包管理 | Cargo | `cargo install basalt-tui` |
| 包管理器（可选） | aqua | 日本开发者常用的 CLI 工具管理器 |

三窗格布局

```
┌─────────────────────────────────────────────────────────┐
│  ┌──────────┐  ┌─────────────────────┐  ┌───────────┐  │
│  │ Explorer │  │   Note Editor        │  │  Outline  │  │
│  │          │  │                      │  │           │  │
│  │ 📁 notes │  │ # Heading 1          │  │ ▼ H1      │  │
│  │  📄 a.md │  │ ## Heading 2         │  │   H2      │  │
│  │  📄 b.md │  │ Body text...         │  │   H3      │  │
│  │ 📁 daily │  │ ```rust              │  │ ▼ H2      │  │
│  │          │  │ fn main() {}         │  │   H3      │  │
│  │          │  │ ```                  │  │           │  │
│  └──────────┘  └─────────────────────┘  └───────────┘  │
│  [EXPLORER]  字数: 1,234  字符: 7,890                  │
└─────────────────────────────────────────────────────────┘
```

- **Explorer（左侧）**：浏览保险库的文件和文件夹
- **Note Editor（中央）**：以 WYSIWYG 风格渲染 Markdown 内容
- **Outline（右侧）**：当前笔记的标题大纲，支持跳转

窗格之间用 `Tab` / `Shift+Tab` 切换焦点，底部状态栏显示当前焦点窗格和字数统计。

---

Markdown 渲染：pulldown-cmark 的支持边界

已支持

| 元素 | 渲染方式 |
|------|----------|
| 标题 H1-H6 | 隐藏 `#` 符号，显示彩色指示条 |
| 段落/列表/引用 | 标准渲染，引用用垂直条代替 `>` |
| 代码块 | 带背景样式（**尚无语法高亮**） |
| 任务列表 `[ ]` / `[x]` | 视觉化复选框 |
| Callouts | Obsidian 风格的 `>[!NOTE]` 等语法 |
| Wiki-links | `[[Note]]` / `[[Note#Heading]]` 解析 |

尚未支持

| 元素 | 状态 |
|------|------|
| 图片 | ❌ 不渲染 |
| 表格 | ❌ 不渲染 |
| 分割线 `---` | ❌ 不渲染 |
| 语法高亮 | ❌ 代码块统一样式 |
| 粗体/斜体/删除线 | 解析但不视觉化 |
| 数学公式 `$...$` / `$$...$$` | ❌ 不支持 |
| 脚注 | ❌ 不支持 |
| HTML 内容 | ❌ 不支持 |
| 外链点击 | ❌ 不可点击 |

README 明确标注了这些限制，对于追求完整 Obsidian 体验的用户，这是重要的预期管理。

---

核心功能

. 保险库自动发现

Basalt 启动时会在启动屏（Splash Screen）显示所有自动发现的 Obsidian 保险库。保险库发现机制读取 Obsidian 的配置文件 `obsidian.json`，列出本地所有保险库路径。

```
basalt
→ 启动屏显示保险库列表
→ 用 j/k 或方向键导航
→ Enter 打开保险库
```

`Ctrl+G` 随时呼出保险库选择器切换保险库。

. WYSIWYG Markdown 渲染

Basalt 的渲染策略是**替换语法字符为视觉样式**，而非简单地将纯文本显示出来：

- 标题 `#` 符号被彩色指示条替代
- 引用块 `>` 被左侧垂直条替代
- 代码块用背景色区分

这种渲染方式在终端的约束下最大化了可读性。

. 重命名自动更新 Wiki-links

在 Explorer 中按 `r` 重命名笔记或文件夹时，Basalt 会自动扫描并更新保险库中所有引用该笔记的 Wiki-links。

```
假设有笔记 A.md 内容为：参见 [[B]] 和 [[C]]
将 B.md 重命名为 D.md 后
A.md 自动更新为：参见 [[D]] 和 [[C]]
```

这是 Obsidian 用户最常用的功能之一，Basalt 正确实现了它。

. Vim 模式

配置 `vim_mode = true` 启用一套模拟 Vim 的按键预设：

| 窗格 | 按键 | 命令 |
|------|------|------|
| Note Editor | `gg` | 跳转到笔记顶部 |
| Note Editor | `G` | 跳转到笔记底部 |
| Note Editor | `w` / `b` | 按词移动光标 |
| Explorer | `gg` / `G` | 跳转到首项/末项 |
| Input Modal | `w` / `b` | 按词移动光标 |

Vim 模式下，Note Editor 引入 Normal/Insert 子模式：`i` 进入 Insert 模式编辑，`Esc` 返回 Normal 模式导航，再按一次 Esc 退出到 READ 模式。

. 实验性内置编辑器

Basalt 内置了一个**实验性编辑器**，默认关闭，需在配置中启用：

```toml
experimental_editor = true
```

启用后按 `i` 进入编辑模式。但当前能力非常有限：

**支持的编辑操作：**
- 光标左右移动（`h`/`l` 或方向键）
- 按词移动（`Alt+f` / `Alt+b`）
- Backspace 删除
- `Ctrl+x` 保存，`Esc` 退出

**尚不支持的编辑操作：**
- ❌ 撤销/重做
- ❌ 复制/剪切/粘贴
- ❌ 文本选择
- ❌ 多行删除
- ❌ 跳转到行首/行尾
- ❌ 整行删除

官方推荐：**使用外部编辑器**（如 Vim、VS Code）进行实际编辑，Basalt 的实验性编辑器仅作为轻量补充。

. 自定义命令

支持配置外部命令调用，通过 `%note_path`、`%vault` 等占位符注入上下文：

```toml
[global]
key_bindings = [
  # 用 Vim 打开当前笔记
  { key = "ctrl+alt+e", command = "exec:vi %note_path" },
  # 用 Obsidian 打开当前笔记（deep link 协议）
  { key = "ctrl+alt+o", command = "spawn:open obsidian://open?vault=%vault&file=%note" },
]
```

---

安装与配置

安装方式

```bash
方式：Cargo（推荐）
cargo install basalt-tui

方式：aqua
aqua g -i erikjuhani/basalt

方式：下载预编译二进制
从 GitHub Releases 下载，解压后移到 PATH
```

配置文件位置

```toml
macOS / Linux
$HOME/.basalt.toml
$XDG_CONFIG_HOME/basalt/config.toml

Windows
%USERPROFILE%\.basalt.toml
%APPDATA%\basalt\config.toml
```

配置文件采用 **merge 策略**：只需定义要覆盖的按键，所有其他默认值保持有效。

符号预设

内置三套符号预设：

| 预设 | 特点 |
|------|------|
| `unicode`（默认） | Unicode 字符渲染 |
| `ascii` | 纯 ASCII 字符 |
| `nerd-font` | Nerd Font 图标 |

可单独覆盖任意符号：

```toml
[symbols]
preset = "unicode"
[symbols.override]
folder = "📂"
file = "📄"
```

---

与 Obsidian 的边界

README 明确说：**Basalt 不是 Obsidian 的替代品**。

这一定位很重要，因为 Basalt 不支持的功能很多：

| Obsidian 功能 | Basalt 支持 |
|---------------|-------------|
| Graph View | ❌ |
| Backlinks Panel | ❌ |
| Obsidian 插件 | ❌ |
| 创建保险库 | ❌ |
| 创建/删除/移动笔记 | ❌ |
| 搜索笔记 | ❌ |
| 完整 Markdown 渲染 | 部分 |

Basalt 的定位是：**用终端方式快速浏览和导航 Obsidian 保险库**，而非完整的笔记管理。

---

适用场景

**✅ 强项场景：**
- **终端重度用户**：日常在终端工作，不需要切换到 GUI
- **快速笔记浏览**：快速定位和浏览笔记，不做编辑
- **键盘导航爱好者**：Vim 模式 + 快捷键，0 鼠标操作
- **多保险库管理**：同时管理多个 Obsidian 保险库
- **开发者文档站**：用 Obsidian 管理开发文档，用 Basalt 快速查阅

**❌ 局限：**
- 编辑功能非常基础（实验性），重度编辑建议用外部编辑器
- 不支持图片、表格等非纯文本内容渲染
- 不支持搜索（这是 Obsidian 的核心功能之一）

---

技术实现亮点

ratatui 的实战应用

Basalt 是学习 ratatui 的优秀参考项目。它的实现展示了：

1. **Block + Flex 布局**：三窗格通过 `Layout` 和 `Flex` 实现灵活的窗格分割
2. **Style 组合**：`Style::from()` 链式调用实现复杂的文本样式
3. **StatefulWidget**：Explorer 和 Outline 需要维护选中/滚动状态，通过 `StatefulWidget` 实现
4. **事件处理**：`EventListener` 模式处理键盘事件

pulldown-cmark 的扩展解析

Basalt 在 pulldown-cmark 的基础上扩展了 Obsidian 特有的语法：

- Wiki-links `[[Note]]` 的自定义解析
- Callout blocks `>[!NOTE]` 的正则识别和渲染

这种在通用解析器上叠加自定义语法的模式，是处理 Markdown 方言的标准做法。

跨平台文件发现

保险库自动发现需要读取 Obsidian 的配置文件（跨平台路径处理）：

```rust
// macOS: ~/Library/Application Support/obsidian/obsidian.json
// Linux: ~/.config/obsidian/obsidian.json
// Windows: %APPDATA%\obsidian\obsidian.json
```

Basalt 对这三个路径分别处理，解析 JSON 获取 vault 列表。

---

总结

Basalt 是一个定位清晰的 Rust TUI 项目。它给终端用户提供了一个极简的 Obsidian 保险库浏览器，不试图替代 Obsidian。

对于已经重度使用 Obsidian、又希望减少 GUI 切换的开发者来说，Basalt 是一个自然的效率工具。它的 ratatui 实现也适合作为 Rust TUI 开发的参考。

但它的局限性也很明确：编辑功能实验性、缺少搜索、不支持富媒体。如果你需要的是完整的笔记管理，Obsidian GUI 仍是必备；Basalt 是终端里的一个快速查阅层。

---

**项目信息**

- GitHub：[erikjuhani/basalt](https://github.com/erikjuhani/basalt) ⭐ 1.2k
- 语言：Rust
- 框架：ratatui + pulldown-cmark
- 许可证：MIT
- 安装：`cargo install basalt-tui`
