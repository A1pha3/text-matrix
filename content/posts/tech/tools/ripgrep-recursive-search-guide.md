---
title: "Ripgrep 完全指南：从入门到原理、架构与扩展"
slug: "ripgrep-recursive-search-guide"
github_repo: "BurntSushi/ripgrep"
source_key: "gh:BurntSushi/ripgrep"
aliases:
  - /posts/tech/ripgrep-recursive-search-guide/
date: "2026-03-31T23:14:00+08:00"
categories: ["技术笔记"]
tags: ["Rust", "ripgrep", "命令行工具"]
description: "基于 Ripgrep 官方 README、GUIDE、FAQ、CHANGELOG 与 15.1.0 帮助信息整理，系统讲解 rg 的默认行为、性能原理、工程架构、扩展方式与常见误区。"
---

# Ripgrep 完全指南：从入门到原理、架构与扩展

## 学习目标

读完本文，你能够：

- 说清 Ripgrep 的定位：它默认做什么、不做什么、边界在哪；
- 从安装一路用到多行搜索、编码处理、压缩文件、预处理器和 PCRE2；
- 解释它为什么快，以及哪些操作会让它变慢；
- 看懂仓库的 crate 分层，知道二次开发该从哪里读起；
- 避开文档和中文教程里流传最广的几个错误说法。

---

## 项目概述

### 什么是 Ripgrep

**Ripgrep** 是一个命令行文本搜索工具，命令名是 `rg`。官方 README 的定义是一句话：

> ripgrep is a line-oriented search tool that recursively searches the current directory for a regex pattern.

落到日常使用上，几个默认值构成了它的第一印象：

- 默认递归搜索目录；
- 默认把输入当作按行匹配的任务；
- 默认尊重 `.gitignore`、`.ignore`、`.rgignore`；
- 默认跳过隐藏文件、隐藏目录和二进制文件；
- 围绕"在代码仓库里搜东西"这个场景做优化。

所以它最适合做的事是：在代码仓库里找函数、配置、错误信息；搜 UTF-8 / UTF-16 文本；按文件类型或忽略规则过滤；以及作为编辑器、脚本、终端工具链的搜索后端。

### 版本、许可证与资料依据

- 本文的行为描述基于 `ripgrep 15.1.0`（2025-10-22 发布，本地验证 `features:+pcre2`）；
- 上游最新版本是 `15.2.0`（2026-07-15 发布）：修复了多处跨目录搜索时的 gitignore 匹配 bug，改进了超大语料下的目录遍历耗时（issue #3293），并开始尊重 `GIT_CONFIG_GLOBAL` 与 `GIT_CONFIG_SYSTEM` 环境变量。本文的命令与结论在 15.2.0 上同样成立；
- 许可证为 **MIT 或 Unlicense 双许可证**，仓库顶层的 `COPYING`、`LICENSE-MIT`、`UNLICENSE` 三个文件与之对应；
- 关键信息（性能数据、默认行为、配置方式、Shell 补全、PCRE2、压缩文件、编码处理）只取自官方 README、GUIDE、FAQ、CHANGELOG 与本地 `rg --help`，不采用二手说法。

---

## 先建立正确的心智模型

### Ripgrep 不只是"更快的 grep"

第一次用 `rg`，多数人的感受是命令更短、搜得更快、输出更好看。这些都对，但只是结果。它的设计重心在三个地方：

1. **代码仓库搜索是默认任务。** 忽略规则、文件类型、并行遍历、输出可读性，优先级都是按这个任务排的。
2. **Unicode 是默认能力，不是额外负担。** 中文、日文、emoji 直接搜，不用额外配置——这一点和不少传统工具的体验不同。
3. **常见的事默认做对。** 默认递归、默认跳过二进制、默认尊重 ignore 规则，都是这条产品决定的直接体现。

### 真正要记住的四条默认行为

初学者踩的坑大多不在正则，而在默认行为。记住下面四条，能解释大部分"为什么搜不到"：

1. **没写路径时，默认搜当前目录。**
2. **遇到目录时，默认递归。**
3. **默认尊重 `.gitignore`、`.ignore`、`.rgignore`。**
4. **默认跳过隐藏文件和二进制文件。**

其中第 3、4 条最容易被误判成"Ripgrep 漏结果了"。多数时候不是漏，而是它在替你做筛选。

### 它适合什么，不适合什么

适合：搜代码仓库、搜大量文本文件、搜 UTF-8 / UTF-16 内容、嵌进脚本和编辑器流水线。

不适合硬替代的场景：

- 要求 **POSIX 兼容** 的 Shell 脚本；
- 需要完全复刻 GNU grep 行为的场景；
- **原地修改文件**；
- 把压缩包当目录树递归展开搜索；
- 既要求完全稳定的输出顺序，又不想牺牲并行性能。

---

## 快速上手

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

### 第一个例子

```bash
rg 'panic|error|fatal' .
```

这条命令体现了 Ripgrep 的典型风格：模式是正则；路径可省略也可显式写出；目录自动递归；输出文件名、行号和匹配行。

### 新手高频命令速查

| 目的 | 命令 |
| ------ | ------ |
| 搜当前目录 | `rg pattern` |
| 搜指定目录 | `rg pattern src` |
| 搜多个路径 | `rg pattern src tests README.md` |
| 显示行号 | `rg -n pattern` |
| 只列出命中文件 | `rg -l pattern` |
| 列出未命中的文件 | `rg --files-without-match pattern` |
| 统计命中行数 | `rg -c pattern` |
| 只输出匹配片段 | `rg -o pattern` |
| 显示前后文 | `rg -C 3 pattern` |
| 按文件名排序输出 | `rg --sort path pattern` |

### 从 grep 迁移时最容易犯的错

不少旧教程会写：

```bash
rg -r pattern
```

这是错的。在 Ripgrep 里，递归搜索本来就是默认行为，`-r` / `--replace` 的含义是**替换输出中的匹配文本**。想递归搜索，直接写：

```bash
rg pattern
```

想做输出替换，才写：

```bash
rg 'foo' -r 'bar'
```

而且这个替换**不会修改磁盘上的文件**，只改输出结果。

---

## 使用指南

### 基础搜索：八个高频开关

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

### 自动过滤：默认帮你做了什么

递归搜索目录时，Ripgrep 会自动处理：

- `.gitignore`、`.ignore`、`.rgignore` 规则；
- 隐藏文件和隐藏目录；
- 二进制文件；
- 符号链接默认不跟随。

```bash
# 搜索隐藏文件
rg --hidden 'TODO'

# 关闭 ignore 规则
rg --no-ignore 'TODO'

# 跟随符号链接
rg --follow 'TODO'

# 快速排查"是不是被过滤掉了"
rg -uuu 'TODO'
```

`-u` 系列值得单独记：

- `-u`：不尊重 ignore 文件；
- `-uu`：额外包含隐藏文件和隐藏目录；
- `-uuu`：再额外把二进制文件也当作可搜索对象。

排查"为什么搜不到"时，先跑一遍 `-uuu` 是最快的排除法。

### 手动过滤：glob 与文件类型

自动过滤解决常规情况，手动过滤解决临时意图。

#### 用 glob 做临时筛选

```bash
# 只搜 TOML
rg clap -g '*.toml'

# 排除压缩后的产物
rg error -g '!*.min.js'

# 同时组合多个 glob
rg error -g '*.ts' -g '!*.d.ts'
```

`-g` 的规则语义与 `.gitignore` 风格接近；多个 glob 可以叠加；`!` 前缀表示排除。

#### 用文件类型做结构化筛选

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

文件类型本质上是"类型名 → 若干 glob"的映射。它的优势不是功能更强，而是更容易复用和记忆。

### 输出控制：既给人看，也给机器读

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

顺带纠正一个常见误传：Ripgrep 支持 `--json`，但**不提供内建 `--csv` 输出**。一些博客把别的工具的参数混了进来，照抄会报错。

### 替换：只改输出，不改文件

```bash
# 把输出里的 foo 替换成 bar
rg 'foo' -r 'bar'

# 使用捕获组
rg '(\d+)' -r '[$1]'
```

验证一下：

```bash
printf 'id=12\nid=34\n' | rg '(\d+)' -r '[$1]'
```

输出是：

```text
id=[12]
id=[34]
```

原文件不会被修改。官方 FAQ 也明确说明：Ripgrep 单独使用时不会改写文件。

---

## 进阶用法

### 正则引擎：默认引擎与 PCRE2 怎么选

`rg 15.1.0` 的帮助信息里有三种引擎选择：

- `--engine=default`
- `--engine=pcre2`
- `--engine=auto`

结论可以压缩成三条：

1. **默认引擎通常最快，是首选。**
2. **需要 look-around（环视断言）或反向引用（backreferences）时，改用 PCRE2。**
3. **`--auto-hybrid-regex` 仍可用，但已标记为 deprecated，用 `--engine=auto` 替代。**

```bash
# 需要先行断言时，用 PCRE2
rg -P 'foo(?=bar)'

# 或者显式指定引擎
rg --engine pcre2 'foo(?=bar)'

# 自动选择引擎
rg --engine auto 'foo(?=bar)'
```

默认引擎为什么不支持 look-around 和反向引用？官方 FAQ 给出的原因是：默认引擎基于**有限状态机**，以此保证**线性最坏时间复杂度**，而反向引用不适合这个模型。

### PCRE2 为什么可能变慢

官方 FAQ 为这个问题写了很长一段解释，核心机制值得展开：

ripgrep 默认只报告单行内的匹配，所以它必须阻止模式跨行命中。默认引擎提供语法分析接口，能自动改写模式来满足这个约束——比如把 `foo\sbar` 中 `\s` 字符类里的 `\n` 剥掉。剥完之后，ripgrep 就可以在大块数据上连续搜索，省掉逐行切分、逐行起停的开销。

PCRE2 没有对等的分析 API，ripgrep 无法静态判断"这个模式会不会跨行"，只能退回逐行搜索的慢路径。再加上 PCRE2 本身是回溯（backtracking）实现，最坏复杂度高于默认引擎的有限自动机，差距会进一步放大。

经验法则：

- 平时用默认引擎；
- 需要 look-around、反向引用这些特性时再开 PCRE2；
- 不要为了高级而高级。

### 多行搜索：`-U` 不是"更强正则"

```bash
# 允许匹配跨行
rg -U '(?s)start.*end' notes.txt

# PCRE2 也可以和多行模式一起用
rg -P -U 'foo.*bar'
```

要点：

- `-U` / `--multiline` 的作用是**允许结果跨行**；
- 它不是"开启高级正则"的开关；
- 写 `foo.*bar` 这类模式时，通常还需要 `(?s)` 让 `.` 能匹配换行。

### 编码：不是只会搜 UTF-8

官方 GUIDE 对编码策略说得很清楚：

- 默认自动处理常见 ASCII 兼容文本；
- 对 UTF-16 做 BOM 检测，转码后搜索；
- 用 `-E` / `--encoding` 手动指定编码；
- 用 `-E none` 关闭编码逻辑，直接按原始字节搜索。

```bash
# 手动指定编码
rg -E utf-16 '配置项' windows-export.txt

# 关闭编码处理，直接搜字节语义
rg -E none '(?-u)\x00foo'
```

这是 Ripgrep 在 Windows 和跨编码文本场景里体验很好的一个关键原因。

### 二进制文件：默认跳过，但不是永远不搜

官方 GUIDE 对二进制文件的说明比很多中文教程细：

- 递归遍历时，默认尽量把二进制文件排除在搜索之外；
- 判据是文件里是否含有 NUL 字节；
- 如果显式把文件路径写到命令行上，行为会更接近"你既然点名了，那我就试着搜"；
- `-a` / `--text` 可以强制把文件按文本看待。

```bash
rg -a 'PNG' image-or-dump.bin
```

这条命令要谨慎使用，终端可能被不可打印内容污染。

### 搜压缩文件：搜压缩流，不展开归档

```bash
rg -z 'panic'
```

`-z` / `--search-zip` 的关键边界（来自官方帮助与 FAQ）：

- 支持 gzip、bzip2、xz、lzma、lz4、Brotli、Zstd；
- 依赖系统里存在相应的解压命令；
- 缺少外部程序时默认不报显眼错误，加 `--debug` 才容易看清原因；
- 搜索的是**解压后的文件内容**；
- **不会**把 `tar.gz` 之类的归档当目录树展开。

### 预处理器：最强的扩展钩子

如果一个文件不是适合直接匹配的纯文本格式，可以用 `--pre` 先转成文本再搜。

```bash
rg --pre ./preprocess 'The Commentz-Walter algorithm' thesis.pdf
```

官方 GUIDE 给出的典型思路：

- PDF 先交给 `pdftotext`；
- 某些压缩文件先交给 `pzstd`；
- 其他文件直接 `cat`；
- 再配合 `--pre-glob '*.pdf'`，让预处理器只作用于特定文件。

有了这个钩子，Ripgrep 的边界就从"只能搜它认识的文本"扩展成"只要能先转成文本，它就能接着搜"。

### 配置文件：最容易写错的一点

很多文章说 Ripgrep 会按顺序自动读取 `./.ripgreprc`、`~/.ripgreprc` 和环境变量。在当前官方 GUIDE 与 `rg --help` 的语义里，这个说法**不成立**。

正确的配置方式是：通过 `RIPGREP_CONFIG_PATH` 环境变量显式指定配置文件路径。

```bash
export RIPGREP_CONFIG_PATH="$HOME/.config/ripgrep/rc"
```

配置文件的规则：

- 每一行是一个参数；
- 以 `#` 开头的行被忽略；
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

临时不想加载配置文件时：

```bash
rg --no-config pattern
```

### Man Page 与 Shell 补全

15.1.0 的生成接口是 `--generate=KIND`：

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

注意不是一些博客里写的 `--generate-completion bash`，帮助信息里的正式接口就是 `--generate=KIND`。

---

## 配置详解

### 一个靠谱的个人配置

```ini
--smart-case
--hidden
--max-columns=200
--max-columns-preview
--colors=match:fg:yellow
--colors=match:style:bold
```

每一行的用意：

- `--smart-case`：默认大小写更自然；
- `--hidden`：把 dotfile 纳入搜索；
- `--max-columns`：不让超长行刷爆终端；
- `--max-columns-preview`：超长行仍给出预览；
- `--colors`：统一匹配高亮风格。

### 团队与 CI 要注意什么

把 Ripgrep 用进团队脚本、CI 或编辑器集成时，建议：

1. **显式写出关键参数**，不完全依赖个人配置文件；
2. **对顺序敏感的输出显式加 `--sort path`**；
3. **机器消费的结果优先用 `--json`**；
4. **怀疑环境被个人配置污染时，显式加 `--no-config`**。

### 常用配置项速查

| 配置项 | 说明 | 示例 |
| ------ | ------ | ------ |
| `--smart-case` | 大写则区分大小写 | `--smart-case` |
| `--hidden` | 搜索隐藏文件 | `--hidden` |
| `--glob` | 加入全局筛选 | `--glob=!.git/*` |
| `--type-add` | 添加自定义类型 | `--type-add` + `web:*.{html,css,js}` |
| `--max-count` | 每个文件最大匹配行数 | `--max-count=100` |
| `--max-depth` | 最大递归深度 | `--max-depth 5` |
| `--sort` | 排序方式 | `--sort path` |

### Git 集成

```bash
# 在仓库内找某个 API
rg 'OldApiName'

# 只看工作树里哪些文件会被搜到
rg --files

# 排查为什么某个文件没被搜到
rg --files --debug
```

### 退出码：脚本与 CI 里最该先确认的事实

`rg` 的退出码只有三档：

| 退出码 | 含义 |
| ------ | ------ |
| `0` | 至少命中一处，且没有出错 |
| `1` | 未命中，且没有出错 |
| `2` | 发生了错误（例如某个文件无法读取） |

两个容易写错的细节，都在 15.1.0 上实测确认过：

1. **`--no-messages` 不改变退出码。** 它只是不再打印错误信息。`rg hello file.txt missing-dir/ --no-messages` 明明输出了命中行，退出码仍是 `2`。
2. **真正的例外是 `-q/--quiet`。** man page 写明：出错时退出码固定为 2，除非用了 `-q/--quiet` 且找到了匹配——此时返回 `0`。

Shell 里的 `set -e`、`if rg ...; then` 和 CI 步骤判定都以这三档为准。`1` 的语义是"没找到"，不是"出错"；把 `rg foo || exit 1` 的含义想反是脚本里常见的坑。

配合脚本还有一对容易混淆的命令，注意区分"行"与"文件"：

- `rg -v 'foo' file`：输出文件中**不含** `foo` 的**行**；
- `rg --files-without-match 'foo'`：列出**整个文件都没有** `foo` 的**文件名**。

前者是行级取反，后者是文件级取反。man page 特别提醒过：`--files-without-match` 的结果可能与 `-l`（列出含命中的文件）对不上，写脚本时别混用，也别拿 `-v` 当"列出未命中文件"的替代品。

---

## 性能优化

### 官方基准里最常被引用的结论

官方 README 的代表性基准搜索整个 Linux 内核源码树（先跑 `make defconfig && make -j8`），测试机是 Intel i9-12900K（5.2 GHz）。以词边界方式搜 `[A-Z]+_SUSPEND`，结果如下：

| 工具 | 命令 | 耗时 |
| ------ | ------ | ------ |
| ripgrep (Unicode) | `rg -n -w '[A-Z]+_SUSPEND'` | **0.082s** |
| hypergrep | `hgrep -n -w '[A-Z]+_SUSPEND'` | 0.167s |
| git grep（PCRE2） | `git grep -P -n -w '[A-Z]+_SUSPEND'` | 0.273s |
| git grep（C locale） | `LC_ALL=C git grep -E -n -w '[A-Z]+_SUSPEND'` | 0.727s |
| git grep（Unicode） | `LC_ALL=en_US.UTF-8 git grep -E -n -w '[A-Z]+_SUSPEND'` | 2.670s |

同一份 README 里还有一组单大文件基准：在约 13GB 的 OpenSubtitles 语料上搜 `Sherlock [A-Z]\w+`，ripgrep 用时 1.042s，GNU egrep（Unicode locale）用时 6.577s。

读这组数字时注意两点：它不代表"所有场景永远领先"，README 自己就提醒单一 benchmark 永远不够，并链接了一篇更详细的博客对比；另外绝对值绑定在特定硬件上，横向倍率比绝对数字更有参考意义。

### 为什么 Ripgrep 通常很快

结合 README、GUIDE 和 FAQ，原因可以归为五类：

1. **默认引擎重视有限自动机与字面量优化**，常见模式下吞吐能力很强；
2. **默认搜索模型就是"找少量命中，跳过大量无关内容"**——ignore 规则、隐藏文件过滤、二进制过滤都在减少无效 IO；
3. **递归遍历默认并行**，现代多核机器上容易吃满硬件；
4. **输出与搜索是一体化设计**，行号、高亮、上下文、JSON 都不是后补的；
5. **底层搜索路径按情况切换**——官方 GUIDE 提到 memory map、逐行搜索、rolling buffer 的策略差异，这同时影响性能和一些边界行为。

上游也在持续改进这条路径：15.2.0 就专门优化了大语料下的目录遍历耗时（issue #3293）。

### 什么时候会明显变慢

官方 FAQ 对"启用 PCRE2 为什么变慢"解释得非常细，加上 README 里的性能悬崖示例，可以归成几类：

- 模式几乎没有可利用的字面量；
- 匹配量极高，时间被输出吞掉；
- 开启 PCRE2；
- 开启多行搜索；
- 需要转码；
- 强行搜索大体量二进制数据；
- 给所有文件都启动预处理器。

### 真正有用的优化技巧

| 技巧 | 为什么有效 | 示例 |
| ------ | ------ | ------ |
| 优先用字面量或含明确字面量的模式 | 让引擎更容易做快速过滤 | `rg 'timeout exceeded'` |
| 缩小文件集合 | 先减少 IO 再谈 regex | `rg -tpy 'asyncio'` |
| 用 `-F` 搜纯文本 | 跳过正则解析与语义负担 | `rg -F 'config.toml'` |
| `--sort path` 只在必要时开启 | 稳定顺序会牺牲并行 | `rg --sort path error` |
| 给预处理器加 `--pre-glob` | 少起无谓子进程 | `rg --pre ./pdf2txt --pre-glob '*.pdf' foo` |
| 排查时用 `--debug` | 找出忽略、解压、配置原因 | `rg --debug foo` |

### 性能诊断命令

```bash
# 显示搜索统计
rg --stats pattern

# 显示调试信息
rg --debug pattern

# 更底层的跟踪信息
rg --trace pattern
```

---

## 项目结构

### 仓库的高层组织

Ripgrep 不是一个单文件工具，而是一个 Rust workspace。顶层除了 `README.md`、`GUIDE.md`、`FAQ.md`、`CHANGELOG.md`，还能看到：

- `crates/`——全部核心实现；
- `benchsuite/`、`fuzz/`、`tests/`——基准、模糊测试与集成测试；
- `ci/`、`pkg/`——打包与发布；
- `HomebrewFormula/`、`scripts/`——发行与辅助脚本；
- `.cargo/`、`.github/`——构建配置与 CI 工作流；
- `COPYING`、`LICENSE-MIT`、`UNLICENSE`——双许可证声明；
- `Cargo.toml`、`build.rs`——workspace 定义与构建脚本。

终端工具之外，它同时是一个有明确分层、测试、打包和基准体系的工程。

### crate 分工

根据仓库 workspace 定义与各 crate 职责，核心部分可以概括为：

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
| `crates/index` | 实验性索引 crate（其 README 标注 WIP，以 optional 依赖存在，尚未成为正式功能） |
| `crates/grep` | 对外整合搜索能力的 façade 风格 crate |

理解到 crate 这一层就够用了：**Ripgrep 的"快"不来自某一个超强正则引擎，而来自遍历、过滤、匹配、输出四层的协同优化。**

### 一次搜索的执行流水线

把 `rg pattern path` 拆开看，大致经过这些步骤：

1. 解析 CLI 参数；
2. 合并环境配置；
3. 选择正则引擎；
4. 构建遍历器与 ignore 规则；
5. 找出要搜索的文件集合；
6. 对文件执行搜索；
7. 把命中结果交给 printer；
8. 输出标准文本、JSON 或其他格式；
9. 按是否命中、是否报错决定退出码。

这条流水线里有两个常被忽略的事实：文件发现本身就是性能关键路径；输出策略也会显著影响性能和行为。

### 这个架构值得看什么

它展示了一种成熟的 CLI 工程分层：遍历与过滤独立成模块；正则引擎通过抽象接口切换；输出集中管理而不是散落在逻辑各处；CLI 只是装配层，没有把所有逻辑塞进 main。设计代码搜索、日志扫描这类工具时，这套分层可以直接参考。

---

## 从源码构建与二次开发

### 从源码构建

```bash
git clone https://github.com/BurntSushi/ripgrep
cd ripgrep
cargo build --release
./target/release/rg --version
```

启用 PCRE2 feature：

```bash
cargo build --release --features 'pcre2'
```

运行测试：

```bash
cargo test
```

### 不改源码能做的扩展

很多"扩展 Ripgrep"的需求，其实不需要 fork 项目：

1. **新增文件类型**：用 `--type-add` 或配置文件；
2. **搜索 PDF、特定压缩流、私有格式**：用 `--pre` / `--pre-glob`；
3. **定制颜色和默认行为**：用配置文件；
4. **接入编辑器或脚本**：用 `--json`、`--vimgrep`。

常见的扩展点已经被做成了接口，改内核是最后的选择。

### 真要读源码时的顺序

1. 先看 `README.md` 和 `GUIDE.md`，确认产品语义；
2. 再看 `FAQ.md`，理解边界与性能取舍；
3. 然后看 `crates/core`，把主流程串起来；
4. 再分别读 `ignore`、`searcher`、`printer`、`regex` / `pcre2`；
5. 最后回到 `tests/` 和 `benchsuite/` 看回归保障。

### 改源码时的几条原则

- 别破坏"默认就适合代码搜索"的产品定位；
- 别把少数高级能力变成所有用户的默认性能负担；
- 别忽视输出层——输出语义直接影响集成生态；
- 别照搬 GNU grep 语义，Ripgrep 本来就不是 POSIX grep。

---

## 典型使用场景

### 代码仓库全局搜索

```bash
rg -tpy 'async def|await '
```

适合找函数定义、调用点、配置项，以及局部重构前的影响面扫描。

### 日志排障

```bash
rg -n -C 2 'timeout|refused|panic' logs/
```

如果日志目录里有很多被忽略或隐藏的文件：

```bash
rg -uuu -n -C 2 'timeout|refused|panic' logs/
```

### 配置审计

```bash
rg -tjson -tyaml -ttoml 'token|secret|password'
```

### 搜 Windows / UTF-16 文本

```bash
rg -E utf-16 '错误'
```

### 搜压缩文件

```bash
rg -z 'Exception'
```

### 搜 PDF 或其他需要预处理的格式

```bash
rg --pre ./pre-pdf --pre-glob '*.pdf' 'finite automata'
```

### 与其他工具管道协作

```bash
rg --json 'panic'
```

这个输出可以被编辑器、终端 TUI、代码索引脚本或你自己写的小工具直接消费。

---

## 常见误区与事实纠正

### 误区一：`-r` 表示递归

在 grep 里 `-r` 是递归，在 Ripgrep 里 `-r` 是 `--replace`，替换输出中的匹配文本。递归本来就是默认行为，直接 `rg pattern` 就是递归搜索。

### 误区二：Ripgrep 会自动读取 `~/.ripgreprc`

不少文章说 Ripgrep 会按 `./.ripgreprc`、`~/.ripgreprc`、环境变量的顺序自动加载配置。至少在当前官方 GUIDE 与 15.1.0 的帮助语义下，这个说法不成立：配置文件必须通过 `RIPGREP_CONFIG_PATH` 显式指定，`--no-config` 可以在单次调用里禁用。

### 误区三：`-z` 能搜所有压缩包

`-z` / `--search-zip` 处理的是压缩文件的内容流；`tar.gz` 这类归档不会被当成目录树展开。想在归档里搜，先解包。

### 误区四：`-P` 一定可用

`-P` / `--pcre2` 是否可用取决于编译选项。官方 FAQ 的说法是：GitHub 上发布的官方二进制多数带 PCRE2，发行版包管理器装的则不一定。没有 PCRE2 时会直接报错：

```text
PCRE2 is not available in this build of ripgrep
```

### 误区五：Ripgrep 可以直接做批量替换

Ripgrep 只负责搜索和输出层替换，不会改写磁盘文件。真要改文件，把结果交给 `sed`、`xargs`、`fastmod` 这类工具。

### 误区六：Ripgrep 自带 `--csv`

当前帮助信息里能确认的机器可读输出是 `--json` 和 `--vimgrep`，没有内建 `--csv` 选项。一些博客把其他工具的参数混了进来。

### 误区七：`--auto-hybrid-regex` 是推荐写法

15.1.0 的帮助信息已把它标为 DEPRECATED，并注明 "Use --engine instead"。同样的效果用 `--engine=auto`。

### 误区八：`-L` 表示"列出未命中的文件"

`-L` / `--follow` 的含义是跟随符号链接，默认不跟随。列出没有任何命中的文件要用 `--files-without-match`。顺带分清两个"取反"：`-v` 取反的是**行**，`--files-without-match` 取反的是**文件**。

---

## 实用命令清单

### 精准搜字面量

```bash
rg -F 'panic: failed to load config'
```

### 只看命中的文件

```bash
rg -l 'TODO|FIXME'
```

### 排除某类噪音文件

```bash
rg error -g '!dist/**' -g '!*.min.js'
```

### 只搜已知类型的文件

```bash
rg -t all 'license'
```

`all` 是 `--type` 的特殊值，等价于对 `--type-list` 里的每个类型各写一个 `--type`。注意它匹配的是"属于某个已知类型的文件"——没有扩展名的文件（比如一个叫 `my-shell-script` 的脚本）不属于任何类型，不会被 `-t all` 搜到。反过来，`--type-not all` 只搜不属于任何已知类型的文件，可以用来找类型系统没覆盖的文件。

### 查被忽略原因

```bash
rg --debug foo
```

### 结果给编辑器消费

```bash
rg --json 'deprecated_api'
```

### 需要高级正则时再开 PCRE2

```bash
rg --engine pcre2 '(?<=user_id=)\d+'
```

### 限制搜索深度

```bash
rg --max-depth 3 'Dockerfile'
```

### 跟随符号链接

```bash
rg --follow 'shared-config'
```

### 先看哪些文件会被搜索

```bash
rg --files
```

---

## 总结

把全文收拢成一句：Ripgrep 是围绕"在代码仓库里搜东西"这个具体任务，把遍历、过滤、匹配、输出和扩展接口重新组织了一遍的系统——"快"是这个组织的副产品。分层来看：产品层默认递归、默认懂 ignore、默认 Unicode 友好；算法层默认引擎以线性最坏复杂度和字面量优化为先；工程层用 workspace 把遍历、搜索、输出解耦成独立 crate；扩展层把配置文件、类型系统、预处理器、JSON 输出留在接口上；边界层则明确承认自己不是 POSIX grep，不是替换工具，也不是归档浏览器。

### 如果只记住七句话

1. `rg` 默认就递归，不需要 `-r`。
2. 默认尊重 ignore 规则、跳过隐藏和二进制文件。
3. 默认引擎通常最快，PCRE2 只在需要 look-around、反向引用时开启。
4. `-r` 只改输出，不改文件。
5. 配置文件用 `RIPGREP_CONFIG_PATH` 显式指定。
6. `--pre`、`--type-add`、`--json` 是最值得掌握的三个扩展接口。
7. 退出码 `0/1/2` 对应命中、未命中、出错；`-q` 且有命中时出错也返回 `0`；`-v` 取反行，`--files-without-match` 取反文件。

### 推荐学习路径

1. 先熟悉基础搜索、过滤、类型、上下文；
2. 再理解 `-u` / `-uu` / `-uuu`；
3. 再掌握 `-F`、`-w`、`-x`、`--sort path`；
4. 然后学 `--engine pcre2`、`-U`、`-E`、`-z`、`--pre`；
5. 最后看源码分层和性能 FAQ。

### 官方资料入口

- README：项目定位、基准、快速示例；
- GUIDE：详细使用指南与大量边界行为；
- FAQ：PCRE2、配置、排序、替换、压缩文件、多行等问题；
- CHANGELOG / Releases：版本变化；
- `rg --help`：最权威的当前参数真相。
