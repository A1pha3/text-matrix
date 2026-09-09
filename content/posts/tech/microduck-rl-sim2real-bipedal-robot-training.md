---
title: "Microduck RL：800 克双足机器人的完整 sim2real 训练配方"
date: 2026-09-08T03:50:00+08:00
slug: "microduck-rl-sim2real-bipedal-robot-training"
github_repo: "pollen-robotics/microduck_rl"
source_key: "gh:pollen-robotics/microduck_rl"
description: "Microduck RL 是 Pollen Robotics 为 800 克双足机器人 Microduck 开发的强化学习训练环境，基于 mjlab 与 PPO，涵盖 BAM 执行器物理、域随机化与齿隙仿真，策略经 ONNX 导出部署到真机，是开源界少见的完整 sim2real 配方。"
draft: false
categories: ["技术笔记"]
tags: ["机器人", "强化学习", "sim2real", "MuJoCo"]
---

# Microduck RL：800 克双足机器人的完整 sim2real 配方

面向做足式机器人控制的工程师与具身智能研究者：想知道一条"仿真里训出来、真机上跑起来"的流水线长什么样。前置知识：PPO 基本概念、MuJoCo 或同类物理仿真的使用经验、ONNX 的角色定位。

读完本文你能回答：这个仓库在整条 sim2real 链路里的位置；它的训练配方由哪几层构成；任务注册表里有哪些策略、部署时怎么热切换；以及复现它需要什么硬件预算。

## 一句话判断

这是开源界少见的"全配方"双足机器人 RL 仓库：环境代码之外，执行器物理（BAM）、域随机化（domain randomization）、齿隙仿真（backlash simulation），连同"哪些 reward 设计真正让策略 work"的提炼文档（AGENTS.md）一并开放。硬件门槛明确（CUDA GPU + uv），训练吞吐设计激进（MuJoCo Warp，4096 并行环境），产出的策略经 ONNX 导出后由姊妹仓库 microduck 的运行时部署到真机。对研究者，它是可复现的 sim2real 基线；对从业者，它是 reward 调试经验的公开样本。

## 系统地图：两个仓库，一条链路

```
microduck_rl（本仓库）                     microduck（姊妹仓库）
┌─────────────────────────┐              ┌──────────────────┐
│ mjlab (MuJoCo Warp) 仿真 │  ONNX 导出 →  │ 50Hz 真机运行时   │
│ PPO 训练 @ 4096 envs     │              │ 策略热切换        │
│ 域随机化 / BAM / 齿隙仿真 │              │ 61 维观测契约     │
└─────────────────────────┘              └──────────────────┘
```

关键设计是 **61 维共享观测契约（observation contract）**：48 维本体感觉（proprioception）加上命令槽 [twist(3)、head_pose(4)、body_pose(6)]，所有任务策略（行走、摔倒恢复、特技）吃同一种观测向量，真机运行时可以随时把控制权交给任意一个策略。不用的命令槽以零填充，而不是删除。这是"策略即技能模块"的架构选择，比单一巨型多任务策略更贴近工程可维护性。

机器人本体：约 800 克、约 25 厘米高的双足机器人 Microduck（Pollen Robotics），14 个舵机。

## 训练配方：四块叠加

README 把配方拆成四块，这个清单本身就是仓库的定位：

1. **BAM 执行器物理**：用 Rhoban 的 BAM M6 模型刻画 Dynamixel XL330 舵机——电压控制律、反电动势、Coulomb/Stribeck 与负载相关摩擦——而不是理想化扭矩源。在这个尺度（小舵机驱动约 800 克的双足），执行器保真度几乎占了 sim2real gap 的大头。
2. **域随机化**：对电池电压、负载压降、命令延迟、摩擦幅度逐环境（per-env）随机化，让策略对真机参数误差鲁棒。
3. **齿隙仿真**：每个舵机串联 ±1°（共 2°）齿轮间隙。真机编码器在齿隙输出侧，所以固件的 PD 模拟与关节观测都"透过"齿隙读取（qpos[servo] + qpos[backlash]）。观测与动作维度不变，ONNX 导出和运行时无需改动。
4. **reward 设计教训**：README 明说"让这套系统 work 的 reward 设计经验"提炼在 AGENTS.md，把调试智慧当作仓库资产公开，这在同类仓库里不常见。

训练栈：mjlab（MuJoCo Warp 后端，GPU 并行物理仿真）+ PPO，50Hz 控制频率，4096 并行环境下约 1-2 小时得到可用步态。没有本地 GPU 时可加 `--hf-jobs` 参数把训练发到 Hugging Face Jobs。

## 任务注册表与最小上手

`uv run list-envs` 打印实时任务注册表。README 列出的任务族（Flat/Rough 地形变体仅部分存在）：

| 任务族 | 内容 |
|---|---|
| Velocity | 主任务：速度指令 + 头部姿态指令的行走 |
| VelStand | 行走 + 摔倒恢复合入同一策略 |
| StandUp / SitStand | 起身（俯卧/仰卧/坐姿）、坐立切换 |
| GroundPick / BallKick | 俯身触地、踢球（actor 对球盲） |
| Roulade | 前滚翻 |
| Rollers / Swizzle / Spin | 轮滑系列：脚底被动轮滑行、倒八字、原地旋转 |

每个主任务还有 Backlash 孪生变体：在任务 id 的 MicroDuck 前插入 `-Backlash`，例如 `Mjlab-Velocity-Flat-Backlash-MicroDuck`。

任务间还按"摔倒是否便宜"选碰撞模型：Velocity 用剥掉躯干与头部接触的 `robot_walk.xml`（跌倒代价低），需要躺地或触地的 VelStand、StandUp、GroundPick 等改用精选碰撞集 `robot_groundcontact.xml`。同一个真机，每个任务在仿真里换一套碰撞几何。

把上面串成一条完整流转：

```bash
git clone https://github.com/pollen-robotics/microduck_rl
cd microduck_rl
# 训练行走策略：4096 环境，约 1-2 小时
uv run train Mjlab-Velocity-Flat-MicroDuck --env.scene.num-envs 4096
# 导出 ONNX——exporter 会把观测归一化器烘焙进图里
uv run scripts/export.py Mjlab-Velocity-Flat-MicroDuck --wandb-run-path <...>
# CPU MuJoCo 里用键盘驱动导出的策略，预演真机热切换
uv run scripts/infer_policy.py --walking output.onnx
# 发布到 Hugging Face Hub
uv run publish --onnx output.onnx --repo <user>/microduck-<name> --kind episodic --duration-s 4.0
```

`infer_policy.py` 支持 `--walking/--standing/--sitstand/--roulade` 多策略同时加载，正是真机运行时热切换机制的预演。发布前 `publish` 会校验导出图是 [1,61]→[1,14]（旧版 51 维策略会被拒绝）、输入合理、无 NaN 或恒定输出，仓库默认私有。episodic 表示策略运行 `--duration-s` 秒后自动回到站立姿态（适合踢球、滚翻这类一次性动作）。

两个部署细节值得记住：永远部署 `scripts/export.py` 产出的 ONNX，绝不用手工转换的 checkpoint——归一化器没烘焙进去，真机上的策略收到的是未归一化观测。ARM 机器（DGX Spark、Jetson）首次 `uv sync` 需设 `UV_HTTP_TIMEOUT=600`（约 2GB CUDA wheels）。

## 适用边界与采用建议

1. **想复现 sim2real 流水线的研究者**：这是完整度很高的参考实现，BAM + 域随机化 + 齿隙三层配方可直接对照学习。
2. **没有 Microduck 本体也有价值**：训练、导出、CPU 仿真预演全链路不需要真机；但"真机上 work"的结论只能由拥有本体的用户验证。
3. **硬件预算**：训练需 CUDA GPU（MuJoCo Warp 走 GPU 物理仿真），纯 CPU 路径只有推理预演。
4. **想迁移到自己的机器人**：61 维观测契约、任务注册表结构可以借鉴，但执行器模型与 reward 需要针对自己的硬件重调——AGENTS.md 的方法论比它的具体数值更有迁移价值。

本文不覆盖：reward 函数逐项解析（见仓库 AGENTS.md）、真机运行时细节（属姊妹仓库 microduck）、与 Isaac Lab 等仿真栈的对比（仓库未提供）。

## 仓库信息

- 仓库：https://github.com/pollen-robotics/microduck_rl （约 1.9k stars，Apache 2.0，Python）
- 姊妹仓库：https://github.com/pollen-robotics/microduck （真机运行时）
- 机器人主页：https://pollen-robotics.com/microduck （25 cm、800 g）
- 相关项目：mjlab（MuJoCo Warp + rsl_rl 训练框架）、Rhoban/BAM（执行器模型）
