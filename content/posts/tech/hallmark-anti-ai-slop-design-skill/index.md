---
title: "Hallmark：让 AI 生成的页面不再长得像 AI 生成的"
date: 2026-08-10T03:40:00+08:00
draft: true
categories: ["技术笔记"]
tags: ["hallmark", "ai-design", "claude-code", "anti-slop", "frontend"]
description: "Hallmark 是一个面向 Claude Code、Cursor 和 Codex 的设计技能（skill），通过 21 套主题、57 道 slop-test 检测门和预发射自评机制，系统性地阻止 AI 生成千篇一律的 UI 页面。"
github_repo: "Nutlope/hallmark"
source_key: "gh:Nutlope/hallmark"
---

## 问题：AI 生成的页面为什么一眼就能认出来

用 LLM 生成前端页面时有一个普遍现象：不管你描述什么需求，产出的页面都有一种微妙的"AI 味"——居中 hero、渐变背景、三列卡片、rounded-2xl、indigo→purple 色板。这不是某个模型的缺陷，而是所有主流 LLM 在训练数据中见过太多同类模板后的统计回归——模型倾向于输出分布最密集的那个设计。

Hallmark（[Nutlope/hallmark](https://github.com/Nutlope/hallmark)）针对的就是这个问题。它的定位不是一个 UI 生成器，而是一个 **设计技能（skill）**——一组规则和检测门，挂载到 Claude Code、Cursor 或 Codex 上，在代理生成 HTML/CSS 时执行约束。

## 它怎么工作

### 四个动词

Hallmark 的全部操作围绕四个动词展开：

| 动词 | 作用 |
|---|---|
| *(默认)* | 构建新 UI。选择宏观结构，应用规则集，通过 slop-test 后交付 |
| `hallmark audit <target>` | 对已有代码做评分，输出问题清单，不做修改 |
| `hallmark redesign <target>` | 保留文案、信息架构和品牌，用不同的设计指纹重建结构 |
| `hallmark study <screenshot \| URL>` | 从你欣赏的设计中提取 DNA（宏观结构、字体配对、色彩锚点），可选生成可移植的 `design.md` |

默认模式是核心：你给一个需求简报，Hallmark 选择一种宏观结构（macrostructure）和一套主题（theme），生成页面后跑 57 道 slop-test 检测门，通过才交付。

### 21 套主题 + 自定义模式

Hallmark 内置 21 套命名主题（Hum、Cobalt、Carnival、Lumen、Garden、Riso、Grid 等），每套主题有自己的字体配对、色板、布局节奏和视觉语言。不同需求简报会匹配到不同主题——一个酸面包烘焙 app 和一个 API 文档站点拿到的设计完全不同，不是换色卡而是换骨架。

当 21 套主题都无法匹配需求中的创意意图时，Hallmark 切换到 **Custom 模式**：从头设计页面，量身定制调色板、字体和布局。Custom 模式同样跑 57 道 slop-test，但底下没有模板。这是一个安静的分支——普通需求永远不会触发它。

### 57 道 slop-test 检测门

这是 Hallmark 的核心防线。在页面交付前，它运行 57 项检测，覆盖已知的 AI 设计坏习惯：

- 居中 hero 三件套（标题 + 副标题 + CTA 全居中）
- indigo→purple 渐变
- 三列等高 feature 卡
- rounded-2xl 通用
- emoji 当 icon
- 透明玻璃拟态（glassmorphism）
- 以及更多统计高频但设计低质的模式

检测门不只是模式匹配——它还包含一道 **预发射自评**（pre-emit self-critique），让模型在交付前审视自己的输出。

### 不同简报，不同形态

Hallmark 的核心主张是：两个不同需求简报产出的页面应该感觉像不同的网站，而不是同一个模板的换色。仓库中展示了 12+ 个示例页面（酸面包 app、提取 API、唱片厂牌、AI 推理工具、茶单、蜂蜜农场、丝网印刷展、字体工作室、SaaS、旅行预订、摩洛哥时尚品牌、开发者基础设施），每个都有完全不同的视觉语言和布局结构。

## 安装

```bash
npx skills add nutlope/hallmark
```

重新运行即可更新。或者手动复制 `SKILL.md` 和 `references/` 目录到：

- **Claude Code**：`~/.claude/skills/hallmark/`
- **Cursor**：`.cursor/rules/hallmark.mdc`（用 `SKILL.md` 正文，去掉 frontmatter）
- **Codex**：`~/.codex/skills/hallmark/`（个人）或 `.codex/skills/hallmark/`（项目级）

规则集主体在 [`skills/hallmark/SKILL.md`](https://github.com/Nutlope/hallmark/blob/main/skills/hallmark/SKILL.md) 和 [`references/`](https://github.com/Nutlope/hallmark/tree/main/skills/hallmark/references)，实例教程在 `docs/recipes.md` 和 `docs/study-examples.md`。

## 与其他工具的关系

Hallmark 不是网站构建器。它是一个技能层——规则集 + 检测门——挂载到已有的 AI 编程代理上。代理负责理解需求、写 HTML/CSS、处理交互逻辑；Hallmark 负责确保输出不滑入统计平均值。

这意味着它与你现有的工作流兼容：你依然用 Claude Code 或 Cursor 写代码，只是在生成前端页面时多了一层设计约束。

## 项目数据

| 指标 | 数值 |
|---|---|
| Stars | ~23,000 |
| Forks | ~1,180 |
| 主语言 | CSS |
| 许可证 | MIT |
| 制作方 | Together AI |
| 最近更新 | 2026-08-06（新增 Grid 主题） |

## 适用边界

### 适合

- 用 AI 代理生成前端页面，苦于输出千篇一律
- 需要快速产出多种设计风格的原型
- 想从已有设计中提取设计 DNA 复用到新项目
- 团队有品牌规范但 AI 输出总不遵守

### 不适合

- 后端、CLI、API 等非前端场景——Hallmark 只管视觉设计
- 需要像素级精确控制（Hallmark 选择主题和结构，不是手动调 CSS）
- 没有 AI 代理作为宿主——Hallmark 是 skill 不是独立应用

## 判断

Hallmark 的价值在于它正面攻击了 AI 生成 UI 的核心痛点：统计回归导致的设计同质化。57 道 slop-test 是一个工程化的解决方案——把"不要这样设计"从模糊的建议变成可执行的检测门。21 套主题提供了足够的多样性，Custom 模式为边缘案例留了出口。

它的局限是必须依附于 AI 编程代理使用，本身不独立运行；且它主要面向营销页/hero 页/产品落地页，对复杂 Web 应用（dashboard、管理后台）的覆盖有限。但作为一个让 AI 输出更有品味的设计约束层，它目前是这个方向上最系统的尝试。
