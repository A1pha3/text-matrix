---
title: "Newton 拆解：它统一的是 State 数组而不是物理算法，能力表里的空格就是定价"
date: "2026-04-09T12:35:00+08:00"
lastmod: "2026-09-20T00:00:00+08:00"
slug: "newton-gpu-accelerated-physics-simulation-guide"
github_repo: "newton-physics/newton"
source_key: "gh:newton-physics/newton"
description: "对着 newton-physics/newton 的 main 分支、docs/solvers 能力对比表与 114 个示例逐条核查后拆解它：Newton 统一的不是物理算法而是 Model/State/Control/Contacts 这套数组约定，八个求解器各自放弃了什么，可微分为何在能力表里只有两格写着 basic，仓库里唯一的性能口径 real_time_factor 为什么不能当加速比读，以及哪些仿真任务该直接换工具。"
draft: false
categories: ["技术笔记"]
tags: ["GPU加速", "物理仿真", "机器人", "CUDA", "开源项目解读"]
---

> **判断**：Newton 想解决的不是「再写一个更快的物理引擎」。它把机器人仿真里三件原本互相牵制的事拆开了——数据模型、积分算法、资产与观测格式——而缝合它们的只有一样东西：`Model`（模型）、`State`（状态）、`Control`（控制量）、`Contacts`（接触集合）这套数组约定。八个求解器共用同一个 `step(state_in, state_out, control, contacts, dt)` 签名，换求解器不用重建模，导一次 URDF 或 MJCF 就能在 XPBD、MuJoCo、Kamino 之间来回试。代价也全写在这里：能被这套约定表达的物理才有后端，表达不出来的字段就在官方能力表里留一个 ❌。那张表八行求解器、七列物理维度，空格不少——可微分只有两格写着 `basic`，`joint_velocity_limit` 一整行全空，equality constraints 只有 MuJoCo 支持。读懂 Newton 的标志不是能背出它有多少示例，而是能指出自己那件事落在哪一列。
>
> **读完后能做什么**：判断一次仿真任务的物理类型有没有 GPU 后端；说清 `--use-mujoco-contacts` 换掉的是哪一段接触计算；解释 `diffsim_*` 为什么清一色用 `SolverSemiImplicit`；把仓库里的 `real_time_factor` 读成「比实时快几倍」而不是「比 CPU 快几倍」；以及哪些场景应该直接用 MuJoCo、Isaac Lab 或者桌面级引擎。
>
> **依据**：[newton-physics/newton](https://github.com/newton-physics/newton) `main@4963486`（末次提交 2026-09-18，`pyproject.toml` 版本 `1.7.0.dev0`），最新 release `v1.6.0`（2026-09-10 发布，PyPI 同名包最新即 `1.6.0`，累计 34 个发行版本、仓库共 41 个 tag）。GitHub API（应用程序接口）在 2026-09-20 读到 5,655 stars / 687 forks / 106 位贡献者，仓库创建于 2025-04-22，代码 Apache-2.0、文档 CC-BY-4.0。定位与需求出自 `README.md`；分层与调用顺序出自 `docs/guide/overview.rst`、`docs/guide/installation.rst`；能力边界出自求解器指南 `docs/solvers/index.rst`（索引页）的三张对比表；命令与默认值按 `newton/examples/__init__.py` 逐条对照；示例统计来自 `newton/examples/` 目录本身；性能口径来自 `asv/`；版本策略出自 `docs/guide/compatibility.rst`、`docs/guide/release.rst` 与 `CHANGELOG.md`。

## 目录

- [§1 三条主线要分开看：数据模型、求解后端、资产与观测](#1-三条主线要分开看数据模型求解后端资产与观测)
- [§2 从 warp.sim 接手的是 API 约定，不是代码](#2-从-warpsim-接手的是-api-约定不是代码)
- [§3 一次仿真的真实调用顺序](#3-一次仿真的真实调用顺序)
- [§4 八个求解器，和一张必须逐格读的表](#4-八个求解器和一张必须逐格读的表)
- [§5 可微分支持到哪一层](#5-可微分支持到哪一层)
- [§6 多世界与耦合：experimental 集中在这两处](#6-多世界与耦合experimental-集中在这两处)
- [§7 114 个示例的真实分布与命令行](#7-114-个示例的真实分布与命令行)
- [§8 一次四足并行落地时会经过哪些对象](#8-一次四足并行落地时会经过哪些对象)
- [§9 仓库里唯一的性能口径不是加速比](#9-仓库里唯一的性能口径不是加速比)
- [§10 安装、extras 与硬件边界](#10-安装extras-与硬件边界)
- [§11 与 MuJoCo、Isaac Sim、PhysX 的分界](#11-与-mujocoisaac-simphysx-的分界)
- [§12 几类常见故障的排查顺序](#12-几类常见故障的排查顺序)
- [§13 谁该现在上，谁可以再等](#13-谁该现在上谁可以再等)
- [五道自测题](#五道自测题)
- [下一步读哪份代码](#下一步读哪份代码)
- [参考](#参考)

## §1 三条主线要分开看：数据模型、求解后端、资产与观测

README 里的定义只有一句：

> Newton is a GPU-accelerated physics simulation engine built upon NVIDIA Warp, specifically targeting roboticists and simulation researchers.

紧接着的第二段更关键。Newton 扩展并泛化了 Warp 里已经废弃的 `warp.sim` 模块，把 MuJoCo Warp 集成为主后端（primary backend），强调四点：GPU 计算、OpenUSD 支持、可微分、用户可扩展。第三段是治理结构。Newton 是一个 Linux Foundation（Linux 基金会）项目，由社区构建和维护，最初由 Disney Research、Google DeepMind 和 NVIDIA 三方发起。「三巨头联合开发」这个说法只覆盖了发起阶段。现在决定什么改动可以合并的是维护者，`docs/guide/compatibility.rst` 里那套 Experimental / Stable / Deprecated / Removed 四态标记才是真实的所有权表达。

`docs/guide/overview.rst` 列的对象可以按职责压成三层：

| 层 | 入口对象 | 负责什么 | 换掉它要付什么代价 |
|---|---|---|---|
| 数据模型 | `ModelBuilder` → `Model` → `State` / `Control` / `Contacts` | 只存几何、质量、关节坐标和力，不决定怎么积分 | 没有替代；所有后端都吃这一层 |
| 求解后端 | `newton.solvers.Solver*`（八个） | 决定坐标约定、接触算法、能不能给梯度 | 换后端要重看能力表，字段支持不一 |
| 资产与观测 | `add_urdf` / `add_mjcf` / `add_usd`、`CollisionPipeline`、`newton.sensors`、`newton.viewer` | 把外部模型搬进来，把状态搬出去 | 换可视化不改仿真语义 |

这三层里只有第二层是「物理算法」。第一层是 Newton 真正的公共契约：`State` 上 `body_q`（位置姿态）与 `body_qd`（速度）这些数组，加上 `joint_q` / `joint_qd` 的关节坐标布局，谁都得按它写。第三层与第二层之间还夹着一个可选环节：接触由 Newton 自己的 `CollisionPipeline` 算，还是交回 MuJoCo 的接触管线。这个开关会改变后面每一步的行为，§4 的脚注、§8 的示例代码和 §12 的排查都绕不开它。

`newton/_src/` 下的包结构与这三层对得上：`sim/` 是数据模型层，`solvers/` 是八个后端加一个 `coupled/`，其余 `geometry/`、`sensors/`、`viewer/`、`actuators/`、`controllers/`、`usd/`、`utils/` 分别管几何表示、传感器、可视化、执行器、控制器、USD 读写和工具函数。对外只有 `newton`、`newton.geometry`、`newton.solvers`、`newton.utils` 这些无下划线符号算公共 API，`newton._src.*` 是私有的，官方明确要求文档示例不许 import（`docs/guide/compatibility.rst`）。

## §2 从 warp.sim 接手的是 API 约定，不是代码

`warp.sim` 的结局在 FAQ 里写得很短：它是 NVIDIA 放在 Warp 里的模块，Warp 1.8 废弃，Warp 1.10 移除（`docs/faq.rst`）。Newton 是它的接班人，但 `docs/migration.rst` 通篇没在讲算法移植，讲的是改名和拆职责。这决定了从 Warp 老代码迁过来会踩到什么：

| `warp.sim` 时代 | Newton | 迁移的实际差别 |
|---|---|---|
| `FeatherstoneIntegrator` / `SemiImplicitIntegrator` / `XPBDIntegrator` / `VBDIntegrator` | `SolverFeatherstone` / `SolverSemiImplicit` / `SolverXPBD` / `SolverVBD` | integrator 升格为 solver，接触和执行器归进同一层 |
| `integrator.simulate(model, state0, state1, dt, None)` | `solver.step(state_in, state_out, control, contacts, dt)` | 参数顺序变了，`control` 和 `contacts` 变成显式入参 |
| `parse_urdf` / `parse_mjcf` / `parse_usd` | `ModelBuilder.add_urdf` / `add_mjcf` / `add_usd` | 解析结果直接写进调用方的 `ModelBuilder`，不再返回独立结构 |
| `model.collide(state)` | `pipeline.collide(state, contacts)` | 接触集合要自己持有；`Model.collide` / `Model.contacts` 在 1.4 已弃用 |
| `num_envs` | `world_count` | 术语统一到 world，`num_envs` 已废弃 |
| `UsdRenderer` / `OpenGLRenderer` | `ViewerUSD` / `ViewerGL` | 渲染器名字换成 viewer 系列 |

有几处是默认值变了、代码不报错但物理不对的，值得单独记：

- 默认 up axis 从 Y 改成 Z，`plane` / `capsule` / `cylinder` / `cone` 这四种几何体的默认朝向也跟着从 Y 变成 Z。`docs/migration.rst` 明说这一条，`robot_anymal_d` 里也显式写了 `ModelBuilder(up_axis=newton.Axis.Z)`。导入器另有 `up_axis` 参数，默认 +Z，且现在会旋转资产去贴合 `ModelBuilder` 的朝向（旧的 USD 导入是直接覆盖 `up_axis`）。
- `ModelBuilder.add_body(origin=..., m=...)` 换成 `add_body(xform=..., mass=...)`，`add_shape_*(pos=..., rot=...)` 换成 `add_shape_*(xform=...)`。
- 导入器的逐关节参数被移除，改在 `ModelBuilder.default_joint_cfg` 上设默认值；接触参数同理走 `ModelBuilder.default_shape_cfg`，而且要在加载资产之前设。
- `Model.ground` 移除，改为显式调 `add_ground_plane()`。
- `JointMode` 换成 `JointTargetMode`，`joint_act` 不再是目标数组。
- `linear_compliance` / `angular_compliance` 从 `add_joint` 挪到 `SolverXPBD` 的构造参数，并且不再支持逐关节设置。
- MJCF 的 `geom_density` 现在对所有 shape 类型都读，旧模型的等效密度会变（§12 末条有细节）。
- universal / compound 关节被 D6 取代。
- `joint_target_q` 的默认布局改成与 `joint_q` 对齐的坐标布局，旧的 DOF 布局通过 `newton.use_coord_layout_targets = False` 恢复，但已在 1.5 标弃用。这段话连同它的 `.. deprecated:: 1.5` 就写在该模块的文档字符串（docstring）里。

`docs/concepts/conventions.rst` 另有一条更容易咬人的约定：Newton 公开的 `spatial_vector` 数组用 (linear, angular) 顺序，而 Warp 原生是 (angular, linear)，`State.body_qd` 与 `State.body_f` 都在此列；`body_qd` 里线速度和角速度都存在世界坐标系下，线速度那三项是质心在世界系的速度。文档同时说明 Newton 在这件事上跟随的是多数物理引擎的惯例，也与 Isaac Lab 的做法一致。自己写的 Warp kernel 若要读这些数组，顺序反了不会报错，只会静默给出错误结果。

## §3 一次仿真的真实调用顺序

`docs/guide/installation.rst` 给的最小闭环，只依赖 `pip install newton` 装上的东西（也就是只有 Warp 这一个强制依赖）：

```python
import warp as wp
import newton

# Build a model
builder = newton.ModelBuilder()
body = builder.add_body(
    xform=wp.transform((0.0, 1.0, 0.0), wp.quat_identity()),
    mass=1.0,
)
builder.add_shape_sphere(body, radius=0.25)
builder.add_ground_plane()
model = builder.finalize()

# Create a solver and allocate state
solver = newton.solvers.SolverXPBD(model)
state_0 = model.state()
state_1 = model.state()
control = model.control()
collision_pipeline = newton.CollisionPipeline(model)
contacts = collision_pipeline.contacts()

newton.eval_fk(model, model.joint_q, model.joint_qd, state_0)

# Step the simulation
for step in range(120):
    state_0.clear_forces()
    collision_pipeline.collide(state_0, contacts)
    solver.step(state_0, state_1, control, contacts, 1.0 / 60.0)
    state_0, state_1 = state_1, state_0
```

`docs/guide/overview.rst` 把这段归纳成六步：`ModelBuilder` 建模或导入 → `finalize()` 出 `Model` → 建传感器与 `CollisionPipeline`，分配 `State` / `Control` / `Contacts` → `collide()` 填当前接触集 → `solver.step()` → 更新传感器、渲染或导出。

几个从签名里读得出来、但文档不点破的细节：

- 两个 `State` 不是风格选择。`SolverBase.step(state_in, state_out, control, contacts, dt)` 要求读一个写另一个，循环末尾交换引用，于是同一个 step 既可被 CUDA graph 捕获，也可被 `wp.Tape()` 记录——§5 的可微分正是走这条路。
- `eval_fk` 必须在第一次 `collide` 之前调用。`robot_anymal_d` 里那行注释写的是 "Evaluate forward kinematics for collision detection"：刚体位姿要从关节坐标推出来，否则碰撞阶段读到的是没初始化的 `body_q`。
- `clear_forces()` 每子步一次，紧跟在循环开头。力累加是外部写入的，不清就会跨步叠加。
- `control` 可以为 `None`。文档里那个可微分完整示例传的就是 `None`；`robot_anymal_d` 传 `model.control()` 分配的实例。
- `CollisionPipeline` 的构造参数比示例显示的多：`broad_phase` 取 `"nxn"` / `"sap"` / `"explicit"`（`newton.examples.create_collision_pipeline()` 的默认是 `explicit`），另有 `reduce_contacts`、`rigid_contact_max`、`max_triangle_pairs`、`soft_contact_max`、`requires_grad`。Newton 1.6 加了 `speculative_contact_gap_max`，配合 `collide(..., dt=...)` 做预测性接触。

相关签名（取自源码，不是文档转述）：`ModelBuilder.finalize(device=None, *, requires_grad=False, skip_all_validations=False, ...)`、`Model.state(requires_grad=None)`、`Model.control(requires_grad=None, clone_variables=True)`、`CollisionPipeline.collide(state, contacts, *, soft_contact_margin=None, soft_self_contact=False, dt=None)`。

## §4 八个求解器，和一张必须逐格读的表

`newton.solvers` 的 `__all__` 是九个类名加两个子模块：`SolverBase`、`SolverFeatherstone`、`SolverImplicitMPM`、`SolverKamino`、`SolverMuJoCo`、`SolverSemiImplicit`、`SolverStyle3D`、`SolverVBD`、`SolverXPBD`，外加 `style3d` 与 §6 会讲的 `experimental`。去掉基类正好八个后端。类名全部走 PEP 562 的惰性 `__getattr__` 解析，所以 `import newton` 不会把八个后端一起拖进来。

`docs/solvers/index.rst` 的主能力表横向是求解器名加七个维度。以下按表中每一行照抄（✅ 支持、🟨 部分、❌ 不支持）：

| 求解器 | 积分 | 刚体 | Articulation | 粒子 | 布料 | 软体 | 可微分 |
|---|---|---|---|---|---|---|---|
| `SolverFeatherstone` | 半隐式 | ✅ | ✅ 广义坐标 | ✅ | 🟨 无自碰撞 | ✅ | 🟨 basic¹ |
| `SolverImplicitMPM` | 隐式 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `SolverKamino` | 半隐式（Euler、Moreau-Jean） | ✅ 最大坐标 | ✅ 最大坐标 | ❌ | ❌ | ❌ | ❌ |
| `SolverMuJoCo` | 显式 / 半隐式 / 速度隐式 | ✅² | ✅ 广义坐标 | ❌ | ❌ | ❌ | ❌ |
| `SolverSemiImplicit` | 半隐式 | ✅ | ✅ 最大坐标 | ✅ | 🟨 无自碰撞 | ✅ | 🟨 basic¹ |
| `SolverStyle3D` | 隐式 | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| `SolverVBD` | 隐式 | ✅ | 🟨 limited joint support | ✅ | ✅ | ✅ | ❌ |
| `SolverXPBD` | 隐式 | ✅ | ✅ 最大坐标 | ✅ | 🟨 无自碰撞 | 🟨 experimental | ❌ |

表里两个上标是文档自带的脚注。¹ `basic` 表示 Newton 带了几个用该求解器跑 diffsim 工作流的示例，细节在 Differentiability 一节。² MuJoCo 默认使用它自己的接触管线，要用 Newton 的 `CollisionPipeline` 得设 `use_mujoco_contacts=False`。

文档在表格之前先给了选择顺序：刚体机器人先决定坐标表示，`SolverMuJoCo` 与 `SolverFeatherstone` 用广义坐标，`SolverXPBD`、`SolverSemiImplicit`、`SolverKamino` 用最大坐标；可变形、粒子、可微分再回到这张表筛。表格之后的话更准。真正在操作 articulation（广义或约化坐标下的运动树）的只有 Featherstone 和 MuJoCo 两个，三个最大坐标求解器把关节当作成对刚体之间的约束施加，不建运动树；VBD 只支持一部分关节类型；Style3D 与 ImplicitMPM 完全不支持关节。

同一个 `step()` 签名背后因此有两种不兼容的状态语义：换后端时 `joint_q` 的含义可能从「每关节一个坐标」变成「每刚体一个七维位姿」。这也是 §12 那个多求解器叠加示例存在的理由。

这张表还有两处提醒：

**它没有 GPU、多世界、接触质量这些列。** 表格只回答「这类物理有没有人实现」，不回答「实现得好不好」。GPU 与并行世界在别处（`docs/concepts/worlds.rst`、`asv/`），接触能力在紧跟着的第二张表里。想拿这张表论证「Newton 比谁强」是读错了表。

**两个求解器带着 public API 级别的警告。** `docs/solvers/index.rst` 在表格后紧跟两条 `.. experimental::`，分别说明 `SolverKamino` 与 `SolverVBD` 的公共 API 和行为"may change without prior notice"。`SolverVBD` 的 articulation 一栏直接写着关节支持有限。`docs/solvers/kamino.rst` 更直：Kamino 处于 BETA 1，"Newton users are discouraged from depending on it"，后端有 `"padmm"`（默认）和 `"dvi"` 两种，每世界的求解器终态通过 `SolverKamino.status` 暴露。它值得注意的地方是它只做一件事——最大坐标下的受约束多刚体，带运动闭环和硬摩擦接触——1.6 才补上库仑关节摩擦与力矩上限。

第二张表管接触材质字段，这是最容易选错后端的地方。这些字段存在 `ModelBuilder.ShapeConfig` 和 `Model` 的材质数组里，文档强调它们是 solver-neutral（求解器中立）的。写进模型只表示「有这么个物理量」；哪个后端读它由后端自己列，第三方求解器也可以只取其中一部分：

| 字段 | 实际使用它的求解器 |
|---|---|
| `mu`（摩擦系数） | 八个全有 |
| `ke` / `kd`（接触刚度阻尼） | Featherstone、SemiImplicit、MuJoCo、VBD |
| `kf` / `ka`（摩擦相关） | 只有 Featherstone、SemiImplicit；MuJoCo 只用 `kf` |
| `restitution`（恢复系数） | XPBD（需 `enable_restitution=True`）、Kamino |
| `mu_torsional` / `mu_rolling` | XPBD、MuJoCo |
| `kh`（hydroelastic） | Featherstone、SemiImplicit、MuJoCo，且必须 `use_mujoco_contacts=False` |

关节侧的空格更零散，而且三处关键缺失凑不出一个都有的后端。`PRISMATIC` / `REVOLUTE` / `BALL` / `FIXED` / `FREE` 参与对比的六个求解器全支持，`D6` 除 Kamino 外全支持，`ROD` 只有 VBD 支持。`DISTANCE` 一行的分布最容易被误读：只有 `SolverXPBD` 真正施加距离约束，Featherstone 与 SemiImplicit 是 🟨——脚注写明它们把 DISTANCE 当作 FREE 处理，也就是完全不拉；MuJoCo、VBD、Kamino 三列直接是 ❌。等式约束（`CONNECT` / `WELD` / `JOINT`）反过来只有 MuJoCo 支持。mimic joint 除 Kamino 外都有，实现机制各写各的：Featherstone 从约化动力学里消掉跟随自由度、把力和惯量转移到参考关节；SemiImplicit 用 `joint_mimic_ke` / `joint_mimic_kd` 配置的惩罚弹簧；XPBD 与 VBD 走耦合的最大坐标修正，每个求解器迭代应用一次；MuJoCo 把它降级成关节等式约束，多轴 D6 关系每个轴产生一条等式约束。

属性层面的缺口更细。`joint_enabled` 只有 SemiImplicit、XPBD、VBD 认；`joint_armature` 只有 Featherstone、MuJoCo、Kamino；`joint_friction` 与 `joint_effort_limit` 只有 MuJoCo、Kamino；`joint_limit_ke` / `joint_limit_kd` 这一行 XPBD 和 Kamino 都是 ❌；`joint_target_mode` 只有 MuJoCo 和 Kamino。`joint_limit_lower` / `joint_limit_upper` 六个全 ✅，但脚注补了一句 SemiImplicit 不约束 BALL 关节的限位；`joint_target_ke` / `joint_target_kd` 与 `Control.joint_f` 前馈六个全 ✅（VBD 那里有注：它把 `joint_target_kd` 和 `joint_limit_kd` 解释为物理单位下的绝对阻尼系数）。最反直觉的一行是 `joint_velocity_limit`：六个求解器全部 ❌。

于是刚体机器人这条线上有了一条硬约束：要等式约束就锁在 MuJoCo，而 MuJoCo 恰恰不支持 DISTANCE；要距离约束就得上 XPBD，它又拿不到等式约束和力矩上限。常见的处理办法是把缺的那条换成该后端认的表示，或者按 §6 的耦合求解器把一个模型拆开，交给两套物理分别承担。

## §5 可微分支持到哪一层

能力表「可微分」一列里，八个求解器只有 `SolverFeatherstone` 和 `SolverSemiImplicit` 不是 ❌，而且写的是 🟨 `basic`。这个 `basic` 是脚注定义过的：意思是 Newton 有几个示例在这些求解器上跑通了可微分工作流。它不等于「该求解器的全部物理都可微」。

主线的可微分流程在 `docs/solvers/index.rst` 的 Differentiability 一节里有完整代码。它的说法是：Newton 通常在 `wp.Tape()` 里跑前向 rollout，从仿真状态算一个标量 loss，再调 `tape.backward(loss)` 把梯度填到可微的状态、控制或模型数组上；起点是 `finalize(requires_grad=True)`。文档原样代码如下（一个粒子，损失是它到目标点的距离平方，反传后断言初速度梯度为负）：

```python
import warp as wp
import newton

@wp.kernel
def loss_kernel(particle_q: wp.array[wp.vec3], target: wp.vec3, loss: wp.array[float]):
    delta = particle_q[0] - target
    loss[0] = wp.dot(delta, delta)

builder = newton.ModelBuilder()
builder.add_particle(pos=wp.vec3(0.0, 0.0, 0.0), vel=wp.vec3(1.0, 0.0, 0.0), mass=1.0)

model = builder.finalize(requires_grad=True)
solver = newton.solvers.SolverSemiImplicit(model)

state_in = model.state(requires_grad=True)
state_out = model.state(requires_grad=True)
control = model.control()
loss = wp.zeros(1, dtype=float, requires_grad=True)
target = wp.vec3(0.25, 0.0, 0.0)

tape = wp.Tape()
with tape:
    state_in.clear_forces()
    solver.step(state_in, state_out, control, None, 1.0 / 60.0)
    wp.launch(
        loss_kernel,
        dim=1,
        inputs=[state_out.particle_q, target],
        outputs=[loss],
    )

tape.backward(loss)
initial_velocity_grad = state_in.particle_qd.grad.numpy()
assert float(initial_velocity_grad[0, 0]) < 0.0
```

三个地方值得停一下。`contacts` 传的是 `None`——这份代码里没有接触；`requires_grad=True` 要分别打在 `finalize()`、`state()` 和 loss 数组上，缺一个梯度就落不到实处；`tape.backward` 之后读的是 `state_in.particle_qd.grad`，也就是「改变初速度会让末态离目标更近还是更远」。整套机制复用 Warp 的自动微分，Newton 自己不实现反向传播。

接触梯度是另一回事。`docs/concepts/collisions.rst` 的写法很克制：narrow phase 在反向时被冻结（`enable_backward=False`），可微接触是**后处理阶段**在冻结的接触对上做一阶切平面近似，`eval_rigid_contact_kinematics()` 给出接触距离对 `body_q` 的一阶梯度。整节标 experimental，并附一句"may change without prior notice"。旧字段 `Contacts.rigid_contact_diff_*` 在 Newton 1.6 已弃用。

`newton/examples/diffsim/` 下 6 个示例（`diffsim_ball`、`diffsim_bear`、`diffsim_cloth`、`diffsim_drone`、`diffsim_soft_body`、`diffsim_spring_cage`）**全部**用 `SolverSemiImplicit` 构造求解器，与能力表恰好一致；`diffsim_bear` 还显式关掉三角接触（`enable_tri_contact=False`）。

这个示例做的事和名字给人的直觉完全不同：它加载 `newton/examples/assets/bear.usd` 里的网格，生成四面体软体，用 8 个随时间变化的相位喂给一层 tanh 全连接网络，网络输出当作四面体激活，再把质心动量当损失函数，用 `warp.optim` 训它走路。也就是说 Newton 在演示「可微软体能直接优化控制」，而不是在演示一个四足机器人。

## §6 多世界与耦合：experimental 集中在这两处

`world_count` 是 Newton 并行训练的地基，做法是在建模阶段复制模板：

```python
template = newton.ModelBuilder()
template.add_mjcf("humanoid.xml")

builder = newton.ModelBuilder()
builder.replicate(template, world_count=1024)
builder.add_ground_plane()
model = builder.finalize()

solver = newton.solvers.SolverMuJoCo(model)   # 一次 step 推进 1024 个世界
```

世界索引有个约定：`-1` 是全局（地面、共享地形），`0..N-1` 是具体世界；`begin_world` / `end_world`、`add_world`、`replicate` 管理这个划分（`docs/concepts/worlds.rst`）。**异构世界**——不同世界放不同机器人——文档仍标 experimental。`ModelBuilder.replicate` 到 1.6 才加上 `label_prefixes`，用来给每个世界的标签加前缀；`add_world` 和 `add_builder` 早就支持这个参数。

多物理场耦合走的是 `newton.solvers.experimental.coupled`，要从这个命名空间里直接导入，它不是 `newton.solvers` 上的平铺符号。文档对它的定义是：一次仿真步进被拆给多个求解器后端，而这些后端仍然通过同一个共享 `Model` 交换力、位姿和约束信息。五个公开名字各司其职——`SolverCoupled` 负责切分模型、分发状态、逐个推进并合并结果；`ModelView` 是共享模型上的视图内叠加层；`CouplingInterface` 是给需要自定义耦合行为的求解器实现的钩子协议；`SolverCoupledProxy` 是延迟或错拍的代理耦合；`SolverCoupledADMM` 是固定迭代次数的 ADMM 耦合，处理由模型推导出的关节、连接与接触。

文档给的适用场景是三类：MuJoCo 或 Kamino 的刚体机构耦合 VBD 布料、XPBD 粒子耦合 MPM 材料、刚体经 ADMM 约束连到粒子。`newton/examples/multiphysics/` 那 16 个示例就是这套框架目前的全部样本，其中 14 个确实 import 了 `SolverCoupled*`，剩下两个（`softbody_gift`、`vbd_dat_rigid_soft`）是纯 VBD 场景，不涉及耦合。可复现的组合比文档列举的更宽：`mujoco_vbd_admm_solver`、`mujoco_xpbd_coupled_solver`、`xpbd_mpm_coupled_solver`、`vbd_mpm_coupled_solver`、`kamino_mujoco_admm_solver`、`xpbd_vbd_coupled_solver`、`franka_cable_ik_pick_place`、`proxy_joint_gripper`。

`docs/concepts/` 里有三份调参文档（`simulation_tuning.rst` 加 MuJoCo 与 solvers 两份分册），说明这里有个不显眼的成本：同一套 `ke` / `kd` / `mu` 在不同后端上不是同一个物理量。

还有一处是属性申请制。默认情况下 `State` 上没有派生量；要用刚体加速度（IMU 需要）、执行器力矩这类扩展属性，得在 `finalize()` 之前调 `ModelBuilder.request_state_attributes("body_qdd")`。可选清单在 `State.EXTENDED_ATTRIBUTES`，当前是 `body_qdd`、`body_parent_f`、`mujoco.qfrc_actuator`（`docs/concepts/extended_attributes.rst`）。这条设计的直接后果：`solver.step()` 的签名不用为每个传感器扩张，代价是属性忘了申请时会拿到空数组。

## §7 114 个示例的真实分布与命令行

`newton/examples/__init__.py` 的 `get_examples()` 是唯一的事实来源：它遍历 `newton/examples/` 下每个**不以 `_` 开头的子目录**，收集文件名形如 `example_*.py` 的文件，去掉 `example_` 前缀和 `.py` 后缀作为示例名。名字是扫出来的，不是手维护的注册表。按这个规则逐目录数，`main@4963486` 上是 16 个目录、114 个示例：

| 目录 | 数量 | 覆盖的场景 |
|---|---|---|
| `basic` | 14 | 形状、关节、URDF、高度场、传送带、Dzhanibekov 效应、多求解器叠加、录制回放 |
| `multiphysics` | 16 | 耦合求解器与刚柔接触组合 |
| `vbd` | 14 | VBD 的布料、电缆、软体夹爪与接触变体 |
| `robot` | 11 | 关节机器人本体与预训练策略 |
| `mpm` | 9 | 颗粒材料、雪、粘滞、溃坝、双向耦合 |
| `cloth` | 8 | 布料弯曲、悬挂、扭转、Style3D 服装 |
| `contacts` | 8 | 堆叠、插头螺栓、多米诺、平衡鸟 |
| `cable` | 6 | 电缆扭转、Y 型分支、缆束滞后、超螺旋、绳索驱动十字滑台 |
| `diffsim` | 6 | 可微分 rollout 与优化 |
| `kamino` | 5 | 四连杆、异构机构、TestMech、DR Legs、Anymal D |
| `selection` | 4 | `ArticulationView` 批量读写 |
| `ik` | 4 | Franka、H1、自定义、立方体堆叠 |
| `sensors` | 3 | 接触力、IMU、分块渲染相机（tiled camera） |
| `controllers` | 3 | 微分 IK、关节阻抗、操作空间力位混合 |
| `softbody` | 2 | 软体悬挂与机械臂交互 |
| `mujoco` | 1 | MuJoCo Warp 的 sleeping islands |

几个目录名的读法：`vbd` 那 14 个是 `SolverVBD` 的接触回归测试。VBD 全称 Vertex Block Descent。`newton/_src/solvers/vbd/solver_vbd.py` 的类文档给了出处：粒子用 2024 年的 Vertex Block Descent，刚体用 2025 年的 Augmented VBD（AVBD），两篇都发在 ACM Transactions on Graphics。这些示例测的口子往往很窄。`vbd_gripper_soft_grid` 用一个 1×1 软网格，四个角撑在夹爪之外，横跨钳口中点的只剩那一条对角边；旧的逐粒子路径在这条缝里找不到任何顶点，只有打开 `enable_rigid_soft_full_surface_contact` 走水密 soft-EDGE 那一趟才夹得起来。文件注释直接给了对照结果：这个开关关掉，网格滑出、落地。`kamino` 5 个示例直接对应它自己的 BETA 状态。`mujoco` 只剩 1 个，因为 MuJoCo 主线示例散在 `robot/`、`contacts/` 和 `multiphysics/` 里。

命令行入口的行为按源码是这样的，几处容易想当然的地方一并标出：

```console
python -m newton.examples                    # 直接跑 basic_pendulum，不是列清单
python -m newton.examples --list             # 打印全部 114 个示例名
python -m newton.examples robot_anymal_d --world-count 16 --viewer gl
python -m newton.examples <name> --help      # 每个示例自己追加了哪些参数
```

`create_parser()` 给出的公共参数与默认值：`--device`（默认 `None`，即交给 Warp）、`--viewer`（默认 `gl`，可选 `gl` / `usd` / `rtx` / `rerun` / `null` / `viser`）、`--output-path`（默认 `output.usd`）、`--num-frames`（默认 `100`）、`--render-fps`、`--headless`、`--test`、`--quiet`、`--paused`、`--benchmark [SECONDS]`、`--warp-config KEY=VALUE`（可重复）、`--realtime`。

`--benchmark` 会把 viewer 强制切成 `null` 并提升进程优先级（`init()` 里 `_raise_benchmark_priority`），`--realtime` 再往上进到最激进的调度类。`--test` 会关掉交互式示例浏览器，改跑 `test_post_step` / `test_final`；一个示例若两者都没实现，`--test` 抛 `NotImplementedError`。可选追加的参数由各示例自己挂：`--broad-phase`（`nxn` / `sap` / `explicit`，默认 `explicit`）、`--world-count`（默认 `1`，`robot_anymal_d` 把它设成 `8`）、`--use-mujoco-contacts`（默认 `False`）、`--max-worlds`。

`newton.examples.init(parser)` 返回 `(viewer, args)`，`newton.examples.run(example, args)` 驱动 `while viewer.is_running()` 的帧循环。

## §8 一次四足并行落地时会经过哪些对象

`python -m newton.examples robot_anymal_d` 是最好的教学样本，因为它把上面三条主线在同一段代码里全用上了。以下逐段对照 `newton/examples/robot/example_robot_anymal_d.py`。

`__main__` 只做三件事：`Example.create_parser()`（在基础 parser 上追加 `--world-count` 与 `--use-mujoco-contacts`，并把 `world_count` 默认设成 8）、`newton.examples.init(parser)`、`newton.examples.run(...)`。

构造函数里的时间参数值得抄下来：`fps = 50` → `frame_dt = 1/50`，`sim_substeps = 4` → `sim_dt = 1/200`。也就是说一帧渲染对应四个物理子步。

建模分两段。先在模板 `ModelBuilder` 上配好物理常数：

```python
articulation_builder = newton.ModelBuilder(up_axis=newton.Axis.Z)
newton.solvers.SolverMuJoCo.register_custom_attributes(articulation_builder)
articulation_builder.default_joint_cfg = newton.ModelBuilder.JointDofConfig(
    limit_ke=1.0e3, limit_kd=1.0e1, friction=1e-5
)
articulation_builder.default_shape_cfg.ke = 2.0e3
articulation_builder.default_shape_cfg.kd = 1.0e2
articulation_builder.default_shape_cfg.kf = 1.0e3
articulation_builder.default_shape_cfg.mu = 0.75
```

`register_custom_attributes` 这一行是扩展属性机制在用：告诉 `ModelBuilder`「MuJoCo 后端会需要 `mujoco.qfrc_actuator`」。资产从 `newton.utils.download_asset("anybotics_anymal_d")` 拿到 USD，再 `add_usd(..., collapse_fixed_joints=False, enable_self_collisions=False, hide_collision_shapes=True)`。之后直接写 `joint_q[:3] = [0, 0, 0.68]`、`joint_q[3:7] = [0, 0, 0, 1]`（四元数），给每个 DOF 设 `joint_target_ke=150`、`joint_target_kd=5`、`joint_target_mode=POSITION`——PD 位置控制在建模阶段就把增益写死了。

世界用第二个 `ModelBuilder` 拼，把模板按世界数装进去：

```python
builder = newton.ModelBuilder(up_axis=newton.Axis.Z)
for _ in range(self.world_count):
    builder.add_world(articulation_builder)

builder.default_shape_cfg.ke = 1.0e3
builder.default_shape_cfg.kd = 1.0e2
builder.add_ground_plane()

self.model = builder.finalize()
```

`add_ground_plane()` 只调一次，地面是所有世界共享的。那两行 `default_shape_cfg` 不是重复代码：外层这个 `ModelBuilder` 的接触刚度是 `ke=1e3` / `kd=1e2`，模板里机器人自身形状用的是 `ke=2e3` / `kd=1e2`。同一份模型里因此并存两组接触参数，各自作用于被复制进世界的形状和之后追加的地面。

求解器构造时带了不少参数：`SolverMuJoCo(model, cone="elliptic", impratio=100, iterations=100, ls_iterations=50, nconmax=45, njmax=100, use_mujoco_contacts=...)`。

`simulate()` 是整段代码里信息量最大的八行：

```python
if not self.use_mujoco_contacts:
    self.collision_pipeline.collide(self.state_0, self.contacts)
for _ in range(self.sim_substeps):
    self.state_0.clear_forces()
    self.viewer.apply_forces(self.state_0)
    self.solver.step(self.state_0, self.state_1, self.control, self.contacts, self.sim_dt)
    self.state_0, self.state_1 = self.state_1, self.state_0
if self.use_mujoco_contacts:
    self.solver.update_contacts(self.contacts, self.state_0)
```

`collide` 在子步循环**外面**，一帧只算一次，四个子步复用同一份 `contacts`。这不是偷懒，是两种接触路径的分水岭：走 Newton 自己的管线时，几何没有大位移，重复检测的代价换不到精度；`--use-mujoco-contacts` 打开后顺序整个反过来，`CollisionPipeline` 根本不创建，`contacts` 由 `newton.Contacts(self.solver.get_max_contact_count(), 0)` 分配，接触在步进**之后**由 `solver.update_contacts()` 回填。同一个布尔值还决定 §4 里那行 `kh`（hydroelastic）能不能用。

`step()` 与 `simulate()` 分开是因为 CUDA graph：构造末尾调 `capture()`，如果设备是 CUDA 就在 `wp.ScopedCapture()` 里把 `simulate()` 录成图，之后每帧只是 `wp.capture_launch(self.graph)`。`--test` 下的两条检查（所有 body 的 `z > -0.006`；CUDA 上额外检查 `max(abs(qd)) < 0.25`）带着注释说明为什么阈值这么松：CPU 只跑 10 帧、CUDA 跑 500 帧，接触管线本身留有约 0.2 m/s 的残余速度。示例目录末尾的 `render()` 是 `begin_frame` → `log_state` → `log_contacts` → `end_frame`，与 viewer 的接口契约一致。

## §9 仓库里唯一的性能口径不是加速比

README、`docs/guide/overview.rst` 和 `docs/faq.rst` 里搜不到 faster、speedup、Nx 或 throughput 任何一个词，也没有跨引擎的吞吐量对照表。Newton 没有发布「相对 CPU 快多少倍」这类数字，任何以它名义给出的 50×、100×、200× 倍数，都不是仓库里查得到的结论。

仓库里真实存在的性能设施是 `asv/`（Airspeed Velocity 基准框架），配置在 `asv.conf.json`：`"branches": ["main"]`，`default_benchmark_timeout: 600`，安装命令把依赖钉死在 `warp-lang==1.17.0`、`mujoco==3.12.0`、`mujoco-warp==3.12.0`。它测的是 Newton 自己相对上一个提交的回归，不是一个跨引擎排行榜。

指标定义在 `asv/benchmarks/benchmark_metric_tracks.py`，单位写在代码里：

| track | 单位 | 含义 |
|---|---|---|
| `track_simulate` | `ms/world-step` | 单个世界一步的平均耗时 |
| `track_simulation_steps_per_second` | `world-steps/s` | 每秒完成多少个「世界 × 步」 |
| `track_real_time_factor` | `x` | 实时因子 |
| `track_p95_step_time` | `ms/frame` | 帧时间 95 分位 |
| `track_steady_state_gpu_memory` | `MiB` | 稳态显存 |

`real_time_factor` 的计算式在 `asv/benchmarks/benchmark_metrics.py`：`world_steps * sim_dt / experience_total_time`。分子是模拟时间、分母是墙钟时间，所以 `x = 1` 的含义是「以实时速度推进一个世界」，`x = 100` 是快实时 100 倍——它衡量的是仿真相对实时的快慢，与「比 CPU 快多少」「比 MuJoCo 快多少」没有关系。三个问题用它回答不了：换一张 GPU 数字怎么变（基准固定在 `g7e.2xlarge`，多 GPU 测试才用 `g7e.12xlarge`，即 4× L40S）；世界数放大后的扩展性（大部分 track 带 `world_count` 参数，必须按参数读）；以及能不能拿它评价 `SolverKamino`（`asv/benchmarks/simulation/bench_kamino.py` 存在，但 BETA 状态说明结论不稳）。

绝大多数 GPU track 上挂着 `@skip_benchmark_if(wp.get_cuda_device_count() == 0)`：没有 NVIDIA GPU 时静默跳过，不是「跑了但很慢」，所以 CI 全绿不等于这些数字存在。

`asv/pr_benchmarks.txt` 定义了 PR 阶段跑哪些：`Fast(?!SensorTiledCamera)\w*\.time_`、`Fast\w*\.track_simulate`、`Fast(?!TeleopMuJoCo)\w*\.track_mean_\w*(time|ms)`、`Fast\w*\.track_p95_\w*(time|ms)` 等六条正则，前缀 `Fast` 是筛掉慢基准的约定，负向断言用来把相机和遥操作这两类抖动大的单独管。想读具体场景就点进 `asv/benchmarks/simulation/`，那 16 个场景文件各自对应一件事：`bench_anymal`、`bench_mujoco`、`bench_quadruped_xpbd`、`bench_cloth`、`bench_cable`、`bench_contacts`、`bench_heightfield`、`bench_implicit_mpm`、`bench_kamino`、`bench_ik`、`bench_inverse_dynamics`、`bench_selection`、`bench_sensor_tiled_camera`、`bench_teleop_mujoco`、`bench_viewer`、`bench_cpu`。`newton/examples/` 里的 `test_final` 才是功能正确性关口。

## §10 安装、extras 与硬件边界

强制依赖只有 NVIDIA Warp 一个（`docs/guide/installation.rst`）。基础包 `pip install newton` 之后就能建模、建求解器、跑 §3 那个小球。示例与后端靠 extras 拉进来：

| extra | 用途 |
|---|---|
| `sim` | MuJoCo 仿真依赖（`mujoco-warp~=3.12.0` + `mujoco~=3.12.0`） |
| `importers` | HTTP 下载与网格处理（`requests`、`scipy`、`trimesh`、`coacd`、`fast-simplification`、`alphashape`、`meshio`、`pycollada`），支撑 `ModelBuilder.approximate_meshes` |
| `remesh` | `pyfqmr` 加 Open3D，给 `newton.utils.remesh_mesh` 用；Open3D 那一条带了标记条件，Python 3.13 与 Linux aarch64 上不会装 |
| `onnx` | `warp-nn[onnx]==0.3.1`，神经执行器与 RL 策略推理，不需要 PyTorch |
| `examples` | `sim` + `importers` + `onnx`，再加 `pyglet`（OpenGL 窗口）、`GitPython`（`download_asset()` 拉资产）、`imgui_bundle`（viewer 侧边栏）、`cbor2`（`.bin` 录制格式）。跑示例就装这个 |
| `torch-cu12` / `torch-cu13` | CUDA 12.8+ / 13 的 PyTorch 组合，各自带 examples |
| `notebook` | Jupyter + Rerun，带 examples |
| `rtx` | OVVRTX 实时光追 viewer（写在 `pyproject.toml`，但没进 installation.rst 的 extras 表，只在 `docs/guide/visualization.rst` 以 `uv sync --extra rtx` 出现） |
| `dev` / `docs` | 开发与文档构建 |

硬件边界的完整表述是：Python 3.10 以上（文档推荐 3.11+）；Linux x86-64 与 aarch64、Windows x86-64、macOS 只有 CPU；GPU 要求算力 5.0 起（Maxwell 及之后），驱动 545+（CUDA 12）或 550+（CUDA 12.4），CUDA 12 与 13 都支持，**不需要本地 CUDA Toolkit**。

三条容易在选型时才撞到的：

- 支持矩阵里的「经过测试的 GPU」只有 Ada Lovelace 和 Blackwell。Maxwell 是最低门槛，不是被验证过的档位；CI（持续集成）跑在 AWS 的 `g7e.2xlarge` 上。
- ARM64 Linux 上装 `importers` 需要 GLIBC 2.35+，RHEL 9 的 2.34 不行。Jetson Thor 与 DGX Spark 装 `examples` 需要 X11 开发库。
- CUDA graph 需要 CUDA 12.3 起，12.4 才是推荐档位。§8 里那个 `capture()` 在无 CUDA 设备上会走 `simulate()` 直调分支。

版本策略是 `major.minor.patch`，预发布形如 `1.1.0.dev0`（main 分支源码里的版本）与 `1.1.0rcN`。`docs/guide/compatibility.rst` 说 RC「通常不发到 PyPI」，但 PyPI 上 `newton` 的实际发行记录里躺着 `1.5.0rc1`、`1.5.0rc2`、`1.5.1rc1` 和 `1.6.0rc1`——政策与执行有出入，别拿这句话当排查依据。弃用组件至少保留一个完整 minor 周期（1.2.0 弃用 → 1.3.0 或更晚移除），破坏性变更只出现在 minor。micro 版本只给最新 minor 线，默认不向后移植。从 `CHANGELOG.md` 看发布节奏相当稳定：1.3.0（2026-06-11）、1.4.0（2026-07-16）、1.5.0（2026-08-11）、1.5.1（08-27）、1.5.2（09-09）、1.6.0（09-10）。

## §11 与 MuJoCo、Isaac Sim、PhysX 的分界

FAQ 给的答案比通常的竞品表老实。

和 MuJoCo 的关系是复用而非对抗。Newton 把 MuJoCo Warp 作为关键求解器，后者是 Google DeepMind 与 NVIDIA 用 Warp 重写的 MuJoCo，为的是把它搬上 GPU。FAQ 明确写着 "compatible with MuJoCo at both asset and solver levels"，资产与求解语义两侧都兼容。`SolverMuJoCo` 就是 mujoco_warp 的 Newton 接口封装（`docs/solvers/mujoco.rst`）。因此「Newton 还是 MuJoCo」这个问题在刚体机器人这条线上问得不成立，真正要选的是 §4 那张表里 `SolverMuJoCo` 那一行的四个 ❌——粒子、布料、软体、可微分它都不做。

PhysX 那条是直接否认："Will Newton replace PhysX? No."，理由是目标不同：Newton 面向机器人学习与可扩展多物理、强调可微分，PhysX 面向工业数字孪生仿真；Isaac Lab 的 Newton 集成不支持 PhysX，PhysX 也接不进 Newton。

Isaac Lab 与 Isaac Sim 是下游，不是同级。FAQ 里 Isaac Lab 的 Newton 集成标着 experimental、"under active development"，Isaac Sim 作为物理后端仍在开发。`docs/integrations/` 这一节已被整段拆走：求解器比较挪到 `/solvers/index`，后端细节挪到 `/solvers/mujoco`，下游项目挪到 `/lab/isaac-lab`。留存的正式集成页只剩 Isaac Lab 一篇，内容是一句指向 Isaac Lab 官方文档的跳转。除它之外，文档里没有「官方集成清单」这个东西。

一个能说明定位的细节来自 `robot_policy`。它加载的是在 Isaac Lab 里预训练好的 RL 策略，以 ONNX 形式经 Warp-NN 运行时推理，文件头注释专门写了一句 "PyTorch is not required for policy inference"。可选机器人是 `--robot g1_29dof` / `g1_23dof` / `go2`，键盘 `p` 复位、`i j k l u o` 移动。这条链路的分工因此很清楚：Isaac Lab 负责训练，Newton 负责训练之后那一段仿真验证。两个引擎在这里不是替代关系。

## §12 几类常见故障的排查顺序

**装完就跑不起来。** 先看 `import newton` 之后 `wp.get_cuda_device_count()` 是不是 0。macOS 上它必然是 0，此时 §8 的 `capture()` 不走 CUDA graph 分支，基准里的 GPU track 也全部被跳过。真在 NVIDIA 卡上跑不起来，先核对驱动是否到 545（CUDA 12）或 550（CUDA 12.4），再确认没去装本地 CUDA Toolkit——Warp 自带运行时，两套并存反而容易冲突。

**要用 `SolverMuJoCo` 的示例装完仍跑不通。** 基础包 `pip install newton` 只带 Warp，不含 `mujoco` 与 `mujoco-warp`。`docs/guide/installation.rst` 在多世界那段代码前专门插了一句提示：这段用 `SolverMuJoCo`，先装 `pip install "newton[sim]"`。

**`Unknown example 'xxx'`。** `main()` 会顺带打印全部示例名。示例名是从文件名派生的：`example_robot_anymal_d.py` → `robot_anymal_d`，带目录前缀，不带 `example_`。

**`--test` 抛 `NotImplementedError`。** 说明这个示例没有 `test_final` 也没有 `test_post_step`，只能人眼看。

**`--output-path is required when using usd viewer`。** 公共 `--output-path` 的默认值已经是 `output.usd`，所以这条异常实际只在示例自己重建了该参数且不给默认值时才抛得出来。

**`test_final` 失败，报 "all bodies are above the ground"。** 最常见是接触刚度没配。`robot_anymal_d` 那组常数就是为此存在的：`limit_ke=1e3` / `limit_kd=1e1` / `ke=2e3` / `kd=1e2` / `mu=0.75`；`SolverMuJoCo` 还要配 `iterations=100`、`ls_iterations=50`、`nconmax=45`、`njmax=100`。

**关节行为不对。** 先回 §4 的属性表，别怀疑积分器。速度上限六个求解器全是 ❌，只能靠 MuJoCo 与 Kamino 的 `joint_effort_limit` 在执行器侧绕；`DISTANCE` 在 Featherstone 与 SemiImplicit 里等同没有；`joint_limit_ke` / `joint_limit_kd` 在 XPBD 和 Kamino 上不起作用。

**模型建出来方向歪。** 默认 up axis 是 Z，从 `warp.sim` 迁移的 Y 轴代码需要显式指定。

**换求解器后画面或行为变了。** 这不算故障，而且仓库里有个专门演示它的示例。`basic_multi_solver_overlay` 用 XPBD、Featherstone、MuJoCo Warp 三种后端跑同一个四级摆，在同一窗口分层叠加。它的注释说得很直白：默认让三层完全重合，就是为了让各求解器的发散程度显眼；把 `spacing` 常数调大就能沿世界 X 轴并排摆开，侧边栏的 Layers 组可以逐层开关。想比对不同后端时直接用它，这个差异是 §4 那张表的物理后果，不是 bug。

**资产里的密度算出的质量不对。** 这是 `warp.sim` 与 Newton 的一处真实行为差异：旧导入器只对 sphere 和 box 读 MJCF 里的 `geom_density`，其它 shape 用 `parse_mjcf` 传入的统一 `density`；Newton 的导入器对所有 shape 类型都读 `geom_density`。`docs/migration.rst` 直接写明这会改变仿真结果，需要重调接触等参数才能对齐旧行为。

## §13 谁该现在上，谁可以再等

下面五件事里，只要有一件是硬需求，Newton 就是目前唯一把它们放进同一个模型的开源选项：

- 可微分 rollout（`wp.Tape` 配 `SolverSemiImplicit`，§5）；
- 布料、电缆、软体与刚体在同一个世界里相互作用（`experimental.coupled`，§6）；
- 上千个同构世界一次步进（`ModelBuilder.replicate`，§6）；
- 现成 MJCF 资产不改直接用，同时还能换接触管线（§11）；
- 同一个模型在 Python 里换后端做交叉验证（§12 的叠加示例）。

可以再等的三种情况。只要刚体机器人加 RL，`mujoco_warp` 或 Isaac Lab 的现成路径更短，Newton 主要多提供一层对象模型。需要速度上限、等式约束、距离约束里任意两样同时到位的精确装配，§4 已经说明没有一个后端能一次给全，先想清楚能放弃哪条。需要开箱渲染质量和角色动画的影视或游戏管线，那是 PhysX 与 Omniverse 一侧的目标，FAQ 里 Newton 自己不争。

上手顺序建议这样走，每步都能验证：

1. `pip install "newton[examples]"`，跑 `python -m newton.examples --list` 确认扫到 114 个示例，再跑 `basic_pendulum`。
2. 跑 `robot_anymal_d`，先 `--viewer null --num-frames 10` 确认无窗口可跑通，再开 `--viewer gl`。
3. 加 `--world-count` 到 GPU 显存吃满，用 `--test` 断言收敛，把 §9 的 `real_time_factor` 记下来。
4. 换成 `--use-mujoco-contacts`，比较接触表现差异，读 §4 的接触字段表。
5. 用 §3 的最小循环替换一个自己的模型，只在 `SolverSemiImplicit` 与 `SolverXPBD` 之间换后端。
6. 最后才尝试 `experimental.coupled`，先照抄 `multiphysics/` 里已有的示例。

## 五道自测题

1. 同一份 URDF 导入的机械臂，`SolverXPBD` 下工作正常，换 `SolverSemiImplicit` 后某个距离关节形同虚设。为什么？（§4：`DISTANCE` 在 Featherstone / SemiImplicit 里被当作 FREE，不施加拉压约束。）
2. 论文里写「用 Newton 做了可微分的接触梯度优化」，梯度能反到接触刚度上吗？（§5：narrow phase 反向时冻结，只有后处理的一阶切平面近似，`eval_rigid_contact_kinematics()` 给的是接触距离对 `body_q` 的梯度，整块 experimental。）
3. `robot_anymal_d` 的 `simulate()` 里 `collide()` 为什么在子步循环外面？如果机器人一帧内位移很大，这有什么问题？（§8：一帧只算一次接触、四个子步复用；预测性接触要靠 `CollisionPipeline(speculative_contact_gap_max=...)` 加 `collide(..., dt=...)`。）
4. `track_real_time_factor` 报 800x，能说「仿真比 CPU 快 800 倍」吗？（§9：它是模拟时间除以墙钟时间，`1x` 即实时速度，跟 CPU 基线无关。）
5. 想在同一个世界里既跑 MuJoCo 的机器人又跑布料，需要改哪些对象？（§6：`newton.solvers.experimental.coupled` 的 `SolverCoupledADMM` / `SolverCoupledProxy`，参照 `multiphysics/` 下的示例。）

## 下一步读哪份代码

- `newton/examples/__init__.py` 的 `get_examples()`、`create_parser()`、`init()`、`run()` 四个函数，90 + 80 + 86 + 15 共约 270 行，是示例命令行的全部真相。
- `docs/solvers/index.rst` 的三张表，选后端前唯一需要通读的东西。
- `docs/concepts/collisions.rst` 后半节讲可微接触的部分，比 `diffsim` 示例本身更能说明限制在哪。
- `asv/benchmarks/benchmark_metrics.py`，160 行，`real_time_factor` 的算式就在里面，读完不会再把它当加速比引。
- `docs/guide/compatibility.rst` 与 `CHANGELOG.md`，判断该跟哪条版本线。

## 参考

- Newton 仓库与示例源码：[newton-physics/newton](https://github.com/newton-physics/newton)（`main@4963486`）
- 官方文档与安装/兼容指南：[newton-physics.github.io/newton/stable](https://newton-physics.github.io/newton/stable/)
- MuJoCo Warp（Newton 的刚体主后端）：[google-deepmind/mujoco_warp](https://github.com/google-deepmind/mujoco_warp)
- NVIDIA Warp（GPU 计算与自动微分内核）：[NVIDIA/warp](https://github.com/NVIDIA/warp)，`warp.sim` 废弃说明见 [NVIDIA/warp discussion #735](https://github.com/NVIDIA/warp/discussions/735)
- `warp.sim` 迁移对照：`docs/migration.rst`
- 示例清单：`newton/examples/`，共 16 个目录 / 114 个示例
- 基准与 CI 机型：`asv.conf.json`、`.github/workflows/aws_gpu_benchmarks.yml`、`docs/guide/release.rst`
