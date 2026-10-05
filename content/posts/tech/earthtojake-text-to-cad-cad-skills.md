---
title: "text-to-cad：把 CAD、机器人与制造链路拆给 AI 代理的 13 个技能"
date: "2026-08-02T02:59:48+08:00"
lastmod: "2026-09-29T10:00:00+08:00"
slug: "earthtojake-text-to-cad-cad-skills"
github_repo: "earthtojake/text-to-cad"
source_key: "gh:earthtojake/text-to-cad"
author: "钳岳"
canonical: "https://txtmix.com/posts/tech/earthtojake-text-to-cad-cad-skills/"
description: "earthtojake/text-to-cad 把 CAD、CAE、CAM 工程链路拆成 13 个可独立加载的代理技能：build123d 参数化建模、几何引用与快照验证、URDF/SDF/SRDF 机器人描述、DFM 审查、真实切片器切片、Bambu 打印接力。本文拆解它的模型契约、验证机制与适用边界，数据核实至 2026 年 9 月底。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "CAD", "URDF", "SDF", "机器人", "3D 打印", "DFM"]
---

## 一句话判断

多数 "text-to-3D" 项目把力气花在"一句话生成一张网格"上，网格能不能进后续工序没人管。`earthtojake/text-to-cad` 走的是另一条路：它不替代理画图，而是把"设计 → 检视 → 制造 → 打印"这条工程链路拆成 13 个技能，每一步产出可打开、可测量、可复查的工件文件——STEP、URDF、DXF、G-code。代理缺哪段补哪段，每一步都有检查手段。

## 项目现状

仓库 2026 年 4 月 22 日创建，到 9 月底已有 16,462 stars、1,706 forks，MIT 许可证，要求 Python 3.11+（GitHub API 快照 2026-09-29）。官方一句话定位是 "A library of agent skills for CAD, CAE and CAM"，文档站 [texttocad.dev](https://www.texttocad.dev) 的自我描述是 "100% open source + free, runs locally"——本地运行是这个项目的底线设定。

本文初稿写于 8 月初，那时仓库刚满三个月。此后项目明显加速：支撑技能运行的 `cadgen` 包 8 月 11 日才首次发布到 PyPI（0.4.1），9 月 27 日一天连发 0.7.0、0.7.1、0.7.2 三个版本；技能数量也从早期围绕工件格式的六枚徽章，扩展到覆盖设计、审查、机器人、采购、打印的 13 个。下文按 9 月底的 0.7.2 版本描述。

## 13 个技能怎么分工

安装整个库，代理得到的是一条工序链，而不是一个庞大 CLI：

| 工序 | 技能 | 做什么 |
|------|------|--------|
| 设计 | `cad` | 从自然语言或图片建参数化模型，STEP 为主输出，可导出 STL/3MF/GLB |
| 设计 | `dxf` | 生成 2D DXF：轮廓、模板、垫片、切割排版 |
| 检视 | `cad-viewer` | 在本地浏览器里预览 CAD 与机器人文件 |
| 检视 | `engineering-drawing` | 从零件出带尺寸标注的工程图 PDF：视图、隐藏线、孔标注、标题栏 |
| 检视 | `dfam-check` | 按工艺测网格可打印性：壁厚、悬垂、支撑体积、建造方向 |
| 检视 | `dfm` | 钣金/CNC/注塑可制造性审查，每条结论附测量证据与规则出处 |
| 机器人 | `urdf` | 写机器人结构文件：links、joints、limits、惯量、网格引用 |
| 机器人 | `srdf` | 在 URDF 上加 MoveIt 语义层：规划组、末端执行器、位姿、碰撞规则 |
| 机器人 | `sdf` | 建仿真模型与世界：坐标系、物理、传感器、光源 |
| 采购 | `step-parts` | 在 step.parts 目录检索现成零件（螺丝、轴承、电机、连接器），下载其 STEP 文件 |
| 加工 | `sendcutsend` | 检查 DXF/STEP，准备上传 SendCutSend 钣金服务 |
| 打印 | `gcode` | 编排真实切片器 CLI，把网格切成带打印机 profile 的 FDM G-code |
| 打印 | `bambu-labs` | 从验证过的 G-code 干跑、上传、谨慎启动本地 Bambu Lab 打印任务 |

表格之外值得记住的一点：这些技能不是平铺的菜单，`cad` 是主干，其余技能在它的 SKILL.md 里有明确挂接点——需要 2D 图纸时转给 `$dxf`，需要紧固件时先查 `$step-parts` 再画占位几何，建好模型后把文件路径交给 `$cad-viewer` 出预览链接。机器人三件套则自成一支，与 CAD 主干平行。

## 核心机制：cad 技能的模型契约

`cad` 技能对"模型"的定义很严格：一个普通 Python 脚本，里面是一个无参的装饰函数，返回 build123d 形状。仓库自带的示例 `src/bracket.py`：

```python
from cadgen import build123d as bd
from cadgen import step

WIDTH = 40.0


@step(out="../STEP/bracket.step")
def bracket():
    body = bd.Box(WIDTH, 20, 6)
    body.label = "bracket"
    return body


if __name__ == "__main__":
    bracket()
```

运行 `python src/bracket.py`，装饰器就把返回的形状写进 STEP 文件。想常驻维护网格输出，把 `@stl`、`@threemf` 或 `@glb` 叠在同一个函数上；只想从现成 STEP 一次性导出，走命令：

```bash
cadgen stl build STEP/bracket.step STL/bracket.stl
cadgen 3mf build STEP/bracket.step 3MF/bracket.3mf
cadgen glb build STEP/bracket.step GLB/bracket.glb
```

SKILL.md 给代理立的规矩比"怎么生成"更值得看：

- 尺寸用毫米，默认 XY 平面、+Z 朝上，除非任务另有约定；
- 装配体在父模型里调用子模型，用 `.moved()` 或 `Location * shape` 摆位，改了子模型就重跑父模型；
- 供应商 STEP 用 `cadgen.read_step` 读入并记录为构建输入，其他数据输入用 `cadgen.declare_input` 声明——模型不许把自己的输出当自己的输入；
- 几何不得依赖时间、随机数、环境变量或工作目录。

最后两条是奔着可重建性去的：任何一次重新运行都应得到同样的几何，构建系统才能判断"哪些输出需要重建、哪些没变"。配套的 `cadgen store why <model>.py` 用来解释一次意外的重建，`python <模型>.py --force` 强制单个模型重建，`cadgen daemon status` 看构建进度。

这套契约的底座是 `cadgen` PyPI 包（官方摘要："STEP-first CAD artifact generation runtime"），CAD 内核是 OCP——OpenCascade 的 Python 绑定，建模 API 来自 build123d。每个技能的 `requirements.txt` 钉死与发布版配套的 `cadgen` 版本（0.7.2 对应 `cadgen[snapshot]==0.7.2`）。快照渲染依赖 Chromium，装完技能还要跑一次 `python -m playwright install chromium`。

## 让代理"指着几何说话"：引用语法与验证闭环

生成只是半个环节，`cad` 技能花在"验证"上的笔墨比生成还多。

第一步是精确指认。`assembly.step#o1.2.f7` 这样的引用语法可以在保存的文档里定位到具体对象和面，代理用 `read_scene` 打开文件、`resolve` 解析引用，拿到原生几何做测量：

```python
from cadgen import read_scene

scene = read_scene("STEP/assembly.step")
selection = scene.resolve("assembly.step#o1.2.f7")
face = selection.shape()
print(selection.ref, face.area)
```

SKILL.md 明确说没有 inspect CLI：探索性检查脚本放项目忽略的 `tmp/`，可复用的检查留在 `checks/` 或现有测试目录，不得混进模型源码和输出目录。

第二步是看图。创建或明显改动了几何之后，代理必须生成至少一张快照并复查：

```bash
cadgen step snapshot STEP/bracket.step tmp/review.png
cadgen stl snapshot STL/bracket.stl tmp/mesh.png
```

第三步是汇报纪律：验证要按用户要的尺寸、间隙、拓扑选检查项，报告里写清单位、阈值、所选几何和未覆盖的需求。SKILL.md 里有一句值得直接引用的话——"A failed computation is not a pass"，算不出结果的检查不算通过。修好源码、重跑受影响的检查，这一步才算收尾。

装不上、加载失败时另有诊断入口：`cadgen doctor <skill-dir>` 检查包版本钉死与 CAD 内核状态，OCP 加载错误它会直接点名原因。

## 一次真实任务流：把支架加宽并送进打印机

把上面这些机制串一遍。用户说："把 bracket 加宽到 50 mm，确认开孔到边缘的距离，然后在我打印机上打一个。"

1. 代理找到 `src/bracket.py`，把 `WIDTH` 改成 50.0，运行脚本。`@step` 输出的 STEP 重建，叠了 `@stl` 的网格同步重建；
2. 用 `read_scene` 打开新 STEP，`resolve` 到孔位所在的面，写个小脚本量孔心到边缘的距离，与要求比对——量不出来就如实报告，不硬凑通过；
3. `cadgen step snapshot` 出 PNG，换一个能暴露孔位特征的视角复查；
4. 需要螺丝固定时，先查 `$step-parts` 而不是画占位几何。SKILL.md 连检索姿势都交代了：型号名要试别名和厂商拼法，`STS3215` 可能写作 `ST3215`、`3215` 或归到 Feetech 家族下；API 可达但没有匹配才算检索失败，记录后再用简化包络；
5. 进入 `gcode` 技能切片。它要求代理使用明确的打印机/profile 包装 JSON，不许自己编造真实打印机的 profile；后端不明就先 `python scripts/gcode_tool.py discover` 找本地切片器；
6. G-code 通过静态验证后交给 `bambu-labs`：先干跑，再上传，最后才谨慎启动打印。

注意这个流程里没有一步是"相信模型生成的对"。每一步产物都是文件，每个文件都有对应的检查命令——这是它和"生成一张网格看看像不像"的根本分野。

## 机器人三件套：URDF、SRDF、SDF 的分工

三条主线各有领地。`urdf` 技能管机器人结构文件，SKILL.md 把 URDF 工作定义为"受约束的运动学建模，不是写 XML"，并列出五个主要出错点：坐标系摆放、关节轴语义、单位一致、网格缩放、惯量数据。注意 URDF 本身就包含惯量与视觉/碰撞几何的网格引用，"URDF 只有运动学"是常见误解。

`srdf` 技能不另起炉灶，它是在 URDF 之上加 MoveIt 需要的语义层——规划组、末端执行器、命名位姿、碰撞规则。`sdf` 技能面向 Gazebo 一类仿真器，写的是模型与世界：坐标系、物理参数、传感器、光源。仿真侧的增量（传感器、光源、世界组合）正是 SDF 与 URDF 的分界。

## 安装：一条首选路径，两条插件路径，一个 Windows 坑

首选路径是 Skills CLI：

```bash
npx skills add earthtojake/text-to-cad
```

README 特意提醒了更新语义：**更新用同一条 `add` 命令**，它重新拉取并覆盖已装技能；`npx skills update` 只刷新 lockfile 里已有的，会静默漏掉新版新增的技能——对这个"发版会加技能"的项目来说是要紧事。上游退役的技能两条命令都不会替你删，需要 `npx skills remove <skill>`。`npx skills install` 是 `add` 的未文档化别名，仍然可用。

三家代理另有原生插件路径：

```bash
# Codex（需 0.142.0+，更旧版本会静默跳过、插件列表里也不出现）
codex plugin marketplace add earthtojake/text-to-cad
codex plugin add cad@text-to-cad

# Claude Code
claude plugin marketplace add earthtojake/text-to-cad
claude plugin install cad@text-to-cad

# Grok Build（复用 .claude-plugin/marketplace.json，无独立清单）
grok plugin install earthtojake/text-to-cad --trust
grok plugin enable cad
```

装完不出现就重启代理。仓库里的 `models/` 固定件语料以 LFS 指针形式存在，用技能不需要它。

Windows 用户有一个绕不开的坑：CAD 内核 OCP 的 wheel 带未签名原生模块，Windows 11 的 Smart App Control 默认拦截未签名原生代码，症状是所有 `cadgen` 命令和 `import build123d` 报 `ImportError: DLL load failed while importing OCP`，事件查看器在 CodeIntegrity 下记 Event ID 3077。SAC 没有按应用放行的机制——要么整体关掉（关闭后想再开只能重装 Windows），要么把 CAD 技能放进 WSL 跑。wheel 由 cadquery-ocp 项目构建，本仓库无力签名。

## 与同类技能集的差异

放在技能生态里看，它的切法相当少见：

| 仓库 | 定位 | 技能颗粒度 | stars |
|------|------|-----------|-------|
| `emilkowalski/skills` | 给设计师和工程师的技能集 | 一条实践原则 = 一个 skill | 41,667 |
| `virgiliojr94/book-to-skill` | 把技术书 PDF 变成 Claude Code 技能 | 一本书 = 一个 skill | 32,903 |
| `earthtojake/text-to-cad` | CAD/CAE/CAM 工程链路 | 一道工序 = 一个 skill | 16,462 |
| `NomaDamas/k-skill` | 让代理按韩国语境行事的技能集 | 一项本地化能力 = 一个 skill | 7,706 |

（stars 为 2026-09-29 GitHub API 快照。）

多数技能库在"知识"层面做文章——品味、教程、本地化常识。text-to-cad 切的是工序边界：设计、检视、机器人、采购、加工、打印，每道工序有自己的工件格式和验收手段。工程链路本来就有清晰的交接物，按工序切技能，代理就能按"我现在在哪一步"做局部激活，不必每次加载全部上下文。更难得的是它把验证写进了技能契约——快照必出、失败不算通过、检索失败要记录，这在同类技能集里几乎没有对手。

## 适用边界与采用顺序

**适合**：

- 在 Claude Code、Codex、Grok Build 里有 Python 3.11+ 环境、想让代理产出真实可加工工件的人；
- 做机器人原型，要产出 URDF/SRDF/SDF 并接 MoveIt2 或仿真的人；
- 有 Bambu Lab 打印机、想让"改模型 → 切片 → 打印"整条链在代理里跑通的人；
- 想把几何知识与工艺参数沉淀成代理可执行资产、而不是躺在 wiki 里的团队。

**不适合或要注意**：

- 期望"文生 3D"的人——这是参数化建模，输出靠 build123d 代码生成，不是扩散模型出网格；
- 找求解器级 CAE（结构、流体、热仿真）的人——定位里的 CAE 落在 DfAM/DFM 这类分析与审查上，不是有限元求解；
- 依赖 PLM/PDM 流程集成的企业场景——技能层不管这一段；
- 开着 Smart App Control 的 Windows 11 裸机——除非走 WSL。

采用顺序建议：先装 `cad` + `cad-viewer`，拿一个简单零件跑通"改参数 → 重建 → 快照复查"，确认 OCP 在你的环境里装得上（Windows 先看 SAC）；采购和打印链路（`step-parts`、`gcode`、`bambu-labs`）按任务需要再加；机器人三件套与 CAD 主干基本独立，做机器人的直接从 `urdf` 进。

## 结尾判断

这个仓库最值得借鉴的不是某个具体技能，而是它给代理立的规矩：几何不得依赖环境、模型不得吃自己的输出、改完几何必出快照、算不出的检查不算通过、检索失败要记录再降级。技能会过时，命令会改名，但这些约束回答的是"代理做工程时凭什么让人放心"——把一次性的生成，变成一条每步可复查的流程。这也是它比大多数技能库走得更远的原因：知识可以塞给代理，纪律必须写进契约。
