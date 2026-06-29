---
title: "SimpleX Chat 架构指南：把\"用户 ID\"从隐私消息里拆掉的工程问题"
date: 2026-06-26T21:04:12+08:00
slug: "simplex-chat-simplex-chat-privacy-first-messaging-architecture-guide"
aliases:
  - "/posts/tech/simplex-chat-simplex-chat-privacy-first-messaging-architecture-guide/"
description: "SimpleX Chat 是第一个不分配任何用户标识符的消息网络——不是匿名 ID，不是随机号，而是整套协议里根本没有\"我是谁\"这个槽位。本文拆解它如何用单向消息队列、双 ratchet 加 NaCl 附加层、SMP 代理和无 ID 的连接邀请把社交图谱压扁到服务器看不到的程度。"
draft: false
categories: ["技术笔记"]
tags: ["SimpleX", "隐私消息", "端到端加密", "协议设计", "去中心化通信"]
---

# SimpleX Chat 架构指南：把"用户 ID"从隐私消息里拆掉的工程问题

> SimpleX 不是又一个加密聊天应用。它的核心创新是**整个协议里没有"用户 ID"这个槽位**——不是隐藏，不是加密，而是从设计上就不存在。Signal 有电话号码，Matrix 有 MXID，Session 有随机号，而 SimpleX 的服务器从未见过一个能跨会话拼出"你是谁、你跟谁说话"的稳定标识符。这件事改变了威胁模型，也改变了整套架构。
>
> 读完这篇文章，你能在不查文档的前提下回答：SimpleX 与 Signal、Matrix、Session 的根本差异在哪里；"无用户 ID"具体意味着消息流经哪些组件；为什么 SimpleX 在 2024 年加了后量子密钥交换却没换掉双 ratchet；以及在什么场景下应该把 SimpleX 当成主力通信工具，什么场景下应该绕开。
>
> 来源：GitHub [simplex-chat/simplex-chat](https://github.com/simplex-chat/simplex-chat)，AGPL-3.0 协议；协议细节在 [simplex-chat/simplexmq](https://github.com/simplex-chat/simplexmq) 仓库和 [SimpleX whitepaper](https://github.com/simplex-chat/simplexmq/blob/stable/protocol/overview-tjr.md)。

---

## 这套系统解决的是什么

Signal 已经把"消息内容"端到端加密做到了工业级，问题是它仍然知道"谁在跟谁说话、什么时候"。Mohamedou Ould Salahi 仅仅因为一通电话就被关进关塔那摩 15 年——端到端加密救不了他，因为威胁来自**元数据**（metadata），而不是密文本身。SimpleX 想拆掉的恰恰是这一层：让服务器不仅看不到内容，也看不到"和你通信的是谁"。

它选择的办法是**取消"用户"这个维度**。整套协议里没有用户档案、没有全局 ID、没有随机号。每个人和每个联系人之间的连接是一对独立的"消息队列对"，每对队列有自己的一次性地址。换 10 个联系人就有 20 个独立地址，10 个联系人之间彼此不可关联——他们只看到各自那条通道，根本不知道用户还有别的通道。

代价是：**别人怎么找到你**。答案是一个一次性邀请链接或可选的临时地址（SimpleX address，本质上是一个可吊销的收件箱），用完就失效。把"可发现性"做窄，就把"被关联"做小。

## 系统地图：消息怎么走

下面这张图覆盖了从 Alice 发消息给 Bob 的全部组件。SimpleX 的客户端是控制平面，SMP（SimpleX Messaging Protocol）服务器是数据平面，二者严格分离。

```mermaid
graph TB
  subgraph 客户端层
    A[Alice 客户端<br/>CLI / iOS / Android / Desktop]
    B[Bob 客户端<br/>CLI / iOS / Android / Desktop]
  end
  subgraph Alice 端队列
    AQ1[发送队列 S1<br/>NaCl 加密层]
    AQ2[接收队列 R1<br/>NaCl 加密层]
  end
  subgraph Bob 端队列
    BQ1[发送队列 S2<br/>NaCl 加密层]
    BQ2[接收队列 R2<br/>NaCl 加密层]
  end
  subgraph SMP 代理
    S1[Alice 用 SMP-A<br/>SMP 内存存储]
    S2[Bob 用 SMP-B<br/>SMP 内存存储]
  end
  subgraph 一次性资源
    INV[一次性邀请链接 / 临时地址]
  end
  subgraph 传输层
    PR[私路由<br/>v6.0+ 中继]
    XFTP[XFTP 协议<br/>大文件]
  end

  A -->|写入| AQ1
  AQ1 -->|通过 PR 中继| S1
  S1 -->|通过 PR 中继| BQ2
  BQ2 -->|解密| B

  B -->|写入| BQ1
  BQ1 --> S2
  S2 --> AQ2
  AQ2 --> A

  A -.->|扫码/分享| INV
  INV -.->|扫码/接受| B

  A -->|大文件| XFTP
  B -->|拉取| XFTP

  style SMP 代理 fill:#f5f5f5
  style 一次性资源 fill:#fff5e6
```

关键事实：

- **服务器只在内存里缓存消息**，不持久化。消息被接收后即丢弃，服务器也不存"队列归属人"——只知道有一个加密队列。
- **Alice 和 Bob 用的可能不是同一台 SMP 服务器**，也可能各自多台冗余。服务器之间互不通信，没有"全网视图"。
- **大文件不走 SMP**，走 [XFTP 协议](https://github.com/simplex-chat/simplexmq/blob/stable/protocol/xftp.md)，由独立 XFTP 中继分块传输。文件本身端到端加密，中继只看到 chunk hash。

## 核心机制拆解

### 1. 没有用户 ID：pairwise 队列是协议的根基

SimpleX 的协议原文用了"pairwise per-queue identifiers"这个术语。每个连接（conversation）由两对队列组成——一对用于 Alice → Bob，一对用于 Bob → Alice，每对队列有独立地址，外加一个可选的 iOS 推送通知地址（Android 用长连接，不需要这第三地址）。

| 系统 | 用户标识 | 跨会话可关联性 |
|------|---------|----------------|
| **Signal** | 手机号 | 单一 ID 串起所有联系人 |
| **Matrix** | MXID（@user:server） | 跨服务器可发现 |
| **Session** | 随机号（Session ID） | 同一 ID 串起所有联系人 |
| **Briar / Cwtch** | 匿名身份密钥 | 同一密钥串起所有联系人 |
| **SimpleX** | **无** | 每个连接独立地址，无法跨会话关联 |

这是 SimpleX 与"匿名但有 ID"方案（Session / Matrix / Cwtch / Ricochet）的根本差别。后者只是把"真实身份"藏起来，但保留了"同一个 ID 出现在不同联系人会话里"的可关联性。SimpleX 把这条线索也切断了——Alice 用同一客户端给 Bob 和 Carol 发消息时，Bob 和 Carol 看到的"发送方地址"完全不同，没有任何共享 ID 能让他们确认"这俩是同一个人发的"。

代价是**发现机制必须外置**：SimpleX 不存在"搜索用户名加好友"。你只能通过一次性邀请链接、二维码、临时地址（或群链接）建立连接。这是为元数据保护付的合理代价。

### 2. 双 ratchet + NaCl 附加层：消息在网络里经过几次加密

SimpleX 复用 Signal 的双 ratchet（Double Ratchet）算法做端到端密钥管理，但包了一层自己的结构：

```text
应用层明文
  ↓ ratchet 加密（每个消息独立临时密钥，提供 forward secrecy）
密文 A
  ↓ NaCl cryptobox 加密（队列级共享密钥）
密文 B
  ↓ TLS 1.2/1.3（限 CHACHA20POLY1305_SHA256、Ed25519/Ed448、Curve25519/Curve448）
密文 C → SMP 服务器 → 接收方
```

四层加密各管一段：

1. **双 ratchet**（Curve448 两对密钥做初始 X3DH 协商，之后每条消息用临时密钥）：保证**前向保密**（forward secrecy，被动监听无法追溯历史消息）和**事后保密**（post-compromise security / break-in recovery，密钥在消息交换中自动重协商）。这是 Signal 已经验证过的算法。
2. **NaCl cryptobox 队列级加密**（Curve25519 密钥协商，密钥不轮换，靠队列轮换）：避免服务器在 TLS 被破时看到不同队列里有相同密文，也是为未来**队列冗余**（同一条消息走多台服务器）做准备——冗余路径上的相同消息在 ratchet 层之外多一道独立保护。
3. **TLS 1.2/1.3**：标准传输层加密。SimpleX 把密码学套件卡得很死，只允许经过审计的算法组合，禁用所有 weak cipher。
4. **tlsunique 通道绑定**（[RFC 5929](https://www.rfc-editor.org/rfc/rfc5929.html)）：每条 SMP 命令用队列临时密钥对会话 ID 签名，防重放攻击。

> SimpleX 在 2024 年 3 月（v5.6）给双 ratchet 加了**后量子密钥交换**（post-quantum key exchange），在每个 ratchet 步骤里混入后量子密钥分量。Apple iMessage PQ3 也是同样的设计思路——双 ratchet 算法本身不替换，但每次密钥推进时叠加一层抗量子分量。这意味着 SimpleX 不用"等标准出后量子 ratchet 再行动"，而是在已有协议上做最小侵入式升级。

### 3. SMP 服务器：能存什么、看不到什么

SMP 服务器是 SimpleX 的中转组件，定位很明确：**临时加密消息队列**，不持久化、不互联、不知道队列归属人。

| 能力 | 是否支持 |
|------|---------|
| 持久化消息 | ❌ 仅内存缓存 |
| 服务器间互相同步 | ❌ 完全独立 |
| 知道"这个队列属于谁" | ❌ 队列是加密端点 |
| 知道"两个队列属于同一用户" | ❌ 队列地址对每个连接独立 |
| 给客户端推送通知 | iOS 用 APNS，Android 用长连接 |
| 抗重放 | ✅ tlsunique 通道绑定 |
| 队列冗余（同一消息走多台） | 🏗 计划中（手动支持） |
| 消息混淆（加延迟防时间关联） | 🏗 计划中 |

服务器在协议层**能看到**的只有：连接时间（rounded to second）、密文大小、客户端 IP（除非走 Tor 或私路由）。即使攻破一台服务器，攻击者也只能看到一堆"加密信封"，拼不出社交图谱。

### 4. 私路由（private message routing）：v6.0 之后的 IP 保护

2024 年 6 月（v6.0）SimpleX 默认开启私路由。问题是：**Alice 的 IP 在向 Bob 的 SMP 服务器发送时是暴露的**。SMP 服务器理论上可以通过 IP 反查地理位置和 ISP。SimpleX 的解法是让客户端先把消息发到一台"中继 SMP"，再由中继转发到 Bob 的收件 SMP。

结果是：

- Bob 的 SMP 服务器看不到 Alice 的 IP，看到的是中继的 IP
- 中继服务器看不到消息内容（消息已端到端加密），也看不到 Bob 在哪（目标是 Bob 的收件地址而非 IP）
- 攻击者必须**同时控制中继和收件服务器**才能做关联

这是"per-message transport anonymity"（每条消息的传输匿名），比 Tor 的"per-connection anonymity"（每连接的匿名）粒度更细——每条消息可以走不同中继路径。

### 5. 群组、群链接与频道

SimpleX 的群组也是基于同一套机制：每个群成员之间是 N 个独立的 pairwise 队列。群消息广播时，发送方要把消息分别加密后投递到 N 个收件队列。这看起来浪费，但换来了**服务器完全不知道群成员列表**——它只看到 N 个独立的加密队列，没有"这是一个群"的视图。

2025 年 1 月发布的 v6.x 系列引入了大群组（large groups）和隐私保护的公开频道。频道是"可被搜索、可被订阅"的群组，但订阅者之间的关联对服务器仍然不可见。

## 任务流：Alice 第一次给 Bob 发消息的完整路径

把上面拆开的机制串成一次具体工作：

**Step 0：建立连接**

```text
Alice 客户端生成一个临时连接邀请链接：
  simplex:/invitation#/?v=2-7&smp=smp%3A%2F%2F...%40smp-a.example.com%2F...
  e2e=eyJfZGlkIjoi...
  + 接收方队列地址 R1（分配在 SMP-A 上）
  + Curve448 初始密钥对 K_A

Alice 通过任意渠道（短信、邮件、面对面扫码）把链接发给 Bob。
```

**Step 1：Bob 接受邀请**

```text
Bob 客户端打开链接：
  1. 用 e2e 密钥做 X3DH 初始密钥协商
  2. 创建 Bob → Alice 发送队列 S2（分配在 SMP-B，可能跟 SMP-A 不同）
  3. 在 R1 队列上写入 CONF 消息（含 S2 地址、Curve448 初始密钥对 K_B）
```

**Step 2：双 ratchet 初始化**

```text
Alice 收到 CONF 后：
  1. 用 K_A + K_B 完成 X3DH，得到 root key
  2. 初始化发送链 + 接收链
  3. 后续每条消息都推进 ratchet
```

**Step 3：发消息**

```text
Alice 输入 "hi"：
  1. 应用层明文 → ratchet 加密（用当前 sending chain key）
  2. ratchet 密文 → NaCl 加密（用队列共享密钥 K_queue）
  3. NaCl 密文 + 元数据（包在加密信封里，连消息时间都对服务器不可见）→ TLS
  4. 通过私路由（v6.0+）：先发到中继 → 中继转发到 SMP-A 的 R1 队列
  5. 消息在 SMP-A 内存中暂存
```

**Step 4：Bob 接收**

```text
Bob 客户端长轮询 SMP-B 的 S2 队列：
  1. 拉到密文
  2. NaCl 解密 → ratchet 解密 → 应用层明文 "hi"
  3. 接收链 ratchet 推进
  4. 服务器删除已读消息
```

**Step 5：多端同步**

Bob 在桌面端和手机端登录同一账号时，桌面端会通过 v5.4 引入的"后量子抗性 mobile-desktop 链接协议"自动同步。同步通道是另外一对独立 SMP 队列，跟普通消息通道不共享密钥——服务器无法通过观察同步流量推断"这是哪个用户"。

整个过程中 SMP 服务器看到了什么？**只有加密信封、时间戳（rounded to second）和 Alice 的 IP（如果没走私路由/Tor）**。看不到"Alice"、"Bob"、"hi"、看不到消息大小是否变化（content padding）、看不到两个队列属于同一用户。

## 安全/隐私声明：测什么、不能推出什么

SimpleX 的安全模型建立在几条**明确的可验证声明**上，下面分"它确实做到了"和"它没承诺做到"两组：

**确实做到的**（来自 [SimpleX Chat Protocol](https://github.com/simplex-chat/simplex-chat/blob/master/docs/protocol/simplex-chat.md) 和已发布的 Trail of Bits 审计报告）：

- 端到端消息内容加密：双 ratchet + NaCl 附加层，未发现已知可破解的攻击
- 服务器看不到消息内容：消息密文 + 加密元数据信封
- 跨会话不可关联：不同联系人看到的"发送方地址"完全不同
- 服务器不持久化：内存存储，进程重启后清空
- 重放攻击防护：tlsunique 通道绑定 + 每队列临时密钥签名
- IP 保护：v6.0+ 默认私路由，可选 Tor
- 后量子密钥交换：v5.6+ 每个 ratchet 步骤叠加 PQ 密钥分量
- 2022 年 11 月发布 [Trail of Bits 安全审计](https://simplex.chat/blog/20221108-simplex-chat-v4.2-security-audit-new-website.html)

**没承诺做到**的（必须自己承担风险）：

- **群消息广播的"N 倍加密"成本**：1000 人群里每条消息要做 1000 次 ratchet 加密和投递，电池和流量开销大。SimpleX 用消息合并、增量同步等机制缓解，但没有 Signal 群那样高效的"server-side fan-out"。
- **全局流量分析**：如果攻击者控制多数 SMP 服务器并做时间关联，理论上还能推断"这俩队列在同时活跃"。SimpleX 计划加"消息混淆"（人为延迟）来缓解，但尚未发布。
- **客户端设备安全**：本地数据库用 passphrase 加密，但客户端本身的安全依赖操作系统和设备硬件。
- **元数据残留**：连接邀请链接如果通过明文渠道（明文邮件）发送，对邮件服务器是可见的。SimpleX 的设计假设是"分享渠道可以不可靠，但你要能确认是谁发的"。
- **法律强制披露**：SimpleX 的服务器只存内存消息，没有持久化记录可披露。这既是隐私优势也是合规特性——某些司法管辖区可能要求持久化元数据。
- **客户端的指纹**：iOS/Android 客户端二进制本身的指纹可以被平台识别（应用签名、依赖库等）。如果威胁模型包含"客户端被定位"，需要用 Tails / Whonix 等环境运行 CLI 版本。
- **"完全不可追踪"是营销话术，不是技术声明**：SimpleX 的 README 从未声称"100% 不可追踪"，它说的是"100% private by design"——设计上的隐私优先。两者差距巨大。

**怎么验证这些声明**：

1. 读 SimpleX whitepaper（[overview-tjr.md](https://github.com/simplex-chat/simplexmq/blob/stable/protocol/overview-tjr.md)）和 SimpleX Chat Protocol 规范，自己跑一次 Wireshark 抓包
2. 装 CLI 客户端，开两台虚拟机互发消息，验证服务器侧确实只看到加密信封
3. 跑 [reproducible server build](https://github.com/simplex-chat/simplex-chat/blob/master/docs/SERVER.md#reproduce-builds) 自己编译 SMP 服务器，比对 hash
4. 读 Trail of Bits 审计报告原文，看具体发现和建议项

## 与同类工具的横向对比

| 工具 | 标识符 | 服务器模型 | 元数据保护 | 后量子 | 群组 | 大文件 | 客户端类型 |
|------|--------|----------|-------------|--------|------|--------|------------|
| **SimpleX Chat** | 无 ID | SMP 中继（无持久化） | 跨会话不可关联 | ✅ v5.6+ | ✅ 大群组 | XFTP | CLI/iOS/Android/Desktop |
| [Signal](https://github.com/signalapp/Signal-Android) | 手机号 | 集中式 | 已知联系人+时间 | ✅ PQXDH | ✅ | ✅ | Mobile/Desktop |
| [Matrix](https://github.com/matrix-org/synapse) | MXID | 联邦式 | 服务器可见 | 🏗 实验 | ✅ | ✅ | 多客户端 |
| [Session](https://github.com/oxen-io/session-android) | 随机 Session ID | 洋葱路由 Oxen | 同 ID 跨会话可关联 | ❌ | ✅ | ✅ | Mobile/Desktop |
| [Briar](https://github.com/briar/briar) | 匿名身份密钥 | 无中心（Tor/Wi-Fi/蓝牙） | 仅在连接时匿名 | ❌ | 🏗 | ❌ | Android only |
| [Cwtch](https://github.com/cwtch.im/cwtch) | 匿名身份密钥 | Tor 隐藏服务 | 可关联 | ❌ | ✅ | ✅ | Desktop/Android |

SimpleX 在"元数据保护"维度领先，在"生态成熟度"维度落后于 Signal 和 Matrix。**不存在"最好的隐私消息工具"**——只有"匹配你威胁模型的工具"。

## 适用边界与采用顺序

### 该用的场景

- 你的威胁模型包含"被监控谁能跟你说话"——记者、举报人、持不同政见者、组织内敏感沟通
- 你想要一个**不依赖手机号或邮箱**的通信账号
- 你愿意为元数据保护牺牲易发现性（不能搜用户名加好友）
- 你能接受客户端相对小众、生态不如 Signal/Matrix 完整
- 你想自己跑服务器（[simplexmq 仓库](https://github.com/simplex-chat/simplexmq) 提供 SMP server 实现），用自家基础设施保护特定团队

### 不该用的场景

- **只是想"普通聊天"**——Signal 或 WhatsApp 在易用性、生态、稳定性上完胜，SimpleX 的优势在极端威胁模型下才显现
- **需要 1000+ 人的大群组做实时讨论**——SimpleX 的大群组方案刚发布，流量和延迟开销仍高于 Matrix/Signal
- **企业 IM 替代品**——SimpleX 没有 Slack/Teams 那样的工作流集成、SSO、审计日志、管理后台
- **客户端必须支持 Web**——SimpleX 没有 Web 客户端（明确的设计选择，避免浏览器指纹泄露）
- **你的对手是国家行为体**——任何工具都救不了物理层面的威胁（设备扣押、强制解锁），SimpleX 解决的是网络层元数据，不是物理层

### 采用顺序建议

按这个顺序判断要不要把 SimpleX 引入你的工作流：

1. **装 CLI 版本验证理解**：用 `curl -o- https://raw.githubusercontent.com/simplex-chat/simplex-chat/stable/install.sh | bash` 装 CLI 客户端，开两台机器互发消息。CLI 版本让你看到协议层的全部细节：队列地址、SMP 服务器、ratchet 推进。如果你连这一步都嫌麻烦，后面别用。
2. **换一台手机当主力**：把 iOS 或 Android 客户端装在一部不重要的备用机上，先用 2-4 周处理低敏感度对话。这个阶段观察三点：消息延迟（SimpleX 离线消息延迟比 Signal 高）、电量消耗（群消息加密开销大）、联系人接受度（你得说服对方也装）。
3. **评估自家服务器需求**：如果你的场景是"小团队（5-20 人）需要通信但不想用第三方服务器"，按 [SERVER.md](https://github.com/simplex-chat/simplex-chat/blob/master/docs/SERVER.md) 部署自家 SMP server。一台 2 核 4G 的 VPS 就够，内存存储不占硬盘。配合私路由做团队内部匿名 IP 保护。
4. **谨慎扩展到敏感场景**：通过上面 3 步后，再把 SimpleX 引入真正的敏感对话。期间保持至少一个 Signal 通道作为 fallback——SimpleX 的"联系人不在线就完全联系不上"特性在跨地区/跨时区协作中很痛。
5. **不要让 SimpleX 成为唯一通道**：SimpleX 的设计哲学是"让消息消失在内存里"，这意味着**没有云端备份、没有多设备无缝同步**（5.4 之后有但体验不如 Signal）。把它当成"高敏感对话专用通道"，日常协作继续用 Signal/Slack。

## 常见问题

**SimpleX 怎么实现"无 ID"还能发消息？**

靠一次性邀请链接。链接里包含接收方队列地址和初始密钥，对方接受邀请后双方建立 pairwise 队列对。链接用完即失效，可以重发新链接"换地址"。

**Signal 已经加密了，SimpleX 比它强在哪？**

Signal 加密了"说了什么"，SimpleX 还隐藏了"跟谁说"。Signal 服务器知道你的手机号、联系人列表、通信时间；SimpleX 服务器连"两个队列是不是同一个人"都不知道。如果你只关心内容保密，Signal 够用；如果你关心"被关联"风险，SimpleX 是不同威胁模型下的工具。

**Matrix / Element 也能自建服务器，跟 SimpleX 差别在哪？**

Matrix 是联邦式协议，MXID 在所有服务器间可发现。服务器知道你在哪些房间、跟谁私聊。SimpleX 的 SMP 服务器是独立节点、不互连、不知道队列归属人。联邦 vs 独立中继是两种不同的去中心化路径。

**SimpleX 的群组能像 Signal 群那样用吗？**

能，但流量和电池开销更大。Signal 群用 server-side fan-out（服务器分发），SimpleX 是 client-side fan-out（每条消息 N 次加密投递）。小群（< 50 人）体验差异不大；大群（> 200 人）会有明显延迟和电量消耗。

**后量子密钥交换到底换了什么？**

v5.6（2024 年 3 月）开始，SimpleX 在双 ratchet 的每个 ratchet 步骤里混入后量子密钥分量（应该是 ML-KEM / Kyber 类似方案，具体见 [v5.6 公告](https://simplex.chat/blog/20240314-simplex-chat-v5-6-quantum-resistance-signal-double-ratchet-algorithm.md)）。双 ratchet 算法本身没换，升级方式跟 Apple iMessage PQ3 类似——最小侵入式叠加，而不是等"后量子 ratchet 标准"。

**怎么自建 SMP 服务器？**

按 [SERVER.md](https://github.com/simplex-chat/simplex-chat/blob/master/docs/SERVER.md) 编译 [simplexmq 仓库](https://github.com/simplex-chat/simplexmq) 的 `smp-server` 二进制，配置端口和存储。默认内存存储，不需要数据库。可以用 Docker 一键部署，也支持 reproducible build 验证。

## 自测：判断你是否掌握了 SimpleX 的核心机制

下面几个问题能帮你确认是否理解了关键判断，答案都在上文里：

1. SimpleX 与 Signal 在"加密"维度上本质差别是什么？为什么"端到端加密"对 SimpleX 是必要条件而不是充分条件？
2. "pairwise 队列"为什么能切断跨会话关联？Session 用随机 ID 做不到吗？
3. 双 ratchet 和 NaCl 附加层各自解决什么威胁？为什么要叠加而不只用其中之一？
4. SMP 服务器在协议层能看到什么、看不到什么？什么情况下服务器能看到"两个队列是同一用户"？
5. v6.0 的私路由解决了什么问题？为什么它比 Tor 的"per-connection anonymity"粒度更细？
6. SimpleX 在哪些场景下比 Signal 强？哪些场景下反而是劣势？

如果第 1、3、4 题答不上来，建议回到"核心机制拆解"和"任务流"两节重读；如果第 6 题答不上来，建议把"适用边界"一段贴在做选型决策的工作笔记里——它本身就是一张"什么场景该用什么工具"的对照表。

## 相关项目

- [simplex-chat/simplexmq](https://github.com/simplex-chat/simplexmq) — SimpleX Messaging Protocol (SMP) 和 XFTP 协议实现
- [SimpleX whitepaper](https://github.com/simplex-chat/simplexmq/blob/stable/protocol/overview-tjr.md) — 平台目标和协议设计的总览文档
- [SimpleX Chat Protocol](https://github.com/simplex-chat/simplex-chat/blob/master/docs/protocol/simplex-chat.md) — 客户端之间的消息格式
- [simplex-chat/docs](https://github.com/simplex-chat/simplex-chat/tree/master/docs) — 用户指南、服务器部署、bot API
- [Trail of Bits 审计报告](https://simplex.chat/blog/20221108-simplex-chat-v4.2-security-audit-new-website.html) — 2022 年 11 月发布的安全审计

---

> **许可证**：AGPL-3.0
> **仓库**：[simplex-chat/simplex-chat](https://github.com/simplex-chat/simplex-chat)
> **协议**：[simplex-chat/simplexmq](https://github.com/simplex-chat/simplexmq)
