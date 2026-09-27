---
title: "cloudflare/quiche 解读：库只管协议状态机，I/O 交给应用"
date: 2026-09-22T03:35:00+08:00
lastmod: 2026-09-27T00:00:00+08:00
slug: "cloudflare-quiche-quic-http3-rust-implementation"
github_repo: "cloudflare/quiche"
source_key: "gh:cloudflare/quiche"
description: "quiche 是 Cloudflare 用 Rust 写的 QUIC 传输协议与 HTTP/3 实现，支撑着 Cloudflare 边缘网络的 HTTP/3 流量，也被 Android 系统 DNS 解析器和 curl 采用。本文从「库不做 I/O」的 API 设计、BoringSSL 集成、C FFI 边界与 crate 生态布局四个维度拆解这个工业级协议栈。"
draft: false
categories: ["技术笔记"]
tags: ["Cloudflare", "QUIC", "HTTP/3", "Rust", "网络协议", "BoringSSL", "开源项目"]
---

## 核心判断

[cloudflare/quiche](https://github.com/cloudflare/quiche)（12,626 stars，Rust，BSD-2-Clause）是一个 QUIC 传输协议与 HTTP/3 的开源实现，遵循 IETF 规范。但它最值得读的不是"又一份协议实现"，而是它对"协议库应该长什么样"这个问题给出的答案：**库只管协议状态机，I/O 与事件循环完全交给应用**。

这个设计决策直接决定了它的三个知名用户：

- **Cloudflare 边缘网络**的 HTTP/3 支持由 quiche 驱动，官方测试站 [cloudflare-quic.com](https://cloudflare-quic.com) 可直接体验
- **Android 系统 DNS 解析器**用它实现 DNS over HTTP/3（见 Google 安全博客 2022 年的介绍）
- **curl** 的 HTTP/3 构建文档把 quiche 列为两种 QUIC 后端之一（另一种是 ngtcp2，且文档明确说目前只有 ngtcp2 不算实验性）

## 一个仓库，两层协议，一圈配套工具

读源码之前先看地图。这个仓库不只有 quiche 一个 crate，workspace 里挂着 11 个成员，职责分三层：

| 层 | crate | 职责 |
| --- | --- | --- |
| 协议本体 | `quiche` | QUIC 状态机 + HTTP/3 语义（`quiche::h3` 模块） |
| 运行时桥接 | `tokio-quiche` | 把 `Connection` 接到 tokio 事件循环，给不想手写事件循环的应用 |
| 配套工具与基础件 | `apps`、`h3i`、`octets`、`qlog`、`qlog-dancer`、`netlog`、`buffer-pool`、`datagram-socket`、`task-killswitch` | 演示用命令行工具、HTTP/3 调试器、零拷贝包解析、日志与缓冲等支撑件 |

表中每个 crate 的职责描述都来自其 `Cargo.toml` 的 description 字段，比如 `octets` 的官方定位就是 "Zero-copy abstraction for parsing and constructing network packets"。后文的机制拆解按这张地图展开。

## 它解决什么问题

QUIC（RFC 9000）不是"跑在 UDP 上的 TCP"，它把传输层握手、TLS 1.3 握手、流多路复用、拥塞控制全部折叠进用户态。这意味着实现一个 QUIC 栈要同时吃透三样东西：TLS 密码学、可靠传输状态机、以及操作系统 UDP 收发的所有坑（GSO、ECN、MTU 探测、包大小协商）。

自己从零写一个能跑生产的 QUIC 栈，团队级投入以年计。quiche 把这件事变成了一个 `cargo add quiche` 就能拿到（或一个静态链接的 `libquiche.a`）的组件。

## API 设计：库不做 I/O

quiche README 的第一段就把设计哲学说清楚了：

> The application is responsible for providing I/O (e.g. sockets handling) as well as an event loop with support for timers.

落到代码上，`Connection` 对象只暴露一对收发方法：

```rust
// 应用从 socket 读到数据后，喂给协议状态机
let read = conn.recv(&mut buf[..read], quiche::RecvInfo { from, to })?;

// 协议状态机生成待发数据，应用自己决定怎么发出去
let (write, send_info) = conn.send(&mut out)?;
socket.send_to(&out[..write], &send_info.to)?;
```

`recv()` 吃进原始 UDP 载荷，`send()` 吐出待发包。中间没有 epoll、没有 tokio、没有线程——那些是应用层的事。

这个取舍的收益是**嵌入性**：Cloudflare 的边缘服务器有自己的事件循环和内存模型，curl 有另一个，Android DNS 解析器又有第三个。quiche 不预设运行时，三边都能塞进去。代价是用起来比"开箱即用的 QUIC 服务器"繁琐——你必须自己维护定时器（`conn.timeout()` 查询下次到期时间，到期后调 `on_timeout()`），自己实现发送节奏（pacing）。

官方也知道这个代价。仓库里的 `tokio-quiche` crate 就是官方给的台阶：它把 `quiche::Connection` 和 `quiche::h3::Connection` 接进 tokio 的事件循环，想用现成异步运行时的项目不必从零手写。同在 workspace 的 `apps` crate 还提供了 `quiche-client` / `quiche-server` 命令行工具，但官方在免责声明里写明：它们只是演示 API 用法的例子，不做性能、安全或可靠性保证。

## 一次 HTTP/3 请求怎么流过 quiche

把上面的抽象串起来。`quiche-client` 向 `cloudflare-quic.com` 发一个请求，完整生命周期是这样的：

1. **建配置**：`Config::new(PROTOCOL_VERSION)` 指定 QUIC 版本，`set_application_protos()` 声明 ALPN（应用层协议协商，告诉对端跑什么协议）——HTTP/3 的标识是 `h3`，quiche-client 源码 `common.rs` 里写的就是 `[b"h3"]`。QUIC 是通用传输协议，很多参数没有合理默认值——并发流数、各类流控窗口在 quiche 里默认全是 0，应用必须按自己的场景调 `set_initial_max_data()`、`set_initial_max_streams_bidi()` 这一系列 setter，否则连接建立后基本传不了数据。
2. **建连接**：客户端走 `connect()` 工具函数拿到一个 `Connection`。
3. **握手循环**：应用进入事件循环——`socket.recv_from()` 读到 UDP 包就喂给 `conn.recv()`；然后反复调 `conn.send()`，把吐出的每个包按 `send_info.to` 写回 socket。TLS 1.3 握手就藏在这一来一回里。
4. **发请求**：`conn.is_established()` 为真后，应用改用 `quiche::h3` 的高层 API 发出 HTTP 请求；底层则是往 QUIC 流里 `stream_send()` 写数据。
5. **收响应**：`conn.readable()` 返回有数据可读的流集合，逐个 `stream_recv()` 取出，再交给 h3 层解析成 HTTP 响应。
6. **定时与节奏**：每轮循环用 `conn.timeout()` 查下次超时时刻并挂一个定时器，到期调 `on_timeout()` 让协议状态机处理丢包重传，随后再 `send()` 补发包。发包节奏由应用掌握——`send()` 返回的 `SendInfo.at` 会提示每个包"应该"何时进入网络。

整个过程中 quiche 从不碰 socket。这就是"库不做 I/O"六个字在真实请求里的样子。

## 关键实现细节

### TLS 层：BoringSSL 而非纯 Rust 栈

QUIC 的握手强制要求 TLS 1.3，且需要从 TLS 栈里抽取加密级别的密钥材料（QUIC 对初始包、握手包、应用数据用不同密钥加密）。quiche 选择链接 **BoringSSL**（通过 `boring-sys` crate，构建时自动完成，依赖 cmake）。Cloudflare 在发布 quiche 的博客里给过理由：他们自己的 HTTPS 栈早已迁到 BoringSSL，而 BoringSSL 恰好提供了 QUIC 需要的专用握手 API——"so it made sense that our QUIC implementation would also use BoringSSL to implement that part of the protocol"。

这也解释了构建依赖：编译 quiche 需要 cmake，Windows 上还需要 NASM。已有自定义 BoringSSL 构建的用户可以用 `BORING_BSSL_PATH` 环境变量接管。

### 包解析：octets 的零拷贝抽象

协议状态机高频做的一件事是解析字节流，quiche 把这件事抽成了独立的 `octets` crate——官方描述为"解析与构造网络包的零拷贝抽象"。解析器直接在现有缓冲区上切片取值，不为每个字段重新分配内存；想往包里写数据时，它也提供带边界检查的写入端。这是理解 quiche 源码时绕不开的基础件，`Connection` 的收发路径里到处是它的身影。

### 拥塞控制与 pacing 提示

发送侧实现了 RFC 9002 拥塞控制，并且把 pacing（发包节奏控制，避免突发造成瞬时丢包）做成了**提示而非强制**：`send()` 返回的 `SendInfo` 结构体带一个 `at` 字段，表示这个包"应该"在什么时刻进入网络。应用可以忽略它，也可以对接 Linux 的 `SO_TXTIME` socket 选项让内核按时发包。库建议但不强制——又是同一个哲学。

### C FFI：让 C/C++ 生态直接链接

cargo build 时会自动产出一个独立的静态库 `libquiche.a`，C/C++ 应用直接链接即可（需 `--features ffi` 开启，默认关闭）。C API 与 Rust API 设计一致，"只受 C 语言本身的约束"。这条路径是 curl 和 Android 能采用它的前提——它们都不可能引入 Rust 运行时。

仓库自带的示例也照着这条路径配平：`quiche/examples/` 里除了 Rust 版的 client/server，还有 `client.c`、`http3-server.c` 等 C 版本，两边对照着读就能看清 FFI 层怎么映射。

### h3 模块与 h3i 调试器

HTTP/3 语义在独立的 `quiche::h3` 模块里，提供收发 HTTP 请求响应的高层 API。仓库还维护 [h3i](https://github.com/cloudflare/quiche/tree/master/h3i)（2026-09-17 发布 0.7.0）：一个交互式命令行工具加库，面向低层 HTTP/3 调试与测试。它的特别之处是可以故意违反 RFC 规则——在任意流上以任意顺序发帧、随时 reset 流——用来探测服务器对畸形报文的容忍度。官方明确声明 h3i 不打算做成生产 HTTP/3 客户端，定位就是调试器。

## 上手路径

```bash
git clone https://github.com/cloudflare/quiche
cargo build --examples   # 需要 cmake（BoringSSL 构建依赖），Rust 1.88+
cargo run --bin quiche-client -- https://cloudflare-quic.com/
```

代码里最值得按顺序读的三块：

1. `quiche/src/lib.rs` 的 `Config` —— 看 QUIC 有多少参数没有合理默认值（并发流数、流控窗口全部默认为 0，应用必须显式调用 `set_initial_max_data()` 等一系列 setter），这是 QUIC "通用传输协议" 定位的直接体现
2. `quiche/examples/client.rs` 里 `recv()`/`send()` 的事件循环 —— 对照 README 的 "Handling incoming packets" 一节，十几行看懂库与应用的边界
3. `quiche/include/quiche.h` —— 对照 Rust API 看 FFI 层如何做语言间映射

要部署到移动端，README 也给了现成路径：Android 走 cargo-ndk（NDK 19+，最低 API level 21），iOS 走 cargo-lipo，都带 `--features ffi`。

## 适合谁、不适合谁

**适合**：需要在自己的网络服务里嵌 QUIC/HTTP/3 能力的项目（Rust 项目直接依赖，C/C++ 项目走 FFI）；想读一份生产级、规范对齐的 QUIC 源码的人；做协议研究或 fuzzing 的团队（仓库自带 `fuzz/` 目录，h3i 也能当探测工具用）。

**不适合**：想要一条命令起 HTTP/3 服务器直接对外服务的场景——那是 nginx / Caddy 这类服务器的职责（nginx 用自己的 QUIC 实现，Caddy 用 Go 生态的 quic-go）；以及强制要求纯 Rust 依赖树（不许出现 BoringSSL）的项目。

## 维护状态

Cloudflare 全职维护，master 分支持续活跃（最近提交 2026-09-21，FFI 层为 PathStats 填充 max_rtt），最新 release 0.30.0（2026-09-17），同一批还发了 h3i 0.7.0 与 tokio-quiche 0.20.0。Docker 镜像 `cloudflare/quiche`（含 server/client）与 `cloudflare/quiche-qns`（互操作性测试用）的 latest 标签随 master 更新自动刷新。

## 采用建议

按需求从轻到重：

1. 只想体验或验证 HTTP/3 连通性：打开 [cloudflare-quic.com](https://cloudflare-quic.com)，或用 quiche-client 发一个请求，五分钟的事。
2. Rust 项目要嵌 QUIC/HTTP/3：直接用 `quiche` crate；除非有特殊理由，事件循环交给 `tokio-quiche`。
3. C/C++ 项目：开 `--features ffi` 链接 `libquiche.a`，照 `examples/` 里的 C 示例写胶水层。
4. 只需要一个 HTTP/3 网站或反代：不必碰 quiche，nginx 或 Caddy 更合适；要给 curl 配 HTTP/3 后端做实验则注意 quiche 后端目前是实验性的。

## 一句话总结

quiche 用"库管协议、应用管 I/O"的极简边界，加上 Rust 安全性 + C FFI 可达性的组合，成了 QUIC 生态里被验证最多的开源实现之一。读它的源码，学的不是 QUIC 规范本身，而是如何把一个复杂协议栈设计成别人愿意嵌入的组件。

## 参考来源与口径说明

- 仓库元数据（stars 12,626、forks 1,149、BSD-2-Clause 许可证）：GitHub API，2026-09-27 读数。
- 版本锚点：0.30.0（2026-09-17）。文中的 API、默认值、构建要求与免责声明均以此版本前后的 master 分支为准；最近提交 2026-09-21（`ffi: populate max_rtt in PathStats`）来自 commits API。
- 设计哲学引文、`recv()`/`send()` 示例、pacing 与 `SO_TXTIME`、Config 默认值为 0 的说明、构建要求（Rust 1.88+、cmake、Windows 需 NASM、`BORING_BSSL_PATH`）、移动端构建、免责声明原文：master 分支 README.md 当前版本，逐节核对。
- 各 crate 职责描述：各 crate `Cargo.toml` 的 `description` 字段原文。
- curl 后端与实验性标注：curl/curl 仓库 master 分支 `docs/HTTP3.md` 当前版本。
- BoringSSL 选择理由：Cloudflare 博客《Enjoy a slice of QUIC and Rust》（2019-01-22）。
- Android DNS over HTTP/3：Google 安全博客（2022-07）。
- 本文为项目解读与使用判断，非官方文档；英文引文均为原文及其中文翻译。
