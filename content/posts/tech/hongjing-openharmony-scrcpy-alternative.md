---
title: "鸿镜 HongJing：面向 OpenHarmony 设备的投屏调试工具"
date: "2026-05-17T12:01:30+08:00"
slug: "hongjing-openharmony-scrcpy-alternative"
description: "鸿镜是一个面向 OpenHarmony 5.0+ 设备的投屏调试工具，Flutter 桌面客户端通过 hdc fport 端口转发与设备通信，实时镜像屏幕并提供触控注入、应用管理、终端模拟等功能，是 OpenHarmony 设备开发调试的实用辅助。"
draft: false
categories: ["技术笔记"]
tags: ["OpenHarmony", "Flutter", "投屏", "调试工具", "Scrcpy", "H.264"]
---

## 学习目标

读完本文，你应该能：

1. 说明鸿镜（HongJing）在 OpenHarmony 生态中的定位，以及它和 Android 平台 Scrcpy 的对应关系。
2. 描述鸿镜的技术架构：设备端 ScrcpyService 和 PC 端 Flutter 客户端如何通过 `hdc fport` 通信。
3. 列出鸿镜的 7 项核心功能，并判断哪些能力在你的调试场景中是最优先的。
4. 在 macOS / Windows 上完成鸿镜客户端的部署，并把 OpenHarmony 5.0+ 设备成功连接。
5. 解释鸿镜当前已知限制（单点触摸、系统签名、Linux 客户端进度），评估它是否适合你的项目。

---

## 目录

1. [项目概览](#项目概览)
2. [功能特性](#功能特性)
3. [技术架构](#技术架构)
4. [支持平台](#支持平台)
5. [快速上手](#快速上手)
6. [已知限制](#已知限制)
7. [自测题](#自测题)
8. [进阶路径](#进阶路径)
9. [总结](#总结)

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

Flutter 的跨平台能力在这里发挥了作用——桌面端只需写一次，就能覆盖 macOS 和 Windows（Linux 规划中）。H.264 硬件编解码的思路也保证了低延迟：设备端用硬件编码避免 CPU 压力，PC 端同样用平台原生硬件解码来保证流畅播放。`hdc fport` 端口转发是 OpenHarmony 官方工具提供的 ADB-like 能力，项目不需要自己实现 USB/网络传输层。

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

## 常见问题

**Q1：鸿镜需要设备有 root 权限吗？**
不需要。`OHScrcpyServer.hap` 以系统应用身份运行，需要的是系统应用签名和权限白名单，不是 root。普通开发者调试阶段可以联系设备厂商获取签名，或者用有系统权限的调试设备。

**Q2：macOS 上客户端能连上，但画面是黑的？**
先确认设备端 `OHScrcpyServer` 是否在运行（设备上能看到该应用已启动）。如果应用在后台被杀了，TCP 连接会断。另外检查设备是否支持 H.264 硬件编码——不支持时会降级为 JPEG，如果降级也失败就会黑屏。

**Q3：触控注入在部分应用里不生效？**
鸿镜的触控注入走的是 OpenHarmony 系统注入接口，部分应用如果自己处理了触摸事件或者用了自定义视图，可能会消费掉注入的事件。这不是鸿镜的 bug，是系统事件分发的正常行为。

**Q4：hdc fport 端口转发和 adb forward 有什么区别？**
思路一样，都是把设备的端口转到 PC 本地。`hdc` 是 OpenHarmony 的官方调试工具，对应 Android 的 `adb`。鸿镜通过 `hdc fport` 把设备端的 TCP 服务端口转到 PC 端，这样 Flutter 客户端就能通过 `localhost:XXXX` 和设备通信。

**Q5：能同时连多个设备吗？**
当前版本客户端一次连一个设备。如果你有多个 OpenHarmony 设备需要同时调试，可以跑多个客户端实例，每个连不同的设备（需要不同的端口转发）。

---

## 已知限制

- 服务端需要系统应用签名，普通开发者调试阶段可能需要联系设备厂商获取签名权限
- 仅支持单点触摸，复杂手势暂不支持
- Linux 客户端尚未完成

## 自测题

**题 1（功能定位）**：鸿镜和 Android 上的 Scrcpy 核心区别是什么？鸿镜在哪些场景下是更好的选择？

<details>
<summary>参考答案</summary>

核心区别：鸿镜面向 OpenHarmony 5.0+ 设备，使用 `hdc fport` 端口转发和 H.264 硬件编解码；Scrcpy 面向 Android，使用 ADB 和 `screenrecord`/`minicap`。

鸿镜更好的场景：
- 你正在做 OpenHarmony 应用开发或系统调试，需要桌面端实时看屏幕。
- 你希望用 Flutter 的跨平台能力同时覆盖 macOS 和 Windows。
- 你的设备支持 H.264 硬件编码，低延迟是硬需求。

</details>

**题 2（架构判断）**：鸿镜的 PC 端用 Flutter Texture 渲染视频帧，设备端用 `ScreenCapture` + `VideoEncoder`。请解释为什么这套架构能做到低延迟。

<details>
<summary>参考答案</summary>

低延迟来自三点：
1. **硬件编解码**：设备端用 H.264 硬件编码（`VideoEncoder`），避免 CPU 软编码的延迟和开销；PC 端用平台原生硬件解码（macOS VideoToolbox、Windows MediaFoundation）。
2. **TCP 直传**：设备端 `TcpServer` 直接通过 `hdc fport` 转发的 TCP 通道传 H.264 码流，没有额外的协议封装开销。
3. **Flutter Texture 渲染**：解码后的视频帧通过 Flutter 的 Texture 组件直接渲染到窗口，避免了额外的内存拷贝和格式转换。

对比：如果设备不支持 H.264 硬件编码，会降级为 JPEG 模式，延迟会明显上升。

</details>

**题 3（部署排查）**：你安装完 `OHScrcpyServer.hap` 并打开鸿镜客户端，但点击连接后一直卡在"等待设备响应"。请列出至少 3 个可能原因和排查步骤。

<details>
<summary>参考答案</summary>

可能原因：
1. **服务端未获得系统权限**：`OHScrcpyServer.hap` 需要系统应用签名和权限白名单，普通调试证书装上去后服务无法启动。排查：在设备上检查该应用的权限状态，或联系设备厂商获取签名。
2. **hdc 连接异常**：`hdc list targets` 看不到设备。排查：重新插拔 USB、检查 hdc 版本、确认设备已开启开发者模式。
3. **端口转发未建立**：`hdc fport` 转发未成功。排查：手动执行 `hdc fport tcp:XXXX tcp:XXXX` 看是否有报错。
4. **H.264 不支持且 JPEG 降级失败**：设备不支持 H.264 硬件编码，且降级逻辑有问题。排查：看客户端日志是否提到 codec 错误。

</details>

---

## 进阶路径

如果你是 OpenHarmony 应用开发者，想进一步利用鸿镜的思路，可以按这个顺序深入：

1. **会用**：完成本文的快速上手流程，成功在 macOS/Windows 上投屏并操控设备。
2. **看懂**：阅读鸿镜源码，理解 `ScrcpyService` 的 `ScreenCapture` → `VideoEncoder` → `TcpServer` 流水线，以及 Flutter 端如何解包 H.264 并渲染。
3. **能改**：基于鸿镜的代码结构，添加你自己需要的功能——比如多指触控注入、屏幕录制保存、或者设备日志实时同步到 PC 端。
4. **能借鉴**：如果你在做其他 OpenHarmony 工具类应用，参考鸿镜的 `hdc fport` 通信模式和 Flutter 跨平台桌面端架构，可以避免重复造轮子。

如果你对 AI 辅助开发感兴趣，鸿镜本身也是一个案例：作者提到主要编码工作是通过 Claude Code 完成的。你可以对比最终代码和 prompt 设计，思考哪些部分适合 AI 生成、哪些部分需要人工架构设计。

---

## 总结

鸿镜填补了 OpenHarmony 生态中"类 Scrcpy 工具"的空白。对于在 OpenHarmony 设备上做应用开发或系统调试的开发者来说，有一个可以在电脑上直接看屏幕+操作设备的工具会方便很多。项目本身也展示了 AI 辅助工具开发的可行性——主要代码由 Claude Code 生成，开发者做的是架构设计和产品定义。

**链接汇总：**

- GitHub：[guoxiucai/ohos-scrcpy-app](https://github.com/guoxiucai/ohos-scrcpy-app)
- Releases：[ohos-scrcpy-app/releases](https://github.com/guoxiucai/ohos-scrcpy-app/releases)