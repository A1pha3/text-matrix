---
title: "scrcpy：开源 Android 屏幕投射与设备控制利器"
date: "2026-05-14T20:17:49+08:00"
categories: ["技术笔记"]
tags: ["Android", "屏幕投射", "开源工具", "adb", "设备控制"]
description: "scrcpy 是 Genymobile 开源的 Android 设备投射工具，通过 USB 或 TCP/IP 将手机屏幕镜像至电脑，并支持键盘鼠标控制设备。无需 root，1 秒启动，30~120fps，低延迟 35~70ms，支持音频转发、录制、虚拟显示、HID 模式等丰富功能。"
---

# scrcpy：开源 Android 屏幕投射与设备控制利器

## 什么是 scrcpy？

[scrcpy](https://github.com/Genymobile/scrcpy)（发音为 "screen copy"）是 [Genymobile](https://github.com/Genymobile) 团队开源的 Android 设备投射与控制工具。它通过 USB 或 TCP/IP 无线连接，将 Android 设备的屏幕与音频实时投射到电脑，并允许用电脑的键盘和鼠标直接操控设备。整个过程**无需在手机端安装任何 App，无需 root 权限**，做到了真正的零侵入。

截至目前，该项目已累计获得约 **141,000 颗 GitHub Stars**，是 Android 开发与自动化领域最受欢迎的明星项目之一。

## 核心特性

根据仓库 README 描述，scrcpy 的核心设计目标与能力如下：

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

scrcpy 提供的功能非常丰富，覆盖了日常开发、测试自动化、游戏操控等多种场景：

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

通信协议本质上是一个自定义的二进制协议，视频帧通过 protobuf 序列化，延迟控制得很好。

## 为什么选择 scrcpy？

市面上有不少 Android 投射工具，例如 Vysor、Samsung Flow 等，但 scrcpy 有几个显著优势：

- **完全开源**：代码完全透明，无后顾之忧，适合企业安全环境
- **无依赖**：不需要 Google 服务，不需要账号
- **性能卓越**：C + Java 的原生实现，延迟远低于 Electron/WebView 方案
- **功能全面**：从基础投射到 HID 模拟，覆盖了几乎所有投射控制需求
- **持续活跃**：项目长期维护，版本迭代稳定

## 总结

scrcpy 堪称 Android 开发者和高级用户的「瑞士军刀」——它轻量、快速、功能丰富且完全免费。无论是做 App 演示、自动化测试、游戏操控，还是日常办公投射，它都能胜任。其开源属性和出色的性能使其在同类工具中脱颖而出，成为 GitHub 上最受欢迎的 Android 相关项目之一。

如果你还没有尝试过 scrcpy，不妨现在就下载体验，1 秒启动、流畅投射，感受它带来的高效与自由。

> **官方仓库**：https://github.com/Genymobile/scrcpy