+++
github_repo = "st-tech/ppf-contact-solver"
source_key = "gh:st-tech/ppf-contact-solver"
date = '2026-05-26T23:00:00+08:00'
draft = false
title = 'PPF Contact Solver：把「无穿透」做成数学保证的物理求解器'
slug = 'ppf-contact-solver-physics-simulation-guide'
description = 'PPF Contact Solver 是 ZOZO 开源的物理接触求解器，以连续碰撞检测加立方 barrier 从构造上保证求解成功即无穿透。本文覆盖其技术原理、真实 API 用法、性能数字的正确读法与采用建议。'
categories = ['技术笔记']
tags = ['物理仿真', 'Rust', 'Python', '开源', '计算机图形学']
+++

# PPF Contact Solver：把「无穿透」做成数学保证的物理求解器

物理仿真里最招人烦的问题不是算得慢，是穿模：两帧之间布料穿过人体，求解器根本没看见。多数引擎的对策是调参数、加后处理，把穿模压制到肉眼不明显。PPF Contact Solver 走了另一条路——它用连续碰撞检测配上自己提出的立方 barrier 函数，从数学构造上保证：只要求解成功，这一步就不存在任何穿插。这不是「穿模很少」，是零穿模。

这个项目最初是日本时尚电商 ZOZO, Inc. 的内部物理引擎，2024 年在 SIGGRAPH Asia 发表核心论文后开源。它为离线仿真而生，不追求实时帧率，也因此敢做游戏引擎不敢做的承诺。

## 项目速览

| 维度 | 数据 |
|------|------|
| 仓库 | [st-tech/ppf-contact-solver](https://github.com/st-tech/ppf-contact-solver) |
| 维护方 | ZOZO, Inc.，作者 Ryoichi Ando 兼职维护（不接受直接 PR，走 Issue/Discussion） |
| Stars | ~4.5k |
| 许可证 | Apache-2.0 |
| 实现语言 | Rust 为主（Python 仅作前端 API） |
| 支持对象 | 薄壳、固体、杆件、刚体、沙 |
| 硬件后端 | NVIDIA（CUDA 12.8+）、AMD（ROCm）、Apple silicon（Metal）、CPU（AVX2/NEON） |
| 核心论文 | A Cubic Barrier with Elasticity-Inclusive Dynamic Stiffness，ACM TOG Vol.43 No.6（SIGGRAPH Asia 2024） |

## 它解决什么问题

主流引擎普遍采用离散碰撞检测（DCD）：在每个时间步结束时检查物体有没有相交。步子迈大了，物体就会从一端直接跨到另一端，检测形同虚设——这就是穿模的主要来源。

PPF 采用连续碰撞检测（CCD）：检查的是整个时间区间内的运动轨迹，而不是孤立的两帧。配合论文提出的立方 barrier，把「不穿透」写进了求解目标本身——barrier 在接触距离处给出无穷大的能量壁，求解器只要收敛，结果就落在壁的这一侧。

README 对这个保证的措辞很克制，边界也讲得清楚：

- 保证的前提是**求解成功**。极端场景下（比如把接触厚度压到原子级、钉住的两块面板被驱动着互相穿过、布料卡进自交的角色动画），求解器可能找不到解，此时它会直接停下或崩溃——停下来恰恰是为了保住保证，硬算完就会静默接受穿透。
- 项目在 GitHub Actions 里对每次成功运行、每一步都跑交叉检查器，确认零穿透后才算通过。保证不是宣传语，是回归测试。

## 三条主线

这个项目的技术内容可以拆成三条互不重叠的主线，读它的代码和文档时分开看会清晰很多：

| 主线 | 关键词 | 一句话说明 |
|------|--------|-----------|
| 接触 | CCD、cubic barrier | 从构造上排除穿透，而不是检测后再修复 |
| 弹性 | FEM、符号雅可比、应变上界 | 变形体的力学计算，精度可控 |
| 工程 | Rust、GPU 并行、双前端 | 接触和弹性两个求解器都跑在 GPU 上 |

## 核心机制

### 接触：CCD 加立方 barrier

CCD 解决「看见」，barrier 解决「拦住」。论文的 contribution 在于那个立方 barrier 函数的刚度是动态的、把弹性也纳入考量，让求解器在保证无穿透的同时不需要付出传统 barrier 方法那种收敛代价。参考实现单独维护在 `sigasia-2024` 分支，并配有预编译 Docker 镜像，论文结果可以直接复现。

刚体部分来自另一篇论文（Painless Differentiable Rotation Dynamics），这是仓库里少数与主论文并行引用的技术来源。

### 弹性：FEM 加符号雅可比

变形体（薄壳、固体、杆件）用有限元方法计算力学，力对位置的雅可比由符号推导生成——手写雅可比容易出错，符号推导的雅可比和实现天然一致。GPU 上全部使用单精度，作者的理由很直接：单精度省一半带宽，而这个量级的仿真瓶颈正在访存。

面料参数不是拍脑袋给的。项目提供了一份 fabric report，把内置预设与真实织物的测量数据对齐， stretch、bend 这些参数在代码里设多少，现实里就有对应的参照。

### 工程：为 GPU 而写

接触求解器和弹性求解器都完整跑在 GPU 上，官方给出的极端案例超过 1.8 亿个接触点。2026 年 6 月借社区反馈完成了一次 2 倍性能优化；9 月又加入了 Metal、ROCm 和 SIMD 优化的 CPU 后端（AVX2/NEON）。

## 一次真实仿真：五张布落到球上

官方示例 `drape` 最能说明这个引擎的用法。任务：五张方形布料，两角钉住，依次落到下方的球面上。

前端是 Python，从 JupyterLab 里跑。第一步，生成网格、注册资产、搭场景：

```python
from frontend import App

app = App.create("drape")

# 生成一张 128x128 的方形网格，铺在 xz 平面
V, F = app.mesh.square(res=128, ex=[1, 0, 0], ey=[0, 0, 1])
app.asset.add.tri("sheet", V, F)

# 生成半径 0.5 的球
V, F = app.mesh.icosphere(r=0.5, subdiv_count=4)
app.asset.add.tri("sphere", V, F)

scene = app.scene.create()
gap = 0.05
for i in range(5):
    obj = scene.add("sheet").at(0, gap * i, 0)
    corner = obj.grab([1, 0, -1]) + obj.grab([-1, 0, -1])
    obj.pin(corner)                          # 钉住两角
    obj.param.set("strain-limit", 0.05)      # 应变上限 5%
    obj.param.set("young-mod", 1000).set("bend", 10.0)

# 球体作为静态碰撞体，加一点扰动避免完美对称
scene.add("sphere").at(0, -0.5 - gap, 0).jitter().pin()

scene = scene.build().report()
scene.preview()
```

API 是链式风格：`scene.add(...).at(...).jitter().pin()` 一路读下来就是这段物理设置的自然语序。`strain-limit` 就是前文说的应变上界——任何单个三角形的伸长不允许超过 5%，这是布料看起来「挺括」而不「橡皮」的原因。

第二步，建会话并开跑：

```python
session = app.session.create(scene)
session.param.set("frames", 100).set("dt", 0.01)
session = session.build()

session.start().preview()
session.stream()      # 实时滚动求解日志
```

第三步，导出动画、读日志。日志接口返回的是结构化数据，`time-per-frame` 是每帧耗时，`newton-steps` 是每帧消耗的牛顿迭代步数——求解器收敛难不难，看这个数字就知道：

```python
session.export.animation()

logs = session.get.log.names()
msec_per_video = session.get.log.numbers("time-per-frame")
newton_steps = session.get.log.numbers("newton-steps")
```

长任务不怕断线。前端支持会话恢复：服务器重启或浏览器关掉之后，用 `App.recover("drape")` 接回原来的会话，不用重跑已完成的帧。官方的大规模示例动辄上千帧，这个设计是刚需。

## 性能数字怎么读

README 里最显眼的数字是 1.8 亿接触、320 万顶点，先说清它们是什么、不是什么，再决定要不要为它动心。

大规模示例都在 RTX 4090 上跑：

| 示例 | 顶点 | 接触数 | 帧数 | 每帧耗时 |
|------|------|--------|------|----------|
| large-twist | 320 万 | 5670 万 | 2,000 | 46.4s |
| large-five-twist | 820 万 | 1.84 亿 | 2,413 | 144.5s |
| large-woven | 270 万 | 890 万 | 946 | 436.8s |

关键在最后一列：每帧几十到几百秒。这些数字衡量的是离线吞吐能力——单帧精度换时间，说明它完全不在「游戏引擎能不能用」的赛道上。倒过来读才有意义：46 秒算一帧、还能撑住 5670 万接触不穿模，这个精度-规模组合在开源引擎里没有几家能给出。

小规模场景的成本可以更直接地换算成钱。官方在 AWS `g6.2xlarge`（NVIDIA L4，约 $1/小时，性能约为 RTX 4090 的 36%）上跑完了全部 20 个示例：最便宜的 `yarn` 只要 $0.01，最贵的 `woven` 是 $0.39，drape 是 $0.04。部署开销约 8 分钟（$0.13）。想验证「这引擎对我的场景够不够用」，几毛钱就能拿到第一手数据。

## 上手路径

三种方式，按省事程度排序：

**1. 预编译二进制（最快）**。到 [GitHub Releases](https://github.com/st-tech/ppf-contact-solver/releases) 下载解压，macOS 和 Linux 直接 `./ppf-contact-solver`（自包含，不需要 Python、Homebrew 或 Xcode；Linux 需 glibc 2.28+），Windows 双击 `start.bat`。

**2. Docker**。仅支持 x86_64 + NVIDIA：

```bash
docker run --rm -it --name ppf-contact-solver --gpus all \
  -p 8080:8080 -p 9090:9090 -e WEB_PORT=8080 \
  ghcr.io/st-tech/ppf-contact-solver-compiled:latest
```

启动后浏览器打开 `http://localhost:8080` 就是现成的 JupyterLab，20 多个示例 notebook 直接能跑。README 特别警告：不要在本地跑 `warmup.py`，出问题很难清理。

**3. Blender 插件**。适合习惯在 DCC 工具里工作的用户。插件走远程架构：本地 Blender 只做场景编辑，仿真在远程 GPU 上跑、结果回传——所以 macOS 用户没有本地 N 卡也能用，这是它和多数要求本地 CUDA 的物理插件不同的地方。代价是后端要自己部署，不是一键安装。

还有一个玩法值得单独说：插件的所有工具都通过 MCP server（Model Context Protocol，让大模型调用外部工具的标准接口）暴露，任何接上 MCP 的 LLM（Claude、Codex 等）都能用一句自然语言完成建场景、调参数、跑仿真。README 里有 Codex 驱动 Blender 的演示截图。

## 适用边界

**值得上手的场景**：

- 布料、绳索、织物的高精度离线仿真——这是它的主场，面料参数有实测校准背书
- 影视/VFX 前期的物理效果预演，可以容忍每帧分钟级的计算时间
- 接触动力学研究：论文分支加预编译镜像，SIGGRAPH Asia 2024 的结果可直接复现
- 想「用嘴跑仿真」的 LLM 工作流：MCP 接口现成

**暂不适合**：

- 游戏等实时场景。它是离线求解器，部分小示例虽然能到交互速率，但这是副产品不是设计目标
- 逆向设计、可微仿真、强化学习。没有对仿真输入的梯度，这类工作流明确超范围
- 生产环境。项目自述尚未 production ready，已知 bug 在 Issues 里跟踪；AMD 的 ROCm 后端作者没有真实硬件测过，靠社区反馈修问题

## 结语

PPF Contact Solver 的价值不在「又一个物理引擎」，而在把一件通常靠调参糊弄的事变成了可验证的数学性质：求解成功即无穿透，并且每次提交都在 CI 里验证这一点。它源自 ZOZO 的内部引擎，仓库里保留着 `fitting`（服装试穿）这类与业务直接相关的示例；作者一人兼职维护、不接受直接 PR，这些约束反而让它保持了罕见的代码一致性。

判断其实很简单：需要离线高精度接触仿真，现在就可以拿 drape 试试，成本不到一毛钱；要的是实时或可微，等它都不必等——那是另一条技术路线的事。

👉 **GitHub**: https://github.com/st-tech/ppf-contact-solver
