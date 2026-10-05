---
title: "emilkowalski/skills：把设计工程师的判断顺序交给代理"
date: 2026-08-02T02:59:48+08:00
slug: "emilkowalski-skills-design-taste"
github_repo: "emilkowalski/skills"
source_key: "gh:emilkowalski/skills"
description: "emilkowalski/skills 是 Emil Kowalski 开源的 13 个 Agent Skills：主线是把动画决策拆成该不该动、为什么动、用什么曲线、多快的固定顺序，周边覆盖 Apple 设计原则、移动端原生感、Swift 与库选型。作者有 Vercel、Linear 的工作经历，本文对照 README 与技能源文件拆解它的结构与规则。"
draft: false
categories: ["技术笔记"]
tags: ["Agent Skills", "UI 设计", "前端", "动画", "品味"]
---

## 开场判断

教代理写 UI 的技能仓库不少，`emilkowalski/skills` 是其中最聚焦的一个：13 个技能里有 7 个围着动画转，而动画技能真正编码的不是代码模板，是一套先于代码的判断顺序——该不该动、为什么动、用什么曲线、多快。顺序对了，代码才有对错的分野。

仓库的由来，作者 Emil Kowalski 在 README 里说得很直白：

> Agents don't have great taste.
>
> I have seen plenty of times that agents don't pick the right ingredients for an animation. An `ease-in` easing for an enter animation when it's supposed to be `ease-out`. Or they choose a solid border instead of a semi-transparent shadow for your UIs.

这些技能是他给自己经验做的切片。README 的原话是 "They are based on my years of experience working at companies like Vercel and Linear"，技能则是 "a side-effect of domain-expertise" 的副产品。更系统的论述在他那篇 [Agents with Taste](https://emilkowal.ski/ui/agents-with-taste)：把代理可能犯的小错一条条列出来，再逐条解释怎么修。

## 仓库速览

| 维度 | 数据 |
|------|------|
| 仓库 | [emilkowalski/skills](https://github.com/emilkowalski/skills) |
| Stars | 41,449（2026-09-28，GitHub API） |
| 建仓时间 | 2026-03-16 |
| 技能数 | 13 |
| 主语言 | Markdown |
| 许可证 | MIT |

安装只有一行：

```bash
npx skills@latest add emilkowalski/skills
```

也可以在 [skills.sh/emilkowalski/skills](https://skills.sh/emilkowalski/skills) 浏览每个技能的安装量。

## 13 个技能分三条线

先看地图。13 个技能不是按"缓动、阴影、留白"这类主题切的，而是按任务切的，大致三条线：

| 线 | 技能 | 干什么 |
|------|------|------|
| 动画主线 | `emil-design-eng` | 主技能：动画决策框架 + 组件原则 + 性能与可访问性 |
| | `animate` | 从零构建一个动画，按决策顺序走完每一步 |
| | `animate-expo` | 同一套标准搬到 React Native/Expo：手势、sheet、触感反馈、把动效挪出 JS 线程 |
| | `review-animations` | 按 craft 高标准审查动画代码，默认挑刺 |
| | `improve-animations` | 全库动画审计，产出带优先级的改造计划，对源码只读 |
| | `find-animation-opportunities` | 找值得加动效的地方，同时拒绝不该动的 |
| | `animation-vocabulary` | 把模糊描述反查成准确术语："popover 打开时那个弹一下的" → Pop in |
| 设计与工程延伸 | `apple-design` | Apple 的界面设计与物理动效原则，从 WWDC 设计讲座提炼、翻译到 web |
| | `mobile-native` | 让 web app 在手机上有原生感：sticky hover、点击高亮、100vh 问题、输入框缩放页面 |
| | `write-swift` | 写现代 Swift：值类型建模、Swift 6 并发安全、泛型、性能与 ARC |
| | `pick-ui-library` | 从作者信任的清单里为任务选库，而不是让代理手搓 toast |
| | `prototype` | 对同一段 UI 生成多个真正不同的版本，切换器里现场对比 |
| 生态配套 | `ask-sonner` | 作者自家 toast 库 [Sonner](https://sonner.emilkowal.ski) 的使用指南：安装、样式、常见问题修复 |

动画是绝对主线。剩下六个技能服务于同一种判断力在相邻领域的延伸——Apple 的动效哲学、移动端的触摸细节、Swift 的工程规范，都是"界面为什么 feels right"在不同层面的答案。

## 主技能：674 行的判断框架

`emil-design-eng` 是全套技能的地基，674 行（2026-09-28 读数），自我介绍是"This skill encodes Emil Kowalski's philosophy on UI polish, component design, animation decisions, and the invisible details that make software feel great"。它的核心是写任何动画代码前必须依次回答的四个问题。

**第一问：该不该动？** 按使用频率决策。键盘快捷键、命令面板开关这类每天上百次的操作，答案是 "No animation. Ever."——技能里举的正面例子是 Raycast，一个没有开合动画的启动器。每天几十次的 hover 效果要删或大幅简化。偶尔出现的弹窗、抽屉、toast 用标准动画。首次出现的 onboarding 才允许加一点惊喜。

**第二问：目的是什么？** 合法的答案有五种：空间一致性（toast 从哪个方向进就从哪个方向出，滑动关闭才符合直觉）、状态指示（按钮变形表示点击已生效）、解释（营销动画演示功能怎么用）、反馈（按下时轻微缩小，确认界面听到了）、避免跳变。如果答案只是"看起来酷"，而用户又会频繁看到它，那就别动。

**第三问：用什么曲线？** 决策树很短：进出屏幕用 `ease-out`；屏内移动或形变用 `ease-in-out`；hover 和颜色变化用 `ease`；匀速运动（跑马灯、进度条）用 `linear`。然后是全仓库最重的一条禁令：

> **Never use ease-in for UI animations.** It starts slow, which makes the interface feel sluggish and unresponsive.

内置曲线也被认为太弱，技能要求用自定义 `cubic-bezier`，比如 `cubic-bezier(0.23, 1, 0.32, 1)` 这类更"冲"的 ease-out 变体，并推荐 [easing.dev](https://easing.dev/) 和 [easings.co](https://easings.co/) 找现成曲线。

**第四问：多快？** 技能给了一张按元素的时长表：

| 元素 | 时长 |
|------|------|
| 按钮按压反馈 | 100-160ms |
| Tooltip、小 popover | 125-200ms |
| 下拉框、选择器 | 150-250ms |
| 弹窗、抽屉 | 200-500ms |

总上限是 300ms。配套的还有感知性能的算账：180ms 的选择器动画比 400ms 的"感觉"更响应，转得更快的 spinner 让加载显得更快——加载时间没变，变的是用户的判断。

框架之外，几条高辨识度的规则值得单独记：

- 元素入场从 `scale(0.95)` 加透明度开始，而不是 `scale(0)`。理由写成了 fixed 句式："Nothing in the real world appears from nothing"——现实世界里没有东西是从无到有凭空出现的。
- 弹出层的 `transform-origin` 要跟随触发它的按钮，居中缩放的 popover 一眼就假；模态框例外，保持居中。
- 退出要比进入快。checklist 原文给的量级是 "enter 2s, exit 200ms"。注意这是时长上的快，不是把 ease-in 用在退出上——后者正是被禁的。
- hover 动画必须包在 `@media (hover: hover) and (pointer: fine)` 里，否则触屏设备会踩进粘住的 hover 态。
- 列表项依次入场用 stagger，间隔 30-80ms；stagger 是装饰，播完之前不许阻塞交互。

主技能的哲学部分只有三条，但每条都在给上面的规则兜底：品味是训练出来的而非天生（"Taste is trained, not innate"）；看不见的细节会复利（引的是 Paul Graham 那句 "a thousand barely audible voices all singing in tune"）；美是杠杆（"Beauty is leverage"——人人软件都够好的时候，体验本身就是差异化）。

## 审查格式是强制的

这套技能有一个很少见的设计：连输出格式都写死在技能里。审查 UI 代码时，必须输出 `Before | After | Why` 三列的 markdown 表格，一行一个问题，并明确禁止"Before: xxx / After: xxx"这种逐行罗列的格式。技能原文用的是 "you MUST" 和 "Wrong format (never do this)"——措辞强度在技能文件里属于最高档。

表格里的行直接来自那份 11 条的 Review Checklist，随手举几行：

| Before | After | Why |
| --- | --- | --- |
| `transition: all 300ms` | `transition: transform 200ms ease-out` | 指明具体属性，避免 `all` |
| `ease-in` on dropdown | 换自定义曲线的 `ease-out` | `ease-in` 起步慢，反馈迟滞 |
| 键盘触发的动画 | 整个删掉 | 高频操作，动画即延迟 |
| 元素同时出现 | 加 30-80ms stagger | 级联入场比"哗"一下全出来自然 |

审查立场上，`review-animations` 的 description 写着 "Default to flagging; approval is earned"——默认标记问题，通过是挣来的。这个姿态和大多数"夸两句再提建议"的 AI 审查拉开了距离。

分工也考虑到了执行成本：`improve-animations` 对源码只读，产出的是"带优先级、各自独立"的改造计划，description 里明说这些计划可以交给其他代理或更便宜的模型去执行。审查用贵的模型，施工用便宜的，这个组合是写进技能定位里的。

## 一次审查怎么走

把一个现成的下拉菜单动画交给装了这套技能的代理，流程大致是这样：

1. 代理读到 `transition: all 300ms ease-in`，对照 checklist 命中两条：`transition: all` 该指明具体属性；UI 动画禁用 `ease-in`。
2. 按 Review Format 输出 Before/After/Why 表格，修复方向同样来自 checklist——`transform 200ms ease-out`，曲线可换成自定义变体。
3. 如果入场还有个 `scale(0)`，会被一并指出：改成 `scale(0.95)` 加透明度起步。
4. 用户接着说"把整个应用都过一遍"，就轮到 `improve-animations`：扫全库、按优先级出计划，每条计划自成一体，可以丢给任何代理执行。

这个流程里没有一步是猜的——四问框架、时长表、checklist 条目、输出格式、模型分工，全部写在技能文件里。代理做的事是把规则套到具体代码上，而不是凭"感觉"发挥。这正是这套技能和泛泛的"帮你写好看 UI"类技能的分野：它把品味拆成了可执行、可复查的判定步骤。

## 与同类项目的位置

动画品味这个方向上，另外两个常被一起提及的技能仓库：

| 项目 | 定位 | Stars（2026-09-28） |
|------|------|------|
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | "The design language that makes your AI harness better at design"，通用设计语言 | 71,766 |
| `emilkowalski/skills` | 动画判断为主线的设计工程技能集 | 41,449 |
| [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd) | 管 AI 的输出形态：别把答案埋在长文里 | 51,551 |

三者不冲突，颗粒度也不同：impeccable 给的是整体设计语言，`emilkowalski/skills` 深耕动画与交互微决策，i-have-adhd 根本不管 UI，管的是代理回答问题的方式。一起装是常见组合——骨架、细节、输出形态各管一层。

## 采用建议

**值得马上装**：天天用 Claude Code、Codex 写前端的人，尤其是被"动画能跑但就是不对"反复消耗的团队。React Native/Expo 项目有对应的 `animate-expo`，移动端 web 有 `mobile-native`，覆盖是完整的。

**按需看**：`write-swift`、`apple-design` 与前端 UI 关系较远，装不装取决于技术栈；`pick-ui-library` 和 `prototype` 被设计成只在显式调用时运行，不会自己抢戏。

**别期待它做的事**：它不教你从零学设计——技能假设使用者已经写得动 UI 代码，缺的是判断；它也不是设计系统，组件库还得自己选；Apple 原则部分是 WWDC 讲座的翻译提炼，想深挖还是得回源头看讲座。

**一个更普适的读法**：这个仓库的样板意义可能大于它的直接用处。它示范了一件事——领域专家的判断可以编码成代理可加载、可执行的规则。作者自己在 README 里把这层意思说破了：

> All the skills here are a side-effect of domain-expertise. AI doesn't replace such expertise, it amplifies what you can get out of it and makes you way better relative to others.

技能不会替你长出品味，它只是把一个有品味的人怎么下决定，摊开给代理看。别的领域也一样：先把判断顺序写清楚，代理才有的可执行。
