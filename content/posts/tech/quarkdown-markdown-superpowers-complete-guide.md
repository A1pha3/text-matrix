---
title: "Quarkdown：给 Markdown 装上计算能力，一份源文件编译出论文、幻灯片和知识库"
date: "2026-04-29T16:41:29+08:00"
slug: quarkdown-markdown-superpowers-complete-guide
github_repo: "iamgio/quarkdown"
description: "Quarkdown 是构建在 CommonMark 与 GFM 之上的 Markdown 超集，通过图灵完备的函数系统为文档引入计算能力，可把单一源文件编译成 HTML、PDF、Markdown 与纯文本。"
draft: false
categories: ["技术笔记"]
tags: ["Kotlin", "Markdown", "编译器", "排版", "知识库"]
---

写文档时你多半遇到过的场景：同一份内容要出网页、出 PDF，还要做演示文稿；文档里有表格、有公式，还想让读者动动手就运行一段代码。传统 Markdown 写什么就是什么，没有计算、没有变量、没有逻辑，这些需求往往被拆成三份工具来维护。Quarkdown 想用一套语法把这些收拢回一个源文件：你在文档里写函数、定义变量、做条件判断和循环，编译器负责算出结果并决定最终输出成哪一种形态。

## 一、它是什么

Quarkdown 是一个由 Kotlin 编写的 Markdown 超集与排版系统，口号是"Markdown with superpowers"。它从 CommonMark 和 GFM 出发，给 Markdown 加上了能在文档内部执行的函数系统，以及一套持续扩充的标准库，覆盖布局、I/O、数学、条件与循环。同一个 `.qd` 源文件可以编译成印刷级书籍、学术论文、知识库和交互式演示文稿四种形态。

它的关键不是"多几种输出格式"，而是让文档具备计算能力：文档不再是被动的静态文本，而是一个可以运行的程序。

### 核心数据

| 指标 | 数值 |
|------|------|
| Stars | 16.0k+ |
| 主语言 | Kotlin |
| 许可证 | GPL-3.0 |
| 首次发布 | 2024-01 |
| GitHub | [iamgio/quarkdown](https://github.com/iamgio/quarkdown) |

### 它和 Markdown、LaTeX 的关系

三者不是替代关系，而是摆在不同位置的工具。Markdown 简单但对版式和计算几乎无能为力；LaTeX 排版能力顶级，学习曲线陡、写起来冗长；Typst 平衡了语法与能力，但生态较新。Quarkdown 的选择是保留 Markdown 的简洁写作体验，把 LaTeX 那类需要的能力（公式、图表、分页排版）通过函数调用藏进标准库里，写作时你不用先学会一门完整排版语言。

## 二、核心概念

### 一份源，多种形态

文档类型由 `.doctype` 函数在源码内声明，编译时据此决定排版方式：

- `.doctype {plain}`：连续流，类似 Notion/Obsidian，适合静态站点与知识管理，这也是默认值
- `.doctype {paged}`：分页，适合论文、文章与书籍
- `.doctype {slides}`：幻灯片，适合交互式演示
- `.doctype {docs}`：文档站点，适合 wiki 与大型知识库

同一份源文件不必为不同用途各写一份，改这个函数即可切换输出目标。

### 函数调用：贯穿一切的核心

Quarkdown 的一切扩展都以函数调用为入口。一个调用以点号开头，参数放在花括号里，可以用位置传参，也可以命名（`name:{value}`）：

```
.somefunction {arg1} {arg2}
    Body argument
```

调用可以嵌套，也可以用 `::` 链式书写，把左侧的值当作右侧函数的第一个参数：

```
.multiply {.pow {3} to:{2}} by:{.pi}
```

函数调用不仅生成文字，还能直接参与计算。整段文档因此变成了一个可执行程序：写 Markdown，就是在写逻辑。

### 变量与自定义函数

变量用 `.var` 定义，赋值后能像无参函数一样反复引用：

```
.var {name} {Quarkdown}
Hello, **.name**!
```

自定义函数用 `.function`，参数列在函数体第一行；因为参数可以带默认标记，函数既能传值也能留空。函数没有 `return`——凡是执行到的语句都会成为输出的一部分：

```
.function {greet}
    to from:
    **Hello, .to** from .from!

.greet {world} from:{iamgio}
```

### 条件与循环

文档里可以写真正的控制流。`.if` 满足条件才输出其主体，`.ifnot` 取其反；`.foreach` 遍历一个序列，`.` 隐式指代当前项：

```
.foreach {1..5}
    n:
    .multiply {.n} by:{.n}
```

这些能力叠加起来，Quarkdown 就是一个写在文档内部的图灵完备脚本语言。

### 数学公式

Quarkdown 原生支持 TeX 数学公式，HTML 端由 MathJax 渲染。内联公式用单个 `$` 包裹，公式前后需要留白或处于行首尾：

```
Let $ \overline v = \frac {\Delta x} {\Delta t} $ be the **average velocity** of an object.
```

独立成块的公式可以直接放在段落里，多行公式则用三个 `$` 作为定界符：

```
$$$ f(x) = \begin{cases}
    0 & \text{if } x = 0 \\
    1 & \text{if } x \neq 0
\end{cases} $$$
```

## 三、输出能力

Quarkdown 的目标不是单一格式，而是一份源对接所有需要交付的产物：

| 目标 | 覆盖的文档类型 | 说明 |
|------|---------------|------|
| HTML | plain / paged / slides / docs | paged 走 paged.js，slides 走 reveal.js，docs 适合知识库与 wiki |
| PDF | 全部 | 依赖 Node.js、npm 与 Puppeteer 生成 |
| Markdown | GFM | 导出为通用的 Markdown |
| Plain text | — | 通用纯文本导出 |

把 HTML 定义为第一等目标，再在其上叠加 PDF 导出，是它区别于"各格式写一套渲染器"的关键：多数排版能力只要实现一次。

### 编译速度与实时预览

Quarkdown 原生支持低时延的实时预览：官方 wiki 有 100 多个子文档，编译只需约 2 秒。配合 CLI 的 `-p`（编译后自动刷新预览）和 `-w`（监听源码目录，文件变动即重编译），写作时能边写边看结果。

### 编辑器支持

- VS Code 官方扩展
- IntelliJ IDEA 插件（社区为非官方维护）

### 权限与代理友好

Quarkdown 默认限制了文档对系统资源的访问（权限系统），从设计上减少"文档即程序"这一特性带来的安全面。标准库之外，项目还内置了一个面向 coding agent 的 skill，让语言模型写 Quarkdown 时能遵循主管道而不用猜语法。这里需要区分两类概念：Quarkdown 的"函数"是文档排版与计算的抽象，与别的项目里"工具调用/Agent 函数"并非一回事。

## 四、安装与环境要求

安装前先确认机器上有 Java 运行时，因为编译工具链基于 JVM。PDF 导出额外需要 Node.js、npm 和 Puppeteer，仅做 HTML/文本输出时不需要。

### 方式一：官方安装脚本（Linux/macOS）

```bash
curl -fsSL https://raw.githubusercontent.com/quarkdown-labs/get-quarkdown/refs/heads/main/install.sh | sudo env "PATH=$PATH" bash
```

脚本会把程序装到 `/opt/quarkdown`，并在 `/usr/local/bin` 建立 `quarkdown` 快捷命令。若机器没有 Node.js，脚本会通过系统包管理器自动补装。

### 方式二：Homebrew（macOS/Linux）

```bash
brew install quarkdown-labs/quarkdown/quarkdown
```

### 方式三：Windows

PowerShell 安装脚本：

```powershell
irm https://raw.githubusercontent.com/quarkdown-labs/get-quarkdown/refs/heads/main/install.ps1 | iex
```

或用 Scoop：

```powershell
scoop bucket add quarkdown https://github.com/quarkdown-labs/scoop-quarkdown
scoop install quarkdown
```

### 方式四：手动安装

从 [latest release](https://github.com/iamgio/quarkdown/releases/latest) 下载 `quarkdown.zip` 解压，或用 `gradlew installDist` 从源码构建。若希望随处可用，把 `<install_dir>/bin` 加入 `PATH`。

安装完成后运行 `quarkdown --help` 验证命令可用。

## 五、快速上手

### 创建项目

`quarkdown create [directory]` 会启动交互式向导，自动生成带文档元数据（metadata）和初始内容的项目骨架。

### 写并编译第一份文档

新建一个源文件，比如 `hello.qd`：

```
.doctype {paged}
# 我的第一篇 Quarkdown 文档

这是一段普通文本。下面把公式写进标记里：

Let $ E = mc^2 $ be a start.

.function {greet}
    to from:
    **Hello, .to** from .from!

.greet {world} from:{iamgio}
```

编译并预览：

```bash
quarkdown c hello.qd
```

`quarkdown c FILE` 编译指定文件并把结果写到目标。若项目有多个源文件，命令行传入的必须是根文件，即负责 include 其他文件的那个入口文件。`quarkdown c hello.qd -p` 会在编译后自动打开预览，配合 `-w` 得到实时预览：

```bash
quarkdown c hello.qd -p -w
```

要输出 PDF，追加 `--pdf`：

```bash
quarkdown c hello.qd --pdf
```

想边读边试语法，可以用交互模式：

```bash
quarkdown repl
```

### 生成幻灯片和知识库

改变文档类型即可切换产物。想出一套幻灯片，把 `hello.qd` 开头改为 `.doctype {slides}`，再编译同一个文件；想建知识库，则用 `.doctype {docs}` 并把多个 `.qd` 文件通过 include 函数组织起来。同一个源，输出随你的声明而变。

## 六、完整示例

下面这组是可直接放进 `.qd` 文件验证的片段。

### 变量复用一段布局

变量可以存一整段布局内容，再在文档里反复调用：

```
.var {myrow}
    .row gap:{2cm}
        A
        B
        C

.container background:{teal} padding:{1cm}
    .myrow
```

### 函数复用与链式计算

```
.function {area}
    width height:
    .multiply {.width} by:{.height}

The area is **.area {4} {2}**.
```

链式写法把嵌套调用变成左到右的序列，读起来更像自然语言：

```
.pow {3} {2}::subtract {1}::sum {2}
```

等价于 `.sum {.subtract {.pow {3} {2}} {1}} {2}`，两者结果相同，前者可读性更好。

### 条件渲染

```
.let {.iseven {3}}
    condition:
    .if {.condition}
        3 is even!
    .ifnot {.condition}
        3 is odd!
```

### 循环生成序列

```
.row alignment:{spacearound}
    .foreach {1..5}
        n:
        .multiply {.n} by:{.n}
```

`.repeat {n}` 是 `.foreach {1..n}` 的缩写，遍历整数区间可省略 1 的起点。

## 七、适用场景与局限

### 适合的场景

- **技术博客与文档**：想在正文里嵌入可计算的内容、公式和图表
- **学术写作**：要 LaTeX 的公式与分页质量，但不想付出完整 LaTeX 学习成本
- **演示文稿**：不想切换工具，直接用 Markdown 出幻灯片
- **知识库**：内容经常要同步到站点、文档中心与演示，希望单源维护
- **数据报告**：定期报告里嵌动态图表，数字随数据源变化

### 与同类工具的取舍

和 Typst 相比，Quarkdown 保留了 Markdown 的书写感；和 AsciiDoc、MDX 相比，它把脚本能力内建而非依赖外部框架。代价是它的生态仍在早期，文档级插件与模板数量还不及 Pandoc、LaTeX 社区。

### 当前局限

- **JVM 依赖**：编译依赖 Java 运行时，安装脚本会自动处理，但纯前端项目会觉得偏重
- **PDF 依赖链**：PDF 导出需要 Node.js、npm 与 Puppeteer，不是开箱即得的单一二进制
- **生态规模小**：标准库可用但第三方扩展和模板远少于成熟排版工具
- **调试体验**：文档内函数出错时，错误信息可读性还有提升空间；函数虽强大，滥用会让文档难以维护

几句取舍上的建议：简单文档不必引入函数，纯静态内容用 Markdown 就好；只有出现重复内容、动态数值或要跨格式维护时，才值得把文档升级成 "文档即程序" 的写法。

## 八、排错与常见问题

**`quarkdown` 命令找不到**：确认安装路径的 `bin` 目录已加入 `PATH`；用安装脚本装过的话，检查 `/usr/local/bin/quarkdown` 是否存在。

**PDF 导出失败**：它依赖 Node.js、npm 与 Puppeteer，先确认三者已正确安装，再重新编译。仅做 HTML 或文本输出时不受影响。

**实时预览不刷新**：确认用了 `-p -w` 组合；`-w` 监听的是源目录，改动文件需落在监听范围内。

**多文件项目编译报错**：命令行传入的必须是根文件（include 其他文件的那一个），不是任意子文件。

**函数不生效、原样输出**：检查调用是否以点号开头、参数是否在花括号内；模块缩进至少要两个空格或一个 Tab，若缩进混入四空格会意外被当成代码块。

**依赖外部的数据或资源时打不开**：Quarkdown 默认限制文档进程对系统资源的访问权限，属预期行为；需要访问外部资源时按权限系统规则显式授权。

## 九、进阶与资源

想深入，可以从这几个方向走：

1. **把编译器当黑盒看**：先跑 `mock` 示例工程（`quarkdown c mock/main.qd -p`）感受各文档类型的排版差异，再定位到 `compiler/` 下的 lexer、parser、renderer 模块，理解一次编译里各阶段做了什么
2. **写自己的函数库**：用 `.function` 把重复的版式收成一条调用，体会"复用"在文档里的形态
3. **接入 CI**：用官方 setup 把编译放进 GitHub Actions，实现文档随源码自动构建发布
4. **对照脚本特性**：官方 wiki 对变量、条件、循环、链式调用都有独立页面，按需查阅

参考资料：

- GitHub 仓库：[iamgio/quarkdown](https://github.com/iamgio/quarkdown)
- 官方 Wiki：[quarkdown.com/wiki](https://quarkdown.com/wiki)
- 官方文档：[quarkdown.com/docs](https://quarkdown.com/docs)
- 安装脚本项目：[get-quarkdown](https://github.com/quarkdown-labs/get-quarkdown)