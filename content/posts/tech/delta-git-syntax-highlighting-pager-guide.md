---
title: "Delta：让 git diff 在终端里也好看"
date: "2026-04-12T02:31:39+08:00"
lastmod: "2026-09-29T12:00:00+08:00"
slug: delta-git-syntax-highlighting-pager-guide
github_repo: "dandavison/delta"
source_key: "gh:dandavison/delta"
description: "Delta 是 Rust 编写的语法高亮分页器，在 git、diff、grep、blame 的输出和终端之间插入一层可配置的渲染：语法高亮、词级标色、双栏对比、行号导航、超链接跳编辑器。本文讲清它的管线位置、各功能的真实边界与采用建议。"
draft: false
categories: ["技术笔记"]
tags: ["Git", "Rust", "终端"]
---

git 的 diff 输出是给程序读的，开发者却每天盯着它看。Delta（Rust 编写，MIT 协议）在 git 和终端之间插了一层可配置的渲染：语法高亮、词级标色、双栏对比、行号、文件间跳转。它不改 git 的任何行为，只在结果上屏之前接管显示。这篇拆解讲清它的管线位置、每个功能的真实边界，以及什么情况下不必用它。

## 一、管线位置：git → delta → less

配置生效后，`git diff` 的输出走这条链路：

```text
git / diff / grep / blame 的输出
        │  stdout 是终端时，git 自动调用 pager
        ▼
     delta 渲染（高亮、词级标色、行号、双栏）
        │
        ▼
     less 分页（默认 less -R）──▶ 终端
```

这条链路里有两个容易被忽略的事实。

**git 只在 stdout 是终端时才调用 pager。** `git diff | grep foo` 这样接管道，delta 根本不会被调用，下游拿到的就是 git 原始输出。想让管道里的命令也拿到渲染结果，得手动接进去：`git diff | delta | …`。反过来说，脚本和 CI 里不用担心 delta 突然改写输出。

**delta 自己不做分页。** 它渲染完就把结果转交给真正的 pager，默认 `less -R`。你按下的 j/k、空格、q 都发生在 less 里；`navigate = true` 激活的 n / N 跳转，停靠点由 `--navigate-regex` 定义的规则决定。

语法高亮引擎是 syntect，bat 用的同一个库。delta 用户不需要安装 bat，但两边共享同一批语法主题；主题名也可以通过 `BAT_THEME` 环境变量传给 delta，想和 bat 保持一致时有用。

## 二、安装与快速配置

### 各平台安装

包管理器里的包名大多是 git-delta，装出来的可执行文件叫 delta。

| 平台 | 命令 |
|------|------|
| macOS | `brew install git-delta` |
| Debian / Ubuntu | `sudo apt install git-delta`（官方仓库已收录 0.19.2；更旧的系统从 [Releases](https://github.com/dandavison/delta/releases) 下载 .deb 后 `sudo dpkg -i`） |
| Fedora | `sudo dnf install git-delta` |
| Arch Linux | `sudo pacman -S git-delta` |
| Windows (Scoop) | `scoop install delta` |
| Windows (Winget) | `winget install dandavison.delta` |
| Nix | `nix-env -iA nixpkgs.delta` |
| 源码 | `cargo install git-delta` |

装完跑 `delta --version` 确认可执行文件在 PATH 里。

截至 2026 年 9 月的仓库数据：Stars 32,377，Forks 584，贡献者 156，最新版 0.19.2（2026-03-28 发布）。本文配置均按 0.19.x 核对；升级后某项失效，先跑 `delta -h`（短帮助）或 `delta --help`（完整手册）确认当前版本的写法。

### 最小可用配置

官方 README 给的五条配置就是最佳起点：

```ini
[core]
    pager = delta

[interactive]
    diffFilter = delta --color-only

[delta]
    navigate = true    # n / N 在文件之间跳转
    dark = true        # 或 light = true；两者都不写则自动检测

[merge]
    conflictStyle = zdiff3
```

五行各管一件事：

- `core.pager`：git 所有翻页输出都经过 delta。
- `interactive.diffFilter`：`git add -p` 这类交互界面也拿到 delta 的着色，`--color-only` 表示只上色、不改排版。
- `navigate`：激活 n / N 跳转键。
- `dark`：默认配色按亮暗背景分两套；自动检测在 lazygit、zellij 这类环境里会失效，显式指定最稳。
- `merge.conflictStyle = zdiff3`：这是 Git 的配置项，不是 delta 的。zdiff3 让冲突块带上共同祖先的内容，delta 对这种格式有专门渲染（见「合并冲突」一节）。

不想改文件，等效的命令行写法：

```bash
git config --global core.pager delta
git config --global interactive.diffFilter 'delta --color-only'
git config --global delta.navigate true
git config --global delta.dark true
git config --global merge.conflictStyle zdiff3
```

`core.pager` 是全局默认，`git log`、`git show` 会自动走它。想按子命令精细控制（blame 的高亮和超链接值得单独指），用 `[pager]` 段：

```ini
[pager]
    log = delta
    show = delta
    diff = delta
    blame = delta
```

临时绕开 delta 看一次原始输出：

```bash
git --no-pager diff      # 不分页，直接输出原始 diff
GIT_PAGER=less git diff  # 这一次用 less
```

`GIT_PAGER` 要么不设置，要么设为 delta——长期把它指到别的 pager，等于绕开 delta。

## 三、一次 diff 在 delta 里的流转

配置生效后敲 `git diff`，会经过五步：

1. git 检查 stdout 是不是终端。是，就把原始 diff 交给 `core.pager` 指定的 delta。
2. delta 按 git 的 hunk（以 `@@` 开头的变更块）语法解析输入，从文件路径后缀推断语言，交给 syntect 做语法高亮。
3. 对删除行、新增行做配对：按 Levenshtein 距离推断两行是否「同源」，阈值由 `--max-line-distance` 控制，默认 0.6。同源的行内再算出具体哪些词变了。
4. 按配置组装版面：行号、边框、双栏、主题色。
5. 结果转交 less 显示，键盘交互发生在 less 里。

整条链路里，git 负责算 diff，delta 只负责把结果变可读，less 负责滚动。三层各干一件事。这也解释了 delta 的配置为什么会同时出现 git 的配置键（`merge.conflictStyle`）和自己的配置键（`delta.*`）——前者的输出格式影响 delta 怎么读，后者管 delta 怎么画。

## 四、读 diff 的核心功能

### 4.1 语法高亮

语言靠文件后缀识别，识别不出时回退到 `--default-language`（默认 txt）。行内高亮默认截断在 400 字符（`--max-syntax-highlighting-length`）——超长行（比如压缩过的 .js）全量高亮会明显变慢，这个截断是护栏。只想要 diff 配色、不要语法色，用 `--syntax-theme=none`。

### 4.2 词级标色

这是 delta 和原生 git 差距最直观的一处。改函数里的一个常量，git 把整行标红再标绿；delta 先配对删除行和新增行，行内再标出真正变化的词。配对的宽松度就是上文流转过程里提到的 `max-line-distance`：值越小越严格，默认 0.6。

### 4.3 Side-by-side 双栏

```ini
[delta]
    side-by-side = true
```

左右两栏都有语法高亮，长行自动换行，行号默认打开。栏宽取当前终端宽度；要固定宽度用 `--width`（git config 里是 `delta.width`，或环境变量 `COLUMNS`）。

### 4.4 行号

```ini
[delta]
    line-numbers = true
```

删除、未变、新增三类的行号样式分开控制（`line-numbers-minus-style` / `line-numbers-zero-style` / `line-numbers-plus-style`），左右两列的格式用 `line-numbers-left-format` / `line-numbers-right-format` 调。

### 4.5 导航

n 下一个文件，N 上一个；`git log -p` 里同样有效，会停在 commit 边界。停靠点可以用 `--navigate-regex` 重新定义。

### 4.6 合并冲突

前提是 `merge.conflictStyle = zdiff3`：这样冲突块里有三方内容——ours、theirs、共同祖先。delta 把它渲染成两个 diff：祖先到 ours、祖先到 theirs，比原始的三行 `<<<<<<<` 标记直观得多。冲突的起始/结束符号和两侧标题的样式可以分别调整（`merge-conflict-begin-symbol`、`merge-conflict-ours-diff-header-style`、`merge-conflict-theirs-diff-header-style` 等）。

### 4.7 blame

```bash
git blame main.rs
```

`pager.blame` 指到 delta 后，blame 输出获得语法高亮；hyperlinks 打开时 commit 哈希变成托管平台的链接（支持 GitHub、GitLab、SourceHut、Codeberg），点开就是提交页。

## 五、grep 输出的着色与跳转

delta 能给 rg、git grep、grep 的输出上色。rg 官方推荐的接法是 `--json`：

```bash
rg --json "pattern" | delta
```

理由写在手册里：`--json` 是结构化输出，没有解析歧义；git grep 和 grep 的文本格式总有边角情况。git grep 的 `-p` / `-W` 会把命中位置的函数上下文一起输出，delta 对这种格式有专门处理。

hyperlinks 打开后，grep 结果里的行号是可点击链接——配合「文件与行号链接」一节的格式，从搜索结果直接跳进编辑器的对应行。

rg 自己的分页也可以交给 delta：在 `RIPGREP_CONFIG_PATH` 指向的配置文件里写一行 `--pager=delta`。注意 rg 的配置文件只接受命令行选项，不能写管道。

## 六、超链接：从终端跳回编辑器

```ini
[delta]
    hyperlinks = true
```

三个前提，缺一个链接就退化为纯文本：

1. 终端模拟器支持 OSC 8（在文本里嵌超链接的终端转义序列标准）。
2. less ≥ 581 且带 `-R` 参数。老版本 less 用 `-r` 也能渲染，但会弄坏 `--navigate`。
3. tmux 用户需要 dandavison 维护的补丁版 tmux。

### commit 链接

开启后 commit 哈希自动链到托管平台。自建 Git 服务可以用模板覆盖：

```ini
[delta]
    hyperlinks-commit-link-format = "https://git.example.com/team/repo/commit/{commit}"
```

`{commit}` 会被替换成完整哈希。

### 文件与行号链接

这是超链接最实用的用法：在 diff 里点行号，编辑器直接打开对应文件的对应行。

```ini
[delta]
    hyperlinks = true
    hyperlinks-file-link-format = "vscode://file/{path}:{line}"
    # JetBrains 系：
    # hyperlinks-file-link-format = "idea://open?file={path}&line={line}"
```

三个占位符：`{path}` 是绝对路径，`{line}` 是行号，`{host}` 是 delta 所在主机名。默认值是一个只含文件名的 file URI，交给终端或操作系统自行处理。

VSCode、JetBrains 全家桶、Zed 都有自己的 URL 协议，直接用。编辑器没有协议的话，手册给了两条路：起一个本地 HTTP 服务接收跳转请求再拉起编辑器（手册附了 Python 起步代码）；或者给操作系统注册自定义协议，[dandavison/open-in-editor](https://github.com/dandavison/open-in-editor) 是个可以参考的实现。

## 七、主题系统：两层概念

delta 文档里 "theme" 有两层意思，混起来就会配错。

**第一层：syntax-theme，语法高亮配色。** 就是 bat 内置的那批主题，两边同一套。看实际效果用 `delta --show-syntax-themes --dark`（或 `--light`），它拿示例 diff 逐个主题演示；只要名单用 `--list-syntax-themes`。

```ini
[delta]
    syntax-theme = Monokai Extended
```

也在用 bat 的话注意一点：如果跑 `bat cache --build` 装过自定义语法或主题，delta 能自动识别它们，但 bat 的版本要和 delta 构建时锁定的版本一致（见 delta 仓库 Cargo.toml），错配会触发已知的内存错误（issue #1712）。

**第二层：delta 主题，一个命名 feature。** 打包背景色、边框、行号样式等一整组设置。delta 没有叫 theme 的配置键，选主题走 features。官方仓库的 [themes.gitconfig](https://github.com/dandavison/delta/blob/main/themes.gitconfig) 收录了一批用户贡献的主题（每条合并 PR 基本都带效果图）。用法是先 include，再把主题名放进 features：

```ini
[include]
    path = /PATH/TO/delta/themes.gitconfig

[delta]
    features = collared-trogon
    side-by-side = true
```

`delta --show-themes` 同样拿示例 diff 演示这批主题。亮暗背景默认自动检测，检测失败（比如在 lazygit、zellij 里）就显式写 `dark = true` 或 `light = true`。

### feature：给一组设置起名字

任何 delta 配置都可以塞进 `[delta "名字"]` 段做成 feature，再用 `features` 键按顺序启用：

```ini
[delta]
    features = unobtrusive-line-numbers decorations

[delta "unobtrusive-line-numbers"]
    line-numbers = true
    line-numbers-minus-style = "#444444"
    line-numbers-zero-style = "#444444"
    line-numbers-plus-style = "#444444"
```

不想改配置文件、临时试一个：`export DELTA_FEATURES=+side-by-side`，加号表示在现有配置上追加；撤销追加用 `export DELTA_FEATURES=+`。

## 八、样式语言与装饰

所有 `*-style` 选项用同一套样式语言，写法和 git config 的 color.* 接近：前景色、背景色、属性按空格排列。属性有 bold、italic、ul（下划线）、ol（上划线）、box（画框），装饰类选项还接受 omit（不显示）：

```ini
[delta]
    file-style = bold yellow ul
    file-decoration-style = "#606018" overline
    hunk-header-style = file line-number syntax bold
    hunk-header-decoration-style = "#cfd6ff" ul
```

`hunk-header-style` 里有三个特殊属性值得单独记：写 `file` 才显示文件路径（颜色由 `hunk-header-file-style` 控制），写 `line-number` 才显示首个 hunk 的行号，`syntax` 表示沿用语法高亮色。可样式化的元素有 20 多个，完整清单在 `delta --help` 的 STYLES 一节。上面两个装饰色取自官方 themes.gitconfig 里的真实主题。

## 九、同类工具的边界与设计取舍

官方没有发布跨工具的基准测试——手册的对比章节只有截图，没有数字；网上流传的启动耗时之类，大多给不出可复现的测量方法。能负责任对比的只有能力：

| 工具 | 语法高亮 | 词级标色 | 双栏视图 | 跨文件导航 | 实现 |
|------|----------|----------|----------|------------|------|
| delta | ✅ | ✅ | ✅ | ✅ n / N | Rust |
| diff-so-fancy | ❌ | ✅ | ❌ | ❌ | Perl |
| diff-highlight | ❌ | ✅ | ❌ | ❌ | Perl（Git 自带） |
| git + less | ❌ | ❌ | ❌ | ❌ | — |

delta 拉开差距的地方不在颜色本身：语法高亮需要语言感知，diff-highlight 只认 diff 语法；导航、行号、双栏、冲突重排、blame 超链接，则是一次性过滤器不会做的工作流能力。代价也在同一边——语法分析和行配对都是计算，超大 diff 的首次渲染会慢于原生 git，行内高亮 400 字符截断就是为此设的护栏。

给其他工具喂带色的局部输出时，走 `delta --color-only`：只上色，不改排版，分页职责留给 delta 本身。

## 十、怎么选

- 每天在终端里看 diff、做 review：直接配上。一次设置，git / diff / grep / blame 全部接管，长期收益最大。
- 只想要词级标色、不引入任何依赖：git 自带的 contrib/diff-highlight 够用，把 `pager.diff` 指过去即可。
- 终端不支持真彩色、less 版本太老：delta 的体验会打折扣，先修环境再上。
- 主要在 IDE 里看 diff：IDE 自带的 diff 视图更合适，delta 解决的是终端里的阅读问题。

## 十一、常见问题排查

**diff 没有高亮？**
按顺序查三处：`git config --get core.pager` 是否指向 delta；终端是否支持 24 位色（缺了就设 `COLORTERM=truecolor`）；当前命令是不是在管道里——管道里 git 根本不会调用 delta。

**side-by-side 栏宽不对？**
栏宽默认向终端询问，非交互环境下显式指定：`--width` 或 `COLUMNS` 环境变量。仍异常先回单栏：`git config --global delta.side-by-side false`。

**亮暗背景检测错了？**
显式指定：`git config --global delta.light true`（暗色用 `delta.dark`）。lazygit、zellij 这类环境里必须显式。

**配置改乱了想恢复默认？**
`git config --global --remove-section delta` 删掉整个 delta 段，回到 git 默认输出，再重新贴配置。

**Windows 下分页行为异常？**
Windows 附带的 less 版本经常是坏的。手册的建议：自己装一份 less，或用 Git for Windows 自带的那份。

## 参考出处与延伸阅读

- [delta 用户手册](https://dandavison.github.io/delta/)：本文所有配置项与行为描述的主要来源，grep、超链接、主题、安装等章节与源码同步维护。
- [dandavison/delta](https://github.com/dandavison/delta)：仓库与 README。仓库数据（Stars 32,377、Forks 584、贡献者 156、v0.19.2）由 GitHub API 于 2026-09-29 核实。
- [themes.gitconfig](https://github.com/dandavison/delta/blob/main/themes.gitconfig)：官方主题合集，§7、§8 的配色示例取自这里。
- [安装文档](https://dandavison.github.io/delta/installation.html)与 [repology: git-delta](https://repology.org/project/git-delta/versions)：各平台包名与收录状态。
- [dandavison/open-in-editor](https://github.com/dandavison/open-in-editor)：行号跳编辑器的自定义协议参考实现。
- [终端超链接规范（OSC 8）](https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda)：§6 前提条件的依据。
