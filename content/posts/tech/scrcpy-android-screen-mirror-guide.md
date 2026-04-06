---
title: "scrcpy：138k Stars Android 屏幕镜像完全指南"
date: 2026-04-06T22:23:00+08:00
slug: "scrcpy-android-screen-mirror-guide"
description: "全面介绍 138k Stars 的 scrcpy Android 屏幕镜像工具，涵盖安装配置、USB/无线连接、屏幕录制、音频转发、键盘鼠标/游戏手柄控制、OTG 模式、摄像头镜像、性能优化等全部功能。"
draft: false
categories: ["技术笔记"]
tags: ["scrcpy", "Android", "屏幕镜像", "无线调试", "ADB", "远程控制"]
---

## 学习目标

通过本文，你将全面掌握以下核心能力：

- 深入理解 scrcpy 的项目定位、核心概念和技术架构
- 掌握 scrcpy 的安装方法（Linux/Windows/macOS）
- 学会通过 USB 和 TCP/IP 连接 Android 设备
- 掌握屏幕录制、音频转发、虚拟显示器等核心功能
- 学会使用键盘、鼠标、游戏手柄控制 Android 设备
- 理解 OTG 模式和摄像头镜像等高级功能
- 掌握性能优化技巧和常见问题解决方案

---

## 1. 项目概述

### 1.1 是什么

**scrcpy**（发音为 "scr**een** **c**o**py**）是一个通过 USB 或 TCP/IP 无线连接来镜像和控制 Android 设备的应用程序。无需 ROOT 权限，也无需在设备上安装任何应用。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **138k** |
| GitHub Forks | **12.9k** |
| Contributors | **150** |
| Releases | **50** |
| 最新版本 | **v3.3.4** (2025-12-18) |
| License | **Apache-2.0** |
| 语言 | **C 63.9%**，Java 31.8%，Meson 0.7% |

### 1.3 项目特点

| 特性 | 说明 |
|------|------|
| **轻量** | 原生性能，仅显示设备屏幕 |
| **高性能** | 30~120fps，取决于设备性能 |
| **高质量** | 支持 1920×1080 或更高分辨率 |
| **低延迟** | 35~70ms |
| **快速启动** | 约 1 秒显示首帧 |
| **无侵入** | 设备不留任何安装痕迹 |
| **无广告** | 无账号、无广告、无需联网 |
| **自由开源** | Apache-2.0 许可证 |

### 1.4 核心作者

**Romain Vimont** (@rom1v) 是主要作者和维护者。可以通过 GitHub Sponsors、Liberapay 或 PayPal 支持他的开源工作。

---

## 2. 安装指南

### 2.1 系统要求

**Android 设备要求**：

- Android 5.0（API 21）或更高版本
- 音频转发需要 Android 11（API 30）或更高版本
- 摄像头镜像需要 Android 12（API 31）或更高版本

**电脑要求**：

- Linux / Windows / macOS 均可
- ADB 工具（通常已包含）

### 2.2 Linux 安装

```bash
# Debian/Ubuntu
sudo apt install scrcpy

# Fedora
sudo dnf install scrcpy

# Arch Linux
sudo pacman -S scrcpy

# 从源码构建（需要 Android SDK）
git clone https://github.com/Genymobile/scrcpy.git
cd scrcpy
./build.py --release
```

### 2.3 Windows 安装

**方法一：Scoop**

```powershell
 scoop install scrcpy
```

**方法二：Chocolatey**

```powershell
 choco install scrcpy
```

**方法三：手动下载**

1. 从 GitHub Releases 下载最新版本
2. 解压到任意目录
3. 将目录添加到 PATH 环境变量

### 2.4 macOS 安装

```bash
# Homebrew
brew install scrcpy

# 或从 App Store 下载 Android 文件传输工具
```

---

## 3. 连接设备

### 3.1 USB 连接（基础）

**步骤 1：启用 USB 调试**

```bash
# 在 Android 设备上：
# 设置 → 关于手机 → 点击"版本号"7次启用开发者模式
# 设置 → 开发者选项 → 启用"USB 调试"
```

**步骤 2：连接电脑**

```bash
# 使用 USB 线连接设备
# 在电脑上执行：
adb devices

# 应该看到类似输出：
# List of devices attached
# emulator-5554    device
```

**步骤 3：启动 scrcpy**

```bash
scrcpy
```

### 3.2 无线连接（推荐）

**方法一：通过 USB 转发**

```bash
# 1. 先通过 USB 连接设备
adb tcpip 5555

# 2. 拔掉 USB 线

# 3. 通过 IP 连接
adb connect <设备IP>:5555

# 4. 启动 scrcpy
scrcpy
```

**方法二：无线安装（无需 USB 线）**

```bash
# 确保电脑和设备在同一网络
# 启用 USB 调试后执行：
adbWireless enable  # 如果设备有 adbWireless app

# 或者手动：
adb tcpip 5555
adb connect <设备IP>:5555
scrcpy
```

### 3.3 多设备切换

```bash
# 查看所有连接的设备
adb devices

# 指定设备序列号
scrcpy -s <序列号>

# 例如：
scrcpy -s 192.168.1.100:5555
```

---

## 4. 核心功能

### 4.1 基础镜像

```bash
# 最简单的启动方式
scrcpy

# 指定分辨率（大幅提升性能）
scrcpy -m 1024

# 指定帧率
scrcpy --max-fps 60

# 同时指定分辨率和帧率
scrcpy -m 1024 --max-fps 60
```

### 4.2 屏幕录制

```bash
# 录制屏幕到 MP4 文件
scrcpy --record=screen.mp4

# 录制时禁用音频
scrcpy --record=screen.mp4 --no-audio

# 指定录制分辨率
scrcpy --record=screen.mp4 -m 1920
```

### 4.3 音频转发

```bash
# Android 11+ 支持音频转发
scrcpy --audio

# 录制音频
scrcpy --record=output.mp4 --audio
```

### 4.4 屏幕关闭镜像

```bash
# 镜像时关闭设备屏幕（节省电量）
scrcpy --turn-screen-off

# 或按快捷键 Ctrl+Shift+O 切换屏幕开关
```

### 4.5 复制粘贴

```bash
# 电脑 → 设备：Ctrl+V
# 设备 → 电脑：Ctrl+C

# 自动同步剪贴板
scrcpy --copy-keyboard
```

---

## 5. 控制方式

### 5.1 鼠标控制

| 操作 | 说明 |
|------|------|
| **左键点击** | 点击设备屏幕 |
| **右键点击** | 返回键 |
| **中键点击** | HOME 键 |
| **滚轮** | 滚动列表 |
| **拖拽文件** | 推送文件到设备 |

### 5.2 键盘控制

| 操作 | 说明 |
|------|------|
| **Ctrl+H** | 返回键 |
| **Ctrl+S** | HOME 键 |
| **Ctrl+M** | 多任务键 |
| **Ctrl+↑/↓** | 音量调节 |
| **Ctrl+P** | 电源键 |
| **打字** | 直接在设备输入 |

### 5.3 游戏手柄支持

```bash
# 启用游戏手柄控制
scrcpy --gamepad=uhid

# 或使用短参数
scrcpy -G
```

**支持的游戏手柄按钮**：

- 左/右摇杆：移动
- A/B/X/Y 按钮：点击
- LB/RB：菜单
- Start/Select：返回/主页

### 5.4 OTG 模式

OTG 模式无需 USB 调试即可控制设备：

```bash
# OTG 模式（USB 调试不需要）
scrcpy --otg

# 只启用键盘和鼠标（不需要 ADB）
scrcpy --otg --keyboard=uhid --mouse=uhid
```

---

## 6. 高级功能

### 6.1 摄像头镜像

Android 12+ 支持摄像头镜像为电脑的虚拟摄像头：

```bash
# 镜像后置摄像头
scrcpy --video-source=camera --camera-facing=back

# 镜像前置摄像头
scrcpy --video-source=camera --camera-facing=front

# 指定分辨率
scrcpy --video-source=camera --camera-size=1920x1080
```

### 6.2 V4L2 作为 webcam（Linux）

将 Android 摄像头暴露为 Linux 的虚拟摄像头设备：

```bash
# 安装 V4L2 支持
scrcpy --v4l2-sink=/dev/video0

# 然后可以在 OBS 或其他软件中使用
```

### 6.3 虚拟显示器

创建独立于设备屏幕的虚拟显示器：

```bash
# 创建 1920x1080 虚拟显示器并启动 VLC
scrcpy --new-display=1920x1080 --start-app=org.videolan.vlc

# 创建自定义尺寸
scrcpy --new-display=1280x720
```

### 6.4 窗口管理

```bash
# 禁用窗口装饰
scrcpy --window-no-decoration

# 指定窗口标题
scrcpy --window-title="我的设备"

# 全屏启动
scrcpy -f

# 调整窗口大小
scrcpy --resize=widthxheight
```

---

## 7. 性能优化

### 7.1 降低分辨率

```bash
# 降至 720p（推荐，延迟最低）
scrcpy -m 720

# 降至 480p（最低延迟）
scrcpy -m 480
```

### 7.2 降低码率

```bash
# 降低视频码率（默认 8Mbps）
scrcpy --video-bit-rate=2M

# 极低码率（最低带宽）
scrcpy --video-bit-rate=1M
```

### 7.3 选择编解码器

```bash
# 使用 H.265（更好压缩率）
scrcpy --video-codec=h265

# 使用 H.264（更广泛兼容）
scrcpy --video-codec=h264
```

### 7.4 组合优化

```bash
# 综合优化：720p + 60fps + H.265
scrcpy -m 720 --max-fps 60 --video-codec=h265

# 极低延迟配置
scrcpy -m 480 --max-fps 120 --video-bit-rate=1M
```

---

## 8. 常见问题

### 8.1 权限问题

**症状**：出现错误 "Injecting input events requires the caller to have the INJECT_EVENTS permission"

**解决方案**：

1. 启用 USB 调试（安全设置）
2. 重启设备

```bash
# 设置 → 开发者选项 → USB 调试（安全设置）→ 启用
```

### 8.2 设备检测不到

```bash
# 重启 ADB 服务
adb kill-server
adb start-server

# 检查设备授权状态
adb devices
```

### 8.3 延迟高

```bash
# 1. 降低分辨率
scrcpy -m 720

# 2. 使用有线 USB 连接
# 3. 关闭设备后台应用
# 4. 启用性能模式
```

### 8.4 音频不同步

```bash
# 禁用音频（如果只需要视频）
scrcpy --no-audio

# 或使用较低分辨率
scrcpy -m 1024
```

---

## 9. 快捷键汇总

### 9.1 基础快捷键

| 快捷键 | 功能 |
|--------|------|
| **Ctrl+H** | 返回 |
| **Ctrl+M** | 多任务 |
| **Ctrl+S** | HOME |
| **Ctrl+P** | 电源 |
| **Ctrl+B** | 返回（替代） |
| **Alt+F** | 全屏 |
| **Alt+Enter** | 全屏（替代） |

### 9.2 屏幕控制

| 快捷键 | 功能 |
|--------|------|
| **鼠标中键** | HOME |
| **右键** | 返回 |
| **滚轮上/下** | 音量 +/- |
| **Ctrl+滚轮** | 缩放 |

### 9.3 文本输入

| 操作 | 说明 |
|------|------|
| **Ctrl+Z** | 启用文本注入 |
| **打字** | 直接输入英文 |
| **Ctrl+E** | 启用文本注入（替代） |

---

## 10. 技术架构

### 10.1 组件结构

scrcpy 由以下组件构成：

| 组件 | 说明 |
|------|------|
| **scrcpy-client** | C 语言实现的客户端 |
| **scrcpy-server** | Android 服务端 Java 应用 |
| **ADB** | Android Debug Bridge 连接 |

### 10.2 工作流程

```
电脑 ←USB/TCP/IP→ ADB ←Socket→ scrcpy-server ←Surface→ Android 设备屏幕
```

### 10.3 视频流

- 设备端：scrcpy-server 通过 MediaCodec 编码屏幕
- 客户端：SDL2 渲染显示
- 协议：自定义二进制协议（基于 socket）

---

## 11. 应用场景

### 11.1 开发调试

```bash
# 在大屏幕上测试 Android 应用
scrcpy -m 1080

# 配合 logcat
adb logcat | grep "my-app"
```

### 11.2 游戏直播

```bash
# 低延迟游戏直播
scrcpy --max-fps 120 --video-bit-rate=8M -f

# 录制游戏过程
scrcpy --record=gameplay.mp4 --max-fps 60
```

### 11.3 自动化测试

```bash
# 配合 shell 脚本自动化
adb shell input tap 100 100  # 点击坐标
sleep 1
scrcpy --stay-awake  # 保持屏幕常亮
```

### 11.4 远程演示

```bash
# 无线连接进行远程演示
adb connect <设备IP>:5555
scrcpy --window-title="远程演示"
```

---

## 12. 总结

**scrcpy** 是 Android 设备镜像控制的最佳开源解决方案：

| 优势 | 说明 |
|------|------|
| **无需 ROOT** | 直接使用，无需越狱 |
| **跨平台** | Linux/Windows/macOS |
| **高性能** | 30~120fps，低延迟 |
| **功能丰富** | 录制、音频、控制、游戏手柄 |
| **轻量快速** | 约 1 秒启动 |
| **开源免费** | Apache-2.0 |

**适用场景**：

- Android 应用开发调试
- 游戏直播和录制
- 自动化测试
- 远程演示和教学
- 日常使用（大屏幕操作手机）

**官方资源**：

- GitHub：https://github.com/Genymobile/scrcpy
- 官方文档：https://github.com/Genymobile/scrcpy#readme
- 作者博客：https://blog.rom1v.com/
- Reddit：r/scrcpy
- Twitter：@scrcpy_app