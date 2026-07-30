---
title: "Baileys 深度拆解：WhatsApp Web 逆向工程与 WebSocket 协议实现"
slug: "whiskeysockets-baileys-whatsapp-web-api-guide"
date: "2026-07-31T01:23:00+08:00"
lastmod: "2026-07-31T01:23:00+08:00"
draft: false
categories: ["技术笔记"]
tags: ["WhatsApp", "逆向工程", "WebSocket", "TypeScript", "加密通信"]
description: "Baileys 是 WhiskeySockets 维护的 WhatsApp Web 逆向工程库，通过 WebSocket 长连接复用 WhatsApp Web 的 Noise 协议握手与 Signal 端到端加密体系，在 TypeScript/JavaScript 运行时中实现消息收发、群组管理和多设备同步。本文拆解其分层架构、加密握手流程、二进制协议编解码与认证状态管理。"
---

# Baileys 深度拆解：WhatsApp Web 逆向工程与 WebSocket 协议实现

## 核心判断

Baileys 不是一层薄封装。它把 WhatsApp Web 浏览器客户端的完整通信链路——从 WebSocket 建连、Noise XX 握手、Signal 协议加解密，到 WhatsApp 自定义二进制协议（Binary XML）的编解码——全部在 TypeScript 中重新实现了一遍。这意味着每一条消息的收发，实际上都在重复浏览器版 WhatsApp 的加密通信流程，而不是调用某个 REST API。理解了这一点，才能理解 Baileys 为什么选择 WebSocket 长连接、为什么认证状态如此复杂、以及为什么它天然受到 WhatsApp 反自动化策略的约束。

## 项目坐标

| 维度 | 数据 |
|------|------|
| 仓库 | WhiskeySockets/Baileys |
| Stars | 约 10.4k |
| 主语言 | JavaScript / TypeScript |
| License | MIT |
| 当前版本 | v7.0.0-rc14（2026-07-29） |
| npm 包名 | `baileys` |
| 文档站 | baileys.wiki |
| 核心依赖 | `ws`、`libsignal`、`protobufjs`、`whatsapp-rust-bridge` |

项目最初由 Adriano Tajer 维护（原名 `@adiwajshing/baileys`），后由 Rajeh Taher / WhiskeySockets 社区接手，目前仍在活跃开发，最新提交集中在 2026 年 7 月。

## 系统地图：四层通信栈

Baileys 的源码按通信协议的层次自底向上组织，而非按功能模块平铺。理解这个分层是阅读代码的入口：

```
┌──────────────────────────────────────────────────┐
│  API 层（src/Socket/）                            │
│  messages-send / messages-recv / groups / chats  │
│  business / communities / newsletter / mex       │
├──────────────────────────────────────────────────┤
│  加密层（src/Signal/ + src/Utils/crypto.ts）       │
│  libsignal 会话 / 组播 SenderKey / AES-GCM / ECDH │
├──────────────────────────────────────────────────┤
│  帧层（src/Utils/noise-handler.ts）                │
│  Noise XX 握手 / Transport 加解密 / 帧分包        │
├──────────────────────────────────────────────────┤
│  传输层（src/Socket/Client/）                      │
│  WebSocket 连接 / 心跳 / 重连                      │
└──────────────────────────────────────────────────┘
         ↕  二进制协议编解码（src/WABinary/）
         ↕  Protobuf 定义（WAProto/）
```

四层各自独立，通过函数调用串联。传输层负责 WebSocket 生命周期，帧层处理 Noise 协议的加密帧，加密层在帧内做 Signal 协议的消息加解密，API 层把加密后的 payload 封装成 WhatsApp 的业务语义（发消息、建群、同步历史等）。`src/WABinary/` 是一条横切的编解码通道，所有层的 XML-like 节点都经过它编码为 WhatsApp 私有二进制格式。

### Socket 分层组合

API 层本身采用洋葱式组合。最内层是 `makeSocket`（`src/Socket/socket.ts`），负责连接管理和原始消息收发。每一层 Socket 函数接收 config、返回增强后的 Socket 对象：

```typescript
// src/Socket/index.ts
const makeWASocket = (config: UserFacingSocketConfig) => {
  const newConfig = { ...DEFAULT_CONNECTION_CONFIG, ...config }
  return makeCommunitiesSocket(newConfig)
}
```

调用链从外到内是：`makeWASocket` → `makeCommunitiesSocket` → `makeNewsletterSocket` → `makeMessagesSocket` → `makeGroupsSocket` → `makeChatsSocket` → `makeBusinessSocket` → `makeSocket`。每一层通过解构上一层 Socket 的方法，再挂载自己的能力。每层只处理自己的业务域（群组、消息、社区等），但整个 Socket 对象的类型推导链因此拉得很长，调试时需要理清层级关系才能定位方法定义。

## 传输层：WebSocket 连接的生命周期

### 建连

WhatsApp Web 的入口是 `wss://web.whatsapp.com/ws/chat`。Baileys 使用 Node.js `ws` 库建立 WebSocket 连接，并在握手阶段伪造浏览器 Origin：

```typescript
// src/Socket/Client/websocket.ts
this.socket = new WebSocket(this.url, {
  origin: DEFAULT_ORIGIN, // 'https://web.whatsapp.com'
  headers: this.config.options?.headers as {},
  handshakeTimeout: this.config.connectTimeoutMs,
  agent: this.config.agent
})
```

WhatsApp 服务器通过 Origin 头部判断请求来源。Baileys 将其设为 `'https://web.whatsapp.com'`（定义在 `src/Defaults/index.ts`），让服务器认为对面是浏览器会话。如果连接 URL 中携带了 `routingInfo`（多设备注册后获得的路由信息），还会以 `ED` 前缀追加到 WebSocket URL 的查询参数中。

### 心跳与重连

连接建立后，Baileys 以 `keepAliveIntervalMs`（默认 30 秒）为间隔发送心跳。如果连接断开，会根据 `DisconnectReason` 判断是否重连。` DisconnectReason.loggedOut` 表示认证失效，不再重连；其他原因（网络抖动、服务器关闭等）会自动重新建立连接。

### 事件驱动模型

WebSocket 客户端继承 `EventEmitter`，把 `ws` 的事件（`open`、`message`、`close`、`error`）转发给上层。所有消息收发都通过事件系统异步处理。`makeSocket` 内部维护了一个 tag 计数器，每条发出的消息都会获得唯一 tag（如 `TAG:123`），收到对应 tag 的响应时触发回调。这是一种基于消息 ID 的 request-response 匹配机制。

## 帧层：Noise XX 协议握手

这是整个项目最硬核的逆向工程成果。Baileys 复现了 WhatsApp Web 的 Noise 协议握手——具体是 `Noise_XX_25519_AESGCM_SHA256` 模式。

### Noise 协议是什么

Noise Framework 是一套密钥协商协议族，由 Trevor Perrin 设计。`Noise_XX` 表示双向交换身份的握手模式，双方各自生成临时密钥对，经过三轮握手完成双向认证和共享密钥推导。WhatsApp 选择了 `XX` 模式配合 X25519（椭圆曲线 Diffie-Hellman）、AES-GCM（对称加密）和 SHA-256（哈希），构成完整的传输加密方案。

### Baileys 的实现

`src/Utils/noise-handler.ts` 是 Noise 握手的核心，约 300 行代码：

```typescript
// src/Defaults/index.ts
export const NOISE_MODE = 'Noise_XX_25519_AESGCM_SHA256\0\0\0\0'
export const NOISE_WA_HEADER = Buffer.from([87, 65, 6, DICT_VERSION]) // 'WA' + version bytes
```

握手开始前，Baileys 生成一对临时 X25519 密钥对（`ephemeralKeyPair`），然后构造 intro header 发送给服务器。header 内容是 `NOISE_WA_HEADER`（固定字节 `0x57 0x41 0x06 0x03`），如果有路由信息则前缀 `ED` 标记和长度字段。

握手过程中，双方交换公钥，通过 HKDF（HMAC-based Key Derivation Function）逐步推导出加密密钥和解密密钥。每一步的 `mixIntoKey` 调用都会用上一轮的输出作为下一轮的 salt，完成密钥轮换：

```typescript
const localHKDF = (data: Uint8Array): [Uint8Array, Uint8Array] => {
  const key = hkdf(Buffer.from(data), 64, { salt, info: '' })
  return [key.subarray(0, 32), key.subarray(32)]
}

const mixIntoKey = (data: Uint8Array) => {
  const [write, read] = localHKDF(data)
  salt = write
  encKey = read
  decKey = read
  counter = 0
}
```

握手完成后进入 Transport 状态，后续所有 WebSocket 帧都用 AES-256-GCM 加密。`TransportState` 类维护读写两个计数器，每个计数器递增后填入 12 字节 IV 的后 4 字节，保证每次加密的 IV 唯一。这是一个标准的 Counter-based IV 方案。

### 为什么 Noise 而非 TLS

WhatsApp 的 WebSocket 连接虽然走 `wss://`（即 TLS），但 WhatsApp 在 TLS 之上又叠加了一层 Noise 加密。这意味着即使 TLS 被中间人攻击突破，WhatsApp 的通信内容仍然被 Noise 层保护。对于逆向工程项目来说，复现这层加密是最关键的门槛——做不到就无法与服务器通信。

## 加密层：Signal 协议与端到端加密

Noise 层保护的是客户端与 WhatsApp 服务器之间的传输安全。在此之上，WhatsApp 使用 Signal 协议保护消息内容的端到端加密（End-to-End Encryption，E2EE）——即使是 WhatsApp 服务器也无法解密消息明文。

### libsignal 集成

Baileys 直接依赖 `libsignal`（Signal 协议的参考实现），在 `src/Signal/libsignal.ts` 中构建了自己的 `SignalRepository`。核心能力包括：

- **单聊会话**（`SessionCipher`）：每个联系人对应一个 Signal 会话，使用 X3DH（Extended Triple Diffie-Hellman）完成密钥协商，Double Ratchet 算法保证每条消息使用不同的密钥。
- **群聊会话**（`GroupCipher` + `SenderKey`）：群组消息使用 Sender Key 协议，每个发送者在群里广播一次 Sender Key Distribution Message（SKDM），后续群成员即可用该密钥解密发送者的消息，避免群组内 N×N 的会话膨胀。
- **PreKey 管理**：每个设备需要维护一批 PreKey（预共享密钥），服务器在分配消息时消耗 PreKey。当 PreKey 数量低于 `MIN_PREKEY_COUNT`（5）时，客户端需要补充上传新批次。

```typescript
// src/Signal/libsignal.ts
decryptMessage({ jid, type, ciphertext }) {
  const addr = jidToSignalProtocolAddress(jid)
  const session = new libsignal.SessionCipher(storage, addr)
  // 根据消息类型选择 PreKeyWhisperMessage 或 WhisperMessage 解密路径
}
```

### whatsapp-rust-bridge

从依赖列表可以看到，Baileys 引入了 `whatsapp-rust-bridge`（v0.5.4）。这个包通过 Rust FFI 或 WASM 提供了以下核心原语的 Rust 实现：

- `hkdf`：HMAC-based Key Derivation Function
- `md5`：MD5 哈希（用于媒体文件哈希校验）
- `LTHashAntiTampering`：LT Hash（Lattice Tree Hash），用于应用状态同步（App State Sync）的完整性校验

Rust 实现的引入主要是性能考虑——Node.js 的 crypto 模块不直接提供 HKDF（旧版本），而 LT Hash 是 WhatsApp 专有算法，没有现成的 npm 包。

### 认证状态与密钥持久化

Signal 协议要求客户端持久化大量加密材料：身份密钥对（identity key pair）、会话状态（session state）、PreKey 批次、Sender Key 记录、应用状态同步密钥等。Baileys 在 `src/Utils/use-multi-file-auth-state.ts` 中提供了基于文件系统的默认实现：

```typescript
export const useMultiFileAuthState = async (folder: string) => {
  // 每种密钥类型存为单独的 JSON 文件
  // 文件名格式：{type}-{id}.json
  // 使用 async-mutex 防止并发写入冲突
}
```

这个实现为每个密钥创建独立的 JSON 文件，用 `async-mutex` 加文件锁防止并发写入。作者在注释中明确说明这不适合生产环境使用，推荐替换为 SQL 或 NoSQL 数据库后端。真实部署中，开发者通常需要实现自定义的 `AuthenticationState`，将密钥存入 Redis、PostgreSQL 或 MongoDB。

## 二进制协议：WhatsApp 私有的 Binary XML

WhatsApp Web 不使用 JSON 或标准 XML，而是一种自研的二进制 XML 编码。Baileys 在 `src/WABinary/` 中实现了完整的编解码器。

### 协议特征

WhatsApp 的二进制协议把 XML-like 的树形结构（`BinaryNode`）编码为紧凑的字节流：

```typescript
interface BinaryNode {
  tag: string           // 元素标签，如 'message', 'iq', 'presence'
  attrs: Record<string, string>  // 属性键值对
  content?: BinaryNode[] | Uint8Array | string  // 子节点或二进制内容
}
```

编码器（`encode.ts`）的核心逻辑：

- **Token 压缩**：常用标签名和属性名被映射为单字节或双字节 token。例如 `<message>` 的 tag 名可能被编码为一个字节，而非 ASCII 字符串。
- **长度编码**：支持 8-bit（1 字节）、20-bit（3 字节）和 32-bit（4 字节）三种长度前缀，适配不同大小的 payload。
- **JID 编码**：WhatsApp 的用户标识符（JID，Jabber ID）有专用编码格式，支持携带 device ID 和 domain type。
- **Nibble/Hex 打包**：数字字符串和十六进制字符串被压缩存储，两个字符打包为一个字节。

解码器（`decode.ts`）还处理可选的 zlib 压缩——如果首字节的第 1 位为 1，则 payload 经过 `zlib.inflate` 解压后再解码。

### 一次消息发送的完整路径

以"向好友发送一条文本消息"为例，追踪数据在系统中的流转：

```
1. 调用 sock.sendMessage(jid, { text: 'hello' })
   ↓  API 层：messages-send.ts
2. 构造 proto.Message 对象（Protobuf 编码）
   ↓
3. 查找收件人的 Signal 会话，加密消息体
   ↓  加密层：libsignal.ts → SessionCipher.encrypt()
4. 封装成 BinaryNode（<message> 节点，携带加密 payload）
   ↓
5. 编码为 WhatsApp 二进制格式
   ↓  WABinary/encode.ts → encodeBinaryNode()
6. Noise Transport 加密（AES-256-GCM）
   ↓  帧层：noise-handler.ts → transport.encrypt()
7. WebSocket 发送加密帧
   ↓  传输层：WebSocketClient.send()
8. WhatsApp 服务器接收并路由
```

收消息是反向路径：WebSocket 收到帧 → Noise 解密 → 二进制解码 → Signal 解密 → 触发 `messages.upsert` 事件。

## 认证流程：QR Code 与配对码

Baileys 支持两种认证方式：

### QR Code 扫码

默认方式。连接建立后，Baileys 发送注册请求（`generateRegistrationNode`），服务器返回一个包含 QR 码数据的响应。用户用手机 WhatsApp 扫描这个 QR 码，完成设备绑定。绑定成功后，服务器返回 companion metadata（设备身份、注册 ID、Signal 密钥种子等），Baileys 将这些信息存入 `authState.creds`。

### 配对码（Pairing Code）

适用于无法扫码的场景（如服务器部署）。调用 `sock.requestPairingCode(phoneNumber)` 后，服务器返回一个 8 位配对码，用户在手机 WhatsApp 中输入该码完成绑定：

```typescript
if (usePairingCode && !sock.authState.creds.registered) {
  const phoneNumber = await question('Please enter your phone number:\n')
  const code = await sock.requestPairingCode(phoneNumber)
  console.log(`Pairing code: ${code}`)
}
```

配对码通过 `derivePairingCodeKey` 从手机号派生密钥，加密后发送给服务器验证。两种方式最终都会在 `configureSuccessfulPairing` 中完成设备注册，生成 Signal 协议所需的身份密钥对和 PreKey 批次。

## 多设备架构的影响

WhatsApp 的多设备支持（Multi-Device）从根本上改变了协议设计。在旧架构中，手机是主设备，Web 客户端只是手机的"镜像"——所有消息先到手机再转发。多设备架构下，每个设备成为独立的端点，直接与服务器通信，消息在设备间端到端加密。

这对 Baileys 的影响包括：

- **LID（Linked Identity）映射**：多设备引入了 LID 体系，每个用户有一个 PN（Phone Number）JID 和一个 LID。`src/Signal/lid-mapping.ts` 负责两者之间的映射，确保消息发给正确的设备组。
- **PreKey 协商**：发送消息时，Baileys 需要查询收件人所有已注册设备的 PreKey，对每台设备分别加密。`extractDeviceJids` 和 `parseAndInjectE2ESessions` 完成这一工作。
- **历史同步**：新设备首次连接时，通过 `HistorySync` 协议批量拉取历史聊天记录。Baileys 在 `src/Utils/history.ts` 中处理同步数据的分块接收和解密。同步类型包括 `INITIAL_BOOTSTRAP`、`RECENT`、`FULL`、`ON_DEMAND` 等，可通过 `shouldSyncHistoryMessage` 配置过滤策略。
- **应用状态同步**：联系人和聊天的变更通过 App State Patch 机制同步。LT Hash 用于验证 patch 序列的完整性——如果某个 patch 丢失或乱序，哈希校验会失败。

## 事件系统与消息处理

Baileys 使用 `EventEmitter` + 批处理的设计处理事件。`makeEventBuffer`（`src/Utils/event-buffer.ts`）是一个中间层，把高频事件先缓存再批量触发，避免逐条消息触发回调导致的性能问题：

```typescript
// Example/example.ts
sock.ev.process(async (events) => {
  if (events['messages.upsert']) {
    const upsert = events['messages.upsert']
    if (upsert.type === 'notify') {
      for (const msg of upsert.messages) {
        // 处理消息
      }
    }
  }
  if (events['connection.update']) {
    // 处理连接状态变更
  }
})
```

核心事件包括：

| 事件名 | 触发时机 |
|--------|----------|
| `connection.update` | 连接状态变更（开启、关闭、QR 码更新） |
| `messages.upsert` | 收到新消息或历史同步消息 |
| `messages.update` | 消息状态变更（已送达、已读、撤回） |
| `presence.update` | 联系人在线状态变更 |
| `messaging-history.set` | 历史同步批次到达 |
| `creds.update` | 认证凭据变更（需要持久化） |
| `contacts.upsert` / `contacts.update` | 联系人新增或变更 |
| `groups.update` | 群组信息变更 |

## API 能力一览

Baileys 的 API 覆盖了 WhatsApp Web 的绝大多数功能。以下列举主要能力域及其对应的 Socket 层：

| 能力域 | Socket 层 | 代表方法 |
|--------|-----------|----------|
| 消息收发 | `messages-send.ts` / `messages-recv.ts` | `sendMessage`、`requestPlaceholderResend` |
| 媒体上传 | `messages-media.ts` | `waUploadToServer`（支持 image/video/audio/document/sticker） |
| 群组管理 | `groups.ts` | `groupCreate`、`groupMetadata`、`groupToggleEphemeral` |
| 聊天操作 | `chats.ts` | `chatModify`（归档、置顶、静音等） |
| 社区 | `communities.ts` | 社区创建与管理 |
| Newsletter | `newsletter.ts` | 频道消息发布与订阅 |
| 商业账号 | `business.ts` | 商业资料管理 |
| 联系人同步 | WAUSync | `fetchContacts`、USync 协议 |
| 链接预览 | `link-preview.ts` | 自动抓取 URL 的 OG 元数据 |

媒体处理是 Baileys 的一个亮点。上传时，文件先经过 AES 加密再发送到 WhatsApp 的媒体服务器（`mmg.whatsapp.net`），加密密钥通过 HKDF 派生，与消息类型一一对应：

```typescript
// src/Defaults/index.ts
export const MEDIA_HKDF_KEY_MAPPING = {
  audio: 'Audio',
  document: 'Document',
  gif: 'Video',
  image: 'Image',
  sticker: 'Image',
  video: 'Video',
  // ...
}
```

下载媒体时走反向路径：获取 CDN URL → 下载加密文件 → HKDF 派生解密密钥 → AES 解密。

## 采用建议与适用边界

### 适合用 Baileys 的场景

- **客服自动化**：中小团队需要通过 WhatsApp 提供自动客服，且无法承担 WhatsApp Business API 的按条计费成本。
- **通知机器人**：内部系统（监控告警、订单通知）通过 WhatsApp 推送消息，利用其高触达率。
- **聊天机器人原型**：快速验证 NLP / LLM 对话效果，Baileys 提供了足够的消息类型支持（文本、图片、按钮、列表等）。
- **数据备份**：个人用户导出自己的聊天记录（配合 `HistorySync` 事件）。

### 不适合的场景

- **大规模群发营销**：WhatsApp 的反垃圾机制会对短时间内大量发送异常消息的账号进行封禁，Baileys 作为非官方 API 没有官方限流保护。
- **需要高稳定性的生产系统**：WhatsApp 可以在任何时候修改协议（更换服务器证书、调整握手流程、更新二进制协议 token 映射），每次变更都可能导致 Baileys 短暂失效，直到社区完成适配。
- **合规敏感场景**：Baileys 明确声明不与 WhatsApp 官方关联，使用逆向工程 API 存在法律灰色地带。企业级生产环境应优先考虑 WhatsApp Business API（官方 Cloud API / On-Premise API）。

### 接入顺序建议

如果决定使用 Baileys，推荐的接入路径：

1. 先跑通 Example 目录下的 `example.ts`，完成 QR 码或配对码认证，确认能收发消息。
2. 实现自定义 `AuthenticationState`，把密钥从文件系统迁移到数据库。
3. 搭配 `pino` 日志做 trace 级别调试，理解事件触发顺序。
4. 处理重连逻辑：监听 `connection.update`，在非 `loggedOut` 的断开场景中自动重连。
5. 按需扩展：群组管理、媒体处理、链接预览等能力在确认基础消息链路稳定后再接入。

### 风险认知

Baileys 的核心风险来自其非官方性质。WhatsApp 没有公开 WebSocket 协议的文档，所有协议知识都来自社区逆向。每个 WhatsApp Web 版本更新都可能引入协议变更：

- **版本号跟踪**：Baileys 在 `src/Defaults/index.ts` 中硬编码了 WA Web 版本号（当前 `[2, 3000, 1043857760]`），并提供 `fetchLatestBaileysVersion()` 从 npm registry 获取社区维护的最新版本号。
- **Breaking Change**：7.0.0 引入了多处破坏性变更，迁移指南发布在 `whiskey.so/migrate-latest`。
- **封号风险**：新注册的号码或发送模式异常的账号容易被封。社区经验建议使用已活跃一段时间的号码，初期控制消息频率。

## 结语

Baileys 的技术含量集中在两个维度：一是完整复现了 WhatsApp Web 的 Noise + Signal 双层加密通信链路，二是把 WhatsApp 的私有二进制协议和 Protobuf 定义做了系统性的 TypeScript 映射。阅读这个项目的源码，等于沿着一条真实的逆向工程产品走了一遍从传输层到业务层的完整路径。对于想理解即时通讯协议设计、端到端加密工程实践或 WebSocket 逆向的人来说，Baileys 是一个信息密度极高的学习样本。

但正因为它的能力建立在逆向工程之上，每一个使用 Baileys 的人都应该清楚：这条链路的稳定性不取决于 Baileys 自身的代码质量，而取决于 WhatsApp 何时改协议。
