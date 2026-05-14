---
title: "Brush：跨平台3D高斯泼溅渲染引擎，支持浏览器实时预览"
date: "2026-05-14T16:07:00+08:00"
slug: "brush-3d-gaussian-splatting-renderer"
description: "Brush是基于高斯泼溅（Gaussian Splatting）技术的3D重建引擎，使用Rust语言和WebGPU兼容技术开发，支持macOS/Windows/Linux/安卓全平台运行，可在浏览器中实时预览3D场景，支持COLMAP和Nerfstudio格式数据导入。"
draft: false
categories: ["技术笔记"]
tags: ["3D重建", "Gaussian Splatting", "Rust", "WebGPU", "WebAssembly"]
---

# Brush：跨平台3D高斯泼溅渲染引擎，支持浏览器实时预览

## 项目概览

**Brush** 是由 ArthurBrussee 开发的开源 3D 重建引擎，使用高斯泼溅（Gaussian Splatting）技术实现 3D 场景重建和渲染。项目星数 **4,442**，Forks 240，语言为 Rust。

核心设计目标是：**跨平台、零依赖、易分发**。大多数 ML 渲染工具依赖 CUDA，只在特定硬件上运行，而 Brush 通过 WebGPU 兼容技术和 [Burn](https://github.com/tracel-ai/burn)（Rust 机器学习框架）实现了真正的跨平台——macOS、Windows、Linux、Android 均支持，且可以在浏览器（Chrome/Edge）中直接实时预览 3D 场景，无需安装任何东西。

## 核心功能

### 训练（Training）

- 支持 **COLMAP** 数据格式和 **Nerfstudio** 格式的数据导入
- 支持在训练过程中实时交互、观察训练动态，并与输入视图对比渲染效果
- 支持图像遮罩：可通过带透明度的 PNG 或专门的 `masks` 文件夹指定忽略区域

### 查看器（Viewer）

- 可作为独立的 splat 查看器使用
- 支持加载 `.ply` 和 `.compressed.ply` 文件
- 支持从 URL 流式加载数据（URL 末尾加 `?url=` 参数）
- 可加载 `.zip` 格式的 splat 动画文件
- 支持加载包含 delta frames 的特殊 ply 格式（如 [cat-4D](https://cat-4d.github.io/) 和 [Cap4D](https://felixtaubner.github.io/cap4d/) 使用的那种）

### CLI 工具

所有 CLI 命令都支持 `--with-viewer` 参数，在启动 UI 的同时执行对应操作，便于调试。

### Rerun 可视化集成

训练时支持用 [rerun](https://rerun.io/) 可视化额外数据，安装 rerun-cli 后打开 `./brush_blueprint.rbl` 即可获得最佳可视化体验。

## 技术架构

- **语言**：Rust
- **ML 框架**：Burn（纯 Rust实现的机器学习框架，替代 CUDA 依赖）
- **渲染后端**：WebGPU（浏览器）+ 原生 GPU（桌面/移动端）
- **Web 编译**：wasm-pack 编译为 WebAssembly
- **浏览器要求**：Chrome 134+（Windows/macOS），Firefox/Safari 支持开发中

### 平台特定说明

**Android** 构建：
```bash
# 安装 Android SDK & NDK，设置 ANDROID_NDK_HOME 和 ANDROID_HOME
rustup target add aarch64-linux-android
cargo install cargo-ndk

# 编译 Rust 代码
cargo ndk -t arm64-v8a -o crates/brush-app/app/src/main/jniLibs/ build
cargo ndk -t arm64-v8a -o crates/brush-app/app/src/main/jniLibs/ build --release

# 安装到设备
./gradlew build
./gradlew installDebug
adb shell am start -n com.splats.app/.MainActivity
```

**Web** 构建：
```bash
npm run dev  # 启动 Next.js demo 网站
```

## 性能基准

官方 benchmark 显示渲染和训练速度通常优于 gsplat（主流高斯泼溅参考实现）。可用 `cargo bench` 运行各内核的性能测试。

## 与 gsplat 的关系

Brush 是 Google Research [brush_splat](https://github.com/google-research/google-research/tree/master/brush_splat) 仓库的公开分支（fork），经过了大量改进和重构。

## 适用场景

- 需要处理 COLMAP 或 Nerfstudio 格式 3D 数据的科研人员和开发者
- 希望在网页中嵌入实时 3D 预览的应用场景
- 需要 Android 端 3D 渲染能力但不想绑 CUDA 依赖的移动应用
- 对高斯泼溅技术进行研究和基准测试

---

**延伸阅读**：[在线 Demo（Chrome/Edge）](https://arthurbrussee.github.io/brush-demo) · [GitHub 仓库](https://github.com/ArthurBrussee/brush) · [Burn 框架](https://github.com/tracel-ai/burn)