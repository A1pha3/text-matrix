---
title: "Emil Kowalski Skills：让AI代理拥有UI/UX品味的技能库"
date: 2026-08-04T03:20:00+08:00
slug: "emilkowalski-skills-ui-animation-design"
github_repo: "emilkowalski/skills"
description: "Emil Kowalski 的 Skills 库为AI代理注入了UI/UX设计品味，包含动画审查、设计原则、组件选择等技能，让AI生成的界面不再千篇一律。"
draft: false
categories: ["技术笔记"]
tags: ["UI设计", "动画", "AI代理", "开源", "用户体验"]
---

## 项目概览

[emilkowalski/skills](https://github.com/emilkowalski/skills) 是一个为 AI 代理（Coding Agent）设计的 UI/UX 技能库，由前 Vercel 和 Linear 设计师 Emil Kowalski 创建。它不是一个传统的前端组件库或设计系统，而是一套 **"AI 的品味训练手册"**——让 AI 代理在生成用户界面时，能够做出正确的动画、设计和组件选择决策。

项目自 2026 年 3 月发布以来，已获得超过 24,000 颗星标（截至 2026 年 8 月已超 24,300 颗），成为 AI 驱动 UI 开发领域现象级项目。它的核心输出是 8 个可被 AI 代理加载的 `SKILL.md` 文件，每个文件针对一个具体的设计决策场景。

## 痛点：AI 没有审美

这是项目的出发点。Emil 在 README 中直言不讳：

> "Agents don't have great taste."

AI 代理在生成 UI 时，经常犯下一些微小但致命的错误：

- 入场动画用了 `ease-in`（缓入），实际上应该用 `ease-out`（缓出）——前者让用户等待动画最慢的阶段，而入场动画最应该让用户感觉"瞬间完成"
- 用实线边框代替半透明阴影
- 给高频操作（如快捷键）添加动画，实际上应该完全禁用动画
- 使用 CSS 内置的缓动曲线（太弱），而非自定义的强曲线

这些"小细节"的累积，决定了界面是"惊艳"还是"平庸"。正如 Emil 在文章《[Agents with Taste](https://emilkowal.ski/ui/agents-with-taste)》中所说，AI 可以放大专家的能力，但它无法替代专家——你需要先知道什么是"好"，才能教给 AI 什么是"好"。

## 技能库全景

项目包含 8 个核心技能，覆盖了从动画审查到组件选择的完整决策链：

### 1. emil-design-eng（主技能）
最核心的技能，整合了 Emil 在 UI 打磨、组件设计、动画决策方面的哲学。它不会主动触发，而是在被调用时以"设计工程师"的身份给出建议。核心理念：**品味是训练出来的，不是天生的**——它是对"什么让界面感觉好"的深度思考，而非个人偏好。

### 2. review-animations（严格审查动画）
一个专门化的审查技能，以极高的标准审视动画代码。它的姿态是"默认有问题，通过才放行"。核心规则包括：

- **十项不可协商标准**：动画必须有正当理由、必须匹配使用频率、必须使用正确的缓动曲线、UI 动画必须控制在 300ms 以内……
- **频率分级**：快捷键/每天 100+ 次的操作 → 零动画；偶尔出现（弹窗/抽屉）→ 标准动画；首次/罕见 → 可以加入惊喜
- **绝不使用 `ease-in`**：它让用户等待最需要流畅的时刻
- **CSS 内置缓动太弱**：必须使用 `cubic-bezier(0.23, 1, 0.32, 1)` 这样的强曲线

### 3. improve-animations（审计式改进）
以"审计→计划→执行"的分离模式运作。它遍历代码库中的所有动画代码，产出优先级排序的审计报告，每个报告包含自包含的执行计划。这意味着：**用最贵的模型做判断，用最便宜的模型做执行**。

### 4. find-animation-opportunities（发现动画机会）
扫查 UI 中"应该动但没有动"的地方，同时**拒绝**那些"不应该动"的地方。它的核心是"克制"——一个建议动画的工具如果到处推荐动画，反而有害。产出上限为 5-7 条建议，按杠杆率排序。

### 5. animation-vocabulary（动画术语翻译）
反向查词表：把用户对动画的模糊描述（"弹窗出来时那个弹弹的东西"）翻译成精确的术语（"Pop in"）。让你能用正确的词汇向 AI 提需求，从而获得更好的结果。

### 6. apple-design（苹果设计原则）
从 Apple 的 WWDC 设计讲座（尤其是 2018 年的《Designing Fluid Interfaces》）中提炼的界面设计和流畅动效原则，**翻译到 Web 平台**（CSS、Pointer Events、requestAnimationFrame、Spring 库）。核心线索：

> "当界面以物理方式响应时，它就不再像一台电脑，而像身体的延伸。"

### 7. pick-ui-library（选择 UI 库）
一个高度主观的推荐列表。当代理需要 toast 组件、拖拽库、命令菜单、图表库时，根据 Emil 信赖的库列表做出选择，而不是让 AI 手写一个 toast 组件或安装一个已废弃的包。

### 8. prototype（原型探索）
给定一个 UI 描述（"一个 toast"、"一个定价卡片"、"一个按住删除按钮"），构建多个**真正不同的版本**，并放在一个视觉切换器中，让用户翻看对比、选出最佳的。核心要求是"发散"——三个相同色调的变体浪费了选择器的价值。

## 作者背景

Emil Kowalski 是知名的设计工程师，曾在 **Vercel** 和 **Linear** 工作。他创建了 [Sonner](https://sonner.emilkowal.ski)（Toast 组件库）和 [cmdk](https://cmdk.paco.me)（⌘K 命令菜单库），并运营着 [animations.dev](https://animations.dev/) 设计课程。他在 [emilkowal.ski](https://emilkowal.ski/) 上发表了一系列关于 UI 动画的深度文章，包括《7 Practical Animation Tips》和《You Don't Need Animations》。

他的核心观点是：**AI 不替代专业知识，它放大专业知识**。如果你不懂动画，AI 也不会帮你写出好的动画。这个技能库的本质是把他的专业知识"编码"成 AI 可读的规则文件。

## 安装与使用

安装极其简单，一行命令即可将整个技能库添加到当前项目中：

```bash
npx skills@latest add emilkowalski/skills
```

这个命令会下载所有 `SKILL.md` 文件到你的项目中，然后 AI 代理（如 Claude Code、Cursor、Windsurf 等）就可以在后续对话中自动加载这些技能。

使用示例：

**场景一：审查动画代码**
```bash
# 在对话中引用 review-animations 技能
"请用 review-animations 技能审查这段动画代码"
```

**场景二：审计整个代码库的动画**
```bash
"用 improve-animations 审计当前项目的所有动画，给出改进计划"
```

**场景三：选择正确的 UI 组件库**
```bash
"我需要一个命令菜单组件，用 pick-ui-library 帮我选"
```

**场景四：探索设计方案**
```bash
"用 prototype 技能，给我看三种不同风格的定价卡片"
```

## 适用边界

**适合的场景：**
- 使用 AI 编码代理（Claude Code、Cursor、Windsurf、GitHub Copilot）进行 UI 开发
- 前端项目需要动画一致性审查
- 设计团队希望将设计规范"编码"为 AI 可执行的规则
- 新手开发者需要"设计品味训练"

**不适合的场景：**
- 传统的前端开发流程（不依赖 AI 代理）
- 后端/数据密集型项目
- 对动画有极低容忍度的项目（如后台管理面板）
- 需要 AI 直接修改代码的场景（improve-animations 明确声明只读分析，不修改代码）

## 阅读路径

1. **[README](https://github.com/emilkowalski/skills)**（3 分钟）— 了解项目动机和全景
2. **[Agents with Taste](https://emilkowal.ski/ui/agents-with-taste)**（8 分钟）— Emil 的博客文章，解释"为什么 AI 需要品味"
3. **[emil-design-eng](https://github.com/emilkowalski/skills/blob/HEAD/skills/emil-design-eng/SKILL.md)**（10 分钟）— 主技能，理解 Emil 的设计哲学
4. **[review-animations/STANDARDS.md](https://github.com/emilkowalski/skills/blob/HEAD/skills/review-animations/STANDARDS.md)**（15 分钟）— 动画标准参考，最实用的技术细节
5. 根据需要查看其他技能文件

---

这个项目最令人兴奋的地方在于它定义了一种新的范式：**知识编码**。不再是"人写文档给 AI 看"，而是"专家写规则给 AI 执行"。在 AI 驱动的开发时代，专业品味将成为最稀缺的资源——而 `emilkowalski/skills` 正是将这种稀缺资源规模化的最佳实践。