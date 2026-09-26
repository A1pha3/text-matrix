---
title: "Text to CAD：让AI代理直接生成CAD模型的技能库"
date: 2026-08-04T03:20:00+08:00
lastmod: "2026-09-26T10:00:00+08:00"
slug: "text-to-cad-agent-skills-for-cad"
github_repo: "earthtojake/text-to-cad"
source_key: "gh:earthtojake/text-to-cad"
description: "Text to CAD 是一个面向 AI 代理的 CAD/CAE/CAM 技能库，13 个技能覆盖建模、2D 图纸、工程图、机器人描述文件、可制造性审查与 G-code 切片，让 AI 代理直接生成并验证工程文件。"
draft: false
categories: ["技术笔记"]
tags: ["CAD", "3D建模", "AI代理", "Agent Skills", "开源", "机器人", "DFM", "工程图"]
---

## 先给结论

Text to CAD（v0.6.6）是一个面向 AI 代理的技能库，覆盖 CAD、CAE、CAM 三个工程领域。它解决的问题很具体：Claude Code、Codex 这类代理会写代码，但一直读不懂工程文件。装了这个技能库，代理能自己生成 STEP 模型、写 URDF 机器人描述、审可制造性、切片出 G-code——全程不用人打开一次专业软件。

这个判断不是基于理念，而是有可验证的材料：项目 2026 年 4 月 22 日建仓，到 9 月 22 日 GitHub 上 16,277 个 Star、1,690 个 Fork（数据来自 GitHub API），MIT 许可证，仓库主语言为 Python。半年冲到 1.6 万星，社区用脚投票的速度说明这个缺口是真实存在的。

本文先给系统地图，再讲它为什么值得关注、技能怎么工作、能验证到什么程度，最后落到采用建议。

## 系统地图：13 个技能一张表

技能是这套系统的最小交付单元。下表按"设计 → 检查 → 制造"的链路排列：

| 技能 | 功能 | 输出 |
|------|------|------|
| **CAD** | 从自然语言或图片创建、编辑 3D 模型 | STEP（主格式），可选 STL / 3MF / GLB |
| **CAD Viewer** | 本地浏览器预览 CAD 与机器人文件 | 浏览器渲染 |
| **step.parts** | 查找标准件：螺丝、轴承、电机、连接器 | STEP 文件 |
| **Engineering Drawing** | 从零件生成带尺寸标注的 2D 工程图：视图、隐藏线、尺寸、孔标注、标题栏 | PDF |
| **DXF** | 创建 2D 图纸：轮廓、模板、垫片、切割排版 | DXF 文件 |
| **URDF** | 编写机器人结构文件：links、joints、limits、inertials、meshes | URDF XML |
| **SRDF** | 为 URDF 添加 MoveIt 规划组、末端执行器、位姿、碰撞规则 | SRDF XML |
| **SDF** | 创建仿真模型与世界：frame、物理、传感器、光源 | SDF 文件 |
| **SendCutSend** | 上传前检查 DXF / STEP 文件 | 校验报告 |
| **DfAM Check** | 测量网格可打印性：壁厚、悬垂、支撑体积、构建方向 | 测量报告 |
| **DFM** | 钣金 / CNC / 注塑制造审查，每条发现附测量证据与规则出处；测量拔模角、底切、投影面积 | 审查报告 |
| **G-code** | 用真实切片器 CLI 将网格文件切片为经过验证、带打印机配置的 FDM G-code | G-code 文件 |
| **Bambu Labs** | 试运行、上传并谨慎启动本地 Bambu Lab 打印任务 | 打印任务 |

13 个技能不是 13 个孤立工具。CAD 生成模型，CAD Viewer 预览，DfAM Check 查可打印性，G-code 切片，Bambu Labs 送打印——它们串起来就是一条从想法到实物的流水线。

## 为什么需要：AI 代理与工程文件之间的断层

传统 CAD 工作流的问题不在建模本身，而在工具链太长。做一个简单的 L 型支架：打开 Fusion 360 或 SolidWorks，建草图、拉伸、打孔、倒角，导出 STEP，再用切片软件生成 G-code。三四个软件、十几次鼠标操作，中间任何一步都可能是人的时间黑洞。

AI 代理补得上这个缺口吗？补不上——不是模型能力不够，而是它根本没有操作工程文件的接口。代理会写代码、会读 Markdown，但一个 STEP 文件对它来说是一堆无法理解的二进制，URDF 的关节约束、G-code 的打印参数更无从下手。

Text to CAD 的思路是给代理补齐这层接口，而不是做一个人工智能版本的 SolidWorks。它把"如何理解几何请求、如何调用底层内核、如何验证输出、如何处理错误"写进每个技能的工作流定义里，让代理按流程执行，而不是靠模型自己猜。

这层接口的价值可以从一个细节看出来：每个技能的 `requirements.txt` 都固定了配套 `cadgen` 内核的版本。技能与内核版本绑定，代理拿到什么版本就按什么版本的行为工作，结果可复现。

## 技能如何工作：工作流定义 + 本地内核

### 每个技能是一份 SKILL.md

技能不是一段提示词，而是一个完整的目录：入口 `SKILL.md` 定义触发条件和执行步骤，配套 reference 文件描述项目布局、运动学建模等约定。代理安装技能后，按这份定义执行，而不是自由发挥。

以 CAD 技能为例，它定义了一套工程化约定：

- 几何参数是模型函数的签名，改参数即改模型；
- 装配关系用 typed mates 表达，作为 `@step` 装饰器下 `kinematics=` 的纯数据；
- 动画编排是嵌入 Python 的 JavaScript，传给 `animation=`。

三件事分开写，几何、装配、动画各自独立，代理生成的代码结构是稳定的。

### 本地内核：cadgen

技能背后的 CAD 内核是 `cadgen`，一个随仓库发布、也在 PyPI 上线的 Python 包。它建立在 build123d 之上，底层是 OCP——OpenCascade 的 Python 绑定，另外集成 ezdxf 处理 2D 图纸、shapely 处理几何运算。所有建模和转换都在本地跑，不依赖任何云服务。

内核自带诊断命令 `cadgen doctor`。环境出问题时（比如下面要说的 Windows 原生模块被拦截），它直接点名问题所在，代理可以据此向用户报告而不是卡死。

### 验证是流程的一部分

每个技能在产出文件之后还留了一手验证，不是"生成完就交差"：

- G-code 技能调用真实切片器 CLI 切片，输出经过验证且带打印机配置，不是模拟生成的文本；
- SendCutSend 技能在文件上传前先做检查，避免把坏文件发给加工厂；
- DFM 技能的每条发现都附测量证据和规则出处，拔模角、底切、投影面积从网格实测得来。

这层验证正是"技能库"和"工具函数"的分界：工具函数只负责把输入变成输出，技能库负责让输出值得信任。

## 一个完整流转案例：从想法到实物

把 13 个技能串起来看一条完整链路，比单个技能的描述更有说服力。假设要做一个带四个安装孔的外壳：

1. **CAD**：用自然语言描述外壳尺寸、壁厚、孔位，生成 STEP 文件；
2. **CAD Viewer**：本地浏览器里预览，确认形状符合预期；
3. **step.parts**：为安装孔找四颗标准螺丝的 STEP 模型；
4. **Engineering Drawing**：从零件生成带尺寸标注的 2D 工程图，给加工厂或装配文档用；
5. **DfAM Check**：测量壁厚和悬垂，判断这个模型适不适合 3D 打印；
6. **G-code**：切片出针对本机打印机的 G-code；
7. **Bambu Labs**：试运行校验后发送到打印机。

人在这个流程里的角色从"操作者"变成了"验收者"：每个环节代理做完，人只看结果。整条链路每步的输入都是上一步的输出，中间不需要人手动转换格式。

## 能力纵深：从校准块到猎鹰重型

想知道这套技能的能力边界，仓库的 `models/` 目录是最好的证据——它是一套用 Git LFS 管理的演示语料，全部由 CAD 技能生成，从简单的独立零件到复杂的整机装配：

- **examples/**：独立零件，一个脚本一个模型；
- **assemblies/**：装配体，包括带 typed mates 和动画的行星齿轮装配、火星车概念；
- **drawings/**：2D DXF 图纸；
- **thang010146/**：来自同名 YouTube 频道的机械机构，逐个导入并加了运动学注释；
- **f1/**：开轮 F1 赛车，DRS 四连杆和转向机构都是闭环求解；
- **f14d/**：格鲁曼 F-14D 雄猫，放样机身蒙皮外加十个系统分组；
- **w16/**：8.0 升四涡轮 W16 引擎，13 个系统模型，博物馆剖切视角；
- **tendon_hand/**：腱驱动研究用手，24 个关节自由度、48 根拮抗肌腱，仅提供源码；
- **falcon_heavy/**：猎鹰重型运载火箭，三芯级、27 台 Merlin 1D 实例、约 2,150 个命名零件；
- **juno/**、**lyra/**：人形机器人（27 自由度）和灵巧手（16 自由度），各自带着配套 URDF / SRDF。

这套语料怎么读：它能证明技能在参数化建模、装配约束、运动学、机器人描述上的能力是真实跑出来的，不是宣传文案。但要注意另一面——猎鹰重型的 README 明确标注"基于公开资料的教育性重建，不适用于制造、推进、测试或工程运营"。演示语料证明的是"代理能生成什么"，不是"生成的东西可以直接生产"。

`models/` 默认不在常规克隆的下载范围内（仓库用 LFS 配置把 `models/**` 排除在默认拉取之外），需要本地字节时执行 `git lfs pull --include="models/**" --exclude=""`。

## 安装与接入

### 通过 Skills CLI 安装（推荐）

```bash
npx skills add earthtojake/text-to-cad
```

`add` 是官方命令，直接把各技能安装到受支持的代理。升级也用同一条命令——`add` 会重新拉取并覆盖已装内容；而 `npx skills update` 只刷新 lockfile 里已有的技能，会静默漏掉新版本新增的技能（本项目每个版本都在加技能，这条差异值得记住）。`npx skills install` 仍然可用，但它是 `add` 的未文档化别名。

### 通过 Codex 插件安装

```bash
# 需要 Codex 0.142.0 或更高版本
codex plugin marketplace add earthtojake/text-to-cad
codex plugin add cad@text-to-cad
```

Codex 从 0.142.0 起才解析仓库根插件。更早的版本会静默跳过插件安装，不出现在 `codex plugin list` 里也不报错。遇到这种情况先升级：`npm install -g @openai/codex@latest`。

### 通过 Claude Code 插件安装

```bash
claude plugin marketplace add earthtojake/text-to-cad
claude plugin install cad@text-to-cad
```

### 通过 Grok Build 安装

```bash
grok plugin install earthtojake/text-to-cad --trust
grok plugin enable cad
```

Grok Build 复用仓库里现成的 `.claude-plugin/marketplace.json`，没有单独的插件清单。

安装后技能没生效，重启代理即可。本地开发从 `main` 分支开始，PR 也提交到 `main`。

## 常见问题与排查

**Windows 11 上 `import build123d` 报 `ImportError: DLL load failed`。** 原因是 CAD 内核依赖的 OCP（OpenCascade 的 Python 绑定）wheel 自带未签名的原生模块，Windows 11 的 Smart App Control（新装机器默认开启）会拦截未签名原生代码，事件查看器里记录为 CodeIntegrity 下的 Event ID 3077。`cadgen doctor` 能检测到这个问题。Smart App Control 没有按应用放行的例外，要么关掉它（关闭后只能重装系统才能重新开启），要么把 CAD 技能放到 WSL 里跑。wheel 由 cadquery-ocp 项目构建，签名不是本仓库能做的事。

**技能安装了但在代理里不出现。** 先重启代理，仍不生效再检查插件版本（Codex 的场景见上文）。

**技能说环境有问题。** 跑 `cadgen doctor`，内核会直接指出缺什么。

## 适用边界

### Text to CAD 擅长的

- **参数化零件设计**：法兰、支架、外壳、轴类等规则几何体，改参数即出新版本；
- **标准件选型**：step.parts 直接返回螺丝、轴承等现成 STEP 模型；
- **机器人模型定义**：URDF / SRDF / SDF 覆盖 ROS 2 开发链路；
- **制造预检**：DfAM Check 查可打印性、DFM 审钣金 / CNC / 注塑、SendCutSend 验上传文件；
- **打印准备**：G-code 切片 + Bambu Labs 送打印，全自动；
- **2D 与工程图**：DXF 出切割排版，Engineering Drawing 出带标注的图纸 PDF。

### 需要注意的

- **它不是 Fusion 360 或 SolidWorks 的替代品**：适合快速原型和自动化工作流，工业级曲面造型、大型装配管理仍要专业软件；
- **演示语料 ≠ 生产零件**：`models/` 里的猎鹰重型等复杂模型是教育性重建，不代表输出可以直接制造；
- **本地运行依赖**：技能底层依赖 Python 环境和 build123d / OCP 等内核依赖，第一次运行要装齐；Windows 上另有 Smart App Control 的坑（见上文）。

## 采用建议

按由浅入深的顺序引入：

1. **先验证**：装好技能，让代理复现 `models/` 里一个简单零件，确认本地内核和技能链路是通的；
2. **个人原型**：日常零件设计交给 CAD + CAD Viewer，替代重复的参数化建模；
3. **标准件与图纸**：设计里需要选型、出 2D 图时接入 step.parts 和 DXF / Engineering Drawing；
4. **机器人项目**：做 ROS 2 开发时用 URDF / SRDF / SDF 三件套；
5. **制造闭环**：要真打印或外发加工时，接上 DfAM Check、G-code、SendCutSend、DFM。

如果工作流里根本没有"生成工程文件"这一步——比如你只写业务代码、不碰机械件——那这套技能库暂时用不上。它值得关注，但不必为了安装而安装。

## 阅读路径

- **看完整文档**：[texttocad.dev](https://www.texttocad.dev)
- **看技能实现**：仓库 [skills/](https://github.com/earthtojake/text-to-cad/tree/main/skills) 下每个技能目录的 [SKILL.md](https://github.com/earthtojake/text-to-cad/blob/main/skills/cad/SKILL.md)，定义了完整工作流
- **看演示语料**：仓库 [models/](https://github.com/earthtojake/text-to-cad/tree/main/models) 的 README 是模型目录地图
- **做本地开发**：阅读 [CONTRIBUTING.md](https://github.com/earthtojake/text-to-cad/blob/main/CONTRIBUTING.md)，从 `main` 分支开始
