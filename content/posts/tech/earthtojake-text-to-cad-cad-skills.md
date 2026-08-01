---
title: "text-to-cad：把 CAD 与机器人描述喂给代理的技能库"
date: 2026-08-02T02:59:48+08:00
slug: "earthtojake-text-to-cad-cad-skills"
description: "earthtojake/text-to-cad 是一个面向代理的 CAD 与机器人描述技能库，覆盖 STEP/STL/3MF 网格生成、URDF/SDF/SRDF 机器人描述、Slicer 切片、零件采购等环节，可被 Claude Code/Codex 等代理按需加载。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "CAD", "URDF", "SDF", "机器人", "3D 打印"]
---

## 一句话判断

`earthtojake/text-to-cad` 是一个把"CAD/机器人描述/3D 打印切片"这条工程链路拆成可独立加载技能的集合：每个技能对应一个具体工件格式（STEP/STL/3MF/URDF/SDF/SRDF），代理按"我现在想做什么"的需求去取，而不是被喂一整个庞大的 CLI。

## 项目定位

仓库描述直接点题：

> A skills library for CAD, robotics, and hardware design agents.

它的产品形态是一组 SKILL 文件 + Python 工具脚本（`skills/cad/requirements.txt` 写着 Python 3.11+），围绕"AI 代理如何与工程世界交换几何"这条线展开：

- **CAD 端**：生成 STEP/STL/3MF 网格；从本地工程文件反查几何
- **机器人端**：URDF 装配、SDF 仿真、SRDF（MoveIt2）配置
- **加工端**：切片（Slicer）准备、采购清单生成
- **检视端**：几何检查、属性查询、可打印性判断

每条技能在 README 的徽章列里被显式标出（STEP-Export、STL-Export、3MF-Export、URDF-Robots、SDF-Simulation、SRDF-MoveIt2）。

## 安装与运行

```bash
# 通过 skills 协议
npx skills@latest add earthtojake/text-to-cad

# 或按子技能加载
npx skills add earthtojake/text-to-cad --skill cad
npx skills add earthtojake/text-to-cad --skill urdf
```

要求：Python 3.11+、可访问 Discord（社区支持入口）、可访问文档站 [cadskills.xyz](https://www.cadskills.xyz)。

## 一次端到端任务流：从一句自然语言到可打印工件

把"我想做一个能装 ESP32 的桌面音箱外壳"当成任务样本：

1. **意图捕获**（代理）：用户说"做一个桌面音箱外壳，装 ESP32、留 USB-C 开口"
2. **激活 `cad` 技能**：代理调用 SKILL.md 给出的命令，先生成参数化 STEP
3. **几何检视**：代理调出 STEP viewer，确认 USB-C 开口位置、ESP32 安装孔位
4. **导出 3MF**：调 `cad` 技能里的 `mesh-export` 子流程，输出带颜色的 3MF
5. **激活 `slicer` 技能**：自动切片并估算打印时间与耗材
6. **激活 `sourcing` 技能**：列出 BOM（磁铁×4、M3 螺丝×6、热熔嵌件×4）

如果换成传统方式，这个任务至少要在 FreeCAD/CADQuery 里手写 200+ 行 Python，再加上人工切片和手工 BOM。

## 与同类项目的差异

| 项目 | 偏向 | 技能颗粒度 |
|------|------|-----------|
| `NomaDamas/k-skill` | 韩国本地生活公共服务 | 一项服务 = 一个 skill |
| `emilkowalski/skills` | 设计师 UI/动画品味 | 一条原则 = 一个 skill |
| `virgiliojr94/book-to-skill` | 把书籍/文档变成 skill | 一个文件 = 一个 skill |
| `earthtojake/text-to-cad` | CAD/机器人工程链路 | 一种工件格式 = 一个 skill |

这条路线最大的好处是：工程链路本身有清晰的工序边界（设计 → 网格 → 切片 → 采购），按工序切技能既符合工程师心智，也方便代理按"我现在在哪一步"做局部激活。

## 适用边界与不适用边界

**适用**：

- 已经在做硬件/机器人原型，每周要迭代 5+ 个零件几何的人
- 团队希望把"几何知识 + 工艺参数"沉淀成可被代理调用的资产，而不是写在 wiki 里吃灰
- 教学场景：让学生用自然语言探索 CAD，而不是先学一整套 GUI

**不适用**：

- 高端曲面 / 五轴加工 / 钣金展开（仓库定位在入门到中级原型）
- 大型 PLM / PDM 流程集成（这一层需要企业级 CAD 系统，不是 skill 能覆盖的）
- 完全离线的工控场景（依赖网络检索参数，部分 skill 会调在线服务）

## 工程链路上值得记住的几件事

1. **STEP 是中性格式首选** —— 不要一上来就丢 STL，SKILL.md 里 STEP 走在 STL/3MF 前面是有道理的
2. **URDF 严格只描述运动学** —— 视觉/碰撞/惯量需要 SDF + mesh 一起
3. **3MF 比 STL 更适合彩色** —— 多色打印优先走 3MF
4. **MoveIt2 路径必须走 SRDF** —— URDF 没有规划组、避障边界这些概念

这些是仓库通过技能分层间接传达给代理的常识，也是它和"普通 CAD 教程"最大的区别：技能描述里写的是"代理该怎么做"，而不是"人该怎么做"。