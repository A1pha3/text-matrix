---
title: "OpenLogi：用 Rust 重写 Logitech Options+ 的本地优先替代"
date: 2026-08-21T03:25:00+08:00
slug: "openlogi-rust-logitech-options-plus-alternative"
github_repo: "AprilNEA/OpenLogi"
source_key: "gh:AprilNEA/OpenLogi"
description: "OpenLogi 是一个用 Rust 编写的 Logitech Options+ 本地替代品，基于 HID++ 与 UVC 协议解锁罗技鼠标、键盘与摄像头的能力。本文梳理其特性边界、安装方式与跨平台现状，帮助读者判断是否值得替换官方驱动。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "Logitech", "HID++", "开源硬件"]
---
# OpenLogi：用 Rust 重写 Logitech Options+ 的本地优先替代

## 核心判断

OpenLogi 是一个以 **Rust + GPUI** 编写的 Logitech Options+ 开源替代品，目标不是「复刻官方界面」，而是把罗技设备的底层能力（按键重映射、DPI、SmartShift、RGB、UVC 摄像头控制）用**本地优先、纯文本配置、无账号无遥测**的方式重新开放出来。

它最值得关注的点有三个：Linux 被当作一等平台（而官方 Options+ 没有 Linux 版）、配置完全落在单个 TOML 文件里、以及一个真正的 CLI 与 GUI 并存。对于「受够 Options+」的用户，它提供了一条与官方完全不同的控制路径。

> 注意：README 明确标注项目仍处于 active development，尚未稳定，特性与配置可能变化。

## 系统地图：GUI 与 Agent 的分工

```
OpenLogi
├── GUI（OpenLogi.exe / OpenLogi.app）
└── 后台 Agent（openlogi-agent）—— 拥有全部设备 I/O
    ├── HID++   → 鼠标 / 键盘 / Logi Bolt / Unifying / 蓝牙
    └── UVC     → 罗技 USB 摄像头（Brio、StreamCam、C920 等）
```

架构上的关键点是 **GUI 与后台 agent 分离**：agent 负责所有设备读写，GUI 负责展示与交互。Windows 便携版要求两者放在同一目录下，否则 GUI 没有可连接的后端——这个细节直接反映了「界面与设备逻辑解耦」的设计。

## 特性边界

### 鼠标（HID++）

- 中键、模式切换键（mode-shift）、滚轮键的捕获与重映射。
- 任意按键上的手势绑定（gesture），支持实时录制（live capture），也可以完全关闭手势。
- **Actions Ring**：光标居中、八槽位的操作叠加层，支持按应用定制布局。
- DPI 预设与 Cycle / Set-preset 动作（协议 `0x2201`）。
- **SmartShift 滚轮**：模式切换、灵敏度与常驻棘轮面板（`0x2111`）。
- 每设备原生滚动方向反转（`0x2121`，限支持设备）。

### 键盘（HID++）

- 全局 F 键重映射，动作目录与鼠标一致，外加高级动作：键入文本、按键组合、多步骤工作流（macOS + Windows）。
- 静态 RGB 灯效（`0x8070` / `0x8080`，限支持设备）。

### 摄像头（UVC）

- 任意罗技 UVC 摄像头即插即用。
- 实时预览遵循「只在观看时占用摄像头」原则：离开即释放设备、LED 熄灭。
- 图像控制直接写入 UVC 硬件：变焦、对焦、曝光、亮度、对比度、饱和度、清晰度、白平衡、色调，含自动模式开关。改动在 Meet / Zoom / OBS 等所有调用摄像头的应用中即时生效。
- 一键配置文件：内置 Default / Streaming / Video call 三种，支持自定义快照，按摄像头持久化并在下次取景时写回硬件。

### 跨应用行为

- **按键重映射经 OS 输入钩子（input hook）实现**，而非改设备内部——重映射动作对系统全局生效。
- **按应用叠加配置**：聚焦切换自动切换配置（macOS + Windows；Linux 仅 X11 / XWayland）。
- **Litra 灯**：电源、亮度、色温控制，可选「跟随摄像头活动」的自动开关。

## 安装方式

### macOS（需 macOS 13+）

- 从 [latest release](https://github.com/AprilNEA/OpenLogi/releases/latest) 下载签名公证的 `.dmg`，拖入 `/Applications`。
- 或 Homebrew：`brew install --cask openlogi`（官方 cask 为默认路径；`brew tap aprilnea/tap` + `aprilnea/tap/openlogi@latest` 可追踪 GitHub 最新版，二选一勿同时装）。

### Linux

- 从 release 下载发行版对应包：`.deb`（Debian/Ubuntu）、`.rpm`（Fedora/RHEL）、`.pkg.tar.zst`（Arch）。
- 所有 Linux 包都会安装 udev 规则，免 sudo 访问 `/dev/hidraw*`、`/dev/uinput` 与鼠标的 `/dev/input/event*` 节点。
- 安装后启用用户级服务：`systemctl --user enable --now openlogi-agent.service`。
- NixOS 用户可直接 import 仓库模块，自动装包 + udev 规则 + 随图形会话启动 agent。

### Windows

- 每 release 附带签名便携 `.zip` 与 per-user `.msi`（x86_64 与 arm64）。
- GUI 与 `openlogi-agent.exe` 需并存（便携版必须同目录）。
- 已在 Windows 11 + 真实硬件（有线键盘 + Unifying 鼠标）验证端到端流程。Windows 构建比 macOS 更新，遇到问题可上报。

> ⚠️ **安装前必读**：先退出 **Logi Options+**。两个程序会争夺 HID++ 访问权，同一接收器同一时刻只能被一个程序持有。

## 配置模型

配置全部收敛到**一个 TOML 文件**，可用任意方式在多机间同步。这既是特色也是取舍：相比官方图形化设置面板，OpenLogi 把「改配置」变成了「改文本」，对可脚本化、可版本管理的用户更友好，但也意味着上手门槛高于点选式 GUI。

## 跨平台现状与适用边界

| 平台 | 状态 | 备注 |
|------|------|------|
| macOS | 完整支持 | macOS 13+ |
| Linux | 一等平台 | X11/XWayland 下支持按应用叠加 |
| Windows | 已支持但较新 | Windows 11 端到端验证 |

**适用人群**：被 Options+ 的账号、遥测或功能限制困扰的罗技用户；需要 Linux 驱动能力的用户；偏好纯文本、可脚本化配置的工程师。

**不适用/需注意**：项目未稳定，生产环境建议先评估；部分 macOS 专属动作在 Linux 无对应实现（no-op）；Windows 媒体键走 D-Bus MPRIS（Linux）；摄像头/键盘能力受硬件支持范围限制（README 均标注「supported devices」）。

## 技术底座与致谢

- 底层依赖 **Solaar**（开源 HID++ 实现）与 **Mouser**（本地无账号的 Options+ 替代）的思路。
- `crates/openlogi-hidpp` 是 `hidpp` crate 的 vendored fork（0BSD）。
- 许可证：双许可 Apache-2.0 / MIT；**logo 与品牌资产除外**（© 2026 AprilNEA，保留所有权利，不随代码许可）。

## 一句话总结

OpenLogi 用「Rust 原生 + 纯文本配置 + 无账号无遥测」重新定义了罗技外设的控制方式，Linux 与可脚本化是它相比官方 Options+ 最实质的差异——但请把它当作一个活跃演进的替代品，而非稳定的生产驱动。
