---
title: "Atuin：29.1K Stars·加密同步的Shell历史管理器"
date: "2026-04-12T01:56:00+08:00"
slug: atuin-shell-history-manager-guide
description: "Atuin 是一款用 Rust 编写的 Shell 历史管理器，用 SQLite 替换文本文件历史，支持端到端加密同步。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "Shell", "历史管理", "SQLite", "加密"]
---

# Atuin：29.1K Stars·加密同步的 Shell 历史管理器·Rust 编写

## 项目概述

Atuin 是一款用 Rust 编写的 Shell 历史管理器，它用 SQLite 数据库替换了 Shell 原有的文本文件历史记录。除了记录命令本身，Atuin 还会额外记录命令的上下文信息，包括退出码、工作目录、主机名、会话 ID 和命令执行时长等。

Atuin 的核心亮点在于提供了可选的端到端加密同步功能。用户可以选择使用 Atuin 官方托管的服务器、自建服务器，或者完全不使用同步功能。由于所有历史同步都是加密的，服务器运营者无法访问用户的命令历史数据。

## 快速上手

### 安装

Atuin 支持多种安装方式，最简单的是使用官方安装脚本：

```bash
curl --proto '=https' --tlsv1.2 -LsSf https://setup.atuin.sh | sh
```

其他安装方式包括：

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

# 组合筛选：查找昨天下午3点后所有成功的 make 命令
atuin search --exit 0 --after "yesterday 3pm" make
```

## 核心功能

### 全局加密同步

Atuin 支持在多台机器间同步 Shell 历史，所有数据传输前都会在本地加密，确保隐私安全：

```bash
# 注册账号（使用官方服务器）
atuin register -u <USERNAME> -e <EMAIL>

# 或使用自建服务器
ATUIN_HOST=https://my-atuin-server.com atuin register -u <USERNAME> -e <EMAIL>

# 手动同步
atuin sync
```

自建服务器非常适合企业内网使用，详细部署指南请参考官方文档。

### 命令统计

查看最常用的命令：

```bash
atuin stats
```

输出示例：

```
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

## 支持的 Shell

Atuin 目前支持以下 Shell：

| Shell | 支持级别 | 说明 |
|--------|----------|------|
| zsh | 完整支持 | 首选推荐 |
| bash | 完整支持 | 需要 bash-preexec |
| fish | 完整支持 | 原生支持 |
| nushell | 完整支持 | 实验性支持 |
| xonsh | 完整支持 | 实验性支持 |
| powershell | 次级支持 | 可能有 bug |

## 配置选项

Atuin 的配置文件位于 `~/.config/atuin.toml`（Linux/macOS）或 `%APPDATA%\atuin\atuin.toml`（Windows）。

### 同步配置

```toml
[sync]
host = "https://api.atuin.sh"  # Atuin 官方服务器
# host = "https://my-server.com"  # 自建服务器
# key = "your-encryption-key"      # 端到端加密密钥
```

### 快捷键配置

```toml
[keybindings]
up = "ctrl-r"          # 搜索历史
up = "up"               # 方向键上也可以
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

## 数据导入

Atuin 支持从多种历史格式导入数据：

```bash
# 自动检测格式导入
atuin import auto

# 指定格式导入
atuin import bash
atuin import zsh
atuin import fish
atuin import nu

# 从文件导入
atuin import < ~/.zsh_history
```

## 数据库结构

Atuin 使用 SQLite 存储历史记录。数据库文件通常位于：

- Linux: `~/.local/share/atuin/history.db`
- macOS: `~/Library/Application Support/atuin/history.db`
- Windows: `%APPDATA%\atuin\history.db`

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

## 自建服务器

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

### vs-fzf

fzf 是 Shell 的模糊查找工具，Atuin 可以与 fzf 配合使用，也可以完全替代它。Atuin 的优势在于完整的数据库存储和同步功能。

### vs-eshell/history

Zsh 的 eshell 也有类似功能，但 Atuin 支持更多 Shell 和加密同步。

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