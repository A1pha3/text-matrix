+++
date = '2026-05-21T11:50:00+08:00'
draft = false
title = 'Phosphene：macOS 视频壁纸引擎'
slug = 'phosphene-macos-video-wallpaper-engine'
description = 'Phosphene 是一个 macOS 视频壁纸引擎，支持将视频文件设置为桌面背景，兼容 macOS Tahoe 系统。'
categories = ['技术笔记']
tags = ['macOS', '开源', 'Swift', '桌面美化']
+++

# Phosphene：macOS 视频壁纸引擎

Phosphene 把视频壁纸这件事在 macOS 上做对了，做法是调用 Apple 私有的 `WallpaperExtensionKit` 框架——和系统自带 Aerials（航拍壁纸）走同一条通路。这意味着它不需要在桌面层塞一个透明窗口，也不需要常驻一个播放器进程假装是壁纸。代价是依赖私有 API，Apple 任何一次大版本更新都可能让它失效。

项目地址：[kageroumado/phosphene](https://github.com/kageroumado/phosphene)。2026 年 5 月 21 日开源，MIT 许可，Swift 6 编写，目标平台 `arm64-apple-macos26.0`。仓库当前 7 个 commit、1 个 tag（v1.0），作者在 README 里说明这个项目原本是商业软件，因为"macOS 视频壁纸应用市场比看起来拥挤"才转开源。

## 目录

- [学习目标](#学习目标)
- [为什么 macOS 上的视频壁纸难做](#为什么-macos-上的视频壁纸难做)
- [系统地图：Phosphene 的两层结构](#系统地图phosphene-的两层结构)
- [任务如何流过系统：从导入到渲染](#任务如何流过系统从导入到渲染)
- [关键工程决策](#关键工程决策)
- [与 Windows Wallpaper Engine 的对比](#与-windows-wallpaper-engine-的对比)
- [macOS Tahoe 适配与 API 风险](#macos-tahoe-适配与-api-风险)
- [适用场景与边界](#适用场景与边界)
- [采用顺序与决策建议](#采用顺序与决策建议)
- [常见问题](#常见问题)
- [进阶路径](#进阶路径)

## 学习目标

读完这篇文章后，你应当能够：

- 说清 macOS 上做视频壁纸的三层技术障碍（桌面层、Space 持久化、远程渲染上下文），并解释为什么 Windows 的 `WorkerW` 方案在 macOS 上没有等价物。
- 画出 Phosphene 的两层结构（菜单栏应用 + 壁纸扩展），标出 App Group 容器与 Darwin 通知在两者之间承担的角色。
- 描述一个 MP4 文件从导入到渲染成壁纸的完整路径，包括 `acquire`/`update`/`invalidate`/`snapshot` 四个 XPC 回调的触发时机。
- 解释 Phosphene 为什么用 `AVSampleBufferDisplayLayer` 而不是 `AVPlayerLayer`，以及 `PlaybackPolicy` 如何把多个输入信号塌缩成四个状态。
- 识别私有 API（`WallpaperExtensionKit`、`Mirror` 反射、`NSXPCCoder` swizzle）带来的维护风险，并知道升级 macOS 前需要验证哪些环节。

## 为什么 macOS 上的视频壁纸难做

Windows 上有 [Wallpaper Engine](https://www.wallpaperengine.io/) 这类成熟方案，底层靠的是把渲染窗口挂到 `WorkerW`（`Progman`/`SHELLDLL` 的子窗口）上，桌面图标层在上面、壁纸层在下面，公开 API 就能实现。macOS 没有等价机制，原因有三层。

**第一层障碍在桌面层。** macOS 的桌面背景由系统进程管理，窗口层级（NSWindow level）里有一个 `kCGDesktopWindowLevel`，理论上可以把窗口放到这个层级，但 Finder（访达）的桌面图标层会盖在上面，且系统在切换 Space（工作区）、连接外接显示器、进入锁屏时会重建桌面层，自定义窗口很难跟上这些事件。

再往上一层是 Space 与多显示器的持久化。macOS 允许每个 Space、每台显示器配置不同壁纸，状态由系统持久化。第三方窗口方案做不到这一点——用户切到另一个 Space，视频窗口要么不跟过去，要么跟过去但和系统壁纸冲突。Apple 自己的 Aerials 能正确处理，是因为它们注册成系统壁纸提供方（wallpaper provider），由系统的 `WallpaperAgent` 进程统一调度。

就算前两层都绕过去，还有最后一个坑：视频解码与远程渲染上下文冲突。把 `AVPlayerLayer` 放进系统壁纸的远程 `CAContext`（Core Animation 上下文）里会静默失败——不报错，但画面不出。这是 Phosphene 在 README 里明确点出的坑，也是为什么它不用 `AVPlayerLayer`。

## 系统地图：Phosphene 的两层结构

Phosphene 由一个菜单栏应用和一个壁纸扩展（wallpaper extension，`.appex`）组成，两者通过 App Group 容器共享数据，通过 Darwin 通知同步状态。

```
┌─────────────────────────┐  ┌──────────────────────────────┐
│ Phosphene.app           │  │ PhospheneExtension.appex     │
│ (菜单栏 UI)              │  │ (宿主: WallpaperAgent)        │
│                         │  │                              │
│ • 视频库管理              │  │ • XPC handler                │
│ • 视频元数据              │  │ • AVSampleBufferDisplayLayer │
│ • HEVC 转码              │  │ • 电源/温度监控               │
│ • 偏好设置                │  │ • 快照生成                   │
└─────────────────────────┘  └──────────────────────────────┘
            │                              │
            └──────────┬───────────────────┘
                       ▼
           Shared App Group container
           (~/Library/Group Containers/glass.kagerou.phosphene)
           • 视频库 + 降分辨率变体
           • WallpaperPrefs.plist
           • BMP 快照缓存
```

应用侧（`Phosphene/`）是 SwiftUI 菜单栏应用，负责管理磁盘上的视频库、用 `VideoOptimizationService` 转码可选的低分辨率变体、暴露偏好设置，库变化时发一个 Darwin 通知。

扩展侧（`PhospheneExtension/`）运行在系统的 `WallpaperAgent` 进程里，当某个 Phosphene 壁纸处于激活状态时被拉起。它通过 `dlopen` 运行时加载 `WallpaperExtensionKit.framework`，注册成壁纸提供方，把帧渲染进远程 `CAContext`。系统通过 XPC 调用 `acquire`/`update`/`invalidate`/`snapshot` 四个方法，扩展把展示模式（活跃/锁屏/空闲）的变化路由给 `PlaybackPolicy`。

## 任务如何流过系统：从导入到渲染

把一个 MP4 设成壁纸，完整路径是这样的：

1. 用户从菜单栏点 **Manage Library**，选一个 AVFoundation 能读的视频文件（MP4/MOV 等）。
2. 应用侧把视频拷进 App Group 容器，可选触发 `VideoOptimizationService` 预渲染低分辨率/低帧率变体（比如 1080p@30）。
3. 用户打开 **系统设置 → 壁纸**，Phosphene 的视频出现在独立分类下——和 Apple 自带 Aerials 并列。
4. 用户选中某个视频。macOS 把这个选择记到系统壁纸持久化里，按显示器和 Space 分别保存。
5. 系统 `WallpaperAgent` 进程通过 XPC 调用扩展的 `acquire`，扩展开始用 `AVSampleBufferDisplayLayer` 往远程 `CAContext` 推帧。
6. 解码管线用两个 `AVAssetReader`：一个跑当前循环，一个预加载下一个循环；PTS（presentation timestamp）偏移随循环累加，保持时间线单调递增，实现无缝循环。
7. 系统进入锁屏或空闲时，`WallpaperAgent` 通过 XPC 通知 `update`，`PlaybackPolicy` 把状态从 `full` 降到 `reduced`/`minimal`/`paused`，渲染器在下一个循环边界切换到更便宜的变体或暂停。

## 关键工程决策

### 用 AVSampleBufferDisplayLayer 而不是 AVPlayerLayer

`AVPlayerLayer` 在远程 `CAContext` 里静默失败，这是 Phosphene 必须绕开的硬约束。`VideoRenderer` 改用手动驱动 `AVSampleBufferDisplayLayer`：自己管 `AVAssetReader`、自己算 PTS 偏移、自己在循环边界做无缝拼接。代价是解码逻辑全部自己写，收益是渲染能跑在系统壁纸进程里，和 Aerials 走同一条路。

### PlaybackPolicy 作为单一真相源

`PlaybackPolicy` 是播放行为的唯一决策点。输入信号——温度状态、电池电量、用电模式（电池/充电）、Game Mode、展示模式（活跃/锁屏/空闲）、用户手动暂停、窗口遮挡——全部塌缩成四个状态之一：`full`/`reduced`/`minimal`/`paused`。渲染器在每次状态变化时应用策略。

这里有个容易踩的坑：变体（variant）是建议性的。即使预渲染了 1080p@30 的变体，如果 `PlaybackPolicy` 判断当前在充电且空闲，它会选最高档而不是省电档。变体只在策略允许的范围内挑最便宜的那个。

### Mirror 反射 + 运行时 swizzle

`WallpaperExtensionKit` 是私有框架，Apple 的请求类型（`WallpaperCreationRequestXPC` 等）不在任何公开 SDK 头文件里。扩展用 `Mirror` 反射读取这些类型的字段。如果 Apple 重命名字段，会出"外科手术式"的破坏——某一行字段读不到，对应功能失效。

另一个坑在快照编码。系统的快照编码器检查 `type(of: coder) == NSXPCCoder.self`，但实际传入的 coder 是 `NSXPCCoder` 的子类，类型检查失败。Phosphene 在 `PhospheneExtension.swift` 里做了一个运行时 swizzle（方法混淆）绕过这个检查。不做这个 swizzle，快照会编码成空，锁屏切换时看到的是灰屏。

## 与 Windows Wallpaper Engine 的对比

| 维度 | Wallpaper Engine (Windows) | Phosphene (macOS) |
|---|---|---|
| 底层机制 | `WorkerW` 窗口挂载，公开 API | `WallpaperExtensionKit` 私有框架 |
| 内容类型 | 2D/3D 动画、视频、网页、应用 | 视频文件（AVFoundation 可读格式） |
| 生态系统 | Steam 创意工坊，海量内容 | 自带视频（BYO videos） |
| 多显示器 | 支持 | 支持，每显示器独立壁纸 |
| Space/虚拟桌面 | Windows 虚拟桌面支持有限 | 每个 Space 独立壁纸，系统持久化 |
| 电源管理 | 有，但依赖 Windows 电源策略 | `PlaybackPolicy`，按温度/电池/模式分级 |
| 锁屏集成 | 有限 | 系统级锁屏/空闲生命周期集成 |
| 风险 | 公开 API，稳定 | 私有 API，Apple 大版本可能破坏 |
| 平台 | Windows | macOS Tahoe 26.0+，Apple Silicon only |

Wallpaper Engine 胜在内容生态和稳定性（公开 API），Phosphene 胜在和系统壁纸机制的深度集成（锁屏、Space、多显示器都由系统管理）。两者的工程路线完全不同：Wallpaper Engine 是"在桌面层放一个渲染窗口"，Phosphene 是"注册成系统壁纸提供方"。

## macOS Tahoe 适配与 API 风险

Phosphene 的硬性要求：

- **macOS Tahoe (26.0+)**：壁纸扩展点（wallpaper extension point）在 macOS 14 引入，但 Phosphene 用了 Tahoe 才有的 SwiftUI API 和 `glassEffect()`。
- **Apple Silicon**：目标三元组 `arm64-apple-macos26.0`，Intel Mac 不支持。
- **Xcode 17+**：开启 Swift 6 strict concurrency（严格并发）。

私有框架风险是这篇文章必须说清楚的边界。`WallpaperExtensionKit` 通过 `dlopen` 加载，XPC 类型通过 `Mirror` 反射访问，Apple 在任何一次大版本更新里重命名字段、调整方法签名、改变快照编码逻辑，都会让 Phosphene 部分或全部功能失效。README 里明确写了"Apple could change this at any major OS release"。

这意味着 Phosphene 的维护成本和 Apple 系统更新节奏绑定。每次 macOS 大版本发布，作者需要重新逆向 `WallpaperExtensionKit` 的变化、验证 Mirror 反射和 swizzle 是否仍然有效。对用户来说，升级 macOS 前应该先确认 Phosphene 是否已适配新版本。

## 适用场景与边界

**适合用的场景：**

- 个人桌面个性化，想用自己的视频做壁纸，且接受私有 API 的不稳定性
- macOS 桌面定制开发者，想研究 `WallpaperExtensionKit` 的逆向工程实践
- 需要锁屏壁纸、多显示器独立壁纸、Space 独立壁纸的系统级集成

**不适合用的场景：**

- 生产环境或商业部署，私有 API 的稳定性无法保证
- Intel Mac 用户，项目只编译 `arm64`
- macOS Tahoe 以下的系统，依赖 Tahoe 专属 SwiftUI API
- 需要 3D/网页/应用类壁纸，Phosphene 只支持视频

## 采用顺序与决策建议

如果决定试用 Phosphene，建议按这个顺序：

1. 确认系统是 macOS Tahoe 26.0+ 且是 Apple Silicon。
2. `git clone https://github.com/kageroumado/phosphene.git` 后用 Xcode 17 打开 `Phosphene.xcodeproj`，设置开发团队做代码签名。
3. 选 Phosphene scheme 运行，从菜单栏导入一个 MP4。
4. 打开系统设置 → 壁纸，确认 Phosphene 视频出现在分类下。
5. 如果只想做无签名编译验证：

```bash
xcodebuild -project Phosphene.xcodeproj -scheme Phosphene -configuration Debug \
 -destination 'generic/platform=macOS' \
 CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY='' build
```

编译产物在 `~/Library/Developer/Xcode/DerivedData/Phosphene-*/Build/Products/Debug/Phosphene.app`。

**决策建议。** 把 Phosphene 放在哪类用途上，决定了你能不能接受它的私有 API 风险。个人桌面美化属于低风险场景——某次 macOS 升级后失效，大不了换回静态壁纸。生产环境或商业部署不要用，私有 API 的稳定性无法保证，且 Apple 可能随时封堵。对桌面定制开发者来说，这份代码的价值不在"能当壁纸用"，而在它是一份完整的 `WallpaperExtensionKit` 逆向工程参考实现——`Mirror` 反射读取私有类型、`NSXPCCoder` swizzle 绕过类型检查、`AVSampleBufferDisplayLayer` 在远程 `CAContext` 里手动推帧，这些手法可以迁移到其他需要接入私有系统框架的场景。

## 常见问题

**Q：升级 macOS 后 Phosphene 失效了怎么办？**

A：先看仓库的 issue 区有没有对应版本的反馈。失效通常出在三个环节：`WallpaperExtensionKit` 的字段被重命名（`Mirror` 反射读不到）、`NSXPCCoder` 的子类结构变化（swizzle 失效）、快照编码逻辑调整（锁屏灰屏）。前两个需要作者更新代码，用户无法自行修复。升级前建议先确认仓库是否已适配新版本。

**Q：为什么我的视频导入后没有出现在系统壁纸列表里？**

A：检查三件事。第一，视频格式是否是 AVFoundation 能读的（MP4/MOV 等常见格式，HEVC 需要硬件解码支持）。第二，扩展是否被系统正确加载——在"系统设置 → 扩展 → 壁纸扩展"里确认 PhospheneExtension 已启用。第三，编译时是否用了正确的代码签名，未签名的扩展不会被系统加载。

**Q：Phosphene 支持 Intel Mac 吗？**

A：不支持。目标三元组是 `arm64-apple-macos26.0`，只编译 Apple Silicon 架构。Intel Mac 用户需要自行修改 target triple 并处理潜在的架构相关问题，但作者没有提供官方支持。

**Q：可以用 Phosphene 播放 GIF 或网页壁纸吗？**

A：不能。Phosphene 只支持 AVFoundation 可读的视频文件。它的渲染管线基于 `AVSampleBufferDisplayLayer` 推视频帧，没有处理 GIF 动画或网页渲染的逻辑。需要这类内容只能考虑其他方案。

**Q：私有 API 会不会导致应用被 App Store 拒审？**

A：会。`WallpaperExtensionKit` 是私有框架，`dlopen` 加载私有框架和 `Mirror` 反射访问私有类型都违反 App Store 审核规则。Phosphene 只能通过自行编译签名使用，无法上架 App Store。这也是作者把它开源而非商业化的原因之一。

## 进阶路径

如果想深入理解 Phosphene 的实现或做二次开发，按以下顺序读代码和扩展。

**第一步：通读系统地图与任务流。** 先读 `Phosphene/` 目录下的菜单栏应用代码，理解视频库管理、`VideoOptimizationService` 转码、App Group 容器写入。再读 `PhospheneExtension/` 下的扩展入口，理解 `dlopen` 加载 `WallpaperExtensionKit` 和 XPC 回调注册。

**第二步：拆解渲染管线。** 重点读 `VideoRenderer` 的实现：`AVAssetReader` 如何分两个实例做当前循环与预加载、PTS 偏移如何随循环累加、`AVSampleBufferDisplayLayer` 如何接收帧。试着在循环边界加日志，观察无缝拼接的实际时间线。

**第三步：理解 PlaybackPolicy 的状态机。** 读 `PlaybackPolicy` 的输入信号收集与状态塌缩逻辑。自测方法：手动改温度、电池、展示模式的输入，观察状态在 `full`/`reduced`/`minimal`/`paused` 之间的迁移路径，验证变体选择是否在策略允许范围内。

**第四步：研究私有 API 逆向手法。** 读 `PhospheneExtension.swift` 里的 `Mirror` 反射和 `NSXPCCoder` swizzle。如果想验证这些手法是否仍适用于未来 macOS 版本，可以在新的 Xcode 里用 `lldb` 打印 `WallpaperCreationRequestXPC` 的字段列表，对比当前代码读取的字段名。

**第五步：扩展内容类型。** 如果想支持 GIF 或实时渲染壁纸，需要替换 `VideoRenderer` 的帧来源——把 `AVAssetReader` 换成 `CGImage` 序列或 `MTKView` 的帧输出，再喂给 `AVSampleBufferDisplayLayer`。注意帧率与 `PlaybackPolicy` 的协同，避免在 `reduced`/`minimal` 状态下仍跑满帧率。

Phosphene 的价值在于它证明了一件事：macOS 视频壁纸的正确解法是接入系统的壁纸提供方机制，而不是在桌面层做窗口 hack。这条路线的代价是依赖私有 API，收益是锁屏、Space、多显示器、电源管理全部由系统接管。对桌面定制开发者来说，这份代码是一份值得读的逆向工程参考实现；对普通用户来说，它是一个能用但需要跟着 macOS 版本走的工具。
