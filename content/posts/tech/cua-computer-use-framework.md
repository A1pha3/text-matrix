---
title: "Cua：让 AI 代理真正操控电脑的开源全栈框架"
date: 2026-04-27T00:59:00+08:00
slug: cua-computer-use-agent-framework
description: "Cua 是一个开源 computer-use 全栈框架，包含 macOS 后台驱动 Driver、跨平台沙箱 Sandbox、CLI 工具 CuaBot、基准测试 Cua-Bench 和虚拟化工具 Lume，让 AI 代理真正操控计算机而非只是生成文本。"
draft: false
categories: ["技术笔记"]
tags: ["AI", "Agent", "Computer-Use", "MCP", "macOS", "自动化"]
---

# Cua：让 AI 代理真正操控电脑的开源全栈框架

一句"Build, benchmark, and deploy agents that use computers"道出了 Cua 的野心：**不是让 AI 生成操控电脑的指令，而是让 AI 直接操控电脑。**

Cua 是当前 computer-use 领域最完整的开源方案之一，GitHub 14k stars，涵盖从底层驱动到上层基准测试的全栈能力。本文深入解析它的架构、各组件能力以及适用场景。

---

## 一、核心定位：computer-use 的全栈方案

传统的 AI 助手能生成文字、代码、邮件，但始终停留在"说"的层面。Cua 要解决的是让 AI agent 真正**看见屏幕、点击按钮、输入文字、执行任务**——完成从"会说"到"会做"的跨越。

Cua 不是单一工具，而是一套完整的 computer-use 基础设施：

| 组件 | 定位 | 解决的问题 |
|------|------|-----------|
| **Cua Driver** | macOS 后台驱动 | 在后台操控原生应用，不抢焦点 |
| **Cua Sandbox** | 跨平台沙箱 | 一套 API 操控 Linux/macOS/Windows/Android |
| **CuaBot** | CLI 工具 | 给 Claude Code、OpenClaw 等 Agent 挂载沙箱 |
| **Cua-Bench** | 基准测试 | 评估 agent 在真实 OS 环境中的表现 |
| **Lume** | macOS 虚拟化 | Apple Silicon 上跑高性能 macOS VM |

---

## 二、Cua Driver：后台操控 macOS 的核心能力

Cua Driver 是 Cua 体系中最有特色的组件——它让 agent 在**后台操控 macOS 应用**，不抢鼠标焦点、不干扰用户操作。

### 2.1 它能做什么

- **操作任何原生 macOS 应用**：通过 Accessibility API 和 AX 事件，即使是非 AX 表面（如 Chromium 内容、Canvas 工具 Figma/Blender/DAWs/游戏引擎）也能操控
- **后台运行**：不 stealing cursor、focus 或 Space，用户正常干活，agent 在后台执行
- **MCP 协议**：通过 stdio 与 Claude Code、Cursor 等主流 coding agent 对接
- **轨迹录制**：每个 session 都录制为可回放的 trajectory，可用于 RL 训练或复盘

安装方式一行搞定：

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.sh)"
```

### 2.2 与 AppleScript 的本质区别

macOS 本身有 AppleScript 和 Accessibility API，为什么还需要 Cua Driver？

| 对比维度 | AppleScript | Cua Driver |
|---------|-------------|------------|
| 操控范围 | 仅支持 AX 应用 | 覆盖 Chromium web content、Canvas 工具 |
| 焦点影响 | 会抢占窗口焦点 | 后台运行，用户无感知 |
| 轨迹录制 | 无 | 完整 session 回放 |
| MCP 集成 | 需自行封装 | 原生支持 stdio MCP |
| 多 agent 支持 | 弱 | 多 agent 并发操控不同 app |

### 2.3 Claude Code Skill

Cua Driver 随包装了一个 Claude Code skill，agent 可以直接调用底层的 screenshot、click、type 等工具，实现"看见啥干啥"的能力。

---

## 三、Cua：跨平台的 Agent-ready 沙箱

Cua 是通用的沙箱 SDK，一个 API 覆盖 Linux/macOS/Windows/Android，支持云端和本地（QEMU）两种运行模式。

### 3.1 安装与基本用法

```bash
pip install cua
```

```python
from cua import Sandbox, Image

async with Sandbox.ephemeral(Image.linux()) as sb:
    result = await sb.shell.run("echo hello")
    screenshot = await sb.screenshot()
    await sb.mouse.click(100, 200)
    await sb.keyboard.type("Hello from Cua!")
    await sb.mobile.gesture((100, 500), (100, 200))  # multi-touch
```

**同一套 API，跨所有平台**，不需要为每个 OS 写不同的控制逻辑。

### 3.2 平台支持矩阵

| 平台 | 云端 (cua.ai) | 本地 (QEMU) |
|------|-------------|------------|
| Linux container | ✅ | ✅ |
| Linux VM | ✅ | ✅ |
| macOS | ✅ | ✅ |
| Windows | ✅ | ✅ |
| Android | ✅ | ✅ |
| BYOI (.qcow2, .iso) | 🔜 | ✅ |

### 3.3 核心工具集

每个 Sandbox 实例提供以下能力：

- **shell.run**：执行命令
- **screenshot**：获取屏幕截图
- **mouse.click/move/drag**：鼠标操作
- **keyboard.type**：文本输入
- **mobile.gesture**：多点触控手势
- **viewport**：获取视口信息

这套工具集足够支撑从简单自动化到复杂 OS 操作的一切场景。

---

## 四、CuaBot：给 coding agent 挂个沙箱

CuaBot 是 Cua 提供的 CLI 工具，它的核心理念是：**给任何 coding agent 一个可操控的沙箱环境**。

### 4.1 安装与基本用法

```bash
npx cuabot  # Setup onboarding

# 运行 agent
cuabot claude   # Claude Code in sandbox
cuabot openclaw # OpenClaw in sandbox

# 运行 GUI workflow
cuabot chromium
cuabot --screenshot
cuabot --click <x> <y>
```

### 4.2 内置支持的 Agent 类型

- `agent-browser`：浏览器自动化
- `agent-device`：iOS 和 Android 设备操控
- 任意自定义 agent 通过 `cuabot <command>` 调用

### 4.3 用户体验设计

CuaBot 将沙箱中的独立窗口原生呈现到用户桌面，支持 H.265 视频流、共享剪贴板和音频。用户在本地看到的窗口，实际上运行在远程或本地的沙箱中——兼顾了安全性和交互体验。

CuaBot 最早在 ClawCon（OpenClaw 社区大会）上亮相，是 OpenClaw 官方推荐的 sandbox 方案。

---

## 五、Cua-Bench：computer-use 能力的基准测试

Cua-Bench 是 Cua 的评测组件，用于评估 agent 在真实 OS 环境中的 computer-use 能力。

### 5.1 支持的基准测试集

- **OSWorld**：通用 OS 任务评测
- **ScreenSpot**：UI 操作评测
- **Windows Arena**：Windows 环境评测
- **自定义任务**：支持用户定义自己的评测集

### 5.2 工作流程

```bash
# 安装并创建 base image
cd cua-bench
uv tool install -e . && cb image create linux-docker

# 用 agent 运行基准测试
cb run dataset datasets/cua-bench-basic --agent cua-agent --max-parallel 4
```

### 5.3 导出轨迹用于 RL

每个评测任务完成后，轨迹（trajectory）数据可以被导出用于强化学习训练。这意味着 Cua 不仅是个执行环境，还是一个**数据采集和模型训练平台**。

合作伙伴可以在 [cuabench.ai](https://cuabench.ai) 注册并贡献评测任务。

---

## 六、Lume：Apple Silicon 上的高性能 macOS 虚拟机

Lume 是 Cua 生态中专注于 macOS 虚拟化的组件，使用 Apple 的 Virtualization.Framework 在 Apple Silicon 上跑 macOS 和 Linux VM，性能接近原生。

### 6.1 安装

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/lume/scripts/install.sh)"
```

### 6.2 使用示例

```bash
# 拉取并启动 macOS VM
lume run macos-sequoia-vanilla:latest
```

### 6.3 Lumier：Docker 兼容接口

Lumier 是 Lume 的高级接口，提供了 Docker 兼容的 CLI：

```bash
lumier run --image macos-sequoia-vanilla:latest
```

这对已经熟悉 Docker 的开发者来说几乎没有学习成本。

---

## 七、技术架构总览

```
┌─────────────────────────────────────────────┐
│             Agent (Claude Code, OpenClaw...)  │
├─────────────────────────────────────────────┤
│              CuaBot (CLI)                    │
│         cua-agent (Agent SDK)               │
├─────────────────────────────────────────────┤
│        Cua Sandbox / Cua Driver             │
│   (跨平台抽象层 + macOS 后台驱动)            │
├────────────┬────────────┬────────────────────┤
│ Cloud      │ QEMU       │ Apple Virtualization│
│ (cua.ai)   │ (本地)     │ (Lume, Apple Silicon)│
└────────────┴────────────┴────────────────────┘
```

**MCP 协议**贯穿整个架构，所有组件通过 stdio 进行通信，保持了极低的集成成本。

---

## 八、典型使用场景

| 场景 | 推荐组件 |
|------|---------|
| 给 Claude Code 挂载可操控的 macOS 环境 | Cua Driver + Claude Code skill |
| 跨平台 browser 自动化测试 | Cua Sandbox + agent-browser |
| 评测 LLM 的 computer-use 能力 | Cua-Bench |
| 本地跑 macOS VM（开发/测试） | Lume |
| 给 OpenClaw 配置沙箱 | CuaBot openclaw |
| 采集 trajectory 训练 RL 模型 | Cua-Bench + 轨迹导出 |
| iOS/Android 自动化测试 | CuaBot agent-device |

---

## 九、快速开始

**Cua Driver（macOS 后台控制）：**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/cua-driver/scripts/install.sh)"
```

**Cua Python SDK：**
```bash
pip install cua
```

**CuaBot CLI：**
```bash
npx cuabot
```

**Lume（macOS 虚拟化）：**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/trycua/cua/main/libs/lume/scripts/install.sh)"
```

---

## 总结

Cua 解决的是一个根本问题：**让 AI agent 真正在电脑里干活，而不是只在聊天框里出主意**。

从底层看，它有 Driver 的后台操控能力、Sandbox 的跨平台抽象、Bench 的评测体系、Lume 的虚拟化支持；从上层看，它通过 CuaBot 给 Claude Code、OpenClaw 等主流 coding agent 一键挂载沙箱，零门槛接入。

如果你在：
- 做一些需要 agent 操控 GUI 的事情（自动化测试、工作流）
- 评估/训练 computer-use 能力的模型
- 需要一个可靠的跨平台 OS 操控环境

Cua 值得优先考虑。

**相关链接：**

- GitHub：https://github.com/trycua/cua（14k stars）
- 官网：https://cua.ai
- 文档：https://cua.ai/docs
- Discord：https://discord.gg/mVnXXpdE85

🦞 每日08:00自动更新