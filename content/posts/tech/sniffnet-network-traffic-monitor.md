---
title: "Sniffnet：Rust 跨平台网络流量监控工具架构解析"
date: "2026-04-27T19:40:00+08:00"
lastmod: "2026-09-30T00:00:00+08:00"
slug: sniffnet-network-traffic-monitor
github_repo: "GyulyVGC/sniffnet"
source_key: "gh:GyulyVGC/sniffnet"
description: "Sniffnet 是一款用 Rust 和 iced 构建的跨平台网络流量监控工具，提供实时图表、进程归属、地理定位、端口服务识别、BPF 过滤与 PCAP 导入导出。本文对照 v1.5.1 源码解析其线程模型、编译期服务表与跨平台权限设计。"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "跨平台", "网络监控"]
---

## 快速信息卡

| 属性 | 值 |
|------|-----|
| **GitHub Stars** | 41,300+（2026-09-30 检索） |
| **GitHub Forks** | 1,900+（同上） |
| **主要语言** | Rust（edition 2024） |
| **开源协议** | MIT OR Apache-2.0 |
| **GUI 框架** | iced 0.14（v1.5.0 迁移） |
| **当前版本** | v1.5.1（2026-07-22 发布） |
| **界面语言** | 26 种 |
| **项目定位** | 面向普通用户的跨平台网络流量监控工具 |

---

# Sniffnet：Rust 跨平台网络流量监控工具架构解析

Sniffnet 真正解决的不是"怎么抓到包"——这件事 libpcap 早就做完了。它解决两件更难的事：把持续的原始字节流整理成普通人一眼能看懂的连接视图；让这条链路在 Windows、macOS、Linux 三套权限模型下都跑得通。它的架构要点，是在抓包线程和界面之间切出一条消息边界，再把跨平台的差异压进边界两侧各自的实现里。

读完这篇解析，你会带走：

- 抓包线程与界面线程的边界在哪里，为什么这样切
- 服务识别为什么选编译期烘焙成静态哈希表，代价是什么
- 三个平台的抓包权限与进程识别来源各是什么
- 什么场景该用它，什么场景该换 Wireshark

文中机制描述对照 `main` 分支 v1.5.1 源码；Stars、Fork 与版本信息检索于 2026-09-30。

---

## 目录

- [快速信息卡](#快速信息卡)
- [项目背景与定位](#项目背景与定位)
- [整体架构：两个线程域和一条消息边界](#整体架构两个线程域和一条消息边界)
- [技术选型决策分析](#技术选型决策分析)
- [服务识别的编译期烘焙](#服务识别的编译期烘焙)
- [一次数据包的完整旅程](#一次数据包的完整旅程)
- [性能与稳定性设计](#性能与稳定性设计)
- [跨平台差异处理](#跨平台差异处理)
- [开发与扩展](#开发与扩展)
- [常见问题与故障排查](#常见问题与故障排查)
- [自测题](#自测题)
- [进阶路径](#进阶路径)
- [与 Wireshark 如何取舍](#与-wireshark-如何取舍)

---

## 项目背景与定位

Sniffnet 是开发者 Giuliano Bellini（GitHub ID：GyulyVGC）用 Rust 写的开源网络流量监控应用，目前 41,300+ Stars、1,900+ Forks，支持 Windows、macOS、Linux，界面翻译覆盖 26 种语言。版本节奏可以看出来活跃度：v1.4.0（2025-06）引入 PCAP 导入和 ARP 支持，v1.4.1（2025-09）加入 BPF 过滤和 AppImage，v1.5.0（2026-04）带来进程归属、iced 0.14 迁移和适配器流量预览，v1.5.1（2026-07）补上连接延迟显示和反向 DNS 线程池。

它想服务的既不是安全研究员的取证需求，也不是运维的全流量分析平台，而是"我想知道我电脑现在到底在和谁说话"的普通用户。这个定位决定了：别人靠命令行参数完成的事，它靠界面直觉完成；也决定了它不做深度包检测——认服务靠端口号，不拆应用层载荷。

**能力一览**（版本为该能力首次出现的版本）：

| 功能 | 说明 |
|------|------|
| 适配器选择与预览 | 选择本机网络适配器；v1.5.0 起初始页可预览各适配器流量图 |
| 流量过滤 | BPF 过滤器（v1.4.1 起），也支持按 IP、端口、协议、程序的界面过滤 |
| PCAP 导入导出 | 导入自 v1.4.0 起，兼容 Wireshark 生态 |
| 实时统计 | 上下行速率、连接数、协议分布、流量环图（v1.4.0 起） |
| 地理定位 | 内置 GeoLite2 数据库，归属地与 ASN 直接可查 |
| 服务识别 | 按"端口 + 传输协议"对照 12,000+ 条映射，覆盖 6,400+ 个服务名 |
| 进程归属 | 显示产生流量的应用与图标（v1.5.0 起，三平台） |
| 连接延迟 | 显示各连接延迟（v1.5.1 起） |
| 告警通知 | 自定义规则触发系统通知；v1.4.2 起支持远程 webhook |
| IP 黑名单 | 导入自定义黑名单（v1.5.0 起），标记可疑连接 |
| 暂停恢复 | 抓包中途暂停与恢复（v1.4.2 起） |

---

## 整体架构：两个线程域和一条消息边界

读代码前，先抓住 Sniffnet 内部两个在时间尺度上完全不同的线程域：

- **抓包域（高频、节奏固定）**：原生线程 `thread_parse_packets` 跑抓包循环，读包、解析、聚合，把更新写进异步通道。这条线不碰任何界面代码。
- **界面域（低频、响应交互）**：iced 主循环消费通道里的消息，更新连接表、速率曲线和统计数字，然后重绘。

两条域之间用 `async-channel` 隔开，通道里传的是已经聚合好的流量更新（`BackendTrafficMessage`），不是单个数据包。这条边界的意义在于：抓包线程永远不等界面，界面也永远不面对原始字节。这套异步通道是 v1.4.0 引入的（PR #806），此前的耦合方式在流量大时明显吃力。

另外还有一条辅助链路：反向 DNS 查询由一个独立线程池处理（v1.5.1 改造），请求队列也走 `async-channel`，多个线程共享消费——一个慢查询不会再拖住所有域名解析。

```
[网络适配器]
     ↓ pcap 捕获（BPF 过滤在内核先行）
[thread_parse_packets]            抓包域（原生线程）
     ↓ 解析 + 聚合为流量更新
[async-channel]                   ←── 消息边界（解耦点）
     ↓ iced Subscription 收消息
[iced 0.14 主循环 update/view]     界面域
     ↓
[连接表 · 速率曲线 · 进程归属 · 国旗]
```

模块职责矩阵（路径相对仓库根目录）：

| 模块/路径 | 职责 | 关键类型 |
|------|------|----------|
| src/networking/capture.rs | 起抓包线程、装配会话、rDNS 线程池 | CaptureContext, CaptureSource |
| src/networking/parse_packets.rs | 抓包循环、etherparse 解析调度 | packet_stream, LaxPacketHeaders |
| src/networking/manage_packets.rs | 服务识别、按连接聚合统计 | get_service, InfoAddressPortPair |
| src/networking/types/program_lookup.rs | 端口→进程反查（v1.5.0 起） | ProgramLookup, Program |
| src/mmdb | GeoLite2 国家/ASN 数据库读取 | MmdbReader |
| src/chart | 实时图表渲染 | Chart, Series |
| src/notifications | 告警规则匹配与触发 | Rule, Notification |
| src/report | PCAP 导入导出的记录读写 | Savefile |
| src/gui | 页面、组件与主题 | Sniffer（iced 应用） |

---

## 技术选型决策分析

### 为什么选择 Rust

Rust 给 Sniffnet 三个实际好处，外加一条工程纪律。

**内存安全与零成本抽象的平衡。** 网络监控应用长时间运行，抓到的每个数据包都绑定到原始缓冲区的生命周期。Rust 的所有权和借用检查在编译期保证这些缓冲区在解析期间始终有效，不引入运行时开销。对一个从网卡持续灌数据的程序来说，这直接决定了它能跑多久不出事。

**多线程分发天然清晰。** 抓包线程、rDNS 线程池、端口反查线程各自持有自己的数据，跨线程只走通道。所有权模型让"谁拥有这条连接的统计"在编译期就有答案，不需要靠约定。

**二进制分发友好。** 编译产物静态链接，目标机器不需要装运行时。Windows 用户下载 MSI，macOS 用户加载 DMG，Linux 用户跑 DEB/RPM/AppImage，开箱即用。

工程纪律也在收紧：main 分支的 workspace 配置已全仓禁用 unsafe（`unsafe_code = "forbid"`），`unwrap_used`、`expect_used`、`panic` 在 clippy pedantic 之下全部设为告警——这组约束尚未随版本发布，但对一个要长期挂在用户后台跑的抓包工具，方向比功能列表更能说明态度。

### GUI 框架选型：iced

Rust 生态里的 GUI 框架有 egui、iced、relm4、dioxus 等。Sniffnet 选 iced，并且在 v1.5.0 完成了从旧版到 iced 0.14 的整体迁移（PR #1032）。选它的理由有三点。

**声明式 UI 与单向数据流。** iced 沿用 Elm 的模型：应用状态是一个纯数据结构，view 函数把它渲染成界面；用户交互产生 Message，update 函数应答消息、修改状态，状态再触发重绘。这套模型和"抓包线程持续推送状态更新"的形态天然契合——后端消息就是 Message 的一种。

```rust
// iced 的编程模型示意：view 是纯函数，update 应答消息
fn view(&self) -> Element<Message> {
    Column::new()
        .push(Text::new(&self.status))
        .push(Button::new("Start").on_press(Message::StartCapturing))
        .into()
}

fn update(&mut self, message: Message) {
    match message {
        Message::StartCapturing => self.status = "Capturing...".to_string(),
        _ => {}
    }
}
```

**渲染后端有兜底。** iced 0.14 的渲染栈同时支持 wgpu（GPU 加速）和 tiny-skia（CPU 软件渲染），两者都启用时走 fallback 组合：优先 wgpu，GPU 初始化失败自动落到 tiny-skia。对流量图表这种高频重绘的界面，GPU 渲染是主力；而对 GPU 驱动不正常的机器，软件渲染保证程序至少能用。

**跨平台控件抽象。** 按钮、输入框、下拉菜单有统一实现，一套界面代码三端通用。页面包括欢迎页（v1.5.0 起带动画）、初始页、Overview、Inspect、连接详情、Notifications、缩略图模式，以及设置页（常规/通知/外观三个子页）。

### 关键依赖分析

下表来自 v1.5.1 的 Cargo.toml，全部核实过：

| 依赖 | 版本 | 职责 |
|------|------|------|
| pcap | 2.4 | libpcap 封装，抓包会话与 BPF |
| etherparse | 0.20.3 | 链路层到传输层的协议解析 |
| async-channel | 2.5 | 抓包域与界面域之间的消息通道 |
| iced | 0.14 | GUI 框架（features：tokio、svg、lazy、image 等） |
| phf + phf_codegen | 0.14 | 编译期完美哈希表，服务识别（build.rs 生成） |
| maxminddb | 0.30 | 读取 GeoLite2 国家/ASN 数据库 |
| plotters + plotters-iced2 | 0.3 / 0.14 | 2D 图表绘制并嵌入 iced |
| listeners | 0.6 | 按（端口， 协议）跨平台反查进程 |
| picon | 0.1 | 程序图标获取 |
| dns-lookup | 3.0 | 反向 DNS 解析 |
| surge-ping | 0.9 | 连接延迟测量（v1.5.1 起） |
| confy | 2.0 | 配置持久化 |
| clap | 4.6 | 命令行参数 |
| prefix-trie | 0.9 | IP 黑名单的 CIDR 匹配 |
| rfd | 0.17 | PCAP 导入导出的文件对话框 |
| rodio | 0.22 | 通知提示音播放 |
| reqwest | 0.13 | 检查新版本 |

**抓包层：pcap crate。** Sniffnet 在 `CaptureContext` 里装配会话，实际参数如下（摘自 src/networking/types/capture_context.rs，注释为原文含义）：

```rust
let inactive = Capture::from_device(device.to_pcap_device())?;
let cap = inactive
    .promisc(false)              // 不开混杂模式，只看本机收发的流量
    .buffer_size(2_000_000)      // 2 MB 缓冲，约容 1 万个 200 字节的包
    .snaplen(if pcap_out_path.is_some() {
        i32::from(u16::MAX)      // 要写 PCAP 文件时保留完整帧（65535）
    } else {
        200                      // 平时只留每包前 200 字节
    })
    .immediate_mode(false)
    .timeout(150)                // 无包时每 150ms 返回一次，保证界面持续刷新
    .open()?;
```

注意这里有两个反直觉的选择：混杂模式是关的（监控对象就是本机，没必要收整个网段的包）；普通抓包的 snaplen 只有 200 字节——判定服务、协议、方向只需要头部，负载字节直接截掉，同样的 2 MB 缓冲就能多容 30 倍的包。只有导出 PCAP 时才把 snaplen 提到 65535 保留完整帧。BPF 过滤器只在用户填写时应用（`set_bpf`），写错会直接返回错误而不是静默忽略。

**解析层：etherparse。** v1.5.1 直接依赖 etherparse 0.20.3 做二三层解析。抓包线程先看链路类型，再选对应的解析入口（src/networking/parse_packets.rs，节选）：

```rust
match my_link_type {
    MyLinkType::Ethernet(_) => LaxPacketHeaders::from_ethernet(packet).ok(),
    MyLinkType::RawIp(_) | MyLinkType::IPv4(_) | MyLinkType::IPv6(_) => {
        LaxPacketHeaders::from_ip(packet).ok()
    }
    MyLinkType::LinuxSll(_) => from_linux_sll(packet, true),
    // ...
}
```

以太网卡走标准解析，裸 IP 接口走 `from_ip`，Linux 的 `any` 虚拟接口（SLL 链路类型，v1.4.1 起支持）有专门入口。协议覆盖 TCP、UDP、ICMPv4/v6、ARP，剥出源/目的 IP、端口、协议类型和字节数，交给上层聚合。

顺带看一眼 main 分支的动向：解析代码正在被抽成独立 crate `sniffnet-packet-parser`（基于 etherparse 0.21，新增 IGMP 与 VLAN 支持，已单独发布到 crates.io），产出统一的 `ParsedPacket` 结构。这个重构尚未随正式版本发布，读 v1.5.1 源码看到的仍是 etherparse 直接调用。

**地理定位：maxminddb + 内置数据库。** GeoLite2 的国家库和 ASN 库直接打包在安装包里（resources/DB/*.mmdb），开箱可用，不要求用户去 MaxMind 注册下载。`maxminddb` 读内存映射，单次查询微秒级，结果按 IP 缓存。

**图表：plotters + plotters-iced2。** `plotters` 负责画速率曲线和分布图，`plotters-iced2` 把它接进 iced 的渲染管线，版本号与 iced 0.14 对齐。

---

## 服务识别的编译期烘焙

Sniffnet 把"这个端口上跑的是什么服务"做成了一张编译期生成的静态哈希表，这是全项目最能体现取舍的一处。

数据源是仓库根目录的 `services.txt`：文件头写明它由 nmap 的 nmap-services 自动生成，"Don't edit this file manually"。当前 12,093 条端口/协议映射，覆盖 6,466 个不同的服务名（README 对外口径"6000+ upper layer services"，含协议、木马、蠕虫条目）。

`build.rs` 在编译期把它读进来，用 `phf_codegen` 烘焙成一张 `phf::Map<ServiceQuery, Service>`，键是 `(端口, TCP/UDP)` 二元组，生成的代码写进 `OUT_DIR/services.rs`，再由 `manage_packets.rs` include 进来。构建脚本里有硬断言：`assert_eq!(num_entries, 12093)`——条目数对不上就直接编译失败。运行时查表是 O(1)，代价是改表必须重编译，还有断言这道门。

查找逻辑比"查一次表"更讲究。`get_service` 对源、目的两个端口各查一次，然后按分数取优：

- 查到服务的端口才有分；
- 知名端口（< 1024）记 3 分，其余记 1 分；
- 远端端口加 1 分（组播/广播流量则给目的端口加 1 分）。

比如本机 52341 端口连远端 443：两端都命中时，远端 443 以"知名端口 + 远端"的 4 分胜出，连接被标为 https。这套评分解决了"源端口恰好撞上知名端口号"时的误判。另外，build.rs 还会在 debug 构建下用 rustrict 检查服务名，把 nmap 表里的不雅名称挡在编译期。

这个设计的边界也要说清：认服务靠端口对照，不做应用层指纹识别。端口上跑的不是登记协议时（比如 443 上跑非 TLS 流量），标签就会失真——这是静态表方案的固有代价，Sniffnet 选择用简单换性能和确定性。

---

## 一次数据包的完整旅程

用一个具体场景把机制串起来：你启动 Sniffnet，选了 Wi-Fi 适配器，浏览器打开 `https://example.com`。

1. 界面把可选的 BPF 过滤（比如 `tcp dst port 443`）交给会话装配，`set_bpf` 把表达式编译成内核过滤程序。不匹配的包在内核就被丢掉，不消耗用户空间拷贝。
2. `capture.rs` 起一个原生线程 `thread_parse_packets`，进入抓包循环。pcap 每次交付帧的前 200 字节，负载已经被截掉。
3. etherparse 按链路类型剥头（`LaxPacketHeaders`）：以太网头、IPv4 头、TCP 头，得到源/目的 IP、端口、协议、字节数。
4. `get_service` 拿 `(443, TCP)` 和本机临时端口各查一次 phf 表，评分后命中 `https`。
5. 这条连接的统计写进以 `AddressPortPair` 为键的聚合表：字节数、包数累加，首末时间戳更新，方向和消息类型归类。没有逐包对象长期留存。
6. 聚合更新装进 `BackendTrafficMessage`，从 `async-channel` 发出去。抓包线程立刻回去读下一个包，不等界面。
7. iced 的 Subscription 收到消息，update 更新连接表和速率统计，view 重绘——Overview 页的曲线跳一下，Inspect 页多出一行连接。
8. 如果这是条新连接：固定 5 个线程的 rDNS 线程池反查域名；`ProgramLookup` 把 `(本地端口, 协议)` 发给查找线程，listeners crate 反查归属进程，picon 取回应用图标；GeoLite2 查出国家与 ASN。几步都是异步补齐的，连接先出现，国旗、进程名随后跟上。
9. v1.5.1 起，这条连接还会显示延迟——用 surge-ping 对远端连发 3 个 ICMP 探测（单发超时 2 秒），取成功回包的平均往返时间。

九步里真正"抓"的只有第 2 步，其余全是在把抓到的字节变成"人看得懂的连接"。这也是理解 Sniffnet 架构的关键：大部分代码不是抓包，而是围绕抓包结果做的整理与呈现。

---

## 性能与稳定性设计

### Release 编译配置

Cargo.toml 的 release profile：

```toml
[profile.release]
opt-level = 3     # 最高优化级别
lto = true        # 跨 crate 链接期优化
strip = true      # 剥离调试符号
codegen-units = 1 # 单编译单元，换取更大优化空间
```

`lto = true` 让编译器跨 crate 边界内联和消除死代码，单包处理路径上的间接跳转随之减少。`codegen-units = 1` 拉长编译时间，对性能敏感的桌面应用是划算的交换。

### 缓冲与截断的配合

上面提过的三个参数合起来是套完整设计：2 MB 内核缓冲决定突发流量能攒多少包不丢；snaplen 200 让同样大的缓冲容纳约 1 万个包（源码注释原话"2MB buffer -> 10k packets of 200 bytes"）；`timeout(150)` 保证即使没有新包，pcap 读调用每 150 毫秒也返回一次，界面刷新不断档。三者的目标是同一个：突发不丢包，空闲不卡界面。

### 解耦与异步补齐

抓包线程只管产出，界面只管消费，通道满时各自节奏互不牵制。所有昂贵的补齐动作——反查域名、反查进程、查 GeoIP——都异步进行，且带缓存：进程反查结果有效 60 秒，失败后 1.5 秒重试，不会每个包都触发一次系统调用。rDNS 用线程池并发处理，v1.5.1 专门修了"一个慢查询拖住全部解析"的问题。

### 编译期兜底

main 分支的 workspace 配置已全仓禁用 unsafe，配合 clippy pedantic 告警，把内存安全和大量可疑写法挡在 CI 阶段（尚未随版本发布）。服务表的条目数断言、debug 构建的服务名审查，都在编译期把数据文件的问题拦下。运行期的错误处理走显式 Result 传递，v1.4.0 起还专门清理过一批可能崩溃的路径。

---

## 跨平台差异处理

跨平台是 Sniffnet 复杂度最高的部分。抓包读包逻辑三端共用，差异被压在"获取权限""进程识别""安装形态"三个点上。

先说进程识别，因为它最容易传错。这个能力是 v1.5.0 才引入的（PR #1056，修复的是 2019 年开的 issue #170）——在那之前，任何平台都看不到流量归属的进程。v1.5.0 起三平台统一由 listeners crate 的 `get_process_by_port` 按 `(本地端口, 协议)` 反查进程，crate 在各端调用平台专属的底层系统 API 并做缓存，Sniffnet 侧只面对一套接口。查到的进程配上 picon 取回的应用图标，出现在 Inspect 页和连接详情里。

### Windows

抓包底层依赖 npcap（libpcap 的 Windows 实现），安装 npcap 时需要勾选 WinPcap API 兼容模式；开发者构建另需 Npcap SDK 并配置 `LIB` 环境变量。运行需要管理员权限。安装包是 MSI，v1.4.1 起用 SignPath Foundation 提供的证书签名，v1.4.2 起支持 Windows ARM64。

### macOS

构建不需要装任何额外依赖，系统自带的东西就够；运行需要管理员权限。安装包是 DMG。进程识别走 listeners 的 macOS 实现。

### Linux

运行时依赖 libasound2、libpcap0.8、libfontconfig1 三个库。权限方案最灵活：RPM 包安装时自动执行授权（Cargo.toml 里写死的后安装脚本）：

```bash
setcap cap_net_raw,cap_net_admin=eip /usr/bin/sniffnet
```

DEB 装完手动跑同样命令，或者直接 `sudo -E sniffnet`。AppImage（v1.4.1 起）必须以 sudo 运行。另有 Docker 镜像（v1.4.0 起）。构建期需要 libpcap-dev、libasound2-dev、libfontconfig1-dev、libgtk-3-dev 四个开发包。

三端差异汇总：

| 平台 | 抓包底层 | 运行权限 | 安装形态 |
|------|----------|----------|----------|
| Windows | npcap | 管理员 | MSI（v1.4.1 起签名） |
| macOS | 系统 libpcap | 管理员 | DMG |
| Linux | libpcap | setcap / sudo | DEB、RPM、AppImage、Docker |

---

## 开发与扩展

### 从源码构建运行

```bash
git clone https://github.com/GyulyVGC/sniffnet.git
cd sniffnet
cargo run # 或 cargo run --release
```

首次编译的系统依赖按平台装：Linux 需要 libpcap-dev、libasound2-dev、libfontconfig1-dev、libgtk-3-dev 四个开发包，macOS 不需要额外安装，Windows 需要 Visual Studio Build Tools 加 Npcap SDK。细节以仓库 Wiki 的 Required Dependencies 页为准。

### 自定义主题

内置主题是 A11y（默认）、Dracula、Gruvbox、Nord、Solarized、Yeti 六套，各分深浅两版，另支持完全自定义调色板。主题定义在 src/gui/styles/custom_themes/ 下，按现有文件照葫芦画瓢，再在 StyleType 枚举里注册即可。

### 命令行参数

`--adapter [<NAME>]`（v1.3.2 起）直接从指定适配器开始抓包，`--config_path`（v1.5.0 起）打印配置文件路径。完整列表见 Wiki 的 Command-line arguments 页。

### 扩展服务表

`services.txt` 由 nmap-services 自动生成，文件头明确要求不要手动编辑。如果你确实要加自定义映射：改文件、重新编译，并且同步更新 build.rs 里的 `assert_eq!(num_entries, 12093)` 断言，否则编译直接失败——这道断言就是设计给"改了文件没对账"的场景的。

---

## 常见问题与故障排查

### Q: 运行时提示 "Permission denied" 怎么办？

**Linux**：给二进制授权 `sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/sniffnet`（RPM 包安装时已自动执行），或 `sudo -E sniffnet`；AppImage 必须 sudo。

**macOS / Windows**：以管理员身份运行。

### Q: 为什么看不到任何流量？

按顺序排查：适配器是否选对（通常是 Wi-Fi 或 Ethernet）；BPF 过滤是否过严（清空再试）；权限是否配置正确；所选适配器上是否真有流量。

### Q: 为什么有的连接看不到"是哪个程序发的"？

进程识别自 v1.5.0 才有，先确认版本。它是异步反查：结果缓存 60 秒、失败 1.5 秒后重试，所以存活很长的连接基本都能补上归属，而存在几秒就关闭的短连接可能在查到之前就结束了，显示为未知。这属于机制本身的取舍，不是故障。

### Q: 只抓每包前 200 字节，会不会漏信息？

对 Sniffnet 的定位不会。它做的是统计与连接视图，判定服务、协议、方向只需要各层头部，不分析应用层载荷。要看载荷内容、做流重组，那是 Wireshark 的工作，用 Sniffnet 导出 PCAP 接过去。

---

## 自测题

1. Sniffnet 的两个线程域是什么？中间的消息边界为什么必要？
2. 服务识别为什么选编译期烘焙成 phf 静态哈希表？代价是什么？运行时改 services.txt 有效吗？
3. BPF 过滤器在哪一层起作用？普通抓包时 snaplen 为什么只有 200 字节？
4. `get_service` 在两端端口都命中服务时怎么选？评分规则是什么？
5. 进程归属能力是哪个版本引入的？三个平台各自的反查来源是什么？
6. Linux 上让非 root 用户运行 Sniffnet 有哪几种方式？

<details>
<summary>参考答案</summary>

**题 1**：抓包域（`thread_parse_packets` 原生线程：读包、解析、聚合）和界面域（iced 主循环：消费消息、更新状态、重绘）。边界是 `async-channel`，传聚合好的流量更新。必要性：抓包线程永远不等界面，界面永远不面对原始字节；v1.4.0 引入。

**题 2**：12,093 条映射在 build.rs 里烘焙成 `phf::Map`，运行时 O(1) 精确查找，无运行时解析成本；代价是改表要重编译，且受 `assert_eq!(num_entries, 12093)` 断言约束。运行时改 services.txt 无效，必须重编译并同步断言。文件本身由 nmap-services 自动生成，官方不建议手改。

**题 3**：BPF 由 libpcap 编译成内核过滤程序，在内核执行，不匹配的包不进用户空间。snaplen 200 是因为判定服务和协议只需要头部，截掉负载后同样的 2 MB 缓冲能容约 1 万个包；只有导出 PCAP 时才提到 65535 保留完整帧。

**题 4**：按分数取优。查到服务才计分；知名端口（<1024）3 分、其余 1 分；远端端口（组播/广播时为目的端口）加 1 分。远端知名端口通常以 4 分胜出，避免本机临时端口撞号误判。

**题 5**：v1.5.0（PR #1056）。三平台统一走 listeners crate 的 `get_process_by_port` 按 `(本地端口, 协议)` 反查，crate 在各端调用平台专属的底层系统 API 并缓存结果；图标由 picon 提供。

**题 6**：`setcap cap_net_raw,cap_net_admin=eip` 授权二进制（RPM 安装自动做）；`sudo -E sniffnet` 直接以管理员跑；AppImage 必须 sudo；或者用 Docker 镜像。

</details>

---

## 进阶路径

按下面顺序读，每一环都建立在前一环的问题上：

1. **[Sniffnet GitHub 仓库](https://github.com/GyulyVGC/sniffnet)**：先通读 README 和 Wiki 的 Required Dependencies、Command-line arguments 两页，建立整体认知。
2. **src/networking/capture.rs 与 capture_context.rs**：抓包线程怎么起、会话参数怎么配，抓包侧的全部秘密在这两个文件里。
3. **[sniffnet-packet-parser](https://github.com/GyulyVGC/sniffnet/tree/main/lib/sniffnet-packet-parser)**：main 分支正把解析抽成的独立 crate（尚未随版本发布），基于 [etherparse](https://docs.rs/etherparse/latest/etherparse/)，想理解"如何把字节变成结构化头信息"时读。
4. **src/networking/manage_packets.rs**：`get_service` 的评分逻辑和连接聚合都在这里，是业务语义最浓的一个文件。
5. **[pcap crate 文档](https://docs.rs/pcap/latest/pcap/)** 和 **[iced 官网](https://iced.rs/)**：想深挖某一侧的底层机制时分别查阅。

---

## 与 Wireshark 如何取舍

把 Sniffnet 的定位说清楚，才知道它什么时候派得上用场。

**Wireshark 胜在深度**：完整协议解码器、流重组、应用层分析，是安全分析和协议调试的标配。代价是学习曲线陡、界面信息密度高，普通用户容易劝退。

**Sniffnet 赢在直觉**：三端图形界面、进程归属、地理定位、延迟显示、告警通知，装上就能回答"我的电脑在和谁通信"。代价是它不做深度包检测——服务靠端口对照，看不到载荷内容。

一个可行的采用顺序：

- **日常查流量、看谁在联网、简单告警** → 直接上 Sniffnet，几分钟上手。
- **排查协议问题、深挖会话、取证** → 用 Wireshark；Sniffnet 的 PCAP 导出正好喂给它继续分析。
- **两者不冲突**：Sniffnet 常驻看全貌，Wireshark 按需深挖，是验证过的高效组合。

**项目信息**（2026-09-30 检索）：

- GitHub：https://github.com/GyulyVGC/sniffnet
- 官网：https://sniffnet.app
- 当前版本：v1.5.1（2026-07-22）
- License：MIT OR Apache-2.0

---

*🦞 钳岳星君撰写 | 2026-04-27*
