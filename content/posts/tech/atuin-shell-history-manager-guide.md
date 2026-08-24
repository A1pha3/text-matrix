---
title: "Atuin：加密同步的 Shell 历史管理器"
date: "2026-04-12T01:56:00+08:00"
slug: atuin-shell-history-manager-guide
github_repo: "atuinsh/atuin"
description: "Atuin 用 SQLite 替换纯文本 Shell 历史，记录退出码、目录、主机等上下文，并支持端到端加密同步。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "SQLite", "加密"]
---

# Atuin：把 Shell 历史从纯文本升级成可加密同步的数据库

读完后你能做到：

- 说清 Atuin 与 Shell 自带历史在存储、字段、同步、搜索上的差异，判断自己是否需要它。
- 安装并初始化 Atuin，导入现有历史，用 `Ctrl+R` 和 `atuin search` 找回带上下文的命令。
- 理解加密同步的链路，备份 `atuin key`，在新机器登录并解密同步的数据。
- 按需调整过滤规则、自建 `atuin-server`，并依据适用边界决定是否采用。

Shell 自带的 `Ctrl+R` 和 `~/.bash_history` 只能告诉你"敲过什么"，说不清"在哪敲的、成了没有、花了多久"。Atuin 用 SQLite 替换这套纯文本机制，把每条命令连同退出码、目录、主机、会话、时长一起存进数据库，再通过端到端加密在多台机器间同步。历史变成结构化数据后，按退出码、目录、时间筛选就是一条 SQL 的事，不再需要 `grep` 和管道的组合。

Atuin 以 Rust 编写，仓库排在 GitHub [atuinsh/atuin](https://github.com/atuinsh/atuin)（Stars 约 3.1 万，2026-08-07 验证）。本文按"它在解决什么 → 一条命令怎么流过系统 → 并行机制 → 自建服务器 → 选型判断"展开，结尾给出采用顺序和适用边界。

## 它和 Shell 自带历史差在哪

两者核心差异集中在存储、字段、同步和搜索四个维度，先看这张对照表再进入细节：

| 维度 | Shell 自带历史 | Atuin |
|------|---------------|-------|
| 存储格式 | 文本文件（`~/.bash_history` 等） | SQLite 数据库 |
| 记录字段 | 命令文本 | 命令、退出码、目录、主机、会话、时长 |
| 跨机器同步 | 无 | 端到端加密同步 |
| 搜索 | 线性 `grep` / `Ctrl+R` | 全屏交互搜索 + 多维筛选 |
| Shell 支持 | 各 Shell 独立 | zsh / bash / fish / nushell 等统一 |
| 自建服务 | 不适用 | 支持独立 `atuin-server` 二进制 |

```mermaid
flowchart LR
    A[Shell 钩子<br/>precmd / preexec] --> B[本地 SQLite<br/>history.db]
    B --> C{同步?}
    C -->|启用| D[端到端加密<br/>Sync 服务器]
    C -->|关闭| E[纯本地模式]
    D --> F[其他机器<br/>atuin login + sync]
    B --> G[全屏搜索 UI<br/>Ctrl+R]
```

两条主线并行：本地数据库负责记录和搜索，同步链路在加密后才把数据送出去。下文先讲记录，再讲同步，最后讲自建服务器。

## 一条命令的完整旅程

一条命令从敲下到在另一台机器被搜索到，经过六个步骤：

1. **本地记录**：在 zsh 敲下 `npm test`，Atuin 的 shell 钩子（zsh 用 `precmd` / `preexec`）捕获命令文本、工作目录、主机名、会话 ID，命令结束后补上退出码和执行时长。
2. **写入数据库**：写入本地 SQLite `~/.local/share/atuin/history.db`，离线也能正常工作。
3. **加密上传**：执行 `atuin sync` 时，数据用注册时生成的密钥加密，再上传到同步服务器。服务器只看得到密文。
4. **另一台机器拉取**：在另一台已登录同一账号的机器上执行 `atuin sync`，从服务器拉取加密数据。
5. **本地解密**：拉取的密文用本地密钥解密，合并进本地数据库。
6. **搜索召回**：按 `Ctrl+R`，输入 `npm test`，Atuin 从本地数据库返回结果，附带退出码、目录、时间等上下文。

这条链路里，服务器始终只拿到密文。即使官方服务器被入侵，攻击者能拿到的也只有加密后的历史，没有本地密钥就无法还原命令内容。

## 快速上手

### 前置条件

- 一台类 Unix 系统（macOS / Linux），Shell 为 zsh、bash 或 fish 之一。
- 有 `curl` 或 `brew` 等包管理器可执行安装。
- 若打算用官方同步，需要能访问外网；纯本地模式可离线使用。

### 安装

官方安装脚本适合首次试用：

```bash
curl --proto '=https' --tlsv1.2 -LsSf https://setup.atuin.sh | sh
```

其他安装方式：

```bash
# Homebrew (macOS/Linux)
brew install atuin

# Nix/NixOS
nix-env -iA nixpkgs.atuin

# Arch Linux
pacman -S atuin

# FreeBSD
pkg install atuin
```

### 初始化配置

安装完成后，注册账号、导入现有历史并触发首次同步：

```bash
atuin register -u <USERNAME> -e <EMAIL>
atuin import auto
atuin sync
```

然后重启 Shell 使配置生效。注册时 Atuin 会生成一把加密密钥并保存在本地，用 `atuin key` 可以查看。这把密钥是解密历史的关键，请妥善备份——丢了它，已加密的历史无法恢复。

### 基础使用

Atuin 提供两个搜索入口：交互式全屏搜索（`Ctrl+R` 呼出）用方向键实时翻找，命令行搜索（`atuin search`）适合写进脚本或精确筛选。

全屏搜索界面里几个键很常用：

- `Enter` 直接执行选中的命令。
- `Tab` 只把命令带回编辑框，不立即执行，方便先改再跑。
- `Alt+数字` 跳到对应序号的结果。
- `Ctrl+R` 循环切换过滤模式（见下文"搜索过滤模式"）。

命令行搜索按需组合过滤参数：

```bash
# 搜索历史命令
atuin search <关键词>

# 只看当前目录跑过的命令
atuin search --cwd . <关键词>

# 只看某台机器的历史
atuin search --host <主机名> <关键词>

# 只看成功的命令（--exit 0）或失败的（--exit 1）
atuin search --exit 0 <关键词>
atuin search --exit 1 <关键词>

# 按时间筛选，看昨天下午 3 点之后的
atuin search --after "yesterday 3pm"

# 组合：昨天下午 3 点后所有成功的 make 命令
atuin search --exit 0 --after "yesterday 3pm" make
```

最后一个组合是官方文档在 README 里直接给出的示例，能同时按退出码、时间和命令文本过滤，纯文本历史做不到。想复盘某次"在某目录下失败的构建"，`atuin search --cwd <项目目录> --exit 1` 一句就能定位，不用再靠 `grep` 加管道的组合。

### 验证安装

跑一遍简单命令确认记录链路通了：

```bash
atuin --version  # 确认二进制可执行
ls -la                # 制造一条历史记录
atuin search ls       # 应能搜到刚执行的 ls
```

若 `atuin search ls` 搜不到刚才的命令，先确认是否把 Atuin 的钩子加进了 Shell 配置（zsh 是 `.zshrc`，bash 是 `.bashrc`），并重启了 Shell。

## 核心机制：加密同步

Atuin 的同步在本地完成加密，服务器只负责存储和转发密文。同步配置有两个关键点：服务器地址和加密密钥。

服务器地址在配置文件的顶层 `sync_address` 字段指定，默认指向官方服务器：

```toml
# ~/.config/atuin/config.toml
sync_address = "https://api.atuin.sh"
```

加密密钥不在配置文件里，而是注册时生成、单独存在 `key_path`（默认 `~/.local/share/atuin/key`），用 `atuin key` 查看。注册的账号密码只用来登录和鉴权，不参与解密；解密依赖的是这把本地密钥。换机器同步时，需要在新机器上先 `atuin login -u <USERNAME>` 输入密码，再配合导入的密钥，才能解密拉到本地的历史。密钥和账号密码分属两套凭证，丢了密钥，即使账号密码还在，已加密的历史也无法还原。

同步默认每小时自动执行一次，可用 `sync_frequency` 调整；手动同步用 `atuin sync`，发现漏数据时用 `atuin sync -f` 触发全量同步，把历史数据完整过一遍。

## 命令统计

`atuin stats` 基于数据库里的命令记录，统计最常用的命令，以及按时间段分布的调用频率：

```bash
atuin stats
```

```text
Commands:
    git            4821
    ls             2342
    vim            1234
    cd             987
    npm            876
    docker         654

Hours of the day:
    00:00 - 04:00 ████░░░░░░░░░░░░░░░░░░░ 12%
    04:00 - 08:00 ████████░░░░░░░░░░░░░░░░░░ 23%
```

## 支持的 Shell

zsh、bash、fish 成熟稳定；nushell 和 xonsh 处于实验性支持；PowerShell 的支持成熟度低于前几个。核心差异在钩子机制：zsh 原生提供 `precmd` / `preexec`，Atuin 直接挂载；bash 不自带这类钩子，需要先装 `bash-preexec` 才能正常记录命令，官方安装脚本会一并处理。Windows 通过 PowerShell 使用，数据目录走 `%APPDATA%\atuin`。

## 配置详解

Atuin 的配置文件位于 `~/.config/atuin/config.toml`（Windows 为 `%APPDATA%\atuin\config.toml`）。配置格式是 TOML，所有选项都有默认值，文件里只需要写需要调整的部分。

### 搜索过滤模式

在搜索界面中按 `Ctrl+R` 可以循环切换过滤范围。官方支持的过滤模式比"全局/目录"更细，包括：

| 模式 | 说明 |
|------|------|
| global | 从全部历史搜索（默认） |
| host | 只在本机历史中搜索 |
| session | 仅当前终端会话 |
| directory | 仅当前目录 |
| workspace | 当前 Git 仓库的工作区 |
| session-preload | 当前会话 + 会话开始前的全局历史 |

过滤模式可以在配置里用 `filter_mode` 指定默认值，也可用 `[search] filters` 控制循环切换时包含哪些模式。

### 忽略规则

官方用正则表达式控制哪些命令不入库，而不是简单的开关列表。两处过滤点：

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

此外，Atuin 默认开启了 `secrets_filter`，会识别并跳过一批内置的敏感模式——AWS 密钥 ID、GitHub PAT、Slack token、Stripe 密钥、云环境变量（`AWS_ACCESS_KEY_ID` 等）——避免这些信息被意外记入历史并同步到服务器。改完过滤规则后，可用 `atuin prune` 把已入库的旧条目按新规则清掉。

## 数据存储

Atuin 用 SQLite 替代文本文件，原因在于 Shell 历史天然带结构——退出码、目录、主机、会话、时长都是命令的属性，按这些维度筛选时，SQL 一句就能完成；文本文件要做到同样效果，得靠 `awk`、`grep` 和临时脚本的组合，且无法保证一致性。

数据库文件默认位于 `~/.local/share/atuin/history.db`（macOS 同样遵循 XDG 路径，数据也存在 `~/.local/share/atuin`，除非被 `XDG_*` 环境变量覆盖）。核心字段对应命令的上下文属性：

| 字段 | 含义 |
|------|------|
| `command` | 命令文本 |
| `cwd` | 执行时的工作目录 |
| `exit_status` | 退出码 |
| `duration` | 执行时长 |
| `hostname` | 主机名 |
| `session` | 终端会话 ID |
| `timestamp` | 执行时间 |

`cwd`、`exit_status`、`duration` 让筛选能精确到"在某目录下失败的命令"或"耗时超过阈值的命令"，这些是纯文本历史无法提供的维度。

### 数据导入

从现有 Shell 历史迁移到 Atuin，可以用自动检测，也可以指定格式：

```bash
# 自动检测格式导入
atuin import auto

# 指定格式导入
atuin import bash
atuin import zsh
atuin import fish
```

早期文档中曾出现 `atuin import < ~/.zsh_history` 的写法，新版本已不推荐此重定向语法，正确做法是使用 `atuin import zsh` 让 Atuin 自动定位并读取 `~/.zsh_history`。历史文件不在默认路径时，参考 `atuin import --help` 查看自定义路径选项。

## 自建同步服务器

官方同步服务器对个人使用足够，但企业团队或对数据主权有要求的场景更适合自建。自 v18.12.0 起，服务器是独立的 `atuin-server` 二进制，不再和客户端 `atuin server` 混在一起。

### 安装与启动

服务器从 GitHub releases 安装独立二进制：

```bash
curl --proto '=https' --tlsv1.2 -LsSf \
  https://github.com/atuinsh/atuin/releases/latest/download/atuin-server-installer.sh | sh
```

然后启动：

```bash
atuin-server start
```

### 配置

服务器的配置文件在 `~/.config/atuin/server.toml`，与客户端的 `config.toml` 分开。核心要求是提供一个数据库连接串，支持 PostgreSQL 14+ 或 SQLite：

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

服务端配置同样支持环境变量，关键参数如下：

| 参数 / 环境变量 | 说明 | 默认值 |
|------|------|--------|
| `host` / `ATUIN_HOST` | 监听地址 | `127.0.0.1` |
| `port` / `ATUIN_PORT` | 端口 | `8888` |
| `open_registration` / `ATUIN_OPEN_REGISTRATION` | 是否接受新用户注册 | `false` |
| `db_uri` / `ATUIN_DB_URI` | PostgreSQL / SQLite 连接串（必填） | 无 |

TLS 不再由 Atuin 内置支持（旧版 `[tls]` 配置已移除），官方建议用 nginx、Caddy 或 Traefik 做反向代理终结 HTTPS。容器部署时，把 `/config` 目录映射为持久化数据卷。

客户端侧，自建服务器时把 `sync_address` 指向自建地址即可，其余加密逻辑不变：

```toml
# ~/.config/atuin/config.toml
sync_address = "https://my-atuin-server.com"
```

## 与其他工具对比

### vs fzf

fzf 是 Shell 的模糊查找工具，Atuin 可以与 fzf 配合使用，也可以完全替代它。两者分工不同：Atuin 背后是带上下文的 SQLite 数据库，能按退出码、目录、主机筛选，并跨机器同步；fzf 是通用的模糊匹配器，输入流是什么就匹配什么，轻量但不存储上下文。单机搜索且已习惯 fzf 交互的场景下，两者可以并存，Atuin 接管 `Ctrl+R`，fzf 留给其他场景。

### vs Shell 自带 history + HIST_IGNORE_DUPS

Zsh 和 Bash 自带的 `history` 命令配合 `HIST_IGNORE_DUPS`、`HIST_IGNORE_SPACE` 等选项能解决去重和敏感命令过滤，但仍然是纯文本存储，没有退出码、目录、主机等上下文，也无法跨机器同步。Atuin 在这些维度上补了字段和同步链路，代价是引入一个本地 SQLite 数据库和可选的同步服务。

## 采用建议与适用边界

**谁适合用 Atuin：**

- 多台机器间切换工作（公司电脑、个人电脑、服务器），需要历史跟着走的人。
- 经常要按目录、退出码、时间回溯命令的场景，纯文本历史搜不动。
- 不希望 Shell 历史明文留在本地或同步服务器上。

**谁可以暂缓：**

- 单台机器干活，对 `Ctrl+R` 已经够用，多机器同步用不上。
- 工作环境严格禁止任何外部同步，只能跑纯本地模式。
- 用的 Shell 还在实验性支持阶段（如老版本 PowerShell），等成熟再说。

**采用顺序建议：**

1. 先在单台机器上安装，导入现有历史，习惯 `Ctrl+R` 的交互。
2. 注册账号开启官方同步，验证 `atuin key` 密钥已备份、多机器同步是否符合预期。
3. 如果对数据主权有要求，再部署自建 `atuin-server`，切换 `sync_address`。
4. 最后按需调整 `history_filter` / `cwd_filter` 和快捷键，把 Atuin 接到既有工作流里。

## 常见问题

**同步失败怎么办？** 先检查网络和服务器地址，再确认账号是否登录。`atuin status` 查看同步状态，`atuin key` 查看本地密钥。密钥丢失后历史数据无法解密，只能重新生成密钥并重新同步。

**换机器后历史没同步过来？** 新机器需要先 `atuin login -u <USERNAME>` 用同一账号登录，输入密码和密钥后再 `atuin sync` 拉取。启用了端到端加密的话，必须导入原来的密钥才能解密历史数据。漏数据时用 `atuin sync -f` 强制全量同步。

**不想用同步功能可以吗？** 可以。Atuin 完全支持纯本地模式，不注册账号、不配置 `sync_address` 即可，配置文件里把 `auto_sync` 设为 `false` 更稳妥。

**和 fzf 的历史搜索冲突吗？** 不冲突。Atuin 默认接管 `Ctrl+R`，如果更习惯 fzf 的交互，可以在配置里把 Atuin 的快捷键改成别的，两者并存。

## 参考链接

- GitHub：https://github.com/atuinsh/atuin
- 官网：https://atuin.sh
- 文档：https://docs.atuin.sh
- 论坛：https://forum.atuin.sh/
- Discord：https://discord.gg/Fq8bJSKPHh