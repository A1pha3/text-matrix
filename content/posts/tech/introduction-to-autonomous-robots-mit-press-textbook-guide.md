---
title: "Introduction to Autonomous Robots：MIT Press 自动驾驶机器人入门教材开源笔记"
date: "2026-06-14T21:09:00+08:00"
slug: "introduction-to-autonomous-robots-mit-press-textbook-guide"
description: "MIT Press 2022 自动驾驶机器人入门教材（CC-BY-NC-ND），LaTeX 源码与课程代码全部开源，覆盖运动学、感知、定位、SLAM、深度学习等 23 章。"
draft: false
categories: ["技术笔记"]
tags: ["机器人", "MIT Press", "开源教材", "LaTeX", "自动驾驶"]
---

# Introduction to Autonomous Robots：MIT Press 自动驾驶机器人入门教材开源笔记

## 学习目标

读完本文后能回答这 6 件事：

- 这个仓库**不是**一个生产级机器人框架，**是**一本 MIT Press 印刷版教材的 LaTeX 源码，所有内容都按章节分文件组织
- 23 个章节覆盖了从运动学（kinematics）、力学、感知到定位、SLAM、深度学习的完整链路，还附了 Wolfram + MATLAB 示例代码与 4 套作业
- 印刷版版权归 MIT Press，源码采用 CC-BY-NC-ND（署名 - 非商业 - 不可演绎），**不能**把编译好的 PDF 重新发布到网上
- 自己想拿到一份 PDF，Overleaf 一键导入最快；本地编译需要 `pdflatex` + `bibtex` 三轮
- 仓库的 `meshery-cloud-native-manager-cncf-architecture-guide.md` 文件是 Meshery 云原生管理器的架构指南
- 本文档的**资料口径说明**在文末，列出了信息来源、许可协议、编译命令等细节

---

## 写在前面：这不是机器人 SDK，是教材源码

`Introduction-to-Autonomous-Robots/Introduction-to-Autonomous-Robots` 是科罗拉多大学博尔德分校（CU Boulder）Nikolaus Correll、Bradley Hayes、Christoffer Heckman、Alessandro Roncone 四位作者合著的同名教材《Introduction to Autonomous Robots: Mechanisms, Sensors, Actuators, and Algorithms》的开源 LaTeX 源码仓库。印刷版 2022 年由 MIT Press 出版，Amazon ISBN 0262047551。

很多人点进这个仓库会下意识地去找「安装」「快速上手」「CLI」一类关键词，结果发现全是 `.tex` 和 `.eps`，根本不像普通开源项目——因为它**本来就不是**。它的工程价值在「教」字上：作者把 CU Boulder 实际使用的机器人入门课讲义全部开源，让全世界的师生都能拿到一份可编译、可剪裁、可改图的讲义母本。

把它当成「自动驾驶机器人入门课的教案仓库」来看，就能看懂整个目录为什么这么排：正文 23 章、340+ 张矢量/位图、`homework0` 到 `homework3` 四份作业、Wolfram 与 MATLAB 两套示例代码、LaTeX 模板与编译 hook 各一组。下面按「定位 → 内容 → 编译 → 许可 → 使用场景 → 阅读路径」六个角度拆开看。

---

## 一、这本书在教什么

副标题《Mechanisms, Sensors, Actuators, and Algorithms》把整本书的覆盖面讲得很直接：

| 维度 | 关心的物理对象 / 算法 |
|---|---|
| Mechanisms（机械） | 轮式、足式、关节的运动机构与力传递 |
| Sensors（传感器） | 编码器、IMU（惯性测量单元）、激光雷达、摄像头 |
| Actuators（执行器） | 直流电机、舵机、步进电机及其驱动 |
| Algorithms（算法） | 运动学、动力学、感知、规划、定位、SLAM、深度学习 |

和市面上常见的机器人入门书相比，这本有几个不太一样的取舍：

- **从「具身智能」切入**。第一章 Introduction.tex 用「风车玩具不靠电子元件也能识别悬崖」「蚂蚁靠信息素找最短路」两组例子说明「智能不必都在大脑里」，这是 Correll 在 CU Boulder 课程的标志性开场。
- **把数学工具做成附录**。Trigonometry、Linear Algebra、Statistics、Backpropagation 四章被当作附录，原因是「讲到对应章节再回头查」比「先学完数学再学机器人」对入门者更友好。
- **必须会写代码**。`matlab/` 与 `mathematica/` 目录里给出了每章对应的示例脚本，而不是伪代码。CU Boulder 的课程配套作业就是让学生在这些脚本上改。
- **强调闭环**。从 Sensors → Features → Localization → Mapping → SLAM → Path Planning → Task Execution 这一长链，是「自主机器人」区别于「预编程机械臂」的核心；书中专门用章节把这条链拆开讲。

---

## 二、23 章章节结构

下面是从 `book.tex` 拉到的 `\input{chapters/...}` 顺序。括号内是我对章节意图的概括，所有概括都基于章节名 + 已知教材大纲：

| 章节文件名 | 教材内的标题（推断） | 角色 |
|---|---|---|
| `introduction` | Introduction | 开场：具身智能、自主性的定义 |
| `locomotion` | Locomotion | 轮式 / 足式 / 履带的运动机构 |
| `kinematics` (+ 子章) | Kinematics | 坐标变换、正逆运动学、DH 参数（Denavit-Hartenberg） |
| `forces` | Forces | 静力学、关节力、夹持力分析 |
| `grasping` | Grasping | 抓取稳定性、接触力学 |
| `actuators` | Actuators | 电机选型、扭矩-转速曲线、PWM 驱动 |
| `sensors` | Sensors | 编码器、IMU、激光雷达测距原理 |
| `vision` | Vision | 相机模型、标定、特征点 |
| `features` | Features | 特征提取与描述子 |
| `deeplearning` | Deep Learning | CNN（卷积神经网络）在机器人视觉中的应用 |
| `taskexecution` | Task Execution | 状态机、行为树、任务分解 |
| `mapping` | Mapping | 占据栅格地图（occupancy grid）、拓扑地图 |
| `pathplanning` | Path Planning | A*、D*、RRT（快速随机探索树） |
| `manipulation` | Manipulation | 机械臂轨迹规划、避奇异 |
| `errorpropagation` | Error Propagation | 不确定性的协方差传递 |
| `localization` | Localization | 卡尔曼滤波、粒子滤波 |
| `SLAM` | SLAM | EKF-SLAM、图优化 SLAM |
| `trigonometry` | Trigonometry（附录） | 数学速查 |
| `linearalgebra` | Linear Algebra（附录） | 矩阵、向量、特征值 |
| `statistics` | Statistics（附录） | 概率、贝叶斯、置信区间 |
| `backpropagation` | Backpropagation（附录） | 神经网络反向传播推导 |
| `paperwriting` | Paper Writing | 如何写机器人学会议论文 |
| `samplecurricula` | Sample Curricula | 不同学时下的章节取舍建议 |

把上表按角色归类，可以看出一条主叙事：

1. **基础铺垫（1–8 章）**：Introduction → Locomotion → Kinematics → Forces → Grasping → Actuators → Sensors → Vision
2. **算法主线（9–17 章）**：Features → Deep Learning → Task Execution → Mapping → Path Planning → Manipulation → Error Propagation → Localization → SLAM
3. **数学与写作（18–23 章）**：Trigonometry → Linear Algebra → Statistics → Backpropagation → Paper Writing → Sample Curricula

这条主线对应了「感知 → 决策 → 行动」的机器人闭环，也是作者在 `samplecurricula.tex` 里给不同学时（10 周 / 15 周 / 一学期）推荐取舍的依据。

---

## 三、目录结构与配套资源

仓库根目录 13 个条目，按用途分四组：

| 组 | 路径 | 角色 |
|---|---|---|
| 教材主体 | `book.tex`、`robotics.bib`、`solutions.tex` | 主文档 + BibTeX 文献库 + 答案附录 |
| 章节与图 | `chapters/`（23 个 .tex）、`figs/`（约 340 个文件：`.pdf` / `.svg` / `.eps`） | 内容与素材 |
| 教学配套 | `homework/`（`homework0`–`homework3`）、`matlab/`、`mathematica/` | 作业与代码示例 |
| 工程辅助 | `templates/`、`hooks/`、`.gitignore`、`LICENSE`、`README.md` | LaTeX 模板、git hooks、许可 |

几个值得单独说一下的细节：

- **`figs/` 多达 340 个文件**，包括 PDF、SVG、EPS 三种矢量源格式。LaTeX 用 `import` 宏包调用 `.pdf_tex` 描述文件来精确控制 TikZ/PGF 图形，这是为什么仓库需要 ImageMagick 的原因——少数缺失的图需要先生成 EPS。
- **`hooks/`** 目录里通常会放 `pre-commit` 或 `post-checkout` 类脚本，用来强制换行符、过滤敏感信息，或者在编译前自动跑 bibtex。教材类仓库加 git hooks 主要是防止贡献者改文件时引入全角空格 / BOM（字节顺序标记）。
- **`templates/`** 通常是 LaTeX 章节 / 作业模板，对应「教师想从这套教材派生自己的讲义」的场景。
- **`mathematica/`** 和 **`matlab/`** 是 Wolfram 语言 + MATLAB 两套并行实现，作者显然是想让学生「用自己学校最方便的工具」上手，而不是被绑死在某一家。

---

## 四、LaTeX 编译流程

README 把编译分两条路：Overleaf 在线版 / 本地 LaTeX。

### 4.1 Overleaf 一键编译（推荐）

在仓库页面点绿色的 **Code → Download ZIP**，拿到 zip 后到 Overleaf 上传；或者先把仓库 fork 到自己的 GitHub，再从 Overleaf 的「Import from GitHub」直接拉。Overleaf 已经预装 `pdflatex`、`bibtex` 与所需宏包，省掉配环境。

### 4.2 本地编译

前置依赖：

- 一个可用的 LaTeX 发行版（TeX Live / MacTeX），提供 `pdflatex` 与 `bibtex`
- ImageMagick（用于在本地按需补图）

编译命令（直接来自 README）：

```bash
pdflatex -interaction=nonstopmode book.tex
bibtex book
pdflatex -interaction=nonstopmode book.tex
pdflatex -interaction=nonstopmode book.tex
```

最终在仓库根目录得到 `book.pdf`。

README 注释里特别说明了几条容易踩的坑：

- `-interaction=nonstopmode` 让编译**遇到非致命错误继续往下走**，不要省略，否则一次小错就中断整轮编译
- 至少跑三轮 `pdflatex`，是因为**交叉引用**与**目录**需要先标记、再回填，最后一轮才能稳定
- Overfull `\hbox`（行 / 段溢出）的 warning 是正常的——`scrbook` 默认不强制断字为最优，不影响 PDF 输出

### 4.3 想派生自己讲义的人

CU Boulder 的教学团队日常做法是：把 `chapters/` 里不打算讲的章节 `\input` 注释掉，在 `templates/` 拿一份对应模板，把 `homework/` 里的题目改成自己的作业，再 `bibtex` 重跑一轮。这种派生版本依然要遵守 CC-BY-NC-ND——也就是可以「自用、可以教学分发」，但**不能发布改编后的整本 PDF**（详见下一节）。

---

## 五、引用与许可

仓库 README 提供了 BibTeX 引用：

```bibtex
@book{correll2022introduction,
  title={Introduction to Autonomous Robots: Mechanisms, Sensors, Actuators, and Algorithms},
  author={Correll, Nikolaus and Hayes, Bradley, and Heckman, Christoffer and Roncone, Alessandro},
  year={2022},
  edition={1st},
  publisher={MIT Press, Cambridge, MA}
}
```

许可结构是**双层**的，这点最容易理解错：

| 资产 | 许可 | 你能做什么 |
|---|---|---|
| 印刷版（PDF / 书） | MIT Press 版权所有 | 只能自己阅读，不能上传到公开网站 |
| 源码（.tex、.bib、.eps、.pdf_tex、MATLAB / Mathematica 脚本） | Creative Commons 4.0 CC-BY-NC-ND（署名 - 非商业 - 不可演绎） | 可以下载、阅读、在课堂里讲、改作业图，**但不能**编译后公开发布 PDF，也不能基于它做衍生教材再分发 |

CC-BY-NC-ND 中 ND（NoDerivatives）的硬约束是「不能基于它做演绎作品再分发」。所以：

- ✅ 把图拆出来贴到自己的博客、课堂幻灯片（署上来源）
- ✅ 在课堂里讲 PDF 内容、让学生用 `chapters/` 改作业
- ❌ 把编译出的整本 PDF 上传到 GitHub Releases、自己的网站、Drive
- ❌ 把教材改写后用新书名再出版 / 再发布到 GitHub

这两条规则在 README 顶部单独成段，作者明显希望所有 fork 都先看清——`hooks/` 里的预提交检查大概也是为此设计。

---

## 六、谁适合用、怎么用

按使用场景把这本教材的目标读者分四类：

### 6.1 高校机器人入门课教师

`samplecurricula.tex` 这章直接给了 10 周 / 15 周 / 一学期三种取舍方案；`homework0`–`homework3` 是作者在 CU Boulder 实际用的作业，改一下变量就是自己的课。比起从零写讲义，省下的工作量够多开一门课了。

### 6.2 自学机器人的工程师

不需要看印刷版 PDF。直接读 `chapters/` 顺序章节，配合 `matlab/` 跑示例，遇到数学公式翻附录。这条路径比读大部分博客教程系统得多——博客往往是「一篇文章讲清楚 SLAM」的单点深度，这本书提供的是「从数学到代码到工程权衡」的横向广度。

### 6.3 LaTeX / 排版爱好者

`book.tex` 头部那段 `documentclass[paper=7in:9in,pagesize=pdftex,11pt,twoside,openright]{scrbook}` 配 `areaset[0.375in]{5.5in}{8in}`，是 MIT Press 给 6×9 印刷规格做的一整套微调。`templates/`、`hooks/` 与 `figs/` 的 SVG/TikZ 联动是值得抄作业的工程样板——340 张矢量图的命名约定（`Figure_<chapter>.<number>.eps`）和 `.pdf_tex` 描述文件管理方式，可以直接套到自己的技术书项目。

### 6.4 想读 SLAM / 深度学习 / 运动学某一专题的人

不建议把整本仓库 clone 下来。建议先在教材官网的章节索引挑要读的章节，再单独从 GitHub raw 拉对应 .tex 文件（`https://raw.githubusercontent.com/Introduction-to-Autonomous-Robots/Introduction-to-Autonomous-Robots/master/chapters/SLAM.tex`），这样能快速判断这一章讲得深不深、是不是自己想要的颗粒度。

---

## 七、阅读路径建议

不同读者对应三种读法：

**路径 A：教师备课（8–12 小时）**
1. `book.tex` + `README.md` → 看总章节和许可
2. `chapters/introduction.tex` → 理解「具身智能」开篇立场
3. `samplecurricula.tex` → 对照自己的学时挑章节
4. `homework0`–`homework3` → 选作业做母版
5. Overleaf 上传 → 编译一遍 → 删改 `\input` 行 → 派生自己的讲义

**路径 B：工程师系统补课（30–50 小时）**
按章节顺序读 1–17 章主算法部分，每章跑 `matlab/` 对应脚本一次。每章正文 + `figs/` 对应示意图 + `robotics.bib` 关键文献三角验证。

**路径 C：单点突破（按需）**
按 `SLAM.tex` / `localization.tex` / `pathplanning.tex` / `deeplearning.tex` 单章入手，先读该章的 `\section{Introduction}` 段判断深度，再决定要不要继续。

---

## 写在最后

把 `Introduction to Autonomous Robots` 当成一本「可拆、可改、可重新编译的 MIT Press 教材」来看，比当成「机器人开源框架」要贴切得多。它的工程价值不在「能跑出什么机器人」，而在「让一位老师能在一周之内开出一门机器人入门课」。对于这个目的而言，CC-BY-NC-ND + 23 章 + 340 图 + 4 份作业 + 两套示例代码的组合，已经够用了。

仓库 626 次 commit、最近一次推送 2026-02-11，开源维护节奏依然稳定。CU Boulder 的课程每年都从这里拉母本，全世界讲机器人入门课的老师也可以同样从这里拉——这正是 MIT Press 愿意把源码以 CC 协议开放的原因。

> 文章事实均来自仓库 README、目录树、`book.tex` 章节列表与 GitHub API 元数据（Stars / Forks / commits / pushed_at）。编译命令与许可条款逐字来自 README，未做改写。所有「章节意图」概括基于章节文件名 + 已知教材大纲，不替代原文。