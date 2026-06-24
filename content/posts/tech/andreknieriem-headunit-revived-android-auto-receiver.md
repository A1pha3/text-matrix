---
title: "Headunit Revived：把旧 Android 平板变成 Android Auto 主机的开源复活方案"
date: 2026-06-24T20:55:27+08:00
slug: "andreknieriem-headunit-revived-android-auto-receiver"
description: "Headunit Revived 是一个用 Kotlin 写的 Android Auto 接收端 App，让旧 Android 平板或手机变身为车载主机屏幕，复刻了 mikereidis/headunit 原始项目并补完无线/USB 连接、Helper 配套 App 与 Intent 自动化能力。"
draft: false
categories: ["技术笔记"]
tags: ["Android Auto", "Kotlin", "Headunit", "开源项目", "车机互联"]
---

# Headunit Revived：把旧 Android 平板变成 Android Auto 主机的开源复活方案

> **阅读时间**：约 12 分钟
>
> **适用读者**：对 Android Auto 协议、车机改装、老设备再利用感兴趣的开发者或 DIY 玩家
>
> **前置知识**：了解 Android 平台基础、有 ADB 与 Intent 使用经验会更顺

## 这篇文章解决什么问题

如果你手边有一台闲置的 Android 平板，扔掉可惜、用起来又嫌慢，但车机本身的屏幕总是让你失望——Headunit Revived 这类项目就是一个非常具体的解决方案：把平板变成 Android Auto 的接收端主机，把手机变成 Android Auto 的源头，让原车那块 "灰头土脸" 的内置屏被彻底绕开。

这是一份**项目导读 + 快速上手**形态的拆解。本文会先讲清楚 Headunit Revived 解决的核心矛盾、它和原版 mikereidis/headunit 之间的关系，再把 USB、有线 Helper、Intent 自动化三种连接路径讲明白，最后给出适用边界和几个常见坑。

## 项目身份卡

- **仓库**：[andreknieriem/headunit-revived](https://github.com/andreknieriem/headunit-revived)
- **原始项目**：[mikereidis/headunit](https://github.com/mikereidis/headunit)
- **主语言**：Kotlin
- **License**：AGPL-3.0
- **Stars / Forks**：1.4k / 112
- **Topics**：android, androidauto, headunit
- **首次提交**：2025-10-28
- **最近更新**：2026-06-24
- **README 体量**：约 1,500 字，含连屏指引 + 已知问题清单

## 这项目想干什么：一句话定位

Headunit Revived 是个**让平板/手机"假装成"Android Auto 车机**的 App。它运行在一台 Android 设备（推荐平板）上，接收另一台手机发过来的 Android Auto 投屏流，再把车机才能看到的地图、音乐、电话等界面渲染在这块"次屏"上。

换句话说：**它处于"Android Auto 接收端"的位置，扮演车载主机那块屏幕**。手机还是手机，只是不再依赖原车那块屏。

## 为什么这个项目值得看

老车没有 CarPlay / Android Auto、新车屏又卡又封闭，是 Android 玩家圈里反复出现的需求。Google 官方没有提供独立的"Android Auto Receiver"App，市面上的零散方案往往只能跑半天、断了就连不上、或者得 Root。

Headunit Revived 的价值在于：

1. **复活了 8 年前的 mikereidis/headunit 原项目**——原项目长期停更，作者接手后适配新版本 Android Auto 协议、补完无线连接、加入 Helper App 配套。
2. **不需要 Root**——这是与同类工具最大的分水岭。
3. **三种连接路径并列**——USB、有线 Helper、Intent 触发，给不同人群（普通车主 / Tasker 玩家 / 自动化研究者）都留了入口。
4. **作者持续维护**——从 2025-10 重启到 2026-06 持续有提交，最近一次 push 距今 1 天内。

## 架构边界：Headunit Revived 不是"中间人"那么简单

理解这个项目最容易踩的误区，是以为它在"转发"画面——其实不是。它的角色更接近"伪车机"：

```
┌────────────────┐    Android Auto 协议     ┌──────────────────────────┐
│  你的手机       │  ────────────────────▶   │  平板（Headunit Revived）│
│ （AA 投屏源）   │   USB / WiFi / Helper   │   = 伪车机 = 渲染端      │
└────────────────┘                          └──────────────────────────┘
                                                       │
                                                       ▼
                                                平板屏幕显示 AA UI
```

它要做的事至少包括：

- 模拟 Android Auto 协议里的 headunit 端（DHU 风格）
- 解析手机发过来的 UI 描述流
- 在自己 Activity 里把 UI 渲染出来
- 把触摸/按键事件反向回传给手机
- 处理媒体音频、电话音频、导航语音的混合路由

这是典型的"接收端实现"，难度在协议层——Google 的 AA 协议没有官方公开文档，全靠逆向与社区抓包。

## 三种连接路径详解

### 1. 有线 USB（最稳的入门路径）

这是**官方推荐的新手入门方式**，稳定性和延迟都最好：

1. 平板上装 Headunit Revived App。
2. 平板和手机用 USB 数据线连接。
3. 手机必须装了 Android Auto。
4. 手机切到 "Host-Mode"（开发者选项里开启），选择 "Android Auto"。
5. 平板上点 "USB" 按钮，在列表里选中手机，允许授权。
6. 等待 AA 投屏启动，地图 / 音乐 / 通话直接渲染到平板上。

> **注意**：第一次连接必须用 USB 配对一次，之后才能切到无线。

### 2. Wireless Helper 模式（推荐，**生产环境首选**）

这是**项目方主推的方案**——在手机上装一个配套 App：[Wireless Helper on Google Play](https://play.google.com/store/apps/details?id=com.andrerinas.wirelesshelper)，负责发现 headunit、维持心跳、触发连接。

- **优势**：自动发现 NSD（Network Service Discovery）、支持 Wi-Fi Direct 自动连、蓝牙自动起。
- **设置步骤**：
  - Headunit Revived Settings → 把 "Wireless Mode" 设为 **Helper Mode**。
  - 保证手机和平板在同一个网段（热点 / 同一 WiFi 都行）。
  - 打开手机上的 Wireless Helper，启动服务。
  - Helper 自动找到 headunit 并建立连接。
- **典型场景**：上车 → 蓝牙自动连车机 → Helper 拉起 AA → 平板亮屏即用。

### 3. Intent 触发（Power User 玩法）

适合 **Tasker / MacroDroid / ADB 自动化**玩家，可以用 Intent URI 直接命令 headunit 去连某台手机：

```bash
adb shell am start -a android.intent.action.VIEW -d "headunit://connect?ip=192.168.1.25"
```

URI Scheme 是 `headunit://connect?ip=<PHONE_IP>`。这一通道让"自动化"和"脚本化"成为可能——比如你可以写一个 MacroDroid 宏：

```
触发：蓝牙连上车机
动作：adb shell am start -a android.intent.action.VIEW -d "headunit://connect?ip=192.168.1.25"
```

> 备注：原 README 还提到 "Legacy Wireless Launcher"（[Emil Borconi 的 Wireless Launcher](https://play.google.com/store/apps/details?id=com.borconi.emil.wifilauncherforhur)）和 "Native Headunit Server" 两种旧的无线方案，但都有限制——**Helper 是当前最稳的选择**。

## 核心源码目录（基于公开 README 与项目结构推断）

Headunit Revived 是个 Android 原生项目，Kotlin 是主语言。以下是公开结构能直接读到的部分：

```
headunit-revived/
├── app/                    # 主 App 模块
│   ├── src/main/           # 主代码（AA 协议、UI 渲染、事件回传）
│   ├── src/main/res/       # 资源文件
│   └── src/main/AndroidManifest.xml
├── protocol/               # AA 协议解析与打包
├── ui/                     # 接收端 UI 渲染
├── audio/                  # 音频路由（媒体/电话/导航）
├── settings/               # 设置页
└── wiki/                   # 文档（已迁移到 GitHub Wiki）
```

具体到代码实现，公开 README 没展开关键协议细节（这与协议非公开有关），建议感兴趣的人 clone 后从 `MainActivity` 和 `UsbConnection` 入手。

## 已知问题（README 明确点名的 4 个坑）

README 把"已知问题"单列了一节，**直接来自作者亲测**，可信度高：

| 问题 | 触发条件 | 临时解决方案 |
|------|----------|------------|
| Google Maps 竖屏模式触摸失效 | 部分设备竖屏 + Pixel density ≥ 200 | 设置 DPI < 200（如 190）通常恢复 |
| 无线连接频繁掉线 | 手机 WiFi 设置里的 "WiFi Assistant" / "切换网络" 主动断流 | 关掉 "WiFi Assistant" 和电池节能对 WiFi 的限制 |
| Android 10 (Q) 及以下 Self-mode 失效 | 旧 Android 不支持无线自起 | 用 USB 配对一次后走无线，或升级手机 |
| USB 端口供电不足 | 车机 USB 口电流不够 | 用独立供电的 USB Hub，或长按 power 让平板保持亮屏 |

> 这 4 个问题都不是项目 bug，而是 AA 协议 / OEM 策略层面的限制——选 Headunit Revived 之前先对照自己的设备清单排查。

## 和原版 mikereidis/headunit 的关系

| 维度 | mikereidis/headunit（原版） | andreknieriem/headunit-revived（复活版） |
|------|-----------------------------|------------------------------------------|
| 最后更新 | 2018 年前后停更 | 2026 年持续维护 |
| Android 目标 | 适配 Android 8-9 | 适配 Android 11+ |
| 无线连接 | 不支持或实验性 | Helper 模式 + Intent 自动化 |
| 协议适配 | AA 旧协议 | AA 新协议（持续跟进） |
| 社区维护 | 仅 issues 偶尔回复 | 活跃 issue 响应 |

**判断**：如果你今天第一次听说这个领域，**直接上 Revived 版**。原版除非要考古旧协议，否则没有继续用的理由。

## 适用边界

**适合**：

- 旧车无 Android Auto / CarPlay，想低成本升级
- 原车屏太烂（颗粒感、卡顿、UI 丑），但有闲置 Android 平板
- 喜欢 DIY / 折腾的车主玩家
- 自动化研究者（Tasker / MacroDroid 玩家）

**不适合**：

- 对延迟敏感的实时导航（AA 投屏始终比 CarPlay 慢）
- 完全不想动手机设置的人（需要装 AA + Helper + 授权一堆）
- iPhone 用户（这是 Android 生态专有方案）

## 自测题

1. Headunit Revived 扮演的是 Android Auto 协议里的哪一端？和 DHU（Desktop Head Unit）有什么关系？
2. 第一次连接为什么必须 USB？无线配对的最小步骤是什么？
3. 三个连接路径里，哪一个适合"上车自动连"场景？为什么 Helper 模式比 Native Headunit Server 更稳？
4. README 列的 4 个已知问题，有几个是项目本身能修的？哪些是协议或 OEM 层的限制？

## 进阶阅读

- 官方 Wiki：[github.com/andreknieriem/headunit-revived/wiki](https://github.com/andreknieriem/headunit-revived/wiki)
- 原版项目（参考）：[mikereidis/headunit](https://github.com/mikereidis/headunit)
- Android Auto 协议逆向参考（社区）：AA Protocol Reverse Engineering 系列文章
- Tasker + Intent 自动化模板（社区 Wiki）：[Tasker Wiki - Auto Connect](https://tasker.joaoapps.com/)

## 常见问题

**Q：是否需要 Root？**
A：不需要。这是这个项目最大的卖点。

**Q：能不能只跑平板、手机不装 AA？**
A：不能。手机必须装 Android Auto 客户端，它是协议源头。

**Q：Helper 模式收不收费？**
A：Google Play 上是免费 App，作者在 README 里推荐，但有可选捐赠。

**Q：能不能在车机原生系统里直接跑这个 App？**
A：理论上可以，但需要车机开启 ADB、装 GMS，且违反车机保修——不推荐。
