---
title: "bitchat-android：蓝牙 Mesh 与 Nostr 双传输的去中心化聊天 Android 实现"
date: 2026-08-03T03:28:00+08:00
slug: "permissionlesstech-bitchat-android-dual-transport-mesh-chat"
github_repo: "permissionlesstech/bitchat-android"
description: "bitchat-android 是 permissionlesstech/bitchat 的 Android 客户端，采用蓝牙 LE Mesh 和 Nostr 双传输架构实现去中心化 P2P 聊天。无需账号、无需手机号、无中心服务器，支持端到端加密、多跳中继和地理位置频道。"
draft: false
categories: ["技术笔记"]
tags: ["Android", "去中心化", "Bluetooth Mesh", "Nostr", "端到端加密"]
---

## 核心判断

大多数即时通讯 App 的架构假设是：有一台中心服务器，所有人连上去。bitchat-android 不做这个假设。它的默认工作模式是蓝牙局域网——手机和手机之间通过 Bluetooth LE 直接通信，不需要互联网，不需要基站，不需要任何服务器。当互联网可用时，它通过 Nostr 协议扩展到全球中继。

这不是一个"离线模式"的补充功能。双传输架构是系统的第一设计原则，两种传输各自独立运作，由统一的路由层根据可达性自动切换。

## 仓库概况

- **仓库**：permissionlesstech/bitchat-android
- **Stars**：7.3k | **Forks**：1.8k | **Watchers**：91
- **协议**：GPL-3.0
- **Commits**：765
- **语言**：Kotlin, Jetpack Compose (Material 3), MVVM
- **最低 SDK**：API 26+ (Android 8.0)
- **iOS/macOS 互通**：二进制协议兼容

## 双传输架构

bitchat-android 的通信层由两条独立传输通道组成，上层通过 `UnifiedMeshService` 统一管理。

### 传输 1：蓝牙 LE Mesh（离线）

| 维度 | 设计 |
|------|------|
| 通信范围 | 蓝牙直连范围内（通常 10-30 米） |
| 中继 | 多跳中继，最多 7 跳 |
| 发现 | 自动发现附近设备并建立连接 |
| 分片 | 紧凑二进制包格式，支持分片和 TTL 路由 |
| 去重 | 数据包级去重，避免中继环 |
| 省电 | 自适应占空比 cycling + 连接数限制 |
| 后台 | `MeshForegroundService` 前台服务保持 Mesh 存活 |

蓝牙 Mesh 层的设计要点是：它不是一个广播式 ping 网络。每两个设备之间建立 Noise Protocol 加密会话，身份由静态密钥派生。这意味着即使物理层是开放的蓝牙信号，中间节点也无法读取内容——它们只能看到加密后的中继包。

### 传输 2：Nostr 协议（互联网）

| 维度 | 设计 |
|------|------|
| 通信范围 | 全球（通过公共中继） |
| 位置频道 | 基于 geohash 的地理聊天室 |
| 密钥 | 每个地理区域使用临时密钥对 |
| 私信降级 | Mesh 不可达时，私信通过 Nostr 回退投递 |

Nostr（Notes and Other Stuff Transmitted by Relays）是一个简单的事件发布/订阅协议。bitchat-android 不是用 Nostr 做"又一个聊天服务器"——它利用 Nostr 中继的广播特性来实现地理位置相关的群组通信和 Mesh 不可达时的消息投递。

### 统一路由

`MessageRouter` 是双传输的调度核心。它的职责是：

1. 判断目标对端的可达性（Mesh 还是 Nostr）
2. 选择最优传输通道
3. 管理消息队列和重试
4. 对端不可达时缓存并在恢复后投递

开发者不需要手动选择传输方式。系统自动判断，用户感知到的只是"消息发出去了"。

## 加密层

| 通信场景 | 加密方案 |
|----------|----------|
| Mesh 私信 | Noise Protocol（XX 模式，X25519 + ChaCha20-Poly1305） |
| 群组频道 | Argon2id + AES-256-GCM（密码保护） |
| Nostr 通信 | Nostr 原生事件签名 |

Noise Protocol 的 XX 模式提供前向保密（forward secrecy）——即使长期密钥未来被泄露，此前会话的内容也无法解密。这是比简单 AES 加密更强的安全模型，与 Signal Protocol 的设计思路一脉相承。

群组频道使用 Argon2id 做密码密钥派生——这是一种内存困难的 KDF（Key Derivation Function），抵抗暴力破解。密码保护的频道意味着即使 Nostr 中继被监控，没有密码的观察者也看不到内容。

## Wi-Fi Aware 传输

除了蓝牙 Mesh 和 Nostr，bitchat-android 还支持 Wi-Fi Aware（NAN，Neighbor Awareness Networking）作为第三条本地传输：

- 更高带宽（相比 BLE）
- 设备需要硬件支持
- 在支持的设备上自动启用

三条传输通道（BLE Mesh、Wi-Fi Aware、Nostr）的优先级和切换由 `UnifiedMeshService` 管理。

## Android 工程栈

bitchat-android 的技术选型代表了 2025-2026 年 Android 原生开发的主流实践：

| 层级 | 选型 |
|------|------|
| UI | Jetpack Compose + Material 3 |
| 架构 | MVVM |
| 异步 | Kotlin Coroutines + Flow |
| 网络 | 全链路 Coroutines/Flow 驱动 |
| 后台 | Foreground Service（保活 Mesh） |
| 加密 | NoiseSessionManager 管理会话 |

核心组件：

- `BluetoothMeshService` / `WifiAwareMeshService`：传输层实现
- `UnifiedMeshService`：传输选择和统一管理
- `NoiseSessionManager`：加密会话生命周期管理
- `MessageRouter`：消息路由（Mesh/Nostr 切换 + 重试队列）

## 构建

```bash
git clone https://github.com/permissionlesstech/bitchat-android.git
cd bitchat-android
./gradlew assembleDebug
```

安装到设备：

```bash
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

App 会在运行时请求蓝牙、位置（BLE 扫描必需）和通知权限。

### 可复现构建

Release APK 和 Android App Bundle 可以在固定的 Linux 容器中逐字节重建。这意味着任何人都可以验证 GitHub Release 上的 APK 与源码一致——这是一个安全敏感项目的重要信任锚。

## Tor 支持

内置 Tor（Arti 实现）用于隐私敏感的互联网连接场景。这意味着即使通过 Nostr 中继通信，网络层也可以走 Tor 隐藏路径，避免 IP 暴露。

## IRC 风格命令

bitchat-android 保留了 IRC 风格的命令交互：

- `/join` 加入频道
- `/msg` 发送私信
- `/who` 查看在线用户

这个设计选择反映了项目的定位：面向技术用户，不做"傻瓜化"，保持操作的透明度和可控性。

## 紧急擦除

三击屏幕触发 Emergency Wipe——即时清除所有本地数据（消息、密钥、配置）。这是面向高风险场景（记者、活动人士、隐私敏感用户）的功能，在普通聊天 App 中几乎不存在。

## 测试策略

```bash
./gradlew test              # 单元测试
./gradlew lint              # 静态检查
./gradlew connectedAndroidTest  # 设备测试
```

README 明确指出 BLE Mesh 的无线电级行为难以在模拟器中复现——协议和会话逻辑由单元测试覆盖，但射频层面的行为需要真实设备。这是蓝牙开发中的常见限制，能主动说明这一点说明开发团队对测试边界有清晰认知。

## 与 bitchat 主仓的关系

bitchat 主仓（已写过技术文章）是跨平台的核心实现，包含协议定义和 iOS/macOS 客户端。bitchat-android 是独立的 Android 原生实现：

- 二进制协议兼容（可以与 iOS/macOS 客户端互通）
- 但代码库独立，不是跨平台共享代码
- 使用 Kotlin 而非跨平台方案（如 React Native 或 Flutter）

选择原生 Kotlin + Compose 而非跨平台框架，对于蓝牙 Mesh 这种深度依赖平台底层 API 的场景是合理的——蓝牙 BLE 的后台执行模型、前台服务限制和省电策略在 Android 上有大量平台特定的处理逻辑。

## 采用建议

**适合**：隐私敏感用户、离线场景（户外活动、灾难恢复、无网络环境）、去中心化通信研究者、Android 蓝牙 Mesh 开发者。

**不适合**：需要中心化管理的团队协作场景、依赖云端历史同步的常规用户、iOS 为主的技术栈（虽然协议兼容，但本仓库是纯 Android 实现）。

**注意**：蓝牙 Mesh 的实际性能受物理环境影响极大——设备密度、障碍物、其他蓝牙设备干扰都会影响中继质量。7 跳上限是协议层限制，不代表所有场景都能达到。
