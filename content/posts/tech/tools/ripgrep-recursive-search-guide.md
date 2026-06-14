---
title: "Ripgrep 完全指南：从入门到原理、架构与扩展"
slug: "ripgrep-recursive-search-guide"
aliases:
  - /posts/tech/ripgrep-recursive-search-guide/
date: "2026-03-31T23:14:00+08:00"
categories: ["技术笔记"]
tags: ["Ripgrep", "rg", "Rust", "PCRE2", "代码搜索"]
description: "基于 Ripgrep 官方 README、GUIDE、FAQ、CHANGELOG 与 15.1.0 帮助信息整理，系统讲解 rg 的默认行为、性能原理、工程架构、扩展方式与常见误区。"
---

# Ripgrep 使用指南：从入门到原理、架构与扩展

## §1 学习目标

完成本文档后，你将能够：

- ✅ 理解 Ripgrep 的定位、默认行为与适用边界
- ✅ 从入门命令一路掌握到常见高级用法
- ✅ 理解 Ripgrep 为什么快，以及什么时候会变慢
- ✅ 看懂 Ripgrep 的高层工程架构与核心 crate 分工
- ✅ 掌握多行、编码、压缩文件、预处理器、PCRE2 等进阶能力
- ✅ 了解如何配置、扩展、集成与二次开发
- ✅ 避开文档和网络教程里最常见的错误说法

---

## §2 项目概述

### 2.1 什么是 Ripgrep？

**Ripgrep** 是一个命令行文本搜索工具，命令名是 `rg`。官方对它的定义是：

> ripgrep is a line-oriented search tool that recursively searches the current directory for a regex pattern.

翻成更容易落地的话，可以理解成：

- 它默认递归搜索目录；
- 它默认把输入当成“按行匹配”的搜索任务；
- 它默认尊重 `.gitignore`、`.ignore`、`.rgignore`；
- 它默认跳过隐藏文件、隐藏目录和二进制文件；
- 它把“代码仓库搜索”当成核心主场景来优化。

如果你经常做下面这些事，Ripgrep 往往非常合适：

- 在代码仓库里快速搜函数、配置、错误信息；
- 搜 UTF-8 / UTF-16 文本；
- 需要文件类型过滤、忽略规则和高亮输出；
- 需要把搜索接进编辑器、脚本或终端工具链。

### 2.2 这篇文章严格依据什么资料？

本文尽量只保留**可核实**的信息，主要依据：

- 官方 README；
- 官方 GUIDE；
- 官方 FAQ；
- 官方 Releases / CHANGELOG；
- 本地 `rg 15.1.0` 的 `--help` 与 `--version` 输出。

文中的“性能、默认行为、配置方式、Shell 补全、PCRE2、压缩文件、编码处理”等关键信息，都以这些官方资料为准，不采用道听途说的说法。

### 2.3 最新版本与许可

- 本地验证版本：`ripgrep 15.1.0`
- 本地验证特性：`features:+pcre2`
- 许可证：**MIT 或 Unlicense 双许可证**

---

## §3 先建立正确的心智模型

### 3.1 Ripgrep 不是“更快的 grep”这么简单

很多人第一次用 `rg`，会把它理解成：

- 命令更短；
- 搜得更快；
- 输出更好看。

这当然没错，但不够本质。Ripgrep 真正的设计重点是：

1. **把代码仓库搜索当成默认任务**  
   所以它天然重视忽略规则、文件类型、并行遍历和输出可读性。

2. **把 Unicode 当成默认能力，而不是额外负担**  
   这和很多传统工具的使用体验不同。

3. **把“自动做对常见事”当成产品哲学**  
   比如默认跳过二进制、默认递归、默认尊重 ignore 规则。

### 3.2 你真正需要记住的 4 条默认行为

初学者最容易踩坑的地方，不在正则，而在默认行为。记住下面 4 条，已经能解释 80% 的“为什么搜不到”：

1. **没写路径时，默认搜当前目录。**
2. **遇到目录时，默认递归。**
3. **默认尊重 `.gitignore`、`.ignore`、`.rgignore`。**
4. **默认跳过隐藏文件和二进制文件。**

这四条里，第 3 条和第 4 条最容易让新手误以为“Ripgrep 漏结果了”。事实上，很多时候不是漏，而是它在替你做筛选。

### 3.3 它最适合什么，不适合什么？

更适合：

- 搜代码仓库；
- 搜大量文本文件；
- 搜 UTF-8 / UTF-16 内容；
- 搭配脚本、编辑器、终端流水线。

不适合直接替代的场景：

- 需要 **POSIX 兼容** 的 Shell 脚本；
- 需要完全复刻 GNU grep 的行为；
- 需要**原地修改文件**；
- 需要把压缩包当目录树递归展开搜索；
- 需要完全稳定、确定的输出顺序但又不愿牺牲并行性能。

---

## §4 5 分钟快速上手

```bash
# 安装（macOS / Homebrew）
brew install ripgrep

# 查看版本
rg --version

# 在当前目录递归搜索 error
rg error

# 只搜 Python 文件
rg -tpy 'def main'

# 搜字面量而不是正则
rg -F 'foo.bar'

# 显示 2 行上下文
rg -C 2 timeout
```

### 4.1 第一个必须会的例子

```bash
rg 'panic|error|fatal' .
```

这条命令表达了 Ripgrep 的典型风格：

- 搜索模式是正则；
- 路径可以省略，也可以显式写出；
- 对目录自动递归；
- 输出文件名、行号、匹配行。

### 4.2 新手高频命令速查

| 目的 | 命令 |
| ------ | ------ |
| 搜当前目录 | `rg pattern` |
| 搜指定目录 | `rg pattern src` |
| 搜多个路径 | `rg pattern src tests README.md` |
| 显示行号 | `rg -n pattern` |
| 只列出命中文件 | `rg -l pattern` |
| 列出未命中的文件 | `rg -L pattern` |
| 统计命中行数 | `rg -c pattern` |
| 只输出匹配片段 | `rg -o pattern` |
| 显示前后文 | `rg -C 3 pattern` |
| 按文件名排序输出 | `rg --sort path pattern` |

### 4.3 从 grep 迁移时最容易犯的错

很多旧教程会写：

```bash
rg -r pattern
```

这是错的。

在 Ripgrep 里：

- **递归搜索本来就是默认行为**；
- `-r` / `--replace` 的含义是**替换输出中的匹配文本**，不是“递归”。

所以如果你想递归搜索，最普通的写法就是：

```bash
rg pattern
```

如果你想做输出替换，才写：

```bash
rg 'foo' -r 'bar'
```

而且这个替换**不会修改磁盘上的文件**，它只改输出结果。

---

## §5 使用指南

### 5.1 基础搜索：先把最常用的 8 个开关练熟

```bash
# 忽略大小写
rg -i 'error'

# 智能大小写：模式里有大写时自动区分大小写
rg -S 'httpServer'

# 按完整单词匹配
rg -w 'select'

# 整行匹配
rg -x 'TODO'

# 按字面量匹配，不走正则
rg -F 'user.name'

# 只显示命中的文本片段
rg -o '\berror\b'

# 显示列号
rg --column 'panic'

# 输出 Vim 可消费的格式
rg --vimgrep 'TODO|FIXME'
```

### 5.2 自动过滤：Ripgrep 的“聪明”到底做了什么？

默认递归搜索目录时，Ripgrep 会自动处理：

- `.gitignore` 规则；
- `.ignore` 规则；
- `.rgignore` 规则；
- 隐藏文件和目录；
- 二进制文件；
- 符号链接默认不跟随。

```bash
# 搜索隐藏文件
rg --hidden 'TODO'

# 关闭 ignore 规则
rg --no-ignore 'TODO'

# 跟随符号链接
rg --follow 'TODO'

# 快速排查“是不是被过滤掉了”
rg -uuu 'TODO'
```

`-u` 系列尤其值得记住：

- `-u`：不尊重 ignore 文件；
- `-uu`：额外包含隐藏文件和隐藏目录；
- `-uuu`：再额外把二进制文件也当作可搜索对象。

这常常是排查“为什么搜不到”的第一把锤子。

### 5.3 手动过滤：glob 与文件类型

自动过滤解决“常规情况”，手动过滤解决“临时意图”。

#### 5.3.1 用 glob 做临时筛选

```bash
# 只搜 TOML
rg clap -g '*.toml'

# 排除压缩后的产物
rg error -g '!*.min.js'

# 同时组合多个 glob
rg error -g '*.ts' -g '!*.d.ts'
```

注意：

- `-g` 的规则语义与 `.gitignore` 风格接近；
- 多个 glob 可以叠加；
- `!` 前缀表示排除。

#### 5.3.2 用文件类型做结构化筛选

```bash
# 只搜 Python
rg -tpy 'async def'

# 排除 JavaScript
rg -Tjs 'fetch'

# 搜多种类型
rg -tpy -ttoml 'timeout'

# 查看内置类型表
rg --type-list

# 临时添加自定义类型
rg --type-add 'web:*.{html,css,js}' -tweb 'title'
```

文件类型实际上是“类型名 → 若干 glob”的映射。它的优势不是功能更强，而是更容易复用和记忆。

### 5.4 输出控制：既适合人看，也适合机器处理

```bash
# JSON 事件流，适合脚本或编辑器集成
rg --json 'panic'

# 紧凑输出
rg --no-heading 'TODO'

# 只列出文件
rg -l 'TODO'

# 上下文
rg -B 2 -A 2 'panic'

# 稳定排序
rg --sort path 'panic'
```

这里要专门纠正一个常见误传：

- Ripgrep **支持 `--json`**；
- Ripgrep **不提供内建 `--csv` 输出格式**；
- 很多博客把别的工具的参数混进来了，这会误导读者。

### 5.5 替换功能：只替换输出，不替换文件

```bash
# 把输出里的 foo 替换成 bar
rg 'foo' -r 'bar'

# 使用捕获组
rg '(\d+)' -r '[$1]'
```

示例：

```bash
printf 'id=12\nid=34\n' | rg '(\d+)' -r '[$1]'
```

输出会是：

```text
id=[12]
id=[34]
```

但原文件并不会被修改。官方 FAQ 也明确说明：**Ripgrep 单独使用时不会改写文件**。

---

## §6 进阶用法

### 6.1 正则引擎：默认引擎与 PCRE2 到底怎么选？

Ripgrep 当前支持多种正则引擎选择方式，本地 `rg 15.1.0` 的帮助信息显示可以使用：

- `--engine=default`
- `--engine=pcre2`
- `--engine=auto`

最重要的结论只有三条：

1. **默认引擎通常最快，应该是首选。**
2. **需要 look-around 或 backreferences 时，改用 PCRE2。**
3. **`--auto-hybrid-regex` 仍可用，但已经标记为 deprecated，优先使用 `--engine=auto`。**

```bash
# 需要先行断言时，用 PCRE2
rg -P 'foo(?=bar)'

# 或者显式指定引擎
rg --engine pcre2 'foo(?=bar)'

# 自动选择引擎
rg --engine auto 'foo(?=bar)'
```

默认引擎为什么不支持 look-around 和 backreferences？官方 FAQ 给出的核心原因是：默认引擎基于**有限状态机**思路来保证**线性最坏时间复杂度**，而回溯引用不适合这个模型。

### 6.2 为什么开启 PCRE2 可能变慢？

官方 FAQ 专门解释过这件事，核心原因主要有两个：

1. **PCRE2 的语义更复杂。**
2. **Ripgrep 为了保证单行匹配与 Unicode 行为，在 PCRE2 模式下常常需要更保守的搜索策略。**

简化理解：

- 默认引擎更容易做激进优化；
- PCRE2 功能更强，但搜索路径往往更“重”；
- 你是在用**更强的表达能力**换一部分性能。

所以经验法则很简单：

- 平时默认引擎；
- 真的需要高级特性时再开 PCRE2；
- 不要“为了高级而高级”。

### 6.3 多行搜索：`-U` 的含义并不是“更强正则”

```bash
# 允许匹配跨行
rg -U '(?s)start.*end' notes.txt

# PCRE2 也可以和多行模式一起用
rg -P -U 'foo.*bar'
```

要点：

- `-U` / `--multiline` 的作用是**允许结果跨行**；
- 它不是“开启高级正则”的开关；
- 如果你写的是 `foo.*bar`，很多情况下还需要 `(?s)` 让 `.` 可以匹配换行。

### 6.4 文本编码：Ripgrep 并不是只会搜 UTF-8

官方 GUIDE 对编码策略说得很清楚：

- 默认会在自动模式下处理常见 ASCII 兼容文本；
- 会对 UTF-16 做 BOM 检测并转码后搜索；
- 也可以通过 `-E` / `--encoding` 手动指定编码；
- 还可以用 `-E none` 关闭编码相关逻辑，直接按原始字节搜索。

```bash
# 手动指定编码
rg -E utf-16 '配置项' windows-export.txt

# 关闭编码处理，直接搜字节语义
rg -E none '(?-u)\x00foo'
```

这也是 Ripgrep 在 Windows 和跨编码文本场景里体验很好的关键原因之一。

### 6.5 二进制文件：默认跳过，但不是“永远不搜”

官方 GUIDE 对二进制文件的说明比很多中文教程细得多：

- 递归遍历时，默认会尽量把二进制文件从搜索里排除；
- 它把“含有 NUL 字节”作为核心判据；
- 如果你显式把文件路径写到命令行上，行为会更接近“你既然明确点名了，那我就试着搜”；
- `-a` / `--text` 可以强制把文件按文本看待。

```bash
rg -a 'PNG' image-or-dump.bin
```

这条命令要谨慎使用，因为终端可能被不可打印内容污染。

### 6.6 搜压缩文件：能搜压缩流，但不会把归档当目录树展开

```bash
rg -z 'panic'
```

根据官方 FAQ 和帮助信息，`-z` / `--search-zip` 的关键边界是：

- 支持 gzip、bzip2、xz、lzma、lz4、Brotli、Zstd；
- 依赖系统里存在相应解压命令；
- 如果缺少外部程序，默认不一定直接报显眼错误，`--debug` 更容易看明白原因；
- 它搜索的是**解压后的文件内容**；
- 它**不会**把 `tar.gz` 之类的归档视为目录树递归展开。

### 6.7 预处理器：这是 Ripgrep 最强的扩展钩子之一

如果一个文件本身不是适合直接匹配的纯文本格式，可以用 `--pre` 先转成文本再搜。

```bash
rg --pre ./preprocess 'The Commentz-Walter algorithm' thesis.pdf
```

官方 GUIDE 给出的典型思路是：

- PDF 先交给 `pdftotext`；
- 某些压缩文件先交给 `pzstd`；
- 其他文件直接 `cat`；
- 再配合 `--pre-glob '*.pdf'` 限制预处理器只作用于特定文件。

这套机制非常重要，因为它说明 Ripgrep 的边界不是“只能搜它自己认识的文本”，而是“只要能先转成文本，它就能接着搜”。

### 6.8 配置文件：这一点最容易被写错

很多文章会说 Ripgrep 会按顺序自动读取：

- `./.ripgreprc`
- `~/.ripgreprc`
- 环境变量

这在当前官方 GUIDE 和 `rg --help` 语义里**并不成立**。

Ripgrep 的正确配置方式是：**通过 `RIPGREP_CONFIG_PATH` 环境变量显式指定配置文件路径**。

```bash
export RIPGREP_CONFIG_PATH="$HOME/.config/ripgrep/rc"
```

配置文件的规则也很简单：

- 每一行是一个参数；
- 以 `#` 开头的行会被忽略；
- 没有复杂转义语法；
- 带值参数要么写成 `--flag=value`，要么分两行写。

示例：

```ini
# $HOME/.config/ripgrep/rc
--smart-case
--hidden
--glob=!.git/*
--type-add
web:*.{html,css,js}
```

如果临时不想吃配置文件，可以用：

```bash
rg --no-config pattern
```

### 6.9 Man Page 与 Shell 补全

当前 15.1.0 的正确生成方式是：

```bash
# 生成 man page
rg --generate man > rg.1

# 生成 Bash 补全
rg --generate complete-bash > rg.bash

# 生成 Zsh 补全
rg --generate complete-zsh > _rg

# 生成 Fish 补全
rg --generate complete-fish > rg.fish
```

注意不是很多博客里写的 `--generate-completion bash`。当前帮助信息里的正式接口是 `--generate=KIND`。

---

## §7 配置详解

### 7.1 一个靠谱的个人配置思路

下面这个配置，适合日常代码搜索：

```ini
--smart-case
--hidden
--max-columns=200
--max-columns-preview
--colors=match:fg:yellow
--colors=match:style:bold
```

含义分别是：

- `--smart-case`：默认大小写更自然；
- `--hidden`：把 dotfile 也纳入搜索；
- `--max-columns`：别让超长行把终端刷爆；
- `--max-columns-preview`：超长行仍给你一个预览；
- `--colors`：统一你的匹配高亮风格。

### 7.2 团队配置要注意什么？

如果你把 Ripgrep 用在团队脚本、CI 或编辑器集成里，建议：

1. **显式写出关键参数，不要完全依赖个人配置文件。**
2. **对顺序敏感的输出显式加 `--sort path`。**
3. **对机器消费结果优先用 `--json`。**
4. **如果你怀疑环境污染，显式加 `--no-config`。**

### 7.3 常用配置项速查

| 配置项 | 说明 | 示例 |
| ------ | ------ | ------ |
| `--smart-case` | 大写则区分大小写 | `--smart-case` |
| `--hidden` | 搜索隐藏文件 | `--hidden` |
| `--glob` | 加入全局筛选 | `--glob=!.git/*` |
| `--type-add` | 添加自定义类型 | `--type-add` + `web:*.{html,css,js}` |
| `--max-count` | 每个文件最大匹配行数 | `--max-count=100` |
| `--max-depth` | 最大递归深度 | `--max-depth 5` |
| `--sort` | 排序方式 | `--sort path` |

### 7.4 Git 集成

```bash
# 在仓库内找某个 API
rg 'OldApiName'

# 只看工作树里哪些文件会被搜到
rg --files

# 排查为什么某个文件没被搜到
rg --files --debug
```

---

## §8 性能优化

### 8.1 官方基准里最常被引用的结论

官方 README 给出的代表性基准中，Ripgrep 在 Linux 内核源码搜索、单大文件搜索和高匹配率场景里都表现很强。例如最常被引用的一组数据是：

- Linux 内核搜索 `[A-Z]+_SUSPEND`：`rg` 约 `0.082s`
- 对照命令 `LC_ALL=C git grep -E -n -w ...`：约 `0.727s`
- Unicode 模式的 `git grep`：约 `2.670s`

需要注意两点：

1. **这不是“所有场景永远碾压”的承诺。**
2. **官方自己也明确提醒：单一 benchmark 永远不够。**

### 8.2 为什么 Ripgrep 通常很快？

结合 README、GUIDE 和 FAQ，可以把原因归纳为 5 类：

1. **默认引擎重视有限自动机与字面量优化**  
   这让它在常见模式下具备很强的吞吐能力。

2. **默认搜索模型就是“找少量命中，跳过大量无关内容”**  
   ignore 规则、隐藏文件过滤、二进制过滤，都会减少无效 IO。

3. **递归遍历默认并行**  
   这让它在现代多核机器上更容易吃满硬件能力。

4. **输出与搜索是一体化设计**  
   包括行号、高亮、上下文、JSON 等，都不是后补上去的。

5. **它会根据情况采用不同的底层搜索路径**  
   官方 GUIDE 提到 memory map、逐行搜索、rolling buffer 等策略差异，这会影响性能和某些边界行为。

### 8.3 什么时候会明显变慢？

官方 FAQ 对“为什么启用 PCRE2 变慢”解释得非常细。再加上 README 的性能悬崖示例，可以总结成下面几类：

- 模式几乎没有可利用的字面量；
- 匹配量极高，时间被输出吞掉；
- 开启 PCRE2；
- 开启多行搜索；
- 需要转码；
- 强行搜索大体量二进制数据；
- 为所有文件都启动预处理器。

### 8.4 真正有用的优化技巧

| 技巧 | 为什么有效 | 示例 |
| ------ | ------ | ------ |
| 优先用字面量或含明确字面量的模式 | 让引擎更容易做快速过滤 | `rg 'timeout exceeded'` |
| 缩小文件集合 | 先减少 IO 再谈 regex | `rg -tpy 'asyncio'` |
| 用 `-F` 搜纯文本 | 跳过正则解析与语义负担 | `rg -F 'config.toml'` |
| 用 `--sort path` 只在必要时开启 | 稳定顺序会牺牲并行 | `rg --sort path error` |
| 给预处理器加 `--pre-glob` | 少起无谓子进程 | `rg --pre ./pdf2txt --pre-glob '*.pdf' foo` |
| 排查时用 `--debug` | 找出忽略、解压、配置原因 | `rg --debug foo` |

### 8.5 性能诊断命令

```bash
# 显示搜索统计
rg --stats pattern

# 显示调试信息
rg --debug pattern

# 更底层的跟踪信息
rg --trace pattern
```

---

## §9 项目结构

### 9.1 仓库的高层组织

从公开仓库结构可以看到，Ripgrep 不是一个单文件工具，而是一个 **Rust workspace**。顶层除了 `README.md`、`GUIDE.md`、`FAQ.md`、`CHANGELOG.md` 之外，还能看到：

- `.cargo/`
- `.github/`
- `benchsuite/`
- `ci/`
- `crates/`
- `fuzz/`
- `pkg/`
- `tests/`
- `Cargo.toml`
- `build.rs`

这说明它既是一个终端工具，也是一个有明确分层、测试、打包和基准体系的工程。

### 9.2 关键 crate 分工

根据公开仓库索引与 crate 命名，可以把核心部分概括成下表：

| 组件 | 作用 |
| ------ | ------ |
| `crates/core` | 主程序入口与总控层 |
| `crates/cli` | 命令行相关能力 |
| `crates/matcher` | 匹配接口抽象 |
| `crates/searcher` | 搜索执行逻辑 |
| `crates/printer` | 输出格式化 |
| `crates/regex` | 默认正则引擎适配 |
| `crates/pcre2` | PCRE2 引擎适配 |
| `crates/ignore` | 目录遍历与 ignore 规则处理 |
| `crates/globset` | glob 模式匹配 |
| `crates/grep` | 对外整合搜索能力的 façade 风格 crate |

最值得你建立的理解是：**Ripgrep 的“快”不是只来自一个超强 regex engine，而是来自遍历、过滤、匹配、输出这四层协同优化。**

### 9.3 一次搜索的大致执行流水线

把 `rg pattern path` 拆开看，大致可以理解为：

1. 解析 CLI 参数；
2. 合并环境配置；
3. 选择正则引擎；
4. 构建遍历器与 ignore 规则；
5. 找出要搜索的文件集合；
6. 对文件执行搜索；
7. 把命中结果交给 printer；
8. 输出标准文本、JSON 或其他格式；
9. 根据是否命中、是否报错决定退出码。

这个流水线解释了两个经常被忽略的事实：

- 文件发现本身就是性能关键路径；
- 输出策略本身也会显著影响性能和行为。

### 9.4 为什么这个架构值得开发者关注？

因为它体现了一个很成熟的 CLI 工程设计：

- **遍历与过滤** 独立成模块；
- **正则引擎** 通过抽象接口切换；
- **输出** 不是散落在逻辑各处，而是集中管理；
- **CLI 只是装配层，不是所有逻辑都塞在 main 里**。

如果你正在设计自己的代码搜索、日志搜索、文本扫描类工具，这种分层很值得学习。

---

## §10 从源码构建与开发扩展

### 10.1 从源码构建

```bash
git clone https://github.com/BurntSushi/ripgrep
cd ripgrep
cargo build --release
./target/release/rg --version
```

如果你要启用 PCRE2 feature：

```bash
cargo build --release --features 'pcre2'
```

运行测试：

```bash
cargo test
```

### 10.2 哪些扩展不需要改源码？

很多“扩展 Ripgrep”的需求，其实不需要 fork 项目：

1. **新增文件类型**  
   用 `--type-add` 或配置文件即可。

2. **搜索 PDF、特定压缩流、私有格式**  
   用 `--pre` / `--pre-glob` 即可。

3. **定制颜色和默认行为**  
   用配置文件即可。

4. **接入编辑器或脚本**  
   用 `--json`、`--vimgrep` 即可。

这说明 Ripgrep 的扩展策略并不是“让所有人都改内核”，而是优先把常见扩展点做成接口。

### 10.3 真要改源码时，该从哪里理解系统？

一个比较实用的阅读顺序是：

1. 先看 `README.md` 和 `GUIDE.md`，确认产品语义；
2. 再看 `FAQ.md`，理解边界与性能取舍；
3. 然后看 `crates/core`，把主流程串起来；
4. 再分别读 `ignore`、`searcher`、`printer`、`regex` / `pcre2`；
5. 最后回到 `tests/` 和 `benchsuite/` 理解回归保障。

### 10.4 扩展时的几个关键原则

- 不要轻易破坏“默认就适合代码搜索”的产品哲学；
- 不要把少数高级能力变成所有用户的默认性能负担；
- 不要忽视输出层，因为输出语义会直接影响集成生态；
- 不要想当然地照搬 GNU grep 语义，Ripgrep 本来就不是 POSIX grep。

---

## §11 典型使用场景

### 11.1 代码仓库全局搜索

```bash
rg -tpy 'async def|await '
```

适合：

- 找函数定义；
- 找调用点；
- 找配置项；
- 做局部重构前的影响面扫描。

### 11.2 日志排障

```bash
rg -n -C 2 'timeout|refused|panic' logs/
```

如果日志目录里有很多被忽略或隐藏的文件：

```bash
rg -uuu -n -C 2 'timeout|refused|panic' logs/
```

### 11.3 配置审计

```bash
rg -tjson -tyaml -ttoml 'token|secret|password'
```

### 11.4 搜 Windows / UTF-16 文本

```bash
rg -E utf-16 '错误'
```

### 11.5 搜压缩文件

```bash
rg -z 'Exception'
```

### 11.6 搜 PDF 或其他需要预处理的格式

```bash
rg --pre ./pre-pdf --pre-glob '*.pdf' 'finite automata'
```

### 11.7 与其他工具管道协作

```bash
rg --json 'panic'
```

这个输出非常适合被：

- 编辑器；
- 终端 TUI；
- 代码索引脚本；
- 自己写的小工具；

进一步消费。

---

## §12 常见误区与事实纠正

### 12.1 误区一：`-r` 表示递归

错误。

- Ripgrep 默认就递归；
- `-r` 表示 `--replace`。

### 12.2 误区二：Ripgrep 会自动读取 `~/.ripgreprc`

至少在当前官方 GUIDE 与 15.1.0 帮助信息语义下，这样说并不准确。

正确说法是：

- 通过 `RIPGREP_CONFIG_PATH` 显式指定配置文件；
- `--no-config` 可以禁用该配置。

### 12.3 误区三：`-z` 能搜所有压缩包

错误。

它针对的是**压缩文件内容**，不是把归档当目录树展开。

### 12.4 误区四：`-P` 一定可用

错误。

PCRE2 是否可用，取决于你的构建版本。官方 FAQ 也明确提醒：GitHub 发布的多数官方二进制通常会带上 PCRE2，但某些系统包不一定。

### 12.5 误区五：Ripgrep 可以直接做批量替换

错误。

Ripgrep 自身只负责搜索与输出替换预览，不会直接改文件。真要改文件，需要把结果交给 `sed`、`xargs`、`fastmod` 等其他工具。

### 12.6 误区六：Ripgrep 自带 `--csv`

错误。

当前官方帮助信息可确认有 `--json`、`--vimgrep` 等输出方式，但没有内建 `--csv` 选项。

### 12.7 误区七：`--auto-hybrid-regex` 是最新推荐写法

错误。

在 15.1.0 帮助信息里，它已经标为 deprecated，优先使用 `--engine=auto`。

---

## §13 一组真正实用的命令清单

### 13.1 精准搜字面量

```bash
rg -F 'panic: failed to load config'
```

### 13.2 只看命中的文件

```bash
rg -l 'TODO|FIXME'
```

### 13.3 排除某类噪音文件

```bash
rg error -g '!dist/**' -g '!*.min.js'
```

### 13.4 只搜索受支持文件类型

```bash
rg -tall 'license'
```

### 13.5 查被忽略原因

```bash
rg --debug foo
```

### 13.6 结果给编辑器消费

```bash
rg --json 'deprecated_api'
```

### 13.7 需要高级正则时再开 PCRE2

```bash
rg --engine pcre2 '(?<=user_id=)\d+'
```

### 13.8 限制搜索深度

```bash
rg --max-depth 3 'Dockerfile'
```

### 13.9 跟随符号链接

```bash
rg --follow 'shared-config'
```

### 13.10 先看哪些文件会被搜索

```bash
rg --files
```

---

## §14 性能、原理与架构应该怎样整体理解？

如果把全文压缩成一张脑图，Ripgrep 的本质可以概括成下面这句话：

> 它不是“给 grep 加一点 Rust 优化”，而是围绕代码搜索场景，重新组织了遍历、过滤、匹配、输出与扩展接口的一整套系统。

拆开来看：

- **产品层**：默认就递归、默认就懂 ignore、默认就有 Unicode 体验；
- **算法层**：默认引擎优先保证线性复杂度与可优化性；
- **工程层**：workspace + 多 crate 分层，把遍历、搜索、输出解耦；
- **扩展层**：配置文件、类型系统、预处理器、JSON 输出，把“可定制”留给用户；
- **边界层**：明确承认自己不是 POSIX grep，也不是就地替换工具，更不是归档浏览器。

这也是为什么 Ripgrep 常常被认为不只是“一个很好用的命令”，而是 CLI 工具设计的一个优秀范例。

---

## §15 总结

### 15.1 如果你只记住 6 句话

1. `rg` 默认就递归，不需要 `-r`。
2. 默认会尊重 ignore、跳过隐藏和二进制。
3. 默认引擎通常最快，PCRE2 只在需要时开启。
4. `-r` 只改输出，不改文件。
5. 配置文件通过 `RIPGREP_CONFIG_PATH` 显式指定。
6. `--pre`、`--type-add`、`--json` 是最值得掌握的扩展接口。

### 15.2 推荐学习路径

如果你想把 Ripgrep 学扎实，建议按这个顺序：

1. 先熟悉基础搜索、过滤、类型、上下文；
2. 再理解 `-u` / `-uu` / `-uuu`；
3. 再掌握 `-F`、`-w`、`-x`、`--sort path`；
4. 然后学 `--engine pcre2`、`-U`、`-E`、`-z`、`--pre`；
5. 最后再看源码分层和性能 FAQ。

### 15.3 官方资料入口

- README：项目定位、基准、快速示例；
- GUIDE：详细使用指南与很多边界行为；
- FAQ：PCRE2、配置、排序、替换、压缩文件、多行等问题；
- CHANGELOG / Releases：版本变化；
- `rg --help`：最权威的当前参数真相。

---

*文档版本 2.0｜撰写日期：2026-03-31｜依据：Ripgrep 官方 README、GUIDE、FAQ、CHANGELOG 与本地 `rg 15.1.0` 帮助信息整理。*
