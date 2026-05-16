---
title: "witr：回答「这个进程为什么在跑」的因果溯源工具"
date: 2026-05-16T19:45:00+08:00
slug: "witr-agentic-task-runner"
description: "witr 是一个用 Go 编写的进程溯源工具，通过构建因果链回答「这个进程为什么在跑」这个问题。它整合 systemd、Docker、SSH 会话等多种来源，以人类可读的叙事风格展示进程的完整启动链路，并提供交互式 TUI 面板。"
draft: false
categories: ["技术笔记"]
tags: ["Go", "系统诊断", "进程管理", "开源工具", "TUI"]
---

## 项目概览

**witr**（Why Is This Running?）是一个开源进程溯源工具，作者是 [pranshuparmar](https://github.com/pranshuparmar)。截至 2026 年 5 月，该项目在 GitHub 上拥有约 **16,523** 颗 Stars，是近期 GitHub Trending 榜单上的热门项目。

项目以一个简洁却深刻的问题为核心：**为什么这个进程在跑？**

传统系统工具（`ps`、`top`、`lsof`、`systemctl`）告诉你 _what_——有什么在运行、占用哪个端口。但它们无法回答 _why_——这个进程是怎么被启动的，谁是它的上级Supervisor，它为什么会出现在这里。

**witr** 填补了这个空白。

---

## 核心问题与解决思路

当一个进程运行时，它背后总有一个因果链：

- `systemd` 启动了某个服务
- `pm2` 托管了一个 Node.js 应用
- Docker 容器里跑着一条命令
- SSH 会话里用户执行了某个脚本
- 某个 cron 定时任务触发了

这些链条在传统工具里是断裂的——你需要手动关联 `ps` 输出和 `systemctl show` 结果，才能拼凑出一个完整的故事。

**witr 的解决方案：** 给定任意进程名、PID、端口或文件，它自动构建并展示这个因果链。

---

## 工作原理

### 输入方式

witr 支持四种定位方式，可以混合使用：

| 方式 | 示例 | 说明 |
|------|------|------|
| **进程名** | `witr node` | 子串模糊匹配 |
| **PID** | `witr --pid 14233` | 精确 PID 查询 |
| **端口** | `witr --port 5000` | 查看占用端口的进程 |
| **文件** | `witr --file /var/log/app.log` | 查看持有某文件的进程 |

### 输出示例

```bash
witr node
```

```
Target      : node

Process     : node (pid 14233)
User        : pm2
Command     : node index.js
Started     : 2 days ago (Mon 2025-02-02 11:42:10 +05:30)
Restarts    : 1

Why It Exists :
  systemd (pid 1) → pm2 (pid 5034) → node (pid 14233)

Source      : pm2

Working Dir : /opt/apps/expense-manager
Git Repo    : expense-manager (main)
Listening   : 127.0.0.1:5001
```

这个输出清晰展示了：`systemd` → `pm2` → `node` 的完整链路，并且给出了工作目录、Git 仓库和监听地址等上下文信息。

### 多种输出模式

- `--short`：只显示因果链
- `--tree`：树状展示进程族谱
- `--json`：JSON 格式，便于脚本集成
- `--env`：显示进程的环境变量
- `--verbose`：显示扩展信息
- `--warnings`：只显示警告信息

```bash
witr --port 5000 --short
# 输出: systemd (pid 1) → PM2 v5.3.1: God (pid 1481580) → python (pid 1482060)
```

### 退出码

witr 提供有意义的退出码，便于在脚本和 CI 中使用：

| 退出码 | 含义 |
|--------|------|
| 0 | 找到进程，无警告 |
| 1 | 找到进程，但有警告 |
| 2 | 未找到匹配进程 |
| 3 | 权限不足 |
| 4 | 输入无效或匹配模糊 |

---

## 交互式 TUI 模式

不加任何参数运行 `witr`（或加 `-i`）会启动交互式 TUI 面板，提供：

- **实时进程列表**：可排序、可过滤
- **端口视图**：查看开放端口及持有进程
- **进程详情面板**：查看完整祖先树、子进程、环境变量、工作目录
- **进程操作**：发送信号（Kill、Terminate、Pause、Resume）或 Renice 进程
- **鼠标支持**：可用鼠标导航和点击

---

## 溯源能力覆盖

witr 会检测并展示进程来源，以下类型均被支持：

| 来源类型 | Linux | macOS | Windows | FreeBSD |
|----------|:-----:|:-----:|:-------:|:-------:|
| systemd 单元 | ✅ | - | - | - |
| launchd 服务 | - | ✅ | - | - |
| Windows 服务 | - | - | ✅ | - |
| Docker 容器 | ✅ | ✅ | ✅ | ✅ |
| Podman | ✅ | ✅ | ✅ | ✅ |
| Kubernetes (Kubepods) | ✅ | ✅ | ✅ | ✅ |
| SSH 远程会话 | ✅ | ✅ | ✅ | ✅ |
| tmux / screen 会话 | ✅ | ✅ | ❌ | ✅ |
| cron 定时任务 | ✅ | ✅ | ❌ | ❌ |
| PM2 / Supervisor | ✅ | ✅ | ✅ | ✅ |
| Snap / Flatpak | ✅ | ❌ | ❌ | ❌ |

**警告信息**也是 witr 的亮点——它会检测：

- 以 root 运行
- 持有危险 Linux capabilities（如 `CAP_SYS_ADMIN`）
- 在公网接口（`0.0.0.0`）监听
- 二进制文件已被删除（deleted binary）
- 高内存占用（>1GB RSS）
- 长时间运行（>90 天）

---

## 安装方式

witr 提供极度广泛的安装渠道：

### 快速安装（Unix）

```bash
curl -fsSL https://raw.githubusercontent.com/pranshuparmar/witr/main/install.sh | bash
```

### 包管理器

```bash
# Homebrew
brew install witr

# Conda
conda install -c conda-forge witr

# npm (跨平台)
npm install -g @pranshuparmar/witr

# Winget (Windows)
winget install -e --id PranshuParmar.witr

# Arch Linux (AUR)
yay -S witr-bin
```

### Go 安装

```bash
go install github.com/pranshuparmar/witr/cmd/witr@latest
```

### Nix / Pixi

```bash
# Nix
nix run github:pranshuparmar/witr

# Pixi
pixi exec witr
```

---

## 适用场景与优势

**适用场景：**

- 调试生产环境进程，发现某个不知名进程占用端口
- 排查服务重启原因，判断是 systemd 定时触发还是手动重启
- 了解长期运行进程的来源，判断是否应该继续运行
- 应急响应时快速建立进程上下文

**优势：**

- 零配置，下载即用
- 单一二进制，支持 Linux/macOS/Windows/FreeBSD
- 输出人类可读，紧急情况下也能快速理解
- 支持脚本化（JSON 输出、有意义退出码）

**边界（不属于 witr 的能力）：**

- 不是监控工具（不持续采集指标）
- 不是性能分析器（不提供 CPU/内存趋势）
- 不是修复工具（只读，不做修改）

---

## 总结

witr 回答了一个看似简单却极其实用的问题：**「这个进程为什么在跑？」** 它通过整合系统多层级的溯源信息（Supervisor、容器、会话、定时器），将原本需要手动关联多个工具才能得到的信息，一次性以叙事风格呈现。

无论是日常调试还是突发事件应急，witr 都能帮你省下大量「拼凑线索」的时间。项目目前维护活跃，支持四种平台和十余种包管理器，安装门槛极低。

**仓库链接：** https://github.com/pranshuparmar/witr