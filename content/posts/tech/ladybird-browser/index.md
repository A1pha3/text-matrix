---
title: "Ladybird：从零开始的独立浏览器引擎"
date: 2026-08-12T03:23:25+08:00
slug: "ladybird-browser"
github_repo: "LadybirdBrowser/ladybird"
source_key: "gh:LadybirdBrowser/ladybird"
description: "Ladybird 是一个真正独立的 Web 浏览器项目，不基于 Chromium 或 Gecko，而是从零构建全新的引擎。本文梳理其架构分层、核心库组成与当前开发状态。"
draft: false
categories: ["技术笔记"]
tags: ["浏览器引擎", "Ladybird", "C++", "Web 标准", "开源"]
---

## 这个项目的特别之处

浏览器市场已经很久没有"新玩家"了。Chromium 系（Chrome、Edge、Brave、Arc）占据大多数桌面流量，Gecko（Firefox）和 WebKit（Safari）分剩余份额。它们共享一个特征：引擎都从已有代码库演进而来。

Ladybird 不同。它不 fork Chromium、不 fork Gecko、不 fork WebKit，而是从零写一个全新的 Web 引擎。65,389 颗星、3,128 个 fork——对一个 pre-alpha 阶段的浏览器引擎项目来说，这个关注度本身就说明社区对"浏览器引擎垄断"这件事的态度。

项目当前处于 pre-alpha 状态，官方明确表示"只适合开发者使用"。

## 多进程架构

Ladybird 采用多进程架构，核心进程角色：

| 进程 | 职责 |
|---|---|
| **主 UI 进程** | 窗口管理、标签页控制、用户交互 |
| **WebContent 渲染进程** | 每个标签页独立一个渲染进程，与系统其余部分沙箱隔离 |
| **ImageDecoder 进程** | 图片解码在进程外完成，增强对恶意内容的防御能力 |
| **RequestServer 进程** | 网络请求在进程外完成，渲染进程不直接访问网络 |

进程外解码和进程外网络是这个架构的两个设计亮点。浏览器安全漏洞的常见入口是"恶意图片触发解码器内存损坏"和"网络协议解析缺陷"。把这两类操作隔离到独立进程中，意味着即使解码器或网络栈被攻破，攻击者也难以直接接触渲染引擎的核心状态。

## 核心库组成

Ladybird 的引擎能力分散在一组库中。这些库目前从 SerenityOS 继承而来——项目创始人 Andreas Kling 最初在 SerenityOS 中开发这些组件，后来将其独立为 Ladybird 的基础。

| 库 | 功能 |
|---|---|
| **LibWeb** | Web 渲染引擎——HTML 解析、CSS 布局、DOM 操作 |
| **LibJS** | JavaScript 引擎——ECMAScript 规范实现 |
| **LibWasm** | WebAssembly 实现 |
| **LibCrypto / LibTLS** | 密码学原语与传输层安全（TLS） |
| **LibHTTP** | HTTP/1.1 客户端 |
| **LibGfx** | 2D 图形库——图像解码与渲染 |
| **LibUnicode** | Unicode 与 locale 支持 |
| **LibMedia** | 音频与视频播放 |
| **LibCore** | 事件循环、操作系统抽象层 |
| **LibIPC** | 进程间通信 |

这套库的设计是"自给自足"的——不依赖浏览器领域已有的基础设施（如 skia 渲染库、v8 引擎、NSS/OpenSSL 加密库），而是自己实现。这是"独立引擎"的真正含义：不是换一层壳，而是从渲染到加密全栈自研。

代价也显而易见：Web 平台规范极其庞大（CSS 一项就有数百个模块），一个人或小团队从零实现，覆盖率和兼容性需要长期积累。最新提交的 commit message——`LibWeb: Guard active window earlier in ::begin_navigation()`、`LibWeb: Support mask-composite when painting CSS masks`、`LibWeb: Contribute grid containing-block info instead of stamping it`——可以看出团队正在集中攻坚 CSS 布局和导航相关的 Web 标准细节。

## 平台支持

Ladybird 支持在以下平台构建和运行：

- **Linux**（主要开发平台）
- **macOS**
- **Windows**（需要 WSL2）
- **其他 \*Nix 系统**

构建说明在仓库的 `Documentation/BuildInstructionsLadybird.md` 中。项目使用 CMake 构建系统（`CMakeLists.txt` + `CMakePresets.json`），同时使用 vcpkg 管理第三方依赖（`vcpkg.json`）。Rust 工具链配置（`rust-toolchain.toml` + `Cargo.toml`）表明项目有部分组件使用 Rust 实现。

## 与 SerenityOS 的关系

Ladybird 的核心库（LibWeb、LibJS 等）最初在 SerenityOS 项目中开发。Andreas Kling 在 2024 年宣布将浏览器部分独立出来，成立 Ladybird 项目，专注于浏览器引擎的开发。这意味着：

- 核心库的代码质量和测试覆盖度受益于 SerenityOS 的长期打磨
- 但库的演进方向现在由 Ladybird 项目决定，与 SerenityOS 逐步解耦
- 两个项目共享部分代码，但 Ladybird 是独立的法人实体和技术路线

## 谁应该关注这个项目

- **浏览器引擎开发者**：研究一个从零开始的引擎如何组织，与 Chromium/Gecko 的架构取舍有何不同
- **Web 平台标准实现者**：Ladybird 的 LibWeb 实现过程本身就是对 CSS/HTML/JS 标准的"重新发现"——哪些部分设计良好，哪些部分在现有引擎中被 hack 绕过
- **安全研究者**：进程外解码和进程外网络是值得参考的浏览器安全架构模式
- **对浏览器垄断担忧的人**：Ladybird 证明"从零写浏览器引擎"这件事仍然有人在做

## 当前状态与风险

- **Pre-alpha**：不保证基本浏览功能可用，会崩溃、会渲染异常
- **标准覆盖率**：Web 平台测试（WPT）通过率未在 README 中公布，但可以从 commit 内容推断仍在快速补齐 CSS 核心模块
- **开发节奏**：提交非常活跃，最新提交在数小时内，主要聚焦 LibWeb 渲染引擎
- **团队规模**：相比 Chromium（Google）和 Gecko（Mozilla）的团队体量，Ladybird 是小团队项目，依赖社区贡献
- **资金模式**：项目通过 [ladybird.org](https://ladybird.org) 接受赞助，全职开发者数量有限

## 版本与仓库信息

- **仓库**：[LadybirdBrowser/ladybird](https://github.com/LadybirdBrowser/ladybird)
- **Stars**：65,389（截至 2026-08-11）
- **主要语言**：C++
- **许可证**：BSD 2-Clause
- **官方站点**：[ladybird.org](https://ladybird.org)
- **活跃度**：每日多条提交，处于活跃开发状态
