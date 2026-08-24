+++
github_repo = "Genymobile/scrcpy"
date = '2026-05-14T20:17:49+08:00'
draft = false
title = 'scrcpy：开源 Android 屏幕投射与设备控制'
slug = 'scrcpy-android-screen-mirroring-guide'
description = 'scrcpy 是 Genymobile 开源的 Android 设备投射工具，通过 USB 或 TCP/IP 将手机屏幕镜像至电脑，支持键盘鼠标控制设备，无需 root，手机端也不装任何 App。'
categories = ['技术笔记']
tags = ['Android', '开源', '工具']
+++

# scrcpy：开源 Android 屏幕投射与设备控制

## 学习目标

读完本文，可以掌握以下能力：

- 说清 scrcpy 客户端 / scrcpy-server 两端架构的职责分工与通信方式
- 区分普通 USB 调试模式、HID 输入模拟、OTG 模式、V4L2 模式的适用场景
- 用命令行参数调整分辨率、帧率、编码格式以平衡画质与延迟
- 在 Linux / Windows / macOS 上完成安装并解决常见连接问题
- 判断 scrcpy 相比 Vysor、Samsung Flow 等工具的取舍依据

---

## 目录

- [什么是 scrcpy？](#什么是-scrcpy)
- [核心能力](#核心能力)
- [系统要求](#系统要求)
- [快速上手](#快速上手)
  - [安装方式](#安装方式)
  - [基础用法与常用配置](#基础用法与常用配置)
  - [进阶用法](#进阶用法)
- [技术架构简析](#技术架构简析)
  - [一次 USB 投射的完整链路](#一次-usb-投射的完整链路)
- [与同类工具的差异](#与同类工具的差异)
- [采用顺序与适用边界](#采用顺序与适用边界)
- [自测题](#自测题)
- [练习](#练习)
- [进阶路径](#进阶路径)
- [常见问题 FAQ](#常见问题-faq)

---

## 什么是 scrcpy？

[scrcpy](https://github.com/Genymobile/scrcpy)（读作 "screen copy"）是 [Genymobile](https://github.com/Genymobile) 团队开源的 Android 设备投射与控制工具。通过 USB 或 TCP/IP 无线连接，把设备屏幕与音频实时镜像到电脑，并用电脑的键盘鼠标直接操控设备。整个过程不要求 root，手机端不用装任何 App，只依赖 Android 自带的 ADB 调试通道；连接断开后，设备上不留任何文件或进程。

## 核心能力

scrcpy 的定位是「只做屏幕投射和控制，尽量轻、尽量快」：

| 方面 | 表现 |
|------|------|
| 性能 | 帧率 30～120fps，取决于设备编解码能力 |
| 画质 | 默认 1920×1080 或更高 |
| 延迟 | 官方口径 35～70ms |
| 启动 | 约 1 秒显示第一帧 |
| 无侵入 | 手机端不安装、不留痕迹，无需账号、广告和联网 |

覆盖的功能大致分几类：

- 基础：音频转发（Android 11+，API 30）、屏幕录制为 MP4、双向剪贴板
- 显示：虚拟显示（独立于物理屏，可投特定 App）、熄屏投射
- 输入：键盘鼠标控制、物理键盘 / 鼠标模拟（HID/uhid）、游戏手柄（`--gamepad=uhid`）
- 摄像头（Android 12+）与 V4L2（仅 Linux）：把摄像头或整个屏幕暴露成电脑的 webcam
- 画质：分辨率、帧率、码率、编码格式均可配置，支持 H.264 / H.265 / AV1

## 系统要求

- **Android 设备**：至少 API 21（Android 5.0）
- **音频转发**：需要 API 30（Android 11+）
- **电脑端**：Linux、Windows、macOS 均支持

> **注意**：部分机型（尤其小米 / 红米）用键盘鼠标控制时会报 `INJECT_EVENTS permission` 错误。此时需要额外打开「USB 调试（安全设置）」这一项（注意它和「USB 调试」是两个不同的开关），并重启设备。

## 快速上手

### 安装方式

**Linux（Ubuntu 示例）**
```bash
sudo apt install scrcpy
```

**Windows**：下载官方 Release 包解压，直接双击 `scrcpy.exe`。

**macOS**
```bash
brew install scrcpy
```

发行版仓库里的版本可能略旧；需要最新版时，按[官方构建文档](https://github.com/Genymobile/scrcpy/blob/master/doc/build.md)从源码编译，或从 [GitHub Releases](https://github.com/Genymobile/scrcpy/releases) 获取。

### 基础用法与常用配置

连上设备并开启 USB 调试后（`adb devices` 能列出设备即可），命令行直接运行：

```bash
scrcpy
```

几个常用参数组合：

**降低分辨率提升流畅度（优先做法）**
```bash
scrcpy -m 1024
```

**H.265 编码 + 限流 + 物理键盘模拟 + 关闭音频**
```bash
scrcpy --video-codec=h265 -m1920 --max-fps=60 --no-audio -K
```

录制设备摄像头（含麦克风）为 MP4
```bash
scrcpy --video-source=camera --video-codec=h265 --camera-size=1920x1080 --record=file.mp4
```

无线连接（先让设备监听，再通过电脑连接）
```bash
adb tcpip 5555          # 在已连接 USB 的设备上执行
adb connect 设备IP:5555  # 电脑端连接
scrcpy                  # 断开 USB 后同样可行
```

### 进阶用法

**虚拟显示里单独跑一个 App**（不影响物理屏幕）
```bash
scrcpy --new-display=1920x1080 --start-app=org.videolan.vlc
```

**把手机摄像头暴露成电脑 webcam（仅 Linux）**
```bash
scrcpy --video-source=camera --camera-size=1920x1080 --camera-facing=front \
  --v4l2-sink=/dev/video2 --no-playback
```

**OTG 模式**（不镜像、只模拟物理键盘鼠标，不要求 USB 调试）
```bash
scrcpy --otg
```

## 技术架构简析

scrcpy 由两部分组成，各自分工：

1. **scrcpy 客户端**：跑在电脑端，用 C 语言编写，基于 SDL2 渲染，对接 FFmpeg 做音视频解码。它是交互的主入口，所有命令行参数都由它解析。
2. **scrcpy-server**：跑在 Android 设备端的一段 Java 小程序，启动时由客户端通过 ADB 推送到设备并拉起。它负责用系统硬件编码器 `MediaCodec` 采集屏幕 / 摄像头画面并编码，把音频和画面通过 ADB 建立起的本地 socket 隧道回传。会话结束即被移除。

两端之间的视频数据是一个自定义二进制协议传输的原始编码码流，控制指令（按键、触摸、剪贴板）走同一条通道反向上行。整条链路里没有云端、没有中转服务器，ADB 连接断开即全部终止。

延迟主要来自编码、传输、解码三段：编码端用设备硬件编码器（MediaCodec）压到几毫秒，传输走 ADB 本地通道开销很小，解码端交给 FFmpeg（在支持硬件解码的平台上优先硬解）。这也是为什么它能维持 35～70ms 的整体延迟。

### 一次 USB 投射的完整链路

把上面的机制串起来看一次实机连接：电脑端 `scrcpy` 启动后，先用 `adb` 把 `scrcpy-server` 推到设备并拉起；服务端用 `MediaCodec` 抓屏并编码成 H.264/H.265 码流，经本地 socket 回传；客户端收到后交给 FFmpeg 解码、SDL2 渲染出画面。你敲的键、点的鼠标逆向上行，经同一通道投到设备。整个过程对手机是"临时接管"，断开即清理干净。

## 与同类工具的差异

- **完全开源**：代码透明，可审计，适合对安全敏感的环境
- **低依赖**：不需要 Google 服务、不需要账号，无广告无联网
- **原生实现**：C + Java，路径上比 Electron / WebView 方案少一层运行时开销，延迟更低
- **覆盖广**：从基础投射到 HID 模拟、摄像头、V4L2，一条链路上满足多数投射控制需求
- **长期维护**：项目持续维护、迭代稳定，新 Android 版本跟进及时

## 采用顺序与适用边界

### 采用顺序建议

1. **先用 USB 跑通默认投射**：`adb devices` 确认设备在线，跑一次默认 `scrcpy`，验证兼容性和基础体验
2. **再调画质参数**：根据设备能力用 `-m`、`--max-fps`、`--video-codec` 找到画质与延迟的平衡点
3. **需要移动设备时切无线**：USB 稳定后再用 `adb tcpip` + `adb connect` 转 TCP/IP
4. **有特定需求再上高级模式**：OTG（免调试控制）、V4L2（webcam）、虚拟显示（单独跑 App）

### 适用边界

- **适合**：开发调试、自动化测试、屏幕录制、演示投影、需要用键盘鼠标操控 Android 的场景
- **不适合**：需要 root 才能做的系统级操作；对延迟极度敏感的电竞级实时操作（35～70ms 仍有体感）；需要设备长期本机运行的前台监控——scrcpy 是依附于电脑连接的前台工具，不是常驻服务

> **官方仓库**：https://github.com/Genymobile/scrcpy

---

## 自测题

1. scrcpy 的客户端和服务端分别用什么语言实现，各自运行在哪里？
2. 官方 35～70ms 延迟主要来自哪三段，scrcpy 怎么把这三段压下去？
3. `scrcpy --otg` 和普通 USB 调试模式在输入控制和「是否要求 USB 调试」上有什么不同？
4. 音频转发对 Android 系统版本有什么硬性要求？
5. 哪些场景其实不适合用 scrcpy？

<details>
<summary>参考答案</summary>

1. 客户端用 C 写、跑在电脑上，基于 SDL2 渲染、FFmpeg 处理音视频；服务端是一段 Java 小程序，跑在 Android 设备端，负责用 MediaCodec 采集和编码屏幕与音频。
2. 编码、传输、解码三段。scrcpy 用设备硬件编码器 MediaCodec 和电脑端 FFmpeg（优先硬解）把每段延迟压到毫秒级。
3. `scrcpy --otg` 只模拟物理键盘鼠标、不做画面镜像，且**不要求**开启 USB 调试；普通模式需要 USB 调试，才能把 server 推到设备并注入输入事件。
4. 需要 Android 11 及以上（API 30+）。
5. 依赖 root 的系统级修改、对延迟极度敏感的实时竞技操控，以及需要设备脱离电脑独立常驻运行的场景。

</details>

---

## 练习

1. 用 USB 连上手机，先跑一次默认 `scrcpy`，再用 `scrcpy -m 1024` 降分辨率，对比两者的清晰度和操作跟手程度。
2. 用 `scrcpy --video-codec=h265 -m1920 --max-fps=60 --no-audio -K` 录一段 60 秒操作视频，回看码率和流畅度。
3. 开一个虚拟显示并把某个 App 投进去：`scrcpy --new-display=1920x1080 --start-app=包名`，体验不影响物理屏的独立投射。
4. 在 Linux 上把手机摄像头当 webcam：`scrcpy --video-source=camera --camera-size=1920x1080 --camera-facing=front --v4l2-sink=/dev/video2 --no-playback`，再在会议软件里选中这个摄像头。
5. 体验 OTG 模式：关掉 USB 调试后执行 `scrcpy --otg`，确认在无 ADB 权限下仍能用键盘鼠标控制设备（注意此时不显示画面）。

---

## 进阶路径

- **读 scrcpy-server 源码**：体量不大，读一遍能弄清 MediaCodec 抓屏、socket 通信、会话生命周期。
- **研究 HID / OTG**：对照 `uhid` 实现，理解电脑如何被模拟成物理输入设备，以及它和普通 ADB 输入注入的本质区别。
- **封装启动命令**：把常用参数写成脚本或 shell 别名，按「开发调试 / 演示 / 录制」等场景一键切换。
- **跟踪 issue tracker**：特定机型、特定 Android 版本的兼容问题都沉淀在 issue 里，信息往往比文档更细。

---

## 常见问题 FAQ

**连上后黑屏，或提示找不到设备？**
先 `adb devices` 确认设备在线。没出现就重开「USB 调试」，换一根数据线（很多线只充电不通数据），再试 `adb kill-server && adb start-server`。

**小米、红米等机型能投射但键盘鼠标控不了？**
这类机型需要在「开发者选项」里额外打开「USB 调试（安全设置）」，并重启一次设备，否则输入事件会被系统拦截，报 `INJECT_EVENTS permission` 错误。

**无线连接动不动就断？**
无线依赖 `adb tcpip` 通道，走普通 Wi-Fi，干扰和耗电都会影响稳定性。对稳定性要求高时优先用 USB；无线适合演示或临时场景。

**延迟太高、画面卡顿？**
优先降分辨率（`-m`）和帧率（`--max-fps`），换 H.265 通常更省带宽，再确认用的是原装数据线、电脑解码走了硬件而非软解。

**有画面没声音？**
音频转发只在 Android 11（API 30）以上可用。更低版本 scrcpy 本身不传声音，需要另接采集方案。

**macOS 上 `brew install scrcpy` 后命令找不到？**
一般是 PATH 没包含 Homebrew 的 sbin。把 `eval "$(/opt/homebrew/bin/brew shellenv)"` 加进 shell 配置后重开终端即可。

**分不清 `--otg` 和 `--keyboard=uhid`？**
`--keyboard=uhid` 是在普通 USB 调试模式下，把电脑模拟成物理键盘来输入；`--otg` 则完全不镜像、也不要求 USB 调试，只单纯提供物理键盘鼠标控制。