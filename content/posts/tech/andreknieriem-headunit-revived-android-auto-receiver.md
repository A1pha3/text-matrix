---
title: "Open Headunit：把旧 Android 平板变成 Android Auto 车机的开源方案"
date: 2026-06-24T20:55:27+08:00
lastmod: 2026-09-26T10:30:00+08:00
slug: "andreknieriem-headunit-revived-android-auto-receiver"
github_repo: "andreknieriem/open-headunit"
source_key: "gh:andreknieriem/open-headunit"
description: "Open Headunit（原名 Headunit Revived）是一个用 Kotlin 写的 Android Auto 接收端 App,让旧 Android 平板或手机变身为车载主机屏幕,复活了 mikereidis/headunit 原始项目,支持有线 USB 与四种无线路径,并提供完整的 Intent 自动化契约。"
draft: false
categories: ["技术笔记"]
tags: ["Kotlin", "开源项目"]
---

# Open Headunit：把旧 Android 平板变成 Android Auto 车机的开源方案

## 快速信息卡

| 指标 | 数值 |
|------|------|
| Stars | 2,498 |
| Forks | 210 |
| 许可证 | AGPL-3.0 |
| 语言 | Kotlin（内嵌 C 层：ffmpeg + libusb） |
| 最新版本 | v3.5.0-beta1（2026-09-25） |
| 仓库 | [andreknieriem/open-headunit](https://github.com/andreknieriem/open-headunit) |

数据为 2026-09-26 的 GitHub API 读数。

## 这篇文章解决什么问题

如果你手边有一台闲置的 Android 平板,扔掉可惜、用起来又嫌慢,但车机屏幕总让你失望——Open Headunit 就是为这个场景准备的：把平板变成 Android Auto 的接收端主机,手机依旧是投屏源,原车那块屏被彻底绕开。

这是一份项目导读加快速上手。文章会讲清楚它和原版 mikereidis/headunit 的关系、USB 有线与四条无线路径各自适合谁、Intent 自动化接口怎么用,最后给出适用边界和真实的常见坑。

## 项目身份卡

- **仓库**：[andreknieriem/open-headunit](https://github.com/andreknieriem/open-headunit)
- **改名历史**：2025-10 开源时叫 `headunit-revived`,后更名为 `open-headunit`；Google Play 上的应用包名 `com.andrerinas.headunitrevived` 一直未变
- **原始项目**：[mikereidis/headunit](https://github.com/mikereidis/headunit)（Michael Reid,2015-06 创建,2018-04 停更）
- **作者**：Andre Rinas（GitHub @andreknieriem,Play 商店开发者名 Andrerinas）,342 次提交居首,15 位以上贡献者参与
- **主语言**：Kotlin,原生层内嵌 ffmpeg 与 libusb
- **License**：AGPL-3.0（仓库内附 `COPYRIGHT_MICHAEL_REID_GPLv3AFFERO.txt` 向原作者致意）
- **Stars / Forks**：2,498 / 210
- **Topics**：android, androidauto, headunit
- **仓库创建**：2025-10-28；首个发布版 v1.0.0 于 2025-12-03
- **分发渠道**：[Google Play](https://play.google.com/store/apps/details?id=com.andrerinas.headunitrevived)、Amazon Appstore,另有配套 App [Wireless Helper](https://play.google.com/store/apps/details?id=com.andrerinas.wirelesshelper)
- **官网/文档**：[headunit.andrerinas.com](https://headunit.andrerinas.com/) 与 [GitHub Wiki](https://github.com/andreknieriem/open-headunit/wiki)（10 个页面,含硬件兼容、自动化、排障、FAQ）

## 这项目想干什么：一句话定位

Open Headunit 是个让平板/手机"扮演"Android Auto 车机的 App。它运行在一台 Android 设备（推荐平板）上,接收另一台手机发来的 Android Auto 投屏,把车机才能看到的地图、音乐、电话界面渲染在这块"次屏"上。

它处于 Android Auto 协议里 head unit（车机端）的位置。手机还是手机,只是不再依赖原车那块屏。整个流程不需要 Root。

## 为什么这个项目值得看

老车没有 CarPlay / Android Auto、新车屏又卡又封闭,是 Android 玩家圈里反复出现的需求。Google 官方没有提供独立的"Android Auto 接收器"应用。

Open Headunit 的价值在于：

1. **复活了 Michael Reid 的 headunit 项目**——原项目 2015 年创建、2018 年 4 月后停更,本项目的 README 明确写它是 "a revived version of the original headunit project by the great Michael Reid",并以同样的 AGPL-3.0 许可证继承原代码。
2. **迭代非常快**——从 2025-12-03 的 v1.0.0 到 2026-09-25 的 v3.5.0-beta1,10 个月里发了 106 个 release,累计 2,050 多次提交。v2.0 重写了连接核心（CommManager）并加入 Wi-Fi Direct,v3.0 加了设置导入导出、USB 设备白名单、二维码配对等一批功能。
3. **多人协作**——除作者外,andrecuellar（291 次提交）、o-jcardenass（247）、MrEAlderson（67）等贡献者深度参与,CHANGELOG 里多处功能直接署名致谢。
4. **自动化接口是正经设计过的**——不是"顺便能发个 Intent",而是一个独立的 `contract` 模块,17 个控制指令、状态广播、深链一应俱全,Tasker/MacroDroid/ADB 都有明确用法（下文详述）。

## 架构边界：它不是"转发画面"那么简单

理解这个项目最容易踩的误区,是以为它在"转发"什么——其实它自己就是一台虚拟车机：

```
┌──────────────┐   Android Auto 协议    ┌────────────────────────┐
│   你的手机    │ ────────────────────▶ │ 平板（Open Headunit）   │
│ （AA 投屏源） │  USB / Wi-Fi 五种通道  │  = 虚拟车机 = 解码渲染端 │
└──────────────┘                        └────────────────────────┘
                                                  │
                                                  ▼
                                          平板屏幕显示 AA 界面
```

Android Auto 投屏的本质是：手机端渲染好界面,把画面编码成 H.264/H.265 视频流推给车机,车机解码显示,同时把触摸、按键事件反向回传。所以 Open Headunit 要做的事至少包括：

- 实现 AA 协议的车机端（`aap` 包：消息封帧、SSL 握手、版本协商、视频/音频/控制/导航四类通道）
- 用内嵌的 ffmpeg 解码视频流（`app/src/main/cpp/` 下 131 个 ffmpeg 文件加一个 HEVC 解码入口,这就是它能撑 4K 分辨率、出问题能切 H.264 的原因）
- 反向回传触摸与按键（`input` 包）
- 路由媒体音频、电话音频与导航语音（`AapAudio` 与 Audio Sink 策略）

AA 协议没有官方公开文档,这些实现全部来自社区逆向。这也是为什么 Google 一旦调整协议或客户端行为（比如近一次的 AA 17.4 更新）,第三方实现就得跟着追赶——后文"连接方式"一节会展开。

## 连接方式：一条有线 + 四条无线

先说一个近期的重要背景：**Android Auto 17.4 起,Google 收紧了无线投影的自动启动,几乎所有第三方触发方式失效**——包括 Self-Mode 和 Wireless Helper 的自动拉起。README 顶部用整段 NOTE 郑重其事地说明了这一点。选哪条路径,取决于你手机的 Android Auto 版本：

| 路径 | 原理 | Android Auto 版本要求 |
|------|------|----------------------|
| USB 有线 | 数据线直连 | 无限制,最稳定 |
| USB 无线 Dongle | 车机侧插硬件加密狗 | 无限制,官方标注"最可靠" |
| Native Mode | App 直接实现 AA 原生无线握手 | 17.4+ 可用 |
| Headunit Server | 手机开 AA 开发者服务器 | 17.4+ 上 Self-Mode 的唯一解 |
| Wireless Helper | 配套 App 后台自动触发 | 仅 17.3 及以下 |

### USB 有线：最稳的入门路径

1. 平板上装 Open Headunit,手机上装 Android Auto。
2. 用数据线把手机连到平板。
3. 必要时把手机切到 Host-Mode 并选择 Android Auto。
4. 在 Open Headunit 里点 USB 按钮,列表里选中手机,确认连接,等待投屏启动。

地图、音乐、通话会直接渲染到平板上。第一次上手建议先走通这条路,再折腾无线。

### 无线路径一：USB Wireless Dongle（最可靠）

车机侧插一个标准的 USB 无线 Android Auto 加密狗,由硬件独立完成无线协商,与手机 AA 版本无关,即插即用。README 把它列为推荐方案——代价是要买硬件。

### 无线路径二：Native Mode（免 Helper App）

App 直接实现 Android Auto 的原生无线握手,支持 Wi-Fi Direct（P2P 直连,无需共享网络）和 Headunit Hotspot（平板做热点）两种传输。设置入口在 Open Headunit Settings → Android Auto Mode → Native Mode。这是 v2.0.0 引入、v3.x 持续增强的能力,还配套了 Google Nearby 连接（Beta）与自动扫描。

### 无线路径三：Headunit Server（17.4+ 上 Self-Mode 的唯一解）

用 Android Auto 内置的开发者服务器,手机和平板都能开。开启步骤：手机上打开 Android Auto 设置,一路滚到底,连点 "Version" 十次解锁开发者设置,右上角三点菜单里选 "Start headunit server",然后在 Open Headunit 里点 Wi-Fi 按钮连接。

对想在平板本机"自己投影自己"（Self-Mode）的用户,这是 AA 17.4+ 上唯一还走得通的路。

### 无线路径四：Wireless Helper（仅限 AA 17.3 及以下）

配套 App [Wireless Helper](https://play.google.com/store/apps/details?id=com.andrerinas.wirelesshelper) 在手机后台自动触发连接。设置：Open Headunit 的 Wireless Mode 设为 Helper Mode,两台设备同一网络或同一 Wi-Fi Direct 组,手机上启动 Helper 服务即可。

它的典型场景是"上车自动连"：平板随车供电亮屏,手机蓝牙一连上车机,Helper 自动拉起投影。但在 AA 17.4+ 上它的自动触发已经失效,老手机没升级 AA 的用户才用得上。

### Intent 与自动化：一个独立的 contract 模块

对 Tasker / MacroDroid / ADB 玩家,这个项目专门维护了一个 `contract` 模块,把自动化接口当正式 API 写文档（`contract/README.md`）,这在同类项目里少见。

**先记住最容易踩的坑**：应用包名和指令前缀刻意不同——包名是 `com.andrerinas.headunitrevived`（为了保留 Play 商店原上架）,指令前缀却是 `com.andrerinas.openheadunit`。用错了不会报错,只会静默无效。官方文档原话管这叫 "The one thing that trips everybody up"（把所有人都绊一跤的那件事）。

**深链**（走 Activity,发它们的自动化 App 需要"显示在其他应用上层"权限）：

```bash
adb shell am start -a android.intent.action.VIEW -d "headunit://connect?ip=192.168.1.25"
```

支持五个：`headunit://connect?ip=<IP>`、`disconnect`、`exit`、`nightmode?state=day|night|auto`、`selfmode`。App 还发布了 7 个启动器快捷方式,Samsung Modes and Routines 之类能直接拾取。

**广播指令**（走 BroadcastReceiver,不需要悬浮窗权限,是自动化首选）：

```bash
PKG=com.andrerinas.headunitrevived
RX=$PKG/com.andrerinas.openheadunit.automation.AutomationReceiver
adb shell am broadcast -n $RX -a com.andrerinas.openheadunit.ACTION_CONNECT --es ip 192.168.1.25
```

控制类 17 个指令全部开放给任何调用方：连接（`ACTION_CONNECT`,带 `ip` 走无线、不带则查 USB）、断开、Self-Mode、日/夜主题、启动/停止无线扫描、蓝牙唤醒手机（Native AA 模式）、重启音频管线、查询状态等。配置类 7 个指令（读写设置、日志级别、日志抓取导出）默认关闭,要在设置里先打开 "Allow external configuration"；即便打开,导出也会隐去热点密码等 6 个凭证键,写入路径也限制在应用外部目录和 Downloads。

**状态广播**：会话每次变化,App 都会发出 `com.andrerinas.headunitrevived.SESSION_STATE` 广播,带 `state`（connecting / connected / projecting / disconnected / failed）、`transport`（usb / wifi / self）、失败原因和存活时长。其中 `projecting` 才代表"Android Auto 真正在屏幕上跑视频"——想判断投影是否真的活着,这是设备上唯一可靠的信号。

## 源码结构：两个模块,读码从哪里入手

Open Headunit 是标准 Android 工程,两个 Gradle 模块：

```
open-headunit/
├── app/                        # 主应用
│   └── src/main/
│       ├── java/com/andrerinas/openheadunit/
│       │   ├── aap/            # AA 协议层（75 个文件：封帧、SSL、视频、音频、导航、版本协商）
│       │   ├── connection/     # 连接核心（193 个文件：CommManager + wifi/usb/self/carkey 子系统）
│       │   ├── decoder/        # 视频解码
│       │   ├── automation/     # AutomationReceiver（对外指令入口）
│       │   ├── main/           # 界面与设置页（41 个文件）
│       │   └── input/ location/ ssl/ utils/ view/ ...
│       ├── cpp/                # 原生层：ffmpeg（131 个文件）+ HEVC 解码入口 + libusb
│       └── proto/              # AA 协议的 protobuf 消息定义
└── contract/                   # 自动化契约模块（HeadUnitIntent.kt + 文档）
```

`connection/` 是理解工程质量的好样本：v2.0 重写后,连接决策被拆成一族明确的策略类——`ConnectionArbiter`（仲裁）、`ConnectionPriorityPolicy`（优先级）、`VideoStarvationPolicy`（视频断流判定）、`UnresponsivePeerPolicy`（对端无响应）、`TeardownGuard`（拆除保护）——Wi-Fi 子系统一个目录就有 128 个文件,无线连接的各种边角都在这里。

想读代码,从 `main/MainActivity.kt` 入手理清界面流,再到 `connection/` 挑一条路径（`usb/` 最短）看会话建立,最后进 `aap/` 看协议。`contract/src/.../HeadUnitIntent.kt` 文件头注释标注的日期是 2016 年 5 月——契约层的血统可以直接追到作者早期的 headunit 应用。

## 已知问题：README 点名的 5 个坑

README 把已知问题单列一节,全部来自作者与用户实测：

| 问题 | 触发条件 | 处理办法 |
|------|----------|----------|
| Google Maps 竖屏触摸失效 | 部分设备竖屏模式 | 把 App 设置里的 DPI 降到 200 以下（如 190）,通常恢复 |
| 无线连接频繁掉线 | 手机系统的"智能"网络功能 | 关掉 WiFi Assistant、"Switch between networks"、网络加速,并给两台设备关电池优化 |
| Android 10 及以下 Self-Mode 失效 | AA 16.4+ 禁用了旧系统的自动无线启动 | 手机上启动 AA 内置 Headunit Server,用 Wi-Fi 模式走 loopback 连接（wiki 有分步指引） |
| Wi-Fi Direct 连接很慢 | 与手机上跑 Google Assistant（而非 Gemini）相关 | 换用 Gemini 后恢复正常；作者坦言不知原因 |
| 卡在 "Android is starting" | 设备 H.265 解码器有缺陷 | 设置里把 Video Codec 从 Auto 改为 H.264 |

Wiki 的 [Troubleshooting](https://github.com/andreknieriem/open-headunit/wiki/Troubleshooting) 页还收录了一批高频问题的对症方案,几个值得提前知道的：

- **绿屏/花屏**：多数是老设备 H.265 硬解不行,切 H.264、把 View Mode 换成 GLES20 或 TextureView、或降分辨率。
- **黑屏但有声音**：在 Settings → Video 里开 Force Software Decoding。
- **画面 30 FPS 不是 bug**：Android Auto 在无交互时主动降到 30 FPS 省电,一触摸就回 60 FPS。
- **音乐反复暂停**：手机同时连着车机/平板的蓝牙媒体音频与 AA 音频流冲突所致,这是 Google 支持社区确认的 AA 已知问题——把该蓝牙设备的"媒体音频"关掉即可（电话音频保留）。
- **手机热点直连难成**：手机开热点（10.x 网段）时手动连接 5277 端口常因手机侧路由问题失败,改用 Helper Mode 或 Native Mode。
- **追求无线画质**：高码率流用 5GHz Wi-Fi。

## 和原版 mikereidis/headunit 的关系

| 维度 | mikereidis/headunit（原版） | andreknieriem/open-headunit |
|------|------------------------------|------------------------------|
| 时间线 | 2015-06 创建,2018-04 起停更 | 2025-10 开源至今,106 个 release |
| 语言 | C | Kotlin + C 原生层（ffmpeg/libusb） |
| 许可证 | AGPL-3.0 | AGPL-3.0（附原作者版权致意文件） |
| 平板端系统 | 老版本 Android | Android 4.1+（SDK 16）起 |
| 无线连接 | 无或实验性 | Wi-Fi Direct / 热点 / Server / Helper 四条路径 |
| 自动化 | 无正式接口 | contract 模块：17 个控制指令 + 状态广播 + 深链 |
| 分发 | 源码自编译 | Google Play、Amazon Appstore、GitHub Releases |

判断很简单：今天入坑直接用 Open Headunit。原版只在考古旧协议实现时还有价值。

## 适用边界

**适合**：

- 旧车无 Android Auto / CarPlay,想低成本升级
- 原车屏拉胯（颗粒感、卡顿、UI 老）,但有闲置 Android 平板
- DIY 玩家与 Tasker / MacroDroid 自动化玩家
- 想研究 Android Auto 协议实现的开发者（`aap/` 包是 Android Auto 车机端少有的公开实现之一）

**不适合**：

- iPhone 用户——这是 Android Auto 生态的方案,CarPlay 需要另找（CarPlay 没有官方接收端方案）
- 完全不想动手机设置的人——手机要装 Android Auto,无线还可能要装 Helper 或开开发者设置
- 期待"装机即完美"的人——投屏链路涉及两台设备、无线协商、视频解码,首次配置多半要按 wiki 排一两个坑

---

## 进阶路径

### 阶段 1：快速体验（1-2 天）

- [ ] 平板装 Open Headunit（Google Play 或 GitHub Releases）
- [ ] 手机装 Android Auto
- [ ] USB 数据线连接,走通首次有线投屏
- [ ] 验证地图、音乐、电话三个基础功能

### 阶段 2：无线连接（1 周）

- [ ] 对照上文连接方式表,按手机 AA 版本选路径（17.3 及以下可走 Helper；17.4+ 优先 Native Mode 或 Dongle）
- [ ] 追求稳定给两台设备关闭电池优化
- [ ] 无线掉线就回看"已知问题"一节,逐一排除系统"智能"网络功能

### 阶段 3：自动化集成（2-4 周）

- [ ] 读 `contract/README.md`,记住包名与前缀的区别
- [ ] Tasker/MacroDroid 用 Broadcast Receiver 目标发 `ACTION_CONNECT`,免去悬浮窗权限
- [ ] 用 `SESSION_STATE` 广播做状态联动（如 `projecting` 时亮出仪表主题）
- [ ] 深链方式验证：`adb shell am start -a android.intent.action.VIEW -d "headunit://connect?ip=<PHONE_IP>"`

### 阶段 4：深度定制（1-3 个月）

- [ ] clone 源码,按"源码结构"一节的路径读码
- [ ] 定制 UI、DPI、按键映射（`KeymapFragment`）
- [ ] 从 wiki 的 Translations 页参与翻译,或修 bug 提 PR

---

## 动手练习

### 练习 1：完成首次有线连接

找一台闲置 Android 平板和一台 Android 手机,按 README 指引完成 USB 投屏,记录遇到的问题。

<details>
<summary>参考思路</summary>

**步骤**：
1. 平板装 Open Headunit,手机装 Android Auto
2. 数据线连接两台设备（确认线支持数据传输,只能充电的线不行）
3. 必要时在手机上切换到 Host-Mode 并选择 Android Auto
4. 平板上点 USB 按钮,列表里选中手机并确认
5. 等待投屏启动,测试触摸回传是否正常

**可能遇到的问题**：
- 列表里找不到手机：换一根确定能传数据的线
- 连接后马上断开：查 wiki 排障页的 Broken Pipe 条目,给两台设备关电池优化
- 画面卡在 "Android is starting"：把 Video Codec 改为 H.264

</details>

### 练习 2：配置无线上车自动连（AA 17.3 及以下）

在练习 1 基础上,用 Wireless Helper 实现"上车自动连"。

<details>
<summary>参考思路</summary>

**步骤**：
1. 手机装 Wireless Helper
2. 平板与手机同一网络（或平板开热点/组 Wi-Fi Direct）
3. 平板 Settings 里把 Wireless Mode 设为 Helper Mode
4. 手机上启动 Wireless Helper 服务
5. 上车后蓝牙一连,Helper 自动拉起投影

**排查**：
- 频繁掉线：关掉手机的 WiFi Assistant / 网络切换类功能
- 找不到设备：确认同网段或同一 Wi-Fi Direct 组,必要时按 wiki 用 Wi-Fi Analyzer 找平板的 P2P BSSID 填进 Static BSSID

</details>

### 练习 3：用 Tasker 实现"上车自动启动"

<details>
<summary>参考思路</summary>

**Tasker 配置**：
- Profile 触发：State → Net → Bluetooth Connected → 选车载蓝牙
- 任务动作：Action → Misc → Send Intent,Target 选 **Broadcast Receiver**,Package 填 `com.andrerinas.headunitrevived`,Class 填 `com.andrerinas.headunitrevived/com.andrerinas.openheadunit.automation.AutomationReceiver`,Action 填 `com.andrerinas.openheadunit.ACTION_CONNECT`

**要点**：
- 走 Broadcast Receiver 目标不需要"显示在其他应用上层"权限；发深链（activity 目标）才需要
- 想知道投影是否真的起来了,监听 `com.andrerinas.headunitrevived.SESSION_STATE` 广播,等 `state=projecting`
- 配置类指令（改设置、导日志）要先在 App 设置里打开 Allow external configuration

</details>

---

## 自测题

1. Open Headunit 在 Android Auto 协议里扮演哪一端？手机渲染的画面以什么形式到达平板？
2. AA 17.4 之后,为什么 Wireless Helper 的自动触发失效了？此时 Self-Mode 还剩哪条路？
3. 自动化时包名 `com.andrerinas.headunitrevived` 和指令前缀 `com.andrerinas.openheadunit` 为什么不一样？用错了会报错吗？
4. `SESSION_STATE` 广播的五种 state 里,哪一个才代表"Android Auto 真的在跑"？为什么说它是设备上唯一的可靠判据？
5. README 点名的 5 个已知问题里,哪些是 App 层面能修的,哪些是 Google 或 OEM 策略层的限制？

## 进阶阅读

- 官方文档站：[headunit.andrerinas.com](https://headunit.andrerinas.com/)
- GitHub Wiki（排障/自动化/硬件兼容/设置详解）：[github.com/andreknieriem/open-headunit/wiki](https://github.com/andreknieriem/open-headunit/wiki)
- 自动化契约文档：仓库内 `contract/README.md`
- 原版项目（考古用）：[mikereidis/headunit](https://github.com/mikereidis/headunit)
- Tasker 官网：[tasker.joaoapps.com](https://tasker.joaoapps.com/)

## 常见问题

### Q1：需要 Root 吗？

**A**：不需要。全程通过 Android Auto 的既有协议通道通信,无线用的开发者服务器也是 AA 自带的隐藏功能,不碰系统分区。

### Q2：能不能只跑平板、手机不装 Android Auto？

**A**：分两种情况。标准玩法是"手机投屏、平板显示",手机必须装 Android Auto,它是投屏源头。另有 Self-Mode：平板自己装 Android Auto 自己投影自己（适合没有第二台设备的测试场景）,AA 17.4+ 上需要启动内置 Headunit Server 才能触发。

### Q3：Wireless Helper 是什么来头？

**A**：作者官方推荐的配套 App,Google Play 可下。注意它只负责触发无线连接,且在 AA 17.4+ 上自动触发已失效——新手机优先考虑 Native Mode。

### Q4：能装在车机原生系统里直接跑吗？

**A**：项目的目标设备是通用 Android 平板/手机。部分改装安卓车机本质就是大平板,装得上就能跑（wiki 的 Supported-Hardware 页专门讨论 MTK、Rockchip 等芯片方案的最优设置）,但原厂车机系统受限多,以实际尝试为准。

### Q5：Google Maps 竖屏模式触摸失效怎么办？

**A**：已知问题。在 App 设置里把 DPI 降到 200 以下（如 190）,通常恢复。

### Q6：无线连接频繁掉线怎么排查？

**A**：最常见的原因是手机系统的"智能"网络功能——投屏用的 Wi-Fi 往往没有互联网,系统会主动切换或断开。依次检查：关掉 WiFi Assistant / "Switch between networks" / 网络加速；给两台设备关电池优化；高码率场景用 5GHz Wi-Fi。

### Q7：USB 连接后平板没反应怎么办？

**A**：按顺序查：线是否支持数据传输；手机是否切到 Host-Mode；平板上是否点了 USB 按钮并选中手机；视频编解码是否需要从 Auto 改为 H.264（老设备 H.265 硬解常见问题）。

### Q8：Intent 发了没反应？

**A**：九成是包名与前缀用混了。广播指令的 Package 是 `com.andrerinas.headunitrevived`,Action 前缀是 `com.andrerinas.openheadunit.`,用错不报错、静默无效。第二常见原因是把深链当广播发——深链走 Activity,需要"显示在其他应用上层"权限,改走 AutomationReceiver 即可绕开。

### Q9：Open Headunit 和 CarPlay 能同时用吗？

**A**：不能。它只实现 Android Auto 协议。CarPlay 没有官方接收端方案,需要另找社区实现。

### Q10：想跟进项目动态,看哪里？

**A**：仓库的 CHANGELOG 记录了全部 106 个版本的明细；Wiki 首页维护着"Latest Version"；官网有 Getting Started 与 FAQ。问题的最佳提问处是仓库 Issues。

---

## 参考来源与口径说明

- **仓库元数据**（stars/forks/时间线/贡献者）：GitHub API,2026-09-26 读数；改名经由 API 301 重定向确认（仓库 ID 1084806666 不变）。
- **版本与功能演进**：仓库 `README.md`、`CHANGELOG.md`（main 分支）与 GitHub Releases（106 条）；AA 17.4 兼容性说明以 README 顶部 NOTE 与 Wiki Wireless 页为准。
- **连接方式与已知问题**：README "How to use" 与 "Known Issues" 两节原文；排障细节出自 Wiki 的 Wireless、Troubleshooting 两页。
- **自动化接口**：仓库 `contract/README.md` 与 `contract/src/.../HeadUnitIntent.kt` 源码；指令清单、Extras、权限边界均照原文。
- **源码结构**：GitHub git trees API 全量目录列表（1,321 项）；包名、文件数、ffmpeg/libusb 构成实测。
- **原版数据**：mikereidis/headunit 仓库 GitHub API（创建 2015-06、最后推送 2018-04-25、语言 C、AGPL-3.0）。
- **分发与官网**：Google Play 两条目（Open Headunit、Wireless Helper）与 headunit.andrerinas.com 均 2026-09-26 实测可达。
- 文中未标注出处的体验性描述（如"最稳""拉胯"）为行文判断,技术事实以上列信源为准。
