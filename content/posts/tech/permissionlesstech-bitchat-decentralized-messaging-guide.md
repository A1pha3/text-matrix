---
title: "BitChat：蓝牙 mesh + Nostr 双传输层，让消息在没有信号时也能离开本地"
date: "2026-07-31T02:53:07+08:00"
slug: "permissionlesstech-bitchat-decentralized-messaging-guide"
github_repo: "permissionlesstech/bitchat"
aliases:
  - "/posts/tech/permissionlesstech-bitchat-decentralized-messaging-guide/"
description: "BitChat 用蓝牙 mesh 做离线本地组网，用 Nostr relay 做全球可达，两层之间靠智能路由切换。本文拆解这套双传输层架构如何在一个 Swift 应用里把两个完全异构的网络协议缝合成一条消息路径，以及它的 geohash 频道、Noise XX 握手、私有 envelope 与适用边界。"
draft: false
categories: ["技术笔记"]
tags: ["Nostr", "蓝牙mesh", "去中心化", "隐私通讯", "开源"]
---

# BitChat：蓝牙 mesh + Nostr 双传输层，让消息在没有信号时也能离开本地

> BitChat 的真正贡献不是"又一个加密聊天 App"，而是把两个完全异构的传输层——蓝牙 LE 多跳 mesh 和 Nostr 中继网络——塞进同一个客户端，让消息按"蓝牙优先、Nostr 兜底"的策略自动选路。它读懂了一个被多数隐私通讯产品忽略的现实：**离线性（offline-capable）和可达性（reachability）是两件事**，而真正的灾难场景里，你既需要没信号的本地组网，也需要能在信号恢复时把那条消息送出小镇。
>
> 读完这篇文章，你能不查文档回答：BitChat 的双层架构里哪一层处理"最后一公里"，哪一层处理"最后一海里"；消息从 A 到达 B 在不同网络条件下走的是哪条路径；`#dr5rsj7`、`#dr5rs`、`#dr` 这种 geohash 频道是怎么从经纬度映射出来的；BitChat 私信 envelope 为什么故意不兼容 NIP-17 / NIP-44 / NIP-59；以及它最适合谁、最不该被用在哪。
>
> 来源：GitHub [permissionlesstech/bitchat](https://github.com/permissionlesstech/bitchat)，源码以 Unlicense 进入公共领域；架构与威胁模型细节见仓库内 [WHITEPAPER.md](https://github.com/permissionlesstech/bitchat/blob/main/WHITEPAPER.md)。

---

## 核心判断

BitChat 的工程价值落在三个具体决策上：

1. **承认"端到端加密"不等于"可达"**。Signal、Telegram、Matrix 解决的是消息在传输途中不被偷看，但都默认你至少有一种 IP 路径。BitChat 直接面对"基站被洪水冲走、海底光缆被切断、戒严区域关闭蜂窝网络"这种场景，于是把蓝牙 LE 多跳 mesh 作为一等公民——mesh 不需要 SIM 卡、不需要 Wi-Fi、不需要任何基础设施，设备之间直接对讲。
2. **拒绝在两个极端间二选一**。纯 mesh 工具（Briar、Meshtastic）走到一定距离外就完全失联；纯 Nostr 客户端（Damus、Amethyst）只要没网就哑火。BitChat 用一条智能路由把它们拼起来：你和隔壁邻居对话走蓝牙，你离开小镇后给他发消息走 Nostr，你在地铁里写一条消息等出了站再发，走队列。
3. **故意把 Nostr 私信箱子做成"BitChat 专属"**。仓库 README 明确写："BitChat's private-envelope format is proprietary and is **not** NIP-17, NIP-44, or NIP-59 compatible." 这是一个**反互操作**的决策，但它换来了不依赖任何 Nostr 标准库、不被 Nostr 生态升级绑架、可以随时升级密码学套件的独立性。BitChat 用 Nostr 做"传输管道"，但内容层是自己的。

把"协议层互联"和"应用层专有"拆开，是 BitChat 架构上最清醒的选择。

---

## 系统地图：双传输层对照

下表给出 BitChat 两个传输层的横向对照。后面所有拆解都回到这张表展开。

| 维度 | 蓝牙 mesh 层（BLE Mesh） | Nostr 层（Internet） |
|---|---|---|
| **物理介质** | 蓝牙低功耗（Bluetooth Low Energy, BLE）2.4 GHz | 任意 IP 网络（Wi-Fi、4G/5G、有线） |
| **拓扑** | 自组织多跳（ad-hoc multi-hop），最大 7 跳 | 客户端—中继（client-relay）星型，全球 440+ relays |
| **范围** | 单跳约 10–100 米，7 跳可达 1–3 公里（视密度） | 只要有 IP，全球可达 |
| **基础设施依赖** | 无（设备间直连） | 依赖 DNS + 公网可达的 Nostr relay |
| **延迟** | 几十毫秒到几秒（视跳数） | 100 ms–几秒（视 relay） |
| **带宽** | 极低（BLE GATT 约束），LZ4 压缩 | 受限于 IP，单事件几十 KB |
| **寻址** | 设备身份（持久身份密钥派生的 peer ID） | Nostr 公钥（`npub...`），每个 geohash 一对临时密钥 |
| **加密** | Noise Protocol（Noise_XX_25519_ChaChaPoly_SHA256） | BitChat 私有 envelope：XChaCha20-Poly1305 over kind-1059 events |
| **私密性边界** | 端到端加密，但**每台设备的 peer ID 稳定**，附近设备可观察到你的存在 | 信封加密，但 relay 看到你订阅了哪些 geohash |
| **典型场景** | 山野、灾区、戒严、演唱会 | 城市日常、社区群聊、跨城私信 |
| **数据通路** | 设备 → 设备（store-and-forward 离线缓存） | 设备 → relay → relay → 设备 |

这个对照最重要的一点是：**两个层在物理上是冗余的，但在应用层是同一根"消息总线"**。发送方写一条消息，BitChat 客户端决定它走哪根线；接收方在另一端不一定知道这条消息是从蓝牙穿越了 6 个中间人过来的，还是从法兰克福的某个 relay 跳过来的。

---

## 消息如何从 A 送达 B：四类任务流

BitChat 的 README 把"私消息路由（Direct Message Routing）"拆成三种策略：蓝牙优先、Nostr 兜底、智能队列。下面把它们展开成完整的任务流，并加一条"地理频道"的旁支作为第四种流。

### 流 1：同城邻居，Wi-Fi 满格，蓝牙也开着

Alice 给隔壁楼的 Bob 发"晚饭吃了没"。

```
Alice 客户端
  └─→ 检查 Bob 的 peer ID 是否在蓝牙邻居表里
       ├─ 是 → 与 Bob 之间已建立 Noise XX 会话？
       │       ├─ 是 → 直接用 Noise 加密 payload，写入 BLE GATT characteristic
       │       │       └─→ Bob 的手机 BLE 接收 → Noise 解密 → 显示
       │       └─ 否 → 触发 Noise XX 握手（XX 模式：Alice→Bob→Alice→Bob 三步）
       │               └─→ 建立会话后正常发
       └─ 否 → 检查 Bob 的 npub 是否在 favorites
                ├─ 是 → 构造 BitChat private envelope（kind-1059）
                │       └─→ 加密 + 发布到至少 3 个 Nostr relay
                └─ 否 → 提示用户"未找到联系人"
```

关键点：**蓝牙不是广播，是 GATT characteristic 读写**。每条消息都封装成 BLE 的 `characteristic.value` 二进制载荷，UUID 由 BitChat 自定义。这避免了 iOS 端对 BLE 广播包的字符长度限制。

### 流 2：跨国朋友，Alice 在纽约地铁

Alice 给伦敦的 Charlie 发消息，但地铁里完全没信号，蓝牙也没人。

```
Alice 客户端
  └─→ 蓝牙扫描：0 邻居（地铁里没人打开 BitChat）
  └─→ IP 探测：无网络
  └─→ 消息进入"待发送队列"（encrypted blob + 目标 npub + 时间戳）
  └─→ 用户锁屏 / App 进后台（iOS 进入 suspended state）
  ─── 30 分钟后，Alice 出地铁 ───
  └─→ iOS 推送唤醒 + BitChat 检测到 IP 恢复
  └─→ 取出队列头部消息，构造 envelope
  └─→ 发布到 3 个 relay，收到至少 1 个 OK 视为成功
  └─→ 从队列删除
```

关键点：**BitChat 没有中心服务器记着"Charlie 在线"**，所以它不能"消息已送达"语义化。它能做的是"消息至少被一个 relay 接收"。Charlie 何时来拉取，取决于他自己的客户端在线节奏。这是对 Nostr 模型本身"pull-based"特性的诚实接受。

### 流 3：离线灾区，本地 mesh 组网

地震后整个片区断网。Alice、Bo、Carmen、Dave 四人都装了 BitChat，相距几十米到几百米。

```
Alice 发："救援队在广场"
  └─→ 蓝牙优先：BLE 广播给所有邻居（Bo、Carmen、Dave）
       ├─ Bo 收到 → BLE 已可达 Bo → 直接送达
       ├─ Carmen 不在 BLE 范围但 Bo 在范围内
       │    └─ Bo 收到后，BitChat mesh 协议判断"目标 npub 不在邻居表"
       │    └─ Bo 检查自己的待发送队列，发现没有
       │    └─ Bo 不转发（mesh 不是 gossip，是 store-and-forward 给目标）
       │
       └─ Dave 在 Bo + Carmen 之间 → 多跳转发
            路径：Alice → Bo → Carmen → Dave（3 跳，< 7 跳限制）
  └─→ 同时 BitChat 尝试 Nostr fallback
       └─→ 网络不可用 → 写入"等网络恢复后发"队列
```

关键点：**mesh 层的"消息如何到达"不是 gossip 协议**（不是每个人都转发给所有人），而是 store-and-forward——只有目标 peer ID 的持有者会最终拿到，中间节点只是临时缓存。这意味着 mesh 流量不会随跳数指数爆炸，但也意味着 Alice 不能指望"Broadcast"——她必须知道目标。

### 流 4：地理频道，城市级群聊

Alice 进入 `#dr5rsj7` 频道（多伦多某街区级 geohash）。

```
Alice 客户端
  └─→ 计算当前位置 → geohash 精度 7 位 = "街区"（约 153m × 153m）
  └─→ 派生该频道的临时身份密钥对
       （依据：白皮书 "Ephemeral Keys: Fresh cryptographic identity per geohash area"）
  └─→ 订阅至少 3 个 Nostr relay 的 filter（authors = 该临时公钥 OR kinds = 20000 chat)
  └─→ 发出第一条 kind-20000 事件（频道消息）
       └─→ 所有在 `#dr5rsj7` 同一坐标格内的 BitChat 客户端
            都订阅了相同 filter，自然收到
```

关键点：**geohash 精度决定频道粒度**——`#dr`（2 位）= 国家/大区，`#dr5`（4 位）= 省份，`#dr5rs`（6 位）= 街区，`#dr5rsj7`（7 位）= 城市街区（更小）。这是个**有趣的几何性质**：geohash 是 base32 编码的经纬度区间，精度增加 1 位就是把格子四分，所以"加入 `#dr`"的用户其实也隐式接收 `#dr5`、`#dr5rs`... 的所有消息流吗？BitChat 默认每个精度独立订阅。

---

## 蓝牙 mesh 层拆解

### 物理与协议栈

BitChat 把 BLE 用到接近它的协议上限：

- **服务发现（Service Discovery）**：每个 BitChat 节点暴露一个自定义 GATT service（UUID 在代码中定义），characteristic 用来读写加密 payload。
- **广播（Advertising）**：用 BLE advertisement 包携带 peer ID + 短元数据，附近设备扫描后发起 GATT 连接。
- **多跳转发**：BLE 本身没有 mesh 协议栈。BitChat 在应用层实现了一个简单的 store-and-forward 路由器：每条消息带 (sender_peer_id, recipient_peer_id, TTL, payload)，TTL 默认 7。
- **压缩**：每条消息在加密前用 LZ4 压缩。BLE characteristic 单次写入上限通常 20 字节（MTU 协商前）或更高（MTU 协商后），LZ4 把典型聊天消息压到几十字节。

### Noise Protocol 的角色

BitChat 用 Noise Protocol 做蓝牙层的端到端加密，具体是 **Noise_XX_25519_ChaChaPoly_SHA256** 模式（这是 README 的描述，具体 handshake 细节以 WHITEPAPER 为准）。Noise 在这个项目里的几个特点值得说清楚：

1. **XX 模式 = 双向认证 + 密钥派生**。Alice 和 Bob 互换临时密钥，互相验证对方长期身份密钥，最终派生出两个方向的传输密钥。这是 "mutual authentication" 模式，符合"我和邻居聊天也该确认对方是邻居"的需求。
2. **前向保密（Forward Secrecy）**：live session 每次握手都会产生新的临时密钥对，旧 session 即使被解密也无法回溯新 session 的内容。
3. **store-and-forward 邮件没有前向保密**：README 明确写"store-and-forward mail is sealed without it"。这是 BitChat 的一个公开权衡——离线缓存的消息不在 forward secrecy 保护伞下，因为它们必须能被目标设备在任何时刻解密，但还没建立 Noise 会话。

### 隐私权衡

蓝牙 mesh 不是隐身的。**每台设备的 peer ID 是稳定的，从身份密钥派生**。这意味着附近任何运行 BLE 扫描的设备（不一定是 BitChat）都能观察到"有一台 BitChat 设备在这里"，并且只要它持续出现在你的广播范围，对手就能推断"这台设备的用户在某地"。白皮书把这条列在 "Identity and Metadata" 章节，BitChat 没有假装这个问题不存在——它只是把它写在了文档里。

如果你在威胁模型里把"我的 BitChat 设备的持续存在性"列为高敏感信息，那 BitChat 的 mesh 层不适合你；它适合的威胁模型是"我的消息内容不能被中间人看到，但对端知道我在线这件事本身是低成本可观察的"。

---

## Nostr 层拆解

### 为什么选 Nostr 而不是 Matrix 或 SSB

BitChat 选了 Nostr 做全球层，原因是它的传输语义刚好对路：

- **relay 模型 = 天然抗单点故障**。440+ relay 散布全球，发一条消息至少发到 3 个 relay，接收方从自己订阅的 relay 拉。
- **事件（event）是不可变的发布-订阅单元**，非常贴合"消息就是事件"的抽象。
- **公钥 = 身份**，无需注册、无需服务器开账号。

相比之下，Matrix 要 homeserver，SSB 要 invite 链。Briar 选了类似"蓝牙 + Tor"，但 Tor 在国内/灾区场景几乎一定被掐掉。BitChat 的"蓝牙本地 + Nostr 公网"组合，在抗审查能力和可达性之间找到了一个实用的甜区。

### BitChat 私有 envelope

这是 BitChat 在 Nostr 上最反直觉的设计：

> BitChat's private-envelope format is proprietary and is **not** NIP-17, NIP-44, or NIP-59 compatible.

也就是说：当 Alice 通过 Nostr 给 Bob 发私信时，她发的并不是一个标准的 NIP-17 gift wrap，也不是 NIP-44 加密的 kind-4 DM。它是一个 **kind-1059（gift wrap 的事件 kind）**，但 `content` 字段是 `v2:` 前缀的 **BitChat-specific XChaCha20-Poly1305** 密文。

为什么不直接用 NIP-44？

- NIP-44 是 Noise + ChaCha20 的混合，有自己的版本演进规则（早期版到新版不断迭代）。BitChat 想要完全控制信封格式、加密套件、消息大小边界。
- 不走 NIP-17 意味着不需要 NIP-59 的 seal/gift-wrap 双层包装，BitChat 私信只有一层。
- 这种"借用 relay、不借用加密"的策略让 BitChat 可以在 Nostr 协议升级时保持自己的节奏，不会被 NIP 标准升级绑定。

**代价**：任何 BitChat 节点想和 Damus / Amethyst 等通用 Nostr 客户端互发私信，都做不到。BitChat 是 Nostr 上的一个**应用孤岛**。这是它明确接受的代价——README 把这条写在显眼位置，意思是"我们知道，我们故意的"。

### 地理频道与 geohash

频道名 `#dr5rsj7` 是一个 7 位的 geohash。每个字符是 base32 字母表（`0123456789bcdefghjkmnpqrstuvwxyz`），代表一个不断四分的经纬度格子。

| 频道名前缀 | 精度 | 近似范围 | 用途 |
|---|---|---|---|
| `#dr` | 2 字符 | 国家/大区 | 跨国/全国闲聊 |
| `#dr5` | 4 字符 | 省/州 | 区域讨论 |
| `#dr5rs` | 6 字符 | 街区 | 邻里 |
| `#dr5rsj7` | 7 字符 | 城市街区（~153m × 153m） | 广场、咖啡馆级别的群 |

每次加入一个新频道，BitChat 为该 geohash 派生一对**临时密钥**（ephemeral key）。这样：

- 同一物理位置的用户在 `block #dr5rsj7` 频道用同一对密钥签名 → 互相可验证彼此都在该位置附近；
- 离开该区域（或切换频道）→ 旧密钥对作废，新频道用新密钥；
- relay 上看不到你"真正的 npub"，只看得到该频道的临时身份。

这是 BitChat 把"地理范围"和"身份范围"对齐的方法：你在哪，签名的密钥对就属于哪。

---

## 加密方案对照

| 层 | 协议 | 算法 | 模式 | 前向保密 |
|---|---|---|---|---|
| 蓝牙 mesh live | Noise Protocol | X25519 + ChaCha20-Poly1305 + SHA-256 | Noise_XX | ✅ 每次会话 |
| 蓝牙 mesh store-and-forward | Noise Protocol 衍生 | 同上，但密钥绑定到长期身份 | sealed envelope | ❌（文档明示） |
| Nostr 私信 | BitChat 私有 envelope | XChaCha20-Poly1305 | kind-1059 + v2: 前缀 | 由 envelope 设计决定（无 NIP-44 演进依赖） |
| Nostr 地理频道 | 明文 kind-20000 事件 | —— | —— | 不适用（公共频道本就是公开的） |

一个值得展开的细节：**store-and-forward 没有 forward secrecy** 这件事。意思是：灾区里 Alice 给 Bob 发了一条消息，Bob 三天后才离开灾区收到。这条消息在 Bob 手机上的本地数据库里加密了——但如果 Bob 的长期身份密钥三年后泄露，攻击者**理论上可以解开这条离线缓存**。这不是 BitChat 实现 bug，是"可离线送达"和"前向保密"在物理上不可两全：消息必须被存储在某处，那个存储必须能被目标在任意时刻解密。

BitChat 的应对是让 store-and-forward 的**存储期**有限（白皮书未给出具体值，TODO 查阅源码 `MessageStore` 实现确认），并把"长期身份密钥"留在用户手机的 Secure Enclave / Keychain 里。

---

## 适用场景与边界

### 适合用 BitChat 的场景

- **灾害通信**：地震、台风、洪水后基站失效，但人还能聚集。BitChat mesh 在 1 公里内的人群里就是 IRC 替代品。
- **戒严 / 大规模抗议**：传统通讯被关停时，蓝牙 mesh 是少数不依赖任何基础设施的选项。Nostr layer 在信号恢复后把消息外传。
- **山林徒步 / 远海航行**：队友间 7 跳蓝牙覆盖几公里，不需要卫星电话。
- **音乐节 / 演唱会 / 大型集会**：几万人聚集、4G 拥塞、Wi-Fi 不可信。BitChat 的 `#dr5rs`（街区级）频道就是给现场群聊准备的。
- **普通隐私聊天**：不想要账号、不要手机号、不信任中心服务器。BitChat 的"favorites"机制支持存 Nostr 公钥做长期联系人。

### 不适合用 BitChat 的场景

- **高吞吐多媒体消息**：BLE GATT characteristic 写速率有限，发图会卡得很痛苦。BitChat 文本优先。
- **大规模公共讨论**：geohash 频道用临时密钥，每次切频道换一对身份——你没法在 `#dr` 频道里积累"个人声誉"。BitChat 不是 Twitter 替代品。
- **强 metadata 隐私需求**：mesh 层 peer ID 稳定，附近任何 BLE 扫描器都能观察你的存在性。Signal、SimpleX 在 metadata 上做得更彻底。
- **需要"已读回执"的场景**：Nostr 是 pull-based，BitChat 没有"已送达 / 已读"语义。
- **企业内协作**：BitChat 没有组织/角色/审计日志，不是 Slack 替代品。

### 与其他隐私通讯工具的对比

| 工具 | 离线本地组网 | 全球互联网层 | metadata 保护 | 用户账号 |
|---|---|---|---|---|
| **BitChat** | ✅ BLE mesh（7 跳） | ✅ Nostr（relay-based） | 中（peer ID 稳定） | ❌ 无 |
| Signal | ❌ | ✅ Signal 服务器 | 中（Sealed Sender 部分保护） | ✅ 电话号 |
| Briar | ✅ Wi-Fi/BLE/网状 | ✅ Tor | 较好 | ❌ 无 |
| Meshtastic | ✅ LoRa mesh | ❌ | 较好 | ❌ 无 |
| SimpleX | ❌ | ✅ SMP 代理 | 强（无用户 ID） | ❌ 无 |
| Damus | ❌ | ✅ Nostr | 中（公钥即身份） | ❌ 无 |

BitChat 的定位是**唯一在"离线组网"和"全球可达"两项上都打勾的隐私通讯工具**。这不是说它在每一项上都最强——事实上它在 metadata 保护上不如 SimpleX，在 mesh 范围上不如 Meshtastic——但它在两项上的组合是稀缺的。

---

## 一些值得继续追的细节

- **kind-1059 envelope 的具体字段布局**：README 没有给出，`v2:` 前缀的解析逻辑要去读 `BitChatNostrProtocol.swift`（仓库内）。这影响与第三方 Nostr 客户端的兼容性测试。
- **store-and-forward 的 TTL**：白皮书提到"sealed without forward secrecy"，但消息在中间节点缓存多久被丢弃、是否可配置？这关系到灾区场景的可靠性。
- **relay 选择策略**：Alice 选哪 3 个 relay？是硬编码清单、按地理位置选、还是 pubkey 关联的 trusted relay 集合？
- **多设备登录**：一个 npub 在 iPhone 和 Mac 上同时登录时，私消息路由到哪台？这影响 Nostr 层的去重逻辑。
- **Nostr 临时密钥与地理频道的可关联性**：你在 `#dr5rsj7` 用了临时密钥 K1，在 `#dr5rsj8` 用了 K2，relay 能看出 K1 和 K2 的发布模式相似吗？这是一个 fingerprinting 问题。

---

## 一句话总结

BitChat 不是在做"又一个加密聊天 App"，而是在做一个**承认现实世界没有连续 IP**的通讯工具：蓝牙 mesh 解决最后一海里，Nostr relay 解决最后一公里，智能路由让消息在两条线之间无缝切换。代价是不兼容 Nostr 标准的私信层、不抗 BLE 扫描的 peer ID 暴露、和 store-and-forward 的前向保密缺位。它适合的威胁模型是"消息内容 + 全球可达 + 无需账号"，不适合的是"metadata 极致隐私 + 大规模公共讨论 + 已读回执"。
