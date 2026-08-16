---
title: "diagram-design：给 Claude Code 的编辑级图表技能，29 种自包含 HTML/SVG"
date: 2026-08-17T03:28:00+08:00
slug: "diagram-design-editorial-diagrams-claude-code-skill"
github_repo: "cathrynlavery/diagram-design"
source_key: "gh:cathrynlavery/diagram-design"
description: "diagram-design 是一个面向 Claude Code/Codex/Pi 的 Agent 技能，提供 27+ 种编辑级图表类型，自包含 HTML+SVG 输出、可自动抓取网站品牌色。本文梳理其设计取舍与安装方式。"
draft: false
categories: ["技术笔记"]
tags: ["Claude Code", "图表", "Agent Skill", "可视化", "开源"]
---

让 AI 画一张架构图，大概率会得到一堆圆角矩形加阴影的"Mermaid 风"产物——能用，但放在正经的技术文章里一眼廉价。cathrynlavery/diagram-design（19.4k stars，1.2k forks）就是为了解决这个问题而生的 Claude Code 技能（skill）：27 种编辑级（editorial）图表类型，输出自包含的 HTML + SVG，无阴影、无渐变堆砌、无"Mermaid-slop"。

## 它解决什么问题

作者在 README 里讲了动机：她运营着自己的内容站，每次需要配图——架构草图、流程图、优先级金字塔——问 Claude 得到的结果都和整站视觉风格格格不入，要么去 Figma 里磨 30 分钟，要么干脆放弃配图。于是她把这个能力做成了一个 Agent 技能，让 AI 直接产出符合编辑标准的图表。

README 里那条设计原则点明了品味来源："The highest-quality move is usually deletion"（最高质量的操作通常是删除）——每个节点都要挣得自己的位置，强调色只留给读者应该最先看的 1-2 个元素，目标信息密度是 4/10。

## 27 种图表类型与一个关键设计

类型覆盖技术写作的高频场景：架构图、流程图、时序图、状态机、ER 数据模型、时间线、泳道图、象限图、嵌套图、树、组织架构、韦恩图、层级栈、金字塔/漏斗、咨询顾问 2×2、雷达图、Loop 飞轮（2.0 新增，带共享内存枢纽的环形结构）、IT 现状图、柱状/折线/散点图、甘特图、多角色流程图、Medallion 数据分层、数据流、DP 集成与权限矩阵等。

所有类型都有三种静态变体：极简浅色、极简深色、完整编辑风。输出是**纯自包含 HTML + SVG**——没有构建步骤、没有 JavaScript、没有外部图片依赖，浏览器直接打开。

一个值得单独说的设计是 2.3 版引入的**语义系统模式（Semantic Patterns）**：行为描述与布局分离。队列、策略追踪、信任边界这类语义可以复用最接近的现有图表类型表达，而不需要为每种语义新增图表类型——类型数量因此收敛在 27 种，而不是无限膨胀。

## 60 秒品牌匹配

这个项目最聪明的一步是 onboarding 流程。你对 Agent 说"onboard diagram-design to https://yoursite.com"，它会：

1. 抓取你的首页
2. 提取主色调和字体栈
3. 映射到语义角色：paper（背景）、ink（正文）、muted（次要）、accent（强调）、link
4. 给出 diff 提案，确认后写入 `references/style-guide.md`

之后每张图都用你的颜色。网站的背景色变成图纸底色，CTA 按钮色变成焦点强调色，正文字体变成节点标签字体。写 token 之前还会自动做 WCAG AA 对比度校验——如果你的品牌色在 9-12px 的图表字号下对比度不达标，它会提议调整值并解释原因。品牌匹配还会产出一份"保真回执"：采样 URL、颜色角色、字体族与字重、字体源 URL 及回退方案。

## 安装

**Claude Code**（插件市场方式）：

```text
/plugin marketplace add cathrynlavery/diagram-design
/plugin install diagram-design@diagram-design
```

装完记得在 `/plugin` → Marketplaces 里打开 auto-update（Claude Code 对第三方市场默认关闭自动更新）。

**Codex**：

```bash
codex plugin marketplace add cathrynlavery/diagram-design
codex plugin add diagram-design@diagram-design
```

**Pi**：

```bash
pi install https://github.com/cathrynlavery/diagram-design
```

想深度定制样式指南的，可以 clone 后用 editable install（符号链接 `skills/diagram-design/` 到 `~/.claude/skills/`），避免包更新覆盖你的定制。

## 适用边界

适合：用 Claude Code / Codex / Pi 写技术内容，需要频繁配图且对视觉品质有要求的作者；团队需要统一风格的架构图、流程图产出。

不适合：需要交互式图表的场景（输出是静态 HTML/SVG，可选动效仅限有序讲解类）；需要精确数据绑定的 BI 类图表（这是编辑配图工具，不是数据分析工具）；不使用上述 Agent 工具链的用户——它本质是一个 Agent 技能包，不是独立应用。

## 小结

diagram-design 抓住了 Agent 时代一个新出现的缝隙：AI 能生成图表，但生成"好看且符合品牌"的图表需要把设计知识显式化。它把 27 种图表的结构、配色语义、对比度规则都固化成技能文件，让 AI 每次产出都落在编辑标准线以上。19.4k stars 说明这个痛点真实存在。如果你正在为文章或文档配图发愁，值得装上试一次。

- 仓库：https://github.com/cathrynlavery/diagram-design
- 图库预览：https://cathrynlavery.github.io/diagram-design/
