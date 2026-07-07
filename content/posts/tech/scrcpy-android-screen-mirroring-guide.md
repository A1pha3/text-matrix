+++
date = '2026-05-14T20:17:49+08:00'
draft = false
title = 'scrcpy：开源 Android 屏幕投射与设备控制'
slug = 'scrcpy-android-screen-mirroring-guide'
description = 'scrcpy 是 Genymobile 开源的 Android 设备投射工具，通过 USB 或 TCP/IP 将手机屏幕镜像至电脑，支持键盘鼠标控制设备，无需 root。'
categories = ['技术笔记']
tags = ['Android', '开源', '工具']
+++

# scrcpy：开源 Android 屏幕投射与设备控制

## 学习目标

读完本文，可以掌握以下能力：

- 说出 scrcpy 客户端 / scrcpy-server 两端架构的职责分工与通信方式
- 区分 USB 调试模式、OTG HID 模式、V4L2 模式的适用场景
- 用命令行参数调整分辨率、帧率、编码格式以平衡画质与延迟
- 在 Linux / Windows / macOS 上完成安装并解决常见连接问题
- 判断 scrcpy 相比 Vysor、Samsung Flow 等工具的取舍依据

---

## 目录

- [什么是 scrcpy？](#什么是-scrcpy)
- [核心特性](#核心特性)
- [功能一览](#功能一览)
  - [基础投射与控制](#基础投射与控制)
  - [高级控制能力](#高级控制能力)
  - [可配置性](#可配置性)
- [系统要求](#系统要求)
- [快速上手](#快速上手)
  - [安装方式](#安装方式)
  - [基础用法](#基础用法)
  - [常用配置示例](#常用配置示例)
- [技术架构简析](#技术架构简析)
- [与同类工具的差异](#与同类工具的差异)
- [采用顺序与适用边界](#采用顺序与适用边界)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [常见问题 FAQ](#常见问题-faq)

---

## 什么是 scrcpy？

[scrcpy](https://github.com/Genymobile/scrcpy)（发音为 "screen copy"）是 [Genymobile](https://github.com/Genymobile) 团队开源的 Android 设备投射与控制工具。它通过 USB 或 TCP/IP 无线连接，将 Android 设备的屏幕与音频实时投射到电脑，并允许用电脑的键盘和鼠标直接操控设备。整个过程**无需在手机端安装任何 App，无需 root 权限**——只依赖 Android 自带的 ADB 调试通道，断开后设备上不留任何痕迹。

## 核心特性

scrcpy 的设计目标与能力如下：

| 特性 | 描述 |
|------|------|
| **轻盈原生** | 专注于设备屏幕投射，无多余功能 |
| **高帧率** | 支持 30～120fps（取决于设备性能） |
| **高画质** | 默认 1920×1080 或更高分辨率 |
| **低延迟** | 延迟约 35～70ms |
| **秒级启动** | 约 1 秒即可显示第一帧画面 |
| **无残留** | Android 端不留任何安装痕迹 |
| **零依赖** | 无需账号、无广告、无需联网 |

## 功能一览

scrcpy 覆盖了日常开发、测试自动化、游戏操控等多种场景：

### 基础投射与控制
- **音频转发**（Android 11+ 即 API 30+）
- **屏幕录制**：可记录设备屏幕为 MP4 文件
- **虚拟显示**：创建独立于物理屏幕的虚拟显示，可用于多任务或隐私场景
- **熄屏投射**：在投射时关闭设备屏幕，延长手机寿命
- **双向剪贴板**：电脑与手机之间复制粘贴文本

### 高级控制能力
- **摄像头投射**（Android 12+）：将手机摄像头画面作为视频源投射
- **V4L2 模式**（Linux 专用）：将手机作为 webcam 暴露给系统
- **HID 模式（OTG）**：模拟物理键盘和鼠标，通过 USB HID 协议控制设备
- **游戏手柄支持**：连接手柄控制 Android 设备
- **全功能快捷键**：支持 HOME、BACK、音量、电源等快捷键

### 可配置性
- 画质、帧率、码率均可配置
- 支持 H.264 / H.265 视频编码
- 支持竖屏/横屏切换、全屏、旋转

## 系统要求

- **Android 设备**：至少 API 21（Android 5.0）
- **音频转发**：需要 API 30（Android 11+）
- **电脑端**：支持 Linux、Windows、macOS

> **注意**：在部分设备（尤其是小米）上，使用键盘鼠标控制功能时，需要额外开启「USB 调试（安全设置）」选项，并重启设备。

## 快速上手

### 安装方式

**Linux（Ubuntu 示例）：**
```bash
sudo apt install scrcpy
```

**Windows：**直接下载 Release 包，双击 `scrcpy.exe` 运行。

**macOS：**
```bash
brew install scrcpy
```

### 基础用法

连接设备后，命令行直接运行：
```bash
scrcpy
```

### 常用配置示例

**降低分辨率提升性能：**
```bash
scrcpy -m 1024
```

**使用 H.265 编码录制视频：**
```bash
scrcpy --video-codec=h265 --max-size=1920 --max-fps=60 --no-audio -K
```

**启动虚拟显示并运行 VLC：**
```bash
scrcpy --new-display=1920x1080 --start-app=org.videolan.vlc
```

**将手机摄像头作为摄像头使用（Linux）：**
```bash
scrcpy --video-source=camera --camera-size=1920x1080 --v4l2-sink=/dev/video2
```

**OTG 模式（无需 USB 调试，纯 HID 控制）：**
```bash
scrcpy --keyboard=uhid --mouse=uhid
```

## 技术架构简析

scrcpy 由两部分组成：

1. **scrcpy 客户端**（运行在电脑端）：采用 C 语言编写，基于 SDL2 渲染，配合 FFmpeg 处理音视频流。
2. **scrcpy-server**（运行在 Android 设备端）：一个部署在设备上的微型 Java 服务，负责采集屏幕帧和音频数据，通过 socket 发送给客户端。

通信协议是自定义的二进制协议，视频帧通过 protobuf 序列化。延迟主要来自编码、传输、解码三段，scrcpy 用 Android 硬件编码器（MediaCodec）和电脑端 FFmpeg 硬件解码把每段延迟压到毫秒级，整体延迟在 35～70ms 之间，取决于设备性能和网络状况。

### 一次 USB 投射的完整链路

把上面的两段机制串起来看一次实际连接：电脑端 scrcpy 启动后，先用 `adb` 把 `scrcpy-server` 推到设备并拉起；服务端用 `MediaCodec` 抓屏、编码成 H.264/H.265 码流，通过本地 socket 回传；客户端收到后交给 FFmpeg 解码、SDL2 渲染出画面。你敲击的按键和鼠标动作则逆向上行，经同一通道投到设备。整套链路里没有云端、没有中转服务器，断线即止。

## 与同类工具的差异

scrcpy 相比 Vysor、Samsung Flow 等工具的差异：

- 完全开源，代码透明，适合企业安全环境
- 无依赖：不需要 Google 服务，不需要账号
- C + Java 原生实现，延迟远低于 Electron/WebView 方案
- 从基础投射到 HID 模拟，覆盖几乎所有投射控制需求
- 项目长期维护，版本迭代稳定

## 采用顺序与适用边界

### 采用顺序建议

1. **USB 连接投射**：先用 `scrcpy` 默认参数跑通 USB 投射，确认设备兼容性和基础体验
2. **调整画质参数**：根据设备性能用 `-m`、`--max-fps`、`--video-codec` 平衡画质与延迟
3. **无线连接**：USB 稳定后再切 TCP/IP 无线模式，适合需要移动设备的场景
4. **高级模式**：有特定需求时再启用 OTG HID、V4L2、虚拟显示等模式

### 适用边界

- **适合**：开发调试、自动化测试、屏幕录制、演示投影、需要键盘鼠标操控 Android 的场景
- **不适合**：需要长期后台监控（scrcpy 是前台工具）、需要 root 专属功能（如修改系统设置）、对延迟极度敏感的实时游戏（35～70ms 仍有感知）

> **官方仓库**：https://github.com/Genymobile/scrcpy

---

## 自测题

1. scrcpy 的客户端和服务端分别用什么语言实现，各自运行在哪里？
2. 官方给出的 35～70ms 延迟主要来自哪三段，scrcpy 怎么把这三段压下去？
3. OTG HID 模式（`--keyboard=uhid --mouse=uhid`）为什么可以完全不开启 USB 调试？
4. 音频转发对 Android 系统版本有什么硬性要求？
5. 哪些场景其实不适合用 scrcpy？

<details>
<summary>参考答案</summary>

1. 客户端用 C 写、跑在电脑上，基于 SDL2 渲染、FFmpeg 处理音视频；服务端是一个微型 Java 程序，跑在 Android 设备端，负责采集屏幕和音频。
2. 编码、传输、解码三段。scrcpy 用设备的硬件编码器 MediaCodec 和电脑端 FFmpeg 硬件解码，把每段延迟压到毫秒级。
3. 因为它走的是 USB HID 协议，直接把电脑模拟成物理键盘和鼠标，设备端不需要授予 ADB 调试权限就能接收输入。
4. 需要 Android 11 及以上（API 30+）。
5. 长期后台监控（scrcpy 是前台工具）、依赖 root 的系统级修改、以及对延迟极度敏感的电竞场景。

</details>

---

## 练习

1. 用 USB 连上手机，先跑一次默认 `scrcpy`，再用 `scrcpy -m 1024` 降低分辨率，对比两者的画面清晰度和操作跟手程度。
2. 用 `scrcpy --video-codec=h265 --max-fps=60 --no-audio -K` 录一段 60 秒的操作视频，回看码率和流畅度。
3. 开一个虚拟显示并把某个 App 投进去：`scrcpy --new-display=1920x1080 --start-app=包名`，体验熄屏投射。
4. 在 Linux 上把手机摄像头当 webcam 用：`scrcpy --video-source=camera --camera-size=1920x1080 --v4l2-sink=/dev/video2`，然后打开会议软件选这个摄像头。
5. 切到无线模式：设备上 `adb tcpip 5555`，电脑 `adb connect 手机IP:5555` 后断开 USB，再跑 `scrcpy`。

---

## 进阶路径

- **读服务端源码**：scrcpy-server 体量不大，读完能弄清 MediaCodec 抓屏、protobuf 序列化与 socket 通信的全貌。
- **研究 OTG HID**：深入 `uhid` 实现，理解电脑如何被模拟成物理输入设备，以及它和 ADB 输入注入的本质区别。
- **做启动封装**：把自己常用的参数写成脚本或别名，按场景一键切换（开发调试 / 演示 / 录制）。
- **跟踪 issue tracker**：scrcpy 的边界（特定机型、特定 Android 版本的坑）都沉淀在 issue 里，比文档更全。

---

## 常见问题 FAQ

**连上后黑屏，或提示找不到设备？**
先 `adb devices` 确认设备在线。没出现就重开「USB 调试」，换根数据线（很多线只充电不通数据），再试 `adb kill-server && adb start-server`。

**小米、红米等机型能投射但键盘鼠标控不了？**
这类机型需要在「开发者选项」里额外打开「USB 调试（安全设置）」，并重启一次设备，否则输入事件会被系统拦截。

**无线连接动不动就断？**
无线依赖 `adb tcpip` 通道，走的是普通 Wi-Fi，干扰和耗电都会影响稳定性。对稳定性要求高时优先用 USB；无线只适合演示或临时场景。

**延迟太高、画面卡顿？**
优先降分辨率（`-m`）和帧率（`--max-fps`），换 H.265 通常更省带宽；同时确认用的是原装线、电脑解码走的是硬件而非软解。

**有画面没声音？**
音频转发只在 Android 11（API 30）以上可用。低于这个版本，scrcpy 本身不传声音，需要另接采集方案。

**macOS 上 `brew install scrcpy` 后命令找不到？**
一般是 PATH 没包含 Homebrew 的 sbin。把 `eval "$(/opt/homebrew/bin/brew shellenv)"` 加进 shell 配置后重开终端即可。