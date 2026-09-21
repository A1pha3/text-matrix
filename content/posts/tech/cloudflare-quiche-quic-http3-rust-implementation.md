---
title: "cloudflare/quiche 源码拆解：QUIC 与 HTTP/3 的 Rust 工业级实现"
date: 2026-09-22T03:35:00+08:00
slug: "cloudflare-quiche-quic-http3-rust-implementation"
github_repo: "cloudflare/quiche"
source_key: "gh:cloudflare/quiche"
description: "quiche 是 Cloudflare 用 Rust 写的 QUIC 传输协议与 HTTP/3 实现，支撑着 Cloudflare 边缘网络的 HTTP/3 流量，也被 Android 系统 DNS 解析器和 curl 采用。本文从 API 设计取舍、零拷贝内核、C FFI 与 BoringSSL 集成三个维度拆解这个工业级协议栈。"
draft: false
categories: ["技术笔记"]
tags: ["Cloudflare", "QUIC", "HTTP/3", "Rust", "网络协议", "BoringSSL", "开源项目"]
---

## 核心判断

[cloudflare/quiche](https://github.com/cloudflare/quiche)（约 12.3k stars，Rust，BSD-2-Clause）是一个 QUIC 传输协议与 HTTP/3 的开源实现，遵循 IETF 规范。但它最值得读的不是"又一份协议实现"，而是它对"协议库应该长什么样"这个问题给出的答案：**库只管协议状态机，I/O 与事件循环完全交给应用**。

这个设计决策直接决定了它的三个知名用户：

- **Cloudflare 边缘网络**的 HTTP/3 支持由 quiche 驱动，官方测试站 [cloudflare-quic.com](https://cloudflare-quic.com) 可直接体验
- **Android 系统 DNS 解析器**用它实现 DNS over HTTP/3（见 Google 安全博客 2022 年的介绍）
- **curl** 的 HTTP/3 构建文档里，quiche 是官方支持的三个 QUIC 后端之一

## 它解决什么问题

QUIC（RFC 9000）不是"跑在 UDP 上的 TCP"，它把传输层握手、TLS 1.3 握手、流多路复用、拥塞控制全部折叠进用户态。这意味着实现一个 QUIC 栈要同时吃透三样东西：TLS 密码学、可靠传输状态机、以及操作系统 UDP 收发的所有坑（GSO、ECN、MTU 探测、包大小协商）。

自己从零写一个能跑生产的 QUIC 栈，团队级投入以年计。quiche 把这件事变成了一个 `cargo add quiche` 就能拿到（或一个静态链接的 `libquiche.a`）的组件。

## API 设计：库不做 I/O

quiche README 的第一段就把设计哲学说清楚了：

> The application is responsible for providing I/O (e.g. sockets handling) as well as an event loop with support for timers.

翻译成架构语言：quiche 是一个**纯协议状态机库**，不是网络框架。`Connection` 对象暴露两个核心方法：

```rust
// 应用从 socket 读到数据后，喂给协议状态机
let read = conn.recv(&mut buf[..read], quiche::RecvInfo { from, to })?;

// 协议状态机生成待发数据，应用自己决定怎么发出去
let (write, send_info) = conn.send(&mut out)?;
socket.send_to(&out[..write], &send_info.to)?;
```

`recv()` 吃进原始 UDP 载荷，`send()` 吐出待发包。中间没有 epoll、没有 tokio、没有线程——那些是应用层的事。

这个取舍的收益是**嵌入性**：Cloudflare 的边缘服务器有自己的事件循环和内存模型，curl 有另一个，Android DNS 解析器又有第三个。quiche 不预设运行时，三边都能塞进去。代价是用起来比"开箱即用的 QUIC 服务器"繁琐——你必须自己维护定时器（`conn.timeout()` 查询下次到期时间，到期后调 `on_timeout()`），自己实现发送节奏（pacing）。

## 关键实现细节

### TLS 层：BoringSSL 而非 rustls

QUIC 的握手强制要求 TLS 1.3，且需要从 TLS 栈里抽取加密级别的密钥材料（QUIC 对初始包、握手包、应用数据用不同密钥加密）。quiche 选择链接 **BoringSSL**（通过 `boring-sys` crate，构建时自动完成，依赖 cmake），而不是纯 Rust 的 rustls——因为当时 rustls 尚未暴露 QUIC 所需的底层密钥 API。这也解释了为什么编译 quiche 需要 cmake，Windows 上还需要 NASM。

已有自定义 BoringSSL 构建的用户可以用 `BORING_BSSL_PATH` 环境变量接管。

### 拥塞控制与 pacing 提示

发送侧实现了 RFC 9002 拥塞控制，并且把 pacing（发包节奏控制，避免突发造成瞬时丢包）做成了**提示而非强制**：`send()` 返回的 `SendInfo` 结构体带一个 `at` 字段，表示这个包"应该"在什么时刻进入网络。应用可以忽略它，也可以对接 Linux 的 `SO_TXTIME` socket 选项让内核按时发包。库建议但不强制——又是同一个哲学。

### C FFI：让 C/C++ 生态直接链接

cargo build 时会自动产出一个独立的静态库 `libquiche.a`，C/C++ 应用直接链接即可（需 `--features ffi` 开启）。C API 与 Rust API 设计一致，"只受 C 语言本身的约束"。这条路径是 curl 和 Android 能采用它的前提——它们都不可能引入 Rust 运行时。

### h3 模块与 h3i

HTTP/3 语义在独立的 `quiche::h3` 模块里，提供高层 API 收发 HTTP 请求响应。仓库还维护 h3i（一个 HTTP/3 内省工具，最近刚发布 0.7.0），以及 quiche-apps 里的 `quiche-client` / `quiche-server` 命令行工具（官方明确声明：演示用，不保证生产级安全与性能）。

## 上手路径

```bash
git clone https://github.com/cloudflare/quiche
cargo build --examples   # 需要 cmake（BoringSSL 构建依赖）
cargo run --bin quiche-client -- https://cloudflare-quic.com/
```

代码里最值得按顺序读的三块：

1. `quiche/src/lib.rs` 的 `Config` —— 看 QUIC 有多少参数没有合理默认值（并发流数、流控窗口全部默认为 0，应用必须显式设置 `set_initial_max_data()` 等一系列方法），这是 QUIC "通用传输协议" 定位的直接体现
2. `Connection::recv()/send()` 的调用方（`quiche/examples/` 目录）—— 30 行看懂库与应用的边界
3. `quiche/include/quiche.h` —— 对照 Rust API 看 FFI 层如何做语言间映射

## 适合谁、不适合谁

**适合**：需要在自己的网络服务里嵌 QUIC/HTTP/3 能力（尤其是 C/C++ 或 Rust 项目）；想读一份生产级、规范对齐的 QUIC 源码；做协议研究或 fuzzing。

**不适合**：想要一条命令起 HTTP/3 服务器直接对外服务的场景——那是 nginx / Caddy 这类服务器的职责（它们各自集成自己的 QUIC 实现）；以及需要纯 Rust 依赖树（无 BoringSSL）的项目。

## 维护状态

Cloudflare 全职维护，master 分支持续活跃（最近提交 2026-09-21，FFI 层为 PathStats 填充 max_rtt），最新 release 0.30.0（2026-09-17）。Docker 镜像 `cloudflare/quiche` 每次 master 更新自动发布。

## 一句话总结

quiche 用"库管协议、应用管 I/O"的极简边界，加上 Rust 安全性 + C FFI 可达性的组合，成了 QUIC 生态里被验证最多的开源实现之一。读它的源码，学的不是 QUIC 规范本身，而是如何把一个复杂协议栈设计成别人愿意嵌入的组件。
