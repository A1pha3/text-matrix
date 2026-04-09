---
title: "Newton：Disney+Google+NVIDIA联手打造的GPU加速物理仿真引擎"
date: 2026-04-09T12:35:00+08:00
slug: "newton-gpu-accelerated-physics-simulation-guide"
description: "Newton是基于NVIDIA Warp的GPU加速物理仿真引擎，由Disney Research、Google DeepMind和NVIDIA联合开发，支持机器人仿真、柔体物理、软体物理等多物理场仿真，广泛应用于机器人学和仿真研究。"
draft: false
categories: ["技术笔记"]
tags: ["GPU加速", "物理仿真", "NVIDIA Warp", "机器人仿真", "Python", "CUDA", "Isaac Sim"]
---

# Newton：Disney+Google+NVIDIA联手打造的GPU加速物理仿真引擎

## §1 学习目标

通过本文，你将掌握：

- Newton的核心设计理念与技术架构
- NVIDIA Warp与MuJoCo Warp的继承关系
- 完整的仿真功能分类（12大类50+示例）
- GPU加速的底层原理与CUDA调度机制
- 机器人仿真完整工作流程（URDF导入、控制器、IK求解）
- 柔体与软体物理仿真（Cloth/Cable/Softbody）
- 多物理场耦合仿真（MPM + 刚体）
- 自定义扩展与二次开发方法
- 性能优化与最佳实践

## §2 背景与项目定位

### 2.1 物理仿真引擎生态

当前主流物理仿真引擎可分为三类：

| 类型 | 代表引擎 | 特点 | 适用场景 |
|------|----------|------|----------|
| **工业级** | Isaac Sim, MuJoCo | 高保真、物理精度 | 自动驾驶、工业机器人 |
| **研究级** | NVIDIA Warp, Newton | GPU加速、可微分化 | 机器人控制、RL训练 |
| **游戏引擎** | Unity, Unreal | 实时性、渲染 | 游戏、VR |

### 2.2 Newton的独特定位

**Newton是什么？**

> Newton is a GPU-accelerated physics simulation engine built upon NVIDIA Warp, specifically targeting roboticists and simulation researchers.

**三位一体发起方：**

| 发起方 | 贡献领域 |
|--------|----------|
| **Disney Research** | 仿真精度、创意应用 |
| **Google DeepMind** | 强化学习、策略优化 |
| **NVIDIA** | Warp核心、GPU加速 |

**核心设计哲学：**

1. **GPU-First**：所有计算在GPU上完成，充分利用并行计算优势
2. **可微分化**：支持JIT自动微分，天然适配强化学习
3. **OpenUSD支持**：与工业仿真数据格式无缝对接
4. **用户可扩展**：开放的Python API，支持自定义物理场

## §3 技术架构深度解析

### 3.1 与NVIDIA Warp的关系

Newton构建于NVIDIA Warp之上，继承了Warp的核心优势：

```
┌─────────────────────────────────────────────────────────────┐
│                        Newton                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │              MuJoCo Warp Backend                  │   │
│  │  ┌───────────────────────────────────────────┐ │   │
│  │  │            NVIDIA Warp                     │ │   │
│  │  │  ┌─────────────────────────────────────┐ │ │   │
│  │  │  │    CUDA Kernels (cuWarp)          │ │ │   │
│  │  │  └─────────────────────────────────────┘ │ │   │
│  │  └───────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Warp的核心特性（Newton继承）：**

| 特性 | 说明 | Newton支持 |
|------|------|-----------|
| GPU加速 | 所有物理计算在CUDA核心 | ✅ 全部 |
| 自动微分 | JIT编译下的梯度计算 | ✅ 全部 |
| MPM求解器 | Material Point Method | ✅ 扩展 |
| SDF距离场 | 符号距离函数 | ✅ 全部 |
| Warp Device Abstraction | 统一CPU/GPU接口 | ✅ 全部 |

### 3.2 系统需求

| 组件 | 要求 |
|------|------|
| **Python** | 3.10+ |
| **OS** | Linux (x86-64, aarch64), Windows (x86-64), macOS (CPU only) |
| **GPU** | NVIDIA GPU (Maxwell or newer) |
| **CUDA Driver** | 545+ (CUDA 12) |
| **本地CUDA Toolkit** | ❌ 不需要 |

**重要说明**：macOS仅支持CPU计算，无GPU加速。

## §4 功能分类详解

### 4.1 功能总览

Newton提供**12大类**仿真功能，覆盖机器人学主要场景：

| 类别 | 示例数量 | 核心场景 |
|------|----------|----------|
| Basic（基础） | 10+ | 入门级物理演示 |
| Robot（机器人） | 15+ | 足式机器人、机械臂 |
| Cable（电缆） | 5+ | 线缆操作、布线仿真 |
| Cloth（布料） | 10+ | 布料仿真、衣物操作 |
| Inverse Kinematics（IK） | 5+ | 运动学求解 |
| MPM | 10+ | 颗粒材料、耦合仿真 |
| Sensors（传感器） | 3+ | 感知仿真 |
| Selection（选择） | 5+ | 场景选择逻辑 |
| DiffSim（可微仿真） | 8+ | 可微分物理 |
| Multi-Physics（多物理场） | 2+ | 耦合仿真 |
| Contacts（接触） | 6+ | 精密装配 |
| Softbody（软体） | 2+ | 软体操作 |

### 4.2 基础功能（Basic）

基础示例是Newton的入门必读，包含10+示例：

| 示例 | 命令 | 说明 |
|------|------|------|
| Pendulum | `python -m newton.examples basic_pendulum` | 单摆系统 |
| URDF | `python -m newton.examples basic_urdf` | URDF模型导入 |
| Viewer | `python -m newton.examples basic_viewer` | 可视化窗口 |
| Shapes | `python -m newton.examples basic_shapes` | 基础几何体 |
| Joints | `python -m newton.examples basic_joints` | 关节系统 |
| Conveyor | `python -m newton.examples basic_conveyor` | 传送带 |
| Heightfield | `python -m newton.examples basic_heightfield` | 高度场地形 |
| Recording | `python -m newton.examples recording` | 仿真录制 |
| Replay Viewer | `python -m newton.examples replay_viewer` | 回放可视化 |
| Plotting | `python -m newton.examples basic_plotting` | 数据绘图 |

### 4.3 机器人仿真（Robot）

机器人仿真是Newton的核心应用场景：

#### 4.3.1 足式机器人

| 机器人 | 示例命令 | 说明 |
|--------|----------|------|
| **Cartpole** | `python -m newton.examples robot_cartpole` | 小车平衡杆 |
| **G1** | `python -m newton.examples robot_g1` | 宇树H1人形机器人 |
| **H1** | `python -m newton.examples robot_h1` | 华为盘古人形机器人 |

#### 4.3.2 四足机器人

| 机器人 | 示例命令 | 说明 |
|--------|----------|------|
| **Anymal D** | `python -m newton.examples robot_anymal_d` | ANYbotics四足D型 |
| **Anymal C Walk** | `python -m newton.examples robot_anymal_c_walk` | ANYbotics四足C型 |

#### 4.3.3 机械臂

| 机械臂 | 示例命令 | 说明 |
|--------|----------|------|
| **UR10** | `python -m newton.examples robot_ur10` | Universal Robots UR10 |
| **Panda + Hydro** | `python -m newton.examples robot_panda_hydro` | Franka Panda + Hydro |
| **Allegro Hand** | `python -m newton.examples robot_allegro_hand` | 灵巧手仿真 |

#### 4.3.4 控制器与策略

```bash
# 运行预训练策略
python -m newton.examples robot_policy
```

### 4.4 布料仿真（Cloth）

布料仿真是柔体物理的核心应用：

| 示例 | 命令 | 物理现象 |
|------|------|----------|
| Cloth Bending | `python -m newton.examples cloth_bending` | 布料弯曲 |
| Cloth Hanging | `python -m newton.examples cloth_hanging` | 悬挂布料 |
| Cloth Style3D | `python -m newton.examples cloth_style3d` | 3D款式设计 |
| Cloth H1 | `python -m newton.examples cloth_h1` | 人形机器人+布料 |
| Cloth Twist | `python -m newton.examples cloth_twist` | 布料扭转 |
| Cloth Franka | `python -m newton.examples cloth_franka` | 机械臂+布料 |
| Cloth Rollers | `python -m newton.examples cloth_rollers` | 辊压布料 |
| Cloth Poker Cards | `python -m newton.examples cloth_poker_cards` | 扑克牌+布料 |

### 4.5 电缆仿真（Cable）

电缆仿真用于线缆操作和布线分析：

| 示例 | 命令 | 场景 |
|------|------|------|
| Cable Twist | `python -m newton.examples cable_twist` | 电缆扭转 |
| Cable Y-Junction | `python -m newton.examples cable_y_junction` | Y型电缆分支 |
| Cable Bundle Hysteresis | `python -m newton.examples cable_bundle_hysteresis` | 电缆束滞后 |
| Cable Pile | `python -m newton.examples cable_pile` | 电缆堆叠 |

### 4.6 可微仿真（DiffSim）

DiffSim是Newton的特色功能，支持物理仿真过程的自动微分：

| 示例 | 命令 | 应用 |
|------|------|------|
| DiffSim Ball | `python -m newton.examples diffsim_ball` | 可微球体碰撞 |
| DiffSim Cloth | `python -m newton.examples diffsim_cloth` | 可微布料 |
| DiffSim Drone | `python -m newton.examples diffsim_drone` | 可微无人机控制 |
| DiffSim Spring Cage | `python -m newton.examples diffsim_spring_cage` | 可微弹簧笼 |
| DiffSim Soft Body | `python -m newton.examples diffsim_soft_body` | 可微软体 |
| DiffSim Quadruped | `python -m newton.examples diffsim_bear` | 可微四足 |

**DiffSim的核心价值**：

```python
# 传统仿真：前向计算
state = simulator.forward(params)

# DiffSim：前向 + 反向梯度
state, grad = simulator.forward_and_backward(params)
```

### 4.7 传感器仿真（Sensors）

| 示例 | 命令 | 传感器类型 |
|------|------|------------|
| Sensor Contact | `python -m newton.examples sensor_contact` | 接触力传感器 |
| Sensor Tiled Camera | `python -m newton.examples sensor_tiled_camera` | 相机感知 |
| Sensor IMU | `python -m newton.examples sensor_imu` | IMU惯性测量 |

## §5 快速开始

### 5.1 安装

```bash
# 安装Newton（包含示例）
pip install "newton[examples]"

# 验证安装
python -m newton.examples --help
```

### 5.2 运行第一个示例

```bash
# 运行基础单摆示例
python -m newton.examples basic_pendulum
```

### 5.3 查看所有示例

```bash
# 列出所有可用示例
python -m newton.examples
```

### 5.4 USD格式输出

```bash
# 运行并输出为USD文件
python -m newton.examples basic_viewer \
    --viewer usd \
    --output-path my_output.usd
```

## §6 命令行参数详解

### 6.1 全局参数

| 参数 | 说明 | 默认值 |
|------|------|---------|
| `--viewer` | 可视化类型 | `gl` |
| `--device` | 计算设备 | Warp默认设备 |
| `--num-frames` | 仿真帧数 | 100 |
| `--output-path` | USD输出路径 | - |

### 6.2 Viewer类型

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| `gl` | OpenGL实时窗口 | 交互调试 |
| `usd` | USD文件输出 | 离线渲染 |
| `rerun` | ReRun可视化 | 云端查看 |
| `null` | 无可视化 | 纯计算 |

### 6.3 Device选择

```bash
# 使用特定GPU
python -m newton.examples basic_pendulum --device cuda:0

# 使用CPU
python -m newton.examples basic_pendulum --device cpu
```

## §7 机器人仿真进阶

### 7.1 URDF模型导入

Newton支持直接导入URDF格式的机器人模型：

```bash
# 加载URDF模型
python -m newton.examples basic_urdf
```

**URDF支持的机器人模型**：

| 模型 | 类型 | 来源 |
|------|------|------|
| UR10 | 机械臂 | Universal Robots |
| Panda | 机械臂 | Franka |
| G1 | 人形机器人 | 宇树科技 |
| H1 | 人形机器人 | 华为 |
| Anymal D/C | 四足机器人 | ANYbotics |

### 7.2 逆运动学（IK）求解

Newton提供多种IK求解器：

```bash
# 基础IK示例
python -m newton.examples ik_franka    # Franka机械臂IK
python -m newton.examples ik_h1        # H1人形机器人IK
python -m newton.examples ik_custom    # 自定义IK

# 复杂IK任务
python -m newton.examples ik_cube_stacking  # 立方体堆叠IK
```

### 7.3 控制器与策略

```python
# 运行预训练策略
python -m newton.examples robot_policy

# 支持的策略类型：
# - locomotion (行走)
# - manipulation (操作)
# - tracking (跟踪)
```

## §8 物理场详解

### 8.1 刚体动力学

Newton的刚体求解器支持：

| 特性 | 说明 |
|------|------|
| 碰撞检测 | SDP + 连续碰撞检测 |
| 关节约束 | Revolute, Prismatic, Ball, Fixed |
| 外力 | 重力、接触力、电机力矩 |

### 8.2 柔体物理（Cloth/Cable）

| 求解器 | 方法 | 适用场景 |
|--------|------|----------|
| XPBD | Position Based Dynamics | 布料、电缆 |
| PBD | Projective Dynamics | 实时仿真 |
| MPM | Material Point Method | 颗粒材料 |

### 8.3 软体物理（Softbody/MPM）

```bash
# 软体仿真示例
python -m newton.examples softbody_hanging    # 悬挂软体
python -m newton.examples softbody_franka      # 机械臂+软体

# MPM示例
python -m newton.examples mpm_granular        # 颗粒材料
python -m newton.examples mpm_snow_ball       # 雪球破碎
```

## §9 多物理场耦合

### 9.1 耦合仿真示例

| 示例 | 命令 | 耦合类型 |
|------|------|----------|
| Softbody Gift | `python -m newton.examples softbody_gift` | 软体+刚体 |
| Dropping to Cloth | `python -m newton.examples softbody_dropping_to_cloth` | 软体+布料 |
| MPM Two-Way Coupling | `python -m newton.examples mpm_twoway_coupling` | MPM+刚体 |

### 9.2 耦合仿真原理

```python
# Newton的多物理场耦合通过统一的时间步长实现
for t in range(num_frames):
    # 1. 更新刚体状态
    rigid_body.step(dt)
    
    # 2. 更新柔体/软体状态
    soft_body.step(dt)
    
    # 3. 计算耦合接触力
    contact_forces = compute_coupling(rigid_body, soft_body)
    
    # 4. 应用耦合力
    rigid_body.apply(contact_forces)
    soft_body.apply(-contact_forces)
```

## §10 性能优化

### 10.1 GPU利用率

| 场景 | 建议GPU | 性能提升 |
|------|--------|----------|
| 实时仿真 | RTX 3080+ | 50-100x vs CPU |
| 高保真仿真 | A100 | 200x+ vs CPU |
| 批量仿真 | 多卡并行 | 线性扩展 |

### 10.2 仿真参数调优

| 参数 | 影响 | 建议 |
|------|------|------|
| `--num-frames` | 仿真精度 | 精度要求高时增加 |
| `--device` | 计算速度 | 优先使用GPU |
| 子步数 | 数值稳定性 | 复杂接触增加 |

### 10.3 最佳实践

```bash
# 推荐的工作流
# 1. CPU调试（快速迭代）
python -m newton.examples robot_g1 --device cpu --num-frames 50

# 2. GPU最终仿真（高精度）
python -m newton.examples robot_g1 --device cuda:0 --num-frames 500

# 3. USD输出用于可视化
python -m newton.examples robot_g1 \
    --viewer usd \
    --output-path gait.usd
```

## §11 与竞品对比

### 11.1 Newton vs MuJoCo

| 维度 | Newton | MuJoCo |
|------|--------|--------|
| **GPU加速** | ✅ 原生CUDA | ❌ CPU |
| **可微分化** | ✅ JIT自动微分 | ✅ JAX绑定 |
| **渲染集成** | ✅ OpenUSD原生 | ⚠️ 需额外配置 |
| **学习资源** | ⭐⭐⭐⭐⭐ 丰富示例 | ⭐⭐⭐⭐ 学术为主 |
| **机器人模型** | ⭐⭐⭐⭐ 主流支持 | ⭐⭐⭐⭐⭐ 全覆盖 |
| **许可** | Apache-2.0 | Apache-2.0 |

### 11.2 Newton vs Isaac Sim

| 维度 | Newton | Isaac Sim |
|------|--------|----------|
| **部署难度** | ⭐ 低（pip安装） | ⭐⭐⭐ 高（Omniverse依赖） |
| **Python优先** | ✅ 原生 | ⚠️ C++/Python混合 |
| **物理精度** | ⭐⭐⭐⭐ 高 | ⭐⭐⭐⭐⭐ 极高 |
| **实时仿真** | ⭐⭐⭐⭐ 佳 | ⭐⭐⭐⭐⭐ 极佳 |
| **成本** | 免费开源 | 需要Omniverse |

## §12 应用场景

### 12.1 机器人学

| 应用 | Newton优势 |
|------|-----------|
| **强化学习训练** | GPU加速 + 可微分化 |
| **运动控制** | 实时仿真 + IK求解器 |
| **灵巧操作** | 柔体/软体 + 多指手 |

### 12.2 自动驾驶

| 应用 | Newton优势 |
|------|-----------|
| **传感器仿真** | 相机/LiDAR物理 |
| **车辆动力学** | 高保真轮胎模型 |
| **场景生成** | OpenUSD导出 |

### 12.3 内容创作

| 应用 | Newton优势 |
|------|-----------|
| **电影特效** | 布料/柔体物理 |
| **游戏开发** | 实时物理 |
| **VR/AR** | 低延迟交互 |

## §13 总结

Newton是由Disney Research、Google DeepMind和NVIDIA三大科技巨头联手打造的新一代物理仿真引擎，它：

- ✅ **基于NVIDIA Warp**：继承CUDA加速、自动微分等核心能力
- ✅ **覆盖12大仿真领域**：刚体、柔体、软体、机器人、IK等
- ✅ **GPU加速**：50-100x性能提升
- ✅ **可微分化**：天然支持强化学习
- ✅ **OpenUSD原生**：与工业仿真无缝对接
- ✅ **开源Apache-2.0**：社区驱动，开放生态

**官方资源**：

- 官网：newton-physics.github.io
- GitHub：github.com/newton-physics/newton
- 文档：newton-physics.github.io/newton/latest
- 讨论：github.com/newton-physics/newton/discussions

---

🦞 文档版本：v1.0 | 写作日期：2026-04-09
