---
title: "Pumpkin：用 Rust 从零构建的 Minecraft 服务器"
date: "2026-07-31T02:53:41+08:00"
draft: false
categories: ["技术笔记"]
tags: ["Rust", "Minecraft", "游戏服务器", "性能优化", "开源"]
description: "Pumpkin 是一个完全用 Rust 编写的 Minecraft 服务器实现，以多线程性能、安全性和可扩展性为核心设计目标。"
slug: pumpkin-mc-rust-minecraft-server-guide

---

## 一句话判断

Pumpkin 是一个仍处于 `0.1.0-dev` 阶段、重度开发中的 Rust 版 Minecraft 服务端。它最大的价值不在「现在能不能跑」，而在把「用 Java 堆了几年的服务端工程」重新放进类型系统和线程模型的框架里看一遍。本文读完，你会知道它想解决什么、凭什么解决、现在缺什么，以及该不该跟。

## 项目概览

Pumpkin 隶属于 Pumpkin-MC 组织，副标题原文是「Empowering everyone to host fast and efficient Minecraft servers」。它不是 Mojang 官方改装，也不是某个 Java 服务端的对比竞品——协议编解码、Tick 调度、世界存储、玩家实体、插件 ABI（Application Binary Interface，应用程序二进制接口）整套都用 Rust 与现代运行时重写。

仓库版本号标注为 `0.1.0-dev+26.2`，仍在 1.0 之前的快速迭代期。开发节奏很高频：默认分支 `master` 经常一天多次提交。

按仓库约定，Pumpkin 同时接受 Java 版（走标准 Minecraft 协议登录）与基岩版（Bedrock Edition，W.I.P 状态）客户端。协议层不是「顺便兼容」的补丁，而是被当作一等公民设计。这是一条关键取舍：它的目标是一个能跑 Vanilla 多人逻辑的 Rust 服务端，而不是一个「Minecraft 项目的脚手架」。

## 为什么 Rust 适合重写 Minecraft 服务器

理由不止「性能强」。Minecraft 服务端是 I/O 密集、Tick 密集、状态密集三者叠加的工程：

- **网络层**：每秒处理成百上千玩家的封包解析、加密、压缩与广播，是高频小数据；
- **世界层**：按 Chunk（16×16 方块柱）做生成、加载、保存、光照、Tick，是高吞吐的磁盘与内存操作；
- **逻辑层**：红石、实体行为、计划刻（Scheduled Tick）这些对顺序敏感的规则，对并发原子性与一致性要求很高。

Rust 在这三个维度都给了相对扎实的答案：所有权与借用让数据竞争在编译期被排除；`tokio` 提供异步运行时；`rayon` 提供数据并行（Data Parallelism）；`crossbeam` 提供无锁与有锁同步原语；`dashmap` 承接高频并发读写。

换句话说，Pumpkin 押注的是「用类型系统和线程模型表达领域」，而不是靠 JVM 调参去挤性能。

## 设计目标：五条 Goals

仓库 README 显式列出了五条 Goals，这是对外承诺的硬边界：

1. **Performance** — 借助多线程获得最大速度与效率。写得直白，没有修饰，意味着性能是它愿意用复杂度去换的指标。
2. **Compatibility** — 在坚持 Vanilla 机制的前提下，支持最新 Java 版与基岩版（基岩版 W.I.P）。它不会为绕过 Mojang 协议而引入私有客户端。
3. **Security** — 优先防御已知安全漏洞，对应 Minecraft 多年累积的协议层与账号层 CVE（Common Vulnerabilities and Exposures，公开漏洞编号）。
4. **Flexibility** — 高度可配置，能禁用不需要的功能。禁掉插件容器、禁掉 Chat 渲染、禁掉 Query 协议，在小型部署里是常见操作。
5. **Extensibility** — 为插件开发提供底盘。

两条线值得分开看：性能与安全靠 Rust 类型系统和运行时保证，属于「写给自己的」；兼容、可配、可扩展是对外契约，属于「写给生态的」。同时押这两边不是没有代价，下文「当前状态与边界」会展开。

## 架构概览

Pumpkin 的代码组织本身就是信息。仓库顶层是一个 Cargo Workspace，列出 11 个成员 crate（`pumpkin-codegen` 被显式 `exclude`），命名都遵循 `pumpkin-*` 前缀：

- `pumpkin`：主二进制入口；
- `pumpkin-protocol`：协议层，处理 Java 与基岩版封包编解码；
- `pumpkin-codecs`：通用编解码工具集；
- `pumpkin-nbt`：NBT（Named Binary Tag，Minecraft 自定义二进制格式）解析与序列化；
- `pumpkin-world`：世界区块、生成、保存与光照；
- `pumpkin-data`：方块、物品、生物群系等静态数据表；
- `pumpkin-config`：TOML 配置加载；
- `pumpkin-inventory`：物品栏与容器；
- `pumpkin-util`：通用工具；
- `pumpkin-plugin-api`：插件 ABI；
- `pumpkin-macros` / `pumpkin-api-macros`：过程宏。

从 `Cargo.toml` 还能读出几条架构取向：

### 编译器与工具链

`rust-toolchain.toml` 锁 `channel = "stable"`，附带 `rust-analyzer` 与 `rust-src`。Workspace 标记 `edition = "2024"`、`rust-version = "1.95"`——它愿意吃最新版编译器红利。

### 并发栈

`tokio`（默认 feature 关闭、按需开启）搭配 `rayon`、`crossbeam`、`dashmap`、`arc-swap`、`crossfire`。分工明确：`rayon` 管 CPU 密集的数据并行，`tokio` 管 I/O 密集的异步等待，而不是把线程全塞进 Tokio runtime。

### 网络与零拷贝

`bytes` 用作字节缓冲，`uuid`、`bitflags`、`lru`，以及更小众但性能稳定的 `rustc-hash`。协议层对延迟的敏感在依赖列表里一览无余。

### 加密与账号

`rsa`、`aes`、`ctr`、`ecdsa`、`p384`、`sha1`、`sha2`、`hmac`，覆盖 Online Mode（在线模式，玩家连接须验证 Mojang Session Server）的登录挑战、签名验证与 HMAC-SHA256 校验。

### 压缩与编码

`flate2`（zlib）、`ruzstd`（zstd）、`lz4-java-wrc`（与 Minecraft Java 客户端兼容的 LZ4 变种）、`async-compression`。基岩版走 `cfb8`，对应 RakNet 协议族的 8-bit 加密流。

### 插件运行时

这是最值得高亮的一块。`wasmtime` 启用了 `component-model`、`async`、`gc`、`threads` 等重型 feature，配合 `wasmtime-wasi`、`wasmtime-wasi-http`、`wit-bindgen` 与 `pumpkin-plugin-wit` 仓库。含义是：Pumpkin 计划用 WebAssembly 组件模型加 WIT（WebAssembly Interface Types，组件接口描述）做插件 ABI，插件以 `.wasm` 模块加载，通过 WASI P2 访问文件与网络。`libloading` 保留了加载原生动态库的通道，但 Wasm 才是差异化的主线。

### 静态检查纪律

`workspace.lints.clippy` 对 `all`、`nursery`、`pedantic`、`cargo` 四个语义组 `deny`，连 `todo`、`unreachable`、`unimplemented`、`dbg_macro`、`print_stdout`、`print_stderr` 也一并 `deny`。想在这种 lint 下提 PR，几乎先得扛过一轮 clippy 检查。

### 发布配置

`[profile.release]` 启用 `lto = true`、`codegen-units = 1`、`strip = "debuginfo"`，产出的跨模块 LTO（Link-Time Optimization，链接时优化）最小镜像，对体积、启动延迟、内存占用都是利好。

World 层的能力从 README Features 列表能看出轮廓：World Loading、World Time、World Borders、World Saving、Lighting、Entity Spawning、Bossbar、Chunk Loading（Vanilla/Linear/Pump 三种实现）、Chunk Saving（三种实现）、Liquid Physics 都已打勾；Chunk Generation 与 Redstone 还在 Issue 追踪页上。

## 一个玩家连接会流经哪里

把上面的 crate 拆开再串起来，看一段真实任务流——一个玩家从连接进入世界的路径：

1. 客户端发起握手与 Login Start，`pumpkin-protocol` 在最外层完成 Java 版封包的解码与压缩解压；
2. Online Mode 下，`pumpkin` 用 `rsa` 完成密钥交换、`aes` 建立对称加密通道，再用 `sha1`/`hmac` 校验签名，最终验证 Mojang Session Server；
3. 进入 Play 状态后，`pumpkin-world` 加载玩家所在 chunk，`pumpkin-inventory` 初始化物品栏，`pumpkin-nbt` 读写实体与世界的二进制数据；
4. 每 Tick，主调度推进计划刻等顺序敏感逻辑，`rayon` 在 chunk 粒度上做可并行的数据计算，`dashmap` 承载高频并发读写。

这条路把「协议层、加密层、世界层、逻辑层」串成一个可追踪的闭环。它说明的是 Pumpkin 怎么把分 crate 的边界落实到一次真实连接上。

## 当前状态与边界

Pumpkin README 顶部有一段 IMPORTANT 提示：

> Pumpkin is currently under heavy development.
> See what needs to be done before the 1.0.0 Release

这是官方背书的状态描述。读者应该带走的预期：

- **协议对最新版的覆盖是追赶式的**。Java 版每年若干次小版本更新，每次都可能动协议细节。Pumpkin 把支持最新版列为目标，但声明「正在追」——`Tracking: Protocol`、`Tracking: World`、`Tracking: Player` 三个 Tracking Issue 就是总账。
- **基岩版仍在 W.I.P**。Java 版是基本盘，Bedrock 端处于着手阶段，不承诺时间线。
- **战斗、红石、实体 AI、完整生物行为等模块没有收尾**。Villagers、Mobs、Animals、Boss 都标着 W.I.P；插件系统也还在 Tracking。商用复合玩法服务器目前不具备 readiness。
- **Commands 仍是空缺**，这是影响玩家体验的硬指标。
- **版本号 `0.1.0-dev+26.2`** 本身说明模块化边界还没稳定，crate 拆分与依赖随时会调整。

一句话：Pumpkin 是「工程可能性更高、版本成熟度更低」的项目。

## 适用人群

把上面的信号综合起来看，Pumpkin 对谁有用，决定了它对你是资产还是噪声：

- **Rust 工程师 + 游戏服务器研究者**：协议层、Tick 调度、并发原语都有真实的现代 Rust 使用样本；Workspace、lint 策略、release profile 值得当研究骨架。
- **小型 Vanilla 玩家圈**：能容忍「偶尔手动跟协议 patch」的小团体，可以用它跑低资源消耗的私域联机服。
- **Minecraft 生态插件开发者**：等到 1.0 之后插件 API 稳定，Wasm + WIT 加 WASI P2 提供的是沙箱化、可控权限的插件形态，比 Java 插件更现代。
- **不该选它的场景**：要 Bukkit/Spigot/Paper 的成熟生态、离线模式公网运营、完整红石与命令系统、即插即用的大型商业服——Pumpkin 目前都不是答案。

## 一句话总结

Pumpkin 用 Rust 把「重写 Minecraft 服务端」这件事押在多线程性能、协议兼容、内存安全与 Wasm 组件模型插件 ABI 上。它仍在 `0.1.0-dev`，处于重度开发中——读者拿到的不是稳定的生产方案，而是一个值得跟进的现代服务端骨架。愿意为「类型系统和线程模型」付学费的工程读者，值得花一个晚上通读它的 `Cargo.toml`。