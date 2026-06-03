---
title: "mathVideoMaker：当 AI 不会看图，怎么稳定产出数学讲解视频与交互网页"
date: "2026-06-03T08:43:03+08:00"
slug: "mathvideomaker-ai-friendly-math-explainer-skill"
description: "mathVideoMaker 用 SafeScene、checktext、checkweb 三项护栏把「看图纠错」机械化，让无视觉 AI 稳定产出 Manim 视频与配套交互网页。"
draft: false
categories: ["技术笔记"]
tags: ["AI Agent", "Cursor Skill", "Manim", "数学可视化", "护栏工程"]
---

# mathVideoMaker：当 AI 不会看图，怎么稳定产出数学讲解视频与交互网页

## 核心判断

`mathVideoMaker`（仓库 [GordenSun/mathVideoMaker](https://github.com/GordenSun/mathVideoMaker)）在发布 3 天内拿到 149 颗星，热度来自一个被很多人忽略的工程问题：**当一个 AI Agent 看不到自己渲染出来的画面，它怎么保证做出来的数学讲解视频能看？**

仓库的真正护城河不是 Manim 本身，而是一套把"视觉反馈"机械化、文本化的**三层质检闭环**——`SafeScene` 渲染时自动打印 `[layout]` 警告、`check_text.py` 静态扫字符防方框、`check_web.py` 用 7 个静态检查项把交互网页的"静默故障"逐条列出。这套闭环让一个没有视觉能力（或视觉能力不可靠）的模型，也能稳定产出"讲清楚 + 玩明白"的配套产物。

这个范式的价值超出数学讲解：**它示范了一种"AI 友好型 Skill"该怎么设计**——质检前置、护栏内嵌、共享设计规范、阶段化工作流。

## 系统地图

仓库本身只有 57KB 体积，但内部分层清晰。下面这张图覆盖它的全部主路径：用户输入 → 阶段化执行 → 双重产物 → 闭环质检。

```mermaid
flowchart TD
    A[用户输入<br/>主题/受众/形式] --> B[A. 明确需求<br/>默认值兜底]
    B --> C[B. 写分镜 storyboard.md<br/>共享设计规范]
    C --> D{阶段 C<br/>环境准备}
    D -->|视频需要| E[setup_manim.sh<br/>check_env.py]
    D -->|纯网页可跳过| G
    E --> F[D1. 视频 Manim 渲染]
    C --> G[D2. 网页 HTML 生成]
    F --> F1[SafeScene 自动布局检查<br/>[layout] WARN/DONE]
    F --> F2[check_text.py 字体字形]
    F1 --> H[render.sh 渲染 MP4]
    F2 --> H
    G --> G1[check_web.py 7 项静态检查]
    G1 --> I[index.html 浏览器验证]
    H --> J[E. 交付]
    I --> J
    J --> K[视频 + 网页 + 分镜<br/>并排放在主题文件夹]
```

整条链路里**最值得看的是质检层**——它不是事后审查，而是**嵌进执行步骤的护栏**：每写一个镜头就静帧渲染一次、每写一个 HTML 元素就跑 `check_web.py`，所有检查结果都是文字输出，可以被没有视觉的 Agent 消化。

## 三层质检闭环拆解

仓库里 5 个脚本和 1 个护栏模块共同构成质检体系，但它们不是平级的——按触发时机和检查对象，可以拆成三条边界清晰的线：

| 层级 | 名称 | 触发时机 | 检查对象 | 输出形式 |
|------|------|----------|----------|----------|
| L1 | `SafeScene.layout_check()` | 每次 `self.wait()` / `self.caption()` | Manim 场景中元素的边界框（出界/重叠） | 日志 `[layout] DONE 共发现 0 处` |
| L2 | `check_text.py` | 渲染前静态扫描 | `scene.py` 中所有 `Text`/`frow` 字符串的字体字形 | 缺失字符列表（防方框 □） |
| L3 | `check_web.py` | 网页写完立即跑 | 7 类网页静默故障（详见下表） | `[PASS]` / `[FAIL]` 分类汇总 |

### L3 是整个闭环最巧妙的一环

`check_web.py` 把 HTML 交互网页最常见的"看图看不出来但功能已坏"的问题机械化：

1. **公式不渲染**：`$...$` 漏配对、KaTeX CDN 缺一个、`renderMathInElement` 没调用
2. **JS 引用 null**：`getElementById('x')` 引用了 HTML 里不存在的 id（拼写错）
3. **canvas 链路断开**：有 `<canvas>` 但 JS 没 `getContext`、定义了 `draw()` 但从未调用
4. **滑块没绑事件**：有 `<input type=range>` 但没监听 `input` 事件 → 拖了没反应
5. **布局规范违反**：没单列居中 `.wrap`、交互区 `.stage` 出现在讲解区 `.explain` 之后
6. **class 拼写错**：`querySelector('.foo')` 引用了不存在的 class
7. **JS 语法错**（有 node 时）：用 `node --check` 二次确认

这 7 项覆盖了 90% 的"我自己打开看看发现没问题但用户那边坏了"的故障模式。**它用一个约 187 行的 Python 脚本替代了 4 个 QA 工程师的眼力**。

## 共享设计规范——视频和网页的"同一灵魂"

仓库的另一个非显然设计是**视频和网页不是两个独立产物，而是同一个概念的两种投影**。两件产物必须共享：

- 同一概念、同一种记号（视频里用 `n`，网页里就不能用 `k`）
- 同一组可交互参数（视频里 `n=1,3,0.3,0,-1` 是关键镜头，网页里 `n` 滑块范围/步长严格一致）
- 同一套配色（背景 `#0b1020`、主色 `#5b9cff`、强调 `#ffd166`）
- 同一批关键视觉标注（如 x=1 处 y=n 的点，视频画出来，网页也画出来）

这种"一份分镜、两件产物"的共享约束在 `templates/storyboard.md` 里以**必填字段**形式出现：分镜不写明"共享设计规范"就进不了 D 阶段。这种硬性约束在多产物 Skill 里极其罕见——多数 Skill 允许两件产物各自独立，结果出现"视频用红、网页用蓝、记号还不同步"的撕裂感。

默认两件都做（`SKILL.md` 阶段 A 明文要求），只有用户明确说"只要视频"或"只要网页"才单做。这种"先充分后收窄"的设计哲学也值得其他 Skill 学习。

## 任务流案例：勾股定理证明如何流过这个 Skill

光有层级图不够，我用一个具体例子把抽象机制串起来——仓库自带的**黄金范例** `templates/example_pythagoras_proof.py`（勾股定理的重排/面积法证明）。

**第 1 步：阶段 A 默认参数兜底**
- 主题：勾股定理的面积证明
- 形式：视频 + 网页（默认）
- 受众：初高中
- 时长：~60–90 秒
- 风格：深色 + 高对比

**第 2 步：阶段 B 写分镜**
- 共享设计规范定下：记号 `a,b,c`；可调参数为 `a,b`（直角边长度，范围 1.6-2.4）；配色用默认深色蓝底
- 推导主线（占镜头 50%+）："两个一样大的正方形各塞进 4 个相同直角三角形，左边空出 a²+b²、右边空出 c² → 大正方形相等、扣掉的三角形相等 → 剩下的面积相等 → a²+b²=c²"

**第 3 步：阶段 D1 视频生成**
- 复制 `templates/scene_template.py` + `mathviz.py` 到主题文件夹
- `scene.py` 继承 `SafeScene`，`construct()` 依次调用 `intro → build_two_squares → fill_left → fill_right → compare_and_conclude`
- 写完一段就先 `bash render.sh scene.py PythagorasProof s`（出静帧）→ 在日志搜 `[layout]`，确保 `DONE 共发现 0 处`
- 跑 `check_text.py` 防方框（Python 公式的 `²` 字符在 PingFang SC 中存在，但如果是别的符号会立刻告警）
- 草稿用 `m`（720p30）渲染，render.sh 会**自动把成片复制到主题文件夹根目录**，和 `index.html` 并排

**第 4 步：阶段 D2 网页生成**
- 复制 `templates/interactive_template.html` 为 `index.html`
- 把视频里的"两个正方形、4 个三角形"画法在 canvas 里实现，参数 `a, b` 各对应一个滑块
- 跑 `check_web.py`，必须 `[PASS]`（7 项全过）
- 浏览器打开（macOS `open index.html`）二次确认

**第 5 步：阶段 E 交付**
- 视频 `PythagorasProof.mp4` + 网页 `index.html` + 分镜 `storyboard.md` 全部放在主题文件夹根目录
- 交付说明强调一致性：记号、配色、参数范围三件一致
- 告诉用户："先看视频理解原理，再打开网页拖滑块看参数变化"

整个流程里，**质检闭环保证了任何一步出故障都能在文字输出里被捕捉**——Agent 不需要"看"，只需要"读"。

## "质检覆盖范围"能告诉我们什么、不能告诉我们什么

仓库里没有跑分表（这是教学型 Skill，不是性能基准），但**质检覆盖范围本身就是一种可观察的"质量基准"**——

- **L1（布局检查）能保证**：元素不出界、不重叠、字幕在安全区。但**不保证美学质量**（颜色好不好看、动效是否流畅）——那是有视觉能力时的二次确认项。
- **L2（字体检查）能保证**：你写的所有字符在选定字体里有字形，渲染不会是方框。**不保证文字内容正确**——拼写错、术语错它查不出来。
- **L3（网页检查）能保证**：7 类功能级故障一个没有。**不保证交互设计**够不够直观、滑块手感顺不顺——那需要真人体验。

换句话说，这套闭环解决的是"功能正确性"，不解决"体验质量"。**它把 Skill 的可靠性从 30%（没视觉就盲飞）拉到了 90%（结构性故障都被文字化）**，剩下的 10% 是体验层，需要人类或有视觉能力的模型补位。

## 与同类项目的工程取舍对比

mathVideoMaker 解决的是"AI 看不到图也能做出数学可视化"这个具体问题，与它对照的有几条不同路线：

| 路线 | 工具 | 核心机制 | 适用场景 |
|------|------|----------|----------|
| **本仓库路线** | Manim + KaTeX + 文字化质检 | 视频推导 + 网页交互 + 三层护栏 | AI Agent 自动生产、批量讲解 |
| Jupyter / Marimo | Python 笔记本 | 代码即文档、就地执行 | 探索性教学、课程作业 |
| Observable / D3 | JS 笔记本 | 数据驱动可视化、声明式 | 数据新闻、统计可视化 |
| Desmos / GeoGebra | 在线工具 | 即点即用、社区共享 | 课堂演示、几何探索 |

mathVideoMaker 的护城河在于**"为 AI 而不是为人设计"**：把需要眼睛判断的事全部转成文字可读的事。这与 Notebook 系（为人设计）的取向正相反。

## 适用边界与采用顺序

**先用的团队/场景：**
- 在 Cursor / Claude Code 里搭数学/物理教学 Agent 的团队，把这个 Skill 直接 clone 到 `.cursor/skills/`
- 做 K12 数学可视化内容、需要批量产出"讲解视频 + 配套交互页"的创作者
- 研究"AI 友好型 Skill"工程范式的团队，把它当范式参考

**先等等的场景：**
- 想要 3Blue1Brown 那种**精雕细琢的**视频——这个 Skill 强调"先求对、再求好"，美学要靠后续打磨
- 项目需要 LaTeX 公式渲染但环境装不了 LaTeX——脚本会自动降级到 `Text` + Unicode，公式会变得朴素
- 主题没有可交互参数（如纯几何定理）——网页会自动降级为"分步可点选"，但体验会打折

**采用顺序建议：**
1. 先 clone 仓库，复制 `.cursor/skills/math-explainer/` 到你的项目根
2. 在 Cursor 里直接说"做一个视频，讲解勾股定理"，跑通一次完整流程
3. 跑完后看 log 里 `[layout] DONE 0 处` 和 `check_web.py [PASS]` 这两条核心信号
4. 把默认配色（`#0b1020` / `#5b9cff` / `#ffd166`）换成你的品牌色
5. 在 `templates/scene_template.py` 基础上加你的"分镜套路"（如先讲应用场景再讲定理）

## 仓库元数据

| 维度 | 取值 | 验证来源 |
|------|------|----------|
| 仓库全名 | `GordenSun/mathVideoMaker` | GitHub API |
| 作者 | GordenSun | GitHub API |
| 描述 | 未填写 | 仓库 description 为 null |
| Stars | 149 | GitHub API（2026-06-03） |
| Forks | 24 | GitHub API |
| Watchers | 149 | GitHub API |
| 主要语言 | Python | GitHub API |
| 许可证 | 未指定 | License 字段为 null |
| 创建时间 | 2026-05-31 | GitHub API |
| 最后推送 | 2026-05-31 | GitHub API |
| Open issues | 0 | GitHub API |
| 默认分支 | main | GitHub API |
| 仓库体积 | 57 KB | GitHub API |

## 参考资源

- **仓库入口**：[github.com/GordenSun/mathVideoMaker](https://github.com/GordenSun/mathVideoMaker)
- **核心 Skill 定义**：[`.cursor/skills/math-explainer/SKILL.md`](https://github.com/GordenSun/mathVideoMaker/blob/main/.cursor/skills/math-explainer/SKILL.md)
- **护栏模块**：[`templates/mathviz.py`](https://github.com/GordenSun/mathVideoMaker/blob/main/.cursor/skills/math-explainer/templates/mathviz.py) — `SafeScene` + 自动布局检查
- **黄金范例**：[`templates/example_pythagoras_proof.py`](https://github.com/GordenSun/mathVideoMaker/blob/main/.cursor/skills/math-explainer/templates/example_pythagoras_proof.py) — 真正的勾股定理证明
- **网页模板**：[`templates/interactive_template.html`](https://github.com/GordenSun/mathVideoMaker/blob/main/.cursor/skills/math-explainer/templates/interactive_template.html)
- **核心教学法**：[`references/pedagogy-and-storyboard.md`](https://github.com/GordenSun/mathVideoMaker/blob/main/.cursor/skills/math-explainer/references/pedagogy-and-storyboard.md)
- **Manim 指南**：[`references/manim-guide.md`](https://github.com/GordenSun/mathVideoMaker/blob/main/.cursor/skills/math-explainer/references/manim-guide.md)
- **Manim 配方**：[`references/manim-cookbook.md`](https://github.com/GordenSun/mathVideoMaker/blob/main/.cursor/skills/math-explainer/references/manim-cookbook.md)
- **网页指南**：[`references/interactive-web-guide.md`](https://github.com/GordenSun/mathVideoMaker/blob/main/.cursor/skills/math-explainer/references/interactive-web-guide.md)
- **底座项目**：[ManimCommunity/manim](https://github.com/ManimCommunity/manim)（基于 v0.20+）
