---
title: "LazyGit：Git 终端可视化的日常操作指南"
date: "2026-04-12T02:29:31+08:00"
slug: lazygit-git-terminal-ui-guide
github_repo: "jesseduffield/lazygit"
source_key: "gh:jesseduffield/lazygit"
description: "LazyGit 是 Go 编写的 Git 终端 UI，用面板把暂存、提交、分支、变基、冲突解决等操作可视化。本文从安装配置讲起，按面板介绍常用快捷键，一步步走通提交、变基和冲突解决的完整流程。"
draft: false
categories: ["技术笔记"]
tags: ["Git", "Go", "终端", "TUI"]
---

# LazyGit：Git 终端可视化的日常操作指南

LazyGit 解决的问题很具体：Git 命令行能做所有事，但交互式变基（interactive rebase）、逐行暂存、Cherry-pick 这类操作要记一堆参数，敲错了只能重来。LazyGit 把这些操作放进一个终端里的 TUI（Text User Interface，文本用户界面），用面板分开展示，按一个键就执行对应的 `git` 命令。

它没有重新实现 Git，而是把你常用的 Git 操作封装成不到一两个按键的动作，并实时展示执行结果。本文针对「已经会用 `git`，想在日常开发里取代命令行」的读者，按面板介绍快捷键，再带你把提交、变基、冲突解决走一遍。

## 前置条件

- 已安装 Git（macOS 与 Linux 建议 2.32 及以上；Windows 用户可通过官方安装包获取）
- 能打开终端，基本会用 `cd`、`git status`

## 一、项目概况

### 1.1 它到底是什么

LazyGit 是一个开源的 Git 终端 UI，用 Go 编写，基于 tcell 库绘制界面。它自己不处理 Git 的底层逻辑，而是调用系统的 `git` 可执行文件来完成实际操作——你在界面上做的每一步，对应的都是一条真实的 `git` 命令。

这样做的好处是行为与命令行完全一致：LazyGit 显示的分支、提交、状态就是 `git` 的输出，不引入另一套语义。它替你省下的是「记忆命令 + 敲参数」这部分，而不是改变 Git 本身的行为。

### 1.2 数据口径

以下数据取自 GitHub 仓库，供参考。Stars、Forks 会随时间增长，以仓库页面为准。

| 指标 | 数值（2026-09 核实） |
|------|---------------------|
| 语言 | Go |
| 开源协议 | MIT |
| Stars | 约 8.3 万 |
| Forks | 约 3,000 |
| 最新稳定版 | v0.65.1（2026-09-13 发布） |

## 二、安装与启动

按你的平台选择一种即可。装好后在任一 Git 仓库目录里运行 `lazygit` 就能进入界面；在非仓库目录里运行，默认会弹出询问，让你选择初始化一个新仓库还是打开最近用过的仓库（该行为由配置项 `notARepository` 控制）。

### 2.1 macOS

```sh
brew install lazygit
```

### 2.2 Linux

- **Ubuntu / Debian**：Debian 13（Trixie）、Ubuntu 25.10 及以后的版本已收录官方包，直接安装：

  ```sh
  sudo apt install lazygit
  ```

  更早的版本没有现成 apt 包，走 GitHub Releases 下载预编译二进制。仓库 `Releases` 页面提供 `lazygit_<版本>_Linux_x86_64.tar.gz`，解压后放入 `PATH`：

  ```sh
  sudo install lazygit -D -t /usr/local/bin/
  ```

- **Arch 及其衍生**：lazygit 在官方仓库里，用 pacman 安装；想跟最新分支可以装 AUR 的 `lazygit-git`：

  ```sh
  sudo pacman -S lazygit
  ```

- **其他发行版**：Fedora 系可用社区 COPR 源，openSUSE、Gentoo、NixOS 也各有对应包；都没有时，同样使用 Releases 页面下载对应架构的压缩包，或用 Homebrew 的 Linux 版（`brew install lazygit`）。

### 2.3 从源码安装

适合想改代码或跟进最新分支的场景：

```sh
go install github.com/jesseduffield/lazygit@latest
```

装完确认二进制在 `PATH` 中。Go 版本过低或环境变量未配好时，可先看 `go env GOPATH` 把对应的 `bin` 目录加入 `PATH`。

### 2.4 Windows

通过 Winget 或 Scoop 安装：

```sh
winget install -e --id=JesseDuffield.lazygit
# 或
scoop bucket add extras
scoop install lazygit
```

## 三、界面与导航

### 3.1 五个面板

LazyGit 启动后界面主要分成五个面板，按数字键跳到对应面板：

| 数字键 | 面板 | 作用 |
|--------|------|------|
| `1` | 状态（Status） | 仓库信息、当前分支、检查更新 |
| `2` | 文件（Files） | 工作区改动：暂存区与未暂存文件的增删改 |
| `3` | 分支（Local Branches） | 本地分支，`Enter` 查看某分支的提交 |
| `4` | 提交（Commits） | 提交历史，`Enter` 查看某次提交改动的文件 |
| `5` | 储藏（Stash） | 储藏（stash）列表 |

主面板在右侧，展示当前选中条目的 diff（差异）或操作预览。任意时刻按 `?` 打开当前面板的快捷键帮助。

### 3.2 通用快捷键

这些键在任何面板都有效：

| 键 | 动作 |
|-----|------|
| `?` | 打开 / 关闭当前面板快捷键菜单 |
| `q` | 退出 |
| 数字键 | 跳到对应面板 |
| `P` | 推送当前分支（push） |
| `p` | 拉取当前分支（pull） |
| `R` | 刷新界面（不会执行 `git fetch`） |
| `↑↓` 或 `jk` | 上下移动选中项 |
| `Enter` | 进入选中项（如查看某提交改了什么） |
| `/` | 在当前面板内按文本搜索 |
| `:` | 执行一条自定义 shell 命令 |
| `z` / `Z` | 撤销 / 重做上一次 Git 操作（借助 reflog，只回退提交类操作） |

## 四、文件面板：暂存与提交

文件面板是你最常用的地方，展示所有未提交的改动。选择文件用 `space` 切换暂存状态，`Enter` 进入逐行（line-by-line）暂存视图——这是 LazyGit 比命令行 `git add -p` 顺手的地方。

| 键 | 动作 |
|-----|------|
| `space` | 暂存 / 取消暂存当前文件 |
| `a` | 暂存 / 取消暂存全部文件 |
| `Enter` | 进入逐行暂存视图；在目录上按则展开 / 收起目录 |
| `` ` `` | 在文件树与平铺两种布局间切换 |
| `s` | 储藏全部改动（进入储藏面板） |
| `S` | 打开储藏选项（全部 / 仅已暂存 / 仅未暂存） |
| `d` | 放弃当前文件的改动（弹出选项） |
| `D` | 重置工作区（弹出选项） |
| `c` | 提交暂存的改动 |
| `w` | 提交暂存的改动（跳过 pre-commit 钩子） |
| `A` | 用已暂存的改动补充到最近一次提交（amend） |
| `f` | 拉取远程更新（只 `git fetch`，不改本地分支） |
| `e` | 用系统编辑器打开当前文件 |
| `i` | 把当前文件加入 `.gitignore` |
| `M` | 打开合并冲突选项菜单（有冲突时用） |

逐行暂存视图里，`space` 暂存光标所在的块或行，`a` 在整块（hunk）与单行两种粒度间切换，`Esc` 返回文件面板。这一模式适合做「只提交某个改动的一小部分」这种事。

## 五、提交面板：历史与变基

提交面板列出提交历史。它最强大的能力是交互式变基（`interactive rebase`）——在历史里选定一个起点，然后用一组键对每个提交做 pick / reword / squash / fixup，边看 diff 边改历史。

| 键 | 动作 |
|-----|------|
| `Enter` | 查看选中提交改动的文件清单 |
| `r` | 修改选中提交的提交信息（reword） |
| `s` | 把选中提交压入它下面的（更早的）提交，信息合并保留（squash） |
| `f` | fixup：并入下面的提交但丢弃提交信息 |
| `<ctrl+j>` / `<ctrl+k>` | 把选中提交向下 / 向上移动 |
| `d` | 丢弃选中提交（drop，通过一次变基完成） |
| `e` | 从选中提交开始交互式变基 |
| `i` | 从最新提交到第一个合并提交（或主分支分叉点）的一段提交整体进入交互式变基 |
| `F` | 为选中提交创建 `fixup!` 提交，之后可按 `S` 合并 |
| `S` | 把 `fixup!` 提交合并进目标提交（autosquash） |
| `t` | 还原选中提交（revert） |
| `n` | 基于选中提交新建分支 |
| `C` | 复制选中提交（Cherry-pick，可连续标记多个） |
| `V` | 把已复制的提交粘贴到当前分支 |
| `A` | 用暂存改动补充最近一次提交（amend） |
| `b` | 打开 bisect（二分定位）选项 |

### 5.1 交互式变基流程

要压缩最近三个提交为一个：

1. 进入提交面板（`4`），选中倒数第三个提交。
2. 按 `e`，LazyGit 以该提交为基点启动交互式变基，它及之后的提交都会列出来。
3. 逐个选中要改动的提交，按键标记处理方式：
   `p` pick（保留）、`r` reword（改提交信息）、`s` squash（并入下面的提交并保留信息）、`f` fixup（并入但丢信息）、`d` drop（丢弃）。动作即时生效，不用像命令行那样先编辑 TODO 文件再整体执行。
4. 变基途中按 `m` 可打开变基菜单，选择 Abort 放弃整个变基，回到起点状态。

### 5.2 Cherry-pick 流程

1. 在提交面板选中要复制的提交，按 `C`（大写）。连续对多个提交按 `C` 可以一次复制一批。
2. 切到目标分支，回到提交面板按 `V`（大写）粘贴，复制的提交会依次重放为该分支上的新提交。随时按 `Esc` 可取消复制选择。

### 5.3 Bisect：二分定位坏提交

出了问题不知道哪个提交引入的，不必手动 `git bisect start`。在提交面板按 `b` 打开 bisect 选项：把当前提交标记为好（good）或坏（bad），LazyGit 自动二分切换到中间提交，你再看一眼、再标记一次，反复几轮就能锁定引入问题的提交。定位结束后从同一个菜单里结束 bisect，回到正常状态。

## 六、分支面板

分支面板处理本地分支与远程跟踪。`space` 是切换分支最常用的动作。

| 键 | 动作 |
|-----|------|
| `space` | 切换（checkout）到选中分支 |
| `n` | 新建分支 |
| `c` | 按名字输入并切换到某分支（输入 `-` 可回到上一个分支） |
| `-` | 直接切回上一个分支 |
| `r` | 把当前分支变基到选中分支上 |
| `M` | 把选中分支合并进当前分支（可选普通合并或 squash 合并） |
| `d` | 删除选中分支（弹出选项） |
| `R` | 重命名分支 |
| `u` | 打开上游选项（设置 / 取消 upstream、重置到上游） |
| `f` | 把选中分支从其上游快进 |
| `g` | 打开重置选项（soft / mixed / hard） |
| `o` | 为选中分支创建 Pull Request |
| `T` | 打标签 |
| `w` | 新建 worktree |

实际项目多用「分支 + Rebase」而非频繁合并：切到功能分支，在分支面板按 `r` 变基到 `main`，解决了冲突再推上去，历史是线性的，干净。

## 七、储藏面板

储藏（stash）用于把当前改动临时收起来，切换到别的分支再取回。

| 键 | 动作 |
|-----|------|
| `space` | 应用选中的储藏（不删除它） |
| `g` | 应用并移除选中的储藏（pop） |
| `d` | 删除选中的储藏 |
| `n` | 从选中的储藏新建分支 |
| `r` | 重命名储藏 |
| `Enter` | 查看储藏涉及的文件 |

在文件面板按 `s` 会创建一个储藏并跳到储藏面板；之后随时到这里 `g` 取回。

## 八、配置

默认配置通常够用，只有想改主题或默认行为时才需要写配置文件。

### 8.1 配置文件位置

| 平台 | 全局配置文件 |
|------|--------------|
| Linux | `~/.config/lazygit/config.yml` |
| macOS | `~/Library/Application Support/lazygit/config.yml` |
| Windows | `%LOCALAPPDATA%\lazygit\config.yml` |

另外支持仓库级配置：放在仓库内的 `.git/lazygit.yml` 只对该仓库生效；放在仓库的某个上级目录、命名为 `.lazygit.yml`，则对该目录下的所有仓库都生效，适合给一组相关项目统一设置。仓库级配置会覆盖全局配置。

### 8.2 常用配置项

```yaml
gui:
  # 选中行与活动边框的颜色
  theme:
    activeBorderColor: [green]
    selectedLineBgColor: [blue]

git:
  paging:
    color: always
```

配置是覆盖式的：只写你想改的键，其余用默认值。官方文档的 `Config.md` 列出了全部可配置项，改之前先去那里确认某个键的准确名称，避免填了无效字段。

### 8.3 命令别名

在 `~/.gitconfig` 里加两行，之后用 `git lg` 快速进入：

```ini
[alias]
    lg = lazygit
```

## 九、常见问题

### 9.1 在非仓库目录启动

默认会弹出询问：初始化一个新仓库，还是打开最近用过的仓库。想直接指定目录，用 `lazygit --path <仓库路径>`。该行为也可用配置项 `notARepository` 固化：`create` 直接初始化新仓库，`skip` 直接打开最近仓库。

### 9.2 方向键没反应

多半是焦点停在提交信息、搜索这类输入框里。按 `Esc` 退出输入，再操作列表；界面显示不对劲时按 `R` 强制刷新。

### 9.3 想撤销上一步操作

按 `z` 撤销，LazyGit 通过 `reflog` 推断上一条 Git 命令并回退；按 `Z` 重做。注意它只覆盖提交类操作，工作区里未提交的改动不受影响，别用它处理文件内容层面的误删。

### 9.4 合并冲突怎么处理

冲突发生时，冲突文件会出现在文件面板。`Enter` 进入文件，主面板按段展示冲突：`space` 选用当前段，`b` 两边都保留，`↑↓` 在段之间移动，`←→` 跳到上 / 下一个冲突。选错了按 `z` 撤销刚才的选择；复杂的段落按 `e` 打开编辑器手动改。每解决一个文件就用 `space` 暂存它标记为已解决，全部处理完提交；中途想放弃，按 `m` 打开菜单选择 Abort。

### 9.5 版本和快捷键对不上

LazyGit 迭代较快，个别键位会变。以界面内 `?` 实时帮助为准，其次是官方 `Keybindings_en.md`。本文章程以 v0.65 为准。

## 十、自测

**1.** 文件面板里，`space` 和 `a` 各自做什么？进入逐行暂存视图的键是哪个？

<details><summary>参考答案</summary>

`space` 暂存或取消暂存当前选中的文件；`a` 暂存或取消暂存全部文件。`Enter`（选中某个文件时）进入逐行暂存视图。

</details>

**2.** 想把最近三次提交压缩成一个，完整操作顺序是什么？

<details><summary>参考答案</summary>

进入提交面板，选中倒数第三个提交；按 `e` 进入交互式变基，把最后两个提交的动作改为 `s`（squash，或 `f` fixup），动作即时生效，变基完成后三条历史合成一条。

</details>

**3.** 你在功能分支上，想把主分支的改动并到自己这边，用分支面板的哪个键？与 `M` 有何不同？

<details><summary>参考答案</summary>

按 `r` 把当前分支变基到选中分支（这里选中主分支）；`M` 是把选中的分支合并进当前分支。前者重写历史为线性，后者保留合并提交。

</details>

**4.** 一个文件既有你不想提交的改动，也想提交其中一部分，怎么做？

<details><summary>参考答案</summary>

在文件面板选中该文件按 `Enter` 进入逐行暂存视图，用 `space` 只暂存想提交的块或行，回到文件面板按 `c` 提交，剩下的改动留在工作区。

</details>

## 练习

**练习 1**：在任意仓库里完成一次「暂存 → 提交 → 推送」。要求：只用 `space`、`c`、`P`（`P` 是 push，`p` 才是 pull）完成，不敲一条 `git commit`、`git push`。

**练习 2**：新建两个提交，然后在提交面板选中最新的那个按 `s`，把它压入下面的提交。确认两条历史合成一条，提交信息合并保留。

**练习 3**：用 `z` 撤销练习 2 的变基操作，确认提交历史恢复到压缩前。

## 资料口径

本文数据与快捷键基于官方 GitHub 仓库 `jesseduffield/lazygit` 的 README、`docs/keybindings/Keybindings_en.md`、`docs/Config.md` 与 Releases 页面（v0.65.1，2026-09 核实）。Stars、Forks 随时间增长；键位随版本演进，以界面内 `?` 帮助为最终依据。未验证的功能未写入本文。

## 相关资源

- 官方仓库：https://github.com/jesseduffield/lazygit
- 官方快捷键文档：https://github.com/jesseduffield/lazygit/blob/master/docs/keybindings/Keybindings_en.md
- 官方配置文档：https://github.com/jesseduffield/lazygit/blob/master/docs/Config.md
- 更新日志：https://github.com/jesseduffield/lazygit/releases