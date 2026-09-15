---
title: "scrcpy：近 15 万 Stars Android 屏幕镜像完全指南"
date: "2026-09-01T10:00:00+08:00"
lastmod: "2026-09-14T00:00:00+08:00"
slug: "scrcpy-android-screen-mirror-guide"
github_repo: "Genymobile/scrcpy"
source_key: "gh:Genymobile/scrcpy"
description: "全面介绍 GitHub 近 15 万 Stars 的 scrcpy Android 屏幕镜像与控制工具，涵盖安装配置、USB/无线连接、屏幕录制、音频转发、键盘鼠标/游戏手柄控制、OTG 模式、摄像头镜像、虚拟显示器、性能优化与常见问题排查。"
draft: false
categories: ["技术笔记"]
tags: ["Android"]
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
- 掌握 OTG 模式、摄像头镜像和虚拟显示器等高级功能
- 排查连接失败、延迟过高、音频不同步等常见问题

**预计阅读时间**：20 分钟
**实践时间**：30 分钟

---

## 1. 项目概述

### 1.1 是什么

**scrcpy**（发音为 "screen copy"）是一个通过 USB 或 TCP/IP 无线连接来镜像和控制 Android 设备的应用程序，同时转发视频和音频。

为什么需要它？Android 开发者经常需要在电脑上查看手机屏幕——要么是为了演示，要么是因为手机屏幕太小看不清。Android Studio 自带的模拟器很重，真机调试又得低头看手机。scrcpy 把手机屏幕实时投到电脑上，还能用键盘鼠标直接操作，延迟低到几乎感觉不到。

不需要 ROOT 权限，也不需要在设备上安装任何应用——这是它相比其他方案最大的优势。

### 1.2 核心数据

| 指标 | 数值 |
|------|------|
| GitHub Stars | **149,535**（截至 2026-09-14） |
| GitHub Forks | **13.7k** |
| Contributors | **177** |
| Releases | **52** |
| 最新版本 | **v4.1**（2026-07-12 发布） |
| License | **Apache-2.0** |
| 语言 | **C 63.0%**，Java 32.7% |

### 1.3 项目特点

| 特性 | 说明 |
|------|------|
| **轻量** | 原生 C 实现，窗口里只显示设备屏幕本身 |
| **高性能** | 30~120fps，取决于设备性能 |
| **高质量** | 支持 1920×1080 或更高分辨率 |
| **低延迟** | 35~70ms |
| **快速启动** | 约 1 秒显示首帧 |
| **无侵入** | 设备上不留任何安装痕迹 |
| **无附加条件** | 无账号、无广告、无需联网 |
| **自由软件** | Apache-2.0 许可证 |

其中 30~120fps、35~70ms、约 1 秒首帧这几组数字都来自官方 README 的自述口径。

### 1.4 核心作者

**Romain Vimont**（@rom1v）是主要作者和维护者。可以通过 [GitHub Sponsors](https://github.com/sponsors/rom1v)、[Liberapay](https://liberapay.com/rom1v/) 或 [PayPal](https://paypal.me/rom2v) 支持他的开源工作。

---

## 2. 安装指南

### 2.1 系统要求

**Android 设备要求**：

- Android 5.0（API 21）或更高版本（基础镜像功能）
- Android 11（API 30）或更高版本（音频转发）
- Android 12（API 31）或更高版本（摄像头镜像）

**电脑要求**：

- Linux / Windows / macOS 均可
- ADB 工具（Windows/macOS 的安装包通常已随 scrcpy 一起装好，详见下文各平台说明）

ADB 的角色：scrcpy 通过它与设备建立连接，把一个服务端程序推到设备上运行，由服务端负责屏幕捕获和输入事件注入。USB 调试（ADB）是这条链路的前提——唯一的例外是 5.4 节的 OTG 模式。

### 2.2 Linux 安装

**官方静态构建（推荐，版本最新）**：从 [GitHub Releases](https://github.com/Genymobile/scrcpy/releases) 下载 `scrcpy-linux-x86_64-v4.1.tar.gz`，解压即可运行。

**发行版包管理器**：

```bash
# Arch Linux
sudo pacman -S scrcpy

# Fedora（第三方 COPR 仓库，官方仓库无此包）
sudo dnf copr enable zeno/scrcpy
sudo dnf install scrcpy
```

> **注意**：Debian/Ubuntu 官方仓库和 Snap 商店里的 scrcpy 版本严重滞后，官方文档已明确将其标注为"过时版本"，不建议使用。

**从源码安装**（官方简化流程，适用于已发布版本）：

```bash
# Debian/Ubuntu 先装依赖
sudo apt install ffmpeg libsdl3-0 libusb-1.0-0 adb wget \
                 gcc git pkg-config meson ninja-build libsdl3-dev \
                 libavcodec-dev libavdevice-dev libavformat-dev libavutil-dev \
                 libswresample-dev libusb-1.0-0-dev libv4l-dev

# 克隆仓库并执行安装脚本
git clone https://github.com/Genymobile/scrcpy.git
cd scrcpy
./install_release.sh

# 之后出新版本时更新
git pull
./install_release.sh
```

其他发行版的包名和构建细节见官方 `doc/linux.md` 与 `doc/build.md`。

### 2.3 Windows 安装

**方法一：WinGet（推荐）**

```bash
winget install --exact Genymobile.scrcpy
```

WinGet 会在安装 scrcpy 的同时自动装好 ADB 等依赖。

**方法二：Chocolatey 或 Scoop**

```bash
choco install scrcpy
choco install adb    # 如果系统里还没有 ADB

scoop install scrcpy
scoop install adb    # 如果系统里还没有 ADB
```

**方法三：手动下载**

1. 从 [GitHub Releases](https://github.com/Genymobile/scrcpy/releases) 下载 `scrcpy-win64-v4.1.zip`（32 位系统选 win32 版）
2. 解压到任意目录（建议加入 PATH 环境变量）

发布包里已经包含 `adb.exe` 等全部依赖，不需要再单独下载 ADB。两个实用细节：目录里的 `open_a_terminal_here.bat` 可以就地打开终端；想免控制台运行就双击 `scrcpy-noconsole.vbs`（但出错信息也看不到，排查问题时建议临时加 `--pause-on-exit=if-error` 让窗口在报错时停住）。

### 2.4 macOS 安装

```bash
# Homebrew（推荐）
brew install scrcpy

# adb 需要单独装（如果还没有）
brew install --cask android-platform-tools

# MacPorts 会自动配好 adb，一步到位
sudo port install scrcpy
```

---

## 3. 连接设备

### 3.1 USB 连接（最稳定）

**步骤 1：启用 USB 调试**

在 Android 设备上操作：

1. 设置 → 关于手机 → 连续点击"版本号"7 次（启用开发者模式）
2. 设置 → 开发者选项 → 启用"USB 调试"

> USB 调试是必要条件：scrcpy 要通过 ADB 向设备推送服务端并以 shell 身份运行它，缺少它整条链路无从建立。

**步骤 2：连接电脑**

```bash
# 使用 USB 线连接设备后执行：
adb devices

# 首次连接时，设备上会弹出"允许 USB 调试吗？"对话框
# 勾选"一律允许使用这台计算机进行调试"后点击确定
```

预期输出：

```text
List of devices attached
0123456789abcdef    device
```

如果看不到设备，检查：

- USB 线是否支持数据传输（有些线只能充电）
- 设备是否弹出了授权对话框
- 电脑上是否安装了正确的 USB 驱动（Windows）

**步骤 3：启动 scrcpy**

```bash
scrcpy
```

### 3.2 无线连接

无线连接比 USB 方便。推荐先插一次 USB 线完成配置，之后就可以完全无线上使用。

**方法一：`--tcpip` 自动模式（最省事）**

```bash
# 设备先用 USB 线连着电脑，scrcpy 自动获取设备 IP、
# 开启 TCP/IP 模式并连接，然后正常启动
scrcpy --tcpip

# 设备已经在监听 TCP/IP（或你已知 IP）时，直接指定地址，默认端口 5555
scrcpy --tcpip=192.168.1.100
scrcpy --tcpip=192.168.1.100:5555
```

**方法二：手动 ADB 转发（传统方式）**

```bash
# 1. 先通过 USB 连接设备
# 2. 让 ADB 监听 TCP/IP 端口
adb tcpip 5555

# 3. 查询设备 IP（也可以在"设置 → 关于手机 → 状态"里看）
adb shell ip route | awk '{print $9}'

# 4. 拔掉 USB 线，通过 IP 连接
adb connect 192.168.1.100:5555

# 5. 启动 scrcpy
scrcpy

# 用完后断开
adb disconnect
```

**方法三：无线调试配对（Android 11+，全程无需 USB 线）**

Android 11 引入了"无线调试"功能，可以不通过 USB 完成配对：

1. 设置 → 开发者选项 → 无线调试 → 启用
2. 点击"使用配对码配对设备"
3. 在电脑上执行：

```bash
# 替换为设备上显示的配对地址和端口
adb pair 192.168.1.100:41373
# 输入 6 位配对码
```

4. 配对成功后，连接无线调试页面上显示的地址和端口：

```bash
adb connect 192.168.1.100:39513
scrcpy
```

### 3.3 多设备切换

当多台设备同时连接时，需要指定目标设备：

```bash
# 查看所有连接的设备
adb devices

# 指定设备序列号（TCP/IP 连接时序列号就是 ip:port）
scrcpy -s 192.168.1.100:5555
scrcpy -s 0123456789abcdef

# 只有一台 USB 设备 / 只有一台 TCP/IP 设备时可以偷懒
scrcpy -d   # 选择 USB 设备
scrcpy -e   # 选择 TCP/IP 设备

# 也可以用环境变量（对 adb 同样生效）
export ANDROID_SERIAL=0123456789abcdef
scrcpy
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

`-m` 限制的是宽高中较长的一边，另一边按设备宽高比自动计算——一台 1920×1080 的设备在 `-m 1024` 下会镜像为 1024×576。

**为什么限制分辨率能提升性能？** scrcpy 传输的是设备端编码后的图像数据，分辨率越高，编码和传输的数据量越大。降分辨率是所有优化手段里收益最直接的一项。

还有一个容易误解的点：`--max-fps` 是上限而不是目标。屏幕内容没有变化时不会产生新帧——设备停在静止画面上，实际帧率就是 0。

### 4.2 屏幕录制

```bash
# 录制屏幕到 MP4 文件
scrcpy --record=screen.mp4

# 只录视频不录音频
scrcpy --record=screen.mp4 --no-audio

# 只录音频
scrcpy --no-video --record=audio.opus

# 指定录制分辨率
scrcpy --record=screen.mp4 -m 1920

# 限制录制时长（秒）
scrcpy --record=screen.mkv --time-limit=20
```

几条官方口径：

- 容器格式按文件扩展名自动选择，支持 MP4、Matroska（`.mkv`/`.mka`）、OPUS、FLAC、WAV 等
- 时间戳在设备端打点，所以网络抖动不会写进录制文件，录制结果始终是干净的
- 录制的同时还在电脑上播放视频会占额外资源，只录不看时可以加 `--no-playback`（或 `--no-window`）关掉回放窗口

### 4.3 音频转发

```bash
# Android 11+ 支持音频转发，v2.0 起默认开启
scrcpy

# 显式指定音频源
scrcpy --audio-source=output        # 设备音频输出（默认，且设备本地会静音）
scrcpy --audio-source=mic           # 麦克风
scrcpy --audio-source=mic-unprocessed   # 未处理的麦克风原始音频
scrcpy --audio-source=voice-communication  # 语音通话（含回声消除等处理）

# Android 13+ 可以让设备本地继续出声（默认 --audio-dup 隐含 playback 源）
scrcpy --audio-dup
```

几个边界要知道：

- Android 11 设备启动音频转发前必须解锁屏幕，否则捕获会失败（scrcpy 会短暂弹一个伪窗口骗过系统前台检查）
- Android 10 及以下不支持音频捕获，scrcpy 会自动禁用音频继续投屏，不会因此启动失败；希望"没音频就报错"的话加 `--require-audio`
- 音频源还有 `playback`（Android 13+，应用可自行拒绝被捕获）、`voice-call` 等多种，完整列表见官方 `doc/audio.md`
- 播放报 `Failed to initialize audio/opus` 说明设备没有 Opus 编码器，改用 `--audio-codec=aac`

### 4.4 屏幕关闭镜像

```bash
# 启动时关闭设备屏幕（省电、少发热），电脑端保持镜像
scrcpy --turn-screen-off
scrcpy -S  # 短参数

# 运行中：MOD+O 关闭设备屏幕 / MOD+Shift+O 重新点亮（镜像不中断）

# 搭配 --stay-awake 防止设备休眠
scrcpy -Sw
```

**适用场景**：已经熟悉操作后，可以关闭手机屏幕，只用电脑显示器。

### 4.5 复制粘贴

scrcpy 支持剪贴板双向同步，设备剪贴板一有变化就自动同步到电脑；`Ctrl+C/X/V` 等组合键会原样转发给设备上的应用处理。

```bash
# 禁用剪贴板自动同步
scrcpy --no-clipboard-autosync
```

**操作方式**（仅支持 Android 7+）：

- 电脑 → 设备：在 scrcpy 窗口中按 `MOD+v`（同步电脑剪贴板并粘贴）
- 设备 → 电脑：在设备上复制，然后在 scrcpy 窗口按 `MOD+c`（或 `MOD+x` 剪切）
- 若应用不支持粘贴（如 Termux），可用 `MOD+Shift+v` 把电脑剪贴板内容作为按键序列注入（可能破坏非 ASCII 内容）
- 个别设备程序化设置剪贴板行为异常时，试试 `--legacy-paste`

> **安全提示**：通过 `Ctrl+v` 或 `MOD+v` 粘贴时，内容会被写入 Android 系统剪贴板，任何应用都可能读到它。不要用这种方式粘贴密码等敏感内容。

> 注意：这里用 `MOD` 指代快捷键修饰键，默认是左 `Alt` 或左 `Super`（Windows 键 / Command 键），可用 `--shortcut-mod` 自定义。下文所有快捷键同理。

---

## 5. 控制方式

### 5.1 鼠标控制

| 操作 | 说明 |
|------|------|
| **左键点击** | 相当于点击设备屏幕对应位置 |
| **右键点击** | 返回键（屏幕亮时）；点亮屏幕（屏灭时） |
| **中键点击** | HOME 键 |
| **第 4 键** | 多任务键（APP_SWITCH） |
| **第 5 键** | 展开通知栏 |
| **滚轮** | 滚动列表（相当于滑动手势） |
| **Ctrl+拖拽** | 模拟双指捏合缩放/旋转 |
| **Shift+拖拽** | 模拟双指垂直倾斜 |
| **Ctrl+Shift+拖拽** | 模拟双指水平倾斜 |
| **拖入 APK 文件** | 安装 APK 到设备 |
| **拖入其他文件** | 将文件推送到设备 `/sdcard/Download/`（可用 `--push-target` 改目录） |

带 Shift 的次级点击（如 `Shift+右键`）会把点击原样注入设备，而不是触发快捷键。捏合等手势只在默认的 `--mouse=sdk` 模式下可用。

### 5.2 键盘控制

scrcpy 默认用 `MOD`（左 Alt 或左 Super）作为快捷键前缀，所有 `Ctrl+*` 组合键会原样透传给设备，由设备上的应用处理。

| 快捷键 | 功能 |
|--------|------|
| **MOD+H** | HOME 键 |
| **MOD+B** | 返回键（Back） |
| **MOD+S** | 多任务键（App Switch） |
| **MOD+M** | 菜单键 |
| **MOD+↑/↓** | 音量调节 |
| **MOD+P** | 电源键（唤醒/锁屏） |
| **打字** | 直接在设备输入框中输入 |

打字默认走 `--keyboard=sdk` 模式：在 Android API 层注入输入事件，处处可用，但只支持 ASCII 等有限字符。日常使用建议换成物理键盘模拟模式：

```bash
scrcpy --keyboard=uhid
scrcpy -K  # 短参数
```

UHID 模式把电脑键盘模拟成插在设备上的物理键盘，支持全部字符和输入法（包括中文），还能关掉屏幕软键盘；代价是需要在设备上把物理键盘布局配置成和电脑一致（scrcpy 窗口里按 `MOD+K` 打开配置页），且老版本 Android 可能因权限问题不可用。

### 5.3 游戏手柄支持

scrcpy 可以把电脑上插着的每只物理手柄，逐一模拟成设备端的 HID 游戏手柄。默认关闭，需要显式启用：

```bash
# UHID 模式：通过设备内核 UHID 模块模拟，USB/无线连接都可用
scrcpy --gamepad=uhid
scrcpy -G  # 短参数

# AOA 模式：走 AOAv2 协议在 USB 层直接工作，不需要 ADB/USB 调试
scrcpy --gamepad=aoa
```

两种模式怎么选：

- **UHID**：通用性最好。老版本 Android 可能因权限问题不可用。
- **AOA**：仅 USB 连接可用，但可以配合 OTG 模式在无 USB 调试的设备上使用；多只手柄会被设备识别成一只行为异常的手柄（官方文档原话），需要多手柄请用 UHID；Windows 上镜像运行时可能无法使用（USB 设备已被 adb 占用）。

### 5.4 OTG 模式

OTG 模式让你只用键盘和鼠标控制设备，完全不需要 USB 调试（ADB）：

```bash
# OTG 模式（只需要 USB 连接，不需要 ADB）
scrcpy --otg

# 多台 USB 设备时指定序列号
scrcpy --otg -s 0123456789abcdef

# 禁用键盘或鼠标（默认两者都启用）
scrcpy --otg --keyboard=disabled
scrcpy --otg --mouse=disabled

# 启用游戏手柄（默认关闭；OTG 模式下 -G 等价于 aoa）
scrcpy --otg --gamepad=aoa
scrcpy --otg -G  # 短参数
```

**工作原理**：OTG 模式下视频和音频被禁用，scrcpy 隐式启用 `--keyboard=aoa` 和 `--mouse=aoa`，通过 AOAv2 协议把电脑键盘、鼠标模拟成直接插在设备上的物理外设——等效于用 OTG 线连接。该模式仅适用于 USB 连接。

**注意**：OTG 的目的是"免 USB 调试控制设备"。如果只是想"不投屏、仅控制"且 USB 调试已开启，不必用 OTG，直接用 `--no-video --no-audio -KMG`（UHID 模式，还支持无线）即可。

---

## 6. 高级功能

### 6.1 摄像头镜像

Android 12+ 支持把设备摄像头当作视频源：

```bash
# 镜像后置/前置摄像头
scrcpy --video-source=camera --camera-facing=back
scrcpy --video-source=camera --camera-facing=front

# 指定分辨率
scrcpy --video-source=camera --camera-size=1920x1080

# 指定帧率（默认 30fps）
scrcpy --video-source=camera --camera-fps=60

# 列出设备可用摄像头及声明的分辨率、帧率
scrcpy --list-cameras
scrcpy --list-camera-sizes
```

**为什么这个功能有用？** 可以把 Android 设备当作电脑的高清摄像头，用于视频会议等场景。摄像头模式下音频源会自动切换为麦克风（可用 `--audio-source=output` 改回设备扬声器）。

更多控制项：`--camera-id` 按 ID 选摄像头（指定后不能再加 `--camera-facing`）、`--camera-ar` 按宽高比选分辨率、`--camera-high-speed` 高速捕获模式；v4.0 起支持手电筒（`--camera-torch` 启动即开，运行中用 `MOD+T`/`MOD+Shift+T` 开关）和变焦（`--camera-zoom=1.5`，运行中用 `MOD+↑/↓` 调节——注意此模式下这两个键不再是音量键）。

一个官方提醒：`--list-camera-sizes` 列出的分辨率和帧率是设备声明值，不一定全部真实可用，也有能用的没被声明。

### 6.2 V4L2 作为 webcam（Linux）

将 Android 画面暴露为 Linux 的虚拟摄像头设备，可以直接在 OBS、Zoom、Google Meet 中使用。前提是先安装并加载 v4l2loopback 内核模块：

```bash
sudo apt install v4l2loopback-dkms
sudo modprobe v4l2loopback
```

然后启动 scrcpy：

```bash
# 把屏幕投到虚拟摄像头，不在电脑上开播放窗口
scrcpy --v4l2-sink=/dev/video0 --no-video-playback

# 或把前置摄像头当 webcam 用
scrcpy --video-source=camera --camera-facing=front --v4l2-sink=/dev/video0 --no-playback
```

设备编号用 `ls /dev/video*` 确认。如果 Chrome/WebRTC 检测不到设备，用 `sudo modprobe v4l2loopback exclusive_caps=1` 重新加载模块。

### 6.3 虚拟显示器

创建独立于设备物理屏幕的虚拟显示器，适合多任务场景：

```bash
# 创建 1920x1080 虚拟显示器并自动启动 VLC 播放器
scrcpy --new-display=1920x1080 --start-app=org.videolan.vlc

# 不带参数则使用主显示器的尺寸和密度；也可强制指定 DPI
scrcpy --new-display=1920x1080/420

# Flex 可变尺寸显示器（v4.0+）：分辨率跟随窗口大小实时调整
scrcpy --new-display -x --start-app=org.videolan.vlc
```

**为什么需要虚拟显示器？** 设备物理屏幕上干一件事，电脑窗口里同时干另一件事，互不干扰——比如手机上开会，电脑窗口里跑自动化脚本。两个配套选项：`--keep-active` 防止虚拟显示器休眠；默认关闭 scrcpy 时虚拟显示器连同里面的应用一起销毁，想保留就加 `--no-vd-destroy-content`，应用会被移回主屏。

### 6.4 窗口管理

```bash
# 无边框窗口（去掉窗口装饰）
scrcpy --window-borderless

# 指定窗口标题
scrcpy --window-title="我的 Pixel 7"

# 全屏启动
scrcpy -f

# 指定初始窗口位置和大小（改变的是窗口，不是镜像分辨率）
scrcpy --window-x=100 --window-y=100 --window-width=800 --window-height=600

# 窗口置顶
scrcpy --always-on-top
```

---

## 7. 性能优化

### 7.1 降低分辨率

```bash
# 降至 720p（推荐的平衡方案）
scrcpy -m 720

# 降至 480p（最低开销，适合游戏）
scrcpy -m 480
```

分辨率直接决定编码数据量，是收益最大的优化项。顺带一提，如果编码失败，scrcpy 会自动降低分辨率重试（可用 `--no-downsize-on-error` 关闭）。

### 7.2 降低码率

```bash
# 默认视频码率 8Mbps
scrcpy --video-bit-rate=2M

# 带宽受限环境
scrcpy --video-bit-rate=1M
```

### 7.3 选择编解码器

```bash
scrcpy --video-codec=h264  # 默认
scrcpy --video-codec=h265
scrcpy --video-codec=av1   # 需设备支持（官方：AV1 编码器目前在 Android 设备上并不普及）
scrcpy --video-codec=vp8   # v4.1+
scrcpy --video-codec=vp9   # v4.1+
```

官方口径是：H.265 同码率下画质更好，H.264 延迟更低；AV1 编码器目前在 Android 设备上并不普及。VP8/VP9 是 v4.1 新增的，面向少数不支持 H.264/H.265/AV1 的设备。

如果默认编码器有问题甚至崩溃，可以列出并更换编码器：

```bash
scrcpy --list-encoders
scrcpy --video-codec=h264 --video-encoder=OMX.qcom.video.encoder.avc
```

### 7.4 组合优化方案

```bash
# 平衡方案：720p + 60fps + H.265（大多数场景）
scrcpy -m 720 --max-fps 60 --video-codec=h265

# 高画质演示：1080p + H.264（兼容性最好）
scrcpy -m 1080 --video-codec=h264

# 低延迟游戏：低分辨率 + 高帧率，码率给足避免画面糊
scrcpy -m 480 --max-fps 120 --video-bit-rate=8M
```

反方向的取舍也存在：如果不交互、只想看视频，加大缓冲换流畅更划算——`scrcpy --video-buffer=200 --audio-buffer=200`。

---

## 8. 常见问题

### 8.1 权限问题

**症状**：出现错误 `Injecting input events requires the caller (or the source of the instrumentation, if any) to have the INJECT_EVENTS permission.`

**原因**：官方 README 明确说明，这个问题出现在部分设备上（尤其是小米），注入输入事件需要额外权限。

**解决方案**：

1. 确认已启用"USB 调试"
2. 另行启用"USB 调试（安全设置）"——这是与"USB 调试"不同的另一个选项：设置 → 开发者选项 → USB 调试（安全设置）→ 启用
3. 重启设备后重试（官方说明此选项设置后必须重启）

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
# 3. 切换到 H.264（官方口径：H.264 延迟更低）
scrcpy --video-codec=h264
```

**定位工具**：`scrcpy --print-fps` 在控制台打印实际帧率，或运行中按 `MOD+i` 开关 FPS 计数——先确认瓶颈是帧率上不去还是延迟叠加，再对症下药。

**实测方法**：用另一台设备拍一段视频，让手机屏幕和电脑窗口同框，对比两者对同一操作的响应时间差，逐帧播放就能读出延迟。

### 8.4 音频不同步或有杂音

**症状**：画面和声音对不上，或声音有"机械音"、爆音。

**解决方案**：

```bash
# 方案 1：不需要声音就直接关掉
scrcpy --no-audio

# 方案 2：加大音频缓冲（默认 50ms），以延迟换连贯
scrcpy --audio-buffer=100

# 方案 3：只是看视频不交互时，视频音频一起加缓冲最平滑
scrcpy --video-buffer=200 --audio-buffer=200

# 方案 4：声音"机械音"、断续时微调音频输出缓冲（默认 10ms，无把握别动）
scrcpy --audio-output-buffer=5
```

官方文档特别提醒：音频缓冲不可避免，太小会欠载（杂音），太大会延迟，目标是找到平衡点。

### 8.5 无线连接不稳定

**症状**：无线连接后经常断开。

**解决方案**：

- 电脑和设备尽量连同一个 5GHz Wi-Fi 频段（2.4GHz 干扰大）
- 不要离路由器太远
- 固定设备的 IP 地址（防止 DHCP 重新分配）
- 降低分辨率和码率：`scrcpy -m 720 --video-bit-rate=2M`
- 用完记得 `adb disconnect`，避免残留的无效连接干扰下次连接

---

## 9. 快捷键汇总

### 9.1 基础快捷键

`MOD` 默认是左 `Alt` 或左 `Super`（Windows 键 / Command 键），可用 `--shortcut-mod` 修改（可选值：`lctrl`、`rctrl`、`lalt`、`ralt`、`lsuper`、`rsuper`）。

| 快捷键 | 功能 |
|--------|------|
| **MOD+H** | HOME（返回桌面），或鼠标中键 |
| **MOD+B** | BACK（返回），或鼠标右键，或 MOD+Backspace |
| **MOD+S** | 多任务（App Switch），或鼠标第 4 键 |
| **MOD+M** | 菜单键（解锁屏幕用；对 react-native 开发中的应用触发开发菜单） |
| **MOD+↑/↓** | 音量调节 |
| **MOD+P** | 电源（唤醒/锁屏） |
| **MOD+Q** | 退出 scrcpy（v4.0+） |
| **MOD+F** 或 **F11** | 全屏切换（F11 为 v4.0 新增） |
| **MOD+G** | 窗口 1:1（像素完美） |
| **MOD+W** | 去除黑边（或双击黑边） |

### 9.2 屏幕与显示控制

| 快捷键 | 功能 |
|--------|------|
| **MOD+←/→** | 向左/向右旋转显示方向 |
| **MOD+Shift+←/→** | 水平翻转 |
| **MOD+Shift+↑/↓** | 垂直翻转 |
| **MOD+Z** | 暂停显示（再按仍是暂停） |
| **MOD+Shift+Z** | 恢复显示 |
| **MOD+Shift+R** | 重置视频捕获/编码 |
| **MOD+R** | 旋转设备屏幕 |
| **MOD+O** | 关闭设备屏幕（保持镜像） |
| **MOD+Shift+O** | 重新点亮设备屏幕 |
| **MOD+N** | 展开通知栏（或鼠标第 5 键） |
| **MOD+N+N** | 展开设置面板 |
| **MOD+Shift+N** | 收起面板 |
| **MOD+I** | 开/关 FPS 计数（输出到控制台） |
| **MOD+K** | 打开物理键盘布局设置（仅 HID 键盘模式） |
| **MOD+T / MOD+Shift+T** | 开/关摄像头手电筒（仅摄像头模式） |
| **MOD+↑/↓** | 摄像头变焦（仅摄像头模式） |

### 9.3 剪贴板与文本输入

| 操作 | 说明 |
|--------|------|
| **MOD+C** | 将设备剪贴板复制到电脑（Android 7+） |
| **MOD+X** | 剪切（设备 → 电脑，Android 7+） |
| **MOD+V** | 同步剪贴板并粘贴到设备（Android 7+） |
| **MOD+Shift+V** | 将电脑剪贴板内容作为按键序列注入 |
| **直接打字** | sdk 模式输入 ASCII 字符；UHID 模式（`-K`）支持全部字符和输入法（含中文） |
| **拖入 APK 文件** | 安装 APK |
| **拖入其他文件** | 推送文件到设备（默认 `/sdcard/Download/`） |

连击类快捷键的按键方式：按住 `MOD`，再双击目标键，最后松开 `MOD`。

---

## 10. 技术架构

### 10.1 组件结构

scrcpy 由以下部分构成：

| 组件 | 说明 | 技术栈 |
|------|------|--------|
| **scrcpy 客户端** | 桌面端，负责解码显示和输入采集 | C + FFmpeg + SDL3（v4.0 从 SDL2 迁移） |
| **scrcpy-server** | 设备端服务，由客户端随启动推入设备 | Java（Android SDK） |
| **ADB** | Android Debug Bridge，负责建立隧道 | C++（Google platform-tools） |

### 10.2 工作流程

```text
电脑 scrcpy 客户端 ←[adb 隧道（本地 socket）]→ adb daemon ←→ 设备端 scrcpy-server ←[MediaCodec]→ 屏幕内容/摄像头
```

**关键流程**：

1. 用户运行 `scrcpy` 命令
2. 客户端通过 adb 把内嵌的 scrcpy-server 推送到设备，以 shell 身份启动
3. server 端用 Android 的 `MediaCodec` API 建立视频/音频编码器，将显示器内容（或摄像头画面）作为编码输入
4. 编码后的码流经 adb 隧道传回电脑端
5. 客户端用 FFmpeg 解码、SDL3 渲染显示，同时把键鼠输入按所选模式（API 注入或 HID 模拟）发回设备

### 10.3 为什么延迟能这么低？

官方口径的 35~70ms 来自作者对链路的持续优化（详见 [PR #646](https://github.com/Genymobile/scrcpy/pull/646)），机制上可以归结为四点：

- **设备端硬件编码**：`MediaCodec` 走设备硬件编码器，网络上传的是压缩码流而非原始帧
- **客户端零缓冲**：默认不加视频缓冲，解码后立即渲染
- **直连链路**：USB 或局域网点对点传输，没有中间服务器
- **编码器低延迟配置**：v4.0 起把 `MediaCodec` 的 `KEY_PRIORITY` 和 `KEY_LATENCY` 显式设为最小值

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

### 11.2 游戏录制与演示

```bash
# 高帧率投屏，配合 OBS 等工具窗口采集
scrcpy --max-fps 120 --video-bit-rate=8M -f

# 直接录制游戏过程
scrcpy --record=gameplay.mp4 --max-fps 60
```

### 11.3 自动化测试

```bash
# 配合 shell 脚本自动化操作
adb shell input tap 100 100               # 点击坐标 (100, 100)
adb shell input text "hello"              # 输入文本
adb shell input swipe 500 1000 500 500    # 滑动手势

# 保持屏幕常亮（注意：设备需处于充电/插电状态才生效）
scrcpy --stay-awake
```

### 11.4 远程演示

```bash
# 无线连接进行演示（会议室场景），演示中设备不会休眠
scrcpy --tcpip=192.168.1.100 --window-title="产品演示" --stay-awake
```

想在画面上展示触点的话，可以加 `--show-touches`（退出时自动恢复原设置）。注意官方文档的说明：它只显示手指在物理屏幕上的真实触点，scrcpy 从电脑注入的点击不会显示——适合演示者直接操作手机的场合。

---

## 12. 总结

在 Android 投屏控制这个需求上，scrcpy 同时做到了低延迟、功能全和零侵入——不用 root、不留痕、跨三平台，这也是它能积累近 15 万 Stars 的原因。

| 优势 | 说明 |
|------|------|
| **无需 ROOT** | 直接使用，不需要解锁 Bootloader |
| **跨平台** | Linux/Windows/macOS 全支持 |
| **高性能** | 30~120fps，官方口径延迟 35~70ms |
| **功能丰富** | 录制、音频转发、HID 键鼠、游戏手柄、OTG、摄像头、虚拟显示器 |
| **轻量快速** | 约 1 秒显示首帧 |
| **开源免费** | Apache-2.0，代码完全透明 |

**适用场景**：

- Android 应用开发调试（比看手机屏幕高效）
- 游戏录制与演示（低延迟 + 高帧率）
- 自动化测试（配合 ADB 脚本）
- 远程演示和教学（会议室大屏展示）
- 日常使用（在大屏幕上回消息比看手机舒服）

**官方资源**：

- GitHub：https://github.com/Genymobile/scrcpy
- 官方文档：https://github.com/Genymobile/scrcpy#readme （`doc/` 目录下按主题分篇）
- FAQ：https://github.com/Genymobile/scrcpy/blob/master/FAQ.md
- 作者博客：https://blog.rom1v.com/
- Reddit 社区：[r/scrcpy](https://www.reddit.com/r/scrcpy)
- BlueSky：[@scrcpy.bsky.social](https://bsky.app/profile/scrcpy.bsky.social)

> 下载提醒（官方 README 原话的意译）：这个 GitHub 仓库是 scrcpy 唯一的官方来源，不要从名字里带 "scrcpy" 的随机网站下载发行包。

---

## 自测检查

完成阅读后，请确认你能回答以下问题：

- [ ] scrcpy 为什么不需要 ROOT 权限？
- [ ] ADB 在 scrcpy 工作流程中扮演什么角色？
- [ ] 如何判断应该降低分辨率还是降低码率？
- [ ] OTG 模式和普通模式的核心区别是什么？
- [ ] 无线调试（Android 11+）和传统 TCP/IP 转发的区别？
- [ ] sdk 键盘模式和 UHID 键盘模式各有什么取舍？
- [ ] H.265 和 H.264 应该如何选择？
- [ ] 为什么某些设备会报 INJECT_EVENTS 权限错误？
- [ ] 如何排查 `adb devices` 看不到设备的问题？

---

## 进阶路径

**如果你完成了本文的学习，可以继续探索：**

1. **源码研究**：阅读客户端（`app/` 目录，C + SDL3）和设备端（`server/` 目录，Java）的源码，理解 MediaCodec 编码与 SDL 渲染的实现
2. **二次开发**：基于 scrcpy 的协议开发自定义功能（例如批量设备管理），官方另有 [ws-scrcpy](https://github.com/NetrisTV/ws-scrcpy) 等浏览器端衍生项目
3. **性能调优**：研究 Android 的 `SurfaceFlinger` 和 `MediaCodec` 底层机制
4. **替代方案对比**：了解 Vysor、AirDroid、TeamViewer 等方案的优缺点
5. **自动化集成**：将 scrcpy 集成到 CI/CD 流水线中，实现自动化 UI 测试（可搭配作者开发的 [AutoAdb](https://github.com/rom1v/autoadb) 在设备插入时自动启动）

**推荐阅读**：

- [scrcpy 官方文档](https://github.com/Genymobile/scrcpy#readme)
- [Android MediaCodec 官方文档](https://developer.android.com/reference/android/media/MediaCodec)
- [ADB 协议文档](https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/main/docs/dev/protocol.md)

---

## 练习

### 练习 1：基础连接（预计 10 分钟）

在你的 Android 设备上启用 USB 调试，然后通过 USB 连接电脑并启动 scrcpy。尝试用鼠标键盘操作设备。

**验收标准**：scrcpy 窗口正常显示设备屏幕，鼠标点击和键盘输入都能正确响应。

### 练习 2：无线连接配置（预计 15 分钟）

分别用 `scrcpy --tcpip` 和 Android 11+ 的"无线调试"配对两种方式建立无线连接。

**验收标准**：拔掉 USB 线后，scrcpy 仍能正常镜像设备屏幕。

### 练习 3：性能调优实验（预计 10 分钟）

分别用以下参数启动 scrcpy，观察延迟和画质的差异：

```bash
scrcpy -m 480 --max-fps 120        # 方案 A
scrcpy -m 1080 --max-fps 60        # 方案 B
scrcpy -m 720 --video-codec=h265   # 方案 C（需设备支持 H.265）
```

**验收标准**：能说清楚三种方案分别适合什么场景。

### 练习 4：屏幕录制（预计 5 分钟）

录制一段 30 秒的设备屏幕操作，然后用视频播放器查看录制结果。

```bash
scrcpy --record=test.mp4 --time-limit=30
# 或者不加参数，操作 30 秒后在终端按 Ctrl+C 停止
```

**验收标准**：`test.mp4` 文件正常生成且可以播放。
