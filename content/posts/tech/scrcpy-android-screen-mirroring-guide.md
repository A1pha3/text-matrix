+++
github_repo = "Genymobile/scrcpy"
source_key = "gh:Genymobile/scrcpy"
date = '2026-05-14T20:17:49+08:00'
lastmod = '2026-09-19T13:40:00+08:00'
draft = false
title = 'scrcpy：开源 Android 屏幕投射与设备控制'
slug = 'scrcpy-android-screen-mirroring-guide'
description = 'scrcpy 是 Genymobile 开源的 Android 设备投射工具，通过 USB 或 TCP/IP 将手机屏幕镜像至电脑，支持键盘鼠标控制设备，无需 root，手机端也不装任何 App。'
categories = ['技术笔记']
tags = ['Android', '开源', '工具']
+++

# scrcpy：开源 Android 屏幕投射与设备控制

## 读完你会做什么

这篇文档按「先跑通、再调优、后排错」的顺序组织。读完之后，你应该能：

- 讲清 scrcpy 客户端与 scrcpy-server 各自做什么、数据走哪条路
- 分清 USB 调试、HID 输入模拟、OTG 模式、V4L2 模式各自适用的场景
- 用命令行参数调整分辨率、帧率、码率，在画质与延迟之间做取舍
- 在 Linux / Windows / macOS 上完成安装，并处理常见连接问题
- 判断什么场景值得选 scrcpy，什么场景它并不合适

---

## 目录

- [什么是 scrcpy？](#什么是-scrcpy)
- [核心能力](#核心能力)
- [系统要求](#系统要求)
- [快速上手](#快速上手)
  - [安装方式](#安装方式)
  - [基础用法与常用配置](#基础用法与常用配置)
  - [示例：一次会议室演示的完整准备](#示例一次会议室演示的完整准备)
  - [进阶用法](#进阶用法)
- [技术架构简析](#技术架构简析)
  - [一次 USB 投射的完整链路](#一次-usb-投射的完整链路)
- [与同类工具的差异](#与同类工具的差异)
- [采用顺序与适用边界](#采用顺序与适用边界)
  - [采用顺序建议](#采用顺序建议)
  - [适用边界](#适用边界)
- [自测题](#自测题)
- [练习](#练习)
- [下一步读什么](#下一步读什么)
- [常见问题 FAQ](#常见问题-faq)

---

## 什么是 scrcpy？

[scrcpy](https://github.com/Genymobile/scrcpy)（读作 "screen copy"）是 [Genymobile](https://github.com/Genymobile)（Genymotion 模拟器背后的公司）开源的 Android 设备投射与控制工具，由 Romain Vimont（[rom1v](https://github.com/rom1v)）编写并维护，2018 年 3 月发布 v1.0，采用 Apache-2.0 许可证。截至本文更新，最新版本是 v4.1（2026-07-12 发布）。

它通过 USB 或 TCP/IP 无线连接，把设备屏幕与音频实时镜像到电脑，并用电脑的键盘鼠标直接操控设备。整个过程不要求 root，手机端不装任何 App，只依赖 Android 自带的 ADB 调试通道；连接断开后，设备上不留任何文件或进程。

## 核心能力

scrcpy 的定位是「只做屏幕投射和控制，尽量轻、尽量快」：

| 方面 | 表现 |
|------|------|
| 性能 | 帧率 30～120fps，取决于设备编解码能力 |
| 画质 | 官方口径 1920×1080 及以上；默认不限制分辨率，`-m` 才设上限 |
| 延迟 | 官方口径 35～70ms |
| 启动 | 约 1 秒显示第一帧 |
| 无侵入 | 手机端不安装、不留痕迹，无需账号、广告和联网 |

主要功能分几类：

- 基础：音频转发（Android 11+）、屏幕录制为 MP4 / MKV、双向剪贴板
- 显示：虚拟显示（独立于物理屏，可单独投一个 App，v4.0 起还支持随窗口大小连续调整的 flex display）、熄屏投射
- 输入：键盘鼠标控制、物理键盘 / 鼠标 / 手柄模拟（UHID 或 AOA 协议）、免 USB 调试的 OTG 模式
- 摄像头（Android 12+）与 V4L2（仅 Linux）：把摄像头或整个屏幕暴露成电脑的 webcam
- 编码：视频支持 H.264（默认）、H.265、AV1，v4.1 起新增 VP8 / VP9 兜底；音频默认 Opus，可换 AAC、FLAC、RAW
- 画质参数：分辨率、帧率、码率（默认 8 Mbps）均可配置

## 系统要求

- **Android 设备**：至少 API（应用程序接口）21，也就是 Android 5.0
- **音频转发**：需要 API 30（Android 11+）。Android 12 起开箱可用；Android 11 要求在**启动 scrcpy 时**屏幕处于解锁状态，系统会短暂弹出一个假通知让 shell 进程看起来在前台，否则音频采集直接失败；Android 10 及以下取不到音频，会自动关闭
- **摄像头镜像**：Android 12+
- **电脑端**：Linux、Windows、macOS 均支持，另外需要 adb

> **注意**：部分机型（尤其小米 / 红米）用键盘鼠标控制时会报 `INJECT_EVENTS permission` 错误。此时需要额外打开「USB 调试（安全设置）」这一项（注意它和「USB 调试」是两个不同的开关），并重启设备。

## 快速上手

### 安装方式

**Linux**：优先用[官方 Release](https://github.com/Genymobile/scrcpy/releases) 的静态构建包，解压即可运行，版本最新。各发行版仓库里的包版本参差：

```bash
# Arch Linux
sudo pacman -S scrcpy
# Fedora
dnf copr enable zeno/scrcpy && dnf install scrcpy
```

Debian / Ubuntu 的 `apt install scrcpy` 和 Snap 包被官方文档标记为过时版本（obsolete），装到的可能是旧版，不建议依赖。需要最新版时，要么下载 Release 包，要么按[官方构建文档](https://github.com/Genymobile/scrcpy/blob/master/doc/build.md)从源码编译。

**Windows**：从 [GitHub Releases](https://github.com/Genymobile/scrcpy/releases) 下载官方压缩包解压，直接双击 `scrcpy.exe`。注意只从官方仓库下载。

**macOS**
```bash
brew install scrcpy
```

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

**限制码率**（默认 8 Mbps，直播或弱网环境可压低）
```bash
scrcpy -b 2M
```

录制设备摄像头（含麦克风）为 MP4
```bash
scrcpy --video-source=camera --video-codec=h265 --camera-size=1920x1080 --record=file.mp4
```

无线连接有两种做法。省事的方式是 `--tcpip`，它自动找到设备 IP 与 adb 端口、必要时打开 TCP/IP 模式再连接：

```bash
scrcpy --tcpip              # 设备先插一次 USB，之后拔掉也能连
scrcpy --tcpip=192.168.1.1  # 设备已在监听时直接指定 IP（默认端口 5555）
scrcpy --tcpip=+192.168.1.1 # IP 前加 + 表示强制重新连接
```

手动方式步骤更多，但适合写进脚本：

```bash
adb tcpip 5555              # 在已连接 USB 的设备上执行
adb connect 设备IP:5555      # 电脑端连接，IP 可在 设置 → 关于手机 → 状态 里查到
scrcpy                      # 断开 USB 后同样可行
adb disconnect              # 用完断开
```

设备不止一台时，scrcpy 不会替你猜，必须显式指定：`--serial=`（缩写 `-s`，无线设备的 serial 就是 `ip:port`）、`-d` 选中唯一那台 USB 设备、`-e` 选中唯一那台 TCP/IP 设备，也可以用 `adb` 认识的环境变量 `ANDROID_SERIAL`。

Android 11 起系统自带「无线调试」，配对后可以完全不插 USB 线。

### 示例：一次会议室演示的完整准备

场景是把手机投到会议室的大屏上讲半小时，要求手机屏幕别一直亮着、中途不因为省电策略掉线。每一步都配了验证点：

1. **前置检查**：手机打开 USB 调试，电脑上 `scrcpy --version` 能打印版本号，`adb devices` 能列出设备。这一步的目标只是确认工具链在位，不要跳过它去调参数。
2. **确认设备授权**：`adb devices` 第二列必须是 `device`。显示 `unauthorized` 就是手机上那个「允许 USB 调试」还没点。
3. **有线跑通并熄屏**：执行 `scrcpy -Sw`（`-S` 关闭设备屏幕，`-w` 让设备保持不休眠）。验证点是窗口标题——它显示的是设备名，由 server 在第一条连接上发回。多台设备时，这是确认自己连对机器的最快办法。
4. **切到无线**：USB 还插着时执行 `scrcpy --tcpip`，成功后拔线重跑一次第 3 步的命令。这里有个容易踩空的地方：`--stay-awake` 只在设备充电时有效，拔线之后它就不起作用了，得自己保证手机不会睡着。
5. **收尾**：`adb disconnect`。关掉 scrcpy 窗口后，它改过的设备设置会被恢复。

### 进阶用法

**虚拟显示里单独跑一个 App**（不影响物理屏幕）
```bash
scrcpy --new-display=1920x1080 --start-app=org.videolan.vlc
```

`--start-app` 并不依赖 `--new-display`，单独用也会在主屏上把 App 拉起来；它的硬约束是不能和 `-n/--no-control` 同用。包名可以用 `scrcpy --list-apps` 列出来，`--start-app=+?firefox` 里 `+` 表示先 force-stop、`?` 表示按应用名而不是包名查找——按名字找要多等几秒，能用包名就用包名。

追加 `--flex-display`（缩写 `-x`）可让这块虚拟显示跟随窗口大小连续变化，适合「窗口拖多大、App 就多大」的用法。它的限制条件不少：只能作用于 `--new-display` 创建的显示，与 `-n/--no-control`、`--crop` 互斥，`--window-width` / `--window-height` 也会被拒（显示尺寸改由 `--new-display=WxH` 决定）。

**把手机摄像头暴露成电脑 webcam（仅 Linux）**
```bash
scrcpy --video-source=camera --camera-size=1920x1080 --camera-facing=front \
  --v4l2-sink=/dev/video2 --no-playback
```

**OTG 模式**（不镜像画面、不转发音频，只把电脑键盘鼠标模拟成物理输入设备，走 AOA 协议，不要求 USB 调试）
```bash
scrcpy --otg
```

OTG 模式下手柄默认关闭，需要时显式加 `--gamepad=aoa`（OTG 下 `-G` 等价）。

## 技术架构简析

scrcpy 由两部分组成，各自分工：

1. **scrcpy 客户端**：跑在电脑端，用 C 语言编写，基于 SDL 渲染（v4.0 起从 SDL2 迁移到 SDL3），音视频解码交给 FFmpeg，录制时也是在客户端封装成 MP4 / MKV。所有命令行参数由它解析。
2. **scrcpy-server**：跑在 Android 设备端的一段 Java 程序，构建产物是一个未签名的 APK（即 `scrcpy-server.jar`）。启动时客户端通过 adb 把它推到 `/data/local/tmp`，再以 shell 身份用 `app_process` 拉起。选这个目录有讲究：它对 shell 可读写、但不是 world-writable，恶意应用没法在执行前把 server 换掉。会话结束由设备端一个独立的清理线程删文件、并把改过的系统设置还原——这个线程独立于主进程，所以设备被直接拔线、主进程被杀掉时同样会执行。

两端之间的连接默认走 `adb reverse` 建立的本地 socket（套接字）隧道（`adb forward` 是备用方案）。视频、音频、控制是**最多三条独立的 socket**，各自由独立线程处理——只有控制通道是双向的：输入事件从电脑发往设备，设备剪贴板变化时反向推给电脑。视频与音频各自单向传输编码码流。客户端与 server 的版本必须完全一致，内部协议在版本之间没有兼容性保证。

一个容易忽略的细节：帧是按需产生的，屏幕内容不变时就不产生新帧。播放 24fps 的视频时，scrcpy 最多也就 24fps——这也让它静止画面下省电省带宽。设备旋转同样由 server 处理，客户端只知道自己收到了多大尺寸的帧。

延迟主要来自编码、传输、解码三段：编码端用设备硬件编码器 `MediaCodec` 压到几毫秒，传输走 adb 本地通道开销很小，解码端交给 FFmpeg（在支持硬件解码的平台上优先硬解）。解码完的帧默认立刻上屏，不为了画面平滑而攒缓冲——真要那样得显式加 `--video-buffer=delay`。这也是为什么它能维持 35～70ms 的整体延迟。

### 一次 USB 投射的完整链路

把上面的机制串起来看一次实机连接：电脑端 `scrcpy` 启动后，先用 `adb` 把 `scrcpy-server` 推到设备并拉起，随后建立视频、音频、控制三条 socket；服务端用 `MediaCodec` 抓屏并编码成码流，经视频 socket 回传；客户端收到后交给 FFmpeg 解码、SDL 渲染出画面。你敲的键、点的鼠标走控制通道逆向上行，投到设备。整个过程对手机是「临时接管」，断开即清理干净。

## 与同类工具的差异

- **完全开源**：Apache-2.0 许可证，代码透明可审计，适合对安全敏感的环境
- **低依赖**：不需要 Google 服务、不需要账号，无广告无联网
- **原生实现**：C + Java，不像 Electron / WebView 类方案那样在链路里多带一层运行时
- **覆盖面宽**：从基础投射到 HID 输入模拟、摄像头镜像、V4L2、虚拟显示，一条链路覆盖多数投射控制需求
- **维护活跃**：2018 年开源至今持续迭代，由 rom1v 主导维护，新 Android 版本跟进及时

## 采用顺序与适用边界

### 采用顺序建议

1. **先用 USB 跑通默认投射**：`adb devices` 确认设备在线，跑一次默认 `scrcpy`，验证兼容性和基础体验
2. **再调画质参数**：根据设备能力用 `-m`、`--max-fps`、`--video-codec` 找到画质与延迟的平衡点
3. **需要移动设备时切无线**：USB 稳定后用 `scrcpy --tcpip` 转 TCP/IP
4. **有特定需求再上高级模式**：OTG（免调试控制）、V4L2（webcam）、虚拟显示（单独跑 App）

### 适用边界

- **适合**：开发调试、自动化测试、屏幕录制、演示投影、需要用键盘鼠标操控 Android 的场景
- **不适合**：需要 root 才能做的系统级操作；对延迟极度敏感的电竞级实时操作（35～70ms 仍有体感）；需要设备长期本机运行的前台监控——scrcpy 是依附于电脑连接的前台工具，不是常驻服务

> **官方仓库**：https://github.com/Genymobile/scrcpy
>
> **核对口径**：本文的参数与行为按 v4.1（2026-07-12）加上 2026-09-03 的 master 文档与源码核对。版本敏感度最高的两处是 `-x/--flex-display` 的互斥清单和音频转发的系统门槛，后续 scrcpy 改版时优先复核这两段。

---

## 自测题

1. scrcpy 的客户端和服务端分别用什么语言实现，各自运行在哪里？
2. scrcpy 的视频、音频、控制数据是走一条通道还是多条？哪些方向是双向的？
3. `scrcpy --otg` 和普通 USB 调试模式在输入控制和「是否要求 USB 调试」上有什么不同？
4. 音频转发对 Android 系统版本有什么硬性要求？Android 11 上还有哪个附加条件？
5. 哪些场景其实不适合用 scrcpy？

<details>
<summary>参考答案</summary>

1. 客户端用 C 写、跑在电脑上，基于 SDL 渲染（v4.0 起 SDL3）、FFmpeg 处理音视频；服务端是一段 Java 程序，以 shell 身份跑在 Android 设备端，负责用 MediaCodec 采集和编码屏幕与音频。
2. 最多三条独立 socket：视频、音频、控制。只有控制通道双向（输入下行、剪贴板上行），视频音频各自单向回传。客户端与 server 版本必须完全一致。
3. `scrcpy --otg` 只模拟物理键盘鼠标（走 AOA 协议）、不做画面镜像，且**不要求**开启 USB 调试；普通模式需要 USB 调试，才能把 server 推到设备并注入输入事件。
4. 需要 Android 11 及以上（API 30+）；Android 11 上启动 scrcpy 时设备屏幕须处于解锁状态，Android 12 起才不用管这件事。
5. 依赖 root 的系统级修改、对延迟极度敏感的实时竞技操控，以及需要设备脱离电脑独立常驻运行的场景。

</details>

---

## 练习

1. 用 USB 连上手机，先跑一次默认 `scrcpy`，再用 `scrcpy -m 1024` 降分辨率，对比两者的清晰度和操作跟手程度。
2. 用 `scrcpy --video-codec=h265 -m1920 --max-fps=60 --no-audio -K` 录一段 60 秒操作视频（加 `--record=file.mp4`），回看码率和流畅度。
3. 开一个虚拟显示并把某个 App 投进去：`scrcpy --new-display=1920x1080 --start-app=包名`，再试试加 `--flex-display` 让显示区跟随窗口变化。
4. 在 Linux 上把手机摄像头当 webcam：`scrcpy --video-source=camera --camera-size=1920x1080 --camera-facing=front --v4l2-sink=/dev/video2 --no-playback`，再在会议软件里选中这个摄像头。
5. 体验 OTG 模式：关掉 USB 调试后执行 `scrcpy --otg`，确认在无 ADB 权限下仍能用键盘鼠标控制设备（注意此时不显示画面）。

---

## 下一步读什么

- **读 scrcpy-server 源码**：体量不大，读一遍能弄清 MediaCodec 抓屏、socket 通信、会话生命周期。
- **对照官方 develop 文档**：`doc/develop.md` 写清了推送路径、socket 划分和二进制协议格式，是理解架构的最短路径。
- **研究 HID / OTG**：对照 `uhid` 与 AOA 两种实现，理解电脑如何被模拟成物理输入设备，以及它和普通 ADB 输入注入的本质区别。
- **封装启动命令**：把常用参数写成脚本或 shell 别名，按「开发调试 / 演示 / 录制」等场景一键切换。
- **跟踪 issue tracker**：特定机型、特定 Android 版本的兼容问题都沉淀在 issue 里，信息往往比文档更细。

---

## 常见问题 FAQ

**连上后黑屏，或提示找不到设备？**
先 `adb devices` 确认设备在线。没出现就重开「USB 调试」，换一根数据线（很多线只充电不通数据），再试 `adb kill-server && adb start-server`。

**小米、红米等机型能投射但键盘鼠标控不了？**
这类机型需要在「开发者选项」里额外打开「USB 调试（安全设置）」，并重启一次设备，否则输入事件会被系统拦截，报 `INJECT_EVENTS permission` 错误。

**无线连接动不动就断？**
无线依赖 adb 的 TCP/IP 通道，走普通 Wi-Fi，干扰和耗电都会影响稳定性。对稳定性要求高时优先用 USB；无线适合演示或临时场景。

**延迟太高、画面卡顿？**
优先降分辨率（`-m`）和帧率（`--max-fps`）。编码格式上，同码率下 H.265 画质更好，而官方口径是 H.264 延迟更低——追求极限跟手度时可以回落 H.264。同时确认用的是原装数据线、电脑端解码走了硬件而非软解。

**有画面没声音？**
音频转发只在 Android 11（API 30）以上可用，且 Android 11 上要求启动时设备屏幕处于解锁状态。更低版本 scrcpy 本身不传声音，需要另接采集方案。另外，音频采集失败时 scrcpy 默认只丢掉音频、继续投画面，所以「没声音但不报错」是正常行为；想让这种时候直接失败，加 `--require-audio`。

**macOS 上 `brew install scrcpy` 后仍然连不上设备？**
scrcpy 依赖 PATH 里能找到的 `adb`，而 Homebrew 装 scrcpy 并不会带上它。补一句 `brew install --cask android-platform-tools` 即可；改用 MacPorts 的 `sudo port install scrcpy` 则会顺手把 adb 一起配好。

**分不清 `--otg` 和 `--keyboard=uhid`？**
`--keyboard=uhid`（缩写 `-K`）是在普通 USB 调试模式下，把电脑模拟成物理键盘来输入；`--otg` 则完全不镜像、也不要求 USB 调试，走 AOA 协议，只单纯提供物理键盘鼠标控制。
