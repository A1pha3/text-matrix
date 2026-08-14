---
title: "ManimGL：用代码精确编排数学动画的引擎——从 3Blue1Brown 到你的讲解视频"
date: 2026-08-15T03:24:06+08:00
slug: "manim-math-animation-engine"
github_repo: "3b1b/manim"
source_key: "gh:3b1b/manim"
description: "Manim 是 Grant Sanderson（3Blue1Brown）开发的开源数学动画引擎，用精确的程序化动画制作数学讲解视频。本文聚焦作者原版 ManimGL：讲清它和 Manim Community 版的区别、安装、最小示例与使用边界。"
draft: true
categories: ["技术笔记"]
tags: ["Manim", "动画", "数学", "Python", "3Blue1Brown"]
---

# ManimGL：用代码精确编排数学动画的引擎

**核心判断**：Manim 的价值在于"精确"——它把数学动画从手工拖拽变成可复现的程序化编排，让一个复杂推导的每个几何变换、每条曲线运动都能被代码精确控制。它诞生于 Grant Sanderson（3Blue1Brown）制作数学视频的个人项目。但选择它之前必须分清一件事：**3b1b/manim 是作者原版 ManimGL，与社区维护的 Manim Community 是两条不同的安装与生态路径**，装错版本会导致一系列问题。

## 为什么值得看

Manim 是一个"用于精确程序化动画的引擎，专为制作数学讲解视频而设计"。当前约 9.1 万 star（Python，MIT 许可），是 GitHub 上最知名的数学动画项目之一，社区活跃。

关键背景：这个仓库源自 3Blue1Brown 的个人项目，视频专属代码在 <https://github.com/3b1b/videos>。**2020 年**一群开发者把它 fork 成社区版（Manim Community, <https://github.com/ManimCommunity/manim>），目标是更稳定、测试更好、响应更快、对新人更友好。

## 两版 Manim（必须先分清）

| | 本仓库（3b1b/manim） | Manim Community |
|---|---|---|
| 别称 | ManimGL | manim |
| pip 包名 | `manimgl` | `manim` |
| 维护方 | Grant Sanderson（原版） | ManimCommunity 社区 |
| 特点 | 原版，个人驱动 | 更稳定、测试更好、社区响应快 |
| 目标 | 复现 3Blue1Brown 风格 | 易上手、更通用 |

> ⚠️ README 明确警告：安装指令只适用于 ManimGL。用这套指令去装 Manim Community（或反过来）会造成问题。请先决定用哪个版本，再只按对应版本的说明操作。

## 快速上手（ManimGL）

需要 Python 3.10+、FFmpeg、OpenGL，以及可选的 LaTeX（想用 LaTeX 渲染时）。Linux 还需 Pango 及其开发头文件。

```bash
pip install manimgl

# 试运行
manimgl
```

从源码开发：

```bash
git clone https://github.com/3b1b/manim.git
cd manim
pip install -e .
manimgl example_scenes.py OpeningManimExample
# 或
manim-render example_scenes.py OpeningManimExample
```

Linux（Ubuntu/Debian）系统依赖：

```bash
sudo apt update
sudo apt install ffmpeg
sudo apt install libpango1.0-dev
# 可选：轻量 LaTeX
sudo apt install texlive-science texlive-fonts-extra texlive-latex-extra
```

## 一个最小场景示例

以 `example_scenes.py` 里的 `OpeningManimExample` 为例，`manimgl example_scenes.py OpeningManimExample` 会渲染一个经典开场场景。ManimGL 以"场景（Scene）"为单位：你在 `Scene` 子类里用代码描述对象（文本、几何图形、函数图像）和它们随时间的变化（`self.play(...)`），引擎据此生成精确动画。

## 适用边界

- **适合**：制作数学 / 物理 / 算法讲解视频；想用代码精确控制动画、追求可复现性的人；复现 3Blue1Brown 风格的教学内容。
- **边界**：ManimGL 是个人驱动的原版，API 相对社区版更"原汁原味"但迭代方向取决于作者；追求稳定与社区支持、或想用更丰富现成模块的，优先考虑 Manim Community。
- **环境要求**：FFmpeg + OpenGL 是硬依赖，LaTeX 可选但用数学公式渲染时需要。建议用虚拟环境避免与系统包冲突。

## 进一步阅读

- 两版安装区分说明：<https://docs.manim.community/en/stable/faq/installation.html#different-versions>
- 3Blue1Brown 视频仓库：<https://github.com/3b1b/videos>
- 社区版：<https://github.com/ManimCommunity/manim>
