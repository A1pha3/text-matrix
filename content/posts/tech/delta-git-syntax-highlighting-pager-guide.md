---
title: "Delta：让 git diff 在终端里也好看"
date: "2026-04-12T02:31:39+08:00"
slug: delta-git-syntax-highlighting-pager-guide
github_repo: "dandavison/delta"
description: "Delta 是一个用 Rust 编写的 Git 语法高亮分页器。本文从安装配置讲起，覆盖主题、行号、Side-by-side 对比、合并冲突与 grep、blame 集成，把 git、diff、grep 的输出统一成清晰可读的样式。"
draft: false
categories: ["技术笔记"]
tags: ["Git", "Rust", "终端"]
---

## 学习目标

完成本文阅读后，你将能够：

1. **理解 Delta 的核心价值**：明白为什么需要 Git 语法高亮分页器，以及 Delta 在 Git 工作流中的定位
2. **掌握安装与配置**：在 macOS、Linux、Windows 等平台完成安装，并正确配置 `~/.gitconfig`
3. **运用核心功能**：使用语法高亮、Side-by-side 对比、行号导航、合并冲突显示等功能
4. **定制个性化主题**：选择并配置适合的语法高亮主题，理解主题配置的工作原理
5. **集成到工作流**：将 Delta 与 ripgrep、git grep、git log 等工具集成，提升日常效率

## 目录

1. [项目概述](#一项目概述)
   - [Delta 是什么](#11-delta-是什么)
   - [核心数据](#12-核心数据)
   - [核心定位](#13-核心定位)
   - [核心特性](#14-核心特性)
2. [安装](#二安装)
   - [各平台安装](#21-各平台安装)
   - [快速配置](#22-快速配置)
   - [交互式配置](#23-交互式配置)
3. [核心功能](#三核心功能)
   - [语法高亮](#31-语法高亮)
   - [Side-by-side 对比](#32-side-by-side-对比)
   - [行号导航](#33-行号导航)
   - [合并冲突显示](#34-合并冲突显示)
4. [配色主题](#四配色主题)
   - [内置主题](#41-内置主题)
   - [查看所有主题](#42-查看所有主题)
   - [自定义主题](#43-自定义主题)
5. [导航功能](#五导航功能)
   - [文件间导航](#51-文件间导航)
   - [日志视图](#52-日志视图)
   - [grep 结果导航](#53-grep-结果导航)
6. [高级配置](#六高级配置)
   - [超链接](#61-超链接)
   - [文件路径为链接](#62-文件路径为链接)
   - [装饰边框](#63-装饰边框)
   - [代码复制](#64-代码复制)
7. [grep 集成](#七grep-集成)
   - [ripgrep 输出](#71-ripgrep-输出)
   - [git grep](#72-git-grep)
8. [性能与对比](#八性能与对比)
   - [与同类工具的能力边界](#81-与同类工具的能力边界)
   - [设计取舍](#82-设计取舍)
9. [怎么选](#九怎么选)
10. [实践建议](#十实践建议)
    - [完整配置示例](#101-完整配置示例)
    - [主题切换脚本](#102-主题切换脚本)
    - [CI 中的 Delta](#103-ci-中的-delta)
11. [命令行参考](#十一命令行参考)
    - [主要选项](#111-主要选项)
    - [环境变量](#112-环境变量)
12. [资源链接](#十二资源链接)
    - [官方资源](#121-官方资源)
    - [安装包](#122-安装包)
13. [自测题与练习](#十三自测题与练习)
14. [常见问题](#十四常见问题)
15. [进阶路径](#十五进阶路径)
16. [总结](#十六总结)

---

# Delta：让 git diff 在终端里也好看

Delta 是一个语法高亮分页器，给 `git`、`diff`、`grep` 和 `blame` 的输出上色并重排，让每天都要看的变更一眼能分清新增、删除和上下文。

## 一、项目概述

### 1.1 Delta 是什么

**Delta** 是一个 **Git 语法高亮分页器**，用于 git、diff、grep 和 blame 输出。

> "Delta is a syntax-highlighting pager for git, diff, grep, and blame output."

一句话解释定位：git 自带的 diff 是"能看"，Delta 负责把它变成"好看且高效"。语法高亮、行内 diff、双栏对比、跨文件跳转，都属于它接管的范围。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| Stars | **约 3.1 万** ⭐ |
| Forks | 540+ |
| 贡献者 | 150+ |
| 最新版本 | **0.19.2** (2026-03-28) |
| 许可证 | MIT |
| 语言 | Rust（语法高亮引擎与 bat 共用） |

> 维护说明：本文配置示例针对 0.19.x。个别命令名和配置键在不同版本间有别名（如 `--show-syntax-themes` 在新版本里也可能叫 `--list-syntax-themes`），升级后若某项失效，先跑 `delta --help` 或 `delta --show-config` 核对当前版本的实际写法。

### 1.3 核心定位

| 定位 | 说明 |
|------|------|
| 分页器 | 交互式浏览 |
| 语法高亮 | 代码着色 |
| Diff | 代码对比 |
| grep | 搜索结果高亮 |
| blame | 代码历史 |

### 1.4 核心特性

| 特性 | 说明 |
|------|------|
| 语法高亮 | 与 bat 同源的引擎，同一批配色主题 |
| 词级别 Diff | 基于 Levenshtein 编辑推断 |
| Side-by-side | 双栏对比视图，自动换行 |
| 行号 | 显示代码行号 |
| 导航 | n / N 键跳转文件 |
| 合并冲突 | 改进的冲突展示 |
| blame | 历史代码高亮，commit 转链接 |
| grep | 搜索结果着色 |
| Hyperlinks | 超链接 |
| --color-moved | 识别被移动的代码块并单独着色 |
| 模拟模式 | 可模拟 diff-highlight / diff-so-fancy 输出 |
| 主题 | 20+ 配色主题，自动检测亮暗背景 |

## 二、安装

### 2.1 各平台安装

| 平台 | 安装命令 |
|------|----------|
| **Ubuntu/Debian** | `sudo apt install git-delta` |
| **Fedora** | `sudo dnf install git-delta` |
| **macOS** | `brew install git-delta` |
| **Windows (Scoop)** | `scoop install git-delta` |
| **Arch Linux** | `sudo pacman -S git-delta` |
| **Nix** | `nix-env -iA nixpkgs.git-delta` |
| **源码编译** | `cargo install git-delta` |

### 2.2 快速配置

装好后先验证一下能不能跑：

```bash
delta --version   # 应打印版本号，例如 0.19.2
```

再在 `~/.gitconfig` 中添加：

```ini
[core]
    pager = delta

[interactive]
    diffFilter = delta --color-only

[delta]
    navigate = true    # 使用 n 和 N 键导航
    dark = true         # 或 light = true，或省略自动检测

[merge]
    conflictStyle = zdiff3
```

配置写入后，随便 `git diff` 一次，能看到彩色输出就说明生效了。

### 2.3 交互式配置

与直接改 `~/.gitconfig` 等价，但不熟悉的配置项可以逐条来：

```bash
# 运行以下命令逐项配置
git config --global core.pager delta
git config --global interactive.diffFilter 'delta --color-only'
git config --global delta.navigate true
git config --global delta.dark true  # 或 light
git config --global merge.conflictStyle zdiff3
```

想临时不用 delta 看一次 diff，用 `git -c` 在单条命令里关掉对应选项即可，不用改全局配置：

```bash
git -c core.pager= -c delta.line-numbers=false diff
```

排查问题时也能先用 `delta --help`（完整手册）或 `delta -h`（短帮助）确认某个版本是否支持某个选项。

## 三、核心功能

### 3.1 语法高亮

Delta 使用与 **bat** 相同的语法高亮引擎。

```
┌─────────────────────────────────────────────────────────────┐
│                    Delta 语法高亮示例                                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  diff --git a/main.rs b/main.rs                             │
│  index 1234567..89abcdef 100644                            │
│  --- a/main.rs                                              │
│  +++ b/main.rs                                              │
│  @@ -10,7 +10,7 @@ fn main() {                              │
│  -    println!("Hello, world!");                            │
│  +    println!("Hello, Delta!");                            │
│       // 这行未改动                                            │
│       let x = 42;                                           │
│  -    do_something(x);                                       │
│  +    do_something_else(x);                                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Side-by-side 对比

```bash
# 启用双栏对比
git config --global delta.side-by-side true

# 设置列宽
git config --global delta.side-by-side-line-length 120
```

```
┌────────────────────────────┬────────────────────────────┐
│  -    println!("Hello"); │  +    println!("Hi");     │
│  -    let x = 1;        │  +    let x = 2;         │
│      let y = 2;         │      let y = 2;          │
│  -    foo(x, y);        │  +    bar(x, y);         │
└────────────────────────────┴────────────────────────────┘
```

### 3.3 行号导航

| 按键 | 功能 |
|------|------|
| `n` | 下一个文件 |
| `N` | 上一个文件 |
| `j` | 下一行 |
| `k` | 上一行 |
| `g` | 跳转到开头 |
| `G` | 跳转到结尾 |

### 3.4 合并冲突显示

```bash
# 设置冲突样式
git config --global merge.conflictStyle zdiff3

# Delta 会高亮冲突区域
```

```
    <<<<<<< HEAD
    fn old_function() {
    =======
    fn new_function() {
    >>>>>>> feature-branch
```

## 四、配色主题

### 4.1 内置主题

Delta 提供 20+ 预置主题：

| 主题 | 说明 |
|------|------|
| `GitHub` | GitHub 风格 |
| `Monokai` | Monokai 配色 |
| `Dracula` | 吸血鬼配色 |
| `Solarized Dark` | 太阳黑子暗色 |
| `One Dark` | Atom 风格 |
| `Nord` | 北欧风格 |
| `Gruvbox` | 复古风格 |
| `Cold Dark` | 冷色调 |
| `Vincent` | 梵高风格 |

### 4.2 查看所有主题

```bash
# 暗色主题
delta --show-syntax-themes --dark

# 亮色主题
delta --show-syntax-themes --light
```

不同版本里，这个命令也可能叫 `delta --list-syntax-themes`，跑任意一个看输出即可确认。

### 4.3 自定义主题

Delta 的主题分两层。第一层是语法高亮主题，指定某套配色如下：

```ini
[delta]
    syntax-theme = Monokai Extended
```

把 `Monokai Extended` 换成 `delta --show-syntax-themes --dark` 里看到的任意名字即可。主题名若带空格，整体作为一项书写，不要拆开。

第二层是把一组 delta 设置打包成一个"带名字的 feature"，这样一套自选样式可以起个名字复用。先在 `~/.gitconfig` 里定义一个 feature（名为 `my-dracula`），再用 `features` 引用它：

```ini
[delta "my-dracula"]
    syntax-theme = Dracula
    dark = true
    file-style = bold yellow
    hunk-header-style = "syntax bold"
    line-numbers = true

[delta]
    features = my-dracula
```

feature 里的行号、边框、配色想怎么改都行；需要临时停用，把 `delta.features` 里的名字去掉，或运行 `git -c delta.features= diff` 覆盖即可。官方仓库还有一份 `themes.gitconfig`，内置了一批成体系的配色，`delta --show-themes` 可以列出它们。

## 五、导航功能

### 5.1 文件间导航

```bash
# 大型 diff 中快速跳转
git diff --name-only  # 先看有哪些文件

git diff  # 然后用 n/N 跳转
```

### 5.2 日志视图

```bash
# 带语法的日志
git log -p

# 在日志中导航
delta --navigate
```

### 5.3 grep 结果导航

```bash
rg "pattern" | delta
git grep "pattern" | delta
```

grep 输出接上 delta 就会着色，`n` / `N` 在命中行之间跳转。与 rg 的更多配合见「grep 集成」一章。

### 5.4 blame 视图

`git blame` 的输出同样被 delta 接管：语法高亮后，每行能一眼看出作者、时间戳和 commit。打开超链接后，commit 哈希会被格式化成托管平台（GitHub、GitLab、SourceHut、Codeberg）的页面链接，点一下就能跳到提交详情。

```bash
git blame main.rs | delta
```

## 六、高级配置

### 6.1 超链接

Git 默认不渲染超链接，Linux 终端里要配合新版 less（≥ 581）加 `-R` 才有效。启用后，commit 哈希、文件名和行号会变成可点击链接。

```ini
[delta]
    hyperlinks = true
```

commit 链接默认按托管平台自动生成（GitHub、GitLab、SourceHut、Codeberg），想手动指定可以覆盖：

```ini
[delta]
    hyperlinks = true
    hyperlinks-commit-link-format = "https://github.com/dandavison/delta/commit/{commit}"
```

这里只看得到 `{commit}` 一个占位符，它会被替换为完整 commit 哈希。

### 6.2 文件路径为链接

行号跳回编辑器是 delta 超链接最有用的地方。用 `hyperlinks-file-link-format` 指定编辑器协议，就能在 diff 里直接点开对应文件的那一行：

```ini
[delta]
    hyperlinks = true
    hyperlinks-file-link-format = "vscode://file/{path}:{line}"
    # hyperlinks-file-link-format = "idea://open?file={path}&line={line}"
    # hyperlinks-file-link-format = "pycharm://open?file={path}&line={line}"
```

这一项支持 `{path}`（绝对路径）、`{line}`（行号）和 `{host}`（主机名）三个占位符。编辑器没有自己的 URL 协议时，可以用 `file://`（默认值）或写一个本地 HTTP 服务把链接转发给编辑器。

### 6.3 装饰边框

```ini
[delta]
    header-file-style = bold plus-magenta
    file-style = bold yellow
    hunk-header-style = "syntaxbold syntaxcyan"
    hunk-header-decoration-style = "ul above"
```

### 6.4 代码复制

从 diff 里复制代码很方便：Delta 会把新增行和删除行的 `+`、`-` 前缀去掉，只保留颜色作为视觉标记，这样在终端里选中复制到的就是干净代码。该行为默认开启，不需要额外配置。

## 七、grep 集成

### 7.1 ripgrep 输出

Delta 可以直接处理 rg 的输出。最省事的方式是管道：

```bash
rg "pattern" | delta
```

这里不需要 `--pretty`，因为着色和分页都由 delta 接管。如果希望 rg 自带的分页也落到 delta，就在 `~/.ripgreprc` 里配置其分页命令：

```text
--pager=delta
```

再用 `export RIPGREP_CONFIG_PATH=~/.ripgreprc` 指向它即可。注意 rg 的配置文件只接受命令行选项，不能直接写管道。

### 7.2 git grep

```bash
# 高亮的 git grep
git grep "pattern" | delta
```

## 八、性能与对比

### 8.1 与同类工具的能力边界

官方没有发布跨工具的基准测试，网上流传的启动耗时、内存占用数字大多缺乏可复现方法，这里只对比能力边界：

| 工具 | 语法高亮 | 词级 Diff | Side-by-side | 跨文件导航 | 实现 |
|------|----------|-----------|--------------|------------|------|
| **Delta** | ✅ | ✅ | ✅ | ✅ n/N | Rust |
| diff-so-fancy | ❌ | ⚠️ 单行内 | ❌ | ❌ | Perl |
| diff-highlight | ❌ | ✅ 词级着色 | ❌ | ❌ | Shell/Perl |
| 原生 git + less | ❌ | ❌ | ❌ | ❌ | — |

Delta 的语法高亮与主题来自 syntect（与 bat 同一引擎），词级高亮基于 Levenshtein 编辑推断。它真正拉开差距的是工作流能力：跨文件导航、行号、合并冲突重排，以及 blame 里把 commit 变成可点击链接。

### 8.2 设计取舍

- 超大 diff 的首次渲染比之后慢，属正常现象，不代表后续每次都会这样。
- 需要给其他工具喂带色的局部输出时，用 `delta --color-only` 走管道；分页职责交给 delta 本身更合适。
- 常用参数组合可以用 `--features` 打包成命名集合，避免每次敲一长串参数。

## 九、怎么选

一句话判断：想要完整的语法高亮、双栏对比和跨文件导航，Delta 是目前最省事的选项；只是想让输出稍微好看一点，Git 自带的 `contrib/diff-highlight` 也够用。

- 主力工作流：直接配 Delta，一次设置，git / diff / grep / blame 全部接管。
- 只想看词级着色、不想引入新依赖：用 Git 自带的 `contrib/diff-highlight`（为 `git config pager.diff` 指一下即可）。
- 终端不支持真彩色：语法高亮会退化成普通着色，Delta 的优势变小，轻量方案更合适。

## 十、实践建议

### 10.1 完整配置示例

```ini
[core]
    pager = delta

[interactive]
    diffFilter = delta --color-only

[delta]
    navigate = true
    dark = true
    show-line-numbers = true
    line-numbers-minus-style = cyan
    line-numbers-plus-style = cyan
    syntax-theme = GitHub Dark
    side-by-side = true
    side-by-side-line-length = 120
    file-style = bold blue underline
    hunk-header-style = "syntaxbold syntaxcyan"
    hunk-header-decoration-style = "ul above"

[merge]
    conflictStyle = zdiff3

[pager]
    log = delta
    show = delta
    diff = delta
    blame = delta
```

> 提示：`merge.conflictStyle = zdiff3` 属于 Git 的 `[merge]` 段，不属于 delta，把它放对位置才生效。`core.autocrlf` 与 delta 无关，属于 Git 行尾处理，不要顺手加在这里。

### 10.2 主题切换脚本

亮暗主题切换的底层是 `delta.dark` 和 `delta.light` 两个布尔值，二者是互斥关系。写脚本时把当前值读出来、改到另一侧即可：

```bash
#!/bin/bash
# toggle_delta_theme.sh

if [ "$(git config --global delta.dark 2>/dev/null)" = "true" ]; then
    git config --global --unset delta.dark
    git config --global delta.light true
    echo "Switched to light theme"
else
    git config --global --unset delta.light
    git config --global delta.dark true
    echo "Switched to dark theme"
fi
```

语法高亮配色和亮暗背景是两回事：脚本切的只是背景亮暗，想要同时换一套配色，加一行 `git config --global delta.syntax-theme <theme-name>` 即可。

### 10.3 CI 中的 Delta

```yaml
# .github/workflows/ci.yml
- name: Run tests
  run: |
    cargo test
    cargo test --doc
    cargo fmt --check
    cargo clippy -- -D warnings
```

## 十一、命令行参考

### 11.1 主要选项

| 选项 | 说明 | 示例 |
|------|------|------|
| `--side-by-side` | 双栏对比 | `--side-by-side` |
| `--line-numbers` | 显示行号 | `--line-numbers` |
| `--navigate` | 启用 n / N 导航 | `--navigate` |
| `--syntax-theme` | 语法高亮主题 | `--syntax-theme=Monokai` |
| `--dark` | 暗色背景 | `--dark` |
| `--light` | 亮色背景 | `--light` |
| `--show-syntax-themes` | 列出可用配色主题 | `--show-syntax-themes --dark` |
| `--hyperlinks` | 把 commit、文件、行号变成超链接 | `--hyperlinks` |
| `--hyperlinks-commit-link-format` | 覆盖 commit 链接格式 | `--hyperlinks-commit-link-format=https://.../commit/{commit}` |
| `--hyperlinks-file-link-format` | 覆盖文件/行号链接格式 | `--hyperlinks-file-link-format="vscode://file/{path}:{line}"` |
| `--features` | 启用一组命名设置 | `--features side-by-side` |

### 11.2 环境变量

| 变量 | 说明 |
|------|------|
| `DELTA_FEATURES` | 临时启用的 feature 名，前面加 `+` 表示在 git config 基础上追加，如 `+side-by-side` |
| `DELTA_PAGER` | delta 用来翻页的命令，优先级最高的分页器变量；未设置时依次回退 `BAT_PAGER`、`PAGER`，最后是 `less -R` |
| `GIT_PAGER` | Git 的分页器变量，要么不设置，要么设为 `delta`，否则 Git 不会走 delta |
| `COLORTERM` | 设为 `truecolor` 启用 24 位色，保证高亮正常 |

## 十二、资源链接

### 12.1 官方资源

| 资源 | 链接 |
|------|------|
| 🌐 **官网** | https://dandavison.github.io/delta/ |
| 📦 **GitHub** | https://github.com/dandavison/delta |
| 📖 **文档** | https://dandavison.github.io/delta/ |
| 💬 **Gitter** | https://gitter.im/dandavison-delta/community |

### 12.2 安装包

| 平台 | 安装命令 |
|------|----------|
| Ubuntu/Debian | `apt install git-delta` |
| macOS | `brew install git-delta` |
| Arch | `pacman -S git-delta` |
| 源码 | `cargo install git-delta` |

## 十三、自测题与练习

完成本文阅读后，请尝试回答以下问题，检验你的理解程度：

1. **Delta 的核心价值是什么？为什么需要 Git 语法高亮分页器？**
   - 参考答案：Delta 解决了传统 git diff 输出单调、难以快速定位变更的问题。它通过语法高亮、Side-by-side 对比、行号导航等功能，显著提升了代码审查效率和体验。

2. **如何在 macOS 上安装 Delta？如何在 Linux 上安装 Delta？**
   - 参考答案：macOS 使用 `brew install git-delta`；Ubuntu/Debian 使用 `sudo apt install git-delta`；Fedora 使用 `sudo dnf install git-delta`。

3. **如何配置 Delta 作为 Git 的默认分页器？需要设置哪些配置项？**
   - 参考答案：需要设置 `core.pager = delta`、`interactive.diffFilter = delta --color-only`、`delta.navigate = true` 等配置项。

4. **如何启用 Side-by-side 对比视图？它有什么优势？**
   - 参考答案：使用 `git config --global delta.side-by-side true` 启用。优势是左右对比更直观，便于快速理解代码变更。

5. **如何切换 Delta 的主题？如何查看所有可用的主题？**
   - 参考答案：使用 `git config --global delta.syntax-theme <theme-name>` 切换语法高亮主题；用 `delta --show-syntax-themes --dark` 或 `--light` 查看所有可用的主题名。

### 13.1 动手练习

如果你手边有 Git 仓库，可以跟着做一遍：

1. **安装 Delta**：在你的系统上安装 Delta（macOS 用 `brew install git-delta`，Linux 用 `sudo apt install git-delta` 或 `sudo dnf install git-delta`）。
2. **基础配置**：运行 `git config --global core.pager delta` 等命令，把 Delta 配成默认分页器。
3. **换个主题**：运行 `delta --show-syntax-themes --dark`，挑一个你喜欢的主题，然后用 `git config --global delta.syntax-theme <theme-name>` 切换过去。`syntax-theme` 是设置语法高亮主题的配置项，注意它不是 `theme`。
4. **看一次 Side-by-side 对比**：改一下某个文件，然后 `git diff`，打开 Side-by-side 视图看效果。
5. **配一次 ripgrep**：运行 `rg "pattern" | delta`，看搜索结果的高亮效果。

---

## 十四、常见问题

**为什么我的 diff 没有高亮？**
多数情况是终端没开真彩色。在 shell 配置里加上 `COLORTERM=truecolor`，并确认终端支持 24 位色；再跑 `git config --get core.pager` 确认分页器确实指向了 delta。

**想临时不用 delta 怎么看 diff？**
单次跳过即可：`git --no-pager diff`，或临时改分页器 `GIT_PAGER=less git diff`。

**side-by-side 对不齐、错位怎么办？**
调大 `side-by-side-line-length`，或先回单栏排障：`git config --global delta.side-by-side false`。

**我想要亮色主题，但自动检测成了暗色？**
显式指定：`git config --global delta.light true`，反之用 `delta.dark true`。

**配色弄乱了想恢复默认？**
`git config --global --remove-section delta` 会删掉 delta 段，回到 Git 默认输出，再重新贴配置即可。

---

## 十五、进阶路径

如果你希望深入掌握 Delta，可以参考以下进阶路径：

1. **基础配置**：掌握 Delta 的安装和基本配置，理解核心功能和选项
   - 实践任务：在你的所有开发环境中安装 Delta，并配置基本选项
   - 学习目标：能够独立安装和配置 Delta，理解核心功能

2. **高级定制**：学习如何定制 Delta 的主题、样式和行为，满足个性化需求
   - 实践任务：尝试不同的主题，定制符合你喜好的配色和样式
   - 学习目标：能够根据个人偏好定制 Delta 的外观和行为

3. **工作流集成**：将 Delta 集成到日常 Git 工作流，与 ripgrep、git grep 等工具配合使用
   - 实践任务：配置 Delta 与 ripgrep、git grep、git log 等工具集成
   - 学习目标：能够构建高效、流畅的 Git 工作流

4. **社区参与**：参与 Delta 社区，学习源码实现，甚至贡献代码或文档
   - 实践任务：阅读 Delta 源码，理解其实现原理；参与社区讨论，贡献代码或文档
   - 学习目标：能够深入理解 Delta 的实现细节，并为项目做出贡献

---

## 十六、总结

如果你每天要用 git diff 看代码变更，Delta 值得试一试。

它的核心价值是把「能看」变成「好看且高效」：语法高亮让你一眼分出字符串、关键字和注释；Side-by-side 视图把新增和删除并排，不用在上下行之间来回比对；行号加 n/N 跳转让你在大型 diff 里不迷路。

配置一次，所有 git、diff、grep、blame 的输出都会走 Delta。主题有 20+ 套，配色不满意可以自己改；和 ripgrep 搭配尤其顺手，搜索结果直接高亮。

当然它也不是万能的：超大型仓库的 diff 第一次渲染会稍慢（后续有缓存），主题配置项比较多，刚开始可能需要翻文档找个合适的配色。但一旦配好，基本就不用再管了。

---

**🔗 相关资源：**

| 资源 | 链接 |
|------|------|
| GitHub | https://github.com/dandavison/delta |
| 官网 | https://dandavison.github.io/delta/ |
| Gitter | https://gitter.im/dandavison-delta/community |

---

---

_🦞 本文由钳岳星君撰写，基于 Delta (31.2k+ Stars)_
