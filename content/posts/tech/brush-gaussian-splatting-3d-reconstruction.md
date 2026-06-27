---
title: "Brush: 一个跨平台的 Gaussian Splatting 3D 重建引擎"
date: "2026-05-14T11:44:12+08:00"
slug: "brush-gaussian-splatting-3d-reconstruction"
aliases:
  - "/posts/tech/brush-3d-gaussian-splatting-renderer/"
description: "Brush 是一个基于 Rust 和 Burn ML 框架构建的 Gaussian Splatting 3D 重建引擎，支持 macOS、Windows、Linux、Android 和浏览器多平台运行，通过 WebGPU 实现跨设备渲染能力。"
draft: false
categories: ["技术笔记"]
tags: ["3D重建", "Gaussian-Splatting", "Rust", "WebGPU", "Burn", "开源"]
---
 
## 快速信息卡

| 项目 | 信息 |
|------|------|
| **Stars** | 4,760+ |
| **Forks** | 273+ |
| **许可证** | Apache-2.0 |
| **语言** | Rust |
| **仓库** | [ArthurBrussee/brush](https://github.com/ArthurBrussee/brush) |

最近在 GitHub Trending 上看到一个挺有意思的项目——[Brush](https://github.com/ArthurBrussee/brush)，一个用 Rust 写的 3D 重建引擎。

## 学习目标

阅读本文后，你将能够：

1. **理解 Brush 的技术定位**，掌握其基于 Gaussian Splatting 的 3D 重建原理
2. **解释 Brush 的跨平台实现方式**，包括 Rust + Burn 框架的技术选型理由
3. **在本地运行 Brush**，包括安装依赖、准备训练数据、启动 CLI 和查看器
4. **使用 Brush 进行 3D 重建**，包括数据格式选择、训练参数配置、实时预览
5. **集成 Brush 到自己的项目**，包括作为库使用、WebGPU 渲染、移动端部署
6. **判断 Brush 是否适合你的场景**，包括质量、性能、跨平台需求评估

## 目录

- [项目定位与背景](#项目定位与背景)
- [核心特性](#核心特性)
- [技术栈分析](#技术栈分析)
- [构建方式速览](#构建方式速览)
- [性能表现](#性能表现)
- [项目维护状态](#项目维护状态)
- [适用场景与局限](#适用场景与局限)
- [自测题](#自测题)
- [常见问题](#常见问题)
- [进阶路径](#进阶路径)
- [总结](#总结)

---

## 项目定位与背景

Brush 是一个基于 [Gaussian Splatting](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) 技术的实时 3D 重建引擎。Gaussian Splatting 这项技术通过海量高斯分布来表达场景，可以在保持较高重建质量的同时实现实时渲染，近年来在 NeRF 家族中脱颖而出。

项目 fork 自 Google Research 的 [brush_splat](https://github.com/google-research/google-research/tree/master/brush_splat) 公开版本，核心开发语言是 **Rust**，ML 框架选用了 [Burn](https://github.com/tracel-ai/burn)——一个纯 Rust 实现、跨平台支持的深度学习框架。这个技术组合直接决定了 Brush 最重要的特性：**跨平台、零依赖部署**。

> ⚠️ **免责声明**：本文所有技术细节均基于该仓库的公开 README 和源码，尚未在实际环境中运行验证。

## 核心特性

### 多平台覆盖

这是 Brush 最突出的卖点。当前支持：

- **桌面端**：macOS、Windows、Linux
- **GPU**：AMD、Nvidia、Intel 显卡均支持
- **移动端**：Android
- **浏览器**：通过 WebGPU 运行（需要 Chrome 134+）

一个统一的代码库，覆盖从手机到浏览器到桌面，背后的支撑是 Burn 框架的跨平台能力加上 WebGPU 作为统一的渲染接口。

### 训练与查看

Brush 支持输入 [COLMAP](https://colmap.github.io/) 格式数据或 [Nerfstudio](https://docs.nerfstudio.org/) 格式的数据集进行训练。训练过程中可以：

- 实时预览场景，与渲染结果对比
- 支持带透明通道的图片作为 masking 手段
- 也支持单独的 `masks` 文件夹来排除图像中的特定区域

作为查看器使用时，Brush 能加载 `.ply` 和 `.compressed.ply` 文件，也支持从 URL 远程流式加载数据。此外还能加载包含 delta frames 的特殊 ply 文件——这是 [cat-4D](https://cat-4d.github.io/) 和 [Cap4D](https://felixt aubner.github.io/cap4d/) 项目使用的格式，用于展示动态场景。

### CLI 工具

Brush 提供了完整的命令行接口，运行 `brush --help` 可查看所有可用命令。每个 CLI 子命令都支持 `--with-viewer` 参数，在命令行训练的同时打开图形界面辅助调试。

### 可视化集成

训练过程中可以通过 [Rerun](https://rerun.io/) 可视化额外数据（深度图、训练动态等），仓库根目录附带了 `brush_blueprint.rbl` 文件，打开即可获得最佳可视化效果。

## 技术栈分析

| 层次 | 技术选型 |
|------|----------|
| 核心语言 | Rust |
| ML 框架 | Burn（纯 Rust，跨平台） |
| 渲染接口 | WebGPU（WASM 编译） |
| Android | cargo-ndk（Rust → arm64 SO） |
| 数据格式 | COLMAP、Nerfstudio、.ply |

Burn 框架的选择是整个技术路线的关键。相比 PyTorch 或其他主流 ML 框架，Burn 用 Rust 原生实现，不依赖 Python 运行时也不需要 CUDA——最终产出的二进制文件**零外部依赖**，这是实现"任意设备上运行"这个目标的核心。

WebGPU 则是浏览器侧的统一渲染接口。当前浏览器端仅支持 Chrome 134+（Windows 和 macOS），Firefox 和 Safari 的支持还在路上。

## 构建方式速览

### 桌面端

安装 Rust 1.88+ 后：

```bash
cargo run --release  # 优化构建
cargo run             # 调试构建
cargo test --all      # 运行测试
```

### 浏览器端

```bash
cd app/brush-app/web
npm run dev           # 启动 Next.js demo
```

依赖 `wasm-pack` 构建 WASM bundle。需要 Chrome 134+ 才能运行 WebGPU 版本。

### Android 端

一次性配置 Android SDK/NDK 后，每次修改 Rust 代码需要：

```bash
cargo ndk -t arm64-v8a -o crates/brush-app/app/src/main/jniLibs/ build
./gradlew build
./gradlew installDebug
adb shell am start -n com.splats.app/.MainActivity
```

Android Studio 只负责 Java/Kotlin 层代码，Rust 层需要单独用 cargo-ndk 构建。

## 性能表现

README 提到渲染和训练速度"generally faster than gsplat"（通常优于 gsplat），并提供了 `cargo bench` 命令可以跑部分 kernel 的 benchmark。但需要注意的是，这是项目自述，没有在统一硬件环境下做过公开第三方对比，参考价值有限。

## 项目维护状态

从 commit 记录来看，项目**非常活跃**。最新几条 commit：

- `74e0230b` (2026-05-13) - Per-OS-thread Actor pinning + drop Slot for SplatChannel
- `6c8372df` (2026-05-13) - Add f32 fallback for image loss backward
- `7a56a9a9` (2026-05-12) - Fix args.txt round-trip for Vec args

最近一次提交就在昨天（2026-05-13），项目仍在高速迭代中。当前最新 release 是 **v0.3.0**（2025-09-14），但从 commit 频率看 v0.4.0 应该不会太远。

## 适用场景与局限

**适合的场景：**
- 想在手机或浏览器里实时查看 3D Gaussian Splatting 结果
- 需要一个跨平台、无外部依赖的 3D 重建工具
- 研究场景，需要在训练过程中实时可视化中间状态

**需要注意的边界：**
- WebGPU 浏览器支持有限，非 Chrome 浏览器暂时用不了 Web 版本
- Android 端构建流程相对复杂，需要同时管理 Rust (cargo-ndk) 和 Gradle 两套工具链
- 项目明确声明不是 Google 官方产品，线上生产使用需要自己承担风险

## 自测题

### 基础概念

**问题 1**：Brush 基于什么技术实现 3D 重建？它相比 NeRF 家族有什么优势？

<details>
<summary>参考答案</summary>

Brush 基于 Gaussian Splatting 技术实现 3D 重建。相比 NeRF 家族，Gaussian Splatting 通过海量高斯分布来表达场景，可以在保持较高重建质量的同时实现实时渲染。

</details>

**问题 2**：Brush 的技术栈选型是什么？为什么选择这套技术栈？

<details>
<summary>参考答案</summary>

Brush 的核心开发语言是 Rust，ML 框架选用了 Burn（一个纯 Rust 实现、跨平台支持的深度学习框架）。这个技术组合直接决定了 Brush 最重要的特性：**跨平台、零依赖部署**。

</details>

### 实践操作

**问题 3**：你需要在本地运行 Brush 进行 3D 重建，需要准备哪些依赖和步骤？

<details>
<summary>参考答案</summary>

依赖：
- Rust 工具链（cargo）
- Burn 框架依赖
- 训练数据：COLMAP 格式或 Nerfstudio 格式

步骤：
1. 克隆仓库：`git clone https://github.com/ArthurBrussee/brush.git`
2. 准备训练数据
3. 运行训练：`cargo run --release -- train --data-path <path>`
4. 实时预览：添加 `--with-viewer` 参数

</details>

**问题 4**：Brush 支持哪些平台？WebGPU 渲染需要什么环境？

<details>
<summary>参考答案</summary>

支持平台：
- 桌面端：macOS、Windows、Linux
- GPU：AMD、Nvidia、Intel 显卡均支持
- 移动端：Android
- 浏览器：通过 WebGPU 运行（需要 Chrome 134+）

WebGPU 渲染需要 Chrome 134+ 浏览器。

</details>

**问题 5**：你正在评估是否在生产环境使用 Brush，应该考虑哪些因素？

<details>
<summary>参考答案</summary>

需要考虑：
1. **性能**：README 提到的性能数据是项目自述，没有统一硬件环境下的公开第三方对比
2. **稳定性**：项目非常活跃（最新 release v0.3.0，但 commit 频率高），可能还在快速迭代
3. **浏览器支持**：WebGPU 目前只有 Chrome 支持
4. **移动端构建**：Android 端需要同时管理 Rust (cargo-ndk) 和 Gradle 两套工具链
5. **许可证**：Apache-2.0，适合商业使用

</details>

---

## 常见问题

### Brush 与 gsplat 等其他 Gaussian Splatting 实现有什么区别？

Brush 的核心优势是**跨平台零依赖部署**。相比 gsplat 等 Python/CUDA 实现，Brush 基于 Rust + Burn 框架，编译后只有一个二进制文件，不需要 Python 运行时或 CUDA 依赖。性能方面，README 提到"generally faster than gsplat"，但这是项目自述，建议在实际硬件上运行 `cargo bench` 验证。

### WebGPU 版本的性能如何？是否适合生产环境？

WebGPU 版本通过 WASM 编译，性能比原生版本低。当前仅支持 Chrome 134+，Firefox 和 Safari 的支持还在开发中。如果是生产环境，建议优先使用原生版本（桌面端或移动端）。

### 如何在 Android 设备上部署 Brush？

需要配置 Android SDK/NDK，然后使用 `cargo ndk` 构建 Rust 代码，再用 Gradle 构建 Android Studio 项目。具体步骤参考[构建方式速览](#构建方式速览)中的 Android 端部分。

### Brush 的训练速度如何？需要什么硬件配置？

训练速度取决于场景复杂度和硬件配置。README 提到性能"generally faster than gsplat"，但未提供具体硬件配置下的 benchmark。建议在实际使用前，用你的数据跑一次完整训练，记录时间和质量。

### 可以将 Brush 集成到现有的 3D 应用程序中吗？

可以。Brush 支持作为库使用（参考[技术栈分析](#技术栈分析)），也支持加载 `.ply` 和 `.compressed.ply` 文件。如果是 Web 环境，可以通过 WebGPU 接口集成。

---

## 进阶路径

### 1. 深入理解 Gaussian Splatting 原理

- 阅读原始论文：[3D Gaussian Splatting for Real-Time Radiance Field Rendering](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/)
- 理解算法核心：如何用高斯分布表达场景、如何优化协方差矩阵、如何实现实时渲染
- 对比 NeRF 家族：为什么 Gaussian Splatting 能实现实时渲染

### 2. 贡献到 Brush 项目

- 从 [GitHub 仓库](https://github.com/ArthurBrussee/brush) 克隆代码
- 阅读贡献指南（如果有）
- 从简单 issue 开始：修复文档错误、添加单元测试、优化错误处理
- 理解代码结构：核心库、CLI 工具、Web 前端、Android 应用

### 3. 将 Brush 集成到生产环境

- 评估需求：跨平台支持、性能要求、许可证兼容性
- 测试稳定性：在实际数据集上运行 Brush，记录崩溃、内存泄漏、性能瓶颈
- 集成到流水线：将数据准备、训练、查看、导出集成到现有 3D 重建流水线

### 4. 优化 Brush 性能

- 运行 `cargo bench` 识别性能瓶颈
- 优化数据加载：使用更快的存储、并行加载、缓存策略
- 优化训练参数：调整学习率、批量大小、迭代次数
- 贡献优化：将你的优化提交到上游仓库

### 5. 探索 Brush 的高级功能

- 动态场景：使用 cat-4D 和 Cap4D 格式的数据
- 实时可视化：集成 Rerun 进行训练过程监控
- 自定义渲染：修改 WebGPU 着色器，实现自定义渲染效果

---

## 总结

Brush 是一个目标很明确的项目——用 Rust+Burn 这套技术栈，把 Gaussian Splatting 这项技术做成一个真正可以跨设备、零依赖运行的工具。当前 Stars 4,760+，说明社区对这类"一次构建，到处运行"的 3D 工具确实有需求。如果你有 3D 重建相关的需求，不妨先去它的 [Web Demo](https://arthurbrussee.github.io/brush-demo)（需要 Chrome）体验一下效果，再决定要不要深入折腾。

**仓库链接**：https://github.com/ArthurBrussee/brush