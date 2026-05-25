---
title: "CUA：开源计算机控制AI Agent基础设施，支持macOS/Linux/Windows全平台"
date: "2026-05-14T15:22:32+08:00"
slug: "trycua-cua-open-source-computer-use-agents"
description: "CUA 是 trycua 推出的开源计算机控制 AI Agent 基础设施，提供沙箱、SDK 和基准测试，覆盖 macOS、Linux、Windows 全平台，支持本地 QEMU 和云端虚拟化，可训练和评估能控制完整桌面的 AI 智能体。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "计算机控制", "沙箱", "QEMU", "macOS", "AI编程", "开源"]
---

# CUA：开源计算机控制AI Agent基础设施，支持macOS/Linux/Windows全平台

## 项目概览

**CUA**（https://github.com/trycua/cua，官网 [cua.ai](https://cua.ai)）是 trycua 团队推出的开源计算机使用智能体（Computer-Use Agents）基础设施，提供沙箱、SDK 和基准测试三大核心组件，支持训练和评估能控制完整桌面的 AI 智能体。截至 2026 年 5 月，已积累 **16,649 Stars** 和 **1,048 Forks**，是 Computer-Use Agent 领域最具影响力的开源项目之一。

项目核心信息：

| 指标 | 数值 |
|------|------|
| Stars | 16,649 |
| Forks | 1,048 |
| 主要语言 | HTML（网页+文档）、Python（SDK） |
| 许可证 | MIT |
| 最后推送 | 2026-05-14（今日活跃） |
| 所属组织 | trycua |

CUA 解决的核心问题是：**如何让 AI Agent 像人类一样使用计算机**——不仅仅是处理文本，而是能够看到屏幕、点击按钮、操作应用程序、完成复杂的多步骤桌面任务。

---

## 核心组件解析

### 1. Cua Driver — macOS 后台计算机控制

这是 CUA 最具差异化的组件：能够在**后台**驱动 macOS 原生应用，而不需要抢夺光标、焦点或屏幕空间。

关键能力：
- **后台操控**：Agent 在后台点击、输入和验证，不影响用户当前工作
- **非 AX 表面支持**：除了标准 macOS 辅助功能（AX）表面，还能操作 Chromium 网页内容、Canvas 工具（Figma、Blender、DAW、游戏引擎等）
- **轨迹录制**：每个 session 都被记录为可回放的轨迹（trajectory），可用于训练或复盘
- **MCP 服务器支持**：可接入 Claude Code、Cursor 等主流 Agent 客户端

安装方式：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.sh)"
```

### 2. Cua — 全平台可用的 Agent 沙箱

跨 OS（Linux/macOS/Windows/Android）的统一沙箱 API，一套代码可以在任何操作系统上运行，支持本地 QEMU 虚拟机和云端容器两种运行时。

核心 Python 示例：

```python
from cua import Sandbox, Image

# 同一套 API，不分操作系统
async with Sandbox.ephemeral(Image.linux()) as sb:
    result = await sb.shell.run("echo hello")
    screenshot = await sb.screenshot()
    await sb.mouse.click(100, 200)
    await sb.keyboard.type("Hello from Cua!")
    await sb.mobile.gesture((100, 500), (100, 200))  # 多点触控手势
```

支持矩阵：

| 平台 | 云端（cua.ai） | 本地（QEMU） |
|------|---------------|-------------|
| Linux 容器 | ✅ | ✅ |
| Linux 虚拟机 | ✅ | ✅ |
| macOS | ✅ | ✅ |
| Windows | ✅ | ✅ |
| Android | ✅ | ✅ |
| 自定义镜像（.qcow2/.iso） | 🔜 soon | ✅ |

### 3. CuaBot — 协作式多 Agent 计算机使用沙箱

CuaBot 提供给任何编程 Agent 一个无缝的沙箱环境，隔离运行。与 Cua Driver 不同的是，CuaBot 的每个窗口都以原生形式出现在用户桌面上，支持 H.265 视频编码、共享剪贴板和音频。

```bash
# 安装
npx cuabot

# 在沙箱中运行各种 Agent
cuabot claude        # Claude Code
cuabot openclaw      # OpenClaw
cuabot chromium      # Chromium 浏览器

# 直接操作
cuabot --screenshot
cuabot --type "hello"
cuabot --click <x> <y> [button]
```

内置支持 `agent-browser` 和 `agent-device`（iOS、Android）。

### 4. Cua-Bench — 基准测试与强化学习环境

评估计算机使用智能体在 OSWorld、ScreenSpot、Windows Arena 等标准基准测试上的表现，并支持导出轨迹数据用于训练。

```bash
cd cua-bench
uv tool install -e . && cb image create linux-docker

# 运行基准测试
cb run dataset datasets/cua-bench-basic --agent cua-agent --max-parallel 4
```

### 5. Lume — Apple Silicon macOS 虚拟化

用 Apple 的 Virtualization.Framework 在 Apple Silicon 上创建和运行 macOS/Linux 虚拟机，性能接近原生，支持 Docker 兼容接口（Lumier）。

```bash
# 安装 Lume
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/lume/scripts/install.sh)"

# 拉取并启动 macOS VM
lume run macos-sequoia-vanilla:latest
```

---

## 技术架构亮点

### 统一的 Agent SDK

`cua-agent` 是面向 AI 智能体开发者的框架 SDK，提供标准化的计算控制抽象。开发者不需要关心底层是 QEMU 还是云端虚拟机，API 完全一致。

### 多层隔离安全

沙箱设计强调多层隔离：
- 进程级：每个操作在独立环境执行
- 系统级：QEMU/容器级虚拟机隔离
- 网络级：可选完全断网的沙箱环境

### 轨迹驱动的数据飞轮

Cua Driver 每次 session 都会录制完整的操作轨迹，这些轨迹可用于：
- 强化学习训练数据
- 回归测试（验证修复没有引入新问题）
- Agent 行为分析

---

## 适用场景

**直接适用：**
- 构建能操作桌面应用的 AI Agent（客服机器人、自动化测试、数据录入）
- 在隔离环境中运行第三方 Agent（安全隔离不受信的 AI 操作）
- 评估不同 Agent 在标准任务上的能力差异
- macOS 原生应用的自动化操控（在用户不知觉的后台运行）

**不适用：**
- 纯 API 调用类 Agent（不需要视觉/点击能力）
- 对实时性要求极高的场景（沙箱本身有延迟开销）

---

## 与同类方案对比

| 方案 | 平台覆盖 | 本地支持 | 后台运行 | 基准测试 |
|------|---------|---------|---------|---------|
| CUA | 全平台 | ✅ QEMU | ✅ Driver | ✅ Cua-Bench |
| OS-World | Linux 为主 | ❌ | ❌ | ✅ |
| Microsoft/UIA | Windows 为主 | ❌ | ✅ | ❌ |
| Apple Accessibility | macOS 为主 | ✅ | 部分 | ❌ |

---

## 总结与延伸阅读

CUA 是目前最完整的开源计算机控制 Agent 基础设施，覆盖了从沙箱运行时、Driver 控制、基准测试到 VM 虚拟化的完整链路。其全平台支持和本地 QEMU 运行的特性，使得个人开发者和小型团队也能低成本构建和测试自己的 Agent 系统。

**延伸阅读：**
- 官网：https://cua.ai
- 文档：https://cua.ai/docs
- GitHub：https://github.com/trycua/cua
- Discord 社区：https://discord.gg/mVnXXpdE85