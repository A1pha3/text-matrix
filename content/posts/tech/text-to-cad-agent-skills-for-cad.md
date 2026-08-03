---
title: "Text to CAD：让AI代理直接生成CAD模型的技能库"
date: 2026-08-04T03:20:00+08:00
slug: "text-to-cad-agent-skills-for-cad"
github_repo: "earthtojake/text-to-cad"
description: "Text to CAD 是一个面向AI代理的CAD/CAE/CAM技能库，支持自然语言生成3D模型、机器人描述文件、G-code等工程输出，让AI成为硬件设计师的得力助手。"
draft: false
categories: ["技术笔记"]
tags: ["CAD", "3D建模", "AI代理", "开源", "机器人"]
---

## 项目概览

[Text to CAD](https://github.com/earthtojake/text-to-cad)（当前版本 0.3.13）是一个面向 AI 代理的开源技能库，覆盖 CAD、CAE、CAM 三大工程领域。它的核心理念很简单：让 Claude Code、Codex 等 AI 编码代理具备读写工程文件的能力——从 3D 模型到机器人描述文件，从 2D 工程图到 G-code 切片验证，一站式在本地完成。

截至目前，该项目在 GitHub 上获得了超过 12,600 个 Star、1,300 余个 Fork，采用 MIT 许可证，主语言为 JavaScript（技能定义层）与 Python（CAD 内核）。

**一句话定位**：如果你的 AI 代理能写代码，现在它也能画零件图了。

## 为什么需要 AI CAD 工具

传统 CAD 工作流有一个痛点：从「想法」到「可制造文件」之间的工具链太长。设计一个简单的 L 型支架，你需要打开 Fusion 360 或 SolidWorks，手动建草图、拉伸、打孔、倒角，然后导出 STEP/STL 文件。如果还需要 3D 打印，再导入切片软件生成 G-code。整个过程涉及三四个软件、十几次鼠标操作。

Text to CAD 把这条链路压成了一句话：

> 「创建一个 100×60×20 mm 的矩形校准块，带四个 8 mm 通孔，顶部外围倒 2 mm 角。」

AI 代理接收到这条自然语言指令后，调用 CAD 技能，生成符合工程标准的 STEP 文件，并可在本地浏览器中实时预览。不需要打开任何专业软件。

更重要的是，这些技能不只是一个 API 封装。它们为 AI 代理提供了完整的工作流定义：如何理解几何请求、如何调用底层引擎、如何验证输出、如何处理错误——这才是「技能库」而非「工具函数」的区别。

## 技能库全景

Text to CAD 包含 11 个技能，覆盖从设计到制造的完整链路：

| 技能 | 功能 | 输入 | 输出 | 适用场景 |
|------|------|------|------|----------|
| **CAD** | 创建和编辑 3D 模型 | 自然语言或图片 | STEP / STL / 3MF / GLB | 参数化建模、零件设计 |
| **CAD Viewer** | 本地浏览器预览 | CAD / G-code / 机器人文件 | 浏览器渲染 | 本地审查、可视化 |
| **step.parts** | 查找标准件 | 关键词描述 | STEP 文件 | 螺丝、轴承、电机选型 |
| **DXF** | 创建 2D 工程图 | Python 源或 CAD 几何 | DXF 文件 | 轮廓、垫片、切割排版 |
| **URDF** | 编写机器人结构文件 | 关节/连杆参数 | URDF XML | 机器人模型定义 |
| **SRDF** | 添加 MoveIt 规划组 | URDF + 规划参数 | SRDF XML | 运动规划、碰撞规则 |
| **SDF** | 创建仿真模型 | 物理/传感器参数 | SDF 文件 | Gazebo/Ignition 仿真 |
| **SendCutSend** | 检查制造文件 | DXF / STEP 文件 | 校验报告 | 在线钣金加工预检 |
| **G-code** | 切片验证 | 网格文件 + 打印配置 | G-code 文件 | FDM 3D 打印准备 |
| **Bambu Labs** | 3D 打印任务 | G-code 文件 | 打印任务 | 拓竹打印机远程控制 |
| **Implicit CAD** | GLSL 隐式建模 | GLSL 着色器代码 | 浏览器渲染 | 实验性隐式曲面建模 |

这些技能可以串联使用。典型的工作流是：CAD 生成模型 → CAD Viewer 预览 → step.parts 配齐标准件 → DXF 导出 2D 图纸 → G-code 切片 → Bambu Labs 发送到打印机。

## 安装

### 通过 Skills CLI 安装（推荐）

```bash
npx skills install earthtojake/text-to-cad
```

这是官方推荐的安装方式，会自动为受支持的 AI 代理安装所有技能。

### 通过 Codex 插件安装

```bash
# 需要 Codex 0.142.0 或更高版本
codex plugin marketplace add earthtojake/text-to-cad
codex plugin add cad@text-to-cad
```

> ⚠️ Codex 0.142.0 之前的版本会静默跳过插件安装，不会报错也不会出现在 `codex plugin list` 中。如遇问题，先升级：`npm install -g @openai/codex@latest`

### 通过 Claude Code 插件安装

```bash
claude plugin marketplace add earthtojake/text-to-cad
claude plugin install cad@text-to-cad
```

安装后如果技能未生效，重启代理即可。本地开发请基于 `develop` 分支，PR 也提交到 `develop`。

## 使用示例

安装完成后，在你的 AI 代理中直接用自然语言描述需求即可。以下是几个典型场景：

### 场景一：创建 3D 零件

> 创建一个直径 80 mm、厚 10 mm 的圆形法兰，中心有一个 30 mm 的通孔。在 60 mm 节圆直径上添加六个 6 mm 通孔，外圆边缘倒圆角。

CAD 技能会解析这段描述，生成参数化模型，输出 STEP 文件（主格式），同时可选导出 STL、3MF 和 GLB 格式。

### 场景二：查找标准件

> 我需要 4 颗 M3×10 mm 的不锈钢内六角螺丝，帮我找 STEP 模型。

step.parts 技能会从标准件库中检索匹配的型号，返回可直接装配的 STEP 文件。

### 场景三：机器人模型

> 为一个六轴机械臂编写 URDF 文件，基座高度 300 mm，臂展 800 mm，各关节包含惯量参数和限位。

URDF 技能会生成包含 links、joints、inertials、limits 和 meshes 的完整机器人描述文件，随后可以用 SRDF 技能为 MoveIt2 添加规划组。

## 基准测试

仓库内置了 10 个基准测试，从简单到复杂，直观展示了 CAD 技能的能力边界：

| # | 测试目标 | 复杂度 | 验证要点 |
|---|---------|--------|---------|
| 1 | 矩形校准块（四孔 + 顶部倒角） | ★☆☆☆☆ | 基础拉伸、孔阵列、倒角 |
| 2 | 圆形法兰（螺栓孔分布圆） | ★☆☆☆☆ | 旋转体、孔圆周阵列、圆角 |
| 3 | L 型支架（加强筋 + 双向孔） | ★★☆☆☆ | 多体组合、不同方向特征 |
| 4 | 阶梯轴（键槽 + 端部倒角） | ★★☆☆☆ | 旋转轴、键槽切削、倒角 |
| 5 | 电子外壳（带凸台） | ★★★☆☆ | 薄壁、内部沉孔、圆角 |
| 6 | 航空风格 U 型接头（减重孔） | ★★★☆☆ | 对称设计、加强筋、轻量化 |
| 7 | 星型发动机气缸（散热片） | ★★★★☆ | 阵列薄壁、角度特征、通孔 |
| 8 | 离心叶轮（后弯叶片） | ★★★★☆ | 螺旋扫掠、叶片融合 |
| 9 | 螺旋楼梯（含扶手） | ★★★★★ | 螺旋几何、阵列踏步、栏杆 |
| 10 | 行星齿轮组（太阳轮 + 行星轮 + 齿圈） | ★★★★★ | 齿轮啮合、多体装配、运动关系 |

每个基准测试都包含完整的 prompt 描述和期望输出的旋转预览图，可以用来评估不同 AI 代理在 CAD 任务上的表现。

## 适用边界

### Text to CAD 擅长的

- **参数化零件设计**：法兰、支架、外壳、轴类零件等规则几何体
- **标准件选型**：通过 step.parts 快速获取螺丝、轴承等现成 STEP 模型
- **机器人模型定义**：URDF/SRDF/SDF 三件套覆盖 ROS 2 开发全流程
- **制造准备**：从 3D 模型到 G-code 的自动切片和打印验证
- **原型迭代**：自然语言驱动，修改参数即可快速生成新版本

### 需要注意的

- **复杂曲面建模**：基准测试中最难的行星齿轮组仍使用「简化的梯形齿」，并非真正的渐开线齿廓。对于工业级曲面建模（如汽车外形、涡轮叶片），仍需专业 CAD 软件
- **Implicit CAD 是实验性的**：基于 GLSL 符号距离场的隐式建模目前仍标记为 Experimental，不适合生产环境
- **本地运行依赖**：CAD 技能底层依赖 Python 3.11+，需要本地安装相应的内核和依赖
- **不是替代品**：Text to CAD 是 AI 代理的技能增强，不是 Fusion 360 或 SolidWorks 的替代品。它的价值在于让 AI 代理具备工程文件读写能力，适合快速原型和自动化工作流

## 阅读路径

- **想快速上手**：直接跑 `npx skills install earthtojake/text-to-cad`，然后在你的 AI 代理里尝试基准测试 #1 的 prompt
- **想了解技能实现**：阅读仓库中 [skills/cad/SKILL.md](https://github.com/earthtojake/text-to-cad/blob/main/skills/cad/SKILL.md)，每个技能都有完整的工作流定义
- **想做本地开发**：阅读 [CONTRIBUTING.md](https://github.com/earthtojake/text-to-cad/blob/main/CONTRIBUTING.md)，从 `develop` 分支开始
- **想看完整文档**：访问 [cadskills.xyz](https://www.cadskills.xyz)，或在线 [Demo](https://demo.cadskills.xyz)
