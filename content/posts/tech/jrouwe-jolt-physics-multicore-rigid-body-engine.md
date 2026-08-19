---
title: 'jrouwe/JoltPhysics 原理拆解：一个被《地平线 西之绝境》和《死亡搁浅 2》选中的多核友好刚体物理引擎是怎么设计的'
date: "2026-07-17T02:57:12+08:00"
slug: "jrouwe-jolt-physics-multicore-rigid-body-engine"
github_repo: "jrouwe/JoltPhysics"
description: "Jolt Physics 是 Jorrit Rouwe 写的 C++ 多核友好刚体物理与碰撞检测库，11.4k stars，被《Horizon Forbidden West》与《Death Stranding 2》采用。本文拆解它的核心设计判断（多线程并发读 / 写、不自动唤醒、确定性边界）、系统地图（Jolt/Physics/Collision/BroadPhase 分层）、与 PhysX/Bullet 的横向对比，以及 GDC 2022 演讲背后的工程取舍。"
categories: ["技术笔记"]
tags: ["C++", "游戏开发"]
---

# Jolt Physics 原理拆解：多核友好的刚体物理引擎是怎么设计的

## 目录

- 一句话判断
- 系统地图
- 边界与角色划分
- 关键机制：五个工程判断是怎么落到代码的
- 任务流案例：跑一个 160 个 ragdoll 的 pile
- 与同类项目的横向对照
- 适用边界
- 动手练习
- 进阶方向
- 参考文献与事实来源
- 边界声明

## 一句话判断

**Jolt Physics（[jrouwe/JoltPhysics](https://github.com/jrouwe/JoltPhysics)）是一个 11.4k stars 的 C++ 刚体物理与碰撞检测库，它的工程价值不在"物理算法新"，而在"多线程友好"这条路上走得非常彻底**。作者 Jorrit Rouwe 在 README 里直接列出五个核心设计判断：① 后台线程并发预构造 body batch；② 碰撞查询与 body 增删并行（单线程改可见，跨线程读看到一致快照）；③ broadphase 查询与 simulation step 并行（narrowphase 后台跑）；④ body 创建 / 删除不自动唤醒邻居；⑤ 仿真 deterministic（同输入必同输出）。这套设计已经被 Guerrilla Games 的《Horizon Forbidden West》和《Death Stranding 2: On the Beach》采用，并在 GDC 2022 上做了公开演讲（"Architecting Jolt Physics for Horizon Forbidden West"）。

阅读目标：读完能判断 Jolt 的多线程模型与 PhysX / Bullet 差在哪，能说清 deterministic simulation 的边界（同平台默认成立、跨平台需要开关），并能跑通一个 160 个 ragdoll 同时下落的示例。不需要先懂物理引擎，但需要 C++ 基础。

如果你在做游戏 / VR / 仿真，并且对 PhysX / Bullet 的"主线程同步"或者"多线程加锁开销"有痛感，这篇文章值得读完整。

---

## 系统地图

```text
┌──────────────────────────────────────────────────────────────────────┐
│                      Jolt Physics (C++ library)                       │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Jolt/                          ← 所有源码                          │ │
│  │    ├─ Core/        Memory / Threading / JobSystem / FP exceptions │ │
│  │    ├─ Math/        Vec / Mat / Quat / AABox                       │ │
│  │    ├─ Geometry/    Convex / Mesh / HeightField / TriangleSplitter │ │
│  │    ├─ Physics/     PhysicsSystem / Body / Constraints            │ │

│  │    │    ├─ Collision/    NarrowPhase + Casts + Collectors         │ │
│  │    │    │    └─ BroadPhase/   QuadTree / BroadPhaseQuadTree       │ │
│  │    │    │                    / BroadPhaseBruteForce / LayerFilter │ │
│  │    ├─ Renderer/    DebugRenderer (recorder + .jor file)           │ │
│  │    ├─ Skeleton/    SkeletalAnimation + Ragdoll mapping            │ │
│  │    ├─ Compute/     Cosserat / SoftBody / GPU hair sim             │ │
│  │    └─ Shaders/     Hair simulation shaders                       │ │
│  └──────────────────────────────────────────────────────────────────┘ │

│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Parallel layers                                                  │ │
│  │    ├─ Thread 1 (main sim): step → broadphase → narrowphase        │ │
│  │    ├─ Background pool: AddBodiesPrepare / Finalize / narrowphase  │ │
│  │    ├─ Game thread: AddBody / RemoveBody / queries (lock-free R/W) │ │
│  │    └─ JobSystem: per-task thread pinning                          │ │
│  └──────────────────────────────────────────────────────────────────┘ │

│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Public surface (BodyInterface / PhysicsSystem)                   │ │
│  │    ├─ Body lifecycle: CreateBody / AddBody / RemoveBody / Destroy │ │
│  │    ├─ Batch: AddBodiesPrepare / AddBodiesFinalize / AddBodiesAbort│ │
│  │    ├─ Queries: ray cast / shape cast / collide shape / overlap    │ │
│  │    ├─ Constraints: Fixed / Hinge / Slider / 6DOF / SoftBody ...   │ │
│  │    └─ Vehicles / Characters / Hair / Soft body                    │ │
│  └──────────────────────────────────────────────────────────────────┘ │

└──────────────────────────────────────────────────────────────────────┘
                          ▼
                Game / VR / Simulation engine
                          ▼
       .jor recording → JoltViewer (Windows / macOS / Linux)
```

这张图最重要的一条路径：**`Jolt/Physics/Collision/BroadPhase/` 是并发性的核心战场**——`QuadTree` 提供 lock-free 的 layer filter（`ObjectVsBroadPhaseLayerFilterMask/Table`），让 query（查询）与 step 可以并行；`Jolt/Physics/Body/BodyInterface.h` 的 batch API（应用程序接口）让后台线程预构造 body 不阻塞主仿真。

---

## 边界与角色划分

Jolt 的工程边界可以按"线程所有权"分三组：

| 线程角色 | 谁负责 | 谁不允许 | 关键 API |
|---|---|---|---|
| 主仿真线程 | Step / broadphase / narrowphase | 同时跑另一个 Step | `PhysicsSystem::Update` |
| 游戏 / 业务线程 | AddBody / RemoveBody / query | 直接改 broadphase 内部 | `BodyInterface` |
| 后台工作线程 | AddBodiesPrepare / narrowphase 后台 batch | 调主 step | `BodyInterface::AddBodiesPrepare` |

不变项之外，**Jolt 明确不做**的事：

- ❌ **不**自动唤醒邻居 body。"Accidental wake up of bodies cause performance problems when loading/unloading content. Therefore, bodies will not automatically wake up when created. Neighboring bodies will not be woken up when bodies are removed."——唤醒要手动触发。
- ❌ **不**用 `new` / `delete` 创建 / 销毁 Body。`BodyInterface::CreateBody` 与 `DestroyBody` 是唯一路径（避免 allocator 失误触发 double free 或 invalid free）。
- ❌ **不**依赖 RTTI 或 exceptions（C++17 + STL only）。原因：① 性能；② 跨平台一致性；③ 与 console SDK（软件开发包）兼容（Platform Blue 等）。
- ❌ **不**保仿真 always-on。冷 body 不参与 narrowphase，CPU 不浪费。
- ❌ **不**提供开箱即用的渲染 / 资产管线。Jolt 只做物理，渲染要 game engine 自己接；`Jolt/Renderer/` 只提供 debug draw 与 .jor 录制。

这五条"不做"恰好决定了 Jolt 的设计取舍——下面拆开看。

---

## 关键机制：五个工程判断是怎么落到代码的

### 1. 后台预构造 + 原子提交：AddBodiesPrepare / Finalize / Abort

`Jolt/Physics/Body/BodyInterface.h` 的批处理 API 是 Jolt 并发性最值得读的一段。注意 `AddBodiesPrepare` 返回一个 `AddState` 句柄，`Finalize` / `Abort` 都要把它传回去：

```cpp
// 主线程：告诉 Jolt "我要加一批 body，先准备"，拿到状态句柄
BodyInterface::AddState state =
    body_interface.AddBodiesPrepare(bodies, numBodies);

// 后台线程：构造 Body、计算 inertia、填 broadphase 节点（不阻塞仿真）
// 这一步完全可以在 job system 里派出去

// 主线程：用句柄原子提交整批
body_interface.AddBodiesFinalize(bodies, numBodies, state, EActivation::Activate);
// 或者中途后悔：
body_interface.AddBodiesAbort(bodies, numBodies, state);
```

为什么必须分两步？因为如果 `AddBody` 是同步的，主线程会被 broadphase 更新阻塞；如果不分 Prepare / Finalize，跨线程读 query 会看到"半批插入"的脏状态。Jolt 的做法是：

- Prepare：把 body 数据填好，但**不**进入 broadphase；
- Finalize：原子地把整批 body 挂进 broadphase；
- Abort：如果玩家突然转身，streamed-in level section 不再需要，扔掉已经 Prepare 的 body，不污染仿真。

README 写得直接："Sections of the simulation can be loaded/unloaded in the background. We prepare a batch of physics bodies on a background thread without locking or affecting the simulation. We insert the batch into the simulation with a minimal impact on performance."

### 2. 单线程改立刻可见 + 跨线程读看到一致快照

Jolt 在 query 与 mutation 的并发上做了一个非常精细的取舍——body 的状态（state）何时可见、可见到什么程度，是这里的核心权衡。README 直接列出来：

> Collision queries can run parallel to adding / removing or updating a body. If a change to a body happened on the same thread, the change will be immediately visible. If the change happened on another thread, the query will see a consistent before or after state. An alternative would be to have a read and write version of the world. This prevents changes from being visible immediately, so we avoid this.

这一条对比 PhysX 的"read/write 双版本世界"——PhysX 的做法是 query 时 lock，commit（提交）时 swap read/write buffer；Jolt 的做法是把状态（state）视图挂在每个线程上、用 lock-free 操作读写，但**保证不会读到半改状态**。代价是 Jolt 必须自己维护 per-thread 的 mutation log（哪些 body 在本帧被改了），query 阶段根据当前查询线程的 view 选择 consistent snapshot。

这个选择的工程含义是：**没有全局 read/write 锁，但 single-frame 内的可见性是有边界的**。如果你的 game thread 改了 body 然后立刻在同一线程 query，OK；如果另一个线程改了 body，当前线程的 query 不会看到这次改，但也不会看到半改。这是 PhysX / Bullet 都没做到的细致语义。

### 3. Broadphase query 与 step 并行

```cpp
// 帧 N：
// 1) 主线程：broadphase coarse query（哪些 body pair 可能相交？）
physics_system.Update(...) → 收集碰撞候选对

// 2) 后台线程：narrowphase（精确 GJK / EPA / CCD）
// 这一步 CPU heavy，可以跨多帧摊销

// 3) 同时主线程继续做下一帧的 broadphase / AI / streaming
```

README 的原话：

> Collision queries can run parallel to the main physics simulation. We do a coarse check (broad phase query) before the simulation step and do fine checks (narrow phase query) in the background. This way, long running processes (like navigation mesh generation) can be spread out across multiple frames.

注意 `broad phase query` 的双重含义：① step 内部的碰撞对粗筛；② 游戏的 query（射线、shape cast、overlap）。这两类查询走的都是 `Jolt/Physics/Collision/BroadPhase/`，但路径不同——step 内的走 `BroadPhaseQuery`（已 pair 化的对集），游戏的走 `BroadPhase` 单点查询。

### 4. 不自动唤醒 + 双阶段 sleep/wake

`Body` 的 `EMotionType` 决定行为，但 activation 是独立的 state machine。Jolt 的默认姿态是：

```cpp
// CreateBody + AddBody 不会自动唤醒邻居
body_interface.AddBody(bodyID, EActivation::DontActivate);

// 显式激活才进入 narrowphase
body_interface.ActivateBody(bodyID);

// RemoveBody 不唤醒任何东西
body_interface.RemoveBody(bodyID);
```

为什么要这样？因为 game streaming 经常要"先卸载一段地形，再加载新一段"——如果 remove 会唤醒所有邻居，broadphase 会被无意义地更新；如果 create 会唤醒周围所有 dynamic body，物理状态会被无意义地扰动。Jolt 把"什么时候唤醒"完全交给 game code 自己决定。

`EActivation` 枚举只有两个值（`Jolt/Physics/EActivation.h`）：

- `Activate`：立即 wake，进入 narrowphase；
- `DontActivate`：保持当前状态（不会把已激活的 body 弄睡，只是不主动唤醒）。

没有"只唤醒自己、不传染邻居"的第三态——不想传染就把激活操作放进不共享的路径自己控制。

### 5. Deterministic simulation：边界比口号重要

Jolt 的 simulation 是 deterministic 的，README 的限制声明：

> The simulation runs deterministically. You can replicate a simulation to a remote client by merely replicating the inputs to the simulation. Read the Deterministic Simulation section to understand the limits.

但 `Docs/Architecture.md` 把边界说得很细，两点必须记住：

- **默认只保证同平台**：只要用同一份二进制、按同样顺序调用修改 API，同输入必同输出（AMD / Intel 都无所谓）。
- **跨平台需要开关**：打开 CMake 选项 `CROSS_PLATFORM_DETERMINISTIC`，代价是大约慢 8%，之后编译器（MSVC / clang / gcc / emscripten）、配置（Debug / Release）、OS（Windows / macOS / Linux）、架构（x86 / ARM / RISC-V / PowerPC / LoongArch）、字长（32 / 64 bit）都不影响结果。

还有一个容易踩的坑：**BroadPhaseQuery 不是 deterministic 的**。broad phase 树会被多线程修改，body 的包围盒在维护更新前会被加宽，查询结果可能不同。要确定性查询，得自己写 `CollisionCollector`，在 `AddHit` 里用 `Body::GetWorldSpaceBounds` 复核真实包围盒。NarrowPhaseQuery 结果一致，但返回顺序可能变化。

这意味着 lockstep multiplayer 客户端可以只同步"输入序列"（玩家操作、AI 决策），不需要同步"完整世界状态"。代价是浮点必须严格（默认 SSE2），要按 `Docs/Architecture.md` 的要求编译：`-ffp-model=precise`（clang）/ `/fp:precise`（MSVC）、关闭浮点 contract（`-ffp-contract=off`）、保证各平台 / 各线程 FPU 状态一致（rounding 为 nearest，DAZ / FTZ 标志一致）。

### 6. HelloWorld 的最小骨架

`HelloWorld/HelloWorld.cpp` 是上手的最短路径（README 推荐）。注意第一个 include 必须是 `Jolt.h`，注释里特别强调："The Jolt headers don't include Jolt.h. Always include Jolt.h before including any other Jolt header."

```cpp
// 1) 注册 allocator / factory / logger（一次性）
RegisterDefaultAllocator();
Factory::sInstance = new Factory();
RegisterTypes();

// 2) 创建 PhysicsSystem
TempAllocatorImpl temp_allocator(10 * 1024 * 1024);  // 预分配 10 MB
JobSystemThreadPool job_system(cMaxPhysicsJobs, cMaxPhysicsBarriers,
                               thread::hardware_concurrency() - 1);
PhysicsSystem physics_system;
physics_system.Init(cMaxBodies, cNumBodyMutexes, cMaxBodyPairs, cMaxContactConstraints,
                    broad_phase_layer_interface, object_vs_broadphase_layer_filter,
                    object_vs_object_layer_filter);

// 3) BodyInterface
BodyInterface &body_interface = physics_system.GetBodyInterface();

// 4) 加 ground plane
BoxShapeSettings floor_shape_settings(Vec3(100.0f, 1.0f, 100.0f));
ShapeSettings::ShapeResult floor_shape_result = floor_shape_settings.Create();
ShapeRefC floor_shape = floor_shape_result.Get();
BodyCreationSettings floor_settings(floor_shape, RVec3(0.0_r, -1.0_r, 0.0_r),
                                    Quat::sIdentity(), EMotionType::Static, Layers::NON_MOVING);
body_interface.CreateAndAddBody(floor_settings, EActivation::DontActivate);

// 5) 仿真循环：60 Hz 步长，直到球睡着
const float cDeltaTime = 1.0f / 60.0f;
while (body_interface.IsActive(sphere_id)) {
    body_interface.SetLinearVelocity(sphere_id, Vec3(0.0f, -5.0f, 0.0f));
    physics_system.Update(cDeltaTime, 1, &temp_allocator, &job_system);
}
```

CMake 集成走 `Jolt/Jolt.cmake` + FetchContent（独立仓库 [JoltPhysicsHelloWorld](https://github.com/jrouwe/JoltPhysicsHelloWorld) 演示）。`JobSystemThreadPool` 是示例实现，README 建议生产项目自己实现 `JobSystem` 接口，让 Jolt 跑在自己的 job scheduler 上。

---

## 任务流案例：跑一个 160 个 ragdoll 的 pile

`Docs/Samples.md` 列出大量 sample，README 顶部 YouTube 视频是"160 Ragdolls in a Pile"（160 个布娃娃从《Horizon Zero Dawn》场景里砸下来）。把上面的零件拼起来：

**Step 1：环境**

```bash
git clone https://github.com/jrouwe/JoltPhysics
cd JoltPhysics
cmake -B build -DCMAKE_BUILD_TYPE=Release -DTARGET_SAMPLES=1
cmake --build build --config Release
```

**Step 2：跑 Samples app**

```bash
./build/Samples
```

**Step 3：选 "Rig Pile" sample**

源码在 `Samples/Tests/Rig/RigPileTest.cpp`。默认参数：debug 构建每堆 5 个 ragdoll、每轴 2 堆；release 构建每堆 10 个、每轴 4 堆（10 × 4 × 4 = 160 个）。scene 默认是 `PerlinMesh`，也可以切到 `Terrain1` / `Terrain2`（需要 ObjectStream 支持）。

**Step 4：观察并发行为**

- 主线程：broadphase 收集碰撞对；
- 后台线程：narrowphase（GJK / EPA）算接触点 + 约束求解；
- 游戏线程：UI 渲染 + 输入处理；
- JobSystem：每个 narrowphase 任务派到独立 worker，per-thread pinning 避免 false sharing。

CPU profile 会看到 narrowphase CPU 占用被摊到多个 worker，主线程只负责 broadphase + step 调度——这就是 README 里 "long running processes can be spread out across multiple frames" 的实战形态。

**Step 5：跨平台验证**

把 `JoltViewer`（`./build/JoltViewer --jor recording.jor`）跑起来，跨平台重放 `.jor` 文件验证 deterministic 输出。

---

## 与同类项目的横向对照

| 维度 | Jolt | PhysX | Bullet | Havok |
|---|---|---|---|---|
| 语言 | C++17（无 RTTI / exceptions） | C++ | C++ | C++（闭源） |
| License | MIT | BSD-3（已开源） | Zlib | 商业 |
| Stars | 11.4k | 4.7k（NVIDIA-Omniverse/PhysX） | 14.7k | n/a |
| 物理范围 | rigid + soft + hair + vehicles + characters | rigid + soft + cloth + particles | rigid + soft + cloth + vehicles | rigid + soft + cloth + AI |
| 多线程模型 | lock-free per-thread + batch prepare/finalize | read/write 双版本世界 | sequential + OpenMP 可选 | job-based 闭源 |
| Deterministic | ✅ 同平台默认；跨平台需开关 | ❌ 默认非 deterministic | 部分（依赖平台） | ❌ |
| 默认不唤醒 | ✅ 必须手动 activate | ❌ 默认 propagate | ❌ 默认 propagate | ❌ |
| 跨平台 | Win/Linux/macOS/Android/iOS/WASM/RISC-V/LoongArch/PPC/Blue | Win/Linux/macOS/Android/iOS/Xbox/PS/Switch | Win/Linux/macOS/Android | 主流 console |
| 自带 GPU hair sim | ✅ Cosserat + grid velocity | ❌ | ❌ | ❌ |
| 公开 GDC 演讲 | ✅ GDC 2022 | ✅ 多场 | ❌ | ❌ |

这张表想表达一件事：**Jolt 不是"另一个 PhysX 翻版"，它是少数同时把"lock-free 多线程 + 严格 deterministic + 开源 MIT + 跨 RISC-V/LoongArch + GPU hair sim"塞进同一个 C++17 库的项目**。它的工程取舍（不自动唤醒、不 RTTI、不 exceptions）都是为了 console-grade 性能与跨平台一致性。

---

## 适用边界

**推荐使用**：

- 新游戏项目、需要在 PC + console + mobile 跨平台部署刚体物理
- 多线程需求强、有专门的 job system、痛恨 PhysX 的 read/write 锁 / Bullet 的 sequential 性能
- 需要 deterministic simulation（lockstep multiplayer、回放系统、AI 训练数据采集）
- 需要 soft body / hair / vehicle / character 这些 first-class 模块
- 不需要 GUI（图形用户界面）/ 渲染 / 资产生命周期管理（这些 game engine 自己接）

社区验证案例（`Docs/ProjectsUsingJolt.md`）比 README 两句更有说服力：Godot 4.4 把它作为官方可选物理后端、Geekbench 7 用它做物理基准、War Thunder 的 Dagor Engine 用它、还有 ezEngine、GDevelop、Qt Quick 3D 的 Jolt 绑定等。生产级验证案例已经不是个位数。

**不推荐使用**：

- 只需要简单 sphere-on-plane demo → 直接用任何库都行，Jolt 的 batch API 是 overkill
- 已经在用某个游戏引擎（Unity / Unreal / Godot 4）的内建物理 → 切换成本远大于收益
- 需要 GPU 上的大规模粒子（百万级） → Jolt 是 CPU 库，看 PhysX / FleX / Box2D 的 GPU 版本
- 需要 cloth / destruction 的成熟管线 → Jolt 的 soft body 在持续迭代，但 production 验证案例少于 Havok / PhysX
- 不熟悉 C++17 现代并发语义 → Jolt 的 per-thread view 机制需要理解 memory model，否则容易踩坑

---

## 动手练习

按下面三条路线验证，每条都能独立完成：

1. **编译并跑 Samples**：按"任务流案例"的 Step 1-3 操作，把 `RigPileTest.cpp` 里的 `sPileSize` 从 5 改成 20 重新编译，观察 CPU profile 中 narrowphase 如何摊到多个线程。改之前先读 `Docs/Samples.md` 了解 UI 快捷键。
2. **验证 deterministic**：在 CMake 里开 `CROSS_PLATFORM_DETERMINISTIC=ON`，把同一个 scene 录成 `.jor` 文件，分别在 macOS 和 Linux（或不同编译器）上重放，对比每帧的 body 变换是否一致。再试一下关掉开关，看结果是否分叉。
3. **写一个最小集成**：基于 `HelloWorld/HelloWorld.cpp`，把地面换成高度场（`HeightFieldShape`），加 100 个随机位置的 box，用 `AddBodiesPrepare / Finalize` 批量提交，测量一次提交 1 个与一次提交 100 个的帧耗时差。

自测：能否说出 `EActivation` 有几个值？`AddBodiesFinalize` 为什么需要 `AddState` 参数？跨平台 deterministic 的开关和代价是什么？

---

## 常见问题与排查

**Q：AddBodiesPrepare 之后忘记调 Finalize 会怎样？**

body 不会进入仿真，`BodyID` 处于"已创建未插入"状态，后续对它的查询 / 修改不会生效，也不会报错。写代码时把 Prepare 和 Finalize 配对放在同一个函数作用域，或封装成 RAII 对象，避免后台线程异常路径跳过 Finalize。

**Q：为什么我的 ray cast 结果和其他线程不一致？**

看 `Docs/Architecture.md` 的 deterministic 一节：BroadPhaseQuery 本来就不保证确定性（包围盒加宽导致）。如果只是要"一致的查询结果"，用 NarrowPhaseQuery；如果连顺序都要一致，需要自定义 `CollisionCollector` 复核。

**Q：开 CROSS_PLATFORM_DETERMINISTIC 之后性能掉了多少？**

文档说大约 8%。这是全库级别的影响，不是只影响特定场景。如果项目只在单一平台跑 lockstep，可以不开，省下这 8%。

**Q：链接报错 / 编译失败怎么排查？**

先确认第一个 include 是 `Jolt.h`；再确认链接了 `Jolt` 库且没有同时启用 `JPH_DEBUG` 与 release 库混链；最后看 `Build/README.md` 的平台矩阵——例如 WebAssembly 需要走 [JoltPhysics.js](https://github.com/jrouwe/JoltPhysics.js) 单独项目，不是直接编。

**Q：Jolt 能跑在 Switch / PS5 上吗？**

官方平台列表里没有公开列 console，但 `Platform Blue`（一个流行游戏主机）在列表里，说明 console SDK 兼容性是设计目标。具体主机要自己评估 SDK 适配。

---

## 决策建议

按项目现状选：

1. **新项目、跨 PC + console + mobile + VR** → Jolt 是当前 MIT 阵营里唯一可选的 production-grade 方案
2. **lockstep multiplayer / 回放系统** → Jolt 的 deterministic simulation 是少数开源实做
3. **多线程密集、需要 narrowphase 后台跑** → Jolt 的 batch prepare/finalize + parallel narrowphase 显著优于 Bullet
4. **已经有 PhysX pipeline** → 切换收益评估：多线程 + deterministic + MIT 是主要收益；切换成本（已训练的 physics behavior、调试工具链）也要算
5. **只需要 2D 物理** → Box2D / Chipmunk2D 更轻量，Jolt 是 3D 库
6. **学习 / 研究目的** → 看 `Jolt/Physics/Collision/BroadPhase/QuadTree.cpp` + `Jolt/Physics/Body/BodyInterface.cpp` 是少数公开的"lock-free game physics"参考实现

---

## 阅读路径

按需读：

- **只想上手**：`HelloWorld/HelloWorld.cpp` + [JoltPhysicsHelloWorld](https://github.com/jrouwe/JoltPhysicsHelloWorld) + `Build/README.md`
- **想理解架构**：`Docs/Architecture.md`（Bodies / BroadPhase / Constraints / Vehicles 全覆盖）+ `Docs/Samples.md` + `Jolt/Physics/PhysicsSystem.h`
- **想看多线程**：`Jolt/Core/JobSystemThreadPool.cpp` + `Jolt/Core/Mutex.h`（per-thread atomics）+ `Jolt/Physics/Body/BodyInterface.cpp`（batch API）
- **想看 deterministic**：`Docs/Architecture.md` 的 Deterministic Simulation 节 + 编译选项（`CROSS_PLATFORM_DETERMINISTIC`、`USE_AVX2` / `USE_AVX512` 对结果的影响）
- **想看 GDC 2022 演讲背后的工程取舍**：GDC Vault slides + Jolt 作者 notes
- **想看性能基准**：`Docs/PerformanceTest.md` + [Multicore Scaling PDF](https://jrouwe.nl/jolt/JoltPhysicsMulticoreScaling.pdf) + `PerformanceTest/` 二进制

---

## 进阶方向

把这一篇读透之后，按兴趣选一条：

- **深入并发实现**：读 `Jolt/Core/JobSystemThreadPool.cpp` 和 `Jolt/Physics/Body/BodyInterface.cpp` 的 `AddBodiesPrepare` 实现，画一张"Prepare 到 Finalize 之间各线程能看到什么"的状态图，然后对照 `Docs/Architecture.md` 的 Multithreaded Access 节验证。
- **做回放系统**：基于 `JoltViewer` + `.jor` 格式，给自己的项目写一个输入级回放（只记录输入序列，不记录世界状态），跑通后自然理解 deterministic 的边界在哪。
- **读 GDC 2022 演讲**：从 GDC Vault 看原版演讲（30 分钟），对照 README 五个设计判断，把演讲里提到的取舍逐条映射到本文的机制小节。

---

## 参考文献与事实来源

- [jrouwe/JoltPhysics README](https://github.com/jrouwe/JoltPhysics)（2026-08-19 抓取）
- [Docs/Architecture.md](https://github.com/jrouwe/JoltPhysics/blob/master/Docs/Architecture.md)（Deterministic Simulation、Broad Phase、Multithreaded Access 节）
- [Docs/Samples.md](https://github.com/jrouwe/JoltPhysics/blob/master/Docs/Samples.md)（Rig 类目与 160 Ragdolls 视频）
- [Docs/ProjectsUsingJolt.md](https://github.com/jrouwe/JoltPhysics/blob/master/Docs/ProjectsUsingJolt.md)
- [Docs/PerformanceTest.md](https://github.com/jrouwe/JoltPhysics/blob/master/Docs/PerformanceTest.md)
- [HelloWorld/HelloWorld.cpp](https://github.com/jrouwe/JoltPhysics/blob/master/HelloWorld/HelloWorld.cpp)（源码）
- [Jolt/Physics/Body/BodyInterface.h](https://github.com/jrouwe/JoltPhysics/blob/master/Jolt/Physics/Body/BodyInterface.h)（batch API 签名）
- [Jolt/Physics/EActivation.h](https://github.com/jrouwe/JoltPhysics/blob/master/Jolt/Physics/EActivation.h)（枚举定义）
- [GDC 2022: Architecting Jolt Physics for Horizon Forbidden West](https://gdcvault.com/play/1027560/Architecting-Jolt-Physics-for-Horizon)（slides）
- GitHub API 仓库元数据（2026-08-19：JoltPhysics 11,377 stars / 963 forks；PhysX 4,729 stars；bullet3 14,681 stars）

---

## 边界声明

本文基于 `jrouwe/JoltPhysics` 仓库 README（2026-08-19 抓取）、`Docs/Architecture.md`、`Docs/Samples.md`、`Build/README.md`、GitHub API 仓库元数据。仓库处于活跃迭代期，`BodyInterface` 的 batch API 与 `BroadPhase` 的具体实现可能在未来版本微调；deterministic simulation 边界（哪些特性 deterministic、哪些不）以 `Docs/Architecture.md` 的"Deterministic Simulation"小节为准。

Jolt 是少数同时把"lock-free 多线程 + 严格 deterministic + MIT + RISC-V/LoongArch 支持 + GPU hair sim"塞进同一 C++17 库的项目；如果你的工作流强依赖 PhysX 的 GPU rigid body pipeline 或 Havok 的成熟 cloth，需要评估 Jolt 在这些维度的功能完整度。
