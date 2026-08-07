---
title: "tuicr：终端里的代码审查利器，用 Vim 快捷键搞定 GitHub/GitLab 审查"
date: 2026-08-07T03:24:02+08:00
draft: true
categories: ["技术笔记"]
tags: ["Rust", "代码审查", "TUI", "开发工具"]
description: "tuicr 是一个用 Rust 编写的终端代码审查工具，支持 Vim 快捷键、GitHub/GitLab/Bitbucket 三平台推送、git/jj/hg 三种 VCS（版本控制系统），以及跨 session 的审查状态持久化。"
slug: tuicr-code-review-tui
github_repo: "agavra/tuicr"
source_key: "gh:agavra/tuicr"

---

# tuicr：终端里的代码审查利器，用 Vim 快捷键搞定 GitHub/GitLab 审查

## 一句话判断

tuicr（读作 *tweaker*）是一个用 Rust 编写的终端代码审查 TUI（Text-based User Interface，文本终端界面），把"在浏览器里点 PR review"这件事搬进终端：GitHub 风格的连续 diff（按行级展示代码改动的视图）、Vim 全套快捷键、行内/范围/文件级注释、原生推送评论到 GitHub / GitLab / Bitbucket 三平台，对 git、jj（Jujutsu）、mercurial 三种 VCS 同样友好。最新版本 v0.21.0（2026-08-05），MIT 协议，单静态二进制。

## 项目概览

| 维度 | 事实 |
|------|------|
| 仓库 | `agavra/tuicr` |
| 语言 | Rust |
| 协议 | MIT |
| 官网 | [tuicr.dev](https://tuicr.dev/) |
| 最新版本 | v0.21.0（2026-08-05） |
| GitHub Stars / Forks | 2.4k+ / 189+ |
| 安装形态 | 单静态二进制，无运行时依赖 |

tuicr 的设计目标很明确：让"代码审查"这个高频但又被打断的工作流，回到键盘上——不离开终端、不打开浏览器、不会被上百个 tab 淹没。开发者从 `tuicr` 一个命令开始，到 `:submit` 把整个审查推回 PR 页，中间全程在 TUI 里完成。

## 安装

四种主流安装方式，按场景挑：

```bash
# 一键脚本（Linux / macOS）
curl -fsSL tuicr.dev/install.sh | sh

# Homebrew（macOS / Linux）
brew install tuicr

# Cargo
cargo install tuicr

# Mise
mise use github:agavra/tuicr

# Nix（临时运行）
nix run github:agavra/tuicr

# 从源码
git clone https://github.com/agavra/tuicr.git
cd tuicr
cargo install --path .
```

更新也是一行：

```bash
tuicr update          # 升级到最新版
tuicr update 0.18.0   # 回滚或安装指定版本
```

`tuicr update` 会探测当前二进制由谁管理（Homebrew / Cargo / Mise / Nix / 直接下载），并走对应通道升级；install-script 与手动下载的二进制走原地替换，且会做 SHA-256 校验。

## 快速上手

四种典型调用形式，覆盖了日常工作流的所有入口：

```bash
tuicr                  # 从 commit 选择器开始
tuicr -w               # 直接审查未提交更改（跳过选择器）
tuicr pr 125           # 拉取 GitHub PR #125 进行审查
tuicr mr 125           # 拉取 GitLab MR #125
tuicr --stdout         # 管道输出到 stdout（用于脚本/agent 集成）
tuicr review list      # 列出本机已保存的审查 session
```

VCS 自动检测顺序：**jj → git → hg**（jj 仓库底层仍是 Git）。如果你的工作目录是 Jujutsu 仓库，tuicr 会直接读 jj 的 change set，不必先 `jj git export`。

第一次进 TUI 的工作循环只有三步：

1. 用 `j` / `k` / `Ctrl-d` / `Ctrl-u` / `g` / `G` 在 diff 流里穿梭，`{` / `}` 跳到上/下一个文件，`[` / `]` 跳到上/下一个 hunk（一个连续的改动块）。
2. 光标停在目标行按 `c`，写注释；多行范围按 `v` 进入 visual mode 选区再写；整文件 `C`；review-level（整份审查的总结意见）用 `;c`。
3. 写完按 `y` 复制结构化 markdown 到剪贴板，或 `:submit` 直接推送到 GitHub / GitLab / Bitbucket。

## 核心能力

### 1. GitHub 风格的连续 diff

不切窗口、不分 tab，所有改动文件在同一屏连续滚动，按 GitHub PR 的视觉习惯排版。配合相对行号（`relative_line_numbers = true`）和 Vim 的 `{N}G` 跳转，可以从 500 行的长 diff 里瞬间定位到目标行。

### 2. PR 级别的注释模型

注释不是字符串，而是有"靶位"的对象：

| 靶位 | 触发 |
|------|------|
| 单行注释 | 光标停在行上，按 `c` |
| 多行范围 | `v` 进入 visual mode 选区，按 `c` |
| 整文件注释 | `C` |
| Review-level 总结 | `;c` |

每条注释还可以打类型标签（comment type）：`issue` / `suggestion` / `note` / `praise` 四种内置类型，可在配置里新增自定义类型并指定颜色。`Tab` 键在写注释时切换类型。

### 3. 跨 session 的审查持久化

审查状态按文件 / hunk 粒度写到本地 session 文件，下次打开同一 PR 时：

- 已经审过的 commit 在内联选择器里标 ✓
- 重新打开同一 PR 时，会预选比"上次已提交审查"更新的 commit（GitHub / GitLab 支持；Bitbucket 不记录 approval 覆盖的 commit，故不支持此预选）

也就是说，**审查进度是真正可中断、可恢复的**——昨天没审完的 PR，今天 `tuicr pr 125` 一打开直接接着干。

### 4. 三种导出目标

**A. 推到远程平台（`:submit`）**

- GitHub：Comment / Approve / Request changes / Draft 四种动作，内联评论作为真实 PR review 落点，review-level 评论变成 review summary。需要 `gh` 已认证到目标仓库。
- GitLab：Comment / Approve / Request changes（需你是 assigned reviewer）。需要 `glab` 已认证。Draft 不可用，自托管实例需看 `docs/GITLAB.md`。
- Bitbucket Cloud：Comment / Approve 两档，内联评论支持多行范围。需要 `bkt` 已认证到 `bitbucket.org`。Request changes / Draft 未支持；Bitbucket Data Center 不在范围内。

**B. 复制 markdown 到剪贴板（`y` 或 `:clip`）**

每条注释带编号 + 类型 + 文件/行锚点：

```markdown
I reviewed your code and have the following comments. Please address them.

1. `src/auth.rs` — Consider adding unit tests
2. `src/auth.rs:42` — Magic number should be a named constant
3. `src/auth.rs:50-55` — This block could be refactored
```

粘贴给 Claude / Codex / Cursor / 任何 LLM 都能直接消费——这是为 "agent loop"（AI 编程助手循环工作流）准备的出口。

**C. Pipe 到 stdout（`--stdout`）**

```bash
tuicr --stdout > review.md
tuicr --stdout | pbcopy
```

把 markdown 流给任何下游：CI 作业、自家脚本、再 `pbcopy` 一轮。

### 5. 三 VCS 同源

`jj`（Jujutsu）、`git`、`hg`（Mercurial）三套版本控制都接，自动检测。Mercurial 在同类工具里几乎是 tuicr 独家支持——hunk、lumen、`gh pr review`、`git diff` 都不接 hg。

### 6. Agent skill 集成

仓库自带 `skills/tuicr/SKILL.md`，把 `/tuicr` skill 投喂给 Claude Code 或 Codex 后，agent 会在 tmux / Zellij / Herdr 分屏里自动开 tuicr；你审完按 `y`，评论自动回到 agent 会话。对 "agent 写代码，人在 TUI 里 review" 的工作流是开箱即用。

## 配置与主题

配置文件路径：

- Linux / macOS：`~/.config/tuicr/config.toml`
- Windows：`%APPDATA%\tuicr\config.toml`

一份最小配置长这样：

```toml
theme = "catppuccin-mocha"
diff_view = "side-by-side"   # 或 "unified"
ignore_whitespace = false    # 本地 VCS diff 是否忽略所有空白
appearance = "system"        # 或 "dark" / "light"
mouse = true
leader = ";"                 # leader 前缀键
comment_vim = false          # 注释输入框是否走 vim modal
relative_line_numbers = false
review_watch_interval_ms = 1000  # 持久化审查轮询间隔，0 = 禁用

[[comment_types]]
id = "issue"
color = "red"
definition = "must fix before merge"
```

### 内置主题（20+）

`dark` / `light` / `ayu-light` / `ayu-mirage` / `onedark` / `github-light` / `github-dark` / `catppuccin-latte` / `catppuccin-frappe` / `catppuccin-macchiato` / `catppuccin-mocha` / `everforest-dark` / `everforest-light` / `gruvbox-dark` / `gruvbox-light` / `nord-dark` / `nord-light` / `nord-dark-high-contrast` / `nord-light-high-contrast` / `solarized-light` / `solarized-dark` / `tokyo-night-storm` / `tokyo-night-day`。

### 自定义主题

设置 `theme = "my-theme"` 或 `tuicr --theme my-theme`，然后在 `~/.config/tuicr/themes/my-theme.toml` 写一份。还可以挂自定义语法高亮 `syntax_theme = "my-syntax.tmTheme"`。

仓库 `examples/tuicr-teal.toml` + `examples/tuicr-teal-syntax.tmTheme` 给了一份完整可抄的范例。

完整选项与解析优先级参见 `docs/CONFIG.md`，`.tuicrignore` 规则同文档。

## 快捷键速查

第一次进 TUI 用得到的最常用键：

| 键 | 动作 |
|------|------|
| `j` / `k` | 上下移动 |
| `Ctrl-d` / `Ctrl-u` | 半页滚动 |
| `g` / `G` / `{N}G` | 顶 / 底 / 第 N 行 |
| `{` / `}` | 上 / 下一个文件 |
| `[` / `]` | 上 / 下一个 hunk |
| `m` / `M` | 上 / 下一条注释 |
| `/` | 搜索当前焦点面板（diff / 文件树 / 帮助，大小写不敏感） |
| `i` / `e`（文件树） | 按正则 include / exclude 过滤文件 |
| `c` / `C` | 单行 / 整文件注释 |
| `v` / `V` | visual mode 范围选择 |
| `r` / `R` | 标记文件 / hunk 为已审查 |
| `e` / `:edit` | 在 `$EDITOR` 打开当前文件 |
| `y` | 复制审查到剪贴板 |
| `:submit` | 推送到 GitHub / GitLab / Bitbucket |
| `?` | 切换完整帮助 |

TUI 内按 `?` 随时拉出完整参考。

## 与其他工具的对比

README 给出的对照表（社区维护的可验证事实，截至 v0.21.0）：

| 能力 | tuicr | hunk | lumen | gh pr review | git diff |
|------|:---:|:---:|:---:|:---:|:---:|
| TUI diff viewer | ✅ | ✅ | ✅ | ❌ | ❌ |
| TUI 内写注释 | ✅ | ✅ | ✅ | ❌ | ❌ |
| Vim 快捷键（完整模型） | ✅ | ❌ | partial¹ | ❌ | ❌ |
| 推 inline review 到 GitHub | ✅ | ❌ | ❌ | partial² | ❌ |
| 推 inline review 到 GitLab | ✅ | ❌ | ❌ | ❌ | ❌ |
| 推 inline review 到 Bitbucket | ✅ | ❌ | ❌ | ❌ | ❌ |
| Agent-ready markdown 导出 | ✅ | via CLI skill | ❌ | ❌ | ❌ |
| git | ✅ | ✅ | ✅ | ❌ | ✅ |
| jj | ✅ | ✅ | ✅ | ❌ | ❌ |
| Mercurial | ✅ | ❌ | ❌ | ❌ | ❌ |
| 单静态二进制 | ✅ | needs Node | ✅ | ✅ | ✅ |

¹ lumen 只有 `j` / `k` 导航，没有 visual mode、`{N}G`、`Ctrl-d` / `Ctrl-u` 这些更广义的 Vim 模型。
² `gh pr review` 只能在 review-level 发 approve / comment / request-changes，没有行内注释。

**tuicr 的独占领地**：完整 Vim 模型 × 三平台推送 × 三 VCS × 单静态二进制。其它工具最多覆盖其中两条。

## 适用场景

按工作流挑：

- **习惯 Vim / tmux 的后端 / 基础设施工程师**：审查 diff 时不需要离开终端，j/k 一路翻，c 写注释，`:submit` 走人。整段操作不进浏览器。
- **重度 jj / Mercurial 用户**：同类工具对这两种 VCS 支持稀疏，tuicr 是少数同时接住的。
- **跨平台团队**（GitHub + GitLab + Bitbucket 混用）：不用为不同平台切换不同工具，一份配置、一套快捷键通吃。
- **AI agent 协作流**：把 `/tuicr` skill 喂给 Claude Code 或 Codex，让 agent 自己开 TUI 分屏；你审完 `y` 一按，结构化评论回灌给 agent，闭环。
- **离线 / 远程开发场景**：没有浏览器的环境（容器、SSH、低带宽终端）下，本地 diff + 写好注释 → `y` 复制 → 联机时粘贴提交，或 `:submit` 在认证可用时直推。

不适合的场景：需要图片对比、复杂合并冲突图、跨多仓库联邦 diff 的超大规模 review——这类仍建议 GitHub / GitLab Web。

## 资源

- 仓库：[github.com/agavra/tuicr](https://github.com/agavra/tuicr)
- 官网：[tuicr.dev](https://tuicr.dev/)
- 安装脚本：[tuicr.dev/install.sh](https://tuicr.dev/install.sh)
- Crates：[crates.io/crates/tuicr](https://crates.io/crates/tuicr)
- 文档：`docs/CONFIG.md` / `docs/KEYBINDINGS.md` / `docs/GITLAB.md` / `docs/BITBUCKET.md` / `docs/REVIEW_CLI.md`
- Agent skill：`skills/tuicr/SKILL.md`