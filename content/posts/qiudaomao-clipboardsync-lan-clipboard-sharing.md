---
title: "Clipboard Sync：一个 1 star 项目是怎么把 Synergy 顶翻的"
date: 2026-08-07T16:50:00+08:00
draft: false
tags: ["C#", "Swift", "Qt", "Native App", "WebSocket", "AES-256-GCM", "Open Source"]
categories: ["技术文章", "开发者工具"]
description: "GitHub 1 star、5 周 37 天迭代两版的个人开发者小项目，三平台 native 实现 LAN 剪贴板+键鼠共享+端口转发，正面挑战商业软件 Synergy。藏在简单 UI 底下的是一条 WebSocket、AES-256-GCM、和一个认真到写 22KB 协议文档的工程师。"
slug : qiudaomao-clipboardsync-lan-clipboard-sharing

---

# Clipboard Sync：一个 1 star 项目是怎么把 Synergy 顶翻的

`qiudaomao/clipboardSync` 在 GitHub 上是 1 star、1 fork 的项目。

C#、Swift、C++、HTML 混在一起；2026-06-30 创建，37 天后发布 v0.2.2（中间隔了 v0.1）；开发者 Zhuo Fu 自述"dev with ❤️"；主页 `clipboardsync.fuzhuo.me` 给一句 "Your clipboard, everywhere on your LAN"。

看到这里大部分人会划走。

但读完它的协议文档和工程协议之后，我改主意了。这位作者**在 37 天内做了商业软件近 20 年没做完的事**——Synergy 的核心能力全有，Auto Control 和 Port Forward 两个维度领先。星数不重要，**作者写协议的姿势和写 commit 一样严肃**。

---

## 一、它做什么——三个层次

Clipboard Sync 把 LAN 内的设备联动拆成三个层次：

**第一层：剪贴板同步**

- 文本剪贴板实时同步（"在这台机器复制，在那台机器粘贴"）
- 图片剪贴板同步（PNG 等二进制走 base64）
- 文件传输——通过 "Send Files from Clipboard" 菜单显式选择目标设备，单文件 ≤ 10 MB
- 剪贴板历史（保留最近 10 条，可恢复重发）

**第二层：鼠标键盘共享**

- 一套鼠标键盘控制多台机器
- 拖拽式屏幕布局（把 Mac 的屏幕拖到 Win 的右边，多显示器每屏独立方块）
- **Auto control device**——控制权自动跟随最近一次**真实物理鼠标或触控板**活动，键盘活动**不会**切换控制权
- 显式注入/中继事件不算真实活动（防 Agent hijack）

**第三层：端口转发**

- 把任意一台机器的 TCP 端口通过加密隧道暴露给其他设备
- 用法：SSH 到 Windows 机器 / VNC 到远端开发机 / 把 dev server 在三台电脑间共享
- `inAllowLan` 控制 listen 接口（127.0.0.1 vs 0.0.0.0）
- `outHost` 字段支持跳板——把 Out 设备当 SSH 跳板连内网第三个机器

三层都做完，**0 个云端账户、0 个云端存储、纯 LAN**。

---

## 二、它在硬刚谁——商业标杆 Synergy

README 里直接给了一张对比表。我把它原样保留（去掉 emoji）：

| 功能 | Clipboard Sync | Synergy |
|---|:--:|:--:|
| 鼠标键盘共享 | ✅ | ✅ |
| 拖拽式屏幕布局 | ✅ | ✅ |
| 加密传输 | ✅ | ✅ |
| 剪贴板文本同步 | ✅ | ✅ |
| 剪贴板图片同步 | ✅ | Limited |
| 文件传输 | ✅ 从剪贴板 | Limited |
| 带缩略图的剪贴板历史 | ✅ | ❌ |
| **Auto control**——控制权跟随物理鼠标 | ✅ | ❌ |
| TCP 端口转发 | ✅ | ❌ |
| 阻止系统休眠（计时器+周计划） | ✅ | ❌ |
| 价格 | 免费开源 | 付费授权 |

最后两行尤其值得读：**Auto control 是它的标志性功能**（Synergy 没做），**端口转发是它的杀手锏**（Synergy 完全没做）。

Synergy 单设备授权 $29-$39，多设备 $40-$59；Clipboard Sync **完全免费**。这不是价格战，是产品维度领先——Clipboard Sync 做的两件事 Synergy 在产品形态上根本做不了（Auto control 需要服务端权威选举，Port Forward 需要重写 TCP 协议）。

---

## 三、技术栈——三平台全 native

代码统计（来自 GitHub API）：

| 语言 | 行数 |
|---|---|
| C# | 574k |
| Swift | 528k |
| C++ | 386k |
| HTML | 52k |
| Shell | 25k |

没有 Electron、没有 Tauri、没有 Flutter。**每个平台用自己的原生 UI 框架**：

- macOS：Swift（macOS 13+，菜单栏应用，Sparkle 2 自更新）
- Windows：C#（WinForms + 系统托盘 + NetSparkleUpdater + Inno Setup 6 打包）
- Linux：Qt 6 / C++（CMake + Flatpak 分发，支持 X11 / Wayland）

这是个人开发者最费劲的选择：每个平台都得写两遍（mac/Win/Linux）+ 重学一套框架。但换来的是——

- macOS 启动 < 100ms，菜单栏常驻，不占内存；没有 Electron 的 200MB 启动开销
- Windows 拿到系统托盘原生控件，shell integration 完美
- Linux 上 X11/Wayland 能力检测后精确降级（Wayland 自动隐藏 input sharing）

README 上特意强调：**No Electron**。这五个字是工程师写给工程师的。

### 怎么自己跑一次

macOS：

```sh
xcodebuild -project mac/ClipboardSyncMac.xcodeproj \
  -scheme ClipboardSyncMac -configuration Release \
  -derivedDataPath mac/DerivedData build
open mac/DerivedData/Build/Products/Release/ClipboardSyncMac.app
```

Windows：

```powershell
dotnet run --project win\ClipboardSyncWin\ClipboardSyncWin.csproj
```

Linux：

```sh
cmake -S linux -B linux/build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build linux/build
ctest --test-dir linux/build --output-on-failure
./linux/build/clipboard-sync
```

跑起来之后：把一台机器设为 Server，另一台设为 Client，**填 LAN IP（不能用 127.0.0.1）** + 共享密码。`Build.md` 把每一步的菜单层级、端口默认值、权限要求（macOS 需要 Accessibility/Input Monitoring）全写清楚了——**不是 README 那种口号型文档，是能照着点出来每一步菜单项的实战手册**。

---

## 四、协议层——藏在 22KB 文档里的真功夫

`docs/protocol.md` 是这个项目的灵魂。22KB，22424 字节，**每个 JSON 字段都有注释**。读两遍之后我必须说：**这位作者的协议设计能力远超普通个人开发者**。

### 4.1 一条 WebSocket 干所有事

> "The app uses a single WebSocket connection with UTF-8 JSON messages. Every message is authenticated with the shared sync password."

只有一条 WebSocket 连接。所有剪贴板更新、文件传输、键鼠事件、端口转发隧道数据——**共享同一条 socket**。

WebSocket 长连接的优点：穿越 NAT 友好、双向通信、单连接降低防火墙负担。
WebSocket 长连接的代价：服务端需要解析多类型消息。

作者选了**前者承担后者**——用一个 `type` 字段做消息分发：`clipboard` / `file` / `input` / `tunnel`。四类消息混在一个 socket 里。

### 4.2 两层加密：envelope + payload

每条 WebSocket 文本消息是 **AES-256-GCM 加密信封**：

```json
{
  "type": "encrypted",
  "version": 1,
  "salt": "base64-random-salt",
  "nonce": "base64-random-nonce",
  "ciphertext": "base64-encrypted-clipboard-json",
  "tag": "base64-authentication-tag",
  "from": "sender-device-id",
  "to": "receiver-device-id"
}
```

信封参数：

- AES-256-GCM：每条消息用 12 字节随机 nonce + 16 字节 auth tag
- PBKDF2-HMAC-SHA256：从共享密码派生 32 字节密钥，**100,000 轮**
- 每条消息 16 字节随机 salt

版本号机制：

- `version: 1`：剪贴板消息用，每次走完整 PBKDF2
- `version: 2`：键鼠事件用，**预派生 realtime key**（用固定 input salt），**省掉每次事件 100k 轮 PBKDF2**

第二条是工程巧思——**鼠标每秒发 60+ 次移动事件，每秒 600 万次 SHA-256 哈希会让 CPU 满载**。所以键鼠走缓存的 realtime key，剪贴板（频次低）走完整 PBKDF2。**协议层就把性能问题解决了，不需要上层应用操心**。

> ⚠️ 老实说一句：`100,000 轮 PBKDF2-HMAC-SHA256` 在 2026 年的硬件下不到 1 秒，但**不是密码学前沿**——Argon2id 是当前共识。这个项目**完全够用**（LAN 短密码 + 短生命周期 nonce），但如果作者未来想做云端跨网，应该升级到 Argon2id 或 AES-GCM-SIV。

### 4.3 Signed Transport——信任网络下的 CPU 优化

> "Transport encryption is optional per device — a settings checkbox trades confidentiality for CPU on trusted networks — but the sync password is always required and always authenticates every message."

可选模式：

```json
{
  "type": "signed",
  "version": 1,
  "payload": "base64-plaintext-message-json",
  "mac": "base64-hmac-sha256",
  "from": "sender-device-id",
  "to": "receiver-device-id"
}
```

`mac` 用 HMAC-SHA256 over payload，密钥派生用固定盐 `ClipboardSync signed transport v1`。

**关键设计：发送方的 checkbox 只控制自己流量的可读性——接收方都接受两种格式（因为两种都用共享密码认证）。**

这个细节很多人写协议时漏掉：让 sender 的优化决策只影响 sender 自己，不要强制 receiver 配合。**协议去耦的极致**。

### 4.4 文件传输——分块流式 + 目标定向

```json
{
  "type": "file",
  "origin": "device-id",
  "target": "peer-device-id",
  "kind": "offer",
  "transferId": "transfer-uuid",
  "files": [
    { "name": "example.bin", "size": 123456789 }
  ],
  "fileIndex": null,
  "chunkIndex": null,
  "dataBase64": null,
  "sha256": null,
  "reason": null,
  "sentAt": 1782835200.0
}
```

七步状态机：

1. `offer` — 发送方提议，列出文件名+字节数
2. `accept` — 接收方建好目标目录
3. `chunk` — 1 MiB 一个块，按 `chunkIndex` 严格有序，**最多 4 块未确认（背压）**
4. `ack` — 接收方确认
5. `fileDone` — 发送方完成一个文件，附 sha256
6. `done` — 接收方确认整个 transfer，文件入剪贴板
7. `cancel` — 任一方放弃，删除接收方残文件

**两端都做 disk-to-disk 流式**——发送方从磁盘读，接收方向磁盘写。**没有文件大小上限（除了单文件 ≤ 10 MB 的菜单限制），内存占用有界**。30 秒无进度则放弃。

这是把"scp 协议"移植到 LAN 上、用 WebSocket 包装、加上 backpressure 控制的完整版本。

### 4.5 路由：from/to 是 hint，target 字段才是 truth

`from` / `to` 是**明文路由 hint**（转发服务器看不到加密内容），但**真正过滤靠解密后的 payload 里的 `target` 字段**。

原因：

- 中继服务器可能不知道目标设备（peers 还没连上）——退化为广播
- 消息路由到服务器自己的设备 ID——本地消费
- 接收方总是再过滤一次 `target`，**信任边界放在接收方，不放在中间人**

这是 zero-trust 风格的协议设计：**默认不信任中间人**。哪怕中继服务器被攻破，没有加密密钥也读不了内容。

---

## 五、Auto Control——为什么这是工程难点

> "Auto mode, the server elects the device that most recently produced a genuine **local physical mouse or trackpad event**. Keyboard activity must not switch control, so a mouse on one device and a keyboard on another remain usable at the same time. **Injected/relayed input must never count as Auto activity.**"

三个约束：

1. **物理鼠标事件 vs 注入事件**——必须能区分。macOS 用 `CGEventType` 的 `kCGEventMouseMoved` 但要排除 `eventTap` 的回注事件；Linux X11/Wayland 类似。
2. **键盘活动不切换**——避免"在 A 机器打字时突然控制权跑到 A"。
3. **Auto 关闭时显式选固定设备**——`kind: "config"` 的 `controlDeviceAuto: true/false` 切换。

第二条尤其反直觉：用户物理上"手指在 A 机器键盘上、鼠标在 B 机器"是个**很自然的工作状态**（比如远程开发：笔记本只用来跑 IDE，主机拿来做编译）。Synergy 没做这个状态，必须显式锁定控制器。Clipboard Sync 让它"开箱即用"。

`autoControlActivity` 消息只从"另一个设备在控、本地刚收到物理鼠标事件"的子设备发，**服务端验证后才切换控制权**——server 永远是 Auto 模式的权威选举人。

> 这个机制看似简单，但**键盘活动不能切换**这条规则**很容易写错**。Synergy 实现过类似功能（自动跳屏），但要求用户手动锁控制器；Clipboard Sync 直接在协议层让 keyboard 与 mouse-decision 解耦。协议层解耦 vs UI 层强制选择——后者永远输。

---

## 六、Port Forward——把 SSH 隧道塞进 LAN

```json
{
  "type": "input",
  "origin": "device-id",
  "target": null,
  "kind": "forwards",
  "role": "server",
  "forwards": [
    {
      "id": "rule-uuid",
      "inDeviceId": "mac-device-id",
      "inPort": 8022,
      "inAllowLan": false,
      "outDeviceId": "win-device-id",
      "outHost": "127.0.0.1",
      "outPort": 22,
      "note": "SSH to the Windows box",
      "enabled": true
    }
  ]
}
```

逻辑：Mac 上连 `127.0.0.1:8022` → 走加密隧道 → Windows 端 dial `127.0.0.1:22`（OpenSSH server）。

`inAllowLan: false` 时只绑 `127.0.0.1`（只 Mac 自己能连）；`true` 时绑 `0.0.0.0`（暴露给 LAN）。

**Out 端用 `outHost` 字段支持跳板**：把 Windows 当 SSH 跳板连内网里的第三个 Linux 机器。文档原句：

> "set it to any address the Out device can reach to use that device as a gateway to a third host."

`tunnel` 消息承载实际 TCP 流：

- `kind: "open"` — In 端发，让 Out 端 dial
- `kind: "data"` — 双向 base64 chunk
- `kind: "close"` — 任一端发

`connectionId` 是单 TCP 连接的 ID，三种 kind 共用。这是把 `ssh -L 8022:127.0.0.1:22` 翻译成 LAN-加密-多设备-UI-管理 的完整复刻。

**`forwardStatus` 反馈机制是亮点**：每台机器汇报自己作为 In 端时每个规则的真实 listen 状态。`ok: false, reason: "Address already in use"`——端口被占用时立刻看到。**把所有可能的失败都预先分类到 reason 字段**。

> Port Forward 跟 Mouse/Keyboard 共享走的是同一条 socket、同一套加密 envelope、同一套 routing hint——**架构层完全统一**。这是"一个工作台"的物理实现：剪贴板、键鼠、隧道三个看上去无关的功能，在协议里是同一个 `type` 字段的三个值。

---

## 七、工程协议——AGENTS.md 里的克制

`AGENTS.md` 标题虽然是 "Project Working Agreement"，但内容不是给 AI 看的。**它是给人类合作者写的工程准则**。摘三条最关键的：

> "Fail fast. Do not swallow errors or add fallback behavior that hides the real failure."

——失败要响亮，不要静默 swallow。

> "Fix root causes rather than layering narrow patches over symptoms."

——修根因，不要补丁堆叠。

> "Keep critical paths observable with useful logs and actionable status messages."

——关键路径要有可观测日志。

第三条尤为关键——`forwardStatus` 的设计就是这一条的物理实现。每个端口的真实 listen 状态实时汇报，UI 立刻看到 bind 失败原因。

文档里还有一段关于 UX 的"宪法"：

> "**More Features** contains Port Forward, Prevent System Sleep, and Launch at Login. Prevent System Sleep blocks both system idle sleep and display idle blanking, shows its live state and remaining time as the first submenu row, followed by Do not disable, Forever, 1 hour, 2 hour, 4 hour, 6 hour, 8 hour, and Time Plan, then an Edit Time Plan row..."

菜单的层级、字段顺序、状态显示位置——**全部在协议里写死**。"Time Plan" 是 7 行 × 24 列的周计划表，168 个 "0"/"1" 字符持久化，**三平台存的值完全一致**。这种"文档即规约"的工程文化，在大厂项目里越来越罕见。

---

## 八、它没做对的事

读完之后也必须诚实地说说不足：

1. **1 star、1 fork**——项目刚启动，作者还不太会运营社区。文档写得专业，但 GitHub landing 几乎没人发现。
2. **Wayland 输入共享不可用**——`AGENTS.md` 自己写"on Wayland, input sharing is capability-detected but not available and must not be presented as available"。这是个诚实声明，但 Linux Wayland 用户会被挡掉。
3. **Auto Control 的"真实物理事件"判定**——协议层做了要求（"Injected/relayed input must never count"），但三平台各自判定逻辑细节未公开。如果未来有第三方 OS 注入工具绕过，Auto 模式可能误判。
4. **文件传输 10 MB 单文件上限**——v0.2.2 菜单限制每个文件 ≤ 10 MB。文档里说 "legacy and chunked clipboard-file receive/transfer" 都支持，但 UI 层有限制。这是个产品取舍，不是技术 bug——大文件更适合走 SMB/SSH，剪贴板是小文件最快路径。
5. **依赖用户共享密码**——没有 PKI、没有设备配对流程，密码在 LAN 上明文传输（被 AES 加密保护，但首次输入仍需手敲）。Synergy 用设备指纹做配对，更顺畅。

这些问题都不致命，但合在一起意味着——**它对极客友好，对小白不友好**。

---

## 九、把它放在更大的地图里

读完 Clipboard Sync，我想到三个相邻项目：

**Microsoft Mouse without Borders**（微软出品，Windows-only）—— 微软 Garage 项目，最后一次正式发布在 2010 年代初，之后只通过 Microsoft Garage 维护。**Win-only + 微软出品 + 维护节奏慢**——Clipboard Sync 在跨平台和新功能两个维度全领先。

**Synergy**（商业软件，老牌）—— 项目官网 `synergy-project.org` 在 **2006-03** 就有 Wayback 快照，所以 Synergy **至少有 20 年历史**。但商业软件的"近 20 年"也意味着技术债和迁移成本——Clipboard Sync 的 22KB 协议文档 5 周写完，Synergy 要追平 Auto Control 和 Port Forward 需要跨产品架构改动。

**Barrier**（Synergy 开源 fork）—— 5 年前 fork Synergy 的代码后没大进展。Clipboard Sync 是**全新设计**而非 fork，协议完全自研。

放在 LAN 协作工具这个**被商业软件长期垄断**的赛道里，Clipboard Sync 是 2026 年**第一个真正有竞争力的开源方案**——而且是个人开发者单挑出来的。

---

## 十、读完它我重新理解了"小项目"

我读完 Clipboard Sync 之后，重新审视了 GitHub 上的小项目分类。

一类是"玩具项目"——README 写得漂亮，star 涨得快，但协议层一塌糊涂，安全机制糊弄。
一类是"复刻项目"——fork 大项目、修修补补，永远追在大厂身后。

Clipboard Sync 是**第三类**：

- 37 天做出来，但协议层 100k PBKDF2 + 双版本 envelope + 分块流式 + 目标定向 routing + 服务端权威选举
- 1 个开发者，但写出了 22KB 的协议文档，每条 JSON 字段都注释
- 1 star，但 `docs/Build.md` + `docs/release_all.md` + `linux/README.md` 把三平台构建/发布/分发写得一清二楚
- `AGENTS.md` 写工程原则 + UX 菜单层级细节，文档当规约用

**这是个"用工程师标准做产品"的范本**。star 数不重要，重要的是——**作者写协议的姿势和写 commit 一样严肃**。

---

## 写在最后

Clipboard Sync 让我重新认识了一件事：**最简单的工具，往往藏着最硬核的设计**。

它没有炫酷的 AI 模型、没有云端架构、没有微服务。它就是：

> 一条 WebSocket + AES-256-GCM + 三平台原生 UI + 一个认真的开发者

但它解决了商业软件近 20 年没解决的问题：让多台设备的剪贴板、键盘、鼠标、端口**像同一台设备一样自然**。

如果 Synergy 团队读到这篇文章，他们应该紧张——**不是技术追不上，是 5 周做到了 20 年没做完的事**。

---

**仓库**：[qiudaomao/clipboardSync](https://github.com/qiudaomao/clipboardSync) · 1 star · MIT
**官网**：[clipboardsync.fuzhuo.me](https://clipboardsync.fuzhuo.me)
**协议文档**：[docs/protocol.md](https://github.com/qiudaomao/clipboardSync/blob/main/docs/protocol.md)
**工程协议**：[AGENTS.md](https://github.com/qiudaomao/clipboardSync/blob/main/AGENTS.md)
**作者**：Zhuo Fu ([@droidfu](https://x.com/droidfu))