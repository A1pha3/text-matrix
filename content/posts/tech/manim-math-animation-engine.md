---
title: "ManimGL：用代码精确编排数学动画的引擎——从 3Blue1Brown 到你的讲解视频"
date: 2026-08-15T03:24:06+08:00
lastmod: 2026-09-28
slug: "manim-math-animation-engine"
github_repo: "3b1b/manim"
source_key: "gh:3b1b/manim"
description: "Manim 是 Grant Sanderson（3Blue1Brown）开发的开源数学动画引擎，用精确的程序化动画制作数学讲解视频。本文聚焦作者原版 ManimGL：讲清它和 Manim Community 版的区别、安装、第一个场景怎么写、动画如何渲染成片、交互式开发与项目配置，并给出选型判断。"
draft: false
categories: ["技术笔记"]
tags: ["Manim", "动画", "数学", "Python", "3Blue1Brown"]
---

# ManimGL：用代码精确编排数学动画的引擎

**核心判断**：Manim 的价值在“精确”。它把数学动画从逐帧手工拖拽变成可复现的程序化编排，让每个几何变换、每条曲线运动都能被代码精确控制。它源于 Grant Sanderson（3Blue1Brown）做视频的个人工具。动手前必须分清一件事：**3b1b/manim 是作者原版 ManimGL，与社区维护的 Manim Community 是两条不同的安装与生态路径**，装错版本会一路踩坑。

本文按“为什么需要它 → 两个版本怎么区分 → 怎么写第一个场景 → 一次渲染怎么走完全程 → 边界与选型”的顺序展开。想最快拿到结论，直接跳到「怎么选」；想跟着写一遍，从「写一个场景」开始。

## 它解决的是什么

传统视频工具把动画拆成时间轴上的关键帧，创作者靠鼠标一帧帧调位置、颜色、速度。Manim 反着来：一段数学关系被写成 Python 对象，放到“场景”里，再用动画把它随时间的变化描述出来——一个向量绕定点旋转、一条曲线随公式形变、一次矩阵变换同时作用于画面上所有对象。

这套设计的好处在于重放。输入的数值一变，重跑一遍场景，整段动画跟着变，不需要回到每个关键帧上返工。3Blue1Brown 正是靠它把推导视频做成生产流水线：他每个视频背后的场景代码都公开在 3b1b/videos 仓库里，这些代码经受住了多年真实生产使用，反过来也压着原版 API 不断演进出可靠能力。

仓库现状：约 9.4 万 star（2026-09-28 GitHub 读数），Python，MIT 许可。PyPI 上的 `manimgl` 最新版是 1.7.2（2024 年 12 月发布），而 master 分支仍在持续演进（2026-09-09 还有提交）——想跟上最新改动，得按下面「快速上手」里的方式从源码装。star 是关注度信号，不等于安装量或稳定性，选型仍以前面的那件事为准。

## 两个版本，先分清再装

| | 本仓库（3b1b/manim） | Manim Community |
|---|---|---|
| 别称 | ManimGL | manim |
| pip 包名 | `manimgl` | `manim` |
| Python 要求 | 3.10+ | 3.11+（v0.21.0） |
| 维护方 | Grant Sanderson（原版） | ManimCommunity 社区，2020 年从原版 fork |
| 渲染 | OpenGL（GPU） | Cairo（CPU）为主，内置 OpenGL 渲染器 |
| 交互开发 | `self.embed()` / `-e` 命令断点，内建 | Jupyter `%%manim` 魔法命令、在线环境 |
| 文档 | 示例驱动、较简，有中文翻译版 | ReadTheDocs、官方站点 |
| 生态 | 无官方 Docker/Jupyter | 官方 Docker 镜像、`%%manim`、try.manim.community |

两个细节值得注意。其一是类名不同：同是“画出对象”这个动画，原版叫 `ShowCreation`，社区版叫 `Create`——网上抄来的代码若直接跑报 `AttributeError`，先查是不是版本对不上。其二是两边 README 都在推荐自己：原版说社区版“更稳定、测试更好、上手更友好”，社区版则建议大多数人选社区版、想研究 Grant 本人的工作方式再去原版。推荐都有立场，看完本文的选型段再定。

> ⚠️ README 明确警告：这些安装指令只适用于 ManimGL。把社区版安装说明套到原版（或反过来）会造成问题。请先决定用哪个版本，再只看对应版本的文档。这条警告是真实的版本区分依据，不是防呆口号。

渲染器差异不是性能八卦。ManimGL 用 OpenGL 渲染，复杂场景能靠 GPU 加速，还带实时预览窗口——边写边看，不用等渲染完。代价是依赖 OpenGL 环境。社区版默认走 Cairo（CPU），换平台更省心、输出更可预测，但复杂场景要等。

## 快速上手（ManimGL）

需要 Python 3.10+、FFmpeg、OpenGL，以及可选的 LaTeX（渲染数学公式时）。Linux 还需 Pango 及其开发头文件。

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

macOS 用 Homebrew：`brew install ffmpeg mactex`。完整 MacTeX 约 6GB，嫌大可以改装轻量的 BasicTeX，再按需补包；Apple Silicon 机器还要额外装 Cairo（`arch -arm64 brew install pkg-config cairo`）。Windows 先装 FFmpeg 和 MiKTeX（LaTeX），再走源码安装那三行。用 Anaconda 的话，官方建议开一个 `python=3.10` 的独立环境再 `pip install -e .`。

建议用虚拟环境安装，避免与系统 Python 包冲突。

## 写一个场景：从代码到画面

ManimGL 里没有“画一帧”的概念，只有“定义一个场景，然后让它动”。最小结构是这样：

```python
from manimlib import *

class SquareToCircle(Scene):
    def construct(self):
        square = Square()
        circle = Circle()

        self.play(ShowCreation(square))
        self.wait()
        self.play(Transform(square, circle))
        self.wait()
```

这段代码对应四个核心概念：

1. **对象（Mobject）**：`Square()` 和 `Circle()` 是画面里的几何对象。它们不是像素，而是带坐标、颜色、描边等属性的数学结构，可以变换、组合、复用。
2. **场景（Scene）**：`class SquareToCircle(Scene)` 定义一段独立的视频单元，`construct` 是它的入口。一条视频就是一串场景按顺序跑完。
3. **动画（Animation）**：`self.play(ShowCreation(square))` 让正方形从无到有画出来，`Transform(square, circle)` 让正方形平滑变成圆形。`self.play` 负责插值，你只声明起点和终点，引擎在对象上逐帧过渡。
4. **节奏（wait）**：`self.wait()` 让画面停留一拍（默认 1 秒），给观众消化的时间。

保存成 `scenes.py`，然后渲染：

```bash
manimgl scenes.py SquareToCircle
```

渲染完成后默认打开预览窗口。常用参数：

| 参数 | 作用 |
|------|------|
| `-w` | 写入视频文件 |
| `-o` | 写入并自动打开 |
| `-s` | 跳过过程，只存最后一帧；`-so` 存成图片并显示，出缩略图常用 |
| `-n 3` | 从场景的第 3 个动画开始渲染；写成 `-n 3,6` 则渲染到第 6 个为止，调试常用 |
| `-a` | 把文件里所有场景都渲染出来 |
| `-i` / `-t` | 输出 GIF / 带透明通道的视频 |
| `-l` / `-m` / `--hd` / `--uhd` | 分辨率档位：480p / 720p / 1080p / 4K |
| `-r 1920x1080` + `--fps 60` | 精确指定分辨率和帧率 |
| `-p` | 演示者模式：wait 处暂停，按空格或右方向键继续，像放幻灯片 |
| `-f` | 预览窗口全屏 |

这批参数里，`-w`、`-o`、`-s`、`-n` 四条来自官方示例文件顶部注释，是调试时最常用的；其余来自命令行帮助，做正式输出和演讲时用得上。

理解了“对象 + 动画 + 渲染”这条链，就理解了为什么改参数是重跑而不是重画：动画的每一帧都由引擎按起点、终点和插值函数算出来，改一个数值，重跑一遍，整段跟着变。视频输出时，帧序列交给 FFmpeg 打包成文件。

## 一次渲染的完整链路

把上面的机制串成一次真实成片，全程是这样：

1. 你运行 `manimgl scenes.py SquareToCircle -w`。引擎读配置（默认分辨率 1920×1080、30fps、深灰背景 `#333333`），加载场景类，调用 `construct`。
2. 每个 `self.play` 被拆成一串帧：引擎在起点和终点状态之间逐帧插值，OpenGL 负责把每帧画出来；预览窗口同步播放。
3. 帧序列流给 FFmpeg（默认 `libx264` 编码、`yuv420p` 像素格式），打包成一个 mp4。
4. 成片落在运行目录下的 `videos/` 里。要逐像素无损输出，配置里可换 `libx264rgb` 编码、`rgb24` 像素格式加 `crf: 0`。

两处最常见的调整都在这条链上：改画质用上面的分辨率档位参数，改输出位置和素材目录用 `custom_config.yml`（下一节）。若场景里用了 `Tex` 或 `Text`，首次渲染会把 LaTeX 编译结果缓存下来加速后续运行——这也是排错时要记住的一环。

## 交互模式：边写边看

ManimGL 最被低估的能力是交互式开发，官方 Quick Start 里专门有一节。在 `construct` 里写一行 `self.embed()`：

```python
class InteractiveDevelopment(Scene):
    def construct(self):
        circle = Circle()
        self.play(ShowCreation(circle))
        self.embed()
        # self.embed() 之后的代码，在交互终端里试出来再抄回源码
```

运行到这一行时会弹出一个 iPython 终端，`circle`、`square`、`self` 都在当前命名空间里。你可以直接敲 `self.play(circle.animate.shift(RIGHT))` 看效果，满意了再把这行抄回源码；终端里 `play`、`wait`、`add`、`clear` 这些方法还能省掉 `self.` 前缀。不想改代码，也可以用 `-e 行号` 直接在指定行下断点进交互。

预览窗口本身也能操作：终端里输入 `touch()` 进入交互态，滚轮平移、按住 `z` 滚轮缩放、按住 `d` 拖动鼠标转 3D 视角，`r` 复位机位，`q` 退出回到终端。配合 `always(circle.move_to, self.mouse_point)` 这类语句，对象可以实时跟随鼠标，做出真正的响应式演示。改完代码想重跑，在交互终端里执行 `reload_scene()`；跨文件改动多的话加 `--autoreload` 让引擎自动重载模块。

这套“终端里逐行写、窗口里即时看”的工作流，正是 OpenGL 路线的独特收益。社区版的对应生态是 Jupyter：`%%manim` 魔法命令在 notebook 单元格里逐格渲染。

## 用 custom_config.yml 固化项目配置

比命令行参数更进一步的固化手段是配置文件。在你运行 manim 的目录里放一个 `custom_config.yml`，它就会覆盖默认值；文件放别处也行，用 `--config_file 路径` 指定。所有可配项和默认值都在源码的 `manimlib/default_config.yml` 里，常用的几类：

- **目录**：视频输出位置（默认 `videos/`），以及 manim 读取图片、声音、3D 模型、CSV 数据的素材子目录——做系列视频时把素材归置好，场景代码里直接按名引用。
- **画质**：默认分辨率、帧率、视频编码参数。
- **观感**：背景色、默认描边宽度与颜色、`Text` 的默认字体（默认 `Consolas`）、LaTeX 模板。
- **坐标系**：`frame_height` 默认 8.0，即画面竖向跨 8 个 manim 单位——布局时对齐、留白都以此为尺度。

3b1b/videos 仓库就带着一份自己的 `custom_config.yml`，定义了 3Blue1Brown 视频的输出与样式约定，是最真实的参考样例。

## 常见问题与踩坑

**Q：装了 `manim`，脚本里却报 `manimlib` 找不到？**

多半是把包名混了。原版必须 `pip install manimgl`，社区版才是 `manim`。两个包可以共存（包名与导入名都不同：`manimgl` 对应 `from manimlib import *`，社区版对应 `from manim import *`），真正会出错的是想用 A 版却只装了 B 版的包，或者照着另一个版的文档在装。

**Q：渲染数学公式报 LaTeX 错误？**

公式依赖 LaTeX。ManimGL 本身不含 TeX 发行版，需要系统里有 `texlive` 或 `mactex`。不想装全套，Linux 上装 `texlive-science` 加 `texlive-latex-extra` 这类组合、macOS 上用 BasicTeX，也能覆盖大部分公式。

**Q：`manimgl` 打不开窗口，或报 OpenGL 错误？**

ManimGL 走 OpenGL，必须有可用的图形环境。无头服务器没有显示环境，实时预览打不开；要么配虚拟显示，要么改用不依赖 GPU 的社区版走 Cairo 渲染。

**Q：中文文本显示成方块或乱码？**

文本渲染依赖系统字体，默认字体是 `Consolas`，系统里没有这个字体或没有中文字体都会出问题。先确认系统装了中文字体，再通过 `Text` 的 `font` 参数指定字体名称，或者在 `custom_config.yml` 里改 `text.font` 默认值。

**Q：渲染出来只有一帧，没有动起来？**

确认命令里没有带 `-s`。`-s` 只存最后一帧；去掉它，`self.play` 声明的动画才会逐帧写入视频。

**Q：改了公式或字体设置，渲染结果却没变？**

`Tex` 和 `Text` 的编译结果有本地缓存，异常情况下旧缓存可能挡路。用 `--clear-cache` 清掉再试。

## 自测：确认你真的读懂了

- 看到 `pip install manim`，你装的是哪个版本？反过来 `manimgl` 呢？
- `self.play(Transform(a, b))` 里，引擎替你做了哪件事？
- 一段公式渲染不出来，先查哪个系统依赖？
- 想边写边看效果，该用 `self.embed()` 还是 `-s`？两者分别发生在什么阶段？

这四问能答上来，版本、动画、渲染链、工作流几条主线就都通了。

## 适用边界

- **适合**：制作数学 / 物理 / 算法讲解视频；想用代码精确控制动画、看重可复现性的人；复现 3Blue1Brown 风格的教学内容。
- **边界**：ManimGL 是个人驱动的原版，API 更“原汁原味”，但迭代方向取决于作者，接口可能随他的视频需求变动；踩坑时能依赖的社区支持也比社区版少。官方文档自己也标注"in progress"，深度内容常要去源码和示例里找。
- **环境要求**：FFmpeg + OpenGL 是硬依赖，LaTeX 可选但数学公式渲染时会用到。GPU 加速、实时预览和交互式开发只属于 ManimGL，不是社区版的卖点。

## 怎么选

- 想复现 3Blue1Brown 风格、要做实时预览、偏好“终端里逐行写、窗口里即时看”的，直接用 ManimGL。
- 要稳定 API、完整文档和教程、想要 Docker 镜像或 Jupyter 集成的（面向长期项目或团队协作），先看 Manim Community。
- 二元落地建议：**一个人做视频、追求 3B1B 效果 → ManimGL；多人协作、要工程化稳定 → Community。**

## 进一步阅读

按上手顺序，官方文档（[3b1b.github.io/manim](https://3b1b.github.io/manim/)）的 Getting Started 就是按“安装 → Quick Start → CLI 配置 → 示例场景”排的，照着走一遍即可。中文资料有 manim-kindergarten 维护的翻译版[文档站](https://docs.manim.org.cn/)和收集实用扩展的 [manim_sandbox](https://github.com/manim-kindergarten/manim_sandbox) 仓库。

源码里的 `example_scenes.py` 是最好的语法速查，十二个示例场景各有分工：`OpeningManimExample` 开场示例，`AnimatingMethods` 讲 `.animate` 语法，`TextExample` 与 `TexTransformExample` 讲文本和公式变换，`TexIndexing` 讲按子串截取公式局部，`TexAndNumbersExample` 讲把公式里的数字接上实时数值，`UpdatersExample` 讲逐帧更新的对象，`CoordinateSystemExample` 讲坐标系作图，`GraphExample` 讲图结构，`SurfaceExample` 讲 3D 曲面，`InteractiveDevelopment` 和 `ControlsExample` 讲交互。按这个顺序读，够你上手大部分 3B1B 风格效果。

- 官方仓库与示例场景：<https://github.com/3b1b/manim>
- 3Blue1Brown 视频仓库（注意：较早视频的代码可能与最新版 manim 不兼容）：<https://github.com/3b1b/videos>
- 两版安装区分说明：<https://docs.manim.community/en/stable/faq/installation.html#different-versions>
- 社区版：<https://github.com/ManimCommunity/manim>
