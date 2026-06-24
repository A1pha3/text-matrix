---
title: "scrcpy：138k Stars Android 屏幕镜像完全指南"
date: "2026-04-06T22:23:00+08:00"
slug: "scrcpy-android-screen-mirror-guide"
description: "全面介绍 138k Stars 的 scrcpy Android 屏幕镜像工具，涵盖安装配置、USB/无线连接、屏幕录制、音频转发、键盘鼠标/游戏手柄控制、OTG 模式、摄像头镜像、性能优化等全部功能。"
draft: false
categories: ["技术笔记"]
tags: ["scrcpy", "Android", "屏幕镜像", "无线调试", "ADB", "远程控制"]
---

## 目录

- [学习目标](#学习目标)
- [1. 项目概述](#1-项目概述)
- [2. 安装指南](#2-安装指南)
- [3. 连接设备](#3-连接设备)
- [4. 核心功能](#4-核心功能)
- [5. 控制方式](#5-控制方式)
- [6. 高级功能](#6-高级功能)
- [7. 性能优化](#7-性能优化)
- [8. 常见问题](#8-常见问题)
- [9. 快捷键汇总](#9-快捷键汇总)
- [10. 技术架构](#10-技术架构)
- [11. 应用场景](#11-应用场景)
- [12. 总结](#12-总结)
- [自测检查](#自测检查)
- [进阶路径](#进阶路径)

---

## 学习目标

阅读本文并完成练习后，你将能够：

- 在 Linux/Windows/macOS 上正确安装和配置 scrcpy
- 通过 USB 和无线两种方式连接 Android 设备
- 理解 scrcpy 的工作原理和性能瓶颈所在
- 根据使用场景调整分辨率和码率
- 熟练使用键盘、鼠标和游戏手柄控制设备
- 掌握 OTG 模式和摄像头镜像等高级功能
- 排查连接失败、延迟过高、音频不同步等常见问题

**预计阅读时间**：20 分钟
**实践时间**：30 分钟

---

## 1. 项目概述

### 1.1 是什么

**scrcpy**（发音为 "scr**een** **c**o**py**）是一个通过 USB 或 TCP/IP 无线连接来镜像和控制 Android 设备的应用程序。

为什么需要它？Android 开发者经常需要在电脑上查看手机屏幕——要么是为了演示，要么是因为手机屏幕太小看不清。Android Studio 自带的模拟器很重，真机调试又得低头看手机。scrcpy 把手机屏幕实时投到电脑上，还能用键盘鼠标直接操作，延迟低到几乎感觉不到。

不需要 ROOT 权限，也不需要在设备上安装任何应用——这是它相比其他方案最大的优势。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **138k** |
| GitHub Forks | **12.9k** |
| Contributors | **150+** |
| Releases | **50+** |
| 最新版本 | **v3.3.4** (2025-12-18) |
| License | **Apache-2.0** |
| 语言 | **C 63.9%**，Java 31.8% |

### 1.3 项目特点

| 特性 | 说明 |
|------|------|
| **轻量** | 原生 C 实现，只传输屏幕变化部分 |
| **高性能** | 30~120fps，具体取决于设备性能 |
| **高质量** | 支持 1920×1080 或更高分辨率 |
| **低延迟** | 35~70ms，足够的实时性 |
| **快速启动** | 约 1 秒显示首帧 |
| **无侵入** | 设备不留任何安装痕迹 |
| **无广告** | 无账号、无广告、无需联网 |
| **自由开源** | Apache-2.0 许可证 |

### 1.4 核心作者

**Romain Vimont** (@rom1v) 是主要作者和维护者。可以通过 [GitHub Sponsors](https://github.com/sponsors/rom1v)、[Liberapay](https://liberapay.com/rom1v) 或 PayPal 支持他的开源工作。

---

## 2. 安装指南

### 2.1 系统要求

**Android 设备要求**：

- Android 5.0（API 21）或更高版本（基础镜像功能）
- Android 11（API 30）或更高版本（音频转发）
- Android 12（API 31）或更高版本（摄像头镜像）

**电脑要求**：

- Linux / Windows / macOS 均可
- ADB 工具（通常已包含在 Android SDK 中，也可单独安装）

为什么需要 ADB？scrcpy 底层通过 ADB 与设备建立连接，然后在设备上启动一个临时服务端（scrcpy-server.jar）来处理屏幕捕获和输入事件。

### 2.2 Linux 安装

```bash
# Debian/Ubuntu
sudo apt install scrcpy

# Fedora
sudo dnf install scrcpy

# Arch Linux
sudo pacman -S scrcpy

# 从源码构建（需要 Android SDK 和 Meson）
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

1. 从 [GitHub Releases](https://github.com/Genymobile/scrcpy/releases) 下载最新版本
2. 解压到任意目录（建议 `C:\scrcpy`）
3. 将目录添加到 PATH 环境变量

> **Windows 用户注意**：手动安装时需要同时下载 `scrcpy-win64.zip` 和 `adb.zip`（如果系统没有 ADB），并将 ADB 也添加到 PATH。

### 2.4 macOS 安装

```bash
# Homebrew（推荐）
brew install scrcpy

# MacPorts
sudo port install scrcpy
```

---

## 3. 连接设备

### 3.1 USB 连接（最稳定）

**步骤 1：启用 USB 调试**

在 Android 设备上操作：

1. 设置 → 关于手机 → 连续点击"版本号"7 次（启用开发者模式）
2. 设置 → 开发者选项 → 启用"USB 调试"

> **为什么需要 USB 调试**？scrcpy 需要通过 ADB 向设备发送 shell 命令并启动服务端。USB 调试是 ADB 与设备通信的必要条件。

**步骤 2：连接电脑**

```bash
# 使用 USB 线连接设备后执行：
adb devices

# 首次连接时，设备上会弹出"允许 USB 调试吗？"对话框
# 勾选"一律允许使用这台计算机进行调试"后点击确定
```

预期输出：

```
List of devices attached
emulator-5554    device
```

如果看不到设备，检查：
- USB 线是否支持数据传输（有些线只能充电）
- 设备是否弹出了授权对话框
- 电脑上是否安装了正确的 USB 驱动（Windows）

**步骤 3：启动 scrcpy**

```bash
scrcpy
```

### 3.2 无线连接（推荐，但需要先 USB 配对）

无线连接比 USB 方便，但初次配置需要 USB 线。

**方法一：通过 USB 转发（传统方式）**

```bash
# 1. 先通过 USB 连接设备
# 2. 让 ADB 监听 TCP/IP 端口
adb tcpip 5555

# 3. 拔掉 USB 线
# 4. 通过 IP 连接（设备 IP 可在"设置 → 关于手机 → 状态"中查看）
adb connect 192.168.1.100:5555

# 5. 启动 scrcpy
scrcpy
```

**方法二：无线调试（Android 11+，无需 USB 线）**

Android 11 引入了"无线调试"功能，可以不通过 USB 完成配对：

1. 设置 → 开发者选项 → 无线调试 → 启用
2. 点击"使用配对码配对设备"
3. 在电脑上执行：

```bash
# 替换为设备上显示的配对码和端口
adb pair 192.168.1.100:41373
# 输入 6 位配对码
```

4. 配对成功后，连接设备：

```bash
adb connect 192.168.1.100:39513
scrcpy
```

### 3.3 多设备切换

当多台设备同时连接时，需要指定目标设备：

```bash
# 查看所有连接的设备
adb devices

# 输出示例：
# List of devices attached
# 192.168.1.100:5555    device
# emulator-5554    device

# 指定设备序列号
scrcpy -s 192.168.1.100:5555

# 或者使用设备 USB 序列号
scrcpy -s 1234567890abcdef
```

---

## 4. 核心功能

### 4.1 基础镜像

```bash
# 最简单的启动方式
scrcpy

# 限制分辨率（大幅提升性能，推荐）
scrcpy -m 1024

# 限制帧率
scrcpy --max-fps 60

# 同时指定分辨率和帧率
scrcpy -m 1024 --max-fps 60
```

**为什么限制分辨率能提升性能？** scrcpy 传输的是屏幕图像数据，分辨率越高，每秒需要传输的数据量越大。将分辨率限制在 1024 以下，可以显著减少带宽占用，降低延迟。

### 4.2 屏幕录制

```bash
# 录制屏幕到 MP4 文件（默认保存为 H.264 视频）
scrcpy --record=screen.mp4

# 录制时禁用音频（仅录制视频）
scrcpy --record=screen.mp4 --no-audio

# 指定录制分辨率
scrcpy --record=screen.mp4 -m 1920
```

录制时的性能影响：录制功能会在客户端（电脑）上同时写入视频文件，会占用一定的磁盘 I/O 和 CPU。如果电脑性能有限，建议降低录制分辨率。

### 4.3 音频转发

```bash
# Android 11+ 支持音频转发
scrcpy --audio

# 录制音频 + 视频
scrcpy --record=output.mp4 --audio
```

> **注意**：音频转发需要 Android 11 以上，且某些设备可能因为厂商定制 ROM 而不支持。

### 4.4 屏幕关闭镜像

```bash
# 镜像时关闭设备屏幕（节省电量，同时减少发热）
scrcpy --turn-screen-off

# 或按快捷键 Ctrl+Shift+O 切换屏幕开关
```

**适用场景**：已经熟悉操作后，可以关闭手机屏幕，只用电脑显示器。

### 4.5 复制粘贴

scrcpy 支持剪贴板同步：

```bash
# 自动同步剪贴板（默认启用）
scrcpy

# 禁用剪贴板自动同步
scrcpy --no-clipboard-autosync
```

**操作方式**：

- 电脑 → 设备：在 scrcpy 窗口中按 `Ctrl+V`
- 设备 → 电脑：在设备上复制，然后在电脑上按 `Ctrl+C`（需要 scrcpy 窗口处于焦点状态）

---

## 5. 控制方式

### 5.1 鼠标控制

| 操作 | 说明 |
|------|------|
| **左键点击** | 相当于点击设备屏幕对应位置 |
| **右键点击** | 返回键 |
| **中键点击** | HOME 键 |
| **滚轮** | 滚动列表（相当于滑动手势） |
| **拖拽文件到窗口** | 将文件推送到设备 `/sdcard/Download/` |

### 5.2 键盘控制

| 快捷键 | 功能 |
|--------|------|
| **Ctrl+H** | 返回键 |
| **Ctrl+S** | HOME 键 |
| **Ctrl+M** | 多任务键 |
| **Ctrl+↑/↓** | 音量调节 |
| **Ctrl+P** | 电源键（唤醒/锁屏） |
| **打字** | 直接在设备输入框中输入 |

### 5.3 游戏手柄支持

scrcpy 支持通过 USB HID 模拟游戏手柄输入：

```bash
# 启用游戏手柄控制（需要 Linux，且需要 uinput 权限）
scrcpy --gamepad=uhid

# 或使用短参数
scrcpy -G
```

**支持的游戏手柄按钮映射**：

- 左/右摇杆：相当于触摸滑动
- A/B/X/Y 按钮：点击屏幕对应区域
- LB/RB：菜单按钮
- Start/Select：返回/主页

> **注意**：游戏手柄支持在 Linux 上最稳定。Windows 和 macOS 可能需要额外配置。

### 5.4 OTG 模式

OTG 模式允许你只使用键盘和鼠标控制设备，不需要 USB 调试：

```bash
# OTG 模式（只需要 USB 连接，不需要 ADB）
scrcpy --otg

# 只启用键盘和鼠标（不需要 ADB，适合设备无法开启 USB 调试的场景）
scrcpy --otg --keyboard=uhid --mouse=uhid
```

**适用场景**：设备无法开启 USB 调试（例如某些 IoT 设备），或者只想用键盘鼠标操作而不需要屏幕镜像。

---

## 6. 高级功能

### 6.1 摄像头镜像

Android 12+ 支持将设备摄像头作为虚拟摄像头输出到电脑：

```bash
# 镜像后置摄像头
scrcpy --video-source=camera --camera-facing=back

# 镜像前置摄像头
scrcpy --video-source=camera --camera-facing=front

# 指定分辨率
scrcpy --video-source=camera --camera-size=1920x1080
```

**为什么这个功能有用？** 可以把 Android 设备当作电脑的高清摄像头使用，用于视频会议等场景。

### 6.2 V4L2 作为 webcam（Linux）

将 Android 摄像头暴露为 Linux 的虚拟摄像头设备，可以直接在 OBS、Zoom、Google Meet 中使用：

```bash
# 需要 Linux 内核支持 V4L2
scrcpy --video-source=camera --camera-facing=front --v4l2-sink=/dev/video0
```

### 6.3 虚拟显示器

创建独立于设备物理屏幕的虚拟显示器，适合多任务场景：

```bash
# 创建 1920x1080 虚拟显示器并自动启动 VLC 播放器
scrcpy --new-display=1920x1080 --start-app=org.videolan.vlc

# 创建自定义尺寸
scrcpy --new-display=1280x720
```

**为什么需要虚拟显示器？** 某些应用场景下，你希望设备在后台运行某个 App，同时在电脑上操作另一个 App，互不干扰。

### 6.4 窗口管理

```bash
# 禁用窗口装饰（无边框窗口）
scrcpy --window-no-decoration

# 指定窗口标题
scrcpy --window-title="我的 Pixel 7"

# 全屏启动
scrcpy -f

# 调整窗口大小（非分辨率，而是显示窗口的大小）
scrcpy --window-width=800 --window-height=600
```

---

## 7. 性能优化

### 7.1 降低分辨率

```bash
# 降至 720p（推荐平衡方案）
scrcpy -m 720

# 降至 480p（最低延迟，适合游戏）
scrcpy -m 480
```

**分辨率 vs 延迟**：分辨率每降低一档，带宽占用大约减少 50%~70%。如果网络环境不好，优先降低分辨率。

### 7.2 降低码率

```bash
# 降低视频码率（默认 8Mbps）
scrcpy --video-bit-rate=2M

# 极低码率（适合带宽受限的环境）
scrcpy --video-bit-rate=1M
```

### 7.3 选择编解码器

```bash
# 使用 H.265（更好压缩率，节省带宽）
scrcpy --video-codec=h265

# 使用 H.264（更广泛兼容，老旧设备推荐）
scrcpy --video-codec=h264
```

**H.265 vs H.264**：H.265 在相同画质下带宽占用比 H.264 低约 30%~50%，但需要设备硬件支持。如果启动时报错，换回 H.264。

### 7.4 组合优化方案

```bash
# 平衡方案：720p + 60fps + H.265（大多数场景推荐）
scrcpy -m 720 --max-fps 60 --video-codec=h265

# 极低延迟方案：480p + 120fps + H.265（游戏场景）
scrcpy -m 480 --max-fps 120 --video-bit-rate=1M

# 高质量方案：1080p + 60fps + H.264（演示场景）
scrcpy -m 1080 --max-fps 60 --video-codec=h264
```

---

## 8. 常见问题

### 8.1 权限问题

**症状**：出现错误 `"Injecting input events requires the caller to have the INJECT_EVENTS permission"`

**原因**：从 Android 4.2 开始，INPUT_EVENT 权限（INJECT_EVENTS）不再对普通应用开放，但 scrcpy-server 通过 ADB 以 shell 身份运行，理论上应该有这个权限。

**解决方案**：

1. 确认已启用"USB 调试"
2. 如果是 Android 12+，还需要启用"USB 调试（安全设置）"：
   - 设置 → 开发者选项 → USB 调试（安全设置）→ 启用
3. 重启设备后重试

### 8.2 设备检测不到

**症状**：`adb devices` 输出为空，或者显示 `unauthorized`。

**排查步骤**：

```bash
# 1. 重启 ADB 服务
adb kill-server
adb start-server

# 2. 检查设备授权状态
adb devices

# 3. 如果显示 unauthorized，在设备上允许授权对话框
# 如果看不到对话框，尝试撤销 USB 调试授权后重新连接：
# 设置 → 开发者选项 → 撤销 USB 调试授权
```

**其他可能原因**：

- USB 线不支持数据传输（换一根线）
- Windows 上缺少 USB 驱动（安装 Google USB Driver）
- 设备接口损坏（换个 USB 口试试）

### 8.3 延迟高

**症状**：画面卡顿，操作响应慢。

**优化方案**：

```bash
# 1. 降低分辨率（效果最明显）
scrcpy -m 720

# 2. 使用有线 USB 连接（比无线稳定得多）
# 3. 关闭设备后台应用（减少 CPU 占用）
# 4. 启用性能模式（部分设备支持）
# 5. 切换编解码器
scrcpy --video-codec=h265
```

**延迟测试**：可以用手机打开 https://www.toolster.dk/fps-test/ 然后在 scrcpy 窗口中观察，对比直接看手机屏幕的延迟差异。

### 8.4 音频不同步

**症状**：画面和声音对不上。

**解决方案**：

```bash
# 方案 1：禁用音频（如果只需要视频）
scrcpy --no-audio

# 方案 2：降低分辨率（减少视频解码延迟）
scrcpy -m 1024

# 方案 3：换用更低延迟的音频输出（Linux PulseAudio 用户）
# 在启动 scrcpy 前设置：
export PULSE_SERVER=unix:/tmp/pulse-socket
```

### 8.5 无线连接不稳定

**症状**：无线连接后经常断开。

**解决方案**：

- 确保电脑和设备在同一 5GHz Wi-Fi 频段（2.4GHz 干扰大）
- 减少距离路由器的距离
- 尝试固定设备的 IP 地址（防止 DHCP 重新分配）
- 降低分辨率和码率：`scrcpy -m 720 --video-bit-rate=2M`

---

## 9. 快捷键汇总

### 9.1 基础快捷键

| 快捷键 | 功能 |
|--------|------|
| **Ctrl+H** | 返回 |
| **Ctrl+M** | 多任务 |
| **Ctrl+S** | HOME |
| **Ctrl+P** | 电源（唤醒/锁屏） |
| **Ctrl+B** | 返回（替代方式） |
| **Alt+F** | 全屏 |
| **Alt+Enter** | 全屏（替代方式） |

### 9.2 屏幕控制

| 快捷键 | 功能 |
|--------|------|
| **鼠标中键** | HOME |
| **右键** | 返回 |
| **滚轮上/下** | 音量 +/- |
| **Ctrl+滚轮** | 缩放显示 |

### 9.3 文本输入

| 操作 | 说明 |
|------|------|
| **Ctrl+Z** | 启用/禁用文本注入模式 |
| **直接打字** | 输入英文（中文输入需要在设备上操作） |
| **Ctrl+V** | 从电脑剪贴板粘贴到设备 |
| **Ctrl+C** | 从设备复制（部分应用支持） |

---

## 10. 技术架构

### 10.1 组件结构

scrcpy 由以下组件构成：

| 组件 | 说明 | 技术栈 |
|------|------|--------|
| **scrcpy-client** | 桌面客户端，负责解码显示和接收输入 | C + SDL2 |
| **scrcpy-server** | Android 端服务，运行在设备上 | Java（Android SDK） |
| **ADB** | Android Debug Bridge，负责初始连接 | C++ |

### 10.2 工作流程

```
电脑 scrcpy-client ←[ADB forward]→ ADB daemon ←→ scrcpy-server ←[Surface]→ Android 设备屏幕
```

**关键流程**：

1. 用户运行 `scrcpy` 命令
2. scrcpy-client 通过 ADB 将 `scrcpy-server.jar` 推送到设备并执行
3. 设备端 scrcpy-server 通过 `MediaCodec` API 捕获屏幕并编码
4. 编码后的视频数据通过 socket 传回电脑端
5. 电脑端 scrcpy-client 用 SDL2 解码并显示，同时接收键盘鼠标输入并发送回设备

### 10.3 为什么延迟能这么低？

- **直接访问 Surface**：scrcpy-server 直接读取 `Surface` 的帧数据，不经过 Android 的窗口合成器
- **硬件编码**：使用设备的 Hardware Codec（MediaCodec）进行 H.264/H.265 编码
- **零拷贝传输**：编码后的数据直接通过 socket 发送，减少内存拷贝
- **客户端轻量**：C + SDL2 的实现比 Java 方案高效得多

---

## 11. 应用场景

### 11.1 开发调试

```bash
# 在大屏幕上测试 Android 应用（比看手机舒服得多）
scrcpy -m 1080

# 配合 logcat 实时查看日志
adb logcat | grep "my-app"

# 快速截图
adb exec-out screencap -p > screenshot.png
```

### 11.2 游戏直播

```bash
# 低延迟游戏直播（竞技类游戏）
scrcpy --max-fps 120 --video-bit-rate=8M -f

# 录制游戏过程
scrcpy --record=gameplay.mp4 --max-fps 60
```

### 11.3 自动化测试

```bash
# 配合 shell 脚本自动化操作
adb shell input tap 100 100  # 点击坐标 (100, 100)
adb shell input text "hello"   # 输入文本
adb shell input swipe 500 1000 500 500  # 滑动手势

# 保持屏幕常亮（自动化测试时不锁屏）
scrcpy --stay-awake
```

### 11.4 远程演示

```bash
# 无线连接进行远程演示（会议室场景）
adb connect <设备IP>:5555
scrcpy --window-title="产品演示 - Pixel 7"
```

---

## 12. 总结

**scrcpy** 是 Android 设备镜像控制的最佳开源解决方案，没有之一。

| 优势 | 说明 |
|------|------|
| **无需 ROOT** | 直接使用，不需要解锁 Bootloader |
| **跨平台** | Linux/Windows/macOS 全支持 |
| **高性能** | 30~120fps，延迟低至 35ms |
| **功能丰富** | 录制、音频、控制、游戏手柄、OTG |
| **轻量快速** | 约 1 秒启动 |
| **开源免费** | Apache-2.0，代码完全透明 |

**适用场景**：

- Android 应用开发调试（比 Android Studio 的镜像流畅）
- 游戏直播和录制（低延迟 + 高质量）
- 自动化测试（配合 ADB 脚本）
- 远程演示和教学（会议室大屏展示）
- 日常使用（在大屏幕上回消息比看手机舒服）

**官方资源**：

- GitHub：https://github.com/Genymobile/scrcpy
- 官方文档：https://github.com/Genymobile/scrcpy#readme
- 作者博客：https://blog.rom1v.com/
- Reddit 社区：r/scrcpy

---

## 自测检查

完成阅读后，请确认你能回答以下问题：

- [ ] scrcpy 为什么不需要 ROOT 权限？
- [ ] ADB 在 scrcpy 工作流程中扮演什么角色？
- [ ] 如何判断应该降低分辨率还是降低码率？
- [ ] OTG 模式和普通模式的核心区别是什么？
- [ ] 无线调试（Android 11+）和传统 TCP/IP 转发的区别？
- [ ] H.265 和 H.264 应该如何选择？
- [ ] 为什么某些设备不支持音频转发？
- [ ] 如何排查 `adb devices` 看不到设备的问题？

---

## 进阶路径

**如果你完成了本文的学习，可以继续探索：**

1. **源码研究**：阅读 scrcpy-client 和 scrcpy-server 的源码，理解 MediaCodec 和 SDL2 的使用方式
2. **二次开发**：基于 scrcpy 的协议开发自定义功能（例如批量设备管理）
3. **性能调优**：研究 Android 的 `SurfaceFlinger` 和 `MediaCodec` 底层机制
4. **替代方案对比**：了解 Vysor、AirDroid、TeamViewer 等方案的优缺点
5. **自动化集成**：将 scrcpy 集成到 CI/CD 流水线中，实现自动化 UI 测试

**推荐阅读**：

- [scrcpy 官方文档](https://github.com/Genymobile/scrcpy#readme)
- [Android MediaCodec 官方文档](https://developer.android.com/reference/android/media/MediaCodec)
- [ADB 协议文档](https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/main/protocol.txt)

---

## 练习

### 练习 1：基础连接（预计 10 分钟）

在你的 Android 设备上启用 USB 调试，然后通过 USB 连接电脑并启动 scrcpy。尝试用鼠标键盘操作设备。

**验收标准**：scrcpy 窗口正常显示设备屏幕，鼠标点击和键盘输入都能正确响应。

### 练习 2：无线连接配置（预计 15 分钟）

不通过 USB 线，使用 Android 11+ 的"无线调试"功能完成配对和连接。

**验收标准**：拔掉 USB 线后，scrcpy 仍能正常镜像设备屏幕。

### 练习 3：性能调优实验（预计 10 分钟）

分别用以下参数启动 scrcpy，观察延迟和画质的差异：

```bash
scrcpy -m 480 --max-fps 120  # 方案 A
scrcpy -m 1080 --max-fps 60  # 方案 B
scrcpy -m 720 --video-codec=h265  # 方案 C
```

**验收标准**：能说清楚三种方案分别适合什么场景。

### 练习 4：屏幕录制（预计 5 分钟）

录制一段 30 秒的设备屏幕操作，然后用视频播放器查看录制结果。

```bash
scrcpy --record=test.mp4
# 操作 30 秒后按 Ctrl+C 停止录制
```

**验收标准**：`test.mp4` 文件正常生成且可以播放。
