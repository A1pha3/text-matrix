---
title: "Brush: 一个跨平台的 Gaussian Splatting 3D 重建引擎"
date: "2026-05-14T11:44:12+08:00"
slug: "brush-gaussian-splatting-3d-reconstruction"
description: "Brush 是一个基于 Rust 和 Burn ML 框架构建的 Gaussian Splatting 3D 重建引擎，支持 macOS、Windows、Linux、Android 和浏览器多平台运行，通过 WebGPU 实现跨设备渲染能力。"
draft: false
categories: ["技术笔记"]
tags: ["3D重建", "Gaussian-Splatting", "Rust", "WebGPU", "Burn", "开源"]
---

# Brush: 一个跨平台的 Gaussian Splatting 3D 重建引擎

最近在 GitHub Trending 上看到一个挺有意思的项目——[Brush](https://github.com/ArthurBrussee/brush)，一个用 Rust 写的 3D 重建引擎，截至目前已收获 **4,403 Stars** 和 236 个 Forks。项目的 slogan 很直接：**3D Reconstruction for all**——想做一个人人都能用的 3D 重建工具。

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

Brush 提供了完整的命令行接口，运行 `brush --help` 可查看所有可用命令。值得注意的是，每个 CLI 子命令都支持 `--with-viewer` 参数，在命令行训练的同时打开图形界面辅助调试。

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

## 总结

Brush 是一个目标很明确的项目——用 Rust+Burn 这套技术栈，把 Gaussian Splatting 这项技术做成一个真正可以跨设备、零依赖运行的工具。当前 Stars 4,403，说明社区对这类"一次构建，到处运行"的 3D 工具确实有需求。如果你有 3D 重建相关的需求，不妨先去它的 [Web Demo](https://arthurbrussee.github.io/brush-demo)（需要 Chrome）体验一下效果，再决定要不要深入折腾。

**仓库链接**：https://github.com/ArthurBrussee/brush