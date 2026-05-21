---
title: "OpenToonz：开源工业级2D动画制作软件完全指南"
date: "2026-05-20T20:22:00+08:00"
slug: "opentoonz-open-source-2d-animation-guide"
description: "OpenToonz是基于Toonz Studio Ghibli Version开发的开源2D动画软件，拥有6112 Stars和711 Forks，支持Windows、macOS、Linux平台。本文深入解析其架构设计、核心功能模块、历史沿革及与商业软件的定位差异。"
draft: false
categories: ["技术笔记"]
tags: ["OpenToonz", "2D动画", "开源软件", "动画制作", "Ghibli"]
---

# OpenToonz：开源工业级2D动画制作软件完全指南

## 核心判断

OpenToonz 不是什么"入门级动画工具"，而是一套从日本工业动画生产线脱胎而来的专业级 2D 矢量与位图混合动画制作系统。它的技术血脉直接来自 Digital Video, S.p.A.（意大利）为 Studio Ghibli（吉卜力工作室）定制的 Toonz Studio Ghibli Version——这意味着它从第一天起就不是为"画着玩"设计的，而是为"能进电影院"设计的。

如果你在找一款免费、无版权限制、可以承接中等规模商业项目生产的 2D 动画软件，OpenToonz 是目前开源生态里最接近这个目标的选择。如果你在找一款五分钟上手的简易工具，这个仓库不适合你。

---

## 项目概览

| 项目 | 信息 |
|------|------|
| 仓库 | [opentoonz/opentoonz](https://github.com/opentoonz/opentoonz) |
| Stars / Forks | 6112 / 711 |
| 主要语言 | C++（约 26.6M 行），其次是 C、HLSL、Less、CMake |
| 许可证 | Modified BSD License（`thirdparty` 目录除外） |
| 维护活跃度 | 最新 release 为 nightly build 2026-05-20；最近一次正式版 v1.7.1 发布于 2023-05 |
| 官方网站 | <https://opentoonz.github.io/e/index.html> |
| 文档 | <https://github.com/opentoonz/opentoonz_docs> |

核心贡献者包括 RodneyBaker（1116 次提交）、shun-iwasawa（966 次提交）等，主要来自日本动画社区和开源社区。

---

## 历史沿革：Toonz → Studio Ghibli → OpenToonz

理解 OpenToonz，需要先理解它的血统。

**第一代：Toonz（Digital Video, Italy）**

1980 年代末，意大利公司 Digital Video, S.p.A. 开发了一款名为 Toonz 的 2D 动画软件，在当时的动画工作站市场上属于高端产品。这套系统的设计目标是为专业动画工作室提供完整的无纸化解决方案，包括矢量绘制、有限动画（limited animation）、特殊效果合成等功能。

**第二代：Toonz Studio Ghibli Version（DWANGO + Studio Ghibli）**

1990 年代，日本公司 DWANGO（后与 KADOKAWA 合并）获得 Toonz 源码授权，并与 Studio Ghibli 合作，在多年实际生产中对其进行深度定制。Ghibli 版本增加了大量面向电影级动画生产的功能，包括更高的色彩管理精度、更精细的矢量控制、以及与 Studio 生产流程匹配的摄制跟踪（camera tracking）能力。

**第三代：OpenToonz（开源化）**

2016 年，DWANGO 将基于 Toonz Studio Ghibli Version 的代码库开源，发布为 OpenToonz。开源的目标有两个：一是让全球独立动画创作者能够使用这套专业工具；二是借助社区力量继续推进功能开发。值得注意的是，原始 Toonz 代码的版权仍然归属于 Digital Video, S. p.A.（意大利），OpenToonz 的开源基于 DWANGO 的授权条款进行。

---

## 架构设计：模块分层与核心组件

### 目录结构

```
opentoonz/
├── toonz/               # 核心应用程序代码
├── stuff/               # 内置资源（笔刷、样式表、模板）
├── thirdparty/          # 第三方依赖库
├── plugins/             # 插件系统
├── doc/                 # 构建文档
└── .github/             # CI/CD 配置
```

### 核心模块分析

**toonz 目录**是整个项目的主干，包含：

- **RasterBrush（光栅笔刷系统）**：支持自定义笔刷形状、压力感应、混合模式，是动画师日常使用最频繁的模块。
- **Vector Animation（矢量动画）**：与位图层混合使用，支持路径编辑、描摹（trace）功能，可将铅笔线稿转换为可控的矢量曲线。
- **Scene Management（场景管理）**：以 `.tnz` 为后缀的项目文件格式，支持多镜头（multi-camera）、多层次（multi-level）组织方式，与传统动画摄影台（camera stand）的操作逻辑高度一致。
- **Xsheet（时间轴表）**：OpenToonz 的核心编辑界面，模拟传统动画台上的 Xsheet（定位销纸），允许逐帧、逐层、逐栏目地进行动画编排。这是 Toonz 系列区别于大多数现代动画软件的最显著特征。
- **FX（特效系统）**：内置基于 GLSL/HLSL 的渲染管线，支持色调分离、胶片颗粒、运动模糊等电影级特效。

**stuff 目录**存放的是预置资源：

- 内置画笔（brush）库
- 样式表（stylesheets）
- 纹理素材
- 输出模板

这些资源与应用程序二进制分离，允许用户自定义和扩展。

**plugins 目录**提供插件接口，支持第三方扩展。

### 语言分布的技术含义

从 GitHub 的语言统计数据看：

| 语言 | 规模 | 角色 |
|------|------|------|
| C++ | 26.6M 行 | 核心渲染引擎、UI、场景管理 |
| C | 1.8M 行 | 系统级底层绑定 |
| HLSL / GLSL | ~180K 行 | GPU 着色器与特效渲染 |
| Less | 149K 行 | Web 前端样式（文档站相关） |
| CMake | 119K 行 | 跨平台构建系统 |

C++ 主导意味着这是一套对性能要求极高的实时渲染系统，动画软件中大量存在的笔刷延迟、路径平滑、帧缓冲处理都依赖底层 C++ 实现。

---

## 核心能力：为什么动画工作室关注 OpenToonz

### 1. 工业级无纸化工作流

OpenToonz 的设计哲学是"尽可能保留传统动画工艺的灵活性，同时消除纸张介质的所有物理限制"。这具体体现在：

- **Xsheet 界面**：与实体定位销纸一一对应的数字界面，老版动画师可以无缝迁移。
- **Column（栏）系统**：每个角色、每个物件独占一栏，支持独立时序编辑，天然适配多角色复合动画场景。
- ** Onion Skin（叠影）**：显示前后帧叠加，是动画师打中间帧的必备工具，OpenToonz 支持多层级 onion skin 配置。

### 2. 矢量与位图混合绘制

OpenToonz 不强制用户二选一。一个场景里可以同时存在：

- 矢量绘制的角色主体（放大不失真，便于绑定运动）
- 位图绘制的前景物件（支持随意笔触质感）
- 照片级背景合成

这种混合方式在 Studio Ghibli 的实际生产中被长期使用。

### 3. 有限动画（Limited Animation）工具链

日本电视动画大量依赖有限动画技法——角色只动嘴型和身体关键部位，其他部分保持静止。OpenToonz 提供了：

- **自动口型同步（Lip Sync）工具**：输入音频，自动生成对口型的帧序列。
- **插值曲线编辑器**：关键帧之间可以精细控制缓动（easing）曲线。
- **多层次复用机制**：同一角色在不同场景中可以通过组件复用降低重复劳动。

### 4. 自定义笔刷系统

OpenToonz 的笔刷引擎支持完整自定义：

- 可导入自定义纹理
- 压力曲线可调
- 支持笔刷动画（brush animation，即笔刷形状随时序变化）

这对追求手绘质感的独立动画创作者是关键能力。

---

## 与同类开源项目的定位差异

OpenToonz 并不是"唯一选择"。同类 2D 动画开源软件包括 Pencil2D、Synfig Studio、Krita（动画模块）等。它们之间的定位差异：

| 软件 | 定位 | 强项 | 弱项 |
|------|------|------|------|
| **OpenToonz** | 专业级工业生产 | Xsheet、矢量位图混合、Ghibli 血统、有限动画工具链 | 界面较老，上手门槛高 |
| **Synfig Studio** | 矢量骨构图动画 | 骨架（bone）系统强大，适合角色绑定 | 位图编辑能力弱，界面更复杂 |
| **Pencil2D** | 轻量位图动画 | 简洁，上手快 | 功能有限，无 Xsheet，无矢量 |
| **Krita** | 数字绘画 + 动画模块 | 绘画功能强大，社区活跃 | 动画模块不是主业，非 Xsheet 界面 |

OpenToonz 的差异化价值在于：**它是唯一一套把 Xsheet 作为原生一等公民的开源方案**。如果你需要制作多角色、多层次、有专业分工（线稿师、上色师、合成师协作）的动画项目，OpenToonz 的数据模型天然适配这种工作方式。Synfig 的骨架系统更适合"一个人绑定并驱动一个角色"，而不适合"工作室分工制作一个镜头"。

---

## 安装与构建

### 官方预编译版（推荐新手）

从 <https://opentoonz.github.io/e/index.html> 下载最新 installer，支持 Windows、macOS、Linux。预编译版开箱即用，无需自行编译。

### 从源码构建

官方文档分别在以下位置：

- [Windows]({{</* relref "doc/how_to_build_win.md" */>}})
- [macOS]({{</* relref "doc/how_to_build_macosx.md" */>}})
- [Linux]({{</* relref "doc/how_to_build_linux.md" */>}})
- [BSD]({{</* relref "doc/how_to_build_bsd.md" */>}})

源码构建的主要依赖包括 CMake、Qt、以及一系列 thirdparty 库。Linux 和 macOS 的构建脚本已封装为 GitHub Actions workflow，可在对应仓库的 `.github/workflows/` 目录查看。

如果需要自定义样式表（stylesheet），参考 [doc/how_to_stylesheet.md]({{</* relref "doc/how_to_stylesheet.md" */>}})。

---

## 适用边界：什么时候该用，什么时候不必用

### 值得用 OpenToonz 的场景

- 独立动画工作室或学生团队，需要专业级工具但预算为零
- 有传统动画背景（熟悉 Xsheet / PEG），希望迁移到数字工作流
- 需要制作日式有限动画（电视动画、短篇）而非电影级全动画
- 需要矢量与位图混合制作，项目规模在单集 ~12 分钟 TV 动画量级

### 不必选择 OpenToonz 的场景

- 只需要轻量位图动画（Pencil2D 更简单）
- 主要做角色绑定与骨构图动画（Synfig Studio 的骨架系统更直观）
- 需要实时协作、云端同步（目前 OpenToonz 没有这类功能）
- 需要对接 DCC 管线（目前对 Maya/Houdini 等主流 DCC 软件的集成有限）

---

## 社区与生态

- **论坛**：[Google OpenToonz Users Forum](https://groups.google.com/forum/#!forum/opentoonz_en) — 提问与经验交流
- **文档**：[opentoonz_docs](https://github.com/opentoonz/opentoonz_docs) 独立仓库，包含官方使用文档
- **翻译**：通过 [Weblate](https://hosted.weblate.org/widgets/opentoonz/-/svg-badge.svg) 接受社区翻译贡献
- **CI**：AppVeyor（Windows）+ GitHub Actions（Windows/macOS/Linux 三平台）
- **Issue 管理**：GitHub Issues 活跃（撰写本文时 open issues 约 230 个）

活跃的贡献者结构表明项目在稳定维护中，但核心开发者数量有限（主要贡献者约 5 人），重大功能的开发周期可能较长。

---

## 结语：开源生态里的一支"老枪"

OpenToonz 不是新技术。它诞生于 2016 年，代码库的老脉搏可以追溯到 1980 年代末的 Toonz。但它的"老"恰恰是它的价值——三十年的工业级动画生产验证、Studio Ghibli 的生产级背书、以及在此基础上开源社区持续推进的维护，这些都意味着这是一套经过真实项目检验的工具，而非概念验证或极客玩具。

如果你在认真考虑用开源工具做 2D 动画生产，OpenToonz 是最值得评估的起点。它的 Xsheet、无纸化工作流、矢量位图混合能力，在同价位的开源方案中找不到直接对位的产品。

唯一需要清醒认识的是：**这是一套有门槛的工具**。没有动画基础的人可能需要几周时间才能理解 Xsheet 的逻辑；习惯了 Adobe Animate 的用户需要重新适应一套完全不同的交互范式。如果你能接受这个学习曲线，OpenToonz 给你的回报会超出预期。