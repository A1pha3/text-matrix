---
title: "鸿镜 HongJing：面向 OpenHarmony 设备的投屏调试工具"
date: "2026-05-17T12:01:30+08:00"
slug: "hongjing-openharmony-scrcpy-alternative"
description: "鸿镜是一个面向 OpenHarmony 5.0+ 设备的投屏调试工具，Flutter 桌面客户端通过 hdc fport 端口转发与设备通信，实时镜像屏幕并提供触控注入、应用管理、终端模拟等功能，是 OpenHarmony 设备开发调试的实用辅助。"
draft: false
categories: ["技术笔记"]
tags: ["OpenHarmony", "Flutter", "投屏", "调试工具", "Scrcpy", "H.264"]
---

## 项目概览

**鸿镜 HongJing**（[guoxiucai/ohos-scrcpy-app](https://github.com/guoxiucai/ohos-scrcpy-app)）是一个面向 OpenHarmony 设备的实时投屏与远程控制工具，思路与安卓平台上的 [Scrcpy](https://github.com Genymobile/scrcpy) 类似：PC 端运行一个客户端，通过 USB 或网络连接到设备，把设备屏幕实时镜像到电脑，同时支持从电脑端直接操控设备。

作者在项目 README 中直接说明，这个项目的主要编码工作是通过 Claude Code 完成的，UI 部分用了 ui-ux-pro-max 做了美化。对于想了解 AI 辅助开发桌面工具的读者，这个项目本身也是一个小案例。

## 功能特性

| 功能 | 说明 |
|------|------|
| 实时投屏 | H.264 硬件编码 + 平台原生硬件解码，低延迟流畅画面 |
| 触控注入 | 鼠标操控设备触摸屏（支持单点触摸） |
| 应用管理 | HAP 安装 / 卸载、查看已安装应用列表 |
| 音量 / 亮度控制 | 远程调节设备音量与屏幕亮度 |
| 系统功能键 | 返回、主页、最近任务等系统按键模拟 |
| 模拟终端 | 内嵌 hdc shell 终端，直接操作设备命令行 |
| 动态参数 | 运行时调整分辨率、码率、帧率 |

## 技术架构

项目分为设备端（OpenHarmony 服务）和 PC 端（Flutter 客户端）两部分：

**设备端（ScrcpyService）：**
运行在 OpenHarmony 设备上，负责屏幕采集（`ScreenCapture`）、H.264 硬件编码（`VideoEncoder`）、TCP 视频流传输（`TcpServer`）和触控事件注入（`InputInjector`）。

**PC 端（Flutter 客户端）：**
跨平台桌面应用，通过 `hdc fport` 端口转发与设备通信。Windows 上用 MediaFoundation 做 H.264 硬件解码，macOS 上用 VideoToolbox。解码后的视频帧通过 Flutter Texture 组件渲染到窗口中，同时提供触控指令注入、终端模拟和应用管理界面。

```
┌────────────────────┐         hdc fport          ┌────────────────────────┐
│   OpenHarmony 设备  │◄─────────────────────────►│     PC 客户端 (Flutter)  │
│                    │      TCP over USB/网络       │                        │
│  ScrcpyService     │                            │  hdc CLI 包装           │
│  ├─ ScreenCapture  │  ──── H.264 视频流 ────▶   │  ├─ 协议解析            │
│  ├─ VideoEncoder   │                            │  ├─ 原生硬件解码         │
│  ├─ TcpServer      │  ◄─── 控制指令 ────────    │  ├─ Flutter Texture 渲染 │
│  └─ InputInjector  │                            │  └─ UI（投屏/终端/侧栏） │
└────────────────────┘                            └────────────────────────┘
```

### 技术选型说明

Flutter 的跨平台能力在这里发挥了作用——桌面端只需写一次，就能覆盖 macOS 和 Windows（Linux 规划中）。H.264 硬件编解码的思路也保证了低延迟：设备端用硬件编码避免 CPU 压力，PC 端同样用平台原生硬件解码来保证流畅播放。`hdc fport` 端口转发是 OpenHarmony 官方工具提供的ADB-like 能力，项目不需要自己实现 USB/网络传输层。

## 支持平台

**服务端（设备侧）：**

- OpenHarmony 5.0+（API 15+）
- 需要设备支持 H.264 硬件编码；不支持时会自动降级为 JPEG 模式

**客户端（PC 侧）：**

- macOS（VideoToolbox 硬件解码）✅
- Windows（MediaFoundation 硬件解码）✅
- Linux（计划中）

## 快速上手

### 1. 获取预编译包

从 [Releases](https://github.com/guoxiucai/ohos-scrcpy-app/releases) 页面下载：

- `OHScrcpyServer.hap`：设备端服务
- `HongJing-x.x.x.dmg`：macOS 客户端
- `HongJing-Setup-x.x.x.exe`：Windows 客户端

### 2. 安装服务端

```bash
# 连接设备后安装 HAP
hdc install -r OHScrcpyServer.hap
```

> ⚠️ 服务端需要系统应用签名和权限白名单配置，详见项目 docs 目录中的说明。

### 3. 启动客户端

确保 PC 与 OpenHarmony 设备已通过 USB 或 WiFi 连接。打开鸿镜客户端 → 选择已连接的设备 → 点击连接，即可看到实时投屏画面。

客户端已内置 HDC 工具（PC PATH 上有 `hdc` 命令可用也行）。

## 已知限制

- 服务端需要系统应用签名，普通开发者调试阶段可能需要联系设备厂商获取签名权限
- 仅支持单点触摸，复杂手势暂不支持
- Linux 客户端尚未完成

## 总结

鸿镜填补了 OpenHarmony 生态中"类 Scrcpy 工具"的空白。对于在 OpenHarmony 设备上做应用开发或系统调试的开发者来说，有一个可以在电脑上直接看屏幕+操作设备的工具会方便很多。项目本身也展示了 AI 辅助工具开发的可行性——主要代码由 Claude Code 生成，开发者做的是架构设计和产品定义。

**链接汇总：**

- GitHub：[guoxiucai/ohos-scrcpy-app](https://github.com/guoxiucai/ohos-scrcpy-app)
- Releases：[ohos-scrcpy-app/releases](https://github.com/guoxiucai/ohos-scrcpy-app/releases)