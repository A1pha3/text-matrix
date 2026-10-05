---
title: "Box3D：Box2D 作者的新一代 3D 物理引擎"
date: 2026-08-01T02:54:21+08:00
lastmod: 2026-09-29T00:00:00+08:00
draft: false
categories: ["技术笔记"]
tags: ["Box3D", "物理引擎", "游戏开发", "C语言", "Box2D", "确定性"]
description: "Box3D 是 Box2D 作者 Erin Catto 用 C17 写的 3D 刚体物理库：延续 Box2D v3 的 Soft Step 求解器与 data-oriented 设计，新增跨平台确定性、录制回放和可选的大世界双精度模式。本文按 2026-09 仓库 main 分支核实。"
slug: erincatto-box3d-3d-physics-engine-guide
github_repo: "erincatto/box3d"
source_key: "gh:erincatto/box3d"

---

## 一句话判断

Box2D 作者 Erin Catto 的 3D 引擎。它不是把 Box2D 升一个维度，而是把 Box2D v3 那套被验证过的东西——C17、data-oriented、Soft Step 求解器——原样带进 3D，再加两样 2D 版没有的东西：跨平台确定性，和围绕它建立的录制回放系统。如果你在做联网对战、回放、或者需要"同一输入永远得到同一结果"的模拟，这两样是选它的理由。

## 项目概览

| 维度 | 数据 |
|------|------|
| 仓库 | erincatto/box3d |
| Stars | 6,473（2026-09-29 读数） |
| 语言 | C17（核心库）/ C++20（示例程序） |
| 许可证 | MIT |
| 作者 | Erin Catto（Box2D 作者） |
| 时间线 | 2026-05-10 建仓，v0.1.0 发布于 2026-06-30，此后 main 持续更新 |

唯一正式发布是 v0.1.0，新特性（录制回放、大世界双精度）先落在 main。本文以 2026-09-29 的 main 分支为口径。

## 一次模拟如何发生

物理引擎容易被当成黑盒。先用官方 hello world 把数据流过引擎的路径走一遍，后面各节就都有了抓手。目标是让一个动态方块从 y=4 落到静止在 y=1 的地面上：

1. 创建世界。`b3DefaultWorldDef()` 拿默认配置（重力已是 `{0, -10, 0}`），`b3CreateWorld` 返回不透明句柄 `b3WorldId`。Box3D 没有内置"上"方向，重力向量可以指向任意一边。
2. 建静态地面：`b3CreateBody` 默认创建的是静态刚体（零质量、不动、彼此不碰），再用 `b3MakeBoxHull(50, 10, 50)` 造一个盒形凸包挂上去。Box3D 的盒子就是凸包，参数是半尺寸。
3. 建动态方块：`bodyDef.type = b3_dynamicBody`，形状定义里给非零密度。漏了类型或密度，物体不会按预期运动——这是手册里专门用 Caution 框强调的两处。
4. 步进：`b3World_Step(worldId, 1.0f/60.0f, 4)`。固定 1/60 秒步长，配 4 个子步（sub-step），约束内部实际以 240 Hz 运行。手册建议不要把时间步绑到帧率上——可变步长产生不可复现的结果。
5. 每步之后用 `b3Body_GetPosition` 和 `b3Body_GetRotation` 取位姿。3D 里没有单一角度可取，朝向是四元数，喂给渲染器前用 `b3MakeMatrixFromQuat` 转矩阵。

这条路径里有两套彼此独立的机制：碰撞系统回答"哪些东西碰上了"，求解器回答"碰上之后怎么动"。这两套机制也可以只用一半——碰撞查询和 dynamic tree（BVH）可以脱离刚体模拟独立使用，拿来做游戏自己的空间排序。

## 碰撞系统

碰撞系统负责找出重叠的形状对，是求解的输入。

- **连续碰撞检测（CCD）**：防止高速物体隧穿，靠两套算法配合——碰撞算法插值两个物体的运动求首次撞击时间（TOI），以及推测性碰撞（speculative collision），在物体接触之前就先建好接触约束。
- **形状**：凸包、胶囊体、球体、三角网格、高度场。盒形是凸包的便捷构造，胶囊适合角色，球适合车轮。
- **复合形状**：单个刚体挂多个形状，拼出贴近实际的轮廓。
- **碰撞过滤**：按位掩码分组，控制谁和谁碰撞。
- **查询接口**：射线投射、形状投射、重叠查询，用于拾取、探测、视野判定。
- **传感器**：只报告重叠事件，不产生物理响应，适合触发器。
- **角色移动器（Character Mover）**：官方标注 experimental。它是一个活在刚体模拟之外的胶囊，由应用代码全权驱动：每帧先 `b3World_CastMover` 求实际可移动距离，再 `b3World_CollideMover` 收集接触面，`b3SolvePlanes` 解出修正位移。这是第一人称射击和精确平台跳跃游戏常用的做法，换来的是不被求解器"打架"，代价是碰撞解决要自己做。

## 物理求解器

求解器接收碰撞系统给的接触点，把速度与位置算到稳定。

- **Soft Step 刚体求解器**：README 原话是 "Robust Soft Step rigid body solver"。这是 Erin Catto 在 Box2D v3 里给出的求解思路，Box3D 延续下来，配合子步机制——60 Hz 步长、4 子步时约束以 240 Hz 求解，长关节链的拉伸会明显减小。手册同时坦白求解器是近似的：焊接关节连成的链条在某些情况下仍会变软。
- **连续物理**：对快速平移和旋转持续处理，压制隧穿，不只靠离散步长。
- **岛屿休眠**：静止刚体按 island 归组整块睡眠，几乎不占 CPU。
- **关节**：源码 `b3JointType` 枚举列了 9 种——旋转副、棱柱副、距离、球面（spherical）、焊接、车轮、电机（motor）、平行（parallel）、滤波（filter）。README 的 Features 只列了其中 6 种，以源码为准。每种都可叠加限位、电机、弹簧、摩擦。弹簧刚度用赫兹表达，调好后与相连物体的质量无关。
- **力查询**：可读取关节受力和接触力，用于手感反馈或音效触发。
- **事件**：每步结束时产生一批事件——刚体运动事件、接触开始/结束、传感器开始/结束、接触撞击事件，供游戏逻辑同步。

单位尺度有硬边界，这在选型时比功能清单更重要：Box3D 按 MKS 单位调优，移动物体在 0.1 到 10 米之间（汤罐到公交车）表现最好，静态形状最长 50 米左右，世界坐标建议小于 12 公里（小心调优可推到 24 公里）。角度用弧度，朝向是四元数，没有欧拉角的取值范围概念。

## 系统设计

**C17 与零依赖。** 核心库只依赖 C 运行时（Unix 下加 libm），无任何第三方依赖，链接后暴露 `box3d::box3d` 这个 CMake target。C 语言转向始于 Box2D v3 的重写，Box3D 直接继承了这一选择。公开 API 全在 `include/box3d/` 下（8 个头文件），`src/` 里 88 个源文件属内部实现，官方支持范围以 include 为界。

**id 句柄与定义结构。** 创建世界、刚体、形状、关节都返回不透明的 id，附带 64k 代计数防止悬挂引用，配 `B3_IS_NULL`、`B3_ID_EQUALS` 这类宏做判断。创建时传入 definition 结构体，用 `b3DefaultBodyDef()` 这类工厂函数拿默认值——C 没有构造函数，零初始化对这类结构不适用，这个模式把构造错误挡在了编译期之外。

**多线程：内置调度器，默认单线程。** 默认 `workerCount = 1` 完全单线程；要并行，要么直接设 worker 数（内置调度器自己建线程，设 4 会建 3 个新线程，调用 `b3World_Step` 的线程算第 4 个），要么通过 `enqueueTask`/`finishTask` 回调接你自己的任务系统。官方建议 worker 数用物理核数，不算超线程和能效核。设计取向是数据并行：让 Box3D 摊开用满所有核尽快算完，而不是任务并行。线程安全边界要记牢：`b3World_Step` 期间不可读写世界；Step 之外，射线、形状投射、重叠查询这类只读操作多线程安全。

**SIMD 与缓存。** SSE2 和 Neon 双路径，可用 `BOX3D_DISABLE_SIMD` 关掉。data-oriented 布局把同类数据连续存放，服务缓存命中——手册还提醒一个反直觉的细节：引擎会在模拟中移动数据结构来优化缓存，所以并发读世界可能读到垃圾。

**确定性是设计出来的，不是碰运气。** 手册的 Determinism 节给出了实现清单：多线程下的模拟顺序基于创建顺序（包括事件顺序）；跨平台靠编译器纪律——MSVC 开精确数学，Clang/GCC 关浮点缩合（`-ffp-contract=off`），`atan2`、`sin`、`cos` 全部自己实现，不依赖平台库。确定性默认开启且没有关闭选项，每个 PR 都跑确定性单元测试，因为它太容易碎。手册同时划清界限：引擎确定不等于你的应用确定，应用侧要自己遵守同样的纪律。

## 录制回放：确定性的兑现

跨平台确定性写在特性列表里只是承诺，Box3D 把它做成了可验证的工具链，这在 README 的 System 一栏里对应 "Recording and replay"。

录制是把某个步进边界上的世界快照，加上之后每一个修改世界的 API 调用日志，写进一块你自己持有的内存缓冲；回放则从快照出发重放这些调用。几何数据（凸包、网格、高度场）会被 intern 进录制自带的注册表，所以一个录制文件完全自包含，不需要外部资产就能重建世界。典型用途是调试：出问题前 30 秒才开录制也没关系，录制随时可以从中途开始。

配套的验证器 `b3ValidateReplay` 无头重放并逐帧比对状态哈希；示例程序里有 Replay Viewer，可以拖进度条逐帧看，分歧帧会被直接标出。这套工具有三个讲究的设计：

- **布局哈希门**：录制内嵌 struct 布局、指针宽度、字节序和格式版本的哈希，重放构建不匹配就拒绝加载——包括 SIMD 宽度的变化，宁可拒绝也不给你一份静默错误的回放。
- **浮点环境要求**：构建必须 `-ffp-contract=off`，`-ffast-math` 不受支持。
- **跨线程回放即测试**：用与录制时不同的 worker 数回放，约束图会被重新划分，状态哈希比对就变成了一次跨线程确定性测试。

局限也要知道：录制不保存 userData 指针，宿主回调（摩擦/恢复系数混合器、preSolve、自定义过滤器）不被捕获——装了自定义回调的会话回放时会分歧。

## 大世界模式：可选的双精度

单精度浮点在坐标 1e7 米处的步长约为 1 米，物体会吸附到粗网格上抖动。Box3D 提供 `BOX3D_DOUBLE_PRECISION` 构建选项：世界位置用 double，其余一切——速度、力、形状、接触流形、求解器、broad-phase——保持 float。这是 Jolt Physics 大世界模式的同款边界设计：double 只携带绝对位置，刚体局部坐标系内的积分量级小，float 精度绰绰有余。代价是百分之几，不是全 double 构建的两倍。

该选项默认关闭，关闭时所有 double 类型经 typedef 折叠回 float，行为与历来版本一致。开启是刻意的源码迁移——`b3Pos` 与 `b3Vec3` 是不同类型，混用的代码过不了编译，编译器会指出每一处需要转换的位置。实用范围在 ±1e7 到 ±1e8 米：再远，float 的 broad-phase 包围盒会开始产生多余误配对，只损性能不损正确性。两种精度模式内部各自确定、都可跨 worker 数复现，但彼此状态哈希不同，不算同一次模拟。

## 构建与集成

CMake presets 是官方推荐路径（`CMakePresets.json` 内置 windows、linux-release、macos、mingw-release、windows-clang-cl 等配置）：

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

示例程序运行路径（需在 Box3D 目录下）：

```bash
# Windows
.\build\bin\Release\samples.exe
# Linux
./build/bin/samples
# macOS
./build/bin/Release/samples
```

集成到项目推荐 FetchContent（与 README 一致，钉在当前唯一发布版）：

```cmake
include(FetchContent)
FetchContent_Declare(box3d
  GIT_REPOSITORY https://github.com/erincatto/box3d.git
  GIT_TAG v0.1.0)
FetchContent_MakeAvailable(box3d)

target_link_libraries(my_app PRIVATE box3d::box3d)
```

vendor 拷贝或 submodule 走 `add_subdirectory`，`cmake --install` 之后走 `find_package(box3d 0.1 REQUIRED)`，三条路都通。

示例应用用 sokol 做图形后端（Windows 上 D3D11、macOS 上 Metal、Linux 上 OpenGL 4.5），界面是 imgui，内含大量演示场景，包括 Large World 和 Replay Viewer，适合跑起来对照理解上面的机制。编译到 WebAssembly 走 Emscripten，用 SSE2：

```bash
emcmake cmake -B build -DBOX3D_SAMPLES=OFF
cmake --build build
```

用户手册在 `docs/` 下，用 Doxygen 构建（开 `BOX3D_DOCS` 选项编 `doc` target）。注意手册随 release 更新，main 分支可能领先于它。

## Box3D vs Box2D v3：真实的差异在哪

网上流传的对比常停留在 Box2D 2.x 时代，那早已失真。Box2D v3 自己就完成过一次 C17 重写，今天两个引擎的 System 清单几乎同构——都是 C17、data-oriented、多线程 SIMD、面向海量刚体优化。真正的差异在维度带来的形状与约束，以及 Box3D 独有的两栏：

| 维度 | Box2D v3 | Box3D |
|------|----------|-------|
| 维度 | 2D | 3D |
| 语言 | C17 | C17 |
| 求解器 | Soft Step | Soft Step |
| 多线程 / SIMD | 有 | 有 |
| 形状 | 凸多边形、胶囊、圆、圆角多边形、线段、链 | 凸包、胶囊、球、三角网格、高度场 |
| 关节 | 旋转、棱柱、距离、鼠标、焊接、车轮 | 9 种（含球面、平行、滤波、电机） |
| 跨平台确定性 | 未列入特性 | 明确承诺，每 PR 验证 |
| 录制回放 | 无 | 内置，含无头验证器 |
| 大世界双精度 | 无 | 可选（BOX3D_DOUBLE_PRECISION） |

所以选型结论很直接：要 2D，Box2D v3 依然是成熟答案；当需求进入 3D、并且在意确定性或世界尺度时，C 语言物理引擎里没有第二个现成选项。

## 上手路径

- 先克隆仓库按上面的 presets 编出 samples，把演示场景过一遍，对照本文感受接口与机制。
- 动手从 `docs/hello.md` 的最小程序起步，跑通"建世界 → 放动态刚体 → 步进"这条线，再加关节和传感器。
- 从 Box2D 迁移过来不要按 2D 的 API 习惯找同名函数，概念还在、接口已换；朝向从角度变成了四元数，这处心智转换最容易被忽略。
- 多线程不用一开始就上：默认单线程的确定性语义与并行时完全一致，先保证正确再开 worker。
- 手册明确说 Box3D 不适合作为你的第一个 C 项目——编译、链接、调试的熟练度是前置要求。

## 适用边界

**适合**：

- 游戏开发：角色控制、碰撞检测、物理交互，碰撞查询与 BVH 可脱离模拟单独用。
- 需要跨平台确定性的联网对战、回放、录制调试——这是它区别于其他开源 3D 物理引擎的核心牌。
- 大世界场景（行星尺度坐标）——开双精度模式，代价百分之几。
- 嵌入式与 WebAssembly：零第三方依赖、C17、SIMD 可关。

**不适合**：

- 高精度科学计算（FEM、流体）——求解器是近似的，服务于游戏级稳定而非数值收敛。
- 需要现成脚本绑定的项目——核心库是纯 C，Python/Lua 绑定要自己写。
- 尺度超出调优区间的模拟——移动物体小于 0.1 米或大于 10 米、世界超过 24 公里，都会碰精度边界。

还有两件事影响协作预期：仓库目前关闭了 Pull Request，反馈走 issue、Discord 或 GitHub Discussions；作者在 README 的 LLM Usage 一节声明，LLM 只用于单元测试、示例程序、Box2D/Box3D 代码迁移、构建配置、代码评审和基准测试，其余代码全部本人编写——"我为 Box2D/3D 的每一行代码负责"。

## 相关链接

- 仓库：[github.com/erincatto/box3d](https://github.com/erincatto/box3d)
- Box2D（前作）：[github.com/erincatto/box2d](https://github.com/erincatto/box2d)
- 介绍视频：[youtube.com/watch?v=jr_Fzl2XwKU](https://www.youtube.com/watch?v=jr_Fzl2XwKU)
- 最小程序：仓库内 `docs/hello.md`；用户手册在 `docs/`（Doxygen 构建）
- 两代引擎共通的底层算法：Erin Catto 的 GDC 演讲合集，见 [box2d.org/publications](https://box2d.org/publications/)
