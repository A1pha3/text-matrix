---
title: "Atuin：29.1K Stars·加密同步的Shell历史管理器"
date: "2026-04-12T01:56:00+08:00"
slug: atuin-shell-history-manager-guide
description: "Atuin 是一款用 Rust 编写的 Shell 历史管理器，用 SQLite 替换文本文件历史，支持端到端加密同步。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "Shell", "历史管理", "SQLite", "加密"]
---

# Atuin：把 Shell 历史从纯文本升级成可加密同步的数据库

Shell 自带的历史是一行一行的纯文本，没有退出码、没有目录、没有主机信息，更没有跨机器同步。Atuin 用 SQLite 替换这套机制，把每条命令连同它的上下文一起存进数据库，再通过端到端加密在多台机器间同步。Atuin 把 Shell 历史从纯文本升级成结构化数据，搜索、统计、加密同步都建立在这个基础上。

> 文中提到的 29.1K Stars 为 2026 年 4 月初的统计时点数据，实际数值请以 [GitHub 仓库](https://github.com/atuinsh/atuin) 当前显示为准。

接下来从安装配置走到自建服务器，覆盖日常使用和进阶部署两条路径，最后给出采用顺序和适用边界。

## 学习目标

读完本文后，你应能完成以下任务：

- 说明 Atuin 用 SQLite 替换纯文本历史的动机，以及结构化存储带来的查询能力提升
- 完成从安装、注册、导入历史到开启同步的完整初始化流程
- 描述一条命令从本地敲下到在另一台机器被搜索召回的全过程，指出加密发生在哪一步
- 调整 `~/.config/atuin.toml` 中的同步、快捷键、忽略规则等常用配置项
- 判断自己的场景是否需要自建同步服务器，并完成 Docker 部署
- 评估 Atuin 与 fzf、Shell 自带 history 的适用边界，做出合理选型

## 目录

- [功能总览](#功能总览)
- [快速上手](#快速上手)
- [一条命令的完整旅程](#一条命令的完整旅程)
- [核心功能](#核心功能)
- [配置详解](#配置详解)
- [数据存储](#数据存储)
- [自建同步服务器](#自建同步服务器)
- [与其他工具对比](#与其他工具对比)
- [采用建议与适用边界](#采用建议与适用边界)
- [常见问题](#常见问题)
- [自测题](#自测题)
- [安装速查](#安装速查)

## 功能总览

| 维度 | Shell 自带历史 | Atuin |
|------|---------------|-------|
| 存储格式 | 文本文件（`~/.bash_history` 等） | SQLite 数据库 |
| 记录字段 | 命令文本 | 命令、退出码、目录、主机、会话、时长 |
| 跨机器同步 | 无 | 端到端加密同步 |
| 搜索 | 线性 grep / `Ctrl+R` | 全屏交互搜索 + 多维筛选 |
| Shell 支持 | 各 Shell 独立 | zsh / bash / fish / nushell 等统一 |
| 自建服务 | 不适用 | 支持 Docker 部署 |

## 快速上手

### 安装

Atuin 支持多种安装方式，最简单的是使用官方安装脚本：

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

安装完成后，注册 Atuin 账号并同步历史：

```bash
atuin register -u <USERNAME> -e <EMAIL>
atuin import auto
atuin sync
```

然后重启 Shell 使配置生效。

### 基础使用

Atuin 提供了全屏历史搜索界面，通过快捷键 `Ctrl+R`（可自定义）呼出：

```bash
# 搜索历史命令
atuin search <关键词>

# 按退出码筛选
atuin search --exit 0

# 按时间筛选
atuin search --after "yesterday 3pm"

# 组合筛选：查找昨天下午 3 点后所有成功的 make 命令
atuin search --exit 0 --after "yesterday 3pm" make
```

## 一条命令的完整旅程

为了理解 Atuin 的工作机制，跟踪一条命令从敲下到在另一台机器上被搜索到的全过程：

1. **本地记录**：在 zsh 中敲下 `npm test`，Atuin 的 shell 钩子（通过 `precmd` 和 `preexec`）捕获命令文本、当前工作目录、主机名、会话 ID，命令结束后再补上退出码和执行时长。
2. **写入数据库**：这条记录被写入本地 SQLite 数据库 `~/.local/share/atuin/history.db`，即使离线也能正常工作。
3. **加密上传**：执行 `atuin sync` 时，本地数据用注册时生成的密钥加密，再上传到配置的同步服务器（官方或自建）。服务器只看到密文，无法解读命令内容。
4. **另一台机器拉取**：在另一台已登录同一账号的机器上执行 `atuin sync`，从服务器拉取加密数据。
5. **本地解密**：拉取的密文用本地密钥解密，合并进本地数据库。
6. **搜索召回**：在这台机器上按 `Ctrl+R`，输入 `npm test`，Atuin 从本地数据库按相关性返回结果，并显示退出码、目录、时间等上下文。

整个过程中，服务器始终无法访问明文命令。即使官方服务器被入侵，攻击者拿到的也只是加密后的密文。

## 核心功能

### 全局加密同步

Atuin 支持在多台机器间同步 Shell 历史，所有数据传输前都会在本地用注册时生成的密钥加密，服务器只存储密文，无法解读命令内容：

```bash
# 注册账号（使用官方服务器）
atuin register -u <USERNAME> -e <EMAIL>

# 或使用自建服务器
ATUIN_HOST=https://my-atuin-server.com atuin register -u <USERNAME> -e <EMAIL>

# 手动同步
atuin sync
```

> **注意**：`ATUIN_HOST` 环境变量名待以官方文档为准确认；自建服务器场景下，注册前需先指向自建地址。加密密钥在注册时自动生成，可用 `atuin key` 查看，请妥善备份——密钥丢失后历史数据无法解密。

自建服务器适合企业内网或对数据主权有要求的场景，下文"自建同步服务器"一节给出 Docker 部署的最小配置。

### 命令统计

查看最常用的命令：

```bash
atuin stats
```

输出示例：

```text
Welcome to Atuin stats!

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
    ...
```

### Shell 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+R` | 打开全屏历史搜索 |
| `↑` / `↓` | 在历史列表中导航 |
| `Enter` | 执行选中的命令 |
| `Tab` | 在编辑器中修改命令 |
| `Alt+数字` | 快速跳转到历史记录 |
| `Ctrl+C` | 退出搜索 |

### 支持的 Shell

Atuin 目前支持以下 Shell：

| Shell | 支持级别 | 说明 |
|--------|----------|------|
| zsh | 完整支持 | 首选推荐 |
| bash | 完整支持 | 需要 bash-preexec |
| fish | 完整支持 | 原生支持 |
| nushell | 完整支持 | 实验性支持 |
| xonsh | 完整支持 | 实验性支持 |
| powershell | 次级支持 | 可能有 bug |

## 配置详解

Atuin 的配置文件位于 `~/.config/atuin.toml`（Linux/macOS）或 `%APPDATA%\atuin\atuin.toml`（Windows）。配置格式是 TOML，所有选项都有默认值，文件里只需要写需要调整的部分。

### 同步配置

```toml
[sync]
host = "https://api.atuin.sh"  # Atuin 官方服务器
# host = "https://my-server.com"  # 自建服务器时取消注释并替换地址
key = "your-encryption-key"  # 端到端加密密钥
```

> **注意**：`key` 字段在注册时由 Atuin 自动生成，不要手动填写占位字符串。用 `atuin key` 命令查看当前密钥；换机器同步时需导入同一密钥才能解密历史数据。如果密钥丢失，已加密的历史无法恢复，只能重新生成密钥并重新同步。

### 快捷键配置

```toml
[keybindings]
# up = "ctrl-r"  # 触发搜索的快捷键（默认 Ctrl+R，按需自定义）
```

### 历史过滤模式

在搜索界面中使用 `Ctrl+R` 切换过滤模式：

| 模式 | 说明 |
|------|------|
| 全局 | 搜索所有历史 |
| 会话 | 仅当前终端会话 |
| 目录 | 仅当前目录 |
| 工作区 | 当前 Git 仓库的工作区 |

### 忽略规则

```toml
[history]
# 忽略以空格开头的命令
ignore_blank = true

# 忽略特定命令
ignore_cmd = ["exit", "clear", "bg"]

# 忽略特定目录
ignore_dir = ["/tmp", "/var/log"]

# 忽略子字符串
ignore_substring = ["password=", "secret="]
```

## 数据存储

Atuin 选择 SQLite 而不是继续用文本文件，是因为 Shell 历史天然适合结构化查询——按退出码、目录、时间筛选用 SQL 一句就能完成，文本文件要做到同样效果需要外部工具和复杂管道。

数据库文件通常位于：

- Linux: `~/.local/share/atuin/history.db`
- macOS: `~/Library/Application Support/atuin/history.db`
- Windows: `%APPDATA%\atuin\history.db`

### 数据库结构

数据库 schema 核心表：

```sql
CREATE TABLE IF NOT EXISTS history (
    id TEXT PRIMARY KEY,
    timestamp INTEGER NOT NULL,
    hostname TEXT NOT NULL,
    cwd TEXT NOT NULL,
    command TEXT NOT NULL,
    exit_status INTEGER,
    duration INTEGER,
    session TEXT NOT NULL,
    deleted INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL
);
```

`cwd` 记录命令执行时的工作目录，`exit_status` 和 `duration` 让筛选能精确到"在某目录下失败的命令"或"耗时超过阈值的命令"，这些是纯文本历史无法提供的维度。

### 数据导入

Atuin 支持从多种历史格式导入数据：

```bash
# 自动检测格式导入
atuin import auto

# 指定格式导入
atuin import bash
atuin import zsh
atuin import fish
atuin import nu
```

> **注意**：早期文档中曾出现 `atuin import < ~/.zsh_history` 的写法，该重定向语法在新版本中已不推荐，正确做法是使用 `atuin import zsh` 让 Atuin 自动定位并读取 `~/.zsh_history`。如果历史文件不在默认路径，可参考 `atuin import --help` 查看自定义路径的选项。

## 自建同步服务器

官方同步服务器对个人使用足够，但企业团队或对数据主权有要求的场景，自建服务器更合适。Atuin 的服务器组件用 Rust 写成，可以单二进制运行，也支持容器部署。

### Docker 部署

```bash
docker run -d \
  --name atuin-server \
  -p 8888:8080 \
  -v atuin-data:/store \
  -e ATUIN_SECRET_KEY=<your-secret-key> \
  ghcr.io/atuinsh/atuin
```

### Docker Compose 部署

```yaml
version: '3'
services:
  atuin:
    image: ghcr.io/atuinsh/atuin
    container_name: atuin
    restart: unless-stopped
    ports:
      - "8888:8080"
    volumes:
      - atuin-data:/store
    environment:
      - ATUIN_SECRET_KEY=<your-secret-key>
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 3s
      retries: 3

volumes:
  atuin-data:
```

### 环境变量配置

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ATUIN_PORT` | 服务端口 | `8080` |
| `ATUIN_DB_PATH` | 数据库路径 | `/store/history.db` |
| `ATUIN_SECRET_KEY` | 加密密钥（必填） | - |
| `ATUIN_MAX_REQUEST_SIZE` | 最大请求大小 | `10485760` (10MB) |
| `ATUIN_REQUEST_LIMIT_PER_MINUTE` | 每分钟限制 | `240` |

## 与其他工具对比

### vs fzf

fzf 是 Shell 的模糊查找工具，Atuin 可以与 fzf 配合使用，也可以完全替代它。Atuin 的优势在于完整的数据库存储和同步功能；fzf 的优势是轻量、通用，能模糊匹配任意输入流。如果只需要单机搜索且已习惯 fzf 的交互，两者可以并存。

### vs Shell 自带 history + HIST_IGNORE_DUPS

Zsh 和 Bash 自带的 `history` 命令配合 `HIST_IGNORE_DUPS`、`HIST_IGNORE_SPACE` 等选项能解决去重和敏感命令过滤，但仍然是纯文本存储，没有退出码、目录、主机等上下文，也无法跨机器同步。Atuin 在这些维度上做了补齐，代价是引入一个本地数据库和可选的同步服务。

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
2. 注册账号开启官方同步，验证多机器同步是否符合预期。
3. 如果对数据主权有要求，再部署自建服务器，切换同步地址。
4. 最后按需调整忽略规则和快捷键，让 Atuin 融入既有工作流。

## 常见问题

**同步失败怎么办？**

先检查网络和服务器地址，再确认账号是否登录。`atuin status` 能看到当前同步状态，`atuin key` 能查看本地密钥。如果密钥丢失，历史数据无法解密，只能重新生成密钥并重新同步。

**换机器后历史没同步过来？**

新机器需要先 `atuin login` 用同一账号登录，再 `atuin sync` 拉取。如果启用了端到端加密，必须导入原来的密钥才能解密历史数据。

**不想用同步功能可以吗？**

可以。Atuin 完全支持纯本地模式，只用作 SQLite 历史搜索工具。配置文件里把 `auto_sync` 设为 `false` 即可。

**和 fzf 的历史搜索冲突吗？**

不冲突。Atuin 默认接管 `Ctrl+R`，如果更习惯 fzf 的交互，可以在配置里把 Atuin 的快捷键改成别的，两者并存。

## 自测题

以下问题用于检验对本文内容的理解，建议先自己作答再对照正文：

1. **存储动机**：Atuin 选择 SQLite 而不是继续用文本文件，根本原因是什么？请举出一个纯文本历史无法直接完成、但 SQL 一句就能搞定的查询场景。
2. **加密链路**：在"一条命令的完整旅程"中，加密发生在哪一步？服务器拿到的是明文还是密文？换机器同步时为什么必须导入原密钥？
3. **导入语法**：要把 `~/.zsh_history` 里的历史导入 Atuin，正确的命令是什么？为什么不用 `atuin import < ~/.zsh_history`？
4. **配置取舍**：`ignore_substring = ["password=", "secret="]` 这条忽略规则解决什么问题？如果只配 `ignore_blank = true` 是否足够保护敏感命令？
5. **同步失败排查**：执行 `atuin sync` 报错，你会按什么顺序检查？至少列出三个排查方向。
6. **选型判断**：一位同事只用单台 macOS 机器，对 `Ctrl+R` 已经满意，且公司禁止任何外部同步服务。他是否需要安装 Atuin？理由是什么？

### 进阶路径

掌握本文内容后，可以继续探索以下方向：

- 阅读 [Atuin 官方文档](https://docs.atuin.sh)，了解搜索语法（如 `--before`、`--cwd`、`--exit` 组合）和自定义主题
- 研究自建服务器的高可用部署：配合 PostgreSQL 后端、反向代理和 TLS 证书
- 探索 Atuin 与其他 Shell 工具的集成：如 starship 提示符、direnv、tmux 会话管理
- 关注 Atuin 的 `atuin search` 命令行模式，将其嵌入脚本实现历史命令的自动化分析

## 安装速查

```bash
# 一键安装
curl --proto '=https' --tlsv1.2 -LsSf https://setup.atuin.sh | sh

# Homebrew
brew install atuin

# 注册并启用同步
atuin register -u <USERNAME> -e <EMAIL>
atuin import auto
atuin sync

# 重启 Shell
```

## 参考链接

- GitHub：https://github.com/atuinsh/atuin
- 官网：https://atuin.sh
- 文档：https://docs.atuin.sh
- 论坛：https://forum.atuin.sh/
- Discord：https://discord.gg/Fq8bJSKPHh
