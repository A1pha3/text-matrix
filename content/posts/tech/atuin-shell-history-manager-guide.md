---
title: "Atuin：加密同步的 Shell 历史管理器"
date: "2026-04-12T01:56:00+08:00"
lastmod: "2026-09-08T00:00:00+08:00"
slug: atuin-shell-history-manager-guide
github_repo: "atuinsh/atuin"
source_key: "gh:atuinsh/atuin"
description: "Atuin 用 SQLite 替换纯文本 Shell 历史，记录退出码、目录、主机等上下文，支持端到端加密同步，并能记录 AI Agent 执行的命令。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "SQLite", "加密", "Shell"]
---

# Atuin：把 Shell 历史从纯文本升级成可加密同步的数据库

读完后你能做到：

- 说清 Atuin 与 Shell 自带历史在存储、字段、同步、搜索上的差异，判断自己是否需要它。
- 安装并初始化 Atuin，导入现有历史，用 `Ctrl+R` 和 `atuin search` 找回带上下文的命令。
- 理解加密同步的链路，备份 `atuin key`，在新机器登录并解密同步的数据。
- 把 Claude Code、Codex 这类 AI Agent 执行的命令也记进同一条历史，并按"谁执行的"过滤。
- 按需调整过滤规则、自建 `atuin-server`，并依据适用边界决定是否采用。

Shell 自带的 `Ctrl+R` 和 `~/.bash_history` 只能告诉你"敲过什么"，说不清"在哪敲的、成了没有、花了多久"。Atuin 用 SQLite 替换这套纯文本机制，把每条命令连同退出码、目录、主机、会话、时长一起存进数据库，再通过端到端加密在多台机器间同步。历史变成结构化数据后，按退出码、目录、时间筛选就是一条 SQL 的事，不再需要 `grep` 和管道的组合。

到了 2026 年，这个定位多了一层现实感：越来越多的命令不是你敲的，而是 Claude Code、Codex 这类 Agent 替你执行的。Atuin 从 v18.18.0 起支持通过各 Agent 的 hook 机制记录它们跑过的命令，打上作者标签，默认不混入你自己的搜索结果——Shell 历史第一次能分清"谁干的"。

Atuin 以 Rust 编写，MIT 协议，仓库在 GitHub [atuinsh/atuin](https://github.com/atuinsh/atuin)（Stars 31,563，2026-09-08 快照），最新版本 v18.21.0（2026-08-31 发布）。本文按"它在解决什么 → 一条命令怎么流过系统 → 快速上手 → 加密同步与 Agent 记录 → 自建服务器 → 选型判断"展开，结尾给出采用顺序和适用边界。文中命令与默认值均对照 v18.21.0 源码与官方文档核实。

## 它和 Shell 自带历史差在哪

两者差异集中在存储、字段、同步和搜索四个维度，先看这张对照表再进入细节：

| 维度 | Shell 自带历史 | Atuin |
|------|---------------|-------|
| 存储格式 | 文本文件（`~/.bash_history` 等） | SQLite 数据库 |
| 记录字段 | 命令文本 | 命令、退出码、目录、主机与用户、会话、时长、执行者 |
| 跨机器同步 | 无 | 端到端加密同步 |
| 搜索 | 线性 `grep` / `Ctrl+R` | 全屏交互搜索 + 多维筛选 |
| Shell 支持 | 各 Shell 独立 | zsh / bash / fish（Tier 1）；nushell / xonsh / PowerShell（Tier 2） |
| 自建服务 | 不适用 | 支持独立 `atuin-server` 二进制 |

```mermaid
flowchart LR
    A[Shell 钩子<br/>precmd / preexec] --> B[本地 SQLite<br/>history.db]
    B --> C{同步?}
    C -->|启用| D[端到端加密<br/>Atuin Hub / 自建服务器]
    C -->|关闭| E[纯本地模式]
    D --> F[其他机器<br/>atuin login + sync]
    B --> G[全屏搜索 UI<br/>Ctrl+R / 上箭头]
```

两条主线并行：本地数据库负责记录和搜索，同步链路在加密后才把数据送出去。下文先讲记录，再讲同步，最后讲自建服务器。

## 一条命令的完整旅程

一条命令从敲下到在另一台机器被搜索到，经过六个步骤：

1. **本地记录**：在 zsh 敲下 `npm test`，Atuin 的 shell 钩子（zsh 用 `precmd` / `preexec`）捕获命令文本、工作目录、主机名和用户名、会话 ID，命令结束后补上退出码和执行时长。
2. **写入数据库**：写入本地 SQLite `~/.local/share/atuin/history.db`，离线也能正常工作。同步使用的记录另存于同目录的 `records.db`，`history.db` 是本地查询视图。
3. **加密上传**：执行 `atuin sync` 时，数据用注册时生成的密钥加密，再上传到同步服务器。服务器只看得到密文。
4. **另一台机器拉取**：在另一台已登录同一账号的机器上执行 `atuin sync`，从服务器拉取加密数据。
5. **本地解密**：拉取的密文用本地密钥解密，合并进本地数据库。
6. **搜索召回**：按 `Ctrl+R`，输入 `npm test`，Atuin 从本地数据库返回结果，附带退出码、目录、时间等上下文。

这条链路里，服务器始终只拿到密文。作者在 README 里的原话是：所有历史同步都是加密的，就算他想看你的数据也看不到——而且他真的一点都不想看。即使服务器被入侵，攻击者拿到的也只有密文，没有本地密钥就无法还原命令内容。

命令的来源不止人类。装上 AI Agent 的 hook 之后（下文详述），Agent 执行的命令走同样的链路入库，只是多了一个作者标签——这条旅程对 Agent 命令同样成立。

## 快速上手

### 前置条件

- 一台类 Unix 系统（macOS / Linux）或 Windows，Shell 为 zsh、bash 或 fish 体验最完整。
- 有 `curl` 或 `brew` 等包管理器可执行安装。
- 若打算用官方同步，需要能访问外网；纯本地模式可离线使用。

### 安装

官方安装脚本适合首次试用，它会把二进制装到 `~/.atuin/bin` 并引导你导入历史、注册同步账号；在 CI 或 Dockerfile 里可以加 `--non-interactive` 跳过交互：

```bash
curl --proto '=https' --tlsv1.2 -LsSf https://setup.atuin.sh | sh
```

其他安装方式（按官方安装文档）：

```bash
# Homebrew (macOS/Linux)
brew install atuin

# Cargo，需要较新的 Rust 工具链（最低版本见仓库 Cargo.toml 的 rust-version）
cargo install atuin --locked

# Nix（flake）
nix profile install "github:atuinsh/atuin"

# Arch Linux（extra 仓库）
pacman -S atuin

# Windows（WinGet）
winget install -e Atuinsh.Atuin

# Termux（Android）
pkg install atuin
```

官方文档还列出了 MacPorts、mise、XBPS、zinit 等渠道。注意一点：如果不走安装脚本而是手动装二进制，还需要自行配置 shell 插件（例如 zsh 是 `echo 'eval "$(atuin init zsh)"' >> ~/.zshrc`），只装二进制不会开始记录。

### 初始化配置

安装完成后，注册账号、导入现有历史并触发首次同步：

```bash
atuin register -u <USERNAME> -e <EMAIL>
atuin import auto
atuin sync
```

然后重启 Shell 使配置生效。注册时 Atuin 会生成一把加密密钥并保存在本地，用 `atuin key` 可以查看。这把密钥是解密历史的关键，官方文档的措辞是"丢了密钥我们无能为力"，建议放进密码管理器——丢了它，已加密的历史无法恢复。

### 基础使用

Atuin 提供两个搜索入口：交互式全屏搜索（`Ctrl+R` 或上箭头呼出）用方向键实时翻找，命令行搜索（`atuin search`）适合写进脚本或精确筛选。装完 Atuin 后按上箭头不再逐条翻历史，而是直接呼出搜索界面；不习惯的话，可以在 `atuin init` 时加 `--disable-up-arrow` 恢复原行为。

全屏搜索界面里几个键很常用：

- `Enter` 直接执行选中的命令（行为由 `enter_accept` 控制，改为 `false` 则只把命令放回编辑框）。
- `Tab` 只把命令带回编辑框，不立即执行，方便先改再跑。
- `Ctrl+R` 循环切换过滤模式（见下文"搜索过滤模式"）。
- `Ctrl+S` 循环切换搜索模式：模糊（默认）、前缀、全文、daemon 模糊。
- `Alt+数字` 跳到对应序号的结果——macOS 上不可用，官方支持矩阵明确标注了这一限制。

命令行搜索按需组合过滤参数：

```bash
# 搜索历史命令
atuin search <关键词>

# 只看当前目录跑过的命令
atuin search --cwd . <关键词>

# 只看成功的命令（--exit 0）或失败的（--exit 1）
atuin search --exit 0 <关键词>
atuin search --exit 1 <关键词>

# 按时间筛选，看昨天下午 3 点之后的
atuin search --after "yesterday 3pm"

# 组合：昨天下午 3 点后所有成功的 make 命令
atuin search --exit 0 --after "yesterday 3pm" make

# 只看某台主机的历史（过滤模式，而非 --host 参数）
atuin search --filter-mode host <关键词>
```

最后一个组合是官方 README 里直接给出的示例，能同时按退出码、时间和命令文本过滤，纯文本历史做不到。想复盘某次"在某目录下失败的构建"，`atuin search --cwd <项目目录> --exit 1` 一句就能定位。`search` 的参数还有 `--before`、`--limit`、`--offset`、`--reverse`、`--delete` 等，可用 `atuin search --help` 查看全表。

### 验证安装

跑一遍简单命令确认记录链路通了：

```bash
atuin --version  # 确认二进制可执行
ls -la                # 制造一条历史记录
atuin search ls       # 应能搜到刚执行的 ls
```

若 `atuin search ls` 搜不到刚才的命令，先确认是否把 Atuin 的钩子加进了 Shell 配置（zsh 是 `.zshrc`，bash 是 `.bashrc`），并重启了 Shell。VS Code、JetBrains 系 IDE 内置终端常以非交互 shell 启动、不加载你的 Shell 配置，钩子自然没装上——把 IDE 终端改成启动交互 shell（比如 `/bin/bash -i`）即可，这是官方 FAQ 里的第一条。排查更复杂的问题可以用 `atuin doctor`，它收集版本、配置、数据库等诊断信息，官方排障时也会要这份输出。

## 核心机制：加密同步

Atuin 的同步在本地完成加密，服务器只负责存储和转发密文。同步配置有两个关键点：服务器地址和加密密钥。

服务器地址在配置文件的顶层 `sync_address` 字段指定，默认指向官方托管服务 Atuin Hub：

```toml
# ~/.config/atuin/config.toml
sync_address = "https://api.atuin.sh"
```

客户端对官方地址默认使用新的 Hub 认证协议，对自定义地址沿用旧协议，也可以用 `sync_protocol` 显式指定——自建服务器的用户升级后如果同步异常，先检查这个值。

加密密钥不在配置文件里，而是注册时生成、单独存在 `key_path`（默认 `~/.local/share/atuin/key`），用 `atuin key` 查看。注册的账号密码只用来登录和鉴权，不参与解密；解密依赖的是这把本地密钥。换机器同步时，在新机器上 `atuin login -u <USERNAME>`，Atuin 会依次要密码和密钥，两样都对才能解密拉到本地的历史。密钥和账号密码分属两套凭证，丢了密钥，即使账号密码还在，已加密的历史也无法还原；官方也没有密码重置功能，只要还有一台机器处于登录状态，就可以删号重建。

自动同步的节奏由 `sync_frequency` 控制，默认 `5m`——每 5 分钟同步一次，设为 `0` 则每条命令执行完都同步（部分服务器可能对高频同步限流）。手动同步用 `atuin sync`；发现漏数据时用 `atuin sync -f` 触发全量同步，把历史数据完整过一遍，耗时也更长。

另外提一句：没开同步也可能看到 Atuin 每小时连一次 `api.atuin.sh`——那是版本更新检查，不带任何历史数据，介意的话在配置里设 `update_check = false`。

## AI Agent 的命令，也进同一条历史

v18.18.0 起，Atuin 开始把 AI Agent 执行的命令记进同一条历史。各主流 AI 编码 Agent 都有 hook 机制，能在执行 shell 命令前后通知外部工具，Atuin 借此把 Agent 跑的命令记成普通历史条目，只是多写两个字段：执行者（author）和意图（intent）。一条命令是人在终端敲的还是 Agent 替你跑的，数据库里分得清清楚楚。

安装 hook 是一条命令的事，装完重启对应 Agent 生效：

```bash
atuin hook install claude-code   # 写入 ~/.claude/settings.json
atuin hook install codex         # 写入 ~/.codex/hooks.json
atuin hook install opencode      # 写入 ~/.config/opencode/plugins/atuin.ts
atuin hook install pi            # 写入 ~/.pi/agent/extensions/atuin.ts
```

官方支持矩阵列出的 Agent 是 Claude Code、Codex、Copilot、opencode 和 pi。hook 的生命周期和人在终端敲命令完全对称：命令开始前记下命令、目录、时间（等价于 `atuin history start`），结束后补退出码和时长（等价于 `atuin history end`）。只捕获 Bash 类工具调用，写文件、抓网页这些不记。重复执行 `atuin hook install` 是安全的，已装的 hook 会跳过。

搜索时可以按执行者过滤：

```bash
# 默认行为：交互搜索只显示你自己跑的命令，Agent 命令不掺进来
atuin search --author '$all-user'

# 只看 Agent 跑过的命令
atuin search --author '$all-agent'

# 只看 Claude Code 跑的
atuin search --author 'claude-code'
```

这个设计解决的是实际痛点：Agent 干过的活过去散落在它的会话日志里，现在统一进了可搜索的历史，复盘"那天 Claude Code 到底跑了什么命令把环境改坏的"有了着落。

## 命令统计

`atuin stats` 基于数据库里的命令记录做统计，支持限定时间窗口（`today` / `week` / `month` / `year`，或一个具体日期，表示从那一刻起的 24 小时）：

```console
$ atuin stats week
$ atuin stats last friday

+---------------------+------------+
| Statistic           | Value      |
+---------------------+------------+
| Most used command   | git status |
+---------------------+------------+
| Commands ran        |        450 |
+---------------------+------------+
| Unique commands ran |        213 |
+---------------------+------------+
```

不带参数（或 `all`）则统计全部历史，输出同样的三项：最常用命令、命令总数、去重后的命令数。官方文档自述这个功能"目前还比较基础"——它是"最常用命令"级别的概览，做不出按小时分布的可视化报表，需要更细的统计就得直接查 SQLite 了。

## 支持的 Shell 与平台

官方按两级划分支持力度：**Tier 1** 由 Atuin 团队积极维护，是 zsh、bash、fish；**Tier 2** 由社区支持、尽力而为，是 nushell、xonsh 和 PowerShell。Tier 2 的功能覆盖不全：inline 弹出窗口、dotfiles 同步、Atuin AI 这几项，三个 Shell 都有不同程度的缺失（比如 nushell 没有 inline 弹窗）；Windows 平台则没有语法高亮和 pty-proxy。核心差异在钩子机制：zsh 原生提供 `precmd` / `preexec`，Atuin 直接挂载；bash 不自带这类钩子，需要先装 `bash-preexec`，官方安装脚本会一并处理，但 bash-preexec 本身有已知局限（例如前导空格过滤在部分场景失效，见官方 shell 插件文档）。

操作系统方面，Linux x86_64、macOS（arm64 / x86_64）、Windows x86_64 和 WSL-2 都有官方预编译包；macOS 上 `Alt+数字` 快捷跳转不可用。数据目录全平台统一放在用户主目录的 `.local/share/atuin`（可用 `XDG_DATA_HOME` 改到别处），配置文件在 `~/.config/atuin/config.toml`。

## 配置详解

Atuin 的配置文件位于 `~/.config/atuin/config.toml`。配置格式是 TOML，所有选项都有默认值，文件里只需要写需要调整的部分；`atuin default-config` 可以打印一份带注释的完整默认配置作底稿。常用的还有几处：`search_mode` 改默认匹配方式，`inline_height` 把全屏界面改成底部弹出的小窗，`style = "compact"` 换紧凑样式，tmux 用户可以开 `[tmux] enabled = true` 让搜索界面浮在 popup 里。

### 搜索过滤模式

在搜索界面中按 `Ctrl+R` 可以循环切换过滤范围。官方支持六种模式：

| 模式 | 说明 |
|------|------|
| global | 从全部历史搜索（默认） |
| host | 只在本机历史中搜索 |
| session | 仅当前终端会话 |
| directory | 仅当前目录 |
| workspace | 当前 Git 仓库的范围 |
| session-preload | 当前会话 + 会话开始前的全局历史 |

`workspace` 模式需要在配置里开 `workspaces = true`，且不在 Git 仓库里时会自动跳过。过滤模式可以用 `filter_mode` 指定默认值，用 `[search] filters` 控制循环切换时包含哪些模式，上箭头和 `Ctrl+R` 还可以分别用不同的起始模式（`filter_mode_shell_up_key_binding`）。

### 忽略规则

官方用正则表达式控制哪些命令不入库，加上最原始的前导空格约定，一共四种手段：

```toml
# ~/.config/atuin/config.toml
# 匹配的命令不入库（正则非锚定，会匹配命令任意位置）
history_filter = [
    "^secret-cmd",
    "^innocuous-cmd .*--secret=.+"
]

# 匹配的目录不入库（正则非锚定，匹配路径任意位置）
cwd_filter = [
    "^/very/secret/directory",
]
```

`^secret-cmd` 这组示例出自官方配置文档。正则没有锚定，`secret` 会匹配命令中的任何位置，想精确匹配整条命令就自己加上 `^` 和 `$`。更轻的手段是命令前面敲一个空格：多数 Shell 的 ignorespace 约定下，这条命令不会进历史，Atuin 也遵守这个约定（bash + bash-preexec 组合有已知例外，命令不进 Atuin 但可能仍留在 bash 自己的历史文件里）。

在这之外，Atuin 默认开启了 `secrets_filter`，识别并拒绝记录长得像凭证的内容——AWS 密钥、GitHub 和 npm token、Slack webhook、Stripe 密钥等，避免这些信息被意外记入历史并同步出去。改完过滤规则后，已入库的旧条目不会自动消失，用 `atuin history prune` 按新规则清理，先加 `--dry-run` 看会删掉哪些再真删。

## 自建同步服务器

官方托管服务对个人使用足够，但企业团队或对数据主权有要求的场景更适合自建。自 v18.12.0 起，服务器是独立的 `atuin-server` 二进制，不再和客户端混在一个可执行文件里。

### 安装与启动

官方为每次发布提供服务器二进制和安装脚本：

```bash
curl --proto '=https' --tlsv1.2 -LsSf \
  https://github.com/atuinsh/atuin/releases/latest/download/atuin-server-installer.sh | sh

atuin-server start
```

仓库里还有 Docker 镜像、systemd 单元和 Kubernetes 清单，容器化部署不用自己写编排。

### 配置

服务器的配置文件在 `~/.config/atuin/server.toml`，与客户端的 `config.toml` 分开。核心要求是提供一个数据库连接串，支持 PostgreSQL、SQLite 和 MySQL（MySQL 自 v18.21.0 起支持，官方将其列为二档数据库：出了问题修复优先级排在这两家之后）：

```toml
host = "0.0.0.0"
port = 8888
open_registration = true
db_uri = "postgres://user:password@hostname/database"
```

SQLite 则用：

```toml
db_uri = "sqlite:///config/atuin.db"
```

数据库文件不存在时服务器会自动创建。服务端配置同样支持环境变量，关键参数如下：

| 参数 / 环境变量 | 说明 | 默认值 |
|------|------|--------|
| `host` / `ATUIN_HOST` | 监听地址 | `127.0.0.1` |
| `port` / `ATUIN_PORT` | 端口 | `8888` |
| `open_registration` / `ATUIN_OPEN_REGISTRATION` | 是否接受新用户注册 | `false` |
| `db_uri` / `ATUIN_DB_URI` | PostgreSQL / SQLite / MySQL 连接串（必填） | 无 |
| `path` | 所有路由的前缀（挂在反向代理子路径后面时用） | 空 |

自 v17.2.0 加入又移除了内置 TLS 之后，现在的 `atuin-server` 不再自己终结 HTTPS，官方文档的措辞相当直接：不开 TLS，密码就是明文传输，强烈建议在前面挂 nginx、Caddy 或 Traefik 做反向代理。客户端侧把 `sync_address` 指向自建地址即可，加密逻辑不变：

```toml
# ~/.config/atuin/config.toml
sync_address = "https://my-atuin-server.com"
```

## 历史之外：周边能力一览

围绕 Shell 历史，Atuin 已经长出一圈周边，版本号都是这几年的事：`atuin dotfiles` 把别名和环境变量纳入同一套加密同步（v18.1.0）；`atuin kv` 存取小型键值对；`atuin scripts` 管理常用脚本；`atuin wrapped <年份>` 生成年度命令报告（v18.4.0）；`atuin mcp` 以 stdio 方式启动一个 MCP 服务器，把历史搜索暴露给 AI 工具（v18.17.0）；常驻后台的 daemon 提供内存索引和 `daemon-fuzzy` 搜索（v18.13.0 起逐步成型，目前标注为实验性）。这些能力与历史记录共用同步链路，装好 Atuin 之后基本是零成本顺手可用，本文不展开，需要时查官方文档对应章节即可。

## 与其他工具对比

### vs fzf

fzf 是 Shell 的模糊查找工具，Atuin 可以与 fzf 配合使用，也可以完全替代它。两者分工不同：Atuin 背后是带上下文的 SQLite 数据库，能按退出码、目录、执行者筛选，并跨机器同步；fzf 是通用的模糊匹配器，输入流是什么就匹配什么，轻量但不存储上下文。单机搜索且已习惯 fzf 交互的场景下，两者可以并存，Atuin 接管 `Ctrl+R`，fzf 留给其他场景。

### vs Shell 自带 history + HIST_IGNORE_DUPS

Zsh 和 Bash 自带的 `history` 命令配合 `HIST_IGNORE_DUPS`、`HIST_IGNORE_SPACE` 等选项能解决去重和敏感命令过滤，但仍然是纯文本存储，没有退出码、目录、主机等上下文，也无法跨机器同步。Atuin 在这些维度上补了字段和同步链路，代价是引入一个本地 SQLite 数据库和可选的同步服务。

## 采用建议与适用边界

**谁适合用 Atuin：**

- 多台机器间切换工作（公司电脑、个人电脑、服务器），需要历史跟着走的人。
- 经常要按目录、退出码、时间回溯命令的场景，纯文本历史搜不动。
- 重度使用 AI 编码 Agent，想让 Agent 跑过的命令可检索、可审计的团队。
- 不希望 Shell 历史明文留在本地或同步服务器上。

**谁可以暂缓：**

- 单台机器干活，对 `Ctrl+R` 已经够用，多机器同步用不上。
- 工作环境严格禁止任何外部同步，只能跑纯本地模式。
- 主力 Shell 是 nushell、xonsh 或 PowerShell，且依赖的功能恰好在 Tier 2 缺失清单里。

**采用顺序建议：**

1. 先在单台机器上安装，导入现有历史，习惯 `Ctrl+R` 的交互。
2. 注册账号开启官方同步，验证 `atuin key` 密钥已备份、多机器同步是否符合预期。
3. 用 AI Agent 的话，装上对应 hook，确认 Agent 命令入库且默认不干扰你自己的搜索。
4. 如果对数据主权有要求，再部署自建 `atuin-server`，切换 `sync_address`。
5. 最后按需调整 `history_filter` / `cwd_filter` 和快捷键，把 Atuin 接到既有工作流里。

## 常见问题

**同步失败怎么办？** 先检查网络和服务器地址，再确认账号是否登录。`atuin status` 查看同步状态，`atuin key` 查看本地密钥。密钥丢失后历史数据无法解密，官方明确表示无能为力，只能删号重建、重新开始记录。

**换机器后历史没同步过来？** 新机器需要先 `atuin login -u <USERNAME>`，Atuin 会要求密码和密钥，两样都通过后再 `atuin sync` 拉取。端到端加密决定了必须导入原来的密钥才能解密历史数据。漏数据时用 `atuin sync -f` 强制全量同步。自建服务器升级客户端后同步异常，检查 `sync_protocol` 的新旧协议匹配。

**不想用同步功能可以吗？** 可以。不注册账号就能一直纯本地使用；`auto_sync` 虽然默认开启，但没有登录状态时它不会做什么，介意联网行为的把 `auto_sync` 和 `update_check` 都设为 `false` 最干净。

**和 fzf 的历史搜索冲突吗？** 不冲突。Atuin 默认接管 `Ctrl+R` 和上箭头，上箭头可以用 `atuin init <shell> --disable-up-arrow` 还给 Shell；更习惯 fzf 交互的也可以把 Atuin 的快捷键改成别的，两者并存。

**Agent 的命令和我的混在一起了？** 默认不会——交互搜索只显示人类执行的命令。如果用了非默认配置后想找回边界，`atuin search --author '$all-user'` 只看自己的，`--author '$all-agent'` 只看 Agent 的。

**账号能删吗？** 能，`atuin account delete`，注意它不会二次确认，会删掉服务器端的账号和全部历史，本地数据不动。密码忘了也没有重置渠道，前提是至少还有一台机器保持登录。

## 参考链接

- GitHub：https://github.com/atuinsh/atuin
- 官网：https://atuin.sh
- 文档：https://docs.atuin.sh
- 官方托管服务（Atuin Hub）：https://hub.atuin.sh
- 平台支持矩阵：https://docs.atuin.sh/latest/support/
- AI Agent hooks 指南：https://docs.atuin.sh/latest/guide/agent-hooks/
- 自建服务器指南：https://docs.atuin.sh/latest/self-hosting/server-setup/
- 论坛：https://forum.atuin.sh/
- Discord：https://discord.gg/Fq8bJSKPHh
