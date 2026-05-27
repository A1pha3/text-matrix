---
title: "Cua：开源计算机控制Agent基础设施完全指南"
date: "2026-05-14T10:47:00+08:00"
slug: "cua-computer-use-agent-infrastructure-guide"
aliases:
    - "/posts/tech/cua-computer-use-framework/"
    - "/posts/tech/cua-computer-use-agent-framework/"
description: "Cua是专注于Computer-Use的开源基础设施，提供沙箱、SDK和Benchmark来训练与评估能控制完整桌面的AI Agent。支持macOS、Linux、Windows三大平台，提供Cua Driver（后台控制）、Cua Sandbox（Agent-ready隔离环境）和Cua Bench（评估基准），是当前最完整的开源CUA方案。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Computer-Use", "沙箱", "Benchmark", "macOS"]
---

# Cua：开源计算机控制Agent基础设施完全指南

**Cua**（Computer-Use Agent）是当前最完整的开源 Computer-Use Agent 基础设施项目，由 trycua 团队开发。它提供三大核心组件——**Cua Driver**（后台桌面控制）、**Cua Sandbox**（跨平台隔离执行环境）和 **Cua Bench**（标准化评估基准），让开发者可以训练和评估能够操控完整桌面的 AI Agent。

与 Browser Use、Web Automat 等浏览器自动化方案不同，Cua 直指**原生桌面应用控制**这一更高难度场景——包括非 AX 标准的 Web 内容、Canvas 渲染工具（Blender、Figma、DAW）、游戏引擎等。

## 核心架构

```
┌─────────────────────────────────────────────┐
│            Cua Architecture                 │
├─────────────────────────────────────────────┤
│  Cua Bench    │ 评估基准，标准化测试环境      │
│  Cua Sandbox │ 跨 OS 沙箱，支持 macOS/Linux   │
│  Cua Driver  │ 后台桌面控制，零焦点抢占       │
│  Lume        │ macOS 虚拟化层                 │
└─────────────────────────────────────────────┘
```

## 三大核心组件

### 1. Cua Driver — 后台控制 macOS

Cua Driver 是 Cua 最独特的能力组件：可以在**不抢占焦点、不干扰用户当前窗口**的前提下，控制任意 macOS 原生应用。

核心特性：
- **后台操控**：Agent 在后台完成点击、输入、验证操作，用户正常继续使用电脑
- **非 AX 表面支持**：不仅支持标准无障碍（AX）API，还能操控 Chromium Web 内容、Canvas 渲染工具等非标准表面
- **MCP 集成**：提供 Claude Code、Cursor 等主流 Agent 的 MCP Server
- **轨迹录制**：每个操作会话自动录制成可回放的轨迹文件

```bash
# 一键安装
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.sh)"
```

安装后提供：
- `cua-driver` 命令行工具
- Claude Code Skill（`libs/cua-driver/skills/claude-code-skill.md`）
- MCP Server（端口可配置）

### 2. Cua — Agent-Ready 沙箱

提供跨 OS 的标准化隔离执行环境，Agent 在沙箱内完成整个任务生命周期：

```python
from cua import Sandbox, Image

# 定义任务镜像（预装 OS + 应用）
sandbox = Sandbox(
    image=Image("ubuntu:22.04"),  # 或 macOS
    os="linux"
)

# 启动 Agent 会话
session = sandbox.session()

# Agent 自动完成：看屏幕→点击按钮→验证结果
result = session.run("在浏览器中打开 github.com 并登录")
```

支持平台：
- **macOS**：通过 Lume 虚拟化
- **Linux**：Docker/KVM
- **Windows**：即将支持

### 3. Cua Bench — Benchmark 与 RL 环境

提供标准化的评估任务集，用于衡量 Agent 的计算机操控能力：

- **GUI 任务集**：文件操作、浏览器操作、文档编辑等真实任务
- **轨迹质量评估**：自动评分 Agent 操作的准确性与效率
- **RL 训练支持**：支持通过轨迹数据训练强化学习模型

## 安装

### Cua（Python SDK）

```bash
pip install cua
# 依赖 Python 3.11+
```

### Cua Driver（macOS 桌面控制）

```bash
curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.sh | bash
```

## 使用示例：后台自动化任务

```python
# 完整示例：让 Agent 在后台完成 GitHub PR 创建
from cua import Driver

driver = Driver()  # 自动连接 macOS 辅助功能 API

# 让 Agent 独立完成 GitHub PR 创建流程
task = """
在 Chrome 中打开 github.com，
使用当前登录的 GitHub 账号，
为仓库 trycua/cua 创建一个 PR，标题为 "fix: update driver"
"""
driver.run(task)
```

## 与 Browser Use 的区别

| 维度 | Browser Use | Cua |
|------|-------------|-----|
| 操控对象 | 浏览器 | 原生桌面 |
| 后台运行 | ❌ 需占用标签页 | ✅ 完全后台 |
| 非 AX 表面 | ❌ 不可支持 | ✅ 支持 |
| Canvas/游戏引擎 | ❌ | ✅ |
| 轨迹录制 | 基础 | 完整生命周期 |
| RL 训练数据 | 有限 | 完整支持 |

## 适用场景

- **桌面 RPA**：用 AI Agent 自动化 macOS 应用操作
- **测试自动化**：替代人工操作进行桌面应用 E2E 测试
- **Accessibility 研究**：在无障碍 API 层面构建辅助工具
- **Agent 评估**：用 Cua Bench 标准化评估各模型的桌面操控能力
- **RL 训练**：生成高质量轨迹数据训练桌面控制模型

## 资源链接

- 官网：[https://cua.ai](https://cua.ai)
- 文档：[https://cua.ai/docs](https://cua.ai/docs)
- GitHub：[https://github.com/trycua/cua](https://github.com/trycua/cua)