---
title: "Basalt：终端里的 Obsidian 阅读层，一个 Elm 架构的 ratatui 实战样本"
date: "2026-05-11T22:50:00+08:00"
lastmod: "2026-09-20T06:20:00+08:00"
slug: "basalt-rust-obsidian-tui-notes"
github_repo: "erikjuhani/basalt"
source_key: "gh:erikjuhani/basalt"
description: "从源码与官方文档拆解 erikjuhani/basalt：三个 crate 的分工与双许可证、Elm 单向数据流在 ratatui 上的落地、全量解析与有意收缩的渲染子集，以及一个更容易被忽略的问题——README 跟随 main，而 cargo install 装到的是 0.12.7，两者的能力清单并不重合。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "TUI", "Obsidian", "Markdown", "终端", "ratatui"]
hiddenFromHomePage: true
---

## 先说结论

Basalt 押的是「读」，不是「写」。

这个判断不是从功能清单里读出来的，是从它拒绝做什么读出来的：笔记的删除、移动、复制一概不实现，全文搜索没有，Graph View 和反向链接面板没有，内置编辑器挂着 experimental 标签且编辑态键位当前不允许自定义。仓库文档《Basalt》一节里作者交代了动机——他同时用 Neovim 和 Obsidian 官方客户端，知道 `obsidian.nvim` 对很多人已经够用，但他要的是不出终端就能看到图片、排版过的文字和笔记图谱。这个愿望和「在终端里写笔记」是两件事。

它对自己定位的原话出现在两处。README 里写「Basalt is not a replacement for Obsidian. Instead, it provides a minimalist terminal interface with a WYSIWYG experience」；文档站里那句更直白，一个 minimalist terminal companion——配着可读渲染和熟悉键位的终端伴生工具。后一句其实更贴近实情：companion，不是替代。

所以这篇文章要回答的问题不是「Basalt 能不能替掉 Obsidian」，而是两件事：它的读体验是用什么工程结构撑起来的，以及你要用的那个版本到底有没有某个能力。

## 先划清版本口径

这条放在最前面，因为它决定后面每张表能不能照着做。

Basalt 的 README 和 `docs/` 目录跟随 `main` 分支，而 `main` 上 `basalt/Cargo.toml` 已经写成 `version = "0.13.0"`。这个版本还没有发布：GitHub Releases 里最新的稳定版是 `basalt/v0.12.7`，发布于 2026-08-14，crates.io 上 `basalt-tui` 的最新版本同样是 0.12.7。

两者的差别不是修辞问题。v0.12.7 的 `docs/Known Limitations.md` 里有两行：

```text
- Syntax highlighting is not supported
- Code blocks are rendered without syntax highlighting
```

这两行在 `main` 上被删掉了，换成了另一行——语法高亮覆盖 Rust、TOML、JSON、Bash、JavaScript、TypeScript、Python、Go、YAML 和 C，围栏里写了名单外的语言则按纯代码渲染。也就是说，**你在文档里读到的语法高亮，`cargo install basalt-tui` 装到的那个二进制里没有**。

下文凡属于只在 `main` 上成立的能力，都会显式标注 `main`。

## 目录

- [先说结论](#先说结论)
- [先划清版本口径](#先划清版本口径)
- [系统地图：三个 crate 与两层界面](#系统地图三个-crate-与两层界面)
- [三组容易混在一起的概念](#三组容易混在一起的概念)
- [Elm 架构落到代码上是什么样](#elm-架构落到代码上是什么样)
- [渲染边界：全量解析，有意少画](#渲染边界全量解析有意少画)
- [语法高亮为什么还不能算已发布能力](#语法高亮为什么还不能算已发布能力)
- [键位系统：leader、按键序列与两种预设语义](#键位系统leader按键序列与两种预设语义)
- [一次任务怎么流过整个系统](#一次任务怎么流过整个系统)
- [保险库是怎么被找到的](#保险库是怎么被找到的)
- [外观是配置而不是代码](#外观是配置而不是代码)
- [装哪个版本，怎么装](#装哪个版本怎么装)
- [适用边界与采用顺序](#适用边界与采用顺序)
- [排查从哪几处入手](#排查从哪几处入手)
- [自测题](#自测题)
- [下一步读哪份代码](#下一步读哪份代码)
- [参考](#参考)

## 系统地图：三个 crate 与两层界面

`main` 的 `Cargo.toml` 把仓库声明成 workspace，成员是 `basalt`、`basalt-*` 和 `obsidian-to-zola`。前两类是 Basalt 本体，第四个是把 `docs/` 那套 Obsidian 语法文档发布成站点的小工具——顺带说明作者的文档确实是用 Obsidian 写的。

本体三个 crate 的分工和许可证：

| crate | 职责 | 许可证 |
|-------|------|--------|
| `basalt-core` | 领域逻辑与 Obsidian 集成：vault、note、`obsidian.json` 定位、Markdown 解析。不依赖任何 UI 库 | Apache-2.0 |
| `basalt-widgets` | 可复用的 ratatui 组件，主体是 `MarkdownView` | Apache-2.0 |
| `basalt`（发布名 `basalt-tui`） | 主程序，把前两者拼成应用，持有事件循环与全部界面状态 | GPL-3.0-or-later |

README 的措辞是「Basalt spans three crates under two licenses」，这个切法是有意图的：库保持 Apache 以便别的项目复用，应用走 GPL 要求分发修改版时同样开源。仓库根目录因此同时有 `LICENSE-APACHE` 和 `LICENSE-GPL` 两个文件，接受贡献还要签 `CLA.md`。

有一条工程上的推论值得先记下：GitHub 仓库页右上角那个许可证徽章显示 Apache-2.0，那是自动扫描认到了 `LICENSE-APACHE` 的结果，不代表 `basalt-tui` 本身可以闭源分发。想把 `basalt-widgets` 摘出去用，Apache 放行；想把 Basalt 嵌进自己的产品，挡路的是 GPL。

界面那一侧分四层元素：

| 元素 | 位置 | 管什么 |
|------|------|--------|
| 标签栏 | 顶部 | 已打开的笔记，每个标签独立保存光标、滚动位置和未保存的修改 |
| Explorer | 左 | 当前保险库的文件夹与笔记树 |
| Note editor | 中 | 渲染后的当前笔记 |
| Outline | 右 | 当前笔记的标题层级，可跳转 |
| 模态 | 覆盖在界面上 | 帮助（`?`）、保险库选择（`Space v`）、输入框（重命名）、主题选择（`Space t`）、调试日志（`Space d`） |
| 状态栏 | 底部 | 当前焦点窗格、字数与字符数、启用内置编辑器时的编辑模式 |

窗格中哪个有焦点由更粗的边框标出，状态栏同时写一遍，焦点在窗格间移动用 `Tab` 与 `Shift+Tab`。

最影响日常手感的其实是标签栏：**Basalt 是多标签的**。从 Explorer 打开一篇笔记，如果它的标签已经开着就聚焦过去，否则新开一个；在标签间循环时 Explorer 的选择会跟着跳到那篇笔记，并把它路径上被折叠的文件夹展开，好让笔记保持可见。同名标签靠父目录区分，标签宽度统一、随数量增多而压缩。

## 三组容易混在一起的概念

读下去之前先把这三组切开，它们各自都会造成误判。

**解析能力不等于渲染能力。** `basalt-core/src/markdown.rs:438` 用 `pulldown_cmark::Parser::new_ext(text, Options::all())` 建解析器——所有扩展都开了。所以脚注、数学、删除线在 AST 里都存在，只是渲染层没有给它们画样式。这就是「bold/italic 解析但不加视觉样式」这句话的确切含义：不是解析失败，是渲染层主动不做。

**你的配置与默认值合并，vim 预设与默认值替换。** 这两句话在文档里挨着放，语义相反。用户配置只覆盖你写出来的那些键，其余默认键位继续有效；而 `vim_mode = true` 加载的 `basalt/vim.toml` 预设，对它自己定义的每一节是整节替换掉默认键位，然后你的配置再叠在替换后的结果上。开 vim 模式之前你以为保留的东西，可能已经被换掉了。

**保险库模式不等于单文件模式。** 前者有 Explorer，后者只有 Note editor 和 Outline 两个窗格，靠传一个文件路径进入。这两种模式下「能改什么」的答案不一样。

## Elm 架构落到代码上是什么样

`docs/Basalt.md` 明确写了架构取向：Elm 风格，单向数据流加显式状态管理，一条环路是 `Event → Message → Update → State → Render → Event`。三个概念：

- **Model**：应用状态用不可变数据结构表达，中心是 `AppState`（`basalt/src/app.rs:78`），每个 UI 组件持有自己的子状态，状态从不被就地修改。
- **Message**：用户动作表达成带类型的消息，各组件定义自己的枚举，例如 `explorer::Message::Select`、`note_editor::Message::CursorUp`。消息描述发生了什么，不描述怎么处理。
- **Update**：更新函数吃当前状态和一条消息，返回新状态以及可选的新消息。消息可以级联——一个组件的 update 返回另一个组件的消息，环路继续转，直到不再产生新消息。

级联那句在源码里能直接看到形状。`App::update` 的调用点是个 while 循环：

```rust
// basalt/src/app.rs:550 附近
let mut message = App::handle_event(&config, &mut state, event);
while message.is_some() {
    message = App::update(self.terminal.get_mut(), &config, &mut state, message);
}
```

事件读取用的是 crossterm 的 `event::poll(timeout)` 配阻塞的 `event::read()`，tick 间隔 250 毫秒；**没有使用 ratatui 的 `EventListener` 或 `EventStream`**，主循环里也没有异步任务，整个应用没有引入 tokio。照着「参考别人的 ratatui 项目」去抄事件循环时，这一点容易抄错：Basalt 的取事件方式就是一个 250 毫秒的 poll 窗口。

组件的绘制实现哪种 trait 也各不相同：`Explorer`（`basalt/src/explorer.rs:205`）、`Outline`（`basalt/src/outline.rs:167`）、输入模态、帮助模态、主题选择器、调试日志覆盖层实现 `StatefulWidget`；`Header` 和 `Toast` 实现 `Widget`；`basalt-widgets` 里的 `MarkdownView` 实现的是 `StatefulWidgetRef`（`basalt-widgets/src/markdown/view.rs:211`）。

为什么这一层值得读：窗格之间不互相调用，只发消息。加一个新窗格不需要改动旧窗格，代价全在消息路由上；而「重命名一篇笔记要顺带更新全库 wiki-link」「切换标签要同步 Explorer 选择」这类跨组件动作，在这套结构里都是一条消息触发的级联，路径可追。

## 渲染边界：全量解析，有意少画

渲染的做法是把语法字符换成视觉样式：标题的 `#` 隐去、改成彩色指示，引用块的 `>` 换成左侧竖条，行内代码套一层样式。

`main` 上已渲染的元素：

| 元素 | 渲染方式 |
|------|----------|
| 标题 H1 至 H6 | 隐藏 `#`，按级别给指示符；H5、H6 可另设装饰字体 |
| 段落、有序与无序列表 | 项目符号按嵌套深度循环取用 |
| 引用块 | 左侧竖条 |
| 行内代码 | 代码底色 |
| 任务项 `- [ ]` 与 `- [x]` | 视觉复选框；`- [?]` 不支持 |
| GFM 表格 | 带框渲染 |
| 围栏代码块 | 独立底色；`main` 上有语法高亮 |
| Callout | 图标加彩色标题头，支持自定义标题 |
| 链接 | 解析 `[[Note]]`、`[[Note\|Display Text]]`、`[[Note#Heading]]` 与标准 Markdown 链接 |

不渲染的东西，照 `docs/Known Limitations.md` 的口径列全：图片、分割线、粗体与斜体与删除线（解析但不加样式）、数学块（`$...$` 与 `$$...$$`）、脚注、HTML 内容；外链不能用鼠标点击；Callout 的折叠标记 `-` 与 `+` 能识别，但折叠不可交互，展开态一律按展开画。

**不过「不能用鼠标点」不等于「打不开」。** 开了 `vim_mode` 之后，Note editor 多出一个 `gx`，它取光标所在的链接，然后分两种走法：标准链接交给系统 opener；wiki-link 如果能在库里解析出来，就在 Explorer 里定位到那个文件并把它作为标签打开，如果解析不出来，就在当前笔记所在目录下把缺失的那篇笔记建出来再打开。Obsidian 里「点一个还不存在的链接、顺手把笔记建了」这个动作，终端这边是有的。

于是对「它到底支不支持笔记图」这个问题，答案要分成两层：顺着链接跳、改标题不断引用这两件维持局部连通性的事它做了；Graph View 与反向链接面板这类全局视图它不做。

**表格要单独说一句，因为它推翻了一个常见的想当然说法。** GFM 表格在 v0.12.7 就已经渲染成带框的盒子：列宽按内容计算，表格整体放不下时按各列比例分配剩余宽度，单元格长文本自动换行。编辑时表格保持渲染态，只有光标所在的那一行还原成原始管道语法；一旦表格语法被写坏，整块退回纯文本，保证它仍然可见、仍然可编辑。

于是「终端是字符网格，所以表格做不了」这种解释站不住：列宽计算与文本换行本来就在字符网格的能力圈内，做不了的其实是像素级定位（图片）和排版引擎（数学公式）那一类。剩下的缺口该怎么读，官方自己给了口径。那一页的标题写的是 current limitations and features not yet implemented，分割线和粗体斜体被列在「尚未实现」底下，而不是「做不到」。

Callout 的兼容面比「支持 Obsidian 语法」这句概括要宽：Obsidian 的全部 callout 类型及其别名都被识别且大小写不敏感，`tip` 认 `hint` 与 `important`，`success` 认 `check` 与 `done`，未知类型退化成 `note`。图标跟随当前的符号预设，也可以按类型单独覆盖。

## 语法高亮为什么还不能算已发布能力

前面已经交代过版本口径，这里补上实现细节，因为它决定你敢不敢依赖它。

`main` 引入的是 tree-sitter 而不是 Rust 生态里另一条常见路线 syntect（`Cargo.lock` 里没有它）。`basalt/Cargo.toml` 里挂了 `tree-sitter` 与 `tree-sitter-highlight` 加十个语言 grammar crate；`basalt/src/note_editor/highlight.rs:123` 那张别名表就是能力边界：

```rust
"rust" | "rs" => Some(Self::Rust),
"toml" => Some(Self::Toml),
"json" => Some(Self::Json),
"bash" | "sh" | "shell" | "zsh" => Some(Self::Bash),
"javascript" | "js" | "mjs" | "cjs" => Some(Self::JavaScript),
"typescript" | "ts" => Some(Self::TypeScript),
"python" | "py" => Some(Self::Python),
"go" | "golang" => Some(Self::Go),
"yaml" | "yml" => Some(Self::Yaml),
"c" => Some(Self::C),
```

语言取开场围栏后的第一个词，写语言名或文件扩展名都行；名单之外、或者干脆没写语言，就按纯代码渲染。构造 `HighlightConfiguration` 时只填了高亮查询（highlight query）这一个参数，injection 与 local properties 两个查询位传的是空串，所以跨语言嵌入这类高级玩法没有启用。

着色不查语法库，高亮结果只落到六个语义角色上：`keyword`、`string`、`comment`、`function`、`type`、`constant`（数字、布尔、`null` 和转义序列都归这一类）。颜色取自当前主题的 `[syntax]` 表，没写全的角色继承 `default` 主题的值。这意味着换一个主题，代码配色跟着换，而不是绑死在某套语法主题上。

还有两条实际影响：从源码构建需要一个 C 编译器，因为每种支持语言的 grammar 都要编译一份 C 文件，这条 `docs/Getting started/Installation.md` 里专门放了提示；以及这套高亮在 0.12.7 上不存在，如果你按 README 装完发现代码块只有底色，不是你配置错了。

## 键位系统：leader、按键序列与两种预设语义

配置是一个 TOML 文件，按窗格分节。每一节的键位写成内联表数组，一个绑定只有两个字段：

```toml
[global]
key_bindings = [
  { key = "<leader>e", command = "exec:vi %note_path" },
  { key = "<leader>o", command = "spawn:open obsidian://open?vault=%vault&file=%note" },
]
```

`KeyBinding` 结构体定义在 `basalt/src/config/key_binding.rs:13`，字段就是 `key` 和 `command`。往绑定里塞 `description` 不会报错，但也确实什么都不会发生。

按键序列是这套配置里最值得学的部分。一个键可以是单字符、命名键、带修饰键的键，或者一串按键序列；`gg` 这类序列要求连续按下、中间不插其它键。大写字母 `G` 就是 `shift+g` 的简写。多字符串会按字符拆开，所以命名键想当序列开头必须用尖括号包起来分组：`<space>f` 表示空格加 f，不包就会被读成 `s p a c e` 五个键。尖括号本身要绑定用 `<lt>` 和 `<gt>`。

`<leader>` 是一个可搬移的前缀，默认 `<space>`，在配置文件顶层 `leader = ","` 一行就能整套搬家，且默认键位也跟着搬（`Space v` 变成 `,v`）。leader 可以是组合键（`leader = "ctrl+w"`）也可以是序列（`leader = "gs"`），可以在一条绑定里出现两次（`<leader><leader>`），不能引用自己。

默认键位里有几条属于每天都要用的：

| 键 | 命令 | 作用 |
|----|------|------|
| `?` | `help_modal_toggle` | 打开帮助模态，显示**当前焦点窗格**的可用键位 |
| `Space v` | `vault_selector_modal_toggle` | 保险库选择器 |
| `Space d` | `debug_log_toggle` | 调试日志覆盖层 |
| `Space e` | `exec:vi %note_path` | 用 vi 打开当前笔记（阻塞） |
| `Space o` | `spawn:open obsidian://…` | 在 Obsidian 里打开当前笔记 |
| `Ctrl+n` `Ctrl+p` | `tab_next` `tab_previous` | 切标签，等价键还有 `L` `H` 与 `]b` `[b` |
| `Ctrl+w` | `tab_close` | 关闭当前标签 |

`global` 节先于窗格节求值，所以全局绑定优先命中。

预设语义就是前面切开的那组概念，落到实处要看 `basalt/vim.toml` 到底写了哪几节：`note_editor`、`explorer`、`outline`、`input_modal` 四节，仅此四节被整节替换，`global` 和各模态节不受影响。四节里 Explorer 与 Outline 的替换表是默认键位的超集，只在原表上多了 `gg` 与 `G`，原有键位一个没少；真正会改变手感的是 Note editor。那一节是一整套仿 vim 的动作面：`gg`、`G`、`gk`、`gj`、`w`/`b`/`e` 与大写变体、`0`、`^`、`$`、`{`、`}`、`%`、`f`/`F`/`t`/`T`/`;`/`,`，操作符 `d`、`c`、`x`、`D`、`C`、`s`、`p`、`P`，撤销重做 `u` 与 `Ctrl+r`，可视选择 `v` 与 `V`，以及 `i`、`a`、`r`。代价也在这里：默认那节里 `t` 是切换 Explorer 窗格，换上 vim 预设后 `t` 变成 till-forward，想切窗格得改用 `Ctrl+b`。在 Note editor 里，vim 模式还在 EDIT 之内再分 Normal 与 Insert 两个子模式——`i` 进 Insert 打字，`Esc` 回 Normal 导航，再按 `Esc` 退回 READ。

自定义命令有两种前缀，行为差别明确：`exec:` 在当前 shell 环境里运行并阻塞到结束，且**只有第一个参数被当作可执行文件**，其余按字面传参；`spawn:` 起新进程不阻塞，适合打开外部应用或 URL。上下文变量只有三个——`%vault`（当前库名）、`%note`（当前笔记名）、`%note_path`（当前笔记完整路径），没有 `%note_dir` 之类的目录变量。不做 shell 展开，管道、重定向、命令替换都不支持，复杂操作要自己包成脚本。变量还要求上下文齐备，比如 `%note` 得先有选中的笔记。平台 opener 各异：macOS 用 `open`，Linux 用 `xdg-open`，Windows 用 `start`。Obsidian 的 URL scheme 可以接 `open`、`new`、`daily`、`search` 几个动作。

## 一次任务怎么流过整个系统

把上面的机制串成一次真实操作。

1. 终端敲 `basalt`，进入启动屏，列出从 Obsidian 配置里自动发现的保险库；`j`/`k` 或方向键选择，`Enter` 打开。进入后焦点落在 Explorer。
2. Explorer 里 `j`/`k` 定位到某篇笔记，`Enter` 打开。标签栏出现这篇笔记的标签，Note editor 渲染内容，Outline 按当前笔记的标题重建。此刻笔记正文是从磁盘读进 `SelectedNote` 的一份副本。
3. `Tab` 把焦点移到 Outline，`j`/`k` 选中一个二级标题。这里要注意：**`Enter` 是展开或收起这个标题节点，`g` 才是让编辑器跳过去**。
4. 中途想看另一篇已开的笔记，`Ctrl+p` 切过去，Explorer 的选择跟着移动、沿途折叠的文件夹自动展开；每篇笔记的光标和滚动位置都还在。
5. 决定改一处文字。`Space e` 触发 `exec:vi %note_path`，`exec:` 阻塞，终端交给 Vim；写完 `:wq` 保存退出，控制权回到 Basalt。
6. 画面这时未必是新的。文件监听（`notify-debouncer-full`，250 毫秒去抖、递归监视、跳过 `.obsidian` 和 `.git` 这类隐藏目录）收到变更后只发一条 `Message::RescanVault`，而它的处理函数只有一行实质动作——`state.explorer.refresh_entries(state.vault.entries())`，刷新的是 Explorer 的文件列表。要看外部修改的结果，`Ctrl+w` 关掉标签再打开，重开的过程才会重新读盘。
7. 顺手改名。回 Explorer 按 `r`，输入模态里按 `i` 进编辑态，改完 `Enter` 确认。全库指向这篇笔记的 wiki-link 一起更新。
8. 新建。`n` 建未命名笔记，`N` 建未命名文件夹，落在当前选中的文件夹下（选中的是笔记就落到它的父文件夹），什么都没选就落在库根；目标文件夹展开，新条目自动选中。
9. 换库用 `Space v`；过程不对劲就 `Space d` 开调试日志覆盖层看它到底收到了什么。

第 6 步值得停一下。这类「终端做壳、真编辑器在外面」的组合，共同坑就是缓冲区归属：Basalt 的可见状态属于内存里那份 `SelectedNote`，不是磁盘文件。它没有实现「外部写入即重载」，而文件监听确实又在跑——于是很容易让人以为改了就会刷新。判断这类工具时可以直接问一句：磁盘内容是不是单一真源。Basalt 的答案是打开那一刻是，之后不是。

## 保险库是怎么被找到的

Basalt 读 Obsidian 自己的配置文件来发现保险库，`docs/Files and Folders.md` 列了五条位置：

| 平台 | 路径 |
|------|------|
| macOS | `~/Library/Application Support/obsidian/obsidian.json` |
| Linux | `~/.config/obsidian/obsidian.json` |
| Linux Flatpak | `~/.var/app/md.obsidian.Obsidian/config/obsidian/obsidian.json` |
| Linux Snap | `~/snap/obsidian/current/.config/obsidian/obsidian.json` |
| Windows | `%APPDATA%\Obsidian\obsidian.json` |

Windows 那一行的目录名首字母大写，这不是笔误：`basalt-core/src/obsidian/config.rs:164` 用 `cfg!(windows)` 在两个常量之间切换，Windows 上是 `Obsidian`，其余平台是 `obsidian`。解析由 `dirs` crate 提供平台配置目录，再拼上这个目录名。

实现细节里还有两点。**取的是第一个存在的位置**（`existing_config_locations.first()`），不是全部合并；以及 `OBSIDIAN_CONFIG_DIR` 环境变量可以整段覆盖配置目录，路径里的开头 `~` 会展开。于是 Obsidian 客户端没装、或者那个配置文件压根不存在时，仍然有两条路可走。其一是上面那个环境变量，其二干脆绕过保险库：

```text
basalt path/to/note.md
```

带一个文件参数就跳过保险库直接开文件，进入的是只有 Note editor 和 Outline 的聚焦视图，没有 Explorer，`Tab` 与 `Shift+Tab` 在两者之间移焦点。文件不存在时它会被创建成空文件，且文件路径优先于任何保险库。想回到某个库，`Space v` 选一个，Explorer 就回来了。

Explorer 里以点开头的隐藏文件和文件夹不显示。`s` 在升序降序之间切换，文件夹永远排在文件前面。

## 外观是配置而不是代码

界面颜色由一个命名主题驱动，`theme = "gruvbox-dark"` 这样选。默认是 `default`，它自己不设背景，因此完全跟随终端配色。内置主题有 14 个文件（`basalt/themes/`）：`default`、`causeway-dark`、`causeway-light`、`gruvbox-dark`、`gruvbox-light`、`everforest-dark`、`everforest-light`、`nord`、`dracula`、`catppuccin-latte`、`catppuccin-frappe`、`catppuccin-macchiato`、`catppuccin-mocha`、`minimal`。

`<leader>t` 打开主题选择器，滚动时整套界面实时预览：`Enter` 保留并把 `theme` 写回你的配置文件，`Esc` 则撤销回打开前的样子。写回只动 `theme` 这一个键，你配置里的注释、顺序和其它内容原样保留。

主题文件是一组语义角色加一张 `[palette]`：角色值要么引用调色板里的名字，要么写字面色（`#rrggbb` 或 ANSI 名）。角色覆盖正文与背景、`muted`、`accent`、`heading-1` 到 `heading-6`、`code-bg`、`blockquote`、`list-marker`、`task`、状态栏三个模式色块、以及 callout 和 toast 用的 `success`/`info`/`warning`/`error`。没写的角色继承 `default`。边框可以整体设 `border-type`（`none`、`plain`、`rounded`、`thick`、`double`），也能用 `border-edges` 只画某些边——`minimal` 主题就是靠 `[explorer] border-edges = "right"`、`[note-editor] border-edges = "vertical"` 只留窗格之间的分隔线。`border-type` 不写时跟随符号预设，焦点窗格粗、其余圆角。

符号是另一套东西，`[symbols]` 选预设、直接平铺要改的字段：

```toml
[symbols]
preset = "nerd-font"
task_checked = "[x]"
task_unchecked = "[ ]"
list_markers = ["->", "=>", "~>"]
h5_font_style = "fraktur-bold"
```

三个预设是 `unicode`（默认）、`ascii`、`nerd-font`。字段名是 `tree_expanded`、`tree_collapsed`、`selected`、`unselected`、`wrap_marker`、`h1_underline`、`blockquote_border`、`callout_note` 这一类，外加 `outline_*` 一组和 `list_markers` 数组；`title_font_style`、`h5_font_style`、`h6_font_style` 可以取 `black-board-bold`、`fraktur-bold`、`script` 三种装饰字体，`ascii` 预设下这三项没有对应字形，文档给的默认值就是空。**没有 `[symbols.override]` 这个子表，也没有 `folder`、`file` 两个字段**——结构体 `Symbols` 的字段能在 `basalt/src/config/symbol.rs:40` 一次读完。

### 示例：一份能直接落盘的配置

前面三件事——搬走前缀键、只改个别绑定、降级符号字形——放在一份文件里是这样。位置写 `$HOME/.basalt.toml`，两个候选位置里只取第一个存在的那个，不合并。

```toml
# 顶层键：前缀、主题、内置编辑器与 vim 预设
leader = ","
theme = "gruvbox-dark"
experimental_editor = true
vim_mode = true

[global]
key_bindings = [
  # 默认就是 exec:vi %note_path，换掉可执行文件即可，阻塞语义不变
  { key = "<leader>e", command = "exec:nvim %note_path" },
  # 不阻塞地把今天的 daily note 丢给 Obsidian
  { key = "<leader>f", command = "spawn:open obsidian://daily?vault=%vault" },
]

[outline]
key_bindings = [
  { key = "enter", command = "outline_select" },
]

[symbols]
preset = "ascii"
```

三处容易看漏。`[outline]` 这一节在 `vim_mode = true` 时已经被 `vim.toml` 整节替换过，你这条 `enter` 是叠在替换结果上的，于是原本的 `outline_expand` 被顶掉、`enter` 变成跳转，而 `g` 仍然指向同一个命令。`<leader>f` 不与任何默认绑定冲突，但 `<leader>d` 已经是调试日志覆盖层，别拿它做别的用途。`theme` 这一行写不写都行——用 `<leader>t` 选主题并按 `Enter` 确认时，Basalt 会自己在配置文件里更新 `theme` 这一个键，其余内容和注释顺序不动。

## 装哪个版本，怎么装

安装入口有四个，README 把前三条并列给出：

```bash
brew install erikjuhani/tap/basalt      # Homebrew tap
cargo install basalt-tui                # crates.io，包名带 -tui 后缀
aqua g -i erikjuhani/basalt             # aqua
```

第四条是从 GitHub Releases 下预编译包，解压后把 `basalt` 放进 `PATH`。crate 名与二进制名不一致这件事要多看一眼：包名是 `basalt-tui`，装完可执行文件叫 `basalt`。而 crates.io 上 `basalt` 这个名字已经被一个无关的 Vulkan UI 框架占用（0.21.0），敲 `cargo install basalt` 不会报错，只会装到另一个项目身上。

想跟最新开发进度，有个 `nightly` 发布标签始终挂着 `main` 的最新一次构建。两种从源码跟进的装法：

```bash
brew install --HEAD erikjuhani/tap/basalt
cargo install --git https://github.com/erikjuhani/basalt --branch main basalt-tui
```

版本自证也给了：下载来的 nightly 在 `basalt --version` 里带 `-nightly` 后缀，源码构建则报提交哈希（commit hash）。

从源码构建的两个门槛：workspace 的 `rust-version` 是 1.91.0（0.12.7 与 main 相同），edition 2021；只在 main 上还需要一个 C 编译器，因为 tree-sitter 要为每种支持语言编一份 C grammar，这条提示写在 `docs/Getting started/Installation.md`，0.12.7 的那份文档里没有它。那份文档也只列 Cargo、aqua 和预编译包，Homebrew 当时只写在 README 里。

自己声明的命令行参数有四个（`--help` 与 `--version` 由 clap 自动生成）：可选的位置参数 `FILE`（单文件模式）、`--debug`（启动即打开调试日志覆盖层）、`--log-level`（覆盖层最低可见级别，默认 trace）、`--theme`（按名覆盖配置里的主题）。

装完先做一件事再谈别的：`basalt --version` 报的是 0.12.7 还是带 hash 的 main。前文那些标注 `main` 的能力，取决于你这个答案。

## 适用边界与采用顺序

把能力边界摊开，适合与不适合都很具体。

适合：终端是主工作场所、切到 Obsidian 客户端查笔记会断节奏；用 Obsidian 管技术文档，动作多是查阅而不是撰写；习惯 vim 键位，愿意为 `j`/`k` 导航放弃鼠标；同时维护多个保险库，需要快速切换。多标签和 `Space v` 是这一类需求的核心支撑。

不适合：主要动作是写。内置编辑器逐行整篇编辑，编辑态键位当前不可改，粘贴图片不支持，不开 vim 模式时也没有撤销重做和选择。需要全文搜索、Graph View、反向链接面板的，这些 Basalt 明确不做。笔记里图片密集的，它不渲染图片。Obsidian 插件产生的语法不保证渲染，插件本身不支持。依赖删除、移动、复制笔记的自动化流程走不通，它只有新建和重命名。

采用顺序，每一步都留了可判定的验收条件：

1. `cargo install basalt-tui` 或 `brew install erikjuhani/tap/basalt`，跑 `basalt`，看启动屏是否列出你的保险库。没有就查 `OBSIDIAN_CONFIG_DIR`，或用 `basalt path/to/note.md` 先验证渲染本身。
2. 在最常用的库里走一遍「打开笔记、用 Outline 的 `g` 跳转、切标签」这条路径，确认渲染子集对你那些笔记可接受，特别检查有没有依赖图片。
3. 配 `vim_mode = true`，并核对一遍 `?` 模态里当前窗格的键位，确认被 vim 预设整节替换掉的键位里没有你依赖的默认键。
4. 配一个外部编辑器绑定（默认 `Space e` 已经给了 `exec:vi %note_path`，按需改成 `nvim` 或 `code`），实测一次外部修改后关标签重开的刷新路径。
5. 库里 wiki-link 密集的话，拿一篇被引用多的笔记做 `r` 重命名，确认引用同步。
6. 上面任一步不达预期，Basalt 先放观望；全部达到，它就能作为 Obsidian 之上的查阅层长期用下去。

如果你打算是改代码而不是用，还有一条许可约束要先想清楚：改 `basalt-core` 或 `basalt-widgets` 并另作他用，Apache-2.0 允许；分发修改过的 `basalt-tui`，GPL-3.0-or-later 要求同样开源；提 PR 受 `CLA.md` 约束。仓库的 `CONTRIBUTING.md` 也写了接受范围——主要收 bug 修复，新功能要先开 issue 讨论。

## 排查从哪几处入手

按现象定位，最常见的两类是「找不到保险库」和「按键不生效」。

**启动屏是空的或没有你要的库。** 先确认 Obsidian 本机配置过该库；再按五条位置逐一核对，尤其 Windows 目录名是 `Obsidian` 不是 `obsidian`。配置文件有多个候选位置时只取第一个存在的那个，家目录下的 `.basalt.toml` 优先于 `XDG_CONFIG_HOME/basalt/config.toml`——注意这是 Obsidian 那一侧的定位逻辑。Basalt 自己的配置文件同样是只取第一个、不合并，`Known Limitations` 里单列了这一条。

**改了配置没反应。** 最可能是位置写错导致整份文件没被读到，其次是节名或字段名对不上：文档用的写法是 `key_bindings = [ { key = …, command = … } ]`，一条绑定只有 `key` 和 `command` 两个字段。命令里的 `|`、`>`、`$(…)` 不会被解析，需要就包成脚本。

**某个键触发了意外动作。** 先看是否开了 `vim_mode`：`vim.toml` 对 `note_editor`、`explorer`、`outline`、`input_modal` 四节是替换而非合并，最典型的后果是 Note editor 里 `t` 从「切换 Explorer」变成 till-forward，切窗格要改用 `Ctrl+b`。再看序列：`gg` 要求两键之间不插入其它按键，中间混进任何一次按键序列就断了；想让命名键当序列开头必须写成 `<space>f` 这种尖括号形式。

**外部编辑后画面不变。** 见前文第 6 步，`Ctrl+w` 关标签再打开。

**代码块只有底色、没有配色。** 这是版本问题不是配置问题，0.12.7 的高亮还不存在。

**表格掉成一行行管道原文。** 表格语法被写坏时整块回退纯文本，检查分隔行与列数。

**图标显示成方块或问号。** 终端字体不含这些字形，切 `preset = "ascii"`，或装 Nerd Font 后用 `nerd-font`。

**想看到底发生了什么。** `Space d` 开调试日志覆盖层，`l` 在 trace 到 error 之间循环最低可见级别，`c` 清空；`--debug` 与 `--log-level` 可以在启动时就带着，标题栏会显示当前级别和进程内存占用。

## 自测题

**1. `cargo install basalt-tui` 之后，代码块会有语法高亮吗？**

不会。最新稳定发布是 0.12.7，它的 `Known Limitations` 里明写不支持语法高亮；tree-sitter 那套在 `main` 上（版本号已写 0.13.0），还没进任何一个发布版本。

**2. Outline 里想把编辑器跳到某个标题，按哪个键？**

`g`。`Enter` 是展开或收起该标题节点，不做跳转。

**3. 用外部编辑器改完并保存，Basalt 的画面会自己刷新吗？**

不会。文件监听只发一条 `Message::RescanVault`，它刷新的是 Explorer 的文件列表；已打开的标签在 `open_note` 里被 `open_or_focus` 提前返回，不重读磁盘。关掉标签再打开才会重读。

**4. 一篇笔记被全库十几处 wiki-link 引用，重命名要额外做什么？**

不需要。Explorer 按 `r` 改名后，指向它的 wiki-link 会全库更新。但删除、移动、复制笔记这三件事 Basalt 都不做。

**5. 光标停在一篇还不存在的笔记的 `[[链接]]` 上，能做什么？**

开 `vim_mode` 之后按 `gx`：链接能解析到已有笔记就跳过去并在 Explorer 里定位，解析不到就在当前笔记所在目录下把目标笔记建出来再打开。前提是 `gx` 属于 vim 预设的 Note editor 那一节，默认键位表里没有它。

**6. 把 `basalt-widgets` 里的 `MarkdownView` 用在自己的闭源项目里，许可证上有障碍吗？**

没有。`basalt-core` 和 `basalt-widgets` 是 Apache-2.0；受限的是应用本体 `basalt-tui`，它是 GPL-3.0-or-later。仓库页那个 Apache-2.0 徽章是自动识别 `LICENSE-APACHE` 的结果，不能作为 `basalt-tui` 的许可证依据。

**7. 只想改一个默认键位，需要把整份默认配置复制过来吗？**

不需要，你的配置与默认值合并，写出那一条就行。但要留意 `vim_mode`：它带的 `vim.toml` 对自己那四节是整节替换，替换之后你的绑定才叠上去。

## 下一步读哪份代码

想搞清架构与事件流，按这个顺序读 `main`：

- `basalt/src/app.rs:78`，`AppState` 的全部字段
- `basalt/src/app.rs:535` 起的 `run`，250 毫秒 tick、poll 加 read、消息级联和 watcher 分支
- `basalt/src/app.rs:317`，`open_note` 与标签复用那条提前返回
- `basalt/src/config/mod.rs:97`，`Config` 的节结构，以及 `ConfigSection` 的 `merge_key_bindings` 与 `replace_key_bindings`
- `basalt/src/command.rs`，`exec:` 与 `spawn:` 的解析
- `basalt/src/note_editor/highlight.rs:123`，语言别名表与六个着色角色
- `basalt/src/config/symbol.rs:40` 与 `basalt/src/config/theme.rs`，符号字段和主题角色
- `basalt/vim.toml`，vim 预设到底替换了哪些节
- `basalt-core/src/obsidian/config.rs`，保险库定位与环境变量覆盖
- `basalt-widgets/src/markdown/view.rs:211`，`MarkdownView` 的渲染入口

想确认某个能力到底算不算已发布，别看 README，看那个 tag 上的文档：`git show "basalt/v0.12.7:docs/Known Limitations.md"`。这一条比读任何架构章节都省事，也能避免把作者正在做的工作当成你已经拿到的东西。

## 参考

- 仓库：<https://github.com/erikjuhani/basalt>（2026-09-20 观测：1,357 stars、39 forks，Rust）
- 最新稳定发布：`basalt/v0.12.7`，2026-08-14；crates.io 上的 `basalt-tui` 同版本
- `docs/Known Limitations.md`：渲染、文件操作、内置编辑器、配置、Obsidian 兼容五类边界的权威清单
- `docs/Basalt.md`：Elm 架构三概念、三个 crate 的分工、作者自述动机
- `docs/Configuration/Configuration.md`：完整默认配置，含各窗格节与全部默认键位
- `docs/Configuration/Key mappings.md`：序列语法、leader 规则与可用命令全表
- `docs/Configuration/Custom commands.md`：`exec:` 与 `spawn:` 的差别、三个变量、平台 opener
- `docs/Configuration/Themes.md` 与 `docs/Configuration/Symbols.md`：语义角色、边框、符号预设与字段
- `docs/User interface/`：User interface、Explorer、Note editor、Outline、Editor (experimental)
- `docs/Editing and Formatting.md`、`docs/Files and Folders.md`、`docs/Getting started/Installation.md`
- ratatui：<https://github.com/ratatui/ratatui>（0.30.0；tui-rs 已归档，ratatui 是其社区后继）
- pulldown-cmark：<https://github.com/pulldown-cmark/pulldown-cmark>（0.13.0，以 CommonMark 为基准、通过 Options 开启扩展）
