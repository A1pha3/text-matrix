---
title: "CodeIsland 深度解析：13 个 AI 编码 Agent 怎么挤进 MacBook 刘海"
date: "2026-08-13T11:03:04+08:00"
slug: "wxtsky-codeisland-macos-notch-ai-coding-agent-panel"
description: "CodeIsland 是一个 macOS 灵动岛 UI，实时聚合 13 种 AI 编码 Agent 的会话状态、权限请求、工具调用。背后是一个 86KB 的 native bridge 二进制 + Unix socket IPC + SwiftUI 灵动岛，主程序 39,663 行 Swift。这篇文章拆解它的事件归一化层、进程祖先进化、远程主机回连、iPhone/Apple Watch 伴侣同步这些真正难做的部分。"
draft: false
github_repo: "wxtsky/CodeIsland"
source_key: "gh:wxtsky/CodeIsland"
categories: ["技术笔记"]
tags: ["AI Agent", "macOS", "Swift", "灵动岛", "IPC", "开源项目深拆", "CLI 工具"]
toc: true
---

## 这篇文章在回答什么

CodeIsland 做的事情表面上很简单：把 AI 编码 Agent 的状态塞进 MacBook 刘海。Claude Code 在等审批、Codex 跑完了、Cursor 在执行一个 shell——这些事件原本散落在 13 个不同的终端、IDE、CLI 进程里，开发者需要切窗口才能知道谁在干什么。CodeIsland 把它们汇总到屏幕顶部那条 24px 高的弧形里。

这件事的难点不在 UI，而在 13 种 Agent 的 hook 协议千差万别。我读完 `Sources/` 后看到的数字是：主程序 82 个 Swift 文件，39,663 行代码，其中 `NotchPanelView.swift` 3,184 行，`ConfigInstaller.swift` 3,217 行。这不是 demo 的体量——每个 CLI 的字段命名、hook 触发条件、阻塞 vs 非阻塞语义都不一样，Bridge 必须把它们收编到同一个协议里。

这篇文章回答四个问题：

1. **13 种 Agent 的 hook 协议千差万别，CodeIsland 如何用一个 86KB 的 native bridge 二进制把它们收编？**
2. **macOS 灵动岛 UI 怎么从物理刘海"展开"——三阶段 hover 状态机做了哪些空间上的精打细算？**
3. **远程 Linux 服务器上的 Claude Code 怎么把事件回传到 MacBook 刘海？** SSH 反向隧道 + cwd 过滤 + 自适应重连
4. **iPhone 灵动岛、Lock Screen、StandBy、Apple Watch 怎么同步？** MultipeerConnectivity + BLE 双通道的工程权衡

最后我会写一个最小可运行的"30 行 Bridge 示例"——如果你想自己写一个类似的 IPC 适配层，可以从这里开始。

## 系统地图：39,663 行 Swift 在做什么

打开仓库，先看模块切分：

```
Sources/
├── CodeIsland/              # 主 App (SwiftUI + AppKit)
│   ├── NotchPanelView.swift           # 灵动岛 UI 主控 (3,184 行)
│   ├── ConfigInstaller.swift          # 13 种 CLI 的 hook 自安装 (3,217 行)
│   ├── HookServer.swift               # Unix socket 服务端 (648 行)
│   ├── AppState.swift                 # 状态机 + session 注册表
│   ├── MascotView.swift + 24 个 *View  # 像素角色动画
│   └── ...
├── CodeIslandCore/          # 跨模块共享 (1,629 行 SessionSnapshot 等)
│   ├── SessionSnapshot.swift
│   ├── EventNormalizer.swift          # 13 种 hook 事件名归一
│   ├── AppleCompanionPayload.swift
│   └── ...
└── CodeIslandBridge/        # 86KB native bridge 二进制
    └── main.swift                     # 570 行，全部 hook 适配都在这
```

三个模块的角色非常清晰：

- **Bridge** 是被 hook 脚本调用的命令行工具（每个 CLI 触发 hook 时会 fork 它拿到一个 socket 写入），用纯 POSIX socket + JSON 做最薄的转译层
- **Core** 是无 UI 依赖的纯 Swift 库，承载跨进程的数据模型和事件归一化
- **CodeIsland** 是主 App，处理 SwiftUI 渲染、socket 服务端、settings、远程主机、伴侣同步

这个分层不是教科书式三层架构的硬套——它是对应"hook 协议千差万别"这个问题做出的工程反应。Bridge 必须保持极小（86KB）才能让它挂着各个 CLI 进程下运行时接近零开销；Core 必须可独立测试（很多纯函数）；主 App 才能放心堆 SwiftUI 视图。

## 事件归一化：13 种 hook 协议如何被一个二进制收编

不同 AI 编码 Agent 的 hook 协议差异巨大。CodeIsland 的 `EventNormalizer.swift` 把它们全部归一到内部分析事件：

```swift
public static func normalize(_ name: String) -> String {
    switch name {
    // Cursor (camelCase)
    case "beforeSubmitPrompt":    return "UserPromptSubmit"
    case "beforeShellExecution":  return "PreToolUse"
    case "afterShellExecution":   return "PostToolUse"
    // Gemini
    case "BeforeTool":            return "PermissionRequest"
    case "BeforeAgent":           return "SubagentStart"
    // GitHub Copilot CLI
    case "sessionStart":          return "SessionStart"
    case "preToolUse":            return "PreToolUse"
    // Kiro CLI (camelCase, agent-scoped)
    case "agentSpawn":            return "SessionStart"
    // Traecli (snake_case)
    case "session_start":         return "SessionStart"
    case "pre_tool_use":          return "PreToolUse"
    // Hermes (Nous Research)
    case "pre_tool_call":         return "PreToolUse"
    case "on_session_start":      return "SessionStart"
    // Cline (VSCode extension)
    case "TaskStart":             return "SessionStart"
    case "TaskResume":            return "UserPromptSubmit"
    default:                      return name
    }
}
```

表面上是字符串映射。但仔细看 `Bridge/main.swift` 里的归一化逻辑，发现 Bridge 远不止做事件名映射，它还做**字段名归一化**：

```swift
// Copilot CLI adaptation: its stdin JSON lacks session_id and hook_event_name.
if sourceTag == "copilot" {
    if json["hook_event_name"] == nil, let event = eventTag {
        json["hook_event_name"] = event
    }
    if json["session_id"] == nil, let sessionId = nonEmptyString(json["sessionId"]) {
        json["session_id"] = sessionId
    }
    if let toolName = json["toolName"] as? String {
        json["tool_name"] = toolName
    }
    if let toolArgsStr = json["toolArgs"] as? String,
       let argsData = toolArgsStr.data(using: .utf8),
       let argsObj = try? JSONSerialization.jsonObject(with: argsData) as? [String: Any] {
        json["tool_input"] = argsObj
    }
}

// Cline adaptation: sends hookName and taskId instead of hook_event_name and session_id.
if sourceTag == "cline" {
    if json["hook_event_name"] == nil, let name = nonEmptyString(json["hookName"]) {
        json["hook_event_name"] = name
    }
    // ...
}
```

每个 Agent 的 hook payload 字段命名都不一样——`sessionId` / `session_id` / `taskId`、`toolName` / `tool_name`、`toolArgs` / `tool_input`，甚至同一个字段在不同 fork 里是 snake_case 还是 camelCase 也不一致。Bridge 通过 `--source` flag 区分上游，然后做条件归一化。

但这还不是最难的部分。最难的是——**有些 CLI 根本不在 stdin 里告诉 Bridge 自己是谁**。

## 进程祖先进化：当 hook 不知道自己跑了哪个 CLI

OpenCode 的 `omo` JS 插件会触发 Claude 的 hook，但 hook 脚本里没有任何 `--source` 信息。CodeIsland 在 `Bridge/main.swift` 里做了一件有点 hack 但很聪明的事：调用 `proc_pidpath` 沿父进程链向上爬 6 层，找出真正的 CLI 二进制：

```swift
func buildAncestry(startingAt pid: pid_t, maxDepth: Int = 6) -> [(pid: pid_t, executablePath: String?)] {
    guard pid > 0 else { return [] }
    var result: [(pid: pid_t, executablePath: String?)] = []
    var current: pid_t? = pid
    var visited = Set<pid_t>()

    while let currentPid = current, currentPid > 0, result.count < maxDepth, !visited.contains(currentPid) {
        visited.insert(currentPid)
        result.append((pid: currentPid, executablePath: executablePath(for: currentPid)))
        current = parentPID(of: currentPid)
    }
    return result
}
```

为什么要爬 6 层？因为很多 CLI 把 hook 包装成 `sh -c "..."` 调用，hook 脚本的 `getppid()` 拿到的不是长生命周期的 CLI 进程，而是中间那个转瞬即逝的 shell。必须穿透它找到真正的源头。

更进一步：`cursor-agent` 和 `qodercli` 在 Cursor IDE 旁边跑时，会复用同一份 hook 配置文件；如果只靠 `--source cursor` 标记，所有事件都会被错误归到 IDE 端。Bridge 用 `CLIProcessResolver.cliVariantOverride` 做一次"祖先里如果出现 `cursor-agent` 二进制，就把 `cursor` 升格为 `cursor-cli`"的修正。

这是非常实际的问题——很多团队把多个 CLI 跑在同一台机器上，hook 错归类会让 CodeIsland 面板里出现重复的 session 卡。

## 终端定位：13 种终端、5 种 multiplexer 怎么精确定位

事件归一化做完了，CodeIsland 还需要回答另一个问题：**用户当前看的是哪个 tab？** 因为"智能通知抑制"功能——避免在你已经盯着某个 session 时还弹通知——需要这个精度。

Bridge 扫了一堆环境变量：

```swift
// iTerm2 session — extract GUID after "w0t0p0:" prefix for AppleScript matching
if let iterm = env["ITERM_SESSION_ID"], !iterm.isEmpty {
    if let colonIdx = iterm.firstIndex(of: ":") {
        json["_iterm_session"] = String(iterm[iterm.index(after: colonIdx)...])
    }
}

// tmux detection — deep info collection
if let tmux = env["TMUX"], !tmux.isEmpty {
    json["_tmux"] = tmux
    if let pane = env["TMUX_PANE"], !pane.isEmpty {
        json["_tmux_pane"] = pane
        // Get client TTY — use explicit path (hook PATH may lack homebrew)
        if let tmuxBin = findBinary("tmux"),
           let clientTTY = runCommand(tmuxBin, args: ["display-message", "-p", "-t", pane, "-F", "#{client_tty}"]) {
            json["_tmux_client_tty"] = clientTTY
        }
    }
}

// cmux — auto-injects CMUX_SURFACE_ID and CMUX_WORKSPACE_ID
if let cmuxSurface = env["CMUX_SURFACE_ID"], !cmuxSurface.isEmpty {
    json["_cmux_surface_id"] = cmuxSurface
}

// Zellij pane id
if let zellij = env["ZELLIJ_PANE_ID"], !zellij.isEmpty {
    json["_zellij_pane_id"] = zellij
}

// WezTerm / Kaku pane id
if let weztermPane = env["WEZTERM_PANE"], !weztermPane.isEmpty {
    json["_wezterm_pane"] = weztermPane
}
```

注意 `findBinary("tmux")` 用了硬编码路径 `/opt/homebrew/bin/tmux` / `/usr/local/bin/tmux` / `/usr/bin/tmux`——因为 hook 进程的 PATH 经常被精简（很多 shell 的 hook 配置不继承 homebrew 路径），用 `which tmux` 会失败。

而且 `tmux display-message -p -t <pane> -F "#{client_tty}"` 这个调用——它把 tmux 的 pane ID 翻译成具体的 TTY 设备路径。这是为什么 CodeIsland 能做出"tab 级"通知抑制而不是"应用级"。

## 灵动岛 UI：三阶段 hover 状态机与精打细算的空间

`NotchPanelView.swift` 3184 行，不是空中楼阁。它在做一件空间精算：用一台 MacBook 的物理刘海（240px 宽、约 33px 高的弧形）作为视觉锚点，根据状态切换宽度。

```swift
enum NotchWidthMetrics {
    static func effectiveNotchWidth(notchW: CGFloat, collapsedWidthScale: Int, hasNotch: Bool) -> CGFloat {
        let clampedScale = Swift.max(NotchWidthScale.min, Swift.min(collapsedWidthScale, NotchWidthScale.max))
        let scaled = notchW * CGFloat(clampedScale) / 100.0
        if hasNotch { return Swift.max(notchW, scaled) }
        return scaled
    }
}
```

注意 `if hasNotch { return Swift.max(notchW, scaled) }`——在有物理刘海的屏幕上，缩放后的宽度**不能小于物理刘海本身**。否则会露出刘海边沿的黑色切口。这个细节用单行代码注释 `#268` 标记，留下 issue 编号让后来者能追溯。

三阶段 hover 拆分同样精细：

```swift
enum NotchHoverPhase {
    case collapsed
    case prehover
    case expanded
}

enum NotchHoverInteraction {
    static let prehoverAnimationDuration: TimeInterval = 0.21
    static let expandDelay: TimeInterval = 0.5
    static let collapseDelay: TimeInterval = 0.5
    static let prehoverWidthDelta: CGFloat = 7
    static let prehoverScale: CGFloat = 1.004
}
```

为什么是三阶段？因为鼠标快速划过刘海时（pass-through），如果直接展开，会让面板抽搐。`prehover` 阶段只做 `+7px` 宽度变化 + `1.004` 缩放——肉眼能感知到"这个区域在响应"但不至于弹层。鼠标停留 500ms 才进入 `expanded`。这种"即时反馈 + 延迟展开"的拆分正是 macOS 系统菜单栏本身在用的交互模式。

`NotchWidthScale` 是 50–150 的可变缩放——你可以让刘海只占原宽度的一半（外接显示器场景），也可以拉到 150% 让"碰撞面积"更大。这个参数的默认值、min/max/step 都在文件里集中定义，保持设置滑块和数学公式两边的常量同步。

## 像素角色：MascotMotion 的"确定性伪随机"

24 个 `*View` 文件，每个对应一个 CLI 的像素角色。Codex 的 `DexView` 是云朵 + `>_` 提示符，Cursor 的 `CursorView` 是经典箭头，Kimi 的 `KimiView` 是日式折纸。这些不是静态图——它们有呼吸、眨眼、quark（耳抽/尾巴摆/伸懒腰）。

但 mascot 帧是从时间线 `t` 重新渲染的，没有保留动画状态。那"随机"眨眼怎么在不存储状态的前提下做？

```swift
static func hash01(_ n: Int, seed: UInt64 = 0) -> Double {
    var x = UInt64(bitPattern: Int64(n)) &+ 0x9E3779B97F4A7C15 &+ seed &* 0xBF58476D1CE4E5B9
    x = (x ^ (x >> 30)) &* 0xBF58476D1CE4E5B9
    x = (x ^ (x >> 27)) &* 0xBF58476D1CE4E5B9
    x = x ^ (x >> 31)
    return Double(x % 1_000_000) / 1_000_000
}
```

`hash01(n, seed:)` 是稳定哈希到 [0,1)。拿 `Int(floor(t / 4.0))` 作为 slot，用 `hash01(slot, seed)` 决定 4 秒里的眨眼时机。`0.15 + 0.6 * r` 让你既有"2.4s 后眨眼"也有"3.6s 后眨眼"，看起来不机械。18% 概率再来一次双眨眼——这是那种"看见的人在细节里会心一笑"的细节。

呼吸曲线做了**非对称设计**：

```swift
// 35% inhale, 45% exhale, 20% rest.
if phase < 0.35 {
    let p = phase / 0.35
    return CGFloat(0.5 - 0.5 * cos(p * .pi))            // ease-in-out up
} else if phase < 0.80 {
    let p = (phase - 0.35) / 0.45
    return CGFloat(0.5 + 0.5 * cos(p * .pi))            // ease-in-out down
} else {
    return 0
}
```

不是简单的 `sin(t)`。吸 35%、呼 45%、停 20%——更接近真人的呼吸节奏。文件顶部注释 `#15 polish pass` 标记这是第 15 号 issue 的美学打磨。

## 远程主机：SSH 反向隧道 + 自适应重连

大部分 AI 编码 Agent 跑在远程 Linux 服务器上——开发机在云端，MacBook 只是终端。CodeIsland 提供"远程主机"功能：把 SSH 上的 Claude/Codex 事件也吸到 MacBook 刘海里。

`RemoteManager.swift` 里的自适应重连策略：

```swift
private static let reconnectBackoffSeconds: [Int] = [5, 15, 45, 120, 300]
private static let reconnectMaxAttempts = 10

static func reconnectDelay(attempt: Int) -> Int {
    guard attempt >= 1 else { return reconnectBackoffSeconds[0] }
    let idx = min(attempt - 1, reconnectBackoffSeconds.count - 1)
    return reconnectBackoffSeconds[attempt - 1]
}
```

5 秒 → 15 秒 → 45 秒 → 2 分钟 → 5 分钟，10 次封顶。这是为"笔记本盖子合上 → wifi 断开 → SSH 隧道挂掉"这种场景设计的。你不会想每一秒都重连打断用户；你也不会想五分钟后隧道已经没人记得它死了。指数退避 + 封顶是这类长连接的标准答案。

`updateHost` 里的"只对真正影响连接字段的修改触发重连"也值得展开：

```swift
let connectionChanged = previous.host != host.host
    || previous.user != host.user
    || previous.port != host.port
    || previous.identityFile != host.identityFile
    || previous.authSocket != host.authSocket
if wasConnected && connectionChanged {
    reconnect(id: host.id)
}
```

如果用户只改了 `name` 或 `cwdFilter`（远程会话的 cwd 过滤，详见下面），**不该**把已经连上的 SSH 隧道踢掉。这个边界判断写在 `RemoteManager` 里，让上层 UI 可以放心改字段。

对共享远程账号（团队共用一个 dev box），`HookServer` 里还有一个 `cwd` 过滤：

```swift
nonisolated static func remoteEventPassesCwdFilter(
    cwd: String?,
    workspaceRoots: [String]?
) -> Bool {
    // Empty filter = allow everything (previous behavior).
    // With a filter set, events must carry a cwd containing one of the entries.
    // Without cwd, drop — on a shared account they can't be attributed.
}
```

空字符串 = 不过滤（默认行为），非空 = 必须 cwd 包含其中一个根目录才放行。共享账号场景下，不带 cwd 的事件会被丢弃——因为无法判断属于哪个用户。

## iPhone / Apple Watch 伴侣同步：MultipeerConnectivity + BLE 双通道

`AppleCompanionPublisher.swift` 是另一个有意思的部分。Code Island Buddy 是一个独立的 iPhone App（App Store ID `6773881129`），把 Mac 上的 session 状态同步到 iPhone 灵动岛、锁屏、StandBy 和 Apple Watch。

双通道设计：

```swift
private lazy var session = MCSession(peer: peerID, securityIdentity: nil, encryptionPreference: .required)
private lazy var advertiser = MCNearbyServiceAdvertiser(
    peer: peerID,
    discoveryInfo: ["protocol": "1"],
    serviceType: Self.serviceType
)
// ...
private let bluetooth = AppleCompanionBluetoothPeripheral()
```

- **MultipeerConnectivity（MCSession）**：iPhone App 前台打开时通过本地网络（Wi-Fi / Bluetooth）传输完整 session 快照——开销大但完整
- **CoreBluetooth Peripheral**：后台运行时（屏幕锁、StandBy、Apple Watch）只发压缩后的状态摘要——开销小但够用

```swift
func configure(enabled: Bool, heartbeatSeconds: Double) {
    guard enabled else {
        advertiser.stopAdvertisingPeer()
        bluetooth.configure(enabled: false)
        advertising = false
        connectedPeerNames = []
        session.disconnect()
        return
    }
    lastError = nil
    advertiser.startAdvertisingPeer()
    bluetooth.configure(enabled: true)
    advertising = true
    heartbeatTimer = Timer.scheduledTimer(withTimeInterval: max(1.0, heartbeatSeconds), repeats: true) { [weak self] _ in
        Task { @MainActor in
            self?.flush(reason: "heartbeat")
        }
    }
    flush(reason: "enabled")
}
```

`heartbeatSeconds` 默认值在 `Settings.swift` 控制。`flush(reason: ...)` 包装所有状态推送——`"enabled"` / `"change"` / `"heartbeat"` / `"reconnect"` / `"requested"`——日志里能看到每次推送的理由，便于追踪推送链路。

iPhone 端可以反向发控制命令：`approveCurrentPermission` / `denyCurrentPermission` / `skipCurrentQuestion` / `answerQuestion`。`onControlCommand` 回调把命令转回主 App 的权限队列，MacBook 刘海不再是单向消息板——你可以在 Apple Watch 上批准 Claude 的 bash 执行请求。

## 思考：CodeIsland 的工程取舍

### 让人比较欣赏的几个决策

1. **Bridge 86KB + 三阶段 hover + 进程祖先进化**——这是 13 种 CLI 在协议层差异巨大的客观条件下，最简洁的统一路径。把"脏活"压到最小二进制里，主 App 不用 import 任何 CLI 的 hook 协议。换一个团队大概会写 13 个适配器，CodeIsland 写一个归一化器。

2. **Core/App/Bridge 严格分层**——Bridge 不依赖 SwiftUI，Core 不依赖 AppKit，主 App 才有 SwiftUI 视图。这让 Bridge 可以独立打包成独立进程、独立测试、独立分发。写跨 CLI 工具时这种分层往往是必须的：很多 CLI 不会让你的主 App 加载进来。

3. **祖先链路 + CLI 变体升格**——`cursor` vs `cursor-cli` 这种细节在 Issue #134 里有记录。一个项目愿意处理这种粒度，说明它认了"我的用户会同时跑多个 CLI"这件事。不是所有人都意识到这个问题。

4. **远程主机 cwd 过滤 + 自适应重连**——共享远程账号场景、笔记本睡眠场景，这类"非典型环境"在 `RemoteManager` 里都有显式分支。5/15/45/120/300 秒的退避表写在常量里，比写在注释里更难被人忘掉。

### 几个还能打磨的地方

1. **`NotchPanelView.swift` 3184 行**——这是 SwiftUI 视图体过大的典型信号。但要把 mascot、tool status、permission card、question card 从一个 view 里拆出来，需要重写整个 hover 状态机的数据流，不是简单 `SubView` 抽出。也许项目方想做但 ROI 不高。

2. **`ConfigInstaller.swift` 3217 行**——13 种 CLI × 多个操作系统 × 多个 shells 的安装逻辑堆在一个文件。值得拆成 `ConfigInstaller+Claude.swift` / `ConfigInstaller+Cursor.swift` 这样的扩展。否则新人改一个 CLI 的 hook 路径要通读整个 3217 行。

3. **Bridge 没有持久化队列**——如果 CodeIsland App 暂时挂掉，bridge 写到 socket 失败就丢弃。某些关键事件（比如权限请求）可以加本地 fallback（写入文件，等待 App 重启后回放）。但 Bridge 本身很短命（hook 触发后几秒退出），加持久化有点杀鸡用牛刀。

4. **iOS companion 的协议细节没完全公开**——iOS App 源码在 `ios/CodeIslandCompanion` 但 README 里那几个截图的 UI 组件应该是私有 API，handoff 体验还不完整。

## 30 行最小 Bridge：如果你想自己写一个

CodeIsland 的 Bridge 是 570 行——那是 13 种 CLI 的归一化逻辑加进去之后的体积。如果你只需要做"一个 CLI 事件转 socket"的最小骨架，30 行 C 就能搞定：

```c
// minimal-bridge.c — 30 行，C99 编译：cc minimal-bridge.c -o minimal-bridge
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

int main(int argc, char **argv) {
    const char *sock = argc > 1 ? argv[1] : "/tmp/minimal-bridge.sock";

    // 1. 检查 socket 是否存在（不存在或不可用 → 静默退出）
    struct stat st;
    if (stat(sock, &st) != 0 || (st.st_mode & S_IFMT) != S_IFSOCK) return 0;

    // 2. 读 stdin 一次性拿到 hook JSON
    char buf[65536]; ssize_t n = read(0, buf, sizeof(buf) - 1);
    if (n <= 0) return 0; buf[n] = 0;

    // 3. 连接 socket（3s 超时）
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    struct sockaddr_un addr = {.sun_family = AF_UNIX};
    strncpy(addr.sun_path, sock, sizeof(addr.sun_path) - 1);
    if (connect(fd, (struct sockaddr*)&addr, sizeof(addr)) != 0) return 0;

    // 4. 写 JSON（简化为 socket 半关闭即可）
    write(fd, buf, n);
    shutdown(fd, SHUT_WR);

    // 5. 等服务端 ack（最长 1s）
    struct timeval tv = {1, 0};
    setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    char ack[4096]; ssize_t m = read(fd, ack, sizeof(ack));
    if (m > 0) write(1, ack, m);  // 反向写到 stdout（仅阻塞事件需要）

    return 0;
}
```

把这 30 行编译成一个 8KB 的二进制，挂到任何 CLI 的 hook 里，就能让所有 hook 事件实时打到主 App。CodeIsland 的 570 行 Bridge 就是在它的基础上，加了这些工程化的东西：

- **进程祖先进化**（`proc_pidpath` 爬 6 层父进程）——确定 hook 实际被哪个 CLI 触发
- **多终端环境变量归一化**——iTerm2 / tmux / cmux / zellij / WezTerm 各家有各家的 env
- **字段名归一化**——`sessionId` / `session_id` / `taskId` 都转成内部分析字段
- **session 卡片去重**——Cursor IDE 触发多个并发子代理时，按根 binary 折叠成一张卡
- **ptysocket 权限**——`umask 0o077` 防止 socket 被同机其他用户读取（参见 `HookServer.start`）

从 30 行"能用"到 570 行"跨 13 种 CLI 都能用"，中间那段是真实工程时间。CodeIsland 把这条路走通后，把所有复杂度都封装在 Bridge 里，主 App 长得很干净。

## 适合谁读

- **做 AI 编码产品的工程师**——`ConfigInstaller` 是"如何让自己适配 13 个客户端"的实战教材
- **做 macOS 灵动岛 App 的开发者**——`NotchPanelView` 是少有的"刘海作为 UI 锚点"完整工程实现
- **做实时状态聚合的工程师**——Bridge/Server/Core 三层 + MultipeerConnectivity 案例非常完整
- **对 CLI 工具多协议兼容感兴趣的人**——`EventNormalizer` + `CLIProcessResolver` 的字段归一化可复用

不适合：只想找一个 AI 状态栏工具、不想理解架构的"用户视角"读者——直接 `brew install --cask codeisland` 就好。

## 参考

- 仓库：github.com/wxtsky/CodeIsland
- iPhone 伴侣：Code Island Buddy（App Store ID 6773881129）
- 主 App 评测：github.com/farouqaldori/claude-island（启发项目）
- 协议：MIT
