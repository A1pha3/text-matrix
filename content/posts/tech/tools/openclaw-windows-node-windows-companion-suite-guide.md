---
title: "openclaw-windows-node 实战指南：Scott Hanselman 出品的 OpenClaw Windows 伴侣套件（系统托盘 + PowerToys + WSL 网关）"
date: "2026-06-04T23:00:00+08:00"
slug: "openclaw-windows-node-windows-companion-suite-guide"
aliases:
  - /posts/tech/openclaw-windows-node-windows-companion-suite-guide/
description: "openclaw-windows-node 是 OpenClaw 官方的 Windows 端伴侣套件，WinUI 3 系统托盘 + 共享网关客户端库 + WSL Gateway + PowerToys Command Palette 扩展，由 Scott Hanselman 主导开发。"
draft: false
categories: ["技术笔记"]
tags: ["OpenClaw", "Windows", "WinUI", "PowerToys", "WSL", "Scott Hanselman"]
---

# openclaw-windows-node 实战指南：Scott Hanselman 出品的 OpenClaw Windows 伴侣套件（系统托盘 + PowerToys + WSL 网关）

## 核心判断

`openclaw-windows-node`（仓库 [openclaw/openclaw-windows-node](https://github.com/openclaw/openclaw-windows-node)）在 1.2K stars、331 今日 star 的体量下，回答了一个被 OpenClaw 跨平台版图掩盖的问题：**「OpenClaw 跑在 Linux/macOS 上很顺，但 Windows 用户的托盘 / PowerToys / WSL 集成谁来管？」**

openclaw-windows-node 的真正价值不是「又一款 Windows 客户端」——它是 **OpenClaw 官方**出品的 **Windows Hub** 全家桶：WinUI 3 系统托盘 + 共享网关客户端库 + CLI 工具 + PowerToys Command Palette 扩展 + 锁定的 `OpenClawGateway` WSL 发行版。它把 Windows 上 OpenClaw 的「**配对 → 命令中心 → 活动诊断 → 跨设备控制**」四件事一站打通。

它的护城河在三件别家没拼齐的事：

1. **由 Scott Hanselman 主导**——这位前 Microsoft Principal、知名播客主理人给项目背书，质量和品味都在「Microsoft 内部级」水准
2. **WSL Gateway 设计 = 零信任 + 锁定的 app-owned 发行版**——`OpenClawGateway` 是一个「被 OpenClaw 拥有」的特殊 WSL 发行版，文件权限按 `openclaw` 用户管理，root 写保护关键文件
3. **同时覆盖 x64 + ARM64 + MSIX**——`PackageMsix=true` 可生成可侧载的 MSIX 包，触发 Windows 的相机 / 麦克风 consent 弹窗

## 系统地图

| 项目 | 作用 |
| --- | --- |
| **OpenClaw.Tray.WinUI** | WinUI 3 系统托盘，提供 OpenClaw 状态、配对、命令中心、活动 / 诊断入口 |
| **OpenClaw.Shared** | 共享网关客户端库，封装 WebSocket connect/send/probe |
| **OpenClaw.Cli** | CLI 校验器，使用托盘里的设置做连接 / 发送 / 探测 |
| **OpenClawGateway（WSL 发行版）** | 锁定的 app-owned WSL 发行版，运行 OpenClaw 网关进程 |
| **PowerToys Command Palette 扩展** | 在 PowerToys Run / Command Palette 里直接触发 OpenClaw 命令 |
| **MSIX 包** | 可侧载安装包，触发 Windows 相机 / 麦克风 consent 弹窗 |

## 快速开始

### 0. 准备

- Windows 10 (20H2+) 或 Windows 11
- [.NET 10.0 SDK](https://dotnet.microsoft.com/download/dotnet/10.0)
- Windows 10 SDK（WinUI 编译需要）
- WebView2 Runtime（Win11 预装，旧版系统要装）

### 1. 装预编译 installer（终端用户）

直接下安装包：

```text
OpenClawCompanion-Setup-x64.exe
OpenClawCompanion-Setup-arm64.exe
```

SHA256 校验：`OpenClawCompanion-SHA256SUMS.txt`。

### 2. 从源码 build（开发者）

```bash
git clone https://github.com/openclaw/openclaw-windows-node.git
cd openclaw-windows-node

# 校验环境
.\build.ps1 -CheckOnly

# 编译全部
.\build.ps1

# 只编译 WinUI 托盘
.\build.ps1 -Project WinUI

# 直接用 dotnet（注意 ARM64 / x64 RID）
dotnet build src/OpenClaw.Tray.WinUI/OpenClaw.Tray.WinUI.csproj -r win-x64
dotnet build src/OpenClaw.Tray.WinUI/OpenClaw.Tray.WinUI.csproj -r win-arm64

# 生成可侧载 MSIX
dotnet build src/OpenClaw.Tray.WinUI -r win-x64    -p:PackageMsix=true
dotnet build src/OpenClaw.Tray.WinUI -r win-arm64  -p:PackageMsix=true
```

### 3. 跑托盘

```bash
# 默认：直接跑未打包的可执行
.\run-app-local.ps1

# 已有 build，跳过重新编译
.\run-app-local.ps1 -NoBuild

# 多 worktree 隔离（不污染你日常的托盘设置）
.\run-app-local.ps1 -Isolated

# Alpha 通道测试
.\run-app-local.ps1 -Configuration Release -Isolated -UpdateChannel alpha

# 通过 WinAppCLI 走 Package.appxmanifest 启动（需 `winget install Microsoft.WinAppCLI`）
.\run-app-local.ps1 -UseWinApp -NoBuild
```

### 4. 用 CLI 校验托盘配置

```bash
# 探测当前托盘设置（连接地址、token、gateway 状态）
OpenClaw.Cli probe

# 用托盘里的设置发一条消息
OpenClaw.Cli send --target gateway.local --message "hello from cli"
```

### 5. 配 WSL Gateway

`OpenClawGateway` 是 app-owned 发行版，admin 文档在 [`docs/WSL_GATEWAY_ADMIN.md`](https://github.com/openclaw/openclaw-windows-node/blob/master/docs/WSL_GATEWAY_ADMIN.md)：

```bash
# 进入 gateway 发行版（首次启动会自动 import）
wsl -d OpenClawGateway

# 以 openclaw 用户身份编辑配置
su openclaw
nano ~/openclaw.json

# 退出后再用 root 改受保护文件
exit
sudo nano /etc/openclaw/protected.json
```

## 关键能力

- **系统托盘**：WinUI 3，动画 + 主题跟随 Windows 11 系统模式
- **配对与连接设置**：在托盘里直接配 OpenClaw Gateway，配对码 + 状态实时显示
- **命令中心**：从托盘进「发送命令 / 触发工作流 / 调用设备」入口
- **活动与诊断**：实时显示网关心跳、消息往返、错误栈
- **PowerToys Command Palette 集成**：在 PowerToys Run（`Alt+Space`）里搜「OpenClaw」直达命令
- **多 worktree 隔离**：`-Isolated` 参数支持同时跑多个版本的 OpenClaw 托盘做对比

## 它在解决谁的什么问题

- **Windows 桌面 AI 重度用户**：用 OpenClaw 作为「system-wide 智能层」，但不想每次打开浏览器 / 终端；托盘常驻 + PowerToys 触发是最顺手的姿势
- **OpenClaw 跨平台开发者**：要在 Windows 上调试 / 演示 OpenClaw；MSIX 包让 demo 分发更简单
- **企业 IT / 隐私敏感用户**：WSL Gateway 的「app-owned 发行版 + openclaw 用户 + root 写保护」是一个比「双击安装」更安全的部署模型
- **PowerToys 重度用户**：Command Palette 是 Windows 11 的 launchpad；OpenClaw 接进去之后系统级 AI 触手可及

## 关键事实

| 维度 | 数据 |
| --- | --- |
| Stars | 1,209（trending 截屏时） |
| 今日新增 | 331 |
| 主要语言 | C#（WinUI 3） |
| 协议 | 见 `LICENSE`（与 OpenClaw 主项目一致） |
| 主开发者 | Scott Hanselman + OpenClaw 团队 |
| 平台 | Windows 10 20H2+ / Windows 11 |
| 架构 | x64 / ARM64 |
| 部署形态 | 预编译 installer / MSIX / unpackaged exe |
| WSL 发行版 | `OpenClawGateway`（app-owned，锁定） |
| 集成 | PowerToys Command Palette / PowerToys Run |

## 它和竞品的边界

- **vs Raycast / Alfred（macOS）**：Windows 上没有等量级系统级 launcher；OpenClaw Hub + PowerToys 拼起来是对位替代
- **vs PowerToys Run 单纯启动器**：PowerToys Run 只启动应用；OpenClaw 扩展可触发**对话 / 工作流 / 设备控制**
- **vs WSL 默认 ubuntu / debian**：OpenClawGateway 是锁定发行版，权限与生命周期由 app 管理，普通 WSL 发行版做不到
- **vs ChatGPT Desktop / Claude Desktop**：这些是单一模型厂的桌面端；OpenClaw Hub 是「**模型 + 网关 + 工作流**」三件套的桌面入口
- **vs LangChain / LlamaIndex 的 Web UI**：没有桌面托盘 + PowerToys 集成；OpenClaw 的 Windows 端优势在「**系统级可达性**」

## 适合与不适合

**适合**

- 日常在 Windows 上生活，希望 OpenClaw 像「任务栏里的智能体」一样常驻
- 已经用 PowerToys，想把 OpenClaw 纳入 Command Palette 一键触发
- OpenClaw 跨平台开发 / 测试 / 演示，要给 Windows 用户发可侧载的 MSIX
- 想用 WSL Gateway 而不是双击装 daemon 的「安全部署」模型

**不适合**

- 不在 Windows 11 / Windows 10 20H2+ 上：WinUI 3 不支持更老版本
- 没有 .NET 10 SDK：编译 / 调试会卡在第一行
- 想要「零依赖离线装」：MSIX 需要 WebView2 Runtime，旧版 Windows 要先装
- 想要 OpenClaw **替代** PowerToys：两个项目是**互补**不是替代；本仓库是 PowerToys 的扩展

## 已知边界

- **WinUI 3 + WebView2 编译时间较长**：冷 build 5-10 分钟
- **`OpenClawGateway` 是 app-owned 发行版**：每次 OpenClaw 升级可能需要 re-import；admin 文档会说明流程
- **PowerToys 必须先安装**：Command Palette 扩展依赖 PowerToys Run 注入
- **MSIX 侧载需要开发者模式开启**：Settings → Privacy & security → For developers → Developer Mode = On
- **托盘的 WebView2 渲染**：少数企业代理会拦截 WebView2 子进程，注意配 bypass

## 与文本矩阵的关联

文本矩阵的工作流深度依赖 **OpenClaw 自身**（早报 / 藏经阁 / GitHub 趋势榜多时段 cron 全都跑在 OpenClaw 上）。`openclaw-windows-node` 是把 OpenClaw 带到 **Windows 桌面 / PowerToys 触发**的官方桥梁——尤其对 Windows 重度用户，等于把 cron / Agent 流程从「开机后台跑」升级到「**任务栏右键 → OpenClaw 帮我做 X**」的交互入口。

## 资源

- 仓库：<https://github.com/openclaw/openclaw-windows-node>
- 官网：<https://openclaw.ai/>
- Windows 文档：<https://docs.openclaw.ai/platforms/windows>
- 安装指南：<https://github.com/openclaw/openclaw-windows-node/blob/master/docs/SETUP.md>
- WSL Gateway Admin：<https://github.com/openclaw/openclaw-windows-node/blob/master/docs/WSL_GATEWAY_ADMIN.md>
- 发行包下载：<https://github.com/openclaw/openclaw/releases/latest>
- 主项目 OpenClaw：<https://github.com/openclaw/openclaw>
