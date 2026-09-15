---
title: 'jrouwe/JoltPhysics 原理拆解：一个被《地平线 西之绝境》和《死亡搁浅 2》选中的多核友好刚体物理引擎是怎么设计的'
date: "2026-07-17T02:57:12+08:00"
slug: "jrouwe-jolt-physics-multicore-rigid-body-engine"
github_repo: "jrouwe/JoltPhysics"
source_key: "gh:jrouwe/JoltPhysics"
description: "Jolt Physics 是 Jorrit Rouwe 写的 C++ 多核友好刚体物理与碰撞检测库，11.5k stars，被《Horizon Forbidden West》与《Death Stranding 2》采用。本文拆解它的核心设计判断（后台批量预构造 body、查询与修改并行、不自动唤醒、确定性仿真）、系统地图（Jolt 源码分层）、与 PhysX/Bullet 的横向对比，以及 GDC 2022 演讲背后的工程取舍。"
categories: ["技术笔记"]
tags: ["C++", "游戏开发"]
---

# Jolt Physics 原理拆解：多核友好的刚体物理引擎是怎么设计的

## 目录

- 一句话判断
- 系统地图
- 边界与角色划分
- 关键机制：五个工程判断是怎么落到代码的
- 任务流案例：跑一个 160 个布娃娃的堆
- 与同类项目的横向对照
- 适用边界
- 动手练习
- 常见问题与排查
- 决策建议
- 阅读路径
- 参考文献与事实来源
- 边界声明

## 一句话判断

**Jolt Physics（[jrouwe/JoltPhysics](https://github.com/jrouwe/JoltPhysics)）是一个 11.5k stars 的 C++ 刚体物理与碰撞检测库，它的工程价值不在"物理算法新"，而在"多线程友好"这条路上走得非常彻底**。作者 Jorrit Rouwe 在 README 的 Design considerations 一节解释了他为什么要再写一个物理引擎：现有引擎的物理数据在主仿真循环之外很难被安全地并发访问，而游戏恰恰要在别的线程做资源加载、射线查询、导航网格生成这些事。围绕这条主线，README 列出了具体的并发语义——后台线程预构造整批 body（刚体对象，下同）、查询与增删改并行、查询与仿真步并行；外加两条配套原则：body 创建和删除不自动唤醒邻居（避免加载/卸载内容时误唤醒带来的性能毛刺），仿真 deterministic（同输入必同输出，可以把输入序列而非世界状态复制给远端）。这套设计已经被 Guerrilla Games 的《Horizon Forbidden West》和 Kojima Productions 的《Death Stranding 2: On the Beach》采用，作者也在 GDC 2022 做了公开演讲（"Architecting Jolt Physics for 'Horizon Forbidden West'"）。

阅读目标：读完能判断 Jolt 的多线程模型与 PhysX / Bullet 的差异大致在哪，能说清 deterministic simulation 的边界（同平台同二进制默认成立、跨平台需要编译开关），并能按官方脚本构建跑通 Samples 里 160 个布娃娃同时下落的场景。不需要先懂物理引擎，但需要 C++ 基础。

如果你在做游戏 / VR / 仿真，并且对 PhysX / Bullet 的"主线程同步"或者"多线程加锁开销"有痛感，这篇文章值得读完整。

---

## 系统地图

```text
┌──────────────────────────────────────────────────────────────────────┐
│                      Jolt Physics (C++17 library)                     │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Jolt/                          ← 全部源码都在这一棵目录树下          │ │
│  │    ├─ Core/            Memory / Threading / JobSystem / MutexArray │ │
│  │    ├─ Math/            Vec / Mat / Quat / AABox                    │ │
│  │    ├─ Geometry/        凸形支持 / 网格射线等几何算法                   │ │
│  │    ├─ TriangleSplitter/  三角形切分（BVH 构建用）                     │ │
│  │    ├─ AABBTree/        通用 AABB 树                                  │ │
│  │    ├─ ObjectStream/    物理数据序列化（Samples 用）                   │ │
│  │    ├─ Physics/         PhysicsSystem / Body / Constraints           │ │
│  │    │    ├─ Body/         BodyInterface / BodyLock / Body creation   │ │
│  │    │    ├─ Collision/    NarrowPhase + Casts + Collectors            │ │
│  │    │    │    └─ BroadPhase/  QuadTree / BruteForce / LayerFilter     │ │
│  │    │    ├─ Constraints/ Constraints / Motor / ConstraintManager      │ │
│  │    │    ├─ Ragdoll/ Ragdoll / Character / Vehicle / SoftBody / Hair  │ │
│  │    │    └─ IslandBuilder / StateRecorder / PhysicsSystem             │ │
│  │    ├─ Renderer/        DebugRenderer + 录制器（产出 .jor 文件）        │ │
│  │    ├─ Skeleton/        骨架与 ragdoll 映射                            │ │
│  │    ├─ Compute/         GPU 计算后端抽象（CPU fallback / DX12 / MTL / VK）│ │
│  │    └─ Shaders/         hair 等 GPU 模拟使用的着色器                    │ │
│  └──────────────────────────────────────────────────────────────────┘ │

│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  并发模型                                                          │ │
│  │    ├─ 仿真：Update 内部 job 化，narrowphase / 求解器多线程执行         │ │
│  │    ├─ body 读写：mutex array（哈希分桶锁）+ BodyLock 接口              │ │
│  │    ├─ broadphase：lock-free AABB 树，查询与更新并行                    │ │
│  │    └─ 后台批量加载：AddBodiesPrepare / Finalize                       │ │
│  └──────────────────────────────────────────────────────────────────┘ │

│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Public surface (BodyInterface / PhysicsSystem)                    │ │
│  │    ├─ Body 生命周期：CreateBody / AddBody / RemoveBody / DestroyBody │ │
│  │    ├─ 批量：AddBodiesPrepare / AddBodiesFinalize / AddBodiesAbort    │ │
│  │    ├─ 查询：ray cast / shape cast / collide shape / collect shapes   │ │
│  │    ├─ 约束：Fixed / Hinge / Slider / 6DOF / Motors ...               │ │
│  │    └─ 角色与载具：Rigid/Virtual character / Wheeled/Tracked vehicles │ │
│  └──────────────────────────────────────────────────────────────────┘ │

└──────────────────────────────────────────────────────────────────────┘
                          ▼
                Game / VR / Simulation engine
                          ▼
       DebugRendererRecorder → .jor 文件 → JoltViewer（Windows / macOS / Linux）回放
```

这张图里最值得盯住的是并发模型一栏：body 的增删改查走 `Jolt/Physics/Body/BodyInterface.h`，底层用 `Jolt/Core/MutexArray.h` 的哈希分桶锁保护单个 body；broadphase（宽相，快速筛掉不可能相交的 body 对）的四叉树在 `Jolt/Physics/Collision/BroadPhase/QuadTree.cpp`，用无锁方式支持多线程同时移动 body；narrowphase（窄相，对粗筛结果算精确接触）在碰撞检测里紧随其后；GPU 相关的 hair 模拟则通过 `Jolt/Compute/` 的后端抽象跑在显卡上。

---

## 边界与角色划分

Jolt 把"谁能碰物理数据"这件事按线程说清楚。`Docs/Architecture.md` 的 Multithreaded Access 一节给了两条硬规则：

- **`PhysicsSystem::Update` 运行期间，所有 body / constraint 的 mutex 都被锁住**，此时不能通过 BodyInterface 读写 body 或 constraint——所以游戏线程的修改要么排在 Update 之前，要么等它结束。
- BodyInterface 分**锁定和非锁定两个变体**。锁定变体用 mutex array（固定大小的 mutex 数组，body 按哈希映射到某个 mutex，多个 body 共享一把锁）防止并发访问同一个 body；非锁定变体完全不加锁，只适合你保证单线程访问、或者自己管好所有权的情况。

另一个高频场景是按 ID 访问单个 body：`Jolt/Physics/Body/BodyLock.h` 提供 `BodyLockRead` / `BodyLockWrite`，拿锁失败（body 已被别的线程删掉）时安全返回，持有锁期间其他线程改不了这个 body。注意不能用它连续锁多个 body——两个线程按相反顺序锁同样两个 body 会死锁，要锁多个用保证顺序的 `BodyLockMultiRead` / `BodyLockMultiWrite`。

在这些规则之外，**Jolt 明确不做**的事同样重要：

- ❌ **不**自动唤醒邻居 body。README 原话："Accidental wake up of bodies cause performance problems when loading/unloading content. Therefore, bodies will not automatically wake up when created. Neighboring bodies will not be woken up when bodies are removed."——什么时候唤醒由游戏代码手动触发。
- ❌ **不**用 `new` / `delete` 直接创建 / 销毁 Body。Body 由 Factory 分配，生命周期只能走 `BodyInterface::CreateBody` / `DestroyBody`（HelloWorld 的注释还提醒了另一种失败方式：body 池耗尽时 `CreateBody` 返回 `nullptr`，需要检查）。
- ❌ **不**依赖 RTTI 或 exceptions，只依赖 C++17 标准模板库（README：Compiles with Visual Studio 2022+, Clang 16+ or GCC 12+）。README 没有解释动机，只陈述事实；考虑到它要在 Platform Blue 这类需要 NDA 环境才能编译的游戏主机上运行（需要开发者自带 PlatformBlue.h），对工具链保持最小依赖是说得通的工程判断。
- ❌ **不**永远模拟所有 body。速度长期低于阈值的 dynamic body 会进入睡眠，不再消耗每帧的求解开销，被激活后重新参与仿真。
- ❌ **不**提供渲染 / 资产管线。`Jolt/Renderer/` 只有 debug 绘制和 .jor 录制，正式渲染、资源管理交给游戏引擎自己接。

这五条"不做"和三条并发语义是配套的：不自动唤醒让后台加载线程可以放心增删 body，不依赖 RTTI / exceptions 让引擎能在受限主机工具链上编译，不做渲染让库的线程模型保持简单。下面拆开看它们各自怎么落到代码。

---

## 关键机制：五个工程判断是怎么落到代码的

### 1. 后台预构造 + 原子提交：AddBodiesPrepare / Finalize / Abort

`Jolt/Physics/Body/BodyInterface.h` 的批处理 API 是 Jolt 并发设计最集中的地方。三个函数的签名（摘自头文件）：

```cpp
using AddState = void *;

// 准备加入 inNumber 个 body，返回句柄供 Finalize/Abort 使用
// 注意：ioBodies 数组可能被本函数重排，调用方要保持原样传回
AddState AddBodiesPrepare(BodyID *ioBodies, int inNumber);

// 提交整批进物理系统，激活模式显式传入
void AddBodiesFinalize(BodyID *ioBodies, int inNumber, AddState inAddState,
                       EActivation inActivationMode);

// 中途放弃整批
void AddBodiesAbort(BodyID *ioBodies, int inNumber, AddState inAddState);
```

为什么必须分两步？如果只有同步的 `AddBody`，主线程会被 broadphase 更新阻塞；如果不区分 Prepare 和 Finalize，跨线程查询可能看到"半批插入"的中间状态。Jolt 的拆法是：

- Prepare：把 body 数据构造好，但**不**进入 broadphase——这一步可以整体丢给后台线程；
- Finalize：把整批 body 原子地挂进物理系统；
- Abort：如果玩家转身走开、这段流式加载的关卡不再需要，直接扔掉已 Prepare 的 body，不污染仿真。

README 对这个场景的原话："Sections of the simulation can be loaded/unloaded in the background. We prepare a batch of physics bodies on a background thread without locking or affecting the simulation. We insert the batch into the simulation with a minimal impact on performance."

配套的还有 `PhysicsSystem::OptimizeBroadPhase()`：HelloWorld 的注释建议开模拟前调用一次来优化 broadphase，并特别强调**不要每帧调用**，流式加载新关卡内容时也应该批量插入而不是逐个插入——这正是 batch API 存在的理由。

### 2. 查询与修改并行：同线程立即可见，跨线程看到一致前后态

body 的状态何时对查询可见、可见到什么程度，是并发语义里最微妙的部分。README 的原话值得整段读：

> Collision queries can run parallel to adding / removing or updating a body. If a change to a body happened on the same thread, the change will be immediately visible. If the change happened on another thread, the query will see a consistent before or after state. An alternative would be to have a read and write version of the world. This prevents changes from being visible immediately, so we avoid this.

落到实现上，这个语义靠三样东西支撑（见 Architecture.md）：

- **mutex array**：body 状态被哈希分桶的 mutex 数组保护，锁定变体的 BodyInterface 和 `BodyLock` 都走这条路，保证不会读到改了一半的状态；
- **TransformedShape 快照**：NarrowPhaseQuery 查询时在 body lock 保护下构造一个 `TransformedShape`（包含变换、引用计数的 shape 和 BodyID），构造完就放锁，后续大量碰撞检测工作在锁外进行——shape 有引用计数保活，所以这个快照始终一致；
- **lock-free broadphase**：body 移动时四叉树上从根到该 body 的路径节点会被"撑大"，用的是无锁写法，多线程同时移动 body 不需要锁整棵树。

README 里"读写双版本世界"那句，是作者解释为什么不选另一种常见设计——它对比的是一种泛化的替代方案，指代的是通用设计空间，不是特指某家引擎的实现。Jolt 选了"单世界 + 细粒度锁"：改动在发起它的线程上立即可见，代价是需要自己管理锁的粒度和顺序；双缓冲世界推迟可见性，换来的是更大的内存和同步开销。这是两种都成立的选择，Jolt 把理由写在了 README 里。

### 3. Broadphase 粗筛与 narrowphase 后台精查

仿真步内部的流水线，README 的原话：

> Collision queries can run parallel to the main physics simulation. We do a coarse check (broad phase query) before the simulation step and do fine checks (narrow phase query) in the background. This way, long running processes (like navigation mesh generation) can be spread out across multiple frames.

注意这里其实有两条"查询"路径，容易混：

- **仿真步内部的碰撞对收集**：broadphase 先粗筛出可能相交的 body pair，Architecture.md 描述实现是"找到的碰撞对被插入一个 lock-free queue 稍后处理"，narrowphase 再算精确接触；narrowphase 用的是双缓冲 contact cache（读缓存存上一帧接触、写缓存累积本帧新接触，延续的接触点从读缓存拷到写缓存）；island 的划分（把有约束关系的 body 归成一组求解）也是无锁的，每个仿真步都从零重建，复杂度 O(N)（N 为约束数）。
- **游戏主动发起的查询**（射线、shape cast、overlap、收集范围内的 body）：走 `BroadPhaseQuery` / `NarrowPhaseQuery` 接口。对导航网格生成这类长任务，Architecture.md 建议用 `NarrowPhaseQuery::CollectTransformedShapes` 一次性收集快照，然后在没有锁的后台线程里慢慢处理。

### 4. 不自动唤醒：activation 交给调用方

`Jolt/Physics/EActivation.h` 的枚举只有两个值，头文件注释原文照录：

```cpp
enum class EActivation
{
    Activate,       ///< Activate the body, making it part of the simulation
    DontActivate    ///< Leave activation state as it is (will not deactivate an active body)
};
```

也就是说 `AddBody(body, EActivation::DontActivate)` 只是"不加激活"，不会把已经醒着的 body 弄睡；需要立刻参与仿真就传 `Activate`。需要后续手动唤醒时，`BodyInterface::ActivateBody(bodyID)` 随时可用。

为什么默认姿态这么保守？游戏流式加载的典型节奏是"卸载一段地形、加载新一段"——如果删除 body 会唤醒邻居，broadphase 和 island 结构就要为一大批即将静态化的 body 买单；如果创建会自动唤醒周围 dynamic body，物理状态会被无意义地扰动。README 把这个取舍挑明了：误唤醒在内容加载/卸载时造成性能问题，所以创建不唤醒、删除不波及邻居，要不要唤醒留给游戏代码决定。

### 5. Deterministic simulation：边界比口号重要

README 承诺仿真 deterministic，并提醒"Read the Deterministic Simulation section to understand the limits"。`Docs/Architecture.md` 把边界写得非常细，两条前提：

- **修改 API 必须按完全相同的顺序调用**：body 和 constraint 的增删改顺序一致，每个仿真步开始时的状态才一致；
- **同一份二进制**：同一平台跑同一份二进制，AMD 还是 Intel 处理器无所谓。

跨平台需要打开 CMake 选项 `CROSS_PLATFORM_DETERMINISTIC`（或对应宏 `JPH_CROSS_PLATFORM_DETERMINISTIC`），官方说法是库会慢大约 8%，换来越过的差异清单：编译器（测试过 MSVC 2022、clang、gcc、emscripten）、构建配置（Debug / Release / Distribution）、操作系统（Windows / macOS / Linux）、指令集架构（x86、ARM、RISC-V、PowerPC、LoongArch）、字长（32 / 64 bit）。作者还在 CI 里固定跑了一套跨架构组合，验证它们对同样场景产生同样的结果。

应用侧要自己负责的部分同样明确：

- 浮点编译为 precise 模式（clang：`-ffp-model=precise`；MSVC：`/fp:precise`）；
- 关闭浮点 contraction（`-ffp-contract=off`；开确定性选项后 Jolt 自己也会忽略 FMADD 指令开关 `JPH_USE_FMADD`）;
- 保证各平台 / 各线程 FPU 状态一致：rounding 取 nearest，DAZ / FTZ 标志设置一致；
- **不要用**标准库的 `sin` / `cos`（各平台实现不同，用 Jolt 自己的 `Sin` / `Cos`）、`std::sort`（用 `QuickSort`）、`std::push_heap` / `std::pop_heap`（用 `BinaryHeapPush` / `BinaryHeapPop`）、`std::hash`（用 `Hash`）。

两个容易踩的坑：

- **`BroadPhaseQuery` 不 deterministic**。broadphase 会被多线程修改，body 被移动后包围盒先撑大、等下一次维护更新才收紧（可能要过好几次 `PhysicsSystem::Update`），所以查询命中集合可能因时序不同。要让 broadphase 查询有确定性，Architecture.md 给的办法是写自定义 `CollisionCollector`，在 `AddHit` 里用 `Body::GetWorldSpaceBounds` 拿真实包围盒复验，并自己对结果排序。
- **`NarrowPhaseQuery` 结果一致，但返回顺序可能变**，原因同样是 broadphase 被多线程修改。各类 listener（ContactListener 等）的回调顺序也不保证。

这些代价换来的是：lockstep multiplayer 客户端只需要同步"输入序列"（玩家操作、AI 决策），不需要同步完整世界状态。Samples 里还内置了一个验证工具——ESC 打开 Physics Settings 勾选 "Check Determinism"，每个仿真步前用 StateRecorder 记录状态、倒回、重算一遍再对比，任何不确定都会当场暴露。

### 6. HelloWorld 的最小骨架

`HelloWorld/HelloWorld.cpp` 是官方推荐的上手起点。第一条硬规则写在注释里："The Jolt headers don't include Jolt.h. Always include Jolt.h before including any other Jolt header."（其他 Jolt 头文件都不会替你包含 Jolt.h，必须第一个包含它；也可以放进预编译头加速编译。）

初始化是一次性的三步：

```cpp
RegisterDefaultAllocator();
Factory::sInstance = new Factory();
RegisterTypes();

// 每个仿真步用的临时内存从这块预分配里出
TempAllocatorImpl temp_allocator(10 * 1024 * 1024);

// 官方提供的线程池版 JobSystem，只是示例实现
JobSystemThreadPool job_system(cMaxPhysicsJobs, cMaxPhysicsBarriers,
                               thread::hardware_concurrency() - 1);

PhysicsSystem physics_system;
physics_system.Init(cMaxBodies, cNumBodyMutexes, cMaxBodyPairs, cMaxContactConstraints,
                    broad_phase_layer_interface, object_vs_broadphase_layer_filter,
                    object_vs_object_layer_filter);
BodyInterface &body_interface = physics_system.GetBodyInterface();
```

然后创建地面和球。地面走"创建、再添加"两步，球用一步到位的捷径——两种方式都在官方示例里：

```cpp
BoxShapeSettings floor_shape_settings(Vec3(100.0f, 1.0f, 100.0f));
floor_shape_settings.SetEmbedded();  // 栈上的引用计数对象必须标记 embedded，否则会被释放
ShapeSettings::ShapeResult floor_shape_result = floor_shape_settings.Create();
ShapeRefC floor_shape = floor_shape_result.Get();

BodyCreationSettings floor_settings(floor_shape, RVec3(0.0_r, -1.0_r, 0.0_r),
                                    Quat::sIdentity(), EMotionType::Static, Layers::NON_MOVING);
Body *floor = body_interface.CreateBody(floor_settings);   // body 池耗尽时返回 nullptr
body_interface.AddBody(floor->GetID(), EActivation::DontActivate);

// 动态球：CreateAndAddBody 一步完成创建和添加
BodyCreationSettings sphere_settings(new SphereShape(0.5f), RVec3(0.0_r, 2.0_r, 0.0_r),
                                     Quat::sIdentity(), EMotionType::Dynamic, Layers::MOVING);
BodyID sphere_id = body_interface.CreateAndAddBody(sphere_settings, EActivation::Activate);
body_interface.SetLinearVelocity(sphere_id, Vec3(0.0f, -5.0f, 0.0f));

physics_system.OptimizeBroadPhase();  // 只在模拟开始前调一次，不要每帧调
```

仿真循环到球睡着为止，最后记得成对地 Remove + Destroy：

```cpp
const float cDeltaTime = 1.0f / 60.0f;
while (body_interface.IsActive(sphere_id)) {
    physics_system.Update(cDeltaTime, 1, &temp_allocator, &job_system);
}

body_interface.RemoveBody(sphere_id);
body_interface.DestroyBody(sphere_id);
```

两个工程提示：`cMaxBodies` / `cNumBodyMutexes` 这些常量在示例文件里定义（示例取值 1024 / 0 / 1024 / 1024），真实项目按场景规模调；`JobSystemThreadPool` 是示例实现，HelloWorld 的注释明确建议生产项目自己实现 `JobSystem` 接口，让 Jolt 挂在你自己的 job scheduler 上。

CMake 集成可参考独立仓库 [JoltPhysicsHelloWorld](https://github.com/jrouwe/JoltPhysicsHelloWorld)，它演示了用 FetchContent 把 Jolt 拉进自己的构建。

---

## 任务流案例：跑一个 160 个布娃娃的堆

README 顶部的 YouTube 视频演示的就是一个布娃娃堆；GDC 2022 演讲里的性能基准也是 160 个布娃娃同时下落。这个场景在 Samples 里对应 "Rig / Rig Pile"，下面把它跑起来。

**Step 1：按官方方式构建**

仓库根目录没有 CMakeLists.txt，构建入口在 `Build/` 目录下的脚本（也可以直接把 `Build` 作为 CMake 源目录）。Linux/macOS 下：

```bash
git clone https://github.com/jrouwe/JoltPhysics
cd JoltPhysics/Build
./cmake_linux_clang_gcc.sh Release clang++   # macOS 换成 ./cmake_xcode_macos.sh
cd Linux_Release && make -j$(nproc)
```

脚本实际执行的是 `cmake -S . -B Linux_Release -DCMAKE_BUILD_TYPE=Release ...`。`TARGET_SAMPLES` 等 target 开关默认全开，不需要显式传；Windows 用 `Build/cmake_vs2026_cl.bat` 生成 `JoltPhysics.slnx` 工程再编译。

**Step 2：跑 Samples，选 Rig Pile**

```bash
./Linux_Release/Samples
```

在测试列表里选 Rig 分类下的 RigPileTest，源码在 `Samples/Tests/Rig/RigPileTest.cpp`。

**Step 3：认识默认参数**

这个测试的默认值按构建类型分两档，都在源码里写死：

- Debug 构建（或未启用 ObjectStream）：场景 `PerlinMesh`，每堆 5 个布娃娃、每轴 2 堆，即 5 × 2 × 2 = 20 个；
- Release 构建且启用 ObjectStream：场景 `Terrain1`，每堆 10 个、每轴 4 堆，即 10 × 4 × 4 = **160 个**。

代码里还有一道保险：`pile_size = min(sPileSize, 160 / Square(sNumPilesPerAxis))`，注释写明是为了不超过 160 个布娃娃。不用改源码也能调参——测试内按 ESC 打开设置菜单，"Num Ragdolls Per Pile"（1–160）和 "Num Piles Per Axis"（1–4）两个滑杆直接改；场景可以在 PerlinMesh / PerlinHeightField / Terrain1 / Terrain2 之间切换，后两个需要构建时启用 ObjectStream（加载 `.bof` 序列化场景）。

**Step 4：观察并发行为**

运行时的分工是这样的：

- 仿真步内：主线程驱动 `PhysicsSystem::Update`，broadphase 粗筛出的碰撞对进无锁队列，narrowphase 和约束求解作为 job 派给多个 worker；
- 每帧结束后：游戏线程读 body 位姿做渲染和输入；
- broadphase：worker 线程移动 body 时无锁地撑大树上路径，下一次维护更新在后台重建紧凑的树。

用性能分析器看，narrowphase 的 CPU 占用应该摊在多个 worker 上，主线程只负责调度——这就是 README 里 "long running processes can be spread out across multiple frames" 的实战形态。Jolt 自带内部分析器（`JPH_PROFILE_ENABLED`），Samples 里可以直接调出按 job 类型的耗时分布。

**Step 5：验证确定性**

单机自检最快：ESC → Physics Settings → 勾选 "Check Determinism"，每个仿真步都会记录状态、倒回重算并对比。要看跨平台行为，分别在不同平台跑 PerformanceTest（它会输出 `performance_test_<tag>.jor` 渲染录制），再用 JoltViewer 打开回放对比：

```bash
./Linux_Release/JoltViewer performance_test_Linux.jor
```

JoltViewer 接受录制文件作为位置参数（源码里的用法提示就是 `Usage: JoltViewer <recording filename>`），逐帧播放两份录制即可人工比对分叉。要注意 .jor 是渲染录制而非仿真状态，严格的自动化验证还是以 StateRecorder 对比和 CI 里的跨架构矩阵为准。

---

## 与同类项目的横向对照

先说清楚这张表怎么读：Jolt 列的数据来自本文核实过的 README、文档和 GitHub API（2026-09-15）；PhysX 和 Bullet 两列只填仓库元数据和官方 README 自述的公开事实，多线程与确定性的细粒度行为各家文档口径不一，本文不代替它们的官方文档下结论，选型时请以各自文档为准。

| 维度 | Jolt | PhysX（NVIDIA-Omniverse/PhysX） | Bullet（bulletphysics/bullet3） |
|---|---|---|---|
| 语言 / 标准 | C++17，仅依赖 STL，无 RTTI / exceptions | C++ | C++ |
| License | MIT | BSD-3-Clause | Zlib |
| Stars（2026-09-15） | 11,544 | 4,768 | 14,725 |
| 仿真范围（官方 README 自述） | 刚体 + 软体 + GPU hair + 载具 + 角色 + 水浮力 | 刚体 + 粒子 + 布料 + 软体 | 刚体 + 软体 + 布料 + 载具 |
| 多线程模型 | mutex array 保护 body、lock-free broadphase、job 化仿真步、后台批量预构造 | 本文未逐项核实，见官方文档 | 本文未逐项核实，见官方文档 |
| Deterministic | 同平台同二进制默认成立；跨平台开 `CROSS_PLATFORM_DETERMINISTIC`（约慢 8%），边界见 Architecture.md | 本文未逐项核实，见官方文档 | 本文未逐项核实，见官方文档 |
| 平台 | Windows / Linux / macOS / Android / iOS / FreeBSD / WASM / RISC-V64 / LoongArch64 / PowerPC64LE + Platform Blue | 见官方仓库 | 见官方仓库 |

如果只看"开源 + 允许商用 + 多核设计 + 确定性仿真 + 跨到国产架构"这一组条件的交集，Jolt 是目前少有的同时满足者——这也解释了为什么它近几年被这么多引擎采纳。社区验证案例（`Docs/ProjectsUsingJolt.md`）比 README 顶部两款 3A 游戏更有说服力：Godot 4.4 把 Jolt 作为内置的物理模块选项、Geekbench 7 用它做物理基准（2026-07 官方公告）、War Thunder 的 Dagor Engine 开源仓库里有 `physJolt` 集成目录，此外还有 ezEngine、GDevelop、Wicked Engine、X4 Foundations、《Garry's Mod》的 VPhysics-Jolt 替换等。生产级验证案例已经不是个位数。

**不推荐使用的场景**：

- 只需要几个球落地的 demo → 任何库都行，Jolt 的 batch API 和 layer 体系是杀鸡用牛刀；
- 已经在用 Unity / Unreal 内建物理 → 引擎内切换成本远大于收益（Godot 用户例外——4.4 起 Jolt 就是官方内置选项，在项目设置里启用即可）；
- 需要百万级 GPU 粒子 / 流体 → 这不是刚体物理库的职责范围，Jolt 的 GPU 部分目前只服务于 hair；
- 需要 production 验证过的布料 / 破坏管线 → Jolt 的软体还在快速演进，成熟管线仍是 Havok / PhysX 的传统强项；
- 团队不熟悉 C++ 并发 → mutex array、锁顺序、Update 期间锁全持有这些规则需要理解 memory model 才能用好，误用不如不用。

---

## 适用边界

Jolt 的 README 末尾有一条容易被忽略的定位声明：它对真实世界刚体行为做近似，**主要面向游戏和 VR 仿真**。工程类仿真（惯性精确、接触求解精度有硬指标的场景）要另行评估。

**适合采用的信号**：

- 新项目，需要在 PC + 主机 + 移动端部署刚体物理，或需要 RISC-V / LoongArch 支持；
- 多线程需求强、有自己的 job system，希望物理数据在主仿真循环外被安全访问；
- 需要 deterministic simulation（lockstep multiplayer、回放系统、AI 训练环境重置）；
- 需要 soft body / hair / vehicle / character 作为一等公民模块；
- 不需要内置渲染 / 资产管线（图形引擎自己接，Jolt 只做物理）。

**不适合的信号**见上一节末尾的五条。一句话版本：如果你的痛点是"物理把主线程卡住"或者"跨平台结果不一致"，Jolt 是对症的；如果你的痛点在渲染、资产或其他子系统的集成上，先解决那个问题。

---

## 动手练习

按下面三条路线验证，每条都能独立完成：

1. **调参跑压测**：按"任务流案例"的 Step 1-2 构建运行 Samples，选 Rig Pile 后按 ESC 用设置菜单把每堆数量和堆数拉满，观察性能分析器里 narrowphase 如何摊到多个线程；再切回 Debug 构建跑同样的参数，感受 20 个与 160 个布娃娃的差距。
2. **验证确定性**：用 `cmake_linux_clang_gcc.sh Release clang++ --deterministic`（脚本会转成 `-DCROSS_PLATFORM_DETERMINISTIC=ON`）构建，勾选 Samples 的 "Check Determinism" 确认通过；再分别在两台不同架构的机器上构建运行，对比行为是否一致。关掉开关重编译，看看 Docs 里描述的哪些不确定性会显现。
3. **写一个最小集成**：基于 `HelloWorld/HelloWorld.cpp`，把地面换成 `HeightFieldShape`，加 100 个随机位置的 box，用 `AddBodiesPrepare / AddBodiesFinalize` 批量提交，测量一次提交 1 个与一次提交 100 个的帧耗时差。

自测三问：`EActivation` 有哪两个值、`DontActivate` 会不会把醒着的 body 弄睡？`AddBodiesFinalize` 为什么需要 `AddState` 参数？跨平台 deterministic 需要开什么开关、代价是多少、应用侧要改掉哪些标准库调用？

---

## 常见问题与排查

**Q：AddBodiesPrepare 之后忘记调 Finalize 会怎样？**

body 不会进入物理系统，`BodyID` 处于"已创建未插入"状态，后续对它的查询不会命中，也不会报错。写代码时把 Prepare 和 Finalize 配对放在同一个函数作用域，或封装成 RAII 对象，避免后台线程的异常路径跳过 Finalize（走 Abort 也要显式调用）。

**Q：为什么我的 ray cast 结果和其他线程不一致？**

两种情况分开看：如果指"和别的线程同一时刻结果不同"，这是设计内行为——跨线程的修改对本线程只保证前后一致，不保证立刻可见；如果指"同一程序多次运行结果不同"，看 `Docs/Architecture.md` 的 Deterministic Simulation 一节——`BroadPhaseQuery` 本来就不保证确定性（包围盒加宽导致），要一致结果用 `NarrowPhaseQuery`，连顺序都要一致就按文档写自定义 `CollisionCollector` 复验并自行排序。

**Q：开 CROSS_PLATFORM_DETERMINISTIC 之后性能掉了多少？**

文档说大约 8%，这是库级别的代价。只在单一平台跑 lockstep 的项目可以不开，省下这 8%。

**Q：链接报错 / 编译失败怎么排查？**

按顺序检查三件事：第一个 include 是不是 `Jolt.h`（官方把这条写在最显眼的位置）；构建类型是否匹配——Debug / Release / Distribution 的库不要混链（Build/README.md 定义了这几种构建类型的行为差异）；目标平台是否在支持列表——比如 WebAssembly 要走 [JoltPhysics.js](https://github.com/jrouwe/JoltPhysics.js) 独立项目，Platform Blue 需要按 NDA 流程自带平台头文件。

**Q：Jolt 能跑在游戏主机上吗？**

README 的支持平台列表里写着 "Platform Blue (a popular game console)"——出于 NDA 原因官方不点名，运行它需要开发者自带构建环境和 PlatformBlue.h（在对应主机开发者论坛获取）。两款已发售的采用作品都在主机上运行过 Jolt，主机适配是现实验证过的路径，具体主机的 SDK 适配需要开发者在自己的授权环境里评估。

---

## 决策建议

按项目现状选：

1. **新项目、跨 PC + 主机 + 移动端 + VR** → Jolt 是开源阵营里少数经过 3A 验证的 production-grade 刚体物理方案，优先试它；
2. **lockstep multiplayer / 回放系统** → Jolt 的 deterministic simulation 是开源实现里少见的完备实做，配合官方文档的边界清单评估；
3. **多线程密集、需要物理数据在主循环外被访问** → Jolt 的并发语义（后台批量构造、查询与修改并行）是它相对传统开源引擎最大的差异点，值得为此做一次原型验证；
4. **已有 PhysX / Havok 管线** → 切换收益（MIT 许可、确定性、多核扩展）和成本（已调好的物理手感、调试工具链、团队习惯）都要算，建议从回放或新 DLC 关卡这类隔离场景试点；
5. **只需要 2D 物理** → Box2D / Chipmunk2D 更轻量，Jolt 是 3D 库；
6. **学习并发引擎设计** → 读 `Jolt/Physics/Collision/BroadPhase/QuadTree.cpp`（无锁四叉树）、`Jolt/Core/MutexArray.h`（分桶锁）、`Jolt/Physics/Body/BodyInterface.cpp`（批量 API），配上 GDC 2022 演讲 notes，是一份带源码的"多核友好物理引擎"公开教材。

---

## 阅读路径

按需读：

- **只想上手**：[HelloWorld/HelloWorld.cpp](https://github.com/jrouwe/JoltPhysics/blob/master/HelloWorld/HelloWorld.cpp) + [JoltPhysicsHelloWorld](https://github.com/jrouwe/JoltPhysicsHelloWorld)（CMake FetchContent 集成）+ [Build/README.md](https://github.com/jrouwe/JoltPhysics/blob/master/Build/README.md)（构建类型与宏定义）
- **想理解架构**：[Docs/Architecture.md](https://github.com/jrouwe/JoltPhysics/blob/master/Docs/Architecture.md)（Bodies / BroadPhase / Islands / Deterministic Simulation 全覆盖）+ [Docs/Samples.md](https://github.com/jrouwe/JoltPhysics/blob/master/Docs/Samples.md) + `Jolt/Physics/PhysicsSystem.h`
- **想看多线程**：`Jolt/Physics/Body/BodyLock.h`（锁接口）+ `Jolt/Core/MutexArray.h`（分桶锁）+ `Jolt/Physics/Body/BodyInterface.cpp`（batch API 实现）+ `Jolt/Core/JobSystemThreadPool.cpp`（示例 job system）
- **想看确定性**：Architecture.md 的 Deterministic Simulation 节 + Build/CMakeLists.txt 里的 `CROSS_PLATFORM_DETERMINISTIC` 选项 + `Jolt/Physics/DeterminismLog.h`
- **想看 GDC 2022 演讲**：[slides](https://gdcvault.com/play/1027560/Architecting-Jolt-Physics-for-Horizon)、[speaker notes 完整版 PDF](https://jrouwe.nl/architectingjolt/ArchitectingJoltPhysics_Rouwe_Jorrit_Notes.pdf)、[video](https://gdcvault.com/play/1027891/Architecting-Jolt-Physics-for-Horizon)
- **想看性能基准**：[Multicore Scaling PDF](https://jrouwe.nl/jolt/JoltPhysicsMulticoreScaling.pdf) + `PerformanceTest/` 目录 + [Docs/PerformanceTest.md](https://github.com/jrouwe/JoltPhysics/blob/master/Docs/PerformanceTest.md)

---

## 进阶方向

把这一篇读透之后，按兴趣选一条：

- **深入并发实现**：读 `BodyInterface.cpp` 的 `AddBodiesPrepare` 实现和 `QuadTree.cpp` 的无锁更新路径，画一张"Prepare 到 Finalize 之间各线程能看到什么"的状态图，对照 Architecture.md 的 Multithreaded Access 节验证自己的理解。
- **做回放系统**：基于 `PhysicsSystem::SaveState / RestoreState` 给自己的项目做输入级回放（只记录输入序列，不记录世界状态），跑通后自然理解 Architecture.md 里 Rolling Back a Simulation 一节讲的 BodyID 一致性问题。
- **读 GDC 2022 演讲**：对照 README 的设计判断逐条映射到演讲里的取舍（演讲约 30 分钟，notes PDF 比幻灯片信息量大得多），再读 `QuadTree.cpp` 验证演讲里"撑大节点、后台重建"的描述。

---

## 参考文献与事实来源

- [jrouwe/JoltPhysics README](https://github.com/jrouwe/JoltPhysics)（2026-09-15 抓取：设计判断、平台矩阵、构建要求、GDC 链接、JoltViewer 说明）
- [Docs/Architecture.md](https://github.com/jrouwe/JoltPhysics/blob/master/Docs/Architecture.md)（Multithreaded Access、Deterministic Simulation、Broad Phase、Island Builder 各节）
- [Docs/Samples.md](https://github.com/jrouwe/JoltPhysics/blob/master/Docs/Samples.md)（Rig 类目与视频列表）
- [Docs/ProjectsUsingJolt.md](https://github.com/jrouwe/JoltPhysics/blob/master/Docs/ProjectsUsingJolt.md)（Godot 4.4、Geekbench 7、Dagor Engine 等采用清单）
- [Build/README.md](https://github.com/jrouwe/JoltPhysics/blob/master/Build/README.md)（构建类型、宏定义、各平台脚本）
- Build/cmake_linux_clang_gcc.sh、cmake_vs2026_cl.bat（构建入口脚本）
- [HelloWorld/HelloWorld.cpp](https://github.com/jrouwe/JoltPhysics/blob/master/HelloWorld/HelloWorld.cpp)（示例代码与常量取值）
- [Samples/Tests/Rig/RigPileTest.cpp](https://github.com/jrouwe/JoltPhysics/blob/master/Samples/Tests/Rig/RigPileTest.cpp)（默认参数、场景列表、上限逻辑）
- [Jolt/Physics/Body/BodyInterface.h](https://github.com/jrouwe/JoltPhysics/blob/master/Jolt/Physics/Body/BodyInterface.h)（batch API 签名与 AddState 定义）
- [Jolt/Physics/EActivation.h](https://github.com/jrouwe/JoltPhysics/blob/master/Jolt/Physics/EActivation.h)（枚举定义）
- JoltViewer/JoltViewer.cpp（命令行用法：`Usage: JoltViewer <recording filename>`）
- [GDC 2022: Architecting Jolt Physics for 'Horizon Forbidden West'](https://gdcvault.com/play/1027560/Architecting-Jolt-Physics-for-Horizon)（slides，同页有 video 与 notes PDF 链接）
- GitHub API 仓库元数据（2026-09-15：JoltPhysics 11,544 stars / 965 forks / MIT；NVIDIA-Omniverse/PhysX 4,768 stars / BSD-3-Clause；bulletphysics/bullet3 14,725 stars）

---

## 边界声明

本文基于 `jrouwe/JoltPhysics` 仓库 master 分支的 README、`Docs/Architecture.md`、`Docs/Samples.md`、`Build/README.md`、构建脚本、关键源码文件以及 GitHub API 元数据（除特别标注外均为 2026-09-15 抓取）。仓库处于活跃迭代期，`BodyInterface` 的批量 API、hair 模拟（较新的功能，仍在演进，环境碰撞目前只支持 ConvexHull 和 CompoundShape）与 broadphase 的实现细节都可能在后续版本调整；deterministic simulation 的边界以 `Docs/Architecture.md` 的 "Deterministic Simulation" 小节为准。

横向对照表中 PhysX 与 Bullet 的多线程、确定性两格本文未逐项核实其官方文档，仅保留仓库元数据与官方自述，选型判断请以各自文档为准；Jolt 相对它们的具体性能差异可参考作者公布的 [Multicore Scaling 报告](https://jrouwe.nl/jolt/JoltPhysicsMulticoreScaling.pdf)（作者自测口径）。
