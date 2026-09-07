---
title: "Microduck RL：800 克双足机器人的完整 sim2real 训练配方"
date: 2026-09-08T03:50:00+08:00
slug: "microduck-rl-sim2real-bipedal-robot-training"
github_repo: "pollen-robotics/microduck_rl"
source_key: "gh:pollen-robotics/microduck_rl"
description: "Microduck RL 是 Pollen Robotics 为 800 克双足机器人 Microduck 开发的强化学习训练环境，基于 mjlab 与 PPO，涵盖域随机化、BAM 执行器物理与 ONNX 导出部署，是开源界少见的完整 sim2real 配方。"
draft: false
categories: ["技术笔记"]
tags: ["机器人", "强化学习", "sim2real", "MuJoCo"]
---

# Microduck RL：800 克双足机器人的完整 sim2real 配方

面向做足式机器人控制的工程师与具身智能研究者：想知道一条"仿真里训出来、真机上跑起来"的流水线长什么样。前置知识：PPO 基本概念、MuJoCo 或同类物理仿真的使用经验、ONNX 的角色定位。

读完本文你能回答：这个仓库在整条 sim2real 链路里的位置；它的训练配方由哪几层构成；任务注册表里有哪些策略、部署时怎么热切换；以及复现它需要什么硬件预算。

## 一句话判断

这是一个**少见的"全配方开源"的双足机器人 RL 仓库**：不只是环境代码，而是把执行器物理建模（BAM）、域随机化（domain randomization）、齿隙仿真（backlash simulation）、以及"哪些 reward 设计教训让策略真正 work"的提炼文档（AGENTS.md）一并交出。硬件门槛明确（CUDA GPU + uv），训练吞吐设计激进（MuJoCo Warp，4096 并行环境），产出的策略经 ONNX 导出后由姊妹仓库 microduck 的运行时部署到真机。对研究者，它是可复现的 sim2real 基线；对从业者，它是reward 调试经验的公开样本。

## 系统地图：两个仓库，一条链路

```
microduck_rl（本仓库）                     microduck（姊妹仓库）
┌─────────────────────────┐              ┌──────────────────┐
│ mjlab (MuJoCo Warp) 仿真 │  ONNX 导出 →  │ 50Hz 真机运行时   │
│ PPO 训练 @ 4096 envs     │              │ 策略热切换        │
│ 域随机化 / BAM / 齿隙仿真 │              │ 61 维观测契约     │
└─────────────────────────┘              └──────────────────┘
```

关键设计是**61 维共享观测契约（observation contract）**：所有任务策略（行走、摔倒恢复、特技）吃同一种观测向量，真机运行时可以随时把控制权交给任意一个策略。这是"策略即技能模块"的架构选择，比单一巨型多任务策略更贴近工程可维护性。

机器人本体：约 800 克、约 25 厘米高的双足机器人 Microduck（Pollen Robotics）。

## 训练配方：三层叠加

README 明确列出配方组成，这个清单本身就是仓库的核心价值：

1. **BAM 执行器物理**：用 Rhoban 的 BAM 模型刻画执行器动力学，而不是理想化的扭矩源——小尺寸舵机的延迟与饱和是 sim2real gap 的主要来源之一。
2. **域随机化**：对物理参数做随机化训练，让策略对真机参数误差鲁棒。
3. **齿隙仿真**：显式模拟传动间隙（backlash），微型机器人的齿轮箱普遍存在。
4. **reward 设计教训**：README 明说"让这套系统 work 的 reward 设计经验"提炼在 AGENTS.md——把调试智慧当作一等公民资产开源，这在同类仓库里不常见。

训练栈：mjlab（MuJoCo Warp 后端，GPU 并行物理仿真）+ PPO，50Hz 控制频率训练，4096 并行环境下约 1-2 小时得到可用步态。没有本地 GPU 时可加 `--hf-jobs` 参数把训练发到 Hugging Face Jobs。

## 任务注册表与最小上手

`uv run list-envs` 打印实时任务注册表，每类任务都有 Flat/Rough 地形变体（部分）：

| 任务族 | 内容 |
|---|---|
| Velocity | 主任务：速度指令 + 头部姿态指令的行走 |
| VelStand | 行走 + 摔倒恢复合入同一策略 |
| StandUp / SitStand | 起身、坐立切换 |
| GroundPick / BallKick | 俯身触地、踢球（actor 对球盲） |
| Roulade | 前滚翻 |
| Rollers / Swizzle / Spin | 轮滑系列：脚底被动轮上的滑行、倒八字、原地旋转 |

最小上手路径（需 CUDA GPU 与 uv）：

```bash
git clone https://github.com/pollen-robotics/microduck_rl
cd microduck_rl
uv run train Mjlab-Velocity-Flat-MicroDuck --env.scene.num-envs 4096
# 训练完导出 ONNX
uv run scripts/export.py Mjlab-Velocity-Flat-MicroDuck --wandb-run-path <...>
# CPU MuJoCo 里用键盘驱动导出的策略，预演真机热切换
uv run scripts/infer_policy.py --walking output.onnx
```

`infer_policy.py` 支持 `--walking/--standing/--sitstand/--roulade` 多策略同时加载，正是真机运行时热切换机制的预演。ARM 机器（DGX Spark、Jetson）首次 `uv sync` 需设 `UV_HTTP_TIMEOUT=600`（约 2GB CUDA wheels）。

策略还可以发布分享：`uv run publish --onnx output.onnx --repo <user>/microduck-<name> --kind episodic --duration-s 4.0`。

## 适用边界与采用建议

1. **想复现 sim2real 流水线的研究者**：这是完整度很高的参考实现，BAM + 域随机化 + 齿隙三层配方可直接对照学习。
2. **没有 Microduck 本体也有价值**：训练、导出、CPU 仿真预演全链路不需要真机；但"真机上 work"的结论只能由拥有本体的用户验证。
3. **硬件预算**：训练需 CUDA GPU（MuJoCo Warp 走 GPU 物理仿真），纯 CPU 路径只有推理预演。
4. **想迁移到自己的机器人**：61 维观测契约、任务注册表结构可以借鉴，但执行器模型与 reward 需要针对自己的硬件重调——AGENTS.md 的方法论比它的具体数值更有迁移价值。

本文不覆盖：reward 函数逐项解析（见仓库 AGENTS.md）、真机运行时细节（属姊妹仓库 microduck）、与 Isaac Lab 等仿真栈的对比（仓库未提供）。

## 仓库信息

- 仓库：https://github.com/pollen-robotics/microduck_rl （1.9k stars，Apache 2.0，Python）
- 姊妹仓库：https://github.com/pollen-robotics/microduck （真机运行时）
- 机器人主页：https://pollen-robotics.com/microduck
