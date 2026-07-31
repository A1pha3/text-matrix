---
title: "Pumpkin：用 Rust 从零构建的 Minecraft 服务器"
date: "2026-07-31T02:53:41+08:00"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "Minecraft", "游戏服务器", "性能优化", "开源"]
description: "Pumpkin 是一个完全用 Rust 编写的 Minecraft 服务器实现，以多线程性能、安全性和可扩展性为核心设计目标。"
---

## 项目概览

Pumpkin 是 Pumpkin-MC 组织下的一款完全用 Rust 编写的 Minecraft 服务端实现，副标题原文为「Empowering everyone to host fast and efficient Minecraft servers」。它既不是某个 Mojang 官方的改装，也不是某个 Java 服务的对比替代品——它从协议编解码、Tick 调度、世界存储、玩家实体到插件 ABI（Application Binary Interface，应用程序二进制接口），都试图用 Rust 与现代运行时重写一遍。GitHub 仓库当前版本号标注为 `0.1.0-dev+26.2`，意味着它仍处在 1.0 之前的快速迭代阶段，但开发节奏相当高频：默认分支 `master` 在项目存续期内持续刷新，单日多次提交。

按照其仓库约定，Pumpkin 同时支持 Java 版（通过标准 Minecraft 协议登录流程）与基岩版（Bedrock Edition，处于 W.I.P 状态）。这意味着协议层不是补丁式的「顺便兼容」，而被视为第一类公民。这也是理解 Pumpkin 的关键：它的取舍基线是「一个能跑 Vanilla 多人游戏逻辑的 Rust 服务端」，而不是「一个 Minecraft 项目的脚手架」。

## 为什么 Rust 适合重写 Minecraft 服务器

把 Minecraft 服务端放进 Rust 生态的理由，远不止「性能强」这么一句口号。Minecraft 服务端是典型的 I/O 密集、Tick 密集、状态密集三位一体的工程：

- **网络层**每秒钟要处理成百上千个玩家的封包解析、加密、压缩与广播，是高频小数据；
- **世界层**需要按 Chunk（世界划分的 16×16 方块柱）粒度做生成、加载、保存、光照、Tick，是高吞吐磁盘与内存操作；
- **逻辑层**有红石、实体行为、计划刻（Scheduled Tick）等顺序敏感的推理规则，对并发原子性与一致性高度敏感。

Rust 在这三个维度上同时给出了相对扎实的答案：所有权与借用机制让数据竞争在编译期被排除；`tokio` 提供跨线程、跨任务的异步运行时；`rayon` 给数据并行（Data Parallelism）一条数据流最干净的路径；`crossbeam` 提供无锁与有锁的同步原语；`dashmap` 让高频并发读写落到工程实践。当协议层是核心 CGo 不可避免的领域（编解码、压缩、加密），Rust 还能用 `default-features = false` 严格控制特性裁剪、再用 `#[deny]` 级别的 clippy 规则束缚面上的风格漂移。

换言之，相比「性能等于快」，Pumpkin 的真正价值在于它把 Minecraft 服务端这门工程从「堆 JVM 调参」重新拉回到「用类型系统和线程模型表达领域」的频道上。

## 核心能力与设计目标

仓库 README 显式声明了五条 Goals（设计目标），构成了对外部期待的硬边界：

1. **Performance** — 借助多线程获得最大速度与效率。这点写得很直白，没有任何附加修饰，意味着「性能」是 Pumpkin 愿意用复杂度换的指标。
2. **Compatibility** — 在坚持 Vanilla 游戏机制的前提下，支持最新 Java 版与基岩版（基岩版尚在 W.I.P）。换言之，Pumpkin 不会为了绕过 Mojang 协议而引入私有客户端。
3. **Security** — 优先防御已知安全漏洞，对应的是 Minecraft 多年来累积的协议层与账号层 CVE（Common Vulnerabilities and Exposures，公开漏洞编号）。
4. **Flexibility** — 高度可配置，能够禁用不需要的功能。这一点对小型部署尤其重要——禁掉 Plugin 容器、禁掉 Chat 渲染、禁掉 Query 协议，是常见做法。
5. **Extensibility** — 为插件开发提供底盘。这是它在性能与安全之间预留的最大一块「妥协」：插件 API 必须稳定、安全、易用。

把五条 Goals 摊开看，会发现一个有意思的取舍：性能与安全要靠 Rust 类型系统与运行时保证，而兼容性、可配置性、可扩展性则是「对外契约」。前者是写给自己的，后者是写给生态的。Pumpkin 同时押注这两条，并不是没有代价——下文「当前状态与边界」会谈到。

## 技术栈与架构信号

Pumpkin 的代码组织本身就是一种态度。仓库顶层是一个 Cargo Workspace，列出了 11 个成员 crate（除 `pumpkin-codegen` 显式被 `exclude` 之外），每个 crate 命名空间都遵循 `pumpkin-*` 前缀：

- `pumpkin` 主二进制入口，描述为「Empowering everyone to host fast and efficient Minecraft servers.」；
- `pumpkin-protocol` 协议层，处理 Java 版与基岩版的封包编解码；
- `pumpkin-codecs` 通用编解码工具集；
- `pumpkin-nbt` NBT（Named Binary Tag，Minecraft 自定义二进制格式）解析与序列化；
- `pumpkin-world` 世界区块、生成、保存与光照；
- `pumpkin-data` 方块、物品、生物群系等静态数据表；
- `pumpkin-config` TOML 配置加载；
- `pumpkin-inventory` 物品栏与容器；
- `pumpkin-util` 通用工具；
- `pumpkin-plugin-api` 插件 ABI；
- `pumpkin-macros` / `pumpkin-api-macros` 过程宏。

从 `Cargo.toml` 还能读出几条架构信号：

- **MSRV（Minimum Supported Rust Version，最低支持 Rust 编译器版本）严格**：通过 `rust-toolchain.toml` 锁到 `channel = "stable"`，额外附 `rust-analyzer` 与 `rust-src` 组件；Workspace 标记 `edition = "2024"`、`rust-version = "1.95"`——这是一个愿意吃最新版编译器红利的取向。
- **并发栈组合**：`tokio = 1.53`（默认 feature 关闭，按需开启）搭配 `rayon`、`crossbeam`、`dashmap`、`arc-swap`、`crossfire`。这套组合意味着 Pumpkin 在「CPU 密集型计算（Rayon 数据并行）」与「I/O 密集型等待（Tokio 异步任务）」之间有明确的分工，而不是把所有线程都塞进 Tokio runtime。
- **零拷贝与字节层**：`bytes = 1.12` 用作字节缓冲，`uuid` 启用 `v3/v4`、`bitflags` 启用 `std`，`lru` 内置缓存，以及 `rustc-hash` 这种比较小众但性能稳定的选择。协议层对延迟的敏感在依赖列表里一览无余。
- **加密与账号**：`rsa`、`aes`、`ctr`、`ecdsa`、`p384`、`sha1`、`sha2`、`hmac`，这一组密码学库覆盖了 Minecraft Online Mode（在线模式，玩家的连接必须验证 Mojang Session Server）的全部需要——登录挑战、签名验证、HMAC-SHA256 校验等。
- **压缩与编码**：`flate2`（zlib）、`ruzstd`（zstd）、`lz4-java-wrc`（与 Minecraft Java 客户端兼容的 LZ4 变种）。`async-compression` 兼顾异步封包压缩。Bedrock 端则用 `cfb8`，对应 RakNet 协议族的 8-bit 加密流。
- **插件 VM**：这是最值得高亮的一项。`wasmtime` 47.0 启用了 `component-model`、`async`、`gc`、`gc-drc`、`threads` 等重型 feature，配合 `wasmtime-wasi`、`wasmtime-wasi-http`、`wit-bindgen` 与 `pumpkin-plugin-wit` 仓库——构型相当完整。翻译过来：Pumpkin 计划使用 WebAssembly 组件模型（Component Model）+ WIT（WebAssembly Interface Types，组件接口描述）作为插件 ABI，让插件以 Wasm 模块形式加载，并通过 WASI P2 访问系统资源（文件、网络等）。`libloading` 的存在意味着 Pumpkin 也能加载原生动态库格式插件，但显式 Wasm 的支持路径才是差异化的主线。
- **极端静态检查**：`workspace.lints.clippy` 直接 `deny` 了 `all`、`nursery`、`pedantic`、`cargo` 四个语义组，再加 `todo`、`unreachable`、`unimplemented` 都 `deny`；`dbg_macro`、`print_stdout`、`print_stderr` 也一并 `deny`。一堆以 `redundant_`、`needless_`、`useless_` 开头的 lint 全开。这是一种用 lint 防止腐烂的工程纪律，意味着贡献者提的 PR 几乎肯定要先扛过一轮 clippy 司法。
- **发布配置**：`[profile.release]` 启用了 `lto = true`、`codegen-units = 1`、`strip = "debuginfo"`，组合出来的就是单文件、跨模块 LTO（Link-Time Optimization，链接时优化）的最小镜像——对镜像大小、启动延迟、内存占用都显眼。

World 层的 Functionality 则从 README 的 Features 列表里能看出完成的轮廓：World Loading、World Time、World Borders、World Saving、Lighting、Entity Spawning、Bossbar、Chunk Loading（Vanilla/Linear/Pump 三种实现）、Chunk Saving（Vanilla/Linear/Pump 三种实现）、Liquid Physics 等都打勾；Chunk Generation 与 Redstone 仍挂在 Issue 追踪页上。

## 当前状态与边界

必须把一段话单独留给边界。Pumpkin README 顶部那段 IMPORTANT 提示：

> Pumpkin is currently under heavy development.
> See what needs to be done before the 1.0.0 Release

这是 Pumpkin 官方背书的状态描述。把它翻译成读者应该带走的预期：

- **协议对最新版的覆盖是追赶式**。Minecraft Java 版每年若干次小版本更新，每次都可能动协议细节。Pumpkin 把支持最新版本列为目标，但同时声明「我们正追」。`Tracking: Protocol`、`Tracking: World`、`Tracking: Player` 三个 Tracking Issue 即黑盒总账。
- **Bedrock（基岩版）仍在 W.I.P**。Java 版是基本盘，Bedrock 端处于着手阶段，并不承诺时间线。
- **战斗（Combat）、红石（Redstone）、实体 AI（Entity AI）、完整生物行为**等模块仍未收尾。Villagers、Mobs、Animals、Boss 都打着 W.I.P 标记；Plugin 系统也还在 Tracking。这意味着如果你打算用作商业化的复合玩法服务器，目前 Pumpkin 远不具备 readiness。
- **Commands 仍是空缺**。这是个影响玩家体验的硬指标。
- **版本号 `0.1.0-dev+26.2`** 表白身份：每一次小迭代都在重写期。`+26.2` 这种 dev tag 一般说明模块化边界尚未稳定，依赖与 crate 拆分随时会调整。

换个角度来说，Pumpkin 的「未完成」是写在基因里的——它用 Rust 2024 edition、用 `default-features = false` 严格控制依赖、用 `deny` 级别的 lint 防止腐烂，但是它的功能集与协议范围都还在追赶阶段。换句话说，**它是工程可能性更高、版本成熟度更低**的项目。

## 适用人群

把以上所有信号综合起来，Pumpkin 适合哪一类读者，决定了它对你是宝藏还是噪声：

- **Rust 工程师 + 游戏服务器研究者**：如果你想看一个完整用现代 Rust 写大规模网络服务的 reference，Pumpkin 提供了协议层、Tick 调度、并发原语的真实使用样本；Workspace、Lint 策略、Release Profile 都值得当研究骨架。
- **小型 Vanilla 玩家圈**：能容忍「偶尔手动更新协议 patch」的小团体，可以用 Pumpkin 跑一个 Vanilla 体验、低资源占用的私域联机服务器。
- **Minecraft 生态插件开发者**：如果能等到 Pumpkin 1.0 之后 Plugin API 稳定，Wasm + WIT 加载路径与 WASI P2 意味着插件既可以沙箱化运行，又能在权限边界内访问必要系统调用——这是一种比 Java 插件更现代的形态。
- **反向选择**：如果你要跑 Bukkit/Spigot/Paper 那一套成熟生态、要离线模式公网运营、要完整红石与命令系统、要即插即用的大型商业服务器，Pumpkin 还远不是答案。

## 一句话总结

Pumpkin 用 Rust 走了一条「重写 Minecraft 服务端」的工程之路，押注多线程性能、协议兼容、内存安全与基于 Wasm 组件模型的插件 ABI。它目前仍是 0.1.0-dev 阶段，处于重度开发中——读者获得的不是稳定生产方案，而是一个值得跟进的现代服务端骨架。对愿意为「类型系统和线程模型」付学费的工程读者而言，Pumpkin 是当下最值得花一个晚上通读 `Cargo.toml` 的游戏服务器项目之一。
