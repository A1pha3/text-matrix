---
title: "Box3D：Box2D 作者的新一代 3D 物理引擎"
date: 2026-08-01T02:54:21+08:00
draft: false
categories: ["技术笔记"]
tags: ["Box3D", "物理引擎", "游戏开发", "C语言", "Box2D"]
description: "Box3D 是 Box2D 作者 Erin Catto 用 C17 重写的 3D 物理引擎，采用 data-oriented design，支持连续碰撞检测、Soft Step 刚体求解器、跨平台确定性，以及丰富的关节类型和传感器系统。"
slug: erincatto-box3d-3d-physics-engine-guide
github_repo: "erincatto/box3d"

---

## 一句话判断

如果你在 2D 里用过 Box2D，多半也关注过更广的物理引擎生态。Box3D 是同一作者把多年的 2D 物理引擎经验延伸到 3D 的作品——它不是 Box2D 的维度扩展，而是用 C17 从零设计的现代 3D 物理引擎，data-oriented、多线程、SIMD、跨平台确定性，面向游戏和实时仿真。

读完你会看到三条线：它和 Box2D 在哪些地方是延续、哪些地方是重写，什么场景下用它更划算，以及能力边界在哪里。

## 项目概览

| 维度 | 数据 |
|------|------|
| 仓库 | erincatto/box3d |
| Stars | ~5,700 |
| 语言 | C17（核心库）/ C++20（示例） |
| 许可证 | MIT |
| 作者 | Erin Catto（Box2D 作者） |

## 一次模拟如何发生

物理引擎经常被当成看不懂的黑盒，先拆一遍数据流过它的路径，后面各章就都有了抓手。以一颗胶囊体落下撞到地面为例：

1. 创建刚体时给出初始参数：类型（动态/静态）、初始位置和朝向、线速度，并挂上形状，交给 world。
2. 每帧调用步进后，求解器先按运动方程更新速度和位置，对快速移动的物体用 CCD 外推，避免它整个穿过地面。
3. 碰撞系统筛选出可能相交的形状对，生成接触；若是传感器，只发重叠事件，不产生任何物理响应。
4. Soft Step 求解器把这些接触连同关节、弹簧、电机当成约束一起收敛，迭代后得到稳定的新的速度与位置。
5. 一次步进收尾时产生事件通知：刚体是继续运动还是进入休眠。闲置的刚体被归入 island 后睡眠，不再占用 CPU，直到被再次唤醒。
6. 游戏逻辑每帧通过射线投射、重叠查询等接口取出结果，喂给 AI 或渲染管线。

这个路径里有两套彼此独立的机制——碰撞系统和求解器。碰撞系统回答"哪些东西碰上了"，求解器回答"碰上之后怎么动"。后面两节分别展开。

## 碰撞系统

碰撞系统负责回答"哪些物体重叠，重叠成什么样"，是后续求解的输入。

- **连续碰撞检测（CCD）**：对高速物体做外推，防止穿模。这是 2D 里深挖过的问题，在 3D 里代价更值得控制。
- **碰撞事件**：接触建立、保持、解除时提供回调，供游戏逻辑挂载。
- **形状支持**：凸包（convex hull）、胶囊体（capsule）、球体、三角网格、高度场。胶囊体对角色、球体对车辆轮子都很常用。
- **复合形状**：单个刚体可挂多个形状，拼出更贴近实际的轮廓。
- **碰撞过滤**：用按位掩码分组，控制不同物体之间是否碰撞、与谁碰撞。
- **查询接口**：射线投射（ray cast）、形状投射（shape cast）、重叠查询，用于拾取、探测、视野判定。
- **传感器系统**：只检测重叠与否，不参与物理响应，适合触发器。
- **角色移动器（Character Mover）**：专门处理角色这种频繁贴墙、站坡的特例，避免走得磕磕绊绊。

## 物理求解器

求解器接收碰撞系统给的接触点，负责把速度与位置算到稳定。

- **Soft Step 刚体求解器**：Erin Catto 的标志性做法，用位置求解配合软约束，让堆叠和关节收敛更稳。这是他在 Box2D v3 里验证过的思路，Box3D 里延续下来。
- **连续物理**：对快速平移和旋转做外推，进一步压制隧穿，而不只是依赖离散步长。
- **岛屿休眠**：按 island 分区管理活跃物体，空闲刚体整块睡眠，空闲场景几乎不耗 CPU。
- **关节类型**：旋转副（revolute）、棱柱副（prismatic）、距离（distance）、电机（motor）、焊接（weld）、车轮（wheel），覆盖常见机械结构。
- **关节附件**：限位、电机、弹簧、摩擦，可以叠加在一个关节上做精细调节。
- **力查询**：可读取关节受到的力和接触力，用于手感反馈或音效触发。
- **事件通知**：刚体运动状态变化和睡眠/唤醒都有通知，方便同步外部逻辑。

## 系统设计

这一节的取舍决定了它能跑多快、多省心，也是和业余引擎拉开差距的地方。

**为什么是 C17，而不是继续用 C++？** 作者在 2D 时代吃过 C++ 的亏：ABI 脆弱、不同编译器的差异容易让跨平台行为不一致。换成 C17 后，核心库只依赖 C 运行时（Unix 下加一个 libm），没有第三方依赖。这给跨平台确定性和嵌入式移植都铺平了路——几个指令就能在无 C++ 运行时的环境里编译起来。

**为什么 data-oriented？** 物理模拟每帧要遍历大量刚体，如果用一层层对象引用来组织，缓存命中率会很糟。data-oriented design 把同类数据紧凑地连续存放，让 CPU 尽量命中缓存，这是性能和确定性共同需要的。Box2D 后期才往这个方向改，Box3D 从第一行起就是这种布局。

**多线程和 SIMD 是内置的**：原生支持多线程，SSE2/Neon 自动向量化，密集堆叠场景专门做过优化。跨平台确定性保证相同输入在 x86、ARM、macOS 上得到一致结果——对回放、联网对战和可复现的离线模拟，这是能不能用的分水岭，而不只是加分项。

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

仓库提供了 `docs/hello.md` 作为最小入门程序。示例应用使用 sokol 跨平台图形后端（D3D11 on Windows、Metal on macOS、OpenGL 4.5 on Linux）和 imgui 界面，包含大量演示，适合跑起来对照理解上文提到的特性和接口。

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

Box3D 不是 Box2D 的 3D 版本，而是作者在多年 2D 物理引擎经验基础上的重新设计。C17 的选择尤其关键——避开了 C++ 的 ABI 脆弱性和编译器差异，使跨平台确定性和嵌入式移植更容易实现。

## 上手路径与注意点

- 先在仓库的示例场景里跑一遍，尤其看看碰撞过滤、传感器、角色移动器这几个演示，感受接口如何对应到玩法逻辑。
- 动手时从 `docs/hello.md` 的最小程序起步，先只做"创建 world → 放一个动态刚体 → 步进"这一条线，再逐步加关节和传感器。
- 如果你从 Box2D 迁移过来，别按 2D 的 API 习惯去找同名函数。接口设计变了，熟悉概念比查函数快得多。
- 核心库是纯 C，若要在 Python、Lua 这类脚本语言里用，需要自己写绑定，这会影响你的语言选型。

## 适用边界

**适合**：

- 游戏开发（角色控制、碰撞检测、物理交互）
- 实时物理仿真（VR/AR、数字孪生）
- 需要跨平台确定性的联网模拟
- 嵌入式和 WebAssembly 场景（零依赖、C17）

**不适合**：

- 高精度科学计算（FEM、流体动力学）——面向游戏级精度，不追求数值上的苛刻收敛。
- 非物理交互的 UI 动画——功能过剩，引入成本和收益不匹配。
- 需要 Python/脚本绑定的快速原型——核心库是 C，需自行绑定。

## 相关链接

- 仓库：[github.com/erincatto/box3d](https://github.com/erincatto/box3d)
- Box2D（前作）：[github.com/erincatto/box2d](https://github.com/erincatto/box2d)
- 介绍视频：[youtube.com/watch?v=jr_Fzl2XwKU](https://www.youtube.com/watch?v=jr_Fzl2XwKU)
- 最小程序：仓库内 `docs/hello.md`