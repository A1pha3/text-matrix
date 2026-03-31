---
title: "Ripgrep：极速递归搜索工具完全指南"
slug: "ripgrep-recursive-search-guide"
date: 2026-03-31T23:14:00+08:00
categories: ["技术笔记"]
tags: ["Ripgrep", "rg", "grep", "搜索工具", "Rust", "正则表达式", "命令行工具", "性能优化", "PCRE2", "代码搜索"]
description: "深度解析 Ripgrep (61.7k Stars)：比 GNU grep 快 6-30x 的极速递归搜索工具，基于 Rust 正则引擎 + SIMD + literal 优化，支持 Unicode/PCRE2/压缩文件/多编码，官方基准测试显示 Linux 内核搜索 0.082s vs GNU grep 0.727s。"
---

# Ripgrep：极速递归搜索工具完全指南

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 Ripgrep 的设计理念与核心优势
- ✅ 掌握 Ripgrep 的安装与配置方法
- ✅ 熟练使用 Ripgrep 进行日常搜索任务
- ✅ 理解 Ripgrep 的性能优化技术
- ✅ 掌握正则表达式与文件过滤技巧
- ✅ 使用 Ripgrep 的进阶功能（PCRE2、压缩文件、编码支持）
- ✅ 编写自定义配置与 Shell 补全

---

## §2 项目概述

### 2.1 什么是 Ripgrep？

**Ripgrep**（[GitHub 仓库](https://github.com/BurntSushi/ripgrep)，二进制名称 `rg`）是一个**行-oriented 搜索工具**，递归搜索当前目录下的正则表达式模式。

**官方描述**：

> ripgrep is a line-oriented search tool that recursively searches the current directory for a regex pattern. By default, ripgrep will respect gitignore rules and automatically skip hidden files/directories and binary files.

**核心定位**：比 grep/ag/ugrep 更快、更智能的代码搜索工具，同时默认支持 Unicode。

### 2.2 核心数据

| 指标 | 数值 |
|------|------|
| **Stars** | 61,665 (61.7k) |
| **Forks** | 2,500 (2.5k) |
| **Watchers** | 281 |
| **贡献者** | （详见 GitHub） |
| **提交数** | 2,209 |
| **发布版本** | 74 个 |
| **最新版本** | v15.1.0 (2025-10-22) |
| **许可证** | Unlicense + MIT（双许可证） |

### 2.3 技术栈

| 类别 | 技术 | 占比 |
|------|------|------|
| **核心语言** | Rust | 94.6% |
| **构建/测试** | Python | 2.6% |
| **脚本** | Shell | 2.1% |
| **其他** | — | 0.7% |

### 2.4 核心特性

| 特性 | 说明 |
|------|------|
| **极速搜索** | 基于 Rust 正则引擎 + SIMD + literal 优化 |
| **智能过滤** | 自动跳过 .gitignore/.ignore/.rgignore 中的文件 |
| **隐藏文件** | 默认跳过隐藏文件和目录 |
| **二进制文件** | 默认跳过二进制文件 |
| **Unicode 支持** | 默认开启，无需额外配置 |
| **文件类型** | 支持按文件类型搜索（-t/-T） |
| **压缩文件** | 支持搜索压缩文件（brotli/bzip2/gzip/lz4/lzma/xz/zstd） |
| **文本编码** | 支持 UTF-16/GBK/EUC-JP/Shift_JIS 等编码 |
| **PCRE2** | 可选支持 PCRE2（-P/--pcre2） |
| **多行搜索** | 支持跨行模式匹配 |
| **替换功能** | 支持搜索结果替换 |

### 2.5 竞品对比

| 工具 | 适用场景 | 优势 |
|------|----------|------|
| **Ripgrep** | 代码搜索 | 极速、Unicode、智能过滤 |
| **The Silver Searcher (ag)** | 代码搜索 | 简单易用 |
| **ack** | 代码搜索 | 功能丰富 |
| **GNU grep** | 通用搜索 | POSIX 兼容、 ubiquitous |

---

## §3 性能基准

### 3.1 Linux 内核源码搜索

测试环境：Intel i9-12900K 5.2 GHz，搜索模式 `[A-Z]+_SUSPEND`（仅匹配完整单词）

| 工具 | 命令 | 匹配行数 | 时间 | 相对速度 |
|------|------|----------|------|----------|
| **Ripgrep** | `rg -n -w '[A-Z]+_SUSPEND'` | 536 | **0.082s** | 1.00x |
| hypergrep | `hgrep -n -w '[A-Z]+_SUSPEND'` | 536 | 0.167s | 2.04x |
| git grep | `git grep -P -n -w '[A-Z]+_SUSPEND'` | 536 | 0.273s | 3.34x |
| The Silver Searcher | `ag -w '[A-Z]+_SUSPEND'` | 534 | 0.443s | 5.43x |
| ugrep | `ugrep -r --ignore-files --no-hidden -I -w '[A-Z]+_SUSPEND'` | 536 | 0.639s | 7.82x |
| GNU grep (C) | `LC_ALL=C git grep -E -n -w '[A-Z]+_SUSPEND'` | 536 | 0.727s | 8.91x |
| GNU grep (Unicode) | `LC_ALL=en_US.UTF-8 git grep -E -n -w '[A-Z]+_SUSPEND'` | 536 | 2.670s | 32.70x |
| ack | `ack -w '[A-Z]+_SUSPEND'` | 2677 | 2.935s | 35.94x |

### 3.2 大文件搜索（13GB OpenSubtitles）

| 工具 | 命令 | 匹配行数 | 时间 | 相对速度 |
|------|------|----------|------|----------|
| **Ripgrep** | `rg -w 'Sherlock [A-Z]\w+'` | 7882 | **1.042s** | 1.00x |
| ugrep | `ugrep -w 'Sherlock [A-Z]\w+'` | 7882 | 1.339s | 1.28x |
| GNU grep (Unicode) | `LC_ALL=en_US.UTF-8 egrep -w 'Sherlock [A-Z]\w+'` | 7882 | 6.577s | 6.31x |

### 3.3 性能悬崖测试

某些正则模式会导致所有工具性能下降，但 Ripgrep 仍保持领先：

| 工具 | 命令 | 时间 | 相对速度 |
|------|------|------|----------|
| **Ripgrep** | `rg -w '[A-Z]\w+ Sherlock [A-Z]\w+'` | **1.053s** | 1.00x |
| GNU grep | `LC_ALL=en_US.UTF-8 grep -E -w '[A-Z]\w+ Sherlock [A-Z]\w+'` | 6.234s | 5.92x |
| ugrep | `ugrep -w '[A-Z]\w+ Sherlock [A-Z]\w+'` | 28.973s | 27.51x |

### 3.4 高匹配率场景（8.34 亿次匹配）

| 工具 | 命令 | 匹配数 | 时间 | 相对速度 |
|------|------|---------|------|----------|
| **Ripgrep** | `rg the` | 83,499,915 | **6.948s** | 1.00x |
| ugrep | `ugrep the` | 83,499,915 | 11.721s | 1.69x |
| GNU grep | `LC_ALL=C grep the` | 83,499,915 | 15.217s | 2.19x |

### 3.5 极速之谜

Ripgrep 如此快速的原因：

1. **Rust 正则引擎**：基于有限自动机 + SIMD + 激进 literal 优化
2. **UTF-8 内置**：Unicode 支持不影响性能
3. **智能搜索**：自动选择内存映射（单文件）或增量搜索（大型目录）
4. **RegexSet 优化**：使用单一正则同时匹配多个 glob 模式
5. **并行迭代器**：无锁并行递归目录遍历（crossbeam + ignore）

---

## §4 安装与部署

### 4.1 系统包管理器

| 系统 | 命令 |
|------|------|
| **macOS Homebrew** | `brew install ripgrep` |
| **MacPorts** | `sudo port install ripgrep` |
| **Windows Chocolatey** | `choco install ripgrep` |
| **Windows Scoop** | `scoop install ripgrep` |
| **Windows Winget** | `winget install BurntSushi.ripgrep.MSVC` |
| **Arch Linux** | `sudo pacman -S ripgrep` |
| **Gentoo** | `sudo emerge sys-apps/ripgrep` |
| **Fedora** | `sudo dnf install ripgrep` |
| **openSUSE** | `sudo zypper install ripgrep` |
| **Debian/Ubuntu** | `sudo apt-get install ripgrep` 或下载 .deb |
| **FreeBSD** | `sudo pkg install ripgrep` |
| **OpenBSD** | `doas pkg_add ripgrep` |
| **NetBSD** | `sudo pkgin install ripgrep` |
| **Void Linux** | `sudo xbps-install -Syv ripgrep` |
| **Nix** | `nix-env --install ripgrep` |
| **Guix** | `guix install ripgrep` |
| **Rust (cargo)** | `cargo install ripgrep` |
| **Rust (binstall)** | `cargo binstall ripgrep` |

### 4.2 从源码编译

```bash
# 克隆仓库
git clone https://github.com/BurntSushi/ripgrep
cd ripgrep

# 编译（需要 Rust 1.85.0+）
cargo build --release
./target/release/rg --version
```

### 4.3 启用 PCRE2 支持

```bash
# 启用 PCRE2（如 look-around、backreferences）
cargo build --release --features 'pcre2'
```

### 4.4 构建 MUSL 静态二进制

```bash
# 添加 MUSL 目标
rustup target add x86_64-unknown-linux-musl

# 编译静态二进制
cargo build --release --target x86_64-unknown-linux-musl
```

### 4.5 运行测试

```bash
# 运行完整测试套件
cargo test --all
```

---

## §5 使用指南

### 5.1 基础用法

```bash
# 基本搜索
rg pattern

# 递归搜索（默认开启）
rg -r pattern

# 显示行号
rg -n pattern

# 显示匹配和行号
rg -n pattern

# 显示文件名（默认）
rg pattern

# 显示文件名（仅匹配）
rg -l pattern

# 显示不含匹配的文件的文件名
rg -L pattern

# 统计匹配数
rg -c pattern
```

### 5.2 智能过滤

默认情况下，Ripgrep 会自动跳过：

- `.gitignore`/`.ignore`/`.rgignore` 中的文件
- 隐藏文件和目录
- 二进制文件

```bash
# 禁用所有自动过滤
rg -uuu pattern

# 搜索隐藏文件
rg --hidden pattern

# 包含被忽略的文件
rg --no-ignore pattern
```

### 5.3 文件类型过滤

```bash
# 仅搜索 Python 文件
rg -tpy pattern

# 排除 JavaScript 文件
rg -Tjs pattern

# 搜索多种类型
rg -tpy -tts pattern

# 列出支持的文件类型
rg --type-list
```

### 5.4 正则表达式

```bash
# 基本正则（默认）
rg 'foo.*bar'

# 完整单词匹配
rg -w 'pattern'

# 不区分大小写
rg -i 'pattern'

# 转义特殊字符
rg -F 'pattern.with.dots'
```

### 5.5 输出格式

```bash
# JSON 输出（可用于管道）
rg --json pattern

# CSV 输出
rg --csv pattern

# 紧凑输出
rg --no-heading pattern

# 显示上下文
rg -C 3 pattern  # 3 行上下文

# 显示匹配周围的行
rg -B 2 -A 2 pattern  # 2 行 before + 2 行 after
```

### 5.6 搜索压缩文件

```bash
# 搜索压缩文件（brotli/bzip2/gzip/lz4/lzma/xz/zstd）
rg -z pattern

# 示例
rg -z 'function_name' --gzipped
```

### 5.7 文本编码

```bash
# 指定编码
rg -E utf-16 pattern

# 自动检测编码
rg --preload pattern

# 支持的编码：utf-8, utf-16, latin-1, gbk, euc-jp, shift_jis
```

### 5.8 替换功能

```bash
# 替换匹配（需要 -r）
rg 'old_pattern' -r 'new_pattern'

# 使用捕获组
rg '(\d+)' -r '[$1]'
```

---

## §6 进阶用法

### 6.1 PCRE2 正则

Ripgrep 默认使用 Rust 正则引擎。要使用 PCRE2（支持 look-around 和 backreferences）：

```bash
# 使用 PCRE2
rg -P 'pattern(?=lookahead)'

# 自动选择（仅在需要时使用 PCRE2）
rg --auto-hybrid-regex 'pattern'
```

### 6.2 多行搜索

```bash
# 多行模式（使用 \n）
rg 'start.*\n.*end' pattern.txt

# 跨行匹配（PCRE2）
rg -P 'foo.*bar' -U pattern.txt
```

### 6.3 预处理器

使用外部过滤器预处理输入：

```bash
# 使用预处理器（如 PDF 提取）
rg --pre 'pdftotext -q' 'pattern' file.pdf

# 使用 xxd 预览二进制
rg --pre 'xxd' 'pattern' file.bin
```

### 6.4 配置文件

Ripgrep 支持配置文件（`.ripgreprc`）：

```ini
# ~/.ripgreprc
--smart-case
--hidden
--glob !*.log
--type-add 'config:*.{toml,yaml,json}'
```

### 6.5 Shell 补全

```bash
# 生成 Bash 补全
rg --generate-completion bash

# 生成 Zsh 补全
rg --generate-completion zsh

# 生成 Fish 补全
rg --generate-completion fish
```

---

## §7 配置详解

### 7.1 配置搜索顺序

1. `RIPGREP_CONFIG_PATH` 环境变量
2. `./.ripgreprc`（当前目录）
3. `~/.ripgreprc`（用户目录）

### 7.2 常用配置项

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `--smart-case` | 大写则区分大小写 | `--smart-case` |
| `--hidden` | 搜索隐藏文件 | `--hidden` |
| `--glob` | 全局模式排除 | `--glob !*.log` |
| `--type-add` | 添加自定义文件类型 | `--type-add 'config:*.toml'` |
| `--max-count` | 最大匹配数 | `--max-count 100` |
| `--max-depth` | 最大递归深度 | `--max-depth 5` |
| `--sort` | 排序方式 | `--sort path` |

### 7.3 Git 集成

```bash
# 仅搜索 Git 跟踪的文件
rg --glob '!.git/**' pattern

# 搜索 Git stash
git stash list | rg pattern

# 搜索 Git 历史
git log --all -S 'pattern'
```

---

## §8 性能优化

### 8.1 优化技巧

| 技巧 | 说明 | 命令 |
|------|------|------|
| **使用字面量** | 包含字面量的模式更快 | `rg 'literal_text'` |
| **禁用 Unicode** | 加速 ASCII-only 搜索 | `rg -u 'ASCII'` |
| **限制深度** | 避免过深递归 | `rg --max-depth 10` |
| **文件类型** | 仅搜索相关类型 | `rg -tpy pattern` |
| **内存映射** | 适用于单文件 | `rg -mmap pattern` |

### 8.2 诊断工具

```bash
# 显示搜索统计
rg --stats pattern

# 显示调试信息
rg -vvv pattern
```

---

## §9 项目结构

### 9.1 目录结构

```
ripgrep/
├── .cargo/               # Cargo 配置
├── .github/              # GitHub Actions
├── benchsuite/           # 基准测试套件
├── ci/                   # CI 配置
├── crates/               # 子 crate
├── fuzz/                 # 模糊测试
├── pkg/                  # 打包配置
├── scripts/              # 脚本
├── tests/                # 集成测试
├── Cargo.toml            # 根 workspace 配置
├── Cargo.lock            # 依赖锁定
├── build.rs              # 构建脚本
└── rustfmt.toml         # Rust 格式化配置
```

### 9.2 核心模块

| 模块 | 说明 |
|------|------|
| **crates/core** | 核心搜索逻辑 |
| **crates/printer** | 输出格式化 |
| **crates/search** | 正则搜索 |
| **crates/wtr** | 输出写入器 |

### 9.3 关键文件

| 文件 | 说明 |
|------|------|
| **GUIDE.md** | 用户指南 |
| **FAQ.md** | 常见问题 |
| **CHANGELOG.md** | 发布历史 |

---

## §10 常见问题

### Q1：Ripgrep 能完全替代 grep 吗？

**基本可以**。Ripgrep 默认行为与 grep 不同（递归、跳过隐藏文件/二进制），但可通过 `-uuu` 禁用所有过滤获得与传统 grep 类似的行为。

### Q2：Ripgrep 支持 POSIX grep 吗？

Ripgrep 不是 POSIX 兼容的。如果需要完全兼容的 grep，请使用 GNU grep。

### Q3：Ripgrep 如何处理大文件？

Ripgrep 自动选择最佳策略：
- **单文件**：使用内存映射（mmap）
- **大型目录**：使用增量搜索和中间缓冲区

### Q4：Ripgrep 支持哪些正则语法？

**默认**：Rust regex 语法（类似 PCRE，但不支持 look-around 和 backreferences）

**PCRE2**：`rg -P pattern`（需要 `--features 'pcre2'` 编译）

### Q5：Ripgrep 如何处理二进制文件？

默认跳过二进制文件。使用 `-a/--text` 强制将二进制文件当作文本搜索。

### Q6：Ripgrep 如何处理压缩文件？

使用 `-z/--search-zip` 搜索压缩文件：

```bash
rg -z 'pattern' file.gz
```

---

## §11 总结

### 11.1 核心优势

| 优势 | 说明 |
|------|------|
| **极速** | 比 GNU grep 快 6-30x |
| **智能过滤** | 默认跳过 .gitignore/隐藏/二进制 |
| **Unicode** | 默认支持，无需配置 |
| **跨平台** | Windows/macOS/Linux 完美支持 |
| **功能丰富** | PCRE2、压缩文件、多编码 |

### 11.2 适用场景

| 场景 | 推荐命令 |
|------|----------|
| **代码搜索** | `rg -tpy pattern` |
| **日志分析** | `rg -uuu pattern *.log` |
| **大文件搜索** | `rg -z pattern` |
| **正则替换** | `rg pattern -r 'replace'` |
| **JSON 处理** | `rg --json pattern` |

### 11.3 项目信息

| 项目 | 信息 |
|------|------|
| **Stars** | 61.7k |
| **Forks** | 2.5k |
| **版本** | v15.1.0 |
| **许可证** | Unlicense + MIT |

### 11.4 相关链接

| 资源 | 链接 |
|------|------|
| **GitHub** | https://github.com/BurntSushi/ripgrep |
| **文档** | https://github.com/BurntSushi/ripgrep/blob/master/GUIDE.md |
| **FAQ** | https://github.com/BurntSushi/ripgrep/blob/master/FAQ.md |
| **博客** | https://blog.burntsushi.net/ripgrep/ |

---

## §12 附录：命令行参考

### 12.1 常用选项

| 选项 | 说明 |
|------|------|
| `-n/--line-number` | 显示行号 |
| `-l/--files-with-matches` | 仅显示文件名 |
| `-L/--files-without-match` | 显示不含匹配的文件 |
| `-i/--ignore-case` | 不区分大小写 |
| `-w/--word-regexp` | 仅匹配完整单词 |
| `-F/--fixed-strings` | 使用字面量（非正则） |
| `-c/--count` | 显示匹配数 |
| `-C/--context` | 显示上下文行数 |
| `-o/--only-matching` | 仅显示匹配部分 |
| `-r/--replace` | 替换匹配 |
| `-A/--after-context` | 匹配后行数 |
| `-B/--before-context` | 匹配前行数 |
| `-z/--search-zip` | 搜索压缩文件 |
| `-E/--encoding` | 指定文本编码 |
| `-t/--type` | 搜索特定类型 |
| `-T/--type-not` | 排除特定类型 |
| `-u/--unrestricted` | 禁用过滤（-uuu 完全禁用） |

### 12.2 输出格式

| 选项 | 说明 |
|------|------|
| `--json` | JSON 格式 |
| `--csv` | CSV 格式 |
| `--vimgrep` | Vim 格式 |
| `--colout` | 列格式化 |

---

*文档版本 1.0 | 撰写日期：2026-03-31 | 基于 Ripgrep v15.1.0 (61.7k Stars) | 性能数据来源：官方基准测试*