---
title: "smux：一键 tmux 配置，让 AI Agent 操控终端"
date: "2026-03-29T21:10:00+08:00"
slug: "smux-tmux-ai-agent-setup"
aliases:
  - /posts/tech/smux-tmux-ai-agent-setup/
description: "深入解读 smux 项目，一键配置 tmux 环境，支持 Option 键绑定、鼠标操作、窗格标签，并提供 tmux-bridge CLI 实现 AI Agent 间的跨窗格通信。"
draft: false
categories: ["技术笔记"]
tags: ["tmux", "终端", "AI Agent", "自动化", "Claude Code"]
---

# smux：一键 tmux 配置，让 AI Agent 操控终端

> 预计阅读时间：15 分钟 | 难度：⭐⭐

---

> 一文读懂 smux：让 AI Agent 与人类共享同一个终端

**学习目标**

本文覆盖以下内容：
- 理解 smux 的核心设计理念：为什么需要一个 AI 与人类共用的终端配置
- 掌握 smux 的安装与基本使用方法
- 熟练使用 tmux-bridge 实现 AI Agent 间的跨窗格通信
- 能够配置 Claude Code、Codex 等 AI Agent 使用 tmux-bridge
- 理解 agent-to-agent 工作流的实际应用场景

---

## 一、项目概述

### 1.1 是什么

[smux](https://github.com/ShawnPana/smux) 是一个**一键安装的 tmux 配置**，专门为 AI Agent 时代设计。它既是给人类用的终端配置，也**让 AI Agent 能够读、写、控制终端**。

### 1.2 价值

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
```textbash
# 更新 smux
smux update

# 卸载 smux
smux uninstall
```textbash
# 读取名为 codex 的窗格的最后 20 行
tmux-bridge read codex 20

# 向 codex 窗格输入 "review src/auth.ts"
tmux-bridge type codex "review src/auth.ts"

# 向 codex 窗格发送回车键
tmux-bridge keys codex Enter
```text
1. 在一个窗格运行 Claude Code
2. 在另一个窗格运行 Codex
3. Claude Code 使用 tmux-bridge 向 Codex 发送任务
4. Codex 执行后，结果返回给 Claude Code
5. 两个 Agent 协同完成复杂任务
```textbash
npx skills add ShawnPana/smux
```textbash
# 安装 smux
curl -fsSL https://shawnpana.com/smux/install.sh | bash

# 安装 smux skill
npx skills add ShawnPana/smux
```textbash
# 终端上半部分：Claude Code
claude

# 终端下半部分：Codex
codex
```text
# Claude Code 发送指令
tmux-bridge type codex "review src/auth.ts"
tmux-bridge keys codex Enter

# Codex 执行完后，Claude Code 读取结果
tmux-bridge read codex 50
```text
Claude Code（人类视角）→ Codex（自动化审查）→ 结果汇总
```text
主 Agent（规划）→ 子 Agent（执行）→ 主 Agent（汇总）
```text
人类 ↔ Claude Code ↔ Codex
```text
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

**价值：**
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
