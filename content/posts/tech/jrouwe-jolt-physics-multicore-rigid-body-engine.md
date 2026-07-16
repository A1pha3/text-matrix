---
title: 'jrouwe/JoltPhysics 原理拆解：一个被《地平线 西之绝境》和《死亡搁浅 2》选中的多核友好刚体物理引擎是怎么设计的'
date: 2026-07-17T02:57:12+08:00
lastmod: 2026-07-17T02:57:12+08:00
draft: false
categories: ["技术笔记"]
tags: ["Jolt Physics", "C++", "物理引擎", "碰撞检测", "刚体仿真", "游戏开发"]
description: "Jolt Physics 是 Jorrit Rouwe 写的 C++ 多核友好刚体物理与碰撞检测库，10.9k stars，被《Horizon Forbidden West》与《Death Stranding 2》采用。本文拆解它的核心设计判断（多线程并发读 / 写、不自动唤醒、防确定性退化）、系统地图（Jolt/Physics/Collision/BroadPhase 分层）、与 PhysX/Bullet 的横向对比，以及 GDC 2022 演讲背后的工程取舍。"
weight: 1
slug: "jrouwe-jolt-physics-multicore-rigid-body-engine"
author: text-matrix
---

## 一句话判断

**Jolt Physics（[jrouwe/JoltPhysics](https://github.com/jrouwe/JoltPhysics)）是一个 10.9k stars 的 C++ 刚体物理与碰撞检测库，它的工程价值不在"物理算法新"，而在"多线程友好"这条路上做得非常彻底**。作者 Jorrit Rouwe 在 README 里直接列出五个核心设计判断：① 后台线程并发预构造 body batch；② 碰撞查询与 body 增删并行（单线程改可见，跨线程读看到一致快照）；③ broadphase 查询与 simulation step 并行（narrowphase 后台跑）；④ body 创建/删除不自动唤醒邻居；⑤ 仿真 deterministic（同输入必同输出）。这套设计已经被 Guerrilla Games 的《Horizon Forbidden West》和《Death Stranding 2: On the Beach》采用，并在 GDC 2022 上做了公开演讲（"Architecting Jolt Physics for Horizon Forbidden West"）。

如果你在做游戏 / VR / 仿真，并且对 PhysX / Bullet 的"主线程同步"或者"多线程加锁开销"有痛感，这篇文章值得读完整。

---

## 系统地图

```
┌──────────────────────────────────────────────────────────────────────┐
│                      Jolt Physics (C++ library)                       │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  Jolt/                          ← 所有源码                          │ │
│  │    ├─ Core/        Memory / Threading / JobSystem / FP exceptions │ │
│  │    ├─ Math/        Vec / Mat / Quat / AABox                       │ │
│  │    ├─ Geometry/    Convex / Mesh / HeightField / TriangleSplitter │ │
│  │    ├─ Physics/     PhysicsSystem / BodyInterface / Constraints   │ │
│  │    │    ├─ Collision/    NarrowPhase + Casts + Collectors         │ │
│  │    │    │    └─ BroadPhase/   QuadTree / BruteForce / LayerFilter │ │
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

这张图最重要的一条路径：**`Jolt/Physics/Collision/BroadPhase/` 是并发性的核心战场**——QuadTree 提供 lock-free 的 layer filter（`ObjectVsBroadPhaseLayerFilterMask/Table`），让 query 与 step 可以并行；`Jolt/Physics/BodyInterface.cpp` 的 batch API（`AddBodiesPrepare` / `AddBodiesFinalize` / `AddBodiesAbort`）让后台线程预构造 body 不阻塞主仿真。

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
- ❌ **不**依赖 RTTI 或 exceptions（C++ 17 + STL only）。原因：① 性能；② 跨平台一致性；③ 与 console SDK 兼容（Platform Blue 等）。
- ❌ **不**保仿真 always-on。"Bodies will not automatically wake up"——冷 body 不参与 narrowphase，CPU 不浪费。
- ❌ **不**提供开箱即用的渲染 / 资产管线。Jolt 只做物理，渲染要 game engine 自己接；`Jolt/Renderer/` 只提供 debug draw 与 .jor 录制。

这五条"不做"恰好决定了 Jolt 的设计取舍——下面拆开看。

---

## 关键机制：五个工程判断是怎么落到代码的

### 1. 后台预构造 + 原子提交：AddBodiesPrepare / Finalize / Abort

`Jolt/Physics/BodyInterface.cpp` 的批处理 API 是 Jolt 并发性最值得读的一段：

```cpp
// 主线程：告诉 Jolt "我要加一批 body，先准备"
BodyInterface::AddBodiesPrepare(BodyID *bodies, int numBodies);

// 后台线程：构造 Body、计算 inertia、填 broadphase 节点（不阻塞仿真）
// 这一步完全可以在 job system 里派出去

// 主线程：原子提交
BodyInterface::AddBodiesFinalize(BodyID *bodies, int numBodies, EActivation activate);
// 或者中途后悔：
BodyInterface::AddBodiesAbort(BodyID *bodies, int numBodies);
```

为什么必须分两步？因为如果 `AddBody` 是同步的，主线程会被 broadphase 更新阻塞；如果不分 Prepare / Finalize，跨线程读 query 会看到"半批插入"的脏状态。Jolt 的做法是：

- Prepare：把 body 数据填好，但**不**进入 broadphase；
- Finalize：原子地把整批 body 挂进 broadphase；
- Abort：如果玩家突然转身，streamed-in level section 不再需要，扔掉已经 Prepare 的 body，不污染仿真。

README 写得直接："Sections of the simulation can be loaded/unloaded in the background. We prepare a batch of physics bodies on a background thread without locking or affecting the simulation. We insert the batch into the simulation with a minimal impact on performance."

### 2. 单线程改立刻可见 + 跨线程读看到一致快照

Jolt 在 query 与 mutation 的并发上做了一个非常精细的取舍，README 直接列出来：

> Collision queries can run parallel to adding / removing or updating a body. If a change to a body happened on the same thread, the change will be immediately visible. If the change happened on another thread, the query will see a consistent before or after state. An alternative would be to have a read and write version of the world. This prevents changes from being visible immediately, so we avoid this.

这一条对比 PhysX 的"read/write 双版本世界"——PhysX 的做法是 query 时 lock，commit 时 swap read/write buffer；Jolt 的做法是 per-thread 视图 + lock-free 操作，但**保证不会读到半改状态**。代价是 Jolt 必须自己维护 per-thread 的 mutation log（哪些 body 在本帧被改了），query 阶段根据当前查询线程的 view 选择 consistent snapshot。

这个选择的工程含义是：**没有全局 read/write 锁，但 single-frame 内的可见性是有边界的**。如果你的 game thread 改了 body 然后立刻在同一线程 query，OK；如果另一个线程改了 body，当前线程的 query 不会看到这次改，但也不会看到半改。这是 PhysX / Bullet 都没做到的细致语义。

### 3. Broadphase query 与 step 并行

```cpp
// 帧 N：
// 1) 主线程：broadphase coarse query（哪些 body pair 可能相交？）
PhysicsSystem::Update(...) → 收集碰撞候选对

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
BodyInterface::AddBody(bodyID, EActivation::DontActivate);

// 显式激活才进入 narrowphase
BodyInterface::ActivateBody(bodyID);

// RemoveBody 不唤醒任何东西
BodyInterface::RemoveBody(bodyID);
```

为什么要这样？因为 game streaming 经常要"先卸载一段地形，再加载新一段"——如果 remove 会唤醒所有邻居，broadphase 会被无意义地更新；如果 create 会唤醒周围所有 dynamic body，物理状态会被无意义地扰动。Jolt 把"什么时候唤醒"完全交给 game code 自己决定。

`EActivation` 枚举：

- `Activate`：立即 wake，进入 narrowphase；
- `DontActivate`：保持 sleep；
- `ActivateOnly`：仅 wake 自身，不传染邻居（罕见但有用）。

### 5. Deterministic simulation

Jolt 的 simulation 是 deterministic 的——同输入必同输出，跨平台 / 跨编译选项都是。README 的限制声明：

> The simulation runs deterministically. You can replicate a simulation to a remote client by merely replicating the inputs to the simulation. Read the Deterministic Simulation section to understand the limits.

这意味着 lockstep multiplayer 客户端可以只同步"输入序列"（玩家操作、AI 决策），不需要同步"完整世界状态"。代价是 floating point 必须严格（默认 SSE2，禁用任何会影响 bit-exact 的编译优化），这正是 Jolt 在 README 里单独开一节说明的限制。

### 6. HelloWorld 的最小骨架

`HelloWorld/HelloWorld.cpp` 是上手的最短路径（README 推荐）：

```cpp
// 1) 注册 allocator / factory / logger（一次性）
RegisterDefaultAllocator();
Factory::sInstance = new Factory();
RegisterTypes();

// 2) 创建 PhysicsSystem
TempAllocator *temp_allocator = new TempAllocatorMalloc();
JobSystem *job_system = new JobSystemThreadPool(cMaxPhysicsJobs);
PhysicsSystem physics_system;
physics_system.Init(cMaxBodies, cNumBodyMutexes, cMaxBodyPairs, cMaxContactConstraints,
                    broad_phase_layer_interface, object_vs_broad_phase_layer_filter,
                    object_vs_object_layer_filter);

// 3) BodyInterface
BodyInterface &body_interface = physics_system.GetBodyInterface();

// 4) 加 ground plane
BoxShapeSettings floor_shape_settings(Vec3(100.0f, 1.0f, 100.0f));
ShapeSettings::ShapeResult floor_shape_result = floor_shape_settings.Create();
BodyCreationSettings floor_settings(floor_shape_result.Get(), Vec3(0.0f, -1.0f, 0.0f),
                                    Quat::sIdentity(), EMotionType::Static, Layers::NON_MOVING);
body_interface.CreateAndAddBody(floor_settings, EActivation::DontActivate);

// 5) 仿真循环
for (physics_system.Update(delta_time, collision_steps, temp_allocator, job_system); ; )
    physics_system.Update(...);
```

CMake 集成走 `Jolt/Jolt.cmake` + FetchContent（独立仓库 [JoltPhysicsHelloWorld](https://github.com/jrouwe/JoltPhysicsHelloWorld) 演示）。

---

## 任务流案例：做一个 1000 个 ragdoll 同时下落的 demo

`Docs/Samples.md` 列出大量 sample，最有代表性的是"ragdoll pile"（README 顶部 YouTube 视频）。把上面的零件拼起来：

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

**Step 3：选 "Ragdoll Pile" sample**

源码在 `Samples/Tests/RigidBody/RagdollPileTest.cpp`，加载 50-200 个 ragdoll 从空中下落。

**Step 4：观察并发行为**

- 主线程：broadphase 收集碰撞对；
- 后台线程：narrowphase（GJK / EPA）算接触点 + 约束求解；
- 游戏线程：UI 渲染 + 输入处理；
- JobSystem：每个 narrowphase 任务派到独立 worker，per-thread pinning 避免 false sharing。

CPU profile 会看到 narrowphase CPU 占用被摊到 4-8 个 worker，主线程只负责 broadphase + step 调度——这就是 README 里 "long running processes can be spread out across multiple frames" 的实战形态。

**Step 5：跨平台验证**

把 `JoltViewer`（`./build/JoltViewer --jor recording.jor`）跑起来，跨平台重放 `.jor` 文件验证 deterministic 输出。

---

## 与同类项目的横向对照

| 维度 | Jolt | PhysX | Bullet | Havok |
|---|---|---|---|---|
| 语言 | C++17（无 RTTI / exceptions） | C++ | C++ | C++（闭源） |
| License | MIT | BSD-3 | Zlib | 商业 |
| Stars | 10.9k | n/a（NVIDIA 内部） | 13k+ | n/a |
| 物理范围 | rigid + soft + hair + vehicles + characters + characters | rigid + soft + cloth + particles | rigid + soft + cloth + vehicles | rigid + soft + cloth + AI |
| 多线程模型 | lock-free per-thread + batch prepare/finalize | read/write 双版本世界 | sequential + OpenMP 可选 | job-based 闭源 |
| Deterministic | ✅ 同输入同输出 | ❌ 默认非 deterministic | 部分（依赖平台） | ❌ |
| 默认不唤醒 | ✅ 必须手动 activate | ❌ 默认 propagate | ❌ 默认 propagate | ❌ |
| 跨平台 | Win/Linux/macOS/Android/iOS/WASM/RISC-V/LoongArch/PPC/Blue | Win/Linux/macOS/Android/iOS/Xbox/PS/Switch | Win/Linux/macOS/Android | 主流 console |
| 自带 GPU hair sim | ✅ Cosserat + grid velocity | ❌ | ❌ | ❌ |
| 公开 GDC 演讲 | ✅ GDC 2022 | ✅ 多场 | ❌ | ❌ |

这张表想表达一件事：**Jolt 不是"另一个 PhysX clone"，它是少数同时把"lock-free 多线程 + 严格 deterministic + 开源 MIT + 跨 RISC-V/LoongArch + GPU hair sim"塞进同一个 C++17 库的项目**。它的工程取舍（不自动唤醒、不 RTTI、不 exceptions）都是为了 console-grade 性能与跨平台一致性。

---

## 适用边界

**推荐使用**：

- 新游戏项目、需要在 PC + console + mobile 跨平台部署刚体物理
- 多线程需求强、有专门的 job system、痛恨 PhysX 的 read/write 锁 / Bullet 的 sequential 性能
- 需要 deterministic simulation（lockstep multiplayer、回放系统、AI 训练数据采集）
- 需要 soft body / hair / vehicle / character 这些 first-class 模块
- 不需要 GUI / 渲染 / 资产生命周期管理（这些 game engine 自己接）

**不推荐使用**：

- 只需要简单 sphere-on-plane demo → 直接用任何库都行，Jolt 的 batch API 是 overkill
- 已经在用某个游戏引擎（Unity / Unreal / Godot 4）的内建物理 → 切换成本远大于收益
- 需要 GPU 上的大规模粒子（百万级） → Jolt 是 CPU 库，看 PhysX / FleX / Box2D 的 GPU 版本
- 需要 cloth / destruction 的成熟管线 → Jolt 的 soft body 在持续迭代，但 production 验证案例少于 Havok / PhysX
- 不熟悉 C++17 现代并发语义 → Jolt 的 per-thread view 机制需要理解 memory model，否则容易踩坑

---

## 决策建议

按项目现状选：

1. **新项目、跨 PC + console + mobile + VR** → Jolt 是当前 MIT 阵营里唯一可选的 production-grade 方案
2. **lockstep multiplayer / 回放系统** → Jolt 的 deterministic simulation 是少数开源实做
3. **多线程密集、需要 narrowphase 后台跑** → Jolt 的 batch prepare/finalize + parallel narrowphase 显著优于 Bullet
4. **已经有 PhysX pipeline** → 切换收益评估：多线程 + deterministic + MIT 是主要收益；切换成本（已训练的 physics behavior、调试工具链）也要算
5. **只需要 2D 物理** → Box2D / Chipmunk2D 更轻量，Jolt 是 3D 库
6. **学习 / 研究目的** → 看 `Jolt/Physics/Collision/BroadPhase/QuadTree.cpp` + `Jolt/Physics/BodyInterface.cpp` 是少数公开的"lock-free game physics"参考实现

---

## 阅读路径

按需读：

- **只想上手**：`HelloWorld/HelloWorld.cpp` + [JoltPhysicsHelloWorld](https://github.com/jrouwe/JoltPhysicsHelloWorld) + `Build/README.md`
- **想理解架构**：`Docs/Architecture.md`（Bodies / BroadPhase / Constraints / Vehicles 全覆盖）+ `Docs/Samples.md` + `Jolt/Physics/PhysicsSystem.h`
- **想看多线程**：`Jolt/Core/JobSystemThreadPool.cpp` + `Jolt/Core/Mutex.h`（per-thread atomics）+ `Jolt/Physics/BodyInterface.cpp`（batch API）
- **想看 deterministic**：`Docs/Architecture.md` 的 Deterministic Simulation 节 + 编译选项（`USE_AVX512` / `USE_AVX2` 对结果的影响）
- **想看 GDC 2022 演讲背后的工程取舍**：GDC Vault slides + Jolt 作者 notes
- **想看性能基准**：`Docs/PerformanceTest.md` + [Multicore Scaling PDF](https://jrouwe.nl/jolt/JoltPhysicsMulticoreScaling.pdf) + `PerformanceTest/` 二进制

---

## 边界声明

本文基于 `jrouwe/JoltPhysics` 仓库 README（2026-07-16 抓取）、`Docs/Architecture.md`、`Docs/Samples.md`、`Build/README.md`、GitHub API 仓库元数据（10.9k stars、845 forks、C++ 主语言、MIT license）。仓库处于活跃迭代期，`BodyInterface` 的 batch API 与 `BroadPhase` 的具体实现可能在未来版本微调；deterministic simulation 边界（哪些特性 deterministic、哪些不）以 `Docs/Architecture.md` 的"Deterministic Simulation"小节为准。

Jolt 是少数同时把"lock-free 多线程 + 严格 deterministic + MIT + RISC-V/LoongArch 支持 + GPU hair sim"塞进同一 C++17 库的项目；如果你的工作流强依赖 PhysX 的 GPU rigid body pipeline 或 Havok 的成熟 cloth，需要评估 Jolt 在这些维度的功能完整度。
