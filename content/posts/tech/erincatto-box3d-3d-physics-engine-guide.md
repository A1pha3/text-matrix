---
title: "Box3D：Box2D 作者的新一代 3D 物理引擎"
date: 2026-08-01T02:54:21+08:00
draft: false
categories: ["技术笔记"]
tags: ["Box3D", "物理引擎", "游戏开发", "C语言", "Box2D"]
description: "Box3D 是 Box2D 作者 Erin Catto 用 C17 重写的 3D 物理引擎，采用 data-oriented design，支持连续碰撞检测、Soft Step 刚体求解器、跨平台确定性，以及丰富的关节类型和传感器系统。"
slug: erincatto-box3d-3d-physics-engine-guide

---

## 一句话判断

如果你做过 2D 物理仿真，大概率用过或听过 Box2D。Box3D 是同一作者将多年 2D 物理引擎经验延伸到 3D 的作品——不是 Box2D 的维度扩展，而是用 C17 从零设计的现代 3D 物理引擎，data-oriented、多线程、SIMD、跨平台确定性，瞄准游戏和实时仿真场景。

## 项目概览

| 维度 | 数据 |
|------|------|
| 仓库 | erincatto/box3d |
| Stars | ~5,700 |
| 语言 | C17（核心库）/ C++20（示例） |
| 许可证 | MIT |
| 作者 | Erin Catto（Box2D 作者） |

## 核心能力

### 碰撞系统

- **连续碰撞检测（CCD）**：防止快速移动物体穿透
- **碰撞事件**：提供接触回调
- **形状支持**：凸包（convex hull）、胶囊体（capsule）、球体、三角网格、高度场
- **复合形状**：单个刚体可挂多个形状
- **碰撞过滤**：按位掩码分组
- **查询接口**：射线投射（ray cast）、形状投射（shape cast）、重叠查询
- **传感器系统**：检测重叠但不产生物理响应
- **角色移动器（Character Mover）**：专为游戏角色设计的碰撞处理

### 物理求解器

- **Soft Step 刚体求解器**：Erin Catto 的标志性贡献，通过位置基求解（position-based solver）实现稳定收敛
- **连续物理**：对快速平移和旋转进行外推，减少隧穿
- **岛屿睡眠**：基于 island 分区的休眠机制，节省空闲物体的计算开销
- **关节类型**：旋转副（revolute）、棱柱副（prismatic）、距离（distance）、电机（motor）、焊接（weld）、车轮（wheel）
- **关节附件**：限位、电机、弹簧、摩擦
- **力查询**：可读取关节力和接触力
- **事件通知**：刚体运动事件和睡眠通知

### 系统设计

Box3D 在系统层面有几个区别于业余引擎的工程决策：

- **Data-Oriented Design（DOD）**：数据布局以缓存友好为首要目标，不是面向对象的对象层级
- **C17 实现**：核心库仅依赖 C 运行时（Unix 还需 libm），无第三方依赖
- **多线程 + SIMD**：内置多线程支持和 SSE2/Neon 自动向量化
- **大物体堆优化**：针对大量堆叠刚体的性能做了专门优化
- **跨平台确定性**：相同输入在不同平台产生相同结果，这对回放和联网模拟至关重要

## 构建

### CMake Presets（推荐）

```bash
# Windows
cmake --preset windows
cmake --build --preset windows-release

# Linux
cmake --preset linux-release
cmake --build --preset linux-release

# macOS
cmake --preset macos
cmake --build --preset macos-release
```

运行示例（需在 Box3D 目录下）：

```bash
# Windows
.\build\bin\Release\samples.exe
# Linux
./build/bin/samples
# macOS
./build/bin/Release/samples
```

### 集成到你的项目

Box3D 核心库零依赖（C 运行时除外），推荐用 CMake FetchContent：

```cmake
include(FetchContent)
FetchContent_Declare(box3d
  GIT_REPOSITORY https://github.com/erincatto/box3d.git
  GIT_TAG v0.1.0)
FetchContent_MakeAvailable(box3d)

target_link_libraries(my_app PRIVATE box3d::box3d)
```

也可以用 git submodule + add_subdirectory，或 cmake --install 后 find_package。

### 示例程序

仓库提供了 `docs/hello.md` 作为最小入门程序。示例应用使用 sokol 跨平台图形后端（D3D11 on Windows、Metal on macOS、OpenGL 4.5 on Linux）和 imgui 界面，包含大量演示。

### WebAssembly

Box3D 支持 Emscripten 编译到 WebAssembly，使用 SSE2 SIMD：

```bash
emcmake cmake -B build -DBOX3D_SAMPLES=OFF
cmake --build build
```

可通过 `BOX3D_DISABLE_SIMD` 关闭 SIMD。

## Box3D vs Box2D：定位差异

| 维度 | Box2D | Box3D |
|------|-------|-------|
| 维度 | 2D | 3D |
| 语言 | C++ | C17 |
| 设计范式 | 面向对象（后期 v3 改 DOD） | Data-Oriented from scratch |
| SIMD | 可选 | 内置 SSE2/Neon |
| 多线程 | 无（v2）/ 有（v3） | 内置 |
| 确定性 | 无保证 | 跨平台确定性 |
| 关节 | 基本类型 | 扩展限位/电机/弹簧/摩擦 |

Box3D 不是 Box2D 的 3D 版本，而是作者在多年 2D 物理引擎经验基础上的重新设计。C17 的选择尤其有意思——避开了 C++ 的 ABI 脆弱性和编译器差异，使跨平台确定性和嵌入式移植更容易实现。

## 适用边界

**适合**：

- 游戏开发（角色控制、碰撞检测、物理交互）
- 实时物理仿真（VR/AR、数字孪生）
- 需要跨平台确定性的联网模拟
- 嵌入式和 WebAssembly 场景（零依赖、C17）

**不适合**：

- 高精度科学计算（FEM、流体动力学）——Box3D 面向游戏级精度
- 非物理交互的 UI 动画
- 需要 Python/脚本绑定的快速原型（核心库是 C，需自行绑定）

## 相关链接

- 仓库：[github.com/erincatto/box3d](https://github.com/erincatto/box3d)
- Box2D（前作）：[github.com/erincatto/box2d](https://github.com/erincatto/box2d)
- 介绍视频：[youtube.com/watch?v=jr_Fzl2XwKU](https://www.youtube.com/watch?v=jr_Fzl2XwKU)
- 最小程序：仓库内 `docs/hello.md`
