---
title: "smux：一键 tmux 配置，让 AI Agent 操控终端"
date: 2026-03-29T21:00:00+08:00
slug: "smux-tmux-ai-agent-setup"
description: "深入解读 smux 项目，一键配置 tmux 环境，支持 Option 键绑定、鼠标操作、窗格标签，并提供 tmux-bridge CLI 实现 AI Agent 间的跨窗格通信。"
draft: false
categories: ["技术笔记"]
tags: ["tmux", "终端", "AI Agent", "自动化", "Claude Code"]
---

# smux：一键 tmux 配置，让 AI Agent 操控终端

> 一文读懂 smux：让 AI Agent 与人类共享同一个终端

**学习目标**

学完本文后，你将掌握：
- 理解 smux 的核心设计理念：为什么需要一个 AI 与人类共用的终端配置
- 掌握 smux 的安装与基本使用方法
- 熟练使用 tmux-bridge 实现 AI Agent 间的跨窗格通信
- 能够配置 Claude Code、Codex 等 AI Agent 使用 tmux-bridge
- 理解 agent-to-agent 工作流的实际应用场景

---

## 一、项目概述

### 1.1 是什么

[smux](https://github.com/ShawnPana/smux) 是一个**一键安装的 tmux 配置**，专门为 AI Agent 时代设计。它不仅仅是给人类用的终端配置，更重要的是**让 AI Agent 能够读、写、控制终端**。

### 1.2 核心价值

| 特性 | 说明 |
|------|------|
| **一键安装** | `curl -fsSL https://shawnpana.com/smux/install.sh \| bash` |
| **人类友好** | Option 键绑定、鼠标支持、窗格标签 |
| **Agent 可控** | tmux-bridge CLI 让任何 Agent 都能操控终端 |
| **跨 Agent 通信** | Claude Code 可以与 Codex 在不同窗格中对话 |

### 1.3 项目数据

- ⭐ 393 Stars | 21 Forks | 24 Commits
- 语言：Shell 100%
- 许可证：MIT
- 主要贡献者：ShawnPana、Claude

---

## 二、安装与配置

### 2.1 一键安装

```bash
curl -fsSL https://shawnpana.com/smux/install.sh | bash
```

安装脚本会自动检测你的系统并安装：
- **tmux**：如果尚未安装（通过 Homebrew、apt、dnf、pacman 或 apk）
- **tmux.conf**：配置 Option 键绑定、鼠标支持、窗格标签、最小化状态栏
- **tmux-bridge**：用于跨窗格 Agent 通信的 CLI 工具

所有文件都存放在 `~/.smux/` 目录下。

### 2.2 系统要求

| 要求 | 说明 |
|------|------|
| **操作系统** | macOS（需要 Homebrew）或 Linux |
| **tmux 版本** | 3.2+（自动安装） |

### 2.3 更新与卸载

```bash
# 更新 smux
smux update

# 卸载 smux
smux uninstall
```

---

## 三、基础快捷键

smux 的所有快捷键都使用 **Option（Alt）键**，无需按前缀键。

### 3.1 窗格操作（Panes）

| 快捷键 | 操作 |
|--------|------|
| `Option + i/k/j/l` | 向上/下/左/右导航（不循环） |
| `Option + n` | 新建窗格（分裂 + 自动平铺） |
| `Option + w` | 关闭当前窗格 |
| `Option + o` | 切换布局 |
| `Option + g` | 标记当前窗格 |
| `Option + y` | 与标记的窗格交换位置 |

### 3.2 窗口操作（Windows）

| 快捷键 | 操作 |
|--------|------|
| `Option + m` | 新建窗口 |
| `Option + u` | 切换到下一个窗口 |
| `Option + h` | 切换到上一个窗口 |

### 3.3 滚动模式（Scrolling）

| 快捷键 | 操作 |
|--------|------|
| `Option + Tab` | 开启/关闭滚动模式 |
| `i / k` | 上/下滚动 |
| `Shift + I / K` | 半页上/下滚动 |
| `q` 或 `Escape` | 退出滚动模式 |

### 3.4 鼠标支持（Mouse）

- **点击**：选择窗格
- **拖拽**：选择文本（自动复制到剪贴板）
- **滚轮**：滚动内容

---

## 四、核心功能：tmux-bridge

### 4.1 什么是 tmux-bridge

tmux-bridge 是一个 CLI 工具，**让任何能运行 bash 的工具**（Claude Code、Codex、Gemini CLI、Shell 脚本等）都能读、写、控制 tmux 窗格。

### 4.2 命令详解

| 命令 | 说明 |
|------|------|
| `tmux-bridge list` | 显示所有窗格（目标、进程、标签） |
| `tmux-bridge read <target> [lines]` | 从窗格读取最后 N 行 |
| `tmux-bridge type <target> <text>` | 向窗格输入文本（不按回车） |
| `tmux-bridge keys <target> <key>...` | 发送按键（Enter、Escape、C-c 等） |
| `tmux-bridge name <target> <label>` | 给窗格设置标签 |
| `tmux-bridge resolve <label>` | 通过标签查找窗格 |
| `tmux-bridge id` | 打印当前窗格的 ID |

### 4.3 使用示例

```bash
# 读取名为 codex 的窗格的最后 20 行
tmux-bridge read codex 20

# 向 codex 窗格输入 "review src/auth.ts"
tmux-bridge type codex "review src/auth.ts"

# 向 codex 窗格发送回车键
tmux-bridge keys codex Enter
```

### 4.4 典型工作流

```
1. 在一个窗格运行 Claude Code
2. 在另一个窗格运行 Codex
3. Claude Code 使用 tmux-bridge 向 Codex 发送任务
4. Codex 执行后，结果返回给 Claude Code
5. 两个 Agent 协同完成复杂任务
```

---

## 五、AI Agent 集成

### 5.1 安装 smux Skill

要让你的 AI Agent 学会使用 tmux-bridge，运行：

```bash
npx skills add ShawnPana/smux
```

### 5.2 支持的 Agent

smux 兼容 **40+ 种 AI Agent**，包括：
- Claude Code
- Codex
- Cursor
- Copilot
- Gemini CLI
- 等等

### 5.3 Claude Code + Codex 协同示例

**场景**：让 Claude Code 指挥 Codex 审查代码

**步骤 1**：设置环境
```bash
# 安装 smux
curl -fsSL https://shawnpana.com/smux/install.sh | bash

# 安装 smux skill
npx skills add ShawnPana/smux
```

**步骤 2**：在两个窗格启动 Agent
```bash
# 终端上半部分：Claude Code
claude

# 终端下半部分：Codex
codex
```

**步骤 3**：Claude Code 使用 tmux-bridge 指挥 Codex
```
# Claude Code 发送指令
tmux-bridge type codex "review src/auth.ts"
tmux-bridge keys codex Enter

# Codex 执行完后，Claude Code 读取结果
tmux-bridge read codex 50
```

**步骤 4**：Claude Code 分析 Codex 的反馈，继续对话或修复

---

## 六、为什么需要 smux

### 6.1 传统方案的问题

在没有 smux 之前，AI Agent 操控终端的方式很有限：

| 方案 | 问题 |
|------|------|
| **SSH 远程连接** | 需要额外配置、安全性问题 |
| **Docker 容器** | 资源占用大、启动慢 |
| **tmux 直接控制** | 人类无法同时使用 |
| **pTTY 模拟** | 实现复杂、不稳定 |

### 6.2 smux 的创新

smux 通过 **tmux-bridge** 实现了：
- **共享终端**：人类和 Agent 共用同一个 tmux 会话
- **隔离执行**：Agent 在独立窗格中运行，不影响人类工作
- **灵活通信**：通过 CLI 实现任意 Agent 间的通信
- **即插即用**：支持 40+ 种 Agent，无需复杂配置

### 6.3 核心洞察

> smux 的本质是**重新定义人类与 AI Agent 在终端的协作模式**。

在过去，人类是终端的唯一主人。在 AI Agent 时代，终端变成了**人类与 Agent 的共享空间**。

---

## 七、实际应用场景

### 7.1 代码审查

```
Claude Code（人类视角）→ Codex（自动化审查）→ 结果汇总
```

Claude Code 可以指挥 Codex 审查代码，自己做最终决策。

### 7.2 复杂任务分解

```
主 Agent（规划）→ 子 Agent（执行）→ 主 Agent（汇总）
```

主 Agent 将任务分解后，分配给多个子 Agent 并行执行。

### 7.3 对话式编程

```
人类 ↔ Claude Code ↔ Codex
```

人类与 Claude Code 对话，Claude Code 与 Codex 协作，形成三角协作模式。

### 7.4 自动化测试

```
Claude Code（测试计划）→ Codex（编写测试）→ 运行测试
```

Claude Code 负责规划，Codex 负责实现，自动化完成整个测试流程。

---

## 八、常见问题

### Q: 为什么需要用 Option 键而不是 Ctrl 键？

A: Option 键在 macOS 上很少被程序使用，冲突少。而且 `Option + 方向键` 是 macOS 终端的标准操作，用户体验一致。

### Q: tmux-bridge 安全吗？

A: tmux-bridge 只是读写 tmux 窗格的内容，不涉及系统级操作。但建议在受信任的环境中使用，避免恶意 Agent 操控终端。

### Q: 支持 Windows 吗？

A: 目前主要支持 macOS 和 Linux。Windows 用户可以通过 WSL（Windows Subsystem for Linux）使用。

### Q: 如何调试 tmux-bridge？

A: 使用 `tmux-bridge list` 查看所有窗格状态，确认窗格名称和进程是否正确。

---

## 九、总结

smux 不仅仅是一个 tmux 配置，更是一个**人类与 AI Agent 共享终端的解决方案**。

**核心价值：**
- 一键安装，开箱即用
- Option 键绑定，符合人体工程学
- tmux-bridge 实现跨窗格通信
- 支持 40+ 种 AI Agent
- MIT 许可证，完全开源

**适用场景：**
- 代码审查与重构
- 复杂任务分解与执行
- 对话式编程
- 自动化测试流水线

---

## 十、资源链接

| 资源 | 链接 |
|------|------|
| GitHub 仓库 | https://github.com/ShawnPana/smux |
| 官方安装脚本 | https://shawnpana.com/smux/install.sh |
| smux Skill | `npx skills add ShawnPana/smux` |
| tmux 官网 | https://tmux.github.io/ |
| Homebrew | https://brew.sh/ |
